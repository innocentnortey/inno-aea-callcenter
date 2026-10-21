"""AEA-19 Langfuse sink unit tests (risk::security): never blocks, project check, status, no key leaks, fail closed."""

from __future__ import annotations

import ast
import base64
import logging
import re
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from meridian.privacy.redact import Redacted, RedactionProfile
from tests.unit.adapters._tracing_doubles import (
    ErroringExporter,
    FakeClock,
    HangingExporter,
    ProjectsStub,
    build_sink,
    call_record,
    close_all,
    connect_error,
    ok,
    other,
    read_timeout,
    seeded_values,
    several,
    span_strings,
    status,
    trace_hex,
    tracing_module,
    turn_ids,
    unexpected_error,
    wp2_text,
)

MODULE_PATH = Path(__file__).resolve().parents[3] / "src" / "meridian" / "adapters" / "tracing_langfuse.py"
LIMIT_S = 0.050


@pytest.fixture
def sinks() -> Iterator[list[Any]]:
    registry: list[Any] = []
    yield registry
    close_all(registry)


def _finished(exporter: Any) -> list[Any]:
    assert isinstance(exporter, InMemorySpanExporter)
    return list(exporter.get_finished_spans())


class Timer:
    def __init__(self) -> None:
        self.worst = 0.0

    def call(self, fn: Any, *args: Any) -> Any:
        start = time.perf_counter()
        try:
            return fn(*args)
        finally:
            self.worst = max(self.worst, time.perf_counter() - start)


def test_export_never_blocks_hanging_exporter(sinks: list[Any]) -> None:
    """failure (AC-3): a hanging exporter and a full queue never slow a turn; refused spans are counted."""
    exporter = HangingExporter()
    sink, _e, _stub, _alerts = build_sink(sinks, exporter=exporter)
    sink.start()
    timer = Timer()
    ids = turn_ids()
    cm = sink.turn(ids)
    handle = timer.call(cm.__enter__)
    for i in range(1600):
        timer.call(sink.node, handle, f"n{i}", 1, "ok")
    for _ in range(50):
        timer.call(sink.model_call, handle, call_record(), "in", "out")
    timer.call(cm.__exit__, None, None, None)
    print("max call ms", round(timer.worst * 1000, 2))
    assert timer.worst < LIMIT_S
    dropped = sink.dropped_spans()
    assert dropped > 0
    assert dropped >= 1651 - (1024 + 512)
    assert sink.export_status(handle) == "failed"
    exporter.release.set()
    sink.flush()
    assert len(exporter.spans) + dropped == 1651


def test_export_never_blocks_small_cap_counts_drops(sinks: list[Any]) -> None:
    """failure (AC-3): past queue_max_spans the excess is dropped and dropped_spans() equals the spans refused."""
    sink, exporter, _stub, _alerts = build_sink(sinks, queue_max_spans=8)
    sink.start()
    timer = Timer()
    cm = sink.turn(turn_ids())
    handle = timer.call(cm.__enter__)
    for i in range(20):
        timer.call(sink.node, handle, f"n{i}", 1, "ok")
    timer.call(cm.__exit__, None, None, None)
    assert timer.worst < LIMIT_S
    assert sink.dropped_spans() == 13
    sink.flush()
    assert len(_finished(exporter)) == 8


def test_export_never_blocks_erroring_exporter(sinks: list[Any]) -> None:
    """failure (AC-3): an exporter that raises never reaches the caller; the next turn reads failed."""
    exporter = ErroringExporter()
    sink, _e, _stub, _alerts = build_sink(sinks, exporter=exporter)
    sink.start()
    with sink.turn(turn_ids()) as first:
        for i in range(5):
            sink.node(first, f"a{i}", 1, "ok")
    sink.flush()
    timer = Timer()
    cm = sink.turn(turn_ids())
    second = timer.call(cm.__enter__)
    for i in range(5):
        timer.call(sink.node, second, f"b{i}", 1, "ok")
    timer.call(cm.__exit__, None, None, None)
    assert timer.worst < LIMIT_S
    assert sink.export_status(second) == "failed"
    assert exporter.calls >= 1


