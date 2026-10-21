"""Model ports: request and answer shapes and the three model Protocols (AEA-02; DO-4 section 12, models.md 1).

`Role`, `ProviderName`, `ProviderCall` and `CallRecord` are defined in `domain.common` (so domain results can hold
them without importing a port) and re-exported here (plan 4.0).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, Literal, Protocol

from pydantic import BaseModel, Field, JsonValue

from meridian.domain.common import CallRecord as CallRecord
from meridian.domain.common import MeridianModel, ProviderFailure, ProviderName
from meridian.domain.common import ProviderCall as ProviderCall
from meridian.domain.common import Role as Role

ChoiceRole = Literal[Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK]
StructuredRole = Literal[Role.RESPONDER, Role.BRIEF]
ToolRole = Literal[Role.SPECIALIST]
ProviderTurn = JsonValue  # decision D-6: one provider message object, as in ProviderMessages.items (MOD-17)


@dataclass(frozen=True)
class TokenPrice:
    """models.md section 1 (R-G-5): US dollars per million tokens."""

    input: float
    output: float
    cache_write_5m: float
    cache_read: float


class ChoiceField(MeridianModel):
    name: str
    instructions: str
    options: dict[str, str] = Field(max_length=255)


class ChoiceRequest(MeridianModel):
    system: str
    state: dict[str, JsonValue]
    fields: tuple[ChoiceField, ...]


class ChoiceAnswer(MeridianModel):
    choices: dict[str, str]
    probabilities: dict[str, dict[str, float]] | None


class StructuredRequest[T: BaseModel](MeridianModel):
    system_prefix: str
    system_dynamic: str
    user: str
    output_model: type[T]
    max_tokens: int
    effort: Literal["low", "medium", "high"] | None


class ToolSchema(MeridianModel):
    name: str
    description: str
    input_schema: dict[str, JsonValue]
    strict: bool = True


class ToolCall(MeridianModel):
    id: str
    name: str
    args: dict[str, JsonValue] | None


class ProviderMessages(MeridianModel):
    provider: ProviderName
    model: str
    items: tuple[JsonValue, ...]


class ToolStepRequest(MeridianModel):
    system_prefix: str
    system_dynamic: str
    messages: ProviderMessages
    tools: tuple[ToolSchema, ...]
    max_tokens: int
    effort: Literal["low", "medium", "high"] | None


class ToolStep(MeridianModel):
    text: str
    tool_calls: tuple[ToolCall, ...]
    raw: ProviderTurn
    stop_reason: str | None


class Attempt[T: BaseModel](MeridianModel):
    value: T | None
    record: ProviderCall  # CHANGED by models.md section 1: a ProviderCall, not a CallRecord
    failure: ProviderFailure | None


class ChoiceModel(Protocol):
    provider: ClassVar[ProviderName]

    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...


class StructuredModel(Protocol):
    provider: ClassVar[ProviderName]

    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...


class ToolCallingModel(Protocol):
    provider: ClassVar[ProviderName]

    def start(self, user: str) -> ProviderMessages: ...

    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...

    def append(
        self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]
    ) -> ProviderMessages: ...


class ToolTranscript(Protocol):
    """graph-tools section 2."""

    def start(self, user: str) -> ProviderMessages: ...

    def append(
        self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]
    ) -> ProviderMessages: ...
