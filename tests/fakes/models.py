"""Scripted model-port fakes (AEA-11). No vendor SDK, no network, no logging."""

from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, cast

from pydantic import BaseModel, JsonValue, ValidationError

from meridian.domain.common import (
    CallRecord,
    ProviderCall,
    ProviderFailure,
    ProviderFailureKind,
    ProviderName,
)
from meridian.ports.models import (
    Attempt,
    ChoiceAnswer,
    ChoiceRequest,
    ProviderMessages,
    StructuredRequest,
    ToolStep,
    ToolStepRequest,
)


class ScriptExhaustedError(BaseException):
    """A model fake was called more often than its script allows. Derives from BaseException so
    `except Exception` in the code under test cannot hide it (PD-3)."""


@dataclass(frozen=True)
class ScriptedFailure:
    """A scripted provider failure; `retryable=None` means the adapters' rule (PD-5)."""

    kind: ProviderFailureKind
    http_status: int | None = None
    retry_after_s: float | None = None
    retryable: bool | None = None


def provider_call(
    *,
    provider: ProviderName,
    model: str,
    failure: ProviderFailure | None = None,
    stop_reason: str | None = None,
    latency_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    thinking_tokens: int = 0,
    cost_usd: float = 0.0,
    cost_source: Literal["reported", "price_table"] = "price_table",
    provider_request_id: str | None = None,
) -> ProviderCall:
    """Build a ProviderCall (never a CallRecord: the gateway wraps it, MOD-1)."""
    return ProviderCall(
        provider=provider,
        model=model,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        thinking_tokens=thinking_tokens,
        cost_usd=cost_usd,
        cost_source=cost_source,
        status="error" if failure is not None else "ok",
        failure=failure,
        provider_request_id=provider_request_id,
        stop_reason=stop_reason,
    )


_RETRYABLE_KINDS = frozenset(
    {
        ProviderFailureKind.TIMEOUT,
        ProviderFailureKind.CONNECTION,
        ProviderFailureKind.RATE_LIMITED,
        ProviderFailureKind.OVERLOADED,
        ProviderFailureKind.SERVER,
    }
)
_BODY_RETRYABLE_CODES = frozenset({408, 429, 500, 502, 503, 504, 529})


def _default_retryable(kind: ProviderFailureKind, http_status: int | None) -> bool:
    if kind in _RETRYABLE_KINDS:
        return True
    return kind is ProviderFailureKind.BODY_ERROR and http_status in _BODY_RETRYABLE_CODES


def _failure(
    provider: ProviderName,
    model: str,
    kind: ProviderFailureKind,
    *,
    http_status: int | None,
    retry_after_s: float | None,
    retryable: bool | None,
) -> tuple[ProviderFailure, ProviderCall]:
    failure = ProviderFailure(
        kind=kind,
        provider=provider,
        http_status=http_status,
        retry_after_s=retry_after_s,
        retryable=retryable if retryable is not None else _default_retryable(kind, http_status),
        provider_request_id=None,
    )
    stop_reason = {ProviderFailureKind.REFUSAL: "refusal", ProviderFailureKind.MAX_TOKENS: "max_tokens"}.get(
        kind
    )
    return failure, provider_call(provider=provider, model=model, failure=failure, stop_reason=stop_reason)


def _scripted(
    provider: ProviderName, model: str, entry: ScriptedFailure
) -> tuple[ProviderFailure, ProviderCall]:
    return _failure(
        provider,
        model,
        entry.kind,
        http_status=entry.http_status,
        retry_after_s=entry.retry_after_s,
        retryable=entry.retryable,
    )


def _invalid_output(provider: ProviderName, model: str) -> tuple[ProviderFailure, ProviderCall]:
    return _failure(
        provider,
        model,
        ProviderFailureKind.INVALID_OUTPUT,
        http_status=200,
        retry_after_s=None,
        retryable=False,
    )


