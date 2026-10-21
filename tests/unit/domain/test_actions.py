"""AEA-02 AC-5: Settled.has / current_visit / only_turn (WP-4F, graph-core section 14)."""

from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled, VisitChange, VisitView
from meridian.domain.common import ThreadId, TurnId

THREAD = ThreadId("3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10")
TURN_3 = TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")
TURN_4 = TurnId("a2b4c6d8-1e3f-4a5b-8c7d-9e0f1a2b3c4d")
READ_AT = dt.datetime(2026, 10, 16, 10, 20, tzinfo=dt.UTC)


def _moved(*, at: dt.datetime, turn: TurnId = TURN_3, appointment: str = "159") -> CompletedAction:
    return CompletedAction(
        key=ActionKey(thread_id=THREAD, turn_id=turn, kind=ActionKind.MOVED, record_id=appointment),
        kind=ActionKind.MOVED,
        records={"appointment": appointment, "slot": "56", "old_slot": "159"},
        before={"date": "2026-10-22", "window": "08:00-12:00"},
        after={
            "date": "2026-10-19",
            "window": "08:00-12:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "fee line (fixture)",
        },
        at=at,
    )


def _booked(*, at: dt.datetime, appointment: str) -> CompletedAction:
    return CompletedAction(
        key=ActionKey(thread_id=THREAD, turn_id=TURN_3, kind=ActionKind.BOOKED, record_id=appointment),
        kind=ActionKind.BOOKED,
        records={"appointment": appointment, "slot": "60"},
        after={
            "date": "2026-10-20",
            "window": "12:00-16:00",
            "technician": "Marta Kowalski",
            "service_type": "plumbing",
            "fee_line": "fee line (fixture)",
        },
        at=at,
    )


def _cancelled(*, at: dt.datetime, appointment: str) -> CompletedAction:
    return CompletedAction(
        key=ActionKey(thread_id=THREAD, turn_id=TURN_3, kind=ActionKind.CANCELLED, record_id=appointment),
        kind=ActionKind.CANCELLED,
        records={"appointment": appointment},
        at=at,
    )


def _change_request(*, at: dt.datetime, appointment: str) -> CompletedAction:
    return CompletedAction(
        key=ActionKey(
            thread_id=THREAD, turn_id=TURN_3, kind=ActionKind.CHANGE_REQUEST_SENT, record_id=appointment
        ),
        kind=ActionKind.CHANGE_REQUEST_SENT,
        records={"appointment": appointment},
        after={"change": "move", "wanted_text": "Thursday afternoon", "fee_line": "fee line (fixture)"},
        at=at,
    )


T0 = dt.datetime(2026, 10, 16, 10, 12, tzinfo=dt.UTC)


def test_wp4f_move_is_settled() -> None:
    settled = Settled(actions=(_moved(at=T0),), open_case=None, read_at=READ_AT)
    assert settled.has(ActionKind.MOVED)
    assert settled.current_visit() == VisitView(
        appointment_id=159,
        date=dt.date(2026, 10, 19),
        window="08:00-12:00",
        technician="Marta Kowalski",
        service_type="hvac_repair",
        fee_line="fee line (fixture)",
        status="moved",
        change_request=None,
    )
    assert settled.only_turn(TURN_4).actions == ()
    assert settled.only_turn(TURN_4).open_case is None
    assert len(settled.only_turn(TURN_3).actions) == 1


def test_has_with_record_id() -> None:
    settled = Settled(actions=(_moved(at=T0),), open_case=None, read_at=READ_AT)
    assert settled.has(ActionKind.MOVED, "159")
    assert not settled.has(ActionKind.MOVED, "160")
    assert not settled.has(ActionKind.CANCELLED)


def test_cancelled_visit_is_not_current() -> None:
    later = T0 + dt.timedelta(minutes=1)
    earlier_visit = _booked(at=T0, appointment="160")
    settled = Settled(
        actions=(
            _moved(at=T0 - dt.timedelta(minutes=5)),
            earlier_visit,
            _cancelled(at=later, appointment="160"),
        ),
        open_case=None,
        read_at=READ_AT,
    )
    visit = settled.current_visit()
    assert visit is not None
    assert visit.appointment_id == 159  # 160 was cancelled, so the older moved visit is the current one
    assert settled.has(ActionKind.BOOKED, "160")  # the cancelled visit stays in actions

    only_cancelled = Settled(
        actions=(earlier_visit, _cancelled(at=later, appointment="160")), open_case=None, read_at=READ_AT
    )
    assert only_cancelled.current_visit() is None


def test_change_request_keeps_original() -> None:
    settled = Settled(
        actions=(_moved(at=T0), _change_request(at=T0 + dt.timedelta(minutes=2), appointment="159")),
        open_case=None,
        read_at=READ_AT,
    )
    visit = settled.current_visit()
    assert visit is not None
    assert visit.status == "original_stays"
    assert visit.date == dt.date(2026, 10, 19)
    assert visit.change_request == VisitChange(
        change="move", wanted_text="Thursday afternoon", fee_line="fee line (fixture)"
    )


def test_only_turn_filters_to_one_turn() -> None:
    other = _booked(at=T0 + dt.timedelta(minutes=3), appointment="161")
    other = other.model_copy(update={"key": other.key.model_copy(update={"turn_id": TURN_4})})
    settled = Settled(actions=(_moved(at=T0), other), open_case=None, read_at=READ_AT)
    assert [a.key.record_id for a in settled.only_turn(TURN_3).actions] == ["159"]
    assert [a.key.record_id for a in settled.only_turn(TURN_4).actions] == ["161"]


def test_missing_after_key_is_loud() -> None:
    action = _moved(at=T0).model_copy(update={"after": {"date": "2026-10-19"}})
    with pytest.raises(ValidationError):
        Settled(actions=(action,), open_case=None, read_at=READ_AT).current_visit()
