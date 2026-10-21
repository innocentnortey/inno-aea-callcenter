"""AEA-42 CON-4 `requestPerson` and CON-5 `saveFollowUp` through the real app, middleware and hunk (doubles for siblings).

Synthetic data only. The seeded customer's contact values are read from the temp DB copy at run time and are only ever
asserted absent.
"""

from __future__ import annotations

import inspect
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from meridian.domain.common import TurnId
from meridian.domain.handoff import HandoffReason, HandoffRequest
from meridian.domain.staff import DemoRole
from meridian.policy.handoff import priority_for, promise_for
from meridian.policy.limits import WebLimits
from meridian.services.person_request import PersonRequestService
from meridian.web.middleware import LimitScope, RateLimiter
from tests.api.handoff_support import (
    FOLLOW_UP_PATH,
    HANDOFF_PATH,
    HandoffHarness,
    customer_token,
    handoff_app,
    request_example,
    session_id_of,
    thread_for,
)
from tests.api.web_shell_support import (
    app_log_text,
    assert_matches,
    cookie_header,
    error_body,
    make_client,
    without_request_id,
)
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.person_request_support import (
    NOW,
    WALL_T0,
    customer_contact,
    end_thread,
    open_thread,
    verify_thread,
)

BUTTON = request_example(HANDOFF_PATH, "post", "BUTTON")
PHONE_MORNINGS = request_example(FOLLOW_UP_PATH, "put", "PHONE_MORNINGS")
EMAIL_GENERAL = request_example(FOLLOW_UP_PATH, "put", "EMAIL_GENERAL")


def _new_turn() -> dict[str, str]:
    return {"turn_id": str(uuid.uuid4())}


def _post(client: TestClient, token: str, thread: str, body: Any = None) -> Any:
    return client.post(
        HANDOFF_PATH.format(thread_id=thread),
        json=body if body is not None else _new_turn(),
        headers=cookie_header(token),
    )


def _put(client: TestClient, token: str, thread: str, body: Any) -> Any:
    return client.put(FOLLOW_UP_PATH.format(thread_id=thread), json=body, headers=cookie_header(token))


def _count(db: TempStore, sql: str, *params: object) -> int:
    conn = sqlite3.connect(db.db_path)
    try:
        return int(conn.execute(sql, params).fetchone()[0])
    finally:
        conn.close()


def test_request_person_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): one 200 body per result value validates against the OpenAPI."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path / "a", db)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            created = _post(client, token, thread)
            again = _post(client, token, thread)
        assert created.status_code == 200 and created.json()["result"] == "case_created"
        assert created.json()["block"]["type"] == "handoff"
        assert again.json()["result"] == "already_open"
        assert_matches(created, "requestPerson")
        assert_matches(again, "requestPerson")
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path / "b", db, presence="simulated_on_shift")
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            live = _post(client, token, thread)
        assert live.json()["result"] == "live_queued" and live.json()["block"]["type"] == "live_queued"
        assert_matches(live, "requestPerson")
        print("results:", created.json()["result"], live.json()["result"], again.json()["result"])


def test_request_person_passes_handoff_request(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-3, WF-2): the request and the context the HandoffService double received."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = thread_for(h, token)
        verify_thread(db, thread)
        body = _new_turn()
        with make_client(h.app) as client:
            resp = _post(client, token, str(thread), body)
        assert resp.status_code == 200
        (req, ctx) = h.handoff.calls[0]
        assert str(req.thread_id) == str(thread)
        assert str(req.turn_id) == body["turn_id"]
        assert req.reason is HandoffReason.CUSTOMER_REQUESTED_PERSON
        assert req.priority == priority_for(HandoffReason.CUSTOMER_REQUESTED_PERSON)
        assert (req.rule_id, req.trigger) == ("CON4.person", "con4")
        assert req.identity.status == "verified"
        assert ctx.intake is None
        assert ctx.now == NOW
        assert ctx.demo_session == session_id_of(h, token)
        assert ctx.ids.request_id == resp.headers["X-Request-ID"]
        assert ctx.span.trace_id == h.trace.turns[0].trace_id


def test_request_person_idempotent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-4): same body twice is identical; a new turn id is already_open; two turn rows after three presses."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        first_body = _new_turn()
        with make_client(h.app) as client:
            first = _post(client, token, thread, first_body)
            same = _post(client, token, thread, first_body)
            third = _post(client, token, thread)
        assert same.json() == first.json()
        assert _count(db, "SELECT COUNT(*) FROM turns WHERE thread_id = ?", thread) == 2
        assert third.json()["result"] == "already_open"
        assert third.json()["block"]["reference"] == first.json()["block"]["reference"]
        assert _count(db, "SELECT COUNT(*) FROM cases WHERE thread_id = ?", thread) == 1


