"""The one gate in front of every route (web.md sections 4 to 6).

Pure ASGI, async, no worker thread. In order: request id, reset gate, session, rate limits, eval tag, route, `request`
log record. Nothing but the registered public paths runs without a session. Also holds the rate limiter, the public
path registry, the cookie helpers and the pure helpers the gate and the tests share.
"""

from __future__ import annotations

import collections
import hmac
import math
import re
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal
from urllib.parse import quote, urlencode

from fastapi.responses import RedirectResponse
from fastapi.routing import iter_route_contexts
from pydantic import SecretStr
from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from meridian.config import Settings
from meridian.domain.common import ApiErrorCode, RequestId, ThreadId
from meridian.domain.staff import LoginSession, SessionExpired
from meridian.policy.limits import WebLimits
from meridian.services.reset_gate import ResetGate
from meridian.web.errors import REQUEST_ID_HEADER, ApiProblem, render_api_problem, render_unhandled_error
from meridian.web.logging import REQUEST_LOGGER, emit_record, request_record

if TYPE_CHECKING:
    from starlette.applications import Starlette

    from meridian.web.deps import LoginSessions

EVAL_KEY_HEADER = "X-Meridian-Eval-Key"
RUN_ID_HEADER = "X-Meridian-Run-Id"
RUN_TAG_HEADER = "X-Meridian-Run-Tag"
SESSION_COOKIE = "mhc_session"
HEALTHZ_PATH = "/healthz"
SUBMIT_TURN_OPERATION = "submitTurn"
UNMATCHED_ROUTE = "<unmatched>"
RESET_RETRY_AFTER_MS = 5000

OPERATIONS_BY_ROUTE: Mapping[tuple[str, str], str] = MappingProxyType(
    {
        ("POST", "/api/chat/sessions"): "startChatSession",
        ("GET", "/api/chat/sessions/{thread_id}"): "getChatThread",
        ("POST", "/api/chat/sessions/{thread_id}/turns"): "submitTurn",
        ("GET", "/api/chat/sessions/{thread_id}/events"): "streamChatEvents",
        ("POST", "/api/chat/sessions/{thread_id}/handoff"): "requestPerson",
        ("PUT", "/api/chat/sessions/{thread_id}/follow-up"): "saveFollowUp",
        ("GET", "/api/demo/inbox"): "listDemoInbox",
        ("GET", "/api/demo/staffing"): "getStaffing",
        ("PUT", "/api/demo/staffing"): "setStaffing",
        ("GET", "/api/demo/clock"): "getDemoClock",
        ("POST", "/api/demo/clock"): "advanceDemoClock",
        ("POST", "/api/demo/reset"): "resetDemo",
        ("GET", "/api/staff/queue"): "getQueue",
        ("GET", "/api/staff/cases/{reference}"): "getCase",
        ("POST", "/api/staff/cases/{reference}/actions"): "applyCaseAction",
        ("POST", "/api/staff/cases/{reference}/live"): "liveChatAction",
        ("GET", "/api/staff/cases/{reference}/events"): "streamCaseEvents",
        ("POST", "/api/staff/cases/{reference}/activities"): "recordContactActivity",
        ("POST", "/api/staff/flags"): "createFlag",
        ("GET", "/api/staff/flags"): "listFlags",
        ("PATCH", "/api/staff/flags/{flag_id}"): "reviewFlag",
        ("GET", "/api/staff/oversight"): "getOversight",
        ("GET", "/api/staff/owner-metrics"): "getOwnerMetrics",
        ("GET", "/api/monitoring"): "getMonitoring",
        ("GET", "/api/eval/latest"): "getLatestEval",
        ("POST", "/api/login"): "login",
        ("POST", "/api/logout"): "logout",
        ("GET", "/api/session"): "getSession",
        ("GET", "/api/session/roles"): "listDemoRoles",
        ("PUT", "/api/session/role"): "switchRole",
    }
)
RATE_LIMITED_READ_OPERATIONS: frozenset[str] = frozenset(
    {"startChatSession", "listDemoInbox", "getStaffing", "getDemoClock", "getMonitoring", "getLatestEval"}
)
RESET_503_OPERATIONS: frozenset[str] = frozenset(
    {
        "startChatSession",
        "submitTurn",
        "listDemoInbox",
        "setStaffing",
        "advanceDemoClock",
        "switchRole",
        "getMonitoring",
        "getLatestEval",
    }
)
# resetDemo answers its own 409 RESET_IN_PROGRESS through ResetAlreadyRunning; waiting would run a second reset.
RESET_NO_WAIT_OPERATIONS: frozenset[str] = frozenset(
    {"login", "resetDemo", "streamChatEvents", "streamCaseEvents"}
)


