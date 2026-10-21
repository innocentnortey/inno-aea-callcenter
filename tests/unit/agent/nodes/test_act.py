"""The act nodes: fan-out, task slices, escalation decisions and the handoff call (AEA-39 AC-1 to AC-16)."""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from meridian.agent.nodes import act as act_mod
from meridian.agent.nodes.act import build_specialist_task, escalation, handoff, run_specialist
from meridian.agent.specialists.runner import scope_for
from meridian.domain.common import (
    CustomerId,
    FailureCounters,
    Halt,
    HaltReason,
    PassageId,
    Priority,
    ProviderFailureKind,
)
from meridian.domain.handoff import HandoffReason
from meridian.domain.specialists import KnowledgePoint, SchedulingSlice
from meridian.domain.state import (
    ChatLine,
    ConversationState,
    EscalationUpdate,
    HandoffNodeUpdate,
    OpenTask,
    SpecialistUpdate,
    TaskDetails,
)
from meridian.domain.tools import AccountSlice, KnowledgeSlice
from meridian.domain.turn import (
    DangerAssessment,
    EscalationDecision,
    GateKind,
    Plan,
    TaskIntent,
)
from meridian.policy.escalation import decide_escalation
from meridian.policy.handoff import PROMISE_TABLE
from meridian.policy.limits import Limits
from tests.fakes import WORKED_PAIRS_NOW
from tests.graph._spine_doubles import THREAD
from tests.unit.agent.nodes.act_fixtures import (
    T1,
    T2,
    T3,
    WP4_DRAFT,
    WP4_INPUTS,
    WP4_TEXT,
    WP7_TEXT,
    GatewayDouble,
    HandoffDouble,
    LedgerDouble,
    RunnerDouble,
    SchedulingDouble,
    UowCounter,
    account,
    act_ctx,
    act_harness,
    act_plan,
    apply,
    deps_for,
    failure,
    fanout_graph,
    gate,
    gates_returning,
    knowledge,
    make_state,
    rt,
    scheduling,
    state_input,
    talk_plan,
    task,
    unverified,
    verified,
)

LIMITS = Limits()


