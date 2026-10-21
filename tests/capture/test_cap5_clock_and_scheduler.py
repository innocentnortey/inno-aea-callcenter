"""AEA-52 CAP-5: demo controls and the scheduler job on the real app (AC-6, AC-12, AC-24, AC-25, AC-26).

Tests that need a live chat (CON-3 `clock_changed`, WP-4 variants) and the CON-19 tile wait on AEA-51 and AEA-53.
"""

from __future__ import annotations

import itertools
import json
import logging
import sqlite3
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from langgraph.checkpoint.base import empty_checkpoint

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import ConversationRow
from meridian.domain.common import ThreadId
from meridian.services.health import AlertEvaluator, AlertSettings
from meridian.services.scheduler import ERROR_KINDS, PROMISE_MISSED_KIND
from meridian.web.container import Key
from meridian.web.deps import UOW_FACTORY
from meridian.web.logging import ALLOWED_FIELDS, AllowListFormatter
from tests.integration.staff_support import (
    CHICAGO,
    DEMO_NEEDS,
    DEMO_OPERATIONS,
    OVERDUE_KIND,
    SCHEDULER_THREAD,
    Actor,
    advance,
    assert_bound,
    call,
    open_staff_run,
    parse_dt,
    scheduler_job,
    sentinel,
    set_staffing,
    sign_in,
)
from tests.journeys.support.env import PLACEHOLDER_ANTHROPIC_KEY, PLACEHOLDER_OPENROUTER_KEY
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.server import StepClock

STEPS = ("next_business_morning", "plus_4h", "plus_4h", "plus_4h", "plus_1h")
PAST_DUE = ("MHC-C-0006", "MHC-C-0007")


def drive_seed_clock(sup: Actor) -> list[httpx.Response]:
    """Fri 10:00 -> Mon 07:00 -> 11:00 -> 15:00 -> 19:00 -> 20:00."""
    responses = [advance(sup, step) for step in STEPS]
    assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
    return responses


def stale_check(run: JourneyRun) -> int:
    """Evaluates the stale-tick rule with a clock 181 s ahead of the run's wall clock, read at evaluate time."""
    now_fn: Callable[[], datetime] = run.clock if run.clock is not None else (lambda: datetime.now(UTC))
    evaluator = AlertEvaluator(
        run.container.get(UOW_FACTORY),
        run.container.get(Key[Any]("ledger")),
        AlertSettings(),
        lambda: now_fn() + timedelta(seconds=181),
        run.container.limits.spend.daily_cap_usd,
        agent_version=run.settings.agent_version,
    )
    evaluator.evaluate()
    return run.db.count("health_events", "kind = 'alert_fired' AND alert_type = 'scheduler_stale'")


def assert_overdue_and_missed(run: JourneyRun) -> None:
    for ref in PAST_DUE:
        overdue = run.db.rows(
            "SELECT job_run_id FROM case_events WHERE case_ref = ? AND kind = ?", (ref, OVERDUE_KIND)
        )
        assert overdue, ref
        for row in overdue:
            assert row["job_run_id"] is not None
            status = run.db.scalar("SELECT status FROM job_runs WHERE job_run_id = ?", (row["job_run_id"],))
            assert status == "completed"
        assert run.db.scalar("SELECT status FROM promises WHERE case_ref = ?", (ref,)) == "missed"
        missed = run.db.rows(
            "SELECT job_run_id FROM case_events WHERE case_ref = ? AND kind = ?", (ref, PROMISE_MISSED_KIND)
        )
        assert missed
        assert all(r["job_run_id"] is not None for r in missed)
    assert run.db.count("case_events", "case_ref = 'MHC-C-0008' AND kind = ?", (OVERDUE_KIND,)) == 0


