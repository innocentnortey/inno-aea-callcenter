"""The reply nodes (graph-nodes 9.6): facts, responder, brief, checks (AEA-38)."""

from __future__ import annotations

from typing import Literal

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.prompts.reply import brief_request, brief_shown, responder_input, responder_request
from meridian.agent.signals import emit_signal
from meridian.checks import build_evidence, check_completion, check_facts, check_quotes
from meridian.domain.actions import ActionKind, CompletedAction
from meridian.domain.common import HaltReason, ProviderFailureKind, TurnId
from meridian.domain.identity import CodeWrong, NotVerified
from meridian.domain.records import Passage, ShownSlot
from meridian.domain.specialists import (
    AccountResult,
    KnowledgeResult,
    SchedulingResult,
    SpecialistResult,
)
from meridian.domain.state import (
    BriefUpdate,
    ChecksUpdate,
    ConversationState,
    FactsUpdate,
    FailureCounters,
    OpenTask,
    ResponderUpdate,
    TaskDetails,
)
from meridian.domain.turn import (
    CheckedReply,
    CheckEvent,
    GateKind,
    PlannedTask,
    Removal,
    SignalName,
    SignalRecord,
    TaskIntent,
    TurnContext,
    TurnFacts,
)
from meridian.ports.models import Role

__all__ = ["brief", "checks", "facts", "responder"]


def _signal(
    ctx: TurnContext,
    name: SignalName,
    node: str,
    *,
    cause: str | None = None,
    role: Literal["responder", "brief"] | None = None,
    attempt: int | None = None,
) -> None:
    """One `signal` record: ids and codes only, never text (both ids come from `ctx.ids`)."""
    emit_signal(
        ctx.ids,
        SignalRecord(
            name=name,
            turn_id=ctx.ids.turn_id,
            thread_id=ctx.ids.thread_id,
            request_id=ctx.ids.request_id,
            run_tag=ctx.ids.run_tag,
            node=node,
            cause=cause,
            role=role,
            attempt=attempt,
        ),
    )


# ---------------------------------------------------------------------------
# facts
# ---------------------------------------------------------------------------


def _knowledge_intent(state: ConversationState) -> TaskIntent:
    if state.plan is not None:
        for task in state.plan.tasks:
            if task.specialist == "knowledge":
                return task.intent
    return TaskIntent.ANSWER_QUESTION


def _next_counters(
    state: ConversationState, knowledge: list[KnowledgeResult], writes: tuple[CompletedAction, ...]
) -> FailureCounters:
    c = state.counters
    results: list[SpecialistResult] = list(state.specialist_results)
    failed_answer = any(r.status in ("no_current_source", "failed") for r in knowledge)
    tool_failed = any(r.status == "failed" or any(t.error is not None for t in r.tools) for r in results)
    identity_failed = isinstance(state.identity_step, NotVerified | CodeWrong)
    corrected = state.gate is not None and state.gate.rules.correction
    return c.model_copy(
        update={
            "failed_answers": c.failed_answers + (1 if failed_answer else 0),
            "tool_failures": c.tool_failures + (1 if tool_failed else 0),
            "identity_failures": c.identity_failures + (1 if identity_failed else 0),
            "corrections": c.corrections + (1 if corrected else 0),
            "bookings": c.bookings + sum(1 for a in writes if a.kind is ActionKind.BOOKED),
        }
    )


def _task_status(
    planned: PlannedTask, result: SpecialistResult | None, identity_status: str
) -> Literal["open", "waiting_identity", "done"]:
    if result is None:
        if planned.needs_identity and identity_status != "verified":
            return "waiting_identity"
        return "open"
    if isinstance(result, KnowledgeResult):
        return "done"
    if isinstance(result, AccountResult):
        return "waiting_identity" if result.status == "not_verified" else "done"
    if result.status in ("windows_shown", "slot_taken"):
        return "open"
    if result.status == "not_verified":
        return "waiting_identity"
    return "done"


def _next_open_tasks(state: ConversationState, turn_id: TurnId) -> list[OpenTask]:
    tasks = list(state.open_tasks)
    touched: set[str] = set()
    if state.plan is not None and state.plan.mode == "act":
        for planned in state.plan.tasks:
            result = next((r for r in state.specialist_results if r.kind == planned.specialist), None)
            status = _task_status(planned, result, state.identity.status)
            carried = state.plan.handoff_request if status == "waiting_identity" else None  # F-1
            update: dict[str, object] = {}
            if isinstance(result, SchedulingResult) and result.change_request is not None:
                update = {
                    "appointment_id": result.change_request.appointment_id,
                    "wanted_text": result.change_request.wanted_text,
                }
            resumed = next((i for i, t in enumerate(tasks) if t.task_id == planned.resumes_task_id), None)
            if resumed is not None:
                old = tasks[resumed]
                task_id = old.task_id
                tasks[resumed] = old.model_copy(
                    update={
                        "status": status,
                        "details": old.details.model_copy(update=update),
                        "handoff_request": carried,
                    }
                )
            else:
                task_id = f"task-{str(turn_id)[:8]}-{planned.order}"
                new = OpenTask(
                    task_id=task_id,
                    specialist=planned.specialist,
                    intent=planned.intent,
                    opened_turn=turn_id,
                    details=TaskDetails(**update),  # type: ignore[arg-type]
                    status=status,
                    handoff_request=carried,
                )
                same = next((i for i, t in enumerate(tasks) if t.task_id == task_id), None)
                if same is not None:
                    tasks[same] = new
                else:
                    tasks.append(new)
            touched.add(task_id)
    return [t for t in tasks if t.status != "done" or t.task_id in touched]


