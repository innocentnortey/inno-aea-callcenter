"""Specialist result, capture and report types (AEA-02; DO-4 section 5, graph-tools sections 2-3).

Not built here (plan 8.2, blocked on the AEA-02b follow-up): SpecialistTask, KnowledgeSlice, AccountSlice.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import Field

from meridian.domain.actions import CompletedAction
from meridian.domain.common import (
    CallRecord,
    HaltReason,
    InvoiceId,
    LLMFacing,
    MeridianModel,
    PassageId,
    ProviderFailure,
    ToolCallRecord,
    ToolErrorCode,
)
from meridian.domain.records import (
    FeeNote,
    MembershipTier,
    Passage,
    RetrievalResult,
    ServiceType,
    ShownSlot,
    Window,
    Zone,
)


class ConfirmationView(MeridianModel):
    """DO-4 section 5: date, window, technician, fee_note (R-20)."""

    date: dt.date
    window: Window
    technician: str
    fee_note: FeeNote


class WriteResult(MeridianModel):
    action: CompletedAction
    confirmation: ConfirmationView


class ChangeRequestDraft(MeridianModel):
    appointment_id: int
    change: Literal["move", "cancel"]
    wanted_text: str
    windows_shown: tuple[int, ...]
    hours_before: float
    window_start: dt.datetime


class KnowledgePoint(MeridianModel):
    # "must be a passage returned in this run" is enforced by AEA-35's builder, not here (plan 8.3).
    text: str = Field(max_length=500)
    passage_id: PassageId


class InvoiceLineView(MeridianModel):
    description: str
    amount_cents: int


class InvoiceView(MeridianModel):
    invoice_id: InvoiceId
    lines: tuple[InvoiceLineView, ...]
    total_cents: int
    balance_cents: int
    issued_on: dt.date
    due_on: dt.date
    paid: bool


class MembershipView(MeridianModel):
    tier: MembershipTier
    renewal_date: dt.date | None


class WarrantyView(MeridianModel):
    install_date: dt.date
    equipment_brand: str | None
    sentence: str


class StaffNote(MeridianModel):
    kind: Literal["billed_differs_from_schedule", "diagnostic_without_credit"]
    record_id: InvoiceId
    text: str = Field(max_length=300)
    source_file: Literal["pricing/2026_fee_schedule.pdf", "faq/customer_faq.md"]


class KnowledgeCapture(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"
    result: RetrievalResult


class AccountCapture(MeridianModel):
    kind: Literal["account"] = "account"
    invoices: tuple[InvoiceView, ...] = ()
    membership: MembershipView | None = None
    warranty: WarrantyView | None = None
    staff_notes: tuple[StaffNote, ...] = ()


class SchedulingCapture(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    windows: tuple[ShownSlot, ...] = ()
    write: WriteResult | None = None
    change_request: ChangeRequestDraft | None = None
    refused: ToolErrorCode | None = None


class AppointmentView(MeridianModel):
    """graph-tools section 3 (R-G-19)."""

    appointment_id: int
    date: dt.date
    window: Window
    service_type: ServiceType
    technician: str | None
    is_warranty_visit: bool


class SchedulingSliceInputs(MeridianModel):
    zone: Zone | None
    member: bool
    appointments: tuple[AppointmentView, ...] = ()


class SchedulingSlice(MeridianModel):
    """DO-4 section 5."""

    customer_zone: Zone | None
    member: bool
    appointments: tuple[AppointmentView, ...]
    shown_slots: tuple[ShownSlot, ...]
    pending_change: bool
    bookings_left: int


class KnowledgeResult(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"
    status: Literal["answered", "no_current_source", "failed"]
    passages: tuple[Passage, ...]
    points: tuple[KnowledgePoint, ...]
    quick_checks: tuple[PassageId, ...] = ()
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None


class AccountResult(MeridianModel):
    kind: Literal["account"] = "account"
    status: Literal["read", "not_verified", "failed"]
    invoices: tuple[InvoiceView, ...] = ()
    membership: MembershipView | None = None
    warranty: WarrantyView | None = None
    staff_notes: tuple[StaffNote, ...] = ()
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None


class SchedulingResult(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
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
    ]
    windows: tuple[ShownSlot, ...] = ()
    write: WriteResult | None = None
    change_request: ChangeRequestDraft | None = None
    quick_checks: tuple[Passage, ...] = ()  # graph-tools section 3 (GRT-8)
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None


SpecialistResult = Annotated[KnowledgeResult | AccountResult | SchedulingResult, Field(discriminator="kind")]


class ReportedPoint(LLMFacing):
    """DO-4 section 5: {text <= 500, passage_id}."""

    text: str = Field(max_length=500)
    passage_id: PassageId


class KnowledgeReport(LLMFacing):
    points: list[ReportedPoint] = Field(max_length=5)
    answered: bool


class AccountReport(LLMFacing):
    summary: str = Field(max_length=300)


class SchedulingReport(LLMFacing):
    appointment_id: int
    wanted_time: str
    note: str = Field(max_length=200)
