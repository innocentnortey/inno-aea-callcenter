"""Anthropic adapter: one Sonnet request per call, reported as a typed Attempt; never raises."""

from __future__ import annotations

import json
import logging
import math
import re
import time
from collections.abc import Callable, Mapping, Sequence
from types import MappingProxyType
from typing import Any, ClassVar, Final, Literal, cast

import anthropic
from anthropic.types import Message, MessageParam, TextBlock, TextBlockParam, ToolUseBlock
from pydantic import BaseModel, JsonValue, SecretStr

from meridian.domain.common import ProviderFailure, ProviderFailureKind, ProviderName
from meridian.ports.models import (
    Attempt,
    ChoiceAnswer,
    ChoiceRequest,
    ProviderCall,
    ProviderMessages,
    StructuredRequest,
    TokenPrice,
    ToolCall,
    ToolStep,
    ToolStepRequest,
)

ANTHROPIC_PRICES: Mapping[str, TokenPrice] = MappingProxyType(
    {
        # US dollars per million tokens; research section 2a (S-187), read 2026-10-20.
        "claude-sonnet-5-5": TokenPrice(input=2.00, output=10.00, cache_write_5m=2.50, cache_read=0.10),
    }
)
CHOICE_MAX_TOKENS: Final = 1500  # = AEA-02 default PLANNER_FALLBACK max_tokens (D-4)
CHOICE_EFFORT: Final[Literal["low", "medium", "high"]] = "low"  # = PLANNER_FALLBACK effort (D-4)

_LOG = logging.getLogger(__name__)
_SPEND_LIMIT_PHRASES: Final = ("spend limit", "usage limit", "credit balance")  # MOD-3 [A]
_RETRYABLE: Final = frozenset(
    {
        ProviderFailureKind.TIMEOUT,
        ProviderFailureKind.CONNECTION,
        ProviderFailureKind.RATE_LIMITED,
        ProviderFailureKind.OVERLOADED,
        ProviderFailureKind.SERVER,
    }
)  # DO-4 section 11
_REQUEST_ID: Final = re.compile(r"[A-Za-z0-9_-]{1,128}")


class _InvalidOutput(Exception):
    """The reply arrived but is not usable."""


def _clean_request_id(value: object) -> str | None:
    """Keep only a well-formed request id (AC-9)."""
    if isinstance(value, str) and _REQUEST_ID.fullmatch(value):
        return value
    return None


def _count(value: object) -> int:
    """A non-negative int, else 0, so building ProviderCall cannot raise."""
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return 0


def _counts(usage: object) -> tuple[int, int, int, int, int]:
    """(input, output, cache_read, cache_write, thinking) from a usage block."""
    details = getattr(usage, "output_tokens_details", None)
    return (
        _count(getattr(usage, "input_tokens", None)),
        _count(getattr(usage, "output_tokens", None)),
        _count(getattr(usage, "cache_read_input_tokens", None)),
        _count(getattr(usage, "cache_creation_input_tokens", None)),
        _count(getattr(details, "thinking_tokens", None)),
    )


def _cost(price: TokenPrice, in_tokens: int, out_tokens: int, cache_write: int, cache_read: int) -> float:
    """Thinking is not a parameter: it is already inside output_tokens (MOD-16)."""
    total = (
        in_tokens * price.input
        + out_tokens * price.output
        + cache_write * price.cache_write_5m
        + cache_read * price.cache_read
    ) / 1_000_000
    if not math.isfinite(total) or total < 0:
        return 0.0
    return total


def _retry_after(headers: Any) -> tuple[bool, float | None]:
    """(a retry-after header is present, its value in seconds if it parses)."""
    raw_ms = headers.get("retry-after-ms")
    raw_s = headers.get("retry-after")
    present = any(isinstance(h, str) and h.strip() for h in (raw_ms, raw_s))
    for raw, scale in ((raw_ms, 1000.0), (raw_s, 1.0)):
        if not isinstance(raw, str):
            continue
        try:
            seconds = float(raw) / scale
        except ValueError:
            continue
        if math.isfinite(seconds) and seconds >= 0:
            return present, seconds
    return present, None


