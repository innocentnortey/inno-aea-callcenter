"""Card builders for the compose node (AEA-21b): the labels and block ids both compose modules use, and the cards
built from specialist results and the open task.

Pure: no I/O, no model, no clock read. Sentences come from `policy/texts.py`; non-sentence labels are copied from the
OpenAPI CON-2 examples (AEA-21 PD-9) or the KB's tier headings.
"""

from __future__ import annotations

import datetime as dt
import itertools
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Literal, TypedDict

from meridian.domain import blocks as b
from meridian.domain import turn as tn
from meridian.domain.actions import Settled
from meridian.domain.common import HandoffReason
from meridian.domain.records import ShownSlot
from meridian.domain.specialists import AccountResult, SchedulingResult, SpecialistResult
from meridian.domain.state import ConversationState, OpenTask
from meridian.policy.booking import fee_note
from meridian.policy.texts import TEXTS, TextId, format_usd

__all__ = [
    "ASSISTANT",
    "DOW3",
    "MON3",
    "WINDOW_LABELS",
    "BlockIds",
    "BlockKw",
    "ErrCode",
    "NoticeCode",
    "account_cards",
    "appointment_block",
    "error_block",
    "exact_money",
    "is_urgent",
    "make_notice",
    "notice_block",
    "offer_block",
    "open_scheduling_task",
    "scheduling_cards",
    "slot_card",
    "slot_taken_error",
    "task_missing",
    "urgency_questions_block",
    "where_prompt_block",
    "window_label",
]

# --- labels that are not sentences (copied from the OpenAPI CON-2 examples) ---
ASSISTANT = b.Speaker(kind="assistant", display_name="Meridian assistant")
WINDOW_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "08:00-12:00": "8:00 am – 12:00 pm",
        "12:00-16:00": "12:00 pm – 4:00 pm",
        "13:00-17:00": "1:00 pm – 5:00 pm",
        "16:00-19:00": "4:00 pm – 7:00 pm",
    }
)
DOW3 = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MON3 = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
ErrCode = Literal[
    "SLOT_TAKEN",
    "OUT_OF_AREA",
    "CODE_WRONG",
    "CODE_EXPIRED",
    "CODE_LOCKED",
    "CODE_CAP_REACHED",
    "NOT_VERIFIED",
]
NoticeCode = Literal["AI_PAUSED", "BOOKING_CAP", "SPEND_CAP_REACHED", "TURN_TIMEOUT"]

_TIER_LABELS: Mapping[str, str] = MappingProxyType(
    {"standard": "Comfort Club (Standard)", "plus": "Comfort Club Plus"}  # KB tier headings (PD-21b-3)
)
_WHERE_LABEL = "ZIP code or city"  # OpenAPI WHERE_PROMPT; SCREEN_SPECS
_WHERE_SUBMIT = "Show windows"
_SKIP = b.Option(option="skip", label="Skip", disabled=False, reason=None)
_YES_NO_SKIP = (
    b.Option(option="yes", label="Yes", disabled=False, reason=None),
    b.Option(option="no", label="No", disabled=False, reason=None),
    _SKIP,
)
_URGENCY: tuple[tuple[str, TextId], ...] = (
    ("temp", TextId.URGENCY_HOT_COLD),
    ("water", TextId.URGENCY_WATER),
    ("risk", TextId.URGENCY_AT_RISK),
)  # OpenAPI URGENCY_QUESTIONS ids
_ZIP_NEEDED = "zip_needed"  # DO-4 §1 MissingInfo value


def window_label(window: str) -> str:
    return WINDOW_LABELS.get(window, window)


class BlockKw(TypedDict):
    block_id: str
    speaker: b.Speaker
    at: dt.datetime


class BlockIds:
    """Block ids for one reply (the k-th block gets `blk-<turn>-<k>`) and task card ids (`<task_id>.<n>`, graph-core §3)."""

    def __init__(self, ctx: tn.TurnContext) -> None:
        self.turn_id = str(ctx.ids.turn_id)
        self._at = ctx.now
        self._n = 0
        self._task_cards: dict[str, int] = {}

    def kw(self) -> BlockKw:
        self._n += 1
        return {"block_id": f"blk-{self.turn_id}-{self._n}", "speaker": ASSISTANT, "at": self._at}

    def task_card(self, task_id: str) -> str:
        """The next card id of this task in this reply: "<task_id>.1", then ".2" (PD-8 of AEA-21, now counted)."""
        n = self._task_cards.get(task_id, 0) + 1
        self._task_cards[task_id] = n
        return f"{task_id}.{n}"


