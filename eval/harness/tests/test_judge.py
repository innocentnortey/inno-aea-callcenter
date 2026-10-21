"""AEA-24 AC-3 and AC-13, P-3: the judge is advisory until calibrated, and spend never passes its caps."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from eval.harness.tests.fixture_cases import (
    item,
    run_secrets,
    simple_case,
    simple_key,
    write_cases,
)
from eval.harness.tests.support import FakeJudge, base_argv, make_stub, run_cli

RANK = {"must_say": 0, "must_not_say": 0, "must_do": 1, "invariant": 1, "trajectory": 2, "judge": 3}


def _judge_case(root: Path) -> Path:
    key = simple_key(
        "J-1",
        must_say=[item("I can help with that")],
        must_not_say=[item("refund", "R-1")],
        judge_items=[item("Explains the plan honestly", "DEC-2", hard=True)],
    )
    return write_cases(root / "cases", [(simple_case("J-1"), key)])


def _run(tmp_path: Path, tag: str, calibration: Path) -> dict[str, Any]:
    root = tmp_path / tag
    root.mkdir()
    run = run_secrets()
    judge = FakeJudge(failing={0})
    argv = base_argv(_judge_case(root), root / "reports", extra=["--calibration", str(calibration)])
    out = run_cli(root, argv, stub=make_stub(run), run=run, judge=judge)
    assert out.code in (0, 4)
    assert judge.calls, "the judge is asked about the judge item"
    return out.report()["results"][0]  # type: ignore[no-any-return]


def test_judge_advisory_until_calibrated(tmp_path: Path) -> None:
    """invariant: grader order assertion, invariant, trajectory, judge; an uncalibrated judge never changes passed_hard."""
    uncalibrated = _run(tmp_path, "uncal", tmp_path / "absent.json")
    ranks = [RANK[i["item"]] for i in uncalibrated["items"]]
    assert ranks == sorted(ranks)
    judge_item = next(i for i in uncalibrated["items"] if i["item"] == "judge")
    assert judge_item["passed"] is None
    assert judge_item["failing_quote"].startswith("[judge fail]")
    assert uncalibrated["passed_hard"] is True

    record = tmp_path / "calibration.json"
    record.write_text(
        json.dumps(
            {
                "judge_model": "fake-judge",
                "labels": 20,
                "agreement": 0.85,
                "recorded_on": "2026-10-20",
                "labelled_by": "Innocent",
            }
        ),
        encoding="utf-8",
    )
    calibrated = _run(tmp_path, "cal", record)
    judge_item = next(i for i in calibrated["items"] if i["item"] == "judge")
    assert judge_item["passed"] is False
    assert calibrated["passed_hard"] is False


def test_calibration_needs_enough_labels_agreement_and_the_same_model(tmp_path: Path) -> None:
    """boundary: calibrated means >= 20 labels, >= 0.8 agreement, for the judge model in use; a missing file is none."""
    from eval.harness.judge import CalibrationRecord, is_calibrated, load_calibration

    def record(**over: Any) -> CalibrationRecord:
        fields: dict[str, Any] = {
            "judge_model": "m",
            "labels": 20,
            "agreement": 0.8,
            "recorded_on": "2026-10-20",
            "labelled_by": "Innocent",
        }
        return CalibrationRecord.model_validate({**fields, **over})

    assert is_calibrated(record(), judge_model="m") is True
    assert is_calibrated(record(labels=19), judge_model="m") is False
    assert is_calibrated(record(agreement=0.79), judge_model="m") is False
    assert is_calibrated(record(), judge_model="other") is False
    assert is_calibrated(None, judge_model="m") is False
    assert load_calibration(tmp_path / "missing.json") is None


def test_judge_spend_ledger_stops_at_cap(tmp_path: Path) -> None:
    """failure: charges up to $5 for a Chicago day pass, the next raises and writes nothing; a new day starts at 0."""
    from eval.harness.ledger import HarnessLedger, JudgeSpendCapReached

    now = {"at": datetime(2026, 10, 17, 4, 30, tzinfo=UTC)}  # 23:30 on Oct 16 in Chicago
    ledger = HarnessLedger(5.0, path=tmp_path / "ledger", now=lambda: now["at"])
    ledger.charge(2.5)
    ledger.charge(2.5)
    assert ledger.spent_today() == pytest.approx(5.0)
    day_file = tmp_path / "ledger" / "2026-10-16.jsonl"
    assert len(day_file.read_text(encoding="utf-8").splitlines()) == 2
    with pytest.raises(JudgeSpendCapReached):
        ledger.charge(0.01)
    assert len(day_file.read_text(encoding="utf-8").splitlines()) == 2
    with pytest.raises(ValueError):
        ledger.charge(-1.0)

    now["at"] = datetime(2026, 10, 17, 5, 30, tzinfo=UTC)  # 00:30 on Oct 17 in Chicago
    assert ledger.spent_today() == 0.0
    ledger.charge(1.0)
    assert ledger.spent_today() == pytest.approx(1.0)
    assert (tmp_path / "ledger" / "2026-10-17.jsonl").exists()


def test_preflight_refuses_over_cap() -> None:
    """failure: today + run estimate + judge cap past the app's cap refuses; equal passes; no spend block refuses."""
    from eval.harness.ledger import SpendPreflightRefused, preflight_spend

    with pytest.raises(SpendPreflightRefused):
        preflight_spend(
            {"spend": {"today_cents": 2900, "cap_cents": 3000}}, run_estimate_usd=0.5, judge_cap_usd=5.0
        )
    preflight_spend(
        {"spend": {"today_cents": 2450, "cap_cents": 3000}}, run_estimate_usd=0.5, judge_cap_usd=5.0
    )
    with pytest.raises(SpendPreflightRefused):
        preflight_spend({}, run_estimate_usd=0.0, judge_cap_usd=0.0)
    with pytest.raises(SpendPreflightRefused):
        preflight_spend({"spend": {"cap_cents": 3000}}, run_estimate_usd=0.0, judge_cap_usd=0.0)


