"""AEA-17 frozen contract tests (part 2): tool round trip, call records, cost, secrets and import bounds.

Split from test_anthropic_adapter.py to stay under the 500-line test cap; no assertion changed.
"""

from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue

from meridian.adapters.models.anthropic import (
    ANTHROPIC_PRICES,
)
from meridian.domain.common import ProviderFailureKind as K
from meridian.ports.models import (
    ProviderCall,
    ProviderMessages,
    TokenPrice,
    ToolCall,
    ToolStep,
)
from tests.contract._anthropic_fixtures import (
    FAKE_KEY,
    MODEL,
    REQUEST_ID,
    SENTINEL,
    SIGNATURE,
    TOOL_CONTENT,
    USAGE,
    adapter_for,
    call,
    case_by_id,
    error_body,
    make,
    message_body,
    ok,
    respond,
    sequence,
    tool_request,
)

ADAPTER_LOGGER = "meridian.adapters.models.anthropic"


def _text(text: str) -> Any:
    return ok([{"type": "text", "text": text}])


def test_tool_step_round_trip() -> None:
    """AC-8, P-4 [invariant]: tool calls parse, assistant content is resent byte-identical, results follow."""
    second = ok([{"type": "text", "text": "Yes, active."}])
    adapter, rec = adapter_for(sequence(ok(TOOL_CONTENT, stop_reason="tool_use"), second))
    messages = adapter.start("Is my membership active?")
    assert messages == ProviderMessages(
        provider="anthropic", model=MODEL, items=({"role": "user", "content": "Is my membership active?"},)
    )
    attempt = adapter.tool_step(tool_request(messages), timeout_s=5.0)
    step = attempt.value
    assert isinstance(step, ToolStep)
    assert step.tool_calls == (
        ToolCall(id="toolu_01", name="kb_search", args={"query": "membership"}),
        ToolCall(id="toolu_02", name="account_read", args=None),
    )
    assert step.text == "Let me check."
    assert step.stop_reason == "tool_use"
    assert step.raw == {"role": "assistant", "content": TOOL_CONTENT}
    raw: Any = step.raw
    assert raw["content"][0]["thinking"] == "  Need the KB.\n"
    assert raw["content"][0]["signature"] == SIGNATURE

    results = [("toolu_01", '{"ok": true}'), ("toolu_02", '{"error": "bad_arguments"}')]
    messages2 = adapter.append(messages, step, results)
    assert messages2.provider == "anthropic"
    assert messages2.model == MODEL
    tool_content = cast("JsonValue", TOOL_CONTENT)
    expected_items: tuple[JsonValue, ...] = (
        *messages.items,
        {"role": "assistant", "content": tool_content},
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "toolu_01", "content": '{"ok": true}'},
                {"type": "tool_result", "tool_use_id": "toolu_02", "content": '{"error": "bad_arguments"}'},
            ],
        },
    )
    assert messages2.items == expected_items
    adapter.tool_step(tool_request(messages2), timeout_s=5.0)
    wire = rec.bodies()[1]["messages"]
    assert wire == list(messages2.items)
    assert wire[1]["content"][0] == TOOL_CONTENT[0]


def test_append_rejects_foreign_messages() -> None:
    """AC-8 [negative]: messages from another provider or model are refused without echoing the model."""
    adapter, _ = adapter_for(ok([]))
    step = ToolStep(text="", tool_calls=(), raw={"role": "assistant", "content": []}, stop_reason="end_turn")
    foreign = (
        ProviderMessages(provider="openrouter_jev", model=MODEL, items=()),
        ProviderMessages(provider="anthropic", model="claude-other-9", items=()),
    )
    for messages in foreign:
        with pytest.raises(ValueError) as excinfo:
            adapter.append(messages, step, [])
        assert "claude-other-9" not in str(excinfo.value)


def test_no_key_or_message_in_failure(caplog: pytest.LogCaptureFixture) -> None:
    """AC-9 [negative]: neither the provider's message nor the API key reaches failures, records, reprs or logs."""
    caplog.set_level(logging.DEBUG)
    ids = [
        "status_400",
        "status_400_spend_limit",
        "status_401",
        "status_402",
        "status_429_bare",
        "status_529",
        "status_500",
    ]
    cases: list[tuple[Any, str | None]] = [(case_by_id(i), REQUEST_ID) for i in ids]
    cases += [(case_by_id("raised_before_request"), None), (case_by_id("raised_after_response"), REQUEST_ID)]
    for case, expected_id in cases:
        adapter, _ = make(case, key=FAKE_KEY) if case.handler is not None else make(case)
        attempt = call("structured", adapter)
        assert attempt.failure is not None, case.id
        texts = [
            attempt.failure.model_dump_json(),
            attempt.record.model_dump_json(),
            repr(attempt.failure),
            repr(attempt.record),
            repr(attempt),
            repr(adapter),
            caplog.text,
        ]
        for text in texts:
            assert SENTINEL not in text, case.id
            assert FAKE_KEY not in text, case.id
        assert attempt.failure.provider_request_id == expected_id, case.id
        assert attempt.record.provider_request_id == expected_id, case.id
    bad_id = respond(
        500,
        json=error_body("api_error", "internal " + SENTINEL),
        headers={"request-id": "req_ok " + SENTINEL},
    )
    attempt = call("structured", adapter_for(bad_id)[0])
    assert attempt.failure is not None
    assert attempt.failure.provider_request_id is None
    assert SENTINEL not in attempt.failure.model_dump_json() + attempt.record.model_dump_json() + caplog.text


