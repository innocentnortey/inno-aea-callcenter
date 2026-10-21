"""Builders for the AEA-29 service tests (frozen with the tests; plan section 6).

Synthetic or issued data only. No contact value is written here: phone and email are read from the issued database at
run time. The service modules are imported lazily inside ``services()`` so this file imports on its own.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import (
    CaseEventRow,
    CaseRow,
    ConversationRow,
    FollowupRow,
    StreamEvent,
    thread_stream,
)
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import CaseRef, CustomerId, PassageId, ThreadId, TurnId
from meridian.domain.handoff import CaseSummary, FollowUp, HandoffReason, HandoffRequest, Priority
from meridian.domain.identity import IdentityState
from meridian.domain.specialists import ChangeRequestDraft
from meridian.domain.staff import StaffRole
from meridian.domain.state import Controller, ConversationState
from meridian.domain.tools import LookupEntry
from meridian.domain.turn import SpanHandle, TurnBudget, TurnContext, TurnIds, TurnInput
from meridian.policy.handoff import STAFF_GUIDANCE_FOR, priority_for, promise_for
from meridian.policy.texts import TEXTS, TextId
from meridian.ports.runtime import UnitOfWork
from meridian.retrieval.manifest import StaffGuidance
from tests.fakes.clock import WORKED_PAIRS_NOW, FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite

CHI = ZoneInfo("America/Chicago")
NOW = WORKED_PAIRS_NOW
assert NOW == DEMO_START

_THREAD: TypeAdapter[ThreadId] = TypeAdapter(ThreadId)
_TURN: TypeAdapter[TurnId] = TypeAdapter(TurnId)
_CASE: TypeAdapter[CaseRef] = TypeAdapter(CaseRef)
_CUSTOMER: TypeAdapter[CustomerId] = TypeAdapter(CustomerId)

OMAR = _CUSTOMER.validate_python("MHC-10002")
OMAR_MESSAGE = "Nobody told me about an after-hours fee. I want that taken off."
DISPLAY_NOW = dt.datetime(2026, 10, 16, 14, 20, tzinfo=CHI)
STAFF_ROLES = (StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR, StaffRole.OWNER)


def store() -> Any:
    """Context manager over ``temp_sqlite()`` (the issued database copy, migrations applied)."""
    return temp_sqlite()


def ref(n: int) -> CaseRef:
    return _CASE.validate_python(f"MHC-C-{n:04d}")


def new_turn() -> TurnId:
    return _TURN.validate_python(str(uuid4()))


def j(model: Any) -> Any:
    """The wire form of any returned model, as plain JSON data."""
    return model.model_dump(mode="json")


def jtext(model: Any) -> str:
    text: str = model.model_dump_json()
    return text


def is_rejected(result: Any) -> bool:
    return hasattr(result, "code") and hasattr(result, "details")


def code_of(result: Any) -> str:
    return str(j(result)["code"])


# --------------------------------------------------------------------------------------------- views (lazy import)


def case_action(action: str, expected_version: int, **kw: Any) -> Any:
    from meridian.domain.views import CaseAction

    data: dict[str, Any] = {"action": action, "expected_version": expected_version}
    data.update(kw)
    return CaseAction.model_validate(data)


def followup_choice(channel: str, destination: str, window: str) -> Any:
    from meridian.domain.views import FollowUpChoice

    return FollowUpChoice.model_validate({"channel": channel, "destination": destination, "window": window})


def activity_in(kind: str, outcome: str, expected_version: int, note: str | None = None) -> Any:
    from meridian.domain.views import ActivityIn

    return ActivityIn.model_validate(
        {"kind": kind, "outcome": outcome, "note": note, "expected_version": expected_version}
    )


# ------------------------------------------------------------------------------------------------ threads, requests


def new_thread(
    tx: UnitOfWork, *, customer_text: str | None = None, at: dt.datetime = NOW, run_tag: str = "live"
) -> tuple[ThreadId, int]:
    thread = _THREAD.validate_python(str(uuid4()))
    tx.core.conversations.insert(
        ConversationRow.model_validate(
            {
                "thread_id": str(thread),
                "demo_session": "test",
                "run_tag": run_tag,
                "agent_version": "test-0",
                "started_at": at,
            }
        )
    )
    last = tx.core.messages.append(thread, "assistant", TEXTS[TextId.GREETING], at)
    if customer_text is not None:
        last = tx.core.messages.append(thread, "customer", customer_text, at)
    return thread, last


def identity(customer: CustomerId | None = None) -> IdentityState:
    if customer is None:
        return IdentityState(
            status="not_checked",
            customer_id=None,
            masked_hint=None,
            code_expires_at=None,
            tries_left=3,
            codes_sent=0,
            verified_at=None,
        )
    return IdentityState(
        status="verified",
        customer_id=customer,
        masked_hint=None,
        code_expires_at=None,
        tries_left=3,
        codes_sent=1,
        verified_at=NOW,
    )


def request(
    thread: ThreadId,
    reason: HandoffReason,
    *,
    priority: Priority | None = None,
    trigger: str = "escalation",
    turn: TurnId | None = None,
    verified_customer: CustomerId | None = None,
    change_request: ChangeRequestDraft | None = None,
    safety_kind: Any = None,
) -> HandoffRequest:
    return HandoffRequest.model_validate(
        {
            "thread_id": thread,
            "turn_id": turn or new_turn(),
            "reason": reason,
            "priority": priority or priority_for(reason),
            "rule_id": f"TEST.{reason.value}",
            "trigger": trigger,
            "identity": identity(verified_customer),
            "change_request": change_request,
            "safety_kind": safety_kind,
        }
    )


def window_change(start: dt.datetime | None = None) -> ChangeRequestDraft:
    return ChangeRequestDraft(
        appointment_id=1,
        change="move",
        wanted_text="Monday morning",
        windows_shown=(),
        hours_before=2.0,
        window_start=start or dt.datetime(2026, 10, 16, 12, 0, tzinfo=CHI),
    )


def ctx(thread: ThreadId, turn: TurnId, now: dt.datetime = NOW) -> TurnContext:
    ids = TurnIds.model_validate(
        {
            "thread_id": str(thread),
            "turn_id": str(turn),
            "request_id": str(uuid4()),
            "run_tag": "live",
            "run_id": None,
            "agent_version": "test-0",
        }
    )
    started = time.monotonic()
    return TurnContext(
        ids=ids,
        budget=TurnBudget(started=started, deadline=started + 60.0),
        now=now,
        demo_session="test",
        span=SpanHandle(turn_id=turn, trace_id=None),
    )


def state_for(tx: UnitOfWork, thread: ThreadId) -> ConversationState:
    anchor = tx.core.messages.handoff_anchor(thread)
    turn_input = TurnInput(
        turn_id=new_turn(), message_id=anchor, kind="text", text_store="synthetic", received_at=NOW
    )
    return ConversationState(
        thread_id=thread, turn_input=turn_input, identity=tx.core.reads.identity_state(thread)
    )


def summary_of(tx: UnitOfWork, case_ref: CaseRef) -> CaseSummary:
    row = tx.cases.cases.get(case_ref)
    promise = tx.cases.promises.current(case_ref)
    follow = tx.cases.followups.get(case_ref)
    assert row is not None and promise is not None
    return CaseSummary(
        case_ref=case_ref,
        reason=row.reason,
        priority=row.priority,
        state=row.lifecycle,
        created_at=row.created_at,
        promise=promise.promise,
        followup=None
        if follow is None
        else FollowUp(
            channel=follow.channel,
            destination_label=follow.destination_label,
            on_record=follow.on_record,
            window=follow.window,
            saved_line=follow.saved_line,
        ),
        version=row.version,
        seed=row.seed,
        due_at=row.due_at,
    )


# ---------------------------------------------------------------------------------------------------- doubles


class StaffingDemo:
    """Double honouring cases section 6 ``presence(tx)``; records every unit of work it was handed."""

    def __init__(self) -> None:
        self.seen: list[UnitOfWork] = []

    def presence(self, tx: UnitOfWork | None = None) -> Any:
        assert tx is not None, "presence must be read inside the caller's transaction"
        self.seen.append(tx)
        return tx.cases.demo_state.get().staffing


class FlakyUow:
    """Wraps a unit-of-work factory; the first ``fail_writes`` write units of work fail at the promise insert."""

    def __init__(self, inner: Any, *, fail_writes: int) -> None:
        self._inner = inner
        self._left = fail_writes
        self.write_attempts = 0

    @contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[Any]:
        with self._inner(write=write, exclusive=exclusive) as tx:
            if write:
                self.write_attempts += 1
                if self._left > 0:
                    self._left -= 1

                    def _boom(*_a: object, **_k: object) -> int:
                        raise RuntimeError("injected")

                    tx.cases.promises.insert = _boom
            yield tx


def guidance(reason: HandoffReason) -> StaffGuidance:
    text = STAFF_GUIDANCE_FOR[reason][0]
    return StaffGuidance(
        passage_id=PassageId(f"internal/agent_discretion_notes.md#{list(STAFF_GUIDANCE_FOR).index(reason)}"),
        file="internal/agent_discretion_notes.md",
        section="Agents may NOT",
        version_label="undated",
        text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
    )


class BlockRecorder:
    """Stands in for ``ReplyComposer.handoff_block``; records the results it was given and the blocks it returned."""

    def __init__(self) -> None:
        self.results: list[Any] = []
        self.blocks: list[Any] = []

    def __call__(self, result: Any) -> Any:
        from meridian.domain.blocks import LiveQueuedBlock, Speaker

        self.results.append(result)
        block = LiveQueuedBlock(
            block_id=f"blk-{len(self.results)}",
            speaker=Speaker(kind="assistant", display_name=None),
            at=NOW,
            reference=str(result.case.case_ref),
            promise_text="recorded by the test double",
        )
        self.blocks.append(block)
        return block


def set_identity(tx: UnitOfWork, thread: ThreadId, status: str, customer: CustomerId | None = None) -> None:
    """Writes the identity row the service reads (``core.reads.identity_state``)."""
    tx.connection.execute(  # type: ignore[attr-defined]
        "INSERT OR REPLACE INTO identity_threads (thread_id, status, customer_id, masked_hint, channel, verified_at, "
        "updated_at) VALUES (?,?,?,NULL,NULL,?,?)",
        (
            str(thread),
            status,
            None if customer is None else str(customer),
            format_wall(NOW) if status == "verified" else None,
            format_wall(NOW),
        ),
    )


def services(
    uow: Any, *, guidance_map: Any = None, handoff_block: Any = None
) -> tuple[Any, Any, Any, StaffingDemo]:
    """``(CaseService, HandoffService, BriefAssembler, StaffingDemo)`` built with ``FixedClock(NOW)``."""
    from meridian.services.cases import CaseService
    from meridian.services.handoff import BriefAssembler, HandoffService

    clock = FixedClock(NOW)
    demo = StaffingDemo()
    cases = CaseService(uow, clock, handoff_block=handoff_block)
    kwargs: dict[str, Any] = {} if guidance_map is None else {"staff_guidance": guidance_map}
    handoff = HandoffService(uow, cases, demo, clock, **kwargs)
    by_id = (
        None if guidance_map is None else {g.passage_id: g for items in guidance_map.values() for g in items}
    )
    return cases, handoff, BriefAssembler(staff_guidance=by_id), demo


# --------------------------------------------------------------------------------------------------- counting


def count(tx: UnitOfWork, sql: str, *params: object) -> int:
    return int(tx.connection.execute(sql, params).fetchone()[0])  # type: ignore[attr-defined]


def rows_for_thread(tx: UnitOfWork, thread: ThreadId) -> dict[str, int]:
    """The six tables a handoff writes, counted for one thread."""
    t = str(thread)
    return {
        "cases": count(tx, "SELECT COUNT(*) FROM cases WHERE thread_id = ?", t),
        "case_events": count(
            tx,
            "SELECT COUNT(*) FROM case_events WHERE case_ref IN (SELECT case_ref FROM cases WHERE thread_id = ?)",
            t,
        ),
        "promises": count(
            tx,
            "SELECT COUNT(*) FROM promises WHERE case_ref IN (SELECT case_ref FROM cases WHERE thread_id = ?)",
            t,
        ),
        "actions": count(tx, "SELECT COUNT(*) FROM actions WHERE thread_id = ? AND kind = 'case_opened'", t),
        "events": count(tx, "SELECT COUNT(*) FROM events WHERE stream = ?", str(thread_stream(thread))),
        "lookup_log": count(tx, "SELECT COUNT(*) FROM lookup_log WHERE thread_id = ?", t),
    }


def contact_of(tx: UnitOfWork, customer: CustomerId = OMAR) -> tuple[str, str, str]:
    """``(phone, phone digits only, email)`` read from the issued data at run time."""
    row = tx.core.reads.customer(customer)
    assert row is not None and row.email is not None
    return row.phone, re.sub(r"\D", "", row.phone), row.email


# ---------------------------------------------------------------------------------------------- direct case builders


def _insert_case(
    tx: UnitOfWork,
    *,
    case_ref: CaseRef,
    thread: ThreadId,
    reason: HandoffReason,
    priority: Priority,
    created: dt.datetime,
    customer: CustomerId | None,
    lifecycle: str = "unassigned",
    owner_role: StaffRole | None = None,
    version: int = 1,
    seed: bool = False,
    safety_kind: str | None = None,
    presence: str = "nobody_online",
    turn: TurnId | None = None,
) -> None:
    promise = promise_for(reason, presence, created)  # type: ignore[arg-type]
    tx.cases.cases.insert(
        CaseRow.model_validate(
            {
                "case_ref": str(case_ref),
                "thread_id": str(thread),
                "turn_id": None if turn is None else str(turn),
                "customer_id": None if customer is None else str(customer),
                "reason": reason,
                "priority": priority,
                "rule_id": f"TEST.{reason.value}",
                "trigger": "escalation",
                "lifecycle": lifecycle,
                "owner_role": owner_role,
                "owner_since": created if owner_role else None,
                "due_at": promise.due_at,
                "version": version,
                "seed": seed,
                "safety_kind": safety_kind,
                "created_at": created,
                "updated_at": created,
                "resolved_at": created if lifecycle in ("resolved", "closed_unresolved") else None,
                "queued_at": created if lifecycle == "live_queued" else None,
            }
        )
    )
    tx.cases.promises.insert(case_ref, promise, created)
    tx.cases.case_events.append(
        CaseEventRow(
            case_ref=case_ref,
            kind="case_opened",
            actor_role="ai",
            detail={"reason": reason.value},
            at=created,
        )
    )
    turn_id = turn or new_turn()
    tx.core.actions.record(
        CompletedAction(
            key=ActionKey(
                thread_id=thread, turn_id=turn_id, kind=ActionKind.CASE_OPENED, record_id=str(case_ref)
            ),
            kind=ActionKind.CASE_OPENED,
            records={"case": str(case_ref)},
            at=created,
        )
    )
    tx.core.events.append(
        thread_stream(thread),
        StreamEvent(
            type="case_created", payload={"case_ref": str(case_ref), "thread_id": str(thread)}, at=created
        ),
    )


def _seed_case(
    tx: UnitOfWork,
    n: int,
    reason: HandoffReason,
    created: dt.datetime,
    customer: str | None,
    *,
    follow: tuple[str, str, bool, str, str] | None = None,
    message: str | None = None,
    safety_kind: str | None = None,
    lookup: bool = False,
) -> CaseRef:
    thread, last = new_thread(tx, customer_text=message, at=created, run_tag="seed")
    case_ref = ref(n)
    _insert_case(
        tx,
        case_ref=case_ref,
        thread=thread,
        reason=reason,
        priority=priority_for(reason),
        created=created,
        customer=None if customer is None else _CUSTOMER.validate_python(customer),
        seed=True,
        safety_kind=safety_kind,
    )
    if follow is not None:
        channel, label, on_record, window, line = follow
        tx.cases.followups.upsert(
            FollowupRow(
                case_ref=case_ref,
                thread_id=thread,
                channel=channel,  # type: ignore[arg-type]
                destination_label=label,
                on_record=on_record,
                window=window,  # type: ignore[arg-type]
                saved_line=line,
                updated_at=created,
            )
        )
    if lookup:
        tx.core.lookup_log.append(
            LookupEntry(
                tool="read_invoices",
                record_ids=("INV-204411",),
                passage_ids=(),
                result_seen=json.dumps({"amount_cents": 47800, "balance_cents": 47800}),
                message_id=last,
                turn_id=new_turn(),
            )
        )
    from meridian.services.handoff import BriefAssembler

    lookups = tx.core.lookup_log.for_thread(thread)
    brief = BriefAssembler().assemble(summary_of(tx, case_ref), state_for(tx, thread), lookups)
    tx.cases.briefs.upsert(brief.model_copy(update={"status": "ready"}), created)
    return case_ref


def seed_shaped(tx: UnitOfWork) -> dict[int, CaseRef]:
    """The four cases of cases.md section 7, inserted directly (refs MHC-C-0005 to 0008)."""

    def day(d: int, h: int, m: int) -> dt.datetime:
        return dt.datetime(2026, 10, d, h, m, tzinfo=CHI)

    return {
        5: _seed_case(
            tx,
            5,
            HandoffReason.REFUND,
            day(13, 10, 0),
            "MHC-10023",
            follow=("email", "the email on record", True, "any", "Follow-up saved: email."),
        ),
        6: _seed_case(
            tx,
            6,
            HandoffReason.COMPLAINT_OR_MANAGER,
            day(16, 9, 14),
            "MHC-10052",
            follow=(
                "phone",
                "the number ending in 52",
                True,
                "afternoon",
                "Follow-up saved: phone, afternoons.",
            ),
        ),
        7: _seed_case(
            tx,
            7,
            HandoffReason.BILLING_DISPUTE,
            day(16, 9, 24),
            "MHC-10002",
            follow=("phone", "the number ending in 02", True, "morning", "Follow-up saved: phone, mornings."),
            message=OMAR_MESSAGE,
            lookup=True,
        ),
        8: _seed_case(
            tx, 8, HandoffReason.SAFETY, day(16, 9, 56), None, safety_kind="gas", message="I smell gas."
        ),
    }


def display_case(tx: UnitOfWork) -> CaseRef:
    """The MHC-C-0007 shape with the OpenAPI example's own inputs (created 14:14, read at ``DISPLAY_NOW``)."""
    created = dt.datetime(2026, 10, 16, 14, 14, tzinfo=CHI)
    return _seed_case(
        tx,
        7,
        HandoffReason.BILLING_DISPUTE,
        created,
        "MHC-10002",
        follow=("phone", "the number ending in 02", True, "morning", "Follow-up saved: phone, mornings."),
        message=OMAR_MESSAGE,
        lookup=True,
    )


