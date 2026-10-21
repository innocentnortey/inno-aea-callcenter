"""CON-6 to CON-9: listDemoInbox, getStaffing, setStaffing, getDemoClock (GET only) and resetDemo
(web.md §4, §5, §7; cases.md §6, §7; graph-tools §5). AEA-43.

Every operation accepts every signed-in role (R-48) and takes the session from the gate, never from a query, header
or body; sync routes (the real services touch SQLite); the inbox is the only response carrying a code, unwrapped
only while the response is serialised; nothing here logs.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Final, Protocol

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from meridian.domain.common import ApiErrorCode, RequestId
from meridian.domain.identity import InboxMessage
from meridian.domain.staff import DemoRole, LoginSession, LoginSessionId
from meridian.policy.texts import TextId, render
from meridian.services.reset_gate import ResetAlreadyRunning
from meridian.web.deps import (
    get_demo_service,
    get_identity_service,
    get_login_session,
    get_rate_limiter,
    get_request_context,
    get_reset_service,
    get_wall_clock,
)
from meridian.web.errors import ApiProblem
from meridian.web.middleware import RESET_RETRY_AFTER_MS, LimitScope, RateLimiter, RequestContext
from meridian.web.schemas.demo import (
    DemoClock,
    InboxMessageOut,
    InboxResponse,
    ResetRequest,
    ResetResponse,
    Staffing,
    StaffingMode,
    StaffingRequest,
    StaffingResponse,
)

CODE_GONE: Final = "·" * 6  # "······", shown when this process no longer holds the digits
RESET_FAILED_CODE: Final = "RESET_FAILED"


class _ClockLike(Protocol):
    @property
    def now(self) -> datetime: ...


class InboxReader(Protocol):
    def inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]: ...


class DemoControls(Protocol):
    def staffing(self) -> object: ...

    def set_staffing(self, mode: StaffingMode, *, request_id: RequestId, role: DemoRole) -> object: ...

    def clock_view(self) -> _ClockLike: ...


class DemoReset(Protocol):
    def reset(
        self,
        now: datetime,
        *,
        request_id: RequestId,
        session_id: LoginSessionId | None,
        role: DemoRole | None,
    ) -> object: ...


def to_wire_message(message: InboxMessage) -> InboxMessageOut:
    """Wire form of one inbox message. Without digits it shows dots and INBOX_CODE_GONE, and a message the service
    called `active` is sent as `expired` (AEA-43-1: dots are never an active code); `used` and `expired` keep their
    status (AEA-27 returns a used code with code=None)."""
    if message.code is None:
        return InboxMessageOut(
            id=message.id,
            at=message.at,
            to_masked=message.to_masked,
            body=SecretStr(render(TextId.INBOX_CODE_GONE)),
            code=SecretStr(CODE_GONE),
            status="expired" if message.status == "active" else message.status,
            expires_at=message.expires_at,
        )
    digits = message.code.get_secret_value()
    return InboxMessageOut(
        id=message.id,
        at=message.at,
        to_masked=message.to_masked,
        body=SecretStr(render(TextId.INBOX_CODE_BODY, digits=digits)),
        code=SecretStr(digits),
        status=message.status,
        expires_at=message.expires_at,
    )


def list_demo_inbox(
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    identity: InboxReader = Depends(get_identity_service),  # noqa: B008
    demo: DemoControls = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    now = demo.clock_view().now
    messages = identity.inbox(str(session.session_id), now=now)
    payload = InboxResponse(messages=tuple(to_wire_message(m) for m in messages))
    return JSONResponse(payload.model_dump(mode="json"))


def get_staffing(demo: DemoControls = Depends(get_demo_service)) -> JSONResponse:  # noqa: B008
    return JSONResponse(
        Staffing.model_validate(demo.staffing(), from_attributes=True).model_dump(mode="json")
    )


def set_staffing(
    body: StaffingRequest,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    demo: DemoControls = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    change = demo.set_staffing(body.mode, request_id=ctx.request_id, role=session.role)
    return JSONResponse(StaffingResponse.model_validate(change, from_attributes=True).model_dump(mode="json"))


def get_demo_clock(demo: DemoControls = Depends(get_demo_service)) -> JSONResponse:  # noqa: B008
    return JSONResponse(
        DemoClock.model_validate(demo.clock_view(), from_attributes=True).model_dump(mode="json")
    )


def reset_demo(
    body: ResetRequest,  # validated before this runs: confirm is true
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    resets: DemoReset = Depends(get_reset_service),  # noqa: B008
    limiter: RateLimiter = Depends(get_rate_limiter),  # noqa: B008
    wall_clock: Callable[[], datetime] = Depends(get_wall_clock),  # noqa: B008
) -> JSONResponse:
    now = wall_clock()
    stamp = now.timestamp()
    verdict = limiter.peek(LimitScope.RESET_IP, ctx.client_ip, stamp)
    if not verdict.allowed:
        raise ApiProblem(
            409, ApiErrorCode.RESET_IN_PROGRESS, details={"retry_after_ms": verdict.retry_after_ms or 1000}
        )
    limiter.record_reset(ctx.client_ip, stamp)
    try:
        result = resets.reset(
            now, request_id=ctx.request_id, session_id=session.session_id, role=session.role
        )
    except ResetAlreadyRunning:
        raise ApiProblem(
            409, ApiErrorCode.RESET_IN_PROGRESS, details={"retry_after_ms": RESET_RETRY_AFTER_MS}
        ) from None
    if getattr(result, "code", None) == RESET_FAILED_CODE:
        raise ApiProblem(500, ApiErrorCode.RESET_FAILED)
    return JSONResponse(ResetResponse.model_validate(result, from_attributes=True).model_dump(mode="json"))


def build_router() -> APIRouter:
    router = APIRouter(
        dependencies=[Depends(get_login_session)]
    )  # defence in depth: 401 if the gate let one by
    router.add_api_route(
        "/api/demo/inbox", list_demo_inbox, methods=["GET"], operation_id="listDemoInbox", response_model=None
    )
    router.add_api_route(
        "/api/demo/staffing", get_staffing, methods=["GET"], operation_id="getStaffing", response_model=None
    )
    router.add_api_route(
        "/api/demo/staffing", set_staffing, methods=["PUT"], operation_id="setStaffing", response_model=None
    )
    router.add_api_route(
        "/api/demo/clock", get_demo_clock, methods=["GET"], operation_id="getDemoClock", response_model=None
    )
    router.add_api_route(
        "/api/demo/reset", reset_demo, methods=["POST"], operation_id="resetDemo", response_model=None
    )
    return router
