"""FU-identity-plan (AEA-51 finding F-2, CAS-16 option A): the escalation node moves a burning_ruled_out case's due to the booked window start; a failed move never fails the turn."""

from __future__ import annotations

import datetime as dt
from typing import Any, cast
from zoneinfo import ZoneInfo

from meridian.agent.nodes.act import escalation
from meridian.domain.actions import OpenCase
from meridian.domain.common import CaseRef
from meridian.domain.handoff import HandoffReason
from meridian.domain.specialists import SchedulingResult
from meridian.policy.handoff import priority_for, promise_for
from tests.unit.agent.nodes.reply_fixtures import (
    NOW,
    THREAD,
    TURN_4,
    booked,
    deps,
    gateway,
    no_uow,
    run,
    settled,
    signals,
    state,
    turn_ctx,
    watch_signals,
    write_result,
)

CHI = ZoneInfo("America/Chicago")
START = dt.datetime(2026, 10, 20, 12, 0, tzinfo=CHI)


class AlignSpy:
    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.error = error

    def align_burning_due(self, thread_id: Any, window_start: Any, turn_id: Any, now: Any) -> bool:
        self.calls.append((thread_id, window_start, turn_id, now))
        if self.error is not None:
            raise self.error
        return True


def _case(reason: HandoffReason) -> OpenCase:
    return OpenCase(
        case_ref=CaseRef("MHC-C-0042"),
        reason=reason,
        priority=priority_for(reason),
        state="unassigned",
        promise=promise_for(reason, "nobody_online", NOW),
        followup=None,
        live_queued=False,
    )


def _written() -> SchedulingResult:
    return SchedulingResult(status="written", write=write_result(booked(TURN_4)), tools=(), calls=())


def _run(spy: AlignSpy, **overrides: object) -> dict[str, Any]:
    d = deps(uow=no_uow, gw=gateway()[0], cases=cast(Any, spy))
    update: dict[str, Any] = dict(escalation(state(**overrides), run(turn_ctx(turn=TURN_4)), deps=d))
    return update


def test_booking_moves_the_burning_case_due() -> None:
    spy = AlignSpy()
    update = _run(
        spy,
        settled=settled(open_case=_case(HandoffReason.BURNING_RULED_OUT)),
        specialist_results=[_written()],
    )
    assert set(update) == {"escalation"}
    assert update["escalation"].outcome == "none"
    assert spy.calls == [(THREAD, START, TURN_4, NOW)]


def test_no_move_without_a_burning_case_or_a_booking() -> None:
    spy = AlignSpy()
    _run(spy, settled=settled(open_case=_case(HandoffReason.REFUND)), specialist_results=[_written()])
    shown = SchedulingResult(status="windows_shown", tools=(), calls=())
    _run(spy, settled=settled(open_case=_case(HandoffReason.BURNING_RULED_OUT)), specialist_results=[shown])
    _run(spy, settled=settled(), specialist_results=[_written()])
    assert spy.calls == []


def test_failed_move_signals_and_keeps_the_turn(caplog: Any) -> None:
    watch_signals(caplog)
    spy = AlignSpy(RuntimeError("case store unavailable (test)"))
    update = _run(
        spy,
        settled=settled(open_case=_case(HandoffReason.BURNING_RULED_OUT)),
        specialist_results=[_written()],
    )
    assert set(update) == {"escalation"}
    [sig] = signals(caplog)
    assert (sig["name"], sig["node"], sig["cause"]) == ("case_write_failed", "escalation", "write_error")
