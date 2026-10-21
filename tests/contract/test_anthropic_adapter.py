"""AEA-17 frozen contract tests: the Anthropic adapter turns a provider response into a typed Attempt.

Every test names the failure mode it guards (boundary / invariant / regression / negative). No network and
no paid call: all traffic goes through ``httpx2.MockTransport`` (see ``_anthropic_fixtures``).
"""

from __future__ import annotations

import json
import logging
import types
from typing import Any

import anthropic
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from meridian.adapters.models.anthropic import (
    CHOICE_EFFORT,
    CHOICE_MAX_TOKENS,
    AnthropicAdapter,
)
from meridian.domain.common import ProviderFailureKind as K
from meridian.policy.limits import Limits
from meridian.ports.models import (
    Attempt,
    ChoiceAnswer,
    ChoiceModel,
    ProviderCall,
    StructuredModel,
    ToolCallingModel,
    ToolTranscript,
)
from meridian.web.container import Container, Key, register_anthropic
from tests.contract._anthropic_fixtures import (
    FAKE_KEY,
    HTTP_CASES,
    KB_SCHEMA,
    METHODS,
    MODEL,
    REQUEST_ID,
    SENTINEL,
    STANDARD_LOG_ATTRS,
    SUCCESS_CONTENT,
    Reply,
    adapter_for,
    body_cases,
    call,
    choice_request,
    error_body,
    make,
    ok,
    plain_client,
    requests_seen,
    respond,
    structured_request,
    tool_request,
)

ADAPTER_LOGGER = "meridian.adapters.models.anthropic"
ALL_CASES = [pytest.param(m, c, id=f"{m}-{c.id}") for m in METHODS for c in (*HTTP_CASES, *body_cases(m))]


def _ports_accept_adapter(
    adapter: AnthropicAdapter,
) -> tuple[ChoiceModel, StructuredModel, ToolCallingModel, ToolTranscript]:
    """P-1 [invariant], static only: mypy proves the adapter satisfies all four ports."""
    return (adapter, adapter, adapter, adapter)


@pytest.mark.parametrize(("method", "case"), ALL_CASES)
def test_never_raises_and_always_records(method: str, case: Any) -> None:
    """AC-1 [invariant]: one HTTP attempt, no exception, a ProviderCall on every outcome."""
    adapter, handle = make(case)
    attempt = call(method, adapter)
    assert isinstance(attempt, Attempt)
    assert type(attempt.record) is ProviderCall
    assert "role" not in ProviderCall.model_fields
    assert "attempt" not in ProviderCall.model_fields
    assert (attempt.failure is None) == (attempt.record.status == "ok")
    assert attempt.record.failure == attempt.failure
    if attempt.failure is not None:
        assert attempt.value is None
    # start() for tool_step makes no HTTP call; exactly one request per method call
    assert requests_seen(handle) == 1


@pytest.mark.parametrize(("method", "case"), [p for p in ALL_CASES if p.values[0] == "structured"])
def test_model_bound_at_construction(method: str, case: Any) -> None:
    """AC-2 [invariant]: record.model is the constructor value, even when the response names another."""
    adapter, _ = make(case)
    attempt = call(method, adapter)
    assert attempt.record.model == MODEL
    assert attempt.record.provider == "anthropic"


def test_model_binding_and_unknown_model() -> None:
    """AC-2 [boundary]: class/instance identity, unknown model refused, model is read-only."""
    adapter, _ = adapter_for(ok([]))
    assert AnthropicAdapter.provider == "anthropic"
    assert adapter.model == MODEL
    with pytest.raises(ValueError):
        AnthropicAdapter(plain_client(), model="claude-unknown")
    with pytest.raises(AttributeError):
        adapter.model = "x"  # type: ignore[misc]


def test_failure_kind_mapping(capsys: pytest.CaptureFixture[str]) -> None:
    """AC-3 [failure/refusal]: the Anthropic failure table (kind, retryable, status, retry-after, id)."""
    for case in HTTP_CASES:
        adapter, _ = make(case)
        failure = call("structured", adapter).failure
        assert failure is not None, case.id
        assert failure.provider == "anthropic", case.id
        assert failure.kind == case.kind, case.id
        assert failure.retryable == case.retryable, case.id
        assert failure.http_status == case.http_status, case.id
        assert failure.retry_after_s == case.retry_after_s, case.id
        assert failure.provider_request_id == case.request_id, case.id
        print(f"{case.id:28} -> {failure.kind.value}")
    capsys.readouterr()


