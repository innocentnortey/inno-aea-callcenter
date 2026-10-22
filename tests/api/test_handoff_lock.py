"""FU-person-request F-4 through the real app, middleware and AEA-42 hunk: a held SQLite write lock answers 503
HANDOFF_FAILED matching the OpenAPI, with no raw error text. Synthetic data.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from pathlib import Path

import pytest

from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
from tests.api.handoff_support import HANDOFF_PATH, customer_token, handoff_app, thread_for
from tests.api.web_shell_support import app_log_text, assert_matches, cookie_header, error_body, make_client
from tests.fixtures.sqlite import TempStore, temp_sqlite


def test_held_write_lock_gives_503_matching_openapi(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """failure (F-4, AC-48): a write lock held past busy_timeout is 503 HANDOFF_FAILED and writes nothing."""
    caplog.set_level(logging.DEBUG)
    with temp_sqlite() as db:
        fast = TempStore(
            db.data_dir, db.db_path, db.issued_path, SqliteUnitOfWorkFactory(db.db_path, busy_timeout_ms=200)
        )
        h = handoff_app(monkeypatch, tmp_path, fast)
        token = customer_token(h)
        thread = str(thread_for(h, token))
        turn_id = str(uuid.uuid4())
        with make_client(h.app) as client:
            holder = sqlite3.connect(str(db.db_path), isolation_level=None, timeout=0)
            holder.execute("BEGIN IMMEDIATE")
            try:
                resp = client.post(
                    HANDOFF_PATH.format(thread_id=thread),
                    json={"turn_id": turn_id},
                    headers=cookie_header(token),
                )
            finally:
                holder.execute("ROLLBACK")
                holder.close()
        data = error_body(resp, 503, "HANDOFF_FAILED")
        assert data["error"]["details"]["retry_after_ms"] > 0
        assert_matches(resp, "requestPerson")
        assert h.handoff.calls == []
        conn = sqlite3.connect(db.db_path)
        try:
            cases = conn.execute("SELECT COUNT(*) FROM cases WHERE thread_id = ?", (thread,)).fetchone()[0]
            turns = conn.execute("SELECT COUNT(*) FROM turns WHERE turn_id = ?", (turn_id,)).fetchone()[0]
        finally:
            conn.close()
        assert cases == 0
        assert turns == 0
        for needle in ("database is locked", "OperationalError"):
            assert needle not in app_log_text(caplog)
            assert needle not in caplog.text
            assert needle not in resp.text
