"""AEA-44 AC-1 to AC-6, AC-8, AC-10, AC-15, AC-17 and the ticket's example pair: CON-10 routes over the real
StaffSessionStore through AEA-23's real middleware (frozen with the AEA-44 tests).

Failure modes guarded: invariant (role cards, switch persists, no cookie on switch, providers share one store),
refusal (admin role, no session, gate held, tampered/expired cookie, role matrix, role_reset), negative (no token,
username, password or session secret in any output). Temp SQLite copies; no `.env`, no paid call. AEA-44's modules are
imported inside the tests so the suite collects before they exist.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from meridian.domain.staff import DemoRole, LoginSession, LoginSessionId, RoleRefusal, StaffRole
from meridian.policy.limits import Limits
from meridian.web.container import Container, ContainerError, register_staff_session
from tests.api.openapi_check import load_contract
from tests.api.staff_session_support import (
    ROLE_NAMES,
    WALL_T0,
    CountingUow,
    StaffHarness,
    container_app,
    example,
    login_token,
    make_store,
    run_reset,
    staff_app,
    staff_rows,
    switch,
    tab,
    without_signed_in_at,
)
from tests.api.web_shell_support import (
    all_output_text,
    app_log_text,
    assert_matches,
    captured_log,
    demo_pair,
    error_body,
    make_client,
    make_settings,
    records_of,
    request_for,
    reset_gate_of,
    session_cookie_value,
    set_cookie_lines,
)
from tests.fixtures.sqlite import TempStore, temp_sqlite

QUEUE = load_contract().operations["getQueue"].path_template
OWNER_METRICS = load_contract().operations["getOwnerMetrics"].path_template


@pytest.fixture
def db() -> Iterator[TempStore]:
    with temp_sqlite() as store:
        yield store


@pytest.fixture
def h(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, db: TempStore) -> StaffHarness:
    return staff_app(monkeypatch, tmp_path, db)


def _expected(role: str) -> dict[str, Any]:
    return without_signed_in_at(example("switchRole", f"TO_{role.upper()}"))


# -- AC-1 ---------------------------------------------------------------------------------------------------------
def test_get_session_matches_openapi(h: StaffHarness) -> None:
    """invariant (AC-1): four roles validate and equal the examples; signed_in_at is the demo reading, not wall time."""
    with make_client(h.app) as client:
        for role in ROLE_NAMES:
            token = login_token(client, h.settings)
            if role != "customer":
                assert switch(client, token, role).status_code == 200
            response = client.get("/api/session", headers=tab(token))
            assert response.status_code == 200, response.text
            assert_matches(response, "getSession")
            body = response.json()
            assert without_signed_in_at(body) == _expected(role), role
            signed_in = datetime.fromisoformat(body["signed_in_at"])
            assert signed_in == h.demo.now()
            assert signed_in != WALL_T0
    assert without_signed_in_at(example("getSession", "CUSTOMER")) == _expected("customer")
    assert without_signed_in_at(example("getSession", "REPRESENTATIVE")) == _expected("representative")


# -- AC-2 ---------------------------------------------------------------------------------------------------------
def test_list_demo_roles(h: StaffHarness) -> None:
    """invariant (AC-2): the four roles in order with the ROLES example lines, for customer and for staff."""
    with make_client(h.app) as client:
        token = login_token(client, h.settings)
        response = client.get("/api/session/roles", headers=tab(token))
        assert response.status_code == 200, response.text
        assert_matches(response, "listDemoRoles")
        assert response.json() == example("listDemoRoles", "ROLES")
        assert [r["role"] for r in response.json()["roles"]] == list(ROLE_NAMES)

        assert switch(client, token, "representative").status_code == 200
        as_rep = client.get("/api/session/roles", headers=tab(token))
        assert as_rep.status_code == 200 and as_rep.json() == example("listDemoRoles", "ROLES")


# -- AC-3 ---------------------------------------------------------------------------------------------------------
def test_switch_role_persists_on_session(h: StaffHarness) -> None:
    """invariant (AC-3): each switch returns the TO_* shape and both tabs on the same cookie read the new role."""
    with make_client(h.app) as client:
        token = login_token(client, h.settings)
        second_tab = make_client(h.app)  # a second client; the lifespan is already running
        for role in ("representative", "supervisor", "owner", "customer"):
            response = switch(client, token, role)
            assert response.status_code == 200, response.text
            assert_matches(response, "switchRole")
            assert without_signed_in_at(response.json()) == _expected(role)
            for who in (client, second_tab):
                seen = who.get("/api/session", headers=tab(token))
                assert seen.status_code == 200 and seen.json()["role"] == role
            print(f"switch -> {role}: both tabs read {role}")


# -- AC-4 ---------------------------------------------------------------------------------------------------------
def test_switch_sets_no_cookie(h: StaffHarness) -> None:
    """invariant (AC-4): a switch sends no Set-Cookie and the same token keeps working."""
    with make_client(h.app) as client:
        token = login_token(client, h.settings)
        response = switch(client, token, "supervisor")
        assert response.status_code == 200
        assert set_cookie_lines(response) == []
        assert client.get("/api/session", headers=tab(token)).status_code == 200


# -- AC-5 ---------------------------------------------------------------------------------------------------------
def test_switch_role_refusals(
    h: StaffHarness, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """refusal (AC-5): admin -> 400 without the value; no session -> 401; gate held -> 503 and the store is not called."""
    from meridian.services.staff import StaffSessionStore

    calls: list[object] = []

    def spy(self: object, session_id: object, role: object) -> object:
        calls.append((session_id, role))
        raise AssertionError("switch_role must not be called on a refused request")

    monkeypatch.setattr(StaffSessionStore, "switch_role", spy)
    caplog.set_level(logging.DEBUG)
    with make_client(h.app) as client, captured_log() as stream:
        token = login_token(client, h.settings)

        bad = client.put("/api/session/role", json={"role": "admin"}, headers=tab(token))
        body = error_body(bad, 400, "VALIDATION_ERROR")
        assert body["error"]["field"] == "role"
        assert_matches(bad, "switchRole")

        anonymous = client.put("/api/session/role", json={"role": "representative"})
        unauth = error_body(anonymous, 401, "UNAUTHENTICATED")
        assert unauth["error"]["details"] == {"reason": "none"}
        assert_matches(anonymous, "switchRole")

        with reset_gate_of(h.app).hold():
            held = client.put("/api/session/role", json={"role": "representative"}, headers=tab(token))
        busy = error_body(held, 503, "RESET_IN_PROGRESS")
        assert busy["error"]["details"]["retry_after_ms"] == 5000
        assert_matches(held, "switchRole")

        for text in (bad.text, app_log_text(caplog), stream.getvalue()):
            assert "admin" not in text, "the rejected role value leaked"
    assert calls == [], "the store was called on a refused request"
    assert staff_rows(h.db.uow)[0]["role"] == "customer"


# -- AC-6 ---------------------------------------------------------------------------------------------------------
def test_tampered_and_expired_cookie_401(h: StaffHarness) -> None:
    """refusal (AC-6): altered, blank and absent cookies -> reason none; past the lifetime -> reason expired."""
    with make_client(h.app) as client:
        token = login_token(client, h.settings)
        control = client.get("/api/session", headers=tab(token))
        assert control.status_code == 200
        assert_matches(control, "getSession")

        flipped = token[:-1] + ("A" if token[-1] != "A" else "B")
        for label, response in (
            ("flipped", client.get("/api/session", headers=tab(flipped))),
            ("blank", client.get("/api/session", headers={"Cookie": "mhc_session="})),
            ("absent", client.get("/api/session")),
        ):
            body = error_body(response, 401, "UNAUTHENTICATED")
            assert body["error"]["details"] == {"reason": "none"}, label
            assert_matches(response, "getSession")

        h.wall.advance(43_200)
        expired = client.get("/api/session", headers=tab(token))
        body = error_body(expired, 401, "UNAUTHENTICATED")
        assert body["error"]["details"] == {"reason": "expired"}
        assert_matches(expired, "getSession")
        cleared = [line for line in set_cookie_lines(expired) if line.startswith("mhc_session=")]
        assert len(cleared) == 1 and "max-age=0" in cleared[0].lower(), set_cookie_lines(expired)
        assert staff_rows(h.db.uow) == []

        again = client.get("/api/session", headers=tab(token))
        assert error_body(again, 401, "UNAUTHENTICATED")["error"]["details"] == {"reason": "none"}


# -- AC-8 ---------------------------------------------------------------------------------------------------------
def test_require_staff_matrix(h: StaffHarness) -> None:
    """refusal (AC-8): 401 never 403 without a session; 403 names role, needs in x-roles order, reason; personas."""
    rep_sup = ["representative", "supervisor"]
    owner_sup = ["owner", "supervisor"]
    with make_client(h.app) as client:
        anonymous = client.get(QUEUE)
        assert error_body(anonymous, 401, "UNAUTHENTICATED")["error"]["details"] == {"reason": "none"}

        token = login_token(client, h.settings)
        denied = client.get(QUEUE, headers=tab(token))
        details = error_body(denied, 403, "ROLE_NOT_ALLOWED")["error"]["details"]
        assert details == {"role": "customer", "needs": rep_sup, "reason": "wrong_role"}
        assert_matches(denied, "getQueue")
        denied_owner = client.get(OWNER_METRICS, headers=tab(token))
        owner_details = error_body(denied_owner, 403, "ROLE_NOT_ALLOWED")["error"]["details"]
        assert owner_details == {"role": "customer", "needs": owner_sup, "reason": "wrong_role"}
        assert_matches(denied_owner, "getOwnerMetrics")

        assert switch(client, token, "supervisor").status_code == 200
        for path in (QUEUE, OWNER_METRICS):
            ok = client.get(path, headers=tab(token))
            assert ok.status_code == 200, ok.text
            assert ok.json() == {
                "role": "supervisor",
                "name": "Demo supervisor",
                "signature": "Demo supervisor",
            }

        assert switch(client, token, "representative").status_code == 200
        queue = client.get(QUEUE, headers=tab(token))
        assert queue.json() == {"role": "representative", "name": "Riley", "signature": "Riley (demo)"}
        rep_owner = client.get(OWNER_METRICS, headers=tab(token))
        assert error_body(rep_owner, 403, "ROLE_NOT_ALLOWED")["error"]["details"]["needs"] == owner_sup
        assert_matches(rep_owner, "getOwnerMetrics")

        assert switch(client, token, "owner").status_code == 200
        owner_queue = client.get(QUEUE, headers=tab(token))
        assert error_body(owner_queue, 403, "ROLE_NOT_ALLOWED")["error"]["details"]["role"] == "owner"
        assert_matches(owner_queue, "getQueue")
        owner_ok = client.get(OWNER_METRICS, headers=tab(token))
        assert owner_ok.status_code == 200 and owner_ok.json()["name"] == "Demo business owner"

    counting = CountingUow()
    store = make_store(counting, secret=SecretStr("zqsecretplaceholderletters"))
    expiry = WALL_T0
    session_id = LoginSessionId("00000000-0000-4000-8000-000000000001")
    rep_session = LoginSession(
        session_id=session_id,
        role=DemoRole.REPRESENTATIVE,
        role_reset=False,
        signed_in_at=expiry,
        expires_at=expiry,
    )
    wrong = store.actor_for(rep_session, (StaffRole.SUPERVISOR,))
    assert isinstance(wrong, RoleRefusal) and wrong.reason == "wrong_role"
    reset_session = rep_session.model_copy(update={"role": DemoRole.CUSTOMER, "role_reset": True})
    reset = store.actor_for(reset_session, (StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR))
    assert isinstance(reset, RoleRefusal) and reset.reason == "role_reset"
    assert counting.calls == 0, "actor_for made a unit-of-work call"


# -- AC-10 --------------------------------------------------------------------------------------------------------
def test_no_secret_in_any_output(h: StaffHarness, caplog: pytest.LogCaptureFixture) -> None:
    """negative (AC-10): token, username, password and session secret appear in no body, log, record, span or column."""
    from meridian.web.schemas.auth import SessionInfo

    caplog.set_level(logging.DEBUG)
    pair = demo_pair(h.settings)
    secrets_under_test = {
        "username": pair["username"],
        "password": pair["password"],
        "session_secret": h.settings.session_secret.get_secret_value(),
    }
    with make_client(h.app) as client, captured_log() as stream:
        logged_in = client.post("/api/login", json=pair)
        assert logged_in.status_code == 200
        token = session_cookie_value(logged_in)
        assert token
        client.cookies.clear()
        secrets_under_test["token"] = token
        responses = [logged_in]
        info = client.get("/api/session", headers=tab(token))
        switched = switch(client, token, "representative")
        queue = client.get(QUEUE, headers=tab(token))
        roles = client.get("/api/session/roles", headers=tab(token))
        responses += [info, switched, queue, roles]
        assert [r.status_code for r in responses] == [200] * 5

        expected_keys = {"authenticated", "role", "display_name", "sees", "signed_in_at"}
        assert set(info.json()) == expected_keys and set(switched.json()) == expected_keys
        assert set(SessionInfo.model_fields) == expected_keys

        haystacks = {
            "bodies and headers": all_output_text(responses, skip_set_cookie=True),
            "captured log": stream.getvalue(),
            "request records": repr(records_of(stream, "request")),
            "app log": app_log_text(caplog),
            "trace double": "".join(h.trace.seen),
            "staff_sessions": " ".join(str(v) for row in staff_rows(h.db.uow) for v in row.values()),
        }
    for name, value in secrets_under_test.items():
        for where, text in haystacks.items():
            assert value not in text, f"{name} leaked into {where}"


# -- AC-15 --------------------------------------------------------------------------------------------------------
def test_register_staff_binds_providers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-15): one StaffSessionStore for both providers (lifetime 43,200), a FlagService, hunk filled in."""
    from meridian.services.staff import FlagService, StaffSessionStore
    from meridian.web.deps import (
        FLAG_SERVICE,
        LOGIN_SESSIONS,
        STAFF_ACCESS,
        get_login_sessions,
        get_staff_access,
    )

    built = container_app(monkeypatch, tmp_path)
    with make_client(built.app):
        container = built.app.state.container
        sessions = container.get(LOGIN_SESSIONS)
        access = container.get(STAFF_ACCESS)
        assert sessions is access
        assert isinstance(sessions, StaffSessionStore)
        assert sessions.lifetime_s == 43_200
        assert isinstance(container.get(FLAG_SERVICE), FlagService)
        from_request: object = get_login_sessions(request_for(built.app))
        assert from_request is get_staff_access(request_for(built.app))

    bare = Container(settings=make_settings(tmp_path / "bare"), limits=Limits())
    register_staff_session(bare, FastAPI(), settings=make_settings(tmp_path / "bare"), limits=Limits())
    bare.build()
    with pytest.raises(ContainerError):
        bare.get(LOGIN_SESSIONS)

    doc = register_staff_session.__doc__ or ""
    assert "AEA-44" in doc and "No-op until" not in doc


