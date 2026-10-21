"""AEA-23 shared test support: doubles, app builders and small helpers (frozen with the AEA-23 tests).

Not a conftest. Other route tickets may import this module read-only. Everything here is synthetic and built at
run time: no `.env`, no real secret, no paid call, no socket. Distinctive "must be absent" values are letters only,
so no test value can look like a verification code, a card number or a phone number.

The doubles stand in for AEA-44's StaffSessionStore (login sessions and staff access), AEA-32's heartbeat and
AEA-10's unit of work, which are same-wave siblings of AEA-23 and not built yet.
"""

from __future__ import annotations

import io
import json
import logging
import secrets
import string
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.routing import iter_route_contexts
from fastapi.testclient import TestClient
from pydantic import SecretStr

import meridian.web.app as app_module
from meridian.config import Settings
from meridian.domain.staff import (
    DemoRole,
    IssuedSession,
    LoginSession,
    LoginSessionId,
    RoleRefusal,
    SessionExpired,
    SessionInfoData,
    SessionMissing,
    StaffActor,
    StaffRole,
)
from meridian.domain.staff import actor_for as staff_actor_for
from meridian.policy.limits import Limits
from meridian.services.reset_gate import ResetGate
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.container import Container, register_web
from meridian.web.deps import (
    RESET_GATE,
    get_heartbeat,
    get_login_sessions,
    get_rate_limiter,
    get_request_context,
    get_staff_access,
    get_uow_factory,
)
from meridian.web.logging import AllowListFormatter
from meridian.web.middleware import RateLimiter, RequestContext
from tests.api.openapi_check import assert_response_matches, load_contract

SESSION_COOKIE_NAME = "mhc_session"
FIXED_SIGNED_IN_AT = datetime(2026, 10, 16, 14, 0, tzinfo=timezone(timedelta(hours=-5)))
SEES = ("Chat", "Demo guide", "Demo inbox", "Monitoring", "Evaluation")


def rand_word(length: int = 16, prefix: str = "zq") -> str:
    """A distinctive letters-only value (never digits, so never code-, card- or phone-like)."""
    return prefix + "".join(secrets.choice(string.ascii_lowercase) for _ in range(length))


def new_thread_id() -> str:
    return str(uuid.uuid4())


def make_settings(tmp_path: Path, **changes: Any) -> Settings:
    """Settings with generated, per-test secrets. Nothing is read from the environment or a file."""
    base: dict[str, Any] = {
        "anthropic_api_key": rand_word(20, "ak"),
        "openrouter_api_key": rand_word(20, "ok"),
        "demo_username": rand_word(10, "user"),
        "demo_password": rand_word(14, "pw"),
        "session_secret": rand_word(24, "ss"),
        "data_dir": tmp_path / "data",
        "index_dir": tmp_path / "index",
        "web_dist_dir": tmp_path / "no-dist",
        "require_frontend": False,
    }
    base.update(changes)
    return Settings.model_validate(base)


def demo_pair(settings: Settings) -> dict[str, str]:
    return {
        "username": settings.demo_username.get_secret_value(),
        "password": settings.demo_password.get_secret_value(),
    }


class MutableClock:
    """A wall clock a test can move. Counts its reads."""

    def __init__(self, start: datetime) -> None:
        self._now = start
        self.reads = 0

    def __call__(self) -> datetime:
        self.reads += 1
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + timedelta(seconds=seconds)


class SequenceClock:
    """Returns the given times in order, then the last one forever. Records every value it returned."""

    def __init__(self, times: Sequence[datetime]) -> None:
        self._times = list(times)
        self.returned: list[datetime] = []

    def __call__(self) -> datetime:
        index = min(len(self.returned), len(self._times) - 1)
        value = self._times[index]
        self.returned.append(value)
        return value


