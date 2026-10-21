"""AEA-51 AC-23 (WF-4, GRC-3 option A): a customer turn while a representative holds the chat is relayed, not answered.

The AI is paused: the customer gets the AI_PAUSED notice with delivered_to_representative, the representative's stream
(CON-21) carries the customer's message in its STORE-redacted form, no model is called, and a carbon monoxide message
still gets the fixed safety card without handing the chat back.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from meridian.privacy.redact import RedactionProfile, redact
from tests.api.openapi_check import SseFrame, assert_sse_frames_match
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import blocks, open_chat, read_events, say, set_staffing, switch_role
from tests.integration.customer_support import RunOptions, open_customer_run
from tests.journeys.support.client import JourneyClient


def read_case_events(client: JourneyClient, reference: str, *, seconds: float = 2.0) -> list[SseFrame]:
    return read_events(client, f"/api/staff/cases/{reference}/events", seconds=seconds)


def test_relayed_turn_while_representative_holds_chat(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        set_staffing(client, "simulated_on_shift")
        chat = open_chat(run, client)
        # a refund request while someone is on shift: the case is live-queued
        run.steps.set_step(
            {
                sc.Role.PLANNER: sc.planner(handoff="refund", topic="billing"),
                sc.Role.CLASSIFIER: sc.NORMAL,
                sc.Role.RESPONDER: sc.responder("A representative has been asked to join."),
                sc.Role.BRIEF: sc.brief(
                    needs=[{"message_id": sc.next_message_id(run), "text": sc.REFUND_TEXT[:20]}],
                    claims=[],
                    open_decision="Decide on the refund request.",
                ),
            }
        )
        say(chat, sc.REFUND_TEXT)
        [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (chat.thread_id,))
        assert case["lifecycle"] == "live_queued"
        assert (
            run.db.one("SELECT live_state FROM conversations WHERE thread_id = ?", (chat.thread_id,))[
                "live_state"
            ]
            == "queued"
        )

        # a representative claims the case and joins the chat (CON-13, CON-14)
        switch_role(client, "representative")
        reference = case["case_ref"]
        got = client.call("GET", f"/api/staff/cases/{reference}", operation_id="getCase")
        assert got.status_code == 200
        claimed = client.call(
            "POST",
            f"/api/staff/cases/{reference}/actions",
            operation_id="applyCaseAction",
            body={"action": "claim", "expected_version": got.json()["case"]["version"]},
        )
        assert claimed.status_code == 200
        joined = client.call(
            "POST",
            f"/api/staff/cases/{reference}/live",
            operation_id="liveChatAction",
            body={"action": "join"},
        )
        assert joined.status_code == 200
        assert (
            run.db.one("SELECT controller FROM conversations WHERE thread_id = ?", (chat.thread_id,))[
                "controller"
            ]
            == "human"
        )

        # the customer writes again: relayed, not answered, no model call
        switch_role(client, "customer")
        run.steps.set_step({})
        mark = len(run.script.calls)
        text = "Are you still there?"
        reply = say(chat, text)
        notice = reply.json()["notice"]
        assert notice["code"] == "AI_PAUSED" and notice["delivered_to_representative"] is True
        turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (reply.json()["turn_id"],))
        assert turn["outcome"] == "to_staff"
        assert run.steps.calls_since(mark) == ()
        assert run.db.count("messages", "thread_id = ? AND text = ?", (chat.thread_id, text)) == 1

        # CON-21: the representative's stream carries the message as stored (STORE profile)
        switch_role(client, "representative")
        frames = read_case_events(client, reference)
        assert_sse_frames_match(frames, "streamCaseEvents")
        relayed = [f for f in frames if json.loads(f.data).get("type") == "customer_message"]
        assert len(relayed) == 1, [json.loads(f.data).get("type") for f in frames]
        payload: dict[str, Any] = json.loads(relayed[0].data)
        assert redact(text, RedactionProfile.STORE).text in json.dumps(payload)

        # a carbon monoxide message while paused: the safety card, still delivered, the controller stays human
        switch_role(client, "customer")
        mark = len(run.script.calls)
        alarm = say(chat, sc.CO_TEXT)
        first = blocks(alarm)[0]
        assert first["type"] == "safety" and first["steps"][0].startswith("Leave the home immediately")
        alarm_turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (alarm.json()["turn_id"],))
        assert (alarm_turn["gate_result"], alarm_turn["outcome"]) == ("safety", "safety_reply")
        # still delivered: the representative's stream carries the alarm message too (the response itself has no notice)
        switch_role(client, "representative")
        later = [json.loads(f.data).get("type") for f in read_case_events(client, reference)]
        assert later.count("customer_message") == 2
        switch_role(client, "customer")
        assert (
            run.db.one("SELECT controller FROM conversations WHERE thread_id = ?", (chat.thread_id,))[
                "controller"
            ]
            == "human"
        )
        assert run.steps.calls_since(mark) == ()
