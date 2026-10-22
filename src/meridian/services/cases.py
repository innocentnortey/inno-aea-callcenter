"""Case service (A6): opens, lists, shows and changes cases for the staff console and the handoff.

Every method opens one unit of work and reads or writes through it; nothing here calls a model, a route or SQL. Pure
rules live in `_case_rules.py`, view builders in `_case_views.py`. `HandoffService` (handoff.py) calls `open_case`
inside its own transaction, and `convert_live_queued` joins the caller's transaction when it is given one.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Literal, TypeAlias

from meridian.adapters.sqlite.rows import (
    CaseEventRow,
    CaseRow,
    ConversationRow,
    StreamEvent,
    case_stream,
    thread_stream,
)
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.blocks import HandoffBlock, LiveQueuedBlock, SettledView
from meridian.domain.common import CaseRef, ThreadId, TurnId
from meridian.domain.handoff import (
    Brief,
    CaseSummary,
    FollowUp,
    HandoffReason,
    HandoffRequest,
    HandoffResult,
    Priority,
    Promise,
)
from meridian.domain.identity import IdentityState
from meridian.domain.staff import StaffActor, StaffRole
from meridian.domain.state import Controller
from meridian.domain.views import (
    ActivityIn,
    ActivityResult,
    Alert,
    CaseAction,
    CaseActionRejected,
    CaseDetail,
    CaseIdentityView,
    CaseSummaryView,
    FollowUpChoice,
    Lane,
    LiveStateView,
    OtherCase,
    OversightLanes,
    OversightView,
    QueueView,
)
from meridian.policy.handoff import case_due_at, promise_for
from meridian.policy.texts import TEXTS, TextId, render
from meridian.ports.runtime import Clock, UnitOfWork, UnitOfWorkFactory
from meridian.services._case_actions import (
    align_burning_due_in,
    apply_in,
    record_activity_in,
    set_followup_in,
)
from meridian.services._case_rules import (
    LANE_ORDER,
    LIFECYCLE_WORD,
    due_state,
    identity_view,
    lane_for,
    queue_key,
    staffing_view,
)
from meridian.services._case_views import (
    activity_view,
    brief_view,
    case_sources,
    conversation_lines,
    live_state_of,
    promise_record,
    queue_row,
    summary_view,
)

__all__ = ["CaseNotFound", "CaseService", "staffing_view"]

HandoffBlockFn: TypeAlias = Callable[[HandoffResult], HandoffBlock | LiveQueuedBlock | None]
SettledViewFn: TypeAlias = Callable[[Settled, IdentityState, Controller], SettledView]


class CaseNotFound(LookupError):
    """No case has this reference; the route answers 404."""

    def __init__(self, case_ref: str) -> None:
        super().__init__(f"no case {case_ref}")
        self.case_ref = case_ref


def _rank(p: Priority) -> int:
    return int(p.value[1])


def _actor_for(trigger: str) -> str:
    return "system" if trigger == "con4" else "ai"


def _alert(priority: Priority, reason: HandoffReason) -> str | None:
    if priority in (Priority.P0, Priority.P1) or reason is HandoffReason.FEE_BEARING_CHANGE:
        return "supervisor_now"
    return None


class CaseService:
    """Cases for the handoff and the staff console."""

    def __init__(
        self,
        uow: UnitOfWorkFactory,
        clock: Clock,
        *,
        handoff_block: HandoffBlockFn | None = None,
        settled_view: SettledViewFn | None = None,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._handoff_block = handoff_block
        self._settled_view = settled_view

    # ---- opening

    def open_case(
        self, tx: UnitOfWork, req: HandoffRequest, promise: Promise, now: dt.datetime
    ) -> HandoffResult:
        """Opens the thread's case (or joins the open one) in the caller's transaction; never commits."""
        existing = tx.cases.cases.get_for_thread_open(req.thread_id)
        if existing is not None:
            return self._join_open(tx, existing, req, now)
        ref = tx.cases.refs.next_case_ref()
        window_start = req.change_request.window_start if req.change_request else None
        case_due = case_due_at(req.reason, promise, window_start)
        lifecycle: Literal["live_queued", "unassigned"] = (
            "live_queued" if promise.live_queued else "unassigned"
        )
        alert = _alert(req.priority, req.reason)
        customer_id = req.identity.customer_id if req.identity.status == "verified" else None
        tx.cases.cases.insert(
            CaseRow(
                case_ref=ref,
                thread_id=req.thread_id,
                turn_id=req.turn_id,
                customer_id=customer_id,
                reason=req.reason,
                priority=req.priority,
                rule_id=req.rule_id,
                trigger=req.trigger,
                lifecycle=lifecycle,
                due_at=case_due,
                version=1,
                seed=False,
                safety_kind=req.safety_kind.value if req.safety_kind else None,
                change_request=req.change_request.model_dump(mode="json") if req.change_request else None,
                alert=alert,  # type: ignore[arg-type]
                created_at=now,
                updated_at=now,
                queued_at=now if promise.live_queued else None,
            )
        )
        tx.cases.promises.insert(ref, promise, now)
        tx.cases.case_events.append(
            CaseEventRow(
                case_ref=ref,
                kind="case_opened",
                actor_role=_actor_for(req.trigger),  # type: ignore[arg-type]
                detail={
                    "reason": req.reason.value,
                    "priority": req.priority.value,
                    "rule_id": req.rule_id,
                    "trigger": req.trigger,
                    "thread_id": str(req.thread_id),
                    "turn_id": str(req.turn_id),
                    "version": 1,
                },
                at=now,
            )
        )
        action = tx.core.actions.record(
            CompletedAction(
                key=ActionKey(
                    thread_id=req.thread_id,
                    turn_id=req.turn_id,
                    kind=ActionKind.CASE_OPENED,
                    record_id=str(ref),
                ),
                kind=ActionKind.CASE_OPENED,
                records={"case": str(ref)},
                at=now,
            )
        )
        tx.core.events.append(
            thread_stream(req.thread_id),
            StreamEvent(
                type="case_created",
                payload={
                    "case_ref": str(ref),
                    "thread_id": str(req.thread_id),
                    "turn_id": str(req.turn_id),
                    "reason": req.reason.value,
                    "priority": req.priority.value,
                    "lifecycle": lifecycle,
                },
                at=now,
            ),
        )
        if promise.live_queued:
            tx.core.conversations.set_live_state(req.thread_id, "queued", now)
        return HandoffResult(case=self._summary(tx, ref), created=True, action=action, alert=alert)  # type: ignore[arg-type]

    def _join_open(
        self, tx: UnitOfWork, existing: CaseRow, req: HandoffRequest, now: dt.datetime
    ) -> HandoffResult:
        ref = existing.case_ref
        seen = {existing.reason} | {
            HandoffReason(str(e.detail["reason"]))
            for e in tx.cases.case_events.list_for_case(ref)
            if e.kind == "reason_added" and isinstance(e.detail.get("reason"), str)
        }
        if req.reason not in seen:
            raise_to = req.priority if _rank(req.priority) < _rank(existing.priority) else None
            version = existing.version
            if raise_to is not None:
                new_version = tx.cases.cases.update_versioned(
                    ref,
                    existing.version,
                    priority=raise_to,
                    alert=_alert(raise_to, existing.reason) or existing.alert,
                    updated_at=now,
                )
                if new_version is None:
                    raise RuntimeError("case changed during handoff")
                version = new_version
                tx.core.events.append(
                    case_stream(ref),
                    StreamEvent(
                        type="case_changed",
                        payload={"version": version, "lifecycle": existing.lifecycle},
                        at=now,
                    ),
                )
            tx.cases.case_events.append(
                CaseEventRow(
                    case_ref=ref,
                    kind="reason_added",
                    actor_role=_actor_for(req.trigger),  # type: ignore[arg-type]
                    detail={
                        "reason": req.reason.value,
                        "priority": req.priority.value,
                        "rule_id": req.rule_id,
                        "trigger": req.trigger,
                        "turn_id": str(req.turn_id),
                        "priority_from": existing.priority.value,
                        "priority_to": (raise_to or existing.priority).value,
                        "version": version,
                    },
                    at=now,
                )
            )
        return HandoffResult(
            case=(summary := self._summary(tx, ref)),
            created=False,
            action=self._opened_action(tx, existing, req.turn_id),
            alert=_alert(summary.priority, req.reason),  # type: ignore[arg-type]
        )

    @staticmethod
    def _opened_action(tx: UnitOfWork, row: CaseRow, fallback_turn: TurnId | None) -> CompletedAction:
        ref = row.case_ref
        for a in tx.core.actions.for_thread(row.thread_id):
            if a.kind is ActionKind.CASE_OPENED and a.key.record_id == str(ref):
                return a
        return CompletedAction(
            key=ActionKey(
                thread_id=row.thread_id,
                turn_id=row.turn_id or fallback_turn,  # type: ignore[arg-type]
                kind=ActionKind.CASE_OPENED,
                record_id=str(ref),
            ),
            kind=ActionKind.CASE_OPENED,
            records={"case": str(ref)},
            at=row.created_at,
        )

    @staticmethod
    def _summary(tx: UnitOfWork, ref: CaseRef) -> CaseSummary:
        row = tx.cases.cases.get(ref)
        prow = tx.cases.promises.current(ref)
        f = tx.cases.followups.get(ref)
        if row is None or prow is None:
            raise LookupError("case row missing")
        return CaseSummary(
            case_ref=row.case_ref,
            reason=row.reason,
            priority=row.priority,
            state=row.lifecycle,
            created_at=row.created_at,
            promise=prow.promise,
            followup=None
            if f is None
            else FollowUp(
                channel=f.channel,
                destination_label=f.destination_label,
                on_record=f.on_record,
                window=f.window,
                saved_line=f.saved_line,
            ),
            version=row.version,
            seed=row.seed,
            due_at=row.due_at,
        )

    def attach_brief(self, case_ref: CaseRef, brief: Brief) -> None:
        """Stores (or replaces) the case's brief."""
        if brief.case_ref != case_ref:
            raise ValueError("brief belongs to another case")
        now = self._clock.now()
        with self._uow(write=True) as tx:
            if tx.cases.cases.get(case_ref) is None:
                raise ValueError("unknown case")
            tx.cases.briefs.upsert(brief, now)
            tx.commit()

    def open_case_for_thread(self, thread_id: ThreadId) -> CaseSummary | None:
        """The thread's open case, if any."""
        with self._uow() as tx:
            row = tx.cases.cases.get_for_thread_open(thread_id)
            return None if row is None else self._summary(tx, row.case_ref)

    # ---- shift end

    def convert_live_queued(self, now: dt.datetime, tx: UnitOfWork | None = None) -> int:
        """Turns every live-queued case into an ordinary unassigned one; joins the caller's transaction if given."""
        if tx is not None:
            return self._convert(tx, now)
        with self._uow(write=True) as own:
            count = self._convert(own, now)
            own.commit()
        return count

    def _convert(self, tx: UnitOfWork, now: dt.datetime) -> int:
        count = 0
        for row in tx.cases.cases.list_open():
            if row.lifecycle != "live_queued":
                continue
            ref = row.case_ref
            cr = row.change_request
            raw = cr.get("window_start") if cr else None
            window_start = dt.datetime.fromisoformat(raw) if isinstance(raw, str) else None
            new = promise_for(row.reason, "nobody_online", now, window_start)
            case_due = case_due_at(row.reason, new, window_start)
            tx.cases.promises.set_status(ref, "changed", now, "shift_ended")
            tx.cases.promises.insert(ref, new, now)
            tx.cases.promises.set_status(ref, "changed", now, "shift_ended")
            version = tx.cases.cases.update_versioned(
                ref, row.version, lifecycle="unassigned", due_at=case_due, updated_at=now
            )
            if version is None:
                raise RuntimeError("case changed during shift end")
            tx.core.conversations.set_live_state(row.thread_id, "not_live", None)
            tx.cases.case_events.append(
                CaseEventRow(
                    case_ref=ref,
                    kind="converted",
                    actor_role="system",
                    detail={
                        "reason": "shift_ended",
                        "policy_row": new.policy_row,
                        "promise_status": "changed",
                        "version": version,
                    },
                    at=now,
                )
            )
            result = HandoffResult(
                case=self._summary(tx, ref),
                created=False,
                action=self._opened_action(tx, row, None),
                alert=None,
            )
            block = self._handoff_block(result) if self._handoff_block is not None else None
            conv = tx.core.conversations.lookup(str(row.thread_id))
            controller = conv.controller if isinstance(conv, ConversationRow) else Controller(kind="ai")
            payload: dict[str, object] = {
                "speaker": {"kind": "event", "display_name": None},
                "line": TEXTS[TextId.SHIFT_ENDED],
                "handoff": block.model_dump(mode="json") if block is not None else None,
            }
            if self._settled_view is not None:
                settled = self._settled_view(
                    tx.core.settled_for(row.thread_id, now),
                    tx.core.reads.identity_state(row.thread_id),
                    controller,
                )
                payload["settled"] = settled.model_dump(mode="json")
            tx.core.events.append(
                thread_stream(row.thread_id),
                StreamEvent(type="shift_ended", payload=payload, at=now),  # type: ignore[arg-type]
            )
            tx.core.events.append(
                case_stream(ref),
                StreamEvent(
                    type="case_changed", payload={"version": version, "lifecycle": "unassigned"}, at=now
                ),
            )
            tx.core.events.append(
                case_stream(ref), StreamEvent(type="chat_closed", payload={"reason": "shift_ended"}, at=now)
            )
            count += 1
        return count

    # ---- views

    def queue(self, role: StaffRole, now: dt.datetime) -> QueueView:
        """The live queue and this role's needs-action list."""
        with self._uow() as tx:
            staffing = tx.cases.demo_state.get().staffing
            rows = tx.cases.cases.list_open()
            live_rows = sorted(
                (r for r in rows if r.lifecycle == "live_queued") if staffing == "simulated_on_shift" else (),
                key=lambda r: (
                    0 if r.priority is Priority.P0 else 1 if r.priority is Priority.P1 else 2,
                    (r.queued_at or r.created_at).timestamp(),
                    str(r.case_ref),
                ),
            )
            needs = sorted(
                (r for r in rows if r.lifecycle != "live_queued" and r.owner_role in (None, role)),
                key=lambda r: queue_key(
                    r.priority, due_state(r.due_at, now), r.due_at, r.created_at, str(r.case_ref)
                ),
            )
            return QueueView(
                as_of=now,
                staffing=staffing_view(staffing),
                live=tuple(queue_row(tx, r, now) for r in live_rows),
                needs_my_action=tuple(queue_row(tx, r, now) for r in needs),
            )

    def detail(self, case_ref: CaseRef, role: StaffRole, now: dt.datetime) -> CaseDetail:
        """Everything the case view shows. Raises CaseNotFound for an unknown reference."""
        with self._uow() as tx:
            row = tx.cases.cases.get(case_ref)
            if row is None:
                raise CaseNotFound(str(case_ref))
            staffing = tx.cases.demo_state.get().staffing
            live_state, conv = live_state_of(tx, row.thread_id)
            identity = tx.core.reads.identity_state(row.thread_id)
            lookups = tx.core.lookup_log.for_thread(row.thread_id)
            brief = tx.cases.briefs.get(case_ref)
            sources = case_sources(tx, lookups, brief)
            changed_ids = {s.source_id for s in sources if s.changed_since}
            status, line, note = identity_view(identity, case_customer=row.customer_id is not None)
            others = (
                tuple(
                    OtherCase(reference=str(o.case_ref), status=LIFECYCLE_WORD[o.lifecycle])
                    for o in tx.cases.cases.list_for_customer(row.customer_id)
                    if o.case_ref != row.case_ref
                )
                if row.customer_id
                else ()
            )
            return CaseDetail(
                case=summary_view(tx, row, role, staffing, now),
                promise=promise_record(tx, row),
                brief=brief_view(brief, changed_ids),
                identity=CaseIdentityView(status=status, line=line, demo_note=note),  # type: ignore[arg-type]
                sources=sources,
                conversation=conversation_lines(tx, row.thread_id),
                activities=tuple(activity_view(a) for a in tx.cases.activities.list_for_case(case_ref)),
                live=LiveStateView(
                    state=live_state,  # type: ignore[arg-type]
                    since=conv.live_since if conv else None,
                    controller=conv.controller.kind if conv else "ai",
                ),
                other_cases=others,
                agent_version=conv.agent_version if conv else "unknown",
                as_of=now,
            )

    def oversight(self, now: dt.datetime) -> OversightView:
        """The five oversight lanes, the overdue alerts and the counters."""
        with self._uow() as tx:
            staffing = tx.cases.demo_state.get().staffing
            rows = tx.cases.cases.list_open()
            grouped: dict[str, list[CaseRow]] = {name: [] for name in LANE_ORDER}
            for r in rows:
                lane = lane_for(
                    r.priority, due_state(r.due_at, now), r.lifecycle, r.created_at, r.wake_up_at, now
                )
                if lane is not None:
                    grouped[lane].append(r)

            def lane_of(name: str) -> Lane:
                ordered = sorted(
                    grouped[name],
                    key=lambda r: queue_key(
                        r.priority, due_state(r.due_at, now), r.due_at, r.created_at, str(r.case_ref)
                    ),
                )
                return Lane(count=len(ordered), rows=tuple(queue_row(tx, r, now) for r in ordered))

            lanes = OversightLanes(**{name: lane_of(name) for name in LANE_ORDER})
            alerts = tuple(
                Alert(
                    type="overdue",
                    case_ref=str(r.case_ref),
                    line=render(TextId.OVERSIGHT_OVERDUE, case_ref=str(r.case_ref)),
                    at=r.due_at or now,
                )
                for r in grouped["overdue"]
            )
            live_queue = (
                sum(1 for r in rows if r.lifecycle == "live_queued")
                if staffing == "simulated_on_shift"
                else 0
            )
            return OversightView(
                as_of=now,
                demo_now=now,
                staffing=staffing_view(staffing),
                alerts=alerts,
                lanes=lanes,
                live_queue_length=live_queue,
                new_flags_count=tx.core.reads.new_flags_count(),
            )

    # ---- actions

    def apply(
        self,
        case_ref: CaseRef,
        action: CaseAction,
        actor: StaffActor,
        expected_version: int,
        now: dt.datetime,
    ) -> CaseSummaryView | CaseActionRejected:
        """One CON-13 action. Every rejection leaves nothing written."""
        with self._uow(write=True) as tx:
            result = apply_in(tx, case_ref, action, actor, expected_version, now)
            if not isinstance(result, CaseActionRejected):
                tx.commit()
            return result

    def set_followup(
        self, thread_id: ThreadId, choice: FollowUpChoice, now: dt.datetime
    ) -> FollowUp | CaseActionRejected:
        """Saves how and when the customer wants to be reached; only the phone on record is built so far."""
        with self._uow(write=True) as tx:
            followup = set_followup_in(tx, thread_id, choice, now)
            if not isinstance(followup, CaseActionRejected):
                tx.commit()
            return followup

    def record_activity(
        self, case_ref: CaseRef, activity: ActivityIn, actor: StaffActor, now: dt.datetime
    ) -> ActivityResult | CaseActionRejected:
        """Records a call or an email the representative did by hand. Nothing is sent."""
        with self._uow(write=True) as tx:
            recorded = record_activity_in(tx, case_ref, activity, actor, now)
            if not isinstance(recorded, CaseActionRejected):
                tx.commit()
            return recorded

    def align_burning_due(
        self, thread_id: ThreadId, window_start: dt.datetime, turn_id: TurnId, now: dt.datetime
    ) -> bool:
        """CAS-16 option A: the burning_ruled_out case is due at its booked window start; True when it moved."""
        with self._uow(write=True) as tx:
            moved = align_burning_due_in(tx, thread_id, window_start, turn_id, now)
            if moved:
                tx.commit()
            return moved
