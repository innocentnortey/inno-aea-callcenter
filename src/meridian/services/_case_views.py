"""Case view builders (A6): turn stored rows into the `domain.views` types the staff console reads.

Private to `cases.py`. Every builder reads through the unit of work it is given and writes nothing. Every
customer-derived string passes through `mask` before it reaches a view (no contact value in any view).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from typing import Final

from pydantic import JsonValue

from meridian.adapters.sqlite.rows import ActivityRow, CaseRow, ConversationRow
from meridian.domain.blocks import Speaker
from meridian.domain.common import CustomerId, InvoiceId
from meridian.domain.handoff import BRIEF_KEYS, BRIEF_TITLES, Brief
from meridian.domain.staff import CUSTOMER_SPEAKER_NAME, STAFF_PERSONAS, StaffRole
from meridian.domain.tools import LookupRow
from meridian.domain.views import (
    Activity,
    BriefHeadingView,
    BriefItemView,
    BriefView,
    CaseSource,
    CaseSummaryView,
    ChatLineView,
    PriorityView,
    PromiseFollowUp,
    PromiseHistoryItem,
    PromiseRecord,
    QueueRow,
)
from meridian.policy.texts import TEXTS, TextId
from meridian.ports.runtime import UnitOfWork
from meridian.services._case_rules import (
    PRIORITY_WORD,
    actions_for,
    age_label,
    case_due_label,
    due_state,
    fill_promise_text,
    follow_up_short,
    mask,
    parse_seen,
    reason_label,
    record_kind,
    row_title,
    staff_name,
)

RECORDED_NOT_SENT: Final = "Demo: recorded, not sent"
if TEXTS[TextId.RECORDED_NOT_SENT] != RECORDED_NOT_SENT:
    raise RuntimeError("recorded-not-sent text drifted from the signed Activity label")

_GUIDANCE_REF = "internal/agent_discretion_notes.md"


def live_state_of(tx: UnitOfWork, thread_id: object) -> tuple[str, ConversationRow | None]:
    """The thread's live-chat state and its conversation row (`not_live` when the thread has none)."""
    conv = tx.core.conversations.lookup(str(thread_id))
    if isinstance(conv, ConversationRow):
        return conv.live_state, conv
    return "not_live", None


def is_window_start(row: CaseRow) -> bool:
    """True when the case due is a fee-bearing change's window start."""
    window = row.change_request.get("window_start") if row.change_request else None
    return isinstance(window, str) and row.due_at == dt.datetime.fromisoformat(window)


def queue_row(tx: UnitOfWork, row: CaseRow, now: dt.datetime) -> QueueRow:
    """One queue row. No phone, email or address is ever read."""
    f = tx.cases.followups.get(row.case_ref)
    brief = tx.cases.briefs.get(row.case_ref)
    customer = tx.core.reads.customer(row.customer_id) if row.customer_id else None
    queued_at = row.queued_at if row.lifecycle == "live_queued" else None
    return QueueRow(
        reference=str(row.case_ref),
        priority=PriorityView(level=row.priority, word=PRIORITY_WORD[row.priority]),
        reason=reason_label(row.reason, row.safety_kind),
        customer_display_name=customer.name if customer else "No name given",
        owner=staff_name(row.owner_role.value) if row.owner_role else None,
        created_at=row.created_at,
        due_at=row.due_at,
        due_label=case_due_label(row.due_at, is_window_start=is_window_start(row)),
        due_state=due_state(row.due_at, now),
        wake_up_at=row.wake_up_at,
        lifecycle=row.lifecycle,
        follow_up_short=follow_up_short(f.channel if f else None, f.window if f else None),
        seed=row.seed,
        brief_status=brief.status if brief else "being_written",
        queued_at=queued_at,
        age_label=age_label(row.created_at, now, queued_at=queued_at),
    )


def summary_view(
    tx: UnitOfWork, row: CaseRow, actor_role: StaffRole, staffing: str, now: dt.datetime
) -> CaseSummaryView:
    """The wire summary of one case, with the actions this role may take now."""
    prow = tx.cases.promises.current(row.case_ref)
    if prow is None:
        raise LookupError("case promise missing")
    return CaseSummaryView(
        reference=str(row.case_ref),
        reason=reason_label(row.reason, row.safety_kind),
        priority=PriorityView(level=row.priority, word=PRIORITY_WORD[row.priority]),
        lifecycle=row.lifecycle,
        owner=staff_name(row.owner_role.value) if row.owner_role else None,
        created_at=row.created_at,
        due_at=row.due_at,
        due_label=case_due_label(row.due_at, is_window_start=is_window_start(row)),
        due_state=due_state(row.due_at, now),
        wake_up_at=row.wake_up_at,
        promise_status=prow.status,
        seed=row.seed,
        version=row.version,
        allowed_actions=actions_for(
            lifecycle=row.lifecycle,
            owner_role=row.owner_role,
            live_state=live_state_of(tx, row.thread_id)[0],
            staffing=staffing,
            actor_role=actor_role,
        ),
    )


