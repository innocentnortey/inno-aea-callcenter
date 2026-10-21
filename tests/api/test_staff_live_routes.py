"""AEA-46 CON-14 liveChatAction and the CON-21 gates: AC-9 to AC-12, AC-18, PA-4."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import anyio
import pytest

from meridian.domain.staff import DemoRole
from meridian.services.live_chat import LiveRefused, LiveView
from meridian.web.routes import staff_live
from tests.api.staff_live_support import (
    RecordingLiveChat,
    app_uow,
    close_stream,
    events_url,
    live_url,
    open_stream,
    running,
    staff_live_app,
)
from tests.api.web_shell_support import (
    FakeSessionStore,
    app_log_text,
    assert_matches,
    cookie_header,
    error_body,
    make_client,
    rand_word,
)
from tests.services.live_chat_support import (
    JOIN_AT,
    SECOND_REF,
    STAFF_TEXT,
    UNKNOWN_REF,
    WP2_REF,
    seed_live_case,
)

LIVE = live_url(str(WP2_REF))
JOINED = LiveView(controller_kind="human", controller_name="Riley", state="joined", since=JOIN_AT)


def _rep(store: FakeSessionStore) -> dict[str, str]:
    return cookie_header(store.issue(DemoRole.REPRESENTATIVE))


def test_live_action_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-9: JOINED, SENT, HANDED_BACK and CLOSED bodies validate against the OpenAPI."""
    store = FakeSessionStore()
    app = staff_live_app(monkeypatch, tmp_path, store=store)
    with make_client(app) as client:
        seed_live_case(app_uow(app))
        seed_live_case(app_uow(app), case_ref=SECOND_REF)
        headers = _rep(store)
        calls = [
            (WP2_REF, {"action": "join"}),
            (WP2_REF, {"action": "send", "text": STAFF_TEXT}),
            (WP2_REF, {"action": "hand_back"}),
            (SECOND_REF, {"action": "join"}),
            (SECOND_REF, {"action": "close"}),
        ]
        states = []
        for ref, body in calls:
            response = client.post(live_url(str(ref)), json=body, headers=headers)
            assert response.status_code == 200, response.text
            assert_matches(response, "liveChatAction")
            states.append(response.json()["live"]["state"])
        print("live.state values:", states)
        assert states == ["joined", "joined", "handed_back", "joined", "closed"]


