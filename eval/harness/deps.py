"""Paths and the ``HarnessDeps`` injection bundle (a seam AEA-51 relies on: keep the field names)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, TextIO

import httpx

from eval.harness.judge import Judge
from eval.harness.records import EvalReportFile

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
HARNESS_ROOT: Final = Path(__file__).resolve().parent
ISSUED_DB: Final = REPO_ROOT / "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
DEFAULT_CASES_DIR: Final = REPO_ROOT / "eval/cases"
DEFAULT_REPORTS_DIR: Final = REPO_ROOT / "eval/reports"
DEFAULT_LEDGER_DIR: Final = REPO_ROOT / "var/eval-ledger"  # var/ is git-ignored
DEFAULT_CALIBRATION: Final = REPO_ROOT / "eval/judge-calibration.json"
FREEZE_FILE: Final = HARNESS_ROOT / "freeze.json"


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class HarnessDeps:
    """Every injection a test (or AEA-51) needs; the defaults are production."""

    transport: httpx.AsyncBaseTransport | None = None
    judge: Judge | None = None
    env: Mapping[str, str] | None = None
    harness_root: Path = HARNESS_ROOT
    freeze_file: Path = FREEZE_FILE
    log_stream: TextIO | None = None
    wall_clock: Callable[[], datetime] = _utc_now
    ledger_dir: Path = DEFAULT_LEDGER_DIR
    issued_db: Path = ISSUED_DB


@dataclass(frozen=True)
class RunConfig:
    suite: Literal["worked-pairs", "e2e", "load"]
    split: Literal["dev", "held-out"] | None
    repeats: int
    base_url: str | None
    heldout_key_dir: Path | None
    experiment_id: str | None
    dry_run: bool
    judge: bool
    db_copy: Path | None
    cases_dir: Path
    reports_dir: Path
    conversations: int
    calibration: Path


class UsageError(Exception):
    """A bad flag combination or configuration. The message names the flag or the split, never a secret."""

    def __init__(self, message: str, reason: str = "usage") -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class RunOutcome:
    exit_code: int
    report: EvalReportFile | None
    report_path: Path | None
