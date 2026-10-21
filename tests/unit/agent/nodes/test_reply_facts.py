"""AEA-38: the facts node (AC-1, AC-10, PA-1, PA-2)."""

from __future__ import annotations

from meridian.agent.nodes import reply
from meridian.domain.actions import ActionKind
from meridian.domain.common import FailureCounters, Halt, HaltReason
from meridian.domain.identity import NotVerified
from meridian.domain.specialists import KnowledgeResult, SchedulingResult
from meridian.domain.state import ConversationState, FactsUpdate
from meridian.domain.turn import GateKind, Plan, PlannedTask, TaskIntent
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.agent.nodes.reply_fixtures import (  # noqa: F401
    MOVED_T3,
    THREAD,
    TURN_4,
    TURN_5,
    FakeCaseService,
    booked,
    deps,
    gate,
    gateway,
    knowledge_answered,
    passage,
    run,
    seed,
    state,
    tool_record,
    turn_ctx,
    write_result,
)


def _facts(st: ConversationState, store: object, *, turn: object = TURN_4) -> FactsUpdate:
    gw, _ = gateway()
    d = deps(uow=store.uow, gw=gw)  # type: ignore[attr-defined]
    return reply.facts(st, run(turn_ctx(turn=turn)), deps=d)  # type: ignore[arg-type]


def _written(turn: object = TURN_4) -> SchedulingResult:
    return SchedulingResult(status="written", write=write_result(booked(turn)), tools=(), calls=())  # type: ignore[arg-type]


def test_settled_reread_from_db() -> None:
    with temp_sqlite() as store:
        seed(store, actions=[booked(TURN_4)])
        from tests.unit.agent.nodes.reply_fixtures import settled

        st = state(settled=settled(MOVED_T3), specialist_results=[_written()])
        update = _facts(st, store)
    assert [(a.kind, a.key.turn_id) for a in update["settled"].actions] == [(ActionKind.BOOKED, TURN_4)]
    assert update["settled"].actions[0].at == booked(TURN_4).at
    assert update["facts"].writes_this_turn == update["settled"].actions
    assert update["counters"].bookings == 1
    with temp_sqlite() as store:
        update = _facts(state(specialist_results=[_written()]), store)
    assert update["settled"].actions == ()
    assert update["facts"].writes_this_turn == ()
    assert update["counters"].bookings == 0


def test_failure_counters_rules() -> None:
    with temp_sqlite() as store:
        seed(store, actions=[booked(TURN_4)])
        st = state(
            counters=FailureCounters(timeouts=2),
            specialist_results=[
                KnowledgeResult(status="no_current_source", passages=(), points=(), tools=(), calls=())
            ],
            gate=gate(correction=True),
            identity_step=NotVerified(),
        )
        c = _facts(st, store)["counters"]
    assert (c.failed_answers, c.corrections, c.identity_failures, c.bookings) == (1, 1, 1, 1)
    assert (c.tool_failures, c.timeouts) == (0, 2)
    from meridian.domain.common import ToolErrorCode

    with temp_sqlite() as store:
        st = state(
            specialist_results=[
                SchedulingResult(status="failed", tools=(), calls=()),
                KnowledgeResult(
                    status="answered",
                    passages=(),
                    points=(),
                    tools=(tool_record(error=ToolErrorCode.TOOL_FAILED),),
                    calls=(),
                ),
            ]
        )
        c = _facts(st, store)["counters"]
    assert c.tool_failures == 1


def test_quick_checks_into_turn_facts() -> None:
    p1 = passage("troubleshooting/ac_not_cooling.md", 1, "Check the filter.")
    p2 = passage("troubleshooting/ac_not_cooling.md", 2, "Check the thermostat.")
    with temp_sqlite() as store:
        st = state(
            specialist_results=[
                SchedulingResult(status="windows_shown", quick_checks=(p1, p2, p1), tools=(), calls=())
            ]
        )
        f = _facts(st, store)["facts"]
    assert f.quick_checks == (p1.passage_id, p2.passage_id)
    assert [p.passage_id for p in f.passages] == [p1.passage_id, p2.passage_id]


def _act_plan(*, resumes: str | None = None, needs_identity: bool = False, spec: str = "scheduling") -> Plan:
    return Plan(
        mode="act",
        tasks=(
            PlannedTask(
                order=1,
                specialist=spec,  # type: ignore[arg-type]
                intent=TaskIntent.BOOK_NEW if spec == "scheduling" else TaskIntent.READ_INVOICE,
                needs_identity=needs_identity,
                resumes_task_id=resumes,
            ),
        ),
        handoff_request=None,
        topic="booking",
        source="planner",
    )


def test_open_tasks_lifecycle() -> None:
    from meridian.domain.records import ShownSlot  # noqa: F401

    with temp_sqlite() as store:
        shown = SchedulingResult(status="windows_shown", tools=(), calls=())
        u1 = _facts(state(plan=_act_plan(), specialist_results=[shown]), store)
        assert [(t.task_id, t.status) for t in u1["open_tasks"]] == [("task-a2b4c6d8-1", "open")]
        u2 = _facts(
            state(
                plan=_act_plan(resumes="task-a2b4c6d8-1"),
                open_tasks=u1["open_tasks"],
                specialist_results=[_written(TURN_5)],
            ),
            store,
            turn=TURN_5,
        )
        assert [(t.task_id, t.status) for t in u2["open_tasks"]] == [("task-a2b4c6d8-1", "done")]
        u3 = _facts(state(open_tasks=u2["open_tasks"]), store, turn=TURN_5)
        assert u3["open_tasks"] == []
        u4 = _facts(state(plan=_act_plan(needs_identity=True, spec="account")), store)
        assert [t.status for t in u4["open_tasks"]] == ["waiting_identity"]


def test_shown_slots_replaced_and_cleared() -> None:
    from datetime import date

    from meridian.domain.records import ShownSlot

    slot = ShownSlot(
        slot_id=7,
        date=date(2026, 10, 20),
        window="12:00-16:00",
        technician="Marta Kowalski",
        service_type="hvac_repair",
        zone="north",
        member_reserved=False,
        shown_turn=TURN_4,
    )
    with temp_sqlite() as store:
        u = _facts(
            state(
                specialist_results=[
                    SchedulingResult(status="windows_shown", windows=(slot,), tools=(), calls=())
                ]
            ),
            store,
        )
        assert u["shown_slots"] == [slot]
        u = _facts(state(shown_slots=[slot], specialist_results=[_written()]), store)
        assert u["shown_slots"] == []
        u = _facts(state(shown_slots=[slot], specialist_results=[knowledge_answered()]), store)
        assert u["shown_slots"] == [slot]


def test_facts_runs_on_halted_state() -> None:
    halt = Halt(reason=HaltReason.DEADLINE, node="run_specialist", elapsed_ms=60000)
    with temp_sqlite() as store:
        u = _facts(state(halt=halt, gate=gate(GateKind.FREE_TEXT)), store)
    assert set(u) == {"facts", "settled", "open_tasks", "shown_slots", "counters"}
    assert THREAD
