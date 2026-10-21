"""AEA-23 AC-9 to AC-11, AC-23, AC-26, AC-30, AC-33 to AC-35 and PA-1: the app factory, error shape, request ids,
/healthz, the lifespan and the test-only wall-clock override.

Failure modes guarded: invariant (one renderer, one request id per response, healthz independent of workers, storage
and the reset gate, build and close once), boundary (validation errors never echo a value), negative (nothing outside
code can set the wall clock or the container overrides).
"""

from __future__ import annotations

import ast
import inspect
import logging
import re
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import anyio
import anyio.to_thread
import pytest
from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from meridian.config import ENV_NAMES, Settings
from meridian.domain.staff import StaffRole
from meridian.policy.limits import WebLimits
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.deps import get_wall_clock, owned_thread, provided, require_staff
from meridian.web.errors import ApiProblem
from meridian.web.middleware import RateLimiter
from tests.api.web_shell_support import (
    EndedThreadStub,
    FakeHeartbeat,
    FakeSessionStore,
    FakeUow,
    MutableClock,
    SequenceClock,
    add_probe_route,
    add_test_route,
    app_log_text,
    captured_log,
    cookie_header,
    effective_routes,
    full_app,
    install_builder_spy,
    login,
    make_client,
    make_settings,
    rand_word,
    records_of,
    reset_gate_of,
    session_cookie_value,
    suppress_container_starters,
    web_app,
)

REPO = Path(__file__).resolve().parents[2]
WEB_SRC = REPO / "src" / "meridian" / "web"
YEAR_2000 = "2000-01-01T00:00:00+00:00"


BOOM_TEXT = rand_word(20, "boom")


def boom_endpoint() -> None:
    raise RuntimeError(BOOM_TEXT)


class ProbeBody(BaseModel):
    qty: int
    name: str


def validate_endpoint(body: ProbeBody) -> dict[str, str]:
    return {"ok": "yes"}


def query_endpoint(limit: int) -> dict[str, int]:
    return {"limit": limit}


def thread_endpoint(thread_id: str = Depends(owned_thread)) -> dict[str, str]:
    return {"thread_id": str(thread_id)}


def test_validation_error_is_400_without_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """boundary (AC-9): 400 VALIDATION_ERROR with field and constraint, no value; one ApiError renderer."""
    app = web_app(monkeypatch, make_settings(tmp_path))
    add_test_route(app, "POST", "/api/test/validate", validate_endpoint)
    add_test_route(app, "GET", "/api/test/query", query_endpoint)
    token = app.state.test_store.issue()
    seeded = rand_word(16)
    caplog.set_level(logging.DEBUG)
    with make_client(app) as client, captured_log() as stream:
        bad_body = client.post(
            "/api/test/validate", json={"qty": seeded, "name": "ok"}, headers=cookie_header(token)
        )
        bad_query = client.get(f"/api/test/query?limit={seeded}", headers=cookie_header(token))
        for response, field in ((bad_body, "qty"), (bad_query, "limit")):
            assert response.status_code == 400, response.text
            body = response.json()
            assert body["error"]["code"] == "VALIDATION_ERROR"
            assert body["error"]["field"] == field
            assert body["error"]["constraint"]
            assert set(body["error"]) == {"code", "field", "constraint", "details"}
            assert body["request_id"] == response.headers["X-Request-ID"]
            assert seeded not in response.text
    assert seeded not in stream.getvalue() + app_log_text(caplog)
    assert ApiProblem in app.exception_handlers
    assert RequestValidationError in app.exception_handlers

    found: list[tuple[str, int]] = []
    for path in sorted(WEB_SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text("utf-8"))):
            if isinstance(node, ast.Constant) and node.value == "constraint":
                found.append((path.name, node.lineno))
    assert len(found) == 1, f"exactly one ApiError renderer expected, found {found}"
    errors_tree = ast.parse((WEB_SRC / "errors.py").read_text("utf-8"))
    renderer = next(
        n for n in ast.walk(errors_tree) if isinstance(n, ast.FunctionDef) and n.name == "render_api_problem"
    )
    assert found[0][0] == "errors.py" and renderer.lineno <= found[0][1] <= (renderer.end_lineno or 0)


