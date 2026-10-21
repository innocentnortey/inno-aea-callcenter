"""CON-3 streamChatEvents (stage7/web.md section 11): one async SSE route that polls this thread's events stream off
the event loop, replays from Last-Event-ID, sends a heartbeat comment and closes after chat_closed or demo_reset.
Reads only; writes no row and no event."""

from __future__ import annotations

import functools
import time
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, cast

import anyio
import anyio.to_thread
from fastapi import APIRouter, Depends, Request
from starlette.responses import StreamingResponse

from meridian.domain.common import ThreadId
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.services.reset_gate import ResetGate
from meridian.web.deps import (
    get_request_context,
    get_reset_gate,
    get_stream_poll_limiter,
    get_uow_factory,
    owned_stream_thread,
)
from meridian.web.logging import STREAM_LOGGER, emit_record
from meridian.web.middleware import RequestContext
from meridian.web.schemas.events import (
    CHAT_EVENT_TYPES,
    CLOSING_EVENT_TYPES,
    HEARTBEAT_FRAME,
    StoredEvent,
    encode_event_frame,
)

if TYPE_CHECKING:
    from meridian.adapters.sqlite.rows import EventRow, StreamKey

STREAM_POLL_S: Final = 1.0  # [A] DO-3 S-11; replaced by the measured first_event_ms at Stage 9
STREAM_HEARTBEAT_S: Final = (
    15  # [Source: OpenAPI streamChatEvents "Heartbeat comment every 15 s (decided 2026-10-21)"]
)
EVENTS_PATH: Final = "/api/chat/sessions/{thread_id}/events"
OPERATION_ID: Final = "streamChatEvents"
LAST_EVENT_ID_HEADER: Final = "last-event-id"
MAX_EVENT_ID_DIGITS: Final = 18


@dataclass(frozen=True)
class StreamTiming:
    """How long the loop sleeps and how it reads time; tests override get_stream_timing."""

    poll_s: float = STREAM_POLL_S
    heartbeat_s: float = STREAM_HEARTBEAT_S
    sleep: Callable[[float], Awaitable[None]] = anyio.sleep
    monotonic: Callable[[], float] = time.monotonic


def get_stream_timing() -> StreamTiming:
    return StreamTiming()


def parse_last_event_id(raw: str | None) -> int:
    """The id to resume after; anything that is not 1 to 18 ASCII digits starts at 0 (never an undocumented status)."""
    if raw is None:
        return 0
    value = raw.strip()
    if value.isascii() and value.isdigit() and 1 <= len(value) <= MAX_EVENT_ID_DIGITS:
        return int(value)
    return 0


def thread_stream_key(thread_id: ThreadId) -> StreamKey:
    """The thread form of a stream key (equals adapters.sqlite.rows.thread_stream; kept out of web/ at run time)."""
    return cast("StreamKey", str(thread_id))


def read_events_after(uow: UnitOfWorkFactory, stream: StreamKey, last: int) -> list[EventRow]:
    """One read unit of work; runs on a worker thread."""
    with uow(write=False) as tx:
        return tx.core.events.after(stream, last)


async def chat_event_frames(
    *,
    start: int,
    read_after: Callable[[int], Awaitable[Sequence[StoredEvent]]],
    reset_held: Callable[[], bool],
    disconnected: Callable[[], Awaitable[bool]],
    timing: StreamTiming,
    on_replayed: Callable[[int], None] | None,
) -> AsyncGenerator[bytes]:
    """Poll, replay and heartbeat. Exceptions are not caught: a failing read ends the stream and the browser reconnects."""
    last = start
    reported = on_replayed is None
    last_sent_at = timing.monotonic()
    try:
        while True:
            if await disconnected():
                return
            if not reset_held():
                rows = await read_after(last)
                frames: list[bytes] = []
                closing = False
                for row in rows:
                    last = row.id
                    if row.type not in CHAT_EVENT_TYPES:
                        continue
                    frames.append(encode_event_frame(row))
                    if row.type in CLOSING_EVENT_TYPES:
                        closing = True
                        break
                if not reported:
                    reported = True
                    if on_replayed is not None:
                        on_replayed(len(frames))
                for frame in frames:
                    yield frame
                if frames:
                    last_sent_at = timing.monotonic()
                if closing:
                    return
            if timing.monotonic() - last_sent_at >= timing.heartbeat_s:
                yield HEARTBEAT_FRAME
                last_sent_at = timing.monotonic()
            await timing.sleep(timing.poll_s)
    finally:
        if not reported and on_replayed is not None:
            on_replayed(0)


async def stream_chat_events(
    request: Request,
    owned: ThreadId = Depends(owned_stream_thread),  # noqa: B008
    context: RequestContext = Depends(get_request_context),  # noqa: B008
    uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
    limiter: anyio.CapacityLimiter = Depends(get_stream_poll_limiter),  # noqa: B008
    gate: ResetGate = Depends(get_reset_gate),  # noqa: B008
    timing: StreamTiming = Depends(get_stream_timing),  # noqa: B008
) -> StreamingResponse:
    """CON-3: this thread's chat events as Server-Sent Events."""
    start = parse_last_event_id(request.headers.get(LAST_EVENT_ID_HEADER))
    stream = thread_stream_key(owned)

    async def read_after(last: int) -> Sequence[StoredEvent]:
        return await anyio.to_thread.run_sync(
            functools.partial(read_events_after, uow, stream, last), limiter=limiter
        )

    on_replayed: Callable[[int], None] | None = None
    if start > 0:

        def record(replayed: int) -> None:
            emit_record(
                STREAM_LOGGER,
                {
                    "record": "stream_reconnect",
                    "request_id": str(context.request_id),
                    "thread_id": str(owned),
                    "last_event_id": start,
                    "replayed": replayed,
                },
            )

        on_replayed = record

    return StreamingResponse(
        chat_event_frames(
            start=start,
            read_after=read_after,
            reset_held=gate.held,
            disconnected=request.is_disconnected,
            timing=timing,
            on_replayed=on_replayed,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store"},
    )


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        EVENTS_PATH, stream_chat_events, methods=["GET"], operation_id=OPERATION_ID, response_model=None
    )
    return router
