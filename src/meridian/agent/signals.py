"""The one place a graph signal is logged (graph-nodes section 4). IDs and codes only."""

from __future__ import annotations

import logging

from meridian.domain.turn import SignalRecord, TurnIds

__all__ = ["SIGNAL_LOGGER", "emit_signal"]

SIGNAL_LOGGER = "meridian.signal"


def emit_signal(ids: TurnIds, record: SignalRecord) -> None:
    """One `signal` LOG record, IDs and codes only (graph-nodes section 4). web/logging.py's allow-list formats it."""
    if record.turn_id != ids.turn_id or record.thread_id != ids.thread_id:
        raise ValueError("signal record is for another turn")
    logging.getLogger(SIGNAL_LOGGER).info("signal", extra={"signal": record.model_dump(mode="json")})