class FakeSessionStore:
    """Implements both LoginSessions and StaffAccess, like AEA-44's real store.

    `calls` records (method, now-or-None) for start, resolve and end only. `issue` mints a live token without a login.
    """

    def __init__(
        self,
        *,
        lifetime_s: int = 43_200,
        end_invalidates: bool = True,
        fail_on_start: bool = False,
    ) -> None:
        self.lifetime_s = lifetime_s
        self.end_invalidates = end_invalidates
        self.fail_on_start = fail_on_start
        self.calls: list[tuple[str, datetime | None]] = []
        self.ended_tokens: list[str] = []
        self.issued_tokens: list[str] = []
        self._sessions: dict[str, LoginSession] = {}
        self._expired: set[str] = set()

    def _mint(self, now: datetime, role: DemoRole, role_reset: bool) -> tuple[str, LoginSession]:
        token = rand_word(40, "tok")
        session = LoginSession(
            session_id=LoginSessionId(str(uuid.uuid4())),
            role=role,
            role_reset=role_reset,
            signed_in_at=FIXED_SIGNED_IN_AT,
            expires_at=now + timedelta(seconds=self.lifetime_s),
        )
        self._sessions[token] = session
        self.issued_tokens.append(token)
        return token, session

    # -- test helpers (not part of the ports) ---------------------------------------------------------------
    def issue(self, role: DemoRole = DemoRole.CUSTOMER, *, now: datetime | None = None) -> str:
        token, _ = self._mint(now if now is not None else datetime.now(UTC), role, False)
        return token

    def session_of(self, token: str) -> LoginSession:
        return self._sessions[token]

    def set_role(self, token: str, role: DemoRole, *, role_reset: bool = False) -> None:
        self._sessions[token] = self._sessions[token].model_copy(
            update={"role": role, "role_reset": role_reset}
        )

    def expire(self, token: str) -> None:
        self._expired.add(token)

    def live_tokens(self) -> frozenset[str]:
        return frozenset(self._sessions)

    # -- LoginSessions ---------------------------------------------------------------------------------------
    def start(self, now: datetime) -> IssuedSession:
        self.calls.append(("start", now))
        if self.fail_on_start:
            raise RuntimeError("session store is down")
        token, session = self._mint(now, DemoRole.CUSTOMER, False)
        return IssuedSession(session=session, token=SecretStr(token))

    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired:
        self.calls.append(("resolve", now))
        raw = token.get_secret_value()
        session = self._sessions.get(raw) if raw else None
        if session is None:
            return SessionMissing()
        if raw in self._expired or now >= session.expires_at:
            return SessionExpired()
        return session

    def end(self, token: SecretStr) -> None:
        self.calls.append(("end", None))
        raw = token.get_secret_value()
        self.ended_tokens.append(raw)
        if self.end_invalidates:
            self._sessions.pop(raw, None)

    def session_info(self, session: LoginSession) -> SessionInfoData:
        return SessionInfoData(
            role=session.role,
            display_name="Customer (demo)",
            sees=SEES,
            signed_in_at=session.signed_in_at,
        )

    # -- StaffAccess -----------------------------------------------------------------------------------------
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal:
        if session.role.value in {role.value for role in needs}:
            return staff_actor_for(StaffRole(session.role.value))
        return RoleRefusal(
            role=session.role,
            needs=needs,
            reason="role_reset" if session.role_reset else "wrong_role",
        )


class FakeHeartbeat:
    """Implements HeartbeatReader. `fresh(mono)` returns `value` or raises `raises`."""

    def __init__(self, fresh: bool = True, raises: Exception | None = None) -> None:
        self.value = fresh
        self.raises = raises
        self.calls: list[float] = []

    def fresh(self, mono: float) -> bool:
        self.calls.append(mono)
        if self.raises is not None:
            raise self.raises
        return self.value


@dataclass(frozen=True)
class ConversationRowStub:
    thread_id: str
    demo_session: str
    live_state: str = "not_live"


@dataclass(frozen=True)
class EndedThreadStub:
    thread_id: str
    demo_session: str
    ended_wall_at: str
    reason: str
    reset_id: str | None = None


class FakeUow:
    """A UnitOfWorkFactory double: `core.conversations.lookup(thread_id)` from a dict, with a lookup record.

    `raise_on_use=True` raises as soon as the factory is called (used to prove /healthz never touches storage).
    """

    def __init__(self, rows: Mapping[str, object] | None = None, *, raise_on_use: bool = False) -> None:
        self.rows: dict[str, object] = dict(rows or {})
        self.raise_on_use = raise_on_use
        self.calls = 0
        self.lookups: list[str] = []

    def _lookup(self, thread_id: str) -> object:
        self.lookups.append(thread_id)
        return self.rows.get(thread_id)

    @contextmanager
    def _transaction(self) -> Iterator[Any]:
        conversations = type("Conversations", (), {"lookup": staticmethod(self._lookup)})()
        core = type("Core", (), {"conversations": conversations})()
        yield type("Tx", (), {"core": core})()

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Any:
        self.calls += 1
        if self.raise_on_use:
            raise RuntimeError("the unit of work must not be used here")
        return self._transaction()


class RecordingTraceSink:
    """Implements TraceSink's four methods and keeps a repr of every argument it ever saw."""

    def __init__(self) -> None:
        self.seen: list[str] = []

    def turn(self, ids: Any) -> Any:
        self.seen.append(repr(ids))
        from contextlib import nullcontext

        return nullcontext(None)

    def model_call(self, parent: Any, record: Any, masked_input: str, masked_output: str) -> None:
        self.seen.extend([repr(parent), repr(record), masked_input, masked_output])

    def node(self, parent: Any, name: str, elapsed_ms: int, status: str) -> None:
        self.seen.extend([repr(parent), name, str(elapsed_ms), status])

    def export_status(self, turn: Any) -> Any:
        self.seen.append(repr(turn))
        return None


