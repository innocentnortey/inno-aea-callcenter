"""load_context (AEA-34): the DB-authority keys are rebuilt from the working copy every turn."""

from __future__ import annotations

import dataclasses
import functools
import random
import re
from collections.abc import Iterator
from datetime import date, timedelta
from typing import cast

import pytest
from langgraph.runtime import Runtime

from meridian.adapters.sqlite.rows import CaseRow, FollowupRow
from meridian.agent.graph import NodeFn, timed_node
from meridian.agent.nodes.load_context import load_context
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.common import (
    CaseRef,
    CustomerId,
    FailureCounters,
    HandoffReason,
    Priority,
)
from meridian.domain.handoff import Promise
from meridian.domain.identity import IdentityState
from meridian.domain.state import ChatLine, Controller, LoadContextUpdate
from meridian.domain.turn import TurnIds
from meridian.policy.limits import ContextLimits, Limits
from meridian.privacy.redact import RedactionProfile, redact
from tests.fakes import InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.agent.nodes.load_context_fixtures import (
    DEMO_START,
    RecordingUow,
    add_line,
    connection_of,
    count_rows,
    make_ctx,
    make_deps,
    make_state,
    new_thread,
    new_turn,
    run_node,
    seed_conversation,
    seed_identity,
    seed_twenty_turns,
    seed_wp4f,
    wp4f_moved,
)

MIN = timedelta(minutes=1)
CASE = CaseRef("MHC-C-0009")


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def test_action_without_checkpoint_is_seen(store: TempStore) -> None:
    thread, turn3, turn4 = seed_wp4f(store)
    now = DEMO_START + 5 * MIN
    state = make_state(
        thread, turn4, now=now, settled=Settled(actions=(), open_case=None, read_at=DEMO_START)
    )
    deps, touched = make_deps(store.uow)
    update = run_node(state, make_ctx(thread, turn4, now=now), deps)
    settled = update["settled"]
    assert len(settled.actions) == 1
    a = settled.actions[0]
    assert a.kind is ActionKind.MOVED
    assert a.key.turn_id == turn3
    assert a.key.record_id == "159"
    assert a.after == wp4f_moved(thread, turn3).after
    assert a.source == "actions_table"
    v = settled.current_visit()
    assert v is not None
    assert v.appointment_id == 159
    assert v.date == date(2026, 10, 19)
    assert v.window == "08:00-12:00"
    assert v.technician == "Marta Kowalski"
    assert v.status == "moved"
    assert settled.read_at == now
    assert touched == []


def test_stale_checkpoint_settled_replaced(store: TempStore) -> None:
    thread, turn3, turn4 = seed_wp4f(store)
    now = DEMO_START + 5 * MIN
    extra = CompletedAction(
        key=ActionKey(thread_id=thread, turn_id=new_turn(), kind=ActionKind.BOOKED, record_id="160"),
        kind=ActionKind.BOOKED,
        records={"appointment": "160", "slot": "57"},
        after={
            "date": "2026-10-20",
            "window": "12:00-16:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "Diagnostic fee: waived for members",
        },
        at=DEMO_START,
    )
    stale = Settled(
        actions=(wp4f_moved(thread, turn3), extra), open_case=None, read_at=DEMO_START - timedelta(days=1)
    )
    deps, touched = make_deps(store.uow)
    update = run_node(
        make_state(thread, turn4, now=now, settled=stale), make_ctx(thread, turn4, now=now), deps
    )
    assert len(update["settled"].actions) == 1
    assert not update["settled"].has(ActionKind.BOOKED)
    assert update["settled"].read_at == now
    assert touched == []


