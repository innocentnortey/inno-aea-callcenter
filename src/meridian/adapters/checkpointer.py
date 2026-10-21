"""The LangGraph checkpointer over its own file, ``checkpoints.sqlite`` (AEA-10; DO-1 sections 4 and 9, CAS-2, SDQ-10).

Separate from ``meridian.sqlite`` so a reset can clear it in its own transaction (``clearing()``). The saver is what
AEA-51 compiles the graph with.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from meridian.adapters.sqlite.db import BUSY_TIMEOUT_MS

CHECKPOINTS_DB_NAME = "checkpoints.sqlite"


class Checkpointer:
    def __init__(self, path: Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._busy_timeout_ms = busy_timeout_ms
        self._closed = False
        self._conn = sqlite3.connect(str(path), check_same_thread=False, timeout=busy_timeout_ms / 1000)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
        self._saver = SqliteSaver(self._conn)
        self._saver.setup()  # tables exist before any prune or clear

    @property
    def saver(self) -> SqliteSaver:
        return self._saver

    @property
    def path(self) -> Path:
        return self._path

    @property
    def closed(self) -> bool:
        return self._closed

    def _own(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self._path),
            timeout=self._busy_timeout_ms / 1000,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.execute(f"PRAGMA busy_timeout={int(self._busy_timeout_ms)}")
        return conn

    def prune(self, keep: int = 2) -> int:
        """Leave each thread its newest ``keep`` checkpoints [Decided SDQ-10]; returns the number removed."""
        if keep < 1:
            raise ValueError("keep must be >= 1")
        conn = self._own()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                # checkpoint ids are time-ordered, so DESC keeps the newest
                removed = conn.execute(
                    "DELETE FROM checkpoints WHERE rowid IN (SELECT rowid FROM (SELECT rowid, ROW_NUMBER() OVER "
                    "(PARTITION BY thread_id, checkpoint_ns ORDER BY checkpoint_id DESC) AS rn FROM checkpoints) "
                    "WHERE rn > ?)",
                    (keep,),
                ).rowcount
                conn.execute(
                    "DELETE FROM writes WHERE NOT EXISTS (SELECT 1 FROM checkpoints c WHERE c.thread_id = writes.thread_id "
                    "AND c.checkpoint_ns = writes.checkpoint_ns AND c.checkpoint_id = writes.checkpoint_id)"
                )
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            return int(removed)
        finally:
            conn.close()

    @contextmanager
    def clearing(self) -> Iterator[None]:
        """Delete every saver table's rows; commit on a clean exit, roll back when the block raises (CAS-2)."""
        conn = self._own()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                tables = [
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                ]
                for name in tables:
                    conn.execute(f'DELETE FROM "{name}"')  # noqa: S608 - names read from sqlite_master
                yield
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        finally:
            conn.close()

    def clear(self) -> None:
        with self.clearing():
            pass

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._conn.close()
