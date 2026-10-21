"""ReplyComposer.compose / halt_reply / handoff_block and turn_trace (AEA-21 AC-9 to AC-13; WP-4F)."""

from __future__ import annotations

import datetime as dt
import re
import typing

import pytest

from meridian.agent.nodes.compose import ReplyComposer, turn_trace
from meridian.domain import blocks as b
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.common import Halt, HaltReason, Priority, ProviderFailure, ProviderFailureKind
from meridian.domain.identity import CodeSent
from meridian.domain.specialists import AccountResult, KnowledgeResult, StaffNote
from meridian.domain.state import Controller
from meridian.domain.turn import (
    CheckedReply,
    DangerAssessment,
    DegradeReason,
    EscalationDecision,
    GateKind,
    GateResult,
    Intake,
    Plan,
    PlannedTask,
    PlannerOutcome,
    ResponderDraft,
    TaskIntent,
    TurnOutcome,
)
from meridian.policy.texts import TEXTS, TextId, render
from tests.unit.agent.nodes import compose_fixtures as fx

COMPOSER = ReplyComposer()
_CODE_SENTINEL = "914276"
_STAFF_SENTINEL = "SENTINEL-STAFF-NOTE-7731"
_CARD_ID = re.compile(r"^(burn|code|locate)-[0-9a-f-]{36}$|^[A-Za-z0-9_-]+\.[0-9]+$|^handoff-MHC-C-[0-9]{4}$")


def checked(text: str, *, fallback: bool = False) -> CheckedReply:
    return CheckedReply(text=text, removals=(), fallback_used=fallback, events=())


def talk_plan(mode: typing.Literal["talk", "act"] = "talk", tasks: tuple[PlannedTask, ...] = ()) -> Plan:
    return Plan(mode=mode, tasks=tasks, handoff_request=None, topic="other", source="planner")


def unstaffed(case_ref: str = "MHC-C-0007") -> typing.Any:
    text = render(TextId.PROMISE_UNSTAFFED, due_label="Monday, October 19, 7:00 pm", case_ref=case_ref)
    return fx.handoff_result("R26.unstaffed", text, case_ref=case_ref)


