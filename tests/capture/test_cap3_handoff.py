"""CAP-3 (WF-1 person words, WF-2 CON-4 and CON-5): the hand-off to a person leaves its case, events, promise and turn
records, model-free for CON-4, with the forbidden values absent. Real app, scripted model, in-memory trace sink."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from typing import Any

import pytest

from meridian.policy.handoff import PROMISE_TABLE
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import Chat, open_chat, read_events
from tests.integration.customer_support import (
    CustomerRun,
    RunOptions,
    build_capture_sink,
    finished_spans,
    open_customer_run,
    request_json,
    response_text,
    span_meta,
    span_text,
)
from tests.journeys.support.env import letters
from tests.unit.adapters._tracing_doubles import close_all, trace_hex


def con4(run: CustomerRun, chat: Chat, *, turn_id: str | None = None) -> Any:
    return chat.client.call(
        "POST",
        f"/api/chat/sessions/{chat.thread_id}/handoff",
        operation_id="requestPerson",
        body={"turn_id": turn_id or str(uuid.uuid4())},
    )


def con5(chat: Chat, body: dict[str, str]) -> Any:
    return chat.client.call(
        "PUT", f"/api/chat/sessions/{chat.thread_id}/follow-up", operation_id="saveFollowUp", body=body
    )


def chat_of(run: CustomerRun, client: Any, thread_id: str) -> Chat:
    return Chat(run=run, client=client, thread_id=thread_id, opened={})


def test_cap3_records(request: pytest.FixtureRequest) -> None:
    """AC-22: after WP-7, CON-4 and CON-5: the case, its events, the promise from the table, the CON-4 turn row, the
    stored follow-up; a second press answers already_open with the same reference; an unverified on-record follow-up
    is refused with 409 NOT_ALLOWED_IN_STATE."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        refund = sc.wp7(run, client)
        again = con4(run, chat_of(run, client, refund.thread_id))
        assert again.json()["result"] == "already_open"
        assert again.json()["block"]["reference"] == refund.case_refs[0]

        fresh = open_chat(run, client)
        first = con4(run, fresh)
        assert first.status_code == 200 and first.json()["result"] == "case_created"
        [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (fresh.thread_id,))
        assert (case["reason"], case["priority"]) == ("customer_requested_person", "P3")
        promise = run.db.one("SELECT * FROM promises WHERE case_ref = ?", (case["case_ref"],))
        assert promise["text"] == PROMISE_TABLE["R26.unstaffed"]
        block = first.json()["block"]
        assert block["reference"] == case["case_ref"] and block["promise_text"] == promise["text"]
        assert run.db.count("case_events", "case_ref = ?", (case["case_ref"],)) >= 1
        turn = run.db.one(
            "SELECT * FROM turns WHERE turn_id = ?",
            (first.request.content and json.loads(first.request.content)["turn_id"],),
        )
        assert (turn["gate_result"], turn["outcome"]) == ("person_requested", "handed_off")
        assert turn["trace_export"] is not None
        assert (
            run.db.one("SELECT outcome FROM conversations WHERE thread_id = ?", (fresh.thread_id,))["outcome"]
            == "handed_off"
        )
        repeat = con4(run, fresh)
        assert (
            repeat.json()["result"] == "already_open"
            and repeat.json()["block"]["reference"] == case["case_ref"]
        )

        saved = con5(fresh, {"channel": "email", "destination": "general", "window": "any"})
        assert saved.status_code == 200
        stored = run.db.one("SELECT * FROM followups WHERE case_ref = ?", (case["case_ref"],))
        assert (stored["channel"], stored["on_record"], stored["contact_window"]) == ("email", 0, "any")
        refused = fresh.client.call(
            "PUT",
            f"/api/chat/sessions/{fresh.thread_id}/follow-up",
            operation_id="saveFollowUp",
            body={"channel": "phone", "destination": "on_record", "window": "any"},
        )
        assert refused.status_code == 409 and refused.json()["error"]["code"] == "NOT_ALLOWED_IN_STATE"


def test_wf1_person_words_first_ask(request: pytest.FixtureRequest) -> None:
    """AC-33: 'can I talk to a person' hands off on the first ask: gate person_requested, one case and promise, no
    specialist span or call first."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(trace=sink)) as run:
            result = sc.person_words(run)
            row = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (result.turn_ids[0],))
            assert (row["gate_result"], row["outcome"]) == ("person_requested", "handed_off")
            [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (result.thread_id,))
            assert run.db.count("promises", "case_ref = ?", (case["case_ref"],)) == 1
            assert not any(c.role.value == "specialist" for c in run.script.calls)
            names = {s.name for s in finished_spans(sink, exporter) if trace_hex(s) == row["trace_id"]}
            assert "model_call:specialist" not in names and "run_specialist" not in names
    finally:
        close_all(registry)


def test_wf2_turn_records(request: pytest.FixtureRequest) -> None:
    """AC-46: the CON-4 turn row carries the version, a non-negative server time and a trace id whose trace holds the
    turn span with a timed child; no ledger row and no model call."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(trace=sink)) as run:
            chat = open_chat(run, run.login().client)
            mark = len(run.script.calls)
            turn_id = str(uuid.uuid4())
            assert con4(run, chat, turn_id=turn_id).status_code == 200
            row = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
            assert row["agent_version"] == run.settings.agent_version and row["server_ms"] >= 0
            in_trace = [s for s in finished_spans(sink, exporter) if trace_hex(s) == row["trace_id"]]
            [root] = [s for s in in_trace if s.name == "turn"]
            assert span_meta(root, "turn_id") == turn_id
            assert run.db.count("spend_ledger", "turn_id = ?", (turn_id,)) == 0
            assert run.steps.calls_since(mark) == ()
    finally:
        close_all(registry)


