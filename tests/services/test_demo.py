"""AEA-30: DemoClock, DemoService (staffing, clock advance), WF-5 records, the CON-8 + WF-7 worked pair."""

from __future__ import annotations

import inspect
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast, get_args

import pytest

import meridian.services.demo as demo_module
from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.domain.handoff import HandoffReason, Priority
from meridian.domain.staff import DemoRole, StaffRole, actor_for
from meridian.domain.views import ClockView, StaffingView
from meridian.policy.handoff import case_due_at, promise_for
from meridian.policy.texts import TEXTS, TextId
from meridian.services.demo import (
    STAFFING_CHANGED_OFF_LINE,
    ClockStep,
    DeferredCases,
    DemoClock,
    DemoService,
    format_clock,
)
from meridian.services.scheduler import SchedulerJob
from meridian.web.schemas.staff_clock import CLOCK_STEP_NAMES, ClockAdvanceResponse
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.demo_support import (
    CASE_REF,
    ConvertingCases,
    RaisingCases,
    WallClock,
    add_case,
    add_conversation,
    chi,
    count,
    make_demo,
    new_request_id,
    rows,
    set_demo,
    stream_events,
)

ACTOR = actor_for(StaffRole.SUPERVISOR)


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _example_case(store: TempStore) -> None:
    created = chi(2026, 10, 16, 9, 24)
    promise = promise_for(HandoffReason.BILLING_DISPUTE, "nobody_online", created)
    assert promise.due_at == chi(2026, 10, 19, 19, 0)
    due = case_due_at(HandoffReason.BILLING_DISPUTE, promise, None)
    assert due == promise.due_at
    add_case(
        store,
        ref="MHC-C-0007",
        reason=HandoffReason.BILLING_DISPUTE,
        priority=Priority.P3,
        lifecycle="unassigned",
        created_at=created,
        due_at=due,
        promise=promise,
    )


def test_clock_starts_at_demo_start(store: TempStore) -> None:
    now = DemoClock(store.uow).now()
    assert now == DEMO_START
    assert getattr(now.tzinfo, "key", None) == "America/Chicago"
    assert (now.year, now.month, now.day, now.hour, now.minute) == (2026, 10, 16, 10, 0)


