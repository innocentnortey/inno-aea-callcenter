"""Serve stored measures without recomputing outcomes (A10b, AEA-53; stage7/cases.md section 9; DO-3 section 4.4).

Each method opens one read-only unit of work, counts and divides stored fields, and returns a mapping with the OpenAPI
field names (web.md section 4 MetricsReads, structurally). It never runs a gate, a check, a policy rule or a model,
never applies an alert line (AlertEvaluator does) and never re-judges an outcome or re-scores an eval run (the writers
store them).
"""

from __future__ import annotations

import json
import logging
import math
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, time, timedelta
from typing import Final, Protocol
from zoneinfo import ZoneInfo

from meridian.adapters.sqlite.repos_metrics import CaseFact, ConversationFact, PromiseFact, TurnFact
from meridian.adapters.sqlite.repos_ops import ALERT_TYPES, StoredEvalRun
from meridian.domain.common import HandoffReason
from meridian.policy.texts import TextId, format_usd, render
from meridian.ports.runtime import Clock, UnitOfWorkFactory
from meridian.services._case_rules import LIFECYCLE_WORD, reason_label
from meridian.services.health import AlertSettings

CHICAGO: Final = ZoneInfo("America/Chicago")
HANDLED_TOPICS: Final = frozenset({"booking", "membership", "billing", "warranty"})
FAILURE_REASONS: Final = frozenset({"model_error", "tool_error", "timeout"})
OWNER_TAGS: Final = ("live", "seed")
LIVE_TAGS: Final = ("live",)

NO_CONVERSATIONS: Final = "No conversations since the reset."
NO_HANDLED_TOPIC: Final = "No ended conversations on a handled topic yet."
NO_PROMISES_DUE: Final = "No promises are due yet."
NO_TURNS: Final = "No turns yet"
NO_JOB_RUN: Final = "The overdue job has not run yet"
SPEND_DAY: Final = "America/Chicago midnight to midnight"
DEV_LABEL: Final = "Dev (we read and fixed these, so it overstates)"
NORTH_STAR_LINK_LABEL: Final = "The measured number is on the Evaluation page (latest held-out run)."
M3_OWNER_LABEL: Final = "Estimate from live chats (no verified answers)"
M3_MONITOR_LABEL: Final = (
    "Estimate of correct resolution from live chats (the measured number is on the Evaluation page)"
)

OUTCOME_ROWS: Final[tuple[tuple[str, str], ...]] = (
    ("ai_resolved", "Resolved by the AI"),
    ("handed_off", "Handed off to a person"),
    ("safety_reply", "Safety reply given"),
    ("abandoned", "Abandoned"),
)
HEALTH_TILES: Final[tuple[tuple[str, str, str], ...]] = (
    ("M-22", "Conversations", "count"),
    ("M-22", "Turns", "count"),
    ("M-24", "Failures", "count"),
    ("M-23", "Latency p50", "ms"),
    ("M-23", "Latency p95", "ms"),
    ("scheduler_last_run", "Overdue job last ran", "ms"),
    ("handoff_only", "Handoff-only mode (1 = on)", "count"),
)
MONITOR_ALERT_TYPES: Final = tuple(a for a in ALERT_TYPES if a != "scheduler_stale")
DECISION_LINE: Final[Mapping[str, TextId]] = {
    "spend_cap_reached": TextId.MONITOR_SPEND_CAP,
    "p95_latency_over_12_5s": TextId.MONITOR_LATENCY,
    "health_check_restart": TextId.MONITOR_RESTART,
    "zero_traffic": TextId.MONITOR_ZERO_TRAFFIC,
    "failure_rate_over_2pct": TextId.MONITOR_FAILURE_RATE,
    "trace_export_failed": TextId.MONITOR_TRACE_EXPORT,
}
EVAL_RUN_KEYS: Final = ("run_id", "date", "agent_version", "size", "mix", "measures", "dev_failures")
_LOG = logging.getLogger("meridian.reads")


class MetricsLedger(Protocol):
    def spend_today(self) -> float: ...
    def models_disabled(self) -> bool: ...
    def open_circuits(self) -> tuple[str, ...]: ...


def _chicago(at: datetime) -> datetime:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("naive datetime")
    return at.astimezone(CHICAGO)


