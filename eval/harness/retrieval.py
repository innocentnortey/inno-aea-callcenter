"""The retrieval suite (E-2, WF-8): top 3 with version labels, hit at 3 with no floor, excluded files apart (AC-10, AC-18)."""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from eval.cases.models import RetrievalQuery
from eval.harness.freeze import harness_commit, harness_digest
from eval.harness.invariants import is_excluded_file
from eval.harness.records import (
    EvalCaseResult,
    EvalReportFile,
    ItemResult,
    RetrievedDoc,
    RunStamp,
    new_record,
)
from eval.harness.report import JUDGE_OFF, base_summary, measure_dict


class PassageLike(Protocol):
    @property
    def file(self) -> str: ...
    @property
    def section(self) -> str: ...
    @property
    def version_label(self) -> str: ...
    @property
    def score(self) -> float: ...


class SearchResultLike(Protocol):
    @property
    def passages(self) -> Sequence[PassageLike]: ...
    @property
    def below_floor(self) -> bool: ...


class SearchesPassages(Protocol):
    def search(self, query: str, *, k: int, min_score: float) -> SearchResultLike: ...


def run_retrieval_suite(
    index: SearchesPassages,
    queries: Sequence[RetrievalQuery],
    *,
    k: int,
    min_score: float,
    stamp: RunStamp | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> EvalReportFile:
    stamp = stamp or RunStamp(
        run_id=str(uuid.uuid4()),
        agent_version=os.environ.get("MERIDIAN_AGENT_VERSION", "dev"),
        harness_commit=harness_commit(),
        harness_digest=harness_digest(),
        index_manifest_hash=None,
        started_at=now(),
    )
    ordered = sorted(queries, key=lambda q: q.query_id)
    results: list[EvalCaseResult] = []
    unscored: list[str] = []  # the run becomes incomplete: nothing is reported from it
    by_id: dict[str, RetrievalQuery] = {}
    flags: dict[str, tuple[bool | None, bool, bool]] = {}  # query id -> (hit, excluded, below_floor)
    for query in ordered:
        try:
            raw = index.search(query.query, k=k, min_score=float("-inf"))
            floored = index.search(query.query, k=k, min_score=min_score)
        except Exception:  # any index failure leaves the query unscored
            unscored.append(query.query_id)
            continue
        top3 = tuple(
            RetrievedDoc(file=p.file, version_label=p.version_label, score=round(p.score, 4))
            for p in raw.passages[:k]
        )
        hit = query.expected_file is not None and any(d.file == query.expected_file for d in top3)
        excluded = any(is_excluded_file(d.file) for d in top3)
        passed_goal = hit if query.expected_file is not None else floored.below_floor
        results.append(
            EvalCaseResult(
                run_id=stamp.run_id,
                case_id=query.query_id,
                repeat=1,
                thread_id=None,
                passed_hard=not excluded,
                items=(
                    ItemResult(item="must_do", index=0, passed=passed_goal, failing_quote=None),
                    ItemResult(
                        item="invariant",
                        index=0,
                        passed=not excluded,
                        failing_quote="excluded_file_in_top3" if excluded else None,
                    ),
                ),
                outcome="resolved",
                in_scope=None,
                topic=None,
                top3=top3,
                below_floor=floored.below_floor,
            )
        )
        by_id[query.query_id] = query
        flags[query.query_id] = (hit, excluded, floored.below_floor)
    status: Literal["completed", "incomplete"] = "completed" if len(results) == len(ordered) else "incomplete"
    record = new_record(
        stamp,
        suite="retrieval",
        split=None,
        repeats=1,
        experiment_id=None,
        status=status,
        finished_at=now(),
        cases_expected=len(ordered),
        cases_scored=len(results),
    )
    withheld = base_summary(
        record,
        mix=None,
        size=len(results),
        measures=[],
        dev_failures=[],
        headline=None,
        gates={},
        failure_rows=[],
        topic_readiness={},
        db=None,
        unscored=[],
        judge_summary=JUDGE_OFF,
        cost_per_conversation_usd=None,
        not_measured=[],
        empty_measures=[],
        withheld=record.status,
    )
    if status != "completed":
        return EvalReportFile(run=record, results=tuple(results), summary=withheld)

    def pair(pop: Callable[[RetrievalQuery], bool], num: Callable[[str], bool]) -> dict[int, tuple[int, int]]:
        chosen = [q for q in ordered if pop(q)]
        return {1: (sum(1 for q in chosen if num(q.query_id)), len(chosen))}

    candidates = [
        measure_dict(
            "M-6",
            "Retrieval hit @3 (current document)",
            pair(lambda q: q.expected_file is not None, lambda i: bool(flags[i][0])),
            "≥ 90%",
        ),
        measure_dict(
            "M-7",
            "Queries with an excluded file in the top 3",
            pair(lambda q: True, lambda i: flags[i][1]),
            "0",
        ),
        measure_dict(
            "E-2:floor",
            "Off-corpus queries below the relevance floor",
            pair(lambda q: q.expect_below_floor, lambda i: flags[i][2]),
            None,
        ),
    ]
    failed = [q.query_id for q in ordered if flags[q.query_id][1]]
    gates: dict[str, Any] = {"excluded_file": {"state": "fail" if failed else "pass", "failed": failed}}
    misses = [
        {"case_id": q.query_id, "redacted_summary": "expected current document not in top 3"}
        for q in ordered
        if q.expected_file is not None and not flags[q.query_id][0]
    ]
    summary = base_summary(
        record,
        mix=None,
        size=len(ordered),
        measures=[m for m in candidates if m is not None],
        dev_failures=misses,
        headline=None,
        gates=gates,
        failure_rows=[],
        topic_readiness={},
        db=None,
        unscored=[],
        judge_summary=JUDGE_OFF,
        cost_per_conversation_usd=None,
        not_measured=[],
        empty_measures=[m for m, c in zip(("M-6", "M-7", "E-2:floor"), candidates, strict=True) if c is None],
        withheld=None,
    )
    return EvalReportFile(run=record, results=tuple(results), summary=summary)
