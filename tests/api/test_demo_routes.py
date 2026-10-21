"""AEA-43 frozen tests (risk::security, written first): the customer demo routes CON-6 to CON-9.

Every test drives AEA-23's real app and gate middleware in process with TestClient; the identity, demo and reset
services are doubles from `tests.api.demo_support` bound through dependency overrides. Each docstring names the failure
mode it guards (invariant / negative / failure-refusal) and its acceptance criterion. The routes and schemas are
imported inside the tests that need them, so this file collects before they exist.

Frozen: the implementer must not edit this file or `tests/api/demo_support.py`.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.routing import APIRoute

from meridian.domain.staff import DemoRole
from meridian.policy.limits import WebLimits
from meridian.policy.texts import TextId, render
from meridian.services.reset_gate import ResetAlreadyRunning
from meridian.web.middleware import RateLimiter
from tests.api.demo_support import (
    CODE_GONE,
    DEMO_START,
    OFF,
    ON,
    START_DATE_LABEL,
    START_LABEL,
    WALL_START,
    FakeDemoService,
    ResetFailedStub,
    demo_app,
    hold_gate_for,
    inbox_message,
    new_digits,
    signed_in,
)
from tests.api.web_shell_support import (
    FakeSessionStore,
    app_log_text,
    assert_matches,
    captured_log,
    effective_routes,
    error_body,
    make_client,
    make_settings,
    records_of,
    reset_gate_of,
)

INBOX = "/api/demo/inbox"
STAFFING = "/api/demo/staffing"
CLOCK = "/api/demo/clock"
RESET = "/api/demo/reset"


def test_inbox_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): ONE_ACTIVE, USED_AND_EXPIRED, EMPTY and code-gone bodies validate; text and order are exact."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    active, a = signed_in(h)
    used_expired, b = signed_in(h)
    empty, _ = signed_in(h)
    gone, c = signed_in(h)
    d1, d2, d3 = new_digits(), new_digits(), new_digits()
    h.identity.by_session[str(a.session_id)] = (inbox_message(digits=d1),)
    h.identity.by_session[str(b.session_id)] = (
        inbox_message(digits=d2, status="used", msg_id="msg-2", at=DEMO_START + timedelta(minutes=5)),
        inbox_message(digits=d3, status="expired", msg_id="msg-1"),
    )
    h.identity.by_session[str(c.session_id)] = (inbox_message(digits=None, status="expired"),)
    with make_client(h.app) as client:
        r = client.get(INBOX, headers=active)
        assert r.status_code == 200, r.text
        assert_matches(r, "listDemoInbox")
        (message,) = r.json()["messages"]
        assert message["body"] == render(TextId.INBOX_CODE_BODY, digits=d1)
        assert message["code"] == d1
        assert message["status"] == "active"
        assert message["to_masked"] == "···02"

        r = client.get(INBOX, headers=used_expired)
        assert r.status_code == 200, r.text
        assert_matches(r, "listDemoInbox")
        messages = r.json()["messages"]
        assert [m["id"] for m in messages] == ["msg-2", "msg-1"]
        assert [m["status"] for m in messages] == ["used", "expired"]

        r = client.get(INBOX, headers=empty)
        assert r.status_code == 200, r.text
        assert_matches(r, "listDemoInbox")
        assert r.json() == {"messages": []}

        r = client.get(INBOX, headers=gone)
        assert r.status_code == 200, r.text
        assert_matches(r, "listDemoInbox")
        (message,) = r.json()["messages"]
        assert message["body"] == render(TextId.INBOX_CODE_GONE)
        assert message["code"] == CODE_GONE
    # the demo clock, not the wall clock, is what the service is asked about
    assert h.identity.calls[0][1] == DEMO_START
    assert h.identity.calls[0][1] != WALL_START


def test_inbox_scoped_to_login_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-2): the session comes only from the login; query and header values change nothing."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    a_cookie, a = signed_in(h)
    b_cookie, b = signed_in(h)
    da, db = new_digits(), new_digits()
    h.identity.by_session[str(a.session_id)] = (inbox_message(digits=da, msg_id="msg-a"),)
    h.identity.by_session[str(b.session_id)] = (inbox_message(digits=db, msg_id="msg-b"),)
    with make_client(h.app) as client:
        ra = client.get(
            INBOX,
            params={"demo_session": str(b.session_id)},
            headers={**a_cookie, "X-Demo-Session": str(b.session_id)},
        )
        rb = client.get(INBOX, headers=b_cookie)
    assert ra.status_code == 200 and rb.status_code == 200
    assert da in ra.text and db not in ra.text
    assert db in rb.text and da not in rb.text
    assert [call[0] for call in h.identity.calls] == [str(a.session_id), str(b.session_id)]


def test_inbox_code_never_logged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-3): the digits appear only in the response body, never in a log, trace or repr."""
    from meridian.web.routes.demo import to_wire_message

    h = demo_app(monkeypatch, make_settings(tmp_path))
    cookie, session = signed_in(h)
    d = new_digits()
    message = inbox_message(digits=d)
    h.identity.by_session[str(session.session_id)] = (message,)
    caplog.set_level(logging.DEBUG)
    with captured_log() as stream, make_client(h.app) as client:
        r = client.get(INBOX, headers=cookie)
    assert r.status_code == 200, r.text
    body = r.json()["messages"][0]
    assert body["code"] == d and d in body["body"]
    assert d not in stream.getvalue()
    assert d not in app_log_text(caplog)
    for record in caplog.records:
        assert d not in repr(record.__dict__)
    assert d not in repr(message)
    wire = to_wire_message(message)
    assert d not in repr(wire)
    assert d not in str(wire.model_dump())
    assert wire.model_dump(mode="json")["code"] == d
    assert h.trace.turns == ()
    requests = records_of(stream, "request")
    assert [rec["route"] for rec in requests] == [INBOX]
    assert body["to_masked"] == "···02"


