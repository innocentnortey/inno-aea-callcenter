"""Every dependency provider the HTTP shell declares (web.md sections 2 to 4). Sole owner: AEA-23.

A provider whose ticket is later is declared by name here and bound by its owner's ``register_<area>()`` hunk through
the container keys below. Until bound it raises ``RuntimeError("not bound: <name>")`` when called, never at import.
Providers take the ``Request`` and resolve from ``app.state.container``; usage (``Depends(get_x)``) and overrides
(``app.dependency_overrides[get_x] = ...``) are the ordinary FastAPI ones. Hunks never call providers: they provide
and ``container.get`` the keys.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from datetime import datetime
from types import MappingProxyType
from typing import Any, Protocol, cast, runtime_checkable

import anyio
from fastapi import Depends, Request
from pydantic import SecretStr
from starlette.applications import Starlette

from meridian.config import Settings
from meridian.domain.common import ApiErrorCode, ThreadId
from meridian.domain.staff import (
    IssuedSession,
    LoginSession,
    RoleRefusal,
    SessionExpired,
    SessionInfoData,
    SessionMissing,
    StaffActor,
    StaffRole,
)
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.services.reset_gate import ResetGate
from meridian.web.container import ContainerError, Key
from meridian.web.errors import ApiProblem
from meridian.web.middleware import RateLimiter, RequestContext

STREAM_POLL_THREADS = 4  # [A] DO-3 section 2.3 rule 4; WEB-19: one CapacityLimiter(4) per process


# -- protocols consumed here, implemented by later tickets ------------------------------------------------------
class LoginSessions(Protocol):
    """staff.md section 2 (AEA-44's StaffSessionStore)."""

    def start(self, now: datetime) -> IssuedSession: ...
    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired: ...
    def end(self, token: SecretStr) -> None: ...
    def session_info(self, session: LoginSession) -> SessionInfoData: ...


class StaffAccess(Protocol):
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal: ...


class MetricsReads(Protocol):
    def owner_metrics(self) -> Mapping[str, object]: ...
    def monitoring(self) -> Mapping[str, object]: ...
    def latest_eval(self) -> Mapping[str, object]: ...


class HeartbeatReader(Protocol):
    """cases.md section 8: the Heartbeat (AEA-32) satisfies it."""

    def fresh(self, mono: float) -> bool: ...


# -- container keys: the names other tickets provide ------------------------------------------------------------
LOGIN_SESSIONS: Key[LoginSessions] = Key("login_sessions")  # AEA-44
STAFF_ACCESS: Key[StaffAccess] = Key("staff_access")  # AEA-44 (same instance)
FLAG_SERVICE: Key[Any] = Key("flag_service")  # AEA-44, FlagService (staff.md section 2)
SESSION_SERVICE: Key[Any] = Key("session_service")  # AEA-40, SessionService (web.md section 14)
TURN_SERVICE: Key[Any] = Key("turn_service")  # AEA-40, TurnService (web.md section 9)
PERSON_REQUESTS: Key[Any] = Key("person_requests")  # AEA-42, PersonRequestService (web.md section 8)
HANDOFF_SERVICE: Key[Any] = Key("handoff_service")  # AEA-29, HandoffService (cases.md section 5)
CASE_SERVICE: Key[Any] = Key("case_service")  # AEA-29, CaseService (cases.md section 5)
REPLY_COMPOSER: Key[Any] = Key("reply_composer")  # AEA-21 / AEA-51, ReplyComposer (graph-core section 13)
IDENTITY_SERVICE: Key[Any] = Key("identity_service")  # AEA-27, IdentityService (graph-tools section 5)
DEMO_SERVICE: Key[Any] = Key("demo_service")  # AEA-30, DemoService (cases.md section 6)
RESET_SERVICE: Key[Any] = Key("reset_service")  # AEA-31, ResetService (cases.md section 7)
RESET_GATE: Key[ResetGate] = Key("reset_gate")  # AEA-23
LIVE_CHAT: Key[Any] = Key("live_chat")  # AEA-46, LiveChatService (staff.md section 5)
METRICS_READS: Key[MetricsReads] = Key("metrics_reads")  # AEA-53
UOW_FACTORY: Key[UnitOfWorkFactory] = Key("uow_factory")  # AEA-10
STREAM_POLL_LIMITER: Key[anyio.CapacityLimiter] = Key("stream_poll_limiter")  # AEA-23
RATE_LIMITER: Key[RateLimiter] = Key("rate_limiter")  # AEA-23
WALL_CLOCK: Key[Callable[[], datetime]] = Key("wall_clock")  # AEA-23
HEARTBEAT: Key[HeartbeatReader] = Key("heartbeat")  # AEA-32


def _bound[T](app: Starlette, provider: Callable[..., Any], key: Key[T]) -> T:
    container = getattr(app.state, "container", None)
    if container is None:
        raise RuntimeError(f"not bound: {provider.__name__}")
    try:
        return cast(T, container.get(key))
    except ContainerError as exc:
        if str(exc) == f"not provided: {key.name}":
            raise RuntimeError(f"not bound: {provider.__name__}") from None
        raise


def get_login_sessions(request: Request) -> LoginSessions:
    return _bound(request.app, get_login_sessions, LOGIN_SESSIONS)


def get_staff_access(request: Request) -> StaffAccess:
    return _bound(request.app, get_staff_access, STAFF_ACCESS)


def get_flag_service(request: Request) -> Any:
    """FlagService (staff.md section 2), bound by AEA-44."""
    return _bound(request.app, get_flag_service, FLAG_SERVICE)


def get_session_service(request: Request) -> Any:
    """SessionService (web.md section 14), bound by AEA-40."""
    return _bound(request.app, get_session_service, SESSION_SERVICE)


def get_turn_service(request: Request) -> Any:
    """TurnService (web.md section 9), bound by AEA-40."""
    return _bound(request.app, get_turn_service, TURN_SERVICE)


def get_person_requests(request: Request) -> Any:
    """PersonRequestService (web.md section 8), bound by AEA-42."""
    return _bound(request.app, get_person_requests, PERSON_REQUESTS)


def get_handoff_service(request: Request) -> Any:
    """HandoffService (cases.md section 5), bound by AEA-29."""
    return _bound(request.app, get_handoff_service, HANDOFF_SERVICE)


def get_case_service(request: Request) -> Any:
    """CaseService (cases.md section 5), bound by AEA-29."""
    return _bound(request.app, get_case_service, CASE_SERVICE)


def get_reply_composer(request: Request) -> Any:
    """ReplyComposer (graph-core section 13), bound by AEA-21 / AEA-51."""
    return _bound(request.app, get_reply_composer, REPLY_COMPOSER)


def get_identity_service(request: Request) -> Any:
    """IdentityService (graph-tools section 5), bound by AEA-27."""
    return _bound(request.app, get_identity_service, IDENTITY_SERVICE)


def get_demo_service(request: Request) -> Any:
    """DemoService (cases.md section 6), bound by AEA-30."""
    return _bound(request.app, get_demo_service, DEMO_SERVICE)


def get_reset_service(request: Request) -> Any:
    """ResetService (cases.md section 7), bound by AEA-31."""
    return _bound(request.app, get_reset_service, RESET_SERVICE)


def get_reset_gate(request: Request) -> ResetGate:
    return _bound(request.app, get_reset_gate, RESET_GATE)


def get_live_chat(request: Request) -> Any:
    """LiveChatService (staff.md section 5), bound by AEA-46."""
    return _bound(request.app, get_live_chat, LIVE_CHAT)


def get_metrics_reads(request: Request) -> MetricsReads:
    return _bound(request.app, get_metrics_reads, METRICS_READS)


def get_uow_factory(request: Request) -> UnitOfWorkFactory:
    return _bound(request.app, get_uow_factory, UOW_FACTORY)


def get_stream_poll_limiter(request: Request) -> anyio.CapacityLimiter:
    return _bound(request.app, get_stream_poll_limiter, STREAM_POLL_LIMITER)


def get_rate_limiter(request: Request) -> RateLimiter:
    return _bound(request.app, get_rate_limiter, RATE_LIMITER)


def get_wall_clock(request: Request) -> Callable[[], datetime]:
    """The one wall clock the container passes to every service (MC-20); a test may have replaced it (D-13)."""
    return _bound(request.app, get_wall_clock, WALL_CLOCK)


def get_heartbeat(request: Request) -> HeartbeatReader:
    return _bound(request.app, get_heartbeat, HEARTBEAT)


# Keys behind the providers the middleware resolves through `provided` (it has an app, not a request).
PROVIDER_KEYS: Mapping[Callable[..., Any], Key[Any]] = MappingProxyType(
    {
        get_login_sessions: LOGIN_SESSIONS,
        get_staff_access: STAFF_ACCESS,
        get_flag_service: FLAG_SERVICE,
        get_session_service: SESSION_SERVICE,
        get_turn_service: TURN_SERVICE,
        get_person_requests: PERSON_REQUESTS,
        get_handoff_service: HANDOFF_SERVICE,
        get_case_service: CASE_SERVICE,
        get_reply_composer: REPLY_COMPOSER,
        get_identity_service: IDENTITY_SERVICE,
        get_demo_service: DEMO_SERVICE,
        get_reset_service: RESET_SERVICE,
        get_reset_gate: RESET_GATE,
        get_live_chat: LIVE_CHAT,
        get_metrics_reads: METRICS_READS,
        get_uow_factory: UOW_FACTORY,
        get_stream_poll_limiter: STREAM_POLL_LIMITER,
        get_rate_limiter: RATE_LIMITER,
        get_wall_clock: WALL_CLOCK,
        get_heartbeat: HEARTBEAT,
    }
)


def provided[T](app: Starlette, provider: Callable[..., T]) -> T:
    """Resolve a provider outside a request: the override (a zero-argument callable) when one is set, else the container."""
    overrides: Mapping[Callable[..., Any], Callable[..., Any]] = getattr(app, "dependency_overrides", {})
    override = overrides.get(provider)
    if override is not None:
        return cast(T, override())
    return cast(T, _bound(app, provider, PROVIDER_KEYS[provider]))


def wall_now(app: Starlette) -> datetime:
    return provided(app, get_wall_clock)()


def get_request_context(request: Request) -> RequestContext:
    context = getattr(request.state, "request_context", None)
    if not isinstance(context, RequestContext):
        raise RuntimeError("request context missing: GateMiddleware not installed")
    return context


def get_login_session(context: RequestContext = Depends(get_request_context)) -> LoginSession:  # noqa: B008
    if context.session is None:  # defence: a public route asking for a session
        raise ApiProblem(401, ApiErrorCode.UNAUTHENTICATED, details={"reason": "none"})
    return context.session


def get_settings(request: Request) -> Settings:
    shell_settings: Settings = request.app.state.web_shell.settings
    return shell_settings


def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]:
    """Allow the given staff roles; refuse the rest with 403 ROLE_NOT_ALLOWED naming this request's role (MC-4)."""
    needs = tuple(roles)

    def dependency(
        session: LoginSession = Depends(get_login_session),  # noqa: B008
        access: StaffAccess = Depends(get_staff_access),  # noqa: B008
    ) -> StaffActor:
        result = access.actor_for(session, needs)
        if isinstance(result, RoleRefusal):
            raise ApiProblem(
                403,
                ApiErrorCode.ROLE_NOT_ALLOWED,
                details={
                    "role": result.role.value,
                    "needs": [role.value for role in result.needs],
                    "reason": result.reason,
                },
            )
        return result

    dependency.__name__ = "require_staff_" + "_".join(role.value for role in needs)
    return dependency


