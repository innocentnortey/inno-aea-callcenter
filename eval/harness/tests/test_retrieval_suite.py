"""AEA-24 AC-10 and AC-18: the retrieval suite (E-2, WF-8) over a SearchesPassages double."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from eval.harness.tests.fixture_cases import (
    env_for,
    flip_one_byte,
    harness_copy,
    run_secrets,
    write_retrieval_queries,
)
from eval.harness.tests.retrieval_double import (
    FLOOR,
    INDEX_MANIFEST,
    QUERY_TEXTS,
    TABLE,
    ScriptedIndex,
    queries,
    stamp,
    write_index_dir,
)
from eval.harness.tests.support import validate_eval_run, validate_report_file


def _suite(index: ScriptedIndex, *ids: str) -> dict[str, Any]:
    from eval.harness.retrieval import run_retrieval_suite

    report = run_retrieval_suite(index, queries(*ids), k=3, min_score=FLOOR, stamp=stamp())
    dumped: dict[str, Any] = report.model_dump(mode="json")
    return dumped


def test_hit_at_3_and_excluded_counted() -> None:
    """invariant: top 3 with version labels, hit @3 with no floor, below_floor at the floor, excluded hits apart."""
    index = ScriptedIndex(TABLE)
    report = _suite(index, "R-1", "R-2", "R-3", "R-4", "R-5")
    validate_report_file(report)
    run = report["run"]
    assert (run["suite"], run["split"], run["status"]) == ("retrieval", None, "completed")
    assert (run["cases_expected"], run["cases_scored"]) == (5, 5)
    assert run["index_manifest_hash"] == INDEX_MANIFEST
    results = {r["case_id"]: r for r in report["results"]}
    assert list(results) == ["R-1", "R-2", "R-3", "R-4", "R-5"]
    assert results["R-1"]["top3"][0] == {
        "file": "membership/comfort_club.md",
        "version_label": "Rev 2026-01",
        "score": 0.91,
    }
    assert [d["version_label"] for d in results["R-3"]["top3"]] == ["2023", "Rev 2026-01", "Rev 2026-01"]
    assert [r["below_floor"] for r in results.values()] == [False, False, False, True, False]
    assert [r["passed_hard"] for r in results.values()] == [True, True, False, True, True]
    searches = {(q, floor) for q, _, floor in index.calls}
    assert (QUERY_TEXTS["R-1"], float("-inf")) in searches
    assert (QUERY_TEXTS["R-1"], FLOOR) in searches

    summary = report["summary"]
    validate_eval_run(summary)
    by_id = {m["id"]: m for m in summary["measures"]}
    assert (by_id["M-6"]["numerator"], by_id["M-6"]["denominator"]) == (3, 4)
    assert by_id["M-6"]["value"] == 0.75
    assert by_id["M-6"]["target"] == "≥ 90%"
    assert (by_id["M-7"]["numerator"], by_id["M-7"]["denominator"]) == (1, 5)
    assert (by_id["E-2:floor"]["numerator"], by_id["E-2:floor"]["denominator"]) == (1, 1)


def test_excluded_file_fails_hard_gate() -> None:
    """failure: an excluded (R-10) file in the top 3 is a hard failure and the gate names the query."""
    report = _suite(ScriptedIndex(TABLE), "R-3")
    result = report["results"][0]
    assert result["passed_hard"] is False
    invariant = next(i for i in result["items"] if i["item"] == "invariant")
    assert invariant["passed"] is False
    assert invariant["failing_quote"] == "excluded_file_in_top3"
    assert report["summary"]["gates"]["excluded_file"] == {"state": "fail", "failed": ["R-3"]}


def test_incomplete_retrieval_run_not_reported() -> None:
    """failure: a query the index could not answer makes the run incomplete and withholds hit @3."""
    index = ScriptedIndex(TABLE, raises_on={QUERY_TEXTS["R-2"]})
    report = _suite(index, "R-1", "R-2", "R-5")
    assert report["run"]["status"] == "incomplete"
    assert (report["run"]["cases_expected"], report["run"]["cases_scored"]) == (3, 2)
    assert report["summary"]["measures"] == []
    assert "M-6" not in {m["id"] for m in report["summary"]["measures"]}
    assert report["summary"]["withheld"] == "incomplete"


def test_tamper_refuses_retrieval(tmp_path: Path) -> None:
    """regression: a one-byte change to the harness source refuses the retrieval run: failed, no results."""
    from eval.harness.deps import HarnessDeps
    from eval.harness.freeze import write_freeze
    from eval.run_retrieval import main

    run = run_secrets()
    copy = harness_copy(tmp_path)
    freeze_file = tmp_path / "freeze.json"
    write_freeze(freeze_file, root=copy)
    flip_one_byte(copy)
    queries_dir = write_retrieval_queries(tmp_path / "queries", queries("R-1", "R-5"))
    reports = tmp_path / "reports"
    deps = HarnessDeps(
        env={**env_for(run), "MERIDIAN_AGENT_VERSION": "v-test"},
        harness_root=copy,
        freeze_file=freeze_file,
        log_stream=io.StringIO(),
    )
    argv = [
        "--index-dir",
        str(write_index_dir(tmp_path)),
        "--queries-dir",
        str(queries_dir),
        "--reports-dir",
        str(reports),
    ]
    code = main(argv, deps=deps, index_factory=lambda _path: ScriptedIndex(TABLE))
    assert code == 3
    files = list(reports.glob("*.json"))
    assert len(files) == 1
    report = json.loads(files[0].read_text(encoding="utf-8"))
    assert report["run"]["status"] == "failed"
    assert report["results"] == []
