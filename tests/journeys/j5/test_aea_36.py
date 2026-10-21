"""J-5 (slice plan section 0a), AEA-36 step: a CO-alarm message gets the safety card first and one P0 case row, with no
model call. API level on AEA-57's harness; the step is reported blocked until AEA-40, AEA-51 and AEA-29 bind their
services.
"""

from __future__ import annotations

import uuid

import pytest

from meridian.policy.texts import TEXTS, TextId
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J5 = "J-5"
SIGN_IN_NEEDS = ("login_sessions", "demo_clock")
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
SAFETY_TURN_NEEDS = (*CHAT_NEEDS, "turn_service", "run_graph", "handoff_service")
WP5 = "My carbon monoxide detector is going off."


def test_j5_co_alarm_instruction_first_and_p0_case(journey: JourneyRun) -> None:
    with journey.step(J5, "1 login", needs=SIGN_IN_NEEDS, operations=("login",)):
        signed = journey.login()
    with journey.step(J5, "2 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):
        start = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        assert start.status_code == 201
        thread_id = start.json()["thread_id"]
    turn_id = str(uuid.uuid4())
    with journey.step(
        J5, "3 CO alarm: instruction first, P0 case", needs=SAFETY_TURN_NEEDS, operations=("submitTurn",)
    ):
        calls_before = len(journey.script.calls)
        r = signed.client.call(
            "POST",
            f"/api/chat/sessions/{thread_id}/turns",
            operation_id="submitTurn",
            body={"turn_id": turn_id, "payload": {"kind": "text", "text": WP5}},
        )
        assert r.status_code == 200
        first = r.json()["blocks"][0]
        assert first["type"] == "safety"
        assert list(first["steps"]) == [TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH]]
        assert len(journey.script.calls) == calls_before
        assert journey.script.problems() == ()
        assert journey.db.count("spend_ledger", "turn_id = ?", (turn_id,)) == 0
        assert journey.db.count("cases", "thread_id = ?", (thread_id,)) == 1
        case = journey.db.one("SELECT * FROM cases WHERE thread_id = ?", (thread_id,))
        assert case["reason"] == "safety"
        assert case["priority"] == "P0"
        assert case["safety_kind"] == "co"
        assert case["handoff_trigger"] == "safety"
        assert case["rule_id"] == "R5.co"
        assert case["turn_id"] == turn_id
        assert first["case_reference"] == case["case_ref"]
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["gate_result"] == "safety"
        print(f"step 3: block=safety case={case['case_ref']} priority=P0 model_calls=0")