def wp7(tx: UnitOfWork) -> tuple[ThreadId, HandoffRequest]:
    """WP-7: the refund request (text from worked-pairs.md)."""
    thread, _ = new_thread(
        tx,
        customer_text="I want a full refund on the repair. It didn't fix anything and I had to call another company.",
    )
    return thread, request(thread, HandoffReason.REFUND, verified_customer=OMAR)


def wp4(tx: UnitOfWork) -> tuple[ThreadId, HandoffRequest]:
    """WP-4: the fee-bearing change for MHC-57204 (window starts at 12:00 today)."""
    thread, _ = new_thread(tx, customer_text="Something came up. Can I move my visit?")
    return thread, request(
        thread,
        HandoffReason.FEE_BEARING_CHANGE,
        verified_customer=_CUSTOMER.validate_python("MHC-57204"),
        change_request=window_change(),
    )


def case_in_state(
    tx: UnitOfWork,
    *,
    lifecycle: str,
    owner_role: StaffRole | None,
    live_state: str,
    staffing: str,
    reason: HandoffReason = HandoffReason.CUSTOMER_REQUESTED_PERSON,
    version: int = 3,
    customer: str | None = None,
) -> CaseRef:
    """A fresh thread and case inserted directly in the given state (Appendix B rows)."""
    thread, _ = new_thread(tx, customer_text="I need a person.")
    case_ref = tx.cases.refs.next_case_ref()
    _insert_case(
        tx,
        case_ref=case_ref,
        thread=thread,
        reason=reason,
        priority=priority_for(reason),
        created=NOW,
        customer=None if customer is None else _CUSTOMER.validate_python(customer),
        lifecycle=lifecycle,
        owner_role=owner_role,
        version=version,
        presence="simulated_on_shift" if lifecycle == "live_queued" else "nobody_online",
        safety_kind="gas" if reason is HandoffReason.SAFETY else None,
    )
    if live_state == "joined":
        tx.core.conversations.set_controller(
            thread,
            Controller(kind="human", representative_name="Riley", case_ref=case_ref),
            live_state="joined",
            live_since=NOW,
        )
    elif live_state != "not_live":
        tx.core.conversations.set_live_state(thread, live_state, NOW)
    tx.cases.demo_state.set_staffing(staffing)
    return case_ref


def thread_of(tx: UnitOfWork, case_ref: CaseRef) -> ThreadId:
    row = tx.cases.cases.get(case_ref)
    assert row is not None
    return row.thread_id


__all__ = ["TempStore"]