# -- AC-17 --------------------------------------------------------------------------------------------------------
def test_role_reread_after_switch_and_reset(h: StaffHarness) -> None:
    """failure/refusal (AC-17): a tab can always re-read its role; after a reset every staff call says role_reset."""
    lines: list[str] = []

    def note(label: str, response: Any) -> None:
        reason = ""
        if response.status_code == 403:
            reason = response.json()["error"]["details"]["reason"]
        elif response.status_code == 200 and "role" in response.json():
            reason = response.json()["role"]
        lines.append(f"{label} {response.status_code} {reason}")

    with make_client(h.app) as client:
        token = login_token(client, h.settings)
        tab_b = make_client(h.app)
        for role in ROLE_NAMES:
            assert switch(client, token, role).status_code == 200
            for path in ("/api/session", "/api/session/roles"):
                response = client.get(path, headers=tab(token))
                assert response.status_code == 200, f"{path} as {role}"

        assert switch(tab_b, token, "representative").status_code == 200
        seen = client.get("/api/session", headers=tab(token))
        assert seen.json()["role"] == "representative", "tab A did not see tab B's switch"
        note("A getSession", seen)

        assert run_reset(h.db.uow) == 1
        for round_number in range(3):
            for label, who in (("A", client), ("B", tab_b)):
                denied = who.get(QUEUE, headers=tab(token))
                details = error_body(denied, 403, "ROLE_NOT_ALLOWED")["error"]["details"]
                assert details == {
                    "role": "customer",
                    "needs": ["representative", "supervisor"],
                    "reason": "role_reset",
                }, f"{label} call {round_number + 1}"
                note(f"{label} queue #{round_number + 1}", denied)
                info = who.get("/api/session", headers=tab(token))
                assert info.status_code == 200 and info.json()["role"] == "customer"
                note(f"{label} getSession", info)
                assert who.get("/api/session/roles", headers=tab(token)).status_code == 200

        assert switch(tab_b, token, "representative").status_code == 200
        for who in (client, tab_b):
            granted = who.get(QUEUE, headers=tab(token))
            assert granted.status_code == 200 and granted.json()["name"] == "Riley"
            note("after switch queue", granted)
    print("\n".join(lines))


