"""AEA-40 AC-22 (local driver): tests/contract/cases/chat.py holds the server cases for CON-1 and CON-2.

AEA-59's runner reads the same data later; until it lands this file drives every case through the in-process app.
Failure mode guarded: invariant (every named request example and every documented error status the routes can produce
has a case, and each case yields the status it names, valid against the OpenAPI).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from tests.api.chat_support import chat_env
from tests.api.openapi_check import load_contract, load_document
from tests.api.web_shell_support import assert_matches, cookie_header, make_client, reset_gate_of
from tests.contract.cases.chat import CASES, ROUTE_FILE
from tests.fakes import WORKED_PAIRS_NOW
from tests.services.chat_doubles import make_cmd, seed_thread, text_payload, turn_ids_of

# statuses the chat routes can produce (429 on startChatSession is AEA-23's middleware, not these routes)
ROUTE_STATUSES = {
    "startChatSession": {"201", "401", "503"},
    "getChatThread": {"200", "401", "404", "410"},
    "submitTurn": {"200", "400", "401", "404", "409", "410", "503"},
}
PATHS = {
    "startChatSession": "/api/chat/sessions",
    "getChatThread": "/api/chat/sessions/{thread_id}",
    "submitTurn": "/api/chat/sessions/{thread_id}/turns",
}


def _example(document: Any, name: str) -> dict[str, Any]:
    body = document["paths"][PATHS["submitTurn"]]["post"]["requestBody"]["content"]["application/json"]
    value: dict[str, Any] = body["examples"][name]["value"]
    return value


def test_chat_cases_cover_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-22): each case yields its status and code; every example and route-produced status is covered."""
    assert ROUTE_FILE == "chat"
    cases: dict[str, Any] = dict(CASES)
    assert set(cases) == {"startChatSession", "getChatThread", "submitTurn"}
    document = load_document()
    contract = load_contract()
    examples = set(
        document["paths"][PATHS["submitTurn"]]["post"]["requestBody"]["content"]["application/json"][
            "examples"
        ]
    )
    named: set[str] = set()
    covered: dict[str, set[str]] = {op: set() for op in cases}
    ran = 0

    for operation_id, entry in cases.items():
        spec = contract.operations[operation_id]
        assert entry["drives"], f"{operation_id} has no cases"
        for index, case in enumerate(entry["drives"]):
            needs_sessions = operation_id in ("startChatSession", "getChatThread") and case["status"] in (
                200,
                201,
            )
            with (
                chat_env(
                    monkeypatch, tmp_path / f"{operation_id}-{index}", with_session_service=needs_sessions
                ) as env,
                make_client(env.app) as client,
            ):
                headers: dict[str, str] = {}
                context: dict[str, str] = {"unknown": str(uuid.uuid4()), "malformed": "not-a-thread-id"}
                for step in case["preconditions"]:
                    assert step in ("login", "start_thread"), f"unknown precondition {step!r}"
                    if step == "login":
                        headers = cookie_header(env.token)
                    else:
                        context["started"] = str(seed_thread(env.store.uow, env.demo_session))
                body = case["body"]
                payload: dict[str, Any] | None = None
                if body is not None and "example" in body:
                    assert body["example"] in examples, f"{body['example']!r} is not a named request example"
                    named.add(body["example"])
                    payload = _example(document, body["example"])
                elif body is not None:
                    payload = body["raw"]
                setup = case.get("setup")
                if setup == "other_session_thread":
                    context["other_session"] = str(
                        seed_thread(env.store.uow, str(env.other_session().session_id))
                    )
                elif setup == "ended_thread":
                    assert "started" in context
                    with env.store.uow(write=True) as tx:
                        tx.core.reset.clear_demo_tables("reset-contract", ended_at=WORKED_PAIRS_NOW)
                        tx.commit()
                    context["ended"] = context["started"]
                elif setup == "turn_running":
                    assert payload is not None and "started" in context
                    running = make_cmd(
                        context["started"],
                        text_payload("x"),
                        turn_id=payload["turn_id"],
                    )
                    with env.store.uow(write=True) as tx:
                        tx.core.turns.begin(turn_ids_of(running), WORKED_PAIRS_NOW)
                        tx.commit()
                else:
                    assert setup in (None, "reset_held"), f"unknown setup {setup!r}"
                thread = context.get((case.get("path") or {}).get("thread_id", ""), "")
                path = spec.path_template.replace("{thread_id}", thread)
                kwargs: dict[str, Any] = {} if payload is None else {"json": payload}
                if setup == "reset_held":
                    with reset_gate_of(env.app).hold():
                        response = client.request(spec.method.upper(), path, headers=headers, **kwargs)
                else:
                    response = client.request(spec.method.upper(), path, headers=headers, **kwargs)
            assert response.status_code == case["status"], f"{operation_id}/{case['name']}: {response.text}"
            if "code" in case:
                assert response.json()["error"]["code"] == case["code"], f"{operation_id}/{case['name']}"
            assert str(case["status"]) in spec.responses, (
                f"{operation_id}/{case['name']}: status not documented"
            )
            assert_matches(response, operation_id)
            covered[operation_id].add(str(case["status"]))
            ran += 1

    for operation_id, wanted in ROUTE_STATUSES.items():
        assert wanted <= covered[operation_id], (
            f"{operation_id}: statuses without a case: {wanted - covered[operation_id]}"
        )
    assert examples <= named, f"request examples without a case: {examples - named}"
    assert ran >= 20
