"""Compose AEA-57's harness parts into a run that serves the production build with require_frontend=True (AEA-58)."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from meridian.config import Settings
from tests.journeys.browser.build import ProductionBuild
from tests.journeys.support.db import DbReader
from tests.journeys.support.env import journey_environ, journey_environment
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import JourneyScript, scripted_overrides
from tests.journeys.support.server import launch_server, socket_guard
from tests.journeys.support.steps import RunNote, StepCollector


def browser_environ(root: Path, dist_dir: Path) -> dict[str, str]:
    """AEA-57's journey_environ(root) plus the build: MERIDIAN_WEB_DIST_DIR and MERIDIAN_REQUIRE_FRONTEND=true."""
    environ = journey_environ(root)
    environ["MERIDIAN_WEB_DIST_DIR"] = str(dist_dir)
    environ["MERIDIAN_REQUIRE_FRONTEND"] = "true"
    return environ


@contextmanager
def open_browser_journey(
    *,
    collector: StepCollector,
    strict: bool,
    nodeid: str,
    build: ProductionBuild,
    environ_overrides: dict[str, str] | None = None,
) -> Iterator[JourneyRun]:
    """Mirrors AEA-57's open_journey; differs only in the settings (the build) and the absent wall clock."""
    with socket_guard() as guard, tap_logs() as logs, journey_environment() as base:
        environ = browser_environ(base.root, build.dist_dir)
        environ.update(environ_overrides or {})
        settings = Settings.from_env(environ)
        env = dataclasses.replace(base, settings=settings, web_dist_dir=build.dist_dir)
        script = JourneyScript()
        overrides, models = scripted_overrides(settings, script, wall_clock=None)
        with launch_server(settings, overrides=overrides) as server:
            run = JourneyRun(
                env=env,
                server=server,
                script=script,
                models=models,
                clock=None,
                db=DbReader(env.db_path),
                logs=logs,
                guard=guard,
                collector=collector,
                strict=strict,
                nodeid=nodeid,
            )
            try:
                yield run
            finally:
                run.close_clients()
        spend = DbReader(env.db_path).one(
            "SELECT COUNT(*) AS n, COALESCE(SUM(cost_usd), 0.0) AS total FROM spend_ledger"
        )
        collector.add_note(
            RunNote(
                host=server.host,
                port=server.port,
                agent_version=settings.agent_version,
                models={r.value: f"{m.provider}/{m.model}" for r, m in models.items()},
                issued_sha256=env.issued_sha256_before,
                spend_rows=int(spend["n"]),
                spend_total_usd=float(spend["total"]),
                outbound_blocked=len(guard.blocked),
            )
        )
    if guard.blocked:
        raise AssertionError(
            f"journey socket guard refused {len(guard.blocked)} non-loopback connection(s): {guard.blocked}"
        )
