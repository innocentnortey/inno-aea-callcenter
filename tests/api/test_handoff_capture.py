"""AEA-42 AC-19 (capture, WF-2): both entry points leave a `request` record; CON-4 leaves its `turn` row."""

from __future__ import annotations

from pathlib import Path

import pytest

from meridian.adapters.tracing_langfuse import NullTraceSink
from tests.api.handoff_support import (
    FOLLOW_UP_PATH,
    HANDOFF_PATH,
    customer_token,
    handoff_app,
    request_example,
    thread_for,
)
from tests.api.web_shell_support import captured_log, cookie_header, make_client, records_of
from tests.fixtures.sqlite import temp_sqlite
from tests.services.person_request_support import verify_thread


def test_wf2_entry_points_emit_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-19): one request record per call; the CON-4 turn row carries the code fields and export status."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db, trace=NullTraceSink())
        token = customer_token(h)
        thread = thread_for(h, token)
        verify_thread(db, thread)
        with captured_log() as stream, make_client(h.app) as client:
            post = client.post(
                HANDOFF_PATH.format(thread_id=thread),
                json=request_example(HANDOFF_PATH, "post", "BUTTON"),
                headers=cookie_header(token),
            )
            put = client.put(
                FOLLOW_UP_PATH.format(thread_id=thread),
                json=request_example(FOLLOW_UP_PATH, "put", "PHONE_MORNINGS"),
                headers=cookie_header(token),
            )
        records = records_of(stream, "request")
        assert len(records) == 2
        for record, resp, route in (
            (records[0], post, HANDOFF_PATH),
            (records[1], put, FOLLOW_UP_PATH),
        ):
            assert record["route"] == route
            assert record["status"] == 200
            assert record["caller_role"] == "customer"
            assert record["thread_id"] == str(thread)
            assert record["request_id"] == resp.headers["X-Request-ID"]
        with db.uow() as tx:
            (row,) = tx.core.turns.for_thread(thread)
        assert row.gate_result == "person_requested"
        assert row.path == "handoff"
        assert row.outcome == "handed_off"
        assert row.trace_id is None
        assert row.trace_export == "off"
        print("request records:", records)
        print("turn row:", row.gate_result, row.path, row.outcome, row.trace_id, row.trace_export)
