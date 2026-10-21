"""Builders shared by the AEA-53 tests (no test functions here). Rows go in through the real writers' repositories;
raw SQL appears only in assertions. Synthetic values only; every sentinel is generated per run and never printed."""

from __future__ import annotations

import functools
import json
import secrets
import string
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from meridian.adapters.sqlite.repos_cases import DEMO_START, CaseRow
from meridian.adapters.sqlite.repos_ops import HealthEvent
from meridian.adapters.sqlite.repos_staff import FlagRow
from meridian.domain.common import CaseRef, HandoffReason, ThreadId
from meridian.domain.turn import TurnIds, TurnRecord
from meridian.policy.handoff import case_due_at, priority_for, promise_for
from meridian.ports.models import CallRecord, Role
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.services.handoff import BriefAssembler
from meridian.services.metrics_reader import MetricsReader
from meridian.services.reset import seed_demo, seed_first_boot
from tests.unit.adapters.sqlite.helpers import conversation, new_thread, new_turn, turn_ids

CHI = ZoneInfo("America/Chicago")
WALL_NOW = datetime(2026, 10, 21, 20, 15, tzinfo=UTC)  # 15:15 Chicago
DEMO_NOW = DEMO_START


class WallClock:
    """A callable wall clock with a mutable `.now`."""

    def __init__(self, now: datetime = WALL_NOW) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class Pages:
    """A MetricsReader whose pages come back as plain dicts, so assertions can index them."""

    def __init__(self, reader: MetricsReader) -> None:
        self._reader = reader

    def owner_metrics(self) -> dict[str, Any]:
        return dict(self._reader.owner_metrics())

    def monitoring(self) -> dict[str, Any]:
        return dict(self._reader.monitoring())

    def latest_eval(self) -> dict[str, Any]:
        return dict(self._reader.latest_eval())


class LedgerDouble:
    def __init__(self, spent: float = 0.0, circuits: tuple[str, ...] = (), capped: bool = False) -> None:
        self.spent = spent
        self.circuits = circuits
        self.capped = capped

    def spend_today(self) -> float:
        return self.spent

    def open_circuits(self) -> tuple[str, ...]:
        return self.circuits

    def models_disabled(self) -> bool:
        return bool(self.circuits) or self.capped


# -- turns -------------------------------------------------------------------------------------------------------
def turn_record_for(
    *,
    gate_result: str = "clear",
    path: str = "talk",
    outcome: str = "answered",
    degrade_reason: str | None = None,
    topic: str | None = "billing",
    server_ms: int | None = 1200,
    trace_export: str = "off",
    trace_id: str | None = None,
    response: str | None = None,
) -> TurnRecord:
    planner: dict[str, Any] | None = {
        "model": "test-planner",
        "fallback_used": False,
        "failure": None,
        "plan_mode": "talk",
        "plan_source": "planner",
        "intents": [],
        "handoff_request": None,
        "topic": topic,
        "planner_failed": False,
    }
    if topic is None:
        planner = None
    return TurnRecord.model_validate(
        {
            "status": "completed",
            "trace": {
                "gate_result": gate_result,
                "path": path,
                "outcome": outcome,
                "degrade_reason": degrade_reason,
                "planner": planner,
                "danger_raised": False,
                "specialists_run": [],
            },
            "replied_at": WALL_NOW,
            "server_ms": server_ms,
            "model_calls": 2,
            "input_tokens": 100,
            "output_tokens": 40,
            "cost_usd": 0.0125,
            "tool_calls": 1,
            "trace_id": trace_id,
            "trace_export": trace_export,
            "response": response if response is not None else "synthetic reply " + uuid4().hex[:6],
        }
    )


def add_turn(uow: UnitOfWorkFactory, thread: ThreadId, *, run_tag: str = "live", **record_kw: Any) -> TurnIds:
    ids = turn_ids(thread, new_turn(), run_tag=run_tag)
    with uow(write=True) as tx:
        tx.core.turns.begin(ids, DEMO_START)
        tx.core.turns.finish(ids.turn_id, turn_record_for(**record_kw))
        tx.commit()
    return ids


