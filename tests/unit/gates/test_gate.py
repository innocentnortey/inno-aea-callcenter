"""Frozen tests for AEA-12: intake parsing and the gate decision (meridian.gates.gate).

Written from the acceptance criteria and plan section 7.1 before the module exists. Every test takes the
``g`` fixture, which imports the module at call time, so the file collects now and each test is red with
ModuleNotFoundError until gate.py lands. All secrets are generated at run time; none is a literal.
"""

from __future__ import annotations

import ast
import importlib
import logging
import secrets
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

from meridian.domain.common import TurnId
from meridian.domain.handoff import HandoffReason
from meridian.domain.state import Controller, ConversationState, IdentityState, OpenTask
from meridian.domain.turn import (
    ChoicePayload,
    CodePayload,
    FormPayload,
    FormValues,
    GateDecision,
    GateFlags,
    GateKind,
    Intake,
    SafetyKind,
    TextPayload,
)

WP5 = "My carbon monoxide detector is going off."
WP6 = "I need to schedule a service call. I smell something burning from the vents."
PERSON = "can I talk to a person"


@pytest.fixture
def g() -> ModuleType:
    return importlib.import_module("meridian.gates.gate")


def _flags(
    *,
    paused: bool = False,
    burning: str | None = None,
    code_open: bool = False,
    tasks: tuple[str, ...] | list[str] = (),
) -> GateFlags:
    return GateFlags(
        ai_paused=paused,
        burning_card_id=burning,
        code_card_open=code_open,
        open_task_ids=tuple(tasks),
    )


def _text(t: str) -> TextPayload:
    return TextPayload(text=t)


def _choice(card_id: str, option: str) -> ChoicePayload:
    return ChoicePayload(card_id=card_id, option=option)


def _code_payload(card_id: str, digits: str) -> CodePayload:
    return CodePayload(card_id=card_id, code=SecretStr(digits))


def _form(card_id: str, **values: Any) -> FormPayload:
    return FormPayload(card_id=card_id, values=FormValues(**values))


def _code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(6))


def _card() -> str:
    digits = "4" + "".join(str(secrets.randbelow(10)) for _ in range(15))
    return " ".join(digits[i : i + 4] for i in range(0, 16, 4))


def _phone() -> str:
    return f"512-555-01{secrets.randbelow(100):02d}"


def _turn_id() -> TurnId:
    return TurnId(str(uuid.uuid4()))


def _decide(g: ModuleType, payload: Any, flags: GateFlags | None = None) -> tuple[Intake, GateDecision]:
    i = g.parse_intake(payload)
    d = g.decide_gate(i, flags or _flags())
    return i, d


def _state(
    *,
    controller_kind: str = "ai",
    burning: str | None = None,
    identity_status: str = "not_checked",
    tasks: tuple[tuple[str, str], ...] | list[tuple[str, str]] = (),
) -> ConversationState:
    construct_state: Any = ConversationState.model_construct
    construct_identity: Any = IdentityState.model_construct
    construct_task: Any = OpenTask.model_construct
    result: ConversationState = construct_state(
        controller=Controller(kind=controller_kind),
        identity=construct_identity(status=identity_status),
        open_tasks=[construct_task(task_id=tid, status=st) for tid, st in tasks],
        burning_card_id=burning,
    )
    return result


# --- AC-1 -------------------------------------------------------------------------------------------------

_ORDERS = [
    pytest.param((GateKind.SAFETY, GateKind.AI_PAUSED), id="option_a"),
    pytest.param((GateKind.AI_PAUSED, GateKind.SAFETY), id="option_b"),
]

# (case number, text, flags kwargs, expected under A, expected under B)
_ORDER_CASES: list[tuple[int, str, dict[str, Any], GateKind, GateKind]] = [
    (1, WP5, {"paused": True}, GateKind.SAFETY, GateKind.AI_PAUSED),
    (2, "co alarm keeps going off, can I talk to a person", {}, GateKind.SAFETY, GateKind.SAFETY),
    (3, "I smell something burning, can I talk to a person", {}, GateKind.BURNING_ASK, GateKind.BURNING_ASK),
    (4, "My son can't breathe, can I talk to a person", {}, GateKind.DANGER_RULE, GateKind.DANGER_RULE),
    (5, PERSON, {"code_open": True}, GateKind.PERSON, GateKind.PERSON),
    (6, PERSON, {"paused": True}, GateKind.AI_PAUSED, GateKind.AI_PAUSED),
    (7, "I smell something burning", {"paused": True}, GateKind.AI_PAUSED, GateKind.AI_PAUSED),
]