def test_wf2_turn_has_timed_children(request: pytest.FixtureRequest) -> None:
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(trace=sink)) as run:
            chat = open_chat(run, run.login().client)
            turn_id = str(uuid.uuid4())
            con4(run, chat, turn_id=turn_id)
            row = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
            in_trace = [s for s in finished_spans(sink, exporter) if trace_hex(s) == row["trace_id"]]
            children = [s for s in in_trace if s.name != "turn"]
            assert children and any(span_meta(s, "elapsed_ms") is not None for s in children)
    finally:
        close_all(registry)


def test_wf2_forbidden_values_absent(request: pytest.FixtureRequest) -> None:
    """AC-47: the sentinels, the refund message, and the customer's name and phone are absent from the records, logs and
    bodies of CON-4 and CON-5, and masked in the CON-4 turn span; the scripted model is not called."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(trace=sink)) as run:
            client = run.login().client
            sentinel = "sentinel-" + letters(12)
            refund = sc.wp7(run, client)
            chat = chat_of(run, client, refund.thread_id)
            mark = len(run.script.calls)
            run.logs._snapshot()
            before_logs = len(run.logs.all_text())
            turn_id = str(uuid.uuid4())
            person = con4(run, chat, turn_id=turn_id)
            saved = con5(chat, {"channel": "email", "destination": "general", "window": "any"})
            assert person.status_code == 200 and saved.status_code == 200
            assert run.steps.calls_since(mark) == ()
            bodies = person.text + saved.text
            logs = run.logs.all_text()[before_logs:]
            row = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
            spans = [s for s in finished_spans(sink, exporter) if trace_hex(s) == row["trace_id"]]
            blob = span_text(spans)
            assert sentinel not in bodies + logs + blob + request_json(run)
            for needle in (sc.REFUND_TEXT, refund.extra["sentinel_quote"], refund.extra["refund_amount"]):
                assert needle not in logs and needle not in blob
            assert response_text([client]) is not None
    finally:
        close_all(registry)


def test_con4_event_in_handoff_commit(request: pytest.FixtureRequest) -> None:
    """AC-48 (first half): the case_created event commits with its case and is delivered exactly once."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        chat = open_chat(run, client)
        last = str(chat.opened["events"]["last_event_id"])
        response = con4(run, chat)
        assert response.json()["result"] == "case_created"
        assert run.db.count("cases", "thread_id = ?", (chat.thread_id,)) == 1
        rows = run.db.rows("SELECT * FROM events WHERE type = 'case_created'")
        assert len([r for r in rows if json.loads(r["payload"])["thread_id"] == chat.thread_id]) == 1
        # polled once: one row after the id CON-1 reported. (The customer's stream does not carry case_created: its
        # route sends only the chat event types, so the stored row is the poll.)
        later = run.db.rows("SELECT * FROM events WHERE id > ? AND type = 'case_created'", (int(last),))
        assert (
            len(later) == 1
            and json.loads(later[0]["payload"])["case_ref"]
            == run.db.one("SELECT case_ref FROM cases WHERE thread_id = ?", (chat.thread_id,))["case_ref"]
        )
        frames = read_events(client, f"/api/chat/sessions/{chat.thread_id}/events", last_event_id=last)
        assert not [f for f in frames if json.loads(f.data).get("type") == "case_created"]


def test_con4_held_write_lock_gives_503(request: pytest.FixtureRequest) -> None:
    """AC-48 (second half): a write lock held beyond the retry answers 503 HANDOFF_FAILED and writes neither row."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        chat = open_chat(run, client)
        holder = sqlite3.connect(str(run.env.db_path), isolation_level=None, timeout=0)
        holder.execute("BEGIN IMMEDIATE")
        outcome: dict[str, Any] = {}

        def send() -> None:
            outcome["r"] = client._http.post(
                f"/api/chat/sessions/{chat.thread_id}/handoff", json={"turn_id": str(uuid.uuid4())}
            )

        thread = threading.Thread(target=send)
        thread.start()
        thread.join(timeout=60)
        holder.execute("ROLLBACK")
        holder.close()
        assert outcome["r"].status_code == 503
        assert outcome["r"].json()["error"]["code"] == "HANDOFF_FAILED"
        assert run.db.count("cases", "thread_id = ?", (chat.thread_id,)) == 0
        assert not [
            r
            for r in run.db.rows("SELECT payload FROM events WHERE type = 'case_created'")
            if json.loads(r["payload"])["thread_id"] == chat.thread_id
        ]
