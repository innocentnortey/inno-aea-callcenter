"""Responder and brief wording, the model-facing input types, and the trimmed output schemas (DO-3 4.5, DO-4 9).

Plan AEA-38 PD-1. Pure: no I/O, no clock, no model call.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal

from pydantic import BaseModel

from meridian.domain.actions import ActionKind, CompletedAction, Settled
from meridian.domain.common import MeridianModel, TurnId
from meridian.domain.handoff import BriefExtraction, CaseSummary
from meridian.domain.specialists import (
    AccountResult,
    InvoiceView,
    MembershipView,
    SpecialistResult,
    WarrantyView,
)
from meridian.domain.state import ChatLine, ConversationState
from meridian.domain.turn import ResponderDraft, TurnContext, TurnFacts
from meridian.policy.texts import format_usd
from meridian.ports.models import StructuredRequest
from meridian.privacy.redact import RedactionProfile, redact

__all__ = [
    "BRIEF_RULES",
    "BRIEF_SYSTEM_PREFIX",
    "LABEL_ACCOUNT",
    "LABEL_CHAT",
    "LABEL_LATEST",
    "LABEL_MESSAGES",
    "LABEL_SETTLED",
    "LABEL_THIS_TURN",
    "REQUEST_MAX_TOKENS",
    "RESPONDER_RULES",
    "RESPONDER_SYSTEM_PREFIX",
    "STAFF_ONLY_PREFIX",
    "AccountForModel",
    "DoneItem",
    "FactsForModel",
    "PointForModel",
    "ResponderInput",
    "ResponderRules",
    "SettledForModel",
    "WindowForModel",
    "account_for_model",
    "brief_request",
    "brief_shown",
    "date_label",
    "done_item",
    "facts_for_model",
    "render_responder_dynamic",
    "render_responder_user",
    "responder_input",
    "responder_request",
    "settled_for_model",
    "today_label",
    "trimmed_schema",
    "window_label",
]

LABEL_THIS_TURN: Final = "WHAT HAPPENED THIS TURN"
LABEL_SETTLED: Final = "ALREADY DONE IN THIS CONVERSATION"
LABEL_ACCOUNT: Final = "ACCOUNT (the customer's own records, read this turn)"
LABEL_CHAT: Final = "RECENT CHAT"
LABEL_LATEST: Final = "LATEST CUSTOMER MESSAGE"
LABEL_MESSAGES: Final = "CUSTOMER MESSAGES"
STAFF_ONLY_PREFIX: Final = "internal/"
REQUEST_MAX_TOKENS: Final = 1024  # placeholder: the gateway replaces it with RoleSpec.max_tokens
RESPONDER_RULES: Final[tuple[str, ...]] = (
    "You are Meridian Home Comfort's automated assistant, not a person. Never say or suggest that you are a person.",
    "Write only the words of your reply. Cards, buttons, confirmations, the case reference and any promise about when "
    "a person will reply are added by the system after you. Never write them.",
    "Never write a case reference, a promise of when someone will reply, or a due time.",
    "Never say that the customer was charged, refunded or credited, or that money is owed to them.",
    "Never say that something is done, booked, moved, cancelled, sent, saved or verified unless it is listed under "
    "ALREADY DONE IN THIS CONVERSATION.",
    "Use only the numbers, prices, dates, times and IDs shown under WHAT HAPPENED THIS TURN, ALREADY DONE IN THIS "
    "CONVERSATION or ACCOUNT. Never add a price or fee that is not shown there.",
    "Explain amounts exactly as billed. Never say a bill is wrong.",
    "When an invoice line and a document give different amounts for the same fee, give only the invoice amount and do "
    "not mention the document's amount.",
    "If WHAT HAPPENED THIS TURN says no source answers part of the question, say you don't have that information. "
    "Do not guess.",
    "If a person was offered or will follow up, say so briefly, with no time and no reference.",
    "Write plain, short sentences. Write times in 12-hour form, such as 8:00 am. Stay under 1200 characters.",
)
BRIEF_RULES: Final[tuple[str, ...]] = (
    "You prepare notes for a Meridian Home Comfort staff member who will take over this conversation.",
    "needs: one or two quotes of what the customer is asking for. Copy each quote exactly, character for character, "
    "from one customer message, and give that message's id.",
    "claims: up to five quotes of things the customer says happened that nobody has checked. Copy each exactly and "
    "give its message id.",
    "open_decision: one sentence naming what the staff member must decide. Use no number, date, price or ID unless it "
    "appears in the customer messages.",
    "Never invent, shorten or reword a quote.",
)

# ---------------------------------------------------------------------------
# Pure formatters
# ---------------------------------------------------------------------------


def _drop_titles(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_titles(v) for k, v in value.items() if k != "title"}
    if isinstance(value, list):
        return [_drop_titles(v) for v in value]
    return value


def trimmed_schema(model: type[BaseModel]) -> str:
    """The model's JSON schema without `title` keys, as deterministic compact JSON."""
    return json.dumps(_drop_titles(model.model_json_schema()), sort_keys=True, separators=(",", ":"))


