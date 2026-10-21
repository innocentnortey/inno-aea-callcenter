"""AEA-29 Step 1: the pure case rules (allowed actions, refusals, due state, order, lanes, labels, masking)."""

from __future__ import annotations

import datetime as dt
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from meridian.domain.common import ApiErrorCode
from meridian.domain.handoff import HandoffReason, Priority
from meridian.domain.identity import IdentityState
from meridian.domain.staff import ROLE_ACTIONS, StaffRole
from meridian.domain.tools import LookupRow
from meridian.domain.views import CaseAction
from meridian.policy.texts import TEXTS, TextId
from meridian.services._case_rules import (
    CON13_ACTIONS,
    actions_for,
    age_label,
    case_due_label,
    con13_refusal,
    due_state,
    follow_up_short,
    identity_view,
    lane_for,
    mask,
    missing_field_refusal,
    parse_seen,
    queue_key,
    reason_label,
    record_kind,
    row_title,
    staffing_view,
)
from tests.fixtures.sqlite import temp_sqlite
from tests.services._allowed_actions_table import REPRESENTATIVE_EXAMPLES, TABLE

CHI = ZoneInfo("America/Chicago")
NOW = dt.datetime(2026, 10, 16, 10, 0, tzinfo=CHI)


def _at(minutes: int) -> dt.datetime:
    return NOW + dt.timedelta(minutes=minutes)


@pytest.mark.parametrize("row", TABLE, ids=[r[0] for r in TABLE])
def test_state_allows_and_refusal_agree(row: tuple[Any, ...]) -> None:
    """Every table row, role and CON-13 action: accepted exactly when the action is listed."""
    _, lifecycle, owner, live, staffing, *_ = row
    for role in (StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR, StaffRole.OWNER):
        listed = actions_for(
            lifecycle=lifecycle, owner_role=owner, live_state=live, staffing=staffing, actor_role=role
        )
        for action in CON13_ACTIONS:
            refusal = con13_refusal(
                action, lifecycle=lifecycle, owner_role=owner, owner_since=NOW, actor_role=role
            )
            assert (refusal is None) == (action in listed), (row[0], role, action)


def test_actions_for_examples_and_owner() -> None:
    for name, (lifecycle, owner, live, staffing, expected) in REPRESENTATIVE_EXAMPLES.items():
        got = actions_for(
            lifecycle=lifecycle,
            owner_role=owner,
            live_state=live,
            staffing=staffing,
            actor_role=StaffRole.REPRESENTATIVE,
        )
        assert list(got) == expected, name
    assert ROLE_ACTIONS[StaffRole.OWNER] == frozenset()
    assert (
        actions_for(
            lifecycle="unassigned",
            owner_role=None,
            live_state="not_live",
            staffing="nobody_online",
            actor_role=StaffRole.OWNER,
        )
        == ()
    )


def _action(name: str, **kw: Any) -> CaseAction:
    return CaseAction.model_validate({"action": name, "expected_version": 1, **kw})


def test_missing_field_refusal() -> None:
    cases = [
        (_action("release"), ApiErrorCode.REASON_REQUIRED, "reason", "required for release"),
        (_action("close_unresolved", reason="  "), ApiErrorCode.REASON_REQUIRED, "reason", None),
        (_action("wait"), ApiErrorCode.WAKE_UP_REQUIRED, "wake_up_at", "required for wait"),
        (
            _action("wait", wake_up_at=_at(-1)),
            ApiErrorCode.VALIDATION_ERROR,
            "wake_up_at",
            "must be after the demo time",
        ),
        (_action("resolve"), ApiErrorCode.OUTCOME_REQUIRED, "outcome", "required for resolve"),
        (_action("assign", reason="why"), ApiErrorCode.VALIDATION_ERROR, "assignee", "required for assign"),
        (
            _action("change_priority", reason="why"),
            ApiErrorCode.VALIDATION_ERROR,
            "priority",
            "required for change_priority",
        ),
    ]
    for action, code, field, constraint in cases:
        got = missing_field_refusal(action, NOW)
        assert got is not None and got.code == code and got.field == field, action
        assert got.details is None
        if constraint:
            assert got.constraint == constraint
    assert missing_field_refusal(_action("wait", wake_up_at=_at(60)), NOW) is None
    assert missing_field_refusal(_action("claim"), NOW) is None
    assert missing_field_refusal(_action("resolve", outcome="done"), NOW) is None


