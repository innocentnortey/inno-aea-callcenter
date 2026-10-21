"""CON-10: getSession, listDemoRoles, switchRole (stage7/staff.md section 2, section 11).

Sync routes: the real store touches SQLite. No cookie is written here and nothing is logged.
"""

from __future__ import annotations

from typing import Protocol, cast

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response

from meridian.domain.common import ApiErrorCode
from meridian.domain.staff import DemoRole, LoginSession, LoginSessionId, SessionInfoData
from meridian.services.staff import ROLE_CARDS, SessionGone
from meridian.web.deps import LoginSessions, get_login_session, get_login_sessions
from meridian.web.errors import ApiProblem
from meridian.web.schemas.auth import SessionInfo
from meridian.web.schemas.staff_session import RoleLine, RolesResponse, SwitchRoleRequest


class RoleSwitcher(LoginSessions, Protocol):
    """web.md section 2: ``switch_role`` is not part of ``LoginSessions``; the one bound store has it."""

    def switch_role(self, session_id: LoginSessionId, role: DemoRole) -> LoginSession: ...


def get_role_switcher(sessions: LoginSessions = Depends(get_login_sessions)) -> RoleSwitcher:  # noqa: B008
    return cast(RoleSwitcher, sessions)


def _info_body(info: SessionInfoData) -> JSONResponse:
    body = SessionInfo(
        authenticated=True,
        role=info.role,
        display_name=info.display_name,
        sees=info.sees,
        signed_in_at=info.signed_in_at,
    )
    return JSONResponse(body.model_dump(mode="json"))


def get_session(
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    sessions: LoginSessions = Depends(get_login_sessions),  # noqa: B008
) -> Response:
    return _info_body(sessions.session_info(session))


def list_demo_roles(_session: LoginSession = Depends(get_login_session)) -> Response:  # noqa: B008
    roles = RolesResponse(
        roles=tuple(
            RoleLine(role=c.role, display_name=c.display_name, sees=c.sees_line) for c in ROLE_CARDS.values()
        )
    )
    return JSONResponse(roles.model_dump(mode="json"))


def switch_role(
    body: SwitchRoleRequest,
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    switcher: RoleSwitcher = Depends(get_role_switcher),  # noqa: B008
) -> Response:
    try:
        changed = switcher.switch_role(session.session_id, body.role)
    except SessionGone:
        raise ApiProblem(401, ApiErrorCode.UNAUTHENTICATED, details={"reason": "none"}) from None
    return _info_body(switcher.session_info(changed))


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        "/api/session", get_session, methods=["GET"], operation_id="getSession", response_model=None
    )
    router.add_api_route(
        "/api/session/roles",
        list_demo_roles,
        methods=["GET"],
        operation_id="listDemoRoles",
        response_model=None,
    )
    router.add_api_route(
        "/api/session/role", switch_role, methods=["PUT"], operation_id="switchRole", response_model=None
    )
    return router
