"""SQLite working copy of the issued scheduling DB, plus the new case-store tables.

The issued file is never written (audit G-7). `reset()` copies it fresh and re-creates our tables.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from meridian.config import ISSUED_DB, SETTINGS

_LOCK = threading.RLock()  # one writer at a time (SQLite); fine at ~20 concurrent chats (PRD §5)

CASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS conversations (
  thread_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, controller TEXT NOT NULL DEFAULT 'ai',
  customer_id TEXT, verified INTEGER NOT NULL DEFAULT 0, outcome TEXT, case_id TEXT,
  bookings INTEGER NOT NULL DEFAULT 0, last_activity TEXT
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, role TEXT NOT NULL,
  author TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL, meta TEXT
);
CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, created_at TEXT NOT NULL, reason TEXT NOT NULL,
  priority TEXT NOT NULL, state TEXT NOT NULL, owner TEXT, next_action TEXT, due_at TEXT,
  promise_text TEXT NOT NULL, promise_status TEXT NOT NULL DEFAULT 'open',
  followup_channel TEXT, followup_destination TEXT, destination_on_record INTEGER, followup_window TEXT,
  customer_id TEXT, identity_status TEXT NOT NULL, brief TEXT NOT NULL, demo_seed INTEGER NOT NULL DEFAULT 0,
  outcome TEXT, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS case_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL, at TEXT NOT NULL, actor TEXT NOT NULL,
  event TEXT NOT NULL, detail TEXT
);
CREATE TABLE IF NOT EXISTS lookup_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, at TEXT NOT NULL, tool TEXT NOT NULL,
  record_ref TEXT, args TEXT, result TEXT, used_by TEXT
);
CREATE TABLE IF NOT EXISTS verification_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, customer_id TEXT NOT NULL,
  channel TEXT NOT NULL, destination_masked TEXT NOT NULL, code_hash TEXT NOT NULL, created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, used INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS demo_inbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, channel TEXT NOT NULL, destination TEXT NOT NULL,
  body TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, thread_id TEXT, at TEXT NOT NULL, kind TEXT NOT NULL,
  note TEXT, reviewed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, thread_id TEXT, kind TEXT NOT NULL,
  value REAL, detail TEXT
);
"""


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def reset() -> None:
    """Fresh working copy from the issued DB, plus empty case-store tables."""
    SETTINGS.var_dir.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        for suffix in ("", "-wal", "-shm"):
            Path(str(SETTINGS.db_path) + suffix).unlink(missing_ok=True)
        shutil.copyfile(ISSUED_DB, SETTINGS.db_path)
        conn = _connect(SETTINGS.db_path)
        conn.executescript(CASE_SCHEMA)
        conn.commit()
        conn.close()
        for suffix in ("", "-wal", "-shm"):
            Path(str(SETTINGS.checkpoint_path) + suffix).unlink(missing_ok=True)


def ensure() -> None:
    if not SETTINGS.db_path.exists():
        reset()
    else:
        with connect() as conn:
            conn.executescript(CASE_SCHEMA)


@contextmanager
def connect():
    with _LOCK:
        conn = _connect(SETTINGS.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def get_setting(key: str, default: str | None = None) -> str | None:
    if not SETTINGS.db_path.exists():
        return default
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def get_setting_int(key: str, default: int) -> int:
    try:
        return int(get_setting(key, str(default)) or default)
    except (ValueError, sqlite3.OperationalError):
        return default


def set_setting(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                     (key, value))


def log_metric(kind: str, value: float | None = None, thread_id: str | None = None, detail: dict | None = None):
    from meridian.config import now

    with connect() as conn:
        conn.execute("INSERT INTO metrics(at,thread_id,kind,value,detail) VALUES(?,?,?,?,?)",
                     (now().isoformat(timespec="seconds"), thread_id, kind, value,
                      json.dumps(detail) if detail else None))
