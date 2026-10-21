"""SQLite connections, the wall-time formatter and the unit of work (AEA-10; cases.md 1.0, CAS-35).

One connection per unit of work. Every transaction is an explicit ``BEGIN`` the factory issues; a unit of work commits
only when ``commit()`` ran and nothing raised after it. Storage errors name the table and the constraint, never a value.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meridian.adapters.sqlite.repos_booking import BookingRepos
    from meridian.adapters.sqlite.repos_cases import CaseRepos
    from meridian.adapters.sqlite.repos_core import CoreRepos
    from meridian.adapters.sqlite.repos_identity import IdentityRepos
    from meridian.adapters.sqlite.repos_ops import OpsRepos
    from meridian.adapters.sqlite.repos_spend import SpendRepo
    from meridian.adapters.sqlite.repos_staff import StaffRepos

BUSY_TIMEOUT_MS = 5000  # [A] DO-3 section 4.3 "busy_timeout 5 s"; replaced by the Stage 9 load re-measure


class StorageError(Exception):
    """A storage failure naming the table and the constraint kind, never a value (safe-validation-errors)."""

    def __init__(self, table: str, constraint: str) -> None:
        super().__init__(f"{table}: {constraint}")
        self.table = table
        self.constraint = constraint


_KINDS = ("UNIQUE", "FOREIGN KEY", "CHECK", "NOT NULL")


@contextmanager
def integrity_errors(table: str) -> Iterator[None]:
    """Turn a sqlite3.IntegrityError into a StorageError that copies nothing of the sqlite message."""
    try:
        yield
    except sqlite3.IntegrityError as exc:
        message = str(exc)
        kind = next((k for k in _KINDS if message.startswith(k)), "INTEGRITY")
        raise StorageError(table, kind) from None


def connect(
    path: Path, *, read_only: bool = False, busy_timeout_ms: int = BUSY_TIMEOUT_MS
) -> sqlite3.Connection:
    """Open a connection: WAL, busy timeout, foreign keys on, no implicit transactions."""
    timeout = busy_timeout_ms / 1000
    if read_only:
        conn = sqlite3.connect(
            f"{path.resolve().as_uri()}?mode=ro",
            uri=True,
            timeout=timeout,
            isolation_level=None,
            check_same_thread=False,
        )
    else:
        conn = sqlite3.connect(str(path), timeout=timeout, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def format_wall(dt: datetime) -> str:
    """The one wall-time format: UTC ISO-8601 (MC-20). A naive datetime is a bug."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("naive datetime")
    return dt.astimezone(UTC).isoformat()


def parse_wall(text: str) -> datetime:
    """Inverse of format_wall: tz-aware, UTC."""
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("naive timestamp")
    return parsed.astimezone(UTC)


def last_row_id(cur: sqlite3.Cursor, table: str) -> int:
    rid = cur.lastrowid
    if rid is None:
        raise StorageError(table, "no row id")
    return int(rid)


class SqliteUnitOfWork:
    """Implements ports.runtime.UnitOfWork: the seven repositories over one connection."""

    core: CoreRepos
    spend: SpendRepo
    identity: IdentityRepos
    booking: BookingRepos
    cases: CaseRepos
    staff: StaffRepos
    ops: OpsRepos

    def __init__(self, conn: sqlite3.Connection) -> None:
        # repositories import this module's helpers; a top-level import would be circular
        from meridian.adapters.sqlite.repos_booking import BookingRepos
        from meridian.adapters.sqlite.repos_cases import CaseRepos
        from meridian.adapters.sqlite.repos_core import CoreRepos
        from meridian.adapters.sqlite.repos_identity import IdentityRepos
        from meridian.adapters.sqlite.repos_ops import OpsRepos
        from meridian.adapters.sqlite.repos_spend import SpendRepo
        from meridian.adapters.sqlite.repos_staff import StaffRepos

        self._conn = conn
        self._committed = False
        self.core = CoreRepos(conn)
        self.spend = SpendRepo(conn)
        self.identity = IdentityRepos(conn)
        self.booking = BookingRepos(conn)
        self.cases = CaseRepos(conn)
        self.staff = StaffRepos(conn)
        self.ops = OpsRepos(conn)

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    @property
    def committed(self) -> bool:
        return self._committed

    def commit(self) -> None:
        if self._committed:
            return
        self._conn.execute("COMMIT")
        self._committed = True


class SqliteUnitOfWorkFactory:
    """Implements ports.runtime.UnitOfWorkFactory: a new connection per unit of work."""

    def __init__(self, db_path: Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS) -> None:
        self._db_path = db_path
        self._busy_timeout_ms = busy_timeout_ms

    @property
    def db_path(self) -> Path:
        return self._db_path

    @contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[SqliteUnitOfWork]:
        conn = connect(self._db_path, busy_timeout_ms=self._busy_timeout_ms)
        try:
            # a lock timeout raises here, before the caller's block runs: no statement executes (AC-9)
            if exclusive:
                conn.execute("BEGIN EXCLUSIVE")
            elif write:
                conn.execute("BEGIN IMMEDIATE")
            else:
                conn.execute("PRAGMA query_only=ON")
                conn.execute("BEGIN DEFERRED")
        except BaseException:
            conn.close()
            raise
        uow = SqliteUnitOfWork(conn)
        try:
            try:
                yield uow
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        finally:
            if not uow.committed and conn.in_transaction:
                conn.execute("ROLLBACK")
            conn.close()
