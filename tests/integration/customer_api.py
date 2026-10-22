"""AEA-51's HTTP helpers over AEA-57's JourneyClient: every /api call names its operationId, so every response is
checked against the signed OpenAPI. Phone numbers and codes are read at run time (customer row, inbox) and are never
printed or written into a test file.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx

from tests.api.openapi_check import SseFrame
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.run import JourneyRun


@dataclass
class Chat:
    run: JourneyRun
    client: JourneyClient
    thread_id: str
    opened: dict[str, Any]  # the 201 StartSessionResponse body
    responses: list[httpx.Response] = field(default_factory=list)
    codes: list[str] = field(
        default_factory=list
    )  # every code read from the inbox for this chat (capture tests scan for them)


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
    code = str(max(live, key=lambda m: m["at"])["code"])
    chat.codes.append(code)
    return code


def customer_row(run: JourneyRun, customer_id: str) -> dict[str, Any]:
    return run.db.one("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))


def verify(
    chat: Chat,
    customer_id: str,
    opening_text: str,
    *,
    before_form: Callable[[], None] | None = None,
    before_code: Callable[[], None] | None = None,
) -> httpx.Response:
    """Opening message, the locate form filled from the customer row, then the code from the inbox.

    `before_form` and `before_code` let a scenario set the model script for those turns."""
    resp = say(chat, opening_text)
    if blocks(resp, "locate_prompt"):
        if before_form is not None:
            before_form()
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
    if before_code is not None:
        before_code()
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


def read_events(
    client: JourneyClient, path: str, *, last_event_id: str | None = None, seconds: float = 2.0
) -> list[SseFrame]:
    """An event stream for a short while: the complete frames received before the time limit (heartbeats skipped)."""
    frames: list[SseFrame] = []
    data: list[str] = []
    event: str | None = None
    ident: str | None = None
    headers = {"Last-Event-ID": last_event_id} if last_event_id is not None else {}
    try:
        with client._http.stream(
            "GET",
            path,
            headers=headers,
            timeout=httpx.Timeout(connect=5.0, read=seconds, write=5.0, pool=5.0),
        ) as response:
            assert response.status_code == 200, f"{path} answered HTTP {response.status_code}"
            deadline = time.monotonic() + seconds
            for raw in response.iter_lines():
                line = raw.rstrip("\r\n")
                if line == "":
                    if data:
                        frames.append(SseFrame(event=event, id=ident, data="\n".join(data)))
                    event, ident, data = None, None, []
                elif line.startswith("id:"):
                    ident = line[3:].strip()
                elif line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data.append(line[5:].lstrip(" "))
                if time.monotonic() > deadline:
                    break
    except httpx.ReadTimeout:
        pass
    return frames
