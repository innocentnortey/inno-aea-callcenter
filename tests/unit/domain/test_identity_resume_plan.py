"""FU-identity-plan (AEA-51 finding F-1): the identity-resume plan is a pure function of the open tasks."""

from __future__ import annotations

import pytest

from meridian.domain.common import HandoffReason, TurnId
from meridian.domain.state import OpenTask, TaskDetails, identity_resume_plan
from meridian.domain.turn import SpecialistKind, TaskIntent

_TURN = TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")


def _task(
    task_id: str,
    specialist: SpecialistKind,
    intent: TaskIntent,
    status: str,
    request: HandoffReason | None = None,
) -> OpenTask:
    return OpenTask.model_validate(
        {
            "task_id": task_id,
            "specialist": specialist,
            "intent": intent,
            "opened_turn": _TURN,
            "details": TaskDetails(),
            "status": status,
            "handoff_request": request,
        }
    )


def test_verified_resumes_a_carried_request() -> None:
    tasks = [
        _task("t-1", "scheduling", TaskIntent.BOOK_NEW, "waiting_identity", HandoffReason.BURNING_RULED_OUT)
    ]
    plan = identity_resume_plan(tasks, "verified")
    assert plan is not None
    assert plan.mode == "act"
    assert plan.handoff_request is HandoffReason.BURNING_RULED_OUT
    assert plan.source == "open_task"
    assert plan.topic == "booking"
    assert plan.planner_failed is False
    assert [(t.order, t.specialist, t.intent, t.needs_identity, t.resumes_task_id) for t in plan.tasks] == [
        (1, "scheduling", TaskIntent.BOOK_NEW, True, "t-1")
    ]


def test_verified_without_a_carried_request_returns_none() -> None:
    assert (
        identity_resume_plan(
            [_task("t-1", "account", TaskIntent.READ_INVOICE, "waiting_identity")], "verified"
        )
        is None
    )


def test_code_locked_resumes_waiting_tasks() -> None:
    plan = identity_resume_plan(
        [_task("t-1", "account", TaskIntent.READ_INVOICE, "waiting_identity")], "code_locked"
    )
    assert plan is not None
    assert plan.handoff_request is None
    assert plan.topic == "billing"
    assert plan.tasks[0].needs_identity is True
    assert (
        identity_resume_plan([_task("t-1", "account", TaskIntent.READ_INVOICE, "open")], "code_locked")
        is None
    )
    assert identity_resume_plan([], "code_locked") is None


@pytest.mark.parametrize(
    "kind", ["located", "not_verified", "code_sent", "code_cap_reached", "code_wrong", "code_expired"]
)
def test_other_steps_never_resume(kind: str) -> None:
    tasks = [
        _task("t-1", "scheduling", TaskIntent.BOOK_NEW, "waiting_identity", HandoffReason.BURNING_RULED_OUT)
    ]
    assert identity_resume_plan(tasks, kind) is None


def test_resume_plan_skips_done_and_caps_at_three() -> None:
    tasks = [
        _task("t-0", "account", TaskIntent.READ_INVOICE, "done"),
        _task(
            "t-1", "account", TaskIntent.READ_MEMBERSHIP, "waiting_identity", HandoffReason.MEMBERSHIP_CANCEL
        ),
        _task("t-2", "knowledge", TaskIntent.ANSWER_QUESTION, "open"),
        _task("t-3", "scheduling", TaskIntent.BOOK_NEW, "waiting_identity"),
        _task("t-4", "account", TaskIntent.READ_WARRANTY, "open"),
    ]
    plan = identity_resume_plan(tasks, "verified")
    assert plan is not None
    assert [t.resumes_task_id for t in plan.tasks] == ["t-1", "t-2", "t-3"]
    assert [t.order for t in plan.tasks] == [1, 2, 3]
    assert [t.needs_identity for t in plan.tasks] == [True, False, True]
    assert plan.handoff_request is HandoffReason.MEMBERSHIP_CANCEL
    assert plan.topic == "membership"


def test_open_task_request_defaults_to_none() -> None:
    task = OpenTask.model_validate(
        {
            "task_id": "t-1",
            "specialist": "account",
            "intent": TaskIntent.READ_INVOICE,
            "opened_turn": _TURN,
            "details": TaskDetails(),
            "status": "open",
        }
    )
    assert task.handoff_request is None
