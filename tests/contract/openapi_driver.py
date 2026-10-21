"""AEA-59 server runner support: the real-app launcher, exception tap, socket guard and drive realisation.

The app is the real one (`create_app(settings)`: real middleware, login, gate, rate limiter and persistence on a
first-boot copy of the issued DB, no `dependency_overrides`). The only thing a drive can skip for is a piece another
ticket has not merged yet, and it says so with one of two reasons: `route not registered: <operationId>` or the
verbatim `not bound: <name>`. With `CONTRACT_STRICT=1` both are failures. A failure message names the operation, the
drive and the status (plus `error.code`); it never prints a response body.
"""

from __future__ import annotations

import re
import socket
import sqlite3
import sys
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NoReturn

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import meridian.web.middleware as middleware_module
from meridian.adapters.sqlite.migrate import WORKING_DB_NAME
from meridian.config import Settings
from meridian.domain.common import ThreadId
from meridian.policy.limits import WebLimits
from meridian.web.app import create_app
from meridian.web.deps import RESET_GATE, UOW_FACTORY
from meridian.web.errors import render_unhandled_error
from tests.api.events_support import append_stored, payload
from tests.api.openapi_check import assert_response_matches, assert_sse_frames_match, load_contract
from tests.api.web_shell_support import (
    cookie_header,
    demo_pair,
    effective_routes,
    make_client,
    make_settings,
    rand_word,
    session_cookie_value,
)
from tests.contract.openapi_cases import (
    MALFORMED_THREAD_ID,
    PATH_WORDS,
    PRECONDITIONS,
    SETUPS,
    Drive,
)
from tests.contract.openapi_sse import STREAM_READ_TIMEOUT_S, SseRead, as_response, read_asgi_stream
from tests.contract.openapi_variants import contract_strict, request_examples
from tests.fixtures.sqlite import ISSUED_DB, TempStore
from tests.services.person_request_support import verify_thread

GUARD_MESSAGE: Final = "AEA-59 socket guard: non-loopback connect refused"
_LOOPBACK: Final = ("127.", "::1", "localhost")


def blocked(reason: str) -> NoReturn:
    """Skip (default) or fail (CONTRACT_STRICT=1). The only two reasons passed are the ones named in the module doc."""
    if contract_strict():
        pytest.fail(reason)
    pytest.skip(reason)


def install_exception_tap(monkeypatch: pytest.MonkeyPatch) -> list[BaseException]:
    """Observe the exception behind a 500 without changing what the app answers."""
    taps: list[BaseException] = []
    original = render_unhandled_error

    def tapped(request_id: str) -> Any:
        exc = sys.exc_info()[1]
        if exc is not None:
            taps.append(exc)
        return original(request_id)

    monkeypatch.setattr(middleware_module, "render_unhandled_error", tapped)
    return taps


def _is_loopback(host: object) -> bool:
    return isinstance(host, str) and host.startswith(_LOOPBACK)