@pytest.mark.parametrize("order", _ORDERS)
def test_order_first_match_wins(
    g: ModuleType, order: tuple[GateKind, GateKind], monkeypatch: pytest.MonkeyPatch
) -> None:
    """invariant: AC-1 earliest step wins; steps 1-2 are one tuple (GRC-3 option A by default)."""
    assert g.GATE_ORDER_HEAD == (GateKind.SAFETY, GateKind.AI_PAUSED)
    assert isinstance(g.GATE_ORDER_HEAD, tuple)
    monkeypatch.setattr(g, "GATE_ORDER_HEAD", order)
    order_id = "option_a" if order[0] is GateKind.SAFETY else "option_b"
    for n, text, flag_kwargs, under_a, under_b in _ORDER_CASES:
        expected = under_a if order_id == "option_a" else under_b
        _, d = _decide(g, _text(text), _flags(**flag_kwargs))
        print(f"{order_id} case{n}: {d.kind.value}")
        assert d.kind is expected, f"{order_id} case{n}"


# --- AC-2 .. AC-7 -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("text", [WP5, "co alarm keeps going off"])
def test_wp5_co_alarm_is_safety(g: ModuleType, text: str) -> None:
    """invariant: AC-2 WP-5 and the HP-2 typo form give the safety decision with no model."""
    _, d = _decide(g, _text(text))
    print(f"{text!r}: {d.kind.value} {d.rules.safety}")
    assert d.kind is GateKind.SAFETY
    assert d.rules.safety is SafetyKind.CO
    assert d.gate_result() == "safety"


def test_wp6_burning_smell_asks(g: ModuleType) -> None:
    """invariant: AC-3 WP-6 asks the burning question and does not answer it."""
    _, d = _decide(g, _text(WP6))
    assert d.kind is GateKind.BURNING_ASK
    assert d.gate_result() == "burning_unclear"
    assert d.burning_answer is None


def test_burning_answers(g: ModuleType) -> None:
    """invariant: AC-4 yes/no/not_sure map; stale card counts; text answers unsure; person words win; PA-6 unknown option."""
    burn = g.burning_card_id(_turn_id())
    flags = _flags(burning=burn)
    expected = [
        ("yes", "yes", "safety"),
        ("no", "no", "clear"),
        ("not_sure", "unsure", "burning_unclear"),
        ("maybe", "unsure", "burning_unclear"),
    ]
    for option, answer, result in expected:
        _, d = _decide(g, _choice(burn, option), flags)
        print(f"{option}: {d.kind.value} {d.burning_answer}")
        assert d.kind is GateKind.BURNING_ANSWER
        assert d.burning_answer == answer
        assert d.gate_result() == result

    stale = g.burning_card_id(_turn_id())
    _, d = _decide(g, _choice(stale, "yes"), _flags())
    print(f"stale yes: {d.kind.value} {d.burning_answer}")
    assert d.kind is GateKind.BURNING_ANSWER
    assert d.burning_answer == "yes"

    _, d = _decide(g, _text("not sure"), flags)
    print(f"text not sure: {d.kind.value} {d.burning_answer}")
    assert d.kind is GateKind.BURNING_ANSWER
    assert d.burning_answer == "unsure"

    _, d = _decide(g, _text("not sure, can I talk to a person"), flags)
    print(f"text not sure + person: {d.kind.value}")
    assert d.kind is GateKind.PERSON


def test_person_words_first_ask(g: ModuleType) -> None:
    """invariant: AC-5 person words route to a person on the first ask, nothing else set."""
    _, d = _decide(g, _text(PERSON), _flags())
    assert d.kind is GateKind.PERSON
    assert d.gate_result() == "person_requested"


def test_danger_words(g: ModuleType) -> None:
    """invariant: AC-6 danger words are a gate decision."""
    _, d = _decide(g, _text("My son can't breathe"))
    assert d.kind is GateKind.DANGER_RULE
    assert d.gate_result() == "danger"


def test_human_controller_pauses_ai(g: ModuleType) -> None:
    """invariant: AC-7 a person in control pauses the AI for ordinary text."""
    _, d = _decide(g, _text("When will the technician arrive?"), _flags(paused=True))
    assert d.kind is GateKind.AI_PAUSED
    assert d.gate_result() == "ai_paused"
    assert g.flags_from_state(_state(controller_kind="human")).ai_paused is True


# --- AC-8 -------------------------------------------------------------------------------------------------


