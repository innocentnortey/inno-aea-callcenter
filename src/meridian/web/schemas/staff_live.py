"""Wire shapes for CON-14 liveChatAction and CON-21 streamCaseEvents (OpenAPI LiveActionRequest,
LiveActionResponse, CaseEvent; stage7/staff.md sections 5 to 7). CON-21 keeps its own frame encoder (DO-3 S-11):
nothing here is shared with web/schemas/events.py."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Final, Literal, Protocol, get_args
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError

from meridian.policy.limits import TurnLimits
from meridian.services.live_chat import LiveView

MAX_LIVE_TEXT_CHARS: Final = TurnLimits().max_message_chars  # 2000: the customer's limit (STF-12)
MAX_EVENT_ID_DIGITS: Final = 18
WIRE_ZONE: Final = ZoneInfo("America/Chicago")
CaseEventType = Literal["customer_message", "controller_changed", "chat_closed", "demo_reset", "case_changed"]
CASE_EVENT_TYPES: Final[frozenset[str]] = frozenset(get_args(CaseEventType))
CLOSING_CASE_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {"demo_reset"}
)  # NOT chat_closed (staff.md 7, step 6)
RESERVED_KEYS: Final[tuple[str, ...]] = ("event_id", "type", "at")
HEARTBEAT_FRAME: Final[bytes] = b": heartbeat\n\n"


class LiveActionRequest(BaseModel):
    """The CON-14 body. A plain BaseModel: the OpenAPI schema is open and the validator strips the text itself."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    action: Literal["join", "send", "hand_back", "close"]
    text: str | None = Field(default=None, validate_default=True)

    @field_validator("text", mode="after")
    @classmethod
    def _text_rules(cls, value: str | None, info: ValidationInfo) -> str | None:
        action = info.data.get("action")
        if action is None:
            return value  # the action already failed and its error is reported first
        if action != "send":
            if value is not None:
                raise PydanticCustomError("live_text", "only for send")
            return None
        stripped = (value or "").strip()
        if not stripped:
            raise PydanticCustomError("live_text", "required for send")
        if len(stripped) > MAX_LIVE_TEXT_CHARS:
            raise PydanticCustomError("live_text", f"at most {MAX_LIVE_TEXT_CHARS} characters")
        return stripped


class SpeakerOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["representative"]
    display_name: str


class ChatLineOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_id: str
    speaker: SpeakerOut
    at: str
    text: str


class ControllerOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["ai", "human"]
    display_name: str | None


class LiveStateOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Literal["not_live", "queued", "joined", "handed_back", "closed"]
    since: str | None
    controller: Literal["ai", "human"]


class LiveActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    controller: ControllerOut
    live: LiveStateOut
    message: ChatLineOut | None


def wire_time(value: datetime) -> str:
    return value.astimezone(WIRE_ZONE).isoformat()


def live_action_response(view: LiveView) -> LiveActionResponse:
    m = view.message
    return LiveActionResponse(
        controller=ControllerOut(kind=view.controller_kind, display_name=view.controller_name),
        live=LiveStateOut(
            state=view.state,
            since=None if view.since is None else wire_time(view.since),
            controller=view.controller_kind,
        ),
        message=None
        if m is None
        else ChatLineOut(
            message_id=m.message_id,
            speaker=SpeakerOut(kind="representative", display_name=m.speaker_name),
            at=wire_time(m.at),
            text=m.text,
        ),
    )


class StoredCaseEvent(Protocol):
    """One stored events row; AEA-10's EventRow satisfies it structurally."""

    @property
    def id(self) -> int: ...

    @property
    def type(self) -> str: ...

    @property
    def payload(self) -> Mapping[str, JsonValue]: ...

    @property
    def at(self) -> datetime: ...


def case_event_data(event: StoredCaseEvent) -> dict[str, JsonValue]:
    data: dict[str, JsonValue] = {"event_id": event.id, "type": event.type, "at": wire_time(event.at)}
    for key, value in event.payload.items():
        if key not in RESERVED_KEYS:
            data[key] = value
    return data


def encode_case_frame(event: StoredCaseEvent) -> bytes:
    data = json.dumps(case_event_data(event), ensure_ascii=False, separators=(",", ":"))
    return f"id: {event.id}\nevent: {event.type}\ndata: {data}\n\n".encode()


def parse_last_event_id(raw: str | None) -> int | None:
    """The id to resume after; anything that is not 1 to 18 ASCII digits is treated as not sent (PA-5)."""
    if raw is None:
        return None
    value = raw.strip()
    if value.isascii() and value.isdigit() and 1 <= len(value) <= MAX_EVENT_ID_DIGITS:
        return int(value)
    return None
