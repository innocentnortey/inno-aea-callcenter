# ruff: noqa: S608  (table names below come from module constants, never from input)
"""AEA-10 AC-1 to AC-6: first boot, restart, the issued file, restore and clear."""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from meridian.adapters.sqlite.migrate import (
    CLEARED_TABLES,
    ISSUED_TABLES,
    KEPT_TABLES,
    UPDATED_TABLES,
    WORKING_DB_NAME,
    migrate,
    restore_working_copy,
    schema_files,
)
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import StreamEvent, case_stream
from meridian.domain.actions import CompletedAction
from meridian.domain.handoff import Promise
from tests.fixtures.sqlite import ISSUED_DB, TempStore, temp_sqlite
from tests.unit.adapters.sqlite.helpers import (
    NOW,
    case_ref,
    case_row,
    conversation,
    new_thread,
    new_turn,
)

ISSUED_COUNTS = {
    "customers": 154,
    "technicians": 8,
    "appointment_slots": 528,
    "appointments": 159,
    "invoices": 81,
}


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scalar(store: TempStore, sql: str, *params: object) -> object:
    with store.uow() as tx:
        return tx.connection.execute(sql, params).fetchone()[0]


def _book_slot_56(store: TempStore) -> None:
    with store.uow(write=True) as tx:
        tx.connection.execute("UPDATE appointment_slots SET status='booked' WHERE slot_id=56")
        tx.connection.execute(
            "INSERT INTO appointments (slot_id, customer_id, issue_description, created_at) "
            "VALUES (56, 'MHC-10004', 'synthetic', '2026-10-16')"
        )
        tx.commit()


def test_first_boot_copies_issued_db_and_applies_schema(tmp_path: Path) -> None:
    db = tmp_path / WORKING_DB_NAME
    assert migrate(db, issued_path=ISSUED_DB) is True
    conn = sqlite3.connect(db)
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ISSUED_COUNTS}
    finally:
        conn.close()
    print(sorted(tables))
    assert set(ISSUED_TABLES + CLEARED_TABLES + UPDATED_TABLES + KEPT_TABLES) <= tables
    assert counts == ISSUED_COUNTS
    assert [p.name.split("_", 1)[0] for p in schema_files()] == ["00", "20", "40", "50", "60", "90", "95"]


def test_existing_working_copy_survives_restart(store: TempStore) -> None:
    thread, turn = new_thread(), new_turn()
    convo = conversation(thread)
    action = CompletedAction.model_validate(
        {
            "key": {
                "thread_id": str(thread),
                "turn_id": str(turn),
                "kind": "verified",
                "record_id": "MHC-10001",
            },
            "kind": "verified",
            "records": {"customer": "MHC-10001"},
            "at": NOW,
        }
    )
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(convo)
        tx.core.actions.record(action)
        tx.cases.cases.insert(case_row(thread))
        tx.commit()
    assert migrate(store.db_path, issued_path=ISSUED_DB) is False
    with store.uow() as tx:
        assert tx.core.conversations.lookup(str(thread)) == convo
        assert tx.core.actions.for_thread(thread) == (action,)
        assert tx.cases.cases.get(case_ref(9)) == case_row(thread)


def test_issued_file_never_written(store: TempStore) -> None:
    before = _sha(ISSUED_DB)
    sentinel = "sentinel-" + uuid4().hex
    thread = new_thread()
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(conversation(thread, demo_session=sentinel))
        tx.commit()
    with store.uow(write=True) as tx:
        restore_working_copy(tx, issued_path=ISSUED_DB)
        tx.commit()
    assert _sha(ISSUED_DB) == before
    assert _scalar(store, "SELECT COUNT(*) FROM conversations WHERE demo_session = ?", sentinel) == 1
    assert sentinel.encode() not in ISSUED_DB.read_bytes()
    for suffix in ("-wal", "-shm", "-journal"):
        assert not ISSUED_DB.with_name(ISSUED_DB.name + suffix).exists()


