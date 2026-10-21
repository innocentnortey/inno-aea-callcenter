"""SpecialistRunner tests (AEA-35 AC-1…AC-4, AC-8…AC-10, AC-13, AC-14, AC-17, AC-20). Synthetic values only."""

from __future__ import annotations

import logging

import pytest
from pydantic import JsonValue

from meridian.agent.gateway import ModelOutcome
from meridian.agent.specialists.runner import scope_for
from meridian.domain.common import (
    CustomerId,
    Halt,
    HaltReason,
    ProviderFailure,
    ProviderFailureKind,
    ToolErrorCode,
)
from meridian.domain.identity import IdentityState
from meridian.domain.specialists import (
    AccountCapture,
    AccountResult,
    KnowledgeResult,
    SchedulingCapture,
    SchedulingResult,
)
from meridian.domain.state import ConversationState
from meridian.domain.tools import ToolKind
from meridian.domain.turn import TaskIntent, TurnInput
from meridian.ports.models import CallRecord, Role, ToolCall, ToolSchema, ToolStep
from tests.fakes import WORKED_PAIRS_NOW, FakeToolModel, InMemoryTraceSink, provider_call
from tests.unit.agent.specialists._doubles import (
    FAQ_CREDIT,
    INV_204411,
    SLOT_44,
    SLOT_61,
    STAFF_NOTE,
    THREAD,
    TROUBLESHOOTING,
    TURN_1,
    TURN_2,
    WP1_INCLUDES,
    WP1_MINIMUM,
    WP1_PRICE,
    ScriptedDispatcher,
    ScriptedGateway,
    dispatched,
    failed_dispatched,
    kb_dispatched,
    make_runner,
    make_task,
    refused_dispatched,
    report_call,
    scope,
    step,
    tool_call,
    turn_ctx,
)

_KB_SCHEMA = ToolSchema(name="kb_search", description="search", input_schema={"type": "object"})
_WP1_ALL = [WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM]
_COMFORT = "membership/comfort_club_overview.md#0"
_EMPTY_REPORT = {"points": [], "answered": False}


def _kb_task(text: str = "What does the Comfort Club membership actually include?", **kw):
    return make_task("knowledge", TaskIntent.ANSWER_QUESTION, text, **kw)


def test_two_tool_rounds_brake() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "kb_search", query="a")),
            step(tool_call("c2", "kb_search", query="b")),
            step(tool_call("c3", "kb_search", query="c")),
        ]
    )
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: kb_dispatched(c, ctx, [WP1_INCLUDES]))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert len(dispatcher.batches) == 2
    assert "c3" not in [c.id for c in dispatcher.dispatched_calls]
    assert result.brake == HaltReason.BRAKE_TOOL_ROUNDS
    assert str(result.brake) == "brake_tool_rounds"
    assert len(model.requests) == 3


@pytest.mark.parametrize(
    "script",
    [
        [
            step(tool_call("c1", "kb_search", query="same")),
            step(tool_call("c2", "kb_search", query="same")),
        ],
        [
            step(
                tool_call("c1", "x_tool", a=1, b=2),
                ToolCall(id="c2", name="x_tool", args={"b": 2, "a": 1}),
            )
        ],
    ],
    ids=["across_rounds", "within_step"],
)
def test_identical_call_breaker(script: list[ToolStep]) -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(script)
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: kb_dispatched(c, ctx, [WP1_INCLUDES]))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert [c.id for c in dispatcher.dispatched_calls] == ["c1"]
    assert result.brake == HaltReason.BRAKE_IDENTICAL_CALL
    if len(script) == 2:
        assert len(model.requests) == 2


def test_final_answer_branch() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel([step(text="Nothing to look up.")])
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: kb_dispatched(c, ctx, []))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert dispatcher.batches == []
    assert len(model.requests) == 1
    assert result.status == "no_current_source"
    assert result.brake is None
    assert result.failure is None


def test_report_facts_ends_loop_not_dispatched() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "kb_search", query="comfort club")),
            step(
                report_call(
                    "r1",
                    points=[{"text": "Two tune-ups a year.", "passage_id": _COMFORT}],
                    answered=True,
                )
            ),
        ]
    )
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(
            lambda c: kb_dispatched(c, ctx, [WP1_INCLUDES]), schemas=(_KB_SCHEMA,)
        )
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert "report_facts" not in [c.name for c in dispatcher.dispatched_calls]
    assert len(dispatcher.batches) == 1
    assert len(model.requests) == 2
    assert result.status == "answered"
    names = [t.name for t in model.requests[0].tools]
    assert names[-1] == "report_facts"
    assert names[:-1] == [s.name for s in dispatcher.schemas(frozenset({ToolKind.KB_SEARCH}))]


