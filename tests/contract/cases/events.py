"""Server contract cases for CON-3 (`streamChatEvents`), owned by AEA-41 (AC-15, AEA-41-1).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, tests/api/test_contract_cases_events.py
drives them. Vocabulary (closed):
  preconditions: "login" = sign in and keep the cookie; "started_thread" = a conversations row owned by this login session.
  thread: "started" (the precondition's thread), "unknown" (a fresh UUID4) or a literal path segment ("thr_9d41").
  events: ChatEvent types appended in order to the started thread's stream, payloads from the OpenAPI Ev* examples.
  last_event_id: None sends no header; {"after_event": n} sends the id of the n-th appended event (1-based).
  frames: the number of SSE frames expected; every 200 case ends on chat_closed, so a runner can read to the end.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "events"
_TAKEOVER: Final = ("representative_joined", "ai_paused", "staff_message", "chat_closed")
CASES: Final[dict[str, dict[str, object]]] = {
    "streamChatEvents": {
        "public": False,
        "drives": (
            {
                "name": "first_connect",
                "status": 200,
                "preconditions": ("login", "started_thread"),
                "thread": "started",
                "events": _TAKEOVER,
                "last_event_id": None,
                "frames": 4,
            },
            {
                "name": "resume",
                "status": 200,
                "preconditions": ("login", "started_thread"),
                "thread": "started",
                "events": _TAKEOVER,
                "last_event_id": {"after_event": 2},
                "frames": 2,
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "thread": "unknown",
            },
            {
                "name": "unknown_thread",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login",),
                "thread": "unknown",
            },
            {
                "name": "malformed_thread",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login",),
                "thread": "thr_9d41",
            },
        ),
    }
}
