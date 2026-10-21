"""AEA-40 Part B: `SessionService` (CON-1 behind the routes) on a temp working copy.

Acceptance criteria covered: AC-1 (service side), AC-16, AC-17 and the plan-added PA-5.
Part B waits for AEA-02b (`ClockView`, `StaffingView`): the doubles resolve those types lazily and fail with a message
naming the missing prerequisite until it lands.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest

from meridian.domain.blocks import HandoffBlock, LiveQueuedBlock
from meridian.policy.limits import Limits
from meridian.policy.texts import TextId, render
from meridian.services.turn import ThreadNotOpen
from tests.api.web_shell_support import FakeSessionStore
from tests.fakes import WORKED_PAIRS_NOW, FixedClock
from tests.fixtures.sqlite import temp_sqlite
from tests.services.chat_doubles import (
    AGENT_VERSION,
    WALL_NOW,
    FakeDemo,
    HookedUow,
    RaisingRunGraph,
    ScriptedRunGraph,
    attr,
    conversation,
    count_rows,
    fail_after,
    handoff_block,
    live_queued_block,
    make_cmd,
    make_session_service,
    make_turn_service,
    messages_of,
    new_request_id,
    new_thread_id,
    newest_event_id,
    seed_case,
    seed_person_request_turn,
    seed_takeover,
    text_payload,
)

QUESTION = "I got an invoice and I am not sure what it is for."


def _login() -> Any:
    sessions = FakeSessionStore()
    return sessions.session_of(sessions.issue())


# -- AC-1 (service side) and PA-5 --------------------------------------------------------------------------------
def test_open_writes_one_transaction_with_wall_start() -> None:
    """invariant (AC-1, PA-5): open writes the conversation and the greeting together; the wall start is UTC."""
    login = _login()
    with temp_sqlite() as store:
        demo = FakeDemo()
        service = make_session_service(store, demo=demo, wall=lambda: WALL_NOW)

        opened = service.open(login, run_tag="eval", run_id="run-abc", request_id=new_request_id())

        conv = conversation(store, opened.thread_id)
        assert conv.demo_session == str(login.session_id)
        assert (conv.run_tag, conv.run_id, conv.agent_version) == ("eval", "run-abc", AGENT_VERSION)
        assert (conv.outcome, conv.controller.kind, conv.live_state) == ("open", "ai", "not_live")
        assert conv.started_at == WORKED_PAIRS_NOW
        assert conv.started_wall_at == WALL_NOW  # PA-5: UTC wall start, for the zero-traffic alert
        assert conv.staffing_at_start == "nobody_online"
        messages = messages_of(store, opened.thread_id)
        assert [(m.role, m.turn_id, m.text) for m in messages] == [
            ("assistant", None, render(TextId.GREETING))
        ]
        assert opened.greeting_message_id == messages[0].id
        assert opened.greeting_text == render(TextId.GREETING)
        assert opened.greeting_at == WORKED_PAIRS_NOW
        assert opened.clock == demo.clock_view() and opened.staffing == demo.staffing()
        assert opened.controller.kind == "ai"
        assert opened.settled.actions == () and opened.settled.replying.kind == "ai"
        limits = Limits().turn
        assert (
            (
                opened.limits.turn_deadline_ms,
                opened.limits.still_working_after_ms,
                opened.limits.browser_give_up_after_ms,
                opened.limits.max_message_chars,
            )
            == (60000, 10000, 65000, 2000)
            == (
                limits.turn_deadline_ms,
                limits.still_working_after_ms,
                limits.browser_give_up_after_ms,
                limits.max_message_chars,
            )
        )
        assert opened.last_event_id == 0
        for table in ("turns", "events", "lookup_log", "spend_ledger", "check_events"):
            assert count_rows(store, table) == 0  # no model, no turn, no event


def test_open_is_one_transaction() -> None:
    """invariant (AC-1): a failure after the greeting write rolls the conversation row back too."""
    login = _login()
    with temp_sqlite() as store:
        broken = HookedUow(store.uow, {"messages.append": fail_after("injected after the greeting write")})
        service = make_session_service(store, uow=broken)

        with pytest.raises(RuntimeError, match="injected after the greeting write"):
            service.open(login, run_tag="live", run_id=None, request_id=new_request_id())

        assert count_rows(store, "conversations") == 0
        assert count_rows(store, "messages") == 0


def test_two_opens_make_two_threads() -> None:
    """invariant (AC-1): each open mints a new thread id and its own greeting."""
    login = _login()
    with temp_sqlite() as store:
        service = make_session_service(store)
        first = service.open(login, run_tag="live", run_id=None, request_id=new_request_id())
        second = service.open(login, run_tag="live", run_id=None, request_id=new_request_id())
        assert first.thread_id != second.thread_id
        assert count_rows(store, "conversations") == 2
        assert count_rows(store, "messages", "role = 'assistant' AND turn_id IS NULL") == 2


# -- AC-16: the whole conversation, in order ---------------------------------------------------------------------
def test_thread_holds_full_history() -> None:
    """invariant (AC-16): greeting, customer line, reply, join, pause, Riley, resume and a shift end, in time order."""
    login = _login()
    step = dt.timedelta(seconds=1)
    with temp_sqlite() as store:
        demo = FakeDemo()
        service = make_session_service(store, demo=demo)
        opened = service.open(login, run_tag="live", run_id=None, request_id=new_request_id())
        thread = opened.thread_id
        turn_cmd = make_cmd(thread, text_payload(QUESTION), demo_session=str(login.session_id))
        later = FixedClock().advanced(dt.timedelta(minutes=1))
        make_turn_service(store, run_graph=ScriptedRunGraph(), clock=later).run_turn(turn_cmd)
        shift = handoff_block("MHC-C-0042", WORKED_PAIRS_NOW + dt.timedelta(minutes=6))
        takeover = seed_takeover(
            store.uow, thread, WORKED_PAIRS_NOW + dt.timedelta(minutes=5), step=step, shift_end=shift
        )

        history = service.thread(thread)

        entries = history.entries
        assert [e.speaker_kind for e in entries] == [
            "assistant",
            "customer",
            "assistant",
            "event",
            "event",
            "representative",
            "event",
            "assistant",
        ]
        greeting, customer, reply, joined, paused, riley, resumed, shift_ended = entries
        assert greeting.turn_id == "greeting"
        assert len(greeting.blocks) == 1 and greeting.blocks[0].type == "text"
        assert attr(greeting.blocks[0], "text") == render(TextId.GREETING)
        assert (customer.turn_id, customer.text, customer.blocks) == (str(turn_cmd.turn_id), QUESTION, ())
        assert reply.turn_id == str(turn_cmd.turn_id)
        assert reply.blocks[0].type == "text"
        assert attr(reply.blocks[0], "text") == "Here is what that invoice covers."
        assert (joined.turn_id, joined.text, joined.speaker_name) == (
            f"evt-{takeover.joined_id}",
            takeover.lines["joined"],
            None,
        )
        assert (paused.turn_id, paused.text) == (f"evt-{takeover.paused_id}", takeover.lines["paused"])
        assert (riley.turn_id, riley.speaker_name, riley.text, riley.blocks) == (
            f"msg-{takeover.riley_message_id}",
            "Riley",
            takeover.riley_text,
            (),
        )
        assert (resumed.turn_id, resumed.text) == (f"evt-{takeover.resumed_id}", takeover.lines["resumed"])
        assert shift_ended.turn_id == f"evt-{takeover.shift_end_id}"
        assert shift_ended.text is None
        assert len(shift_ended.blocks) == 1 and shift_ended.blocks[0].type == "handoff"
        assert attr(shift_ended.blocks[0], "reference") == "MHC-C-0042"
        # a turn's customer line and reply share the turn's id; every other entry has an id unique in the thread
        others = [
            e.turn_id for e in entries if e.turn_id == "greeting" or e.turn_id.startswith(("msg-", "evt-"))
        ]
        assert len(others) == len(entries) - 2 and len(set(others)) == len(others)
        assert [e.at for e in entries] == sorted(e.at for e in entries)
        assert history.last_event_id == takeover.newest_event_id == newest_event_id(store, thread)
        assert history.state == "open"
        assert history.thread_id == thread
        assert history.clock == demo.clock_view() and history.staffing == demo.staffing()
        assert history.settled.replying.kind == "ai"


def test_failed_turn_contributes_only_its_customer_line() -> None:
    """boundary (AC-16): a failed turn shows the customer's message and no reply (and a retry never doubles it)."""
    login = _login()
    with temp_sqlite() as store:
        service = make_session_service(store)
        thread = service.open(login, run_tag="live", run_id=None, request_id=new_request_id()).thread_id
        failing = make_cmd(thread, text_payload("this one fails"), demo_session=str(login.session_id))
        make_turn_service(store, run_graph=RaisingRunGraph()).run_turn(failing)

        entries = service.thread(thread).entries

        assert [(e.speaker_kind, e.turn_id) for e in entries] == [
            ("assistant", "greeting"),
            ("customer", str(failing.turn_id)),
        ]
        assert entries[1].text == "this one fails"

        make_turn_service(store, run_graph=ScriptedRunGraph()).run_turn(failing)  # the retry succeeds
        again = service.thread(thread).entries
        assert [e.speaker_kind for e in again] == ["assistant", "customer", "assistant"]


