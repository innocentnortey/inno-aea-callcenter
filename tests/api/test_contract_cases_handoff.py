"""AEA-42 AC-21 (local driver): tests/contract/cases/handoff.py holds the server cases for `requestPerson` and
`saveFollowUp`. AEA-59's runner reads the same data later; until it lands this file drives every case in-process.
Failure mode guarded: invariant (each documented error status and each named request example has a case that
produces its status, valid against the OpenAPI).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from tests.api.handoff_support import (
    FOLLOW_UP_PATH,
    HANDOFF_PATH,
    customer_token,
    handoff_app,
    request_example,
    session_id_of,
    thread_for,
)
from tests.api.openapi_check import load_contract, load_document
from tests.api.web_shell_support import assert_matches, cookie_header, make_client
from tests.contract.cases.handoff import CASES, ROUTE_FILE
from tests.fixtures.sqlite import temp_sqlite
from tests.services.person_request_support import end_thread, verify_thread

PATHS = {"requestPerson": (HANDOFF_PATH, "post"), "saveFollowUp": (FOLLOW_UP_PATH, "put")}


def test_handoff_cases_drive_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-21): each case yields its status and code; every example and documented error status is covered."""
    assert ROUTE_FILE == "handoff"
    cases: dict[str, Any] = dict(CASES)
    assert set(cases) == {"requestPerson", "saveFollowUp"}
    document = load_document()
    contract = load_contract()
    named: set[str] = set()
    covered: dict[str, set[str]] = {op: set() for op in cases}
    ran = 0
    for operation_id, entry in cases.items():
        path, method = PATHS[operation_id]
        examples = set(
            document["paths"][path][method]["requestBody"]["content"]["application/json"]["examples"]
        )
        spec = contract.operations[operation_id]
        assert entry["drives"], operation_id
        for case in entry["drives"]:
            with temp_sqlite() as db:
                h = handoff_app(
                    monkeypatch,
                    tmp_path / operation_id / case["name"],
                    db,
                    handoff_fails=case.get("setup") == "handoff_fails",
                )
                token = customer_token(h)
                pre = set(case["preconditions"])
                assert pre <= {"login", "thread", "open_case", "verified", "ended", "unknown"}, pre
                thread = str(uuid.uuid4())
                if "ended" in pre:
                    thread = end_thread(db, demo_session=session_id_of(h, token))
                elif "unknown" not in pre:
                    thread_id = thread_for(h, token)
                    thread = str(thread_id)
                    if "verified" in pre:
                        verify_thread(db, thread_id)
                headers = cookie_header(token) if "login" in pre else {}
                body = case["body"]
                kwargs: dict[str, Any] = {}
                with make_client(h.app) as client:
                    if "open_case" in pre:
                        opened = client.post(
                            HANDOFF_PATH.format(thread_id=thread),
                            json=request_example(HANDOFF_PATH, "post", "BUTTON"),
                            headers=headers,
                        )
                        assert opened.status_code == 200
                    if body is not None and "raw" in body:
                        kwargs["json"] = body["raw"]
                    elif body is not None:
                        assert body["example"] in examples, f"{body['example']!r} is not a named example"
                        named.add(f"{operation_id}:{body['example']}")
                        payload = request_example(path, method, body["example"])
                        if body.get("turn_id") == "new":
                            payload["turn_id"] = str(uuid.uuid4())
                        kwargs["json"] = payload
                    response = client.request(
                        spec.method.upper(),
                        spec.path_template.format(thread_id=thread),
                        headers=headers,
                        **kwargs,
                    )
                assert response.status_code == case["status"], (
                    f"{operation_id}/{case['name']}: {response.text}"
                )
                if "code" in case:
                    assert response.json()["error"]["code"] == case["code"], f"{operation_id}/{case['name']}"
                assert_matches(response, operation_id)
                covered[operation_id].add(str(case["status"]))
                ran += 1
                print(f"{operation_id}/{case['name']}: {response.status_code}")
        assert {f"{operation_id}:{e}" for e in examples} <= named, f"{operation_id}: example without a case"
    for operation_id in cases:
        documented_errors = {s for s in contract.operations[operation_id].responses if int(s) >= 400}
        assert documented_errors <= covered[operation_id], (
            f"{operation_id}: documented statuses without a case: {documented_errors - covered[operation_id]}"
        )
        assert "200" in covered[operation_id]
    assert ran == 16
