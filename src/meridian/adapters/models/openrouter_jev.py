"""JevAdapter: one OpenRouter decisions request per call, reported as a typed Attempt (AEA-18).

Implements ChoiceModel only (DO-3 S-1): Jev returns choices, never text, so it has no structured or tool methods.
Every request sends provider.data_collection "deny"; an `error` object inside an HTTP 200 is a failure (readiness
SD-6.3); failures are mapped here from raw status and body (stage7/models.md §3; no shared classifier, DO-3 S-24).
choose() never raises and never logs; the API key leaves only in the Authorization header.
"""

from __future__ import annotations

import math
import re
import time
from collections.abc import Mapping
from typing import Any, ClassVar, Final, Literal

import httpx
from pydantic import SecretStr

from meridian.domain.common import ProviderFailure, ProviderFailureKind, ProviderName
from meridian.ports.models import Attempt, ChoiceAnswer, ChoiceRequest, ProviderCall, TokenPrice

DECISIONS_URL: Final = "https://openrouter.ai/api/alpha/decisions"  # SP-1 build plan step 5 (measured)

JEV_PRICES: Mapping[str, TokenPrice] = {  # research §2e (S-223, S-219): output is free
    "typesafe/jev-1.13": TokenPrice(input=0.042, output=0.0, cache_write_5m=0.0, cache_read=0.0),
}

_BODY_ERROR_RETRYABLE_CODES: Final = (408, 429, 500, 502, 503, 504, 529)
_TOKEN_PATTERN: Final = r"[A-Za-z0-9._:-]+"  # noqa: S105 (a regex, not a credential)
_REQUEST_ID_MAX: Final = 200
_STOP_REASON_MAX: Final = 64
_NO_USAGE: Final = (0, 0, None)

_Usage = tuple[int, int, float | None]


def _clock() -> float:
    return time.perf_counter()


def _elapsed_ms(started: float) -> int:
    return max(0, round((_clock() - started) * 1000))


def _json_object(response: httpx.Response) -> dict[str, Any] | None:
    try:
        parsed = response.json()
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _count(v: object) -> int:
    if type(v) is int and v >= 0:
        return v
    if type(v) is float and math.isfinite(v) and v >= 0 and v.is_integer():
        return int(v)
    return 0


def _reported_cost(v: object) -> float | None:
    if (type(v) is int or type(v) is float) and math.isfinite(v) and v >= 0:
        return float(v)
    return None


def _usage(data: dict[str, Any] | None) -> _Usage:
    u = data.get("usage") if data is not None else None
    if not isinstance(u, dict):
        return _NO_USAGE
    return _count(u.get("input_tokens")), _count(u.get("output_tokens")), _reported_cost(u.get("cost"))


def _safe_token(v: object, max_len: int) -> str | None:
    if isinstance(v, str) and 1 <= len(v) <= max_len and re.fullmatch(_TOKEN_PATTERN, v):
        return v
    return None


def _retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        x = float(value.strip())
    except ValueError:
        return None
    return x if math.isfinite(x) and x >= 0 else None


def _status_failure(status: int, headers: httpx.Headers) -> tuple[ProviderFailureKind, bool, float | None]:
    if status in (401, 403):
        return ProviderFailureKind.AUTH, False, None
    if status == 402:
        return ProviderFailureKind.PROVIDER_SPEND_CAP, False, None
    if status == 404:
        return ProviderFailureKind.NOT_FOUND, False, None
    if status == 408:
        return ProviderFailureKind.TIMEOUT, True, None
    if status == 429:
        return ProviderFailureKind.RATE_LIMITED, True, _retry_after(headers.get("retry-after"))
    if status >= 500:
        return ProviderFailureKind.SERVER, True, None
    return ProviderFailureKind.BAD_REQUEST, False, None


def _probabilities(v: object) -> dict[str, float] | None:
    if not isinstance(v, dict):
        return None
    out: dict[str, float] = {}
    for k, x in v.items():
        if not isinstance(k, str) or type(x) not in (int, float) or not math.isfinite(x):
            return None
        out[k] = float(x)
    return out


def _answer(req: ChoiceRequest, data: dict[str, Any]) -> ChoiceAnswer | None:
    answers = data.get("answers")
    if not isinstance(answers, dict):
        return None
    choices: dict[str, str] = {}
    probabilities: dict[str, dict[str, float]] = {}
    for f in req.fields:
        a = answers.get(f.name)
        if not isinstance(a, dict):
            return None
        choice = a.get("choice")
        if not isinstance(choice, str) or choice not in f.options:
            return None
        choices[f.name] = choice
        p = _probabilities(a.get("probabilities"))
        if p is not None:
            probabilities[f.name] = p
    return ChoiceAnswer(choices=choices, probabilities=probabilities or None)


