"""FU-handoff-placeholders (AEA-55 F5), J-6 card text: WP-7's handoff card and a nobody-online CON-4 card
join (UXR-19) to the fixed sentences word for word. Level: integrated with a scripted model (real app, real graph, DB
copy, scripted model at the provider boundary; API level, no browser). Blocked by: none."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from meridian.policy.handoff import due_label
from meridian.policy.texts import TEXTS, TextId, render
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import blocks, open_chat
from tests.integration.customer_support import RunOptions, open_customer_run
from tests.unit.agent.nodes.compose_fixtures import join_uxr19

pytestmark = pytest.mark.journey

J6 = "J-6"
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
    "person_requests",
)


def _join(p: dict[str, Any]) -> str:
    return join_uxr19(p["promise_text"], p["due_label"], p["extra_lines"])


def _clean(text: str) -> None:
    assert "{" not in text and "}" not in text, text
    assert ".," not in text, text


def test_j6_handoff_cards_read_as_fixed_sentences(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        with run.step(
            J6, "1 WP-7 refund card", needs=NEEDS, operations=("login", "startChatSession", "submitTurn")
        ):
            res = sc.wp7(run, client)
            h = blocks(res.responses[-1], "handoff")[-1]
            ref = h["reference"]
            expected = " ".join(
                (
                    TEXTS[TextId.PROMISE_REFUND],
                    render(TextId.PROMISE_REFUND_NO_OUTCOME),
                    render(TextId.REFERENCE_LINE, case_ref=ref),
                )
            )
            assert _join(h) == expected
            _clean(_join(h))
            assert h["due_label"] is None
            assert datetime.fromisoformat(h["due_at"]) == datetime(2026, 10, 20, 19, 0, tzinfo=CHI)
            s = res.responses[-1].json()["settled"]["request"]
            assert s["reference"] == ref and _join(s) == expected
            print(f"step 1: {ref} refund card joins clean")
        with run.step(
            J6,
            "2 nobody-online person request card",
            needs=NEEDS,
            operations=("startChatSession", "requestPerson"),
        ):
            fresh = open_chat(run, client)
            r = client.call(
                "POST",
                f"/api/chat/sessions/{fresh.thread_id}/handoff",
                operation_id="requestPerson",
                body={"turn_id": str(uuid.uuid4())},
            )
            assert r.status_code == 200 and r.json()["result"] == "case_created"
            block = r.json()["block"]
            ref = block["reference"]
            due = due_label(datetime.fromisoformat(block["due_at"]))
            expected = render(TextId.PROMISE_UNSTAFFED, due_label=due, case_ref=ref)
            assert _join(block) == expected
            _clean(_join(block))
            assert block["due_label"] == f"by {due}"
            s = r.json()["settled"]["request"]
            assert s["reference"] == ref and _join(s) == expected
            print(f"step 2: {ref} person-request card joins clean")
