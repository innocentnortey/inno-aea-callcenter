"""Compose AEA-57's harness parts into a run that serves the production build with require_frontend=True (AEA-58)."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Final

from meridian.config import ENV_NAMES, Settings
from meridian.domain.common import Role
from meridian.web.app import ContainerOverrides
from tests.journeys.browser.build import ProductionBuild
from tests.journeys.support.db import DbReader
from tests.journeys.support.env import journey_environ, journey_environment
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import JourneyScript, ScriptedModel, scripted_overrides
from tests.journeys.support.server import StepClock, launch_server, socket_guard
from tests.journeys.support.steps import RunNote, StepCollector

INDEX_DIR_ENV: Final = ENV_NAMES["index_dir"]  # "MERIDIAN_INDEX_DIR" (src/meridian/config.py)

OverridesFor = Callable[
    [Settings, JourneyScript, Callable[[], datetime] | None],
    tuple[ContainerOverrides, Mapping[Role, ScriptedModel]],
]


def _default_overrides(
    settings: Settings, script: JourneyScript, clock: Callable[[], datetime] | None
) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]:
    """AEA-57's scripted_overrides: the default when a run passes no builder."""
    return scripted_overrides(settings, script, wall_clock=clock)


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
    script: JourneyScript | None = None,
    with_clock: bool = False,
    overrides_for: OverridesFor | None = None,
) -> Iterator[JourneyRun]:
    """Mirrors AEA-57's open_journey; differs in the settings (the build). Run options (AEA-58-F1): a
    caller's script, the run clock, a caller's override builder."""
    with socket_guard() as guard, tap_logs() as logs, journey_environment() as base:
        environ = browser_environ(base.root, build.dist_dir)
        environ.update(environ_overrides or {})
        settings = Settings.from_env(environ)
        env = dataclasses.replace(base, settings=settings, web_dist_dir=build.dist_dir)
        script = script if script is not None else JourneyScript()
        clock = StepClock() if with_clock else None
        overrides, models = (overrides_for or _default_overrides)(settings, script, clock)
        with launch_server(settings, overrides=overrides) as server:
            run = JourneyRun(
                env=env,
                server=server,
                script=script,
                models=models,
                clock=clock,
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
