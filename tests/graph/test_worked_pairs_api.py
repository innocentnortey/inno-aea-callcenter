"""AEA-51 worked pairs through the HTTP API on the real graph (pass 1: the greeting and demo date, AC-5).

The WP-1..WP-8 drivers and their tests arrive in pass 2, once the act node's cards (AEA-21b) are on main.
"""

from __future__ import annotations

import pytest

from meridian.adapters.sqlite.repos_cases_state import DEMO_START
from meridian.policy.texts import TextId, render
from meridian.services.demo import format_clock
from tests.integration.customer_api import login, open_chat
from tests.integration.customer_support import RunOptions, open_customer_run


def test_greeting_and_demo_date(request: pytest.FixtureRequest) -> None:
    """AC-5: CON-1 answers the fixed greeting (R-1) and the demo date label, with no model call."""
    with open_customer_run(request, RunOptions()) as run:
        opened = open_chat(run, login(run)).opened
        greeting = opened["greeting"]
        assert greeting["type"] == "text"
        assert greeting["text"] == render(TextId.GREETING)
        assert opened["demo_clock"]["label"] == format_clock(DEMO_START)[0]
        assert run.script.calls == ()
