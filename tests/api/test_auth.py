"""AEA-23 AC-4 to AC-8, AC-22, AC-25, AC-32: demo login and logout (CON-22, WF-18, CAP-10).

Failure modes guarded: invariant (cookie attributes, logout), refusal (one body for every wrong pair, malformed body,
throttle), negative (no credential or token in any output), capture (CAP-10 records, status values, no outbound call).
"""

from __future__ import annotations

import hmac
import logging
import socket
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from meridian.policy.limits import WebLimits
from meridian.web.app import ContainerOverrides
from tests.api.web_shell_support import (
    FakeSessionStore,
    MutableClock,
    RecordingTraceSink,
    all_output_text,
    app_log_text,
    assert_matches,
    captured_log,
    cookie_attributes,
    cookie_header,
    demo_pair,
    error_body,
    log_records,
    login,
    make_client,
    make_settings,
    rand_word,
    records_of,
    session_cookie_value,
    set_cookie_lines,
    web_app,
    without_request_id,
)

T0 = datetime(2031, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_login_success_sets_session_cookie(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-4): 200 LoginResponse, the cookie attributes for both cookie_secure values, end before start."""
    for secure in (False, True):
        settings = make_settings(tmp_path / str(secure), cookie_secure=secure)
        store = FakeSessionStore()
        app = web_app(monkeypatch, settings, store=store)
        with make_client(app) as client:
            response = login(client, settings)
            assert response.status_code == 200, response.text
            assert_matches(response, "login")
            body = response.json()
            assert body["session"]["role"] == "customer"
            assert body["session"]["authenticated"] is True
            assert body["landing"] == "/"
            pair = demo_pair(settings)
            assert pair["username"] not in response.text and pair["password"] not in response.text

            lines = [line for line in set_cookie_lines(response) if line.startswith("mhc_session=")]
            assert len(lines) == 1, set_cookie_lines(response)
            attributes = cookie_attributes(lines[0])
            assert attributes["mhc_session"] == store.issued_tokens[-1]
            assert attributes["path"] == "/"
            assert "httponly" in attributes
            assert attributes["samesite"] == "Lax"
            assert attributes["max-age"] == "43200"
            assert ("secure" in attributes) is secure
            print(f"cookie_secure={secure}: attributes {sorted(k for k in attributes if k != 'mhc_session')}")

            # A login over a still-valid cookie ends the old session before starting the new one.
            old = store.issue()
            store.calls.clear()
            again = login(client, settings, headers=cookie_header(old))
            assert again.status_code == 200
            order = [name for name, _ in store.calls if name in {"end", "start"}]
            assert order == ["end", "start"], store.calls
            assert store.ended_tokens == [old]

            # An unknown cookie is not a session: nothing to end.
            store.calls.clear()
            store.ended_tokens.clear()
            login(client, settings, headers=cookie_header("tok-not-issued-by-anyone"))
            assert [name for name, _ in store.calls if name == "end"] == []


def test_login_failed_identical_for_every_cause(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """refusal (AC-5): five causes, one body; both comparisons run on every attempt."""
    settings = make_settings(tmp_path)
    pair = demo_pair(settings)
    app = web_app(monkeypatch, settings)
    attempts = {
        "wrong username": {"username": rand_word(8), "password": pair["password"]},
        "wrong password": {"username": pair["username"], "password": rand_word(8)},
        "both wrong": {"username": rand_word(8), "password": rand_word(8)},
        "empty username": {"username": "", "password": pair["password"]},
        "empty password": {"username": pair["username"], "password": ""},
    }
    real = hmac.compare_digest
    counts: list[int] = []

    def spy(a: Any, b: Any) -> bool:
        counts.append(1)
        return real(a, b)

    bodies: dict[str, dict[str, Any]] = {}
    with make_client(app) as client:
        monkeypatch.setattr(hmac, "compare_digest", spy)
        for label, credentials in attempts.items():
            counts.clear()
            response = client.post("/api/login", json=credentials)
            body = error_body(response, 401, "LOGIN_FAILED")
            assert body["error"]["field"] is None
            assert body["error"]["constraint"] is None
            assert body["error"]["details"] is None
            assert_matches(response, "login")
            assert not [line for line in set_cookie_lines(response) if line.startswith("mhc_session=")]
            assert len(counts) == 2, f"{label}: {len(counts)} comparisons"
            bodies[label] = without_request_id(response)
    first = next(iter(bodies.values()))
    assert all(body == first for body in bodies.values()), bodies
    print(f"five bodies equal; comparisons per attempt: 2 ({sorted(bodies)})")


def test_login_malformed_body_is_400(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """boundary (AC-6): missing field, non-string field and non-JSON text give 400 naming the field, never the value."""
    settings = make_settings(tmp_path)
    app = web_app(monkeypatch, settings)
    seeded = rand_word(18)
    with make_client(app) as client:
        missing = client.post("/api/login", json={"username": seeded})
        body = error_body(missing, 400, "VALIDATION_ERROR")
        assert body["error"]["field"] == "password"
        assert body["error"]["constraint"]

        non_string = client.post("/api/login", json={"username": "someone", "password": [seeded]})
        body = error_body(non_string, 400, "VALIDATION_ERROR")
        assert body["error"]["field"] == "password"
        assert body["error"]["constraint"]

        not_json = client.post(
            "/api/login", content=f"not json {seeded}", headers={"Content-Type": "application/json"}
        )
        body = error_body(not_json, 400, "VALIDATION_ERROR")
        assert body["error"]["field"]
        assert body["error"]["constraint"]

        for response in (missing, non_string, not_json):
            assert_matches(response, "login")
            assert seeded not in response.text


def test_login_rate_limited_per_ip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """refusal (AC-7): after login_rejects_per_ip rejects in the window, even the right pair gets 429 for that IP only."""
    limits = WebLimits()
    settings = make_settings(tmp_path, trust_proxy_headers=True)
    clock = MutableClock(T0)
    app = web_app(monkeypatch, settings, overrides=ContainerOverrides(wall_clock=clock))
    ip_a = {"X-Forwarded-For": "198.51.100.1"}
    ip_b = {"X-Forwarded-For": "198.51.100.2"}
    with make_client(app) as client, captured_log() as stream:
        for _ in range(limits.login_rejects_per_ip):
            wrong = client.post(
                "/api/login", json={**demo_pair(settings), "password": rand_word(8)}, headers=ip_a
            )
            error_body(wrong, 401, "LOGIN_FAILED")
        limited = login(client, settings, headers=ip_a)
        body = error_body(limited, 429, "LOGIN_RATE_LIMITED")
        assert_matches(limited, "login")
        retry_after = int(limited.headers["Retry-After"])
        assert retry_after >= 1
        assert body["error"]["details"]["retry_after_ms"] >= 1000
        assert body["error"]["details"]["retry_after_ms"] // 1000 == retry_after
        print(f"429: Retry-After {retry_after}, retry_after_ms {body['error']['details']['retry_after_ms']}")

        other = login(client, settings, headers=ip_b)
        assert other.status_code == 200, "a different IP must still log in"

        clock.advance(limits.login_reject_window_s + 1)
        after_window = login(client, settings, headers=ip_a)
        assert after_window.status_code == 200, "the pair works again once the window has passed"
    events = records_of(stream, "auth_event")
    assert [e["outcome"] for e in events].count("rate_limited") == 1
    assert [e["outcome"] for e in events][: limits.login_rejects_per_ip] == [
        "rejected"
    ] * limits.login_rejects_per_ip


def test_credentials_and_token_absent_from_body_log_span_db(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-8): username, password (right or wrong), token and session secret appear in no sink."""
    settings = make_settings(tmp_path, trust_proxy_headers=True)
    pair = demo_pair(settings)
    wrong_user, wrong_password = rand_word(12, "zqu"), rand_word(12, "zqp")
    sink = RecordingTraceSink()
    store = FakeSessionStore()
    app = web_app(monkeypatch, settings, store=store, overrides=ContainerOverrides(trace=sink))
    caplog.set_level(logging.DEBUG)
    responses = []
    with make_client(app) as client, captured_log() as stream:
        ok = login(client, settings, headers={"X-Forwarded-For": "198.51.100.30"})
        responses.append(ok)
        token = session_cookie_value(ok)
        assert token
        responses.append(
            client.post(
                "/api/login",
                json={"username": wrong_user, "password": pair["password"]},
                headers={"X-Forwarded-For": "198.51.100.31"},
            )
        )
        for _ in range(WebLimits().login_rejects_per_ip - 1):
            responses.append(
                client.post(
                    "/api/login",
                    json={"username": pair["username"], "password": wrong_password},
                    headers={"X-Forwarded-For": "198.51.100.31"},
                )
            )
        limited = login(client, settings, headers={"X-Forwarded-For": "198.51.100.31"})
        assert limited.status_code == 429
        responses.append(limited)
        responses.append(client.post("/api/logout", headers=cookie_header(token)))

    # The one Set-Cookie that carries the token is the only place the token may appear.
    leaves_token_out = all_output_text(responses[1:])
    leaves_token_out += "\n" + all_output_text(responses[:1], skip_set_cookie=True)
    log_text = stream.getvalue() + "\n" + app_log_text(caplog)
    span_text = "\n".join(sink.seen)
    db_text = ""
    db_files = (
        [p for pattern in ("*.sqlite", "*.db") for p in settings.data_dir.rglob(pattern)]
        if settings.data_dir.exists()
        else []
    )
    for path in db_files:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            db_text += "\n".join(connection.iterdump())
        finally:
            connection.close()
    secrets = {
        "username": pair["username"],
        "password": pair["password"],
        "wrong username": wrong_user,
        "wrong password": wrong_password,
        "session secret": settings.session_secret.get_secret_value(),
        "token": token,
    }
    sinks = {
        "response bodies and headers": leaves_token_out,
        "log": log_text,
        "trace sink": span_text,
        "db dump": db_text,
    }
    for sink_name, text in sinks.items():
        for label, value in secrets.items():
            assert value not in text, f"{label} leaked into {sink_name}"
    print(
        f"absence asserted for {len(secrets)} values in {len(sinks)} sinks; sqlite files dumped: {len(db_files)}"
    )


def test_logout_clears_cookie_and_ends_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-22): 204, cookie cleared, session ended; the old cookie then gets 401; a second end is harmless."""
    settings = make_settings(tmp_path)
    store = FakeSessionStore()
    app = web_app(monkeypatch, settings, store=store)
    with make_client(app) as client:
        token = session_cookie_value(login(client, settings))
        assert token
        out = client.post("/api/logout", headers=cookie_header(token))
        assert out.status_code == 204
        assert out.content == b""
        assert_matches(out, "logout")
        cleared = [line for line in set_cookie_lines(out) if line.startswith("mhc_session=")]
        assert cleared and cookie_attributes(cleared[0])["max-age"] == "0"
        assert store.ended_tokens == [token]

        again = client.post("/api/logout", headers=cookie_header(token))
        body = error_body(again, 401, "UNAUTHENTICATED")
        assert body["error"]["details"] == {"reason": "none"}
        assert_matches(again, "logout")

    # Two tabs log out at once: the store has not forgotten the token yet, so both reach the route and both get 204.
    twin_store = FakeSessionStore(end_invalidates=False)
    twin_app = web_app(monkeypatch, make_settings(tmp_path / "twin"), store=twin_store)
    with make_client(twin_app) as client:
        token = twin_store.issue()
        first = client.post("/api/logout", headers=cookie_header(token))
        second = client.post("/api/logout", headers=cookie_header(token))
        assert (first.status_code, second.status_code) == (204, 204)
        assert twin_store.ended_tokens == [token, token]


def test_cap10_login_records_captured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-25): CAP-10's order gives four request records and three auth_events with web section 10's fields."""
    settings = make_settings(tmp_path)
    pair = demo_pair(settings)
    store = FakeSessionStore()
    app = web_app(monkeypatch, settings, store=store)
    with make_client(app) as client, captured_log() as stream:
        right = login(client, settings)
        token = session_cookie_value(right)
        assert token
        wrong = client.post("/api/login", json={**pair, "password": rand_word(10)})
        out = client.post("/api/logout", headers=cookie_header(token))
        client.cookies.clear()
        refused = client.post("/api/logout")
    assert (right.status_code, wrong.status_code, out.status_code, refused.status_code) == (
        200,
        401,
        204,
        401,
    )
    error_body(refused, 401, "UNAUTHENTICATED")

    requests = records_of(stream, "request")
    events = records_of(stream, "auth_event")
    assert len(requests) == 4 and len(events) == 3, log_records(stream)
    request_fields = {"record", "request_id", "route", "status", "duration_ms", "caller_role", "thread_id"}
    for record in requests:
        assert set(record) == request_fields, record
    assert [r["route"] for r in requests] == ["/api/login", "/api/login", "/api/logout", "/api/logout"]
    assert [r["status"] for r in requests] == [200, 401, 204, 401]
    assert [r["request_id"] for r in requests] == [
        r.headers["X-Request-ID"] for r in (right, wrong, out, refused)
    ]
    assert requests[2]["caller_role"] == "customer"
    assert requests[3]["caller_role"] == "anonymous"

    event_fields = {"record", "request_id", "outcome", "session_id", "at"}
    for event in events:
        assert set(event) == event_fields, event
    assert [e["outcome"] for e in events] == ["ok", "rejected", "logged_out"]
    assert events[0]["session_id"] and events[0]["session_id"] == events[2]["session_id"]
    assert events[1]["session_id"] is None
    assert [e["request_id"] for e in events] == [r["request_id"] for r in requests[:3]]
    everything = stream.getvalue()
    for value in (pair["username"], pair["password"], token):
        assert value not in everything
    print(
        f"request records {[(r['route'], r['status']) for r in requests]}; auth outcomes {[e['outcome'] for e in events]}"
    )


