"""AEA-02 PA-2: wire-facing models match their OpenAPI schemas (read only); union discriminators match the mappings."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, get_args

import pydantic
import pytest
import yaml

from meridian.domain import blocks, common, identity, turn

OPENAPI = Path(__file__).resolve().parents[3] / "docs/ux/03-structure/ui-contracts.openapi.yaml"
LOADED: Any = yaml.load(OPENAPI.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)  # noqa: S506  read-only plain-string load
SCHEMAS: dict[str, Any] = LOADED["components"]["schemas"]


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _object(node: dict[str, Any]) -> dict[str, Any]:
    """Properties of an object schema, merging allOf parts and following $ref."""
    if "$ref" in node:
        return _object(SCHEMAS[_ref_name(node["$ref"])])
    merged: dict[str, Any] = {}
    for part in node.get("allOf", []):
        merged.update(_object(part))
    merged.update(node.get("properties", {}))
    return merged


def _non_null(node: dict[str, Any]) -> dict[str, Any]:
    """The non-null branch of a nullable `oneOf`."""
    if "oneOf" in node:
        return next(option for option in node["oneOf"] if option.get("type") != "null")
    return node


def _descend(path: str) -> dict[str, Any]:
    """`Schema`, `Schema.prop`, `Schema.prop[]` and chains of them, to an object's properties."""
    head, *rest = path.split(".")
    node: dict[str, Any] = SCHEMAS[head]
    for step in rest:
        node = _non_null(_object(node)[step.removesuffix("[]")])
        if step.endswith("[]"):
            node = _non_null(node["items"])
    return _object(node)


# (python class, OpenAPI path)
PAIRS: list[tuple[type[pydantic.BaseModel], str]] = [
    (blocks.Speaker, "Speaker"),
    (blocks.SourceChip, "SourceChip"),
    (blocks.Option, "Option"),
    (blocks.Money, "Money"),
    (blocks.FollowUpOptions, "FollowUpOptions"),
    (blocks.FollowUpChannelOption, "FollowUpOptions.channels[]"),
    (blocks.FollowUpWindowOption, "FollowUpOptions.windows[]"),
    (common.FollowUp, "FollowUpView"),
    (blocks.SettledVisit, "SettledVisit"),
    (blocks.SettledRequest, "SettledRequest"),
    (blocks.Write, "Write"),
    (blocks.SettledView, "Settled"),
    (blocks.SettledIdentity, "Settled.identity"),
    (blocks.SettledReplying, "Settled.replying"),
    (blocks.Notice, "Notice"),
    (blocks.TextBlock, "TextBlock"),
    (blocks.SourceChipBlock, "SourceChipBlock"),
    (blocks.SafetyBlock, "SafetyBlock"),
    (blocks.CallKey, "SafetyBlock.call_key"),
    (blocks.ConditionalSafetyBlock, "ConditionalSafetyBlock"),
    (blocks.BurningCheckBlock, "BurningCheckBlock"),
    (blocks.EmergencyLineBlock, "EmergencyLineBlock"),
    (blocks.QuickChecksBlock, "QuickChecksBlock"),
    (blocks.QuickCheck, "QuickChecksBlock.checks[]"),
    (blocks.UrgencyQuestionsBlock, "UrgencyQuestionsBlock"),
    (blocks.UrgencyQuestion, "UrgencyQuestionsBlock.questions[]"),
    (blocks.WherePromptBlock, "WherePromptBlock"),
    (blocks.LocatePromptBlock, "LocatePromptBlock"),
    (blocks.CodePromptBlock, "CodePromptBlock"),
    (blocks.SlotCardBlock, "SlotCardBlock"),
    (blocks.SlotDay, "SlotCardBlock.days[]"),
    (blocks.SlotWindow, "SlotCardBlock.days[].windows[]"),
    (blocks.ConfirmationBlock, "ConfirmationBlock"),
    (blocks.AppointmentBlock, "AppointmentBlock"),
    (blocks.CancelledBlock, "CancelledBlock"),
    (blocks.AccountCardBlock, "AccountCardBlock"),
    (blocks.AccountInvoice, "AccountCardBlock.invoice"),
    (blocks.AccountInvoiceLine, "AccountCardBlock.invoice.lines[]"),
    (blocks.AccountMembership, "AccountCardBlock.membership"),
    (blocks.AccountWarranty, "AccountCardBlock.warranty"),
    (blocks.ChangeRequestBlock, "ChangeRequestBlock"),
    (blocks.ShownWindow, "ChangeRequestBlock.windows_shown[]"),
    (blocks.HandoffBlock, "HandoffBlock"),
    (blocks.LiveQueuedBlock, "LiveQueuedBlock"),
    (blocks.FailureOfferBlock, "FailureOfferBlock"),
    (blocks.NoInfoBlock, "NoInfoBlock"),
    (blocks.NoticeBlock, "NoticeBlock"),
    (blocks.ErrorBlock, "ErrorBlock"),
    (blocks.SessionEndedBlock, "SessionEndedBlock"),
    (turn.TextPayload, "TextPayload"),
    (turn.ChoicePayload, "ChoicePayload"),
    (turn.CodePayload, "CodePayload"),
    (turn.FormPayload, "FormPayload"),
    (identity.FormValues, "FormPayload.values"),
    (identity.InboxMessage, "InboxMessage"),
]


@pytest.mark.parametrize(("cls", "path"), PAIRS, ids=[f"{c.__name__}<-{p}" for c, p in PAIRS])
def test_wire_models_match_openapi(cls: type[pydantic.BaseModel], path: str) -> None:
    properties = _descend(path)
    expected = set(properties)
    if cls is identity.InboxMessage:
        expected -= {"body"}  # the route renders the body (graph-tools section 5)
    actual = set(cls.model_fields)
    print(f"{cls.__name__}: {sorted(actual)}")
    assert actual == expected, (sorted(actual - expected), sorted(expected - actual))
    for name, schema in properties.items():
        if name not in cls.model_fields or "const" not in schema:
            continue
        default = cls.model_fields[name].default
        assert str(default).lower() == str(schema["const"]).lower(), name


def _mapping_keys(schema_name: str, discriminator: str) -> set[str]:
    discriminated = SCHEMAS[schema_name]["discriminator"]
    assert discriminated["propertyName"] == discriminator
    return set(discriminated["mapping"])


def _literal_values(member: Any, field: str) -> str:
    (value,) = get_args(member.model_fields[field].annotation)
    assert isinstance(value, str)
    return value


def test_union_discriminators_match_openapi() -> None:
    module = importlib.import_module("meridian.domain.blocks")
    members = get_args(get_args(module.ReplyBlock)[0])
    assert {_literal_values(m, "type") for m in members} == _mapping_keys("ReplyBlock", "type")
    assert len(members) == 24

    payloads = get_args(get_args(turn.TurnPayload)[0])
    assert {_literal_values(m, "kind") for m in payloads} == _mapping_keys("TurnPayload", "kind")
