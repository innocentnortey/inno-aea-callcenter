"""Case-store repositories, part two: demo state, demo events, job runs, reset and seed records, case refs (AEA-10).

Split from ``repos_cases.py`` to keep both files under the 600-line adapter cap (code-structure.md). ``DEMO_START`` and
``SEED_REF_MAX`` live here and are re-exported by ``repos_cases``.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter

from meridian.adapters.sqlite.db import StorageError, format_wall, integrity_errors
from meridian.adapters.sqlite.rows import (
    DemoEventRow,
    DemoStateRow,
    JobRunRow,
    ResetEventRow,
    SeedEventRow,
    _dt,
    _j,
)
from meridian.domain.common import CaseRef

DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))  # CAS-23, verbatim
SEED_REF_MAX = 8  # seeds hold MHC-C-0005 to 0008 (cases.md 7, CAS-24)
_CASE_REF: TypeAdapter[CaseRef] = TypeAdapter(CaseRef)


class DemoStateRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get(self) -> DemoStateRow:
        """A fresh store reads DEMO_START and nobody_online without writing."""
        r = self._conn.execute("SELECT demo_now, staffing FROM demo_state WHERE id = 1").fetchone()
        if r is None:
            return DemoStateRow(demo_now=DEMO_START, staffing="nobody_online")
        return DemoStateRow.model_validate({"demo_now": _dt(r[0]), "staffing": r[1]})

    def set_now(self, dt: datetime) -> None:
        with integrity_errors("demo_state"):
            self._conn.execute(
                "INSERT INTO demo_state (id, demo_now, staffing) VALUES (1, ?, 'nobody_online') "
                "ON CONFLICT(id) DO UPDATE SET demo_now = excluded.demo_now",
                (format_wall(dt),),
            )

    def set_staffing(self, mode: str) -> None:
        with integrity_errors("demo_state"):
            self._conn.execute(
                "INSERT INTO demo_state (id, demo_now, staffing) VALUES (1, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET staffing = excluded.staffing",
                (format_wall(DEMO_START), mode),
            )

    def reset(self) -> None:
        with integrity_errors("demo_state"):
            self._conn.execute(
                "INSERT INTO demo_state (id, demo_now, staffing) VALUES (1, ?, 'nobody_online') "
                "ON CONFLICT(id) DO UPDATE SET demo_now = excluded.demo_now, staffing = excluded.staffing",
                (format_wall(DEMO_START),),
            )


class DemoEventsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, row: DemoEventRow) -> None:
        with integrity_errors("demo_events"):
            self._conn.execute(
                "INSERT INTO demo_events (demo_event_id, at_wall, kind, step, mode, demo_before, demo_after, "
                "became_overdue, converted_cases, request_id, role) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row.demo_event_id,
                    format_wall(row.at_wall),
                    row.kind,
                    row.step,
                    row.mode,
                    row.demo_before,
                    row.demo_after,
                    row.became_overdue,
                    row.converted_cases,
                    row.request_id,
                    row.role,
                ),
            )


class JobRunsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def start(self, job_run_id: str, *, started_wall_at: datetime, demo_now: datetime) -> None:
        with integrity_errors("job_runs"):
            self._conn.execute(
                "INSERT INTO job_runs (job_run_id, started_wall_at, demo_now, status) VALUES (?,?,?,'started')",
                (job_run_id, format_wall(started_wall_at), format_wall(demo_now)),
            )

    def finish(
        self,
        job_run_id: str,
        status: str,
        counts: Mapping[str, int | None],
        error_kind: str | None,
        *,
        finished_wall_at: datetime | None = None,
    ) -> None:
        with integrity_errors("job_runs"):
            cur = self._conn.execute(
                "UPDATE job_runs SET finished_wall_at = ?, status = ?, counts_json = ?, error_kind = ? "
                "WHERE job_run_id = ?",
                (
                    format_wall(finished_wall_at or datetime.now(UTC)),
                    status,
                    _j(dict(counts)),
                    error_kind,
                    job_run_id,
                ),
            )
        if cur.rowcount == 0:
            raise StorageError("job_runs", "no row")

    def latest(self) -> JobRunRow | None:
        r = self._conn.execute(
            "SELECT job_run_id, started_wall_at, finished_wall_at, demo_now, status, error_kind, counts_json "
            "FROM job_runs ORDER BY started_wall_at DESC, job_run_id DESC LIMIT 1"
        ).fetchone()
        if r is None:
            return None
        return JobRunRow.model_validate(
            {
                "job_run_id": r[0],
                "started_wall_at": _dt(r[1]),
                "finished_wall_at": _dt(r[2]),
                "demo_now": _dt(r[3]),
                "status": r[4],
                "error_kind": r[5],
                "counts": json.loads(r[6]),
            }
        )


class RecordsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def reset_event(self, row: ResetEventRow) -> None:
        with integrity_errors("reset_events"):
            self._conn.execute(
                "INSERT INTO reset_events (reset_id, at_wall, asked_by_role, asked_by_session, request_id, "
                "restored_json, open_chats_ended, roles_reset, checkpoints_cleared) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    row.reset_id,
                    format_wall(row.at_wall),
                    None if row.asked_by_role is None else row.asked_by_role.value,
                    row.asked_by_session,
                    row.request_id,
                    _j(row.restored),
                    row.open_chats_ended,
                    row.roles_reset,
                    None if row.checkpoints_cleared is None else int(row.checkpoints_cleared),
                ),
            )

    def seed_event(self, row: SeedEventRow) -> None:
        with integrity_errors("seed_events"):
            self._conn.execute(
                "INSERT INTO seed_events (seed_event_id, at_wall, reset_id, deploy_id, seed_count, label) "
                "VALUES (?,?,?,?,?,?)",
                (
                    row.seed_event_id,
                    format_wall(row.at_wall),
                    row.reset_id,
                    row.deploy_id,
                    row.seed_count,
                    row.label,
                ),
            )

    def seed_rows_present(self) -> bool:
        return bool(self._conn.execute("SELECT EXISTS (SELECT 1 FROM cases WHERE seed = 1)").fetchone()[0])

    def set_checkpoints_cleared(self, reset_id: str, cleared: bool) -> None:
        cur = self._conn.execute(
            "UPDATE reset_events SET checkpoints_cleared = ? WHERE reset_id = ?", (int(cleared), reset_id)
        )
        if cur.rowcount == 0:
            raise StorageError("reset_events", "no row")

    def latest_reset_event(self) -> ResetEventRow | None:
        r = self._conn.execute(
            "SELECT reset_id, at_wall, asked_by_role, asked_by_session, request_id, restored_json, "
            "open_chats_ended, roles_reset, checkpoints_cleared FROM reset_events "
            "ORDER BY at_wall DESC, reset_id DESC LIMIT 1"
        ).fetchone()
        if r is None:
            return None
        return ResetEventRow.model_validate(
            {
                "reset_id": r[0],
                "at_wall": _dt(r[1]),
                "asked_by_role": r[2],
                "asked_by_session": r[3],
                "request_id": r[4],
                "restored": json.loads(r[5]),
                "open_chats_ended": r[6],
                "roles_reset": r[7],
                "checkpoints_cleared": None if r[8] is None else bool(r[8]),
            }
        )

    def latest_seed_event(self) -> SeedEventRow | None:
        r = self._conn.execute(
            "SELECT seed_event_id, at_wall, reset_id, deploy_id, seed_count, label FROM seed_events "
            "ORDER BY at_wall DESC, seed_event_id DESC LIMIT 1"
        ).fetchone()
        if r is None:
            return None
        return SeedEventRow.model_validate(
            {
                "seed_event_id": r[0],
                "at_wall": _dt(r[1]),
                "reset_id": r[2],
                "deploy_id": r[3],
                "seed_count": r[4],
                "label": r[5],
            }
        )


class RefsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def next_case_ref(self) -> CaseRef:
        """max(highest numeric part, SEED_REF_MAX) + 1."""
        top = self._conn.execute("SELECT MAX(CAST(substr(case_ref, 7) AS INTEGER)) FROM cases").fetchone()[0]
        return _CASE_REF.validate_python(f"MHC-C-{max(top or 0, SEED_REF_MAX) + 1:04d}")