def test_clock_ignores_wall_clock(store: TempStore, monkeypatch: pytest.MonkeyPatch) -> None:
    class _Tomorrow(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
            return datetime.now(tz) + timedelta(days=1)

        @classmethod
        def utcnow(cls) -> datetime:  # type: ignore[override]
            return datetime.utcnow() + timedelta(days=1)

        @classmethod
        def today(cls) -> datetime:  # type: ignore[override]
            return datetime.today() + timedelta(days=1)

    monkeypatch.setattr("meridian.services.demo.datetime", _Tomorrow)
    assert DemoClock(store.uow).now() == DEMO_START
    source = inspect.getsource(DemoClock)
    for needle in ("datetime.now", "utcnow", "date.today", "time.time"):
        assert needle not in source


def test_advance_steps(store: TempStore) -> None:
    demo = make_demo(store, ConvertingCases())
    clock = DemoClock(store.uow)
    for step, expected in (
        ("plus_1h", chi(2026, 10, 16, 11)),
        ("plus_4h", chi(2026, 10, 16, 15)),
        ("next_business_morning", chi(2026, 10, 19, 7)),
    ):
        result = demo.advance_clock(cast(ClockStep, step), actor=ACTOR, request_id=new_request_id())
        assert result.now == expected
        assert clock.now() == expected
    set_demo(store, now=chi(2026, 11, 25, 10))
    result = demo.advance_clock("next_business_morning", actor=ACTOR, request_id=new_request_id())
    assert result.now == chi(2026, 11, 30, 7)
    assert clock.now() == result.now


def test_unknown_step_rejected(store: TempStore) -> None:
    add_conversation(store)
    demo = make_demo(store, ConvertingCases())
    with pytest.raises(ValueError):
        demo.advance_clock(cast(ClockStep, "minus_1h"), actor=ACTOR, request_id=new_request_id())
    assert rows(store, "demo_state") == []
    assert count(store, "demo_events") == 0
    assert count(store, "events") == 0
    assert DemoClock(store.uow).now() == DEMO_START


def test_advance_counts_became_overdue(store: TempStore) -> None:
    _example_case(store)
    add_conversation(store)  # a second open thread
    add_conversation(store, live_state="closed")
    demo = make_demo(store, ConvertingCases())
    steps = ["next_business_morning", "plus_4h", "plus_4h", "plus_4h", "plus_1h"]
    requests = [new_request_id() for _ in steps]
    results = [
        demo.advance_clock(cast(ClockStep, s), actor=ACTOR, request_id=r)
        for s, r in zip(steps, requests, strict=True)
    ]
    assert [r.became_overdue for r in results] == [0, 0, 0, 0, 1]
    for r in results:
        assert set(r.model_dump().keys()) == {"now", "label", "became_overdue"}
    events = rows(store, "demo_events")
    assert len(events) == 5
    olds = [DEMO_START, *[r.now for r in results[:-1]]]
    for row, step, request, old, new in zip(events, steps, requests, olds, results, strict=True):
        assert row["kind"] == "clock_advanced"
        assert row["role"] == "supervisor"
        assert row["step"] == step
        assert row["request_id"] == str(request)
        assert row["demo_before"] == format_wall(old)
        assert row["demo_after"] == format_wall(new.now)
        assert row["became_overdue"] == new.became_overdue
    per_thread: dict[str, int] = {}
    for ev in rows(store, "events"):
        if ev["type"] == "clock_changed":
            per_thread[ev["stream"]] = per_thread.get(ev["stream"], 0) + 1
    assert sorted(per_thread.values()) == [5, 5]  # two open threads; the closed one got none


def test_example_pair_con8_wf7(store: TempStore) -> None:
    _example_case(store)
    wall = WallClock()
    demo = make_demo(store, ConvertingCases(), wall)
    steps = ["next_business_morning", "plus_4h", "plus_4h", "plus_4h", "plus_1h"]
    for s in steps:
        demo.advance_clock(cast(ClockStep, s), actor=ACTOR, request_id=new_request_id())
    assert DemoClock(store.uow).now() == chi(2026, 10, 19, 20)
    first = SchedulerJob(store.uow, object(), DemoClock(store.uow), lambda: 0, wall).tick()
    assert (first.status, first.overdue, first.promises_missed) == ("completed", 1, 1)
    ref = CASE_REF.validate_python("MHC-C-0007")
    with store.uow() as tx:
        kinds = [(e.kind, e.job_run_id) for e in tx.cases.case_events.list_for_case(ref)]
        current = tx.cases.promises.current(ref)
    assert ("overdue", first.job_run_id) in kinds
    assert ("promise_missed", first.job_run_id) in kinds
    assert current is not None
    assert current.status == "missed"
    SchedulerJob(store.uow, object(), DemoClock(store.uow), lambda: 0, wall).tick()
    assert count(store, "job_runs") == 2
    with store.uow() as tx:
        assert [e.kind for e in tx.cases.case_events.list_for_case(ref)].count("overdue") == 1


def test_advance_result_fits_con8_route(store: TempStore) -> None:
    demo = make_demo(store, ConvertingCases())
    result = demo.advance_clock("next_business_morning", actor=ACTOR, request_id=new_request_id())
    body = ClockAdvanceResponse.model_validate(result, from_attributes=True).model_dump(mode="json")
    assert body == {
        "now": "2026-10-19T07:00:00-05:00",
        "label": "Mon Oct 19, 2026 · 7:00 am",
        "became_overdue": 0,
    }
    assert get_args(ClockStep) == CLOCK_STEP_NAMES


def test_staffing_default_and_toggle(store: TempStore) -> None:
    cases = ConvertingCases()
    demo = make_demo(store, cases)
    assert demo.presence() == "nobody_online"
    assert demo.staffing() == StaffingView(mode="nobody_online", label="Nobody online", banner=None)
    same = demo.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert same.converted_cases == 0
    assert count(store, "demo_events") == 0
    assert count(store, "events") == 0
    open_a = add_conversation(store)
    open_b = add_conversation(store)
    closed = add_conversation(store, live_state="closed")
    request = new_request_id()
    on = demo.set_staffing("simulated_on_shift", request_id=request, role=DemoRole.CUSTOMER)
    assert on.label == "Simulated staff on shift (demo)"
    (row,) = rows(store, "demo_events")
    assert (row["kind"], row["mode"], row["demo_before"], row["demo_after"]) == (
        "staffing_changed",
        "simulated_on_shift",
        "nobody_online",
        "simulated_on_shift",
    )
    assert (row["converted_cases"], row["role"], row["request_id"]) == (0, "customer", str(request))
    for tid in (open_a, open_b):
        (event,) = stream_events(store, tid)
        assert event.type == "staffing_changed"
        assert event.payload["line"] == TEXTS[TextId.STAFFING_CHANGED_ON_SHIFT]
        staffing = cast(dict[str, Any], event.payload["staffing"])
        assert staffing["mode"] == "simulated_on_shift"
        assert staffing["label"] == "Simulated staff on shift (demo)"
    assert stream_events(store, closed) == []
    assert cases.calls == []
    demo.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert count(store, "demo_events") == 1
    off = demo.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert off.label == "Nobody online"
    last = stream_events(store, open_a)[-1]
    assert last.payload["line"] == STAFFING_CHANGED_OFF_LINE
    assert cast(dict[str, Any], last.payload["staffing"])["banner"] is None


def test_shift_end_commits_with_conversions(store: TempStore) -> None:
    cases = ConvertingCases()
    demo = make_demo(store, cases)
    demo.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    t1 = add_conversation(store, live_state="queued")
    promise = promise_for(HandoffReason.CUSTOMER_REQUESTED_PERSON, "simulated_on_shift", DEMO_START)
    add_case(
        store,
        ref="MHC-C-0011",
        reason=HandoffReason.CUSTOMER_REQUESTED_PERSON,
        priority=Priority.P3,
        lifecycle="live_queued",
        created_at=DEMO_START,
        due_at=None,
        promise=promise,
        thread_id=t1,
    )
    off = demo.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert off.converted_cases == 1
    assert len(cases.calls) == 1
    assert cases.calls[0][0] == DEMO_START
    assert cases.calls[0][1] is not None
    with store.uow() as tx:
        case = tx.cases.cases.get(CASE_REF.validate_python("MHC-C-0011"))
    assert case is not None
    assert case.lifecycle == "unassigned"
    assert [e.type for e in stream_events(store, t1)][-2:] == ["shift_ended", "staffing_changed"]
    assert demo.presence() == "nobody_online"
    demo.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    before = (count(store, "demo_events"), count(store, "events"))
    failing = make_demo(store, RaisingCases())
    with pytest.raises(RuntimeError):
        failing.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert failing.presence() == "simulated_on_shift"
    assert (count(store, "demo_events"), count(store, "events")) == before


def test_deferred_cases_resolves_at_call_time(store: TempStore) -> None:
    resolved: list[int] = []
    double = ConvertingCases()

    def resolver() -> ConvertingCases:
        resolved.append(1)
        return double

    deferred = DeferredCases(resolver)
    assert resolved == []
    demo = DemoService(store.uow, DemoClock(store.uow), deferred)
    demo.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.OWNER)
    assert resolved == []
    off = demo.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.OWNER)
    assert resolved == [1]
    assert off.converted_cases == 0

    def unbound() -> ConvertingCases:
        raise RuntimeError("not bound: case_service")

    other = DemoService(store.uow, DemoClock(store.uow), DeferredCases(unbound))
    other.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.OWNER)
    events_before = count(store, "demo_events")
    with pytest.raises(RuntimeError, match="not bound: case_service"):
        other.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.OWNER)
    assert other.presence() == "simulated_on_shift"
    assert count(store, "demo_events") == events_before


