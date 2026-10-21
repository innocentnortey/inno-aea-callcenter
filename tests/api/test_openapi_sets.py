"""AEA-23 AC-12, AC-21 and PA-2: the constants in web/middleware.py are checked against the signed OpenAPI, so a
contract change breaks the build, not production.

Failure mode guarded: invariant (the rate-limit set, the reset-503 set and the operation table equal the contract's).
"""

from __future__ import annotations

from meridian.web.middleware import OPERATIONS_BY_ROUTE, RATE_LIMITED_READ_OPERATIONS, RESET_503_OPERATIONS
from tests.api.openapi_check import load_contract, operations_documenting, operations_documenting_code

SIX_READS = frozenset(
    {"startChatSession", "listDemoInbox", "getStaffing", "getDemoClock", "getMonitoring", "getLatestEval"}
)
EIGHT_RESET = frozenset(
    {
        "startChatSession",
        "submitTurn",
        "listDemoInbox",
        "setStaffing",
        "advanceDemoClock",
        "switchRole",
        "getMonitoring",
        "getLatestEval",
    }
)


def test_rate_limit_set_matches_openapi() -> None:
    """invariant (AC-12): the six rate-limited reads are the operations documenting 429, minus login (WEB-3)."""
    documented = operations_documenting("429") - {"login"}
    print(f"429 set: {sorted(documented)}")
    assert RATE_LIMITED_READ_OPERATIONS == documented
    assert RATE_LIMITED_READ_OPERATIONS == SIX_READS


def test_reset_503_set_matches_openapi() -> None:
    """invariant (AC-21): the eight reset-refused operations are those documenting 503 RESET_IN_PROGRESS."""
    documented = operations_documenting_code("503", "RESET_IN_PROGRESS")
    print(f"503 RESET_IN_PROGRESS set: {sorted(documented)}")
    assert RESET_503_OPERATIONS == documented
    assert RESET_503_OPERATIONS == EIGHT_RESET
    assert "requestPerson" not in RESET_503_OPERATIONS  # its 503 is HANDOFF_FAILED, not a reset


def test_operation_table_matches_openapi() -> None:
    """invariant (PA-2): OPERATIONS_BY_ROUTE is exactly the contract's (method, path) to operationId map."""
    contract = load_contract()
    expected = {
        (spec.method.upper(), spec.path_template): operation_id
        for operation_id, spec in contract.operations.items()
    }
    assert dict(OPERATIONS_BY_ROUTE) == expected
    assert len(OPERATIONS_BY_ROUTE) == 30
