"""AEA-46 capture: AC-17 (message text never logged) and AC-20 (WF-4 records and correlation keys)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import anyio
import pytest

from meridian.adapters.sqlite.rows import case_stream, thread_stream
from meridian.domain.staff import DemoRole
from tests.api.staff_live_support import (
    app_uow,
    asgi_call,
    close_stream,
    events_url,
    fast_stream,
    live_url,
    open_stream,
    read_frames,
    running,
    staff_live_app,
)
from tests.api.web_shell_support import FakeSessionStore, app_log_text, captured_log, rand_word, records_of
from tests.services.live_chat_support import (
    JOIN_AT,
    RILEY,
    SECOND_REF,
    STAFF_TEXT,
    WP2_REF,
    append_customer_reply,
    seed_live_case,
)


def test_message_text_never_logged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-17: staff and relayed customer text sit in rows and the response/frame, and in no log record."""
    fast_stream(monkeypatch)
    staff, reply = rand_word(18, "zqstaff"), rand_word(18, "zqreply")
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    app = staff_live_app(monkeypatch, tmp_path, store=store)
    caplog.set_level(logging.DEBUG)

    async def scenario() -> tuple[str, Any, Any]:
        async with running(app) as tg:
            seeded = seed_live_case(app_uow(app))
            with captured_log() as log:
                for body in ({"action": "join"}, {"action": "send", "text": staff}):
                    status, _, raw = await asgi_call(
                        app, "POST", live_url(str(WP2_REF)), token=token, json_body=body
                    )
                    assert status == 200
                assert json.loads(raw)["message"]["text"] == staff
                append_customer_reply(app_uow(app), seeded, reply, JOIN_AT)
                handle = await open_stream(tg, app, events_url(str(WP2_REF)), token=token)
                frames = await read_frames(handle, 2)  # controller_changed, customer_message
                assert reply in [json.loads(f.data).get("message", {}).get("text") for f in frames]
                await close_stream(handle)
                reconnect = await open_stream(
                    tg, app, events_url(str(WP2_REF)), token=token, last_event_id="1"
                )
                await read_frames(reconnect, 1)
                await close_stream(reconnect)
            with app_uow(app)(write=False) as tx:
                texts = [m.text for m in tx.core.messages.all_for_thread(seeded.thread_id)]
            return log.getvalue(), texts, records_of(log, "stream_reconnect")

    captured, texts, reconnects = anyio.run(scenario)
    assert staff in texts and reply in texts
    assert len(reconnects) == 1
    everything = "\n".join([captured, caplog.text, app_log_text(caplog)])
    assert staff not in everything and reply not in everything


def test_wf4_live_entry_points_emit_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-20: one request record per call, one case_event per live action, correlation keys on the streams."""
    fast_stream(monkeypatch)
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    app = staff_live_app(monkeypatch, tmp_path, store=store)

    async def scenario() -> Any:
        async with running(app) as tg:
            a = seed_live_case(app_uow(app))
            b = seed_live_case(app_uow(app), case_ref=SECOND_REF)
            calls = [
                (WP2_REF, {"action": "join"}),
                (WP2_REF, {"action": "send", "text": STAFF_TEXT}),
                (WP2_REF, {"action": "hand_back"}),
                (SECOND_REF, {"action": "join"}),
                (SECOND_REF, {"action": "close"}),
            ]
            request_ids: list[str] = []
            with captured_log() as log:
                for ref, body in calls:
                    status, headers, _ = await asgi_call(
                        app, "POST", live_url(str(ref)), token=token, json_body=body
                    )
                    assert status == 200
                    request_ids.append(headers["x-request-id"])
                handle = await open_stream(tg, app, events_url(str(WP2_REF)), token=token, last_event_id="1")
                await read_frames(handle, 1)
                request_ids.append(handle.headers["x-request-id"])
                await close_stream(handle)
                await anyio.sleep(0.1)
            uow = app_uow(app)
            with uow(write=False) as tx:
                events = {
                    "A": tx.cases.case_events.list_for_case(a.case_ref),
                    "B": tx.cases.case_events.list_for_case(b.case_ref),
                    "thread": tx.core.events.after(thread_stream(a.thread_id), 0),
                    "case": tx.core.events.after(case_stream(a.case_ref), 0),
                }
            return request_ids, records_of(log, "request"), events

    request_ids, requests, events = anyio.run(scenario)
    assert len(requests) == 6
    assert [r["request_id"] for r in requests] == request_ids
    assert (
        sorted(r["route"] for r in requests)
        == ["/api/staff/cases/{reference}/events"] + ["/api/staff/cases/{reference}/live"] * 5
    )
    assert {r["caller_role"] for r in requests} == {"representative"}
    for key, kinds in (
        ("A", ["live_join", "live_send", "live_hand_back"]),
        ("B", ["live_join", "live_close"]),
    ):
        rows = events[key]
        assert [r.kind for r in rows] == kinds
        assert {r.actor_role for r in rows} == {RILEY.role.value}
        assert [r.detail["action"] for r in rows] == [k.removeprefix("live_") for k in kinds]
    assert events["thread"] and events["case"]
    print("request records:", [(r["route"], r["status"]) for r in requests])
    print("case events:", {k: [r.kind for r in events[k]] for k in ("A", "B")})
    print("stream rows:", [e.type for e in events["thread"]], [e.type for e in events["case"]])