def test_staffing_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-4): getStaffing and setStaffing validate in both modes and pass the service values through."""
    settings = make_settings(tmp_path)
    h = demo_app(monkeypatch, settings, demo=FakeDemoService(staffing=OFF))
    cookie, session = signed_in(h)
    sup_cookie, sup = signed_in(h, DemoRole.SUPERVISOR)
    with make_client(h.app) as client:
        r = client.get(STAFFING, headers=cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "getStaffing")
        assert r.json() == {"mode": OFF.mode, "label": OFF.label, "banner": OFF.banner}

        r = client.put(STAFFING, json={"mode": "simulated_on_shift"}, headers=sup_cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "setStaffing")
        assert r.json()["mode"] == "simulated_on_shift"
        assert r.json()["converted_cases"] == 0
        call = [c for c in h.demo.calls if c.method == "set_staffing"][-1]
        assert call.kwargs["mode"] == "simulated_on_shift"
        assert call.kwargs["request_id"] == r.headers["X-Request-ID"]
        assert call.kwargs["role"] == DemoRole.SUPERVISOR == sup.role

        r = client.get(STAFFING, headers=cookie)
        assert_matches(r, "getStaffing")
        assert r.json() == {"mode": ON.mode, "label": ON.label, "banner": ON.banner}

        h.demo.converted_on_change = 1
        r = client.put(STAFFING, json={"mode": "nobody_online"}, headers=cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "setStaffing")
        assert r.json()["converted_cases"] == 1
        call = [c for c in h.demo.calls if c.method == "set_staffing"][-1]
        assert call.kwargs["role"] == session.role

        r = client.put(STAFFING, json={"mode": "nobody_online"}, headers=cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "setStaffing")
        assert r.json()["converted_cases"] == 0


def test_clock_is_demo_clock_and_get_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-5): the clock is the service's demo clock whatever the wall clock reads; GET is the only method."""
    from meridian.web.routes.demo import build_router

    # the session outlives the 3-day wall advance below, so only the route's clock source can change the answer
    h = demo_app(monkeypatch, make_settings(tmp_path), store=FakeSessionStore(lifetime_s=4 * 86_400))
    cookie, _ = signed_in(h)
    with make_client(h.app) as client:
        r = client.get(CLOCK, headers=cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "getDemoClock")
        first = r.json()
        assert datetime.fromisoformat(first["now"]) == DEMO_START
        assert first["now"].endswith("-05:00")
        assert first["label"] == START_LABEL
        assert first["date_label"] == START_DATE_LABEL
        h.wall.advance(3 * 86400)
        again = client.get(CLOCK, headers=cookie)
        assert again.status_code == 200, again.text
        assert again.json() == first
    methods = {
        m
        for route in build_router().routes
        if isinstance(route, APIRoute) and route.path == CLOCK
        for m in (route.methods or set())
    }
    assert methods == {"GET"}
    app_methods: set[str] = set()
    for info in effective_routes(h.app):
        if info.path == CLOCK:
            app_methods |= set(info.methods)
    assert app_methods == {"GET"}


