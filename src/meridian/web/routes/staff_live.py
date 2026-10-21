"""CON-14 liveChatAction (a def route) and CON-21 streamCaseEvents (an async SSE route with its own
generator; DO-3 S-11). stage7/staff.md sections 5 to 7 and 11. The route files read no clock; poll and heartbeat are
this file's own copies of web.md section 11's values.

During a reset a CON-21 connect skips its existence lookup (the stream never waits on connect), so an unknown case
opened mid-reset only heartbeats until the client closes."""

from __future__ import annotations

import functools
import re
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Final, cast

import anyio
import anyio.to_thread
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from meridian.domain.common import ApiErrorCode, CaseRef
from meridian.domain.staff import StaffActor, StaffRole
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.services.live_chat import LiveChatService, LiveRefused
from meridian.services.reset_gate import ResetGate
from meridian.web.deps import (
    get_live_chat,
    get_request_context,
    get_reset_gate,
    get_stream_poll_limiter,
    get_uow_factory,
    require_staff,
)
from meridian.web.errors import ApiProblem
from meridian.web.logging import STREAM_LOGGER, emit_record
from meridian.web.middleware import RequestContext
from meridian.web.schemas.staff_live import (
    CASE_EVENT_TYPES,
    CLOSING_CASE_EVENT_TYPES,
    HEARTBEAT_FRAME,
    LiveActionRequest,
    StoredCaseEvent,
    encode_case_frame,
    live_action_response,
    parse_last_event_id,
)

if TYPE_CHECKING:
    from meridian.adapters.sqlite.rows import EventRow, StreamKey

# Plain module globals (not Final): read at request time so tests can patch them.
STREAM_POLL_S = 1.0  # [A] web.md section 11 / DO-3 S-11; this file's own copy (AC-19)
STREAM_HEARTBEAT_S = (
    15.0  # [Source: OpenAPI streamChatEvents "Heartbeat comment every 15 s"; web.md section 11]
)
LIVE_PATH: Final = "/api/staff/cases/{reference}/live"
EVENTS_PATH: Final = "/api/staff/cases/{reference}/events"
LAST_EVENT_ID_HEADER: Final = "last-event-id"
STATUS_BY_CODE: Final[Mapping[str, int]] = {
    "CASE_NOT_FOUND": 404,
    "NOT_CLAIMED_BY_YOU": 403,
    "CASE_ALREADY_CLAIMED": 409,
    "NOT_LIVE": 409,
}
_LIVE_ROLES = require_staff(StaffRole.REPRESENTATIVE)  # x-roles of liveChatAction
_STREAM_ROLES = require_staff(
    StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR, StaffRole.OWNER
)  # x-roles of CON-21


def parse_case_ref(reference: str) -> CaseRef | None:
    return CaseRef(reference) if re.fullmatch(CaseRef.PATTERN, reference) else None


def case_stream_key(case_ref: CaseRef) -> StreamKey:
    """Equals adapters.sqlite.rows.case_stream; kept out of web/ at run time."""
    return cast("StreamKey", "case:" + str(case_ref))


def read_case_events(
    uow: UnitOfWorkFactory, stream: StreamKey, last: int | None
) -> tuple[int, list[EventRow]]:
    """One read unit of work; runs on a worker thread. With no start, the start is the newest demo_reset (MC-8)."""
    with uow(write=False) as tx:
        if last is None:
            found = tx.core.events.latest_of(stream, "demo_reset")
            last = 0 if found is None else found
        return last, tx.core.events.after(stream, last)


async def case_event_frames(
    *,
    start: int | None,
    read_after: Callable[[int | None], Awaitable[tuple[int, Sequence[StoredCaseEvent]]]],
    reset_held: Callable[[], bool],
    disconnected: Callable[[], Awaitable[bool]],
    poll_s: float,
    heartbeat_s: float,
    on_replayed: Callable[[int], None] | None,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = anyio.sleep,
) -> AsyncIterator[bytes]:
    """Poll, replay and heartbeat. Exceptions are not caught: a failing read ends the stream and the browser reconnects."""
    last: int | None = start
    reported = on_replayed is None
    last_sent_at = monotonic()
    try:
        while True:
            if await disconnected():
                return
            if not reset_held():
                last, rows = await read_after(last)
                frames: list[bytes] = []
                closing = False
                for row in rows:
                    last = row.id
                    if row.type not in CASE_EVENT_TYPES:
                        continue
                    frames.append(encode_case_frame(row))
                    if row.type in CLOSING_CASE_EVENT_TYPES:
                        closing = True
                        break
                if not reported:
                    reported = True
                    if on_replayed is not None:
                        on_replayed(len(frames))
                for frame in frames:
                    yield frame
                if frames:
                    last_sent_at = monotonic()
                if closing:
                    return
            if monotonic() - last_sent_at >= heartbeat_s:
                yield HEARTBEAT_FRAME
                last_sent_at = monotonic()
            await sleep(poll_s)
    finally:
        if not reported and on_replayed is not None:
            on_replayed(0)


