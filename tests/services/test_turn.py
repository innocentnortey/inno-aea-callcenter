"""AEA-40 Part A: `TurnService` (CON-2 behind the route) on a temp working copy, with every sibling doubled.

Acceptance criteria covered: AC-3, 4, 5, 7, 8, 10, 11, 12, 13, 20, 21 and the plan-added PA-2, PA-3, PA-4.
Each test names its failure mode: invariant, failure/refusal, negative, boundary or regression.
No model, no network, no socket. The code, card number and phone number are built from a seeded generator.
"""

from __future__ import annotations

import datetime as dt
import inspect
import json
import logging
import threading
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

import meridian.services.turn as turn_module
from meridian.adapters.sqlite.rows import case_stream
from meridian.domain.staff import CUSTOMER_SPEAKER_NAME
from meridian.domain.turn import TurnInput
from meridian.policy.limits import Limits
from meridian.services.turn import (
    LOG_RECORD_ATTR,
    TURN_IN_PROGRESS_RETRY_MS,
    ThreadNotOpen,
    TurnInProgress,
    next_outcome,
    reopened_outcome,
)
from meridian.web.container import Container, Key, register_chat, register_web
from meridian.web.deps import TURN_SERVICE
from meridian.web.logging import RECORD_ATTR
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.openapi_check import SseFrame, assert_sse_frames_match
from tests.api.web_shell_support import make_settings
from tests.fakes import WORKED_PAIRS_NOW, FixedClock, InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.chat_doubles import (
    WALL_NOW,
    BlockingRunGraph,
    DeadlineRunGraph,
    FakeComposer,
    FakeSpendGuard,
    RaisingRunGraph,
    ScriptedRunGraph,
    answered_outcome,
    code_payload,
    degraded_outcome,
    handed_off_outcome,
    locate_form_payload,
    make_cmd,
    make_turn_service,
    new_request_id,
    new_thread_id,
    new_turn_id,
    synthetic,
    text_payload,
)
from tests.services.chat_hooks import HookedUow, fail_after, fail_first_call
from tests.services.chat_storage import (
    Collected,
    conversation,
    count_rows,
    customer_messages,
    has_person_key,
    human_controller,
    log_blob,
    messages_of,
    notice_codes,
    raw_value,
    records_of_kind,
    seed_thread,
    text_dump,
    turn_ids_of,
    turn_row,
)


# -- AC-3: idempotent turn_id ------------------------------------------------------------------------------------
def test_same_turn_id_returns_stored() -> None:
    """invariant (AC-3): a completed turn resent returns the stored response, run_graph called once in total."""
    with temp_sqlite() as store:
        graph = ScriptedRunGraph()
        service = make_turn_service(store, run_graph=graph)
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("I got an invoice and I am not sure what it is for."))

        first = service.run_turn(cmd)
        again = service.run_turn(cmd.model_copy(update={"request_id": new_request_id()}))

        assert len(graph.calls) == 1
        assert again == first
        assert again.model_dump_json() == first.model_dump_json()
        stored = turn_row(store, cmd.turn_id)
        assert stored.status == "completed"
        assert json.loads(stored.response) == json.loads(first.model_dump_json())
        assert len(customer_messages(store, thread, cmd.turn_id)) == 1
        assert first.notice is None


def test_running_turn_409() -> None:
    """invariant (AC-3): a resend while the turn runs is refused (TURN_IN_PROGRESS, retry 2000 ms); nothing runs."""
    assert TURN_IN_PROGRESS_RETRY_MS == 2000
    with temp_sqlite() as store:
        graph = ScriptedRunGraph()
        service = make_turn_service(store, run_graph=graph)
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("hello"))
        with store.uow(write=True) as tx:
            assert tx.core.turns.begin(turn_ids_of(cmd), WORKED_PAIRS_NOW).status == "new"
            tx.commit()

        with pytest.raises(TurnInProgress) as excinfo:
            service.run_turn(cmd)

        assert excinfo.value.retry_after_ms == 2000
        assert graph.calls == []
        assert turn_row(store, cmd.turn_id).status == "running"
        assert customer_messages(store, thread) == []


