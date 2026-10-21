"""J-3 booking write, then "Yes, please." with no new write (AEA-39 AC-15).

Level: mock-tested. The real `build_graph` and the real act nodes run with AEA-21's doubles for the other nodes and
doubles for the runner, scheduling and handoff services. No server, no database, no model.
Blocked by AEA-51: the integrated steps (confirmation card on screen, appointment row stored, the follow-up reply
naming the new window) need the graph wired into AEA-40's CON-2 `submitTurn` on AEA-57's harness.
"""

from __future__ import annotations

import pytest

from meridian.domain.actions import ActionKind
from meridian.domain.turn import TaskIntent
from tests.unit.agent.nodes.act_fixtures import (
    T1,
    T2,
    HandoffDouble,
    RunnerDouble,
    SchedulingDouble,
    act_harness,
    act_plan,
    booked_write,
    deps_for,
    plan_join_returning,
    scheduling,
    talk_plan,
    task,
    verified_load_context,
)

pytestmark = pytest.mark.journey


def test_j3_booking_write_then_yes_please_no_new_write(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = RunnerDouble({"scheduling": scheduling("written", write=booked_write(T1))})
    sched = SchedulingDouble()
    handoff = HandoffDouble()
    deps = deps_for(runner=runner, scheduling_=sched, handoff_=handoff)
    h = act_harness(
        monkeypatch,
        deps,
        load_context=verified_load_context("MHC-57204"),
        plan_join=plan_join_returning(
            {T1: act_plan(task(1, "scheduling", TaskIntent.BOOK_NEW)), T2: talk_plan()}
        ),
    )
    out1 = h.run(T1, "My AC stopped cooling, can someone come out Monday morning?")
    values = h.values()
    assert values["escalation"].outcome == "none"
    assert [r.kind for r in values["specialist_results"]] == ["scheduling"]
    write = values["specialist_results"][0].write
    assert write is not None
    assert write.action.kind is ActionKind.BOOKED
    assert out1.turn_trace.specialists_run == ("scheduling",)

    out2 = h.run(T2, "Yes, please.")
    assert out2.turn_trace.specialists_run == ()
    assert h.visits.count("run_specialist") == 1
    assert len(runner.calls) == 1
    assert handoff.requests == []
    assert sched.calls == ["slice_inputs"]
