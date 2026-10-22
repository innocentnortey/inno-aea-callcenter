"""FU-identity-plan (AEA-51 finding F-1): facts keeps a waiting task's handoff request across the identity detour."""

from __future__ import annotations

from meridian.agent.nodes import reply
from meridian.domain.common import HandoffReason
from meridian.domain.specialists import SchedulingResult
from meridian.domain.state import ConversationState, FactsUpdate, OpenTask, TaskDetails
from meridian.domain.turn import Plan, PlannedTask, TaskIntent
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent.nodes.reply_fixtures import TURN_3, TURN_4, deps, gateway, run, state, turn_ctx


def _facts(st: ConversationState, store: object) -> FactsUpdate:
    gw, _ = gateway()
    return reply.facts(st, run(turn_ctx(turn=TURN_4)), deps=deps(uow=store.uow, gw=gw))  # type: ignore[attr-defined]


def _plan(request: HandoffReason | None, *, resumes: str | None = None, source: str = "rules_only") -> Plan:
    return Plan(
        mode="act",
        tasks=(
            PlannedTask(
                order=1,
                specialist="scheduling",
                intent=TaskIntent.BOOK_NEW,
                needs_identity=True,
                resumes_task_id=resumes,
            ),
        ),
        handoff_request=request,
        topic="booking",
        source=source,  # type: ignore[arg-type]
    )


def test_waiting_task_carries_the_plan_request() -> None:
    with temp_sqlite() as store:
        update = _facts(state(plan=_plan(HandoffReason.BURNING_RULED_OUT)), store)
    [task] = update["open_tasks"]
    assert task.status == "waiting_identity"
    assert task.handoff_request is HandoffReason.BURNING_RULED_OUT
    assert task.task_id == f"task-{str(TURN_4)[:8]}-1"


def test_task_that_runs_drops_the_request() -> None:
    old = OpenTask(
        task_id="t-1",
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        opened_turn=TURN_3,
        details=TaskDetails(),
        status="waiting_identity",
        handoff_request=HandoffReason.BURNING_RULED_OUT,
    )
    st = state(
        plan=_plan(HandoffReason.BURNING_RULED_OUT, resumes="t-1", source="open_task"),
        open_tasks=[old],
        specialist_results=[SchedulingResult(status="windows_shown", tools=(), calls=())],
    )
    with temp_sqlite() as store:
        update = _facts(st, store)
    [task] = update["open_tasks"]
    assert task.task_id == "t-1"
    assert task.status == "open"
    assert task.handoff_request is None


def test_no_request_stays_none() -> None:
    with temp_sqlite() as store:
        update = _facts(state(plan=_plan(None)), store)
    [task] = update["open_tasks"]
    assert task.status == "waiting_identity"
    assert task.handoff_request is None
