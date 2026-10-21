"""AEA-02 AC-8: ConversationState reducers and defaults."""

from __future__ import annotations

import datetime as dt
import operator

from meridian.domain.common import Halt, HaltReason, ThreadId, TurnId
from meridian.domain.state import ConversationState, add_turn_events, first_halt
from meridian.domain.turn import CheckEvent, TurnInput

THREAD = ThreadId("3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10")
TURN_A = TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")
TURN_B = TurnId("a2b4c6d8-1e3f-4a5b-8c7d-9e0f1a2b3c4d")


def _event(turn: TurnId, code: str) -> CheckEvent:
    return CheckEvent(check="gate", turn_id=turn, result="fired", codes=(code,))


def _halt(reason: HaltReason) -> Halt:
    return Halt(reason=reason, node="n", elapsed_ms=1)


def test_reducers() -> None:
    assert operator.add([1], [2]) == [1, 2]  # the reducer specialist_results uses
    h1, h2 = _halt(HaltReason.BRAKE_TASKS), _halt(HaltReason.DEADLINE)
    assert first_halt(None, h1) is h1
    assert first_halt(h1, h2) is h1
    assert first_halt(None, None) is None

    old = (_event(TURN_A, "a1"),)
    assert add_turn_events(old, ()) is old
    # a new turn's first event drops the previous turn's events
    assert add_turn_events(old, (_event(TURN_B, "b1"),)) == (_event(TURN_B, "b1"),)
    # two writers in one turn keep both, in order
    first = add_turn_events((), (_event(TURN_B, "b1"),))
    both = add_turn_events(first, (_event(TURN_B, "b2"),))
    assert [e.codes for e in both] == [("b1",), ("b2",)]


def test_conversation_state_defaults() -> None:
    turn_input = TurnInput(
        turn_id=TURN_A,
        message_id=1,
        kind="text",
        text_store="hello",
        received_at=dt.datetime(2026, 10, 16, 10, 0, tzinfo=dt.UTC),
    )
    state = ConversationState(thread_id=THREAD, turn_input=turn_input)
    assert state.controller.kind == "ai"
    assert state.identity.status == "not_checked"
    assert state.identity.tries_left == 3
    assert state.open_tasks == []
    assert state.shown_slots == []
    assert state.specialist_results == []
    assert state.halt is None
    assert state.check_events == ()
    assert state.settled is None
