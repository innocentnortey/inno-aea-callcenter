"""AEA-23 AC-18 to AC-20, AC-28 and PA-3: web/deps.py providers, require_staff, owned_thread, owned_stream_thread and the
register_web hunk.

Failure modes guarded: invariant (every provider declared, overridable and lazy; one stream limiter), refusal (wrong
role, role reset, a thread that is not yours), regression (a role cached between requests; a second lookup).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anyio
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import meridian.web.deps as deps
from meridian.domain.staff import DemoRole, StaffActor, StaffRole
from meridian.policy.limits import Limits
from meridian.services.reset_gate import ResetGate
from meridian.web.app import create_app
from meridian.web.container import Container, ContainerError, register_web
from meridian.web.deps import (
    RATE_LIMITER,
    RESET_GATE,
    STREAM_POLL_LIMITER,
    WALL_CLOCK,
    owned_stream_thread,
    owned_thread,
    require_staff,
)
from meridian.web.middleware import RateLimiter
from tests.api.web_shell_support import (
    ConversationRowStub,
    EndedThreadStub,
    FakeSessionStore,
    FakeUow,
    add_probe_route,
    add_test_route,
    assert_matches,
    cookie_header,
    error_body,
    make_client,
    make_settings,
    new_thread_id,
    request_for,
    web_app,
    without_request_id,
)

# web section 4: every provider the shell declares. The first group is bound by AEA-23; the rest by later tickets.
BOUND_BY_SHELL = ("get_reset_gate", "get_rate_limiter", "get_wall_clock", "get_stream_poll_limiter")
BOUND_LATER = (
    "get_login_sessions",
    "get_staff_access",
    "get_flag_service",
    "get_session_service",
    "get_turn_service",
    "get_person_requests",
    "get_handoff_service",
    "get_case_service",
    "get_reply_composer",
    "get_identity_service",
    "get_demo_service",
    "get_reset_service",
    "get_live_chat",
    "get_metrics_reads",
    "get_uow_factory",
)
CONTEXT_PROVIDERS = ("get_request_context", "get_login_session")
PROVIDERS = (*CONTEXT_PROVIDERS, *BOUND_LATER, *BOUND_BY_SHELL)


def actor_endpoint(
    actor: StaffActor = Depends(require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR)),  # noqa: B008
) -> dict[str, str]:
    return {"role": actor.role.value, "name": actor.name}


def thread_endpoint(thread_id: str = Depends(owned_thread)) -> dict[str, str]:
    return {"thread_id": str(thread_id)}


def stream_thread_endpoint(thread_id: str = Depends(owned_stream_thread)) -> dict[str, str]:
    return {"thread_id": str(thread_id)}


def _sentinel_endpoint(provider: Any, sentinel: object) -> Any:
    def endpoint(value: Any = Depends(provider)) -> dict[str, bool]:  # noqa: B008
        return {"is_sentinel": value is sentinel}

    return endpoint


def _constant(value: object) -> Any:
    def provide() -> object:
        return value

    return provide


def test_every_provider_declared_overridable_and_lazy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """invariant (AC-18): all providers exist and can be overridden; unbound ones fail at call time, not import time."""
    # Importing meridian.web.deps with nothing bound raises nothing: this module imports it at the top.
    for name in PROVIDERS:
        assert callable(getattr(deps, name)), name
    for name in ("require_staff", "owned_thread", "owned_stream_thread"):
        assert callable(getattr(deps, name)), name
    assert callable(require_staff(StaffRole.OWNER))

    # Overridable: each provider can be replaced through app.dependency_overrides.
    for name in PROVIDERS:
        provider = getattr(deps, name)
        sentinel = object()
        app = FastAPI()
        app.add_api_route("/p", _sentinel_endpoint(provider, sentinel), response_model=None)
        app.dependency_overrides[provider] = _constant(sentinel)
        assert TestClient(app).get("/p").json() == {"is_sentinel": True}, name

    # Lazy: with no container, and with a container that never provided the key, the call says what is unbound.
    bare = FastAPI()
    for name in BOUND_LATER:
        with pytest.raises(RuntimeError) as raised:
            getattr(deps, name)(request_for(bare))
        assert str(raised.value) == f"not bound: {name}", name

    app = web_app(monkeypatch, make_settings(tmp_path))
    with make_client(app):
        for name in BOUND_LATER:
            with pytest.raises(RuntimeError) as raised:
                getattr(deps, name)(request_for(app))
            assert str(raised.value) == f"not bound: {name}", name
        assert isinstance(deps.get_reset_gate(request_for(app)), ResetGate)
        assert isinstance(deps.get_rate_limiter(request_for(app)), RateLimiter)
        assert callable(deps.get_wall_clock(request_for(app)))
        first, second = (deps.get_stream_poll_limiter(request_for(app)) for _ in range(2))
        assert first is second
        assert isinstance(first, anyio.CapacityLimiter)
        assert first.total_tokens == 4
    print(
        f"{len(PROVIDERS)} providers declared and overridable; {len(BOUND_LATER)} unbound ones raise 'not bound: <name>'"
    )


def test_require_staff_refusals(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """refusal (AC-19): the actor on an allowed role; 403 ROLE_NOT_ALLOWED with role, needs in order and reason."""
    store = FakeSessionStore()
    app = web_app(monkeypatch, make_settings(tmp_path), store=store)
    add_probe_route(app, "getQueue", endpoint=actor_endpoint)
    with make_client(app) as client:
        supervisor = store.issue(DemoRole.SUPERVISOR)
        allowed = client.get("/api/staff/queue", headers=cookie_header(supervisor))
        assert allowed.status_code == 200
        assert allowed.json()["role"] == "supervisor"

        customer = store.issue(DemoRole.CUSTOMER)
        wrong = client.get("/api/staff/queue", headers=cookie_header(customer))
        body = error_body(wrong, 403, "ROLE_NOT_ALLOWED")
        assert body["error"]["details"] == {
            "role": "customer",
            "needs": ["representative", "supervisor"],
            "reason": "wrong_role",
        }
        assert_matches(wrong, "getQueue")

        store.set_role(customer, DemoRole.CUSTOMER, role_reset=True)
        reset = client.get("/api/staff/queue", headers=cookie_header(customer))
        assert error_body(reset, 403, "ROLE_NOT_ALLOWED")["error"]["details"]["reason"] == "role_reset"
        assert_matches(reset, "getQueue")

        owner = store.issue(DemoRole.OWNER)
        refused = client.get("/api/staff/queue", headers=cookie_header(owner))
        assert error_body(refused, 403, "ROLE_NOT_ALLOWED")["error"]["details"]["role"] == "owner"

    # needs keep the order the declaration gave them.
    reversed_app = web_app(monkeypatch, make_settings(tmp_path / "order"), store=store)
    add_probe_route(
        reversed_app,
        "getQueue",
        dependencies=[Depends(require_staff(StaffRole.SUPERVISOR, StaffRole.REPRESENTATIVE))],
    )
    with make_client(reversed_app) as client:
        response = client.get("/api/staff/queue", headers=cookie_header(store.issue(DemoRole.CUSTOMER)))
    assert error_body(response, 403, "ROLE_NOT_ALLOWED")["error"]["details"]["needs"] == [
        "supervisor",
        "representative",
    ]


def _thread_fixture(store: FakeSessionStore, token: str) -> tuple[FakeUow, dict[str, str]]:
    mine = str(store.session_of(token).session_id)
    ids = {name: new_thread_id() for name in ("live", "ended", "other_live", "other_ended", "unknown")}
    when = "2031-01-01T00:00:00+00:00"
    uow = FakeUow(
        {
            ids["live"]: ConversationRowStub(ids["live"], mine),
            ids["ended"]: EndedThreadStub(ids["ended"], mine, when, "demo_reset"),
            ids["other_live"]: ConversationRowStub(ids["other_live"], "someone-else"),
            ids["other_ended"]: EndedThreadStub(ids["other_ended"], "someone-else", when, "demo_reset"),
        }
    )
    return uow, ids


def test_owned_thread_404_410(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """refusal (AC-20): own live thread passes; own ended thread is 410; every other case is the same 404."""
    store = FakeSessionStore()
    token = store.issue()
    uow, ids = _thread_fixture(store, token)
    app = web_app(monkeypatch, make_settings(tmp_path), store=store, uow=uow)
    add_test_route(app, "GET", "/api/test/threads/{thread_id}", thread_endpoint)
    headers = cookie_header(token)
    with make_client(app) as client:
        ok = client.get(f"/api/test/threads/{ids['live']}", headers=headers)
        assert ok.status_code == 200 and ok.json() == {"thread_id": ids["live"]}

        ended = client.get(f"/api/test/threads/{ids['ended']}", headers=headers)
        body = error_body(ended, 410, "SESSION_ENDED")
        assert body["error"]["details"] == {"reason": "demo_reset"}
        assert_matches(ended, "getChatThread")

        candidates = {
            "malformed id": "not-a-thread-id",
            "unknown id": ids["unknown"],
            "another session's live thread": ids["other_live"],
            "another session's ended thread": ids["other_ended"],
        }
        bodies = {}
        for label, thread_id in candidates.items():
            response = client.get(f"/api/test/threads/{thread_id}", headers=headers)
            body = error_body(response, 404, "SESSION_NOT_FOUND")
            assert (body["error"]["field"], body["error"]["constraint"], body["error"]["details"]) == (
                None,
                None,
                None,
            )
            assert_matches(response, "getChatThread")
            bodies[label] = without_request_id(response)
    first = next(iter(bodies.values()))
    assert all(body == first for body in bodies.values()), bodies
    print(f"four 404 bodies equal: {sorted(bodies)}")


def test_owned_stream_thread_maps_ended_to_404(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """refusal (AC-20, R-W-3): an ended thread of this session is the identical 404, from a single lookup."""
    store = FakeSessionStore()
    token = store.issue()
    uow, ids = _thread_fixture(store, token)
    app = web_app(monkeypatch, make_settings(tmp_path), store=store, uow=uow)
    add_test_route(app, "GET", "/api/test/streams/{thread_id}", stream_thread_endpoint)
    headers = cookie_header(token)
    with make_client(app) as client:
        live = client.get(f"/api/test/streams/{ids['live']}", headers=headers)
        assert live.status_code == 200

        unknown = client.get(f"/api/test/streams/{ids['unknown']}", headers=headers)
        error_body(unknown, 404, "SESSION_NOT_FOUND")

        uow.lookups.clear()
        ended = client.get(f"/api/test/streams/{ids['ended']}", headers=headers)
        error_body(ended, 404, "SESSION_NOT_FOUND")
        assert_matches(ended, "streamChatEvents")
        print(f"lookups for the ended thread: {uow.lookups}")
        assert uow.lookups == [ids["ended"]], "exactly one lookup"
    assert without_request_id(ended) == without_request_id(unknown)


def test_role_refusal_names_current_role(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """regression (AC-28): the 403 names the role held on THIS request; a role change between requests shows."""
    store = FakeSessionStore()
    app = web_app(monkeypatch, make_settings(tmp_path), store=store)
    add_probe_route(app, "getQueue", dependencies=[Depends(require_staff(StaffRole.SUPERVISOR))])
    token = store.issue(DemoRole.CUSTOMER)
    with make_client(app) as client:
        first = client.get("/api/staff/queue", headers=cookie_header(token))
        store.set_role(token, DemoRole.REPRESENTATIVE)
        second = client.get("/api/staff/queue", headers=cookie_header(token))
    one, two = error_body(first, 403, "ROLE_NOT_ALLOWED"), error_body(second, 403, "ROLE_NOT_ALLOWED")
    print(f"roles named: {one['error']['details']['role']} then {two['error']['details']['role']}")
    assert one["error"]["details"]["role"] == "customer"
    assert two["error"]["details"]["role"] == "representative"
    assert_matches(first, "getQueue")
    assert_matches(second, "getQueue")


def test_register_web_binds_shell_objects_and_skips_bare_app(tmp_path: Path) -> None:
    """invariant (PA-3): register_web binds the four shell objects and two public paths, and does nothing on a bare app."""
    settings = make_settings(tmp_path)
    limits = Limits()
    keys = (RESET_GATE, RATE_LIMITER, STREAM_POLL_LIMITER, WALL_CLOCK)

    bare = Container(settings=settings, limits=limits)
    register_web(bare, FastAPI(), settings=settings, limits=limits)
    bare.build()
    for key in keys:
        with pytest.raises(ContainerError):
            bare.get(key)

    app = create_app(settings)
    container = Container(settings=settings, limits=limits)
    register_web(container, app, settings=settings, limits=limits)
    container.build()
    assert isinstance(container.get(RESET_GATE), ResetGate)
    assert isinstance(container.get(RATE_LIMITER), RateLimiter)
    limiter = container.get(STREAM_POLL_LIMITER)
    assert isinstance(limiter, anyio.CapacityLimiter) and limiter.total_tokens == 4
    assert container.get(WALL_CLOCK) is app.state.web_shell.wall_clock
    assert app.state.web_shell.public_paths.entries() == {
        ("exact", "POST", "/api/login"),
        ("exact", "GET", "/healthz"),
    }
