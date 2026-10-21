"""AEA-42 J-7 step: "Talk to a person" opens one case, a second press answers already_open with the same card.

Level: `mock-tested` (real app, middleware and hunk over a temp SQLite copy; doubles for HandoffService, ReplyComposer,
CaseService and DemoService; no server, no model, no browser).
Blocked by: AEA-57 (journey harness), AEA-52 (integrated J-7) and AEA-40 (the reload step reads `getChatThread`).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

import pytest

from tests.api.handoff_support import HANDOFF_PATH, customer_token, handoff_app, thread_for
from tests.api.web_shell_support import cookie_header, make_client
from tests.fixtures.sqlite import temp_sqlite

pytestmark = pytest.mark.journey


def test_j7_person_request_once_then_already_open(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """While staffed: press 1 is live_queued; press 2 (new turn id) is already_open with the same card; the stored
    state is one case, a handed_off conversation and the press-1 turn row holding press 1's card."""
    with temp_sqlite() as db:
        h = handoff_app(monkeypatch, tmp_path, db, presence="simulated_on_shift")
        token = customer_token(h)
        thread = str(thread_for(h, token))
        with make_client(h.app) as client:
            url = HANDOFF_PATH.format(thread_id=thread)
            first_turn = str(uuid.uuid4())
            one = client.post(url, json={"turn_id": first_turn}, headers=cookie_header(token))
            two = client.post(url, json={"turn_id": str(uuid.uuid4())}, headers=cookie_header(token))
        assert one.status_code == 200 and one.json()["result"] == "live_queued"
        assert one.json()["block"]["type"] == "live_queued"
        assert two.json()["result"] == "already_open"
        assert two.json()["block"] == one.json()["block"]
        conn = sqlite3.connect(db.db_path)
        try:
            cases = conn.execute("SELECT COUNT(*) FROM cases WHERE thread_id = ?", (thread,)).fetchone()[0]
            outcome = conn.execute(
                "SELECT outcome FROM conversations WHERE thread_id = ?", (thread,)
            ).fetchone()[0]
            stored = conn.execute("SELECT response FROM turns WHERE turn_id = ?", (first_turn,)).fetchone()[0]
        finally:
            conn.close()
        assert cases == 1
        assert outcome == "handed_off"
        assert json.loads(stored)["block"] == one.json()["block"]


@pytest.mark.skip(reason="blocked: getChatThread is AEA-40; integrated harness AEA-57")
def test_j7_reload_shows_card() -> None:
    """After a reload the card is in `getChatThread` (customer audit A-2, B-1): load the thread through
    SessionService.thread() and assert the stored `block` of the CON-4 turn appears in the history. Needs AEA-40."""
