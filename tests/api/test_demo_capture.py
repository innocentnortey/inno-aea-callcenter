"""AEA-43 capture checks (AC-13, AC-17, AC-18, AC-19): one `request` record per demo call, with the status the caller
saw, the caller's role and `error_kind` on server errors only; no inbox digits in any record.

The recorded and served statuses are printed side by side (`pytest -s`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from meridian.domain.staff import DemoRole
from meridian.policy.limits import WebLimits
from meridian.services.reset_gate import ResetAlreadyRunning
from meridian.web.app import ContainerOverrides
from meridian.web.deps import get_demo_service, get_identity_service, get_reset_service
from meridian.web.middleware import RateLimiter
from tests.api.demo_support import (
    START_CLOCK,
    WALL_START,
    FakeDemoService,
    FakeIdentityService,
    FakeResetService,
    ResetDoneStub,
    ResetFailedStub,
    demo_app,
    inbox_message,
    new_digits,
    signed_in,
)
from tests.api.web_shell_support import (
    FakeHeartbeat,
    FakeSessionStore,
    MutableClock,
    app_log_text,
    assert_matches,
    captured_log,
    cookie_header,
    full_app,
    make_client,
    make_settings,
    records_of,
    reset_gate_of,
)

INBOX = "/api/demo/inbox"
STAFFING = "/api/demo/staffing"
CLOCK = "/api/demo/clock"
RESET = "/api/demo/reset"


def _show(label: str, responses: list[Any], records: list[dict[str, Any]]) -> None:
    for response, record in zip(responses, records, strict=True):
        print(f"{label} {record['route']}: response {response.status_code} record {record['status']}")


def _limiter() -> RateLimiter:
    return RateLimiter(WebLimits(reads_per_session_per_min=1, reads_per_ip_per_min=100))


def test_demo_entry_points_emit_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-13): through the real container, five calls leave five request records and the identifiers reach
    the services."""
    store = FakeSessionStore()
    app = full_app(
        monkeypatch,
        make_settings(tmp_path),
        store=store,
        heartbeat=FakeHeartbeat(),
        overrides=ContainerOverrides(wall_clock=MutableClock(WALL_START)),
    )
    identity, demo, resets = FakeIdentityService(), FakeDemoService(), FakeResetService()
    app.dependency_overrides[get_identity_service] = lambda: identity
    app.dependency_overrides[get_demo_service] = lambda: demo
    app.dependency_overrides[get_reset_service] = lambda: resets
    token = store.issue(DemoRole.SUPERVISOR, now=WALL_START)
    headers = cookie_header(token)
    with make_client(app) as client, captured_log() as stream:
        responses = [
            client.get(INBOX, headers=headers),
            client.get(STAFFING, headers=headers),
            client.put(STAFFING, json={"mode": "simulated_on_shift"}, headers=headers),
            client.get(CLOCK, headers=headers),
            client.post(RESET, json={"confirm": True}, headers=headers),
        ]
    records = records_of(stream, "request")
    _show("AC-13", responses, records)
    assert [r["route"] for r in records] == [INBOX, STAFFING, STAFFING, CLOCK, RESET]
    for response, record in zip(responses, records, strict=True):
        assert response.status_code == 200, response.text
        assert record["status"] == 200
        assert record["caller_role"] == "supervisor"
        assert record["request_id"] == response.headers["X-Request-ID"]
    (change,) = [c for c in demo.calls if c.method == "set_staffing"]
    assert str(change.kwargs["request_id"]) == responses[2].headers["X-Request-ID"]
    assert change.kwargs["role"] == DemoRole.SUPERVISOR
    ((_, reset_kwargs),) = resets.calls
    assert str(reset_kwargs["request_id"]) == responses[4].headers["X-Request-ID"]
    assert reset_kwargs["session_id"] == store.session_of(token).session_id
    assert reset_kwargs["role"] == DemoRole.SUPERVISOR


