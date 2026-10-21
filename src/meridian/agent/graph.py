"""The fixed shape of one customer turn: building the graph and running it (DO-3 section 5.4, graph-core 2, 4, 5, 11).

`build_graph` registers the 15 nodes, wraps each in `timed_node` and draws the edges. `run_graph` resets the turn-scoped
state keys, invokes the graph and hands AEA-40 one `GraphOutcome`; a recursion-limit stop becomes a halt outcome, never
an exception. The only key in the invoke config is `thread_id`, so `intake` (code digits, form values) can never reach a
checkpoint (graph-core section 2).
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable, Mapping
from typing import Any, Final, TypeAlias, cast

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langgraph.types import Overwrite

from meridian.agent.context import GraphDeps
from meridian.agent.nodes import act as act_nodes
from meridian.agent.nodes import compose as compose_nodes
from meridian.agent.nodes import front as front_nodes
from meridian.agent.nodes import load_context as load_context_nodes
from meridian.agent.nodes import plan as plan_nodes
from meridian.agent.nodes import reply as reply_nodes
from meridian.agent.nodes.compose import ReplyComposer, turn_trace
from meridian.agent.routers import (
    route_after_escalation,
    route_after_facts,
    route_after_gates,
    route_after_identity,
    route_after_plan_join,
    route_after_specialists,
)
from meridian.agent.signals import emit_signal
from meridian.domain.actions import Settled
from meridian.domain.common import Halt, HaltReason, TurnId
from meridian.domain.state import (
    BriefUpdate,
    ChecksUpdate,
    ComposeUpdate,
    ConversationState,
    DangerUpdate,
    EscalationUpdate,
    FactsUpdate,
    GatesUpdate,
    HandoffNodeUpdate,
    IdentityNodeUpdate,
    LoadContextUpdate,
    PlanJoinUpdate,
    PlannerUpdate,
    ResponderUpdate,
    SafetyUpdate,
    SpecialistSend,
    SpecialistUpdate,
)
from meridian.domain.turn import (
    CheckEvent,
    GraphOutcome,
    RunGraph,
    SignalName,
    SignalRecord,
    TurnContext,
    TurnInput,
    TurnTrace,
)

__all__ = [
    "DURABLE_KEYS",
    "NODE_NAMES",
    "RECURSION_LIMIT",
    "TURN_SCOPED_KEYS",
    "CompiledGraph",
    "NodeFn",
    "NodeInput",
    "NodeUpdate",
    "bind_run_graph",
    "build_graph",
    "run_graph",
    "timed_node",
]

NodeInput = ConversationState | SpecialistSend
NodeUpdate = (
    LoadContextUpdate
    | GatesUpdate
    | SafetyUpdate
    | IdentityNodeUpdate
    | PlannerUpdate
    | DangerUpdate
    | PlanJoinUpdate
    | SpecialistUpdate
    | EscalationUpdate
    | HandoffNodeUpdate
    | FactsUpdate
    | ResponderUpdate
    | BriefUpdate
    | ChecksUpdate
    | ComposeUpdate
)
NodeFn = Callable[[NodeInput, Runtime[TurnContext]], NodeUpdate]
CompiledGraph: TypeAlias = CompiledStateGraph[Any, Any, Any, Any]
RECURSION_LIMIT: Final = 25  # DO-3 section 5.4; set explicitly (agent-architecture rule 15)

NODE_NAMES: Final = (
    "load_context",
    "gates",
    "safety",
    "identity",
    "planner",
    "danger_classifier",
    "plan_join",
    "run_specialist",
    "escalation",
    "handoff",
    "facts",
    "responder",
    "brief",
    "checks",
    "compose",
)
# DO-3 section 5.1: every ConversationState key is turn-scoped (reset each invocation), durable (the checkpoint keeps
# it), or one of the identity keys written every turn. `last_lookups` and `pending_change` are durable once AEA-02b
# builds them; they may be absent from the model today.
TURN_SCOPED_KEYS: Final = (
    "chat_window",
    "gate",
    "planner",
    "danger",
    "plan",
    "identity_step",
    "specialist_results",
    "escalation",
    "handoff",
    "facts",
    "draft",
    "brief_extraction",
    "checked",
    "reply",
    "halt",
)
DURABLE_KEYS: Final = (
    "settled",
    "controller",
    "identity",
    "open_tasks",
    "shown_slots",
    "last_lookups",
    "pending_change",
    "counters",
    "burning_card_id",
)

GATES_PATHS: Final = (
    "compose",
    "safety",
    "handoff",
    "identity",
    "run_specialist",
    "planner",
    "danger_classifier",
    "escalation",
)
IDENTITY_PATHS: Final = ("escalation", "compose", "run_specialist", "facts")
PLAN_JOIN_PATHS: Final = ("escalation", "compose", "safety", "facts", "identity", "run_specialist")
SPECIALISTS_PATHS: Final = ("escalation", "compose")
ESCALATION_PATHS: Final = ("handoff", "facts", "compose")
FACTS_PATHS: Final = ("compose", "responder", "brief")


def timed_node(name: str, fn: NodeFn, deps: GraphDeps) -> NodeFn:
    """Exactly one trace span per node run, also when the node raises; never state or text (AC-8)."""

    def _run(state: NodeInput, runtime: Runtime[TurnContext]) -> NodeUpdate:
        t0 = time.monotonic()
        status = "error"
        try:
            update = fn(state, runtime)
            halted = isinstance(update, dict) and cast(Mapping[str, object], update).get("halt") is not None
            status = "halted" if halted else "ok"
            return update
        finally:
            deps.trace.node(runtime.context.span, name, int((time.monotonic() - t0) * 1000), status)

    return _run


def build_graph(
    deps: GraphDeps, *, checkpointer: BaseCheckpointSaver[Any] | None, composer: ReplyComposer
) -> CompiledGraph:
    builder: StateGraph[Any, Any, Any, Any] = StateGraph(ConversationState, context_schema=TurnContext)

    def add(name: str, fn: Callable[..., Any]) -> None:
        action: Any = timed_node(name, cast(NodeFn, functools.partial(fn, deps=deps)), deps)
        builder.add_node(name, action)

    add("load_context", load_context_nodes.load_context)
    add("gates", front_nodes.gates)
    add("safety", front_nodes.safety)
    add("identity", front_nodes.identity)
    add("planner", plan_nodes.planner)
    add("danger_classifier", plan_nodes.danger_classifier)
    add("plan_join", plan_nodes.plan_join)
    add("run_specialist", act_nodes.run_specialist)
    add("escalation", act_nodes.escalation)
    add("handoff", act_nodes.handoff)
    add("facts", reply_nodes.facts)
    add("responder", reply_nodes.responder)
    add("brief", reply_nodes.brief)
    add("checks", reply_nodes.checks)
    add("compose", functools.partial(compose_nodes.compose, composer=composer))

    builder.add_edge(START, "load_context")
    for source, target in (
        ("load_context", "gates"),
        ("safety", "compose"),
        ("planner", "plan_join"),
        ("danger_classifier", "plan_join"),
        ("handoff", "facts"),
        ("responder", "checks"),
        ("brief", "checks"),
        ("checks", "compose"),
        ("compose", END),
    ):
        builder.add_edge(source, target)
    builder.add_conditional_edges("gates", route_after_gates, list(GATES_PATHS))
    builder.add_conditional_edges("identity", route_after_identity, list(IDENTITY_PATHS))
    builder.add_conditional_edges("plan_join", route_after_plan_join, list(PLAN_JOIN_PATHS))
    builder.add_conditional_edges("run_specialist", route_after_specialists, list(SPECIALISTS_PATHS))
    builder.add_conditional_edges("escalation", route_after_escalation, list(ESCALATION_PATHS))
    builder.add_conditional_edges("facts", route_after_facts, list(FACTS_PATHS))
    # No `configurable` default is set, so `intake` can never reach checkpoint metadata (graph-core section 2 rule 2).
    return builder.compile(checkpointer=checkpointer).with_config(recursion_limit=RECURSION_LIMIT)


def _turn_events(state: ConversationState, turn_id: TurnId) -> tuple[CheckEvent, ...]:
    own = tuple(e for e in state.check_events if e.turn_id == turn_id)
    return own + (tuple(state.checked.events) if state.checked is not None else ())


def _closed_every_open_task(state: ConversationState) -> bool:
    plan = state.plan
    return (
        state.halt is None
        and plan is not None
        and plan.mode == "act"
        and len(plan.tasks) >= 1
        and all(t.status == "done" for t in state.open_tasks)
    )


def _saved_values(graph: CompiledGraph, config: Any) -> Mapping[str, Any]:
    """The last checkpoint's values; empty on a new thread or a graph built without a checkpointer."""
    try:
        return cast(Mapping[str, Any], graph.get_state(config).values)
    except ValueError:
        return {}


