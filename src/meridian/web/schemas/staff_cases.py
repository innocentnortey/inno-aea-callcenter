"""Wire shapes for CON-11…13 and CON-15…17 (OpenAPI field names; times in America/Chicago) and the CON-13 result
line (stage7/staff.md section 6). AEA-45."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from types import MappingProxyType
from typing import Annotated, Any, Final, Literal
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PlainSerializer, StrictInt, field_validator
from pydantic_core import PydanticCustomError

from meridian.domain.staff import STAFF_PERSONAS, StaffActor, StaffRole
from meridian.domain.views import CaseActionName

WIRE_ZONE: Final = ZoneInfo("America/Chicago")  # UI_CONTRACTS Conventions: times in America/Chicago
FLAG_TEXT_MAX_CHARS: Final = 2000  # staff.md section 6 (STF-10)
TEXT_TOO_LONG: Final = "at most 2000 characters"
REFERENCE_CONSTRAINT: Final = "must match ^MHC-C-[0-9]{4}$"
RESULT_RELEASED: Final = "Released back to Unassigned."  # staff.md section 6 proposal
_WEEKDAYS: Final = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS: Final = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def wire_time(value: datetime) -> str:
    """The same instant, written with its America/Chicago offset."""
    return value.astimezone(WIRE_ZONE).isoformat()


WireTime = Annotated[AwareDatetime, PlainSerializer(wire_time, return_type=str, when_used="json")]

AllowedActionName = Literal[
    "claim",
    "claim_and_join",
    "release",
    "start",
    "wait",
    "resolve",
    "close_unresolved",
    "assign",
    "change_priority",
    "join_chat",
    "send_live_message",
    "hand_back",
    "close_chat",
    "log_call",
    "log_email",
    "flag",
]
Lifecycle = Literal[
    "live_queued", "unassigned", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved"
]
DueStateName = Literal["on_time", "due_soon", "overdue", "no_due_time"]
BriefStatusName = Literal["ready", "being_written", "failed"]
PromiseStatusName = Literal["open", "kept", "missed", "changed"]


# -- requests ----------------------------------------------------------------------------------------------------
class _WireIn(BaseModel):
    model_config = ConfigDict(
        extra="ignore", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
    )


def _blank_is_none(value: str | None) -> str | None:  # runs after stripping
    return None if value is None or value == "" else value


def _capped_text(value: str | None) -> str | None:
    value = _blank_is_none(value)
    if value is not None and len(value) > FLAG_TEXT_MAX_CHARS:
        raise PydanticCustomError("text_too_long", TEXT_TOO_LONG)
    return value


class CaseActionRequest(_WireIn):
    action: CaseActionName
    expected_version: StrictInt
    reason: str | None = None
    wake_up_at: AwareDatetime | None = None
    outcome: str | None = None
    assignee: Literal["riley", "supervisor"] | None = None
    priority: Literal["P0", "P1", "P2", "P3", "P4"] | None = None

    @field_validator("reason", "outcome", mode="after")
    @classmethod
    def _texts(cls, value: str | None) -> str | None:
        return _blank_is_none(value)


class ActivityRequest(_WireIn):
    kind: Literal["call", "email"]
    outcome: Literal["reached", "no_answer", "left_message"]
    note: str | None = None
    expected_version: StrictInt

    @field_validator("note", mode="after")
    @classmethod
    def _note(cls, value: str | None) -> str | None:
        return _blank_is_none(value)


class FlagRequest(_WireIn):
    case_ref: str
    target: Literal["answer", "brief", "escalation"]
    message_id: str | None = None
    note: str | None = None
    reason: str | None = None

    @field_validator("note", "reason", mode="after")
    @classmethod
    def _texts(cls, value: str | None) -> str | None:
        return _capped_text(value)


class FlagReviewRequest(_WireIn):
    status: Literal["reviewed"]
    note: str | None = None

    @field_validator("note", mode="after")
    @classmethod
    def _note(cls, value: str | None) -> str | None:
        return _capped_text(value)


# -- responses ---------------------------------------------------------------------------------------------------
class _WireOut(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True, frozen=True)


class StaffingOut(_WireOut):
    mode: Literal["nobody_online", "simulated_on_shift"]
    label: str
    banner: str | None


class PriorityOut(_WireOut):
    level: Literal["P0", "P1", "P2", "P3", "P4"]
    word: Literal["Safety", "Danger", "Time-sensitive", "Standard", "Routine"]


class QueueRowOut(_WireOut):
    reference: str
    priority: PriorityOut
    reason: str
    customer_display_name: str
    owner: str | None
    created_at: WireTime
    due_at: WireTime | None
    due_label: str | None
    due_state: DueStateName
    wake_up_at: WireTime | None
    lifecycle: Lifecycle
    follow_up_short: str | None
    seed: bool
    brief_status: BriefStatusName
    queued_at: WireTime | None
    age_label: str | None


class QueueResponse(_WireOut):
    as_of: WireTime
    staffing: StaffingOut
    live: list[QueueRowOut]
    needs_my_action: list[QueueRowOut]


class CaseSummaryOut(_WireOut):
    reference: str
    reason: str
    priority: PriorityOut
    lifecycle: Lifecycle
    owner: str | None
    created_at: WireTime
    due_at: WireTime | None
    due_label: str | None
    due_state: DueStateName
    wake_up_at: WireTime | None
    promise_status: PromiseStatusName
    seed: bool
    version: int
    allowed_actions: list[AllowedActionName]


class PromiseFollowUpOut(_WireOut):
    channel: Literal["email", "phone"]
    destination_label: str
    on_record: bool
    window: str | None


class PromiseHistoryItemOut(_WireOut):
    at: WireTime
    text: str
    reason: str


class PromiseRecordOut(_WireOut):
    text: str
    due_at: WireTime | None
    due_label: str | None
    policy_row: str
    status: PromiseStatusName
    follow_up: PromiseFollowUpOut | None
    history: list[PromiseHistoryItemOut]


class BriefItemOut(_WireOut):
    text: str
    kind: Literal["fact", "claim", "ai_action", "told_customer", "decision", "contact"]
    source_ids: list[str]
    changed: bool


class BriefHeadingOut(_WireOut):
    number: int = Field(ge=1, le=8)
    key: Literal["why", "needs", "know", "says", "ai_did", "told", "decide", "who"]
    title: str
    checked: bool
    items: list[BriefItemOut]
    trimmed: bool
    trim_note: str | None
    not_generated: bool


class BriefOut(_WireOut):
    status: BriefStatusName
    headings: list[BriefHeadingOut] = Field(min_length=8, max_length=8)


class CaseIdentityOut(_WireOut):
    status: Literal["not_checked", "code_sent", "verified", "not_verified", "locked"]
    line: str
    demo_note: str


class CaseSourceOut(_WireOut):
    source_id: str
    lookup_log_id: str
    audience: Literal["customer", "staff_only"]
    title: str
    ref: str
    version_date: date | None
    snapshot: dict[str, Any]
    current: dict[str, Any] | None
    changed_since: bool
    changed_note: str | None
    current_unavailable: bool
    version_label: str


class SpeakerOut(_WireOut):
    kind: Literal["assistant", "customer", "representative", "event"]
    display_name: str | None


class ChatLineOut(_WireOut):
    message_id: str
    speaker: SpeakerOut
    at: WireTime
    text: str


class ActivityOut(_WireOut):
    activity_id: str
    kind: Literal["call", "email"]
    outcome: Literal["reached", "no_answer", "left_message"]
    note: str | None
    at: WireTime
    by: str
    label: Literal["Demo: recorded, not sent"]


class LiveStateOut(_WireOut):
    state: Literal["not_live", "queued", "joined", "handed_back", "closed"]
    since: WireTime | None
    controller: Literal["ai", "human"]


class OtherCaseOut(_WireOut):
    reference: str
    status: str


class CaseDetailOut(_WireOut):
    case: CaseSummaryOut
    promise: PromiseRecordOut
    brief: BriefOut
    identity: CaseIdentityOut
    sources: list[CaseSourceOut]
    conversation: list[ChatLineOut]
    activities: list[ActivityOut]
    live: LiveStateOut
    other_cases: list[OtherCaseOut]
    agent_version: str
    as_of: WireTime


class CaseActionResponse(_WireOut):
    case: CaseSummaryOut
    result_line: str


class ActivityResponse(_WireOut):
    activity: ActivityOut
    case: CaseSummaryOut


class FlagOut(_WireOut):
    flag_id: str
    target: Literal["answer", "brief", "escalation"]
    reason: str | None
    case_ref: str
    message_id: str | None
    note: str | None
    flagged_by: str
    at: WireTime
    status: Literal["new", "reviewed"]
    reviewed_by: str | None
    reviewed_note: str | None


class FlagsResponse(_WireOut):
    as_of: WireTime
    flags: list[FlagOut]


class AlertOut(_WireOut):
    type: Literal[
        "p0_p1_created", "unowned", "due_soon", "overdue", "stuck_waiting", "shift_ended_with_queued"
    ]
    case_ref: str | None
    line: str
    at: WireTime


class LaneOut(_WireOut):
    count: int
    rows: list[QueueRowOut]


class OversightLanesOut(_WireOut):
    p0_p1: LaneOut
    overdue: LaneOut
    due_soon: LaneOut
    unowned: LaneOut
    stuck_waiting: LaneOut


class OversightResponse(_WireOut):
    as_of: WireTime
    demo_now: WireTime
    staffing: StaffingOut
    alerts: list[AlertOut]
    lanes: OversightLanesOut
    live_queue_length: int
    new_flags_count: int


# -- result line (staff.md section 6) ----------------------------------------------------------------------------
_ROLE_BY_NAME: Final[Mapping[str, StaffRole]] = MappingProxyType(
    {p.name: r for r, p in STAFF_PERSONAS.items()}
)


def chicago_label(moment: datetime) -> str:
    """'Mon Oct 19 · 9:00 am' in America/Chicago (staff.md section 6)."""
    local = moment.astimezone(WIRE_ZONE)
    hour12 = local.hour % 12 or 12
    return (
        f"{_WEEKDAYS[local.weekday()]} {_MONTHS[local.month - 1]} {local.day} · "
        f"{hour12}:{local.minute:02d} {'am' if local.hour < 12 else 'pm'}"
    )


def result_line(action: CaseActionName, case: CaseSummaryOut, actor: StaffActor) -> str:
    """The one composed sentence the console shows after a case action."""
    if action == "claim":
        return f"Claimed · {actor.signature}"
    if action == "wait":
        if case.wake_up_at is None:
            raise RuntimeError("wait result has no wake_up_at")
        return f"Waiting until {chicago_label(case.wake_up_at)}"
    if action == "resolve":
        return f"{case.reference} resolved."
    if action == "assign":
        role = _ROLE_BY_NAME.get(case.owner) if case.owner is not None else None
        if role is None:
            raise RuntimeError("assign result has no known owner")
        return f"Assigned to {STAFF_PERSONAS[role].signature}."
    if action == "change_priority":
        return f"Priority is now {case.priority.level} · {case.priority.word}."
    if action == "release":
        return RESULT_RELEASED
    if action == "start":
        return f"In progress · {actor.signature}"
    return f"{case.reference} closed unresolved."
