"""AEA-46 CON-21 streamCaseEvents: AC-13 to AC-16 and PA-5 (in-process ASGI, no socket)."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import anyio
import pytest
from fastapi import FastAPI

from meridian.adapters.sqlite.rows import StreamEvent, case_stream
from meridian.domain.common import CaseRef
from meridian.domain.staff import DemoRole
from meridian.services.live_chat import LiveView
from meridian.web.deps import get_reset_gate, get_stream_poll_limiter, provided
from meridian.web.routes import staff_live
from tests.api.openapi_check import assert_sse_frames_match
from tests.api.staff_live_support import (
    RecordingLiveChat,
    app_uow,
    asgi_call,
    close_stream,
    events_url,
    fast_stream,
    frame_ids,
    live_url,
    next_item,
    open_stream,
    read_frames,
    read_until_heartbeat,
    running,
    staff_live_app,
)
from tests.api.web_shell_support import (
    FakeSessionStore,
    assert_matches,
    captured_log,
    make_client,
    records_of,
)
from tests.services.live_chat_support import EVENT_SPEAKER, JOIN_AT, UNKNOWN_REF, WP2_REF, seed_live_case

URL = events_url(str(WP2_REF))
RESET_LINE = "The demo was reset, so this chat has ended. Nothing from it was kept."


def _append(app: FastAPI, ref: CaseRef, kind: str, payload: dict[str, Any]) -> int:
    with app_uow(app)(write=True) as tx:
        new_id = tx.core.events.append(case_stream(ref), StreamEvent(type=kind, payload=payload, at=JOIN_AT))
        tx.commit()
    return int(new_id)


def _changed(i: int) -> dict[str, Any]:
    return {"version": i, "lifecycle": "claimed"}


def test_case_stream_replay_live_and_heartbeat(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-13: replay after Last-Event-ID, one stream_reconnect record, live append, heartbeat, 404 before any frame."""
    fast_stream(monkeypatch)
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    app = staff_live_app(monkeypatch, tmp_path, store=store)

    async def scenario() -> tuple[str, list[dict[str, Any]]]:
        async with running(app) as tg:
            seed_live_case(app_uow(app))
            for i in range(1, 33):
                _append(app, WP2_REF, "case_changed", _changed(i))
            with captured_log() as log:
                handle = await open_stream(tg, app, URL, token=token, last_event_id="30")
                assert handle.headers["content-type"].startswith("text/event-stream")
                frames = await read_frames(handle, 2)
                assert frame_ids(frames) == [31, 32]
                assert_sse_frames_match(frames, "streamCaseEvents")
                new_id = _append(
                    app,
                    WP2_REF,
                    "controller_changed",
                    {"controller": {"kind": "ai", "display_name": None}, "line": "x"},
                )
                more = await read_frames(handle, 1)
                assert frame_ids(more) == [new_id] == [33]
                assert_sse_frames_match(more, "streamCaseEvents")
                seen: list[Any] = []
                while "heartbeat" not in seen:
                    seen.append(await next_item(handle))
                request_id = handle.headers["x-request-id"]
                await close_stream(handle)
            return request_id, records_of(log, "stream_reconnect")

    request_id, records = anyio.run(scenario)
    assert records == [
        {
            "record": "stream_reconnect",
            "request_id": request_id,
            "case_ref": "MHC-C-0007",
            "last_event_id": 30,
            "replayed": 2,
        }
    ]
    with make_client(app) as client:
        missing = client.get(events_url(str(UNKNOWN_REF)), headers={"cookie": f"mhc_session={token}"})
        assert missing.status_code == 404
        assert_matches(missing, "streamCaseEvents")
        assert not missing.headers["content-type"].startswith("text/event-stream")


