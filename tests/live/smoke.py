"""The live-smoke facade: re-exports the public API of the smoke modules and owns `execute()`, the live index, the live
environment and the live launcher (AEA-61; integrated-journeys rule 4).

Compatibility only: nothing here is an E-run, and nothing here writes under `eval/reports/`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final

from meridian.config import Settings
from meridian.policy.limits import Limits
from meridian.retrieval.ingest import main as ingest_main
from meridian.retrieval.settings import EMBEDDING_MODEL
from scripts.agent_version import build_sha_from_git
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.support.db import DbReader, sha256_file
from tests.journeys.support.env import REPO_ROOT, JourneyEnv, journey_environ
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import JourneyScript
from tests.journeys.support.server import SocketGuard, launch_server
from tests.journeys.support.steps import StepCollector
from tests.live.smoke_audit import audit_opened, offending_paths, opened_counts
from tests.live.smoke_cases import (
    CASES_DIR,
    DEV_DIR,
    HELDOUT_KEY_ROOT,
    HELDOUT_SCRIPTS_DIR,
    NO_WARRANTY,
    SCHEMA_PATH,
    SMOKE_TABLE,
    CaseCustodyError,
    NotRunCase,
    SmokeCase,
    checked_dev_path,
    first_warranty_case,
    load_dev_case,
    select_smoke_set,
)
from tests.live.smoke_checks import (
    CaseResult,
    check_case,
    check_compatibility,
    compat_counts,
    visible_text,
)
from tests.live.smoke_player import CaseOutcome, SignalTap, play_case, signal_tap
from tests.live.smoke_record import (
    LIVE_LEVEL,
    LIVE_TITLE_SUFFIX,
    NOT_AN_EVAL_LINE,
    SPENT_SOURCE,
    SmokeRun,
    next_smoke_number,
    quote,
    render_smoke_record,
    scrub,
    write_smoke_record,
)
from tests.live.smoke_spend import (
    NOT_RUN_SPEND,
    PER_CASE_ESTIMATE_USD,
    RUN_ESTIMATE_USD,
    SPENT_ENV,
    SmokeRefused,
    micros,
    preflight,
    should_stop,
)
from tests.unit.adapters.test_retrieval_fastembed import KB_DIR, TRANSCRIPTIONS_DIR, cached_model_dir

CaseLauncher = Callable[[SmokeCase], CaseOutcome]
LIVE_INDEX_MISSING: Final = (
    "bge-small-en-v1.5 is not cached locally (var/fastembed); the live smoke needs the built index"
)
LANGFUSE_NAMES: Final = (
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASE_URL",
    "LANGFUSE_PROJECT_ID",
)
PROVIDER_KEY_NAMES: Final = ("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY")


def live_skip_reason(environ: Mapping[str, str]) -> str | None:
    """Why the paid tests skip, or None when the run is opted in. Names only, never a value."""
    if environ.get("MERIDIAN_LIVE_SMOKE") != "1":
        return "live smoke not requested: set MERIDIAN_LIVE_SMOKE=1 after Innocent's gate::paid go"
    missing = [n for n in PROVIDER_KEY_NAMES if not environ.get(n, "").strip()]
    if missing:
        return f"live smoke needs {', '.join(missing)} in the environment"
    return None


def run_cases(
    selection: Sequence[SmokeCase | NotRunCase],
    *,
    spent_today_usd: float,
    cap_usd: float,
    launch: CaseLauncher,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    total = 0.0
    stopped = False
    left = sum(1 for e in selection if isinstance(e, SmokeCase))
    for entry in selection:
        if isinstance(entry, NotRunCase):
            results.append(CaseResult(entry, None, ()))
            continue
        if stopped or should_stop(total, left, spent_today_usd=spent_today_usd, cap_usd=cap_usd):
            stopped = True
            skipped = NotRunCase(entry.label, entry.journey, entry.case_id, NOT_RUN_SPEND)
            results.append(CaseResult(skipped, None, ()))
            left -= 1
            continue
        outcome = launch(entry)
        results.append(CaseResult(entry, outcome, tuple(check_case(outcome))))
        total += outcome.cost_usd
        stopped = outcome.spend_cap_hit
        left -= 1
    return results


def execute(
    environ: Mapping[str, str],
    *,
    make_launcher: Callable[[], CaseLauncher],
    cap_usd: float | None = None,
    dev_dir: Path = DEV_DIR,
) -> list[CaseResult]:
    cap = Limits().spend.daily_cap_usd if cap_usd is None else cap_usd
    figure = preflight(environ, cap_usd=cap)  # a refusal raises before anything is built (PD-14)
    selection = select_smoke_set(dev_dir)
    launch = make_launcher()
    return run_cases(selection, spent_today_usd=figure, cap_usd=cap, launch=launch)


def build_live_index(out_parent: Path) -> tuple[Path, Path]:
    """The WF-14 CLI entry point with the cached embedder; it downloads nothing."""
    cache = cached_model_dir()
    if cache is None:
        raise RuntimeError(LIVE_INDEX_MISSING)
    import numpy as np
    from fastembed import TextEmbedding

    from meridian.adapters.retrieval_fastembed import FastembedIndex

    model = TextEmbedding(EMBEDDING_MODEL, cache_dir=str(cache), local_files_only=True)

    def embed(texts: Sequence[str]) -> Any:
        return np.asarray([np.asarray(v) for v in model.embed(list(texts))], dtype=np.float32)

    out = out_parent / "index"
    rc = ingest_main(
        ["--kb-dir", str(KB_DIR), "--transcriptions-dir", str(TRANSCRIPTIONS_DIR), "--out-dir", str(out)],
        embed=embed,
    )
    if rc != 0:
        raise RuntimeError(f"index build failed (ingest exit {rc})")
    readiness = FastembedIndex(out, model_cache_dir=cache).readiness()
    if not readiness.ok:
        raise RuntimeError(f"index not ready: {readiness.reasons}")
    return out, cache


@contextmanager
def fastembed_env(cache: Path) -> Iterator[None]:
    names = {"FASTEMBED_CACHE_PATH": str(cache), "HF_HUB_OFFLINE": "1"}
    previous = {n: os.environ.get(n) for n in names}
    os.environ.update(names)
    try:
        yield
    finally:
        for name, old in previous.items():
            if old is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old


def live_environ(
    root: Path, *, source: Mapping[str, str], index_dir: Path, agent_version: str
) -> dict[str, str]:
    environ = journey_environ(root)
    for name in PROVIDER_KEY_NAMES:
        environ[name] = source[name]
    environ["MERIDIAN_INDEX_DIR"] = str(index_dir)
    environ["MERIDIAN_AGENT_VERSION"] = agent_version
    if all(source.get(n, "").strip() for n in LANGFUSE_NAMES):
        for name in LANGFUSE_NAMES:
            environ[name] = source[name]
    assert "MERIDIAN_EVAL_KEY" not in environ
    return environ


def agent_version_cli(root: Path) -> str:
    env = {**os.environ, "RAILWAY_GIT_COMMIT_SHA": build_sha_from_git(root)}
    done = subprocess.run(
        [sys.executable, "-m", "scripts.agent_version"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    version = done.stdout.strip()
    if not version:
        raise RuntimeError("scripts.agent_version printed nothing")
    return version


def live_launcher(
    *,
    source: Mapping[str, str],
    index_dir: Path,
    agent_version: str,
    sink: list[str],
    info: dict[str, Any],
) -> CaseLauncher:
    def launch(case: SmokeCase) -> CaseOutcome:
        root = Path(tempfile.mkdtemp(prefix="meridian-live-smoke-"))
        try:
            (root / "data").mkdir()
            (root / "no-dist").mkdir()
            settings = Settings.from_env(
                live_environ(root, source=source, index_dir=index_dir, agent_version=agent_version)
            )
            info.setdefault(
                "role_models",
                {role: f"{v['provider']}/{v['model']}" for role, v in settings.role_model_map().items()},
            )
            env = JourneyEnv(
                root=root,
                data_dir=root / "data",
                web_dist_dir=root / "no-dist",
                index_dir=index_dir,
                settings=settings,
                issued_sha256_before=sha256_file(ISSUED_DB),
            )
            with tap_logs() as logs, launch_server(settings, overrides=None) as server:
                run = JourneyRun(
                    env=env,
                    server=server,
                    script=JourneyScript(),
                    models={},
                    clock=None,
                    db=DbReader(env.db_path),
                    logs=logs,
                    guard=SocketGuard(),
                    collector=StepCollector(),
                    strict=False,
                    nodeid=f"tests/live::{case.case_id}",
                )
                try:
                    outcome = play_case(run, case)  # every read happens before the server stops
                finally:
                    run.close_clients()
                    sink.append(logs.all_text())
            return outcome
        finally:
            shutil.rmtree(root, ignore_errors=True)

    return launch


def forbidden_values(
    results: Sequence[CaseResult], environ: Mapping[str, str]
) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for name in (*PROVIDER_KEY_NAMES, "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"):
        value = environ.get(name, "").strip()
        if value:
            pairs.append((name, value))
    for r in results:
        if r.outcome is not None:
            pairs.extend(r.outcome.secrets.values)
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for label, value in pairs:
        if value and value not in seen:
            seen.add(value)
            unique.append((label, value))
    return tuple(unique)


__all__ = [
    "CASES_DIR",
    "DEV_DIR",
    "HELDOUT_KEY_ROOT",
    "HELDOUT_SCRIPTS_DIR",
    "LANGFUSE_NAMES",
    "LIVE_INDEX_MISSING",
    "LIVE_LEVEL",
    "LIVE_TITLE_SUFFIX",
    "NOT_AN_EVAL_LINE",
    "NOT_RUN_SPEND",
    "NO_WARRANTY",
    "PER_CASE_ESTIMATE_USD",
    "REPO_ROOT",
    "RUN_ESTIMATE_USD",
    "SCHEMA_PATH",
    "SMOKE_TABLE",
    "SPENT_ENV",
    "SPENT_SOURCE",
    "CaseCustodyError",
    "CaseLauncher",
    "CaseOutcome",
    "CaseResult",
    "NotRunCase",
    "SignalTap",
    "SmokeCase",
    "SmokeRefused",
    "SmokeRun",
    "agent_version_cli",
    "audit_opened",
    "build_live_index",
    "check_case",
    "check_compatibility",
    "checked_dev_path",
    "compat_counts",
    "execute",
    "fastembed_env",
    "first_warranty_case",
    "forbidden_values",
    "live_environ",
    "live_launcher",
    "live_skip_reason",
    "load_dev_case",
    "micros",
    "next_smoke_number",
    "offending_paths",
    "opened_counts",
    "play_case",
    "preflight",
    "quote",
    "render_smoke_record",
    "run_cases",
    "scrub",
    "select_smoke_set",
    "should_stop",
    "signal_tap",
    "visible_text",
    "write_smoke_record",
]
