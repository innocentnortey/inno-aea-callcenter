"""spend_ledger repository (AEA-02 shell; body: AEA-26, stage7/models.md §6, MOD-19).

Append-only: the only write is ``append``. No update, delete or clear (the demo reset keeps spend_ledger, cases.md §1.3).
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Final

from meridian.adapters.sqlite.db import format_wall, integrity_errors, last_row_id, parse_wall
from meridian.domain.common import ProviderFailure, ProviderFailureKind, RequestId, ThreadId, TurnId
from meridian.domain.turn import RunTag
from meridian.ports.models import CallRecord

__all__ = ["SpendRepo", "SpendRow"]


class SpendRow(CallRecord):
    """One spend_ledger row: CallRecord's fields plus the row id, the wall time and the TurnIds fields (models.md §6)."""

    id: int | None = None
    recorded_at: dt.datetime
    thread_id: ThreadId
    turn_id: TurnId
    request_id: RequestId
    run_tag: RunTag
    run_id: str | None
    agent_version: str


_INSERT: Final = (
    "INSERT INTO spend_ledger (recorded_at, thread_id, turn_id, request_id, run_tag, run_id, agent_version, "
    "role, provider, model, attempt, latency_ms, input_tokens, output_tokens, cache_read_tokens, "
    "cache_write_tokens, thinking_tokens, cost_usd, cost_source, status, failure_kind, http_status, "
    "provider_request_id, stop_reason) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_SELECT_FOR_TURN: Final = (
    "SELECT id, recorded_at, thread_id, turn_id, request_id, run_tag, run_id, agent_version, "
    "role, provider, model, attempt, latency_ms, input_tokens, output_tokens, cache_read_tokens, "
    "cache_write_tokens, thinking_tokens, cost_usd, cost_source, status, failure_kind, http_status, "
    "provider_request_id, stop_reason FROM spend_ledger WHERE turn_id = ? ORDER BY id"
)
_SUM_BETWEEN: Final = (
    "SELECT COALESCE(SUM(cost_usd), 0.0) FROM spend_ledger WHERE recorded_at >= ? AND recorded_at < ?"
)
_RETRYABLE_KINDS: Final = frozenset(
    {
        ProviderFailureKind.TIMEOUT,
        ProviderFailureKind.CONNECTION,
        ProviderFailureKind.RATE_LIMITED,
        ProviderFailureKind.OVERLOADED,
        ProviderFailureKind.SERVER,
    }
)  # DO-4 §11: retryable kinds; BODY_ERROR's inner code is not stored, so it reads back False


class SpendRepo:
    """spend_ledger rows (models.md §6, MOD-19). Append-only: append, total_between, for_turn; nothing else."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, row: SpendRow) -> int:
        if row.id is not None:
            raise ValueError("append takes a row without an id")
        failure = row.failure
        values = (
            format_wall(row.recorded_at),
            str(row.thread_id),
            str(row.turn_id),
            str(row.request_id),
            row.run_tag,
            row.run_id,
            row.agent_version,
            row.role.value,
            row.provider,
            row.model,
            row.attempt,
            row.latency_ms,
            row.input_tokens,
            row.output_tokens,
            row.cache_read_tokens,
            row.cache_write_tokens,
            row.thinking_tokens,
            row.cost_usd,
            row.cost_source,
            row.status,
            failure.kind.value if failure is not None else None,
            failure.http_status if failure is not None else None,
            row.provider_request_id,
            row.stop_reason,
        )
        with integrity_errors("spend_ledger"):
            cur = self._conn.execute(_INSERT, values)
        return last_row_id(cur, "spend_ledger")

    def total_between(self, start_utc: dt.datetime, end_utc: dt.datetime) -> float:
        (value,) = self._conn.execute(_SUM_BETWEEN, (format_wall(start_utc), format_wall(end_utc))).fetchone()
        return float(value)

    def for_turn(self, turn_id: TurnId) -> tuple[SpendRow, ...]:
        rows = self._conn.execute(_SELECT_FOR_TURN, (str(turn_id),)).fetchall()
        return tuple(_row_from_db(r) for r in rows)


def _row_from_db(r: tuple[object, ...]) -> SpendRow:
    (
        id_,
        recorded_at,
        thread_id,
        turn_id,
        request_id,
        run_tag,
        run_id,
        agent_version,
        role,
        provider,
        model,
        attempt,
        latency_ms,
        input_tokens,
        output_tokens,
        cache_read_tokens,
        cache_write_tokens,
        thinking_tokens,
        cost_usd,
        cost_source,
        status,
        failure_kind,
        http_status,
        provider_request_id,
        stop_reason,
    ) = r
    failure = None
    if failure_kind is not None:
        failure = ProviderFailure.model_validate(
            {
                "kind": failure_kind,
                "provider": provider,
                "http_status": http_status,
                "retry_after_s": None,
                "retryable": ProviderFailureKind(str(failure_kind)) in _RETRYABLE_KINDS,
                "provider_request_id": provider_request_id,
            }
        )
    return SpendRow.model_validate(
        {
            "id": id_,
            "recorded_at": parse_wall(str(recorded_at)),
            "thread_id": thread_id,
            "turn_id": turn_id,
            "request_id": request_id,
            "run_tag": run_tag,
            "run_id": run_id,
            "agent_version": agent_version,
            "role": role,
            "provider": provider,
            "model": model,
            "attempt": attempt,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": cache_write_tokens,
            "thinking_tokens": thinking_tokens,
            "cost_usd": cost_usd,
            "cost_source": cost_source,
            "status": status,
            "failure": failure,
            "provider_request_id": provider_request_id,
            "stop_reason": stop_reason,
        }
    )
