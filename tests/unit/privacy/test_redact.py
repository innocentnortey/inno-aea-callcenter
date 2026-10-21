"""AEA-04: `privacy/redact.py`, one redaction function with five profiles (frozen tests, written first).

All private-looking values are built at run time from seeded generators; the only literals are the
issued, fictional WP-2 identifiers. The module under test is imported through a fixture so this file
collects before `redact.py` exists.
"""

import dataclasses
import importlib
import random
import re
import time
import traceback
from types import ModuleType

import pytest

PROFILES = ("store", "sonnet", "jev", "trace", "log")
KINDS = ("card", "code", "phone", "email", "address", "name", "customer_id", "invoice_id")

# Which kinds each profile replaces (data.md section 1). LOG replaces everything.
REPLACED: dict[str, set[str]] = {
    "store": {"card", "code"},
    "sonnet": {"card", "code", "phone", "email", "address"},
    "jev": set(KINDS),
    "trace": {"card", "code", "phone", "email", "address", "name"},
    "log": set(KINDS),
}

TEMPLATE = (
    "Hi, my name is {name}. Phone {phone}, email {email}. I live at {address}, Kyle, TX 78640. "
    "Account {customer_id}, invoice {invoice_id}. My code is {code}. Card {card}."
)
FACTS = (
    "Invoice {invoice_id}: Diagnostic visit $89, Contactor replacement $245, After-hours dispatch $144, "
    "total $478.00, due 2026-11-01. Window 8:00 am – 12:00 pm, Plus tier, case MHC-C-0007."
)

AC7_TEXT = (
    "Austin, TX 78620. Kyle 78640. Total $478.00, $89, $1,245.50. "
    "Due 2026-11-01, issued 2026-10-02, between 2026-11-01 to 2026-11-05. Slot 37, slot 4. "
    "Window 8:00 am – 12:00 pm, 1:00 pm – 5:00 pm. Case MHC-C-0007. Plus tier. "
    "A 2 hour drive, 2 techs on the way."
)


# --------------------------------------------------------------------------- helpers


