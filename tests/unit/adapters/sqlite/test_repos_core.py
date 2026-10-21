"""AEA-10 AC-7, AC-12 to AC-17, AC-20, AC-23: the core repositories."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import timedelta
from uuid import uuid4

import pytest

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.repos_core import ConversationRow, EndedThread
from meridian.adapters.sqlite.rows import StreamEvent, case_stream, thread_stream
from meridian.domain.actions import CompletedAction
from meridian.domain.handoff import Promise
from meridian.domain.tools import LookupEntry, LookupRow
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.adapters.sqlite.helpers import (
    NOW,
    case_ref,
    case_row,
    conversation,
    customer_id,
    invoice_id,
    new_thread,
    new_turn,
    turn_ids,
    turn_record,
)


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _action(thread: object, turn: object, kind: str, record_id: str, **kw: object) -> CompletedAction:
    data: dict[str, object] = {
        "key": {"thread_id": str(thread), "turn_id": str(turn), "kind": kind, "record_id": record_id},
        "kind": kind,
        "records": {"appointment": record_id},
        "at": NOW,
    }
    data.update(kw)
    return CompletedAction.model_validate(data)


def test_ids_not_reused_and_tombstone_lookup(store: TempStore) -> None:
    live, cleared_thread = new_thread(), new_thread()
    stream = case_stream(case_ref(9))
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(conversation(live))
        tx.core.conversations.insert(conversation(cleared_thread, live_state="closed"))
        assert isinstance(tx.core.conversations.lookup(str(live)), ConversationRow)
        first = [tx.core.events.append(stream, StreamEvent(type="t", at=NOW)) for _ in range(3)]
        tx.commit()
    with store.uow(exclusive=True) as tx:
        tx.core.reset.clear_demo_tables("reset-1", ended_at=NOW)
        tx.commit()
    with store.uow(write=True) as tx:
        new_id = tx.core.events.append(stream, StreamEvent(type="t", at=NOW))
        tx.commit()
    print("ids before", first, "after", new_id)
    assert new_id > max(first)
    with store.uow() as tx:
        ended = tx.core.conversations.lookup(str(cleared_thread))
        assert isinstance(ended, EndedThread)
        assert (ended.reason, ended.reset_id) == ("demo_reset", "reset-1")
        assert tx.core.conversations.lookup(str(uuid4())) is None
        assert tx.core.conversations.lookup("not-a-uuid") is None


def test_action_record_idempotent_on_key(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    first = _action(thread, turn, "booked", "160")
    with store.uow(write=True) as tx:
        stored = tx.core.actions.record(first)
        again = tx.core.actions.record(first.model_copy(update={"at": NOW + timedelta(seconds=5)}))
        assert again == stored == first
        assert tx.connection.execute("SELECT COUNT(*) FROM actions").fetchone()[0] == 1


def test_settled_for_returns_earlier_turn_move(store: TempStore) -> None:
    thread, turn3, turn4 = new_thread(), new_turn(), new_turn()
    moved = _action(
        thread,
        turn3,
        "moved",
        "159",
        records={"appointment": "159", "slot": "56", "old_slot": "159"},
        before={"date": "2026-10-22", "window": "08:00-12:00", "technician": "Marta Kowalski"},
        after={
            "date": "2026-10-19",
            "window": "08:00-12:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "Synthetic fee line",
        },
        at=DEMO_START,
    )
    promise = Promise(policy_row="R26.unstaffed", text="We will call you Monday.", due_at=NOW, due_label=None)
    read_at = DEMO_START + timedelta(minutes=2)
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(conversation(thread))
        tx.core.actions.record(moved)
        tx.cases.cases.insert(case_row(thread, 9, due_at=NOW + timedelta(hours=2)))
        tx.cases.promises.insert(case_ref(9), promise, DEMO_START)
        assert tx.core.actions.record(moved) == moved  # retried turn 3 writes nothing new
        tx.commit()
    with store.uow() as tx:
        assert turn4 != turn3
        listed = tx.core.actions.for_thread(thread)
        settled = tx.core.settled_for(thread, read_at)
        assert tx.connection.execute("SELECT COUNT(*) FROM actions").fetchone()[0] == 1
        case_due = tx.cases.cases.get(case_ref(9))
    assert listed == (moved,)
    assert settled.actions == (moved,)
    assert settled.actions[0].before == moved.before
    assert settled.actions[0].after == moved.after
    assert settled.read_at == read_at
    assert settled.open_case is not None
    assert str(settled.open_case.case_ref) == "MHC-C-0009"
    assert settled.open_case.promise.text == "We will call you Monday."
    assert settled.open_case.promise.due_at == NOW
    assert case_due is not None
    assert case_due.due_at == NOW + timedelta(hours=2)


def test_turn_begin_finish_and_timeouts(store: TempStore) -> None:
    thread, turn, other = new_thread(), new_turn(), new_thread()
    ids = turn_ids(thread, turn)
    done = turn_record()
    with store.uow(write=True) as tx:
        t = tx.core.turns
        assert t.begin(ids, NOW).status == "new"
        row = t.get(turn)
        assert row is not None
        assert (row.status, row.sequence) == ("running", 1)
        assert t.begin(ids, NOW).status == "running"
        t.finish(turn, done)
        again = t.begin(ids, NOW)
        assert (again.status, again.response) == ("completed", done.response)
        stored = t.get(turn)
        assert stored is not None
        assert stored.as_record() == done

        failed_turn = new_turn()
        fids = turn_ids(thread, failed_turn)
        assert t.begin(fids, NOW).status == "new"
        t.finish(failed_turn, turn_record("failed", degrade_reason="timeout", planner=False))
        assert t.begin(fids, NOW).status == "failed"
        refreshed = t.get(failed_turn)
        assert refreshed is not None
        assert refreshed.status == "running"
        assert t.timeouts_for(thread) == 1
        assert [r.sequence for r in t.for_thread(thread)] == [1, 2]

        hijack = t.begin(turn_ids(other, turn), NOW)  # same turn_id, another thread
        assert (hijack.status, hijack.response) == ("running", None)
        assert tx.connection.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == 2
        with pytest.raises(StorageError):
            t.finish(new_turn(), done)


def test_events_after_and_latest_of(store: TempStore) -> None:
    thread = new_thread()
    cs, ts = case_stream(case_ref(9)), thread_stream(thread)
    assert cs == "case:MHC-C-0009"
    assert ts == str(thread)
    with store.uow(write=True) as tx:
        e = tx.core.events
        a = e.append(cs, StreamEvent(type="demo_reset", payload={"n": 1}, at=NOW))
        b = e.append(ts, StreamEvent(type="message", at=NOW))
        c = e.append(cs, StreamEvent(type="case_updated", at=NOW))
        d = e.append(cs, StreamEvent(type="demo_reset", at=NOW))
        assert a < b < c < d
        after = e.after(cs, a)
        assert [r.id for r in after] == [c, d]
        assert all(r.stream == cs for r in after)
        assert [r.id for r in e.after(ts, 0)] == [b]
        assert e.latest_of(cs, "demo_reset") == d
        assert e.latest_of(cs, "nope") is None
        assert e.latest_id(thread_stream(new_thread())) == 0
        assert e.latest_id(cs) == d
        assert e.after(cs, a)[0].payload == {}
        assert e.after(cs, 0)[0].payload == {"n": 1}


def test_lookup_log_and_handoff_anchor(store: TempStore) -> None:
    thread, other_thread, turn = new_thread(), new_thread(), new_turn()
    with store.uow(write=True) as tx:
        m = tx.core.messages
        greeting = m.append(thread, "assistant", "hello", NOW)
        c1 = m.append(thread, "customer", "first", NOW, turn_id=turn)
        c2 = m.append(thread, "customer", "second", NOW, turn_id=turn)
        only_greeting = m.append(other_thread, "assistant", "hello", NOW)
        entry = LookupEntry.model_validate(
            {
                "tool": "kb_search",
                "record_ids": [],
                "passage_ids": ["kb/sample.md#1"],
                "result_seen": "synthetic",
                "message_id": c2,
                "turn_id": str(turn),
            }
        )
        first = tx.core.lookup_log.append(entry)
        second = tx.core.lookup_log.append(entry.model_copy(update={"message_id": c1}))
        rows = tx.core.lookup_log.for_thread(thread)
        assert [r.id for r in rows] == [first, second]
        assert all(isinstance(r, LookupRow) and r.thread_id == thread for r in rows)
        assert (rows[0].message_id, rows[0].passage_ids) == (c2, entry.passage_ids)
        with pytest.raises(StorageError) as err:
            tx.core.lookup_log.append(entry.model_copy(update={"message_id": 999999}))
        assert err.value.table == "lookup_log"
        assert m.handoff_anchor(thread) == c2
        assert m.handoff_anchor(other_thread) == only_greeting
        assert greeting < c1


def test_cross_ticket_reads(store: TempStore) -> None:
    thread = new_thread()
    with store.uow(write=True) as tx:
        tx.connection.execute(
            "UPDATE invoices SET amount_cents = amount_cents + 100 WHERE invoice_id = 'INV-204411'"
        )
        tx.commit()
    with store.uow(write=True) as tx:
        r = tx.core.reads
        invoice = r.invoice(invoice_id("INV-204411"))
        assert invoice is not None
        assert invoice.amount_cents == 47900
        appt = r.appointment(159)
        assert appt is not None
        assert (appt.slot_id, appt.technician) == (159, "Marta Kowalski")
        assert "issue_description" not in type(appt).model_fields
        customer = r.customer(customer_id("MHC-10001"))
        assert customer is not None
        assert customer.membership_tier == "standard"
        assert r.invoice(invoice_id("INV-999999")) is None
        blank = r.identity_state(thread)
        assert (blank.status, blank.tries_left, blank.codes_sent) == ("not_checked", 3, 0)

        c = tx.connection
        c.execute(
            "INSERT INTO identity_threads (thread_id, status, customer_id, masked_hint, verified_at, updated_at) "
            "VALUES (?, 'verified', 'MHC-10001', 'synthetic hint', '2026-10-16T16:00:00+00:00', '2026-10-16T16:00:00+00:00')",
            (str(thread),),
        )
        for tries, exp in ((3, "2026-10-16T15:10:00+00:00"), (2, "2026-10-16T15:40:00+00:00")):
            c.execute(
                "INSERT INTO identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, "
                "tries_left, inbox_message_id) VALUES (?, 'MHC-10001', ?, 'inbox', '2026-10-16T15:00:00+00:00', ?, ?, 1)",
                (str(thread), uuid4().hex, exp, tries),
            )
        state = r.identity_state(thread)
        assert (state.status, state.codes_sent, state.tries_left) == ("verified", 2, 2)
        assert state.code_expires_at is not None
        assert state.code_expires_at.isoformat() == "2026-10-16T15:40:00+00:00"
        assert str(state.customer_id) == "MHC-10001"
        c.execute("INSERT INTO flags (status) VALUES ('new')")
        c.execute("INSERT INTO flags (status) VALUES ('reviewed')")
        assert r.new_flags_count() == 1


def test_storage_error_hides_value(store: TempStore, caplog: pytest.LogCaptureFixture) -> None:
    sentinel = "sentinel-" + uuid4().hex
    thread, turn = new_thread(), new_turn()
    a = _action(thread, turn, "booked", sentinel)
    a2 = _action(thread, turn, "booked", sentinel, after={"date": "2026-10-19"})
    caplog.set_level(logging.DEBUG)
    with store.uow(write=True) as tx:
        tx.core.actions.record(a)
        with pytest.raises(StorageError) as err:
            tx.core.actions.record(a2)
    exc = err.value
    for text in (str(exc), repr(exc), caplog.text):
        assert sentinel not in text
    assert "actions" in str(exc)
    assert "UNIQUE" in str(exc)
    assert exc.__context__ is None
    assert exc.__cause__ is None


def test_fail_running_sweeps_every_running_row(store: TempStore) -> None:
    thread = new_thread()
    t1, t2, t3 = new_turn(), new_turn(), new_turn()
    with store.uow(write=True) as tx:
        t = tx.core.turns
        for n, tid in enumerate((t1, t2, t3)):
            t.begin(turn_ids(thread, tid), NOW + timedelta(seconds=n))
        t.finish(t3, turn_record())
        swept = t.fail_running()
        rows = {tid: t.get(tid) for tid in (t1, t2, t3)}
        for tid, row in rows.items():
            assert row is not None
            print(tid, row.status, row.path, row.outcome, row.degrade_reason)
        assert set(swept) == {t1, t2}
        for tid in (t1, t2):
            row = rows[tid]
            assert row is not None
            assert (row.status, row.path, row.outcome, row.degrade_reason) == (
                "failed",
                "degraded",
                "degraded_handoff",
                "timeout",
            )
        done = rows[t3]
        assert done is not None
        assert (done.status, done.path, done.outcome, done.degrade_reason) == (
            "completed",
            "talk",
            "answered",
            None,
        )
        assert t.fail_running() == ()
