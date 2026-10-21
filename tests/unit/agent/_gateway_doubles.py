"""Test doubles and builders for the AEA-20 gateway tests (frozen with test_gateway.py).

Scripted model adapters honouring the DO-4 port signatures, a recording ledger and trace sink, a fake clock, and
seed builders. Every sensitive-looking value is assembled at run time; nothing here is a real person, number or key.
"""

from __future__ import annotations

import datetime as dt
import secrets
import threading
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar, Literal, cast

from pydantic import BaseModel

from meridian.agent.gateway import ModelGateway, ModelOutcome
from meridian.config import RoleSpec
from meridian.domain.common import (
    CallRecord,
    LLMFacing,
    ProviderFailure,
    ProviderFailureKind,
    ProviderName,
    RequestId,
    ThreadId,
    TurnId,
)
from meridian.domain.turn import SpanHandle, TurnBudget, TurnContext, TurnIds
from meridian.policy.limits import Limits
from meridian.ports.models import (
    Attempt,
    ChoiceAnswer,
    ChoiceField,
    ChoiceRequest,
    ProviderCall,
    ProviderMessages,
    Role,
    StructuredRequest,
    ToolStep,
    ToolStepRequest,
)
from meridian.privacy.redact import RedactionProfile, redact

# --------------------------------------------------------------------------------------------------------------
# Seeds (assembled at run time; never literals in test names)
# --------------------------------------------------------------------------------------------------------------


def wp2_phone() -> str:
    return "-".join(("512", "555", "01" + "02"))


def wp2_line() -> str:
    return f"This is Omar Patel, {wp2_phone()}, customer MHC-10002, invoice INV-204411"


def card_like() -> str:
    return " ".join(str(n) for n in (5005, 1234, 9876, 4321))


def six_digit_code() -> str:
    return "".join(str(d) for d in (9, 1, 4, 2, 7, 6))


def email_seed() -> str:
    return "omar.p" + "@" + "example.test"


def street_seed() -> str:
    return "4410 Bluebonnet Ln"


def key_sentinel() -> str:
    return "sk-test-" + secrets.token_hex(8)


# --------------------------------------------------------------------------------------------------------------
# Clock and budget
# --------------------------------------------------------------------------------------------------------------


class FakeAdmission(StrEnum):
    """Mirrors models.md section 6 CallAdmission; proves a StrEnum return satisfies a string comparison."""

    ALLOW = "allow"
    PROBE = "probe"
    REFUSE = "refuse"


@dataclass
class FakeClock:
    t: float = 1_000.0
    waits: list[tuple[float, float]] = field(default_factory=list)

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.waits.append((self.t, seconds))
        self.t += seconds

    def advance(self, seconds: float) -> None:
        self.t += seconds


@dataclass(frozen=True)
class ClockedBudget(TurnBudget):
    """A TurnBudget whose remaining() reads the fake clock (the base timeout_for calls self.remaining())."""

    clock: FakeClock = field(default_factory=FakeClock, compare=False, repr=False)

    def remaining(self) -> float:
        return max(0.0, self.deadline - self.clock.now())


def budget(clock: FakeClock, seconds_left: float) -> ClockedBudget:
    return ClockedBudget(started=clock.now(), deadline=clock.now() + seconds_left, clock=clock)


def context(b: TurnBudget, *, turn_id: TurnId | None = None) -> TurnContext:
    tid = turn_id or TurnId(str(uuid.uuid4()))
    return TurnContext(
        ids=TurnIds(
            thread_id=ThreadId(str(uuid.uuid4())),
            turn_id=tid,
            request_id=RequestId(str(uuid.uuid4())),
            run_tag="live",
            run_id=None,
            agent_version="test",
        ),
        budget=b,
        now=dt.datetime(2026, 10, 21, 15, 0, tzinfo=dt.UTC),
        demo_session="demo-test",
        span=SpanHandle(turn_id=tid, trace_id="0" * 32),
    )


