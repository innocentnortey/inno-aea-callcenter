"""AEA-41 AC-14 (capture): the real app records one `request` per stream and one `stream_reconnect` per reconnect.

Failure mode guarded: the stream runs but leaves no record, or a record with the wrong ids or counts. CAP-4 end to end
with the real writers is AEA-52's.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import anyio
import pytest

from meridian.web.deps import UOW_FACTORY
from meridian.web.routes.events import EVENTS_PATH
from tests.api.events_support import (
    TAKEOVER_TRIO,
    append_stored,
    close_stream,
    full_stream_app,
    open_stream,
    payload,
    read_frames,
    running,
    seed_conversation,
    session_of,
)
from tests.api.web_shell_support import FakeSessionStore, captured_log, new_thread_id, records_of


def test_stream_request_and_reconnect_recorded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-14): two connections leave two request records; only the reconnect leaves stream_reconnect."""
    sessions = FakeSessionStore()
    token = sessions.issue()
    app = full_stream_app(monkeypatch, tmp_path, store=sessions)
    holder: dict[str, Any] = {"ids": []}

    async def scenario() -> None:
        async with running(app) as tg:
            uow = app.state.container.get(UOW_FACTORY)
            tid = seed_conversation(uow, session_of(sessions, token))
            other = new_thread_id()
            append_stored(uow, other, [("case_changed", payload("case_changed"))] * 11)
            ids = append_stored(uow, tid, [(k, payload(k)) for k in TAKEOVER_TRIO])
            assert ids == [12, 13, 14]
            holder["tid"] = tid
            with captured_log() as log:
                first = await open_stream(tg, app, tid, token=token, last_event_id="12")
                await read_frames(first, 2)
                await close_stream(first)
                second = await open_stream(tg, app, tid, token=token)
                await read_frames(second, 3)
                await close_stream(second)
            holder["log"] = log.getvalue()
            holder["request_ids"] = [first.headers["x-request-id"], second.headers["x-request-id"]]

    anyio.run(scenario)

    stream = io.StringIO(holder["log"])
    requests = records_of(stream, "request")
    assert len(requests) == 2
    for record, request_id in zip(requests, holder["request_ids"], strict=True):
        assert record["route"] == EVENTS_PATH
        assert record["status"] == 200
        assert record["thread_id"] == holder["tid"]
        assert record["caller_role"] == "customer"
        assert record["request_id"] == request_id
    assert records_of(stream, "stream_reconnect") == [
        {
            "record": "stream_reconnect",
            "request_id": holder["request_ids"][0],
            "thread_id": holder["tid"],
            "last_event_id": 12,
            "replayed": 2,
        }
    ]
