"""AEA-03: every fixed customer sentence equals its word source; render refuses misuse."""

from __future__ import annotations

import json
import re
import string
from pathlib import Path
from typing import Any, cast

import pytest

from meridian.policy.texts import (
    PLACEHOLDERS,
    TEXTS,
    TextId,
    TextRenderError,
    format_usd,
    render,
)

REPO = Path(__file__).resolve().parents[3]
FIXTURE = json.loads(Path(__file__).with_name("texts_source_fixture.json").read_text("utf-8"))
ENTRIES: list[dict[str, Any]] = FIXTURE["entries"]

GROUPS = (
    "greeting",
    "safety",
    "identity",
    "promise",
    "fee_change",
    "followup",
    "booking",
    "limits",
    "live",
    "demo",
)
EXPECTED_COUNTS = {
    "greeting": 2,
    "safety": 11,
    "identity": 7,
    "promise": 7,
    "fee_change": 4,
    "followup": 3,
    "booking": 12,
    "limits": 7,
    "live": 6,
    "demo": 12,
}


def test_every_sentence_matches_its_source_fixture() -> None:
    ids = [e["id"] for e in ENTRIES]
    assert len(ids) == len(set(ids)), "duplicate fixture id"
    assert set(ids) == {t.value for t in TextId}, "fixture and TextId differ"
    for e in ENTRIES:
        text_id = TextId(e["id"])
        assert TEXTS[text_id] == e["template"], e["id"]
        src = e["source"]
        assert src["kind"] in {"screen_specs", "openapi", "proposal"}, e["id"]
        assert src["file"] and src["line"] and src["where"], e["id"]
        if e["example"] is not None:
            got = render(text_id, **e["example"]["values"])
            assert got == e["example"]["rendered"], e["id"]
    print(f"{len(ENTRIES)} fixture entries, {len(TextId)} text ids, unmatched: 0")


def test_fixture_quotes_its_source_files() -> None:
    cache: dict[str, str] = {}
    for e in ENTRIES:
        file = e["source"]["file"]
        if file not in cache:
            raw = (REPO / file).read_text("utf-8")
            cache[file] = re.sub(r"\s+", " ", raw)
        doc = cache[file]
        for literal, _field, _spec, _conv in string.Formatter().parse(e["template"]):
            if literal:
                assert literal in doc, f"{e['id']}: {literal!r} not in {file}"
        if e["example"] is not None:
            assert e["example"]["rendered"] in doc, e["id"]


def test_text_id_shape_and_named_ids() -> None:
    shape = re.compile(r"^(" + "|".join(GROUPS) + r")\.[a-z][a-z0-9_]*$")
    counts = dict.fromkeys(GROUPS, 0)
    for t in TextId:
        assert shape.match(t.value), t.value
        counts[t.value.split(".")[0]] += 1
    print("group -> count:", counts, "total", sum(counts.values()))
    assert counts == EXPECTED_COUNTS
    assert TextId.INBOX_CODE_BODY.value == "identity.inbox_code_body"
    assert TextId.INBOX_CODE_GONE.value == "identity.inbox_code_gone"
    assert TextId("booking.urgent_note") is TextId.URGENT_NOTE
    assert TextId.PERSON_REQUEST_LABEL.value == "live.person_request_label"
    assert render(TextId.PERSON_REQUEST_LABEL) == "Talk to a person"
    rep = {"rep_name": "Riley"}
    assert render(TextId.REP_JOINED, **rep) == "Riley (demo representative) has joined."
    assert render(TextId.AI_PAUSED, **rep) == "The assistant is paused while Riley is here."
    assert render(TextId.AI_RESUMED, **rep) == ("Riley handed the chat back to the automated assistant.")
    assert render(TextId.CHAT_CLOSED, **rep) == "Riley closed this chat."


