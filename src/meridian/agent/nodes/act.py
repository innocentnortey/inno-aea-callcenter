"""Stub of the act node(s) with their final signatures (graph-nodes section 9). Owner of the real bodies: AEA-39."""

from __future__ import annotations

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.domain.state import (
    ConversationState,
    EscalationUpdate,
    HandoffNodeUpdate,
    SpecialistSend,
    SpecialistUpdate,
)
from meridian.domain.turn import TurnContext


def run_specialist(
    payload: SpecialistSend, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> SpecialistUpdate:
    raise NotImplementedError(
        "src/meridian/agent/nodes/act.py run_specialist: stub from AEA-21; AEA-39 fills it"
    )


def escalation(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> EscalationUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/act.py escalation: stub from AEA-21; AEA-39 fills it")


def handoff(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> HandoffNodeUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/act.py handoff: stub from AEA-21; AEA-39 fills it")
