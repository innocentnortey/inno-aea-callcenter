"""The one model-call path (DO-3 section 4.5, S-2; DO-4 section 12; stage7/models.md section 5).

Every model call in a turn goes through ``ModelGateway``. A node names a role; the gateway finds the adapter and
``RoleSpec`` the typed role maps hold for it, then applies the rules in order: provider admission, deadline, the
per-turn Sonnet-call brake, redaction with the role's profile, at most two attempts, one ledger row and one span
per attempt, and the provider circuit. It never raises on a provider failure and never chooses a fallback.

Our own daily spend cap is checked before the turn by the turn service (MOD-11), not here.
"""

from __future__ import annotations

import json
import random
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Protocol

from pydantic import BaseModel, JsonValue

from meridian.config import RoleSpec
from meridian.domain.common import (
    Halt,
    HaltReason,
    MeridianModel,
    ProviderFailure,
    ProviderFailureKind,
    ProviderName,
)
from meridian.domain.turn import TurnContext, TurnIds
from meridian.policy.limits import Limits
from meridian.ports.models import (
    Attempt,
    CallRecord,
    ChoiceAnswer,
    ChoiceModel,
    ChoiceRequest,
    ChoiceRole,
    Role,
    StructuredModel,
    StructuredRequest,
    StructuredRole,
    ToolCallingModel,
    ToolRole,
    ToolStep,
    ToolStepRequest,
)
from meridian.ports.runtime import TraceSink
from meridian.privacy.redact import RedactionProfile, Redactor

__all__ = ["CallLedger", "ModelGateway", "ModelOutcome"]

_REFUSE: Final = "refuse"  # = CallAdmission.REFUSE.value (models.md section 6)
_PROBE: Final = "probe"  # = CallAdmission.PROBE.value
_ANTHROPIC: Final = "anthropic"
_JEV: Final = "openrouter_jev"
_CAP_KINDS: Final = frozenset({ProviderFailureKind.PROVIDER_SPEND_CAP, ProviderFailureKind.OUR_SPEND_LIMIT})
_MAX_ATTEMPTS: Final = 2
_RETRY_MARGIN_S: Final = 1.0  # "wait plus 1 s still fits" (DO-4 section 12)
_BACKOFF_MIN_S: Final = 0.5  # MOD-4
_BACKOFF_MAX_S: Final = 1.0
_PRUNE_AFTER_S: Final = 1.0  # MOD-12
_CHOICE_ROLES: Final = frozenset({Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK})
_STRUCTURED_ROLES: Final = frozenset({Role.RESPONDER, Role.BRIEF})
_TOOL_ROLES: Final = frozenset({Role.SPECIALIST})
_REQUEST_PROFILES: Final = frozenset({RedactionProfile.JEV, RedactionProfile.SONNET})


def _monotonic() -> float:
    return time.monotonic()


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _backoff_s() -> float:
    return random.uniform(_BACKOFF_MIN_S, _BACKOFF_MAX_S)  # noqa: S311 - retry jitter, not security


@dataclass
class _SonnetCount:
    deadline: float
    calls: int = 0


class CallLedger(Protocol):
    """The four LedgerService methods the gateway calls (models.md section 6).

    LedgerService (AEA-26) satisfies it structurally; its CallAdmission is a StrEnum, so comparing with the
    strings above works.
    """

    def admit_call(self, provider: ProviderName) -> str: ...

    def record(self, call: CallRecord, ids: TurnIds) -> None: ...

    def trip_provider_cap(self, failure: ProviderFailure) -> None: ...

    def close_provider_cap(self, provider: ProviderName) -> None: ...


class ModelOutcome[T: BaseModel](MeridianModel):
    """DO-4 section 12: what a node reads back from the gateway."""

    value: T | None
    calls: tuple[CallRecord, ...]
    failure: ProviderFailure | None
    halt: Halt | None


# ---------------------------------------------------------------------------
# Redaction and rendering helpers (pure; the redactor is passed in)
# ---------------------------------------------------------------------------


def _redact_json(value: JsonValue, profile: RedactionProfile, redact: Redactor) -> JsonValue:
    """Redact every string leaf; keys are identifiers and are never redacted."""
    if isinstance(value, str):
        return redact(value, profile).text
    if isinstance(value, list):
        return [_redact_json(v, profile, redact) for v in value]
    if isinstance(value, dict):
        return {k: _redact_json(v, profile, redact) for k, v in value.items()}
    return value


def _redact_choice(req: ChoiceRequest, profile: RedactionProfile, redact: Redactor) -> ChoiceRequest:
    def r(text: str) -> str:
        return redact(text, profile).text

    state = {k: _redact_json(v, profile, redact) for k, v in req.state.items()}
    fields = tuple(
        f.model_copy(
            update={"instructions": r(f.instructions), "options": {k: r(v) for k, v in f.options.items()}}
        )
        for f in req.fields
    )
    return req.model_copy(update={"system": r(req.system), "state": state, "fields": fields})


