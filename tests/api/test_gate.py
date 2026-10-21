"""AEA-23 AC-1, AC-2, AC-3 and the ticket's example pair: the one login gate in front of every route.

Failure modes guarded (labels in the test names): invariant (nothing but the login and /healthz answers without a
session), boundary (hostile redirect targets, an expired session), refusal (wrong role).
"""

from __future__ import annotations

import urllib.parse
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import Depends

from meridian.domain.staff import DemoRole, StaffRole
from meridian.web.app import ContainerOverrides
from meridian.web.deps import require_staff
from meridian.web.middleware import OPERATIONS_BY_ROUTE, safe_return_to
from tests.api.openapi_check import load_contract
from tests.api.web_shell_support import (
    FakeHeartbeat,
    FakeSessionStore,
    MutableClock,
    RouteInfo,
    add_probe_route,
    assert_matches,
    cookie_attributes,
    cookie_header,
    demo_pair,
    effective_routes,
    error_body,
    full_app,
    login,
    make_client,
    make_settings,
    session_cookie_value,
    set_cookie_lines,
    web_app,
)

THREAD = str(uuid.uuid4())
PATH_VALUES = {"thread_id": THREAD, "reference": "MHC-C-0001", "flag_id": "1"}
WRITE_METHODS = {"POST", "PUT", "PATCH"}


def _concrete(path: str) -> str:
    for name, value in PATH_VALUES.items():
        path = path.replace("{" + name + "}", value)
    return path


def _api_routes(app: Any) -> list[RouteInfo]:
    return [r for r in effective_routes(app) if r.path.startswith("/api/")]


def _registered(app: Any) -> set[tuple[str, str]]:
    return {(m, r.path) for r in effective_routes(app) for m in r.methods}


def test_every_api_route_but_login_requires_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """invariant (AC-1): every /api route except POST /api/login answers 401 UNAUTHENTICATED reason none."""
    store = FakeSessionStore()
    app = full_app(monkeypatch, make_settings(tmp_path), store=store, heartbeat=FakeHeartbeat())
    contract = load_contract()
    # Cover every operation in the contract today, not only the routes registered so far: stand-in routes fill the gaps.
    registered = _registered(app)
    for probe_id, spec in contract.operations.items():
        if (spec.method.upper(), spec.path_template) not in registered:
            add_probe_route(app, probe_id)

    valid = store.issue()
    tampered = valid[:-1] + ("A" if valid[-1] != "A" else "B")
    cookies: dict[str, dict[str, str]] = {
        "no cookie": {},
        "blank cookie": {"Cookie": "mhc_session="},
        "unknown token": cookie_header("tok-not-issued-by-anyone"),
        "tampered token": cookie_header(tampered),
    }
    unclassified: list[str] = []
    cases = 0
    with make_client(app) as client:
        for route in _api_routes(app):
            for method in sorted(route.methods):
                if (method, route.path) == ("POST", "/api/login"):
                    continue
                operation_id = OPERATIONS_BY_ROUTE.get((method, route.path))
                if operation_id is None:
                    unclassified.append(f"{method} {route.path}")
                    continue
                for label, headers in cookies.items():
                    kwargs: dict[str, Any] = {"json": {}} if method in WRITE_METHODS else {}
                    response = client.request(method, _concrete(route.path), headers=headers, **kwargs)
                    assert response.status_code == 401, (
                        f"{method} {route.path} ({label}): {response.status_code}"
                    )
                    body = error_body(response, 401, "UNAUTHENTICATED")
                    assert body["error"]["details"] == {"reason": "none"}, f"{method} {route.path} ({label})"
                    assert_matches(response, operation_id)
                    cases += 1
        # Control: a valid session passes the gate on a real route, so the 401s above are not a blanket refusal.
        assert client.post("/api/logout", headers=cookie_header(valid)).status_code == 204
        health = client.get("/healthz")
        assert health.status_code != 401
    assert not unclassified, f"/api routes missing from OPERATIONS_BY_ROUTE: {unclassified}"
    entries = app.state.web_shell.public_paths.entries()
    print(f"public entries: {sorted(entries)}; unauthenticated cases passed: {cases}")
    assert ("exact", "POST", "/api/login") in entries
    assert ("exact", "GET", "/healthz") in entries
    assert not [e for e in entries if e[2].startswith("/api/") and e != ("exact", "POST", "/api/login")]
    assert cases >= 4 * 29