# -- conversations, cases, flags -----------------------------------------------------------------------------------
def add_conversation(
    uow: UnitOfWorkFactory,
    *,
    run_tag: str = "live",
    outcome: str = "open",
    last_customer_wall_at: datetime | None = None,
) -> ThreadId:
    thread = new_thread()
    with uow(write=True) as tx:
        tx.core.conversations.insert(
            conversation(
                thread,
                run_tag=run_tag,
                started_wall_at=WALL_NOW,
                last_customer_wall_at=last_customer_wall_at,
            )
        )
        if outcome != "open":
            tx.core.conversations.set_outcome(thread, outcome, ended_wall_at=WALL_NOW)
        tx.commit()
    return thread


def add_case(
    uow: UnitOfWorkFactory,
    thread: ThreadId,
    *,
    reason: HandoffReason,
    lifecycle: str = "unassigned",
    safety_kind: str | None = None,
    missed: bool = False,
) -> CaseRef:
    with uow(write=True) as tx:
        ref = tx.cases.refs.next_case_ref()
        promise = promise_for(reason, "nobody_online", DEMO_NOW)
        tx.cases.cases.insert(
            CaseRow.model_validate(
                {
                    "case_ref": ref,
                    "thread_id": thread,
                    "reason": reason,
                    "priority": priority_for(reason, promise_due=promise.due_at),
                    "rule_id": "test.rule",
                    "trigger": "escalation",
                    "lifecycle": lifecycle,
                    "due_at": case_due_at(reason, promise, None),
                    "safety_kind": safety_kind,
                    "created_at": DEMO_NOW,
                    "updated_at": DEMO_NOW,
                }
            )
        )
        tx.cases.promises.insert(ref, promise, DEMO_NOW)
        if missed and promise.due_at is not None:
            tx.cases.promises.set_status(ref, "missed", DEMO_NOW, "past_due")
        tx.commit()
    return ref


def add_flag(uow: UnitOfWorkFactory, ref: CaseRef) -> None:
    with uow(write=True) as tx:
        tx.staff.flags.insert(
            FlagRow.model_validate(
                {
                    "case_ref": ref,
                    "target": "answer",
                    "message_id": None,
                    "note": None,
                    "reason": None,
                    "flagged_by_role": "supervisor",
                    "flagged_at": DEMO_NOW,
                    "status": "new",
                    "reviewed_by_role": None,
                    "reviewed_note": None,
                    "reviewed_at": None,
                }
            )
        )
        tx.commit()


def call_record(cost: float) -> CallRecord:
    return CallRecord.model_validate(
        {
            "provider": "anthropic",
            "model": "claude-sonnet-test",
            "latency_ms": 1200,
            "input_tokens": 9000,
            "output_tokens": 700,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "thinking_tokens": 0,
            "cost_usd": cost,
            "cost_source": "price_table",
            "status": "ok",
            "failure": None,
            "provider_request_id": "req_test_0001",
            "stop_reason": "end_turn",
            "role": Role.RESPONDER,
            "attempt": 1,
        }
    )


# -- eval reports ----------------------------------------------------------------------------------------------------
def _measures(split: str) -> list[dict[str, Any]]:
    if split == "held-out":
        return [
            {"id": "M-1", "label": "In-scope correct resolution (held-out)", "numerator": 3, "denominator": 4,
             "value": 0.75, "min": 0.5, "max": 0.75, "target": "≥ 90% per handled topic"},
            {"id": "M-1:billing", "label": "In-scope correct resolution: billing (held-out)", "numerator": 3,
             "denominator": 4, "value": 0.75, "min": 0.5, "max": 0.75, "target": "≥ 90% for this topic"},
            {"id": "M-19", "label": "Escalation recall on out-of-scope cases", "numerator": 1, "denominator": 1,
             "value": 1.0, "min": 1.0, "max": 1.0, "target": "≥ 95%"},
        ]  # fmt: skip
    return [
        {"id": "M-2", "label": "In-scope correct resolution (dev)", "numerator": 2, "denominator": 4,
         "value": 0.5, "min": 0.25, "max": 0.5, "target": None},
        {"id": "M-4", "label": "Scope coverage: in-scope cases", "numerator": 4, "denominator": 4,
         "value": 1.0, "min": 1.0, "max": 1.0, "target": None},
    ]  # fmt: skip


