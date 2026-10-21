"""AEA-02 AC-4: enums and status literals carry exactly their sources' values."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, get_args

import pytest
import yaml

from meridian.domain.actions import ActionKind
from meridian.domain.common import (
    ApiErrorCode,
    HandoffReason,
    Priority,
    ProviderName,
    ToolErrorCode,
    ToolKind,
)
from meridian.domain.staff import DemoRole, StaffRole
from meridian.domain.turn import (
    CheckKind,
    DegradeReason,
    ExportStatus,
    GateKind,
    GateResult,
    SignalName,
    TurnOutcome,
    TurnTrace,
)

OPENAPI = Path(__file__).resolve().parents[3] / "docs/ux/03-structure/ui-contracts.openapi.yaml"


def _schemas() -> dict[str, Any]:
    loaded = yaml.load(OPENAPI.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)  # noqa: S506  read-only plain-string load
    schemas: dict[str, Any] = loaded["components"]["schemas"]
    return schemas


_ENUM_EXPECTED: dict[str, tuple[type[StrEnum], set[str]]] = {
    "ActionKind": (
        ActionKind,
        {"booked", "moved", "cancelled", "change_request_sent", "case_opened", "followup_saved", "verified"},
    ),
    "GateKind": (
        GateKind,
        {
            "ai_paused",
            "safety",
            "burning_ask",
            "burning_answer",
            "danger_rule",
            "person",
            "code_entry",
            "locate",
            "card_choice",
            "free_text",
        },
    ),
    "HandoffReason": (
        HandoffReason,
        {
            "safety",
            "danger",
            "burning_unclear",
            "customer_requested_person",
            "refund",
            "billing_dispute",
            "complaint_or_manager",
            "legal_or_chargeback",
            "commercial",
            "late_technician",
            "fee_bearing_change",
            "membership_cancel",
            "unsupported_action",
            "identity_unverified",
            "ai_failure",
            "burning_ruled_out",
        },
    ),
    "Priority": (Priority, {"P0", "P1", "P2", "P3", "P4"}),
    "ToolErrorCode": (
        ToolErrorCode,
        {
            "not_allowed",
            "bad_arguments",
            "unknown_tool",
            "not_verified",
            "not_shown",
            "fee_bearing",
            "outside_service_area",
            "slot_taken",
            "booking_cap",
            "identical_call",
            "tool_failed",
            "wrong_service_type",
            "not_owned",
        },
    ),
    "ToolKind": (
        ToolKind,
        {"kb_search", "account_read", "slot_search", "book", "move", "cancel", "change_request"},
    ),
    "SignalName": (
        SignalName,
        {
            "safety_reply_sent",
            "case_write_failed",
            "classifier_fallback",
            "planner_fallback",
            "specialist_failed",
            "brake_fired",
            "responder_fallback",
            "brief_failed",
        },
    ),
    "DemoRole": (DemoRole, {"customer", "representative", "supervisor", "owner"}),
    "StaffRole": (StaffRole, {"representative", "supervisor", "owner"}),
}
_ENUM_COUNTS = {
    "ActionKind": 7,
    "GateKind": 10,
    "HandoffReason": 16,
    "Priority": 5,
    "ToolErrorCode": 13,
    "ToolKind": 7,
    "SignalName": 8,
    "DemoRole": 4,
    "StaffRole": 3,
}


@pytest.mark.parametrize("name", list(_ENUM_EXPECTED))
def test_enum_value_sets(name: str) -> None:
    enum_type, expected = _ENUM_EXPECTED[name]
    actual = {member.value for member in enum_type}
    print(name, sorted(actual))
    assert actual == expected
    assert len(actual) == _ENUM_COUNTS[name]


def test_literal_value_sets() -> None:
    assert len(get_args(CheckKind)) == 7
    assert set(get_args(CheckKind)) == {
        "completion",
        "fact",
        "brief_fact",
        "brief_quote",
        "gate",
        "classifier",
        "brake",
    }
    assert set(get_args(ProviderName)) == {"anthropic", "openrouter_jev"}


def test_api_error_code_equals_openapi() -> None:
    schemas = _schemas()
    api = set(schemas["ApiError"]["properties"]["error"]["properties"]["code"]["enum"])
    notice = set(schemas["Notice"]["properties"]["code"]["enum"])
    block = set(schemas["ErrorBlock"]["allOf"][1]["properties"]["code"]["enum"])
    expected = api | notice | block
    actual = {member.value for member in ApiErrorCode}
    print("openapi:", sorted(expected))
    print("python:", sorted(actual))
    assert actual == expected
    assert len(actual) == 35
    assert "STAFF_AUTH_REQUIRED" not in actual


def test_status_values_equal_do6() -> None:
    """DO-6 *Status values* (lines 52-54) and models.md section 4."""
    gate = {"clear", "safety", "burning_unclear", "danger", "person_requested", "ai_paused"}
    outcome = {"answered", "acted", "safety_reply", "handed_off", "to_staff", "degraded_handoff"}
    degrade = {"model_error", "tool_error", "timeout", "brake", "spend_cap", "rate_limit"}
    export = {"off", "sent", "failed"}
    assert set(get_args(GateResult)) == gate
    assert set(get_args(TurnOutcome)) == outcome
    assert set(get_args(DegradeReason)) == degrade
    assert set(get_args(ExportStatus)) == export
    gate_annotation: Any = TurnTrace.model_fields["gate_result"].annotation
    outcome_annotation: Any = TurnTrace.model_fields["outcome"].annotation
    assert gate_annotation == GateResult
    assert outcome_annotation == TurnOutcome
    assert set(get_args(TurnTrace.model_fields["degrade_reason"].annotation)) - {type(None)} == {
        DegradeReason
    }
