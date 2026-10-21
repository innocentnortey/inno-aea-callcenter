"""The three plan nodes called directly with a scripted gateway (AEA-37 AC-1 to AC-4, AC-6, AC-7, AC-10)."""

from __future__ import annotations

import logging
from typing import Any

import pytest

from meridian.agent.nodes.plan import (
    danger_classifier,
    plan_join,
    planner,
    raise_only,
    rules_verdict,
)
from meridian.domain.common import (
    Halt,
    HaltReason,
    ProviderFailureKind,
    SafetyKind,
)
from meridian.domain.state import DangerUpdate, PlanJoinUpdate, PlannerUpdate
from meridian.domain.turn import (
    DangerAssessment,
    Plan,
    PlannedTask,
    PlannerTrace,
    TaskIntent,
)
from meridian.policy.limits import Brakes, Limits
from meridian.ports.models import Role
from tests.graph._spine_doubles import make_ctx, no_rules
from tests.unit.agent.nodes.plan_fixtures import (
    DANGER,
    JEV_MODEL,
    NODANGER,
    SONNET_MODEL,
    TURN_1,
    WP3,
    WP4F,
    ScriptedGateway,
    choices,
    failed,
    free_text_gate,
    halted,
    make_deps,
    make_state,
    merged,
    ok,
    open_task,
    rules,
    runtime,
)

WP3_PICKS = choices(scheduling="book_new", topic="booking")
LABELS = ("normal", "burning_unclear", "danger")
_RANK = {"normal": 0, "burning_unclear": 1, "danger": 2}


def signals(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [r.signal for r in caplog.records if r.name == "meridian.signal"]  # type: ignore[attr-defined]


def run_planner(gw: ScriptedGateway, text: str = WP3, **state_kw: Any) -> PlannerUpdate:
    return planner(make_state(text, **state_kw), runtime(make_ctx(TURN_1)), deps=make_deps(gw))


def run_classifier(gw: ScriptedGateway, text: str = NODANGER, **state_kw: Any) -> DangerUpdate:
    return danger_classifier(make_state(text, **state_kw), runtime(make_ctx(TURN_1)), deps=make_deps(gw))


def run_join(
    state: Any, gw: ScriptedGateway | None = None, *, limits: Limits | None = None
) -> PlanJoinUpdate:
    return plan_join(
        state, runtime(make_ctx(TURN_1)), deps=make_deps(gw or ScriptedGateway({}), limits=limits)
    )


# --- AC-1 ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "verdict", "expected"),
    [
        ("normal", "normal", False),
        ("normal", "burning_unclear", False),
        ("normal", "danger", False),
        ("burning_unclear", "normal", True),
        ("burning_unclear", "burning_unclear", False),
        ("burning_unclear", "danger", False),
        ("danger", "normal", True),
        ("danger", "burning_unclear", True),
        ("danger", "danger", False),
    ],
)
def test_classifier_raise_only(label: Any, verdict: Any, expected: bool) -> None:
    assert raise_only(label, verdict) is expected
    assert expected is (_RANK[label] > _RANK[verdict])


def test_classifier_raise_only_rules_verdict_and_node_rows() -> None:
    assert rules_verdict(no_rules()) == "normal"
    assert rules_verdict(rules(burning_unclear=True)) == "burning_unclear"
    assert rules_verdict(rules(danger_words=True)) == "danger"
    assert rules_verdict(rules(safety=SafetyKind.CO)) == "danger"

    danger = run_classifier(
        ScriptedGateway({Role.CLASSIFIER: [ok(Role.CLASSIFIER, {"danger_level": "danger"})]}), DANGER
    )
    assert danger["danger"].raised is True
    assert danger["danger"].label == "danger"
    assert danger["check_events"][0].result == "raised"
    assert danger["check_events"][0].codes == ("danger",)

    calm = run_classifier(
        ScriptedGateway({Role.CLASSIFIER: [ok(Role.CLASSIFIER, {"danger_level": "normal"})]})
    )
    assert calm["danger"].raised is False
    assert calm["check_events"][0].result == "pass"
    assert calm["check_events"][0].codes == ("normal",)

    gate = free_text_gate(danger_words=True)
    lowered = run_classifier(
        ScriptedGateway({Role.CLASSIFIER: [ok(Role.CLASSIFIER, {"danger_level": "normal"})]}),
        DANGER,
        gate=gate,
    )
    assert lowered["danger"].label == "normal"
    assert lowered["danger"].raised is False


