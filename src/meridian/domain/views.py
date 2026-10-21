"""Case and demo view types (AEA-02b; cases.md A-2, AEA-29 plan Appendix A, AEA-30 plan 4.3).

Pure types, no behaviour beyond validation. Field names are the OpenAPI property names of the schema named beside each
class (`docs/ux/03-structure/ui-contracts.openapi.yaml`, read only); the Stage 7 addenda win over DO-4. Where a name
would collide with a domain type of another module it carries a `View` suffix (`CaseSummaryView` vs
`handoff.CaseSummary`, `BriefView` vs `handoff.Brief`, `ChatLineView` vs `state.ChatLine`). Sequences are tuples (the
module convention for frozen models); they serialise as JSON arrays. Imports `common` and `blocks` only.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import Field, JsonValue

from meridian.domain.blocks import Speaker
from meridian.domain.common import ApiErrorCode, CaseState, MeridianModel, Presence, Priority

DueState = Literal["on_time", "due_soon", "overdue", "no_due_time"]
BriefStatus = Literal["ready", "being_written", "failed"]
PromiseStatus = Literal["open", "kept", "missed", "changed"]
ContactKind = Literal["call", "email"]
ContactOutcome = Literal["reached", "no_answer", "left_message"]
AllowedAction = Literal[
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
CaseActionName = Literal[
    "claim", "release", "start", "wait", "resolve", "close_unresolved", "assign", "change_priority"
]


# --- demo views (AEA-30; cases A-2) ---


class StaffingView(MeridianModel):
    """= OpenAPI Staffing."""

    mode: Presence
    label: str
    banner: str | None


class StaffingChange(MeridianModel):
    """= OpenAPI StaffingResponse."""

    mode: Presence
    label: str
    converted_cases: int


class ClockView(MeridianModel):
    """= OpenAPI DemoClock."""

    now: dt.datetime
    label: str
    date_label: str


class ClockAdvanced(MeridianModel):
    """= OpenAPI ClockAdvanceResponse (no date_label)."""

    now: dt.datetime
    label: str
    became_overdue: int


class ResetDone(MeridianModel):
    """= OpenAPI ResetResponse (cases.md section 6)."""

    ok: Literal[True] = True
    open_chats_ended: int
    roles_reset: int
    clock: ClockView


# --- queue and summary ---


class PriorityView(MeridianModel):
    """= OpenAPI Priority."""

    level: Priority
    word: Literal["Safety", "Danger", "Time-sensitive", "Standard", "Routine"]


class QueueRow(MeridianModel):
    """= OpenAPI QueueRow."""

    reference: str
    priority: PriorityView
    reason: str
    customer_display_name: str
    owner: str | None
    created_at: dt.datetime
    due_at: dt.datetime | None
    due_label: str | None
    due_state: DueState
    wake_up_at: dt.datetime | None
    lifecycle: CaseState
    follow_up_short: str | None
    seed: bool
    brief_status: BriefStatus
    queued_at: dt.datetime | None
    age_label: str | None


class QueueView(MeridianModel):
    """= OpenAPI QueueResponse."""

    as_of: dt.datetime
    staffing: StaffingView
    live: tuple[QueueRow, ...]
    needs_my_action: tuple[QueueRow, ...]


class CaseSummaryView(MeridianModel):
    """= OpenAPI CaseSummary (the wire shape; `handoff.CaseSummary` is the domain record)."""

    reference: str
    reason: str
    priority: PriorityView
    lifecycle: CaseState
    owner: str | None
    created_at: dt.datetime
    due_at: dt.datetime | None
    due_label: str | None
    due_state: DueState
    wake_up_at: dt.datetime | None
    promise_status: PromiseStatus
    seed: bool
    version: int
    allowed_actions: tuple[AllowedAction, ...]


# --- case detail ---


class BriefItemView(MeridianModel):
    """= OpenAPI BriefItem (wire: `source_ids`, no `origin`)."""

    text: str
    kind: Literal["fact", "claim", "ai_action", "told_customer", "decision", "contact"]
    source_ids: tuple[str, ...]
    changed: bool


class BriefHeadingView(MeridianModel):
    """= OpenAPI BriefHeading."""

    number: int = Field(ge=1, le=8)
    key: Literal["why", "needs", "know", "says", "ai_did", "told", "decide", "who"]
    title: str
    checked: bool
    items: tuple[BriefItemView, ...]
    trimmed: bool
    trim_note: str | None
    not_generated: bool


class BriefView(MeridianModel):
    """= OpenAPI Brief: always eight headings."""

    status: BriefStatus
    headings: tuple[BriefHeadingView, ...] = Field(min_length=8, max_length=8)


class CaseSource(MeridianModel):
    """= OpenAPI CaseSource."""

    source_id: str
    lookup_log_id: str
    audience: Literal["customer", "staff_only"]
    title: str
    ref: str
    version_date: dt.date | None
    snapshot: dict[str, JsonValue]
    current: dict[str, JsonValue] | None
    changed_since: bool
    changed_note: str | None
    current_unavailable: bool
    version_label: str


class ChatLineView(MeridianModel):
    """= OpenAPI ChatLine (`state.ChatLine` is the in-graph line)."""

    message_id: str
    speaker: Speaker
    at: dt.datetime
    text: str


class Activity(MeridianModel):
    """= OpenAPI Activity."""

    activity_id: str
    kind: ContactKind
    outcome: ContactOutcome
    note: str | None
    at: dt.datetime
    by: str
    label: Literal["Demo: recorded, not sent"]


class PromiseFollowUp(MeridianModel):
    """= OpenAPI PromiseRecord.follow_up."""

    channel: Literal["email", "phone"]
    destination_label: str
    on_record: bool
    window: str | None


class PromiseHistoryItem(MeridianModel):
    """= OpenAPI PromiseRecord.history[]."""

    at: dt.datetime
    text: str
    reason: str


class PromiseRecord(MeridianModel):
    """= OpenAPI PromiseRecord."""

    text: str
    due_at: dt.datetime | None
    due_label: str | None
    policy_row: str
    status: PromiseStatus
    follow_up: PromiseFollowUp | None
    history: tuple[PromiseHistoryItem, ...]


class LiveStateView(MeridianModel):
    """= OpenAPI LiveState."""

    state: Literal["not_live", "queued", "joined", "handed_back", "closed"]
    since: dt.datetime | None
    controller: Literal["ai", "human"]


class CaseIdentityView(MeridianModel):
    """= OpenAPI CaseDetail.identity."""

    status: Literal["not_checked", "code_sent", "verified", "not_verified", "locked"]
    line: str
    demo_note: str


class OtherCase(MeridianModel):
    """= OpenAPI CaseDetail.other_cases[]."""

    reference: str
    status: str


class CaseDetail(MeridianModel):
    """= OpenAPI CaseDetail (no `events` until the UX amendment, AEA-29 AC-23)."""

    case: CaseSummaryView
    promise: PromiseRecord
    brief: BriefView
    identity: CaseIdentityView
    sources: tuple[CaseSource, ...]
    conversation: tuple[ChatLineView, ...]
    activities: tuple[Activity, ...]
    live: LiveStateView
    other_cases: tuple[OtherCase, ...]
    agent_version: str
    as_of: dt.datetime


# --- actions and their results ---


class CaseAction(MeridianModel):
    """= OpenAPI CaseActionRequest. Which optional fields an action needs is the service's rule, not a type rule."""

    action: CaseActionName
    expected_version: int
    reason: str | None = None
    wake_up_at: dt.datetime | None = None
    outcome: str | None = None
    assignee: Literal["riley", "supervisor"] | None = None
    priority: Priority | None = None