def test_failed_turn_reruns() -> None:
    """invariant (AC-3, PA-2): a failed turn re-runs on the same turn_id and does not duplicate the customer line."""
    with temp_sqlite() as store:
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("hello again"))
        broken = RaisingRunGraph()
        make_turn_service(store, run_graph=broken).run_turn(cmd)
        assert turn_row(store, cmd.turn_id).status == "failed"

        graph = ScriptedRunGraph()
        second = make_turn_service(store, run_graph=graph).run_turn(cmd)

        assert broken.calls == 1
        assert len(graph.calls) == 1
        assert turn_row(store, cmd.turn_id).status == "completed"
        assert second.model_dump_json() == turn_row(store, cmd.turn_id).response
        assert (
            len(customer_messages(store, thread, cmd.turn_id)) == 1
        )  # PA-2: one customer row for the turn_id
        assert graph.calls[0].turn_input.message_id == customer_messages(store, thread, cmd.turn_id)[0].id


def test_timed_out_turn_reruns() -> None:
    """invariant (AC-3): a timed-out turn also re-runs on the same turn_id."""
    with temp_sqlite() as store:
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("book me in"))
        timed_out = make_turn_service(store, run_graph=DeadlineRunGraph(store.uow)).run_turn(cmd)
        assert timed_out.notice is not None and timed_out.notice.code == "TURN_TIMEOUT"
        assert turn_row(store, cmd.turn_id).status == "failed"

        graph = ScriptedRunGraph()
        make_turn_service(store, run_graph=graph).run_turn(cmd)

        assert len(graph.calls) == 1
        assert turn_row(store, cmd.turn_id).status == "completed"
        assert len(customer_messages(store, thread, cmd.turn_id)) == 1


# -- AC-4: admission ---------------------------------------------------------------------------------------------
def test_admission_31st_turn_busy() -> None:
    """failure/refusal (AC-4): with 30 turns in flight a 31st gets BUSY with the person key and no model call."""
    assert Limits().admission.max_in_flight == 30
    with temp_sqlite() as store:
        blocking = BlockingRunGraph()
        service = make_turn_service(store, run_graph=blocking)
        threads = [seed_thread(store.uow) for _ in range(31)]
        collected = Collected()
        workers: list[threading.Thread] = []
        for thread in threads[:30]:
            cmd = make_cmd(thread, text_payload("hello"))
            worker = threading.Thread(target=collected.run, args=(lambda c=cmd: service.run_turn(c),))
            worker.start()
            workers.append(worker)
        try:
            for _ in range(30):
                assert blocking.entered.acquire(timeout=10), "30 turns never reached the graph"

            cmd31 = make_cmd(threads[30], text_payload("one more please"))
            busy = service.run_turn(cmd31)

            assert busy.notice is not None
            assert busy.notice.code == "BUSY"
            assert busy.notice.actions == ("talk_to_person",)
            assert notice_codes(busy.blocks) == ["BUSY"]
            assert has_person_key(busy.blocks)
            assert blocking.calls == 30  # no model call for the 31st
            row = turn_row(store, cmd31.turn_id)
            assert (row.gate_result, row.path, row.outcome, row.degrade_reason) == (
                "clear",
                "degraded",
                "degraded_handoff",
                "rate_limit",
            )
        finally:
            blocking.release.set()
            for worker in workers:
                worker.join(timeout=10)

        assert not collected.errors
        assert len(collected.results) == 30
        assert all(r.notice is None for r in collected.results)
        after = service.run_turn(make_cmd(threads[30], text_payload("again")))  # a slot is always given back
        assert after.notice is None


# -- AC-5: spend cap ---------------------------------------------------------------------------------------------
def test_spend_cap_notice_no_model() -> None:
    """failure/refusal (AC-5): allow_turn() false gives SPEND_CAP_REACHED with the person key and no graph call."""
    with temp_sqlite() as store:
        graph = ScriptedRunGraph()
        guard = FakeSpendGuard(allow=False)
        service = make_turn_service(store, run_graph=graph, spend=guard)
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("what does this invoice line mean?"))

        result = service.run_turn(cmd)

        assert result.notice is not None
        assert result.notice.code == "SPEND_CAP_REACHED"
        assert "talk_to_person" in result.notice.actions
        assert notice_codes(result.blocks) == ["SPEND_CAP_REACHED"]
        assert has_person_key(result.blocks)
        assert guard.calls >= 1
        assert graph.calls == []
        row = turn_row(store, cmd.turn_id)
        assert (row.outcome, row.degrade_reason) == ("degraded_handoff", "spend_cap")
        assert (
            customer_messages(store, thread) == []
        )  # nothing from the customer is stored when no model runs

        guard.allow = True  # the cap lifts: the same turn_id runs (the rejected row is `failed`, not stuck)
        service.run_turn(cmd)
        assert len(graph.calls) == 1