# -- rate limiter ---------------------------------------------------------------------------------------------
class LimitScope(StrEnum):
    THREAD = "thread"
    SESSION = "session"
    IP = "ip"
    LOGIN_IP = "login_ip"
    RESET_IP = "reset_ip"


@dataclass(frozen=True)
class LimitVerdict:
    allowed: bool
    scope: LimitScope | None
    retry_after_ms: int | None


ALLOWED = LimitVerdict(allowed=True, scope=None, retry_after_ms=None)
_SWEEP_EVERY_S = 60.0
_BUCKET_IDLE_S = 120.0  # 2 x the 60 s per-minute window
_WINDOW_SCOPES = (LimitScope.LOGIN_IP, LimitScope.RESET_IP)


class RateLimiter:
    """In-process limits: token buckets per minute, sliding logs for the login and reset windows."""

    def __init__(self, limits: WebLimits) -> None:
        self._limits = limits
        self._lock = threading.Lock()  # the middleware runs on the loop, the login route in a worker thread
        self._buckets: dict[tuple[str, str, str], list[float]] = {}  # [tokens, last_ts]
        self._logs: dict[tuple[str, str], collections.deque[float]] = {}
        self._last_sweep = 0.0

    def _capacity(self, scope: LimitScope, family: str) -> int:
        w = self._limits
        if scope is LimitScope.THREAD:
            return w.chat_turns_per_thread_per_min
        if family == "turn":
            return (
                w.chat_turns_per_session_per_min
                if scope is LimitScope.SESSION
                else w.chat_turns_per_ip_per_min
            )
        return w.reads_per_session_per_min if scope is LimitScope.SESSION else w.reads_per_ip_per_min

    def _window(self, scope: LimitScope) -> tuple[int, int]:
        w = self._limits
        if scope is LimitScope.LOGIN_IP:
            return w.login_rejects_per_ip, w.login_reject_window_s
        return w.resets_per_ip, w.reset_window_s

    def _sweep(self, now: float) -> None:
        if now - self._last_sweep < _SWEEP_EVERY_S:
            return
        self._last_sweep = now
        for key in [k for k, (_, last) in self._buckets.items() if now - last > _BUCKET_IDLE_S]:
            del self._buckets[key]
        for log_key in list(self._logs):
            log = self._logs[log_key]
            window = self._window(LimitScope(log_key[0]))[1]
            if not log or log[-1] < now - 2 * window:
                del self._logs[log_key]

    def _peek(self, scope: LimitScope, key: str, now: float, family: str) -> LimitVerdict:
        if scope in _WINDOW_SCOPES:
            allowed_count, window = self._window(scope)
            log = self._logs.get((scope.value, key))
            if log is not None:
                while log and log[0] <= now - window:
                    log.popleft()
            if log is None or len(log) < allowed_count:
                return ALLOWED
            wait_s = max(1, math.ceil(log[0] + window - now))
            return LimitVerdict(False, scope, wait_s * 1000)
        fam = "turn" if scope is LimitScope.THREAD else family
        capacity = self._capacity(scope, fam)
        rate = capacity / 60.0
        bucket = self._buckets.get((fam, scope.value, key))
        tokens = capacity if bucket is None else min(capacity, bucket[0] + (now - bucket[1]) * rate)
        if tokens >= 1:
            return ALLOWED
        wait_s = max(1, math.ceil((1 - tokens) / rate))
        return LimitVerdict(False, scope, wait_s * 1000)

    def peek(
        self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read"
    ) -> LimitVerdict:
        with self._lock:
            self._sweep(now)
            return self._peek(scope, key, now, family)

    def check(
        self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read"
    ) -> LimitVerdict:
        with self._lock:
            self._sweep(now)
            verdict = self._peek(scope, key, now, family)
            if verdict.allowed:
                self._consume(scope, key, now, family)
            return verdict

    def _consume(self, scope: LimitScope, key: str, now: float, family: str) -> None:
        if scope in _WINDOW_SCOPES:
            self._log_for(scope, key).append(now)
            return
        fam = "turn" if scope is LimitScope.THREAD else family
        capacity = self._capacity(scope, fam)
        bucket = self._buckets.get((fam, scope.value, key))
        tokens = (
            capacity if bucket is None else min(capacity, bucket[0] + (now - bucket[1]) * capacity / 60.0)
        )
        self._buckets[(fam, scope.value, key)] = [tokens - 1, now]

    def _log_for(self, scope: LimitScope, key: str) -> collections.deque[float]:
        log = self._logs.get((scope.value, key))
        if log is None:
            log = collections.deque(maxlen=self._window(scope)[0])
            self._logs[(scope.value, key)] = log
        return log

    def record_login_reject(self, ip: str, now: float) -> None:
        with self._lock:
            self._sweep(now)
            self._log_for(LimitScope.LOGIN_IP, ip).append(now)

    def record_reset(self, ip: str, now: float) -> None:
        with self._lock:
            self._sweep(now)
            self._log_for(LimitScope.RESET_IP, ip).append(now)

    def bucket_keys(self) -> frozenset[tuple[str, str, str]]:
        with self._lock:
            return frozenset(self._buckets) | frozenset(("window", s, k) for (s, k) in self._logs)


