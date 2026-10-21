"""Request and response bodies for CON-4 and CON-5 (AEA-42; OpenAPI HandoffRequest, FollowUpRequest, FollowUpResponse)."""

from __future__ import annotations

from typing import Final, Literal

from meridian.domain.blocks import SettledView
from meridian.domain.common import FollowUp, MeridianModel, TurnId

HANDOFF_RETRY_AFTER_MS: Final = 3000  # [A] the OpenAPI requestPerson 503 example's details.retry_after_ms


class HandoffRequestBody(MeridianModel):
    """OpenAPI HandoffRequest."""

    turn_id: TurnId


class FollowUpRequestBody(MeridianModel):
    """OpenAPI FollowUpRequest (the same three fields as AEA-29's FollowUpChoice)."""

    channel: Literal["email", "phone"]
    destination: Literal["on_record", "general"]
    window: Literal["morning", "afternoon", "any"]


class FollowUpResponse(MeridianModel):
    """OpenAPI FollowUpResponse."""

    followup: FollowUp
    settled: SettledView
