"""Write bodies of the case service (A6): the staff actions `apply`, `set_followup`, `record_activity`, and the burning due move.

Each function runs inside the caller's write unit of work and never commits: `CaseService` commits only when the
result is not a `CaseActionRejected`, so a rejection leaves nothing written. No model, route or SQL here.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Final

from meridian.adapters.sqlite.rows import (
    ActivityRow,
    CaseEventRow,
    CaseRow,
    FollowupRow,
    StreamEvent,
    case_stream,
)
from meridian.domain.common import ApiErrorCode, CaseRef, ThreadId, TurnId
from meridian.domain.handoff import FollowUp, HandoffReason
from meridian.domain.staff import ASSIGNEE_ROLES, ROLE_ACTIONS, StaffActor
from meridian.domain.views import (
    ActivityIn,
    ActivityResult,
    AllowedAction,
    CaseAction,
    CaseActionRejected,
    CaseSummaryView,
    FollowUpChoice,
)
from meridian.policy.handoff import case_due_at
from meridian.policy.texts import TextId, render
from meridian.ports.runtime import UnitOfWork
from meridian.services._case_rules import (
    WINDOW_WORD,
    con13_refusal,
    mask,
    missing_field_refusal,
    promise_status_after_activity,
    promise_status_after_resolve,
    staff_name,
    state_allows,
)
from meridian.services._case_views import activity_view, live_state_of, summary_view

__all__ = [
    "align_burning_due_in",
    "apply_in",
    "record_activity_in",
    "rejected",
    "set_followup_in",
    "version_conflict",
]


def rejected(code: ApiErrorCode, **details: object) -> CaseActionRejected:
    """A typed refusal with optional details."""
    return CaseActionRejected(code=code, details=dict(details) if details else None)  # type: ignore[arg-type]


def version_conflict(tx: UnitOfWork, row: CaseRow) -> CaseActionRejected:
    events = tx.cases.case_events.list_for_case(row.case_ref)
    match = [e for e in events if e.detail.get("version") == row.version]
    e = (match or list(events))[-1] if (match or events) else None
    return rejected(
        ApiErrorCode.VERSION_CONFLICT,
        changed_by=staff_name(e.actor_role) if e else "System",
        changed_at=e.at.isoformat() if e else row.updated_at.isoformat(),
        current_version=row.version,
    )


def apply_in(
    tx: UnitOfWork,
    case_ref: CaseRef,
    action: CaseAction,
    actor: StaffActor,
    expected_version: int,
    now: dt.datetime,
) -> CaseSummaryView | CaseActionRejected:
    """One CON-13 action over the caller's unit of work."""
    row = tx.cases.cases.get(case_ref)
    if row is None:
        return rejected(ApiErrorCode.CASE_NOT_FOUND, reference=str(case_ref))
    name = action.action
    if name not in ROLE_ACTIONS[actor.role]:
        refusal = con13_refusal(
            name,
            lifecycle=row.lifecycle,
            owner_role=row.owner_role,
            owner_since=row.owner_since,
            actor_role=actor.role,
        )
        if refusal is not None:
            return refusal
    missing = missing_field_refusal(action, now)
    if missing is not None:
        return missing
    if expected_version != row.version:
        return version_conflict(tx, row)
    refusal = con13_refusal(
        name,
        lifecycle=row.lifecycle,
        owner_role=row.owner_role,
        owner_since=row.owner_since,
        actor_role=actor.role,
    )
    if refusal is not None:
        return refusal
    changes: dict[str, object] = {"updated_at": now}
    if name == "claim":
        changes.update(lifecycle="claimed", owner_role=actor.role, owner_since=now)
    elif name == "release":
        changes.update(lifecycle="unassigned", owner_role=None, owner_since=None, wake_up_at=None)
    elif name == "start":
        changes.update(lifecycle="in_progress", wake_up_at=None)
    elif name == "wait":
        changes.update(lifecycle="waiting", wake_up_at=action.wake_up_at)
    elif name == "resolve":
        changes.update(lifecycle="resolved", resolved_at=now, wake_up_at=None)
    elif name == "close_unresolved":
        changes.update(lifecycle="closed_unresolved", resolved_at=now, wake_up_at=None)
    elif name == "assign":
        if action.assignee is None:
            raise LookupError("assignee missing")
        changes.update(
            owner_role=ASSIGNEE_ROLES[action.assignee],
            owner_since=now,
            lifecycle="claimed",
            wake_up_at=None,
        )
    elif name == "change_priority":
        changes.update(priority=action.priority)
    version = tx.cases.cases.update_versioned(case_ref, expected_version, **changes)
    if version is None:
        fresh = tx.cases.cases.get(case_ref)
        return version_conflict(tx, fresh or row)
    detail: dict[str, object] = {"action": name, "version": version}
    if action.reason:
        detail["reason"] = mask(action.reason)
    if action.outcome:
        detail["outcome"] = mask(action.outcome)
    if action.wake_up_at is not None and name == "wait":
        detail["wake_up_at"] = action.wake_up_at.isoformat()
    if name == "assign" and action.assignee is not None:
        detail["assignee"] = ASSIGNEE_ROLES[action.assignee].value
    if name == "change_priority" and action.priority is not None:
        detail["priority_from"] = row.priority.value
        detail["priority_to"] = action.priority.value
    if name == "resolve":
        prow = tx.cases.promises.current(case_ref)
        if prow is not None and prow.status in {"open", "changed"}:
            new = promise_status_after_resolve(prow.promise.due_at, now)
            tx.cases.promises.set_status(case_ref, new, now, "resolved")
            detail["promise_status_to"] = new
    tx.cases.case_events.append(
        CaseEventRow(
            case_ref=case_ref,
            kind=f"action:{name}",
            actor_role=actor.role.value,
            detail=detail,  # type: ignore[arg-type]
            at=now,
        )
    )
    fresh = tx.cases.cases.get(case_ref)
    if fresh is None:
        raise LookupError("case row missing")
    tx.core.events.append(
        case_stream(case_ref),
        StreamEvent(type="case_changed", payload={"version": version, "lifecycle": fresh.lifecycle}, at=now),
    )
    staffing = tx.cases.demo_state.get().staffing
    summary = summary_view(tx, fresh, actor.role, staffing, now)
    return summary


