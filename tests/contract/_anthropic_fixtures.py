"""AEA-17 frozen fixtures: a mocked Anthropic transport and the failure/response catalogue.

Private helper of ``test_anthropic_adapter.py`` (plan section 3.4). No network and no paid call: every
request goes through ``httpx2.MockTransport``. The injected clients are built with ``max_retries=2`` on
purpose, so a test passes only if the adapter itself enforces exactly one attempt (AC-1).
"""

from __future__ import annotations

import json
import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, cast

import anthropic
import httpx2

from meridian.adapters.models.anthropic import AnthropicAdapter
from meridian.domain.common import LLMFacing, ProviderFailureKind
from meridian.ports.models import (
    Attempt,
    ChoiceField,
    ChoiceRequest,
    ProviderMessages,
    StructuredRequest,
    ToolSchema,
    ToolStepRequest,
)

K = ProviderFailureKind
MODEL = "claude-sonnet-5-5"
FAKE_KEY = "sk-test-" + secrets.token_hex(12)
SENTINEL = "ZZSENTINEL-" + secrets.token_hex(4)
REQUEST_ID = "req_011TestFixture01"
SIGNATURE = "EqQBCkYIBhgCKkD/+=Q2xhdWRlU2lnbmF0dXJl=="
METHODS = ("choose", "structured", "tool_step")
USAGE: dict[str, Any] = {
    "input_tokens": 1000,
    "output_tokens": 500,
    "cache_creation_input_tokens": 200,
    "cache_read_input_tokens": 3000,
    "output_tokens_details": {"thinking_tokens": 120},
}
KB_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
    "additionalProperties": False,
}
TOOL_CONTENT: list[dict[str, Any]] = [
    {"type": "thinking", "thinking": "  Need the KB.\n", "signature": SIGNATURE},
    {"type": "text", "text": "Let me check."},
    {"type": "tool_use", "id": "toolu_01", "name": "kb_search", "input": {"query": "membership"}},
    {"type": "tool_use", "id": "toolu_02", "name": "account_read", "input": "not-json{"},
]
SUCCESS_CONTENT: dict[str, list[dict[str, Any]]] = {
    "choose": [{"type": "text", "text": '{"topic": "billing", "urgency": "today"}'}],
    "structured": [{"type": "text", "text": '{"text": "Two tune-ups a year."}'}],
    "tool_step": TOOL_CONTENT,
}
STANDARD_LOG_ATTRS = set(vars(logging.LogRecord("n", logging.INFO, "p", 1, "m", None, None))) | {
    "message",
    "asctime",
}


class Reply(LLMFacing):
    text: str


def message_body(
    *,
    content: object,
    stop_reason: str | None = "end_turn",
    model: str = MODEL,
    usage: dict[str, Any] | None = USAGE,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
    }
    if usage is not None:
        body["usage"] = usage
    return body


def error_body(etype: str, message: str) -> dict[str, Any]:
    return {"type": "error", "error": {"type": etype, "message": message}, "request_id": REQUEST_ID}


Handler = Callable[[httpx2.Request], httpx2.Response]


def respond(
    status: int,
    *,
    json: object | None = None,
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> Handler:
    hdrs = dict(headers or {})
    hdrs.setdefault("request-id", REQUEST_ID)

    def handler(request: httpx2.Request) -> httpx2.Response:
        if content is not None:
            return httpx2.Response(status, content=content, headers=hdrs)
        if json is not None:
            return httpx2.Response(status, json=json, headers=hdrs)
        return httpx2.Response(status, headers=hdrs)

    return handler


def raises(factory: Callable[[httpx2.Request], Exception]) -> Handler:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise factory(request)

    return handler


def ok(content: object, *, stop_reason: str | None = "end_turn", **kw: Any) -> Handler:
    return respond(200, json=message_body(content=content, stop_reason=stop_reason, **kw))


def sequence(*handlers: Handler) -> Handler:
    queue = list(handlers)

    def handler(request: httpx2.Request) -> httpx2.Response:
        return queue.pop(0)(request)

    return handler


@dataclass
class Recorder:
    requests: list[httpx2.Request] = field(default_factory=list)

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(r.content) for r in self.requests]


def plain_client(key: str = FAKE_KEY) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=key, max_retries=2, open_telemetry=False)


