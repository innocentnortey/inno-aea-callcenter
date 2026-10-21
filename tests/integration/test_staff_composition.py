"""AEA-52: the real staff objects are bound, refuse correctly and leak nothing (AC-1, AC-5, AC-13 twin, AC-21)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import pytest

from meridian.adapters.checkpointer import Checkpointer
from meridian.services.cases import CaseService
from meridian.services.demo import DemoClock, DemoService
from meridian.services.handoff import HandoffService
from meridian.services.live_chat import LiveChatService
from meridian.services.reset import ResetService
from meridian.services.reset_gate import ResetGate
from meridian.services.scheduler import SchedulerJob, SchedulerThread
from meridian.services.session import SessionService
from meridian.services.staff import FlagService, StaffSessionStore
from meridian.services.turn import TurnService
from meridian.web.container import Key
from meridian.web.deps import (
    CASE_SERVICE,
    DEMO_SERVICE,
    FLAG_SERVICE,
    HANDOFF_SERVICE,
    LIVE_CHAT,
    LOGIN_SESSIONS,
    RESET_GATE,
    RESET_SERVICE,
    SESSION_SERVICE,
    STAFF_ACCESS,
    TURN_SERVICE,
)
from tests.integration.staff_support import (
    P1_NEEDS,
    P1_OPERATIONS,
    SCHEDULER_JOB,
    SCHEDULER_THREAD,
    SCHEDULER_THREAD_KEY,
    X_ROLES,
    act,
    assert_bound,
    call,
    error_of,
    open_staff_run,
    seed_contact_values,
    set_staffing,
    sign_in,
    version_of,
)
from tests.journeys.support.run import JourneyRun

ROOT = Path(__file__).resolve().parents[2]


def _scheduler_threads() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == SCHEDULER_THREAD and t.is_alive()]


def test_real_objects_bound(request: pytest.FixtureRequest) -> None:
    strict = bool(request.config.getoption("--journeys-strict"))
    with open_staff_run(strict=strict, nodeid=request.node.nodeid) as run:
        assert_bound(run, P1_NEEDS, P1_OPERATIONS)
        assert run.app.dependency_overrides == {}
        get = run.container.get
        assert id(get(LOGIN_SESSIONS)) == id(get(STAFF_ACCESS))
        table: list[tuple[Any, type]] = [
            (get(LOGIN_SESSIONS), StaffSessionStore),
            (get(FLAG_SERVICE), FlagService),
            (get(CASE_SERVICE), CaseService),
            (get(HANDOFF_SERVICE), HandoffService),
            (get(LIVE_CHAT), LiveChatService),
            (get(DEMO_SERVICE), DemoService),
            (get(Key("demo_clock")), DemoClock),
            (get(SCHEDULER_JOB), SchedulerJob),
            (get(SCHEDULER_THREAD_KEY), SchedulerThread),
            (get(RESET_SERVICE), ResetService),
            (get(RESET_GATE), ResetGate),
            (get(Key("checkpointer")), Checkpointer),
            (get(SESSION_SERVICE), SessionService),
            (get(TURN_SERVICE), TurnService),
        ]
        for obj, cls in table:
            assert type(obj) is cls, f"{type(obj).__name__} is not {cls.__name__}"
            print(f"{cls.__name__:<18} bound")

        thread = get(SCHEDULER_THREAD_KEY)
        assert thread.alive is True
        assert len(_scheduler_threads()) == 1

        sup = sign_in(run, "supervisor")
        set_staffing(sup, "simulated_on_shift")
        off = set_staffing(sup, "nobody_online")
        assert off.json()["converted_cases"] == 0  # the on -> off path resolved case_service
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and (thread.alive or _scheduler_threads()):
        time.sleep(0.05)
    assert thread.alive is False
    assert _scheduler_threads() == []
    print("scheduler thread alive after start, gone after shutdown")


def _wrong_role(response: Any, role: str, op: str) -> None:
    assert response.status_code == 403, (op, response.status_code)
    error = error_of(response)
    assert error["code"] == "ROLE_NOT_ALLOWED"
    assert error["details"] == {"role": role, "needs": list(X_ROLES[op]), "reason": "wrong_role"}


def _probes(version: int) -> dict[str, tuple[str, str, object | None]]:
    ref = "MHC-C-0006"
    return {
        "getQueue": ("GET", "/api/staff/queue", None),
        "getCase": ("GET", f"/api/staff/cases/{ref}", None),
        "applyCaseAction": (
            "POST",
            f"/api/staff/cases/{ref}/actions",
            {"action": "claim", "expected_version": version},
        ),
        "liveChatAction": ("POST", f"/api/staff/cases/{ref}/live", {"action": "join"}),
        "recordContactActivity": (
            "POST",
            f"/api/staff/cases/{ref}/activities",
            {"kind": "call", "outcome": "no_answer", "note": None, "expected_version": version},
        ),
        "createFlag": ("POST", "/api/staff/flags", {"case_ref": ref, "target": "brief"}),
        "listFlags": ("GET", "/api/staff/flags", None),
        "reviewFlag": ("PATCH", "/api/staff/flags/flg-999999", {"status": "reviewed"}),
        "getOversight": ("GET", "/api/staff/oversight", None),
    }


def test_role_and_state_refusals(journey: JourneyRun) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    rep = sign_in(journey, "representative")
    sup = sign_in(journey, "supervisor")
    owner = sign_in(journey, "owner")
    cust = sign_in(journey)
    anon = journey.client()
    v0 = version_of(sup, "MHC-C-0006")

    owner_view = call(owner, "GET", "/api/staff/cases/MHC-C-0006", "getCase")
    assert owner_view.status_code == 200
    assert owner_view.json()["case"]["allowed_actions"] == []
    ref = "MHC-C-0006"
    for op, (method, path, body) in _probes(v0).items():
        if op in ("getQueue", "getCase", "listFlags", "getOversight"):
            continue
        _wrong_role(call(owner, method, path, op, body), "owner", op)
    owner_review = call(owner, "PATCH", "/api/staff/flags/flg-1", "reviewFlag", {"status": "reviewed"})
    _wrong_role(owner_review, "owner", "reviewFlag")
    owner_clock = call(owner, "POST", "/api/demo/clock", "advanceDemoClock", {"step": "plus_1h"})
    _wrong_role(owner_clock, "owner", "advanceDemoClock")

    for op, body in (
        ("advanceDemoClock", {"step": "plus_1h"}),
        ("reviewFlag", {"status": "reviewed"}),
    ):
        path = "/api/demo/clock" if op == "advanceDemoClock" else "/api/staff/flags/flg-1"
        method = "POST" if op == "advanceDemoClock" else "PATCH"
        refused = call(rep, method, path, op, body)
        assert refused.status_code == 403
        assert error_of(refused)["details"]["needs"] == ["supervisor"]

    for op, (method, path, body) in _probes(v0).items():
        _wrong_role(call(cust, method, path, op, body), "customer", op)
    _wrong_role(
        call(cust, "GET", f"/api/staff/cases/{ref}/events", "streamCaseEvents"),
        "customer",
        "streamCaseEvents",
    )
    _wrong_role(
        call(cust, "POST", "/api/demo/clock", "advanceDemoClock", {"step": "plus_1h"}),
        "customer",
        "advanceDemoClock",
    )

    changed = act(sup, ref, "change_priority", version=v0, priority="P2", reason="Synthetic priority reason.")
    assert changed.status_code == 200, changed.text
    conflict = act(rep, ref, "claim", version=v0)
    assert conflict.status_code == 409
    err = error_of(conflict)
    assert err["code"] == "VERSION_CONFLICT"
    assert set(err["details"]) == {"changed_by", "changed_at", "current_version"}
    assert err["details"]["changed_by"] == "Demo supervisor"
    assert err["details"]["current_version"] == v0 + 1

    assert act(sup, "MHC-C-0007", "claim").status_code == 200
    taken = act(rep, "MHC-C-0007", "claim")
    assert taken.status_code == 409
    assert error_of(taken)["code"] == "CASE_ALREADY_CLAIMED"
    assert error_of(taken)["details"]["claimed_by"] == "Demo supervisor"

    unowned = call(rep, "POST", "/api/staff/cases/MHC-C-0005/live", "liveChatAction", {"action": "join"})
    assert unowned.status_code == 403
    assert error_of(unowned)["code"] == "NOT_CLAIMED_BY_YOU"
    assert error_of(unowned)["details"] == {"owner": None}
    theirs = call(rep, "POST", "/api/staff/cases/MHC-C-0007/live", "liveChatAction", {"action": "join"})
    assert theirs.status_code == 409
    assert error_of(theirs)["code"] == "CASE_ALREADY_CLAIMED"
    assert error_of(theirs)["details"]["claimed_by"] == "Demo supervisor"

    blank = call(
        rep, "POST", "/api/staff/cases/MHC-C-0005/live", "liveChatAction", {"action": "send", "text": "   "}
    )
    assert blank.status_code == 400
    assert error_of(blank)["code"] == "VALIDATION_ERROR"
    assert error_of(blank)["field"] == "text"
    long_text = "x" * 2001
    too_long = call(
        rep,
        "POST",
        "/api/staff/cases/MHC-C-0005/live",
        "liveChatAction",
        {"action": "send", "text": long_text},
    )
    assert too_long.status_code == 400
    assert error_of(too_long)["field"] == "text"
    assert long_text not in too_long.text

    unauth = anon.call("GET", "/api/staff/queue", operation_id="getQueue")
    assert unauth.status_code == 401
    assert error_of(unauth)["code"] == "UNAUTHENTICATED"
    assert error_of(unauth)["details"] == {"reason": "none"}


def test_least_privilege_matrix(journey: JourneyRun) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    actors = {
        "representative": sign_in(journey, "representative"),
        "supervisor": sign_in(journey, "supervisor"),
        "owner": sign_in(journey, "owner"),
        "customer": sign_in(journey),
    }
    probes = _probes(999999)
    values = seed_contact_values(journey)
    assert values, "no seed contact values found"
    table: dict[tuple[str, str], int] = {}
    for role, actor in actors.items():
        for op, (method, path, body) in probes.items():
            response = call(actor, method, path, op, body)
            table[(role, op)] = response.status_code
            refused = response.status_code == 403 and error_of(response)["code"] == "ROLE_NOT_ALLOWED"
            assert refused == (role not in X_ROLES[op]), (role, op, response.status_code)
            if op in ("getQueue", "getOversight") and response.status_code == 200:
                hits = [v for v in values if v in response.text]
                assert hits == [], f"{op} leaks {len(hits)} contact value(s)"
    assert table[("owner", "getCase")] == 200
    assert table[("owner", "listFlags")] == 200
    assert table[("representative", "getOversight")] == 403
    assert table[("representative", "reviewFlag")] == 403
    for op in probes:
        assert table[("customer", op)] == 403
    for role in actors:
        print(role, {op: table[(role, op)] for op in probes})
    print("0 contact-value hits")


def test_staff_routes_never_open_cases() -> None:
    files = sorted((ROOT / "src/meridian/web/routes").glob("staff_*.py"))
    assert files, "no staff route modules found"
    for file in files:
        assert "open_case" not in file.read_text(), file.name
