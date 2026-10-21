"""Shared helpers for the AEA-28 scheduling tests (no test functions here)."""

from __future__ import annotations

import datetime as dt
import hashlib
import sqlite3
from collections.abc import Iterable
from zoneinfo import ZoneInfo

from meridian.domain.actions import ActionKey, ActionKind
from meridian.domain.common import CustomerId, RequestId, ThreadId, TurnId
from meridian.domain.tools import LookupEntry, ToolCallScope
from meridian.domain.turn import TurnIds
from meridian.policy.limits import BookingLimits, Limits
from meridian.services.scheduling import SchedulingService
from tests.fixtures.sqlite import ISSUED_DB, TempStore

CHI = ZoneInfo("America/Chicago")
NOW = dt.datetime(2026, 10, 16, 10, 0, tzinfo=CHI)  # WP-4 demo clock (worked-pairs header)
LINDA = CustomerId("MHC-10001")
OMAR = CustomerId("MHC-10002")
MHC_57204 = CustomerId("MHC-57204")
REQUEST = RequestId("c0000000-0000-4000-8000-000000000001")


def thread(n: int) -> ThreadId:
    return ThreadId(f"a0000000-0000-4000-8000-{n:012d}")


def turn(n: int) -> TurnId:
    return TurnId(f"b0000000-0000-4000-8000-{n:012d}")


def ids(th: ThreadId, tu: TurnId) -> TurnIds:
    return TurnIds(
        thread_id=th, turn_id=tu, request_id=REQUEST, run_tag="live", run_id=None, agent_version="test"
    )


def seed_message(store: TempStore, th: ThreadId) -> int:
    with store.uow(write=True) as tx:
        mid = tx.core.messages.append(th, "customer", "synthetic message", NOW)
        tx.commit()
    return mid


def scope(
    store: TempStore,
    th: ThreadId,
    tu: TurnId,
    customer: CustomerId | None,
    shown: Iterable[int] = (),
    now: dt.datetime = NOW,
) -> ToolCallScope:
    return ToolCallScope(
        ids=ids(th, tu),
        customer_id=customer,
        shown_slot_ids=frozenset(shown),
        now=now,
        message_id=seed_message(store, th),
    )


def entry(
    sc: ToolCallScope, tool: str = "test_tool", record_ids: tuple[str, ...] = (), result_seen: str = "test"
) -> LookupEntry:
    return LookupEntry(
        tool=tool,
        record_ids=record_ids,
        passage_ids=(),
        result_seen=result_seen,
        message_id=sc.message_id,
        turn_id=sc.ids.turn_id,
    )


def key(sc: ToolCallScope, kind: ActionKind, record_id: str) -> ActionKey:
    return ActionKey(thread_id=sc.ids.thread_id, turn_id=sc.ids.turn_id, kind=kind, record_id=record_id)


def service(store: TempStore, cap: int | None = None) -> SchedulingService:
    booking = Limits().booking if cap is None else BookingLimits(max_per_conversation=cap)
    return SchedulingService(store.uow, booking)


def raw(store: TempStore) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{store.db_path}?mode=ro", uri=True)


_DIGEST_SQL = (
    "SELECT * FROM appointment_slots ORDER BY 1",
    "SELECT * FROM appointments ORDER BY 1",
    "SELECT * FROM actions ORDER BY 1",
    "SELECT * FROM lookup_log ORDER BY 1",
)


def row_digest(store: TempStore) -> str:
    h = hashlib.sha256()
    conn = raw(store)
    try:
        for sql in _DIGEST_SQL:
            h.update(repr(conn.execute(sql).fetchall()).encode())
    finally:
        conn.close()
    return h.hexdigest()


def slot_row(store: TempStore, slot_id: int) -> tuple[object, ...]:
    conn = raw(store)
    try:
        return tuple(conn.execute("SELECT * FROM appointment_slots WHERE slot_id = ?", (slot_id,)).fetchone())
    finally:
        conn.close()


def appt_row(store: TempStore, appointment_id: int) -> tuple[object, ...]:
    conn = raw(store)
    try:
        return tuple(
            conn.execute("SELECT * FROM appointments WHERE appointment_id = ?", (appointment_id,)).fetchone()
        )
    finally:
        conn.close()


def count(store: TempStore, sql: str, params: tuple[object, ...] = ()) -> int:
    conn = raw(store)
    try:
        return int(conn.execute(sql, params).fetchone()[0])
    finally:
        conn.close()


def issued_sha256() -> str:
    return hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest()
