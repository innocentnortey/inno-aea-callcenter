"""Planner, raise-only danger classifier and plan join (A7d, AEA-37; graph-nodes section 9.4)."""

from __future__ import annotations

import re
import time
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal, TypeAlias

from langgraph.runtime import Runtime
from pydantic import ValidationError

from meridian.agent.context import GraphDeps
from meridian.agent.prompts.routing import DANGER_FIELD, classifier_request, planner_request
from meridian.agent.signals import emit_signal
from meridian.domain.common import (
    Halt,
    HaltReason,
    HandoffReason,
    ProviderFailure,
    ProviderFailureKind,
    ProviderName,
)
from meridian.domain.state import (
    ConversationState,
    DangerUpdate,
    OpenTask,
    PlanJoinUpdate,
    PlannerUpdate,
)
from meridian.domain.turn import (
    CheckEvent,
    DangerAssessment,
    GateDecision,
    Plan,
    PlannedTask,
    PlannerChoices,
    PlannerInput,
    PlannerOutcome,
    RuleMatches,
    SignalName,
    SignalRecord,
    StateFlags,
    TaskIntent,
    Topic,
    TurnContext,
)
from meridian.policy.limits import Brakes, ContextLimits
from meridian.ports.models import ChoiceAnswer, ChoiceRequest, ChoiceRole, Role
from meridian.privacy.redact import RedactionProfile, redact

if TYPE_CHECKING:
    from meridian.agent.gateway import ModelOutcome

__all__ = [
    "TaskBrakeExceeded",
    "build_planner_input",
    "danger_classifier",
    "join_plan",
    "plan_join",
    "planner",
    "raise_only",
    "rules_verdict",
]

DangerLabel: TypeAlias = Literal["normal", "burning_unclear", "danger"]
_Specialist: TypeAlias = Literal["knowledge", "account", "scheduling"]
_Draft: TypeAlias = tuple[_Specialist, TaskIntent, bool, str | None]

_DANGER_RANK: Final[Mapping[str, int]] = MappingProxyType({"normal": 0, "burning_unclear": 1, "danger": 2})
_LABELS: Final[Mapping[str, DangerLabel]] = MappingProxyType(
    {"normal": "normal", "burning_unclear": "burning_unclear", "danger": "danger"}
)
_UNKNOWN_MODEL: Final = "unknown"
_JEV: Final[ProviderName] = "openrouter_jev"
_ANTHROPIC: Final[ProviderName] = "anthropic"
_ACCOUNT_INTENT: Final[Mapping[str, TaskIntent]] = MappingProxyType(
    {
        "invoice": TaskIntent.READ_INVOICE,
        "membership": TaskIntent.READ_MEMBERSHIP,
        "appointments": TaskIntent.READ_APPOINTMENTS,
        "warranty": TaskIntent.READ_WARRANTY,
    }
)
_SCHEDULING_INTENT: Final[Mapping[str, TaskIntent]] = MappingProxyType(
    {
        "book_new": TaskIntent.BOOK_NEW,
        "reschedule": TaskIntent.RESCHEDULE,
        "cancel": TaskIntent.CANCEL,
        "confirm": TaskIntent.CONFIRM,
    }
)
_HANDOFF_REASON: Final[Mapping[str, HandoffReason | None]] = MappingProxyType(
    {
        "none": None,
        "refund": HandoffReason.REFUND,
        "billing_dispute": HandoffReason.BILLING_DISPUTE,
        "membership_cancel": HandoffReason.MEMBERSHIP_CANCEL,
        "unsupported_other": HandoffReason.UNSUPPORTED_ACTION,
        "complaint_or_manager": HandoffReason.COMPLAINT_OR_MANAGER,
        "late_technician": HandoffReason.LATE_TECHNICIAN,
    }
)
_TOPIC_BY_INTENT: Final[Mapping[TaskIntent, Topic]] = MappingProxyType(
    {
        TaskIntent.ANSWER_QUESTION: "other",
        TaskIntent.READ_INVOICE: "billing",
        TaskIntent.READ_MEMBERSHIP: "membership",
        TaskIntent.READ_APPOINTMENTS: "booking",
        TaskIntent.READ_WARRANTY: "warranty",
        TaskIntent.BOOK_NEW: "booking",
        TaskIntent.RESCHEDULE: "booking",
        TaskIntent.CANCEL: "booking",
        TaskIntent.CONFIRM: "booking",
    }
)
_DEFAULT_TASKS_PER_TURN: Final = Brakes().tasks_per_turn