@pytest.mark.parametrize("variant", ["seeds"])
def test_clock_past_due_and_scheduler(journey: JourneyRun, variant: str) -> None:
    sup = sign_in(journey, "supervisor")
    responses = drive_seed_clock(sup)
    assert [r.json()["became_overdue"] for r in responses] == [0, 0, 0, 0, 2]
    last = parse_dt(responses[-1].json()["now"]).astimezone(CHICAGO)
    assert (last.year, last.month, last.day, last.hour) == (2026, 10, 19, 20)

    events = journey.db.rows("SELECT * FROM demo_events ORDER BY at_wall, rowid")
    assert len(events) == 5
    for event, step, response in zip(events, STEPS, responses, strict=True):
        assert event["kind"] == "clock_advanced"
        assert event["step"] == step
        assert event["became_overdue"] == response.json()["became_overdue"]
        assert event["request_id"] == response.headers["X-Request-ID"]
        assert event["role"] == "supervisor"
    for before, after in itertools.pairwise(events):
        assert before["demo_after"] == after["demo_before"]

    job = scheduler_job(journey)
    run1 = job.tick()
    assert run1.status == "completed"
    row = journey.db.one("SELECT * FROM job_runs WHERE job_run_id = ?", (run1.job_run_id,))
    assert row["status"] == "completed"
    assert row["finished_wall_at"] is not None
    assert_overdue_and_missed(journey)

    oversight = call(sup, "GET", "/api/staff/oversight", "getOversight").json()
    overdue_refs = {r["reference"] for r in oversight["lanes"]["overdue"]["rows"]}
    assert {"MHC-C-0005", "MHC-C-0006", "MHC-C-0007"} <= overdue_refs
    assert "MHC-C-0008" in {r["reference"] for r in oversight["lanes"]["p0_p1"]["rows"]}
    assert stale_check(journey) == 1
    print("demo_events:", [(e["step"], e["became_overdue"]) for e in events])
    print("job_run:", row["job_run_id"], row["status"], "overdue lane:", sorted(overdue_refs))


@pytest.mark.parametrize("variant", ["seeds"])
def test_wf7_ticks(
    journey: JourneyRun, journey_clock: StepClock, monkeypatch: pytest.MonkeyPatch, variant: str
) -> None:
    sup = sign_in(journey, "supervisor")
    drive_seed_clock(sup)
    job = scheduler_job(journey)
    r1 = job.tick()
    assert r1.status == "completed"
    assert (
        journey.db.scalar("SELECT status FROM job_runs WHERE job_run_id = ?", (r1.job_run_id,)) == "completed"
    )
    assert_overdue_and_missed(journey)

    n = journey.db.count("case_events", "kind = ?", (OVERDUE_KIND,))
    r2 = job.tick()
    assert r2.status == "completed"
    assert journey.db.count("case_events", "kind = ?", (OVERDUE_KIND,)) == n
    assert journey.db.count("job_runs", "job_run_id = ?", (r2.job_run_id,)) == 1

    cp = journey.container.get(Key[Any]("checkpointer"))

    def boom(*_a: object, **_k: object) -> int:
        raise RuntimeError("forced tick failure")

    monkeypatch.setattr(cp, "prune", boom)
    journey_clock.advance(86_400)  # a new Chicago wall day, so the tick prunes
    failed = job.tick()
    assert failed.status == "failed"
    assert failed.error_kind == "prune_failed"
    assert failed.error_kind in ERROR_KINDS
    assert "forced" not in failed.error_kind
    row = journey.db.one("SELECT * FROM job_runs WHERE job_run_id = ?", (failed.job_run_id,))
    assert row["status"] == "failed"
    assert row["error_kind"] == "prune_failed"
    assert row["finished_wall_at"] is not None
    monkeypatch.undo()
    r3 = job.tick()
    assert r3.status == "completed"
    assert r3.error_kind is None
    assert stale_check(journey) == 1
    for run_id in (r1.job_run_id, r2.job_run_id, failed.job_run_id, r3.job_run_id):
        r = journey.db.one(
            "SELECT job_run_id, status, error_kind FROM job_runs WHERE job_run_id = ?", (run_id,)
        )
        print("job_run:", r)
    print(
        "overdue rows:",
        journey.db.rows("SELECT case_ref, job_run_id FROM case_events WHERE kind = ?", (OVERDUE_KIND,)),
    )