def test_wp4f_settled_view_matches_words() -> None:
    words = "Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta."
    settled = Settled(actions=(fx.wp4f_action(),), open_case=None, read_at=fx.DEMO_NOW)
    st = fx.state(
        settled=settled,
        gate=fx.gate(GateKind.FREE_TEXT),
        plan=talk_plan(),
        facts=fx.facts(),
        checked=checked(words),
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    assert [type(x) for x in reply.blocks] == [b.TextBlock]
    assert typing.cast(b.TextBlock, reply.blocks[0]).text == words
    visit = reply.settled_view.visit
    assert visit is not None
    assert (visit.date, visit.window, visit.window_label) == (
        dt.date(2026, 10, 19),
        "08:00-12:00",
        "8:00 am – 12:00 pm",
    )
    assert (visit.technician, visit.status) == ("Marta Kowalski", "moved")
    assert reply.writes == ()
    assert (reply.outcome, reply.path, reply.notice) == ("answered", "talk", None)
    trace = turn_trace(st, reply)
    print("WP-4F trace:", trace.model_dump_json())
    assert (trace.gate_result, trace.outcome, trace.degrade_reason) == ("clear", "answered", None)


def test_handoff_card_only_from_handoff_result() -> None:
    result = unstaffed()
    text = "Your reference is MHC-C-9999 and someone will call within the hour."
    st = fx.state(gate=fx.gate(GateKind.FREE_TEXT), handoff=result, facts=fx.facts(), checked=checked(text))
    reply = COMPOSER.compose(st, fx.make_ctx())
    card = reply.blocks[-1]
    assert isinstance(card, b.HandoffBlock)
    promise = result.case.promise
    assert (card.reference, card.promise_text, card.due_label) == (
        "MHC-C-0007",
        promise.text,
        promise.due_label,
    )
    assert card.extra_lines == promise.extra_lines
    assert card.card_id == "handoff-MHC-C-0007"
    assert sum(isinstance(x, b.HandoffBlock) for x in reply.blocks) == 1
    queued = fx.handoff_result("R26.staffed", TEXTS[TextId.PROMISE_STAFFED], live_queued=True)
    live = COMPOSER.handoff_block(queued)
    assert isinstance(live, b.LiveQueuedBlock)
    assert live.promise_text == TEXTS[TextId.PROMISE_STAFFED]


def test_card_ids_use_prefixes() -> None:
    from meridian.agent.nodes.compose import _burning_card_id

    turn = str(fx.TURN4)
    ask = COMPOSER.compose(fx.state(gate=fx.gate(GateKind.BURNING_ASK)), fx.make_ctx())
    burning = typing.cast(b.BurningCheckBlock, ask.blocks[0])
    assert burning.card_id == _burning_card_id(fx.TURN4) == f"burn-{turn}"
    step = CodeSent(
        masked_hint="text ending 0142", expires_at=fx.DEMO_NOW + dt.timedelta(minutes=10), sends_left=2
    )
    code = COMPOSER.compose(
        fx.state(
            gate=fx.gate(GateKind.LOCATE), identity_step=step, facts=fx.facts(), checked=checked("Sent.")
        ),
        fx.make_ctx(),
    )
    locate_plan = talk_plan(
        "act",
        (PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=True),),
    )
    locate = COMPOSER.compose(
        fx.state(
            gate=fx.gate(GateKind.FREE_TEXT),
            plan=locate_plan,
            facts=fx.facts(),
            checked=checked("One moment."),
        ),
        fx.make_ctx(),
    )
    passages = (fx.passage("faq/a.md#1", "Check the filter."),)
    quick = COMPOSER.compose(
        fx.state(
            gate=fx.gate(GateKind.FREE_TEXT),
            open_tasks=[fx.open_booking_task()],
            facts=fx.facts(passages=passages, quick_checks=(passages[0].passage_id,)),
            checked=checked("Booking."),
        ),
        fx.make_ctx(),
    )
    handoff = COMPOSER.compose(
        fx.state(
            gate=fx.gate(GateKind.PERSON), handoff=unstaffed(), facts=fx.facts(), checked=checked("OK.")
        ),
        fx.make_ctx(),
    )
    ids = {
        type(x).__name__: x.card_id
        for reply in (ask, code, locate, quick, handoff)
        for x in reply.blocks
        if hasattr(x, "card_id")
    }
    print("card ids:", ids)
    assert ids["CodePromptBlock"] == f"code-{turn}"
    assert ids["LocatePromptBlock"] == f"locate-{turn}"
    assert ids["QuickChecksBlock"] == "t-1.1"
    assert all(_CARD_ID.match(card) for card in ids.values()), ids


def test_quick_checks_inline() -> None:
    passages = (fx.passage("faq/a.md#1", "Check the filter."), fx.passage("faq/b.md#2", "Check the breaker."))
    quick_ids = (passages[1].passage_id, passages[0].passage_id)
    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        open_tasks=[fx.open_booking_task()],
        facts=fx.facts(passages=passages, quick_checks=quick_ids),
        checked=checked("Booking."),
    )
    reply = COMPOSER.compose(st, fx.make_ctx())
    cards = [x for x in reply.blocks if isinstance(x, b.QuickChecksBlock)]
    assert len(cards) == 1
    assert [o.option for o in cards[0].options] == ["skip_and_book", "show_checks"]
    assert cards[0].offer_text == TEXTS[TextId.QUICK_CHECKS_OFFER]
    assert cards[0].checks is not None
    assert [c.text for c in cards[0].checks] == ["Check the breaker.", "Check the filter."]
    assert [c.source.passage_id for c in cards[0].checks] == ["faq/b.md#2", "faq/a.md#1"]
    no_task = COMPOSER.compose(st.model_copy(update={"open_tasks": []}), fx.make_ctx())
    assert not any(isinstance(x, b.QuickChecksBlock) for x in no_task.blocks)


