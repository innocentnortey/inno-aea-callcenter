"""Tool definitions, scope, results and the lookup log rows (AEA-02; DO-4 section 5, cases.md 1.2, graph-tools 1).

`ToolKind` and `ToolCallRecord` are defined in `common` and re-exported here (plan 4.0).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Annotated, Literal

from pydantic import Field, JsonValue

from meridian.domain.common import (
    CustomerId,
    LLMFacing,
    MeridianModel,
    PassageId,
    ThreadId,
    ToolErrorCode,
    TurnId,
)
from meridian.domain.common import ToolCallRecord as ToolCallRecord
from meridian.domain.common import ToolKind as ToolKind
from meridian.domain.specialists import AccountCapture, KnowledgeCapture, SchedulingCapture
from meridian.domain.turn import TurnIds


class ToolCallScope(MeridianModel):
    """DO-4 section 5; code binds it, the model never supplies it."""

    ids: TurnIds
    customer_id: CustomerId | None
    shown_slot_ids: frozenset[int]
    now: dt.datetime
    message_id: int


class LookupEntry(MeridianModel):
    tool: str
    record_ids: tuple[str, ...]
    passage_ids: tuple[PassageId, ...]
    result_seen: str
    message_id: int
    turn_id: TurnId


class LookupRow(LookupEntry):
    """cases.md section 1.2 (CAS-38, R-G-8)."""

    id: int
    thread_id: ThreadId


class ToolError(MeridianModel):
    code: ToolErrorCode
    message: str
    retryable: bool


Capture = Annotated[KnowledgeCapture | AccountCapture | SchedulingCapture, Field(discriminator="kind")]


class ToolResult(MeridianModel):
    ok: bool
    for_model: ToolError | JsonValue = Field(union_mode="left_to_right")
    captured: Capture | None
    lookup: LookupEntry
    lookup_written: bool


class ToolDef(MeridianModel):
    name: str
    description: str
    args_model: type[LLMFacing]
    kind: ToolKind
    effect: Literal["read", "write"]
    requires_verified: bool
    executor: Callable[[LLMFacing, ToolCallScope], ToolResult] = Field(exclude=True)
