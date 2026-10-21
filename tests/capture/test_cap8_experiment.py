"""AEA-24 CAP-8 (WF-12): an experiment run is an e2e dev run with its id stamped, scored by the same rules."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from eval.harness.tests.fixture_cases import (
    GATE_IDS,
    coded_case,
    coded_scripted,
    flip_one_byte,
    gate_cases,
    gate_scripted,
    harness_copy,
    run_secrets,
    sentinel,
    simple_case,
    simple_key,
    wp4_case,
    wp4_key,
    wp4_scripted,
    write_cases,
    write_sealed_heldout,
)
from eval.harness.tests.netblock import block_network
from eval.harness.tests.stub_app import DEFAULT_CLOCK, OTHER_CLOCK
from eval.harness.tests.support import (
    HEX64,
    UUID4,
    FakeJudge,
    assert_absent,
    assert_all_requests_have_eval_headers,
    assert_log_allow_listed,
    base_argv,
    items_of,
    make_stub,
    run_cli,
)

__all__ = ["block_network"]
AGENT_VERSION = "abc123def456+0a1b2c3d"
CODE_TEXTS = (
    "The $49 fee applies under current policy.",
    "Your original appointment stays until a representative confirms.",
    "A representative will get back to you within 1 business day",
    "I can't promise anyone will confirm a change before your appointment starts",
    "charged",
    "moved",
)
XP = ["--experiment", "XP-1"]


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_experiment_record(tmp_path: Path, block_network: list[object]) -> None:
    """capture: --experiment XP-1 stamps the run; without the flag the id is None and the report says none."""
    phrase = sentinel()
    run = run_secrets()
    stub = make_stub(run, coded_scripted, agent_version=AGENT_VERSION)
    cases = write_cases(
        tmp_path / "cases", [(coded_case("D-1", f"Hello, {phrase}, I need help."), simple_key("D-1"))]
    )
    out = run_cli(
        tmp_path, base_argv(cases, tmp_path / "xp_reports", repeats=3, extra=XP), stub=stub, run=run
    )
    assert out.code == 0
    report = out.report()
    record = report["run"]
    assert record["experiment_id"] == "XP-1"
    assert UUID4.match(record["run_id"])
    assert HEX64.match(record["harness_digest"])
    assert record["agent_version"] == AGENT_VERSION
    assert (record["status"], record["repeats"]) == ("completed", 3)
    assert report["summary"]["experiment_id"] == "XP-1"
    assert report["summary"]["measures"]
    assert all(m["min"] is not None and m["max"] is not None for m in report["summary"]["measures"])
    assert re.search(r"\|\s*Experiment\s*\|\s*XP-1\s*\|", out.markdown())
    assert_all_requests_have_eval_headers(stub, run, record["run_id"], "eval")
    assert_log_allow_listed(out.log_lines())
    assert_absent(
        out.all_text(),
        [run.eval_key, run.password, run.username, phrase, *stub.issued_codes],
        where="the experiment",
    )

    plain_stub = make_stub(run, coded_scripted)
    plain = run_cli(
        tmp_path, base_argv(cases, tmp_path / "plain_reports", repeats=3), stub=plain_stub, run=run
    )
    assert plain.report()["run"]["experiment_id"] is None
    assert re.search(r"\|\s*Experiment\s*\|\s*none\s*\|", plain.markdown())
    assert block_network == []


def test_experiment_refused_on_heldout(tmp_path: Path) -> None:
    """failure: an experiment on the held-out split is refused before any request, naming the split only."""
    run = run_secrets()
    stub = make_stub(run)
    write_sealed_heldout(
        tmp_path / "cases", tmp_path / "keys", [(simple_case("H-1", split="held-out"), simple_key("H-1"))]
    )
    argv = base_argv(
        tmp_path / "cases",
        tmp_path / "reports",
        split="held-out",
        extra=[*XP, "--heldout-key-dir", str(tmp_path / "keys")],
    )
    out = run_cli(tmp_path, argv, stub=stub, run=run)
    assert out.code == 2
    assert stub.requests == []
    assert out.json_files() == []
    assert "refused: --experiment is not allowed with --split held-out" in out.log_text
    assert "held-out" in out.log_text
    assert "XP-1" not in out.log_text


def test_experiment_scoring_rules(tmp_path: Path) -> None:
    """invariant: sentence checks are code checks, the judge sees none of them, judge items stay advisory."""
    run = run_secrets()
    judge = FakeJudge()
    cases = write_cases(tmp_path / "cases", [(wp4_case(), wp4_key())])
    argv = base_argv(cases, tmp_path / "reports", extra=[*XP, "--calibration", str(tmp_path / "none.json")])
    out = run_cli(tmp_path, argv, stub=make_stub(run, wp4_scripted(charged=True)), run=run, judge=judge)
    result = out.report()["results"][0]
    assert items_of(result, "must_not_say")[0]["passed"] is False
    assert [i["passed"] for i in items_of(result, "must_say")[:3]] == [True, True, True]
    assert judge.calls, "the judge still gets the free-text meaning items"
    for rubric in judge.rubrics():
        assert rubric not in CODE_TEXTS
    assert all(i["passed"] is None for i in items_of(result, "judge"))


def test_experiment_hard_gates(tmp_path: Path) -> None:
    """invariant: a seeded breach of any one hard gate fails that case and the experiment run's gate."""
    for gate in GATE_IDS:
        root = tmp_path / gate
        root.mkdir()
        run = run_secrets()
        cases = write_cases(root / "cases", gate_cases(only=[gate]))
        out = run_cli(
            root, base_argv(cases, root / "reports", extra=XP), stub=make_stub(run, gate_scripted), run=run
        )
        report = out.report()
        assert out.code == 4, gate
        assert report["results"][0]["passed_hard"] is False, gate
        assert report["summary"]["gates"][gate]["state"] == "fail", gate


