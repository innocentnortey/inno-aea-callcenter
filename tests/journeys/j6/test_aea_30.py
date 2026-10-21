"""J-6 (proposed extension, slice plan section 0a): the supervisor advances the one demo clock on the real server; the
scheduler runs on it; a case past its case due shows in the Overdue lane. API level on AEA-57's harness with the
scripted model. The lane step is blocked until AEA-29 (case service and first-boot seed) and AEA-45 (getOversight) land.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytest

from meridian.adapters.sqlite.db import parse_wall
from meridian.adapters.sqlite.repos_cases import DEMO_START
from tests.journeys.support.run import JourneyRun, LoginResult

pytestmark = pytest.mark.journey

J6 = "J-6"
STEPS = ["next_business_morning", "plus_4h", "plus_4h", "plus_4h", "plus_1h"]
SEVEN_KEYS = {"overdue", "promises_missed", "due_soon", "stuck_waiting", "unowned", "abandoned", "pruned"}


def _open_dues(journey: JourneyRun) -> list[datetime]:
    rows = journey.db.rows(
        "SELECT due_at FROM cases WHERE lifecycle NOT IN ('resolved','closed_unresolved') AND due_at IS NOT NULL"
    )
    return [parse_wall(r["due_at"]) for r in rows]


def _became(dues: list[datetime], old: datetime, new: datetime) -> int:
    return sum(old <= d < new for d in dues)


def _wait_for(predicate: Callable[[], bool], timeout_s: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("timed out waiting for the condition")


def _supervisor(journey: JourneyRun) -> LoginResult:
    signed = journey.login()
    r = signed.client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "supervisor"})
    assert r.json()["role"] == "supervisor"
    return signed


def _demo_now(journey: JourneyRun) -> datetime:
    found = journey.db.rows("SELECT demo_now FROM demo_state WHERE id = 1")
    return parse_wall(found[0]["demo_now"]) if found else DEMO_START


def test_j6_scheduler_ran_at_start(journey: JourneyRun) -> None:
    with journey.step("J-6", "1 scheduler ran at start", needs=("demo_clock",)):
        _wait_for(lambda: journey.db.count("job_runs", "status = ?", ("completed",)) >= 1)
        row = journey.db.one("SELECT * FROM job_runs ORDER BY started_wall_at LIMIT 1")
        assert row["demo_now"] == "2026-10-16T15:00:00+00:00"  # DEMO_START (10:00 Chicago) in UTC
        assert str(row["started_wall_at"]).endswith("+00:00")
        assert row["error_kind"] is None
        assert set(json.loads(row["counts_json"])) == SEVEN_KEYS


def test_j6_clock_advance_on_the_real_server(journey: JourneyRun) -> None:
    with journey.step(
        "J-6",
        "2 supervisor advances the clock",
        needs=("login_sessions", "staff_access", "demo_service", "demo_clock"),
        operations=("login", "switchRole", "advanceDemoClock"),
    ):
        signed = _supervisor(journey)
        dues = _open_dues(journey)
        bodies: list[dict[str, Any]] = []
        first_request_id = ""
        for s in STEPS:
            old = _demo_now(journey)
            r = signed.client.call(
                "POST", "/api/demo/clock", operation_id="advanceDemoClock", body={"step": s}
            )
            assert r.status_code == 200
            body = r.json()
            assert body["became_overdue"] == _became(dues, old, datetime.fromisoformat(body["now"]))
            if not bodies:
                first_request_id = r.headers["X-Request-ID"]
            bodies.append(body)
        assert bodies[0]["now"] == "2026-10-19T07:00:00-05:00"
        assert bodies[0]["label"] == "Mon Oct 19, 2026 · 7:00 am"
        assert bodies[-1]["now"] == "2026-10-19T20:00:00-05:00"
        assert bodies[-1]["label"] == "Mon Oct 19, 2026 · 8:00 pm"
        assert (
            journey.db.scalar("SELECT demo_now FROM demo_state WHERE id = 1") == "2026-10-20T01:00:00+00:00"
        )
        assert journey.db.count("demo_events", "kind = ?", ("clock_advanced",)) == 5
        first = journey.db.one("SELECT * FROM demo_events WHERE step = 'next_business_morning'")
        assert first["role"] == "supervisor"
        assert first["request_id"] == first_request_id
        assert first["demo_before"] == "2026-10-16T15:00:00+00:00"
        assert first["demo_after"] == "2026-10-19T12:00:00+00:00"


def test_j6_case_in_overdue_lane(journey: JourneyRun) -> None:
    with journey.step(
        "J-6",
        "3 overdue lane",
        needs=("login_sessions", "staff_access", "demo_service", "case_service"),
        operations=("login", "switchRole", "advanceDemoClock", "getOversight"),
    ):
        signed = _supervisor(journey)
        for s in STEPS:
            r = signed.client.call(
                "POST", "/api/demo/clock", operation_id="advanceDemoClock", body={"step": s}
            )
            assert r.status_code == 200
        o = signed.client.call("GET", "/api/staff/oversight", operation_id="getOversight")
        assert o.status_code == 200
        refs = [row["reference"] for row in o.json()["lanes"]["overdue"]["rows"]]
        assert "MHC-C-0007" in refs  # seed case (cases.md section 7)
        due = parse_wall(journey.db.scalar("SELECT due_at FROM cases WHERE case_ref = 'MHC-C-0007'"))
        assert due < _demo_now(journey)
