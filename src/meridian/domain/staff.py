"""Staff surface types and constants (AEA-02; staff.md section 1, residuals R-W-1, R-W-13, R-W-14).

Imports `common` only. `LoginSessionId` has this one definition.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, NewType

from pydantic import SecretStr

from meridian.domain.common import MeridianModel


class DemoRole(StrEnum):
    CUSTOMER = "customer"
    REPRESENTATIVE = "representative"
    SUPERVISOR = "supervisor"
    OWNER = "owner"


class StaffRole(StrEnum):
    REPRESENTATIVE = "representative"
    SUPERVISOR = "supervisor"
    OWNER = "owner"


class StaffPersona(MeridianModel):
    name: str
    signature: str


STAFF_PERSONAS: Mapping[StaffRole, StaffPersona] = MappingProxyType(
    {
        StaffRole.REPRESENTATIVE: StaffPersona(name="Riley", signature="Riley (demo)"),
        StaffRole.SUPERVISOR: StaffPersona(name="Demo supervisor", signature="Demo supervisor"),
        StaffRole.OWNER: StaffPersona(name="Demo business owner", signature="Demo business owner"),
    }
)


class StaffActor(MeridianModel):
    role: StaffRole
    name: str
    signature: str

    def owns(self, owner_role: StaffRole | None) -> bool:
        return owner_role == self.role


def actor_for(role: StaffRole) -> StaffActor:
    persona = STAFF_PERSONAS[role]
    return StaffActor(role=role, name=persona.name, signature=persona.signature)


ASSIGNEE_ROLES: Mapping[str, StaffRole] = MappingProxyType(
    {"riley": StaffRole.REPRESENTATIVE, "supervisor": StaffRole.SUPERVISOR}
)
LoginSessionId = NewType("LoginSessionId", str)


class LoginSession(MeridianModel):
    session_id: LoginSessionId
    role: DemoRole
    role_reset: bool
    signed_in_at: dt.datetime  # demo clock
    expires_at: dt.datetime  # wall clock UTC


class IssuedSession(MeridianModel):
    session: LoginSession
    token: SecretStr


class SessionMissing(MeridianModel):
    """No fields."""


class SessionExpired(MeridianModel):
    """No fields."""


class RoleRefusal(MeridianModel):
    role: DemoRole
    needs: tuple[StaffRole, ...]
    reason: Literal["wrong_role", "role_reset"]


class SessionInfoData(MeridianModel):
    role: DemoRole
    display_name: str
    sees: tuple[str, ...]
    signed_in_at: dt.datetime


CUSTOMER_SPEAKER_NAME = "Customer"
ROLE_ACTIONS: Mapping[StaffRole, frozenset[str]] = MappingProxyType(
    {
        StaffRole.REPRESENTATIVE: frozenset(
            {
                "claim",
                "claim_and_join",
                "release",
                "start",
                "wait",
                "resolve",
                "close_unresolved",
                "join_chat",
                "send_live_message",
                "hand_back",
                "close_chat",
                "log_call",
                "log_email",
                "flag",
            }
        ),
        StaffRole.SUPERVISOR: frozenset(
            {
                "claim",
                "release",
                "start",
                "wait",
                "resolve",
                "close_unresolved",
                "assign",
                "change_priority",
                "flag",
            }
        ),
        StaffRole.OWNER: frozenset(),
    }
)
