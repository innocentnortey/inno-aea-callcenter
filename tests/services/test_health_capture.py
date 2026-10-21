"""AEA-12/14 capture: the watchdog against create_app's real async /healthz bound to the real Heartbeat (WF-17)."""

from __future__ import annotations

import time
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from meridian.services.health import AlertEvaluator, AlertSettings, Heartbeat, Watchdog
from meridian.web import deps
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.ops_support import (
    BASE,
    FakeWall,
    LedgerDouble,
    add_conversation,
    build_ops_app,
    chi,
    health_rows,
    make_settings,
)


def _watchdog(
    store: TempStore, client: TestClient, exits: list[int], wall: FakeWall, evaluator: AlertEvaluator
) -> Watchdog:
    return Watchdog(
        store.uow,
        lambda: client.get("/healthz").status_code == 200,
        exits.append,
        evaluator,
        AlertSettings(),
        wall,
        agent_version="test-ops",
    )


def _stop_beat(hb: Heartbeat) -> None:
    hb.beat(time.monotonic() - (AlertSettings().heartbeat_stale_after_s + 1))


def _evaluator(store: TempStore, wall: FakeWall) -> AlertEvaluator:
    return AlertEvaluator(store.uow, LedgerDouble(), AlertSettings(), wall, 30.0, agent_version="test-ops")


def test_watchdog_against_app_healthz(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with temp_sqlite() as store:
        wall = FakeWall(BASE)
        app = build_ops_app(
            monkeypatch, store=store, settings=make_settings(tmp_path), wall=wall, ledger=LedgerDouble()
        )
        with TestClient(app) as client:
            hb = app.state.container.get(deps.HEARTBEAT)
            assert isinstance(hb, Heartbeat)
            exits: list[int] = []
            wd = _watchdog(store, client, exits, wall, _evaluator(store, wall))
            wd.run_once()
            _stop_beat(hb)
            for _ in range(3):
                wd.run_once()
        rows = health_rows(store)
        print([(k, r) for k, _a, r in rows if k != "alert_fired"])
        assert [r[0] for r in rows if r[0] in ("check_ok", "check_failed", "restart")] == [
            "check_ok",
            "check_failed",
            "check_failed",
            "check_failed",
            "restart",
        ]
        assert exits == [1]


def test_watchdog_raises_zero_traffic_and_restart_alerts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with temp_sqlite() as store:
        wall = FakeWall(chi(2026, 10, 21, 19, 0))
        add_conversation(store, run_tag="live", started_wall_at=chi(2026, 10, 21, 14, 0))
        app = build_ops_app(
            monkeypatch, store=store, settings=make_settings(tmp_path), wall=wall, ledger=LedgerDouble()
        )
        with TestClient(app) as client:
            hb = app.state.container.get(deps.HEARTBEAT)
            assert isinstance(hb, Heartbeat)
            exits: list[int] = []
            wd = _watchdog(store, client, exits, wall, _evaluator(store, wall))
            wd.run_once()
            with store.uow() as tx:
                zero = tx.ops.health.latest_alert_states()["zero_traffic"]
            assert zero.state == "firing"
            assert [r for r in health_rows(store, "alert_fired") if r[1] == "zero_traffic"]

            _stop_beat(hb)
            for _ in range(3):
                wd.run_once()
            assert exits == [1]
            hb.beat(time.monotonic())
            second = _watchdog(store, client, exits, wall, _evaluator(store, wall))
            second.run_once()
            with store.uow() as tx:
                states = tx.ops.health.latest_alert_states()
            print(health_rows(store, "alert_fired"), states["zero_traffic"], states["health_check_restart"])
            assert states["health_check_restart"].state == "firing"
    with temp_sqlite() as store:
        wall = FakeWall(chi(2026, 10, 22, 7, 0))
        add_conversation(store, run_tag="live", started_wall_at=chi(2026, 10, 21, 21, 0))
        app = build_ops_app(
            monkeypatch, store=store, settings=make_settings(tmp_path), wall=wall, ledger=LedgerDouble()
        )
        with TestClient(app) as client:
            _watchdog(store, client, [], wall, _evaluator(store, wall)).run_once()
        assert health_rows(store, "alert_fired") == []


def test_example_pair_wf17(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with temp_sqlite() as store:
        wall = FakeWall(BASE)
        app = build_ops_app(
            monkeypatch, store=store, settings=make_settings(tmp_path), wall=wall, ledger=LedgerDouble()
        )
        with TestClient(app) as client:
            hb = app.state.container.get(deps.HEARTBEAT)
            assert isinstance(hb, Heartbeat)
            exits: list[int] = []
            wd = _watchdog(store, client, exits, wall, _evaluator(store, wall))
            wd.run_once()
            _stop_beat(hb)
            for _ in range(3):
                wall.now += timedelta(seconds=15)
                wd.run_once()
            assert exits == [1]
            hb.beat(time.monotonic())
            wall.now += timedelta(seconds=15)
            _watchdog(store, client, exits, wall, _evaluator(store, wall)).run_once()
            kinds = [r[0] for r in health_rows(store)]
            print(kinds)
            assert kinds[:5] == ["check_ok", "check_failed", "check_failed", "check_failed", "restart"]
            assert ("alert_fired", "health_check_restart") in [(r[0], r[1]) for r in health_rows(store)]
            with store.uow() as tx:
                assert tx.ops.health.restarts_by_day("America/Chicago") == [(date(2026, 10, 21), 1)]
