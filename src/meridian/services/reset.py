"""Demo reset and demo seed (AEA-31; stage7/cases.md §7, CAS-1…3, CAS-24).

ResetService restores the demo all-or-nothing; seed_demo writes the four seed cases; seed_first_boot loads them once.
Adapters arrive as injected callables (DO-3 S-3); this module writes no SQL.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Protocol
from zoneinfo import ZoneInfo

from pydantic import Field

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import (
    CaseRow,
    ConversationRow,
    FollowupRow,
    ResetEventRow,
    SeedEventRow,
    StreamEvent,
    case_stream,
    thread_stream,
)
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import (
    CaseRef,
    CustomerId,
    InvoiceId,
    MeridianModel,
    RequestId,
    SafetyKind,
    ThreadId,
    TurnId,
)
from meridian.domain.handoff import Brief, BriefExtraction, CaseSummary, FollowUp, HandoffReason, Quote
from meridian.domain.identity import IdentityState
from meridian.domain.staff import DemoRole, LoginSessionId
from meridian.domain.state import ConversationState
from meridian.domain.tools import LookupEntry, LookupRow
from meridian.domain.turn import CheckResult, TurnInput
from meridian.policy.handoff import case_due_at, priority_for, promise_for
from meridian.policy.texts import TEXTS, TextId, render
from meridian.ports.runtime import UnitOfWork, UnitOfWorkFactory
from meridian.services.reset_gate import ResetGate

_log = logging.getLogger(__name__)

CHICAGO = ZoneInfo("America/Chicago")
SEED_DEMO_SESSION = "demo-seed"  # conversations.demo_session of seed threads; no login session matches it
SEED_AGENT_VERSION = "demo-seed"  # conversations.agent_version of seed threads
SEED_COUNT = 4


class ResetClock(
    MeridianModel
):  # = OpenAPI DemoClock; same fields as AEA-30's ClockView (cases A-2, plan R-3)
    now: datetime
    label: str
    date_label: str


class ResetDone(MeridianModel):  # = OpenAPI ResetResponse (CAS-31)
    ok: Literal[True] = True
    open_chats_ended: int = Field(ge=0)
    roles_reset: int = Field(ge=0)
    clock: ResetClock


class ResetFailed(MeridianModel):
    code: Literal["RESET_FAILED"] = "RESET_FAILED"


@dataclass(frozen=True)
class SeedCase:
    """One row of cases.md §7's seed table (CAS-24)."""

    ref: str
    reason: HandoffReason
    rule_id: str
    trigger: Literal["escalation", "safety"]
    safety_kind: SafetyKind | None
    customer_id: str | None  # issued customer (None = unmatched caller)
    invoice_id: str | None  # read_invoices lookup row when set
    created_at: datetime  # Chicago, before DEMO_START
    outcome: Literal["handed_off", "safety_reply"]
    alert: Literal["supervisor_now"] | None
    messages: tuple[str, ...]  # fixed customer messages, in order
    needs: tuple[str, ...]  # heading 2 quotes (each an exact substring of one message)
    claims: tuple[str, ...]  # heading 4 quotes
    open_decision: str  # heading 7 (<= 200 chars)
    followup_window: Literal["morning"] | None  # phone follow-up on record (MHC-C-0007 only)


