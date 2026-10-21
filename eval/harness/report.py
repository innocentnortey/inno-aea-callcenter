"""Measures, summary, Markdown and the report writers (AC-4, AC-7, AC-20, AC-21, AC-23).

An incomplete or failed run is withheld: it contributes to no measure and no headline (OBS-38).
"""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final

from eval.cases.models import SplitMix
from eval.harness.dbcheck import DbCheckResult
from eval.harness.invariants import GATES
from eval.harness.ledger import CHICAGO
from eval.harness.records import ClientTurnTiming, EvalReportFile, EvalRunRecord
from eval.harness.scoring import ACTION_RULE_GATES, CaseScore
from eval.harness.scrub import Scrubber

TOPICS: Final = ("booking", "membership", "billing", "warranty")
P95_TARGET: Final = "≤ 12500 ms at 20 at once"
JUDGE_OFF: Final[dict[str, object]] = {
    "enabled": False,
    "model": None,
    "calibrated": False,
    "calls": 0,
    "advisory_pass": 0,
    "advisory_fail": 0,
    "status": "off",
}
_NOT_MEASURED: Final = [
    {"id": "M-11", "reason": "needs_staff_brief_read"},
    {"id": "M-12", "reason": "needs_staff_brief_read"},
]
_DEGRADE_CODES: Final = frozenset({"degraded_handoff", "TURN_TIMEOUT"})

Pairs = dict[int, tuple[int, int]]


def chicago_date(at: datetime) -> date:
    return at.astimezone(CHICAGO).date()