# -- AC-7: deadline and graph failure ----------------------------------------------------------------------------
def test_deadline_turn_timeout_notice() -> None:
    """failure/refusal (AC-7): a DEADLINE halt gives TURN_TIMEOUT (try again + person), settled keeps the earlier write."""
    with temp_sqlite() as store:
        graph = DeadlineRunGraph(store.uow)
        service = make_turn_service(store, run_graph=graph, monotonic=lambda: 1000.0)
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("book the tune-up"))

        result = service.run_turn(cmd)

        budget = graph.calls[0].context.budget
        assert (budget.started, budget.deadline) == (1000.0, 1060.0)  # 60 s from server receipt (SDQ-1)
        assert result.notice is not None
        assert result.notice.code == "TURN_TIMEOUT"
        assert result.notice.actions == ("try_again", "talk_to_person")
        assert result.notice.retry_turn_id == str(cmd.turn_id)
        assert "TURN_TIMEOUT" in notice_codes(result.blocks)
        assert [w.kind for w in result.settled.actions] == [
            "booked"
        ]  # committed earlier in the turn, still shown
        row = turn_row(store, cmd.turn_id)
        assert (row.status, row.outcome, row.degrade_reason) == ("failed", "degraded_handoff", "timeout")


def test_graph_exception_degraded_not_500(caplog: pytest.LogCaptureFixture) -> None:
    """failure/refusal (AC-7): a run_graph that raises returns a person offer and a degraded row, never an exception."""
    caplog.set_level(logging.DEBUG)
    with temp_sqlite() as store:
        graph = RaisingRunGraph()
        service = make_turn_service(store, run_graph=graph)
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("hello"))

        result = service.run_turn(cmd)  # must not raise

        assert graph.calls == 1
        assert has_person_key(result.blocks)
        row = turn_row(store, cmd.turn_id)
        assert (row.status, row.outcome) == ("failed", "degraded_handoff")
        assert RaisingRunGraph.MARKER not in log_blob(caplog)  # the exception text is never logged
        assert RaisingRunGraph.MARKER not in text_dump(store)


# -- AC-8: intake redaction and the carrier ----------------------------------------------------------------------
def test_intake_redacted_and_never_in_turn_input(caplog: pytest.LogCaptureFixture) -> None:
    """negative (AC-8): stored text is redacted; TurnInput holds no code, card or form value; the intake does."""
    caplog.set_level(logging.DEBUG)
    syn = synthetic()
    caller_name = "Zqname Testperson"
    with temp_sqlite() as store:
        graph = ScriptedRunGraph()
        service = make_turn_service(store, run_graph=graph)
        thread = seed_thread(store.uow)

        code_cmd = make_cmd(thread, code_payload(syn.code))
        card_cmd = make_cmd(thread, text_payload(f"my card is {syn.card} please"))
        form_cmd = make_cmd(thread, locate_form_payload(caller_name, syn.phone))
        for cmd in (code_cmd, card_cmd, form_cmd):
            service.run_turn(cmd)

        assert len(graph.calls) == 3
        code_call, card_call, form_call = graph.calls
        stored = {m.turn_id: m for m in customer_messages(store, thread)}

        # a code turn stores "[code entered]"; the digits travel only in TurnContext.intake as a SecretStr
        assert stored[code_cmd.turn_id].text == "[code entered]"
        assert code_call.turn_input.text_store == "[code entered]"
        assert code_call.turn_input.kind == "code"
        assert code_call.turn_input.message_id == stored[code_cmd.turn_id].id
        intake = code_call.context.intake
        assert intake is not None
        assert isinstance(intake.code_digits, SecretStr)
        assert intake.code_digits.get_secret_value() == syn.code

        # a card number in free text is stored as "[card number removed]"
        assert stored[card_cmd.turn_id].text == "my card is [card number removed] please"
        assert card_call.turn_input.text_store == "my card is [card number removed] please"
        assert card_call.turn_input.card_number_seen is True
        assert card_call.turn_input.message_id == stored[card_cmd.turn_id].id

        # a locate form stores "[details submitted]"; the values travel only in TurnContext.intake
        assert stored[form_cmd.turn_id].text == "[details submitted]"
        assert form_call.turn_input.text_store == "[details submitted]"
        assert form_call.turn_input.kind == "form"
        form_intake = form_call.context.intake
        assert form_intake is not None and form_intake.form is not None
        assert isinstance(form_intake.form.phone, SecretStr)
        assert form_intake.form.phone.get_secret_value() == syn.phone

        # nowhere else: not in the recorded TurnInput, the rows, the working-copy files or any log record
        recorded = "\n".join(c.input_json + repr(c.turn_input) for c in graph.calls)
        everything = {
            "recorded TurnInput": recorded,
            "stored rows": text_dump(store),
            "log capture": log_blob(caplog),
        }
        for label, haystack in everything.items():
            for needle in (*syn.needles(), caller_name):
                assert needle not in haystack, f"{label} holds a value that must never be stored"


