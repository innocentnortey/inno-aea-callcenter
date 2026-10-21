"""AEA-24 CAP-7 (WF-8, WF-9, WF-10): the eval workflows leave their records, with nothing secret in them."""

from __future__ import annotations

import io
from pathlib import Path

from eval.harness.tests.fixture_cases import (
    coded_case,
    coded_scripted,
    env_for,
    run_secrets,
    sentinel,
    simple_case,
    simple_key,
    write_cases,
    write_retrieval_queries,
)
from eval.harness.tests.netblock import block_network
from eval.harness.tests.retrieval_double import (
    INDEX_MANIFEST,
    QUERY_TEXTS,
    TABLE,
    ScriptedIndex,
    queries,
    write_index_dir,
)
from eval.harness.tests.support import (
    HEX64,
    UUID4,
    FakeJudge,
    Outcome,
    assert_absent,
    assert_all_requests_have_eval_headers,
    assert_log_allow_listed,
    assert_targets_only_in_target_column,
    base_argv,
    make_stub,
    run_cli,
    validate_eval_run,
)
from meridian.services.health import load_eval_reports
from tests.fixtures.sqlite import temp_sqlite

__all__ = ["block_network"]
AGENT_VERSION = "abc123def456+0a1b2c3d"


def _assert_json_log(out: Outcome) -> None:
    assert out.log_text.strip()
    assert all(line.startswith("{") for line in out.log_text.splitlines() if line.strip())
    assert_log_allow_listed(out.log_lines())


def test_wf9_dev_case_records(tmp_path: Path, block_network: list[object]) -> None:
    """capture: one fixture dev case over 3 repeats leaves the run record, three results with their own thread ids,
    headers on every request, an allow-listed log and none of the secrets or the planted sentinel."""
    run = run_secrets()
    phrase = sentinel()
    stub = make_stub(run, coded_scripted, agent_version=AGENT_VERSION)
    cases = write_cases(
        tmp_path / "cases", [(coded_case("D-1", f"Hello, {phrase}, I need help."), simple_key("D-1"))]
    )
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports", repeats=3), stub=stub, run=run)
    assert out.code == 0
    report = out.report()
    record = report["run"]
    assert UUID4.match(record["run_id"])
    assert record["agent_version"] == AGENT_VERSION
    assert record["harness_commit"]
    assert HEX64.match(record["harness_digest"])
    assert (record["suite"], record["split"], record["status"], record["repeats"]) == (
        "e2e",
        "dev",
        "completed",
        3,
    )
    assert record["experiment_id"] is None
    assert record["cases_scored"] == record["cases_expected"] == 3
    results = report["results"]
    assert len(results) == 3
    assert {r["run_id"] for r in results} == {record["run_id"]}
    assert all(r["in_scope"] is True for r in results)
    thread_ids = [r["thread_id"] for r in results]
    assert all(thread_ids) and len(set(thread_ids)) == 3
    assert_all_requests_have_eval_headers(stub, run, record["run_id"], "eval")
    _assert_json_log(out)
    assert len(stub.issued_codes) == 3
    assert_absent(
        out.all_text(),
        [run.eval_key, run.password, run.username, phrase, *stub.issued_codes],
        where="the dev run outputs",
    )
    assert block_network == []


def test_wf10_load_run_records(tmp_path: Path, block_network: list[object]) -> None:
    """capture: a two-conversation load run over 3 repeats signs in once, tags every request load, writes one timing
    line per call and never calls the judge."""
    run = run_secrets()
    phrase = sentinel()
    judge = FakeJudge()
    stub = make_stub(run, agent_version=AGENT_VERSION)
    cases = write_cases(
        tmp_path / "cases",
        [
            (simple_case("L-1", f"Hello, {phrase}, one."), simple_key("L-1")),
            (simple_case("L-2", f"Hello, {phrase}, two."), simple_key("L-2")),
        ],
    )
    argv = base_argv(cases, tmp_path / "reports", suite="load", repeats=3, extra=["--conversations", "2"])
    out = run_cli(tmp_path, argv, stub=stub, run=run, judge=judge)
    assert out.code == 0
    report = out.report()
    record = report["run"]
    assert UUID4.match(record["run_id"])
    assert (record["suite"], record["split"], record["status"], record["repeats"]) == (
        "load",
        "dev",
        "completed",
        3,
    )
    assert record["agent_version"] == AGENT_VERSION
    assert record["cases_scored"] == record["cases_expected"] == 6
    assert stub.paths()[0] == ("POST", "/api/login")
    assert stub.paths().count(("POST", "/api/login")) == 1
    assert_all_requests_have_eval_headers(stub, run, record["run_id"], "load")
    for repeat in (1, 2, 3):
        threads = [r["thread_id"] for r in report["results"] if r["repeat"] == repeat]
        assert len(threads) == 2 and len(set(threads)) == 2
    timings = out.timings()
    assert len(timings) == len(stub.turn_requests()) == 6
    assert {t["run_id"] for t in timings} == {record["run_id"]}
    latency = report["summary"]["latency_ms"]
    for stat in ("p50", "p95", "max"):
        assert latency[stat]["min"] is not None and latency[stat]["max"] is not None
    _assert_json_log(out)
    assert_absent(
        out.all_text(), [run.eval_key, run.password, run.username, phrase], where="the load run outputs"
    )
    assert judge.calls == []
    assert block_network == []


