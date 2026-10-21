"""J-8 reset leg (AEA-43, AC-16; proposed J-8 extension). API level on AEA-57's harness. Needs AEA-30 (DemoService and
format_clock, which the real ResetService calls) and AEA-29 (the demo seed the reset reloads); until both land the step
is skipped `blocked-on`.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from tests.fakes.clock import WORKED_PAIRS_NOW
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

DEMO_START = WORKED_PAIRS_NOW
START_LABEL = "Fri Oct 16, 2026 · 10:00 am"
START_DATE_LABEL = "Fri Oct 16, 2026 (demo date)"


def test_j8_reset_returns_staffing_and_clock_to_start(journey: JourneyRun) -> None:
    with journey.step(
        "J-8",
        "reset 1 resetDemo answers the start clock; reads back at defaults; who asked stored",
        needs=("login_sessions", "reset_service", "demo_service", "handoff_service"),
        operations=("login", "setStaffing", "resetDemo", "getStaffing", "getDemoClock"),
    ):
        signed = journey.login()
        c = signed.client
        on = c.call(
            "PUT", "/api/demo/staffing", operation_id="setStaffing", body={"mode": "simulated_on_shift"}
        )
        assert on.status_code == 200 and on.json()["mode"] == "simulated_on_shift"
        r = c.call("POST", "/api/demo/reset", operation_id="resetDemo", body={"confirm": True})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert datetime.fromisoformat(body["clock"]["now"]) == DEMO_START
        assert (body["clock"]["label"], body["clock"]["date_label"]) == (START_LABEL, START_DATE_LABEL)
        row = journey.db.one(
            "SELECT asked_by_role, asked_by_session, open_chats_ended, roles_reset FROM reset_events "
            "WHERE request_id = ?",
            (r.headers["X-Request-ID"],),
        )
        assert row["asked_by_session"] == signed.session_id
        assert row["asked_by_role"] == "customer"
        assert (row["open_chats_ended"], row["roles_reset"]) == (
            body["open_chats_ended"],
            body["roles_reset"],
        )
        state = journey.db.one("SELECT demo_now, staffing FROM demo_state WHERE id = 1")
        assert state["staffing"] == "nobody_online"
        assert datetime.fromisoformat(state["demo_now"]) == DEMO_START
        staffing = c.call("GET", "/api/demo/staffing", operation_id="getStaffing").json()
        assert staffing["mode"] == "nobody_online" and staffing["banner"] is None
        clock = c.call("GET", "/api/demo/clock", operation_id="getDemoClock").json()
        assert (clock["label"], clock["date_label"]) == (START_LABEL, START_DATE_LABEL)
        assert datetime.fromisoformat(clock["now"]) == DEMO_START