def test_live_action_refusals(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-10: each LiveRefused maps to its status and a valid ApiError; an unknown action is a 400."""
    store = FakeSessionStore()
    double = RecordingLiveChat(JOINED)
    app = staff_live_app(monkeypatch, tmp_path, store=store, live_chat=double)
    cases = [
        (LiveRefused(code="CASE_NOT_FOUND", details={"reference": "MHC-C-0099"}), 404),
        (LiveRefused(code="NOT_CLAIMED_BY_YOU", details={"owner": None}), 403),
        (
            LiveRefused(
                code="CASE_ALREADY_CLAIMED",
                details={"claimed_by": "Demo supervisor", "claimed_at": "2026-10-16T14:20:00-05:00"},
            ),
            409,
        ),
        (LiveRefused(code="NOT_LIVE", details={"reason": "not_joined"}), 409),
    ]
    with make_client(app) as client:
        headers = _rep(store)
        for refusal, status in cases:
            double.result = refusal
            response = client.post(LIVE, json={"action": "join"}, headers=headers)
            body = error_body(response, status, refusal.code)
            assert_matches(response, "liveChatAction")
            if refusal.code == "NOT_CLAIMED_BY_YOU":
                assert body["error"]["details"]["owner"] is None
        count = len(double.calls)
        response = client.post(LIVE, json={"action": "wave"}, headers=headers)
        body = error_body(response, 400, "VALIDATION_ERROR")
        assert body["error"]["field"] == "action"
        assert_matches(response, "liveChatAction")
        assert len(double.calls) == count


def test_unknown_case_through_real_service(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """PA-1 at route level: the route is reachable through the real container and answers an ApiError."""
    store = FakeSessionStore()
    app = staff_live_app(monkeypatch, tmp_path, store=store)
    with make_client(app) as client:
        response = client.post(live_url(str(UNKNOWN_REF)), json={"action": "join"}, headers=_rep(store))
        error_body(response, 404, "CASE_NOT_FOUND")
        assert_matches(response, "liveChatAction")
        assert "detail" not in response.json()


def test_text_rules(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-11: text rules give 400 on field text with the constraint; no service call; text is never echoed."""
    store = FakeSessionStore()
    double = RecordingLiveChat(JOINED)
    app = staff_live_app(monkeypatch, tmp_path, store=store, live_chat=double)
    caplog.set_level(logging.DEBUG)
    secret = rand_word(20, "zqjoin")
    long_text = "q" * 2001
    cases: list[tuple[dict[str, Any], str]] = [
        ({"action": "send", "text": None}, "required for send"),
        ({"action": "send", "text": "   "}, "required for send"),
        ({"action": "send", "text": long_text}, "at most 2000 characters"),
        ({"action": "join", "text": secret}, "only for send"),
    ]
    with make_client(app) as client:
        headers = _rep(store)
        for payload, constraint in cases:
            response = client.post(LIVE, json=payload, headers=headers)
            body = error_body(response, 400, "VALIDATION_ERROR")
            assert (body["error"]["field"], body["error"]["constraint"]) == ("text", constraint)
            assert_matches(response, "liveChatAction")
            assert secret not in response.text and long_text not in response.text
    assert double.calls == []
    assert secret not in app_log_text(caplog) and long_text not in app_log_text(caplog)


def test_live_roles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-12: live is representative only; the stream is representative, supervisor or owner."""
    store = FakeSessionStore()
    double = RecordingLiveChat(JOINED)
    app = staff_live_app(monkeypatch, tmp_path, store=store, live_chat=double)
    reads: list[object] = []
    original = staff_live.read_case_events

    def counting(*args: Any) -> Any:
        reads.append(args)
        return original(*args)

    monkeypatch.setattr(staff_live, "read_case_events", counting)
    with make_client(app) as client:
        seed_live_case(app_uow(app))
        for role in (DemoRole.CUSTOMER, DemoRole.SUPERVISOR, DemoRole.OWNER):
            response = client.post(LIVE, json={"action": "join"}, headers=cookie_header(store.issue(role)))
            body = error_body(response, 403, "ROLE_NOT_ALLOWED")
            assert body["error"]["details"]["needs"] == ["representative"]
            assert_matches(response, "liveChatAction")
        customer = client.get(events_url(str(WP2_REF)), headers=cookie_header(store.issue(DemoRole.CUSTOMER)))
        body = error_body(customer, 403, "ROLE_NOT_ALLOWED")
        assert body["error"]["details"]["needs"] == ["representative", "supervisor", "owner"]
        assert_matches(customer, "streamCaseEvents")
        assert double.calls == [] and reads == []

    async def scenario() -> None:
        async with running(app) as tg:
            for role in (DemoRole.REPRESENTATIVE, DemoRole.SUPERVISOR, DemoRole.OWNER):
                handle = await open_stream(tg, app, events_url(str(WP2_REF)), token=store.issue(role))
                assert handle.status == 200
                await close_stream(handle)

    anyio.run(scenario)


def test_login_gate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-18: no session cookie gives 401 UNAUTHENTICATED on both operations (real middleware)."""
    app = staff_live_app(monkeypatch, tmp_path, store=FakeSessionStore())
    with make_client(app) as client:
        post = client.post(LIVE, json={"action": "join"})
        error_body(post, 401, "UNAUTHENTICATED")
        assert_matches(post, "liveChatAction")
        get = client.get(events_url(str(WP2_REF)))
        error_body(get, 401, "UNAUTHENTICATED")
        assert_matches(get, "streamCaseEvents")


def test_malformed_reference_is_not_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """PA-4: a malformed reference is 404 CASE_NOT_FOUND with no details on both operations."""
    store = FakeSessionStore()
    app = staff_live_app(monkeypatch, tmp_path, store=store)
    with make_client(app) as client:
        headers = _rep(store)
        for response, op in (
            (client.post(live_url("mhc-c-7"), json={"action": "join"}, headers=headers), "liveChatAction"),
            (client.get(events_url("mhc-c-7"), headers=headers), "streamCaseEvents"),
        ):
            body = error_body(response, 404, "CASE_NOT_FOUND")
            assert body["error"].get("details") is None
            assert_matches(response, op)
