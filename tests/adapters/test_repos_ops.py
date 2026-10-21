"""AEA-32 repos_ops: round trips, upsert, restart days, deploy status, alert states, live-only signals."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from meridian.adapters.sqlite.repos_ops import (
    ALERT_TYPES,
    DeployRecord,
    EvalCaseResultRow,
    EvalRunRow,
    HealthEvent,
)
from meridian.ports.runtime import UnitOfWork
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.ops_support import BASE, add_conversation, add_turn, chi


def _event(kind: str, at: datetime, alert_type: str | None = None, reason: str | None = None) -> HealthEvent:
    return HealthEvent.model_validate(
        {
            "at_wall": at,
            "kind": kind,
            "alert_type": alert_type,
            "reason_code": reason,
            "value": 1.5,
            "threshold": 2.5,
            "agent_version": "test-ops",
        }
    )


def _run(**kw: object) -> EvalRunRow:
    data: dict[str, object] = {
        "run_id": "run-1",
        "suite": "worked-pairs",
        "split": None,
        "agent_version": "test-ops",
        "harness_commit": "abc123def456",
        "harness_digest": "d1g3st",
        "experiment_id": None,
        "repeats": 1,
        "started_at": datetime(2026, 10, 21, 18, 0, tzinfo=UTC),
        "finished_at": datetime(2026, 10, 21, 18, 5, tzinfo=UTC),
        "status": "completed",
        "cases_expected": 2,
        "cases_scored": 2,
        "index_manifest_hash": None,
        "judge_spend_usd": 0.0,
    }
    data.update(kw)
    return EvalRunRow.model_validate(data)


def _results(run_id: str = "run-1") -> list[EvalCaseResultRow]:
    return [
        EvalCaseResultRow.model_validate(
            {
                "run_id": run_id,
                "case_id": case,
                "repeat": 0,
                "thread_id": None,
                "passed_hard": True,
                "items": [{"item": "must_do", "index": 0, "passed": True, "failing_quote": None}],
                "outcome": "resolved",
                "in_scope": True,
                "topic": "billing",
            }
        )
        for case in ("WP-1", "WP-3")
    ]


def _write(store: TempStore, fn: Callable[[UnitOfWork], None]) -> None:
    with store.uow(write=True) as tx:
        fn(tx)
        tx.commit()


def test_round_trips() -> None:
    with temp_sqlite() as store:
        kinds = ("check_ok", "check_failed", "restart", "alert_fired", "alert_cleared")

        def go(tx: UnitOfWork) -> None:
            for kind in kinds:
                alert = "zero_traffic" if kind.startswith("alert") else None
                tx.ops.health.append(_event(kind, BASE, alert, "r"))
            tx.ops.deploy.insert(
                DeployRecord(
                    deploy_id="dep-1",
                    at_wall=BASE,
                    agent_version="test-ops",
                    git_commit="abc",
                    image_digest="sha256:x",
                    config_hash="cfg",
                    trace_export_on=True,
                    status="started",
                )
            )
            tx.ops.eval.upsert_report(_run(), _results(), '{"k":1}')

        _write(store, go)
        with store.uow() as tx:
            assert tx.ops.health.last_restart() == _event("restart", BASE, None, "r")
            dep = tx.ops.deploy.latest()
            assert dep is not None and dep.trace_export_on is True and dep.git_commit == "abc"
            stored = tx.ops.eval.latest_completed("worked-pairs", None)
            assert stored is not None and stored.summary_json == '{"k":1}'
            assert stored.run_id == "run-1"
            assert tx.ops.eval.case_results("run-1") == _results()
            raw = tx.connection.execute("SELECT at_wall FROM health_events LIMIT 1").fetchone()[0]
        print(raw)
        assert raw == "2026-10-21T19:00:00+00:00"


def test_upsert_report_by_run_id() -> None:
    with temp_sqlite() as store:
        outcomes: list[bool] = []

        def first(tx: UnitOfWork) -> None:
            outcomes.append(tx.ops.eval.upsert_report(_run(), _results(), "{}"))

        _write(store, first)
        _write(store, first)
        assert outcomes == [True, False]

        def changed(tx: UnitOfWork) -> None:
            outcomes.append(tx.ops.eval.upsert_report(_run(cases_scored=1), _results()[:1], "{}"))

        _write(store, changed)
        assert outcomes == [True, False, True]
        with store.uow() as tx:
            assert tx.connection.execute("SELECT COUNT(*) FROM eval_runs").fetchone()[0] == 1
            assert tx.connection.execute("SELECT cases_scored FROM eval_runs").fetchone()[0] == 1
            assert tx.connection.execute("SELECT COUNT(*) FROM eval_case_results").fetchone()[0] == 1


def test_restart_and_deploy_reads() -> None:
    with temp_sqlite() as store:

        def go(tx: UnitOfWork) -> None:
            tx.ops.health.append(_event("restart", chi(2026, 10, 21, 23, 30)))
            tx.ops.health.append(_event("restart", chi(2026, 10, 22, 0, 30)))
            tx.ops.deploy.insert(DeployRecord(deploy_id="old", at_wall=BASE, agent_version="v"))
            tx.ops.deploy.insert(
                DeployRecord(deploy_id="new", at_wall=BASE + timedelta(hours=1), agent_version="v")
            )

        _write(store, go)
        with store.uow() as tx:
            assert tx.ops.health.restarts_by_day("America/Chicago") == [
                (date(2026, 10, 21), 1),
                (date(2026, 10, 22), 1),
            ]
            last = tx.ops.health.last_restart()
            assert last is not None and last.at_wall == chi(2026, 10, 22, 0, 30)
            dep = tx.ops.deploy.latest()
            assert dep is not None and dep.deploy_id == "new"


def test_deploy_set_status() -> None:
    with temp_sqlite() as store:
        results: list[bool] = []

        def go(tx: UnitOfWork) -> None:
            tx.ops.deploy.insert(
                DeployRecord(deploy_id="d", at_wall=BASE, agent_version="v", status="started")
            )
            results.append(tx.ops.deploy.set_status("d", "completed"))
            results.append(tx.ops.deploy.set_status("nope", "failed"))

        _write(store, go)
        assert results == [True, False]
        with store.uow() as tx:
            dep = tx.ops.deploy.latest()
            assert dep is not None and dep.status == "completed"


def test_latest_alert_states_defaults_and_newest_row() -> None:
    with temp_sqlite() as store:
        with store.uow() as tx:
            states = tx.ops.health.latest_alert_states()
        assert tuple(states) == ALERT_TYPES
        assert all(s.state == "quiet" and s.fired_at is None for s in states.values())

        def go(tx: UnitOfWork) -> None:
            h = tx.ops.health
            h.append(_event("alert_fired", BASE, "zero_traffic"))
            h.append(_event("alert_cleared", BASE + timedelta(minutes=1), "zero_traffic"))
            h.append(_event("alert_fired", BASE + timedelta(minutes=2), "zero_traffic"))

        _write(store, go)
        with store.uow() as tx:
            s = tx.ops.health.latest_alert_states()["zero_traffic"]
        assert s.state == "firing" and s.fired_at == BASE + timedelta(minutes=2)


def test_signals_read_live_turns_only() -> None:
    with temp_sqlite() as store:
        live = add_conversation(store, run_tag="live", started_wall_at=BASE)
        evalc = add_conversation(store, run_tag="eval", started_wall_at=BASE)
        seed = add_conversation(store, run_tag="seed", started_wall_at=BASE)
        loadc = add_conversation(store, run_tag="load", started_wall_at=BASE)
        since = BASE - timedelta(minutes=60)
        add_turn(store, live, run_tag="live", replied_at=BASE - timedelta(minutes=5), trace_export="failed")
        add_turn(store, evalc, run_tag="eval", replied_at=BASE - timedelta(minutes=5))
        add_turn(store, loadc, run_tag="load", replied_at=BASE - timedelta(minutes=5))
        add_turn(store, live, run_tag="eval", replied_at=BASE - timedelta(minutes=5))
        add_turn(store, seed, run_tag="live", replied_at=BASE - timedelta(minutes=5))
        add_turn(store, live, run_tag="live", replied_at=BASE - timedelta(minutes=90))
        # inserted last, replied long ago: still "latest" by insertion order
        add_turn(store, live, run_tag="live", replied_at=BASE - timedelta(days=3), trace_export="sent")
        with store.uow() as tx:
            assert len(tx.ops.signals.live_turns_replied_since(since)) == 1
            assert tx.ops.signals.latest_live_trace_export() == "sent"
