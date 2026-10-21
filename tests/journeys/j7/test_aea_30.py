"""J-7 (proposed extension): with staffing on, a person request is live-queued; turning staffing off converts the case
and tells the chat. API level on AEA-57's harness. Blocked today on AEA-43 (setStaffing), AEA-40 (startChatSession) and
AEA-29 (handoff and case services); the service-level behaviour is in tests/services/test_demo.py
(test_shift_end_commits_with_conversions, mock-tested).
"""

from __future__ import annotations

import uuid

import pytest

from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J7 = "J-7"


def test_j7_shift_end_converts_queued_case(journey: JourneyRun) -> None:
    signed = None
    with journey.step(
        "J-7",
        "1 staffing on",
        needs=("login_sessions", "demo_service"),
        operations=("login", "setStaffing"),
    ):
        signed = journey.login()
        r = signed.client.call(
            "PUT", "/api/demo/staffing", operation_id="setStaffing", body={"mode": "simulated_on_shift"}
        )
        assert r.json() == {
            "mode": "simulated_on_shift",
            "label": "Simulated staff on shift (demo)",
            "converted_cases": 0,
        }
        assert journey.db.scalar("SELECT staffing FROM demo_state WHERE id = 1") == "simulated_on_shift"
        row = journey.db.one("SELECT * FROM demo_events WHERE kind = 'staffing_changed'")
        assert row["role"] == "customer"
        assert row["request_id"] == r.headers["X-Request-ID"]
    assert signed is not None
    thread_id = ""
    case_ref = ""
    created_at = ""
    with journey.step(
        "J-7",
        "2 person request live-queued",
        needs=("session_service", "handoff_service", "person_requests"),
        operations=("startChatSession", "requestPerson"),
    ):
        started = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        thread_id = started.json()["thread_id"]
        r = signed.client.call(
            "POST",
            f"/api/chat/sessions/{thread_id}/handoff",
            operation_id="requestPerson",
            body={"turn_id": str(uuid.uuid4())},
        )
        assert r.json()["result"] == "live_queued"
        case = journey.db.one(
            "SELECT case_ref, lifecycle, created_at FROM cases WHERE thread_id = ?", (thread_id,)
        )
        assert case["lifecycle"] == "live_queued"
        assert (
            journey.db.scalar("SELECT live_state FROM conversations WHERE thread_id = ?", (thread_id,))
            == "queued"
        )
        case_ref, created_at = case["case_ref"], case["created_at"]
    with journey.step(
        "J-7",
        "3 staffing off converts",
        needs=("case_service", "demo_service"),
        operations=("setStaffing",),
    ):
        r = signed.client.call(
            "PUT", "/api/demo/staffing", operation_id="setStaffing", body={"mode": "nobody_online"}
        )
        body = r.json()
        assert body["converted_cases"] == 1
        assert body["label"] == "Nobody online"
        case = journey.db.one(
            "SELECT case_ref, lifecycle, created_at FROM cases WHERE thread_id = ?", (thread_id,)
        )
        assert (case["case_ref"], case["created_at"]) == (case_ref, created_at)
        assert case["lifecycle"] == "unassigned"
        assert (
            journey.db.scalar("SELECT live_state FROM conversations WHERE thread_id = ?", (thread_id,))
            == "not_live"
        )
        types = [
            r_["type"]
            for r_ in journey.db.rows("SELECT type FROM events WHERE stream = ? ORDER BY id", (thread_id,))
        ]
        assert types[-2:] == ["shift_ended", "staffing_changed"]
        assert journey.db.count("demo_events", "kind = ?", ("staffing_changed",)) == 2
