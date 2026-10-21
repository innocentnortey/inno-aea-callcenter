"""AEA-15: R-46 completion, fact and quote checks (pure; no model, no I/O)."""

from __future__ import annotations

import ast
import datetime as dt
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

import meridian.checks as checks_mod
from meridian.checks import (
    COMPLETION_WORDS,
    GENERIC_COMPLETION_WORDS,
    UNBACKED_COMPLETION_WORDS,
    build_evidence,
    check_completion,
    check_facts,
    check_quotes,
)
from meridian.domain.actions import ActionKind, CompletedAction, Settled
from meridian.domain.common import PassageId, ThreadId, TurnId
from meridian.domain.handoff import BriefExtraction, Quote, SourceRef
from meridian.domain.records import Passage
from meridian.domain.state import ChatLine
from meridian.domain.tools import LookupRow
from meridian.domain.turn import GateKind, TurnFacts

THREAD = ThreadId("3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10")
TURN_3 = TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")
TURN_4 = TurnId("a2b4c6d8-1e3f-4a5b-8c7d-9e0f1a2b3c4d")
DIGIT_THREAD = ThreadId("12345678-1234-4123-8123-123456789012")
NOW = dt.datetime(2026, 10, 16, 10, 12, tzinfo=ZoneInfo("America/Chicago"))

WP4F_DRAFT = "Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta."
WP8_DRAFT = "Done, auto-renew is off. Auto-renewal can be cancelled any time before the renewal date."
WP8_HONEST = (
    "I can't switch off auto-renewal from this chat. "
    "I've created a request for a representative to do it before your renewal date of November 3."
)
SHOWN = {3: "I want a full refund on the repair. It didn't fix anything and I had to call another company."}

B = ActionKind.BOOKED
M = ActionKind.MOVED
C = ActionKind.CANCELLED


def _action(
    kind: ActionKind,
    record_id: str,
    *,
    turn: TurnId = TURN_3,
    records: dict[str, str] | None = None,
    before: dict[str, str] | None = None,
    after: dict[str, str] | None = None,
    thread: ThreadId = THREAD,
) -> CompletedAction:
    return CompletedAction.model_validate(
        {
            "key": {"thread_id": thread, "turn_id": turn, "kind": kind, "record_id": record_id},
            "kind": kind,
            "records": records or {},
            "before": before,
            "after": after,
            "at": NOW,
        }
    )


def _settled(*actions: CompletedAction) -> Settled:
    return Settled(actions=actions, open_case=None, read_at=NOW)


def _facts(**overrides: object) -> TurnFacts:
    base: dict[str, Any] = {
        "turn_id": TURN_4,
        "gate_kind": GateKind.FREE_TEXT,
        "plan_mode": "talk",
        "points": [],
        "passages": [],
        "no_source_tasks": [],
        "windows_shown": [],
        "writes_this_turn": [],
        "change_request": None,
        "handoff": None,
        "escalation": None,
        "identity_step": None,
    }
    base.update(overrides)
    return TurnFacts.model_validate(base)


def _row(row_id: int, result_seen: str, record_ids: tuple[str, ...] = ()) -> LookupRow:
    return LookupRow(
        tool="account_read",
        record_ids=record_ids,
        passage_ids=(),
        result_seen=result_seen,
        message_id=5,
        turn_id=TURN_3,
        id=row_id,
        thread_id=THREAD,
    )


MOVED_T3 = _action(
    M,
    "159",
    records={"appointment": "159", "slot": "56", "old_slot": "159"},
    before={"date": "2026-10-22", "window": "08:00-12:00"},
    after={
        "date": "2026-10-19",
        "window": "08:00-12:00",
        "technician": "Marta Kowalski",
        "service_type": "hvac_repair",
        "fee_line": "fee line (fixture)",
    },
)
WP2_ROW = _row(
    7,
    "INV-204411 2026-10-02 due 2026-11-01 $89.00 $245.00 $144.00 total $478.00",
    ("INV-204411",),
)
FEE_PASSAGE = Passage(
    passage_id=PassageId("pricing/2026_fee_schedule.pdf#2"),
    file="pricing/2026_fee_schedule.pdf",
    section="Fees",
    version_label="undated",
    version_date=None,
    text="Late cancellation (<24h) $49",
    score=0.82,
)


