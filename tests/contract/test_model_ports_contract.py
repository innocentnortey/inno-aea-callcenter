"""AEA-51 AC-3: one failure contract both model adapters honour (models.md section 3).

Every case runs against a mock transport behind the real adapter: no socket, no key, no paid call. The Anthropic SDK
sits on httpx2 in this repository, the Jev adapter on httpx, so each side gets its own transport type.
Situations in SHARED must map to the same ProviderFailureKind on both adapters; the per-adapter rows are asserted
against models.md section 3 only. A disagreement is reported on the ticket, never smoothed over here.
"""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import anthropic
import httpx
import httpx2
import pytest
from pydantic import SecretStr

from meridian.adapters.models.anthropic import AnthropicAdapter
from meridian.adapters.models.openrouter_jev import JevAdapter
from meridian.domain.common import LLMFacing, ProviderFailureKind
from meridian.ports.models import Attempt, ChoiceField, ChoiceRequest, ProviderCall, StructuredRequest

K = ProviderFailureKind
SONNET = "claude-sonnet-5-5"
JEV = "typesafe/jev-1.13"
TIMEOUT_S = 3.0

REQUEST = ChoiceRequest(
    system="Decide whether the customer may be in danger.",
    state={"message": "my AC is not cooling"},
    fields=(
        ChoiceField(
            name="danger",
            instructions="Is anyone at risk right now?",
            options={"normal": "No one is at risk", "danger": "Someone may be in danger"},
        ),
    ),
)


class Draft(LLMFacing):
    text: str


@dataclass
class Rig:
    """One adapter on a recording mock transport; ``call`` runs the choice request."""

    name: str
    adapter: Any
    requests: list[Any]

    def call(self) -> Attempt[Any]:
        attempt: Attempt[Any] = self.adapter.choose(REQUEST, timeout_s=TIMEOUT_S)
        return attempt


# ---- Anthropic side (httpx2) ----------------------------------------------------------------------------------


def _anthropic(handler: Callable[[httpx2.Request], httpx2.Response]) -> Rig:
    seen: list[Any] = []

    def recording(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)

    client = anthropic.Anthropic(
        api_key="sk-test-" + secrets.token_hex(8),
        max_retries=2,  # the adapter must still make exactly one attempt
        open_telemetry=False,
        http_client=httpx2.Client(transport=httpx2.MockTransport(recording)),
    )
    return Rig("anthropic", AnthropicAdapter(client, model=SONNET), seen)


def _a_message(text: str, *, stop_reason: str = "end_turn") -> httpx2.Response:
    return httpx2.Response(
        200,
        json={
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": SONNET,
            "content": [{"type": "text", "text": text}],
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {"input_tokens": 100, "output_tokens": 10},
        },
    )


def _a_error(status: int, etype: str, headers: dict[str, str] | None = None) -> httpx2.Response:
    return httpx2.Response(
        status, json={"type": "error", "error": {"type": etype, "message": "synthetic"}}, headers=headers
    )


def _a_timeout(request: httpx2.Request) -> httpx2.Response:
    raise httpx2.ReadTimeout("timed out", request=request)


ANTHROPIC_SITUATIONS: dict[str, Callable[[httpx2.Request], httpx2.Response]] = {
    "timeout": _a_timeout,
    "rate_limit": lambda r: _a_error(429, "rate_limit_error", {"retry-after": "2"}),
    "provider_spend_cap": lambda r: _a_error(402, "billing_error"),
    "invalid_choice": lambda r: _a_message('{"danger": "emergency"}'),
    "unparseable_body": lambda r: httpx2.Response(200, content=b"{not json"),
}


# ---- Jev side (httpx) -----------------------------------------------------------------------------------------


def _jev(handler: Callable[[httpx.Request], httpx.Response]) -> Rig:
    seen: list[Any] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.Client(transport=httpx.MockTransport(recording))
    adapter = JevAdapter(http, api_key=SecretStr("test-or-" + secrets.token_hex(8)), model=JEV)
    return Rig("jev", adapter, seen)


def _j_answer(choice: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "model": "typesafe/jev-1.13-20260917",
            "id": "gen-test",
            "answers": {
                "danger": {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": {"normal": 0.9, "danger": 0.1},
                }
            },
            "usage": {"input_tokens": 100, "output_tokens": 10, "cost": 1e-05},
        },
    )