def test_promise_texts_word_for_word() -> None:
    assert render(
        TextId.PROMISE_UNSTAFFED,
        due_label="Monday, October 19, 7:00 pm",
        case_ref="MHC-C-0007",
    ) == (
        "No representative is online right now. A representative will get back to "
        "you within 1 business day, by Monday, October 19, 7:00 pm. "
        "Your reference is MHC-C-0007."
    )
    assert render(TextId.PROMISE_REFUND) == (
        "A representative will get to your refund request within 2 business days."
    )
    assert render(TextId.PROMISE_REFUND_NO_OUTCOME) == "I can't promise an outcome."
    assert render(TextId.PROMISE_STAFFED) == (
        "A representative will join this chat when available. "
        "You can keep chatting with me while you wait, if you like."
    )
    assert render(TextId.PROMISE_DANGER_REVIEW) == (
        "No representative is online right now, so someone will review this online "
        "request within 1 business day. That is not the wait for emergency help; "
        "for that, please use the emergency line."
    )
    assert TEXTS[TextId.PROMISE_SAFETY_NONE] == ""
    assert render(TextId.FEE_CANT_GUARANTEE, window="12:00 pm – 4:00 pm") == (
        "I can't promise anyone will confirm a change before your appointment "
        "starts; until a representative confirms, please plan on the technician "
        "arriving 12:00 pm – 4:00 pm."
    )
    time_promise = re.compile(
        r"\bwithin\b|\bby \{|\bby \d|"
        r"\bby (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        re.IGNORECASE,
    )
    promising = {
        TextId.PROMISE_UNSTAFFED,
        TextId.PROMISE_REFUND,
        TextId.PROMISE_STAFFED,
        TextId.PROMISE_DANGER_REVIEW,
        TextId.PROMISE_SAFETY_NONE,
    }
    for text_id, template in TEXTS.items():
        if text_id not in promising:
            assert not time_promise.search(template), text_id.value
    for live in (
        TextId.PROMISE_UNSTAFFED,
        TextId.PROMISE_REFUND,
        TextId.PROMISE_DANGER_REVIEW,
    ):
        assert time_promise.search(TEXTS[live]), live.value


def test_safety_lines() -> None:
    kb = (
        REPO / "docs/data/issued/meridian_dataset/knowledge_base/policies" / "escalation_and_safety.md"
    ).read_text("utf-8")
    kb = re.sub(r"\s+", " ", kb)
    kb_phrase = "leave the home immediately and call 911 or their gas utility from outside"
    assert kb_phrase in kb
    your = kb_phrase.replace("their", "your")
    assert TEXTS[TextId.SAFETY_LEAVE_NOW] == your[0].upper() + your[1:] + "."
    keep = "flip switches, open windows near the furnace, or restart equipment"
    assert keep in kb
    assert keep in TEXTS[TextId.SAFETY_DONT_TOUCH]
    assert "immediately" in TEXTS[TextId.SAFETY_LEAVE_NOW]
    assert "immediately" in TEXTS[TextId.WARNING_TEXT]
    for t in TextId:
        if t.value.startswith("safety."):
            assert not re.search(r"\btheir\b", TEXTS[t]), t.value
    demo = "(512) 555-0199 (demo number)"
    assert demo in TEXTS[TextId.EMERGENCY_NUMBER_LINE]
    assert demo in TEXTS[TextId.EMERGENCY_LINE_LEAD]


def test_wp5_carbon_monoxide_lines() -> None:
    lines = [
        render(TextId.SAFETY_LEAVE_NOW),
        render(TextId.SAFETY_DONT_TOUCH),
        render(TextId.SAFETY_CONTACT_LINE),
    ]
    assert lines == [
        "Leave the home immediately and call 911 or your gas utility from outside.",
        "Don't flip switches, open windows near the furnace, or restart equipment.",
        "Once you're outside and safe, you can leave a number here if you'd like.",
    ]
    timey = re.compile(r"\bwithin\b|business day|\d{1,2}:\d{2}|\bby \w+day\b")
    assert not any(timey.search(line) for line in lines)
    assert render(TextId.PROMISE_SAFETY_NONE) == ""


def test_timeout_and_busy_sentences() -> None:
    by_id = {e["id"]: e["template"] for e in ENTRIES}
    assert render(TextId.TURN_TIMEOUT) == "This is taking longer than it should."
    assert render(TextId.BUSY) == (
        "A lot of people are chatting right now, so I can't take this message. A person can pick it up."
    )
    assert render(TextId.TURN_TIMEOUT) == by_id["limits.turn_timeout"]
    assert render(TextId.BUSY) == by_id["limits.busy"]
    assert not any("I'm sorry" in text for text in TEXTS.values())


def test_forbidden_phrases_absent() -> None:
    patterns = {
        "charged": r"\bcharged\b",
        "shortly": r"\bshortly\b",
        "agent": r"\ban agent will be with you\b",
        "wait time": r"\bwait(ing)? time\b|\b\d+\s*(minute|min|hour)s?\s+(wait|away)\b",
        "queue position": (
            r"\bqueue position\b|\bposition in (the )?(queue|line)\b"
            r"|\b(you are|you're) (next|number \d+|#\s*\d+)\b|\bin line\b"
        ),
    }
    # "charged in any form" is read as any sentence using "charged"; "free of charge"
    # is not a charge claim (reported to UX, plan 8b U-10).
    sentences: list[tuple[str, str]] = [(t.value, v) for t, v in TEXTS.items()]
    sentences += [(e["id"], e["example"]["rendered"]) for e in ENTRIES if e["example"] is not None]
    hits: list[str] = []
    for ident, text in sentences:
        for label, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                hits.append(f"{ident}: {label}")
        if ident.startswith("followup.") and re.search(r"(?<!not )\bsent\b", text, re.IGNORECASE):
            hits.append(f"{ident}: sent")
    assert hits == []


