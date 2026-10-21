"""AEA-59 server runner: every operationId driven through the real app, each response checked against the OpenAPI.

Levels: the drives are `integrated with a scripted model` (real app on a first-boot DB copy, guards on; no model is
reached until AEA-51). The case-file checks are `mock-tested (static)`. A drive whose route is not registered, or that
meets `RuntimeError("not bound: <name>")`, is skipped with exactly that reason; `CONTRACT_STRICT=1` (the wave-merge form)
turns both into failures. Cases live in `tests/contract/cases/<route>.py`, one file per route ticket; see its README.
"""

from __future__ import annotations

import ast
import re
import socket
import uuid
from pathlib import Path
from typing import Any

import pytest

from tests.api.openapi_check import assert_response_matches, load_contract
from tests.api.web_shell_support import demo_pair, rand_word
from tests.contract.openapi_cases import (
    README_PATH,
    Drive,
    all_drives,
    case_file_problems,
    check_cases_mapping,
    completeness,
    expected_route_file,
    is_public,
    load_case_files,
    local_driver_reason,
    missing_operations,
    staff_role_for,
)
from tests.contract.openapi_driver import (
    GUARD_MESSAGE,
    AppRun,
    install_exception_tap,
    install_socket_guard,
    real_app,
    run_drive,
    send,
)
from tests.contract.openapi_variants import contract_strict, operation_node, request_examples

FILES = load_case_files()
DRIVES = all_drives(FILES)
RUNNABLE = [d for d in DRIVES if local_driver_reason(d) is None and isinstance(d.spec.get("status"), int)]
SUCCESS = [d for d in RUNNABLE if 200 <= d.status < 300]
ROUTE_ERRORS = [d for d in RUNNABLE if d.status >= 300]
UNAUTH_OPS = sorted(op for op in load_contract().operations if not is_public(op))
VALIDATION_OPS = sorted(
    op
    for op, spec in load_contract().operations.items()
    if "400" in spec.responses and "requestBody" in operation_node(op)
)


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    return install_socket_guard(monkeypatch)


@pytest.fixture
def taps(monkeypatch: pytest.MonkeyPatch) -> list[BaseException]:
    return install_exception_tap(monkeypatch)


def test_case_files_are_well_formed() -> None:
    problems = case_file_problems(FILES)
    for problem in problems:
        print(problem)
    assert problems == []


def test_every_operation_has_a_case() -> None:
    found, missing, unknown = completeness(FILES)
    for stem, ids in found.items():
        print(f"cases/{stem}.py: {len(ids)} ({', '.join(ids)})")
    print(f"missing ({len(missing)} of {len(load_contract().operations)}):")
    for line in missing:
        print(f"  {line}")
    print("local-driver only:")
    for drive in DRIVES:
        reason = local_driver_reason(drive)
        if reason:
            print(f"  {drive.id} - {reason}")
    assert unknown == [], f"cases name operationIds the OpenAPI lacks: {unknown}"
    if contract_strict():
        assert missing == [], "operations with no case:\n" + "\n".join(missing)


def test_completeness_names_a_removed_case() -> None:
    ids = [op for f in FILES for op in f.cases]
    removed = ids[0]
    lines = missing_operations(set(ids) - {removed})
    assert any(
        line.startswith(removed) and line.endswith(f"tests/contract/cases/{expected_route_file(removed)}.py")
        for line in lines
    )


def test_case_format_example_is_valid() -> None:
    text = README_PATH.read_text("utf-8")
    block = text.split("<!-- example-case:start -->", 1)[1].split("<!-- example-case:end -->", 1)[0]
    code = "\n".join(line for line in block.splitlines() if not line.startswith("```"))
    cases = ast.literal_eval(code.split("=", 1)[1].strip())
    assert check_cases_mapping(cases, "cases/README.md") == []


@pytest.mark.parametrize("drive", SUCCESS, ids=lambda d: d.id)
def test_success_matches_contract(drive: Drive, tmp_path: Path, taps: list[BaseException]) -> None:
    with real_app(tmp_path, taps) as run:
        print(run_drive(run, drive))


@pytest.mark.parametrize("drive", ROUTE_ERRORS, ids=lambda d: d.id)
def test_route_cases_match_contract(drive: Drive, tmp_path: Path, taps: list[BaseException]) -> None:
    with real_app(tmp_path, taps) as run:
        print(run_drive(run, drive))


def _unsigned_path(op: str) -> str:
    template = load_contract().operations[op].path_template
    for name in re.findall(r"\{(\w+)\}", template):
        value = "MHC-C-0001" if name == "reference" else _uuid()
        template = template.replace("{" + name + "}", value)
    return template


def _uuid() -> str:
    return str(uuid.uuid4())


def _assert_error(run: AppRun, op: str, response: Any, status: int, code: str) -> None:
    body = response.json() if response.content else {}
    seen = body.get("error", {}).get("code") if isinstance(body, dict) else None
    assert response.status_code == status and seen == code, (
        f"{op}: expected {status} {code}, got {response.status_code} {seen}"
    )
    assert_response_matches(response, op)


@pytest.mark.parametrize("op", ["login", *UNAUTH_OPS])
def test_unauthenticated_matches_contract(op: str, tmp_path: Path, taps: list[BaseException]) -> None:
    with real_app(tmp_path, taps) as run:
        if op == "login":
            pair = demo_pair(run.settings)
            body: dict[str, Any] | None = {
                "json": {"username": pair["username"], "password": rand_word(14, "pw")}
            }
            response = send(run, op, path=_unsigned_path(op), token=None, body=body)
            _assert_error(run, op, response, 401, "LOGIN_FAILED")
            return
        examples = list(request_examples(op).values())
        body = {"json": examples[0]} if examples else None
        response = send(run, op, path=_unsigned_path(op), token=None, body=body)
        _assert_error(run, op, response, 401, "UNAUTHENTICATED")


@pytest.mark.parametrize("op", VALIDATION_OPS)
def test_validation_error_matches_contract(op: str, tmp_path: Path, taps: list[BaseException]) -> None:
    template = load_contract().operations[op].path_template
    role = staff_role_for(op)
    pre: list[str] = [] if is_public(op) else ["login"]
    if role is not None:
        pre.append(f"role:{role}")
    if "{thread_id}" in template:
        pre.append("thread")
    spec: dict[str, Any] = {
        "name": "malformed_body",
        "status": 400,
        "code": "VALIDATION_ERROR",
        "preconditions": tuple(pre),
        "body": {"text": "not json"},
    }
    if "{reference}" in template:
        spec["path"] = {"reference": "seeded_case"}
    with real_app(tmp_path, taps) as run:
        print(run_drive(run, Drive(op, "<generated>", spec)))


def test_no_outbound_connections(socket_guard: list[str], tmp_path: Path, taps: list[BaseException]) -> None:
    assert socket_guard == []
    with socket.socket() as probe, pytest.raises(ConnectionRefusedError, match="AEA-59 socket guard"):
        probe.connect(("192.0.2.1", 9))
    with pytest.raises(socket.gaierror, match="AEA-59 socket guard"):
        socket.getaddrinfo("example.invalid", 443)
    assert socket_guard == ["192.0.2.1", "example.invalid"]
    socket_guard.clear()
    assert GUARD_MESSAGE
    with real_app(tmp_path, taps) as run:
        pair = demo_pair(run.settings)
        run.client.post("/api/login", json=pair)
        run.client.post("/api/chat/sessions")
        run.client.get(f"/api/chat/sessions/{_uuid()}")
    assert socket_guard == []
    print("refused connects: 0")
