"""Builders and doubles for the reply-node tests (AEA-38 plan section 6). Synthetic ids and data only."""

from __future__ import annotations

import datetime as dt
import logging
import time
import uuid
from collections.abc import Sequence
from typing import Any, cast

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.gateway import ModelGateway
from meridian.domain.actions import ActionKind, CompletedAction, Settled
from meridian.domain.common import (
    CaseRef,
    HandoffReason,
    PassageId,
    Priority,
    Promise,
    RequestId,
    ThreadId,
    ToolCallRecord,
    ToolErrorCode,
    ToolKind,
    TurnId,
)
from meridian.domain.handoff import (
    BRIEF_KEYS,
    BRIEF_ORIGINS,
    BRIEF_TITLES,
    Brief,
    BriefExtraction,
    BriefHeading,
    CaseSummary,
    HandoffResult,
)
from meridian.domain.records import FeeNote, Passage
from meridian.domain.specialists import (
    AccountResult,
    ConfirmationView,
    InvoiceLineView,
    InvoiceView,
    KnowledgePoint,
    KnowledgeResult,
    StaffNote,
    WriteResult,
)
from meridian.domain.state import ConversationState
from meridian.domain.tools import LookupEntry
from meridian.domain.turn import (
    GateDecision,
    GateKind,
    RuleMatches,
    SpanHandle,
    TurnBudget,
    TurnContext,
    TurnFacts,
    TurnIds,
    TurnInput,
)
from meridian.policy.limits import Limits
from tests.fakes import WORKED_PAIRS_NOW
from tests.unit.agent._gateway_doubles import RecordingLedger, RecordingSink, default_doubles, gateway_kwargs

THREAD = ThreadId("3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10")
TURN_1 = TurnId("0b6d1f3a-5c2e-4a71-9d84-1e2f3a4b5c61")
TURN_2 = TurnId("1c7e2a4b-6d3f-4b82-8e95-2f3a4b5c6d72")
TURN_3 = TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")
TURN_4 = TurnId("a2b4c6d8-1e3f-4a5b-8c7d-9e0f1a2b3c4d")
TURN_5 = TurnId("2d8f3b5c-7e4a-4c93-9fa6-3a4b5c6d7e83")
NOW = WORKED_PAIRS_NOW
CASE_REF = CaseRef("MHC-C-0042")


def turn_ctx(
    *, thread: ThreadId = THREAD, turn: TurnId = TURN_4, now: dt.datetime = NOW, seconds_left: float = 60.0
) -> TurnContext:
    ids = TurnIds(
        thread_id=thread,
        turn_id=turn,
        request_id=RequestId(str(uuid.uuid4())),
        run_tag="live",
        run_id=None,
        agent_version="test",
    )
    t = time.monotonic()
    return TurnContext(
        ids=ids,
        budget=TurnBudget(started=t, deadline=t + seconds_left),
        now=now,
        demo_session="demo-test",
        span=SpanHandle(turn_id=turn, trace_id="0" * 32),
    )


def run(ctx: TurnContext) -> Runtime[TurnContext]:
    return Runtime(context=ctx)


def turn_input(*, turn: TurnId = TURN_4, message_id: int = 1, text: str = "Yes, please.") -> TurnInput:
    return TurnInput(turn_id=turn, message_id=message_id, kind="text", text_store=text, received_at=NOW)


def rules(*, correction: bool = False) -> RuleMatches:
    return RuleMatches(
        safety=None,
        burning_unclear=False,
        danger_words=False,
        person=False,
        policy_trigger=None,
        rule_ids=(),
        correction=correction,
    )


def gate(kind: GateKind = GateKind.FREE_TEXT, *, correction: bool = False) -> GateDecision:
    return GateDecision(kind=kind, rules=rules(correction=correction))


def action(
    kind: ActionKind,
    record_id: str,
    *,
    turn: TurnId = TURN_3,
    records: dict[str, str] | None = None,
    before: dict[str, str] | None = None,
    after: dict[str, str] | None = None,
) -> CompletedAction:
    return CompletedAction.model_validate(
        {
            "key": {"thread_id": THREAD, "turn_id": turn, "kind": kind, "record_id": record_id},
            "kind": kind,
            "records": records or {},
            "before": before,
            "after": after,
            "at": NOW,
        }
    )


MOVED_T3 = action(
    ActionKind.MOVED,
    "159",
    records={"appointment": "159", "slot": "56", "old_slot": "159"},
    before={"date": "2026-10-22", "window": "08:00-12:00"},
    after={
        "date": "2026-10-19",
        "window": "08:00-12:00",
        "technician": "Marta Kowalski",
        "service_type": "hvac_repair",
    },
)


def booked(turn: TurnId) -> CompletedAction:
    return action(
        ActionKind.BOOKED,
        "160",
        turn=turn,
        records={"appointment": "160"},
        after={
            "date": "2026-10-20",
            "window": "12:00-16:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
        },
    )


