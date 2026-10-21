"""Shared test doubles for the DO-4 ports (AEA-11). Import from here: `from tests.fakes import FixedClock`."""

from tests.fakes.clock import CHICAGO, WORKED_PAIRS_NOW, FixedClock
from tests.fakes.index import FakeIndex
from tests.fakes.models import (
    FakeAnthropicChoiceModel,
    FakeChoiceModel,
    FakeStructuredModel,
    FakeToolModel,
    ScriptedFailure,
    ScriptExhaustedError,
    provider_call,
)
from tests.fakes.trace import InMemoryTraceSink, RecordedModelCall, RecordedNode, RecordedTurn

__all__ = [
    "CHICAGO",
    "WORKED_PAIRS_NOW",
    "FakeAnthropicChoiceModel",
    "FakeChoiceModel",
    "FakeIndex",
    "FakeStructuredModel",
    "FakeToolModel",
    "FixedClock",
    "InMemoryTraceSink",
    "RecordedModelCall",
    "RecordedNode",
    "RecordedTurn",
    "ScriptExhaustedError",
    "ScriptedFailure",
    "provider_call",
]
