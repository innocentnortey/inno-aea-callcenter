"""Compose: identity steps, write cards, the Settled view, change requests and scheduling results (plan-added PA-1 to PA-4)."""

from __future__ import annotations

import datetime as dt
import typing

import pytest

from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.nodes.compose_promise import UNSTAFFED_LEAD
from meridian.domain import blocks as b
from meridian.domain import identity as idn
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, OpenCase, Settled
from meridian.domain.common import CustomerId, Priority
from meridian.domain.records import ShownSlot
from meridian.domain.specialists import ChangeRequestDraft, SchedulingResult
from meridian.domain.state import Controller
from meridian.domain.turn import CheckedReply, EscalationDecision, GateKind
from meridian.policy.texts import TEXTS, TextId, render
from tests.unit.agent.nodes import compose_fixtures as fx

COMPOSER = ReplyComposer()
_HINT = "text ending 0142"
_EXPIRES = fx.DEMO_NOW + dt.timedelta(minutes=10)


def checked(text: str = "Ok.") -> CheckedReply:
    return CheckedReply(text=text, removals=(), fallback_used=False, events=())


def action(
    kind: ActionKind, turn: typing.Any = fx.TURN4, record_id: str = "201", **kw: typing.Any
) -> CompletedAction:
    fields: dict[str, typing.Any] = {"records": {"appointment": record_id}, "at": fx.DEMO_NOW}
    fields.update(kw)
    return CompletedAction(
        key=ActionKey(thread_id=fx.THREAD, turn_id=turn, kind=kind, record_id=record_id), kind=kind, **fields
    )


def blocks_of(reply: typing.Any, kind: type) -> list[typing.Any]:
    return [x for x in reply.blocks if isinstance(x, kind)]


_STEPS: list[tuple[str, typing.Any, list[tuple[str, str | None]], str | None, bool]] = [
    # (name, step, [(error code, text)], code-prompt state, verified line)
    ("located", idn.Located(masked_hint=_HINT), [], None, False),
    ("not_verified", idn.NotVerified(), [("NOT_VERIFIED", TEXTS[TextId.NOT_VERIFIED])], None, False),
    ("code_locked", idn.CodeLocked(), [("CODE_LOCKED", TEXTS[TextId.NOT_VERIFIED])], None, False),
    (
        "code_cap_reached",
        idn.CodeCapReached(),
        [("CODE_CAP_REACHED", TEXTS[TextId.NOT_VERIFIED])],
        None,
        False,
    ),
    ("code_sent", idn.CodeSent(masked_hint=_HINT, expires_at=_EXPIRES, sends_left=2), [], "sent", False),
    (
        "code_wrong",
        idn.CodeWrong(tries_left=2),
        [("CODE_WRONG", render(TextId.CODE_WRONG, n="2"))],
        "wrong",
        False,
    ),
    (
        "code_expired",
        idn.CodeExpired(resend_offered=True, sends_left=1),
        [("CODE_EXPIRED", TEXTS[TextId.CODE_EXPIRED])],
        "expired",
        False,
    ),
    (
        "verified",
        idn.Verified(
            customer_id=CustomerId("MHC-10001"), action=action(ActionKind.VERIFIED, record_id="MHC-10001")
        ),
        [],
        None,
        True,
    ),
]


@pytest.mark.parametrize("case", _STEPS, ids=lambda c: c[0])
def test_identity_steps_map_to_con2_codes(
    case: tuple[str, typing.Any, list[tuple[str, str]], str | None, bool],
) -> None:
    _, step, errors, prompt_state, verified_line = case
    st = fx.state(gate=fx.gate(GateKind.CODE_ENTRY), identity_step=step, facts=fx.facts(), checked=checked())
    reply = COMPOSER.compose(st, fx.make_ctx())
    got = [(e.code, e.text) for e in blocks_of(reply, b.ErrorBlock)]
    assert got == errors
    prompts = blocks_of(reply, b.CodePromptBlock)
    assert [p.state for p in prompts] == ([prompt_state] if prompt_state else [])
    texts = [t.text for t in blocks_of(reply, b.TextBlock)]
    assert (TEXTS[TextId.VERIFIED] in texts) is verified_line
    if step.kind == "code_expired":
        assert [o.option for o in prompts[0].options] == ["new_code"]
        assert prompts[0].resend_offered is True
    if step.kind == "code_wrong":
        assert blocks_of(reply, b.ErrorBlock)[0].tries_left == 2
        assert blocks_of(reply, b.ErrorBlock)[0].person_key is False
    if step.kind == "code_sent":
        assert (prompts[0].hint, prompts[0].resends_left, prompts[0].code_in_response) == (_HINT, 2, "never")
    if step.kind == "code_expired":
        none_offered = idn.CodeExpired(resend_offered=False, sends_left=0)
        again = COMPOSER.compose(st.model_copy(update={"identity_step": none_offered}), fx.make_ctx())
        assert blocks_of(again, b.CodePromptBlock)[0].options == ()


