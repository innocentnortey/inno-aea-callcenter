"""AEA-10 AC-18 and PA-5: the case-store repositories."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from uuid import uuid4

import pytest

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.repos_cases import (
    DEMO_START,
    ActivityRow,
    CaseEventRow,
    DemoEventRow,
    FollowupRow,
    ResetEventRow,
    SeedEventRow,
)
from meridian.domain.handoff import BRIEF_KEYS, BRIEF_ORIGINS, BRIEF_TITLES, Brief, Promise
from meridian.domain.staff import DemoRole, StaffRole
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.adapters.sqlite.helpers import NOW, case_ref, case_row, conversation, customer_id, new_thread


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _brief(ref: int, thread: object, marker: str) -> Brief:
    headings: list[dict[str, object]] = [
        {
            "number": n + 1,
            "key": BRIEF_KEYS[n],
            "title": BRIEF_TITLES[n],
            "origin": BRIEF_ORIGINS[n],
            "checked": False,
            "items": [],
            "trimmed": False,
            "trim_note": marker if n == 0 else None,
            "not_generated": False,
        }
        for n in range(8)
    ]
    return Brief.model_validate(
        {
            "case_ref": str(case_ref(ref)),
            "thread_id": str(thread),
            "assembled_at": NOW,
            "status": "ready",
            "headings": headings,
        }
    )


def test_case_round_trip_keeps_both_dues(store: TempStore) -> None:
    thread = new_thread()
    case_due, customer_due = NOW + timedelta(hours=1), NOW + timedelta(days=2)
    row = case_row(
        thread,
        9,
        due_at=case_due,
        seed=True,
        version=3,
        customer_id="MHC-10001",
        change_request={"change": "move"},
        owner_role="representative",
        owner_since=NOW,
        safety_kind=None,
    )
    promise = Promise(
        policy_row="R26.unstaffed",
        text="  stored exactly  ".strip(),
        due_at=customer_due,
        due_label="Monday",
        extra_lines=("a", "b"),
        live_queued=True,
    )
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(conversation(thread))
        tx.cases.cases.insert(row)
        tx.cases.promises.insert(row.case_ref, promise, NOW)
        got = tx.cases.cases.get(row.case_ref)
        current = tx.cases.promises.current(row.case_ref)
        assert got == row
        assert current is not None
        assert current.promise == promise
        assert current.promise.due_at == customer_due
        assert got is not None
        assert got.due_at == case_due
        assert tx.cases.cases.get_for_thread_open(thread) == row
        assert tx.cases.cases.list_for_thread(thread) == (row,)
        assert tx.cases.cases.list_for_customer(customer_id("MHC-10001")) == (row,)
        assert tx.cases.cases.list_open() == (row,)
        assert tx.cases.cases.update_versioned(row.case_ref, 3, lifecycle="resolved") == 4
        assert tx.cases.cases.list_open() == ()
        assert tx.cases.cases.get_for_thread_open(thread) is None


def test_case_events_append_and_exists(store: TempStore) -> None:
    thread = new_thread()
    ref = case_ref(9)
    with store.uow(write=True) as tx:
        tx.cases.cases.insert(case_row(thread))
        ev = CaseEventRow(
            case_ref=ref,
            kind="overdue",
            key="k1",
            actor_role="system",
            job_run_id="j1",
            detail={"n": 1},
            at=NOW,
        )
        first = tx.cases.case_events.append(ev)
        tx.cases.case_events.append(ev.model_copy(update={"key": "", "actor_role": "ai"}))
        tx.cases.case_events.append(ev.model_copy(update={"key": ""}))  # empty keys never collide
        assert tx.cases.case_events.exists(ref, "overdue", "k1")
        assert not tx.cases.case_events.exists(ref, "overdue", "k2")
        rows = tx.cases.case_events.list_for_case(ref)
        assert rows[0] == ev.model_copy(update={"id": first})
        assert [r.actor_role for r in rows] == ["system", "ai", "system"]
        with pytest.raises(StorageError) as err:
            tx.cases.case_events.append(ev)
        assert err.value.constraint == "UNIQUE"


def test_promise_text_history_and_list_open_past(store: TempStore) -> None:
    thread = new_thread()
    ref = case_ref(9)
    text = "We will call you back by 7 pm Monday, between 8 and 12."
    with store.uow(write=True) as tx:
        p = tx.cases.promises
        tx.cases.cases.insert(case_row(thread))
        assert p.current(ref) is None
        assert p.set_status(ref, "kept", NOW, "x") is False
        p.insert(ref, Promise(policy_row="R1", text=text, due_at=NOW, due_label=None), DEMO_START)
        assert [r.promise.text for r in p.history(ref)] == [text]
        assert [r.case_ref for r in p.list_open_past(NOW + timedelta(seconds=1))] == [ref]
        assert p.list_open_past(NOW) == []
        assert p.set_status(ref, "changed", NOW, "customer moved it") is True
        p.insert(
            ref,
            Promise(policy_row="R2", text="new text", due_at=NOW + timedelta(days=1), due_label=None),
            NOW,
        )
        history = p.history(ref)
        assert [r.status for r in history] == ["changed", "open"]
        assert history[0].status_reason == "customer moved it"
        assert p.current(ref) == history[1]
        assert p.set_status(ref, "kept", NOW, "done") is True
        assert [r.status for r in p.history(ref)] == ["changed", "kept"]
        assert p.list_open_past(NOW + timedelta(days=5)) == []


def test_followups_and_activities(store: TempStore) -> None:
    thread = new_thread()
    ref = case_ref(9)
    with store.uow(write=True) as tx:
        tx.cases.cases.insert(case_row(thread))
        fu = FollowupRow(
            case_ref=ref,
            thread_id=thread,
            channel="email",
            destination_label="the email on file",
            destination="x@example.test",
            on_record=True,
            window="morning",
            saved_line="saved",
            updated_at=NOW,
        )
        tx.cases.followups.upsert(fu)
        assert tx.cases.followups.get(ref) == fu
        newer = fu.model_copy(
            update={"window": "any", "channel": "phone", "updated_at": NOW + timedelta(minutes=1)}
        )
        tx.cases.followups.upsert(newer)
        assert tx.cases.followups.get(ref) == newer
        assert tx.connection.execute("SELECT COUNT(*) FROM followups").fetchone()[0] == 1
        assert tx.cases.followups.get(case_ref(10)) is None
        a2 = ActivityRow(
            case_ref=ref,
            kind="email",
            outcome="left_message",
            actor_role=StaffRole.SUPERVISOR,
            at=NOW + timedelta(minutes=2),
        )
        a1 = ActivityRow(
            case_ref=ref,
            kind="call",
            outcome="reached",
            note="n",
            actor_role=StaffRole.REPRESENTATIVE,
            at=NOW,
        )
        tx.cases.activities.insert(a2)
        tx.cases.activities.insert(a1)
        listed = tx.cases.activities.list_for_case(ref)
        assert [r.kind for r in listed] == ["call", "email"]
        assert listed[0].note == "n"


def test_briefs_upsert_replaces(store: TempStore) -> None:
    thread = new_thread()
    ref = case_ref(9)
    with store.uow(write=True) as tx:
        tx.cases.cases.insert(case_row(thread))
        assert tx.cases.briefs.get(ref) is None
        tx.cases.briefs.upsert(_brief(9, thread, "first"), NOW)
        second = _brief(9, thread, "second")
        tx.cases.briefs.upsert(second, NOW + timedelta(minutes=1))
        assert tx.cases.briefs.get(ref) == second
        assert tx.connection.execute("SELECT COUNT(*) FROM case_briefs").fetchone()[0] == 1


def test_demo_state_defaults_and_reset(store: TempStore) -> None:
    with store.uow(write=True) as tx:
        d = tx.cases.demo_state
        fresh = d.get()
        assert (fresh.demo_now, fresh.staffing) == (DEMO_START, "nobody_online")
        assert tx.connection.execute("SELECT COUNT(*) FROM demo_state").fetchone()[0] == 0
        d.set_staffing("simulated_on_shift")
        assert (d.get().demo_now, d.get().staffing) == (DEMO_START, "simulated_on_shift")
        later = DEMO_START + timedelta(days=1)
        d.set_now(later)
        assert (d.get().demo_now, d.get().staffing) == (later, "simulated_on_shift")
        d.reset()
        assert (d.get().demo_now, d.get().staffing) == (DEMO_START, "nobody_online")
        assert tx.connection.execute("SELECT COUNT(*) FROM demo_state").fetchone()[0] == 1


def test_demo_events_and_job_runs_latest(store: TempStore) -> None:
    with store.uow(write=True) as tx:
        tx.cases.demo_events.insert(
            DemoEventRow(
                demo_event_id="de-" + uuid4().hex[:6],
                at_wall=NOW,
                kind="clock_advanced",
                step="next_morning",
                demo_before="2026-10-16T15:00:00+00:00",
                demo_after="2026-10-17T14:00:00+00:00",
                became_overdue=1,
                converted_cases=0,
                request_id="r1",
                role="owner",
            )
        )
        assert tx.connection.execute("SELECT became_overdue, role FROM demo_events").fetchone() == (
            1,
            "owner",
        )
        j = tx.cases.job_runs
        assert j.latest() is None
        j.start("j1", started_wall_at=NOW, demo_now=DEMO_START)
        j.start("j2", started_wall_at=NOW + timedelta(minutes=1), demo_now=DEMO_START)
        latest = j.latest()
        assert latest is not None
        assert (latest.job_run_id, latest.status, latest.finished_wall_at) == ("j2", "started", None)
        j.finish(
            "j2",
            "completed",
            {"overdue": 2, "converted": None},
            None,
            finished_wall_at=NOW + timedelta(minutes=2),
        )
        done = j.latest()
        assert done is not None
        assert done.counts == {"overdue": 2, "converted": None}
        assert done.finished_wall_at == NOW + timedelta(minutes=2)
        with pytest.raises(StorageError):
            j.finish("nope", "failed", {}, "err")


def test_reset_and_seed_records(store: TempStore) -> None:
    thread = new_thread()
    with store.uow(write=True) as tx:
        r = tx.cases.records
        assert not r.seed_rows_present()
        assert r.latest_reset_event() is None
        assert r.latest_seed_event() is None
        reset = ResetEventRow(
            reset_id="r1",
            at_wall=NOW,
            asked_by_role=DemoRole.SUPERVISOR,
            asked_by_session="s1",
            request_id="req",
            restored={"appointments": 159},
            open_chats_ended=2,
            roles_reset=1,
        )
        r.reset_event(reset)
        assert r.latest_reset_event() == reset
        r.set_checkpoints_cleared("r1", False)
        latest = r.latest_reset_event()
        assert latest is not None
        assert latest.checkpoints_cleared is False
        with pytest.raises(StorageError):
            r.set_checkpoints_cleared("missing", True)
        r.seed_event(SeedEventRow(seed_event_id="s1", at_wall=NOW, reset_id="r1", seed_count=4))
        seed = r.latest_seed_event()
        assert seed is not None
        assert (seed.label, seed.seed_count, seed.deploy_id) == ("demo seed", 4, None)
        tx.cases.cases.insert(case_row(thread, 5, seed=True))
        assert r.seed_rows_present()


def test_next_case_ref_after_seeds(store: TempStore) -> None:
    with store.uow(write=True) as tx:
        refs = tx.cases.refs
        assert refs.next_case_ref() == "MHC-C-0009"
        thread = new_thread()
        for n in (5, 6, 7, 8):
            tx.cases.cases.insert(case_row(thread, n, seed=True))
        assert refs.next_case_ref() == "MHC-C-0009"
        tx.cases.cases.insert(case_row(thread, 9))
        assert refs.next_case_ref() == "MHC-C-0010"


def test_update_versioned_conflict(store: TempStore) -> None:
    thread = new_thread()
    ref = case_ref(9)
    with store.uow(write=True) as tx:
        c = tx.cases.cases
        c.insert(case_row(thread))
        assert (
            c.update_versioned(ref, 1, lifecycle="claimed", owner_role="representative", updated_at=NOW) == 2
        )
        after = c.get(ref)
        assert after is not None
        assert (after.version, after.lifecycle) == (2, "claimed")
        assert c.update_versioned(ref, 1, lifecycle="resolved") is None  # stale
        unchanged = c.get(ref)
        assert unchanged == after
        assert c.update_versioned(case_ref(77), 1, lifecycle="resolved") is None
        with pytest.raises(ValueError, match="unknown case column"):
            c.update_versioned(ref, 2, thread_id="x")
        with pytest.raises(ValueError):
            c.update_versioned(ref, 2)
