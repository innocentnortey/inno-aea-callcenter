"""Stub of the reply node(s) with their final signatures (graph-nodes section 9). Owner of the real bodies: AEA-38."""

from __future__ import annotations

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.domain.state import (
    BriefUpdate,
    ChecksUpdate,
    ConversationState,
    FactsUpdate,
    ResponderUpdate,
)
from meridian.domain.turn import TurnContext


def facts(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> FactsUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/reply.py facts: stub from AEA-21; AEA-38 fills it")


def responder(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ResponderUpdate:
    raise NotImplementedError(
        "src/meridian/agent/nodes/reply.py responder: stub from AEA-21; AEA-38 fills it"
    )


def brief(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> BriefUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/reply.py brief: stub from AEA-21; AEA-38 fills it")


def checks(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ChecksUpdate:
    raise NotImplementedError("src/meridian/agent/nodes/reply.py checks: stub from AEA-21; AEA-38 fills it")