# -- thread ownership -------------------------------------------------------------------------------------
class _ConversationsLookup(Protocol):
    def lookup(self, thread_id: str) -> object: ...


class _CoreWithConversations(Protocol):
    conversations: _ConversationsLookup


@runtime_checkable
class _EndedThreadLike(Protocol):
    demo_session: str
    reason: str


@runtime_checkable
class _ConversationLike(Protocol):
    demo_session: str


def _not_found() -> ApiProblem:
    return ApiProblem(404, ApiErrorCode.SESSION_NOT_FOUND)


def _owned(thread_id: str, session: LoginSession, uow: UnitOfWorkFactory, *, ended_as_404: bool) -> ThreadId:
    if re.fullmatch(ThreadId.PATTERN, thread_id) is None:
        raise _not_found()
    with uow() as tx:  # one read-only unit of work, one lookup
        found = cast(_CoreWithConversations, tx.core).conversations.lookup(thread_id)
    mine = str(session.session_id)
    if isinstance(found, _EndedThreadLike):  # first: a ConversationRow has no `reason`
        if found.demo_session == mine and not ended_as_404:
            raise ApiProblem(410, ApiErrorCode.SESSION_ENDED, details={"reason": found.reason})
        raise _not_found()
    if isinstance(found, _ConversationLike) and found.demo_session == mine:
        return ThreadId(thread_id)
    raise _not_found()


def owned_thread(
    thread_id: str,
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
) -> ThreadId:
    """This session's live thread; 410 for its ended one; the identical 404 for anything else (WEB-34, MC-16)."""
    return _owned(thread_id, session, uow, ended_as_404=False)


def owned_stream_thread(
    thread_id: str,
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
) -> ThreadId:
    """As owned_thread, but the stream documents no 410, so an ended thread is the identical 404 (R-W-3)."""
    return _owned(thread_id, session, uow, ended_as_404=True)
