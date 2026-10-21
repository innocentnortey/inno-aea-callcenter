"""An in-process stub of the eight OpenAPI operations the eval harness uses (AEA-24 plan 7.2).

It sits behind an ``httpx.MockTransport``: no server, no port. It records every request, counts concurrent
``submitTurn`` calls, issues inbox codes generated at run time and never holds a literal secret.

Test hooks:
  * ``scripted(call)`` returns a full TurnResponse body for that turn, or ``None`` for the default behaviour. A body
    containing the key ``"__status__"`` makes the stub answer with that HTTP status and an empty JSON object.
  * ``clock_for_thread(n)`` gives the demo clock for the n-th ``GET /api/demo/clock`` (0-based). The runner reads the
    clock once per played case, before it opens the chat, so n is the index of the case about to be played.
"""

from __future__ import annotations

import asyncio
import json
import re
import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import httpx

BASE_URL = "http://stub.example.test"
DEFAULT_CLOCK = "2026-10-16T10:00:00-05:00"
OTHER_CLOCK = "2026-10-17T10:00:00-05:00"
AT = "2026-10-16T10:00:00-05:00"
STATUS_KEY = "__status__"
PROMISE_R26 = "A representative will get back to you within 1 business day"

_TURN_PATH = re.compile(r"^/api/chat/sessions/([^/]+)/turns$")
_HANDOFF_PATH = re.compile(r"^/api/chat/sessions/([^/]+)/handoff$")


def _block(block_type: str, **fields: Any) -> dict[str, Any]:
    return {"block_id": f"blk-{secrets.token_hex(3)}", "type": block_type, **fields}


def text_block(text: str, sources: Sequence[dict[str, Any]] = ()) -> dict[str, Any]:
    return _block("text", text=text, sources=list(sources))


def source_chip(file: str, version_label: str = "Rev 2026-01") -> dict[str, Any]:
    return {
        "passage_id": f"p-{secrets.token_hex(3)}",
        "file": file,
        "section": "Section",
        "version_date": None,
        "excerpt": "quoted passage",
        "audience": "customer",
        "version_label": version_label,
    }


def handoff_block(promise_text: str = PROMISE_R26, reference: str = "MHC-C-0001") -> dict[str, Any]:
    return _block(
        "handoff",
        card_id="card-handoff",
        options=[],
        answered=None,
        reference=reference,
        variant="nobody_online",
        promise_text=promise_text,
        due_at="2026-10-19T12:00:00-05:00",
        due_label="by noon on Monday",
        extra_lines=[],
        produced_by_code=True,
        followup_chooser=None,
    )


def safety_block() -> dict[str, Any]:
    return _block(
        "safety",
        level="DANGER",
        signal_word="DANGER",
        steps=["Leave the house now."],
        call_key={"label": "Call", "number": "911"},
        contact_line="We will follow up.",
        case_priority="P0",
        case_reference="MHC-C-0002",
        fixed_text="Safety first.",
        pinned=True,
    )


def emergency_line_block() -> dict[str, Any]:
    return _block(
        "emergency_line",
        lead_text="Call our emergency line.",
        number="000",
        number_note="Always open.",
        separate_line=None,
        case_priority="P1",
        case_reference="MHC-C-0003",
    )


def account_card_block() -> dict[str, Any]:
    return _block("account_card", kind="invoice", invoice=None, membership=None, warranty=None)


def failure_offer_block(text: str = "We could not finish this here.") -> dict[str, Any]:
    return _block("failure_offer", text=text, person_key=True)


def code_prompt_block(state: str = "sent") -> dict[str, Any]:
    return _block(
        "code_prompt",
        card_id="card-code",
        options=[],
        answered=None,
        state=state,
        hint="the phone on file",
        tries_left=3,
        expires_at="2026-10-16T10:10:00-05:00",
        resend_offered=False,
        resends_left=2,
        inbox_link=None,
        code_in_response=None,
    )


def locate_prompt_block() -> dict[str, Any]:
    return _block(
        "locate_prompt",
        card_id="card-locate",
        options=[],
        answered=None,
        reason_text="Who am I speaking with?",
        field_sets=[["name", "phone"]],
    )


