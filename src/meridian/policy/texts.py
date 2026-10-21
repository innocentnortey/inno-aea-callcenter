"""Every fixed sentence the backend sends to a customer, word for word.

UX owns the words (UXR-18, DAT-6); this module copies them and never rewrites them.
After wave 0 it is frozen: a missing sentence is a small follow-up ticket merged
before its dependants. It imports only the standard library (DO-3 section 4.1).
"""

from __future__ import annotations

import re
import string
from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Final

__all__ = [
    "PLACEHOLDERS",
    "TEXTS",
    "TextId",
    "TextRenderError",
    "format_usd",
    "render",
]

PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {"case_ref", "due_label", "window", "digits", "rep_name", "n", "amount"}
)


class TextId(StrEnum):
    """Text ids, valued "<group>.<name>" (data.md section 2)."""

    # --- greeting ---
    GREETING = "greeting.opening"
    ARE_YOU_A_PERSON = "greeting.are_you_a_person"
    # --- safety ---
    SAFETY_LEAVE_NOW = "safety.leave_now"
    SAFETY_DONT_TOUCH = "safety.dont_touch"
    SAFETY_CONTACT_LINE = "safety.contact_line"
    BURNING_QUESTION = "safety.burning_question"
    WARNING_TEXT = "safety.warning_text"
    EMERGENCY_NUMBER_LINE = "safety.emergency_number_line"
    EMERGENCY_LINE_LEAD = "safety.emergency_line_lead"
    URGENCY_HOT_COLD = "safety.urgency_hot_cold"
    URGENCY_WATER = "safety.urgency_water"
    URGENCY_AT_RISK = "safety.urgency_at_risk"
    REGULAR_BOOKING_NOTE = "safety.regular_booking_note"
    # --- identity ---
    CODE_PROMPT = "identity.code_prompt"
    VERIFIED = "identity.verified"
    CODE_WRONG = "identity.code_wrong"
    CODE_EXPIRED = "identity.code_expired"
    NOT_VERIFIED = "identity.not_verified"
    INBOX_CODE_BODY = "identity.inbox_code_body"
    INBOX_CODE_GONE = "identity.inbox_code_gone"
    # --- promise ---
    PROMISE_UNSTAFFED = "promise.unstaffed"
    PROMISE_REFUND = "promise.refund"
    PROMISE_REFUND_NO_OUTCOME = "promise.refund_no_outcome"
    PROMISE_STAFFED = "promise.staffed"
    PROMISE_DANGER_REVIEW = "promise.danger_review"
    PROMISE_SAFETY_NONE = "promise.safety_none"
    REFERENCE_LINE = "promise.reference_line"
    # --- fee_change ---
    FEE_APPLIES = "fee_change.fee_applies"
    FEE_ORIGINAL_STAYS = "fee_change.original_stays"
    FEE_CANT_GUARANTEE = "fee_change.cant_guarantee"
    FEE_PHONE_SUPPORT_OPEN = "fee_change.phone_support_open"
    # --- followup ---
    FOLLOWUP_LEGEND = "followup.legend"
    FOLLOWUP_SAVED_PHONE = "followup.saved_phone"
    RECORDED_NOT_SENT = "followup.recorded_not_sent"
    # --- booking ---
    BOOKED = "booking.booked"
    SLOT_TAKEN = "booking.slot_taken"
    OUT_OF_AREA = "booking.out_of_area"
    NO_WINDOW_FITS = "booking.no_window_fits"
    IDENTITY_NEEDED = "booking.identity_needed"
    CANCELLED_NO_FEE = "booking.cancelled_no_fee"
    FEE_STANDARD_DIAGNOSTIC = "booking.fee_standard_diagnostic"
    FEE_DIAGNOSTIC_WAIVED = "booking.fee_diagnostic_waived"
    FEE_TUNE_UP = "booking.fee_tune_up"
    FEE_TUNE_UP_INCLUDED = "booking.fee_tune_up_included"
    FEE_ESTIMATE_FREE = "booking.fee_estimate_free"
    SLOTS_NOT_HELD = "booking.slots_not_held"
    MEMBERS_NOTE = "booking.members_note"
    FREE_CHANGE_NOTE = "booking.free_change_note"
    URGENT_NOTE = "booking.urgent_note"
    QUICK_CHECKS_OFFER = "booking.quick_checks_offer"
    # --- limits ---
    TURN_TIMEOUT = "limits.turn_timeout"
    BUSY = "limits.busy"
    RATE_LIMITED = "limits.rate_limited"
    BOOKING_CAP = "limits.booking_cap"
    SPEND_CAP_REACHED = "limits.spend_cap_reached"
    NO_INFORMATION = "limits.no_information"
    FAILURE_OFFER = "limits.failure_offer"
    # --- live ---
    REP_JOINED = "live.rep_joined"
    AI_PAUSED = "live.ai_paused"
    AI_RESUMED = "live.ai_resumed"
    CHAT_CLOSED = "live.chat_closed"
    AI_PAUSED_NOTICE = "live.ai_paused_notice"
    PERSON_REQUEST_LABEL = "live.person_request_label"
    # --- demo ---
    SHIFT_ENDED = "demo.shift_ended"
    STAFFING_CHANGED_ON_SHIFT = "demo.staffing_changed_on_shift"
    STAFFING_BANNER = "demo.staffing_banner"
    DEMO_RESET = "demo.reset"
    OVERSIGHT_OVERDUE = "demo.oversight_overdue"
    OVERSIGHT_SHIFT_ENDED_ONE_WAITING = "demo.oversight_shift_ended_one_waiting"
    MONITOR_SPEND_CAP = "demo.monitor_spend_cap"
    MONITOR_LATENCY = "demo.monitor_latency"
    MONITOR_RESTART = "demo.monitor_restart"
    MONITOR_ZERO_TRAFFIC = "demo.monitor_zero_traffic"
    MONITOR_FAILURE_RATE = "demo.monitor_failure_rate"
    MONITOR_TRACE_EXPORT = "demo.monitor_trace_export"


