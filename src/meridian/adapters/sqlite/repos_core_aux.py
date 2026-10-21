"""Auxiliary core repositories: lookup log, check events, stream events, reads, reset, case owner (AEA-10).

Split from ``repos_core.py`` to keep both files under the 600-line adapter cap (code-structure.md). Same rules: the unit
of work's connection, no commit, errors name table and constraint only.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from meridian.adapters.sqlite.db import StorageError, format_wall, integrity_errors, last_row_id
from meridian.adapters.sqlite.migrate import CLEARED_TABLES
from meridian.adapters.sqlite.rows import (
    AppointmentRow,
    CaseOwnerRow,
    Cleared,
    CustomerRow,
    EventRow,
    InvoiceRow,
    StreamEvent,
    StreamKey,
    _d,
    _dt,
    _j,
    _w,
)
from meridian.domain.common import CaseRef, CustomerId, EventId, InvoiceId, ThreadId
from meridian.domain.state import IdentityState
from meridian.domain.tools import LookupEntry, LookupRow
from meridian.domain.turn import CheckEvent

__all__ = [
    "CasesReadRepo",
    "CheckEventsRepo",
    "EventsRepo",
    "LookupLogRepo",
    "ReadsRepo",
    "ResetRepo",
]


class LookupLogRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, entry: LookupEntry) -> int:
        """Copies the message's thread_id in the same statement; an unknown message is a foreign-key failure (CAS-38)."""
        with integrity_errors("lookup_log"):
            cur = self._conn.execute(
                "INSERT INTO lookup_log (thread_id, turn_id, message_id, tool, record_ids, passage_ids, result_seen) "
                "SELECT m.thread_id, ?, m.id, ?, ?, ?, ? FROM messages m WHERE m.id = ?",
                (
                    str(entry.turn_id),
                    entry.tool,
                    _j(list(entry.record_ids)),
                    _j([str(p) for p in entry.passage_ids]),
                    entry.result_seen,
                    entry.message_id,
                ),
            )
        if cur.rowcount == 0:
            raise StorageError("lookup_log", "FOREIGN KEY")
        return last_row_id(cur, "lookup_log")

    def for_thread(self, thread_id: ThreadId) -> tuple[LookupRow, ...]:
        rows = self._conn.execute(
            "SELECT id, thread_id, turn_id, message_id, tool, record_ids, passage_ids, result_seen "
            "FROM lookup_log WHERE thread_id = ? ORDER BY id",
            (str(thread_id),),
        ).fetchall()
        return tuple(
            LookupRow.model_validate(
                {
                    "id": r[0],
                    "thread_id": r[1],
                    "turn_id": r[2],
                    "message_id": r[3],
                    "tool": r[4],
                    "record_ids": tuple(json.loads(r[5])),
                    "passage_ids": tuple(json.loads(r[6])),
                    "result_seen": r[7],
                }
            )
            for r in rows
        )


class CheckEventsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, event: CheckEvent, thread_id: ThreadId, *, at: datetime | None = None) -> int:
        """``at`` None takes the turn's received_at (NULL when there is no turn row)."""
        with integrity_errors("check_events"):
            cur = self._conn.execute(
                "INSERT INTO check_events (thread_id, at, check_kind, turn_id, result, removed, claim_kinds, codes) "
                "VALUES (?, COALESCE(?, (SELECT received_at FROM turns WHERE turn_id = ?)), ?,?,?,?,?,?)",
                (
                    str(thread_id),
                    _w(at),
                    str(event.turn_id),
                    event.check,
                    str(event.turn_id),
                    event.result,
                    event.removed,
                    _j(list(event.claim_kinds)),
                    _j(list(event.codes)),
                ),
            )
        return last_row_id(cur, "check_events")

    def for_thread(self, thread_id: ThreadId) -> tuple[CheckEvent, ...]:
        rows = self._conn.execute(
            "SELECT check_kind, turn_id, result, removed, claim_kinds, codes FROM check_events "
            "WHERE thread_id = ? ORDER BY id",
            (str(thread_id),),
        ).fetchall()
        return tuple(
            CheckEvent.model_validate(
                {
                    "check": r[0],
                    "turn_id": r[1],
                    "result": r[2],
                    "removed": r[3],
                    "claim_kinds": tuple(json.loads(r[4])),
                    "codes": tuple(json.loads(r[5])),
                }
            )
            for r in rows
        )


class EventsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, stream: StreamKey, event: StreamEvent) -> EventId:
        with integrity_errors("events"):
            cur = self._conn.execute(
                "INSERT INTO events (stream, type, payload, at) VALUES (?,?,?,?)",
                (str(stream), event.type, _j(event.payload), format_wall(event.at)),
            )
        return last_row_id(cur, "events")

    def after(self, stream: StreamKey, last: EventId) -> list[EventRow]:
        rows = self._conn.execute(
            "SELECT id, stream, type, payload, at FROM events WHERE stream = ? AND id > ? ORDER BY id",
            (str(stream), last),
        ).fetchall()
        return [
            EventRow.model_validate(
                {"id": r[0], "stream": r[1], "type": r[2], "payload": json.loads(r[3]), "at": _dt(r[4])}
            )
            for r in rows
        ]

    def latest_of(self, stream: StreamKey, kind: str) -> EventId | None:
        row = self._conn.execute(
            "SELECT MAX(id) FROM events WHERE stream = ? AND type = ?", (str(stream), kind)
        ).fetchone()
        return None if row[0] is None else int(row[0])

    def latest_id(self, stream: StreamKey) -> EventId:
        row = self._conn.execute("SELECT MAX(id) FROM events WHERE stream = ?", (str(stream),)).fetchone()
        return 0 if row[0] is None else int(row[0])


