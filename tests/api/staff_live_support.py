"""AEA-46 test support: the app builder, an in-process ASGI stream harness (pattern copied from AEA-41's
tests/api/events_support.py: no import from another slice's test file), and a recording LiveChatService double.
Synthetic, socket-free, no .env, no paid call."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import anyio
import pytest
from anyio.abc import TaskGroup
from anyio.streams.memory import MemoryObjectReceiveStream
from fastapi import FastAPI

from meridian.domain.common import CaseRef
from meridian.domain.staff import StaffActor
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.services.live_chat import LiveChatService, LiveRefused, LiveView
from meridian.web.deps import get_live_chat, get_uow_factory, provided
from tests.api.openapi_check import SseFrame
from tests.api.web_shell_support import FakeHeartbeat, FakeSessionStore, full_app, make_settings
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import ISSUED_DB
from tests.services.live_chat_support import JOIN_AT, store_redactor


# -- app builders -------------------------------------------------------------------------------------------------
def staff_live_app(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    store: FakeSessionStore,
    live_chat: object | None = None,
    at: datetime = JOIN_AT,
) -> FastAPI:
    """The REAL build_container (so the register_staff_live hunk includes the router). The real service replaces only
    AEA-30's still-unbound demo clock; a double replaces the service entirely."""
    settings = make_settings(tmp_path, issued_db_path=ISSUED_DB)
    app = full_app(monkeypatch, settings, store=store, heartbeat=FakeHeartbeat())
    if live_chat is not None:
        app.dependency_overrides[get_live_chat] = lambda: live_chat
    else:
        app.dependency_overrides[get_live_chat] = lambda: LiveChatService(
            provided(app, get_uow_factory), FixedClock(at), store_redactor
        )
    return app


def app_uow(app: FastAPI) -> UnitOfWorkFactory:
    """Call only while the lifespan runs."""
    return provided(app, get_uow_factory)


def fast_stream(monkeypatch: pytest.MonkeyPatch, *, poll_s: float = 0.01, heartbeat_s: float = 0.05) -> None:
    monkeypatch.setattr("meridian.web.routes.staff_live.STREAM_POLL_S", poll_s)
    monkeypatch.setattr("meridian.web.routes.staff_live.STREAM_HEARTBEAT_S", heartbeat_s)


def live_url(ref: str) -> str:
    return f"/api/staff/cases/{ref}/live"


def events_url(ref: str) -> str:
    return f"/api/staff/cases/{ref}/events"


