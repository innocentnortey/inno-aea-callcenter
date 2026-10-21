"""J-3 (slice plan section 0a), AEA-51 steps: booking, a fee-free move, and a follow-up that remembers both. Real app,
real graph and DB copy, scripted model at the provider boundary."""

from __future__ import annotations

import pytest

from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import Chat, blocks
from tests.integration.customer_support import RunOptions, open_customer_run

pytestmark = pytest.mark.journey

J3 = "J-3"
CHAT = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
BOOKING = (*CHAT, "turn_service", "run_graph", "identity_service", "handoff_service")
OPS = ("login", "startChatSession", "submitTurn", "getChatThread")


def test_j3_booking_and_follow_up(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        with run.step(J3, "1 book slot 56", needs=BOOKING, operations=OPS):
            booked = sc.wp3(run, client)
            confirmation = blocks(booked.responses[-1], "confirmation")[0]
            assert confirmation["window_label"].startswith("8:00 am")
            appointment = run.db.one(
                "SELECT * FROM appointments WHERE appointment_id = ?", (confirmation["appointment_id"],)
            )
            assert (appointment["slot_id"], appointment["status"]) == (56, "scheduled")
            assert run.db.count("actions", "thread_id = ? AND kind = 'booked'", (booked.thread_id,)) == 1
            assert run.db.one("SELECT status FROM appointment_slots WHERE slot_id = 56")["status"] != "open"
            print(f"step 1: appointment={confirmation['appointment_id']} slot=56")
        chat, _responses, card, target, row = sc.wp4f_prepare(run, client)
        app_id = int(row["appointment_id"])
        with run.step(J3, "2 move to a shown window", needs=BOOKING, operations=OPS):
            moved = sc.wp4f_pick(run, chat, card, target, app_id)
            assert blocks(moved, "confirmation")[0]["timeline"][0] == "Moved"
            assert (
                run.db.one("SELECT slot_id FROM appointments WHERE appointment_id = ?", (app_id,))["slot_id"]
                == target
            )
            assert run.db.count("actions", "thread_id = ? AND kind = 'moved'", (chat.thread_id,)) == 1
            print(f"step 2: appointment={app_id} new_slot={target}")
        with run.step(J3, "3 the follow-up remembers the move", needs=BOOKING, operations=OPS):
            follow = sc.wp4f_followup(run, chat, str(row["service_type"]), app_id)
            text = " ".join(str(b.get("text", "")) for b in blocks(follow))
            assert sc.MOVED_SENTENCE in text
            kinds = [a["kind"] for a in follow.json()["settled"]["actions"]]
            assert kinds.count("moved") == run.db.count(
                "actions", "thread_id = ? AND kind = 'moved'", (chat.thread_id,)
            )
            print(f"step 3: kept={sc.MOVED_SENTENCE!r} settled_actions={kinds}")
        with run.step(J3, "4 a refresh shows the move", needs=BOOKING, operations=OPS):
            reread = Chat(run=run, client=client, thread_id=chat.thread_id, opened={})
            thread = reread.client.call(
                "GET", f"/api/chat/sessions/{reread.thread_id}", operation_id="getChatThread"
            )
            assert thread.status_code == 200
            assert "confirmation" in thread.text and "moved" in thread.text.lower()
            print("step 4: the stored thread still shows the confirmation")
