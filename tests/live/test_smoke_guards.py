"""Free guards for the live smoke (AEA-61): case selection and custody, spend rules, the skip rule, the record and the
not-an-E-run check. No network and no paid call; the paid tests are in `test_live_smoke.py`.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from tests.journeys.support.env import letters
from tests.journeys.support.record import FIELDS
from tests.live.smoke import (
    CASES_DIR,
    DEV_DIR,
    HELDOUT_KEY_ROOT,
    HELDOUT_SCRIPTS_DIR,
    LIVE_LEVEL,
    LIVE_TITLE_SUFFIX,
    NO_WARRANTY,
    NOT_AN_EVAL_LINE,
    NOT_RUN_SPEND,
    REPO_ROOT,
    SCHEMA_PATH,
    SMOKE_TABLE,
    SPENT_ENV,
    SPENT_SOURCE,
    CaseCustodyError,
    CaseLauncher,
    CaseOutcome,
    CaseResult,
    NotRunCase,
    SmokeCase,
    SmokeRefused,
    SmokeRun,
    audit_opened,
    checked_dev_path,
    execute,
    live_skip_reason,
    load_dev_case,
    next_smoke_number,
    offending_paths,
    render_smoke_record,
    run_cases,
    select_smoke_set,
)
from tests.live.smoke_player import CaseEvidence, TurnExchange

EVIDENCE_FREE_CASES = 6


def _selection() -> list[SmokeCase]:
    chosen = select_smoke_set()
    assert all(isinstance(c, SmokeCase) for c in chosen)
    return [c for c in chosen if isinstance(c, SmokeCase)]


def fake_outcome(
    case: SmokeCase,
    cost_usd: float,
    *,
    notice: Mapping[str, Any] | None = None,
    failure_kind: str | None = None,
    reply: str = "",
) -> CaseOutcome:
    """A CaseOutcome with one spend row and one exchange, for tests that never reach a model."""
    body: dict[str, Any] = {"blocks": [{"type": "text", "text": reply}], "notice": notice}
    spend = {
        "id": 1,
        "turn_id": "t1",
        "run_tag": "live",
        "role": "planner",
        "provider": "anthropic",
        "model": "m",
        "attempt": 1,
        "latency_ms": 5,
        "cost_usd": cost_usd,
        "status": "ok",
        "failure_kind": failure_kind,
        "http_status": None,
        "provider_request_id": "req-1",
    }
    turn = {
        "turn_id": "t1",
        "sequence": 1,
        "run_tag": "live",
        "gate_result": "pass",
        "outcome": "answered",
        "degrade_reason": None,
        "planner_fallback_used": 0,
        "danger_raised": 0,
        "server_ms": 12,
        "model_calls": 1,
        "cost_usd": cost_usd,
        "trace_id": None,
        "trace_export": "off",
    }
    return CaseOutcome(
        case=case,
        thread_id="th-1",
        exchanges=(TurnExchange(0, "text", "submitTurn", "t1", 200, body),),
        evidence=CaseEvidence(turns=(turn,), spend=(spend,), run_tags=("live",)),
        mismatches=(),
        player_errors=(),
        header_names=frozenset(),
    )


class Recorder:
    """Counts launcher constructions (`made`) and case launches (`launches`); `plan` maps a case position to kwargs."""

    def __init__(
        self, plan: Mapping[int, Mapping[str, Any]] | None = None, default_cost: float = 0.0
    ) -> None:
        self.made = 0
        self.launches = 0
        self.plan = plan or {}
        self.default_cost = default_cost
        self.order: list[str] = []

    def make(self) -> CaseLauncher:
        self.made += 1
        return self.launch

    def launch(self, case: SmokeCase) -> CaseOutcome:
        position = len(self.order)
        self.order.append(case.case_id)
        self.launches += 1
        spec = dict(self.plan.get(position, {}))
        cost = float(spec.pop("cost_usd", self.default_cost))
        return fake_outcome(case, cost, **spec)


def _copy_dev(target: Path, case_ids: tuple[str, ...]) -> None:
    target.mkdir()
    for case_id in case_ids:
        for suffix in ("case", "key"):
            shutil.copy(DEV_DIR / f"{case_id}.{suffix}.json", target / f"{case_id}.{suffix}.json")


def test_smoke_set_is_six_dev_cases(tmp_path: Path) -> None:
    chosen = select_smoke_set()
    assert len(chosen) == EVIDENCE_FREE_CASES
    assert all(isinstance(c, SmokeCase) for c in chosen)
    expected = None
    for path in sorted(DEV_DIR.glob("*.key.json")):
        key = json.loads(path.read_text(encoding="utf-8"))
        if key["topic"] == "warranty" and key["in_scope"]:
            expected = path.name.removesuffix(".key.json")
            break
    assert expected is not None
    assert [c.case_id for c in chosen if isinstance(c, SmokeCase)] == [
        "WP-1",
        "WP-2",
        expected,
        "WP-4F",
        "DANGER",
        "WP-4",
    ]
    assert [(c.label, c.journey) for c in chosen] == [(label, j) for label, j, _ in SMOKE_TABLE]
    assert all(c.script.split == "dev" for c in chosen if isinstance(c, SmokeCase))
    print([(c.case_id, c.label) for c in chosen if isinstance(c, SmokeCase)])

    tmp_dev = tmp_path / "dev"
    _copy_dev(tmp_dev, ("WP-1",))
    script_path = tmp_dev / "WP-1.case.json"
    document = json.loads(script_path.read_text(encoding="utf-8"))
    script_path.write_text(json.dumps({**document, "clock": "2026-10-17T10:00:00-05:00"}), encoding="utf-8")
    with pytest.raises(CaseCustodyError) as clock:
        load_dev_case("WP-1", dev_dir=tmp_dev)
    assert str(clock.value) == "WP-1: clock_mismatch"
    print(f"refused: {clock.value}")

    document.pop("turns")
    script_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(CaseCustodyError) as schema:
        load_dev_case("WP-1", dev_dir=tmp_dev)
    assert str(schema.value) == "WP-1: schema_invalid"


def test_refuses_heldout_and_outside_dev(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    link_dev = tmp_path / "linked"
    link_dev.mkdir()
    (link_dev / "WP-1.case.json").symlink_to(outside)
    held = tmp_path / "held"
    _copy_dev(held, ("WP-1",))
    script_path = held / "WP-1.case.json"
    script_path.write_text(
        json.dumps({**json.loads(script_path.read_text(encoding="utf-8")), "split": "held-out"}),
        encoding="utf-8",
    )
    no_warranty = tmp_path / "no-warranty"
    _copy_dev(no_warranty, ("WP-1", "WP-2", "WP-4F", "DANGER", "WP-4"))

    with audit_opened() as opened:
        fake = "T-CALL-20260101-0001"  # invented: the held-out folder is never listed
        with pytest.raises(CaseCustodyError) as a:
            checked_dev_path(HELDOUT_SCRIPTS_DIR / f"{fake}.case.json", fake)
        assert str(a.value) == f"{fake}: outside_dev"
        with pytest.raises(CaseCustodyError) as b:
            checked_dev_path(DEV_DIR / ".." / "heldout" / "X.case.json", "X")
        assert b.value.reason == "outside_dev"
        with pytest.raises(CaseCustodyError) as c:
            load_dev_case("WP-1", dev_dir=link_dev)
        assert c.value.reason == "outside_dev"
        with pytest.raises(CaseCustodyError) as d:
            load_dev_case("WP-1", dev_dir=held)
        assert str(d.value) == "WP-1: not_dev_split"
        assert "/" not in str(d.value)
        with pytest.raises(CaseCustodyError) as e:
            load_dev_case("../heldout/X")
        assert e.value.reason == "bad_case_id"
        chosen = select_smoke_set(no_warranty)
        assert chosen[2] == NotRunCase("warranty", "J-2", None, NO_WARRANTY)
        assert all(isinstance(x, SmokeCase) for i, x in enumerate(chosen) if i != 2)
    for refusal in (a.value, b.value, c.value, d.value, e.value):
        print(f"refused: {refusal}")
    assert (
        offending_paths(
            opened,
            dev_dir=DEV_DIR,
            schema_path=SCHEMA_PATH,
            cases_dir=CASES_DIR,
            heldout_key_root=HELDOUT_KEY_ROOT,
        )
        == ()
    )
    assert not any(p == str(outside) or Path(p).is_relative_to(HELDOUT_SCRIPTS_DIR) for p in opened)


def test_preflight_refuses_over_cap() -> None:
    stub = Recorder()
    for figure in (None, "abc", "nan", "inf", "-1", "29.767"):
        environ = {} if figure is None else {SPENT_ENV: figure}
        with pytest.raises(SmokeRefused) as refusal:
            execute(environ, make_launcher=stub.make, cap_usd=30.0)
        assert stub.made == 0
        assert stub.launches == 0
        print(f"refused ({figure}): {refusal.value}")
    results = execute({SPENT_ENV: "29.766"}, make_launcher=stub.make, cap_usd=30.0)  # the boundary (PD-5)
    assert stub.made == 1
    assert len(results) == EVIDENCE_FREE_CASES


def _not_run(results: list[CaseResult]) -> list[bool]:
    return [isinstance(r.entry, NotRunCase) and r.entry.reason == NOT_RUN_SPEND for r in results]


def test_stops_between_cases_and_on_cap() -> None:
    selection = select_smoke_set()
    scenarios: list[tuple[str, float, dict[int, Mapping[str, Any]], int]] = [
        ("between cases", 29.70, {0: {"cost_usd": 0.12}}, 1),
        ("cap notice", 0.0, {1: {"notice": {"code": "SPEND_CAP_REACHED"}}}, 2),
        ("provider cap", 0.0, {0: {"failure_kind": "provider_spend_cap"}}, 1),
        ("our limit", 0.0, {0: {"failure_kind": "our_spend_limit"}}, 1),
    ]
    for name, figure, plan, launched in scenarios:
        stub = Recorder(plan)
        results = run_cases(selection, spent_today_usd=figure, cap_usd=30.0, launch=stub.launch)
        assert stub.launches == launched, name
        assert _not_run(results) == [False] * launched + [True] * (EVIDENCE_FREE_CASES - launched), name
        print(f"{name}: {launched} launched, {EVIDENCE_FREE_CASES - launched} {NOT_RUN_SPEND}")


def test_live_cases_skip_without_opt_in() -> None:
    assert "MERIDIAN_LIVE_SMOKE" in (live_skip_reason({}) or "")
    both = live_skip_reason({"MERIDIAN_LIVE_SMOKE": "1"}) or ""
    assert "ANTHROPIC_API_KEY" in both and "OPENROUTER_API_KEY" in both
    one = live_skip_reason({"MERIDIAN_LIVE_SMOKE": "1", "ANTHROPIC_API_KEY": "placeholder"}) or ""
    assert "OPENROUTER_API_KEY" in one and "ANTHROPIC_API_KEY" not in one
    assert (
        live_skip_reason({"MERIDIAN_LIVE_SMOKE": "1", "ANTHROPIC_API_KEY": "a", "OPENROUTER_API_KEY": "b"})
        is None
    )

    drop = {"MERIDIAN_LIVE_SMOKE", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", SPENT_ENV}
    env = {k: v for k, v in os.environ.items() if k not in drop}
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/live/test_live_smoke.py",
            "-m",
            "live",
            "-q",
            "-rs",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert done.returncode == 0, done.stdout[-500:]
    assert "10 skipped" in done.stdout
    assert "live smoke not requested" in done.stdout
    print("10 live cases skipped: live smoke not requested; 0 outbound connections")


def _fixture_run() -> SmokeRun:
    cases = _selection()
    passed = CaseResult(cases[0], fake_outcome(cases[0], 0.011), ())
    failed = CaseResult(
        cases[3], fake_outcome(cases[3], 0.02, reply="Done, it is moved."), ("WP-4F: no actions(moved) row",)
    )
    skipped = CaseResult(
        NotRunCase(cases[4].label, cases[4].journey, cases[4].case_id, NOT_RUN_SPEND), None, ()
    )
    return SmokeRun(
        spent_today_usd=1.5,
        cap_usd=30.0,
        results=[passed, failed, skipped],
        agent_version="x",
        role_models={"planner": "anthropic/m"},
        index_note="fixture index",
        issued_sha_before="aa",
        issued_sha_after="aa",
    )


def test_record_has_every_field(tmp_path: Path) -> None:
    run = _fixture_run()
    text = render_smoke_record(
        run, scope="live-smoke-1", revision="abc1234; agent_version x", command="cmd", forbidden=()
    )
    for name in FIELDS:
        assert f"| {name} |" in text
    for needle in (LIVE_LEVEL, NOT_AN_EVAL_LINE, SPENT_SOURCE, LIVE_TITLE_SUFFIX):
        assert needle in text
    total = sum(o.cost_usd for o in run.outcomes)
    assert f"run total cost_usd {total:.6f}" in text
    assert "WP-4F" in text and NOT_RUN_SPEND in text
    assert next_smoke_number(tmp_path) == 1
    (tmp_path / "2026-10-21-live-smoke-2.md").write_text("x", encoding="utf-8")
    assert next_smoke_number(tmp_path) == 3
    print(f"record rendered: 9 fields, run total cost_usd {total:.6f}")


def test_record_writer_redacts() -> None:
    sentinels = {
        "key": "sk-sentinel-" + letters(24),
        "secret": letters(48),
        "password": "pw" + letters(20),
        "code": f"{secrets.randbelow(900000) + 100000}",
        "phone": f"512-555-{secrets.randbelow(9000) + 1000}",
    }
    joined = " ".join(sentinels.values())
    cases = _selection()
    run = SmokeRun(
        spent_today_usd=0.0,
        cap_usd=30.0,
        results=[
            CaseResult(
                cases[0], fake_outcome(cases[0], 0.01, reply=f"reply {joined}"), (f"failed on {joined}",)
            )
        ],
    )
    text = render_smoke_record(
        run, scope="live-smoke-1", revision="r", command="c", forbidden=tuple(sentinels.values())
    )
    hits = {name: text.count(value) for name, value in sentinels.items()}
    print(f"sentinel hits: {hits}")
    assert set(hits.values()) == {0}


def test_not_an_eval_run(request: pytest.FixtureRequest) -> None:
    """AC-16 (scripted dry run): no eval header, tag live, no eval_runs row, eval/reports unchanged."""
    from tests.integration.customer_support import open_customer_run
    from tests.live.scripted_cases import scripted_turns
    from tests.live.smoke import check_case, play_case

    danger = next(c for c in _selection() if c.case_id == "DANGER")
    reports = REPO_ROOT / "eval" / "reports"
    before = sorted(os.listdir(reports)) if reports.is_dir() else []
    with open_customer_run(request) as run:
        outcome = play_case(run, danger, before_turn=scripted_turns(danger, run))
    after = sorted(os.listdir(reports)) if reports.is_dir() else []
    eval_headers = {"x-meridian-eval-key", "x-meridian-run-id", "x-meridian-run-tag"}
    assert not (outcome.header_names & eval_headers)
    assert set(outcome.evidence.run_tags) == {"live"}
    assert outcome.evidence.eval_runs == 0
    assert check_case(outcome) == []
    assert after == before
    record = render_smoke_record(
        SmokeRun(spent_today_usd=0.0, cap_usd=30.0, results=[CaseResult(danger, outcome, ())]),
        scope="live-smoke-1",
        revision="r",
        command="c",
        forbidden=(),
    )
    assert NOT_AN_EVAL_LINE in record
    print(
        f"eval headers 0; run_tags {sorted(outcome.evidence.run_tags)}; eval_runs 0; eval/reports unchanged"
    )
