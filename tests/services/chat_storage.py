"""AEA-40 test support, storage half: row readers, hooked unit of work, seeders and log/dump helpers (frozen with the AEA-40 tests).

Split out of `chat_doubles.py` to keep every test-support file under 500 lines; no helper changed. Synthetic only.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from meridian.adapters.sqlite.rows import ConversationRow
from meridian.domain.blocks import (
    FollowUpOptions,
    HandoffBlock,
    LiveQueuedBlock,
    Notice,
)
from meridian.domain.common import ThreadId, TurnId
from meridian.domain.state import Controller
from meridian.domain.turn import (
    TurnTrace,
)
from meridian.policy.texts import TextId, render
from tests.fakes import WORKED_PAIRS_NOW
from tests.fixtures.sqlite import TempStore
from tests.services.chat_doubles import (
    AGENT_VERSION,
    ASSISTANT_SPEAKER,
    DEMO_SESSION,
    UUID_RE,
    empty_view,
    new_request_id,
    new_thread_id,
    new_turn_id,
)


def conversation(store: TempStore, thread_id: ThreadId) -> Any:
    with store.uow() as tx:
        return tx.core.conversations.lookup(str(thread_id))


def messages_of(store: TempStore, thread_id: ThreadId) -> tuple[Any, ...]:
    with store.uow() as tx:
        return tuple(tx.core.messages.all_for_thread(thread_id))


def customer_messages(store: TempStore, thread_id: ThreadId, turn_id: TurnId | None = None) -> list[Any]:
    return [
        m
        for m in messages_of(store, thread_id)
        if m.role == "customer" and (turn_id is None or m.turn_id == turn_id)
    ]


def turn_row(store: TempStore, turn_id: TurnId) -> Any:
    with store.uow() as tx:
        return tx.core.turns.get(turn_id)


def count_rows(store: TempStore, table: str, where: str = "1=1", params: tuple[Any, ...] = ()) -> int:
    conn = sqlite3.connect(store.db_path)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0])  # noqa: S608 - test-only constants
    finally:
        conn.close()


def raw_value(store: TempStore, sql: str, params: tuple[Any, ...] = ()) -> Any:
    conn = sqlite3.connect(store.db_path)
    try:
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    return None if row is None else row[0]


_DUMPED_TABLES = ("messages", "turns", "conversations", "check_events", "events", "lookup_log")


def text_dump(store: TempStore) -> str:
    """Every row of every table a customer value could land in, as one string, with UUIDs removed (so a random id
    cannot hold a six-digit run by chance)."""
    conn = sqlite3.connect(store.db_path)
    try:
        parts = [repr(conn.execute(f"SELECT * FROM {table}").fetchall()) for table in _DUMPED_TABLES]  # noqa: S608 - test-only constants
    finally:
        conn.close()
    return UUID_RE.sub("", "\n".join(parts))


# -- storage seeding and reading --------------------------------------------------------------------------------
def human_controller(case_ref: str = "MHC-C-0042", name: str = "Riley") -> Controller:
    return Controller.model_validate({"kind": "human", "representative_name": name, "case_ref": case_ref})


def seed_thread(
    uow: Any,
    demo_session: str = DEMO_SESSION,
    *,
    controller: Controller | None = None,
    outcome: str = "open",
    at: dt.datetime = WORKED_PAIRS_NOW,
    run_tag: str = "live",
) -> ThreadId:
    """A conversations row plus the greeting assistant message, in one write transaction (cases.md section 5)."""
    thread_id = new_thread_id()
    row = ConversationRow.model_validate(
        {
            "thread_id": str(thread_id),
            "demo_session": demo_session,
            "run_tag": run_tag,
            "agent_version": AGENT_VERSION,
            "started_at": at,
            "outcome": outcome,
            "controller": (controller or Controller(kind="ai")).model_dump(),
        }
    )
    with uow(write=True) as tx:
        tx.core.conversations.insert(row)
        tx.core.messages.append(thread_id, "assistant", render(TextId.GREETING), at)
        tx.commit()
    return thread_id


# -- blocks used by history tests -------------------------------------------------------------------------------
def handoff_block(
    reference: str = "MHC-C-0042", at: dt.datetime = WORKED_PAIRS_NOW, *, block_id: str = "blk-handoff"
) -> HandoffBlock:
    return HandoffBlock(
        block_id=block_id,
        speaker=ASSISTANT_SPEAKER,
        at=at,
        card_id=f"handoff-{reference}",
        options=(),
        answered=None,
        reference=reference,
        variant="nobody_online",
        promise_text="A person will reach out by tomorrow at noon.",
        due_at=None,
        due_label=None,
        extra_lines=(),
        followup_chooser=FollowUpOptions(
            legend="How should we reach you?", channels=(), windows=(), general_only=True
        ),
    )


def live_queued_block(
    reference: str = "MHC-C-0042", at: dt.datetime = WORKED_PAIRS_NOW, *, block_id: str = "blk-queued"
) -> LiveQueuedBlock:
    return LiveQueuedBlock(
        block_id=block_id,
        speaker=ASSISTANT_SPEAKER,
        at=at,
        reference=reference,
        promise_text="A representative is being asked to join.",
    )


def notice_codes(blocks: Any) -> list[str]:
    return [b.code for b in blocks if getattr(b, "type", None) == "notice"]


def has_person_key(blocks: Any) -> bool:
    return any(getattr(b, "person_key", False) for b in blocks)


@dataclass
class Collected:
    """Results of worker threads: either a response or the exception the call raised."""

    results: list[Any] = field(default_factory=list)
    errors: list[BaseException] = field(default_factory=list)

    def run(self, fn: Callable[[], Any]) -> None:
        try:
            self.results.append(fn())
        except BaseException as exc:
            self.errors.append(exc)


def turn_ids_of(cmd: Any) -> Any:
    """The `TurnIds` a command stands for (what `core.turns.begin` takes)."""
    from meridian.domain.turn import TurnIds

    return TurnIds.model_validate(
        {
            "thread_id": str(cmd.thread_id),
            "turn_id": str(cmd.turn_id),
            "request_id": str(cmd.request_id),
            "run_tag": cmd.run_tag,
            "run_id": cmd.run_id,
            "agent_version": AGENT_VERSION,
        }
    )


def records_of_kind(caplog: pytest.LogCaptureFixture, kind: str) -> list[dict[str, Any]]:
    """The `meridian_record` extras (web/logging.py RECORD_ATTR) with `record == kind`, from pytest's capture."""
    found: list[dict[str, Any]] = []
    for record in caplog.records:
        extra = record.__dict__.get("meridian_record")
        if isinstance(extra, dict) and extra.get("record") == kind:
            found.append(extra)
    return found


