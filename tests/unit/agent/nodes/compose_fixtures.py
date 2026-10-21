"""Builders shared by the two compose test files (AEA-21 plan section 6). Synthetic ids and data only."""

from __future__ import annotations

import datetime as dt
from typing import Any
from zoneinfo import ZoneInfo

from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import CaseRef, HandoffReason, PassageId, RequestId, ThreadId, TurnId
from meridian.domain.handoff import CaseSummary, HandoffResult, Priority, Promise
from meridian.domain.records import Passage
from meridian.domain.specialists import KnowledgePoint
from meridian.domain.state import ConversationState, OpenTask, TaskDetails
from meridian.domain.turn import (
    GateDecision,
    GateKind,
    Intake,
    RuleMatches,
    SpanHandle,
    TaskIntent,
    TurnBudget,
    TurnContext,
    TurnFacts,
    TurnIds,
    TurnInput,
)

THREAD = ThreadId("6f1c2d3e-4b5a-4c6d-8e7f-0a1b2c3d4e5f")
TURN3 = TurnId("1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d")
TURN4 = TurnId("2b3c4d5e-6f7a-4b8c-9d0e-1f2a3b4c5d6e")
REQ = RequestId("3c4d5e6f-7a8b-4c9d-8e0f-2a3b4c5d6e7f")
DEMO_NOW = dt.datetime(2026, 10, 16, 14, 20, tzinfo=ZoneInfo("America/Chicago"))


def wp4f_action() -> CompletedAction:
    """WP-4F: turn 3 moved appointment 159 to Monday 2026-10-19 (the fee line is synthetic; AEA-13 owns the real one)."""
    return CompletedAction(
        key=ActionKey(thread_id=THREAD, turn_id=TURN3, kind=ActionKind.MOVED, record_id="159"),
        kind=ActionKind.MOVED,
        records={"appointment": "159", "slot": "56", "old_slot": "159"},
        before={"date": "2026-10-22", "window": "08:00-12:00", "technician": "Marta Kowalski"},
        after={
            "date": "2026-10-19",
            "window": "08:00-12:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "Diagnostic fee: waived for members",
        },
        at=DEMO_NOW - dt.timedelta(minutes=2),
    )


def make_ctx(turn_id: TurnId = TURN4, *, intake: Intake | None = None) -> TurnContext:
    return TurnContext(
        ids=TurnIds(
            thread_id=THREAD,
            turn_id=turn_id,
            request_id=REQ,
            run_tag="live",
            run_id=None,
            agent_version="test",
        ),
        budget=TurnBudget(started=0.0, deadline=60.0),
        now=DEMO_NOW,
        demo_session="demo-session-1",
        span=SpanHandle(turn_id=turn_id, trace_id=None),
        intake=intake,
    )


def no_rules() -> RuleMatches:
    return RuleMatches(
        safety=None,
        burning_unclear=False,
        danger_words=False,
        person=False,
        policy_trigger=None,
        rule_ids=(),
        correction=False,
    )


def gate(kind: GateKind, **kw: Any) -> GateDecision:
    return GateDecision(kind=kind, rules=no_rules(), **kw)


def state(**kw: Any) -> ConversationState:
    turn_input = TurnInput(
        turn_id=TURN4, message_id=1, kind="text", text_store="Yes, please.", received_at=DEMO_NOW
    )
    return ConversationState(thread_id=THREAD, turn_input=turn_input, **kw)


def facts(**kw: Any) -> TurnFacts:
    fields: dict[str, Any] = {
        "turn_id": TURN4,
        "gate_kind": GateKind.FREE_TEXT,
        "plan_mode": None,
        "points": (),
        "passages": (),
        "no_source_tasks": (),
        "windows_shown": (),
        "writes_this_turn": (),
        "change_request": None,
        "handoff": None,
        "escalation": None,
        "identity_step": None,
    }
    fields.update(kw)
    return TurnFacts(**fields)


def handoff_result(
    policy_row: str,
    text: str,
    *,
    live_queued: bool = False,
    priority: Priority = Priority.P3,
    case_ref: str = "MHC-C-0007",
    reason: HandoffReason = HandoffReason.UNSUPPORTED_ACTION,
    due_label: str | None = "Monday, October 19, 7:00 pm",
    turn_id: TurnId = TURN4,
) -> HandoffResult:
    promise = Promise(
        policy_row=policy_row,
        text=text,
        due_at=DEMO_NOW + dt.timedelta(days=3),
        due_label=due_label,
        extra_lines=("A person will pick this up.",),
        live_queued=live_queued,
    )
    case = CaseSummary(
        case_ref=CaseRef(case_ref),
        reason=reason,
        priority=priority,
        state="live_queued" if live_queued else "unassigned",
        created_at=DEMO_NOW,
        promise=promise,
        followup=None,
        version=1,
        due_at=promise.due_at,
    )
    action = CompletedAction(
        key=ActionKey(thread_id=THREAD, turn_id=turn_id, kind=ActionKind.CASE_OPENED, record_id=case_ref),
        kind=ActionKind.CASE_OPENED,
        records={"case": case_ref},
        at=DEMO_NOW,
    )
    return HandoffResult(case=case, created=True, action=action, alert=None)


def passage(pid: str, text: str) -> Passage:
    return Passage(
        passage_id=PassageId(pid),
        file=pid.split("#")[0],
        section="Section",
        version_label="v1",
        version_date=dt.date(2026, 1, 5),
        text=text,
        score=0.9,
    )


def point(pid: str) -> KnowledgePoint:
    return KnowledgePoint(text="A point.", passage_id=PassageId(pid))


def open_booking_task(task_id: str = "t-1") -> OpenTask:
    return OpenTask(
        task_id=task_id,
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        opened_turn=TURN4,
        details=TaskDetails(),
        status="open",
    )