def test_person_key_never_limited(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-6, WF-2): exhausted session and IP buckets still answer 200; no limiter argument exists."""
    limiter = RateLimiter(
        WebLimits(
            chat_turns_per_session_per_min=1,
            chat_turns_per_ip_per_min=1,
            reads_per_session_per_min=1,
            reads_per_ip_per_min=1,
        )
    )
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db, limiter=limiter)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        mono = WALL_T0.timestamp()
        sid = session_id_of(h, token)
        for family in ("turn", "read"):
            for scope, key in ((LimitScope.SESSION, sid), (LimitScope.IP, "198.51.100.7")):
                for _ in range(5):
                    limiter.check(scope, key, mono, family=family)
                assert not limiter.peek(scope, key, mono, family=family).allowed
        with make_client(h.app) as client:
            resp = _post(client, token, thread)
        assert resp.status_code == 200 and resp.json()["result"] == "case_created"
        assert list(inspect.signature(PersonRequestService.__init__).parameters) == [
            "self",
            "uow",
            "handoff",
            "composer",
            "trace",
            "demo_clock",
            "wall_clock",
        ]


def test_handoff_failed_503(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-7): open raising gives 503 HANDOFF_FAILED with retry_after_ms, no reference, turn not completed."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db, handoff_fails=True)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        body = _new_turn()
        with make_client(h.app) as client:
            resp = _post(client, token, thread, body)
        data = error_body(resp, 503, "HANDOFF_FAILED")
        assert data["error"]["details"]["retry_after_ms"] > 0
        assert "MHC-C-" not in resp.text
        assert_matches(resp, "requestPerson")
        with db.uow() as tx:
            row = tx.core.turns.get(TurnId(body["turn_id"]))
        assert row is not None and row.status != "completed"


def test_session_not_found_identical(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-8): malformed, unknown and foreign thread ids answer the identical 404 on both operations."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        other = customer_token(h)
        foreign = str(open_thread(db, demo_session=session_id_of(h, other)))
        ids = ["thr_9d41", str(uuid.uuid4()), foreign]
        with make_client(h.app) as client:
            posts = [_post(client, token, t) for t in ids]
            puts = [_put(client, token, t, EMAIL_GENERAL) for t in ids]
        for group in (posts, puts):
            bodies = []
            for resp in group:
                error_body(resp, 404, "SESSION_NOT_FOUND")
                bodies.append(without_request_id(resp))
            assert bodies[0] == bodies[1] == bodies[2]
        assert _count(db, "SELECT COUNT(*) FROM turns") == 0
        assert _count(db, "SELECT COUNT(*) FROM followups") == 0
        assert _count(db, "SELECT COUNT(*) FROM cases WHERE thread_id = ?", foreign) == 0


def test_session_ended_410(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-9): a thread this session lost to a demo reset answers 410 SESSION_ENDED on both operations."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        ended = end_thread(db, demo_session=session_id_of(h, token))
        with make_client(h.app) as client:
            post = _post(client, token, ended)
            put = _put(client, token, ended, EMAIL_GENERAL)
        for resp, op in ((post, "requestPerson"), (put, "saveFollowUp")):
            data = error_body(resp, 410, "SESSION_ENDED")
            assert data["error"]["details"]["reason"] == "demo_reset"
            assert_matches(resp, op)


def test_follow_up_without_case_409(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-10): no open case gives 409 no_open_case and set_followup is never called."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            resp = _put(client, token, thread, EMAIL_GENERAL)
        data = error_body(resp, 409, "NOT_ALLOWED_IN_STATE")
        assert data["error"]["details"] == {"state": "no_open_case"}
        assert_matches(resp, "saveFollowUp")
        assert [c for c in h.cases.calls if c[0] == "set_followup"] == []


def test_unverified_on_record_refused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (AC-11): unverified plus on_record is refused before any service call; general saves."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            assert _post(client, token, thread).status_code == 200
            h.cases.calls.clear()
            refused = _put(client, token, thread, PHONE_MORNINGS)
            assert h.cases.calls == []
            assert _count(db, "SELECT COUNT(*) FROM followups") == 0
            saved = _put(client, token, thread, EMAIL_GENERAL)
        data = error_body(refused, 409, "NOT_ALLOWED_IN_STATE")
        assert data["error"]["details"] == {"state": "not_verified"}
        assert saved.status_code == 200
        assert [c[0] for c in h.cases.calls].count("set_followup") == 1
        assert _count(db, "SELECT COUNT(*) FROM followups") == 1


def _verified_with_case(h: HandoffHarness, client: TestClient) -> tuple[str, str]:
    token = customer_token(h)
    thread = thread_for(h, token)
    verify_thread(h.db, thread)
    assert _post(client, token, str(thread)).status_code == 200
    return token, str(thread)


def test_save_follow_up_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-12): 200 validates; followup is set_followup's return; called with the demo clock's now."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        with make_client(h.app) as client:
            token, thread = _verified_with_case(h, client)
            resp = _put(client, token, thread, PHONE_MORNINGS)
        assert resp.status_code == 200
        assert_matches(resp, "saveFollowUp")
        followup = resp.json()["followup"]
        assert followup["destination_label"] == "the number ending in 02"
        assert followup["saved_line"] == "Follow-up saved: phone call, the number ending in 02, mornings."
        (_name, (_thread, choice, now)) = next(c for c in h.cases.calls if c[0] == "set_followup")
        assert now == NOW and h.demo.calls == 1
        assert choice.model_dump() == PHONE_MORNINGS  # type: ignore[attr-defined]


def test_both_responses_carry_settled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-13, WF-2): both operations carry the panel, with the verified action and the same reference."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        with make_client(h.app) as client:
            token = customer_token(h)
            thread = thread_for(h, token)
            verify_thread(db, thread)
            post = _post(client, token, str(thread))
            put = _put(client, token, str(thread), PHONE_MORNINGS)
        reference = post.json()["block"]["reference"]
        for resp in (post, put):
            settled = resp.json()["settled"]
            assert "verified" in [a["kind"] for a in settled["actions"]]
            assert settled["request"]["reference"] == reference
        assert put.json()["settled"]["request"]["followup"] == put.json()["followup"]
        assert len(h.composer.view_calls) == 2


def test_validation_error_names_field_not_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """failure (AC-14, WF-2): 400 VALIDATION_ERROR names the field and constraint, never the value."""
    caplog.set_level(logging.DEBUG)
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            bad_turn = _post(client, token, thread, {"turn_id": "not-a-uuid"})
            bad_window = _put(
                client, token, thread, {"channel": "phone", "destination": "general", "window": "evening"}
            )
            no_channel = _put(client, token, thread, {"destination": "general", "window": "any"})
        for resp, field in ((bad_turn, "turn_id"), (bad_window, "window"), (no_channel, "channel")):
            data = error_body(resp, 400, "VALIDATION_ERROR")
            assert data["error"]["field"] == field
            assert data["error"]["constraint"]
            assert "not-a-uuid" not in resp.text and "evening" not in resp.text
        assert "not-a-uuid" not in app_log_text(caplog) and "evening" not in app_log_text(caplog)
        assert "not-a-uuid" not in caplog.text and "evening" not in caplog.text


def _all_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _all_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _all_strings(v)]
    return []


def test_nothing_claims_a_send(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """negative (AC-15, WF-2): no CON-4 or CON-5 body says a message was sent."""
    banned = ("was sent", "we sent", "emailed you", "called you")
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        with make_client(h.app) as client:
            token, thread = _verified_with_case(h, client)
            bodies = [
                _post(client, token, thread),
                _put(client, token, thread, PHONE_MORNINGS),
                _put(client, token, thread, EMAIL_GENERAL),
            ]
        for resp in bodies:
            assert resp.status_code == 200
            for text in _all_strings(resp.json()):
                assert not any(phrase in text.lower() for phrase in banned), text


def test_destination_masked_everywhere(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-16, WF-2): the full phone and email appear in no body, log record or trace span."""
    caplog.set_level(logging.DEBUG)
    with temp_sqlite() as db:
        phone, email = customer_contact(db)
        h = handoff_app(monkeypatch, tmp_path, db)
        with make_client(h.app) as client:
            token, thread = _verified_with_case(h, client)
            resp = _put(client, token, thread, PHONE_MORNINGS)
            other = _put(client, token, thread, EMAIL_GENERAL)
        everything = "\n".join(
            [resp.text, other.text, caplog.text, app_log_text(caplog), repr(h.trace.turns)]
            + [repr(ids) for ids in (t.ids for t in h.trace.turns)]
        )
        assert phone not in everything and email not in everything
        assert "the number ending in 02" in resp.text


