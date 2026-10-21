"""Helpers for the AEA-31 reset tests: stores, doubles, the dirty demo, snapshots. Not collected by pytest."""

from __future__ import annotations

import functools
import hashlib
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from langgraph.checkpoint.base import empty_checkpoint

from meridian.adapters.checkpointer import CHECKPOINTS_DB_NAME, Checkpointer
from meridian.adapters.sqlite.migrate import restore_working_copy
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import CaseRow, ConversationRow, StreamEvent, case_stream
from meridian.domain.common import CaseRef, RequestId, ThreadId, TurnId
from meridian.domain.handoff import (
    BRIEF_KEYS,
    BRIEF_ORIGINS,
    BRIEF_TITLES,
    Brief,
    BriefExtraction,
    BriefHeading,
    CaseSummary,
    HandoffReason,
    Priority,
)
from meridian.domain.staff import DemoRole, LoginSession, LoginSessionId
from meridian.domain.state import ConversationState
from meridian.domain.tools import LookupRow
from meridian.domain.turn import CheckResult
from meridian.policy.handoff import promise_for
from meridian.ports.runtime import UnitOfWork
from meridian.services.reset import CHICAGO, ResetService, seed_demo, seed_first_boot
from meridian.services.reset_gate import ResetGate
from tests.fixtures.sqlite import ISSUED_DB, TempStore, temp_sqlite

__all__ = ["CHICAGO", "ISSUED_DB", "WALL"]

WALL = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)
ISSUED_TABLES = ("customers", "technicians", "appointment_slots", "appointments", "invoices")


def new_request_id() -> RequestId:
    return RequestId(str(uuid4()))


@contextmanager
def demo_store() -> Iterator[tuple[TempStore, Checkpointer]]:
    with temp_sqlite() as store:
        cp = Checkpointer(store.data_dir / CHECKPOINTS_DB_NAME)
        try:
            yield store, cp
        finally:
            cp.close()


def fake_brief(case_ref: CaseRef, thread_id: ThreadId, at: datetime) -> Brief:
    headings = tuple(
        BriefHeading(
            number=i + 1,
            key=cast(Any, BRIEF_KEYS[i]),
            title=BRIEF_TITLES[i],
            origin=cast(Any, BRIEF_ORIGINS[i]),
            checked=i != 3,
            items=(),
            trimmed=False,
            trim_note=None,
            not_generated=False,
        )
        for i in range(8)
    )
    return Brief(
        case_ref=case_ref, thread_id=thread_id, assembled_at=at, status="being_written", headings=headings
    )


class RecordingAssembler:
    def __init__(self, staff_guidance: object = None) -> None:
        self.assembled: list[tuple[CaseSummary, ConversationState, tuple[LookupRow, ...]]] = []
        self.extractions: list[BriefExtraction | None] = []
        self.checks: list[CheckResult | None] = []

    def assemble(self, case: CaseSummary, state: ConversationState, lookups: Any) -> Brief:
        self.assembled.append((case, state, tuple(lookups)))
        return fake_brief(case.case_ref, state.thread_id, case.created_at)

    def attach_extraction(
        self, brief: Brief, extraction: BriefExtraction | None, check: CheckResult | None
    ) -> Brief:
        self.extractions.append(extraction)
        self.checks.append(check)
        return brief.model_copy(update={"status": "ready"})


def fake_format_clock(dt: datetime) -> tuple[str, str]:
    return (f"label {dt.isoformat()}", f"date {dt.date().isoformat()}")


def seed_fn(assembler: RecordingAssembler | None = None) -> Callable[[UnitOfWork], int]:
    return functools.partial(seed_demo, assembler=assembler or RecordingAssembler())


