"""J-7 (proposed in slice plan section 0a): during a takeover the customer's stream shows the staff events in order.

Level today: mock-tested (real app factory, middleware and temp SQLite; the takeover rows are seeded by the test, standing
in for AEA-46's writers). Blocked by AEA-57 (journey harness), AEA-51 (integrated turn) and AEA-52 (real takeover writers).
"""

from __future__ import annotations

import json
from pathlib import Path

import anyio
import pytest

from meridian.web.deps import UOW_FACTORY
from tests.api.events_support import (
    STAFF_TEXT,
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
    table_counts,
)
from tests.api.web_shell_support import FakeSessionStore

pytestmark = pytest.mark.journey


def test_j7_takeover_events_reach_customer_stream_in_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """journey (AC-16): joined, paused, message, resumed arrive in order; the read changes no stored row."""
    sessions = FakeSessionStore()
    token = sessions.issue()
    app = full_stream_app(monkeypatch, tmp_path, store=sessions)
    out: dict[str, object] = {}

    async def scenario() -> None:
        async with running(app) as tg:
            uow = app.state.container.get(UOW_FACTORY)
            tid = seed_conversation(uow, session_of(sessions, token))
            items = [(k, payload(k)) for k in (*TAKEOVER_TRIO, "ai_resumed")]
            append_stored(uow, tid, items)
            db_path = app.state.container.settings.data_dir / "meridian.sqlite"
            assert db_path.exists()
            before = table_counts(db_path)
            h = await open_stream(tg, app, tid, token=token)
            out["frames"] = await read_frames(h, 4)
            await close_stream(h)
            out["unchanged"] = before == table_counts(db_path)

    anyio.run(scenario)
    frames = out["frames"]
    assert [f.event for f in frames] == ["representative_joined", "ai_paused", "staff_message", "ai_resumed"]  # type: ignore[attr-defined]
    data = [json.loads(f.data) for f in frames]  # type: ignore[attr-defined]
    assert data[0]["speaker"]["display_name"] == "Riley" and data[2]["speaker"]["display_name"] == "Riley"
    assert data[2]["text"] == STAFF_TEXT
    assert out["unchanged"]