def test_p1_unstaffed_separate_line() -> None:
    result = fx.handoff_result(
        "OD4.danger_review", TEXTS[TextId.PROMISE_DANGER_REVIEW], priority=Priority.P1, case_ref="MHC-C-0010"
    )
    danger = DangerAssessment(label="danger", raised=True, failure=None)
    st = fx.state(gate=fx.gate(GateKind.FREE_TEXT), danger=danger, handoff=result)
    reply = COMPOSER.compose(st, fx.make_ctx())
    first = reply.blocks[0]
    assert isinstance(first, b.EmergencyLineBlock)
    assert first.separate_line == TEXTS[TextId.PROMISE_DANGER_REVIEW]
    assert first.case_reference == "MHC-C-0010"
    assert first.number in TEXTS[TextId.EMERGENCY_NUMBER_LINE]
    assert first.number_note in TEXTS[TextId.EMERGENCY_NUMBER_LINE]
    assert not any(isinstance(x, b.HandoffBlock | b.LiveQueuedBlock) for x in reply.blocks)
    unstaffed_sentence = TEXTS[TextId.PROMISE_UNSTAFFED].split(".")[0] + "."
    assert unstaffed_sentence not in reply.model_dump_json()
    assert reply.outcome == "safety_reply"
    assert reply.path == "danger"


@pytest.mark.parametrize(
    "controller",
    [Controller(kind="ai"), Controller(kind="human", representative_name="Riley")],
    ids=["ai", "human"],
)
def test_safety_instruction_first(controller: Controller) -> None:
    result = fx.handoff_result(
        "R26.safety_none", TEXTS[TextId.PROMISE_SAFETY_NONE], priority=Priority.P0, case_ref="MHC-C-0008"
    )
    st = fx.state(gate=fx.gate(GateKind.SAFETY), handoff=result, controller=controller)
    reply = COMPOSER.compose(st, fx.make_ctx())
    first = reply.blocks[0]
    assert isinstance(first, b.SafetyBlock)
    assert first.steps == (TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH])
    assert first.case_reference == "MHC-C-0008"
    assert reply.outcome == "safety_reply"
    assert [w.kind.value for w in reply.writes] == ["case_opened"]
    assert reply.settled_view.request is not None
    assert reply.settled_view.request.reference == "MHC-C-0008"
    assert reply.settled_view.replying.kind == controller.kind


def _halt(reason: HaltReason) -> Halt:
    return Halt(reason=reason, node="run_specialist", elapsed_ms=1200)


_DRAFT = ResponderDraft(text="A draft.")
_FAILED = ProviderFailure(
    kind=ProviderFailureKind.TIMEOUT,
    provider="anthropic",
    http_status=None,
    retry_after_s=None,
    retryable=True,
    provider_request_id=None,
)


def _halt_case(reason: HaltReason, *, handoff: bool = False) -> typing.Any:
    return fx.state(
        gate=fx.gate(GateKind.FREE_TEXT), halt=_halt(reason), handoff=unstaffed() if handoff else None
    )