SEED_CASES: tuple[SeedCase, ...] = (
    SeedCase(
        ref="MHC-C-0005",
        reason=HandoffReason.REFUND,
        rule_id="R24.refund",
        trigger="escalation",
        safety_kind=None,
        customer_id="MHC-94339",
        invoice_id="INV-200037",
        created_at=datetime(2026, 10, 13, 10, 0, tzinfo=CHICAGO),
        outcome="handed_off",
        alert=None,
        messages=(
            "I paid invoice INV-200037 for a condensate drain clearing in August, and the leak came back two weeks later.",
            "I would like a refund for that repair.",
        ),
        needs=("I would like a refund for that repair",),
        claims=("the leak came back two weeks later",),
        open_decision="Decide whether INV-200037 gets a refund or a free return visit for the leak.",
        followup_window=None,
    ),
    SeedCase(
        ref="MHC-C-0006",
        reason=HandoffReason.COMPLAINT_OR_MANAGER,
        rule_id="R24.complaint_or_manager",
        trigger="escalation",
        safety_kind=None,
        customer_id="MHC-39394",
        invoice_id=None,
        created_at=datetime(2026, 10, 16, 9, 14, tzinfo=CHICAGO),
        outcome="handed_off",
        alert=None,
        messages=(
            "The technician who came to my house last month was rude to my mother and left before the job was finished.",
            "I want to talk to a manager about how we were treated.",
        ),
        needs=("I want to talk to a manager about how we were treated",),
        claims=("was rude to my mother", "left before the job was finished"),
        open_decision="Decide who calls the customer back about the technician's conduct, and what to offer.",
        followup_window=None,
    ),
    SeedCase(
        ref="MHC-C-0007",
        reason=HandoffReason.BILLING_DISPUTE,
        rule_id="R24.billing_dispute",
        trigger="escalation",
        safety_kind=None,
        customer_id="MHC-10002",
        invoice_id="INV-204411",
        created_at=datetime(2026, 10, 16, 9, 24, tzinfo=CHICAGO),
        outcome="handed_off",
        alert=None,
        messages=(
            "My invoice INV-204411 has a $144.00 after-hours dispatch charge on it.",
            "Nobody told me the visit would be after hours, and I want that charge taken off.",
        ),
        needs=("I want that charge taken off",),
        claims=("Nobody told me the visit would be after hours",),
        open_decision="Decide whether to remove or reduce the after-hours dispatch charge on INV-204411.",
        followup_window="morning",
    ),
    SeedCase(
        ref="MHC-C-0008",
        reason=HandoffReason.SAFETY,
        rule_id="R5.gas",
        trigger="safety",
        safety_kind=SafetyKind.GAS,
        customer_id=None,
        invoice_id=None,
        created_at=datetime(2026, 10, 16, 9, 56, tzinfo=CHICAGO),
        outcome="safety_reply",
        alert="supervisor_now",
        messages=("I smell gas near my furnace.",),
        needs=("I smell gas near my furnace",),
        claims=(),
        open_decision="Call back to confirm the customer is safe and arrange an emergency visit.",
        followup_window=None,
    ),
)


def _check_seed_table() -> None:
    """A bad edit to the seed table fails at import, not in the demo."""
    expected = ("MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008")
    if tuple(s.ref for s in SEED_CASES) != expected:
        raise RuntimeError("seed table invalid: refs")
    for seed in SEED_CASES:
        quotes = (*seed.needs, *seed.claims)
        ok = (
            all(any(q in m for m in seed.messages) for q in quotes)
            and 1 <= len(seed.needs) <= 2
            and len(seed.claims) <= 5
            and len(seed.open_decision) <= 200
            and all(len(q) <= 300 for q in quotes)
        )
        if not ok:
            raise RuntimeError(f"seed table invalid: {seed.ref}")


_check_seed_table()


class _BriefAssembler(Protocol):
    """Private typing of the injected AEA-29 object (not a new seam; plan R-7)."""

    def assemble(
        self, case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]
    ) -> Brief: ...

    def attach_extraction(
        self, brief: Brief, extraction: BriefExtraction | None, check: CheckResult | None
    ) -> Brief: ...


def _quote(text: str, messages: tuple[str, ...], message_ids: list[int]) -> Quote:
    index = next(i for i, m in enumerate(messages) if text in m)
    return Quote(message_id=message_ids[index], text=text)


