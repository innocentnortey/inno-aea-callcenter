"""J-6 seed leg at the integrated level (AEA-52): the representative sees the four seeded cases and opens one with
its brief. The WP-7/WP-8 escalation leg needs AEA-51 (`reply_composer`, `run_graph`) and is not built here."""

from __future__ import annotations

import pytest

from tests.integration.staff_support import SEED_REFS
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J6 = "J-6"
SERVICES = ("login_sessions", "demo_clock", "case_service")


def test_j6_seeded_cases_in_queue_with_brief(journey: JourneyRun) -> None:
    signed = journey.login()
    c = signed.client
    with journey.step(J6, "1 act as the representative", needs=SERVICES, operations=("switchRole",)):
        r = c.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "representative"})
        assert r.status_code == 200
    with journey.step(
        J6, "2 the queue lists the four seeded cases", needs=SERVICES, operations=("getQueue",)
    ):
        r = c.call("GET", "/api/staff/queue", operation_id="getQueue")
        assert r.status_code == 200
        listed = {row["reference"] for row in r.json()["needs_my_action"]}
        assert set(SEED_REFS) <= listed
        stored = journey.db.rows("SELECT case_ref, seed FROM cases ORDER BY case_ref")
        assert [(s["case_ref"], s["seed"]) for s in stored if s["case_ref"] in SEED_REFS] == [
            (ref, 1) for ref in SEED_REFS
        ]
    with journey.step(J6, "3 a case opens with its brief", needs=SERVICES, operations=("getCase",)):
        r = c.call("GET", "/api/staff/cases/MHC-C-0005", operation_id="getCase")
        assert r.status_code == 200
        body = r.json()
        assert len(body["brief"]["headings"]) == 8
        assert body["promise"]["policy_row"] == "R26.refund"
        assert body["promise"]["text"]
        known = {s["source_id"] for s in body["sources"]}
        for heading in body["brief"]["headings"]:
            for item in heading["items"]:
                assert set(item["source_ids"]) <= known
        assert journey.db.count("case_briefs", "case_ref = ?", ("MHC-C-0005",)) >= 1
