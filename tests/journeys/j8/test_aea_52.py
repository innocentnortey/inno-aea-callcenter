"""J-8 (role switch and session) at the integrated level: AEA-57's harness, the real staff routes and store (AEA-52)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from tests.journeys.support.run import JourneyRun
from tests.journeys.support.server import StepClock

pytestmark = pytest.mark.journey

J8 = "J-8"
SESSION = ("login_sessions", "demo_clock")


def _cookie(value: str) -> dict[str, str]:
    return {"Cookie": f"mhc_session={value}"}


def test_j8_role_switch_seen_by_second_client(journey: JourneyRun) -> None:
    a = journey.login()
    b = journey.client()  # a second browser tab: same cookie, no cookie jar of its own
    headers = _cookie(a.cookie)
    with journey.step(
        J8,
        "1 a role switched in one tab is seen in the other",
        needs=(*SESSION, "case_service"),
        operations=("switchRole", "getSession", "getQueue"),
    ):
        r = a.client.call(
            "PUT", "/api/session/role", operation_id="switchRole", body={"role": "representative"}
        )
        assert r.status_code == 200
        seen = b.call("GET", "/api/session", operation_id="getSession", headers=headers)
        assert seen.json()["role"] == "representative"
        assert b.call("GET", "/api/staff/queue", operation_id="getQueue", headers=headers).status_code == 200
        stored = journey.db.scalar("SELECT role FROM staff_sessions WHERE session_id = ?", (a.session_id,))
        assert stored == "representative"
    with journey.step(
        J8,
        "2 switching back is refused at the queue in both tabs",
        needs=(*SESSION, "case_service"),
        operations=("switchRole", "getQueue"),
    ):
        a.client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "customer"})
        refused = b.call("GET", "/api/staff/queue", operation_id="getQueue", headers=headers)
        assert refused.status_code == 403
        assert refused.json()["error"]["details"]["reason"] == "wrong_role"


def test_j8_reset_sends_both_clients_to_role_reset(journey: JourneyRun) -> None:
    a = journey.login()
    b = journey.client()
    headers = _cookie(a.cookie)
    with journey.step(
        J8,
        "1 a reset by another session sends both tabs to role_reset",
        needs=(*SESSION, "case_service", "reset_service"),
        operations=("switchRole", "resetDemo", "getQueue"),
    ):
        a.client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "supervisor"})
        other = journey.login()
        done = other.client.call("POST", "/api/demo/reset", operation_id="resetDemo", body={"confirm": True})
        assert done.status_code == 200
        for client, extra in ((a.client, None), (b, headers)):
            r = client.call("GET", "/api/staff/queue", operation_id="getQueue", headers=extra)
            assert r.status_code == 403
            assert r.json()["error"]["details"]["reason"] == "role_reset"
        pending = journey.db.scalar(
            "SELECT role_reset_pending FROM staff_sessions WHERE session_id = ?", (a.session_id,)
        )
        assert pending == 1
    with journey.step(
        J8,
        "2 choosing a role again clears the flag in both tabs",
        needs=(*SESSION, "case_service"),
        operations=("switchRole", "getQueue"),
    ):
        a.client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "representative"})
        for client, extra in ((a.client, None), (b, headers)):
            assert (
                client.call("GET", "/api/staff/queue", operation_id="getQueue", headers=extra).status_code
                == 200
            )
        pending = journey.db.scalar(
            "SELECT role_reset_pending FROM staff_sessions WHERE session_id = ?", (a.session_id,)
        )
        assert pending == 0


def test_j8_refresh_signed_out_and_expired(journey: JourneyRun, journey_clock: StepClock) -> None:
    a = journey.login()
    with journey.step(J8, "1 a refresh keeps the same session", needs=SESSION, operations=("getSession",)):
        first = a.client.call("GET", "/api/session", operation_id="getSession").json()
        second = a.client.call("GET", "/api/session", operation_id="getSession").json()
        assert first["signed_in_at"] == second["signed_in_at"]
    with journey.step(
        J8, "2 signing out ends the session", needs=SESSION, operations=("logout", "getSession")
    ):
        out = a.client.call("POST", "/api/logout", operation_id="logout")
        assert out.status_code == 204
        after = a.client.call("GET", "/api/session", operation_id="getSession")
        assert after.status_code == 401
        assert after.json()["error"]["code"] == "UNAUTHENTICATED"
        assert after.json()["error"]["details"]["reason"] == "none"
        assert journey.db.count("staff_sessions", "session_id = ?", (a.session_id,)) == 0
    with journey.step(J8, "3 an old session has expired", needs=SESSION, operations=("login", "getSession")):
        b = journey.login()
        journey_clock.advance(timedelta(hours=12).total_seconds() + 1)
        expired = b.client.call("GET", "/api/session", operation_id="getSession")
        assert expired.status_code == 401
        assert expired.json()["error"]["details"]["reason"] == "expired"
        assert journey.db.count("staff_sessions", "session_id = ?", (b.session_id,)) == 0