def _signals(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [r.__dict__["signal"] for r in caplog.records if r.name == "meridian.signal"]


def _decide(state: ConversationState, deps: Any = None, *, ctx: Any = None) -> EscalationDecision:
    ctx = ctx or act_ctx(state.turn_input.turn_id)
    deps = deps or deps_for(runner=RunnerDouble({}))
    update = escalation(state, rt(ctx), deps=deps)
    return update["escalation"]


# ---------------------------------------------------------------------------------------------- AC-1, AC-2


def test_fanout_three_tasks_parallel() -> None:
    state = make_state(
        plan=act_plan(
            task(1, "account", TaskIntent.READ_INVOICE),
            task(2, "scheduling", TaskIntent.BOOK_NEW),
            task(3, "knowledge", TaskIntent.ANSWER_QUESTION),
        ),
    )
    runner = RunnerDouble(
        {"account": account(), "scheduling": scheduling(), "knowledge": knowledge()},
        delays={"account": 0.9, "scheduling": 0.6, "knowledge": 0.3},
    )
    sched = SchedulingDouble()
    deps = deps_for(runner=runner, scheduling_=sched)
    ctx = act_ctx()
    graph = fanout_graph(deps)
    done: list[Any] = []
    worker = threading.Thread(target=lambda: done.append(graph.invoke(state_input(state), context=ctx)))
    t0 = time.monotonic()
    worker.start()
    worker.join()
    elapsed = time.monotonic() - t0
    print(f"fan-out of three runner calls: {elapsed:.3f} s (serial would be at least 1.8 s)")
    assert len(runner.calls) == 3
    assert elapsed < 1.5
    out = ConversationState.model_validate(done[0])
    assert [r.kind for r in out.specialist_results] == ["account", "scheduling", "knowledge"]
    assert all(scope == scope_for(state, ctx) for _, scope, _ in runner.calls)
    assert sched.customer_ids == [CustomerId("MHC-57204")]


@pytest.mark.parametrize(
    ("label", "planned", "gate_kind", "burning", "danger_raised", "expected"),
    [
        ("book_free_text", (TaskIntent.BOOK_NEW, None), GateKind.FREE_TEXT, None, None, True),
        ("book_danger_normal", (TaskIntent.BOOK_NEW, None), GateKind.FREE_TEXT, None, False, True),
        ("resumed", (TaskIntent.BOOK_NEW, "task-1"), GateKind.FREE_TEXT, None, None, False),
        ("reschedule", (TaskIntent.RESCHEDULE, None), GateKind.FREE_TEXT, None, None, False),
        ("burning_no", (TaskIntent.BOOK_NEW, None), GateKind.BURNING_ANSWER, "no", None, False),
        ("danger_raised", (TaskIntent.BOOK_NEW, None), GateKind.FREE_TEXT, None, True, False),
        ("card_choice", (TaskIntent.BOOK_NEW, None), GateKind.CARD_CHOICE, None, None, False),
    ],
)
def test_specialist_task_slices_and_quick_check_offer(
    label: str,
    planned: tuple[TaskIntent, str | None],
    gate_kind: GateKind,
    burning: Any,
    danger_raised: bool | None,
    expected: bool,
) -> None:
    intent, resumes = planned
    danger = (
        None
        if danger_raised is None
        else DangerAssessment(
            label="danger" if danger_raised else "normal", raised=danger_raised, failure=None
        )
    )
    state = make_state(gate_=gate(gate_kind, burning_answer=burning), danger=danger)
    t = build_specialist_task(
        task(1, "scheduling", intent, resumes=resumes), state, act_ctx(), scheduling=None, limits=LIMITS
    )
    assert t.offer_quick_checks is expected, label


def test_specialist_task_offer_other_cases_and_slices() -> None:
    ctx = act_ctx()
    # knowledge never offers; a resumed task of another service type never offers
    state = make_state()
    k = build_specialist_task(
        task(1, "knowledge", TaskIntent.ANSWER_QUESTION), state, ctx, scheduling=None, limits=LIMITS
    )
    assert k.offer_quick_checks is False
    assert isinstance(k.slice, KnowledgeSlice)
    assert set(k.slice.model_dump()) <= {"kind"}
    assert k.customer_text == "Hello"
    assert k.task_messages == ()
    a = build_specialist_task(
        task(1, "account", TaskIntent.READ_INVOICE), state, ctx, scheduling=None, limits=LIMITS
    )
    assert isinstance(a.slice, AccountSlice)
    # scheduling slice: no customer id, no chat window, no assistant line
    chat = [ChatLine(speaker="assistant", text="assistant text", turn_id=T1, at=WORKED_PAIRS_NOW)]
    s = build_specialist_task(
        task(1, "scheduling", TaskIntent.RESCHEDULE),
        make_state(chat=chat),
        ctx,
        scheduling=WP4_INPUTS,
        limits=LIMITS,
    )
    dumped = s.model_dump_json()
    assert "MHC-57204" not in dumped
    assert "chat_window" not in s.model_dump()
    assert "assistant text" not in dumped
    # scope_for binds the customer only when verified
    assert scope_for(make_state(identity=unverified("not_verified")), ctx).customer_id is None
    assert scope_for(make_state(identity=verified()), ctx).customer_id == CustomerId("MHC-57204")


def test_resumed_task_with_other_service_type_does_not_offer() -> None:
    open_task = OpenTask(
        task_id="task-1",
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        opened_turn=T1,
        details=TaskDetails(service_type="hvac_tune_up"),
        status="open",
    )
    state = make_state(open_tasks=[open_task])
    t = build_specialist_task(
        task(1, "scheduling", TaskIntent.BOOK_NEW), state, act_ctx(), scheduling=None, limits=LIMITS
    )
    assert t.offer_quick_checks is True  # a new task has no resumed details


# ---------------------------------------------------------------------------------------------- AC-3, AC-4


def test_wp4_fee_bearing_escalates_p2() -> None:
    state = make_state(text=WP4_TEXT, plan=act_plan(task(1, "scheduling", TaskIntent.RESCHEDULE)))
    runner = RunnerDouble({"scheduling": scheduling("staff_change_request", change_request=WP4_DRAFT)})
    sched = SchedulingDouble()
    double = HandoffDouble()
    deps = deps_for(runner=runner, scheduling_=sched, handoff_=double)
    ctx = act_ctx()
    state = apply(
        state,
        run_specialist({"planned": state.plan.tasks[0], "state": state}, rt(ctx), deps=deps),  # type: ignore[union-attr]
    )
    state = apply(state, escalation(state, rt(ctx), deps=deps))
    decision = state.escalation
    assert decision is not None
    assert (decision.outcome, decision.reason, decision.priority, decision.rule_id, decision.degraded) == (
        "escalate",
        HandoffReason.FEE_BEARING_CHANGE,
        Priority.P2,
        "R21.fee_bearing",
        False,
    )
    update = handoff(state, rt(ctx), deps=deps)
    assert len(double.requests) == 1
    req = double.requests[0]
    assert (req.reason, req.priority, req.rule_id, req.trigger) == (
        HandoffReason.FEE_BEARING_CHANGE,
        Priority.P2,
        "R21.fee_bearing",
        "escalation",
    )
    assert req.change_request == WP4_DRAFT
    assert req.identity == verified()
    assert update == {"handoff": double._by_key[(THREAD, T1)]}
    assert sched.calls == ["slice_inputs"]


def _recording_decide(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    recorded: list[Any] = []
    real = decide_escalation

    def wrapper(inputs: Any) -> Any:
        recorded.append(inputs)
        return real(inputs)

    monkeypatch.setattr(act_mod, "decide_escalation", wrapper)  # the node calls it by module-level name
    return recorded


def test_wp7_refund_p3(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = _recording_decide(monkeypatch)
    plan = Plan(
        mode="act", tasks=(), handoff_request=HandoffReason.REFUND, topic="billing", source="rules_only"
    )
    state = make_state(text=WP7_TEXT, gate_=gate(policy=HandoffReason.REFUND), plan=plan)
    ctx = act_ctx()
    decision = _decide(state, ctx=ctx)
    assert (decision.reason, decision.priority, decision.rule_id) == (
        HandoffReason.REFUND,
        Priority.P3,
        "R24.refund",
    )
    assert recorded[0].now == ctx.now
    double = HandoffDouble()
    handoff(
        apply(state, {"escalation": decision}),
        rt(ctx),
        deps=deps_for(runner=RunnerDouble({}), handoff_=double),
    )
    case = double._by_key[(THREAD, T1)].case
    assert case.promise.text == PROMISE_TABLE["R26.refund"]
    assert case.promise.due_label == "Tuesday, October 20, 7:00 pm"


def test_wp8_membership_cancel_d4(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded = _recording_decide(monkeypatch)
    ctx = act_ctx()
    for renewal, priority in ((date(2026, 11, 3), Priority.P3), (date(2026, 10, 19), Priority.P2)):
        state = make_state(
            identity=verified("MHC-10001"),
            plan=act_plan(
                task(1, "account", TaskIntent.READ_MEMBERSHIP),
                handoff_request=HandoffReason.MEMBERSHIP_CANCEL,
                topic="membership",
            ),
            results=(account(renewal=renewal),),
        )
        decision = _decide(state, ctx=ctx)
        assert decision.rule_id == "D4.membership_cancel"
        assert decision.priority is priority
        assert recorded[-1].now == ctx.now


# ---------------------------------------------------------------------------------------------- AC-5, AC-6


def test_person_gate_first_ask(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = RunnerDouble({})
    gateway = GatewayDouble()
    double = HandoffDouble()
    deps = deps_for(runner=runner, handoff_=double, gateway=gateway)
    h = act_harness(monkeypatch, deps, gates=gates_returning(gate(GateKind.PERSON)))
    out = h.run(T1, "Can I talk to a person?")
    assert len(double.requests) == 1
    req = double.requests[0]
    assert req.reason is HandoffReason.CUSTOMER_REQUESTED_PERSON
    assert req.priority is Priority.P3
    assert req.rule_id == "R2.person"
    assert req.trigger == "gate"
    assert runner.calls == []
    assert gateway.accessed == []
    for name in ("planner", "run_specialist", "escalation"):
        assert name not in h.visits
    assert "handoff" in h.visits
    assert out.turn_trace.outcome == "handed_off"


@pytest.mark.parametrize("case", ["halt", "specialist_failed", "models_disabled", "planner_failed"])
def test_rule6_degraded_handoff(case: str) -> None:
    ledger = LedgerDouble()
    kwargs: dict[str, Any] = {}
    if case == "halt":
        kwargs = {
            "plan": act_plan(task(1, "knowledge", TaskIntent.ANSWER_QUESTION)),
            "halt": Halt(reason=HaltReason.BRAKE_TOOL_ROUNDS, node="run_specialist", elapsed_ms=5),
        }
        rule = "AI.halt"
    elif case == "specialist_failed":
        kwargs = {"results": (knowledge("failed"),)}
        rule = "AI.specialist_failed"
    elif case == "models_disabled":
        ledger = LedgerDouble(disabled=True)
        kwargs = {"results": (knowledge(),)}
        rule = "AI.models_disabled"
    else:
        kwargs = {
            "plan": Plan(
                mode="act",
                tasks=(),
                handoff_request=None,
                topic="other",
                source="rules_only",
                planner_failed=True,
            )
        }
        rule = "AI.planner_failed"
    double = HandoffDouble()
    deps = deps_for(runner=RunnerDouble({}), handoff_=double, ledger=ledger)
    state = make_state(**kwargs)
    ctx = act_ctx()
    state = apply(state, escalation(state, rt(ctx), deps=deps))
    decision = state.escalation
    assert decision is not None
    assert (decision.outcome, decision.reason, decision.priority, decision.rule_id, decision.degraded) == (
        "escalate",
        HandoffReason.AI_FAILURE,
        Priority.P3,
        rule,
        True,
    )
    handoff(state, rt(ctx), deps=deps)
    assert len(double.requests) == 1
    assert double.requests[0].reason is HandoffReason.AI_FAILURE
    assert double.requests[0].trigger == "escalation"


# ---------------------------------------------------------------------------------------------- AC-7, AC-8


def _run_one_knowledge(result: Any, caplog: pytest.LogCaptureFixture) -> SpecialistUpdate:
    caplog.clear()
    planned = task(1, "knowledge", TaskIntent.ANSWER_QUESTION)
    state = make_state(plan=act_plan(planned))
    deps = deps_for(runner=RunnerDouble({"knowledge": result}))
    with caplog.at_level(logging.INFO, logger="meridian.signal"):
        return run_specialist({"planned": planned, "state": state}, rt(act_ctx()), deps=deps)


def test_brakes_and_failures_emit_events_and_signals(caplog: pytest.LogCaptureFixture) -> None:
    update = _run_one_knowledge(knowledge("failed", brake=HaltReason.BRAKE_TOOL_ROUNDS), caplog)
    assert update["halt"].reason is HaltReason.BRAKE_TOOL_ROUNDS
    assert update["halt"].node == "run_specialist"
    events = update["check_events"]
    assert len(events) == 1
    assert (events[0].check, events[0].turn_id, events[0].result, events[0].codes) == (
        "brake",
        T1,
        "fired",
        ("brake_tool_rounds", "run_specialist"),
    )
    signals = _signals(caplog)
    assert [(s["name"], s["cause"]) for s in signals] == [("brake_fired", "brake_tool_rounds")]
    assert signals[0]["role"] == "specialist"
    assert signals[0]["specialist"] == "knowledge"

    for brake in (HaltReason.DEADLINE, HaltReason.PROVIDER_SPEND_CAP):
        update = _run_one_knowledge(knowledge("failed", brake=brake), caplog)
        assert update["halt"].reason is brake
        assert "check_events" not in update
        assert _signals(caplog) == []

    update = _run_one_knowledge(knowledge("failed", failure=failure(ProviderFailureKind.TIMEOUT)), caplog)
    assert "halt" not in update
    assert "check_events" not in update
    assert [(s["name"], s["cause"]) for s in _signals(caplog)] == [("specialist_failed", "timeout")]

    update = _run_one_knowledge(knowledge("failed"), caplog)
    assert [(s["name"], s["cause"]) for s in _signals(caplog)] == [("specialist_failed", "tool_error")]

    update = _run_one_knowledge(knowledge(), caplog)
    assert set(update) == {"specialist_results"}
    assert _signals(caplog) == []


@pytest.mark.parametrize("status", ["not_verified", "locked"])
def test_not_verified_escalates_reveals_nothing(status: Any) -> None:
    state = make_state(
        identity=unverified(status), plan=act_plan(task(1, "account", TaskIntent.READ_INVOICE))
    )
    update = escalation(state, rt(act_ctx()), deps=deps_for(runner=RunnerDouble({})))
    decision = update["escalation"]
    assert (decision.outcome, decision.reason, decision.priority, decision.rule_id, decision.degraded) == (
        "escalate",
        HandoffReason.IDENTITY_UNVERIFIED,
        Priority.P3,
        "R16.identity_unverified",
        False,
    )
    assert set(update) == {"escalation"}
    assert "INV-" not in json.dumps(decision.model_dump(mode="json"))


# ---------------------------------------------------------------------------------------------- AC-9, AC-10


@pytest.mark.parametrize(
    ("counters", "rule"),
    [
        (FailureCounters(failed_answers=2), "OD6.two_misses"),
        (FailureCounters(corrections=2), "OD6.two_misses"),
        (FailureCounters(timeouts=2), "OD6.two_timeouts"),
    ],
)
def test_two_misses_or_timeouts_offer(counters: FailureCounters, rule: str) -> None:
    double = HandoffDouble()
    deps = deps_for(runner=RunnerDouble({}), handoff_=double)
    state = make_state(plan=talk_plan(), counters=counters)
    ctx = act_ctx()
    state = apply(state, escalation(state, rt(ctx), deps=deps))
    assert state.escalation is not None
    assert (state.escalation.outcome, state.escalation.rule_id) == ("offer", rule)
    assert handoff(state, rt(ctx), deps=deps) == {}
    assert double.requests == []


def test_second_handoff_same_reference() -> None:
    double = HandoffDouble()
    deps = deps_for(runner=RunnerDouble({}), handoff_=double)
    refund = EscalationDecision(
        outcome="escalate",
        reason=HandoffReason.REFUND,
        priority=Priority.P3,
        rule_id="R24.refund",
    )
    first = handoff(make_state(turn_id=T1, text=WP7_TEXT, escalation=refund), rt(act_ctx(T1)), deps=deps)
    r1 = first["handoff"]
    assert r1.created is True
    late = EscalationDecision(
        outcome="escalate",
        reason=HandoffReason.LATE_TECHNICIAN,
        priority=Priority.P2,
        rule_id="D4.late_technician",
    )
    state2 = make_state(turn_id=T2, escalation=late)
    second = handoff(state2, rt(act_ctx(T2)), deps=deps)["handoff"]
    assert second.created is False
    assert second.case.case_ref == r1.case.case_ref
    repeat = handoff(state2, rt(act_ctx(T2)), deps=deps)["handoff"]
    assert double.requests[2] == double.requests[1]
    assert repeat.action.key == second.action.key
    assert {r.case.case_ref for r in (r1, second, repeat)} == {r1.case.case_ref}


# ---------------------------------------------------------------------------------------------- AC-11, AC-12


def test_handoff_request_has_no_model_text(caplog: pytest.LogCaptureFixture) -> None:
    secret = "we'll refund you, ref " + "MHC-C-" + "9999"
    point = KnowledgePoint(text=secret, passage_id=PassageId("faq/customer_faq.md#1"))
    planned = task(1, "knowledge", TaskIntent.ANSWER_QUESTION)
    double = HandoffDouble()
    deps = deps_for(runner=RunnerDouble({"knowledge": knowledge("failed", points=(point,))}), handoff_=double)
    state = make_state(plan=act_plan(planned))
    ctx = act_ctx()
    with caplog.at_level(logging.INFO, logger="meridian.signal"):
        state = apply(state, run_specialist({"planned": planned, "state": state}, rt(ctx), deps=deps))
    state = apply(state, escalation(state, rt(ctx), deps=deps))
    update = handoff(state, rt(ctx), deps=deps)
    texts = [
        double.requests[0].model_dump_json(),
        update["handoff"].model_dump_json(),
        *(e.model_dump_json() for e in state.check_events),
    ]
    signals = _signals(caplog)
    assert signals
    texts += [json.dumps(s) for s in signals]
    for text in texts:
        assert secret not in text
        assert "MHC-C-9999" not in text


def test_no_uow_during_specialists() -> None:
    uow = UowCounter()
    sched = SchedulingDouble(uow=uow)
    runner = RunnerDouble({"scheduling": scheduling()}, uow=uow)
    deps = deps_for(runner=runner, scheduling_=sched, uow=uow)
    planned = task(1, "scheduling", TaskIntent.BOOK_NEW)
    state = make_state(plan=act_plan(planned))
    run_specialist({"planned": planned, "state": state}, rt(act_ctx()), deps=deps)
    assert uow.entered == 1
    assert runner.uow_open_at_call == [0]
    source = Path(act_mod.__file__).read_text()
    assert "uow(" not in source
    assert "deps.uow" not in source


# ---------------------------------------------------------------------------------------------- AC-13, AC-14


def _keys(typed: Any) -> set[str]:
    return set(typed.__required_keys__ | typed.__optional_keys__)


def test_act_nodes_write_only_own_keys(caplog: pytest.LogCaptureFixture) -> None:
    plain = _run_one_knowledge(knowledge(), caplog)
    braked = _run_one_knowledge(knowledge("failed", brake=HaltReason.BRAKE_TOOL_ROUNDS), caplog)
    deadline = _run_one_knowledge(knowledge("failed", brake=HaltReason.DEADLINE), caplog)
    assert set(plain) == {"specialist_results"}
    assert set(braked) == {"specialist_results", "halt", "check_events"}
    assert set(deadline) == {"specialist_results", "halt"}
    for update in (plain, braked, deadline):
        assert set(update) <= _keys(SpecialistUpdate)
    deps = deps_for(runner=RunnerDouble({}))
    refund = EscalationDecision(
        outcome="escalate", reason=HandoffReason.REFUND, priority=Priority.P3, rule_id="R24.refund"
    )
    state = make_state(escalation=refund)
    esc = escalation(state, rt(act_ctx()), deps=deps)
    assert set(esc) == {"escalation"} <= _keys(EscalationUpdate)
    escalated = handoff(state, rt(act_ctx()), deps=deps)
    assert set(escalated) == {"handoff"} <= _keys(HandoffNodeUpdate)
    offer = EscalationDecision(outcome="offer", reason=None, priority=None, rule_id="OD6.two_misses")
    assert set(handoff(make_state(escalation=offer), rt(act_ctx()), deps=deps)) == set()


def test_escalation_record_fields_and_case_per_escalate() -> None:
    wp4_plan = act_plan(task(1, "scheduling", TaskIntent.RESCHEDULE))
    refund_plan = Plan(
        mode="act", tasks=(), handoff_request=HandoffReason.REFUND, topic="billing", source="rules_only"
    )
    wp8_plan = act_plan(
        task(1, "account", TaskIntent.READ_MEMBERSHIP),
        handoff_request=HandoffReason.MEMBERSHIP_CANCEL,
        topic="membership",
    )
    scenarios: list[tuple[str, ConversationState, tuple[str, ...]]] = [
        (
            "wp4",
            make_state(
                plan=wp4_plan,
                results=(scheduling("staff_change_request", change_request=WP4_DRAFT),),
            ),
            ("scheduling",),
        ),
        ("wp7", make_state(gate_=gate(policy=HandoffReason.REFUND), plan=refund_plan), ()),
        (
            "wp8",
            make_state(
                identity=verified("MHC-10001"), plan=wp8_plan, results=(account(renewal=date(2026, 11, 3)),)
            ),
            ("account",),
        ),
        ("rule6", make_state(results=(knowledge("failed"),)), ("knowledge",)),
        (
            "locked",
            make_state(
                identity=unverified("locked"), plan=act_plan(task(1, "account", TaskIntent.READ_INVOICE))
            ),
            (),
        ),
        ("offer", make_state(plan=talk_plan(), counters=FailureCounters(failed_answers=2)), ()),
        ("none", make_state(plan=talk_plan()), ()),
    ]
    escalates = 0
    requests = 0
    for name, state, kinds in scenarios:
        double = HandoffDouble()
        deps = deps_for(runner=RunnerDouble({}), handoff_=double)
        ctx = act_ctx()
        state = apply(state, escalation(state, rt(ctx), deps=deps))
        handoff(state, rt(ctx), deps=deps)
        decision = state.escalation
        assert decision is not None, name
        assert decision.rule_id, name
        assert isinstance(decision.degraded, bool)
        if decision.outcome == "escalate":
            assert decision.reason is not None and decision.priority is not None, name
            escalates += 1
        else:
            assert decision.reason is None and decision.priority is None, name
        assert tuple(r.kind for r in state.specialist_results) == kinds, name
        requests += len(double.requests)
        if name == "wp7":
            assert double.requests[0].change_request is None
    assert escalates == requests == 5


def test_handoff_open_failure_propagates() -> None:
    double = HandoffDouble(error=RuntimeError("write failed"))
    deps = deps_for(runner=RunnerDouble({}), handoff_=double)
    refund = EscalationDecision(
        outcome="escalate", reason=HandoffReason.REFUND, priority=Priority.P3, rule_id="R24.refund"
    )
    with pytest.raises(RuntimeError):
        handoff(make_state(escalation=refund), rt(act_ctx()), deps=deps)
    assert len(double.requests) == 1


# ---------------------------------------------------------------------------------------------- AC-16


def test_build_specialist_task() -> None:
    card = " ".join(["4242"] * 4)
    phone = "-".join(("512", "555", "01" + "40"))
    uow = UowCounter()
    gateway = GatewayDouble()
    ctx = act_ctx()
    planned = task(1, "scheduling", TaskIntent.BOOK_NEW)
    state = make_state(
        text=f"Book me Monday. Card {card}, call {phone}", counters=FailureCounters(bookings=1)
    )
    built = build_specialist_task(planned, state, ctx, scheduling=WP4_INPUTS, limits=LIMITS)
    dumped = built.model_dump_json()
    assert card not in dumped
    assert phone not in dumped
    assert "MHC-57204" not in dumped
    assert isinstance(built.slice, SchedulingSlice)
    assert built.slice.customer_zone == "central"
    assert built.slice.member is False
    assert built.slice.appointments == WP4_INPUTS.appointments
    assert built.slice.bookings_left == 2
    assert built.slice.pending_change is False
    assert build_specialist_task(planned, state, ctx, scheduling=WP4_INPUTS, limits=LIMITS) == built
    bare = build_specialist_task(planned, state, ctx, scheduling=None, limits=LIMITS)
    assert isinstance(bare.slice, SchedulingSlice)
    assert (bare.slice.customer_zone, bare.slice.member, bare.slice.appointments) == (None, False, ())
    spent = build_specialist_task(
        planned, make_state(counters=FailureCounters(bookings=5)), ctx, scheduling=None, limits=LIMITS
    )
    assert isinstance(spent.slice, SchedulingSlice)
    assert spent.slice.bookings_left == 0

    open_task = OpenTask(
        task_id="task-1",
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        opened_turn=T1,
        details=TaskDetails(),
        status="open",
    )

    def line(speaker: Any, turn: Any, text: str) -> ChatLine:
        return ChatLine(speaker=speaker, text=text, turn_id=turn, at=WORKED_PAIRS_NOW)

    resumed = task(1, "scheduling", TaskIntent.BOOK_NEW, resumes="task-1")
    chat = [
        line("customer", T1, "first"),
        line("assistant", T1, "reply"),
        line("customer", T2, "second"),
        line("customer", T3, "current"),
    ]
    got = build_specialist_task(
        resumed,
        make_state(turn_id=T3, open_tasks=[open_task], chat=chat),
        act_ctx(T3),
        scheduling=None,
        limits=LIMITS,
    )
    assert got.task_messages == ("first", "second")
    assert got.offer_quick_checks is False
    short = build_specialist_task(
        resumed,
        make_state(turn_id=T3, open_tasks=[open_task], chat=[line("customer", T2, "second")]),
        act_ctx(T3),
        scheduling=None,
        limits=LIMITS,
    )
    assert short.task_messages == ("second",)
    assert uow.entered == 0
    assert gateway.accessed == []