def offer_block(ids: BlockIds, text: str | None = None) -> b.FailureOfferBlock:
    return b.FailureOfferBlock(
        **ids.kw(), text=TEXTS[TextId.FAILURE_OFFER] if text is None else text, person_key=True
    )


def error_block(ids: BlockIds, code: ErrCode, text: str, tries_left: int | None = None) -> b.ErrorBlock:
    return b.ErrorBlock(
        **ids.kw(),
        code=code,
        text=text,
        tries_left=tries_left,
        fresh_windows=None,
        person_key=tries_left is None,
    )


def notice_block(ids: BlockIds, code: NoticeCode, text: str) -> b.NoticeBlock:
    return b.NoticeBlock(**ids.kw(), code=code, text=text, person_key=True)


def make_notice(
    code: NoticeCode,
    actions: tuple[Literal["try_again", "talk_to_person"], ...],
    retry: str | None = None,
    to_rep: bool = False,
) -> b.Notice:
    return b.Notice(code=code, actions=actions, retry_turn_id=retry, delivered_to_representative=to_rep)


def exact_money(cents: int) -> b.Money:
    """Invoice amounts as billed, always two decimals: 8900 -> "$89.00", 125000 -> "$1,250.00", -1250 -> "-$12.50"."""
    sign = "-" if cents < 0 else ""
    dollars, rem = divmod(abs(cents), 100)
    return b.Money(amount_cents=cents, display=f"{sign}${dollars:,}.{rem:02d}")


def open_scheduling_task(state: ConversationState) -> OpenTask | None:
    """The first open task of the scheduling specialist (status != "done"), or None."""
    return next((t for t in state.open_tasks if t.specialist == "scheduling" and t.status != "done"), None)


def task_missing(task: OpenTask) -> frozenset[str]:
    """DO-4 §1 `OpenTask.missing` (MissingInfo) is not built yet (AEA-02 plan 8.2): read it by name, so the where
    prompt appears the day the field lands, and nothing happens before."""
    raw = getattr(task, "missing", None)
    return frozenset(str(m) for m in raw) if raw else frozenset()


def is_urgent(state: ConversationState, settled: Settled) -> bool:
    """The code-built urgent booking after a burning "no" (graph-nodes §6; CAS-16 A: P2 burning_ruled_out)."""
    gate = state.gate
    ruled_out_now = (
        gate is not None and gate.kind is tn.GateKind.BURNING_ANSWER and gate.burning_answer == "no"
    )
    case = settled.open_case
    return ruled_out_now or (case is not None and case.reason is HandoffReason.BURNING_RULED_OUT)


def slot_card(
    ids: BlockIds, windows: Sequence[ShownSlot], *, task: OpenTask | None, urgent: bool, verified: bool
) -> b.SlotCardBlock | None:
    if task is None or not windows:
        return None  # nothing consumed: no block id, no task card number
    ordered = sorted(windows, key=lambda s: (s.date, s.window, s.slot_id))
    card_id = ids.task_card(task.task_id)
    base = ids.kw()
    days = []
    for day, group in itertools.groupby(ordered, key=lambda s: s.date):
        ws = tuple(group)
        days.append(
            b.SlotDay(
                date=day,
                label=f"{DOW3[day.weekday()]} {day.day} · {len(ws)} open",
                open_count=len(ws),
                windows=tuple(
                    b.SlotWindow(
                        slot_id=str(s.slot_id),
                        date=s.date,
                        window=s.window,
                        window_label=window_label(s.window),
                        technician=s.technician,
                        member_only=s.member_reserved,
                        taken=False,
                    )
                    for s in ws
                ),
            )
        )
    options = tuple(
        b.Option(option=str(s.slot_id), label=window_label(s.window), disabled=False, reason=None)
        for s in ordered
    )
    fee = fee_note(ordered[0].service_type, "none")
    return b.SlotCardBlock(
        **base,
        card_id=card_id,
        options=options,
        answered=None,
        urgent=urgent,
        days=tuple(days),
        standard_fee=b.Money(amount_cents=fee.amount_cents, display=format_usd(fee.amount_cents)),
        hint=TEXTS[TextId.SLOTS_NOT_HELD],
        members_note=None if verified else TEXTS[TextId.MEMBERS_NOTE],
    )


def slot_taken_error(
    ids: BlockIds, windows: Sequence[ShownSlot], *, task: OpenTask | None, urgent: bool, verified: bool
) -> b.ErrorBlock:
    base = ids.kw()  # the error's id comes first, as in the OpenAPI example
    fresh = slot_card(ids, windows, task=task, urgent=urgent, verified=verified)
    return b.ErrorBlock(
        **base,
        code="SLOT_TAKEN",
        text=TEXTS[TextId.SLOT_TAKEN],
        tries_left=None,
        fresh_windows=fresh,
        person_key=fresh is None,
    )


