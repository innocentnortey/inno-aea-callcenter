"""AEA-02 frozen tests: Locator accepts exactly one locator group (AC-11).

Frozen by the test-writer before the implementer starts; the implementer must not edit this file.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

from meridian.domain.common import SafeError
from meridian.domain.identity import FormValues, Locator

CUSTOMER_ID = "MHC-10001"  # issued test data
INVOICE_NUMBER = "INV-204411"  # issued test data


def _values(name: str, phone: str) -> dict[str, str]:
    return {"name": name, "phone": phone, "customer_id": CUSTOMER_ID, "invoice_number": INVOICE_NUMBER}


@pytest.mark.parametrize(
    ("keys", "valid"),
    [
        ((), False),
        (("name",), False),
        (("phone",), False),
        (("name", "phone", "customer_id"), False),
        (("customer_id", "invoice_number"), False),
        (("name", "phone", "invoice_number"), False),
        (("name", "phone"), True),
        (("customer_id",), True),
        (("invoice_number",), True),
    ],
    ids=[
        "empty",
        "name-only",
        "phone-only",
        "pair+customer",
        "customer+invoice",
        "pair+invoice",
        "ok-name+phone",
        "ok-customer_id",
        "ok-invoice_number",
    ],
)
def test_locator_exactly_one(
    keys: tuple[str, ...], valid: bool, make_sentinel: Callable[[str], str], make_phone: Callable[[], str]
) -> None:
    """[failure/refusal, AC-11] Exactly one group builds; any other combination raises without echoing name or phone."""
    name = make_sentinel("sentinel-name")
    phone = make_phone()
    supplied = {k: v for k, v in _values(name, phone).items() if k in keys}
    if valid:
        assert isinstance(Locator.model_validate(supplied), Locator)
        return
    with pytest.raises(ValidationError) as caught:
        Locator.model_validate(supplied)
    exc = caught.value
    for leaked in (name, phone):
        assert leaked not in str(exc)
        assert leaked not in repr(exc)
    problems = SafeError.from_validation_error(exc)
    assert any(p.code == "locator_combination" for p in problems), [p.code for p in problems]
    for problem in problems:
        for leaked in (name, phone):
            assert leaked not in problem.model_dump_json()


def test_locator_blank_name_with_phone_is_a_half_pair(make_phone: Callable[[], str]) -> None:
    """[boundary, AC-11] A whitespace-only name does not count as set, so name+phone is a half pair and is refused."""
    with pytest.raises(ValidationError):
        Locator.model_validate({"name": "   ", "phone": make_phone()})


@pytest.mark.parametrize(
    "keys",
    [(), ("name",), ("phone",), ("zip_or_city",), ("blank_name", "phone"), ("name", "phone", "customer_id")],
    ids=["empty", "name-only", "phone-only", "zip-only", "blank-name+phone", "two-complete-groups"],
)
def test_from_form_incomplete_is_none(
    keys: tuple[str, ...], make_sentinel: Callable[[str], str], make_phone: Callable[[], str]
) -> None:
    """[boundary, AC-11] An incomplete, empty or ambiguous form gives None and never raises."""
    name = make_sentinel("sentinel-name")
    phone = make_phone()
    data: dict[str, Any] = {}
    for key in keys:
        if key == "blank_name":
            data["name"] = "  "
        elif key == "zip_or_city":
            data[key] = "78701"
        elif key == "customer_id":
            data[key] = CUSTOMER_ID
        else:
            data[key] = {"name": name, "phone": phone}[key]
    form = FormValues.model_validate(data)
    assert Locator.from_form(form) is None


def test_from_form_complete_group_returns_only_that_group(
    make_sentinel: Callable[[str], str], make_phone: Callable[[], str]
) -> None:
    """[invariant, AC-11] A complete form group returns a Locator holding only that group's fields."""
    name = make_sentinel("sentinel-name")
    phone = make_phone()

    pair = Locator.from_form(
        FormValues.model_validate({"name": name, "phone": phone, "zip_or_city": "78701"})
    )
    assert pair is not None
    assert pair.name == name
    assert isinstance(pair.phone, SecretStr)
    assert pair.phone.get_secret_value() == phone
    assert pair.customer_id is None
    assert pair.invoice_number is None

    by_customer = Locator.from_form(FormValues.model_validate({"customer_id": CUSTOMER_ID}))
    assert by_customer is not None
    assert by_customer.customer_id == CUSTOMER_ID
    assert by_customer.name is None
    assert by_customer.phone is None
    assert by_customer.invoice_number is None

    by_invoice = Locator.from_form(FormValues.model_validate({"invoice_number": INVOICE_NUMBER}))
    assert by_invoice is not None
    assert by_invoice.invoice_number == INVOICE_NUMBER
    assert by_invoice.customer_id is None
