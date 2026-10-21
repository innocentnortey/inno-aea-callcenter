"""AEA-26 PA-1: the register_spend hunk provides the one LedgerService from limits and the wall-clock key."""

from __future__ import annotations

import datetime as dt
import sqlite3
import types
import uuid
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI

from meridian.domain.turn import TurnIds
from meridian.policy.limits import Limits, SpendLimits
from meridian.ports.models import CallRecord
from meridian.services.ledger import LedgerService, SpendGuard
from meridian.web.container import Container, Key, register_spend
from tests.fixtures.sqlite import temp_sqlite


class FakeWall:
    def __init__(self, now: dt.datetime) -> None:
        self.now = now

    def __call__(self) -> dt.datetime:
        return self.now


def test_register_spend_provides_one_ledger_from_limits_and_wall_clock() -> None:
    with temp_sqlite() as store:
        fake = FakeWall(dt.datetime(2026, 10, 21, 14, 0, tzinfo=ZoneInfo("America/Chicago")))
        limits = Limits(spend=SpendLimits(daily_cap_usd=0.5))
        c = Container(settings=types.SimpleNamespace(name="stand-in"), limits=limits)
        try:
            c.provide(Key[Any]("uow_factory"), lambda _c: store.uow)
            c.provide(Key[Any]("wall_clock"), lambda _c: fake)
            register_spend(c, FastAPI(), settings=c.settings, limits=limits)
            c.build()

            ledger = c.get(Key[LedgerService]("ledger"))
            assert ledger is c.get(Key[LedgerService]("ledger"))
            assert isinstance(ledger, LedgerService)
            assert isinstance(ledger, SpendGuard)

            assert ledger.allow_turn() is True
            call = CallRecord.model_validate(
                {
                    "provider": "anthropic", "model": "claude-sonnet-test", "latency_ms": 10,
                    "input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0, "cache_write_tokens": 0,
                    "thinking_tokens": 0, "cost_usd": 0.5, "cost_source": "price_table", "status": "ok",
                    "failure": None, "provider_request_id": None, "stop_reason": "end_turn",
                    "role": "responder", "attempt": 1,
                }
            )  # fmt: skip
            ids = TurnIds.model_validate(
                {
                    "thread_id": str(uuid.uuid4()), "turn_id": str(uuid.uuid4()),
                    "request_id": str(uuid.uuid4()), "run_tag": "live", "run_id": None,
                    "agent_version": "test-agent-0",
                }
            )  # fmt: skip
            ledger.record(call, ids)
            assert ledger.allow_turn() is False  # the cap came from limits, not the default

            conn = sqlite3.connect(store.db_path)
            try:
                stamp = conn.execute("SELECT recorded_at FROM spend_ledger").fetchone()
            finally:
                conn.close()
            assert stamp == ("2026-10-21T19:00:00+00:00",)  # the wall clock came from the "wall_clock" key

            doc = register_spend.__doc__ or ""
            assert "AEA-26" in doc and "No-op until" not in doc
        finally:
            c.close()
