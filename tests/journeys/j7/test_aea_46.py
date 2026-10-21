"""J-7 (slice plan section 0a), AEA-46 leg: a representative joins, writes in, hands back and closes; the customer's
thread shows each line; the case version never moves; the staff stream carries controller_changed and no case_changed.

Level today: mock-tested. Real: the app factory, the middleware, the routes, LiveChatService and the SQLite working
copy. Doubled: FakeSessionStore (AEA-44), the demo clock (AEA-30), and the customer reply, written the way AEA-40 will.
Blocked by AEA-57 (journey harness, scripted model) and AEA-52 (integration).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anyio
import pytest
from starlette.datastructures import Headers

from meridian.adapters.sqlite.rows import case_stream, thread_stream
from meridian.domain.staff import DemoRole
from tests.api.openapi_check import assert_response_matches, assert_sse_frames_match
from tests.api.staff_live_support import (
    app_uow,
    asgi_call,
    close_stream,
    events_url,
    fast_stream,
    live_url,
    open_stream,
    read_until_heartbeat,
    running,
    staff_live_app,
)
from tests.api.web_shell_support import FakeSessionStore
from tests.services.live_chat_support import (
    CUSTOMER_REPLY,
    JOIN_AT,
    SECOND_REF,
    STAFF_TEXT,
    WP2_REF,
    append_customer_reply,
    seed_live_case,
)

pytestmark = pytest.mark.journey


@dataclass
class _Resp:
    """What assert_response_matches needs from a response."""

    status_code: int
    headers: Headers
    content: bytes

    def json(self) -> Any:
        return json.loads(self.content)


def test_j7_live_takeover_mock_level(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fast_stream(monkeypatch)
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    app = staff_live_app(monkeypatch, tmp_path, store=store)

    async def post(ref: Any, body: dict[str, Any]) -> Any:
        status, headers, content = await asgi_call(
            app, "POST", live_url(str(ref)), token=token, json_body=body
        )
        response = _Resp(status, Headers(headers), content)
        assert status == 200, content
        assert_response_matches(response, "liveChatAction")
        return response.json()

    async def scenario() -> None:
        async with running(app) as tg:
            uow = app_uow(app)
            a = seed_live_case(uow, version=2)
            b = seed_live_case(uow, case_ref=SECOND_REF, version=2)
            assert (await post(WP2_REF, {"action": "join"}))["live"]["state"] == "joined"
            sent = await post(WP2_REF, {"action": "send", "text": STAFF_TEXT})
            assert sent["message"]["text"] == STAFF_TEXT
            append_customer_reply(uow, a, CUSTOMER_REPLY, JOIN_AT)
            assert (await post(WP2_REF, {"action": "hand_back"}))["live"]["state"] == "handed_back"
            await post(SECOND_REF, {"action": "join"})
            assert (await post(SECOND_REF, {"action": "close"}))["live"]["state"] == "closed"

            # what the customer sees: the thread rows and the thread-stream events CON-3 will send
            with uow(write=False) as tx:
                messages = tx.core.messages.all_for_thread(a.thread_id)
                thread_a = tx.core.events.after(thread_stream(a.thread_id), 0)
                thread_b = tx.core.events.after(thread_stream(b.thread_id), 0)
                case_a, case_b = tx.cases.cases.get(WP2_REF), tx.cases.cases.get(SECOND_REF)
            assert [(m.role, m.text) for m in messages[-2:]] == [
                ("representative", STAFF_TEXT),
                ("customer", CUSTOMER_REPLY),
            ]
            assert [e.type for e in thread_a] == [
                "representative_joined",
                "ai_paused",
                "staff_message",
                "ai_resumed",
            ]
            assert "Riley" in str(thread_a[0].payload["line"])
            assert [e.type for e in thread_b][-1] == "chat_closed"
            assert thread_b[-1].payload["composer_disabled"] is True

            # what is stored: versions and lifecycles never moved
            assert case_a is not None and case_b is not None
            assert (case_a.version, case_a.lifecycle, case_b.version, case_b.lifecycle) == (
                2,
                "claimed",
                2,
                "claimed",
            )

            # what staff see on CON-21
            handle = await open_stream(tg, app, events_url(str(WP2_REF)), token=token)
            frames = await read_until_heartbeat(handle)
            await close_stream(handle)
            types = [f.event for f in frames]
            print("CON-21 frames:", types)
            assert types == ["controller_changed", "customer_message", "controller_changed"]
            assert "case_changed" not in types
            assert_sse_frames_match(frames, "streamCaseEvents")
            with uow(write=False) as tx:
                assert [e.type for e in tx.core.events.after(case_stream(SECOND_REF), 0)] == [
                    "controller_changed",
                    "chat_closed",
                ]

    anyio.run(scenario)


@pytest.mark.skip(
    reason="blocked: integrated J-7 needs AEA-57's harness (scripted model) and AEA-52's wiring; record level mock-tested"
)
def test_j7_live_takeover_integrated() -> None:
    """Integrated steps, once AEA-57 and AEA-52 land:

    1. real login, switchRole to representative, claim (CON-13);
    2. the customer opens the chat and asks for a person (CON-4);
    3. join, send, the customer's turn relayed with AI_PAUSED, hand back, close;
    4. the browser sees each line.
    """
