"""AEA-43 mock-level flows for AC-16 (J-3 inbox legs, J-8 reset leg) and the AC-14 status rule (R3-2).

Not journey files: the harness forbids TestClient and doubles under tests/journeys/. The same flows on the real app
are tests/journeys/j3/test_aea_43.py and tests/journeys/j8/test_aea_43.py (skipped `blocked-on` until their needs land).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from meridian.policy.texts import TextId, render
from meridian.web.routes.demo import to_wire_message
from tests.api.demo_support import (
    CODE_GONE,
    DEMO_START,
    OFF,
    START_CLOCK,
    START_DATE_LABEL,
    START_LABEL,
    ClockViewStub,
    FakeDemoService,
    FakeResetService,
    demo_app,
    inbox_message,
    new_digits,
    signed_in,
)
from tests.api.web_shell_support import assert_matches, make_client, make_settings

INBOX = "/api/demo/inbox"
STAFFING = "/api/demo/staffing"
CLOCK = "/api/demo/clock"
RESET = "/api/demo/reset"


def test_wp2_inbox_active_then_used_and_second_reviewer_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """invariant (AC-16, WP-2): the inbox shows an active code, then the same message used with dots; a second login
    sees nothing; reset answers the start clock."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    a_cookie, a = signed_in(h)
    b_cookie, _ = signed_in(h)
    d = new_digits()
    h.identity.by_session[str(a.session_id)] = (inbox_message(digits=d, status="active"),)
    with make_client(h.app) as client:
        r = client.get(INBOX, headers=a_cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "listDemoInbox")
        (message,) = r.json()["messages"]
        assert message["status"] == "active"
        assert message["code"] == d
        assert message["body"] == render(TextId.INBOX_CODE_BODY, digits=d)
        assert message["to_masked"] == "···02"
        assert datetime.fromisoformat(message["expires_at"]) - datetime.fromisoformat(
            message["at"]
        ) == timedelta(minutes=10)

        r = client.get(INBOX, headers=b_cookie)
        assert r.json() == {"messages": []}
        assert_matches(r, "listDemoInbox")

        h.identity.by_session[str(a.session_id)] = (inbox_message(digits=None, status="used"),)
        r = client.get(INBOX, headers=a_cookie)
        assert_matches(r, "listDemoInbox")
        (message,) = r.json()["messages"]
        assert message["status"] == "used"
        assert message["code"] == CODE_GONE
        assert message["body"] == render(TextId.INBOX_CODE_GONE)
        assert d not in r.text

        r = client.post(RESET, json={"confirm": True}, headers=a_cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "resetDemo")
        assert r.json()["clock"]["date_label"] == START_DATE_LABEL


def test_inbox_code_gone_keeps_used_and_expired(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-14, R3-2): dots are never active; used and expired keep their status."""
    h = demo_app(monkeypatch, make_settings(tmp_path))
    cookie, session = signed_in(h)
    h.identity.by_session[str(session.session_id)] = (
        inbox_message(digits=None, status="used", msg_id="msg-3"),
        inbox_message(digits=None, status="expired", msg_id="msg-2"),
        inbox_message(digits=None, status="active", msg_id="msg-1"),
    )
    with make_client(h.app) as client:
        r = client.get(INBOX, headers=cookie)
    assert r.status_code == 200, r.text
    assert_matches(r, "listDemoInbox")
    messages = r.json()["messages"]
    assert [m["status"] for m in messages] == ["used", "expired", "expired"]
    assert all(m["code"] == CODE_GONE for m in messages)
    assert all(m["body"] == render(TextId.INBOX_CODE_GONE) for m in messages)
    assert to_wire_message(inbox_message(digits=None, status="used")).status == "used"


class LinkedResetService(FakeResetService):
    """Stands in for the real reset's effect on the demo double: staffing off, clock at DEMO_START."""

    def __init__(self, demo: FakeDemoService) -> None:
        super().__init__()
        self._demo = demo

    def reset(self, now: datetime, *, request_id: object, session_id: object, role: object) -> object:
        result = super().reset(now, request_id=request_id, session_id=session_id, role=role)
        self._demo.current_mode = OFF.mode
        self._demo.clock = START_CLOCK
        return result


def test_j8_reset_returns_staffing_and_clock_to_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """invariant (AC-16, J-8): after a reset, staffing reads back at nobody online and the clock at the start."""
    demo = FakeDemoService(staffing=OFF)
    h = demo_app(monkeypatch, make_settings(tmp_path), demo=demo, resets=LinkedResetService(demo))
    cookie, _ = signed_in(h)
    with make_client(h.app) as client:
        r = client.put(STAFFING, json={"mode": "simulated_on_shift"}, headers=cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "setStaffing")
        demo.clock = ClockViewStub(
            DEMO_START + timedelta(days=3), "Mon Oct 19, 2026 · 10:00 am", "Mon Oct 19, 2026 (demo date)"
        )
        r = client.get(CLOCK, headers=cookie)
        assert r.json()["label"] == "Mon Oct 19, 2026 · 10:00 am"
        assert_matches(r, "getDemoClock")

        r = client.post(RESET, json={"confirm": True}, headers=cookie)
        assert r.status_code == 200, r.text
        assert_matches(r, "resetDemo")

        r = client.get(STAFFING, headers=cookie)
        assert_matches(r, "getStaffing")
        assert r.json()["mode"] == "nobody_online"
        assert r.json()["banner"] is None
        r = client.get(CLOCK, headers=cookie)
        assert_matches(r, "getDemoClock")
        body = r.json()
        assert (body["label"], body["date_label"]) == (START_LABEL, START_DATE_LABEL)
        assert datetime.fromisoformat(body["now"]) == DEMO_START