# -- logging capture ---------------------------------------------------------------------------------------------
@contextmanager
def captured_log() -> Iterator[io.StringIO]:
    """Capture the "meridian" logger tree through the allow-list formatter, one JSON object per line."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(AllowListFormatter())
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger("meridian")
    old_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


def log_records(stream: io.StringIO) -> list[dict[str, Any]]:
    return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]


def records_of(stream: io.StringIO, kind: str) -> list[dict[str, Any]]:
    return [record for record in log_records(stream) if record.get("record") == kind]


# -- app builders ----------------------------------------------------------------------------------------------
@dataclass
class BuilderSpy:
    """What the lifespan asked the container builder for, and how often it was built and closed."""

    calls: list[dict[str, Any]] = field(default_factory=list)
    built: int = 0
    closed: int = 0

    def note_closed(self) -> None:
        self.closed += 1


def install_builder_spy(monkeypatch: pytest.MonkeyPatch) -> BuilderSpy:
    """Replace `meridian.web.app.build_container` with a builder that runs only AEA-23's `register_web` hunk."""
    spy = BuilderSpy()

    def build(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container:
        spy.calls.append({"app": app, "settings": settings, "overrides": overrides})
        limits = Limits()
        container = Container(settings=settings, limits=limits)
        register_web(container, app, settings=settings, limits=limits)
        container.on_close(spy.note_closed)
        container.build()
        spy.built += 1
        return container

    monkeypatch.setattr(app_module, "build_container", build)
    return spy


def _install_doubles(
    app: FastAPI,
    *,
    store: FakeSessionStore,
    heartbeat: FakeHeartbeat,
    uow: FakeUow | None,
    limiter: RateLimiter | None,
) -> None:
    app.dependency_overrides[get_login_sessions] = lambda: store
    app.dependency_overrides[get_staff_access] = lambda: store
    app.dependency_overrides[get_heartbeat] = lambda: heartbeat
    if uow is not None:
        app.dependency_overrides[get_uow_factory] = lambda: uow
    if limiter is not None:
        app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.state.test_store = store
    app.state.test_heartbeat = heartbeat


def web_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    *,
    overrides: ContainerOverrides | None = None,
    store: FakeSessionStore | None = None,
    heartbeat: FakeHeartbeat | None = None,
    uow: FakeUow | None = None,
    limiter: RateLimiter | None = None,
) -> FastAPI:
    """`create_app` over a container that runs only `register_web`; the store, heartbeat, unit of work and limiter
    are dependency overrides (zero-argument lambdas). The spy is on `app.state.test_spy`."""
    spy = install_builder_spy(monkeypatch)
    app = create_app(settings, overrides=overrides)
    _install_doubles(
        app,
        store=store if store is not None else FakeSessionStore(),
        heartbeat=heartbeat if heartbeat is not None else FakeHeartbeat(),
        uow=uow,
        limiter=limiter,
    )
    app.state.test_spy = spy
    return app


def suppress_container_starters(monkeypatch: pytest.MonkeyPatch) -> None:
    """No background thread or watchdog starts in tests."""
    monkeypatch.setattr(Container, "on_start", lambda self, starter: None)


def full_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    *,
    store: FakeSessionStore,
    heartbeat: FakeHeartbeat,
    overrides: ContainerOverrides | None = None,
) -> FastAPI:
    """`create_app` over the REAL `build_container` (every hunk), starters suppressed, store and heartbeat overridden."""
    suppress_container_starters(monkeypatch)
    app = create_app(settings, overrides=overrides)
    _install_doubles(app, store=store, heartbeat=heartbeat, uow=None, limiter=None)
    return app


def make_client(app: FastAPI, *, peer: str = "198.51.100.7") -> TestClient:
    """Use as a context manager so the lifespan runs. Redirects are not followed; a server error is a response."""
    return TestClient(app, client=(peer, 50000), follow_redirects=False, raise_server_exceptions=False)


def reset_gate_of(app: FastAPI) -> ResetGate:
    gate: ResetGate = app.state.container.get(RESET_GATE)
    return gate


def request_for(app: FastAPI) -> Request:
    """A bare request on `app`, for calling providers directly."""
    scope: dict[str, Any] = {
        "type": "http",
        "app": app,
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
    }
    return Request(scope)


# -- probe and test routes ---------------------------------------------------------------------------------------
def probe_endpoint(ctx: RequestContext = Depends(get_request_context)) -> dict[str, Any]:  # noqa: B008
    verdict = ctx.turn_verdict
    return {
        "run_tag": ctx.run_tag,
        "run_id": ctx.run_id,
        "client_ip": ctx.client_ip,
        "turn_verdict": None
        if verdict is None
        else {
            "allowed": verdict.allowed,
            "scope": verdict.scope.value if verdict.scope is not None else None,
            "retry_after_ms": verdict.retry_after_ms,
        },
    }


