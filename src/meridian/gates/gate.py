"""Intake parsing and the gate decision: which turns never reach a model.

Pure code (DO-3 section 2.1): no I/O, no logging, no clock. The order of the
decision follows stage7/graph-core.md section 3.
"""

from __future__ import annotations

import re
from typing import Final, Literal

from meridian.domain.common import TurnId
from meridian.domain.state import ConversationState
from meridian.domain.turn import (
    CardChoice,
    ChoicePayload,
    CodePayload,
    FormPayload,
    FormValues,
    GateDecision,
    GateFlags,
    GateKind,
    Intake,
    TextPayload,
    TurnPayload,
)
from meridian.gates.rules import match_rules
from meridian.privacy.redact import Redacted, RedactionKind, RedactionProfile, redact

CODE_ENTERED: Final = "[code entered]"
DETAILS_SUBMITTED: Final = "[details submitted]"

# GRC-3, decided option A by D-14 (stage7-signoff): safety is checked before
# "AI paused", as one tuple so the order is data, not control flow.
GATE_ORDER_HEAD: tuple[GateKind, GateKind] = (GateKind.SAFETY, GateKind.AI_PAUSED)

_MAX_CARD_ID_CHARS: Final = 128
_CARD_ID_CHARS: Final = re.compile(r"[A-Za-z0-9._-]+")
_TASK_CARD: Final = re.compile(r"(?P<task>.+)\.(?P<n>[0-9]+)")
_PREFIXES: Final[tuple[tuple[str, Literal["burning", "code", "locate"]], ...]] = (
    ("burn-", "burning"),
    ("code-", "code"),
    ("locate-", "locate"),
)
CardTarget = tuple[Literal["burning", "code", "locate", "task", "unknown"], str | None]


def card_target(card_id: str) -> CardTarget:
    """Classify an untrusted card id; never raises, never trusts it."""
    if len(card_id) > _MAX_CARD_ID_CHARS or _CARD_ID_CHARS.fullmatch(card_id) is None:
        return ("unknown", None)
    for prefix, kind in _PREFIXES:
        if card_id.startswith(prefix):
            return (kind, None) if len(card_id) > len(prefix) else ("unknown", None)
    m = _TASK_CARD.fullmatch(card_id)
    if m:
        return ("task", m.group("task"))
    return ("unknown", None)


def burning_card_id(turn_id: TurnId) -> str:
    return f"burn-{turn_id}"


def flags_from_state(state: ConversationState) -> GateFlags:
    return GateFlags(
        ai_paused=state.controller.kind == "human",
        burning_card_id=state.burning_card_id,
        code_card_open=state.identity.status == "code_sent",
        open_task_ids=tuple(t.task_id for t in state.open_tasks if t.status != "done"),
    )


def _card_seen(r: Redacted) -> bool:
    return r.replaced.get(RedactionKind.CARD, 0) > 0


def _store_card_id(card_id: str) -> tuple[str, bool]:
    """Known-shape ids are kept verbatim; an unknown id is STORE-redacted."""
    if card_target(card_id)[0] != "unknown":
        return card_id, False
    r = redact(card_id, RedactionProfile.STORE)
    return r.text, _card_seen(r)


def _is_where_form(v: FormValues) -> bool:
    return (
        bool(v.zip_or_city)
        and v.name is None
        and v.phone is None
        and v.customer_id is None
        and v.invoice_number is None
    )


def parse_intake(payload: TurnPayload) -> Intake:
    """Turn a payload into an Intake before anything stores the text."""
    if isinstance(payload, TextPayload):
        r = redact(payload.text, RedactionProfile.STORE)
        return Intake(
            kind="text",
            text_store=r.text,
            code_digits=None,
            form=None,
            card_number_seen=_card_seen(r),
            choice=None,
            card_id=None,
        )
    card_id, id_card_seen = _store_card_id(payload.card_id)
    target_kind = card_target(card_id)[0]
    if isinstance(payload, ChoicePayload):
        r = redact(payload.option, RedactionProfile.STORE)
        return Intake(
            kind="choice",
            text_store=r.text,
            code_digits=None,
            form=None,
            card_number_seen=id_card_seen or _card_seen(r),
            choice=CardChoice(card_id=card_id, option=r.text),
            card_id=card_id,
        )
    if isinstance(payload, CodePayload):
        return Intake(
            kind="code",
            text_store=CODE_ENTERED,
            code_digits=payload.code,
            form=None,
            card_number_seen=id_card_seen,
            choice=None,
            card_id=card_id,
        )
    if not isinstance(payload, FormPayload):
        raise TypeError(f"parse_intake: unsupported payload type {type(payload).__name__}")
    v = payload.values
    text_store = DETAILS_SUBMITTED
    form: FormValues | None = None
    seen = id_card_seen
    if target_kind == "locate":
        form = v
    elif target_kind == "task":
        form = v
        if _is_where_form(v):
            zc = v.zip_or_city or ""
            r = redact(zc, RedactionProfile.STORE)
            text_store = r.text or DETAILS_SUBMITTED
            seen = id_card_seen or _card_seen(r)
    return Intake(
        kind="form",
        text_store=text_store,
        code_digits=None,
        form=form,
        card_number_seen=seen,
        choice=None,
        card_id=card_id,
    )


def _burning_answer(option: str) -> Literal["yes", "no", "unsure"]:
    match option:
        case "yes":
            return "yes"
        case "no":
            return "no"
        case _:
            return "unsure"


def decide_gate(intake: Intake, flags: GateFlags) -> GateDecision:
    """Return the first gate that applies (graph-core section 3)."""
    rules = match_rules(intake.text_store)
    target_kind, task_id = card_target(intake.card_id) if intake.card_id is not None else ("unknown", None)

    for head in GATE_ORDER_HEAD:
        if head is GateKind.SAFETY and rules.safety is not None:
            return GateDecision(kind=GateKind.SAFETY, rules=rules)
        if head is GateKind.AI_PAUSED and flags.ai_paused:
            return GateDecision(kind=GateKind.AI_PAUSED, rules=rules)

    if intake.kind == "choice" and intake.choice is not None and target_kind == "burning":
        return GateDecision(
            kind=GateKind.BURNING_ANSWER,
            rules=rules,
            burning_answer=_burning_answer(intake.choice.option),
        )
    if rules.burning_unclear:
        return GateDecision(kind=GateKind.BURNING_ASK, rules=rules)
    if rules.danger_words:
        return GateDecision(kind=GateKind.DANGER_RULE, rules=rules)
    if rules.person:
        return GateDecision(kind=GateKind.PERSON, rules=rules)
    if intake.kind == "text" and flags.burning_card_id is not None:
        return GateDecision(kind=GateKind.BURNING_ANSWER, rules=rules, burning_answer="unsure")
    if intake.kind == "code" or (intake.kind == "choice" and target_kind == "code" and flags.code_card_open):
        return GateDecision(kind=GateKind.CODE_ENTRY, rules=rules)
    if intake.kind == "form" and target_kind == "locate":
        return GateDecision(kind=GateKind.LOCATE, rules=rules)
    if (
        intake.kind in ("choice", "form")
        and target_kind == "task"
        and task_id is not None
        and task_id in flags.open_task_ids
    ):
        return GateDecision(kind=GateKind.CARD_CHOICE, rules=rules, resume_task_id=task_id)
    return GateDecision(kind=GateKind.FREE_TEXT, rules=rules)
