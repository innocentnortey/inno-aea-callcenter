"""Server contract cases for CON-10 (`getSession`, `listDemoRoles`, `switchRole`), owned by AEA-44 (AC-18).

Read by AEA-59's runner; until it lands, tests/api/test_contract_cases_staff_session.py drives them. Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie;
                 "as_representative" / "as_supervisor" / "as_owner" = after "login", PUT /api/session/role to that role.
  setup: "reset_gate_held" = hold the app's ResetGate for the duration of the request.
  body: {"example": <named request example>} sends that example's value; {"raw": <JSON value>} sends it as given;
        None = no body.
  response_example: the named 200 response example the body must equal, apart from signed_in_at.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "staff_session"


def _ok(name: str, pre: tuple[str, ...], example: str | None = None) -> dict[str, object]:
    case: dict[str, object] = {"name": name, "status": 200, "preconditions": pre, "body": None}
    if example is not None:
        case["response_example"] = example
    return case


def _switch(name: str, pre: tuple[str, ...], request: str, response: str) -> dict[str, object]:
    return {
        "name": name,
        "status": 200,
        "preconditions": pre,
        "body": {"example": request},
        "response_example": response,
    }


def _no_session(body: dict[str, object] | None = None) -> dict[str, object]:
    return {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (), "body": body}


CASES: Final[dict[str, dict[str, object]]] = {
    "getSession": {
        "public": False,
        "drives": (
            _ok("customer", ("login",), "CUSTOMER"),
            _ok("representative", ("login", "as_representative"), "REPRESENTATIVE"),
            _ok("supervisor", ("login", "as_supervisor")),
            _ok("owner", ("login", "as_owner")),
            _no_session(),
        ),
    },
    "listDemoRoles": {
        "public": False,
        "drives": (_ok("roles", ("login",), "ROLES"), _no_session()),
    },
    "switchRole": {
        "public": False,
        "drives": (
            _switch("to_representative", ("login",), "REPRESENTATIVE", "TO_REPRESENTATIVE"),
            _switch("to_supervisor", ("login",), "SUPERVISOR", "TO_SUPERVISOR"),
            _switch("to_owner", ("login",), "OWNER", "TO_OWNER"),
            _switch("to_customer", ("login", "as_representative"), "CUSTOMER", "TO_CUSTOMER"),
            {
                "name": "bad_role",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login",),
                "body": {"raw": {"role": "admin"}},
            },
            {
                "name": "missing_role",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login",),
                "body": {"raw": {}},
            },
            _no_session({"example": "REPRESENTATIVE"}),
            {
                "name": "reset_in_progress",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "reset_gate_held",
                "body": {"example": "REPRESENTATIVE"},
            },
        ),
    },
}
