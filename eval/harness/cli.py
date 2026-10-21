"""``python -m eval.harness run|freeze``: parse arguments, refuse bad combinations, dispatch, map outcomes to exit codes.

Exit codes: 0 completed, gates pass or not run; 1 incomplete; 2 usage or configuration error (no request, no report);
3 refused or failed (not frozen, tamper, held-out hash, preflight, login); 4 completed with a failed gate;
5 a leak was blocked while writing an output.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from eval.harness.deps import (
    DEFAULT_CALIBRATION,
    DEFAULT_CASES_DIR,
    DEFAULT_REPORTS_DIR,
    FREEZE_FILE,
    HarnessDeps,
    RunConfig,
    RunOutcome,
    UsageError,
)
from eval.harness.freeze import write_freeze
from eval.harness.load import run_load_suite
from eval.harness.runlog import RunLog
from eval.harness.runner import run_scored_suite
from eval.harness.scrub import LeakDetected, Scrubber

__all__ = ["RunConfig", "RunOutcome", "UsageError", "main", "parse_run_args"]

_SAFE_PATH = re.compile(r"[\w.:+#/@-]{1,200}")


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


def _run_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="python -m eval.harness run", add_help=False)
    parser.add_argument("--suite", choices=["worked-pairs", "e2e", "load"], required=True)
    parser.add_argument("--split", choices=["dev", "held-out"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--base-url")
    parser.add_argument("--heldout-key-dir", type=Path)
    parser.add_argument("--experiment")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--db-copy", type=Path)
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--conversations", type=int, default=20)
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    return parser


def parse_run_args(argv: Sequence[str]) -> RunConfig:
    """Parse the arguments after ``run``. Raises ``UsageError`` (never ``SystemExit``) on a bad combination."""
    args = _run_parser().parse_args(list(argv))
    if args.experiment is not None and args.split == "held-out":
        raise UsageError("--experiment is not allowed with --split held-out", reason="experiment_on_heldout")
    if args.experiment is not None and not re.fullmatch(r"XP-[0-9]+", args.experiment):
        raise UsageError("--experiment must look like XP-1", reason="experiment_format")
    if args.suite in {"e2e", "load"} and args.split is None:
        raise UsageError(f"--split is required for --suite {args.suite}", reason="split")
    if args.suite == "load" and args.split != "dev":
        raise UsageError("--suite load runs only on --split dev", reason="split")
    if args.suite == "worked-pairs" and args.split not in {None, "dev"}:
        raise UsageError("--suite worked-pairs runs only on --split dev", reason="split")
    if args.repeats < 1:
        raise UsageError("--repeats must be at least 1", reason="repeats")
    if args.conversations < 1:
        raise UsageError("--conversations must be at least 1", reason="conversations")
    if args.split == "held-out" and args.heldout_key_dir is None:
        raise UsageError("--heldout-key-dir is required with --split held-out", reason="heldout_key_dir")
    if args.base_url is None and not args.dry_run:
        raise UsageError("--base-url is required unless --dry-run", reason="base_url")
    return RunConfig(
        suite=args.suite,
        split=None if args.suite == "worked-pairs" else args.split,
        repeats=args.repeats,
        base_url=args.base_url,
        heldout_key_dir=args.heldout_key_dir,
        experiment_id=args.experiment,
        dry_run=args.dry_run,
        judge=args.judge,
        db_copy=args.db_copy,
        cases_dir=args.cases_dir,
        reports_dir=args.reports_dir,
        conversations=args.conversations,
        calibration=args.calibration,
    )


def _refuse_usage(log: RunLog, error: UsageError) -> int:
    log.say(f"refused: {error}")
    log.emit("refused", reason=error.reason)
    return 2


def _freeze(argv: Sequence[str], deps: HarnessDeps, log: RunLog) -> int:
    parser = _Parser(prog="python -m eval.harness freeze", add_help=False)
    parser.add_argument("--freeze-file", type=Path, default=FREEZE_FILE)
    try:
        args = parser.parse_args(list(argv))
    except UsageError as error:
        return _refuse_usage(log, error)
    stamp = write_freeze(args.freeze_file, root=deps.harness_root)
    log.emit("frozen", harness_commit=stamp.harness_commit, harness_digest=stamp.harness_digest)
    return 0


def main(argv: Sequence[str] | None = None, *, deps: HarnessDeps | None = None) -> int:
    deps = deps or HarnessDeps()
    args = list(sys.argv[1:] if argv is None else argv)
    log = RunLog(deps.log_stream or sys.stderr, Scrubber())
    if not args or args[0] not in {"run", "freeze"}:
        return _refuse_usage(
            log, UsageError("usage: python -m eval.harness run|freeze ...", reason="command")
        )
    if args[0] == "freeze":
        return _freeze(args[1:], deps, log)
    try:
        cfg = parse_run_args(args[1:])
    except UsageError as error:
        return _refuse_usage(log, error)
    scrubber = Scrubber()
    log = RunLog(deps.log_stream or sys.stderr, scrubber)
    try:
        if cfg.suite == "load":
            outcome = asyncio.run(
                run_load_suite(cfg, deps, log=log, scrubber=scrubber, transport=deps.transport)
            )
        else:
            outcome = asyncio.run(
                run_scored_suite(cfg, deps, log=log, scrubber=scrubber, transport=deps.transport)
            )
    except UsageError as error:
        return _refuse_usage(log, error)
    except LeakDetected:
        log.emit("leak_blocked", suite=cfg.suite)
        return 5
    fields: dict[str, str | int | float | bool | None] = {"suite": cfg.suite, "exit_code": outcome.exit_code}
    if outcome.report is not None:
        fields["run_id"] = outcome.report.run.run_id
        fields["status"] = outcome.report.run.status
    if outcome.report_path is not None:
        text = str(outcome.report_path)
        fields["report_path"] = text if _SAFE_PATH.fullmatch(text) else outcome.report_path.name
    log.emit("run_finished", **fields)
    return outcome.exit_code
