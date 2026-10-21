"""AEA-10 PA-2 to PA-4: conversation writes, the message window and check events."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import timedelta

import pytest

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.rows import ConversationRow
from meridian.domain.state import Controller
from meridian.domain.turn import CheckEvent
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.adapters.sqlite.helpers import (
    NOW,
    case_ref,
    conversation,
    new_thread,
    new_turn,
    turn_ids,
)


def _conv(row: object) -> ConversationRow:
    assert isinstance(row, ConversationRow)
    return row


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def test_conversation_writes(store: TempStore) -> None:
    a, b, closed, eval_thread, seed_thread = (new_thread() for _ in range(5))
    wall = NOW
    with store.uow(write=True) as tx:
        c = tx.core.conversations
        c.insert(conversation(a, started_wall_at=wall, last_customer_wall_at=wall - timedelta(minutes=30)))
        c.insert(
            conversation(
                b,
                started_wall_at=wall + timedelta(minutes=1),
                last_customer_wall_at=wall - timedelta(minutes=29),
            )
        )
        c.insert(conversation(closed, live_state="closed"))
        c.insert(conversation(eval_thread, run_tag="eval", last_customer_wall_at=wall - timedelta(hours=2)))
        c.insert(conversation(seed_thread, run_tag="seed", last_customer_wall_at=wall - timedelta(hours=2)))
        assert set(c.open_thread_ids()) == {a, b, eval_thread, seed_thread}
        cutoff = wall - timedelta(minutes=29, seconds=30)
        assert [t for t, _ in c.idle_live(cutoff)] == [a]
        assert [t for t, _ in c.idle_live(wall - timedelta(minutes=29))] == [a, b]
        assert c.last_started_wall() == wall + timedelta(minutes=1)

        c.set_last_customer_wall_at(a, wall)
        c.set_outcome(a, "handed_off", ended_wall_at=wall)
        c.set_controller(
            b,
            Controller(kind="human", representative_name="Riley", case_ref=case_ref(9)),
            live_state="joined",
            live_since=wall,
        )
        c.set_live_state(closed, "queued", wall)
        row_a, row_b, row_c = (_conv(c.lookup(str(t))) for t in (a, b, closed))
        assert (row_a.outcome, row_a.ended_wall_at, row_a.last_customer_wall_at) == ("handed_off", wall, wall)
        assert row_b.controller == Controller(kind="human", representative_name="Riley", case_ref=case_ref(9))
        assert (row_b.live_state, row_b.live_since) == ("joined", wall)
        assert row_c.live_state == "queued"
        assert [t for t, _ in c.idle_live(cutoff)] == []
        calls: list[Callable[[], None]] = [
            lambda: c.set_outcome(new_thread(), "abandoned"),
            lambda: c.set_live_state(new_thread(), "closed", None),
            lambda: c.set_last_customer_wall_at(new_thread(), wall),
        ]
        for call in calls:
            with pytest.raises(StorageError):
                call()


def test_messages_recent_window(store: TempStore) -> None:
    thread = new_thread()
    turns = [new_turn() for _ in range(12)]
    with store.uow(write=True) as tx:
        m = tx.core.messages
        greeting = m.append(thread, "assistant", "hello", NOW)
        ids: dict[int, int] = {}
        rep = 0
        for n, turn in enumerate(turns, start=1):
            ids[n] = m.append(thread, "customer", f"q{n}", NOW, turn_id=turn)
            m.append(thread, "assistant", f"a{n}", NOW, turn_id=turn)
            if n == 6:
                rep = m.append(thread, "representative", "hi from a person", NOW)
        recent = m.recent(thread, 10)
        assert recent[0].id == ids[3]
        assert rep in {r.id for r in recent}
        assert greeting not in {r.id for r in recent}
        everything = m.recent(thread, 20)
        assert everything[0].id == greeting
        assert len(everything) == 1 + 24 + 1
        assert len(m.all_for_thread(thread)) == 26
        with pytest.raises(ValueError):
            m.recent(thread, 0)


def test_check_events_append_round_trip(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    event = CheckEvent.model_validate(
        {
            "check": "fact",
            "turn_id": str(turn),
            "result": "trimmed",
            "removed": 2,
            "claim_kinds": ["date", "amount"],
            "codes": ["c1"],
        }
    )
    with store.uow(write=True) as tx:
        tx.core.turns.begin(turn_ids(thread, turn), NOW)
        tx.core.check_events.append(event, thread)
        explicit = NOW + timedelta(minutes=9)
        tx.core.check_events.append(event, thread, at=explicit)
        assert tx.core.check_events.for_thread(thread) == (event, event)
        ats = [r[0] for r in tx.connection.execute("SELECT at FROM check_events ORDER BY id")]
        assert ats[0] == "2026-10-16T15:05:00+00:00"
        assert ats[1] == "2026-10-16T15:14:00+00:00"
