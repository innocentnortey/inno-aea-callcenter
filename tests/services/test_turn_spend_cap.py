"""AEA-40-F1: at our spend cap a turn the deterministic gates answer with no model still runs; every other turn is
refused. Level: mock-tested (real TurnService on a temp SQLite copy; run_graph and SpendGuard doubled). No model, no
network.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest

from meridian.domain.blocks import CallKey, SafetyBlock
from meridian.domain.common import TurnId
from meridian.domain.turn import ChoicePayload, ComposedReply, GraphOutcome, TextPayload, TurnTrace
from meridian.gates.gate import parse_intake
from meridian.policy.texts import TEXTS, TextId
from meridian.services.turn import answered_without_model
from tests.fixtures.sqlite import temp_sqlite
from tests.services.chat_doubles import (
    ASSISTANT_SPEAKER,
    FakeSpendGuard,
    ScriptedRunGraph,
    empty_view,
    make_cmd,
    make_turn_service,
    text_payload,
)
from tests.services.chat_storage import (
    conversation,
    count_rows,
    customer_messages,
    has_person_key,
    notice_codes,
    seed_thread,
    turn_row,
)

WP5 = "My carbon monoxide detector is going off."
NORMAL = "what does this invoice line mean?"


def safety_outcome(turn_id: TurnId, at: dt.datetime) -> GraphOutcome:
    block = SafetyBlock(
        block_id=f"blk-{turn_id}-1", speaker=ASSISTANT_SPEAKER, at=at, signal_word="DANGER",
        steps=(TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH]),
        call_key=CallKey(label="Call 911 (from outside)", number="911"),
        contact_line=TEXTS[TextId.SAFETY_CONTACT_LINE], case_reference=None,
    )  # fmt: skip
    reply = ComposedReply(
        blocks=(block,), settled_view=empty_view(), writes=(), notice=None,
        path="safety", outcome="safety_reply", degrade_reason=None,
    )  # fmt: skip
    return GraphOutcome(
        reply=reply, turn_trace=TurnTrace(gate_result="safety", path="safety", outcome="safety_reply")
    )


def test_safety_turn_at_cap_answered_without_model() -> None:
    """regression (WP-5): the cap used to refuse the CO alarm message with SPEND_CAP_REACHED."""
    with temp_sqlite() as store:
        guard = FakeSpendGuard(allow=False)
        graph = ScriptedRunGraph(lambda i, c: safety_outcome(i.turn_id, c.now))
        service = make_turn_service(store, run_graph=graph, spend=guard)
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload(WP5))

        result = service.run_turn(cmd)

        assert result.notice is None
        assert notice_codes(result.blocks) == []
        assert result.blocks[0].type == "safety"
        assert result.blocks[0].steps == (TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH])
        assert len(graph.calls) == 1
        assert graph.calls[0].turn_input.text_store == WP5
        assert guard.calls == 0
        row = turn_row(store, cmd.turn_id)
        assert (row.status, row.gate_result, row.outcome, row.degrade_reason) == (
            "completed", "safety", "safety_reply", None,
        )  # fmt: skip
        assert row.model_calls == 0
        assert count_rows(store, "spend_ledger") == 0
        assert len(customer_messages(store, thread, cmd.turn_id)) == 1
        assert conversation(store, thread).outcome == "safety_reply"


def test_normal_turn_at_cap_still_refused() -> None:
    """failure/refusal: a turn that needs a model is still refused at the cap and stores nothing."""
    with temp_sqlite() as store:
        guard = FakeSpendGuard(allow=False)
        graph = ScriptedRunGraph()
        service = make_turn_service(store, run_graph=graph, spend=guard)
        thread = seed_thread(store.uow)
        cmd = make_cmd(thread, text_payload(NORMAL))

        result = service.run_turn(cmd)

        assert result.notice is not None and result.notice.code == "SPEND_CAP_REACHED"
        assert result.notice.actions == ("talk_to_person",)
        assert notice_codes(result.blocks) == ["SPEND_CAP_REACHED"]
        assert has_person_key(result.blocks)
        assert graph.calls == []
        assert guard.calls == 1
        row = turn_row(store, cmd.turn_id)
        assert (row.status, row.outcome, row.degrade_reason) == ("failed", "degraded_handoff", "spend_cap")
        assert row.model_calls == 0
        assert customer_messages(store, thread) == []


def test_safety_then_normal_at_cap() -> None:
    """boundary: on one thread the cap stays reached; safety is answered, the next normal turn is refused."""
    with temp_sqlite() as store:
        guard = FakeSpendGuard(allow=False)
        graph = ScriptedRunGraph(lambda i, c: safety_outcome(i.turn_id, c.now))
        service = make_turn_service(store, run_graph=graph, spend=guard)
        thread = seed_thread(store.uow)

        first = service.run_turn(make_cmd(thread, text_payload(WP5)))
        second = service.run_turn(make_cmd(thread, text_payload(NORMAL)))

        assert first.notice is None
        assert second.notice is not None and second.notice.code == "SPEND_CAP_REACHED"
        assert len(graph.calls) == 1
        assert guard.calls == 1


ROWS: list[Any] = [
    pytest.param(TextPayload(text=WP5), True, id="safety-wp5"),
    pytest.param(
        TextPayload(text="co alarm keeps going off, can I talk to a person"), True, id="safety-plus-person"
    ),
    pytest.param(TextPayload(text="My son can't breathe, can I talk to a person"), True, id="danger-words"),
    pytest.param(
        TextPayload(text="I smell something burning, can I talk to a person"), True, id="burning-ask"
    ),
    pytest.param(ChoicePayload(card_id="burn-t1", option="yes"), True, id="burning-yes"),
    pytest.param(ChoicePayload(card_id="burn-t1", option="not_sure"), True, id="burning-unsure"),
    pytest.param(ChoicePayload(card_id="burn-t1", option="no"), False, id="burning-no"),
    pytest.param(TextPayload(text="can I talk to a person"), False, id="person"),
    pytest.param(TextPayload(text=NORMAL), False, id="free-text"),
]


@pytest.mark.parametrize(("payload", "expected"), ROWS)
def test_answered_without_model_table(payload: Any, expected: bool) -> None:
    """invariant: only gate kinds whose graph path has no model node skip the cap."""
    assert answered_without_model(parse_intake(payload)) is expected
