"""AEA-23 AC-12 to AC-16: rate limits, client IP, the eval run tag and the eval key's absence from every output.

Failure modes guarded: invariant (who is limited, who never is, the 20-conversation load shape, the eval key rule),
boundary (a spoofed forwarding header when proxies are not trusted), negative (the eval key and run id never leak).
"""

from __future__ import annotations

import hmac
import logging
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr
from starlette.datastructures import Headers

from meridian.policy.limits import WebLimits
from meridian.web.app import ContainerOverrides
from meridian.web.middleware import (
    EVAL_KEY_HEADER,
    RATE_LIMITED_READ_OPERATIONS,
    RUN_ID_HEADER,
    RUN_TAG_HEADER,
    SUBMIT_TURN_OPERATION,
    RateLimiter,
    client_ip_of,
    limit_verdict,
    run_tag_of,
)
from tests.api.openapi_check import load_contract
from tests.api.web_shell_support import (
    FakeSessionStore,
    RecordingTraceSink,
    add_probe_route,
    all_output_text,
    app_log_text,
    assert_matches,
    captured_log,
    cookie_header,
    make_client,
    make_settings,
    new_thread_id,
    quiet_endpoint,
    rand_word,
    web_app,
)

READ_OPERATIONS = sorted(RATE_LIMITED_READ_OPERATIONS)


def _probe_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, limits: WebLimits, **settings_changes: Any
) -> Any:
    store = FakeSessionStore()
    app = web_app(
        monkeypatch,
        make_settings(tmp_path, **settings_changes),
        store=store,
        limiter=RateLimiter(limits),
    )
    return app, store


