"""Wire models of the customer chat routes: OpenAPI TurnRequest, StartSessionResponse and ChatThread."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from meridian.domain.blocks import ReplyBlock, SettledView, Speaker, TextBlock
from meridian.domain.common import EventId, MeridianModel, ThreadId, TurnId
from meridian.domain.turn import TurnPayload
from meridian.domain.views import ClockView, StaffingView
from meridian.services.session import ChatLimits
from meridian.services.turn import ChatController


class TurnRequest(MeridianModel):
    """OpenAPI TurnRequest: the client's turn id and one payload (the domain union, declared once)."""

    turn_id: TurnId
    payload: TurnPayload


class EventsRef(MeridianModel):
    """OpenAPI StartSessionResponse.events: where the CON-3 stream lives and the last event already seen."""

    url: str
    last_event_id: EventId


class StartSessionResponse(MeridianModel):
    """OpenAPI StartSessionResponse (startChatSession, 201)."""

    thread_id: ThreadId
    greeting: TextBlock
    demo_clock: ClockView
    staffing: StaffingView
    controller: ChatController
    settled: SettledView
    events: EventsRef
    limits: ChatLimits


class ChatThreadTurn(MeridianModel):
    """OpenAPI ChatThread.turns[] item."""

    turn_id: str
    speaker: Speaker
    at: dt.datetime
    text: str | None
    blocks: tuple[ReplyBlock, ...]


class ChatThread(MeridianModel):
    """OpenAPI ChatThread (getChatThread, 200)."""

    thread_id: ThreadId
    state: Literal["open", "closed", "ended_by_reset"]
    turns: tuple[ChatThreadTurn, ...]
    settled: SettledView
    demo_clock: ClockView
    staffing: StaffingView
    last_event_id: EventId
