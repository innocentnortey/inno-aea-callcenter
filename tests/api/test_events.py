"""AEA-41 CON-3 streamChatEvents: replay, live polling, heartbeat, closing, ownership, limits and read-only (AC-1..AC-13).

Every async scenario is a plain sync test that calls `anyio.run`; time is a test clock or a 10 ms poll, bounded by
`fail_after`. No socket, no paid call.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import anyio
import pytest
from fastapi import FastAPI

from meridian.adapters.sqlite.rows import StreamKey
from meridian.web.deps import STREAM_POLL_LIMITER
from meridian.web.routes.events import chat_event_frames
from meridian.web.schemas.events import HEARTBEAT_FRAME, RESERVED_KEYS
from tests.api.events_support import (
    STAFF_TEXT,
    TAKEOVER_TRIO,
    WP2_JOINED_AT,
    WP2_MESSAGE_AT,
    FakeMonotonic,
    FakeStreamStore,
    FlagGate,
    RecordingUowFactory,
    append_stored,
    close_stream,
    count_event_reads,
    events_app,
    frame_ids,
    next_item,
    open_stream,
    payload,
    read_frames,
    running,
    seed_conversation,
    session_of,
    table_counts,
)
from tests.api.openapi_check import SseFrame, assert_sse_frames_match, load_document
from tests.api.web_shell_support import (
    ConversationRowStub,
    EndedThreadStub,
    FakeSessionStore,
    app_log_text,
    assert_matches,
    captured_log,
    cookie_header,
    error_body,
    make_client,
    make_settings,
    new_thread_id,
    records_of,
    without_request_id,
)
from tests.fixtures.sqlite import temp_sqlite

EXAMPLE_PATH = "/api/chat/sessions/{thread_id}/events"


def _example_data_lines() -> dict[int, str]:
    text = load_document()["paths"][EXAMPLE_PATH]["get"]["responses"]["200"]["content"]["text/event-stream"][
        "examples"
    ]["FRAMES"]["value"]
    lines: dict[int, str] = {}
    for line in text.splitlines():
        if line.startswith("data: "):
            lines[json.loads(line[6:])["event_id"]] = line[6:]
    return lines


class Setup:
    """One customer login, one owned thread and an in-memory store."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **app_kw: Any) -> None:
        self.sessions = FakeSessionStore()
        self.token = self.sessions.issue()
        self.tid = new_thread_id()
        self.store = FakeStreamStore(
            {self.tid: ConversationRowStub(self.tid, session_of(self.sessions, self.token))}
        )
        self.settings = make_settings(tmp_path)
        self.app: FastAPI = events_app(
            monkeypatch, self.settings, uow=self.store, store=self.sessions, **app_kw
        )

    def add_thread(self) -> str:
        tid = new_thread_id()
        self.store.rows[tid] = ConversationRowStub(tid, session_of(self.sessions, self.token))
        return tid


def _trio(store: FakeStreamStore, tid: str, first_id: int = 12) -> None:
    for offset, kind in enumerate(TAKEOVER_TRIO):
        at = WP2_MESSAGE_AT if kind == "staff_message" else WP2_JOINED_AT
        store.append(tid, kind, payload(kind), at=at, event_id=first_id + offset)