def test_unclassified_400_logs_only_for_unmatched(caplog: pytest.LogCaptureFixture) -> None:
    """AC-3/AC-4 [failure/refusal]: only the plain 400 case logs anthropic_400_unclassified."""
    caplog.set_level(logging.DEBUG)
    for case in HTTP_CASES:
        caplog.clear()
        adapter, _ = make(case)
        call("structured", adapter)
        ours = [r for r in caplog.records if r.name == ADAPTER_LOGGER]
        assert len(ours) == (1 if case.logs_unclassified else 0), case.id


def _status_400(etype: str, message: str, **kw: Any) -> Any:
    return respond(400, json=error_body(etype, message + " " + SENTINEL), **kw)


def test_spend_limit_400_pattern(caplog: pytest.LogCaptureFixture) -> None:
    """AC-4 [failure/refusal]: 400 is OUR_SPEND_LIMIT only for invalid_request_error plus a phrase."""
    caplog.set_level(logging.DEBUG)
    spend = [
        _status_400("invalid_request_error", "Your workspace has reached its Spend Limit."),
        _status_400("invalid_request_error", "You hit your USAGE LIMIT for this month."),
        _status_400("invalid_request_error", "Your Credit Balance is too low to access the Anthropic API."),
    ]
    other = [
        _status_400("invalid_request_error", "messages.0.content: Field required"),
        _status_400("api_error", "spend limit reached"),
        respond(400, content=b"Bad Request", headers={"content-type": "text/plain"}),
    ]
    for handler in spend:
        caplog.clear()
        failure = call("structured", adapter_for(handler)[0]).failure
        assert failure is not None
        assert failure.kind == K.OUR_SPEND_LIMIT
        assert not [r for r in caplog.records if r.name == ADAPTER_LOGGER]
    for handler in other:
        caplog.clear()
        failure = call("structured", adapter_for(handler)[0]).failure
        assert failure is not None
        assert failure.kind == K.BAD_REQUEST
        ours = [r for r in caplog.records if r.name == ADAPTER_LOGGER]
        assert len(ours) == 1
        rec = ours[0]
        assert rec.levelno == logging.WARNING
        assert rec.getMessage() == "anthropic_400_unclassified"
        assert not rec.args
        assert rec.provider_request_id == REQUEST_ID  # type: ignore[attr-defined]
        assert {k for k in vars(rec) if k not in STANDARD_LOG_ATTRS} == {"provider_request_id"}


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize(
    ("cid", "kind"), [("refusal_with_text", K.REFUSAL), ("max_tokens_with_text", K.MAX_TOKENS)]
)
def test_stop_reason_checked_first(method: str, cid: str, kind: K) -> None:
    """AC-5 [failure/refusal]: refusal / max_tokens win over valid text; no value is returned."""
    case = next(c for c in body_cases(method) if c.id == cid)
    attempt = call(method, make(case)[0])
    assert attempt.value is None
    assert attempt.failure is not None
    assert attempt.failure.kind == kind
    assert attempt.failure.retryable is False
    assert attempt.record.stop_reason == case.stop_reason
    assert attempt.record.status == "error"


