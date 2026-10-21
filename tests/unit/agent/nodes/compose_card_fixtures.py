"""Synthetic builders for the compose card tests (AEA-21b plan section 6). Issued ids and synthetic data only."""

from __future__ import annotations

import datetime as dt

from jsonschema import Draft202012Validator

from meridian.domain import blocks as b
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, OpenCase
from meridian.domain.common import CaseRef, CustomerId, HandoffReason, InvoiceId, Priority, TurnId
from meridian.domain.identity import IdentityState
from meridian.domain.records import ShownSlot
from meridian.domain.specialists import (
    AccountResult,
    InvoiceLineView,
    InvoiceView,
    MembershipView,
    SchedulingResult,
    StaffNote,
    WarrantyView,
)
from meridian.domain.state import OpenTask, TaskDetails
from meridian.domain.turn import TaskIntent
from tests.api.openapi_check import load_contract
from tests.contract.openapi_variants import ref_schema
from tests.unit.agent.nodes import compose_fixtures as fx

BOOKING_TASK_ID = "task-1a2b3c4d-1"  # what `facts` mints for TURN3 order 1 (reply.py)
STAFF_SENTINEL = "SENTINEL-STAFF-NOTE-21B"


def booking_task(
    status: str = "open", intent: TaskIntent = TaskIntent.BOOK_NEW, task_id: str = BOOKING_TASK_ID
) -> OpenTask:
    return OpenTask.model_validate(
        {
            "task_id": task_id,
            "specialist": "scheduling",
            "intent": intent,
            "opened_turn": fx.TURN3,
            "details": TaskDetails(),
            "status": status,
        }
    )


class TaskWithMissing(OpenTask):
    """Stands in for DO-4 section 1's `missing` field until AEA-02 adds it."""

    missing: tuple[str, ...] = ()


def _slot(slot_id: int, date: dt.date, window: str, tech: str, *, member: bool = False) -> ShownSlot:
    return ShownSlot.model_validate(
        {
            "slot_id": slot_id,
            "date": date,
            "window": window,
            "technician": tech,
            "service_type": "hvac_repair",
            "zone": "north",
            "member_reserved": member,
            "shown_turn": fx.TURN4,
        }
    )


def wp3_windows() -> tuple[ShownSlot, ...]:
    """WP-3 Monday 2026-10-19, given out of order (58, 56, 42) so the tests prove the sort."""
    mon = dt.date(2026, 10, 19)
    return (
        _slot(58, mon, "13:00-17:00", "Marta Kowalski"),
        _slot(56, mon, "08:00-12:00", "Marta Kowalski"),
        _slot(42, mon, "12:00-16:00", "Ray Mendoza"),
    )


def wednesday_member_window() -> ShownSlot:
    return _slot(61, dt.date(2026, 10, 21), "16:00-19:00", "Marta Kowalski", member=True)


def scheduling(status: str, windows: tuple[ShownSlot, ...] = ()) -> SchedulingResult:
    return SchedulingResult.model_validate({"status": status, "windows": windows, "tools": (), "calls": ()})


def verified_identity() -> IdentityState:
    return IdentityState(
        status="verified",
        customer_id=CustomerId("MHC-10001"),
        masked_hint="the phone ending in 01",
        code_expires_at=None,
        tries_left=3,
        codes_sent=1,
        verified_at=fx.DEMO_NOW,
    )


def wp2_invoice() -> InvoiceView:
    """WP-2: INV-204411, $89 + $245 + $144 = $478.00, due 2026-11-01, unpaid."""
    return InvoiceView(
        invoice_id=InvoiceId("INV-204411"),
        lines=(
            InvoiceLineView(description="Diagnostic visit", amount_cents=8900),
            InvoiceLineView(description="Contactor replacement", amount_cents=24500),
            InvoiceLineView(description="After-hours dispatch", amount_cents=14400),
        ),
        total_cents=47800,
        balance_cents=47800,
        issued_on=dt.date(2026, 10, 2),
        due_on=dt.date(2026, 11, 1),
        paid=False,
    )


def account_read(
    *,
    invoices: tuple[InvoiceView, ...] = (),
    membership: MembershipView | None = None,
    warranty: WarrantyView | None = None,
    staff_notes: tuple[StaffNote, ...] = (),
) -> AccountResult:
    return AccountResult(
        status="read",
        invoices=invoices,
        membership=membership,
        warranty=warranty,
        staff_notes=staff_notes,
        tools=(),
        calls=(),
    )


def warranty() -> WarrantyView:
    return WarrantyView(
        install_date=dt.date(2025, 6, 2),
        equipment_brand=None,
        sentence="Labor is covered for 2 years from the install date; a representative can confirm whether the 5-year term applies.",
    )


def staff_note() -> StaffNote:
    return StaffNote(
        kind="diagnostic_without_credit",
        record_id=InvoiceId("INV-204411"),
        text=STAFF_SENTINEL,
        source_file="faq/customer_faq.md",
    )


def booked_action(turn: TurnId = fx.TURN3) -> CompletedAction:
    """WP-3 booked visit: appointment 30412, slot 56, Monday 2026-10-19 8-12."""
    return CompletedAction.model_validate(
        {
            "key": ActionKey(thread_id=fx.THREAD, turn_id=turn, kind=ActionKind.BOOKED, record_id="30412"),
            "kind": ActionKind.BOOKED,
            "records": {"appointment": "30412", "slot": "56"},
            "after": {
                "date": "2026-10-19",
                "window": "08:00-12:00",
                "technician": "Marta Kowalski",
                "service_type": "hvac_repair",
                "fee_line": "Diagnostic fee: waived for Comfort Club members (normally $89)",
            },
            "at": fx.DEMO_NOW - dt.timedelta(minutes=5),
        }
    )


def ruled_out_case() -> OpenCase:
    promise = fx.handoff_result("R26.unstaffed", "A person will call.").case.promise
    return OpenCase(
        case_ref=CaseRef("MHC-C-0009"),
        reason=HandoffReason.BURNING_RULED_OUT,
        priority=Priority.P2,
        state="unassigned",
        promise=promise,
        followup=None,
        live_queued=False,
    )


def assert_matches_openapi(block: b.ReplyBlock) -> None:
    validator = Draft202012Validator(
        ref_schema("/components/schemas/ReplyBlock"), registry=load_contract().registry
    )
    errors = [e.message[:200] for e in validator.iter_errors(block.model_dump(mode="json"))]
    assert errors == []
