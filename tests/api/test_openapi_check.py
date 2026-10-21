"""AEA-23 AC-24 and AC-27: the one OpenAPI response validator and the YAML 1.2 loader behind it (web section 13).

Failure modes guarded: invariant (the validator rejects what the contract forbids and accepts the contract's own
examples; error codes match the signed enum), regression (YAML 1.1 turned timestamps and yes/no/on/off into
datetime and bool objects, and 22:00 into the integer 1320).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from meridian.domain.common import ApiErrorCode
from tests.api.openapi_check import assert_response_matches, load_contract, load_document

HEADERS = {"X-Request-ID": "x"}


def json_examples(document: Any) -> Iterator[tuple[str, str, str, Any]]:
    """(operationId, status, example name, value) for every application/json response example."""
    shared = document["components"]["responses"]
    for item in document["paths"].values():
        for operation in item.values():
            if not isinstance(operation, dict) or "operationId" not in operation:
                continue
            for status, response in operation["responses"].items():
                if "$ref" in response:
                    response = shared[response["$ref"].rsplit("/", 1)[1]]
                media = response.get("content", {}).get("application/json", {})
                for name, example in (media.get("examples") or {}).items():
                    if isinstance(example, dict) and "value" in example:
                        yield operation["operationId"], str(status), str(name), example["value"]


def test_validator_rejects_and_accepts() -> None:
    """invariant (AC-24): three rejections name the OpenAPI version; every example in the contract passes."""
    document = load_document()
    version = str(document["info"]["version"])
    contract = load_contract()
    assert contract.version == version

    undocumented_status = httpx.Response(418, json={"anything": 1}, headers=HEADERS)
    broken_schema = httpx.Response(200, json={"session": 1, "landing": 5}, headers=HEADERS)
    unknown_code = httpx.Response(
        401,
        json={
            "error": {"code": "NOT_A_REAL_CODE", "field": None, "constraint": None, "details": None},
            "request_id": "x",
        },
        headers=HEADERS,
    )
    for label, response, operation in (
        ("undocumented status", undocumented_status, "logout"),
        ("schema break", broken_schema, "login"),
        ("unknown error code", unknown_code, "login"),
    ):
        with pytest.raises(AssertionError) as raised:
            assert_response_matches(response, operation)
        message = str(raised.value)
        print(f"{label}: {message[:140]}")
        assert version in message, label
        assert operation in message, label

    checked = 0
    for operation, status, name, value in json_examples(document):
        request_id = value.get("request_id", "x") if isinstance(value, dict) else "x"
        response = httpx.Response(int(status), json=value, headers={"X-Request-ID": str(request_id)})
        try:
            assert_response_matches(response, operation)
        except AssertionError as exc:
            raise AssertionError(f"contract example {operation} {status} {name} was rejected: {exc}") from exc
        checked += 1
    print(f"contract examples accepted: {checked}")
    assert checked >= 200


def test_error_codes_match_openapi() -> None:
    """invariant (AC-24, WEB-9): Contract.error_codes is the HTTP members of ApiErrorCode, which is the ApiError enum."""
    document = load_document()
    schemas = document["components"]["schemas"]
    notice = set(schemas["Notice"]["properties"]["code"]["enum"])
    block = set(schemas["ErrorBlock"]["allOf"][1]["properties"]["code"]["enum"])
    api_error = set(schemas["ApiError"]["properties"]["error"]["properties"]["code"]["enum"])
    http_members = {member.value for member in ApiErrorCode} - notice - block
    contract = load_contract()
    print(f"{len(contract.error_codes)} HTTP error codes")
    assert contract.error_codes == http_members
    assert contract.error_codes == api_error


def test_loader_keeps_yaml12_strings() -> None:
    """regression (AC-24, R-W-9): timestamps, yes/no and ON/OFF stay strings; 22:00 does not become 1320."""
    document = load_document()
    examples = {(op, status, name): value for op, status, name, value in json_examples(document)}

    at = examples[("startChatSession", "201", "STARTED")]["greeting"]["at"]
    print(f"STARTED greeting.at = {at!r} ({type(at).__name__})")
    assert isinstance(at, str) and at == "2026-10-16T14:20:00-05:00"

    option = examples[("submitTurn", "200", "BURNING_CHECK")]["blocks"][0]["options"][0]["option"]
    print(f"BURNING_CHECK option = {option!r} ({type(option).__name__})")
    assert isinstance(option, str) and option == "yes"

    staffing = document["paths"]["/api/demo/staffing"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]
    print(f"getStaffing example names = {sorted(map(repr, staffing))}")
    assert set(staffing) == {"ON", "OFF"}
    assert all(isinstance(key, str) for key in staffing)

    start = examples[("getMonitoring", "200", "DEFAULT")]["alert_config"]["quiet_hours"]["start"]
    print(f"quiet_hours.start = {start!r} ({type(start).__name__})")
    assert isinstance(start, str) and start == "22:00"


def test_contract_keeps_yaml_strings() -> None:
    """invariant (AC-27): no datetime or date anywhere in the loaded document; true and false stay booleans."""
    document = load_document()
    dates: list[Any] = []
    booleans: list[bool] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(key)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, (dt.datetime, dt.date)):
            dates.append(node)
        elif isinstance(node, bool):
            booleans.append(node)

    walk(document)
    greeting = next(
        value
        for op, status, name, value in json_examples(document)
        if (op, status, name) == ("startChatSession", "201", "STARTED")
    )["greeting"]["at"]
    print(
        f"datetime/date objects: {len(dates)}; booleans: {len(booleans)}; greeting.at = {greeting!r} ({type(greeting).__name__})"
    )
    assert dates == []
    assert isinstance(greeting, str)
    assert True in booleans and False in booleans
    assert document["components"]["schemas"]["SessionInfo"]["properties"]["authenticated"]["const"] is True
