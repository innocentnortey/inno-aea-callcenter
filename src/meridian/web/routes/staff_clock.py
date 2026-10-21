"""CON-8 advance: `advanceDemoClock`, POST /api/demo/clock, supervisor only (stage7/staff.md §8). AEA-47.

One call DemoService.advance_clock(step, actor=actor, request_id=ctx.request_id) (cases.md §6, MC-13). The body is the
service's now, label and became_overdue, unchanged (R-W-17): the route reads no clock and builds no label. While a reset
holds the ResetGate the middleware answers 503 before this runs (staff.md §11). The GET on this path is AEA-43's.
"""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from meridian.domain.common import RequestId
from meridian.domain.staff import StaffActor, StaffRole
from meridian.web.deps import get_demo_service, get_request_context, require_staff
from meridian.web.middleware import RequestContext
from meridian.web.schemas.staff_clock import ClockAdvanceRequest, ClockAdvanceResponse, ClockStepName

ADVANCE_PATH = "/api/demo/clock"
ADVANCE_OPERATION = "advanceDemoClock"
_SUPERVISOR_ONLY = require_staff(StaffRole.SUPERVISOR)  # the operation's x-roles: [supervisor] (MC-4)


class ClockAdvancer(Protocol):
    """The one DemoService method this route calls (cases.md §6, MC-13); AEA-30's DemoService satisfies it."""

    def advance_clock(self, step: ClockStepName, *, actor: StaffActor, request_id: RequestId) -> object: ...


def advance_demo_clock(
    body: ClockAdvanceRequest,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    actor: StaffActor = Depends(_SUPERVISOR_ONLY),  # noqa: B008
    demo: ClockAdvancer = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    result = demo.advance_clock(body.step, actor=actor, request_id=ctx.request_id)
    payload = ClockAdvanceResponse.model_validate(result, from_attributes=True)
    return JSONResponse(payload.model_dump(mode="json"))


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        ADVANCE_PATH,
        advance_demo_clock,
        methods=["POST"],
        operation_id=ADVANCE_OPERATION,
        response_model=None,
    )
    return router