def log_blob(caplog: pytest.LogCaptureFixture) -> str:
    """Everything the loggers captured: messages, arguments, extras, exception text."""
    parts: list[str] = []
    for record in caplog.records:
        parts.append(record.getMessage())
        parts.append(repr(sorted((k, repr(v)) for k, v in record.__dict__.items() if k != "exc_info")))
        if record.exc_info:
            parts.append(repr(record.exc_info[1]))
        if record.exc_text:
            parts.append(record.exc_text)
    return "\n".join(parts)


def notice_of(response: Any) -> Notice | None:
    notice = response.notice
    assert notice is None or isinstance(notice, Notice)
    return notice


def dump_json(model: Any) -> str:
    return json.dumps(model.model_dump(mode="json"), sort_keys=True)


def data_dir_text(root: Path) -> str:
    """Every file under a directory, decoded leniently, for the 'nowhere in the working copy' checks."""
    parts: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            parts.append(path.read_bytes().decode("utf-8", errors="ignore"))
    return "\n".join(parts)


# -- history seeding (AC-16 to AC-18): rows in the shapes AEA-42 (web.md section 8) and AEA-46 (staff.md 5, 7) write ---
RILEY = "Riley"
_EVENT_SPEAKER: dict[str, Any] = {"kind": "event", "display_name": None}


@dataclass
class Takeover:
    """The ids and texts of one seeded representative takeover, in event-id order."""

    joined_id: int
    paused_id: int
    riley_message_id: int
    staff_event_id: int
    resumed_id: int
    riley_text: str
    lines: dict[str, str]
    staffing_id: int | None = None
    shift_end_id: int | None = None

    @property
    def newest_event_id(self) -> int:
        return max(
            i
            for i in (self.resumed_id, self.staff_event_id, self.staffing_id, self.shift_end_id)
            if i is not None
        )


def seed_case(
    uow: Any, thread_id: ThreadId, case_ref: str = "MHC-C-0042", at: dt.datetime = WORKED_PAIRS_NOW
) -> None:
    """A case row and its promise for the thread (an open case needs its promise: `settled_for` reads both)."""
    from meridian.adapters.sqlite.rows import CaseRow
    from meridian.domain.common import Promise

    row = CaseRow.model_validate(
        {
            "case_ref": case_ref,
            "thread_id": str(thread_id),
            "reason": "customer_requested_person",
            "priority": "P3",
            "rule_id": "R-TEST",
            "trigger": "customer",
            "lifecycle": "unassigned",
            "created_at": at,
            "updated_at": at,
        }
    )
    with uow(write=True) as tx:
        tx.cases.cases.insert(row)
        tx.cases.promises.insert(
            row.case_ref,
            Promise(policy_row="test", text="A person will reach out.", due_at=None, due_label=None),
            at,
        )
        tx.commit()