def write_result(act: CompletedAction) -> WriteResult:
    return WriteResult(
        action=act,
        confirmation=ConfirmationView(
            date=dt.date(2026, 10, 20),
            window="12:00-16:00",
            technician="Marta Kowalski",
            fee_note=FeeNote(
                service_type="hvac_repair",
                tier="standard",
                fee_row=None,
                amount_cents=0,
                waived=True,
                line="Diagnostic fee waived (member)",
            ),
        ),
    )


def tool_record(*, error: ToolErrorCode | None = None) -> ToolCallRecord:
    return ToolCallRecord(
        tool_call_id="call-1",
        name="kb_search",
        kind=ToolKind.KB_SEARCH,
        outcome="failed" if error else "ok",
        error=error,
        record_ids=(),
        passage_ids=(),
        lookup_id=None,
        elapsed_ms=5,
    )


def passage(file: str, n: int, text: str) -> Passage:
    return Passage(
        passage_id=PassageId(f"{file}#{n}"),
        file=file,
        section="Test",
        version_label="2026",
        version_date=None,
        text=text,
        score=0.9,
    )


def settled(*actions: CompletedAction, open_case: Any = None) -> Settled:
    return Settled(actions=actions, open_case=open_case, read_at=NOW)


def facts(**overrides: object) -> TurnFacts:
    base: dict[str, Any] = {
        "turn_id": TURN_4,
        "gate_kind": GateKind.FREE_TEXT,
        "plan_mode": "talk",
        "points": [],
        "passages": [],
        "no_source_tasks": [],
        "windows_shown": [],
        "writes_this_turn": [],
        "change_request": None,
        "handoff": None,
        "escalation": None,
        "identity_step": None,
    }
    base.update(overrides)
    return TurnFacts.model_validate(base)


def state(**overrides: object) -> ConversationState:
    base: dict[str, Any] = {
        "thread_id": THREAD,
        "turn_input": turn_input(),
        "gate": gate(),
        "settled": settled(),
    }
    base.update(overrides)
    return ConversationState.model_validate(base)


# --- WP-2 ------------------------------------------------------------------------------------------------------


def invoice_204411() -> InvoiceView:
    return InvoiceView(
        invoice_id="INV-204411",  # type: ignore[arg-type]
        lines=(
            InvoiceLineView(description="Diagnostic visit", amount_cents=8900),
            InvoiceLineView(description="Contactor replacement", amount_cents=24500),
            InvoiceLineView(description="After-hours dispatch", amount_cents=14400),
        ),
        total_cents=47800,
        balance_cents=47800,
        issued_on=dt.date(2026, 10, 2),
        due_on=dt.date(2026, 11, 1),
        paid=False,
    )


STAFF_NOTE_TEXT = "Billed after-hours " + "$" + "144" + "; fee schedule says " + "$" + "1" + "49"


def staff_note_149() -> StaffNote:
    return StaffNote(
        kind="billed_differs_from_schedule",
        record_id="INV-204411",  # type: ignore[arg-type]
        text=STAFF_NOTE_TEXT,
        source_file="pricing/2026_fee_schedule.pdf",
    )


def account_read() -> AccountResult:
    return AccountResult(
        status="read",
        invoices=(invoice_204411(),),
        staff_notes=(staff_note_149(),),
        tools=(),
        calls=(),
    )


WP2_LOOKUP_TEXT = "INV-204411 total $478.00 balance $478.00 lines $89.00 / $245.00 / $144.00"
WP2_QUESTION = "I got an invoice and I'm not sure what it's for."
WP2_KEPT = "Your invoice shows a $89 diagnostic, $245 for the repair and a $144 after-hours fee."


def wp2_draft() -> str:
    return WP2_KEPT + " The after-hours fee is " + "$" + "1" + "49" + "."


FAQ_DIAG = passage(
    "faq/customer_faq.md",
    3,
    "The diagnostic fee is credited toward the repair if you approve the repair at the same visit.",
)


def knowledge_answered() -> KnowledgeResult:
    return KnowledgeResult(
        status="answered",
        passages=(FAQ_DIAG,),
        points=(KnowledgePoint(text=FAQ_DIAG.text, passage_id=FAQ_DIAG.passage_id),),
        tools=(),
        calls=(),
    )


# --- WP-7 ------------------------------------------------------------------------------------------------------

WP7_MESSAGE = "I want a full refund on the repair. It didn't fix anything and I had to call another company."


def case_summary(
    reason: HandoffReason = HandoffReason.REFUND, priority: Priority = Priority.P3
) -> CaseSummary:
    return CaseSummary(
        case_ref=CASE_REF,
        reason=reason,
        priority=priority,
        state="unassigned",
        created_at=NOW,
        promise=Promise(
            policy_row="R26.refund",
            text="A representative will get to your refund request within 2 business days.",
            due_at=None,
            due_label=None,
        ),
        followup=None,
        version=1,
        due_at=None,
    )


