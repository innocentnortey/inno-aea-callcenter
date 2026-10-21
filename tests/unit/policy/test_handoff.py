"""AEA-14: promises, due times, priorities (policy/handoff.py)."""

from __future__ import annotations

import ast
import re
import typing
from collections.abc import Callable, Iterator
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from meridian.domain.handoff import HandoffReason, Priority, Promise
from meridian.policy.handoff import (
    D4_ROWS,
    DUE_SOON_WINDOW,
    PROMISE_TABLE,
    STAFF_GUIDANCE_FOR,
    UNOWNED_AFTER,
    PolicyRow,
    business_due,
    case_due_at,
    due_label,
    is_business_day,
    phone_support_open,
    priority_for,
    promise_for,
)
from meridian.policy.texts import TEXTS, TextId, render

CHI = ZoneInfo("America/Chicago")
ROOT = Path(__file__).resolve().parents[3]
R = HandoffReason


def at(y: int, mo: int, d: int, h: int = 10, mi: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=CHI)


FRI_10 = at(2026, 10, 16)
CANT_12 = (
    "I can't promise anyone will confirm a change before your appointment starts; "
    "until a representative confirms, please plan on the technician arriving 12:00 pm – 4:00 pm."
)
PHONE = "Phone support is open until 7:00 pm today if you'd like to call."


def test_business_due_after_hours() -> None:
    cases = [
        (FRI_10, 1, at(2026, 10, 19, 19)),
        (FRI_10, 2, at(2026, 10, 20, 19)),
        (at(2026, 10, 16, 20), 1, at(2026, 10, 19, 19)),
        (at(2026, 10, 19, 8), 1, at(2026, 10, 20, 19)),
    ]
    for now, days, expected in cases:
        got = business_due(now, days)
        assert got == expected
        assert got.utcoffset() == timedelta(hours=-5)


def test_business_due_weekend() -> None:
    assert business_due(at(2026, 10, 17), 1) == at(2026, 10, 19, 19)
    assert business_due(at(2026, 10, 18), 1) == at(2026, 10, 19, 19)
    assert not is_business_day(date(2026, 10, 17))
    assert not is_business_day(date(2026, 10, 18))
    assert is_business_day(date(2026, 10, 19))


def test_business_due_thanksgiving() -> None:
    got = business_due(at(2026, 11, 25), 1)
    assert got == datetime(2026, 11, 30, 19, 0, tzinfo=CHI)
    assert got.utcoffset() == timedelta(hours=-6)
    assert not is_business_day(date(2026, 11, 26))
    assert not is_business_day(date(2026, 11, 27))


def test_business_due_short_day_and_new_year() -> None:
    assert business_due(at(2026, 12, 23), 1) == datetime(2026, 12, 24, 12, 0, tzinfo=CHI)
    assert business_due(at(2026, 12, 24), 1) == datetime(2026, 12, 28, 19, 0, tzinfo=CHI)
    assert business_due(at(2026, 12, 31), 1) == datetime(2027, 1, 4, 19, 0, tzinfo=CHI)
    assert is_business_day(date(2026, 12, 24))


def test_phone_support_hours() -> None:
    assert phone_support_open(at(2026, 10, 16, 10)) is True
    assert phone_support_open(at(2026, 10, 16, 19, 30)) is False
    assert phone_support_open(at(2026, 10, 17, 9)) is True
    assert phone_support_open(at(2026, 10, 18, 10)) is False
    assert phone_support_open(at(2026, 12, 25, 10)) is False
    assert phone_support_open(at(2026, 12, 24, 13)) is False


def test_naive_times_and_bad_days_refused() -> None:
    naive = datetime(2026, 10, 16, 10)
    calls: list[Callable[[], object]] = [
        lambda: business_due(naive, 1),
        lambda: phone_support_open(naive),
        lambda: due_label(naive),
        lambda: promise_for(R.REFUND, "nobody_online", naive),
    ]
    for call in calls:
        with pytest.raises(ValueError) as exc:
            call()
        assert not re.search(r"\d", str(exc.value))
    with pytest.raises(ValueError):
        business_due(FRI_10, 0)
    utc = FRI_10.astimezone(ZoneInfo("UTC"))
    assert business_due(utc, 1) == business_due(FRI_10, 1)


