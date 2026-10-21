"""AEA-47 AC-11 (local driver): tests/contract/cases/staff_clock.py holds the server cases for `advanceDemoClock`.

AEA-59's runner reads the same data later; until it lands this file drives every case through the in-process app.
Failure mode guarded: invariant (every named request example and every documented error status has a case, and each
case produces the status it names, valid against the OpenAPI).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from meridian.domain.staff import DemoRole
from tests.api.openapi_check import load_contract, load_document
from tests.api.staff_clock_support import ADVANCE_PATH, clock_app
from tests.api.web_shell_support import (
    assert_matches,
    cookie_header,
    login,
    make_client,
    make_settings,
    reset_gate_of,
    session_cookie_value,
)
from tests.contract.cases.staff_clock import CASES, ROUTE_FILE


def test_staff_clock_cases_drive_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-11): each case yields its status and code; every example and documented error is covered."""
    assert ROUTE_FILE == "staff_clock"
    cases: dict[str, Any] = dict(CASES)
    assert set(cases) == {"advanceDemoClock"}
    examples = load_document()["paths"][ADVANCE_PATH]["post"]["requestBody"]["content"]["application/json"][
        "examples"
    ]
    contract = load_contract()
    sent_examples: set[str] = set()
    covered: set[str] = set()
    ok_steps: list[str] = []
    ran = 0

    for case in cases["advanceDemoClock"]["drives"]:
        settings = make_settings(tmp_path / case["name"])
        h = clock_app(monkeypatch, settings)
        with make_client(h.app) as client:
            headers: dict[str, str] = {}
            for step in case["preconditions"]:
                if step == "login":
                    found = session_cookie_value(login(client, settings))
                    assert found
                    token = found
                    headers = cookie_header(token)
                elif step.startswith("role:"):
                    h.store.set_role(token, DemoRole(step.split(":", 1)[1]))
                else:
                    raise AssertionError(f"unknown precondition {step!r}")
            body = case["body"]
            if "raw" in body:
                payload = body["raw"]
            else:
                assert body["example"] in examples, f"{body['example']!r} is not a named request example"
                sent_examples.add(body["example"])
                payload = examples[body["example"]]["value"]
            if case.get("setup") == "reset_gate_held":
                with reset_gate_of(h.app).hold():
                    response = client.post(ADVANCE_PATH, headers=headers, json=payload)
            else:
                assert "setup" not in case, case["setup"]
                response = client.post(ADVANCE_PATH, headers=headers, json=payload)
        assert response.status_code == case["status"], f"{case['name']}: {response.text}"
        if "code" in case:
            assert response.json()["error"]["code"] == case["code"], case["name"]
        assert_matches(response, "advanceDemoClock")
        covered.add(str(case["status"]))
        if case["status"] == 200:
            assert len(h.demo.calls) == 1
            ok_steps.append(h.demo.calls[0].step)
        else:
            assert h.demo.calls == []
        ran += 1
        print(f"advanceDemoClock/{case['name']}: {response.status_code}")

    documented_errors = {s for s in contract.operations["advanceDemoClock"].responses if int(s) >= 400}
    assert documented_errors <= covered, (
        f"documented error statuses without a case: {documented_errors - covered}"
    )
    assert "200" in covered
    assert set(examples) <= sent_examples
    assert ok_steps == ["next_business_morning", "plus_4h", "plus_1h"]
    assert ran == 7