def test_rate_limits_by_operation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-12): six reads get 429; requestPerson never; submitTurn is never 429 but exposes its verdict."""
    small = WebLimits(reads_per_session_per_min=3, reads_per_ip_per_min=1000)
    app, store = _probe_app(monkeypatch, tmp_path / "reads", small)
    for operation in READ_OPERATIONS:
        add_probe_route(app, operation)
    add_probe_route(app, "requestPerson")
    add_probe_route(app, "submitTurn")
    contract = load_contract()
    with make_client(app) as client:
        for operation in READ_OPERATIONS:
            spec = contract.operations[operation]
            headers = cookie_header(
                store.issue()
            )  # one session per operation: the read bucket is per session
            path = spec.path_template
            statuses = [
                client.request(spec.method.upper(), path, headers=headers).status_code for _ in range(3)
            ]
            assert statuses == [200, 200, 200], f"{operation}: {statuses}"
            limited = client.request(spec.method.upper(), path, headers=headers)
            assert limited.status_code == 429, operation
            body = limited.json()
            assert body["error"]["code"] == "REQUEST_RATE_LIMITED"
            assert body["error"]["details"]["retry_after_ms"] >= 1000
            assert_matches(limited, operation)
        print(f"six read operations limited: {READ_OPERATIONS}")

        # requestPerson is never limited, however many calls: even with the session's read bucket empty.
        exhausted = cookie_header(store.issue())
        thread = new_thread_id()
        outcomes = {
            client.post(f"/api/chat/sessions/{thread}/handoff", json={}, headers=exhausted).status_code
            for _ in range(40)
        }
        assert outcomes == {200}

    # submitTurn: never 429 from the middleware; the first refusing scope is in the request context (thread, session, ip).
    for label, limits, expected in (
        ("thread", WebLimits(chat_turns_per_thread_per_min=1), "thread"),
        (
            "session",
            WebLimits(chat_turns_per_thread_per_min=100, chat_turns_per_session_per_min=1),
            "session",
        ),
        (
            "ip",
            WebLimits(
                chat_turns_per_thread_per_min=100,
                chat_turns_per_session_per_min=100,
                chat_turns_per_ip_per_min=1,
            ),
            "ip",
        ),
    ):
        turn_app, turn_store = _probe_app(monkeypatch, tmp_path / label, limits)
        add_probe_route(turn_app, "submitTurn")
        with make_client(turn_app) as client:
            if label == "ip":
                first = client.post(
                    f"/api/chat/sessions/{new_thread_id()}/turns",
                    json={},
                    headers=cookie_header(turn_store.issue()),
                )
                second = client.post(
                    f"/api/chat/sessions/{new_thread_id()}/turns",
                    json={},
                    headers=cookie_header(turn_store.issue()),
                )
            else:
                headers = cookie_header(turn_store.issue())
                same = new_thread_id()
                first = client.post(f"/api/chat/sessions/{same}/turns", json={}, headers=headers)
                other = same if label == "thread" else new_thread_id()
                second = client.post(f"/api/chat/sessions/{other}/turns", json={}, headers=headers)
        assert first.status_code == 200 and second.status_code == 200, (first.text, second.text)
        assert first.json()["turn_verdict"]["allowed"] is True
        verdict = second.json()["turn_verdict"]
        print(f"submitTurn second call, {label} limit: {verdict}")
        assert verdict["allowed"] is False and verdict["scope"] == expected
        assert verdict["retry_after_ms"] >= 1000

    # Order: thread, then session, then ip, when more than one refuses.
    both, both_store = _probe_app(
        monkeypatch,
        tmp_path / "order",
        WebLimits(
            chat_turns_per_thread_per_min=1, chat_turns_per_session_per_min=1, chat_turns_per_ip_per_min=1
        ),
    )
    add_probe_route(both, "submitTurn")
    with make_client(both) as client:
        headers = cookie_header(both_store.issue())
        thread = new_thread_id()
        client.post(f"/api/chat/sessions/{thread}/turns", json={}, headers=headers)
        refused = client.post(f"/api/chat/sessions/{thread}/turns", json={}, headers=headers)
    assert refused.json()["turn_verdict"]["scope"] == "thread"

    # A read operation's probe carries no turn verdict.
    plain, plain_store = _probe_app(monkeypatch, tmp_path / "plain", WebLimits())
    add_probe_route(plain, "listDemoInbox")
    with make_client(plain) as client:
        assert (
            client.get("/api/demo/inbox", headers=cookie_header(plain_store.issue())).json()["turn_verdict"]
            is None
        )
    assert SUBMIT_TURN_OPERATION == "submitTurn"


def test_limits_admit_twenty_conversations_from_one_ip_and_login() -> None:
    """invariant (AC-13): 20 conversations from one IP and one login at about 255 turns a minute are never limited."""
    limiter = RateLimiter(WebLimits())
    threads = [new_thread_id() for _ in range(20)]
    start = 1_000_000.0
    verdicts = [
        limit_verdict(
            limiter, "startChatSession", thread_id="", session_id="one-login", ip="203.0.113.5", now=start
        )
        for _ in threads
    ]
    turns_per_minute, minutes = 255, 5
    step = 60.0 / turns_per_minute
    for index in range(turns_per_minute * minutes):
        verdicts.append(
            limit_verdict(
                limiter,
                "submitTurn",
                thread_id=threads[index % 20],
                session_id="one-login",
                ip="203.0.113.5",
                now=start + index * step,
            )
        )
    classified = [v for v in verdicts if v is not None]
    limited = [v for v in classified if not v.allowed]
    print(f"{len(classified)} classified calls, {len(limited)} limited")
    assert len(classified) == 20 + turns_per_minute * minutes
    assert limited == []


def _scope(headers: list[tuple[bytes, bytes]], peer: str | None) -> dict[str, Any]:
    return {"type": "http", "headers": headers, "client": (peer, 1234) if peer else None}


def test_client_ip_and_bucket_keys(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """boundary + invariant (AC-14): last forwarded entry when trusted, the peer otherwise; no token in a bucket key."""
    forwarded = [(b"x-forwarded-for", b"1.1.1.1, 2.2.2.2 ,  3.3.3.3 ")]
    assert client_ip_of(_scope(forwarded, "10.0.0.9"), trust_proxy_headers=True) == "3.3.3.3"
    assert client_ip_of(_scope(forwarded, "10.0.0.9"), trust_proxy_headers=False) == "10.0.0.9"
    assert client_ip_of(_scope([], "10.0.0.9"), trust_proxy_headers=True) == "10.0.0.9"

    limiter = RateLimiter(WebLimits())
    store = FakeSessionStore()
    for trusted in (True, False):
        app = web_app(
            monkeypatch,
            make_settings(tmp_path / str(trusted), trust_proxy_headers=trusted),
            store=store,
            limiter=limiter,
        )
        add_probe_route(app, "listDemoInbox")
        add_probe_route(app, "submitTurn")
        token = store.issue()
        with make_client(app, peer="198.51.100.7") as client:
            sent = {"X-Forwarded-For": "9.9.9.9, 8.8.8.8", **cookie_header(token)}
            ip = client.get("/api/demo/inbox", headers=sent).json()["client_ip"]
            assert ip == ("8.8.8.8" if trusted else "198.51.100.7"), (trusted, ip)
            client.post(f"/api/chat/sessions/{new_thread_id()}/turns", json={}, headers=sent)
        assert all(token not in str(part) for key in limiter.bucket_keys() for part in key), (
            "a bucket is keyed by the cookie"
        )
    keys = limiter.bucket_keys()
    print(f"bucket keys: {sorted(map(str, keys))[:6]}")
    assert keys
    assert not [k for k in keys if any(token in str(part) for token in store.live_tokens() for part in k)]


def test_run_tag_requires_eval_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-15): eval or load only with the matching key (compare_digest); six sub-cases, pure and over HTTP."""
    key = rand_word(18, "ev")
    secret = SecretStr(key)
    run = rand_word(10, "run")
    cases: list[tuple[str, dict[str, str], SecretStr | None, tuple[str, str | None]]] = [
        ("no key", {RUN_ID_HEADER: run}, secret, ("live", None)),
        ("wrong key", {EVAL_KEY_HEADER: rand_word(18, "ev"), RUN_ID_HEADER: run}, secret, ("live", None)),
        ("key unset", {EVAL_KEY_HEADER: key, RUN_ID_HEADER: run}, None, ("live", None)),
        ("eval", {EVAL_KEY_HEADER: key, RUN_TAG_HEADER: "eval", RUN_ID_HEADER: run}, secret, ("eval", run)),
        ("load", {EVAL_KEY_HEADER: key, RUN_TAG_HEADER: "load", RUN_ID_HEADER: run}, secret, ("load", run)),
        (
            "unknown tag",
            {EVAL_KEY_HEADER: key, RUN_TAG_HEADER: "banana", RUN_ID_HEADER: run},
            secret,
            ("eval", run),
        ),
    ]
    real = hmac.compare_digest
    calls: list[int] = []

    def spy(a: Any, b: Any) -> bool:
        calls.append(1)
        return real(a, b)

    for label, sent, configured, expected in cases:
        calls.clear()
        monkeypatch.setattr(hmac, "compare_digest", spy)
        assert run_tag_of(Headers(headers=sent), configured) == expected, label
        monkeypatch.setattr(hmac, "compare_digest", real)
        if EVAL_KEY_HEADER in sent and configured is not None:
            assert calls, f"{label}: the key must be compared with hmac.compare_digest"

    # Over HTTP, through the request context.
    for label, sent, configured, expected in cases:
        settings = make_settings(
            tmp_path / label.replace(" ", "-"), eval_key=configured.get_secret_value() if configured else None
        )
        store = FakeSessionStore()
        app = web_app(monkeypatch, settings, store=store)
        add_probe_route(app, "listDemoInbox")
        with make_client(app) as client:
            seen = client.get("/api/demo/inbox", headers={**sent, **cookie_header(store.issue())}).json()
        print(f"{label}: run_tag {seen['run_tag']}, run_id present {seen['run_id'] is not None}")
        assert (seen["run_tag"], seen["run_id"]) == expected, label

    # A matching key with no run id header: tagged, but no run id.
    assert run_tag_of(Headers(headers={EVAL_KEY_HEADER: key}), secret) == ("eval", None)