def test_invalid_report_is_ignored() -> None:
    sink = InMemoryTraceSink()
    bad_points: list[JsonValue] = [{"text": "x", "passage_id": _COMFORT}] * 6
    model = FakeToolModel(
        [
            step(tool_call("c1", "kb_search", query="comfort club")),
            step(report_call("r1", points=bad_points, answered=True)),
        ]
    )
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: kb_dispatched(c, ctx, [WP1_INCLUDES]))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert isinstance(result, KnowledgeResult)
    assert result.status == "no_current_source"
    assert result.points == ()
    assert len(model.requests) == 2


def test_results_keep_tool_call_ids() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "kb_search", query="a"), tool_call("c2", "kb_search", query="b")),
            step(tool_call("c3", "kb_search", query="c")),
            step(report_call("r1", points=[], answered=False)),
        ]
    )
    contents: dict[str, str] = {}
    with turn_ctx(sink) as ctx:

        def handler(call: ToolCall):
            d = kb_dispatched(call, ctx, [WP1_INCLUDES])
            contents[call.id] = d.content
            return d

        dispatcher = ScriptedDispatcher(handler)
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        runner.run(_kb_task(), scope(ctx), ctx)
    assert [r for r, _ in model.appends[0][2]] == ["c1", "c2"]
    assert [r for r, _ in model.appends[1][2]] == ["c3"]
    for _, _, results in model.appends:
        for call_id, content in results:
            assert content == contents[call_id]
    assert len(model.appends) == 2


def test_message_list_is_per_run() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [step(report_call("r1", **_EMPTY_REPORT)), step(report_call("r2", **_EMPTY_REPORT))]  # type: ignore[arg-type]
    )
    dispatcher = ScriptedDispatcher(lambda c: pytest.fail("no dispatch expected"))
    runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
    with turn_ctx(sink, turn_id=TURN_1) as ctx:
        runner.run(_kb_task("What does the Comfort Club membership actually include?"), scope(ctx), ctx)
    with turn_ctx(sink, turn_id=TURN_2) as ctx:
        runner.run(_kb_task("And how much is it?"), scope(ctx), ctx)
    assert len(model.starts) == 2
    assert "And how much is it?" in model.starts[1]
    assert "actually include" not in model.starts[1]
    assert model.requests[1].messages.items == ({"role": "user", "content": model.starts[1]},)


def test_never_raises_on_failure() -> None:
    sink = InMemoryTraceSink()
    failure = ProviderFailure(
        kind=ProviderFailureKind.SERVER,
        provider="anthropic",
        http_status=503,
        retry_after_s=None,
        retryable=True,
        provider_request_id=None,
    )
    recs = tuple(
        CallRecord.from_provider(
            provider_call(provider="anthropic", model="claude-sonnet-5-5", failure=failure),
            role=Role.SPECIALIST,
            attempt=a,
        )
        for a in (1, 2)
    )
    outcome = ModelOutcome[ToolStep](value=None, calls=recs, failure=failure, halt=None)
    model = FakeToolModel([])
    gateway = ScriptedGateway(outcomes=[outcome])
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: pytest.fail("no dispatch expected"))
        runner = make_runner(gateway, model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert result.status == "failed"
    assert result.failure is not None
    assert result.failure.kind == ProviderFailureKind.SERVER
    assert len(result.calls) == 2
    assert len(gateway.requests) == 1
    assert dispatcher.batches == []


@pytest.mark.parametrize(
    "reason",
    [HaltReason.DEADLINE, HaltReason.BRAKE_SONNET_CALLS, HaltReason.PROVIDER_SPEND_CAP],
    ids=lambda r: r.value,
)
def test_gateway_halt_stops_run(reason: HaltReason) -> None:
    sink = InMemoryTraceSink()
    outcome = ModelOutcome[ToolStep](
        value=None, calls=(), failure=None, halt=Halt(reason=reason, node="specialist", elapsed_ms=0)
    )
    model = FakeToolModel([])
    gateway = ScriptedGateway(outcomes=[outcome])
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: pytest.fail("no dispatch expected"))
        runner = make_runner(gateway, model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert result.brake == reason
    assert len(gateway.requests) == 1
    assert dispatcher.batches == []


def test_tool_failed_content_reaches_model() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "kb_search", query="a")),
            step(report_call("r1", points=[], answered=False)),
        ]
    )
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(lambda c: failed_dispatched(c, ctx, kind=ToolKind.KB_SEARCH))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(_kb_task(), scope(ctx), ctx)
    assert '"tool_failed"' in model.appends[0][2][0][1]
    assert len(model.requests) == 2
    assert result.tools[0].outcome == "failed"
    assert result.brake is None


