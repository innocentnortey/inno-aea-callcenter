"""Reply blocks and the Settled view: wire shapes taken field for field from the signed OpenAPI (AEA-02).

Every class takes its field names, required set and value sets from the OpenAPI schema of the same name
(docs/ux/03-structure/ui-contracts.openapi.yaml, read only; plan 4.7 and Appendix A). Every property is required;
only `const` fields carry a default.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import Field

from meridian.domain.actions import VisitView
from meridian.domain.common import FollowUp, MeridianModel


class Speaker(MeridianModel):
    kind: Literal["assistant", "customer", "representative", "event"]
    display_name: str | None


class SourceChip(MeridianModel):
    passage_id: str
    file: str
    section: str
    version_date: dt.date | None
    excerpt: str
    audience: Literal["customer"] = "customer"
    version_label: str


class Option(MeridianModel):
    option: str
    label: str
    disabled: bool
    reason: str | None


class Money(MeridianModel):
    amount_cents: int
    display: str


class FollowUpChannelOption(MeridianModel):
    channel: Literal["email", "phone"]
    label: str
    on_record: bool


class FollowUpWindowOption(MeridianModel):
    window: Literal["morning", "afternoon", "any"]
    label: str


class FollowUpOptions(MeridianModel):
    legend: str
    channels: tuple[FollowUpChannelOption, ...]
    windows: tuple[FollowUpWindowOption, ...]
    general_only: bool


class SettledVisit(VisitView):
    """OpenAPI SettledVisit = VisitView plus window_label (graph-core section 14)."""

    window_label: str


class SettledRequest(MeridianModel):
    reference: str
    promise_text: str
    due_at: dt.datetime | None
    due_label: str | None
    extra_lines: tuple[str, ...]
    live_queued: bool
    followup: FollowUp | None


class Write(MeridianModel):
    kind: Literal[
        "booked", "moved", "cancelled", "change_request_sent", "case_opened", "followup_saved", "verified"
    ]
    summary: str
    turn_id: str
    at: dt.datetime


class SettledIdentity(MeridianModel):
    status: Literal["not_checked", "code_sent", "verified", "not_verified", "locked"]
    hint: str | None


class SettledReplying(MeridianModel):
    kind: Literal["ai", "human"]
    display_name: str | None


class SettledView(MeridianModel):
    """OpenAPI Settled (DO-3 name SettledView)."""

    built_from: Literal["conversation_state"] = "conversation_state"
    visit: SettledVisit | None
    request: SettledRequest | None
    identity: SettledIdentity
    replying: SettledReplying
    actions: tuple[Write, ...]


class Notice(MeridianModel):
    code: Literal["RATE_LIMITED", "BOOKING_CAP", "SPEND_CAP_REACHED", "TURN_TIMEOUT", "BUSY", "AI_PAUSED"]
    actions: tuple[Literal["try_again", "talk_to_person"], ...]
    retry_turn_id: str | None
    delivered_to_representative: bool


class BlockBase(MeridianModel):
    """block_id, speaker and at only: each block declares its own `type` literal."""

    block_id: str
    speaker: Speaker
    at: dt.datetime


class TextBlock(BlockBase):
    type: Literal["text"] = "text"
    text: str
    sources: tuple[SourceChip, ...]


class SourceChipBlock(BlockBase):
    type: Literal["source_chip"] = "source_chip"
    source: SourceChip


class CallKey(MeridianModel):
    label: str
    number: str


class SafetyBlock(BlockBase):
    type: Literal["safety"] = "safety"
    level: Literal["DANGER"] = "DANGER"
    signal_word: str
    steps: tuple[str, ...]
    call_key: CallKey
    contact_line: str
    case_priority: Literal["P0"] = "P0"
    case_reference: str | None
    fixed_text: Literal[True] = True
    pinned: Literal[True] = True


class ConditionalSafetyBlock(BlockBase):
    type: Literal["conditional_safety"] = "conditional_safety"
    level: Literal["WARNING"] = "WARNING"
    text: str
    emergency_line: str
    case_priority: Literal["P1"] = "P1"
    case_reference: str | None
    fixed_text: Literal[True] = True


class BurningCheckBlock(BlockBase):
    type: Literal["burning_check"] = "burning_check"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    question: str


class EmergencyLineBlock(BlockBase):
    type: Literal["emergency_line"] = "emergency_line"
    lead_text: str
    number: str
    number_note: str
    separate_line: str | None
    case_priority: Literal["P1"] = "P1"
    case_reference: str


class QuickCheck(MeridianModel):
    text: str
    source: SourceChip


class QuickChecksBlock(BlockBase):
    type: Literal["quick_checks"] = "quick_checks"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    offer_text: str
    checks: tuple[QuickCheck, ...] | None


class UrgencyQuestion(MeridianModel):
    question_id: str
    text: str
    answers: tuple[Option, ...]


class UrgencyQuestionsBlock(BlockBase):
    type: Literal["urgency_questions"] = "urgency_questions"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    questions: tuple[UrgencyQuestion, ...]
    skippable: Literal[True] = True


class WherePromptBlock(BlockBase):
    type: Literal["where_prompt"] = "where_prompt"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    label: str
    submit_label: str


class LocatePromptBlock(BlockBase):
    type: Literal["locate_prompt"] = "locate_prompt"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    reason_text: str
    field_sets: tuple[tuple[Literal["name", "phone", "customer_id", "invoice_number"], ...], ...]


class CodePromptBlock(BlockBase):
    type: Literal["code_prompt"] = "code_prompt"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    state: Literal["sent", "wrong", "expired", "locked"]
    hint: str
    tries_left: int | None
    expires_at: dt.datetime | None
    resend_offered: bool
    resends_left: int | None
    inbox_link: str
    code_in_response: Literal["never"] = "never"


class SlotWindow(MeridianModel):
    slot_id: str
    date: dt.date
    window: str
    window_label: str
    technician: str
    member_only: bool
    taken: bool


class SlotDay(MeridianModel):
    date: dt.date
    label: str
    open_count: int
    windows: tuple[SlotWindow, ...]


class SlotCardBlock(BlockBase):
    type: Literal["slot_card"] = "slot_card"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    urgent: bool
    days: tuple[SlotDay, ...]
    standard_fee: Money
    hint: str
    members_note: str | None


class ConfirmationBlock(BlockBase):
    type: Literal["confirmation"] = "confirmation"
    appointment_id: int
    date: dt.date
    window_label: str
    technician: str
    fee_line: str
    timeline: tuple[str, ...]
    free_change_note: str


class AppointmentBlock(BlockBase):
    type: Literal["appointment"] = "appointment"
    appointment_id: int
    date: dt.date
    window_label: str
    technician: str
    fee_line: str
    label: Literal["Your booked visit"] = "Your booked visit"


class CancelledBlock(BlockBase):
    type: Literal["cancelled"] = "cancelled"
    appointment_id: int
    date: dt.date
    fee_line: str


class AccountInvoiceLine(MeridianModel):
    description: str
    amount: Money
    source: SourceChip | None


class AccountInvoice(MeridianModel):
    invoice_id: str
    lines: tuple[AccountInvoiceLine, ...]
    total: Money
    balance: Money
    due_on: dt.date
    paid: bool


class AccountMembership(MeridianModel):
    tier: str
    renewal_date: dt.date


class AccountWarranty(MeridianModel):
    install_date: dt.date
    sentence: str


class AccountCardBlock(BlockBase):
    type: Literal["account_card"] = "account_card"
    kind: Literal["invoice", "membership", "warranty"]
    invoice: AccountInvoice | None
    membership: AccountMembership | None
    warranty: AccountWarranty | None


class ShownWindow(MeridianModel):
    slot_id: str
    window_label: str
    date: dt.date


class ChangeRequestBlock(BlockBase):
    type: Literal["change_request"] = "change_request"
    change: Literal["move", "cancel"]
    fee_line: str
    original_stays_line: str
    wanted_text: str
    windows_shown: tuple[ShownWindow, ...]
    reference: str
    promise_text: str
    due_at: dt.datetime | None
    due_label: str | None
    extra_lines: tuple[str, ...]
    cant_guarantee_line: str | None
    phone_support_line: str | None
    produced_by_code: Literal[True] = True


class HandoffBlock(BlockBase):
    type: Literal["handoff"] = "handoff"
    card_id: str
    options: tuple[Option, ...]
    answered: str | None
    reference: str
    variant: Literal["nobody_online", "refund", "staffed"]
    promise_text: str
    due_at: dt.datetime | None
    due_label: str | None
    extra_lines: tuple[str, ...]
    produced_by_code: Literal[True] = True
    followup_chooser: FollowUpOptions


class LiveQueuedBlock(BlockBase):
    type: Literal["live_queued"] = "live_queued"
    reference: str
    promise_text: str
    produced_by_code: Literal[True] = True


class FailureOfferBlock(BlockBase):
    type: Literal["failure_offer"] = "failure_offer"
    text: str
    person_key: bool


class NoInfoBlock(BlockBase):
    type: Literal["no_info"] = "no_info"
    text: str
    person_key: bool


class NoticeBlock(BlockBase):
    type: Literal["notice"] = "notice"
    code: Literal["RATE_LIMITED", "BOOKING_CAP", "SPEND_CAP_REACHED", "TURN_TIMEOUT", "BUSY", "AI_PAUSED"]
    text: str
    person_key: bool


class ErrorBlock(BlockBase):
    type: Literal["error"] = "error"
    code: Literal[
        "SLOT_TAKEN",
        "OUT_OF_AREA",
        "CODE_WRONG",
        "CODE_EXPIRED",
        "CODE_LOCKED",
        "CODE_CAP_REACHED",
        "NOT_VERIFIED",
    ]
    text: str
    tries_left: int | None
    fresh_windows: SlotCardBlock | None
    person_key: bool


class SessionEndedBlock(BlockBase):
    type: Literal["session_ended"] = "session_ended"
    text: str
    new_chat_action: str


ReplyBlock = Annotated[
    TextBlock
    | SourceChipBlock
    | SafetyBlock
    | ConditionalSafetyBlock
    | BurningCheckBlock
    | EmergencyLineBlock
    | QuickChecksBlock
    | UrgencyQuestionsBlock
    | WherePromptBlock
    | LocatePromptBlock
    | CodePromptBlock
    | SlotCardBlock
    | ConfirmationBlock
    | AppointmentBlock
    | CancelledBlock
    | AccountCardBlock
    | ChangeRequestBlock
    | HandoffBlock
    | LiveQueuedBlock
    | FailureOfferBlock
    | NoInfoBlock
    | NoticeBlock
    | ErrorBlock
    | SessionEndedBlock,
    Field(discriminator="type"),
]
