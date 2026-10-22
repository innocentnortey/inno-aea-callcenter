"""Strict tool schemas reach the API without keywords it rejects (2026-10-22 rehearsal fix).

The knowledge specialist's report_facts schema carried ``maxItems: 5``; Anthropic answered HTTP 400
"tools.1.custom: For 'array' type, property 'maxItems' is not supported" (req_011CgGmTkC3SU8nDfxx47YHf).
No network: traffic goes through the ``_anthropic_fixtures`` mock transport.
"""

from __future__ import annotations

import json
from typing import Any

from meridian.domain.specialists import KnowledgeReport
from meridian.ports.models import ToolSchema
from tests.contract._anthropic_fixtures import KB_SCHEMA, SUCCESS_CONTENT, adapter_for, ok, tool_request

_REJECTED = ("maxItems", "minItems", "maxLength", "minLength", "pattern")


def _keywords(node: Any) -> list[str]:
    if isinstance(node, dict):
        return [k for k in node if k in _REJECTED] + [k for v in node.values() for k in _keywords(v)]
    if isinstance(node, list):
        return [k for v in node for k in _keywords(v)]
    return []


def test_strict_tool_schema_constraints_moved_out() -> None:
    """[regression]: report_facts' maxItems/maxLength/pattern are not sent as schema keywords; KB_SCHEMA is unchanged."""
    report = KnowledgeReport.model_json_schema()
    assert _keywords(report)  # the source schema really has them
    adapter, rec = adapter_for(ok(SUCCESS_CONTENT["tool_step"], stop_reason="tool_use"))
    base = tool_request(adapter.start("What does Comfort Club cost?"))
    req = base.model_copy(
        update={
            "tools": (
                *base.tools,
                ToolSchema(name="report_facts", description="Report.", input_schema=report),
            )
        }
    )
    adapter.tool_step(req, timeout_s=8.0)
    tools = rec.bodies()[0]["tools"]
    assert tools[0]["input_schema"] == KB_SCHEMA
    assert all(t["strict"] is True for t in tools)
    assert _keywords(tools[1]["input_schema"]) == []
    assert "maxItems: 5" in json.dumps(tools[1]["input_schema"]["properties"]["points"])
