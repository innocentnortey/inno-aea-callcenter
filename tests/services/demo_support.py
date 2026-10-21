"""Helpers for the AEA-30 demo and scheduler tests: builders, raw row readers, CaseService doubles. Not collected."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import TypeAdapter

from meridian.adapters.sqlite.rows import (
    CaseRow,
    ConversationRow,
    EventRow,
    StreamEvent,
    thread_stream,
)
from meridian.domain.common import CaseRef, CustomerId, RequestId, ThreadId
from meridian.domain.handoff import HandoffReason, Priority, Promise
from meridian.domain.staff import StaffRole
from meridian.policy.texts import TEXTS, TextId
from meridian.ports.runtime import UnitOfWork
from meridian.services.demo import DemoClock, DemoService
from tests.fakes.clock import CHICAGO
from tests.fixtures.sqlite import TempStore

THREAD: TypeAdapter[ThreadId] = TypeAdapter(ThreadId)
CASE_REF: TypeAdapter[CaseRef] = TypeAdapter(CaseRef)
REQUEST: TypeAdapter[RequestId] = TypeAdapter(RequestId)
CUSTOMER: TypeAdapter[CustomerId] = TypeAdapter(CustomerId)

DEFAULT_WALL = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)
_TABLES = ("job_runs", "demo_events", "case_events", "events", "promises", "demo_state", "conversations")


def chi(y: int, m: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=CHICAGO)


def new_thread_id() -> ThreadId:
    return THREAD.validate_python(str(uuid4()))


def new_request_id() -> RequestId:
    return REQUEST.validate_python(str(uuid4()))


class WallClock:
    """A small mutable wall clock (UTC only); `now` is the attribute tests move."""

    def __init__(self, now: datetime = DEFAULT_WALL) -> None:
        self.now = now

    @property
    def now(self) -> datetime:
        return self._now

    @now.setter
    def now(self, value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None or value.utcoffset() != UTC.utcoffset(None):
            raise ValueError("WallClock needs a UTC datetime")
        self._now = value

    def __call__(self) -> datetime:
        return self._now


def rows(store: TempStore, table: str) -> list[dict[str, Any]]:
    if table not in _TABLES:
        raise ValueError("table not allowed")
    conn = sqlite3.connect(store.db_path)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(f"SELECT * FROM {table}")]  # noqa: S608
    finally:
        conn.close()


def count(store: TempStore, table: str) -> int:
    return len(rows(store, table))


def add_conversation(
    store: TempStore,
    *,
    run_tag: str = "live",
    outcome: str = "open",
    last_customer_wall_at: datetime | None = None,
    live_state: str = "not_live",
) -> ThreadId:
    from meridian.adapters.sqlite.repos_cases import DEMO_START

    tid = new_thread_id()
    row = ConversationRow.model_validate(
        {
            "thread_id": str(tid),
            "demo_session": "test-session",
            "run_tag": run_tag,
            "agent_version": "test",
            "started_at": DEMO_START,
            "outcome": outcome,
            "last_customer_wall_at": last_customer_wall_at,
            "live_state": live_state,
        }
    )
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(row)
        tx.commit()
    return tid


def add_case(
    store: TempStore,
    *,
    ref: str,
    reason: HandoffReason,
    priority: Priority,
    lifecycle: str,
    created_at: datetime,
    due_at: datetime | None,
    promise: Promise | None,
    wake_up_at: datetime | None = None,
    owner_role: StaffRole | None = None,
    thread_id: ThreadId | None = None,
    customer_id: CustomerId | None = None,
) -> CaseRow:
    tid = thread_id if thread_id is not None else add_conversation(store)
    row = CaseRow.model_validate(
        {
            "case_ref": ref,
            "thread_id": str(tid),
            "customer_id": str(customer_id) if customer_id is not None else None,
            "reason": reason,
            "priority": priority,
            "rule_id": "R24.billing_dispute",
            "trigger": "planner",
            "lifecycle": lifecycle,
            "owner_role": owner_role,
            "due_at": due_at,
            "wake_up_at": wake_up_at,
            "seed": False,
            "created_at": created_at,
            "updated_at": created_at,
        }
    )
    with store.uow(write=True) as tx:
        tx.cases.cases.insert(row)
        if promise is not None:
            tx.cases.promises.insert(CASE_REF.validate_python(ref), promise, created_at)
        tx.commit()
    return row


def set_demo(store: TempStore, *, now: datetime | None = None, staffing: str | None = None) -> None:
    with store.uow(write=True) as tx:
        if now is not None:
            tx.cases.demo_state.set_now(now)
        if staffing is not None:
            tx.cases.demo_state.set_staffing(staffing)
        tx.commit()


def stream_events(store: TempStore, thread_id: ThreadId) -> list[EventRow]:
    with store.uow() as tx:
        return list(tx.core.events.after(thread_stream(thread_id), 0))


class ConvertingCases:
    """CaseService double honouring stage7/cases section 5 for convert_live_queued."""

    def __init__(self) -> None:
        self.calls: list[tuple[datetime, UnitOfWork | None]] = []

    def convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int:
        assert tx is not None
        self.calls.append((now, tx))
        converted = 0
        for c in tx.cases.cases.list_open():
            if c.lifecycle != "live_queued":
                continue
            tx.cases.cases.update_versioned(c.case_ref, c.version, lifecycle="unassigned", updated_at=now)
            tx.core.conversations.set_live_state(c.thread_id, "not_live", None)
            tx.core.events.append(
                thread_stream(c.thread_id),
                StreamEvent(
                    type="shift_ended",
                    at=now,
                    payload={
                        "speaker": {"kind": "event", "display_name": None},
                        "line": TEXTS[TextId.SHIFT_ENDED],
                    },
                ),
            )
            converted += 1
        return converted


class RaisingCases:
    def __init__(self) -> None:
        self.calls: list[tuple[datetime, UnitOfWork | None]] = []

    def convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int:
        self.calls.append((now, tx))
        raise RuntimeError("converter failed")


def make_demo(store: TempStore, cases: Any, wall: WallClock | None = None) -> DemoService:
    return DemoService(
        store.uow, DemoClock(store.uow), cases, wall_clock=wall if wall is not None else WallClock()
    )