def test_wf3_inbox_login_gate_and_request_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """capture (AC-17, WF-3): inbox statuses 401, 200 per role, 429, 503, 500 are recorded as served; only the 500
    carries a class-name error_kind (the 503 names its code); no served digits in any record."""
    h = demo_app(monkeypatch, make_settings(tmp_path), limiter=_limiter())
    served: list[str] = []
    cookies: list[dict[str, str]] = []
    for role in DemoRole:
        cookie, session = signed_in(h, role)
        digits = new_digits()
        served.append(digits)
        h.identity.by_session[str(session.session_id)] = (inbox_message(digits=digits),)
        cookies.append(cookie)
    fifth, _ = signed_in(h)
    sixth, _ = signed_in(h)
    responses: list[Any] = []
    with make_client(h.app) as client, captured_log() as stream:
        responses.append(client.get(INBOX))
        assert_matches(responses[-1], "listDemoInbox")
        assert h.identity.calls == []
        for cookie in cookies:
            responses.append(client.get(INBOX, headers=cookie))
            assert_matches(responses[-1], "listDemoInbox")
        responses.append(client.get(INBOX, headers=cookies[0]))
        assert_matches(responses[-1], "listDemoInbox")
        with reset_gate_of(h.app).hold():
            responses.append(client.get(INBOX, headers=fifth))
        assert_matches(responses[-1], "listDemoInbox")
        h.identity.raises = RuntimeError("inbox down")
        responses.append(client.get(INBOX, headers=sixth))
    assert [r.status_code for r in responses] == [401, 200, 200, 200, 200, 429, 503, 500]
    records = records_of(stream, "request")
    _show("AC-17", responses, records)
    assert [r["status"] for r in records] == [r.status_code for r in responses]
    kinds = [r.get("error_kind") for r in records]
    assert kinds == [None, None, None, None, None, None, "RESET_IN_PROGRESS", "RuntimeError"]
    text = stream.getvalue() + app_log_text(caplog)
    for digits in served:
        assert digits not in text


def test_wf5_read_limits_and_request_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-18, WF-5): staffing and clock reads are limited, setStaffing never is; every status is recorded as
    served and a forced 500 carries error_kind."""
    h = demo_app(monkeypatch, make_settings(tmp_path), limiter=_limiter())
    a, _ = signed_in(h)
    b, _ = signed_in(h)
    with make_client(h.app) as client, captured_log() as stream:
        responses = [
            client.get(STAFFING, headers=a),
            client.get(STAFFING, headers=a),
            client.get(CLOCK, headers=a),
            client.put(STAFFING, json={"mode": "simulated_on_shift"}, headers=a),
            client.put(STAFFING, json={"mode": "maybe"}, headers=a),
        ]
        h.demo.staffing_raises = RuntimeError("staffing down")
        responses.append(client.get(STAFFING, headers=b))
    assert [r.status_code for r in responses] == [200, 429, 429, 200, 400, 500]
    assert_matches(responses[1], "getStaffing")
    assert_matches(responses[2], "getDemoClock")
    records = records_of(stream, "request")
    _show("AC-18", responses, records)
    assert [r["status"] for r in records] == [r.status_code for r in responses]
    assert [bool(r.get("error_kind")) for r in records] == [False, False, False, False, False, True]


def test_wf15_reset_request_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-19, WF-15): reset records 200, 400, 409 busy, 409 throttled and 500 as served; error_kind only on
    the 500."""
    done = ResetDoneStub(open_chats_ended=0, roles_reset=0, clock=START_CLOCK)
    resets = FakeResetService(outcomes=[done, ResetAlreadyRunning(), ResetFailedStub()])
    h = demo_app(monkeypatch, make_settings(tmp_path, trust_proxy_headers=True), resets=resets)
    cookie, _ = signed_in(h)
    headers = {**cookie, "X-Forwarded-For": "198.51.100.40"}
    responses: list[Any] = []
    with make_client(h.app) as client, captured_log() as stream:
        responses.append(client.post(RESET, json={"confirm": True}, headers=headers))
        responses.append(client.post(RESET, json={"confirm": False}, headers=headers))
        for _ in range(9):  # post 2 (busy), post 3 (failed), posts 4-10 (seven 200s)
            responses.append(client.post(RESET, json={"confirm": True}, headers=headers))
        responses.append(client.post(RESET, json={"confirm": True}, headers=headers))
    statuses = [r.status_code for r in responses]
    assert statuses == [200, 400, 409, 500, *[200] * 7, 409]
    records = records_of(stream, "request")
    _show("AC-19", responses, records)
    assert [r["status"] for r in records] == statuses
    assert [r["status"] for r in records if r.get("error_kind")] == [500]
    assert [r["error_kind"] for r in records if r.get("error_kind")] == ["RESET_FAILED"]
    assert len(h.resets.calls) == 10
