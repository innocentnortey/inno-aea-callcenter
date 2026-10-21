"""First boot, schema files and the in-place reset helper for the issued tables (AEA-10; cases.md 1.3, 1.4, DO-1 section 9).

The issued scheduling file is only ever read: copied with ``shutil.copyfile`` on first boot, and read through a
separate ``mode=ro&immutable=1`` connection by ``restore_working_copy``. This module imports no repository.
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from meridian.adapters.sqlite.db import SqliteUnitOfWork, connect

if TYPE_CHECKING:
    from meridian.ports.runtime import UnitOfWork

WORKING_DB_NAME = "meridian.sqlite"
SCHEMA_DIR = Path(__file__).with_name("schema")
ISSUED_TABLES = ("customers", "technicians", "appointment_slots", "appointments", "invoices")  # parents first
CLEARED_TABLES = (  # children first (delete order)
    "lookup_log",
    "check_events",
    "actions",
    "turns",
    "messages",
    "events",
    "case_briefs",
    "activities",
    "followups",
    "promises",
    "case_events",
    "cases",
    "conversations",
    "flags",
    "identity_codes",
    "demo_inbox",
    "identity_threads",
)
UPDATED_TABLES = ("staff_sessions", "demo_state")
KEPT_TABLES = (
    "spend_ledger",
    "health_events",
    "deploy_records",
    "eval_runs",
    "eval_case_results",
    "job_runs",
    "demo_events",
    "reset_events",
    "seed_events",
    "ended_threads",
)

_SCHEMA_NAME = re.compile(r"^\d{2}_[a-z_]+\.sql$")


def schema_files() -> tuple[Path, ...]:
    """Every schema/NN_name.sql, in numeric order."""
    files = list(SCHEMA_DIR.glob("*.sql"))
    for path in files:
        if not _SCHEMA_NAME.match(path.name):
            raise ValueError("bad schema file name")
    return tuple(sorted(files, key=lambda p: int(p.name.split("_", 1)[0])))


def migrate(db_path: Path, *, issued_path: Path) -> bool:
    """Copy the issued file when the working copy is missing, then apply every schema file. True when copied."""
    copied = False
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = db_path.with_name(db_path.name + ".tmp")
        shutil.copyfile(issued_path, tmp)
        os.replace(tmp, db_path)  # atomic: a crash mid-copy never leaves a half file at db_path
        copied = True
    conn = connect(db_path)
    try:
        for path in schema_files():
            conn.executescript("BEGIN;\n" + path.read_text(encoding="utf-8") + "\nCOMMIT;")
    finally:
        conn.close()
    return copied


def restore_working_copy(tx: UnitOfWork, *, issued_path: Path) -> None:
    """Return the five issued tables to the issued rows inside the caller's transaction. Never commits."""
    if not isinstance(tx, SqliteUnitOfWork):
        raise TypeError("restore_working_copy needs a SqliteUnitOfWork")
    dst = tx.connection
    if not dst.in_transaction:
        raise RuntimeError("restore needs an open write transaction")
    snapshot: dict[str, tuple[list[str], list[tuple[object, ...]]]] = {}
    src = sqlite3.connect(f"{issued_path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        for table in ISSUED_TABLES:
            cur = src.execute(f"SELECT * FROM {table} ORDER BY rowid")  # noqa: S608 - module constant table name
            snapshot[table] = ([d[0] for d in cur.description], cur.fetchall())
    finally:
        src.close()
    for table in reversed(ISSUED_TABLES):
        dst.execute(f"DELETE FROM {table}")  # noqa: S608 - module constant table name
    for table in ISSUED_TABLES:
        cols, rows = snapshot[table]
        marks = ",".join("?" for _ in cols)
        dst.executemany(
            f"INSERT INTO {table} ({','.join(cols)}) VALUES ({marks})",  # noqa: S608 - constant table, issued columns
            rows,
        )
    has_sequence = dst.execute("SELECT 1 FROM sqlite_master WHERE name = 'sqlite_sequence'").fetchone()
    if has_sequence:
        for table in ISSUED_TABLES:
            _, rows = snapshot[table]
            ints = [r[0] for r in rows if isinstance(r[0], int)]
            if not ints:
                continue
            # the issued tables are not AUTOINCREMENT today, so this updates no row; kept so the rule holds if one is
            top = max(ints)
            dst.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = ?", (top, table))
