"""AEA-46 payload seams: PA-2 (AEA-40 relays by controller.case_ref) and PA-3 (events validate as OpenAPI events)."""

from __future__ import annotations

import json

from meridian.adapters.sqlite.rows import ConversationRow, EventRow, case_stream, thread_stream
from tests.api.openapi_check import SseFrame, assert_sse_frames_match
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.live_chat_support import (
    CUSTOMER_REPLY,
    JOIN_AT,
    RILEY,
    SECOND_REF,
    STAFF_TEXT,
    WP2_REF,
    SeededCase,
    append_customer_reply,
    new_service,
    seed_live_case,
)


def _frames(rows: list[EventRow]) -> list[SseFrame]:
    return [
        SseFrame(
            event=row.type,
            id=str(row.id),
            data=json.dumps({"event_id": row.id, "type": row.type, "at": row.at.isoformat(), **row.payload}),
        )
        for row in rows
    ]


def test_join_sets_case_ref_for_relay() -> None:
    """PA-2: the reply AEA-40 relays by controller.case_ref lands on case:MHC-C-0007."""
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow)
        new_service(db.uow).join(WP2_REF, RILEY)
        with db.uow(write=False) as tx:
            conv = tx.core.conversations.lookup(str(seeded.thread_id))
        assert isinstance(conv, ConversationRow)
        assert conv.controller.case_ref == WP2_REF
        append_customer_reply(db.uow, seeded, CUSTOMER_REPLY, JOIN_AT)
        with db.uow(write=False) as tx:
            types = [e.type for e in tx.core.events.after(case_stream(conv.controller.case_ref), 0)]
        assert types == ["controller_changed", "customer_message"]
        print("relay stream:", case_stream(WP2_REF), types)


def _run_both(db: TempStore) -> tuple[SeededCase, SeededCase]:
    uow = db.uow
    a = seed_live_case(uow)
    b = seed_live_case(uow, case_ref=SECOND_REF)
    svc = new_service(uow)
    svc.join(WP2_REF, RILEY)
    svc.send(WP2_REF, STAFF_TEXT, RILEY)
    svc.hand_back(WP2_REF, RILEY)
    svc.join(SECOND_REF, RILEY)
    svc.close(SECOND_REF, RILEY)
    return a, b


def test_thread_events_validate_as_chat_events() -> None:
    """PA-3: AEA-41 sends {event_id, type, at} + payload unchanged; the result matches streamChatEvents."""
    with temp_sqlite() as db:
        a, b = _run_both(db)
        frames: list[SseFrame] = []
        with db.uow(write=False) as tx:
            for seeded in (a, b):
                frames += _frames(tx.core.events.after(thread_stream(seeded.thread_id), 0))
        assert len(frames) == 7
        assert_sse_frames_match(frames, "streamChatEvents")


def test_case_events_validate_as_case_events() -> None:
    """PA-3: case-stream payloads render as OpenAPI CaseEvents."""
    with temp_sqlite() as db:
        _run_both(db)
        frames: list[SseFrame] = []
        with db.uow(write=False) as tx:
            for ref in (WP2_REF, SECOND_REF):
                frames += _frames(tx.core.events.after(case_stream(ref), 0))
        assert [f.event for f in frames] == [
            "controller_changed",
            "controller_changed",
            "controller_changed",
            "chat_closed",
        ]
        assert_sse_frames_match(frames, "streamCaseEvents")
