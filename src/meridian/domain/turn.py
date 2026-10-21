"""Per-turn types: ids, budget, inputs, gate, planner, escalation, checks, records and outcome (AEA-02).

DO-4 sections 1-4, 6, 8-10 as amended by graph-core sections 2-3, 8-11, graph-nodes sections 1, 4, 5. `SafetyKind`
(defined in `common`) and `FormValues` (defined in `identity`) are re-exported here (plan 4.0). Not built here
(plan 8.2): ResponderInput.
"""

from __future__ import annotations

import datetime as dt
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_core import PydanticCustomError

from meridian.domain.actions import ActionKind, CompletedAction
from meridian.domain.blocks import Notice, ReplyBlock, SettledView
from meridian.domain.common import (
    FailureCounters,
    Halt,
    HaltReason,
    HandoffReason,
    LLMFacing,
    MeridianModel,
    PassageId,
    Priority,
    ProviderFailure,
    ProviderFailureKind,
    RequestId,
    ThreadId,
    TurnId,
)
from meridian.domain.common import SafetyKind as SafetyKind
from meridian.domain.handoff import HandoffResult, SourceRef
from meridian.domain.identity import FormValues as FormValues
from meridian.domain.identity import IdentityState, IdentityStep
from meridian.domain.records import Passage, ShownSlot
from meridian.domain.specialists import ChangeRequestDraft, KnowledgePoint, SpecialistResult

ExportStatus = Literal["off", "sent", "failed"]  # models.md section 4 (re-exported by ports/runtime)
TurnPath = Literal[
    "safety",
    "burning_questions",
    "burning_unclear",
    "danger",
    "person",
    "talk",
    "act",
    "handoff",
    "code",
    "paused",
    "degraded",
]  # DO-4 section 9 comment (complete list)
GateResult = Literal["clear", "safety", "burning_unclear", "danger", "person_requested", "ai_paused"]  # DO-6
TurnOutcome = Literal[
    "answered", "acted", "safety_reply", "handed_off", "to_staff", "degraded_handoff"
]  # DO-6
DegradeReason = Literal["model_error", "tool_error", "timeout", "brake", "spend_cap", "rate_limit"]  # DO-6
RunTag = Literal["live", "eval", "load"]
Topic = Literal["booking", "membership", "billing", "warranty", "other"]
SpecialistKind = Literal["knowledge", "account", "scheduling"]


class TurnIds(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    request_id: RequestId
    run_tag: RunTag
    run_id: str | None
    agent_version: str


@dataclass(frozen=True)
class TurnBudget:
    started: float  # time.monotonic()
    deadline: float  # started + 60 s (AEA-40 builds it from Limits)

    def remaining(self) -> float:
        return max(0.0, self.deadline - time.monotonic())

    def timeout_for(self, cap_s: float, min_call_s: float = 1.0) -> float | None:
        """The time a call may use: None when too little is left, else the smaller of the cap and what is left."""
        left = self.remaining()
        if left < min_call_s:
            return None
        return min(cap_s, left)


@dataclass(frozen=True)
class SpanHandle:
    """models.md section 4, file per graph-core section 1."""

    turn_id: TurnId
    trace_id: str | None
    native: object = field(default=None, compare=False, repr=False)


class CardChoice(MeridianModel):
    card_id: str
    option: str


class TextPayload(MeridianModel):
    kind: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=2000)


class ChoicePayload(CardChoice):
    kind: Literal["choice"] = "choice"


class CodePayload(MeridianModel):
    kind: Literal["code"] = "code"
    card_id: str
    code: SecretStr

    @field_validator("code")
    @classmethod
    def _six_digits(cls, value: SecretStr) -> SecretStr:
        if re.fullmatch(r"[0-9]{6}", value.get_secret_value()) is None:
            raise PydanticCustomError("invalid_format", "expected exactly six digits")
        return value


class FormPayload(MeridianModel):
    kind: Literal["form"] = "form"
    card_id: str
    values: FormValues


TurnPayload = Annotated[TextPayload | ChoicePayload | CodePayload | FormPayload, Field(discriminator="kind")]


class Intake(MeridianModel):
    kind: Literal["text", "choice", "code", "form"]
    text_store: str
    code_digits: SecretStr | None
    form: FormValues | None
    card_number_seen: bool
    choice: CardChoice | None
    card_id: str | None = None


