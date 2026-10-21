"""Core repositories: conversations, messages, turns, actions, lookups, checks, events, reads, reset (AEA-10; cases.md 1.2).

Every sub-repository takes the unit of work's connection and never commits. SQL stays here; services call
``tx.core.<repo>.<method>`` (DO-3 section 2.1). Errors name table and constraint only (AC-20).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from pydantic import TypeAdapter

from meridian.adapters.sqlite.db import (
    StorageError,
    format_wall,
    integrity_errors,
    last_row_id,
    parse_wall,
)
from meridian.adapters.sqlite.repos_core_aux import (
    CasesReadRepo,
    CheckEventsRepo,
    EventsRepo,
    LookupLogRepo,
    ReadsRepo,
    ResetRepo,
)
from meridian.adapters.sqlite.rows import (
    TURN_COLS,
    AppointmentRow,
    CaseOwnerRow,
    Cleared,
    ConversationRow,
    CustomerRow,
    EndedThread,
    EventRow,
    InvoiceRow,
    MessageRow,
    StreamEvent,
    StreamKey,
    TurnBegin,
    TurnRow,
    _dt,
    _j,
    _w,
    case_stream,
    thread_stream,
    turn_row,
)
from meridian.domain.actions import CompletedAction, OpenCase, Settled
from meridian.domain.common import CaseRef, ThreadId, TurnId
from meridian.domain.state import Controller
from meridian.domain.turn import TurnIds, TurnRecord

__all__ = [  # the repositories and the row models they return (consumers may import either from here)
    "ActionsRepo",
    "AppointmentRow",
    "CaseOwnerRow",
    "CasesReadRepo",
    "CheckEventsRepo",
    "Cleared",
    "ConversationRow",
    "ConversationsRepo",
    "CoreRepos",
    "CustomerRow",
    "EndedThread",
    "EventRow",
    "EventsRepo",
    "InvoiceRow",
    "LookupLogRepo",
    "MessageRow",
    "MessagesRepo",
    "ReadsRepo",
    "ResetRepo",
    "StreamEvent",
    "StreamKey",
    "TurnBegin",
    "TurnRow",
    "TurnsRepo",
    "case_stream",
    "thread_stream",
]

_CONV_COLS = (
    "thread_id, demo_session, run_tag, run_id, agent_version, started_at, started_wall_at, staffing_at_start, "
    "outcome, ended_wall_at, last_customer_wall_at, controller, controller_name, controller_case_ref, "
    "live_state, live_since"
)


def _conversation(r: tuple[Any, ...]) -> ConversationRow:
    return ConversationRow.model_validate(
        {
            "thread_id": r[0],
            "demo_session": r[1],
            "run_tag": r[2],
            "run_id": r[3],
            "agent_version": r[4],
            "started_at": _dt(r[5]),
            "started_wall_at": _dt(r[6]),
            "staffing_at_start": r[7],
            "outcome": r[8],
            "ended_wall_at": _dt(r[9]),
            "last_customer_wall_at": _dt(r[10]),
            "controller": {"kind": r[11], "representative_name": r[12], "case_ref": r[13]},
            "live_state": r[14],
            "live_since": _dt(r[15]),
        }
    )


class ConversationsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, row: ConversationRow) -> None:
        with integrity_errors("conversations"):
            self._conn.execute(
                f"INSERT INTO conversations ({_CONV_COLS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",  # noqa: S608 - constant column list
                (
                    str(row.thread_id),
                    row.demo_session,
                    row.run_tag,
                    row.run_id,
                    row.agent_version,
                    format_wall(row.started_at),
                    _w(row.started_wall_at),
                    row.staffing_at_start,
                    row.outcome,
                    _w(row.ended_wall_at),
                    _w(row.last_customer_wall_at),
                    row.controller.kind,
                    row.controller.representative_name,
                    None if row.controller.case_ref is None else str(row.controller.case_ref),
                    row.live_state,
                    _w(row.live_since),
                ),
            )

    def lookup(self, thread_id: str) -> ConversationRow | EndedThread | None:
        """Any string; a malformed id simply matches nothing (web.md section 4)."""
        found = self._conn.execute(
            f"SELECT {_CONV_COLS} FROM conversations WHERE thread_id = ?",  # noqa: S608 - constant column list
            (thread_id,),
        ).fetchone()
        if found is not None:
            return _conversation(found)
        ended = self._conn.execute(
            "SELECT thread_id, demo_session, ended_wall_at, reason, reset_id FROM ended_threads WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
        if ended is None:
            return None
        return EndedThread.model_validate(
            {
                "thread_id": ended[0],
                "demo_session": ended[1],
                "ended_wall_at": _dt(ended[2]),
                "reason": ended[3],
                "reset_id": ended[4],
            }
        )

    def _update(self, sql: str, params: tuple[Any, ...]) -> None:
        with integrity_errors("conversations"):
            cur = self._conn.execute(sql, params)
        if cur.rowcount == 0:
            raise StorageError("conversations", "no row")

    def set_outcome(
        self, thread_id: ThreadId, outcome: str, *, ended_wall_at: datetime | None = None
    ) -> None:
        self._update(
            "UPDATE conversations SET outcome = ?, ended_wall_at = COALESCE(?, ended_wall_at) WHERE thread_id = ?",
            (outcome, _w(ended_wall_at), str(thread_id)),
        )

    def set_last_customer_wall_at(self, thread_id: ThreadId, at_wall: datetime) -> None:
        self._update(
            "UPDATE conversations SET last_customer_wall_at = ? WHERE thread_id = ?",
            (format_wall(at_wall), str(thread_id)),
        )

    def set_controller(
        self, thread_id: ThreadId, controller: Controller, *, live_state: str, live_since: datetime | None
    ) -> None:
        self._update(
            "UPDATE conversations SET controller = ?, controller_name = ?, controller_case_ref = ?, "
            "live_state = ?, live_since = ? WHERE thread_id = ?",
            (
                controller.kind,
                controller.representative_name,
                None if controller.case_ref is None else str(controller.case_ref),
                live_state,
                _w(live_since),
                str(thread_id),
            ),
        )

    def set_live_state(self, thread_id: ThreadId, live_state: str, live_since: datetime | None) -> None:
        self._update(
            "UPDATE conversations SET live_state = ?, live_since = ? WHERE thread_id = ?",
            (live_state, _w(live_since), str(thread_id)),
        )

    def open_thread_ids(self) -> tuple[ThreadId, ...]:
        rows = self._conn.execute(
            "SELECT thread_id FROM conversations WHERE live_state <> 'closed' ORDER BY started_at, thread_id"
        ).fetchall()
        return tuple(_THREAD.validate_python(r[0]) for r in rows)

    def idle_live(self, cutoff_wall: datetime) -> tuple[tuple[ThreadId, datetime], ...]:
        rows = self._conn.execute(
            "SELECT thread_id, last_customer_wall_at FROM conversations WHERE run_tag = 'live' "
            "AND outcome = 'open' AND last_customer_wall_at IS NOT NULL AND last_customer_wall_at <= ? "
            "ORDER BY last_customer_wall_at, thread_id",
            (format_wall(cutoff_wall),),
        ).fetchall()
        return tuple((_THREAD.validate_python(r[0]), parse_wall(r[1])) for r in rows)

    def last_started_wall(self) -> datetime | None:
        row = self._conn.execute(
            "SELECT MAX(started_wall_at) FROM conversations WHERE run_tag = 'live'"
        ).fetchone()
        return _dt(row[0])


class MessagesRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    _COLS = "id, thread_id, role, text, at, turn_id, kind, card_id, choice_option"

    @staticmethod
    def _row(r: tuple[Any, ...]) -> MessageRow:
        return MessageRow.model_validate(
            {
                "id": r[0],
                "thread_id": r[1],
                "role": r[2],
                "text": r[3],
                "at": _dt(r[4]),
                "turn_id": r[5],
                "kind": r[6],
                "card_id": r[7],
                "choice_option": r[8],
            }
        )

    def append(
        self,
        thread_id: ThreadId,
        role: str,
        text_redacted: str,
        at: datetime,
        *,
        turn_id: TurnId | None = None,
        kind: str | None = None,
        card_id: str | None = None,
        choice_option: str | None = None,
    ) -> int:
        with integrity_errors("messages"):
            cur = self._conn.execute(
                "INSERT INTO messages (thread_id, role, text, at, turn_id, kind, card_id, choice_option) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(thread_id),
                    role,
                    text_redacted,
                    format_wall(at),
                    None if turn_id is None else str(turn_id),
                    kind,
                    card_id,
                    choice_option,
                ),
            )
        return last_row_id(cur, "messages")

    def recent(self, thread_id: ThreadId, turns: int) -> tuple[MessageRow, ...]:
        """The lines of the last ``turns`` turn ids, plus null-turn lines after the oldest kept one (graph-core 7)."""
        if turns < 1:
            raise ValueError("turns must be >= 1")
        tid = str(thread_id)
        ids = [
            r[0]
            for r in self._conn.execute(
                "SELECT turn_id FROM messages WHERE thread_id = ? AND turn_id IS NOT NULL "
                "GROUP BY turn_id ORDER BY MIN(id) DESC",
                (tid,),
            ).fetchall()
        ]
        if len(ids) <= turns:
            return self.all_for_thread(thread_id)
        marks = ",".join("?" for _ in range(turns))
        start = self._conn.execute(
            f"SELECT MIN(id) FROM messages WHERE thread_id = ? AND turn_id IN ({marks})",  # noqa: S608 - only "?" marks interpolated
            (tid, *ids[:turns]),
        ).fetchone()[0]
        rows = self._conn.execute(
            f"SELECT {self._COLS} FROM messages WHERE thread_id = ? AND id >= ? ORDER BY id",  # noqa: S608 - constant column list
            (tid, start),
        ).fetchall()
        return tuple(self._row(r) for r in rows)

    def all_for_thread(self, thread_id: ThreadId) -> tuple[MessageRow, ...]:
        rows = self._conn.execute(
            f"SELECT {self._COLS} FROM messages WHERE thread_id = ? ORDER BY id",  # noqa: S608 - constant column list
            (str(thread_id),),
        ).fetchall()
        return tuple(self._row(r) for r in rows)

    def belongs_to_case(self, message_id: int | str, case_ref: CaseRef) -> bool:
        try:
            mid = int(message_id)
        except ValueError:
            return False
        row = self._conn.execute(
            "SELECT 1 FROM messages m JOIN cases c ON c.thread_id = m.thread_id WHERE m.id = ? AND c.case_ref = ?",
            (mid, str(case_ref)),
        ).fetchone()
        return row is not None

    def handoff_anchor(self, thread_id: ThreadId) -> int:
        tid = str(thread_id)
        row = self._conn.execute(
            "SELECT MAX(id) FROM messages WHERE thread_id = ? AND role = 'customer'", (tid,)
        ).fetchone()
        if row[0] is None:
            row = self._conn.execute("SELECT MIN(id) FROM messages WHERE thread_id = ?", (tid,)).fetchone()
        if row[0] is None:
            raise StorageError("messages", "no anchor")
        return int(row[0])


class TurnsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def begin(self, ids: TurnIds, received_at: datetime) -> TurnBegin:
        row = self._conn.execute(
            "SELECT thread_id, status, response FROM turns WHERE turn_id = ?", (str(ids.turn_id),)
        ).fetchone()
        if row is None:
            with integrity_errors("turns"):
                self._conn.execute(
                    "INSERT INTO turns (turn_id, thread_id, request_id, run_tag, run_id, agent_version, sequence, "
                    "received_at, status) VALUES (?,?,?,?,?,?,"
                    "(SELECT COALESCE(MAX(sequence), 0) + 1 FROM turns WHERE thread_id = ?),?,'running')",
                    (
                        str(ids.turn_id),
                        str(ids.thread_id),
                        str(ids.request_id),
                        ids.run_tag,
                        ids.run_id,
                        ids.agent_version,
                        str(ids.thread_id),
                        format_wall(received_at),
                    ),
                )
            return TurnBegin(status="new")
        if row[0] != str(ids.thread_id):
            return TurnBegin(status="running")  # PA-7: never read another thread's reply
        if row[1] == "completed":
            return TurnBegin(status="completed", response=row[2])
        if row[1] == "running":
            return TurnBegin(status="running")
        # failed: re-arm so a concurrent duplicate now sees "running"
        self._conn.execute(
            "UPDATE turns SET status = 'running', request_id = ?, received_at = ? WHERE turn_id = ?",
            (str(ids.request_id), format_wall(received_at), str(ids.turn_id)),
        )
        return TurnBegin(status="failed")

    def finish(self, turn_id: TurnId, record: TurnRecord) -> None:
        trace = record.trace
        p = trace.planner
        with integrity_errors("turns"):
            cur = self._conn.execute(
                "UPDATE turns SET status = ?, gate_result = ?, path = ?, outcome = ?, degrade_reason = ?, "
                "planner_model = ?, planner_fallback_used = ?, planner_failure = ?, plan_mode = ?, plan_source = ?, "
                "plan_intents = ?, plan_handoff_request = ?, plan_topic = ?, planner_failed = ?, danger_raised = ?, "
                "specialists_run = ?, replied_at = ?, server_ms = ?, model_calls = ?, input_tokens = ?, "
                "output_tokens = ?, cost_usd = ?, tool_calls = ?, trace_id = ?, trace_export = ?, response = ? "
                "WHERE turn_id = ?",
                (
                    record.status,
                    trace.gate_result,
                    trace.path,
                    trace.outcome,
                    trace.degrade_reason,
                    None if p is None else p.model,
                    None if p is None else int(p.fallback_used),
                    None if p is None or p.failure is None else p.failure.value,
                    None if p is None else p.plan_mode,
                    None if p is None else p.plan_source,
                    None if p is None else _j([i.value for i in p.intents]),
                    None if p is None or p.handoff_request is None else p.handoff_request.value,
                    None if p is None else p.topic,
                    None if p is None else int(p.planner_failed),
                    int(trace.danger_raised),
                    _j(list(trace.specialists_run)),
                    format_wall(record.replied_at),
                    record.server_ms,
                    record.model_calls,
                    record.input_tokens,
                    record.output_tokens,
                    record.cost_usd,
                    record.tool_calls,
                    record.trace_id,
                    record.trace_export,
                    record.response,
                    str(turn_id),
                ),
            )
        if cur.rowcount == 0:
            raise StorageError("turns", "no row")

    def timeouts_for(self, thread_id: ThreadId) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM turns WHERE thread_id = ? AND degrade_reason = 'timeout'", (str(thread_id),)
        ).fetchone()
        return int(row[0])

    def fail_running(self) -> tuple[TurnId, ...]:
        ids = [
            r[0]
            for r in self._conn.execute(
                "SELECT turn_id FROM turns WHERE status = 'running' ORDER BY received_at, turn_id"
            ).fetchall()
        ]
        self._conn.execute(
            "UPDATE turns SET status = 'failed', path = 'degraded', outcome = 'degraded_handoff', "
            "degrade_reason = 'timeout' WHERE status = 'running'"
        )
        return tuple(_TURN.validate_python(i) for i in ids)

    def get(self, turn_id: TurnId) -> TurnRow | None:
        row = self._conn.execute(
            f"SELECT {TURN_COLS} FROM turns WHERE turn_id = ?",  # noqa: S608 - constant column list
            (str(turn_id),),
        ).fetchone()
        return None if row is None else turn_row(row)

    def for_thread(self, thread_id: ThreadId) -> tuple[TurnRow, ...]:
        rows = self._conn.execute(
            f"SELECT {TURN_COLS} FROM turns WHERE thread_id = ? ORDER BY sequence",  # noqa: S608 - constant column list
            (str(thread_id),),
        ).fetchall()
        return tuple(turn_row(r) for r in rows)


class ActionsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    _COLS = "thread_id, turn_id, kind, record_id, records_json, before_json, after_json, at"

    @staticmethod
    def _action(r: tuple[Any, ...]) -> CompletedAction:
        return CompletedAction.model_validate(
            {
                "key": {"thread_id": r[0], "turn_id": r[1], "kind": r[2], "record_id": r[3]},
                "kind": r[2],
                "records": json.loads(r[4]),
                "before": None if r[5] is None else json.loads(r[5]),
                "after": None if r[6] is None else json.loads(r[6]),
                "at": _dt(r[7]),
            }
        )

    def _find(self, action: CompletedAction) -> CompletedAction | None:
        k = action.key
        row = self._conn.execute(
            f"SELECT {self._COLS} FROM actions WHERE thread_id = ? AND turn_id = ? AND kind = ? AND record_id = ?",  # noqa: S608 - constant column list
            (str(k.thread_id), str(k.turn_id), k.kind.value, k.record_id),
        ).fetchone()
        return None if row is None else self._action(row)

    def record(self, action: CompletedAction) -> CompletedAction:
        """Idempotent on the key: same content returns the stored row; different content is a loud error (R-3)."""
        stored = self._find(action)
        if stored is not None:
            if (stored.records, stored.before, stored.after) == (action.records, action.before, action.after):
                return stored
            raise StorageError("actions", "UNIQUE (thread_id, turn_id, kind, record_id)")
        k = action.key
        with integrity_errors("actions"):
            self._conn.execute(
                "INSERT INTO actions (thread_id, turn_id, kind, record_id, records_json, before_json, after_json, at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(k.thread_id),
                    str(k.turn_id),
                    k.kind.value,
                    k.record_id,
                    _j(action.records),
                    None if action.before is None else _j(action.before),
                    None if action.after is None else _j(action.after),
                    format_wall(action.at),
                ),
            )
        stored = self._find(action)
        if stored is None:  # pragma: no cover - the insert above just succeeded
            raise StorageError("actions", "not stored")
        return stored

    def for_thread(self, thread_id: ThreadId) -> tuple[CompletedAction, ...]:
        rows = self._conn.execute(
            f"SELECT {self._COLS} FROM actions WHERE thread_id = ? ORDER BY id",  # noqa: S608 - constant column list
            (str(thread_id),),
        ).fetchall()
        return tuple(self._action(r) for r in rows)


class CoreRepos:
    """Repositories for 00_core and the cross-ticket reads; body AEA-10 (cases.md 1.2)."""

    conversations: ConversationsRepo
    messages: MessagesRepo
    turns: TurnsRepo
    actions: ActionsRepo
    lookup_log: LookupLogRepo
    check_events: CheckEventsRepo
    events: EventsRepo
    reads: ReadsRepo
    reset: ResetRepo
    cases_ro: CasesReadRepo

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.conversations = ConversationsRepo(conn)
        self.messages = MessagesRepo(conn)
        self.turns = TurnsRepo(conn)
        self.actions = ActionsRepo(conn)
        self.lookup_log = LookupLogRepo(conn)
        self.check_events = CheckEventsRepo(conn)
        self.events = EventsRepo(conn)
        self.reads = ReadsRepo(conn)
        self.reset = ResetRepo(conn)
        self.cases_ro = CasesReadRepo(conn)

    def settled_for(self, thread_id: ThreadId, read_at: datetime) -> Settled:
        """The one builder of Settled (graph-core 6): actions plus the open case and its promise. Reads no clock."""
        actions = self.actions.for_thread(thread_id)
        tid = str(thread_id)
        case = self._conn.execute(
            "SELECT case_ref, reason, priority, lifecycle FROM cases WHERE thread_id = ? "
            "AND lifecycle NOT IN ('resolved','closed_unresolved') ORDER BY created_at DESC, case_ref DESC LIMIT 1",
            (tid,),
        ).fetchone()
        open_case: OpenCase | None = None
        if case is not None:
            promise = self._conn.execute(
                "SELECT policy_row, text, due_at, due_label, extra_lines, live_queued FROM promises "
                "WHERE case_ref = ? ORDER BY id DESC LIMIT 1",
                (case[0],),
            ).fetchone()
            if promise is None:
                raise StorageError("promises", "no promise for open case")
            fu = self._conn.execute(
                "SELECT channel, destination_label, on_record, contact_window, saved_line FROM followups "
                "WHERE case_ref = ?",
                (case[0],),
            ).fetchone()
            open_case = OpenCase.model_validate(
                {
                    "case_ref": case[0],
                    "reason": case[1],
                    "priority": case[2],
                    "state": case[3],
                    "promise": {
                        "policy_row": promise[0],
                        "text": promise[1],
                        "due_at": _dt(promise[2]),
                        "due_label": promise[3],
                        "extra_lines": tuple(json.loads(promise[4])),
                        "live_queued": bool(promise[5]),
                    },
                    "followup": None
                    if fu is None
                    else {
                        "channel": fu[0],
                        "destination_label": fu[1],
                        "on_record": bool(fu[2]),
                        "window": fu[3],
                        "saved_line": fu[4],
                    },
                    "live_queued": case[3] == "live_queued",
                }
            )
        return Settled(actions=actions, open_case=open_case, read_at=read_at)


_THREAD: TypeAdapter[ThreadId] = TypeAdapter(ThreadId)
_TURN: TypeAdapter[TurnId] = TypeAdapter(TurnId)
