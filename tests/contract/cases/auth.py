"""Server contract cases for CON-22 (`login`, `logout`), owned by AEA-23 (AC-29, AEA-23-3).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, AEA-23's
tests/api/test_contract_cases_auth.py drives them. Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie.
  setup: "login_rejects_exhausted" = first send limits.web.login_rejects_per_ip wrong-pair logins from the same client.
  body: {"example": <named request example>, "credentials": "configured" | "wrong_password"} fills username and
        password from the test settings ("wrong_password" keeps the configured username and sends another password);
        {"raw": <JSON value>} sends JSON as given; {"text": <str>} sends non-JSON text; None sends no body.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "auth"
CASES: Final[dict[str, dict[str, object]]] = {
    "login": {
        "public": True,
        "drives": (
            {
                "name": "signed_in",
                "status": 200,
                "preconditions": (),
                "body": {"example": "PLACEHOLDERS", "credentials": "configured"},
            },
            {
                "name": "missing_password",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": (),
                "body": {"raw": {"username": "placeholder-user"}},
            },
            {
                "name": "not_json",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": (),
                "body": {"text": "not json"},
            },
            {
                "name": "wrong_pair",
                "status": 401,
                "code": "LOGIN_FAILED",
                "preconditions": (),
                "body": {"example": "PLACEHOLDERS", "credentials": "wrong_password"},
            },
            {
                "name": "throttled",
                "status": 429,
                "code": "LOGIN_RATE_LIMITED",
                "preconditions": (),
                "setup": "login_rejects_exhausted",
                "body": {"example": "PLACEHOLDERS", "credentials": "configured"},
            },
        ),
    },
    "logout": {
        "public": False,
        "drives": (
            {"name": "logged_out", "status": 204, "preconditions": ("login",), "body": None},
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": None,
            },
        ),
    },
}
