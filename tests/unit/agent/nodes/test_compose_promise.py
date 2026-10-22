"""FU-handoff-placeholders (AEA-55 F5): the promise reaches the screen in the UXR-19 split. Synthetic data only."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

import meridian.domain.blocks as b
from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.nodes.compose_promise import UNSTAFFED_DUE, UNSTAFFED_LEAD, PromiseWire, promise_wire
from meridian.domain.common import Presence
from meridian.domain.handoff import HandoffReason, HandoffResult, Promise
from meridian.policy.handoff import promise_for
from meridian.policy.texts import TEXTS, TextId, render
from tests.fakes import WORKED_PAIRS_NOW
from tests.unit.agent.nodes import compose_fixtures as fx

CHI = ZoneInfo("America/Chicago")
COMPOSER = ReplyComposer()


def _result(promise: Promise, case_ref: str = "MHC-C-0007") -> HandoffResult:
    base = fx.handoff_result(
        promise.policy_row, promise.text, case_ref=case_ref, live_queued=promise.live_queued
    )
    case = base.case.model_copy(update={"promise": promise, "due_at": promise.due_at})
    return base.model_copy(update={"case": case})


def _joined(block: b.HandoffBlock) -> str:
    return fx.join_uxr19(block.promise_text, block.due_label, block.extra_lines)


def test_person_request_nobody_online_card_has_no_placeholders() -> None:
    p = promise_for(HandoffReason.CUSTOMER_REQUESTED_PERSON, "nobody_online", WORKED_PAIRS_NOW)
    block = COMPOSER.handoff_block(_result(p))
    assert isinstance(block, b.HandoffBlock)
    text = _joined(block)
    assert "{" not in text and "}" not in text
    assert ".," not in text
    assert "Monday, October 19, 7:00 pm" in text
    assert "MHC-C-0007" in text
    assert text == render(
        TextId.PROMISE_UNSTAFFED, due_label="Monday, October 19, 7:00 pm", case_ref="MHC-C-0007"
    )


def test_wp7_refund_card_has_no_stray_comma() -> None:
    p = promise_for(HandoffReason.REFUND, "nobody_online", WORKED_PAIRS_NOW)
    block = COMPOSER.handoff_block(_result(p))
    assert isinstance(block, b.HandoffBlock)
    assert block.variant == "refund"
    assert block.due_label is None
    assert block.due_at == dt.datetime(2026, 10, 20, 19, 0, tzinfo=CHI)
    text = _joined(block)
    assert ".," not in text
    assert "{" not in text and "}" not in text
    assert text == (
        "A representative will get to your refund request within 2 business days. "
        "I can't promise an outcome. Your reference is MHC-C-0007."
    )


def test_unstaffed_split_rejoins_word_for_word() -> None:
    assert UNSTAFFED_LEAD == (
        "No representative is online right now. A representative will get back to you within 1 business day"
    )
    assert UNSTAFFED_DUE == "by {due_label}"
    p = promise_for(HandoffReason.CUSTOMER_REQUESTED_PERSON, "nobody_online", WORKED_PAIRS_NOW)
    w = promise_wire(p, "MHC-C-0007")
    reference = render(TextId.REFERENCE_LINE, case_ref="MHC-C-0007")
    assert w == PromiseWire(UNSTAFFED_LEAD, "by Monday, October 19, 7:00 pm", (reference,))
    assert p.due_label is not None
    assert fx.join_uxr19(*w) == render(TextId.PROMISE_UNSTAFFED, due_label=p.due_label, case_ref="MHC-C-0007")


def test_fee_bearing_change_reference_then_fee_lines() -> None:
    p = promise_for(
        HandoffReason.FEE_BEARING_CHANGE,
        "nobody_online",
        WORKED_PAIRS_NOW,
        dt.datetime(2026, 10, 17, 12, 0, tzinfo=CHI),
    )
    assert len(p.extra_lines) == 2
    w = promise_wire(p, "MHC-C-0009")
    assert w.extra_lines == (render(TextId.REFERENCE_LINE, case_ref="MHC-C-0009"), *p.extra_lines)
    joined = fx.join_uxr19(*w)
    assert "{" not in joined and "}" not in joined
    assert ".," not in joined


@pytest.mark.parametrize(
    ("reason", "presence"),
    [
        (HandoffReason.DANGER, "nobody_online"),
        (HandoffReason.SAFETY, "nobody_online"),
        (HandoffReason.REFUND, "simulated_on_shift"),
    ],
)
def test_other_rows_pass_through_without_due_label(reason: HandoffReason, presence: Presence) -> None:
    p = promise_for(reason, presence, WORKED_PAIRS_NOW)
    w = promise_wire(p, "MHC-C-0007")
    assert w == PromiseWire(p.text, None, p.extra_lines)
    if reason is HandoffReason.DANGER:
        assert ".," not in fx.join_uxr19(*w)


@pytest.mark.parametrize("presence", ["nobody_online", "simulated_on_shift"])
@pytest.mark.parametrize("reason", list(HandoffReason))
def test_every_promise_row_renders_clean(reason: HandoffReason, presence: Presence) -> None:
    p = promise_for(reason, presence, WORKED_PAIRS_NOW, dt.datetime(2026, 10, 17, 12, 0, tzinfo=CHI))
    joined = fx.join_uxr19(*promise_wire(p, "MHC-C-0007"))
    assert "{" not in joined and "}" not in joined
    assert ".," not in joined
    if p.text == TEXTS[TextId.PROMISE_UNSTAFFED]:
        assert p.due_label is not None
        assert p.due_label in joined and "MHC-C-0007" in joined
