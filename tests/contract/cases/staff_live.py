"""Server contract cases for CON-14 (`liveChatAction`) and CON-21 (`streamCaseEvents`), owned by AEA-46 (AC-22,
AEA-46-2). Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands,
tests/api/test_contract_cases_staff_live.py drives them. Shape follows tests/contract/cases/auth.py.

Closed vocabulary:
  preconditions
    "login": sign in with the configured demo pair and keep the cookie.
    "as_representative": switchRole to representative (CON-10, AEA-44); the local driver issues a representative token.
    "live_case_claimed": the working copy holds MHC-C-0007, lifecycle claimed, owner representative, its
      conversation live_state queued.
    "live_case_joined": as above, then a successful join.
    "live_case_unclaimed": MHC-C-0007 queued with no owner.
    "case_claimed_by_supervisor": MHC-C-0007 queued, owner supervisor.
    "case_events": three events on case:MHC-C-0007 (controller_changed, case_changed, chat_closed closed_by_staff).
  body (liveChatAction): {"example": "<JOIN|SEND|HAND_BACK|CLOSE>"} sends the named OpenAPI request example;
    {"raw": <JSON>} sends the JSON as given.
  last_event_id (streamCaseEvents): the header value, absent when the key is absent.
  frames (streamCaseEvents 200): the number of SSE frames to read.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "staff_live"
_REP: Final = ("login", "as_representative")
_CLAIMED: Final = (*_REP, "live_case_claimed")
_JOINED: Final = (*_REP, "live_case_joined")
_STREAM: Final = (*_CLAIMED, "case_events")
CASES: Final[dict[str, dict[str, object]]] = {
    "liveChatAction": {
        "public": False,
        "drives": (
            {
                "name": "joined",
                "status": 200,
                "preconditions": _CLAIMED,
                "reference": "MHC-C-0007",
                "body": {"example": "JOIN"},
            },
            {
                "name": "sent",
                "status": 200,
                "preconditions": _JOINED,
                "reference": "MHC-C-0007",
                "body": {"example": "SEND"},
            },
            {
                "name": "handed_back",
                "status": 200,
                "preconditions": _JOINED,
                "reference": "MHC-C-0007",
                "body": {"example": "HAND_BACK"},
            },
            {
                "name": "closed",
                "status": 200,
                "preconditions": _JOINED,
                "reference": "MHC-C-0007",
                "body": {"example": "CLOSE"},
            },
            {
                "name": "text_on_join",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": _CLAIMED,
                "reference": "MHC-C-0007",
                "body": {"raw": {"action": "join", "text": "placeholder"}},
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "reference": "MHC-C-0007",
                "body": {"example": "JOIN"},
            },
            {
                "name": "wrong_role",
                "status": 403,
                "code": "ROLE_NOT_ALLOWED",
                "preconditions": ("login",),
                "reference": "MHC-C-0007",
                "body": {"example": "JOIN"},
            },
            {
                "name": "not_claimed_by_you",
                "status": 403,
                "code": "NOT_CLAIMED_BY_YOU",
                "preconditions": (*_REP, "live_case_unclaimed"),
                "reference": "MHC-C-0007",
                "body": {"example": "JOIN"},
            },
            {
                "name": "unknown_case",
                "status": 404,
                "code": "CASE_NOT_FOUND",
                "preconditions": _REP,
                "reference": "MHC-C-0099",
                "body": {"example": "JOIN"},
            },
            {
                "name": "not_live",
                "status": 409,
                "code": "NOT_LIVE",
                "preconditions": _CLAIMED,
                "reference": "MHC-C-0007",
                "body": {"example": "SEND"},
            },
            {
                "name": "already_claimed",
                "status": 409,
                "code": "CASE_ALREADY_CLAIMED",
                "preconditions": (*_REP, "case_claimed_by_supervisor"),
                "reference": "MHC-C-0007",
                "body": {"example": "JOIN"},
            },
        ),
    },
    "streamCaseEvents": {
        "public": False,
        "drives": (
            {
                "name": "first_connect",
                "status": 200,
                "preconditions": _STREAM,
                "reference": "MHC-C-0007",
                "frames": 3,
            },
            {
                "name": "resume",
                "status": 200,
                "preconditions": _STREAM,
                "reference": "MHC-C-0007",
                "last_event_id": 1,
                "frames": 2,
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "reference": "MHC-C-0007",
            },
            {
                "name": "wrong_role",
                "status": 403,
                "code": "ROLE_NOT_ALLOWED",
                "preconditions": ("login",),
                "reference": "MHC-C-0007",
            },
            {
                "name": "unknown_case",
                "status": 404,
                "code": "CASE_NOT_FOUND",
                "preconditions": _REP,
                "reference": "MHC-C-0099",
            },
        ),
    },
}
