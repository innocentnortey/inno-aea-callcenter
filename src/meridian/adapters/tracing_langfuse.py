"""Trace sinks (AEA-19, stage7/models.md section 4).

`LangfuseTraceSink` masks every span in our process and again in Langfuse's `mask_otel_spans` hook, exports on a
background thread through a bounded queue that drops and counts instead of waiting, and turns export on only after
Langfuse confirms the keys belong to this app's project. `NullTraceSink` exports nothing.
"""

from __future__ import annotations

import base64
import logging
import math
import re
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal

import httpx
from langfuse import Langfuse, LangfuseSpan, __version__, propagate_attributes
from langfuse.types import (
    AttributeValue,
    MaskOtelSpansParams,
    MaskOtelSpansResult,
    OtelSpanIdentifier,
    OtelSpanPatch,
)
from opentelemetry.exporter.otlp.proto.http import Compression
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace import format_trace_id
from pydantic import SecretStr

from meridian.ports.models import CallRecord
from meridian.ports.runtime import ExportStatus, SpanHandle, TurnIds
from meridian.privacy.redact import RedactionProfile, Redactor

__all__ = [
    "LangfuseExportSettings",
    "LangfuseTraceSink",
    "NullTraceSink",
    "TraceAlert",
    "TraceAlertReason",
]

_log = logging.getLogger(__name__)

TraceAlertReason = Literal["wrong_project", "project_check_failed"]
TraceAlert = Callable[[TraceAlertReason], None]  # the reason code only; never a key, URL or body (MOD-7)

_EXPORT_BATCH_SPANS = 512  # BSP max_export_batch_size (flush_at); independent of queue_max_spans
_BSP_QUEUE_CEILING = 2048  # OTel BatchSpanProcessor default deque; our cap must stay at or below it
_PROJECTS_PATH = "/api/public/projects"
_OTLP_TRACES_PATH = "/api/public/otel/v1/traces"
_KEY_REMOVED = "[key removed]"
_REMOVED = "[removed]"
_DATA_URI_REMOVED = "[data uri removed]"
_KEY_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:sk|pk)-[A-Za-z0-9][A-Za-z0-9_-]{7,}")
_DATA_URI_PATTERN = re.compile(r"data:[A-Za-z0-9.+/-]*;base64,", re.IGNORECASE)
_UUID4 = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
_META = "langfuse.observation.metadata."
_ID_KEYS = frozenset({"session.id", _META + "turn_id", _META + "thread_id", _META + "request_id"})
_PASS_THROUGH_KEYS = frozenset(
    {
        "langfuse.trace.name",
        "langfuse.environment",
        "langfuse.release",
        "langfuse.version",
        "langfuse.observation.type",
        "langfuse.observation.level",
        "langfuse.observation.model.name",
        "langfuse.observation.usage_details",
        "langfuse.observation.cost_details",
        "langfuse.internal.as_root",
        "langfuse.internal.is_app_root",
        *(
            _META + k
            for k in (
                "run_tag",
                "agent_version",
                "role",
                "provider",
                "attempt",
                "latency_ms",
                "call_status",
                "failure_kind",
                "http_status",
                "cost_source",
                "stop_reason",
                "provider_request_id",
                "thinking_tokens",
                "elapsed_ms",
            )
        ),
    }
)
_ExportState = Literal["pending", "on", "off_wrong_project", "off_check_failed"]


class _LogGuard(logging.Filter):
    """Keeps the Langfuse SDK's own logger from carrying our keys or unmasked span text."""

    def __init__(self, secrets: tuple[str, ...]) -> None:
        super().__init__()
        self._secrets = tuple(s for s in secrets if s)

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < logging.WARNING:
            return False
        text = record.getMessage()
        if any(secret in text for secret in self._secrets):
            for secret in self._secrets:
                text = text.replace(secret, _KEY_REMOVED)
            record.msg, record.args = text, None
        return True


@dataclass(frozen=True)
class LangfuseExportSettings:
    """Built by the container from Settings' four langfuse_* fields."""

    public_key: SecretStr
    secret_key: SecretStr
    base_url: str
    project_id: str
    queue_max_spans: int = 1024  # [A] MOD-8
    batch_interval_s: float = 5.0  # [A]
    export_timeout_s: float = 5.0  # [A]; the exporter's own, never a turn's
    check_timeout_s: float = 5.0  # [A]; the start-up project check
    recheck_after_s: float = 600.0  # [A]; only after project_check_failed