def set_followup_in(
    tx: UnitOfWork, thread_id: ThreadId, choice: FollowUpChoice, now: dt.datetime
) -> FollowUp | CaseActionRejected:
    """Saves how and when the customer wants to be reached; phone on record and email general are built."""
    row = tx.cases.cases.get_for_thread_open(thread_id)
    if row is None:
        return rejected(ApiErrorCode.NOT_ALLOWED_IN_STATE, state="no_open_case")
    identity = tx.core.reads.identity_state(thread_id)
    on_record = choice.destination == "on_record"
    if on_record and identity.status != "verified":
        return rejected(ApiErrorCode.NOT_ALLOWED_IN_STATE, state="not_verified")
    if choice.channel == "email" and not on_record:
        # FU-saveFollowUp-text, provisional wording pending the UX session. No contact value is read or stored.
        label = "a general contact"
        saved = render(TextId.FOLLOWUP_SAVED_EMAIL_GENERAL, window=WINDOW_WORD[choice.window])
    elif choice.channel == "phone" and on_record:
        customer = tx.core.reads.customer(identity.customer_id) if identity.customer_id else None
        if customer is None:
            return rejected(ApiErrorCode.NOT_ALLOWED_IN_STATE, state="not_verified")
        digits = re.sub(r"[^0-9]", "", customer.phone)[-2:]
        label = f"the number ending in {digits}"
        saved = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window=WINDOW_WORD[choice.window])
    else:
        raise NotImplementedError(
            "follow-up text for email/on_record and phone/general: blocked-on a UX wording follow-up"
        )
    tx.cases.followups.upsert(
        FollowupRow(
            case_ref=row.case_ref,
            thread_id=thread_id,
            channel=choice.channel,
            destination_label=label,
            destination=choice.destination,
            on_record=on_record,
            window=choice.window,
            saved_line=saved,
            updated_at=now,
        )
    )
    tx.cases.case_events.append(
        CaseEventRow(
            case_ref=row.case_ref,
            kind="followup_saved",
            actor_role="system",
            detail={"channel": choice.channel, "on_record": on_record, "window": choice.window},
            at=now,
        )
    )
    return FollowUp(
        channel=choice.channel,
        destination_label=label,
        on_record=on_record,
        window=choice.window,
        saved_line=saved,
    )


