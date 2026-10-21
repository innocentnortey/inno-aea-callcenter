"""J-4 (slice plan section 0a), AEA-51 steps: a change inside 24 hours is never written; a P2 staff request and an
honest promise are. Real app, real graph and DB copy, scripted model at the provider boundary."""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from meridian.policy.handoff import PROMISE_TABLE
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import blocks
from tests.integration.customer_support import RunOptions, open_customer_run

pytestmark = pytest.mark.journey

J4 = "J-4"
CHI = ZoneInfo("America/Chicago")
NEEDS = (
    "login_sessions",
    "session_service",
    "demo_service",
    "demo_clock",
    "reply_composer",
    "turn_service",
    "run_graph",
    "identity_service",
    "handoff_service",
    "case_service",
)
OPS = ("login", "startChatSession", "submitTurn")


def test_j4_fee_bearing_no_write(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        with run.step(J4, "1 the move is refused", needs=NEEDS, operations=OPS):
            result = sc.wp4(run)
            original = result.extra["original"]
            row = run.db.one(
                "SELECT status, slot_id FROM appointments WHERE appointment_id = ?",
                (result.extra["appointment_id"],),
            )
            assert (row["status"], row["slot_id"]) == ("scheduled", original["slot_id"])
            assert (
                run.db.count(
                    "actions", "thread_id = ? AND kind IN ('moved','cancelled')", (result.thread_id,)
                )
                == 0
            )
            print(f"step 1: appointment={result.extra['appointment_id']} unchanged")
        with run.step(J4, "2 a P2 staff request opens", needs=NEEDS, operations=OPS):
            [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (result.thread_id,))
            assert (case["reason"], case["priority"]) == ("fee_bearing_change", "P2")
            assert blocks(result.responses[-1], "change_request")
            print(f"step 2: case={case['case_ref']} priority=P2")
        with run.step(J4, "3 the promise is honest", needs=NEEDS, operations=OPS):
            promise = run.db.one("SELECT * FROM promises WHERE case_ref = ?", (case["case_ref"],))
            assert promise["text"] == PROMISE_TABLE["R26.unstaffed"]
            extra = json.loads(promise["extra_lines"])
            assert any("can't promise" in line for line in extra)
            due = datetime.fromisoformat(promise["due_at"].replace("Z", "+00:00"))
            assert due == datetime(2026, 10, 19, 19, 0, tzinfo=CHI)
            print(f"step 3: promise_row={promise['policy_row']} extra_lines={len(extra)}")