def _every_kind_settled() -> Settled:
    actions = []
    for i, kind in enumerate(ActionKind, start=1):
        if kind in (ActionKind.CASE_OPENED, ActionKind.FOLLOWUP_SAVED):
            recs = {"case": "MHC-C-0009"}
        elif kind is ActionKind.VERIFIED:
            recs = {"customer": "MHC-10001"}
        else:
            recs = {"appointment": str(i)}
        actions.append(_action(kind, str(i), records=recs))
    return _settled(*actions)


def _empty_ev() -> Any:
    return build_evidence(_facts(), _settled(), [])


def test_wp4f_move_from_earlier_turn_passes() -> None:
    r = check_completion(WP4F_DRAFT, _settled(MOVED_T3))
    assert r.text == WP4F_DRAFT
    assert r.removals == ()
    assert r.passed is True


def test_wp8_done_without_write_removed() -> None:
    r = check_completion(WP8_DRAFT, _settled())
    assert r.text == "Auto-renewal can be cancelled any time before the renewal date."
    assert len(r.removals) == 1
    assert r.removals[0].reason == "no_completed_action"
    assert r.removals[0].claim.kind == "completion"
    assert r.passed is False


def test_generic_done_needs_backed_kind() -> None:
    booked = _settled(
        _action(
            B,
            "5",
            records={"appointment": "5"},
            after={"date": "2026-10-20", "window": "08:00-12:00"},
        )
    )
    kept = check_completion("Done, your visit is booked.", booked)
    assert kept.passed and kept.text == "Done, your visit is booked."
    assert check_completion("Done, auto-renew is off.", booked).text == ""
    assert len(check_completion("Done, auto-renew is off.", booked).removals) == 1
    assert check_completion("Done!", booked).text == ""
    assert GENERIC_COMPLETION_WORDS == (
        "done",
        "all set",
        "taken care of",
        "sorted",
        "finished",
        "completed",
        "that's handled",
    )
    for w in GENERIC_COMPLETION_WORDS:
        r = check_completion(w[0].upper() + w[1:] + ".", _settled())
        assert len(r.removals) == 1, w
        assert r.removals[0].claim.action_kind is None
        assert r.removals[0].claim.value.lower() == w
    assert len(check_completion("That’s handled.", _settled()).removals) == 1


def test_r46_words_are_claims() -> None:
    r = check_completion("Your visit is cancelled.", _settled())
    assert len(r.removals) == 1 and r.removals[0].claim.action_kind is C
    assert check_completion(
        "Your visit is cancelled.", _settled(_action(C, "1", records={"appointment": "1"}))
    ).passed
    r = check_completion("Your visit is moved.", _settled())
    assert len(r.removals) == 1 and r.removals[0].claim.action_kind is M
    assert check_completion(
        "Your visit is moved.", _settled(_action(M, "1", records={"appointment": "1"}))
    ).passed
    for text in ("Your payment has been refunded.", "Auto-renew has been turned off."):
        r = check_completion(text, _every_kind_settled())
        assert len(r.removals) == 1, text
        assert r.removals[0].claim.action_kind is None
    assert "cancelled" in COMPLETION_WORDS[C]
    assert "moved" in COMPLETION_WORDS[M]
    assert {"refunded", "turned off"} <= set(UNBACKED_COMPLETION_WORDS)
    assert set(COMPLETION_WORDS) == set(ActionKind)