def test_wf8_retrieval_run_records(tmp_path: Path, block_network: list[object]) -> None:
    """capture: the retrieval entry, with its index replaced by a double, records the run, its per-query results and
    a summary CON-20 can read, with no network and no secret."""
    from eval.harness.deps import HarnessDeps
    from eval.harness.freeze import write_freeze
    from eval.run_retrieval import main

    run = run_secrets()
    phrase = sentinel()
    ids = ("R-1", "R-2", "R-4", "R-5")
    texts = {**QUERY_TEXTS, "R-1": f"{QUERY_TEXTS['R-1']} {phrase}"}
    index = ScriptedIndex({texts[i]: TABLE[QUERY_TEXTS[i]] for i in ids})
    queries_dir = write_retrieval_queries(tmp_path / "queries", queries(*ids, query_texts=texts))
    freeze_file = tmp_path / "freeze.json"
    write_freeze(freeze_file)
    log = io.StringIO()
    deps = HarnessDeps(
        env={**env_for(run), "MERIDIAN_AGENT_VERSION": "v-cap7"}, freeze_file=freeze_file, log_stream=log
    )
    reports = tmp_path / "reports"
    argv = [
        "--index-dir",
        str(write_index_dir(tmp_path)),
        "--queries-dir",
        str(queries_dir),
        "--reports-dir",
        str(reports),
    ]
    code = main(argv, deps=deps, index_factory=lambda _path: index)
    out = Outcome(code=code, log_text=log.getvalue(), reports_dir=reports, stub=None, judge=None)
    assert code == 0
    report = out.report()
    record = report["run"]
    assert UUID4.match(record["run_id"])
    assert (record["suite"], record["split"], record["status"]) == ("retrieval", None, "completed")
    assert record["agent_version"] == "v-cap7"
    assert record["harness_commit"]
    assert HEX64.match(record["harness_digest"])
    assert record["index_manifest_hash"] == INDEX_MANIFEST
    assert record["cases_scored"] == record["cases_expected"] == 4
    assert [r["case_id"] for r in report["results"]] == list(ids)
    for result in report["results"]:
        assert result["run_id"] == record["run_id"]
        assert result["top3"] and all(d["version_label"] for d in result["top3"])
        assert isinstance(result["below_floor"], bool)
    summary = report["summary"]
    validate_eval_run(summary)
    hit_at_3 = next(m for m in summary["measures"] if m["id"] == "M-6")
    assert (hit_at_3["numerator"], hit_at_3["denominator"]) == (2, 3)
    assert summary["run_id"] == record["run_id"]
    assert summary["agent_version"] == "v-cap7"
    assert_targets_only_in_target_column(out.markdown(), summary)
    _assert_json_log(out)
    assert len([line for line in out.log_lines() if line["event"] == "retrieval_query_scored"]) == 4
    assert_absent(out.all_text(), [run.eval_key, run.password, phrase], where="the retrieval run outputs")
    assert block_network == []


def test_report_loads_through_start_up_loader(tmp_path: Path) -> None:
    """seam (P-4): a report the harness wrote is accepted by the app's start-up loader and found by its reader."""
    run = run_secrets()
    cases = write_cases(tmp_path / "cases", [(simple_case("D-1"), simple_key("D-1"))])
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports"), stub=make_stub(run), run=run)
    assert out.code == 0
    with temp_sqlite() as store:
        assert load_eval_reports(out.reports_dir, store.uow) == 1
        with store.uow() as tx:
            assert tx.ops.eval.latest_completed("e2e", "dev") is not None
        assert load_eval_reports(out.reports_dir, store.uow) == 0