def test_due_state_boundaries() -> None:
    assert due_state(None, NOW) == "no_due_time"
    assert due_state(_at(-1), NOW) == "overdue"
    assert due_state(_at(240), NOW) == "due_soon"
    assert due_state(_at(241), NOW) == "on_time"


def test_queue_key_order() -> None:
    mon = dt.datetime(2026, 10, 19, 19, 0, tzinfo=CHI)
    rows = [
        ("p3-none", Priority.P3, "no_due_time", None, _at(-10)),
        ("p3-late-b", Priority.P3, "on_time", mon, _at(-26)),
        ("p3-late-a", Priority.P3, "on_time", mon, _at(-46)),
        ("p3-overdue", Priority.P3, "overdue", _at(-30), _at(-100)),
        ("p0", Priority.P0, "no_due_time", None, _at(-5)),
    ]
    ordered = sorted(rows, key=lambda r: queue_key(r[1], r[2], r[3], r[4], r[0]))  # type: ignore[arg-type]
    assert [r[0] for r in ordered] == ["p0", "p3-overdue", "p3-late-a", "p3-late-b", "p3-none"]


def test_lane_for_first_match() -> None:
    assert lane_for(Priority.P1, "overdue", "unassigned", _at(-90), None, NOW) == "p0_p1"
    assert lane_for(Priority.P3, "overdue", "unassigned", _at(-90), None, NOW) == "overdue"
    assert lane_for(Priority.P3, "due_soon", "unassigned", _at(-90), None, NOW) == "due_soon"
    assert lane_for(Priority.P3, "on_time", "unassigned", _at(-29), None, NOW) is None
    assert lane_for(Priority.P3, "on_time", "unassigned", _at(-30), None, NOW) == "unowned"
    assert lane_for(Priority.P3, "on_time", "waiting", _at(-90), _at(-1), NOW) == "stuck_waiting"
    assert lane_for(Priority.P3, "on_time", "waiting", _at(-90), _at(5), NOW) is None


def test_labels() -> None:
    assert age_label(_at(-4), NOW) == "Open 4 min"
    assert age_label(_at(-6), NOW) == "Open 6 min"
    assert age_label(_at(-36), NOW) == "Open 36 min"
    assert age_label(_at(-120), NOW) == "Open 2 h"
    assert age_label(_at(-1680), NOW) == "Open 1 day 4 h"
    assert age_label(_at(-4320), NOW) == "Open 3 days"
    queued = dt.datetime(2026, 10, 16, 14, 14, tzinfo=CHI)
    assert age_label(_at(-5), NOW, queued_at=queued) == "Waiting since 2:14 pm"
    assert follow_up_short("phone", "morning") == "Phone · mornings"
    assert follow_up_short("email", "any") == "Email"
    assert follow_up_short("email", "afternoon") == "Email · afternoons"
    assert follow_up_short(None, None) is None
    for reason in HandoffReason:
        label = reason_label(reason)
        assert label and label != reason.value
    assert reason_label(HandoffReason.SAFETY, "gas") == "Gas smell reported in chat"
    assert case_due_label(NOW, is_window_start=True).endswith(", the window start")  # type: ignore[union-attr]
    assert not case_due_label(NOW, is_window_start=False).endswith("window start")  # type: ignore[union-attr]
    assert case_due_label(None, is_window_start=True) is None


def _identity(status: str, codes_sent: int = 0) -> IdentityState:
    return IdentityState(
        status=status,  # type: ignore[arg-type]
        customer_id=None,
        masked_hint=None,
        code_expires_at=None,
        tries_left=3,
        codes_sent=codes_sent,
        verified_at=None,
    )


