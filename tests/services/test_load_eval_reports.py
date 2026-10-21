"""AEA-32 load_eval_reports: idempotent by run_id, invalid files skipped with one event."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from meridian.services.health import load_eval_reports
from tests.fixtures.sqlite import temp_sqlite
from tests.services.ops_support import BASE, FakeWall, health_rows

SUMMARY = {"measures": {"passed": {"n": 2, "of": 2}}, "mix": {"billing": 1}}


def _report(run_id: str) -> dict[str, Any]:
    return {
        "run": {
            "run_id": run_id,
            "suite": "worked-pairs",
            "split": None,
            "agent_version": "test-ops",
            "harness_commit": "abc123def456",
            "harness_digest": "d1g3st",
            "experiment_id": None,
            "repeats": 1,
            "started_at": "2026-10-21T18:00:00+00:00",
            "finished_at": "2026-10-21T18:05:00+00:00",
            "status": "completed",
            "cases_expected": 2,
            "cases_scored": 2,
            "index_manifest_hash": None,
            "judge_spend_usd": 0.0,
        },
        "results": [
            {
                "run_id": run_id,
                "case_id": case,
                "repeat": 0,
                "thread_id": None,
                "passed_hard": True,
                "items": [{"item": "must_do", "index": 0, "passed": True, "failing_quote": None}],
                "outcome": "resolved",
                "in_scope": True,
                "topic": "billing",
            }
            for case in ("WP-1", "WP-3")
        ],
        "summary": SUMMARY,
    }


def write_valid_reports(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for run_id in ("run-a", "run-b"):
        path = directory / f"{run_id}.json"
        path.write_text(json.dumps(_report(run_id), separators=(",", ":")), encoding="utf-8")
        paths.append(path)
    return paths


def test_loads_idempotently(tmp_path: Path) -> None:
    write_valid_reports(tmp_path)
    with temp_sqlite() as store:
        wall = FakeWall(BASE)
        assert load_eval_reports(tmp_path, store.uow, wall_clock=wall) == 2
        assert load_eval_reports(tmp_path, store.uow, wall_clock=wall) == 0
        with store.uow() as tx:
            stored = tx.ops.eval.latest_completed("worked-pairs", None)
        assert stored is not None
        assert stored.summary_json == json.dumps(SUMMARY, ensure_ascii=False, separators=(",", ":"))
        assert json.loads(stored.summary_json) == SUMMARY


def test_invalid_file_skipped(tmp_path: Path) -> None:
    paths = write_valid_reports(tmp_path)
    bad = tmp_path / "run-bad.json"
    bad.write_bytes(paths[0].read_bytes()[:40])
    with temp_sqlite() as store:
        assert (
            load_eval_reports(tmp_path, store.uow, wall_clock=FakeWall(BASE), agent_version="test-ops") == 2
        )
        with store.uow() as tx:
            n = tx.connection.execute("SELECT COUNT(*) FROM eval_runs WHERE run_id = 'run-bad'").fetchone()[0]
        assert n == 0
        assert health_rows(store) == [("check_failed", None, "eval_report_invalid")]


def test_missing_dir_returns_zero(tmp_path: Path) -> None:
    with temp_sqlite() as store:
        assert load_eval_reports(tmp_path / "absent", store.uow) == 0
        with store.uow() as tx:
            assert tx.connection.execute("SELECT COUNT(*) FROM eval_runs").fetchone()[0] == 0
        assert health_rows(store) == []
