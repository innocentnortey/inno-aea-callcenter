"""The browser fixtures (production_build, journey_chrome, browser_journey, browser_journey_factory) and the two
session hooks (AEA-58, AEA-58-F1). Loaded with
`pytest_plugins = ("tests.journeys.browser.plugin",)` by each browser test module.

Module level imports only the standard library, pytest and TYPE_CHECKING names, as AEA-57's plugin does.
"""

from __future__ import annotations

import shlex
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Browser

    from tests.journeys.browser.build import ProductionBuild
    from tests.journeys.browser.pages import BrowserRun
    from tests.journeys.browser.record import BrowserSession
    from tests.journeys.browser.server import OverridesFor
    from tests.journeys.support.scripted_model import JourneyScript


def _session(config: pytest.Config) -> BrowserSession:
    from tests.journeys.browser.record import BROWSER_KEY, BrowserSession

    return config.stash.setdefault(BROWSER_KEY, BrowserSession())


def _write(config: pytest.Config, line: str) -> None:
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(line)


def _today() -> Any:
    return datetime.now(ZoneInfo("America/Chicago")).date()


@pytest.fixture(scope="session")
def production_build(request: pytest.FixtureRequest) -> ProductionBuild:
    from tests.journeys.browser.build import check_production_build, dist_dir_from_env

    build = check_production_build(dist_dir_from_env())
    _session(request.config).build = build
    _write(request.config, f"production build: {build.dist_dir} index.html sha256 {build.index_sha256}")
    _write(request.config, build.check_line)
    return build


@pytest.fixture(scope="module")
def journey_chrome(
    request: pytest.FixtureRequest, browser_type_launch_args: dict[str, Any]
) -> Iterator[Browser]:
    """Module scope on purpose: a started sync Playwright leaves an event loop running in the main thread, which
    breaks `asyncio.run` in every journey that runs after it (found in the affected-journeys run)."""
    from playwright.sync_api import sync_playwright

    from tests.journeys.browser.build import launch_chrome

    pw = sync_playwright().start()
    try:
        browser, channel = launch_chrome(pw, browser_type_launch_args)
        session = _session(request.config)
        session.channel = channel
        session.chrome_version = browser.version
        _write(request.config, f"browser: Chrome channel {channel} version {browser.version}")
        try:
            yield browser
        finally:
            browser.close()
    finally:
        pw.stop()


@contextmanager
def _browser_run(
    request: pytest.FixtureRequest,
    browser: Browser,
    build: ProductionBuild,
    tmp_path: Path,
    *,
    environ_overrides: dict[str, str] | None = None,
    script: JourneyScript | None = None,
    with_clock: bool = False,
    overrides_for: OverridesFor | None = None,
) -> Iterator[BrowserRun]:
    """One composition for both browser fixtures: collector, strict flag, screenshots folder, BrowserRun, close()."""
    from tests.journeys.browser.pages import BrowserRun
    from tests.journeys.browser.server import open_browser_journey
    from tests.journeys.support.env import REPO_ROOT
    from tests.journeys.support.plugin import COLLECTOR_KEY
    from tests.journeys.support.record import record_path

    collector = request.config.stash[COLLECTOR_KEY]
    strict = bool(request.config.getoption("--journeys-strict"))
    session = _session(request.config)
    scope = request.config.getoption("--journey-record")
    shots = record_path(REPO_ROOT, scope, _today()).with_suffix("") if scope else tmp_path / "shots"
    with open_browser_journey(
        collector=collector,
        strict=strict,
        nodeid=request.node.nodeid,
        build=build,
        environ_overrides=environ_overrides,
        script=script,
        with_clock=with_clock,
        overrides_for=overrides_for,
    ) as run:
        brun = BrowserRun(
            run=run,
            browser=browser,
            channel=str(session.channel),
            build=build,
            shots_dir=shots,
            session=session,
            test_name=request.node.originalname,
        )
        try:
            yield brun
        finally:
            brun.close()


@pytest.fixture
def browser_journey(
    request: pytest.FixtureRequest, journey_chrome: Browser, production_build: ProductionBuild, tmp_path: Path
) -> Iterator[BrowserRun]:
    with _browser_run(request, journey_chrome, production_build, tmp_path) as brun:
        yield brun


@pytest.fixture
def browser_journey_factory(
    request: pytest.FixtureRequest, journey_chrome: Browser, production_build: ProductionBuild, tmp_path: Path
) -> Callable[..., AbstractContextManager[BrowserRun]]:
    """Runs with options (AEA-58-F1 A-1): `with browser_journey_factory(index_dir=..., with_clock=True,
    script=..., overrides_for=...) as brun:`. Each call opens one run; close it with the `with` block."""

    def open_run(
        *,
        index_dir: Path | None = None,
        with_clock: bool = False,
        script: JourneyScript | None = None,
        overrides_for: OverridesFor | None = None,
    ) -> AbstractContextManager[BrowserRun]:
        from tests.journeys.browser.server import INDEX_DIR_ENV

        environ = {INDEX_DIR_ENV: str(index_dir)} if index_dir is not None else None
        return _browser_run(
            request,
            journey_chrome,
            production_build,
            tmp_path,
            environ_overrides=environ,
            script=script,
            with_clock=with_clock,
            overrides_for=overrides_for,
        )

    return open_run


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    from tests.journeys.browser.record import BROWSER_KEY, browser_record_values
    from tests.journeys.support.plugin import COLLECTOR_KEY
    from tests.journeys.support.record import RecordData, build_record_data, record_path, render_record

    config = session.config
    if hasattr(config, "workerinput"):
        return
    data = config.stash.get(BROWSER_KEY, None)
    if data is None or data.build is None:
        return
    _write(config, data.summary_line())
    scope = config.getoption("--journey-record")
    if scope is None:
        return
    collector = config.stash[COLLECTOR_KEY]
    root = Path(config.rootpath)
    command = "uv run pytest " + shlex.join(str(a) for a in config.invocation_params.args)
    base = build_record_data(scope=scope, collector=collector, root=root, command=command)
    values = browser_record_values(base, data, collector=collector, root=root)
    path = record_path(root, scope, _today())
    path.write_text(render_record(RecordData(scope=scope, values=values)), encoding="utf-8")