def test_open_case_from_rows(store: TempStore) -> None:
    a, b = new_thread(), new_thread()
    turn = new_turn()
    promise = Promise(
        policy_row="R26.unstaffed",
        text="Synthetic promise line for AEA-34 tests.",
        due_at=DEMO_START + timedelta(days=3),
        due_label="Monday, October 19, 7:00 pm",
        extra_lines=(),
        live_queued=False,
    )
    with store.uow(write=True) as tx:
        seed_conversation(tx, a, at=DEMO_START)
        seed_conversation(tx, b, at=DEMO_START)
        tx.cases.cases.insert(
            CaseRow(
                case_ref=CASE,
                thread_id=a,
                turn_id=turn,
                customer_id=CustomerId("MHC-10001"),
                reason=HandoffReason.BILLING_DISPUTE,
                priority=Priority.P3,
                rule_id="R2.billing_dispute",
                trigger="planner",
                lifecycle="unassigned",
                created_at=DEMO_START,
                updated_at=DEMO_START,
            )
        )
        tx.cases.promises.insert(CASE, promise, DEMO_START)
        tx.cases.followups.upsert(
            FollowupRow(
                case_ref=CASE,
                thread_id=a,
                channel="email",
                destination_label="the email on file",
                destination=None,
                on_record=True,
                window="morning",
                saved_line="Synthetic follow-up line.",
                updated_at=DEMO_START,
            )
        )
        tx.commit()
    deps, touched = make_deps(store.uow)
    now = DEMO_START + MIN
    ua = run_node(make_state(a, turn, now=now), make_ctx(a, turn, now=now), deps)
    oc = ua["settled"].open_case
    assert oc is not None
    assert oc.case_ref == "MHC-C-0009"
    assert oc.reason is HandoffReason.BILLING_DISPUTE
    assert oc.priority is Priority.P3
    assert oc.state == "unassigned"
    assert oc.promise.text == "Synthetic promise line for AEA-34 tests."
    assert oc.promise.policy_row == "R26.unstaffed"
    assert oc.followup is not None and oc.followup.window == "morning"
    assert oc.live_queued is False
    ub = run_node(make_state(b, turn, now=now), make_ctx(b, turn, now=now), deps)
    assert ub["settled"].open_case is None
    assert touched == []