# -- AC-10: one context per turn, no growing input ---------------------------------------------------------------
def test_turn_context_and_inputs_turns_1_2_5() -> None:
    """invariant (AC-10): one clock reading, one span and a 60 s budget per turn; inputs hold no message list."""
    with temp_sqlite() as store:
        graph = ScriptedRunGraph()
        sink = InMemoryTraceSink()
        service = make_turn_service(store, run_graph=graph, trace=sink, monotonic=lambda: 1000.0)
        thread = seed_thread(store.uow)
        texts = [f"message number {n} about my furnace" for n in range(1, 6)]
        for text in texts:
            service.run_turn(make_cmd(thread, text_payload(text)))

        assert len(graph.calls) == 5
        key_sets = [set(json.loads(c.input_json)) for c in graph.calls]
        assert key_sets[0] == key_sets[1] == key_sets[4] == set(TurnInput.model_fields)
        for keys in key_sets:
            assert not keys & {"messages", "message_history", "history", "recent_chat", "window", "summary"}
        for index in (0, 1, 4):
            call = graph.calls[index]
            assert call.turn_input.text_store == texts[index]
            assert (
                call.context.now == call.turn_input.received_at
            )  # one demo-clock reading, handed to the graph
            assert call.context.now == WORKED_PAIRS_NOW
            assert (call.context.budget.started, call.context.budget.deadline) == (1000.0, 1060.0)
            assert sink.spans_for(call.context.span).closed is True  # the span came from trace.turn(ids)
            assert call.context.span.turn_id == call.turn_input.turn_id
            assert call.context.ids.thread_id == thread
        assert len(sink.turns) == 5
        assert len({c.context.span.trace_id for c in graph.calls}) == 5
        # TurnService reads only GraphOutcome, never ConversationState
        assert "ConversationState" not in inspect.getsource(turn_module)


# -- AC-11 and AC-20: customer message side effects --------------------------------------------------------------
def test_customer_message_event_same_commit_when_human() -> None:
    """invariant (AC-11): last_customer_wall_at in UTC; the CON-21 event commits with the message or not at all."""
    with temp_sqlite() as store:
        controller = human_controller()
        assert controller.case_ref is not None
        stream = case_stream(controller.case_ref)
        thread = seed_thread(store.uow, controller=controller)
        ai_thread = seed_thread(store.uow)
        service = make_turn_service(store, wall=lambda: WALL_NOW)

        cmd = make_cmd(thread, text_payload("are you still there?"))
        service.run_turn(cmd)
        service.run_turn(make_cmd(ai_thread, text_payload("hello")))

        message = customer_messages(store, thread, cmd.turn_id)[0]
        with store.uow() as tx:
            events = tx.core.events.after(stream, 0)
        assert [e.type for e in events] == ["customer_message"]
        assert raw_value(
            store, "SELECT last_customer_wall_at FROM conversations WHERE thread_id = ?", (str(thread),)
        ) == ("2026-10-21T15:30:00+00:00")
        assert cast(dict[str, Any], events[0].payload["message"])["message_id"] == str(message.id)
        # an AI-controlled thread writes the timestamp but no case event
        assert raw_value(
            store, "SELECT last_customer_wall_at FROM conversations WHERE thread_id = ?", (str(ai_thread),)
        ).endswith("+00:00")
        assert count_rows(store, "events", "stream LIKE 'case:%'") == 1

        # a fault injected after the event write rolls back the message, the event and the turn row together
        faulty = HookedUow(store.uow, {"events.append": fail_after("injected after the event write")})
        broken = make_turn_service(store, uow=faulty, wall=lambda: WALL_NOW)
        bad = make_cmd(thread, text_payload("this one must vanish"))
        with pytest.raises(RuntimeError, match="injected after the event write"):
            broken.run_turn(bad)
        assert customer_messages(store, thread, bad.turn_id) == []
        assert count_rows(store, "events", "stream LIKE 'case:%'") == 1  # still only the first event
        assert turn_row(store, bad.turn_id) is None


