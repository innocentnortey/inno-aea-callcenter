"""AEA-38: the responder and checks nodes (AC-2..AC-5, AC-11, AC-13, PA-3)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from meridian.agent.nodes import reply
from meridian.domain.common import HaltReason, ProviderFailureKind
from meridian.domain.state import ConversationState
from meridian.domain.turn import ResponderDraft
from meridian.policy.limits import Brakes, Limits
from tests.fakes import FakeStructuredModel, ScriptedFailure
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent.nodes.reply_fixtures import (
    MOVED_T3,
    TURN_4,
    WP2_KEPT,
    WP2_LOOKUP_TEXT,
    WP2_QUESTION,
    WP7_MESSAGE,
    FakeBriefAssembler,
    FakeCaseService,
    booked,
    case_summary,
    deps,
    facts,
    gateway,
    handoff_result,
    run,
    seed,
    settled,
    signals,
    state,
    turn_ctx,
    watch_signals,
    wp2_draft,
)


def _checks(st: ConversationState, store: Any, **kw: Any) -> Any:
    gw, _ = gateway()
    d = deps(uow=store.uow, gw=gw, **kw)
    return reply.checks(st, run(turn_ctx()), deps=d)["checked"]


def _draft(text: str) -> ResponderDraft:
    return ResponderDraft(text=text)


def _responder(
    st: ConversationState, model: FakeStructuredModel, *, limits: Limits | None = None, ctx: Any = None
) -> Any:
    gw, _ = gateway(responder=model, limits=limits)
    d = deps(uow=lambda: (_ for _ in ()).throw(AssertionError("no uow")), gw=gw, limits=limits)
    return reply.responder(st, run(ctx or turn_ctx()), deps=d)


def _ready(draft: str, **kw: Any) -> ConversationState:
    return state(facts=facts(), draft=_draft(draft), **kw)


def test_wp4f_turn4_claim_backed_by_settled() -> None:
    text = "Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta."
    with temp_sqlite() as store:
        c = _checks(_ready(text, settled=settled(MOVED_T3)), store)
        assert c.removals == () and c.text == text and c.fallback_used is False
        c = _checks(_ready(text, settled=settled()), store)
    assert len(c.removals) == 1
    assert c.removals[0].reason == "no_completed_action"


def test_wp8_generic_done_removed() -> None:
    with temp_sqlite() as store:
        c = _checks(
            _ready("Done, auto-renew is off. Done, your visit is booked.", settled=settled(booked(TURN_4))),
            store,
        )
    assert c.text == "Done, your visit is booked."
    ev = c.events[0]
    assert (ev.check, ev.result, ev.removed, ev.claim_kinds) == ("completion", "trimmed", 1, ("completion",))
    assert "auto-renew" not in ev.model_dump_json()


def test_unmatched_amount_removed() -> None:
    with temp_sqlite() as store:
        seed(
            store, customer=[(TURN_4, WP2_QUESTION)], lookups=[(TURN_4, 0, WP2_LOOKUP_TEXT, ("INV-204411",))]
        )
        c = _checks(_ready(wp2_draft()), store)
    assert [r.reason for r in c.removals] == ["not_in_evidence"]
    assert c.text == WP2_KEPT


def test_responder_failure_and_empty_draft_fallback(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    fail = ScriptedFailure(ProviderFailureKind.OVERLOADED, retry_after_s=0.0)
    model = FakeStructuredModel([fail, fail])
    st = state(facts=facts())
    update = _responder(st, model)
    assert update == {"draft": None}
    assert len(model.requests) == 2
    (sig,) = signals(caplog)
    assert (sig["name"], sig["cause"], sig["attempt"]) == ("responder_fallback", "overloaded", 2)
    with temp_sqlite() as store:
        c = _checks(st.model_copy(update=update), store)
        assert c.fallback_used and c.text == ""
        assert [(e.check, e.result) for e in c.events] == [("completion", "fallback"), ("fact", "fallback")]
        caplog.clear()
        c = _checks(_ready("Done!", settled=settled()), store)
    assert c.fallback_used and c.text == ""
    (sig,) = signals(caplog)
    assert (sig["cause"], sig["node"]) == ("all_removed", "checks")


def test_sonnet_brake_on_responder(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    model = FakeStructuredModel([])
    update = _responder(state(facts=facts()), model, limits=Limits(brakes=Brakes(sonnet_calls=0)))
    assert update["halt"].reason is HaltReason.BRAKE_SONNET_CALLS and update["halt"].node == "responder"
    (ev,) = update["check_events"]
    assert (ev.check, ev.result, ev.codes) == ("brake", "fired", ("brake_sonnet_calls", "responder"))
    assert [s["name"] for s in signals(caplog)] == ["brake_fired"]
    assert model.requests == []


def test_deadline_halt_on_responder_no_brake_event(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    update = _responder(state(facts=facts()), FakeStructuredModel([]), ctx=turn_ctx(seconds_left=0.5))
    assert update["halt"].reason is HaltReason.DEADLINE
    assert "check_events" not in update and update["draft"] is None
    assert signals(caplog) == []


def test_check_events_and_signals_emitted(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    with temp_sqlite() as store:
        c = _checks(_ready("Your visit is on the schedule."), store)
        assert [(e.check, e.result) for e in c.events] == [("completion", "pass"), ("fact", "pass")]
        ids = seed(store, customer=[(TURN_4, WP7_MESSAGE)])
        from meridian.domain.handoff import BriefExtraction, Quote

        ext = BriefExtraction(
            needs=[Quote(message_id=ids[0], text="I want a full refund on the repair")],
            claims=[],
            open_decision="Decide.",
        )
        st = _ready("Done!", handoff=handoff_result(case_summary()), brief_extraction=ext)
        c = _checks(st, store, cases=FakeCaseService(case_summary()), brief=FakeBriefAssembler())
        assert [e.check for e in c.events] == ["completion", "fact", "brief_quote", "brief_fact"]
    model = FakeStructuredModel([ScriptedFailure(ProviderFailureKind.OVERLOADED, retry_after_s=0.0)] * 2)
    _responder(state(facts=facts()), model)
    _responder(state(facts=facts()), FakeStructuredModel([]), limits=Limits(brakes=Brakes(sonnet_calls=0)))
    sigs = signals(caplog)
    assert len(sigs) >= 3
    keys = {
        "record",
        "name",
        "turn_id",
        "thread_id",
        "request_id",
        "run_tag",
        "node",
        "cause",
        "role",
        "specialist",
        "attempt",
        "recovered",
    }
    for s in sigs:
        assert set(s) == keys
        assert s["turn_id"] and s["thread_id"] and s["request_id"] and s["run_tag"] and s["node"]
    assert "Done!" not in json.dumps(sigs) and WP7_MESSAGE not in json.dumps(sigs)