def _turn_update(turn_input: TurnInput, ctx: TurnContext, *, fresh: bool) -> dict[str, Any]:
    """Reset every turn-scoped key, leave durable keys and the event reducer alone (AC-4).

    P2: LangGraph 1.2.16 stores a raw `Overwrite` written to a reducer channel that has no value yet, so the first turn
    of a thread sends a plain value.
    """
    update: dict[str, Any] = {"thread_id": ctx.ids.thread_id, "turn_input": turn_input}
    update.update({key: None for key in TURN_SCOPED_KEYS})
    update["chat_window"] = []
    update["specialist_results"] = Overwrite([])
    update["halt"] = None if fresh else Overwrite(None)
    return update


def run_graph(
    graph: CompiledGraph, turn_input: TurnInput, ctx: TurnContext, *, deps: GraphDeps, composer: ReplyComposer
) -> GraphOutcome:
    if turn_input.turn_id != ctx.ids.turn_id:
        raise ValueError("turn input and context disagree on the turn")
    config: Any = {"configurable": {"thread_id": str(ctx.ids.thread_id)}}  # nothing else, ever
    fresh = not _saved_values(graph, config)
    try:
        result = graph.invoke(_turn_update(turn_input, ctx, fresh=fresh), config, context=ctx)
    except GraphRecursionError:
        return _recursion_outcome(graph, config, ctx, deps=deps, composer=composer)
    state = ConversationState.model_validate(result)
    if state.reply is None:
        raise RuntimeError("graph ended without a reply")
    return GraphOutcome(
        reply=state.reply,
        turn_trace=turn_trace(state, state.reply),
        check_events=_turn_events(state, ctx.ids.turn_id),
        halt=state.halt,
        closed_every_open_task=_closed_every_open_task(state),
    )