def record_activity_in(
    tx: UnitOfWork, case_ref: CaseRef, activity: ActivityIn, actor: StaffActor, now: dt.datetime
) -> ActivityResult | CaseActionRejected:
    """Records a call or an email the representative did by hand. Nothing is sent."""
    row = tx.cases.cases.get(case_ref)
    if row is None:
        return rejected(ApiErrorCode.CASE_NOT_FOUND, reference=str(case_ref))
    key: AllowedAction = "log_call" if activity.kind == "call" else "log_email"
    if key not in ROLE_ACTIONS[actor.role]:
        return rejected(
            ApiErrorCode.ROLE_NOT_ALLOWED,
            role=actor.role.value,
            needs=["representative"],
            reason="wrong_role",
        )
    if activity.expected_version != row.version:
        return version_conflict(tx, row)
    staffing = tx.cases.demo_state.get().staffing
    if not state_allows(
        key,
        lifecycle=row.lifecycle,
        owner_role=row.owner_role,
        live_state=live_state_of(tx, row.thread_id)[0],
        staffing=staffing,
        actor_role=actor.role,
    ):
        if row.owner_role is None:
            return rejected(ApiErrorCode.NOT_ALLOWED_IN_STATE, state=row.lifecycle, needs="claimed")
        if row.owner_role != actor.role:
            return rejected(
                ApiErrorCode.CASE_ALREADY_CLAIMED,
                claimed_by=staff_name(row.owner_role.value),
                claimed_at=row.owner_since.isoformat() if row.owner_since else None,
            )
        return rejected(
            ApiErrorCode.NOT_ALLOWED_IN_STATE, state=row.lifecycle, needs="claimed or in_progress"
        )
    arow = ActivityRow(
        case_ref=case_ref,
        kind=activity.kind,
        outcome=activity.outcome,
        note=mask(activity.note) if activity.note else None,
        actor_role=actor.role,
        at=now,
    )
    aid = tx.cases.activities.insert(arow)
    prow = tx.cases.promises.current(case_ref)
    detail: dict[str, object] = {"kind": activity.kind, "outcome": activity.outcome}
    if prow is not None:
        new = promise_status_after_activity(activity.outcome, prow.promise.due_at, now, prow.status)
        if new != prow.status:
            tx.cases.promises.set_status(case_ref, new, now, f"activity:{activity.outcome}")
            detail["promise_status_to"] = new
    version = tx.cases.cases.update_versioned(case_ref, activity.expected_version, updated_at=now)
    if version is None:
        return version_conflict(tx, row)
    detail["version"] = version
    tx.cases.case_events.append(
        CaseEventRow(
            case_ref=case_ref,
            kind="activity",
            actor_role=actor.role.value,
            detail=detail,  # type: ignore[arg-type]
            at=now,
        )
    )
    tx.core.events.append(
        case_stream(case_ref),
        StreamEvent(type="case_changed", payload={"version": version, "lifecycle": row.lifecycle}, at=now),
    )
    fresh = tx.cases.cases.get(case_ref)
    if fresh is None:
        raise LookupError("case row missing")
    result = ActivityResult(
        activity=activity_view(arow.model_copy(update={"id": aid})),
        case=summary_view(tx, fresh, actor.role, staffing, now),
    )
    return result


DUE_MOVED_RULE: Final = "CAS16.booked_window"  # CAS-16 option A (D-14)


def align_burning_due_in(
    tx: UnitOfWork, thread_id: ThreadId, window_start: dt.datetime, turn_id: TurnId, now: dt.datetime
) -> bool:
    """Moves the thread's open burning_ruled_out case due to the booked window start, once (CAS-16 option A).

    False, with nothing written, when the thread has no open case, the case has another reason, its promise row is
    missing, or its due already differs from the promise due (an earlier booking moved it). Never commits.
    """
    row = tx.cases.cases.get_for_thread_open(thread_id)
    if row is None or row.reason is not HandoffReason.BURNING_RULED_OUT:
        return False
    prow = tx.cases.promises.current(row.case_ref)
    if prow is None or row.due_at != prow.promise.due_at:
        return False
    due = case_due_at(row.reason, prow.promise, window_start)
    if due == row.due_at:
        return False
    version = tx.cases.cases.update_versioned(row.case_ref, row.version, due_at=due, updated_at=now)
    if version is None:
        raise RuntimeError("case changed during the due move")
    tx.cases.case_events.append(
        CaseEventRow(
            case_ref=row.case_ref,
            kind="due_moved",
            actor_role="ai",
            detail={
                "reason": row.reason.value,
                "rule_id": DUE_MOVED_RULE,
                "turn_id": str(turn_id),
                "version": version,
            },
            at=now,
        )
    )
    tx.core.events.append(
        case_stream(row.case_ref),
        StreamEvent(type="case_changed", payload={"version": version, "lifecycle": row.lifecycle}, at=now),
    )
    return True