def _next_chicago_midnight(now: datetime) -> datetime:
    local = _chicago(now)
    return datetime.combine(local.date() + timedelta(days=1), time(0), tzinfo=CHICAGO)


def _nearest_rank(values: Sequence[int], q: float) -> int:
    ordered = sorted(values)
    return ordered[math.ceil(q * len(ordered)) - 1]


def _share(
    mid: str,
    label: str,
    numerator: int,
    denominator: int,
    null_reason: str,
    case_refs: Sequence[str],
    *,
    kind: str = "measured",
) -> dict[str, object]:
    if denominator == 0:
        return {
            "id": mid,
            "label": label,
            "numerator": 0,
            "denominator": 0,
            "unit": "share",
            "value": None,
            "null_reason": null_reason,
            "kind": kind,
            "case_refs": [],
        }
    return {
        "id": mid,
        "label": label,
        "numerator": numerator,
        "denominator": denominator,
        "unit": "share",
        "value": numerator / denominator,
        "null_reason": None,
        "kind": kind,
        "case_refs": sorted(set(case_refs)),
    }


def _tile(
    tid: str,
    label: str,
    unit: str,
    value: int | float | None,
    *,
    numerator: int | None = None,
    denominator: int | None = None,
    null_reason: str | None = None,
) -> dict[str, object]:
    return {
        "id": tid,
        "label": label,
        "value": value,
        "unit": unit,
        "numerator": numerator,
        "denominator": denominator,
        "null_reason": null_reason,
    }


def _m3(conversations: Sequence[ConversationFact]) -> tuple[int, int, list[str], str | None]:
    """D-1: live, ended, at least one handled-topic turn; numerator ai_resolved and never flagged."""
    live = [c for c in conversations if c.run_tag == "live"]
    ended = [c for c in live if c.outcome != "open"]
    population = [c for c in ended if HANDLED_TOPICS.intersection(c.topics)]
    numerator = [c.thread_id for c in population if c.outcome == "ai_resolved" and c.flag_count == 0]
    reason = None
    if not population:
        reason = NO_HANDLED_TOPIC if ended else NO_CONVERSATIONS
    return len(numerator), len(population), numerator, reason


def _refs_on(threads: Sequence[str], cases: Sequence[CaseFact]) -> list[str]:
    wanted = set(threads)
    return [k.case_ref for k in cases if k.thread_id in wanted]


def _eval_split(run: StoredEvalRun | None) -> tuple[dict[str, object] | None, object]:
    """D-10: project the stored summary onto EvalRun's keys; an unreadable report is 'no run'."""
    if run is None:
        return None, None
    try:
        summary = json.loads(run.summary_json)
    except ValueError:
        summary = None
    if not isinstance(summary, dict) or any(k not in summary for k in EVAL_RUN_KEYS):
        _LOG.warning("eval_summary_unreadable run_id=%s", run.run_id)
        return None, None
    return {k: summary[k] for k in EVAL_RUN_KEYS}, summary.get("headline")


