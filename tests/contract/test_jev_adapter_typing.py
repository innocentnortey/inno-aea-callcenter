"""AEA-18 AC-6 [invariant]: JevAdapter satisfies ChoiceModel and is rejected where the other two ports are required.

This module is checked by the project type checker (mypy strict, warn_unused_ignores). The two assignments below that
the checker must reject carry the only two suppression comments in the file; if JevAdapter ever gained the other
ports' methods, those comments would become unused and the type check would fail.
"""

from __future__ import annotations

import httpx
from pydantic import SecretStr

from meridian.adapters.models.openrouter_jev import JevAdapter
from meridian.ports.models import ChoiceModel, StructuredModel, ToolCallingModel


def _ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={})


def test_jev_adapter_port_assignments() -> None:
    adapter = JevAdapter(
        httpx.Client(transport=httpx.MockTransport(_ok)),
        api_key=SecretStr("test-openrouter-key-not-real-0001"),
        model="typesafe/jev-1.13",
    )
    choice: ChoiceModel = adapter
    _structured: StructuredModel = adapter  # type: ignore[assignment]
    _tools: ToolCallingModel = adapter  # type: ignore[assignment]

    assert choice.provider == "openrouter_jev"
    for missing in ("structured", "tool_step", "start", "append"):
        assert not hasattr(adapter, missing), missing
