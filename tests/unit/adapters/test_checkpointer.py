"""AEA-10 AC-19: the checkpointer on its own file."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from langgraph.checkpoint.base import empty_checkpoint

from meridian.adapters.checkpointer import CHECKPOINTS_DB_NAME, Checkpointer
from meridian.adapters.sqlite.migrate import WORKING_DB_NAME, migrate
from tests.fixtures.sqlite import ISSUED_DB


@pytest.fixture
def cp(tmp_path: Path) -> Iterator[Checkpointer]:
    c = Checkpointer(tmp_path / CHECKPOINTS_DB_NAME)
    yield c
    c.close()


def _put(cp: Checkpointer, thread: str, n: int) -> list[str]:
    cfg: Any = {"configurable": {"thread_id": thread, "checkpoint_ns": ""}}
    ids = []
    for i in range(n):
        cfg = cp.saver.put(cfg, empty_checkpoint(), {"source": "loop", "step": i, "parents": {}}, {})
        ids.append(cfg["configurable"]["checkpoint_id"])
    return ids


def _count(cp: Checkpointer, thread: str | None = None) -> int:
    conn = sqlite3.connect(cp.path)
    try:
        if thread is None:
            return int(conn.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0])
        return int(
            conn.execute("SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?", (thread,)).fetchone()[0]
        )
    finally:
        conn.close()


def test_uses_own_file(tmp_path: Path) -> None:
    migrate(tmp_path / WORKING_DB_NAME, issued_path=ISSUED_DB)
    c = Checkpointer(tmp_path / CHECKPOINTS_DB_NAME)
    try:
        saver_db = sqlite3.connect(c.path)
        main_db = sqlite3.connect(tmp_path / WORKING_DB_NAME)
        try:
            saver_tables = {
                r[0] for r in saver_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            main_tables = {r[0] for r in main_db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            saver_db.close()
            main_db.close()
        assert {"checkpoints", "writes"} <= saver_tables
        assert not {"checkpoints", "writes"} & main_tables
        assert c.path.name == "checkpoints.sqlite"
    finally:
        c.close()


def test_prune_keeps_last_two(cp: Checkpointer) -> None:
    ids = _put(cp, "t-prune", 5)
    other = _put(cp, "t-other", 3)
    assert cp.prune(keep=2) == 3 + 1
    conn = sqlite3.connect(cp.path)
    try:
        kept = [r[0] for r in conn.execute("SELECT checkpoint_id FROM checkpoints WHERE thread_id='t-prune'")]
        kept_other = [
            r[0] for r in conn.execute("SELECT checkpoint_id FROM checkpoints WHERE thread_id='t-other'")
        ]
    finally:
        conn.close()
    assert sorted(kept) == sorted(ids[-2:])
    assert sorted(kept_other) == sorted(other[-2:])
    assert cp.prune(keep=2) == 0
    with pytest.raises(ValueError):
        cp.prune(keep=0)


def test_prune_five_to_two_returns_three(cp: Checkpointer) -> None:
    _put(cp, "t-prune", 5)
    assert cp.prune(keep=2) == 3
    assert _count(cp, "t-prune") == 2


def test_clear_empties(cp: Checkpointer) -> None:
    _put(cp, "a", 2)
    _put(cp, "b", 2)
    cp.clear()
    assert _count(cp) == 0


def test_clearing_rolls_back_on_raise_and_commits_on_clean_exit(cp: Checkpointer) -> None:
    _put(cp, "a", 3)
    with pytest.raises(RuntimeError), cp.clearing():
        raise RuntimeError("boom")
    assert _count(cp) == 3
    with cp.clearing():
        pass
    assert _count(cp) == 0
    cp.close()
    cp.close()  # idempotent
    assert cp.closed