def limit_verdict(
    limiter: RateLimiter,
    operation_id: str,
    *,
    thread_id: str,
    session_id: str,
    ip: str,
    now: float,
) -> LimitVerdict | None:
    """Web section 5: the six read operations (SESSION then IP) and submitTurn (THREAD, SESSION, IP). None = never limited."""
    checks: list[tuple[LimitScope, str, Literal["turn", "read"]]]
    if operation_id in RATE_LIMITED_READ_OPERATIONS:
        checks = [(LimitScope.SESSION, session_id, "read"), (LimitScope.IP, ip, "read")]
    elif operation_id == SUBMIT_TURN_OPERATION:
        checks = [
            (LimitScope.THREAD, thread_id, "turn"),
            (LimitScope.SESSION, session_id, "turn"),
            (LimitScope.IP, ip, "turn"),
        ]
    else:
        return None
    for scope, key, family in checks:
        verdict = limiter.peek(scope, key, now, family=family)
        if not verdict.allowed:
            return verdict
    for scope, key, family in checks:
        limiter.check(scope, key, now, family=family)
    return ALLOWED


# -- context, public paths, shell state ----------------------------------------------------------------------
@dataclass(frozen=True)
class RequestContext:
    request_id: RequestId
    client_ip: str
    session: LoginSession | None
    run_tag: Literal["live", "eval", "load"]
    run_id: str | None
    turn_verdict: LimitVerdict | None


class PublicPaths:
    """Paths that answer without a session. AEA-23 registers two; AEA-49 adds the page and asset paths."""

    def __init__(self) -> None:
        self._entries: set[tuple[str, str, str]] = set()

    def add_exact(self, method: str, path: str) -> None:
        self._entries.add(("exact", method.upper(), path))

    def add_prefix(self, method: str, prefix: str) -> None:
        self._entries.add(("prefix", method.upper(), prefix))

    def is_public(self, method: str, path: str) -> bool:
        verb = method.upper()
        for kind, entry_method, entry_path in self._entries:
            if entry_method != verb:
                continue
            if (kind == "exact" and path == entry_path) or (kind == "prefix" and path.startswith(entry_path)):
                return True
        return False

    def entries(self) -> frozenset[tuple[str, str, str]]:
        return frozenset(self._entries)


@dataclass(frozen=True)
class WebShellState:
    """app.state.web_shell, set by create_app."""

    settings: Settings
    wall_clock: Callable[[], datetime]
    public_paths: PublicPaths