def test_claim_must_match_named_record() -> None:
    cancel_1 = _settled(
        _action(
            C,
            "1",
            records={"appointment": "1"},
            before={"date": "2026-10-16", "window": "12:00-16:00"},
        )
    )
    assert check_completion("Your October 16 visit is cancelled.", cancel_1).passed
    r = check_completion("Your October 22 visit is cancelled.", cancel_1)
    assert not r.passed and r.removals[0].claim.action_kind is C
    assert check_completion("Appointment 1 is cancelled.", cancel_1).passed
    assert not check_completion("Appointment 2 is cancelled.", cancel_1).passed
    cross = _settled(
        _action(
            B,
            "3",
            records={"appointment": "3"},
            after={"date": "2026-10-23", "window": "08:00-12:00"},
        ),
        _action(C, "3", records={"appointment": "3"}),
    )
    assert check_completion("Your October 23 visit is cancelled.", cross).passed


def test_only_turn_reading_same_function() -> None:
    r = check_completion(WP4F_DRAFT, _settled(MOVED_T3).only_turn(TURN_4))
    assert r.text == ""
    assert len(r.removals) == 1
    assert r.removals[0].claim.action_kind is M
    assert r.passed is False


def test_wp2_fact_check_amounts() -> None:
    ev = build_evidence(_facts(), _settled(), [WP2_ROW])
    text = (
        "Invoice INV-204411 is due November 1. The total is $478.00. "
        "The after-hours dispatch line is $144. The after-hours line is $149."
    )
    r = check_facts(text, ev)
    assert r.text == (
        "Invoice INV-204411 is due November 1. The total is $478.00. The after-hours dispatch line is $144."
    )
    assert len(r.removals) == 1
    assert r.removals[0].claim.kind == "amount"
    assert r.removals[0].claim.value == "14900"
    assert r.removals[0].reason == "not_in_evidence"


def test_chat_evidence_only_for_brief() -> None:
    chat = (
        ChatLine(speaker="customer", text="The tech has come out 3 times already.", turn_id=TURN_3, at=NOW),
        ChatLine(speaker="assistant", text="I'm sorry to hear that.", turn_id=TURN_3, at=NOW),
    )
    text = "The technician has visited 3 times."
    r = check_facts(text, build_evidence(_facts(), _settled(), []))
    assert not r.passed
    assert r.removals[0].claim.kind == "number" and r.removals[0].claim.value == "3"
    ev = build_evidence(_facts(), _settled(), [], chat)
    assert check_facts(text, ev).passed
    assert ev.sources["number:3"] == SourceRef(kind="message", ref=str(TURN_3))


def test_quote_must_be_exact_substring() -> None:
    extraction = BriefExtraction(
        needs=[Quote(message_id=3, text="I want a full refund on the repair.")],
        claims=[
            Quote(message_id=3, text="It didn't fix anything"),
            Quote(message_id=3, text="It did not fix anything"),
            Quote(message_id=4, text="I had to call another company"),
            Quote(message_id=3, text="I had to call another company"),
        ],
        open_decision="Decide whether to refund the repair.",
    )
    q = check_quotes(extraction, SHOWN)
    assert q.needs == (extraction.needs[0],)
    assert q.claims == (extraction.claims[0], extraction.claims[3])
    assert len(q.removals) == 2
    assert all(r.reason == "quote_not_found" and r.claim.kind == "quote" for r in q.removals)
    assert [r.claim.value for r in q.removals] == ["3", "4"]
    assert q.removals[0].claim.span == (0, len(extraction.claims[1].text))
    assert q.removals[1].claim.span == (0, len(extraction.claims[2].text))
    assert q.passed is False


def test_all_removed_and_clean_results() -> None:
    r = check_completion("Done! It's moved.", _settled())
    assert r.text == "" and len(r.removals) == 2 and r.passed is False
    r = check_completion("Thanks for waiting.", _settled())
    assert r.passed is True and r.removals == ()
    ev = _empty_ev()
    r = check_facts("The fee is $12.", ev)
    assert r.text == "" and r.passed is False
    assert check_facts("Thanks.", ev).passed is True