class TurnInput(MeridianModel):
    """graph-core section 2; never code digits, never FormValues."""

    turn_id: TurnId
    message_id: int
    kind: Literal["text", "choice", "code", "form"]
    text_store: str
    card_id: str | None = None
    choice: CardChoice | None = None
    card_number_seen: bool = False
    received_at: dt.datetime


@dataclass(frozen=True)
class TurnContext:
    """graph-core section 2."""

    ids: TurnIds
    budget: TurnBudget
    now: dt.datetime
    demo_session: str
    span: SpanHandle
    intake: Intake | None = None


class RuleMatches(MeridianModel):
    """DO-4 section 3 + graph-core section 8 (seven fields; AEA-05 checks the names)."""

    safety: SafetyKind | None
    burning_unclear: bool
    danger_words: bool
    person: bool
    policy_trigger: HandoffReason | None
    rule_ids: tuple[str, ...]
    correction: bool


class GateKind(StrEnum):
    AI_PAUSED = "ai_paused"
    SAFETY = "safety"
    BURNING_ASK = "burning_ask"
    BURNING_ANSWER = "burning_answer"
    DANGER_RULE = "danger_rule"
    PERSON = "person"
    CODE_ENTRY = "code_entry"
    LOCATE = "locate"
    CARD_CHOICE = "card_choice"
    FREE_TEXT = "free_text"


class GateFlags(MeridianModel):
    """graph-core section 3."""

    ai_paused: bool
    burning_card_id: str | None
    code_card_open: bool
    open_task_ids: tuple[str, ...]


# graph-core section 3: the fixed part of the table; BURNING_ANSWER depends on the answer.
_GATE_RESULTS: Mapping[GateKind, GateResult] = MappingProxyType(
    {
        GateKind.SAFETY: "safety",
        GateKind.AI_PAUSED: "ai_paused",
        GateKind.BURNING_ASK: "burning_unclear",
        GateKind.DANGER_RULE: "danger",
        GateKind.PERSON: "person_requested",
        GateKind.CODE_ENTRY: "clear",
        GateKind.LOCATE: "clear",
        GateKind.CARD_CHOICE: "clear",
        GateKind.FREE_TEXT: "clear",
    }
)
_BURNING_ANSWER_RESULTS: Mapping[str, GateResult] = MappingProxyType(
    {"yes": "safety", "unsure": "burning_unclear", "no": "clear"}
)
_QUIET_GATES = frozenset({GateKind.FREE_TEXT, GateKind.CODE_ENTRY, GateKind.LOCATE, GateKind.CARD_CHOICE})


class GateDecision(MeridianModel):
    kind: GateKind
    rules: RuleMatches
    burning_answer: Literal["yes", "no", "unsure"] | None = None
    resume_task_id: str | None = None

    def gate_result(self) -> GateResult:
        """The DO-6 `gate_result` value for this decision (graph-core section 3, R-G-10)."""
        if self.kind == GateKind.BURNING_ANSWER:
            if self.burning_answer is None:
                raise ValueError("BURNING_ANSWER gate needs burning_answer")
            return _BURNING_ANSWER_RESULTS[self.burning_answer]
        return _GATE_RESULTS[self.kind]


class TaskIntent(StrEnum):
    ANSWER_QUESTION = "answer_question"
    READ_INVOICE = "read_invoice"
    READ_MEMBERSHIP = "read_membership"
    READ_APPOINTMENTS = "read_appointments"
    READ_WARRANTY = "read_warranty"
    BOOK_NEW = "book_new"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    CONFIRM = "confirm"


class StateFlags(MeridianModel):
    verified: bool
    open_task: Literal["none", "knowledge", "account", "scheduling"]
    open_task_intent: TaskIntent | None
    slots_shown: int
    has_open_case: bool
    pending_change: bool


class PlannerInput(MeridianModel):
    latest_message: str
    recent_chat: tuple[str, ...]
    flags: StateFlags


class PlannerChoices(LLMFacing):
    knowledge: Literal["no", "yes"]
    account: Literal["none", "invoice", "membership", "appointments", "warranty"]
    scheduling: Literal["none", "book_new", "reschedule", "cancel", "confirm"]
    handoff: Literal[
        "none",
        "refund",
        "billing_dispute",
        "membership_cancel",
        "unsupported_other",
        "complaint_or_manager",
        "late_technician",  # cases A-6
    ]
    topic: Topic


