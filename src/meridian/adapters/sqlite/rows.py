"""Row models the two shared repositories return, plus the stream-key helpers (AEA-10; cases.md 1.2, DO-4 section 13).

Datetimes are tz-aware UTC (read back through ``parse_wall``). Nothing here touches the database.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Literal, NewType

from pydantic import Field, JsonValue

from meridian.adapters.sqlite.db import format_wall, parse_wall
from meridian.domain.common import (
    CaseRef,
    CustomerId,
    EventId,
    HandoffReason,
    InvoiceId,
    MeridianModel,
    Priority,
    RequestId,
    ThreadId,
    TurnId,
)
from meridian.domain.handoff import Promise
from meridian.domain.staff import DemoRole, StaffRole
from meridian.domain.state import Controller
from meridian.domain.turn import ExportStatus, PlannerTrace, TurnRecord

StreamKey = NewType("StreamKey", str)  # DO-4 section 13 names it, nothing sketches it; AEA-10 owns `events`
CASE_STREAM_PREFIX = "case:"


def thread_stream(thread_id: ThreadId) -> StreamKey:
    """The thread form of a stream key: the bare thread id."""
    return StreamKey(str(thread_id))


def case_stream(case_ref: CaseRef) -> StreamKey:
    """The case form of a stream key: ``case:<CaseRef>`` (staff.md section 7)."""
    return StreamKey(CASE_STREAM_PREFIX + str(case_ref))


def _j(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _dt(text: str | None) -> datetime | None:
    return None if text is None else parse_wall(text)


def _d(text: str | None) -> date | None:
    return None if text is None else date.fromisoformat(text)


def _w(value: datetime | None) -> str | None:
    return None if value is None else format_wall(value)


class ConversationRow(MeridianModel):
    thread_id: ThreadId
    demo_session: str
    run_tag: Literal["live", "eval", "load", "seed"]
    run_id: str | None = None
    agent_version: str
    started_at: datetime  # demo clock
    started_wall_at: datetime | None = None  # wall clock, UTC
    staffing_at_start: Literal["nobody_online", "simulated_on_shift"] | None = None
    outcome: Literal["ai_resolved", "handed_off", "safety_reply", "abandoned", "open"] = "open"
    ended_wall_at: datetime | None = None
    last_customer_wall_at: datetime | None = None
    controller: Controller = Field(default_factory=lambda: Controller(kind="ai"))
    live_state: Literal["not_live", "queued", "joined", "handed_back", "closed"] = "not_live"
    live_since: datetime | None = None


class EndedThread(MeridianModel):
    """cases.md 1.2, verbatim fields."""

    thread_id: ThreadId
    demo_session: str
    ended_wall_at: datetime
    reason: str
    reset_id: str | None


class Cleared(MeridianModel):
    """cases.md 1.2, verbatim fields."""

    open_threads: tuple[ThreadId, ...]
    case_streams: tuple[CaseRef, ...]
    roles_reset: int
    rows_cleared: dict[str, int]


class MessageRow(MeridianModel):
    id: int
    thread_id: ThreadId
    role: Literal["customer", "assistant", "representative"]
    text: str
    at: datetime
    turn_id: TurnId | None = None
    kind: Literal["text", "choice", "code", "form"] | None = None
    card_id: str | None = None
    choice_option: str | None = None


class TurnBegin(MeridianModel):
    """DO-4 section 13: new | completed(stored response) | running | failed."""

    status: Literal["new", "completed", "running", "failed"]
    response: str | None = None  # set only for "completed"


class TurnRow(MeridianModel):
    """One turns row as stored."""

    turn_id: TurnId
    thread_id: ThreadId
    request_id: RequestId
    run_tag: Literal["live", "eval", "load"]
    run_id: str | None
    agent_version: str
    sequence: int
    received_at: datetime
    status: Literal["running", "completed", "failed"]
    gate_result: str | None = None
    path: str | None = None
    outcome: str | None = None
    degrade_reason: str | None = None
    planner: PlannerTrace | None = None
    danger_raised: bool | None = None
    specialists_run: tuple[str, ...] = ()
    replied_at: datetime | None = None
    server_ms: int | None = None
    model_calls: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    tool_calls: int | None = None
    trace_id: str | None = None
    trace_export: ExportStatus | None = None
    response: str | None = None

    def as_record(self) -> TurnRecord | None:
        """The TurnRecord this row holds; None while running or when a TurnRecord field is NULL."""
        needed = (
            self.gate_result,
            self.path,
            self.outcome,
            self.replied_at,
            self.server_ms,
            self.model_calls,
            self.input_tokens,
            self.output_tokens,
            self.cost_usd,
            self.tool_calls,
            self.trace_export,
            self.response,
        )
        if self.status == "running" or any(v is None for v in needed):
            return None
        return TurnRecord.model_validate(
            {
                "status": self.status,
                "trace": {
                    "gate_result": self.gate_result,
                    "path": self.path,
                    "outcome": self.outcome,
                    "degrade_reason": self.degrade_reason,
                    "planner": self.planner,
                    "danger_raised": bool(self.danger_raised),
                    "specialists_run": self.specialists_run,
                },
                "replied_at": self.replied_at,
                "server_ms": self.server_ms,
                "model_calls": self.model_calls,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cost_usd": self.cost_usd,
                "tool_calls": self.tool_calls,
                "trace_id": self.trace_id,
                "trace_export": self.trace_export,
                "response": self.response,
            }
        )


TURN_COLS = (
    "turn_id, thread_id, request_id, run_tag, run_id, agent_version, sequence, received_at, status, gate_result, "
    "path, outcome, degrade_reason, planner_model, planner_fallback_used, planner_failure, plan_mode, plan_source, "
    "plan_intents, plan_handoff_request, plan_topic, planner_failed, danger_raised, specialists_run, replied_at, "
    "server_ms, model_calls, input_tokens, output_tokens, cost_usd, tool_calls, trace_id, trace_export, response"
)


def turn_row(r: tuple[Any, ...]) -> TurnRow:
    planner = None
    if r[13] is not None:
        planner = PlannerTrace.model_validate(
            {
                "model": r[13],
                "fallback_used": bool(r[14]),
                "failure": r[15],
                "plan_mode": r[16],
                "plan_source": r[17],
                "intents": json.loads(r[18] or "[]"),
                "handoff_request": r[19],
                "topic": r[20],
                "planner_failed": bool(r[21]),
            }
        )
    return TurnRow.model_validate(
        {
            "turn_id": r[0],
            "thread_id": r[1],
            "request_id": r[2],
            "run_tag": r[3],
            "run_id": r[4],
            "agent_version": r[5],
            "sequence": r[6],
            "received_at": _dt(r[7]),
            "status": r[8],
            "gate_result": r[9],
            "path": r[10],
            "outcome": r[11],
            "degrade_reason": r[12],
            "planner": planner,
            "danger_raised": None if r[22] is None else bool(r[22]),
            "specialists_run": tuple(json.loads(r[23])),
            "replied_at": _dt(r[24]),
            "server_ms": r[25],
            "model_calls": r[26],
            "input_tokens": r[27],
            "output_tokens": r[28],
            "cost_usd": r[29],
            "tool_calls": r[30],
            "trace_id": r[31],
            "trace_export": r[32],
            "response": r[33],
        }
    )


class StreamEvent(MeridianModel):
    """What a writer appends (DO-4 section 13 named it, no sketch)."""

    type: str = Field(min_length=1, max_length=40)  # OpenAPI ChatEvent / CaseEvent type, e.g. "demo_reset"
    payload: dict[str, JsonValue] = Field(default_factory=dict)
    at: datetime  # demo clock


class EventRow(MeridianModel):
    id: EventId
    stream: str
    type: str
    payload: dict[str, JsonValue]
    at: datetime


class CustomerRow(MeridianModel):
    customer_id: CustomerId
    name: str
    phone: str
    email: str | None
    service_address: str
    city: str
    zip: str
    membership_tier: Literal["none", "standard", "plus"]
    membership_renewal_date: date | None
    system_brand: str | None
    system_install_date: date | None


class InvoiceRow(MeridianModel):
    invoice_id: InvoiceId
    customer_id: CustomerId
    appointment_id: int | None
    issued_date: date
    due_date: date
    amount_cents: int
    balance_cents: int
    line_items: tuple[dict[str, JsonValue], ...]


class AppointmentRow(MeridianModel):
    """Issued appointment + its slot + technician; never issue_description."""

    appointment_id: int
    slot_id: int
    customer_id: CustomerId
    status: Literal["scheduled", "completed", "cancelled", "no_show"]
    is_warranty_visit: bool
    created_at: date
    slot_date: date
    window: str
    zone: str
    service_type: str
    tech_id: int
    technician: str


class CaseOwnerRow(MeridianModel):
    thread_id: ThreadId
    owner_role: StaffRole | None
    owner_since: datetime | None
    lifecycle: str


# --- case store rows (repos_cases) ---
Lifecycle = Literal[
    "live_queued", "unassigned", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved"
]


class CaseRow(MeridianModel):
    case_ref: CaseRef
    thread_id: ThreadId
    turn_id: TurnId | None = None
    customer_id: CustomerId | None = None
    reason: HandoffReason
    priority: Priority
    rule_id: str
    trigger: str
    lifecycle: Lifecycle
    owner_role: StaffRole | None = None
    owner_since: datetime | None = None
    due_at: datetime | None = None  # the CASE due (CAS-10)
    wake_up_at: datetime | None = None
    version: int = Field(default=1, ge=1)
    seed: bool = False
    safety_kind: str | None = None
    change_request: dict[str, JsonValue] | None = None
    alert: Literal["supervisor_now"] | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    queued_at: datetime | None = None


class CaseEventRow(MeridianModel):
    id: int | None = None
    case_ref: CaseRef
    kind: str = Field(min_length=1, max_length=40)
    key: str = ""  # idempotency key (scheduler); "" = none
    actor_role: Literal["representative", "supervisor", "owner", "ai", "system"]
    job_run_id: str | None = None
    detail: dict[str, JsonValue] = Field(default_factory=dict)
    at: datetime


class PromiseRow(MeridianModel):
    id: int
    case_ref: CaseRef
    promise: Promise  # promise.due_at = the CUSTOMER due (CAS-10)
    status: Literal["open", "kept", "missed", "changed"]
    created_at: datetime
    status_at: datetime | None = None
    status_reason: str | None = None


class FollowupRow(MeridianModel):
    case_ref: CaseRef
    thread_id: ThreadId
    channel: Literal["email", "phone"]
    destination_label: str
    destination: str | None = None  # raw destination for staff; never in a log
    on_record: bool
    window: Literal["morning", "afternoon", "any"]
    saved_line: str
    updated_at: datetime


class ActivityRow(MeridianModel):
    id: int | None = None
    case_ref: CaseRef
    kind: Literal["call", "email"]
    outcome: Literal["reached", "no_answer", "left_message"]
    note: str | None = None
    actor_role: StaffRole
    at: datetime


class DemoStateRow(MeridianModel):
    demo_now: datetime
    staffing: Literal["nobody_online", "simulated_on_shift"]


class DemoEventRow(MeridianModel):
    demo_event_id: str
    at_wall: datetime
    kind: Literal["clock_advanced", "staffing_changed"]
    step: str | None = None
    mode: str | None = None
    demo_before: str  # clock: format_wall of the demo times; staffing: the modes
    demo_after: str
    became_overdue: int | None = None
    converted_cases: int | None = None
    request_id: str
    role: str


class JobRunRow(MeridianModel):
    job_run_id: str
    started_wall_at: datetime
    finished_wall_at: datetime | None
    demo_now: datetime
    status: Literal["started", "completed", "failed"]
    error_kind: str | None
    counts: dict[str, int | None]


class ResetEventRow(MeridianModel):
    reset_id: str
    at_wall: datetime
    asked_by_role: DemoRole | None = None
    asked_by_session: str | None = None
    request_id: str | None = None
    restored: dict[str, int] = Field(default_factory=dict)
    open_chats_ended: int = 0
    roles_reset: int = 0
    checkpoints_cleared: bool | None = None


class SeedEventRow(MeridianModel):
    seed_event_id: str
    at_wall: datetime
    reset_id: str | None = None
    deploy_id: str | None = None
    seed_count: int = Field(ge=0)
    label: str = "demo seed"