def date_label(day: dt.date) -> str:
    return f"{day:%A}, {day:%B} {day.day}"


def today_label(now: dt.datetime) -> str:
    return f"{now:%A}, {now:%B} {now.day}, {now.year}"


def _twelve_hour(hour: int, minute: str) -> str:
    if hour == 0:
        return f"12:{minute} am"
    if hour < 12:
        return f"{hour}:{minute} am"
    if hour == 12:
        return f"12:{minute} pm"
    return f"{hour - 12}:{minute} pm"


def window_label(window: str) -> str | None:
    m = re.fullmatch(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})", window)
    if m is None:
        return None
    return f"{_twelve_hour(int(m[1]), m[2])} to {_twelve_hour(int(m[3]), m[4])}"


def _iso_date_label(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return date_label(dt.date.fromisoformat(value))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Model-facing types
# ---------------------------------------------------------------------------


class DoneItem(MeridianModel):
    """One stored action, without ids, references, customer ids or fee lines."""

    kind: ActionKind
    when: Literal["this_turn", "earlier"]
    date_label: str | None = None
    window_label: str | None = None
    technician: str | None = None
    service_type: str | None = None
    change: str | None = None
    wanted_text: str | None = None


class PointForModel(MeridianModel):
    text: str
    source: str


class WindowForModel(MeridianModel):
    date_label: str
    window_label: str
    technician: str


class FactsForModel(MeridianModel):
    plan_mode: Literal["talk", "act"] | None
    points: tuple[PointForModel, ...]
    no_source: bool
    windows_shown: tuple[WindowForModel, ...]
    done_this_turn: tuple[DoneItem, ...]
    change_wanted: str | None
    handed_to_person: bool
    handoff_reason: str | None
    person_offered: bool
    identity_step: str | None
    quick_checks_offered: bool


class SettledForModel(MeridianModel):
    done: tuple[DoneItem, ...]
    case_open: bool


class AccountForModel(MeridianModel):
    invoices: tuple[InvoiceView, ...]
    membership: MembershipView | None
    warranty: WarrantyView | None


class ResponderRules(MeridianModel):
    lines: tuple[str, ...]


class ResponderInput(MeridianModel):
    chat_window: tuple[ChatLine, ...]
    latest_message: str
    this_turn: FactsForModel
    account: AccountForModel | None
    settled: SettledForModel
    identity_status: str
    today_label: str
    rules: ResponderRules


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def done_item(action: CompletedAction, turn_id: TurnId) -> DoneItem:
    when: Literal["this_turn", "earlier"] = "this_turn" if action.key.turn_id == turn_id else "earlier"
    src = (action.before or action.after) if action.kind is ActionKind.CANCELLED else action.after
    if src is None:
        return DoneItem(kind=action.kind, when=when)
    is_change = action.kind is ActionKind.CHANGE_REQUEST_SENT
    return DoneItem(
        kind=action.kind,
        when=when,
        date_label=_iso_date_label(src.get("date")),
        window_label=window_label(src["window"]) if "window" in src else None,
        technician=src.get("technician"),
        service_type=src.get("service_type"),
        change=src.get("change") if is_change else None,
        wanted_text=src.get("wanted_text") if is_change else None,
    )


def settled_for_model(settled: Settled, turn_id: TurnId) -> SettledForModel:
    return SettledForModel(
        done=tuple(done_item(a, turn_id) for a in settled.actions),
        case_open=settled.open_case is not None,
    )


def facts_for_model(facts: TurnFacts) -> FactsForModel:
    by_id = {p.passage_id: p for p in facts.passages}
    points: list[PointForModel] = []
    for pt in facts.points:
        passage = by_id.get(pt.passage_id)
        if str(pt.passage_id).startswith(STAFF_ONLY_PREFIX):
            continue
        if passage is not None and passage.file.startswith(STAFF_ONLY_PREFIX):
            continue
        source = f"{passage.file}, {passage.version_label}" if passage is not None else str(pt.passage_id)
        points.append(PointForModel(text=pt.text, source=source))
    return FactsForModel(
        plan_mode=facts.plan_mode,
        points=tuple(points),
        no_source=bool(facts.no_source_tasks),
        windows_shown=tuple(
            WindowForModel(
                date_label=date_label(s.date),
                window_label=window_label(s.window) or s.window,
                technician=s.technician,
            )
            for s in facts.windows_shown
        ),
        done_this_turn=tuple(done_item(a, facts.turn_id) for a in facts.writes_this_turn),
        change_wanted=facts.change_request.wanted_text if facts.change_request else None,
        handed_to_person=facts.handoff is not None,
        handoff_reason=facts.handoff.case.reason.value if facts.handoff else None,
        person_offered=facts.escalation is not None and facts.escalation.outcome == "offer",
        identity_step=facts.identity_step.kind if facts.identity_step is not None else None,
        quick_checks_offered=bool(facts.quick_checks),
    )


def account_for_model(results: Sequence[SpecialistResult]) -> AccountForModel | None:
    for r in results:
        if isinstance(r, AccountResult) and r.status == "read":
            return AccountForModel(invoices=r.invoices, membership=r.membership, warranty=r.warranty)
    return None


def responder_input(state: ConversationState, ctx: TurnContext) -> ResponderInput:
    if state.facts is None or state.settled is None:
        raise RuntimeError("responder input needs facts and settled")
    return ResponderInput(
        chat_window=tuple(
            line.model_copy(update={"text": redact(line.text, RedactionProfile.SONNET).text})
            for line in state.chat_window
        ),
        latest_message=redact(state.turn_input.text_store, RedactionProfile.SONNET).text,
        this_turn=facts_for_model(state.facts),
        account=account_for_model(state.specialist_results),
        settled=settled_for_model(state.settled, ctx.ids.turn_id),
        identity_status=state.identity.status,
        today_label=today_label(ctx.now),
        rules=ResponderRules(lines=RESPONDER_RULES),
    )


RESPONDER_SYSTEM_PREFIX: Final[str] = (
    "\n".join(RESPONDER_RULES)
    + "\n\nOUTPUT: one JSON object matching this schema: "
    + trimmed_schema(ResponderDraft)
)


def _done_line(item: DoneItem) -> str:
    parts = [
        item.date_label,
        item.window_label,
        f"with {item.technician}" if item.technician is not None else None,
        item.service_type,
        f"change: {item.change}" if item.change is not None else None,
        f"wanted: {item.wanted_text}" if item.wanted_text is not None else None,
    ]
    kept = [p for p in parts if p is not None]
    head = f"- {item.kind.value}: {', '.join(kept)}" if kept else f"- {item.kind.value}"
    return head + (" (this turn)" if item.when == "this_turn" else " (earlier turn)")


def _turn_lines(t: FactsForModel) -> list[str]:
    lines: list[str] = []
    if t.points:
        lines.append("Answer points:")
        lines.extend(f"- {p.text} [source: {p.source}]" for p in t.points)
    if t.no_source:
        lines.append("No source answers part of the question: yes")
    if t.windows_shown:
        lines.append("Windows shown:")
        lines.extend(f"- {w.date_label}, {w.window_label}, with {w.technician}" for w in t.windows_shown)
    if t.done_this_turn:
        lines.append("Done this turn:")
        lines.extend(_done_line(i) for i in t.done_this_turn)
    if t.change_wanted is not None:
        lines.append(f"Change request for a person: {t.change_wanted}")
    if t.handed_to_person:
        lines.append(f"Handed to a person: yes (reason: {t.handoff_reason})")
    if t.person_offered:
        lines.append("A person was offered: yes")
    if t.identity_step is not None:
        lines.append(f"Identity step: {t.identity_step}")
    if t.quick_checks_offered:
        lines.append("Quick checks offered: yes")
    return lines or ["Nothing else happened this turn."]


def _account_lines(a: AccountForModel) -> list[str]:
    lines = ["", f"{LABEL_ACCOUNT}:"]
    for inv in a.invoices:
        lines.append(
            f"- Invoice {inv.invoice_id}: issued {date_label(inv.issued_on)}, due {date_label(inv.due_on)}, "
            f"total {format_usd(inv.total_cents)}, balance {format_usd(inv.balance_cents)}, "
            f"{'paid' if inv.paid else 'unpaid'}"
        )
        lines.extend(f"  - {line.description}: {format_usd(line.amount_cents)}" for line in inv.lines)
    if a.membership is not None:
        m = a.membership
        renews = f"renews {date_label(m.renewal_date)}" if m.renewal_date else "renewal date not on record"
        lines.append(f"- Membership: {m.tier}, {renews}")
    if a.warranty is not None:
        w = a.warranty
        brand = f", {w.equipment_brand}" if w.equipment_brand else ""
        lines.append(f"- Warranty: installed {date_label(w.install_date)}{brand}: {w.sentence}")
    return lines


def render_responder_dynamic(inp: ResponderInput) -> str:
    lines = [f"TODAY: {inp.today_label}", f"IDENTITY: {inp.identity_status}", "", f"{LABEL_SETTLED}:"]
    lines.extend(_done_line(i) for i in inp.settled.done) if inp.settled.done else lines.append(
        "- nothing yet"
    )
    if inp.settled.case_open:
        lines.append("A person has this conversation's case: yes")
    lines.extend(["", f"{LABEL_THIS_TURN}:", f"Mode: {inp.this_turn.plan_mode or 'none'}"])
    lines.extend(_turn_lines(inp.this_turn))
    if inp.account is not None:
        lines.extend(_account_lines(inp.account))
    return "\n".join(lines)


def render_responder_user(inp: ResponderInput) -> str:
    lines = [f"{LABEL_CHAT}:"]
    lines.extend(
        f"{line.speaker}: {line.text}" for line in inp.chat_window
    ) if inp.chat_window else lines.append("(none)")
    lines.extend(["", f"{LABEL_LATEST}:", inp.latest_message])
    return "\n".join(lines)


def responder_request(inp: ResponderInput) -> StructuredRequest[ResponderDraft]:
    return StructuredRequest[ResponderDraft](
        system_prefix=RESPONDER_SYSTEM_PREFIX,
        system_dynamic=render_responder_dynamic(inp),
        user=render_responder_user(inp),
        output_model=ResponderDraft,
        max_tokens=REQUEST_MAX_TOKENS,
        effort=None,
    )


def brief_shown(customer_lines: Sequence[tuple[int, str]], line_chars: int) -> dict[int, str]:
    """The exact customer text the extraction model is shown (PD-7): redacted, cut to `line_chars`."""
    out: dict[int, str] = {}
    for message_id, text in customer_lines:
        t = redact(text, RedactionProfile.SONNET).text
        if len(t) > line_chars:
            t = t[: line_chars - 1] + "…"
        out[message_id] = t
    return out


BRIEF_SYSTEM_PREFIX: Final[str] = (
    "\n".join(BRIEF_RULES)
    + "\n\nOUTPUT: one JSON object matching this schema: "
    + trimmed_schema(BriefExtraction)
)


def brief_request(case: CaseSummary, shown: Mapping[int, str]) -> StructuredRequest[BriefExtraction]:
    return StructuredRequest[BriefExtraction](
        system_prefix=BRIEF_SYSTEM_PREFIX,
        system_dynamic=f"CASE REASON: {case.reason.value}\nPRIORITY: {case.priority.value}",
        user=f"{LABEL_MESSAGES}:\n" + "\n".join(f"[message {mid}] {text}" for mid, text in shown.items()),
        output_model=BriefExtraction,
        max_tokens=REQUEST_MAX_TOKENS,
        effort=None,
    )
