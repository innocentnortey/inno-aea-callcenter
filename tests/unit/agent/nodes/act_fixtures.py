"""Builders and doubles for the AEA-39 act-node tests. Synthetic values only."""

from __future__ import annotations

import contextlib
import dataclasses
import functools
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Literal, cast

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.graph import CompiledGraph, NodeFn, build_graph, run_graph, timed_node
from meridian.agent.nodes.act import escalation as real_escalation
from meridian.agent.nodes.act import handoff as real_handoff
from meridian.agent.nodes.act import run_specialist as real_run_specialist
from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.routers import route_act_plan
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.common import (
    CaseRef,
    CustomerId,
    FailureCounters,
    Halt,
    HaltReason,
    Presence,
    ProviderFailure,
    ProviderFailureKind,
    ThreadId,
    TurnId,
)
from meridian.domain.handoff import (
    CaseSummary,
    HandoffReason,
    HandoffRequest,
    HandoffResult,
    Priority,
)
from meridian.domain.identity import IdentityState
from meridian.domain.records import FeeNote
from meridian.domain.specialists import (
    AccountResult,
    AppointmentView,
    ChangeRequestDraft,
    ConfirmationView,
    KnowledgePoint,
    KnowledgeResult,
    MembershipView,
    SchedulingResult,
    SchedulingSliceInputs,
    SpecialistResult,
    WriteResult,
)
from meridian.domain.state import ChatLine, ConversationState, OpenTask
from meridian.domain.tools import SpecialistTask, ToolCallScope
from meridian.domain.turn import (
    CheckEvent,
    DangerAssessment,
    EscalationDecision,
    GateDecision,
    GateKind,
    GraphOutcome,
    Plan,
    PlannedTask,
    SpanHandle,
    SpecialistKind,
    TaskIntent,
    Topic,
    TurnBudget,
    TurnContext,
    TurnIds,
    TurnInput,
)
from meridian.policy.handoff import case_due_at, promise_for
from meridian.ports.runtime import UnitOfWorkFactory
from tests.fakes import CHICAGO, WORKED_PAIRS_NOW
from tests.graph._spine_doubles import (
    REQ,
    THREAD,
    RecordingSink,
    install_doubles,
    make_deps,
    make_input,
    no_rules,
)

if TYPE_CHECKING:
    from meridian.agent.gateway import ModelGateway

T1 = TurnId("1f0e2d3c-4b5a-4c69-8a7b-6c5d4e3f2a10")
T2 = TurnId("2a3b4c5d-6e7f-4a8b-9c0d-1e2f3a4b5c6d")
T3 = TurnId("3b4c5d6e-7f80-4a9b-8c1d-2e3f4a5b6c7d")

WP4_TEXT = "I have a tech coming but something came up. Can I move it?"
WP7_TEXT = "I want a full refund on the repair. It didn't fix anything and I had to call another company."
WP4_APPOINTMENT = AppointmentView(
    appointment_id=1,
    date=date(2026, 10, 16),
    window="12:00-16:00",
    service_type="hvac_tune_up",
    technician=None,
    is_warranty_visit=False,
)
WP4_DRAFT = ChangeRequestDraft(
    appointment_id=1,
    change="move",
    wanted_text="Monday morning",
    windows_shown=(),
    hours_before=2.0,
    window_start=datetime(2026, 10, 16, 12, 0, tzinfo=CHICAGO),
)
WP4_INPUTS = SchedulingSliceInputs(zone="central", member=False, appointments=(WP4_APPOINTMENT,))


# ------------------------------------------------------------------------------------------------ builders


def act_ctx(
    turn_id: TurnId = T1, *, now: datetime = WORKED_PAIRS_NOW, thread: ThreadId = THREAD
) -> TurnContext:
    started = time.monotonic()
    return TurnContext(
        ids=TurnIds(
            thread_id=thread,
            turn_id=turn_id,
            request_id=REQ,
            run_tag="live",
            run_id=None,
            agent_version="test",
        ),
        budget=TurnBudget(started=started, deadline=started + 60.0),
        now=now,
        demo_session="demo-session-1",
        span=SpanHandle(turn_id=turn_id, trace_id=None),
    )


def rt(ctx: TurnContext) -> Runtime[TurnContext]:
    return Runtime(context=ctx)


def gate(
    kind: GateKind = GateKind.FREE_TEXT,
    *,
    policy: HandoffReason | None = None,
    burning_answer: Literal["yes", "no", "unsure"] | None = None,
) -> GateDecision:
    rules = no_rules().model_copy(update={"policy_trigger": policy, "person": kind is GateKind.PERSON})
    return GateDecision(kind=kind, rules=rules, burning_answer=burning_answer)


