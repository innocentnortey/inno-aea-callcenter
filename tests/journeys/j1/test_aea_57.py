"""J-1 (slice plan section 0a): login, start a session, one turn, refresh/resume the same thread; guards redirect when
signed out. API level: the real app, container, middleware and guards, a disposable DB copy and a scripted model at the
provider boundary (AEA-57). Steps whose services are not bound yet are reported blocked, never passed.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import httpx
import pytest

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.domain.common import Role
from meridian.policy.texts import TextId, render
from tests.journeys.support.client import JourneyClient, cookie_attributes, set_cookie_lines
from tests.journeys.support.env import (
    PLACEHOLDER_ANTHROPIC_KEY,
    PLACEHOLDER_OPENROUTER_KEY,
    REPO_ROOT,
    letters,
)
from tests.journeys.support.record import build_record_data, render_record
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import role_specs

pytestmark = pytest.mark.journey

J1 = "J-1"
LOGIN_NEEDS = ("login_sessions",)
SIGN_IN_NEEDS = ("login_sessions", "demo_clock")  # a successful login reads the demo clock (AEA-30)
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
SUBMIT_NEEDS = (*CHAT_NEEDS, "turn_service")
TURN_NEEDS = (*SUBMIT_NEEDS, "run_graph")

CUSTOMER_TEXT = "Hi, what can you help me with?"
RESPONDER_TEXT = (
    "I can answer questions about memberships, billing and warranties, or help you find a time for a service "
    "visit. What would you like to do?"
)
PLANNER_RAW = (
    '{"knowledge": "no", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"}'
)
CLASSIFIER_RAW = '{"danger_level": "normal"}'
SENTINEL = "zqrejectedsentinel"


def start_session(journey: JourneyRun, client: JourneyClient) -> httpx.Response:
    response = client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
    assert response.status_code == 201
    return response


def submit(client: JourneyClient, thread_id: str, turn_id: str, text: str) -> httpx.Response:
    return client.call(
        "POST",
        f"/api/chat/sessions/{thread_id}/turns",
        operation_id="submitTurn",
        body={"turn_id": turn_id, "payload": {"kind": "text", "text": text}},
    )


def thread_counts(journey: JourneyRun, thread_id: str) -> dict[str, int]:
    counts = {
        table: journey.db.count(table, "thread_id = ?", (thread_id,))
        for table in ("messages", "turns", "spend_ledger")
    }
    counts["conversations"] = journey.db.count("conversations", "thread_id = ?", (thread_id,))
    return counts


def request_record(journey: JourneyRun, response: httpx.Response) -> dict[str, Any]:
    rid = response.headers["X-Request-ID"]
    return journey.logs.wait_for("request", lambda r: r["request_id"] == rid)


def error_of(response: httpx.Response) -> dict[str, Any]:
    error = response.json()["error"]
    assert isinstance(error, dict)
    return error


def sign_in(journey: JourneyRun) -> Any:
    with journey.step(J1, "3 login", needs=SIGN_IN_NEEDS, operations=("login",)):
        signed = journey.login()
        assert signed.response.json()["session"]["role"] == "customer"
        return signed


def test_j1_guards_and_login(journey: JourneyRun) -> None:
    with journey.step(J1, "1 signed out", needs=LOGIN_NEEDS):
        client = journey.client()
        thread = client.call("GET", f"/api/chat/sessions/{uuid.uuid4()}", operation_id="getChatThread")
        assert thread.status_code == 401
        assert error_of(thread)["code"] == "UNAUTHENTICATED"
        assert error_of(thread)["details"] == {"reason": "none"}
        page = client.call("GET", "/staff/queue", operation_id=None)
        assert page.status_code == 303
        assert page.headers["location"] == "/login?return_to=%2Fstaff%2Fqueue&reason=none"
        assert journey.db.count("staff_sessions") == 0
        print(
            f"step 1: API {thread.status_code}; page {page.status_code} Location={page.headers['location']}"
        )

    with journey.step(J1, "2 wrong login", needs=LOGIN_NEEDS, operations=("login",)):
        wrong = journey.client().call(
            "POST",
            "/api/login",
            operation_id="login",
            body={"username": journey.demo_username, "password": "wrongpass" + letters(12)},
        )
        assert wrong.status_code == 401
        assert error_of(wrong)["code"] == "LOGIN_FAILED"
        assert not [c for c in set_cookie_lines(wrong) if c.startswith("mhc_session=")]
        assert journey.db.count("staff_sessions") == 0
        print(f"step 2: {wrong.status_code} {error_of(wrong)['code']}")

    signed = sign_in(journey)
    with journey.step(J1, "3 login cookie and row", needs=SIGN_IN_NEEDS, operations=("login",)):
        body = signed.response.json()
        assert body["session"]["authenticated"] is True
        assert body["landing"] == "/"
        lines = [c for c in set_cookie_lines(signed.response) if c.startswith("mhc_session=")]
        assert len(lines) == 1
        attrs = cookie_attributes(lines[0])
        assert attrs["path"] == "/" and "httponly" in attrs and attrs["samesite"] == "Lax"
        assert attrs["max-age"] == str(journey.container.limits.web.login_session_lifetime_s)
        assert "secure" not in attrs
        assert journey.db.count("staff_sessions") == 1
        row = journey.db.one("SELECT * FROM staff_sessions")
        assert row["session_id"] == signed.session_id and row["role"] == "customer"
        assert row["token_hash"] != signed.cookie and signed.cookie not in repr(row)
        shown = sorted(k for k in attrs if k != "mhc_session")
        print(
            f"step 3: {signed.response.status_code} cookie attrs {shown} role={row['role']} session={row['session_id']}"
        )


def test_j1_session_resume_and_owner_guard(journey: JourneyRun) -> None:
    signed = sign_in(journey)
    client = signed.client
    with journey.step(J1, "4 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):
        start = start_session(journey, client).json()
        thread_id = start["thread_id"]
        greeting = render(TextId.GREETING)
        assert start["greeting"]["type"] == "text" and start["greeting"]["text"] == greeting
        assert start["controller"] == {"kind": "ai", "display_name": None}
        assert start["settled"]["visit"] is None and start["settled"]["request"] is None
        assert start["settled"]["actions"] == []
        assert start["events"]["last_event_id"] == 0
        assert start["events"]["url"] == f"/api/chat/sessions/{thread_id}/events"
        conv = journey.db.one("SELECT * FROM conversations WHERE thread_id = ?", (thread_id,))
        assert conv["demo_session"] == signed.session_id and conv["run_tag"] == "live"
        assert conv["outcome"] == "open" and conv["agent_version"] == journey.settings.agent_version
        assert conv["controller"] == "ai" and conv["live_state"] == "not_live"
        assert conv["last_customer_wall_at"] is None
        messages = journey.db.rows("SELECT * FROM messages WHERE thread_id = ?", (thread_id,))
        assert len(messages) == 1 and messages[0]["role"] == "assistant" and messages[0]["text"] == greeting
        # A fresh store keeps no demo_state row; the demo clock reads DEMO_START (stage7/cases.md §6, DemoStateRepo.get)
        assert journey.db.rows("SELECT demo_now FROM demo_state WHERE id = 1") == []
        assert datetime.fromisoformat(start["demo_clock"]["now"]) == DEMO_START
        print(
            f"step 4: conversation {conv['outcome']} run_tag={conv['run_tag']}; greeting rows={len(messages)}"
        )

    with journey.step(J1, "6 refresh/resume read", needs=CHAT_NEEDS, operations=("getChatThread",)):
        before = thread_counts(journey, thread_id)
        read = client.call("GET", f"/api/chat/sessions/{thread_id}", operation_id="getChatThread")
        assert read.status_code == 200
        thread = read.json()
        assert thread["state"] == "open" and len(thread["turns"]) == 1
        entry = thread["turns"][0]
        assert entry["turn_id"] == "greeting" and entry["speaker"]["kind"] == "assistant"
        assert entry["blocks"][0]["text"] == greeting
        assert thread_counts(journey, thread_id) == before

    with journey.step(J1, "7 owner guard", needs=CHAT_NEEDS, operations=("login", "getChatThread")):
        before = thread_counts(journey, thread_id)
        other = journey.login()
        refused = other.client.call("GET", f"/api/chat/sessions/{thread_id}", operation_id="getChatThread")
        assert refused.status_code == 404 and error_of(refused)["code"] == "SESSION_NOT_FOUND"
        owner = client.call("GET", f"/api/chat/sessions/{thread_id}", operation_id="getChatThread")
        assert owner.status_code == 200
        assert thread_counts(journey, thread_id) == before
        print(
            f"step 7: other session {refused.status_code} {error_of(refused)['code']}; owner {owner.status_code}"
        )


def test_j1_one_turn_and_resend(journey: JourneyRun) -> None:
    signed = sign_in(journey)
    client = signed.client
    with journey.step(J1, "4 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):
        thread_id = start_session(journey, client).json()["thread_id"]
    turn_id = str(uuid.uuid4())
    first: httpx.Response
    with journey.step(J1, "5 one turn", needs=TURN_NEEDS, operations=("submitTurn",)):
        journey.script.add(Role.PLANNER, PLANNER_RAW)
        journey.script.add(Role.CLASSIFIER, CLASSIFIER_RAW)
        journey.script.add(Role.RESPONDER, json.dumps({"text": RESPONDER_TEXT}))
        calls_before = len(journey.script.calls)
        first = submit(client, thread_id, turn_id, CUSTOMER_TEXT)
        assert first.status_code == 200
        blocks = first.json()["blocks"]
        assert len(blocks) == 1 and blocks[0]["type"] == "text" and blocks[0]["text"] == RESPONDER_TEXT
        assert journey.script.problems() == ()
        assert journey.script.remaining() == 0
        assert {c.role for c in journey.script.calls[calls_before:]} == {
            Role.PLANNER,
            Role.CLASSIFIER,
            Role.RESPONDER,
        }
        customer = journey.db.one(
            "SELECT * FROM messages WHERE turn_id = ? AND role = 'customer'", (turn_id,)
        )
        assert customer["text"] == CUSTOMER_TEXT and customer["kind"] == "text"
        turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
        assert turn["status"] == "completed" and turn["gate_result"] == "clear"
        assert turn["plan_mode"] == "talk" and turn["outcome"] == "answered"
        assert json.loads(turn["specialists_run"]) == []
        assert isinstance(turn["server_ms"], int) and turn["server_ms"] >= 0
        assert turn["replied_at"] is not None and turn["trace_export"] == "off"
        assert turn["agent_version"] == journey.settings.agent_version
        assert turn["request_id"] == first.headers["X-Request-ID"]
        assert turn["model_calls"] == 3 and turn["cost_usd"] == 0.0
        spend = journey.db.rows("SELECT * FROM spend_ledger WHERE turn_id = ?", (turn_id,))
        assert len(spend) == 3
        configured = role_specs(journey.settings)
        for row in spend:
            provider, spec = configured[Role(row["role"])]
            assert row["cost_usd"] == 0.0 and row["status"] == "ok" and row["run_tag"] == "live"
            assert (row["provider"], row["model"]) == (provider, spec.model)
        conv = journey.db.one(
            "SELECT last_customer_wall_at FROM conversations WHERE thread_id = ?", (thread_id,)
        )
        assert conv["last_customer_wall_at"] is not None
        print(
            f"step 5: turn {turn['status']} outcome={turn['outcome']} ledger rows={len(spend)} cost={turn['cost_usd']}"
        )

    with journey.step(J1, "6 refresh/resume read", needs=TURN_NEEDS, operations=("getChatThread",)):
        before = thread_counts(journey, thread_id)
        thread = client.call("GET", f"/api/chat/sessions/{thread_id}", operation_id="getChatThread").json()
        entries = thread["turns"]
        assert len(entries) == 3
        assert entries[1]["speaker"]["kind"] == "customer" and entries[1]["turn_id"] == turn_id
        assert entries[1]["text"] == CUSTOMER_TEXT
        assert entries[2]["speaker"]["kind"] == "assistant" and entries[2]["blocks"] == first.json()["blocks"]
        assert thread_counts(journey, thread_id) == before

    with journey.step(J1, "6 resend", needs=TURN_NEEDS, operations=("submitTurn",)):
        before = thread_counts(journey, thread_id)
        calls = len(journey.script.calls)
        same = submit(client, thread_id, turn_id, CUSTOMER_TEXT)
        assert same.status_code == 200 and same.content == first.content
        assert len(journey.script.calls) == calls
        assert journey.db.count("turns", "turn_id = ?", (turn_id,)) == 1
        assert thread_counts(journey, thread_id) == before
        print(f"step 6 resend: identical body, adapter requests unchanged at {calls}")


def test_j1_rejected_and_secret_values_absent(journey: JourneyRun) -> None:
    signed = sign_in(journey)
    secrets_after_login = (*journey.secret_values(), signed.cookie)
    with journey.step(J1, "secret values absent after login", needs=LOGIN_NEEDS):
        for value in secrets_after_login:
            assert journey.files_containing(value) == []
            assert value not in journey.logs.all_text()
        print("secret hits after login: 0 per value")
    with journey.step(J1, "4 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):
        thread_id = start_session(journey, signed.client).json()["thread_id"]
    with journey.step(J1, "8 validation", needs=SUBMIT_NEEDS, operations=("submitTurn",)):
        before = thread_counts(journey, thread_id)
        text = SENTINEL + "a" * (2001 - len(SENTINEL))
        bad = submit(signed.client, thread_id, str(uuid.uuid4()), text)
        assert bad.status_code == 400 and error_of(bad)["code"] == "VALIDATION_ERROR"
        assert SENTINEL not in bad.text
        assert thread_counts(journey, thread_id) == before
    with journey.step(J1, "secret values absent after step 8", needs=LOGIN_NEEDS):
        rendered = render_record(
            build_record_data(scope="AEA-57", collector=journey.collector, root=REPO_ROOT, command="j1")
        )
        for value in (SENTINEL, *secrets_after_login):
            assert journey.files_containing(value) == []
            assert value not in journey.logs.all_text()
            assert value not in rendered
        print("secret hits after step 8: 0 per value")


def test_j1_records_per_step(journey: JourneyRun) -> None:
    with journey.step(J1, "1 signed out", needs=LOGIN_NEEDS):
        client = journey.client()
        api = client.call("GET", f"/api/chat/sessions/{uuid.uuid4()}", operation_id="getChatThread")
        page = client.call("GET", "/staff/queue", operation_id=None)
        for response in (api, page):
            record = request_record(journey, response)
            assert record["status"] == response.status_code and record["caller_role"] == "anonymous"
            print(f"step 1 request record: status={record['status']} route={record['route']}")
    with journey.step(J1, "2 wrong login", needs=LOGIN_NEEDS, operations=("login",)):
        wrong = journey.client().call(
            "POST",
            "/api/login",
            operation_id="login",
            body={"username": journey.demo_username, "password": "wrongpass" + letters(12)},
        )
        rid = wrong.headers["X-Request-ID"]
        auth = journey.logs.wait_for("auth_event", lambda r: r["request_id"] == rid)
        assert auth["outcome"] == "rejected" and auth["session_id"] is None
        request_record(journey, wrong)
        print(f"step 2 auth_event: {auth['outcome']}")
    signed = sign_in(journey)
    with journey.step(J1, "3 login records", needs=SIGN_IN_NEEDS):
        rid = signed.response.headers["X-Request-ID"]
        auth = journey.logs.wait_for("auth_event", lambda r: r["request_id"] == rid)
        assert auth["outcome"] == "ok" and auth["session_id"] == signed.session_id
        request_record(journey, signed.response)
        print(f"step 3 auth_event: {auth['outcome']} session_id={auth['session_id']}")
    with journey.step(J1, "4 start session records", needs=CHAT_NEEDS, operations=("startChatSession",)):
        started = start_session(journey, signed.client)
        record = request_record(journey, started)
        assert record["caller_role"] == "customer"
        thread_id = started.json()["thread_id"]
        assert journey.db.count("conversations", "thread_id = ?", (thread_id,)) == 1
        assert journey.db.count("messages", "thread_id = ?", (thread_id,)) == 1
        print(f"step 4 request record: status={record['status']} caller_role={record['caller_role']}")


def test_j1_offline_and_placeholders(journey: JourneyRun) -> None:
    assert journey.settings.anthropic_api_key.get_secret_value() == PLACEHOLDER_ANTHROPIC_KEY
    assert journey.settings.openrouter_api_key.get_secret_value() == PLACEHOLDER_OPENROUTER_KEY
    assert journey.settings.langfuse_complete() is False
    assert journey.settings.eval_key is None
    dist = journey.settings.web_dist_dir
    assert dist.is_dir() and list(dist.iterdir()) == []
    assert journey.guard.blocked == []
