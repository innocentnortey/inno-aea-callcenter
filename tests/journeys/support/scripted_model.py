"""The scripted provider adapter for journeys (AEA-57; integrated-journeys rule section 3.1).

One test-only class implementing the three model ports. It takes the provider's **raw** output per role and parses it the
way the real adapters do (models.md section 3), so schema mismatches surface as INVALID_OUTPUT exactly as in production.
Nothing under src/meridian imports this module; it is reachable only through ContainerOverrides, which no env name,
Settings field or flag can build.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, JsonValue, ValidationError

from meridian.config import RoleSpec, Settings
from meridian.domain.common import ProviderCall, ProviderFailure, ProviderFailureKind, ProviderName, Role
from meridian.ports.models import (
    Attempt,
    ChoiceAnswer,
    ChoiceRequest,
    ProviderMessages,
    StructuredRequest,
    ToolCall,
    ToolStep,
    ToolStepRequest,
)
from meridian.web.app import ContainerOverrides
from tests.fakes import ScriptedFailure, provider_call


@dataclass(frozen=True)
class RawToolCall:
    id: str
    name: str
    arguments: str  # the provider's raw JSON text for the arguments


@dataclass(frozen=True)
class RawToolStep:
    text: str
    calls: tuple[RawToolCall, ...] = ()
    stop_reason: str | None = "end_turn"


ScriptEntry = str | RawToolStep | ScriptedFailure
CallResult = Literal["ok", "invalid_output", "scripted_failure", "exhausted"]

CHOICE_ROLES = frozenset({Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK})
STRUCTURED_ROLES = frozenset({Role.RESPONDER, Role.BRIEF})
TOOL_ROLES = frozenset({Role.SPECIALIST})

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


@dataclass(frozen=True)
class ScriptedCall:
    role: Role
    method: Literal["choose", "structured", "tool_step"]
    request: ChoiceRequest | StructuredRequest[Any] | ToolStepRequest
    timeout_s: float
    result: CallResult


class JourneyScript:
    """Per-role queues of raw provider output, consumed in order; shared by every ScriptedModel of one run."""

    def __init__(self) -> None:
        self._queues: dict[Role, list[ScriptEntry]] = {}
        self._calls: list[ScriptedCall] = []
        self._lock = threading.Lock()

    def add(self, role: Role, *entries: ScriptEntry) -> None:
        for entry in entries:
            if isinstance(entry, ScriptedFailure):
                continue
            if role in TOOL_ROLES and not isinstance(entry, RawToolStep):
                raise TypeError(
                    f"{role.value} takes RawToolStep or ScriptedFailure, not {type(entry).__name__}"
                )
            if role not in TOOL_ROLES and not isinstance(entry, str):
                raise TypeError(
                    f"{role.value} takes raw JSON text or ScriptedFailure, not {type(entry).__name__}"
                )
        with self._lock:
            self._queues.setdefault(role, []).extend(entries)

    def take(self, role: Role) -> ScriptEntry | None:
        with self._lock:
            queue = self._queues.get(role)
            return queue.pop(0) if queue else None

    def record(self, call: ScriptedCall) -> None:
        with self._lock:
            self._calls.append(call)

    @property
    def calls(self) -> tuple[ScriptedCall, ...]:
        with self._lock:
            return tuple(self._calls)

    def remaining(self, role: Role | None = None) -> int:
        with self._lock:
            if role is not None:
                return len(self._queues.get(role, []))
            return sum(len(q) for q in self._queues.values())

    def problems(self) -> tuple[ScriptedCall, ...]:
        return tuple(c for c in self.calls if c.result in ("invalid_output", "exhausted"))


class ScriptedModel:
    """Test-only provider adapter implementing ChoiceModel, StructuredModel and ToolCallingModel."""

    provider: ClassVar[ProviderName] = "anthropic"

    def __init__(self, script: JourneyScript, *, role: Role, model: str) -> None:
        self._script = script
        self._role = role
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @property
    def role(self) -> Role:
        return self._role

    # -- shared helpers -------------------------------------------------------------------------------------------

    def _ok(self, stop_reason: str | None) -> ProviderCall:
        return provider_call(provider=self.provider, model=self._model, stop_reason=stop_reason)

    def _failed(self, failure: ProviderFailure) -> tuple[ProviderCall, ProviderFailure]:
        return provider_call(provider=self.provider, model=self._model, failure=failure), failure

    def _invalid(self) -> tuple[ProviderCall, ProviderFailure]:
        return self._failed(
            ProviderFailure(
                kind=ProviderFailureKind.INVALID_OUTPUT,
                provider=self.provider,
                http_status=200,
                retry_after_s=None,
                retryable=False,
                provider_request_id=None,
            )
        )

    def _scripted_failure(self, entry: ScriptedFailure) -> tuple[ProviderCall, ProviderFailure]:
        retryable = (
            entry.retryable
            if entry.retryable is not None
            else (
                entry.kind in _RETRYABLE_KINDS
                or (
                    entry.kind is ProviderFailureKind.BODY_ERROR
                    and entry.http_status in _BODY_RETRYABLE_CODES
                )
            )
        )
        return self._failed(
            ProviderFailure(
                kind=entry.kind,
                provider=self.provider,
                http_status=entry.http_status,
                retry_after_s=entry.retry_after_s,
                retryable=retryable,
                provider_request_id=None,
            )
        )

    def _note(
        self,
        method: Literal["choose", "structured", "tool_step"],
        request: ChoiceRequest | StructuredRequest[Any] | ToolStepRequest,
        timeout_s: float,
        result: CallResult,
    ) -> None:
        self._script.record(ScriptedCall(self._role, method, request, timeout_s, result))

    def _fail_attempt[T: BaseModel](
        self,
        method: Literal["choose", "structured", "tool_step"],
        request: ChoiceRequest | StructuredRequest[Any] | ToolStepRequest,
        timeout_s: float,
        entry: ScriptEntry | None,
    ) -> Attempt[T] | None:
        """The attempt for an empty queue or a scripted failure; None when `entry` is real output to parse."""
        if entry is None:
            call, failure = self._invalid()
            self._note(method, request, timeout_s, "exhausted")
            return Attempt(value=None, record=call, failure=failure)
        if isinstance(entry, ScriptedFailure):
            call, failure = self._scripted_failure(entry)
            self._note(method, request, timeout_s, "scripted_failure")
            return Attempt(value=None, record=call, failure=failure)
        return None

    def _invalid_attempt[T: BaseModel](
        self,
        method: Literal["choose", "structured", "tool_step"],
        request: ChoiceRequest | StructuredRequest[Any] | ToolStepRequest,
        timeout_s: float,
    ) -> Attempt[T]:
        call, failure = self._invalid()
        self._note(method, request, timeout_s, "invalid_output")
        return Attempt(value=None, record=call, failure=failure)

    # -- ports ----------------------------------------------------------------------------------------------------

    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]:
        entry = self._script.take(self._role)
        early: Attempt[ChoiceAnswer] | None = self._fail_attempt("choose", req, timeout_s, entry)
        if early is not None:
            return early
        assert isinstance(entry, str)
        try:
            data = json.loads(entry)
        except json.JSONDecodeError:
            return self._invalid_attempt("choose", req, timeout_s)
        options = {f.name: f.options for f in req.fields}
        if (
            not isinstance(data, dict)
            or not all(isinstance(v, str) for v in data.values())
            or set(data) != set(options)
            or any(data[name] not in options[name] for name in options)
        ):
            return self._invalid_attempt("choose", req, timeout_s)
        self._note("choose", req, timeout_s, "ok")
        return Attempt(
            value=ChoiceAnswer(choices=data, probabilities=None), record=self._ok(None), failure=None
        )

    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]:
        entry = self._script.take(self._role)
        early: Attempt[T] | None = self._fail_attempt("structured", req, timeout_s, entry)
        if early is not None:
            return early
        assert isinstance(entry, str)
        try:
            data = json.loads(entry)
            if not isinstance(data, dict):
                raise ValueError("not an object")
            value = req.output_model.model_validate(data)
        except (json.JSONDecodeError, ValueError, ValidationError):
            return self._invalid_attempt("structured", req, timeout_s)
        self._note("structured", req, timeout_s, "ok")
        return Attempt(value=value, record=self._ok("end_turn"), failure=None)

    def start(self, user: str) -> ProviderMessages:
        items: tuple[JsonValue, ...] = ({"role": "user", "content": user},)
        return ProviderMessages(provider=self.provider, model=self._model, items=items)

    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]:
        entry = self._script.take(self._role)
        early: Attempt[ToolStep] | None = self._fail_attempt("tool_step", req, timeout_s, entry)
        if early is not None:
            return early
        if not isinstance(entry, RawToolStep):
            return self._invalid_attempt("tool_step", req, timeout_s)
        calls: list[ToolCall] = []
        for raw_call in entry.calls:
            try:
                parsed = json.loads(raw_call.arguments)
            except json.JSONDecodeError:
                parsed = None
            calls.append(
                ToolCall(
                    id=raw_call.id, name=raw_call.name, args=parsed if isinstance(parsed, dict) else None
                )
            )
        raw: JsonValue = {
            "text": entry.text,
            "tool_calls": [{"id": c.id, "name": c.name, "arguments": c.arguments} for c in entry.calls],
            "stop_reason": entry.stop_reason,
        }
        step = ToolStep(text=entry.text, tool_calls=tuple(calls), raw=raw, stop_reason=entry.stop_reason)
        self._note("tool_step", req, timeout_s, "ok")
        return Attempt(value=step, record=self._ok(entry.stop_reason), failure=None)

    def append(
        self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]
    ) -> ProviderMessages:
        if messages.provider != self.provider or messages.model != self._model:
            raise ValueError("ProviderMessages were built for another provider or model")
        call_items: list[JsonValue] = [{"id": c.id, "name": c.name, "args": c.args} for c in step.tool_calls]
        new_items: list[JsonValue] = [{"role": "assistant", "text": step.text, "tool_calls": call_items}]
        if results:
            tool_results: list[JsonValue] = [{"tool_call_id": i, "content": c} for i, c in results]
            new_items.append({"role": "tool_results", "results": tool_results})
        return ProviderMessages(
            provider=self.provider, model=self._model, items=messages.items + tuple(new_items)
        )


class ScriptedAnthropicModel(ScriptedModel):
    provider: ClassVar[ProviderName] = "anthropic"


class ScriptedJevModel(ScriptedModel):
    provider: ClassVar[ProviderName] = "openrouter_jev"


def scripted_model_for(
    provider: ProviderName, script: JourneyScript, *, role: Role, model: str
) -> ScriptedModel:
    cls = ScriptedJevModel if provider == "openrouter_jev" else ScriptedAnthropicModel
    return cls(script, role=role, model=model)


def role_specs(settings: Settings) -> dict[Role, tuple[ProviderName, RoleSpec]]:
    """Every configured role with its provider and RoleSpec."""
    specs: dict[Role, tuple[ProviderName, RoleSpec]] = {}
    for table in (settings.models.choice, settings.models.structured, settings.models.tools):
        for role, entry in table.items():
            specs[role] = entry
    return specs


def scripted_overrides(
    settings: Settings, script: JourneyScript, *, wall_clock: Callable[[], datetime] | None
) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]:
    """Each role's object carries the provider and model that role's RoleSpec names (models.md section 7)."""
    choice = {
        role: scripted_model_for(p, script, role=role, model=spec.model)
        for role, (p, spec) in settings.models.choice.items()
    }
    structured = {
        role: scripted_model_for(p, script, role=role, model=spec.model)
        for role, (p, spec) in settings.models.structured.items()
    }
    tools = {
        role: scripted_model_for(p, script, role=role, model=spec.model)
        for role, (p, spec) in settings.models.tools.items()
    }
    overrides = ContainerOverrides(
        choice=choice, structured=structured, tools=tools, trace=None, wall_clock=wall_clock
    )
    models: dict[Role, ScriptedModel] = {}
    for table in (choice, structured, tools):
        for role, model in table.items():
            models[role] = model
    return overrides, models
