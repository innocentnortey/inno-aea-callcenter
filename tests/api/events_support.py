"""AEA-41 test support: doubles, an in-process ASGI stream harness, seed helpers and payload fixtures.

Synthetic and socket-free: no `.env`, no paid call, no server. Other tickets may import it read-only.
"""

from __future__ import annotations

import copy
import sqlite3
import threading
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import anyio
import anyio.lowlevel
import pytest
from anyio.abc import TaskGroup
from anyio.streams.memory import MemoryObjectReceiveStream
from fastapi import FastAPI
from pydantic import JsonValue

import meridian.web.app as app_module
from meridian.adapters.sqlite.repos_core_aux import EventsRepo
from meridian.adapters.sqlite.rows import ConversationRow, EventRow, StreamEvent, StreamKey
from meridian.domain.common import ThreadId
from meridian.policy.limits import Limits
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.web.app import create_app
from meridian.web.container import Container, register_events, register_web
from meridian.web.deps import get_login_sessions, get_reset_gate, get_uow_factory
from meridian.web.routes.events import StreamTiming, get_stream_timing
from tests.api.openapi_check import SseFrame
from tests.api.web_shell_support import (
    FakeHeartbeat,
    FakeSessionStore,
    full_app,
    make_settings,
    new_thread_id,
)
from tests.fakes.clock import CHICAGO
from tests.fixtures.sqlite import ISSUED_DB

WP2_JOINED_AT = datetime(2026, 10, 16, 14, 22, tzinfo=CHICAGO)
WP2_MESSAGE_AT = datetime(2026, 10, 16, 14, 22, 40, tzinfo=CHICAGO)
STAFF_TEXT = "Hi Omar, I can look at the after-hours charge with you."
EVENT_SPEAKER: dict[str, JsonValue] = {"kind": "event", "display_name": None}
RILEY: dict[str, JsonValue] = {"kind": "representative", "display_name": "Riley"}
PAYLOADS: dict[str, dict[str, JsonValue]] = {
    "representative_joined": {
        "speaker": RILEY,
        "display_name": "Riley",
        "line": "Riley (demo representative) has joined.",
    },
    "ai_paused": {"speaker": EVENT_SPEAKER, "line": "The assistant is paused while Riley is here."},
    "staff_message": {"speaker": RILEY, "message_id": "m-88", "text": STAFF_TEXT},
    "ai_resumed": {
        "speaker": EVENT_SPEAKER,
        "line": "Riley handed the chat back to the automated assistant.",
    },
    "chat_closed": {"speaker": EVENT_SPEAKER, "line": "Riley closed this chat.", "composer_disabled": True},
    "demo_reset": {
        "speaker": EVENT_SPEAKER,
        "line": "The demo was reset, so this chat has ended. Nothing from it was kept.",
    },
    "case_changed": {},  # a CaseEvent type: never sent on CON-3
}
TAKEOVER_TRIO = ("representative_joined", "ai_paused", "staff_message")


def payload(event_type: str) -> dict[str, JsonValue]:
    """A deep copy of the fixture payload for the event type."""
    return copy.deepcopy(PAYLOADS[event_type])


# -- timing doubles -------------------------------------------------------------------------------------------
FAST_TIMING = StreamTiming(poll_s=0.01, heartbeat_s=3600.0)


class FakeMonotonic:
    """A test clock: sleep() advances it and never sleeps for real."""

    def __init__(self) -> None:
        self.now: float = 0.0

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds
        await anyio.lowlevel.checkpoint()

    def timing(self) -> StreamTiming:
        return StreamTiming(sleep=self.sleep, monotonic=self.monotonic)


# -- store doubles --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ReadCall:
    stream: str
    last: int
    thread: int  # threading.get_ident() of the reading thread


class FakeStreamStore:
    """UnitOfWorkFactory double: conversations.lookup from `rows`, events.after over an in-memory list."""

    def __init__(self, rows: Mapping[str, object] | None = None) -> None:
        self.rows: dict[str, object] = dict(rows or {})
        self.events: list[EventRow] = []
        self.write_flags: list[bool] = []
        self.reads: list[ReadCall] = []
        self.active_reads = 0
        self.max_active_reads = 0
        self.hold_reads: threading.Event | None = None
        self._lock = threading.Lock()

    def append(
        self,
        stream: str,
        event_type: str,
        data: dict[str, JsonValue],
        *,
        at: datetime = WP2_JOINED_AT,
        event_id: int | None = None,
    ) -> int:
        with self._lock:
            new_id = event_id if event_id is not None else max((e.id for e in self.events), default=0) + 1
            self.events.append(
                EventRow(id=new_id, stream=str(stream), type=event_type, payload=copy.deepcopy(data), at=at)
            )
        return new_id

    def after(self, stream: str, last: int) -> list[EventRow]:
        with self._lock:
            self.reads.append(ReadCall(stream=str(stream), last=last, thread=threading.get_ident()))
            self.active_reads += 1
            self.max_active_reads = max(self.max_active_reads, self.active_reads)
            hold = self.hold_reads
        try:
            if hold is not None:
                hold.wait(timeout=5)
            with self._lock:
                return sorted(
                    (e for e in self.events if e.stream == str(stream) and e.id > last), key=lambda e: e.id
                )
        finally:
            with self._lock:
                self.active_reads -= 1

    def _lookup(self, thread_id: str) -> object:
        return self.rows.get(str(thread_id))

    @contextmanager
    def _transaction(self) -> Iterator[Any]:
        conversations = type("Conversations", (), {"lookup": staticmethod(self._lookup)})()
        events = type(
            "Events", (), {"after": staticmethod(lambda stream, last: self.after(str(stream), last))}
        )()
        core = type("Core", (), {"conversations": conversations, "events": events})()
        yield type("Tx", (), {"core": core})()

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[Any]:
        self.write_flags.append(bool(write or exclusive))
        return self._transaction()


