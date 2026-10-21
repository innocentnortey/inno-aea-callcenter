"""Turn 1, 2 and 5 of WP-1 keep the stable specialist prefix (AEA-35 AC-12; context-management rule 3)."""

from __future__ import annotations

import hashlib

from meridian.agent.prompts.specialists import (
    RULE_NEVER_TALK,
    RULE_NO_CARDS,
    RULE_NO_FIRM_PRICES,
    RULE_REPORT_ONLY,
)
from meridian.domain.turn import TaskIntent
from meridian.ports.models import ToolCall
from tests.fakes import FakeToolModel, InMemoryTraceSink
from tests.unit.agent.specialists._doubles import (
    TURN_1,
    TURN_2,
    TURN_5,
    WP1_INCLUDES,
    WP1_MINIMUM,
    WP1_PRICE,
    ScriptedDispatcher,
    ScriptedGateway,
    kb_dispatched,
    make_runner,
    make_task,
    report_call,
    scope,
    step,
    tool_call,
    turn_ctx,
)


def test_stable_prefix_turns_1_2_5() -> None:
    first = "What does the Comfort Club membership actually include?"
    turns = [
        (TURN_1, first, ()),
        (TURN_2, "And how much is it?", (first,)),
        (TURN_5, "Does it cover plumbing?", (first, "And how much is it?")),
    ]
    script = []
    for i in range(3):
        script += [
            step(tool_call(f"c{i}", "kb_search", query="comfort club")),
            step(report_call(f"r{i}", points=[], answered=False)),
        ]
    model = FakeToolModel(script)
    sink = InMemoryTraceSink()
    runner_holder: list[object] = []
    for turn_id, text, history in turns:
        with turn_ctx(sink, turn_id=turn_id) as ctx:

            def handler(call: ToolCall, ctx=ctx):
                return kb_dispatched(call, ctx, [WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM])

            runner = make_runner(ScriptedGateway(model), model, ScriptedDispatcher(handler), sink)
            runner_holder.append(runner)
            task = make_task("knowledge", TaskIntent.ANSWER_QUESTION, text, messages=history)
            runner.run(task, scope(ctx), ctx)
    reqs = [model.requests[0], model.requests[2], model.requests[4]]
    hashes = {hashlib.sha256(r.system_prefix.encode()).hexdigest() for r in reqs}
    assert len(hashes) == 1
    for r in reqs:
        assert "You are the knowledge specialist" in r.system_prefix
        for rule in (RULE_NEVER_TALK, RULE_REPORT_ONLY, RULE_NO_FIRM_PRICES, RULE_NO_CARDS):
            assert rule in r.system_prefix
    assert len({tuple(t.name for t in r.tools) for r in reqs}) == 1
    contents = [str(r.messages.items[0]["content"]) for r in reqs]  # type: ignore[index,call-overload]
    assert len(set(contents)) == 3
    for content, (_, text, _) in zip(contents, turns, strict=True):
        assert text in content