def _last_two_digits(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    return digits[-2:]


def seed_demo(tx: UnitOfWork, *, assembler: _BriefAssembler) -> int:
    """Write the four seed cases (cases.md §7). Never commits: the caller owns the transaction."""
    for seed in SEED_CASES:
        thread_id = ThreadId(str(uuid.uuid4()))  # never reused: ended_threads.thread_id is a primary key
        turn_id = TurnId(str(uuid.uuid4()))
        t0 = seed.created_at - timedelta(minutes=3)
        # live_state='closed' keeps seed threads out of Cleared.open_threads; run_tag='seed' out of live metrics.
        tx.core.conversations.insert(
            ConversationRow(
                thread_id=thread_id,
                demo_session=SEED_DEMO_SESSION,
                run_tag="seed",
                agent_version=SEED_AGENT_VERSION,
                started_at=t0,
                staffing_at_start="nobody_online",
                outcome=seed.outcome,
                live_state="closed",
            )
        )
        tx.core.messages.append(thread_id, "assistant", TEXTS[TextId.GREETING], t0)
        message_ids: list[int] = []
        message_ats: list[datetime] = []
        for i, text in enumerate(seed.messages):
            at = seed.created_at - timedelta(minutes=len(seed.messages) - i)
            mid = tx.core.messages.append(thread_id, "customer", text, at, turn_id=turn_id, kind="text")
            message_ids.append(mid)
            message_ats.append(at)

        customer = None
        if seed.customer_id:
            customer = tx.core.reads.customer(CustomerId(seed.customer_id))
            if customer is None:
                raise LookupError("seed customer missing")
        if seed.invoice_id:
            inv = tx.core.reads.invoice(InvoiceId(seed.invoice_id))
            if inv is None:
                raise LookupError("seed invoice missing")
            tx.core.lookup_log.append(
                LookupEntry(
                    tool="read_invoices",
                    record_ids=(seed.invoice_id,),
                    passage_ids=(),
                    result_seen=f"{inv.invoice_id} amount_cents={inv.amount_cents} balance_cents={inv.balance_cents}",
                    message_id=message_ids[0],
                    turn_id=turn_id,
                )
            )

        promise = promise_for(seed.reason, "nobody_online", seed.created_at)
        priority = priority_for(seed.reason)
        due = case_due_at(seed.reason, promise, None)
        ref = CaseRef(seed.ref)
        tx.cases.cases.insert(
            CaseRow(
                case_ref=ref,
                thread_id=thread_id,
                turn_id=turn_id,
                customer_id=CustomerId(seed.customer_id) if seed.customer_id else None,
                reason=seed.reason,
                priority=priority,
                rule_id=seed.rule_id,
                trigger=seed.trigger,
                lifecycle="unassigned",
                due_at=due,
                seed=True,
                safety_kind=seed.safety_kind.value if seed.safety_kind else None,
                alert=seed.alert,
                created_at=seed.created_at,
                updated_at=seed.created_at,
            )
        )
        tx.cases.promises.insert(ref, promise, seed.created_at)

        followup: FollowUp | None = None
        if seed.followup_window:
            if customer is None:  # only MHC-C-0007 has a window, and it names a customer
                raise LookupError("seed follow-up needs a customer")
            digits = _last_two_digits(customer.phone)
            label = f"the number ending in {digits}"
            line = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window="mornings")
            tx.cases.followups.upsert(
                FollowupRow(
                    case_ref=ref,
                    thread_id=thread_id,
                    channel="phone",
                    destination_label=label,
                    destination=None,
                    on_record=True,
                    window="morning",
                    saved_line=line,
                    updated_at=seed.created_at,
                )
            )
            followup = FollowUp(
                channel="phone", destination_label=label, on_record=True, window="morning", saved_line=line
            )

        tx.core.actions.record(
            CompletedAction(
                key=ActionKey(
                    thread_id=thread_id, turn_id=turn_id, kind=ActionKind.CASE_OPENED, record_id=seed.ref
                ),
                kind=ActionKind.CASE_OPENED,
                records={"case": seed.ref},
                at=seed.created_at,
            )
        )
        summary = CaseSummary(
            case_ref=ref,
            reason=seed.reason,
            priority=priority,
            state="unassigned",
            created_at=seed.created_at,
            promise=promise,
            followup=followup,
            version=1,
            seed=True,
            due_at=due,
        )
        if seed.customer_id:
            identity = IdentityState(
                status="verified",
                customer_id=CustomerId(seed.customer_id),
                masked_hint=None,
                code_expires_at=None,
                tries_left=3,
                codes_sent=1,
                verified_at=seed.created_at - timedelta(minutes=2),
            )
        else:
            identity = IdentityState(
                status="not_checked",
                customer_id=None,
                masked_hint=None,
                code_expires_at=None,
                tries_left=3,
                codes_sent=0,
                verified_at=None,
            )
        state = ConversationState(
            thread_id=thread_id,
            turn_input=TurnInput(
                turn_id=turn_id,
                message_id=message_ids[-1],
                kind="text",
                text_store=seed.messages[-1],
                received_at=message_ats[-1],
            ),
            settled=tx.core.settled_for(thread_id, seed.created_at),
            identity=identity,
        )
        extraction = BriefExtraction(
            needs=[_quote(q, seed.messages, message_ids) for q in seed.needs],
            claims=[_quote(q, seed.messages, message_ids) for q in seed.claims],
            open_decision=seed.open_decision,
        )
        brief = assembler.assemble(summary, state, tx.core.lookup_log.for_thread(thread_id))
        brief = assembler.attach_extraction(brief, extraction, None)
        tx.cases.briefs.upsert(brief, seed.created_at)
    return len(SEED_CASES)