def test_write_cards_and_summaries() -> None:
    case = fx.handoff_result(
        "R26.safety_none", "", priority=Priority.P0, case_ref="MHC-C-0008", turn_id=fx.TURN3
    )
    open_case = OpenCase(
        case_ref=case.case.case_ref,
        reason=case.case.reason,
        priority=Priority.P0,
        state="unassigned",
        promise=case.case.promise,
        followup=None,
        live_queued=False,
    )
    booked = action(
        ActionKind.BOOKED,
        record_id="201",
        after={
            "date": "2026-10-19",
            "window": "08:00-12:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "Diagnostic fee: waived for members",
        },
    )
    cancelled = action(
        ActionKind.CANCELLED, record_id="159", before={"date": "2026-10-22", "window": "12:00-16:00"}
    )
    verified = action(
        ActionKind.VERIFIED, turn=fx.TURN3, record_id="MHC-10001", records={"customer": "MHC-10001"}
    )
    settled = Settled(
        actions=(verified, case.action, booked, cancelled), open_case=open_case, read_at=fx.DEMO_NOW
    )
    st = fx.state(
        settled=settled, gate=fx.gate(GateKind.FREE_TEXT), facts=fx.facts(), checked=checked("Done.")
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    confirmation = blocks_of(reply, b.ConfirmationBlock)[0]
    assert (confirmation.appointment_id, confirmation.window_label) == (201, "8:00 am – 12:00 pm")
    assert confirmation.timeline[0] == "Booked"
    assert confirmation.free_change_note == TEXTS[TextId.FREE_CHANGE_NOTE]
    cancel = blocks_of(reply, b.CancelledBlock)[0]
    assert (cancel.appointment_id, cancel.date, cancel.fee_line) == (
        159,
        dt.date(2026, 10, 22),
        TEXTS[TextId.CANCELLED_NO_FEE],
    )
    summaries = [w.summary for w in reply.settled_view.actions]
    print("summaries:", summaries)
    assert summaries == [
        "Verified for this chat",
        "P0 case MHC-C-0008 opened",
        "Booked Mon Oct 19, 8:00 am – 12:00 pm",
        "Cancelled Thu Oct 22 visit",
    ]
    assert [w.kind.value for w in reply.writes] == ["booked", "cancelled"]
    bare = action(ActionKind.CANCELLED, record_id="160")  # no date anywhere: no card, a generic summary
    partial = Settled(actions=(bare,), open_case=None, read_at=fx.DEMO_NOW)
    shown = COMPOSER.compose(st.model_copy(update={"settled": partial}), fx.make_ctx())
    assert blocks_of(shown, b.CancelledBlock) == []
    assert [w.summary for w in shown.settled_view.actions] == ["Cancelled a visit"]


def _identity(status: str, hint: str | None = _HINT) -> idn.IdentityState:
    return idn.IdentityState.model_validate(
        {
            "status": status,
            "customer_id": None,
            "masked_hint": hint,
            "code_expires_at": None,
            "tries_left": 3,
            "codes_sent": 1,
            "verified_at": None,
        }
    )


def test_settled_view_identity_and_request() -> None:
    result = fx.handoff_result("R26.unstaffed", TEXTS[TextId.PROMISE_UNSTAFFED], case_ref="MHC-C-0007")
    case = result.case
    open_case = OpenCase(
        case_ref=case.case_ref,
        reason=case.reason,
        priority=case.priority,
        state=case.state,
        promise=case.promise,
        followup=None,
        live_queued=False,
    )
    settled = Settled(actions=(), open_case=open_case, read_at=fx.DEMO_NOW)
    ai = Controller(kind="ai")
    seen = {
        s: COMPOSER.settled_view(settled, _identity(s), ai).identity
        for s in ("located", "code_sent", "verified", "locked")
    }
    assert (seen["located"].status, seen["located"].hint) == ("not_checked", None)
    assert (seen["code_sent"].status, seen["code_sent"].hint) == ("code_sent", _HINT)
    assert (seen["verified"].status, seen["verified"].hint) == ("verified", _HINT)
    assert (seen["locked"].status, seen["locked"].hint) == ("locked", None)
    view = COMPOSER.settled_view(
        settled, _identity("not_checked", None), Controller(kind="human", representative_name="Riley")
    )
    request = view.request
    assert request is not None
    promise = case.promise
    assert (request.reference, request.promise_text, request.due_label) == (
        "MHC-C-0007",
        UNSTAFFED_LEAD,
        "by Monday, October 19, 7:00 pm",
    )
    assert request.extra_lines == (render(TextId.REFERENCE_LINE, case_ref="MHC-C-0007"), *promise.extra_lines)
    assert request.live_queued is False
    assert (view.replying.kind, view.replying.display_name) == ("human", "Riley")
    assert COMPOSER.settled_view(settled, _identity("not_checked", None), ai).replying.display_name is None


def test_change_request_block() -> None:
    result = fx.handoff_result("R26.unstaffed", TEXTS[TextId.PROMISE_UNSTAFFED], case_ref="MHC-C-0011")
    request = action(
        ActionKind.CHANGE_REQUEST_SENT,
        record_id="159",
        after={
            "change": "move",
            "wanted_text": "Tuesday morning",
            "fee_line": "A $89 fee applies under current policy.",
        },
    )
    settled = Settled(actions=(fx.wp4f_action(), request, result.action), open_case=None, read_at=fx.DEMO_NOW)
    draft = ChangeRequestDraft(
        appointment_id=159,
        change="move",
        wanted_text="Tuesday morning",
        windows_shown=(60, 61),
        hours_before=30.0,
        window_start=fx.DEMO_NOW + dt.timedelta(hours=30),
    )
    slots = [
        ShownSlot(
            slot_id=n,
            date=dt.date(2026, 10, 20),
            window=typing.cast(typing.Any, w),
            technician="Marta Kowalski",
            service_type="hvac_repair",
            zone="north",
            member_reserved=False,
            shown_turn=fx.TURN3,
        )
        for n, w in ((60, "08:00-12:00"), (61, "12:00-16:00"), (62, "16:00-19:00"))
    ]
    st = fx.state(
        settled=settled,
        gate=fx.gate(GateKind.FREE_TEXT),
        handoff=result,
        shown_slots=slots,
        facts=fx.facts(change_request=draft, handoff=result),
        checked=checked("I sent that to our team."),
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    cards = blocks_of(reply, b.ChangeRequestBlock)
    assert len(cards) == 1
    assert not any(isinstance(x, b.HandoffBlock | b.LiveQueuedBlock) for x in reply.blocks)
    card = cards[0]
    assert [w.window_label for w in card.windows_shown] == ["8:00 am – 12:00 pm", "12:00 pm – 4:00 pm"]
    assert (card.reference, card.promise_text, card.change) == ("MHC-C-0011", UNSTAFFED_LEAD, "move")
    assert card.due_label == "by Monday, October 19, 7:00 pm"
    assert card.extra_lines == (
        render(TextId.REFERENCE_LINE, case_ref="MHC-C-0011"),
        "A person will pick this up.",
    )
    assert card.fee_line == "A $89 fee applies under current policy."
    assert card.original_stays_line == TEXTS[TextId.FEE_ORIGINAL_STAYS]
    assert reply.settled_view.visit is not None
    assert reply.settled_view.visit.status == "original_stays"


def test_scheduling_result_errors_and_booking_cap() -> None:
    def result(status: typing.Any) -> SchedulingResult:
        return SchedulingResult(status=status, tools=(), calls=())

    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        facts=fx.facts(),
        checked=checked(),
        specialist_results=[result("out_of_area"), result("booking_cap"), result("booking_cap")],
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    errors = blocks_of(reply, b.ErrorBlock)
    assert [(e.code, e.text) for e in errors] == [("OUT_OF_AREA", TEXTS[TextId.OUT_OF_AREA])]
    notices = blocks_of(reply, b.NoticeBlock)
    assert [(n.code, n.text) for n in notices] == [("BOOKING_CAP", TEXTS[TextId.BOOKING_CAP])]
    assert reply.notice is not None
    assert (reply.notice.code, reply.notice.actions) == ("BOOKING_CAP", ("talk_to_person",))


def test_failure_offer_on_escalation_offer() -> None:
    offer = EscalationDecision(outcome="offer", reason=None, priority=None, rule_id="AI.failed_answers")
    st = fx.state(gate=fx.gate(GateKind.FREE_TEXT), facts=fx.facts(), checked=checked(), escalation=offer)
    reply = COMPOSER.compose(st, fx.make_ctx())
    assert len(blocks_of(reply, b.FailureOfferBlock)) == 1
    assert blocks_of(reply, b.FailureOfferBlock)[0].text == TEXTS[TextId.FAILURE_OFFER]
    assert reply.degrade_reason is None