def test_customer_message_payload_valid_and_unnamed() -> None:
    """invariant (AC-20): the relayed customer_message is a valid CaseEvent, redacted, speaker 'Customer'."""
    syn = synthetic()
    assert CUSTOMER_SPEAKER_NAME == "Customer"
    with temp_sqlite() as store:
        controller = human_controller()
        assert controller.case_ref is not None
        thread = seed_thread(store.uow, controller=controller)
        service = make_turn_service(store, wall=lambda: WALL_NOW)
        cmd = make_cmd(thread, text_payload(f"my card is {syn.card} ok"))

        service.run_turn(cmd)

        message = customer_messages(store, thread, cmd.turn_id)[0]
        with store.uow() as tx:
            rows = tx.core.events.after(case_stream(controller.case_ref), 0)
        assert len(rows) == 1
        row = rows[0]
        data = {"event_id": row.id, "type": row.type, "at": row.at.isoformat(), **row.payload}
        assert_sse_frames_match(
            [SseFrame(event="customer_message", id=str(row.id), data=json.dumps(data))], "streamCaseEvents"
        )
        line = data["message"]
        assert isinstance(line, dict)
        assert line["speaker"] == {"kind": "customer", "display_name": CUSTOMER_SPEAKER_NAME}
        assert line["text"] == "my card is [card number removed] ok"
        assert line["message_id"] == str(message.id)
        assert dt.datetime.fromisoformat(str(line["at"])) == message.at
        wire = json.dumps(data)
        assert "You" not in wire.replace("Your", "")
        for needle in syn.needles():
            assert needle not in wire


# -- AC-12: restart sweep ----------------------------------------------------------------------------------------
def _chat_container(
    store: TempStore, tmp_path: Path, graph: ScriptedRunGraph, *, spend: FakeSpendGuard | None = None
) -> Container:
    """A container running register_web and register_chat only, with the siblings bound as doubles."""
    settings = make_settings(tmp_path)
    limits = Limits()
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=settings, wall_clock=lambda: WALL_NOW, public_paths=PublicPaths()
    )
    container = Container(settings=settings, limits=limits)
    container.provide(Key[Any]("uow_factory"), lambda _c: store.uow)
    container.provide(Key[Any]("ledger"), lambda _c: spend or FakeSpendGuard(True))
    container.provide(Key[Any]("trace"), lambda _c: InMemoryTraceSink())
    container.provide(Key[Any]("demo_clock"), lambda _c: FixedClock())
    container.provide(Key[Any]("run_graph"), lambda _c: graph)
    container.provide(Key[Any]("reply_composer"), lambda _c: FakeComposer())
    register_web(container, app, settings=settings, limits=limits)
    register_chat(container, app, settings=settings, limits=limits)
    return container


