"""Health events, heartbeat, watchdog and alerts (AEA-32; stage7/cases.md §8; DO-3 §4.4)."""

from __future__ import annotations

import json
import logging
import math
import threading
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import time as dtime
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

import anyio
import anyio.to_thread

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.repos_ops import (
    ALERT_TYPES,
    AlertState,
    AlertType,
    EvalCaseResultRow,
    EvalRunRow,
    HealthEvent,
)
from meridian.ports.runtime import UnitOfWorkFactory

logger = logging.getLogger("meridian.ops")

__all__ = [
    "ALERT_TYPES",
    "AlertEvaluator",
    "AlertSettings",
    "AlertState",
    "AlertType",
    "AlertWriter",
    "HealthEvent",
    "Heartbeat",
    "SpendReader",
    "Watchdog",
    "load_eval_reports",
    "p95_nearest_rank",
    "run_beats",
    "time_outside_quiet_hours",
]

PROBE_NOT_OK = "healthz_not_ok"
PROBE_ERROR = "healthz_error"


@dataclass(frozen=True)
class AlertSettings:
    """The one place alert lines live (cases.md §8)."""

    latency_p95_s: float = 12.5  # [T] M-23
    failure_rate: float = 0.02  # [T] M-24
    zero_traffic_after: timedelta = timedelta(hours=4)  # [Decided Innocent 2026-10-21] M-22
    quiet_start: dtime = dtime(22)  # [A, configurable] M-22
    quiet_end: dtime = dtime(6)
    tz: str = "America/Chicago"
    turn_window: timedelta = timedelta(minutes=60)  # [A] CAS-25
    min_turns: int = 20  # [A] below it, latency and failure-rate alerts stay quiet
    evaluate_every_s: int = 60  # [A] CAS-25
    scheduler_stale_after_s: int = 180  # [A] CAS-22
    heartbeat_every_s: int = 5  # [A] CAS-26
    heartbeat_stale_after_s: int = 30
    probe_every_s: int = 15  # [A, system design 8.2]
    probe_timeout_s: int = 5
    failures_to_exit: int = 3


class SpendReader(Protocol):
    """The one LedgerService method the evaluator reads (models.md §6)."""

    def spend_today(self) -> float: ...


class Heartbeat:
    """In-memory beat; implements AEA-23's HeartbeatReader structurally. Never touches storage or the pool."""

    def __init__(self, settings: AlertSettings, *, started_mono: float | None = None) -> None:
        self._stale_after_s = settings.heartbeat_stale_after_s
        self._last: float | None = started_mono

    def beat(self, mono: float) -> None:
        self._last = mono

    def fresh(self, mono: float) -> bool:
        return self._last is not None and mono - self._last <= self._stale_after_s


def _pool_noop() -> None:
    return None


async def _to_pool(fn: Callable[[], None]) -> None:
    await anyio.to_thread.run_sync(fn)


