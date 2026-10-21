"""Handoff, case summary and the eight-heading Brief (AEA-02; DO-4 section 7, cases A-4, R-28).

`HandoffReason`, `Priority`, `Presence`, `CaseState`, `Promise` and `FollowUp` are defined in `common` and re-exported
here (plan 4.0). `Promise` has fields only: no text validator (GRC-2).
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from meridian.domain.actions import CompletedAction
from meridian.domain.common import CaseRef, LLMFacing, MeridianModel, SafetyKind, ThreadId, TurnId
from meridian.domain.common import CaseState as CaseState
from meridian.domain.common import FollowUp as FollowUp
from meridian.domain.common import HandoffReason as HandoffReason
from meridian.domain.common import Presence as Presence
from meridian.domain.common import Priority as Priority
from meridian.domain.common import Promise as Promise
from meridian.domain.identity import IdentityState
from meridian.domain.specialists import ChangeRequestDraft


class CaseSummary(MeridianModel):
    """DO-4 section 7 + cases A-4."""

    case_ref: CaseRef
    reason: HandoffReason
    priority: Priority
    state: CaseState
    created_at: dt.datetime
    promise: Promise
    followup: FollowUp | None
    version: int
    seed: bool = False
    due_at: dt.datetime | None  # the CASE due (cases A-4); required, may be None


BRIEF_TITLES: tuple[str, ...] = (
    "Why this came to you",
    "What the customer needs",
    "What we know for sure",
    "What the customer says (not checked)",
    "What the AI did",
    "What we told the customer",
    "What you need to decide",
    "Who they are and how to reach them",
)
BRIEF_KEYS: tuple[str, ...] = ("why", "needs", "know", "says", "ai_did", "told", "decide", "who")
BRIEF_ORIGINS: tuple[str, ...] = (
    "state",
    "extraction",
    "state",
    "extraction",
    "state",
    "state",
    "extraction",
    "state",
)


class SourceRef(MeridianModel):
    kind: Literal["lookup_log", "message", "action", "policy_row", "rule"]
    ref: str


class BriefItem(MeridianModel):
    text: str
    kind: Literal["fact", "claim", "ai_action", "told_customer", "decision", "contact"]
    sources: tuple[SourceRef, ...]  # serialised as the wire's `source_ids` by the route (AEA-45), not here
    changed: bool


class BriefHeading(MeridianModel):
    number: int = Field(ge=1, le=8)
    key: Literal["why", "needs", "know", "says", "ai_did", "told", "decide", "who"]
    title: str
    origin: Literal["state", "extraction"]
    checked: bool
    items: tuple[BriefItem, ...]
    trimmed: bool
    trim_note: str | None
    not_generated: bool


class Brief(MeridianModel):
    case_ref: CaseRef
    thread_id: ThreadId
    assembled_at: dt.datetime
    status: Literal["ready", "being_written", "failed"]
    headings: tuple[BriefHeading, ...]

    @model_validator(mode="after")
    def _fixed_shape(self) -> Brief:
        if len(self.headings) != 8:
            raise PydanticCustomError("brief_shape", "a brief has exactly 8 headings")
        for index, heading in enumerate(self.headings):
            if heading.number != index + 1:
                raise PydanticCustomError("brief_shape", "headings are numbered 1 to 8 in order")
            if heading.title != BRIEF_TITLES[index]:
                raise PydanticCustomError(
                    "brief_shape",
                    "heading {number} title must be BRIEF_TITLES[{index}]",
                    {"number": index + 1, "index": index},
                )
            if heading.key != BRIEF_KEYS[index]:
                raise PydanticCustomError(
                    "brief_shape",
                    "heading {number} key must be BRIEF_KEYS[{index}]",
                    {"number": index + 1, "index": index},
                )
            if heading.origin != BRIEF_ORIGINS[index]:
                raise PydanticCustomError(
                    "brief_shape",
                    "heading {number} origin must be BRIEF_ORIGINS[{index}]",
                    {"number": index + 1, "index": index},
                )
            if index == 3 and heading.checked:
                raise PydanticCustomError("brief_shape", "heading 4 is never checked")
            if heading.not_generated and index not in (1, 3, 6):
                raise PydanticCustomError("brief_shape", "only headings 2, 4 and 7 can be not generated")
        return self


class Quote(LLMFacing):
    message_id: int
    text: str = Field(max_length=300)


class BriefExtraction(LLMFacing):
    needs: list[Quote] = Field(min_length=1, max_length=2)
    claims: list[Quote] = Field(max_length=5)
    open_decision: str = Field(max_length=200)


class HandoffRequest(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    reason: HandoffReason
    priority: Priority
    rule_id: str
    trigger: Literal["gate", "escalation", "con4", "safety"]
    identity: IdentityState
    change_request: ChangeRequestDraft | None = None
    safety_kind: SafetyKind | None = None


class HandoffResult(MeridianModel):
    case: CaseSummary
    created: bool
    action: CompletedAction
    alert: Literal["supervisor_now"] | None
