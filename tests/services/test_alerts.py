"""AEA-32 alerts: every rule fires and clears from stored rows, on change only; test traffic excluded."""

from __future__ import annotations

import threading
import typing
from datetime import timedelta
from pathlib import Path

import pytest
import yaml

from meridian.adapters.sqlite.repos_cases import DEMO_START, CaseRow
from meridian.adapters.sqlite.repos_ops import ALERT_TYPES, AlertType, HealthEvent
from meridian.policy.limits import Limits
from meridian.services.health import AlertSettings, AlertWriter, Watchdog
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.ops_support import (
    BASE,
    FakeWall,
    LedgerDouble,
    add_conversation,
    add_live_turns,
    add_message,
    add_turn,
    chi,
    health_rows,
    make_evaluator,
    make_settings,
    ops_rows,
)
from tests.unit.adapters.sqlite.helpers import case_row, customer_id, new_thread

CAP = Limits().spend.daily_cap_usd


def _count(store: TempStore, kind: str, alert_type: str) -> int:
    return len([r for r in health_rows(store, kind) if r[1] == alert_type])


def _insert_restart(store: TempStore, at: object) -> None:
    with store.uow(write=True) as tx:
        tx.ops.health.append(
            HealthEvent.model_validate(
                {
                    "at_wall": at,
                    "kind": "restart",
                    "alert_type": None,
                    "reason_code": "r",
                    "value": 3.0,
                    "threshold": 3.0,
                    "agent_version": "t",
                }
            )
        )
        tx.commit()


def _fire_and_clear(store: TempStore, wall: FakeWall, ledger: LedgerDouble, alert_type: AlertType) -> None:
    ev = make_evaluator(store, wall, ledger)
    if alert_type == "spend_cap_reached":
        ledger.spent = CAP
        ev.evaluate()
        fired = _count(store, "alert_fired", alert_type)
        ledger.spent = CAP - 1
        ev.evaluate()
    elif alert_type == "p95_latency_over_12_5s":
        add_live_turns(store, 20, replied_at=wall.now - timedelta(minutes=10), server_ms=13_000)
        ev.evaluate()
        fired = _count(store, "alert_fired", alert_type)
        wall.now += timedelta(hours=2)
        ev.evaluate()
    elif alert_type == "failure_rate_over_2pct":
        add_live_turns(store, 19, replied_at=wall.now - timedelta(minutes=10))
        thread = add_conversation(store, run_tag="live", started_wall_at=wall.now - timedelta(minutes=30))
        add_turn(
            store,
            thread,
            run_tag="live",
            replied_at=wall.now - timedelta(minutes=10),
            outcome="degraded_handoff",
            degrade_reason="model_error",
        )
        ev.evaluate()
        fired = _count(store, "alert_fired", alert_type)
        wall.now += timedelta(hours=2)
        ev.evaluate()
    elif alert_type == "zero_traffic":
        add_conversation(store, run_tag="live", started_wall_at=chi(2026, 10, 21, 14, 0))
        wall.now = chi(2026, 10, 21, 19, 0)
        ev.evaluate()
        fired = _count(store, "alert_fired", alert_type)
        add_conversation(store, run_tag="live", started_wall_at=chi(2026, 10, 21, 19, 0))
        ev.evaluate()
    elif alert_type == "health_check_restart":
        _insert_restart(store, chi(2026, 10, 21, 14, 0))
        wall.now = chi(2026, 10, 21, 14, 5)
        ev.evaluate()
        fired = _count(store, "alert_fired", alert_type)
        wall.now = chi(2026, 10, 22, 0, 5)
        ev.evaluate()
    elif alert_type == "trace_export_failed":
        thread = add_conversation(store, run_tag="live", started_wall_at=wall.now)
        add_turn(store, thread, run_tag="live", replied_at=wall.now, trace_export="failed")
        ev.evaluate()
        fired = _count(store, "alert_fired", alert_type)
        add_turn(store, thread, run_tag="live", replied_at=wall.now, trace_export="sent")
        ev.evaluate()
        assert _count(store, "alert_cleared", alert_type) == 1
        add_turn(store, thread, run_tag="live", replied_at=wall.now, trace_export="off")
        ev.evaluate()
        assert _count(store, "alert_fired", alert_type) == 2
        return
    else:
        assert alert_type == "scheduler_stale"
        with store.uow(write=True) as tx:
            tx.cases.job_runs.start(
                "job-1", started_wall_at=wall() - timedelta(seconds=300), demo_now=DEMO_START
            )
            tx.commit()
        ev.evaluate()
        fired = _count(store, "alert_fired", alert_type)
        with store.uow(write=True) as tx:
            tx.cases.job_runs.start(
                "job-2", started_wall_at=wall() - timedelta(seconds=10), demo_now=DEMO_START
            )
            tx.commit()
        ev.evaluate()
    assert fired == 1
    assert _count(store, "alert_cleared", alert_type) == 1