_TEXTS: Final[dict[TextId, str]] = {
    # --- greeting ---
    TextId.GREETING: (
        "Hi, I'm Meridian Home Comfort's automated assistant, not a person. I "
        "can answer questions about our services, book a visit, and look up "
        "your account once you've confirmed it's you. If you'd like a person "
        "at any point, tap Talk to a person."
    ),
    TextId.ARE_YOU_A_PERSON: (
        "No. I'm Meridian's automated assistant. If you'd like a person, tap Talk to a person."
    ),
    # --- safety ---
    TextId.SAFETY_LEAVE_NOW: ("Leave the home immediately and call 911 or your gas utility from outside."),
    TextId.SAFETY_DONT_TOUCH: ("Don't flip switches, open windows near the furnace, or restart equipment."),
    TextId.SAFETY_CONTACT_LINE: ("Once you're outside and safe, you can leave a number here if you'd like."),
    TextId.BURNING_QUESTION: (
        "Do you already know whether a breaker has tripped? Please don't go to "
        "the panel to check. Do you see any smoke, sparks or flames?"
    ),
    TextId.WARNING_TEXT: (
        "A burning smell can be serious. If you smell gas, see smoke, sparks "
        "or flames, or a breaker has tripped, leave the home immediately and "
        "call 911 from outside."
    ),
    TextId.EMERGENCY_NUMBER_LINE: "Meridian's 24/7 emergency number is (512) 555-0199 (demo number).",
    TextId.EMERGENCY_LINE_LEAD: (
        "Because someone may be in danger, please call Meridian's 24/7 "
        "emergency number now: (512) 555-0199 (demo number). I've also logged "
        "this for our team as an emergency-priority request."
    ),
    TextId.URGENCY_HOT_COLD: "Is it very hot or very cold in your home right now?",
    TextId.URGENCY_WATER: "Is water still running?",
    TextId.URGENCY_AT_RISK: ("Is anyone at higher risk, like an older person, a baby or someone unwell?"),
    TextId.REGULAR_BOOKING_NOTE: "This is a regular booking, not emergency service.",
    # --- identity ---
    TextId.CODE_PROMPT: (
        "I've sent a 6-digit code to the phone number on your account, ending "
        "in {digits}. Please type it here."
    ),
    TextId.VERIFIED: "Thanks, you're verified for this chat.",
    TextId.CODE_WRONG: "That code doesn't match. {n} tries left.",
    TextId.CODE_EXPIRED: "That code has expired. Codes last 10 minutes.",
    TextId.NOT_VERIFIED: "I can't confirm your account here. A representative will help.",
    TextId.INBOX_CODE_BODY: (
        "Your Meridian Home Comfort verification code is {digits}. It expires in 10 minutes."
    ),
    TextId.INBOX_CODE_GONE: ("This code is no longer shown. Ask the chat for a new code if you need one."),
    # --- promise ---
    TextId.PROMISE_UNSTAFFED: (
        "No representative is online right now. A representative will get back "
        "to you within 1 business day, by {due_label}. Your reference is "
        "{case_ref}."
    ),
    TextId.PROMISE_REFUND: ("A representative will get to your refund request within 2 business days."),
    TextId.PROMISE_REFUND_NO_OUTCOME: "I can't promise an outcome.",
    TextId.PROMISE_STAFFED: (
        "A representative will join this chat when available. You can keep "
        "chatting with me while you wait, if you like."
    ),
    TextId.PROMISE_DANGER_REVIEW: (
        "No representative is online right now, so someone will review this "
        "online request within 1 business day. That is not the wait for "
        "emergency help; for that, please use the emergency line."
    ),
    TextId.PROMISE_SAFETY_NONE: "",
    TextId.REFERENCE_LINE: "Your reference is {case_ref}.",
    # --- fee_change ---
    TextId.FEE_APPLIES: "The {amount} fee applies under current policy.",
    TextId.FEE_ORIGINAL_STAYS: "Your original appointment stays until a representative confirms.",
    TextId.FEE_CANT_GUARANTEE: (
        "I can't promise anyone will confirm a change before your appointment "
        "starts; until a representative confirms, please plan on the "
        "technician arriving {window}."
    ),
    TextId.FEE_PHONE_SUPPORT_OPEN: "Phone support is open until 7:00 pm today if you'd like to call.",
    # --- followup ---
    TextId.FOLLOWUP_LEGEND: "We'll follow up by email unless you'd prefer a phone call.",
    TextId.FOLLOWUP_SAVED_PHONE: "Follow-up saved: phone call, the number ending in {digits}, {window}.",
    TextId.RECORDED_NOT_SENT: "Demo: recorded, not sent",
    # --- booking ---
    TextId.BOOKED: "You're booked. Here are the details.",
    TextId.SLOT_TAKEN: "Sorry, that window just went. Here are the next open ones.",
    TextId.OUT_OF_AREA: (
        "Sorry, that address is outside Meridian's service area, so I can't book a visit there."
    ),
    TextId.NO_WINDOW_FITS: ("That's the earliest I can book. I can't add you to a waitlist from here."),
    TextId.IDENTITY_NEEDED: (
        "Booking changes your account, so I need to confirm it's you before I write it."
    ),
    TextId.CANCELLED_NO_FEE: "There's no fee.",
    TextId.FEE_STANDARD_DIAGNOSTIC: "Standard diagnostic fee: {amount}",
    # The next four are proposal wording (AEA-13 plan section 9, option A; provisional pending the UX session).
    TextId.FEE_DIAGNOSTIC_WAIVED: "Diagnostic fee: waived for Comfort Club members (normally {amount})",
    TextId.FEE_TUNE_UP: "Seasonal tune-up fee: {amount} per system",
    TextId.FEE_TUNE_UP_INCLUDED: (
        "Seasonal tune-up: included with Comfort Club, two per year (normally {amount})"
    ),
    TextId.FEE_ESTIMATE_FREE: "Free in-home estimate with a Comfort Advisor",
    TextId.SLOTS_NOT_HELD: "Windows are shown, not held.",
    TextId.MEMBERS_NOTE: "Members' fees and member-only windows appear after the code.",
    TextId.FREE_CHANGE_NOTE: ("You can change this visit free of charge until 24 hours before the window."),
    TextId.URGENT_NOTE: "Urgent",
    TextId.QUICK_CHECKS_OFFER: ("Before I book, there are a few quick things you can try. They're optional."),
    # --- limits ---
    TextId.TURN_TIMEOUT: "This is taking longer than it should.",
    TextId.BUSY: (
        "A lot of people are chatting right now, so I can't take this message. A person can pick it up."
    ),
    TextId.RATE_LIMITED: "I can't take more messages in this chat right now.",
    TextId.BOOKING_CAP: "I can't make more bookings in this chat.",
    TextId.SPEND_CAP_REACHED: "I can't answer more questions right now. A person can pick this up.",
    TextId.NO_INFORMATION: "I don't have that information.",
    TextId.FAILURE_OFFER: "It sounds like I'm not getting this right. Would you like a person?",
    # --- live ---
    TextId.REP_JOINED: "{rep_name} (demo representative) has joined.",
    TextId.AI_PAUSED: "The assistant is paused while {rep_name} is here.",
    TextId.AI_RESUMED: "{rep_name} handed the chat back to the automated assistant.",
    TextId.CHAT_CLOSED: "{rep_name} closed this chat.",
    TextId.AI_PAUSED_NOTICE: (
        "{rep_name} is in this chat, so the assistant is paused. Your message went to {rep_name}."
    ),
    TextId.PERSON_REQUEST_LABEL: "Talk to a person",
    # --- demo ---
    TextId.SHIFT_ENDED: "The simulated shift ended before a representative joined.",
    TextId.STAFFING_CHANGED_ON_SHIFT: "Staffing changed: simulated staff on shift (demo).",
    TextId.STAFFING_BANNER: "Simulated staffing (demo). No Meridian employee is online.",
    TextId.DEMO_RESET: "The demo was reset, so this chat has ended. Nothing from it was kept.",
    TextId.OVERSIGHT_OVERDUE: "{case_ref} is past its due time. Assign it or pick it up.",
    TextId.OVERSIGHT_SHIFT_ENDED_ONE_WAITING: (
        "Simulated shift ended with 1 customer waiting. Their case now has the 1-business-day promise."
    ),
    TextId.MONITOR_SPEND_CAP: (
        "Spend reached the {amount} daily cap: new chats hand off and no model calls run until tomorrow."
    ),
    TextId.MONITOR_LATENCY: "p95 latency is over 12.5 s per turn: check the model route.",
    TextId.MONITOR_RESTART: "The health check restarted the service: check the logs.",
    TextId.MONITOR_ZERO_TRAFFIC: ("No new live chat for 4 hours: check the public URL and the health check."),
    TextId.MONITOR_FAILURE_RATE: "More than 2% of turns failed: check the model route and the logs.",
    TextId.MONITOR_TRACE_EXPORT: (
        "Trace export is failing and traces are being dropped: check the Langfuse server on the VPS."
    ),
}

