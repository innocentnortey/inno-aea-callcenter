"""AEA-24 AC-4, AC-7, AC-20, AC-21: the R-39 report, withheld runs, hand-counted measures, failure rows, redaction."""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
from pathlib import Path
from typing import Any

from eval.harness.tests.fixture_cases import (
    FEE_SENTENCE,
    ISSUED_DB,
    WP4_TEMPLATE_TEXT,
    item,
    mix_record,
    run_secrets,
    simple_case,
    simple_key,
    wp4_case,
    wp4_key,
    wp4_scripted,
    write_cases,
    write_mix,
    write_sealed_heldout,
)
from eval.harness.tests.report_support import JUDGE_OFF, hand_counted_scores, run_record
from eval.harness.tests.stub_app import (
    DEFAULT_CLOCK,
    OTHER_CLOCK,
    StubCall,
    notice_of,
    source_chip,
    text_block,
)
from eval.harness.tests.support import (
    HEX64,
    UUID4,
    assert_log_allow_listed,
    assert_targets_only_in_target_column,
    base_argv,
    make_stub,
    markdown_headings,
    measure,
    run_cli,
    validate_eval_run,
    validate_report_file,
)


def _dev_cases(tmp_path: Path) -> Path:
    root = write_cases(
        tmp_path / "cases",
        [(wp4_case(), wp4_key()), (simple_case("S-1"), simple_key("S-1", topic="booking"))],
    )
    write_mix(root)
    return root


def test_report_shape_r39(tmp_path: Path) -> None:
    """invariant: n of N per measure with min-max over 3 repeats, headline only from held-out, dev labelled dev,
    a target only in the Target column, the mix from MixRecord, and both files validate against the contracts."""
    mix = mix_record()
    run = run_secrets()
    dev_out = run_cli(
        tmp_path,
        base_argv(_dev_cases(tmp_path), tmp_path / "dev_reports", repeats=3),
        stub=make_stub(run, wp4_scripted()),
        run=run,
    )
    dev = dev_out.report()
    validate_report_file(dev)
    summary = dev["summary"]
    validate_eval_run(summary)
    assert dev["run"]["status"] == "completed"
    assert dev["run"]["repeats"] == 3
    assert summary["headline"] is None
    assert summary["split_label"] == "dev"
    assert summary["agent_version"] == dev["run"]["agent_version"]
    assert summary["run_id"] == dev["run"]["run_id"]
    assert summary["mix"] == [r.model_dump() for r in mix.splits["dev"].rows]
    assert summary["measures"]
    for m in summary["measures"]:
        assert m["denominator"] > 0
        assert m["min"] is not None
        assert m["max"] is not None
        assert m["min"] <= m["value"] <= m["max"]
    assert not any(m["id"] == "M-1" or m["id"].startswith("M-1:") for m in summary["measures"])
    markdown = dev_out.markdown()
    run_id = dev["run"]["run_id"]
    assert markdown_headings(markdown) == [
        f"# Eval run {run_id}",
        "## Run",
        "## Headline",
        "## Test-set mix",
        "## Measures (dev)",
        "## Hard gates",
        "## Failures by first failing item",
        "## DB-copy check",
        "## Dev failures (redacted)",
        "## Not measured here",
    ]
    for m in summary["measures"]:
        assert f"{m['numerator']} of {m['denominator']}" in markdown
    assert "No headline" in markdown
    assert_targets_only_in_target_column(markdown, summary)

    held_root = tmp_path / "held"
    held_root.mkdir()
    held = [
        (simple_case("H-1", split="held-out"), simple_key("H-1", topic="booking")),
        (
            simple_case("H-2", split="held-out"),
            simple_key(
                "H-2",
                topic="billing",
                must_say=[item("a sentence the stub never says " + secrets.token_hex(4))],
            ),
        ),
    ]
    write_sealed_heldout(held_root / "cases", held_root / "keys", held)
    write_mix(held_root / "cases")
    held_run = run_secrets()
    held_out = run_cli(
        held_root,
        base_argv(
            held_root / "cases",
            held_root / "reports",
            split="held-out",
            repeats=3,
            extra=["--heldout-key-dir", str(held_root / "keys")],
        ),
        stub=make_stub(held_run),
        run=held_run,
    )
    held_report = held_out.report()
    validate_report_file(held_report)
    held_summary = held_report["summary"]
    validate_eval_run(held_summary)
    assert held_summary["split_label"] == "held-out"
    assert held_summary["headline"]["id"] == "M-1"
    assert (held_summary["headline"]["numerator"], held_summary["headline"]["denominator"]) == (3, 6)
    assert held_summary["mix"] == [r.model_dump() for r in mix.splits["held-out"].rows]
    assert (
        measure(held_summary, "M-1:booking")["numerator"],
        measure(held_summary, "M-1:booking")["denominator"],
    ) == (3, 3)
    assert (
        measure(held_summary, "M-1:billing")["numerator"],
        measure(held_summary, "M-1:billing")["denominator"],
    ) == (0, 3)
    assert held_summary["topic_readiness"] == {"booking": "ready", "billing": "not ready"}
    held_md = held_out.markdown()
    assert "over 3 repeats" in held_md
    assert "## Dev failures (redacted)" not in held_md
    assert "## Measures (held-out)" in markdown_headings(held_md)
    assert_targets_only_in_target_column(held_md, held_summary)
    assert UUID4.match(held_report["run"]["run_id"])
    assert HEX64.match(held_report["run"]["harness_digest"])


