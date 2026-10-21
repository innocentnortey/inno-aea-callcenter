"""GraphDeps and ModelsStatus (AEA-21 PA-5; graph-core section 4, R-G-13)."""

from __future__ import annotations

import dataclasses

import pytest

from meridian.agent.context import GraphDeps, ModelsStatus


def test_graph_deps_fields() -> None:
    names = [f.name for f in dataclasses.fields(GraphDeps)]
    print("GraphDeps fields:", names)
    assert names == [
        "gateway",
        "retrieval",
        "uow",
        "identity",
        "scheduling",
        "handoff",
        "brief",
        "demo",
        "limits",
        "trace",
        "specialists",
        "cases",
        "ledger",
    ]


def test_graph_deps_is_frozen() -> None:
    from tests.graph._spine_doubles import RecordingSink, make_deps

    deps = make_deps(RecordingSink())
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(deps, "limits", deps.limits)  # noqa: B010


class _OnlyOneMethod:
    def models_disabled(self) -> bool:
        return True


def test_models_status_is_structural() -> None:
    status: ModelsStatus = _OnlyOneMethod()
    assert status.models_disabled() is True