def write_of(kind: str, turn_id: str = "turn") -> dict[str, Any]:
    return {"kind": kind, "summary": "stub write", "turn_id": turn_id, "at": AT}


def notice_of(code: str) -> dict[str, Any]:
    return {
        "code": code,
        "actions": ["try_again"],
        "retry_turn_id": None,
        "delivered_to_representative": False,
    }


def settled(identity: str = "not_checked") -> dict[str, Any]:
    return {
        "built_from": "conversation_state",
        "visit": None,
        "request": None,
        "identity": {"status": identity, "hint": None},
        "replying": {"kind": "ai", "display_name": None},
        "actions": [],
    }


def turn_response(
    thread_id: str,
    turn_id: str,
    blocks: Sequence[dict[str, Any]],
    *,
    writes: Sequence[dict[str, Any]] = (),
    identity: str = "not_checked",
    notice: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "thread_id": thread_id,
        "turn_id": turn_id,
        "sequence": 1,
        "blocks": list(blocks),
        "settled": settled(identity),
        "writes": list(writes),
        "controller": {"kind": "ai", "display_name": None},
        "notice": notice,
        "last_event_id": 1,
    }


@dataclass
class StubThread:
    thread_id: str
    index: int
    turns: int = 0
    identity: str = "not_checked"
    last_code: str | None = None
    memo: dict[str, Any] = field(default_factory=dict)