def _mask_tree(value: JsonValue) -> JsonValue:
    if isinstance(value, str):
        return mask(value)
    if isinstance(value, dict):
        return {k: _mask_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_tree(v) for v in value]
    return value


def _masked(tree: dict[str, JsonValue]) -> dict[str, JsonValue]:
    out = _mask_tree(tree)
    if not isinstance(out, dict):
        raise TypeError("masked tree lost its shape")
    return out


def _guidance_text(row: LookupRow, brief: Brief | None) -> str | None:
    if brief is None:
        return None
    key = ("lookup_log", str(row.id))
    for heading in brief.headings:
        for item in heading.items:
            if any((s.kind, s.ref) == key for s in item.sources):
                return item.text
    return None


def _record_current(tx: UnitOfWork, rid: str, tool: str) -> tuple[str, dict[str, JsonValue] | None] | None:
    """(ref, current values) for a record id, or None when the id names no record we can read."""
    found = record_kind(rid)
    if found is None:
        return None
    kind, ident = found
    current: dict[str, JsonValue] | None
    if kind == "invoice":
        inv = tx.core.reads.invoice(InvoiceId(ident))
        current = (
            None
            if inv is None
            else {
                "amount_cents": inv.amount_cents,
                "balance_cents": inv.balance_cents,
                "issued_date": inv.issued_date.isoformat(),
                "due_date": inv.due_date.isoformat(),
                "appointment_id": inv.appointment_id,
            }
        )
        return f"invoices/{ident}", current
    if kind == "customer":
        c = tx.core.reads.customer(CustomerId(ident))
        if tool == "read_warranty":  # agent/tools/account.py
            current = (
                None
                if c is None
                else {
                    "system_install_date": c.system_install_date.isoformat()
                    if c.system_install_date
                    else None,
                    "system_brand": c.system_brand[:40] if c.system_brand else None,
                }
            )
            return f"customers/{ident}#warranty", current
        current = (
            None
            if c is None
            else {
                "membership_tier": c.membership_tier,
                "membership_renewal_date": (
                    c.membership_renewal_date.isoformat() if c.membership_renewal_date else None
                ),
            }
        )
        return f"customers/{ident}", current
    if kind == "appointment":
        a = tx.core.reads.appointment(int(ident))
        current = (
            None
            if a is None
            else {
                "slot_date": a.slot_date.isoformat(),
                "window": a.window,
                "status": a.status,
                "service_type": a.service_type,
                "technician": a.technician,
            }
        )
        return f"appointments/{ident}", current
    return f"slots/{ident}", None  # core.reads has no slot read


def case_sources(tx: UnitOfWork, lookups: Sequence[LookupRow], brief: Brief | None) -> tuple[CaseSource, ...]:
    """What the AI saw (the snapshot) beside what is true now. Failed and refused lookups are skipped."""
    out: list[CaseSource] = []
    for r in lookups:
        if r.result_seen == "failed" or r.result_seen.startswith("refused:"):
            continue
        source_id, log_id = f"src-{r.id}", f"ll-{r.id}"
        if r.tool == "staff_guidance":
            text = _guidance_text(r, brief)
            snapshot: dict[str, JsonValue] = (
                {"passage": mask(text)} if text is not None else {"passage_id": str(r.passage_ids[0])}
            )
            out.append(
                CaseSource(
                    source_id=source_id,
                    lookup_log_id=log_id,
                    audience="staff_only",
                    title="Agent discretion notes",
                    ref=_GUIDANCE_REF,
                    version_date=None,
                    snapshot=snapshot,
                    current=snapshot,
                    changed_since=False,
                    changed_note="No change since the snapshot",
                    current_unavailable=False,
                    version_label="undated",
                )
            )
            continue
        rid = r.record_ids[0] if r.record_ids else None
        seen = _masked(parse_seen(r.result_seen, record_id=rid))
        title = row_title(r)
        record = _record_current(tx, rid, r.tool) if rid is not None else None
        version_date: dt.date | None = None
        if record is not None:
            ref, current_values = record
            version_label = "live record"
        else:
            current_values = None
            ref = str(r.passage_ids[0]).split("#")[0] if r.passage_ids else r.tool
            label = seen.get("version_label")
            version_label = label if isinstance(label, str) else "undated"
            raw_date = seen.get("version_date")
            if isinstance(raw_date, str):
                try:
                    version_date = dt.date.fromisoformat(raw_date)
                except ValueError:
                    version_date = None
        current = None if current_values is None else _masked(current_values)
        if current is None:
            changed, note = False, None
        else:
            changed = any(k in current and current[k] != v for k, v in seen.items())
            note = "Changed since the AI saw it" if changed else "No change since the snapshot"
        out.append(
            CaseSource(
                source_id=source_id,
                lookup_log_id=log_id,
                audience="customer",
                title=title,
                ref=ref,
                version_date=version_date,
                snapshot=seen,
                current=current,
                changed_since=changed,
                changed_note=note,
                current_unavailable=current is None,
                version_label=version_label,
            )
        )
    return tuple(out)