def test_incomplete_run_never_reported(tmp_path: Path) -> None:
    """failure (OBS-38): a case that could not be played makes the run incomplete and withholds every number; an
    unscored key is not played and has no results."""
    run = run_secrets()
    stub = make_stub(run, clock_for_thread=lambda n: DEFAULT_CLOCK if n == 0 else OTHER_CLOCK)
    cases = write_cases(
        tmp_path / "cases",
        [
            (simple_case("A-1"), simple_key("A-1")),
            (simple_case("A-2"), simple_key("A-2")),
            (simple_case("A-3"), simple_key("A-3", unscored="needs the staff brief read")),
        ],
    )
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports"), stub=stub, run=run)
    assert out.code == 1
    report = out.report()
    assert report["run"]["status"] == "incomplete"
    assert (report["run"]["cases_expected"], report["run"]["cases_scored"]) == (2, 1)
    summary = report["summary"]
    assert summary["measures"] == []
    assert summary["headline"] is None
    assert summary["withheld"] == "incomplete"
    assert summary["unscored_cases"] == ["A-3"]
    assert "A-3" not in {r["case_id"] for r in report["results"]}
    assert "Withheld: this run is incomplete" in out.markdown()


def _by_id(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {m["id"]: m for m in summary["measures"]}


def test_e3_e4_e5_measures() -> None:
    """invariant: each measure's n of N equals the hand count; per-topic readiness is held-out only."""
    from eval.harness.report import build_scored_report

    scores = hand_counted_scores("held-out")
    run = run_record(split="held-out", repeats=2, expected=26, scored=26)
    report = build_scored_report(
        run,
        scores,
        mix=None,
        size=13,
        db=None,
        unscored=[],
        judge_summary=JUDGE_OFF,
        cost_per_conversation_usd=None,
    )
    summary = report.summary
    by_id = _by_id(summary)
    expected = {
        "M-1": (7, 14, 0.5, 0.4286, 0.5714),
        "M-1:booking": (3, 6, 0.5, 0.3333, 0.6667),
        "M-1:membership": (0, 2, 0.0, 0.0, 0.0),
        "M-1:billing": (2, 4, 0.5, 0.5, 0.5),
        "M-1:warranty": (2, 2, 1.0, 1.0, 1.0),
        "M-4": (14, 26, 0.5385, 0.5385, 0.5385),
        "M-5": (7, 26, 0.2692, 0.2308, 0.3077),
        "M-8": (4, 16, 0.25, 0.25, 0.25),
        "M-19": (8, 12, 0.6667, 0.6667, 0.6667),
        "M-20": (2, 14, 0.1429, 0.1429, 0.1429),
        "M-7": (2, 4, 0.5, 0.5, 0.5),
        "M-10": (6, 8, 0.75, 0.75, 0.75),
        "M-14": (2, 4, 0.5, 0.5, 0.5),
        "M-15": (2, 2, 1.0, 1.0, 1.0),
        "M-16": (2, 4, 0.5, 0.5, 0.5),
        "M-17": (2, 4, 0.5, 0.5, 0.5),
        "M-21": (2, 26, 0.0769, 0.0769, 0.0769),
        "E-1:hard": (22, 26, 0.8462, 0.8462, 0.8462),
    }
    for measure_id, (num, den, value, low, high) in expected.items():
        m = by_id[measure_id]
        assert (m["numerator"], m["denominator"]) == (num, den), measure_id
        assert m["value"] == value, measure_id
        assert (m["min"], m["max"]) == (low, high), measure_id
    assert [m["id"] for m in summary["measures"] if m["id"].startswith("M-1:")] == [
        "M-1:booking",
        "M-1:membership",
        "M-1:billing",
        "M-1:warranty",
    ]
    assert by_id["M-1"]["target"] == "≥ 90% per handled topic"
    assert by_id["M-5"]["target"] == "60–75% (the brief's figure)"
    assert summary["headline"]["id"] == "M-1"
    assert summary["topic_readiness"] == {
        "booking": "not ready",
        "membership": "not ready",
        "billing": "not ready",
        "warranty": "ready",
    }
    assert "M-2" not in by_id
    assert "M-9" not in by_id
    assert "M-24" not in by_id
    assert summary["dev_failures"] == []

    dev_run = run_record(split="dev", repeats=2, expected=26, scored=26)
    dev = build_scored_report(
        dev_run,
        hand_counted_scores("dev"),
        mix=None,
        size=13,
        db=None,
        unscored=[],
        judge_summary=JUDGE_OFF,
        cost_per_conversation_usd=None,
    ).summary
    dev_ids = _by_id(dev)
    assert not any(i == "M-1" or i.startswith("M-1:") for i in dev_ids)
    assert (dev_ids["M-2"]["numerator"], dev_ids["M-2"]["denominator"]) == (7, 14)
    assert dev_ids["M-2"]["target"] is None
    assert dev["headline"] is None
    assert dev["topic_readiness"] == {}
    assert {f["case_id"] for f in dev["dev_failures"]} == {"c01", "c03", "c05", "c08", "c10"}


def test_first_failure_and_categories(tmp_path: Path) -> None:
    """invariant: a case is filed under its first failing item in trace order; degraded, environment and wrong-answer
    categories are separate rows."""
    run = run_secrets()
    forbidden = "forbidden claim phrase"

    def scripted(call: StubCall) -> dict[str, Any] | None:
        if "seed:wrong" in call.text:
            return call.reply([text_block(f"This includes the {forbidden}.")])
        if "seed:order" in call.text:
            return call.reply(
                [text_block("Policy text.", sources=[source_chip("archive/warranty_terms_2023.txt")])]
            )
        if "seed:degrade" in call.text:
            return call.reply([text_block("Please try again.")], notice=notice_of("TURN_TIMEOUT"))
        if "seed:env" in call.text:
            return {"__status__": 500}
        return None

    cases = write_cases(
        tmp_path / "cases",
        [
            (simple_case("F-wrong", "seed:wrong"), simple_key("F-wrong", must_not_say=[item(forbidden)])),
            (
                simple_case("F-order", "seed:order"),
                simple_key("F-order", must_say=[item("a sentence that never appears in any reply")]),
            ),
            (simple_case("F-degrade", "seed:degrade"), simple_key("F-degrade")),
            (simple_case("F-env", "seed:env"), simple_key("F-env")),
        ],
    )
    out = run_cli(tmp_path, base_argv(cases, tmp_path / "reports"), stub=make_stub(run, scripted), run=run)
    assert out.code == 4
    report = out.report()
    assert report["run"]["status"] == "completed"
    outcomes = {r["case_id"]: r["outcome"] for r in report["results"]}
    assert outcomes["F-degrade"] == "degraded"
    assert outcomes["F-env"] == "environment_error"
    assert report["summary"]["failure_rows"] == [
        {"category": "environment", "count": 1},
        {"category": "invented_fact", "count": 1},
        {"category": "operational_degrade", "count": 1},
        {"category": "retrieval_miss", "count": 1},
    ]


def _seed_row() -> dict[str, Any]:
    con = sqlite3.connect(f"file:{ISSUED_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return dict(con.execute("SELECT * FROM customers WHERE customer_id = 'MHC-57204'").fetchone())
    finally:
        con.close()


def test_failure_examples_redacted_and_heldout_items_only(tmp_path: Path) -> None:
    """negative: dev_failures hold ids and codes only; a held-out run has item pass/fail only; logs carry ids only."""
    seed = _seed_row()
    run = run_secrets()
    cases = write_cases(tmp_path / "dev", [(wp4_case(), wp4_key())])
    out = run_cli(
        tmp_path,
        base_argv(cases, tmp_path / "dev_reports"),
        stub=make_stub(run, wp4_scripted(charged=True)),
        run=run,
    )
    report = out.report()
    failures = report["summary"]["dev_failures"]
    assert [f["case_id"] for f in failures] == ["WP-4"]
    pattern = r"first failure: [a-z_]+; failed items: ([a-z_]+\[\d+\](, [a-z_]+\[\d+\])*)?; outcome: [a-z_]+"
    assert re.fullmatch(pattern, failures[0]["redacted_summary"])
    failures_text = json.dumps(failures)
    for value in (
        seed["name"],
        seed["phone"],
        seed["service_address"],
        WP4_TEMPLATE_TEXT,
        FEE_SENTENCE,
        "charged",
    ):
        assert value not in failures_text
    for value in (seed["name"], seed["phone"], seed["service_address"]):
        assert value not in out.all_text()
    assert_log_allow_listed(out.log_lines())

    held_root = tmp_path / "held"
    held_root.mkdir()
    sealed_must_say = "sealed-expect-" + secrets.token_hex(4)
    sealed_must_not = "sealed-forbid-" + secrets.token_hex(4)
    held = [
        (
            simple_case("H-1", split="held-out"),
            simple_key("H-1", must_say=[item(sealed_must_say)], must_not_say=[item(sealed_must_not)]),
        )
    ]
    write_sealed_heldout(held_root / "cases", held_root / "keys", held)
    held_run = run_secrets()
    held_stub = make_stub(
        held_run, lambda call: call.reply([text_block(f"The reply mentions {sealed_must_not}.")])
    )
    held_out = run_cli(
        held_root,
        base_argv(
            held_root / "cases",
            held_root / "reports",
            split="held-out",
            extra=["--heldout-key-dir", str(held_root / "keys")],
        ),
        stub=held_stub,
        run=held_run,
    )
    held_report = held_out.report()
    assert held_report["summary"]["dev_failures"] == []
    assert held_report["summary"]["agent_version"] == held_report["run"]["agent_version"] != ""
    for result in held_report["results"]:
        for entry in result["items"]:
            assert set(entry) == {"item", "index", "passed", "failing_quote"}
            assert entry["failing_quote"] is None
    assert any(e["passed"] is False for r in held_report["results"] for e in r["items"]), (
        "the planted breach fails"
    )
    for value in (sealed_must_say, sealed_must_not):
        assert value not in held_out.all_text()
    assert_log_allow_listed(held_out.log_lines())
