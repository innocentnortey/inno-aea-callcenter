"""Server contract cases for CON-11, 12, 13, 15, 16, 17, owned by AEA-45 (AC-19). Read by AEA-59's runner
(tests/contract/test_openapi_server.py); tests/api/test_contract_cases_staff_cases.py drives them with service doubles.
Shape follows tests/contract/cases/staff_live.py and the README beside this file.

Closed vocabulary:
  preconditions
    "login": sign in with the configured demo pair and keep the cookie.
    "role:<customer|representative|supervisor|owner>": switchRole (CON-10).
    "case_claimed_by_supervisor": local-driver-only; MHC-C-0007 is owned by the supervisor.
    "case_state": local-driver-only; marks drives whose case, message or flag state the runner cannot build on a fresh
      first-boot copy (version, lifecycle, message_id, flag_id). They are proved by the local driver at `mock-tested`.
  body: {"example": "<name>"} sends the named OpenAPI request example; {"raw": <JSON>} sends the JSON as given.
  path: {"reference": "<literal>"} or {"flag_id": "<literal>"}, sent as given.

"MHC-C-0007" is AEA-31's first-boot seed case (unassigned, version 1, services/reset.py). The raw-body drives that send
`expected_version: 1` rely on that seed.
"""

from __future__ import annotations

from typing import Any, Final

ROUTE_FILE: Final = "staff_cases"
_REP: Final = ("login", "role:representative")
_SUP: Final = ("login", "role:supervisor")
_OWN: Final = ("login", "role:owner")
_CUST: Final = ("login",)
_SEEDED: Final = {"reference": "MHC-C-0007"}
_UNKNOWN: Final = {"reference": "MHC-C-9999"}
_MALFORMED: Final = {"reference": "MHC-C-7"}
_FLAG: Final = {"flag_id": "flg-1"}
_LONG: Final = "z" * 2001


def _d(
    name: str,
    status: int,
    pre: tuple[str, ...],
    *,
    code: str | None = None,
    path: dict[str, str] | None = None,
    example: str | None = None,
    raw: object = None,
) -> dict[str, Any]:
    drive: dict[str, Any] = {"name": name, "status": status, "preconditions": pre}
    if code is not None:
        drive["code"] = code
    if path is not None:
        drive["path"] = path
    if example is not None:
        drive["body"] = {"example": example}
    elif raw is not None:
        drive["body"] = {"raw": raw}
    return drive


_UNAUTH: Final = "UNAUTHENTICATED"
_ROLE: Final = "ROLE_NOT_ALLOWED"
_VALID: Final = "VALIDATION_ERROR"
_NOT_FOUND: Final = "CASE_NOT_FOUND"
_STATE: Final = ("case_state",)