def test_export_never_blocks_client_failure(sinks: list[Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """failure (AC-3): a client that raises never fails the turn."""
    sink, _e, _stub, _alerts = build_sink(sinks)
    sink.start()

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("client down")

    monkeypatch.setattr(sink._client, "start_observation", boom)
    with sink.turn(turn_ids()) as handle:
        assert handle.trace_id is None
        sink.node(handle, "front", 1, "ok")
        sink.model_call(handle, call_record(), "a", "b")
    assert sink.export_status(handle) == "failed"


@pytest.mark.parametrize("answer", [other, several, lambda: status(401), lambda: status(403)])
def test_wrong_project_keys_turn_export_off(answer: Any, sinks: list[Any]) -> None:
    """failure (AC-4): keys that are not this app's project turn export off, alert once, send nothing."""
    keys = ("pk-lf-test-" + "1a2b3c4d" * 4, "sk-lf-test-" + "5e6f7a8b" * 4)
    clock = FakeClock()
    sink, exporter, stub, alerts = build_sink(sinks, stub=ProjectsStub(answer()), clock=clock, keys=keys)
    sink.start()
    assert alerts == [("wrong_project",)]
    assert len(stub.requests) == 1
    request = stub.requests[0]
    assert request.url.path == "/api/public/projects"
    token = base64.b64encode(f"{keys[0]}:{keys[1]}".encode()).decode("ascii")
    assert request.headers["Authorization"] == f"Basic {token}"
    with sink.turn(turn_ids()) as handle:
        sink.node(handle, "front", 1, "ok")
        sink.model_call(handle, call_record(), "a", "b")
    assert handle.trace_id is None
    assert sink.export_status(handle) == "off"
    sink._client.start_observation(name="direct", input="x").end()
    sink.flush()
    assert len(_finished(exporter)) == 0
    clock.advance(601)
    sink._recheck_if_due()
    assert len(stub.requests) == 1
    assert alerts == [("wrong_project",)]


@pytest.mark.parametrize("failing", [connect_error, read_timeout, lambda: status(503), unexpected_error])
def test_unreachable_at_start_rechecks(failing: Any, sinks: list[Any]) -> None:
    """failure (AC-5): unreachable at start-up never raises, alerts once, re-checks after recheck_after_s."""
    clock = FakeClock()
    stub = ProjectsStub(failing(), ok())
    sink, exporter, stub, alerts = build_sink(sinks, stub=stub, clock=clock)
    assert sink.start() is None
    assert alerts == [("project_check_failed",)]
    with sink.turn(turn_ids()) as first:
        sink.node(first, "front", 1, "ok")
    assert sink.export_status(first) == "off"
    assert first.trace_id is None
    clock.advance(599)
    sink._recheck_if_due()
    assert len(stub.requests) == 1
    clock.advance(1)
    sink._recheck_if_due()
    assert len(stub.requests) == 2
    assert alerts == [("project_check_failed",)]
    with sink.turn(turn_ids()) as second:
        sink.node(second, "front", 1, "ok")
    assert sink.export_status(second) == "sent"
    sink.flush()
    spans = _finished(exporter)
    assert spans
    assert all(trace_hex(s) == second.trace_id for s in spans)


def test_one_trace_per_turn_with_session_id(sinks: list[Any]) -> None:
    """invariant (AC-6): this app's keys turn export on; one trace per turn with the thread id as session id."""
    stub = ProjectsStub(ok(name="some-other-name"))
    sink, exporter, _stub, _alerts = build_sink(sinks, stub=stub)
    sink.start()
    ids = turn_ids()
    with sink.turn(ids) as handle:
        sink.node(handle, "front", 4, "ok")
        sink.model_call(handle, call_record(), "a", "b")
    with sink.turn(turn_ids()) as other_handle:
        pass
    sink.flush()
    assert handle.trace_id is not None
    assert re.fullmatch(r"[0-9a-f]{32}", handle.trace_id)
    mine = [s for s in _finished(exporter) if trace_hex(s) == handle.trace_id]
    assert len(mine) == 3
    root = next(s for s in mine if s.name == "turn")
    assert root.parent is None
    assert (root.attributes or {})["langfuse.trace.name"] == "turn"
    for span in mine:
        assert (span.attributes or {})["session.id"] == str(ids.thread_id)
        if span is not root:
            assert span.parent is not None
            assert root.context is not None
            assert span.parent.span_id == root.context.span_id
    assert other_handle.trace_id != handle.trace_id


def test_export_status_values(sinks: list[Any]) -> None:
    """capture (AC-7): exactly one of off/sent/failed per handle; concurrent turns do not share a status."""
    tl = tracing_module()
    seen: set[str] = set()

    healthy, _e, _s, _a = build_sink(sinks)
    healthy.start()
    with healthy.turn(turn_ids()) as handle:
        healthy.node(handle, "front", 1, "ok")
    seen.add(healthy.export_status(handle))
    assert healthy.export_status(handle) == "sent"
    assert healthy.export_status(handle) == "sent"

    small, _e, _s, _a = build_sink(sinks, queue_max_spans=4)
    small.start()
    with small.turn(turn_ids()) as handle:
        for i in range(6):
            small.node(handle, f"n{i}", 1, "ok")
    assert small.export_status(handle) == "failed"
    seen.add("failed")

    erroring = ErroringExporter()
    broken, _e, _s, _a = build_sink(sinks, exporter=erroring)
    broken.start()
    with broken.turn(turn_ids()) as first:
        broken.node(first, "front", 1, "ok")
    broken.flush()
    with broken.turn(turn_ids()) as second:
        broken.node(second, "front", 1, "ok")
    assert broken.export_status(second) == "failed"

    null = tl.NullTraceSink()
    with null.turn(turn_ids()) as handle:
        assert null.export_status(handle) == "off"
    wrong, _e, _s, _a = build_sink(sinks, stub=ProjectsStub(other()))
    wrong.start()
    with wrong.turn(turn_ids()) as handle:
        pass
    assert wrong.export_status(handle) == "off"

    inter, _e, _s, _a = build_sink(sinks, queue_max_spans=4)
    inter.start()
    cm_a = inter.turn(turn_ids())
    cm_b = inter.turn(turn_ids())
    handle_a = cm_a.__enter__()
    handle_b = cm_b.__enter__()
    inter.node(handle_a, "a1", 1, "ok")
    inter.node(handle_b, "b1", 1, "ok")
    inter.node(handle_b, "b2", 1, "ok")
    cm_a.__exit__(None, None, None)
    inter.node(handle_b, "b3", 1, "ok")
    cm_b.__exit__(None, None, None)
    assert inter.export_status(handle_a) == "sent"
    assert inter.export_status(handle_b) == "failed"
    assert {seen_value for seen_value in seen} <= {"off", "sent", "failed"}


def test_keys_never_logged(
    sinks: list[Any], monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-10): no key reaches logs, alerts or spans; the check response body is never logged."""
    monkeypatch.setenv("LANGFUSE_DEBUG", "true")
    caplog.set_level(logging.DEBUG)
    all_keys: list[str] = []
    alert_lists: list[list[object]] = []
    exporter = InMemorySpanExporter()
    for stub, use_exporter in (
        (ProjectsStub(status(401)), None),
        (ProjectsStub(connect_error()), None),
        (ProjectsStub(ok()), exporter),
    ):
        keys = ("pk-lf-test-" + "9a8b7c6d" * 4, "sk-lf-test-" + "0f1e2d3c" * 4)
        keys = (keys[0][:-1] + str(len(all_keys)), keys[1][:-1] + str(len(all_keys)))
        all_keys.extend(keys)
        sink, _e, _stub, alerts = build_sink(sinks, stub=stub, keys=keys, exporter=use_exporter)
        alert_lists.append(alerts)
        sink.start()
        if use_exporter is not None:
            with sink.turn(turn_ids()) as handle:
                sink.model_call(handle, call_record(), f"keys {keys[0]} {keys[1]}", f"again {keys[1]}")
            sink.flush()
    for key in all_keys:
        assert key not in caplog.text
        for record in caplog.records:
            assert all(key not in str(arg) for arg in (record.args if isinstance(record.args, tuple) else ()))
        for span in _finished(exporter):
            assert all(key not in s for s in span_strings(span))
    assert "nope-body-marker" not in caplog.text
    flat = [call for alerts in alert_lists for call in alerts]
    print(flat)
    assert flat == [("wrong_project",), ("project_check_failed",)]


def test_mask_fails_closed(sinks: list[Any]) -> None:
    """boundary (PA-2): when masking raises, the text becomes [removed]; nothing raw leaves."""

    def broken(text: str, profile: RedactionProfile) -> Redacted:
        raise RuntimeError("redactor down")

    values = seeded_values()
    sink, exporter, _stub, _alerts = build_sink(sinks, redactor=broken)
    sink.start()
    with sink.turn(turn_ids()) as handle:
        sink.model_call(handle, call_record(), wp2_text(values), wp2_text(values))
    sink.flush()
    spans = _finished(exporter)
    generation = next(s for s in spans if s.name.startswith("model_call"))
    assert (generation.attributes or {})["langfuse.observation.input"] == "[removed]"
    for span in spans:
        for text in span_strings(span):
            assert values["phone"] not in text
            assert values["code"] not in text
            assert "Omar Patel" not in text


def test_data_uri_never_reaches_client(sinks: list[Any]) -> None:
    """invariant (PA-3): a base64 data URI never reaches the Langfuse client (its media upload bypasses the hook)."""
    sink, exporter, _stub, _alerts = build_sink(sinks)
    sink.start()
    with sink.turn(turn_ids()) as handle:
        sink.model_call(handle, call_record(), "see data:text/plain;base64,QUJD end", "ok")
    sink.flush()
    generation = next(s for s in _finished(exporter) if s.name.startswith("model_call"))
    masked = str((generation.attributes or {})["langfuse.observation.input"])
    assert "[data uri removed]" in masked
    assert "base64," not in masked


@pytest.mark.parametrize(
    ("field", "value"),
    [("queue_max_spans", 0), ("queue_max_spans", 4096), ("batch_interval_s", 0)],
)
def test_settings_bounds_rejected(field: str, value: float, sinks: list[Any]) -> None:
    """boundary (PA-4): queue size outside 1..2048 or a non-positive interval is rejected at construction."""
    keys = ("pk-lf-test-" + "abcd1234" * 4, "sk-lf-test-" + "dcba4321" * 4)
    overrides: dict[str, Any] = {field: value}
    with pytest.raises(ValueError) as caught:
        build_sink(sinks, keys=keys, **overrides)
    message = str(caught.value)
    assert field in message
    assert keys[0] not in message
    assert keys[1] not in message


def test_adapter_import_direction() -> None:
    """invariant (PA-5, DO-3 section 2.1): the adapter imports only stdlib, its SDKs and ports/domain/redact."""
    tree = ast.parse(MODULE_PATH.read_text())
    stdlib = set(sys.stdlib_module_names)
    allowed_top = stdlib | {"httpx", "langfuse", "opentelemetry", "pydantic", "meridian"}
    allowed_meridian = {"meridian.ports.models", "meridian.ports.runtime", "meridian.privacy.redact"}
    found: list[str] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import"
            names = [node.module or ""]
        for name in names:
            found.append(name)
            assert name.split(".")[0] in allowed_top, name
            assert not name.startswith("langfuse._"), name
            if name.startswith("meridian"):
                assert name in allowed_meridian or name.startswith("meridian.domain"), name
    print(sorted(set(found)))


def test_close_is_idempotent_and_stops_recheck(sinks: list[Any]) -> None:
    """invariant (PA-6): close() releases the re-check thread and is safe to call twice."""
    sink, _e, _stub, _alerts = build_sink(sinks, stub=ProjectsStub(connect_error()), recheck_poll_s=0.01)
    sink.start()
    names = [t.name for t in threading.enumerate()]
    assert "meridian-trace-recheck" in names
    sink.close()
    sink.close()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and any(
        t.name == "meridian-trace-recheck" for t in threading.enumerate()
    ):
        time.sleep(0.02)
    assert not any(t.name == "meridian-trace-recheck" and t.is_alive() for t in threading.enumerate())