def _report(
    split: str,
    agent_version: str,
    *,
    incomplete: bool = False,
    started: str = "2026-10-21T18:00:00+00:00",
    finished: str | None = "2026-10-21T18:30:00+00:00",
    dev_failure_text: str = "Quoted the stale fee for [name].",
    quote: str | None = None,
) -> tuple[str, dict[str, Any]]:
    rid = f"e2e-{split}-{uuid4().hex[:6]}"
    status = "incomplete" if incomplete else "completed"
    run = {
        "run_id": rid, "suite": "e2e", "split": split, "agent_version": agent_version,
        "harness_commit": "testcommit", "harness_digest": "testdigest", "experiment_id": None, "repeats": 3,
        "started_at": started, "finished_at": None if incomplete else finished, "status": status,
        "cases_expected": 4, "cases_scored": 3 if incomplete else 4, "index_manifest_hash": None,
        "judge_spend_usd": 0.0,
    }  # fmt: skip
    results = []
    for i in range(4):
        item: dict[str, Any] = {"item": "must_do", "index": 0, "passed": True}
        if quote is not None and split == "dev":
            item["failing_quote"] = quote
        results.append(
            {"run_id": rid, "case_id": f"{split}-00{i}", "repeat": 1, "thread_id": None, "passed_hard": True,
             "items": [item], "outcome": "resolved", "in_scope": True, "topic": "billing"}
        )  # fmt: skip
    measures = _measures(split)
    summary = {
        "run_id": rid, "date": "2026-10-21", "agent_version": agent_version, "size": 4,
        "mix": [{"category": "billing", "count": 4, "origin": "transcript", "tests": None}],
        "measures": measures, "suite": "e2e", "split": split, "split_label": split, "status": status,
        "repeats": 3, "experiment_id": None,
        "headline": dict(measures[0]) if split == "held-out" else None,
        "dev_failures": [{"case_id": "dev-001", "redacted_summary": dev_failure_text}] if split == "dev" else [],
        "gates": {}, "failure_rows": [], "topic_readiness": {}, "db_check": {"status": "not_run"},
        "unscored_cases": [], "judge": {"enabled": False}, "cost_per_conversation_usd": None, "withheld": None,
        "empty_measures": [], "not_measured": [],
    }  # fmt: skip
    return rid, {"run": run, "results": results, "summary": summary}


def write_eval_reports(
    directory: Path,
    *,
    agent_version: str,
    dev: bool = True,
    held_out: bool = True,
    held_out_incomplete: bool = False,
    extra_incomplete_held_out: bool = False,
    dev_failure_text: str = "Quoted the stale fee for [name].",
    quote: str | None = None,
) -> dict[str, str]:
    """One <run_id>.json per run, shaped {"run", "results", "summary"}; returns {split: run_id}."""
    directory.mkdir(parents=True, exist_ok=True)
    made: dict[str, str] = {}
    jobs: list[tuple[str, dict[str, Any]]] = []
    if dev:
        jobs.append(("dev", {"dev_failure_text": dev_failure_text, "quote": quote}))
    if held_out:
        jobs.append(("held-out", {"incomplete": held_out_incomplete}))
    for split, kw in jobs:
        rid, doc = _report(split, agent_version, **kw)
        made[split] = rid
        (directory / f"{rid}.json").write_text(json.dumps(doc), encoding="utf-8")
    if extra_incomplete_held_out:
        rid, doc = _report(
            "held-out", agent_version, incomplete=True, started="2026-10-21T19:00:00+00:00", finished=None
        )
        (directory / f"{rid}.json").write_text(json.dumps(doc), encoding="utf-8")
    return made


