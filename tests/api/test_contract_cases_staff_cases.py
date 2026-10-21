"""AEA-45 AC-19 (local driver): tests/contract/cases/staff_cases.py holds the server cases for the eight staff case
operations. AEA-59's runner reads the same data; this file drives every case through the in-process app with service
doubles programmed to the state each drive names (mock-tested). Failure mode guarded: contract (each case yields the
status and error code it names, valid against the OpenAPI, and every documented status has a case)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import JsonValue

from meridian.domain.common import ApiErrorCode
from meridian.domain.staff import DemoRole
from meridian.domain.views import CaseActionRejected
from meridian.services.staff import FlagRejected
from tests.api.openapi_check import load_contract
from tests.api.staff_cases_support import (
    CaseNotFoundStandIn,
    StaffCasesHarness,
    activity_result,
    case_detail,
    case_rejected,
    flag_record,
    flag_records,
    oversight_view,
    queue_view,
    staff_app,
    summary,
)
from tests.api.web_shell_support import (
    assert_matches,
    error_body,
    login,
    make_client,
    make_settings,
    session_cookie_value,
)
from tests.contract.cases.staff_cases import CASES, ROUTE_FILE
from tests.contract.openapi_cases import check_cases_mapping
from tests.contract.openapi_variants import request_examples

OPERATIONS = {
    "getQueue",
    "getCase",
    "applyCaseAction",
    "recordContactActivity",
    "createFlag",
    "listFlags",
    "reviewFlag",
    "getOversight",
}
METHODS = {
    "getQueue": "GET",
    "getCase": "GET",
    "applyCaseAction": "POST",
    "recordContactActivity": "POST",
    "createFlag": "POST",
    "listFlags": "GET",
    "reviewFlag": "PATCH",
    "getOversight": "GET",
}
TEMPLATES = {
    "getQueue": "/api/staff/queue",
    "getCase": "/api/staff/cases/{reference}",
    "applyCaseAction": "/api/staff/cases/{reference}/actions",
    "recordContactActivity": "/api/staff/cases/{reference}/activities",
    "createFlag": "/api/staff/flags",
    "listFlags": "/api/staff/flags",
    "reviewFlag": "/api/staff/flags/{flag_id}",
    "getOversight": "/api/staff/oversight",
}
NOT_FOUND: dict[str, JsonValue] = {"reference": "MHC-C-9999"}

Program = Callable[[StaffCasesHarness], None]


def _set(attr: str, value: Any, on: str = "cases") -> Program:
    def program(h: StaffCasesHarness) -> None:
        setattr(getattr(h, on), attr, value)

    return program


def _detail_missing(h: StaffCasesHarness) -> None:
    h.cases.detail_raises = CaseNotFoundStandIn("MHC-C-9999")


_CASE_MISSING = CaseActionRejected(code=ApiErrorCode.CASE_NOT_FOUND, details=NOT_FOUND)
_ACTIONS_422 = {
    "release_without_reason": "REASON_REQUIRED",
    "wait_without_wake_up": "WAKE_UP_REQUIRED",
    "resolve_without_outcome": "OUTCOME_REQUIRED",
}
SERVICE_ANSWERS: dict[tuple[str, str], Program] = {
    ("getQueue", "representative_reads"): _set("queue_result", queue_view()),
    ("getQueue", "supervisor_reads"): _set("queue_result", queue_view()),
    ("getCase", "representative_reads"): _set("detail_result", case_detail()),
    ("getCase", "owner_reads"): _set("detail_result", case_detail()),
    ("getCase", "unknown_case"): _detail_missing,
    ("getOversight", "supervisor_reads"): _set("oversight_result", oversight_view()),
    ("applyCaseAction", "claim"): _set("apply_result", summary("CLAIMED")),
    ("applyCaseAction", "claim_seeded"): _set("apply_result", summary("CLAIMED")),
    ("applyCaseAction", "wait"): _set("apply_result", summary("WAITING")),
    ("applyCaseAction", "resolve"): _set("apply_result", summary("RESOLVED")),
    ("applyCaseAction", "release"): _set(
        "apply_result", summary("CLAIMED", lifecycle="unassigned", owner=None, version=5)
    ),
    ("applyCaseAction", "assign"): _set("apply_result", summary("ASSIGNED")),
    ("applyCaseAction", "change_priority"): _set("apply_result", summary("PRIORITY_CHANGED")),
    ("applyCaseAction", "unknown_case"): _set("apply_result", _CASE_MISSING),
    ("applyCaseAction", "stale_version"): _set(
        "apply_result", case_rejected("applyCaseAction", "409", "VERSION_CONFLICT")
    ),
    ("applyCaseAction", "claimed_by_supervisor"): _set(
        "apply_result", case_rejected("applyCaseAction", "409", "CASE_ALREADY_CLAIMED")
    ),
    ("applyCaseAction", "resolve_before_claim"): _set(
        "apply_result", case_rejected("applyCaseAction", "409", "NOT_ALLOWED_IN_STATE")
    ),
    **{
        ("applyCaseAction", name): _set("apply_result", case_rejected("applyCaseAction", "422", code))
        for name, code in _ACTIONS_422.items()
    },
    ("recordContactActivity", "call_logged"): _set("activity_result", activity_result()),
    ("recordContactActivity", "unknown_case"): _set("activity_result", _CASE_MISSING),
    ("recordContactActivity", "not_claimed"): _set(
        "activity_result", case_rejected("recordContactActivity", "409", "NOT_ALLOWED_IN_STATE")
    ),
    ("recordContactActivity", "stale_version"): _set(
        "activity_result", case_rejected("recordContactActivity", "409", "VERSION_CONFLICT")
    ),
    ("createFlag", "flag_answer"): _set("flag_result", flag_record(), "flags"),
    ("createFlag", "unknown_case"): _set(
        "flag_result",
        FlagRejected(code="CASE_NOT_FOUND", field=None, constraint=None, details={"reference": "MHC-C-9999"}),
        "flags",
    ),
    ("createFlag", "message_outside_case"): _set(
        "flag_result",
        FlagRejected(
            code="VALIDATION_ERROR", field="message_id", constraint="not a message of this case", details=None
        ),
        "flags",
    ),
    ("listFlags", "representative_lists"): _set("list_result", flag_records(), "flags"),
    ("listFlags", "owner_lists"): _set("list_result", flag_records(), "flags"),
    ("reviewFlag", "review"): _set("review_result", flag_record("reviewFlag", "REVIEWED", "200"), "flags"),
    ("reviewFlag", "unknown_flag"): _set(
        "review_result",
        FlagRejected(code="FLAG_NOT_FOUND", field=None, constraint=None, details={"flag_id": "flg-999999"}),
        "flags",
    ),
}


def test_staff_cases_contract_cases_drive_and_cover(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """contract (AC-19): every drive yields its status and code; all documented statuses are covered."""
    assert check_cases_mapping(CASES, "cases/staff_cases.py") == []
    assert ROUTE_FILE == "staff_cases"
    assert set(CASES) == OPERATIONS
    contract = load_contract()
    covered: dict[str, set[str]] = {op: set() for op in OPERATIONS}
    codes: dict[str, set[str]] = {op: set() for op in OPERATIONS}
    total = 0
    for op, spec in CASES.items():
        drives: Any = spec["drives"]
        print(f"{op}: {len(drives)} cases")
        for drive in drives:
            covered[op].add(str(drive["status"]))
            codes[op].add(str(drive.get("code")))
    for op in OPERATIONS:
        assert covered[op] == set(contract.operations[op].responses), op
    assert {"VERSION_CONFLICT", "CASE_ALREADY_CLAIMED", "NOT_ALLOWED_IN_STATE"} <= codes["applyCaseAction"]
    assert set(_ACTIONS_422.values()) <= codes["applyCaseAction"]
    assert {"NOT_ALLOWED_IN_STATE", "VERSION_CONFLICT"} <= codes["recordContactActivity"]

    for op, spec in CASES.items():
        examples = request_examples(op)
        for drive in spec["drives"]:  # type: ignore[attr-defined]
            name = drive["name"]
            h = staff_app(monkeypatch, make_settings(tmp_path / f"{op}-{name}"))
            pre = tuple(drive["preconditions"])
            body = drive.get("body")
            payload = (
                None if body is None else (examples[body["example"]] if "example" in body else body["raw"])
            )
            path = TEMPLATES[op].format(**drive.get("path", {}))
            program = SERVICE_ANSWERS.get((op, name))
            if program is not None:
                program(h)
            with make_client(h.app) as client:
                headers: dict[str, str] = {}
                if "login" in pre:
                    token = session_cookie_value(login(client, h.settings))
                    assert token is not None
                    headers = {"Cookie": f"mhc_session={token}"}
                    for word in pre:
                        if word.startswith("role:"):
                            h.store.set_role(token, DemoRole(word.split(":", 1)[1]))
                response = client.request(METHODS[op], path, headers=headers, json=payload)
            assert response.status_code == drive["status"], f"{op}/{name}: {response.text}"
            if "code" in drive:
                error_body(response, drive["status"], drive["code"])
            assert_matches(response, op)
            if program is None:
                assert h.cases.calls == [], f"{op}/{name}"
                assert h.flags.calls == [], f"{op}/{name}"
            print(f"{op}/{name}: {drive['status']}")
            total += 1
    expected = 0
    for spec in CASES.values():
        expected_drives: Any = spec["drives"]
        expected += len(expected_drives)
    assert total == expected