def seed_first_boot(
    uow: UnitOfWorkFactory,
    seed: Callable[[UnitOfWork], int],
    now: datetime,
    *,
    deploy_id: str | None = None,
) -> int:
    """Load the demo seed once: 4 on a store without seed rows, 0 when they exist."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("seed needs an aware wall-clock time")
    with uow(write=True) as tx:  # presence check and writes in one transaction: two starts never both seed
        if tx.cases.records.seed_rows_present():
            return 0
        n = seed(tx)
        tx.cases.records.seed_event(
            SeedEventRow(
                seed_event_id=str(uuid.uuid4()), at_wall=now, reset_id=None, deploy_id=deploy_id, seed_count=n
            )
        )
        tx.commit()
        return n


class ResetService:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        gate: ResetGate,
        restore_working_copy: Callable[[UnitOfWork], None],
        clear_checkpoints: Callable[[], AbstractContextManager[None]],
        seed_demo: Callable[[UnitOfWork], int],
        *,
        format_clock: Callable[[datetime], tuple[str, str]],
    ) -> None:
        self._uow = uow
        self._gate = gate
        self._restore = restore_working_copy
        self._clear_checkpoints = clear_checkpoints
        self._seed = seed_demo
        self._format_clock = format_clock

    def reset(
        self,
        now: datetime,
        *,
        request_id: RequestId,
        session_id: LoginSessionId | None,
        role: DemoRole | None,
    ) -> ResetDone | ResetFailed:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("reset needs an aware wall-clock time")
        with self._gate.hold():  # ResetAlreadyRunning propagates; the gate is released on every exit
            return self._run(now, request_id, session_id, role)

    def _run(
        self, now: datetime, request_id: RequestId, session_id: LoginSessionId | None, role: DemoRole | None
    ) -> ResetDone | ResetFailed:
        label, date_label = self._format_clock(DEMO_START)  # before any write: nothing fallible after commit
        clock = ResetClock(now=DEMO_START, label=label, date_label=date_label)
        reset_id = str(uuid.uuid4())
        step = "begin"
        committed = False
        opened = roles = 0
        try:
            with self._uow(write=True, exclusive=True) as tx, self._clear_checkpoints():
                before = tx.cases.demo_state.get().demo_now  # pre-reset demo time for event `at`
                step = "restore"
                self._restore(tx)
                step = "clear"
                cleared = tx.core.reset.clear_demo_tables(reset_id, ended_at=now)
                step = "demo_state"
                tx.cases.demo_state.reset()
                step = "demo_reset_events"
                line = TEXTS[TextId.DEMO_RESET]
                for tid in cleared.open_threads:
                    tx.core.events.append(
                        thread_stream(tid),
                        StreamEvent(
                            type="demo_reset",
                            payload={"speaker": {"kind": "event", "display_name": None}, "line": line},
                            at=before,
                        ),
                    )
                for ref in cleared.case_streams:
                    tx.core.events.append(
                        case_stream(ref), StreamEvent(type="demo_reset", payload={"line": line}, at=before)
                    )
                step = "seed"
                n = self._seed(tx)
                step = "records"
                opened, roles = len(cleared.open_threads), cleared.roles_reset
                tx.cases.records.reset_event(
                    ResetEventRow(
                        reset_id=reset_id,
                        at_wall=now,
                        asked_by_role=role,
                        asked_by_session=str(session_id) if session_id is not None else None,
                        request_id=str(request_id),
                        restored=dict(cleared.rows_cleared),
                        open_chats_ended=opened,
                        roles_reset=roles,
                        checkpoints_cleared=True,
                    )
                )
                tx.cases.records.seed_event(
                    SeedEventRow(
                        seed_event_id=str(uuid.uuid4()), at_wall=now, reset_id=reset_id, seed_count=n
                    )
                )
                step = "commit"
                tx.commit()
                committed = True  # meridian is final from here
        except Exception as exc:
            if not committed:
                _log.warning(
                    "demo reset failed",
                    extra={"reset_id": reset_id, "step": step, "error_kind": type(exc).__name__},
                )
                return ResetFailed()
            self._mark_checkpoints_not_cleared(reset_id, exc)  # residual window
        return ResetDone(open_chats_ended=opened, roles_reset=roles, clock=clock)

    def _mark_checkpoints_not_cleared(self, reset_id: str, exc: Exception) -> None:
        _log.warning(
            "demo reset: checkpoint clear did not commit",
            extra={"reset_id": reset_id, "error_kind": type(exc).__name__},
        )
        try:
            with self._uow(write=True) as tx:
                tx.cases.records.set_checkpoints_cleared(reset_id, False)
                tx.commit()
        except Exception as e2:
            _log.warning(
                "demo reset: could not record checkpoints_cleared",
                extra={"reset_id": reset_id, "error_kind": type(e2).__name__},
            )
