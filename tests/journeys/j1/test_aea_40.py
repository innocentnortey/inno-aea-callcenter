"""J-1 (slice plan section 0a), AEA-40's part: login, start a chat, send one turn, reload and resume the same thread.

Level today: the mock test runs (`mock-tested`: real routes, real middleware, a real SQLite working copy through a
TestClient; the graph, the demo service and the settled-view builder are doubles). The integrated test (real server)
is blocked by AEA-30 (demo clock, DemoService) and AEA-51 (reply composer, graph); the harness reports it as
blocked. Asserts what the user sees and the stored rows.
"""

from __future__ import annotations

import json
import random
import uuid
from pathlib import Path

import pytest

from meridian.policy.texts import TextId, render
from tests.api.chat_support import chat_env, get_thread, post_turn, start_session
from tests.api.web_shell_support import (
    assert_matches,
    error_body,
    login,
    make_client,
    session_cookie_value,
)
from tests.journeys.support.run import JourneyRun
from tests.services.chat_doubles import new_turn_id
from tests.services.chat_storage import count_rows, customer_messages, messages_of, turn_row

pytestmark = pytest.mark.journey

TURN_NEEDS = (
    "login_sessions",
    "session_service",
    "demo_service",
    "demo_clock",
    "reply_composer",
    "turn_service",
    "run_graph",
)

QUESTION = "I got an invoice and I am not sure what it is for."


def test_j1_login_start_one_turn_reload_resumes_the_same_thread(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """invariant: a reload resumes the thread through getChatThread: greeting first, then the turn and its reply."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        before_login = client.post("/api/chat/sessions")
        error_body(before_login, 401, "UNAUTHENTICATED")  # the login gate is on

        signed_in = login(client, env.settings)
        token = session_cookie_value(signed_in)
        assert signed_in.status_code == 200 and token
        started = start_session(client, token)
        assert started.status_code == 201
        assert_matches(started, "startChatSession")
        thread = started.json()["thread_id"]
        assert started.json()["greeting"]["text"] == render(TextId.GREETING)

        turn_id = new_turn_id()
        sent = post_turn(client, token, thread, {"kind": "text", "text": QUESTION}, turn_id)
        assert sent.status_code == 200
        assert_matches(sent, "submitTurn")
        reply_text = sent.json()["blocks"][0]["text"]

        reloaded = get_thread(client, token, thread)  # the page reload: no second startChatSession

        assert reloaded.status_code == 200
        assert_matches(reloaded, "getChatThread")
        turns = reloaded.json()["turns"]
        assert [(t["speaker"]["kind"], t["turn_id"]) for t in turns] == [
            ("assistant", "greeting"),
            ("customer", str(turn_id)),
            ("assistant", str(turn_id)),
        ]
        assert turns[0]["blocks"][0]["text"] == render(TextId.GREETING)
        assert turns[1]["text"] == QUESTION
        assert turns[2]["blocks"][0]["text"] == reply_text
        assert reloaded.json()["state"] == "open"
        assert count_rows(env.store, "conversations") == 1  # one thread, one start
        assert [(m.role, m.turn_id) for m in messages_of(env.store, thread)] == [
            ("assistant", None),
            ("customer", turn_id),
            ("assistant", turn_id),
        ]
        assert [m.text for m in customer_messages(env.store, thread)] == [QUESTION]
        assert turn_row(env.store, turn_id).status == "completed"
        # another browser (no cookie) cannot read it
        client.cookies.clear()
        assert client.get(f"/api/chat/sessions/{thread}").status_code == 401


def test_j1_code_turn_and_reload_through_the_real_server(journey: JourneyRun) -> None:
    """integrated (AC-15, AC-19, AC-8): a code turn reads "Code entered" after a reload; the digits are stored nowhere."""
    with journey.step(
        "J-1",
        "AEA-40 code turn and reload",
        needs=TURN_NEEDS,
        operations=("login", "startChatSession", "submitTurn", "getChatThread"),
    ):
        signed = journey.login()
        start = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        assert start.status_code == 201
        thread_id = start.json()["thread_id"]
        code = "".join(str(d) for d in random.Random(4041).choices(range(10), k=6))
        turn_id = str(uuid.uuid4())
        sent = signed.client.call(
            "POST",
            f"/api/chat/sessions/{thread_id}/turns",
            operation_id="submitTurn",
            body={"turn_id": turn_id, "payload": {"kind": "code", "card_id": "code-card-1", "code": code}},
        )
        assert sent.status_code == 200
        reloaded = signed.client.call("GET", f"/api/chat/sessions/{thread_id}", operation_id="getChatThread")
        turns = reloaded.json()["turns"]
        assert turns[0]["turn_id"] == "greeting"
        assert (turns[1]["speaker"]["kind"], turns[1]["turn_id"], turns[1]["text"]) == (
            "customer",
            turn_id,
            render(TextId.HISTORY_CODE_ENTERED),
        )
        row = journey.db.one("SELECT text FROM messages WHERE turn_id = ? AND role = 'customer'", (turn_id,))
        assert row["text"] == "[code entered]"
        assert journey.db.count("conversations", "demo_session = ?", (signed.session_id,)) == 1
        for table in ("messages", "turns", "conversations", "check_events", "events"):
            assert code not in json.dumps(journey.db.rows(f"SELECT * FROM {table}"), default=str)  # noqa: S608
        assert code not in journey.logs.all_text()
