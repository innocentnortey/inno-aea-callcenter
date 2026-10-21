"""AEA-38: the full responder prompt is rebuilt every turn (AC-9; context-management-multi-turn rule 3)."""

from __future__ import annotations

import hashlib

from meridian.agent.nodes import reply
from meridian.agent.prompts.reply import RESPONDER_RULES, RESPONDER_SYSTEM_PREFIX
from meridian.domain.common import TurnId
from meridian.domain.state import ChatLine
from meridian.domain.turn import ResponderDraft
from tests.fakes import FakeStructuredModel
from tests.unit.agent.nodes.reply_fixtures import (
    MOVED_T3,
    NOW,
    TURN_1,
    TURN_2,
    TURN_3,
    TURN_4,
    TURN_5,
    deps,
    facts,
    gateway,
    no_uow,
    run,
    settled,
    state,
    turn_ctx,
    turn_input,
)

SENTINEL = "SENTINEL line only turn two has"


def _window(n: int, turns: list[TurnId], *, sentinel: bool = False) -> list[ChatLine]:
    lines = []
    for i in range(n):
        text = f"line {i}"
        if sentinel and i == 1:
            text = SENTINEL
        lines.append(
            ChatLine(
                speaker="customer" if i % 2 == 0 else "assistant",
                text=text,
                turn_id=turns[i % len(turns)],
                at=NOW,
            )
        )
    return lines


def test_stable_prefix_turns_1_2_5() -> None:
    model = FakeStructuredModel(
        [ResponderDraft(text="ok one."), ResponderDraft(text="ok two."), ResponderDraft(text="ok five.")]
    )
    gw, _ = gateway(responder=model)
    d = deps(uow=no_uow, gw=gw)
    cases = [
        (TURN_1, "I need to schedule a service call. My AC isn't cooling.", _window(1, [TURN_1]), settled()),
        (
            TURN_2,
            "This Saturday if possible, 4 to 7, after work.",
            _window(3, [TURN_1, TURN_2], sentinel=True),
            settled(),
        ),
        (TURN_5, "Yes, please.", _window(9, [TURN_3, TURN_4, TURN_5]), settled(MOVED_T3)),
    ]
    windows = []
    for turn, text, window, done in cases:
        st = state(
            turn_input=turn_input(turn=turn, text=text),
            chat_window=window,
            facts=facts(turn_id=turn),
            settled=done,
        )
        reply.responder(st, run(turn_ctx(turn=turn)), deps=d)
        windows.append(window)
    assert len(model.requests) == 3
    digest = hashlib.sha256(RESPONDER_SYSTEM_PREFIX.encode()).hexdigest()
    for req, window in zip(model.requests, windows, strict=True):
        assert hashlib.sha256(req.system_prefix.encode()).hexdigest() == digest
        assert "automated assistant, not a person" in req.system_prefix
        assert all(line in req.system_prefix for line in RESPONDER_RULES)
        assert "ALREADY DONE IN THIS CONVERSATION:" in req.system_dynamic
        assert "WHAT HAPPENED THIS TURN:" in req.system_dynamic
        chat = req.user.split("LATEST CUSTOMER MESSAGE:")[0].splitlines()[1:]
        assert [x for x in chat if x] == [f"{ln.speaker}: {ln.text}" for ln in window]
        assert len({ln.turn_id for ln in window}) <= 10
        assert all(len(ln.text) <= 600 for ln in window)
        assert sum(len(ln.text) for ln in window) <= 8000
    assert (
        "- moved: Monday, October 19, 8:00 am to 12:00 pm, with Marta Kowalski, hvac_repair (earlier turn)"
        in model.requests[2].system_dynamic
    )
    assert SENTINEL in model.requests[1].user and SENTINEL not in model.requests[2].user
