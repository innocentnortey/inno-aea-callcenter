"""SchedulingSlice.pending_change and StateFlags.pending_change share one source (FU-pending-change; WP-4, WP-4F)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

import pytest

from meridian.agent.nodes.act import build_specialist_task
from meridian.agent.nodes.plan import build_planner_input
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.specialists import SchedulingSlice
from meridian.domain.state import ConversationState
from meridian.domain.turn import TaskIntent
from meridian.policy.limits import Limits
from tests.fakes import WORKED_PAIRS_NOW
from tests.graph._spine_doubles import THREAD
from tests.unit.agent.nodes.act_fixtures import T1, WP4_INPUTS, act_ctx, make_state, task

LIMITS = Limits()
T0 = WORKED_PAIRS_NOW - dt.timedelta(minutes=30)
APPT = "1"  # WP4_APPOINTMENT.appointment_id
OTHER_APPT = "2"
FIVE = dt.timedelta(minutes=5)


def _key(kind: ActionKind, record: str) -> ActionKey:
    return ActionKey(thread_id=THREAD, turn_id=T1, kind=kind, record_id=record)


def _booked(appointment: str = APPT, *, at: dt.datetime = T0) -> CompletedAction:
    return CompletedAction(
        key=_key(ActionKind.BOOKED, appointment),
        kind=ActionKind.BOOKED,
        records={"appointment": appointment, "slot": "60"},
        after={
            "date": "2026-10-16",
            "window": "12:00-16:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "fee line (fixture)",
        },
        at=at,
    )


def _change_request(appointment: str = APPT, *, at: dt.datetime) -> CompletedAction:
    return CompletedAction(
        key=_key(ActionKind.CHANGE_REQUEST_SENT, appointment),
        kind=ActionKind.CHANGE_REQUEST_SENT,
        records={"appointment": appointment},
        after={"change": "move", "wanted_text": "Friday morning", "fee_line": "fee line (fixture)"},
        at=at,
    )


def _cancelled(appointment: str = APPT, *, at: dt.datetime) -> CompletedAction:
    return CompletedAction(
        key=_key(ActionKind.CANCELLED, appointment),
        kind=ActionKind.CANCELLED,
        records={"appointment": appointment},
        at=at,
    )


def _state(*actions: CompletedAction, settled: bool = True) -> ConversationState:
    base = make_state(text="Can you move it to Friday instead?")
    value = Settled(actions=actions, open_case=None, read_at=WORKED_PAIRS_NOW) if settled else None
    return base.model_copy(update={"settled": value})


def _slice_flag(state: ConversationState) -> bool:
    built = build_specialist_task(
        task(1, "scheduling", TaskIntent.RESCHEDULE), state, act_ctx(), scheduling=WP4_INPUTS, limits=LIMITS
    )
    assert isinstance(built.slice, SchedulingSlice)
    return built.slice.pending_change


_CASES: dict[str, Callable[[], ConversationState]] = {
    "wp4_request_filed": lambda: _state(_booked(), _change_request(at=T0 + FIVE)),
    "wp4f_booked_only": lambda: _state(_booked()),
    "no_actions": lambda: _state(),
    "settled_none": lambda: _state(settled=False),
    "cancelled_after_request": lambda: _state(
        _booked(), _change_request(at=T0 + FIVE), _cancelled(at=T0 + 2 * FIVE)
    ),
    "request_for_other_appointment": lambda: _state(_booked(), _change_request(OTHER_APPT, at=T0 + FIVE)),
}
_FALSE_IDS = [i for i in _CASES if i != "wp4_request_filed"]


def test_wp4_filed_change_request_sets_slice_pending_change() -> None:
    state = _CASES["wp4_request_filed"]()
    assert _slice_flag(state) is True
    assert build_planner_input(state, LIMITS.context).flags.pending_change is True


@pytest.mark.parametrize("case", _FALSE_IDS)
def test_no_change_request_leaves_slice_pending_change_false(case: str) -> None:
    assert _slice_flag(_CASES[case]()) is False


@pytest.mark.parametrize("case", list(_CASES))
def test_planner_flag_and_specialist_slice_agree(case: str) -> None:
    state = _CASES[case]()
    expected = case == "wp4_request_filed"
    assert build_planner_input(state, LIMITS.context).flags.pending_change == _slice_flag(state) == expected
