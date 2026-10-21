"""AEA-38: what the responder and brief models are shown (AC-8, PA-5, PA-6, PA-7)."""

from __future__ import annotations

import json
import uuid

import pytest

from meridian.agent.nodes import reply
from meridian.agent.prompts.reply import (
    RESPONDER_RULES,
    RESPONDER_SYSTEM_PREFIX,
    brief_request,
    brief_shown,
    facts_for_model,
    render_responder_dynamic,
    responder_input,
    responder_request,
    trimmed_schema,
)
from meridian.domain.actions import ActionKind, OpenCase
from meridian.domain.specialists import KnowledgePoint, KnowledgeResult
from meridian.domain.state import ChatLine
from meridian.domain.turn import ResponderDraft
from tests.fakes import FakeStructuredModel
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent._gateway_doubles import card_like, six_digit_code
from tests.unit.agent.nodes.reply_fixtures import (
    CASE_REF,
    NOW,
    STAFF_NOTE_TEXT,
    TURN_4,
    WP2_QUESTION,
    account_read,
    action,
    case_summary,
    deps,
    facts,
    gateway,
    handoff_result,
    knowledge_answered,
    passage,
    run,
    seed,
    settled,
    signals,
    state,
    tool_record,
    turn_ctx,
    turn_input,
    watch_signals,
)


def test_responder_input_excludes_staff_tool_output_and_promise(caplog: pytest.LogCaptureFixture) -> None:
    watch_signals(caplog)
    sentinel = "for_model:" + uuid.uuid4().hex[:8]
    discretion = "Waive the " + "$" + "49 late-cancellation fee once per customer per year"
    internal = passage("internal/agent_discretion_notes.md", 1, discretion)
    kb = KnowledgeResult(
        status="answered",
        passages=(internal, *knowledge_answered().passages),
        points=(
            KnowledgePoint(text=discretion, passage_id=internal.passage_id),
            *knowledge_answered().points,
        ),
        tools=(tool_record().model_copy(update={"name": sentinel}),),
        calls=(),
    )
    case = case_summary()
    case_action = action(ActionKind.CASE_OPENED, str(CASE_REF), turn=TURN_4, records={"case": str(CASE_REF)})
    open_case = OpenCase(
        case_ref=CASE_REF,
        reason=case.reason,
        priority=case.priority,
        state="unassigned",
        promise=case.promise,
        followup=None,
        live_queued=False,
    )
    code, card = six_digit_code(), card_like()
    model = FakeStructuredModel([ResponderDraft(text="Your invoice is itemised below.")])
    with temp_sqlite() as store:
        seed(store, actions=[case_action])
        gw, _ = gateway(responder=model)
        d = deps(uow=store.uow, gw=gw)
        st = state(
            turn_input=turn_input(text=f"{WP2_QUESTION} code {code}"),
            chat_window=[ChatLine(speaker="customer", text=f"my card {card}", turn_id=TURN_4, at=NOW)],
            specialist_results=[account_read(), kb],
            handoff=handoff_result(case),
        )
        st = st.model_copy(update=dict(reply.facts(st, run(turn_ctx()), deps=d)))
        st = st.model_copy(update={"settled": settled(case_action, open_case=open_case)})
        inp = responder_input(st, turn_ctx())
        st = st.model_copy(update=dict(reply.responder(st, run(turn_ctx()), deps=d)))
        checked = reply.checks(st, run(turn_ctx()), deps=d)["checked"]
    sent = model.requests[0]
    haystacks = {
        "input": inp.model_dump_json(),
        "request": sent.system_prefix + sent.system_dynamic + sent.user,
        "events": "".join(e.model_dump_json() for e in checked.events),
        "signals": json.dumps(signals(caplog)),
    }
    for name, text in haystacks.items():
        for banned in (STAFF_NOTE_TEXT, discretion, sentinel, case.promise.text, str(CASE_REF), card, code):
            assert banned not in text, (name, banned[:12])
    assert set(ResponderDraft.model_fields) == {"text"}


def test_internal_passages_never_rendered() -> None:
    internal = passage("internal/agent_discretion_notes.md", 1, "Waive the fee once.")
    normal = passage("faq/customer_faq.md", 3, "Fees are credited.")
    f = facts(
        passages=[internal, normal],
        points=[
            KnowledgePoint(text=internal.text, passage_id=internal.passage_id),
            KnowledgePoint(text=normal.text, passage_id=normal.passage_id),
        ],
    )
    fm = facts_for_model(f)
    assert [p.text for p in fm.points] == [normal.text]
    assert fm.points[0].source == "faq/customer_faq.md, 2026"
    st = state(facts=f)
    text = render_responder_dynamic(responder_input(st, turn_ctx()))
    assert internal.text not in text
    assert "- Fees are credited. [source: faq/customer_faq.md, 2026]" in text


def test_labels_and_schema_in_requests() -> None:
    st = state(facts=facts())
    req = responder_request(responder_input(st, turn_ctx()))
    assert "ALREADY DONE IN THIS CONVERSATION:" in req.system_dynamic
    assert "WHAT HAPPENED THIS TURN:" in req.system_dynamic
    assert trimmed_schema(ResponderDraft) in RESPONDER_SYSTEM_PREFIX
    for line in RESPONDER_RULES:
        assert line in RESPONDER_SYSTEM_PREFIX
    assert any(
        line.startswith("When an invoice line and a document give different amounts")
        for line in RESPONDER_RULES
    )
    assert json.loads(trimmed_schema(ResponderDraft))["properties"].keys() == {"text"}
    shown = brief_shown([(11, "I want a refund."), (12, "It broke again.")], 600)
    b = brief_request(case_summary(), shown)
    assert "[message 11]" in b.user and "[message 12]" in b.user
    assert str(CASE_REF) not in b.system_dynamic
