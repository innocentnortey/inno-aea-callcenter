"""J-1 contract step (AEA-59 AC-16): every HTTP response J-1 receives passes assert_response_matches for its operationId.

Level when it runs: integrated with a scripted model (AEA-57's harness: real app on a disposable DB copy, scripted
adapter at the provider boundary). Blocked by AEA-57: tests/journeys/support/ (the harness and its per-response hook)
is not on main, and this file must not edit support/. When AEA-57 lands, a follow-up on AEA-59 replaces the skip with:
login, startChatSession, submitTurn, getChatThread after a refresh, and a signed-out getChatThread (401), each response
checked by the harness's own hook and listed by operationId, plus J-1's user-visible and stored-row assertions.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.journey


@pytest.mark.skip(
    reason="blocked-on AEA-57: tests/journeys/support/ (journey harness and its response hook) is not on main"
)
def test_j1_every_response_matches_contract() -> None:
    """Placeholder: see the module docstring for the steps it will assert."""
