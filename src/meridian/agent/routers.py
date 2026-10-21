"""Pure routers over typed state (graph-core sections 5 and 11, DO-3 section 5.4; plan decisions PD-1 to PD-6).

Imports no node module, no graph module, no service and no adapter: a router reads typed fields and returns a name.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final, Literal, TypeAlias

from langgraph.types import Send

from meridian.domain.common import HaltReason
from meridian.domain.state import ConversationState, OpenTask, SpecialistSend
from meridian.domain.turn import GateKind, PlannedTask

__all__ = [
    "BRAKE_HALTS",
    "RouterResult",
    "halt_route",
    "route_act_plan",
    "route_after_escalation",
    "route_after_facts",
    "route_after_gates",
    "route_after_identity",
    "route_after_plan_join",
    "route_after_specialists",
]

BRAKE_HALTS: Final[frozenset[HaltReason]] = frozenset(
    {
        HaltReason.BRAKE_TASKS,
        HaltReason.BRAKE_TOOL_ROUNDS,
        HaltReason.BRAKE_SONNET_CALLS,
        HaltReason.BRAKE_IDENTICAL_CALL,
    }
)
RouterResult: TypeAlias = str | list[str] | list[Send]
_FAN_OUT_NODE: Final = "run_specialist"
_IDENTITY_FAILURES: Final = frozenset({"not_verified", "code_locked", "code_cap_reached"})


def halt_route(state: ConversationState) -> Literal["escalation", "compose"] | None:
    """Where a halted state goes: a brake once through escalation, every other halt straight to compose."""
    halt = state.halt
    if halt is None:
        return None
    if halt.reason in BRAKE_HALTS and state.escalation is None:
        return "escalation"
    return "compose"


def _open(state: ConversationState) -> list[OpenTask]:
    return [t for t in state.open_tasks if t.status != "done"]


def _resumed(tasks: Sequence[OpenTask]) -> list[PlannedTask]:
    """PD-4: the open task's own status says whether it waits on identity."""
    return [
        PlannedTask(
            order=i + 1,
            specialist=t.specialist,
            intent=t.intent,
            needs_identity=(t.status == "waiting_identity"),
            resumes_task_id=t.task_id,
        )
        for i, t in enumerate(tasks[:3])
    ]


def _route_planned(
    planned: Sequence[PlannedTask], state: ConversationState
) -> Literal["identity"] | list[Send]:
    """Identity first when a task needs it and the customer is not verified, else one Send per task (R-G-12)."""
    if any(t.needs_identity for t in planned) and state.identity.status != "verified":
        return "identity"
    return [Send(_FAN_OUT_NODE, SpecialistSend(planned=t, state=state)) for t in planned]


def route_act_plan(state: ConversationState) -> Literal["identity"] | list[Send]:
    plan = state.plan
    if plan is None or not plan.tasks:
        raise ValueError("route_act_plan needs an act plan with tasks")
    return _route_planned(plan.tasks, state)


def route_after_gates(state: ConversationState) -> RouterResult:
    routed = halt_route(state)
    if routed is not None:
        return routed
    gate = state.gate
    if gate is None:
        raise ValueError("gates router: no gate decision")
    kind = gate.kind
    if kind is GateKind.AI_PAUSED:
        return "compose"
    if kind in (GateKind.SAFETY, GateKind.BURNING_ASK, GateKind.DANGER_RULE):
        return "safety"
    if kind is GateKind.BURNING_ANSWER:
        return route_act_plan(state) if gate.burning_answer == "no" else "safety"
    if kind is GateKind.PERSON:
        return "handoff"
    if kind in (GateKind.CODE_ENTRY, GateKind.LOCATE):
        return "identity"
    if kind is GateKind.CARD_CHOICE:
        task = next((t for t in _open(state) if t.task_id == gate.resume_task_id), None)
        if task is None:
            raise ValueError("card choice resumes a task that is not open")
        return _route_planned(_resumed([task]), state)
    return ["planner", "danger_classifier"]


def route_after_identity(state: ConversationState) -> RouterResult:
    routed = halt_route(state)
    if routed is not None:
        return routed
    step = state.identity_step
    if step is not None and step.kind in _IDENTITY_FAILURES:
        return "escalation"
    if state.identity.status == "verified":
        plan = state.plan
        if plan is not None and plan.mode == "act" and plan.tasks:
            return route_act_plan(state)
        open_tasks = _open(state)
        if open_tasks:
            return _route_planned(_resumed(open_tasks), state)
    return "facts"


def route_after_plan_join(state: ConversationState) -> RouterResult:
    routed = halt_route(state)
    if routed is not None:
        return routed
    if state.danger is not None and state.danger.raised:
        return "safety"
    plan = state.plan
    if plan is None:
        return "facts"
    if plan.planner_failed and not plan.tasks:
        return "escalation"
    if not plan.tasks and plan.handoff_request is not None:
        return "escalation"
    if plan.mode == "talk":
        return "facts"
    if not plan.tasks:
        return "facts"
    return route_act_plan(state)


def route_after_specialists(state: ConversationState) -> RouterResult:
    routed = halt_route(state)
    if routed is not None:
        return routed
    return "escalation"


def route_after_escalation(state: ConversationState) -> RouterResult:
    routed = halt_route(state)
    halt = state.halt
    brake_before_case = halt is not None and halt.reason in BRAKE_HALTS and state.handoff is None
    if routed is not None and not brake_before_case:
        return routed
    if state.escalation is None:
        return "facts"
    if state.escalation.outcome == "escalate":
        return "handoff"
    return "facts"


def route_after_facts(state: ConversationState) -> RouterResult:
    if halt_route(state) is not None:
        return "compose"
    if state.handoff is not None and state.handoff.created:
        return ["responder", "brief"]
    return ["responder"]
