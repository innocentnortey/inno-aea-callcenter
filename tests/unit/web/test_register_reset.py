"""AEA-31 PA-4: the register_reset hunk binds the reset service and seeds the first boot once."""

from __future__ import annotations

import functools
import sys
import types
from typing import Any, cast

import pytest
from fastapi import FastAPI

from meridian.adapters.sqlite.migrate import restore_working_copy
from meridian.policy.limits import Limits
from meridian.services.reset import ResetDone, ResetService
from meridian.services.reset_gate import ResetGate
from meridian.web.container import Container, Key, register_reset
from meridian.web.deps import RESET_GATE, RESET_SERVICE, UOW_FACTORY, WALL_CLOCK
from meridian.web.middleware import PublicPaths, WebShellState
from tests.services.reset_support import (
    WALL,
    RecordingAssembler,
    count,
    demo_store,
    fake_format_clock,
    new_request_id,
    rows,
)


def _wire(store: Any, cp: Any, settings: Any) -> Container:
    c = Container(settings=settings, limits=Limits())
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=settings, wall_clock=lambda: WALL, public_paths=PublicPaths()
    )
    c.provide(UOW_FACTORY, lambda _c: store.uow)
    c.provide(Key[Any]("checkpointer"), lambda _c: cp)
    c.provide(
        Key[Any]("restore_working_copy"),
        lambda _c: functools.partial(restore_working_copy, issued_path=store.issued_path),
    )
    c.provide(RESET_GATE, lambda _c: ResetGate())
    c.provide(WALL_CLOCK, lambda _c: lambda: WALL)
    register_reset(c, app, settings=settings, limits=c.limits)
    c.build()
    return c


def test_register_reset_binds_service_and_seeds_first_boot(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_handoff = types.ModuleType("meridian.services.handoff")
    monkeypatch.setattr(fake_handoff, "BriefAssembler", RecordingAssembler, raising=False)
    fake_demo = types.ModuleType("meridian.services.demo")
    monkeypatch.setattr(fake_demo, "format_clock", fake_format_clock, raising=False)
    monkeypatch.setitem(sys.modules, "meridian.services.handoff", fake_handoff)
    monkeypatch.setitem(sys.modules, "meridian.services.demo", fake_demo)
    settings = cast(Any, types.SimpleNamespace())
    with demo_store() as (store, cp):
        first = _wire(store, cp, settings)
        assert isinstance(first.get(RESET_SERVICE), ResetService)
        assert count(store.db_path, "cases") == 4
        assert rows(store.db_path, "SELECT reset_id FROM seed_events") == [(None,)]
        result = first.get(RESET_SERVICE).reset(WALL, request_id=new_request_id(), session_id=None, role=None)
        assert isinstance(result, ResetDone)
        second = _wire(store, cp, settings)
        assert (
            count(store.db_path, "seed_events") == 2
        )  # first boot + the reset's own; no second first-boot seed
        assert rows(store.db_path, "SELECT COUNT(*) FROM seed_events WHERE reset_id IS NULL") == [(1,)]
        second.close()
        first.close()
    doc = register_reset.__doc__ or ""
    assert "AEA-31" in doc
    assert "No-op until" not in doc


def test_register_reset_skips_bare_app() -> None:
    settings = cast(Any, types.SimpleNamespace())
    c = Container(settings=settings, limits=Limits())
    register_reset(c, FastAPI(), settings=settings, limits=c.limits)
    c.build()
    assert c._factories == {}
    assert c._starters == []