def _check_prebuilt(entry: Attempt[Any], provider: ProviderName, model: str) -> None:
    if isinstance(entry.record, CallRecord):
        raise ValueError("scripted Attempt carries a CallRecord; fakes return a ProviderCall")
    if entry.record.provider != provider or entry.record.model != model:
        raise ValueError("scripted Attempt is for another provider or model")


class _Script[E]:
    """An ordered list of entries. The caller holds the fake's lock around take() (PD-10)."""

    def __init__(self, entries: Sequence[E], owner: str) -> None:
        self._entries = list(entries)
        self._index = 0
        self._owner = owner

    @property
    def remaining(self) -> int:
        return len(self._entries) - self._index

    def take(self) -> E:
        if self._index >= len(self._entries):
            raise ScriptExhaustedError(f"{self._owner} script exhausted after {self._index} calls")
        entry = self._entries[self._index]
        self._index += 1
        return entry


class FakeChoiceModel:
    """Scripted ChoiceModel (the Jev stand-in)."""

    provider: ClassVar[ProviderName] = "openrouter_jev"
    DEFAULT_MODEL: ClassVar[str] = "typesafe/jev-1.13"

    def __init__(
        self,
        script: Sequence[ChoiceAnswer | ScriptedFailure | Attempt[ChoiceAnswer]],
        *,
        model: str | None = None,
    ) -> None:
        self._model = model if model is not None else self.DEFAULT_MODEL
        for entry in script:
            if isinstance(entry, Attempt):
                _check_prebuilt(entry, self.provider, self._model)
            elif not isinstance(entry, ChoiceAnswer | ScriptedFailure):
                raise TypeError(f"unsupported script entry: {type(entry).__name__}")
        self._script = _Script(script, type(self).__name__)
        self._lock = threading.Lock()
        self.requests: list[ChoiceRequest] = []
        self.timeouts: list[float] = []

    @property
    def model(self) -> str:
        return self._model

    @property
    def remaining(self) -> int:
        return self._script.remaining

    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]:
        with self._lock:
            entry = self._script.take()
            self.requests.append(req)
            self.timeouts.append(timeout_s)
        if isinstance(entry, Attempt):
            return entry
        if isinstance(entry, ScriptedFailure):
            failure, call = _scripted(self.provider, self._model, entry)
            return Attempt[ChoiceAnswer](value=None, record=call, failure=failure)
        valid = {f.name: f.options for f in req.fields}
        ok = set(entry.choices) == set(valid) and all(
            choice in valid[name] for name, choice in entry.choices.items()
        )
        if not ok:
            failure, call = _invalid_output(self.provider, self._model)
            return Attempt[ChoiceAnswer](value=None, record=call, failure=failure)
        return Attempt[ChoiceAnswer](
            value=entry, record=provider_call(provider=self.provider, model=self._model), failure=None
        )


class FakeAnthropicChoiceModel(FakeChoiceModel):
    """The Anthropic `ChoiceModel` stand-in, e.g. for the planner fallback."""

    provider: ClassVar[ProviderName] = "anthropic"
    DEFAULT_MODEL: ClassVar[str] = "claude-sonnet-5-5"


