"""AEA-02 AC-2: validated ID types reject malformed values with field, code and constraint."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from meridian.domain.common import (
    CaseRef,
    CustomerId,
    InvoiceId,
    MeridianModel,
    PassageId,
    RequestId,
    SafeError,
    ThreadId,
    TurnId,
)

GOOD_UUID = "3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10"


def _holder(id_type: type) -> type[MeridianModel]:
    class Holder(MeridianModel):
        value: id_type  # type: ignore[valid-type]

    return Holder


@pytest.mark.parametrize(
    ("id_type", "bad"),
    [
        (ThreadId, "not-a-uuid"),
        (ThreadId, GOOD_UUID.upper()),
        (ThreadId, "3f1c2a4e-8b7d-1e21-9a6b-5c0d7e8f9a10"),  # version 1
        (TurnId, "not-a-uuid"),
        (TurnId, GOOD_UUID.upper()),
        (TurnId, "3f1c2a4e-8b7d-1e21-9a6b-5c0d7e8f9a10"),
        (RequestId, "not-a-uuid"),
        (RequestId, GOOD_UUID.upper()),
        (RequestId, "3f1c2a4e-8b7d-1e21-9a6b-5c0d7e8f9a10"),
        (CustomerId, "MHC-1234"),
        (CustomerId, "MHC-123456"),
        (CustomerId, "mhc-12345"),
        (InvoiceId, "INV-12345"),
        (CaseRef, "MHC-C-123"),
        (PassageId, "faq/x.md"),
        (PassageId, "faq/x.md#a"),
    ],
)
def test_malformed_ids_rejected(id_type: type, bad: str) -> None:
    holder = _holder(id_type)
    with pytest.raises(ValidationError) as caught:
        holder.model_validate({"value": bad})
    problems = SafeError.from_validation_error(caught.value)
    print([(p.field, p.code, p.constraint) for p in problems])
    assert [p.field for p in problems] == ["value"]
    assert problems[0].code == "string_pattern_mismatch"
    assert "pattern" in problems[0].constraint
    assert bad not in str(caught.value)


@pytest.mark.parametrize(
    ("id_type", "good"),
    [
        (ThreadId, GOOD_UUID),
        (TurnId, GOOD_UUID),
        (RequestId, GOOD_UUID),
        (CustomerId, "MHC-10001"),
        (InvoiceId, "INV-204411"),
        (CaseRef, "MHC-C-0042"),
        (PassageId, "faq/customer_faq.md#3"),
    ],
)
def test_valid_ids_round_trip(id_type: type, good: str) -> None:
    holder = _holder(id_type)
    built: Any = holder.model_validate({"value": good})
    assert isinstance(built.value, id_type)
    assert built.model_dump(mode="json") == {"value": good}
    assert built.model_dump_json() == f'{{"value":"{good}"}}'
