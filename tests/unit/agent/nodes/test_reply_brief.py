"""AEA-38: the brief node and the brief half of checks (AC-6, AC-7, PA-4)."""

from __future__ import annotations

from typing import Any

import pytest

from meridian.agent.nodes import reply
from meridian.domain.handoff import BriefExtraction, Quote
from meridian.domain.state import ConversationState
from meridian.policy.limits import Brakes, Limits
from tests.fakes import FakeStructuredModel
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent.nodes.reply_fixtures import (
    CASE_REF,
    TURN_4,
    WP7_MESSAGE,
    FakeBriefAssembler,
    FakeCaseService,
    case_summary,
    deps,
    facts,
    gateway,
    handoff_result,
    run,
    seed,
    signals,
    state,
    turn_ctx,
    watch_signals,
)

LOOKUP = "INV-204411 total $478.00 balance $478.00 lines $89.00 / $245.00 / $144.00"


def _st(**kw: Any) -> ConversationState:
    return state(handoff=handoff_result(case_summary()), facts=facts(), **kw)


def _setup(store: Any, *, case: Any, model: Any, fail_attach: bool = False, limits: Limits | None = None):
    ids = seed(store, customer=[(TURN_4, WP7_MESSAGE)], lookups=[(TURN_4, 0, LOOKUP, ("INV-204411",))])
    cases = FakeCaseService(case, fail_attach=fail_attach)
    assembler = FakeBriefAssembler()
    gw, _ = gateway(brief=model, limits=limits)
    return ids, cases, assembler, deps(uow=store.uow, gw=gw, cases=cases, brief=assembler, limits=limits)


def test_brief_only_when_case_opened() -> None:
    model = FakeStructuredModel([])
    with temp_sqlite() as store:
        _, cases, assembler, d = _setup(store, case=None, model=model)
        st = _st()
        assert reply.brief(st, run(turn_ctx()), deps=d) == {"brief_extraction": None}
        c = reply.checks(st, run(turn_ctx()), deps=d)["checked"]
    assert model.requests == [] and cases.attached == [] and assembler.extractions == []
    assert c.fallback_used  # no draft in this state; nothing attached


def _ext(ids: list[int]) -> BriefExtraction:
    return BriefExtraction(
        needs=[Quote(message_id=ids[0], text="I want a full refund on the repair")],
        claims=[Quote(message_id=ids[0], text="It didn't fix anything")],
        open_decision="Decide on a refund.",
    )


def test_brief_stored_twice() -> None:
    with temp_sqlite() as store:
        ids = seed(store, customer=[(TURN_4, WP7_MESSAGE)])
        cases = FakeCaseService(case_summary())
        gw, _ = gateway(brief=FakeStructuredModel([_ext(ids)]))
        d = deps(uow=store.uow, gw=gw, cases=cases, brief=FakeBriefAssembler())
        st = _st()
        update = reply.brief(st, run(turn_ctx()), deps=d)
        reply.checks(st.model_copy(update=update), run(turn_ctx()), deps=d)
    assert [b.status for _, b in cases.attached] == ["being_written", "ready"]
    assert all(ref == CASE_REF for ref, _ in cases.attached)


def test_brief_failure_not_generated(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    bad = {"needs": [], "claims": [], "open_decision": "x"}
    with temp_sqlite() as store:
        _, cases, assembler, d = _setup(store, case=case_summary(), model=FakeStructuredModel([bad]))
        st = _st()
        update = reply.brief(st, run(turn_ctx()), deps=d)
        assert update == {"brief_extraction": None}
        reply.checks(st.model_copy(update=update), run(turn_ctx()), deps=d)
    (sig,) = signals(caplog)
    assert (sig["name"], sig["cause"], sig["attempt"]) == ("brief_failed", "invalid_output", 1)
    final = cases.attached[-1][1]
    assert final.status == "failed"
    assert [h.number for h in final.headings if h.not_generated] == [2, 4, 7]
    assert assembler.extractions == [(None, None)]


def test_attach_brief_failure_does_not_fail_turn(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    with temp_sqlite() as store:
        ids = seed(store, customer=[(TURN_4, WP7_MESSAGE)])
        cases = FakeCaseService(case_summary(), fail_attach=True)
        gw, _ = gateway(brief=FakeStructuredModel([_ext(ids)]))
        d = deps(uow=store.uow, gw=gw, cases=cases)
        st = _st()
        update = reply.brief(st, run(turn_ctx()), deps=d)
        c = reply.checks(st.model_copy(update=update), run(turn_ctx()), deps=d)["checked"]
    assert c is not None
    sigs = [(s["name"], s["cause"], s["node"]) for s in signals(caplog)]
    assert sigs == [("brief_failed", "write_error", "brief"), ("brief_failed", "write_error", "checks")]


def test_brief_quote_and_fact_checks() -> None:
    with temp_sqlite() as store:
        ids, _, assembler, d = _setup(store, case=case_summary(), model=FakeStructuredModel([]))
        q = ids[0]
        ext = BriefExtraction(
            needs=[Quote(message_id=q, text="I want a full refund on the repair")],
            claims=[
                Quote(message_id=q, text="It didn't fix anything"),
                Quote(message_id=q, text="I had to call another company"),
                Quote(message_id=q, text="The repair made it worse"),
            ],
            open_decision="Decide on a refund, a warranty recall or neither. The repair cost $310.",
        )
        c = reply.checks(_st(brief_extraction=ext), run(turn_ctx()), deps=d)["checked"]
    kept, check = assembler.extractions[0]
    assert kept is not None and len(kept.needs) == 1
    assert [x.text for x in kept.claims] == ["It didn't fix anything", "I had to call another company"]
    assert [r.reason for r in check.removals] == ["not_in_evidence"]
    quote_ev, fact_ev = c.events[-2:]
    assert (quote_ev.check, quote_ev.result, quote_ev.removed, quote_ev.claim_kinds) == (
        "brief_quote",
        "trimmed",
        1,
        ("quote",),
    )
    assert (fact_ev.check, fact_ev.result, fact_ev.removed, fact_ev.claim_kinds) == (
        "brief_fact",
        "trimmed",
        1,
        ("amount",),
    )


def test_brief_sonnet_brake(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    limits = Limits(brakes=Brakes(sonnet_calls=0))
    with temp_sqlite() as store:
        _, _, _, d = _setup(store, case=case_summary(), model=FakeStructuredModel([]), limits=limits)
        update = reply.brief(_st(), run(turn_ctx()), deps=d)
    assert update["halt"].node == "brief" and update["brief_extraction"] is None
    (ev,) = update["check_events"]
    assert ev.check == "brake"
    assert [s["name"] for s in signals(caplog)] == ["brief_failed", "brake_fired"]
