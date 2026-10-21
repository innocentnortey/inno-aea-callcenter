"""Identity locate and verify types (AEA-02; graph-tools section 5, DO-4 section 1).

Private values (phone, code) are `SecretStr` so no log, checkpoint or prompt can print them.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_core import PydanticCustomError

from meridian.domain.actions import CompletedAction
from meridian.domain.common import CustomerId, InvoiceId, MeridianModel


class FormValues(MeridianModel):
    """CON-2 form payload values (home: turn.py)."""

    name: str | None = None
    phone: SecretStr | None = None
    customer_id: CustomerId | None = None
    invoice_number: InvoiceId | None = None
    zip_or_city: str | None = None


def _name_set(name: str | None) -> bool:
    return name is not None and bool(name.strip())


def _phone_set(phone: SecretStr | None) -> bool:
    return phone is not None and bool(phone.get_secret_value().strip())


class Locator(MeridianModel):
    """Exactly one of: name and phone together, customer_id, invoice_number."""

    name: str | None = None
    phone: SecretStr | None = None
    customer_id: CustomerId | None = None
    invoice_number: InvoiceId | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> Locator:
        name_set = _name_set(self.name)
        phone_set = _phone_set(self.phone)
        half = name_set != phone_set
        groups = (
            int(name_set and phone_set)
            + int(self.customer_id is not None)
            + int(self.invoice_number is not None)
        )
        if half or groups != 1:
            raise PydanticCustomError(
                "locator_combination",
                "exactly one locator: name and phone together, or customer_id, or invoice_number",
            )
        return self

    @classmethod
    def from_form(cls, form: FormValues) -> Locator | None:
        """The locator a form holds, or None when it is incomplete or ambiguous. Never raises."""
        name_set = _name_set(form.name)
        phone_set = _phone_set(form.phone)
        if name_set != phone_set:
            return None
        pair = name_set and phone_set
        has_customer = form.customer_id is not None
        has_invoice = form.invoice_number is not None
        if int(pair) + int(has_customer) + int(has_invoice) != 1:
            return None
        if pair:
            return cls(name=form.name, phone=form.phone)
        if has_customer:
            return cls(customer_id=form.customer_id)
        return cls(invoice_number=form.invoice_number)


class Located(MeridianModel):
    kind: Literal["located"] = "located"
    masked_hint: str


class NotVerified(MeridianModel):
    kind: Literal["not_verified"] = "not_verified"


class CodeSent(MeridianModel):
    kind: Literal["code_sent"] = "code_sent"
    masked_hint: str
    expires_at: dt.datetime
    sends_left: int = Field(ge=0, le=2)


class CodeCapReached(MeridianModel):
    kind: Literal["code_cap_reached"] = "code_cap_reached"


class Verified(MeridianModel):
    kind: Literal["verified"] = "verified"
    customer_id: CustomerId
    action: CompletedAction


class CodeWrong(MeridianModel):
    kind: Literal["code_wrong"] = "code_wrong"
    tries_left: int = Field(ge=1, le=2)


class CodeExpired(MeridianModel):
    kind: Literal["code_expired"] = "code_expired"
    resend_offered: bool
    sends_left: int = Field(ge=0, le=2)


class CodeLocked(MeridianModel):
    kind: Literal["code_locked"] = "code_locked"


# Decision D-7: the identity node maps a service result to IdentityStep (graph-tools section 5; graph-core section 8).
IdentityStep = Annotated[
    Located | NotVerified | CodeSent | CodeCapReached | Verified | CodeWrong | CodeExpired | CodeLocked,
    Field(discriminator="kind"),
]


class InboxMessage(MeridianModel):
    """graph-tools section 5 = OpenAPI InboxMessage minus `body` (the route renders it)."""

    id: str
    at: dt.datetime
    to_masked: str
    code: SecretStr | None
    status: Literal["active", "used", "expired"]
    expires_at: dt.datetime


class IdentityState(MeridianModel):
    """DO-4 section 1 (home: state.py)."""

    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None
    masked_hint: str | None
    code_expires_at: dt.datetime | None
    tries_left: int = Field(ge=0, le=3)
    codes_sent: int = Field(ge=0, le=3)
    verified_at: dt.datetime | None
