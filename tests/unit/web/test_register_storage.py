"""AEA-10 PA-6: the register_storage hunk migrates the working copy and exposes the factory, checkpointer and restore."""

from __future__ import annotations

import sqlite3
import types
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from meridian.adapters.checkpointer import Checkpointer
from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
from meridian.policy.limits import Limits
from meridian.web.container import Container, Key, register_storage
from tests.fixtures.sqlite import ISSUED_DB
from tests.unit.adapters.sqlite.helpers import customer_id


def test_register_storage_migrates_and_exposes_factory(tmp_path: Path) -> None:
    settings = types.SimpleNamespace(data_dir=tmp_path / "data", issued_db_path=ISSUED_DB)
    c = Container(settings=settings, limits=Limits())
    register_storage(c, FastAPI(), settings=settings, limits=c.limits)
    c.build()
    uow: Any = c.get(Key[Any]("uow_factory"))
    assert isinstance(uow, SqliteUnitOfWorkFactory)
    db = tmp_path / "data" / "meridian.sqlite"
    assert db.exists()
    conn = sqlite3.connect(db)
    try:
        counts = [
            conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # noqa: S608
            for t in ("customers", "technicians", "appointment_slots", "appointments", "invoices")
        ]
    finally:
        conn.close()
    assert counts == [154, 8, 528, 159, 81]
    with uow() as tx:
        assert tx.core.reads.customer(customer_id("MHC-10001")) is not None
    cp: Any = c.get(Key[Any]("checkpointer"))
    assert isinstance(cp, Checkpointer)
    assert cp.path == tmp_path / "data" / "checkpoints.sqlite"
    restore: Any = c.get(Key[Any]("restore_working_copy"))
    with uow(write=True) as tx:
        restore(tx)
        tx.commit()
    c.close()
    assert cp.closed is True
    doc = register_storage.__doc__ or ""
    assert "AEA-10" in doc
    assert "No-op until" not in doc