def spec(
    *,
    cap_s: float,
    redaction: RedactionProfile,
    model: str = "model-test",
    max_tokens: int = 500,
    effort: Literal["low", "medium", "high"] | None = "low",
) -> RoleSpec:
    return RoleSpec(model=model, effort=effort, cap_s=cap_s, max_tokens=max_tokens, redaction=redaction)


# --------------------------------------------------------------------------------------------------------------
# Provider results
# --------------------------------------------------------------------------------------------------------------

_RETRYABLE_BY_DEFAULT = frozenset(
    {
        ProviderFailureKind.TIMEOUT,
        ProviderFailureKind.CONNECTION,
        ProviderFailureKind.RATE_LIMITED,
        ProviderFailureKind.OVERLOADED,
        ProviderFailureKind.SERVER,
    }
)


def failure(
    kind: ProviderFailureKind,
    provider: ProviderName = "anthropic",
    *,
    retry_after_s: float | None = None,
    retryable: bool | None = None,
) -> ProviderFailure:
    return ProviderFailure(
        kind=kind,
        provider=provider,
        http_status=None,
        retry_after_s=retry_after_s,
        retryable=(kind in _RETRYABLE_BY_DEFAULT) if retryable is None else retryable,
        provider_request_id="req-test",
    )


def provider_call(provider: ProviderName, model: str, fail: ProviderFailure | None) -> ProviderCall:
    return ProviderCall(
        provider=provider,
        model=model,
        latency_ms=120,
        input_tokens=40,
        output_tokens=12,
        cache_read_tokens=0,
        cache_write_tokens=0,
        thinking_tokens=0,
        cost_usd=0.0 if fail else 0.0002,
        cost_source="price_table",
        status="error" if fail else "ok",
        failure=fail,
        provider_request_id="req-test",
        stop_reason=None if fail else "end_turn",
    )


class Reply(LLMFacing):
    """The structured output model used in tests."""

    text: str


# --------------------------------------------------------------------------------------------------------------
# Scripted adapters
# --------------------------------------------------------------------------------------------------------------


class _Scripted:
    """Shared bookkeeping. `script` items are popped from the front: a ProviderFailure fails the attempt, None
    succeeds; an empty script succeeds."""

    provider: ClassVar[ProviderName]

    def __init__(
        self, model: str, script: list[ProviderFailure | None] | None = None, api_key: str | None = None
    ) -> None:
        self.model = model
        self.script: list[ProviderFailure | None] = list(script or [])
        self.requests: list[Any] = []
        self.timeouts: list[float] = []
        self.calls_returned: list[ProviderCall] = []
        self.api_key = api_key or key_sentinel()
        self._lock = threading.Lock()

    def _begin(self, req: Any, timeout_s: float) -> tuple[ProviderFailure | None, ProviderCall]:
        with self._lock:
            self.requests.append(req)
            self.timeouts.append(timeout_s)
            fail = self.script.pop(0) if self.script else None
            call = provider_call(self.provider, self.model, fail)
            self.calls_returned.append(call)
        return fail, call


class JevChoice(_Scripted):
    provider: ClassVar[ProviderName] = "openrouter_jev"

    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]:
        fail, call = self._begin(req, timeout_s)
        if fail is not None:
            return Attempt[ChoiceAnswer](value=None, record=call, failure=fail)
        answer = ChoiceAnswer(choices={f.name: next(iter(f.options)) for f in req.fields}, probabilities=None)
        return Attempt[ChoiceAnswer](value=answer, record=call, failure=None)


class SonnetChoice(JevChoice):
    provider: ClassVar[ProviderName] = "anthropic"


class SonnetStructured(_Scripted):
    provider: ClassVar[ProviderName] = "anthropic"

    def __init__(
        self,
        model: str,
        script: list[ProviderFailure | None] | None = None,
        api_key: str | None = None,
        next_value: BaseModel | None = None,
    ) -> None:
        super().__init__(model, script, api_key)
        self.next_value: BaseModel = next_value if next_value is not None else Reply(text="ok")

    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]:
        fail, call = self._begin(req, timeout_s)
        if fail is not None:
            return Attempt[T](value=None, record=call, failure=fail)
        return Attempt[T](value=cast(T, self.next_value), record=call, failure=None)