def _add_live_conversation(
    run: JourneyRun, *, tag: str, last: datetime, started: datetime, text: str
) -> ThreadId:
    thread = ThreadId(str(uuid.uuid4()))
    uow = run.container.get(UOW_FACTORY)
    with uow(write=True) as tx:
        tx.core.conversations.insert(
            ConversationRow(
                thread_id=thread,
                demo_session="aea52-sweep",
                run_tag=tag,  # type: ignore[arg-type]
                agent_version="test",
                started_at=DEMO_START,
                started_wall_at=started,
                outcome="open",
                last_customer_wall_at=last,
            )
        )
        tx.core.messages.append(thread, "customer", text, DEMO_START)
        tx.commit()
    return thread


def _put_checkpoints(cp: Any, thread: str, n: int) -> None:
    cfg: Any = {"configurable": {"thread_id": thread, "checkpoint_ns": ""}}
    for i in range(n):
        cfg = cp.saver.put(cfg, empty_checkpoint(), {"source": "loop", "step": i, "parents": {}}, {})


def _checkpoint_counts(path: Any) -> dict[str, int]:
    conn = sqlite3.connect(path)
    try:
        return {
            t: int(n)
            for t, n in conn.execute("SELECT thread_id, COUNT(*) FROM checkpoints GROUP BY thread_id")
        }
    finally:
        conn.close()


def test_daily_prune_and_abandonment(journey: JourneyRun, journey_clock: StepClock) -> None:
    assert_bound(journey, DEMO_NEEDS, DEMO_OPERATIONS)
    job = scheduler_job(journey)
    job.tick()  # today's prune is done now (by us or by the runner)
    t = journey_clock() + timedelta(seconds=86_400)
    seed_before = journey.db.rows("SELECT thread_id, outcome FROM conversations WHERE run_tag = 'seed'")
    started = t - timedelta(minutes=40)
    text = "Synthetic sweep message."
    a = _add_live_conversation(
        journey, tag="live", last=t - timedelta(minutes=31), started=started, text=text
    )
    b = _add_live_conversation(
        journey, tag="live", last=t - timedelta(minutes=29), started=started, text=text
    )
    e = _add_live_conversation(
        journey, tag="eval", last=t - timedelta(minutes=31), started=started, text=text
    )
    load = _add_live_conversation(
        journey, tag="load", last=t - timedelta(minutes=31), started=started, text=text
    )
    s = _add_live_conversation(
        journey, tag="seed", last=t - timedelta(minutes=31), started=started, text=text
    )
    messages = {x: journey.db.count("messages", "thread_id = ?", (str(x),)) for x in (a, b, e, load, s)}

    cp = journey.container.get(Key[Any]("checkpointer"))
    _put_checkpoints(cp, str(a), 5)
    _put_checkpoints(cp, str(b), 3)
    extra = sum(
        n - 2 for tid, n in _checkpoint_counts(cp.path).items() if tid not in (str(a), str(b)) and n > 2
    )

    journey_clock.advance(86_400)
    job.tick()

    counts = _checkpoint_counts(cp.path)
    assert counts[str(a)] == 2
    assert counts[str(b)] == 2
    runs = [
        r
        for r in journey.db.rows("SELECT started_wall_at, counts_json FROM job_runs")
        if parse_dt(r["started_wall_at"]) >= t - timedelta(minutes=1)
    ]
    parsed = [json.loads(r["counts_json"]) for r in runs]
    pruned = [c["pruned"] for c in parsed if c.get("pruned") is not None]
    assert pruned
    assert sum(pruned) == 4 + extra
    assert sum(c.get("abandoned") or 0 for c in parsed) == 1
    row_a = journey.db.one(
        "SELECT outcome, ended_wall_at, last_customer_wall_at FROM conversations WHERE thread_id = ?",
        (str(a),),
    )
    assert row_a["outcome"] == "abandoned"
    assert parse_dt(row_a["ended_wall_at"]) == parse_dt(row_a["last_customer_wall_at"]) + timedelta(
        minutes=30
    )
    for other in (b, e, load, s):
        assert (
            journey.db.scalar("SELECT outcome FROM conversations WHERE thread_id = ?", (str(other),))
            == "open"
        )
    assert {x: journey.db.count("messages", "thread_id = ?", (str(x),)) for x in messages} == messages
    assert journey.db.rows(
        "SELECT thread_id, outcome FROM conversations WHERE run_tag = 'seed' AND thread_id != ?", (str(s),)
    ) == [r for r in seed_before]
    print(
        "checkpoints A/B:",
        counts[str(a)],
        counts[str(b)],
        "pruned sum:",
        sum(pruned),
        "messages:",
        list(messages.values()),
    )
    print(
        "outcomes:",
        {
            n: journey.db.scalar("SELECT outcome FROM conversations WHERE thread_id = ?", (str(x),))
            for n, x in zip("ABELS", (a, b, e, load, s), strict=True)
        },
    )