class MetricsReader:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        demo_clock: Clock,
        wall_clock: Callable[[], datetime],
        ledger: MetricsLedger,
        settings: AlertSettings,
        current_agent_version: str,
        daily_cap_usd: float,
    ) -> None:
        self._uow = uow
        self._demo_clock = demo_clock
        self._wall_clock = wall_clock
        self._ledger = ledger
        self._settings = settings
        self._agent_version = current_agent_version
        self._daily_cap_usd = daily_cap_usd

    # -- CON-18 ------------------------------------------------------------------------------------------------
    def owner_metrics(self) -> Mapping[str, object]:
        with self._uow() as tx:
            conversations = tx.ops.metrics.conversations(OWNER_TAGS)
            cases = tx.ops.metrics.cases(OWNER_TAGS)
            promises = tx.ops.metrics.promises(OWNER_TAGS)
        return self._owner_page(conversations, cases, promises)

    def _owner_page(
        self,
        conversations: Sequence[ConversationFact],
        cases: Sequence[CaseFact],
        promises: Sequence[PromiseFact],
    ) -> Mapping[str, object]:
        by_case = {k.case_ref: k for k in cases}
        ended = [c for c in conversations if c.outcome != "open"]

        m3_num, m3_den, m3_threads, m3_reason = _m3(conversations)
        in_scope = _share(
            "M-3", M3_OWNER_LABEL, m3_num, m3_den, m3_reason or NO_HANDLED_TOPIC,
            _refs_on(m3_threads, cases), kind="estimate",
        )  # fmt: skip

        due = [p for p in promises if p.due_at is not None and p.status in ("kept", "missed")]
        kept = [p for p in due if p.status == "kept"]
        kept_measure = _share(
            "M-13", "Promises kept on time", len(kept), len(due), NO_PROMISES_DUE, [p.case_ref for p in kept]
        )

        handed = [c.thread_id for c in ended if c.outcome == "handed_off"]
        handoffs = _share(
            "M-18",
            "Handoffs (all reasons)",
            len(handed),
            len(ended),
            NO_CONVERSATIONS,
            _refs_on(handed, cases),
        )

        outcomes: list[dict[str, object]] = []
        if ended:
            for outcome, label in OUTCOME_ROWS:
                threads = [c.thread_id for c in ended if c.outcome == outcome]
                outcomes.append(
                    _share(
                        "M-18", label, len(threads), len(ended), NO_CONVERSATIONS, _refs_on(threads, cases)
                    )
                )

        by_reason: dict[str, list[str]] = {}
        for k in cases:
            by_reason.setdefault(k.reason, []).append(k.case_ref)
        reason_rows = [
            _share("M-22", reason_label(HandoffReason(reason)), len(refs), len(cases), NO_CONVERSATIONS, refs)
            for reason, refs in by_reason.items()
        ]
        reason_rows.sort(key=lambda m: (-int(str(m["numerator"])), str(m["label"])))

        missed = [p for p in promises if p.status == "missed" and p.due_at is not None]
        missed_promises = [
            {
                "reference": p.case_ref,
                "due_at": _chicago(p.due_at),  # type: ignore[arg-type]
                "outcome": LIFECYCLE_WORD[by_case[p.case_ref].lifecycle],
            }
            for p in missed
        ]

        refs: set[str] = {p.case_ref for p in missed}
        for measure in (in_scope, kept_measure, handoffs, *outcomes, *reason_rows):
            refs.update(str(r) for r in measure["case_refs"])  # type: ignore[attr-defined]
        case_lines = [
            {
                "reference": ref,
                "reason": reason_label(HandoffReason(by_case[ref].reason), by_case[ref].safety_kind),
                "status": LIFECYCLE_WORD[by_case[ref].lifecycle],
            }
            for ref in sorted(refs)
        ]
        seed_count = sum(1 for k in cases if k.seed)
        return {
            "as_of": _chicago(self._demo_clock.now()),
            "seeds_included": seed_count > 0,
            "seed_count": seed_count,
            "in_scope_correct_resolution": in_scope,
            "measured_north_star_link": {"label": NORTH_STAR_LINK_LABEL, "path": "/eval"},
            "promises_kept_on_time": kept_measure,
            "handoffs": handoffs,
            "outcomes": outcomes,
            "handoffs_by_reason": reason_rows,
            "missed_promises": missed_promises,
            "cases": case_lines,
        }

    # -- CON-19 ------------------------------------------------------------------------------------------------
    def monitoring(self) -> Mapping[str, object]:
        wall_now = self._wall_clock()
        wall_local = _chicago(wall_now)
        spent = self._ledger.spend_today()
        handoff_only = self._ledger.models_disabled() or bool(self._ledger.open_circuits())
        with self._uow() as tx:
            conversations = tx.ops.metrics.conversations(LIVE_TAGS)
            turns = tx.ops.metrics.live_turns()
            cases = tx.ops.metrics.cases(LIVE_TAGS)
            states = tx.ops.health.latest_alert_states()
            restart = tx.ops.health.last_restart()
            job = tx.cases.job_runs.latest()
        demo_now = self._demo_clock.now()

        min_turns = self._settings.min_turns
        durations = [t.server_ms for t in turns if t.server_ms is not None]
        if not durations:
            latency_reason: str | None = NO_TURNS
        elif len(durations) < min_turns:
            latency_reason = f"Not enough turns yet (fewer than {min_turns})"
        else:
            latency_reason = None

        def latency(q: float) -> int | None:
            return None if latency_reason is not None else _nearest_rank(durations, q)

        failures = sum(1 for t in turns if _failed(t))
        tile_values: list[dict[str, object]] = []
        tile_values.append(_tile(*HEALTH_TILES[0], len(conversations)))
        tile_values.append(_tile(*HEALTH_TILES[1], len(turns)))
        if turns:
            tile_values.append(_tile(*HEALTH_TILES[2], failures, numerator=failures, denominator=len(turns)))
        else:
            tile_values.append(_tile(*HEALTH_TILES[2], None, null_reason=NO_TURNS))
        tile_values.append(_tile(*HEALTH_TILES[3], latency(0.5), null_reason=latency_reason))
        tile_values.append(_tile(*HEALTH_TILES[4], latency(0.95), null_reason=latency_reason))
        if job is None:
            tile_values.append(_tile(*HEALTH_TILES[5], None, null_reason=NO_JOB_RUN))
        else:
            ms = max(0, int((wall_now - job.started_wall_at).total_seconds() * 1000))
            tile_values.append(_tile(*HEALTH_TILES[5], ms))
        tile_values.append(_tile(*HEALTH_TILES[6], 1 if handoff_only else 0))

        m3_num, m3_den, _threads, m3_reason = _m3(conversations)
        if m3_den == 0:
            containment = _tile("M-3", M3_MONITOR_LABEL, "share", None, null_reason=m3_reason)
        else:
            containment = _tile(
                "M-3", M3_MONITOR_LABEL, "share", m3_num / m3_den, numerator=m3_num, denominator=m3_den
            )
        counts = Counter(k.reason for k in cases)
        escalations = [
            _tile("M-22", reason_label(HandoffReason(reason)), "count", n) for reason, n in counts.items()
        ]
        escalations.sort(key=lambda t: (-int(str(t["value"])), str(t["label"])))

        cap_cents = round(self._daily_cap_usd * 100)
        alerts = []
        for alert_type in MONITOR_ALERT_TYPES:
            state = states[alert_type]
            line = DECISION_LINE[alert_type]
            text = (
                render(line, amount=format_usd(cap_cents))
                if line is TextId.MONITOR_SPEND_CAP
                else render(line)
            )
            firing = state.state == "firing" and state.fired_at is not None
            alerts.append(
                {
                    "type": alert_type,
                    "state": state.state,
                    "fired_at": _chicago(state.fired_at) if firing and state.fired_at is not None else None,
                    "decision_line": text,
                }
            )
        s = self._settings
        sent = sum(1 for t in turns if t.trace_export == "sent")
        return {
            "as_of": wall_local,
            "demo_now": _chicago(demo_now),
            "health": tile_values,
            "spend": {
                "today_cents": round(spent * 100),
                "cap_cents": cap_cents,
                "day": SPEND_DAY,
                "resets_at": _next_chicago_midnight(wall_now),
            },
            "correctness": {"containment_estimate": containment, "escalations_by_reason": escalations},
            "alerts": alerts,
            "alert_config": {
                "zero_traffic_after_hours": int(s.zero_traffic_after.total_seconds() // 3600),
                "quiet_hours": {
                    "start": s.quiet_start.strftime("%H:%M"),
                    "end": s.quiet_end.strftime("%H:%M"),
                    "timezone": s.tz,
                    "configurable": True,
                },
            },
            "last_restart": None
            if restart is None
            else {"at": _chicago(restart.at_wall), "kind": "health_check"},
            "trace_export": f"sent {sent} of {len(turns)} turns",
            "redacted": True,
        }

    # -- CON-20 ------------------------------------------------------------------------------------------------
    def latest_eval(self) -> Mapping[str, object]:
        with self._uow() as tx:
            dev = tx.ops.eval.latest_completed("e2e", "dev")
            held = tx.ops.eval.latest_completed("e2e", "held-out")
        dev_split, _ = _eval_split(dev)
        held_split, stored_headline = _eval_split(held)
        headline = stored_headline if held_split is not None and isinstance(stored_headline, dict) else None
        return {
            "splits": {"dev": dev_split, "held_out": held_split},
            "headline": headline,
            "current_agent_version": self._agent_version,
            "dev_label": DEV_LABEL,
        }


def _failed(turn: TurnFact) -> bool:
    return turn.outcome == "degraded_handoff" and turn.degrade_reason in FAILURE_REASONS