def test_code_cards_and_forms(g: ModuleType) -> None:
    """invariant: AC-8 code, locate form, where form and slot choice parse and route; digits stay in a SecretStr."""
    code = _code()
    cid = f"code-{_turn_id()}"
    i, d = _decide(g, _code_payload(cid, code))
    print(f"code: {i.kind} {i.text_store} -> {d.kind.value} {d.resume_task_id}")
    assert i.kind == "code"
    assert i.text_store == "[code entered]"
    assert isinstance(i.code_digits, SecretStr)
    assert i.code_digits.get_secret_value() == code
    assert i.card_id == cid
    assert d.kind is GateKind.CODE_ENTRY
    assert d.resume_task_id is None
    assert d.gate_result() == "clear"

    i, d = _decide(g, _choice(cid, "new_code"), _flags(code_open=True))
    print(f"new_code: {i.kind} {i.text_store} -> {d.kind.value}")
    assert d.kind is GateKind.CODE_ENTRY
    assert d.gate_result() == "clear"

    i, d = _decide(g, _form(f"locate-{_turn_id()}", name="Omar Patel", phone=SecretStr(_phone())))
    print(f"locate: {i.kind} {i.text_store} -> {d.kind.value}")
    assert i.text_store == "[details submitted]"
    assert i.form is not None
    assert isinstance(i.form.phone, SecretStr)
    assert d.kind is GateKind.LOCATE
    assert d.gate_result() == "clear"

    for where in ("78704", "Austin"):
        i, d = _decide(g, _form("t1.2", zip_or_city=where), _flags(tasks=("t1",)))
        print(f"where {where}: {i.kind} {i.text_store} -> {d.kind.value} {d.resume_task_id}")
        assert i.text_store == where
        assert i.form is not None
        assert i.form.zip_or_city == where
        assert d.kind is GateKind.CARD_CHOICE
        assert d.resume_task_id == "t1"
        assert d.gate_result() == "clear"

    i, d = _decide(g, _choice("t1.1", "56"), _flags(tasks=("t1",)))
    print(f"slot: {i.kind} {i.text_store} -> {d.kind.value} {d.resume_task_id}")
    assert d.kind is GateKind.CARD_CHOICE
    assert d.resume_task_id == "t1"
    assert i.choice is not None
    assert i.choice.option == "56"
    assert i.choice.card_id == "t1.1"
    assert d.gate_result() == "clear"


# --- AC-9 -------------------------------------------------------------------------------------------------


def test_untrusted_and_stale_cards_are_free_text(g: ModuleType) -> None:
    """failure/refusal: AC-9 unknown, closed-task and code-less cards fall to free text and route nowhere."""
    assert {"kind", "rules", "burning_answer", "resume_task_id"} == set(GateDecision.model_fields)
    choices = [
        ("slot-56", "56", _flags()),
        ("t9.1", "56", _flags(tasks=("t1",))),
        (f"code-{_turn_id()}", "new_code", _flags(code_open=False)),
    ]
    for card_id, option, flags in choices:
        i, d = _decide(g, _choice(card_id, option), flags)
        print(f"choice {card_id[:5]}: {d.kind.value} {i.text_store!r}")
        assert d.kind is GateKind.FREE_TEXT
        assert d.resume_task_id is None
        assert i.text_store == option

    phone = _phone()
    forms: list[tuple[str, dict[str, Any], GateFlags, bool]] = [
        ("slot-56", {"name": "Omar Patel", "phone": SecretStr(phone)}, _flags(), True),
        (f"code-{_turn_id()}", {"name": "Omar Patel", "phone": SecretStr(phone)}, _flags(), True),
        (g.burning_card_id(_turn_id()), {"zip_or_city": "78704"}, _flags(), True),
        ("t9.1", {"name": "Omar Patel", "phone": SecretStr(phone)}, _flags(tasks=("t1",)), False),
    ]
    for card_id, values, flags, form_dropped in forms:
        i, d = _decide(g, _form(card_id, **values), flags)
        print(f"form {card_id[:5]}: {d.kind.value} {i.text_store!r}")
        assert d.kind is GateKind.FREE_TEXT
        assert d.resume_task_id is None
        assert i.text_store == "[details submitted]"
        if form_dropped:
            assert i.form is None
        assert phone not in d.model_dump_json()
        assert phone not in i.text_store


# --- AC-10 ------------------------------------------------------------------------------------------------