def handoff_result(case: CaseSummary) -> HandoffResult:
    return HandoffResult(
        case=case,
        created=True,
        action=action(ActionKind.CASE_OPENED, str(CASE_REF), turn=TURN_4, records={"case": str(CASE_REF)}),
        alert=None,
    )


# --- storage ---------------------------------------------------------------------------------------------------


def seed(
    store: Any,
    *,
    customer: Sequence[tuple[TurnId, str]] = (),
    lookups: Sequence[tuple[TurnId, int, str, tuple[str, ...]]] = (),
    actions: Sequence[CompletedAction] = (),
) -> list[int]:
    """Write messages, lookup rows and actions into a temp DB; return the message ids."""
    ids: list[int] = []
    with store.uow(write=True) as tx:
        for turn, text in customer:
            ids.append(tx.core.messages.append(THREAD, "customer", text, NOW, turn_id=turn, kind="text"))
        for turn, index, text, record_ids in lookups:
            tx.core.lookup_log.append(
                LookupEntry(
                    tool="account_read",
                    record_ids=record_ids,
                    passage_ids=(),
                    result_seen=text,
                    message_id=ids[index],
                    turn_id=turn,
                )
            )
        for a in actions:
            tx.core.actions.record(a)
        tx.commit()
    return ids


# --- doubles ---------------------------------------------------------------------------------------------------


class FakeCaseService:
    def __init__(self, case: CaseSummary | None, *, fail_attach: bool = False) -> None:
        self.case = case
        self.fail_attach = fail_attach
        self.opened: list[ThreadId] = []
        self.attached: list[tuple[CaseRef, Brief]] = []

    def open_case_for_thread(self, thread_id: ThreadId) -> CaseSummary | None:
        self.opened.append(thread_id)
        return self.case

    def attach_brief(self, case_ref: CaseRef, brief: Brief) -> None:
        if brief.case_ref != case_ref:
            raise ValueError("brief belongs to another case")
        self.attached.append((case_ref, brief))
        if self.fail_attach:
            raise RuntimeError("case store unavailable (test)")


def make_brief(case_ref: CaseRef, *, status: str, not_generated: bool) -> Brief:
    headings = tuple(
        BriefHeading(
            number=i + 1,
            key=BRIEF_KEYS[i],  # type: ignore[arg-type]
            title=BRIEF_TITLES[i],
            origin=BRIEF_ORIGINS[i],  # type: ignore[arg-type]
            checked=i != 3,
            items=(),
            trimmed=False,
            trim_note=None,
            not_generated=not_generated and i in (1, 3, 6),
        )
        for i in range(8)
    )
    return Brief(
        case_ref=case_ref,
        thread_id=THREAD,
        assembled_at=NOW,
        status=status,  # type: ignore[arg-type]
        headings=headings,
    )


class FakeBriefAssembler:
    def __init__(self) -> None:
        self.assembled: list[int] = []
        self.extractions: list[tuple[BriefExtraction | None, Any]] = []

    def assemble(self, case: CaseSummary, state: ConversationState, lookups: Sequence[Any]) -> Brief:
        self.assembled.append(len(lookups))
        return make_brief(case.case_ref, status="being_written", not_generated=False)

    def attach_extraction(self, brief: Brief, extraction: BriefExtraction | None, check: Any) -> Brief:
        self.extractions.append((extraction, check))
        return make_brief(
            brief.case_ref,
            status="ready" if extraction is not None else "failed",
            not_generated=extraction is None,
        )


def gateway(
    *, responder: Any = None, brief: Any = None, limits: Limits | None = None
) -> tuple[ModelGateway, Any]:
    adapters = {k: v for k, v in {"responder": responder, "brief": brief}.items() if v is not None}
    d = default_doubles(**adapters)
    return ModelGateway(**gateway_kwargs(d, limits)), d


def deps(
    *,
    uow: Any,
    gw: ModelGateway,
    cases: FakeCaseService | None = None,
    brief: FakeBriefAssembler | None = None,
    limits: Limits | None = None,
) -> GraphDeps:
    return GraphDeps(
        gateway=gw,
        retrieval=cast(Any, None),
        uow=uow,
        identity=None,
        scheduling=None,
        handoff=None,
        brief=brief or FakeBriefAssembler(),
        demo=None,
        limits=limits or Limits(),
        trace=RecordingSink(),
        specialists=None,
        cases=cases or FakeCaseService(None),
        ledger=RecordingLedger(),
    )


def no_uow() -> Any:
    raise AssertionError("this node must not open a unit of work")


def signals(caplog: Any) -> list[dict[str, Any]]:
    return [r.__dict__["signal"] for r in caplog.records if r.name == "meridian.signal"]


def watch_signals(caplog: Any) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
