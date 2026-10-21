"""Customer chat routes: `startChatSession`, `getChatThread` (CON-1) and `submitTurn` (CON-2).

Thin sync handlers (DO-3 section 2.1): parse, call the service, shape the answer. Ownership of the path thread comes
from `owned_thread`; `submitTurn` never answers 429, a refused rate-limit verdict becomes a notice in a 200.
"""

from __future__ import annotations

from typing import Final

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from meridian.domain.blocks import Speaker
from meridian.domain.common import ApiErrorCode, ThreadId
from meridian.domain.staff import LoginSession
from meridian.services.session import SessionService, greeting_block
from meridian.services.turn import ChatController, RunTurn, ThreadNotOpen, TurnInProgress, TurnService
from meridian.web.deps import (
    get_login_session,
    get_request_context,
    get_session_service,
    get_turn_service,
    owned_thread,
)
from meridian.web.errors import ApiProblem
from meridian.web.middleware import RequestContext
from meridian.web.schemas.chat import (
    ChatThread,
    ChatThreadTurn,
    EventsRef,
    StartSessionResponse,
    TurnRequest,
)

CHAT_LOGGER: Final = "meridian.web.chat"


def start_chat_session(
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    sessions: SessionService = Depends(get_session_service),  # noqa: B008
) -> JSONResponse:
    opened = sessions.open(session, run_tag=ctx.run_tag, run_id=ctx.run_id, request_id=ctx.request_id)
    body = StartSessionResponse(
        thread_id=opened.thread_id,
        greeting=greeting_block(opened.greeting_text, opened.greeting_at),
        demo_clock=opened.clock,
        staffing=opened.staffing,
        controller=ChatController(
            kind=opened.controller.kind, display_name=opened.controller.representative_name
        ),
        settled=opened.settled,
        events=EventsRef(
            url=f"/api/chat/sessions/{opened.thread_id}/events", last_event_id=opened.last_event_id
        ),
        limits=opened.limits,
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=201)


def get_chat_thread(
    owned: ThreadId = Depends(owned_thread),  # noqa: B008
    sessions: SessionService = Depends(get_session_service),  # noqa: B008
) -> JSONResponse:
    try:
        history = sessions.thread(owned)
    except ThreadNotOpen:
        raise ApiProblem(404, ApiErrorCode.SESSION_NOT_FOUND) from None
    turns = tuple(
        ChatThreadTurn(
            turn_id=e.turn_id,
            speaker=Speaker(kind=e.speaker_kind, display_name=e.speaker_name),
            at=e.at,
            text=e.text,
            blocks=e.blocks,
        )
        for e in history.entries
    )
    body = ChatThread(
        thread_id=history.thread_id,
        state=history.state,
        turns=turns,
        settled=history.settled,
        demo_clock=history.clock,
        staffing=history.staffing,
        last_event_id=history.last_event_id,
    )
    return JSONResponse(body.model_dump(mode="json"))


def submit_turn(
    body: TurnRequest,
    owned: ThreadId = Depends(owned_thread),  # noqa: B008
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    turns: TurnService = Depends(get_turn_service),  # noqa: B008
) -> JSONResponse:
    cmd = RunTurn(
        thread_id=owned,
        turn_id=body.turn_id,
        request_id=ctx.request_id,
        demo_session=str(session.session_id),
        payload=body.payload,
        run_tag=ctx.run_tag,
        run_id=ctx.run_id,
    )
    verdict = ctx.turn_verdict
    try:
        if verdict is not None and not verdict.allowed:
            result = turns.rate_limited(cmd, verdict)
        else:
            result = turns.run_turn(cmd)
    except TurnInProgress as exc:
        raise ApiProblem(
            409, ApiErrorCode.TURN_IN_PROGRESS, details={"retry_after_ms": exc.retry_after_ms}
        ) from None
    except ThreadNotOpen:
        raise ApiProblem(404, ApiErrorCode.SESSION_NOT_FOUND) from None
    return JSONResponse(result.model_dump(mode="json"))


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        "/api/chat/sessions",
        start_chat_session,
        methods=["POST"],
        operation_id="startChatSession",
        status_code=201,
        response_model=None,
    )
    router.add_api_route(
        "/api/chat/sessions/{thread_id}",
        get_chat_thread,
        methods=["GET"],
        operation_id="getChatThread",
        response_model=None,
    )
    router.add_api_route(
        "/api/chat/sessions/{thread_id}/turns",
        submit_turn,
        methods=["POST"],
        operation_id="submitTurn",
        response_model=None,
    )
    return router
