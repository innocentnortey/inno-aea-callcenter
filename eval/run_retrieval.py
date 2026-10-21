"""``python -m eval.run_retrieval``: the E-2 retrieval run. The one eval module that imports app code (AC-10, AC-17)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import NoReturn

from eval.harness.cases import CaseFileError, load_retrieval_queries
from eval.harness.deps import DEFAULT_CASES_DIR, DEFAULT_REPORTS_DIR, HarnessDeps, UsageError
from eval.harness.freeze import (
    FreezeStamp,
    NotFrozen,
    TamperDetected,
    check_frozen,
    harness_commit,
    harness_digest,
)
from eval.harness.records import RunStamp, new_record
from eval.harness.report import build_failed_report, gates_failed, write_report
from eval.harness.retrieval import SearchesPassages, run_retrieval_suite
from eval.harness.runlog import RunLog
from eval.harness.scrub import LeakDetected, Scrubber
from meridian.adapters.retrieval_fastembed import FastembedIndex  # type: ignore[import-untyped,unused-ignore]
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K  # type: ignore[import-untyped,unused-ignore]

_SAFE_PATH = re.compile(r"[\w.:+#/@-]{1,200}")


def default_index(index_dir: Path) -> SearchesPassages:
    index: SearchesPassages = FastembedIndex(index_dir)  # structural fit (AC-10)
    return index


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


def main(
    argv: Sequence[str] | None = None,
    *,
    deps: HarnessDeps | None = None,
    index_factory: Callable[[Path], SearchesPassages] | None = None,
) -> int:
    deps = deps or HarnessDeps()
    scrubber = Scrubber()
    log = RunLog(deps.log_stream or sys.stderr, scrubber)
    env = deps.env if deps.env is not None else os.environ
    for name in ("MERIDIAN_EVAL_KEY", "MERIDIAN_DEMO_PASSWORD"):
        scrubber.add(env.get(name))
    parser = _Parser(prog="python -m eval.run_retrieval", add_help=False)
    parser.add_argument("--index-dir", type=Path, required=True)
    parser.add_argument("--queries-dir", type=Path, default=DEFAULT_CASES_DIR / "retrieval")
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--k", type=int, default=SEARCH_K)
    parser.add_argument("--min-score", type=float, default=MIN_SCORE)
    try:
        args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))
        return _run(args, deps, env, log, scrubber, index_factory)
    except UsageError as error:
        log.say(f"refused: {error}")
        log.emit("refused", reason=error.reason)
        return 2
    except LeakDetected:
        log.emit("leak_blocked", suite="retrieval")
        return 5


def _run(
    args: argparse.Namespace,
    deps: HarnessDeps,
    env: Mapping[str, str],
    log: RunLog,
    scrubber: Scrubber,
    index_factory: Callable[[Path], SearchesPassages] | None,
) -> int:
    agent_version = env.get("MERIDIAN_AGENT_VERSION", "dev")
    started = deps.wall_clock()
    base = RunStamp(
        run_id=str(uuid.uuid4()),
        agent_version=agent_version,
        harness_commit=harness_commit(),
        harness_digest=harness_digest(deps.harness_root),
        index_manifest_hash=None,
        started_at=started,
    )
    try:
        frozen: FreezeStamp = check_frozen(deps.freeze_file, root=deps.harness_root)
    except (NotFrozen, TamperDetected) as exc:
        reason = "tamper" if isinstance(exc, TamperDetected) else "not_frozen"
        log.say(f"refused: {exc}")
        log.emit("refused", run_id=base.run_id, reason=reason)
        record = new_record(
            base,
            suite="retrieval",
            split=None,
            repeats=1,
            experiment_id=None,
            status="failed",
            finished_at=deps.wall_clock(),
        )
        write_report(build_failed_report(record, reason=reason), args.reports_dir, scrubber)
        return 3
    record_path = args.index_dir / "index_record.json"
    try:
        manifest_hash = str(json.loads(record_path.read_text(encoding="utf-8"))["manifest_hash"])
    except (OSError, ValueError, KeyError) as exc:
        raise UsageError(
            "index record is missing or has no manifest hash", reason="index_record_missing"
        ) from exc
    try:
        queries = load_retrieval_queries(args.queries_dir)
    except CaseFileError as exc:
        raise UsageError(str(exc), reason="case_files") from exc
    index = (index_factory or default_index)(args.index_dir)
    stamp = RunStamp(
        run_id=base.run_id,
        agent_version=agent_version,
        harness_commit=frozen.harness_commit,
        harness_digest=frozen.harness_digest,
        index_manifest_hash=manifest_hash,
        started_at=started,
    )
    report = run_retrieval_suite(
        index, queries, k=args.k, min_score=args.min_score, stamp=stamp, now=deps.wall_clock
    )
    for result in report.results:
        log.emit("retrieval_query_scored", run_id=stamp.run_id, case_id=result.case_id, status="scored")
    path = write_report(report, args.reports_dir, scrubber)
    text = str(path)
    log.emit(
        "run_finished",
        run_id=stamp.run_id,
        suite="retrieval",
        status=report.run.status,
        report_path=text if _SAFE_PATH.fullmatch(text) else path.name,
    )
    if report.run.status != "completed":
        return 1
    return 4 if gates_failed(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