def _redact_structured[T: BaseModel](
    req: StructuredRequest[T], spec: RoleSpec, redact: Redactor
) -> StructuredRequest[T]:
    def r(text: str) -> str:
        return redact(text, spec.redaction).text

    return req.model_copy(
        update={
            "system_prefix": r(req.system_prefix),
            "system_dynamic": r(req.system_dynamic),
            "user": r(req.user),
            "max_tokens": spec.max_tokens,
            "effort": spec.effort,
        }
    )


def _redact_tool(req: ToolStepRequest, spec: RoleSpec, redact: Redactor) -> ToolStepRequest:
    """``messages`` and ``tools`` pass through untouched (MOD-17): only the adapter reads the items."""

    def r(text: str) -> str:
        return redact(text, spec.redaction).text

    return req.model_copy(
        update={
            "system_prefix": r(req.system_prefix),
            "system_dynamic": r(req.system_dynamic),
            "max_tokens": spec.max_tokens,
            "effort": spec.effort,
        }
    )


def _dump_masked(payload: JsonValue, redact: Redactor) -> str:
    masked = _redact_json(payload, RedactionProfile.TRACE, redact)
    return json.dumps(masked, ensure_ascii=False, sort_keys=True)


def _render_out_model(value: BaseModel | None, redact: Redactor) -> str:
    if value is None:
        return ""
    return _dump_masked(value.model_dump(mode="json"), redact)


# ---------------------------------------------------------------------------
# The gateway
# ---------------------------------------------------------------------------