def known_case(
    reference: str,
    uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
    gate: ResetGate = Depends(get_reset_gate),  # noqa: B008
) -> CaseRef:
    """Sync dependency (runs on a worker thread): the case exists, else 404 before any frame."""
    ref = parse_case_ref(reference)
    if ref is None:
        raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND)  # the malformed value is never echoed (PA-4)
    if gate.held():
        return ref  # the stream never waits on connect (staff.md section 11)
    with uow(write=False) as tx:
        found = tx.core.cases_ro.owner(ref)
    if found is None:
        raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND, details={"reference": str(ref)})
    return ref


def live_chat_action(
    reference: str,
    body: LiveActionRequest,
    actor: StaffActor = Depends(_LIVE_ROLES),  # noqa: B008
    live_chat: LiveChatService = Depends(get_live_chat),  # noqa: B008
) -> JSONResponse:
    """CON-14: join, send, hand back or close a live chat."""
    ref = parse_case_ref(reference)
    if ref is None:
        raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND)
    if body.action == "join":
        result = live_chat.join(ref, actor)
    elif body.action == "send":
        if body.text is None:
            raise ApiProblem(400, ApiErrorCode.VALIDATION_ERROR, field="text", constraint="required for send")
        result = live_chat.send(ref, body.text, actor)
    elif body.action == "hand_back":
        result = live_chat.hand_back(ref, actor)
    else:
        result = live_chat.close(ref, actor)
    if isinstance(result, LiveRefused):
        raise ApiProblem(STATUS_BY_CODE[result.code], ApiErrorCode(result.code), details=dict(result.details))
    return JSONResponse(live_action_response(result).model_dump(mode="json"))


async def stream_case_events(
    request: Request,
    actor: StaffActor = Depends(_STREAM_ROLES),  # noqa: B008  declared first: 403 before any read (AC-12)
    case_ref: CaseRef = Depends(known_case),  # noqa: B008
    context: RequestContext = Depends(get_request_context),  # noqa: B008
    uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
    limiter: anyio.CapacityLimiter = Depends(get_stream_poll_limiter),  # noqa: B008
    gate: ResetGate = Depends(get_reset_gate),  # noqa: B008
) -> StreamingResponse:
    """CON-21: this case's events as Server-Sent Events."""
    start = parse_last_event_id(request.headers.get(LAST_EVENT_ID_HEADER))
    stream = case_stream_key(case_ref)

    async def read_after(last: int | None) -> tuple[int, Sequence[StoredCaseEvent]]:
        return await anyio.to_thread.run_sync(
            functools.partial(read_case_events, uow, stream, last), limiter=limiter
        )

    on_replayed: Callable[[int], None] | None = None
    if start is not None and start > 0:
        last_event_id = start

        def report(replayed: int) -> None:
            emit_record(
                STREAM_LOGGER,
                {
                    "record": "stream_reconnect",
                    "request_id": str(context.request_id),
                    "case_ref": str(case_ref),
                    "last_event_id": last_event_id,
                    "replayed": replayed,
                },
            )

        on_replayed = report
    return StreamingResponse(
        case_event_frames(
            start=start,
            read_after=read_after,
            reset_held=gate.held,
            disconnected=request.is_disconnected,
            poll_s=STREAM_POLL_S,
            heartbeat_s=STREAM_HEARTBEAT_S,
            on_replayed=on_replayed,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store"},
    )


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        LIVE_PATH, live_chat_action, methods=["POST"], operation_id="liveChatAction", response_model=None
    )
    router.add_api_route(
        EVENTS_PATH, stream_case_events, methods=["GET"], operation_id="streamCaseEvents", response_model=None
    )
    return router