def _digits(rng: random.Random, n: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def _card(rng: random.Random, n: int, sep: str) -> str:
    digits = _digits(rng, n)
    return sep.join(digits[i : i + 4] for i in range(0, n, 4))


def _phone(rng: random.Random, last_two: str) -> str:
    return f"{rng.randint(200, 989)}-{rng.randint(200, 989)}-{_digits(rng, 2)}{last_two}"


def _code(rng: random.Random) -> str:
    return str(rng.randint(100000, 999999))


def _word(rng: random.Random) -> str:
    return rng.choice(["Vel", "Tor", "Quin", "Zar", "Bel"]) + rng.choice(["ana", "ric", "ella", "ton", "ivo"])


def _seeded(seed: int) -> dict[str, str]:
    rng = random.Random(seed)
    first, last = _word(rng), _word(rng)
    return {
        "card": _card(rng, 16, " "),
        "code": _code(rng),
        "phone": _phone(rng, "02"),
        "email": f"{first.lower()}.{last.lower()}{rng.randint(10, 99)}@example.test",
        "customer_id": f"MHC-{rng.randint(10000, 99999)}",
        "invoice_id": f"INV-{rng.randint(200000, 299999)}",
        "address": f"{rng.randint(100, 9999)} {_word(rng)} Dr",
        "name": f"{first} {last}",
    }


def _tokens(profile: str, vals: dict[str, str]) -> dict[str, str]:
    """The expected value of each template field after redaction under `profile`."""
    out = dict(vals)
    out["card"] = "[card number removed]"
    out["code"] = "[code]"
    if profile in ("sonnet", "jev", "trace"):
        out["email"] = "[email]"
        out["address"] = "[address]"
        out["phone"] = "[phone]" if profile == "jev" else f"[phone ending {vals['phone'][-2:]}]"
    if profile in ("jev", "trace"):
        out["name"] = "[name]"
    if profile == "jev":
        out["customer_id"] = "[customer id]"
        out["invoice_id"] = "[invoice id]"
    return out


def _exc_text(exc: BaseException) -> str:
    return str(exc) + repr(exc) + "".join(traceback.format_exception(exc))


def _no_slice_of(sentinel: str, haystack: str, width: int = 12) -> bool:
    return not any(sentinel[i : i + width] in haystack for i in range(len(sentinel) - width + 1))


@pytest.fixture(scope="module")
def rd() -> ModuleType:
    return importlib.import_module("meridian.privacy.redact")


# --------------------------------------------------------------------------- contract shape


def test_enum_values_are_the_contract(rd: ModuleType) -> None:
    """invariant: the enum values are what AEA-02 and every consumer type against."""
    assert [k.value for k in rd.RedactionKind] == [
        "card",
        "code",
        "phone",
        "email",
        "address",
        "name",
        "customer_id",
        "invoice_id",
        "free_text",
    ]
    assert [p.value for p in rd.RedactionProfile] == list(PROFILES)
    assert issubclass(rd.UnknownRedactionProfile, ValueError)


def test_redacted_repr_and_immutability(rd: ModuleType) -> None:
    """invariant: repr shows counts and length only; the result is immutable."""
    r = rd.redact(TEMPLATE.format(**_seeded(11)), rd.RedactionProfile.JEV)
    assert re.fullmatch(r"Redacted\(length=\d+, replaced=\{[a-z_: 0-9,]*\}\)", repr(r)), repr(r)
    assert "[" not in repr(r)
    assert str(r) == repr(r)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.text = "x"
    with pytest.raises(TypeError):
        r.replaced[rd.RedactionKind.CARD] = 5


# --------------------------------------------------------------------------- AC-1


@pytest.mark.parametrize(
    ("n", "sep"),
    [(n, sep) for n in (13, 16, 19) for sep in ("", " ", "-")],
    ids=[f"{n}-{name}" for n in (13, 16, 19) for name in ("plain", "space", "dash")],
)
def test_store_masks_cards_and_codes_keeps_contact(rd: ModuleType, n: int, sep: str) -> None:
    """invariant (AC-1): STORE masks cards and six-digit codes, keeps names, phones, emails, addresses."""
    rng = random.Random(4)
    card, code = _card(rng, n, sep), _code(rng)
    vals = _seeded(11)
    text = (
        f"My card is {card} and my code is {code}. "
        f"I'm {vals['name']}, {vals['phone']}, {vals['email']}, {vals['address']}."
    )
    expected = (
        f"My card is [card number removed] and my code is [code]. "
        f"I'm {vals['name']}, {vals['phone']}, {vals['email']}, {vals['address']}."
    )
    result = rd.redact(text, rd.RedactionProfile.STORE)
    assert result.text == expected
    assert dict(result.replaced) == {rd.RedactionKind.CARD: 1, rd.RedactionKind.CODE: 1}
    assert re.sub(r"\D", "", card) not in re.sub(r"\D", "", result.text)


# --------------------------------------------------------------------------- AC-2


def test_jev_masks_every_identifier(rd: ModuleType) -> None:
    """invariant (AC-2): JEV replaces every identifier kind with the signed tokens."""
    vals = _seeded(11)
    result = rd.redact(TEMPLATE.format(**vals), rd.RedactionProfile.JEV)
    assert result.text == TEMPLATE.format(**_tokens("jev", vals))
    assert dict(result.replaced) == {rd.RedactionKind(k): 1 for k in KINDS}
    for intro in ("this is", "I'm", "I’m", "My name is", "I am"):
        masked = rd.redact(f"{intro} {vals['name']}.", rd.RedactionProfile.JEV)
        assert masked.text == f"{intro} [name].", intro


def test_placeholders_stable_across_calls(rd: ModuleType) -> None:
    """invariant (AC-2): the same kind maps to the same token for different values and repeated calls."""
    a = rd.redact(TEMPLATE.format(**_seeded(11)), rd.RedactionProfile.JEV)
    b = rd.redact(TEMPLATE.format(**_seeded(12)), rd.RedactionProfile.JEV)
    assert a.text == b.text
    again = rd.redact(TEMPLATE.format(**_seeded(11)), rd.RedactionProfile.JEV)
    assert again == a


# --------------------------------------------------------------------------- AC-3, AC-4


def test_sonnet_masks_contact_keeps_ids(rd: ModuleType) -> None:
    """invariant (AC-3): SONNET masks card, code, email, street, turns phone into a hint; keeps names and IDs."""
    vals = _seeded(11)
    result = rd.redact(TEMPLATE.format(**vals) + " " + FACTS.format(**vals), rd.RedactionProfile.SONNET)
    expected = TEMPLATE.format(**_tokens("sonnet", vals)) + " " + FACTS.format(**_tokens("sonnet", vals))
    assert result.text == expected
    assert vals["name"] in result.text
    assert vals["customer_id"] in result.text
    assert vals["invoice_id"] in result.text
    only = rd.redact(TEMPLATE.format(**vals), rd.RedactionProfile.SONNET)
    assert dict(only.replaced) == {rd.RedactionKind(k): 1 for k in REPLACED["sonnet"]}


def test_trace_profile(rd: ModuleType) -> None:
    """invariant (AC-4): TRACE keeps phone last two digits, masks names, emails, streets; account facts survive."""
    vals = _seeded(11)
    result = rd.redact(TEMPLATE.format(**vals) + " " + FACTS.format(**vals), rd.RedactionProfile.TRACE)
    expected = TEMPLATE.format(**_tokens("trace", vals)) + " " + FACTS.format(**_tokens("trace", vals))
    assert result.text == expected
    for kept in ("$478.00", "2026-11-01", "8:00 am – 12:00 pm", "Plus", "MHC-C-0007"):
        assert kept in result.text
    assert vals["customer_id"] in result.text
    assert vals["invoice_id"] in result.text
    only = rd.redact(TEMPLATE.format(**vals), rd.RedactionProfile.TRACE)
    assert dict(only.replaced) == {rd.RedactionKind(k): 1 for k in REPLACED["trace"]}


# --------------------------------------------------------------------------- AC-5


def test_log_profile_is_length_only(rd: ModuleType) -> None:
    """invariant (AC-5): LOG keeps nothing but the length."""
    vals = _seeded(11)
    msg = TEMPLATE.format(**vals)
    result = rd.redact(msg, rd.RedactionProfile.LOG)
    assert result.text == ""
    assert result.length == len(msg)
    assert dict(result.replaced) == {rd.RedactionKind.FREE_TEXT: 1}
    for value in vals.values():
        assert value not in repr(result)

    alphabet = "QWXZJKVBNM#!?%&*"
    rng = random.Random(5)
    msg2 = "".join(rng.choice(alphabet) for _ in range(64))
    result2 = rd.redact(msg2, rd.RedactionProfile.LOG)
    assert result2.length == 64
    for i in range(len(msg2) - 1):
        window = msg2[i : i + 2]
        assert window not in result2.text
        assert window not in repr(result2)


# --------------------------------------------------------------------------- AC-6


@pytest.mark.parametrize("profile", PROFILES)
def test_seeded_values_absent(rd: ModuleType, profile: str) -> None:
    """invariant/negative (AC-6): seeded values are absent wherever the matrix says replaced, kept elsewhere."""
    vals = _seeded(11)
    msg = TEMPLATE.format(**vals)
    result = rd.redact(msg, rd.RedactionProfile(profile))
    out_digits = re.sub(r"\D", "", result.text)
    for kind in KINDS:
        if kind in REPLACED[profile]:
            assert vals[kind] not in result.text, kind
            assert vals[kind] not in repr(result), kind
            assert vals[kind] not in str(result), kind
            if kind == "phone":
                assert re.sub(r"\D", "", vals["phone"])[:8] not in out_digits
            if kind == "card":
                assert re.sub(r"\D", "", vals["card"]) not in out_digits
            if kind == "name":
                for word in vals["name"].split():
                    assert word not in result.text
                    assert word not in repr(result)
        else:
            assert vals[kind] in result.text, kind
    with pytest.raises(rd.UnknownRedactionProfile) as info:
        rd.redact(msg, "no_such_profile")
    exc_text = _exc_text(info.value)
    for value in vals.values():
        assert value not in exc_text
    print(
        f"{profile}: " + ", ".join(f"{k}={'replaced' if k in REPLACED[profile] else 'kept'}" for k in KINDS)
    )


# --------------------------------------------------------------------------- AC-7


@pytest.mark.parametrize("profile", ["store", "sonnet", "trace"])
def test_non_private_values_survive(rd: ModuleType, profile: str) -> None:
    """negative (AC-7): ZIPs, cities, amounts, dates, slots and times survive; a phone is never a card."""
    result = rd.redact(AC7_TEXT, rd.RedactionProfile(profile))
    assert result.text == AC7_TEXT
    assert dict(result.replaced) == {}

    rng = random.Random(7)
    base = _phone(rng, "02")
    digits = re.sub(r"\D", "", base)
    forms = [base, f"({digits[:3]}) {digits[3:6]}-{digits[6:]}", digits]
    for form in forms:
        text = f"Call me at {form} please."
        stored = rd.redact(text, rd.RedactionProfile.STORE)
        assert stored.text == text
        assert dict(stored.replaced) == {}
        hinted = rd.redact(text, rd.RedactionProfile.SONNET)
        assert hinted.text == "Call me at [phone ending 02] please."
        assert "[card number removed]" not in hinted.text


# --------------------------------------------------------------------------- AC-8


def _idempotence_inputs() -> list[str]:
    rng = random.Random(8)
    turn1 = f"Hi, my name is Omar Patel, account MHC-10002, phone {_phone(rng, '02')}."
    turn2 = f"What is INV-204411 for? I can pay now, card {_card(rng, 16, ' ')}."
    return [
        TEMPLATE.format(**_seeded(11)),
        TEMPLATE.format(**_seeded(12)),
        TEMPLATE.format(**_seeded(11)) + " " + FACTS.format(**_seeded(11)),
        AC7_TEXT,
        turn1,
        turn2,
    ]


@pytest.mark.parametrize("profile", PROFILES)
def test_idempotent(rd: ModuleType, profile: str) -> None:
    """invariant (AC-8): redacting redacted text changes nothing and replaces nothing."""
    p = rd.RedactionProfile(profile)
    for text in _idempotence_inputs():
        first = rd.redact(text, p)
        second = rd.redact(first.text, p)
        assert second.text == first.text
        assert all(n == 0 for n in second.replaced.values())


# --------------------------------------------------------------------------- AC-9 and refusals


def test_unknown_profile_refused_without_echo(rd: ModuleType) -> None:
    """failure (AC-9): unknown profile raises; the message names the profile value only, never the text."""
    vals = _seeded(12)
    sentinel = TEMPLATE.format(**vals)
    with pytest.raises(rd.UnknownRedactionProfile) as info:
        rd.redact(sentinel, "no_such_profile")
    assert isinstance(info.value, ValueError)
    assert "no_such_profile" in str(info.value)
    exc_text = _exc_text(info.value)
    for value in vals.values():
        assert value not in exc_text
    assert _no_slice_of(sentinel, exc_text)


def test_unknown_profile_swapped_args_not_echoed(rd: ModuleType) -> None:
    """boundary: redact(profile, text) with swapped arguments never echoes the text."""
    vals = _seeded(12)
    sentinel = TEMPLATE.format(**vals)
    with pytest.raises(rd.UnknownRedactionProfile) as info:
        rd.redact(rd.RedactionProfile.JEV, sentinel)
    exc_text = _exc_text(info.value)
    for value in vals.values():
        assert value not in exc_text
    assert _no_slice_of(sentinel, exc_text)


def test_non_str_text_refused_without_echo(rd: ModuleType) -> None:
    """boundary: non-str text is refused with a type-name-only message."""
    vals = _seeded(12)
    sentinel = TEMPLATE.format(**vals)
    with pytest.raises(TypeError) as info_bytes:
        rd.redact(sentinel.encode(), rd.RedactionProfile.STORE)
    assert "bytes" in str(info_bytes.value)
    with pytest.raises(TypeError) as info_none:
        rd.redact(None, rd.RedactionProfile.STORE)
    assert "NoneType" in str(info_none.value)
    for exc in (info_bytes.value, info_none.value):
        exc_text = _exc_text(exc)
        for value in vals.values():
            assert value not in exc_text


def test_plain_string_profile_value_accepted(rd: ModuleType) -> None:
    """boundary: a plain str equal to a profile value behaves as that profile."""
    msg = TEMPLATE.format(**_seeded(11))
    for value in PROFILES:
        assert rd.redact(msg, value) == rd.redact(msg, rd.RedactionProfile(value))


def test_empty_text_every_profile(rd: ModuleType) -> None:
    """boundary: empty input gives empty text, no counts and length 0 under every profile."""
    for value in PROFILES:
        result = rd.redact("", rd.RedactionProfile(value))
        assert result.text == ""
        assert dict(result.replaced) == {}
        assert result.length == 0


def test_brand_greeting_not_a_name(rd: ModuleType) -> None:
    """negative: the assistant's own greeting is not an introduced name."""
    greeting = "This is Meridian Home Comfort, how can I help?"
    for profile in (rd.RedactionProfile.TRACE, rd.RedactionProfile.JEV):
        assert rd.redact(greeting, profile).text == greeting


def test_patterns_run_in_bounded_time(rd: ModuleType) -> None:
    """boundary: untrusted 100 000-character inputs cannot stall the masker."""
    inputs = [
        "1 " * 50_000,
        "1-" * 50_000,
        "a" * 100_000 + "@",
        "my name is " + "Ab " * 33_000,
        "1234 " + "Oak " * 25_000,
    ]
    start = time.perf_counter()
    for text in inputs:
        for value in PROFILES:
            rd.redact(text, rd.RedactionProfile(value))
    assert time.perf_counter() - start < 2.0


# --------------------------------------------------------------------------- WP-2


@pytest.mark.parametrize("profile", PROFILES)
def test_wp2_worked_pair(rd: ModuleType, profile: str) -> None:
    """regression: the issue's WP-2 worked pair, exact text per profile."""
    rng = random.Random(2)
    turn1 = f"Hi, my name is Omar Patel, account MHC-10002, phone {_phone(rng, '02')}."
    turn2 = f"What is INV-204411 for? I can pay now, card {_card(rng, 16, ' ')}."
    facts = FACTS.format(invoice_id="INV-204411")
    expected: dict[str, tuple[str, str, str]] = {
        "jev": (
            "Hi, my name is [name], account [customer id], phone [phone].",
            "What is [invoice id] for? I can pay now, card [card number removed].",
            facts.replace("INV-204411", "[invoice id]"),
        ),
        "sonnet": (
            "Hi, my name is Omar Patel, account MHC-10002, phone [phone ending 02].",
            "What is INV-204411 for? I can pay now, card [card number removed].",
            facts,
        ),
        "trace": (
            "Hi, my name is [name], account MHC-10002, phone [phone ending 02].",
            "What is INV-204411 for? I can pay now, card [card number removed].",
            facts,
        ),
        "store": (
            turn1,
            "What is INV-204411 for? I can pay now, card [card number removed].",
            facts,
        ),
    }
    p = rd.RedactionProfile(profile)
    turns = (turn1, turn2, facts)
    if profile == "log":
        for turn in turns:
            result = rd.redact(turn, p)
            assert result.text == ""
            assert result.length == len(turn)
        return
    for turn, want in zip(turns, expected[profile], strict=True):
        assert rd.redact(turn, p).text == want
