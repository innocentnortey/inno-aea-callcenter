"""Turn-2+ full prompt through the real gateway (AEA-37 AC-9; context-management rules 3, 4, 5)."""

from __future__ import annotations

import hashlib
import json

from meridian.agent.nodes.plan import planner
from meridian.agent.prompts.routing import PLANNER_FIELDS, PLANNER_SYSTEM
from meridian.ports.models import ChoiceAnswer
from tests.fakes import FakeChoiceModel
from tests.graph._spine_doubles import make_ctx
from tests.unit.agent._gateway_doubles import build_gateway
from tests.unit.agent.nodes.plan_fixtures import (
    JEV_MODEL,
    TURN_1,
    TURN_2,
    TURN_3,
    TURN_4,
    TURN_5,
    choices,
    line,
    make_deps,
    make_state,
    runtime,
    seeded_phone,
)


def _hash(fields: object) -> str:
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


def test_stable_prefix_turns_1_2_5() -> None:
    answer = ChoiceAnswer(choices=choices(scheduling="book_new", topic="booking"), probabilities=None)
    fake = FakeChoiceModel([answer, answer, answer], model=JEV_MODEL)
    gw, _doubles = build_gateway(planner=fake)
    deps = make_deps(gw)

    t1 = f"I need to schedule a service call. My AC isn't cooling. Call me on {seeded_phone()}."
    c1 = line("customer", t1, TURN_1)
    a1 = line("assistant", "Happy to help. What day works for you?", TURN_1)
    t2 = "This Saturday if possible, 4 to 7, after work."
    c2 = line("customer", t2, TURN_2)
    a2 = line("assistant", "I have Saturday 4 to 7 open.", TURN_2)
    c3 = line("customer", "Great, book it.", TURN_3)
    a3 = line("assistant", "x" * 700, TURN_3)
    c4 = line("customer", "Is the technician bringing parts?", TURN_4)
    a4 = line("assistant", "Usually, yes.", TURN_4)
    t5 = f"Yes, still {seeded_phone()}."
    c5 = line("customer", t5, TURN_5)

    planner(make_state(t1, turn_id=TURN_1, chat=[c1]), runtime(make_ctx(TURN_1)), deps=deps)
    planner(make_state(t2, turn_id=TURN_2, chat=[c1, a1, c2]), runtime(make_ctx(TURN_2)), deps=deps)
    planner(
        make_state(t5, turn_id=TURN_5, chat=[c1, a1, c2, a2, c3, a3, c4, a4, c5]),
        runtime(make_ctx(TURN_5)),
        deps=deps,
    )

    assert len(fake.requests) == 3
    r1, r2, r5 = fake.requests
    assert r1.state["recent_chat"] == []
    assert r2.state["recent_chat"] == [
        "customer: I need to schedule a service call. My AC isn't cooling. Call me on [phone].",
        "assistant: Happy to help. What day works for you?",
    ]
    chat5 = r5.state["recent_chat"]
    assert isinstance(chat5, list)
    assert len(chat5) == 6
    assert chat5[0] == f"customer: {t2}"
    assert chat5[-1] == "assistant: Usually, yes."
    assert not any("schedule a service call" in str(x) for x in chat5)
    capped = chat5[3]
    assert isinstance(capped, str)
    assert len(capped) == 400
    assert capped.endswith("…")

    assert r1.system == r2.system == r5.system == PLANNER_SYSTEM
    field_hashes = [_hash([f.model_dump() for f in r.fields]) for r in (r1, r2, r5)]
    assert len(set(field_hashes)) == 1
    assert field_hashes[0] == _hash([f.model_dump() for f in PLANNER_FIELDS])
    for r in (r1, r2, r5):
        window = r.state["recent_chat"]
        assert isinstance(window, list)
        assert len(window) <= 6
        assert all(len(str(entry)) <= 400 for entry in window)
    for r in (r1, r5):
        assert "[phone]" in str(r.state["latest_message"])
        assert seeded_phone() not in str(r.state["latest_message"])
    assert "[phone]" in str(r2.state["recent_chat"][0])
    print("prompt hashes:", field_hashes)