class FakeStructuredModel:
    """Scripted StructuredModel (Anthropic)."""

    provider: ClassVar[ProviderName] = "anthropic"
    DEFAULT_MODEL: ClassVar[str] = "claude-sonnet-5-5"

    def __init__(
        self,
        script: Sequence[BaseModel | Mapping[str, Any] | ScriptedFailure | Attempt[Any]],
        *,
        model: str | None = None,
    ) -> None:
        self._model = model if model is not None else self.DEFAULT_MODEL
        for entry in script:
            if isinstance(entry, Attempt):
                _check_prebuilt(entry, self.provider, self._model)
            elif not isinstance(entry, BaseModel | Mapping | ScriptedFailure):
                raise TypeError(f"unsupported script entry: {type(entry).__name__}")
        self._script = _Script(script, type(self).__name__)
        self._lock = threading.Lock()
        self.requests: list[StructuredRequest[Any]] = []
        self.timeouts: list[float] = []

    @property
    def model(self) -> str:
        return self._model

    @property
    def remaining(self) -> int:
        return self._script.remaining

    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]:
        with self._lock:
            entry = self._script.take()
            self.requests.append(req)
            self.timeouts.append(timeout_s)
        if isinstance(entry, Attempt):
            return cast("Attempt[T]", entry)
        if isinstance(entry, ScriptedFailure):
            failure, call = _scripted(self.provider, self._model, entry)
            failed: Attempt[T] = Attempt(value=None, record=call, failure=failure)
            return failed
        value: T | None = None
        if isinstance(entry, req.output_model):
            value = entry
        elif isinstance(entry, Mapping):
            try:
                value = req.output_model.model_validate(dict(entry))
            except ValidationError:
                value = None
        if value is None:
            failure, call = _invalid_output(self.provider, self._model)
            invalid: Attempt[T] = Attempt(value=None, record=call, failure=failure)
            return invalid
        return Attempt(
            value=value,
            record=provider_call(provider=self.provider, model=self._model, stop_reason="end_turn"),
            failure=None,
        )


class FakeToolModel:
    """Scripted ToolCallingModel (Anthropic)."""

    provider: ClassVar[ProviderName] = "anthropic"
    DEFAULT_MODEL: ClassVar[str] = "claude-sonnet-5-5"

    def __init__(
        self,
        script: Sequence[ToolStep | ScriptedFailure | Attempt[ToolStep]],
        *,
        model: str | None = None,
    ) -> None:
        self._model = model if model is not None else self.DEFAULT_MODEL
        for entry in script:
            if isinstance(entry, Attempt):
                _check_prebuilt(entry, self.provider, self._model)
            elif not isinstance(entry, ToolStep | ScriptedFailure):
                raise TypeError(f"unsupported script entry: {type(entry).__name__}")
        self._script = _Script(script, type(self).__name__)
        self._lock = threading.Lock()
        self.requests: list[ToolStepRequest] = []
        self.timeouts: list[float] = []
        self.starts: list[str] = []
        self.appends: list[tuple[ProviderMessages, ToolStep, tuple[tuple[str, str], ...]]] = []

    @property
    def model(self) -> str:
        return self._model

    @property
    def remaining(self) -> int:
        return self._script.remaining

    def start(self, user: str) -> ProviderMessages:
        with self._lock:
            self.starts.append(user)
        items: tuple[JsonValue, ...] = ({"role": "user", "content": user},)
        return ProviderMessages(provider=self.provider, model=self._model, items=items)

    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]:
        with self._lock:
            entry = self._script.take()
            self.requests.append(req)
            self.timeouts.append(timeout_s)
        if isinstance(entry, Attempt):
            return entry
        if isinstance(entry, ScriptedFailure):
            failure, call = _scripted(self.provider, self._model, entry)
            return Attempt[ToolStep](value=None, record=call, failure=failure)
        return Attempt[ToolStep](
            value=entry,
            record=provider_call(provider=self.provider, model=self._model, stop_reason=entry.stop_reason),
            failure=None,
        )

    def append(
        self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]
    ) -> ProviderMessages:
        if messages.provider != self.provider or messages.model != self._model:
            raise ValueError("ProviderMessages were built for another provider or model")
        with self._lock:
            self.appends.append((messages, step, tuple(results)))
        calls: list[JsonValue] = [{"id": c.id, "name": c.name, "args": c.args} for c in step.tool_calls]
        new_items: list[JsonValue] = [{"role": "assistant", "text": step.text, "tool_calls": calls}]
        if results:
            tool_results: list[JsonValue] = [{"tool_call_id": i, "content": c} for i, c in results]
            new_items.append({"role": "tool_results", "results": tool_results})
        return ProviderMessages(
            provider=self.provider, model=self._model, items=messages.items + tuple(new_items)
        )
