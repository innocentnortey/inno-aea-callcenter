"""AEA-24 AC-9 and AC-23: the load suite (E-8, WF-10) against the stub."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from eval.harness.tests.db_seed import SeedBuilder, copy_issued
from eval.harness.tests.fixture_cases import (
    flip_one_byte,
    harness_copy,
    run_secrets,
    simple_case,
    simple_key,
    write_cases,
)
from eval.harness.tests.stub_app import (
    DEFAULT_CLOCK,
    OTHER_CLOCK,
    StubCall,
    failure_offer_block,
    notice_of,
    text_block,
)
from eval.harness.tests.support import (
    FakeJudge,
    assert_all_requests_have_eval_headers,
    base_argv,
    make_stub,
    run_cli,
)

TIMING_KEYS = {
    "run_id",
    "thread_id",
    "turn_id",
    "conversation_index",
    "turn_index",
    "sent_at",
    "first_byte_ms",
    "total_ms",
    "http_status",
    "outcome",
    "notice_code",
}


def _load_cases(tmp_path: Path) -> Path:
    return write_cases(tmp_path / "cases", [(simple_case("L-1"), simple_key("L-1"))])


def _load_argv(
    tmp_path: Path, *, conversations: int | None = None, extra: list[str] | None = None
) -> list[str]:
    more = list(extra or [])
    if conversations is not None:
        more += ["--conversations", str(conversations)]
    return base_argv(_load_cases(tmp_path), tmp_path / "reports", suite="load", repeats=1, extra=more)


def test_load_twenty_concurrent_against_stub(tmp_path: Path) -> None:
    """invariant: 20 conversations at once, one timing line per submitTurn, p50/p95/max, no judge call."""
    run = run_secrets()
    judge = FakeJudge()
    stub = make_stub(run, turn_delay_s=0.2)
    out = run_cli(tmp_path, _load_argv(tmp_path), stub=stub, run=run, judge=judge)
    assert out.code == 0
    assert stub.max_in_flight_turns == 20
    timings = out.timings()
    assert len(timings) == len(stub.turn_requests()) == 20
    assert all(set(t) == TIMING_KEYS for t in timings)
    assert all(t["sent_at"].endswith(("Z", "+00:00")) for t in timings), "sent_at is UTC"
    assert sorted(t["conversation_index"] for t in timings) == list(range(20))
    report = out.report()
    assert report["run"]["suite"] == "load"
    assert all(t["run_id"] == report["run"]["run_id"] for t in timings)
    latency = report["summary"]["latency_ms"]
    for stat in ("p50", "p95", "max"):
        assert isinstance(latency[stat]["value"], int)
    assert latency["p95"]["target"] == "≤ 12500 ms at 20 at once"
    assert latency["turns"] == 20
    assert judge.calls == []
    assert_all_requests_have_eval_headers(stub, run, report["run"]["run_id"], "load")


def test_db_copy_check_after_load(tmp_path: Path) -> None:
    """failure: a seeded double booking on the working copy fails the load run and is named."""
    run = run_secrets()
    copy = copy_issued(tmp_path / "copy.sqlite")
    builder = SeedBuilder(copy)
    builder.double_booking()
    builder.close()
    argv = _load_argv(tmp_path, conversations=2, extra=["--db-copy", str(copy)])
    out = run_cli(tmp_path, argv, stub=make_stub(run), run=run)
    assert out.code == 4
    gate = out.report()["summary"]["gates"]["db_copy"]
    assert gate["state"] == "fail"
    assert any(entry.startswith("double_booking") for entry in gate["failed"])


def test_incomplete_load_run_not_reported(tmp_path: Path) -> None:
    """failure: fewer conversations finished than scripted makes the run incomplete with no latency numbers."""
    run = run_secrets()
    stub = make_stub(run, clock_for_thread=lambda n: OTHER_CLOCK if n == 1 else DEFAULT_CLOCK)
    out = run_cli(tmp_path, _load_argv(tmp_path, conversations=3), stub=stub, run=run)
    assert out.code == 1
    report = out.report()
    assert report["run"]["status"] == "incomplete"
    assert (report["run"]["cases_expected"], report["run"]["cases_scored"]) == (3, 2)
    assert "latency_ms" not in report["summary"]
    assert report["summary"]["measures"] == []


def test_first_failure_and_degrades_filed_apart(tmp_path: Path) -> None:
    """invariant: notices, degraded handoffs and transport errors are counted in rows apart from wrong answers."""
    run = run_secrets()

    def scripted(call: StubCall) -> dict[str, Any] | None:
        if call.thread_index == 0:
            return call.reply([text_block("Please try again.")], notice=notice_of("TURN_TIMEOUT"))
        if call.thread_index == 1:
            return call.reply([failure_offer_block()])
        return {"__status__": 500}

    out = run_cli(tmp_path, _load_argv(tmp_path, conversations=3), stub=make_stub(run, scripted), run=run)
    report = out.report()
    assert report["run"]["status"] == "completed"
    summary = report["summary"]
    assert {k: v for k, v in summary["turn_rows"].items() if v} == {"notice": 2, "error": 1}
    assert {k: v for k, v in summary["notice_codes"].items() if v} == {
        "TURN_TIMEOUT": 1,
        "degraded_handoff": 1,
    }
    assert summary["failure_rows"] == [
        {"category": "operational_degrade", "count": 2},
        {"category": "environment", "count": 1},
    ]


def test_tamper_refuses_load(tmp_path: Path) -> None:
    """regression: a one-byte change to the harness source refuses the load run with no results and no request."""
    run = run_secrets()
    stub = make_stub(run)
    copy = harness_copy(tmp_path)
    from eval.harness.freeze import write_freeze

    write_freeze(tmp_path / "freeze.json", root=copy)
    flip_one_byte(copy)
    out = run_cli(tmp_path, _load_argv(tmp_path), stub=stub, run=run, harness_root=copy, freeze=False)
    assert out.code == 3
    report = out.report()
    assert report["run"]["status"] == "failed"
    assert report["results"] == []
    assert stub.requests == []


def test_percentile_is_nearest_rank() -> None:
    """boundary: nearest rank, sorted(v)[ceil(q*n)-1]."""
    from eval.harness.load import percentile

    values = list(range(1, 21))
    assert percentile(values, 0.5) == 10
    assert percentile(values, 0.95) == 19
    assert percentile(values, 1.0) == 20
    assert percentile([7], 0.95) == 7
    assert percentile([30, 10, 20], 0.5) == 20