def scheduling_cards(
    state: ConversationState, settled: Settled, ids: BlockIds
) -> tuple[list[b.ReplyBlock], b.Notice | None]:
    """Step 9 of compose: one block per scheduling result, then the where prompt when nothing else was shown."""
    blocks: list[b.ReplyBlock] = []
    notice: b.Notice | None = None
    task = open_scheduling_task(state)
    verified = state.identity.status == "verified"
    urgent = is_urgent(state, settled)
    for result in state.specialist_results:
        if not isinstance(result, SchedulingResult):
            continue
        if result.status == "out_of_area":
            blocks.append(error_block(ids, "OUT_OF_AREA", TEXTS[TextId.OUT_OF_AREA]))
        elif result.status == "booking_cap" and notice is None:
            notice = make_notice("BOOKING_CAP", ("talk_to_person",))
            blocks.append(notice_block(ids, "BOOKING_CAP", TEXTS[TextId.BOOKING_CAP]))
        elif result.status == "slot_taken":
            blocks.append(slot_taken_error(ids, result.windows, task=task, urgent=urgent, verified=verified))
        elif result.status == "windows_shown":
            card = slot_card(ids, result.windows, task=task, urgent=urgent, verified=verified)
            if card is not None:
                blocks.append(card)
        elif result.status == "no_fit":
            blocks.append(offer_block(ids, TEXTS[TextId.NO_WINDOW_FITS]))
    if not blocks and task is not None and _ZIP_NEEDED in task_missing(task):
        blocks.append(where_prompt_block(ids, ids.task_card(task.task_id)))
    return blocks, notice


def account_cards(ids: BlockIds, results: Sequence[SpecialistResult]) -> list[b.AccountCardBlock]:
    """Customer-facing account facts as cards (graph-tools §3): invoices as billed, membership, warranty."""
    cards: list[b.AccountCardBlock] = []
    for r in results:
        if not isinstance(r, AccountResult) or r.status != "read":
            continue
        for inv in r.invoices:
            cards.append(
                b.AccountCardBlock(
                    **ids.kw(),
                    kind="invoice",
                    invoice=b.AccountInvoice(
                        invoice_id=str(inv.invoice_id),
                        lines=tuple(
                            b.AccountInvoiceLine(
                                description=line.description,
                                amount=exact_money(line.amount_cents),
                                source=None,
                            )
                            for line in inv.lines
                        ),
                        total=exact_money(inv.total_cents),
                        balance=exact_money(inv.balance_cents),
                        due_on=inv.due_on,
                        paid=inv.paid,
                    ),
                    membership=None,
                    warranty=None,
                )
            )
        m = r.membership
        if m is not None and m.tier in _TIER_LABELS and m.renewal_date is not None:
            cards.append(
                b.AccountCardBlock(
                    **ids.kw(),
                    kind="membership",
                    invoice=None,
                    membership=b.AccountMembership(tier=_TIER_LABELS[m.tier], renewal_date=m.renewal_date),
                    warranty=None,
                )
            )
        w = r.warranty
        if w is not None:
            cards.append(
                b.AccountCardBlock(
                    **ids.kw(),
                    kind="warranty",
                    invoice=None,
                    membership=None,
                    warranty=b.AccountWarranty(install_date=w.install_date, sentence=w.sentence),
                )
            )
    return cards


def appointment_block(ids: BlockIds, visit: b.SettledVisit) -> b.AppointmentBlock:
    return b.AppointmentBlock(
        **ids.kw(),
        appointment_id=visit.appointment_id,
        date=visit.date,
        window_label=visit.window_label,
        technician=visit.technician,
        fee_line=visit.fee_line,
    )


def where_prompt_block(ids: BlockIds, card_id: str) -> b.WherePromptBlock:
    return b.WherePromptBlock(
        **ids.kw(), card_id=card_id, options=(), answered=None, label=_WHERE_LABEL, submit_label=_WHERE_SUBMIT
    )


def urgency_questions_block(ids: BlockIds, card_id: str) -> b.UrgencyQuestionsBlock:
    """Built and tested, not wired: no state asks for the questions yet and nothing consumes the answers (plan R-2)."""
    return b.UrgencyQuestionsBlock(
        **ids.kw(),
        card_id=card_id,
        options=(_SKIP,),
        answered=None,
        questions=tuple(
            b.UrgencyQuestion(question_id=qid, text=TEXTS[tid], answers=_YES_NO_SKIP) for qid, tid in _URGENCY
        ),
    )
