"""The compiled graph with node doubles and an in-memory saver (AEA-21 AC-1 to AC-9, AC-13; PA-7)."""

from __future__ import annotations

import importlib.metadata
import inspect
import logging
import threading
import time
import typing

import pytest
from langgraph.types import Command
from pydantic import SecretStr

from meridian.agent import graph as graph_mod
from meridian.agent.nodes import act, front, plan, reply
from meridian.domain import blocks as b
from meridian.domain.common import FailureCounters, Halt, HaltReason, Priority, TurnId
from meridian.domain.identity import FormValues
from meridian.domain.records import ShownSlot
from meridian.domain.specialists import AccountResult, KnowledgeResult, StaffNote
from meridian.domain.state import ChatLine, ConversationState, OpenTask, TaskDetails
from meridian.domain.turn import (
    CheckEvent,
    DangerAssessment,
    EscalationDecision,
    Intake,
    Plan,
    PlannedTask,
    TaskIntent,
)
from tests.graph._spine_doubles import DEMO_NOW, THREAD, Harness, default_doubles
from tests.unit.agent.nodes import compose_fixtures as fx

T1 = TurnId("1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d")
T2 = TurnId("2b3c4d5e-6f7a-4b8c-9d0e-1f2a3b4c5d6e")
_CODE_SENTINEL = "914276"
_PHONE_SENTINEL = "512-555-0199"
_STAFF_SENTINEL = "SENTINEL-STAFF-NOTE-7731"
_Fn = typing.Callable[..., typing.Any]