def test_replay_after_last_event_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): Last-Event-ID 12 receives 13 then 14 and one stream_reconnect record."""
    s = Setup(monkeypatch, tmp_path)
    _trio(s.store, s.tid)
    holder: dict[str, Any] = {}

    async def scenario() -> None:
        async with running(s.app) as tg:
            h = await open_stream(tg, s.app, s.tid, token=s.token, last_event_id="12")
            holder["frames"] = await read_frames(h, 2)
            holder["request_id"] = h.headers["x-request-id"]
            await close_stream(h)

    with captured_log() as log:
        anyio.run(scenario)
    frames: list[SseFrame] = holder["frames"]
    assert frame_ids(frames) == [13, 14]
    assert_sse_frames_match(frames, "streamChatEvents")
    example = _example_data_lines()
    assert [f.data for f in frames] == [example[13], example[14]]
    assert s.store.reads[0].stream == s.tid and s.store.reads[0].last == 12
    assert records_of(log, "stream_reconnect") == [
        {
            "record": "stream_reconnect",
            "request_id": holder["request_id"],
            "thread_id": s.tid,
            "last_event_id": 12,
            "replayed": 2,
        }
    ]


def test_first_connect_replays_from_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-2): no header starts at 0; headers are the documented ones; no reconnect record."""
    s = Setup(monkeypatch, tmp_path)
    s.store.append(s.tid, "representative_joined", payload("representative_joined"))
    s.store.append(s.tid, "ai_paused", payload("ai_paused"))
    holder: dict[str, Any] = {}

    async def scenario() -> None:
        async with running(s.app) as tg:
            h = await open_stream(tg, s.app, s.tid, token=s.token)
            holder["frames"] = await read_frames(h, 2)
            holder["status"] = h.status
            holder["headers"] = h.headers
            await close_stream(h)

    with captured_log() as log:
        anyio.run(scenario)
    assert frame_ids(holder["frames"]) == [1, 2]
    assert holder["status"] == 200
    assert holder["headers"]["content-type"].split(";")[0] == "text/event-stream"
    assert holder["headers"]["cache-control"] == "no-store"
    assert uuid.UUID(holder["headers"]["x-request-id"]).version == 4
    assert records_of(log, "stream_reconnect") == []