def verified(customer: str = "MHC-57204") -> IdentityState:
    return IdentityState(
        status="verified",
        customer_id=CustomerId(customer),
        masked_hint=None,
        code_expires_at=None,
        tries_left=3,
        codes_sent=1,
        verified_at=WORKED_PAIRS_NOW,
    )


def unverified(status: Literal["not_verified", "locked", "not_checked"]) -> IdentityState:
    return IdentityState(
        status=status,
        customer_id=None,
        masked_hint=None,
        code_expires_at=None,
        tries_left=0 if status == "locked" else 3,
        codes_sent=1,
        verified_at=None,
    )


def task(
    order: int,
    specialist: SpecialistKind,
    intent: TaskIntent,
    *,
    needs_identity: bool | None = None,
    resumes: str | None = None,
) -> PlannedTask:
    return PlannedTask(
        order=order,
        specialist=specialist,
        intent=intent,
        needs_identity=(specialist != "knowledge") if needs_identity is None else needs_identity,
        resumes_task_id=resumes,
    )


def act_plan(
    *tasks: PlannedTask, handoff_request: HandoffReason | None = None, topic: Topic = "booking"
) -> Plan:
    return Plan(mode="act", tasks=tasks, handoff_request=handoff_request, topic=topic, source="planner")


def talk_plan() -> Plan:
    return Plan(mode="talk", tasks=(), handoff_request=None, topic="other", source="planner")


def make_state(
    *,
    turn_id: TurnId = T1,
    text: str = "Hello",
    gate_: GateDecision | None = None,
    plan: Plan | None = None,
    identity: IdentityState | None = None,
    results: Sequence[SpecialistResult] = (),
    counters: FailureCounters | None = None,
    halt: Halt | None = None,
    danger: DangerAssessment | None = None,
    open_tasks: Sequence[OpenTask] = (),
    chat: Sequence[ChatLine] = (),
    escalation: EscalationDecision | None = None,
) -> ConversationState:
    return ConversationState(
        thread_id=THREAD,
        settled=Settled(actions=(), open_case=None, read_at=WORKED_PAIRS_NOW),
        identity=identity or verified(),
        turn_input=TurnInput(
            turn_id=turn_id, message_id=412, kind="text", text_store=text, received_at=WORKED_PAIRS_NOW
        ),
        gate=gate_ or gate(),
        plan=plan,
        specialist_results=list(results),
        counters=counters or FailureCounters(),
        halt=halt,
        danger=danger,
        open_tasks=list(open_tasks),
        chat_window=list(chat),
        escalation=escalation,
    )


def apply(state: ConversationState, update: Mapping[str, Any]) -> ConversationState:
    """The graph's reducers, for chaining nodes in unit tests."""
    from meridian.domain.state import add_turn_events, first_halt

    merged: dict[str, Any] = {}
    for key, value in update.items():
        if key == "specialist_results":
            merged[key] = [*state.specialist_results, *value]
        elif key == "check_events":
            merged[key] = add_turn_events(state.check_events, value)
        elif key == "halt":
            merged[key] = first_halt(state.halt, value)
        else:
            merged[key] = value
    return state.model_copy(update=merged)


def knowledge(
    status: Literal["answered", "no_current_source", "failed"] = "answered",
    *,
    brake: HaltReason | None = None,
    failure: ProviderFailure | None = None,
    points: tuple[KnowledgePoint, ...] = (),
) -> KnowledgeResult:
    return KnowledgeResult(
        status=status, passages=(), points=points, tools=(), calls=(), brake=brake, failure=failure
    )


def account(
    status: Literal["read", "not_verified", "failed"] = "read",
    *,
    renewal: date | None = None,
    brake: HaltReason | None = None,
    failure: ProviderFailure | None = None,
) -> AccountResult:
    return AccountResult(
        status=status,
        membership=None if renewal is None else MembershipView(tier="standard", renewal_date=renewal),
        tools=(),
        calls=(),
        brake=brake,
        failure=failure,
    )


def scheduling(
    status: Literal[
        "windows_shown",
        "written",
        "staff_change_request",
        "slot_taken",
        "out_of_area",
        "no_fit",
        "not_verified",
        "booking_cap",
        "failed",
    ] = "windows_shown",
    *,
    change_request: ChangeRequestDraft | None = None,
    write: WriteResult | None = None,
    brake: HaltReason | None = None,
    failure: ProviderFailure | None = None,
) -> SchedulingResult:
    return SchedulingResult(
        status=status,
        change_request=change_request,
        write=write,
        tools=(),
        calls=(),
        brake=brake,
        failure=failure,
    )