def _is_spend_limit(body: object) -> bool:
    """Read the provider message to classify only; it is never returned, stored or logged (AC-9)."""
    error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict) or error.get("type") != "invalid_request_error":
        return False
    message = error.get("message")
    return isinstance(message, str) and any(p in message.lower() for p in _SPEND_LIMIT_PHRASES)


def _failure(
    kind: ProviderFailureKind,
    *,
    http_status: int | None,
    request_id: str | None,
    retry_after_s: float | None = None,
) -> ProviderFailure:
    return ProviderFailure(
        kind=kind,
        provider="anthropic",
        http_status=http_status,
        retry_after_s=retry_after_s,
        retryable=kind in _RETRYABLE,
        provider_request_id=request_id,
    )


def _failure_for_status(exc: anthropic.APIStatusError) -> ProviderFailure:
    """stage7/models section 3, Anthropic table."""
    status = exc.status_code
    rid = _clean_request_id(exc.request_id)
    kind: ProviderFailureKind
    retry_after_s: float | None = None
    if status == 400:
        if _is_spend_limit(exc.body):
            kind = ProviderFailureKind.OUR_SPEND_LIMIT
        else:
            _LOG.warning("anthropic_400_unclassified", extra={"provider_request_id": rid})
            kind = ProviderFailureKind.BAD_REQUEST
    elif status in (401, 403):
        kind = ProviderFailureKind.AUTH
    elif status == 402:
        kind = ProviderFailureKind.PROVIDER_SPEND_CAP
    elif status == 404:
        kind = ProviderFailureKind.NOT_FOUND
    elif status == 408:
        kind = ProviderFailureKind.TIMEOUT
    elif status == 409:
        kind = ProviderFailureKind.SERVER
    elif status == 413:
        kind = ProviderFailureKind.BAD_REQUEST
    elif status == 429:
        present, retry_after_s = _retry_after(exc.response.headers)
        kind = ProviderFailureKind.RATE_LIMITED if present else ProviderFailureKind.PROVIDER_SPEND_CAP
    elif status == 529:
        kind = ProviderFailureKind.OVERLOADED
    elif 500 <= status <= 599:
        kind = ProviderFailureKind.SERVER
    elif 400 <= status <= 499:
        kind = ProviderFailureKind.BAD_REQUEST
    else:
        kind = ProviderFailureKind.INVALID_OUTPUT
    return _failure(kind, http_status=status, request_id=rid, retry_after_s=retry_after_s)


def _system_blocks(prefix: str, dynamic: str) -> list[TextBlockParam]:
    """The cache mark sits on the stable prefix only; empty text blocks are omitted (the API rejects them)."""
    blocks: list[TextBlockParam] = []
    if prefix.strip():
        blocks.append({"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}})
    if dynamic.strip():
        blocks.append({"type": "text", "text": dynamic})
    return blocks


def _text(message: Message) -> str:
    return "".join(b.text for b in message.content if isinstance(b, TextBlock))


def _choice_schema(req: ChoiceRequest) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            f.name: {"type": "string", "enum": list(f.options), "description": f.instructions}
            for f in req.fields
        },
        "required": [f.name for f in req.fields],
        "additionalProperties": False,
    }


def _render_choice(req: ChoiceRequest) -> str:
    questions = [{"name": f.name, "instructions": f.instructions, "options": f.options} for f in req.fields]
    return json.dumps({"state": req.state, "questions": questions}, ensure_ascii=False)