def _key_env() -> dict[str, str]:
    return {
        "MERIDIAN_EVAL_KEY": sentinel("eval"),
        "LANGFUSE_PUBLIC_KEY": sentinel("lfpk"),
        "LANGFUSE_SECRET_KEY": sentinel("lfsk"),
    }


def test_wf5_no_key_values_or_outbound(request: pytest.FixtureRequest) -> None:
    env = _key_env()
    strict = bool(request.config.getoption("--journeys-strict"))
    with open_staff_run(extra_env=env, strict=strict, nodeid=request.node.nodeid) as run:
        assert_bound(run, DEMO_NEEDS, DEMO_OPERATIONS)
        sup = sign_in(run, "supervisor")
        texts = [
            set_staffing(sup, "simulated_on_shift").text,
            set_staffing(sup, "nobody_online").text,
            advance(sup, "plus_4h").text,
        ]
        secrets_ = (
            *env.values(),
            PLACEHOLDER_ANTHROPIC_KEY,
            PLACEHOLDER_OPENROUTER_KEY,
            *run.secret_values(),
            sup.cookie,
        )
        rows = str(run.db.rows("SELECT * FROM demo_events"))
        logs = run.logs.all_text()
        for value in secrets_:
            assert value not in rows
            assert all(value not in t for t in texts)
            assert value not in logs
        assert run.guard.blocked == []
    print("0 sentinel hits; 0 connection attempts")


class _Keep(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def test_wf7_logs_keys_and_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    env = _key_env()
    phrase = sentinel("phrase")
    strict = bool(request.config.getoption("--journeys-strict"))
    keep = _Keep()
    root = logging.getLogger()
    root.addHandler(keep)
    try:
        with open_staff_run(extra_env=env, strict=strict, nodeid=request.node.nodeid) as run:
            assert run.clock is not None
            assert_bound(run, DEMO_NEEDS, DEMO_OPERATIONS)
            sup = sign_in(run, "supervisor")
            tomorrow = run.clock() + timedelta(days=1)
            job = scheduler_job(run)
            job.tick()
            _add_live_conversation(
                run,
                tag="live",
                last=tomorrow - timedelta(minutes=31),
                started=tomorrow - timedelta(minutes=40),
                text=f"Synthetic message {phrase}",
            )
            drive_seed_clock(sup)
            job.tick()
            job.tick()
            run.clock.advance(86_400)

            def boom(*_a: object, **_k: object) -> int:
                raise RuntimeError(f"forced failure {phrase}")

            # a failed prune is the one tick path that logs: it makes the allow-list check below non-vacuous
            monkeypatch.setattr(run.container.get(Key[Any]("checkpointer")), "prune", boom)
            failed = job.tick()
            monkeypatch.undo()
            assert failed.error_kind == "prune_failed"
            logs = run.logs.all_text()
            job_rows = str(run.db.rows("SELECT * FROM job_runs"))
            for value in (phrase, *env.values()):
                assert value not in logs
                assert value not in job_rows
            assert run.guard.blocked == []
    finally:
        root.removeHandler(keep)
    allowed = set().union(*ALLOWED_FIELDS.values()) | {"record", "logger", "level", "length", "exc_type"}
    mine = [
        r
        for r in keep.records
        if r.threadName == SCHEDULER_THREAD or r.name.startswith("meridian.services.scheduler")
    ]
    assert mine, "the failed tick logged nothing"
    for rec in mine:
        keys = set(json.loads(AllowListFormatter().format(rec)))
        assert keys <= allowed, keys - allowed
        assert phrase not in repr(vars(rec))
    print("scheduler records:", len(mine), "0 sentinel hits; 0 connection attempts")
