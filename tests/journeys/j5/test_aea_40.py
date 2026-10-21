"""J-5 at the spend cap (AEA-40-F1, DO-4 section 11): the day's spend reaches the cap, a CO-alarm message still gets
the safety card first and one P0 case with no model call, and a normal message gets SPEND_CAP_REACHED (J-9 leg).

Level target: integrated with a scripted model. Blocked by AEA-51 (and AEA-57's harness): the turn steps report
blocked until `run_graph` and `reply_composer` are bound. The run record's spend total includes one synthetic ledger
row worth the daily cap, written to reach the cap; no model was paid.
"""

from __future__ import annotations

import uuid

import pytest

from meridian.domain.turn import TurnIds
from meridian.policy.texts import TEXTS, TextId
from meridian.ports.models import CallRecord
from meridian.services.ledger import LedgerService
from meridian.web.container import Key
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J5 = "J-5"
J9 = "J-9"
SIGN_IN_NEEDS = ("login_sessions", "demo_clock")
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
CAP_NEEDS = ("ledger",)
TURN_NEEDS = (*CHAT_NEEDS, "turn_service", "run_graph")
SAFETY_TURN_NEEDS = (*TURN_NEEDS, "handoff_service")
WP5 = "My carbon monoxide detector is going off."
NORMAL = "How much is a furnace tune-up?"


def _ids() -> TurnIds:
    return TurnIds.model_validate(
        {
            "thread_id": str(uuid.uuid4()), "turn_id": str(uuid.uuid4()), "request_id": str(uuid.uuid4()),
            "run_tag": "live", "run_id": None, "agent_version": "test-agent-0",
        }
    )  # fmt: skip


def _call(cost: float) -> CallRecord:
    return CallRecord.model_validate(
        {
            "provider": "anthropic", "model": "claude-sonnet-test", "latency_ms": 1200, "input_tokens": 9000,
            "output_tokens": 700, "cache_read_tokens": 0, "cache_write_tokens": 0, "thinking_tokens": 0,
            "cost_usd": cost, "cost_source": "price_table", "status": "ok", "failure": None,
            "provider_request_id": None, "stop_reason": "end_turn", "role": "responder", "attempt": 1,
        }
    )  # fmt: skip


def test_j5_co_alarm_at_spend_cap_still_gets_safety_card(journey: JourneyRun) -> None:
    with journey.step(J5, "1 login", needs=SIGN_IN_NEEDS, operations=("login",)):
        signed = journey.login()
    with journey.step(J5, "2 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):
        start = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        assert start.status_code == 201
        thread_id = start.json()["thread_id"]
    with journey.step(J5, "3 day's spend reaches the cap", needs=CAP_NEEDS):
        ledger = journey.container.get(Key[LedgerService]("ledger"))
        ledger.record(_call(journey.container.limits.spend.daily_cap_usd), _ids())
        assert ledger.allow_turn() is False
    turn_id = str(uuid.uuid4())
    with journey.step(
        J5,
        "4 CO alarm at the cap: instruction first, P0 case",
        needs=SAFETY_TURN_NEEDS,
        operations=("submitTurn",),
    ):
        calls_before = len(journey.script.calls)
        r = signed.client.call(
            "POST",
            f"/api/chat/sessions/{thread_id}/turns",
            operation_id="submitTurn",
            body={"turn_id": turn_id, "payload": {"kind": "text", "text": WP5}},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["notice"] is None
        first = body["blocks"][0]
        assert first["type"] == "safety"
        assert list(first["steps"]) == [TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH]]
        assert len(journey.script.calls) == calls_before
        assert journey.script.problems() == ()
        assert journey.db.count("spend_ledger", "turn_id = ?", (turn_id,)) == 0
        assert journey.db.count("cases", "thread_id = ?", (thread_id,)) == 1
        case = journey.db.one("SELECT * FROM cases WHERE thread_id = ?", (thread_id,))
        assert case["priority"] == "P0"
        assert case["reason"] == "safety"
        assert first["case_reference"] == case["case_ref"]
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["status"] == "completed"
        assert turn["gate_result"] == "safety"
        assert turn["outcome"] == "safety_reply"
        print(f"step 4: block=safety case={case['case_ref']} priority=P0 model_calls=0")
    turn2 = str(uuid.uuid4())
    with journey.step(
        J9, "5 normal question at the cap: SPEND_CAP_REACHED", needs=TURN_NEEDS, operations=("submitTurn",)
    ):
        calls_before = len(journey.script.calls)
        r2 = signed.client.call(
            "POST",
            f"/api/chat/sessions/{thread_id}/turns",
            operation_id="submitTurn",
            body={"turn_id": turn2, "payload": {"kind": "text", "text": NORMAL}},
        )
        assert r2.status_code == 200
        notice = r2.json()["notice"]
        assert notice["code"] == "SPEND_CAP_REACHED"
        assert notice["actions"] == ["talk_to_person"]
        assert len(journey.script.calls) == calls_before
        row = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn2,))
        assert (row["status"], row["outcome"], row["degrade_reason"]) == (
            "failed", "degraded_handoff", "spend_cap",
        )  # fmt: skip
        assert journey.db.count("messages", "turn_id = ?", (turn2,)) == 0
        print("step 5: notice=SPEND_CAP_REACHED model_calls=0")
