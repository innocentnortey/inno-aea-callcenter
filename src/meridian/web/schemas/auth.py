"""Wire shapes for CON-22 `login` (OpenAPI LoginRequest, LoginResponse, SessionInfo)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictStr

from meridian.domain.common import MeridianModel
from meridian.domain.staff import DemoRole


class LoginRequest(BaseModel):
    """Plain BaseModel: MeridianModel strips whitespace, which would change a password."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    username: StrictStr
    password: StrictStr


class SessionInfo(MeridianModel):
    authenticated: Literal[True]
    role: DemoRole
    display_name: str
    sees: tuple[str, ...]
    signed_in_at: datetime


class LoginResponse(MeridianModel):
    session: SessionInfo
    landing: str
