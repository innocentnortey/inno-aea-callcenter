"""The act nodes: specialist fan-out, escalation decision (plus the CAS-16 due move after a booking) and handoff (A7b; graph-nodes section 9.5)."""

from __future__ import annotations

import time
from collections.abc import Sequence
from datetime import date, datetime
from typing import Final

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.routers import BRAKE_HALTS
from meridian.agent.signals import emit_signal
from meridian.agent.specialists.runner import scope_for
from meridian.domain.actions import ActionKind
from meridian.domain.common import Halt
from meridian.domain.handoff import HandoffReason, HandoffRequest, HandoffResult
from meridian.domain.specialists import (
    AccountResult,
    ChangeRequestDraft,
    KnowledgeResult,
    SchedulingResult,
    SchedulingSlice,
    SchedulingSliceInputs,
)
from meridian.domain.state import (
    ConversationState,
    EscalationUpdate,
    HandoffNodeUpdate,
    OpenTask,
    SpecialistSend,
    SpecialistUpdate,
)
from meridian.domain.tools import AccountSlice, KnowledgeSlice, SpecialistTask
from meridian.domain.turn import (
    CheckEvent,
    EscalationInputs,
    GateKind,
    PlannedTask,
    SignalName,
    SignalRecord,
    SpecialistKind,
    TaskIntent,
    TurnContext,
)
from meridian.policy.escalation import decide_escalation
from meridian.policy.handoff import priority_for, window_start_of
from meridian.policy.limits import Limits
from meridian.privacy.redact import RedactionProfile, redact

__all__ = [
    "PERSON_RULE_ID",
    "QUICK_CHECK_SERVICE_TYPES",
    "build_specialist_task",
    "escalation",
    "handoff",
    "run_specialist",
]

PERSON_RULE_ID: Final = "R2.person"  # cases section 3.4 residual note (R-G-14)
QUICK_CHECK_SERVICE_TYPES: Final[frozenset[str]] = frozenset(
    {"hvac_repair", "plumbing"}
)  # graph-tools 6 rule 2
_NODE: Final = "run_specialist"


def _open_task(planned: PlannedTask, state: ConversationState) -> OpenTask | None:
    if planned.resumes_task_id is None:
        return None
    for task in state.open_tasks:
        if task.task_id == planned.resumes_task_id:
            return task
    return None


def _task_message_texts(planned: PlannedTask, state: ConversationState) -> tuple[str, ...]:
    """The customer's earlier messages for the open task this call resumes (PD-1); never this turn's own."""
    task = _open_task(planned, state)
    if task is None:
        return ()
    lines = [
        line
        for line in state.chat_window
        if line.speaker == "customer"
        and line.turn_id is not None
        and line.turn_id != state.turn_input.turn_id
    ]
    start = 0
    for index, line in enumerate(lines):
        if line.turn_id == task.opened_turn:
            start = index
            break
    return tuple(line.text for line in lines[start:])


def _has_pending_change(state: ConversationState) -> bool:
    # graph-nodes 9.5; ConversationState has no pending_change yet (AEA-02 8.2), so False until it lands
    return getattr(state, "pending_change", None) is not None


def _offers_quick_checks(planned: PlannedTask, state: ConversationState) -> bool:
    if not (
        planned.specialist == "scheduling"
        and planned.intent is TaskIntent.BOOK_NEW
        and planned.resumes_task_id is None
    ):
        return False
    task = _open_task(planned, state)
    service = None if task is None else task.details.service_type
    if service is not None and service not in QUICK_CHECK_SERVICE_TYPES:
        return False
    if state.gate is None or state.gate.kind is not GateKind.FREE_TEXT:
        return False
    return not (state.danger is not None and state.danger.raised)


def build_specialist_task(
    planned: PlannedTask,
    state: ConversationState,
    ctx: TurnContext,
    *,
    scheduling: SchedulingSliceInputs | None,
    limits: Limits,
) -> SpecialistTask:
    """Pure: the task one specialist sees, with only its own slice and SONNET-masked text (R-G-12, R-45)."""
    customer_text = redact(state.turn_input.text_store, RedactionProfile.SONNET).text
    task_messages = tuple(
        redact(text, RedactionProfile.SONNET).text for text in _task_message_texts(planned, state)
    )
    slice_: KnowledgeSlice | AccountSlice | SchedulingSlice
    match planned.specialist:
        case "knowledge":
            slice_ = KnowledgeSlice()
        case "account":
            slice_ = AccountSlice()
        case "scheduling":
            slice_ = SchedulingSlice(
                customer_zone=None if scheduling is None else scheduling.zone,
                member=False if scheduling is None else scheduling.member,
                appointments=() if scheduling is None else scheduling.appointments,
                shown_slots=tuple(state.shown_slots),
                pending_change=_has_pending_change(state),
                bookings_left=max(0, limits.booking.max_per_conversation - state.counters.bookings),
            )
        case _:
            raise ValueError("unknown specialist")
    return SpecialistTask(
        task=planned,
        customer_text=customer_text,
        task_messages=task_messages,
        slice=slice_,
        offer_quick_checks=_offers_quick_checks(planned, state),
    )


def _slice_inputs(
    planned: PlannedTask, state: ConversationState, deps: GraphDeps
) -> SchedulingSliceInputs | None:
    customer_id = state.identity.customer_id
    if planned.specialist != "scheduling" or state.identity.status != "verified" or customer_id is None:
        return None
    inputs: SchedulingSliceInputs = deps.scheduling.slice_inputs(customer_id)
    return inputs


def _elapsed_ms(ctx: TurnContext) -> int:
    return max(0, int((time.monotonic() - ctx.budget.started) * 1000))


