"""AEA-24 AC-1, AC-5, AC-6, AC-8 (runner half), P-1, P-2: the runner plays cases over HTTP and refuses honestly."""

from __future__ import annotations

import io
import json
import re
import secrets
import sqlite3
import uuid
from pathlib import Path

import pytest

from eval.harness.tests.db_seed import copy_issued
from eval.harness.tests.fixture_cases import (
    ISSUED_DB,
    env_for,
    flip_one_byte,
    harness_copy,
    item,
    run_secrets,
    simple_case,
    simple_key,
    wp4_case,
    wp4_key,
    wp4_scripted,
    write_cases,
    write_sealed_heldout,
)
from eval.harness.tests.stub_app import DEFAULT_CLOCK, OTHER_CLOCK, StubApp
from eval.harness.tests.support import (
    FakeJudge,
    assert_all_requests_have_eval_headers,
    base_argv,
    make_stub,
    run_cli,
)


def _seed_values() -> tuple[str, str]:
    con = sqlite3.connect(f"file:{ISSUED_DB}?mode=ro", uri=True)
    try:
        row = con.execute("SELECT name, phone FROM customers WHERE customer_id = 'MHC-57204'").fetchone()
        return str(row[0]), str(row[1])
    finally:
        con.close()


def test_runner_plays_case_over_http_with_inbox_code(tmp_path: Path) -> None:
    """invariant: HTTP only, one login, one chat per case, a fresh turn_id per turn, the inbox code, the seed values,
    the three eval headers on every request, and a clock-mismatch case is refused and scores nothing (AC-1)."""
    run = run_secrets()
    stub = make_stub(
        run,
        wp4_scripted(),
        clock_for_thread=lambda n: DEFAULT_CLOCK if n == 0 else OTHER_CLOCK,
    )
    cases = write_cases(
        tmp_path / "cases",
        [(wp4_case(), wp4_key()), (simple_case("X-CLOCK"), simple_key("X-CLOCK"))],
    )
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports"), stub=stub, run=run)

    report = out.report()
    run_id = report["run"]["run_id"]
    paths = stub.paths()
    assert paths[0] == ("POST", "/api/login")
    assert paths.count(("POST", "/api/login")) == 1
    assert paths[1] == ("GET", "/api/eval/latest")
    assert paths[2] == ("GET", "/api/monitoring")
    core = [p for p in paths if p[1] not in ("/api/demo/inbox", "/api/monitoring")]
    thread = "/api/chat/sessions/thr_0/turns"
    assert core == [
        ("POST", "/api/login"),
        ("GET", "/api/eval/latest"),
        ("GET", "/api/demo/clock"),
        ("POST", "/api/chat/sessions"),
        *[("POST", thread)] * 5,
        ("GET", "/api/demo/clock"),
    ]

    bodies = stub.turn_bodies()
    turn_ids = [b["turn_id"] for b in bodies]
    assert len(set(turn_ids)) == 5
    assert all(uuid.UUID(t).version == 4 for t in turn_ids)
    assert [b["payload"]["kind"] for b in bodies] == ["text", "form", "code", "text", "text"]
    name, phone = _seed_values()
    assert bodies[1]["payload"]["values"] == {"name": name, "phone": phone}
    assert bodies[1]["payload"]["card_id"] == "card-locate"
    assert bodies[2]["payload"] == {"kind": "code", "card_id": "card-code", "code": stub.issued_codes[0]}

    assert_all_requests_have_eval_headers(stub, run, run_id, "eval")

    assert [r["case_id"] for r in report["results"]] == ["WP-4"]
    assert report["run"]["status"] == "incomplete"
    assert (report["run"]["cases_expected"], report["run"]["cases_scored"]) == (2, 1)
    assert out.code == 1


def test_tamper_check_refuses_scoring(tmp_path: Path) -> None:
    """regression: a one-byte change to the harness source makes the run `failed` with no results and no request."""
    run = run_secrets()
    stub = make_stub(run)
    cases = write_cases(tmp_path / "cases", [(simple_case("A-1"), simple_key("A-1"))])
    copy = harness_copy(tmp_path)
    from eval.harness.freeze import write_freeze

    write_freeze(tmp_path / "freeze.json", root=copy)
    flip_one_byte(copy)
    out = run_cli(
        tmp_path, base_argv(cases, tmp_path / "reports"), stub=stub, run=run, harness_root=copy, freeze=False
    )
    assert out.code == 3
    report = out.report()
    assert report["run"]["status"] == "failed"
    assert report["results"] == []
    assert stub.requests == []


def test_dry_run_makes_no_paid_call(tmp_path: Path, block_network: list[object]) -> None:
    """boundary: --dry-run plays canned responses: exit 0, no judge call, no network, no report file."""
    run = run_secrets()
    judge = FakeJudge()
    cases = write_cases(tmp_path / "cases", [(simple_case("A-1"), simple_key("A-1"))])
    reports = tmp_path / "reports"
    argv = base_argv(cases, reports, base_url=None, extra=["--dry-run"])
    out = run_cli(tmp_path, argv, stub=None, run=run, judge=judge)
    assert out.code == 0
    assert judge.calls == []
    assert block_network == []
    assert not reports.exists() or not any(reports.iterdir())
    assert "dry_run_finished" in {line["event"] for line in out.log_lines()}


def test_dry_run_works_before_first_freeze(tmp_path: Path, block_network: list[object]) -> None:
    """boundary: a dry run needs no freeze file (it only refuses on tamper when one exists)."""
    run = run_secrets()
    cases = write_cases(tmp_path / "cases", [(simple_case("A-1"), simple_key("A-1"))])
    argv = base_argv(cases, tmp_path / "reports", base_url=None, extra=["--dry-run"])
    out = run_cli(tmp_path, argv, stub=None, run=run, freeze=False)
    assert out.code == 0
    assert block_network == []


