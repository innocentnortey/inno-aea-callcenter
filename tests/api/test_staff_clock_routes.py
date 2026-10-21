"""AEA-47: CON-8 `advanceDemoClock` (POST /api/demo/clock, supervisor only) through AEA-23's real app and middleware
with a DemoService double. Each docstring names the failure mode and the acceptance criterion."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from meridian.domain.common import RequestId
from meridian.domain.staff import DemoRole, StaffRole, actor_for
from meridian.policy.limits import Limits
from meridian.web.app import create_app
from meridian.web.container import Container, register_staff_clock
from meridian.web.deps import get_demo_service
from meridian.web.routes.staff_clock import build_router
from meridian.web.schemas.staff_clock import CLOCK_STEP_NAMES
from tests.api.openapi_check import load_document
from tests.api.staff_clock_support import (
    ADVANCE_PATH,
    NEXT_MORNING,
    ClockAdvancedWithDateLabel,
    ClockHarness,
    FakeClockAdvancer,
    clock_app,
    signed_in,
)
from tests.api.web_shell_support import (
    FakeHeartbeat,
    FakeSessionStore,
    all_output_text,
    app_log_text,
    assert_matches,
    captured_log,
    cookie_header,
    effective_routes,
    error_body,
    full_app,
    make_client,
    make_settings,
    rand_word,
    records_of,
    reset_gate_of,
)


def _examples() -> dict[str, Any]:
    post = load_document()["paths"][ADVANCE_PATH]["post"]
    return {
        k: v["value"] for k, v in post["responses"]["200"]["content"]["application/json"]["examples"].items()
    }


def _harness(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ClockHarness:
    return clock_app(monkeypatch, make_settings(tmp_path))


def test_example_pair_next_morning_and_role_not_allowed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """worked pair (ticket example): supervisor gets the OpenAPI NEXT_MORNING body; the representative gets 403."""
    h = _harness(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        headers, _ = signed_in(h, DemoRole.SUPERVISOR)
        r = client.post(ADVANCE_PATH, headers=headers, json={"step": "next_business_morning"})
        assert r.status_code == 200, r.text
        assert_matches(r, "advanceDemoClock")
        assert r.json() == _examples()["NEXT_MORNING"]
        print(r.json())
        rep_headers, _ = signed_in(h, DemoRole.REPRESENTATIVE)
        r = client.post(ADVANCE_PATH, headers=rep_headers, json={"step": "next_business_morning"})
        body = error_body(r, 403, "ROLE_NOT_ALLOWED")
        assert body["error"]["details"] == {
            "role": "representative",
            "needs": ["supervisor"],
            "reason": "wrong_role",
        }
        assert_matches(r, "advanceDemoClock")
        print(body["error"]["details"])
    assert len(h.demo.calls) == 1


def test_advance_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): 200 bodies validate and equal the double's values; exactly three keys."""
    h = _harness(monkeypatch, tmp_path)
    examples = _examples()
    with make_client(h.app) as client:
        headers, _ = signed_in(h, DemoRole.SUPERVISOR)
        for step, example in (("next_business_morning", "NEXT_MORNING"), ("plus_1h", "PLUS_1H")):
            r = client.post(ADVANCE_PATH, headers=headers, json={"step": step})
            assert r.status_code == 200, r.text
            assert_matches(r, "advanceDemoClock")
            stub = h.demo.results[step]
            assert r.json() == examples[example]
            assert r.json() == {
                "now": stub.now.isoformat(),
                "label": stub.label,
                "became_overdue": stub.became_overdue,
            }
            assert sorted(r.json()) == ["became_overdue", "label", "now"]


def test_one_call_with_step_actor_and_request_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-2): one call per request with the step, the supervisor actor and the response's request id."""
    h = _harness(monkeypatch, tmp_path)
    steps = ["plus_1h", "plus_4h", "next_business_morning"]
    with make_client(h.app) as client:
        headers, _ = signed_in(h, DemoRole.SUPERVISOR)
        responses = [client.post(ADVANCE_PATH, headers=headers, json={"step": s}) for s in steps]
    assert [r.status_code for r in responses] == [200, 200, 200]
    assert [c.step for c in h.demo.calls] == steps
    for call, r in zip(h.demo.calls, responses, strict=True):
        assert call.actor == actor_for(StaffRole.SUPERVISOR)
        assert call.actor.name == "Demo supervisor"
        assert call.request_id == r.headers["X-Request-ID"]
        assert isinstance(call.request_id, RequestId)
        print(call)


