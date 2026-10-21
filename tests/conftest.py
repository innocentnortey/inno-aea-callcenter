"""Suite-wide pytest configuration (AEA-01). Shared fixtures only; each ticket keeps its own fixtures in its own test
folder (slice plan §3). No fixtures are shared yet."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tests.journeys.affected import journey_files

# AEA-57 creates tests/journeys/support/plugin.py (its options and fixtures); it is loaded only once it exists.
_OPTIONAL_PLUGINS = ("tests.journeys.support.plugin",)


def _module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


pytest_plugins = [name for name in _OPTIONAL_PLUGINS if _module_exists(name)]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """`pytest -m journey` before any journey exists is not a failure (AEA-01 AC-9). Once a journey file exists,
    an empty journey selection is a real error again."""
    markexpr = str(session.config.getoption("markexpr") or "")
    if (
        exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED
        and markexpr.split()[:1] == ["journey"]
        and not journey_files(Path(session.config.rootpath))
    ):
        session.exitstatus = pytest.ExitCode.OK
