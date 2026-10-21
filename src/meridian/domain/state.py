"""ConversationState, its reducers and the node update shapes (AEA-02; DO-3 section 5.2, graph-core 3, 9, 11).

`FailureCounters` (defined in `common`), `IdentityState` (defined in `identity`) and `ShownSlot` (defined in
`records`) are re-exported here (plan 4.0). Not built here (plan 8.2): `last_lookups`, `pending_change`,
`OpenTask.missing`.
"""

from __future__ import annotations

import datetime as dt
import operator
from typing import Annotated, Literal, TypedDict

from pydantic import Field

from meridian.domain.actions import Settled
from meridian.domain.common import CaseRef, Halt, MeridianModel, ThreadId, TurnId
from meridian.domain.common import FailureCounters as FailureCounters
from meridian.domain.handoff import BriefExtraction, HandoffResult
from meridian.domain.identity import IdentityState as IdentityState
from meridian.domain.identity import IdentityStep
from meridian.domain.records import ServiceType
from meridian.domain.records import ShownSlot as ShownSlot
from meridian.domain.specialists import SpecialistResult
from meridian.domain.turn import (
    CheckedReply,
    CheckEvent,
    ComposedReply,
    DangerAssessment,
    EscalationDecision,
    GateDecision,
    Plan,
    PlannedTask,
    PlannerOutcome,
    ResponderDraft,
    SpecialistKind,
    TaskIntent,
    TurnFacts,
    TurnInput,
)


class Controller(MeridianModel):
    kind: Literal["ai", "human"]
    representative_name: str | None = None
    case_ref: CaseRef | None = None


class TaskDetails(MeridianModel):
    """DO-4 section 1: zip, city, service_type, wanted_text, appointment_id (all optional)."""

    zip: str | None = None
    city: str | None = None
    service_type: ServiceType | None = None
    wanted_text: str | None = None
    appointment_id: int | None = None


class OpenTask(MeridianModel):
    """DO-4 section 1 WITHOUT `missing` (MissingInfo blocked, plan 8.2)."""

    task_id: str
    specialist: SpecialistKind
    intent: TaskIntent
    opened_turn: TurnId
    details: TaskDetails
    status: Literal["open", "waiting_identity", "done"]


class ChatLine(MeridianModel):
    speaker: Literal["customer", "assistant", "representative", "event"]
    text: str
    turn_id: TurnId | None
    at: dt.datetime


def first_halt(left: Halt | None, right: Halt | None) -> Halt | None:
    """Reducer: the first writer wins (DO-3 section 5.2)."""
    return left if left is not None else right


def add_turn_events(left: tuple[CheckEvent, ...], right: tuple[CheckEvent, ...]) -> tuple[CheckEvent, ...]:
    """Reducer (graph-core section 11): a new turn's first event drops the previous turn's events."""
    if not right:
        return left
    turn = right[0].turn_id
    return tuple(e for e in left if e.turn_id == turn) + tuple(right)


def _identity_not_checked() -> IdentityState:
    return IdentityState(
        status="not_checked",
        customer_id=None,
        masked_hint=None,
        code_expires_at=None,
        tries_left=3,
        codes_sent=0,
        verified_at=None,
    )


class ConversationState(MeridianModel):
    """DO-3 section 5.2 as changed by graph-core section 3, 9, 11."""

    thread_id: ThreadId
    # DB-authority copies (load_context writes them every turn)
    settled: Settled | None = None  # decision D-9: None only before load_context's first run
    controller: Controller = Field(default_factory=lambda: Controller(kind="ai"))
    identity: IdentityState = Field(default_factory=_identity_not_checked)
    # durable conversation state (the checkpoint is the authority)
    open_tasks: list[OpenTask] = Field(default_factory=list)
    shown_slots: list[ShownSlot] = Field(default_factory=list)
    counters: FailureCounters = Field(default_factory=FailureCounters)
    burning_card_id: str | None = None  # graph-core section 3; writer: gates node only
    # turn-scoped
    turn_input: TurnInput
    chat_window: list[ChatLine] = Field(default_factory=list)
    gate: GateDecision | None = None
    planner: PlannerOutcome | None = None  # renamed from planner_choices (graph-core section 9)
    danger: DangerAssessment | None = None
    plan: Plan | None = None
    identity_step: IdentityStep | None = None
    specialist_results: Annotated[list[SpecialistResult], operator.add] = Field(default_factory=list)
    escalation: EscalationDecision | None = None
    handoff: HandoffResult | None = None
    facts: TurnFacts | None = None
    draft: ResponderDraft | None = None
    brief_extraction: BriefExtraction | None = None
    checked: CheckedReply | None = None
    reply: ComposedReply | None = None
    halt: Annotated[Halt | None, first_halt] = None
    check_events: Annotated[tuple[CheckEvent, ...], add_turn_events] = ()


class SpecialistSend(TypedDict):
    """graph-nodes section 9.1 (R-G-12)."""

    planned: PlannedTask
    state: ConversationState


class LoadContextUpdate(TypedDict, total=False):
    settled: Settled
    controller: Controller
    identity: IdentityState
    chat_window: list[ChatLine]
    counters: FailureCounters


class GatesUpdate(TypedDict, total=False):
    gate: GateDecision
    check_events: tuple[CheckEvent, ...]
    plan: Plan
    halt: Halt
    burning_card_id: str | None


class SafetyUpdate(TypedDict, total=False):
    handoff: HandoffResult
    halt: Halt


class IdentityNodeUpdate(TypedDict, total=False):
    identity: IdentityState
    identity_step: IdentityStep
    halt: Halt


class PlannerUpdate(TypedDict, total=False):
    planner: PlannerOutcome
    halt: Halt


class DangerUpdate(TypedDict, total=False):
    danger: DangerAssessment
    check_events: tuple[CheckEvent, ...]
    halt: Halt


class PlanJoinUpdate(TypedDict, total=False):
    plan: Plan
    check_events: tuple[CheckEvent, ...]
    halt: Halt


class SpecialistUpdate(TypedDict, total=False):
    specialist_results: list[SpecialistResult]
    check_events: tuple[CheckEvent, ...]
    halt: Halt


class EscalationUpdate(TypedDict, total=False):
    escalation: EscalationDecision


class HandoffNodeUpdate(TypedDict, total=False):
    handoff: HandoffResult
    halt: Halt


class FactsUpdate(TypedDict, total=False):
    facts: TurnFacts
    settled: Settled
    open_tasks: list[OpenTask]
    shown_slots: list[ShownSlot]
    counters: FailureCounters


class ResponderUpdate(TypedDict, total=False):
    draft: ResponderDraft | None
    check_events: tuple[CheckEvent, ...]
    halt: Halt


class BriefUpdate(TypedDict, total=False):
    brief_extraction: BriefExtraction | None
    check_events: tuple[CheckEvent, ...]
    halt: Halt


class ChecksUpdate(TypedDict, total=False):
    checked: CheckedReply


class ComposeUpdate(TypedDict):
    reply: ComposedReply
