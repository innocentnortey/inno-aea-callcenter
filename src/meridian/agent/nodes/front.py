"""Stub of the front node(s) with their final signatures (graph-nodes section 9). Owner of the real bodies: AEA-36."""

from __future__ import annotations

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.domain.state import (
    ConversationState,
    GatesUpdate,
    IdentityNodeUpdate,
    SafetyUpdate,
)
from meridian.domain.turn import TurnContext


def gates(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> GatesUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/front.py gates: stub from AEA-21; AEA-36 fills it")


def safety(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> SafetyUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/front.py safety: stub from AEA-21; AEA-36 fills it")


def identity(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> IdentityNodeUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/front.py identity: stub from AEA-21; AEA-36 fills it")
