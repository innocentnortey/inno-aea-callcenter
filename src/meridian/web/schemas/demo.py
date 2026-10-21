"""Wire shapes for CON-6 to CON-9 (OpenAPI InboxResponse, InboxMessage, Staffing, StaffingRequest,
StaffingResponse, DemoClock, ResetRequest, ResetResponse). AEA-43.

`InboxMessageOut` keeps `body` and `code` as `SecretStr`; `repr` and python-mode dumps show asterisks; only
`model_dump(mode="json")` reveals them (D3; graph-tools §5, C-10).
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, SecretStr, StrictBool, field_serializer, field_validator

from meridian.domain.common import MeridianModel

StaffingMode = Literal["nobody_online", "simulated_on_shift"]
InboxStatus = Literal["active", "used", "expired"]


class InboxMessageOut(MeridianModel):
    """OpenAPI InboxMessage. The only wire model that carries a code (DATA CLASS: secret)."""

    id: str
    at: dt.datetime
    to_masked: str
    body: SecretStr
    code: SecretStr
    status: InboxStatus
    expires_at: dt.datetime

    @field_serializer("body", "code", when_used="json")
    def _reveal(self, value: SecretStr) -> str:
        return value.get_secret_value()


class InboxResponse(MeridianModel):
    messages: tuple[InboxMessageOut, ...]


class Staffing(MeridianModel):
    mode: StaffingMode
    label: str
    banner: str | None


class StaffingRequest(BaseModel):
    """Plain BaseModel: the OpenAPI allows extra properties, so they are ignored, never refused."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    mode: StaffingMode


class StaffingResponse(MeridianModel):
    mode: StaffingMode
    label: str
    converted_cases: int


class DemoClock(MeridianModel):
    now: dt.datetime
    label: str
    date_label: str


class ResetRequest(BaseModel):
    """`confirm` must be the JSON boolean true (OpenAPI const true). StrictBool refuses 1, 1.0 and "true", which
    Literal[True] would accept."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    confirm: StrictBool

    @field_validator("confirm")
    @classmethod
    def _must_be_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("must be true")
        return value


class ResetResponse(MeridianModel):
    ok: Literal[True]
    open_chats_ended: int
    roles_reset: int
    clock: DemoClock