def test_request_id_on_every_response(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-10): X-Request-ID on 200, 204, 303, 400, 401, 403, 404, 410, 429, 503 and 500, equal to the body's."""
    settings = make_settings(tmp_path)
    store = FakeSessionStore()
    token = store.issue()
    session_id = str(store.session_of(token).session_id)
    ended, unknown = str(uuid.uuid4()), str(uuid.uuid4())
    uow = FakeUow({ended: EndedThreadStub(ended, session_id, "2031-01-01T00:00:00+00:00", "demo_reset")})
    app = web_app(
        monkeypatch,
        settings,
        store=store,
        uow=uow,
        limiter=RateLimiter(WebLimits(reads_per_session_per_min=1)),
    )
    add_test_route(app, "POST", "/api/test/validate", validate_endpoint)
    add_test_route(app, "GET", "/api/test/threads/{thread_id}", thread_endpoint)
    add_test_route(app, "GET", "/api/test/boom", boom_endpoint)
    add_probe_route(app, "getQueue", dependencies=[Depends(require_staff(StaffRole.OWNER))])
    add_probe_route(app, "listDemoInbox")
    add_probe_route(app, "startChatSession")
    headers = cookie_header(token)
    seen: dict[int, Any] = {}
    with make_client(app) as client:

        def note(response: Any) -> None:
            seen.setdefault(response.status_code, response)
            assert response.headers["X-Request-ID"], response.status_code
            if response.content and "error" in response.json():
                assert response.json()["request_id"] == response.headers["X-Request-ID"]

        note(client.get("/healthz"))
        note(client.get("/api/demo/inbox", headers=headers))
        note(client.get("/api/demo/inbox", headers=headers))  # second read: over the one-per-minute limit
        note(client.get("/staff/queue"))
        note(client.post("/api/test/validate", json={"qty": "x"}, headers=headers))
        note(client.post("/api/logout"))
        note(client.get("/api/staff/queue", headers=headers))
        note(client.get(f"/api/test/threads/{unknown}", headers=headers))
        note(client.get(f"/api/test/threads/{ended}", headers=headers))
        note(client.get("/api/test/boom", headers=headers))
        with reset_gate_of(app).hold():
            note(client.post("/api/chat/sessions", headers=headers))
        note(client.post("/api/logout", headers=headers))
    print(f"statuses with a request id: {sorted(seen)}")
    assert {200, 204, 303, 400, 401, 403, 404, 410, 429, 503, 500} <= set(seen)


def test_healthz_reads_heartbeat_not_pool_or_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-11): async, heartbeat-driven, answers with every worker blocked, a raising UoW and the gate held."""
    heartbeat = FakeHeartbeat(fresh=True)
    uow = FakeUow(raise_on_use=True)
    store = FakeSessionStore()
    app = web_app(monkeypatch, make_settings(tmp_path), store=store, heartbeat=heartbeat, uow=uow)
    started, release = threading.Event(), threading.Event()

    def block() -> dict[str, bool]:
        started.set()
        release.wait(10)
        return {"done": True}

    add_test_route(app, "GET", "/api/test/block", block)
    route = next(r for r in effective_routes(app) if r.path == "/healthz")
    assert inspect.iscoroutinefunction(route.endpoint), "/healthz must be async def"
    token = store.issue()

    async def set_tokens(count: int) -> int:
        limiter = anyio.to_thread.current_default_thread_limiter()
        previous = int(limiter.total_tokens)
        limiter.total_tokens = count
        return previous

    with make_client(app) as client:
        assert client.get("/healthz").status_code == 200
        heartbeat.value = False
        assert client.get("/healthz").status_code != 200
        heartbeat.value = True

        portal = client.portal
        assert portal is not None
        previous = portal.call(set_tokens, 1)
        blocker = threading.Thread(
            target=lambda: client.get("/api/test/block", headers=cookie_header(token)), daemon=True
        )
        result: dict[str, Any] = {}
        try:
            blocker.start()
            assert started.wait(5), "the blocking route never started"
            caller = threading.Thread(target=lambda: result.update(r=client.get("/healthz")), daemon=True)
            caller.start()
            caller.join(3.0)
            assert not caller.is_alive(), "/healthz waited for a worker thread"
            assert result["r"].status_code == 200
        finally:
            release.set()
            blocker.join(5)
            portal.call(set_tokens, previous)

        with reset_gate_of(app).hold():
            began = time.monotonic()
            held = client.get("/healthz")
            assert held.status_code == 200
            assert time.monotonic() - began < 1.0, "/healthz waited on the held reset gate"
    assert uow.calls == 0, "/healthz touched the unit of work"
    assert heartbeat.calls, "/healthz did not read the heartbeat"


def test_lifespan_builds_and_closes_container(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-23): one build and one close; no module-level client, settings or limiter in web/."""
    app = web_app(monkeypatch, make_settings(tmp_path))
    spy = app.state.test_spy
    assert (spy.built, spy.closed) == (0, 0)
    with make_client(app) as client:
        client.get("/healthz")
        assert (spy.built, spy.closed) == (1, 0)
    assert (spy.built, spy.closed) == (1, 1)
    offenders = [
        f"{path.relative_to(REPO)}: {match.group(0)}"
        for path in sorted(WEB_SRC.rglob("*.py"))
        for match in re.finditer(r"^[a-z_]* = .*\(.*$", path.read_text("utf-8"), re.MULTILINE)
    ]
    assert not offenders, f"module-level assignments that call something: {offenders}"


