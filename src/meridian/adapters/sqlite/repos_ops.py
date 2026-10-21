"""Ops repositories: health events, deploy records, eval results, alert inputs (AEA-32; stage7/cases.md §8)."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import date, datetime
from typing import Literal, cast
from zoneinfo import ZoneInfo

from pydantic import JsonValue

from meridian.adapters.sqlite.db import format_wall, integrity_errors, last_row_id, parse_wall
from meridian.domain.common import MeridianModel
from meridian.ports.runtime import ExportStatus

AlertType = Literal[
    "spend_cap_reached",
    "p95_latency_over_12_5s",
    "health_check_restart",
    "zero_traffic",
    "failure_rate_over_2pct",
    "trace_export_failed",  # = OpenAPI MonitorAlert.type
    "scheduler_stale",  # stored only; CON-19 health tile (CAS-30). No overdue type.
]
ALERT_TYPES: tuple[AlertType, ...] = (
    "spend_cap_reached",
    "p95_latency_over_12_5s",
    "health_check_restart",
    "zero_traffic",
    "failure_rate_over_2pct",
    "trace_export_failed",
    "scheduler_stale",
)  # evaluation and return order
HealthKind = Literal["check_ok", "check_failed", "restart", "alert_fired", "alert_cleared"]
RunStatus = Literal["started", "completed", "failed", "incomplete"]
EvalSuite = Literal["worked-pairs", "retrieval", "e2e", "load"]
EvalSplit = Literal["dev", "held-out"]


class HealthEvent(MeridianModel):
    at_wall: datetime
    kind: HealthKind
    alert_type: AlertType | None
    reason_code: str | None
    value: float | None
    threshold: float | None
    agent_version: str


class AlertState(MeridianModel):
    type: AlertType
    state: Literal["firing", "quiet"]
    fired_at: datetime | None
    value: float | None
    threshold: float | None


class DeployRecord(MeridianModel):
    deploy_id: str
    at_wall: datetime
    agent_version: str
    git_commit: str | None = None
    image_digest: str | None = None
    config_hash: str | None = None
    trace_export_on: bool | None = None
    status: RunStatus = "completed"


class EvalRunRow(MeridianModel):
    run_id: str
    suite: EvalSuite
    split: EvalSplit | None
    agent_version: str
    harness_commit: str
    harness_digest: str
    experiment_id: str | None
    repeats: int
    started_at: datetime
    finished_at: datetime | None
    status: RunStatus
    cases_expected: int
    cases_scored: int
    index_manifest_hash: str | None
    judge_spend_usd: float


class StoredEvalRun(EvalRunRow):
    summary_json: str  # stored as given; AEA-53 reads it, never recomputes
    loaded_at: datetime | None


class EvalCaseResultRow(MeridianModel):
    run_id: str
    case_id: str
    repeat: int
    thread_id: str | None
    passed_hard: bool
    items: tuple[dict[str, JsonValue], ...]
    outcome: Literal["resolved", "handed_off", "degraded", "environment_error"]
    in_scope: bool | None
    topic: str | None
    top3: tuple[dict[str, JsonValue], ...] = ()
    below_floor: bool | None = None


class TurnSignal(MeridianModel):
    status: Literal["running", "completed", "failed"]
    outcome: str | None
    degrade_reason: str | None
    server_ms: int | None


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _opt_dt(text: str | None) -> datetime | None:
    return None if text is None else parse_wall(text)


def _opt_wall(value: datetime | None) -> str | None:
    return None if value is None else format_wall(value)


def _opt_bool(value: int | None) -> bool | None:
    return None if value is None else bool(value)


def _opt_int(value: bool | None) -> int | None:
    return None if value is None else int(value)


class HealthRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, event: HealthEvent) -> int:
        with integrity_errors("health_events"):
            cur = self._conn.execute(
                "INSERT INTO health_events (at_wall, kind, alert_type, reason_code, value, threshold, "
                "agent_version) VALUES (?,?,?,?,?,?,?)",
                (
                    format_wall(event.at_wall),
                    event.kind,
                    event.alert_type,
                    event.reason_code,
                    event.value,
                    event.threshold,
                    event.agent_version,
                ),
            )
        return last_row_id(cur, "health_events")

    def latest_alert_states(self) -> dict[AlertType, AlertState]:
        rows = self._conn.execute(
            "SELECT h.alert_type, h.kind, h.at_wall, h.value, h.threshold FROM health_events h "
            "JOIN (SELECT alert_type, MAX(id) AS id FROM health_events "
            "WHERE kind IN ('alert_fired','alert_cleared') AND alert_type IS NOT NULL "
            "GROUP BY alert_type) m ON h.id = m.id"
        ).fetchall()
        states: dict[AlertType, AlertState] = {
            t: AlertState(type=t, state="quiet", fired_at=None, value=None, threshold=None)
            for t in ALERT_TYPES
        }
        for alert_type, kind, at_wall, value, threshold in rows:
            if alert_type not in states:
                continue
            key = cast(AlertType, alert_type)
            if kind == "alert_fired":
                states[key] = AlertState(
                    type=key, state="firing", fired_at=parse_wall(at_wall), value=value, threshold=threshold
                )
            else:
                states[key] = AlertState(
                    type=key, state="quiet", fired_at=None, value=value, threshold=threshold
                )
        return states

    def last_restart(self) -> HealthEvent | None:
        r = self._conn.execute(
            "SELECT at_wall, kind, alert_type, reason_code, value, threshold, agent_version "
            "FROM health_events WHERE kind = 'restart' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if r is None:
            return None
        return HealthEvent.model_validate(
            {
                "at_wall": parse_wall(r[0]),
                "kind": r[1],
                "alert_type": r[2],
                "reason_code": r[3],
                "value": r[4],
                "threshold": r[5],
                "agent_version": r[6],
            }
        )

    def restarts_by_day(self, tz: str) -> list[tuple[date, int]]:
        zone = ZoneInfo(tz)
        counts: dict[date, int] = {}
        for (at_wall,) in self._conn.execute("SELECT at_wall FROM health_events WHERE kind = 'restart'"):
            day = parse_wall(at_wall).astimezone(zone).date()
            counts[day] = counts.get(day, 0) + 1
        return sorted(counts.items())


class DeployRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, record: DeployRecord) -> None:
        with integrity_errors("deploy_records"):
            self._conn.execute(
                "INSERT INTO deploy_records (deploy_id, at_wall, agent_version, git_commit, image_digest, "
                "config_hash, trace_export_on, status) VALUES (?,?,?,?,?,?,?,?)",
                (
                    record.deploy_id,
                    format_wall(record.at_wall),
                    record.agent_version,
                    record.git_commit,
                    record.image_digest,
                    record.config_hash,
                    _opt_int(record.trace_export_on),
                    record.status,
                ),
            )

    def latest(self) -> DeployRecord | None:
        r = self._conn.execute(
            "SELECT deploy_id, at_wall, agent_version, git_commit, image_digest, config_hash, "
            "trace_export_on, status FROM deploy_records ORDER BY at_wall DESC, rowid DESC LIMIT 1"
        ).fetchone()
        if r is None:
            return None
        return DeployRecord.model_validate(
            {
                "deploy_id": r[0],
                "at_wall": parse_wall(r[1]),
                "agent_version": r[2],
                "git_commit": r[3],
                "image_digest": r[4],
                "config_hash": r[5],
                "trace_export_on": _opt_bool(r[6]),
                "status": r[7],
            }
        )

    def set_status(self, deploy_id: str, status: RunStatus) -> bool:
        with integrity_errors("deploy_records"):
            cur = self._conn.execute(
                "UPDATE deploy_records SET status = ? WHERE deploy_id = ?", (status, deploy_id)
            )
        return cur.rowcount == 1


_RUN_COLS = (
    "run_id, suite, split, agent_version, harness_commit, harness_digest, experiment_id, repeats, "
    "started_at, finished_at, status, cases_expected, cases_scored, index_manifest_hash, judge_spend_usd, "
    "summary_json, loaded_at"
)
_RESULT_COLS = (
    "run_id, case_id, repeat, thread_id, passed_hard, items, outcome, in_scope, topic, top3, below_floor"
)


class EvalRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _run_from(r: Sequence[object]) -> StoredEvalRun:
        return StoredEvalRun.model_validate(
            {
                "run_id": r[0],
                "suite": r[1],
                "split": r[2],
                "agent_version": r[3],
                "harness_commit": r[4],
                "harness_digest": r[5],
                "experiment_id": r[6],
                "repeats": r[7],
                "started_at": parse_wall(str(r[8])),
                "finished_at": _opt_dt(cast("str | None", r[9])),
                "status": r[10],
                "cases_expected": r[11],
                "cases_scored": r[12],
                "index_manifest_hash": r[13],
                "judge_spend_usd": r[14],
                "summary_json": r[15],
                "loaded_at": _opt_dt(cast("str | None", r[16])),
            }
        )

    def _get(self, run_id: str) -> StoredEvalRun | None:
        r = self._conn.execute(
            f"SELECT {_RUN_COLS} FROM eval_runs WHERE run_id = ?",  # noqa: S608 - constant column list
            (run_id,),
        ).fetchone()
        return None if r is None else self._run_from(r)

    def upsert_report(
        self,
        run: EvalRunRow,
        results: Sequence[EvalCaseResultRow],
        summary_json: str,
        *,
        loaded_at: datetime | None = None,
    ) -> bool:
        existing = self._get(run.run_id)
        ordered = sorted(results, key=lambda r: (r.case_id, r.repeat))
        if (
            existing is not None
            and EvalRunRow.model_validate(existing.model_dump(exclude={"summary_json", "loaded_at"})) == run
            and existing.summary_json == summary_json
            and self.case_results(run.run_id) == ordered
        ):
            return False
        with integrity_errors("eval_runs"):
            self._conn.execute("DELETE FROM eval_case_results WHERE run_id = ?", (run.run_id,))
            self._conn.execute(
                f"INSERT OR REPLACE INTO eval_runs ({_RUN_COLS}) "  # noqa: S608 - constant column list
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    run.run_id,
                    run.suite,
                    run.split,
                    run.agent_version,
                    run.harness_commit,
                    run.harness_digest,
                    run.experiment_id,
                    run.repeats,
                    format_wall(run.started_at),
                    _opt_wall(run.finished_at),
                    run.status,
                    run.cases_expected,
                    run.cases_scored,
                    run.index_manifest_hash,
                    run.judge_spend_usd,
                    summary_json,
                    _opt_wall(loaded_at),
                ),
            )
        with integrity_errors("eval_case_results"):
            self._conn.executemany(
                f"INSERT INTO eval_case_results ({_RESULT_COLS}) "  # noqa: S608 - constant column list
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        r.run_id,
                        r.case_id,
                        r.repeat,
                        r.thread_id,
                        int(r.passed_hard),
                        _json(list(r.items)),
                        r.outcome,
                        _opt_int(r.in_scope),
                        r.topic,
                        _json(list(r.top3)),
                        _opt_int(r.below_floor),
                    )
                    for r in ordered
                ],
            )
        return True

    def latest_completed(self, suite: EvalSuite, split: EvalSplit | None) -> StoredEvalRun | None:
        r = self._conn.execute(
            f"SELECT {_RUN_COLS} FROM eval_runs "  # noqa: S608 - constant column list
            "WHERE suite = ? AND status = 'completed' AND split IS ? "
            "ORDER BY finished_at DESC, started_at DESC LIMIT 1",
            (suite, split),
        ).fetchone()
        return None if r is None else self._run_from(r)

    def case_results(self, run_id: str) -> list[EvalCaseResultRow]:
        rows = self._conn.execute(
            f"SELECT {_RESULT_COLS} FROM eval_case_results "  # noqa: S608 - constant column list
            "WHERE run_id = ? ORDER BY case_id, repeat",
            (run_id,),
        ).fetchall()
        return [
            EvalCaseResultRow.model_validate(
                {
                    "run_id": r[0],
                    "case_id": r[1],
                    "repeat": r[2],
                    "thread_id": r[3],
                    "passed_hard": bool(r[4]),
                    "items": tuple(json.loads(r[5])),
                    "outcome": r[6],
                    "in_scope": _opt_bool(r[7]),
                    "topic": r[8],
                    "top3": tuple(json.loads(r[9])),
                    "below_floor": _opt_bool(r[10]),
                }
            )
            for r in rows
        ]


class SignalsRepo:
    """Read-only alert inputs over core tables; live traffic only (AC-6)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def live_turns_replied_since(self, since: datetime) -> tuple[TurnSignal, ...]:
        rows = self._conn.execute(
            "SELECT t.status, t.outcome, t.degrade_reason, t.server_ms FROM turns t "
            "JOIN conversations c ON c.thread_id = t.thread_id "
            "WHERE t.run_tag = 'live' AND c.run_tag = 'live' AND t.replied_at IS NOT NULL "
            "AND t.replied_at >= ?",
            (format_wall(since),),
        ).fetchall()
        return tuple(
            TurnSignal.model_validate(
                {"status": r[0], "outcome": r[1], "degrade_reason": r[2], "server_ms": r[3]}
            )
            for r in rows
        )

    def latest_live_trace_export(self) -> ExportStatus | None:
        r = self._conn.execute(
            "SELECT t.trace_export FROM turns t JOIN conversations c ON c.thread_id = t.thread_id "
            "WHERE t.run_tag = 'live' AND c.run_tag = 'live' AND t.trace_export IS NOT NULL "
            "ORDER BY t.rowid DESC LIMIT 1"
        ).fetchone()
        return None if r is None else cast(ExportStatus, r[0])


class OpsRepos:
    """Ops repositories over one connection (body AEA-32, cases.md §8): health, deploy, eval, signals."""

    health: HealthRepo
    deploy: DeployRepo
    eval: EvalRepo
    signals: SignalsRepo

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.health = HealthRepo(conn)
        self.deploy = DeployRepo(conn)
        self.eval = EvalRepo(conn)
        self.signals = SignalsRepo(conn)
