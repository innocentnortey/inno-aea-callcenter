"""Wire shapes for CON-10 (OpenAPI SwitchRoleRequest, RolesResponse). ``SessionInfo`` lives in schemas/auth.py."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from meridian.domain.common import MeridianModel
from meridian.domain.staff import DemoRole


class SwitchRoleRequest(BaseModel):
    """Plain BaseModel: the OpenAPI allows extra keys, and a rejected value must never be echoed."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    role: DemoRole


class RoleLine(MeridianModel):
    role: DemoRole
    display_name: str
    sees: str


class RolesResponse(MeridianModel):
    roles: tuple[RoleLine, ...]