def test_login_gate_and_role_ignored(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-17, WF-2): no cookie gives 401; a staff role still gets 200 on both operations."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            anon_post = client.post(HANDOFF_PATH.format(thread_id=thread), json=_new_turn())
            anon_put = client.put(FOLLOW_UP_PATH.format(thread_id=thread), json=EMAIL_GENERAL)
            h.store.set_role(token, DemoRole.REPRESENTATIVE)
            post = _post(client, token, thread)
            put = _put(client, token, thread, EMAIL_GENERAL)
        for resp, op in ((anon_post, "requestPerson"), (anon_put, "saveFollowUp")):
            data = error_body(resp, 401, "UNAUTHENTICATED")
            assert data["error"]["details"]["reason"] == "none"
            assert_matches(resp, op)
        assert post.status_code == 200 and put.status_code == 200


def test_case_service_refusal_maps_to_409(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure (PA-1): a CaseService refusal maps to 409 with its details; anything else is a 500."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        with make_client(h.app) as client:
            token, thread = _verified_with_case(h, client)
            h.cases.refuse = SimpleNamespace(code="NOT_ALLOWED_IN_STATE", details={"state": "case_closed"})
            refused = _put(client, token, thread, PHONE_MORNINGS)
            h.cases.refuse = SimpleNamespace(code="SOMETHING_ELSE", details=None)
            odd = _put(client, token, thread, PHONE_MORNINGS)
        data = error_body(refused, 409, "NOT_ALLOWED_IN_STATE")
        assert data["error"]["details"] == {"state": "case_closed"}
        assert odd.status_code == 500


def test_example_pair_1_case_created_then_already_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """WP pair 1: nobody online, MHC-C-0009 on a fresh store, then already_open, then the first body again."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            first = _post(client, token, thread, BUTTON)
            second = _post(client, token, thread)
            same = _post(client, token, thread, BUTTON)
        block = first.json()["block"]
        expected = promise_for(HandoffReason.CUSTOMER_REQUESTED_PERSON, "nobody_online", NOW)
        assert first.json()["result"] == "case_created"
        assert block["reference"] == "MHC-C-0009"
        assert block["variant"] == "nobody_online"
        assert block["due_label"] == expected.due_label
        assert block["due_at"] is not None and expected.due_at is not None
        assert datetime.fromisoformat(block["due_at"]) == expected.due_at
        assert block["produced_by_code"] is True
        assert first.json()["settled"]["request"]["reference"] == block["reference"]
        assert second.json()["result"] == "already_open"
        assert second.json()["block"]["reference"] == "MHC-C-0009"
        assert _count(db, "SELECT COUNT(*) FROM cases WHERE thread_id = ?", thread) == 1
        assert same.json() == first.json()


def test_example_pair_2_phone_mornings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """WP pair 2 (WP-7 + WP-2): verified MHC-10002 after a refund case saves phone mornings; unverified gets 409."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db)
        token = customer_token(h)
        thread = thread_for(h, token)
        verify_thread(db, thread)
        with db.uow() as tx:
            identity = tx.core.reads.identity_state(thread)
        refund = HandoffRequest(
            thread_id=thread,
            turn_id=_turn_id(),
            reason=HandoffReason.REFUND,
            priority=priority_for(HandoffReason.REFUND),
            rule_id="test.refund",
            trigger="escalation",
            identity=identity,
        )
        from meridian.domain.turn import SpanHandle, TurnBudget, TurnContext, TurnIds

        ids = TurnIds(
            thread_id=thread,
            turn_id=refund.turn_id,
            request_id=_request_id(),
            run_tag="live",
            run_id=None,
            agent_version="test-agent-0",
        )
        ctx = TurnContext(
            ids=ids,
            budget=TurnBudget(started=0.0, deadline=60.0),
            now=NOW,
            demo_session=session_id_of(h, token),
            span=SpanHandle(turn_id=refund.turn_id, trace_id=None),
        )
        h.handoff.open(refund, ctx)
        unverified = thread_for(h, token)
        h.handoff.open(refund.model_copy(update={"thread_id": unverified, "turn_id": _turn_id()}), ctx)
        with make_client(h.app) as client:
            ok = _put(client, token, str(thread), PHONE_MORNINGS)
            no = _put(client, token, str(unverified), PHONE_MORNINGS)
        followup = ok.json()["followup"]
        assert ok.status_code == 200
        assert followup["destination_label"] == "the number ending in 02"
        assert followup["on_record"] is True
        assert followup["saved_line"] == "Follow-up saved: phone call, the number ending in 02, mornings."
        error_body(no, 409, "NOT_ALLOWED_IN_STATE")
        assert no.json()["error"]["details"] == {"state": "not_verified"}
        assert _count(db, "SELECT COUNT(*) FROM followups WHERE thread_id = ?", str(unverified)) == 0


def _turn_id() -> Any:
    from meridian.domain.common import TurnId

    return TurnId(str(uuid.uuid4()))


def _request_id() -> Any:
    from meridian.domain.common import RequestId

    return RequestId(str(uuid.uuid4()))
