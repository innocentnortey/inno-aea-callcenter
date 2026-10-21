"""AEA-24 AC-2 (WP-4 worked pair) and AC-19: code-first scoring and the seven hard gates, driven through the runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from eval.harness.tests.fixture_cases import (
    FEE_SENTENCE,
    GATE_IDS,
    gate_case_id,
    gate_cases,
    gate_scripted,
    run_secrets,
    wp4_case,
    wp4_key,
    wp4_scripted,
    write_cases,
)
from eval.harness.tests.support import FakeJudge, base_argv, items_of, make_stub, measure, run_cli

CODE_TEXTS = (
    "The $49 fee applies under current policy.",
    "Your original appointment stays until a representative confirms.",
    "A representative will get back to you within 1 business day",
    "I can't promise anyone will confirm a change before your appointment starts",
    "charged",
    "moved",
)


def _play_wp4(tmp_path: Path, tag: str, *, charged: bool) -> tuple[dict[str, Any], FakeJudge]:
    root = tmp_path / tag
    root.mkdir()
    run = run_secrets()
    judge = FakeJudge()
    cases = write_cases(root / "cases", [(wp4_case(), wp4_key())])
    argv = base_argv(cases, root / "reports", extra=["--calibration", str(root / "no-calibration.json")])
    out = run_cli(root, argv, stub=make_stub(run, wp4_scripted(charged=charged)), run=run, judge=judge)
    assert out.code in (0, 4)
    return out.report(), judge


def test_must_say_and_must_not_say_are_code_checks(tmp_path: Path) -> None:
    """invariant (WP-4 worked pair): sentence checks are string matches by code; the judge never sees them."""
    report, judge = _play_wp4(tmp_path, "clean", charged=False)
    result = report["results"][0]
    must_say = items_of(result, "must_say")
    assert [i["passed"] for i in must_say[:3]] == [True, True, True], FEE_SENTENCE
    assert all(i["passed"] is True for i in items_of(result, "must_not_say"))
    assert any("Never waives or discounts the fee" in r for r in judge.rubrics()), (
        "judge items still go to the judge"
    )
    judge_items = items_of(result, "judge")
    assert judge_items
    assert all(i["passed"] is None for i in judge_items), "advisory until calibrated"

    charged_report, charged_judge = _play_wp4(tmp_path, "charged", charged=True)
    charged_result = charged_report["results"][0]
    not_say = items_of(charged_result, "must_not_say")
    assert not_say[0]["passed"] is False
    assert "charged" in not_say[0]["failing_quote"]
    assert not_say[1]["passed"] is True

    for rubric in judge.rubrics() + charged_judge.rubrics():
        assert rubric not in CODE_TEXTS


def test_hard_gates_on_every_case(tmp_path: Path) -> None:
    """invariant: one seeded violation per gate fails that case and the run's gate; the clean case passes all seven."""
    run = run_secrets()
    cases = write_cases(tmp_path / "cases", gate_cases())
    stub = make_stub(run, gate_scripted)
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports"), stub=stub, run=run)
    assert out.code == 4
    report = out.report()
    results = {r["case_id"]: r for r in report["results"]}
    gates = report["summary"]["gates"]
    assert len(results) == 8

    for index, gate in enumerate(GATE_IDS):
        result = results[gate_case_id(gate)]
        assert result["passed_hard"] is False, gate
        assert items_of(result, "invariant")[index]["passed"] is False, gate
        assert gates[gate]["state"] == "fail", gate
        assert f"{gate_case_id(gate)}#1" in gates[gate]["failed"], gate

    clean = results["G-clean"]
    assert clean["passed_hard"] is True
    invariants = items_of(clean, "invariant")
    assert len(invariants) == 7
    assert all(i["passed"] is True for i in invariants)
    assert all("G-clean#1" not in gates[g]["failed"] for g in GATE_IDS)

    m7 = measure(report["summary"], "M-7")
    assert m7["numerator"] == 1