@dataclass(frozen=True)
class GateBindings:
    """How the middleware reaches web/deps.py (resolved per request, so dependency overrides apply)."""

    login_sessions: Callable[[Starlette], LoginSessions]
    rate_limiter: Callable[[Starlette], RateLimiter]
    reset_gate: Callable[[Starlette], ResetGate]
    wall_clock: Callable[[Starlette], Callable[[], datetime]]


# -- pure helpers -----------------------------------------------------------------------------------------
def session_cookie(token: str, *, max_age: int, secure: bool) -> str:
    """Set-Cookie value, built by hand: Starlette's set_cookie would write SameSite=lax."""
    value = f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"
    return value + "; Secure" if secure else value


def cleared_session_cookie(*, secure: bool) -> str:
    return session_cookie("", max_age=0, secure=secure)


def safe_return_to(target: str) -> str | None:
    """WEB-28: only a same-origin path. No scheme, no protocol-relative form, no backslash or control character."""
    if not target.startswith("/") or target.startswith("//") or target.startswith("/\\"):
        return None
    if "\\" in target or "://" in target or any(ord(c) < 0x20 or ord(c) == 0x7F for c in target):
        return None
    return target


def client_ip_of(scope: Scope, *, trust_proxy_headers: bool) -> str:
    """The last X-Forwarded-For entry when trusted, else the socket peer. [A: confirm Railway's header at AEA-56]"""
    if trust_proxy_headers:
        forwarded = Headers(scope=scope).get("x-forwarded-for")
        if forwarded:
            last = forwarded.split(",")[-1].strip()
            if last:
                return last
    client = scope.get("client")
    return str(client[0]) if client else "unknown"


def run_tag_of(
    headers: Headers, eval_key: SecretStr | None
) -> tuple[Literal["live", "eval", "load"], str | None]:
    """WEB-7: the run tag and run id count only when the eval key matches."""
    supplied = headers.get(EVAL_KEY_HEADER)
    if supplied is None or eval_key is None:
        return "live", None
    if not hmac.compare_digest(supplied.encode("utf-8"), eval_key.get_secret_value().encode("utf-8")):
        return "live", None
    tag = headers.get(RUN_TAG_HEADER)
    return ("load" if tag == "load" else "eval"), headers.get(RUN_ID_HEADER)


