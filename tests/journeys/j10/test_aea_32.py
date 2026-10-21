"""J-10 (proposed extension, slice plan section 0a): the monitoring read's alert states equal the stored
health_event rows, and the scheduler_last_run tile's source is the newest job_runs row. Level today: mock-tested (real
AlertEvaluator and repositories on a temp SQLite copy; no server, no MetricsReader). The integrated steps (CON-19 through
the real app with a scripted model) are blocked by AEA-57 (harness) and AEA-53 (metrics reader)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.repos_ops import ALERT_TYPES, HealthEvent
from meridian.policy.limits import Limits
from meridian.services.health import AlertEvaluator, AlertSettings
from tests.fixtures.sqlite import temp_sqlite
from tests.services.ops_support import BASE, FakeWall, LedgerDouble

pytestmark = pytest.mark.journey


def test_j10_alert_states_match_stored_events() -> None:
    with temp_sqlite() as store:
        wall = FakeWall(BASE)
        with store.uow(write=True) as tx:
            tx.cases.job_runs.start(
                "job-older", started_wall_at=wall() - timedelta(minutes=10), demo_now=DEMO_START
            )
            tx.cases.job_runs.start(
                "job-newest", started_wall_at=wall() - timedelta(minutes=5), demo_now=DEMO_START
            )
            tx.ops.health.append(
                HealthEvent.model_validate(
                    {
                        "at_wall": BASE - timedelta(hours=1),
                        "kind": "restart",
                        "alert_type": None,
                        "reason_code": "r",
                        "value": 3.0,
                        "threshold": 3.0,
                        "agent_version": "j10",
                    }
                )
            )
            tx.commit()
        returned = AlertEvaluator(
            store.uow,
            LedgerDouble(31.0),
            AlertSettings(),
            wall,
            Limits().spend.daily_cap_usd,
            agent_version="j10",
        ).evaluate()
        with store.uow() as tx:
            stored = tx.ops.health.latest_alert_states()
            newest = dict(
                tx.connection.execute(
                    "SELECT h.alert_type, h.kind FROM health_events h JOIN (SELECT alert_type, MAX(id) AS id "
                    "FROM health_events WHERE kind IN ('alert_fired','alert_cleared') GROUP BY alert_type) m "
                    "ON h.id = m.id"
                ).fetchall()
            )
            job = tx.cases.job_runs.latest()
        assert tuple(s.type for s in returned) == ALERT_TYPES
        for s in returned:
            assert s.state == stored[s.type].state
            assert (s.state == "firing") == (newest.get(s.type) == "alert_fired")
        firing = {s.type for s in returned if s.state == "firing"}
        assert {"spend_cap_reached", "health_check_restart", "scheduler_stale"} <= firing
        assert job is not None and job.job_run_id == "job-newest"
