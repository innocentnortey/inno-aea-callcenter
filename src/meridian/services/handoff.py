"""Handoff (A6): opens a case in one write transaction, and assembles the eight-heading brief for staff.

`HandoffService` reads presence, takes the promise from policy, and writes the case, its first event, the promise row,
the case_opened action, the thread-stream event and the staff-guidance lookup rows together, or not at all.
`BriefAssembler` is pure: it builds the brief from stored state and never writes a promise word of its own.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Protocol

from meridian.domain.actions import ActionKind
from meridian.domain.common import PassageId
from meridian.domain.handoff import (
    BRIEF_KEYS,
    BRIEF_ORIGINS,
    BRIEF_TITLES,
    Brief,
    BriefExtraction,
    BriefHeading,
    BriefItem,
    CaseSummary,
    HandoffReason,
    HandoffRequest,
    HandoffResult,
    Presence,
    Quote,
    SourceRef,
)
from meridian.domain.specialists import AccountResult, InvoiceView, KnowledgeResult
from meridian.domain.state import ConversationState
from meridian.domain.tools import LookupEntry, LookupRow
from meridian.domain.turn import CheckResult, TurnContext
from meridian.policy.handoff import promise_for
from meridian.policy.texts import format_usd
from meridian.ports.runtime import Clock, UnitOfWork, UnitOfWorkFactory
from meridian.services._case_rules import (
    PRIORITY_WORD,
    fill_promise_text,
    identity_view,
    reason_label,
    row_title,
)

if TYPE_CHECKING:
    from meridian.retrieval.manifest import StaffGuidance
    from meridian.services.cases import CaseService

__all__ = ["TRIM_NOTE", "BriefAssembler", "CaseWriteFailed", "HandoffService", "resolve_staff_guidance"]

# [Source: SCREEN_SPECS SCR-6; OpenAPI getCase TRIMMED_STOP trim_note] staff copy
TRIM_NOTE: Final = "Something here didn't match the record and was removed."


class CaseWriteFailed(Exception):
    """The case write failed twice (DO-1 section 8.2). Carries no value."""

    def __init__(self, attempts: int = 2) -> None:
        super().__init__(f"case write failed after {attempts} attempts")
        self.attempts = attempts
        self.cause = "write_error"


def resolve_staff_guidance(
    prefixes: Mapping[HandoffReason, tuple[str, ...]], passages: Sequence[StaffGuidance]
) -> Mapping[HandoffReason, tuple[StaffGuidance, ...]]:
    """Maps each reason's text prefixes to the one passage that starts with each; a prefix with no passage fails."""
    resolved: dict[HandoffReason, tuple[StaffGuidance, ...]] = {}
    for reason, words in prefixes.items():
        found: list[StaffGuidance] = []
        for word in words:
            match = next((g for g in passages if g.text.startswith(word)), None)
            if match is None:
                raise ValueError(f"staff guidance prefix matches no passage: {reason.value}")
            found.append(match)
        resolved[reason] = tuple(found)
    return MappingProxyType(resolved)


class _PresenceSource(Protocol):
    """Typing only: AEA-30's DemoService and the container forwarder fit it."""

    def presence(self, tx: UnitOfWork | None = None) -> Presence: ...


class HandoffService:
    """Opens a case for a handoff request: one write unit of work, retried once, typed failure."""

    def __init__(
        self,
        uow: UnitOfWorkFactory,
        cases: CaseService,
        demo: _PresenceSource,
        clock: Clock,
        staff_guidance: Mapping[HandoffReason, tuple[StaffGuidance, ...]] | None = None,
    ) -> None:
        self._uow = uow
        self._cases = cases
        self._demo = demo
        self._clock = clock
        self._staff_guidance = dict(staff_guidance or {})

    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult:
        """Opens (or joins) the thread's case; the whole write is retried once before it fails."""
        now = ctx.now
        window_start = req.change_request.window_start if req.change_request else None
        last: Exception | None = None
        for _attempt in (1, 2):
            try:
                with self._uow(write=True) as tx:
                    result = self._open_in(tx, req, now, window_start)
                    tx.commit()
                return result
            except Exception as exc:
                last = exc
        raise CaseWriteFailed(attempts=2) from last

    def _open_in(
        self, tx: UnitOfWork, req: HandoffRequest, now: dt.datetime, window_start: dt.datetime | None
    ) -> HandoffResult:
        presence = self._demo.presence(tx)
        promise = promise_for(req.reason, presence, now, window_start)
        result = self._cases.open_case(tx, req, promise, now)
        guidance = self._staff_guidance.get(req.reason)
        if result.created and guidance:
            anchor = tx.core.messages.handoff_anchor(req.thread_id)
            for g in guidance:
                tx.core.lookup_log.append(
                    LookupEntry(
                        tool="staff_guidance",
                        record_ids=(),
                        passage_ids=(g.passage_id,),
                        result_seen=g.text_sha256,
                        message_id=anchor,
                        turn_id=req.turn_id,
                    )
                )
        return result


