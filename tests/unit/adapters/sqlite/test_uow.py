"""AEA-10 AC-8 to AC-11: connections, units of work, the lock timeout and the wall-time formatter."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterator
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from meridian.adapters.sqlite.db import (
    SqliteUnitOfWork,
    SqliteUnitOfWorkFactory,
    format_wall,
    parse_wall,
)
from meridian.adapters.sqlite.repos_booking import BookingRepos
from meridian.adapters.sqlite.repos_cases import CaseRepos
from meridian.adapters.sqlite.repos_core import CoreRepos
from meridian.adapters.sqlite.repos_identity import IdentityRepos
from meridian.adapters.sqlite.repos_ops import OpsRepos
from meridian.adapters.sqlite.repos_spend import SpendRepo
from meridian.adapters.sqlite.repos_staff import StaffRepos
from meridian.ports.runtime import UnitOfWorkFactory
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.adapters.sqlite.helpers import conversation, new_thread


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _count(store: TempStore, table: str) -> int:
    with store.uow() as tx:
        return int(tx.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608


def test_pragmas_commit_and_rollback(store: TempStore) -> None:
    with store.uow() as tx:
        pragmas = tuple(
            tx.connection.execute(f"PRAGMA {p}").fetchone()[0]
            for p in ("journal_mode", "busy_timeout", "foreign_keys")
        )
    print("journal_mode, busy_timeout, foreign_keys =", pragmas)
    assert pragmas == ("wal", 5000, 1)

    with store.uow(write=True) as tx:  # no commit: rolls back
        tx.core.conversations.insert(conversation(new_thread()))
    assert _count(store, "conversations") == 0

    with pytest.raises(RuntimeError), store.uow(write=True) as tx:  # exception: rolls back and propagates
        tx.core.conversations.insert(conversation(new_thread()))
        raise RuntimeError("boom")
    assert _count(store, "conversations") == 0

    with pytest.raises(sqlite3.OperationalError), store.uow() as tx:  # write=False: query_only
        tx.core.conversations.insert(conversation(new_thread()))

    with store.uow(write=True) as tx:
        tx.core.conversations.insert(conversation(new_thread()))
        tx.commit()
        tx.commit()  # a second commit is a no-op
        assert tx.committed
    assert _count(store, "conversations") == 1


def test_lock_timeout_writes_nothing(store: TempStore) -> None:
    short = SqliteUnitOfWorkFactory(store.db_path, busy_timeout_ms=200)
    ran = False
    with store.uow(exclusive=True):
        started = time.monotonic()
        with pytest.raises(sqlite3.OperationalError), short(write=True) as tx:
            ran = True
            tx.core.conversations.insert(conversation(new_thread()))
        elapsed = time.monotonic() - started
    assert not ran
    assert elapsed >= 0.15
    assert _count(store, "conversations") == 0
    assert _count(store, "events") == 0


def test_seven_repos_and_port_imports_no_adapter(store: TempStore) -> None:
    factory: UnitOfWorkFactory = SqliteUnitOfWorkFactory(store.db_path)
    with factory() as tx:
        assert isinstance(tx, SqliteUnitOfWork)
        expected = {
            "core": CoreRepos,
            "spend": SpendRepo,
            "identity": IdentityRepos,
            "booking": BookingRepos,
            "cases": CaseRepos,
            "staff": StaffRepos,
            "ops": OpsRepos,
        }
        for name, cls in expected.items():
            repo = getattr(tx, name)
            assert isinstance(repo, cls), name
            assert vars(repo)["_conn"] is tx.connection, name
    out = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, meridian.ports.runtime; "
            "print(sorted(m for m in sys.modules if m.startswith('meridian.adapters')))",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert out == "[]"


def test_wall_time_formatter() -> None:
    chicago = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
    text = format_wall(chicago)
    assert text == "2026-10-16T15:00:00+00:00"
    parsed = parse_wall(text)
    assert parsed == chicago
    assert parsed.tzinfo is not None
    with pytest.raises(ValueError):
        format_wall(datetime(2026, 10, 16, 10, 0))
    with pytest.raises(ValueError):
        parse_wall("2026-10-16T10:00:00")
    base = datetime(2026, 10, 16, 15, 0, tzinfo=ZoneInfo("UTC"))
    later = base + timedelta(microseconds=1)
    assert format_wall(base) < format_wall(later)
