"""J-4 WP-4: a fee-bearing change becomes a P2 case with the policy-table promise (AEA-39 AC-15).

Level: mock-tested. The real `build_graph` and real act nodes run with AEA-21's doubles for the other nodes, doubles
for the runner and the scheduling read, and AEA-29's real `HandoffService` and `CaseService` on a temp SQLite copy of
the issued database. No server, no model.
Blocked by AEA-51: the CON-2 response and the case on screen through the wired turn need the graph wired into
AEA-40's `submitTurn` on AEA-57's harness.
"""

from __future__ import annotations

import hashlib

import pytest

from meridian.domain.blocks import HandoffBlock
from meridian.domain.handoff import HandoffReason, Priority
from meridian.domain.specialists import SchedulingSlice
from meridian.domain.turn import TaskIntent
from meridian.policy.handoff import PROMISE_TABLE, promise_for
from tests.fakes import WORKED_PAIRS_NOW
from tests.fixtures.sqlite import ISSUED_DB, temp_sqlite
from tests.services._case_fixtures import new_thread, services, summary_of
from tests.unit.agent.nodes.act_fixtures import (
    T1,
    WP4_APPOINTMENT,
    WP4_DRAFT,
    WP4_TEXT,
    RunnerDouble,
    SchedulingDouble,
    act_harness,
    act_plan,
    deps_for,
    plan_join_returning,
    scheduling,
    task,
    verified_load_context,
)

pytestmark = pytest.mark.journey


def test_j4_wp4_fee_bearing_change_p2_case_policy_promise(monkeypatch: pytest.MonkeyPatch) -> None:
    issued_before = hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest()
    with temp_sqlite() as db:
        with db.uow(write=True) as tx:
            thread, _ = new_thread(tx, customer_text=WP4_TEXT)
            tx.commit()
        with db.uow() as tx:
            appt_before = tx.booking.appointments.get(1)
        _, handoff_svc, _, _ = services(db.uow)
        runner = RunnerDouble({"scheduling": scheduling("staff_change_request", change_request=WP4_DRAFT)})
        sched = SchedulingDouble()
        deps = deps_for(runner=runner, scheduling_=sched, handoff_=handoff_svc)
        h = act_harness(
            monkeypatch,
            deps,
            thread=thread,
            load_context=verified_load_context("MHC-57204"),
            plan_join=plan_join_returning({T1: act_plan(task(1, "scheduling", TaskIntent.RESCHEDULE))}),
        )
        out = h.run(T1, WP4_TEXT)
        values = h.values()
        result = values["handoff"]
        with db.uow() as tx:
            stored = summary_of(tx, result.case.case_ref)
            appt_after = tx.booking.appointments.get(1)

    assert len(runner.calls) == 1
    sent = runner.calls[0][0].slice
    assert isinstance(sent, SchedulingSlice)
    assert (sent.customer_zone, sent.member, sent.appointments) == ("central", False, (WP4_APPOINTMENT,))
    assert sched.calls == ["slice_inputs"]
    decision = values["escalation"]
    assert (decision.outcome, decision.reason, decision.priority, decision.rule_id) == (
        "escalate",
        HandoffReason.FEE_BEARING_CHANGE,
        Priority.P2,
        "R21.fee_bearing",
    )
    assert result.created is True
    assert result.alert == "supervisor_now"
    assert stored.reason is HandoffReason.FEE_BEARING_CHANGE
    assert stored.priority is Priority.P2
    assert stored.due_at == WP4_DRAFT.window_start
    assert stored.promise.policy_row == "R26.unstaffed"
    assert stored.promise.text == PROMISE_TABLE["R26.unstaffed"]
    assert stored.promise.due_label == "Monday, October 19, 7:00 pm"
    assert len(stored.promise.extra_lines) == 2
    assert stored.promise == promise_for(
        HandoffReason.FEE_BEARING_CHANGE, "nobody_online", WORKED_PAIRS_NOW, WP4_DRAFT.window_start
    )
    assert appt_after == appt_before
    assert hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest() == issued_before
    blocks = [x for x in out.reply.blocks if isinstance(x, HandoffBlock)]
    assert len(blocks) == 1
    assert blocks[0].promise_text == PROMISE_TABLE["R26.unstaffed"]
    assert blocks[0].reference == str(result.case.case_ref)
    assert out.turn_trace.outcome == "handed_off"
