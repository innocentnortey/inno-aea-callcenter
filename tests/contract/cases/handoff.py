"""Server contract cases for CON-4 `requestPerson` and CON-5 `saveFollowUp`, owned by AEA-42 (AC-21, AEA-42-2).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, AEA-42's
tests/api/test_contract_cases_handoff.py drives them. Vocabulary (closed):
  preconditions: "login" = a customer cookie; "thread" = a live conversation of this session; "open_case" = a case on it,
    created by a first BUTTON press; "verified" = identity verified as MHC-10002 with a `verified` action; "ended" = the
    path id is this session's tombstone (reason demo_reset); "unknown" = the path id is a fresh UUID.
  setup: "handoff_fails" = the HandoffService raises on open.
  body: {"example": <named request example>}, {"example": "BUTTON", "turn_id": "new"} (the example with a fresh UUID),
    {"raw": <JSON value>}, or None.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "handoff"
CASES: Final[dict[str, dict[str, object]]] = {
    "requestPerson": {
        "public": False,
        "drives": (
            {
                "name": "case_created",
                "status": 200,
                "preconditions": ("login", "thread"),
                "body": {"example": "BUTTON"},
            },
            {
                "name": "already_open",
                "status": 200,
                "preconditions": ("login", "thread", "open_case"),
                "body": {"example": "BUTTON", "turn_id": "new"},
            },
            {
                "name": "bad_turn_id",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login", "thread"),
                "body": {"raw": {"turn_id": "not-a-uuid"}},
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": ("thread",),
                "body": {"example": "BUTTON"},
            },
            {
                "name": "not_found",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login", "unknown"),
                "body": {"example": "BUTTON"},
            },
            {
                "name": "ended",
                "status": 410,
                "code": "SESSION_ENDED",
                "preconditions": ("login", "ended"),
                "body": {"example": "BUTTON"},
            },
            {
                "name": "handoff_failed",
                "status": 503,
                "code": "HANDOFF_FAILED",
                "preconditions": ("login", "thread"),
                "setup": "handoff_fails",
                "body": {"example": "BUTTON"},
            },
        ),
    },
    "saveFollowUp": {
        "public": False,
        "drives": (
            {
                "name": "phone_mornings",
                "status": 200,
                "preconditions": ("login", "thread", "verified", "open_case"),
                "body": {"example": "PHONE_MORNINGS"},
            },
            {
                "name": "email_general",
                "status": 200,
                "preconditions": ("login", "thread", "open_case"),
                "body": {"example": "EMAIL_GENERAL"},
            },
            {
                "name": "bad_window",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login", "thread", "open_case"),
                "body": {"raw": {"channel": "phone", "destination": "general", "window": "evening"}},
            },
            {
                "name": "missing_channel",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login", "thread", "open_case"),
                "body": {"raw": {"destination": "general", "window": "any"}},
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": ("thread",),
                "body": {"example": "EMAIL_GENERAL"},
            },
            {
                "name": "not_found",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login", "unknown"),
                "body": {"example": "EMAIL_GENERAL"},
            },
            {
                "name": "no_open_case",
                "status": 409,
                "code": "NOT_ALLOWED_IN_STATE",
                "preconditions": ("login", "thread"),
                "body": {"example": "EMAIL_GENERAL"},
            },
            {
                "name": "not_verified",
                "status": 409,
                "code": "NOT_ALLOWED_IN_STATE",
                "preconditions": ("login", "thread", "open_case"),
                "body": {"example": "PHONE_MORNINGS"},
            },
            {
                "name": "ended",
                "status": 410,
                "code": "SESSION_ENDED",
                "preconditions": ("login", "ended"),
                "body": {"example": "EMAIL_GENERAL"},
            },
        ),
    },
}