def test_invalid_step_400(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal (AC-3): an unknown or missing step is a 400 on field `step` and never reaches the service."""
    h = _harness(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        headers, _ = signed_in(h, DemoRole.SUPERVISOR)
        for payload in ({"step": "minus_1h"}, {"step": "back"}, {}):
            r = client.post(ADVANCE_PATH, headers=headers, json=payload)
            body = error_body(r, 400, "VALIDATION_ERROR")
            assert body["error"]["field"] == "step"
            assert_matches(r, "advanceDemoClock")
    assert h.demo.calls == []


def test_rejected_step_never_echoed_or_logged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-4): the rejected step string is in neither the 400 body nor any log record."""
    caplog.set_level(logging.DEBUG)
    h = _harness(monkeypatch, tmp_path)
    bad = rand_word(12, "zqstep")
    with captured_log() as stream, make_client(h.app) as client:
        headers, _ = signed_in(h, DemoRole.SUPERVISOR)
        r = client.post(ADVANCE_PATH, headers=headers, json={"step": bad})
    assert r.status_code == 400
    assert bad not in all_output_text([r])
    assert bad not in stream.getvalue()
    assert bad not in app_log_text(caplog)
    for rec in caplog.records:
        assert bad not in repr(rec.__dict__)
    request_records = records_of(stream, "request")
    assert len(request_records) == 1
    assert request_records[0]["route"] == ADVANCE_PATH
    assert request_records[0]["status"] == 400
    assert h.demo.calls == []


def test_supervisor_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal (AC-5, WF-5): other roles and a role-reset session get 403; the service is never called."""
    h = _harness(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        for role in (DemoRole.CUSTOMER, DemoRole.REPRESENTATIVE, DemoRole.OWNER):
            headers, _ = signed_in(h, role)
            r = client.post(ADVANCE_PATH, headers=headers, json={"step": "plus_1h"})
            body = error_body(r, 403, "ROLE_NOT_ALLOWED")
            assert body["error"]["details"] == {
                "role": role.value,
                "needs": ["supervisor"],
                "reason": "wrong_role",
            }
            assert_matches(r, "advanceDemoClock")
            print(body["error"]["details"])
        token = h.store.issue(DemoRole.SUPERVISOR)
        h.store.set_role(token, DemoRole.CUSTOMER, role_reset=True)
        r = client.post(ADVANCE_PATH, headers=cookie_header(token), json={"step": "plus_1h"})
        body = error_body(r, 403, "ROLE_NOT_ALLOWED")
        assert body["error"]["details"] == {
            "role": "customer",
            "needs": ["supervisor"],
            "reason": "role_reset",
        }
        assert_matches(r, "advanceDemoClock")
        print(body["error"]["details"])
    assert h.demo.calls == []


def test_login_gate_and_reset_503(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal (AC-6, WF-5): no session is 401; a held reset gate is an immediate 503; no service call."""
    h = _harness(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        r = client.post(ADVANCE_PATH, json={"step": "plus_1h"})
        body = error_body(r, 401, "UNAUTHENTICATED")
        assert body["error"]["details"] == {"reason": "none"}
        assert_matches(r, "advanceDemoClock")
        headers, _ = signed_in(h, DemoRole.SUPERVISOR)
        with reset_gate_of(h.app).hold():
            t0 = time.monotonic()
            r = client.post(ADVANCE_PATH, headers=headers, json={"step": "plus_1h"})
            elapsed = time.monotonic() - t0
        body = error_body(r, 503, "RESET_IN_PROGRESS")
        assert body["error"]["details"] == {"retry_after_ms": 5000}
        assert_matches(r, "advanceDemoClock")
        assert elapsed < 1.0
        assert h.demo.calls == []
        r = client.post(ADVANCE_PATH, headers=headers, json={"step": "plus_1h"})
        assert r.status_code == 200
    assert len(h.demo.calls) == 1


def test_router_declares_post_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-8): this router registers only POST /api/demo/clock (AEA-43's GET is never shadowed)."""
    routes = build_router().routes
    assert len(routes) == 1
    route = routes[0]
    assert isinstance(route, APIRoute)
    assert route.path == ADVANCE_PATH
    assert route.methods == {"POST"}
    assert route.operation_id == "advanceDemoClock"
    h = _harness(monkeypatch, tmp_path)
    with make_client(h.app):
        found = [r for r in effective_routes(h.app) if r.path == ADVANCE_PATH]
    assert len(found) == 1
    assert found[0].methods == frozenset({"POST"})
    print(found[0])


def test_wf5_advance_emits_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-9, WF-5): through the real container, one request record; the service gets the same id and role."""
    store = FakeSessionStore()
    app: FastAPI = full_app(monkeypatch, make_settings(tmp_path), store=store, heartbeat=FakeHeartbeat())
    demo = FakeClockAdvancer()
    app.dependency_overrides[get_demo_service] = lambda: demo
    headers = cookie_header(store.issue(DemoRole.SUPERVISOR))
    with captured_log() as stream, make_client(app) as client:
        r = client.post(ADVANCE_PATH, headers=headers, json={"step": "next_business_morning"})
    assert r.status_code == 200, r.text
    recs = [x for x in records_of(stream, "request") if x["route"] == ADVANCE_PATH]
    assert len(recs) == 1
    rec = recs[0]
    print(rec)
    assert rec["request_id"] == r.headers["X-Request-ID"]
    assert rec["status"] == 200
    assert rec["caller_role"] == "supervisor"
    assert rec.get("thread_id") is None
    assert len(demo.calls) == 1
    assert demo.calls[0].request_id == rec["request_id"]
    assert demo.calls[0].actor.role.value == rec["caller_role"]


def test_advance_response_keys_exact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """negative (AC-10, R-W-17): a service result with an extra date_label still yields exactly three keys."""
    h = _harness(monkeypatch, tmp_path)
    h.demo.results["next_business_morning"] = ClockAdvancedWithDateLabel(
        NEXT_MORNING.now, NEXT_MORNING.label, 1, "Mon Oct 19, 2026 (demo date)"
    )
    with make_client(h.app) as client:
        headers, _ = signed_in(h, DemoRole.SUPERVISOR)
        r = client.post(ADVANCE_PATH, headers=headers, json={"step": "next_business_morning"})
    assert r.status_code == 200, r.text
    keys = sorted(r.json())
    print(keys)
    assert keys == ["became_overdue", "label", "now"]
    assert "date_label" not in r.text
    assert_matches(r, "advanceDemoClock")


def test_step_names_equal_openapi_enum() -> None:
    """invariant (drift guard): the schema's step names equal the OpenAPI ClockAdvanceRequest.step enum."""
    enum = load_document()["components"]["schemas"]["ClockAdvanceRequest"]["properties"]["step"]["enum"]
    assert enum == list(CLOCK_STEP_NAMES)


def test_register_staff_clock_includes_router_once(tmp_path: Path) -> None:
    """invariant (hunk): the router is included once on a web-shell app and not at all on a bare app."""
    s = make_settings(tmp_path)
    bare = FastAPI()
    register_staff_clock(Container(settings=s, limits=Limits()), bare, settings=s, limits=Limits())
    assert [r for r in effective_routes(bare) if r.path == ADVANCE_PATH] == []
    app = create_app(s)
    for _ in range(2):
        register_staff_clock(Container(settings=s, limits=Limits()), app, settings=s, limits=Limits())
    found = [r for r in effective_routes(app) if r.path == ADVANCE_PATH]
    assert len(found) == 1
    assert found[0].methods == frozenset({"POST"})
    assert found[0].operation_id == "advanceDemoClock"
    assert app.state.staff_clock_routes_included is True
