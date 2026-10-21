"""``temp_sqlite()``: a temporary working copy with every schema file applied, removed afterwards (AEA-10; CAS-4, S-6)."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
from meridian.adapters.sqlite.migrate import WORKING_DB_NAME, migrate

ISSUED_DB = (
    Path(__file__).resolve().parents[2]
    / "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
)


@dataclass(frozen=True)
class TempStore:
    data_dir: Path
    db_path: Path
    issued_path: Path
    uow: SqliteUnitOfWorkFactory


@contextmanager
def temp_sqlite(*, issued_path: Path = ISSUED_DB) -> Iterator[TempStore]:
    data_dir = Path(tempfile.mkdtemp(prefix="meridian-test-"))
    try:
        db_path = data_dir / WORKING_DB_NAME
        migrate(db_path, issued_path=issued_path)
        yield TempStore(data_dir, db_path, issued_path, SqliteUnitOfWorkFactory(db_path))
    finally:
        shutil.rmtree(data_dir, ignore_errors=True)