def test_case_stream_start_after_reset_and_close_rules(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-14: no header starts at the newest demo_reset; demo_reset closes the stream; chat_closed does not."""
    fast_stream(monkeypatch)
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    app = staff_live_app(monkeypatch, tmp_path, store=store)
    ref = CaseRef("MHC-C-0005")
    url = events_url(str(ref))

    async def scenario() -> None:
        async with running(app) as tg:
            uow = app_uow(app)
            seed_live_case(uow, case_ref=ref)
            _append(
                app,
                ref,
                "controller_changed",
                {"controller": {"kind": "human", "display_name": "Riley"}, "line": "x"},
            )
            with uow(write=True) as tx:
                tx.core.reset.clear_demo_tables("reset-test", ended_at=datetime.now(UTC))
                reset_id = int(
                    tx.core.events.append(
                        case_stream(ref),
                        StreamEvent(
                            type="demo_reset",
                            payload={"speaker": EVENT_SPEAKER, "line": RESET_LINE},
                            at=JOIN_AT,
                        ),
                    )
                )
                tx.commit()
            seed_live_case(uow, case_ref=ref)
            # (a) no header: nothing from before the reset, and the stream stays open
            a = await open_stream(tg, app, url, token=token)
            assert await read_until_heartbeat(a) == []
            _append(app, ref, "case_changed", _changed(2))
            assert len(await read_frames(a, 1)) == 1
            # (c) chat_closed does not close it
            _append(app, ref, "chat_closed", {"reason": "closed_by_staff"})
            _append(app, ref, "case_changed", _changed(3))
            assert [f.event for f in await read_frames(a, 2)] == ["chat_closed", "case_changed"]
            await close_stream(a)
            # (b) a header below the reset id receives it, then the body ends
            b = await open_stream(tg, app, url, token=token, last_event_id=str(reset_id - 1))
            frames = await read_frames(b, 1)
            assert frame_ids(frames) == [reset_id] and frames[0].event == "demo_reset"
            assert await next_item(b) is None
            await close_stream(b)

    anyio.run(scenario)


class BlockingReads:
    """Replaces read_case_events: holds each worker thread until released, counting active reads."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.release = threading.Event()
        self.starts: list[float] = []
        self.active = 0
        self.max_active = 0
        self.done = 0

    def __call__(self, uow: Any, stream: Any, last: int | None) -> tuple[int, list[Any]]:
        with self.lock:
            self.starts.append(time.monotonic())
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        self.release.wait(5)
        with self.lock:
            self.active -= 1
            self.done += 1
        return (last or 0, [])


def test_streams_share_limiter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-15: one limiter of four; a fifth poll waits; a def route still answers with five streams open."""
    fast_stream(monkeypatch)
    blocking = BlockingReads()
    monkeypatch.setattr(staff_live, "read_case_events", blocking)
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    double = RecordingLiveChat(
        LiveView(controller_kind="human", controller_name="Riley", state="joined", since=JOIN_AT)
    )
    app = staff_live_app(monkeypatch, tmp_path, store=store, live_chat=double)

    async def scenario() -> None:
        try:
            async with running(app) as tg:
                seed_live_case(app_uow(app))
                handles = [await open_stream(tg, app, URL, token=token) for _ in range(5)]
                with anyio.fail_after(2):
                    while blocking.active < 4:
                        await anyio.sleep(0.01)
                await anyio.sleep(0.2)
                assert (blocking.active, blocking.max_active, blocking.done) == (4, 4, 0)
                assert provided(app, get_stream_poll_limiter).borrowed_tokens == 4
                with anyio.fail_after(3):
                    status, _, _ = await asgi_call(
                        app, "POST", live_url(str(WP2_REF)), token=token, json_body={"action": "join"}
                    )
                assert status == 200
                release_at = time.monotonic()
                blocking.release.set()
                with anyio.fail_after(3):
                    while blocking.done < 5:
                        await anyio.sleep(0.01)
                assert sorted(blocking.starts)[4] >= release_at
                for handle in handles:
                    await close_stream(handle)
        finally:
            blocking.release.set()

    anyio.run(scenario)


def test_reset_gate_behaviour(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-16: a held reset skips reads and never answers 503; liveChatAction waits then runs."""
    fast_stream(monkeypatch)
    reads: list[int] = []
    original = staff_live.read_case_events

    def counting(uow: Any, stream: Any, last: int | None) -> Any:
        reads.append(1)
        return original(uow, stream, last)

    monkeypatch.setattr(staff_live, "read_case_events", counting)
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    double = RecordingLiveChat(
        LiveView(controller_kind="human", controller_name="Riley", state="joined", since=JOIN_AT)
    )
    app = staff_live_app(monkeypatch, tmp_path, store=store, live_chat=double)

    async def scenario() -> float:
        async with running(app) as tg:
            seed_live_case(app_uow(app))
            gate = provided(app, get_reset_gate)
            with gate.hold():
                with anyio.fail_after(0.5):
                    handle = await open_stream(tg, app, URL, token=token)
                assert handle.status == 200
                assert await read_until_heartbeat(handle) == []
                assert reads == []
            with anyio.fail_after(1):
                while not reads:
                    await anyio.sleep(0.01)
            new_id = _append(app, WP2_REF, "case_changed", _changed(2))
            assert frame_ids(await read_frames(handle, 1)) == [new_id]
            await close_stream(handle)

            async def hold_gate() -> None:
                with gate.hold():
                    await anyio.sleep(0.3)

            tg.start_soon(hold_gate)
            while not gate.held():
                await anyio.sleep(0.005)
            started = time.monotonic()
            status, _, _ = await asgi_call(
                app, "POST", live_url(str(WP2_REF)), token=token, json_body={"action": "join"}
            )
            assert status == 200
            return time.monotonic() - started

    assert anyio.run(scenario) >= 0.25


def test_malformed_last_event_id_is_ignored(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """PA-5: a malformed Last-Event-ID is as if absent: start at the newest demo_reset, no stream_reconnect."""
    fast_stream(monkeypatch)
    store = FakeSessionStore()
    token = store.issue(DemoRole.REPRESENTATIVE)
    app = staff_live_app(monkeypatch, tmp_path, store=store)

    async def scenario() -> tuple[list[int], int, list[dict[str, Any]]]:
        async with running(app) as tg:
            seed_live_case(app_uow(app))
            _append(app, WP2_REF, "case_changed", _changed(1))
            _append(app, WP2_REF, "demo_reset", {"speaker": EVENT_SPEAKER, "line": RESET_LINE})
            changed_id = _append(app, WP2_REF, "case_changed", _changed(2))
            with captured_log() as log:
                handle = await open_stream(tg, app, URL, token=token, last_event_id="abc")
                frames = await read_frames(handle, 1)
                await close_stream(handle)
            return frame_ids(frames), changed_id, records_of(log, "stream_reconnect")

    ids, changed_id, records = anyio.run(scenario)
    assert ids == [changed_id]  # the demo_reset itself is before the start, so only the later event arrives
    assert records == []