class PlannerOutcome(MeridianModel):
    choices: PlannerChoices | None
    probabilities: dict[str, dict[str, float]] | None
    model: str
    fallback_used: bool
    failure: ProviderFailure | None


class DangerAssessment(MeridianModel):
    label: Literal["normal", "burning_unclear", "danger"]
    raised: bool
    confidence: float | None = Field(default=None, ge=0, le=1)
    failure: ProviderFailure | None


class PlannedTask(MeridianModel):
    order: int = Field(ge=1, le=3)
    specialist: SpecialistKind
    intent: TaskIntent
    needs_identity: bool
    resumes_task_id: str | None = None


class Plan(MeridianModel):
    mode: Literal["talk", "act"]
    tasks: tuple[PlannedTask, ...] = Field(max_length=3)
    handoff_request: HandoffReason | None
    topic: Topic
    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]
    planner_failed: bool = False  # graph-nodes section 5


class EscalationInputs(MeridianModel):
    gate: GateDecision
    plan: Plan | None
    results: tuple[SpecialistResult, ...]
    counters: FailureCounters
    identity: IdentityState
    halt: Halt | None
    models_disabled: bool
    now: dt.datetime  # R-G-15


class EscalationDecision(MeridianModel):
    outcome: Literal["none", "offer", "escalate"]
    reason: HandoffReason | None
    priority: Priority | None
    rule_id: str
    degraded: bool = False


class Claim(MeridianModel):
    kind: Literal[
        "completion", "number", "date", "time", "id", "amount", "quote"
    ]  # + quote (graph-nodes section 2)
    span: tuple[int, int]
    value: str
    action_kind: ActionKind | None = None


class Removal(MeridianModel):
    claim: Claim
    reason: Literal["no_completed_action", "not_in_evidence", "quote_not_found"]


class CheckResult(MeridianModel):
    text: str
    removals: tuple[Removal, ...]
    passed: bool


class EvidenceSet(MeridianModel):
    amounts_cents: frozenset[int]
    dates: frozenset[dt.date]
    times: frozenset[str]
    ids: frozenset[str]
    numbers: frozenset[str]
    sources: dict[str, SourceRef]


CheckKind = Literal["completion", "fact", "brief_fact", "brief_quote", "gate", "classifier", "brake"]

_BRAKE_REASONS = frozenset(
    {
        HaltReason.BRAKE_TASKS,
        HaltReason.BRAKE_TOOL_ROUNDS,
        HaltReason.BRAKE_SONNET_CALLS,
        HaltReason.BRAKE_IDENTICAL_CALL,
        HaltReason.RECURSION_LIMIT,
    }
)


class CheckEvent(MeridianModel):
    """graph-nodes section 1. Holds codes and counts only, never text or a value (DO-6)."""

    check: CheckKind
    turn_id: TurnId
    result: Literal["pass", "trimmed", "fallback", "fired", "raised"]
    removed: int = 0
    claim_kinds: tuple[str, ...] = ()
    codes: tuple[str, ...] = ()

    @classmethod
    def from_check(
        cls,
        check: Literal["completion", "fact", "brief_fact", "brief_quote"],
        turn_id: TurnId,
        removals: Sequence[Removal],
        *,
        fallback: bool = False,
    ) -> CheckEvent:
        result: Literal["pass", "trimmed", "fallback"] = (
            "fallback" if fallback else ("trimmed" if removals else "pass")
        )
        return cls(
            check=check,
            turn_id=turn_id,
            result=result,
            removed=len(removals),
            claim_kinds=tuple(sorted({r.claim.kind for r in removals})),
            codes=(),
        )

    @classmethod
    def from_gate(cls, turn_id: TurnId, gate: GateDecision) -> CheckEvent:
        fired = gate.kind not in _QUIET_GATES or bool(gate.rules.rule_ids)
        return cls(
            check="gate",
            turn_id=turn_id,
            result="fired" if fired else "pass",
            codes=(gate.kind.value, *gate.rules.rule_ids),
        )

    @classmethod
    def from_danger(cls, turn_id: TurnId, danger: DangerAssessment) -> CheckEvent:
        if danger.failure is not None:
            return cls(
                check="classifier",
                turn_id=turn_id,
                result="fallback",
                codes=("fallback", danger.failure.kind.value),
            )
        return cls(
            check="classifier",
            turn_id=turn_id,
            result="raised" if danger.raised else "pass",
            codes=(danger.label,),
        )

    @classmethod
    def from_halt(cls, turn_id: TurnId, halt: Halt) -> CheckEvent:
        if halt.reason not in _BRAKE_REASONS:
            raise ValueError(f"no brake event for halt reason {halt.reason.value}")
        return cls(check="brake", turn_id=turn_id, result="fired", codes=(halt.reason.value, halt.node))


