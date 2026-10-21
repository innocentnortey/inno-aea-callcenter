"""J-5 (slice plan section 0a), AEA-60's leg: a malformed classifier reply never blocks a normal booking turn.

The provider's raw body `{"danger_level": "emergency"}` is not one of the three labels, so the adapter refuses it,
the classifier falls back to `normal` (raise-only, R-47), and the turn books as usual: locate prompt, no case, a
`classifier` check event with the fallback codes. API level on AEA-57's harness with the scripted model; the turn
step is reported blocked until its services are bound, never passed another way.
"""

from __future__ import annotations

import json
import uuid

import pytest

from meridian.domain.common import Role
from tests.journeys.j5.test_aea_37 import BOOK_RAW, NODANGER, RESPONDER_RAW, TURN_NEEDS, open_chat, submit
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J5 = "J-5"
EMERGENCY_RAW = '{"danger_level": "emergency"}'  # a label the classifier does not offer


def test_j5_malformed_classifier_reply_books_normally(journey: JourneyRun) -> None:
    client, thread_id = open_chat(journey)
    turn_id = str(uuid.uuid4())
    with journey.step(
        J5,
        "3 malformed classifier reply: normal booking, fallback event, no case",
        needs=TURN_NEEDS,
        operations=("submitTurn",),
    ):
        journey.script.add(Role.PLANNER, BOOK_RAW)
        journey.script.add(Role.CLASSIFIER, EMERGENCY_RAW)
        journey.script.add(Role.RESPONDER, RESPONDER_RAW)
        r = submit(client, thread_id, turn_id, NODANGER)
        assert r.status_code == 200
        types = [x["type"] for x in r.json()["blocks"]]
        assert types.count("locate_prompt") == 1
        assert "emergency_line" not in types
        assert "safety" not in types
        assert journey.db.count("cases", "thread_id = ?", (thread_id,)) == 0
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["danger_raised"] == 0
        assert json.loads(turn["plan_intents"]) == ["book_new"]
        events = journey.db.rows(
            "SELECT * FROM check_events WHERE turn_id = ? AND check_kind = 'classifier'", (turn_id,)
        )
        assert len(events) == 1
        assert events[0]["result"] == "fallback"
        assert json.loads(events[0]["codes"]) == ["fallback", "invalid_output"]
        assert [(c.role, c.result) for c in journey.script.problems()] == [
            (Role.CLASSIFIER, "invalid_output")
        ]
        assert journey.script.remaining() == 0
        print(f"step 3: types={types} cases=0 classifier_event=fallback")
