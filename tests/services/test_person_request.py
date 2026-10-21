"""AEA-42 PersonRequestService (CON-4): block, request fields, idempotency, running wait, settled, outcome, history.

Temp SQLite copy, recording doubles for HandoffService and ReplyComposer. No model, no network, synthetic data only.
"""

from __future__ import annotations

import json
import sqlite3
import time as time_module
from datetime import timedelta
from typing import Any

import pytest

from meridian.domain.handoff import HandoffReason
from meridian.domain.turn import TurnIds, TurnRecord, TurnTrace
from meridian.policy.handoff import priority_for
from meridian.services.person_request import (
    HandoffWriteFailed,
    PersonRequestOutcome,
    PersonRequestService,
)
from tests.fakes.trace import InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.person_request_support import (
    AGENT,
    CUSTOMER,
    NOW,
    WALL_T0,
    RecordingComposer,
    RecordingHandoffService,
    WallClock,
    make_service,
    open_thread,
    person_request,
    verify_thread,
)

SESSION = "sess-aea-42"


def _turn_rows(store: TempStore, thread_id: Any) -> list[Any]:
    with store.uow() as tx:
        return list(tx.core.turns.for_thread(thread_id))


def test_block_from_composer() -> None:
    """invariant (AC-2): the block is exactly what handoff_block returned, asked for once with the HandoffResult."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        handoff = RecordingHandoffService(store.uow)
        composer = RecordingComposer()
        service = make_service(store, handoff=handoff, composer=composer)
        outcome = service.request(person_request(thread, demo_session=SESSION))
        assert len(composer.block_calls) == 1
        assert outcome.block == composer.handoff_block(composer.block_calls[0])
        assert composer.block_calls[0].case.case_ref == outcome.block.reference
        assert outcome.result == "case_created"


def test_handoff_request_fields() -> None:
    """invariant (AC-3, WF-2): every HandoffRequest and TurnContext field the plan names."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        verify_thread(store, thread)
        handoff = RecordingHandoffService(store.uow)
        trace = InMemoryTraceSink()
        service = make_service(store, handoff=handoff, composer=RecordingComposer(), trace=trace)
        cmd = person_request(thread, demo_session=SESSION)
        service.request(cmd)
        assert len(handoff.calls) == 1
        req, ctx = handoff.calls[0]
        assert req.thread_id == cmd.thread_id
        assert req.turn_id == cmd.turn_id
        assert req.reason is HandoffReason.CUSTOMER_REQUESTED_PERSON
        assert req.priority == priority_for(HandoffReason.CUSTOMER_REQUESTED_PERSON)
        assert req.priority.value == "P3"
        assert req.rule_id == "CON4.person"
        assert req.trigger == "con4"
        assert req.identity.status == "verified"
        assert str(req.identity.customer_id) == CUSTOMER
        assert ctx.intake is None
        assert ctx.now == NOW
        assert ctx.demo_session == SESSION
        assert ctx.ids.agent_version == AGENT
        assert ctx.span.turn_id == cmd.turn_id
        assert len(trace.turns) == 1 and ctx.span.trace_id == trace.turns[0].trace_id


def test_idempotent_turn_id() -> None:
    """invariant (AC-4): same turn id twice gives the same body and one turn row; a new id gives already_open."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        handoff = RecordingHandoffService(store.uow)
        service = make_service(store, handoff=handoff, composer=RecordingComposer())
        first_cmd = person_request(thread, demo_session=SESSION)
        first = service.request(first_cmd)
        again = service.request(first_cmd)
        assert again == first
        assert len(handoff.calls) == 1
        assert len(_turn_rows(store, thread)) == 1
        third = service.request(person_request(thread, demo_session=SESSION))
        assert third.result == "already_open"
        assert third.block.reference == first.block.reference
        assert len(_turn_rows(store, thread)) == 2


def test_running_turn_waits_then_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """failure (AC-5): a running turn is waited for up to 3 s; its stored outcome is returned, else HandoffWriteFailed."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        handoff = RecordingHandoffService(store.uow)
        composer = RecordingComposer()
        wall = WallClock(WALL_T0)
        service = make_service(store, handoff=handoff, composer=composer, wall=wall)

        # (a) the row finishes while the second press waits
        first_cmd = person_request(thread, demo_session=SESSION)
        ids = TurnIds(
            thread_id=thread,
            turn_id=first_cmd.turn_id,
            request_id=first_cmd.request_id,
            run_tag="live",
            run_id=None,
            agent_version=AGENT,
        )
        with store.uow(write=True) as tx:
            tx.core.turns.begin(ids, NOW)
            tx.commit()
        donor = make_service(store, handoff=RecordingHandoffService(store.uow), composer=RecordingComposer())
        stored = donor.request(person_request(thread, demo_session=SESSION))

        def finish_on_first_sleep(_seconds: float) -> None:
            with store.uow(write=True) as tx:
                tx.core.turns.finish(
                    first_cmd.turn_id,
                    TurnRecord(
                        status="completed",
                        trace=TurnTrace(gate_result="person_requested", path="handoff", outcome="handed_off"),
                        replied_at=NOW,
                        server_ms=1,
                        model_calls=0,
                        input_tokens=0,
                        output_tokens=0,
                        cost_usd=0.0,
                        tool_calls=0,
                        trace_id=None,
                        trace_export="off",
                        response=stored.model_dump_json(),
                    ),
                )
                tx.commit()

        monkeypatch.setattr(time_module, "sleep", finish_on_first_sleep)
        got = service.request(first_cmd)
        assert got == stored
        assert len(handoff.calls) == 0

        # (b) a row that never finishes: the wall clock moves 1 s per sleep
        stuck_cmd = person_request(thread, demo_session=SESSION)
        stuck_ids = ids.model_copy(update={"turn_id": stuck_cmd.turn_id, "request_id": stuck_cmd.request_id})
        with store.uow(write=True) as tx:
            tx.core.turns.begin(stuck_ids, NOW)
            tx.commit()
        sleeps: list[float] = []

        def advance(seconds: float) -> None:
            sleeps.append(seconds)
            wall.advance(1.0)

        monkeypatch.setattr(time_module, "sleep", advance)
        with pytest.raises(HandoffWriteFailed):
            service.request(stuck_cmd)
        assert len(sleeps) <= 4