def test_live_event_delivered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-3): an event appended while the stream is open arrives within two polls (real SQLite)."""
    sessions = FakeSessionStore()
    token = sessions.issue()
    holder: dict[str, Any] = {}
    with temp_sqlite() as store:
        tid = seed_conversation(store.uow, session_of(sessions, token))
        reads = count_event_reads(monkeypatch)
        app = events_app(monkeypatch, make_settings(tmp_path), uow=store.uow, store=sessions)

        async def scenario() -> None:
            async with running(app) as tg:
                h = await open_stream(tg, app, tid, token=token)
                with anyio.fail_after(3):
                    while len(reads) < 1:
                        await anyio.sleep(0.005)
                n0 = len(reads)
                [eid] = append_stored(store.uow, tid, [("staff_message", payload("staff_message"))])
                [frame] = await read_frames(h, 1)
                holder.update(eid=eid, frame=frame, extra=len(reads) - n0)
                await close_stream(h)

        anyio.run(scenario)
    assert holder["frame"].id == str(holder["eid"])
    assert holder["extra"] <= 2


def _drive_heartbeat(
    read_rows: dict[float, list[Any]], clock: FakeMonotonic, want: int
) -> tuple[list[Any], int]:
    reads: list[int] = []
    chunks: list[tuple[float, bytes]] = []

    async def read_after(last: int) -> list[Any]:
        reads.append(last)
        return read_rows.get(clock.now, [])

    async def disconnected() -> bool:
        return False

    async def scenario() -> None:
        gen = chat_event_frames(
            start=0,
            read_after=read_after,
            reset_held=lambda: False,
            disconnected=disconnected,
            timing=clock.timing(),
            on_replayed=None,
        )
        try:
            async for chunk in gen:
                chunks.append((clock.now, chunk))
                if len(chunks) == want:
                    break
        finally:
            await gen.aclose()

    anyio.run(scenario)
    return chunks, len(reads)


def test_heartbeat_every_15s() -> None:
    """invariant (AC-4): a heartbeat comment at 15 s and 30 s of silence, on a test clock."""
    chunks, reads = _drive_heartbeat({}, FakeMonotonic(), 2)
    assert chunks == [(15.0, HEARTBEAT_FRAME), (30.0, HEARTBEAT_FRAME)]
    assert reads == 31


def test_heartbeat_restarts_after_a_frame() -> None:
    """invariant (PA-2): the 15 s silence timer restarts when a frame is sent."""
    from meridian.adapters.sqlite.rows import EventRow

    clock = FakeMonotonic()
    row = EventRow(id=1, stream="s", type="ai_paused", payload=payload("ai_paused"), at=WP2_JOINED_AT)
    chunks, _ = _drive_heartbeat({10.0: [row]}, clock, 2)
    assert [(t, c == HEARTBEAT_FRAME) for t, c in chunks] == [(10.0, False), (25.0, True)]


@pytest.mark.parametrize("closer", ["chat_closed", "demo_reset"])
def test_stream_closes_after_chat_closed_and_demo_reset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, closer: str
) -> None:
    """invariant (AC-5): the closing event is delivered, later events are not, and the response ends."""
    s = Setup(monkeypatch, tmp_path)
    s.store.append(s.tid, "representative_joined", payload("representative_joined"))
    s.store.append(s.tid, closer, payload(closer))
    s.store.append(s.tid, "staff_message", payload("staff_message"))
    holder: dict[str, Any] = {"frames": []}

    async def scenario() -> None:
        async with running(s.app) as tg:
            h = await open_stream(tg, s.app, s.tid, token=s.token)
            while (item := await next_item(h)) is not None:
                if isinstance(item, SseFrame):
                    holder["frames"].append(item)
            with anyio.fail_after(2):
                await h.done.wait()
            holder["done"] = h.done.is_set()

    anyio.run(scenario)
    assert [f.event for f in holder["frames"]] == ["representative_joined", closer]
    assert "3" not in [f.id for f in holder["frames"]]
    assert holder["done"]


def test_auth_and_ownership(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-6): 401 without a session; malformed, unknown and foreign threads give one identical 404."""
    s = Setup(monkeypatch, tmp_path)
    other = new_thread_id()
    s.store.rows[other] = ConversationRowStub(other, "another-session-id")
    for tid in (s.tid, other):
        s.store.append(tid, "ai_paused", payload("ai_paused"))
    with make_client(s.app) as client:
        r = client.get(f"/api/chat/sessions/{s.tid}/events")
        error_body(r, 401, "UNAUTHENTICATED")
        assert_matches(r, "streamChatEvents")
        bodies = []
        for path_id in ("thr_9d41", new_thread_id(), other):
            r = client.get(f"/api/chat/sessions/{path_id}/events", headers=cookie_header(s.token))
            error_body(r, 404, "SESSION_NOT_FOUND")
            assert_matches(r, "streamChatEvents")
            bodies.append(without_request_id(r))
    assert bodies[0] == bodies[1] == bodies[2]
    assert s.store.reads == []


def test_ended_thread_answers_documented_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-7): this session's ended thread answers the same 404 as an unknown thread."""
    s = Setup(monkeypatch, tmp_path)
    ended = new_thread_id()
    s.store.rows[ended] = EndedThreadStub(
        ended, session_of(s.sessions, s.token), "2026-10-16T15:00:00+00:00", "demo_reset"
    )
    with make_client(s.app) as client:
        r = client.get(f"/api/chat/sessions/{ended}/events", headers=cookie_header(s.token))
        error_body(r, 404, "SESSION_NOT_FOUND")
        assert_matches(r, "streamChatEvents")
        unknown = client.get(f"/api/chat/sessions/{new_thread_id()}/events", headers=cookie_header(s.token))
    assert without_request_id(r) == without_request_id(unknown)
    assert s.store.reads == []


