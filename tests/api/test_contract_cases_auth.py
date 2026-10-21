"""AEA-23 AC-29 (local driver): tests/contract/cases/auth.py holds the server cases for `login` and `logout`.

AEA-59's runner reads the same data later; until it lands this file drives every case through the in-process app.
Failure mode guarded: invariant (every named request example and every documented error status has a case, and each
case produces the status it names, valid against the OpenAPI).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from meridian.policy.limits import WebLimits
from tests.api.openapi_check import load_contract, load_document
from tests.api.web_shell_support import (
    FakeSessionStore,
    assert_matches,
    cookie_header,
    demo_pair,
    login,
    make_client,
    make_settings,
    rand_word,
    session_cookie_value,
    web_app,
)
from tests.contract.cases.auth import CASES, ROUTE_FILE


def _payload(body: dict[str, Any], settings: Any) -> dict[str, str]:
    pair = demo_pair(settings)
    if body.get("credentials") == "wrong_password":
        return {"username": pair["username"], "password": rand_word(10)}
    assert body.get("credentials") == "configured", body
    return pair


def test_auth_cases_drive_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-29): each case yields its status and code; every example and documented error status is covered."""
    assert ROUTE_FILE == "auth"
    cases: dict[str, Any] = dict(CASES)
    assert set(cases) == {"login", "logout"}
    document = load_document()
    contract = load_contract()
    login_examples = set(
        document["paths"]["/api/login"]["post"]["requestBody"]["content"]["application/json"]["examples"]
    )
    named_examples: set[str] = set()
    covered: dict[str, set[str]] = {"login": set(), "logout": set()}
    ran = 0

    for operation_id, entry in cases.items():
        spec = contract.operations[operation_id]
        assert entry["drives"], f"{operation_id} has no cases"
        for case in entry["drives"]:
            settings = make_settings(tmp_path / operation_id / case["name"])
            app = web_app(monkeypatch, settings, store=FakeSessionStore())
            with make_client(app) as client:
                headers: dict[str, str] = {}
                for step in case["preconditions"]:
                    assert step == "login", f"unknown precondition {step!r}"
                    token = session_cookie_value(login(client, settings))
                    assert token
                    headers = cookie_header(token)
                if case.get("setup") == "login_rejects_exhausted":
                    for _ in range(WebLimits().login_rejects_per_ip):
                        wrong = client.post(
                            "/api/login", json={**demo_pair(settings), "password": rand_word(10)}
                        )
                        assert wrong.status_code == 401
                body = case["body"]
                kwargs: dict[str, Any] = {}
                if body is None:
                    pass
                elif "raw" in body:
                    kwargs["json"] = body["raw"]
                elif "text" in body:
                    kwargs["content"] = body["text"]
                    headers = {**headers, "Content-Type": "application/json"}
                else:
                    assert body["example"] in login_examples, (
                        f"{body['example']!r} is not a named request example"
                    )
                    named_examples.add(body["example"])
                    kwargs["json"] = _payload(body, settings)
                response = client.request(spec.method.upper(), spec.path_template, headers=headers, **kwargs)
            assert response.status_code == case["status"], f"{operation_id}/{case['name']}: {response.text}"
            if "code" in case:
                assert response.json()["error"]["code"] == case["code"], f"{operation_id}/{case['name']}"
            assert_matches(response, operation_id)
            covered[operation_id].add(str(case["status"]))
            ran += 1
            print(f"{operation_id}/{case['name']}: {response.status_code}")

    for operation_id in ("login", "logout"):
        documented_errors = {s for s in contract.operations[operation_id].responses if int(s) >= 400}
        assert documented_errors <= covered[operation_id], (
            f"{operation_id}: documented error statuses without a case: {documented_errors - covered[operation_id]}"
        )
    assert {"200"} <= covered["login"] and {"204"} <= covered["logout"]
    assert login_examples <= named_examples, (
        f"request examples without a case: {login_examples - named_examples}"
    )
    assert ran >= 7
