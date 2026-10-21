"""Builders and seeders shared by the load_context unit tests and the J-3 journey step (AEA-34)."""

from __future__ import annotations

import contextlib
import sqlite3
import time
import uuid
from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager
from datetime import datetime, timedelta
from typing import Any, cast

from langgraph.runtime import Runtime

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import ConversationRow
from meridian.agent.context import GraphDeps
from meridian.agent.nodes.load_context import load_context
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import RequestId, ThreadId, TurnId
from meridian.domain.state import ConversationState, LoadContextUpdate
from meridian.domain.turn import SpanHandle, TurnBudget, TurnContext, TurnIds, TurnInput
from meridian.policy.limits import Limits
from meridian.ports.runtime import TraceSink, UnitOfWork, UnitOfWorkFactory
from tests.fixtures.sqlite import TempStore

__all__ = [
    "DEMO_SESSION",
    "DEMO_START",
    "RecordingUow",
    "Tripwire",
    "add_line",
    "connection_of",
    "count_rows",
    "make_ctx",
    "make_deps",
    "make_state",
    "new_thread",
    "new_turn",
    "run_node",
    "seed_conversation",
    "seed_identity",
    "seed_twenty_turns",
    "seed_wp4f",
    "wp4f_moved",
]

DEMO_SESSION = "demo-session-1"
_COUNTED = ("actions", "messages", "turns", "check_events", "lookup_log")


def new_thread() -> ThreadId:
    return ThreadId(str(uuid.uuid4()))


def new_turn() -> TurnId:
    return TurnId(str(uuid.uuid4()))


def make_ctx(
    thread_id: ThreadId, turn_id: TurnId, *, now: datetime, span: SpanHandle | None = None
) -> TurnContext:
    ids = TurnIds(
        thread_id=thread_id,
        turn_id=turn_id,
        request_id=RequestId(str(uuid.uuid4())),
        run_tag="live",
        run_id=None,
        agent_version="test",
    )
    started = time.monotonic()
    budget = TurnBudget(started=started, deadline=started + 60.0)
    return TurnContext(
        ids=ids,
        budget=budget,
        now=now,
        demo_session=DEMO_SESSION,
        span=span or SpanHandle(turn_id=turn_id, trace_id=None),
        intake=None,
    )


def make_state(
    thread_id: ThreadId, turn_id: TurnId, *, now: datetime, text: str = "Hello", **keys: Any
) -> ConversationState:
    return ConversationState(
        thread_id=thread_id,
        turn_input=TurnInput(turn_id=turn_id, message_id=1, kind="text", text_store=text, received_at=now),
        **keys,
    )


class Tripwire:
    """Stands in for every GraphDeps field load_context must never touch; records and fails on any use."""

    def __init__(self, name: str, touched: list[str]) -> None:
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_touched", touched)

    def __getattr__(self, attr: str) -> object:
        name: str = object.__getattribute__(self, "_name")
        touched: list[str] = object.__getattribute__(self, "_touched")
        touched.append(f"{name}.{attr}")
        raise AssertionError(f"load_context touched {name}.{attr}")


class RecordingUow:
    """Wraps the temp store's factory; records ("enter", write, exclusive) and ("exit", write, exclusive)."""

    def __init__(self, inner: UnitOfWorkFactory) -> None:
        self._inner = inner
        self.events: list[tuple[str, bool, bool]] = []

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]:
        return self._open(write, exclusive)

    @contextlib.contextmanager
    def _open(self, write: bool, exclusive: bool) -> Iterator[UnitOfWork]:
        self.events.append(("enter", write, exclusive))
        try:
            with self._inner(write=write, exclusive=exclusive) as tx:
                yield tx
        finally:
            self.events.append(("exit", write, exclusive))


def make_deps(
    uow: UnitOfWorkFactory, *, trace: TraceSink | None = None, limits: Limits | None = None
) -> tuple[GraphDeps, list[str]]:
    touched: list[str] = []

    def t(name: str) -> Any:
        return cast(Any, Tripwire(name, touched))

    deps = GraphDeps(
        gateway=t("gateway"),
        retrieval=t("retrieval"),
        uow=uow,
        identity=t("identity"),
        scheduling=t("scheduling"),
        handoff=t("handoff"),
        brief=t("brief"),
        demo=t("demo"),
        limits=limits or Limits(),
        trace=trace if trace is not None else t("trace"),
        specialists=t("specialists"),
        cases=t("cases"),
        ledger=t("ledger"),
    )
    return deps, touched


def run_node(state: ConversationState, ctx: TurnContext, deps: GraphDeps) -> LoadContextUpdate:
    return load_context(state, Runtime(context=ctx), deps=deps)


def connection_of(tx: UnitOfWork) -> sqlite3.Connection:
    """The adapter's open connection (AEA-10 property; not on the DO-4 Protocol), for test seeding only."""
    return cast(sqlite3.Connection, cast(Any, tx).connection)


