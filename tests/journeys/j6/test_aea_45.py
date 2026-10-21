"""J-6 extension (slice plan section 0a): the representative claims the escalated case MHC-C-0007 on AEA-57's harness
(real app on a first-boot DB copy, scripted model; no model call is reached). Steps that need `case_service` (AEA-29)
or `demo_service` (AEA-30) are reported blocked until those merge; so are steps 0-1, because the real login reads
`demo_clock` (AEA-30). CAP-4 end to end is AEA-52's."""

from __future__ import annotations

import pytest

from meridian.domain.common import CaseRef
from meridian.domain.staff import StaffRole
from meridian.web.deps import CASE_SERVICE, DEMO_SERVICE
from meridian.web.schemas.staff_cases import CaseDetailOut
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

REF = "MHC-C-0007"
J6 = "J-6"
SERVICES = ("case_service", "demo_service")
CASE_PATH = f"/api/staff/cases/{REF}"


def test_j6_representative_claims_escalated_case(journey: JourneyRun) -> None:
    with journey.step(
        J6,
        "0 the customer role is refused the queue",
        needs=("login_sessions", "demo_clock"),  # login reads the demo clock (AEA-30)
        operations=("login", "getQueue"),
    ):
        signed = journey.login()
        c = signed.client
        r = c.call("GET", "/api/staff/queue", operation_id="getQueue")
        assert r.status_code == 403
        assert r.json()["error"]["details"] == {
            "role": "customer",
            "needs": ["representative", "supervisor"],
            "reason": "wrong_role",
        }

    with journey.step(
        J6, "1 act as the representative", needs=("login_sessions", "demo_clock"), operations=("switchRole",)
    ):
        r = c.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "representative"})
        assert r.status_code == 200
        stored_role = journey.db.scalar(
            "SELECT role FROM staff_sessions WHERE session_id = ?", (signed.session_id,)
        )
        assert stored_role == "representative"

    with journey.step(J6, "2 the queue lists the escalated case", needs=SERVICES, operations=("getQueue",)):
        stored = journey.db.one(
            "SELECT lifecycle, owner_role, version, priority FROM cases WHERE case_ref = ?", (REF,)
        )
        r = c.call("GET", "/api/staff/queue", operation_id="getQueue")
        assert r.status_code == 200
        rows = [row for row in r.json()["needs_my_action"] if row["reference"] == REF]
        assert len(rows) == 1
        row = rows[0]
        assert row["lifecycle"] == stored["lifecycle"] == "unassigned"
        assert row["owner"] is None
        assert row["priority"]["level"] == stored["priority"]

    with journey.step(
        J6, "3 the case opens with its brief and allowed actions", needs=SERVICES, operations=("getCase",)
    ):
        r = c.call("GET", CASE_PATH, operation_id="getCase")
        assert r.status_code == 200
        body = r.json()
        assert body["case"]["version"] == stored["version"]
        assert "claim" in body["case"]["allowed_actions"]
        assert len(body["brief"]["headings"]) == 8
        demo_now = journey.container.get(DEMO_SERVICE).clock_view().now
        direct = journey.container.get(CASE_SERVICE).detail(CaseRef(REF), StaffRole.REPRESENTATIVE, demo_now)
        assert CaseDetailOut.model_validate(direct).model_dump(mode="json") == body
        v0 = body["case"]["version"]

    with journey.step(J6, "4 the representative claims it", needs=SERVICES, operations=("applyCaseAction",)):
        where = "case_ref = ? AND actor_role = 'representative'"
        events_before = journey.db.count("case_events", where, (REF,))
        r = c.call(
            "POST",
            f"{CASE_PATH}/actions",
            operation_id="applyCaseAction",
            body={"action": "claim", "expected_version": v0},
        )
        assert r.status_code == 200
        claimed = r.json()
        assert claimed["result_line"] == "Claimed · Riley (demo)"
        assert claimed["case"]["owner"] == "Riley"
        assert claimed["case"]["lifecycle"] == "claimed"
        assert claimed["case"]["version"] == v0 + 1
        after = journey.db.one("SELECT lifecycle, owner_role, version FROM cases WHERE case_ref = ?", (REF,))
        assert (after["lifecycle"], after["owner_role"], after["version"]) == (
            "claimed",
            "representative",
            v0 + 1,
        )
        assert journey.db.count("case_events", where, (REF,)) == events_before + 1

    with journey.step(
        J6,
        "5 a stale version is refused and changes nothing",
        needs=SERVICES,
        operations=("applyCaseAction",),
    ):
        events_now = journey.db.count("case_events", "case_ref = ?", (REF,))
        r = c.call(
            "POST",
            f"{CASE_PATH}/actions",
            operation_id="applyCaseAction",
            body={"action": "claim", "expected_version": v0},
        )
        assert r.status_code == 409
        error = r.json()["error"]
        assert error["code"] == "VERSION_CONFLICT"
        assert error["details"]["current_version"] == v0 + 1
        assert journey.db.scalar("SELECT version FROM cases WHERE case_ref = ?", (REF,)) == v0 + 1
        assert journey.db.count("case_events", "case_ref = ?", (REF,)) == events_now

    with journey.step(J6, "6 reopening shows it claimed", needs=SERVICES, operations=("getCase",)):
        r = c.call("GET", CASE_PATH, operation_id="getCase")
        assert r.status_code == 200
        reopened = r.json()["case"]
        assert reopened["owner"] == "Riley"
        assert reopened["version"] == v0 + 1
        assert "claim" not in reopened["allowed_actions"]
