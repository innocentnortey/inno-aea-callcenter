"""AEA-41 AC-15 (local driver): tests/contract/cases/events.py holds the server cases for `streamChatEvents`.

AEA-59's runner reads the same data later; until it lands this file drives every case through the in-process app.
Failure mode guarded: contract (each case yields the status it names, valid against the OpenAPI, and every documented
status has a case).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.api.events_support import FakeStreamStore, events_app, parse_sse_text, payload, session_of
from tests.api.openapi_check import SseFrame, assert_sse_frames_match, load_contract
from tests.api.web_shell_support import (
    ConversationRowStub,
    FakeSessionStore,
    assert_matches,
    cookie_header,
    error_body,
    make_client,
    make_settings,
    new_thread_id,
)
from tests.contract.cases.events import CASES, ROUTE_FILE


def test_events_cases_drive_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """contract (AC-15): each case produces its status; all documented statuses are covered."""
    assert ROUTE_FILE == "events"
    cases: dict[str, Any] = dict(CASES)
    assert set(cases) == {"streamChatEvents"}
    contract = load_contract()
    spec = contract.operations["streamChatEvents"]
    covered: set[str] = set()
    for case in cases["streamChatEvents"]["drives"]:
        sessions = FakeSessionStore()
        headers: dict[str, str] = {}
        token = None
        for step in case["preconditions"]:
            assert step in {"login", "started_thread"}, f"unknown precondition {step!r}"
        if "login" in case["preconditions"]:
            token = sessions.issue()
            headers = cookie_header(token)
        store = FakeStreamStore()
        started = new_thread_id()
        if "started_thread" in case["preconditions"]:
            assert token is not None
            store.rows[started] = ConversationRowStub(started, session_of(sessions, token))
        event_ids = [store.append(started, kind, payload(kind)) for kind in case.get("events", ())]
        thread = {"started": started, "unknown": new_thread_id()}.get(case["thread"], case["thread"])
        resume = case.get("last_event_id")
        if resume is not None:
            headers["Last-Event-ID"] = str(event_ids[resume["after_event"] - 1])
        app = events_app(monkeypatch, make_settings(tmp_path / case["name"]), uow=store, store=sessions)
        with make_client(app) as client:
            response = client.get(spec.path_template.replace("{thread_id}", thread), headers=headers)
        assert response.status_code == case["status"], f"{case['name']}: {response.text}"
        frames = 0
        if case["status"] == 200:
            items = [i for i in parse_sse_text(response.text) if isinstance(i, SseFrame)]
            frames = len(items)
            assert frames == case["frames"], case["name"]
            assert_sse_frames_match(items, "streamChatEvents")
            assert response.headers["cache-control"] == "no-store"
        else:
            error_body(response, case["status"], case["code"])
            assert_matches(response, "streamChatEvents")
        covered.add(str(case["status"]))
        print(f"{case['name']}: {response.status_code}, frames={frames}")
    assert covered == set(spec.responses) == {"200", "401", "404"}
