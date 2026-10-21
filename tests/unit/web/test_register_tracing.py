"""AEA-19 container hunk: sink choice by settings, alert binding, build-failure fallback (risk::security)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from meridian.config import Settings
from meridian.policy.limits import Limits
from meridian.ports.runtime import TraceSink
from meridian.web.container import Container, Key, register_tracing
from tests.unit.adapters._tracing_doubles import BASE_URL, PROJECT_ID, new_keys, tracing_module

BASE_ENV = {
    "ANTHROPIC_API_KEY": "test-anthropic",
    "OPENROUTER_API_KEY": "test-openrouter",
    "MERIDIAN_DEMO_USERNAME": "demo-user",
    "MERIDIAN_DEMO_PASSWORD": "demo-pass-test",
    "MERIDIAN_SESSION_SECRET": "session-secret-test",
}
LANGFUSE_NAMES = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_PROJECT_ID")


def langfuse_env() -> dict[str, str]:
    pk, sk = new_keys()
    return {
        "LANGFUSE_PUBLIC_KEY": pk,
        "LANGFUSE_SECRET_KEY": sk,
        "LANGFUSE_BASE_URL": BASE_URL,
        "LANGFUSE_PROJECT_ID": PROJECT_ID,
    }


class RecordingWriter:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def fire(self, *args: Any) -> None:
        self.calls.append(args)


@pytest.fixture
def containers() -> Iterator[list[Container]]:
    opened: list[Container] = []
    yield opened
    for c in opened:
        c.close()


def run_hunk(
    opened: list[Container], settings: Settings, alert_writer: RecordingWriter | None = None
) -> Container:
    c = Container(settings=settings, limits=Limits())
    opened.append(c)
    if alert_writer is not None:
        c.provide(Key[Any]("alert_writer"), lambda _c: alert_writer)
    register_tracing(c, FastAPI(), settings=settings, limits=c.limits)
    c.build()
    return c


@pytest.mark.parametrize("missing", LANGFUSE_NAMES)
def test_missing_value_gives_null_sink_without_alert(missing: str, containers: list[Container]) -> None:
    """invariant (AC-9): any one of the four LANGFUSE_* values missing builds the null sink and never alerts."""
    tl = tracing_module()
    env = {k: v for k, v in langfuse_env().items() if k != missing}
    writer = RecordingWriter()
    c = run_hunk(containers, Settings.from_env(BASE_ENV | env), writer)
    sink = c.get(Key[TraceSink]("trace"))
    print(missing, type(sink).__name__)
    assert isinstance(sink, tl.NullTraceSink)
    assert writer.calls == []


def test_sink_choice_by_settings(monkeypatch: pytest.MonkeyPatch, containers: list[Container]) -> None:
    """invariant (AC-9): all four set builds the Langfuse sink from Settings' four fields, starts it, no alert."""
    import inspect

    tl = tracing_module()
    env = langfuse_env()
    started: list[object] = []

    def recording_start(self: object) -> None:
        started.append(self)

    monkeypatch.setattr(tl.LangfuseTraceSink, "start", recording_start)
    writer = RecordingWriter()
    c = run_hunk(containers, Settings.from_env(BASE_ENV | env), writer)
    sink = c.get(Key[TraceSink]("trace"))
    assert isinstance(sink, tl.LangfuseTraceSink)
    assert started == [sink]
    expected = tl.LangfuseExportSettings(
        public_key=SecretStr(env["LANGFUSE_PUBLIC_KEY"]),
        secret_key=SecretStr(env["LANGFUSE_SECRET_KEY"]),
        base_url=BASE_URL,
        project_id=PROJECT_ID,
    )
    assert sink._settings == expected
    assert writer.calls == []
    assert not hasattr(Settings, "langfuse_export")
    assert "langfuse_export" not in inspect.getsource(register_tracing)


def test_on_alert_reaches_alert_writer(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, containers: list[Container]
) -> None:
    """invariant (PA-7): on_alert calls alert_writer.fire('trace_export_failed', reason); unbound only logs."""
    tl = tracing_module()
    captured: list[Any] = []

    class FakeSink:
        def __init__(self, settings: Any, redact: Any, on_alert: Any) -> None:
            captured.append(on_alert)

        def start(self) -> None:
            return None

        def close(self) -> None:
            return None

    monkeypatch.setattr(tl, "LangfuseTraceSink", FakeSink)
    settings = Settings.from_env(BASE_ENV | langfuse_env())

    writer = RecordingWriter()
    run_hunk(containers, settings, writer)
    captured[-1]("wrong_project")
    assert writer.calls == [("trace_export_failed", "wrong_project")]

    caplog.set_level(logging.DEBUG)
    run_hunk(containers, settings, None)
    captured[-1]("wrong_project")
    assert "trace_alert_unbound reason=wrong_project" in caplog.text


def test_build_failure_falls_back_to_null(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, containers: list[Container]
) -> None:
    """boundary (PA-8): a sink that cannot be constructed never fails start-up; the null sink is provided."""
    tl = tracing_module()

    class BrokenSink:
        def __init__(self, settings: Any, redact: Any, on_alert: Any) -> None:
            raise RuntimeError("cannot build")

    monkeypatch.setattr(tl, "LangfuseTraceSink", BrokenSink)
    caplog.set_level(logging.DEBUG)
    c = run_hunk(containers, Settings.from_env(BASE_ENV | langfuse_env()))
    assert isinstance(c.get(Key[TraceSink]("trace")), tl.NullTraceSink)
    assert "trace_sink_error op=build" in caplog.text
