"""SpecialistRunner cases split from test_runner.py (AEA-35 AC-17, AC-20). Synthetic values only."""

from __future__ import annotations

import logging

import pytest
from pydantic import JsonValue

from meridian.domain.specialists import (
    KnowledgeResult,
)
from meridian.domain.turn import TaskIntent
from tests.fakes import FakeToolModel, InMemoryTraceSink
from tests.unit.agent.specialists._doubles import (
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

_WP1_ALL = [WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM]


def _kb_task(text: str = "What does the Comfort Club membership actually include?", **kw):
    return make_task("knowledge", TaskIntent.ANSWER_QUESTION, text, **kw)


def test_wp1_knowledge_run_cites_current_file() -> None:
    sink = InMemoryTraceSink()
    points: list[JsonValue] = [{"text": p.text, "passage_id": str(p.passage_id)} for p in _WP1_ALL]
    points.append(
        {"text": "$149 a year, 10% off repairs", "passage_id": "archive/comfort_club_overview.md#0"}
    )
    # the 4-point report: three valid, one citing a passage no search returned
    model = FakeToolModel(
        [
            step(tool_call("c1", "kb_search", query="comfort club")),
            step(report_call("r1", points=points, answered=True)),
        ]
    )
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: kb_dispatched(c, ctx, _WP1_ALL))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert isinstance(result, KnowledgeResult)
    assert result.status == "answered"
    assert len(result.points) == 3
    returned = {p.passage_id for p in _WP1_ALL}
    for p in result.points:
        assert p.passage_id in returned
        assert p.passage_id.startswith("membership/comfort_club_overview.md#")
    joined = " ".join(p.text for p in result.points)
    for banned in ("$149", "$12.99", "$219", "10% off"):
        assert banned not in joined


def test_unexpected_error_returns_failed_result(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    sink = InMemoryTraceSink()
    model = FakeToolModel([step(tool_call("c1", "kb_search", query="a"))])

    class _Boom(ScriptedDispatcher):
        def dispatch(self, calls, *, kinds, scope):
            raise RuntimeError("boom with secret text")

    with turn_ctx(sink) as ctx:
        dispatcher = _Boom(lambda c: kb_dispatched(c, ctx, []))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert result.status == "failed"
    assert result.failure is None
    records = [r for r in caplog.records if r.name == "meridian.agent.specialists.runner"]
    assert len(records) == 1
    assert "RuntimeError" in records[0].getMessage()
    assert "boom" not in records[0].getMessage()
