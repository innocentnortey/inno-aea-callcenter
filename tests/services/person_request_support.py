"""AEA-42 test support: doubles and database seeding for CON-4 and CON-5 (synthetic; no model, no network).

`RecordingHandoffService` honours DO-4 section 7 (one open case per thread, idempotent, no turn row) over AEA-10's
repositories; AEA-29's real rows are its own tests'. `RecordingComposer` builds the cards and the panel from the stored
promise rows, the way AEA-21's ReplyComposer does, without owning any sentence the policy table does not own.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.rows import CaseRow, ConversationRow, FollowupRow
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.blocks import (
    FollowUpOptions,
    HandoffBlock,
    LiveQueuedBlock,
    SettledIdentity,
    SettledReplying,
    SettledRequest,
    SettledView,
    Speaker,
    Write,
)
from meridian.domain.common import CustomerId, FollowUp, Presence, ThreadId, TurnId
from meridian.domain.handoff import CaseSummary, HandoffRequest, HandoffResult
from meridian.domain.identity import IdentityState
from meridian.domain.state import Controller
from meridian.domain.turn import TurnContext
from meridian.policy.handoff import promise_for
from meridian.policy.texts import TEXTS, TextId, render
from meridian.services.person_request import PersonRequest, PersonRequestService
from tests.fakes.clock import WORKED_PAIRS_NOW, FixedClock
from tests.fakes.trace import InMemoryTraceSink
from tests.fixtures.sqlite import TempStore

NOW = WORKED_PAIRS_NOW
WALL_T0 = datetime(2026, 10, 21, 15, 0, tzinfo=UTC)
AGENT = "test-agent-0"
CUSTOMER = "MHC-10002"
HINT = "the phone ending in 02"
_WINDOW_WORD = {"morning": "mornings", "afternoon": "afternoons", "any": "any time"}


class WallClock:
    """A wall clock a test can move."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self.now = self.now + timedelta(seconds=seconds)


def open_thread(
    store: TempStore,
    *,
    demo_session: str,
    now: datetime = NOW,
    last_customer_wall_at: datetime | None = None,
) -> ThreadId:
    thread_id = ThreadId(str(uuid.uuid4()))
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(
            ConversationRow(
                thread_id=thread_id,
                demo_session=demo_session,
                run_tag="live",
                agent_version=AGENT,
                started_at=now,
                started_wall_at=WALL_T0,
                staffing_at_start="nobody_online",
                last_customer_wall_at=last_customer_wall_at,
            )
        )
        tx.core.messages.append(thread_id, "assistant", "Hello, I am the automated assistant.", now)
        tx.commit()
    return thread_id


def verify_thread(store: TempStore, thread_id: ThreadId, *, now: datetime = NOW) -> None:
    conn = sqlite3.connect(store.db_path)
    try:
        conn.execute(
            "INSERT INTO identity_threads (thread_id, status, customer_id, masked_hint, channel, verified_at, "
            "updated_at) VALUES (?, 'verified', ?, ?, 'phone', ?, ?)",
            (str(thread_id), CUSTOMER, HINT, format_wall(now), format_wall(now)),
        )
        conn.commit()
    finally:
        conn.close()
    with store.uow(write=True) as tx:
        tx.core.actions.record(
            CompletedAction(
                key=ActionKey(
                    thread_id=thread_id,
                    turn_id=TurnId(str(uuid.uuid4())),
                    kind=ActionKind.VERIFIED,
                    record_id=CUSTOMER,
                ),
                kind=ActionKind.VERIFIED,
                records={"customer": CUSTOMER},
                at=now,
            )
        )
        tx.commit()


def end_thread(store: TempStore, *, demo_session: str) -> str:
    """A fresh id with no conversations row and a demo_reset tombstone for this session."""
    thread_id = str(uuid.uuid4())
    conn = sqlite3.connect(store.db_path)
    try:
        conn.execute(
            "INSERT INTO ended_threads (thread_id, demo_session, ended_wall_at, reason, reset_id) "
            "VALUES (?, ?, ?, 'demo_reset', 'reset-test')",
            (thread_id, demo_session, format_wall(WALL_T0)),
        )
        conn.commit()
    finally:
        conn.close()
    return thread_id


