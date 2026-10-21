"""Harness tests: the network block is on for every test (AC-13: no network, no paid call by default)."""

from __future__ import annotations

import pytest

from eval.harness.tests.netblock import block_network

__all__ = ["block_network"]


@pytest.fixture(autouse=True)
def _network_blocked(block_network: list[object]) -> None:
    return None