def test_removed_value_absent_from_text_and_logs(
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    with caplog.at_level(logging.DEBUG):
        r = check_facts("Your balance is $913.37. Thanks for waiting.", _empty_ev())
        c = check_completion("Done, your $913.37 refund is sorted.", _settled())
    assert r.text == "Thanks for waiting."
    assert "913.37" not in r.text
    assert "913" not in caplog.text
    assert caplog.records == []
    assert c.text == ""
    out = capsys.readouterr()
    assert out.out == "" and out.err == ""
    src = Path(checks_mod.__file__).read_text(encoding="utf-8")
    assert "CheckEvent" not in src
    assert "import logging" not in src
    assert "print(" not in src


def test_checks_module_is_pure() -> None:
    src = Path(checks_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden = {
        "logging", "os", "io", "pathlib", "subprocess", "socket", "sqlite3", "shutil", "tempfile",
        "urllib", "http", "asyncio", "time", "random", "sys",
    }  # fmt: skip
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            names = [node.module or ""]
        for name in names:
            top = name.split(".")[0]
            assert (
                top in sys.stdlib_module_names or top == "__future__" or name.startswith("meridian.domain")
            ), name
            assert top not in forbidden, name
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "print", "input", "exec", "eval", "__import__"}
    assert ".now(" not in src and ".today(" not in src and "utcnow" not in src
    code = "import sys, meridian.checks; print('\\n'.join(sorted(m for m in sys.modules if m.startswith('meridian'))))"
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.split()
    print(out)
    for banned in ("meridian.services", "meridian.agent", "meridian.adapters", "meridian.web"):
        assert not [m for m in out if m.startswith(banned)], banned


def test_wp8_honest_limit_reply_passes_with_case() -> None:
    case = _settled(
        _action(ActionKind.CASE_OPENED, "MHC-C-0009", turn=TURN_4, records={"case": "MHC-C-0009"})
    )
    r = check_completion(WP8_HONEST, case)
    assert r.passed and r.text == WP8_HONEST
    r = check_completion(WP8_HONEST, _settled())
    assert r.text == "I can't switch off auto-renewal from this chat."
    assert len(r.removals) == 1 and r.removals[0].claim.action_kind is ActionKind.CASE_OPENED
    row = _row(8, "MHC-10001 standard renewal 2026-11-03", ("MHC-10001",))
    assert check_facts(WP8_HONEST, build_evidence(_facts(), case, [row])).passed


def test_wp4f_facts_match_settled() -> None:
    r = check_facts(WP4F_DRAFT, build_evidence(_facts(), _settled(MOVED_T3), []))
    assert r.passed and r.text == WP4F_DRAFT
    assert check_facts(WP4F_DRAFT, build_evidence(_facts(), _settled(), [])).text == ""


@pytest.mark.parametrize(
    "text",
    [
        "Your visit has not been moved.",
        "It isn't cancelled yet.",
        "Once you're verified, I can read your invoice.",
        "Would you like it moved to Monday?",
        "Do you want it cancelled?",
        "I'll let you know when it's done.",
        "There's no visit booked for that day.",
        "I can't switch off auto-renewal from this chat.",
        "Your tune-up is scheduled for today.",
        "The diagnostic fee is credited toward the repair if approved at the same visit.",
    ],
    ids=[f"neg{i}" for i in range(10)],
)
def test_negated_and_conditional_words_are_not_claims(text: str) -> None:
    r = check_completion(text, _settled())
    assert r.passed and r.text == text


@pytest.mark.parametrize(
    ("text", "kind", "value"),
    [
        ("It costs $1,250.50.", "amount", "125050"),
        ("Your invoice is INV-999999.", "id", "INV-999999"),
        ("See mhc-c-0042 for details.", "id", "MHC-C-0042"),
        ("See you October 5.", "date", "--10-05"),
        ("See you Oct. 5th, 2026.", "date", "2026-10-05"),
        ("It was on 2026-10-05.", "date", "2026-10-05"),
        ("It was on 10/5.", "date", "--10-05"),
        ("Arrive at 4pm.", "time", "16:00"),
        ("Arrive at 4:30 p.m.", "time", "16:30"),
        ("The window is 12–4pm.", "time", "12:00"),
        ("Arrive at 14:30.", "time", "14:30"),
        ("Arrive at noon.", "time", "12:00"),
        ("You have 17 visits.", "number", "17"),
        ("It takes 2.50 hours.", "number", "2.5"),
    ],
    ids=[f"fact{i}" for i in range(14)],
)
def test_fact_claim_kinds_and_values(text: str, kind: str, value: str) -> None:
    r = check_facts(text, _empty_ev())
    assert len(r.removals) == 1
    assert (r.removals[0].claim.kind, r.removals[0].claim.value) == (kind, value)


def test_sentence_split_keeps_abbreviations_and_decimals() -> None:
    text = "Marta arrives 8:00 a.m. to 12:00 p.m. on October 19. The fee is $89.00.\nThanks!"
    r = check_facts(text, build_evidence(_facts(), _settled(MOVED_T3), []))
    assert r.text == "Marta arrives 8:00 a.m. to 12:00 p.m. on October 19.\nThanks!"
    assert len(r.removals) == 1
    assert (r.removals[0].claim.kind, r.removals[0].claim.value) == ("amount", "8900")


def test_evidence_sources_and_skipped_keys() -> None:
    write = _action(
        B,
        "6",
        turn=TURN_4,
        thread=DIGIT_THREAD,
        records={"appointment": "6"},
        after={"date": "2026-10-20", "window": "12:00-16:00"},
    )
    ev = build_evidence(_facts(passages=[FEE_PASSAGE], writes_this_turn=[write]), _settled(), [WP2_ROW])
    assert 4900 in ev.amounts_cents
    assert 47800 in ev.amounts_cents
    assert "INV-204411" in ev.ids
    assert dt.date(2026, 10, 20) in ev.dates
    assert "24" in ev.numbers
    assert ev.sources["id:INV-204411"] == SourceRef(kind="lookup_log", ref="7")
    assert ev.sources["amount:4900"] == SourceRef(kind="policy_row", ref="pricing/2026_fee_schedule.pdf#2")
    assert ev.sources["date:2026-10-20"].kind == "action"
    assert "12345678" not in ev.numbers and "123456789012" not in ev.numbers
    assert "0.82" not in ev.numbers
    assert check_facts("A $49 fee applies to changes within 24 hours.", ev).passed is True


def test_numbers_derived_from_times_dates_amounts() -> None:
    ev = build_evidence(_facts(), _settled(MOVED_T3), [_row(9, "late change fee $49.00")])
    assert check_facts("Marta will arrive between 8 and 12 on the 19th.", ev).passed is True
    assert check_facts("That is a 49 dollar fee.", ev).passed is True
    assert check_facts("That is a 48 dollar fee.", ev).passed is False


def test_one_removal_per_removed_sentence() -> None:
    r = check_completion("Done, it's cancelled and refunded.", _settled())
    assert len(r.removals) == 1 and r.removals[0].claim.value == "Done"
    r = check_facts("It's $5 on October 2.", _empty_ev())
    assert len(r.removals) == 1 and r.removals[0].claim.kind == "amount"


def test_empty_inputs() -> None:
    for r in (check_completion("", _settled()), check_facts("", _empty_ev())):
        assert r.text == "" and r.removals == () and r.passed is True
    ev = _empty_ev()
    assert not (ev.amounts_cents or ev.dates or ev.times or ev.ids or ev.numbers)
    assert ev.sources == {}
    q = check_quotes(BriefExtraction.model_construct(needs=[], claims=[], open_decision=""), {})
    assert q.passed is True and q.needs == () and q.claims == () and q.removals == ()


def test_empty_quote_removed() -> None:
    extraction = BriefExtraction.model_construct(
        needs=[Quote.model_construct(message_id=3, text="")], claims=[], open_decision=""
    )
    q = check_quotes(extraction, SHOWN)
    assert q.needs == ()
    assert len(q.removals) == 1 and q.removals[0].reason == "quote_not_found"