def _signal(ctx: TurnContext, name: SignalName, *, cause: str, specialist: SpecialistKind) -> None:
    emit_signal(
        ctx.ids,
        SignalRecord(
            name=name,
            turn_id=ctx.ids.turn_id,
            thread_id=ctx.ids.thread_id,
            request_id=ctx.ids.request_id,
            run_tag=ctx.ids.run_tag,
            node=_NODE,
            cause=cause,
            role="specialist",
            specialist=specialist,
        ),
    )


def run_specialist(
    payload: SpecialistSend, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> SpecialistUpdate:
    ctx = runtime.context
    planned, state = payload["planned"], payload["state"]
    inputs = _slice_inputs(
        planned, state, deps
    )  # the only I/O before the run; the service closes its own read
    task = build_specialist_task(planned, state, ctx, scheduling=inputs, limits=deps.limits)
    result: KnowledgeResult | AccountResult | SchedulingResult = deps.specialists.run(
        task, scope_for(state, ctx), ctx
    )
    update: SpecialistUpdate = {"specialist_results": [result]}
    if result.brake is not None:
        halt = Halt(reason=result.brake, node=_NODE, elapsed_ms=_elapsed_ms(ctx))
        update["halt"] = halt
        if result.brake in BRAKE_HALTS:
            update["check_events"] = (CheckEvent.from_halt(ctx.ids.turn_id, halt),)
            _signal(ctx, SignalName.BRAKE_FIRED, cause=result.brake.value, specialist=planned.specialist)
    elif result.status == "failed":
        cause = "tool_error" if result.failure is None else result.failure.kind.value
        _signal(ctx, SignalName.SPECIALIST_FAILED, cause=cause, specialist=planned.specialist)
    return update


_ESCALATION_NODE: Final = "escalation"


def _booked_window_start(
    results: Sequence[KnowledgeResult | AccountResult | SchedulingResult],
) -> datetime | None:
    """The start of the window this turn booked, from the BOOKED action's stored `after` (date, window)."""
    for result in results:
        if not isinstance(result, SchedulingResult) or result.status != "written" or result.write is None:
            continue
        action = result.write.action
        after = action.after or {}
        if action.kind is ActionKind.BOOKED and "date" in after and "window" in after:
            return window_start_of(date.fromisoformat(after["date"]), after["window"])
    return None


def _align_burning_due(state: ConversationState, ctx: TurnContext, deps: GraphDeps) -> None:
    """CAS-16 option A (FU-identity-plan, finding F-2): a burning_ruled_out case opened on an earlier turn is due at the
    start of the visit booked for it. The booking is already written, so a failed move is signalled, never raised."""
    case = state.settled.open_case if state.settled is not None else None
    if case is None or case.reason is not HandoffReason.BURNING_RULED_OUT:
        return
    try:
        start = _booked_window_start(state.specialist_results)
        if start is not None:
            deps.cases.align_burning_due(ctx.ids.thread_id, start, ctx.ids.turn_id, ctx.now)
    except Exception:
        emit_signal(
            ctx.ids,
            SignalRecord(
                name=SignalName.CASE_WRITE_FAILED,
                turn_id=ctx.ids.turn_id,
                thread_id=ctx.ids.thread_id,
                request_id=ctx.ids.request_id,
                run_tag=ctx.ids.run_tag,
                node=_ESCALATION_NODE,
                cause="write_error",
                attempt=1,
                recovered=False,
            ),
        )


def escalation(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> EscalationUpdate:
    gate = state.gate
    if gate is None:
        raise ValueError("escalation node: no gate decision")
    inputs = EscalationInputs(
        gate=gate,
        plan=state.plan,
        results=tuple(state.specialist_results),
        counters=state.counters,
        identity=state.identity,
        halt=state.halt,
        models_disabled=deps.ledger.models_disabled(),
        now=runtime.context.now,
    )
    decision = decide_escalation(inputs)
    _align_burning_due(state, runtime.context, deps)
    return {"escalation": decision}


def _change_request(
    results: Sequence[KnowledgeResult | AccountResult | SchedulingResult],
) -> ChangeRequestDraft | None:
    for result in results:
        if (
            isinstance(result, SchedulingResult)
            and result.status == "staff_change_request"
            and result.change_request is not None
        ):
            return result.change_request
    return None


def _handoff_request(state: ConversationState, ctx: TurnContext) -> HandoffRequest | None:
    decision = state.escalation
    if decision is not None and decision.outcome == "escalate":
        if decision.reason is None or decision.priority is None:
            raise ValueError("escalate decision without reason or priority")
        return HandoffRequest(
            thread_id=ctx.ids.thread_id,
            turn_id=ctx.ids.turn_id,
            reason=decision.reason,
            priority=decision.priority,
            rule_id=decision.rule_id,
            trigger="escalation",
            identity=state.identity,
            change_request=_change_request(state.specialist_results),
        )
    if state.gate is not None and state.gate.kind is GateKind.PERSON:
        reason = HandoffReason.CUSTOMER_REQUESTED_PERSON
        return HandoffRequest(
            thread_id=ctx.ids.thread_id,
            turn_id=ctx.ids.turn_id,
            reason=reason,
            priority=priority_for(reason),
            rule_id=PERSON_RULE_ID,
            trigger="gate",
            identity=state.identity,
        )
    return None


def handoff(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> HandoffNodeUpdate:
    ctx = runtime.context
    request = _handoff_request(state, ctx)
    if request is None:
        return {}
    result: HandoffResult = deps.handoff.open(request, ctx)
    return {"handoff": result}
