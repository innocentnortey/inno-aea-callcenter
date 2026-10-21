"""Issued-data record types, slots, passages and retrieval results (AEA-02; DO-4 section 5, cases.md sections 2, 4.1)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import Field, SecretStr

from meridian.domain.common import CustomerId, InvoiceId, MeridianModel, PassageId, TurnId

Zone = Literal["north", "central", "south"]  # cases.md section 2 (CAS-34)
Window = Literal["08:00-12:00", "12:00-16:00", "13:00-17:00", "16:00-19:00"]  # issued appointment_slots CHECK
ServiceType = Literal["hvac_repair", "hvac_tune_up", "plumbing", "estimate"]  # issued appointment_slots CHECK
MembershipTier = Literal["none", "standard", "plus"]  # issued customers CHECK


class FeeNote(MeridianModel):
    """cases.md section 2, transcribed unchanged (R-G-2)."""

    service_type: ServiceType
    tier: MembershipTier
    fee_row: str | None
    amount_cents: int = Field(ge=0)
    waived: bool
    line: str = Field(min_length=1, max_length=120)


class Customer(MeridianModel):
    """Issued customers columns (SCHEMA.md); phone and email are private (decision D-5)."""

    customer_id: CustomerId
    name: str
    phone: SecretStr
    email: SecretStr | None
    service_address: str
    city: str
    zip: str
    membership_tier: MembershipTier
    membership_renewal_date: dt.date | None
    system_brand: str | None
    system_install_date: dt.date | None


class Technician(MeridianModel):
    """Issued technicians columns; skills parsed from the comma list."""

    tech_id: int
    name: str
    skills: tuple[Literal["hvac", "plumbing", "estimate"], ...]
    home_zone: Zone


class InvoiceLineItem(MeridianModel):
    """One element of invoices.line_items JSON ({desc, cents})."""

    desc: str
    cents: int


class Invoice(MeridianModel):
    """Issued invoices columns."""

    invoice_id: InvoiceId
    customer_id: CustomerId
    appointment_id: int | None
    issued_date: dt.date
    due_date: dt.date
    amount_cents: int
    balance_cents: int
    line_items: tuple[InvoiceLineItem, ...]


class Slot(MeridianModel):
    """cases.md section 4.1 (CAS-36)."""

    slot_id: int
    slot_date: dt.date
    window: Window
    tech_id: int
    zone: Zone
    service_type: ServiceType
    status: Literal["open", "booked", "reserved_members", "blocked"]


class Appointment(MeridianModel):
    """cases.md section 4.1 (CAS-36)."""

    appointment_id: int
    slot_id: int
    customer_id: CustomerId
    issue_description: str
    created_at: dt.date
    status: Literal["scheduled", "completed", "cancelled", "no_show"]
    is_warranty_visit: bool


class Passage(MeridianModel):
    """DO-4 section 5."""

    passage_id: PassageId
    file: str
    section: str
    version_label: str
    version_date: dt.date | None
    text: str
    score: float


class RetrievalResult(MeridianModel):
    """DO-4 section 13 (home: ports/runtime.py)."""

    passages: tuple[Passage, ...]
    below_floor: bool


class ShownSlot(MeridianModel):
    """DO-4 section 1 (home: state.py)."""

    slot_id: int
    date: dt.date
    window: Window
    technician: str
    service_type: ServiceType
    zone: Zone
    member_reserved: bool
    shown_turn: TurnId
