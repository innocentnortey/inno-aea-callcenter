"""Specialist wording tests (AEA-35 AC-11, AC-21, AC-22). Synthetic values only."""

from __future__ import annotations

import re
import secrets
from datetime import datetime

import pytest

from meridian.agent.prompts.specialists import (
    ACCOUNT_PREFIX,
    KNOWLEDGE_PREFIX,
    RULE_NEVER_TALK,
    RULE_NO_CARDS,
    RULE_NO_FIRM_PRICES,
    RULE_REPORT_ONLY,
    SCHEDULING_PREFIX,
    TASK_LABELS,
)
from meridian.agent.specialists.specs import SPECS
from meridian.domain.turn import SpecialistKind, TaskIntent
from meridian.privacy.redact import RedactionProfile, redact
from tests.fakes import CHICAGO, InMemoryTraceSink
from tests.unit.agent.specialists._doubles import (
    SLOT_44,
    SLOT_61,
    TURN_1,
    make_task,
    scheduling_slice,
    turn_ctx,
)


@pytest.mark.parametrize("kind", ["knowledge", "account", "scheduling"])
def test_requests_carry_no_secret_values(kind: SpecialistKind) -> None:
    code = f"{secrets.randbelow(10**6):06d}"
    card = "4" + "".join(str(secrets.randbelow(10)) for _ in range(15))
    phone = "512-555-" + f"{secrets.randbelow(10**4):04d}"
    raw = f"my code is {code}, card {card}, call {phone}"
    masked = redact(raw, RedactionProfile.SONNET).text
    slice_ = scheduling_slice(shown=(SLOT_44,)) if kind == "scheduling" else None
    now = datetime(2031, 3, 4, 9, 30, tzinfo=CHICAGO)
    sink = InMemoryTraceSink()
    server_now = datetime.now(CHICAGO)
    server_date = f"{server_now:%B} {server_now.day}, {server_now.year}"
    with turn_ctx(sink, now=now) as ctx:
        for text in (masked, raw):
            task = make_task(
                kind,
                TaskIntent.ANSWER_QUESTION,
                text,
                messages=("[code entered]", "[card number removed]", "[phone ending 02]"),
                slice_=slice_,
            )
            prefix, dynamic, user = SPECS[kind].render(task, ctx)
            whole = "\n".join((prefix, dynamic, user))
            assert code not in whole
            assert card not in whole
            assert phone not in whole
            assert re.search(r"(?<!\d)\d{6}(?!\d)", whole) is None
            assert re.search(r"\d(?:[ -]?\d){12,18}", whole) is None
            assert re.search(r"\d{3}[ .-]?\d{3}[ .-]?\d{4}", whole) is None
            assert "Tuesday, March 4, 2031" in dynamic
            assert server_date not in dynamic


def test_prefix_rules_present() -> None:
    for prefix in (KNOWLEDGE_PREFIX, ACCOUNT_PREFIX, SCHEDULING_PREFIX):
        for rule in (RULE_NEVER_TALK, RULE_REPORT_ONLY, RULE_NO_FIRM_PRICES, RULE_NO_CARDS, "report_facts"):
            assert rule in prefix
        assert re.search(r"\$\d", prefix) is None
    assert "12-month minimum" in KNOWLEDGE_PREFIX
    assert "kb_search" in KNOWLEDGE_PREFIX
    assert "read_invoices" in ACCOUNT_PREFIX
    assert "as billed" in ACCOUNT_PREFIX
    assert "Never judge whether a charge is right" in ACCOUNT_PREFIX
    assert "never move or cancel that visit" in SCHEDULING_PREFIX
    for name in ("move_visit", "book_visit", "find_windows"):
        assert name not in SCHEDULING_PREFIX


def test_task_labels_cover_every_intent() -> None:
    assert set(TASK_LABELS) == set(TaskIntent)
    assert all(TASK_LABELS.values())


def test_scheduling_state_omits_turn_ids() -> None:
    task = make_task(
        "scheduling",
        TaskIntent.BOOK_NEW,
        "I need a visit",
        slice_=scheduling_slice(shown=(SLOT_44, SLOT_61)),
    )
    sink = InMemoryTraceSink()
    with turn_ctx(sink) as ctx:
        _, _, user = SPECS["scheduling"].render(task, ctx)
    assert "shown_turn" not in user
    assert str(TURN_1) not in user
    assert "[card number removed]" not in user
    assert '"slot_id": 44' in user
    assert '"slot_id": 61' in user


def test_user_text_budget() -> None:
    messages = tuple(f"m{i} " + "x" * 1495 for i in range(10))
    task = make_task("knowledge", TaskIntent.ANSWER_QUESTION, "latest question", messages=messages)
    sink = InMemoryTraceSink()
    with turn_ctx(sink) as ctx:
        _, _, user = SPECS["knowledge"].render(task, ctx)
    lines = [ln for ln in user.split("\n") if ln.startswith("- ")]
    assert len(lines) == 6
    # keep the last 6 of the history, append the latest, keep the last 6: m5..m9, then the latest
    assert [ln[2:4] for ln in lines[:5]] == [f"m{i}" for i in range(5, 10)]
    assert lines[-1] == "- latest question"
    for ln in lines[:-1]:
        assert ln.endswith("…")
    assert all(len(ln) <= len("- ") + 1000 for ln in lines)
