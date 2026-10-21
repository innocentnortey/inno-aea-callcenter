"""AEA-52: CON-9 reset through the real app (AC-8, AC-27). The open-chat half waits on AEA-51."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.repos_cases_state import RecordsRepo
from meridian.web.deps import RESET_GATE
from tests.integration.staff_support import (
    DEMO_NEEDS,
    DEMO_OPERATIONS,
    ISSUED_TABLES,
    KEPT_TABLES,
    P1_NEEDS,
    P1_OPERATIONS,
    SEED_REFS,
    act,
    advance,
    assert_bound,
    call,
    demo_now,
    error_of,
    parse_dt,
    reset_demo,
    set_staffing,
    sign_in,
    switch_role,
    write_working_copy,
)
from tests.journeys.support.db import issued_rows
from tests.journeys.support.run import JourneyRun


def test_reset_all_or_nothing(journey: JourneyRun, monkeypatch: pytest.MonkeyPatch) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    db = journey.db
    rep = sign_in(journey, "representative")
    sup = sign_in(journey, "supervisor")
    assert act(rep, "MHC-C-0006", "claim").status_code == 200
    flag = call(rep, "POST", "/api/staff/flags", "createFlag", {"case_ref": "MHC-C-0005", "target": "brief"})
    assert flag.status_code == 201
    flag_id = flag.json()["flag_id"]
    assert advance(sup, "plus_1h").status_code == 200
    set_staffing(sup, "simulated_on_shift")

    before = {t: db.count(t) for t in KEPT_TABLES}
    resets_before, seeds_before = db.count("reset_events"), db.count("seed_events")
    non_customer = db.count("staff_sessions", "role != 'customer'")

    gate = journey.container.get(RESET_GATE)
    with gate.hold():
        held = call(
            sign_in(journey),
            "POST",
            f"/api/chat/sessions/{uuid.uuid4()}/turns",
            "submitTurn",
            {"turn_id": str(uuid.uuid4()), "payload": {"kind": "text", "text": "hello"}},
        )
        assert held.status_code == 503
        assert error_of(held)["code"] == "RESET_IN_PROGRESS"
        assert error_of(held)["details"]["retry_after_ms"] == 5000
        second = reset_demo(rep)
        assert second.status_code == 409
        assert error_of(second)["code"] == "RESET_IN_PROGRESS"
    sessions_before = db.count("staff_sessions")

    done = reset_demo(rep)
    assert done.status_code == 200, done.text
    body = done.json()
    assert body["ok"] is True
    assert body["roles_reset"] == non_customer
    assert body["open_chats_ended"] == 0
    assert parse_dt(body["clock"]["now"]) == DEMO_START
    rid = done.headers["X-Request-ID"]

    for table in ISSUED_TABLES:
        assert db.table_rows(table) == issued_rows(table), table
    assert sorted(r["case_ref"] for r in db.rows("SELECT case_ref FROM cases")) == list(SEED_REFS)
    assert db.count("flags") == 0
    assert db.count("activities") == 0
    state = db.one("SELECT * FROM demo_state")
    assert parse_dt(state["demo_now"]) == DEMO_START
    assert state["staffing"] == "nobody_online"
    assert demo_now(rep) == DEMO_START
    assert db.count("conversations", "run_tag != 'seed'") == 0

    refused = call(rep, "GET", "/api/staff/queue", "getQueue")
    assert refused.status_code == 403
    assert error_of(refused)["code"] == "ROLE_NOT_ALLOWED"
    assert error_of(refused)["details"]["reason"] == "role_reset"
    assert error_of(refused)["details"]["role"] == "customer"
    assert call(rep, "GET", "/api/session", "getSession").json()["role"] == "customer"
    assert db.count("staff_sessions") == sessions_before

    sup_refused = call(sup, "GET", "/api/staff/queue", "getQueue")
    assert error_of(sup_refused)["details"]["reason"] == "role_reset"
    sup = switch_role(sup, "supervisor")
    gone = call(sup, "PATCH", f"/api/staff/flags/{flag_id}", "reviewFlag", {"status": "reviewed"})
    assert gone.status_code == 404
    assert error_of(gone)["code"] == "FLAG_NOT_FOUND"

    assert db.count("reset_events") == resets_before + 1
    reset_row = db.rows("SELECT * FROM reset_events ORDER BY rowid DESC LIMIT 1")[0]
    assert reset_row["asked_by_role"] == "representative"
    assert reset_row["asked_by_session"] == rep.session_id
    assert reset_row["request_id"] == rid
    assert db.count("seed_events") == seeds_before + 1
    seed_row = db.rows("SELECT * FROM seed_events ORDER BY rowid DESC LIMIT 1")[0]
    assert seed_row["reset_id"] == reset_row["reset_id"]
    assert seed_row["seed_count"] == 4

    for table in ("spend_ledger", "deploy_records", "eval_runs", "demo_events"):
        assert db.count(table) == before[table], table
    for table in ("job_runs", "health_events"):
        assert db.count(table) >= before[table], table
    print("reset: issued tables equal, seeds only, flags gone, clock", DEMO_START.isoformat())

    # forced failure rolls back
    rep = switch_role(rep, "representative")
    assert advance(sup, "plus_1h").status_code == 200
    forced_now = demo_now(sup)
    assert (
        call(
            rep, "POST", "/api/staff/flags", "createFlag", {"case_ref": "MHC-C-0005", "target": "brief"}
        ).status_code
        == 201
    )
    update = "UPDATE invoices SET balance_cents = balance_cents + 1000 WHERE invoice_id = ?"
    write_working_copy(journey, update, ("INV-200037",))
    invoice = db.one("SELECT * FROM invoices WHERE invoice_id = ?", ("INV-200037",))
    counts = {t: db.count(t) for t in ("cases", "flags", "reset_events")}

    def boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("forced reset failure")

    monkeypatch.setattr(RecordsRepo, "seed_event", boom)
    failed = reset_demo(rep)
    monkeypatch.undo()
    assert failed.status_code == 500
    assert error_of(failed)["code"] == "RESET_FAILED"
    assert db.one("SELECT * FROM invoices WHERE invoice_id = ?", ("INV-200037",)) == invoice
    assert {t: db.count(t) for t in ("cases", "flags", "reset_events")} == counts
    assert demo_now(sup) == forced_now
    assert call(rep, "GET", "/api/staff/queue", "getQueue").status_code == 200
    print("forced failure: RESET_FAILED, nothing restored, role kept")


def test_reset_makes_no_outbound_connection(journey: JourneyRun) -> None:
    assert_bound(journey, DEMO_NEEDS, DEMO_OPERATIONS)
    rep = sign_in(journey, "representative")
    sup = sign_in(journey, "supervisor")
    assert advance(sup, "plus_1h").status_code == 200
    before = list(journey.guard.blocked)
    done = reset_demo(rep)
    assert done.status_code == 200, done.text
    assert parse_dt(done.json()["clock"]["now"]) == DEMO_START
    assert journey.guard.blocked == before == []
    print("0 connection attempts")
