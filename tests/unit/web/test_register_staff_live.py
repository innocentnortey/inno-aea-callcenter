"""AEA-46 PA-1: the register_staff_live hunk binds LiveChatService, forwards the lazy demo clock, includes routes once."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from meridian.policy.limits import Limits
from meridian.services.live_chat import LiveChatService, LiveView
from meridian.web.container import Container, ContainerError, Key, register_staff_live
from meridian.web.deps import LIVE_CHAT
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.web_shell_support import effective_routes, make_settings
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.live_chat_support import (
    JOIN_AT,
    RILEY,
    WP2_REF,
    card_like_and_code,
    seed_live_case,
    snapshot,
)


def _wall() -> datetime:
    return datetime(2026, 10, 21, tzinfo=UTC)


def _app(tmp_path: Path) -> FastAPI:
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=make_settings(tmp_path), wall_clock=_wall, public_paths=PublicPaths()
    )
    return app


def _container(tmp_path: Path, db: TempStore, *, clock: bool = True) -> tuple[Container, FastAPI]:
    c = Container(settings=make_settings(tmp_path), limits=Limits())
    c.provide(Key[Any]("uow_factory"), lambda _c: db.uow)
    if clock:
        c.provide(Key[Any]("demo_clock"), lambda _c: FixedClock(JOIN_AT))
    app = _app(tmp_path)
    register_staff_live(c, app, settings=c.settings, limits=c.limits)
    c.build()
    return c, app


def _live_routes(app: FastAPI) -> set[tuple[str, str | None]]:
    return {
        (r.path, r.operation_id)
        for r in effective_routes(app)
        if r.operation_id in {"liveChatAction", "streamCaseEvents"}
    }


def test_register_staff_live_binds_service_and_router(tmp_path: Path) -> None:
    with temp_sqlite() as db:
        c, app = _container(tmp_path, db)
        service = c.get(LIVE_CHAT)
        assert isinstance(service, LiveChatService)
        assert service is c.get(LIVE_CHAT)
        expected = {
            ("/api/staff/cases/{reference}/live", "liveChatAction"),
            ("/api/staff/cases/{reference}/events", "streamCaseEvents"),
        }
        assert _live_routes(app) == expected
        c2 = Container(settings=c.settings, limits=c.limits)
        c2.provide(Key[Any]("uow_factory"), lambda _c: db.uow)
        register_staff_live(c2, app, settings=c2.settings, limits=c2.limits)
        c2.build()
        assert len([r for r in effective_routes(app) if r.operation_id == "liveChatAction"]) == 1


def test_redactor_binding_is_store(tmp_path: Path) -> None:
    """MC-23 at the hunk: staff text is STORE-redacted before it is stored."""
    card, _ = card_like_and_code()
    with temp_sqlite() as db:
        c, _ = _container(tmp_path, db)
        seed_live_case(db.uow)
        service = c.get(LIVE_CHAT)
        service.join(WP2_REF, RILEY)
        view = service.send(WP2_REF, f"card {card} ok", RILEY)
        assert isinstance(view, LiveView) and view.message is not None
        assert "[card number removed]" in view.message.text and card not in view.message.text


def test_demo_clock_unbound_raises_not_bound(tmp_path: Path) -> None:
    with temp_sqlite() as db:
        c, _ = _container(tmp_path, db, clock=False)  # build() succeeds without the clock
        seeded = seed_live_case(db.uow)
        before = snapshot(db.uow, seeded)
        with pytest.raises(RuntimeError, match="not bound: demo_clock"):
            c.get(LIVE_CHAT).join(WP2_REF, RILEY)
        assert snapshot(db.uow, seeded) == before


def test_bare_app_gets_nothing(tmp_path: Path) -> None:
    with temp_sqlite() as db:
        c = Container(settings=make_settings(tmp_path), limits=Limits())
        c.provide(Key[Any]("uow_factory"), lambda _c: db.uow)
        app = FastAPI()
        register_staff_live(c, app, settings=c.settings, limits=c.limits)
        c.build()
        with pytest.raises(ContainerError, match="not provided: live_chat"):
            c.get(LIVE_CHAT)
        assert _live_routes(app) == set()
