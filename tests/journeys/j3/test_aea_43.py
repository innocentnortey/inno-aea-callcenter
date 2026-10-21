"""J-3 inbox legs (AEA-43, AC-16; pattern A). API level on AEA-57's harness: real app, container and DB copy, scripted
model. Step 0 needs AEA-30's DemoService (the inbox reads the demo clock). Step 1 (a code sent through the chat shows
`active`, is entered, then shows `used` with dots; a second login sees none) also needs AEA-40 and AEA-51; its body is
written with AEA-51's scripted outputs (AEA-27 plan R-1). The same flow at mock level: tests/api/test_demo_flows.py.
"""

from __future__ import annotations

import pytest

from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J3 = "J-3"


def test_j3_inbox_empty_for_new_login(journey: JourneyRun) -> None:
    with journey.step(
        J3,
        "inbox 0 a new login's inbox is empty",
        needs=("login_sessions", "identity_service", "demo_service"),
        operations=("login", "listDemoInbox"),
    ):
        signed = journey.login()
        r = signed.client.call("GET", "/api/demo/inbox", operation_id="listDemoInbox")
        assert r.status_code == 200
        assert r.json() == {"messages": []}
        assert journey.db.count("demo_inbox", "demo_session = ?", (signed.session_id,)) == 0


def test_j3_inbox_code_active_then_used(journey: JourneyRun) -> None:
    with journey.step(
        J3,
        "inbox 1 code active then used; a second login sees none",
        needs=(
            "login_sessions",
            "session_service",
            "turn_service",
            "run_graph",
            "identity_service",
            "demo_service",
        ),
        operations=("login", "startChatSession", "submitTurn", "listDemoInbox"),
    ):
        pytest.skip("J-3 inbox body not written yet: needs AEA-51's scripted graph outputs (AEA-27 plan R-1)")
