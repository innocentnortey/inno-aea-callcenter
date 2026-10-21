"""AEA-32 unit tests: heartbeat, beats, watchdog, quiet hours, restart-day alert."""

from __future__ import annotations

import ast
import asyncio
import contextlib
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, cast

import pytest

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.repos_ops import HealthEvent
from meridian.services import health
from meridian.services.health import (
    AlertEvaluator,
    AlertSettings,
    Heartbeat,
    Watchdog,
    run_beats,
    time_outside_quiet_hours,
)
from tests.fixtures.sqlite import temp_sqlite
from tests.services.ops_support import (
    BASE,
    EvaluatorDouble,
    FakeWall,
    LedgerDouble,
    ProbeDouble,
    chi,
    health_rows,
    make_evaluator,
)


def test_heartbeat_fresh_and_stale() -> None:
    hb = Heartbeat(AlertSettings())
    assert hb.fresh(100.0) is False
    hb.beat(100.0)
    assert hb.fresh(130.0) is True
    assert hb.fresh(130.001) is False
    assert Heartbeat(AlertSettings(), started_mono=50.0).fresh(60.0) is True

    tree = ast.parse(Path(health.__file__).read_text(encoding="utf-8"))
    banned = {"sqlite3", "uow", "tx", "UnitOfWork", "UnitOfWorkFactory"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef | ast.AsyncFunctionDef) and node.name in ("Heartbeat", "run_beats"):
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            attrs = {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
            assert not (names | attrs) & banned, node.name


def test_beat_goes_through_pool() -> None:
    async def main() -> None:
        never = asyncio.Event()
        seen: list[Callable[[], None]] = []
        slept: list[float] = []

        async def run_sync(fn: Callable[[], None]) -> None:
            seen.append(fn)
            fn()

        async def sleep(s: float) -> None:
            slept.append(s)
            await never.wait()

        hb = Heartbeat(AlertSettings())
        task = asyncio.create_task(
            run_beats(hb, AlertSettings(), run_sync=run_sync, sleep=sleep, monotonic=lambda: 100.0)
        )
        for _ in range(5):
            await asyncio.sleep(0)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert hb.fresh(100.0) is True
        assert seen == [health._pool_noop]

        async def stuck(fn: Callable[[], None]) -> None:
            await never.wait()

        slept2: list[float] = []

        async def sleep2(s: float) -> None:
            slept2.append(s)

        hb2 = Heartbeat(AlertSettings())
        task2 = asyncio.create_task(
            run_beats(hb2, AlertSettings(), run_sync=stuck, sleep=sleep2, monotonic=lambda: 100.0)
        )
        for _ in range(5):
            await asyncio.sleep(0)
        task2.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task2
        assert hb2.fresh(100.0) is False
        assert slept2 == []

    asyncio.run(main())


def _watchdog(store: Any, probe: Any, exits: list[int], wall: FakeWall, evaluator: Any = None) -> Watchdog:
    return Watchdog(
        store.uow,
        probe,
        exits.append,
        cast(AlertEvaluator, evaluator or EvaluatorDouble()),
        AlertSettings(),
        wall,
        agent_version="test-ops",
    )


def test_watchdog_exits_after_three_failures() -> None:
    with temp_sqlite() as store:
        exits: list[int] = []
        wd = _watchdog(store, ProbeDouble([True, False, False, False]), exits, FakeWall(BASE))
        for _ in range(4):
            wd.run_once()
        rows = health_rows(store)
        print(rows)
        assert [r[0] for r in rows] == ["check_ok", "check_failed", "check_failed", "check_failed", "restart"]
        assert exits == [1]
        assert rows[-1][2] == "healthz_failed_3_in_a_row"
        with store.uow() as tx:
            last = tx.ops.health.last_restart()
        assert last is not None and last.at_wall == BASE


def test_success_resets_count() -> None:
    with temp_sqlite() as store:
        exits: list[int] = []
        wd = _watchdog(store, ProbeDouble([False, False, True, False]), exits, FakeWall(BASE))
        for _ in range(4):
            wd.run_once()
        assert exits == []
        kinds = [r[0] for r in health_rows(store)]
        assert kinds == ["check_failed", "check_failed", "check_ok", "check_failed"]


def test_probe_exception_counts_as_failure_without_text() -> None:
    with temp_sqlite() as store:
        wd = _watchdog(store, ProbeDouble([RuntimeError("secret text")]), [], FakeWall(BASE))
        wd.run_once()
        assert health_rows(store) == [("check_failed", None, "healthz_error")]


def test_restart_alert_clears_next_chicago_day() -> None:
    with temp_sqlite() as store:
        wall = FakeWall(chi(2026, 10, 21, 14, 1))

        def add_restart(at: datetime) -> None:
            with store.uow(write=True) as tx:
                tx.ops.health.append(
                    HealthEvent(
                        at_wall=at,
                        kind="restart",
                        alert_type=None,
                        reason_code="r",
                        value=3.0,
                        threshold=3.0,
                        agent_version="t",
                    )
                )
                tx.commit()

        add_restart(chi(2026, 10, 21, 14, 0))
        ev = make_evaluator(store, wall, LedgerDouble(0.0))

        def count(kind: str) -> int:
            return len([r for r in health_rows(store, kind) if r[1] == "health_check_restart"])

        ev.evaluate()
        assert count("alert_fired") == 1
        wall.now = chi(2026, 10, 21, 23, 59)
        ev.evaluate()
        assert count("alert_fired") == 1 and count("alert_cleared") == 0
        add_restart(chi(2026, 10, 21, 23, 58))
        ev.evaluate()
        assert count("alert_fired") == 1
        wall.now = chi(2026, 10, 22, 0, 5)
        ev.evaluate()
        assert count("alert_cleared") == 1 and count("alert_fired") == 1


def test_time_outside_quiet_hours() -> None:
    s = AlertSettings()
    h = timedelta(hours=1)
    assert time_outside_quiet_hours(chi(2026, 10, 21, 21), chi(2026, 10, 22, 7), s) == 2 * h
    assert time_outside_quiet_hours(chi(2026, 10, 21, 14), chi(2026, 10, 21, 19), s) == 5 * h
    assert time_outside_quiet_hours(chi(2026, 10, 31, 20), chi(2026, 11, 1, 8), s) == 4 * h
    off = AlertSettings(quiet_start=time(6), quiet_end=time(6))
    assert time_outside_quiet_hours(chi(2026, 10, 21, 21), chi(2026, 10, 22, 7), off) == 10 * h
    with pytest.raises(ValueError):
        time_outside_quiet_hours(datetime(2026, 10, 21, 1), chi(2026, 10, 22, 7), s)


def test_watchdog_evaluates_on_schedule() -> None:
    with temp_sqlite() as store:
        ev = EvaluatorDouble()
        wall = FakeWall(BASE)
        wd = _watchdog(store, ProbeDouble([True] * 4), [], wall, ev)
        for delta in (0, 15, 59, 60):
            wall.now = chi(2026, 10, 21, 14, 0) + timedelta(seconds=delta)
            wd.run_once()
        assert ev.calls == 2


def test_watchdog_exits_even_if_restart_write_fails() -> None:
    with temp_sqlite() as store:
        writes = {"n": 0}
        real = store.uow

        def flaky(*, write: bool = False, exclusive: bool = False) -> AbstractContextManager[Any]:
            if write:
                writes["n"] += 1
                if writes["n"] == 4:
                    raise StorageError("health_events", "CHECK")
            return real(write=write, exclusive=exclusive)

        exits: list[int] = []
        wd = Watchdog(
            cast(Any, flaky),
            ProbeDouble([False, False, False]),
            exits.append,
            cast(AlertEvaluator, EvaluatorDouble()),
            AlertSettings(),
            FakeWall(BASE),
            agent_version="test-ops",
        )
        wd.run_once()
        wd.run_once()
        with pytest.raises(StorageError):
            wd.run_once()
        assert exits == [1]
