"""AEA-44 AC-18 (local driver): tests/contract/cases/staff_session.py holds the server cases for CON-10.

AEA-59's runner reads the same data later; until it lands this file drives every case through the in-process app.
Failure mode guarded: invariant (each case yields its status and body; every request example and every documented
status has a case).
"""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest

from tests.api.openapi_check import load_contract, load_document
from tests.api.staff_session_support import (
    StaffHarness,
    example,
    login_token,
    staff_app,
    switch,
    tab,
    without_signed_in_at,
)
from tests.api.web_shell_support import assert_matches, error_body, make_client, reset_gate_of
from tests.contract.cases.staff_session import CASES, ROUTE_FILE
from tests.fixtures.sqlite import temp_sqlite

_AS = {"as_representative": "representative", "as_supervisor": "supervisor", "as_owner": "owner"}


def test_staff_session_cases_drive_documented_statuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert ROUTE_FILE == "staff_session"
    cases: dict[str, Any] = dict(CASES)
    assert set(cases) == {"getSession", "listDemoRoles", "switchRole"}
    contract = load_contract()
    document = load_document()
    request_examples = set(
        document["paths"]["/api/session/role"]["put"]["requestBody"]["content"]["application/json"][
            "examples"
        ]
    )
    response_examples = {
        name
        for name in document["paths"]["/api/session/role"]["put"]["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
    }
    used_requests: set[str] = set()
    used_responses: set[str] = set()
    covered: dict[str, set[str]] = {op: set() for op in cases}
    ran = 0

    for operation_id, entry in cases.items():
        spec = contract.operations[operation_id]
        assert entry["drives"], f"{operation_id} has no cases"
        for case in entry["drives"]:
            with temp_sqlite() as db:
                h: StaffHarness = staff_app(monkeypatch, tmp_path / operation_id / case["name"], db)
                with make_client(h.app) as client:
                    headers: dict[str, str] = {}
                    token = ""
                    for step in case["preconditions"]:
                        if step == "login":
                            token = login_token(client, h.settings)
                            headers = tab(token)
                        else:
                            assert step in _AS, f"unknown precondition {step!r}"
                            assert switch(client, token, _AS[step]).status_code == 200
                    body = case["body"]
                    kwargs: dict[str, Any] = {}
                    if body is not None and "raw" in body:
                        kwargs["json"] = body["raw"]
                    elif body is not None:
                        assert body["example"] in request_examples
                        used_requests.add(body["example"])
                        kwargs["json"] = example("switchRole", body["example"], request=True)
                    gate = (
                        reset_gate_of(h.app).hold()
                        if case.get("setup") == "reset_gate_held"
                        else nullcontext()
                    )
                    with gate:
                        response = client.request(
                            spec.method.upper(), spec.path_template, headers=headers, **kwargs
                        )
            assert response.status_code == case["status"], f"{operation_id}/{case['name']}: {response.text}"
            if "code" in case:
                error_body(response, case["status"], case["code"])
            assert_matches(response, operation_id)
            if "response_example" in case:
                name = case["response_example"]
                expected = without_signed_in_at(example(operation_id, name))
                assert without_signed_in_at(response.json()) == expected, f"{operation_id}/{case['name']}"
                if operation_id == "switchRole":
                    used_responses.add(name)
            covered[operation_id].add(str(case["status"]))
            ran += 1
            print(f"{operation_id}/{case['name']}: {response.status_code}")

    for operation_id in cases:
        documented = {s for s in contract.operations[operation_id].responses}
        assert documented <= covered[operation_id], (
            f"{operation_id}: documented statuses without a case: {documented - covered[operation_id]}"
        )
    assert request_examples <= used_requests, (
        f"request examples without a case: {request_examples - used_requests}"
    )
    assert {n for n in response_examples if n.startswith("TO_")} <= used_responses
    print(f"staff_session cases run: {ran}")
