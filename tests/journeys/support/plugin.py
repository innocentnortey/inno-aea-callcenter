"""pytest options, the two public fixtures, the step collector and the record hook (AEA-57).

Module level imports only the standard library and pytest: the root conftest loads this plugin into every pytest
session, and a broken `meridian` import must not stop unrelated tests from starting.
"""

from __future__ import annotations

import shlex
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import pytest

if TYPE_CHECKING:
    from tests.journeys.support.run import JourneyRun
    from tests.journeys.support.server import StepClock
    from tests.journeys.support.steps import StepCollector

PUBLIC_FIXTURES: tuple[str, ...] = ("journey", "journey_clock")
OPTIONS: tuple[str, ...] = ("--journey-record", "--journeys-strict")
COLLECTOR_KEY = pytest.StashKey["StepCollector"]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("journeys", "integrated journeys (AEA-57)")
    group.addoption(
        "--journey-record",
        action="store",
        default=None,
        metavar="SCOPE",
        help="write docs/testing/journeys/<date>-<SCOPE>.md for this run (integrated-journeys rule section 4)",
    )
    group.addoption(
        "--journeys-strict",
        action="store_true",
        default=False,
        help="a blocked journey step fails instead of being skipped (wave merge and pre-deploy runs)",
    )


class _JourneyRecorder:
    def __init__(self, config: pytest.Config, collector: StepCollector) -> None:
        self.config = config
        self.collector = collector

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        from tests.journeys.support.steps import JOURNEY_NODEID, TestOutcome

        if not JOURNEY_NODEID.match(report.nodeid):
            return
        if report.when == "call" or report.skipped:
            self.collector.add_test(TestOutcome(report.nodeid, report.outcome, report.duration))

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        from tests.journeys.support.record import maybe_write_record

        if hasattr(self.config, "workerinput"):
            return  # an xdist worker writes no record
        scope = self.config.getoption("--journey-record")
        command = "uv run pytest " + shlex.join(str(a) for a in self.config.invocation_params.args)
        path = maybe_write_record(
            scope,
            root=Path(self.config.rootpath),
            collector=self.collector,
            command=command,
            day=datetime.now(ZoneInfo("America/Chicago")).date(),
        )
        if path is not None:
            reporter = self.config.pluginmanager.get_plugin("terminalreporter")
            if reporter is not None:
                reporter.write_line(f"journey record: {path}")


def pytest_configure(config: pytest.Config) -> None:
    from tests.journeys.support.steps import StepCollector

    collector = StepCollector()
    config.stash[COLLECTOR_KEY] = collector
    config.pluginmanager.register(_JourneyRecorder(config, collector), "meridian-journey-recorder")


@pytest.fixture
def journey(request: pytest.FixtureRequest) -> Iterator[JourneyRun]:
    """A running real app on a disposable DB copy with the scripted model (see support/README.md)."""
    from tests.journeys.support.run import open_journey

    with open_journey(
        collector=request.config.stash[COLLECTOR_KEY],
        strict=bool(request.config.getoption("--journeys-strict")),
        with_clock="journey_clock" in request.fixturenames,
        nodeid=request.node.nodeid,
    ) as run:
        yield run


@pytest.fixture
def journey_clock(journey: JourneyRun) -> StepClock:
    """The run's wall clock; .advance(seconds) moves get_wall_clock() forward, the demo clock stays (D-13)."""
    assert journey.clock is not None
    return journey.clock
