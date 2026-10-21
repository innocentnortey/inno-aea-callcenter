"""Customer chat routes: `submitTurn` (CON-2). The CON-1 routes join when the session service can be built.

Thin sync handlers (DO-3 section 2.1): parse, call the service, shape the answer. Ownership of the path thread comes
from `owned_thread`; `submitTurn` never answers 429, a refused rate-limit verdict becomes a notice in a 200.
"""

from __future__ import annotations

from typing import Final

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from meridian.domain.common import ApiErrorCode, ThreadId
from meridian.domain.staff import LoginSession
from meridian.services.turn import RunTurn, ThreadNotOpen, TurnInProgress, TurnService
from meridian.web.deps import get_login_session, get_request_context, get_turn_service, owned_thread
from meridian.web.errors import ApiProblem
from meridian.web.middleware import RequestContext
from meridian.web.schemas.chat import TurnRequest

CHAT_LOGGER: Final = "meridian.web.chat"


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
        "/api/chat/sessions/{thread_id}/turns",
        submit_turn,
        methods=["POST"],
        operation_id="submitTurn",
        response_model=None,
    )
    return router