# SP-1 follow-up patterns (gates.is_affirmative / mentions_slot_pick); no home in gates/ yet (plan R-8).
_AFFIRMATIVE: Final = re.compile(
    r"^\s*(yes|yeah|yep|yup|sure|ok|okay|please do|go ahead|sounds good|that works|perfect)\b", re.IGNORECASE
)
_WEEKDAY: Final = re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE)
_RANGE: Final = re.compile(r"\b\d{1,2}\s*(?:to|-|–)\s*\d{1,2}\b")
_WORKS: Final = re.compile(r"\bworks\b", re.IGNORECASE)


def _continues_open_task(text: str) -> bool:
    """A bare affirmative, or a slot pick (weekday, a "4 to 7" range or "works")."""
    return bool(
        _AFFIRMATIVE.search(text) or _WEEKDAY.search(text) or _RANGE.search(text) or _WORKS.search(text)
    )


class TaskBrakeExceeded(Exception):
    """A plan would hold more tasks than the brake allows. Carries counts only."""

    def __init__(self, count: int, limit: int) -> None:
        super().__init__(f"plan has {count} tasks; the brake allows {limit}")
        self.count = count
        self.limit = limit


# --------------------------------------------------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------------------------------------------------


def _choose(
    deps: GraphDeps, role: ChoiceRole, req: ChoiceRequest, ctx: TurnContext
) -> ModelOutcome[ChoiceAnswer]:
    """The only place a model is asked."""
    return deps.gateway.choose(role, req, ctx)


def _model_of(outcome: ModelOutcome[ChoiceAnswer]) -> str:
    return outcome.calls[-1].model if outcome.calls else _UNKNOWN_MODEL


def _invalid_output(outcome: ModelOutcome[ChoiceAnswer], default: ProviderName) -> ProviderFailure:
    last = outcome.calls[-1] if outcome.calls else None
    return ProviderFailure(
        kind=ProviderFailureKind.INVALID_OUTPUT,
        provider=last.provider if last else default,
        http_status=None,
        retry_after_s=None,
        retryable=False,
        provider_request_id=last.provider_request_id if last else None,
    )


def _parse_planner(
    outcome: ModelOutcome[ChoiceAnswer], default: ProviderName
) -> tuple[PlannerChoices | None, ProviderFailure | None]:
    """Exactly one of the two results is None."""
    if outcome.failure is not None:
        return None, outcome.failure
    if outcome.value is None:
        return None, _invalid_output(outcome, default)
    try:
        return PlannerChoices.model_validate(outcome.value.choices), None
    except ValidationError:
        return None, _invalid_output(outcome, default)


def _signal(
    ctx: TurnContext,
    name: SignalName,
    *,
    node: str,
    role: Literal["planner", "classifier"] | None,
    cause: str,
    recovered: bool | None,
) -> None:
    """Codes only: `cause` is always an enum value."""
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
            recovered=recovered,
        ),
    )


def _elapsed_ms(ctx: TurnContext) -> int:
    return max(0, int((time.monotonic() - ctx.budget.started) * 1000))


