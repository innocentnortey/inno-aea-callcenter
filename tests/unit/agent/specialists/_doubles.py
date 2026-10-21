"""Builders and doubles for the AEA-35 specialist tests. Synthetic values only."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from datetime import date, datetime

from pydantic import JsonValue

from meridian.agent.gateway import ModelGateway, ModelOutcome
from meridian.agent.specialists.runner import SpecialistRunner
from meridian.agent.specialists.specs import SPECS
from meridian.agent.tools.dispatch import DispatchedCall, ToolDispatcher
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import (
    CustomerId,
    InvoiceId,
    PassageId,
    ProviderFailure,
    ProviderFailureKind,
    RequestId,
    ThreadId,
    ToolErrorCode,
    TurnId,
)
from meridian.domain.records import FeeNote, Passage, RetrievalResult, ShownSlot
from meridian.domain.specialists import (
    AccountCapture,
    AppointmentView,
    ChangeRequestDraft,
    ConfirmationView,
    InvoiceLineView,
    InvoiceView,
    KnowledgeCapture,
    SchedulingCapture,
    SchedulingSlice,
    StaffNote,
    WarrantyView,
    WriteResult,
)
from meridian.domain.tools import (
    AccountSlice,
    KnowledgeSlice,
    LookupEntry,
    SpecialistTask,
    ToolCallRecord,
    ToolCallScope,
    ToolError,
    ToolKind,
    ToolResult,
)
from meridian.domain.turn import (
    PlannedTask,
    SpecialistKind,
    TaskIntent,
    TurnBudget,
    TurnContext,
    TurnIds,
)
from meridian.policy.limits import Brakes
from meridian.ports.models import (
    CallRecord,
    Role,
    ToolCall,
    ToolRole,
    ToolSchema,
    ToolStep,
    ToolStepRequest,
    ToolTranscript,
)
from tests.fakes import CHICAGO, WORKED_PAIRS_NOW, FakeToolModel, InMemoryTraceSink, provider_call

THREAD = ThreadId("11111111-1111-4111-8111-111111111111")
TURN_1 = TurnId("22222222-2222-4222-8222-222222222201")
TURN_2 = TurnId("22222222-2222-4222-8222-222222222202")
TURN_5 = TurnId("22222222-2222-4222-8222-222222222205")
REQUEST = RequestId("33333333-3333-4333-8333-333333333333")


def passage(file: str, n: int, text: str, *, score: float = 0.8) -> Passage:
    return Passage(
        passage_id=PassageId(f"{file}#{n}"),
        file=file,
        section="Comfort Club (Standard)",
        version_label="Effective 2026-01-01",
        version_date=date(2026, 1, 1),
        text=text,
        score=score,
    )


_MEMBERSHIP = "membership/comfort_club_overview.md"
WP1_INCLUDES = passage(
    _MEMBERSHIP,
    0,
    "Includes two seasonal tune-ups per year, priority scheduling, the $89 diagnostic fee waived, "
    "15% off all repairs, no after-hours dispatch fee, and reminders.",
    score=0.82,
)
WP1_PRICE = passage(_MEMBERSHIP, 1, "Price: $189 per year per system, or $16.99 per month.", score=0.78)
WP1_MINIMUM = passage(_MEMBERSHIP, 2, "Monthly plans require a 12-month minimum commitment.", score=0.71)
ARCHIVE_ID = PassageId("archive/comfort_club_overview.md#0")
TROUBLESHOOTING = passage(
    "faq/troubleshooting_before_you_call.md",
    0,
    "Check that the thermostat is set to Cool and the breaker is on before booking a visit.",
    score=0.74,
)
FAQ_CREDIT = passage(
    "faq/customer_faq.md",
    3,
    "Our diagnostic fee is credited toward the repair when you approve it at the same visit.",
    score=0.70,
)
INV_204411 = InvoiceView(
    invoice_id=InvoiceId("INV-204411"),
    lines=(
        InvoiceLineView(description="Diagnostic visit", amount_cents=8900),
        InvoiceLineView(description="Contactor replacement", amount_cents=24500),
        InvoiceLineView(description="After-hours dispatch", amount_cents=14400),
    ),
    total_cents=47800,
    balance_cents=47800,
    issued_on=date(2026, 10, 2),
    due_on=date(2026, 11, 1),
    paid=False,
)
STAFF_NOTE = StaffNote(
    kind="billed_differs_from_schedule",
    record_id=InvoiceId("INV-204411"),
    text="INV-204411 bills After-hours dispatch at $144.00; the 2026 fee schedule lists $149.00 for non-members.",
    source_file="pricing/2026_fee_schedule.pdf",
)
WARRANTY = WarrantyView(
    install_date=date(2019, 5, 14),
    equipment_brand="Carrier",
    sentence="Parts are covered for 10 years from the install date when the system was registered.",
)
APPT_WP4 = AppointmentView(
    appointment_id=1,
    date=date(2026, 10, 16),
    window="12:00-16:00",
    service_type="hvac_tune_up",
    technician="Marta Kowalski",
    is_warranty_visit=False,
)
SLOT_44 = ShownSlot(
    slot_id=44,
    date=date(2026, 10, 19),
    window="08:00-12:00",
    technician="Marta Kowalski",
    service_type="hvac_tune_up",
    zone="central",
    member_reserved=False,
    shown_turn=TURN_1,
)
SLOT_61 = SLOT_44.model_copy(update={"slot_id": 61, "window": "12:00-16:00"})
DRAFT_WP4 = ChangeRequestDraft(
    appointment_id=1,
    change="move",
    wanted_text="Monday morning",
    windows_shown=(44, 61),
    hours_before=2.0,
    window_start=datetime(2026, 10, 16, 12, 0, tzinfo=CHICAGO),
)
WRITE_WP4F = WriteResult(
    action=CompletedAction(
        key=ActionKey(thread_id=THREAD, turn_id=TURN_1, kind=ActionKind.MOVED, record_id="2"),
        kind=ActionKind.MOVED,
        records={"appointment": "2", "slot": "44", "old_slot": "12"},
        before={"date": "2026-10-21", "window": "12:00-16:00"},
        after={
            "date": "2026-10-19",
            "window": "08:00-12:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_tune_up",
            "fee_line": "",
        },
        at=WORKED_PAIRS_NOW,
    ),
    confirmation=ConfirmationView(
        date=date(2026, 10, 19),
        window="08:00-12:00",
        technician="Marta Kowalski",
        fee_note=FeeNote(
            service_type="hvac_tune_up",
            tier="none",
            fee_row="Seasonal tune-up",
            amount_cents=12900,
            waived=False,
            line="The seasonal tune-up is $129.",
        ),
    ),
)


def turn_ids(turn_id: TurnId = TURN_1) -> TurnIds:
    return TurnIds(
        thread_id=THREAD,
        turn_id=turn_id,
        request_id=REQUEST,
        run_tag="eval",
        run_id=None,
        agent_version="test",
    )


@contextmanager
def turn_ctx(
    sink: InMemoryTraceSink, *, turn_id: TurnId = TURN_1, now: datetime = WORKED_PAIRS_NOW
) -> Iterator[TurnContext]:
    ids = turn_ids(turn_id)
    with sink.turn(ids) as span:
        started = time.monotonic()
        yield TurnContext(
            ids=ids,
            budget=TurnBudget(started=started, deadline=started + 60.0),
            now=now,
            demo_session="demo-test",
            span=span,
        )


def scope(
    ctx: TurnContext,
    *,
    customer_id: CustomerId | None = None,
    shown: frozenset[int] = frozenset(),
    message_id: int = 412,
) -> ToolCallScope:
    return ToolCallScope(
        ids=ctx.ids, customer_id=customer_id, shown_slot_ids=shown, now=ctx.now, message_id=message_id
    )


def knowledge_slice() -> KnowledgeSlice:
    return KnowledgeSlice()


def account_slice() -> AccountSlice:
    return AccountSlice()


def scheduling_slice(
    *, appointments: tuple[AppointmentView, ...] = (), shown: tuple[ShownSlot, ...] = ()
) -> SchedulingSlice:
    return SchedulingSlice(
        customer_zone="central",
        member=False,
        appointments=appointments,
        shown_slots=shown,
        pending_change=False,
        bookings_left=3,
    )


def make_task(
    specialist: SpecialistKind,
    intent: TaskIntent,
    text: str,
    *,
    messages: tuple[str, ...] = (),
    offer_quick_checks: bool = False,
    slice_: KnowledgeSlice | AccountSlice | SchedulingSlice | None = None,
) -> SpecialistTask:
    if slice_ is None:
        if specialist == "knowledge":
            slice_ = knowledge_slice()
        elif specialist == "account":
            slice_ = account_slice()
        else:
            slice_ = scheduling_slice()
    return SpecialistTask(
        task=PlannedTask(
            order=1, specialist=specialist, intent=intent, needs_identity=(specialist != "knowledge")
        ),
        customer_text=text,
        task_messages=messages,
        slice=slice_,
        offer_quick_checks=offer_quick_checks,
    )


def tool_call(call_id: str, name: str, **args: JsonValue) -> ToolCall:
    return ToolCall(id=call_id, name=name, args=dict(args))


def report_call(call_id: str, **args: JsonValue) -> ToolCall:
    return tool_call(call_id, "report_facts", **args)


def step(*calls: ToolCall, text: str = "") -> ToolStep:
    return ToolStep(
        text=text,
        tool_calls=calls,
        raw={"stub": True},
        stop_reason="tool_use" if calls else "end_turn",
    )


def lookup(
    ctx: TurnContext,
    tool: str,
    *,
    record_ids: tuple[str, ...] = (),
    passage_ids: tuple[PassageId, ...] = (),
    seen: str = "ok",
) -> LookupEntry:
    return LookupEntry(
        tool=tool,
        record_ids=record_ids,
        passage_ids=passage_ids,
        result_seen=seen,
        message_id=412,
        turn_id=ctx.ids.turn_id,
    )


def dispatched(
    call: ToolCall,
    ctx: TurnContext,
    *,
    kind: ToolKind | None,
    for_model: JsonValue | ToolError,
    captured: KnowledgeCapture | AccountCapture | SchedulingCapture | None = None,
    record_ids: tuple[str, ...] = (),
    passage_ids: tuple[PassageId, ...] = (),
    elapsed_ms: int = 3,
    name: str | None = None,
) -> DispatchedCall:
    error: ToolErrorCode | None = None
    outcome = "ok"
    if isinstance(for_model, ToolError):
        error = for_model.code
        outcome = "failed" if error == ToolErrorCode.TOOL_FAILED else "refused"
        content = json.dumps(
            {"error": for_model.model_dump(mode="json")}, separators=(",", ":"), ensure_ascii=False
        )
    else:
        content = json.dumps(for_model, separators=(",", ":"), ensure_ascii=False)
    record_name = name or call.name
    record = ToolCallRecord.model_validate(
        {
            "tool_call_id": call.id,
            "name": record_name,
            "kind": kind,
            "outcome": outcome,
            "error": error,
            "record_ids": record_ids,
            "passage_ids": passage_ids,
            "lookup_id": 1,
            "elapsed_ms": elapsed_ms,
        }
    )
    result = ToolResult(
        ok=outcome == "ok",
        for_model=for_model,
        captured=captured,
        lookup=lookup(ctx, record_name, record_ids=record_ids, passage_ids=passage_ids),
        lookup_written=False,
    )
    return DispatchedCall(tool_call_id=call.id, content=content, result=result, record=record)


def kb_dispatched(
    call: ToolCall, ctx: TurnContext, passages: Sequence[Passage], *, below_floor: bool = False
) -> DispatchedCall:
    ids = tuple(p.passage_id for p in passages)
    body: JsonValue = {
        "below_floor": below_floor,
        "passages": [{"passage_id": str(p.passage_id), "file": p.file, "text": p.text} for p in passages],
    }
    return dispatched(
        call,
        ctx,
        kind=ToolKind.KB_SEARCH,
        for_model=body,
        captured=KnowledgeCapture(result=RetrievalResult(passages=tuple(passages), below_floor=below_floor)),
        passage_ids=ids,
    )


def refused_dispatched(
    call: ToolCall,
    ctx: TurnContext,
    code: ToolErrorCode,
    *,
    kind: ToolKind | None,
    captured: SchedulingCapture | None = None,
    name: str | None = None,
) -> DispatchedCall:
    return dispatched(
        call,
        ctx,
        kind=kind,
        for_model=ToolError(code=code, message="refused", retryable=False),
        captured=captured,
        name=name,
    )


def failed_dispatched(call: ToolCall, ctx: TurnContext, *, kind: ToolKind) -> DispatchedCall:
    return refused_dispatched(call, ctx, ToolErrorCode.TOOL_FAILED, kind=kind)


class ScriptedGateway(ModelGateway):
    """Gateway double: forwards each tool step to a FakeToolModel, or returns scripted outcomes first."""

    def __init__(
        self,
        model: FakeToolModel | None = None,
        *,
        outcomes: Sequence[ModelOutcome[ToolStep]] = (),
        retried_steps: frozenset[int] = frozenset(),
    ) -> None:
        self.model = model
        self._outcomes = list(outcomes)
        self._retried = retried_steps
        self.requests: list[ToolStepRequest] = []
        self.roles: list[ToolRole] = []

    def tool_step(self, role: ToolRole, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[ToolStep]:
        n = len(self.requests)
        self.requests.append(req)
        self.roles.append(role)
        if self._outcomes:
            return self._outcomes.pop(0)
        assert self.model is not None
        attempt = self.model.tool_step(req, timeout_s=8.0)
        calls: list[CallRecord] = []
        if n in self._retried:
            failure = ProviderFailure(
                kind=ProviderFailureKind.OVERLOADED,
                provider="anthropic",
                http_status=529,
                retry_after_s=None,
                retryable=True,
                provider_request_id=None,
            )
            calls.append(
                CallRecord.from_provider(
                    provider_call(provider="anthropic", model="claude-sonnet-5-5", failure=failure),
                    role=Role.SPECIALIST,
                    attempt=1,
                )
            )
        calls.append(CallRecord.from_provider(attempt.record, role=Role.SPECIALIST, attempt=len(calls) + 1))
        return ModelOutcome[ToolStep](
            value=attempt.value, calls=tuple(calls), failure=attempt.failure, halt=None
        )


class ScriptedDispatcher(ToolDispatcher):
    """Dispatcher double: records every batch; answers each call with handler(call)."""

    def __init__(
        self, handler: Callable[[ToolCall], DispatchedCall], *, schemas: tuple[ToolSchema, ...] = ()
    ) -> None:
        self._handler = handler
        self._schemas = schemas
        self.batches: list[tuple[tuple[ToolCall, ...], frozenset[ToolKind], ToolCallScope]] = []
        self.schema_requests: list[frozenset[ToolKind]] = []

    def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]:
        self.schema_requests.append(kinds)
        return self._schemas

    def dispatch(
        self, calls: Sequence[ToolCall], *, kinds: frozenset[ToolKind], scope: ToolCallScope
    ) -> tuple[DispatchedCall, ...]:
        self.batches.append((tuple(calls), kinds, scope))
        return tuple(self._handler(c) for c in calls)

    @property
    def dispatched_calls(self) -> tuple[ToolCall, ...]:
        return tuple(c for batch, _, _ in self.batches for c in batch)


def make_runner(
    gateway: ModelGateway,
    transcript: ToolTranscript,
    dispatcher: ToolDispatcher,
    trace: InMemoryTraceSink,
    *,
    brakes: Brakes | None = None,
) -> SpecialistRunner:
    return SpecialistRunner(
        gateway=gateway,
        transcript=transcript,
        dispatcher=dispatcher,
        specs=SPECS,
        brakes=brakes or Brakes(),
        trace=trace,
    )