# -- double -------------------------------------------------------------------------------------------------------
class RecordingLiveChat:
    """Records (method, case_ref) and returns `result` for every method. It never stores text."""

    def __init__(self, result: LiveView | LiveRefused) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []

    def join(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused:
        self.calls.append(("join", str(case_ref)))
        return self.result

    def send(self, case_ref: CaseRef, text: str, actor: StaffActor) -> LiveView | LiveRefused:
        self.calls.append(("send", str(case_ref)))
        return self.result

    def hand_back(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused:
        self.calls.append(("hand_back", str(case_ref)))
        return self.result

    def close(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused:
        self.calls.append(("close", str(case_ref)))
        return self.result


# -- in-process ASGI stream harness -------------------------------------------------------------------------------
@dataclass
class StreamHandle:
    status: int | None
    headers: dict[str, str]
    started: anyio.Event
    disconnect: anyio.Event
    done: anyio.Event
    chunks: MemoryObjectReceiveStream[bytes]
    buffer: str = ""
    request_sent: bool = False
    ended: bool = field(default=False)


@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[TaskGroup]:
    """Run the app's lifespan and a task group for the streams; both end when the block exits."""
    async with app.router.lifespan_context(app):
        async with anyio.create_task_group() as tg:
            yield tg
            tg.cancel_scope.cancel()


def _scope(
    method: str, path: str, token: str | None, headers: Mapping[str, str] | None, spec_version: str
) -> dict[str, Any]:
    raw_headers: list[tuple[bytes, bytes]] = [(b"host", b"testserver")]
    if token is not None:
        raw_headers.append((b"cookie", f"mhc_session={token}".encode()))
    for name, value in (headers or {}).items():
        raw_headers.append((name.lower().encode(), value.encode()))
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": spec_version},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": raw_headers,
        "client": ("198.51.100.7", 50000),
        "server": ("testserver", 80),
        "state": {},
    }


async def asgi_call(
    app: FastAPI,
    method: str,
    path: str,
    *,
    token: str | None,
    json_body: object | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: float = 3.0,
) -> tuple[int, dict[str, str], bytes]:
    """One finite request through the app (status, lower-cased headers, the whole body)."""
    body = b"" if json_body is None else json.dumps(json_body).encode()
    all_headers = dict(headers or {})
    if json_body is not None:
        all_headers["content-type"] = "application/json"
        all_headers["content-length"] = str(len(body))
    scope = _scope(method, path, token, all_headers, "2.3")
    sent = False
    status = 0
    out_headers: dict[str, str] = {}
    chunks: list[bytes] = []
    disconnect = anyio.Event()

    async def receive() -> dict[str, Any]:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        nonlocal status, out_headers
        if message["type"] == "http.response.start":
            status = int(message["status"])
            out_headers = {k.decode().lower(): v.decode() for k, v in message["headers"]}
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    with anyio.fail_after(timeout):
        await app(scope, receive, send)  # type: ignore[arg-type]
    disconnect.set()
    return status, out_headers, b"".join(chunks)


async def open_stream(
    tg: TaskGroup,
    app: FastAPI,
    path: str,
    *,
    token: str | None,
    last_event_id: str | None = None,
    spec_version: str = "2.3",
    timeout: float = 2.0,
) -> StreamHandle:
    extra = {} if last_event_id is None else {"last-event-id": last_event_id}
    scope = _scope("GET", path, token, extra, spec_version)
    send_side, receive_side = anyio.create_memory_object_stream[bytes](max_buffer_size=10_000)
    handle = StreamHandle(
        status=None,
        headers={},
        started=anyio.Event(),
        disconnect=anyio.Event(),
        done=anyio.Event(),
        chunks=receive_side,
    )

    async def receive() -> dict[str, Any]:
        if not handle.request_sent:
            handle.request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        if handle.disconnect.is_set():
            return {"type": "http.disconnect"}
        await handle.disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            handle.status = int(message["status"])
            handle.headers = {k.decode().lower(): v.decode() for k, v in message["headers"]}
            handle.started.set()
        elif message["type"] == "http.response.body":
            data = message.get("body", b"")
            if data:
                send_side.send_nowait(data)
            if not message.get("more_body", False):
                send_side.close()

    async def run() -> None:
        try:
            await app(scope, receive, send)  # type: ignore[arg-type]
        finally:
            send_side.close()
            handle.started.set()
            handle.done.set()

    tg.start_soon(run)
    with anyio.fail_after(timeout):
        await handle.started.wait()
    return handle


async def next_item(handle: StreamHandle, *, timeout: float = 2.0) -> SseFrame | str | None:
    """The next frame (SseFrame), the next comment (text after ': '), or None at the end of the body."""
    while "\n\n" not in handle.buffer:
        if handle.ended:
            return None
        with anyio.fail_after(timeout):
            try:
                handle.buffer += (await handle.chunks.receive()).decode()
            except anyio.EndOfStream:
                handle.ended = True
                return None
    block, handle.buffer = handle.buffer.split("\n\n", 1)
    return _parse_block(block)


def _parse_block(block: str) -> SseFrame | str:
    lines = block.split("\n")
    if all(line.startswith(":") for line in lines):
        return "\n".join(line[1:].lstrip() for line in lines)
    fields: dict[str, list[str]] = {}
    for line in lines:
        name, _, value = line.partition(":")
        fields.setdefault(name, []).append(value[1:] if value.startswith(" ") else value)
    return SseFrame(
        event=fields["event"][0] if "event" in fields else None,
        id=fields["id"][0] if "id" in fields else None,
        data="\n".join(fields.get("data", [])),
    )


async def read_frames(handle: StreamHandle, count: int, *, timeout: float = 2.0) -> list[SseFrame]:
    frames: list[SseFrame] = []
    while len(frames) < count:
        item = await next_item(handle, timeout=timeout)
        assert item is not None, f"the body ended after {len(frames)} frames, expected {count}"
        if isinstance(item, SseFrame):
            frames.append(item)
    return frames


async def read_until_heartbeat(handle: StreamHandle, *, timeout: float = 2.0) -> list[SseFrame]:
    """Frames received before the next ': heartbeat' comment (proves 'nothing else arrived')."""
    frames: list[SseFrame] = []
    while True:
        item = await next_item(handle, timeout=timeout)
        if item is None or isinstance(item, str):
            return frames
        frames.append(item)


async def close_stream(handle: StreamHandle, *, timeout: float = 2.0) -> None:
    handle.disconnect.set()
    with anyio.fail_after(timeout):
        await handle.done.wait()


def frame_ids(frames: Sequence[SseFrame]) -> list[int]:
    return [int(f.id) for f in frames if f.id is not None]