def _next_shown_slots(
    state: ConversationState, scheduling: list[SchedulingResult], windows: tuple[ShownSlot, ...]
) -> list[ShownSlot]:
    if windows:
        return list(windows)
    if any(r.status in ("written", "staff_change_request") for r in scheduling):
        return []
    return list(state.shown_slots)


def facts(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> FactsUpdate:
    ctx = runtime.context
    turn_id = ctx.ids.turn_id
    thread_id = ctx.ids.thread_id
    # No early return on state.halt: facts runs on a halted state (graph-core section 5).
    with deps.uow() as tx:
        settled = tx.core.settled_for(thread_id, ctx.now)  # the DB is the authority (AC-1)
    writes = tuple(a for a in settled.actions if a.key.turn_id == turn_id)
    knowledge = [r for r in state.specialist_results if isinstance(r, KnowledgeResult)]
    scheduling = [r for r in state.specialist_results if isinstance(r, SchedulingResult)]
    points = tuple(p for r in knowledge if r.status == "answered" for p in r.points)
    seen: dict[str, Passage] = {}
    for p in [p for r in knowledge for p in r.passages] + [p for r in scheduling for p in r.quick_checks]:
        seen.setdefault(str(p.passage_id), p)
    quick_checks = tuple(dict.fromkeys(p.passage_id for r in scheduling for p in r.quick_checks))
    slots: dict[int, ShownSlot] = {}
    for r in scheduling:
        for w in r.windows:
            slots.setdefault(w.slot_id, w)
    windows = tuple(slots.values())
    change_request = next((r.change_request for r in scheduling if r.change_request is not None), None)
    no_source = tuple(_knowledge_intent(state) for r in knowledge if r.status == "no_current_source")
    facts_obj = TurnFacts(
        turn_id=turn_id,
        gate_kind=state.gate.kind if state.gate is not None else GateKind.FREE_TEXT,
        plan_mode=state.plan.mode if state.plan is not None else None,
        points=points,
        passages=tuple(seen.values()),
        no_source_tasks=no_source,
        windows_shown=windows,
        writes_this_turn=writes,
        change_request=change_request,
        handoff=state.handoff,
        escalation=state.escalation,
        identity_step=state.identity_step,
        quick_checks=quick_checks,
    )
    return {
        "facts": facts_obj,
        "settled": settled,
        "open_tasks": _next_open_tasks(state, turn_id),
        "shown_slots": _next_shown_slots(state, scheduling, windows),
        "counters": _next_counters(state, knowledge, writes),
    }


# ---------------------------------------------------------------------------
# responder
# ---------------------------------------------------------------------------


def responder(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ResponderUpdate:
    ctx = runtime.context
    turn_id = ctx.ids.turn_id
    if state.facts is None or state.settled is None:
        raise RuntimeError("responder ran before facts")
    outcome = deps.gateway.structured(Role.RESPONDER, responder_request(responder_input(state, ctx)), ctx)
    if outcome.halt is not None:
        update: ResponderUpdate = {"draft": None, "halt": outcome.halt}
        if outcome.halt.reason is HaltReason.BRAKE_SONNET_CALLS:
            update["check_events"] = (CheckEvent.from_halt(turn_id, outcome.halt),)
            _signal(
                ctx, SignalName.BRAKE_FIRED, "responder", cause=outcome.halt.reason.value, role="responder"
            )
        return update
    if outcome.value is None:
        cause = (
            outcome.failure.kind.value
            if outcome.failure is not None
            else ProviderFailureKind.INVALID_OUTPUT.value
        )
        _signal(
            ctx,
            SignalName.RESPONDER_FALLBACK,
            "responder",
            cause=cause,
            role="responder",
            attempt=len(outcome.calls) or None,
        )
        return {"draft": None}
    return {"draft": outcome.value}


# ---------------------------------------------------------------------------
# brief
# ---------------------------------------------------------------------------


def _store_brief(deps: GraphDeps, ctx: TurnContext, case_ref: object, brief_obj: object, node: str) -> None:
    """Upsert the brief; a failed write is signalled, never raised (GRN-8: off the critical path)."""
    try:
        deps.cases.attach_brief(case_ref, brief_obj)
    except Exception:
        _signal(ctx, SignalName.BRIEF_FAILED, node, cause="write_error", role="brief")


def brief(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> BriefUpdate:
    ctx = runtime.context
    thread_id = ctx.ids.thread_id
    turn_id = ctx.ids.turn_id
    case = deps.cases.open_case_for_thread(thread_id)
    if case is None:
        return {"brief_extraction": None}
    with deps.uow() as tx:
        lookups = tx.core.lookup_log.for_thread(thread_id)
        rows = tx.core.messages.recent(thread_id, turns=deps.limits.context.window_turns)
    _store_brief(deps, ctx, case.case_ref, deps.brief.assemble(case, state, lookups), "brief")
    shown = brief_shown(
        [(r.id, r.text) for r in rows if r.role == "customer"], deps.limits.context.window_line_chars
    )
    if not shown:
        return {"brief_extraction": None}
    outcome = deps.gateway.structured(Role.BRIEF, brief_request(case, shown), ctx)
    if outcome.halt is not None:
        reason = outcome.halt.reason
        _signal(ctx, SignalName.BRIEF_FAILED, "brief", cause=reason.value, role="brief")
        if reason is HaltReason.BRAKE_SONNET_CALLS:
            _signal(ctx, SignalName.BRAKE_FIRED, "brief", cause=reason.value, role="brief")
            return {
                "brief_extraction": None,
                "halt": outcome.halt,
                "check_events": (CheckEvent.from_halt(turn_id, outcome.halt),),
            }
        return {"brief_extraction": None}
    if outcome.value is None:
        cause = (
            outcome.failure.kind.value
            if outcome.failure is not None
            else ProviderFailureKind.INVALID_OUTPUT.value
        )
        _signal(
            ctx,
            SignalName.BRIEF_FAILED,
            "brief",
            cause=cause,
            role="brief",
            attempt=len(outcome.calls) or None,
        )
        return {"brief_extraction": None}
    return {"brief_extraction": outcome.value}


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def checks(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ChecksUpdate:
    ctx = runtime.context
    thread_id = ctx.ids.thread_id
    turn_id = ctx.ids.turn_id
    brief_turn = state.handoff is not None and state.handoff.created
    case = deps.cases.open_case_for_thread(thread_id) if brief_turn else None
    with deps.uow() as tx:
        lookups = tx.core.lookup_log.for_thread(thread_id)
        rows = (
            tx.core.messages.recent(thread_id, turns=deps.limits.context.window_turns)
            if case is not None
            else ()
        )
    events: list[CheckEvent] = []
    if state.draft is None:
        text = ""
        removals: tuple[Removal, ...] = ()
        fallback = True
        events += [
            CheckEvent.from_check("completion", turn_id, (), fallback=True),
            CheckEvent.from_check("fact", turn_id, (), fallback=True),
        ]
    else:
        if state.settled is None or state.facts is None:
            raise RuntimeError("checks ran before facts")
        c1 = check_completion(state.draft.text, state.settled)
        c2 = check_facts(c1.text, build_evidence(state.facts, state.settled, lookups))
        removals = c1.removals + c2.removals
        events += [
            CheckEvent.from_check("completion", turn_id, c1.removals),
            CheckEvent.from_check("fact", turn_id, c2.removals),
        ]
        fallback = not c2.text.strip()
        text = "" if fallback else c2.text
        if fallback:
            _signal(ctx, SignalName.RESPONDER_FALLBACK, "checks", cause="all_removed", role="responder")
    if case is not None:
        draft_brief = deps.brief.assemble(case, state, lookups)
        ext = state.brief_extraction
        if ext is None:
            final = deps.brief.attach_extraction(draft_brief, None, None)
        else:
            if state.settled is None or state.facts is None:
                raise RuntimeError("checks ran before facts")
            shown = brief_shown(
                [(r.id, r.text) for r in rows if r.role == "customer"], deps.limits.context.window_line_chars
            )
            q = check_quotes(ext, shown)
            facts_ck = check_facts(
                ext.open_decision, build_evidence(state.facts, state.settled, lookups, state.chat_window)
            )
            kept = ext.model_copy(update={"needs": list(q.needs), "claims": list(q.claims)})
            final = deps.brief.attach_extraction(draft_brief, kept, facts_ck)
            events += [
                CheckEvent.from_check("brief_quote", turn_id, q.removals),
                CheckEvent.from_check("brief_fact", turn_id, facts_ck.removals),
            ]
        _store_brief(deps, ctx, case.case_ref, final, "checks")
    return {
        "checked": CheckedReply(
            text=text, removals=tuple(removals), fallback_used=fallback, events=tuple(events)
        )
    }
