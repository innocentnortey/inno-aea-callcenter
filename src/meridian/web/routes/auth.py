"""CON-22: `login` and `logout` (web.md section 2). Both are sync routes: AEA-44's real store touches SQLite."""

from __future__ import annotations

import hmac
from collections.abc import Callable
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import SecretStr

from meridian.config import Settings
from meridian.domain.common import ApiErrorCode
from meridian.domain.staff import LoginSession
from meridian.web.deps import (
    LoginSessions,
    get_login_sessions,
    get_rate_limiter,
    get_request_context,
    get_settings,
    get_wall_clock,
    wall_now,
)
from meridian.web.errors import ApiProblem
from meridian.web.logging import AUTH_LOGGER, auth_event, emit_record
from meridian.web.middleware import (
    SESSION_COOKIE,
    LimitScope,
    RateLimiter,
    RequestContext,
    cleared_session_cookie,
    session_cookie,
)
from meridian.web.schemas.auth import LoginRequest, LoginResponse, SessionInfo

LANDING = "/"


def _same(supplied: str, expected: SecretStr) -> bool:
    return hmac.compare_digest(supplied.encode("utf-8"), expected.get_secret_value().encode("utf-8"))


def login(
    body: LoginRequest,
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    sessions: LoginSessions = Depends(get_login_sessions),  # noqa: B008
    limiter: RateLimiter = Depends(get_rate_limiter),  # noqa: B008
    wall_clock: Callable[[], datetime] = Depends(get_wall_clock),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> Response:
    now = wall_clock()  # exactly one reading
    mono = now.timestamp()
    verdict = limiter.peek(LimitScope.LOGIN_IP, ctx.client_ip, mono)
    if not verdict.allowed:
        emit_record(
            AUTH_LOGGER,
            auth_event(request_id=ctx.request_id, outcome="rate_limited", session_id=None, at=now),
        )
        retry_ms = verdict.retry_after_ms or 1000
        raise ApiProblem(
            429,
            ApiErrorCode.LOGIN_RATE_LIMITED,
            details={"retry_after_ms": retry_ms},
            headers={"Retry-After": str(retry_ms // 1000)},
        )
    user_ok = _same(body.username, settings.demo_username)
    pass_ok = _same(body.password, settings.demo_password)
    # Bitwise, so both comparisons always run; an empty field never matches.
    if not (user_ok & pass_ok & (body.username != "") & (body.password != "")):
        limiter.record_login_reject(ctx.client_ip, mono)
        emit_record(
            AUTH_LOGGER,
            auth_event(request_id=ctx.request_id, outcome="rejected", session_id=None, at=now),
        )
        raise ApiProblem(401, ApiErrorCode.LOGIN_FAILED)

    old = request.cookies.get(SESSION_COOKIE)
    if old:
        prior = sessions.resolve(SecretStr(old), now)
        if isinstance(prior, LoginSession):
            sessions.end(SecretStr(old))
    issued = sessions.start(now)
    info = sessions.session_info(issued.session)
    payload = LoginResponse(
        session=SessionInfo(
            authenticated=True,
            role=info.role,
            display_name=info.display_name,
            sees=info.sees,
            signed_in_at=info.signed_in_at,
        ),
        landing=LANDING,
    )
    response = JSONResponse(payload.model_dump(mode="json"))
    lifetime = request.app.state.container.limits.web.login_session_lifetime_s
    response.headers.append(
        "set-cookie",
        session_cookie(issued.token.get_secret_value(), max_age=lifetime, secure=settings.cookie_secure),
    )
    emit_record(
        AUTH_LOGGER,
        auth_event(
            request_id=ctx.request_id, outcome="ok", session_id=str(issued.session.session_id), at=now
        ),
    )
    return response


def logout(
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    sessions: LoginSessions = Depends(get_login_sessions),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> Response:
    sessions.end(SecretStr(request.cookies.get(SESSION_COOKIE, "")))
    emit_record(
        AUTH_LOGGER,
        auth_event(
            request_id=ctx.request_id,
            outcome="logged_out",
            session_id=str(ctx.session.session_id) if ctx.session else None,
            at=wall_now(request.app),
        ),
    )
    response = Response(status_code=204)
    response.headers.append("set-cookie", cleared_session_cookie(secure=settings.cookie_secure))
    return response


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/api/login", login, methods=["POST"], operation_id="login", response_model=None)
    router.add_api_route(
        "/api/logout",
        logout,
        methods=["POST"],
        operation_id="logout",
        status_code=204,
        response_model=None,
    )
    return router
