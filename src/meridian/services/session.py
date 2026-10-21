"""CON-1 behind the routes: open a chat conversation and rebuild a thread's history.

`SessionService.open` writes the conversation row and the fixed greeting in ONE write transaction, calls no model and
writes no turn. `SessionService.thread` is one read-only unit of work followed by a pure merge of messages, turns,
events and takeover lines into the customer's history. It never imports `agent/` or `web/`: the demo reads and the
settled-panel builder arrive injected.
"""

from __future__ import annotations

import datetime as dt
import logging
import sys
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, Protocol

from pydantic import TypeAdapter

from meridian.adapters.sqlite.rows import ConversationRow, MessageRow, case_stream, thread_stream
from meridian.domain.blocks import HandoffBlock, ReplyBlock, SettledView, TextBlock
from meridian.domain.common import EventId, MeridianModel, RequestId, ThreadId
from meridian.domain.staff import STAFF_PERSONAS, LoginSession, StaffRole
from meridian.domain.state import Controller
from meridian.domain.views import ClockView, StaffingView
from meridian.policy.limits import Limits
from meridian.policy.texts import TextId, render
from meridian.ports.runtime import Clock, UnitOfWorkFactory
from meridian.services.person_request import PersonRequestOutcome
from meridian.services.turn import (
    ASSISTANT_SPEAKER,
    LOG_RECORD_ATTR,
    SettledViewFn,
    ThreadNotOpen,
    TurnResponse,
)

SESSION_LOGGER: Final = "meridian.services.session"
GREETING_TURN_ID: Final = "greeting"
GREETING_BLOCK_ID: Final = "blk-greeting"
EVENT_LINE_TYPES: Final = frozenset(
    {"representative_joined", "ai_paused", "ai_resumed", "chat_closed", "staffing_changed"}
)
_THREAD_ID: Final = TypeAdapter(ThreadId)


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class DemoReads(Protocol):
    """The two DemoService methods this service reads."""

    def staffing(self) -> StaffingView: ...

    def clock_view(self) -> ClockView: ...


def greeting_block(text: str, at: dt.datetime) -> TextBlock:
    return TextBlock(block_id=GREETING_BLOCK_ID, speaker=ASSISTANT_SPEAKER, at=at, text=text, sources=())


class ChatLimits(MeridianModel):
    turn_deadline_ms: int
    still_working_after_ms: int
    browser_give_up_after_ms: int
    max_message_chars: int


class ChatOpened(MeridianModel):
    thread_id: ThreadId
    greeting_message_id: int
    greeting_text: str
    greeting_at: dt.datetime
    clock: ClockView
    staffing: StaffingView
    controller: Controller
    settled: SettledView
    limits: ChatLimits
    last_event_id: EventId


class HistoryEntry(MeridianModel):
    turn_id: str
    speaker_kind: Literal["assistant", "customer", "representative", "event"]
    speaker_name: str | None
    at: dt.datetime
    text: str | None
    blocks: tuple[ReplyBlock, ...]


class ThreadHistory(MeridianModel):
    thread_id: ThreadId
    state: Literal["open", "closed"]
    entries: tuple[HistoryEntry, ...]
    settled: SettledView
    clock: ClockView
    staffing: StaffingView
    last_event_id: EventId


@dataclass(frozen=True)
class _Item:
    entry: HistoryEntry
    key: int | None  # event spine: sort key; turn spine: the anchor (or None)
    tie: int = 0


def _option_labels(blocks: Iterable[ReplyBlock]) -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    for block in blocks:
        card_id = getattr(block, "card_id", None)
        options = getattr(block, "options", None)
        if isinstance(card_id, str) and isinstance(options, tuple):
            labels[card_id] = {o.option: o.label for o in options}
    return labels


def _customer_text(msg: MessageRow, labels: Mapping[str, Mapping[str, str]]) -> str:
    if msg.kind == "code":
        return render(TextId.HISTORY_CODE_ENTERED)
    if msg.kind == "form":
        return render(TextId.HISTORY_DETAILS_SENT)
    if msg.kind == "choice":
        label = labels.get(msg.card_id or "", {}).get(msg.choice_option or "")
        return label if label is not None else (msg.choice_option or msg.text)
    return msg.text


