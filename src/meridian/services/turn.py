"""CON-2 behind the route: one customer turn, in DO-4 section 14's order as web.md section 9 completes it.

`TurnService.run_turn` admits the turn (30 in flight), checks the spend gate, records the turn as running with the
customer's redacted message, runs the injected graph outside any database transaction with a 60 s budget, then
stores the reply, the turn record and the check events. It never reads the graph's own state, keeps no list of past
messages, and holds no transaction open across `run_graph`. The service imports nothing from `web/` or `agent/`; the
route and the container hunk hand it the pieces it needs.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import logging
import threading
import time
from collections.abc import Callable
from typing import Final, Literal, Protocol, TypedDict

from meridian.adapters.sqlite.rows import ConversationRow, StreamEvent, case_stream, thread_stream
from meridian.domain.actions import Settled
from meridian.domain.blocks import (
    FailureOfferBlock,
    Notice,
    NoticeBlock,
    ReplyBlock,
    SettledView,
    Speaker,
    Write,
)
from meridian.domain.common import (
    EventId,
    HaltReason,
    MeridianModel,
    RequestId,
    ThreadId,
    TurnId,
)
from meridian.domain.staff import CUSTOMER_SPEAKER_NAME
from meridian.domain.state import Controller, IdentityState
from meridian.domain.turn import (
    CheckEvent,
    GraphOutcome,
    RunGraph,
    TurnBudget,
    TurnContext,
    TurnIds,
    TurnInput,
    TurnOutcome,
    TurnPayload,
    TurnRecord,
    TurnTrace,
)
from meridian.gates.gate import parse_intake
from meridian.policy.limits import Limits
from meridian.policy.texts import TextId, render
from meridian.ports.runtime import Clock, TraceSink, UnitOfWork, UnitOfWorkFactory
from meridian.privacy.redact import RedactionProfile, redact
from meridian.services.ledger import SpendGuard

TURN_LOGGER: Final = "meridian.services.turn"
LOG_RECORD_ATTR: Final = "meridian_record"  # == meridian.web.logging.RECORD_ATTR (services never import web/)
TURN_IN_PROGRESS_RETRY_MS: Final = 2000
ASSISTANT_SPEAKER: Final = Speaker(kind="assistant", display_name="Meridian assistant")

SettledViewFn = Callable[[Settled, IdentityState, Controller], SettledView]
NoticeCode = Literal["BUSY", "SPEND_CAP_REACHED", "RATE_LIMITED", "TURN_TIMEOUT"]
_NOTICE_TEXT: Final[dict[str, TextId]] = {
    "BUSY": TextId.BUSY,
    "SPEND_CAP_REACHED": TextId.SPEND_CAP_REACHED,
    "RATE_LIMITED": TextId.RATE_LIMITED,
    "TURN_TIMEOUT": TextId.TURN_TIMEOUT,
}


class RunTurn(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    request_id: RequestId
    demo_session: str
    payload: TurnPayload
    run_tag: Literal["live", "eval", "load"]
    run_id: str | None


class ChatController(MeridianModel):
    kind: Literal["ai", "human"]
    display_name: str | None


class TurnResponse(MeridianModel):
    """OpenAPI TurnResponse, field for field."""

    thread_id: ThreadId
    turn_id: TurnId
    sequence: int
    blocks: tuple[ReplyBlock, ...]
    settled: SettledView
    writes: tuple[Write, ...]
    controller: ChatController
    notice: Notice | None
    last_event_id: EventId


class _Usage(TypedDict):
    model_calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    tool_calls: int


class TurnVerdict(Protocol):
    """What `rate_limited` reads; the web layer's LimitVerdict satisfies it."""

    @property
    def allowed(self) -> bool: ...


class TurnInProgress(Exception):
    def __init__(self, retry_after_ms: int = TURN_IN_PROGRESS_RETRY_MS) -> None:
        super().__init__("turn in progress")
        self.retry_after_ms = retry_after_ms