@pytest.mark.parametrize("alert_type", ALERT_TYPES)
def test_each_alert_fires_and_clears(alert_type: AlertType) -> None:
    with temp_sqlite() as store:
        _fire_and_clear(store, FakeWall(BASE), LedgerDouble(0.0), alert_type)


def test_zero_traffic_quiet_hours_do_not_count() -> None:
    with temp_sqlite() as store:
        add_conversation(store, run_tag="live", started_wall_at=chi(2026, 10, 21, 21, 0))
        make_evaluator(store, FakeWall(chi(2026, 10, 22, 7, 0))).evaluate()
        assert health_rows(store) == []


def test_no_duplicate_events_without_change() -> None:
    with temp_sqlite() as store:
        ledger = LedgerDouble(CAP)
        ev = make_evaluator(store, FakeWall(BASE), ledger)
        ev.evaluate()
        ev.evaluate()
        assert _count(store, "alert_fired", "spend_cap_reached") == 1
        ledger.spent = 0.0
        ev.evaluate()
        ev.evaluate()
        assert _count(store, "alert_cleared", "spend_cap_reached") == 1
        assert len(health_rows(store)) == 2


def test_overdue_is_not_a_health_alert() -> None:
    with temp_sqlite() as store:
        with store.uow(write=True) as tx:
            for ref in (101, 102, 103):
                row: CaseRow = case_row(
                    new_thread(),
                    ref,
                    due_at=DEMO_START - timedelta(days=1),
                    created_at=DEMO_START - timedelta(days=2),
                    updated_at=DEMO_START - timedelta(days=2),
                )
                tx.cases.cases.insert(row)
            tx.commit()
        make_evaluator(store, FakeWall(BASE)).evaluate()
        assert health_rows(store) == []
    assert set(ALERT_TYPES) == set(typing.get_args(AlertType))
    spec = Path(__file__).resolve().parents[2] / "docs/ux/03-structure/ui-contracts.openapi.yaml"
    doc = yaml.load(spec.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)  # noqa: S506 - BaseLoader is safe
    enum = set(doc["components"]["schemas"]["MonitorAlert"]["properties"]["type"]["enum"])
    assert enum | {"scheduler_stale"} == set(ALERT_TYPES)
    assert not any("overdue" in t for t in ALERT_TYPES)