def seed_conversation(tx: UnitOfWork, thread_id: ThreadId, *, at: datetime) -> None:
    tx.core.conversations.insert(
        ConversationRow(
            thread_id=thread_id,
            demo_session=DEMO_SESSION,
            run_tag="live",
            agent_version="test",
            started_at=at,
        )
    )


def add_line(
    tx: UnitOfWork,
    thread_id: ThreadId,
    role: str,
    text: str,
    at: datetime,
    *,
    turn_id: TurnId | None = None,
    kind: str | None = None,
) -> int:
    return tx.core.messages.append(thread_id, role, text, at, turn_id=turn_id, kind=kind)


def wp4f_moved(thread_id: ThreadId, turn3: TurnId) -> CompletedAction:
    return CompletedAction(
        key=ActionKey(thread_id=thread_id, turn_id=turn3, kind=ActionKind.MOVED, record_id="159"),
        kind=ActionKind.MOVED,
        records={"appointment": "159", "slot": "56", "old_slot": "159"},
        before={"date": "2026-10-22", "window": "08:00-12:00", "technician": "Marta Kowalski"},
        after={
            "date": "2026-10-19",
            "window": "08:00-12:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "Diagnostic fee: waived for members",
        },
        at=DEMO_START + timedelta(minutes=3),
    )


def seed_identity(
    tx: UnitOfWork,
    thread_id: ThreadId,
    *,
    status: str,
    customer_id: str | None,
    verified_at: datetime | None,
    updated_at: datetime,
    codes: Sequence[tuple[datetime, datetime, int]] = (),
) -> None:
    connection_of(tx).execute(
        "INSERT INTO identity_threads (thread_id, status, customer_id, masked_hint, channel, verified_at, "
        "updated_at) VALUES (?, ?, ?, 'the phone ending in 01', 'phone', ?, ?)",
        (
            str(thread_id),
            status,
            customer_id,
            None if verified_at is None else format_wall(verified_at),
            format_wall(updated_at),
        ),
    )
    for sent_at, expires_at, tries_left in codes:
        connection_of(tx).execute(
            "INSERT INTO identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, "
            "tries_left, used_at, inbox_message_id) "
            "VALUES (?, ?, 'hmac-placeholder-not-a-code', 'boot-test', ?, ?, ?, NULL, 1)",
            (
                str(thread_id),
                customer_id or "MHC-10001",
                format_wall(sent_at),
                format_wall(expires_at),
                tries_left,
            ),
        )


def seed_wp4f(store: TempStore) -> tuple[ThreadId, TurnId, TurnId]:
    thread, turn3, turn4 = new_thread(), new_turn(), new_turn()
    with store.uow(write=True) as tx:
        seed_conversation(tx, thread, at=DEMO_START)
        seed_identity(
            tx,
            thread,
            status="verified",
            customer_id="MHC-10001",
            verified_at=DEMO_START + timedelta(minutes=1),
            updated_at=DEMO_START + timedelta(minutes=1),
            codes=[(DEMO_START, DEMO_START + timedelta(minutes=10), 2)],
        )
        add_line(
            tx,
            thread,
            "customer",
            "Can you move it to Monday morning instead?",
            DEMO_START + timedelta(minutes=2),
            turn_id=turn3,
            kind="text",
        )
        add_line(
            tx,
            thread,
            "assistant",
            "Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta.",
            DEMO_START + timedelta(minutes=3),
            turn_id=turn3,
            kind="text",
        )
        add_line(
            tx,
            thread,
            "customer",
            "Great, so I'm all set for Monday?",
            DEMO_START + timedelta(minutes=5),
            turn_id=turn4,
            kind="text",
        )
        tx.core.actions.record(wp4f_moved(thread, turn3))
        tx.commit()
    return thread, turn3, turn4


def seed_twenty_turns(
    store: TempStore, thread: ThreadId, *, long_turn: int | None = None, rep_after: int | None = None
) -> list[TurnId]:
    turns: list[TurnId] = []
    with store.uow(write=True) as tx:
        for i in range(1, 21):
            t = new_turn()
            turns.append(t)
            at = DEMO_START + i * timedelta(minutes=1)
            add_line(tx, thread, "customer", f"Question number {i:02d} about my visit.", at, turn_id=t)
            if i == rep_after:
                add_line(
                    tx,
                    thread,
                    "representative",
                    "Riley here, I can help with that.",
                    at + timedelta(seconds=5),
                )
            reply = "A" * 900 if i == long_turn else f"Answer number {i:02d}."
            add_line(tx, thread, "assistant", reply, at + timedelta(seconds=10), turn_id=t)
        tx.commit()
    return turns


def count_rows(store: TempStore, table: str) -> int:
    if table not in _COUNTED:
        raise ValueError("table is not one of the counted tables")
    with store.uow() as tx:
        row = connection_of(tx).execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # noqa: S608 - fixed tuple
    return int(row[0])
