"""Wire shapes for CON-3 streamChatEvents (OpenAPI ChatEvent; stage7/web.md section 11): which event types are sent
and how one stored events row becomes one SSE frame. CON-3 only: CON-21 keeps its own (DO-3 S-11)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Final, Literal, Protocol, get_args
from zoneinfo import ZoneInfo

from pydantic import JsonValue

ChatEventType = Literal[
    "representative_joined",
    "staff_message",
    "ai_paused",
    "ai_resumed",
    "chat_closed",
    "staffing_changed",
    "shift_ended",
    "clock_changed",
    "demo_reset",
]
CHAT_EVENT_TYPES: Final[frozenset[str]] = frozenset(get_args(ChatEventType))
CLOSING_EVENT_TYPES: Final[frozenset[str]] = frozenset({"chat_closed", "demo_reset"})
RESERVED_KEYS: Final[tuple[str, ...]] = ("event_id", "type", "at")
HEARTBEAT_FRAME: Final[bytes] = b": heartbeat\n\n"
WIRE_ZONE: Final = ZoneInfo("America/Chicago")


class StoredEvent(Protocol):
    """One stored events row; AEA-10's EventRow satisfies it structurally."""

    @property
    def id(self) -> int: ...

    @property
    def type(self) -> str: ...

    @property
    def payload(self) -> Mapping[str, JsonValue]: ...

    @property
    def at(self) -> datetime: ...


def chat_event_data(event: StoredEvent) -> dict[str, JsonValue]:
    """The frame data: the row's id, type and demo-clock time first, then the stored payload unchanged."""
    data: dict[str, JsonValue] = {
        "event_id": event.id,
        "type": event.type,
        "at": event.at.astimezone(WIRE_ZONE).isoformat(),
    }
    for key, value in event.payload.items():
        if key not in RESERVED_KEYS:
            data[key] = value
    return data


def encode_event_frame(event: StoredEvent) -> bytes:
    """One SSE frame. json.dumps escapes newlines, so `data:` is always one line."""
    data = json.dumps(chat_event_data(event), ensure_ascii=False, separators=(",", ":"))
    return f"id: {event.id}\nevent: {event.type}\ndata: {data}\n\n".encode()