def failure(kind: ProviderFailureKind = ProviderFailureKind.TIMEOUT) -> ProviderFailure:
    return ProviderFailure(
        kind=kind,
        provider="anthropic",
        http_status=None,
        retry_after_s=None,
        retryable=True,
        provider_request_id=None,
    )


def booked_write(turn_id: TurnId) -> WriteResult:
    return WriteResult(
        action=CompletedAction(
            key=ActionKey(thread_id=THREAD, turn_id=turn_id, kind=ActionKind.BOOKED, record_id="101"),
            kind=ActionKind.BOOKED,
            records={"appointment": "101", "slot": "4401"},
            at=WORKED_PAIRS_NOW,
        ),
        confirmation=ConfirmationView(
            date=date(2026, 10, 19),
            window="08:00-12:00",
            technician="Technician One",
            fee_note=FeeNote(
                service_type="hvac_repair",
                tier="none",
                fee_row=None,
                amount_cents=8900,
                waived=False,
                line="Synthetic test line: diagnostic fee",
            ),
        ),
    )


# -------------------------------------------------------------------------------------------------- doubles


class UowCounter:
    """A UnitOfWorkFactory double that counts open units of work."""

    def __init__(self) -> None:
        self.open_count = 0
        self.entered = 0

    @contextlib.contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[object]:
        self.open_count += 1
        self.entered += 1
        try:
            yield object()
        finally:
            self.open_count -= 1


class SchedulingDouble:
    """`SchedulingService.slice_inputs` only; it has no write method."""

    def __init__(self, inputs: SchedulingSliceInputs = WP4_INPUTS, *, uow: UowCounter | None = None) -> None:
        self.inputs = inputs
        self.uow = uow
        self.calls: list[str] = []
        self.customer_ids: list[CustomerId] = []

    def slice_inputs(self, customer_id: CustomerId) -> SchedulingSliceInputs:
        self.calls.append("slice_inputs")
        self.customer_ids.append(customer_id)
        if self.uow is not None:
            with self.uow():
                pass
        return self.inputs


class RunnerDouble:
    """`SpecialistRunner.run`."""

    def __init__(
        self,
        results: Mapping[SpecialistKind, SpecialistResult],
        *,
        delays: Mapping[SpecialistKind, float] | None = None,
        uow: UowCounter | None = None,
    ) -> None:
        self.results = results
        self.delays = delays or {}
        self.uow = uow
        self.calls: list[tuple[SpecialistTask, ToolCallScope, TurnContext]] = []
        self.uow_open_at_call: list[int] = []

    def run(self, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext) -> SpecialistResult:
        self.calls.append((task, scope, ctx))
        if self.uow is not None:
            self.uow_open_at_call.append(self.uow.open_count)
        time.sleep(self.delays.get(task.task.specialist, 0.0))
        return self.results[task.task.specialist]


class LedgerDouble:
    """`ModelsStatus`."""

    def __init__(self, disabled: bool = False) -> None:
        self.disabled = disabled
        self.calls = 0

    def models_disabled(self) -> bool:
        self.calls += 1
        return self.disabled


class GatewayDouble:
    """Fails loudly if any gateway method is used."""

    def __init__(self) -> None:
        self.accessed: list[str] = []

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_") or name == "accessed":
            raise AttributeError(name)
        self.accessed.append(name)
        raise AssertionError(f"gateway.{name} used")


class HandoffDouble:
    """`HandoffService.open`, built on the real policy functions (AEA-14)."""

    def __init__(self, presence: Presence = "nobody_online", *, error: Exception | None = None) -> None:
        self.presence = presence
        self.error = error
        self.requests: list[HandoffRequest] = []
        self._by_key: dict[tuple[ThreadId, TurnId], HandoffResult] = {}
        self._open: dict[ThreadId, HandoffResult] = {}
        self._count = 0

    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult:
        self.requests.append(req)
        if self.error is not None:
            raise self.error
        key = (req.thread_id, req.turn_id)
        if key in self._by_key:
            return self._by_key[key]
        existing = self._open.get(req.thread_id)
        if existing is not None:
            result = existing.model_copy(update={"created": False})
            self._by_key[key] = result
            return result
        window_start = req.change_request.window_start if req.change_request else None
        promise = promise_for(req.reason, self.presence, ctx.now, window_start)
        self._count += 1
        ref = CaseRef(f"MHC-C-{self._count:04d}")
        case = CaseSummary(
            case_ref=ref,
            reason=req.reason,
            priority=req.priority,
            state="unassigned",
            created_at=ctx.now,
            promise=promise,
            followup=None,
            version=1,
            due_at=case_due_at(req.reason, promise, window_start),
        )
        action = CompletedAction(
            key=ActionKey(
                thread_id=req.thread_id, turn_id=req.turn_id, kind=ActionKind.CASE_OPENED, record_id=str(ref)
            ),
            kind=ActionKind.CASE_OPENED,
            records={"case": str(ref)},
            at=ctx.now,
        )
        alert: Literal["supervisor_now"] | None = (
            "supervisor_now"
            if req.priority in (Priority.P0, Priority.P1) or req.reason is HandoffReason.FEE_BEARING_CHANGE
            else None
        )
        result = HandoffResult(case=case, created=True, action=action, alert=alert)
        self._open[req.thread_id] = result
        self._by_key[key] = result
        return result