class RecordingUowFactory:
    """Wraps a real unit of work factory and records whether each unit asked to write."""

    def __init__(self, inner: UnitOfWorkFactory) -> None:
        self.inner = inner
        self.write_flags: list[bool] = []

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[Any]:
        self.write_flags.append(bool(write or exclusive))
        return self.inner(write=write, exclusive=exclusive)


class FlagGate:
    """ResetGate double."""

    def __init__(self) -> None:
        self.flag = False

    def held(self) -> bool:
        return self.flag


# -- real SQLite helpers --------------------------------------------------------------------------------------
def seed_conversation(uow: UnitOfWorkFactory, session_id: str, *, thread_id: str | None = None) -> str:
    tid = thread_id or new_thread_id()
    with uow(write=True) as tx:
        tx.core.conversations.insert(
            ConversationRow(
                thread_id=ThreadId(tid),
                demo_session=session_id,
                run_tag="live",
                agent_version="test-agent-0",
                started_at=WP2_JOINED_AT,
            )
        )
        tx.commit()
    return tid


def append_stored(
    uow: UnitOfWorkFactory,
    stream: str,
    items: Sequence[tuple[str, dict[str, JsonValue]]],
    *,
    at: datetime = WP2_JOINED_AT,
) -> list[int]:
    ids: list[int] = []
    with uow(write=True) as tx:
        for event_type, data in items:
            ids.append(
                int(
                    tx.core.events.append(
                        StreamKey(stream), StreamEvent(type=event_type, payload=data, at=at)
                    )
                )
            )
        tx.commit()
    return ids


def table_counts(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        counts: dict[str, int] = {}
        for name in names:
            row = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()  # noqa: S608
            counts[name] = int(row[0])
        return counts
    finally:
        conn.close()


def count_event_reads(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    """Wrap EventsRepo.after so each call appends (stream, last)."""
    calls: list[tuple[str, int]] = []
    original = EventsRepo.after

    def wrapped(self: EventsRepo, stream: StreamKey, last: int) -> list[EventRow]:
        calls.append((str(stream), int(last)))
        return original(self, stream, last)

    monkeypatch.setattr(EventsRepo, "after", wrapped)
    return calls


# -- app builders ---------------------------------------------------------------------------------------------
def install_events_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    """A container builder that runs only register_web and register_events."""

    def build(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container:
        limits = Limits()
        container = Container(settings=settings, limits=limits)
        register_web(container, app, settings=settings, limits=limits)
        register_events(container, app, settings=settings, limits=limits)
        container.build()
        return container

    monkeypatch.setattr(app_module, "build_container", build)


def events_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Any,
    *,
    uow: object,
    store: FakeSessionStore,
    gate: object | None = None,
    timing: StreamTiming = FAST_TIMING,
) -> FastAPI:
    install_events_builder(monkeypatch)
    app = create_app(settings)
    app.dependency_overrides[get_login_sessions] = lambda: store
    app.dependency_overrides[get_uow_factory] = lambda: uow
    app.dependency_overrides[get_stream_timing] = lambda: timing
    if gate is not None:
        app.dependency_overrides[get_reset_gate] = lambda: gate
    app.state.test_store = store
    return app


def full_stream_app(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    store: FakeSessionStore,
    timing: StreamTiming = FAST_TIMING,
) -> FastAPI:
    settings = make_settings(tmp_path, issued_db_path=ISSUED_DB)
    app = full_app(monkeypatch, settings, store=store, heartbeat=FakeHeartbeat())
    app.dependency_overrides[get_stream_timing] = lambda: timing
    return app


# -- in-process ASGI stream harness ---------------------------------------------------------------------------
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


async def open_stream(
    tg: TaskGroup,
    app: FastAPI,
    thread_id: str,
    *,
    token: str | None,
    last_event_id: str | None = None,
    spec_version: str = "2.3",
    timeout: float = 2.0,
) -> StreamHandle:
    path = f"/api/chat/sessions/{thread_id}/events"
    headers: list[tuple[bytes, bytes]] = [(b"host", b"testserver")]
    if token is not None:
        headers.append((b"cookie", f"mhc_session={token}".encode()))
    if last_event_id is not None:
        headers.append((b"last-event-id", last_event_id.encode()))
    scope: dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": spec_version},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": headers,
        "client": ("198.51.100.7", 50000),
        "server": ("testserver", 80),
        "state": {},
    }
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
            body = message.get("body", b"")
            if body:
                send_side.send_nowait(body)
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


async def close_stream(handle: StreamHandle, *, timeout: float = 2.0) -> None:
    handle.disconnect.set()
    with anyio.fail_after(timeout):
        await handle.done.wait()


def parse_sse_text(text: str) -> list[SseFrame | str]:
    """The same parser over a whole body."""
    return [_parse_block(block) for block in text.split("\n\n") if block.strip()]


def frame_ids(frames: Sequence[SseFrame]) -> list[int]:
    return [int(f.id) for f in frames if f.id is not None]


def session_of(store: FakeSessionStore, token: str) -> str:
    return str(store.session_of(token).session_id)
