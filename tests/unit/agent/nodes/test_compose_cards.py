"""Pure compose card builders (AEA-21b plan 7.1 A): slot card, SLOT_TAKEN, account cards, prompts, money, ids."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

import pytest

from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.nodes.compose_cards import (
    BlockIds,
    account_cards,
    appointment_block,
    exact_money,
    offer_block,
    slot_card,
    slot_taken_error,
    urgency_questions_block,
    where_prompt_block,
)
from meridian.domain import blocks as b
from meridian.domain.actions import Settled
from meridian.domain.identity import IdentityState
from meridian.domain.specialists import AccountResult, MembershipView, WarrantyView
from meridian.domain.state import Controller
from meridian.gates.gate import card_target
from meridian.policy.texts import TEXTS, TextId
from tests.unit.agent.nodes import compose_card_fixtures as cf
from tests.unit.agent.nodes import compose_fixtures as fx

TASK = cf.BOOKING_TASK_ID


def new_ids() -> BlockIds:
    return BlockIds(fx.make_ctx())


def test_slot_card_groups_windows_by_day() -> None:
    card = slot_card(new_ids(), cf.wp3_windows(), task=cf.booking_task(), urgent=False, verified=True)
    assert card is not None
    assert card.card_id == f"{TASK}.1"
    assert [o.option for o in card.options] == ["56", "42", "58"]
    assert len(card.days) == 1
    day = card.days[0]
    assert (day.date, day.label, day.open_count) == (dt.date(2026, 10, 19), "Mon 19 · 3 open", 3)
    assert [(w.slot_id, w.technician, w.window_label) for w in day.windows] == [
        ("56", "Marta Kowalski", "8:00 am – 12:00 pm"),
        ("42", "Ray Mendoza", "12:00 pm – 4:00 pm"),
        ("58", "Marta Kowalski", "1:00 pm – 5:00 pm"),
    ]
    assert all(w.taken is False for w in day.windows)
    assert card.standard_fee == b.Money(amount_cents=8900, display="$89")
    assert card.hint == TEXTS[TextId.SLOTS_NOT_HELD]
    assert card.members_note is None
    assert card.urgent is False
    assert card.block_id == f"blk-{fx.TURN4}-1"
    other = slot_card(new_ids(), cf.wp3_windows(), task=cf.booking_task(), urgent=True, verified=False)
    assert other is not None
    assert other.members_note == TEXTS[TextId.MEMBERS_NOTE]
    assert other.urgent is True


def test_slot_card_member_window_one_open_day_and_estimate_fee() -> None:
    windows = (*cf.wp3_windows(), cf.wednesday_member_window())
    card = slot_card(new_ids(), windows, task=cf.booking_task(), urgent=False, verified=True)
    assert card is not None
    assert len(card.days) == 2
    assert card.days[1].label == "Wed 21 · 1 open"
    assert card.days[1].windows[0].member_only is True
    estimate = cf.wp3_windows()[1].model_copy(update={"service_type": "estimate"})
    single = slot_card(new_ids(), (estimate,), task=cf.booking_task(), urgent=False, verified=True)
    assert single is not None
    assert single.standard_fee == b.Money(amount_cents=0, display="$0")


def test_slot_card_omitted_without_windows_or_task() -> None:
    ids = new_ids()
    assert slot_card(ids, (), task=cf.booking_task(), urgent=False, verified=True) is None
    assert slot_card(ids, cf.wp3_windows(), task=None, urgent=False, verified=True) is None
    assert ids.kw()["block_id"] == f"blk-{fx.TURN4}-1"
    assert ids.task_card(TASK) == f"{TASK}.1"


def test_slot_taken_error_with_and_without_fresh_windows() -> None:
    err = slot_taken_error(new_ids(), cf.wp3_windows(), task=cf.booking_task(), urgent=False, verified=True)
    assert err.code == "SLOT_TAKEN"
    assert err.text == TEXTS[TextId.SLOT_TAKEN]
    assert err.tries_left is None
    assert err.person_key is False
    assert isinstance(err.fresh_windows, b.SlotCardBlock)
    assert len(err.fresh_windows.options) == 3
    assert err.block_id.endswith("-1")
    assert err.fresh_windows.block_id.endswith("-2")
    bare = slot_taken_error(new_ids(), (), task=cf.booking_task(), urgent=False, verified=True)
    assert bare.fresh_windows is None
    assert bare.person_key is True


def test_wp2_invoice_card_as_billed() -> None:
    cards = account_cards(new_ids(), [cf.account_read(invoices=(cf.wp2_invoice(),))])
    assert len(cards) == 1
    card = cards[0]
    assert card.kind == "invoice"
    assert card.membership is None and card.warranty is None
    inv = card.invoice
    assert inv is not None
    assert inv.invoice_id == "INV-204411"
    assert [ln.amount.display for ln in inv.lines] == ["$89.00", "$245.00", "$144.00"]
    assert all(ln.source is None for ln in inv.lines)
    assert inv.total.display == inv.balance.display == "$478.00"
    assert inv.due_on == dt.date(2026, 11, 1)
    assert inv.paid is False


def test_membership_and_warranty_cards_and_omitted_variants() -> None:
    renewal = dt.date(2026, 11, 3)

    def cards(result: AccountResult) -> list[b.AccountCardBlock]:
        return account_cards(new_ids(), [result])

    std = cards(cf.account_read(membership=MembershipView(tier="standard", renewal_date=renewal)))
    assert [c.kind for c in std] == ["membership"]
    assert std[0].membership is not None
    assert std[0].membership.tier == "Comfort Club (Standard)"
    plus = cards(cf.account_read(membership=MembershipView(tier="plus", renewal_date=renewal)))
    assert plus[0].membership is not None and plus[0].membership.tier == "Comfort Club Plus"
    assert cards(cf.account_read(membership=MembershipView(tier="none", renewal_date=renewal))) == []
    assert cards(cf.account_read(membership=MembershipView(tier="standard", renewal_date=None))) == []
    warranty = cards(cf.account_read(warranty=cf.warranty()))
    assert warranty[0].warranty is not None
    assert warranty[0].warranty.install_date == dt.date(2025, 6, 2)
    assert warranty[0].warranty.sentence == cf.warranty().sentence
    empty = cards(cf.account_read(invoices=(cf.wp2_invoice().model_copy(update={"lines": ()}),)))
    assert empty[0].invoice is not None and empty[0].invoice.lines == ()
    for status in ("not_verified", "failed"):
        assert cards(AccountResult.model_validate({"status": status, "tools": (), "calls": ()})) == []
    everything = cards(
        cf.account_read(
            invoices=(cf.wp2_invoice(),),
            membership=MembershipView(tier="standard", renewal_date=renewal),
            warranty=cf.warranty(),
        )
    )
    assert [c.kind for c in everything] == ["invoice", "membership", "warranty"]


def test_exact_money_formats_cents_thousands_and_credits() -> None:
    assert exact_money(8900).display == "$89.00"
    assert exact_money(125000).display == "$1,250.00"
    assert exact_money(-1250).display == "-$12.50"
    assert exact_money(5).display == "$0.05"


def test_where_prompt_and_urgency_question_shapes() -> None:
    ids = new_ids()
    where = where_prompt_block(ids, "t-1.1")
    assert (where.label, where.submit_label, where.options, where.answered) == (
        "ZIP code or city",
        "Show windows",
        (),
        None,
    )
    urgency = urgency_questions_block(ids, "t-1.2")
    assert [q.question_id for q in urgency.questions] == ["temp", "water", "risk"]
    assert [q.text for q in urgency.questions] == [
        TEXTS[TextId.URGENCY_HOT_COLD],
        TEXTS[TextId.URGENCY_WATER],
        TEXTS[TextId.URGENCY_AT_RISK],
    ]
    assert all([a.option for a in q.answers] == ["yes", "no", "skip"] for q in urgency.questions)
    assert [o.option for o in urgency.options] == ["skip"]
    assert urgency.skippable is True


def test_task_card_ids_count_per_task() -> None:
    ids = new_ids()
    assert ids.task_card("t-1") == "t-1.1"
    assert ids.task_card("t-1") == "t-1.2"
    assert ids.task_card("t-2") == "t-2.1"
    assert card_target("t-1.2") == ("task", "t-1")


def _visit_block(ids: BlockIds) -> b.AppointmentBlock:
    settled = Settled(actions=(cf.booked_action(),), open_case=None, read_at=fx.DEMO_NOW)
    identity = IdentityState(
        status="not_checked",
        customer_id=None,
        masked_hint=None,
        code_expires_at=None,
        tries_left=3,
        codes_sent=0,
        verified_at=None,
    )
    view = ReplyComposer().settled_view(settled, identity, Controller(kind="ai"))
    assert view.visit is not None
    return appointment_block(ids, view.visit)


def _slot(verified: bool, urgent: bool = False) -> Callable[[BlockIds], b.ReplyBlock]:
    def build(ids: BlockIds) -> b.ReplyBlock:
        card = slot_card(ids, cf.wp3_windows(), task=cf.booking_task(), urgent=urgent, verified=verified)
        assert card is not None
        return card

    return build


def _taken(with_fresh: bool) -> Callable[[BlockIds], b.ReplyBlock]:
    windows = cf.wp3_windows() if with_fresh else ()
    return lambda ids: slot_taken_error(ids, windows, task=cf.booking_task(), urgent=False, verified=True)


def _invoice(lines: bool) -> Callable[[BlockIds], b.ReplyBlock]:
    inv = cf.wp2_invoice() if lines else cf.wp2_invoice().model_copy(update={"lines": ()})
    return lambda ids: account_cards(ids, [cf.account_read(invoices=(inv,))])[0]


def _account(**kw: object) -> Callable[[BlockIds], b.ReplyBlock]:
    return lambda ids: account_cards(ids, [cf.account_read(**kw)])[0]  # type: ignore[arg-type]


_CASES: dict[str, Callable[[BlockIds], b.ReplyBlock]] = {
    "slot_card_verified": _slot(True),
    "slot_card_unverified_urgent": _slot(False, urgent=True),
    "slot_taken_with_fresh": _taken(True),
    "slot_taken_without_fresh": _taken(False),
    "invoice_card": _invoice(True),
    "invoice_card_no_lines": _invoice(False),
    "membership_card": _account(membership=MembershipView(tier="plus", renewal_date=dt.date(2026, 11, 3))),
    "warranty_card": _account(warranty=WarrantyView(**cf.warranty().model_dump())),
    "appointment": _visit_block,
    "where_prompt": lambda ids: where_prompt_block(ids, "t-1.1"),
    "urgency_questions": lambda ids: urgency_questions_block(ids, "t-1.1"),
    "no_fit_offer": lambda ids: offer_block(ids, TEXTS[TextId.NO_WINDOW_FITS]),
}


@pytest.mark.parametrize("build", list(_CASES.values()), ids=list(_CASES))
def test_new_blocks_match_openapi(build: Callable[[BlockIds], b.ReplyBlock]) -> None:
    cf.assert_matches_openapi(build(new_ids()))
