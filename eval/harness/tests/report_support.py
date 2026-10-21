"""Hand-built case scores and run records for the report tests (AEA-24 AC-20): no HTTP, no harness run."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

STARTED = datetime(2026, 10, 21, 18, 0, tzinfo=UTC)
JUDGE_OFF = {
    "enabled": False,
    "model": None,
    "calibrated": False,
    "calls": 0,
    "advisory_pass": 0,
    "advisory_fail": 0,
    "status": "off",
}


def run_record(
    *, split: str, status: str = "completed", repeats: int = 1, expected: int = 0, scored: int = 0
) -> Any:
    from eval.harness.records import EvalRunRecord

    fields: dict[str, Any] = {
        "run_id": str(uuid.uuid4()),
        "suite": "e2e",
        "split": split,
        "agent_version": "v-test",
        "harness_commit": "abc123",
        "harness_digest": "d" * 64,
        "experiment_id": None,
        "repeats": repeats,
        "started_at": STARTED,
        "finished_at": STARTED,
        "status": status,
        "cases_expected": expected,
        "cases_scored": scored,
        "index_manifest_hash": None,
        "judge_spend_usd": 0.0,
    }
    return EvalRunRecord(**fields)


def make_score(
    case_id: str,
    repeat: int,
    *,
    split: str,
    in_scope: bool = True,
    topic: str | None = "booking",
    outcome: str = "resolved",
    correct: bool = True,
    passed_hard: bool = True,
    failed_gates: tuple[str, ...] = (),
    first_failure: str | None = None,
    expects_safety: bool = False,
    danger: bool = False,
    no_danger: bool = False,
    person: bool = False,
    safety_seen: bool = False,
    cited_any: bool = False,
    cited_excluded: bool = False,
    handoffs: tuple[int, int] = (0, 0),
    wrong: bool = False,
) -> Any:
    from eval.harness.records import EvalCaseResult
    from eval.harness.scoring import CaseScore

    result_fields: dict[str, Any] = {
        "run_id": "r",
        "case_id": case_id,
        "repeat": repeat,
        "thread_id": None,
        "passed_hard": passed_hard,
        "items": (),
        "outcome": outcome,
        "in_scope": in_scope,
        "topic": topic if in_scope else None,
    }
    score_fields: dict[str, Any] = {
        "result": EvalCaseResult(**result_fields),
        "split": split,
        "failed_gates": failed_gates,
        "first_failure": first_failure,
        "expects_safety": expects_safety,
        "danger_case": danger,
        "no_danger_case": no_danger,
        "person_request_case": person,
        "safety_block_seen": safety_seen,
        "cited_any_source": cited_any,
        "cited_excluded": cited_excluded,
        "handoffs_checked": handoffs[0],
        "handoffs_ok": handoffs[1],
        "wrong_answer": wrong,
        "correct": correct,
        "judge_calls": 0,
        "judge_advisory_pass": 0,
        "judge_advisory_fail": 0,
    }
    return CaseScore(**score_fields)


def _repeat_scores(split: str, repeat: int) -> list[Any]:
    def s(case_id: str, **kw: Any) -> Any:
        return make_score(case_id, repeat, split=split, **kw)

    return [
        s(
            "c01",
            correct=repeat == 1,
            first_failure=None if repeat == 1 else "answer_omission",
            cited_any=True,
        ),
        s("c02"),
        s(
            "c03",
            correct=False,
            passed_hard=False,
            failed_gates=("fee_bearing_write", "excluded_file"),
            first_failure="rule_violation",
            cited_any=True,
            cited_excluded=True,
            wrong=True,
        ),
        s("c04", topic="billing"),
        s("c05", topic="billing", correct=False, first_failure="invented_fact", wrong=True),
        s("c06", topic="membership", outcome="handed_off", handoffs=(1, 1)),
        s("c07", in_scope=False, outcome="handed_off", person=True, handoffs=(1, 1)),
        s("c08", in_scope=False, correct=False, first_failure="under_escalation"),
        s(
            "c09",
            in_scope=False,
            outcome="handed_off",
            danger=True,
            expects_safety=True,
            safety_seen=True,
            handoffs=(2, 1),
        ),
        s(
            "c10",
            in_scope=False,
            correct=False,
            passed_hard=False,
            failed_gates=("safety_first",),
            first_failure="safety_miss",
            danger=True,
            expects_safety=True,
        ),
        s("c11", in_scope=False, outcome="handed_off", no_danger=True, safety_seen=True),
        s("c12", in_scope=False, outcome="handed_off", no_danger=True),
        s("c13", topic="warranty"),
    ]


def hand_counted_scores(split: str) -> list[Any]:
    """13 cases, 2 repeats. Only c01 differs between repeats (correct in repeat 1, not in repeat 2)."""
    return _repeat_scores(split, 1) + _repeat_scores(split, 2)