def act_plan(*specialists: typing.Any) -> _Fn:
    """A plan_join double: an act plan with one task per specialist, none needing identity."""

    def double(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        tasks = tuple(
            PlannedTask(order=i + 1, specialist=s, intent=TaskIntent.ANSWER_QUESTION, needs_identity=False)
            for i, s in enumerate(specialists)
        )
        return {"plan": Plan(mode="act", tasks=tasks, handoff_request=None, topic="other", source="planner")}

    return double


def sleeper(name: str) -> _Fn:
    def double(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        time.sleep(1.0)
        return default_doubles()[name](state, runtime, deps=deps)

    return double


def test_compiled_edges_match_table(monkeypatch: pytest.MonkeyPatch) -> None:
    h = Harness(monkeypatch)
    actual = {(e.source, e.target) for e in h.graph.get_graph().edges}
    static = {
        ("__start__", "load_context"),
        ("load_context", "gates"),
        ("safety", "compose"),
        ("planner", "plan_join"),
        ("danger_classifier", "plan_join"),
        ("handoff", "facts"),
        ("responder", "checks"),
        ("brief", "checks"),
        ("checks", "compose"),
        ("compose", "__end__"),
    }
    maps = {
        "gates": graph_mod.GATES_PATHS,
        "identity": graph_mod.IDENTITY_PATHS,
        "plan_join": graph_mod.PLAN_JOIN_PATHS,
        "run_specialist": graph_mod.SPECIALISTS_PATHS,
        "escalation": graph_mod.ESCALATION_PATHS,
        "facts": graph_mod.FACTS_PATHS,
    }
    expected = static | {(src, dst) for src, paths in maps.items() for dst in paths}
    print("edges:", sorted(actual))
    assert actual == expected
    assert set(graph_mod.NODE_NAMES) | {"__start__", "__end__"} == {n for edge in actual for n in edge}


def test_skeleton_compiles_and_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    h = Harness(monkeypatch)
    out = h.run(T1)
    assert h.visits[:2] == ["load_context", "gates"]
    assert set(h.visits[2:4]) == {"planner", "danger_classifier"}
    assert h.visits[4:] == ["plan_join", "facts", "responder", "checks"]
    assert [type(x) for x in out.reply.blocks] == [b.TextBlock]
    assert typing.cast(b.TextBlock, out.reply.blocks[0]).text == "Hello from the double."


@pytest.mark.parametrize(
    ("module", "name", "path"),
    [
        (front, "gates", "front.py"),
        (front, "safety", "front.py"),
        (front, "identity", "front.py"),
        (plan, "planner", "plan.py"),
        (plan, "danger_classifier", "plan.py"),
        (plan, "plan_join", "plan.py"),
        (act, "run_specialist", "act.py"),
        (act, "escalation", "act.py"),
        (act, "handoff", "act.py"),
        (reply, "facts", "reply.py"),
        (reply, "responder", "reply.py"),
        (reply, "brief", "reply.py"),
        (reply, "checks", "reply.py"),
    ],
)
def test_stubs_raise_loudly(module: typing.Any, name: str, path: str) -> None:
    fn = getattr(module, name)
    assert list(inspect.signature(fn).parameters) == [
        next(iter(inspect.signature(fn).parameters)),
        "runtime",
        "deps",
    ]
    with pytest.raises(
        NotImplementedError, match=f"src/meridian/agent/nodes/{path} {name}: stub from AEA-21"
    ):
        fn(None, None, deps=None)


def test_brake_runs_escalation_once(monkeypatch: pytest.MonkeyPatch) -> None:
    brake = Halt(reason=HaltReason.BRAKE_TOOL_ROUNDS, node="run_specialist", elapsed_ms=40)
    case = fx.handoff_result("R26.unstaffed", "We will call.", priority=Priority.P3)

    def specialist(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        event = CheckEvent.from_halt(runtime.context.ids.turn_id, brake)
        return {
            "halt": brake,
            "check_events": (event,),
            "specialist_results": [
                KnowledgeResult(
                    status="failed", passages=(), points=(), tools=(), calls=(), brake=brake.reason
                )
            ],
        }

    def escalation(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        decision = EscalationDecision(
            outcome="escalate",
            reason=case.case.reason,
            priority=Priority.P3,
            rule_id="AI.halt",
            degraded=True,
        )
        return {"escalation": decision}

    h = Harness(
        monkeypatch,
        plan_join=act_plan("knowledge"),
        run_specialist=specialist,
        escalation=escalation,
        handoff=lambda s, r, *, deps: {"handoff": case},
    )
    out = h.run(T1)
    print("visits:", h.visits)
    assert h.visits.count("escalation") == 1
    assert h.visits[h.visits.index("escalation") :] == ["escalation", "handoff", "facts"]
    assert not {"responder", "brief", "checks"} & set(h.visits)
    assert isinstance(out.reply.blocks[-1], b.HandoffBlock)
    assert out.reply.degrade_reason == "brake"
    assert out.halt == brake


def test_turn_scoped_keys_reset_and_durable_keys_persist(monkeypatch: pytest.MonkeyPatch) -> None:
    fields = ConversationState.model_fields
    scoped, durable = set(graph_mod.TURN_SCOPED_KEYS), set(graph_mod.DURABLE_KEYS) & set(fields)
    assert scoped <= set(fields)
    assert scoped | durable | {"thread_id", "turn_input", "check_events"} == set(fields)
    assert not scoped & durable
    assert "messages" not in fields
    assert {k for k, f in fields.items() if f.metadata} == {"specialist_results", "halt", "check_events"}

    task = OpenTask(
        task_id="t-1",
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        opened_turn=T1,
        details=TaskDetails(),
        status="open",
    )
    slot = ShownSlot(
        slot_id=60,
        date=DEMO_NOW.date(),
        window="08:00-12:00",
        technician="Marta Kowalski",
        service_type="hvac_repair",
        zone="north",
        member_reserved=False,
        shown_turn=T1,
    )
    defaults = default_doubles()

    def by_turn(name: str, first: _Fn) -> _Fn:
        def double(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
            use = first if runtime.context.ids.turn_id == T1 else defaults[name]
            return use(state, runtime, deps=deps)

        return double

    def gates1(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        return {**defaults["gates"](state, runtime, deps=deps), "burning_card_id": f"burn-{T1}"}

    def facts1(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        return {
            **defaults["facts"](state, runtime, deps=deps),
            "open_tasks": [task],
            "shown_slots": [slot],
            "counters": FailureCounters(bookings=1),
        }

    def responder1(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        return {"halt": Halt(reason=HaltReason.DEADLINE, node="responder", elapsed_ms=5)}

    def plan_join(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        if runtime.context.ids.turn_id == T1:
            return act_plan("knowledge")(state, runtime, deps=deps)
        return defaults["plan_join"](state, runtime, deps=deps)

    h = Harness(
        monkeypatch,
        gates=by_turn("gates", gates1),
        facts=by_turn("facts", facts1),
        responder=by_turn("responder", responder1),
        plan_join=plan_join,
    )
    first = h.run(T1)
    one = h.values()
    assert first.halt is not None
    assert len(one["specialist_results"]) == 1
    assert one["halt"] is not None
    h.run(T2)
    two = h.values()
    print("turn 2 keys:", sorted(two))
    assert two["specialist_results"] == []
    assert two["halt"] is None
    assert {e.turn_id for e in two["check_events"]} == {T2}
    assert two["plan"].mode == "talk"
    assert two["chat_window"] == [ChatLine(speaker="customer", text="hello", turn_id=T2, at=DEMO_NOW)]
    written = sorted(durable & set(one))  # a channel nothing has written yet is absent from `values`
    print("durable keys written in turn 1:", written)
    assert {"settled", "open_tasks", "shown_slots", "counters", "burning_card_id"} <= set(written)
    for key in written:
        assert two[key] == one[key], key
    assert two["burning_card_id"] == f"burn-{T1}"
    assert two["open_tasks"] == [task]


def test_three_task_turn_under_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    h = Harness(monkeypatch, plan_join=act_plan("knowledge", "account", "scheduling"))
    out = h.run(T1)
    metadata = h.graph.get_state(h.config).metadata
    assert metadata is not None
    step = metadata["step"]
    print(f"3-task turn finished at step {step}")
    assert h.visits.count("run_specialist") == 3
    assert len(out.turn_trace.specialists_run) == 3
    assert step < graph_mod.RECURSION_LIMIT


def looping_load_context(extra: typing.Any = None) -> _Fn:
    def double(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        return Command(goto="load_context", update=extra or {})

    return double


def test_recursion_limit_returns_graph_outcome(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    h = Harness(monkeypatch, load_context=looping_load_context())
    with caplog.at_level(logging.INFO, logger="meridian.signal"):
        out = h.run(T1)
    assert out.halt is not None
    assert out.halt.reason is HaltReason.RECURSION_LIMIT
    assert h.uow.calls == [(THREAD, DEMO_NOW)]
    assert [type(x) for x in out.reply.blocks] == [b.FailureOfferBlock]
    assert (out.reply.path, out.reply.degrade_reason) == ("degraded", "brake")
    assert (out.check_events[-1].check, out.check_events[-1].codes) == (
        "brake",
        ("recursion_limit", "run_graph"),
    )
    assert all(e.turn_id == T1 for e in out.check_events)
    signals = [r for r in caplog.records if r.name == "meridian.signal"]
    assert len(signals) == 1
    assert signals[0].__dict__["signal"]["name"] == "brake_fired"
    assert signals[0].__dict__["signal"]["cause"] == "recursion_limit"
    assert out.closed_every_open_task is False
    print("recursion outcome:", out.turn_trace.model_dump_json())


def test_two_node_parallel_timing(monkeypatch: pytest.MonkeyPatch) -> None:
    assert importlib.metadata.version("langgraph") == "1.2.16"
    h = Harness(monkeypatch, planner=sleeper("planner"), danger_classifier=sleeper("danger_classifier"))
    done: list[object] = []
    worker = threading.Thread(target=lambda: done.append(h.run(T1)))
    t0 = time.monotonic()
    worker.start()
    worker.join()
    elapsed = time.monotonic() - t0
    print(f"parallel superstep: {elapsed:.3f} s")
    assert len(done) == 1
    assert 0.95 <= elapsed < 1.6


def test_turn_context_reaches_nodes(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}
    defaults = default_doubles()

    def recording(name: str) -> _Fn:
        def double(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
            seen[name] = runtime.context
            return defaults[name](state, runtime, deps=deps)

        return double

    names = [
        "load_context",
        "gates",
        "planner",
        "danger_classifier",
        "plan_join",
        "facts",
        "responder",
        "checks",
    ]
    h = Harness(monkeypatch, **{n: recording(n) for n in names})
    from tests.graph._spine_doubles import make_ctx, make_input

    ctx = make_ctx(T1)
    graph_mod.run_graph(h.graph, make_input(T1), ctx, deps=h.deps, composer=h.composer)
    assert sorted(seen) == sorted(names)
    assert all(value is ctx for value in seen.values())


def test_intake_never_checkpointed(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    delivered: list[str] = []
    defaults = default_doubles()

    def gates(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        intake = runtime.context.intake
        if intake.code_digits is not None:
            delivered.append(intake.code_digits.get_secret_value())
        if intake.form is not None and intake.form.phone is not None:
            delivered.append(intake.form.phone.get_secret_value())
        return defaults["gates"](state, runtime, deps=deps)

    h = Harness(monkeypatch, gates=gates)
    code = Intake(
        kind="code",
        text_store="",
        code_digits=SecretStr(_CODE_SENTINEL),
        form=None,
        card_number_seen=False,
        choice=None,
    )
    form = Intake(
        kind="form",
        text_store="",
        code_digits=None,
        form=FormValues(phone=SecretStr(_PHONE_SENTINEL)),
        card_number_seen=False,
        choice=None,
    )
    with caplog.at_level(logging.DEBUG):
        outs = [h.run(T1, intake=code), h.run(T2, intake=form)]
    assert delivered == [_CODE_SENTINEL, _PHONE_SENTINEL]
    blobs = repr(h.saver.storage) + repr(h.saver.writes) + repr(h.saver.blobs)
    metadata = str([c.metadata for c in h.saver.list(h.config)])
    everything = [blobs, metadata, caplog.text, *(o.model_dump_json() for o in outs)]
    print("checked", len(blobs), "chars of checkpoint blobs and", len(metadata), "of metadata")
    for text in everything:
        assert _CODE_SENTINEL not in text
        assert _PHONE_SENTINEL not in text


def test_every_node_emits_one_span(monkeypatch: pytest.MonkeyPatch) -> None:
    h = Harness(monkeypatch)
    h.run(T1)
    print("spans:", h.sink.nodes)
    assert sorted(n for n, _, _ in h.sink.nodes) == sorted([*h.visits, "compose"])
    assert all(
        status == "ok" and isinstance(ms, int) and len(item) == 3
        for item in h.sink.nodes
        for _, ms, status in [item]
    )

    halting = Harness(
        monkeypatch,
        responder=lambda s, r, *, deps: {
            "halt": Halt(reason=HaltReason.DEADLINE, node="responder", elapsed_ms=1)
        },
    )
    halting.run(T1)
    assert ("responder",) == tuple(n for n, _, st in halting.sink.nodes if st == "halted")

    def boom(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        raise RuntimeError("boom")

    failing = Harness(monkeypatch, facts=boom)
    with pytest.raises(RuntimeError, match="boom"):
        failing.run(T1)
    assert [(n, st) for n, _, st in failing.sink.nodes if n == "facts"] == [("facts", "error")]


def test_graph_outcome_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = default_doubles()

    def gates(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        update = defaults["gates"](state, runtime, deps=deps)
        return update if runtime.context.ids.turn_id == T1 else {"gate": update["gate"]}

    def danger(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        if runtime.context.ids.turn_id != T3:
            return defaults["danger_classifier"](state, runtime, deps=deps)
        raised = DangerAssessment(label="danger", raised=True, failure=None)
        return {"danger": raised, "check_events": (CheckEvent.from_danger(T3, raised),)}

    def specialist(state: typing.Any, runtime: typing.Any, *, deps: typing.Any) -> typing.Any:
        kind = state["planned"].specialist
        made = {
            "account": AccountResult(status="read", tools=(), calls=()),
            "knowledge": KnowledgeResult(status="answered", passages=(), points=(), tools=(), calls=()),
        }
        return {"specialist_results": [made[kind]]}

    h = Harness(
        monkeypatch,
        gates=gates,
        danger_classifier=danger,
        run_specialist=specialist,
        plan_join=act_plan("account", "knowledge"),
    )
    first = h.run(T1)
    assert first.turn_trace.specialists_run == ("account", "knowledge")
    second = h.run(T2)
    kinds = {e.check for e in second.check_events}
    print("turn 2 events:", [(e.check, e.result) for e in second.check_events])
    assert "gate" not in kinds
    assert "completion" in kinds
    assert all(e.turn_id == T2 for e in second.check_events)
    assert second.turn_trace.gate_result == "clear"
    third = h.run(T3)
    assert third.turn_trace.gate_result == "danger"
    assert third.turn_trace.danger_raised is True
    assert third.reply.outcome == "safety_reply"


T3 = TurnId("3c4d5e6f-7a8b-4c9d-8e0f-2a3b4c5d6e7f")


def test_signal_and_span_carry_codes_only(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    note = StaffNote(
        kind="diagnostic_without_credit",
        record_id=typing.cast(typing.Any, "INV-100001"),
        text=_STAFF_SENTINEL,
        source_file="faq/customer_faq.md",
    )
    held = AccountResult(status="read", staff_notes=(note,), tools=(), calls=())
    h = Harness(monkeypatch, load_context=looping_load_context({"specialist_results": [held]}))
    intake = Intake(
        kind="code",
        text_store="",
        code_digits=SecretStr(_CODE_SENTINEL),
        form=None,
        card_number_seen=False,
        choice=None,
    )
    with caplog.at_level(logging.INFO, logger="meridian.signal"):
        out = h.run(T1, intake=intake)
    signals = [str(r.__dict__["signal"]) for r in caplog.records if r.name == "meridian.signal"]
    assert signals
    for text in (repr(h.sink.nodes), *signals, out.model_dump_json()):
        assert _STAFF_SENTINEL not in text
        assert _CODE_SENTINEL not in text