class CaseActionRejected(MeridianModel):
    """= OpenAPI ApiError.error (the route adds `request_id`). `details` never carries a rejected value."""

    code: ApiErrorCode
    field: str | None = None
    constraint: str | None = None
    details: dict[str, JsonValue] | None = None


class FollowUpChoice(MeridianModel):
    """= OpenAPI FollowUpRequest."""

    channel: Literal["email", "phone"]
    destination: Literal["on_record", "general"]
    window: Literal["morning", "afternoon", "any"]


class ActivityIn(MeridianModel):
    """= OpenAPI ActivityRequest."""

    kind: ContactKind
    outcome: ContactOutcome
    note: str | None = None
    expected_version: int


class ActivityResult(MeridianModel):
    """= OpenAPI ActivityResponse."""

    activity: Activity
    case: CaseSummaryView


# --- oversight ---


class Alert(MeridianModel):
    """= OpenAPI Alert."""

    type: Literal[
        "p0_p1_created", "unowned", "due_soon", "overdue", "stuck_waiting", "shift_ended_with_queued"
    ]
    case_ref: str | None
    line: str
    at: dt.datetime


class Lane(MeridianModel):
    """= OpenAPI Lane."""

    count: int
    rows: tuple[QueueRow, ...]


class OversightLanes(MeridianModel):
    """= OpenAPI OversightResponse.lanes."""

    p0_p1: Lane
    overdue: Lane
    due_soon: Lane
    unowned: Lane
    stuck_waiting: Lane


class OversightView(MeridianModel):
    """= OpenAPI OversightResponse."""

    as_of: dt.datetime
    demo_now: dt.datetime
    staffing: StaffingView
    alerts: tuple[Alert, ...]
    lanes: OversightLanes
    live_queue_length: int
    new_flags_count: int