class SonnetTools(_Scripted):
    provider: ClassVar[ProviderName] = "anthropic"

    def start(self, user: str) -> ProviderMessages:
        return ProviderMessages(
            provider="anthropic", model=self.model, items=({"role": "user", "content": user},)
        )

    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]:
        fail, call = self._begin(req, timeout_s)
        if fail is not None:
            return Attempt[ToolStep](value=None, record=call, failure=fail)
        step = ToolStep(text="checking", tool_calls=(), raw={"role": "assistant"}, stop_reason="end_turn")
        return Attempt[ToolStep](value=step, record=call, failure=None)

    def append(self, messages: ProviderMessages, step: ToolStep, results: Any) -> ProviderMessages:
        return messages


# --------------------------------------------------------------------------------------------------------------
# Ledger and sink
# --------------------------------------------------------------------------------------------------------------


@dataclass
class RecordingLedger:
    """The four LedgerService methods the gateway may call (models.md section 6), plus the two it must never call."""

    admissions: list[FakeAdmission] = field(default_factory=list)
    admitted: list[str] = field(default_factory=list)
    records: list[tuple[CallRecord, TurnIds]] = field(default_factory=list)
    trips: list[ProviderFailure] = field(default_factory=list)
    closes: list[str] = field(default_factory=list)
    allow_turn_calls: int = 0
    models_disabled_calls: int = 0

    def admit_call(self, provider: ProviderName) -> FakeAdmission:
        self.admitted.append(provider)
        return self.admissions.pop(0) if self.admissions else FakeAdmission.ALLOW

    def record(self, call: CallRecord, ids: TurnIds) -> None:
        self.records.append((call, ids))

    def trip_provider_cap(self, failure: ProviderFailure) -> None:
        self.trips.append(failure)

    def close_provider_cap(self, provider: ProviderName) -> None:
        self.closes.append(provider)

    def allow_turn(self) -> bool:
        self.allow_turn_calls += 1
        return True

    def models_disabled(self) -> bool:
        self.models_disabled_calls += 1
        return False


@dataclass
class RecordingSink:
    """Satisfies TraceSink; keeps every model_call."""

    model_calls: list[tuple[SpanHandle, CallRecord, str, str]] = field(default_factory=list)

    @contextmanager
    def turn(self, ids: TurnIds) -> Iterator[SpanHandle]:
        yield SpanHandle(turn_id=ids.turn_id, trace_id="0" * 32)

    def model_call(
        self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str
    ) -> None:
        self.model_calls.append((parent, record, masked_input, masked_output))

    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None:
        return None

    def export_status(self, turn: SpanHandle) -> Literal["off", "sent", "failed"]:
        return "off"


# --------------------------------------------------------------------------------------------------------------
# Gateway builder
# --------------------------------------------------------------------------------------------------------------


@dataclass
class Doubles:
    planner: JevChoice
    classifier: JevChoice
    fallback: SonnetChoice
    responder: SonnetStructured
    brief: SonnetStructured
    specialist: SonnetTools
    ledger: RecordingLedger
    sink: RecordingSink
    specs: dict[Role, RoleSpec]


def default_specs() -> dict[Role, RoleSpec]:
    """The AEA-02 code defaults, built locally so these doubles do not depend on default_model_settings()."""
    return {
        Role.PLANNER: spec(cap_s=3.0, redaction=RedactionProfile.JEV, effort=None),
        Role.CLASSIFIER: spec(cap_s=3.0, redaction=RedactionProfile.JEV, effort=None),
        Role.PLANNER_FALLBACK: spec(cap_s=8.0, redaction=RedactionProfile.SONNET),
        Role.RESPONDER: spec(cap_s=12.0, redaction=RedactionProfile.SONNET),
        Role.BRIEF: spec(cap_s=12.0, redaction=RedactionProfile.SONNET),
        Role.SPECIALIST: spec(cap_s=8.0, redaction=RedactionProfile.SONNET),
    }


