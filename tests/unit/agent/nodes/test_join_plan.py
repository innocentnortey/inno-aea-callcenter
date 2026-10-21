"""join_plan: SP-1's normalize rows (AEA-37 AC-5). Pure: no gateway, no clock."""

from __future__ import annotations

import typing

import pytest

from meridian.agent.nodes.plan import (
    _ACCOUNT_INTENT,
    _HANDOFF_REASON,
    _SCHEDULING_INTENT,
    _TOPIC_BY_INTENT,
    TaskBrakeExceeded,
    join_plan,
)
from meridian.domain.common import HandoffReason, ProviderFailureKind
from meridian.domain.turn import Plan, PlannedTask, PlannerChoices, PlannerOutcome, TaskIntent
from tests.unit.agent.nodes.plan_fixtures import (
    LATE_TECH,
    WP1,
    WP3_PICK,
    WP4F,
    WP7,
    WP8,
    choices,
    failure,
    free_text_gate,
    make_state,
    open_task,
)


def outcome(*, fallback: bool = False, **picks: str) -> PlannerOutcome:
    return PlannerOutcome(
        choices=PlannerChoices.model_validate(choices(**picks)),
        probabilities=None,
        model="m",
        fallback_used=fallback,
        failure=None,
    )


def test_wp7_policy_word_wins() -> None:
    gate = free_text_gate(policy_trigger=HandoffReason.REFUND, rule_ids=("R24.refund",))
    plan = join_plan(outcome(topic="billing"), None, gate, make_state(WP7, gate=gate))
    assert plan.handoff_request is HandoffReason.REFUND
    assert plan.tasks == ()
    assert plan.mode == "act"
    assert plan.source == "planner"
    assert plan.topic == "billing"


def test_wp8_membership_cancel_reads_membership_then_knowledge() -> None:
    plan = join_plan(
        outcome(handoff="membership_cancel", topic="membership"), None, free_text_gate(), make_state(WP8)
    )
    assert [t.intent for t in plan.tasks] == [TaskIntent.READ_MEMBERSHIP, TaskIntent.ANSWER_QUESTION]
    assert [t.specialist for t in plan.tasks] == ["account", "knowledge"]
    assert [t.order for t in plan.tasks] == [1, 2]
    assert [t.needs_identity for t in plan.tasks] == [True, False]
    assert plan.handoff_request is HandoffReason.MEMBERSHIP_CANCEL
    assert plan.topic == "membership"


def test_late_technician_maps_to_reason() -> None:
    plan = join_plan(
        outcome(handoff="late_technician", topic="booking"), None, free_text_gate(), make_state(LATE_TECH)
    )
    assert plan.handoff_request is HandoffReason.LATE_TECHNICIAN
    assert plan.tasks == ()
    assert plan.mode == "act"
    assert plan.topic == "booking"


def test_unsupported_other_maps_to_unsupported_action() -> None:
    plan = join_plan(outcome(handoff="unsupported_other"), None, free_text_gate(), make_state("x"))
    assert plan.handoff_request is HandoffReason.UNSUPPORTED_ACTION
    assert plan.topic == "other"


def test_reschedule_reads_appointments_itself() -> None:
    plan = join_plan(
        outcome(scheduling="reschedule", account="appointments", topic="booking"),
        None,
        free_text_gate(),
        make_state("move my visit"),
    )
    assert len(plan.tasks) == 1
    assert plan.tasks[0].specialist == "scheduling"
    assert plan.tasks[0].intent is TaskIntent.RESCHEDULE
    assert plan.topic == "booking"


def test_yes_please_continues_open_task() -> None:
    state = make_state(WP4F, tasks=(open_task("t-1"),))
    plan = join_plan(outcome(topic="booking"), None, free_text_gate(), state)
    assert plan.source == "open_task"
    assert len(plan.tasks) == 1
    assert plan.tasks[0].resumes_task_id == "t-1"
    assert plan.topic == "booking"


def test_slot_pick_continues_open_task() -> None:
    state = make_state(WP3_PICK, tasks=(open_task("t-2", intent=TaskIntent.BOOK_NEW),))
    plan = join_plan(outcome(topic="booking"), None, free_text_gate(), state)
    assert plan.source == "open_task"
    assert plan.tasks[0].intent is TaskIntent.BOOK_NEW
    assert plan.tasks[0].resumes_task_id == "t-2"


@pytest.mark.parametrize("tasks", [(), (open_task("t-1", status="done"),)])
def test_yes_please_without_open_task_is_talk(tasks: tuple[object, ...]) -> None:
    """WP-4F turn 4: the move is closed, so the planner's all-none answer means talk."""
    state = make_state(WP4F, tasks=tasks)  # type: ignore[arg-type]
    plan = join_plan(outcome(topic="booking"), None, free_text_gate(), state)
    assert plan == Plan(mode="talk", tasks=(), handoff_request=None, topic="booking", source="planner")


def test_tasks_ordered_account_scheduling_knowledge() -> None:
    plan = join_plan(
        outcome(account="invoice", scheduling="book_new", knowledge="yes", topic="billing"),
        None,
        free_text_gate(),
        make_state("x"),
    )
    assert [t.specialist for t in plan.tasks] == ["account", "scheduling", "knowledge"]
    assert [t.order for t in plan.tasks] == [1, 2, 3]
    assert plan.topic == "billing"


def test_wp1_membership_question() -> None:
    plan = join_plan(outcome(knowledge="yes", topic="membership"), None, free_text_gate(), make_state(WP1))
    assert plan == Plan(
        mode="act",
        tasks=(
            PlannedTask(
                order=1, specialist="knowledge", intent=TaskIntent.ANSWER_QUESTION, needs_identity=False
            ),
        ),
        handoff_request=None,
        topic="membership",
        source="planner",
    )


def test_fallback_planner_source() -> None:
    plan = join_plan(outcome(fallback=True, knowledge="yes"), None, free_text_gate(), make_state("x"))
    assert plan.source == "fallback_planner"


def test_task_brake_raises_before_plan() -> None:
    picks = outcome(account="invoice", scheduling="book_new", knowledge="yes")
    with pytest.raises(TaskBrakeExceeded) as info:
        join_plan(picks, None, free_text_gate(), make_state("x"), tasks_per_turn=2)
    assert info.value.count == 3
    assert info.value.limit == 2
    assert str(info.value) == "plan has 3 tasks; the brake allows 2"


def test_failed_planner_without_follow_up_is_planner_failed() -> None:
    failed = PlannerOutcome(
        choices=None,
        probabilities=None,
        model="m",
        fallback_used=True,
        failure=failure(ProviderFailureKind.SERVER),
    )
    plan = join_plan(failed, None, free_text_gate(), make_state("Can you help me?"))
    assert plan == Plan(
        mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True
    )


def test_choice_maps_cover_every_option() -> None:
    def options(field: str) -> set[str]:
        return set(typing.get_args(PlannerChoices.model_fields[field].annotation))

    assert set(_ACCOUNT_INTENT) | {"none"} == options("account")
    assert set(_SCHEDULING_INTENT) | {"none"} == options("scheduling")
    assert set(_HANDOFF_REASON) == options("handoff")
    assert set(_TOPIC_BY_INTENT) == set(TaskIntent)