@dataclass(eq=False)
class _TurnState:
    owner: object
    session_id: str
    observation: LangfuseSpan | None
    trace_id: str | None
    saw_off: bool = False
    setup_failed: bool = False
    offered: int = 0
    dropped: int = 0
    status: ExportStatus | None = None


class _RecordingExporter(SpanExporter):
    """Records whether the most recent batch failed or hangs."""

    def __init__(
        self,
        inner: SpanExporter,
        started: Callable[[], None],
        finished: Callable[[bool], None],
    ) -> None:
        self._inner = inner
        self._started = started
        self._finished = finished

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        self._started()
        ok = False
        try:
            ok = self._inner.export(spans) == SpanExportResult.SUCCESS
        except Exception as exc:
            ok = False
            _log.warning("trace_export_batch_error error=%s", type(exc).__name__)
        finally:
            self._finished(ok)
        return SpanExportResult.SUCCESS if ok else SpanExportResult.FAILURE

    def shutdown(self) -> None:
        self._inner.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._inner.force_flush(timeout_millis)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def _str_items(value: object) -> tuple[str, ...] | None:
    """The items of a non-empty sequence of strings, else None (a str is not treated as a sequence)."""
    if isinstance(value, str) or not isinstance(value, Sequence) or len(value) == 0:
        return None
    if not all(isinstance(item, str) for item in value):
        return None
    return tuple(str(item) for item in value)


def _removed_updates(attributes: Mapping[str, AttributeValue]) -> dict[str, AttributeValue]:
    out: dict[str, AttributeValue] = {}
    for key, value in attributes.items():
        if isinstance(value, str):
            out[key] = _REMOVED
        else:
            items = _str_items(value)
            if items is not None:
                out[key] = tuple(_REMOVED for _ in items)
    return out