def default_doubles(
    *,
    ledger: RecordingLedger | None = None,
    sink: RecordingSink | None = None,
    specs: Mapping[Role, RoleSpec] | None = None,
    **adapters: Any,
) -> Doubles:
    """Adapter keyword names: planner, classifier, fallback, responder, brief, specialist."""
    return Doubles(
        planner=adapters.get("planner") or JevChoice("jev-planner"),
        classifier=adapters.get("classifier") or JevChoice("jev-classifier"),
        fallback=adapters.get("fallback") or SonnetChoice("sonnet-fallback"),
        responder=adapters.get("responder") or SonnetStructured("sonnet-responder"),
        brief=adapters.get("brief") or SonnetStructured("sonnet-brief"),
        specialist=adapters.get("specialist") or SonnetTools("sonnet-specialist"),
        ledger=ledger or RecordingLedger(),
        sink=sink or RecordingSink(),
        specs={**default_specs(), **(specs or {})},
    )


def gateway_kwargs(d: Doubles, limits: Limits | None = None) -> dict[str, Any]:
    """The constructor keyword arguments for a well-formed gateway; tests override single entries."""
    return {
        "choice": {
            Role.PLANNER: (d.planner, d.specs[Role.PLANNER]),
            Role.CLASSIFIER: (d.classifier, d.specs[Role.CLASSIFIER]),
            Role.PLANNER_FALLBACK: (d.fallback, d.specs[Role.PLANNER_FALLBACK]),
        },
        "structured": {
            Role.RESPONDER: (d.responder, d.specs[Role.RESPONDER]),
            Role.BRIEF: (d.brief, d.specs[Role.BRIEF]),
        },
        "tools": {Role.SPECIALIST: (d.specialist, d.specs[Role.SPECIALIST])},
        "ledger": d.ledger,
        "trace": d.sink,
        "redact": redact,
        "limits": limits or Limits(),
    }


def build_gateway(
    *,
    ledger: RecordingLedger | None = None,
    sink: RecordingSink | None = None,
    limits: Limits | None = None,
    specs: Mapping[Role, RoleSpec] | None = None,
    **adapters: Any,
) -> tuple[ModelGateway, Doubles]:
    d = default_doubles(ledger=ledger, sink=sink, specs=specs, **adapters)
    return ModelGateway(**gateway_kwargs(d, limits)), d


# --------------------------------------------------------------------------------------------------------------
# Request builders and a role dispatcher
# --------------------------------------------------------------------------------------------------------------


def choice_request(text: str, *, instructions: str = "Pick one.") -> ChoiceRequest:
    return ChoiceRequest(
        system=text,
        state={"recent_chat": [text], "new_message": "hello"},
        fields=(
            ChoiceField(
                name="topic", instructions=instructions, options={"billing": "Billing", "other": "Other"}
            ),
        ),
    )


def structured_request(
    user: str, *, system_prefix: str = "PREFIX", system_dynamic: str = "DYNAMIC"
) -> StructuredRequest[Reply]:
    return StructuredRequest[Reply](
        system_prefix=system_prefix,
        system_dynamic=system_dynamic,
        user=user,
        output_model=Reply,
        max_tokens=9999,
        effort=None,
    )


def tool_request(
    system_dynamic: str, *, items: tuple[Any, ...] = ({"role": "user", "content": "hello"},)
) -> ToolStepRequest:
    return ToolStepRequest(
        system_prefix="PREFIX",
        system_dynamic=system_dynamic,
        messages=ProviderMessages(provider="anthropic", model="sonnet-specialist", items=items),
        tools=(),
        max_tokens=9999,
        effort=None,
    )


def call_role(gw: ModelGateway, role: Role, ctx: TurnContext, text: str = "hello") -> ModelOutcome[Any]:
    """Call the gateway method that serves `role`, with `text` in the request's main text field."""
    g: Any = gw
    if role in (Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK):
        out: ModelOutcome[Any] = g.choose(role, choice_request(text), ctx)
    elif role in (Role.RESPONDER, Role.BRIEF):
        out = g.structured(role, structured_request(text), ctx)
    else:
        out = g.tool_step(role, tool_request(text), ctx)
    return out