def test_experiment_edits_no_case_file(tmp_path: Path) -> None:
    """invariant (EV-9): the SHA-256 of every case and key file is the same before and after the run."""
    run = run_secrets()
    cases = write_cases(
        tmp_path / "cases", [(wp4_case(), wp4_key()), (simple_case("S-1"), simple_key("S-1"))]
    )
    before = _tree_hashes(cases)
    assert before
    run_cli(
        tmp_path,
        base_argv(cases, tmp_path / "reports", extra=XP),
        stub=make_stub(run, wp4_scripted()),
        run=run,
    )
    assert _tree_hashes(cases) == before


def test_incomplete_experiment_not_reported(tmp_path: Path) -> None:
    """failure (OBS-38): a case that could not be played makes the experiment incomplete and reports no measure."""
    run = run_secrets()
    stub = make_stub(run, clock_for_thread=lambda n: OTHER_CLOCK if n == 1 else DEFAULT_CLOCK)
    cases = write_cases(
        tmp_path / "cases", [(simple_case("A-1"), simple_key("A-1")), (simple_case("A-2"), simple_key("A-2"))]
    )
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports", extra=XP), stub=stub, run=run)
    assert out.code == 1
    report = out.report()
    assert report["run"]["status"] == "incomplete"
    assert report["run"]["experiment_id"] == "XP-1"
    assert report["summary"]["measures"] == []
    assert report["summary"]["headline"] is None


def test_experiment_tamper_and_dry_run(tmp_path: Path, block_network: list[object]) -> None:
    """regression: a one-byte change refuses the run; a dry run makes no network call and no request."""
    from eval.harness.freeze import write_freeze

    run = run_secrets()
    cases = write_cases(tmp_path / "cases", [(simple_case("A-1"), simple_key("A-1"))])
    copy = harness_copy(tmp_path)
    write_freeze(tmp_path / "freeze.json", root=copy)
    flip_one_byte(copy)
    tamper_stub = make_stub(run)
    tampered = run_cli(
        tmp_path,
        base_argv(cases, tmp_path / "tamper_reports", extra=XP),
        stub=tamper_stub,
        run=run,
        harness_root=copy,
        freeze=False,
    )
    assert tampered.code == 3
    report = tampered.report()
    assert report["run"]["status"] == "failed"
    assert report["results"] == []
    assert tamper_stub.requests == []

    dry_dir = tmp_path / "dry"
    dry_dir.mkdir()
    dry_stub = make_stub(run)
    dry_argv = base_argv(cases, dry_dir / "reports", base_url=None, extra=[*XP, "--dry-run"])
    dry = run_cli(dry_dir, dry_argv, stub=dry_stub, run=run)
    assert dry.code == 0
    assert dry_stub.requests == []
    assert block_network == []
    assert "dry_run_finished" in {line["event"] for line in dry.log_lines()}
