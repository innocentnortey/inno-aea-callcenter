"""AEA-02 AC-16: CallRecord.from_provider and the re-exports of types defined in the domain."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import meridian.domain.common as common
import meridian.domain.records as records
import meridian.domain.turn as turn
import meridian.ports.models as port_models
import meridian.ports.runtime as port_runtime
from meridian.domain.common import ProviderCall, ProviderFailure, ProviderFailureKind, Role
from meridian.ports.models import CallRecord


def _call() -> ProviderCall:
    return ProviderCall(
        provider="anthropic",
        model="model-x",
        latency_ms=120,
        input_tokens=11,
        output_tokens=7,
        cache_read_tokens=3,
        cache_write_tokens=2,
        thinking_tokens=1,
        cost_usd=0.0123,
        cost_source="price_table",
        status="error",
        failure=ProviderFailure(
            kind=ProviderFailureKind.OVERLOADED,
            provider="anthropic",
            http_status=529,
            retry_after_s=1.5,
            retryable=True,
            provider_request_id="req-1",
        ),
        provider_request_id="req-1",
        stop_reason="end_turn",
    )


def test_from_provider_copies_every_field() -> None:
    call = _call()
    record = CallRecord.from_provider(call, role=Role.SPECIALIST, attempt=2)
    assert set(CallRecord.model_fields) == set(ProviderCall.model_fields) | {"role", "attempt"}
    for name in ProviderCall.model_fields:
        assert getattr(record, name) == getattr(call, name), name
    assert record.role == Role.SPECIALIST
    assert record.attempt == 2


@pytest.mark.parametrize("attempt", [0, 3])
def test_attempt_bounds(attempt: int) -> None:
    with pytest.raises(ValidationError):
        CallRecord.from_provider(_call(), role=Role.PLANNER, attempt=attempt)


def test_reexports_are_the_domain_types() -> None:
    assert port_models.CallRecord is common.CallRecord
    assert port_models.Role is common.Role
    assert port_models.ProviderCall is common.ProviderCall
    assert port_runtime.SpanHandle is turn.SpanHandle
    assert port_runtime.ExportStatus is turn.ExportStatus
    assert port_runtime.RetrievalResult is records.RetrievalResult