def test_controller_from_conversation_row(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    with store.uow(write=True) as tx:
        seed_conversation(tx, thread, at=DEMO_START)
        tx.commit()
    deps, touched = make_deps(store.uow)
    now = DEMO_START + 5 * MIN
    human = Controller(kind="human", representative_name="Riley", case_ref=CASE)
    with store.uow(write=True) as tx:
        tx.core.conversations.set_controller(
            thread, human, live_state="joined", live_since=DEMO_START + 2 * MIN
        )
        tx.commit()
    state_ai = make_state(thread, turn, now=now, controller=Controller(kind="ai"))
    assert run_node(state_ai, make_ctx(thread, turn, now=now), deps)["controller"] == human
    with store.uow(write=True) as tx:
        tx.core.conversations.set_controller(
            thread, Controller(kind="ai"), live_state="handed_back", live_since=DEMO_START + 4 * MIN
        )
        tx.commit()
    state_human = make_state(thread, turn, now=now, controller=human)
    back = run_node(state_human, make_ctx(thread, turn, now=now), deps)["controller"]
    assert back == Controller(kind="ai")
    assert back.representative_name is None and back.case_ref is None
    assert touched == []


def test_identity_kept_over_twenty_turns(store: TempStore) -> None:
    thread = new_thread()
    with store.uow(write=True) as tx:
        seed_conversation(tx, thread, at=DEMO_START)
        seed_identity(
            tx,
            thread,
            status="verified",
            customer_id="MHC-10001",
            verified_at=DEMO_START,
            updated_at=DEMO_START,
            codes=[(DEMO_START - 2 * MIN, DEMO_START + 8 * MIN, 2)],
        )
        tx.commit()
    deps, touched = make_deps(store.uow)
    state = make_state(thread, new_turn(), now=DEMO_START)
    update: LoadContextUpdate = {}
    turns = []
    for i in range(1, 21):
        t = new_turn()
        turns.append(t)
        with store.uow(write=True) as tx:
            add_line(
                tx,
                thread,
                "customer",
                f"Question number {i:02d} about my visit.",
                DEMO_START + i * MIN,
                turn_id=t,
            )
            add_line(
                tx,
                thread,
                "assistant",
                f"Answer number {i:02d}.",
                DEMO_START + i * MIN + timedelta(seconds=10),
                turn_id=t,
            )
            tx.commit()
        now = DEMO_START + i * MIN + timedelta(seconds=20)
        update = run_node(state, make_ctx(thread, t, now=now), deps)
        assert update["identity"].status == "verified"
        assert update["identity"].customer_id == "MHC-10001"
        state = state.model_copy(update=dict(update))
    window = update["chat_window"]
    assert {line.turn_id for line in window} == set(turns[10:])
    assert len(window) == 20
    assert "open_tasks" not in update
    assert touched == []


def test_identity_reread_with_expiry(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    with store.uow(write=True) as tx:
        seed_conversation(tx, thread, at=DEMO_START)
        seed_identity(
            tx,
            thread,
            status="code_sent",
            customer_id="MHC-10001",
            verified_at=None,
            updated_at=DEMO_START,
            codes=[
                (DEMO_START - 30 * MIN, DEMO_START - 20 * MIN, 0),
                (DEMO_START, DEMO_START + 10 * MIN, 2),
            ],
        )
        tx.commit()
    stale = IdentityState(
        status="code_sent",
        customer_id=CustomerId("MHC-10001"),
        masked_hint=None,
        code_expires_at=DEMO_START - 20 * MIN,
        tries_left=3,
        codes_sent=1,
        verified_at=None,
    )
    now = DEMO_START + 15 * MIN
    deps, touched = make_deps(store.uow)
    update = run_node(
        make_state(thread, turn, now=now, identity=stale), make_ctx(thread, turn, now=now), deps
    )
    ident = update["identity"]
    assert ident.code_expires_at == DEMO_START + 10 * MIN
    assert ident.code_expires_at is not None and ident.code_expires_at < now
    assert ident.tries_left == 2
    assert ident.codes_sent == 2
    assert ident.status == "code_sent"
    assert touched == []


def test_window_limits(store: TempStore) -> None:
    thread = new_thread()
    with store.uow(write=True) as tx:
        seed_conversation(tx, thread, at=DEMO_START)
        add_line(tx, thread, "assistant", "Hi, I'm the Meridian assistant.", DEMO_START, turn_id=None)
        tx.commit()
    seed_twenty_turns(store, thread, long_turn=18, rep_after=15)
    turn = new_turn()
    now = DEMO_START + 30 * MIN

    def window(limits: Limits) -> list[ChatLine]:
        deps, touched = make_deps(store.uow, limits=limits)
        out = run_node(make_state(thread, turn, now=now), make_ctx(thread, turn, now=now), deps)[
            "chat_window"
        ]
        assert touched == []
        return out

    a = window(Limits())
    assert len(a) == 21
    assert a[0].text == "Question number 11 about my visit."
    assert not any(line.text.startswith("Question number 01") for line in a)
    assert not any(line.text == "Hi, I'm the Meridian assistant." for line in a)
    reps = [line for line in a if line.speaker == "representative"]
    assert len(reps) == 1 and reps[0].turn_id is None
    assert [line.at for line in a] == sorted(line.at for line in a)
    long_line = next(line for line in a if line.text.startswith("A" * 10))
    assert (
        len(long_line.text) == 600 and long_line.text.endswith("…") and long_line.text.startswith("A" * 599)
    )
    assert sum(len(line.text) for line in a) <= 8000

    b = window(Limits(context=ContextLimits(window_turns=4, window_line_chars=50, window_total_chars=8000)))
    assert len(b) == 8
    cut = next(line for line in b if line.text.startswith("AAAA"))
    assert cut.text == "A" * 49 + "…" and len(cut.text) == 50

    c = window(Limits(context=ContextLimits(window_turns=4, window_line_chars=50, window_total_chars=120)))
    assert [line.text for line in c] == [
        "Question number 19 about my visit.",
        "Answer number 19.",
        "Question number 20 about my visit.",
        "Answer number 20.",
    ]
    assert sum(len(line.text) for line in c) == 102


def test_window_has_no_tool_output_or_codes(store: TempStore) -> None:
    rng = random.Random(34)
    code = str(rng.randrange(100_000, 1_000_000))
    card = "".join(str(rng.randrange(10)) for _ in range(16))
    redacted_code = redact(f"My code is {code}", RedactionProfile.STORE).text
    redacted_card = redact(f"Card {card} please", RedactionProfile.STORE).text
    assert redacted_code == "My code is [code]"
    assert redacted_card == "Card [card number removed] please"
    thread, turn = new_thread(), new_turn()
    sentinel = "LOOKUP-SNAPSHOT-SENTINEL-AEA34"
    with store.uow(write=True) as tx:
        seed_conversation(tx, thread, at=DEMO_START)
        add_line(tx, thread, "customer", "[code entered]", DEMO_START + MIN, turn_id=turn, kind="code")
        add_line(tx, thread, "customer", redacted_code, DEMO_START + 2 * MIN, turn_id=turn)
        add_line(tx, thread, "customer", redacted_card, DEMO_START + 3 * MIN, turn_id=turn)
        msg_id = add_line(
            tx, thread, "assistant", "Thanks, checking your account now.", DEMO_START + 4 * MIN, turn_id=turn
        )
        connection_of(tx).execute(
            "INSERT INTO lookup_log (thread_id, turn_id, message_id, tool, record_ids, passage_ids, result_seen) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(thread), str(turn), msg_id, "read_invoices", "[]", "[]", sentinel),
        )
        tx.commit()
    deps, touched = make_deps(store.uow)
    now = DEMO_START + 5 * MIN
    window = run_node(make_state(thread, turn, now=now), make_ctx(thread, turn, now=now), deps)["chat_window"]
    texts = [line.text for line in window]
    for text in texts:
        assert sentinel not in text
        assert code not in text and card not in text
        assert re.search(r"\d{6}", text) is None
        assert re.search(r"\d{13,19}", text) is None
    assert {"[code entered]", redacted_code, redacted_card} <= set(texts)
    assert touched == []


def test_only_timeouts_counter_copied(store: TempStore) -> None:
    t, u = new_thread(), new_thread()
    with store.uow(write=True) as tx:
        seed_conversation(tx, t, at=DEMO_START)
        seed_conversation(tx, u, at=DEMO_START)
        for k, thread in enumerate((t, t, u), start=1):
            ids = TurnIds(
                thread_id=thread,
                turn_id=new_turn(),
                request_id=make_ctx(t, new_turn(), now=DEMO_START).ids.request_id,
                run_tag="live",
                run_id=None,
                agent_version="test",
            )
            tx.core.turns.begin(ids, DEMO_START + k * MIN)
        tx.core.turns.fail_running()
        tx.commit()
    counters = FailureCounters(
        failed_answers=1, tool_failures=2, identity_failures=1, corrections=3, timeouts=0, bookings=1
    )
    turn = new_turn()
    now = DEMO_START + 10 * MIN
    deps, touched = make_deps(store.uow)
    update = run_node(make_state(t, turn, now=now, counters=counters), make_ctx(t, turn, now=now), deps)
    c = update["counters"]
    assert c.timeouts == 2
    assert (c.failed_answers, c.tool_failures, c.identity_failures, c.corrections, c.bookings) == (
        1,
        2,
        1,
        3,
        1,
    )
    assert touched == []


def test_returns_only_its_keys(store: TempStore) -> None:
    thread, _, turn4 = seed_wp4f(store)
    now = DEMO_START + 5 * MIN
    deps, touched = make_deps(store.uow)
    update = run_node(make_state(thread, turn4, now=now), make_ctx(thread, turn4, now=now), deps)
    allowed = LoadContextUpdate.__required_keys__ | LoadContextUpdate.__optional_keys__
    assert set(update) == {"settled", "controller", "identity", "chat_window", "counters"}
    assert set(update) <= allowed
    for key in (
        "check_events",
        "gate",
        "open_tasks",
        "shown_slots",
        "last_lookups",
        "pending_change",
        "halt",
    ):
        assert key not in update
    assert touched == []


def test_one_read_only_uow_closed_before_return(store: TempStore) -> None:
    thread, _, turn4 = seed_wp4f(store)
    now = DEMO_START + 5 * MIN
    rec = RecordingUow(store.uow)
    deps, touched = make_deps(rec)
    tables = ("actions", "messages", "turns", "check_events", "lookup_log")
    before = {name: count_rows(store, name) for name in tables}
    rec.events.clear()
    run_node(make_state(thread, turn4, now=now), make_ctx(thread, turn4, now=now), deps)
    assert rec.events == [("enter", False, False), ("exit", False, False)]
    assert touched == []
    assert {name: count_rows(store, name) for name in tables} == before


def test_node_span_via_timed_node(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    phrase = "SENTINEL-WINDOW-PHRASE-AEA34"
    with store.uow(write=True) as tx:
        seed_conversation(tx, thread, at=DEMO_START)
        add_line(tx, thread, "customer", f"Please check {phrase} for me.", DEMO_START + MIN, turn_id=turn)
        tx.commit()
    sink = InMemoryTraceSink()
    deps, touched = make_deps(store.uow, trace=sink)
    now = DEMO_START + 2 * MIN
    ctx0 = make_ctx(thread, turn, now=now)
    state = make_state(thread, turn, now=now)
    with sink.turn(ctx0.ids) as span:
        ctx = dataclasses.replace(ctx0, span=span)
        wrapped = timed_node("load_context", cast(NodeFn, functools.partial(load_context, deps=deps)), deps)
        update = cast(LoadContextUpdate, wrapped(state, Runtime(context=ctx)))
        assert any(phrase in line.text for line in update["chat_window"])
        rec = sink.spans_for(span)
        assert len(rec.nodes) == 1
        assert rec.nodes[0].name == "load_context"
        assert rec.nodes[0].status == "ok"
        assert isinstance(rec.nodes[0].elapsed_ms, int) and rec.nodes[0].elapsed_ms >= 0
    assert phrase not in repr(sink.turns)
    assert touched == []


def test_controller_ai_without_conversation_row(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    now = DEMO_START + MIN
    human = Controller(kind="human", representative_name="Riley", case_ref=CASE)
    deps, touched = make_deps(store.uow)
    update = run_node(
        make_state(thread, turn, now=now, controller=human), make_ctx(thread, turn, now=now), deps
    )
    assert update["controller"] == Controller(kind="ai")
    assert touched == []


def test_ended_thread_raises_rather_than_guessing_ai(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    now = DEMO_START + MIN
    with store.uow(write=True) as tx:
        connection_of(tx).execute(
            "INSERT INTO ended_threads (thread_id, demo_session, ended_wall_at, reason, reset_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(thread), "demo", "2026-10-21T00:00:00.000Z", "reset", None),
        )
        tx.commit()
    deps, _ = make_deps(store.uow)
    with pytest.raises(ValueError, match="EndedThread"):
        run_node(make_state(thread, turn, now=now), make_ctx(thread, turn, now=now), deps)


def test_thread_mismatch_raises_before_reading(store: TempStore) -> None:
    t, u, turn = new_thread(), new_thread(), new_turn()
    now = DEMO_START + MIN
    rec = RecordingUow(store.uow)
    deps, _ = make_deps(rec)
    with pytest.raises(ValueError, match="disagree on the thread"):
        run_node(make_state(t, turn, now=now), make_ctx(u, turn, now=now), deps)
    assert rec.events == []
