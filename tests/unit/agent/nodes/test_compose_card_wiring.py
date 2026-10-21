"""ReplyComposer.compose with the new cards, and the J-3 card-path seam (AEA-21b plan 7.1 B)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from langgraph.types import Send

from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.routers import route_after_gates
from meridian.domain import blocks as b
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.common import CustomerId, PassageId
from meridian.domain.identity import Verified
from meridian.domain.specialists import MembershipView
from meridian.domain.turn import (
    CheckedReply,
    ChoicePayload,
    EscalationDecision,
    GateKind,
    Plan,
    PlannedTask,
    TaskIntent,
)
from meridian.gates.gate import decide_gate, flags_from_state, parse_intake
from meridian.policy.texts import TEXTS, TextId
from tests.unit.agent.nodes import compose_card_fixtures as cf
from tests.unit.agent.nodes import compose_fixtures as fx

COMPOSER = ReplyComposer()
TASK = cf.BOOKING_TASK_ID


def checked(text: str = "Ok.") -> CheckedReply:
    return CheckedReply(text=text, removals=(), fallback_used=False, events=())


def of(reply: Any, kind: type) -> list[Any]:
    return [x for x in reply.blocks if isinstance(x, kind)]


def book_plan() -> Plan:
    task = PlannedTask(
        order=1,
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        needs_identity=False,
        resumes_task_id=TASK,
    )
    return Plan(mode="act", tasks=(task,), handoff_request=None, topic="booking", source="card_choice")


def wp3_state(**kw: Any) -> Any:
    fields: dict[str, Any] = {
        "gate": fx.gate(GateKind.CODE_ENTRY),
        "identity": cf.verified_identity(),
        "plan": book_plan(),
        "specialist_results": [cf.scheduling("windows_shown", cf.wp3_windows())],
        "open_tasks": [cf.booking_task()],
        "facts": fx.facts(windows_shown=cf.wp3_windows()),
        "checked": checked("There's no Saturday evening window, so here are the earliest repair windows."),
    }
    fields.update(kw)
    return fx.state(**fields)


def test_wp3_slot_card_on_code_turn() -> None:
    reply = COMPOSER.compose(wp3_state(), fx.make_ctx())
    assert [type(x) for x in reply.blocks] == [b.TextBlock, b.SlotCardBlock]
    card = reply.blocks[1]
    assert isinstance(card, b.SlotCardBlock)
    assert card.card_id == f"{TASK}.1"
    assert [o.option for o in card.options] == ["56", "42", "58"]
    assert card.days[0].label == "Mon 19 · 3 open"
    assert card.members_note is None
    assert card.urgent is False
    assert (reply.path, reply.outcome) == ("code", "acted")
    assert reply.writes == ()


def test_j3_slot_card_choice_resumes_booking_task() -> None:
    st = wp3_state()
    card = of(COMPOSER.compose(st, fx.make_ctx()), b.SlotCardBlock)[0]
    intake = parse_intake(ChoicePayload(card_id=card.card_id, option="56"))
    decision = decide_gate(intake, flags_from_state(st))
    assert decision.kind is GateKind.CARD_CHOICE
    assert decision.resume_task_id == TASK
    sends = route_after_gates(st.model_copy(update={"gate": decision, "plan": None}))
    assert isinstance(sends, list) and len(sends) == 1
    send = sends[0]
    assert isinstance(send, Send)
    planned = send.arg["planned"]
    assert planned.resumes_task_id == TASK
    assert planned.intent is TaskIntent.BOOK_NEW
    print(f"J-3 card id {card.card_id} -> routed task {planned.resumes_task_id} ({planned.intent.value})")


def test_wp3_slot_taken_shows_fresh_windows() -> None:
    st = wp3_state(
        specialist_results=[
            cf.scheduling("slot_taken", tuple(w for w in cf.wp3_windows() if w.slot_id != 56))
        ]
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    errors = of(reply, b.ErrorBlock)
    assert len(errors) == 1 and errors[0].code == "SLOT_TAKEN"
    assert errors[0].fresh_windows is not None
    assert [o.option for o in errors[0].fresh_windows.options] == ["42", "58"]
    assert of(reply, b.ConfirmationBlock) == []
    assert of(reply, b.SlotCardBlock) == []


def test_no_fit_offers_a_person_once() -> None:
    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        specialist_results=[cf.scheduling("no_fit")],
        open_tasks=[cf.booking_task()],
        escalation=EscalationDecision(
            outcome="offer", reason=None, priority=None, rule_id="AI.failed_answers"
        ),
        facts=fx.facts(),
        checked=checked("Ok."),
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    offers = of(reply, b.FailureOfferBlock)
    assert len(offers) == 1
    assert offers[0].text == TEXTS[TextId.NO_WINDOW_FITS]
    assert offers[0].person_key is True
    assert reply.degrade_reason is None


def test_urgent_after_burning_ruled_out() -> None:
    def urgent(st: Any) -> bool:
        return bool(of(COMPOSER.compose(st, fx.make_ctx()), b.SlotCardBlock)[0].urgent)

    burning = wp3_state(gate=fx.gate(GateKind.BURNING_ANSWER, burning_answer="no"))
    settled = Settled(actions=(), open_case=cf.ruled_out_case(), read_at=fx.DEMO_NOW)
    assert urgent(burning) is True
    assert urgent(wp3_state(settled=settled)) is True
    assert urgent(wp3_state()) is False


def test_wp2_invoice_card_after_verified_line() -> None:
    verified = CompletedAction(
        key=ActionKey(thread_id=fx.THREAD, turn_id=fx.TURN4, kind=ActionKind.VERIFIED, record_id="MHC-10002"),
        kind=ActionKind.VERIFIED,
        records={"customer": "MHC-10002"},
        at=fx.DEMO_NOW,
    )
    st = fx.state(
        gate=fx.gate(GateKind.CODE_ENTRY),
        identity_step=Verified(customer_id=CustomerId("MHC-10002"), action=verified),
        specialist_results=[cf.account_read(invoices=(cf.wp2_invoice(),))],
        facts=fx.facts(),
        checked=checked("Here is invoice INV-204411 as billed."),
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    assert [type(x) for x in reply.blocks] == [b.TextBlock, b.TextBlock, b.AccountCardBlock]
    assert reply.blocks[0].text == TEXTS[TextId.VERIFIED]  # type: ignore[union-attr]


def test_wp8_membership_card() -> None:
    membership = MembershipView(tier="standard", renewal_date=dt.date(2026, 11, 3))
    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        specialist_results=[cf.account_read(membership=membership)],
        facts=fx.facts(),
        checked=checked("Your membership renews soon."),
    )
    cards = of(COMPOSER.compose(st, fx.make_ctx()), b.AccountCardBlock)
    assert len(cards) == 1 and cards[0].kind == "membership"
    assert cards[0].membership is not None
    assert cards[0].membership.renewal_date == dt.date(2026, 11, 3)
    assert cards[0].membership.tier == "Comfort Club (Standard)"


def test_account_card_never_carries_staff_notes() -> None:
    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        specialist_results=[cf.account_read(invoices=(cf.wp2_invoice(),), staff_notes=(cf.staff_note(),))],
        facts=fx.facts(),
        checked=checked("Here is the invoice."),
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    assert cf.STAFF_SENTINEL not in reply.model_dump_json()
    assert of(reply, b.AccountCardBlock)


def _visit_state(intent: TaskIntent, specialist: str, settled: Settled, **kw: Any) -> Any:
    task = PlannedTask.model_validate(
        {"order": 1, "specialist": specialist, "intent": intent, "needs_identity": True}
    )
    plan = Plan(mode="act", tasks=(task,), handoff_request=None, topic="booking", source="planner")
    return fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        plan=plan,
        settled=settled,
        facts=fx.facts(),
        checked=checked(),
        **kw,
    )


def test_appointment_card_only_for_a_visit_question_without_a_write() -> None:
    settled = Settled(actions=(cf.booked_action(),), open_case=None, read_at=fx.DEMO_NOW)
    reply = COMPOSER.compose(_visit_state(TaskIntent.CONFIRM, "scheduling", settled), fx.make_ctx())
    cards = of(reply, b.AppointmentBlock)
    assert len(cards) == 1
    assert cards[0].appointment_id == 30412
    assert cards[0].window_label == "8:00 am – 12:00 pm"
    assert cards[0].label == "Your booked visit"
    read = COMPOSER.compose(_visit_state(TaskIntent.READ_APPOINTMENTS, "account", settled), fx.make_ctx())
    assert len(of(read, b.AppointmentBlock)) == 1
    talk = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        plan=Plan(mode="talk", tasks=(), handoff_request=None, topic="booking", source="planner"),
        settled=settled,
        facts=fx.facts(),
        checked=checked(),
    )
    assert of(COMPOSER.compose(talk, fx.make_ctx()), b.AppointmentBlock) == []
    none = Settled(actions=(), open_case=None, read_at=fx.DEMO_NOW)
    reply = COMPOSER.compose(_visit_state(TaskIntent.CONFIRM, "scheduling", none), fx.make_ctx())
    assert of(reply, b.AppointmentBlock) == []
    this_turn = Settled(actions=(cf.booked_action(turn=fx.TURN4),), open_case=None, read_at=fx.DEMO_NOW)
    reply = COMPOSER.compose(_visit_state(TaskIntent.CONFIRM, "scheduling", this_turn), fx.make_ctx())
    assert len(of(reply, b.ConfirmationBlock)) == 1
    assert of(reply, b.AppointmentBlock) == []


def test_where_prompt_reads_task_missing() -> None:
    def state_for(task: Any, results: list[Any]) -> Any:
        return fx.state(
            gate=fx.gate(GateKind.FREE_TEXT),
            open_tasks=[task],
            specialist_results=results,
            facts=fx.facts(),
            checked=checked("Where is the visit?"),
        )

    missing = cf.TaskWithMissing(**cf.booking_task().model_dump(), missing=("zip_needed",))
    prompts = of(COMPOSER.compose(state_for(missing, []), fx.make_ctx()), b.WherePromptBlock)
    assert len(prompts) == 1 and prompts[0].card_id == f"{TASK}.1"
    assert of(COMPOSER.compose(state_for(cf.booking_task(), []), fx.make_ctx()), b.WherePromptBlock) == []
    shown = COMPOSER.compose(
        state_for(missing, [cf.scheduling("windows_shown", cf.wp3_windows())]), fx.make_ctx()
    )
    assert len(of(shown, b.SlotCardBlock)) == 1
    assert of(shown, b.WherePromptBlock) == []


def test_quick_checks_and_slot_card_get_distinct_card_ids() -> None:
    pid = "faq/troubleshooting_before_you_call.md#1"
    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        open_tasks=[cf.booking_task()],
        facts=fx.facts(quick_checks=(PassageId(pid),), passages=(fx.passage(pid, "Check the thermostat."),)),
        specialist_results=[cf.scheduling("windows_shown", cf.wp3_windows())],
        checked=checked(),
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    assert of(reply, b.QuickChecksBlock)[0].card_id == f"{TASK}.1"
    assert of(reply, b.SlotCardBlock)[0].card_id == f"{TASK}.2"
