"""J-5 (slice plan section 0a), AEA-51 steps: the safety path first (WP-5), the DANGER raise, and NODANGER booking
normally. Real app and graph; scripted model at the provider boundary."""

from __future__ import annotations

import pytest

from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import blocks
from tests.integration.customer_support import RunOptions, open_customer_run

pytestmark = pytest.mark.journey

J5 = "J-5"
NEEDS = (
    "login_sessions",
    "session_service",
    "demo_service",
    "demo_clock",
    "reply_composer",
    "turn_service",
    "run_graph",
    "handoff_service",
)
OPS = ("login", "startChatSession", "submitTurn")


def test_j5_safety_first(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        with run.step(J5, "1 CO alarm: the instruction first, P0, no model", needs=NEEDS, operations=OPS):
            co = sc.wp5(run, client)
            first = blocks(co.responses[0])[0]
            assert first["type"] == "safety" and first["steps"][0].startswith("Leave the home immediately")
            assert (
                run.db.one("SELECT model_calls FROM turns WHERE turn_id = ?", (co.turn_ids[0],))[
                    "model_calls"
                ]
                == 0
            )
            [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (co.thread_id,))
            assert (case["reason"], case["priority"]) == ("safety", "P0")
            print(f"step 1: block=safety case={case['case_ref']} model_calls=0")
        with run.step(J5, "2 DANGER: the emergency number first, P1", needs=NEEDS, operations=OPS):
            danger = sc.danger(run, client)
            assert blocks(danger.responses[0])[0]["type"] == "emergency_line"
            [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (danger.thread_id,))
            assert (case["reason"], case["priority"]) == ("danger", "P1")
            print(f"step 2: block=emergency_line case={case['case_ref']}")
        with run.step(J5, "3 NODANGER: the normal path, no case", needs=NEEDS, operations=OPS):
            plain = sc.nodanger(run, client)
            types = [b["type"] for b in blocks(plain.responses[0])]
            assert "locate_prompt" in types and "emergency_line" not in types and "safety" not in types
            assert not run.db.rows("SELECT 1 FROM cases WHERE thread_id = ?", (plain.thread_id,))
            print(f"step 3: blocks={types} cases=0")