def brief_view(brief: Brief | None, changed_ids: set[str]) -> BriefView:
    """The eight headings; every `source_ids` entry names a source of the same case detail."""
    if brief is None:
        return BriefView(
            status="being_written",
            headings=tuple(
                BriefHeadingView(
                    number=i + 1,
                    key=BRIEF_KEYS[i],  # type: ignore[arg-type]
                    title=BRIEF_TITLES[i],
                    checked=i != 3,
                    items=(),
                    trimmed=False,
                    trim_note=None,
                    not_generated=False,
                )
                for i in range(8)
            ),
        )

    def ids(item_sources: Sequence[object]) -> tuple[str, ...]:
        return tuple(f"src-{s.ref}" for s in item_sources if s.kind == "lookup_log")  # type: ignore[attr-defined]

    return BriefView(
        status=brief.status,
        headings=tuple(
            BriefHeadingView(
                number=h.number,
                key=h.key,
                title=h.title,
                checked=h.checked,
                items=tuple(
                    BriefItemView(
                        text=mask(i.text),
                        kind=i.kind,
                        source_ids=ids(i.sources),
                        changed=any(s in changed_ids for s in ids(i.sources)),
                    )
                    for i in h.items
                ),
                trimmed=h.trimmed,
                trim_note=h.trim_note,
                not_generated=h.not_generated,
            )
            for h in brief.headings
        ),
    )


def conversation_lines(tx: UnitOfWork, thread_id: object) -> tuple[ChatLineView, ...]:
    """The full chat. The customer always speaks as "Customer"; contact values are masked."""
    lines: list[ChatLineView] = []
    for m in tx.core.messages.all_for_thread(thread_id):  # type: ignore[arg-type]
        if m.role == "customer":
            speaker = Speaker(kind="customer", display_name=CUSTOMER_SPEAKER_NAME)
        elif m.role == "assistant":
            speaker = Speaker(kind="assistant", display_name="Meridian assistant")
        else:
            speaker = Speaker(
                kind="representative", display_name=STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name
            )
        lines.append(ChatLineView(message_id=str(m.id), speaker=speaker, at=m.at, text=mask(m.text)))
    return tuple(lines)


def promise_record(tx: UnitOfWork, row: CaseRow) -> PromiseRecord:
    """The current promise, its follow-up preference and the earlier promises."""
    ref = row.case_ref
    prow = tx.cases.promises.current(ref)
    if prow is None:
        raise LookupError("case promise missing")
    f = tx.cases.followups.get(ref)
    return PromiseRecord(
        text=fill_promise_text(prow.promise, str(ref)),
        due_at=prow.promise.due_at,
        due_label=prow.promise.due_label,
        policy_row=prow.promise.policy_row,
        status=prow.status,
        follow_up=None
        if f is None
        else PromiseFollowUp(
            channel=f.channel, destination_label=f.destination_label, on_record=f.on_record, window=f.window
        ),
        history=tuple(
            PromiseHistoryItem(
                at=h.status_at or h.created_at,
                text=fill_promise_text(h.promise, str(ref)),
                reason=h.status_reason or "changed",
            )
            for h in tx.cases.promises.history(ref)
            if h.id != prow.id
        ),
    )


def activity_view(a: ActivityRow) -> Activity:
    """One recorded contact activity; it is always labelled recorded, not sent."""
    return Activity(
        activity_id=f"act-{a.id}",
        kind=a.kind,
        outcome=a.outcome,
        note=mask(a.note) if a.note else None,
        at=a.at,
        by=STAFF_PERSONAS[a.actor_role].signature,
        label=RECORDED_NOT_SENT,
    )
