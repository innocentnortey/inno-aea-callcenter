"""The 60 s background job: demo-clock alerts, missed promises, the wall-clock abandonment sweep and the daily
checkpoint prune (stage7/cases.md section 6; DO-3 4.4; system design 8.2).

Two clocks (plan R-10): the alert rules and the promise-missed rule move only with the demo clock; the abandonment
sweep and the prune move only with the wall clock (MC-20, D-13). Rows hold IDs, kinds, statuses, counts and times only.
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Final, Literal
from zoneinfo import ZoneInfo

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.rows import CaseEventRow
from meridian.domain.common import CaseRef, MeridianModel
from meridian.policy.handoff import DUE_SOON_WINDOW, UNOWNED_AFTER
from meridian.ports.runtime import Clock, UnitOfWorkFactory

_log = logging.getLogger(__name__)
_CHICAGO: Final = ZoneInfo("America/Chicago")
TICK_INTERVAL_S: Final = 60.0  # [A] system design 8.2 "Runs every 60 s"
ABANDON_AFTER: Final = timedelta(minutes=30)  # [Decided] DO-7 M-18 end rule, Innocent 2026-10-21 (CAS-29)
ALERT_KINDS: Final = ("overdue", "due_soon", "stuck_waiting", "unowned")
PROMISE_MISSED_KIND: Final = "promise_missed"
PROMISE_MISSED_REASON: Final = "past_due"  # promises.status_reason code (no free text)
ERROR_KINDS: Final = ("alerts_failed", "sweep_failed", "prune_failed")


class JobRun(MeridianModel):
    """One tick's result (internal, not serialised; cases section 6)."""

    job_run_id: str
    started_wall_at: datetime
    finished_wall_at: datetime | None
    demo_now: datetime
    status: Literal["started", "completed", "failed"]
    error_kind: str | None
    overdue: int
    promises_missed: int
    due_soon: int
    stuck_waiting: int
    unowned: int
    abandoned: int
    pruned: int | None  # set only on the once-a-day tick