def test_reset_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-6): a confirmed reset calls the service with the wall time and the caller, and answers 200."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    cookie, session = signed_in(h, DemoRole.REPRESENTATIVE)
    with make_client(h.app) as client:
        r = client.post(RESET, json={"confirm": True}, headers=cookie)
    assert r.status_code == 200, r.text
    assert_matches(r, "resetDemo")
    payload = r.json()
    assert payload["ok"] is True
    assert payload["open_chats_ended"] == 2
    assert payload["roles_reset"] == 1
    assert datetime.fromisoformat(payload["clock"]["now"]) == DEMO_START
    assert payload["clock"]["label"] == START_LABEL
    assert payload["clock"]["date_label"] == START_DATE_LABEL
    assert len(h.resets.calls) == 1
    now, kwargs = h.resets.calls[0]
    assert now == WALL_START
    assert kwargs["request_id"] == r.headers["X-Request-ID"]
    assert kwargs["session_id"] == session.session_id
    assert kwargs["role"] == DemoRole.REPRESENTATIVE


def test_reset_refusals(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure-refusal (AC-7): unconfirmed resets never reach the service; busy gives 409; failure gives 500."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    cookie, _ = signed_in(h)
    with make_client(h.app) as client:
        for payload in ({"confirm": False}, {}, {"confirm": 1}):
            r = client.post(RESET, json=payload, headers=cookie)
            body = error_body(r, 400, "VALIDATION_ERROR")
            assert body["error"]["field"] == "confirm", body
            assert_matches(r, "resetDemo")
        assert h.resets.calls == []

        h.resets.outcomes = [ResetAlreadyRunning()]
        r = client.post(RESET, json={"confirm": True}, headers=cookie)
        body = error_body(r, 409, "RESET_IN_PROGRESS")
        assert body["error"]["details"]["retry_after_ms"] == 5000
        assert_matches(r, "resetDemo")

        h.resets.outcomes = [ResetFailedStub()]
        r = client.post(RESET, json={"confirm": True}, headers=cookie)
        body = error_body(r, 500, "RESET_FAILED")
        assert body["error"].get("details") is None
        assert_matches(r, "resetDemo")


def test_reset_throttle_per_ip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure-refusal (AC-8): ten resets per IP per window succeed; the eleventh is a 409 that never calls the service."""
    settings = make_settings(tmp_path, trust_proxy_headers=True)
    h = demo_app(monkeypatch, settings)
    cookie, _ = signed_in(h)
    with make_client(h.app) as client:
        for _ in range(10):
            r = client.post(
                RESET, json={"confirm": True}, headers={**cookie, "X-Forwarded-For": "198.51.100.20"}
            )
            assert r.status_code == 200, r.text
        r = client.post(RESET, json={"confirm": True}, headers={**cookie, "X-Forwarded-For": "198.51.100.20"})
        body = error_body(r, 409, "RESET_IN_PROGRESS")
        assert body["error"]["details"]["retry_after_ms"] > 0
        assert_matches(r, "resetDemo")
        assert len(h.resets.calls) == 10
        r = client.post(RESET, json={"confirm": True}, headers={**cookie, "X-Forwarded-For": "203.0.113.30"})
        assert r.status_code == 200, r.text
        assert len(h.resets.calls) == 11


def test_reset_gate_answers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure-refusal (AC-9): during a reset the inbox and setStaffing answer 503; the reads wait and then answer 200."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    cookie, _ = signed_in(h)
    with make_client(h.app) as client:
        gate = reset_gate_of(h.app)
        with gate.hold():
            r = client.get(INBOX, headers=cookie)
            body = error_body(r, 503, "RESET_IN_PROGRESS")
            assert body["error"]["details"] == {"retry_after_ms": 5000}
            assert_matches(r, "listDemoInbox")
            r = client.put(STAFFING, json={"mode": "simulated_on_shift"}, headers=cookie)
            body = error_body(r, 503, "RESET_IN_PROGRESS")
            assert body["error"]["details"] == {"retry_after_ms": 5000}
            assert_matches(r, "setStaffing")
        assert h.identity.calls == []
        assert not [c for c in h.demo.calls if c.method == "set_staffing"]

        for path, operation_id, method in (
            (STAFFING, "getStaffing", "staffing"),
            (CLOCK, "getDemoClock", "clock_view"),
        ):
            hold = hold_gate_for(gate, 0.3)
            started = time.monotonic()
            r = client.get(path, headers=cookie)
            elapsed = time.monotonic() - started
            hold.thread.join()
            assert r.status_code == 200, r.text
            assert_matches(r, operation_id)
            assert hold.released_at is not None
            call = [c for c in h.demo.calls if c.method == method][-1]
            assert call.at_mono >= hold.released_at
            assert elapsed < 1.5


def test_staffing_validation_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """failure-refusal (AC-10): an unknown mode is a 400 on field mode; the rejected value is echoed nowhere."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    cookie, _ = signed_in(h)
    caplog.set_level(logging.DEBUG)
    with make_client(h.app) as client:
        r = client.put(STAFFING, json={"mode": "maybe"}, headers=cookie)
    body = error_body(r, 400, "VALIDATION_ERROR")
    assert body["error"]["field"] == "mode", body
    assert_matches(r, "setStaffing")
    assert "maybe" not in r.text
    for record in caplog.records:
        assert "maybe" not in repr(record.__dict__)
    assert not [c for c in h.demo.calls if c.method == "set_staffing"]


def test_inbox_request_rate_limited(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure-refusal (AC-11): once the read bucket is spent, the inbox answers 429 with a retry hint."""
    limiter = RateLimiter(WebLimits(reads_per_session_per_min=1, reads_per_ip_per_min=100))
    h = demo_app(monkeypatch, make_settings(tmp_path), limiter=limiter)
    cookie, _ = signed_in(h)
    with make_client(h.app) as client:
        first = client.get(INBOX, headers=cookie)
        assert first.status_code == 200, first.text
        second = client.get(INBOX, headers=cookie)
    body = error_body(second, 429, "REQUEST_RATE_LIMITED")
    assert body["error"]["details"]["retry_after_ms"] > 0
    assert_matches(second, "listDemoInbox")


def test_login_gate_and_any_role(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-12): no cookie is a 401 for every operation; every one of the four roles is let through."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    calls: tuple[tuple[str, str, str, dict[str, Any] | None], ...] = (
        ("post", RESET, "resetDemo", {"confirm": True}),
        ("get", STAFFING, "getStaffing", None),
        ("put", STAFFING, "setStaffing", {"mode": "simulated_on_shift"}),
        ("get", CLOCK, "getDemoClock", None),
    )
    with make_client(h.app) as client:
        for method, path, operation_id, payload in calls:
            r = client.request(method.upper(), path, json=payload)
            body = error_body(r, 401, "UNAUTHENTICATED")
            assert body["error"]["details"]["reason"] == "none"
            assert_matches(r, operation_id)
        assert h.resets.calls == []
        assert h.demo.calls == []
        for role in DemoRole:
            token_cookie, _ = signed_in(h, role)
            for method, path, operation_id, payload in calls:
                r = client.request(method.upper(), path, json=payload, headers=token_cookie)
                assert r.status_code == 200, (role, operation_id, r.text)
                assert_matches(r, operation_id)


def test_inbox_code_gone_is_expired(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-14): a message with no code is always shown expired with dots; a held code keeps its status."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    cookie, session = signed_in(h)
    d = new_digits()
    h.identity.by_session[str(session.session_id)] = (
        inbox_message(digits=None, status="active", msg_id="msg-2"),
        inbox_message(digits=d, status="active", msg_id="msg-1"),
    )
    with make_client(h.app) as client:
        r = client.get(INBOX, headers=cookie)
    assert r.status_code == 200, r.text
    assert_matches(r, "listDemoInbox")
    first, second = r.json()["messages"]
    assert first["status"] == "expired"
    assert first["code"] == CODE_GONE
    assert first["body"] == render(TextId.INBOX_CODE_GONE)
    assert second["status"] == "active"
    assert second["code"] == d