def test_poll_reads_off_loop_limited_to_4(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-8): six streams, at most 4 reads at once, none on the loop thread, under the provider's limiter."""
    s = Setup(monkeypatch, tmp_path)
    tids = [s.tid] + [s.add_thread() for _ in range(5)]
    for tid in tids:
        s.store.append(tid, "ai_paused", payload("ai_paused"))
    s.store.hold_reads = threading.Event()
    holder: dict[str, Any] = {}

    async def scenario() -> None:
        loop_thread = threading.get_ident()
        async with running(s.app) as tg:
            lim = s.app.state.container.get(STREAM_POLL_LIMITER)
            handles = [await open_stream(tg, s.app, tid, token=s.token) for tid in tids]
            with anyio.fail_after(3):
                while s.store.active_reads < 4:
                    await anyio.sleep(0.005)
            await anyio.sleep(0.1)
            holder["active"] = s.store.active_reads
            holder["borrowed"] = lim.borrowed_tokens
            assert s.store.hold_reads is not None
            s.store.hold_reads.set()
            for h in handles:
                await read_frames(h, 1)
            for h in handles:
                await close_stream(h)
            holder.update(loop_thread=loop_thread, lim=lim)

    anyio.run(scenario)
    assert holder["active"] == 4 and holder["borrowed"] == 4
    assert s.store.max_active_reads == 4
    assert all(r.thread != holder["loop_thread"] for r in s.store.reads)
    assert holder["lim"].borrowed_tokens == 0 and holder["lim"].total_tokens == 4


def test_reset_gate_skips_polls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-9): while the gate is held the stream opens at once and reads nothing; then it delivers and closes."""
    gate = FlagGate()
    gate.flag = True
    s = Setup(monkeypatch, tmp_path, gate=gate)
    holder: dict[str, Any] = {}

    async def scenario() -> None:
        async with running(s.app) as tg:
            h = await open_stream(tg, s.app, s.tid, token=s.token)
            holder["status"] = h.status
            await anyio.sleep(0.1)
            holder["reads_while_held"] = list(s.store.reads)
            s.store.append(s.tid, "demo_reset", payload("demo_reset"))
            gate.flag = False
            [frame] = await read_frames(h, 1)
            holder["type"] = frame.event
            holder["end"] = await next_item(h)
            with anyio.fail_after(2):
                await h.done.wait()

    anyio.run(scenario)
    assert holder["status"] == 200
    assert holder["reads_while_held"] == []
    assert holder["type"] == "demo_reset" and holder["end"] is None


@pytest.mark.parametrize("spec_version", ["2.3", "2.4"])
def test_disconnect_stops_polling(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, spec_version: str) -> None:
    """invariant (AC-10): a disconnect ends the poll loop within one interval and frees the limiter slot."""
    s = Setup(monkeypatch, tmp_path)
    holder: dict[str, Any] = {}

    async def scenario() -> None:
        async with running(s.app) as tg:
            lim = s.app.state.container.get(STREAM_POLL_LIMITER)
            before = lim.borrowed_tokens
            h = await open_stream(tg, s.app, s.tid, token=s.token, spec_version=spec_version)
            with anyio.fail_after(3):
                while len(s.store.reads) < 2:
                    await anyio.sleep(0.005)
            n = len(s.store.reads)
            await close_stream(h, timeout=1.0)
            await anyio.sleep(0.05)
            holder.update(
                extra=len(s.store.reads) - n,
                borrowed=lim.borrowed_tokens,
                before=before,
                done=h.done.is_set(),
            )

    anyio.run(scenario)
    assert holder["extra"] <= 1
    assert holder["borrowed"] == holder["before"]
    assert holder["done"]


def test_only_chat_event_types_sent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """negative (AC-11): a stored case_changed row is never sent; later frames still arrive in order."""
    s = Setup(monkeypatch, tmp_path)
    s.store.append(s.tid, "representative_joined", payload("representative_joined"))
    s.store.append(s.tid, "case_changed", payload("case_changed"))
    s.store.append(s.tid, "ai_paused", payload("ai_paused"))
    holder: dict[str, Any] = {}

    async def scenario() -> None:
        async with running(s.app) as tg:
            h = await open_stream(tg, s.app, s.tid, token=s.token)
            holder["frames"] = await read_frames(h, 2)
            await anyio.sleep(0.05)
            await close_stream(h)

    anyio.run(scenario)
    assert frame_ids(holder["frames"]) == [1, 3]
    assert all(r.last >= 3 for r in s.store.reads[1:])


def test_frames_equal_stored_and_logs_hold_no_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-12): frames carry the stored payload; the staff sentence is in no log record."""
    caplog.set_level(logging.INFO)
    sessions = FakeSessionStore()
    token = sessions.issue()
    holder: dict[str, Any] = {}
    with temp_sqlite() as store:
        tid = seed_conversation(store.uow, session_of(sessions, token))
        ids = append_stored(store.uow, tid, [(k, payload(k)) for k in TAKEOVER_TRIO])
        app = events_app(monkeypatch, make_settings(tmp_path), uow=store.uow, store=sessions)

        async def scenario() -> None:
            async with running(app) as tg:
                h = await open_stream(tg, app, tid, token=token, last_event_id=str(ids[0]))
                holder["frames"] = await read_frames(h, 2)
                await close_stream(h)

        with captured_log() as log:
            anyio.run(scenario)
        with store.uow() as tx:
            stored = {r.id: r for r in tx.core.events.after(StreamKey(tid), 0)}
    frames: list[SseFrame] = holder["frames"]
    assert any(STAFF_TEXT in f.data for f in frames)
    for frame in frames:
        data = json.loads(frame.data)
        row = stored[data["event_id"]]
        assert {k: v for k, v in data.items() if k not in RESERVED_KEYS} == row.payload
        assert datetime.fromisoformat(data["at"]) == row.at
    assert STAFF_TEXT not in app_log_text(caplog)
    assert not any(STAFF_TEXT in repr(r.__dict__) for r in caplog.records if r.name.startswith("meridian"))
    assert STAFF_TEXT not in log.getvalue()