class AnthropicAdapter:
    """ChoiceModel, StructuredModel, ToolCallingModel and ToolTranscript for one Anthropic model."""

    provider: ClassVar[ProviderName] = "anthropic"

    def __init__(self, client: anthropic.Anthropic, *, model: str) -> None:
        if model not in ANTHROPIC_PRICES:
            raise ValueError("no ANTHROPIC_PRICES row for this model ID")
        # The SDK's DEBUG lines carry whole request payloads and response headers: keep them out of any log.
        sdk_log = logging.getLogger("anthropic")
        if sdk_log.getEffectiveLevel() < logging.WARNING:
            sdk_log.setLevel(logging.WARNING)
        # One HTTP attempt even if the caller's client has SDK retries on.
        self._client = client.with_options(max_retries=0)
        self._model = model
        self._price = ANTHROPIC_PRICES[model]

    @property
    def model(self) -> str:
        return self._model

    # -- ports ---------------------------------------------------------------------------------

    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]:
        def build() -> dict[str, Any]:
            return {
                "model": self._model,
                "max_tokens": CHOICE_MAX_TOKENS,
                "system": _system_blocks(req.system, ""),
                "messages": [{"role": "user", "content": _render_choice(req)}],
                "output_config": {
                    "format": {"type": "json_schema", "schema": _choice_schema(req)},
                    "effort": CHOICE_EFFORT,
                },
            }

        def read(message: Message) -> ChoiceAnswer:
            data = json.loads(_text(message))
            if not isinstance(data, dict) or set(data) != {f.name for f in req.fields}:
                raise _InvalidOutput
            for f in req.fields:
                value = data[f.name]
                if not isinstance(value, str) or value not in f.options:
                    raise _InvalidOutput
            return ChoiceAnswer(choices={f.name: data[f.name] for f in req.fields}, probabilities=None)

        return self._send(build, read, timeout_s=timeout_s)

    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]:
        def build() -> dict[str, Any]:
            output_config: dict[str, Any] = {
                "format": {"type": "json_schema", "schema": anthropic.transform_schema(req.output_model)}
            }
            if req.effort is not None:
                output_config["effort"] = req.effort
            return {
                "model": self._model,
                "max_tokens": req.max_tokens,
                "system": _system_blocks(req.system_prefix, req.system_dynamic),
                "messages": [{"role": "user", "content": req.user}],
                "output_config": output_config,
            }

        def read(message: Message) -> T:
            return req.output_model.model_validate_json(_text(message))

        return self._send(build, read, timeout_s=timeout_s)

    def _messages(self, items: tuple[JsonValue, ...]) -> ProviderMessages:
        """Built without validation so provider text stays byte-exact (models.md section 1, MOD-17; D-14)."""
        return ProviderMessages.model_construct(provider="anthropic", model=self._model, items=items)

    def start(self, user: str) -> ProviderMessages:
        return self._messages(({"role": "user", "content": user},))

    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]:
        def build() -> dict[str, Any]:
            kwargs: dict[str, Any] = {
                "model": self._model,
                "max_tokens": req.max_tokens,
                "system": _system_blocks(req.system_prefix, req.system_dynamic),
                "messages": cast(list[MessageParam], list(req.messages.items)),
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema,
                        "strict": True,
                    }
                    for t in req.tools
                ],
                "tool_choice": {"type": "auto"},
            }
            if req.effort is not None:
                kwargs["output_config"] = {"effort": req.effort}
            return kwargs

        def read(message: Message) -> ToolStep:
            calls = tuple(
                ToolCall(
                    id=b.id,
                    name=b.name,
                    args=cast(dict[str, JsonValue], b.input) if isinstance(b.input, dict) else None,
                )
                for b in message.content
                if isinstance(b, ToolUseBlock)
            )
            blocks = cast(
                JsonValue,
                [b.model_dump(mode="json", exclude_none=True, warnings=False) for b in message.content],
            )
            return ToolStep.model_construct(
                text=_text(message),
                tool_calls=calls,
                raw={"role": "assistant", "content": blocks},
                stop_reason=message.stop_reason,
            )

        return self._send(build, read, timeout_s=timeout_s)

    def append(
        self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]
    ) -> ProviderMessages:
        if messages.provider != self.provider or messages.model != self._model:
            raise ValueError("ProviderMessages were built by another adapter")
        tool_results: list[JsonValue] = [
            {"type": "tool_result", "tool_use_id": call_id, "content": text} for call_id, text in results
        ]
        return self._messages((*messages.items, step.raw, {"role": "user", "content": tool_results}))

    # -- the one send path ---------------------------------------------------------------------

    def _send[T: BaseModel](
        self, build: Callable[[], dict[str, Any]], read: Callable[[Message], T], *, timeout_s: float
    ) -> Attempt[T]:
        started = time.perf_counter()
        arrived = False
        status: int | None = None
        rid: str | None = None
        message: Message | None = None
        try:
            kwargs = build()
            raw = self._client.messages.with_raw_response.create(**kwargs, timeout=timeout_s)
            arrived = True
            status = raw.status_code
            rid = _clean_request_id(raw.headers.get("request-id"))
            parsed = raw.parse()
            if not isinstance(parsed, Message):
                raise _InvalidOutput
            message = parsed
            if not isinstance(message.content, list):
                raise _InvalidOutput
            if message.stop_reason == "refusal":
                kind = ProviderFailureKind.REFUSAL
                return self._failed(started, _failure(kind, http_status=status, request_id=rid), message)
            if message.stop_reason == "max_tokens":
                kind = ProviderFailureKind.MAX_TOKENS
                return self._failed(started, _failure(kind, http_status=status, request_id=rid), message)
            value = read(message)
            record = self._record(
                started, usage=message.usage, failure=None, rid=rid, stop_reason=message.stop_reason
            )
            return Attempt[T](value=value, record=record, failure=None)
        except anthropic.APITimeoutError:
            return self._failed(
                started, _failure(ProviderFailureKind.TIMEOUT, http_status=None, request_id=None), None
            )
        except anthropic.APIConnectionError:
            return self._failed(
                started, _failure(ProviderFailureKind.CONNECTION, http_status=None, request_id=None), None
            )
        except anthropic.APIStatusError as exc:
            return self._failed(started, _failure_for_status(exc), None)
        except Exception:
            # MOD-2 catch-all. The exception is deliberately not bound, formatted, logged or chained.
            if not arrived:
                failure = _failure(ProviderFailureKind.CONNECTION, http_status=None, request_id=None)
            else:
                failure = _failure(ProviderFailureKind.INVALID_OUTPUT, http_status=status, request_id=rid)
            return self._failed(started, failure, message)

    def _failed[T: BaseModel](
        self, started: float, failure: ProviderFailure, message: Message | None
    ) -> Attempt[T]:
        record = self._record(
            started,
            usage=message.usage if message is not None else None,
            failure=failure,
            rid=failure.provider_request_id,
            stop_reason=message.stop_reason if message is not None else None,
        )
        return Attempt[T](value=None, record=record, failure=failure)

    def _record(
        self,
        started: float,
        *,
        usage: object,
        failure: ProviderFailure | None,
        rid: str | None,
        stop_reason: str | None,
    ) -> ProviderCall:
        in_tokens, out_tokens, cache_read, cache_write, thinking = _counts(usage)
        return ProviderCall(
            provider="anthropic",
            model=self._model,
            latency_ms=max(0, int((time.perf_counter() - started) * 1000)),
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            cache_read_tokens=cache_read,
            cache_write_tokens=cache_write,
            thinking_tokens=thinking,
            cost_usd=_cost(self._price, in_tokens, out_tokens, cache_write, cache_read),
            cost_source="price_table",
            status="error" if failure else "ok",
            failure=failure,
            provider_request_id=rid,
            stop_reason=stop_reason if isinstance(stop_reason, str) else None,
        )


def build_anthropic_client(api_key: SecretStr) -> anthropic.Anthropic:
    """The one SDK client (models.md section 7): no SDK retries (the gateway owns retrying), no SDK spans or trace headers."""
    return anthropic.Anthropic(
        api_key=api_key.get_secret_value(),
        max_retries=0,
        open_telemetry={"traces": False, "propagation": False},
    )