class SignalName(StrEnum):
    SAFETY_REPLY_SENT = "safety_reply_sent"
    CASE_WRITE_FAILED = "case_write_failed"
    CLASSIFIER_FALLBACK = "classifier_fallback"
    PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST_FAILED = "specialist_failed"
    BRAKE_FIRED = "brake_fired"
    RESPONDER_FALLBACK = "responder_fallback"
    BRIEF_FAILED = "brief_failed"


class SignalRecord(MeridianModel):
    record: Literal["signal"] = "signal"
    name: SignalName
    turn_id: TurnId
    thread_id: ThreadId
    request_id: RequestId
    run_tag: RunTag
    node: str
    cause: str | None = None
    role: Literal["planner", "classifier", "specialist", "responder", "brief"] | None = None
    specialist: SpecialistKind | None = None
    attempt: int | None = None
    recovered: bool | None = None


class TurnFacts(MeridianModel):
    """DO-4 section 8 WITHOUT account, missing, notices (blocked, plan 8.2)."""

    turn_id: TurnId
    gate_kind: GateKind
    plan_mode: Literal["talk", "act"] | None
    points: tuple[KnowledgePoint, ...]
    passages: tuple[Passage, ...]
    no_source_tasks: tuple[TaskIntent, ...]
    windows_shown: tuple[ShownSlot, ...]
    writes_this_turn: tuple[CompletedAction, ...]
    change_request: ChangeRequestDraft | None
    handoff: HandoffResult | None
    escalation: EscalationDecision | None
    identity_step: IdentityStep | None
    quick_checks: tuple[PassageId, ...] = ()


class ResponderDraft(LLMFacing):
    text: str = Field(min_length=1, max_length=1200)


class CheckedReply(MeridianModel):
    text: str
    removals: tuple[Removal, ...]
    fallback_used: bool
    events: tuple[CheckEvent, ...]


class ComposedReply(MeridianModel):
    blocks: tuple[ReplyBlock, ...]
    settled_view: SettledView
    writes: tuple[CompletedAction, ...]
    notice: Notice | None
    path: TurnPath
    outcome: TurnOutcome
    degrade_reason: DegradeReason | None


class PlannerTrace(MeridianModel):
    """graph-core section 2. Codes only."""

    model: str
    fallback_used: bool
    failure: ProviderFailureKind | None
    plan_mode: Literal["talk", "act"] | None
    plan_source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"] | None
    intents: tuple[TaskIntent, ...] = ()
    handoff_request: HandoffReason | None = None
    topic: Topic | None = None
    planner_failed: bool = False


class TurnTrace(MeridianModel):
    """Codes only."""

    gate_result: GateResult
    path: TurnPath
    outcome: TurnOutcome
    degrade_reason: DegradeReason | None = None
    planner: PlannerTrace | None = None
    danger_raised: bool = False
    specialists_run: tuple[SpecialistKind, ...] = ()


class TurnRecord(MeridianModel):
    status: Literal["completed", "failed"]
    trace: TurnTrace
    replied_at: dt.datetime
    server_ms: int
    model_calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    tool_calls: int
    trace_id: str | None
    trace_export: ExportStatus
    response: str


class GraphOutcome(MeridianModel):
    reply: ComposedReply
    turn_trace: TurnTrace
    check_events: tuple[CheckEvent, ...] = ()
    halt: Halt | None = None
    closed_every_open_task: bool = False


RunGraph = Callable[[TurnInput, TurnContext], GraphOutcome]