def customer_contact(store: TempStore) -> tuple[str, str]:
    """The seeded customer's full phone and email, for absence checks only (never written into a test file)."""
    with store.uow() as tx:
        row = tx.core.reads.customer(CustomerId(CUSTOMER))
    assert row is not None and row.phone is not None and row.email is not None
    return row.phone, row.email


class RecordingHandoffService:
    """Honours DO-4 section 7: one open case per thread, idempotent, no turn row."""

    def __init__(self, uow: Any, *, presence: Presence = "nobody_online", fail: bool = False) -> None:
        self._uow = uow
        self.presence: Presence = presence
        self.fail = fail
        self.calls: list[tuple[HandoffRequest, TurnContext]] = []

    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult:
        self.calls.append((req, ctx))
        if self.fail:
            raise RuntimeError("case write failed")
        with self._uow(write=True) as tx:
            existing = tx.cases.cases.get_for_thread_open(req.thread_id)
            if existing is None:
                ref = tx.cases.refs.next_case_ref()
                promise = promise_for(req.reason, self.presence, ctx.now)
                tx.cases.cases.insert(
                    CaseRow(
                        case_ref=ref,
                        thread_id=req.thread_id,
                        turn_id=req.turn_id,
                        reason=req.reason,
                        priority=req.priority,
                        rule_id=req.rule_id,
                        trigger=req.trigger,
                        lifecycle="live_queued" if promise.live_queued else "unassigned",
                        due_at=promise.due_at,
                        created_at=ctx.now,
                        updated_at=ctx.now,
                    )
                )
                tx.cases.promises.insert(ref, promise, ctx.now)
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
                        at=ctx.now,
                    )
                )
                created = True
            else:
                ref = existing.case_ref
                found = [
                    a
                    for a in tx.core.actions.for_thread(req.thread_id)
                    if a.kind is ActionKind.CASE_OPENED and a.key.record_id == str(ref)
                ]
                action = found[0]
                created = False
            row = tx.cases.cases.get(ref)
            current = tx.cases.promises.current(ref)
            assert row is not None and current is not None
            summary = CaseSummary(
                case_ref=ref,
                reason=row.reason,
                priority=row.priority,
                state=row.lifecycle,
                created_at=row.created_at,
                promise=current.promise,
                followup=None,
                version=row.version,
                due_at=row.due_at,
            )
            tx.commit()
        return HandoffResult(case=summary, created=created, action=action, alert=None)


class RecordingComposer:
    """Builds the card and the panel from stored values; records its calls."""

    def __init__(self) -> None:
        self.block_calls: list[HandoffResult] = []
        self.view_calls: list[tuple[Settled, IdentityState, Controller]] = []

    def handoff_block(self, result: HandoffResult) -> HandoffBlock | LiveQueuedBlock:
        self.block_calls.append(result)
        ref = result.case.case_ref
        p = result.case.promise
        speaker = Speaker(kind="assistant", display_name="Meridian assistant")
        block_id = f"blk-{result.action.key.turn_id}-handoff"
        if p.live_queued:
            return LiveQueuedBlock(
                block_id=block_id,
                speaker=speaker,
                at=result.action.at,
                reference=str(ref),
                promise_text=p.text,
            )
        variant: Literal["nobody_online", "refund", "staffed"] = {
            "R26.refund": "refund",
            "R26.staffed": "staffed",
        }.get(p.policy_row, "nobody_online")  # type: ignore[assignment]
        return HandoffBlock(
            block_id=block_id,
            speaker=speaker,
            at=result.action.at,
            card_id=f"handoff-{ref}",
            options=(),
            answered=None,
            reference=str(ref),
            variant=variant,
            promise_text=p.text,
            due_at=p.due_at,
            due_label=p.due_label,
            extra_lines=p.extra_lines,
            followup_chooser=FollowUpOptions(
                legend=TEXTS[TextId.FOLLOWUP_LEGEND], channels=(), windows=(), general_only=True
            ),
        )

    def settled_view(self, settled: Settled, identity: IdentityState, controller: Controller) -> SettledView:
        self.view_calls.append((settled, identity, controller))
        oc = settled.open_case
        request = (
            None
            if oc is None
            else SettledRequest(
                reference=str(oc.case_ref),
                promise_text=oc.promise.text,
                due_at=oc.promise.due_at,
                due_label=oc.promise.due_label,
                extra_lines=oc.promise.extra_lines,
                live_queued=oc.live_queued,
                followup=oc.followup,
            )
        )
        status: Any = "not_checked" if identity.status == "located" else identity.status
        hint = identity.masked_hint if identity.status in ("code_sent", "verified") else None
        return SettledView(
            visit=None,
            request=request,
            identity=SettledIdentity(status=status, hint=hint),
            replying=SettledReplying(
                kind=controller.kind,
                display_name=controller.representative_name if controller.kind == "human" else None,
            ),
            actions=tuple(
                Write(
                    kind=a.kind.value,
                    summary=a.kind.value,
                    turn_id=str(a.key.turn_id),
                    at=a.at,
                )
                for a in settled.actions
            ),
        )


