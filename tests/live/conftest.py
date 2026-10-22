"""tests/live: no network unless the paid run is opted in (AEA-61; integrated-journeys rule 4)."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from tests.journeys.support.server import socket_guard


@pytest.fixture(scope="package", autouse=True)
def no_network() -> Iterator[None]:
    from tests.live.smoke import live_skip_reason

    if live_skip_reason(os.environ) is None:  # opted in with both keys: the paid run needs the network
        yield
        return
    with socket_guard() as guard:
        yield
    assert not guard.blocked, f"tests/live opened {len(guard.blocked)} non-loopback connection(s)"