def test_settled_from_conversation_state() -> None:
    """invariant (AC-13): settled shows the prior verified action and the new case reference."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        verify_thread(store, thread)
        composer = RecordingComposer()
        service = make_service(store, handoff=RecordingHandoffService(store.uow), composer=composer)
        outcome = service.request(person_request(thread, demo_session=SESSION))
        kinds = [a.kind for a in outcome.settled.actions]
        assert "verified" in kinds and "case_opened" in kinds
        assert outcome.settled.identity.status == "verified"
        assert outcome.settled.request is not None
        assert outcome.settled.request.reference == outcome.block.reference
        settled, _identity, controller = composer.view_calls[-1]
        assert settled.read_at == NOW
        assert controller.kind == "ai"


def test_con4_marks_conversation_handed_off() -> None:
    """invariant (AC-18): CON-4 sets outcome handed_off; the abandonment sweep's selection skips the thread."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION, last_customer_wall_at=WALL_T0)
        control = open_thread(store, demo_session=SESSION, last_customer_wall_at=WALL_T0)
        service = make_service(
            store, handoff=RecordingHandoffService(store.uow), composer=RecordingComposer()
        )
        service.request(person_request(thread, demo_session=SESSION))
        with store.uow() as tx:
            row = tx.core.conversations.lookup(str(thread))
            assert getattr(row, "outcome", None) == "handed_off"
            picked = tx.core.conversations.idle_live(WALL_T0 + timedelta(minutes=31) - timedelta(minutes=30))
        picked_ids = {str(t) for t, _ in picked}
        assert str(control) in picked_ids
        assert str(thread) not in picked_ids


def test_stored_outcome_is_history_ready() -> None:
    """invariant (AC-20): the turn row stores the body exactly as returned, with the card under `block`."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        service = make_service(
            store,
            handoff=RecordingHandoffService(store.uow),
            composer=RecordingComposer(),
            trace=InMemoryTraceSink(status="off"),
        )
        cmd = person_request(thread, demo_session=SESSION)
        outcome = service.request(cmd)
        (row,) = _turn_rows(store, thread)
        assert row.status == "completed"
        assert row.gate_result == "person_requested"
        assert row.path == "handoff"
        assert row.outcome == "handed_off"
        assert row.trace_export == "off"
        assert row.response is not None
        assert json.loads(row.response) == json.loads(outcome.model_dump_json())
        assert "block" in json.loads(row.response)
        assert PersonRequestOutcome.model_validate_json(row.response) == outcome


def test_already_open_block_names_existing_case() -> None:
    """invariant (AC-20): a new turn id on a thread with an open case answers with that case's card."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        service = make_service(
            store, handoff=RecordingHandoffService(store.uow), composer=RecordingComposer()
        )
        first = service.request(person_request(thread, demo_session=SESSION))
        second = service.request(person_request(thread, demo_session=SESSION))
        assert second.result == "already_open"
        assert second.block.reference == first.block.reference
        assert second.block.promise_text == first.block.promise_text
        assert second.settled.request is not None
        assert second.settled.request.reference == first.block.reference
        conn = sqlite3.connect(store.db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM cases WHERE thread_id = ?", (str(thread),)).fetchone()[
                0
            ]
        finally:
            conn.close()
        assert count == 1


def test_failed_open_marks_turn_failed_and_retry_reruns() -> None:
    """failure (PA-3): a failing open leaves the turn failed, not running; the next press re-runs and succeeds."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        handoff = RecordingHandoffService(store.uow, fail=True)
        service: PersonRequestService = make_service(store, handoff=handoff, composer=RecordingComposer())
        cmd = person_request(thread, demo_session=SESSION)
        with pytest.raises(HandoffWriteFailed):
            service.request(cmd)
        (row,) = _turn_rows(store, thread)
        assert row.status == "failed"
        handoff.fail = False
        outcome = service.request(cmd)
        assert outcome.result == "case_created"
        (row,) = _turn_rows(store, thread)
        assert row.status == "completed"
        assert len(handoff.calls) == 2