def test_test_traffic_excluded() -> None:
    with temp_sqlite() as store:
        wall = FakeWall(chi(2026, 10, 21, 19, 0))
        add_conversation(store, run_tag="live", started_wall_at=wall.now - timedelta(hours=5))
        for tag in ("eval", "load", "seed"):
            add_conversation(store, run_tag=tag, started_wall_at=wall.now - timedelta(minutes=10))
        make_evaluator(store, wall).evaluate()
        assert _count(store, "alert_fired", "zero_traffic") == 1
    with temp_sqlite() as store:
        wall = FakeWall(BASE)
        at = wall.now - timedelta(minutes=10)
        load = add_conversation(store, run_tag="load", started_wall_at=at)
        evalc = add_conversation(store, run_tag="eval", started_wall_at=at)
        for _ in range(25):
            add_turn(store, load, run_tag="load", replied_at=at, server_ms=20_000)
            add_turn(
                store,
                evalc,
                run_tag="eval",
                replied_at=at,
                outcome="degraded_handoff",
                degrade_reason="timeout",
            )
        make_evaluator(store, wall).evaluate()
        assert _count(store, "alert_fired", "p95_latency_over_12_5s") == 0
        assert _count(store, "alert_fired", "failure_rate_over_2pct") == 0


def test_alert_writer_once_while_firing() -> None:
    with temp_sqlite() as store:
        writer = AlertWriter(store.uow, FakeWall(BASE), "test-ops")
        barrier = threading.Barrier(2)

        def go() -> None:
            barrier.wait()
            writer.fire("trace_export_failed", "wrong_project")

        threads = [threading.Thread(target=go) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert _count(store, "alert_fired", "trace_export_failed") == 1
        with store.uow(write=True) as tx:
            tx.ops.health.append(
                HealthEvent.model_validate(
                    {
                        "at_wall": BASE,
                        "kind": "alert_cleared",
                        "alert_type": "trace_export_failed",
                        "reason_code": None,
                        "value": None,
                        "threshold": None,
                        "agent_version": "t",
                    }
                )
            )
            tx.commit()
        writer.fire("trace_export_failed", "wrong_project")
        assert _count(store, "alert_fired", "trace_export_failed") == 2


def test_evaluator_uses_injected_cap() -> None:
    with temp_sqlite() as store:
        make_evaluator(store, FakeWall(BASE), LedgerDouble(5.0), cap=5.0).evaluate()
        with store.uow() as tx:
            state = tx.ops.health.latest_alert_states()["spend_cap_reached"]
        assert state.state == "firing" and state.threshold == 5.0


def test_ops_records_hold_no_pii(tmp_path: Path) -> None:
    from meridian.adapters.sqlite.repos_ops import DeployRecord
    from tests.services.test_load_eval_reports import write_valid_reports

    with temp_sqlite() as store:
        with store.uow() as tx:
            customer = tx.core.reads.customer(customer_id("MHC-10002"))
        assert customer is not None
        first_name = customer.name.split()[0]
        phone = customer.phone
        digits = "".join(ch for ch in phone if ch.isdigit())
        thread = add_conversation(store, run_tag="live", started_wall_at=BASE)
        add_message(store, thread, f"hello {customer.name}")
        add_message(store, thread, f"call me at {phone}")
        settings = make_settings(tmp_path)
        secret = settings.session_secret.get_secret_value()
        wall = FakeWall(BASE)
        AlertWriter(store.uow, wall, "test-ops").fire("trace_export_failed", "wrong_project")
        ev = make_evaluator(store, wall, LedgerDouble(CAP))
        ev.evaluate()
        probes = iter([False, False, False])
        exits: list[int] = []
        wd = Watchdog(
            store.uow, lambda: next(probes), exits.append, ev, AlertSettings(), wall, agent_version="test-ops"
        )
        for _ in range(3):
            wd.run_once()
        with store.uow(write=True) as tx:
            tx.ops.deploy.insert(DeployRecord(deploy_id="d1", at_wall=BASE, agent_version="test-ops"))
            tx.commit()
        from meridian.services.health import load_eval_reports

        reports = tmp_path / "reports"
        write_valid_reports(reports)
        load_eval_reports(reports, store.uow, wall_clock=wall, agent_version="test-ops")
        rows = ops_rows(store)
        print(len(rows), "ops rows checked; exits", exits)
        assert exits == [1] and rows
        for text in rows:
            for needle in (first_name, phone, digits, secret):
                assert needle not in text
