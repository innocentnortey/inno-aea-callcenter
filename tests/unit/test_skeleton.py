"""AEA-01 AC-1, AC-9 (markers) and S-5: the skeleton imports and the pytest wiring is in place."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

PACKAGES = (
    "meridian",
    "meridian.domain",
    "meridian.policy",
    "meridian.privacy",
    "meridian.ports",
    "meridian.gates",
    "meridian.adapters",
    "meridian.adapters.sqlite",
    "meridian.adapters.models",
    "meridian.retrieval",
    "meridian.services",
    "meridian.agent",
    "meridian.agent.tools",
    "meridian.agent.nodes",
    "meridian.agent.specialists",
    "meridian.agent.prompts",
    "meridian.web",
    "meridian.web.schemas",
    "meridian.web.routes",
    "eval.harness",
)
ROOT = Path(__file__).resolve().parents[2]


def test_every_planned_package_imports() -> None:
    for name in (*PACKAGES, *(f"tests.journeys.j{i}" for i in range(1, 11))):
        importlib.import_module(name)
    print(len(PACKAGES), "packages:", ", ".join(PACKAGES))


def test_journey_and_live_markers_registered(pytestconfig: pytest.Config) -> None:
    markers = pytestconfig.getini("markers")
    assert sum(m.startswith("journey:") for m in markers) == 1
    assert sum(m.startswith("live:") for m in markers) == 1


@pytest.mark.skipif((ROOT / "tests/journeys/support/plugin.py").exists(), reason="AEA-57 plugin present")
def test_optional_journey_plugin_is_absent_today() -> None:
    from tests import conftest

    assert conftest.pytest_plugins == []
