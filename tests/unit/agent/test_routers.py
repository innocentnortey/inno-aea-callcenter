"""Routers over typed state, without a graph (AEA-21 AC-1, AC-2; DO-3 section 5.4, graph-core sections 5 and 11)."""

from __future__ import annotations

import ast
import datetime as dt
import typing
from pathlib import Path

import pytest
from langgraph.types import Send

from meridian.agent import routers
from meridian.domain import identity as idn
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import CustomerId, Halt, HaltReason
from meridian.domain.handoff import HandoffReason
from meridian.domain.state import ConversationState, OpenTask, TaskDetails
from meridian.domain.turn import DangerAssessment, EscalationDecision, GateKind, Plan, PlannedTask, TaskIntent
from tests.unit.agent.nodes import compose_fixtures as fx


def ident(status: str) -> idn.IdentityState:
    return idn.IdentityState.model_validate(
        {
            "status": status,
            "customer_id": "MHC-10001" if status == "verified" else None,
            "masked_hint": None,
            "code_expires_at": None,
            "tries_left": 3,
            "codes_sent": 0,
            "verified_at": None,
        }
    )


def task(
    order: int = 1, *, needs_identity: bool = True, specialist: typing.Any = "scheduling"
) -> PlannedTask:
    intent = TaskIntent.BOOK_NEW if specialist == "scheduling" else TaskIntent.ANSWER_QUESTION
    return PlannedTask(order=order, specialist=specialist, intent=intent, needs_identity=needs_identity)


def plan(
    *tasks: PlannedTask, mode: typing.Any = "act", handoff: HandoffReason | None = None, failed: bool = False
) -> Plan:
    return Plan(
        mode=mode,
        tasks=tasks,
        handoff_request=handoff,
        topic="other",
        source="planner",
        planner_failed=failed,
    )


def open_task(task_id: str = "t-1", status: typing.Any = "open") -> OpenTask:
    return OpenTask(
        task_id=task_id,
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        opened_turn=fx.TURN3,
        details=TaskDetails(),
        status=status,
    )


def halt(reason: HaltReason) -> Halt:
    return Halt(reason=reason, node="run_specialist", elapsed_ms=10)


def sends(result: typing.Any) -> list[Send]:
    assert isinstance(result, list)
    assert all(isinstance(s, Send) for s in result)
    return typing.cast(list[Send], result)


@pytest.mark.parametrize(
    ("gate", "expected"),
    [
        (fx.gate(GateKind.AI_PAUSED), "compose"),
        (fx.gate(GateKind.SAFETY), "safety"),
        (fx.gate(GateKind.BURNING_ASK), "safety"),
        (fx.gate(GateKind.DANGER_RULE), "safety"),
        (fx.gate(GateKind.BURNING_ANSWER, burning_answer="yes"), "safety"),
        (fx.gate(GateKind.BURNING_ANSWER, burning_answer="unsure"), "safety"),
        (fx.gate(GateKind.PERSON), "handoff"),
        (fx.gate(GateKind.CODE_ENTRY), "identity"),
        (fx.gate(GateKind.LOCATE), "identity"),
        (fx.gate(GateKind.FREE_TEXT), ["planner", "danger_classifier"]),
    ],
    ids=lambda v: v.kind.value if hasattr(v, "kind") else str(v),
)
def test_gates_edges(gate: typing.Any, expected: typing.Any) -> None:
    assert routers.route_after_gates(fx.state(gate=gate)) == expected


def test_gates_router_without_a_gate_raises() -> None:
    with pytest.raises(ValueError, match="no gate decision"):
        routers.route_after_gates(fx.state())


def test_burning_no_routes_act_plan() -> None:
    gate = fx.gate(GateKind.BURNING_ANSWER, burning_answer="no")
    code_plan = plan(task())
    assert (
        routers.route_after_gates(fx.state(gate=gate, plan=code_plan, identity=ident("not_checked")))
        == "identity"
    )
    out = sends(routers.route_after_gates(fx.state(gate=gate, plan=code_plan, identity=ident("verified"))))
    assert [(s.node, sorted(s.arg)) for s in out] == [("run_specialist", ["planned", "state"])]