def test_request_shape() -> None:
    """AC-6 [invariant]: auto tool choice, strict tools, output_config, cache prefix only, no thinking."""
    bodies: dict[str, dict[str, Any]] = {}
    timeouts: dict[str, Any] = {}

    def run(name: str, method: str, fn: Any, timeout_s: float) -> None:
        adapter, rec = adapter_for(
            ok(_content(method), stop_reason="tool_use" if method == "tool_step" else "end_turn")
        )
        fn(adapter, timeout_s)
        bodies[name] = rec.bodies()[0]
        timeouts[name] = rec.requests[0].extensions["timeout"]["read"]

    run("choose", "choose", lambda a, t: a.choose(choice_request(), timeout_s=t), 3.5)
    run("low", "structured", lambda a, t: a.structured(structured_request(effort="low"), timeout_s=t), 12.0)
    run(
        "none",
        "structured",
        lambda a, t: a.structured(structured_request(effort=None, system_dynamic=""), timeout_s=t),
        12.0,
    )
    run(
        "tool",
        "tool_step",
        lambda a, t: a.tool_step(tool_request(a.start("Is my membership active?")), timeout_s=t),
        8.0,
    )

    assert timeouts == {"choose": 3.5, "low": 12.0, "none": 12.0, "tool": 8.0}
    for name, body in bodies.items():
        assert body["model"] == MODEL, name
        assert "thinking" not in body, name
        assert "stream" not in body, name
        assert body["system"][0]["cache_control"] == {"type": "ephemeral"}, name
        assert all("cache_control" not in blk for blk in body["system"][1:]), name

    choose = bodies["choose"]
    assert "tools" not in choose
    assert "tool_choice" not in choose
    assert choose["max_tokens"] == CHOICE_MAX_TOKENS
    assert choose["output_config"]["effort"] == CHOICE_EFFORT
    assert choose["output_config"]["format"]["type"] == "json_schema"
    schema = choose["output_config"]["format"]["schema"]
    assert schema["properties"]["topic"]["enum"] == ["billing", "booking"]
    assert schema["properties"]["urgency"]["enum"] == ["today", "later"]
    assert schema["required"] == ["topic", "urgency"]
    assert schema["additionalProperties"] is False
    assert choose["system"] == [
        {"type": "text", "text": "Route this turn.", "cache_control": {"type": "ephemeral"}}
    ]
    assert [m["role"] for m in choose["messages"]] == ["user"]
    assert isinstance(choose["messages"][0]["content"], str)
    assert list(json.loads(choose["messages"][0]["content"])) == ["state", "questions"]

    low = bodies["low"]
    assert len(low["system"]) == 2
    assert low["system"][1] == {"type": "text", "text": "Turn facts: none."}
    assert low["output_config"] == {
        "format": {"type": "json_schema", "schema": anthropic.transform_schema(Reply)},
        "effort": "low",
    }
    assert low["max_tokens"] == 1500
    assert low["messages"] == [{"role": "user", "content": "What does the membership cover?"}]

    none = bodies["none"]
    assert len(none["system"]) == 1
    assert "effort" not in none["output_config"]

    tool = bodies["tool"]
    assert tool["tool_choice"] == {"type": "auto"}
    assert tool["tools"] == [
        {
            "name": "kb_search",
            "description": "Search the knowledge base.",
            "input_schema": KB_SCHEMA,
            "strict": True,
        }
    ]
    assert tool["output_config"] == {"effort": "medium"}
    assert tool["max_tokens"] == 3000
    assert tool["messages"] == [{"role": "user", "content": "Is my membership active?"}]


def _content(method: str) -> Any:
    return SUCCESS_CONTENT[method]


def test_client_built_without_retries() -> None:
    """AC-6, P-2 [invariant]: container client has no SDK retries, no SDK spans, capped SDK logger."""
    logger = logging.getLogger("anthropic")
    before = logger.level
    try:
        c = Container(settings=types.SimpleNamespace(anthropic_api_key=SecretStr(FAKE_KEY)), limits=Limits())
        register_anthropic(c, FastAPI(), settings=c.settings, limits=c.limits)
        c.build()
        client = c.get(Key[anthropic.Anthropic]("anthropic_client"))
        assert isinstance(client, anthropic.Anthropic)
        assert client.max_retries == 0
        assert client.open_telemetry["traces"]["enabled"] is False
        assert client.open_telemetry["propagation"] is False
        assert client.api_key == FAKE_KEY
        assert logger.level == logging.WARNING
        assert AnthropicAdapter(client, model=MODEL).model == MODEL
        c.close()
        assert client.is_closed() is True
    finally:
        logger.setLevel(before)


def _text(text: str) -> Any:
    return ok([{"type": "text", "text": text}])


def test_invalid_output_and_choice_validation() -> None:
    """AC-7 [invariant]: schema-failing or out-of-options replies are INVALID_OUTPUT; valid ones parse."""
    for text in (
        '{"topic": "refunds", "urgency": "today"}',
        '{"topic": "billing"}',
        '{"topic": "billing", "urgency": "today", "extra": "x"}',
        "not json",
    ):
        attempt = adapter_for(_text(text))[0].choose(choice_request(), timeout_s=5.0)
        assert attempt.value is None, text
        assert attempt.failure is not None, text
        assert attempt.failure.kind == K.INVALID_OUTPUT, text
        assert attempt.failure.retryable is False, text
        assert attempt.failure.http_status == 200, text
    good = adapter_for(_text('{"topic": "billing", "urgency": "today"}'))[0].choose(
        choice_request(), timeout_s=5.0
    )
    assert good.failure is None
    assert good.value == ChoiceAnswer(choices={"topic": "billing", "urgency": "today"}, probabilities=None)

    bad = adapter_for(_text('{"txt": "x"}'))[0].structured(structured_request(), timeout_s=5.0)
    assert bad.failure is not None
    assert bad.failure.kind == K.INVALID_OUTPUT
    fine = adapter_for(_text('{"text": "Two tune-ups a year."}'))[0].structured(
        structured_request(), timeout_s=5.0
    )
    assert fine.failure is None
    assert isinstance(fine.value, Reply)
    assert fine.value.text == "Two tune-ups a year."
