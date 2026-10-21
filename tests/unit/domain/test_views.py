"""AEA-02b: the case and demo view types match their OpenAPI schemas and validate the signed examples (read only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pydantic
import pytest
import yaml

from meridian.domain import views
from meridian.domain.common import ApiErrorCode

OPENAPI = Path(__file__).resolve().parents[3] / "docs/ux/03-structure/ui-contracts.openapi.yaml"


class _WireLoader(yaml.SafeLoader):
    """SafeLoader that leaves timestamps as the strings they are on the wire (JSON has no date type)."""


_WireLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
DOC: Any = yaml.load(OPENAPI.read_text(encoding="utf-8"), Loader=_WireLoader)  # noqa: S506  SafeLoader subclass
SCHEMAS: dict[str, Any] = DOC["components"]["schemas"]
OPERATIONS: dict[str, Any] = {
    op["operationId"]: op for item in DOC["paths"].values() for op in item.values() if isinstance(op, dict)
}


def _object(node: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in node:
        return _object(SCHEMAS[node["$ref"].rsplit("/", 1)[-1]])
    return dict(node.get("properties", {}))


def _non_null(node: dict[str, Any]) -> dict[str, Any]:
    if "oneOf" in node:
        return next(option for option in node["oneOf"] if option.get("type") != "null")
    return node


def _descend(path: str) -> dict[str, Any]:
    head, *rest = path.split(".")
    node: dict[str, Any] = SCHEMAS[head]
    for step in rest:
        node = _non_null(_object(node)[step.removesuffix("[]")])
        if step.endswith("[]"):
            node = _non_null(node["items"])
    return _object(node)


PAIRS: list[tuple[type[pydantic.BaseModel], str]] = [
    (views.StaffingView, "Staffing"),
    (views.StaffingChange, "StaffingResponse"),
    (views.ClockView, "DemoClock"),
    (views.ClockAdvanced, "ClockAdvanceResponse"),
    (views.ResetDone, "ResetResponse"),
    (views.PriorityView, "Priority"),
    (views.QueueRow, "QueueRow"),
    (views.QueueView, "QueueResponse"),
    (views.CaseSummaryView, "CaseSummary"),
    (views.BriefItemView, "BriefItem"),
    (views.BriefHeadingView, "BriefHeading"),
    (views.BriefView, "Brief"),
    (views.CaseSource, "CaseSource"),
    (views.ChatLineView, "ChatLine"),
    (views.Activity, "Activity"),
    (views.PromiseFollowUp, "PromiseRecord.follow_up"),
    (views.PromiseHistoryItem, "PromiseRecord.history[]"),
    (views.PromiseRecord, "PromiseRecord"),
    (views.LiveStateView, "LiveState"),
    (views.CaseIdentityView, "CaseDetail.identity"),
    (views.OtherCase, "CaseDetail.other_cases[]"),
    (views.CaseDetail, "CaseDetail"),
    (views.CaseAction, "CaseActionRequest"),
    (views.CaseActionRejected, "ApiError.error"),
    (views.FollowUpChoice, "FollowUpRequest"),
    (views.ActivityIn, "ActivityRequest"),
    (views.ActivityResult, "ActivityResponse"),
    (views.Alert, "Alert"),
    (views.Lane, "Lane"),
    (views.OversightLanes, "OversightResponse.lanes"),
    (views.OversightView, "OversightResponse"),
]


@pytest.mark.parametrize(("cls", "path"), PAIRS, ids=[f"{c.__name__}<-{p}" for c, p in PAIRS])
def test_view_fields_match_openapi(cls: type[pydantic.BaseModel], path: str) -> None:
    expected = set(_descend(path))
    actual = set(cls.model_fields)
    print(f"{cls.__name__}: {sorted(actual)}")
    assert actual == expected, (sorted(actual - expected), sorted(expected - actual))


def _body(content: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = content["content"]["application/json"]
    return body


# (operationId, "request" or an HTTP status, model, unwrap the ApiError envelope)
EXAMPLE_SOURCES: list[tuple[str, str, type[pydantic.BaseModel], bool]] = [
    ("getQueue", "200", views.QueueView, False),
    ("getCase", "200", views.CaseDetail, False),
    ("getOversight", "200", views.OversightView, False),
    ("applyCaseAction", "request", views.CaseAction, False),
    ("applyCaseAction", "409", views.CaseActionRejected, True),
    ("applyCaseAction", "422", views.CaseActionRejected, True),
    ("recordContactActivity", "request", views.ActivityIn, False),
    ("recordContactActivity", "201", views.ActivityResult, False),
    ("recordContactActivity", "409", views.CaseActionRejected, True),
    ("saveFollowUp", "request", views.FollowUpChoice, False),
    ("setStaffing", "200", views.StaffingChange, False),
    ("getStaffing", "200", views.StaffingView, False),
    ("getDemoClock", "200", views.ClockView, False),
    ("advanceDemoClock", "200", views.ClockAdvanced, False),
    ("resetDemo", "200", views.ResetDone, False),
]


def _examples() -> list[Any]:
    cases = []
    for op_id, where, model, unwrap in EXAMPLE_SOURCES:
        op = OPERATIONS[op_id]
        content = op["requestBody"] if where == "request" else op["responses"][where]
        for name, example in _body(content)["examples"].items():
            cases.append(pytest.param(model, example["value"], unwrap, id=f"{op_id}-{where}-{name}"))
    return cases


@pytest.mark.parametrize(("model", "value", "unwrap"), _examples())
def test_signed_openapi_examples_validate(model: type[pydantic.BaseModel], value: Any, unwrap: bool) -> None:
    payload = value["error"] if unwrap else value
    parsed = model.model_validate(payload)
    # The wire form round-trips: nothing an example carries is dropped or invented.
    assert model.model_validate(parsed.model_dump(mode="json")) == parsed


def test_example_inventory_is_not_empty() -> None:
    assert len(_examples()) >= 40


def test_error_codes_are_the_api_error_enum() -> None:
    rejected = views.CaseActionRejected(code=ApiErrorCode.VERSION_CONFLICT)
    assert (rejected.field, rejected.constraint, rejected.details) == (None, None, None)
    with pytest.raises(pydantic.ValidationError):
        views.CaseActionRejected.model_validate({"code": "NOT_A_CODE"})


def test_optional_request_fields_default_to_none() -> None:
    action = views.CaseAction(action="claim", expected_version=3)
    assert (action.reason, action.wake_up_at, action.outcome, action.assignee, action.priority) == (None,) * 5
    assert views.ActivityIn(kind="call", outcome="reached", expected_version=1).note is None


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (
            views.CaseAction,
            {"action": "join_chat", "expected_version": 1},
        ),  # live actions are not case actions
        (views.CaseAction, {"action": "claim"}),  # expected_version is required
        (views.CaseAction, {"action": "claim", "expected_version": 1, "assignee": "owner"}),
        (views.CaseAction, {"action": "claim", "expected_version": 1, "extra": 1}),
        (views.FollowUpChoice, {"channel": "sms", "destination": "general", "window": "any"}),
        (views.ActivityIn, {"kind": "call", "outcome": "reached"}),
        (views.ActivityIn, {"kind": "chat", "outcome": "reached", "expected_version": 1}),
        (views.StaffingView, {"mode": "on_shift", "label": "x", "banner": None}),
        (views.StaffingView, {"mode": "nobody_online", "label": "x"}),  # banner is required (nullable)
    ],
)
def test_invalid_payloads_are_rejected(model: type[pydantic.BaseModel], payload: dict[str, Any]) -> None:
    with pytest.raises(pydantic.ValidationError):
        model.model_validate(payload)


def test_brief_view_has_exactly_eight_headings() -> None:
    example = next(iter(_body(OPERATIONS["getCase"]["responses"]["200"])["examples"].values()))["value"]
    brief = example["brief"]
    views.BriefView.model_validate(brief)
    for headings in (brief["headings"][:7], [*brief["headings"], brief["headings"][0]]):
        with pytest.raises(pydantic.ValidationError):
            views.BriefView.model_validate({**brief, "headings": headings})


def test_views_are_frozen() -> None:
    clock = views.ClockAdvanced.model_validate(
        {"now": "2026-10-16T14:20:00-05:00", "label": "Fri Oct 16, 2026 · 2:20 pm", "became_overdue": 0}
    )
    with pytest.raises(pydantic.ValidationError):
        clock.became_overdue = 1  # type: ignore[misc]


def test_activity_label_is_the_demo_label() -> None:
    base = {
        "activity_id": "a1",
        "kind": "call",
        "outcome": "reached",
        "note": None,
        "at": "2026-10-16T14:20:00-05:00",
        "by": "Riley",
    }
    assert views.Activity.model_validate({**base, "label": "Demo: recorded, not sent"}).by == "Riley"
    with pytest.raises(pydantic.ValidationError):
        views.Activity.model_validate({**base, "label": "Sent"})
