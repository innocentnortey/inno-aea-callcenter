"""Read-only DB reader and issued-table helpers for journey assertions (AEA-57; integrated-journeys rule section 3.2)."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from tests.fixtures.sqlite import ISSUED_DB

_TABLE_NAME = re.compile(r"^[a-z_]+$")


class DbReader:
    """Opens the working copy with `mode=ro`, one connection per assertion, never holding a transaction."""

    def __init__(self, db_path: Path) -> None:
        self._path = db_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(
            f"{self._path.resolve().as_uri()}?mode=ro", uri=True, isolation_level=None, timeout=5.0
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def rows(self, sql: str, params: Sequence[object] = ()) -> list[dict[str, Any]]:
        with self.connect() as conn:
            found = [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]
            if conn.in_transaction:
                raise AssertionError("DbReader left a transaction open")
        return found

    def one(self, sql: str, params: Sequence[object] = ()) -> dict[str, Any]:
        found = self.rows(sql, params)
        if len(found) != 1:
            raise AssertionError(f"expected exactly one row, got {len(found)}")
        return found[0]

    def scalar(self, sql: str, params: Sequence[object] = ()) -> Any:
        row = self.one(sql, params)
        return next(iter(row.values()))

    def count(self, table: str, where: str = "", params: Sequence[object] = ()) -> int:
        if not _TABLE_NAME.match(table):
            raise ValueError(f"not a table name: {table!r}")
        sql = f"SELECT COUNT(*) AS n FROM {table}" + (f" WHERE {where}" if where else "")  # noqa: S608
        return int(self.one(sql, params)["n"])

    def table_rows(self, table: str) -> list[tuple[Any, ...]]:
        if not _TABLE_NAME.match(table):
            raise ValueError(f"not a table name: {table!r}")
        with self.connect() as conn:
            conn.row_factory = None
            return [tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()]  # noqa: S608


def issued_rows(table: str, issued_path: Path = ISSUED_DB) -> list[tuple[Any, ...]]:
    if not _TABLE_NAME.match(table):
        raise ValueError(f"not a table name: {table!r}")
    conn = sqlite3.connect(f"{issued_path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        return [tuple(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()]  # noqa: S608
    finally:
        conn.close()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