def test_route_act_plan_sends_planned_tasks() -> None:
    three = plan(task(1), task(2, specialist="knowledge"), task(3, specialist="account"))
    st = fx.state(plan=three, identity=ident("verified"))
    out = sends(routers.route_act_plan(st))
    assert len(out) == 3
    for index, send in enumerate(out):
        assert send.node == "run_specialist"
        assert set(send.arg) == {"planned", "state"}
        assert send.arg["planned"] is three.tasks[index]
        assert send.arg["state"] is st
    with pytest.raises(ValueError, match="act plan with tasks"):
        routers.route_act_plan(fx.state(plan=plan()))
    with pytest.raises(ValueError, match="act plan with tasks"):
        routers.route_act_plan(fx.state())


def test_planner_failed_goes_to_escalation() -> None:
    failed = plan(failed=True)
    assert routers.route_after_plan_join(fx.state(plan=failed)) == "escalation"
    danger = DangerAssessment(label="danger", raised=True, failure=None)
    assert routers.route_after_plan_join(fx.state(plan=failed, danger=danger)) == "safety"


@pytest.mark.parametrize(
    ("name", "kw", "expected"),
    [
        (
            "danger_raised",
            {
                "danger": DangerAssessment(label="danger", raised=True, failure=None),
                "plan": plan(mode="talk"),
            },
            "safety",
        ),
        ("refund_talk", {"plan": plan(mode="talk", handoff=HandoffReason.REFUND)}, "escalation"),
        ("refund_act", {"plan": plan(mode="act", handoff=HandoffReason.REFUND)}, "escalation"),
        ("talk", {"plan": plan(mode="talk")}, "facts"),
        ("act_no_tasks", {"plan": plan(mode="act")}, "facts"),
        ("no_plan", {}, "facts"),
        ("act_needs_identity", {"plan": plan(task()), "identity": ident("not_checked")}, "identity"),
        ("act_verified", {"plan": plan(task()), "identity": ident("verified")}, "sends"),
    ],
)
def test_plan_join_edges(name: str, kw: dict[str, typing.Any], expected: str) -> None:
    result = routers.route_after_plan_join(fx.state(**kw))
    if expected == "sends":
        assert [s.node for s in sends(result)] == ["run_specialist"]
    else:
        assert result == expected


@pytest.mark.parametrize(
    ("step", "expected"),
    [
        (idn.NotVerified(), "escalation"),
        (idn.CodeLocked(), "escalation"),
        (idn.CodeCapReached(), "escalation"),
        (idn.CodeWrong(tries_left=2), "facts"),
        (
            idn.CodeSent(masked_hint="x", expires_at=fx.DEMO_NOW + dt.timedelta(minutes=10), sends_left=2),
            "facts",
        ),
    ],
    ids=lambda v: v.kind if hasattr(v, "kind") else str(v),
)
def test_identity_failures_and_prompts(step: typing.Any, expected: str) -> None:
    assert (
        routers.route_after_identity(fx.state(identity_step=step, identity=ident("not_checked"))) == expected
    )


def test_identity_edges() -> None:
    verified = ident("verified")
    proof = CompletedAction(
        key=ActionKey(thread_id=fx.THREAD, turn_id=fx.TURN4, kind=ActionKind.VERIFIED, record_id="MHC-10001"),
        kind=ActionKind.VERIFIED,
        records={"customer": "MHC-10001"},
        at=fx.DEMO_NOW,
    )
    done = idn.Verified(customer_id=CustomerId("MHC-10001"), action=proof)
    with_plan = fx.state(identity=verified, identity_step=done, plan=plan(task(1), task(2)))
    assert [s.node for s in sends(routers.route_after_identity(with_plan))] == ["run_specialist"] * 2
    resumed = fx.state(
        identity=verified, open_tasks=[open_task("t-9", "waiting_identity")], identity_step=done
    )
    only = sends(routers.route_after_identity(resumed))
    assert len(only) == 1
    assert only[0].arg["planned"].resumes_task_id == "t-9"
    assert routers.route_after_identity(fx.state(identity=ident("not_checked"))) == "facts"
    assert routers.route_after_identity(fx.state(identity=verified, identity_step=done)) == "facts"
    closed = fx.state(identity=verified, open_tasks=[open_task("t-1", "done")])
    assert routers.route_after_identity(closed) == "facts"


