"""J-9 (slice plan section 0a), AEA-60's legs: malformed provider output reaches the documented fallback through the
real server, and what the user sees and what is stored agree.

(a) both routing models answer wrongly: the turn hands off, degraded, with an `ai_failure` P3 case and its reference
    and promise on screen;
(b) the responder's draft is invalid: the failure offer with the person key, no case.

API level on AEA-57's harness with the scripted model. Steps whose services are not yet bound are reported
`blocked-on ...` by the harness; nothing here passes them another way.
"""

from __future__ import annotations

import json
import uuid

import pytest

from meridian.domain.common import Role
from tests.journeys.j5.test_aea_37 import BOOK_RAW, NODANGER, NORMAL_RAW, TURN_NEEDS, submit
from tests.journeys.j5.test_aea_37 import open_chat as open_chat_j5
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J9 = "J-9"
HANDOFF_NEEDS = (*TURN_NEEDS, "handoff_service", "case_service")
PLANNER_MAYBE = (
    '{"knowledge": "maybe", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"}'
)
FALLBACK_EXTRA = (
    '{"knowledge": "no", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other", '
    '"urgency": "today"}'
)
BRIEF_RAW = json.dumps({"needs": [{"message_id": 1, "text": "question"}], "claims": [], "open_decision": ""})
DRAFT_RAW = json.dumps({"text": "Thanks for your message."})


def test_j9_both_planners_malformed_hand_off_degraded(journey: JourneyRun) -> None:
    client, thread_id = open_chat_j5(journey)
    turn_id = str(uuid.uuid4())
    with journey.step(
        J9,
        "4a both routing models malformed: degraded handoff, ai_failure P3 case",
        needs=HANDOFF_NEEDS,
        operations=("submitTurn",),
    ):
        journey.script.add(Role.PLANNER, PLANNER_MAYBE)
        journey.script.add(Role.CLASSIFIER, NORMAL_RAW)
        journey.script.add(Role.PLANNER_FALLBACK, FALLBACK_EXTRA)
        journey.script.add(Role.RESPONDER, DRAFT_RAW)
        journey.script.add(Role.BRIEF, BRIEF_RAW)
        r = submit(client, thread_id, turn_id, "Hello, I have a question.")
        assert r.status_code == 200
        handoffs = [b for b in r.json()["blocks"] if b["type"] == "handoff"]
        assert len(handoffs) == 1
        case = journey.db.one("SELECT * FROM cases WHERE thread_id = ?", (thread_id,))
        assert handoffs[0]["reference"] == case["case_ref"]
        assert handoffs[0]["promise_text"]
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["outcome"] == "degraded_handoff"
        assert turn["degrade_reason"] == "model_error"
        assert turn["planner_failed"] == 1
        assert journey.db.count("cases", "thread_id = ?", (thread_id,)) == 1
        assert case["reason"] == "ai_failure"
        assert case["priority"] == "P3"
        problems = sorted((c.role.value, c.result) for c in journey.script.problems())
        assert problems == [("planner", "invalid_output"), ("planner_fallback", "invalid_output")]
        print(f"step 4a: handoff reference={case['case_ref']} reason=ai_failure priority=P3")


def test_j9_malformed_responder_draft_falls_back(journey: JourneyRun) -> None:
    client, thread_id = open_chat_j5(journey)
    turn_id = str(uuid.uuid4())
    with journey.step(
        J9,
        "4b invalid responder draft: failure offer with the person key, no case",
        needs=TURN_NEEDS,
        operations=("submitTurn",),
    ):
        journey.script.add(Role.PLANNER, BOOK_RAW)
        journey.script.add(Role.CLASSIFIER, NORMAL_RAW)
        journey.script.add(Role.RESPONDER, '{"text": ""}')
        r = submit(client, thread_id, turn_id, NODANGER)
        assert r.status_code == 200
        blocks = r.json()["blocks"]
        offers = [b for b in blocks if b["type"] == "failure_offer"]
        assert len(offers) == 1 and offers[0]["person_key"] is True
        assert not [b for b in blocks if b["type"] == "text"]
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["outcome"] == "degraded_handoff"
        assert turn["degrade_reason"] == "model_error"
        assert journey.db.count("cases", "thread_id = ?", (thread_id,)) == 0
        problems = [(c.role.value, c.result) for c in journey.script.problems()]
        assert problems == [("responder", "invalid_output")]
        print("step 4b: failure_offer person_key=true cases=0")
