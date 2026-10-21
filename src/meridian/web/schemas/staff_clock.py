"""Wire shapes for CON-8 `advanceDemoClock` (OpenAPI ClockAdvanceRequest, ClockAdvanceResponse). AEA-47.

The response carries exactly the three OpenAPI fields (R-W-17). Its values come from the demo service unchanged.
"""

from __future__ import annotations

import datetime as dt
from typing import Final, Literal, get_args

from pydantic import BaseModel, ConfigDict

from meridian.domain.common import MeridianModel

ClockStepName = Literal["plus_1h", "plus_4h", "next_business_morning"]  # = OpenAPI ClockAdvanceRequest.step
CLOCK_STEP_NAMES: Final[tuple[str, ...]] = get_args(ClockStepName)


class ClockAdvanceRequest(BaseModel):
    """Plain BaseModel: the OpenAPI allows extra properties, so they are ignored, never refused."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    step: ClockStepName


class ClockAdvanceResponse(MeridianModel):
    now: dt.datetime
    label: str
    became_overdue: int
