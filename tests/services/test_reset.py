"""AEA-31: all-or-nothing reset and demo seed (AC-1…AC-13, PA-1…PA-3). Synthetic data only."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import secrets
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import CaseRow, ConversationRow, EndedThread
from meridian.domain.common import CaseRef, ThreadId
from meridian.domain.staff import DemoRole, LoginSession
from meridian.policy.handoff import DUE_SOON_WINDOW, UNOWNED_AFTER, case_due_at, promise_for
from meridian.policy.texts import TEXTS, TextId
from meridian.ports.runtime import UnitOfWork
from meridian.services.reset import (
    CHICAGO,
    SEED_AGENT_VERSION,
    SEED_CASES,
    SEED_COUNT,
    SEED_DEMO_SESSION,
    ResetClock,
    ResetDone,
    ResetFailed,
    seed_demo,
    seed_first_boot,
)
from meridian.services.reset_gate import ResetAlreadyRunning
from meridian.web.deps import get_login_session, get_uow_factory, owned_thread
from meridian.web.errors import ApiProblem, handle_api_problem
from tests.services.reset_support import (
    ISSUED_TABLES,
    WALL,
    Dirty,
    RecordingAssembler,
    count,
    demo_store,
    fake_format_clock,
    issued_rows,
    login_session,
    make_dirty_demo,
    make_service,
    new_request_id,
    rows,
    seed_fn,
    sha256_file,
    snapshot,
)

SERVICE_FILE = Path(__file__).resolve().parents[2] / "src/meridian/services/reset.py"


class _Boom(Exception):
    pass


def _reset(svc: Any, role: DemoRole | None = None, session_id: Any = None) -> ResetDone | ResetFailed:
    result: ResetDone | ResetFailed = svc.reset(
        WALL, request_id=new_request_id(), session_id=session_id, role=role
    )
    return result


def _done(result: ResetDone | ResetFailed) -> ResetDone:
    assert isinstance(result, ResetDone)
    return result


def test_reset_restores_working_copy() -> None:
    with demo_store() as (store, cp):
        h0 = sha256_file(store.issued_path)
        make_dirty_demo(store, cp)
        svc, _ = make_service(store, cp)
        _done(_reset(svc, DemoRole.SUPERVISOR))
        for table in ISSUED_TABLES:
            assert rows(store.db_path, f"SELECT * FROM {table} ORDER BY rowid") == issued_rows(  # noqa: S608
                store.issued_path, table
            ), table
        issued_seq = {r[0]: r[1] for r in issued_rows(store.issued_path, "sqlite_sequence")}
        copy_seq = {
            r[0]: r[1]
            for r in rows(store.db_path, "SELECT name, seq FROM sqlite_sequence")
            if r[0] in ISSUED_TABLES
        }
        assert copy_seq == issued_seq
        issued_max = max(r[0] for r in issued_rows(store.issued_path, "appointments"))
        with store.uow(write=True) as tx:
            cur = tx.connection.execute(
                "INSERT INTO appointments (slot_id, customer_id, created_at) VALUES (1, 'MHC-10004', '2026-10-16')"
            )
            assert cur.lastrowid == issued_max + 1 == 160
        assert sha256_file(store.issued_path) == h0


def _after(
    orig: Callable[..., Any], only: Callable[[tuple[Any, ...]], bool] | None = None
) -> Callable[..., Any]:
    def wrapped(self: Any, *a: Any, **k: Any) -> Any:
        out = orig(self, *a, **k)
        if only is None or only(a):
            raise _Boom
        return out

    return wrapped


STEPS = [
    "restore",
    "clear_demo_tables",
    "demo_state_reset",
    "demo_reset_append",
    "seed_demo",
    "reset_event",
    "seed_event",
    "commit",
]


@pytest.mark.parametrize("step", STEPS)
def test_reset_all_or_nothing(step: str, monkeypatch: pytest.MonkeyPatch) -> None:
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp)
        kwargs: dict[str, Any] = {}
        with store.uow() as probe:
            core_reset = type(probe.core.reset)
            demo_state = type(probe.cases.demo_state)
            events = type(probe.core.events)
            records = type(probe.cases.records)
            uow_cls = type(probe)
        import functools

        from meridian.adapters.sqlite.migrate import restore_working_copy

        real_restore = functools.partial(restore_working_copy, issued_path=store.issued_path)
        if step == "restore":

            def restore(tx: UnitOfWork) -> None:
                real_restore(tx)
                raise _Boom

            kwargs["restore"] = restore
        elif step == "clear_demo_tables":
            monkeypatch.setattr(core_reset, "clear_demo_tables", _after(core_reset.clear_demo_tables))
        elif step == "demo_state_reset":
            monkeypatch.setattr(demo_state, "reset", _after(demo_state.reset))
        elif step == "demo_reset_append":
            monkeypatch.setattr(events, "append", _after(events.append, lambda a: a[1].type == "demo_reset"))
        elif step == "seed_demo":

            def seed(tx: UnitOfWork) -> int:
                seed_fn()(tx)
                raise _Boom

            kwargs["seed"] = seed
        elif step == "reset_event":
            monkeypatch.setattr(records, "reset_event", _after(records.reset_event))
        elif step == "seed_event":
            monkeypatch.setattr(records, "seed_event", _after(records.seed_event))
        else:

            def boom_commit(self: Any) -> None:
                raise _Boom

            monkeypatch.setattr(uow_cls, "commit", boom_commit)
        svc, gate = make_service(store, cp, **kwargs)
        before = snapshot(store, cp)
        result = _reset(svc)
        assert result == ResetFailed()
        assert result.code == "RESET_FAILED"
        assert snapshot(store, cp) == before
        assert gate.held() is False
        monkeypatch.undo()
        svc2, _ = make_service(store, cp)
        _done(_reset(svc2))


def test_checkpoint_commit_failure_residual_window() -> None:
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp)

        @contextmanager
        def clearing() -> Iterator[None]:
            yield
            raise RuntimeError("checkpoint commit failed")

        svc, gate = make_service(store, cp, clearing=clearing)
        _done(_reset(svc))
        newest = rows(
            store.db_path, "SELECT checkpoints_cleared FROM reset_events ORDER BY at_wall DESC, rowid DESC"
        )
        flags = [r[0] for r in newest]
        assert 0 in flags
        assert rows(store.db_path, "SELECT COUNT(*) FROM cases WHERE case_ref='MHC-C-0009'")[0][0] == 0
        assert count(store.db_path, "cases") == SEED_COUNT
        for table in ISSUED_TABLES:
            assert rows(store.db_path, f"SELECT * FROM {table} ORDER BY rowid") == issued_rows(  # noqa: S608
                store.issued_path, table
            )
        assert rows(store.db_path, "SELECT demo_now, staffing FROM demo_state")[0][1] == "nobody_online"
        ended = {r[0] for r in rows(store.db_path, "SELECT thread_id FROM ended_threads")}
        left = {r[0] for r in rows(cp.path, "SELECT thread_id FROM checkpoints")}
        assert left
        assert left <= ended
        assert gate.held() is False


def _blocking_seed(started: threading.Event, release: threading.Event) -> Callable[[UnitOfWork], int]:
    inner = seed_fn()

    def blocking(tx: UnitOfWork) -> int:
        started.set()
        release.wait(10)
        return inner(tx)

    return blocking


def test_concurrent_reset_refused() -> None:
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp)
        started, release = threading.Event(), threading.Event()
        svc, _ = make_service(store, cp, seed=_blocking_seed(started, release))
        out: list[Any] = []
        t1 = threading.Thread(target=lambda: out.append(_reset(svc)))
        before = count(store.db_path, "reset_events")
        t1.start()
        try:
            assert started.wait(5)
            with pytest.raises(ResetAlreadyRunning):
                _reset(svc)
        finally:
            release.set()
            t1.join(10)
        assert isinstance(out[0], ResetDone)
        assert count(store.db_path, "reset_events") == before + 1


def test_writer_waits_for_reset_lock() -> None:
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp)
        started, release, done = threading.Event(), threading.Event(), threading.Event()
        svc, _ = make_service(store, cp, seed=_blocking_seed(started, release))
        stamps: dict[str, float] = {}
        new_thread = ThreadId(str(uuid4()))

        def reset_job() -> None:
            _reset(svc)
            stamps["reset"] = time.monotonic()

        def writer_job() -> None:
            with store.uow(write=True) as tx:
                tx.core.conversations.insert(
                    ConversationRow(
                        thread_id=new_thread,
                        demo_session="writer",
                        run_tag="live",
                        agent_version="test",
                        started_at=DEMO_START,
                    )
                )
                tx.commit()
            stamps["writer"] = time.monotonic()
            done.set()

        t1 = threading.Thread(target=reset_job)
        t2 = threading.Thread(target=writer_job)
        t1.start()
        try:
            assert started.wait(5)
            t2.start()
            time.sleep(0.5)
            assert done.is_set() is False
        finally:
            release.set()
            t1.join(10)
            t2.join(10)
        with store.uow() as tx:
            found = tx.core.conversations.lookup(str(new_thread))
        assert isinstance(found, ConversationRow)
        assert count(store.db_path, "reset_events") >= 2
        # W is a live row, not a tombstone: it committed after the reset did (the reset tombstones every earlier row)
        assert "reset" in stamps and "writer" in stamps


def test_reset_ends_open_chats() -> None:
    with demo_store() as (store, cp):
        dirty = make_dirty_demo(store, cp, open_chats=2)
        svc, _ = make_service(store, cp)
        done = _done(_reset(svc))
        assert done.open_chats_ended == 2
        assert done.roles_reset == 2
        reset_id = rows(store.db_path, "SELECT reset_id FROM reset_events ORDER BY rowid DESC")
        stored = rows(
            store.db_path, "SELECT reset_id FROM reset_events WHERE open_chats_ended = 2 AND roles_reset = 2"
        )
        assert reset_id and len(stored) == 1
        expected = {
            "speaker": {"kind": "event", "display_name": None},
            "line": TEXTS[TextId.DEMO_RESET],
        }
        for tid in dirty.open_threads:
            ev = rows(
                store.db_path,
                "SELECT payload, id FROM events WHERE stream = ? AND type = 'demo_reset'",
                (str(tid),),
            )
            assert len(ev) == 1
            assert json.loads(ev[0][0]) == expected
            assert ev[0][1] > dirty.max_event_id
        case_ev = rows(
            store.db_path,
            "SELECT payload FROM events WHERE stream = 'case:MHC-C-0009' AND type = 'demo_reset'",
        )
        assert len(case_ev) == 1
        assert json.loads(case_ev[0][0]) == {"line": TEXTS[TextId.DEMO_RESET]}
        seed_threads = [r[0] for r in rows(store.db_path, "SELECT thread_id FROM conversations")]
        for tid_text in seed_threads:
            assert not rows(
                store.db_path, "SELECT 1 FROM events WHERE stream = ? AND type = 'demo_reset'", (tid_text,)
            )
        with store.uow() as tx:
            for tid in dirty.open_threads:
                found = tx.core.conversations.lookup(str(tid))
                assert isinstance(found, EndedThread)
                assert found.reason == "demo_reset"
                assert found.reset_id == stored[0][0]


def test_ended_thread_answers_session_ended() -> None:
    with demo_store() as (store, cp):
        dirty = make_dirty_demo(store, cp)
        svc, _ = make_service(store, cp)
        holder: dict[str, LoginSession] = {"session": dirty.sessions["customer"]}
        other = login_session(DemoRole.CUSTOMER)
        app = FastAPI()
        app.add_exception_handler(ApiProblem, handle_api_problem)

        @app.get("/t/{thread_id}")
        def route(thread_id: ThreadId = Depends(owned_thread)) -> dict[str, str]:  # noqa: B008
            return {"ok": "yes"}

        def session_from_holder() -> LoginSession:
            return holder["session"]

        def uow_factory() -> Any:
            return store.uow

        app.dependency_overrides[get_login_session] = session_from_holder
        app.dependency_overrides[get_uow_factory] = uow_factory
        client = TestClient(app)
        path = f"/t/{dirty.open_threads[0]}"
        assert client.get(path).status_code == 200
        _done(_reset(svc))
        gone = client.get(path)
        assert gone.status_code == 410
        assert gone.json()["error"]["code"] == "SESSION_ENDED"
        assert gone.json()["error"]["details"] == {"reason": "demo_reset"}
        holder["session"] = other
        stranger = client.get(path)
        unknown = client.get(f"/t/{uuid4()}")
        assert stranger.status_code == 404
        assert stranger.json()["error"]["code"] == "SESSION_NOT_FOUND"

        def strip(body: dict[str, Any]) -> dict[str, Any]:
            return {k: v for k, v in body.items() if k != "request_id"}

        assert strip(stranger.json()) == strip(unknown.json())


def test_reset_restores_clock_and_staffing() -> None:
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp)
        svc, _ = make_service(store, cp)
        done = _done(_reset(svc))
        with store.uow() as tx:
            state = tx.cases.demo_state.get()
        assert state.demo_now == DEMO_START
        assert state.staffing == "nobody_online"
        label, date_label = fake_format_clock(DEMO_START)
        assert done.clock == ResetClock(now=DEMO_START, label=label, date_label=date_label)


def test_reset_clears_codes_keeps_ops_records() -> None:
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp)
        kept = (
            "spend_ledger",
            "health_events",
            "deploy_records",
            "eval_runs",
            "eval_case_results",
            "job_runs",
            "demo_events",
        )
        before = {t: count(store.db_path, t) for t in kept}
        resets, seeds, ended = (
            count(store.db_path, t) for t in ("reset_events", "seed_events", "ended_threads")
        )
        convs = count(store.db_path, "conversations")
        svc, _ = make_service(store, cp)
        _done(_reset(svc))
        for t in ("identity_codes", "demo_inbox", "identity_threads", "flags"):
            assert count(store.db_path, t) == 0, t
        assert {t: count(store.db_path, t) for t in kept} == before
        assert count(store.db_path, "reset_events") == resets + 1
        assert count(store.db_path, "seed_events") == seeds + 1
        assert count(store.db_path, "ended_threads") == ended + convs
        sessions = rows(store.db_path, "SELECT role, role_reset_pending FROM staff_sessions")
        assert len(sessions) == 3
        assert all(r[0] == "customer" for r in sessions)
        assert sorted(r[1] for r in sessions) == [0, 1, 1]


def _seed_once(store: Any, rec: RecordingAssembler | None = None) -> RecordingAssembler:
    rec = rec or RecordingAssembler()
    with store.uow(write=True) as tx:
        n = seed_demo(tx, assembler=rec)
        tx.commit()
    assert n == SEED_COUNT == 4
    return rec


def test_seed_cases_labelled_and_counted() -> None:
    with demo_store() as (store, _cp):
        rec = _seed_once(store)
        db = store.db_path
        got = rows(db, "SELECT case_ref, seed, lifecycle, created_at, thread_id FROM cases ORDER BY case_ref")
        assert [r[0] for r in got] == [s.ref for s in SEED_CASES]
        assert all(r[1] == 1 and r[2] == "unassigned" for r in got)
        phone = issued_phone(store, "MHC-10002")
        with store.uow() as tx:
            for seed in SEED_CASES:
                ref = CaseRef(seed.ref)
                assert seed.created_at < DEMO_START
                conv = rows(
                    db,
                    "SELECT c.run_tag, c.live_state, c.demo_session FROM conversations c "
                    "JOIN cases k ON k.thread_id = c.thread_id WHERE k.case_ref = ?",
                    (seed.ref,),
                )
                assert conv == [("seed", "closed", SEED_DEMO_SESSION)]
                assert tx.cases.promises.current(ref) is not None
                brief = tx.cases.briefs.get(ref)
                assert brief is not None and brief.status == "ready"
        lookups = rows(
            db,
            "SELECT k.case_ref, l.tool, l.record_ids FROM lookup_log l JOIN cases k ON k.thread_id = l.thread_id "
            "ORDER BY k.case_ref",
        )
        assert [(r[0], r[1], json.loads(r[2])) for r in lookups] == [
            ("MHC-C-0005", "read_invoices", ["INV-200037"]),
            ("MHC-C-0007", "read_invoices", ["INV-204411"]),
        ]
        fups = rows(
            db,
            "SELECT case_ref, channel, contact_window, on_record, destination, destination_label FROM followups",
        )
        assert len(fups) == 1
        assert fups[0][:5] == ("MHC-C-0007", "phone", "morning", 1, None)
        assert fups[0][5].endswith("".join(c for c in phone if c.isdigit())[-2:])
        assert len(rec.extractions) == 4 and all(c is None for c in rec.checks)
        for (_case, state, _lk), extraction in zip(rec.assembled, rec.extractions, strict=True):
            assert extraction is not None
            for quote in (*extraction.needs, *extraction.claims):
                row = rows(
                    db, "SELECT role, text, thread_id FROM messages WHERE id = ?", (quote.message_id,)
                )[0]
                assert row[0] == "customer" and quote.text in row[1]
                assert row[2] == str(state.thread_id)


def issued_phone(store: Any, customer_id: str) -> str:
    for r in issued_rows(store.issued_path, "customers"):
        if r[0] == customer_id:
            return str(r[2])
    raise AssertionError("customer not in issued data")


def test_seed_promises_from_table() -> None:
    with demo_store() as (store, _cp):
        with store.uow(write=True) as tx:
            tx.cases.demo_state.set_now(datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO))
            tx.commit()
        _seed_once(store)
        expected_due = {
            "MHC-C-0005": datetime(2026, 10, 15, 19, 0, tzinfo=CHICAGO),
            "MHC-C-0006": datetime(2026, 10, 19, 19, 0, tzinfo=CHICAGO),
            "MHC-C-0007": datetime(2026, 10, 19, 19, 0, tzinfo=CHICAGO),
            "MHC-C-0008": None,
        }
        priorities = dict(zip(expected_due, ["P3", "P3", "P3", "P0"], strict=True))
        with store.uow() as tx:
            for seed in SEED_CASES:
                ref = CaseRef(seed.ref)
                current = tx.cases.promises.current(ref)
                assert current is not None
                promise = promise_for(seed.reason, "nobody_online", seed.created_at)
                assert current.promise == promise
                case = tx.cases.cases.get(ref)
                assert case is not None
                assert case.due_at == case_due_at(seed.reason, promise, None) == expected_due[seed.ref]
                assert case.priority == priorities[seed.ref]


def test_first_boot_seeds_once() -> None:
    with demo_store() as (store, _cp):
        assert seed_first_boot(store.uow, seed_fn(), WALL) == 4
        tables = ("cases", "conversations", "messages", "seed_events")
        before = {t: count(store.db_path, t) for t in tables}
        assert seed_first_boot(store.uow, seed_fn(), WALL) == 0
        assert {t: count(store.db_path, t) for t in tables} == before
        ev = rows(store.db_path, "SELECT reset_id, seed_count, label FROM seed_events")
        assert ev == [(None, 4, "demo seed")]


def test_next_live_ref_after_seeds() -> None:
    with demo_store() as (store, cp):
        _seed_once(store)
        with store.uow() as tx:
            assert tx.cases.refs.next_case_ref() == "MHC-C-0009"
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp)
        svc, _ = make_service(store, cp)
        _done(_reset(svc))
        with store.uow() as tx:
            assert tx.cases.refs.next_case_ref() == "MHC-C-0009"


def lane_for(case: CaseRow, now: datetime) -> str | None:
    """Test-local copy of cases.md section 5's lane rules (AEA-29's CaseService.oversight replaces it in AEA-52)."""
    if case.priority in ("P0", "P1"):
        return "p0_p1"
    if case.due_at and case.due_at < now:
        return "overdue"
    if case.due_at and case.due_at - now <= DUE_SOON_WINDOW:
        return "due_soon"
    if case.lifecycle == "unassigned" and now - case.created_at >= UNOWNED_AFTER:
        return "unowned"
    if case.wake_up_at and case.wake_up_at < now:
        return "stuck_waiting"
    return None


def test_seed_lanes_at_demo_start() -> None:
    with demo_store() as (store, _cp):
        _seed_once(store)
        with store.uow() as tx:
            lanes = {}
            for seed in SEED_CASES:
                case = tx.cases.cases.get(CaseRef(seed.ref))
                assert case is not None
                lanes[seed.ref] = lane_for(case, DEMO_START)
        assert lanes == {
            "MHC-C-0005": "overdue",
            "MHC-C-0006": "unowned",
            "MHC-C-0007": "unowned",
            "MHC-C-0008": "p0_p1",
        }
        fup = rows(
            store.db_path, "SELECT channel, contact_window FROM followups WHERE case_ref = 'MHC-C-0007'"
        )
        assert fup == [("phone", "morning")]
        assert timedelta(minutes=46) == DEMO_START - SEED_CASES[1].created_at
        assert timedelta(minutes=36) == DEMO_START - SEED_CASES[2].created_at


_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_LONG_DIGITS = re.compile(r"[0-9]{13,19}")
_SIX_DIGITS = re.compile(r"(?<![0-9A-Za-z-])[0-9]{6}(?![0-9])")


def test_seed_holds_no_codes_or_cards() -> None:
    with demo_store() as (store, _cp):
        _seed_once(store)
        db = store.db_path
        queries = [
            "SELECT * FROM conversations WHERE run_tag = 'seed'",
            "SELECT * FROM messages",
            "SELECT * FROM lookup_log",
            "SELECT * FROM cases WHERE seed = 1",
            "SELECT * FROM promises",
            "SELECT * FROM followups",
            "SELECT * FROM case_briefs",
            "SELECT * FROM actions",
        ]
        for q in queries:
            for row in rows(db, q):
                text = _UUID.sub("", " ".join(str(v) for v in row))
                assert not _LONG_DIGITS.search(text), q
                assert not _SIX_DIGITS.search(text), q
        issued_ids = {r[0] for r in issued_rows(store.issued_path, "customers")}
        for (cid,) in rows(db, "SELECT customer_id FROM cases WHERE seed = 1 AND customer_id IS NOT NULL"):
            assert cid in issued_ids
        constants = [m for s in SEED_CASES for m in s.messages]
        for (body,) in rows(db, "SELECT text FROM messages WHERE role = 'customer'"):
            assert body in constants


def test_reset_and_seed_events() -> None:
    with demo_store() as (store, cp):
        dirty = make_dirty_demo(store, cp)
        sup = dirty.sessions["supervisor"]
        svc, _ = make_service(store, cp)
        rid = new_request_id()
        _done(svc.reset(WALL, request_id=rid, session_id=sup.session_id, role=DemoRole.SUPERVISOR))
        _done(_reset(svc))
        resets = rows(
            store.db_path,
            "SELECT reset_id, at_wall, asked_by_role, asked_by_session, request_id, restored_json, "
            "open_chats_ended, roles_reset, checkpoints_cleared FROM reset_events WHERE asked_by_role = 'supervisor'",
        )
        assert len(resets) == 1
        r = resets[0]
        assert r[3] == str(sup.session_id) and r[4] == str(rid)
        restored = json.loads(r[5])
        assert "conversations" in restored and all(isinstance(v, int) for v in restored.values())
        assert (r[6], r[7], r[8]) == (1, 2, 1)
        assert r[1].endswith("+00:00")
        operator = rows(
            store.db_path,
            "SELECT asked_by_role, asked_by_session FROM reset_events WHERE request_id != ? AND asked_by_role IS NULL",
            (str(rid),),
        )
        assert operator and operator[0] == (None, None)
        seeds = rows(store.db_path, "SELECT reset_id, seed_count, label, at_wall FROM seed_events")
        assert sum(1 for s in seeds if s[0] is None) == 1
        assert any(s[0] == r[0] for s in seeds)
        assert all(s[1] == 4 and s[2] == "demo seed" and s[3].endswith("+00:00") for s in seeds)
        assert len(seeds) == 3


def test_reset_records_hold_no_pii() -> None:
    with demo_store() as (store, cp):
        customer = next(r for r in issued_rows(store.issued_path, "customers") if r[0] == "MHC-10002")
        name, phone = str(customer[1]), str(customer[2])
        token = secrets.token_urlsafe(16)
        message = f"This is {name}, call me on {phone}"
        make_dirty_demo(store, cp, customer_message=message)
        with store.uow(write=True) as tx:
            tx.connection.execute(
                "INSERT INTO staff_sessions (token_hash, session_id, role) VALUES (?, ?, 'customer')",
                (hashlib.sha256(token.encode()).hexdigest(), str(uuid4())),
            )
            tx.commit()
        svc, _ = make_service(store, cp)
        _done(_reset(svc, DemoRole.SUPERVISOR))
        for table in ("reset_events", "seed_events"):
            row = rows(store.db_path, f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 1")[0]  # noqa: S608
            blob = "|".join(str(v) for v in row)
            for secret in (name.split()[0], phone, "".join(c for c in phone if c.isdigit()), token, message):
                assert secret not in blob, table


def test_reset_module_imports_no_adapter_callables() -> None:
    tree = ast.parse(SERVICE_FILE.read_text())
    banned = (
        "sqlite3",
        "meridian.adapters.sqlite.db",
        "meridian.adapters.sqlite.migrate",
        "meridian.adapters.checkpointer",
        "meridian.web",
        "meridian.agent",
        "meridian.services.handoff",
        "meridian.services.demo",
        "anthropic",
        "httpx",
    )
    sql = re.compile(r"(?i)\b(SELECT|INSERT|UPDATE|DELETE)\b\s")
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for name in names:
            assert not any(name == b or name.startswith(b + ".") for b in banned), name
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert not sql.search(node.value), node.value
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "now"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "datetime"
        ):
            raise AssertionError("datetime.now in reset.py")


def test_reset_rejects_naive_now() -> None:
    with demo_store() as (store, cp):
        svc, gate = make_service(store, cp)
        before = count(store.db_path, "reset_events")
        with pytest.raises(ValueError, match="aware"):
            svc.reset(datetime(2026, 10, 21, 19, 0), request_id=new_request_id(), session_id=None, role=None)
        assert gate.held() is False
        assert count(store.db_path, "reset_events") == before


_ = (Dirty, SEED_AGENT_VERSION)
