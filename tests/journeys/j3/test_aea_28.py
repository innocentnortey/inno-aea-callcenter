"""J-3 (slice plan section 0a), extended by AEA-28.

Level today: mock-tested (real SchedulingService and scheduling_tools executors on a temp SQLite copy; no server, no
dispatcher, no graph). The integrated steps (a CON-2 submitTurn on AEA-57's harness with the scripted model, dispatch's
lookup rows, compose) are blocked by AEA-40 (submitTurn, TurnService) and AEA-51 (integrated turn).
"""

from __future__ import annotations

import datetime as dt
import hashlib
from collections.abc import Iterator
from datetime import date
from typing import Any, cast
from zoneinfo import ZoneInfo

import pytest

from meridian.agent.tools.scheduling import (
    BookVisitArgs,
    FindWindowsArgs,
    MoveVisitArgs,
    scheduling_tools,
)
from meridian.domain.common import CustomerId, RequestId, ThreadId, TurnId
from meridian.domain.tools import ToolCallScope, ToolResult
from meridian.domain.turn import TurnIds
from meridian.policy.limits import Limits
from meridian.services.scheduling import SchedulingService
from tests.fixtures.sqlite import ISSUED_DB, TempStore, temp_sqlite

pytestmark = pytest.mark.journey

CHI = ZoneInfo("America/Chicago")
NOW = dt.datetime(2026, 10, 16, 10, 0, tzinfo=CHI)
LINDA = CustomerId("MHC-10001")
MHC_57204 = CustomerId("MHC-57204")


@pytest.fixture
def store() -> Iterator[TempStore]:
    before = hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest()
    with temp_sqlite() as s:
        yield s
    assert hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest() == before


def _scope(
    store: TempStore, thread: int, turn: int, who: CustomerId | None, shown: set[int]
) -> ToolCallScope:
    th = ThreadId(f"a0000000-0000-4000-8000-{thread:012d}")
    with store.uow(write=True) as tx:
        mid = tx.core.messages.append(th, "customer", "synthetic message", NOW)
        tx.commit()
    ids = TurnIds(
        thread_id=th,
        turn_id=TurnId(f"b0000000-0000-4000-8000-{turn:012d}"),
        request_id=RequestId("c0000000-0000-4000-8000-000000000001"),
        run_tag="live",
        run_id=None,
        agent_version="test",
    )
    return ToolCallScope(ids=ids, customer_id=who, shown_slot_ids=frozenset(shown), now=NOW, message_id=mid)


def _run(store: TempStore, name: str, args: object, sc: ToolCallScope) -> ToolResult:
    defs = {d.name: d for d in scheduling_tools(SchedulingService(store.uow, Limits().booking))}
    return defs[name].executor(args, sc)  # type: ignore[arg-type]


def test_j3_booking_confirmation_and_follow_up_memory(store: TempStore) -> None:
    # Turn 1 (WP-3): Linda asks for Saturday 4 to 7; nothing fits, the earliest alternatives come back.
    sc1 = _scope(store, 1, 1, LINDA, set())
    found = _run(
        store,
        "find_windows",
        FindWindowsArgs(
            service_type="hvac_repair",
            earliest=date(2026, 10, 17),
            latest=date(2026, 10, 17),
            window="16:00-19:00",
        ),
        sc1,
    )
    assert isinstance(found.for_model, dict)
    assert found.for_model["exact_fit"] is False
    windows = cast(list[dict[str, Any]], found.for_model["windows"])
    assert [w["slot_id"] for w in windows] == [56, 42, 58]
    # Turn 2: she picks slot 56.
    sc2 = _scope(store, 1, 2, LINDA, {56, 42, 58})
    booked = _run(store, "book_visit", BookVisitArgs(slot_id=56, issue="AC not cooling"), sc2)
    assert booked.ok and isinstance(booked.for_model, dict)
    with store.uow() as tx:
        assert tx.booking.slots.get_for_update(56) is not None
        assert tx.booking.slots.get_for_update(56).status == "booked"  # type: ignore[union-attr]
        (appt,) = [a for a in tx.booking.appointments.for_customer(LINDA) if a.slot_id == 56]
        assert appt.appointment_id == 160
        (action,) = tx.core.actions.for_thread(sc2.ids.thread_id)
        assert action.key.turn_id == sc2.ids.turn_id
        (row,) = tx.core.lookup_log.for_thread(sc2.ids.thread_id)
        assert row.message_id == sc2.message_id
        # Turn 3: the follow-up reads what is stored.
        visit = tx.core.settled_for(sc2.ids.thread_id, NOW).current_visit()
    assert visit is not None
    assert (visit.date, visit.window, visit.technician, visit.status) == (
        date(2026, 10, 19),
        "08:00-12:00",
        "Marta Kowalski",
        "booked",
    )
    assert visit.fee_line == booked.for_model["fee_line"]


def test_j3_fee_free_move_wp4f(store: TempStore) -> None:
    sc = _scope(store, 2, 1, MHC_57204, {53})
    r = _run(store, "move_visit", MoveVisitArgs(appointment_id=94, new_slot_id=53), sc)
    assert r.ok
    with store.uow() as tx:
        appt = tx.booking.appointments.get(94)
        assert appt is not None and appt.slot_id == 53
        old = tx.booking.slots.get_for_update(189)
        assert old is not None and old.status == "open"
        visit = tx.core.settled_for(sc.ids.thread_id, NOW).current_visit()
    assert visit is not None
    assert visit.status == "moved" and visit.date == date(2026, 10, 19)


@pytest.mark.skip(
    reason="blocked-on AEA-40, AEA-51: integrated CON-2 turn (submitTurn) with the scripted model"
)
def test_j3_booking_turn_integrated() -> None:
    """On AEA-57's `journey` fixture: login, startChatSession, verify MHC-10001, submitTurn asking for Saturday 4-7,
    then a slot card choice for slot 56; assert the reply shows date, window, technician and the waived diagnostic
    fee line, and the DB holds slot 56 booked, one appointment, one actions(booked) row and its lookup_log row."""
