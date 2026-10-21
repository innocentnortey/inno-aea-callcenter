"""AEA-38: each reply node returns only its own TypedDict's keys (AC-12)."""

from __future__ import annotations

from meridian.agent.nodes import reply
from meridian.domain.handoff import BriefExtraction, Quote
from meridian.domain.state import BriefUpdate, ChecksUpdate, FactsUpdate, ResponderUpdate
from meridian.domain.turn import ResponderDraft
from meridian.policy.limits import Brakes, Limits
from tests.fakes import FakeStructuredModel
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent.nodes.reply_fixtures import (
    TURN_4,
    WP7_MESSAGE,
    FakeCaseService,
    case_summary,
    deps,
    facts,
    gateway,
    handoff_result,
    run,
    seed,
    state,
    turn_ctx,
)


def test_reply_nodes_write_only_own_keys() -> None:
    ctx = turn_ctx()
    with temp_sqlite() as store:
        ids = seed(store, customer=[(TURN_4, WP7_MESSAGE)])
        cases = FakeCaseService(case_summary())
        ext = BriefExtraction(
            needs=[Quote(message_id=ids[0], text="I want a full refund on the repair")],
            claims=[],
            open_decision="Decide.",
        )
        gw, _ = gateway(
            responder=FakeStructuredModel([ResponderDraft(text="Hello.")]),
            brief=FakeStructuredModel([ext]),
        )
        d = deps(uow=store.uow, gw=gw, cases=cases)
        st = state(handoff=handoff_result(case_summary()))
        f = reply.facts(st, run(ctx), deps=d)
        assert set(f) <= FactsUpdate.__optional_keys__
        st = st.model_copy(update=dict(f))
        r = reply.responder(st, run(ctx), deps=d)
        assert set(r) <= ResponderUpdate.__optional_keys__
        b = reply.brief(st, run(ctx), deps=d)
        assert set(b) <= BriefUpdate.__optional_keys__
        st = st.model_copy(update={**r, **{k: v for k, v in b.items() if k != "check_events"}})
        c = reply.checks(st, run(ctx), deps=d)
        assert set(c) == {"checked"} and set(c) <= ChecksUpdate.__optional_keys__
        # halt paths
        limits = Limits(brakes=Brakes(sonnet_calls=0))
        gw0, _ = gateway(responder=FakeStructuredModel([]), brief=FakeStructuredModel([]), limits=limits)
        d0 = deps(uow=store.uow, gw=gw0, cases=cases, limits=limits)
        st0 = state(handoff=handoff_result(case_summary()), facts=facts())
        assert set(reply.responder(st0, run(ctx), deps=d0)) <= ResponderUpdate.__optional_keys__
        assert set(reply.brief(st0, run(ctx), deps=d0)) <= BriefUpdate.__optional_keys__