def test_card_choice_resumes_open_task() -> None:
    gate = fx.gate(GateKind.CARD_CHOICE, resume_task_id="t-1")
    out = sends(
        routers.route_after_gates(fx.state(gate=gate, open_tasks=[open_task()], identity=ident("verified")))
    )
    assert len(out) == 1
    planned = out[0].arg["planned"]
    assert (planned.resumes_task_id, planned.needs_identity, planned.order) == ("t-1", False, 1)
    waiting = fx.state(
        gate=gate, open_tasks=[open_task(status="waiting_identity")], identity=ident("not_checked")
    )
    assert routers.route_after_gates(waiting) == "identity"
    with pytest.raises(ValueError, match="not open"):
        routers.route_after_gates(fx.state(gate=gate, open_tasks=[open_task(status="done")]))


def test_specialists_edges() -> None:
    assert routers.route_after_specialists(fx.state()) == "escalation"


@pytest.mark.parametrize(
    ("outcome", "expected"), [("escalate", "handoff"), ("offer", "facts"), ("none", "facts")]
)
def test_escalation_edges(outcome: typing.Any, expected: str) -> None:
    decision = EscalationDecision(outcome=outcome, reason=None, priority=None, rule_id="x")
    assert routers.route_after_escalation(fx.state(escalation=decision)) == expected


def test_facts_edges() -> None:
    assert routers.route_after_facts(fx.state()) == ["responder"]
    created = fx.handoff_result("R26.unstaffed", "We will call.")
    assert routers.route_after_facts(fx.state(handoff=created)) == ["responder", "brief"]
    existing = created.model_copy(update={"created": False})
    assert routers.route_after_facts(fx.state(handoff=existing)) == ["responder"]


_BRAKES = [
    HaltReason.BRAKE_TASKS,
    HaltReason.BRAKE_TOOL_ROUNDS,
    HaltReason.BRAKE_SONNET_CALLS,
    HaltReason.BRAKE_IDENTICAL_CALL,
]
_OTHERS = [
    HaltReason.DEADLINE,
    HaltReason.SPEND_CAP,
    HaltReason.PROVIDER_SPEND_CAP,
    HaltReason.RECURSION_LIMIT,
]
_ROUTERS: dict[str, typing.Callable[[ConversationState], typing.Any]] = {
    "gates": routers.route_after_gates,
    "identity": routers.route_after_identity,
    "plan_join": routers.route_after_plan_join,
    "specialists": routers.route_after_specialists,
    "escalation": routers.route_after_escalation,
    "facts": routers.route_after_facts,
}
_ESCALATE = EscalationDecision(outcome="escalate", reason=None, priority=None, rule_id="AI.halt")


@pytest.mark.parametrize("name", list(_ROUTERS))
@pytest.mark.parametrize("reason", _BRAKES + _OTHERS, ids=lambda r: r.value)
def test_halt_route_from_every_router(name: str, reason: HaltReason) -> None:
    router = _ROUTERS[name]
    handoff = fx.handoff_result("R26.unstaffed", "We will call.")
    brake = reason in _BRAKES
    # escalation has not run yet / has run but opened no case / has run and opened a case
    before = fx.state(halt=halt(reason), escalation=_ESCALATE if name == "escalation" else None)
    after = fx.state(halt=halt(reason), escalation=_ESCALATE, handoff=handoff)
    expected_before = {"facts": "compose", "escalation": "handoff" if brake else "compose"}.get(
        name, "escalation" if brake else "compose"
    )
    assert router(before) == expected_before
    assert router(after) == "compose"


def test_halt_route_itself() -> None:
    assert routers.halt_route(fx.state()) is None
    assert routers.halt_route(fx.state(halt=halt(HaltReason.BRAKE_TASKS))) == "escalation"
    assert routers.halt_route(fx.state(halt=halt(HaltReason.DEADLINE))) == "compose"


def test_routers_never_import_act() -> None:
    path = Path(routers.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    print("routers.py imports:", sorted(imported))
    forbidden = [
        m
        for m in imported
        if m.startswith(
            ("meridian.agent.nodes", "meridian.agent.graph", "meridian.adapters", "meridian.services")
        )
    ]
    assert forbidden == []
