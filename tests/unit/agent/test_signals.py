"""emit_signal: one codes-only LOG record, never for another turn (AEA-21 PA-6; graph-nodes section 4)."""

from __future__ import annotations

import logging

import pytest

from meridian.agent.signals import SIGNAL_LOGGER, emit_signal
from meridian.domain.common import ThreadId, TurnId
from meridian.domain.turn import SignalName, SignalRecord
from tests.unit.agent.nodes import compose_fixtures as fx


def _record(turn_id: TurnId = fx.TURN4) -> SignalRecord:
    return SignalRecord(
        name=SignalName.BRAKE_FIRED,
        turn_id=turn_id,
        thread_id=fx.THREAD,
        request_id=fx.REQ,
        run_tag="live",
        node="run_graph",
        cause="recursion_limit",
    )


def test_emit_signal_logs_one_record_codes_only(caplog: pytest.LogCaptureFixture) -> None:
    ctx = fx.make_ctx()
    with caplog.at_level(logging.INFO, logger=SIGNAL_LOGGER):
        emit_signal(ctx.ids, _record())
    records = [r for r in caplog.records if r.name == SIGNAL_LOGGER]
    assert len(records) == 1
    assert records[0].getMessage() == "signal"
    assert records[0].__dict__["signal"] == _record().model_dump(mode="json")
    print("signal extra:", records[0].__dict__["signal"])


def test_emit_signal_rejects_other_turn(caplog: pytest.LogCaptureFixture) -> None:
    ctx = fx.make_ctx()
    other = TurnId("9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d")
    with caplog.at_level(logging.INFO, logger=SIGNAL_LOGGER), pytest.raises(ValueError, match="another turn"):
        emit_signal(ctx.ids, _record(other))
    assert [r for r in caplog.records if r.name == SIGNAL_LOGGER] == []
    wrong_thread = _record().model_copy(
        update={"thread_id": ThreadId("7a8b9c0d-1e2f-4a3b-9c4d-5e6f7a8b9c0d")}
    )
    with pytest.raises(ValueError, match="another turn"):
        emit_signal(ctx.ids, wrong_thread)
