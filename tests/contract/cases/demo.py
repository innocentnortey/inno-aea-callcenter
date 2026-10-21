"""Server contract cases for CON-6..CON-9 (listDemoInbox, getStaffing, setStaffing, getDemoClock, resetDemo), owned by
AEA-43 (AC-15, AEA-43-2).

Read by AEA-59's runner (tests/contract/test_openapi_server.py) and by tests/api/test_contract_cases_demo.py.
Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie.
  setup: "reset_gate_held" = hold the app's ResetGate during the request (the middleware answers 503 for
                 listDemoInbox and setStaffing; a real ResetService raises ResetAlreadyRunning for resetDemo);
         "rate_limited" = the limiter refuses the request (local driver only in AEA-59): reads answer 429, resetDemo
                 answers the 409 throttle.
  body: {"example": <named request example>} sends that example's value read from the OpenAPI;
        {"raw": <JSON value>} sends JSON as given.
LOCAL_ONLY_DRIVES holds the RESET_FAILED drive: its setup word "reset_fails" is not in AEA-59's vocabulary yet. When
AEA-59 adds it to LOCAL_DRIVER_ONLY, the drive moves into CASES.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "demo"
CASES: Final[dict[str, dict[str, object]]] = {
    "listDemoInbox": {
        "public": False,
        "drives": (
            {"name": "messages", "status": 200, "preconditions": ("login",), "body": None},
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": None,
            },
            {
                "name": "rate_limited",
                "status": 429,
                "code": "REQUEST_RATE_LIMITED",
                "preconditions": ("login",),
                "setup": "rate_limited",
                "body": None,
            },
            {
                "name": "reset_running",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "reset_gate_held",
                "body": None,
            },
        ),
    },
    "getStaffing": {
        "public": False,
        "drives": (
            {"name": "current", "status": 200, "preconditions": ("login",), "body": None},
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": None,
            },
            {
                "name": "rate_limited",
                "status": 429,
                "code": "REQUEST_RATE_LIMITED",
                "preconditions": ("login",),
                "setup": "rate_limited",
                "body": None,
            },
        ),
    },
    "setStaffing": {
        "public": False,
        "drives": (
            {"name": "on", "status": 200, "preconditions": ("login",), "body": {"example": "ON"}},
            {"name": "off", "status": 200, "preconditions": ("login",), "body": {"example": "OFF"}},
            {
                "name": "bad_mode",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login",),
                "body": {"raw": {"mode": "maybe"}},
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": {"example": "ON"},
            },
            {
                "name": "reset_running",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "reset_gate_held",
                "body": {"example": "ON"},
            },
        ),
    },
    "getDemoClock": {
        "public": False,
        "drives": (
            {"name": "demo_clock", "status": 200, "preconditions": ("login",), "body": None},
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": None,
            },
            {
                "name": "rate_limited",
                "status": 429,
                "code": "REQUEST_RATE_LIMITED",
                "preconditions": ("login",),
                "setup": "rate_limited",
                "body": None,
            },
        ),
    },
    "resetDemo": {
        "public": False,
        "drives": (
            {"name": "confirmed", "status": 200, "preconditions": ("login",), "body": {"example": "CONFIRM"}},
            {
                "name": "not_confirmed",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login",),
                "body": {"raw": {"confirm": False}},
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": {"example": "CONFIRM"},
            },
            {
                "name": "already_running",
                "status": 409,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "reset_gate_held",
                "body": {"example": "CONFIRM"},
            },
            {
                "name": "throttled",
                "status": 409,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "rate_limited",
                "body": {"example": "CONFIRM"},
            },
        ),
    },
}
LOCAL_ONLY_DRIVES: Final[dict[str, tuple[dict[str, object], ...]]] = {
    "resetDemo": (
        {
            "name": "failed",
            "status": 500,
            "code": "RESET_FAILED",
            "preconditions": ("login",),
            "setup": "reset_fails",
            "body": {"example": "CONFIRM"},
        },
    ),
}
