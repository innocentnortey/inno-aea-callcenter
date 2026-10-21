"""AEA-19-F1: register_tracing returns Key("trace_override") as Key("trace") when it is provided (AEA-51 §8 R-1)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from meridian.config import Settings
from meridian.policy.limits import Limits
from meridian.ports.runtime import TraceSink
from meridian.services.person_request import PersonRequestService
from meridian.services.turn import TurnService
from meridian.web.container import (
    Container,
    ContainerError,
    Key,
    register_chat,
    register_person_request,
    register_tracing,
    register_web,
)
from meridian.web.deps import PERSON_REQUESTS, TURN_SERVICE
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.web_shell_support import make_settings
from tests.fakes import FixedClock, InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.chat_doubles import (
    WALL_NOW,
    FakeComposer,
    FakeSpendGuard,
    ScriptedRunGraph,
    make_cmd,
    text_payload,
)
from tests.services.chat_storage import seed_thread
from tests.unit.adapters._tracing_doubles import BASE_URL, PROJECT_ID, new_keys, tracing_module

TRACE = Key[TraceSink]("trace")
OVERRIDE = Key[TraceSink]("trace_override")


@pytest.fixture
def containers() -> Iterator[list[Container]]:
    opened: list[Container] = []
    yield opened
    for c in opened:
        c.close()


def langfuse_settings(tmp_path: Path) -> tuple[Settings, str, str]:
    pk, sk = new_keys()
    settings = make_settings(
        tmp_path,
        langfuse_public_key=pk,
        langfuse_secret_key=sk,
        langfuse_base_url=BASE_URL,
        langfuse_project_id=PROJECT_ID,
    )
    return settings, pk, sk


def tracing_only(opened: list[Container], settings: Settings, override: TraceSink | None) -> Container:
    """register_tracing first, then the override (as register_graph does, later), then build."""
    c = Container(settings=settings, limits=Limits())
    opened.append(c)
    register_tracing(c, FastAPI(), settings=settings, limits=c.limits)
    if override is not None:
        c.provide(OVERRIDE, lambda _c: override)
    c.build()
    return c


def wired_services(
    opened: list[Container], store: TempStore, tmp_path: Path, override: InMemoryTraceSink | None
) -> Container:
    """The real tracing, chat and person-request hunks on one container; siblings are doubles."""
    settings = make_settings(tmp_path)  # no LANGFUSE_* -> the settings choice is NullTraceSink
    limits = Limits()
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=settings, wall_clock=lambda: WALL_NOW, public_paths=PublicPaths()
    )
    c = Container(settings=settings, limits=limits)
    opened.append(c)
    for name, obj in (
        ("uow_factory", store.uow),
        ("ledger", FakeSpendGuard(True)),
        ("demo_clock", FixedClock()),
        ("run_graph", ScriptedRunGraph()),
        ("reply_composer", FakeComposer()),
        ("handoff_service", object()),
    ):
        c.provide(Key[Any](name), lambda _c, o=obj: o)  # type: ignore[misc]
    register_web(c, app, settings=settings, limits=limits)
    register_tracing(c, app, settings=settings, limits=limits)
    register_chat(c, app, settings=settings, limits=limits)
    register_person_request(c, app, settings=settings, limits=limits)
    if override is not None:
        c.provide(OVERRIDE, lambda _c: override)  # last, as register_graph runs after both consumers
    c.build()
    return c


def test_override_replaces_null_sink(tmp_path: Path, containers: list[Container]) -> None:
    """invariant (F1-1): no LANGFUSE_* and an override bound: Key("trace") is the override."""
    sink = InMemoryTraceSink()
    c = tracing_only(containers, make_settings(tmp_path), sink)
    assert c.get(TRACE) is sink


def test_override_wins_over_langfuse_and_langfuse_is_not_started(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    containers: list[Container],
) -> None:
    """invariant (F1-2, F1-9): all four LANGFUSE_* and an override: the override is used, Langfuse is never started, keys never logged."""
    tl = tracing_module()
    started: list[object] = []
    monkeypatch.setattr(tl.LangfuseTraceSink, "start", lambda self: started.append(self))
    caplog.set_level(logging.DEBUG)
    settings, pk, sk = langfuse_settings(tmp_path)
    sink = InMemoryTraceSink()
    c = tracing_only(containers, settings, sink)
    assert c.get(TRACE) is sink
    assert started == []
    c.close()
    assert pk not in caplog.text and sk not in caplog.text


def test_override_replaces_build_failure_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    containers: list[Container],
) -> None:
    """boundary (F1-3): the Langfuse sink cannot be built and an override is bound: the override is used; the build-failure line is still logged."""
    tl = tracing_module()

    class BrokenSink:
        def __init__(self, settings: Any, redact: Any, on_alert: Any) -> None:
            raise RuntimeError("cannot build")

    monkeypatch.setattr(tl, "LangfuseTraceSink", BrokenSink)
    caplog.set_level(logging.DEBUG)
    settings, _, _ = langfuse_settings(tmp_path)
    sink = InMemoryTraceSink()
    c = tracing_only(containers, settings, sink)
    assert c.get(TRACE) is sink
    assert "trace_sink_error op=build error=RuntimeError" in caplog.text
    assert "cannot build" not in caplog.text


def test_other_container_errors_are_not_swallowed(tmp_path: Path, containers: list[Container]) -> None:
    """failure (F1-4): an override factory that reads Key("trace") is a cycle; the build raises instead of falling back."""
    settings = make_settings(tmp_path)
    c = Container(settings=settings, limits=Limits())
    containers.append(c)
    register_tracing(c, FastAPI(), settings=settings, limits=c.limits)
    c.provide(OVERRIDE, lambda cc: cc.get(TRACE))
    with pytest.raises(ContainerError, match="provider cycle: trace -> trace_override -> trace"):
        c.build()


def test_override_reaches_turn_and_person_request_services(
    tmp_path: Path, containers: list[Container]
) -> None:
    """invariant (F1-5, worked pair, with override): both consumers hold the override, and one turn records into it."""
    with temp_sqlite() as store:
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("hello"))
        sink = InMemoryTraceSink()
        c = wired_services(containers, store, tmp_path, sink)
        turns = c.get(TURN_SERVICE)
        requests = c.get(PERSON_REQUESTS)
        assert isinstance(turns, TurnService) and turns._trace is sink
        assert isinstance(requests, PersonRequestService) and requests._trace is sink
        assert c.get(TRACE) is sink
        turns.run_turn(cmd)
        assert [t.ids.turn_id for t in sink.turns] == [cmd.turn_id]
        assert sink.turns[0].closed
        c.close()  # close before temp_sqlite removes the data dir


def test_without_override_services_get_the_settings_choice(
    tmp_path: Path, containers: list[Container]
) -> None:
    """regression (F1-5/F1-6, worked pair, no override): both consumers hold the settings choice (NullTraceSink)."""
    tl = tracing_module()
    with temp_sqlite() as store:
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("hello"))
        c = wired_services(containers, store, tmp_path, None)
        turns = c.get(TURN_SERVICE)
        requests = c.get(PERSON_REQUESTS)
        chosen = c.get(TRACE)
        assert isinstance(chosen, tl.NullTraceSink)
        assert isinstance(turns, TurnService) and turns._trace is chosen
        assert isinstance(requests, PersonRequestService) and requests._trace is chosen
        turns.run_turn(cmd)
        c.close()