def _scheduling_handler(ctx, troubleshooting_below_floor: bool = False):
    def handler(call: ToolCall):
        if call.name == "kb_search":
            return kb_dispatched(
                call, ctx, [TROUBLESHOOTING, FAQ_CREDIT], below_floor=troubleshooting_below_floor
            )
        if call.name == "find_windows":
            return dispatched(
                call,
                ctx,
                kind=ToolKind.SLOT_SEARCH,
                for_model={"windows": [44, 61]},
                captured=SchedulingCapture(windows=(SLOT_44, SLOT_61)),
            )
        return refused_dispatched(call, ctx, ToolErrorCode.UNKNOWN_TOOL, kind=None)

    return handler


@pytest.mark.parametrize("case", ["offer", "no_offer", "below_floor"])
def test_quick_checks_offer(case: str) -> None:
    sink = InMemoryTraceSink()
    text = "My AC stopped cooling, can someone come out? " * 10
    assert len(text) > 300
    model = FakeToolModel(
        [
            step(tool_call("c1", "find_windows", service_type="hvac_repair")),
            step(tool_call("c2", "find_windows", service_type="hvac_repair", day="monday")),
            step(report_call("r1", appointment_id=0, wanted_time="", note="windows shown")),
        ]
    )
    task = make_task("scheduling", TaskIntent.BOOK_NEW, text, offer_quick_checks=case != "no_offer")
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(_scheduling_handler(ctx, case == "below_floor"))
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        sc = scope(ctx)
        result = runner.run(task, sc, ctx)
    assert isinstance(result, SchedulingResult)
    assert result.brake is None
    if case == "offer":
        qc = ToolCall(id=f"qc-{TURN_1}", name="kb_search", args={"query": text[:300]})
        assert dispatcher.batches[0] == ((qc,), frozenset({ToolKind.KB_SEARCH}), sc)
        assert len(dispatcher.batches) == 3
        assert result.quick_checks == (TROUBLESHOOTING,)
        assert result.status == "windows_shown"
        assert all(not r.startswith("qc-") for _, _, results in model.appends for r, _ in results)
    elif case == "no_offer":
        assert not any(c.id.startswith("qc-") for c in dispatcher.dispatched_calls)
        assert result.quick_checks == ()
    else:
        assert result.quick_checks == ()


@pytest.mark.parametrize(
    ("status", "customer"),
    [
        ("not_checked", None),
        ("located", "MHC-10002"),
        ("code_sent", "MHC-10002"),
        ("verified", "MHC-10002"),
        ("not_verified", "MHC-10002"),
        ("locked", "MHC-10002"),
    ],
)
def test_scope_for(status: str, customer: str | None) -> None:
    state = ConversationState(
        thread_id=THREAD,
        turn_input=TurnInput(
            turn_id=TURN_1,
            message_id=412,
            kind="text",
            text_store="Can I move it?",
            received_at=WORKED_PAIRS_NOW,
        ),
        identity=IdentityState.model_validate(
            {
                "status": status,
                "customer_id": customer,
                "masked_hint": None,
                "code_expires_at": None,
                "tries_left": 3,
                "codes_sent": 1,
                "verified_at": None,
            }
        ),
        shown_slots=[SLOT_44, SLOT_61],
    )
    sink = InMemoryTraceSink()
    with turn_ctx(sink) as ctx:
        sc = scope_for(state, ctx)
    expected = CustomerId("MHC-10002") if status == "verified" else None
    assert sc.customer_id == expected
    assert sc.shown_slot_ids == frozenset({44, 61})
    assert sc.now is ctx.now
    assert sc.ids == ctx.ids
    assert sc.message_id == 412


