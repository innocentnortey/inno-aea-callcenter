"""FU-person-request (AEA-51 F-4, F-5): PersonRequestService under a held write lock, and its timed handoff child span.

Synthetic data; no model.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from meridian.services.person_request import HANDOFF_SPAN, HandoffWriteFailed, PersonRequestService
from tests.fakes.clock import FixedClock
from tests.fakes.trace import InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.person_request_support import (
    WALL_T0,
    RecordingComposer,
    RecordingHandoffService,
    WallClock,
    open_thread,
    person_request,
)

SESSION = "sess-fu-person-request"


class LockOnWrite:
    """Wraps a UnitOfWorkFactory; write transaction number `n` (1-based) fails as a busy SQLite lock does."""

    def __init__(self, inner: Any, n: int) -> None:
        self._inner = inner
        self._n = n
        self.writes = 0

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Any:
        if write or exclusive:
            self.writes += 1
            if self.writes == self._n:
                raise sqlite3.OperationalError("database is locked")
        return self._inner(write=write, exclusive=exclusive)


def _service(uow: Any, handoff: Any, trace: InMemoryTraceSink) -> PersonRequestService:
    return PersonRequestService(uow, handoff, RecordingComposer(), trace, FixedClock(), WallClock(WALL_T0))


def _case_count(store: TempStore, thread_id: Any) -> int:
    conn = sqlite3.connect(store.db_path)
    try:
        row = conn.execute("SELECT COUNT(*) FROM cases WHERE thread_id = ?", (str(thread_id),)).fetchone()
    finally:
        conn.close()
    return int(row[0])


def _turn_status(store: TempStore, turn_id: Any) -> str | None:
    with store.uow() as tx:
        row = tx.core.turns.get(turn_id)
    return None if row is None else str(row.status)


def test_claim_lock_raises_handoff_write_failed_and_writes_nothing() -> None:
    """failure (F-4, AC-48): a lock on the turn claim is HandoffWriteFailed; nothing is written."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        handoff = RecordingHandoffService(store.uow)
        trace = InMemoryTraceSink()
        service = _service(LockOnWrite(store.uow, 1), handoff, trace)
        cmd = person_request(thread, demo_session=SESSION)
        with pytest.raises(HandoffWriteFailed) as excinfo:
            service.request(cmd)
        assert "locked" not in str(excinfo.value)
        assert handoff.calls == []
        assert trace.turns == ()
        assert _turn_status(store, cmd.turn_id) is None
        assert _case_count(store, thread) == 0


def test_open_emits_one_timed_handoff_span() -> None:
    """invariant (F-5, AC-46): one timed child span named handoff, status ok."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        trace = InMemoryTraceSink()
        service = _service(store.uow, RecordingHandoffService(store.uow), trace)
        service.request(person_request(thread, demo_session=SESSION))
        assert len(trace.turns) == 1
        [node] = trace.turns[0].nodes
        assert node.name == HANDOFF_SPAN == "handoff"
        assert node.status == "ok"
        assert node.elapsed_ms >= 0


def test_failed_open_still_emits_handoff_span() -> None:
    """failure (F-5): open raising still leaves one span, status error, and the turn failed."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        trace = InMemoryTraceSink()
        service = _service(store.uow, RecordingHandoffService(store.uow, fail=True), trace)
        cmd = person_request(thread, demo_session=SESSION)
        with pytest.raises(HandoffWriteFailed):
            service.request(cmd)
        [node] = trace.turns[0].nodes
        assert node.status == "error"
        assert _turn_status(store, cmd.turn_id) == "failed"


def test_lock_on_failed_turn_write_still_raises_handoff_write_failed() -> None:
    """failure (R-3): a lock on the failed-turn write is still HandoffWriteFailed; the turn row stays running."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        trace = InMemoryTraceSink()
        handoff = RecordingHandoffService(store.uow, fail=True)
        service = _service(LockOnWrite(store.uow, 2), handoff, trace)
        cmd = person_request(thread, demo_session=SESSION)
        with pytest.raises(HandoffWriteFailed):
            service.request(cmd)
        assert _turn_status(store, cmd.turn_id) == "running"
        [node] = trace.turns[0].nodes
        assert node.status == "error"


def test_lock_on_completed_turn_write_raises_handoff_write_failed() -> None:
    """failure (R-4): a lock on the completed-turn write is HandoffWriteFailed; the case exists, the turn is running."""
    with temp_sqlite() as store:
        thread = open_thread(store, demo_session=SESSION)
        handoff = RecordingHandoffService(store.uow)
        service = _service(LockOnWrite(store.uow, 2), handoff, InMemoryTraceSink())
        cmd = person_request(thread, demo_session=SESSION)
        with pytest.raises(HandoffWriteFailed) as excinfo:
            service.request(cmd)
        assert "locked" not in str(excinfo.value)
        assert _case_count(store, thread) == 1
        assert _turn_status(store, cmd.turn_id) == "running"