def test_due_label_format() -> None:
    assert due_label(at(2026, 10, 19, 19)) == "Monday, October 19, 7:00 pm"
    assert due_label(at(2026, 10, 20, 8)) == "Tuesday, October 20, 8:00 am"
    assert due_label(at(2026, 12, 24, 12)) == "Thursday, December 24, 12:00 pm"
    assert due_label(at(2026, 11, 2, 0, 5)) == "Monday, November 2, 12:05 am"


_SPECIAL = {R.SAFETY, R.DANGER, R.BURNING_UNCLEAR, R.REFUND, R.FEE_BEARING_CHANGE}


def test_unstaffed_promise_and_due() -> None:
    for reason in R:
        if reason in _SPECIAL:
            continue
        p = promise_for(reason, "nobody_online", FRI_10)
        assert p.policy_row == "R26.unstaffed"
        assert p.text == PROMISE_TABLE["R26.unstaffed"]
        assert p.due_at == at(2026, 10, 19, 19)
        assert p.due_at is not None
        assert p.due_at.isoformat() == "2026-10-19T19:00:00-05:00"
        assert p.due_label == "Monday, October 19, 7:00 pm"
        assert p.extra_lines == ()
        assert p.live_queued is False


def test_wp7_refund_promise() -> None:
    p = promise_for(R.REFUND, "nobody_online", FRI_10)
    assert p.policy_row == "R26.refund"
    assert p.text == "A representative will get to your refund request within 2 business days."
    assert p.due_at is not None
    assert p.due_at.isoformat() == "2026-10-20T19:00:00-05:00"
    assert p.due_label == "Tuesday, October 20, 7:00 pm"
    assert p.extra_lines == ("I can't promise an outcome.",)
    assert p.live_queued is False
    assert priority_for(R.REFUND) is Priority.P3


def test_staffed_promise() -> None:
    for reason in (R.REFUND, R.DANGER):
        p = promise_for(reason, "simulated_on_shift", FRI_10)
        assert p.policy_row == "R26.staffed"
        assert p.text == TEXTS[TextId.PROMISE_STAFFED]
        assert p.text.startswith("A representative will join this chat when available")
        assert p.due_at is None
        assert p.due_label is None
        assert p.live_queued is True
        assert p.extra_lines == ()


def test_safety_promises_no_time() -> None:
    for presence in ("nobody_online", "simulated_on_shift"):
        p = promise_for(R.SAFETY, presence, FRI_10)
        assert p.policy_row == "R26.safety_none"
        assert p.text == ""
        assert p.due_at is None
        assert p.due_label is None
        assert p.live_queued is False
    assert priority_for(R.SAFETY) is Priority.P0


def test_p1_danger_review_line() -> None:
    for reason in (R.DANGER, R.BURNING_UNCLEAR):
        p = promise_for(reason, "nobody_online", FRI_10)
        assert p.policy_row == "OD4.danger_review"
        assert p.text == TEXTS[TextId.PROMISE_DANGER_REVIEW]
        assert p.due_at == at(2026, 10, 19, 19)
        assert p.extra_lines == ()
        assert PROMISE_TABLE["R26.unstaffed"] not in (p.text, *p.extra_lines)


def test_wp4_fee_bearing_lines_and_case_due() -> None:
    window = at(2026, 10, 16, 12)
    p = promise_for(R.FEE_BEARING_CHANGE, "nobody_online", FRI_10, window)
    assert p.policy_row == "R26.unstaffed"
    assert p.due_at == at(2026, 10, 19, 19)
    assert p.extra_lines == (CANT_12, PHONE)
    assert p.due_at != window
    assert case_due_at(R.FEE_BEARING_CHANGE, p, window) == window

    sun = at(2026, 10, 18)
    p = promise_for(R.FEE_BEARING_CHANGE, "nobody_online", sun, at(2026, 10, 19, 12))
    assert p.extra_lines == (CANT_12,)

    p = promise_for(R.FEE_BEARING_CHANGE, "nobody_online", FRI_10, at(2026, 10, 20, 8))
    assert p.extra_lines == (PHONE,)

    for r in R:
        if r in (R.FEE_BEARING_CHANGE, R.BURNING_RULED_OUT):
            continue
        pr = promise_for(r, "nobody_online", FRI_10, window)
        assert case_due_at(r, pr, window) == pr.due_at

    # CAS-16 option A
    pb = promise_for(R.BURNING_RULED_OUT, "nobody_online", FRI_10, window)
    assert pb.policy_row == "R26.unstaffed"
    assert pb.extra_lines == ()
    assert case_due_at(R.BURNING_RULED_OUT, pb, window) == window
    assert case_due_at(R.BURNING_RULED_OUT, pb, None) == pb.due_at
    pf = promise_for(R.FEE_BEARING_CHANGE, "nobody_online", FRI_10)
    assert case_due_at(R.FEE_BEARING_CHANGE, pf, None) == pf.due_at


