"""AEA-60: rendered prompts against the code that consumes them, and malformed provider output against the
documented fallbacks (integrated-journeys rule 4; slice plan 0a).

Every prompt the graph sends is rendered through the real builder, node or runner on turns 1, 2 and 5 of one fixture
conversation; each offered set is compared with its parser, registry or schema in both directions; malformed and
unsupported output goes through the real adapters (stubbed HTTP), the real gateway and the real node, runner or
dispatcher. Each check is shown to fail on a drifted copy. No paid call, no socket, no held-out file (AC-12).
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from typing import Any

import pytest

from meridian.agent.nodes import reply
from meridian.agent.nodes.plan import join_plan
from meridian.agent.prompts import routing as routing_prompts
from meridian.agent.prompts.routing import DANGER_FIELD
from meridian.agent.specialists.specs import SPECS
from meridian.agent.tools.dispatch import ToolDispatcher
from meridian.checks import check_quotes
from meridian.domain.common import (
    FailureCounters,
    HandoffReason,
    Priority,
    ProviderFailureKind,
    Role,
)
from meridian.domain.handoff import BriefExtraction
from meridian.domain.turn import (
    DangerAssessment,
    EscalationInputs,
    PlannerChoices,
    PlannerOutcome,
    ResponderDraft,
)
from meridian.policy.escalation import decide_escalation
from meridian.policy.handoff import priority_for
from tests.contract import _prompts_expect as ex
from tests.contract import _prompts_malformed as pm
from tests.contract import _prompts_render as pr
from tests.contract._prompts_checks import (
    CODE_ONLY,
    EXEMPT,
    FORBIDDEN_FIELDS,
    GUARD,
    HELD_OUT_PREFIXES,
    Drift,
    check_brief_ids,
    check_choice_fields,
    check_quoted_keys,
    check_responder_request,
    check_specialist_request,
    enum_values,
    install_guard,
    missing_cases,
    parse_brief_lines,
    property_names,
)
from tests.contract._prompts_drift import DRIFTS
from tests.fakes import FakeIndex, InMemoryTraceSink
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent.nodes import plan_fixtures as pf
from tests.unit.agent.nodes import reply_fixtures as rf
from tests.unit.agent.specialists._doubles import WP1_INCLUDES, WP1_MINIMUM, WP1_PRICE

ROLE_NAMES = [r.value for r in Role if r is not Role.SPECIALIST] + [f"specialist:{k}" for k in SPECS]
PLANNER_OPTIONS = [(f.name, o) for f in routing_prompts.PLANNER_FIELDS for o in f.options]
# cases.md section 3.4, written out here and never imported from plan._HANDOFF_REASON.
EXPECTED_HANDOFF = {
    "refund": HandoffReason.REFUND,
    "billing_dispute": HandoffReason.BILLING_DISPUTE,
    "membership_cancel": HandoffReason.MEMBERSHIP_CANCEL,
    "unsupported_other": HandoffReason.UNSUPPORTED_ACTION,
    "complaint_or_manager": HandoffReason.COMPLAINT_OR_MANAGER,
    "late_technician": HandoffReason.LATE_TECHNICIAN,
}


@pytest.fixture(scope="module", autouse=True)
def _no_heldout_no_network() -> Iterator[None]:
    install_guard()
    GUARD.active = True
    yield
    GUARD.active = False
    assert GUARD.opens == [] and GUARD.connects == [], (GUARD.opens, GUARD.connects)


def _render_turn(name: str, k: int) -> list[Any]:
    return pr.RENDERERS[name](k)


def _planner_request(k: int = 0) -> Any:
    return _render_turn("planner", k)[0][1]


# --- AC-1 ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ROLE_NAMES)
def test_every_role_and_spec_has_a_rendered_case(name: str) -> None:
    offered = []
    for k in pr.RENDER_TURNS:
        rendered = _render_turn(name, k)
        assert len(rendered) == 1, name
        offered.append(pr.offered_set(name, rendered[0][1]))
    assert offered[0] == offered[1] == offered[2], f"{name} offers different sets on turns 1, 2 and 5"
    if name == "planner_fallback":
        for k in pr.RENDER_TURNS:
            assert _render_turn("planner_fallback", k)[0][1] == _render_turn("planner", k)[0][1]
    if name == "planner":
        missing_cases([r.value for r in Role], pr.RENDERERS)
        with pytest.raises(Drift, match="triage has no rendered case"):
            missing_cases([*(r.value for r in Role), "triage"], pr.RENDERERS)


# --- AC-2 ---------------------------------------------------------------------------------------------------------


def test_routing_fields_match_planner_choices_and_danger_label() -> None:
    planner_req = _planner_request()
    fallback_req = _render_turn("planner_fallback", 0)[0][1]
    classifier_req = _render_turn("classifier", 0)[0][1]
    check_choice_fields("routing.planner", planner_req, PlannerChoices)
    check_choice_fields("routing.planner_fallback", fallback_req, PlannerChoices)
    check_choice_fields(
        "routing.classifier",
        classifier_req,
        DangerAssessment,
        fields={DANGER_FIELD: "label"},
    )
    assert [f.name for f in classifier_req.fields] == [DANGER_FIELD]
    check_quoted_keys("routing.planner", planner_req)
    check_quoted_keys("routing.classifier", classifier_req)
    handoff = next(f for f in planner_req.fields if f.name == "handoff")
    assert "late_technician" in handoff.options


# --- AC-3 ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("field", "option"), PLANNER_OPTIONS)
def test_join_plan_accepts_every_offered_value(field: str, option: str) -> None:
    outcome = PlannerOutcome(
        choices=PlannerChoices.model_validate(pf.choices(**{field: option})),
        probabilities=None,
        model=pr.JEV_MODEL,
        fallback_used=False,
        failure=None,
    )
    state = pf.make_state(pf.NODANGER)
    plan = join_plan(outcome, None, pf.free_text_gate(), state)
    assert all(t.specialist in SPECS for t in plan.tasks)
    if field == "topic":
        assert plan.topic == option
    if field == "handoff" and option != "none":
        expected = EXPECTED_HANDOFF[option]
        assert plan.handoff_request is expected
        assert isinstance(priority_for(expected), Priority)
        decision = decide_escalation(
            EscalationInputs(
                gate=pf.free_text_gate(),
                plan=plan,
                results=(),
                counters=FailureCounters(),
                identity=state.identity,
                halt=None,
                models_disabled=False,
                now=pr.NOW,
            )
        )
        assert decision.outcome == "escalate"
        assert decision.reason is expected
        assert decision.priority is not None


# --- AC-4 ---------------------------------------------------------------------------------------------------------


def test_no_prompt_offers_a_code_only_value() -> None:
    assert ("classifier", "danger_level") in EXEMPT
    for name in ("planner", "planner_fallback", "classifier"):
        for _, request in _render_turn(name, 0):
            for f in request.fields:
                if (name, f.name) in EXEMPT:
                    continue
                for value in sorted(set(f.options) & CODE_ONLY):
                    raise AssertionError(f"{name}.{f.name} offers code-only value '{value}'")
    for kind in SPECS:
        request = pr.specialist_request(kind, 0)[0]
        for tool in request.tools:
            schema = dict(tool.input_schema)
            for value in sorted((property_names(schema) | enum_values(schema)) & CODE_ONLY):
                raise AssertionError(f"specialist.{kind}.{tool.name} offers code-only value '{value}'")
            for name in sorted(property_names(schema) & FORBIDDEN_FIELDS):
                raise AssertionError(f"specialist.{kind}.{tool.name} lets the model set '{name}'")
    for model in (ResponderDraft, BriefExtraction):
        for name in sorted(property_names(model.model_json_schema()) & FORBIDDEN_FIELDS):
            raise AssertionError(f"{model.__name__} lets the model set '{name}'")


# --- AC-5 ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", list(SPECS))
def test_specialist_tools_match_registry_and_report_models(kind: str) -> None:
    with temp_sqlite() as store:
        registry = pr.build_registry(store, FakeIndex(passages=(WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM)))
        dispatcher = ToolDispatcher(registry, store.uow)
        request, task = pr.specialist_request(kind, 0)
        check_specialist_request(kind, request, registry, dispatcher, task)


# --- AC-6 ---------------------------------------------------------------------------------------------------------


def test_reply_schemas_and_brief_message_ids_match_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    sink = InMemoryTraceSink()
    seen: list[dict[int, str]] = []

    def spy(ext: BriefExtraction, shown: Any) -> Any:
        seen.append(dict(shown))
        return check_quotes(ext, shown)

    monkeypatch.setattr(reply, "check_quotes", spy)
    with temp_sqlite() as store, pr.case_ctx(sink, rf.TURN_4) as ctx:
        with store.uow(write=True) as tx:
            cid = tx.core.messages.append(
                pr.THREAD, "customer", rf.WP7_MESSAGE, pr.NOW, turn_id=rf.TURN_4, kind="text"
            )
            tx.core.messages.append(
                pr.THREAD,
                "assistant",
                "I'm sorry the repair didn't fix it.",
                pr.NOW,
                turn_id=rf.TURN_4,
                kind="text",
            )
            tx.core.messages.append(
                pr.THREAD, "representative", pr.STAFF_LINE, pr.NOW, turn_id=rf.TURN_4, kind="text"
            )
            tx.commit()
        case = rf.case_summary()
        gw = pr.RecordingGateway(
            {
                Role.RESPONDER: [pr.ok_value(ResponderDraft(text="I can pass that to a person."))],
                Role.BRIEF: [
                    pr.ok_value(
                        BriefExtraction(
                            needs=[{"message_id": cid, "text": "full refund"}],  # type: ignore[list-item]
                            claims=[],
                            open_decision="Decide on the refund.",
                        )
                    )
                ],
            }
        )
        deps = rf.deps(
            uow=store.uow,
            gw=gw.as_gateway(),
            cases=rf.FakeCaseService(case),
            brief=pm.real_brief_assembler(),
        )
        state = rf.state(
            turn_input=rf.turn_input(turn=rf.TURN_4, message_id=cid, text=rf.WP7_MESSAGE),
            handoff=rf.handoff_result(case),
            facts=rf.facts(),
            settled=rf.settled(),
        )
        reply.responder(state, rf.run(ctx), deps=deps)
        update = reply.brief(state, rf.run(ctx), deps=deps)
        reply.checks(
            state.model_copy(update={"brief_extraction": update["brief_extraction"]}), rf.run(ctx), deps=deps
        )
        with store.uow() as tx:
            customer_ids = {
                r.id for r in tx.core.messages.recent(pr.THREAD, turns=20) if r.role == "customer"
            }
    responder_req = gw.for_role(Role.RESPONDER)[0]
    brief_req = gw.for_role(Role.BRIEF)[0]
    check_responder_request(responder_req)  # type: ignore[arg-type]
    assert brief_req.output_model is BriefExtraction  # type: ignore[union-attr]
    check_brief_ids(parse_brief_lines(brief_req.user), seen[0], customer_ids)  # type: ignore[union-attr]


# --- AC-7 to AC-9: malformed provider output --------------------------------------------------------------------------

ROUTING_IDS = list(pm.ROUTING_CASES)
SPECIALIST_IDS = list(pm.SPECIALIST_CASES) + list(pm.ACT_CASES)
REPLY_IDS = list(pm.DRAFT_CASES) + list(pm.BRIEF_CASE_IDS)
K = ProviderFailureKind


@pytest.mark.parametrize("case_id", ROUTING_IDS)
def test_malformed_routing_outputs(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    ex.check_routing(case_id, caplog)


@pytest.mark.parametrize("case_id", [c for c in SPECIALIST_IDS if not c.startswith("step-")])
def test_malformed_specialist_outputs(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    ex.check_specialist(case_id, caplog)


@pytest.mark.parametrize("case_id", list(pm.ACT_CASES))
def test_malformed_step_failures_at_the_act_node(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    ex.check_act(case_id, caplog)


@pytest.mark.parametrize("case_id", REPLY_IDS)
def test_malformed_reply_outputs(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    ex.check_reply(case_id, caplog)


# --- AC-10: rejected values never reach a record -----------------------------------------------------------------------


def _haystack(run: pm.CaseRun) -> str:
    parts: list[str] = [json.dumps(f.model_dump(mode="json")) for f in run.failures]
    parts += [json.dumps(c.model_dump(mode="json")) for c, _ in run.ledger.records]
    parts += [json.dumps(s, default=str) for s in run.signals]
    parts += [json.dumps(e.model_dump(mode="json")) for e in run.check_events]
    parts += [json.dumps(r.model_dump(mode="json")) for r in run.tool_records]
    parts += [json.dumps(r.model_dump(mode="json")) for r in run.lookup_rows]
    parts += [json.dumps(b.model_dump(mode="json")) for b in run.stored_briefs]
    for body in run.next_request_bodies:
        for message in body.get("messages", []):
            content = message.get("content")
            if isinstance(content, list):
                parts += [
                    json.dumps(b) for b in content if isinstance(b, dict) and b.get("type") == "tool_result"
                ]
    for record in run.log_records:
        parts += [record.getMessage(), json.dumps(record.__dict__, default=str)]
    return "\n".join(parts)


def test_rejected_values_absent_from_records(caplog: pytest.LogCaptureFixture) -> None:
    cases: list[tuple[pm.CaseRun, str, bool]] = [
        (pm.run_routing_case("a-choice-outside-options", caplog), pm.MARK_OPTION, False),
        (pm.run_specialist_case("query-301", caplog), pm.MARK_QUERY, True),
        (pm.run_reply_case("draft-1201", caplog), pm.MARK_DRAFT, False),
        (pm.run_brief_case("quote-paraphrase", caplog), pm.MARK_DRAFT, True),
    ]
    for run, marker, downstream in cases:
        assert marker not in _haystack(run), (run.case_id, marker)
        calls = [c for turn in run.sink.turns for c in turn.model_calls]
        assert not [i for i, c in enumerate(calls) if marker in c.masked_input], (run.case_id, "masked_input")
        carrying = [i for i, c in enumerate(calls) if marker in c.masked_output]
        # Clarification C-2: a value a downstream consumer rejects was accepted by the adapter, so the signed
        # models.md section 5 rule puts it in the one span of the attempt that produced it.
        assert carrying in ([], [0]) if downstream else carrying == [], (run.case_id, carrying)


# --- AC-11: each check fails on a drifted copy -------------------------------------------------------------------------


@pytest.mark.parametrize("drift_id", list(DRIFTS))
def test_check_fails_on_drift(drift_id: str, monkeypatch: pytest.MonkeyPatch) -> None:
    run, message = DRIFTS[drift_id]
    with pytest.raises(Drift, match=re.escape(message)):
        run(monkeypatch)


# --- AC-14: every malformed case leaves its WF-1 records, codes only ---------------------------------------------------

EXPECTED_FAILURES: dict[str, list[tuple[Role, ProviderFailureKind]]] = {
    "a-choice-outside-options": [(Role.PLANNER, K.INVALID_OUTPUT)],
    "b-missing-field": [(Role.PLANNER, K.INVALID_OUTPUT)],
    "c-unparseable-json": [(Role.PLANNER, K.INVALID_OUTPUT)],
    "d1-fallback-extra-field": [(Role.PLANNER, K.INVALID_OUTPUT), (Role.PLANNER_FALLBACK, K.INVALID_OUTPUT)],
    "d2-fallback-option-outside": [
        (Role.PLANNER, K.INVALID_OUTPUT),
        (Role.PLANNER_FALLBACK, K.INVALID_OUTPUT),
    ],
    "e1-classifier-emergency": [(Role.CLASSIFIER, K.INVALID_OUTPUT)],
    "e2-classifier-empty": [(Role.CLASSIFIER, K.INVALID_OUTPUT)],
    "step-unparseable": [(Role.SPECIALIST, K.INVALID_OUTPUT)],
    "step-max-tokens": [(Role.SPECIALIST, K.MAX_TOKENS)],
    "step-refusal": [(Role.SPECIALIST, K.REFUSAL)],
    "draft-empty": [(Role.RESPONDER, K.INVALID_OUTPUT)],
    "draft-1201": [(Role.RESPONDER, K.INVALID_OUTPUT)],
    "draft-extra-promise": [(Role.RESPONDER, K.INVALID_OUTPUT)],
    "draft-refusal": [(Role.RESPONDER, K.REFUSAL)],
    **{c: [(Role.BRIEF, K.INVALID_OUTPUT)] for c in pm.BRIEF_CASE_IDS if c.startswith("brief-")},
}


def _run_any(case_id: str, caplog: pytest.LogCaptureFixture) -> pm.CaseRun:
    if case_id in pm.ROUTING_CASES:
        return pm.run_routing_case(case_id, caplog)
    if case_id in pm.SPECIALIST_CASES:
        return pm.run_specialist_case(case_id, caplog)
    if case_id in pm.ACT_CASES:
        return pm.run_act_case(case_id, caplog)
    if case_id in pm.DRAFT_CASES:
        return pm.run_reply_case(case_id, caplog)
    return pm.run_brief_case(case_id, caplog)


@pytest.mark.parametrize("case_id", ROUTING_IDS + SPECIALIST_IDS + REPLY_IDS)
def test_malformed_cases_leave_their_records(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    run = _run_any(case_id, caplog)
    records = [c for c, _ in run.ledger.records]
    assert len(records) == sum(run.requests.values())
    failed = sorted((c.role.value, c.failure.kind.value) for c in records if c.failure is not None)
    expected = sorted((r.value, k.value) for r, k in EXPECTED_FAILURES.get(case_id, []))
    assert failed == expected
    assert all(c.status == ("error" if c.failure is not None else "ok") for c in records)
    assert [m.record for t in run.sink.turns for m in t.model_calls] == records
    for signal in run.signals:
        assert signal["name"] and signal["cause"]
        assert signal["node"] and signal["role"]
        assert signal["turn_id"] == str(run.ctx.ids.turn_id)
        assert signal["thread_id"] == str(pr.THREAD)
        assert signal["request_id"] == str(run.ctx.ids.request_id)
        assert signal["run_tag"] == "live"
    if case_id in ("e1-classifier-emergency", "e2-classifier-empty"):
        assert [e.check for e in run.check_events] == ["classifier"]
    if case_id.startswith("quote-"):
        assert [e.check for e in run.check_events if e.check == "brief_quote"] == ["brief_quote"]
    if case_id in pm.SPECIALIST_CASES:
        assert len(run.lookup_rows) == len(run.tool_records)


# --- AC-12 (keep last) --------------------------------------------------------------------------------------------------


def test_no_heldout_reads_and_no_network(tmp_path: Any) -> None:
    assert GUARD.active
    before = (list(GUARD.opens), list(GUARD.connects))
    HELD_OUT_PREFIXES.append(str(tmp_path))
    try:
        probe = tmp_path / "probe.txt"
        probe.write_text("x")
        probe.open().close()
        assert [p for p in GUARD.opens if p.startswith(str(tmp_path))]
    finally:
        HELD_OUT_PREFIXES.remove(str(tmp_path))
        GUARD.opens[:] = [p for p in GUARD.opens if not p.startswith(str(tmp_path))]
    sys.audit("socket.connect", None, ("127.0.0.1", 9))  # an audit event only: no socket is opened
    assert GUARD.connects == [*before[1], "socket.connect"]
    GUARD.connects.pop()
    assert before == ([], [])
