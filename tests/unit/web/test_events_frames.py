"""AEA-41 (PA-3, PA-4, PA-5): frame encoding, Last-Event-ID parsing and the thread stream key, with no app."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from meridian.adapters.sqlite.rows import EventRow, thread_stream
from meridian.domain.common import ThreadId
from meridian.web.routes.events import parse_last_event_id, thread_stream_key
from meridian.web.schemas.events import (
    HEARTBEAT_FRAME,
    RESERVED_KEYS,
    chat_event_data,
    encode_event_frame,
)
from tests.api.events_support import WP2_JOINED_AT, WP2_MESSAGE_AT, payload
from tests.api.openapi_check import load_document


def _row(event_id: int, event_type: str, at: datetime) -> EventRow:
    return EventRow(
        id=event_id, stream=str(uuid.uuid4()), type=event_type, payload=payload(event_type), at=at
    )


def test_frames_match_openapi_example() -> None:
    """invariant (PA-3): the encoder reproduces the OpenAPI FRAMES example byte for byte."""
    rows = [
        _row(12, "representative_joined", WP2_JOINED_AT),
        _row(13, "ai_paused", WP2_JOINED_AT),
        _row(14, "staff_message", WP2_MESSAGE_AT),
    ]
    text = (b"".join(encode_event_frame(r) for r in rows) + HEARTBEAT_FRAME).decode().rstrip("\n")
    example = load_document()["paths"]["/api/chat/sessions/{thread_id}/events"]["get"]["responses"]["200"][
        "content"
    ]["text/event-stream"]["examples"]["FRAMES"]["value"]
    assert text == example.rstrip("\n")


def test_chat_event_data_adds_id_type_at_and_keeps_payload() -> None:
    """invariant: the row's id, type and time win over a stray payload key; other values are unchanged."""
    row = EventRow(
        id=5,
        stream="s",
        type="ai_paused",
        payload={"type": "x", "line": "kept", "event_id": 99, "at": "nope"},
        at=datetime(2026, 10, 16, 19, 22, tzinfo=UTC),
    )
    data = chat_event_data(row)
    assert data["type"] == "ai_paused" and data["event_id"] == 5
    assert data["line"] == "kept"
    assert data["at"] == "2026-10-16T14:22:00-05:00"
    assert datetime.fromisoformat(str(data["at"])) == row.at
    assert set(RESERVED_KEYS) <= set(data)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, 0),
        ("12", 12),
        (" 12 ", 12),
        ("0", 0),
        ("abc", 0),
        ("-3", 0),
        ("+5", 0),
        ("12abc", 0),
        ("1" * 19, 0),
        ("１２", 0),
        ("", 0),
    ],
)
def test_parse_last_event_id(raw: str | None, expected: int) -> None:
    """negative (PA-4): only 1 to 18 ASCII digits resume; everything else starts at 0."""
    assert parse_last_event_id(raw) == expected


def test_thread_stream_key_matches_rows() -> None:
    """invariant (PA-5): the route's stream key equals AEA-10's thread_stream."""
    tid = ThreadId(str(uuid.uuid4()))
    assert thread_stream_key(tid) == thread_stream(tid)
