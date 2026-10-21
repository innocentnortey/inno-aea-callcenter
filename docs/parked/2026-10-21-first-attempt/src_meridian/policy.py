"""Policy as code: zones, promises, priorities, due times, fee rules (PRD R-18, R-21, R-26; OD-4).

Nothing here is decided by the model.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

ZONE_BY_CITY = {
    "round rock": "north", "cedar park": "north", "pflugerville": "north", "georgetown": "north",
    "leander": "north", "hutto": "north", "austin": "central", "kyle": "south", "buda": "south",
    # Q-3 (Innocent, 2026-10-20): bookable, mapped to central in our code (SCHEMA.md not edited)
    "dripping springs": "central", "manor": "central",
}
NOT_SERVED = {"san marcos", "bastrop", "elgin", "lakeway"}
LAKEWAY_ZIPS = {"78734", "78738"}  # "Lakeway (west of 620)" excluded; specific exclusion wins (audit K-11)

PHONE_HOURS = {0: (7, 19), 1: (7, 19), 2: (7, 19), 3: (7, 19), 4: (7, 19), 5: (8, 16)}  # Mon–Sat; closed Sun

WINDOW_LABELS = {"08:00-12:00": "8am–12pm", "12:00-16:00": "12pm–4pm", "13:00-17:00": "1pm–5pm",
                 "16:00-19:00": "4pm–7pm"}

LATE_FEE = 49  # FAQ + 2026 fee schedule: inside 24 hours of the window, every tier

# reason -> (priority, promise when nobody is online, business days)
REASONS = {
    "safety": ("P0", None, None),
    "urgent_comfort": ("P1", "Someone from our team will review this online request within 1 business day. "
                              "That is not the wait for emergency help; for that, please call the emergency number.", 1),
    "burning_unclear": ("P1", "Someone from our team will review this online request within 1 business day.", 1),
    "refund": ("P3", "A representative will get to your refund request within 2 business days.", 2),
    "billing_dispute": ("P3", "A representative will get back to you within 1 business day.", 1),
    "complaint": ("P3", "A representative will get back to you within 1 business day.", 1),
    "manager_request": ("P3", "A representative will get back to you within 1 business day.", 1),
    "legal_or_chargeback": ("P3", "A representative will get back to you within 1 business day.", 1),
    "commercial": ("P3", "A representative will pass your details to Meridian Commercial and get back to you within 1 business day.", 1),
    "late_technician": ("P2", "A representative will get back to you within 1 business day.", 1),
    "fee_contested": ("P3", "A representative will get back to you within 1 business day.", 1),
    "time_sensitive_action": ("P2", "A representative will get back to you within 1 business day.", 1),
    "unsupported_action": ("P4", "A representative will get back to you within 1 business day.", 1),
    "customer_requested_person": ("P3", "A representative will get back to you within 1 business day.", 1),
    "ai_failure": ("P3", "A representative will get back to you within 1 business day.", 1),
    "identity_unverified": ("P3", "A representative will get back to you within 1 business day.", 1),
    "out_of_scope": ("P4", "A representative will get back to you within 1 business day.", 1),
}
STAFFED_PROMISE = "A representative will join this chat when available."
SAFETY_FOLLOWUP = "We've flagged this as a safety priority for our team."  # no time promised (OD-4 iii)


def zone_for(city: str | None, zip_code: str | None) -> str | None:
    if zip_code and zip_code in LAKEWAY_ZIPS:
        return None
    if not city:
        return None
    c = city.strip().lower()
    if c in NOT_SERVED:
        return None
    return ZONE_BY_CITY.get(c)


def add_business_days(start: datetime, n: int) -> datetime:
    """Due time = close of phone hours on the n-th business day after start (Mon–Fri; Sat counts as no business day)."""
    d: date = start.date()
    added = 0
    while added < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return datetime(d.year, d.month, d.day, 19, 0)


def promise_for(reason: str, staffed: bool, now: datetime) -> tuple[str, str, str | None]:
    """Return (priority, promise_text, due_iso) for a handoff reason (policy table, never the model)."""
    priority, text, days = REASONS.get(reason, REASONS["out_of_scope"])
    if reason == "safety":
        return priority, SAFETY_FOLLOWUP, None
    if staffed:
        return priority, STAFFED_PROMISE, None
    due = add_business_days(now, days)
    return priority, text, due.isoformat(timespec="minutes")


def hours_until(window_date: str, window: str, now: datetime) -> float:
    start = datetime.fromisoformat(f"{window_date}T{window.split('-')[0]}")
    return (start - now).total_seconds() / 3600


def late_fee_applies(window_date: str, window: str, now: datetime) -> bool:
    return hours_until(window_date, window, now) < 24
