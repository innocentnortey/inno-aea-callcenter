"""AC-4 (AEA-53): alerts are shown as stored, never applied; the alert settings come from AlertSettings."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from meridian.adapters.sqlite.repos_ops import ALERT_TYPES, HealthEvent
from meridian.policy.texts import TextId, render
from meridian.services.health import AlertEvaluator, AlertSettings
from meridian.services.metrics_reader import MetricsReader
from meridian.web.schemas.reads import EvalResponse, MonitoringResponse, OwnerMetricsResponse
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.services.test_metrics_reader_rows import WALL_NOW, LedgerDouble, Pages, WallClock


def reader_for(store: TempStore) -> Pages:
    return Pages(
        MetricsReader(
            store.uow, FixedClock(), WallClock(), LedgerDouble(), AlertSettings(), "agent-test", 30.0
        )
    )


def event(kind: str, alert_type: str | None, minutes: int, value: float | None = None) -> HealthEvent:
    return HealthEvent.model_validate(
        {
            "at_wall": WALL_NOW - timedelta(minutes=minutes),
            "kind": kind,
            "alert_type": alert_type,
            "reason_code": None,
            "value": value,
            "threshold": 12.5 if alert_type == "p95_latency_over_12_5s" else None,
            "agent_version": "test",
        }
    )


def test_alert_states_equal_stored_rows() -> None:
    with temp_sqlite() as store:
        with store.uow(write=True) as tx:
            tx.ops.health.append(
                event("alert_fired", "p95_latency_over_12_5s", 30, 3.0)
            )  # under its threshold
            tx.ops.health.append(event("alert_fired", "spend_cap_reached", 20, 31.0))
            tx.ops.health.append(event("alert_cleared", "spend_cap_reached", 10))
            tx.ops.health.append(event("alert_fired", "scheduler_stale", 5, 200.0))
            tx.commit()
        page = reader_for(store).monitoring()
        MonitoringResponse.model_validate(page)
        with store.uow() as tx:
            stored = tx.ops.health.latest_alert_states()
    alerts = page["alerts"]
    assert [a["type"] for a in alerts] == [t for t in ALERT_TYPES if t != "scheduler_stale"]
    assert len(alerts) == 6
    for a in alerts:
        assert a["state"] == stored[a["type"]].state
    by_type = {a["type"]: a for a in alerts}
    print({t: a["state"] for t, a in by_type.items()})
    assert by_type["p95_latency_over_12_5s"]["state"] == "firing"
    assert by_type["p95_latency_over_12_5s"]["fired_at"] is not None
    assert by_type["spend_cap_reached"]["state"] == "quiet"
    assert by_type["spend_cap_reached"]["fired_at"] is None
    assert "scheduler_stale" not in by_type
    assert any(t["id"] == "scheduler_last_run" for t in page["health"])


def test_alert_config_and_decision_lines() -> None:
    with temp_sqlite() as store:
        page = reader_for(store).monitoring()
    assert page["alert_config"] == {
        "zero_traffic_after_hours": 4,
        "quiet_hours": {
            "start": "22:00",
            "end": "06:00",
            "timezone": "America/Chicago",
            "configurable": True,
        },
    }
    lines = {a["type"]: a["decision_line"] for a in page["alerts"]}
    assert lines["spend_cap_reached"] == render(TextId.MONITOR_SPEND_CAP, amount="$30")
    assert not any("80%" in line for line in lines.values())
    assert "12.5 s" in lines["p95_latency_over_12_5s"]
    assert "2%" in lines["failure_rate_over_2pct"]


def test_pages_answer_with_evaluator_patched(monkeypatch: pytest.MonkeyPatch) -> None:
    def raiser(*_a: Any, **_k: Any) -> None:
        raise AssertionError("the reader must never apply an alert line")

    monkeypatch.setattr(AlertEvaluator, "evaluate", raiser)
    with temp_sqlite() as store:
        reader = reader_for(store)
        OwnerMetricsResponse.model_validate(reader.owner_metrics())
        MonitoringResponse.model_validate(reader.monitoring())
        EvalResponse.model_validate(reader.latest_eval())