def install_socket_guard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Refuse any non-loopback connect or name lookup; record the host."""
    refused: list[str] = []
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def _check(sock: socket.socket, address: Any) -> None:
        if sock.family in (socket.AF_INET, socket.AF_INET6) and not _is_loopback(address[0]):
            refused.append(str(address[0]))
            raise ConnectionRefusedError(GUARD_MESSAGE)

    def connect(self: socket.socket, address: Any) -> None:
        _check(self, address)
        real_connect(self, address)

    def connect_ex(self: socket.socket, address: Any) -> int:
        _check(self, address)
        return real_connect_ex(self, address)

    def getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        if not _is_loopback(host) and host is not None:
            refused.append(str(host))
            raise socket.gaierror(GUARD_MESSAGE)
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    return refused


@dataclass
class AppRun:
    app: FastAPI
    client: TestClient
    settings: Settings
    registered: frozenset[tuple[str, str]]
    taps: list[BaseException]
    main_token: str | None = None
    main_thread: str | None = None
    other_thread: str | None = None
    event_ids: list[int] = field(default_factory=list)


@contextmanager
def real_app(tmp_path: Path, taps: list[BaseException]) -> Iterator[AppRun]:
    """One fresh app, data dir and first-boot DB copy per use, so resetDemo and rate limits never leak between drives."""
    settings = make_settings(tmp_path, issued_db_path=ISSUED_DB)
    app = create_app(settings)
    with make_client(app) as client:
        assert not app.dependency_overrides, "the contract runner never overrides a dependency"
        registered = frozenset((m.lower(), r.path) for r in effective_routes(app) for m in r.methods)
        yield AppRun(app, client, settings, registered, taps)


def _code_suffix(response: Any) -> str:
    try:
        body = response.json()
    except ValueError:
        return ""
    error = body.get("error") if isinstance(body, dict) else None
    code = error.get("code") if isinstance(error, dict) else None
    return f" ({code})" if isinstance(code, str) else ""


def send(
    run: AppRun,
    operation_id: str,
    *,
    path: str,
    token: str | None,
    body: Mapping[str, Any] | None,
    extra_headers: Mapping[str, str] | None = None,
) -> Any:
    spec = load_contract().operations[operation_id]
    if (spec.method, spec.path_template) not in run.registered:
        blocked(f"route not registered: {operation_id}")
    headers: dict[str, str] = dict(cookie_header(token)) if token is not None else {}
    headers.update(extra_headers or {})
    kwargs: dict[str, Any] = {}
    if body is not None:
        if "raw" in body:
            kwargs["json"] = body["raw"]
        elif "text" in body:
            kwargs["content"] = body["text"]
            headers["Content-Type"] = "application/json"
        else:
            kwargs["json"] = body["json"]
    seen = len(run.taps)
    try:
        response = run.client.request(spec.method.upper(), path, headers=headers, **kwargs)
    finally:
        run.client.cookies.clear()
    if response.status_code == 500 and len(run.taps) > seen:
        exc = run.taps[-1]
        if isinstance(exc, RuntimeError) and str(exc).startswith("not bound: "):
            blocked(str(exc))
        pytest.fail(f"{operation_id}: unhandled {type(exc).__name__} (500)")
    return response


def send_stream(
    run: AppRun,
    operation_id: str,
    *,
    path: str,
    token: str | None,
    extra_headers: Mapping[str, str] | None = None,
    timeout_s: float = STREAM_READ_TIMEOUT_S,
) -> httpx.Response:
    """`send` for an event-stream operation, read with a time bound: a stream where an error was due fails, never hangs."""
    spec = load_contract().operations[operation_id]
    if (spec.method, spec.path_template) not in run.registered:
        blocked(f"route not registered: {operation_id}")
    headers: dict[str, str] = dict(cookie_header(token)) if token is not None else {}
    headers.update(extra_headers or {})
    seen = len(run.taps)
    result = read_sse(run, path, headers, frames=1, timeout_s=timeout_s)
    if result.status == 500 and len(run.taps) > seen:
        exc = run.taps[-1]
        if isinstance(exc, RuntimeError) and str(exc).startswith("not bound: "):
            blocked(str(exc))
        pytest.fail(f"{operation_id}: unhandled {type(exc).__name__} (500)")
    if result.error is not None:
        exc = result.error
        if isinstance(exc, RuntimeError) and str(exc).startswith("not bound: "):
            blocked(str(exc))
        pytest.fail(f"{operation_id}: stream raised {type(exc).__name__}")
    if result.status is None:
        pytest.fail(f"{operation_id}: no response within {timeout_s}s")
    return as_response(result)


def _fill_path(template: str, values: Mapping[str, str]) -> str:
    path = template
    for name, value in values.items():
        path = path.replace("{" + name + "}", value)
    return path


def _checked(run: AppRun, operation_id: str, expect: int, what: str, **kwargs: Any) -> Any:
    spec = load_contract().operations[operation_id]
    path = kwargs.pop("path", spec.path_template)
    response = send(run, operation_id, path=path, **kwargs)
    if response.status_code != expect:
        pytest.fail(f"precondition {what} answered {response.status_code}{_code_suffix(response)}")
    assert_response_matches(response, operation_id)
    return response


def seeded_case_ref(run: AppRun) -> str:
    db_path = Path(run.settings.data_dir) / WORKING_DB_NAME
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT case_ref FROM cases ORDER BY case_ref LIMIT 1").fetchone()
    finally:
        conn.close()
    if row is None:
        blocked("not bound: demo seed (no row in cases; AEA-29/AEA-31 first-boot seed)")
    return str(row[0])


def _resolve_path_param(run: AppRun, drive: Drive, param: str, words: list[str]) -> str:
    given = drive.spec.get("path", {}).get(param)
    if given is None and param == "thread_id":
        given = drive.spec.get("thread")
    if given is None and param == "reference":
        given = drive.spec.get("reference")  # AEA-46 cases name the case here, not under "path"
    if given in PATH_WORDS or given is None:
        if given in ("started", "ended"):
            if run.main_thread is None:
                pytest.fail(f"{drive.id}: path word {given!r} needs a thread precondition")
            return run.main_thread
        if given == "unknown":
            return str(uuid.uuid4())
        if given == "malformed":
            return MALFORMED_THREAD_ID
        if given == "other_session":
            return run.other_thread or str(uuid.uuid4())
        if given == "seeded_case":
            return seeded_case_ref(run)
        if param == "thread_id":
            return str(uuid.uuid4()) if "unknown" in words else (run.main_thread or str(uuid.uuid4()))
        if param == "reference":
            return seeded_case_ref(run) if run.main_token is not None else "MHC-C-0001"
        return str(uuid.uuid4())
    return str(given)


def run_drive(run: AppRun, drive: Drive) -> str:
    """Realise one drive on the real app and check the response; return a one-line evidence string."""
    op = drive.operation_id
    spec = load_contract().operations[op]
    d = drive.spec
    original = [str(w) for w in d.get("preconditions", ())]
    words = [PRECONDITIONS[w] for w in original]
    setup = SETUPS.get(str(d.get("setup", "")))
    if (spec.method, spec.path_template) not in run.registered:
        blocked(f"route not registered: {op}")
    pair = demo_pair(run.settings)
    needs_session = any(w != "unknown" for w in words) or setup in ("ended", "other_session_thread")
    if needs_session:
        login = _checked(run, "login", 200, "login", token=None, body={"json": dict(pair)})
        run.main_token = session_cookie_value(login)
        assert run.main_token is not None, "login set no session cookie"
    for word in words:
        if word.startswith("role:"):
            role = word.split(":", 1)[1]
            _checked(
                run, "switchRole", 200, f"switchRole {role}",
                token=run.main_token, body={"json": request_examples("switchRole")[role.upper()]},
            )  # fmt: skip
    if any(w in ("thread", "verified", "open_case", "ended") for w in words) or setup == "ended":
        started = _checked(run, "startChatSession", 201, "startChatSession", token=run.main_token, body=None)
        run.main_thread = str(started.json()["thread_id"])
    if "verified" in words:
        assert run.main_thread is not None
        data_dir = Path(run.settings.data_dir)
        verify_thread(
            TempStore(
                data_dir=data_dir,
                db_path=data_dir / WORKING_DB_NAME,
                issued_path=ISSUED_DB,
                uow=run.app.state.container.get(UOW_FACTORY),
            ),
            ThreadId(run.main_thread),
        )
    if "open_case" in words:
        example = {**request_examples("requestPerson")["BUTTON"], "turn_id": str(uuid.uuid4())}
        _checked(
            run, "requestPerson", 200, "requestPerson",
            path=_fill_path(load_contract().operations["requestPerson"].path_template, {"thread_id": str(run.main_thread)}),
            token=run.main_token, body={"json": example},
        )  # fmt: skip
    if "ended" in words or setup == "ended":
        _checked(run, "resetDemo", 200, "resetDemo", token=run.main_token,
                 body={"json": request_examples("resetDemo")["CONFIRM"]})  # fmt: skip
    if setup == "other_session_thread":
        second = _checked(run, "login", 200, "second login", token=None, body={"json": dict(pair)})
        other = _checked(run, "startChatSession", 201, "second startChatSession",
                         token=session_cookie_value(second), body=None)  # fmt: skip
        run.other_thread = str(other.json()["thread_id"])
    if setup == "login_rejects_exhausted":
        for _ in range(WebLimits().login_rejects_per_ip):
            _checked(
                run, "login", 401, "login reject",
                token=None, body={"json": {"username": pair["username"], "password": rand_word(14, "pw")}},
            )  # fmt: skip
    if d.get("events"):
        assert run.main_thread is not None
        run.event_ids = append_stored(
            run.app.state.container.get(UOW_FACTORY),
            run.main_thread,
            [(k, payload(k)) for k in d["events"]],
        )
    values = {p: _resolve_path_param(run, drive, p, words) for p in _params(spec.path_template)}
    path = _fill_path(spec.path_template, values)
    body = _build_body(run, op, d.get("body"), pair)
    token = run.main_token if "login" in original else None
    headers: dict[str, str] = {}
    last = d.get("last_event_id")
    if isinstance(last, dict):
        headers["Last-Event-ID"] = str(run.event_ids[last["after_event"] - 1])
    elif last is not None:
        headers["Last-Event-ID"] = str(last)
    if spec.event_schema and drive.status == 200:
        result = read_sse(
            run, path, (cookie_header(token) | headers) if token else headers, frames=d["frames"]
        )
        if result.error is not None:
            exc = result.error
            if isinstance(exc, RuntimeError) and str(exc).startswith("not bound: "):
                blocked(str(exc))
            pytest.fail(f"{drive.id}: stream raised {type(exc).__name__}")
        assert result.status == 200, f"{drive.id}: expected 200, got {result.status}"
        assert result.content_type.startswith("text/event-stream"), (
            f"{drive.id}: content type is not event-stream"
        )
        assert len(result.frames) == d["frames"], (
            f"{drive.id}: expected {d['frames']} frames, got {len(result.frames)}"
        )
        assert_sse_frames_match(list(result.frames), op)
        return f"{drive.id}: 200 ({len(result.frames)} frames)"

    def dispatch() -> Any:
        if spec.event_schema:
            return send_stream(run, op, path=path, token=token, extra_headers=headers)
        return send(run, op, path=path, token=token, body=body, extra_headers=headers)

    if setup == "reset_held":
        with run.app.state.container.get(RESET_GATE).hold():
            response = dispatch()
    else:
        response = dispatch()
    code = _code_suffix(response)
    assert response.status_code == drive.status, (
        f"{drive.id}: expected {drive.status}, got {response.status_code}{code}"
    )
    if "code" in d:
        assert code == f" ({d['code']})", f"{drive.id}: expected error code {d['code']}{code}"
    assert_response_matches(response, op)
    return f"{drive.id}: {response.status_code}"


def _params(template: str) -> list[str]:
    return re.findall(r"\{(\w+)\}", template)


def _build_body(run: AppRun, op: str, raw: Any, pair: Mapping[str, str]) -> Mapping[str, Any] | None:
    if raw is None:
        return None
    if "example" not in raw:
        return dict(raw)
    value = request_examples(op)[raw["example"]]
    if raw.get("credentials") == "configured":
        value.update(pair)
    elif raw.get("credentials") == "wrong_password":
        value.update(username=pair["username"], password=rand_word(14, "pw"))
    if raw.get("turn_id") == "new":
        value["turn_id"] = str(uuid.uuid4())
    return {"json": value}


def read_sse(
    run: AppRun,
    path: str,
    headers: Mapping[str, str],
    *,
    frames: int,
    timeout_s: float = STREAM_READ_TIMEOUT_S,
) -> SseRead:
    """Read an SSE response on the TestClient's own event loop, for at most about 2 x timeout_s."""
    portal = run.client.portal
    assert portal is not None, "the client must be used as a context manager"
    result: SseRead = portal.call(read_asgi_stream, run.app, path, dict(headers), frames, timeout_s)
    return result