class RecordingCaseService:
    """open_case_for_thread and set_followup over AEA-10's repositories; stores no phone or email."""

    def __init__(self, uow: Any) -> None:
        self._uow = uow
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.refuse: object | None = None

    def open_case_for_thread(self, thread_id: ThreadId) -> CaseRow | None:
        self.calls.append(("open_case_for_thread", (thread_id,)))
        with self._uow() as tx:
            row: CaseRow | None = tx.cases.cases.get_for_thread_open(thread_id)
        return row

    def set_followup(self, thread_id: ThreadId, choice: Any, now: datetime) -> Any:
        self.calls.append(("set_followup", (thread_id, choice, now)))
        if self.refuse is not None:
            return self.refuse
        window = _WINDOW_WORD[choice.window]
        with self._uow(write=True) as tx:
            case = tx.cases.cases.get_for_thread_open(thread_id)
            assert case is not None
            if choice.channel == "phone" and choice.destination == "on_record":
                identity = tx.core.reads.identity_state(thread_id)
                assert identity.customer_id is not None
                customer = tx.core.reads.customer(identity.customer_id)
                assert customer is not None
                digits = "".join(ch for ch in customer.phone if ch.isdigit())[-2:]
                label = f"the number ending in {digits}"
                line = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window=window)
            else:
                label = "a general contact"
                channel_word = "phone call" if choice.channel == "phone" else "email"
                line = f"Follow-up saved: {channel_word}, {window}."
            followup = FollowUp(
                channel=choice.channel,
                destination_label=label,
                on_record=choice.destination == "on_record",
                window=choice.window,
                saved_line=line,
            )
            tx.cases.followups.upsert(
                FollowupRow(
                    case_ref=case.case_ref,
                    thread_id=thread_id,
                    channel=followup.channel,
                    destination_label=label,
                    destination=choice.destination,
                    on_record=followup.on_record,
                    window=followup.window,
                    saved_line=line,
                    updated_at=now,
                )
            )
            tx.commit()
        return followup


@dataclass(frozen=True)
class ClockViewStub:
    now: datetime
    label: str
    date_label: str


class FakeDemoService:
    def __init__(self, clock: FixedClock) -> None:
        self._clock = clock
        self.calls = 0

    def clock_view(self) -> ClockViewStub:
        self.calls += 1
        return ClockViewStub(
            now=self._clock.now(),
            label="Fri Oct 16, 2026 · 10:00 am",
            date_label="Fri Oct 16, 2026 (demo date)",
        )


def make_service(
    store: TempStore,
    *,
    handoff: Any,
    composer: Any,
    trace: Any = None,
    clock: FixedClock | None = None,
    wall: Callable[[], datetime] | None = None,
) -> PersonRequestService:
    return PersonRequestService(
        store.uow,
        handoff,
        composer,
        trace if trace is not None else InMemoryTraceSink(),
        clock if clock is not None else FixedClock(),
        wall if wall is not None else WallClock(WALL_T0),
    )


def person_request(thread_id: ThreadId, *, demo_session: str, turn_id: TurnId | None = None) -> PersonRequest:
    return PersonRequest(
        thread_id=thread_id,
        turn_id=turn_id if turn_id is not None else TurnId(str(uuid.uuid4())),
        request_id=_request_id(),
        demo_session=demo_session,
        run_tag="live",
        run_id=None,
    )


def _request_id() -> Any:
    from meridian.domain.common import RequestId

    return RequestId(str(uuid.uuid4()))