# -- example pair -------------------------------------------------------------------------------------------------
def test_example_pair_switch_to_representative(h: StaffHarness) -> None:
    """invariant (ticket example pair): customer -> representative -> Riley acts -> reset -> role_reset, getSession customer."""
    with make_client(h.app) as client:
        logged_in = client.post("/api/login", json=demo_pair(h.settings))
        assert logged_in.status_code == 200
        token = session_cookie_value(logged_in)
        assert token
        client.cookies.clear()
        login_signed_in = datetime.fromisoformat(logged_in.json()["session"]["signed_in_at"])

        before = client.get(QUEUE, headers=tab(token))
        assert error_body(before, 403, "ROLE_NOT_ALLOWED")["error"]["details"] == {
            "role": "customer",
            "needs": ["representative", "supervisor"],
            "reason": "wrong_role",
        }

        switched = switch(client, token, "representative")
        assert switched.status_code == 200, switched.text
        assert_matches(switched, "switchRole")
        assert without_signed_in_at(switched.json()) == _expected("representative")
        assert datetime.fromisoformat(switched.json()["signed_in_at"]) == login_signed_in
        assert set_cookie_lines(switched) == []

        after = client.get(QUEUE, headers=tab(token))
        assert after.status_code == 200
        assert after.json() == {"role": "representative", "name": "Riley", "signature": "Riley (demo)"}

        assert run_reset(h.db.uow) == 1
        reset = client.get(QUEUE, headers=tab(token))
        assert error_body(reset, 403, "ROLE_NOT_ALLOWED")["error"]["details"]["reason"] == "role_reset"
        now = client.get("/api/session", headers=tab(token))
        assert now.status_code == 200 and now.json()["role"] == "customer"
