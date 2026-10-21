"""AEA-52: case view, contact attempts and flags on the real app (AC-9, AC-10, AC-11). WP variants wait on AEA-51."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from meridian.policy.texts import TEXTS, TextId
from tests.integration.staff_support import (
    CHICAGO,
    P1_NEEDS,
    P1_OPERATIONS,
    act,
    assert_bound,
    call,
    case_view,
    error_of,
    parse_dt,
    sign_in,
    tree_digest,
    version_of,
    write_working_copy,
)
from tests.journeys.support.run import JourneyRun

ROOT = Path(__file__).resolve().parents[2]
INVOICE_REF = "invoices/INV-200037"


def _invoice_source(view: dict[str, Any]) -> dict[str, Any]:
    found = [s for s in view["sources"] if s["ref"] == INVOICE_REF]
    assert len(found) == 1, found
    first: dict[str, Any] = found[0]
    return first


@pytest.mark.parametrize("variant", ["seed_invoice"])
def test_case_view_snapshot_vs_current(journey: JourneyRun, variant: str) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    rep = sign_in(journey, "representative")
    view = case_view(rep, "MHC-C-0005")
    due = parse_dt(view["case"]["due_at"]).astimezone(CHICAGO)
    promise_due = parse_dt(view["promise"]["due_at"]).astimezone(CHICAGO)
    assert due == promise_due
    assert (due.year, due.month, due.day, due.hour, due.minute) == (2026, 10, 15, 19, 0)

    source = _invoice_source(view)
    assert isinstance(source["snapshot"], dict)
    assert isinstance(source["current"], dict)
    assert source["changed_since"] is False
    assert source["changed_note"] == "No change since the snapshot"
    assert source["current_unavailable"] is False
    known = {s["source_id"]: s for s in view["sources"]}
    named: set[str] = set()
    for heading in view["brief"]["headings"]:
        for item in heading["items"]:
            for sid in item["source_ids"]:
                assert sid in known, sid
                named.add(sid)
    assert named
    for sid in named:
        log_id = known[sid]["lookup_log_id"]
        assert log_id.startswith("ll-")
        assert journey.db.count("lookup_log", "id = ?", (int(log_id.removeprefix("ll-")),)) == 1
    before_snapshot, before_current = source["snapshot"], source["current"]

    write_working_copy(
        journey,
        "UPDATE invoices SET balance_cents = balance_cents + 1000 WHERE invoice_id = ?",
        ("INV-200037",),
    )
    after = _invoice_source(case_view(rep, "MHC-C-0005"))
    assert after["changed_since"] is True
    assert after["changed_note"] == "Changed since the AI saw it"
    assert after["current"]["balance_cents"] == before_current["balance_cents"] + 1000
    assert after["snapshot"] == before_snapshot
    print("snapshot:", before_snapshot, "current:", after["current"], "marker:", after["changed_note"])


@pytest.mark.parametrize("variant", ["seeds"])
def test_contact_attempt_recorded_not_sent(journey: JourneyRun, variant: str) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    rep = sign_in(journey, "representative")
    assert act(rep, "MHC-C-0006", "claim").status_code == 200
    assert act(rep, "MHC-C-0007", "claim").status_code == 200

    def record(ref: str, outcome: str) -> dict[str, object]:
        body = {
            "kind": "call",
            "outcome": outcome,
            "note": None,
            "expected_version": version_of(rep, ref),
        }
        response = call(rep, "POST", f"/api/staff/cases/{ref}/activities", "recordContactActivity", body)
        assert response.status_code == 201, response.text
        return response.json()  # type: ignore[no-any-return]

    kept = record("MHC-C-0006", "left_message")
    assert kept["activity"]["label"] == TEXTS[TextId.RECORDED_NOT_SENT]  # type: ignore[index]
    assert kept["activity"]["outcome"] == "left_message"  # type: ignore[index]
    assert kept["case"]["promise_status"] == "kept"  # type: ignore[index]
    assert journey.db.scalar("SELECT status FROM promises WHERE case_ref = ?", ("MHC-C-0006",)) == "kept"
    still_open = record("MHC-C-0007", "no_answer")
    assert still_open["case"]["promise_status"] == "open"  # type: ignore[index]
    assert journey.db.scalar("SELECT status FROM promises WHERE case_ref = ?", ("MHC-C-0007",)) == "open"
    rows = journey.db.rows("SELECT case_ref, actor_role FROM activities ORDER BY rowid")
    assert [r["actor_role"] for r in rows] == ["representative", "representative"]
    assert journey.guard.blocked == []
    print("activities:", rows)


def test_flag_review_changes_nothing_else(journey: JourneyRun) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    dirs = [
        ROOT / "eval/cases",
        ROOT / "src/meridian/agent/prompts",
        ROOT / "docs/data/issued/meridian_dataset/knowledge_base",
        journey.env.index_dir,
    ]
    before = {d: tree_digest(d) for d in dirs}
    staff_events = "actor_role IN ('representative','supervisor')"
    staff_rows = journey.db.count("case_events", staff_events)
    rep = sign_in(journey, "representative")
    sup = sign_in(journey, "supervisor")
    one = call(
        rep,
        "POST",
        "/api/staff/flags",
        "createFlag",
        {"case_ref": "MHC-C-0005", "target": "brief", "reason": "Synthetic reason one"},
    )
    two = call(
        rep, "POST", "/api/staff/flags", "createFlag", {"case_ref": "MHC-C-0006", "target": "escalation"}
    )
    assert one.status_code == two.status_code == 201
    f1, f2 = one.json()["flag_id"], two.json()["flag_id"]
    listed = call(sup, "GET", "/api/staff/flags", "listFlags").json()["flags"]
    assert [f["flag_id"] for f in listed[:2]] == [f2, f1]
    reviewed = call(
        sup,
        "PATCH",
        f"/api/staff/flags/{f1}",
        "reviewFlag",
        {"status": "reviewed", "note": "Reviewed in test"},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "reviewed"
    assert reviewed.json()["reviewed_by"] == "Demo supervisor"
    assert {d: tree_digest(d) for d in dirs} == before
    assert journey.db.count("flags") == 2
    assert journey.db.count("case_events", staff_events) == staff_rows
    missing = call(sup, "PATCH", "/api/staff/flags/flg-999999", "reviewFlag", {"status": "reviewed"})
    assert missing.status_code == 404
    assert error_of(missing)["code"] == "FLAG_NOT_FOUND"
    print("review list:", [(f["flag_id"], f["status"]) for f in listed])
