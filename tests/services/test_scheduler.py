"""AEA-30 WF-7: SchedulerJob.tick (demo-clock alerts, missed promises, abandonment sweep, prune) and SchedulerThread."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

import pytest

from meridian.domain.handoff import HandoffReason, Priority
from meridian.domain.staff import DemoRole, StaffRole, actor_for
from meridian.policy.handoff import case_due_at, promise_for
from meridian.services.demo import DemoService
from meridian.services.scheduler import SchedulerJob, SchedulerThread
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.demo_support import (
    CASE_REF,
    CUSTOMER,
    ConvertingCases,
    WallClock,
    add_case,
    add_conversation,
    chi,
    count,
    make_demo,
    new_request_id,
    rows,
    set_demo,
)

SEVEN_KEYS = {"overdue", "promises_missed", "due_soon", "stuck_waiting", "unowned", "abandoned", "pruned"}


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def job(
    store: TempStore, at: datetime, *, prune: Callable[[], int] = lambda: 0, wall: WallClock | None = None
) -> SchedulerJob:
    return SchedulerJob(store.uow, object(), FixedClock(at), prune, wall if wall is not None else WallClock())


def billing_case(
    store: TempStore, ref: str, created: datetime, *, lifecycle: str = "unassigned", **kw: object
) -> None:
    promise = promise_for(HandoffReason.BILLING_DISPUTE, "nobody_online", created)
    add_case(
        store,
        ref=ref,
        reason=HandoffReason.BILLING_DISPUTE,
        priority=Priority.P3,
        lifecycle=lifecycle,
        created_at=created,
        due_at=case_due_at(HandoffReason.BILLING_DISPUTE, promise, None),
        promise=promise,
        **kw,  # type: ignore[arg-type]
    )


def events_of(store: TempStore, ref: str) -> list[tuple[str, str | None]]:
    with store.uow() as tx:
        return [
            (e.kind, e.job_run_id) for e in tx.cases.case_events.list_for_case(CASE_REF.validate_python(ref))
        ]


def kinds_of(store: TempStore, ref: str) -> list[str]:
    return [k for k, _ in events_of(store, ref)]


def plain_case(
    store: TempStore, ref: str, *, lifecycle: str, due: datetime | None, created: datetime, **kw: object
) -> None:
    add_case(
        store,
        ref=ref,
        reason=HandoffReason.BILLING_DISPUTE,
        priority=Priority.P3,
        lifecycle=lifecycle,
        created_at=created,
        due_at=due,
        promise=None,
        **kw,  # type: ignore[arg-type]
    )


def test_tick_writes_job_run(store: TempStore) -> None:
    billing_case(store, "MHC-C-0001", chi(2026, 10, 15, 10))
    run = job(store, chi(2026, 10, 16, 20)).tick()
    (row,) = rows(store, "job_runs")
    assert str(row["started_wall_at"]).endswith("+00:00")
    assert str(row["finished_wall_at"]).endswith("+00:00")
    assert row["status"] == "completed"
    assert row["error_kind"] is None
    counts = json.loads(row["counts_json"])
    assert set(counts) == SEVEN_KEYS
    assert run.job_run_id == row["job_run_id"]
    assert run.status == "completed"
    assert counts["overdue"] == run.overdue == 1
    assert counts["promises_missed"] == run.promises_missed
    assert ("overdue", row["job_run_id"]) in events_of(store, "MHC-C-0001")


def test_failed_tick_records_failed(store: TempStore) -> None:
    billing_case(store, "MHC-C-0001", chi(2026, 10, 15, 10))

    def boom() -> int:
        raise RuntimeError("secret detail xyz")

    run = job(store, chi(2026, 10, 16, 20), prune=boom).tick()
    assert (run.status, run.error_kind, run.overdue) == ("failed", "prune_failed", 1)
    (row,) = rows(store, "job_runs")
    assert (row["status"], row["error_kind"]) == ("failed", "prune_failed")
    assert "secret detail" not in json.dumps(row)


def test_overdue_and_missed(store: TempStore) -> None:
    created = chi(2026, 10, 15, 10)
    promise = promise_for(HandoffReason.BILLING_DISPUTE, "nobody_online", created)
    assert promise.due_at == chi(2026, 10, 16, 19)
    billing_case(store, "MHC-C-0001", created)
    run = job(store, chi(2026, 10, 16, 20)).tick()
    assert kinds_of(store, "MHC-C-0001").count("overdue") == 1
    with store.uow() as tx:
        current = tx.cases.promises.current(CASE_REF.validate_python("MHC-C-0001"))
    assert current is not None
    assert current.status == "missed"
    assert (run.overdue, run.promises_missed) == (1, 1)


def test_fee_bearing_case_due_vs_promise_due(store: TempStore) -> None:
    created, window = chi(2026, 10, 16, 10), chi(2026, 10, 16, 12)
    promise = promise_for(HandoffReason.FEE_BEARING_CHANGE, "nobody_online", created, window_start=window)
    assert promise.due_at == chi(2026, 10, 19, 19)
    due = case_due_at(HandoffReason.FEE_BEARING_CHANGE, promise, window)
    assert due == window
    add_case(
        store,
        ref="MHC-C-0002",
        reason=HandoffReason.FEE_BEARING_CHANGE,
        priority=Priority.P2,
        lifecycle="unassigned",
        created_at=created,
        due_at=due,
        promise=promise,
    )
    run = job(store, chi(2026, 10, 16, 13)).tick()
    assert kinds_of(store, "MHC-C-0002").count("overdue") == 1
    with store.uow() as tx:
        current = tx.cases.promises.current(CASE_REF.validate_python("MHC-C-0002"))
    assert current is not None
    assert current.status == "open"
    assert run.promises_missed == 0


def test_stuck_waiting(store: TempStore) -> None:
    rep = StaffRole.REPRESENTATIVE
    plain_case(
        store,
        "MHC-C-0003",
        lifecycle="waiting",
        due=None,
        created=chi(2026, 10, 16, 8),
        owner_role=rep,
        wake_up_at=chi(2026, 10, 16, 11),
    )
    plain_case(
        store,
        "MHC-C-0004",
        lifecycle="waiting",
        due=None,
        created=chi(2026, 10, 16, 8),
        owner_role=rep,
        wake_up_at=chi(2026, 10, 16, 13),
    )
    run = job(store, chi(2026, 10, 16, 12)).tick()
    assert kinds_of(store, "MHC-C-0003") == ["stuck_waiting"]
    assert kinds_of(store, "MHC-C-0004") == []
    assert run.stuck_waiting == 1


def test_due_soon(store: TempStore) -> None:
    for ref, hour in (("MHC-C-0005", 13), ("MHC-C-0006", 14), ("MHC-C-0007", 15)):
        plain_case(
            store, ref, lifecycle="unassigned", due=chi(2026, 10, 16, hour), created=chi(2026, 10, 16, 9, 50)
        )
    run = job(store, chi(2026, 10, 16, 10)).tick()
    assert kinds_of(store, "MHC-C-0005") == ["due_soon"]
    assert kinds_of(store, "MHC-C-0006") == ["due_soon"]
    assert kinds_of(store, "MHC-C-0007") == []
    assert run.due_soon == 2


def test_unowned_only_on_shift(store: TempStore) -> None:
    plain_case(store, "MHC-C-0008", lifecycle="unassigned", due=None, created=chi(2026, 10, 16, 9))
    plain_case(
        store,
        "MHC-C-0009",
        lifecycle="claimed",
        due=None,
        created=chi(2026, 10, 16, 9),
        owner_role=StaffRole.REPRESENTATIVE,
    )
    plain_case(store, "MHC-C-0010", lifecycle="unassigned", due=None, created=chi(2026, 10, 16, 9, 45))
    at = chi(2026, 10, 16, 10)
    assert job(store, at).tick().unowned == 0
    assert count(store, "case_events") == 0
    set_demo(store, staffing="simulated_on_shift")
    run = job(store, at).tick()
    assert run.unowned == 1
    assert kinds_of(store, "MHC-C-0008") == ["unowned"]
    assert kinds_of(store, "MHC-C-0009") == []
    assert kinds_of(store, "MHC-C-0010") == []


def test_p0_never_overdue(store: TempStore) -> None:
    created = chi(2026, 10, 16, 10)
    promise = promise_for(HandoffReason.SAFETY, "nobody_online", created)
    assert promise.due_at is None
    add_case(
        store,
        ref="MHC-C-0012",
        reason=HandoffReason.SAFETY,
        priority=Priority.P0,
        lifecycle="unassigned",
        created_at=created,
        due_at=None,
        promise=promise,
    )
    job(store, chi(2026, 10, 19, 20)).tick()
    assert kinds_of(store, "MHC-C-0012") == []
    with store.uow() as tx:
        current = tx.cases.promises.current(CASE_REF.validate_python("MHC-C-0012"))
    assert current is not None
    assert current.status == "open"


def test_tick_idempotent(store: TempStore) -> None:
    billing_case(store, "MHC-C-0001", chi(2026, 10, 15, 10))
    plain_case(
        store, "MHC-C-0013", lifecycle="unassigned", due=chi(2026, 10, 16, 21), created=chi(2026, 10, 16, 9)
    )
    at = chi(2026, 10, 16, 20)
    job(store, at).tick()
    after_first = count(store, "case_events")
    job(store, at).tick()
    assert count(store, "case_events") == after_first
    assert count(store, "job_runs") == 2
    job(store, chi(2026, 10, 19, 10)).tick()
    assert kinds_of(store, "MHC-C-0001").count("overdue") == 1
    assert kinds_of(store, "MHC-C-0013").count("due_soon") == 1


def test_abandonment_sweep(store: TempStore) -> None:
    wall = WallClock(datetime(2026, 10, 21, 19, 0, tzinfo=UTC))
    now = wall.now
    a = add_conversation(store, last_customer_wall_at=now - timedelta(minutes=30))
    b = add_conversation(store, last_customer_wall_at=now - timedelta(minutes=29))
    c = add_conversation(store, last_customer_wall_at=None)
    others = [
        add_conversation(store, run_tag=tag, last_customer_wall_at=now - timedelta(hours=2))
        for tag in ("eval", "load", "seed")
    ]
    handed = add_conversation(store, outcome="handed_off", last_customer_wall_at=now - timedelta(hours=2))
    run = job(store, chi(2026, 10, 16, 10), wall=wall).tick()
    assert run.abandoned == 1
    with store.uow() as tx:
        row_a = tx.core.conversations.lookup(str(a))
        assert row_a is not None
        assert getattr(row_a, "outcome", None) == "abandoned"
        assert getattr(row_a, "ended_wall_at", None) == now - timedelta(minutes=30) + timedelta(minutes=30)
        for tid in (b, c, *others):
            untouched = tx.core.conversations.lookup(str(tid))
            assert getattr(untouched, "outcome", None) == "open"
            assert getattr(untouched, "ended_wall_at", None) is None
        done = tx.core.conversations.lookup(str(handed))
        assert getattr(done, "outcome", None) == "handed_off"


def test_prune_once_per_day(store: TempStore) -> None:
    calls: list[int] = []

    def prune() -> int:
        calls.append(1)
        return 7

    wall = WallClock(datetime(2026, 10, 21, 14, 0, tzinfo=UTC))
    sched = SchedulerJob(store.uow, object(), FixedClock(chi(2026, 10, 16, 10)), prune, wall)
    seen = []
    for moment in (
        datetime(2026, 10, 21, 14, 0, tzinfo=UTC),
        datetime(2026, 10, 21, 20, 0, tzinfo=UTC),
        datetime(2026, 10, 22, 3, 0, tzinfo=UTC),
        datetime(2026, 10, 22, 5, 0, tzinfo=UTC),
    ):
        wall.now = moment
        seen.append(sched.tick().pruned)
    assert seen == [7, None, None, 7]
    assert len(calls) == 2
    stored = [json.loads(r["counts_json"])["pruned"] for r in rows(store, "job_runs")]
    assert sorted(stored, key=lambda v: (v is None, v)) == [7, 7, None, None]


def test_wf7_records(store: TempStore) -> None:
    billing_case(store, "MHC-C-0001", chi(2026, 10, 15, 10))
    run = job(store, chi(2026, 10, 16, 20)).tick()
    assert count(store, "job_runs") == 1
    with store.uow() as tx:
        events = tx.cases.case_events.list_for_case(CASE_REF.validate_python("MHC-C-0001"))
        promise = tx.cases.promises.current(CASE_REF.validate_python("MHC-C-0001"))
    assert promise is not None
    overdue = next(e for e in events if e.kind == "overdue")
    assert overdue.job_run_id == run.job_run_id
    missed = next(e for e in events if e.kind == "promise_missed")
    assert missed.job_run_id == run.job_run_id
    assert missed.detail["promise_id"] == promise.id


def test_records_hold_no_pii(store: TempStore) -> None:
    with store.uow() as tx:
        customer = tx.core.reads.customer(CUSTOMER.validate_python("MHC-10002"))
    assert customer is not None
    assert len([ch for ch in customer.phone if ch.isdigit()]) == 10
    created = chi(2026, 10, 16, 9)
    tid = add_conversation(store)
    with store.uow(write=True) as tx:
        tx.core.messages.append(
            tid, "customer", f"Hi, this is {customer.name}, call me on {customer.phone}", created
        )
        tx.commit()
    promise = promise_for(HandoffReason.BILLING_DISPUTE, "nobody_online", created)
    add_case(
        store,
        ref="MHC-C-0014",
        reason=HandoffReason.BILLING_DISPUTE,
        priority=Priority.P3,
        lifecycle="unassigned",
        created_at=created,
        due_at=chi(2026, 10, 16, 12),
        promise=promise,
        thread_id=tid,
        customer_id=CUSTOMER.validate_python("MHC-10002"),
    )
    demo: DemoService = make_demo(store, ConvertingCases())
    demo.advance_clock("plus_4h", actor=actor_for(StaffRole.SUPERVISOR), request_id=new_request_id())
    demo.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    SchedulerJob(store.uow, object(), FixedClock(chi(2026, 10, 16, 14)), lambda: 0, WallClock()).tick()
    needles = [p for p in customer.name.split() if len(p) > 1] + [customer.phone]
    if customer.email:
        needles.append(customer.email)
    for table in ("job_runs", "demo_events", "case_events"):
        blob = json.dumps(rows(store, table), default=str)
        for needle in needles:
            assert needle not in blob, (table, "pii")


def test_scheduler_thread_runs_and_stops() -> None:
    counter = {"n": 0}

    def tick() -> None:
        counter["n"] += 1

    thread = SchedulerThread(tick, interval_s=0.01)
    thread.start()
    deadline = time.monotonic() + 2
    while counter["n"] < 2 and time.monotonic() < deadline:
        time.sleep(0.005)
    thread.stop()
    assert counter["n"] >= 2
    assert thread.alive is False
    frozen = counter["n"]
    time.sleep(0.05)
    assert counter["n"] == frozen
    with pytest.raises(RuntimeError):
        thread.start()


def test_scheduler_thread_survives_a_raising_tick(caplog: pytest.LogCaptureFixture) -> None:
    counter = {"n": 0, "calls": 0}

    def tick() -> None:
        counter["calls"] += 1
        if counter["calls"] == 1:
            raise RuntimeError("tick secret")
        counter["n"] += 1

    with caplog.at_level("WARNING"):
        thread = SchedulerThread(tick, interval_s=0.01)
        thread.start()
        deadline = time.monotonic() + 2
        while counter["n"] < 1 and time.monotonic() < deadline:
            time.sleep(0.005)
        thread.stop()
    assert counter["n"] >= 1
    assert "scheduler tick raised" in caplog.text
    assert "tick secret" not in caplog.text
    assert counter["calls"] >= 2
