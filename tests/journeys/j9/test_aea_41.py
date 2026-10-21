"""J-9 (slice plan section 0a): a dropped chat stream reconnects with Last-Event-ID and gets each missed event once.

Level today: mock-tested (the real app factory, middleware and a temp SQLite copy; a session-store double; events are
seeded by the test, not by the real writers). Blocked by AEA-57 (journey harness), AEA-51 (integrated turn) and AEA-52
(the real takeover writers).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import anyio
import pytest

from meridian.adapters.sqlite.rows import StreamKey
from meridian.web.deps import UOW_FACTORY
from tests.api.events_support import (
    TAKEOVER_TRIO,
    append_stored,
    close_stream,
    frame_ids,
    full_stream_app,
    open_stream,
    payload,
    read_frames,
    running,
    seed_conversation,
    session_of,
)
from tests.api.web_shell_support import FakeSessionStore, captured_log, records_of

pytestmark = pytest.mark.journey


def test_j9_reconnect_replays_each_missed_event_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """journey (AC-16): one frame, a drop, a reconnect with that id, then a live event: every stored id exactly once."""
    sessions = FakeSessionStore()
    token = sessions.issue()
    app = full_stream_app(monkeypatch, tmp_path, store=sessions)
    seen: list[str] = []
    out: dict[str, Any] = {}

    async def scenario() -> None:
        async with running(app) as tg:
            uow = app.state.container.get(UOW_FACTORY)
            tid = seed_conversation(uow, session_of(sessions, token))
            append_stored(uow, tid, [(k, payload(k)) for k in TAKEOVER_TRIO])
            with captured_log() as log:
                first = await open_stream(tg, app, tid, token=token)
                [one] = await read_frames(first, 1)
                await close_stream(first)
                second = await open_stream(tg, app, tid, token=token, last_event_id=str(one.id))
                rest = await read_frames(second, 2)
                append_stored(uow, tid, [("ai_resumed", payload("ai_resumed"))])
                live = await read_frames(second, 1)
                await close_stream(second)
            with uow() as tx:
                stored = tx.core.events.after(StreamKey(tid), 0)
            frames = [one, *rest, *live]
            seen.extend(f.data for f in frames)
            out.update(ids=frame_ids(frames), stored=[r.id for r in stored], log=log.getvalue())

    anyio.run(scenario)
    assert out["ids"] == out["stored"] and len(out["stored"]) == 4
    assert out["ids"] == sorted(out["ids"])
    reconnects = records_of(io.StringIO(str(out["log"])), "stream_reconnect")
    assert len(reconnects) == 1 and reconnects[0]["replayed"] == 2
    assert any("Riley (demo representative) has joined." in d for d in seen)