def test_restart_sweep_fails_every_running_turn(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """invariant (AC-12): at container start every running turn becomes failed/degraded_handoff/timeout."""
    caplog.set_level(logging.INFO)
    with temp_sqlite() as store:
        thread = seed_thread(store.uow)
        old = make_cmd(thread, text_payload("sixty-six seconds ago"))
        recent = make_cmd(thread, text_payload("ten seconds ago"))
        done = make_cmd(thread, text_payload("already answered"))
        finished = make_turn_service(store).run_turn(done)
        before = turn_row(store, done.turn_id)
        with store.uow(write=True) as tx:
            tx.core.turns.begin(turn_ids_of(old), WORKED_PAIRS_NOW - dt.timedelta(seconds=66))
            tx.core.turns.begin(turn_ids_of(recent), WORKED_PAIRS_NOW - dt.timedelta(seconds=10))
            tx.commit()
        assert turn_row(store, old.turn_id).status == "running"

        graph = ScriptedRunGraph()
        container = _chat_container(store, tmp_path, graph)
        try:
            container.build()  # the sweep runs once, before the first request

            for cmd in (old, recent):
                row = turn_row(store, cmd.turn_id)
                assert (row.status, row.path, row.outcome, row.degrade_reason) == (
                    "failed",
                    "degraded",
                    "degraded_handoff",
                    "timeout",
                )
            after = turn_row(store, done.turn_id)
            assert after.status == "completed" and after == before  # a completed row is untouched
            assert json.loads(after.response) == json.loads(finished.model_dump_json())
            sweeps = records_of_kind(caplog, "turn_sweep")
            assert len(sweeps) == 1 and sweeps[0]["count"] == 2

            service = container.get(TURN_SERVICE)
            result = service.run_turn(old)  # resending a swept turn_id runs the graph
            assert len(graph.calls) == 1
            assert turn_row(store, old.turn_id).status == "completed"
            assert result.notice is None
        finally:
            container.close()


# -- AC-13: no transaction open across the graph -----------------------------------------------------------------
def test_no_uow_open_during_run_graph() -> None:
    """invariant (AC-13): no unit of work is open (or entered) while run_graph runs (DO-3 section 2.3 rule 1)."""
    with temp_sqlite() as store:
        guarded = HookedUow(store.uow)
        state = {"in_graph": False}
        guarded.forbidden_while = lambda: state["in_graph"]
        depths: list[int] = []

        def graph(turn_input: TurnInput, context: Any) -> Any:
            state["in_graph"] = True
            try:
                depths.append(guarded.depth)
                return answered_outcome(turn_input.turn_id, context.now)
            finally:
                state["in_graph"] = False

        service = make_turn_service(store, run_graph=graph, uow=guarded)
        thread = seed_thread(store.uow)

        service.run_turn(make_cmd(thread, text_payload("hello")))

        assert depths == [0]
        assert guarded.entered_while_forbidden == 0
        assert guarded.entries >= 2  # begin/store before the graph and finish after it


# -- AC-21: conversation outcome ---------------------------------------------------------------------------------
def test_conversation_outcome_rules() -> None:
    """invariant (AC-21): outcome follows web.md section 9's table; a customer message reopens ai_resolved/abandoned only."""
    with temp_sqlite() as store:
        seen: list[str] = []

        def peek(thread: Any, outcome: Any) -> Any:
            def run(turn_input: TurnInput, context: Any) -> Any:
                seen.append(conversation(store, thread).outcome)  # the outcome while the graph runs
                return outcome(turn_input, context)

            return run

        thread = seed_thread(store.uow)
        script = ScriptedRunGraph(
            peek(thread, lambda i, c: answered_outcome(i.turn_id, c.now, closed=True)),
            peek(thread, lambda i, c: answered_outcome(i.turn_id, c.now, closed=False)),
            peek(thread, lambda i, c: handed_off_outcome(i.turn_id, c.now)),
            peek(thread, lambda i, c: answered_outcome(i.turn_id, c.now, closed=True)),
        )
        service = make_turn_service(store, run_graph=script)

        service.run_turn(make_cmd(thread, text_payload("what is this charge?")))
        assert conversation(store, thread).outcome == "ai_resolved"  # answered and every open task closed

        service.run_turn(make_cmd(thread, text_payload("one more question")))
        assert seen[1] == "open"  # the next customer message reopened it before the graph ran
        assert conversation(store, thread).outcome == "open"  # answered, but a task is still open

        service.run_turn(make_cmd(thread, text_payload("I want to speak to someone about a refund")))
        assert conversation(store, thread).outcome == "handed_off"

        service.run_turn(make_cmd(thread, text_payload("thanks")))
        assert seen[3] == "handed_off"  # a later message never reopens handed_off
        assert conversation(store, thread).outcome == "handed_off"  # and a later answered turn leaves it

        # a degraded_handoff turn leaves an open conversation open
        degraded_thread = seed_thread(store.uow)
        make_turn_service(
            store, run_graph=ScriptedRunGraph(lambda i, c: degraded_outcome(i.turn_id, c.now))
        ).run_turn(make_cmd(degraded_thread, text_payload("hello")))
        assert conversation(store, degraded_thread).outcome == "open"

        # abandoned reopens; safety_reply does not
        abandoned = seed_thread(store.uow, outcome="abandoned")
        safety = seed_thread(store.uow, outcome="safety_reply")
        seen.clear()
        service2 = make_turn_service(
            store,
            run_graph=ScriptedRunGraph(
                peek(abandoned, lambda i, c: answered_outcome(i.turn_id, c.now)),
                peek(safety, lambda i, c: answered_outcome(i.turn_id, c.now, closed=True)),
            ),
        )
        service2.run_turn(make_cmd(abandoned, text_payload("I am back")))
        service2.run_turn(make_cmd(safety, text_payload("thanks")))
        assert seen == ["open", "safety_reply"]
        assert conversation(store, safety).outcome == "safety_reply"


@pytest.mark.parametrize(
    ("stored", "trace_outcome", "closed", "expected"),
    [
        ("open", "answered", True, "ai_resolved"),
        ("open", "acted", True, "ai_resolved"),
        ("open", "answered", False, None),
        ("open", "handed_off", False, "handed_off"),
        ("ai_resolved", "handed_off", False, "handed_off"),
        ("handed_off", "handed_off", False, None),
        ("handed_off", "answered", True, None),
        ("open", "safety_reply", False, "safety_reply"),
        ("open", "degraded_handoff", True, None),
        ("open", "to_staff", False, None),
    ],
)
def test_next_outcome_table(stored: str, trace_outcome: str, closed: bool, expected: str | None) -> None:
    """invariant (AC-21): the pure outcome table (web.md section 9)."""
    assert next_outcome(stored, cast(Any, trace_outcome), closed) == expected


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ("ai_resolved", "open"),
        ("abandoned", "open"),
        ("handed_off", None),
        ("safety_reply", None),
        ("open", None),
    ],
)
def test_reopened_outcome_never_reopens_handed_off_or_safety(stored: str, expected: str | None) -> None:
    """invariant (cases.md A-7): only ai_resolved and abandoned reopen."""
    assert reopened_outcome(stored) == expected


