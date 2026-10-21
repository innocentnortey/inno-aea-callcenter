"""J-4 (slice plan section 0a), extended by AEA-28.

Level today: mock-tested (real SchedulingService and scheduling_tools executors on a temp SQLite copy; no server, no
dispatcher, no graph). The integrated steps (a CON-2 submitTurn on AEA-57's harness with the scripted model, dispatch's
lookup rows, compose) are blocked by AEA-40 (submitTurn, TurnService) and AEA-51 (integrated turn).
"""

from __future__ import annotations

import datetime as dt
import hashlib
from collections.abc import Iterator
from zoneinfo import ZoneInfo

import pytest

from meridian.agent.tools.scheduling import (
    MoveVisitArgs,
    RequestVisitChangeArgs,
    scheduling_tools,
)
from meridian.domain.common import CustomerId, RequestId, ThreadId, ToolErrorCode, TurnId
from meridian.domain.tools import ToolCallScope, ToolError, ToolResult
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


def test_j4_fee_bearing_change_inside_24h_wp4(store: TempStore) -> None:
    with store.uow() as tx:
        before_appt = tx.booking.appointments.get(1)
        before_slots = {i: tx.booking.slots.get_for_update(i) for i in (2, 44, 61)}
    sc = _scope(store, 1, 1, MHC_57204, {44, 61})
    moved = _run(store, "move_visit", MoveVisitArgs(appointment_id=1, new_slot_id=44), sc)
    assert isinstance(moved.for_model, ToolError)
    assert moved.for_model.code == ToolErrorCode.FEE_BEARING
    assert "2.0 hours" in moved.for_model.message
    req = _run(
        store,
        "request_visit_change",
        RequestVisitChangeArgs(appointment_id=1, change="move", wanted_text="Monday morning"),
        _scope(store, 1, 2, MHC_57204, {44, 61}),
    )
    assert req.ok
    draft = req.captured.change_request  # type: ignore[union-attr]
    assert draft is not None
    assert draft.hours_before == 2.0
    assert draft.window_start == dt.datetime(2026, 10, 16, 12, 0, tzinfo=CHI)
    assert draft.windows_shown == (44, 61)
    with store.uow() as tx:
        assert tx.booking.appointments.get(1) == before_appt
        assert {i: tx.booking.slots.get_for_update(i) for i in (2, 44, 61)} == before_slots
        assert before_slots[44] is not None and before_slots[44].status == "open"
        actions = tx.core.actions.for_thread(sc.ids.thread_id)
        rows = tx.core.lookup_log.for_thread(sc.ids.thread_id)
        visit = tx.core.settled_for(sc.ids.thread_id, NOW).current_visit()
    assert [a.kind.value for a in actions] == ["change_request_sent"]
    assert actions[0].after is not None and "$49" in actions[0].after["fee_line"]
    assert len(rows) == 1
    assert visit is None


@pytest.mark.skip(
    reason="blocked-on AEA-40, AEA-51: integrated CON-2 turn (submitTurn) with the scripted model"
)
def test_j4_change_request_turn_integrated() -> None:
    """WP-4 on MHC-57204 at the 2026-10-16 10:00 demo clock: the reply says the $49 fee applies and the original
    appointment stays; appointment 1 and slot 2 are unchanged; one change_request_sent action is stored."""