def _j_timeout(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("timed out", request=request)


JEV_SITUATIONS: dict[str, Callable[[httpx.Request], httpx.Response]] = {
    "timeout": _j_timeout,
    "rate_limit": lambda r: httpx.Response(
        429, json={"error": {"code": 429, "message": "slow"}}, headers={"Retry-After": "2"}
    ),
    "provider_spend_cap": lambda r: httpx.Response(402, json={"error": {"code": 402, "message": "credits"}}),
    "invalid_choice": lambda r: _j_answer("emergency"),
    "unparseable_body": lambda r: httpx.Response(
        200, content=b"{not json", headers={"content-type": "application/json"}
    ),
}

# The shared rows (PD-11): same kind on both adapters.
SHARED: dict[str, tuple[ProviderFailureKind, bool, float | None]] = {
    # situation: (kind, retryable, retry_after_s)
    "timeout": (K.TIMEOUT, True, None),
    "rate_limit": (K.RATE_LIMITED, True, 2.0),
    "provider_spend_cap": (K.PROVIDER_SPEND_CAP, False, None),
    "invalid_choice": (K.INVALID_OUTPUT, False, None),
    "unparseable_body": (K.INVALID_OUTPUT, False, None),
}


def _rig(adapter_name: str, situation: str) -> Rig:
    if adapter_name == "anthropic":
        return _anthropic(ANTHROPIC_SITUATIONS[situation])
    return _jev(JEV_SITUATIONS[situation])


@pytest.mark.parametrize("situation", sorted(SHARED))
@pytest.mark.parametrize("adapter_name", ["anthropic", "jev"])
def test_shared_situations_same_kind(adapter_name: str, situation: str) -> None:
    kind, retryable, retry_after = SHARED[situation]
    attempt = _rig(adapter_name, situation).call()
    assert attempt.value is None
    assert attempt.failure is not None
    print(
        adapter_name,
        situation,
        attempt.failure.kind,
        attempt.failure.retryable,
        attempt.failure.retry_after_s,
    )
    assert attempt.failure.kind == kind
    assert attempt.failure.retryable is retryable
    assert attempt.failure.retry_after_s == retry_after


@pytest.mark.parametrize("situation", sorted(SHARED))
@pytest.mark.parametrize("adapter_name", ["anthropic", "jev"])
def test_one_attempt_never_raises_record_present(adapter_name: str, situation: str) -> None:
    rig = _rig(adapter_name, situation)
    attempt = rig.call()  # a raise here fails the test: adapters never raise
    assert len(rig.requests) == 1
    record = attempt.record
    assert isinstance(record, ProviderCall)
    assert (record.status == "error") == (attempt.failure is not None)
    assert record.provider == rig.adapter.provider
    assert record.model == (SONNET if adapter_name == "anthropic" else JEV)


@pytest.mark.parametrize("adapter_name", ["anthropic", "jev"])
def test_success_has_value_record_and_one_request(adapter_name: str) -> None:
    rig = (
        _anthropic(lambda r: _a_message('{"danger": "normal"}'))
        if adapter_name == "anthropic"
        else _jev(lambda r: _j_answer("normal"))
    )
    attempt = rig.call()
    assert attempt.failure is None and attempt.value is not None
    assert attempt.value.choices == {"danger": "normal"}
    assert attempt.record.status == "ok"
    assert len(rig.requests) == 1


def test_error_inside_200_per_mapping() -> None:
    # Jev (models.md section 3): an error object inside HTTP 200 is BODY_ERROR with the inner code; 503 is retryable.
    jev = _jev(lambda r: httpx.Response(200, json={"error": {"code": 503, "message": "synthetic"}}))
    attempt = jev.call()
    assert attempt.failure is not None
    assert attempt.failure.kind == K.BODY_ERROR
    assert attempt.failure.http_status == 503
    assert attempt.failure.retryable is True
    assert len(jev.requests) == 1
    # Anthropic: the only section 3 row a 200 can take is INVALID_OUTPUT.
    anth = _anthropic(
        lambda r: httpx2.Response(200, json={"type": "error", "error": {"type": "api_error", "message": "x"}})
    )
    attempt = anth.call()
    assert attempt.failure is not None
    assert attempt.failure.kind == K.INVALID_OUTPUT
    assert len(anth.requests) == 1


@pytest.mark.parametrize(("stop_reason", "kind"), [("max_tokens", K.MAX_TOKENS), ("refusal", K.REFUSAL)])
def test_stop_reason_before_content_anthropic(stop_reason: str, kind: ProviderFailureKind) -> None:
    # Valid JSON content, but the stop reason wins (models.md section 3; no Jev row exists for this).
    rig = _anthropic(lambda r: _a_message('{"danger": "normal"}', stop_reason=stop_reason))
    attempt = rig.call()
    assert attempt.value is None
    assert attempt.failure is not None
    assert attempt.failure.kind == kind
    assert attempt.record.stop_reason == stop_reason
    # The same holds through the structured method.
    rig = _anthropic(lambda r: _a_message('{"text": "hello"}', stop_reason=stop_reason))
    structured = rig.adapter.structured(
        StructuredRequest(
            system_prefix="You are Meridian's assistant.",
            system_dynamic="",
            user="Hello",
            output_model=Draft,
            max_tokens=500,
            effort="low",
        ),
        timeout_s=TIMEOUT_S,
    )
    assert structured.value is None
    assert structured.failure is not None and structured.failure.kind == kind


def test_anthropic_structured_success_and_request_shape() -> None:
    rig = _anthropic(lambda r: _a_message('{"text": "hello"}'))
    attempt = rig.adapter.structured(
        StructuredRequest(
            system_prefix="You are Meridian's assistant.",
            system_dynamic="",
            user="Hello",
            output_model=Draft,
            max_tokens=500,
            effort=None,
        ),
        timeout_s=TIMEOUT_S,
    )
    assert attempt.value == Draft(text="hello")
    body = json.loads(rig.requests[0].content)
    assert "tool_choice" not in body
