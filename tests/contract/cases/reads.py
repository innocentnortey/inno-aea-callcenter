"""Server contract cases for CON-18 `getOwnerMetrics`, CON-19 `getMonitoring`, CON-20 `getLatestEval`, owned by AEA-48
(AC-11, AEA-48-2).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, AEA-48's
tests/api/test_contract_cases_reads.py drives them. Until AEA-53 binds the reader, a runner on the real app skips the
200 cases as `not bound: get_metrics_reads`. Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie (the session starts as customer);
                 "role:<owner|supervisor|representative|customer>" = then act as that role (switchRole, CON-10, on the
                 real app; the local driver sets the role on its session-store double).
  setup: "reset_gate_held" = hold the app's ResetGate during the request (the middleware answers 503);
         "rate_limited" = the rate limiter refuses the SESSION and IP read buckets for the request (429).
  reader_example: the OpenAPI 200 example the local driver's MetricsReads double returns; a runner with the real reader
                  ignores it.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "reads"
CASES: Final[dict[str, dict[str, object]]] = {
    "getOwnerMetrics": {
        "public": False,
        "drives": (
            {
                "name": "owner_seeded",
                "status": 200,
                "preconditions": ("login", "role:owner"),
                "reader_example": "SEEDED",
            },
            {
                "name": "supervisor_empty",
                "status": 200,
                "preconditions": ("login", "role:supervisor"),
                "reader_example": "EMPTY",
            },
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": ()},
            {
                "name": "representative",
                "status": 403,
                "code": "ROLE_NOT_ALLOWED",
                "preconditions": ("login", "role:representative"),
            },
        ),
    },
    "getMonitoring": {
        "public": False,
        "drives": (
            {
                "name": "customer_default",
                "status": 200,
                "preconditions": ("login",),
                "reader_example": "DEFAULT",
            },
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": ()},
            {
                "name": "rate_limited",
                "status": 429,
                "code": "REQUEST_RATE_LIMITED",
                "preconditions": ("login",),
                "setup": "rate_limited",
            },
            {
                "name": "reset_running",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "reset_gate_held",
            },
        ),
    },
    "getLatestEval": {
        "public": False,
        "drives": (
            {
                "name": "owner_both_splits",
                "status": 200,
                "preconditions": ("login", "role:owner"),
                "reader_example": "BOTH_SPLITS",
            },
            {
                "name": "customer_no_run",
                "status": 200,
                "preconditions": ("login",),
                "reader_example": "NO_RUN",
            },
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": ()},
            {
                "name": "rate_limited",
                "status": 429,
                "code": "REQUEST_RATE_LIMITED",
                "preconditions": ("login",),
                "setup": "rate_limited",
            },
            {
                "name": "reset_running",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "reset_gate_held",
            },
        ),
    },
}