# --- AC-2 / PA-4 / PA-5 -------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", [ProviderFailureKind.BODY_ERROR, ProviderFailureKind.TIMEOUT])
def test_classifier_failure_rules_stand(kind: ProviderFailureKind, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    gw = ScriptedGateway(
        {Role.CLASSIFIER: [failed(Role.CLASSIFIER, kind)], Role.PLANNER: [ok(Role.PLANNER, WP3_PICKS)]}
    )
    update = run_classifier(gw)
    assert set(update) == {"danger", "check_events"}
    danger = update["danger"]
    assert danger.label == "normal"
    assert danger.raised is False
    assert danger.confidence is None
    assert danger.failure is not None
    assert danger.failure.kind is kind
    (event,) = update["check_events"]
    assert event.check == "classifier"
    assert event.result == "fallback"
    assert event.codes == ("fallback", kind.value)
    (sig,) = signals(caplog)
    assert sig["name"] == "classifier_fallback"
    assert sig["cause"] == kind.value
    assert sig["node"] == "danger_classifier"
    assert sig["role"] == "classifier"
    assert [r for r, _ in gw.calls] == [Role.CLASSIFIER]
    planned = run_planner(gw)
    state = merged(make_state(WP3), update, planned)
    assert "plan" in run_join(state)


def test_invalid_classifier_label_rules_stand() -> None:
    gw = ScriptedGateway({Role.CLASSIFIER: [ok(Role.CLASSIFIER, {"danger_level": "maybe"})]})
    update = run_classifier(gw)
    assert update["danger"].failure is not None
    assert update["danger"].failure.kind is ProviderFailureKind.INVALID_OUTPUT
    assert update["danger"].label == "normal"
    assert update["danger"].raised is False
    assert update["check_events"][0].result == "fallback"


def test_classifier_halt_writes_only_halt(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    gw = ScriptedGateway({Role.CLASSIFIER: [halted(Role.CLASSIFIER, HaltReason.DEADLINE)]})
    update = run_classifier(gw)
    assert update == {"halt": Halt(reason=HaltReason.DEADLINE, node="classifier", elapsed_ms=0)}
    assert signals(caplog) == []


# --- AC-3 / PA-4 --------------------------------------------------------------------------------------------


def test_planner_fallback_sdq6(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    gw = ScriptedGateway(
        {
            Role.PLANNER: [failed(Role.PLANNER, ProviderFailureKind.BODY_ERROR)],
            Role.PLANNER_FALLBACK: [ok(Role.PLANNER_FALLBACK, WP3_PICKS)],
        }
    )
    update = run_planner(gw)
    assert [r for r, _ in gw.calls] == [Role.PLANNER, Role.PLANNER_FALLBACK]
    assert gw.calls[0][1] == gw.calls[1][1]
    out = update["planner"]
    assert out.fallback_used is True
    assert out.model == SONNET_MODEL
    assert out.probabilities is None
    assert out.failure is None
    assert out.choices is not None
    assert out.choices.scheduling == "book_new"
    (sig,) = signals(caplog)
    assert sig["name"] == "planner_fallback"
    assert sig["cause"] == "body_error"
    assert sig["recovered"] is True
    assert sig["node"] == "planner"
    assert sig["role"] == "planner"


def test_planner_halt_never_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    gw = ScriptedGateway({Role.PLANNER: [halted(Role.PLANNER, HaltReason.PROVIDER_SPEND_CAP)]})
    update = run_planner(gw)
    assert [r for r, _ in gw.calls] == [Role.PLANNER]
    assert set(update) == {"halt"}
    assert update["halt"].reason is HaltReason.PROVIDER_SPEND_CAP
    assert signals(caplog) == []

    gw2 = ScriptedGateway(
        {
            Role.PLANNER: [failed(Role.PLANNER, ProviderFailureKind.BODY_ERROR)],
            Role.PLANNER_FALLBACK: [halted(Role.PLANNER_FALLBACK, HaltReason.DEADLINE)],
        }
    )
    update2 = run_planner(gw2)
    assert set(update2) == {"planner", "halt"}
    assert update2["planner"].choices is None
    assert update2["planner"].fallback_used is False
    assert update2["planner"].failure is not None
    assert update2["planner"].failure.kind is ProviderFailureKind.BODY_ERROR
    assert signals(caplog) == []


def test_invalid_planner_answer_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    picks = {k: v for k, v in WP3_PICKS.items() if k != "topic"}
    gw = ScriptedGateway(
        {
            Role.PLANNER: [ok(Role.PLANNER, picks)],
            Role.PLANNER_FALLBACK: [ok(Role.PLANNER_FALLBACK, WP3_PICKS)],
        }
    )
    update = run_planner(gw)
    assert [r for r, _ in gw.calls] == [Role.PLANNER, Role.PLANNER_FALLBACK]
    assert update["planner"].fallback_used is True
    (sig,) = signals(caplog)
    assert sig["cause"] == "invalid_output"


# --- AC-4 ---------------------------------------------------------------------------------------------------


def both_fail() -> ScriptedGateway:
    return ScriptedGateway(
        {
            Role.PLANNER: [failed(Role.PLANNER, ProviderFailureKind.BODY_ERROR)],
            Role.PLANNER_FALLBACK: [failed(Role.PLANNER_FALLBACK, ProviderFailureKind.SERVER)],
        }
    )


def test_both_planners_fail_planner_failed_plan(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    update = run_planner(both_fail(), "Can you help me?")
    out = update["planner"]
    assert out.choices is None
    assert out.failure is not None
    assert out.failure.kind is ProviderFailureKind.SERVER
    assert out.fallback_used is True
    (sig,) = signals(caplog)
    assert sig["recovered"] is False
    state = merged(make_state("Can you help me?"), update)
    assert run_join(state)["plan"] == Plan(
        mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True
    )


def test_both_planners_fail_open_task_continues() -> None:
    task = open_task("t-9", specialist="scheduling", intent=TaskIntent.RESCHEDULE)
    update = run_planner(both_fail(), WP4F, tasks=(task,))
    state = merged(make_state(WP4F, tasks=(task,)), update)
    plan = run_join(state)["plan"]
    assert plan.source == "open_task"
    assert plan.planner_failed is False
    assert plan.mode == "act"
    assert plan.tasks == (
        PlannedTask(
            order=1,
            specialist="scheduling",
            intent=TaskIntent.RESCHEDULE,
            needs_identity=True,
            resumes_task_id="t-9",
        ),
    )
    assert plan.topic == "booking"


# --- AC-6 / PA-5 / PA-6 -------------------------------------------------------------------------------------

THREE_TASKS = choices(account="invoice", scheduling="book_new", knowledge="yes")


def three_task_state(**kw: Any) -> Any:
    update = run_planner(ScriptedGateway({Role.PLANNER: [ok(Role.PLANNER, THREE_TASKS)]}))
    return merged(make_state(WP3, **kw), update)


def test_task_brake_halts_with_event(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    limits = Limits(brakes=Brakes(tasks_per_turn=2))
    update = run_join(three_task_state(), limits=limits)
    assert set(update) == {"halt", "check_events"}
    assert update["halt"].reason is HaltReason.BRAKE_TASKS
    assert update["halt"].node == "plan_join"
    (event,) = update["check_events"]
    assert event.check == "brake"
    assert event.result == "fired"
    assert event.codes == ("brake_tasks", "plan_join")
    (sig,) = signals(caplog)
    assert sig["name"] == "brake_fired"
    assert sig["cause"] == "brake_tasks"
    assert sig["node"] == "plan_join"


def test_plan_join_skips_on_halt() -> None:
    halt = Halt(reason=HaltReason.DEADLINE, node="planner", elapsed_ms=1)
    assert run_join(make_state(WP3, halt=halt)) == {}


def test_danger_raised_skips_brake(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    raised = DangerAssessment(label="danger", raised=True, confidence=None, failure=None)
    state = three_task_state(danger=raised)
    assert run_join(state, limits=Limits(brakes=Brakes(tasks_per_turn=2))) == {}
    assert signals(caplog) == []


# --- PA-1 ---------------------------------------------------------------------------------------------------


def test_wp3_example_pair(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="meridian.signal")
    gw = ScriptedGateway(
        {
            Role.PLANNER: [ok(Role.PLANNER, WP3_PICKS)],
            Role.CLASSIFIER: [ok(Role.CLASSIFIER, {"danger_level": "normal"})],
        }
    )
    state = make_state(WP3)
    planned = planner(state, runtime(make_ctx(TURN_1)), deps=make_deps(gw))
    classified = danger_classifier(state, runtime(make_ctx(TURN_1)), deps=make_deps(gw))
    state = merged(state, planned, classified)
    plan = plan_join(state, runtime(make_ctx(TURN_1)), deps=make_deps(gw))["plan"]
    assert state.danger is not None
    assert state.danger.raised is False
    assert [e.result for e in state.check_events if e.check == "classifier"] == ["pass"]
    assert plan == Plan(
        mode="act",
        tasks=(
            PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=True),
        ),
        handoff_request=None,
        topic="booking",
        source="planner",
    )
    assert {r for r, _ in gw.calls} == {Role.PLANNER, Role.CLASSIFIER}
    assert len(gw.calls) == 2
    assert signals(caplog) == []


# --- AC-7 ---------------------------------------------------------------------------------------------------


def test_plan_nodes_write_only_own_keys() -> None:
    def cls(*outcomes: Any) -> ScriptedGateway:
        return ScriptedGateway({Role.CLASSIFIER: list(outcomes)})

    planner_updates = [
        run_planner(ScriptedGateway({Role.PLANNER: [ok(Role.PLANNER, WP3_PICKS)]})),
        run_planner(
            ScriptedGateway(
                {
                    Role.PLANNER: [failed(Role.PLANNER, ProviderFailureKind.TIMEOUT)],
                    Role.PLANNER_FALLBACK: [ok(Role.PLANNER_FALLBACK, WP3_PICKS)],
                }
            )
        ),
        run_planner(both_fail()),
        run_planner(ScriptedGateway({Role.PLANNER: [halted(Role.PLANNER, HaltReason.DEADLINE)]})),
        run_planner(
            ScriptedGateway(
                {
                    Role.PLANNER: [failed(Role.PLANNER, ProviderFailureKind.TIMEOUT)],
                    Role.PLANNER_FALLBACK: [halted(Role.PLANNER_FALLBACK, HaltReason.DEADLINE)],
                }
            )
        ),
    ]
    danger_updates = [
        run_classifier(cls(ok(Role.CLASSIFIER, {"danger_level": "danger"}))),
        run_classifier(cls(failed(Role.CLASSIFIER, ProviderFailureKind.TIMEOUT))),
        run_classifier(cls(halted(Role.CLASSIFIER, HaltReason.DEADLINE))),
    ]
    join_updates = [
        run_join(merged(make_state(WP3), planner_updates[0])),
        run_join(three_task_state(), limits=Limits(brakes=Brakes(tasks_per_turn=2))),
        run_join(make_state(WP3, halt=Halt(reason=HaltReason.DEADLINE, node="planner", elapsed_ms=1))),
    ]
    planner_keys = {"planner", "halt"}
    danger_keys = {"danger", "check_events", "halt"}
    join_keys = {"plan", "check_events", "halt"}
    assert all(set(u) <= planner_keys for u in planner_updates)
    assert all(set(u) <= danger_keys for u in danger_updates)
    assert all(set(u) <= join_keys for u in join_updates)
    assert PlannerUpdate.__required_keys__ | PlannerUpdate.__optional_keys__ == planner_keys
    assert DangerUpdate.__required_keys__ | DangerUpdate.__optional_keys__ == danger_keys
    assert PlanJoinUpdate.__required_keys__ | PlanJoinUpdate.__optional_keys__ == join_keys
    assert planner_keys & danger_keys <= {"halt", "check_events"}


# --- AC-10 --------------------------------------------------------------------------------------------------


def test_outcomes_carry_provenance_for_turn_trace() -> None:
    probs = {"topic": {"booking": 0.9, "other": 0.1}}
    update = run_planner(ScriptedGateway({Role.PLANNER: [ok(Role.PLANNER, WP3_PICKS, probabilities=probs)]}))
    out = update["planner"]
    assert out.probabilities == probs
    assert out.model == JEV_MODEL
    assert out.fallback_used is False
    assert out.failure is None

    gw = ScriptedGateway(
        {
            Role.CLASSIFIER: [
                ok(
                    Role.CLASSIFIER,
                    {"danger_level": "normal"},
                    probabilities={"danger_level": {"normal": 0.97}},
                ),
                ok(Role.CLASSIFIER, {"danger_level": "normal"}),
            ]
        }
    )
    first = run_classifier(gw)
    second = run_classifier(gw)
    assert first["danger"].confidence == 0.97
    assert second["danger"].confidence is None
    assert len(first["check_events"]) == 1
    assert len(second["check_events"]) == 1

    plan = run_join(merged(make_state(WP3), update))["plan"]
    trace = PlannerTrace(
        model=out.model,
        fallback_used=out.fallback_used,
        failure=None,
        plan_mode=plan.mode,
        plan_source=plan.source,
        intents=tuple(t.intent for t in plan.tasks),
        handoff_request=plan.handoff_request,
        topic=plan.topic,
        planner_failed=plan.planner_failed,
    )
    assert trace.intents == (TaskIntent.BOOK_NEW,)
    assert trace.handoff_request is None

    fb = run_planner(
        ScriptedGateway(
            {
                Role.PLANNER: [failed(Role.PLANNER, ProviderFailureKind.TIMEOUT)],
                Role.PLANNER_FALLBACK: [ok(Role.PLANNER_FALLBACK, WP3_PICKS, probabilities=probs)],
            }
        )
    )
    assert fb["planner"].probabilities is None
