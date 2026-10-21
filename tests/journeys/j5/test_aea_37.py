"""J-5 (slice plan section 0a), AEA-37 steps: DANGER reaches the safety path by the classifier raise (two Jev routing
calls, the emergency line first, one P1 case) and NODANGER books normally (locate prompt, no case). API level on
AEA-57's harness with the scripted model; the turn steps are reported blocked until AEA-40, AEA-51 and AEA-29 bind
their services.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx
import pytest

from meridian.domain.common import Role
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J5 = "J-5"
SIGN_IN_NEEDS = ("login_sessions", "demo_clock")
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
TURN_NEEDS = (*CHAT_NEEDS, "turn_service", "run_graph")
DANGER_TURN_NEEDS = (*TURN_NEEDS, "handoff_service")
DANGER = "my mother is 88 and it's 95 degrees in here"
NODANGER = "my AC isn't cooling"
BOOK_RAW = (
    '{"knowledge": "no", "account": "none", "scheduling": "book_new", "handoff": "none", "topic": "booking"}'
)
DANGER_RAW = '{"danger_level": "danger"}'
NORMAL_RAW = '{"danger_level": "normal"}'
RESPONDER_RAW = json.dumps({"text": "I can help book a visit for that. First I need to find your account."})


def open_chat(journey: JourneyRun) -> tuple[JourneyClient, str]:
    with journey.step(J5, "1 login", needs=SIGN_IN_NEEDS, operations=("login",)):
        signed = journey.login()
    with journey.step(J5, "2 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):
        start = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        assert start.status_code == 201
    return signed.client, str(start.json()["thread_id"])


def submit(client: JourneyClient, thread_id: str, turn_id: str, text: str) -> httpx.Response:
    return client.call(
        "POST",
        f"/api/chat/sessions/{thread_id}/turns",
        operation_id="submitTurn",
        body={"turn_id": turn_id, "payload": {"kind": "text", "text": text}},
    )


def classifier_events(journey: JourneyRun, turn_id: str) -> list[dict[str, Any]]:
    return journey.db.rows(
        "SELECT * FROM check_events WHERE turn_id = ? AND check_kind = 'classifier'", (turn_id,)
    )


def test_j5_danger_raise_reaches_safety(journey: JourneyRun) -> None:
    client, thread_id = open_chat(journey)
    turn_id = str(uuid.uuid4())
    with journey.step(
        J5,
        "3 DANGER: classifier raise, emergency line first, P1 case",
        needs=DANGER_TURN_NEEDS,
        operations=("submitTurn",),
    ):
        journey.script.add(Role.PLANNER, BOOK_RAW)
        journey.script.add(Role.CLASSIFIER, DANGER_RAW)
        calls_before = len(journey.script.calls)
        r = submit(client, thread_id, turn_id, DANGER)
        assert r.status_code == 200
        blocks = r.json()["blocks"]
        assert blocks[0]["type"] == "emergency_line"
        assert "locate_prompt" not in [x["type"] for x in blocks]
        assert sorted(c.role.value for c in journey.script.calls[calls_before:]) == ["classifier", "planner"]
        assert journey.script.problems() == ()
        assert journey.script.remaining() == 0
        assert journey.db.count("spend_ledger", "turn_id = ?", (turn_id,)) == 2
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["gate_result"] == "danger"
        assert turn["danger_raised"] == 1
        assert turn["outcome"] == "safety_reply"
        assert turn["path"] == "danger"
        ev = classifier_events(journey, turn_id)
        assert len(ev) == 1
        assert ev[0]["result"] == "raised"
        assert json.loads(ev[0]["codes"]) == ["danger"]
        assert journey.db.count("cases", "thread_id = ?", (thread_id,)) == 1
        case = journey.db.one("SELECT * FROM cases WHERE thread_id = ?", (thread_id,))
        assert case["reason"] == "danger"
        assert case["priority"] == "P1"
        assert case["handoff_trigger"] == "safety"
        assert case["rule_id"] == "R47.classifier_danger"
        assert case["turn_id"] == turn_id
        assert blocks[0]["case_reference"] == case["case_ref"]
        print(f"step 3: block=emergency_line case={case['case_ref']} priority=P1 model_calls=2")


def test_j5_nodanger_books_normally(journey: JourneyRun) -> None:
    client, thread_id = open_chat(journey)
    turn_id = str(uuid.uuid4())
    with journey.step(
        J5, "3 NODANGER: normal booking, no case", needs=TURN_NEEDS, operations=("submitTurn",)
    ):
        journey.script.add(Role.PLANNER, BOOK_RAW)
        journey.script.add(Role.CLASSIFIER, NORMAL_RAW)
        journey.script.add(Role.RESPONDER, RESPONDER_RAW)
        calls_before = len(journey.script.calls)
        r = submit(client, thread_id, turn_id, NODANGER)
        assert r.status_code == 200
        types = [x["type"] for x in r.json()["blocks"]]
        assert types.count("locate_prompt") == 1
        assert "emergency_line" not in types
        assert "safety" not in types
        assert {c.role for c in journey.script.calls[calls_before:]} == {
            Role.PLANNER,
            Role.CLASSIFIER,
            Role.RESPONDER,
        }
        assert journey.script.problems() == ()
        assert journey.script.remaining() == 0
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["gate_result"] == "clear"
        assert turn["danger_raised"] == 0
        assert turn["plan_mode"] == "act"
        assert turn["plan_source"] == "planner"
        assert json.loads(turn["plan_intents"]) == ["book_new"]
        assert turn["plan_topic"] == "booking"
        assert turn["planner_failed"] == 0
        ev = classifier_events(journey, turn_id)
        assert len(ev) == 1
        assert ev[0]["result"] == "pass"
        assert json.loads(ev[0]["codes"]) == ["normal"]
        assert journey.db.count("cases", "thread_id = ?", (thread_id,)) == 0
        print(f"step 3: types={types} intents={turn['plan_intents']} cases=0")