# -- the gate ---------------------------------------------------------------------------------------------
class GateMiddleware:
    def __init__(self, app: ASGIApp, *, bindings: GateBindings) -> None:
        self.app = app
        self._b = bindings

    @staticmethod
    def _match(app: Starlette, scope: Scope) -> tuple[str, dict[str, object]]:
        """The matched route's template and path params, with no side effects."""
        partial: tuple[str, dict[str, object]] | None = None
        for context in iter_route_contexts(app.router.routes):
            matches = getattr(context, "matches", None)
            if matches is None:
                continue
            match, child = matches(scope)
            template = context.path or UNMATCHED_ROUTE
            if match is Match.FULL:
                return template, dict(child.get("path_params", {}))
            if match is Match.PARTIAL and partial is None:
                partial = (template, dict(child.get("path_params", {})))
        return partial if partial is not None else (UNMATCHED_ROUTE, {})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        app: Starlette = scope["app"]
        shell: WebShellState = app.state.web_shell
        state: dict[str, object] = scope.setdefault("state", {})
        start = time.perf_counter()

        request_id = str(uuid.uuid4())
        state["request_id"] = request_id
        status = 500
        started = False
        pending_cookies: list[str] = []

        async def send_wrapper(message: Message) -> None:
            nonlocal status, started
            if message["type"] == "http.response.start":
                status = message["status"]
                started = True
                headers = MutableHeaders(scope=message)
                headers[REQUEST_ID_HEADER] = request_id
                for cookie in pending_cookies:
                    headers.append("set-cookie", cookie)
            await send(message)

        template, path_params = self._match(app, scope)
        method = scope["method"]
        path = scope["path"]
        operation_id = OPERATIONS_BY_ROUTE.get((method, template))
        raw_thread = path_params.get("thread_id")
        thread_id = (
            raw_thread if isinstance(raw_thread, str) and re.fullmatch(ThreadId.PATTERN, raw_thread) else None
        )
        session: LoginSession | None = None
        error_kind: str | None = None
        ip = client_ip_of(scope, trust_proxy_headers=shell.settings.trust_proxy_headers)

        async def respond(response: Response) -> None:
            await response(scope, receive, send_wrapper)

        try:
            # 3. reset gate
            gate = self._b.reset_gate(app)
            if gate.held():
                if operation_id in RESET_503_OPERATIONS:
                    error_kind = ApiErrorCode.RESET_IN_PROGRESS.value
                    problem = ApiProblem(
                        503,
                        ApiErrorCode.RESET_IN_PROGRESS,
                        details={"retry_after_ms": RESET_RETRY_AFTER_MS},
                    )
                    await respond(render_api_problem(problem, request_id))
                    return
                if operation_id not in RESET_NO_WAIT_OPERATIONS and path != HEALTHZ_PATH:
                    wait_s = app.state.container.limits.web.reset_wait_s
                    await gate.wait_clear(wait_s)

            # 4. session
            now: datetime | None = None
            if not shell.public_paths.is_public(method, path):
                now = self._b.wall_clock(
                    app
                )()  # the only wall-clock reading in the middleware for this request
                token = Request(scope).cookies.get(SESSION_COOKIE, "")
                result = self._b.login_sessions(app).resolve(SecretStr(token), now)
                if isinstance(result, LoginSession):
                    session = result
                else:
                    reason = "expired" if isinstance(result, SessionExpired) else "none"
                    if isinstance(result, SessionExpired):
                        pending_cookies.append(cleared_session_cookie(secure=shell.settings.cookie_secure))
                    if path == "/api" or path.startswith("/api/") or method != "GET":
                        problem = ApiProblem(401, ApiErrorCode.UNAUTHENTICATED, details={"reason": reason})
                        await respond(render_api_problem(problem, request_id))
                    else:
                        query = scope.get("query_string", b"")
                        target = path + ("?" + query.decode("latin-1") if query else "")
                        safe = safe_return_to(target)
                        params = {"return_to": safe, "reason": reason} if safe else {"reason": reason}
                        location = "/login?" + urlencode(params, quote_via=quote)
                        await respond(RedirectResponse(location, status_code=303))
                    return

            # 5. rate limits
            turn_verdict: LimitVerdict | None = None
            if session is not None and operation_id is not None and now is not None:
                verdict = limit_verdict(
                    self._b.rate_limiter(app),
                    operation_id,
                    thread_id=thread_id or "",
                    session_id=str(session.session_id),
                    ip=ip,
                    now=now.timestamp(),
                )
                if verdict is not None and not verdict.allowed:
                    if operation_id in RATE_LIMITED_READ_OPERATIONS:
                        problem = ApiProblem(
                            429,
                            ApiErrorCode.REQUEST_RATE_LIMITED,
                            details={"retry_after_ms": verdict.retry_after_ms},
                        )
                        await respond(render_api_problem(problem, request_id))
                        return
                if operation_id == SUBMIT_TURN_OPERATION:
                    turn_verdict = verdict

            # 6. eval tag, 7. context
            run_tag, run_id = run_tag_of(Headers(scope=scope), shell.settings.eval_key)
            state["request_context"] = RequestContext(
                request_id=RequestId(request_id),
                client_ip=ip,
                session=session,
                run_tag=run_tag,
                run_id=run_id,
                turn_verdict=turn_verdict,
            )

            # 8. the route
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:  # an unhandled error still answers with X-Request-ID and counts as a 5xx
            error_kind = type(exc).__name__
            if started:
                raise
            await respond(render_unhandled_error(request_id))
        finally:
            recorded_kind = state.get("error_kind")
            emit_record(
                REQUEST_LOGGER,
                request_record(
                    request_id=request_id,
                    route=template,
                    status=status,
                    duration_ms=int((time.perf_counter() - start) * 1000),
                    caller_role=session.role.value if session else "anonymous",
                    thread_id=thread_id,
                    error_kind=error_kind
                    or (recorded_kind if isinstance(recorded_kind, str) else None)
                    or (f"http_{status}" if status >= 500 else None),
                ),
            )