class _FakeMessages:
    def __init__(self, text: str) -> None:
        self.calls: list[dict[str, Any]] = []
        self._text = text

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


class _FakeAnthropic:
    def __init__(self, text: str) -> None:
        self.messages = _FakeMessages(text)


def test_anthropic_judge_charges_ledger_before_call(tmp_path: Path) -> None:
    """invariant (P-3): the ledger is charged before the call, so a refused charge means no call at all."""
    from eval.harness.judge import AnthropicJudge
    from eval.harness.ledger import HarnessLedger, JudgeSpendCapReached

    reply = '{"verdicts": [{"index": 0, "passed": true, "quote": "the reply words"}]}'
    near_cap = HarnessLedger(0.001, path=tmp_path / "near")
    refused_client = _FakeAnthropic(reply)
    with pytest.raises(JudgeSpendCapReached):
        AnthropicJudge(refused_client, ledger=near_cap).judge(reply="r", evidence=["e"], rubric=["claim"])
    assert refused_client.messages.calls == []

    ledger = HarnessLedger(5.0, path=tmp_path / "ok")
    client = _FakeAnthropic(reply)
    judge = AnthropicJudge(client, ledger=ledger)
    verdicts = judge.judge(reply="r", evidence=["e"], rubric=["claim"])
    assert [(v.index, v.passed, v.quote) for v in verdicts] == [(0, True, "the reply words")]
    assert len(client.messages.calls) == 1
    assert client.messages.calls[0]["model"] == judge.model
    assert client.messages.calls[0]["temperature"] == 0
    assert judge.calls == 1
    lines = next(iter((tmp_path / "ok").glob("*.jsonl"))).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["cost_usd"] > 0
    assert ledger.spent_today() == pytest.approx(judge.spend_usd)


def test_anthropic_judge_malformed_output_gives_no_verdicts(tmp_path: Path) -> None:
    """boundary: an unparseable judge answer is no verdicts, never an invented pass."""
    from eval.harness.judge import AnthropicJudge
    from eval.harness.ledger import HarnessLedger

    judge = AnthropicJudge(_FakeAnthropic("not json at all"), ledger=HarnessLedger(5.0, path=tmp_path / "l"))
    assert judge.judge(reply="r", evidence=[], rubric=["claim"]) == ()