def test_healthz_request_record(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-26): /healthz writes one request record, route /healthz, caller_role anonymous, status 200."""
    app = web_app(monkeypatch, make_settings(tmp_path))
    with make_client(app) as client, captured_log() as stream:
        response = client.get("/healthz")
    assert response.status_code == 200
    records = records_of(stream, "request")
    assert len(records) == 1, records
    record = records[0]
    assert (record["route"], record["caller_role"], record["status"]) == ("/healthz", "anonymous", 200)
    assert record["request_id"] == response.headers["X-Request-ID"]


def test_overrides_test_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-30): create_app() builds no override; the given object is passed once; nothing in src/ builds one."""
    for env_name in ENV_NAMES.values():
        monkeypatch.delenv(env_name, raising=False)
    for name, value in {
        "ANTHROPIC_API_KEY": rand_word(12),
        "OPENROUTER_API_KEY": rand_word(12),
        "MERIDIAN_DEMO_USERNAME": rand_word(8),
        "MERIDIAN_DEMO_PASSWORD": rand_word(8),
        "MERIDIAN_SESSION_SECRET": rand_word(12),
        "MERIDIAN_DATA_DIR": str(tmp_path / "data"),
    }.items():
        monkeypatch.setenv(name, value)
    spy = install_builder_spy(monkeypatch)
    with make_client(create_app()):
        pass
    assert len(spy.calls) == 1
    assert spy.calls[0]["overrides"] is None

    given = ContainerOverrides()
    with make_client(create_app(make_settings(tmp_path / "given"), overrides=given)):
        pass
    assert len(spy.calls) == 2
    assert spy.calls[1]["overrides"] is given
    builders = [
        str(path.relative_to(REPO))
        for path in sorted((REPO / "src").rglob("*.py"))
        if "ContainerOverrides(" in path.read_text("utf-8")
    ]
    assert builders == [], f"ContainerOverrides is constructed in src/: {builders}"


def test_healthz_status_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-33): record status equals response status; a raising heartbeat is a 500 with error_kind."""
    heartbeat = FakeHeartbeat(fresh=True)
    app = web_app(monkeypatch, make_settings(tmp_path), heartbeat=heartbeat)
    triples = []
    with make_client(app) as client, captured_log() as stream:
        fresh = client.get("/healthz")
        heartbeat.value = False
        stale = client.get("/healthz")
        heartbeat.raises = RuntimeError("heartbeat unreadable")
        broken = client.get("/healthz")
    records = records_of(stream, "request")
    assert len(records) == 3
    for response, record in zip((fresh, stale, broken), records, strict=True):
        triples.append((response.status_code, record["status"], record.get("error_kind")))
        assert record["status"] == response.status_code
        assert record["route"] == "/healthz"
        assert ("error_kind" in record) == (response.status_code >= 500), record
    print(f"(response status, record status, error_kind): {triples}")
    assert fresh.status_code == 200 and stale.status_code != 200
    assert broken.status_code == 500
    assert broken.headers["X-Request-ID"]
    assert broken.json() == {"request_id": broken.headers["X-Request-ID"]}
    assert records[2]["error_kind"]


def test_wall_clock_override_reaches_get_wall_clock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-34): the test-only override IS get_wall_clock(); expiry follows it; the default is real time."""
    first = datetime(2031, 3, 4, 12, 0, tzinfo=UTC)
    second = first + timedelta(seconds=43_200)
    fake = SequenceClock([first, second])
    store = FakeSessionStore()
    settings = make_settings(tmp_path / "fake")
    app = web_app(monkeypatch, settings, store=store, overrides=ContainerOverrides(wall_clock=fake))
    with make_client(app) as client:
        assert provided(app, get_wall_clock) is fake
        token = session_cookie_value(login(client, settings))
        assert token
        expired = client.post("/api/logout", headers=cookie_header(token))
    body = expired.json()
    assert expired.status_code == 401
    assert body["error"]["code"] == "UNAUTHENTICATED"
    assert body["error"]["details"] == {"reason": "expired"}
    seen = [(name, when) for name, when in store.calls if name in {"start", "resolve"}]
    print(f"store saw {seen}; 401 body {body}")
    assert seen == [("start", first), ("resolve", second)]

    for index, (label, overrides) in enumerate(
        (("no overrides", None), ("ContainerOverrides()", ContainerOverrides()))
    ):
        default_app = web_app(monkeypatch, make_settings(tmp_path / f"default{index}"), overrides=overrides)
        with make_client(default_app):
            delta = abs((provided(default_app, get_wall_clock)() - datetime.now(UTC)).total_seconds())
        print(f"{label}: default wall clock is {delta:.3f} s from now")
        assert delta < 2

    clock = MutableClock(first)
    demo_app = web_app(
        monkeypatch,
        make_settings(tmp_path / "demo"),
        store=store,
        overrides=ContainerOverrides(wall_clock=clock),
    )
    has_demo_clock = any(r.path == "/api/demo/clock" for r in effective_routes(demo_app))
    if not has_demo_clock:
        print("getDemoClock not registered yet (AEA-43)")
        return
    demo_token = store.issue(now=first)
    with make_client(demo_app) as client:
        before = client.get("/api/demo/clock", headers=cookie_header(demo_token))
        clock.advance(3_600)
        after = client.get("/api/demo/clock", headers=cookie_header(demo_token))
    assert before.status_code == after.status_code == 200
    assert before.json() == after.json(), "the demo clock must not follow the wall clock"