@dataclass
class _Counts:
    """Private mutable tally; one per tick."""

    overdue: int = 0
    promises_missed: int = 0
    due_soon: int = 0
    stuck_waiting: int = 0
    unowned: int = 0
    abandoned: int = 0
    pruned: int | None = None

    def as_json(self) -> dict[str, int | None]:
        return {
            "overdue": self.overdue,
            "promises_missed": self.promises_missed,
            "due_soon": self.due_soon,
            "stuck_waiting": self.stuck_waiting,
            "unowned": self.unowned,
            "abandoned": self.abandoned,
            "pruned": self.pruned,
        }


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SchedulerJob:
    """WF-7: one tick per call (cases section 6, constructor revised by CAS-29)."""

    def __init__(
        self,
        uow: UnitOfWorkFactory,
        cases: object,
        clock: Clock,
        prune_checkpoints: Callable[[], int],
        wall_clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        # `cases` is the CaseService slot of cases section 6; the tick calls none of its methods (plan R-7).
        self._uow = uow
        self._cases = cases
        self._clock = clock
        self._prune_checkpoints = prune_checkpoints
        self._wall_clock = wall_clock
        self._pruned_on: date | None = None  # the first tick of a process prunes (catch-up after a restart)

    def tick(self) -> JobRun:
        wall_start = self._wall_clock()
        demo_now = self._clock.now()
        job_run_id = str(uuid.uuid4())
        counts = _Counts()
        with self._uow(write=True) as tx:
            tx.cases.job_runs.start(job_run_id, started_wall_at=wall_start, demo_now=demo_now)
            tx.commit()
        step = "alerts"
        status, error_kind = "completed", None
        try:
            self._alerts(job_run_id, demo_now, counts)
            step = "sweep"
            self._sweep(wall_start, counts)
            step = "prune"
            today = wall_start.astimezone(_CHICAGO).date()  # Chicago day bounds (cases section 1.1)
            if self._pruned_on != today:
                counts.pruned = self._prune_checkpoints()
                self._pruned_on = today
        except Exception as exc:
            status, error_kind = "failed", f"{step}_failed"
            _log.warning(
                "scheduler tick step failed",
                extra={"job_run_id": job_run_id, "error_kind": error_kind, "exc_type": type(exc).__name__},
            )
        wall_end = self._wall_clock()
        with self._uow(write=True) as tx:
            tx.cases.job_runs.finish(
                job_run_id, status, counts.as_json(), error_kind, finished_wall_at=wall_end
            )
            tx.commit()
        return JobRun(
            job_run_id=job_run_id,
            started_wall_at=wall_start,
            finished_wall_at=wall_end,
            demo_now=demo_now,
            status="completed" if status == "completed" else "failed",
            error_kind=error_kind,
            overdue=counts.overdue,
            promises_missed=counts.promises_missed,
            due_soon=counts.due_soon,
            stuck_waiting=counts.stuck_waiting,
            unowned=counts.unowned,
            abandoned=counts.abandoned,
            pruned=counts.pruned,
        )

    def _alerts(self, job_run_id: str, n: datetime, counts: _Counts) -> None:
        """Demo-clock rules, one write transaction. Counts are copied only after the commit."""
        tally = _Counts()
        with self._uow(write=True) as tx:
            staffing = tx.cases.demo_state.get().staffing

            def alert(case_ref: CaseRef, kind: str, value: datetime, detail_name: str) -> bool:
                key = format_wall(value)
                if tx.cases.case_events.exists(case_ref, kind, key):
                    return False
                tx.cases.case_events.append(
                    CaseEventRow.model_validate(
                        {
                            "case_ref": str(case_ref),
                            "kind": kind,
                            "key": key,
                            "actor_role": "system",
                            "job_run_id": job_run_id,
                            "detail": {detail_name: key},
                            "at": n,
                        }
                    )
                )
                return True

            for c in tx.cases.cases.list_open():
                if c.due_at is not None and c.due_at < n and alert(c.case_ref, "overdue", c.due_at, "due_at"):
                    tally.overdue += 1
                if (
                    c.due_at is not None
                    and n <= c.due_at <= n + DUE_SOON_WINDOW
                    and alert(c.case_ref, "due_soon", c.due_at, "due_at")
                ):
                    tally.due_soon += 1
                if (
                    c.lifecycle == "waiting"
                    and c.wake_up_at is not None
                    and c.wake_up_at < n
                    and alert(c.case_ref, "stuck_waiting", c.wake_up_at, "wake_up_at")
                ):
                    tally.stuck_waiting += 1
                if (
                    staffing == "simulated_on_shift"
                    and c.lifecycle == "unassigned"
                    and c.owner_role is None
                    and n - c.created_at >= UNOWNED_AFTER
                    and alert(c.case_ref, "unowned", c.created_at, "created_at")
                ):
                    tally.unowned += 1
            for p in tx.cases.promises.list_open_past(n):
                if tx.cases.promises.set_status(p.case_ref, "missed", n, PROMISE_MISSED_REASON):
                    tally.promises_missed += 1
                due = p.promise.due_at
                if due is None:  # list_open_past returns dated rows only
                    continue
                key = format_wall(due)
                if not tx.cases.case_events.exists(p.case_ref, PROMISE_MISSED_KIND, key):
                    tx.cases.case_events.append(
                        CaseEventRow.model_validate(
                            {
                                "case_ref": str(p.case_ref),
                                "kind": PROMISE_MISSED_KIND,
                                "key": key,
                                "actor_role": "system",
                                "job_run_id": job_run_id,
                                "detail": {"promise_id": p.id, "due_at": key},
                                "at": n,
                            }
                        )
                    )
            tx.commit()
        counts.overdue = tally.overdue
        counts.due_soon = tally.due_soon
        counts.stuck_waiting = tally.stuck_waiting
        counts.unowned = tally.unowned
        counts.promises_missed = tally.promises_missed

    def _sweep(self, wall_start: datetime, counts: _Counts) -> None:
        """Wall-clock abandonment: writes only `abandoned`, never another outcome (cases A-7)."""
        cutoff = wall_start - ABANDON_AFTER
        done = 0
        with self._uow(write=True) as tx:
            for thread_id, last in tx.core.conversations.idle_live(cutoff):
                tx.core.conversations.set_outcome(thread_id, "abandoned", ended_wall_at=last + ABANDON_AFTER)
                done += 1
            tx.commit()
        counts.abandoned = done


class SchedulerThread:
    """S-19: one in-process daemon thread, no runner port. `stop()` is its closer."""

    def __init__(
        self,
        tick: Callable[[], object],
        *,
        interval_s: float = TICK_INTERVAL_S,
        name: str = "meridian-scheduler",
    ) -> None:
        self._tick = tick
        self._interval_s = interval_s
        self._name = name
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("scheduler already started")
        self._thread = threading.Thread(target=self._run, name=self._name, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while True:
            try:
                self._tick()
            except Exception as exc:
                _log.warning("scheduler tick raised", extra={"exc_type": type(exc).__name__})
            if self._stop.wait(self._interval_s):
                return

    def stop(self, timeout_s: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout_s)

    @property
    def alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
