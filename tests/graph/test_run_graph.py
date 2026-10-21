"""run_graph outcome flags: closed_every_open_task (AEA-21 AC-14; graph-core section 2)."""

from __future__ import annotations

import typing

import pytest

from meridian.domain.common import Halt, HaltReason, TurnId
from meridian.domain.state import OpenTask, TaskDetails
from meridian.domain.turn import Plan, PlannedTask, TaskIntent
from tests.graph._spine_doubles import Harness, default_doubles
from tests.graph.test_spine import looping_load_context

T1 = TurnId("1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d")
_Fn = typing.Callable[..., typing.Any]


def book_plan(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
    task = PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=False)
    return {"plan": Plan(mode="act", tasks=(task,), handoff_request=None, topic="booking", source="planner")}


def facts_with(status: typing.Any) -> _Fn:
    def double(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        task = OpenTask(
            task_id="t-1",
            specialist="scheduling",
            intent=TaskIntent.BOOK_NEW,
            opened_turn=T1,
            details=TaskDetails(),
            status=status,
        )
        return {**default_doubles()["facts"](state, runtime, deps=deps), "open_tasks": [task]}

    return double


def deadline(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
    return {"halt": Halt(reason=HaltReason.DEADLINE, node="responder", elapsed_ms=3)}


_CASES: dict[str, tuple[dict[str, _Fn], bool]] = {
    "booking_task_done": ({"plan_join": book_plan, "facts": facts_with("done")}, True),
    "talk_turn": ({}, False),
    "task_left_open": ({"plan_join": book_plan, "facts": facts_with("open")}, False),
    "halted_turn": ({"plan_join": book_plan, "facts": facts_with("done"), "responder": deadline}, False),
    "recursion_path": ({"load_context": looping_load_context()}, False),
}


@pytest.mark.parametrize("name", list(_CASES))
def test_closed_every_open_task(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    overrides, expected = _CASES[name]
    outcome = Harness(monkeypatch, **overrides).run(T1)
    print(name, "->", outcome.closed_every_open_task)
    assert outcome.closed_every_open_task is expected