def _cases() -> list[tuple[str, typing.Any, tuple[type, ...], str | None, str, DegradeReason | None]]:
    paused = fx.state(
        gate=fx.gate(GateKind.AI_PAUSED), controller=Controller(kind="human", representative_name="Riley")
    )
    fallback = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT), draft=None, checked=checked("", fallback=True), facts=fx.facts()
    )
    checks_fb = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        draft=_DRAFT,
        checked=checked("A draft.", fallback=True),
        facts=fx.facts(),
    )
    planner_failed = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        handoff=unstaffed(),
        facts=fx.facts(),
        checked=checked("Sorry."),
        escalation=EscalationDecision(
            outcome="escalate", reason=None, priority=Priority.P3, rule_id="AI.planner_failed", degraded=True
        ),
    )
    return [
        (
            "brake_with_handoff",
            _halt_case(HaltReason.BRAKE_TOOL_ROUNDS, handoff=True),
            (b.HandoffBlock,),
            None,
            "degraded_handoff",
            "brake",
        ),
        (
            "deadline",
            _halt_case(HaltReason.DEADLINE),
            (b.NoticeBlock,),
            "TURN_TIMEOUT",
            "degraded_handoff",
            "timeout",
        ),
        (
            "spend_cap",
            _halt_case(HaltReason.SPEND_CAP),
            (b.NoticeBlock,),
            "SPEND_CAP_REACHED",
            "degraded_handoff",
            "spend_cap",
        ),
        (
            "provider_spend_cap",
            _halt_case(HaltReason.PROVIDER_SPEND_CAP),
            (b.NoticeBlock,),
            "SPEND_CAP_REACHED",
            "degraded_handoff",
            "spend_cap",
        ),
        ("paused", paused, (b.NoticeBlock,), "AI_PAUSED", "to_staff", None),
        ("responder_failed", fallback, (b.FailureOfferBlock,), None, "degraded_handoff", "model_error"),
        (
            "checks_fallback_with_draft",
            checks_fb,
            (b.FailureOfferBlock,),
            None,
            "degraded_handoff",
            "model_error",
        ),
        ("planner_failed", planner_failed, (b.HandoffBlock,), None, "degraded_handoff", "model_error"),
    ]


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c[0])
def test_halt_and_fallback_replies(
    case: tuple[str, typing.Any, tuple[type, ...], str | None, str, DegradeReason | None],
) -> None:
    _, st, block_types, notice_code, outcome, degrade = case
    reply = COMPOSER.compose(st, fx.make_ctx())
    last = [type(x) for x in reply.blocks]
    print(case[0], last, reply.notice, reply.path, reply.outcome, reply.degrade_reason)
    assert tuple(last[-len(block_types) :]) == block_types
    assert (reply.notice.code if reply.notice else None) == notice_code
    assert (reply.outcome, reply.degrade_reason) == (outcome, degrade)
    if notice_code == "TURN_TIMEOUT":
        assert reply.notice is not None
        assert reply.notice.actions == ("try_again", "talk_to_person")
        assert reply.notice.retry_turn_id == str(fx.TURN4)
        assert typing.cast(b.NoticeBlock, reply.blocks[0]).text == TEXTS[TextId.TURN_TIMEOUT]
    if notice_code == "SPEND_CAP_REACHED":
        assert reply.notice is not None
        assert reply.notice.actions == ("talk_to_person",)
        assert typing.cast(b.NoticeBlock, reply.blocks[0]).text == TEXTS[TextId.SPEND_CAP_REACHED]
    if notice_code == "AI_PAUSED":
        assert reply.notice is not None
        assert reply.notice.delivered_to_representative is True
        assert typing.cast(b.NoticeBlock, reply.blocks[0]).text == render(
            TextId.AI_PAUSED_NOTICE, rep_name="Riley"
        )
    if outcome == "degraded_handoff":
        assert reply.path == "degraded"


def test_recursion_limit_halt_reply_works_without_graph_state() -> None:
    verified = CompletedAction(
        key=ActionKey(thread_id=fx.THREAD, turn_id=fx.TURN3, kind=ActionKind.VERIFIED, record_id="MHC-10001"),
        kind=ActionKind.VERIFIED,
        records={"customer": "MHC-10001"},
        at=fx.DEMO_NOW,
    )
    settled = Settled(actions=(verified,), open_case=None, read_at=fx.DEMO_NOW)
    reply = COMPOSER.halt_reply(_halt(HaltReason.RECURSION_LIMIT), settled, fx.make_ctx())
    assert [type(x) for x in reply.blocks] == [b.FailureOfferBlock]
    assert (reply.path, reply.outcome, reply.degrade_reason) == ("degraded", "degraded_handoff", "brake")
    assert reply.settled_view.identity.status == "verified"
    assert reply.settled_view.replying.kind == "ai"
    empty = COMPOSER.halt_reply(
        _halt(HaltReason.DEADLINE), Settled(actions=(), open_case=None, read_at=fx.DEMO_NOW), fx.make_ctx()
    )
    assert empty.settled_view.identity.status == "not_checked"
    assert empty.notice is not None