def test_stream_is_read_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """negative (AC-13): only read units of work; no table changes beyond the test's own append."""
    sessions = FakeSessionStore()
    token = sessions.issue()
    with temp_sqlite() as store:
        tid = seed_conversation(store.uow, session_of(sessions, token))
        append_stored(
            store.uow,
            tid,
            [
                ("representative_joined", payload("representative_joined")),
                ("ai_paused", payload("ai_paused")),
            ],
        )
        before = table_counts(store.db_path)
        recording = RecordingUowFactory(store.uow)
        app = events_app(monkeypatch, make_settings(tmp_path), uow=recording, store=sessions)

        async def scenario() -> None:
            async with running(app) as tg:
                h = await open_stream(tg, app, tid, token=token)
                await read_frames(h, 2)
                await close_stream(h)
                h = await open_stream(tg, app, tid, token=token)
                append_stored(store.uow, tid, [("ai_resumed", payload("ai_resumed"))])
                await read_frames(h, 3)
                await close_stream(h)
                h = await open_stream(tg, app, tid, token=token, last_event_id="2")
                await read_frames(h, 1)
                await close_stream(h)

        anyio.run(scenario)
        after = table_counts(store.db_path)
    assert recording.write_flags and not any(recording.write_flags)
    assert after == {**before, "events": before["events"] + 1}


@pytest.mark.parametrize("raw", ["abc", "-3", "12abc"])
def test_malformed_last_event_id_starts_at_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, raw: str
) -> None:
    """negative (PA-1): a malformed Last-Event-ID starts at 0 and writes no stream_reconnect record."""
    s = Setup(monkeypatch, tmp_path)
    s.store.append(s.tid, "representative_joined", payload("representative_joined"))
    s.store.append(s.tid, "ai_paused", payload("ai_paused"))
    holder: dict[str, Any] = {}

    async def scenario() -> None:
        async with running(s.app) as tg:
            h = await open_stream(tg, s.app, s.tid, token=s.token, last_event_id=raw)
            holder["frames"] = await read_frames(h, 2)
            await close_stream(h)

    with captured_log() as log:
        anyio.run(scenario)
    assert frame_ids(holder["frames"]) == [1, 2]
    assert records_of(log, "stream_reconnect") == []