def test_heldout_refuses_on_hash_mismatch(tmp_path: Path) -> None:
    """failure: keys whose hash differs from the recorded one refuse scoring, name both hashes, make no request."""
    from eval.cases.seal import heldout_key_sha256

    run = run_secrets()
    stub = make_stub(run)
    cases_dir = tmp_path / "cases"
    key_a = tmp_path / "keys_a"
    held = [(simple_case("H-1", split="held-out"), simple_key("H-1"))]
    recorded = write_sealed_heldout(cases_dir, key_a, held)
    key_b = tmp_path / "keys_b"
    other = [
        (simple_case("H-1", split="held-out"), simple_key("H-1", must_say=[item("a different expectation")]))
    ]
    write_cases(tmp_path / "other_root", other, split="held-out", key_dir=key_b)
    computed = heldout_key_sha256(key_b)
    assert recorded != computed

    argv = base_argv(
        cases_dir, tmp_path / "reports", split="held-out", extra=["--heldout-key-dir", str(key_b)]
    )
    out = run_cli(tmp_path, argv, stub=stub, run=run)
    assert out.code == 3
    assert recorded in out.log_text
    assert computed in out.log_text
    report = out.report()
    assert report["run"]["status"] == "failed"
    assert report["results"] == []
    assert stub.requests == []


def test_runner_runs_db_check_after_e2e(tmp_path: Path) -> None:
    """invariant: with --db-copy the DB-copy check runs after the last turn and its output is in the report."""
    run = run_secrets()
    stub = make_stub(run, wp4_scripted())
    cases = write_cases(tmp_path / "cases", [(wp4_case(), wp4_key())])
    copy = copy_issued(tmp_path / "copy.sqlite")
    argv = base_argv(cases, tmp_path / "reports", extra=["--db-copy", str(copy)])
    out = run_cli(tmp_path, argv, stub=stub, run=run)
    assert out.code == 0
    summary = out.report()["summary"]
    assert summary["db_check"]["status"] == "ran"
    assert summary["db_check"]["writes"] == 0
    assert summary["db_check"]["untouched_ok"] == [1]
    assert summary["gates"]["db_copy"]["state"] == "pass"
    events = [line["event"] for line in out.log_lines()]
    last_turn = max(i for i, e in enumerate(events) if e == "turn_done")
    assert events.index("db_check_done") > last_turn


def test_missing_environment_variable_is_a_usage_error(tmp_path: Path) -> None:
    """boundary: a missing eval key is exit 2 before any request and writes no report."""
    run = run_secrets()
    stub = make_stub(run)
    cases = write_cases(tmp_path / "cases", [(simple_case("A-1"), simple_key("A-1"))])
    env = env_for(run)
    del env["MERIDIAN_EVAL_KEY"]
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports"), stub=stub, run=run, env=env)
    assert out.code == 2
    assert stub.requests == []
    assert out.json_files() == []
    assert "MERIDIAN_EVAL_KEY" in out.log_text


def test_login_failure_is_a_failed_run(tmp_path: Path) -> None:
    """failure: a refused login stops the run: exit 3, status failed, no results, no chat opened."""
    run = run_secrets()
    stub = StubApp(username=run.username, password=secrets.token_urlsafe(16), eval_key=run.eval_key)
    cases = write_cases(tmp_path / "cases", [(simple_case("A-1"), simple_key("A-1"))])
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports"), stub=stub, run=run)
    assert out.code == 3
    report = out.report()
    assert report["run"]["status"] == "failed"
    assert report["results"] == []
    assert stub.paths() == [("POST", "/api/login")]


def test_heldout_hash_matches_cases_seal(tmp_path: Path) -> None:
    """invariant (P-1): the harness computes the held-out hash by the same byte rule as AEA-06's seal."""
    from eval.cases.seal import heldout_key_sha256 as seal_hash
    from eval.harness.cases import heldout_key_sha256

    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    for name, key in (("b", simple_key("b")), ("A", simple_key("A", must_say=[item("something to say")]))):
        (key_dir / f"{name}.key.json").write_text(key.model_dump_json(indent=2), encoding="utf-8")
    (key_dir / "notes.txt").write_text("not a key file", encoding="utf-8")
    (key_dir / "nested").mkdir()
    assert heldout_key_sha256(key_dir) == seal_hash(key_dir)


def test_runlog_refuses_unlisted_key_and_free_text() -> None:
    """invariant (P-2): the run log fails closed on an unlisted key, free text or a known secret; nothing is written."""
    from eval.harness.runlog import RunLog
    from eval.harness.scrub import LeakDetected, Scrubber

    stream = io.StringIO()
    scrubber = Scrubber()
    secret = "s3cret-" + secrets.token_hex(6)
    scrubber.add(secret)
    log = RunLog(stream, scrubber)
    with pytest.raises(ValueError, match="log key not allowed"):
        log.emit("run_started", body="free text")
    with pytest.raises(ValueError, match="log value not allowed"):
        log.emit("run_started", reason="has spaces")
    with pytest.raises(LeakDetected):
        log.emit("run_started", reason=secret)
    assert stream.getvalue() == ""
    log.emit("run_started", run_id="abc-1", suite="e2e")
    lines = stream.getvalue().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"event": "run_started", "run_id": "abc-1", "suite": "e2e"}
    assert re.fullmatch(r"[\w.:+#/@-]{0,200}", "abc-1")