def test_eval_key_absent_from_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-16): the eval key and a run id sent without the key appear in no body, log or trace."""
    key = rand_word(18, "evk")
    run_without_key, run_with_key = rand_word(14, "rwo"), rand_word(14, "rwk")
    sink = RecordingTraceSink()
    store = FakeSessionStore()
    app = web_app(
        monkeypatch,
        make_settings(tmp_path, eval_key=key),
        store=store,
        overrides=ContainerOverrides(trace=sink),
    )
    add_probe_route(app, "listDemoInbox", endpoint=quiet_endpoint)
    token = store.issue()
    caplog.set_level(logging.DEBUG)
    with make_client(app) as client, captured_log() as stream:
        responses = [
            client.get("/api/demo/inbox", headers={RUN_ID_HEADER: run_without_key, **cookie_header(token)}),
            client.get(
                "/api/demo/inbox",
                headers={EVAL_KEY_HEADER: key, RUN_ID_HEADER: run_with_key, **cookie_header(token)},
            ),
            client.get(
                "/api/demo/inbox", headers={EVAL_KEY_HEADER: rand_word(18), RUN_ID_HEADER: run_without_key}
            ),
            client.post("/api/logout", headers={EVAL_KEY_HEADER: key, RUN_ID_HEADER: run_with_key}),
        ]
    assert [r.status_code for r in responses] == [200, 200, 401, 401]
    sinks = {
        "response bodies and headers": all_output_text(responses),
        "log": stream.getvalue() + app_log_text(caplog),
        "trace sink": "\n".join(sink.seen),
    }
    for sink_name, text in sinks.items():
        for label, value in (
            ("eval key", key),
            ("run id without key", run_without_key),
            ("run id with key", run_with_key),
        ):
            assert value not in text, f"{label} leaked into {sink_name}"