def seed_person_request_turn(
    uow: Any,
    thread_id: ThreadId,
    block: HandoffBlock | LiveQueuedBlock,
    at: dt.datetime = WORKED_PAIRS_NOW,
) -> TurnId:
    """A CON-4 turn row in web.md section 8's stored shape: completed, gate_result `person_requested`, no message."""
    from meridian.domain.turn import TurnIds, TurnRecord

    turn_id = new_turn_id()
    ids = TurnIds.model_validate(
        {
            "thread_id": str(thread_id),
            "turn_id": str(turn_id),
            "request_id": str(new_request_id()),
            "run_tag": "live",
            "run_id": None,
            "agent_version": AGENT_VERSION,
        }
    )
    stored = json.dumps(
        {
            "result": "case_created",
            "block": block.model_dump(mode="json"),
            "settled": empty_view().model_dump(mode="json"),
        }
    )
    record = TurnRecord(
        status="completed",
        trace=TurnTrace(gate_result="person_requested", path="handoff", outcome="handed_off"),
        replied_at=at,
        server_ms=5,
        model_calls=0,
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        tool_calls=0,
        trace_id=None,
        trace_export="off",
        response=stored,
    )
    with uow(write=True) as tx:
        tx.core.turns.begin(ids, at)
        tx.core.turns.finish(turn_id, record)
        tx.commit()
    return turn_id


def seed_takeover(
    uow: Any,
    thread_id: ThreadId,
    at: dt.datetime = WORKED_PAIRS_NOW,
    *,
    riley_text: str = "Hi, this is Riley. I can see your request.",
    staffing_change: bool = False,
    shift_end: HandoffBlock | None = None,
    step: dt.timedelta = dt.timedelta(0),
) -> Takeover:
    """Riley joins, the AI pauses, Riley writes, hands back; optionally the staffing line and a shift end.

    Every row carries `at`; with a non-zero `step` the n-th row (joined 0, paused 1, Riley 2, resumed 3, staffing 4,
    shift end 5) is `n * step` later, so a test can ask for time order without depending on a tie-break.
    """
    from meridian.adapters.sqlite.rows import StreamEvent, thread_stream

    lines = {
        "joined": render(TextId.REP_JOINED, rep_name=RILEY),
        "paused": render(TextId.AI_PAUSED, rep_name=RILEY),
        "resumed": render(TextId.AI_RESUMED, rep_name=RILEY),
        "staffing": render(TextId.STAFFING_CHANGED_ON_SHIFT),
        "shift_ended": render(TextId.SHIFT_ENDED),
    }
    stream = thread_stream(thread_id)

    def event(tx: Any, kind: str, payload: dict[str, Any], n: int) -> int:
        return int(tx.core.events.append(stream, StreamEvent(type=kind, payload=payload, at=at + n * step)))

    with uow(write=True) as tx:
        joined = event(
            tx,
            "representative_joined",
            {"speaker": _EVENT_SPEAKER, "display_name": RILEY, "line": lines["joined"]},
            0,
        )
        paused = event(tx, "ai_paused", {"speaker": _EVENT_SPEAKER, "line": lines["paused"]}, 1)
        message_id = tx.core.messages.append(thread_id, "representative", riley_text, at + 2 * step)
        staff_event = event(
            tx,
            "staff_message",
            {
                "speaker": {"kind": "representative", "display_name": RILEY},
                "message_id": str(message_id),
                "text": riley_text,
            },
            2,
        )
        resumed = event(tx, "ai_resumed", {"speaker": _EVENT_SPEAKER, "line": lines["resumed"]}, 3)
        staffing_id = None
        if staffing_change:
            staffing_id = event(
                tx,
                "staffing_changed",
                {
                    "speaker": _EVENT_SPEAKER,
                    "staffing": {
                        "mode": "simulated_on_shift",
                        "label": "Simulated staff on shift (demo)",
                        "banner": None,
                    },
                    "line": lines["staffing"],
                },
                4,
            )
        shift_id = None
        if shift_end is not None:
            shift_id = event(
                tx,
                "shift_ended",
                {
                    "speaker": _EVENT_SPEAKER,
                    "line": lines["shift_ended"],
                    "handoff": shift_end.model_dump(mode="json"),
                    "settled": empty_view().model_dump(mode="json"),
                },
                5,
            )
        tx.commit()
    return Takeover(
        joined_id=joined,
        paused_id=paused,
        riley_message_id=message_id,
        staff_event_id=staff_event,
        resumed_id=resumed,
        riley_text=riley_text,
        lines=lines,
        staffing_id=staffing_id,
        shift_end_id=shift_id,
    )


def newest_event_id(store: TempStore, thread_id: ThreadId) -> int:
    from meridian.adapters.sqlite.rows import thread_stream

    with store.uow() as tx:
        return int(tx.core.events.latest_id(thread_stream(thread_id)))


def attr(obj: Any, name: str) -> Any:
    """Read a field of a union member without a type ignore (blocks are a discriminated union)."""
    return getattr(obj, name)
