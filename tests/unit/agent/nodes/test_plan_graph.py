"""AEA-37 AC-11 part (a): the real graph and composer with the three real plan nodes (mock level, no server).

Every other node is an AEA-21 double. The planner and classifier talk to a real ModelGateway whose model port is a
recording fake, so the two routing calls and nothing else can be counted.
"""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from meridian.agent.graph import build_graph, run_graph
from meridian.agent.nodes import plan as plan_nodes
from meridian.agent.nodes.compose import ReplyComposer
from meridian.domain.blocks import EmergencyLineBlock, LocatePromptBlock
from meridian.domain.turn import GraphOutcome, TaskIntent
from meridian.ports.models import ChoiceAnswer
from tests.fakes import FakeChoiceModel
from tests.graph._spine_doubles import install_doubles, make_ctx, make_input
from tests.unit.agent._gateway_doubles import Doubles, build_gateway
from tests.unit.agent.nodes.plan_fixtures import DANGER, NODANGER, TURN_1, choices, make_deps


def _run(
    monkeypatch: pytest.MonkeyPatch, text: str, label: str
) -> tuple[GraphOutcome, list[str], FakeChoiceModel, FakeChoiceModel, Doubles]:
    visits: list[str] = []
    real = {
        "planner": plan_nodes.planner,
        "danger_classifier": plan_nodes.danger_classifier,
        "plan_join": plan_nodes.plan_join,
    }
    install_doubles(monkeypatch, visits, **real)
    planner_fake = FakeChoiceModel(
        [ChoiceAnswer(choices=choices(scheduling="book_new", topic="booking"), probabilities=None)]
    )
    classifier_fake = FakeChoiceModel([ChoiceAnswer(choices={"danger_level": label}, probabilities=None)])
    gw, d = build_gateway(planner=planner_fake, classifier=classifier_fake)
    deps = make_deps(gw)
    composer = ReplyComposer()
    graph = build_graph(deps, checkpointer=InMemorySaver(), composer=composer)
    outcome = run_graph(graph, make_input(TURN_1, text), make_ctx(TURN_1), deps=deps, composer=composer)
    return outcome, visits, planner_fake, classifier_fake, d


def test_danger_reaches_safety_by_classifier_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, visits, planner_fake, classifier_fake, d = _run(monkeypatch, DANGER, "danger")
    assert isinstance(outcome.reply.blocks[0], EmergencyLineBlock)
    assert outcome.reply.path == "danger"
    assert outcome.reply.outcome == "safety_reply"
    assert outcome.turn_trace.gate_result == "danger"
    assert outcome.turn_trace.danger_raised is True
    events = [e for e in outcome.check_events if e.check == "classifier"]
    assert len(events) == 1
    assert events[0].result == "raised"
    assert events[0].codes == ("danger",)
    assert "safety" in visits
    for skipped in ("identity", "run_specialist", "responder", "brief", "handoff"):
        assert skipped not in visits
    assert len(planner_fake.requests) == 1
    assert len(classifier_fake.requests) == 1
    assert d.fallback.requests == []
    assert d.responder.requests == []
    assert d.specialist.requests == []


def test_nodanger_routes_to_booking(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, visits, _planner_fake, _classifier_fake, _d = _run(monkeypatch, NODANGER, "normal")
    locate = [b for b in outcome.reply.blocks if isinstance(b, LocatePromptBlock)]
    assert len(locate) == 1
    assert not any(isinstance(b, EmergencyLineBlock) for b in outcome.reply.blocks)
    assert outcome.reply.outcome != "safety_reply"
    assert outcome.turn_trace.gate_result == "clear"
    assert outcome.turn_trace.danger_raised is False
    assert outcome.turn_trace.planner is not None
    assert outcome.turn_trace.planner.intents == (TaskIntent.BOOK_NEW,)
    assert outcome.turn_trace.planner.plan_source == "planner"
    events = [e for e in outcome.check_events if e.check == "classifier"]
    assert len(events) == 1
    assert events[0].result == "pass"
    assert "identity" in visits
    assert "safety" not in visits
    assert "handoff" not in visits