# -- plan-added criteria -----------------------------------------------------------------------------------------
def test_step7_failure_leaves_row_failed() -> None:
    """regression (PA-3): a storage error after the graph never leaves the turn row `running` (no stuck 409)."""
    with temp_sqlite() as store:
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload("hello"))
        flaky = HookedUow(store.uow, {"turns.finish": fail_first_call("injected storage error")})
        service = make_turn_service(store, uow=flaky)

        with pytest.raises(RuntimeError, match="injected storage error"):
            service.run_turn(cmd)

        row = turn_row(store, cmd.turn_id)
        assert row.status == "failed"
        assert row.outcome == "degraded_handoff"
        assert [
            m for m in messages_of(store, thread) if m.role == "assistant" and m.turn_id == cmd.turn_id
        ] == []

        graph = ScriptedRunGraph()
        make_turn_service(store, run_graph=graph).run_turn(cmd)  # the same turn_id runs again
        assert len(graph.calls) == 1
        assert turn_row(store, cmd.turn_id).status == "completed"


def test_log_record_attr_matches_web_logging() -> None:
    """invariant (PA-4): services never import web/, so the log attribute is repeated; the two must agree."""
    assert LOG_RECORD_ATTR == RECORD_ATTR == "meridian_record"


def test_unknown_thread_is_refused_not_created() -> None:
    """boundary (web.md section 4 via the service): a turn for a thread with no conversation row stores nothing."""
    with temp_sqlite() as store:
        graph = ScriptedRunGraph()
        service = make_turn_service(store, run_graph=graph)
        orphan = make_cmd(new_thread_id(), text_payload("hello"), turn_id=new_turn_id())

        with pytest.raises(ThreadNotOpen):
            service.run_turn(orphan)

        assert graph.calls == []
        assert count_rows(store, "turns", "turn_id = ?", (str(orphan.turn_id),)) == 0
        assert count_rows(store, "messages", "role = 'customer'") == 0