def test_staffing_banner_is_fixed_text(store: TempStore) -> None:
    demo = make_demo(store, ConvertingCases())
    demo.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert demo.staffing().banner == TEXTS[TextId.STAFFING_BANNER]
    demo.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert demo.staffing().banner is None
    assert "No Meridian employee" not in Path(demo_module.__file__).read_text()


def test_views_use_format_clock(store: TempStore) -> None:
    thread = add_conversation(store)
    demo = make_demo(store, ConvertingCases())
    label, date_label = format_clock(DEMO_START)
    assert demo.clock_view() == ClockView(now=DEMO_START, label=label, date_label=date_label)
    result = demo.advance_clock("plus_1h", actor=ACTOR, request_id=new_request_id())
    new_label, new_date = format_clock(result.now)
    assert result.label == new_label
    newest = stream_events(store, thread)[-1]
    assert newest.type == "clock_changed"
    assert newest.payload["demo_clock"] == {
        "now": result.now.isoformat(),
        "label": new_label,
        "date_label": new_date,
    }
    assert demo.clock_view().date_label == new_date


def test_wf5_records(store: TempStore) -> None:
    demo = make_demo(store, ConvertingCases())
    r1, r2 = new_request_id(), new_request_id()
    demo.set_staffing("simulated_on_shift", request_id=r1, role=DemoRole.REPRESENTATIVE)
    demo.advance_clock("plus_1h", actor=ACTOR, request_id=r2)
    events = rows(store, "demo_events")
    assert len(events) == 2
    assert all(len(e["demo_event_id"]) == 36 for e in events)
    assert {e["request_id"] for e in events} == {str(r1), str(r2)}
    assert str(events[0]["at_wall"]).endswith("+00:00")
    assert events[0]["at_wall"] == format_wall(datetime(2026, 10, 21, 19, 0, tzinfo=UTC))
