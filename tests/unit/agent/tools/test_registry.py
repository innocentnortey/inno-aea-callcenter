"""AEA-22: `ToolRegistry` start-up checks (AC-5, S-1, S-2) and its lookup API (frozen tests, written first).

The module under test is imported through a fixture so this file collects before `dispatch.py` exists.
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any, cast

import pytest

from meridian.domain.tools import ToolKind
from meridian.ports.models import ToolCall
from meridian.ports.runtime import UnitOfWorkFactory
from tests.unit.agent.tools.dispatch_doubles import (
    EmptyArgs,
    ExecutorDouble,
    KbArgs,
    Recorder,
    RecordingUow,
    ScopeLeakCustomerArgs,
    ScopeLeakMessageArgs,
    ScopeLeakNestedArgs,
    make_def,
    make_scope,
)


@pytest.fixture(scope="module")
def dispatch() -> ModuleType:
    return importlib.import_module("meridian.agent.tools.dispatch")


def _kb(name: str = "kb_search") -> Any:
    return make_def(name, ToolKind.KB_SEARCH, KbArgs, ExecutorDouble(name, Recorder()))


@pytest.mark.parametrize(
    "bad_name",
    ["", "Read", "read-invoices", "read invoices", "r1", "a" * 65],
    ids=lambda n: f"len{len(n)}_{n[:6]}",
)
def test_registry_rejects_bad_names(dispatch: ModuleType, bad_name: str) -> None:
    """boundary (AC-5): a name outside [a-z_]{1,64} fails at construction, not at the first call."""
    with pytest.raises(ValueError):
        dispatch.ToolRegistry(
            [make_def(bad_name, ToolKind.KB_SEARCH, KbArgs, ExecutorDouble("x", Recorder()))]
        )


def test_registry_rejects_duplicate_name(dispatch: ModuleType) -> None:
    """boundary (AC-5): two defs with one name."""
    with pytest.raises(ValueError):
        dispatch.ToolRegistry([_kb(), _kb()])


def test_registry_check_covers(dispatch: ModuleType) -> None:
    """invariant (AC-5): a kind with no registered tool is a start-up error; a covered set returns None."""
    registry = dispatch.ToolRegistry([_kb()])
    with pytest.raises(ValueError):
        registry.check_covers(frozenset({ToolKind.BOOK}))
    assert registry.check_covers(frozenset({ToolKind.KB_SEARCH})) is None


def test_valid_registry_never_raises_from_dispatch(dispatch: ModuleType) -> None:
    """invariant (AC-5): a registry that built fine never raises from `dispatch` (one ok call, one unknown)."""
    uow = RecordingUow()
    registry = dispatch.ToolRegistry([_kb()])
    dispatcher = dispatch.ToolDispatcher(registry, cast(UnitOfWorkFactory, uow))
    calls = [
        ToolCall(id="c1", name="kb_search", args={"query": "filters"}),
        ToolCall(id="c2", name="no_such_tool", args={}),
    ]
    out = dispatcher.dispatch(calls, kinds=frozenset({ToolKind.KB_SEARCH}), scope=make_scope(None))
    assert [d.tool_call_id for d in out] == ["c1", "c2"]


@pytest.mark.parametrize(
    "args_model",
    [ScopeLeakCustomerArgs, ScopeLeakMessageArgs, ScopeLeakNestedArgs],
    ids=["customer_id", "message_id", "nested_shown_slot_ids"],
)
def test_registry_rejects_scope_fields(dispatch: ModuleType, args_model: type) -> None:
    """invariant (S-1): a model-fillable argument named like a ToolCallScope field is refused at start-up."""
    bad = make_def("leaky", ToolKind.KB_SEARCH, args_model, ExecutorDouble("leaky", Recorder()))
    with pytest.raises(ValueError):
        dispatch.ToolRegistry([bad])


@pytest.mark.parametrize(
    "kind",
    [ToolKind.ACCOUNT_READ, ToolKind.BOOK, ToolKind.MOVE, ToolKind.CANCEL, ToolKind.CHANGE_REQUEST],
    ids=lambda k: k.value,
)
def test_registry_rejects_open_private_kinds(dispatch: ModuleType, kind: ToolKind) -> None:
    """invariant (S-2, R-14): an account or write kind with requires_verified=False must not start."""
    bad = make_def(
        "open_tool", kind, EmptyArgs, ExecutorDouble("open_tool", Recorder()), requires_verified=False
    )
    with pytest.raises(ValueError):
        dispatch.ToolRegistry([bad])


@pytest.mark.parametrize("kind", [ToolKind.KB_SEARCH, ToolKind.SLOT_SEARCH], ids=lambda k: k.value)
def test_registry_allows_open_public_kinds(dispatch: ModuleType, kind: ToolKind) -> None:
    """boundary (S-2): the public kinds may be unverified."""
    ok = make_def(
        "public_tool", kind, EmptyArgs, ExecutorDouble("public_tool", Recorder()), requires_verified=False
    )
    dispatch.ToolRegistry([ok])


def test_registry_get_and_for_kinds(dispatch: ModuleType) -> None:
    """invariant: `get` finds by name or returns None; `for_kinds` filters by kind and sorts by name."""
    kb = _kb()
    zed = make_def("zed_read", ToolKind.ACCOUNT_READ, EmptyArgs, ExecutorDouble("zed_read", Recorder()))
    abe = make_def("abe_read", ToolKind.ACCOUNT_READ, EmptyArgs, ExecutorDouble("abe_read", Recorder()))
    registry = dispatch.ToolRegistry([zed, kb, abe])
    assert registry.get("kb_search") is kb
    assert registry.get("nope") is None
    assert [d.name for d in registry.for_kinds(frozenset({ToolKind.ACCOUNT_READ}))] == [
        "abe_read",
        "zed_read",
    ]
    assert registry.for_kinds(frozenset()) == ()