def _item(text: str, kind: str, *sources: SourceRef) -> BriefItem:
    return BriefItem.model_validate({"text": text, "kind": kind, "sources": tuple(sources), "changed": False})


def _first_row(
    rows: Sequence[LookupRow], *, record: str | None = None, passage: str | None = None
) -> LookupRow | None:
    for r in rows:
        if record is not None and record in r.record_ids:
            return r
        if passage is not None and passage in [str(p) for p in r.passage_ids]:
            return r
    return None


def _on(row: LookupRow) -> SourceRef:
    return SourceRef(kind="lookup_log", ref=str(row.id))


class BriefAssembler:
    """Builds the eight-heading brief from state (pure: no I/O, no clock) and attaches the model's extraction."""

    def __init__(self, staff_guidance: Mapping[PassageId, StaffGuidance] | None = None) -> None:
        self._guidance = dict(staff_guidance or {})

    def assemble(
        self,
        case: CaseSummary,
        state: ConversationState,
        lookups: Sequence[LookupRow],
        *,
        invoices: Sequence[InvoiceView] = (),
    ) -> Brief:
        """Headings 1, 3, 5, 6, 8 and the guidance items of 7 from stored facts; 2 and 4 start empty.

        `invoices` are the thread's invoices read on earlier turns; this turn's own views win on the same id.
        """
        rows = [r for r in lookups if r.result_seen != "failed" and not r.result_seen.startswith("refused:")]
        items: dict[int, list[BriefItem]] = {n: [] for n in range(1, 9)}
        items[1] = self._why(case, state)
        items[3] = self._know(state, rows, invoices)
        items[5] = self._ai_did(state, rows)
        items[6] = self._told(case)
        items[7] = self._guidance_items(rows)
        items[8] = self._who(case, state)
        headings = tuple(
            BriefHeading(
                number=i + 1,
                key=BRIEF_KEYS[i],  # type: ignore[arg-type]
                title=BRIEF_TITLES[i],
                origin=BRIEF_ORIGINS[i],  # type: ignore[arg-type]
                checked=i != 3,
                items=tuple(items[i + 1]),
                trimmed=False,
                trim_note=None,
                not_generated=False,
            )
            for i in range(8)
        )
        return Brief(
            case_ref=case.case_ref,
            thread_id=state.thread_id,
            assembled_at=state.turn_input.received_at,
            status="being_written",
            headings=headings,
        )

    def attach_extraction(
        self,
        brief: Brief,
        extraction: BriefExtraction | None,
        check: CheckResult | None,
        *,
        customer_messages: Mapping[int, str] | None = None,
    ) -> Brief:
        """Adds the model's quotes (headings 2, 4) and open decision (7); never touches heading 6."""
        by_number = {h.number: h for h in brief.headings}
        if extraction is None:
            new = {
                n: h.model_copy(update={"not_generated": True}) if n in (2, 4, 7) else h
                for n, h in by_number.items()
            }
            return self._rebuild(brief, new, "failed")

        def kept(quotes: Sequence[Quote]) -> tuple[list[BriefItem], bool]:
            out: list[BriefItem] = []
            dropped = False
            for q in quotes:
                if customer_messages is None or (
                    q.message_id in customer_messages and q.text in customer_messages[q.message_id]
                ):
                    out.append(_item(q.text, "claim", SourceRef(kind="message", ref=str(q.message_id))))
                else:
                    dropped = True
            return out, dropped

        needs, needs_dropped = kept(extraction.needs)
        claims, claims_dropped = kept(extraction.claims)
        h2 = by_number[2].model_copy(
            update={
                "items": tuple(needs),
                "trimmed": needs_dropped,
                "trim_note": TRIM_NOTE if needs_dropped else None,
            }
        )
        h4 = by_number[4].model_copy(
            update={
                "items": tuple(claims),
                "trimmed": claims_dropped,
                "trim_note": TRIM_NOTE if claims_dropped else None,
            }
        )
        h7 = by_number[7]
        decision = (check.text if check is not None else extraction.open_decision).strip()
        h7_items = list(h7.items)
        if decision:
            source = (
                SourceRef(kind="message", ref=needs[0].sources[0].ref)
                if needs
                else next((i.sources[0] for i in h7.items if i.sources[0].kind == "lookup_log"), None)
            )
            if source is not None:
                h7_items.append(_item(decision, "decision", source))
        trimmed = bool(check is not None and check.removals)
        h7 = h7.model_copy(
            update={"items": tuple(h7_items), "trimmed": trimmed, "trim_note": TRIM_NOTE if trimmed else None}
        )
        new = {**by_number, 2: h2, 4: h4, 7: h7}
        return self._rebuild(brief, new, "ready")

    @staticmethod
    def _rebuild(brief: Brief, headings: Mapping[int, BriefHeading], status: str) -> Brief:
        return Brief.model_validate(
            {
                "case_ref": brief.case_ref,
                "thread_id": brief.thread_id,
                "assembled_at": brief.assembled_at,
                "status": status,
                "headings": tuple(headings[n] for n in range(1, 9)),
            }
        )

    # ---- headings built from state

    @staticmethod
    def _why(case: CaseSummary, state: ConversationState) -> list[BriefItem]:
        safety = state.gate.rules.safety.value if state.gate and state.gate.rules.safety else None
        esc = state.escalation
        rule = esc.rule_id if esc is not None and esc.reason == case.reason else case.reason.value
        text = f"{reason_label(case.reason, safety)}. Priority {case.priority.value} ({PRIORITY_WORD[case.priority]})."
        return [_item(text, "fact", SourceRef(kind="rule", ref=rule))]

    @staticmethod
    def _know(
        state: ConversationState, rows: Sequence[LookupRow], earlier_invoices: Sequence[InvoiceView] = ()
    ) -> list[BriefItem]:
        out: list[BriefItem] = []
        seen: set[str] = set()
        views: list[InvoiceView] = []
        for result in state.specialist_results:
            if isinstance(result, AccountResult) and result.status == "read":
                views.extend(result.invoices)
        views.extend(earlier_invoices)
        for inv in views:
            if str(inv.invoice_id) in seen:
                continue
            seen.add(str(inv.invoice_id))
            row = _first_row(rows, record=str(inv.invoice_id))
            if row is None:
                continue
            text = (
                f"Invoice {inv.invoice_id}: total {format_usd(inv.total_cents)}, balance "
                f"{format_usd(inv.balance_cents)}, due {inv.due_on.isoformat()}."
            )
            if inv.lines:
                listed = "; ".join(f"{ln.description} {format_usd(ln.amount_cents)}" for ln in inv.lines)
                text += f" Lines: {listed}."
            out.append(_item(text, "fact", _on(row)))
        for result in state.specialist_results:
            if isinstance(result, AccountResult) and result.status == "read":
                for note in result.staff_notes:
                    row = _first_row(rows, record=str(note.record_id))
                    if row is not None:
                        out.append(_item(note.text, "fact", _on(row)))
            elif isinstance(result, KnowledgeResult) and result.status == "answered":
                for point in result.points:
                    row = _first_row(rows, passage=str(point.passage_id))
                    if row is not None:
                        out.append(_item(point.text, "fact", _on(row)))
        return out

    @staticmethod
    def _ai_did(state: ConversationState, rows: Sequence[LookupRow]) -> list[BriefItem]:
        out: list[BriefItem] = []
        settled = state.settled
        for a in settled.actions if settled is not None else ():
            appointment = a.records.get("appointment", "")
            if a.kind is ActionKind.VERIFIED:
                text = "Confirmed the customer with a code (demo simulation)."
            elif a.kind is ActionKind.BOOKED and appointment:
                text = f"Booked appointment {appointment}."
            elif a.kind is ActionKind.MOVED and appointment:
                text = f"Moved appointment {appointment}."
            elif a.kind is ActionKind.CANCELLED and appointment:
                text = f"Cancelled appointment {appointment}."
            elif a.kind is ActionKind.CHANGE_REQUEST_SENT and appointment:
                text = f"Recorded a change request for appointment {appointment}; the appointment itself was not changed."
            else:
                continue
            out.append(
                _item(text, "ai_action", SourceRef(kind="action", ref=f"{a.kind.value}:{a.key.record_id}"))
            )
        for row in rows:
            if row.tool != "staff_guidance":
                out.append(_item(f"Looked up {row_title(row)}.", "ai_action", _on(row)))
        return out

    @staticmethod
    def _told(case: CaseSummary) -> list[BriefItem]:
        if case.promise.text == "":
            return []
        source = SourceRef(kind="policy_row", ref=case.promise.policy_row)
        lines = [fill_promise_text(case.promise, str(case.case_ref)), *case.promise.extra_lines]
        return [_item(line, "told_customer", source) for line in lines]

    def _guidance_items(self, rows: Sequence[LookupRow]) -> list[BriefItem]:
        out: list[BriefItem] = []
        for row in rows:
            if row.tool != "staff_guidance":
                continue
            pid = row.passage_ids[0] if row.passage_ids else None
            g = self._guidance.get(pid) if pid is not None else None
            text = (
                g.text
                if g is not None and g.text_sha256 == row.result_seen
                else f"Staff guidance: {pid or 'unknown'}"
            )
            out.append(_item(text, "fact", _on(row)))
        return out

    @staticmethod
    def _who(case: CaseSummary, state: ConversationState) -> list[BriefItem]:
        message = SourceRef(kind="message", ref=str(state.turn_input.message_id))
        status, line, _ = identity_view(state.identity, case_customer=False)
        if case.reason is HandoffReason.SAFETY and status != "verified":
            return [_item("No account match needed for safety.", "fact", message)]
        verified = next(
            (a for a in (state.settled.actions if state.settled else ()) if a.kind is ActionKind.VERIFIED),
            None,
        )
        source = SourceRef(kind="action", ref=f"verified:{verified.key.record_id}") if verified else message
        out = [_item(line, "fact", source)]
        if status == "verified" and state.identity.customer_id is not None:
            out.append(_item(f"Record {state.identity.customer_id}.", "fact", source))
        return out