class ModelGateway:
    def __init__(
        self,
        *,
        choice: Mapping[ChoiceRole, tuple[ChoiceModel, RoleSpec]],
        structured: Mapping[StructuredRole, tuple[StructuredModel, RoleSpec]],
        tools: Mapping[ToolRole, tuple[ToolCallingModel, RoleSpec]],
        ledger: CallLedger,
        trace: TraceSink,
        redact: Redactor,
        limits: Limits,
    ) -> None:
        self._choice = MappingProxyType(dict(choice))
        self._structured = MappingProxyType(dict(structured))
        self._tools = MappingProxyType(dict(tools))
        for roles, allowed, name in (
            (self._choice, _CHOICE_ROLES, "choice"),
            (self._structured, _STRUCTURED_ROLES, "structured"),
            (self._tools, _TOOL_ROLES, "tools"),
        ):
            for role in roles:
                if role not in allowed:
                    raise ValueError(f"role {role.value} does not belong in the {name} map")
        for name, mapping in (("structured", self._structured), ("tools", self._tools)):
            for role, (adapter, _) in mapping.items():
                if adapter.provider != _ANTHROPIC:
                    raise ValueError(f"role {role.value} in the {name} map needs an anthropic adapter")
        all_specs: list[tuple[Role, ProviderName, RoleSpec]] = [
            (role, adapter.provider, spec)
            for mapping in (self._choice, self._structured, self._tools)
            for role, (adapter, spec) in mapping.items()
        ]
        for role, provider, spec in all_specs:
            if spec.redaction not in _REQUEST_PROFILES:
                raise ValueError(f"role {role.value} has request profile {spec.redaction.value}")
            if provider == _JEV and spec.redaction is not RedactionProfile.JEV:
                raise ValueError(f"role {role.value} sends to Jev and needs the jev profile")
        self._ledger = ledger
        self._trace = trace
        self._redact = redact
        self._sonnet_limit = limits.brakes.sonnet_calls
        self._sonnet_calls: dict[tuple[str, float], _SonnetCount] = {}
        self._lock = threading.Lock()

    # -- public methods ----------------------------------------------------

    def choose(self, role: ChoiceRole, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]:
        adapter, spec = _route(self._choice, role)

        def prepare() -> tuple[Callable[[float], Attempt[ChoiceAnswer]], str]:
            sent = _redact_choice(req, spec.redaction, self._redact)

            def send(timeout_s: float) -> Attempt[ChoiceAnswer]:
                return adapter.choose(sent, timeout_s=timeout_s)

            return send, _redact_choice(sent, RedactionProfile.TRACE, self._redact).model_dump_json()

        return self._run(role, adapter.provider, spec, ctx, prepare)

    def structured[T: BaseModel](
        self, role: StructuredRole, req: StructuredRequest[T], ctx: TurnContext
    ) -> ModelOutcome[T]:
        adapter, spec = _route(self._structured, role)

        def prepare() -> tuple[Callable[[float], Attempt[T]], str]:
            sent = _redact_structured(req, spec, self._redact)

            def send(timeout_s: float) -> Attempt[T]:
                return adapter.structured(sent, timeout_s=timeout_s)

            parts = (sent.system_prefix, sent.system_dynamic, sent.user)
            masked = "\n\n".join(self._redact(x, RedactionProfile.TRACE).text for x in parts)
            return send, masked

        return self._run(role, adapter.provider, spec, ctx, prepare)

    def tool_step(self, role: ToolRole, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[ToolStep]:
        adapter, spec = _route(self._tools, role)

        def prepare() -> tuple[Callable[[float], Attempt[ToolStep]], str]:
            sent = _redact_tool(req, spec, self._redact)

            def send(timeout_s: float) -> Attempt[ToolStep]:
                return adapter.tool_step(sent, timeout_s=timeout_s)

            masked = "\n\n".join(
                [
                    self._redact(sent.system_prefix, RedactionProfile.TRACE).text,
                    self._redact(sent.system_dynamic, RedactionProfile.TRACE).text,
                    "tools: " + ", ".join(t.name for t in sent.tools),
                ]
            )
            return send, masked

        return self._run(role, adapter.provider, spec, ctx, prepare)

    # -- the shared run loop -----------------------------------------------

    def _halt(self, reason: HaltReason, role: Role, ctx: TurnContext) -> Halt:
        elapsed = max(0, int((_monotonic() - ctx.budget.started) * 1000))
        return Halt(reason=reason, node=role.value, elapsed_ms=elapsed)

    def _run[V: BaseModel](
        self,
        role: Role,
        provider: ProviderName,
        spec: RoleSpec,
        ctx: TurnContext,
        prepare: Callable[[], tuple[Callable[[float], Attempt[V]], str]],
    ) -> ModelOutcome[V]:
        def halted(reason: HaltReason) -> ModelOutcome[V]:
            return ModelOutcome[V](value=None, calls=(), failure=None, halt=self._halt(reason, role, ctx))

        # Rule 1: provider admission.
        adm = self._ledger.admit_call(provider)
        if adm == _REFUSE:
            return halted(HaltReason.PROVIDER_SPEND_CAP)

        # Rule 2: deadline.
        timeout = ctx.budget.timeout_for(spec.cap_s)
        if timeout is None:
            return halted(HaltReason.DEADLINE)

        # Rule 3: Sonnet-call brake (atomic check and increment; pruning on every call).
        with self._lock:
            now = _monotonic()
            stale = [k for k, v in self._sonnet_calls.items() if v.deadline < now - _PRUNE_AFTER_S]
            for key in stale:
                del self._sonnet_calls[key]
            if provider == _ANTHROPIC:
                key = (str(ctx.ids.turn_id), ctx.budget.started)
                entry = self._sonnet_calls.setdefault(key, _SonnetCount(deadline=ctx.budget.deadline))
                if entry.calls >= self._sonnet_limit:
                    over = True
                else:
                    entry.calls += 1
                    over = False
            else:
                over = False
        if over:
            return halted(HaltReason.BRAKE_SONNET_CALLS)

        # Rule 4: redaction with the role's profile.
        send, masked_in = prepare()

        # Rules 5-7: attempts, records, circuit.
        calls: list[CallRecord] = []
        n = 1
        while True:
            attempt = send(timeout)
            rec = CallRecord.from_provider(attempt.record, role=role, attempt=n)
            calls.append(rec)
            self._ledger.record(rec, ctx.ids)
            self._trace.model_call(ctx.span, rec, masked_in, self._render_out(attempt.value))

            def outcome(
                halt: Halt | None,
                value: V | None = None,
                failure: ProviderFailure | None = None,
            ) -> ModelOutcome[V]:
                return ModelOutcome[V](value=value, calls=tuple(calls), failure=failure, halt=halt)

            f = attempt.failure
            if f is None:
                if adm == _PROBE:
                    self._ledger.close_provider_cap(provider)
                return outcome(None, value=attempt.value)
            if f.kind in _CAP_KINDS:
                self._ledger.trip_provider_cap(f)
                return outcome(self._halt(HaltReason.PROVIDER_SPEND_CAP, role, ctx), failure=f)
            if adm == _PROBE:
                self._ledger.close_provider_cap(provider)
                return outcome(None, failure=f)
            if n == _MAX_ATTEMPTS or not f.retryable:
                return outcome(None, failure=f)
            wait = f.retry_after_s if f.retry_after_s is not None else _backoff_s()
            if wait + _RETRY_MARGIN_S > ctx.budget.remaining():
                return outcome(None, failure=f)
            _sleep(wait)
            next_timeout = ctx.budget.timeout_for(spec.cap_s)
            if next_timeout is None:
                return outcome(None, failure=f)
            timeout = next_timeout
            n = 2

    def _render_out(self, value: BaseModel | None) -> str:
        if value is None:
            return ""
        if isinstance(value, ToolStep):
            payload: JsonValue = {
                "text": value.text,
                "tool_calls": [{"name": c.name, "args": c.args} for c in value.tool_calls],
                "stop_reason": value.stop_reason,
            }
            return _dump_masked(payload, self._redact)
        return _render_out_model(value, self._redact)


def _route[R: Role, A](mapping: Mapping[R, tuple[A, RoleSpec]], role: R) -> tuple[A, RoleSpec]:
    try:
        return mapping[role]
    except KeyError:
        raise ValueError(f"no adapter configured for role {role.value}") from None