def _recursion_outcome(
    graph: CompiledGraph, config: Any, ctx: TurnContext, *, deps: GraphDeps, composer: ReplyComposer
) -> GraphOutcome:
    """The graph hit the step limit: answer from the last checkpoint and the stored record; raise nothing."""
    values = _saved_values(graph, config)
    last = ConversationState.model_validate(values) if values else None
    if last is not None and last.turn_input.turn_id != ctx.ids.turn_id:
        last = None
    elapsed_ms = max(0, int((time.monotonic() - ctx.budget.started) * 1000))
    halt = Halt(reason=HaltReason.RECURSION_LIMIT, node="run_graph", elapsed_ms=elapsed_ms)
    with deps.uow() as tx:  # read-only; no model call inside (DO-3 section 2.3 rule 1)
        settled: Settled = tx.core.settled_for(ctx.ids.thread_id, ctx.now)
    reply = composer.halt_reply(halt, settled, ctx)
    events = (_turn_events(last, ctx.ids.turn_id) if last else ()) + (
        CheckEvent.from_halt(ctx.ids.turn_id, halt),
    )
    emit_signal(
        ctx.ids,
        SignalRecord(
            name=SignalName.BRAKE_FIRED,
            turn_id=ctx.ids.turn_id,
            thread_id=ctx.ids.thread_id,
            request_id=ctx.ids.request_id,
            run_tag=ctx.ids.run_tag,
            node="run_graph",
            cause=HaltReason.RECURSION_LIMIT.value,
        ),
    )
    trace = (
        turn_trace(last, reply)
        if last
        else TurnTrace(
            gate_result="clear", path=reply.path, outcome=reply.outcome, degrade_reason=reply.degrade_reason
        )
    )
    return GraphOutcome(
        reply=reply, turn_trace=trace, check_events=events, halt=halt, closed_every_open_task=False
    )


def bind_run_graph(graph: CompiledGraph, *, deps: GraphDeps, composer: ReplyComposer) -> RunGraph:
    def bound(turn_input: TurnInput, ctx: TurnContext) -> GraphOutcome:
        return run_graph(graph, turn_input, ctx, deps=deps, composer=composer)

    return bound
