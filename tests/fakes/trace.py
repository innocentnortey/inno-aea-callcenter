"""InMemoryTraceSink (AEA-11): stores exactly what callers pass; it masks nothing (DO-6)."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from meridian.domain.common import CallRecord
from meridian.domain.turn import ExportStatus, SpanHandle, TurnIds


@dataclass(frozen=True)
class RecordedModelCall:
    record: CallRecord
    masked_input: str
    masked_output: str


@dataclass(frozen=True)
class RecordedNode:
    name: str
    elapsed_ms: int
    status: str


@dataclass(eq=False)  # identity equality: a handle's native is THIS object
class RecordedTurn:
    ids: TurnIds
    trace_id: str
    model_calls: list[RecordedModelCall] = field(default_factory=list)
    nodes: list[RecordedNode] = field(default_factory=list)
    closed: bool = False


class InMemoryTraceSink:
    """Implements TraceSink (models.md section 4) in memory."""

    def __init__(self, *, status: ExportStatus = "sent") -> None:
        self._status: ExportStatus = status
        self._turns: list[RecordedTurn] = []
        self._lock = threading.Lock()

    @property
    def turns(self) -> tuple[RecordedTurn, ...]:
        return tuple(self._turns)

    def _own(self, handle: SpanHandle) -> RecordedTurn:
        native = handle.native
        for rec in self._turns:
            if rec is native:
                return rec
        raise ValueError("span handle was not opened by this sink")

    def spans_for(self, handle: SpanHandle) -> RecordedTurn:
        return self._own(handle)

    @contextmanager
    def turn(self, ids: TurnIds) -> Iterator[SpanHandle]:
        with self._lock:
            rec = RecordedTurn(ids=ids, trace_id=format(len(self._turns) + 1, "032x"))
            self._turns.append(rec)
        handle = SpanHandle(turn_id=ids.turn_id, trace_id=rec.trace_id, native=rec)
        try:
            yield handle
        finally:
            rec.closed = True

    def model_call(
        self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str
    ) -> None:
        rec = self._own(parent)
        with self._lock:
            rec.model_calls.append(RecordedModelCall(record, masked_input, masked_output))

    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None:
        rec = self._own(parent)
        with self._lock:
            rec.nodes.append(RecordedNode(name, elapsed_ms, status))

    def export_status(self, turn: SpanHandle) -> ExportStatus:
        self._own(turn)
        return self._status
