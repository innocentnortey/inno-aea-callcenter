"""Shared doubles and builders for the AEA-19 tracing tests (frozen with the tests; synthetic values only).

The module under test is imported inside functions so every test file collects before it exists.
Private-looking values (phone, code, card, provider key) are built at run time from a seeded generator.
"""

from __future__ import annotations

import importlib
import random
import threading
import uuid
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import httpx
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import SecretStr

from meridian.domain.turn import TurnIds
from meridian.ports.models import CallRecord
from meridian.privacy.redact import Redactor, redact

PROJECT_ID = "proj-aea19-this-app"
OTHER_PROJECT_ID = "proj-aea19-other-app"
PROJECT_NAME = "meridian-call-center"
BASE_URL = "http://langfuse.test"


def tracing_module() -> Any:
    return importlib.import_module("meridian.adapters.tracing_langfuse")


def new_keys() -> tuple[str, str]:
    """Fresh Langfuse keys per sink: the SDK keeps one pipeline per public key per process."""
    return f"pk-lf-test-{uuid.uuid4().hex}", f"sk-lf-test-{uuid.uuid4().hex}"


def seeded_values(seed: int = 19) -> dict[str, str]:
    rng = random.Random(seed)
    phone = "-".join(("512", "555", "01" + "02"))
    code = str(rng.randint(100000, 999999))
    digits = "".join(str(rng.randint(0, 9)) for _ in range(16))
    card = " ".join(digits[i : i + 4] for i in range(0, 16, 4))
    api_key = "sk-ant-test-" + "".join(rng.choice("abcdef0123456789") for _ in range(24))
    return {"phone": phone, "code": code, "card": card, "api_key": api_key}


def wp2_text(values: Mapping[str, str]) -> str:
    return (
        f"Hi, my name is Omar Patel, phone {values['phone']}. My code is {values['code']}. "
        f"Card {values['card']}. Key {values['api_key']}. "
        "Invoice INV-204411 for MHC-10002 is $478.00, due 2026-11-01."
    )


def turn_ids(run_id: str | None = None, turn_id: str | None = None) -> TurnIds:
    return TurnIds.model_validate(
        {
            "thread_id": str(uuid.uuid4()),
            "turn_id": turn_id or str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "run_tag": "live",
            "run_id": run_id,
            "agent_version": "test",
        }
    )


def call_record(**overrides: object) -> CallRecord:
    defaults: dict[str, object] = {
        "provider": "anthropic",
        "model": "claude-sonnet-5-5",
        "latency_ms": 1200,
        "input_tokens": 100,
        "output_tokens": 20,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "thinking_tokens": 0,
        "cost_usd": 0.0004,
        "cost_source": "price_table",
        "status": "ok",
        "failure": None,
        "provider_request_id": "req_test_0001",
        "stop_reason": "end_turn",
        "role": "responder",
        "attempt": 1,
    }
    return CallRecord.model_validate({**defaults, **overrides})


Handler = Callable[[httpx.Request], httpx.Response]


class ProjectsStub:
    """Stands in for GET /api/public/projects."""

    def __init__(self, *handlers: Handler) -> None:
        self._handlers = handlers
        self.requests: list[httpx.Request] = []

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        handler = self._handlers[min(len(self.requests) - 1, len(self._handlers) - 1)]
        return handler(request)


def _projects_response(*projects: tuple[str, str]) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        data = [
            {"id": pid, "name": name, "organization": {"id": "org-test", "name": "Test org"}}
            for pid, name in projects
        ]
        return httpx.Response(200, json={"data": data})

    return handler


def ok(project_id: str = PROJECT_ID, name: str = PROJECT_NAME) -> Handler:
    return _projects_response((project_id, name))


def other() -> Handler:
    return _projects_response((OTHER_PROJECT_ID, PROJECT_NAME))


def several() -> Handler:
    return _projects_response((PROJECT_ID, PROJECT_NAME), (OTHER_PROJECT_ID, "another-name"))


def status(code: int) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(code, json={"message": "nope-body-marker"})

    return handler


def connect_error() -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable", request=request)

    return handler


def read_timeout() -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    return handler


def unexpected_error() -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        raise ValueError("unexpected")

    return handler


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class HangingExporter(SpanExporter):
    """export() blocks until `release` is set."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.spans: list[ReadableSpan] = []

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        self.release.wait(timeout=30)
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        self.release.set()


class ErroringExporter(SpanExporter):
    def __init__(self) -> None:
        self.calls = 0

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        self.calls += 1
        raise RuntimeError("export failed for test")

    def shutdown(self) -> None:
        return None


def span_strings(span: ReadableSpan) -> list[str]:
    out = [span.name]
    for value in (span.attributes or {}).values():
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, Sequence):
            out.extend(item for item in value if isinstance(item, str))
    return out


def trace_hex(span: ReadableSpan) -> str:
    assert span.context is not None
    return format(span.context.trace_id, "032x")


_EXPORTERS: dict[int, SpanExporter] = {}


def build_sink(
    registry: list[Any],
    *,
    exporter: SpanExporter | None = None,
    stub: ProjectsStub | None = None,
    clock: FakeClock | None = None,
    alerts: list[object] | None = None,
    keys: tuple[str, str] | None = None,
    redactor: Redactor | None = None,
    recheck_poll_s: float = 3600.0,
    **overrides: Any,
) -> tuple[Any, SpanExporter, ProjectsStub, list[object]]:
    tl = tracing_module()
    exporter = exporter if exporter is not None else InMemorySpanExporter()
    stub = stub if stub is not None else ProjectsStub(ok())
    clock = clock if clock is not None else FakeClock()
    alerts = alerts if alerts is not None else []
    pk, sk = keys if keys is not None else new_keys()
    settings = tl.LangfuseExportSettings(
        public_key=SecretStr(pk),
        secret_key=SecretStr(sk),
        base_url=BASE_URL,
        project_id=PROJECT_ID,
        **{"batch_interval_s": 3600.0, **overrides},
    )
    sink = tl.LangfuseTraceSink(
        settings,
        redactor if redactor is not None else redact,
        lambda *args: alerts.append(args),
        span_exporter=exporter,
        transport=stub.transport,
        clock=clock,
        recheck_poll_s=recheck_poll_s,
    )
    registry.append(sink)
    _EXPORTERS[id(sink)] = exporter
    return sink, exporter, stub, alerts


def close_all(registry: list[Any]) -> None:
    for sink in registry:
        exporter = _EXPORTERS.pop(id(sink), None)
        if isinstance(exporter, HangingExporter):
            exporter.release.set()
        sink.close()
