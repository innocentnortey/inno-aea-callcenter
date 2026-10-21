"""AEA-40 PA-1: the register_chat hunk provides the two services, the three routes and the start-up sweep.

Failure modes: invariant (an app create_app did not build gets nothing; the app builds before AEA-30 / AEA-51 bind
their keys; an unbound sibling fails only when it is called, with the key's name).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from meridian.policy.limits import Limits
from meridian.services.turn import TurnService
from meridian.web.container import Container, ContainerError, Key, register_chat, register_web
from meridian.web.deps import DEMO_SERVICE, SESSION_SERVICE, TURN_SERVICE
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.web_shell_support import effective_routes, make_settings
from tests.fakes import FixedClock, InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.chat_doubles import (
    WALL_NOW,
    FakeComposer,
    FakeSpendGuard,
    ScriptedRunGraph,
    make_cmd,
    new_request_id,
    text_payload,
)
from tests.services.chat_storage import seed_thread, turn_row


def _provider(value: Any) -> Callable[[Container], Any]:
    return lambda _c: value


def _container(store: TempStore, tmp_path: Path, bound: set[str]) -> tuple[Container, FastAPI]:
    settings = make_settings(tmp_path)
    limits = Limits()
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=settings, wall_clock=lambda: WALL_NOW, public_paths=PublicPaths()
    )
    container = Container(settings=settings, limits=limits)
    container.provide(Key[Any]("uow_factory"), lambda _c: store.uow)
    container.provide(Key[Any]("ledger"), lambda _c: FakeSpendGuard(True))
    container.provide(Key[Any]("trace"), lambda _c: InMemoryTraceSink())
    siblings: dict[str, Any] = {
        "demo_clock": FixedClock(),
        "run_graph": ScriptedRunGraph(),
        "reply_composer": FakeComposer(),
    }
    for name in bound:
        container.provide(Key[Any](name), _provider(siblings[name]))
    register_web(container, app, settings=settings, limits=limits)
    register_chat(container, app, settings=settings, limits=limits)
    return container, app


def test_bare_app_gets_nothing(tmp_path: Path) -> None:
    """invariant (PA-1): an app create_app did not build (no web shell) gets no service, no route and no sweep."""
    settings = make_settings(tmp_path)
    limits = Limits()
    app = FastAPI()
    container = Container(settings=settings, limits=limits)

    register_chat(container, app, settings=settings, limits=limits)
    container.build()

    for key in (SESSION_SERVICE, TURN_SERVICE):
        with pytest.raises(ContainerError, match="not provided"):
            container.get(key)
    assert [r for r in effective_routes(app) if r.path.startswith("/api/chat")] == []
    doc = register_chat.__doc__ or ""
    assert "AEA-40" in doc and "No-op until" not in doc
    container.close()


def test_wires_services_routes_and_lazy_siblings(tmp_path: Path) -> None:
    """invariant (PA-1): services and routes exist; siblings AEA-30 / AEA-51 bind later; unbound ones fail when called."""
    with temp_sqlite() as store:
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("hello"))

        # nothing from AEA-30 or AEA-51 is bound: the app still builds, and the surface is complete
        container, app = _container(store, tmp_path / "a", bound=set())
        try:
            container.build()
            turns = container.get(TURN_SERVICE)
            assert isinstance(turns, TurnService)
            assert container.get(SESSION_SERVICE) is container.get(SESSION_SERVICE)
            operations = {
                (r.operation_id, tuple(sorted(r.methods)), r.path)
                for r in effective_routes(app)
                if r.path.startswith("/api/chat")
            }
            assert operations == {
                ("startChatSession", ("POST",), "/api/chat/sessions"),
                ("getChatThread", ("GET",), "/api/chat/sessions/{thread_id}"),
                ("submitTurn", ("POST",), "/api/chat/sessions/{thread_id}/turns"),
            }
            with pytest.raises(
                RuntimeError, match="not bound: demo_clock"
            ):  # only when called, with the key's name
                turns.run_turn(cmd)
        finally:
            container.close()

        # the clock is bound but DemoService is not: opening a chat names the missing key
        container_d, _ = _container(store, tmp_path / "d", bound={"demo_clock"})
        try:
            container_d.build()
            with pytest.raises(RuntimeError, match="not bound: demo_service"):
                container_d.get(SESSION_SERVICE).open(
                    _login(), run_tag="live", run_id=None, request_id=new_request_id()
                )
        finally:
            container_d.close()

        # the clock is bound but the graph is not: the turn degrades to a person offer, it does not take the app down
        container2, _ = _container(store, tmp_path / "b", bound={"demo_clock", "reply_composer"})
        try:
            container2.build()
            result = container2.get(TURN_SERVICE).run_turn(cmd)
            assert any(getattr(b, "person_key", False) for b in result.blocks)
            assert turn_row(store, cmd.turn_id).status == "failed"
        finally:
            container2.close()

        # everything bound: the turn runs through the forwarders
        container3, _ = _container(store, tmp_path / "c", bound={"demo_clock", "run_graph", "reply_composer"})
        try:
            container3.build()
            ok = container3.get(TURN_SERVICE).run_turn(make_cmd(thread, text_payload("hello again")))
            assert ok.notice is None
        finally:
            container3.close()
    assert DEMO_SERVICE.name == "demo_service"


def _login() -> Any:
    from tests.api.web_shell_support import FakeSessionStore

    sessions = FakeSessionStore()
    return sessions.session_of(sessions.issue())