def test_fee_bearing_phone_line_never_false() -> None:
    sat = at(2026, 10, 17, 9)
    assert phone_support_open(sat)
    p = promise_for(R.FEE_BEARING_CHANGE, "nobody_online", sat, at(2026, 10, 19, 8))
    assert p.extra_lines == (render(TextId.FEE_CANT_GUARANTEE, window="8:00 am – 12:00 pm"),)
    p = promise_for(R.FEE_BEARING_CHANGE, "nobody_online", at(2026, 12, 24, 10), at(2026, 12, 28, 8))
    assert PHONE not in p.extra_lines
    p = promise_for(R.FEE_BEARING_CHANGE, "simulated_on_shift", FRI_10, at(2026, 10, 16, 12))
    assert p.extra_lines == (PHONE,)
    assert p.due_at is None


def test_window_text_from_issued_windows() -> None:
    expected = {
        8: "8:00 am – 12:00 pm",
        12: "12:00 pm – 4:00 pm",
        13: "1:00 pm – 5:00 pm",
        16: "4:00 pm – 7:00 pm",
    }
    for hour, text in expected.items():
        p = promise_for(R.FEE_BEARING_CHANGE, "nobody_online", FRI_10, at(2026, 10, 19, hour))
        assert render(TextId.FEE_CANT_GUARANTEE, window=text) in p.extra_lines
    with pytest.raises(ValueError):
        promise_for(R.FEE_BEARING_CHANGE, "nobody_online", FRI_10, at(2026, 10, 19, 9))


_ROW_TEXT_IDS = {
    "R26.unstaffed": TextId.PROMISE_UNSTAFFED,
    "R26.refund": TextId.PROMISE_REFUND,
    "R26.staffed": TextId.PROMISE_STAFFED,
    "R26.safety_none": TextId.PROMISE_SAFETY_NONE,
    "OD4.danger_review": TextId.PROMISE_DANGER_REVIEW,
}
_CLOCKS = [
    FRI_10,
    at(2026, 10, 16, 20),
    at(2026, 10, 17, 9),
    at(2026, 10, 18, 10),
    at(2026, 12, 24, 10),
]


def _grid() -> Iterator[Promise]:
    for reason in R:
        for presence in ("nobody_online", "simulated_on_shift"):
            for now in _CLOCKS:
                for window in (None, at(2026, 10, 16, 12)):
                    yield promise_for(reason, presence, now, window)


def test_promise_texts_are_the_table() -> None:
    assert set(PROMISE_TABLE) == set(typing.get_args(PolicyRow))
    for row, tid in _ROW_TEXT_IDS.items():
        assert PROMISE_TABLE[row] == TEXTS[tid]  # type: ignore[index]
    values = set(PROMISE_TABLE.values())
    for p in _grid():
        assert p.text in values


