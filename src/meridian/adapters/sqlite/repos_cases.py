"""Case-store repositories: cases, events, promises, follow-ups, activities, briefs, demo state, jobs, records (AEA-10).

Bodies are plain queries (cases.md 1.2). The case lifecycle, scheduler and reset rules belong to the callers
(AEA-29, 30, 31). Every sub-repository takes the unit of work's connection and never commits.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from enum import Enum
from typing import Any

from meridian.adapters.sqlite.db import (
    format_wall,
    integrity_errors,
    last_row_id,
)
from meridian.adapters.sqlite.repos_cases_state import (
    DEMO_START,
    SEED_REF_MAX,
    DemoEventsRepo,
    DemoStateRepo,
    JobRunsRepo,
    RecordsRepo,
    RefsRepo,
)
from meridian.adapters.sqlite.rows import (
    ActivityRow,
    CaseEventRow,
    CaseRow,
    DemoEventRow,
    DemoStateRow,
    FollowupRow,
    JobRunRow,
    PromiseRow,
    ResetEventRow,
    SeedEventRow,
    _dt,
    _j,
    _w,
)
from meridian.domain.common import CaseRef, CustomerId, ThreadId
from meridian.domain.handoff import Brief, Promise

__all__ = [
    "CLOSED_LIFECYCLES",
    "DEMO_START",
    "SEED_REF_MAX",
    "ActivitiesRepo",
    "ActivityRow",
    "BriefsRepo",
    "CaseEventRow",
    "CaseEventsRepo",
    "CaseRepos",
    "CaseRow",
    "CasesRepo",
    "DemoEventRow",
    "DemoEventsRepo",
    "DemoStateRepo",
    "DemoStateRow",
    "FollowupRow",
    "FollowupsRepo",
    "JobRunRow",
    "JobRunsRepo",
    "PromiseRow",
    "PromisesRepo",
    "RecordsRepo",
    "RefsRepo",
    "ResetEventRow",
    "SeedEventRow",
]

CLOSED_LIFECYCLES = ("resolved", "closed_unresolved")

_CASE_COLS = (
    "case_ref, thread_id, turn_id, customer_id, reason, priority, rule_id, handoff_trigger, lifecycle, owner_role, "
    "owner_since, due_at, wake_up_at, version, seed, safety_kind, change_request_json, alert, created_at, "
    "updated_at, resolved_at, queued_at"
)
_UPDATABLE = frozenset(
    {
        "lifecycle",
        "owner_role",
        "owner_since",
        "due_at",
        "wake_up_at",
        "priority",
        "reason",
        "resolved_at",
        "queued_at",
        "alert",
        "customer_id",
        "updated_at",
    }
)
_CLOSED_SQL = "('resolved','closed_unresolved')"


def _case(r: tuple[Any, ...]) -> CaseRow:
    return CaseRow.model_validate(
        {
            "case_ref": r[0],
            "thread_id": r[1],
            "turn_id": r[2],
            "customer_id": r[3],
            "reason": r[4],
            "priority": r[5],
            "rule_id": r[6],
            "trigger": r[7],
            "lifecycle": r[8],
            "owner_role": r[9],
            "owner_since": _dt(r[10]),
            "due_at": _dt(r[11]),
            "wake_up_at": _dt(r[12]),
            "version": r[13],
            "seed": bool(r[14]),
            "safety_kind": r[15],
            "change_request": None if r[16] is None else json.loads(r[16]),
            "alert": r[17],
            "created_at": _dt(r[18]),
            "updated_at": _dt(r[19]),
            "resolved_at": _dt(r[20]),
            "queued_at": _dt(r[21]),
        }
    )


def _value(v: object) -> object:
    if isinstance(v, datetime):
        return format_wall(v)
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, bool):
        return int(v)
    return v


class CasesRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, row: CaseRow) -> None:
        with integrity_errors("cases"):
            self._conn.execute(
                f"INSERT INTO cases ({_CASE_COLS}) VALUES ({','.join('?' * 22)})",  # noqa: S608 - constant column list, "?" marks
                (
                    str(row.case_ref),
                    str(row.thread_id),
                    None if row.turn_id is None else str(row.turn_id),
                    None if row.customer_id is None else str(row.customer_id),
                    row.reason.value,
                    row.priority.value,
                    row.rule_id,
                    row.trigger,
                    row.lifecycle,
                    None if row.owner_role is None else row.owner_role.value,
                    _w(row.owner_since),
                    _w(row.due_at),
                    _w(row.wake_up_at),
                    row.version,
                    int(row.seed),
                    row.safety_kind,
                    None if row.change_request is None else _j(row.change_request),
                    row.alert,
                    format_wall(row.created_at),
                    format_wall(row.updated_at),
                    _w(row.resolved_at),
                    _w(row.queued_at),
                ),
            )

    def get(self, case_ref: CaseRef) -> CaseRow | None:
        r = self._conn.execute(
            f"SELECT {_CASE_COLS} FROM cases WHERE case_ref = ?",  # noqa: S608 - constant column list
            (str(case_ref),),
        ).fetchone()
        return None if r is None else _case(r)

    def get_for_thread_open(self, thread_id: ThreadId) -> CaseRow | None:
        """The newest non-closed case of the thread."""
        r = self._conn.execute(
            f"SELECT {_CASE_COLS} FROM cases WHERE thread_id = ? AND lifecycle NOT IN {_CLOSED_SQL} "  # noqa: S608 - constants only
            "ORDER BY created_at DESC, case_ref DESC LIMIT 1",
            (str(thread_id),),
        ).fetchone()
        return None if r is None else _case(r)

    def list_open(self) -> tuple[CaseRow, ...]:
        rows = self._conn.execute(
            f"SELECT {_CASE_COLS} FROM cases WHERE lifecycle NOT IN {_CLOSED_SQL} ORDER BY created_at, case_ref"  # noqa: S608 - constants only
        ).fetchall()
        return tuple(_case(r) for r in rows)

    def list_for_thread(self, thread_id: ThreadId) -> tuple[CaseRow, ...]:
        rows = self._conn.execute(
            f"SELECT {_CASE_COLS} FROM cases WHERE thread_id = ? ORDER BY created_at, case_ref",  # noqa: S608 - constant column list
            (str(thread_id),),
        ).fetchall()
        return tuple(_case(r) for r in rows)

    def list_for_customer(self, customer_id: CustomerId) -> tuple[CaseRow, ...]:
        rows = self._conn.execute(
            f"SELECT {_CASE_COLS} FROM cases WHERE customer_id = ? ORDER BY created_at, case_ref",  # noqa: S608 - constant column list
            (str(customer_id),),
        ).fetchall()
        return tuple(_case(r) for r in rows)

    def update_versioned(self, case_ref: CaseRef, expected_version: int, **changes: object) -> int | None:
        """One UPDATE that bumps the version; the new version, or None when no row matched (stale or unknown)."""
        if not changes:
            raise ValueError("no changes")
        if not set(changes) <= _UPDATABLE:
            raise ValueError("unknown case column")
        sets = ", ".join(f"{k} = ?" for k in changes)
        cur = self._conn.execute(
            f"UPDATE cases SET {sets}, version = version + 1 WHERE case_ref = ? AND version = ?",  # noqa: S608 - keys come from the allow-list
            (*(_value(v) for v in changes.values()), str(case_ref), expected_version),
        )
        return expected_version + 1 if cur.rowcount else None


class CaseEventsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, event: CaseEventRow) -> int:
        with integrity_errors("case_events"):
            cur = self._conn.execute(
                "INSERT INTO case_events (case_ref, kind, event_key, actor_role, job_run_id, detail_json, at) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    str(event.case_ref),
                    event.kind,
                    event.key,
                    event.actor_role,
                    event.job_run_id,
                    _j(event.detail),
                    format_wall(event.at),
                ),
            )
        return last_row_id(cur, "case_events")

    def exists(self, case_ref: CaseRef, kind: str, key: str) -> bool:
        r = self._conn.execute(
            "SELECT 1 FROM case_events WHERE case_ref = ? AND kind = ? AND event_key = ?",
            (str(case_ref), kind, key),
        ).fetchone()
        return r is not None

    def list_for_case(self, case_ref: CaseRef) -> tuple[CaseEventRow, ...]:
        rows = self._conn.execute(
            "SELECT id, case_ref, kind, event_key, actor_role, job_run_id, detail_json, at FROM case_events "
            "WHERE case_ref = ? ORDER BY id",
            (str(case_ref),),
        ).fetchall()
        return tuple(
            CaseEventRow.model_validate(
                {
                    "id": r[0],
                    "case_ref": r[1],
                    "kind": r[2],
                    "key": r[3],
                    "actor_role": r[4],
                    "job_run_id": r[5],
                    "detail": json.loads(r[6]),
                    "at": _dt(r[7]),
                }
            )
            for r in rows
        )


_PROMISE_COLS = (
    "id, case_ref, policy_row, text, due_at, due_label, extra_lines, live_queued, status, created_at, "
    "status_at, status_reason"
)


def _promise(r: tuple[Any, ...]) -> PromiseRow:
    return PromiseRow.model_validate(
        {
            "id": r[0],
            "case_ref": r[1],
            "promise": Promise.model_validate(
                {
                    "policy_row": r[2],
                    "text": r[3],
                    "due_at": _dt(r[4]),
                    "due_label": r[5],
                    "extra_lines": tuple(json.loads(r[6])),
                    "live_queued": bool(r[7]),
                }
            ),
            "status": r[8],
            "created_at": _dt(r[9]),
            "status_at": _dt(r[10]),
            "status_reason": r[11],
        }
    )


class PromisesRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, case_ref: CaseRef, promise: Promise, at: datetime) -> int:
        with integrity_errors("promises"):
            cur = self._conn.execute(
                "INSERT INTO promises (case_ref, policy_row, text, due_at, due_label, extra_lines, live_queued, "
                "status, created_at) VALUES (?,?,?,?,?,?,?,'open',?)",
                (
                    str(case_ref),
                    promise.policy_row,
                    promise.text,
                    _w(promise.due_at),
                    promise.due_label,
                    _j(list(promise.extra_lines)),
                    int(promise.live_queued),
                    format_wall(at),
                ),
            )
        return last_row_id(cur, "promises")

    def current(self, case_ref: CaseRef) -> PromiseRow | None:
        r = self._conn.execute(
            f"SELECT {_PROMISE_COLS} FROM promises WHERE case_ref = ? ORDER BY id DESC LIMIT 1",  # noqa: S608 - constant column list
            (str(case_ref),),
        ).fetchone()
        return None if r is None else _promise(r)

    def history(self, case_ref: CaseRef) -> tuple[PromiseRow, ...]:
        rows = self._conn.execute(
            f"SELECT {_PROMISE_COLS} FROM promises WHERE case_ref = ? ORDER BY id",  # noqa: S608 - constant column list
            (str(case_ref),),
        ).fetchall()
        return tuple(_promise(r) for r in rows)

    def set_status(self, case_ref: CaseRef, status: str, at: datetime, reason: str) -> bool:
        """Updates the current row only; False when the case has no promise."""
        with integrity_errors("promises"):
            cur = self._conn.execute(
                "UPDATE promises SET status = ?, status_at = ?, status_reason = ? WHERE case_ref = ? "
                "AND id = (SELECT MAX(id) FROM promises WHERE case_ref = ?)",
                (status, format_wall(at), reason, str(case_ref), str(case_ref)),
            )
        return cur.rowcount > 0

    def list_open_past(self, now: datetime) -> list[PromiseRow]:
        rows = self._conn.execute(
            f"SELECT {_PROMISE_COLS} FROM promises WHERE status = 'open' AND due_at IS NOT NULL AND due_at < ? "  # noqa: S608 - constant column list
            "AND id = (SELECT MAX(p2.id) FROM promises p2 WHERE p2.case_ref = promises.case_ref) ORDER BY due_at, id",
            (format_wall(now),),
        ).fetchall()
        return [_promise(r) for r in rows]


class FollowupsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def upsert(self, row: FollowupRow) -> None:
        with integrity_errors("followups"):
            self._conn.execute(
                "INSERT INTO followups (case_ref, thread_id, channel, destination_label, destination, on_record, "
                "contact_window, saved_line, updated_at) VALUES (?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(case_ref) DO UPDATE SET thread_id = excluded.thread_id, channel = excluded.channel, "
                "destination_label = excluded.destination_label, destination = excluded.destination, "
                "on_record = excluded.on_record, contact_window = excluded.contact_window, "
                "saved_line = excluded.saved_line, updated_at = excluded.updated_at",
                (
                    str(row.case_ref),
                    str(row.thread_id),
                    row.channel,
                    row.destination_label,
                    row.destination,
                    int(row.on_record),
                    row.window,
                    row.saved_line,
                    format_wall(row.updated_at),
                ),
            )

    def get(self, case_ref: CaseRef) -> FollowupRow | None:
        r = self._conn.execute(
            "SELECT case_ref, thread_id, channel, destination_label, destination, on_record, contact_window, "
            "saved_line, updated_at FROM followups WHERE case_ref = ?",
            (str(case_ref),),
        ).fetchone()
        if r is None:
            return None
        return FollowupRow.model_validate(
            {
                "case_ref": r[0],
                "thread_id": r[1],
                "channel": r[2],
                "destination_label": r[3],
                "destination": r[4],
                "on_record": bool(r[5]),
                "window": r[6],
                "saved_line": r[7],
                "updated_at": _dt(r[8]),
            }
        )


class ActivitiesRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, row: ActivityRow) -> int:
        with integrity_errors("activities"):
            cur = self._conn.execute(
                "INSERT INTO activities (case_ref, kind, outcome, note, actor_role, at) VALUES (?,?,?,?,?,?)",
                (
                    str(row.case_ref),
                    row.kind,
                    row.outcome,
                    row.note,
                    row.actor_role.value,
                    format_wall(row.at),
                ),
            )
        return last_row_id(cur, "activities")

    def list_for_case(self, case_ref: CaseRef) -> tuple[ActivityRow, ...]:
        rows = self._conn.execute(
            "SELECT id, case_ref, kind, outcome, note, actor_role, at FROM activities WHERE case_ref = ? "
            "ORDER BY at, id",
            (str(case_ref),),
        ).fetchall()
        return tuple(
            ActivityRow.model_validate(
                {
                    "id": r[0],
                    "case_ref": r[1],
                    "kind": r[2],
                    "outcome": r[3],
                    "note": r[4],
                    "actor_role": r[5],
                    "at": _dt(r[6]),
                }
            )
            for r in rows
        )


class BriefsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def upsert(self, brief: Brief, at: datetime) -> None:
        """Replaces the stored brief of ``brief.case_ref``."""
        with integrity_errors("case_briefs"):
            self._conn.execute(
                "INSERT INTO case_briefs (case_ref, thread_id, status, brief_json, updated_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(case_ref) DO UPDATE SET thread_id = excluded.thread_id, status = excluded.status, "
                "brief_json = excluded.brief_json, updated_at = excluded.updated_at",
                (
                    str(brief.case_ref),
                    str(brief.thread_id),
                    brief.status,
                    brief.model_dump_json(),
                    format_wall(at),
                ),
            )

    def get(self, case_ref: CaseRef) -> Brief | None:
        r = self._conn.execute(
            "SELECT brief_json FROM case_briefs WHERE case_ref = ?", (str(case_ref),)
        ).fetchone()
        return None if r is None else Brief.model_validate_json(r[0])


class CaseRepos:
    """Repositories for 60_cases; body AEA-10 (cases.md 1.2)."""

    cases: CasesRepo
    case_events: CaseEventsRepo
    promises: PromisesRepo
    followups: FollowupsRepo
    activities: ActivitiesRepo
    briefs: BriefsRepo
    demo_state: DemoStateRepo
    demo_events: DemoEventsRepo
    job_runs: JobRunsRepo
    records: RecordsRepo
    refs: RefsRepo

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.cases = CasesRepo(conn)
        self.case_events = CaseEventsRepo(conn)
        self.promises = PromisesRepo(conn)
        self.followups = FollowupsRepo(conn)
        self.activities = ActivitiesRepo(conn)
        self.briefs = BriefsRepo(conn)
        self.demo_state = DemoStateRepo(conn)
        self.demo_events = DemoEventsRepo(conn)
        self.job_runs = JobRunsRepo(conn)
        self.records = RecordsRepo(conn)
        self.refs = RefsRepo(conn)
