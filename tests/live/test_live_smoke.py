"""The paid live-model smoke (AEA-61). Marked `live`; skipped unless MERIDIAN_LIVE_SMOKE=1 and both provider keys are set.

Each paid run needs Innocent's gate::paid go with the day's spend statement (LIVE_SMOKE_SPENT_TODAY_USD, D-15).
Compatibility only; not a containment, accuracy or quality result.
"""

from __future__ import annotations

import contextlib
import io
import os
import shlex
from datetime import datetime
from typing import Any, Final
from zoneinfo import ZoneInfo

import pytest

from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.policy.limits import Limits
from meridian.retrieval.settings import EMBEDDING_MODEL
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.support import record as journey_record
from tests.journeys.support.db import sha256_file
from tests.live.smoke import (
    CASES_DIR,
    DEV_DIR,
    HELDOUT_KEY_ROOT,
    LANGFUSE_NAMES,
    LIVE_LEVEL,
    NOT_AN_EVAL_LINE,
    REPO_ROOT,
    SCHEMA_PATH,
    SPENT_ENV,
    SPENT_SOURCE,
    SmokeRefused,
    SmokeRun,
    agent_version_cli,
    audit_opened,
    build_live_index,
    check_compatibility,
    compat_counts,
    execute,
    fastembed_env,
    forbidden_values,
    live_launcher,
    live_skip_reason,
    offending_paths,
    opened_counts,
    quote,
    write_smoke_record,
)

_SKIP = live_skip_reason(os.environ)
pytestmark = [pytest.mark.live, pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")]
CASE_IDS: Final = ("WP-1", "WP-2", "warranty", "WP-4F", "DANGER", "WP-4")  # param ids, in SMOKE_TABLE order
_LABELS: dict[str, str] = {}  # value -> label, for AC-15's message (labels only, never a value)


@pytest.fixture(scope="module")
def smoke_run(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> SmokeRun:
    cap = Limits().spend.daily_cap_usd
    ctx: dict[str, Any] = {}
    logs: list[str] = []
    out, err = io.StringIO(), io.StringIO()
    reports = REPO_ROOT / "eval" / "reports"
    reports_before = sorted(os.listdir(reports)) if reports.is_dir() else []
    issued_before = sha256_file(ISSUED_DB)

    def make() -> Any:
        index_dir, cache = build_live_index(tmp_path_factory.mktemp("live-index"))
        ctx["index_note"] = (
            f"{index_dir} built by meridian.retrieval.ingest.main (WF-14) with {EMBEDDING_MODEL}; "
            f"{FastembedIndex(index_dir, model_cache_dir=cache).info()}"
        )
        ctx["agent_version"] = agent_version_cli(REPO_ROOT)
        ctx["stack"].enter_context(fastembed_env(cache))
        return live_launcher(
            source=os.environ, index_dir=index_dir, agent_version=ctx["agent_version"], sink=logs, info=ctx
        )

    failure: str | None = None
    results: list[Any] = []
    with (
        contextlib.ExitStack() as stack,
        contextlib.redirect_stdout(out),
        contextlib.redirect_stderr(err),
        audit_opened() as opened,
    ):
        ctx["stack"] = stack
        try:
            results = execute(os.environ, make_launcher=make, cap_usd=cap)
        except (SmokeRefused, RuntimeError) as exc:
            failure = str(exc)
    if failure is not None:
        pytest.fail(failure, pytrace=False)

    run = SmokeRun(
        spent_today_usd=float(os.environ[SPENT_ENV]),
        cap_usd=cap,
        results=results,
        agent_version=ctx["agent_version"],
        role_models=ctx.get("role_models", {}),
        index_note=ctx["index_note"],
        issued_sha_before=issued_before,
        issued_sha_after=sha256_file(ISSUED_DB),
        opened_counts=opened_counts(opened, root=REPO_ROOT),
        offending=offending_paths(
            opened,
            dev_dir=DEV_DIR,
            schema_path=SCHEMA_PATH,
            cases_dir=CASES_DIR,
            heldout_key_root=HELDOUT_KEY_ROOT,
        ),
        eval_reports_unchanged=reports_before == (sorted(os.listdir(reports)) if reports.is_dir() else []),
        langfuse_on=all(os.environ.get(n, "").strip() for n in LANGFUSE_NAMES),
        output_text=out.getvalue() + err.getvalue() + "\n".join(logs),
    )
    labelled = forbidden_values(results, os.environ)
    _LABELS.update({value: label for label, value in labelled})
    run.forbidden = tuple(value for _, value in labelled)
    args = shlex.join(str(a) for a in request.config.invocation_params.args)
    command = f"MERIDIAN_LIVE_SMOKE=1 {SPENT_ENV}={os.environ[SPENT_ENV].strip()} uv run pytest {args}"
    run.record_path = write_smoke_record(  # written even when cases fail (PD-12)
        run,
        root=REPO_ROOT,
        day=datetime.now(ZoneInfo("America/Chicago")).date(),
        revision=journey_record.tested_revision(REPO_ROOT, run.agent_version),
        command=command,
        forbidden=run.forbidden,
    )
    for r in results:
        print(f"{r.entry.case_id or '-'} {r.entry.label}: {r.status}")
    print(f"live smoke record: {run.record_path}")
    return run


@pytest.mark.parametrize("position", range(6), ids=CASE_IDS)
def test_live_case(smoke_run: SmokeRun, position: int) -> None:
    result = smoke_run.results[position]
    detail = "\n".join(quote(f, smoke_run.forbidden) for f in result.failures) or getattr(
        result.entry, "reason", ""
    )
    assert result.status == "pass", detail


def test_live_compatibility(smoke_run: SmokeRun) -> None:
    problems = [p for o in smoke_run.outcomes for p in check_compatibility(o)]
    print(compat_counts(smoke_run.outcomes))
    assert problems == []


def test_issued_and_heldout_untouched(smoke_run: SmokeRun) -> None:
    print(dict(smoke_run.opened_counts))
    assert smoke_run.issued_sha_before == smoke_run.issued_sha_after
    assert smoke_run.offending == ()


def test_record_written(smoke_run: SmokeRun) -> None:
    assert smoke_run.record_path is not None and smoke_run.record_path.exists()
    text = smoke_run.record_path.read_text(encoding="utf-8")
    for name in journey_record.FIELDS:
        assert f"| {name} |" in text
    for needle in (LIVE_LEVEL, NOT_AN_EVAL_LINE, SPENT_SOURCE):
        assert needle in text
    assert f"run total cost_usd {sum(o.cost_usd for o in smoke_run.outcomes):.6f}" in text


def test_record_and_output_hold_no_secrets(smoke_run: SmokeRun) -> None:  # defined last: runs last
    assert smoke_run.record_path is not None
    record = smoke_run.record_path.read_text(encoding="utf-8")
    leaked = [_LABELS[v] for v in smoke_run.forbidden if v and (v in record or v in smoke_run.output_text)]
    assert leaked == [], f"values leaked, by label: {sorted(set(leaked))}"
