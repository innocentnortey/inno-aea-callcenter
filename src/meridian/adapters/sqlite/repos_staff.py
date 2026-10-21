"""Staff sessions and flags repositories (AEA-02 shell; body: AEA-44, stage7/staff.md section 3, STF-27).

Every datetime is written with ``format_wall`` and read with ``parse_wall``: one time format in the database. The
repositories take the unit of work's connection and never commit.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Literal

from meridian.adapters.sqlite.db import format_wall, integrity_errors, last_row_id, parse_wall
from meridian.domain.common import CaseRef, MeridianModel
from meridian.domain.staff import DemoRole, LoginSessionId, StaffRole

__all__ = ["FlagRow", "FlagsRepo", "StaffRepos", "StaffSessionRow", "StaffSessionsRepo"]


class StaffSessionRow(MeridianModel):
    token_hash: str
    session_id: LoginSessionId
    role: DemoRole
    role_reset_pending: bool
    signed_in_demo: datetime
    created_real: datetime
    expires_real: datetime


class FlagRow(MeridianModel):
    id: int | None = None
    case_ref: CaseRef
    target: Literal["answer", "brief", "escalation"]
    message_id: str | None
    note: str | None
    reason: str | None
    flagged_by_role: StaffRole
    flagged_at: datetime
    status: Literal["new", "reviewed"]
    reviewed_by_role: StaffRole | None
    reviewed_note: str | None
    reviewed_at: datetime | None


_INSERT_SESSION = (
    "INSERT INTO staff_sessions (token_hash, session_id, role, role_reset_pending, signed_in_demo, created_real, "
    "expires_real) VALUES (?,?,?,?,?,?,?)"
)
_SESSION_SELECT = (
    "SELECT token_hash, session_id, role, role_reset_pending, signed_in_demo, created_real, expires_real "
    "FROM staff_sessions "
)
_SESSION_BY_HASH = _SESSION_SELECT + "WHERE token_hash = ?"
_SESSION_BY_ID = _SESSION_SELECT + "WHERE session_id = ?"
_FLAG_SELECT = (
    "SELECT id, case_ref, target, message_id, note, reason, flagged_by_role, flagged_at, status, "
    "reviewed_by_role, reviewed_note, reviewed_at FROM flags "
)
_FLAG_BY_ID = _FLAG_SELECT + "WHERE id = ?"
_FLAGS_ORDERED = _FLAG_SELECT + "ORDER BY flagged_at DESC, id DESC"


def _session(r: tuple[object, ...]) -> StaffSessionRow:
    return StaffSessionRow(
        token_hash=str(r[0]),
        session_id=LoginSessionId(str(r[1])),
        role=DemoRole(str(r[2])),
        role_reset_pending=bool(r[3]),
        signed_in_demo=parse_wall(str(r[4])),
        created_real=parse_wall(str(r[5])),
        expires_real=parse_wall(str(r[6])),
    )


def _flag(r: tuple[object, ...]) -> FlagRow:
    return FlagRow.model_validate(
        {
            "id": r[0],
            "case_ref": r[1],
            "target": r[2],
            "message_id": r[3],
            "note": r[4],
            "reason": r[5],
            "flagged_by_role": r[6],
            "flagged_at": parse_wall(str(r[7])),
            "status": r[8],
            "reviewed_by_role": r[9],
            "reviewed_note": r[10],
            "reviewed_at": None if r[11] is None else parse_wall(str(r[11])),
        }
    )


class StaffSessionsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, row: StaffSessionRow) -> None:
        with integrity_errors("staff_sessions"):
            self._conn.execute(
                _INSERT_SESSION,
                (
                    row.token_hash,
                    row.session_id,
                    row.role.value,
                    1 if row.role_reset_pending else 0,
                    format_wall(row.signed_in_demo),
                    format_wall(row.created_real),
                    format_wall(row.expires_real),
                ),
            )

    def by_token_hash(self, token_hash: str) -> StaffSessionRow | None:
        r = self._conn.execute(
            _SESSION_BY_HASH,
            (token_hash,),
        ).fetchone()
        return None if r is None else _session(tuple(r))

    def by_session_id(self, session_id: LoginSessionId) -> StaffSessionRow | None:
        r = self._conn.execute(
            _SESSION_BY_ID,
            (session_id,),
        ).fetchone()
        return None if r is None else _session(tuple(r))

    def set_role(self, session_id: LoginSessionId, role: DemoRole) -> bool:
        """Role and reset marker change together in one statement."""
        cur = self._conn.execute(
            "UPDATE staff_sessions SET role = ?, role_reset_pending = 0 WHERE session_id = ?",
            (role.value, session_id),
        )
        return cur.rowcount == 1

    def delete(self, token_hash: str) -> None:
        self._conn.execute("DELETE FROM staff_sessions WHERE token_hash = ?", (token_hash,))


class FlagsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, row: FlagRow) -> int:
        with integrity_errors("flags"):
            cur = self._conn.execute(
                "INSERT INTO flags (case_ref, target, message_id, note, reason, flagged_by_role, flagged_at, "
                "status, reviewed_by_role, reviewed_note, reviewed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row.case_ref),
                    row.target,
                    row.message_id,
                    row.note,
                    row.reason,
                    row.flagged_by_role.value,
                    format_wall(row.flagged_at),
                    row.status,
                    None if row.reviewed_by_role is None else row.reviewed_by_role.value,
                    row.reviewed_note,
                    None if row.reviewed_at is None else format_wall(row.reviewed_at),
                ),
            )
        return last_row_id(cur, "flags")

    def get(self, flag_id: int) -> FlagRow | None:
        r = self._conn.execute(_FLAG_BY_ID, (flag_id,)).fetchone()
        return None if r is None else _flag(tuple(r))

    def review(self, flag_id: int, by_role: StaffRole, note: str | None, at: datetime) -> bool:
        cur = self._conn.execute(
            "UPDATE flags SET status = 'reviewed', reviewed_by_role = ?, reviewed_note = ?, reviewed_at = ? "
            "WHERE id = ?",
            (by_role.value, note, format_wall(at), flag_id),
        )
        return cur.rowcount == 1

    def list_ordered(self) -> tuple[FlagRow, ...]:
        rows = self._conn.execute(_FLAGS_ORDERED).fetchall()
        return tuple(_flag(tuple(r)) for r in rows)


class StaffRepos:
    """Staff sessions and flags, reached as ``UnitOfWork.staff``."""

    sessions: StaffSessionsRepo
    flags: FlagsRepo

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.sessions = StaffSessionsRepo(conn)
        self.flags = FlagsRepo(conn)
