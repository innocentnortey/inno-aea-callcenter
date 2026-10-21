"""Specialist wording (AEA-35; DO-3 S-14; graph-tools §2).

Each `render_*` returns `(system_prefix, system_dynamic, user)`: a stable, cache-controlled prefix that never changes
between turns, a per-run line with today's demo-clock date, and the task text. Starts from SP-1's measured wording
(build step 8).
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Final
from zoneinfo import ZoneInfo

from pydantic.main import IncEx

from meridian.domain.tools import SpecialistTask
from meridian.domain.turn import TaskIntent, TurnContext
from meridian.privacy.redact import RedactionProfile, redact

REPORT_FACTS_TOOL: Final = "report_facts"
REPORT_FACTS_DESCRIPTION: Final = (
    "Report what your tools returned, then stop. Call it exactly once, after your other tools. "
    "Use only values the tools returned for this task; leave out anything they did not return."
)

RULE_NEVER_TALK: Final = "You never talk to the customer; another step writes the reply."
RULE_USE_TOOLS: Final = "Use your tools, then call report_facts exactly once with what you found."
RULE_REPORT_ONLY: Final = "Report only what the tools returned; never guess."
RULE_NO_FIRM_PRICES: Final = (
    "Never state a firm price for a repair; the technician confirms pricing on site. "
    "Published fees and membership prices may be reported exactly as a tool returned them."
)
RULE_NO_CARDS: Final = "Never ask for or accept a card number; payments are never taken in chat."
RULE_MASKED: Final = (
    "Text in square brackets, such as [code] or [email], was hidden before you saw it; "
    "never ask for the hidden value."
)

KNOWLEDGE_RULES: Final = (
    "Call kb_search with a short query for each question in the task, at most 2 searches. "
    "Report up to 5 points that answer the task. Copy each point closely from one passage and give that "
    "passage's passage_id exactly as kb_search returned it. "
    "If the passages do not answer the task, report answered=false and no points. "
    "When you report the Comfort Club monthly price, also report its 12-month minimum."
)
ACCOUNT_RULES: Final = (
    "Call the read tool that matches the task once: read_invoices, read_membership or read_warranty. "
    "Then call report_facts with a one-sentence summary. "
    "Report invoice amounts exactly as billed. Never judge whether a charge is right, never say a charge is wrong "
    "or that money is owed back, and never compare a bill with a price list; a person reviews any question about "
    "a charge."
)
SCHEDULING_RULES: Final = (
    "Service types: hvac_repair (repairs; AC or heat not working), hvac_tune_up, plumbing, estimate "
    "(new system quotes). Windows: 08:00-12:00, 12:00-16:00, 13:00-17:00, and 16:00-19:00 on Tuesday and "
    "Thursday only. "
    "For a new booking: search for open windows that match the customer's wanted days and times; book only a "
    "slot in STATE.shown_slots that the customer has picked. "
    "For a change to an existing visit: STATE.appointments lists the customer's visits; choose the one they mean. "
    "A move or cancel within 24 hours of the visit's window start carries the late-change fee: never move or "
    "cancel that visit. You may search for windows to show, then record a change request with the customer's "
    "wanted time in their own words. "
    "Otherwise move a visit only to a slot in STATE.shown_slots that the customer has picked, and cancel only "
    "when the customer has asked to cancel. "
    "Code refuses any booking or move to a slot not yet shown to the customer and any move or cancel that "
    "carries the fee; when a tool refuses, do not repeat the same call. "
    "In report_facts give appointment_id (0 if none), wanted_time (the customer's words, or an empty string) "
    "and a one-line note."
)


def _prefix(kind: str, rules: str) -> str:
    return "\n".join(
        (
            f"You are the {kind} specialist inside Meridian Home Comfort's chat system.",
            RULE_NEVER_TALK,
            RULE_USE_TOOLS,
            RULE_REPORT_ONLY,
            RULE_NO_FIRM_PRICES,
            RULE_NO_CARDS,
            RULE_MASKED,
            "",
            rules,
        )
    )


KNOWLEDGE_PREFIX: Final = _prefix("knowledge", KNOWLEDGE_RULES)
ACCOUNT_PREFIX: Final = _prefix("account", ACCOUNT_RULES)
SCHEDULING_PREFIX: Final = _prefix("scheduling", SCHEDULING_RULES)

TASK_LABELS: Final = MappingProxyType(
    {
        TaskIntent.ANSWER_QUESTION: "answer the customer's question from the knowledge base",
        TaskIntent.READ_INVOICE: "read the customer's invoices",
        TaskIntent.READ_MEMBERSHIP: "read the customer's membership",
        TaskIntent.READ_APPOINTMENTS: "read the customer's appointments",
        TaskIntent.READ_WARRANTY: "read the customer's warranty",
        TaskIntent.BOOK_NEW: "book a new visit",
        TaskIntent.RESCHEDULE: "move an existing visit",
        TaskIntent.CANCEL: "cancel an existing visit",
        TaskIntent.CONFIRM: "confirm an existing visit",
    }
)

MAX_TASK_MESSAGES: Final = 6  # [A] per-turn budget (context-management rule 4); replaced by the E-1 run
MAX_MESSAGE_CHARS: Final = 1_000  # [A] each task message cut to this with "…"
_SCHEDULING_STATE_EXCLUDE: Final[IncEx] = {"shown_slots": {"__all__": {"shown_turn"}}}  # PD-16: no turn id
_CHICAGO: Final = ZoneInfo("America/Chicago")


def _dynamic(ctx: TurnContext) -> str:
    now = ctx.now.astimezone(_CHICAGO)
    return f"Today is {now:%A}, {now:%B} {now.day}, {now.year}, {now:%H:%M} (America/Chicago)."


def _user(task: SpecialistTask, *, exclude: IncEx | None = None) -> str:
    messages = list(task.task_messages[-MAX_TASK_MESSAGES:])
    if not messages or messages[-1] != task.customer_text:
        messages.append(task.customer_text)
        messages = messages[-MAX_TASK_MESSAGES:]
    cut = [m if len(m) <= MAX_MESSAGE_CHARS else m[: MAX_MESSAGE_CHARS - 1] + "…" for m in messages]
    state = json.dumps(
        task.slice.model_dump(mode="json", exclude=exclude), ensure_ascii=False, sort_keys=True, indent=1
    )
    lines = [
        f"TASK: {TASK_LABELS[task.task.intent]}",
        "CUSTOMER MESSAGES FOR THIS TASK (oldest first):",
        *(f"- {m}" for m in cut),
        "STATE (JSON):",
        state,
    ]
    return redact("\n".join(lines), RedactionProfile.SONNET).text


def render_knowledge(task: SpecialistTask, ctx: TurnContext) -> tuple[str, str, str]:
    return KNOWLEDGE_PREFIX, _dynamic(ctx), _user(task)


def render_account(task: SpecialistTask, ctx: TurnContext) -> tuple[str, str, str]:
    return ACCOUNT_PREFIX, _dynamic(ctx), _user(task)


def render_scheduling(task: SpecialistTask, ctx: TurnContext) -> tuple[str, str, str]:
    return SCHEDULING_PREFIX, _dynamic(ctx), _user(task, exclude=_SCHEDULING_STATE_EXCLUDE)