def test_restore_working_copy_restores_issued_tables(store: TempStore) -> None:
    _book_slot_56(store)
    with store.uow(write=True) as tx:
        tx.connection.execute(
            "INSERT INTO spend_ledger (recorded_at, cost_usd) VALUES ('2026-10-16T15:00:00+00:00', 0.5)"
        )
        tx.connection.execute(
            "INSERT INTO reset_events (reset_id, at_wall) VALUES (?, '2026-10-16T15:00:00+00:00')",
            ("r-" + uuid4().hex,),
        )
        tx.commit()
    assert _scalar(store, "SELECT status FROM appointment_slots WHERE slot_id=56") == "booked"
    with store.uow(write=True) as tx:
        restore_working_copy(tx, issued_path=ISSUED_DB)
        tx.commit()
    assert _scalar(store, "SELECT status FROM appointment_slots WHERE slot_id=56") == "open"
    assert _scalar(store, "SELECT MAX(appointment_id) FROM appointments") == 159
    with store.uow(write=True) as tx:
        cur = tx.connection.execute(
            "INSERT INTO appointments (slot_id, customer_id, created_at) VALUES (56, 'MHC-10004', '2026-10-16')"
        )
        assert cur.lastrowid == 160
    assert _scalar(store, "SELECT COUNT(*) FROM spend_ledger") == 1
    assert _scalar(store, "SELECT COUNT(*) FROM reset_events") == 1
    issued = sqlite3.connect(f"{ISSUED_DB.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        with store.uow() as tx:
            for table in ISSUED_TABLES:
                sql = f"SELECT * FROM {table} ORDER BY rowid"
                assert tx.connection.execute(sql).fetchall() == issued.execute(sql).fetchall(), table
            seq = tx.connection.execute("SELECT name FROM sqlite_sequence").fetchall()
        assert not {r[0] for r in seq} & set(ISSUED_TABLES)
    finally:
        issued.close()


def test_restore_rolls_back_with_caller(store: TempStore) -> None:
    _book_slot_56(store)
    with pytest.raises(RuntimeError), store.uow(write=True) as tx:
        restore_working_copy(tx, issued_path=ISSUED_DB)
        raise RuntimeError("boom")
    assert _scalar(store, "SELECT status FROM appointment_slots WHERE slot_id=56") == "booked"
    assert _scalar(store, "SELECT COUNT(*) FROM appointments WHERE appointment_id=160") == 1


def test_clear_demo_tables_matches_table_list(store: TempStore) -> None:
    open_thread, closed_thread = new_thread(), new_thread()
    turn = new_turn()
    ref = case_ref(9)
    ts = "2026-10-16T15:00:00+00:00"
    with store.uow(write=True) as tx:
        c = tx.connection
        tx.core.conversations.insert(conversation(open_thread))
        tx.core.conversations.insert(conversation(closed_thread, live_state="closed"))
        msg = tx.core.messages.append(open_thread, "customer", "synthetic", NOW, turn_id=turn)
        c.execute(
            "INSERT INTO lookup_log (thread_id, turn_id, message_id, tool, record_ids, passage_ids, result_seen) "
            "VALUES (?,?,?,?,?,?,?)",
            (str(open_thread), str(turn), msg, "kb_search", "[]", "[]", "synthetic"),
        )
        c.execute(
            "INSERT INTO check_events (thread_id, check_kind, turn_id, result) VALUES (?, 'gate', ?, 'pass')",
            (str(open_thread), str(turn)),
        )
        c.execute(
            "INSERT INTO actions (thread_id, turn_id, kind, record_id, records_json, at) "
            "VALUES (?,?,'verified','x','{}',?)",
            (str(open_thread), str(turn), ts),
        )
        c.execute(
            "INSERT INTO turns (turn_id, thread_id, request_id, run_tag, agent_version, sequence, received_at, status) "
            "VALUES (?,?,?, 'live','t',1,?, 'running')",
            (str(turn), str(open_thread), str(uuid4()), ts),
        )
        tx.core.events.append(case_stream(ref), StreamEvent(type="case_updated", at=NOW))
        tx.cases.cases.insert(case_row(open_thread))
        tx.cases.promises.insert(
            ref,
            Promise(policy_row="R26.unstaffed", text="synthetic promise", due_at=None, due_label=None),
            NOW,
        )
        c.execute(
            "INSERT INTO followups (case_ref, thread_id, channel, destination_label, on_record, contact_window, "
            "saved_line, updated_at) VALUES (?,?,'email','on file',1,'any','synthetic',?)",
            (str(ref), str(open_thread), ts),
        )
        c.execute(
            "INSERT INTO activities (case_ref, kind, outcome, actor_role, at) VALUES (?,'call','reached','supervisor',?)",
            (str(ref), ts),
        )
        c.execute(
            "INSERT INTO case_events (case_ref, kind, actor_role, at) VALUES (?, 'created', 'ai', ?)",
            (str(ref), ts),
        )
        c.execute(
            "INSERT INTO case_briefs (case_ref, thread_id, status, brief_json, updated_at) VALUES (?,?,'ready','{}',?)",
            (str(ref), str(open_thread), ts),
        )
        c.execute("INSERT INTO flags (case_ref, status) VALUES (?, 'new')", (str(ref),))
        c.execute(
            "INSERT INTO identity_threads (thread_id, status, updated_at) VALUES (?, 'located', ?)",
            (str(open_thread), ts),
        )
        c.execute(
            "INSERT INTO identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, tries_left, "
            "inbox_message_id) VALUES (?, 'MHC-10001', 'h', 'inbox', ?, ?, 3, 1)",
            (str(open_thread), ts, ts),
        )
        c.execute(
            "INSERT INTO demo_inbox (demo_session, thread_id, to_masked, sent_at, expires_at) VALUES ('s',?,'m',?,?)",
            (str(open_thread), ts, ts),
        )
        for role in ("customer", "representative", "supervisor"):
            c.execute(
                "INSERT INTO staff_sessions (token_hash, session_id, role) VALUES (?,?,?)",
                (uuid4().hex, uuid4().hex, role),
            )
        tx.cases.demo_state.set_now(DEMO_START + timedelta(hours=3))
        kept_sql = {
            "spend_ledger": "INSERT INTO spend_ledger (recorded_at) VALUES ('" + ts + "')",
            "health_events": "INSERT INTO health_events (at_wall, kind, agent_version) VALUES ('"
            + ts
            + "','check_ok','t')",
            "deploy_records": "INSERT INTO deploy_records (deploy_id, at_wall, agent_version) VALUES ('d1','"
            + ts
            + "','t')",
            "eval_runs": "INSERT INTO eval_runs (run_id, suite, agent_version, harness_commit, harness_digest, "
            "repeats, started_at, status, cases_expected, cases_scored) VALUES ('e1','e2e','t','c','d',1,'"
            + ts
            + "','started',1,0)",
            "eval_case_results": "INSERT INTO eval_case_results (run_id, case_id, repeat, passed_hard, outcome) "
            "VALUES ('e1','c1',1,1,'resolved')",
            "job_runs": "INSERT INTO job_runs (job_run_id, started_wall_at, demo_now, status) VALUES ('j1','"
            + ts
            + "','"
            + ts
            + "','started')",
            "demo_events": "INSERT INTO demo_events (demo_event_id, at_wall, kind, demo_before, demo_after, request_id, "
            "role) VALUES ('de1','" + ts + "','staffing_changed','a','b','r','owner')",
            "reset_events": "INSERT INTO reset_events (reset_id, at_wall) VALUES ('old-reset','" + ts + "')",
            "seed_events": "INSERT INTO seed_events (seed_event_id, at_wall, seed_count) VALUES ('s1','"
            + ts
            + "',4)",
            "ended_threads": "INSERT INTO ended_threads (thread_id, demo_session, ended_wall_at, reason) VALUES ('"
            + str(uuid4())
            + "','s','"
            + ts
            + "','idle')",
        }
        assert set(kept_sql) == set(KEPT_TABLES)
        for sql in kept_sql.values():
            c.execute(sql)
        tx.commit()

    with store.uow() as tx:
        seeded = {
            t: tx.connection.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in CLEARED_TABLES + KEPT_TABLES
        }
        kept_before = {t: seeded[t] for t in KEPT_TABLES}
        staff_before = tx.connection.execute("SELECT COUNT(*) FROM staff_sessions").fetchone()[0]
    reset_id = "reset-" + uuid4().hex[:8]
    ended = NOW + timedelta(minutes=1)
    with store.uow(exclusive=True) as tx:
        cleared = tx.core.reset.clear_demo_tables(reset_id, ended_at=ended)
        tx.commit()

    with store.uow() as tx:
        c = tx.connection
        for table in CLEARED_TABLES:
            assert c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table
        rows = c.execute(
            "SELECT thread_id, reason, reset_id FROM ended_threads WHERE reset_id = ?", (reset_id,)
        ).fetchall()
        assert {r[0] for r in rows} == {str(open_thread), str(closed_thread)}
        assert {(r[1], r[2]) for r in rows} == {("demo_reset", reset_id)}
        roles = c.execute("SELECT role, role_reset_pending FROM staff_sessions").fetchall()
        assert len(roles) == staff_before == 3
        assert {r[0] for r in roles} == {"customer"}
        assert sorted(r[1] for r in roles) == [0, 1, 1]
        for table in KEPT_TABLES:
            expected = kept_before[table] + (2 if table == "ended_threads" else 0)
            assert c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == expected, table
        assert c.execute("SELECT COUNT(*) FROM demo_state").fetchone()[0] == 1
        assert tx.cases.demo_state.get().demo_now == DEMO_START + timedelta(hours=3)
    assert cleared.open_threads == (open_thread,)
    assert cleared.case_streams == (ref,)
    assert cleared.roles_reset == 2
    assert cleared.rows_cleared == {t: seeded[t] for t in CLEARED_TABLES}