class ReadsRepo:
    """Read-only queries over the issued tables and the identity rows (CAS-19, graph-tools section 5)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def invoice(self, invoice_id: InvoiceId) -> InvoiceRow | None:
        r = self._conn.execute(
            "SELECT invoice_id, customer_id, appointment_id, issued_date, due_date, amount_cents, balance_cents, "
            "line_items FROM invoices WHERE invoice_id = ?",
            (str(invoice_id),),
        ).fetchone()
        if r is None:
            return None
        try:
            items = json.loads(r[7])
        except ValueError:
            raise StorageError("invoices", "line_items not JSON") from None
        return InvoiceRow.model_validate(
            {
                "invoice_id": r[0],
                "customer_id": r[1],
                "appointment_id": r[2],
                "issued_date": _d(r[3]),
                "due_date": _d(r[4]),
                "amount_cents": r[5],
                "balance_cents": r[6],
                "line_items": tuple(items),
            }
        )

    def appointment(self, appointment_id: int) -> AppointmentRow | None:
        r = self._conn.execute(
            "SELECT a.appointment_id, a.slot_id, a.customer_id, a.status, a.is_warranty_visit, a.created_at, "
            's.slot_date, s."window", s.zone, s.service_type, s.tech_id, t.name '
            "FROM appointments a JOIN appointment_slots s USING (slot_id) JOIN technicians t ON t.tech_id = s.tech_id "
            "WHERE a.appointment_id = ?",
            (appointment_id,),
        ).fetchone()
        if r is None:
            return None
        return AppointmentRow.model_validate(
            {
                "appointment_id": r[0],
                "slot_id": r[1],
                "customer_id": r[2],
                "status": r[3],
                "is_warranty_visit": bool(r[4]),
                "created_at": _d(r[5]),
                "slot_date": _d(r[6]),
                "window": r[7],
                "zone": r[8],
                "service_type": r[9],
                "tech_id": r[10],
                "technician": r[11],
            }
        )

    def customer(self, customer_id: CustomerId) -> CustomerRow | None:
        r = self._conn.execute(
            "SELECT customer_id, name, phone, email, service_address, city, zip, membership_tier, "
            "membership_renewal_date, system_brand, system_install_date FROM customers WHERE customer_id = ?",
            (str(customer_id),),
        ).fetchone()
        if r is None:
            return None
        return CustomerRow.model_validate(
            {
                "customer_id": r[0],
                "name": r[1],
                "phone": r[2],
                "email": r[3],
                "service_address": r[4],
                "city": r[5],
                "zip": r[6],
                "membership_tier": r[7],
                "membership_renewal_date": _d(r[8]),
                "system_brand": r[9],
                "system_install_date": _d(r[10]),
            }
        )

    def identity_state(self, thread_id: ThreadId) -> IdentityState:
        tid = str(thread_id)
        t = self._conn.execute(
            "SELECT status, customer_id, masked_hint, verified_at FROM identity_threads WHERE thread_id = ?",
            (tid,),
        ).fetchone()
        sent = self._conn.execute(
            "SELECT COUNT(*) FROM identity_codes WHERE thread_id = ?", (tid,)
        ).fetchone()[0]
        code = self._conn.execute(
            "SELECT expires_at, tries_left FROM identity_codes WHERE thread_id = ? ORDER BY id DESC LIMIT 1",
            (tid,),
        ).fetchone()
        return IdentityState.model_validate(
            {
                "status": "not_checked" if t is None else t[0],
                "customer_id": None if t is None else t[1],
                "masked_hint": None if t is None else t[2],
                "code_expires_at": None if code is None else _dt(code[0]),
                "tries_left": 3 if code is None else code[1],
                "codes_sent": sent,
                "verified_at": None if t is None else _dt(t[3]),
            }
        )

    def new_flags_count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM flags WHERE status = 'new'").fetchone()[0])


class ResetRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def clear_demo_tables(self, reset_id: str, *, ended_at: datetime | None = None) -> Cleared:
        """Tombstone, clear and update per cases.md 1.3, inside the caller's transaction. Restores nothing."""
        c = self._conn
        open_threads = [
            r[0]
            for r in c.execute(
                "SELECT thread_id FROM conversations WHERE live_state <> 'closed' ORDER BY started_at, thread_id"
            ).fetchall()
        ]
        streams = [
            r[0]
            for r in c.execute(
                "SELECT DISTINCT substr(stream, 6) FROM events WHERE stream LIKE 'case:%' ORDER BY 1"
            ).fetchall()
        ]
        c.execute(
            "INSERT INTO ended_threads (thread_id, demo_session, ended_wall_at, reason, reset_id) "
            "SELECT thread_id, demo_session, ?, 'demo_reset', ? FROM conversations",
            (format_wall(ended_at or datetime.now(UTC)), reset_id),
        )
        roles_reset = c.execute(
            "UPDATE staff_sessions SET role = 'customer', role_reset_pending = 1 WHERE role <> 'customer'"
        ).rowcount
        cleared: dict[str, int] = {}
        for table in CLEARED_TABLES:
            cleared[table] = int(c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608 - module constant table name
            c.execute(f"DELETE FROM {table}")  # noqa: S608 - module constant table name
        return Cleared.model_validate(
            {
                "open_threads": tuple(open_threads),
                "case_streams": tuple(streams),
                "roles_reset": roles_reset,
                "rows_cleared": cleared,
            }
        )


class CasesReadRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def owner(self, case_ref: CaseRef) -> CaseOwnerRow | None:
        r = self._conn.execute(
            "SELECT thread_id, owner_role, owner_since, lifecycle FROM cases WHERE case_ref = ?",
            (str(case_ref),),
        ).fetchone()
        if r is None:
            return None
        return CaseOwnerRow.model_validate(
            {"thread_id": r[0], "owner_role": r[1], "owner_since": _dt(r[2]), "lifecycle": r[3]}
        )