def test_wall_clock_not_settable_from_settings_env_or_http(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """negative (AC-35): no Settings field, env name, header, query, body or route sets the wall clock."""
    names = sorted(Settings.model_fields)
    print(f"Settings fields: {names}")
    assert not [n for n in names if any(word in n for word in ("clock", "time", "now"))]

    for env_name in ENV_NAMES.values():
        monkeypatch.delenv(env_name, raising=False)
    for name, value in {
        "ANTHROPIC_API_KEY": rand_word(12),
        "OPENROUTER_API_KEY": rand_word(12),
        "MERIDIAN_DEMO_USERNAME": rand_word(8),
        "MERIDIAN_DEMO_PASSWORD": rand_word(8),
        "MERIDIAN_SESSION_SECRET": rand_word(12),
        "MERIDIAN_DATA_DIR": str(tmp_path / "env-data"),
        "MERIDIAN_WALL_CLOCK": YEAR_2000,
        "MERIDIAN_NOW": YEAR_2000,
        "MERIDIAN_FAKE_TIME": YEAR_2000,
    }.items():
        monkeypatch.setenv(name, value)
    suppress_container_starters(monkeypatch)
    env_app = create_app()
    with make_client(env_app):
        delta = abs((provided(env_app, get_wall_clock)() - datetime.now(UTC)).total_seconds())
    print(f"env with clock names set: delta {delta:.3f} s")
    assert delta < 2
    monkeypatch.undo()

    eval_key = rand_word(14)
    settings = make_settings(tmp_path / "http", eval_key=eval_key)
    store = FakeSessionStore()
    app = full_app(monkeypatch, settings, store=store, heartbeat=FakeHeartbeat())
    registered = [(r.path, r.operation_id or "") for r in effective_routes(app)]
    assert not [p for p, op in registered if "wall" in p.lower() or "wall" in op.lower()], registered
    add_probe_route(app, "listDemoInbox")
    add_probe_route(app, "submitTurn")
    token = store.issue()
    timed = {"X-Meridian-Now": YEAR_2000, "X-Meridian-Wall-Clock": YEAR_2000}
    thread = str(uuid.uuid4())
    with make_client(app) as client:
        for keyed in (False, True):
            keys = {"X-Meridian-Eval-Key": eval_key} if keyed else {}
            sent = [
                client.get("/api/demo/inbox", headers={**cookie_header(token), **timed, **keys}),
                client.get(
                    f"/api/demo/inbox?now={YEAR_2000}&wall_clock={YEAR_2000}",
                    headers={**cookie_header(token), **keys},
                ),
                client.post(
                    f"/api/chat/sessions/{thread}/turns",
                    json={"now": YEAR_2000, "wall_clock": YEAR_2000},
                    headers={**cookie_header(token), **keys},
                ),
            ]
            for response in sent:
                assert response.status_code == 200, response.text
                skew = abs((provided(app, get_wall_clock)() - datetime.now(UTC)).total_seconds())
                print(
                    f"keyed={keyed}: clock skew {skew:.3f} s after {response.request.method} {response.request.url.path}"
                )
                assert skew < 2


def test_unhandled_error_is_500_with_request_id_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """regression (PA-1, D-P1): an unhandled exception is a 500 holding request_id only, never the exception text."""
    app = web_app(monkeypatch, make_settings(tmp_path))
    add_test_route(app, "GET", "/api/test/boom", boom_endpoint)
    token = app.state.test_store.issue()
    caplog.set_level(logging.DEBUG)
    with make_client(app) as client, captured_log() as stream:
        response = client.get("/api/test/boom", headers=cookie_header(token))
    assert response.status_code == 500
    request_id = response.headers["X-Request-ID"]
    assert request_id
    assert response.json() == {"request_id": request_id}
    assert BOOM_TEXT not in response.text
    record = records_of(stream, "request")[0]
    assert record["status"] == 500 and record["error_kind"] == "RuntimeError"
    assert BOOM_TEXT not in stream.getvalue()