def adapter_for(
    handler: Handler, *, model: str = MODEL, key: str = FAKE_KEY
) -> tuple[AnthropicAdapter, Recorder]:
    recorder = Recorder()

    def recording(request: httpx2.Request) -> httpx2.Response:
        recorder.requests.append(request)
        return handler(request)

    client = anthropic.Anthropic(
        api_key=key,
        max_retries=2,
        open_telemetry=False,
        http_client=httpx2.Client(transport=httpx2.MockTransport(recording)),
    )
    return AnthropicAdapter(client, model=model), recorder


class _Messages:
    def __init__(self, owner: ExplodingClient) -> None:
        self._owner = owner

    @property
    def with_raw_response(self) -> _Messages:
        return self

    def create(self, **kwargs: object) -> object:
        self._owner.calls += 1
        raise RuntimeError(SENTINEL)


class ExplodingClient:
    """A client whose ``create`` raises before any HTTP exchange (case ``raised_before_request``)."""

    max_retries = 2

    def __init__(self) -> None:
        self.calls = 0
        self.messages = _Messages(self)

    def with_options(self, **kwargs: object) -> ExplodingClient:
        return self


def choice_request() -> ChoiceRequest:
    return ChoiceRequest(
        system="Route this turn.",
        state={"new_message": "Can I move my tune-up?"},
        fields=(
            ChoiceField(
                name="topic",
                instructions="Pick the topic.",
                options={"billing": "Billing question", "booking": "Booking or change"},
            ),
            ChoiceField(
                name="urgency", instructions="How soon?", options={"today": "Today", "later": "Later"}
            ),
        ),
    )


def structured_request(
    *, effort: Literal["low", "medium", "high"] | None = "low", system_dynamic: str = "Turn facts: none."
) -> StructuredRequest[Reply]:
    return StructuredRequest(
        system_prefix="You are Meridian's assistant.",
        system_dynamic=system_dynamic,
        user="What does the membership cover?",
        output_model=Reply,
        max_tokens=1500,
        effort=effort,
    )


def tool_request(messages: ProviderMessages) -> ToolStepRequest:
    return ToolStepRequest(
        system_prefix="Specialist rules.",
        system_dynamic="Verified: no.",
        messages=messages,
        tools=(
            ToolSchema(name="kb_search", description="Search the knowledge base.", input_schema=KB_SCHEMA),
        ),
        max_tokens=3000,
        effort="medium",
    )


@dataclass(frozen=True)
class Case:
    id: str
    handler: Handler | None  # None = ExplodingClient
    kind: ProviderFailureKind | None
    retryable: bool | None
    http_status: int | None
    retry_after_s: float | None
    request_id: str | None
    logs_unclassified: bool
    stop_reason: str | None = None  # expected record.stop_reason (response-level cases)
    has_usage: bool = False  # True when the response carries the USAGE block


def _http(
    cid: str,
    status: int,
    etype: str,
    msg: str,
    kind: ProviderFailureKind,
    retryable: bool,
    *,
    ra: float | None = None,
    headers: dict[str, str] | None = None,
    logs: bool = False,
) -> Case:
    handler = respond(status, json=error_body(etype, msg + " " + SENTINEL), headers=headers)
    return Case(cid, handler, kind, retryable, status, ra, REQUEST_ID, logs)


def _no_id(cid: str, handler: Handler | None, kind: ProviderFailureKind) -> Case:
    return Case(cid, handler, kind, True, None, None, None, False)