# -- sentinels -------------------------------------------------------------------------------------------------------
def _digits(n: int) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(n))


def sentinels() -> dict[str, str]:
    """Per-run values that must never appear on a page. Never print them."""
    return {
        "name": "Zq" + "".join(secrets.choice(string.ascii_letters) for _ in range(10)),
        "phone": "-".join((_digits(3), _digits(3), _digits(4))),
        "code": _digits(6),
        "card": "4" + _digits(15),
        "trace_id": "trace-" + uuid4().hex,
    }


# -- the J-10 rows -----------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class J10Rows:
    wp2: ThreadId
    wp5: ThreadId
    wp7: ThreadId
    failed: ThreadId
    flagged: ThreadId
    abandoned: ThreadId
    stale_open: ThreadId
    eval_thread: ThreadId
    load_thread: ThreadId
    wp5_case: CaseRef
    wp7_case: CaseRef
    flagged_case: CaseRef
    wp2_turn: TurnIds


def seed_j10_rows(uow: UnitOfWorkFactory, ledger: Any, *, with_seed: bool) -> J10Rows:
    if with_seed:
        seed_first_boot(uow, functools.partial(seed_demo, assembler=BriefAssembler()), WALL_NOW)
    stale = WALL_NOW - timedelta(hours=2)

    wp2 = add_conversation(uow, outcome="ai_resolved")
    first = add_turn(uow, wp2, path="act", outcome="acted", topic="billing", server_ms=2300)
    add_turn(uow, wp2, path="talk", outcome="answered", topic="billing", server_ms=1500)
    ledger.record(call_record(0.0123), first)
    ledger.record(call_record(0.0456), first)

    wp5 = add_conversation(uow, outcome="safety_reply")
    add_turn(uow, wp5, gate_result="safety", path="safety", outcome="safety_reply", topic=None, server_ms=40)
    wp5_case = add_case(uow, wp5, reason=HandoffReason.SAFETY, safety_kind="co")

    wp7 = add_conversation(uow, outcome="handed_off")
    add_turn(uow, wp7, path="handoff", outcome="handed_off", topic="billing", server_ms=3100)
    wp7_case = add_case(uow, wp7, reason=HandoffReason.REFUND, missed=True)

    failed = add_conversation(uow)
    add_turn(
        uow, failed, path="degraded", outcome="degraded_handoff", degrade_reason="model_error",
        topic=None, server_ms=60000,
    )  # fmt: skip

    flagged = add_conversation(uow, outcome="ai_resolved")
    add_turn(uow, flagged, path="talk", outcome="answered", topic="booking", server_ms=900)
    flagged_case = add_case(uow, flagged, reason=HandoffReason.UNSUPPORTED_ACTION, lifecycle="resolved")
    add_flag(uow, flagged_case)

    abandoned = add_conversation(uow, outcome="abandoned", last_customer_wall_at=stale)
    stale_open = add_conversation(uow, last_customer_wall_at=stale)

    eval_thread = add_conversation(uow, run_tag="eval", outcome="ai_resolved")
    add_turn(uow, eval_thread, run_tag="eval", topic="billing", server_ms=500)
    load_thread = add_conversation(uow, run_tag="load", outcome="ai_resolved")
    add_turn(uow, load_thread, run_tag="load", topic="billing", server_ms=500)

    with uow(write=True) as tx:
        tx.ops.health.append(
            HealthEvent(
                at_wall=WALL_NOW - timedelta(hours=3), kind="restart", alert_type=None,
                reason_code="healthz_failed_3_in_a_row", value=3.0, threshold=3.0, agent_version="test",
            )
        )  # fmt: skip
        tx.cases.job_runs.start("job-j10", started_wall_at=WALL_NOW - timedelta(minutes=2), demo_now=DEMO_NOW)
        tx.commit()
    return J10Rows(
        wp2, wp5, wp7, failed, flagged, abandoned, stale_open, eval_thread, load_thread,
        wp5_case, wp7_case, flagged_case, first,
    )  # fmt: skip
