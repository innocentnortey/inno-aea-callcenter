"""AEA-32 PA-7: the register_ops hunk provides its keys, starts the beat task and watchdog thread, and closes them."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import pytest
from fastapi import FastAPI

from meridian.policy.limits import Limits
from meridian.services.health import AlertSettings, AlertWriter, Heartbeat
from meridian.web import deps
from meridian.web.container import Container, ContainerError, Key, register_ops
from meridian.web.middleware import PublicPaths, WebShellState
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.ops_support import BASE, FakeWall, LedgerDouble, make_settings


def _setup(store: TempStore, tmp_path: Path) -> tuple[Container, FastAPI]:
    app = FastAPI()
    settings = make_settings(tmp_path)
    wall = FakeWall(BASE)
    app.state.web_shell = WebShellState(settings=settings, wall_clock=wall, public_paths=PublicPaths())
    c = Container(settings=settings, limits=Limits())
    c.provide(deps.UOW_FACTORY, lambda _c: store.uow)
    c.provide(deps.WALL_CLOCK, lambda _c: wall)
    c.provide(Key[object]("ledger"), lambda _c: LedgerDouble())
    register_ops(c, app, settings=c.settings, limits=c.limits)
    return c, app


def _watchdog_threads() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == "meridian-watchdog" and t.is_alive()]


def test_register_ops_provides_and_starts(tmp_path: Path) -> None:
    with temp_sqlite() as store:
        c, _app = _setup(store, tmp_path)

        async def main() -> None:
            c.build()
            assert isinstance(c.get(deps.HEARTBEAT), Heartbeat)
            assert isinstance(c.get(Key[AlertWriter]("alert_writer")), AlertWriter)
            assert c.get(Key[AlertSettings]("alert_settings")) == AlertSettings()
            assert _watchdog_threads()
            assert any(t.get_name() == "meridian-heartbeat" for t in asyncio.all_tasks())
            await asyncio.sleep(0.05)
            c.close()
            await asyncio.sleep(0)

        asyncio.run(main())
        assert not _watchdog_threads()
        with store.uow() as tx:
            assert tx.connection.execute("SELECT COUNT(*) FROM health_events").fetchone()[0] == 0


def test_register_ops_ignores_app_without_web_shell() -> None:
    c = Container(settings=type("S", (), {"agent_version": "x"})(), limits=Limits())
    register_ops(c, FastAPI(), settings=c.settings, limits=c.limits)
    c.build()
    with pytest.raises(ContainerError):
        c.get(deps.HEARTBEAT)


def test_register_ops_start_needs_running_loop(tmp_path: Path) -> None:
    with temp_sqlite() as store:
        c, _app = _setup(store, tmp_path)
        with pytest.raises(RuntimeError, match="running event loop"):
            c.build()