def test_identity_view_statuses() -> None:
    seen = {
        "verified": identity_view(_identity("verified"), case_customer=False)[0],
        "code_sent": identity_view(_identity("code_sent", 1), case_customer=False)[0],
        "located_sent": identity_view(_identity("located", 1), case_customer=False)[0],
        "located_none": identity_view(_identity("located", 0), case_customer=False)[0],
        "not_verified": identity_view(_identity("not_verified"), case_customer=False)[0],
        "locked": identity_view(_identity("locked"), case_customer=False)[0],
        "not_checked": identity_view(_identity("not_checked"), case_customer=False)[0],
    }
    assert seen == {
        "verified": "verified",
        "code_sent": "code_sent",
        "located_sent": "code_sent",
        "located_none": "not_checked",
        "not_verified": "not_verified",
        "locked": "locked",
        "not_checked": "not_checked",
    }
    status, line, note = identity_view(_identity("not_checked"), case_customer=True)
    assert status == "verified" and note == "Demo simulation" and "Not real ID proof" in line


def test_parse_seen_formats() -> None:
    assert parse_seen('{"amount_cents": 47800}') == {"amount_cents": 47800}
    assert parse_seen("INV-204411 amount_cents=47800 balance_cents=47800") == {
        "amount_cents": 47800,
        "balance_cents": 47800,
    }
    assert parse_seen("below_floor=false; faq/x.md#3=0.812") == {"below_floor": "false"}
    assert parse_seen("no pairs here") == {"seen": "no pairs here"}
    inv = "INV-204411 total $478.00 balance $478.00 lines $144.00 / $334.00"
    assert parse_seen(inv, record_id="INV-204411") == {"amount_cents": 47800, "balance_cents": 47800}
    assert parse_seen(inv) == {"seen": inv}
    assert (
        parse_seen("INV-204411 total $5.00 balance -$5.00", record_id="INV-204411")["balance_cents"] == -500
    )
    assert parse_seen("membership tier plus renewal 2026-11-03") == {
        "membership_tier": "plus",
        "membership_renewal_date": "2026-11-03",
    }
    assert parse_seen("membership tier none renewal none") == {
        "membership_tier": "none",
        "membership_renewal_date": None,
    }
    assert parse_seen("warranty install none") == {"system_install_date": None}
    assert parse_seen("booked slot:88") == {"seen": "booked slot:88"}


def _lookup(tool: str, records: tuple[str, ...] = (), passages: tuple[str, ...] = ()) -> LookupRow:
    return LookupRow.model_validate(
        {
            "id": 1,
            "thread_id": "11111111-1111-4111-8111-111111111111",
            "tool": tool,
            "record_ids": records,
            "passage_ids": passages,
            "result_seen": "x",
            "message_id": 1,
            "turn_id": "22222222-2222-4222-8222-222222222222",
        }
    )


def test_record_kind_and_row_title() -> None:
    assert record_kind("INV-204411") == ("invoice", "INV-204411")
    assert record_kind("MHC-10002") == ("customer", "MHC-10002")
    assert record_kind("4471") == ("appointment", "4471")
    assert record_kind("appointment:4471") == ("appointment", "4471")
    assert record_kind("slot:88") == ("slot", "88")
    assert record_kind("faq/x.md") is None
    assert row_title(_lookup("read_invoices", ("INV-204411",))) == "Invoice INV-204411"
    assert row_title(_lookup("read_warranty", ("MHC-10002",))) == "Warranty record"
    assert row_title(_lookup("read_membership", ("MHC-10002",))) == "Membership record"
    assert row_title(_lookup("move_visit", ("appointment:4471", "slot:88"))) == "Appointment 4471"
    assert row_title(_lookup("find_windows", ("slot:88",))) == "Open visit windows"
    assert row_title(_lookup("kb_search", (), ("faq/x.md#3",))) == "faq/x.md"


def test_mask_removes_contacts() -> None:
    with temp_sqlite() as db, db.uow() as tx:
        customer = tx.core.reads.customer("MHC-10002")  # type: ignore[arg-type]
    assert customer is not None and customer.email is not None
    text = f"Call {customer.phone} or write {customer.email}."
    out = mask(text)
    assert customer.phone not in out and customer.email not in out
    assert "[phone ending" in out


def test_staffing_view_labels() -> None:
    off = staffing_view("nobody_online")
    on = staffing_view("simulated_on_shift")
    assert (off.label, off.banner) == ("Nobody online", None)
    assert on.label == "Simulated staff on shift (demo)" and on.banner == TEXTS[TextId.STAFFING_BANNER]