def test_card_target_burning_card_id_and_flags(g: ModuleType) -> None:
    """invariant: AC-10 card_target classifies untrusted ids; burning_card_id and flags_from_state are exact."""
    t = _turn_id()
    assert g.card_target(f"burn-{t}") == ("burning", None)
    assert g.card_target(f"code-{t}") == ("code", None)
    assert g.card_target(f"locate-{t}") == ("locate", None)
    assert g.card_target("t7.2") == ("task", "t7")
    assert g.card_target("t.1.3") == ("task", "t.1")
    assert g.card_target("burn-x.1") == ("burning", None)
    for bad in [
        "",
        "burn-",
        "code-",
        "locate-",
        "slot-56",
        "t7",
        "t7.",
        ".3",
        "t7.x",
        "burn-a b",
        "BURN-abc",
        "a" * 127 + ".1",
    ]:
        assert g.card_target(bad) == ("unknown", None), bad
    assert g.card_target("a" * 124 + ".1") == ("task", "a" * 124)
    assert g.burning_card_id(t) == f"burn-{t}"

    state = _state(
        controller_kind="human",
        burning="burn-x",
        identity_status="code_sent",
        tasks=[("t1", "open"), ("t2", "waiting_identity"), ("t3", "done")],
    )
    assert g.flags_from_state(state) == GateFlags(
        ai_paused=True, burning_card_id="burn-x", code_card_open=True, open_task_ids=("t1", "t2")
    )
    assert g.flags_from_state(_state()) == GateFlags(
        ai_paused=False, burning_card_id=None, code_card_open=False, open_task_ids=()
    )
    assert g.flags_from_state(_state(identity_status="verified")).code_card_open is False


# --- AC-11 ------------------------------------------------------------------------------------------------


def test_card_and_code_removed_at_intake(g: ModuleType) -> None:
    """invariant: AC-11 a card-like number never reaches text_store; a standalone six-digit number becomes [code]."""
    card = _card()
    i = g.parse_intake(_text(f"Can you take my card {card} now?"))
    print(f"card text: {i.text_store!r}")
    assert card not in i.text_store
    assert "[card number removed]" in i.text_store
    assert i.card_number_seen is True

    code = _code()
    i = g.parse_intake(_text(f"the code was {code} I think"))
    print(f"code text: {i.text_store!r}")
    assert code not in i.text_store
    assert "[code]" in i.text_store
    assert i.card_number_seen is False


# --- AC-12 ------------------------------------------------------------------------------------------------


def test_secrets_absent_from_intake_decision_errors_logs(
    g: ModuleType, caplog: pytest.LogCaptureFixture
) -> None:
    """negative: AC-12 code, card-like number and full phone appear in no stored text, repr, dump, rule id, error or log."""
    caplog.set_level(logging.DEBUG)
    code, card, phone = _code(), _card(), _phone()
    secrets_ = (code, card, phone)
    turns = [
        _code_payload(f"code-{_turn_id()}", code),
        _text(f"my card {card} and the code {code}"),
        _form(f"locate-{_turn_id()}", name="Omar Patel", phone=SecretStr(phone)),
        _choice("t1.1", f"pay with {card}"),
    ]
    for payload in turns:
        i, d = _decide(g, payload, _flags(tasks=("t1",)))
        for s in secrets_:
            assert s not in i.text_store
            assert s not in repr(i)
            assert s not in i.model_dump_json()
            assert s not in repr(d)
            assert s not in d.model_dump_json()
            assert all(s not in rid for rid in d.rules.rule_ids)

    errors: list[ValidationError] = []
    with pytest.raises(ValidationError) as e1:
        TextPayload.model_validate({"kind": "text", "text": "x" * 1990 + card})
    errors.append(e1.value)
    with pytest.raises(ValidationError) as e2:
        CodePayload.model_validate({"kind": "code", "card_id": "code-x", "code": code, "note": code})
    errors.append(e2.value)
    with pytest.raises(ValidationError) as e3:
        FormPayload.model_validate(
            {"kind": "form", "card_id": "locate-x", "values": {"phone": phone, "customer_id": "MHC-1"}}
        )
    errors.append(e3.value)
    for err in errors:
        for s in secrets_:
            assert s not in str(err)

    for s in secrets_:
        assert s not in caplog.text
        assert all(s not in r.getMessage() for r in caplog.records)


# --- AC-13 ------------------------------------------------------------------------------------------------

_ALLOWED_IMPORTS = {
    "__future__",
    "re",
    "typing",
    "meridian.domain.common",
    "meridian.domain.state",
    "meridian.domain.turn",
    "meridian.gates.rules",
    "meridian.privacy.redact",
}
_FORBIDDEN_IMPORTS = {
    "sqlite3", "httpx", "anthropic", "openai", "langfuse", "fastembed", "requests", "socket",
    "time", "datetime", "random", "logging", "os",
}  # fmt: skip
_FORBIDDEN_PREFIXES = (
    "meridian.agent",
    "meridian.services",
    "meridian.web",
    "meridian.adapters",
    "meridian.ports",
)


