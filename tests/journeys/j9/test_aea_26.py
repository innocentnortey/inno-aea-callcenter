"""J-9 (proposed extension, slice plan section 0a): a turn while the spend cap is reached.

Level today: mock-tested (real LedgerService on a temp SQLite copy; no server, no TurnService). The integrated steps
(the SPEND_CAP_REACHED notice with the person action; the turn row degraded_handoff / spend_cap; no spend_ledger row
of its own) are blocked by AEA-57 (harness) and AEA-51 (integrated turn, which wires AEA-40's TurnService).
"""

from __future__ import annotations

import datetime as dt
import sqlite3
import uuid
from zoneinfo import ZoneInfo

import pytest

from meridian.domain.turn import TurnIds
from meridian.policy.limits import Limits
from meridian.ports.models import CallRecord
from meridian.services.ledger import LedgerService, SpendGuard
from tests.fixtures.sqlite import temp_sqlite

pytestmark = pytest.mark.journey

CHI = ZoneInfo("America/Chicago")


class FakeWall:
    def __init__(self, now: dt.datetime) -> None:
        self.now = now

    def __call__(self) -> dt.datetime:
        return self.now


def _ids() -> TurnIds:
    return TurnIds.model_validate(
        {
            "thread_id": str(uuid.uuid4()), "turn_id": str(uuid.uuid4()), "request_id": str(uuid.uuid4()),
            "run_tag": "live", "run_id": None, "agent_version": "test-agent-0",
        }
    )  # fmt: skip


def _call(cost: float) -> CallRecord:
    return CallRecord.model_validate(
        {
            "provider": "anthropic", "model": "claude-sonnet-test", "latency_ms": 1200, "input_tokens": 9000,
            "output_tokens": 700, "cache_read_tokens": 0, "cache_write_tokens": 0, "thinking_tokens": 0,
            "cost_usd": cost, "cost_source": "price_table", "status": "ok", "failure": None,
            "provider_request_id": None, "stop_reason": "end_turn", "role": "responder", "attempt": 1,
        }
    )  # fmt: skip


def test_j9_spend_cap_guard_refuses_and_writes_nothing() -> None:
    wall = FakeWall(dt.datetime(2026, 10, 21, 14, 0, tzinfo=CHI))
    with temp_sqlite() as store:
        ledger = LedgerService(store.uow, wall_clock=wall, daily_cap_usd=Limits().spend.daily_cap_usd)
        guard: SpendGuard = ledger
        ledger.record(_call(29.98), _ids())
        assert guard.allow_turn() is True
        ledger.record(_call(0.039), _ids())
        assert guard.allow_turn() is False
        assert ledger.models_disabled() is True

        def count() -> int:
            conn = sqlite3.connect(store.db_path)
            try:
                return int(conn.execute("SELECT COUNT(*) FROM spend_ledger").fetchone()[0])
            finally:
                conn.close()

        before = count()
        refused = _ids()
        assert guard.allow_turn() is False
        assert ledger.models_disabled() is True
        assert count() == before
        with store.uow() as tx:
            assert tx.spend.for_turn(refused.turn_id) == ()

        wall.now = dt.datetime(2026, 10, 22, 0, 0, tzinfo=CHI)
        assert guard.allow_turn() is True
