"""Planner and danger-classifier wording and choice fields (A7d, AEA-37).

SP-1's measured text, extended only by the DO-4 section 4 fields and the planner's late_technician option.
The caller passes already-redacted text; this module does no redaction and no I/O.
"""

from __future__ import annotations

from typing import Final

from meridian.domain.turn import PlannerInput
from meridian.ports.models import ChoiceField, ChoiceRequest

__all__ = [
    "CLASSIFIER_FIELDS",
    "CLASSIFIER_SYSTEM",
    "DANGER_FIELD",
    "PLANNER_FIELDS",
    "PLANNER_SYSTEM",
    "classifier_request",
    "planner_request",
]

DANGER_FIELD: Final = "danger_level"

PLANNER_SYSTEM: Final[str] = (
    "You are the planner for Meridian Home Comfort's customer chat (heating, cooling and plumbing in Austin, "
    "Texas). You never write to the customer. Read STATE: the recent chat, any open task and the customer's "
    "latest message. For each field choose the one option that fits the customer's latest message, using the "
    'open task and recent chat to understand short replies. Choose "none" or "no" when the message does not '
    "need that kind of help. Private account details and any booking or change need the account or scheduling "
    "fields; public company questions need knowledge."
)

PLANNER_FIELDS: Final[tuple[ChoiceField, ...]] = (
    ChoiceField(
        name="knowledge",
        instructions=(
            "Does the latest message ask about Meridian's public information: membership plans, prices, fees, "
            "warranty, hours, service area, services or policies?"
        ),
        options={
            "no": "No company information is needed to answer.",
            "yes": "The answer needs Meridian's knowledge base.",
        },
    ),
    ChoiceField(
        name="account",
        instructions="Does the customer need their own account records read?",
        options={
            "none": "No private record is needed.",
            "invoice": "Their invoice or bill: what a charge is for, the balance, the due date.",
            "membership": "Their own membership: tier, renewal date, cancelling it or stopping its renewal.",
            "appointments": "Their existing appointments, without changing them.",
            "warranty": "Their own equipment's warranty: when it was installed or how long its warranty lasts.",
        },
    ),
    ChoiceField(
        name="scheduling",
        instructions="Does the customer want to book a new visit or change an existing one?",
        options={
            "none": "No booking or change is requested.",
            "book_new": "Book a new service visit, including picking a time the assistant offered for a new visit.",
            "reschedule": (
                "Move an existing appointment to another time, including confirming a new time the assistant "
                "offered."
            ),
            "cancel": "Cancel an existing appointment.",
            "confirm": (
                "Check that an existing appointment is still on, or its date, time or technician, without "
                "changing it."
            ),
        },
    ),
    ChoiceField(
        name="handoff",
        instructions="Does the message ask for something that must go to a staff member?",
        options={
            "none": "Nothing for staff.",
            "refund": "Asks for money back.",
            "billing_dispute": "Says a charge is wrong or disputes it.",
            "membership_cancel": "Wants to cancel a membership or stop it renewing.",
            "unsupported_other": (
                "Asks the chat to send, email or change something it cannot, such as a copy of a document, a "
                "payment link or autopay."
            ),
            "complaint_or_manager": (
                "Complains about staff or work, asks for a manager, or mentions legal action or a chargeback."
            ),
            "late_technician": "Says a technician is late, has not arrived in the booked window, or missed the visit.",
        },
    ),
    ChoiceField(
        name="topic",
        instructions="Which subject is the latest message mainly about?",
        options={
            "booking": (
                "Booking, moving, cancelling or checking a service visit, or a problem at home that needs a visit."
            ),
            "membership": "The Comfort Club membership: what it includes, its price, renewal or cancelling it.",
            "billing": "An invoice, a charge, a payment, a refund or a fee.",
            "warranty": "A warranty: what it covers or how long it lasts.",
            "other": "Anything else, including a greeting or a short reply with no subject of its own.",
        },
    ),
)

CLASSIFIER_SYSTEM: Final[str] = (
    'You check one customer message sent to a home heating, cooling and plumbing company. Choose "normal" '
    "unless the message itself says or clearly implies someone is in danger or there is an unexplained burning "
    "smell. You never reply to the customer."
)

CLASSIFIER_FIELDS: Final[tuple[ChoiceField, ...]] = (
    ChoiceField(
        name=DANGER_FIELD,
        instructions=(
            "Is anyone in danger because of conditions in the home, or is there a burning smell whose cause is "
            "unclear?"
        ),
        options={
            "normal": (
                "No one is said to be at risk: an ordinary comfort or service problem, such as an AC not cooling "
                "or a question about a bill."
            ),
            "burning_unclear": "Mentions a burning or electrical smell without saying whether a breaker tripped.",
            "danger": (
                "Says or clearly implies a person is at risk because of the conditions, for example an elderly "
                "person, a baby or someone unwell in a very hot or very cold home, or water near electrics."
            ),
        },
    ),
)


def planner_request(planner_input: PlannerInput) -> ChoiceRequest:
    """The one planner request: system and fields are constants (identical every turn); state is PlannerInput."""
    return ChoiceRequest(
        system=PLANNER_SYSTEM, state=planner_input.model_dump(mode="json"), fields=PLANNER_FIELDS
    )


def classifier_request(latest_message: str) -> ChoiceRequest:
    """The classifier sees the latest message only (SP-1 shape)."""
    return ChoiceRequest(
        system=CLASSIFIER_SYSTEM, state={"latest_message": latest_message}, fields=CLASSIFIER_FIELDS
    )
