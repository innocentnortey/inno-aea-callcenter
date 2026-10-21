"""AEA-19 contract tests: both trace sinks against the TraceSink port, and the masking guarantees (risk::security).

Frozen before the implementation. Real Langfuse SDK client, in-memory span exporter so the mask hook runs as in
production (DO-6 *Capture verification*), the real `redact` from AEA-04. No network, no model.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

import pytest
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from meridian.domain.common import ProviderFailure, ProviderFailureKind
from meridian.ports.runtime import SpanHandle, TraceSink
from tests.unit.adapters._tracing_doubles import (
    build_sink,
    call_record,
    close_all,
    seeded_values,
    span_strings,
    trace_hex,
    tracing_module,
    turn_ids,
    wp2_text,
)

INPUT_KEY = "langfuse.observation.input"


@pytest.fixture
def sinks() -> Iterator[list[Any]]:
    registry: list[Any] = []
    yield registry
    close_all(registry)


def _spans(exporter: Any) -> list[ReadableSpan]:
    assert isinstance(exporter, InMemorySpanExporter)
    return list(exporter.get_finished_spans())


def test_mask_hook_strips_seeded_values(sinks: list[Any]) -> None:
    """negative (AC-1): seeded private values never reach an exported span, even when passed unmasked."""
    values = seeded_values()
    keys = ("pk-lf-test-" + "a1b2c3d4" * 4, "sk-lf-test-" + "e5f6a7b8" * 4)
    sink, exporter, _stub, _alerts = build_sink(sinks, keys=keys)
    sink.start()
    text = wp2_text(values)
    with sink.turn(turn_ids()) as handle:
        sink.model_call(handle, call_record(), text, text + f" {keys[0]} {keys[1]}")
        sink.node(handle, "front", 12, "ok")
    sink._client.start_observation(name="direct", input=text).end()
    sink.flush()

    spans = _spans(exporter)
    assert len(spans) == 4
    forbidden = [values["phone"], "Omar Patel", values["code"], values["card"], values["api_key"], *keys]
    card_digits = re.sub(r"\D", "", values["card"])
    for span in spans:
        for text_seen in span_strings(span):
            for secret in forbidden:
                assert secret not in text_seen, (span.name, "private value leaked")
            assert card_digits not in re.sub(r"\D", "", text_seen)
    model_span = next(s for s in spans if s.name.startswith("model_call"))
    masked_input = str((model_span.attributes or {})[INPUT_KEY])
    print(masked_input)
    for kept in ("[phone ending 02]", "my name is [name]", "INV-204411", "$478.00", "MHC-10002"):
        assert kept in masked_input
    direct = next(s for s in spans if s.name == "direct")
    direct_input = str((direct.attributes or {})[INPUT_KEY])
    assert "[phone ending 02]" in direct_input
    assert "INV-204411" in direct_input


def test_mask_applies_to_all_span_kinds(sinks: list[Any]) -> None:
    """invariant (AC-2): the mask runs on every exported span, whatever created it."""
    code = seeded_values()["code"]
    sink, exporter, _stub, _alerts = build_sink(sinks)
    sink.start()
    with sink.turn(turn_ids(run_id=f"run-{code}")) as handle:
        sink.node(handle, f"tool:{code}", 3, f"failed {code}")
        sink.model_call(handle, call_record(), f"code {code}", f"again {code}")
    sink._client.start_observation(
        name="direct", input=f"code {code}", metadata={"note": f"code {code}"}
    ).end()
    sink.flush()

    spans = _spans(exporter)
    assert len(spans) == 4
    for span in spans:
        strings = span_strings(span)
        assert all(code not in s for s in strings), span.name
        assert any("[code]" in s for s in strings), span.name


@pytest.mark.parametrize("kind", ["null", "langfuse"])
def test_sinks_conform(kind: str, sinks: list[Any]) -> None:
    """invariant (AC-8): both sinks honour the TraceSink port; the null sink sends nothing."""
    tl = tracing_module()
    sink: TraceSink
    if kind == "null":
        sink = tl.NullTraceSink()
    else:
        built, _exporter, _stub, _alerts = build_sink(sinks)
        built.start()
        sink = built
    ids = turn_ids()
    with sink.turn(ids) as handle:
        assert isinstance(handle, SpanHandle)
        assert handle.turn_id == ids.turn_id
        returned_call: object = sink.model_call(handle, call_record(), "hello", "world")  # type: ignore[func-returns-value]
        returned_node: object = sink.node(handle, "front", 5, "ok")  # type: ignore[func-returns-value]
        assert returned_call is None
        assert returned_node is None
        status = sink.export_status(handle)
        assert status in {"off", "sent", "failed"}
    final = sink.export_status(handle)
    print(kind, handle.trace_id, final)
    if kind == "null":
        assert handle.trace_id is None
        assert final == "off"
        assert not hasattr(sink, "_client")
    else:
        assert handle.trace_id is not None
        assert re.fullmatch(r"[0-9a-f]{32}", handle.trace_id)
        assert final == "sent"


def test_ids_and_numbers_pass_unchanged(sinks: list[Any]) -> None:
    """invariant (PA-1, DO-6): IDs, usage, cost, timings and statuses pass the mask unchanged."""
    sink, exporter, _stub, _alerts = build_sink(sinks)
    sink.start()
    ids = turn_ids(turn_id="3f1c2a4e-8b7d-4e21-9a6b-a123456b7c8d")
    failure = ProviderFailure(
        kind=ProviderFailureKind.TIMEOUT,
        provider="anthropic",
        http_status=408,
        retry_after_s=None,
        retryable=True,
        provider_request_id=None,
    )
    record = call_record(
        input_tokens=123456, cost_usd=0.012345, failure=failure, status="error", attempt=2, latency_ms=8001
    )
    with sink.turn(ids) as handle:
        sink.model_call(handle, record, "question", "answer")
    sink.flush()

    spans = _spans(exporter)
    root = next(s for s in spans if s.name == "turn")
    root_attrs = root.attributes or {}
    assert root_attrs["langfuse.observation.metadata.turn_id"] == json.dumps(str(ids.turn_id))
    assert root_attrs["session.id"] == str(ids.thread_id)
    generation = next(s for s in spans if s.name.startswith("model_call"))
    attrs = generation.attributes or {}
    print(dict(attrs))
    assert attrs["langfuse.observation.model.name"] == "claude-sonnet-5-5"
    assert json.loads(str(attrs["langfuse.observation.usage_details"]))["input"] == 123456
    assert json.loads(str(attrs["langfuse.observation.cost_details"]))["total"] == 0.012345
    assert attrs["langfuse.observation.metadata.attempt"] == "2"
    assert attrs["langfuse.observation.metadata.latency_ms"] == "8001"
    assert attrs["langfuse.observation.metadata.http_status"] == "408"
    assert attrs["langfuse.observation.metadata.role"] == '"responder"'
    assert attrs["langfuse.observation.level"] == "ERROR"
    assert trace_hex(generation) == handle.trace_id
