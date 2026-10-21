"""Stub of the load_context node(s) with their final signatures (graph-nodes section 9). Owner of the real bodies: AEA-34."""

from __future__ import annotations

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.domain.state import (
    ConversationState,
    LoadContextUpdate,
)
from meridian.domain.turn import TurnContext


def load_context(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> LoadContextUpdate:
    raise NotImplementedError(
        "src/meridian/agent/nodes/load_context.py load_context: stub from AEA-21; AEA-34 fills it"
    )
