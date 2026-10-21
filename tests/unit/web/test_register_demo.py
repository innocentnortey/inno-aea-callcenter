"""AEA-30 PA-1 / PA-7: the register_demo hunk wires the demo clock, service and scheduler thread."""

from __future__ import annotations

import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.domain.staff import DemoRole
from meridian.policy.limits import Limits
from meridian.services.demo import DemoService
from meridian.services.scheduler import SchedulerThread
from meridian.web.container import Container, ContainerError, Key, register_demo
from meridian.web.deps import DEMO_SERVICE
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.web_shell_support import make_settings
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.demo_support import ConvertingCases, count, new_request_id, rows


def _wall() -> datetime:
    return datetime(2026, 10, 21, 19, 0, tzinfo=UTC)


class _FakeCheckpointer:
    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.keeps: list[int] = []

    def prune(self, keep: int = 2) -> int:
        self.keeps.append(keep)
        return 3

    def close(self) -> None:
        self.log.append("checkpointer")


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _wired(
    tmp_path: Path, store: TempStore, *, case_service: Any = None, shell: bool = True
) -> tuple[Container, _FakeCheckpointer, list[str]]:
    log: list[str] = []
    fake = _FakeCheckpointer(log)
    c = Container(settings=make_settings(tmp_path), limits=Limits())
    app = FastAPI()
    if shell:
        app.state.web_shell = WebShellState(
            settings=make_settings(tmp_path), wall_clock=_wall, public_paths=PublicPaths()
        )
    c.provide(Key[Any]("uow_factory"), lambda _c: store.uow)

    def checkpointer(cc: Container) -> _FakeCheckpointer:
        cc.on_close(fake.close)  # exactly as AEA-10's factory does
        return fake

    c.provide(Key[Any]("checkpointer"), checkpointer)
    c.provide(Key[Any]("wall_clock"), lambda _c: _wall)
    if case_service is not None:
        c.provide(Key[Any]("case_service"), lambda _c: case_service)
    register_demo(c, app, settings=c.settings, limits=c.limits)
    return c, fake, log


def test_register_demo_wires_and_runs_the_thread(tmp_path: Path, store: TempStore) -> None:
    c, fake, _log = _wired(tmp_path, store, case_service=ConvertingCases())
    c.build()
    assert c.get(Key[Any]("demo_clock")).now() == DEMO_START
    assert isinstance(c.get(DEMO_SERVICE), DemoService)
    thread = c.get(Key[SchedulerThread]("scheduler_thread"))
    assert thread.alive
    deadline = time.monotonic() + 2
    while not fake.keeps and time.monotonic() < deadline:
        time.sleep(0.02)
    assert count(store, "job_runs") >= 1
    assert rows(store, "job_runs")[0]["started_wall_at"] == "2026-10-21T19:00:00+00:00"
    assert fake.keeps == [2]
    c.close()
    assert not thread.alive
    doc = register_demo.__doc__ or ""
    assert "AEA-30" in doc
    assert "No-op until" not in doc


def test_thread_stops_before_storage_closes(
    tmp_path: Path, store: TempStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    c, _fake, log = _wired(tmp_path, store, case_service=ConvertingCases())
    original = SchedulerThread.stop

    def recording_stop(self: SchedulerThread, timeout_s: float = 5.0) -> None:
        log.append("thread")
        original(self, timeout_s)

    monkeypatch.setattr(SchedulerThread, "stop", recording_stop)
    c.build()
    c.close()
    assert log == ["thread", "checkpointer"]


def test_register_demo_ignores_app_without_web_shell(tmp_path: Path, store: TempStore) -> None:
    c, _fake, _log = _wired(tmp_path, store, shell=False)
    c.build()
    with pytest.raises(ContainerError, match="not provided: demo_service"):
        c.get(DEMO_SERVICE)
    c.close()


def test_shift_end_without_case_service_fails_closed(tmp_path: Path, store: TempStore) -> None:
    c, _fake, _log = _wired(tmp_path, store)
    c.build()
    demo = c.get(DEMO_SERVICE)
    demo.set_staffing("simulated_on_shift", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    with pytest.raises(RuntimeError, match="not bound: case_service"):
        demo.set_staffing("nobody_online", request_id=new_request_id(), role=DemoRole.CUSTOMER)
    assert demo.presence() == "simulated_on_shift"
    assert count(store, "demo_events") == 1
    c.close()
