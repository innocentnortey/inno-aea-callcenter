"""AEA-43 contract cases (AC-15): drives tests/contract/cases/demo.py on AEA-23's app with doubles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from meridian.policy.limits import Limits, WebLimits
from meridian.services.reset_gate import ResetAlreadyRunning
from meridian.web.middleware import RateLimiter
from tests.api.demo_support import ResetFailedStub, demo_app
from tests.api.openapi_check import load_contract
from tests.api.web_shell_support import (
    assert_matches,
    cookie_header,
    login,
    make_client,
    make_settings,
    reset_gate_of,
    session_cookie_value,
)
from tests.contract.cases.demo import CASES, LOCAL_ONLY_DRIVES, ROUTE_FILE
from tests.contract.openapi_cases import check_cases_mapping, expected_route_file
from tests.contract.openapi_variants import request_examples


def test_demo_cases_drive_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-15): each case yields its status and code on AEA-23's app with doubles; every documented error
    status is covered; the file passes AEA-59's format check."""
    assert ROUTE_FILE == "demo"
    assert set(CASES) == {"listDemoInbox", "getStaffing", "setStaffing", "getDemoClock", "resetDemo"}
    assert check_cases_mapping(CASES, "cases/demo.py") == []
    assert all(expected_route_file(op) == "demo" for op in CASES)
    contract = load_contract()
    covered: dict[str, set[str]] = {op: set() for op in CASES}
    total = 0
    for op in CASES:
        drives: tuple[dict[str, Any], ...] = (*CASES[op]["drives"], *LOCAL_ONLY_DRIVES.get(op, ()))  # type: ignore[misc]
        spec = contract.operations[op]
        for case in drives:
            settings = make_settings(tmp_path / op / case["name"])
            limiter = None
            if case.get("setup") == "rate_limited" and op != "resetDemo":
                limiter = RateLimiter(WebLimits(reads_per_session_per_min=1, reads_per_ip_per_min=100))
            h = demo_app(monkeypatch, settings, limiter=limiter)
            payload: Any = None
            body = case["body"]
            if isinstance(body, dict) and "example" in body:
                payload = request_examples(op)[body["example"]]
            elif isinstance(body, dict) and "raw" in body:
                payload = body["raw"]
            with make_client(h.app) as client:
                headers: dict[str, str] = {}
                for word in case["preconditions"]:
                    if word != "login":
                        raise AssertionError(f"unknown precondition {word!r}")
                    token = session_cookie_value(login(client, settings))
                    assert token
                    headers = cookie_header(token)

                def send(
                    client: Any = client,
                    headers: dict[str, str] = headers,
                    payload: Any = payload,
                    spec: Any = spec,
                ) -> Any:
                    kwargs: dict[str, Any] = {"headers": headers}
                    if payload is not None:
                        kwargs["json"] = payload
                    return client.request(spec.method.upper(), spec.path_template, **kwargs)

                setup = case.get("setup")
                if setup is None:
                    response = send()
                elif setup == "reset_gate_held":
                    if op == "resetDemo":
                        h.resets.outcomes.append(ResetAlreadyRunning())
                    with reset_gate_of(h.app).hold():
                        response = send()
                elif setup == "rate_limited":
                    first_sends = Limits().web.resets_per_ip if op == "resetDemo" else 1
                    for _ in range(first_sends):
                        assert send().status_code == 200
                    response = send()
                elif setup == "reset_fails":
                    h.resets.outcomes.append(ResetFailedStub())
                    response = send()
                else:
                    raise AssertionError(f"unknown setup {setup!r}")
            assert response.status_code == case["status"], (op, case["name"], response.text)
            if "code" in case:
                assert response.json()["error"]["code"] == case["code"]
            assert_matches(response, op)
            covered[op].add(str(case["status"]))
            total += 1
            print(f"{op}/{case['name']}: {response.status_code}")
    for op in CASES:
        documented = {s for s in contract.operations[op].responses if int(s) >= 400}
        assert documented <= covered[op], (op, documented - covered[op])
    assert total == 21  # 20 in CASES plus the local-only RESET_FAILED drive