async def run_beats(
    heartbeat: Heartbeat,
    settings: AlertSettings,
    *,
    run_sync: Callable[[Callable[[], None]], Awaitable[None]] = _to_pool,
    sleep: Callable[[float], Awaitable[None]] = anyio.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> None:
    """Beat only after a no-op ran on a worker thread: a fresh beat proves the loop and the pool (CAS-26)."""
    while True:
        await run_sync(_pool_noop)
        heartbeat.beat(monotonic())
        await sleep(settings.heartbeat_every_s)


def time_outside_quiet_hours(start: datetime, end: datetime, settings: AlertSettings) -> timedelta:
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("naive datetime")
    if end <= start:
        return timedelta(0)
    s, e = start.astimezone(UTC), end.astimezone(UTC)
    total = e - s
    tz = ZoneInfo(settings.tz)
    quiet = timedelta(0)
    first = start.astimezone(tz).date() - timedelta(days=1)
    last = end.astimezone(tz).date()
    day = first
    while day <= last:
        if settings.quiet_start > settings.quiet_end:
            q0 = datetime.combine(day, settings.quiet_start, tzinfo=tz)
            q1 = datetime.combine(day + timedelta(days=1), settings.quiet_end, tzinfo=tz)
        elif settings.quiet_start < settings.quiet_end:
            q0 = datetime.combine(day, settings.quiet_start, tzinfo=tz)
            q1 = datetime.combine(day, settings.quiet_end, tzinfo=tz)
        else:
            break
        overlap = min(e, q1.astimezone(UTC)) - max(s, q0.astimezone(UTC))
        quiet += max(timedelta(0), overlap)
        day += timedelta(days=1)
    return total - quiet


def p95_nearest_rank(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("empty")
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


class AlertWriter:
    def __init__(
        self, uow: UnitOfWorkFactory, wall_clock: Callable[[], datetime], agent_version: str
    ) -> None:
        self._uow = uow
        self._wall_clock = wall_clock
        self._agent_version = agent_version
        self._lock = threading.Lock()

    def fire(self, alert_type: AlertType, reason_code: str) -> None:
        with self._lock, self._uow(write=True) as tx:
            if tx.ops.health.latest_alert_states()[alert_type].state == "firing":
                return
            tx.ops.health.append(
                HealthEvent(
                    at_wall=self._wall_clock(),
                    kind="alert_fired",
                    alert_type=alert_type,
                    reason_code=reason_code,
                    value=None,
                    threshold=None,
                    agent_version=self._agent_version,
                )
            )
            tx.commit()


@dataclass(frozen=True)
class _Decision:
    fire: bool | None  # None = no evidence: leave the stored state as it is
    value: float | None = None
    threshold: float | None = None
    reason: str | None = None


class AlertEvaluator:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        ledger: SpendReader,
        settings: AlertSettings,
        wall_clock: Callable[[], datetime],
        daily_cap_usd: float,
        *,
        agent_version: str,
    ) -> None:
        self._uow = uow
        self._ledger = ledger
        self._settings = settings
        self._wall_clock = wall_clock
        self._cap_usd = daily_cap_usd
        self._agent_version = agent_version

    def evaluate(self) -> tuple[AlertState, ...]:
        now = self._wall_clock()
        if now.tzinfo is None:
            raise ValueError("naive datetime")
        spent = self._ledger.spend_today()  # before the write unit: the ledger opens its own read unit
        cfg = self._settings
        with self._uow(write=True) as tx:
            current = tx.ops.health.latest_alert_states()
            decisions: dict[AlertType, _Decision] = {}
            decisions["spend_cap_reached"] = _Decision(
                spent >= self._cap_usd, spent, self._cap_usd, "spend_at_or_over_cap"
            )

            turns = tx.ops.signals.live_turns_replied_since(now - cfg.turn_window)
            secs = [t.server_ms / 1000 for t in turns if t.server_ms is not None]
            if len(secs) < cfg.min_turns:
                decisions["p95_latency_over_12_5s"] = _Decision(False, None, cfg.latency_p95_s)
            else:
                p95 = p95_nearest_rank(secs)
                decisions["p95_latency_over_12_5s"] = _Decision(
                    p95 > cfg.latency_p95_s, p95, cfg.latency_p95_s, "p95_over_line"
                )
            if len(turns) < cfg.min_turns:
                decisions["failure_rate_over_2pct"] = _Decision(False, None, cfg.failure_rate)
            else:
                failed = sum(
                    1
                    for t in turns
                    if t.outcome == "degraded_handoff"
                    and t.degrade_reason in ("model_error", "tool_error", "timeout")
                )
                rate = failed / len(turns)
                decisions["failure_rate_over_2pct"] = _Decision(
                    rate > cfg.failure_rate, rate, cfg.failure_rate, "failure_rate_over_line"
                )

            anchor = tx.core.conversations.last_started_wall()
            if anchor is None:
                candidates: list[datetime] = []
                deploy = tx.ops.deploy.latest()
                if deploy is not None:
                    candidates.append(deploy.at_wall)
                reset = tx.cases.records.latest_reset_event()
                if reset is not None:
                    candidates.append(reset.at_wall)
                anchor = max(candidates) if candidates else None
            if anchor is None:
                decisions["zero_traffic"] = _Decision(None)
            else:
                counted = time_outside_quiet_hours(anchor, now, cfg)
                decisions["zero_traffic"] = _Decision(
                    counted > cfg.zero_traffic_after,
                    counted / timedelta(hours=1),
                    cfg.zero_traffic_after / timedelta(hours=1),
                    "no_new_live_conversation",
                )

            tz = ZoneInfo(cfg.tz)
            last = tx.ops.health.last_restart()
            if last is None:
                decisions["health_check_restart"] = _Decision(False)
            else:
                today = last.at_wall.astimezone(tz).date() == now.astimezone(tz).date()
                count = dict(tx.ops.health.restarts_by_day(cfg.tz)).get(now.astimezone(tz).date(), 0)
                decisions["health_check_restart"] = _Decision(
                    today,
                    float(count) if today else None,
                    None,
                    (last.reason_code or "health_check_restart") if today else None,
                )

            export = tx.ops.signals.latest_live_trace_export()
            if export is None:
                decisions["trace_export_failed"] = _Decision(None)
            elif export == "sent":
                decisions["trace_export_failed"] = _Decision(False)
            else:
                decisions["trace_export_failed"] = _Decision(True, None, None, f"turn_export_{export}")

            job = tx.cases.job_runs.latest()
            if job is None:
                decisions["scheduler_stale"] = _Decision(None)
            else:
                age = (now - job.started_wall_at).total_seconds()
                decisions["scheduler_stale"] = _Decision(
                    age > cfg.scheduler_stale_after_s,
                    age,
                    float(cfg.scheduler_stale_after_s),
                    "scheduler_tick_missed",
                )

            states: list[AlertState] = []
            for alert_type in ALERT_TYPES:
                cur = current[alert_type]
                d = decisions[alert_type]
                if d.fire is True and cur.state == "quiet":
                    tx.ops.health.append(
                        self._event(now, "alert_fired", alert_type, d.reason, d.value, d.threshold)
                    )
                    cur = AlertState(
                        type=alert_type, state="firing", fired_at=now, value=d.value, threshold=d.threshold
                    )
                elif d.fire is False and cur.state == "firing":
                    tx.ops.health.append(
                        self._event(
                            now, "alert_cleared", alert_type, "condition_cleared", d.value, d.threshold
                        )
                    )
                    cur = AlertState(
                        type=alert_type, state="quiet", fired_at=None, value=d.value, threshold=d.threshold
                    )
                states.append(cur)
            tx.commit()
        return tuple(states)

    def _event(
        self,
        at: datetime,
        kind: str,
        alert_type: AlertType,
        reason: str | None,
        value: float | None,
        threshold: float | None,
    ) -> HealthEvent:
        return HealthEvent.model_validate(
            {
                "at_wall": at,
                "kind": kind,
                "alert_type": alert_type,
                "reason_code": reason,
                "value": value,
                "threshold": threshold,
                "agent_version": self._agent_version,
            }
        )


class Watchdog:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        probe: Callable[[], bool],
        exit: Callable[[int], None],
        evaluator: AlertEvaluator,
        settings: AlertSettings,
        wall_clock: Callable[[], datetime],
        *,
        agent_version: str,
    ) -> None:
        self._uow = uow
        self._probe = probe
        self._exit = exit
        self._evaluator = evaluator
        self._settings = settings
        self._wall_clock = wall_clock
        self._agent_version = agent_version
        self._failures = 0
        self._last_eval: datetime | None = None
        self._stopping: threading.Event | None = None

    def _stopped(self) -> bool:
        return self._stopping is not None and self._stopping.is_set()

    def _write(self, event: HealthEvent) -> None:
        with self._uow(write=True) as tx:
            tx.ops.health.append(event)
            tx.commit()

    def run_once(self) -> None:
        if self._stopped():
            return
        reason: str | None
        try:
            ok = bool(self._probe())
            reason = None if ok else PROBE_NOT_OK
        except Exception:
            ok = False
            reason = PROBE_ERROR
        if self._stopped():
            return
        now = self._wall_clock()
        self._failures = 0 if ok else self._failures + 1
        restarted = False
        try:
            self._write(
                HealthEvent(
                    at_wall=now,
                    kind="check_ok" if ok else "check_failed",
                    alert_type=None,
                    reason_code=reason,
                    value=None,
                    threshold=None,
                    agent_version=self._agent_version,
                )
            )
        finally:
            if self._failures >= self._settings.failures_to_exit:
                restarted = True
                self._restart(now)
        if restarted:
            return
        if (
            self._last_eval is None
            or (now - self._last_eval).total_seconds() >= self._settings.evaluate_every_s
        ):
            self._evaluator.evaluate()
            self._last_eval = now

    def _restart(self, now: datetime) -> None:
        n = self._failures
        try:
            self._write(
                HealthEvent(
                    at_wall=now,
                    kind="restart",
                    alert_type=None,
                    reason_code=f"healthz_failed_{n}_in_a_row",
                    value=float(n),
                    threshold=float(self._settings.failures_to_exit),
                    agent_version=self._agent_version,
                )
            )
        finally:
            self._failures = 0
            self._exit(1)

    def run_until(self, stop: threading.Event) -> None:
        self._stopping = stop
        while not stop.wait(self._settings.probe_every_s):
            try:
                self.run_once()
            except Exception:
                logger.warning("watchdog_run_failed")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def load_eval_reports(
    reports_dir: Path,
    uow: UnitOfWorkFactory,
    *,
    wall_clock: Callable[[], datetime] = _utc_now,
    agent_version: str = "unknown",
) -> int:
    """Copy each eval/reports/*.json into eval_runs / eval_case_results once per run_id; returns the number new."""
    if not reports_dir.is_dir():
        return 0
    new = 0
    for path in sorted(reports_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if (
                not isinstance(raw, dict)
                or set(raw) != {"run", "results", "summary"}
                or not isinstance(raw["summary"], dict)
                or not isinstance(raw["results"], list)
            ):
                raise ValueError("report shape")
            run = EvalRunRow.model_validate(raw["run"])
            results = tuple(EvalCaseResultRow.model_validate(r) for r in raw["results"])
            summary_json = json.dumps(raw["summary"], ensure_ascii=False, separators=(",", ":"))
            with uow(write=True) as tx:
                changed = tx.ops.eval.upsert_report(run, results, summary_json, loaded_at=wall_clock())
                tx.commit()
        except (OSError, ValueError, StorageError):
            logger.warning("eval_report_invalid")
            with uow(write=True) as tx:
                tx.ops.health.append(
                    HealthEvent(
                        at_wall=wall_clock(),
                        kind="check_failed",
                        alert_type=None,
                        reason_code="eval_report_invalid",
                        value=None,
                        threshold=None,
                        agent_version=agent_version,
                    )
                )
                tx.commit()
            continue
        new += int(changed)
    return new