# ----------------------------------------------------------------------------------------- graph helpers


def deps_for(
    *,
    runner: RunnerDouble,
    scheduling_: SchedulingDouble | None = None,
    handoff_: Any = None,
    ledger: LedgerDouble | None = None,
    gateway: GatewayDouble | None = None,
    uow: UowCounter | None = None,
) -> GraphDeps:
    return dataclasses.replace(
        make_deps(RecordingSink()),
        gateway=cast("ModelGateway", gateway or GatewayDouble()),
        uow=cast(UnitOfWorkFactory, uow or UowCounter()),
        specialists=runner,
        scheduling=scheduling_ or SchedulingDouble(),
        handoff=handoff_ or HandoffDouble(),
        ledger=ledger or LedgerDouble(),
    )


def fanout_graph(deps: GraphDeps) -> CompiledGraph:
    """Send fan-out only, with the production node wrapper."""
    builder: StateGraph[Any, Any, Any, Any] = StateGraph(ConversationState, context_schema=TurnContext)
    node: Any = timed_node(
        "run_specialist", cast(NodeFn, functools.partial(real_run_specialist, deps=deps)), deps
    )
    builder.add_node("run_specialist", node)
    builder.add_conditional_edges(START, route_act_plan, ["run_specialist"])
    builder.add_edge("run_specialist", END)
    return builder.compile()


def state_input(state: ConversationState) -> dict[str, Any]:
    return {name: getattr(state, name) for name in ConversationState.model_fields}


@dataclass
class ActHarness:
    """The real `build_graph` with the real act nodes and AEA-21's doubles elsewhere."""

    graph: CompiledGraph
    deps: GraphDeps
    composer: ReplyComposer
    visits: list[str]
    thread: ThreadId = THREAD

    def run(self, turn_id: TurnId, text: str, *, now: datetime = WORKED_PAIRS_NOW) -> GraphOutcome:
        return run_graph(
            self.graph,
            make_input(turn_id, text),
            act_ctx(turn_id, now=now, thread=self.thread),
            deps=self.deps,
            composer=self.composer,
        )

    def values(self) -> dict[str, Any]:
        config: Any = {"configurable": {"thread_id": str(self.thread)}}
        return dict(self.graph.get_state(config).values)


def act_harness(
    monkeypatch: pytest.MonkeyPatch,
    deps: GraphDeps,
    *,
    thread: ThreadId = THREAD,
    **overrides: Callable[..., Any],
) -> ActHarness:
    visits: list[str] = []
    install_doubles(
        monkeypatch,
        visits,
        run_specialist=real_run_specialist,
        escalation=real_escalation,
        handoff=real_handoff,
        **overrides,
    )
    composer = ReplyComposer()
    graph = build_graph(deps, checkpointer=InMemorySaver(), composer=composer)
    return ActHarness(graph, deps, composer, visits, thread)


def verified_load_context(customer: str) -> Callable[..., Any]:
    def node(state: Any, runtime: Any, *, deps: Any) -> Any:
        ctx = runtime.context
        return {
            "settled": Settled(actions=(), open_case=None, read_at=ctx.now),
            "chat_window": [ChatLine(speaker="customer", text="hello", turn_id=ctx.ids.turn_id, at=ctx.now)],
            "identity": verified(customer),
        }

    return node


def plan_join_returning(plans: Mapping[TurnId, Plan]) -> Callable[..., Any]:
    def node(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {"plan": plans[runtime.context.ids.turn_id]}

    return node


def gates_returning(decision: GateDecision) -> Callable[..., Any]:
    def node(state: Any, runtime: Any, *, deps: Any) -> Any:
        return {
            "gate": decision,
            "check_events": (CheckEvent.from_gate(runtime.context.ids.turn_id, decision),),
        }

    return node