def quiet_endpoint() -> dict[str, bool]:
    """A route body that echoes nothing from the request context."""
    return {"ok": True}


def add_probe_route(
    app: FastAPI,
    operation_id: str,
    *,
    dependencies: Sequence[Any] = (),
    endpoint: Callable[..., Any] | None = None,
) -> None:
    """Register the OpenAPI operation's real method and path with a stand-in endpoint (default: `probe_endpoint`).

    The 200 it returns is never checked against the OpenAPI.
    """
    spec = load_contract().operations[operation_id]
    app.add_api_route(
        spec.path_template,
        endpoint if endpoint is not None else probe_endpoint,
        methods=[spec.method.upper()],
        operation_id=operation_id,
        dependencies=list(dependencies),
        response_model=None,
    )


def add_test_route(app: FastAPI, method: str, path: str, endpoint: Callable[..., Any]) -> None:
    """A non-OpenAPI probe, conventionally under /api/test/."""
    app.add_api_route(path, endpoint, methods=[method.upper()], response_model=None)


# -- request helpers ---------------------------------------------------------------------------------------------
def cookie_header(token: str) -> dict[str, str]:
    return {"Cookie": f"{SESSION_COOKIE_NAME}={token}"}


def set_cookie_lines(response: Any) -> list[str]:
    return list(response.headers.get_list("set-cookie"))


def session_cookie_value(response: Any) -> str | None:
    """The token in the response's `mhc_session` Set-Cookie, or None."""
    for line in set_cookie_lines(response):
        if line.startswith(f"{SESSION_COOKIE_NAME}="):
            return line.split(";", 1)[0].split("=", 1)[1]
    return None


def cookie_attributes(line: str) -> dict[str, str | None]:
    """`mhc_session=abc; Path=/; HttpOnly` -> {"mhc_session": "abc", "path": "/", "httponly": None} (names lower-cased)."""
    attributes: dict[str, str | None] = {}
    for index, part in enumerate(line.split(";")):
        name, _, value = part.strip().partition("=")
        attributes[name if index == 0 else name.lower()] = value if "=" in part else None
    return attributes


def login(client: TestClient, settings: Settings, **kwargs: Any) -> Any:
    return client.post("/api/login", json=demo_pair(settings), **kwargs)


def error_body(response: Any, status: int, code: str) -> dict[str, Any]:
    """Assert the status and ApiError code, and that `request_id` equals the X-Request-ID header. Returns the body."""
    assert response.status_code == status, response.text
    body: dict[str, Any] = response.json()
    assert body["error"]["code"] == code, body
    assert body["request_id"] == response.headers["X-Request-ID"]
    return body


def without_request_id(response: Any) -> dict[str, Any]:
    body: dict[str, Any] = dict(response.json())
    body.pop("request_id")
    return body


def all_output_text(responses: Sequence[Any], *, skip_set_cookie: bool = False) -> str:
    """Every body and header of the given responses as one string (optionally leaving out Set-Cookie)."""
    parts: list[str] = []
    for response in responses:
        parts.append(response.text)
        for name, value in response.headers.multi_items():
            if skip_set_cookie and name.lower() == "set-cookie":
                continue
            parts.append(f"{name}: {value}")
    return "\n".join(parts)


def assert_matches(response: Any, operation_id: str) -> None:
    """`assert_response_matches` for a TestClient response (Starlette's TestClient is built on httpx2, not httpx)."""
    assert_response_matches(response, operation_id)


def app_log_text(caplog: pytest.LogCaptureFixture) -> str:
    """Everything the application's own ("meridian.*") loggers sent to pytest's capture, tracebacks included.

    The test client's own loggers (httpx2 logs each request URL) are deliberately left out: they are not the app's output.
    """
    formatter = logging.Formatter("%(name)s %(message)s")
    return "\n".join(formatter.format(r) for r in caplog.records if r.name.startswith("meridian"))


@dataclass(frozen=True)
class RouteInfo:
    path: str
    methods: frozenset[str]
    operation_id: str | None
    endpoint: Callable[..., Any] | None


def effective_routes(app: FastAPI) -> list[RouteInfo]:
    """Every route the app answers, with included routers flattened (FastAPI keeps `include_router` lazy, so
    `app.routes` alone does not list them)."""
    found: list[RouteInfo] = []
    for context in iter_route_contexts(app.routes):
        if context.path is None:
            continue
        found.append(
            RouteInfo(
                path=context.path,
                methods=frozenset(context.methods or ()) - {"HEAD", "OPTIONS"},
                operation_id=getattr(context, "operation_id", None),
                endpoint=context.endpoint,
            )
        )
    return found