def test_no_staff_note_or_code_in_reply() -> None:
    note = StaffNote(
        kind="diagnostic_without_credit",
        record_id=typing.cast(typing.Any, "INV-100001"),
        text=_STAFF_SENTINEL,
        source_file="faq/customer_faq.md",
    )
    result = AccountResult(status="read", staff_notes=(note,), tools=(), calls=())
    intake = Intake(
        kind="code",
        text_store="",
        code_digits=typing.cast(typing.Any, _CODE_SENTINEL),
        form=None,
        card_number_seen=False,
        choice=None,
    )
    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        specialist_results=[result],
        facts=fx.facts(),
        checked=checked("Your balance is paid."),
        plan=talk_plan("act"),
    )
    reply = COMPOSER.compose(st, fx.make_ctx(intake=intake))
    dumped = reply.model_dump_json() + turn_trace(st, reply).model_dump_json()
    assert _STAFF_SENTINEL not in dumped
    assert _CODE_SENTINEL not in dumped


def _trace_state(gate_kind: GateKind, danger: str | None, **kw: typing.Any) -> typing.Any:
    label = typing.cast(typing.Literal["normal", "burning_unclear", "danger"], danger)
    assessment = None if danger is None else DangerAssessment(label=label, raised=True, failure=None)
    return fx.state(gate=fx.gate(gate_kind), danger=assessment, **kw)


@pytest.mark.parametrize(
    ("gate_kind", "danger", "expected"),
    [
        (GateKind.FREE_TEXT, "danger", "danger"),
        (GateKind.FREE_TEXT, "burning_unclear", "burning_unclear"),
        (GateKind.CODE_ENTRY, None, "clear"),
        (GateKind.LOCATE, None, "clear"),
        (GateKind.CARD_CHOICE, None, "clear"),
        (GateKind.FREE_TEXT, None, "clear"),
        (GateKind.SAFETY, None, "safety"),
        (GateKind.PERSON, None, "person_requested"),
        (GateKind.AI_PAUSED, None, "ai_paused"),
    ],
)
def test_turn_trace_values_match_do6(gate_kind: GateKind, danger: str | None, expected: str) -> None:
    st = _trace_state(gate_kind, danger, checked=checked("Ok."), facts=fx.facts())
    reply = COMPOSER.compose(st, fx.make_ctx())
    trace = turn_trace(st, reply)
    assert trace.gate_result == expected
    assert trace.danger_raised is (danger is not None)
    assert trace.gate_result in typing.get_args(GateResult)
    assert trace.outcome in typing.get_args(TurnOutcome)
    assert trace.degrade_reason is None or trace.degrade_reason in typing.get_args(DegradeReason)


def test_turn_trace_copies_planner_fields_and_specialist_order() -> None:
    planner = PlannerOutcome(
        choices=None, probabilities=None, model="jev-test", fallback_used=True, failure=_FAILED
    )
    plan = Plan(mode="act", tasks=(), handoff_request=None, topic="billing", source="fallback_planner")
    results = [
        AccountResult(status="read", tools=(), calls=()),
        KnowledgeResult(status="answered", passages=(), points=(), tools=(), calls=()),
    ]
    st = fx.state(
        gate=fx.gate(GateKind.FREE_TEXT),
        planner=planner,
        plan=plan,
        specialist_results=results,
        checked=checked("Done."),
        facts=fx.facts(),
    )
    trace = turn_trace(st, COMPOSER.compose(st, fx.make_ctx()))
    assert trace.specialists_run == ("account", "knowledge")
    assert trace.planner is not None
    assert (trace.planner.model, trace.planner.fallback_used) == ("jev-test", True)
    assert trace.planner.failure is ProviderFailureKind.TIMEOUT
    assert (trace.planner.plan_mode, trace.planner.plan_source, trace.planner.topic) == (
        "act",
        "fallback_planner",
        "billing",
    )