class ThreadNotOpen(Exception):
    """The thread has no live conversation row."""


def next_outcome(stored: str, trace_outcome: TurnOutcome, closed_every_open_task: bool) -> str | None:
    """web.md section 9's table: the new conversation outcome, or None when it stays."""
    if trace_outcome == "handed_off":
        return "handed_off" if stored != "handed_off" else None
    if trace_outcome == "safety_reply" and stored == "open":
        return "safety_reply"
    if trace_outcome in ("answered", "acted") and closed_every_open_task and stored == "open":
        return "ai_resolved"
    return None


def reopened_outcome(stored: str) -> str | None:
    """A customer message reopens ai_resolved and abandoned; handed_off and safety_reply never reopen."""
    return "open" if stored in ("ai_resolved", "abandoned") else None


def _notice_parts(
    code: NoticeCode, turn_id: TurnId, at: dt.datetime
) -> tuple[tuple[ReplyBlock, ...], Notice]:
    block = NoticeBlock(
        block_id=f"blk-{turn_id}-1",
        speaker=ASSISTANT_SPEAKER,
        at=at,
        code=code,
        text=render(_NOTICE_TEXT[code]),
        person_key=True,
    )
    if code == "TURN_TIMEOUT":
        notice = Notice(
            code=code,
            actions=("try_again", "talk_to_person"),
            retry_turn_id=str(turn_id),
            delivered_to_representative=False,
        )
    else:
        notice = Notice(
            code=code, actions=("talk_to_person",), retry_turn_id=None, delivered_to_representative=False
        )
    return (block,), notice


def _failure_offer(turn_id: TurnId, at: dt.datetime) -> FailureOfferBlock:
    return FailureOfferBlock(
        block_id=f"blk-{turn_id}-1",
        speaker=ASSISTANT_SPEAKER,
        at=at,
        text=render(TextId.FAILURE_OFFER),
        person_key=True,
    )


def _degraded_trace(reason: Literal["model_error", "timeout", "spend_cap", "rate_limit"]) -> TurnTrace:
    return TurnTrace(gate_result="clear", path="degraded", outcome="degraded_handoff", degrade_reason=reason)


def _reply_text(blocks: tuple[ReplyBlock, ...]) -> str:
    texts = [t for b in blocks if isinstance(t := getattr(b, "text", None), str) and t]
    if texts:
        joined = "\n".join(texts)
    elif blocks:
        joined = "[" + ", ".join(b.type for b in blocks) + "]"
    else:
        joined = "[no reply]"
    return redact(joined, RedactionProfile.STORE).text


def _customer_message_event(message_id: int, text_store: str, at: dt.datetime) -> StreamEvent:
    return StreamEvent(
        type="customer_message",
        at=at,
        payload={
            "message": {
                "message_id": str(message_id),
                "speaker": {"kind": "customer", "display_name": CUSTOMER_SPEAKER_NAME},
                "at": at.isoformat(),
                "text": text_store,
            }
        },
    )


def _writes_of(settled: SettledView, turn_id: TurnId) -> tuple[Write, ...]:
    return tuple(w for w in settled.actions if w.turn_id == str(turn_id))


