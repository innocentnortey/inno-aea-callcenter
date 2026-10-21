"""AEA-45 access: the role matrix from the OpenAPI x-roles, the supervisor-only second check, the actor, the login gate
and the router hunk. Mock-tested: the middleware and `require_staff` are real, the services are doubles."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi import FastAPI

from meridian.domain.staff import DemoRole, StaffRole, actor_for
from meridian.policy.limits import Limits
from meridian.web.container import Container, register_staff_cases
from tests.api.openapi_check import load_contract
from tests.api.reads_support import gate_held_for
from tests.api.staff_cases_support import (
    METHODS,
    as_role,
    call,
    default_body,
    request_example,
    staff_app,
    summary,
    x_roles,
)
from tests.api.web_shell_support import (
    assert_matches,
    cookie_header,
    effective_routes,
    error_body,
    make_client,
    make_settings,
)

OPERATIONS = tuple(METHODS)
ROLES = (DemoRole.CUSTOMER, DemoRole.REPRESENTATIVE, DemoRole.SUPERVISOR, DemoRole.OWNER)


@pytest.mark.parametrize("operation_id", OPERATIONS)
@pytest.mark.parametrize("role", ROLES)
def test_role_matrix(
    operation_id: str, role: DemoRole, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-3: the allowed set is the OpenAPI x-roles; a refused role gets 403 with role, needs and reason, and no
    service is touched."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    allowed = x_roles(operation_id)
    h.cases.apply_result = summary()
    with make_client(h.app) as client:
        r = call(client, operation_id, as_role(h, role), body=default_body(operation_id))
    assert_matches(r, operation_id)
    if role.value in allowed:
        assert r.status_code in (200, 201), r.text
    else:
        body = error_body(r, 403, "ROLE_NOT_ALLOWED")
        assert body["error"]["details"] == {"role": role.value, "needs": allowed, "reason": "wrong_role"}
        assert h.cases.calls == []
        assert h.flags.calls == []
        assert h.demo.reads == 0


def test_assign_and_priority_supervisor_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-4: the representative may not assign or change priority; apply is never called. The supervisor may."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    with make_client(h.app) as client:
        rep = as_role(h, DemoRole.REPRESENTATIVE)
        for name in ("ASSIGN", "CHANGE_PRIORITY"):
            r = call(client, "applyCaseAction", rep, body=request_example("applyCaseAction", name))
            body = error_body(r, 403, "ROLE_NOT_ALLOWED")
            assert_matches(r, "applyCaseAction")
            assert body["error"]["details"]["needs"] == ["supervisor"]
        assert h.cases.calls_of("apply") == []
        sup = as_role(h, DemoRole.SUPERVISOR)
        for result, name in (("ASSIGNED", "ASSIGN"), ("PRIORITY_CHANGED", "CHANGE_PRIORITY")):
            h.cases.apply_result = summary(result)
            r = call(client, "applyCaseAction", sup, body=request_example("applyCaseAction", name))
            assert r.status_code == 200, r.text
            assert_matches(r, "applyCaseAction")
    assert len(h.cases.calls_of("apply")) == 2


def test_actor_is_the_role(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-5 (STF-1): the actor is the role's persona; two sessions as representative hand apply equal actors."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    with make_client(h.app) as client:
        for _ in range(2):
            token = h.store.issue(DemoRole.REPRESENTATIVE)
            r = call(
                client,
                "applyCaseAction",
                cookie_header(token),
                body=request_example("applyCaseAction", "CLAIM"),
            )
            assert r.status_code == 200, r.text
    first, second = (c.args["actor"] for c in h.cases.calls_of("apply"))
    assert first == second == actor_for(StaffRole.REPRESENTATIVE)
    assert (first.name, first.signature) == ("Riley", "Riley (demo)")


def test_login_gate_role_reset_and_reset_wait(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-15: 401 without a session, 403 role_reset after a reset, and a held reset waits (200), never 503."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    with make_client(h.app) as client:
        for op in OPERATIONS:
            r = call(client, op, {}, body=default_body(op))
            error_body(r, 401, "UNAUTHENTICATED")
            assert_matches(r, op)
        token = h.store.issue(DemoRole.REPRESENTATIVE)
        h.store.set_role(token, DemoRole.CUSTOMER, role_reset=True)
        r = call(client, "getQueue", cookie_header(token))
        body = error_body(r, 403, "ROLE_NOT_ALLOWED")
        assert body["error"]["details"]["reason"] == "role_reset"
        assert_matches(r, "getQueue")
        headers = as_role(h, DemoRole.REPRESENTATIVE)
        with gate_held_for(h.app, 0.5):
            started = time.monotonic()
            r = call(client, "getQueue", headers)
            elapsed = time.monotonic() - started
        assert r.status_code == 200, r.text
        assert elapsed >= 0.3
        print(
            {"role_reset": body["error"]["details"], "waited_s": round(elapsed, 2), "status": r.status_code}
        )


def test_register_hunk_includes_router_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Plan: no web shell, no routes; two lifespans on one app still list each operation exactly once."""
    settings = make_settings(tmp_path)
    bare = FastAPI()
    register_staff_cases(
        Container(settings=settings, limits=Limits()), bare, settings=settings, limits=Limits()
    )
    assert not [r for r in effective_routes(bare) if r.path == "/api/staff/queue"]

    h = staff_app(monkeypatch, settings)
    for _ in range(2):
        with make_client(h.app) as client:
            client.get("/healthz")
    found = [(r.path, r.operation_id) for r in effective_routes(h.app)]
    assert found.count(("/api/staff/queue", "getQueue")) == 1
    for op in OPERATIONS:
        assert [o for _, o in found].count(op) == 1, op
    assert {load_contract().operations[op].path_template for op in OPERATIONS} <= {p for p, _ in found}