def test_render_refuses_unknown_missing_and_extra() -> None:
    with pytest.raises(TextRenderError) as unknown:
        render(cast(TextId, "greeting.not_a_text"))
    assert unknown.value.text_id == "greeting.not_a_text"
    assert unknown.value.placeholder is None

    with pytest.raises(TextRenderError) as missing:
        render(TextId.CODE_WRONG)
    assert missing.value.text_id == "identity.code_wrong"
    assert missing.value.placeholder == "n"

    with pytest.raises(TextRenderError) as extra:
        render(TextId.VERIFIED, n="2")
    assert extra.value.text_id == "identity.verified"
    assert extra.value.placeholder == "n"

    with pytest.raises(TextRenderError) as plain:
        render(cast(TextId, "greeting.opening"))
    assert plain.value.text_id == "greeting.opening"

    bad: dict[str, Any] = {"n": 2}
    with pytest.raises(TextRenderError) as number:
        render(TextId.CODE_WRONG, **bad)
    assert number.value.placeholder == "n"

    for err in (unknown, missing, extra, plain, number):
        assert isinstance(err.value, KeyError)


def test_render_error_holds_no_values() -> None:
    ref = "MHC-C-" + "".join(str(d) for d in (9, 4, 7, 1))
    six = "".join(str(d) for d in (7, 0, 3, 9, 1, 5))
    number: dict[str, Any] = {"n": int(six)}
    errors: list[TextRenderError] = []
    attempts: list[Any] = [
        lambda: render(TextId.PROMISE_UNSTAFFED, case_ref=ref),
        lambda: render(TextId.VERIFIED, digits=six, case_ref=ref),
        lambda: render(TextId.INBOX_CODE_BODY, digits=six, n=ref),
        lambda: render(TextId.CODE_WRONG, **number),
        lambda: render(cast(TextId, six)),
    ]
    for attempt in attempts:
        with pytest.raises(TextRenderError) as caught:
            attempt()
        errors.append(caught.value)
    assert errors[-1].text_id == "<not a text id>"
    for err in errors:
        seen = [
            str(err),
            repr(err),
            repr(err.args),
            err.text_id,
            repr(err.placeholder),
        ]
        for blob in seen:
            for sentinel in (ref, six, str(int(six))):
                assert sentinel not in blob
        assert err.__cause__ is None
        assert err.__context__ is None
    assert render(TextId.INBOX_CODE_BODY, digits=six) == (
        f"Your Meridian Home Comfort verification code is {six}. It expires in 10 minutes."
    )


def test_format_usd_and_fee_line_amount() -> None:
    cases = {8900: "$89", 12900: "$129", 1250: "$12.50", 125000: "$1,250"}
    cases |= {123456: "$1,234.56", 5: "$0.05", 0: "$0"}
    for cents, expected in cases.items():
        assert format_usd(cents) == expected
    with pytest.raises(ValueError):
        format_usd(-1)
    with pytest.raises(TypeError):
        format_usd(True)
    with pytest.raises(TypeError):
        format_usd(cast(int, 89.0))
    line = render(TextId.FEE_STANDARD_DIAGNOSTIC, amount=format_usd(8900))
    print(line)
    assert line == "Standard diagnostic fee: $89"
    assert render(TextId.FEE_STANDARD_DIAGNOSTIC, amount="$129").endswith("$129")
    assert "$" not in TEXTS[TextId.FEE_STANDARD_DIAGNOSTIC]
    assert not [t for t, v in TEXTS.items() if re.search(r"\$\d", v)]
    number: dict[str, Any] = {"amount": 8900}
    with pytest.raises(TextRenderError):
        render(TextId.FEE_STANDARD_DIAGNOSTIC, **number)
    assert render(TextId.FEE_APPLIES, amount=format_usd(4900)) == (
        "The $49 fee applies under current policy."
    )


def test_templates_use_known_placeholders_only() -> None:
    assert PLACEHOLDERS == {
        "case_ref",
        "due_label",
        "window",
        "digits",
        "rep_name",
        "n",
        "amount",
    }
    for text_id, template in TEXTS.items():
        for _lit, field, spec, conv in string.Formatter().parse(template):
            if field is not None:
                assert field in PLACEHOLDERS, text_id.value
                assert not spec and not conv, text_id.value


def test_greeting_says_automated() -> None:
    greeting = render(TextId.GREETING)
    assert "automated assistant" in greeting
    assert "not a person" in greeting
    assert "Talk to a person" in greeting
    assert "Talk to a person" in render(TextId.ARE_YOU_A_PERSON)