class TurnService:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        demo_clock: Clock,
        wall_clock: Callable[[], dt.datetime],
        spend: SpendGuard,
        trace: TraceSink,
        run_graph: RunGraph,
        settled_view: SettledViewFn,
        limits: Limits,
        agent_version: str,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._uow = uow
        self._demo_clock = demo_clock
        self._wall_clock = wall_clock
        self._spend = spend
        self._trace = trace
        self._run_graph = run_graph
        self._settled_view = settled_view
        self._limits = limits
        self._agent_version = agent_version
        self._monotonic = monotonic
        self._slots = threading.BoundedSemaphore(limits.admission.max_in_flight)
        self._turn_limits = limits.turn

    # -- refusals ---------------------------------------------------------------------------------------------
    def rate_limited(self, cmd: RunTurn, verdict: TurnVerdict) -> TurnResponse:
        """WEB-12: the route's refused verdict becomes a RATE_LIMITED notice; no slot, spend check or model."""
        if verdict.allowed:
            raise ValueError("rate_limited needs a refused verdict")
        mono_start = self._monotonic()
        now = self._demo_clock.now()
        return self._reject(cmd, code="RATE_LIMITED", reason="rate_limit", now=now, mono_start=mono_start)

    def _reject(
        self,
        cmd: RunTurn,
        *,
        code: NoticeCode,
        reason: Literal["spend_cap", "rate_limit"],
        now: dt.datetime,
        mono_start: float,
    ) -> TurnResponse:
        with self._uow(write=True) as tx:
            conv = tx.core.conversations.lookup(str(cmd.thread_id))
            if not isinstance(conv, ConversationRow):
                raise ThreadNotOpen()
            begin = tx.core.turns.begin(self._ids(cmd), now)
            if begin.status == "completed":
                return self._stored(begin.response)
            if begin.status == "running":
                raise TurnInProgress()
            row = tx.core.turns.get(cmd.turn_id)
            if row is None:
                raise ThreadNotOpen()
            blocks, notice = _notice_parts(code, cmd.turn_id, now)
            settled = self._settled_view(
                tx.core.settled_for(cmd.thread_id, now),
                tx.core.reads.identity_state(cmd.thread_id),
                conv.controller,
            )
            response = TurnResponse(
                thread_id=cmd.thread_id,
                turn_id=cmd.turn_id,
                sequence=row.sequence,
                blocks=blocks,
                settled=settled,
                writes=_writes_of(settled, cmd.turn_id),
                controller=self._controller(conv),
                notice=notice,
                last_event_id=tx.core.events.latest_id(thread_stream(cmd.thread_id)),
            )
            tx.core.turns.finish(
                cmd.turn_id,
                TurnRecord(
                    status="failed",
                    trace=_degraded_trace(reason),
                    replied_at=now,
                    server_ms=self._elapsed_ms(mono_start),
                    **self._usage(tx, cmd),
                    trace_id=None,
                    trace_export="off",
                    response=response.model_dump_json(),
                ),
            )
            tx.commit()
            return response

    # -- the turn ---------------------------------------------------------------------------------------------
    def run_turn(self, cmd: RunTurn) -> TurnResponse:
        mono_start = self._monotonic()
        now = self._demo_clock.now()  # one demo reading for the whole turn
        if not self._slots.acquire(blocking=False):
            return self._reject(cmd, code="BUSY", reason="rate_limit", now=now, mono_start=mono_start)
        try:
            return self._run(cmd, now, mono_start)
        finally:
            self._slots.release()

    def _run(self, cmd: RunTurn, now: dt.datetime, mono_start: float) -> TurnResponse:
        if not self._spend.allow_turn():
            return self._reject(
                cmd, code="SPEND_CAP_REACHED", reason="spend_cap", now=now, mono_start=mono_start
            )
        intake = parse_intake(cmd.payload)
        ids = self._ids(cmd)

        # T1: running row + customer message + reopen + CON-21 event commit together or not at all.
        with self._uow(write=True) as tx:
            conv = tx.core.conversations.lookup(str(cmd.thread_id))
            if not isinstance(conv, ConversationRow):
                raise ThreadNotOpen()
            begin = tx.core.turns.begin(ids, now)
            if begin.status == "completed":
                return self._stored(begin.response)
            if begin.status == "running":
                raise TurnInProgress()
            message_id: int | None = None
            new_message = True
            if begin.status == "failed":
                for m in tx.core.messages.all_for_thread(cmd.thread_id):
                    if m.role == "customer" and m.turn_id == cmd.turn_id:
                        message_id = m.id
                        new_message = False
                        break
            if message_id is None:
                message_id = tx.core.messages.append(
                    cmd.thread_id,
                    "customer",
                    intake.text_store,
                    now,
                    turn_id=cmd.turn_id,
                    kind=intake.kind,
                    card_id=intake.card_id,
                    choice_option=intake.choice.option if intake.choice is not None else None,
                )
            tx.core.conversations.set_last_customer_wall_at(cmd.thread_id, self._wall_clock())
            reopen = reopened_outcome(conv.outcome)
            if reopen is not None:
                tx.core.conversations.set_outcome(cmd.thread_id, reopen)
            if new_message and conv.controller.kind == "human" and conv.controller.case_ref is not None:
                tx.core.events.append(
                    case_stream(conv.controller.case_ref),
                    _customer_message_event(message_id, intake.text_store, now),
                )
            tx.commit()

        turn_input = TurnInput(
            turn_id=cmd.turn_id,
            message_id=message_id,
            kind=intake.kind,
            text_store=intake.text_store,
            card_id=intake.card_id,
            choice=intake.choice,
            card_number_seen=intake.card_number_seen,
            received_at=now,
        )
        budget = TurnBudget(started=mono_start, deadline=mono_start + float(self._turn_limits.deadline_s))
        outcome: GraphOutcome | None = None
        failed = False
        # No unit of work is open here (DO-3 section 2.3 rule 1).
        with self._trace.turn(ids) as span:
            ctx = TurnContext(
                ids=ids, budget=budget, now=now, demo_session=cmd.demo_session, span=span, intake=intake
            )
            try:
                outcome = self._run_graph(turn_input, ctx)
            except Exception as exc:
                failed = True
                self._log_error(cmd, type(exc).__name__)
        trace_id = span.trace_id
        export = self._trace.export_status(span)

        status: Literal["completed", "failed"]
        graph_view: SettledView | None = None
        notice: Notice | None
        closed = False
        events: tuple[CheckEvent, ...] = ()
        if failed or outcome is None:
            status = "failed"
            trace = _degraded_trace("model_error")
            blocks: tuple[ReplyBlock, ...] = (_failure_offer(cmd.turn_id, now),)
            notice = None
        elif outcome.halt is not None and outcome.halt.reason == HaltReason.DEADLINE:
            status = "failed"
            trace = outcome.turn_trace.model_copy(
                update={"path": "degraded", "outcome": "degraded_handoff", "degrade_reason": "timeout"}
            )
            blocks = outcome.reply.blocks
            if not any(
                getattr(b, "type", None) == "notice" and getattr(b, "code", None) == "TURN_TIMEOUT"
                for b in blocks
            ):
                blocks = (
                    *blocks,
                    NoticeBlock(
                        block_id=f"blk-{cmd.turn_id}-timeout",
                        speaker=ASSISTANT_SPEAKER,
                        at=now,
                        code="TURN_TIMEOUT",
                        text=render(TextId.TURN_TIMEOUT),
                        person_key=True,
                    ),
                )
            notice = _notice_parts("TURN_TIMEOUT", cmd.turn_id, now)[1]
            events = outcome.check_events
        else:
            status = "completed"
            trace = outcome.turn_trace
            blocks = outcome.reply.blocks
            notice = outcome.reply.notice
            graph_view = outcome.reply.settled_view
            closed = outcome.closed_every_open_task
            events = outcome.check_events

        try:
            with self._uow(write=True) as tx:
                conv = tx.core.conversations.lookup(str(cmd.thread_id))
                if not isinstance(conv, ConversationRow):
                    raise ThreadNotOpen()
                row = tx.core.turns.get(cmd.turn_id)
                if row is None:
                    raise ThreadNotOpen()
                settled = (
                    graph_view
                    if graph_view is not None
                    else self._settled_view(
                        tx.core.settled_for(cmd.thread_id, now),
                        tx.core.reads.identity_state(cmd.thread_id),
                        conv.controller,
                    )
                )
                response = TurnResponse(
                    thread_id=cmd.thread_id,
                    turn_id=cmd.turn_id,
                    sequence=row.sequence,
                    blocks=blocks,
                    settled=settled,
                    writes=_writes_of(settled, cmd.turn_id),
                    controller=self._controller(conv),
                    notice=notice,
                    last_event_id=tx.core.events.latest_id(thread_stream(cmd.thread_id)),
                )
                if status == "completed":
                    tx.core.messages.append(
                        cmd.thread_id, "assistant", _reply_text(blocks), now, turn_id=cmd.turn_id
                    )
                for event in events:
                    tx.core.check_events.append(event, cmd.thread_id)
                tx.core.turns.finish(
                    cmd.turn_id,
                    TurnRecord(
                        status=status,
                        trace=trace,
                        replied_at=self._demo_clock.now(),
                        server_ms=self._elapsed_ms(mono_start),
                        **self._usage(tx, cmd),
                        trace_id=trace_id,
                        trace_export=export,
                        response=response.model_dump_json(),
                    ),
                )
                new = next_outcome(conv.outcome, trace.outcome, closed)
                if new is not None:
                    tx.core.conversations.set_outcome(cmd.thread_id, new)
                tx.commit()
        except Exception:
            # Best effort and never hides the original error: a retry must not be stuck on 409.
            with contextlib.suppress(Exception), self._uow(write=True) as tx2:
                tx2.core.turns.finish(
                    cmd.turn_id,
                    TurnRecord(
                        status="failed",
                        trace=_degraded_trace("model_error"),
                        replied_at=now,
                        server_ms=self._elapsed_ms(mono_start),
                        model_calls=0,
                        input_tokens=0,
                        output_tokens=0,
                        cost_usd=0.0,
                        tool_calls=0,
                        trace_id=trace_id,
                        trace_export=export,
                        response="",
                    ),
                )
                tx2.commit()
            raise
        return response

    # -- helpers ----------------------------------------------------------------------------------------------
    def _ids(self, cmd: RunTurn) -> TurnIds:
        return TurnIds(
            thread_id=cmd.thread_id,
            turn_id=cmd.turn_id,
            request_id=cmd.request_id,
            run_tag=cmd.run_tag,
            run_id=cmd.run_id,
            agent_version=self._agent_version,
        )

    def _stored(self, text: str | None) -> TurnResponse:
        if text is None:
            raise TurnInProgress()
        try:
            return TurnResponse.model_validate_json(text)
        except ValueError:
            raise TurnInProgress() from None

    @staticmethod
    def _controller(conv: ConversationRow) -> ChatController:
        human = conv.controller.kind == "human"
        return ChatController(
            kind=conv.controller.kind, display_name=conv.controller.representative_name if human else None
        )

    def _elapsed_ms(self, mono_start: float) -> int:
        return int((self._monotonic() - mono_start) * 1000)

    @staticmethod
    def _usage(tx: UnitOfWork, cmd: RunTurn) -> _Usage:
        rows = tx.spend.for_turn(cmd.turn_id)
        lookups = tx.core.lookup_log.for_thread(cmd.thread_id)
        return {
            "model_calls": len(rows),
            "input_tokens": sum(r.input_tokens for r in rows),
            "output_tokens": sum(r.output_tokens for r in rows),
            "cost_usd": float(sum(r.cost_usd for r in rows)),
            "tool_calls": sum(1 for r in lookups if r.turn_id == cmd.turn_id),
        }

    @staticmethod
    def _log_error(cmd: RunTurn, error_kind: str) -> None:
        # Never the exception text, the payload or the intake: they may hold customer text.
        logging.getLogger(TURN_LOGGER).warning(
            "turn_error",
            extra={
                LOG_RECORD_ATTR: {
                    "record": "turn_error",
                    "request_id": str(cmd.request_id),
                    "turn_id": str(cmd.turn_id),
                    "thread_id": cmd.thread_id,
                    "error_kind": error_kind,
                }
            },
        )
