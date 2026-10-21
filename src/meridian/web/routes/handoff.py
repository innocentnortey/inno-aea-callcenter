"""CON-4 `requestPerson` and CON-5 `saveFollowUp` (AEA-42; stage7/web.md section 8). Sync routes: SQLite is blocking."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from meridian.domain.common import ApiErrorCode, FollowUp, ThreadId
from meridian.domain.staff import LoginSession
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.services.person_request import (
    HandoffWriteFailed,
    PersonRequest,
    PersonRequestService,
    read_identity,
    settled_view_for,
)
from meridian.web.deps import (
    get_case_service,
    get_demo_service,
    get_login_session,
    get_person_requests,
    get_reply_composer,
    get_request_context,
    get_uow_factory,
    owned_thread,
)
from meridian.web.errors import ApiProblem
from meridian.web.middleware import RequestContext
from meridian.web.schemas.handoff import (
    HANDOFF_RETRY_AFTER_MS,
    FollowUpRequestBody,
    FollowUpResponse,
    HandoffRequestBody,
)


def build_router() -> APIRouter:
    router = APIRouter()

    @router.post("/api/chat/sessions/{thread_id}/handoff", operation_id="requestPerson", response_model=None)
    def request_person(
        body: HandoffRequestBody,
        thread: ThreadId = Depends(owned_thread),  # noqa: B008
        ctx: RequestContext = Depends(get_request_context),  # noqa: B008
        session: LoginSession = Depends(get_login_session),  # noqa: B008
        service: PersonRequestService = Depends(get_person_requests),  # noqa: B008
    ) -> JSONResponse:
        cmd = PersonRequest(
            thread_id=thread,
            turn_id=body.turn_id,
            request_id=ctx.request_id,
            demo_session=str(session.session_id),
            run_tag=ctx.run_tag,
            run_id=ctx.run_id,
        )
        try:
            outcome = service.request(cmd)
        except HandoffWriteFailed:
            raise ApiProblem(
                503,
                ApiErrorCode.HANDOFF_FAILED,
                details={"retry_after_ms": HANDOFF_RETRY_AFTER_MS},
            ) from None
        return JSONResponse(outcome.model_dump(mode="json"))

    @router.put("/api/chat/sessions/{thread_id}/follow-up", operation_id="saveFollowUp", response_model=None)
    def save_follow_up(
        body: FollowUpRequestBody,
        thread: ThreadId = Depends(owned_thread),  # noqa: B008
        uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
        cases: Any = Depends(get_case_service),  # noqa: B008
        demo: Any = Depends(get_demo_service),  # noqa: B008
        composer: Any = Depends(get_reply_composer),  # noqa: B008
    ) -> JSONResponse:
        if body.destination == "on_record" and read_identity(uow, thread).status != "verified":
            raise ApiProblem(409, ApiErrorCode.NOT_ALLOWED_IN_STATE, details={"state": "not_verified"})
        if cases.open_case_for_thread(thread) is None:
            raise ApiProblem(409, ApiErrorCode.NOT_ALLOWED_IN_STATE, details={"state": "no_open_case"})
        now = demo.clock_view().now
        saved = cases.set_followup(thread, body, now)  # FollowUpRequestBody has FollowUpChoice's three fields
        if not isinstance(saved, FollowUp):
            code = getattr(saved, "code", None)
            details = getattr(saved, "details", None)
            if str(code) == ApiErrorCode.NOT_ALLOWED_IN_STATE.value and isinstance(details, Mapping):
                raise ApiProblem(409, ApiErrorCode.NOT_ALLOWED_IN_STATE, details=dict(details))
            raise RuntimeError("saveFollowUp: unexpected result from set_followup")
        view = settled_view_for(uow, composer, thread, now)
        return JSONResponse(FollowUpResponse(followup=saved, settled=view).model_dump(mode="json"))

    return router