def _http_cases() -> tuple[Case, ...]:
    return (
        _no_id("timeout", raises(lambda r: httpx2.ReadTimeout("read timed out", request=r)), K.TIMEOUT),
        _no_id(
            "connection_error",
            raises(lambda r: httpx2.ConnectError("connection refused", request=r)),
            K.CONNECTION,
        ),
        _http(
            "status_400",
            400,
            "invalid_request_error",
            "messages.0.content: Field required",
            K.BAD_REQUEST,
            False,
            logs=True,
        ),
        _http(
            "status_400_spend_limit",
            400,
            "invalid_request_error",
            "Your workspace has reached its Spend Limit.",
            K.OUR_SPEND_LIMIT,
            False,
        ),
        _http("status_401", 401, "authentication_error", "invalid x-api-key", K.AUTH, False),
        _http("status_402", 402, "billing_error", "billing problem", K.PROVIDER_SPEND_CAP, False),
        _http("status_403", 403, "permission_error", "not allowed", K.AUTH, False),
        _http("status_404", 404, "not_found_error", "model not found", K.NOT_FOUND, False),
        _http("status_408", 408, "timeout_error", "request timeout", K.TIMEOUT, True),
        _http("status_409", 409, "conflict_error", "conflict", K.SERVER, True),
        _http("status_413", 413, "request_too_large", "too large", K.BAD_REQUEST, False),
        _http("status_418", 418, "teapot_error", "teapot", K.BAD_REQUEST, False),
        _http(
            "status_429_retry_after",
            429,
            "rate_limit_error",
            "slow down",
            K.RATE_LIMITED,
            True,
            ra=7.0,
            headers={"retry-after": "7"},
        ),
        _http(
            "status_429_retry_after_ms",
            429,
            "rate_limit_error",
            "slow down",
            K.RATE_LIMITED,
            True,
            ra=1.5,
            headers={"retry-after-ms": "1500"},
        ),
        _http("status_429_bare", 429, "rate_limit_error", "limit reached", K.PROVIDER_SPEND_CAP, False),
        _http("status_529", 529, "overloaded_error", "overloaded", K.OVERLOADED, True),
        _http("status_500", 500, "api_error", "internal", K.SERVER, True),
        _http("status_503", 503, "api_error", "unavailable", K.SERVER, True),
        _http("status_504", 504, "timeout_error", "gateway timeout", K.SERVER, True),
        Case(
            "status_302",
            respond(302, headers={"location": "https://example.test/"}),
            K.INVALID_OUTPUT,
            False,
            302,
            None,
            REQUEST_ID,
            False,
        ),
        _no_id("raised_before_request", None, K.CONNECTION),
        Case(
            "raised_after_response",
            respond(200, content=b"{not json", headers={"content-type": "application/json"}),
            K.INVALID_OUTPUT,
            False,
            200,
            None,
            REQUEST_ID,
            False,
        ),
    )


HTTP_CASES: tuple[Case, ...] = _http_cases()


def case_by_id(cid: str) -> Case:
    return next(c for c in HTTP_CASES if c.id == cid)


def body_cases(method: str) -> tuple[Case, ...]:
    content = SUCCESS_CONTENT[method]
    stop = "tool_use" if method == "tool_step" else "end_turn"

    def c(
        cid: str, handler: Handler, kind: ProviderFailureKind | None, status: str | None, usage: bool = True
    ) -> Case:
        return Case(
            cid,
            handler,
            kind,
            None if kind is None else False,
            200 if kind else None,
            None,
            REQUEST_ID,
            False,
            status,
            usage,
        )

    cases = [
        c("success", ok(content, stop_reason=stop), None, stop),
        c("success_other_model", ok(content, stop_reason=stop, model="claude-other-9"), None, stop),
        c("refusal_with_text", ok(content, stop_reason="refusal"), K.REFUSAL, "refusal"),
        c("max_tokens_with_text", ok(content, stop_reason="max_tokens"), K.MAX_TOKENS, "max_tokens"),
        c(
            "missing_content",
            respond(200, json={"id": "msg_test", "type": "message", "role": "assistant"}),
            K.INVALID_OUTPUT,
            None,
            False,
        ),
        c("content_not_list", ok("oops"), K.INVALID_OUTPUT, "end_turn"),
    ]
    bad = {
        "choose": '{"topic": "refunds", "urgency": "today"}',
        "structured": '{"txt": "x"}',
    }.get(method)
    if bad is not None:
        cases.append(c("invalid_output", ok([{"type": "text", "text": bad}]), K.INVALID_OUTPUT, "end_turn"))
    return tuple(cases)


def make(case: Case, **kw: Any) -> tuple[AnthropicAdapter, Recorder | ExplodingClient]:
    if case.handler is None:
        client = ExplodingClient()
        return AnthropicAdapter(cast(anthropic.Anthropic, client), model=kw.get("model", MODEL)), client
    return adapter_for(case.handler, **kw)


def call(method: str, adapter: AnthropicAdapter, timeout_s: float = 5.0) -> Attempt[Any]:
    if method == "choose":
        return adapter.choose(choice_request(), timeout_s=timeout_s)
    if method == "structured":
        return adapter.structured(structured_request(), timeout_s=timeout_s)
    return adapter.tool_step(tool_request(adapter.start("Is my membership active?")), timeout_s=timeout_s)


def requests_seen(handle: Recorder | ExplodingClient) -> int:
    return handle.calls if isinstance(handle, ExplodingClient) else len(handle.requests)