TEXTS: Final[Mapping[TextId, str]] = MappingProxyType(_TEXTS)


def _fields_of(text_id: TextId, template: str) -> frozenset[str]:
    names: set[str] = set()
    for _literal, field, spec, conversion in string.Formatter().parse(template):
        if field is None:
            continue
        if not field or field.isdigit() or spec or conversion:
            raise RuntimeError(f"policy/texts.py: bad field in {text_id.value}")
        if field not in PLACEHOLDERS:
            raise RuntimeError(f"policy/texts.py: unknown placeholder {field!r} in {text_id.value}")
        names.add(field)
    return frozenset(names)


if set(_TEXTS) != set(TextId):
    raise RuntimeError("policy/texts.py: TextId members and texts do not match")

_FIELDS: Final[Mapping[TextId, frozenset[str]]] = MappingProxyType(
    {text_id: _fields_of(text_id, template) for text_id, template in _TEXTS.items()}
)

_ID_SHAPE: Final = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")


class TextRenderError(KeyError):
    """A render was refused. Holds names only, never a supplied value."""

    text_id: str
    placeholder: str | None

    def __init__(self, text_id: str, placeholder: str | None, problem: str) -> None:
        self.text_id = text_id
        self.placeholder = placeholder
        super().__init__(f"{problem}: text_id={text_id!r}, placeholder={placeholder!r}")

    def __str__(self) -> str:
        return str(self.args[0])


def render(text_id: TextId, /, **values: str) -> str:
    """Fill a fixed sentence's named placeholders; refuse anything else."""
    if not isinstance(text_id, TextId):
        name = text_id if isinstance(text_id, str) and _ID_SHAPE.match(text_id) else "<not a text id>"
        raise TextRenderError(name, None, "unknown text id") from None
    required = _FIELDS[text_id]
    supplied = set(values)
    if required - supplied:
        raise TextRenderError(text_id.value, min(required - supplied), "missing placeholder") from None
    if supplied - required:
        raise TextRenderError(text_id.value, min(supplied - required), "unexpected placeholder") from None
    for name in sorted(required):
        if not isinstance(values[name], str):
            raise TextRenderError(text_id.value, name, "placeholder value must be a str") from None
    return _TEXTS[text_id].format(**values)


def format_usd(cents: int) -> str:
    """The one money formatter for customer text: "$89", "$12.50", "$1,250"."""
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise TypeError("format_usd: cents must be an int")
    if cents < 0:
        raise ValueError("format_usd: amount must not be negative")
    dollars, rem = divmod(cents, 100)
    if rem == 0:
        return f"${dollars:,}"
    return f"${dollars:,}.{rem:02d}"
