"""The compose node and ReplyComposer: what the customer sees at the end of a turn (graph-core section 13).

Stateless, no I/O, no model call, no clock read. Every sentence comes from `policy/texts.py`; the labels that are not
sentences are copied from the OpenAPI CON-2 examples (plan PD-9). Compose never reads the staff-only notes, the turn's
`intake` or the stored message text (AC-13): the main text arrives only through `state.checked.text`.
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Literal, cast

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.nodes.compose_cards import (
    ASSISTANT,
    DOW3,
    MON3,
    BlockIds,
    BlockKw,
    ErrCode,
    account_cards,
    appointment_block,
    error_block,
    make_notice,
    notice_block,
    offer_block,
    scheduling_cards,
    window_label,
)
from meridian.agent.nodes.compose_promise import promise_wire
from meridian.domain import blocks as b
from meridian.domain import identity as idn
from meridian.domain import turn as tn
from meridian.domain.actions import ActionKind, CompletedAction, OpenCase, Settled
from meridian.domain.common import Halt, HaltReason, TurnId
from meridian.domain.handoff import CaseSummary, HandoffResult, Priority
from meridian.domain.records import Passage
from meridian.domain.staff import STAFF_PERSONAS, StaffRole
from meridian.domain.state import ComposeUpdate, Controller, ConversationState
from meridian.gates.gate import burning_card_id
from meridian.policy.texts import TEXTS, TextId, render

__all__ = ["ReplyComposer", "compose", "turn_trace"]

_SAFETY_CALL_KEY = b.CallKey(label="Call 911 (from outside)", number="911")
_BURNING_OPTIONS = (
    b.Option(option="yes", label="Yes", disabled=False, reason=None),
    b.Option(option="no", label="No", disabled=False, reason=None),
    b.Option(option="not_sure", label="Not sure", disabled=False, reason=None),
)
_QUICK_CHECK_OPTIONS = (
    b.Option(option="skip_and_book", label="Skip and book", disabled=False, reason=None),
    b.Option(option="show_checks", label="Show the checks", disabled=False, reason=None),
)
# PD-10: the value graph-core, AEA-12 and AEA-36 match on is "new_code" (the OpenAPI example's "resend" would be stale).
_NEW_CODE_OPTION = b.Option(option="new_code", label="Send a new code", disabled=False, reason=None)
_LOCATE_FIELD_SETS: tuple[tuple[Literal["name", "phone", "customer_id", "invoice_number"], ...], ...] = (
    ("name", "phone"),
    ("customer_id",),
    ("invoice_number",),
)
_TIMELINE_TAIL = ("Technician arrives in the window", "Repair approved or declined at the visit")
_GENERAL_FOLLOWUP = b.FollowUpOptions(  # PD-11
    legend=TEXTS[TextId.FOLLOWUP_LEGEND],
    channels=(
        b.FollowUpChannelOption(channel="email", label="Email", on_record=False),
        b.FollowUpChannelOption(channel="phone", label="Phone call", on_record=False),
    ),
    windows=(
        b.FollowUpWindowOption(window="morning", label="Mornings"),
        b.FollowUpWindowOption(window="afternoon", label="Afternoons"),
        b.FollowUpWindowOption(window="any", label="Any time"),
    ),
    general_only=True,
)
_VARIANT: Mapping[str, Literal["nobody_online", "refund", "staffed"]] = MappingProxyType(
    {
        "R26.unstaffed": "nobody_online",
        "R26.refund": "refund",
        "R26.staffed": "staffed",
        "R26.safety_none": "nobody_online",
        "OD4.danger_review": "nobody_online",
    }
)
_BRAKES = frozenset(
    {
        HaltReason.BRAKE_TASKS,
        HaltReason.BRAKE_TOOL_ROUNDS,
        HaltReason.BRAKE_SONNET_CALLS,
        HaltReason.BRAKE_IDENTICAL_CALL,
    }
)
_DEGRADE_BY_RULE: Mapping[str, tn.DegradeReason] = MappingProxyType(
    {"AI.planner_failed": "model_error", "AI.models_disabled": "spend_cap", "AI.halt": "brake"}
)
_VISIT_INTENTS = frozenset({tn.TaskIntent.CONFIRM, tn.TaskIntent.READ_APPOINTMENTS})
IdentityViewStatus = Literal["not_checked", "code_sent", "verified", "not_verified", "locked"]


def _day(d: dt.date) -> str:
    return f"{DOW3[d.weekday()]} {MON3[d.month - 1]} {d.day}"


def _date_in(*sources: Mapping[str, str] | None) -> dt.date | None:
    text = next((src["date"] for src in sources if src and src.get("date")), "")
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def _chip(p: Passage) -> b.SourceChip:
    excerpt = p.text if len(p.text) <= 300 else p.text[:299] + "…"
    return b.SourceChip(
        passage_id=str(p.passage_id),
        file=p.file,
        section=p.section,
        version_date=p.version_date,
        excerpt=excerpt,
        audience="customer",
        version_label=p.version_label,
    )


def _chips(facts: tn.TurnFacts | None) -> tuple[b.SourceChip, ...]:
    if facts is None:
        return ()
    by_id = {p.passage_id: p for p in facts.passages}
    return tuple(_chip(by_id[i]) for i in dict.fromkeys(pt.passage_id for pt in facts.points) if i in by_id)


def _write_summary(a: CompletedAction, settled: Settled) -> str:
    ref = a.records.get("case") or a.key.record_id
    if a.kind in (ActionKind.BOOKED, ActionKind.MOVED):
        word, fallback = (
            ("Booked", "Booked a visit") if a.kind is ActionKind.BOOKED else ("Moved to", "Moved a visit")
        )
        date, window = _date_in(a.after), (a.after or {}).get("window")
        return fallback if date is None or not window else f"{word} {_day(date)}, {window_label(window)}"
    if a.kind is ActionKind.CANCELLED:
        date = _date_in(a.before, a.after)
        return f"Cancelled {_day(date)} visit" if date else "Cancelled a visit"
    if a.kind is ActionKind.CHANGE_REQUEST_SENT:
        return f"Change request {ref} sent to staff"
    if a.kind is ActionKind.CASE_OPENED:
        oc = settled.open_case
        if oc is not None and oc.case_ref == ref and oc.priority in (Priority.P0, Priority.P1):
            return f"{oc.priority.value} case {ref} opened"
        return f"Case {ref} opened"
    if a.kind is ActionKind.FOLLOWUP_SAVED:
        return "Follow-up preference saved"
    return "Verified for this chat"


def _identity_status(
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"],
) -> IdentityViewStatus:
    return "not_checked" if status == "located" else status


def _open_case(c: CaseSummary) -> OpenCase:
    return OpenCase(
        case_ref=c.case_ref,
        reason=c.reason,
        priority=c.priority,
        state=c.state,
        promise=c.promise,
        followup=c.followup,
        live_queued=c.promise.live_queued,
    )


def _effective_settled(state: ConversationState, ctx: tn.TurnContext) -> Settled:
    """The settled record plus the case opened this turn (facts does not re-read on the safety path)."""
    base = state.settled or Settled(actions=(), open_case=None, read_at=ctx.now)
    handoff = state.handoff
    if handoff is not None and handoff.action.key not in {a.key for a in base.actions}:
        return Settled(
            actions=(*base.actions, handoff.action), open_case=_open_case(handoff.case), read_at=base.read_at
        )
    return base


def _emergency_number() -> tuple[str, str]:
    m = re.search(r"(\(\d{3}\) \d{3}-\d{4}) (\(demo number\))", TEXTS[TextId.EMERGENCY_NUMBER_LINE])
    if m is None:
        raise RuntimeError("emergency number line changed shape")
    return m.group(1), m.group(2)


def _reply(
    blocks: Sequence[b.ReplyBlock],
    view: b.SettledView,
    writes: tuple[CompletedAction, ...],
    path: tn.TurnPath,
    outcome: tn.TurnOutcome,
    notice: b.Notice | None = None,
    degrade: tn.DegradeReason | None = None,
) -> tn.ComposedReply:
    return tn.ComposedReply(
        blocks=tuple(blocks),
        settled_view=view,
        writes=writes,
        notice=notice,
        path=path,
        outcome=outcome,
        degrade_reason=degrade,
    )


class ReplyComposer:
    """One concrete class, stateless: state in, tn.ComposedReply out (graph-core section 13)."""

    # ----- public -----
    def compose(self, state: ConversationState, ctx: tn.TurnContext) -> tn.ComposedReply:
        ids = BlockIds(ctx)
        settled = _effective_settled(state, ctx)
        writes = tuple(a for a in settled.actions if a.key.turn_id == ctx.ids.turn_id)
        view = self.settled_view(settled, state.identity, state.controller)
        gate = state.gate

        lead = self._safety_lead(state, ids)  # A: safety comes first, whatever the controller or a halt says
        if lead is not None:
            return _reply(lead[0], view, writes, lead[1], "safety_reply")
        if gate is not None and gate.kind is tn.GateKind.AI_PAUSED:  # B
            name = state.controller.representative_name or STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name
            paused = notice_block(ids, "AI_PAUSED", render(TextId.AI_PAUSED_NOTICE, rep_name=name))
            return _reply(
                [paused], view, writes, "paused", "to_staff", make_notice("AI_PAUSED", (), to_rep=True)
            )
        if state.halt is not None:  # C
            halt_blocks, halt_notice, degrade = self._halt_parts(state.halt, state.handoff, ctx, ids)
            return _reply(halt_blocks, view, writes, "degraded", "degraded_handoff", halt_notice, degrade)
        return self._answer(state, ids, settled, writes, view)  # D

    def halt_reply(self, halt: Halt, settled: Settled, ctx: tn.TurnContext) -> tn.ComposedReply:
        """Works with no graph state (AC-12): the settled record is all it has (PD-14)."""
        blocks, notice, degrade = self._halt_parts(halt, None, ctx, BlockIds(ctx))
        status: IdentityViewStatus = "verified" if settled.has(ActionKind.VERIFIED) else "not_checked"
        view = self._view(settled, status=status, hint=None, controller=Controller(kind="ai"))
        writes = tuple(a for a in settled.actions if a.key.turn_id == ctx.ids.turn_id)
        return _reply(blocks, view, writes, "degraded", "degraded_handoff", notice, degrade)

    def handoff_block(self, result: HandoffResult) -> b.HandoffBlock | b.LiveQueuedBlock:
        """Promise text, reference and due label come only from the HandoffResult (R-26)."""
        p, case = result.case.promise, result.case
        base = BlockKw(
            block_id=f"blk-{result.action.key.turn_id}-handoff", speaker=ASSISTANT, at=result.action.at
        )
        if p.live_queued:
            return b.LiveQueuedBlock(**base, reference=case.case_ref, promise_text=p.text)
        wire = promise_wire(p, str(case.case_ref))
        return b.HandoffBlock(
            **base,
            card_id=f"handoff-{case.case_ref}",
            options=(),
            answered=None,
            reference=case.case_ref,
            variant=_VARIANT.get(p.policy_row, "nobody_online"),
            promise_text=wire.promise_text,
            due_at=p.due_at,
            due_label=wire.due_label,
            extra_lines=wire.extra_lines,
            followup_chooser=_GENERAL_FOLLOWUP,
        )

    def settled_view(
        self, settled: Settled, identity: idn.IdentityState, controller: Controller
    ) -> b.SettledView:
        status = _identity_status(identity.status)
        hint = identity.masked_hint if status in ("code_sent", "verified") else None
        return self._view(settled, status=status, hint=hint, controller=controller)

    # ----- private -----
    def _view(
        self, settled: Settled, *, status: IdentityViewStatus, hint: str | None, controller: Controller
    ) -> b.SettledView:
        v, oc = settled.current_visit(), settled.open_case
        visit = None
        if v is not None:
            visit = b.SettledVisit.model_validate({**v.model_dump(), "window_label": window_label(v.window)})
        request = None
        if oc is not None:
            wire = promise_wire(oc.promise, str(oc.case_ref))
            request = b.SettledRequest(
                reference=oc.case_ref,
                promise_text=wire.promise_text,
                due_at=oc.promise.due_at,
                due_label=wire.due_label,
                extra_lines=wire.extra_lines,
                live_queued=oc.live_queued,
                followup=oc.followup,
            )
        actions = tuple(
            b.Write.model_validate(
                {
                    "kind": a.kind.value,
                    "summary": _write_summary(a, settled),
                    "turn_id": str(a.key.turn_id),
                    "at": a.at,
                }
            )
            for a in settled.actions
        )
        name = controller.representative_name if controller.kind == "human" else None
        return b.SettledView(
            visit=visit,
            request=request,
            identity=b.SettledIdentity(status=status, hint=hint),
            replying=b.SettledReplying(kind=controller.kind, display_name=name),
            actions=actions,
        )

    def _halt_parts(
        self, halt: Halt, handoff: HandoffResult | None, ctx: tn.TurnContext, ids: BlockIds
    ) -> tuple[list[b.ReplyBlock], b.Notice | None, tn.DegradeReason]:
        reason = halt.reason
        if reason is HaltReason.DEADLINE:
            block = notice_block(ids, "TURN_TIMEOUT", TEXTS[TextId.TURN_TIMEOUT])
            notice = make_notice("TURN_TIMEOUT", ("try_again", "talk_to_person"), str(ctx.ids.turn_id))
            return [block], notice, "timeout"
        if reason in (HaltReason.SPEND_CAP, HaltReason.PROVIDER_SPEND_CAP):
            cap = notice_block(ids, "SPEND_CAP_REACHED", TEXTS[TextId.SPEND_CAP_REACHED])
            notice = make_notice("SPEND_CAP_REACHED", ("talk_to_person",))
            return [cap], notice, "spend_cap"
        if reason in _BRAKES and handoff is not None:
            return [self.handoff_block(handoff)], None, "brake"
        return [offer_block(ids)], None, "brake"

    def _safety_lead(
        self, state: ConversationState, ids: BlockIds
    ) -> tuple[list[b.ReplyBlock], tn.TurnPath] | None:
        """Step A: the fixed safety card for this gate or classifier result, or None."""
        gate, danger, handoff = state.gate, state.danger, state.handoff
        if gate is None:
            return None
        ref = None if handoff is None else str(handoff.case.case_ref)
        label = danger.label if danger is not None and danger.raised else None
        answer = gate.burning_answer if gate.kind is tn.GateKind.BURNING_ANSWER else None
        if gate.kind is tn.GateKind.SAFETY or answer == "yes":
            steps = (TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH])
            return [
                b.SafetyBlock(
                    **ids.kw(),
                    signal_word="DANGER",
                    steps=steps,
                    call_key=_SAFETY_CALL_KEY,
                    contact_line=TEXTS[TextId.SAFETY_CONTACT_LINE],
                    case_reference=ref,
                )
            ], "safety"
        if answer == "unsure" or (gate.kind is tn.GateKind.FREE_TEXT and label == "burning_unclear"):
            return [
                b.ConditionalSafetyBlock(
                    **ids.kw(),
                    text=TEXTS[TextId.WARNING_TEXT],
                    emergency_line=TEXTS[TextId.EMERGENCY_NUMBER_LINE],
                    case_reference=ref,
                )
            ], "burning_unclear"
        if gate.kind is tn.GateKind.BURNING_ASK:
            return [
                b.BurningCheckBlock(
                    **ids.kw(),
                    card_id=burning_card_id(TurnId(ids.turn_id)),
                    options=_BURNING_OPTIONS,
                    answered=None,
                    question=TEXTS[TextId.BURNING_QUESTION],
                )
            ], "burning_questions"
        if gate.kind is tn.GateKind.DANGER_RULE or label == "danger":
            number, note = _emergency_number()
            promise = None if handoff is None else handoff.case.promise
            separate = (
                promise.text if promise is not None and promise.policy_row == "OD4.danger_review" else None
            )
            return [
                b.EmergencyLineBlock(
                    **ids.kw(),
                    lead_text=TEXTS[TextId.EMERGENCY_LINE_LEAD],
                    number=number,
                    number_note=note,
                    separate_line=separate,
                    case_reference=ref or "",
                )
            ], "danger"
        return None

    def _answer(
        self,
        state: ConversationState,
        ids: BlockIds,
        settled: Settled,
        writes: tuple[CompletedAction, ...],
        view: b.SettledView,
    ) -> tn.ComposedReply:
        """Step D: assemble the blocks of an ordinary turn, then name its path and outcome."""
        step, facts, handoff, plan = state.identity_step, state.facts, state.handoff, state.plan
        blocks: list[b.ReplyBlock] = []
        # 1-2. identity error, verified line
        if isinstance(step, idn.NotVerified | idn.CodeLocked | idn.CodeCapReached | idn.CodeExpired):
            text = TEXTS[TextId.CODE_EXPIRED if step.kind == "code_expired" else TextId.NOT_VERIFIED]
            blocks.append(error_block(ids, cast(ErrCode, step.kind.upper()), text))
        elif isinstance(step, idn.CodeWrong):
            blocks.append(
                error_block(
                    ids, "CODE_WRONG", render(TextId.CODE_WRONG, n=str(step.tries_left)), step.tries_left
                )
            )
        elif isinstance(step, idn.Verified):
            blocks.append(b.TextBlock(**ids.kw(), text=TEXTS[TextId.VERIFIED], sources=()))
        # 3. main text, or the person offer when the checked reply is a fallback
        checked = state.checked
        fallback = checked is None or checked.fallback_used
        if checked is not None and not fallback and checked.text.strip():
            blocks.append(b.TextBlock(**ids.kw(), text=checked.text, sources=_chips(facts)))
        if fallback:
            blocks.append(offer_block(ids))
        # 4. no source
        if facts is not None and facts.no_source_tasks:
            blocks.append(b.NoInfoBlock(**ids.kw(), text=TEXTS[TextId.NO_INFORMATION], person_key=True))
        blocks.extend(account_cards(ids, state.specialist_results))  # 4a. account cards (AEA-21b)
        # 5. code prompt
        prompt = self._code_prompt(state, ids)
        if prompt is not None:
            blocks.append(prompt)
        # 6. locate prompt
        needs_identity = plan is not None and plan.mode == "act" and any(t.needs_identity for t in plan.tasks)
        if step is None and state.identity.status == "not_checked" and needs_identity:
            blocks.append(
                b.LocatePromptBlock(
                    **ids.kw(),
                    card_id=f"locate-{ids.turn_id}",
                    options=(),
                    answered=None,
                    reason_text=TEXTS[TextId.IDENTITY_NEEDED],
                    field_sets=_LOCATE_FIELD_SETS,
                )
            )
        # 7. write cards
        blocks.extend(card for card in (self._write_card(a, ids) for a in writes) if card is not None)
        # 7a. the booked visit for a visit question, unless a write card already shows it (AEA-21b)
        wrote = any(isinstance(x, b.ConfirmationBlock | b.CancelledBlock) for x in blocks)
        if (
            plan is not None
            and any(t.intent in _VISIT_INTENTS for t in plan.tasks)
            and not wrote
            and view.visit
        ):
            blocks.append(appointment_block(ids, view.visit))
        # 8. quick checks
        quick = self._quick_checks(state, ids)
        if quick is not None:
            blocks.append(quick)
        # 9. scheduling results: errors, booking cap, slot card, SLOT_TAKEN, no fit, where prompt (AEA-21b)
        scheduled, notice = scheduling_cards(state, settled, ids)
        blocks.extend(scheduled)
        # 10. change request replaces the handoff card (PD-12)
        change_shown = facts is not None and facts.change_request is not None and handoff is not None
        if change_shown:
            blocks.append(self._change_request_block(state, writes, ids))
        # 11. offer
        escalation = state.escalation
        if (
            escalation is not None
            and escalation.outcome == "offer"
            and not any(isinstance(x, b.FailureOfferBlock) for x in blocks)
        ):
            blocks.append(offer_block(ids))
        # 12. the handoff card is the last block (R-26)
        if handoff is not None and not change_shown:
            blocks.append(self.handoff_block(handoff))
        path, outcome, degrade = self._path(state, fallback)
        return _reply(blocks, view, writes, path, outcome, notice, degrade)

    def _code_prompt(self, state: ConversationState, ids: BlockIds) -> b.CodePromptBlock | None:
        step, ident = state.identity_step, state.identity
        if isinstance(step, idn.CodeSent):
            shown: tuple[Literal["sent", "wrong", "expired"], str, int | None, dt.datetime | None] = (
                "sent",
                step.masked_hint,
                ident.tries_left,
                step.expires_at,
            )
            resend, left = False, step.sends_left
        elif isinstance(step, idn.CodeWrong):
            shown = ("wrong", ident.masked_hint or "", step.tries_left, ident.code_expires_at)
            resend, left = False, None
        elif isinstance(step, idn.CodeExpired):
            shown = ("expired", ident.masked_hint or "", None, ident.code_expires_at)
            resend, left = step.resend_offered, step.sends_left
        else:
            return None
        return b.CodePromptBlock(
            **ids.kw(),
            card_id=f"code-{ids.turn_id}",
            options=(_NEW_CODE_OPTION,) if resend else (),
            answered=None,
            state=shown[0],
            hint=shown[1],
            tries_left=shown[2],
            expires_at=shown[3],
            resend_offered=resend,
            resends_left=left,
            inbox_link="/demo/inbox",
        )

    def _write_card(self, a: CompletedAction, ids: BlockIds) -> b.ConfirmationBlock | b.CancelledBlock | None:
        """PA-3: a card for a booking, move or cancel; an action missing a needed key gets no card."""
        appointment = a.records.get("appointment")
        after = a.after or {}
        if appointment is None:
            return None
        if a.kind in (ActionKind.BOOKED, ActionKind.MOVED):
            date = _date_in(a.after)
            if date is None or not all(k in after for k in ("window", "technician", "fee_line")):
                return None
            word = "Booked" if a.kind is ActionKind.BOOKED else "Moved"
            return b.ConfirmationBlock(
                **ids.kw(),
                appointment_id=int(appointment),
                date=date,
                window_label=window_label(after["window"]),
                technician=after["technician"],
                fee_line=after["fee_line"],
                timeline=(word, *_TIMELINE_TAIL),
                free_change_note=TEXTS[TextId.FREE_CHANGE_NOTE],
            )
        if a.kind is ActionKind.CANCELLED:
            date = _date_in(a.before, a.after)
            if date is None:
                return None
            return b.CancelledBlock(
                **ids.kw(),
                appointment_id=int(appointment),
                date=date,
                fee_line=TEXTS[TextId.CANCELLED_NO_FEE],
            )
        return None

    def _quick_checks(self, state: ConversationState, ids: BlockIds) -> b.QuickChecksBlock | None:
        facts = state.facts
        if facts is None or not facts.quick_checks:
            return None
        booking = (t for t in state.open_tasks if t.status != "done" and t.specialist == "scheduling")
        task = next((t for t in booking if t.intent is tn.TaskIntent.BOOK_NEW), None)
        if task is None:
            return None
        by_id = {p.passage_id: p for p in facts.passages}
        checks = tuple(
            b.QuickCheck(text=by_id[i].text, source=_chip(by_id[i])) for i in facts.quick_checks if i in by_id
        )
        return b.QuickChecksBlock(
            **ids.kw(),
            card_id=ids.task_card(task.task_id),
            options=_QUICK_CHECK_OPTIONS,
            answered=None,
            offer_text=TEXTS[TextId.QUICK_CHECKS_OFFER],
            checks=checks,
        )

    def _change_request_block(
        self, state: ConversationState, writes: Sequence[CompletedAction], ids: BlockIds
    ) -> b.ChangeRequestBlock:
        facts, handoff = state.facts, state.handoff
        if facts is None or facts.change_request is None or handoff is None:
            raise ValueError("change request block needs a draft and a handoff")
        draft, c = facts.change_request, handoff.case
        fee_line = next(
            (
                (w.after or {}).get("fee_line", "")
                for w in writes
                if w.kind is ActionKind.CHANGE_REQUEST_SENT
                and w.records.get("appointment") == str(draft.appointment_id)
            ),
            "",
        )
        shown = tuple(
            b.ShownWindow(slot_id=str(s.slot_id), window_label=window_label(s.window), date=s.date)
            for s in state.shown_slots
            if s.slot_id in draft.windows_shown
        )
        wire = promise_wire(c.promise, str(c.case_ref))
        return b.ChangeRequestBlock(
            **ids.kw(),
            change=draft.change,
            fee_line=fee_line,
            original_stays_line=TEXTS[TextId.FEE_ORIGINAL_STAYS],
            wanted_text=draft.wanted_text,
            windows_shown=shown,
            reference=c.case_ref,
            promise_text=wire.promise_text,
            due_at=c.promise.due_at,
            due_label=wire.due_label,
            extra_lines=wire.extra_lines,
            cant_guarantee_line=None,
            phone_support_line=None,
        )

    def _path(
        self, state: ConversationState, fallback: bool
    ) -> tuple[tn.TurnPath, tn.TurnOutcome, tn.DegradeReason | None]:
        esc, gate = state.escalation, state.gate
        if fallback:
            return "degraded", "degraded_handoff", "model_error"
        if esc is not None and esc.degraded:
            return "degraded", "degraded_handoff", self._degrade_for(esc.rule_id, state)
        if gate is not None and gate.kind is tn.GateKind.PERSON:
            return "person", "handed_off", None
        if state.handoff is not None:
            return "handoff", "handed_off", None
        acted = any(r.status != "failed" for r in state.specialist_results)
        if gate is not None and gate.kind in (tn.GateKind.CODE_ENTRY, tn.GateKind.LOCATE):
            return "code", ("acted" if acted else "answered"), None
        if acted:
            return "act", "acted", None
        return "talk", "answered", None

    def _degrade_for(self, rule_id: str, state: ConversationState) -> tn.DegradeReason:
        if rule_id == "AI.specialist_failed":
            failed = [r for r in state.specialist_results if r.status == "failed"]
            return "tool_error" if failed and all(r.failure is None for r in failed) else "model_error"
        return _DEGRADE_BY_RULE.get(rule_id, "model_error")


def turn_trace(state: ConversationState, reply: tn.ComposedReply) -> tn.TurnTrace:
    """Codes only (DO-6): the trace row of one turn."""
    danger, p = state.danger, state.plan
    gate_result: tn.GateResult = "clear"
    if danger is not None and danger.raised:
        gate_result = "danger" if danger.label == "danger" else "burning_unclear"
    elif state.gate is not None:
        gate_result = state.gate.gate_result()
    planner = None
    if state.planner is not None:
        planner = tn.PlannerTrace(
            model=state.planner.model,
            fallback_used=state.planner.fallback_used,
            failure=state.planner.failure.kind if state.planner.failure else None,
            plan_mode=p.mode if p else None,
            plan_source=p.source if p else None,
            intents=tuple(t.intent for t in p.tasks) if p else (),
            handoff_request=p.handoff_request if p else None,
            topic=p.topic if p else None,
            planner_failed=p.planner_failed if p else False,
        )
    return tn.TurnTrace(
        gate_result=gate_result,
        path=reply.path,
        outcome=reply.outcome,
        degrade_reason=reply.degrade_reason,
        planner=planner,
        danger_raised=bool(danger and danger.raised),
        specialists_run=tuple(r.kind for r in state.specialist_results),
    )


def compose(
    state: ConversationState, runtime: Runtime[tn.TurnContext], *, deps: GraphDeps, composer: ReplyComposer
) -> ComposeUpdate:
    return {"reply": composer.compose(state, runtime.context)}
