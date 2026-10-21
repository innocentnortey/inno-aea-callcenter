"""Server contract cases for CON-8 `advanceDemoClock`, owned by AEA-47 (AC-11, AEA-47-2).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, AEA-47's
tests/api/test_contract_cases_staff_clock.py drives them. Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie;
                 "role:supervisor" / "role:representative" = then act as that role (switchRole, CON-10, on the real
                 app; the local driver sets the role on its session-store double).
  setup: "reset_gate_held" = hold the app's ResetGate during the request (the middleware answers 503).
  body: {"example": <named request example>} sends that example's value read from the OpenAPI;
        {"raw": <JSON value>} sends JSON as given.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "staff_clock"
CASES: Final[dict[str, dict[str, object]]] = {
    "advanceDemoClock": {
        "public": False,
        "drives": (
            {
                "name": "next_morning",
                "status": 200,
                "preconditions": ("login", "role:supervisor"),
                "body": {"example": "NEXT_MORNING"},
            },
            {
                "name": "plus_4h",
                "status": 200,
                "preconditions": ("login", "role:supervisor"),
                "body": {"example": "PLUS_4H"},
            },
            {
                "name": "plus_1h",
                "status": 200,
                "preconditions": ("login", "role:supervisor"),
                "body": {"raw": {"step": "plus_1h"}},
            },
            {
                "name": "bad_step",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login", "role:supervisor"),
                "body": {"raw": {"step": "minus_1h"}},
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": {"example": "NEXT_MORNING"},
            },
            {
                "name": "representative",
                "status": 403,
                "code": "ROLE_NOT_ALLOWED",
                "preconditions": ("login", "role:representative"),
                "body": {"example": "NEXT_MORNING"},
            },
            {
                "name": "reset_running",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login", "role:supervisor"),
                "setup": "reset_gate_held",
                "body": {"example": "NEXT_MORNING"},
            },
        ),
    },
}