def test_wf18_status_values_and_no_outbound(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-32): record status equals response status, error_kind only on 5xx, no outbound connection."""
    settings = make_settings(tmp_path)
    pair = demo_pair(settings)
    store = FakeSessionStore()
    app = web_app(monkeypatch, settings, store=store)

    outbound: list[Any] = []
    real_connect = socket.socket.connect
    real_create = socket.create_connection
    loopback = {"127.0.0.1", "::1", "localhost"}

    def guarded_connect(self: socket.socket, address: Any) -> Any:
        if isinstance(address, tuple) and address[0] not in loopback:
            outbound.append(address)
            raise AssertionError(f"outbound connect to {address[0]}")
        return real_connect(self, address)

    def guarded_create(address: Any, *args: Any, **kwargs: Any) -> Any:
        if address[0] not in loopback:
            outbound.append(address)
            raise AssertionError(f"outbound connect to {address[0]}")
        return real_create(address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_create)

    responses = []
    with make_client(app) as client, captured_log() as stream:
        right = login(client, settings)
        responses.append(right)
        token = session_cookie_value(right)
        assert token
        responses.append(client.post("/api/logout", headers=cookie_header(token)))
        responses.append(client.post("/api/login", json={**pair, "password": rand_word(10)}))
        responses.append(client.post("/api/login", json={"username": "someone"}))
        store.fail_on_start = True
        forced = login(client, settings)
        responses.append(forced)
        store.fail_on_start = False
        for _ in range(WebLimits().login_rejects_per_ip + 2):
            responses.append(client.post("/api/login", json={**pair, "password": rand_word(10)}))
        assert 429 in [r.status_code for r in responses]

    assert forced.status_code == 500
    assert forced.headers["X-Request-ID"]
    assert forced.json() == {"request_id": forced.headers["X-Request-ID"]}

    requests = records_of(stream, "request")
    assert len(requests) == len(responses)
    triples = []
    for response, record in zip(responses, requests, strict=True):
        triples.append((response.status_code, record["status"], record.get("error_kind")))
        assert record["status"] == response.status_code
        assert record["request_id"] == response.headers["X-Request-ID"]
        if response.status_code >= 500:
            assert record.get("error_kind"), record
        else:
            assert "error_kind" not in record, record
    print(f"(response status, record status, error_kind): {triples}")
    assert outbound == []