def _entry(
    turn_id: str,
    kind: Literal["assistant", "customer", "representative", "event"],
    at: dt.datetime,
    *,
    text: str | None = None,
    blocks: tuple[ReplyBlock, ...] = (),
    name: str | None = None,
) -> HistoryEntry:
    return HistoryEntry(
        turn_id=turn_id, speaker_kind=kind, speaker_name=name, at=at, text=text, blocks=blocks
    )


class SessionService:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        demo_clock: Clock,
        demo: DemoReads,
        limits: Limits,
        settled_view: SettledViewFn,
        agent_version: str,
        *,
        wall_clock: Callable[[], dt.datetime] = _utc_now,
    ) -> None:
        self._uow = uow
        self._demo_clock = demo_clock
        self._demo = demo
        self._limits = limits
        self._settled_view = settled_view
        self._agent_version = agent_version
        self._wall_clock = wall_clock
        self._limits_view = ChatLimits(
            turn_deadline_ms=limits.turn.turn_deadline_ms,
            still_working_after_ms=limits.turn.still_working_after_ms,
            browser_give_up_after_ms=limits.turn.browser_give_up_after_ms,
            max_message_chars=limits.turn.max_message_chars,
        )

    def open(
        self,
        session: LoginSession,
        *,
        run_tag: Literal["live", "eval", "load"],
        run_id: str | None,
        request_id: RequestId,
    ) -> ChatOpened:
        now = self._demo_clock.now()
        clock = self._demo.clock_view()
        staffing = self._demo.staffing()
        thread_id = _THREAD_ID.validate_python(str(uuid.uuid4()))
        text = render(TextId.GREETING)
        with self._uow(write=True) as tx:
            tx.core.conversations.insert(
                ConversationRow(
                    thread_id=thread_id,
                    demo_session=str(session.session_id),
                    run_tag=run_tag,
                    run_id=run_id,
                    agent_version=self._agent_version,
                    started_at=now,
                    started_wall_at=self._wall_clock(),
                    staffing_at_start=staffing.mode,
                    outcome="open",
                    controller=Controller(kind="ai"),
                    live_state="not_live",
                )
            )
            greeting_id = tx.core.messages.append(thread_id, "assistant", text, now)
            settled = tx.core.settled_for(thread_id, now)
            identity = tx.core.reads.identity_state(thread_id)
            last = tx.core.events.latest_id(thread_stream(thread_id))
            tx.commit()
        controller = Controller(kind="ai")
        return ChatOpened(
            thread_id=thread_id,
            greeting_message_id=greeting_id,
            greeting_text=text,
            greeting_at=now,
            clock=clock,
            staffing=staffing,
            controller=controller,
            settled=self._settled_view(settled, identity, controller),
            limits=self._limits_view,
            last_event_id=last,
        )

    def thread(self, thread_id: ThreadId) -> ThreadHistory:
        now = self._demo_clock.now()
        with self._uow() as tx:
            conv = tx.core.conversations.lookup(str(thread_id))
            if not isinstance(conv, ConversationRow):
                raise ThreadNotOpen()
            messages = tx.core.messages.all_for_thread(thread_id)
            turns = tx.core.turns.for_thread(thread_id)
            events = tx.core.events.after(thread_stream(thread_id), 0)
            last_event_id = tx.core.events.latest_id(thread_stream(thread_id))
            case_rows = [
                row
                for case in tx.cases.cases.list_for_thread(thread_id)
                for row in tx.core.events.after(case_stream(case.case_ref), 0)
                if row.type == "customer_message"
            ]
            settled = tx.core.settled_for(thread_id, now)
            identity = tx.core.reads.identity_state(thread_id)
        clock = self._demo.clock_view()
        staffing = self._demo.staffing()

        replies: dict[str, tuple[ReplyBlock, ...]] = {}
        con4: dict[str, tuple[ReplyBlock, ...]] = {}
        for row in turns:
            if row.status != "completed" or not row.response:
                continue
            try:
                replies[str(row.turn_id)] = TurnResponse.model_validate_json(row.response).blocks
            except ValueError:
                try:
                    con4[str(row.turn_id)] = (PersonRequestOutcome.model_validate_json(row.response).block,)
                except ValueError:
                    # Ids only, never the stored response: it may hold customer text.
                    logging.getLogger(SESSION_LOGGER).warning(
                        "thread_turn_skipped",
                        extra={
                            LOG_RECORD_ATTR: {
                                "record": "thread_turn_skipped",
                                "turn_id": str(row.turn_id),
                                "thread_id": thread_id,
                            }
                        },
                    )
        labels = _option_labels(b for blocks in replies.values() for b in blocks)

        case_anchor: dict[int, int] = {}
        for crow in case_rows:
            inner = crow.payload.get("message")
            mid = inner.get("message_id") if isinstance(inner, dict) else None
            if isinstance(mid, str) and mid.isdigit():
                case_anchor[int(mid)] = crow.id

        spine: list[_Item] = []
        greeting = next((m for m in messages if m.role == "assistant" and m.turn_id is None), None)
        if greeting is not None:
            spine.append(
                _Item(
                    _entry(
                        GREETING_TURN_ID,
                        "assistant",
                        greeting.at,
                        blocks=(greeting_block(greeting.text, greeting.at),),
                    ),
                    None,
                )
            )
        for trow in turns:
            tid = str(trow.turn_id)
            cust = next((m for m in messages if m.role == "customer" and m.turn_id == trow.turn_id), None)
            if cust is not None:
                spine.append(
                    _Item(
                        _entry(tid, "customer", cust.at, text=_customer_text(cust, labels)),
                        case_anchor.get(cust.id),
                    )
                )
                if tid in replies:
                    reply = next(
                        (m for m in messages if m.role == "assistant" and m.turn_id == trow.turn_id), None
                    )
                    at = reply.at if reply is not None else (trow.replied_at or trow.received_at)
                    spine.append(_Item(_entry(tid, "assistant", at, blocks=replies[tid]), None))
            elif tid in con4:
                spine.append(
                    _Item(
                        _entry(tid, "customer", trow.received_at, text=render(TextId.PERSON_REQUEST_LABEL)),
                        None,
                    )
                )
                spine.append(
                    _Item(
                        _entry(tid, "assistant", trow.replied_at or trow.received_at, blocks=con4[tid]), None
                    )
                )

        staff_anchor: dict[int, int] = {}
        evspine: list[_Item] = []
        for ev in events:
            line = ev.payload.get("line")
            if ev.type in EVENT_LINE_TYPES and isinstance(line, str):
                evspine.append(_Item(_entry(f"evt-{ev.id}", "event", ev.at, text=line), ev.id, ev.id))
            elif ev.type == "shift_ended":
                try:
                    block = HandoffBlock.model_validate(ev.payload["handoff"])
                except (KeyError, ValueError):
                    continue
                evspine.append(
                    _Item(_entry(f"evt-{ev.id}", "assistant", ev.at, blocks=(block,)), ev.id, ev.id)
                )
            elif ev.type == "staff_message":
                mid = ev.payload.get("message_id")
                if isinstance(mid, str) and mid.isdigit():
                    staff_anchor[int(mid)] = ev.id
        riley = STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name
        for msg in messages:
            if msg.role == "representative":
                evspine.append(
                    _Item(
                        _entry(f"msg-{msg.id}", "representative", msg.at, text=msg.text, name=riley),
                        staff_anchor.get(msg.id, sys.maxsize),
                        msg.id,
                    )
                )
        evspine.sort(key=lambda i: (i.key if i.key is not None else 0, i.tie))

        merged: list[_Item] = []
        remaining = list(evspine)
        for item in spine:
            if item.key is not None:
                while remaining and (remaining[0].key or 0) < item.key:
                    merged.append(remaining.pop(0))
            merged.append(item)
        merged.extend(remaining)
        merged.sort(key=lambda i: i.entry.at)

        return ThreadHistory(
            thread_id=thread_id,
            state="closed" if conv.live_state == "closed" else "open",
            entries=tuple(i.entry for i in merged),
            settled=self._settled_view(settled, identity, conv.controller),
            clock=clock,
            staffing=staffing,
            last_event_id=last_event_id,
        )