def test_priority_per_reason() -> None:
    expected = {
        R.SAFETY: Priority.P0,
        R.DANGER: Priority.P1,
        R.BURNING_UNCLEAR: Priority.P1,
        R.FEE_BEARING_CHANGE: Priority.P2,
        R.LATE_TECHNICIAN: Priority.P2,
        R.BURNING_RULED_OUT: Priority.P2,
        R.UNSUPPORTED_ACTION: Priority.P4,
        R.CUSTOMER_REQUESTED_PERSON: Priority.P3,
        R.REFUND: Priority.P3,
        R.BILLING_DISPUTE: Priority.P3,
        R.COMPLAINT_OR_MANAGER: Priority.P3,
        R.LEGAL_OR_CHARGEBACK: Priority.P3,
        R.COMMERCIAL: Priority.P3,
        R.IDENTITY_UNVERIFIED: Priority.P3,
        R.AI_FAILURE: Priority.P3,
    }
    assert set(expected) | {R.MEMBERSHIP_CANCEL} == set(R)
    for reason, prio in expected.items():
        assert priority_for(reason) is prio
    due = at(2026, 10, 19, 19)
    assert priority_for(R.MEMBERSHIP_CANCEL) is Priority.P3
    assert priority_for(R.MEMBERSHIP_CANCEL, promise_due=due, renewal_date=date(2026, 11, 3)) is Priority.P3
    assert priority_for(R.MEMBERSHIP_CANCEL, promise_due=due, renewal_date=date(2026, 10, 19)) is Priority.P2
    assert priority_for(R.MEMBERSHIP_CANCEL, promise_due=due, renewal_date=date(2026, 10, 18)) is Priority.P2


def test_thresholds_values() -> None:
    assert DUE_SOON_WINDOW == timedelta(hours=4)
    assert UNOWNED_AFTER == timedelta(minutes=30)


def _parse_d4() -> list[tuple[str, str, str, str | None]]:
    doc = ROOT / "docs/analysis/2026-10-20-human-handoff-consolidated-direction.md"
    lines = doc.read_text(encoding="utf-8").splitlines()
    start = lines.index("### 9.4 Requests the issued systems cannot complete (D4)")
    end = lines.index("### 9.5 Follow-up channel (OD-5)")
    out = []
    for line in lines[start:end]:
        if not line.startswith("| **"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        m = re.fullmatch(r"\*\*(.+?)\*\* \((.+)\)", cells[0])
        assert m is not None
        case = cells[-1].replace("**", "")
        t = re.match(r"^(P4 only if (?:the customer accepts|accepted)|None|P[0-4])", case)
        assert t is not None
        token = t.group(1)
        rule = (
            "p4_if_accepted"
            if token.startswith("P4 only if")
            else {"None": "none", "P2": "p2", "P3": "p3", "P4": "p4"}[token]
        )
        note = case[len(token) :].lstrip(" ;,") or None
        out.append((m.group(1), m.group(2), rule, note))
    return out


def test_d4_rows_and_staff_guidance() -> None:
    parsed = _parse_d4()
    assert len(parsed) == 15
    assert [(r.request, r.evidence, r.case_rule, r.note) for r in D4_ROWS] == parsed
    assert set(STAFF_GUIDANCE_FOR) == {
        R.FEE_BEARING_CHANGE,
        R.LATE_TECHNICIAN,
        R.BILLING_DISPUTE,
        R.COMPLAINT_OR_MANAGER,
        R.REFUND,
    }
    kb = (
        ROOT / "docs/data/issued/meridian_dataset/knowledge_base/internal/agent_discretion_notes.md"
    ).read_text(encoding="utf-8")
    for prefixes in STAFF_GUIDANCE_FOR.values():
        for prefix in prefixes:
            assert prefix in kb


def _is_promise_name(node: ast.expr) -> bool:
    return (isinstance(node, ast.Name) and node.id == "Promise") or (
        isinstance(node, ast.Attribute) and node.attr == "Promise"
    )


def test_promise_construction_and_no_staff_text() -> None:
    src = ROOT / "src/meridian"
    handoff = src / "policy/handoff.py"
    for path in src.rglob("*.py"):
        if path == handoff:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            assert not _is_promise_name(node.func), f"Promise( in {path}"
            f = node.func
            assert not (
                isinstance(f, ast.Attribute) and _is_promise_name(f.value) and f.attr == "model_construct"
            ), f"Promise.model_construct in {path}"
    calls = [
        n
        for n in ast.walk(ast.parse(handoff.read_text(encoding="utf-8")))
        if isinstance(n, ast.Call) and _is_promise_name(n.func)
    ]
    assert len(calls) == 1

    banned = re.compile(r"\b(waive|discount|refunded|sent)\b", re.I)
    prefixes = [p for ps in STAFF_GUIDANCE_FOR.values() for p in ps]
    for p in _grid():
        for text in (p.text, *p.extra_lines):
            assert not any(pre in text for pre in prefixes)
            assert not banned.search(text)
