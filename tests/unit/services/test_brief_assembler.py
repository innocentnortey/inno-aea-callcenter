"""AEA-29 Step 2: the pure eight-heading brief and the staff-guidance resolver (no I/O, no clock)."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from meridian.domain.common import CaseRef, InvoiceId, PassageId, ThreadId, TurnId
from meridian.domain.handoff import (
    BRIEF_ORIGINS,
    BRIEF_TITLES,
    Brief,
    BriefExtraction,
    CaseSummary,
    HandoffReason,
    Priority,
    Quote,
)
from meridian.domain.identity import IdentityState
from meridian.domain.specialists import AccountResult, InvoiceLineView, InvoiceView, StaffNote
from meridian.domain.state import ConversationState
from meridian.domain.tools import LookupRow
from meridian.domain.turn import CheckResult, TurnInput
from meridian.policy.handoff import STAFF_GUIDANCE_FOR, promise_for
from meridian.retrieval.manifest import StaffGuidance
from meridian.services._case_rules import fill_promise_text
from meridian.services.handoff import TRIM_NOTE, BriefAssembler, resolve_staff_guidance
from tests.fakes.clock import WORKED_PAIRS_NOW

NOW = WORKED_PAIRS_NOW
REFUND_TEXT = "I want a full refund on the repair. It didn't fix anything and I had to call another company."
NEED = "I want a full refund on the repair."
CLAIMS = ("It didn't fix anything", "I had to call another company")
THREAD = TypeAdapter(ThreadId).validate_python(str(uuid4()))
TURN = TypeAdapter(TurnId).validate_python(str(uuid4()))
REF = TypeAdapter(CaseRef).validate_python("MHC-C-0009")
MESSAGE_ID = 11


def _passage(reason: HandoffReason, i: int) -> StaffGuidance:
    text = STAFF_GUIDANCE_FOR[reason][0] + " (synthetic test passage)."
    return StaffGuidance(
        passage_id=PassageId(f"internal/agent_discretion_notes.md#{i}"),
        file="internal/agent_discretion_notes.md",
        section="Agents may NOT",
        version_label="undated",
        text=text,
        text_sha256=hashlib.sha256(text.strip().encode()).hexdigest(),
    )


def _case(reason: HandoffReason = HandoffReason.REFUND, presence: str = "nobody_online") -> CaseSummary:
    return CaseSummary(
        case_ref=REF,
        reason=reason,
        priority=Priority.P3,
        state="unassigned",
        created_at=NOW,
        promise=promise_for(reason, presence, NOW),  # type: ignore[arg-type]
        followup=None,
        version=1,
        seed=False,
        due_at=None,
    )


def _state(specialists: list[Any] | None = None) -> ConversationState:
    return ConversationState(
        thread_id=THREAD,
        turn_input=TurnInput(
            turn_id=TURN, message_id=MESSAGE_ID, kind="text", text_store="synthetic", received_at=NOW
        ),
        identity=IdentityState(
            status="not_checked",
            customer_id=None,
            masked_hint=None,
            code_expires_at=None,
            tries_left=3,
            codes_sent=0,
            verified_at=None,
        ),
        specialist_results=specialists or [],
    )


def _row(
    row_id: int, tool: str, *, records: tuple[str, ...] = (), passages: tuple[str, ...] = (), seen: str = "x"
) -> LookupRow:
    return LookupRow(
        id=row_id,
        thread_id=THREAD,
        tool=tool,
        record_ids=records,
        passage_ids=tuple(PassageId(p) for p in passages),
        result_seen=seen,
        message_id=MESSAGE_ID,
        turn_id=TURN,
    )


def _guidance_row(g: StaffGuidance, row_id: int = 1, *, seen: str | None = None) -> LookupRow:
    return _row(row_id, "staff_guidance", passages=(str(g.passage_id),), seen=seen or g.text_sha256)


def _texts(brief: Brief, number: int) -> list[str]:
    return [i.text for i in brief.headings[number - 1].items]


def _wp7_brief() -> tuple[Brief, CaseSummary, StaffGuidance]:
    g = _passage(HandoffReason.REFUND, 0)
    case = _case()
    assembler = BriefAssembler({g.passage_id: g})
    brief = assembler.assemble(case, _state(), [_guidance_row(g)])
    extraction = BriefExtraction(
        needs=[Quote(message_id=MESSAGE_ID, text=NEED)],
        claims=[Quote(message_id=MESSAGE_ID, text=t) for t in CLAIMS],
        open_decision="",
    )
    done = assembler.attach_extraction(brief, extraction, None, customer_messages={MESSAGE_ID: REFUND_TEXT})
    return done, case, g


def test_eight_headings_in_order() -> None:
    """AC-15: numbers 1..8, the signed titles and origins, heading 4 unchecked, every item sourced."""
    g = _passage(HandoffReason.REFUND, 0)
    brief = BriefAssembler({g.passage_id: g}).assemble(_case(), _state(), [_guidance_row(g)])
    assert [h.number for h in brief.headings] == list(range(1, 9))
    assert [h.title for h in brief.headings] == list(BRIEF_TITLES)
    assert [h.origin for h in brief.headings] == list(BRIEF_ORIGINS)
    assert [h.checked for h in brief.headings] == [True, True, True, False, True, True, True, True]
    assert brief.status == "being_written"
    assert all(item.sources for h in brief.headings for item in h.items)


def test_extraction_none_marks_not_generated() -> None:
    g = _passage(HandoffReason.REFUND, 0)
    assembler = BriefAssembler({g.passage_id: g})
    brief = assembler.attach_extraction(assembler.assemble(_case(), _state(), [_guidance_row(g)]), None, None)
    assert [h.not_generated for h in brief.headings] == [False, True, False, True, False, False, True, False]
    assert brief.status == "failed"
    assert _texts(brief, 7) == [g.text]


def test_quote_must_be_substring() -> None:
    g = _passage(HandoffReason.REFUND, 0)
    assembler = BriefAssembler({g.passage_id: g})
    base = assembler.assemble(_case(), _state(), [_guidance_row(g)])
    extraction = BriefExtraction(
        needs=[
            Quote(message_id=MESSAGE_ID, text=NEED),
            Quote(message_id=MESSAGE_ID, text="I never said this"),
        ],
        claims=[],
        open_decision="",
    )
    out = assembler.attach_extraction(base, extraction, None, customer_messages={MESSAGE_ID: REFUND_TEXT})
    h2 = out.headings[1]
    assert [i.text for i in h2.items] == [NEED]
    assert h2.trimmed is True and h2.trim_note == TRIM_NOTE
    assert out.headings[3].trimmed is False


def test_wp7_brief_items() -> None:
    brief, case, g = _wp7_brief()
    assert _texts(brief, 2) == [NEED]
    assert _texts(brief, 4) == list(CLAIMS)
    assert brief.headings[3].checked is False
    assert _texts(brief, 6) == [case.promise.text, *case.promise.extra_lines]
    assert "I can't promise an outcome." in _texts(brief, 6)
    item = brief.headings[6].items[0]
    assert item.text == g.text and item.sources[0].kind == "lookup_log"
    assert brief.status == "ready"


def test_heading_six_is_stored_promise() -> None:
    """AC-5: heading 6 is the stored promise; nothing the model wrote can change it."""
    brief, case, _ = _wp7_brief()
    assert _texts(brief, 6)[0] == case.promise.text
    unstaffed = _case(HandoffReason.CUSTOMER_REQUESTED_PERSON)
    plain = BriefAssembler().assemble(unstaffed, _state(), [])
    assert _texts(plain, 6)[0] == fill_promise_text(unstaffed.promise, str(REF))
    lie = "A representative will refund you"
    assembler = BriefAssembler()
    base = assembler.assemble(_case(), _state(), [])
    extraction = BriefExtraction(
        needs=[Quote(message_id=MESSAGE_ID, text=lie)],
        claims=[Quote(message_id=MESSAGE_ID, text=lie)],
        open_decision=lie,
    )
    out = assembler.attach_extraction(base, extraction, None, customer_messages=None)
    assert _texts(out, 6) == _texts(base, 6)


def test_staff_notes_only_in_headings_3_or_7() -> None:
    """AC-16: staff-only text enters only heading 3 (or 7), each time with a lookup_log source."""
    note = "Our fee schedule says after-hours dispatch is $149, not $144."
    invoice = InvoiceView.model_validate(
        {
            "invoice_id": "INV-204411",
            "lines": [],
            "total_cents": 47800,
            "balance_cents": 47800,
            "issued_on": dt.date(2026, 10, 1),
            "due_on": dt.date(2026, 10, 31),
            "paid": False,
        }
    )
    result = AccountResult(
        status="read",
        invoices=(invoice,),
        staff_notes=(
            StaffNote(
                kind="billed_differs_from_schedule",
                record_id=InvoiceId("INV-204411"),
                text=note,
                source_file="pricing/2026_fee_schedule.pdf",
            ),
        ),
        tools=(),
        calls=(),
    )
    row = _row(5, "read_invoices", records=("INV-204411",), seen="amount_cents=47800")
    brief = BriefAssembler().assemble(_case(HandoffReason.BILLING_DISPUTE), _state([result]), [row])
    holders = [h.number for h in brief.headings if any(note in i.text for i in h.items)]
    assert holders == [3]
    assert all(s.kind == "lookup_log" for i in brief.headings[2].items for s in i.sources)


def _dispute_invoice() -> InvoiceView:
    return InvoiceView(
        invoice_id=InvoiceId("INV-204411"),
        lines=(
            InvoiceLineView(description="Diagnostic visit", amount_cents=8900),
            InvoiceLineView(description="Contactor replacement", amount_cents=24500),
            InvoiceLineView(description="After-hours dispatch", amount_cents=14400),
        ),
        total_cents=47800,
        balance_cents=47800,
        issued_on=dt.date(2026, 10, 2),
        due_on=dt.date(2026, 11, 1),
        paid=False,
    )


def test_heading_three_lists_earlier_turn_invoice_with_lines() -> None:
    """Demo fix: an invoice read on an earlier turn is a verified fact on the handoff turn, line items included."""
    row = _row(7, "read_invoices", records=("INV-204411",), seen="amount_cents=47800")
    case = _case(HandoffReason.BILLING_DISPUTE)
    brief = BriefAssembler().assemble(case, _state(), [row], invoices=(_dispute_invoice(),))
    (text,) = _texts(brief, 3)
    assert text == (
        "Invoice INV-204411: total $478, balance $478, due 2026-11-01. "
        "Lines: Diagnostic visit $89; Contactor replacement $245; After-hours dispatch $144."
    )
    assert brief.headings[2].items[0].sources[0].ref == "7"
    # no matching lookup row (or a failed one) -> not listed
    assert _texts(BriefAssembler().assemble(case, _state(), [], invoices=(_dispute_invoice(),)), 3) == []
    failed = _row(8, "read_invoices", records=("INV-204411",), seen="failed")
    assert (
        _texts(BriefAssembler().assemble(case, _state(), [failed], invoices=(_dispute_invoice(),)), 3) == []
    )


def test_heading_three_current_turn_view_wins_and_dedupes() -> None:
    row = _row(7, "read_invoices", records=("INV-204411",), seen="amount_cents=47800")
    current = _dispute_invoice().model_copy(update={"balance_cents": 0})
    result = AccountResult(status="read", invoices=(current,), staff_notes=(), tools=(), calls=())
    brief = BriefAssembler().assemble(
        _case(HandoffReason.BILLING_DISPUTE), _state([result]), [row], invoices=(_dispute_invoice(),)
    )
    (text,) = _texts(brief, 3)
    assert "balance $0," in text


def test_guidance_text_needs_matching_hash() -> None:
    """RF-14: the passage text shows only when it is the one that was logged."""
    g = _passage(HandoffReason.REFUND, 0)
    assembler = BriefAssembler({g.passage_id: g})
    good = assembler.assemble(_case(), _state(), [_guidance_row(g)])
    assert _texts(good, 7) == [g.text]
    wrong_hash = assembler.assemble(_case(), _state(), [_guidance_row(g, seen="0" * 64)])
    assert _texts(wrong_hash, 7) == [f"Staff guidance: {g.passage_id}"]
    other = _passage(HandoffReason.LATE_TECHNICIAN, 4)
    unmapped = assembler.assemble(_case(), _state(), [_guidance_row(other)])
    assert _texts(unmapped, 7) == [f"Staff guidance: {other.passage_id}"]


def test_resolve_staff_guidance_by_prefix() -> None:
    passages = [_passage(reason, i) for i, reason in enumerate(STAFF_GUIDANCE_FOR)]
    resolved = resolve_staff_guidance(STAFF_GUIDANCE_FOR, passages)
    assert list(resolved) == list(STAFF_GUIDANCE_FOR)
    for reason, words in STAFF_GUIDANCE_FOR.items():
        assert len(resolved[reason]) == len(words)
        assert all(g.text.startswith(w) for g, w in zip(resolved[reason], words, strict=True))
    without = [p for p in passages if not p.text.startswith(STAFF_GUIDANCE_FOR[HandoffReason.REFUND][0])]
    with pytest.raises(ValueError, match="refund") as err:
        resolve_staff_guidance(STAFF_GUIDANCE_FOR, without)
    assert not any(p.text in str(err.value) for p in passages)


def test_check_removals_trim_the_decision() -> None:
    """A checked open decision is added after the guidance, and removals mark heading 7 trimmed."""
    g = _passage(HandoffReason.REFUND, 0)
    assembler = BriefAssembler({g.passage_id: g})
    base = assembler.assemble(_case(), _state(), [_guidance_row(g)])
    extraction = BriefExtraction(
        needs=[Quote(message_id=MESSAGE_ID, text=NEED)], claims=[], open_decision="Refund?"
    )
    check = CheckResult(text="Decide whether to refund.", removals=(), passed=True)
    out = assembler.attach_extraction(base, extraction, check, customer_messages=None)
    assert _texts(out, 7)[-1] == "Decide whether to refund."
    assert out.headings[6].items[-1].kind == "decision"
    assert out.headings[6].trimmed is False
