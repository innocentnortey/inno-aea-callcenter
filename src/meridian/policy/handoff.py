"""Promise, due time and priority rules for a handoff (A6).

Pure: no I/O, no clock read (`now` is always an argument), no model. Every customer sentence
comes from `policy/texts.py`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from types import MappingProxyType
from typing import Final, Literal
from zoneinfo import ZoneInfo

from meridian.domain.handoff import HandoffReason, Presence, Priority, Promise
from meridian.policy.texts import TEXTS, TextId, render

__all__ = [
    "CLOSE_OF_BUSINESS",
    "D4_ROWS",
    "DUE_SOON_WINDOW",
    "HOLIDAYS_CLOSED",
    "PHONE_HOURS",
    "PROMISE_TABLE",
    "SHORT_DAYS",
    "STAFF_GUIDANCE_FOR",
    "UNOWNED_AFTER",
    "D4CaseRule",
    "D4Row",
    "PolicyRow",
    "business_due",
    "case_due_at",
    "due_label",
    "is_business_day",
    "phone_support_open",
    "priority_for",
    "promise_for",
    "window_start_of",
]

_CHICAGO: Final = ZoneInfo("America/Chicago")

# [Source: KB policies/holiday_hours_2026.png (CAS-9)]
HOLIDAYS_CLOSED: Final[frozenset[date]] = frozenset(
    {
        date(2026, 5, 25),
        date(2026, 7, 4),
        date(2026, 9, 7),
        date(2026, 11, 26),
        date(2026, 11, 27),
        date(2026, 12, 25),
        date(2027, 1, 1),
    }
)
# Same image, "Christmas Eve 7am - 12pm".
SHORT_DAYS: Final[Mapping[date, time]] = MappingProxyType({date(2026, 12, 24): time(12, 0)})
# [Source: FAQ phone support Mon-Fri 7:00am-7:00pm]
CLOSE_OF_BUSINESS: Final = time(19, 0)
# weekday(); 6 (Sunday) absent = closed
PHONE_HOURS: Final[Mapping[int, tuple[time, time]]] = MappingProxyType(
    {
        0: (time(7, 0), time(19, 0)),
        1: (time(7, 0), time(19, 0)),
        2: (time(7, 0), time(19, 0)),
        3: (time(7, 0), time(19, 0)),
        4: (time(7, 0), time(19, 0)),
        5: (time(8, 0), time(16, 0)),
    }
)

_WEEKDAYS: Final = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
_MONTHS: Final = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _local(dt: datetime, name: str) -> datetime:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return dt.astimezone(_CHICAGO)


def is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in HOLIDAYS_CLOSED


def _close_on(d: date) -> time:
    return SHORT_DAYS.get(d, CLOSE_OF_BUSINESS)


def business_due(now: datetime, days: int) -> datetime:
    if days < 1:
        raise ValueError("days must be at least 1")
    d = _local(now, "now").date()
    count = 0
    while count < days:
        d += timedelta(days=1)
        if is_business_day(d):
            count += 1
    return datetime.combine(d, _close_on(d), tzinfo=_CHICAGO)


def _phone_hours_on(d: date) -> tuple[time, time] | None:
    if d in HOLIDAYS_CLOSED:
        return None
    hours = PHONE_HOURS.get(d.weekday())
    if hours is None:
        return None
    if d in SHORT_DAYS:
        return (hours[0], min(hours[1], SHORT_DAYS[d]))
    return hours


def phone_support_open(now: datetime) -> bool:
    local = _local(now, "now")
    hours = _phone_hours_on(local.date())
    if hours is None:
        return False
    return hours[0] <= local.time() < hours[1]


def _clock_text(t: time) -> str:
    hour12 = t.hour % 12 or 12
    return f"{hour12}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}"


def due_label(dt: datetime) -> str:
    local = _local(dt, "dt")
    return (
        f"{_WEEKDAYS[local.weekday()]}, {_MONTHS[local.month - 1]} {local.day}, {_clock_text(local.time())}"
    )


PolicyRow = Literal["R26.unstaffed", "R26.refund", "R26.staffed", "R26.safety_none", "OD4.danger_review"]

_ROW_TEXT: Final[Mapping[PolicyRow, TextId]] = MappingProxyType(
    {
        "R26.unstaffed": TextId.PROMISE_UNSTAFFED,
        "R26.refund": TextId.PROMISE_REFUND,
        "R26.staffed": TextId.PROMISE_STAFFED,
        "R26.safety_none": TextId.PROMISE_SAFETY_NONE,
        "OD4.danger_review": TextId.PROMISE_DANGER_REVIEW,
    }
)
PROMISE_TABLE: Final[Mapping[PolicyRow, str]] = MappingProxyType(
    {row: TEXTS[tid] for row, tid in _ROW_TEXT.items()}
)

# [Source: scheduling_db/SCHEMA.md "window" 08:00-12:00, 12:00-16:00, 13:00-17:00, 16:00-19:00;
# starts are unique, so the start names the window]
_ISSUED_WINDOW_END: Final[Mapping[time, time]] = MappingProxyType(
    {
        time(8, 0): time(12, 0),
        time(12, 0): time(16, 0),
        time(13, 0): time(17, 0),
        time(16, 0): time(19, 0),
    }
)


def _window_text(window_start: datetime) -> str:
    start = _local(window_start, "window_start").time()
    end = _ISSUED_WINDOW_END.get(start)
    if end is None:
        raise ValueError("window_start is not the start of an issued window")
    return f"{_clock_text(start)} – {_clock_text(end)}"


def window_start_of(slot_date: date, window: str) -> datetime:
    """The Chicago start of an issued appointment window on `slot_date` ("12:00-16:00" -> 12:00).

    Raises ValueError for a window the issued schema does not have. CAS-16 option A: a burning_ruled_out case is due
    at this time once its urgent visit is booked.
    """
    start = time.fromisoformat(window[:5])
    if start not in _ISSUED_WINDOW_END:
        raise ValueError("window is not an issued appointment window")
    return datetime.combine(slot_date, start, tzinfo=_CHICAGO)


def _make(
    row: PolicyRow,
    due_at: datetime | None,
    extra: tuple[str, ...] = (),
    live: bool = False,
) -> Promise:
    return Promise(
        policy_row=row,
        text=PROMISE_TABLE[row],
        due_at=due_at,
        due_label=None if due_at is None else due_label(due_at),
        extra_lines=extra,
        live_queued=live,
    )


def _fee_lines(
    reason: HandoffReason,
    local_now: datetime,
    due: datetime | None,
    window_start: datetime | None,
) -> tuple[str, ...]:
    if reason is not HandoffReason.FEE_BEARING_CHANGE:
        return ()
    lines: list[str] = []
    if window_start is not None and due is not None and window_start < due:
        lines.append(render(TextId.FEE_CANT_GUARANTEE, window=_window_text(window_start)))
    hours = _phone_hours_on(local_now.date())
    if phone_support_open(local_now) and hours is not None and hours[1] == CLOSE_OF_BUSINESS:
        lines.append(render(TextId.FEE_PHONE_SUPPORT_OPEN))
    return tuple(lines)


def promise_for(
    reason: HandoffReason,
    presence: Presence,
    now: datetime,
    window_start: datetime | None = None,
) -> Promise:
    local_now = _local(now, "now")
    if reason is HandoffReason.SAFETY:
        return _make("R26.safety_none", None)
    if presence == "simulated_on_shift":
        return _make(
            "R26.staffed",
            None,
            _fee_lines(reason, local_now, None, window_start),
            live=True,
        )
    if reason in {HandoffReason.DANGER, HandoffReason.BURNING_UNCLEAR}:
        return _make("OD4.danger_review", business_due(now, 1))
    if reason is HandoffReason.REFUND:
        return _make(
            "R26.refund",
            business_due(now, 2),
            (render(TextId.PROMISE_REFUND_NO_OUTCOME),),
        )
    due = business_due(now, 1)
    return _make("R26.unstaffed", due, _fee_lines(reason, local_now, due, window_start))


def case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None:
    if (
        reason in {HandoffReason.FEE_BEARING_CHANGE, HandoffReason.BURNING_RULED_OUT}
        and window_start is not None
    ):
        return window_start
    return promise.due_at


_PRIORITY: Final[Mapping[HandoffReason, Priority]] = MappingProxyType(
    {
        HandoffReason.SAFETY: Priority.P0,
        HandoffReason.DANGER: Priority.P1,
        HandoffReason.BURNING_UNCLEAR: Priority.P1,
        HandoffReason.FEE_BEARING_CHANGE: Priority.P2,
        HandoffReason.LATE_TECHNICIAN: Priority.P2,
        HandoffReason.BURNING_RULED_OUT: Priority.P2,  # CAS-16 option A (D-14)
        HandoffReason.UNSUPPORTED_ACTION: Priority.P4,  # CAS-12
        HandoffReason.CUSTOMER_REQUESTED_PERSON: Priority.P3,
        HandoffReason.REFUND: Priority.P3,
        HandoffReason.BILLING_DISPUTE: Priority.P3,
        HandoffReason.COMPLAINT_OR_MANAGER: Priority.P3,
        HandoffReason.LEGAL_OR_CHARGEBACK: Priority.P3,
        HandoffReason.COMMERCIAL: Priority.P3,
        HandoffReason.IDENTITY_UNVERIFIED: Priority.P3,
        HandoffReason.AI_FAILURE: Priority.P3,
    }
)


def priority_for(
    reason: HandoffReason,
    *,
    promise_due: datetime | None = None,
    renewal_date: date | None = None,
) -> Priority:
    if reason is HandoffReason.MEMBERSHIP_CANCEL:
        if (
            renewal_date is not None
            and promise_due is not None
            and renewal_date <= _local(promise_due, "promise_due").date()
        ):
            return Priority.P2
        return Priority.P3
    try:
        return _PRIORITY[reason]
    except KeyError:
        raise ValueError(f"no priority for reason {reason.value}") from None


DUE_SOON_WINDOW: Final = timedelta(hours=4)  # [A] CAS-20; replaced by the Stage 9 staff walkthrough
UNOWNED_AFTER: Final = timedelta(minutes=30)  # [A] CAS-20; same measurement; both on the demo clock

# [Source: KB internal/agent_discretion_notes.md; cases §5, CAS-33]. Staff guidance only; never customer text.
STAFF_GUIDANCE_FOR: Final[Mapping[HandoffReason, tuple[str, ...]]] = MappingProxyType(
    {
        HandoffReason.FEE_BEARING_CHANGE: ("Waive the $49 late-cancellation fee once per customer per year",),
        HandoffReason.LATE_TECHNICIAN: (
            "Waive the diagnostic fee when the technician arrived more than 30 minutes",
        ),
        HandoffReason.BILLING_DISPUTE: ("Extend a 10% courtesy discount on a repair invoice under $500",),
        HandoffReason.COMPLAINT_OR_MANAGER: (
            "Extend a 10% courtesy discount on a repair invoice under $500",
        ),
        HandoffReason.REFUND: ("Issue refunds of any kind.",),
    }
)

D4CaseRule = Literal["none", "p4_if_accepted", "p4", "p2", "p3"]


@dataclass(frozen=True, slots=True)
class D4Row:
    request: str  # the table's bold request label
    evidence: str  # the parenthesis after it (inventory codes)
    case_rule: D4CaseRule  # the Case column's leading rule
    note: str | None  # the rest of the Case column, `**` removed; None when nothing follows


# [Source: consolidated direction §9.4 table, in order]
D4_ROWS: Final[tuple[D4Row, ...]] = (
    D4Row(
        "Pay an invoice", "BILL-PAY 14; §5.2", "p4", "due date in the brief; P2 if the invoice is past due"
    ),
    D4Row("Set up autopay", "BILL-AUTOPAY 14", "p4_if_accepted", None),
    D4Row(
        "Turn off auto-renew", "MEM-CANCEL 13", "p2", "if renewal falls within the follow-up window, else P3"
    ),
    D4Row(
        "Upgrade to Plus", "MEM-UPGRADE 6", "p4", "the AI does not change `membership_tier` without payment"
    ),
    D4Row(
        "Duplicate charge", "BILL-DUP 11", "none", "at first; P3 if both posted; a dispute → supervisor (P3)"
    ),
    D4Row("Registration check", "WAR-REGISTER 10; WAR-PARTS 7", "p4_if_accepted", None),
    D4Row(
        "Repeat repair under warranty",
        "WAR-REPEAT 6",
        "p4",
        "for staff to check history; the AI does not set `is_warranty_visit` on a claim",
    ),
    D4Row("Install-warranty term", "WAR-CLAIM 14", "none", "unless a booking or a confirmation is wanted"),
    D4Row("Itemized copy by email", "BILL-EXPLAIN 13", "p4_if_accepted", None),
    D4Row("Late technician", "SCH-LATE 9", "p2", None),
    D4Row(
        "Waitlist / earlier slot",
        "34 booking calls",
        "none",
        "unless urgent (P1) or the customer asks for a person",
    ),
    D4Row("Quote vs invoice", "BILL-DISPUTE 16", "p3", None),
    D4Row("Refund", "BILL-REFUND 8", "p3", None),
    D4Row("Commercial quote", "COMMERCIAL 5", "p3", "routed to commercial"),
    D4Row("Job inquiry", "HIRING 6", "none", None),
)