def test_gate_module_is_pure(g: ModuleType) -> None:
    """invariant: AC-13 imports stay on the allowlist and the same input gives the same output."""
    tree = ast.parse(Path(str(g.__file__)).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module is not None
            names.add(node.module)
    print(sorted(names))
    assert names <= _ALLOWED_IMPORTS
    assert names.isdisjoint(_FORBIDDEN_IMPORTS)
    assert not any(n.startswith(_FORBIDDEN_PREFIXES) for n in names)

    burn_turn = _turn_id()
    payloads = [
        _text(WP5),
        _code_payload(f"code-{_turn_id()}", _code()),
        _choice(g.burning_card_id(burn_turn), "yes"),
    ]
    flags = _flags(burning=g.burning_card_id(burn_turn))
    for p in payloads:
        assert g.parse_intake(p) == g.parse_intake(p)
        i = g.parse_intake(p)
        assert g.decide_gate(i, flags) == g.decide_gate(i, flags)


# --- plan-added obligations (PA-1 .. PA-5) ----------------------------------------------------------------


def test_untrusted_choice_strings_are_store_redacted(g: ModuleType) -> None:
    """negative: PA-1 an untrusted option or unknown card id cannot carry a card number into state."""
    card = _card()
    i, _ = _decide(g, _choice("t1.1", f"pay with {card}"), _flags(tasks=("t1",)))
    assert card not in i.text_store
    assert i.choice is not None
    assert card not in i.choice.option
    assert i.card_number_seen is True
    assert i.card_id == "t1.1"

    glued = card.replace(" ", "")
    i, d = _decide(g, _choice(glued, "yes"))
    assert glued not in (i.card_id or "")
    assert card not in repr(i)
    assert glued not in repr(i)
    assert i.card_number_seen is True
    assert d.kind is GateKind.FREE_TEXT

    odd = _code()
    i, d = _decide(g, _code_payload(odd, _code()))
    assert odd not in repr(i)
    assert d.kind is GateKind.CODE_ENTRY

    cid = f"code-{_turn_id()}"
    i, _ = _decide(g, _code_payload(cid, _code()))
    assert i.card_id == cid


def test_form_text_store_rules(g: ModuleType) -> None:
    """invariant: PA-2 form text_store: where form stores ZIP or city; anything else stores [details submitted]."""
    flags = _flags(tasks=("t1",))
    i, _ = _decide(g, _form("t1.2", zip_or_city="Austin"), flags)
    assert i.text_store == "Austin"

    i, _ = _decide(g, _form("t1.2", zip_or_city="   "), flags)
    assert i.text_store == "[details submitted]"

    i, d = _decide(g, _form("t1.2", zip_or_city="78704", phone=SecretStr(_phone())), flags)
    assert i.text_store == "[details submitted]"
    assert i.form is not None
    assert d.kind is GateKind.CARD_CHOICE

    i, d = _decide(g, _form("t9.2", zip_or_city="78704"), flags)
    assert d.kind is GateKind.FREE_TEXT
    assert d.resume_task_id is None
    assert i.text_store == "78704"


def test_ai_paused_precedes_every_card_step(g: ModuleType) -> None:
    """invariant: PA-3 while a person controls the chat, every card step waits behind AI_PAUSED."""
    paused = _flags(paused=True, tasks=("t1",))
    burn = g.burning_card_id(_turn_id())
    payloads = [
        _code_payload(f"code-{_turn_id()}", _code()),
        _choice(burn, "yes"),
        _form(f"locate-{_turn_id()}", name="Omar Patel", phone=SecretStr(_phone())),
        _choice("t1.1", "56"),
    ]
    for p in payloads:
        _, d = _decide(g, p, paused)
        assert d.kind is GateKind.AI_PAUSED


def test_code_payload_is_always_code_entry(g: ModuleType) -> None:
    """invariant: PA-4 a code payload is CODE_ENTRY whether or not a code card is open."""
    _, d = _decide(g, _code_payload(f"code-{_turn_id()}", _code()), _flags(code_open=False))
    assert d.kind is GateKind.CODE_ENTRY
    _, d = _decide(g, _code_payload("slot-56", _code()))
    assert d.kind is GateKind.CODE_ENTRY


def test_policy_word_rides_on_free_text(g: ModuleType) -> None:
    """invariant: PA-5 a policy word gets no gate kind; it rides on rules.policy_trigger."""
    _, d = _decide(g, _text("I want a refund"))
    assert d.kind is GateKind.FREE_TEXT
    assert d.rules.policy_trigger is HandoffReason.REFUND
    assert d.gate_result() == "clear"