def test_no_staff_notes_transcript_or_scope_leak(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    sink = InMemoryTraceSink()
    text = "I got an invoice and I'm not sure what it's for."
    model = FakeToolModel(
        [
            step(tool_call("c1", "read_invoices")),
            step(report_call("r1", summary="One unpaid invoice.")),
        ]
    )
    task = make_task("account", TaskIntent.READ_INVOICE, text)
    gateway = ScriptedGateway(model)
    with turn_ctx(sink) as ctx:

        def handler(call: ToolCall):
            return dispatched(
                call,
                ctx,
                kind=ToolKind.ACCOUNT_READ,
                for_model={"invoices": [INV_204411.model_dump(mode="json")]},
                captured=AccountCapture(invoices=(INV_204411,), staff_notes=(STAFF_NOTE,)),
                record_ids=("INV-204411",),
            )

        dispatcher = ScriptedDispatcher(handler)
        runner = make_runner(gateway, model, dispatcher, sink)
        result = runner.run(task, scope(ctx, customer_id=CustomerId("MHC-10002")), ctx)
    for req in gateway.requests:
        dump = req.model_dump_json()
        assert STAFF_NOTE.text not in dump
        assert "MHC-10002" not in dump
    for r in caplog.records:
        for secret in (STAFF_NOTE.text, "MHC-10002", text):
            assert secret not in r.getMessage()
            assert secret not in str(r.__dict__)
    dump = result.model_dump_json()
    assert '"items"' not in dump
    assert '"for_model"' not in dump
    assert '"speaker"' not in dump
    assert "MHC-10002" not in dump
    assert isinstance(result, AccountResult)
    assert result.staff_notes == (STAFF_NOTE,)
    assert result.status == "read"
    assert caplog.records == []


def test_lookup_and_call_records() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "find_windows", service_type="hvac_repair"), tool_call("c2", "x_read")),
            step(tool_call("c3", "find_windows", service_type="hvac_repair", day="monday")),
            step(report_call("r1", appointment_id=0, wanted_time="", note="n")),
        ]
    )
    task = make_task("scheduling", TaskIntent.BOOK_NEW, "My AC is broken", offer_quick_checks=True)
    with turn_ctx(sink) as ctx:
        dispatcher = ScriptedDispatcher(_scheduling_handler(ctx))
        runner = make_runner(ScriptedGateway(model, retried_steps=frozenset({0})), model, dispatcher, sink)
        result = runner.run(task, scope(ctx), ctx)
    assert len(dispatcher.dispatched_calls) == 4
    assert len(result.tools) == 4
    assert [t.tool_call_id for t in result.tools] == [c.id for c in dispatcher.dispatched_calls]
    assert len(result.calls) == 4
    assert [c.attempt for c in result.calls][:2] == [1, 2]


def test_tool_spans() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(
                tool_call("c1", "find_windows", service_type="hvac_repair"),
                tool_call("c2", "made_up_tool", x=1),
            ),
            step(tool_call("c3", "find_windows", wanted="SENTINEL-ARG-7731")),
            step(report_call("r1", appointment_id=0, wanted_time="", note="n")),
        ]
    )
    task = make_task("scheduling", TaskIntent.BOOK_NEW, "My AC is broken", offer_quick_checks=True)
    with turn_ctx(sink) as ctx:
        base = _scheduling_handler(ctx)

        def handler(call: ToolCall):
            if call.name == "made_up_tool":
                return refused_dispatched(call, ctx, ToolErrorCode.UNKNOWN_TOOL, kind=None)
            return base(call)

        dispatcher = ScriptedDispatcher(handler)
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(task, scope(ctx), ctx)
        nodes = sink.spans_for(ctx.span).nodes
    assert [n.name for n in nodes] == [
        "tool:kb_search",
        "tool:find_windows",
        "tool:unknown",
        "tool:find_windows",
    ]
    for n, r in zip(nodes, result.tools, strict=True):
        assert n.elapsed_ms == r.elapsed_ms
        assert n.status == r.outcome
    for n in nodes:
        for banned in ("made_up_tool", "report_facts", "SENTINEL-ARG-7731"):
            assert banned not in n.name
            assert banned not in n.status
    assert len(nodes) == len(result.tools) == 4
