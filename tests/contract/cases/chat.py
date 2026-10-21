"""Server contract cases for CON-1 and CON-2 (`startChatSession`, `getChatThread`, `submitTurn`), owned by AEA-40 (AC-22).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, tests/api/test_contract_cases_chat.py
drives them through the in-process app. Same shape as tests/contract/cases/auth.py. Vocabulary (closed):
  preconditions: "login" = a signed-in session (its cookie is sent); "start_thread" = a started chat thread of that
                 session (the thread id the path calls "started").
  setup:         "reset_held" = hold the reset gate for the length of the request;
                 "other_session_thread" = a thread that belongs to another login session (path "other_session");
                 "ended_thread" = end the started thread the way a demo reset does (path "ended");
                 "turn_running" = leave a turn of the request's turn_id `running` on the started thread.
  path:          {"thread_id": "started" | "unknown" | "malformed" | "other_session" | "ended"}.
  body:          {"example": <named request example>} | {"raw": <JSON value>} | None (no body).
`run_graph` (AEA-51) is a double in the in-process driver; the strict runner may report a case as
`not bound: run_graph` until it exists.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "chat"
CASES: Final[dict[str, dict[str, object]]] = {
    "startChatSession": {
        "public": False,
        "drives": (
            {"name": "started", "status": 201, "preconditions": ("login",), "body": None},
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "body": None,
            },
            {
                "name": "reset_in_progress",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login",),
                "setup": "reset_held",
                "body": None,
            },
        ),
    },
    "getChatThread": {
        "public": False,
        "drives": (
            {
                "name": "read",
                "status": 200,
                "preconditions": ("login", "start_thread"),
                "path": {"thread_id": "started"},
                "body": None,
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "path": {"thread_id": "unknown"},
                "body": None,
            },
            {
                "name": "unknown_thread",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login",),
                "path": {"thread_id": "unknown"},
                "body": None,
            },
            {
                "name": "malformed_thread",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login",),
                "path": {"thread_id": "malformed"},
                "body": None,
            },
            {
                "name": "other_session_thread",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login",),
                "setup": "other_session_thread",
                "path": {"thread_id": "other_session"},
                "body": None,
            },
            {
                "name": "ended_thread",
                "status": 410,
                "code": "SESSION_ENDED",
                "preconditions": ("login", "start_thread"),
                "setup": "ended_thread",
                "path": {"thread_id": "ended"},
                "body": None,
            },
        ),
    },
    "submitTurn": {
        "public": False,
        "drives": (
            *(
                {
                    "name": f"turn_{example.lower()}",
                    "status": 200,
                    "preconditions": ("login", "start_thread"),
                    "path": {"thread_id": "started"},
                    "body": {"example": example},
                }
                for example in ("TEXT", "CHOICE_SLOT", "CODE", "FORM_LOCATE", "FORM_WHERE")
            ),
            {
                "name": "empty_text",
                "status": 400,
                "code": "VALIDATION_ERROR",
                "preconditions": ("login", "start_thread"),
                "path": {"thread_id": "started"},
                "body": {"raw": {"payload": {"kind": "text", "text": ""}}},
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "path": {"thread_id": "unknown"},
                "body": {"example": "TEXT"},
            },
            {
                "name": "unknown_thread",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login",),
                "path": {"thread_id": "unknown"},
                "body": {"example": "TEXT"},
            },
            {
                "name": "turn_in_progress",
                "status": 409,
                "code": "TURN_IN_PROGRESS",
                "preconditions": ("login", "start_thread"),
                "setup": "turn_running",
                "path": {"thread_id": "started"},
                "body": {"example": "TEXT"},
            },
            {
                "name": "ended_thread",
                "status": 410,
                "code": "SESSION_ENDED",
                "preconditions": ("login", "start_thread"),
                "setup": "ended_thread",
                "path": {"thread_id": "ended"},
                "body": {"example": "TEXT"},
            },
            {
                "name": "reset_in_progress",
                "status": 503,
                "code": "RESET_IN_PROGRESS",
                "preconditions": ("login", "start_thread"),
                "setup": "reset_held",
                "path": {"thread_id": "started"},
                "body": {"example": "TEXT"},
            },
        ),
    },
}