class JevAdapter:
    """One Jev decision request per call (ChoiceModel). Bound to one model at construction (models.md §2)."""

    provider: ClassVar[ProviderName] = "openrouter_jev"

    def __init__(self, http: httpx.Client, *, api_key: SecretStr, model: str) -> None:
        if not isinstance(api_key, SecretStr):
            raise TypeError("api_key must be a pydantic SecretStr")
        if not api_key.get_secret_value():
            raise ValueError("api_key is empty")
        price = JEV_PRICES.get(model)
        if price is None:
            raise ValueError(f"no JEV_PRICES row for model {model!r}")
        self._http = http
        self._api_key = api_key
        self._model = model
        self._price = price

    @property
    def model(self) -> str:
        return self._model

    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]:
        started = _clock()
        try:
            body = self._request_body(req)
            response = self._http.post(
                DECISIONS_URL,
                json=body,
                headers={"Authorization": f"Bearer {self._api_key.get_secret_value()}"},
                timeout=timeout_s,
            )
        except httpx.TimeoutException:
            return self._failed(
                _elapsed_ms(started), kind=ProviderFailureKind.TIMEOUT, retryable=True, http_status=None
            )
        except httpx.TransportError:
            return self._failed(
                _elapsed_ms(started), kind=ProviderFailureKind.CONNECTION, retryable=True, http_status=None
            )
        except Exception:
            return self._failed(
                _elapsed_ms(started), kind=ProviderFailureKind.CONNECTION, retryable=True, http_status=None
            )
        latency_ms = _elapsed_ms(started)
        try:
            return self._from_response(req, response, latency_ms)
        except Exception:
            return self._failed(
                latency_ms,
                kind=ProviderFailureKind.INVALID_OUTPUT,
                retryable=False,
                http_status=response.status_code,
            )

    def _request_body(self, req: ChoiceRequest) -> dict[str, Any]:
        state: dict[str, Any] = {"instructions": req.system}
        for key, value in req.state.items():
            if key != "instructions":
                state[key] = value
        questions = {
            f.name: {"type": "choice", "instructions": f.instructions, "criteria": dict(f.options)}
            for f in req.fields
        }
        return {
            "model": self._model,
            "state": state,
            "questions": questions,
            "provider": {"data_collection": "deny"},
        }

    def _from_response(
        self, req: ChoiceRequest, response: httpx.Response, latency_ms: int
    ) -> Attempt[ChoiceAnswer]:
        data = _json_object(response)
        usage = _usage(data)
        request_id = _safe_token(data.get("id"), _REQUEST_ID_MAX) if data is not None else None
        stop_reason = _safe_token(data.get("stop_reason"), _STOP_REASON_MAX) if data is not None else None
        status = response.status_code

        def fail(
            kind: ProviderFailureKind,
            retryable: bool,
            http_status: int | None,
            retry_after_s: float | None = None,
        ) -> Attempt[ChoiceAnswer]:
            return self._failed(
                latency_ms,
                kind=kind,
                retryable=retryable,
                http_status=http_status,
                retry_after_s=retry_after_s,
                usage=usage,
                request_id=request_id,
                stop_reason=stop_reason,
            )

        if 200 <= status < 300:
            if data is None:
                return fail(ProviderFailureKind.INVALID_OUTPUT, False, status)
            if data.get("error") is not None:
                err = data["error"]
                code = err.get("code") if isinstance(err, dict) else None
                inner = code if type(code) is int else None
                return fail(ProviderFailureKind.BODY_ERROR, inner in _BODY_ERROR_RETRYABLE_CODES, inner)
            answer = _answer(req, data)
            if answer is None:
                return fail(ProviderFailureKind.INVALID_OUTPUT, False, status)
            call = self._call(latency_ms, usage, "ok", None, request_id, stop_reason)
            return Attempt[ChoiceAnswer](value=answer, record=call, failure=None)
        if 400 <= status <= 599:
            kind, retryable, retry_after_s = _status_failure(status, response.headers)
            return fail(kind, retryable, status, retry_after_s)
        return fail(ProviderFailureKind.INVALID_OUTPUT, False, status)

    def _call(
        self,
        latency_ms: int,
        usage: _Usage,
        status: Literal["ok", "error"],
        failure: ProviderFailure | None,
        request_id: str | None,
        stop_reason: str | None,
    ) -> ProviderCall:
        input_tokens, output_tokens, reported = usage
        source: Literal["reported", "price_table"]
        if reported is not None:
            cost, source = reported, "reported"
        else:
            cost, source = input_tokens * self._price.input / 1_000_000, "price_table"
        return ProviderCall(
            provider="openrouter_jev",
            model=self._model,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=0,
            cache_write_tokens=0,
            thinking_tokens=0,
            cost_usd=cost,
            cost_source=source,
            status=status,
            failure=failure,
            provider_request_id=request_id,
            stop_reason=stop_reason,
        )

    def _failed(
        self,
        latency_ms: int,
        *,
        kind: ProviderFailureKind,
        retryable: bool,
        http_status: int | None,
        retry_after_s: float | None = None,
        usage: _Usage = _NO_USAGE,
        request_id: str | None = None,
        stop_reason: str | None = None,
    ) -> Attempt[ChoiceAnswer]:
        failure = ProviderFailure(
            kind=kind,
            provider="openrouter_jev",
            http_status=http_status,
            retry_after_s=retry_after_s,
            retryable=retryable,
            provider_request_id=request_id,
        )
        call = self._call(latency_ms, usage, "error", failure, request_id, stop_reason)
        return Attempt[ChoiceAnswer](value=None, record=call, failure=failure)
