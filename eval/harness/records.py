"""The eval record models (stage7/data.md section 6, exactly) plus the two small helpers the plan names."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RetrievedDoc(_Record):
    file: str
    version_label: str
    score: float


class EvalRunRecord(_Record):
    run_id: str
    suite: Literal["worked-pairs", "retrieval", "e2e", "load"]
    split: Literal["dev", "held-out"] | None
    agent_version: str
    harness_commit: str
    harness_digest: str
    experiment_id: str | None
    repeats: int
    started_at: AwareDatetime
    finished_at: AwareDatetime | None
    status: Literal["started", "completed", "failed", "incomplete"]
    cases_expected: int
    cases_scored: int
    index_manifest_hash: str | None
    judge_spend_usd: float


class ItemResult(_Record):
    item: Literal["must_do", "must_say", "must_not_say", "invariant", "trajectory", "judge"]
    index: int
    passed: bool | None
    failing_quote: str | None


class EvalCaseResult(_Record):
    run_id: str
    case_id: str
    repeat: int
    thread_id: str | None
    passed_hard: bool
    items: tuple[ItemResult, ...]
    outcome: Literal["resolved", "handed_off", "degraded", "environment_error"]
    in_scope: bool | None
    topic: str | None
    top3: tuple[RetrievedDoc, ...] = ()
    below_floor: bool | None = None


class EvalReportFile(_Record):
    run: EvalRunRecord
    results: tuple[EvalCaseResult, ...]
    summary: dict[str, Any]


class ClientTurnTiming(_Record):
    run_id: str
    thread_id: str
    turn_id: str
    conversation_index: int = Field(ge=0)
    turn_index: int = Field(ge=0)
    sent_at: AwareDatetime
    first_byte_ms: int = Field(ge=0)
    total_ms: int = Field(ge=0)
    http_status: int
    outcome: Literal["reply", "notice", "error", "client_timeout"]
    notice_code: str | None


@dataclass(frozen=True)
class RunStamp:
    """The identity every report of one run shares (not a contract model)."""

    run_id: str
    agent_version: str
    harness_commit: str
    harness_digest: str
    index_manifest_hash: str | None
    started_at: datetime


def new_record(
    stamp: RunStamp,
    *,
    suite: Literal["worked-pairs", "retrieval", "e2e", "load"],
    split: Literal["dev", "held-out"] | None,
    repeats: int,
    experiment_id: str | None,
    status: Literal["started", "completed", "failed", "incomplete"],
    finished_at: datetime,
    cases_expected: int = 0,
    cases_scored: int = 0,
    judge_spend_usd: float = 0.0,
) -> EvalRunRecord:
    return EvalRunRecord(
        run_id=stamp.run_id,
        suite=suite,
        split=split,
        agent_version=stamp.agent_version,
        harness_commit=stamp.harness_commit,
        harness_digest=stamp.harness_digest,
        experiment_id=experiment_id,
        repeats=repeats,
        started_at=stamp.started_at,
        finished_at=finished_at,
        status=status,
        cases_expected=cases_expected,
        cases_scored=cases_scored,
        index_manifest_hash=stamp.index_manifest_hash,
        judge_spend_usd=judge_spend_usd,
    )
