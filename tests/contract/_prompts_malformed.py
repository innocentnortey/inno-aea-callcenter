"""AEA-60 helper: malformed provider output through the real adapters (stubbed HTTP), the real gateway and the real
node, runner or dispatcher (plan steps 5-9).

Private to `test_prompts_vs_consumers.py`. The markers are made-up strings; nothing here is a real value.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, cast

import httpx
import pytest
from pydantic import SecretStr

from meridian.adapters.models.openrouter_jev import JevAdapter
from meridian.agent.context import GraphDeps
from meridian.agent.gateway import ModelGateway
from meridian.agent.nodes import act, reply
from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.nodes.plan import danger_classifier, plan_join, planner
from meridian.agent.routers import route_after_plan_join
from meridian.agent.specialists.runner import SpecialistRunner
from meridian.agent.specialists.specs import SPECS, RunOutcome
from meridian.agent.tools.dispatch import ToolDispatcher
from meridian.domain.common import ProviderFailure, ToolCallRecord
from meridian.domain.handoff import Brief
from meridian.domain.state import SpecialistSend
from meridian.domain.tools import LookupRow, ToolCallScope
from meridian.domain.turn import CheckEvent, Plan, PlannedTask, TaskIntent, TurnContext
from meridian.policy.limits import Brakes, Limits
from meridian.services.handoff import BriefAssembler
from tests.contract._anthropic_fixtures import Handler, adapter_for, ok, respond, sequence
from tests.contract._prompts_render import JEV_MODEL, THREAD, NoScheduling, build_registry, case_ctx
from tests.fakes import FakeIndex, InMemoryTraceSink
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent._gateway_doubles import RecordingLedger, default_doubles, gateway_kwargs
from tests.unit.agent.nodes import plan_fixtures as pf
from tests.unit.agent.nodes import reply_fixtures as rf
from tests.unit.agent.specialists._doubles import (
    WP1_INCLUDES,
    WP1_MINIMUM,
    WP1_PRICE,
    make_task,
)

MARK_OPTION = "zq-rejected-option-7731"
MARK_QUERY = "zq-rejected-query-7731"
MARK_DRAFT = "zq-rejected-draft-7731"
BOOK = pf.choices(scheduling="book_new", topic="booking")
BAD_TEXT = b"{not json"


def real_brief_assembler() -> Any:
    return BriefAssembler()


def padded(marker: str, length: int) -> str:
    text = "a" * (length - len(marker) - 1) + " " + marker
    assert len(text) == length
    return text


# --- adapters -------------------------------------------------------------------------------------------------------


def jev_adapter(handler: Callable[[httpx.Request], httpx.Response]) -> tuple[JevAdapter, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    adapter = JevAdapter(
        httpx.Client(transport=httpx.MockTransport(recording)),
        api_key=SecretStr("test-key-" + secrets.token_hex(8)),
        model=JEV_MODEL,
    )
    return adapter, seen


def jev_body(answers: Mapping[str, str]) -> dict[str, Any]:
    return {
        "id": "gen-test-0060",
        "model": JEV_MODEL,
        "answers": {k: {"type": "choice", "choice": v} for k, v in answers.items()},
        "usage": {"input_tokens": 300, "output_tokens": 20},
    }


def jev_ok(answers: Mapping[str, str]) -> Callable[[httpx.Request], httpx.Response]:
    return lambda request: httpx.Response(200, json=jev_body(answers))


def jev_unparseable(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=BAD_TEXT, headers={"content-type": "application/json"})


def real_gateway(*, sink: InMemoryTraceSink, ledger: RecordingLedger, **adapters: Any) -> ModelGateway:
    d = default_doubles(ledger=ledger, **adapters)
    return ModelGateway(**{**gateway_kwargs(d), "trace": sink})


@dataclass
class CaseRun:
    case_id: str
    ledger: RecordingLedger
    sink: InMemoryTraceSink
    ctx: TurnContext
    signals: list[dict[str, Any]] = field(default_factory=list)
    log_records: list[logging.LogRecord] = field(default_factory=list)
    check_events: list[CheckEvent] = field(default_factory=list)
    lookup_rows: list[LookupRow] = field(default_factory=list)
    tool_records: list[ToolCallRecord] = field(default_factory=list)
    failures: list[ProviderFailure] = field(default_factory=list)
    requests: dict[str, int] = field(default_factory=dict)
    next_request_bodies: list[dict[str, Any]] = field(default_factory=list)
    stored_briefs: list[Brief] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)
    outcome: RunOutcome | None = None


def _begin(caplog: pytest.LogCaptureFixture) -> tuple[InMemoryTraceSink, RecordingLedger]:
    caplog.set_level(logging.DEBUG)
    caplog.clear()
    return InMemoryTraceSink(), RecordingLedger()


def _finish(run: CaseRun, caplog: pytest.LogCaptureFixture) -> CaseRun:
    run.log_records = list(caplog.records)
    run.signals = [r.__dict__["signal"] for r in run.log_records if r.name == "meridian.signal"]
    run.failures = [c.failure for c, _ in run.ledger.records if c.failure is not None]
    return run


def _text(raw: object) -> Handler:
    return ok([{"type": "text", "text": json.dumps(raw)}], stop_reason="end_turn")


# --- AC-7: routing --------------------------------------------------------------------------------------------------

ROUTING_CASES: dict[str, dict[str, Any]] = {
    "a-choice-outside-options": {
        "text": pf.WP3,
        "planner": jev_ok({**BOOK, "knowledge": MARK_OPTION}),
        "fallback": _text(BOOK),
    },
    "b-missing-field": {
        "text": pf.WP3,
        "planner": lambda r: httpx.Response(
            200, json=jev_body({k: v for k, v in BOOK.items() if k != "topic"})
        ),
        "fallback": _text(BOOK),
    },
    "c-unparseable-json": {"text": pf.WP3, "planner": jev_unparseable, "fallback": _text(BOOK)},
    "d1-fallback-extra-field": {
        "text": pf.NODANGER,
        "planner": jev_ok({**BOOK, "knowledge": "maybe"}),
        "fallback": _text({**BOOK, "urgency": "today"}),
    },
    "d2-fallback-option-outside": {
        "text": pf.NODANGER,
        "planner": jev_ok({**BOOK, "knowledge": "maybe"}),
        "fallback": _text({**BOOK, "handoff": "cancel_membership"}),
    },
    "e1-classifier-emergency": {
        "text": pf.NODANGER,
        "planner": jev_ok(BOOK),
        "classifier": lambda r: httpx.Response(200, json=jev_body({"danger_level": "emergency"})),
    },
    "e2-classifier-empty": {
        "text": pf.NODANGER,
        "planner": jev_ok(BOOK),
        "classifier": lambda r: httpx.Response(200, json=jev_body({})),
    },
}


def run_routing_case(case_id: str, caplog: pytest.LogCaptureFixture) -> CaseRun:
    spec = ROUTING_CASES[case_id]
    sink, ledger = _begin(caplog)
    jev_planner, planner_http = jev_adapter(spec["planner"])
    adapters: dict[str, object] = {"planner": jev_planner}
    fallback_rec = None
    classifier_http: list[httpx.Request] = []
    if "fallback" in spec:
        adapters["fallback"], fallback_rec = adapter_for(spec["fallback"])
    if "classifier" in spec:
        adapters["classifier"], classifier_http = jev_adapter(spec["classifier"])
    gw = real_gateway(sink=sink, ledger=ledger, **adapters)
    state = pf.make_state(spec["text"], turn_id=pf.TURN_1).model_copy(update={"thread_id": THREAD})
    with case_ctx(sink, pf.TURN_1) as ctx:
        run = CaseRun(case_id, ledger, sink, ctx)
        deps = pf.make_deps(gw)
        rt = pf.runtime(ctx)
        update = planner(state, rt, deps=deps)
        run.results["planner"] = update
        state = state.model_copy(update=dict(update))
        if "classifier" in spec:
            danger = danger_classifier(state, rt, deps=deps)
            run.results["danger"] = danger
            run.check_events = list(danger["check_events"])
            state = pf.merged(state, danger)
        joined = plan_join(state, rt, deps=deps)
        run.results["plan_join"] = joined
        state = state.model_copy(update=dict(joined))
        if "classifier" in spec:
            run.results["route"] = route_after_plan_join(state)
    run.requests["jev_planner"] = len(planner_http)
    if fallback_rec is not None:
        run.requests["fallback"] = len(fallback_rec.requests)
    if "classifier" in spec:
        run.requests["jev_classifier"] = len(classifier_http)
    return _finish(run, caplog)


# --- AC-8: specialists ----------------------------------------------------------------------------------------------


def _tool_use(name: str, tool_input: object, call_id: str = "toolu_01") -> Handler:
    return ok(
        [{"type": "tool_use", "id": call_id, "name": name, "input": tool_input}], stop_reason="tool_use"
    )


DONE: Handler = ok([{"type": "text", "text": "Done."}])
_POINT = {"text": "Two tune-ups a year.", "passage_id": str(WP1_INCLUDES.passage_id)}
INVOICE_TASK = ("account", TaskIntent.READ_INVOICE, "What is my bill for?")
MEMBERSHIP_TASK = ("account", TaskIntent.READ_MEMBERSHIP, "What does my membership cost?")
KNOWLEDGE_TASK = ("knowledge", TaskIntent.ANSWER_QUESTION, pf.WP1)

SPECIALIST_CASES: dict[str, dict[str, Any]] = {
    "unknown-tool": {"task": KNOWLEDGE_TASK, "steps": [_tool_use("issue_refund", {"amount_cents": 47800})]},
    "not-allowed": {"task": KNOWLEDGE_TASK, "steps": [_tool_use("read_invoices", {})]},
    "args-none": {"task": KNOWLEDGE_TASK, "steps": [_tool_use("kb_search", "not-json{")]},
    "extra-customer-id": {
        "task": KNOWLEDGE_TASK,
        "steps": [_tool_use("kb_search", {"query": "membership", "customer_id": "C-0001"})],
    },
    "query-301": {
        "task": KNOWLEDGE_TASK,
        "steps": [_tool_use("kb_search", {"query": padded(MARK_QUERY, 301)})],
    },
    "invoice-pattern": {
        "task": INVOICE_TASK,
        "steps": [_tool_use("read_invoices", {"invoice_number": "INV-12"})],
    },
    "report-6-points": {
        "task": KNOWLEDGE_TASK,
        "steps": [
            ok(
                [
                    {
                        "type": "tool_use",
                        "id": "toolu_01",
                        "name": "kb_search",
                        "input": {"query": "membership"},
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_02",
                        "name": "report_facts",
                        "input": {"answered": True, "points": [_POINT] * 6},
                    },
                ],
                stop_reason="tool_use",
            )
        ],
        "tail": False,
    },
    "report-summary-301": {
        "task": MEMBERSHIP_TASK,
        "steps": [_tool_use("report_facts", {"summary": "s" * 301})],
        "tail": False,
    },
}
ACT_CASES: dict[str, Handler] = {
    "step-unparseable": respond(200, content=BAD_TEXT),
    "step-max-tokens": ok([{"type": "text", "text": "partial"}], stop_reason="max_tokens"),
    "step-refusal": ok([{"type": "text", "text": ""}], stop_reason="refusal"),
}


def _collect_lookups(run: CaseRun, store: Any) -> None:
    with store.uow() as tx:
        run.lookup_rows = list(tx.core.lookup_log.for_thread(THREAD))


def run_specialist_case(case_id: str, caplog: pytest.LogCaptureFixture) -> CaseRun:
    spec = SPECIALIST_CASES[case_id]
    kind, intent, text = spec["task"]
    sink, ledger = _begin(caplog)
    index = FakeIndex(passages=(WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM))
    handlers = [*spec["steps"], *([DONE] if spec.get("tail", True) else [])]
    adapter, recorder = adapter_for(sequence(*handlers))
    with temp_sqlite() as store, case_ctx(sink, rf.TURN_4) as ctx:
        ids = rf.seed(store, customer=[(rf.TURN_4, text)])
        run = CaseRun(case_id, ledger, sink, ctx)
        gw = real_gateway(sink=sink, ledger=ledger, specialist=adapter)

        def observe(outcome: RunOutcome) -> Any:
            run.outcome = outcome
            return SPECS[kind].build_result(outcome)

        specs = {**SPECS, kind: dataclasses.replace(SPECS[kind], build_result=observe)}
        runner = SpecialistRunner(
            gateway=gw,
            transcript=adapter,
            dispatcher=ToolDispatcher(build_registry(store, index), store.uow),
            specs=specs,
            brakes=Brakes(),
            trace=sink,
        )
        scope = ToolCallScope(
            ids=ctx.ids, customer_id=None, shown_slot_ids=frozenset(), now=ctx.now, message_id=ids[0]
        )
        task = make_task(kind, intent, text)
        run.results["specialist"] = runner.run(task, scope, ctx)
        _collect_lookups(run, store)
    assert run.outcome is not None
    run.tool_records = list(run.outcome.tools)
    run.requests["specialist"] = len(recorder.requests)
    run.next_request_bodies = recorder.bodies()[1:]
    run.results["index"] = index
    return _finish(run, caplog)


def run_act_case(case_id: str, caplog: pytest.LogCaptureFixture) -> CaseRun:
    sink, ledger = _begin(caplog)
    index = FakeIndex(passages=(WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM))
    adapter, recorder = adapter_for(ACT_CASES[case_id])
    with temp_sqlite() as store, case_ctx(sink, rf.TURN_4) as ctx:
        ids = rf.seed(store, customer=[(rf.TURN_4, pf.WP1)])
        run = CaseRun(case_id, ledger, sink, ctx)
        gw = real_gateway(sink=sink, ledger=ledger, specialist=adapter)
        runner = SpecialistRunner(
            gateway=gw,
            transcript=adapter,
            dispatcher=ToolDispatcher(build_registry(store, index), store.uow),
            specs=SPECS,
            brakes=Brakes(),
            trace=sink,
        )
        deps = GraphDeps(
            gateway=gw,
            retrieval=index,
            uow=store.uow,
            identity=cast(Any, None),
            scheduling=cast(Any, NoScheduling()),
            handoff=cast(Any, None),
            brief=cast(Any, None),
            demo=cast(Any, None),
            limits=Limits(),
            trace=sink,
            specialists=runner,
            cases=cast(Any, None),
            ledger=cast(Any, ledger),
        )
        planned = PlannedTask(
            order=1, specialist="knowledge", intent=TaskIntent.ANSWER_QUESTION, needs_identity=False
        )
        state = rf.state(turn_input=rf.turn_input(turn=rf.TURN_4, message_id=ids[0], text=pf.WP1))
        rt = pf.runtime(ctx)
        update = act.run_specialist(SpecialistSend(planned=planned, state=state), rt, deps=deps)
        state2 = state.model_copy(
            update={
                "specialist_results": update["specialist_results"],
                "plan": Plan(
                    mode="act", tasks=(planned,), handoff_request=None, topic="other", source="planner"
                ),
            }
        )
        run.results["update"] = update
        run.results["escalation"] = act.escalation(state2, rt, deps=deps)["escalation"]
        _collect_lookups(run, store)
    run.requests["specialist"] = len(recorder.requests)
    return _finish(run, caplog)


# --- AC-9: reply ----------------------------------------------------------------------------------------------------

DRAFT_CASES: dict[str, Handler] = {
    "draft-empty": _text({"text": ""}),
    "draft-1201": _text({"text": padded(MARK_DRAFT, 1201)}),
    "draft-extra-promise": _text({"text": "Your visit is booked.", "promise": "tomorrow"}),
    "draft-refusal": ok([{"type": "text", "text": ""}], stop_reason="refusal"),
}
DECISION = "Decide on the refund."


def _brief_body(cid: int, aid: int, rid: int) -> dict[str, dict[str, Any]]:
    q = {"message_id": cid, "text": "full refund"}
    base = {"needs": [q], "claims": [], "open_decision": DECISION}
    return {
        "brief-needs-0": {"needs": [], "claims": [], "open_decision": DECISION},
        "brief-needs-3": {**base, "needs": [q, q, q]},
        "brief-claims-6": {**base, "claims": [q] * 6},
        "brief-decision-201": {**base, "open_decision": "d" * 201},
        "quote-ai-message": {**base, "claims": [{"message_id": aid, "text": "the repair"}]},
        "quote-staff-message": {**base, "claims": [{"message_id": rid, "text": "reviewing your refund"}]},
        "quote-paraphrase": {
            **base,
            "claims": [{"message_id": cid, "text": "I want my money back " + MARK_DRAFT}],
        },
    }


BRIEF_CASE_IDS = (
    "brief-needs-0",
    "brief-needs-3",
    "brief-claims-6",
    "brief-decision-201",
    "quote-ai-message",
    "quote-staff-message",
    "quote-paraphrase",
)


def run_reply_case(case_id: str, caplog: pytest.LogCaptureFixture) -> CaseRun:
    sink, ledger = _begin(caplog)
    adapter, recorder = adapter_for(DRAFT_CASES[case_id])
    with temp_sqlite() as store, case_ctx(sink, rf.TURN_4) as ctx:
        ids = rf.seed(store, customer=[(rf.TURN_4, rf.WP7_MESSAGE)])
        run = CaseRun(case_id, ledger, sink, ctx)
        gw = real_gateway(sink=sink, ledger=ledger, responder=adapter)
        deps = rf.deps(uow=store.uow, gw=gw)
        state = rf.state(
            turn_input=rf.turn_input(turn=rf.TURN_4, message_id=ids[0], text=rf.WP7_MESSAGE),
            facts=rf.facts(),
            settled=rf.settled(),
        )
        rt = rf.run(ctx)
        upd = reply.responder(state, rt, deps=deps)
        s2 = state.model_copy(update={"draft": upd["draft"]})
        checked = reply.checks(s2, rt, deps=deps)["checked"]
        run.check_events = list(checked.events)
        run.results.update(
            update=upd,
            checked=checked,
            composed=ReplyComposer().compose(s2.model_copy(update={"checked": checked}), ctx),
        )
        _collect_lookups(run, store)
    run.requests["responder"] = len(recorder.requests)
    return _finish(run, caplog)


def run_brief_case(case_id: str, caplog: pytest.LogCaptureFixture) -> CaseRun:
    sink, ledger = _begin(caplog)
    with temp_sqlite() as store, case_ctx(sink, rf.TURN_4) as ctx:
        with store.uow(write=True) as tx:
            cid = tx.core.messages.append(
                THREAD, "customer", rf.WP7_MESSAGE, rf.NOW, turn_id=rf.TURN_4, kind="text"
            )
            aid = tx.core.messages.append(
                THREAD,
                "assistant",
                "I'm sorry the repair didn't fix it.",
                rf.NOW,
                turn_id=rf.TURN_4,
                kind="text",
            )
            rid = tx.core.messages.append(
                THREAD,
                "representative",
                "A team member is reviewing your refund.",
                rf.NOW,
                turn_id=rf.TURN_4,
                kind="text",
            )
            tx.commit()
        adapter, recorder = adapter_for(_text(_brief_body(cid, aid, rid)[case_id]))
        run = CaseRun(case_id, ledger, sink, ctx)
        gw = real_gateway(sink=sink, ledger=ledger, brief=adapter)
        cases = rf.FakeCaseService(rf.case_summary())
        deps = rf.deps(uow=store.uow, gw=gw, cases=cases, brief=cast(Any, BriefAssembler()))
        state = rf.state(
            turn_input=rf.turn_input(turn=rf.TURN_4, message_id=cid, text=rf.WP7_MESSAGE),
            handoff=rf.handoff_result(rf.case_summary()),
            facts=rf.facts(),
            settled=rf.settled(),
        )
        rt = rf.run(ctx)
        b = reply.brief(state, rt, deps=deps)
        checked = reply.checks(
            state.model_copy(update={"brief_extraction": b["brief_extraction"]}), rt, deps=deps
        )["checked"]
        run.check_events = list(checked.events)
        run.results.update(brief=b, checked=checked)
        run.stored_briefs = [brief for _, brief in cases.attached]
    run.requests["brief"] = len(recorder.requests)
    return _finish(run, caplog)
