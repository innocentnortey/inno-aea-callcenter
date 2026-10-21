"""AEA-10 AC-21, AC-22, PA-1: the schema holds every field the contracts name; every table has one reset effect."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from meridian.adapters.sqlite.migrate import (
    CLEARED_TABLES,
    ISSUED_TABLES,
    KEPT_TABLES,
    UPDATED_TABLES,
    schema_files,
)
from meridian.domain.tools import LookupRow
from meridian.domain.turn import CheckEvent
from tests.fixtures.sqlite import TempStore, temp_sqlite


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _columns(store: TempStore) -> dict[str, list[str]]:
    with store.uow() as tx:
        c = tx.connection
        tables = [
            r[0]
            for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {t: [r[1] for r in c.execute(f"PRAGMA table_info({t})")] for t in tables}


EXPECTED: dict[str, set[str]] = {
    "turns": {
        "turn_id",
        "thread_id",
        "request_id",
        "run_tag",
        "run_id",
        "agent_version",
        "sequence",
        "received_at",
        "status",
        "gate_result",
        "path",
        "outcome",
        "degrade_reason",
        "planner_model",
        "planner_fallback_used",
        "planner_failure",
        "plan_mode",
        "plan_source",
        "plan_intents",
        "plan_handoff_request",
        "plan_topic",
        "planner_failed",
        "danger_raised",
        "specialists_run",
        "replied_at",
        "server_ms",
        "model_calls",
        "input_tokens",
        "output_tokens",
        "cost_usd",
        "tool_calls",
        "trace_id",
        "trace_export",
        "response",
    },
    "conversations": {
        "thread_id",
        "run_tag",
        "run_id",
        "agent_version",
        "outcome",
        "started_at",
        "started_wall_at",
        "ended_wall_at",
        "staffing_at_start",
        "last_customer_wall_at",
        "live_state",
    },
    "check_events": {("check_kind" if f == "check" else f) for f in CheckEvent.model_fields}
    | {"thread_id", "at"},
    "lookup_log": set(LookupRow.model_fields),
    "cases": {"case_ref", "thread_id", "turn_id", "due_at", "seed", "priority", "lifecycle"},
    "promises": {"case_ref", "text", "due_at", "status", "policy_row"},
    "case_events": {"case_ref", "kind", "actor_role", "job_run_id"},
    "job_runs": {"job_run_id"},
    "demo_events": {"demo_event_id"},
    "reset_events": {"reset_id", "asked_by_role", "asked_by_session", "checkpoints_cleared"},
    "seed_events": {"reset_id", "deploy_id", "seed_count", "label"},
    "spend_ledger": {
        "id",
        "recorded_at",
        "thread_id",
        "turn_id",
        "request_id",
        "run_tag",
        "run_id",
        "agent_version",
        "role",
        "provider",
        "model",
        "attempt",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "thinking_tokens",
        "cost_usd",
        "cost_source",
        "status",
        "failure_kind",
        "http_status",
        "provider_request_id",
        "stop_reason",
    },
    "identity_threads": {
        "thread_id",
        "status",
        "customer_id",
        "masked_hint",
        "channel",
        "verified_at",
        "updated_at",
    },
    "identity_codes": {
        "id",
        "thread_id",
        "customer_id",
        "code_hmac",
        "held_by",
        "sent_at",
        "expires_at",
        "tries_left",
        "used_at",
        "inbox_message_id",
    },
    "demo_inbox": {"id", "demo_session", "thread_id", "to_masked", "sent_at", "expires_at"},
    "staff_sessions": {
        "token_hash",
        "session_id",
        "role",
        "role_reset_pending",
        "signed_in_demo",
        "created_real",
        "expires_real",
    },
    "flags": {
        "id",
        "case_ref",
        "target",
        "message_id",
        "note",
        "reason",
        "flagged_by_role",
        "flagged_at",
        "status",
        "reviewed_by_role",
        "reviewed_note",
        "reviewed_at",
    },
}


def test_do6_fields_present(store: TempStore) -> None:
    cols = _columns(store)
    for table, names in sorted(cols.items()):
        print(table, names)
    for table, expected in EXPECTED.items():
        assert expected <= set(cols[table]), (table, expected - set(cols[table]))
    for table in (
        "spend_ledger",
        "identity_threads",
        "identity_codes",
        "demo_inbox",
        "staff_sessions",
        "flags",
    ):
        assert set(cols[table]) == EXPECTED[table], table
    with store.uow() as tx:
        rows = tx.connection.execute("PRAGMA table_info(seed_events)").fetchall()
    default = next(r for r in rows if r[1] == "label")[4]
    assert default == "'demo seed'"


def test_temp_sqlite_applies_all_schema() -> None:
    with temp_sqlite() as s:
        tables = set(_columns(s))
        assert set(ISSUED_TABLES + CLEARED_TABLES + UPDATED_TABLES + KEPT_TABLES) <= tables
        assert s.db_path.exists()
        data_dir = s.data_dir
    assert not data_dir.exists()
    assert len(schema_files()) == 7


def test_every_table_has_one_reset_effect(store: TempStore) -> None:
    groups = [ISSUED_TABLES, CLEARED_TABLES, UPDATED_TABLES, KEPT_TABLES]
    flat = [t for g in groups for t in g]
    assert len(flat) == len(set(flat))
    assert set(flat) == set(_columns(store))


def test_no_kept_table_references_cleared_table(store: TempStore) -> None:
    with store.uow() as tx:
        for table in KEPT_TABLES + UPDATED_TABLES:
            targets = {r[2] for r in tx.connection.execute(f"PRAGMA foreign_key_list({table})")}
            assert not targets & set(CLEARED_TABLES), table
