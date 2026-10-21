"""AEA-51's HTTP helpers over AEA-57's JourneyClient: every /api call names its operationId, so every response is
checked against the signed OpenAPI. Phone numbers and codes are read at run time (customer row, inbox) and are never
printed or written into a test file.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx

from tests.journeys.support.client import JourneyClient
from tests.journeys.support.run import JourneyRun


@dataclass
class Chat:
    run: JourneyRun
    client: JourneyClient
    thread_id: str
    opened: dict[str, Any]  # the 201 StartSessionResponse body
    responses: list[httpx.Response] = field(default_factory=list)


def login(run: JourneyRun) -> JourneyClient:
    return run.login().client


def open_chat(
    run: JourneyRun, client: JourneyClient | None = None, *, headers: Mapping[str, str] | None = None
) -> Chat:
    c = client if client is not None else login(run)
    response = c.call("POST", "/api/chat/sessions", operation_id="startChatSession", headers=headers)
    assert response.status_code == 201, f"startChatSession answered HTTP {response.status_code}"
    body = response.json()
    return Chat(run=run, client=c, thread_id=body["thread_id"], opened=body, responses=[response])


def submit(
    chat: Chat,
    payload: Mapping[str, Any],
    *,
    turn_id: str | None = None,
    headers: Mapping[str, str] | None = None,
) -> httpx.Response:
    response = chat.client.call(
        "POST",
        f"/api/chat/sessions/{chat.thread_id}/turns",
        operation_id="submitTurn",
        body={"turn_id": turn_id or str(uuid.uuid4()), "payload": dict(payload)},
        headers=headers,
    )
    chat.responses.append(response)
    assert response.status_code == 200, f"submitTurn answered HTTP {response.status_code}"
    return response


def say(chat: Chat, text: str, **kw: Any) -> httpx.Response:
    return submit(chat, {"kind": "text", "text": text}, **kw)


def pick(chat: Chat, card_id: str, option: str, **kw: Any) -> httpx.Response:
    return submit(chat, {"kind": "choice", "card_id": card_id, "option": option}, **kw)


def send_form(chat: Chat, card_id: str, values: Mapping[str, str], **kw: Any) -> httpx.Response:
    return submit(chat, {"kind": "form", "card_id": card_id, "values": dict(values)}, **kw)


def send_code(chat: Chat, card_id: str, code: str, **kw: Any) -> httpx.Response:
    return submit(chat, {"kind": "code", "card_id": card_id, "code": code}, **kw)


def blocks(resp: httpx.Response, kind: str | None = None) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = resp.json()["blocks"]
    return [b for b in found if kind is None or b["type"] == kind]


def first_block(resp: httpx.Response) -> dict[str, Any]:
    found = blocks(resp)
    assert found, "the response carries no blocks"
    return found[0]


def card_id_of(resp: httpx.Response, kind: str) -> str:
    for block in blocks(resp, kind):
        return str(block["card_id"])
    raise AssertionError(f"no {kind} block in the response")


def inbox(chat: Chat) -> list[dict[str, Any]]:
    response = chat.client.call("GET", "/api/demo/inbox", operation_id="listDemoInbox")
    assert response.status_code == 200
    messages: list[dict[str, Any]] = response.json()["messages"]
    return messages


def newest_code(chat: Chat) -> str:
    live = [m for m in inbox(chat) if m["status"] == "active" and m.get("code")]
    assert live, "the inbox holds no active code"
    return str(max(live, key=lambda m: m["at"])["code"])


def customer_row(run: JourneyRun, customer_id: str) -> dict[str, Any]:
    return run.db.one("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))


def verify(chat: Chat, customer_id: str, opening_text: str) -> httpx.Response:
    """Opening message, the locate form filled from the customer row, then the code from the inbox."""
    resp = say(chat, opening_text)
    if blocks(resp, "locate_prompt"):
        block = blocks(resp, "locate_prompt")[0]
        row = customer_row(chat.run, customer_id)
        wanted = {"name": row["name"], "phone": row["phone"], "customer_id": customer_id}
        field_set = next(
            (fs for fs in block["field_sets"] if all(f in wanted for f in fs)),
            None,
        )
        assert field_set is not None, "the locate prompt offers no field set this helper can fill"
        resp = send_form(chat, block["card_id"], {f: str(wanted[f]) for f in field_set})
    code_card = card_id_of(resp, "code_prompt")
    return send_code(chat, code_card, newest_code(chat))


def switch_role(client: JourneyClient, role: str) -> httpx.Response:
    response = client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": role})
    assert response.status_code == 200
    return response


def set_staffing(client: JourneyClient, mode: str) -> httpx.Response:
    response = client.call("PUT", "/api/demo/staffing", operation_id="setStaffing", body={"mode": mode})
    assert response.status_code == 200
    return response


def advance_clock(client: JourneyClient, step: str) -> httpx.Response:
    response = client.call("POST", "/api/demo/clock", operation_id="advanceDemoClock", body={"step": step})
    assert response.status_code == 200
    return response


def rows_for_turn(run: JourneyRun, table: str, turn_id: str) -> list[dict[str, Any]]:
    assert table.isidentifier(), "table names are code constants"
    return run.db.rows(f"SELECT * FROM {table} WHERE turn_id = ?", (turn_id,))  # noqa: S608


def turn_row(run: JourneyRun, turn_id: str) -> dict[str, Any]:
    return run.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
