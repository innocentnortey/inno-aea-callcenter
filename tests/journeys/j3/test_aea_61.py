"""J-3 scripted (WP-4F), AEA-61: the live-smoke driver and its per-case checks, run on the scripted model.

A script that follows the case passes; the bad script (no move) is caught by the same assertion the paid run uses.
"""

from __future__ import annotations

import pytest

from tests.integration.customer_support import open_customer_run
from tests.live.scripted_cases import scripted_turns
from tests.live.smoke import NO_WARRANTY, NotRunCase, SmokeCase, check_case, play_case, select_smoke_set

pytestmark = pytest.mark.journey

NEEDS = ("session_service", "turn_service", "run_graph", "identity_service", "demo_clock")
OPS = ("startChatSession", "submitTurn", "listDemoInbox")


def _case(label: str) -> SmokeCase:
    entry = next(e for e in select_smoke_set() if e.label == label)
    if isinstance(entry, NotRunCase):
        pytest.skip(NO_WARRANTY)
    assert isinstance(entry, SmokeCase)
    return entry


def test_j3_follow_up_scripted(request: pytest.FixtureRequest) -> None:
    case = _case("booking with follow-up")
    with open_customer_run(request) as run:
        with run.step("J-3", "WP-4F smoke checks (scripted)", needs=NEEDS, operations=OPS):
            outcome = play_case(run, case, before_turn=scripted_turns(case, run))
            failures = check_case(outcome)
            assert failures == [], "\n".join(failures)
            print(f"WP-4F: {len(outcome.exchanges)} turns, 0 failures")


def test_j3_follow_up_without_move_caught(request: pytest.FixtureRequest) -> None:
    case = _case("booking with follow-up")
    with open_customer_run(request) as run:
        with run.step("J-3", "WP-4F skipped move is caught", needs=NEEDS, operations=OPS):
            outcome = play_case(run, case, before_turn=scripted_turns(case, run, variant="bad"))
            failures = check_case(outcome)
            caught = [f for f in failures if f.startswith("WP-4F: no actions(moved) row")]
            assert caught, failures
            print(f"caught: {caught[0]}")
