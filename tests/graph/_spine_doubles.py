"""Plain helpers for graph tests: node doubles, a deps double and a turn context (AEA-21 plan section 6).

AEA-37's journey test imports these names: RecordingSink, make_deps, make_ctx, make_input, install_doubles, THREAD,
DEMO_NOW. No model, no database, no server. All ids are synthetic UUID4 strings.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import time
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, cast
from zoneinfo import ZoneInfo

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from meridian.agent.context import GraphDeps
from meridian.agent.graph import build_graph, run_graph
from meridian.agent.nodes import act, front, load_context, plan, reply
from meridian.agent.nodes.compose import ReplyComposer
from meridian.domain.actions import Settled
from meridian.domain.common import RequestId, ThreadId, TurnId
from meridian.domain.specialists import KnowledgeResult
from meridian.domain.state import ChatLine
from meridian.domain.turn import (
    CheckedReply,
    CheckEvent,
    DangerAssessment,
    EscalationDecision,
    ExportStatus,
    GateDecision,
    GateKind,
    GraphOutcome,
    Intake,
    Plan,
    PlannerOutcome,
    ResponderDraft,
    RuleMatches,
    SpanHandle,
    TurnBudget,
    TurnContext,
    TurnFacts,
    TurnIds,
    TurnInput,
)
from meridian.policy.limits import Limits
from meridian.ports.runtime import RetrievalIndex, UnitOfWorkFactory

if TYPE_CHECKING:
    from meridian.agent.gateway import ModelGateway

THREAD = ThreadId("6f1c2d3e-4b5a-4c6d-8e7f-0a1b2c3d4e5f")
REQ = RequestId("3c4d5e6f-7a8b-4c9d-8e0f-2a3b4c5d6e7f")
DEMO_NOW = dt.datetime(2026, 10, 16, 14, 20, tzinfo=ZoneInfo("America/Chicago"))
EMPTY_SETTLED = Settled(actions=(), open_case=None, read_at=DEMO_NOW)


class RecordingSink:
    """A TraceSink that records one `(name, elapsed_ms, status)` per node span."""

    def __init__(self) -> None:
        self.nodes: list[tuple[str, int, str]] = []

    def turn(self, ids: TurnIds) -> contextlib.AbstractContextManager[SpanHandle]:
        return contextlib.nullcontext(SpanHandle(turn_id=ids.turn_id, trace_id=None))

    def model_call(self, parent: SpanHandle, record: object, masked_input: str, masked_output: str) -> None:
        return None

    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None:
        self.nodes.append((name, elapsed_ms, status))

    def export_status(self, turn: SpanHandle) -> ExportStatus:
        return "off"


class _Core:
    def __init__(self, owner: UowDouble) -> None:
        self._owner = owner

    def settled_for(self, thread_id: ThreadId, read_at: dt.datetime) -> Settled:
        self._owner.calls.append((thread_id, read_at))
        return self._owner.settled


class _Tx:
    def __init__(self, owner: UowDouble) -> None:
        self.core = _Core(owner)


class UowDouble:
    """A UnitOfWorkFactory whose only repository method is `core.settled_for`."""

    def __init__(self, settled: Settled = EMPTY_SETTLED) -> None:
        self.settled = settled
        self.calls: list[tuple[ThreadId, dt.datetime]] = []

    @contextlib.contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[_Tx]:
        yield _Tx(self)


class _LedgerDouble:
    def models_disabled(self) -> bool:
        return False


def make_deps(sink: RecordingSink, uow: UowDouble | None = None) -> GraphDeps:
    return GraphDeps(
        gateway=cast("ModelGateway", object()),
        retrieval=cast(RetrievalIndex, object()),
        uow=cast(UnitOfWorkFactory, uow or UowDouble()),
        identity=object(),
        scheduling=object(),
        handoff=object(),
        brief=object(),
        demo=object(),
        limits=Limits(),
        trace=sink,
        specialists=object(),
        cases=object(),
        ledger=_LedgerDouble(),
    )


def make_ctx(turn_id: TurnId, *, intake: Intake | None = None) -> TurnContext:
    started = time.monotonic()
    return TurnContext(
        ids=TurnIds(
            thread_id=THREAD,
            turn_id=turn_id,
            request_id=REQ,
            run_tag="live",
            run_id=None,
            agent_version="test",
        ),
        budget=TurnBudget(started=started, deadline=started + 60.0),
        now=DEMO_NOW,
        demo_session="demo-session-1",
        span=SpanHandle(turn_id=turn_id, trace_id=None),
        intake=intake,
    )


def make_input(turn_id: TurnId, text_store: str = "Yes, please.") -> TurnInput:
    return TurnInput(turn_id=turn_id, message_id=1, kind="text", text_store=text_store, received_at=DEMO_NOW)


def no_rules() -> RuleMatches:
    return RuleMatches(
        safety=None,
        burning_unclear=False,
        danger_words=False,
        person=False,
        policy_trigger=None,
        rule_ids=(),
        correction=False,
    )


def _facts(state: Any, turn_id: TurnId) -> TurnFacts:
    return TurnFacts(
        turn_id=turn_id,
        gate_kind=state.gate.kind if state.gate else GateKind.FREE_TEXT,
        plan_mode=state.plan.mode if state.plan else None,
        points=(),
        passages=(),
        no_source_tasks=(),
        windows_shown=(),
        writes_this_turn=(),
        change_request=None,
        handoff=state.handoff,
        escalation=state.escalation,
        identity_step=state.identity_step,
    )


def default_doubles() -> dict[str, Callable[..., Any]]:
    """The default update of every node double. Each takes `(state, runtime, *, deps)`."""

    def turn_of(runtime: Any) -> TurnId:
        return cast(TurnId, runtime.context.ids.turn_id)

    def d_load_context(state: Any, runtime: Any, *, deps: Any) -> Any:
        ctx = runtime.context
        line = ChatLine(speaker="customer", text="hello", turn_id=ctx.ids.turn_id, at=ctx.now)
        return {"settled": Settled(actions=(), open_case=None, read_at=ctx.now), "chat_window": [line]}

    def d_gates(state: Any, runtime: Any, *, deps: Any) -> Any:
        g = GateDecision(kind=GateKind.FREE_TEXT, rules=no_rules())
        return {"gate": g, "check_events": (CheckEvent.from_gate(turn_of(runtime), g),)}

    def d_planner(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {
            "planner": PlannerOutcome(
                choices=None, probabilities=None, model="jev-test", fallback_used=False, failure=None
            )
        }

    def d_danger(state: Any, runtime: Any, *, deps: Any) -> Any:
        a = DangerAssessment(label="normal", raised=False, failure=None)
        return {"danger": a, "check_events": (CheckEvent.from_danger(turn_of(runtime), a),)}

    def d_plan_join(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {"plan": Plan(mode="talk", tasks=(), handoff_request=None, topic="other", source="planner")}

    def d_specialist(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {
            "specialist_results": [
                KnowledgeResult(status="answered", passages=(), points=(), tools=(), calls=())
            ]
        }

    def d_escalation(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {"escalation": EscalationDecision(outcome="none", reason=None, priority=None, rule_id="none")}

    def d_facts(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {"facts": _facts(state, turn_of(runtime))}

    def d_responder(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {"draft": ResponderDraft(text="Hello from the double.")}

    def d_checks(state: Any, runtime: Any, *, deps: Any) -> Any:
        event = CheckEvent.from_check("completion", turn_of(runtime), ())
        text = state.draft.text if state.draft else ""
        return {
            "checked": CheckedReply(
                text=text, removals=(), fallback_used=state.draft is None, events=(event,)
            )
        }

    def empty(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {}

    return {
        "load_context": d_load_context,
        "gates": d_gates,
        "safety": empty,
        "identity": empty,
        "planner": d_planner,
        "danger_classifier": d_danger,
        "plan_join": d_plan_join,
        "run_specialist": d_specialist,
        "escalation": d_escalation,
        "handoff": empty,
        "facts": d_facts,
        "responder": d_responder,
        "brief": empty,
        "checks": d_checks,
    }


_MODULES = {
    "load_context": load_context,
    "gates": front,
    "safety": front,
    "identity": front,
    "planner": plan,
    "danger_classifier": plan,
    "plan_join": plan,
    "run_specialist": act,
    "escalation": act,
    "handoff": act,
    "facts": reply,
    "responder": reply,
    "brief": reply,
    "checks": reply,
}


def install_doubles(
    monkeypatch: pytest.MonkeyPatch, visits: list[str], **overrides: Callable[..., Any]
) -> None:
    """Replace the 14 stub node functions with doubles that append their name to `visits`.

    An override is any callable `(state, runtime, *, deps)`; the real node functions fit (AEA-37 passes them).
    """
    defaults = default_doubles()
    for name, module in _MODULES.items():
        body = overrides.get(name, defaults[name])

        def double(
            state: Any, runtime: Any, *, deps: Any, _name: str = name, _body: Callable[..., Any] = body
        ) -> Any:
            visits.append(_name)
            return _body(state, runtime, deps=deps)

        monkeypatch.setattr(module, name, double)


class Harness:
    """A real `build_graph` over the doubles with an in-memory saver, plus a one-call way to run a turn."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, **overrides: Callable[..., Any]) -> None:
        self.visits: list[str] = []
        self.sink = RecordingSink()
        self.uow = UowDouble()
        self.saver = InMemorySaver()
        self.composer = ReplyComposer()
        self.deps = make_deps(self.sink, self.uow)
        install_doubles(monkeypatch, self.visits, **overrides)
        self.graph = build_graph(self.deps, checkpointer=self.saver, composer=self.composer)

    @property
    def config(self) -> Any:
        return {"configurable": {"thread_id": str(THREAD)}}

    def run(
        self, turn_id: TurnId, *, intake: Intake | None = None, text: str = "Yes, please."
    ) -> GraphOutcome:
        ctx = make_ctx(turn_id, intake=intake)
        return run_graph(self.graph, make_input(turn_id, text), ctx, deps=self.deps, composer=self.composer)

    def values(self) -> dict[str, Any]:
        return dict(self.graph.get_state(self.config).values)