def _cap(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _last_open_task(state: ConversationState) -> OpenTask | None:
    for task in reversed(state.open_tasks):
        if task.status != "done":
            return task
    return None


# --------------------------------------------------------------------------------------------------------------
# Planner input
# --------------------------------------------------------------------------------------------------------------


def build_planner_input(state: ConversationState, limits: ContextLimits) -> PlannerInput:
    """DO-4 section 3: only JEV-redacted text and flags (never values) cross to the model."""
    # The newest message is sent separately (graph-core section 7), so it is never also a chat line.
    prior = [line for line in state.chat_window if line.turn_id != state.turn_input.turn_id]
    window = prior[-limits.planner_lines :] if limits.planner_lines > 0 else []
    # Redact before cutting, so a cut never leaves an unmasked fragment of a phone or card.
    recent_chat = tuple(
        _cap(redact(f"{line.speaker}: {line.text}", RedactionProfile.JEV).text, limits.planner_line_chars)
        for line in window
    )
    latest = redact(state.turn_input.text_store, RedactionProfile.JEV).text
    task = _last_open_task(state)
    visit = state.settled.current_visit() if state.settled is not None else None
    flags = StateFlags(
        verified=state.identity.status == "verified",
        open_task=task.specialist if task else "none",
        open_task_intent=task.intent if task else None,
        slots_shown=len(state.shown_slots),
        has_open_case=state.settled is not None and state.settled.open_case is not None,
        pending_change=visit is not None and visit.change_request is not None,
    )
    return PlannerInput(latest_message=latest, recent_chat=recent_chat, flags=flags)


# --------------------------------------------------------------------------------------------------------------
# Planner (Jev, with one Sonnet fallback on a failure, never on a halt)
# --------------------------------------------------------------------------------------------------------------


def planner(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlannerUpdate:
    ctx = runtime.context
    req = planner_request(build_planner_input(state, deps.limits.context))
    jev = _choose(deps, Role.PLANNER, req, ctx)
    if jev.halt is not None:
        return {"halt": jev.halt}
    choices, jev_failure = _parse_planner(jev, _JEV)
    if choices is not None:
        return {
            "planner": PlannerOutcome(
                choices=choices,
                probabilities=jev.value.probabilities if jev.value is not None else None,
                model=_model_of(jev),
                fallback_used=False,
                failure=None,
            )
        }
    fb = _choose(deps, Role.PLANNER_FALLBACK, req, ctx)
    if fb.halt is not None:
        return {
            "planner": PlannerOutcome(
                choices=None,
                probabilities=None,
                model=_model_of(jev),
                fallback_used=False,
                failure=jev_failure,
            ),
            "halt": fb.halt,
        }
    fb_choices, fb_failure = _parse_planner(fb, _ANTHROPIC)
    if jev_failure is not None:
        _signal(
            ctx,
            SignalName.PLANNER_FALLBACK,
            node="planner",
            role="planner",
            cause=jev_failure.kind.value,
            recovered=fb_choices is not None,
        )
    return {
        "planner": PlannerOutcome(
            choices=fb_choices,
            probabilities=None,
            model=_model_of(fb),
            fallback_used=True,
            failure=fb_failure,
        )
    }


# --------------------------------------------------------------------------------------------------------------
# Danger classifier (raise-only, R-47)
# --------------------------------------------------------------------------------------------------------------


def rules_verdict(rules: RuleMatches) -> DangerLabel:
    if rules.safety is not None or rules.danger_words:
        return "danger"
    if rules.burning_unclear:
        return "burning_unclear"
    return "normal"


def raise_only(label: DangerLabel, verdict: DangerLabel) -> bool:
    """Never lowers: an equal or lower label raises nothing."""
    return _DANGER_RANK[label] > _DANGER_RANK[verdict]


def danger_classifier(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> DangerUpdate:
    ctx = runtime.context
    gate = state.gate
    if gate is None:
        raise ValueError("danger_classifier: no gate decision in state")
    verdict = rules_verdict(gate.rules)
    latest = redact(state.turn_input.text_store, RedactionProfile.JEV).text
    out = _choose(deps, Role.CLASSIFIER, classifier_request(latest), ctx)
    if out.halt is not None:
        return {"halt": out.halt}
    failure: ProviderFailure | None = out.failure
    label: DangerLabel | None = None
    if failure is None:
        if out.value is None:
            failure = _invalid_output(out, _JEV)
        else:
            label = _LABELS.get(out.value.choices.get(DANGER_FIELD, ""))
            if label is None:
                failure = _invalid_output(out, _JEV)
    if failure is not None or label is None or out.value is None:
        failure = failure or _invalid_output(out, _JEV)
        danger = DangerAssessment(label="normal", raised=False, confidence=None, failure=failure)
        _signal(
            ctx,
            SignalName.CLASSIFIER_FALLBACK,
            node="danger_classifier",
            role="classifier",
            cause=failure.kind.value,
            recovered=None,
        )
    else:
        probs = out.value.probabilities
        p = probs.get(DANGER_FIELD, {}).get(label) if probs else None
        danger = DangerAssessment(
            label=label,
            raised=raise_only(label, verdict),
            confidence=None if p is None else min(1.0, max(0.0, float(p))),
            failure=None,
        )
    return {"danger": danger, "check_events": (CheckEvent.from_danger(ctx.ids.turn_id, danger),)}


# --------------------------------------------------------------------------------------------------------------
# Plan join
# --------------------------------------------------------------------------------------------------------------


def join_plan(
    planner: PlannerOutcome | None,
    danger: DangerAssessment | None,
    gate: GateDecision,
    state: ConversationState,
    *,
    tasks_per_turn: int = _DEFAULT_TASKS_PER_TURN,
) -> Plan:
    """SP-1's normalize order. `danger` is accepted for the DO-4 signature; the router reads `danger.raised`."""
    choices = planner.choices if planner is not None else None
    if choices is not None:
        knowledge, account, scheduling, handoff = (
            choices.knowledge,
            choices.account,
            choices.scheduling,
            choices.handoff,
        )
    else:
        knowledge, account, scheduling, handoff = "no", "none", "none", "none"
    policy = gate.rules.policy_trigger
    handoff_request = policy if policy is not None else _HANDOFF_REASON[handoff]
    if handoff_request is HandoffReason.MEMBERSHIP_CANCEL:
        account = "membership"
        knowledge = "yes"
    if scheduling != "none" and account == "appointments":
        account = "none"
    drafts: list[_Draft] = []
    if account != "none":
        drafts.append(("account", _ACCOUNT_INTENT[account], True, None))
    if scheduling != "none":
        drafts.append(("scheduling", _SCHEDULING_INTENT[scheduling], True, None))
    if knowledge == "yes":
        drafts.append(("knowledge", TaskIntent.ANSWER_QUESTION, False, None))
    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]
    if choices is not None:
        source = "fallback_planner" if planner is not None and planner.fallback_used else "planner"
    else:
        source = "rules_only"
    acts = bool(drafts) or handoff_request is not None
    if not acts:
        task = _last_open_task(state)
        if task is not None and _continues_open_task(state.turn_input.text_store):
            drafts = [(task.specialist, task.intent, task.specialist != "knowledge", task.task_id)]
            source = "open_task"
    if len(drafts) > tasks_per_turn:
        raise TaskBrakeExceeded(len(drafts), tasks_per_turn)
    planner_failed = planner is not None and choices is None and not drafts and handoff_request is None
    topic: Topic
    if choices is not None:
        topic = choices.topic
    elif source == "open_task":
        topic = _TOPIC_BY_INTENT[drafts[0][1]]
    else:
        topic = "other"
    mode: Literal["talk", "act"] = (
        "act" if drafts or handoff_request is not None or planner_failed else "talk"
    )
    return Plan(
        mode=mode,
        tasks=tuple(
            PlannedTask(order=i + 1, specialist=s, intent=it, needs_identity=ni, resumes_task_id=r)
            for i, (s, it, ni, r) in enumerate(drafts)
        ),
        handoff_request=handoff_request,
        topic=topic,
        source=source,
        planner_failed=planner_failed,
    )


def plan_join(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlanJoinUpdate:
    ctx = runtime.context
    if state.halt is not None:
        return {}
    gate = state.gate
    if gate is None:
        raise ValueError("plan_join: no gate decision in state")
    try:
        plan = join_plan(
            state.planner, state.danger, gate, state, tasks_per_turn=deps.limits.brakes.tasks_per_turn
        )
    except TaskBrakeExceeded:
        if state.danger is not None and state.danger.raised:
            return {}
        halt = Halt(reason=HaltReason.BRAKE_TASKS, node="plan_join", elapsed_ms=_elapsed_ms(ctx))
        _signal(
            ctx,
            SignalName.BRAKE_FIRED,
            node="plan_join",
            role=None,
            cause=HaltReason.BRAKE_TASKS.value,
            recovered=None,
        )
        return {"halt": halt, "check_events": (CheckEvent.from_halt(ctx.ids.turn_id, halt),)}
    return {"plan": plan}
