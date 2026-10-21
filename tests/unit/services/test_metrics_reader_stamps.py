"""AC-8 (AEA-53): time and spend stamps come from the injected clocks and the ledger."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from meridian.adapters.sqlite.db import format_wall
from meridian.services.health import AlertSettings
from meridian.services.ledger import LedgerService
from meridian.services.metrics_reader import MetricsLedger, MetricsReader
from meridian.web.schemas.reads import MonitoringResponse, OwnerMetricsResponse
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.adapters.sqlite.helpers import new_turn, turn_ids
from tests.unit.services.test_metrics_reader_rows import (
    CHI,
    DEMO_NOW,
    WALL_NOW,
    LedgerDouble,
    Pages,
    WallClock,
    add_conversation,
    add_turn,
    call_record,
)


def reader_for(
    store: TempStore, ledger: MetricsLedger, wall: WallClock | None = None, demo: FixedClock | None = None
) -> Pages:
    return Pages(
        MetricsReader(
            store.uow,
            demo or FixedClock(),
            wall or WallClock(),
            ledger,
            AlertSettings(),
            "agent-test",
            30.0,
        )
    )


def test_time_stamps_from_injected_clocks() -> None:
    demo = FixedClock().advanced(timedelta(hours=3))
    with temp_sqlite() as store:
        reader = reader_for(store, LedgerDouble(), demo=demo)
        monitoring = reader.monitoring()
        owner = reader.owner_metrics()
    MonitoringResponse.model_validate(monitoring)
    OwnerMetricsResponse.model_validate(owner)
    assert monitoring["as_of"] == WALL_NOW
    assert monitoring["demo_now"] == demo.now() == DEMO_NOW + timedelta(hours=3)
    assert owner["as_of"] == demo.now()
    for stamp in (monitoring["as_of"], monitoring["demo_now"], owner["as_of"]):
        assert stamp.utcoffset() is not None


def test_spend_cents_and_reset_time() -> None:
    with temp_sqlite() as store:
        page = reader_for(store, LedgerDouble(spent=6.12)).monitoring()
        assert page["spend"]["today_cents"] == 612
        assert page["spend"]["cap_cents"] == 3000
        assert page["spend"]["resets_at"] == datetime(2026, 10, 22, 0, 0, tzinfo=CHI)
        dst = reader_for(
            store, LedgerDouble(), wall=WallClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))
        ).monitoring()
        assert dst["spend"]["resets_at"] == datetime(2026, 11, 2, 0, 0, tzinfo=CHI)


def test_handoff_only_from_open_circuit_or_cap() -> None:
    def tile(ledger: LedgerDouble) -> object:
        with temp_sqlite() as store:
            health = reader_for(store, ledger).monitoring()["health"]
        return next(t for t in health if t["id"] == "handoff_only")["value"]

    assert tile(LedgerDouble(circuits=("anthropic",))) == 1
    assert tile(LedgerDouble(capped=True)) == 1
    assert tile(LedgerDouble()) == 0


def test_real_ledger_spend_today() -> None:
    with temp_sqlite() as store:
        wall = WallClock(datetime(2026, 10, 21, 4, 30, tzinfo=UTC))  # Chicago yesterday 23:30
        ledger = LedgerService(store.uow, wall_clock=wall, daily_cap_usd=30.0)
        thread = add_conversation(store.uow)
        ids = add_turn(store.uow, thread)
        ledger.record(call_record(1.0), ids)
        wall.now = WALL_NOW
        ledger.record(call_record(0.0123), ids)
        ledger.record(call_record(0.0456), turn_ids(thread, new_turn()))
        page = reader_for(store, ledger, wall=wall).monitoring()
        start = datetime(2026, 10, 21, 0, 0, tzinfo=CHI).astimezone(UTC)
        end = start + timedelta(days=1)
        with store.uow() as tx:
            total = tx.connection.execute(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger WHERE recorded_at >= ? AND recorded_at < ?",
                (format_wall(start), format_wall(end)),
            ).fetchone()[0]
    assert page["spend"]["today_cents"] == round(100 * total) == 6  # yesterday's $1.00 is not counted