def test_call_record_fields_and_cost() -> None:
    """AC-10 [invariant]: per-attempt capture fields, price-table cost, thinking never priced."""
    p = ANTHROPIC_PRICES[MODEL]
    assert p == TokenPrice(input=2.00, output=10.00, cache_write_5m=2.50, cache_read=0.10)
    expected = (1000 * p.input + 500 * p.output + 200 * p.cache_write_5m + 3000 * p.cache_read) / 1_000_000

    a = call("structured", adapter_for(_text('{"text": "x"}'))[0]).record
    assert (
        a.input_tokens,
        a.output_tokens,
        a.cache_write_tokens,
        a.cache_read_tokens,
        a.thinking_tokens,
    ) == (
        1000,
        500,
        200,
        3000,
        120,
    )
    assert a.cost_source == "price_table"
    assert a.status == "ok"
    assert a.failure is None
    assert a.provider_request_id == REQUEST_ID
    assert a.stop_reason == "end_turn"
    assert a.latency_ms >= 0
    assert a.cost_usd == pytest.approx(expected, rel=1e-12)

    more_thinking = dict(USAGE, output_tokens_details={"thinking_tokens": 400})
    handler = respond(
        200, json=message_body(content=[{"type": "text", "text": '{"text": "x"}'}], usage=more_thinking)
    )
    b = call("structured", adapter_for(handler)[0]).record
    assert b.thinking_tokens == 400
    assert b.cost_usd == a.cost_usd

    c_attempt = call("structured", make(case_by_id("status_529"))[0])
    c = c_attempt.record
    assert c.cost_usd == 0.0
    assert (
        c.input_tokens,
        c.output_tokens,
        c.cache_write_tokens,
        c.cache_read_tokens,
        c.thinking_tokens,
    ) == (0,) * 5
    assert c.cost_source == "price_table"
    assert c_attempt.failure is not None
    assert c_attempt.failure.kind == K.OVERLOADED
    assert c_attempt.failure.http_status == 529

    bare_usage = {"input_tokens": 1000, "output_tokens": 500}
    handler = respond(
        200, json=message_body(content=[{"type": "text", "text": '{"text": "x"}'}], usage=bare_usage)
    )
    d = call("structured", adapter_for(handler)[0]).record
    assert d.cache_read_tokens == d.cache_write_tokens == d.thinking_tokens == 0


def test_example_pair_bare_429_and_529() -> None:
    """Example pair [failure/refusal]: a bare 429 is a spend cap (not retryable); a 529 is OVERLOADED."""
    cap = call("structured", make(case_by_id("status_429_bare"))[0])
    assert cap.value is None
    assert cap.failure is not None
    assert cap.failure.kind == K.PROVIDER_SPEND_CAP
    assert cap.failure.retryable is False
    assert cap.record.model == "claude-sonnet-5-5"
    assert cap.record.status == "error"
    assert cap.record.cost_usd == 0.0

    over = call("structured", make(case_by_id("status_529"))[0]).record
    assert type(over) is ProviderCall
    assert over.provider == "anthropic"
    assert over.model == "claude-sonnet-5-5"
    assert over.status == "error"
    assert over.failure is not None
    assert over.failure.kind == K.OVERLOADED


def test_adapter_imports_stay_in_bounds() -> None:
    """P-3 [invariant]: only stdlib, anthropic, pydantic and two meridian modules; no streaming, no exc_info."""
    path = Path(__file__).resolve().parents[2] / "src" / "meridian" / "adapters" / "models" / "anthropic.py"
    source = path.read_text()
    allowed = set(sys.stdlib_module_names) | {"__future__", "anthropic", "pydantic", "meridian"}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in allowed, alias.name
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import"
            module = node.module or ""
            assert module.split(".")[0] in allowed, module
            if module.startswith("meridian"):
                assert module in {"meridian.ports.models", "meridian.domain.common"}, module
    for banned in (
        "openrouter_jev",
        "exc_info",
        "logger.exception",
        ".stream(",
        "stream=True",
        "os.environ",
        "getenv",
    ):
        assert banned not in source, banned