def make_service(
    store: TempStore,
    cp: Checkpointer,
    *,
    gate: ResetGate | None = None,
    restore: Callable[[UnitOfWork], None] | None = None,
    clearing: Callable[[], AbstractContextManager[None]] | None = None,
    seed: Callable[[UnitOfWork], int] | None = None,
) -> tuple[ResetService, ResetGate]:
    the_gate = gate or ResetGate()
    service = ResetService(
        store.uow,
        the_gate,
        restore or functools.partial(restore_working_copy, issued_path=store.issued_path),
        clearing or cp.clearing,
        seed or seed_fn(),
        format_clock=fake_format_clock,
    )
    return service, the_gate


def login_session(role: DemoRole) -> LoginSession:
    return LoginSession(
        session_id=LoginSessionId(str(uuid4())),
        role=role,
        role_reset=False,
        signed_in_at=DEMO_START,
        expires_at=WALL + timedelta(hours=12),
    )


@dataclass
class Dirty:
    open_threads: list[ThreadId]
    sessions: dict[str, LoginSession]
    case_ref: CaseRef
    max_event_id: int


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def make_dirty_demo(
    store: TempStore,
    cp: Checkpointer,
    *,
    open_chats: int = 1,
    customer_message: str = "Hi, my AC is making a noise.",
) -> Dirty:
    seed_first_boot(store.uow, seed_fn(), WALL)
    sessions = {
        "customer": login_session(DemoRole.CUSTOMER),
        "representative": login_session(DemoRole.REPRESENTATIVE),
        "supervisor": login_session(DemoRole.SUPERVISOR),
    }
    threads: list[ThreadId] = []
    with store.uow(write=True) as tx:
        conn = tx.connection
        conn.execute("UPDATE appointment_slots SET status='booked' WHERE slot_id=56")
        conn.execute(
            "INSERT INTO appointments (slot_id, customer_id, issue_description, created_at) "
            "VALUES (56, 'MHC-10004', 'synthetic', '2026-10-16')"
        )
        for _ in range(open_chats):
            tid = ThreadId(str(uuid4()))
            threads.append(tid)
            tx.core.conversations.insert(
                ConversationRow(
                    thread_id=tid,
                    demo_session=str(sessions["customer"].session_id),
                    run_tag="live",
                    agent_version="test",
                    started_at=DEMO_START,
                )
            )
            tx.core.messages.append(tid, "assistant", "Hello, how can I help?", DEMO_START)
            tx.core.messages.append(
                tid, "customer", customer_message, DEMO_START, turn_id=TurnId(str(uuid4())), kind="text"
            )
        ref = tx.cases.refs.next_case_ref()
        promise = promise_for(HandoffReason.REFUND, "nobody_online", DEMO_START)
        tx.cases.cases.insert(
            CaseRow(
                case_ref=ref,
                thread_id=threads[0],
                reason=HandoffReason.REFUND,
                priority=Priority.P3,
                rule_id="R24.refund",
                trigger="escalation",
                lifecycle="unassigned",
                created_at=DEMO_START,
                updated_at=DEMO_START,
            )
        )
        tx.cases.promises.insert(ref, promise, DEMO_START)
        tx.core.events.append(case_stream(ref), StreamEvent(type="case_changed", payload={}, at=DEMO_START))
        stamp = _iso(WALL)
        conn.execute(
            "INSERT INTO identity_threads (thread_id, status, customer_id, updated_at) "
            "VALUES (?, 'code_sent', 'MHC-10004', ?)",
            (str(threads[0]), stamp),
        )
        conn.execute(
            "INSERT INTO identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, "
            "tries_left, inbox_message_id) VALUES (?, 'MHC-10004', ?, 'demo_inbox', ?, ?, 3, 1)",
            (str(threads[0]), uuid4().hex, stamp, stamp),
        )
        conn.execute(
            "INSERT INTO demo_inbox (demo_session, thread_id, to_masked, sent_at, expires_at) "
            "VALUES (?, ?, 'e***@example.com', ?, ?)",
            (str(sessions["customer"].session_id), str(threads[0]), stamp, stamp),
        )
        for sess in sessions.values():
            conn.execute(
                "INSERT INTO staff_sessions (token_hash, session_id, role, role_reset_pending) "
                "VALUES (?, ?, ?, 0)",
                (uuid4().hex, str(sess.session_id), sess.role.value),
            )
        conn.execute(
            "INSERT INTO flags (case_ref, target, flagged_by_role, flagged_at, status) "
            "VALUES (?, 'answer', 'representative', ?, 'new')",
            (str(ref), stamp),
        )
        conn.execute("INSERT INTO spend_ledger (recorded_at, run_tag) VALUES (?, 'live')", (stamp,))
        conn.execute(
            "INSERT INTO health_events (at_wall, kind, agent_version) VALUES (?, 'check_ok', 'test')",
            (stamp,),
        )
        conn.execute(
            "INSERT INTO deploy_records (deploy_id, at_wall, agent_version) VALUES (?, ?, 'test')",
            (str(uuid4()), stamp),
        )
        run_id = str(uuid4())
        conn.execute(
            "INSERT INTO eval_runs (run_id, suite, agent_version, harness_commit, harness_digest, repeats, "
            "started_at, status, cases_expected, cases_scored) "
            "VALUES (?, 'e2e', 'test', 'c', 'd', 1, ?, 'completed', 1, 1)",
            (run_id, stamp),
        )
        conn.execute(
            "INSERT INTO eval_case_results (run_id, case_id, repeat, passed_hard, outcome) "
            "VALUES (?, 'case-1', 0, 1, 'resolved')",
            (run_id,),
        )
        conn.execute(
            "INSERT INTO job_runs (job_run_id, started_wall_at, demo_now, status) "
            "VALUES (?, ?, ?, 'completed')",
            (str(uuid4()), stamp, stamp),
        )
        conn.execute(
            "INSERT INTO demo_events (demo_event_id, at_wall, kind, demo_before, demo_after, request_id, role) "
            "VALUES (?, ?, 'clock_advanced', 'a', 'b', ?, 'supervisor')",
            (str(uuid4()), stamp, str(uuid4())),
        )
        conn.execute("INSERT INTO reset_events (reset_id, at_wall) VALUES (?, ?)", (str(uuid4()), stamp))
        conn.execute(
            "INSERT INTO ended_threads (thread_id, demo_session, ended_wall_at, reason, reset_id) "
            "VALUES (?, 'old-session', ?, 'demo_reset', NULL)",
            (str(uuid4()), stamp),
        )
        tx.cases.demo_state.set_now(datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO))
        tx.cases.demo_state.set_staffing("simulated_on_shift")
        tx.commit()
    for tid in threads:
        cfg: Any = {"configurable": {"thread_id": str(tid), "checkpoint_ns": ""}}
        for i in range(2):
            cfg = cp.saver.put(cfg, empty_checkpoint(), {"source": "loop", "step": i, "parents": {}}, {})
    max_id = rows(store.db_path, "SELECT MAX(id) FROM events")[0][0]
    return Dirty(open_threads=threads, sessions=sessions, case_ref=ref, max_event_id=int(max_id or 0))


def snapshot(store: TempStore, cp: Checkpointer) -> dict[str, list[tuple[object, ...]]]:
    out: dict[str, list[tuple[object, ...]]] = {}
    for label, path in (("meridian", store.db_path), ("checkpoints", cp.path)):
        conn = sqlite3.connect(path)
        try:
            names = sorted(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
            for name in names:
                out[f"{label}:{name}"] = [
                    tuple(r)
                    for r in conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid')  # noqa: S608  # names from sqlite_master
                ]
        finally:
            conn.close()
    return out


def rows(path: Path, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(path)
    try:
        return [tuple(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


def count(path: Path, table: str) -> int:
    return int(rows(path, f"SELECT COUNT(*) FROM {table}")[0][0])  # noqa: S608  # table names are literals in tests


def issued_rows(issued_path: Path, table: str) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(f"{issued_path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        return [tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]  # noqa: S608
    except sqlite3.OperationalError:
        if table == "sqlite_sequence":  # the issued file has no AUTOINCREMENT table, so no sqlite_sequence
            return []
        raise
    finally:
        conn.close()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