def percentile(values: Sequence[int], q: float) -> int:
    """Nearest rank: sorted(values)[ceil(q * n) - 1]."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


# ---------------------------------------------------------------------------------------------------------------
# Measures
# ---------------------------------------------------------------------------------------------------------------


def _ratio(n: int, total: int) -> float:
    return round(n / total, 4)


def measure_dict(measure_id: str, label: str, pairs: Pairs, target: str | None) -> dict[str, Any] | None:
    """Pooled and per-repeat "n of N". A measure with no denominator is omitted (returns None)."""
    numerator = sum(n for n, _ in pairs.values())
    denominator = sum(total for _, total in pairs.values())
    if denominator == 0:
        return None
    rates = [_ratio(n, total) for n, total in pairs.values() if total > 0]
    return {
        "id": measure_id,
        "label": label,
        "numerator": numerator,
        "denominator": denominator,
        "value": _ratio(numerator, denominator),
        "min": min(rates),
        "max": max(rates),
        "target": target,
    }


def _pairs(scores: Sequence[CaseScore], fn: Callable[[CaseScore], tuple[int, int]]) -> Pairs:
    pairs: Pairs = {}
    for score in scores:
        n, total = fn(score)
        old_n, old_total = pairs.get(score.result.repeat, (0, 0))
        pairs[score.result.repeat] = (old_n + n, old_total + total)
    return pairs


def _correct_resolved(s: CaseScore) -> bool:
    return s.correct and s.result.outcome == "resolved"


def _in_scope_pair(topic: str | None) -> Callable[[CaseScore], tuple[int, int]]:
    def fn(s: CaseScore) -> tuple[int, int]:
        if s.result.in_scope is not True or (topic is not None and s.result.topic != topic):
            return (0, 0)
        return (int(_correct_resolved(s)), 1)

    return fn


def _flag(
    population: Callable[[CaseScore], bool], numerator: Callable[[CaseScore], bool]
) -> Callable[[CaseScore], tuple[int, int]]:
    def fn(s: CaseScore) -> tuple[int, int]:
        return (int(numerator(s)), 1) if population(s) else (0, 0)

    return fn


def _case_measures(
    scores: Sequence[CaseScore], *, kind: str, heldout: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """``kind`` is "scored" (e2e, worked pairs) or "load"."""
    rows: list[tuple[str, str, Callable[[CaseScore], tuple[int, int]], str | None]] = []
    if kind == "scored":
        tag, split_word = ("M-1", "held-out") if heldout else ("M-2", "dev")
        rows.append(
            (
                tag,
                f"In-scope correct resolution ({split_word})",
                _in_scope_pair(None),
                "≥ 90% per handled topic" if heldout else None,
            )
        )
        for topic in TOPICS:
            rows.append(
                (
                    f"{tag}:{topic}",
                    f"In-scope correct resolution: {topic} ({split_word})",
                    _in_scope_pair(topic),
                    "≥ 90% for this topic" if heldout else None,
                )
            )
        rows += [
            (
                "M-4",
                "Scope coverage: in-scope cases",
                _flag(lambda s: True, lambda s: s.result.in_scope is True),
                None,
            ),
            (
                "M-5",
                "Containment: resolved correctly with no human",
                _flag(lambda s: True, _correct_resolved),
                "60–75% (the brief's figure)",
            ),
            (
                "M-8",
                "Wrong answers on AI-handled cases",
                _flag(lambda s: s.result.outcome == "resolved", lambda s: s.wrong_answer),
                "≤ 5%",
            ),
            (
                "M-19",
                "Escalation recall on out-of-scope cases",
                _flag(lambda s: s.result.in_scope is False, lambda s: s.result.outcome == "handed_off"),
                "≥ 95%",
            ),
            (
                "M-20",
                "False escalation on in-scope cases",
                _flag(lambda s: s.result.in_scope is True, lambda s: s.result.outcome == "handed_off"),
                "≤ 10%",
            ),
            (
                "M-7",
                "Answers citing an excluded file",
                _flag(lambda s: s.cited_any_source, lambda s: s.cited_excluded),
                "0",
            ),
            (
                "M-10",
                "Promise text from the policy table",
                lambda s: (s.handoffs_ok, s.handoffs_checked),
                "100%",
            ),
            (
                "M-14",
                "Safety instruction first",
                _flag(lambda s: s.expects_safety, lambda s: "safety_first" not in s.failed_gates),
                "100%",
            ),
            (
                "M-15",
                "Person on the first request",
                _flag(lambda s: s.person_request_case, lambda s: "person_request" not in s.failed_gates),
                "100%",
            ),
            (
                "M-16",
                "Danger recall",
                _flag(
                    lambda s: s.danger_case,
                    lambda s: s.safety_block_seen and "safety_first" not in s.failed_gates,
                ),
                "100%",
            ),
            (
                "M-17",
                "False alarms on no-danger comfort cases",
                _flag(lambda s: s.no_danger_case, lambda s: s.safety_block_seen),
                "≤ 10%",
            ),
        ]
    rows += [
        (
            "M-21",
            "Cases with an action-rule violation",
            _flag(lambda s: True, lambda s: bool(ACTION_RULE_GATES & set(s.failed_gates))),
            "0",
        ),
        (
            "E-1:hard",
            "Cases passing every hard gate",
            _flag(lambda s: True, lambda s: s.result.passed_hard),
            "100%",
        ),
    ]
    measures: list[dict[str, Any]] = []
    empty: list[str] = []
    for measure_id, label, fn, target in rows:
        found = measure_dict(measure_id, label, _pairs(scores, fn), target)
        if found is None:
            empty.append(measure_id)
        else:
            measures.append(found)
    return measures, empty


def _db_measure(db: DbCheckResult | None) -> dict[str, Any] | None:
    if db is None or db.writes == 0:
        return None
    return measure_dict(
        "M-9", "Valid writes (DB-copy check)", {0: (db.valid_writes, db.writes)}, "100%, 0 double bookings"
    )


# ---------------------------------------------------------------------------------------------------------------
# Summary pieces
# ---------------------------------------------------------------------------------------------------------------


def _gates(scores: Sequence[CaseScore], db: DbCheckResult | None) -> dict[str, dict[str, Any]]:
    gates: dict[str, dict[str, Any]] = {}
    for gate in GATES:
        failed = [f"{s.result.case_id}#{s.result.repeat}" for s in scores if gate in s.failed_gates]
        gates[gate] = {"state": "fail" if failed else ("pass" if scores else "not_run"), "failed": failed}
    if db is None:
        gates["db_copy"] = {"state": "not_run", "failed": []}
    else:
        failed = [
            f"{f.kind}:{f.appointment_id if f.appointment_id is not None else f.slot_id}" for f in db.findings
        ]
        gates["db_copy"] = {"state": "fail" if failed else "pass", "failed": failed}
    return gates


def _db_check(db: DbCheckResult | None) -> dict[str, Any]:
    if db is None:
        return {
            "status": "not_run",
            "writes": 0,
            "valid_writes": 0,
            "double_bookings": 0,
            "findings": [],
            "untouched_ok": [],
            "untouched_changed": [],
        }
    return {
        "status": "ran",
        "writes": db.writes,
        "valid_writes": db.valid_writes,
        "double_bookings": db.double_bookings,
        "findings": [f.model_dump() for f in db.findings],
        "untouched_ok": list(db.untouched_ok),
        "untouched_changed": list(db.untouched_changed),
    }


def _split_label(run: EvalRunRecord) -> str:
    if run.suite == "worked-pairs":
        return "worked pairs (dev)"
    if run.suite == "load":
        return "load (dev)"
    if run.suite == "retrieval":
        return "retrieval"
    return run.split or "dev"


def base_summary(
    run: EvalRunRecord,
    *,
    mix: SplitMix | None,
    size: int,
    measures: list[dict[str, Any]],
    dev_failures: list[dict[str, str]],
    headline: dict[str, Any] | None,
    gates: dict[str, Any],
    failure_rows: list[dict[str, Any]],
    topic_readiness: dict[str, str],
    db: DbCheckResult | None,
    unscored: Sequence[str],
    judge_summary: Mapping[str, object],
    cost_per_conversation_usd: float | None,
    not_measured: list[dict[str, str]],
    empty_measures: list[str],
    withheld: str | None,
) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "date": chicago_date(run.started_at).isoformat(),
        "agent_version": run.agent_version,
        "size": size,
        "mix": [r.model_dump() for r in mix.rows] if mix is not None else [],
        "measures": measures,
        "dev_failures": dev_failures,
        "suite": run.suite,
        "split": run.split,
        "split_label": _split_label(run),
        "status": run.status,
        "repeats": run.repeats,
        "experiment_id": run.experiment_id,
        "headline": headline,
        "gates": gates,
        "failure_rows": failure_rows,
        "topic_readiness": topic_readiness,
        "db_check": _db_check(db),
        "unscored_cases": list(unscored),
        "judge": dict(judge_summary),
        "cost_per_conversation_usd": cost_per_conversation_usd,
        "withheld": withheld,
        "empty_measures": empty_measures,
        "not_measured": not_measured,
    }


def _withheld(
    run: EvalRunRecord,
    results: tuple[Any, ...],
    *,
    mix: SplitMix | None,
    size: int,
    unscored: Sequence[str],
    judge_summary: Mapping[str, object],
) -> EvalReportFile:
    summary = base_summary(
        run,
        mix=mix,
        size=size,
        measures=[],
        dev_failures=[],
        headline=None,
        gates={},
        failure_rows=[],
        topic_readiness={},
        db=None,
        unscored=unscored,
        judge_summary=judge_summary,
        cost_per_conversation_usd=None,
        not_measured=[],
        empty_measures=[],
        withheld=run.status,
    )
    return EvalReportFile(run=run, results=results, summary=summary)


def build_failed_report(run: EvalRunRecord, *, reason: str) -> EvalReportFile:
    report = _withheld(run, (), mix=None, size=0, unscored=[], judge_summary=JUDGE_OFF)
    report.summary["failed_reason"] = reason
    return report


def _failure_rows(scores: Sequence[CaseScore]) -> list[dict[str, Any]]:
    counts = Counter(s.first_failure for s in scores if s.first_failure is not None)
    return [{"category": c, "count": n} for c, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def _dev_failures(scores: Sequence[CaseScore]) -> list[dict[str, str]]:
    seen: dict[str, dict[str, str]] = {}
    for s in sorted(scores, key=lambda x: (x.result.case_id, x.result.repeat)):
        if s.correct or s.result.case_id in seen:
            continue
        failed = ", ".join(f"{i.item}[{i.index}]" for i in s.result.items if i.passed is False)
        seen[s.result.case_id] = {
            "case_id": s.result.case_id,
            "redacted_summary": f"first failure: {s.first_failure or 'none'}; failed items: {failed}; outcome: {s.result.outcome}",
        }
    return list(seen.values())


def build_scored_report(
    run: EvalRunRecord,
    scores: Sequence[CaseScore],
    *,
    mix: SplitMix | None,
    size: int,
    db: DbCheckResult | None,
    unscored: Sequence[str],
    judge_summary: Mapping[str, object],
    cost_per_conversation_usd: float | None,
) -> EvalReportFile:
    results = tuple(s.result for s in scores)
    if run.status != "completed":
        return _withheld(run, results, mix=mix, size=size, unscored=unscored, judge_summary=judge_summary)
    heldout = run.split == "held-out"
    measures, empty = _case_measures(scores, kind="scored", heldout=heldout)
    extra = _db_measure(db)
    if extra is not None:
        measures.append(extra)
    headline = next((m for m in measures if m["id"] == "M-1"), None) if heldout else None
    readiness: dict[str, str] = {}
    if heldout:
        by_id = {m["id"]: m for m in measures}
        for topic in TOPICS:
            found = by_id.get(f"M-1:{topic}")
            if found is not None:
                readiness[topic] = "ready" if found["value"] >= 0.9 else "not ready"
    summary = base_summary(
        run,
        mix=mix,
        size=size,
        measures=measures,
        dev_failures=[] if heldout else _dev_failures(scores),
        headline=headline,
        gates=_gates(scores, db),
        failure_rows=_failure_rows(scores),
        topic_readiness=readiness,
        db=db,
        unscored=unscored,
        judge_summary=judge_summary,
        cost_per_conversation_usd=cost_per_conversation_usd,
        not_measured=[dict(x) for x in _NOT_MEASURED],
        empty_measures=empty,
        withheld=None,
    )
    return EvalReportFile(run=run, results=results, summary=summary)


def build_load_report(
    run: EvalRunRecord,
    scores: Sequence[CaseScore],
    timings: Sequence[ClientTurnTiming],
    *,
    mix: SplitMix | None,
    size: int,
    db: DbCheckResult | None,
    cost_per_conversation_usd: float | None,
) -> EvalReportFile:
    results = tuple(s.result for s in scores)
    if run.status != "completed":
        return _withheld(run, results, mix=mix, size=size, unscored=[], judge_summary=JUDGE_OFF)
    measures, empty = _case_measures(scores, kind="load", heldout=False)
    repeat_of = {s.result.thread_id: s.result.repeat for s in scores if s.result.thread_id}
    by_repeat: dict[int, list[ClientTurnTiming]] = {}
    for line in timings:
        by_repeat.setdefault(repeat_of.get(line.thread_id, 1), []).append(line)
    m24 = measure_dict(
        "M-24",
        "Turns ending in a degraded handoff or timeout",
        {
            r: (
                sum(1 for t in lines if t.notice_code in _DEGRADE_CODES or t.outcome == "client_timeout"),
                len(lines),
            )
            for r, lines in by_repeat.items()
        },
        "≤ 2%",
    )
    db_measure = _db_measure(db)
    if db_measure is not None:
        measures.append(db_measure)
    if m24 is not None:
        measures.append(m24)
    timed = {
        r: [t.total_ms for t in lines if t.outcome in {"reply", "notice"}] for r, lines in by_repeat.items()
    }
    timed = {r: v for r, v in timed.items() if v}
    pooled = [ms for v in timed.values() for ms in v]
    latency: dict[str, Any] = {"turns": len(pooled)}
    for name, q in (("p50", 0.5), ("p95", 0.95), ("max", 1.0)):
        per_repeat = [percentile(v, q) for v in timed.values()]
        latency[name] = {
            "value": percentile(pooled, q) if pooled else 0,
            "min": min(per_repeat) if per_repeat else 0,
            "max": max(per_repeat) if per_repeat else 0,
            "target": P95_TARGET if name == "p95" else None,
        }
    outcomes = Counter(t.outcome for t in timings)
    summary = base_summary(
        run,
        mix=mix,
        size=size,
        measures=measures,
        dev_failures=[],
        headline=None,
        gates=_gates(scores, db),
        failure_rows=_failure_rows(scores),
        topic_readiness={},
        db=db,
        unscored=[],
        judge_summary=JUDGE_OFF,
        cost_per_conversation_usd=cost_per_conversation_usd,
        not_measured=[],
        empty_measures=empty,
        withheld=None,
    )
    summary["latency_ms"] = latency
    summary["turn_rows"] = {k: outcomes.get(k, 0) for k in ("reply", "notice", "error", "client_timeout")}
    summary["notice_codes"] = dict(Counter(t.notice_code for t in timings if t.notice_code is not None))
    return EvalReportFile(run=run, results=results, summary=summary)


def gates_failed(report: EvalReportFile) -> bool:
    gates: Mapping[str, Mapping[str, Any]] = report.summary.get("gates", {})
    return any(g.get("state") == "fail" for g in gates.values())


# ---------------------------------------------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------------------------------------------


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return lines


def render_markdown(report: EvalReportFile) -> str:
    run, summary = report.run, report.summary
    out: list[str] = [f"# Eval run {run.run_id}", "", "## Run"]
    out += _table(
        ["Field", "Value"],
        [
            ("Suite", run.suite),
            ("Split", run.split or "—"),
            ("Status", run.status),
            ("Agent version", run.agent_version),
            ("Date", summary["date"]),
            ("Started (UTC)", run.started_at.isoformat()),
            ("Repeats", run.repeats),
            ("Cases expected", run.cases_expected),
            ("Cases scored", run.cases_scored),
            ("Harness commit", run.harness_commit),
            ("Harness digest", run.harness_digest),
            ("Experiment", run.experiment_id or "none"),
            ("Index manifest hash", run.index_manifest_hash or "—"),
            ("Judge spend (USD)", f"{run.judge_spend_usd:.4f}"),
        ],
    )
    out.append("")
    if summary.get("withheld"):
        out.append(f"Withheld: this run is {run.status}; it reports no measure.")
        return "\n".join(out) + "\n"
    out += ["## Headline", ""]
    headline = summary.get("headline")
    if headline is not None:
        out.append(
            f"{headline['label']}: {headline['numerator']} of {headline['denominator']} ({_pct(headline['value'])}), "
            f"min–max {_pct(headline['min'])}–{_pct(headline['max'])} over {run.repeats} repeats"
        )
    else:
        out.append("No headline: the headline comes only from the sealed held-out split.")
    out += ["", "## Test-set mix"]
    out += _table(
        ["Category", "Count", "Origin", "Tests"],
        [(r["category"], r["count"], r["origin"], r["tests"] or "—") for r in summary["mix"]],
    )
    out += ["", f"## Measures ({summary['split_label']})"]
    out += _table(
        ["Measure", "Result", "Rate", "Min–max (repeats)", "Target"],
        [
            (
                m["label"],
                f"{m['numerator']} of {m['denominator']}",
                _pct(m["value"]),
                f"{_pct(m['min'])}–{_pct(m['max'])}",
                m["target"] or "—",
            )
            for m in summary["measures"]
        ],
    )
    out += ["", "## Hard gates"]
    out += _table(
        ["Gate", "State", "Failed"],
        [(g, v["state"], ", ".join(v["failed"]) or "—") for g, v in summary["gates"].items()],
    )
    out += ["", "## Failures by first failing item"]
    out += _table(["Category", "Count"], [(r["category"], r["count"]) for r in summary["failure_rows"]])
    out += ["", "## DB-copy check"]
    db = summary["db_check"]
    if db["status"] == "ran":
        out.append(
            f"Ran: {db['writes']} writes, {db['valid_writes']} valid, {db['double_bookings']} double bookings."
        )
        if db["findings"]:
            out.append("")
            out += _table(
                ["Kind", "Appointment", "Slot"],
                [(f["kind"], f["appointment_id"] or "—", f["slot_id"] or "—") for f in db["findings"]],
            )
    else:
        out.append("Not run: no working copy was given (--db-copy).")
    if "latency_ms" in summary:
        latency = summary["latency_ms"]
        out += ["", "## Latency (load)"]
        out += _table(
            ["Statistic", "Value (ms)", "Min–max (repeats)", "Target"],
            [
                (
                    n,
                    latency[n]["value"],
                    f"{latency[n]['min']}–{latency[n]['max']}",
                    latency[n]["target"] or "—",
                )
                for n in ("p50", "p95", "max")
            ],
        )
    if summary["split"] != "held-out" and summary["suite"] != "load":
        out += ["", "## Dev failures (redacted)"]
        out += _table(
            ["Case", "Summary"], [(f["case_id"], f["redacted_summary"]) for f in summary["dev_failures"]]
        )
    if summary["not_measured"]:
        out += ["", "## Not measured here"]
        out += [f"- {n['id']}: {n['reason']}" for n in summary["not_measured"]]
    return "\n".join(out) + "\n"


def write_report(
    report: EvalReportFile,
    reports_dir: Path,
    scrubber: Scrubber,
    *,
    timings: Sequence[ClientTurnTiming] = (),
) -> Path:
    """Fail closed: every output is checked for known secrets before any file is written."""
    text = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    markdown = render_markdown(report)
    timing_text = "".join(json.dumps(t.model_dump(mode="json"), sort_keys=True) + "\n" for t in timings)
    scrubber.assert_absent(text, where="report json")
    scrubber.assert_absent(markdown, where="report markdown")
    scrubber.assert_absent(timing_text, where="timings file")
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{report.run.run_id}.json"
    path.write_text(text, encoding="utf-8")
    (reports_dir / f"{report.run.run_id}.md").write_text(markdown, encoding="utf-8")
    if timings:
        (reports_dir / f"{report.run.run_id}.client_side_turn_timings.jsonl").write_text(
            timing_text, encoding="utf-8"
        )
    return path