@dataclass
class StubCall:
    thread_id: str
    thread_index: int
    turn_index: int
    turn_id: str
    payload: dict[str, Any]
    state: StubThread

    @property
    def text(self) -> str:
        return str(self.payload.get("text", ""))

    def reply(
        self,
        blocks: Sequence[dict[str, Any]],
        *,
        writes: Sequence[dict[str, Any]] = (),
        identity: str | None = None,
        notice: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return turn_response(
            self.thread_id,
            self.turn_id,
            blocks,
            writes=writes,
            identity=identity or self.state.identity,
            notice=notice,
        )


class StubApp:
    def __init__(
        self,
        *,
        username: str,
        password: str,
        eval_key: str,
        scripted: Callable[[StubCall], dict[str, Any] | None] | None = None,
        clock_now: str = DEFAULT_CLOCK,
        agent_version: str = "abc123def456+0a1b2c3d",
        today_cents: int = 0,
        cap_cents: int = 3000,
        turn_delay_s: float = 0.0,
        clock_for_thread: Callable[[int], str] | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self.eval_key = eval_key
        self._scripted = scripted
        self._clock_now = clock_now
        self._agent_version = agent_version
        self._today_cents = today_cents
        self._cap_cents = cap_cents
        self._turn_delay_s = turn_delay_s
        self._clock_for_thread = clock_for_thread
        self._token = secrets.token_urlsafe(16)
        self._threads: dict[str, StubThread] = {}
        self._inbox: list[dict[str, Any]] = []
        self._clock_reads = 0
        self._in_flight = 0
        self.requests: list[httpx.Request] = []
        self.max_in_flight_turns = 0
        self.issued_codes: list[str] = []
        self.transport = httpx.MockTransport(self._handle)

    # -- helpers for tests -------------------------------------------------------------------------------------
    def paths(self) -> list[tuple[str, str]]:
        return [(r.method, r.url.path) for r in self.requests]

    def turn_requests(self) -> list[httpx.Request]:
        return [r for r in self.requests if r.method == "POST" and _TURN_PATH.match(r.url.path)]

    def turn_bodies(self) -> list[dict[str, Any]]:
        return [json.loads(r.content) for r in self.turn_requests()]

    # -- the transport handler ---------------------------------------------------------------------------------
    async def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path, method = request.url.path, request.method
        if method == "POST" and path == "/api/login":
            body = json.loads(request.content or b"{}")
            if body.get("username") == self._username and body.get("password") == self._password:
                cookie = f"mhc_session={self._token}; Path=/; HttpOnly; SameSite=Lax"
                return httpx.Response(200, json={"ok": True}, headers={"set-cookie": cookie})
            return httpx.Response(401, json={"error": "login"})
        if f"mhc_session={self._token}" not in request.headers.get("cookie", ""):
            return httpx.Response(401, json={"error": "no session"})
        if method == "GET" and path == "/api/eval/latest":
            return httpx.Response(
                200,
                json={
                    "splits": {"dev": None, "held_out": None},
                    "headline": None,
                    "current_agent_version": self._agent_version,
                    "dev_label": "Dev",
                },
            )
        if method == "GET" and path == "/api/monitoring":
            return httpx.Response(
                200,
                json={
                    "as_of": AT,
                    "spend": {
                        "today_cents": self._today_cents,
                        "cap_cents": self._cap_cents,
                        "day": "America/Chicago midnight to midnight",
                        "resets_at": "2026-10-17T00:00:00-05:00",
                    },
                },
            )
        if method == "GET" and path == "/api/demo/clock":
            now = self._clock_now
            if self._clock_for_thread is not None:
                now = self._clock_for_thread(self._clock_reads)
            self._clock_reads += 1
            return httpx.Response(200, json={"now": now, "label": "Fri", "date_label": "Fri (demo date)"})
        if method == "POST" and path == "/api/chat/sessions":
            thread = StubThread(thread_id=f"thr_{len(self._threads)}", index=len(self._threads))
            self._threads[thread.thread_id] = thread
            return httpx.Response(201, json={"thread_id": thread.thread_id})
        if method == "GET" and path == "/api/demo/inbox":
            return httpx.Response(200, json={"messages": [dict(m) for m in self._inbox]})
        turn = _TURN_PATH.match(path)
        if method == "POST" and turn:
            return await self._turn(request, turn.group(1))
        handoff = _HANDOFF_PATH.match(path)
        if method == "POST" and handoff:
            target = self._threads.get(handoff.group(1))
            if target is None:
                return httpx.Response(404, json={"error": "thread"})
            return httpx.Response(
                200,
                json={
                    "result": "case_created",
                    "block": handoff_block(),
                    "settled": settled(thread.identity),
                },
            )
        return httpx.Response(404, json={"error": "route"})

    async def _turn(self, request: httpx.Request, thread_id: str) -> httpx.Response:
        thread = self._threads.get(thread_id)
        if thread is None:
            return httpx.Response(404, json={"error": "thread"})
        body = json.loads(request.content)
        self._in_flight += 1
        self.max_in_flight_turns = max(self.max_in_flight_turns, self._in_flight)
        try:
            if self._turn_delay_s:
                await asyncio.sleep(self._turn_delay_s)
            call = StubCall(thread_id, thread.index, thread.turns, body["turn_id"], body["payload"], thread)
            thread.turns += 1
            result = self._scripted(call) if self._scripted else None
            if result is None:
                result = self._default(call)
        finally:
            self._in_flight -= 1
        if STATUS_KEY in result:
            return httpx.Response(int(result[STATUS_KEY]), json={})
        return httpx.Response(200, json=result)

    def _default(self, call: StubCall) -> dict[str, Any]:
        payload = call.payload
        kind = payload.get("kind")
        if kind == "form" and payload.get("values", {}).get("phone"):
            code = f"{secrets.randbelow(10**6):06d}"
            self.issued_codes.append(code)
            call.state.last_code = code
            call.state.identity = "code_sent"
            self._inbox.insert(
                0,
                {
                    "id": f"msg_{len(self.issued_codes)}",
                    "at": AT,
                    "to_masked": "masked",
                    "body": "Your Meridian code",
                    "code": code,
                    "status": "active",
                    "expires_at": "2026-10-16T10:10:00-05:00",
                },
            )
            return call.reply(
                [text_block("I sent a code to the phone on file."), code_prompt_block()], identity="code_sent"
            )
        if kind == "code":
            for message in self._inbox:
                if message["status"] == "active" and message["code"] == payload.get("code"):
                    message["status"] = "used"
                    call.state.identity = "verified"
                    return call.reply(
                        [text_block("Thanks, that code matched.")],
                        writes=[write_of("verified", call.turn_id)],
                        identity="verified",
                    )
            return call.reply([code_prompt_block("wrong")], identity="not_verified")
        return call.reply([text_block("Thanks, I can help with that.")])
