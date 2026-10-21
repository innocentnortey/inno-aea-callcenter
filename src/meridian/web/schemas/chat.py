"""Wire models of the customer chat routes (OpenAPI TurnRequest; the CON-1 models arrive with the session service)."""

from __future__ import annotations

from meridian.domain.common import MeridianModel, TurnId
from meridian.domain.turn import TurnPayload


class TurnRequest(MeridianModel):
    """OpenAPI TurnRequest: the client's turn id and one payload (the domain union, declared once)."""

    turn_id: TurnId
    payload: TurnPayload