def test_page_get_redirects_to_login_without_open_redirect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """invariant + boundary (AC-2): an unsigned page GET is a 303 to /login; hostile return_to is never echoed."""
    app = web_app(monkeypatch, make_settings(tmp_path))
    with make_client(app) as client:
        response = client.get("/staff/queue")
        assert response.status_code == 303
        assert response.headers["location"] == "/login?return_to=%2Fstaff%2Fqueue&reason=none"
        assert response.headers["X-Request-ID"]

        with_query = client.get("/staff/queue?tab=open&x=1")
        assert with_query.status_code == 303
        parsed = urllib.parse.parse_qs(urllib.parse.urlsplit(with_query.headers["location"]).query)
        assert parsed == {"return_to": ["/staff/queue?tab=open&x=1"], "reason": ["none"]}

        hostile_path = client.get("http://testserver//evil.example")
        assert hostile_path.status_code == 303
        assert "evil" not in hostile_path.headers["location"]

    for hostile in ("//evil.example", "https://evil.example/x", "evil"):
        assert safe_return_to(hostile) is None, hostile
    assert safe_return_to("/staff/queue") == "/staff/queue"


def test_expired_session_reason_expired_and_cookie_cleared(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """invariant (AC-3): SessionExpired is 401 reason expired (303 reason=expired for a page) and clears the cookie."""
    now = datetime(2031, 5, 6, 7, 8, 9, tzinfo=UTC)
    clock = MutableClock(now)
    store = FakeSessionStore()
    token = store.issue(now=now)
    store.expire(token)
    session_id = str(store.session_of(token).session_id)
    app = web_app(
        monkeypatch,
        make_settings(tmp_path),
        overrides=ContainerOverrides(wall_clock=clock),
        store=store,
    )
    with make_client(app) as client:
        api = client.post("/api/logout", headers=cookie_header(token))
        body = error_body(api, 401, "UNAUTHENTICATED")
        assert body["error"]["details"] == {"reason": "expired"}
        assert_matches(api, "logout")
        cleared = [line for line in set_cookie_lines(api) if line.startswith("mhc_session=")]
        assert cleared, set_cookie_lines(api)
        assert cookie_attributes(cleared[0])["max-age"] == "0"
        assert token not in api.text and session_id not in api.text

        page = client.get("/staff/queue", headers=cookie_header(token))
        assert page.status_code == 303
        assert "reason=expired" in page.headers["location"]
        page_cookies = [
            line for line in page.headers.get_list("set-cookie") if line.startswith("mhc_session=")
        ]
        assert page_cookies
        assert cookie_attributes(page_cookies[0])["max-age"] == "0"

    resolves = [when for name, when in store.calls if name == "resolve"]
    assert resolves
    for when in resolves:
        assert when == now, "resolve must receive the wall clock from get_wall_clock()"
        assert when is not None
        offset = when.utcoffset()
        assert offset is not None and offset.total_seconds() == 0


def test_example_pair_unsigned_page_login_and_role_refusal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """invariant (the ticket's example pair): unsigned page 303, login, wrong password, then a role refusal."""
    settings = make_settings(tmp_path)
    store = FakeSessionStore()
    app = web_app(monkeypatch, settings, store=store)
    add_probe_route(
        app,
        "getQueue",
        dependencies=[Depends(require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR))],
    )
    with make_client(app) as client:
        assert client.get("/staff/queue").status_code == 303

        signed_in = login(client, settings)
        assert signed_in.status_code == 200
        assert_matches(signed_in, "login")
        token = session_cookie_value(signed_in)
        assert token

        wrong = client.post("/api/login", json={**demo_pair(settings), "password": "not-the-password"})
        error_body(wrong, 401, "LOGIN_FAILED")
        assert_matches(wrong, "login")

        refused = client.get("/api/staff/queue", headers=cookie_header(token))
        body = error_body(refused, 403, "ROLE_NOT_ALLOWED")
        assert body["error"]["details"] == {
            "role": DemoRole.CUSTOMER.value,
            "needs": ["representative", "supervisor"],
            "reason": "wrong_role",
        }
        assert_matches(refused, "getQueue")