CASES: Final[dict[str, dict[str, object]]] = {
    "getQueue": {
        "public": False,
        "drives": (
            _d("representative_reads", 200, _REP),
            _d("supervisor_reads", 200, _SUP),
            _d("no_session", 401, (), code=_UNAUTH),
            _d("customer_refused", 403, _CUST, code=_ROLE),
            _d("owner_refused", 403, _OWN, code=_ROLE),
        ),
    },
    "getCase": {
        "public": False,
        "drives": (
            _d("representative_reads", 200, _REP, path=_SEEDED),
            _d("owner_reads", 200, _OWN, path=_SEEDED),
            _d("no_session", 401, (), code=_UNAUTH, path=_SEEDED),
            _d("customer_refused", 403, _CUST, code=_ROLE, path=_SEEDED),
            _d("unknown_case", 404, _REP, code=_NOT_FOUND, path=_UNKNOWN),
            _d("malformed_reference", 404, _REP, code=_NOT_FOUND, path=_MALFORMED),
        ),
    },
    "applyCaseAction": {
        "public": False,
        "drives": (
            _d("claim", 200, (*_REP, *_STATE), path=_SEEDED, example="CLAIM"),
            _d("wait", 200, (*_REP, *_STATE), path=_SEEDED, example="WAIT"),
            _d("resolve", 200, (*_REP, *_STATE), path=_SEEDED, example="RESOLVE"),
            _d("release", 200, (*_REP, *_STATE), path=_SEEDED, example="RELEASE"),
            _d("assign", 200, (*_SUP, *_STATE), path=_SEEDED, example="ASSIGN"),
            _d("change_priority", 200, (*_SUP, *_STATE), path=_SEEDED, example="CHANGE_PRIORITY"),
            _d("claim_seeded", 200, _REP, path=_SEEDED, raw={"action": "claim", "expected_version": 1}),
            _d("no_session", 401, (), code=_UNAUTH, path=_SEEDED, example="CLAIM"),
            _d("owner_refused", 403, _OWN, code=_ROLE, path=_SEEDED, example="CLAIM"),
            _d("assign_as_representative", 403, _REP, code=_ROLE, path=_SEEDED, example="ASSIGN"),
            _d("unknown_case", 404, _REP, code=_NOT_FOUND, path=_UNKNOWN, example="CLAIM"),
            _d("malformed_reference", 400, _REP, code=_VALID, path=_MALFORMED, example="CLAIM"),
            _d("missing_expected_version", 400, _REP, code=_VALID, path=_SEEDED, raw={"action": "claim"}),
            _d("stale_version", 409, _REP, code="VERSION_CONFLICT", path=_SEEDED, example="CLAIM"),
            _d(
                "claimed_by_supervisor",
                409,
                (*_REP, "case_claimed_by_supervisor"),
                code="CASE_ALREADY_CLAIMED",
                path=_SEEDED,
                example="CLAIM",
            ),
            _d(
                "resolve_before_claim",
                409,
                _REP,
                code="NOT_ALLOWED_IN_STATE",
                path=_SEEDED,
                raw={"action": "resolve", "expected_version": 1, "outcome": "Credit decision recorded"},
            ),
            _d(
                "release_without_reason",
                422,
                _REP,
                code="REASON_REQUIRED",
                path=_SEEDED,
                raw={"action": "release", "expected_version": 1},
            ),
            _d(
                "wait_without_wake_up",
                422,
                _REP,
                code="WAKE_UP_REQUIRED",
                path=_SEEDED,
                raw={"action": "wait", "expected_version": 1},
            ),
            _d(
                "resolve_without_outcome",
                422,
                _REP,
                code="OUTCOME_REQUIRED",
                path=_SEEDED,
                raw={"action": "resolve", "expected_version": 1},
            ),
        ),
    },
    "recordContactActivity": {
        "public": False,
        "drives": (
            _d("call_logged", 201, (*_REP, *_STATE), path=_SEEDED, example="CALL"),
            _d(
                "not_claimed",
                409,
                _REP,
                code="NOT_ALLOWED_IN_STATE",
                path=_SEEDED,
                raw={"kind": "call", "outcome": "reached", "expected_version": 1},
            ),
            _d("stale_version", 409, _REP, code="VERSION_CONFLICT", path=_SEEDED, example="CALL"),
            _d("no_session", 401, (), code=_UNAUTH, path=_SEEDED, example="CALL"),
            _d("supervisor_refused", 403, _SUP, code=_ROLE, path=_SEEDED, example="CALL"),
            _d("unknown_case", 404, _REP, code=_NOT_FOUND, path=_UNKNOWN, example="CALL"),
            _d("malformed_reference", 400, _REP, code=_VALID, path=_MALFORMED, example="CALL"),
            _d(
                "missing_expected_version",
                400,
                _REP,
                code=_VALID,
                path=_SEEDED,
                raw={"kind": "call", "outcome": "reached"},
            ),
        ),
    },
    "createFlag": {
        "public": False,
        "drives": (
            _d("flag_answer", 201, (*_REP, *_STATE), example="ANSWER"),
            _d("no_session", 401, (), code=_UNAUTH, example="ANSWER"),
            _d("owner_refused", 403, _OWN, code=_ROLE, example="ANSWER"),
            _d(
                "unknown_case",
                404,
                _REP,
                code=_NOT_FOUND,
                raw={"case_ref": "MHC-C-9999", "target": "answer"},
            ),
            _d(
                "malformed_case_ref",
                400,
                _REP,
                code=_VALID,
                raw={"case_ref": "MHC-C-7", "target": "answer"},
            ),
            _d(
                "note_too_long",
                400,
                _REP,
                code=_VALID,
                raw={"case_ref": "MHC-C-0007", "target": "answer", "note": _LONG},
            ),
            _d(
                "message_outside_case",
                400,
                (*_REP, *_STATE),
                code=_VALID,
                raw={"case_ref": "MHC-C-0007", "target": "answer", "message_id": "m-999999"},
            ),
        ),
    },
    "listFlags": {
        "public": False,
        "drives": (
            _d("representative_lists", 200, _REP),
            _d("owner_lists", 200, _OWN),
            _d("no_session", 401, (), code=_UNAUTH),
            _d("customer_refused", 403, _CUST, code=_ROLE),
        ),
    },
    "reviewFlag": {
        "public": False,
        "drives": (
            _d("review", 200, (*_SUP, *_STATE), path=_FLAG, example="REVIEW"),
            _d("no_session", 401, (), code=_UNAUTH, path=_FLAG, example="REVIEW"),
            _d("representative_refused", 403, _REP, code=_ROLE, path=_FLAG, example="REVIEW"),
            _d(
                "unknown_flag",
                404,
                _SUP,
                code="FLAG_NOT_FOUND",
                path={"flag_id": "flg-999999"},
                example="REVIEW",
            ),
            _d("bad_status", 400, _SUP, code=_VALID, path=_FLAG, raw={"status": "new"}),
            _d(
                "note_too_long",
                400,
                _SUP,
                code=_VALID,
                path=_FLAG,
                raw={"status": "reviewed", "note": _LONG},
            ),
        ),
    },
    "getOversight": {
        "public": False,
        "drives": (
            _d("supervisor_reads", 200, _SUP),
            _d("no_session", 401, (), code=_UNAUTH),
            _d("representative_refused", 403, _REP, code=_ROLE),
            _d("owner_refused", 403, _OWN, code=_ROLE),
        ),
    },
}
