"""The canned transport ``--dry-run`` plays against. It never contacts the network."""

from __future__ import annotations

import json
import secrets
from typing import Any

import httpx

_CLOCK = "2026-10-16T10:00:00-05:00"
_AT = "2026-10-16T10:00:00-05:00"
_PROMISE = "A representative will get back to you within 1 business day"


def _settled(identity: str) -> dict[str, Any]:
    return {
        "built_from": "conversation_state",
        "visit": None,
        "request": None,
        "identity": {"status": identity, "hint": None},
        "replying": {"kind": "ai", "display_name": None},
        "actions": [],
    }


def _handoff_block() -> dict[str, Any]:
    return {
        "block_id": "blk-dry-handoff",
        "type": "handoff",
        "card_id": "card-handoff",
        "options": [],
        "answered": None,
        "reference": "MHC-C-0001",
        "variant": "nobody_online",
        "promise_text": _PROMISE,
        "due_at": _AT,
        "due_label": "by noon on Monday",
        "extra_lines": [],
        "produced_by_code": True,
        "followup_chooser": None,
    }


def dry_run_transport() -> httpx.MockTransport:
    threads: list[str] = []
    inbox: list[dict[str, Any]] = []
    identity: dict[str, str] = {}

    def turn(thread_id: str, payload: dict[str, Any], turn_id: str) -> dict[str, Any]:
        kind = payload.get("kind")
        blocks: list[dict[str, Any]]
        if kind == "form":
            code = f"{secrets.randbelow(10**6):06d}"
            inbox.insert(
                0,
                {
                    "id": f"msg_dry_{len(inbox)}",
                    "at": _AT,
                    "to_masked": "masked",
                    "body": "Your Meridian code",
                    "code": code,
                    "status": "active",
                    "expires_at": _AT,
                },
            )
            identity[thread_id] = "code_sent"
            blocks = [
                {"block_id": "blk-dry-code", "type": "code_prompt", "card_id": "card-code", "options": []}
            ]
        elif kind == "code":
            identity[thread_id] = "verified"
            for message in inbox:
                if message["code"] == payload.get("code"):
                    message["status"] = "used"
            blocks = [{"block_id": "blk-dry-text", "type": "text", "text": "Dry run reply.", "sources": []}]
        else:
            blocks = [{"block_id": "blk-dry-text", "type": "text", "text": "Dry run reply.", "sources": []}]
        return {
            "thread_id": thread_id,
            "turn_id": turn_id,
            "sequence": 1,
            "blocks": blocks,
            "settled": _settled(identity.get(thread_id, "not_checked")),
            "writes": [],
            "controller": {"kind": "ai", "display_name": None},
            "notice": None,
            "last_event_id": 1,
        }

    def handle(request: httpx.Request) -> httpx.Response:
        path, method = request.url.path, request.method
        if method == "POST" and path == "/api/login":
            cookie = f"mhc_session={secrets.token_urlsafe(16)}; Path=/; HttpOnly; SameSite=Lax"
            return httpx.Response(200, json={"ok": True}, headers={"set-cookie": cookie})
        if method == "GET" and path == "/api/eval/latest":
            return httpx.Response(
                200,
                json={
                    "splits": {"dev": None, "held_out": None},
                    "headline": None,
                    "current_agent_version": "dry-run",
                    "dev_label": "Dev",
                },
            )
        if method == "GET" and path == "/api/monitoring":
            return httpx.Response(200, json={"spend": {"today_cents": 0, "cap_cents": 3000}})
        if method == "GET" and path == "/api/demo/clock":
            return httpx.Response(200, json={"now": _CLOCK})
        if method == "POST" and path == "/api/chat/sessions":
            threads.append(f"thr_dry_{len(threads)}")
            return httpx.Response(201, json={"thread_id": threads[-1]})
        if method == "GET" and path == "/api/demo/inbox":
            return httpx.Response(200, json={"messages": [dict(m) for m in inbox]})
        parts = path.strip("/").split("/")
        if method == "POST" and len(parts) == 5 and parts[:3] == ["api", "chat", "sessions"]:
            body = json.loads(request.content or b"{}")
            thread_id = parts[3]
            if parts[4] == "turns":
                return httpx.Response(200, json=turn(thread_id, body["payload"], body["turn_id"]))
            if parts[4] == "handoff":
                return httpx.Response(
                    200,
                    json={
                        "result": "case_created",
                        "block": _handoff_block(),
                        "settled": _settled(identity.get(thread_id, "not_checked")),
                    },
                )
        return httpx.Response(404, json={"error": "route"})

    return httpx.MockTransport(handle)
