"""AEA-48 contract cases (AC-11): drives tests/contract/cases/reads.py until AEA-59's runner is merged."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from meridian.domain.staff import DemoRole
from meridian.web.deps import get_rate_limiter
from tests.api.openapi_check import load_contract
from tests.api.reads_support import (
    EXAMPLE_NAMES,
    FakeMetricsReads,
    RefusingLimiter,
    example,
    get_read,
    reads_app,
)
from tests.api.web_shell_support import (
    assert_matches,
    cookie_header,
    login,
    make_client,
    make_settings,
    reset_gate_of,
    session_cookie_value,
)
from tests.contract.cases.reads import CASES, ROUTE_FILE


def test_reads_cases_drive_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-11): each case yields its status and code; every documented error status is covered."""
    assert ROUTE_FILE == "reads"
    assert set(CASES) == {"getOwnerMetrics", "getMonitoring", "getLatestEval"}
    covered: dict[str, set[str]] = {op: set() for op in CASES}
    total = 0
    for op, spec in CASES.items():
        drives: tuple[dict[str, Any], ...] = spec["drives"]  # type: ignore[assignment]
        for case in drives:
            settings = make_settings(tmp_path / op / case["name"])
            reads = FakeMetricsReads()
            if "reader_example" in case:
                assert case["reader_example"] in EXAMPLE_NAMES[op]
                reads.returns[op] = example(op, case["reader_example"])
            h = reads_app(monkeypatch, settings, reads=reads)
            headers: dict[str, str] = {}
            with make_client(h.app) as client:
                token = ""
                for step in case["preconditions"]:
                    if step == "login":
                        token = session_cookie_value(login(client, settings)) or ""
                        assert token
                        headers = cookie_header(token)
                    elif step.startswith("role:"):
                        h.store.set_role(token, DemoRole(step.split(":", 1)[1]))
                    else:
                        raise AssertionError(f"unknown precondition {step!r}")
                setup = case.get("setup")
                if setup == "reset_gate_held":
                    with reset_gate_of(h.app).hold():
                        response = get_read(client, op, headers)
                elif setup == "rate_limited":
                    h.app.dependency_overrides[get_rate_limiter] = lambda: RefusingLimiter()
                    response = get_read(client, op, headers)
                elif setup is None:
                    response = get_read(client, op, headers)
                else:
                    raise AssertionError(f"unknown setup {setup!r}")
            assert response.status_code == case["status"], (op, case["name"], response.text)
            if "code" in case:
                assert response.json()["error"]["code"] == case["code"]
            assert_matches(response, op)
            if case["status"] == 200:
                assert reads.calls == [op]
                assert response.json() == reads.returns[op]
            else:
                assert reads.calls == []
            covered[op].add(str(case["status"]))
            total += 1
            print(f"{op}/{case['name']}: {response.status_code}")
    contract = load_contract()
    for op in CASES:
        documented = {s for s in contract.operations[op].responses if int(s) >= 400}
        assert documented <= covered[op], (op, documented - covered[op])
        assert "200" in covered[op]
    assert total == 13