class LangfuseTraceSink:
    """Implements TraceSink with Langfuse export behind masking, a bounded queue and a project check."""

    def __init__(
        self,
        settings: LangfuseExportSettings,
        redact: Redactor,
        on_alert: TraceAlert,
        *,
        span_exporter: SpanExporter | None = None,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
        recheck_poll_s: float | None = None,
    ) -> None:
        if not 1 <= settings.queue_max_spans <= _BSP_QUEUE_CEILING:
            raise ValueError("queue_max_spans: out_of_range (1..2048)")
        for name in ("batch_interval_s", "export_timeout_s", "check_timeout_s", "recheck_after_s"):
            if not getattr(settings, name) > 0:
                raise ValueError(f"{name}: must_be_positive")
        self._settings = settings
        self._redact = redact
        self._on_alert = on_alert
        self._clock = clock
        self._pk = settings.public_key.get_secret_value()
        self._sk = settings.secret_key.get_secret_value()
        self._base = settings.base_url.rstrip("/")
        self._recheck_poll_s = (
            recheck_poll_s if recheck_poll_s is not None else min(settings.recheck_after_s, 30.0)
        )

        self._lock = threading.Lock()
        self._state: _ExportState = "pending"
        self._alerted: set[TraceAlertReason] = set()
        self._pending = 0
        self._dropped = 0
        self._last_batch_failed = False
        self._batch_started_at: float | None = None
        self._last_check_at: float | None = None
        self._turns: dict[str, _TurnState] = {}
        self._started = False
        self._closed = False
        self._stop = threading.Event()
        self._recheck_thread: threading.Thread | None = None

        self._http = httpx.Client(
            base_url=self._base,
            auth=httpx.BasicAuth(self._pk, self._sk),
            timeout=settings.check_timeout_s,
            transport=transport,
            follow_redirects=False,
        )
        inner = span_exporter if span_exporter is not None else self._build_otlp_exporter()
        self._recorder = _RecordingExporter(inner, self._batch_started, self._batch_finished)
        self._provider = TracerProvider(sampler=ALWAYS_ON)
        # The SDK logs the public key at INFO on start-up and span bodies at DEBUG (LANGFUSE_DEBUG=true), and it
        # resets its own logger level while starting: a filter drops those records and scrubs our keys from the rest.
        langfuse_logger = logging.getLogger("langfuse")
        langfuse_logger.setLevel(logging.WARNING)
        self._log_guard = _LogGuard((self._pk, self._sk))
        langfuse_logger.addFilter(self._log_guard)
        self._client = Langfuse(
            public_key=self._pk,
            secret_key=self._sk,
            base_url=self._base,
            timeout=max(1, math.ceil(settings.export_timeout_s)),
            debug=False,
            tracing_enabled=True,
            flush_at=_EXPORT_BATCH_SPANS,
            flush_interval=settings.batch_interval_s,
            mask_otel_spans=self._mask_hook,
            should_export_span=self._admit,
            tracer_provider=self._provider,
            span_exporter=self._recorder,
        )
        langfuse_logger.setLevel(logging.WARNING)

    def _build_otlp_exporter(self) -> SpanExporter:
        token = base64.b64encode(f"{self._pk}:{self._sk}".encode()).decode("ascii")
        headers = {
            "Authorization": f"Basic {token}",
            "x-langfuse-sdk-name": "python",
            "x-langfuse-sdk-version": __version__,
            "x-langfuse-public-key": self._pk,
            "x-langfuse-ingestion-version": "4",
        }
        return OTLPSpanExporter(
            endpoint=self._base + _OTLP_TRACES_PATH,
            headers=headers,
            timeout=self._settings.export_timeout_s,
            compression=Compression.Gzip,
        )

    # -- exporter bookkeeping ------------------------------------------------------------------------------

    def _batch_started(self) -> None:
        with self._lock:
            self._batch_started_at = self._clock()

    def _batch_finished(self, ok: bool) -> None:
        with self._lock:
            self._batch_started_at = None
            self._last_batch_failed = not ok

    def _export_hung(self, now: float) -> bool:
        return (
            self._batch_started_at is not None
            and now - self._batch_started_at > self._settings.export_timeout_s
        )

    # -- start-up project check (MOD-6) --------------------------------------------------------------------

    def _check_project(self) -> Literal["pass", "wrong_project", "project_check_failed"]:
        try:
            response = self._http.get(_PROJECTS_PATH)
        except Exception as exc:
            _log.info("trace_project_check unreachable error=%s", type(exc).__name__)
            return "project_check_failed"
        _log.info("trace_project_check http_status=%d", response.status_code)
        if response.status_code >= 500:
            return "project_check_failed"
        if response.status_code != 200:
            return "wrong_project"
        try:
            body = response.json()
        except ValueError:
            return "wrong_project"
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or len(data) != 1:
            return "wrong_project"
        if not isinstance(data[0], dict) or data[0].get("id") != self._settings.project_id:
            return "wrong_project"
        return "pass"

    def start(self) -> None:
        try:
            with self._lock:
                if self._started or self._closed:
                    return
                self._started = True
            self._apply_check(self._check_project())
        except Exception as exc:
            _log.warning("trace_sink_error op=start error=%s", type(exc).__name__)

    def _apply_check(self, result: Literal["pass", "wrong_project", "project_check_failed"]) -> None:
        alert: TraceAlertReason | None = None
        thread: threading.Thread | None = None
        with self._lock:
            if self._closed:
                return
            self._last_check_at = self._clock()
            if result == "pass":
                self._state = "on"
            elif result == "wrong_project":
                self._state = "off_wrong_project"
                if "wrong_project" not in self._alerted:
                    self._alerted.add("wrong_project")
                    alert = "wrong_project"
            else:
                self._state = "off_check_failed"
                if "project_check_failed" not in self._alerted:
                    self._alerted.add("project_check_failed")
                    alert = "project_check_failed"
                if self._recheck_thread is None:
                    thread = threading.Thread(
                        target=self._recheck_loop, name="meridian-trace-recheck", daemon=True
                    )
                    self._recheck_thread = thread
        _log.info("trace_project_check result=%s", result)
        if thread is not None:
            thread.start()
        if alert is not None:
            self._fire_alert(alert)

    def _fire_alert(self, reason: TraceAlertReason) -> None:
        try:
            self._on_alert(reason)
        except Exception as exc:
            _log.warning("trace_alert_failed reason=%s error=%s", reason, type(exc).__name__)

    def _recheck_if_due(self) -> None:
        with self._lock:
            if not (
                not self._closed
                and self._state == "off_check_failed"
                and self._last_check_at is not None
                and self._clock() - self._last_check_at >= self._settings.recheck_after_s
            ):
                return
            self._last_check_at = self._clock()
        self._apply_check(self._check_project())

    def _recheck_loop(self) -> None:
        while not self._stop.wait(self._recheck_poll_s):
            try:
                self._recheck_if_due()
            except Exception as exc:
                _log.warning("trace_sink_error op=recheck error=%s", type(exc).__name__)
            if self._state != "off_check_failed":
                return

    # -- masking -------------------------------------------------------------------------------------------

    def _mask_text(self, text: str) -> str:
        out = text
        for secret in (self._sk, self._pk):  # exact own keys first, before redact can split their digits
            if secret:
                out = out.replace(secret, _KEY_REMOVED)
        out = _KEY_PATTERN.sub(_KEY_REMOVED, out)
        out = self._redact(out, RedactionProfile.TRACE).text
        return _DATA_URI_PATTERN.sub(_DATA_URI_REMOVED, out)

    def _safe_mask(self, text: str) -> str:
        try:
            return self._mask_text(text)
        except Exception:
            return _REMOVED

    def _masked_updates(self, attributes: Mapping[str, AttributeValue]) -> dict[str, AttributeValue]:
        updates: dict[str, AttributeValue] = {}
        for key, value in attributes.items():
            if key in _PASS_THROUGH_KEYS:
                continue
            if key in _ID_KEYS and isinstance(value, str) and _UUID4.fullmatch(_unquote(value)):
                continue
            if isinstance(value, str):
                masked = self._mask_text(value)
                if masked != value:
                    updates[key] = masked
            else:
                items = _str_items(value)
                if items is not None:
                    masked_items = tuple(self._mask_text(v) for v in items)
                    if masked_items != items:
                        updates[key] = masked_items
        return updates

    def _mask_hook(self, *, params: MaskOtelSpansParams) -> MaskOtelSpansResult:
        with self._lock:  # every span leaving the queue frees one slot, exactly once
            self._pending = max(0, self._pending - len(params.spans))
        patches: dict[OtelSpanIdentifier, OtelSpanPatch | None] = {}
        for ident, span in params.spans.items():
            try:
                updates = self._masked_updates(span.attributes)
            except Exception:
                updates = _removed_updates(span.attributes)  # fail closed for this span
            if updates:
                patches[ident] = OtelSpanPatch(set_attributes=updates)
        return MaskOtelSpansResult(span_patches=patches)

    # -- admission: the bounded queue (MOD-8) --------------------------------------------------------------

    def _admit(self, span: ReadableSpan) -> bool:
        if span.end_time is None:  # Langfuse's start-time call (app-root marking only)
            return self._state == "on"
        if span.context is None:
            return False
        trace_id = format_trace_id(span.context.trace_id)
        with self._lock:
            turn = self._turns.get(trace_id)
            if self._state != "on" or self._closed:  # export off: not queued, not counted as dropped
                if turn is not None:
                    turn.saw_off = True
                return False
            if self._pending >= self._settings.queue_max_spans:
                self._dropped += 1
                if turn is not None:
                    turn.dropped += 1
                return False
            self._pending += 1
            if turn is not None:
                turn.offered += 1
            return True

    # -- spans ---------------------------------------------------------------------------------------------

    def _state_of(self, handle: SpanHandle) -> _TurnState | None:
        native = handle.native
        if isinstance(native, _TurnState) and native.owner is self:
            return native
        return None

    @contextmanager
    def turn(self, ids: TurnIds) -> Iterator[SpanHandle]:
        session = str(ids.thread_id)
        state: _TurnState
        if self._state != "on" or self._closed:
            state = _TurnState(owner=self, session_id=session, observation=None, trace_id=None, saw_off=True)
        else:
            try:
                meta: dict[str, str] = {
                    "turn_id": str(ids.turn_id),
                    "thread_id": session,
                    "request_id": str(ids.request_id),
                    "run_tag": ids.run_tag,
                    "agent_version": ids.agent_version,
                }
                if ids.run_id is not None:
                    meta["run_id"] = self._safe_mask(ids.run_id)
                with propagate_attributes(session_id=session, trace_name="turn"):
                    obs = self._client.start_observation(name="turn", as_type="span", metadata=meta)
                state = _TurnState(owner=self, session_id=session, observation=obs, trace_id=obs.trace_id)
                with self._lock:
                    self._turns[obs.trace_id] = state
            except Exception as exc:
                _log.warning("trace_sink_error op=turn error=%s", type(exc).__name__)
                state = _TurnState(
                    owner=self, session_id=session, observation=None, trace_id=None, setup_failed=True
                )
        handle = SpanHandle(turn_id=ids.turn_id, trace_id=state.trace_id, native=state)
        try:
            yield handle
        finally:
            if state.observation is not None:
                try:
                    state.observation.end()
                except Exception as exc:
                    _log.warning("trace_sink_error op=turn_end error=%s", type(exc).__name__)
            with self._lock:
                state.status = self._status_for(state, self._clock())
                if state.trace_id:
                    self._turns.pop(state.trace_id, None)

    @staticmethod
    def _call_metadata(record: CallRecord) -> dict[str, object]:
        meta: dict[str, object] = {
            "role": record.role.value,
            "provider": record.provider,
            "attempt": record.attempt,
            "latency_ms": record.latency_ms,
            "call_status": record.status,
            "cost_source": record.cost_source,
            "thinking_tokens": record.thinking_tokens,
        }
        if record.failure is not None:
            meta["failure_kind"] = record.failure.kind.value
            meta["http_status"] = record.failure.http_status
        if record.stop_reason is not None:
            meta["stop_reason"] = record.stop_reason
        if record.provider_request_id is not None:
            meta["provider_request_id"] = record.provider_request_id
        return meta

    def model_call(
        self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str
    ) -> None:
        try:
            state = self._state_of(parent)
            if state is None or state.observation is None:
                return
            with propagate_attributes(session_id=state.session_id):
                gen = state.observation.start_observation(
                    name=f"model_call:{record.role.value}",
                    as_type="generation",
                    input=self._safe_mask(masked_input),
                    output=self._safe_mask(masked_output),
                    model=record.model,
                    usage_details={
                        "input": record.input_tokens,
                        "output": record.output_tokens,
                        "cache_read": record.cache_read_tokens,
                        "cache_write": record.cache_write_tokens,
                    },
                    cost_details={"total": record.cost_usd},
                    metadata=self._call_metadata(record),
                    level="ERROR" if record.status == "error" else None,
                    status_message=record.failure.kind.value if record.failure is not None else None,
                )
            gen.end()
        except Exception as exc:
            _log.warning("trace_sink_error op=model_call error=%s", type(exc).__name__)

    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None:
        try:
            state = self._state_of(parent)
            if state is None or state.observation is None:
                return
            with propagate_attributes(session_id=state.session_id):
                span = state.observation.start_observation(
                    name=self._safe_mask(name),
                    as_type="span",
                    metadata={"elapsed_ms": elapsed_ms, "node_status": self._safe_mask(status)},
                )
            span.end()
        except Exception as exc:
            _log.warning("trace_sink_error op=node error=%s", type(exc).__name__)

    # -- status (MOD-9) ------------------------------------------------------------------------------------

    def _status_for(self, state: _TurnState, now: float) -> ExportStatus:
        """Call with self._lock held."""
        if state.saw_off:
            return "off"
        if state.setup_failed or state.dropped > 0:
            return "failed"
        if self._last_batch_failed or self._export_hung(now):
            return "failed"
        return "sent"

    def export_status(self, turn: SpanHandle) -> ExportStatus:
        state = self._state_of(turn)
        if state is None:
            return "off" if turn.trace_id is None else "failed"
        with self._lock:
            return state.status if state.status is not None else self._status_for(state, self._clock())

    def dropped_spans(self) -> int:
        with self._lock:
            return self._dropped

    def flush(self) -> None:
        try:
            self._client.flush()
        except Exception as exc:
            _log.warning("trace_sink_error op=flush error=%s", type(exc).__name__)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._stop.set()
        thread = self._recheck_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=self._settings.check_timeout_s + 1.0)
        for name, closer in (
            ("client", self._client.shutdown),
            ("provider", self._provider.shutdown),
            ("http", self._http.close),
        ):
            try:
                closer()
            except Exception as exc:
                _log.warning("trace_sink_error op=close_%s error=%s", name, type(exc).__name__)
        logging.getLogger("langfuse").removeFilter(self._log_guard)


class NullTraceSink:
    """Implements TraceSink; exports nothing, holds nothing."""

    @contextmanager
    def turn(self, ids: TurnIds) -> Iterator[SpanHandle]:
        yield SpanHandle(turn_id=ids.turn_id, trace_id=None)

    def model_call(
        self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str
    ) -> None:
        return None

    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None:
        return None

    def export_status(self, turn: SpanHandle) -> ExportStatus:
        return "off"
