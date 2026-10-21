"""Stub of the plan node(s) with their final signatures (graph-nodes section 9). Owner of the real bodies: AEA-37."""

from __future__ import annotations

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.domain.state import (
    ConversationState,
    DangerUpdate,
    PlanJoinUpdate,
    PlannerUpdate,
)
from meridian.domain.turn import TurnContext


def planner(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlannerUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/plan.py planner: stub from AEA-21; AEA-37 fills it")


def danger_classifier(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> DangerUpdate:
    raise NotImplementedError(
        "src/meridian/agent/nodes/plan.py danger_classifier: stub from AEA-21; AEA-37 fills it"
    )


def plan_join(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlanJoinUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/plan.py plan_join: stub from AEA-21; AEA-37 fills it")