def test_thread_not_open_for_unknown_thread() -> None:
    """boundary (web.md section 4 via the service): a thread with no conversation row is refused."""
    with temp_sqlite() as store:
        service = make_session_service(store)
        with pytest.raises(ThreadNotOpen):
            service.thread(new_thread_id())


# -- AC-17: a CON-4 person request in the history ----------------------------------------------------------------
@pytest.mark.parametrize("make_block", [handoff_block, live_queued_block], ids=["handoff", "live_queued"])
def test_thread_shows_person_request_card(make_block: Any) -> None:
    """invariant (AC-17): a CON-4 turn row shows as 'Talk to a person' then its stored card, both on the CON-4 turn_id."""
    login = _login()
    with temp_sqlite() as store:
        service = make_session_service(store)
        thread = service.open(login, run_tag="live", run_id=None, request_id=new_request_id()).thread_id
        first = make_cmd(thread, text_payload(QUESTION), demo_session=str(login.session_id))
        make_turn_service(store, run_graph=ScriptedRunGraph()).run_turn(first)
        seed_case(store.uow, thread, "MHC-C-0042")
        with store.uow() as tx:
            case_ref = str(tx.cases.cases.list_for_thread(thread)[0].case_ref)
        block: HandoffBlock | LiveQueuedBlock = make_block(case_ref, WORKED_PAIRS_NOW)
        con4_turn = seed_person_request_turn(store.uow, thread, block)

        entries = service.thread(thread).entries

        assert [(e.speaker_kind, e.turn_id) for e in entries] == [
            ("assistant", "greeting"),
            ("customer", str(first.turn_id)),
            ("assistant", str(first.turn_id)),
            ("customer", str(con4_turn)),
            ("assistant", str(con4_turn)),
        ]
        label, card = entries[3], entries[4]
        assert label.text == render(TextId.PERSON_REQUEST_LABEL) == "Talk to a person"
        assert label.blocks == ()
        assert len(card.blocks) == 1
        assert card.blocks[0].type == block.type
        assert attr(card.blocks[0], "reference") == case_ref  # the card's reference is the case's
        assert count_rows(store, "messages", "turn_id = ?", (str(con4_turn),)) == 0  # CON-4 stores no message
