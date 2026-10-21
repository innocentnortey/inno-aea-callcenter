"""Account reads for the account specialist: read_invoices, read_membership, read_warranty (AEA-27; graph-tools 4).

account_tools(uow) binds them to a unit-of-work factory; nothing registers itself (GRT-1). Every read is bound to
``scope.customer_id`` by code: no args model has a customer field. Values are as billed (R-17); facts that differ from
policy go to ``AccountCapture.staff_notes`` only, never to ``for_model`` or the lookup snapshot (GRT-4).
"""

from __future__ import annotations

from typing import Final

from pydantic import Field, JsonValue

from meridian.domain.common import InvoiceId, LLMFacing, ToolErrorCode
from meridian.domain.records import MembershipTier
from meridian.domain.specialists import (
    AccountCapture,
    InvoiceView,
    MembershipView,
    StaffNote,
    WarrantyView,
)
from meridian.domain.tools import LookupEntry, ToolCallScope, ToolDef, ToolError, ToolKind, ToolResult
from meridian.policy.booking import MEMBER_ALLOWANCE_ROWS, SCHEDULE_FEES
from meridian.policy.texts import format_usd
from meridian.ports.runtime import UnitOfWorkFactory

READ_INVOICES_NAME: Final = "read_invoices"
READ_MEMBERSHIP_NAME: Final = "read_membership"
READ_WARRANTY_NAME: Final = "read_warranty"

NOT_VERIFIED_MESSAGE: Final = (
    "The customer has not been verified yet. Account tools work only after the one-time code is entered."
)
INVOICE_NUMBER_HELP: Final = (
    "The invoice number named in the conversation (INV- and six digits). "
    "Omit it to read every invoice on this account."
)
WARRANTY_TERM_SENTENCE: Final = (
    "Meridian's labor warranty on a full system installation is 2 years; "
    "5 years if you were a member at installation; a representative can confirm."
)

_TIER_PHRASE: Final = {"none": "non-members", "standard": "standard members", "plus": "plus members"}

_INVOICES_DESCRIPTION: Final = (
    "Returns this verified account's invoices as billed: invoice number, issue and due dates, line items with "
    "amounts in cents, total, balance and whether it is paid. Pass invoice_number to read one invoice, or omit it "
    "to read all of them. Use for bill, balance and line-item questions. Do not use for membership "
    "(read_membership) or warranty (read_warranty). It reports amounts as billed and never judges whether a "
    "charge is right."
)
_MEMBERSHIP_DESCRIPTION: Final = (
    "Returns this verified account's Comfort Club membership tier (none, standard or plus) and renewal date. "
    "Use for membership status and renewal questions. Do not use for invoices (read_invoices) or warranty "
    "(read_warranty)."
)
_WARRANTY_DESCRIPTION: Final = (
    "Returns this verified account's system install date, equipment brand and the installation labor warranty "
    "term. Use for warranty questions about the installed system. Do not use for invoices (read_invoices) or "
    "membership (read_membership)."
)


class ReadInvoicesArgs(LLMFacing):
    invoice_number: InvoiceId | None = Field(default=None, description=INVOICE_NUMBER_HELP)


class ReadMembershipArgs(LLMFacing):
    pass


class ReadWarrantyArgs(LLMFacing):
    pass


def _usd2(cents: int) -> str:
    return ("-" if cents < 0 else "") + f"${abs(cents) // 100:,}.{abs(cents) % 100:02d}"


def staff_notes_for(invoice: InvoiceView, tier: MembershipTier) -> tuple[StaffNote, ...]:
    """Facts for the staff brief, never verdicts. Rule 1: billed differs from the fee schedule. Rule 2: no credit."""
    notes: list[StaffNote] = []
    for line in invoice.lines:
        if line.description not in SCHEDULE_FEES:
            continue
        if line.description in MEMBER_ALLOWANCE_ROWS and tier != "none":
            continue
        scheduled = SCHEDULE_FEES[line.description][tier]
        if line.amount_cents != scheduled:
            tail = (
                f"lists {_usd2(scheduled)} for {_TIER_PHRASE[tier]}"
                if scheduled > 0
                else f"waives it for {_TIER_PHRASE[tier]}"
            )
            notes.append(
                StaffNote(
                    kind="billed_differs_from_schedule",
                    record_id=invoice.invoice_id,
                    text=(
                        f"{invoice.invoice_id} bills {line.description} at {_usd2(line.amount_cents)}; "
                        f"the 2026 fee schedule {tail}."
                    ),
                    source_file="pricing/2026_fee_schedule.pdf",
                )
            )
    diag = [ln for ln in invoice.lines if ln.description == "Diagnostic visit" and ln.amount_cents > 0]
    other = [ln for ln in invoice.lines if ln.description not in SCHEDULE_FEES]
    credit = [ln for ln in invoice.lines if ln.amount_cents < 0]
    if diag and other and not credit:
        notes.append(
            StaffNote(
                kind="diagnostic_without_credit",
                record_id=invoice.invoice_id,
                text=(
                    f"{invoice.invoice_id} bills the {format_usd(diag[0].amount_cents)} diagnostic visit beside a "
                    "repair with no credit line; the FAQ credits the diagnostic when the repair is approved at "
                    "the same visit (the record does not say whether it was)."
                ),
                source_file="faq/customer_faq.md",
            )
        )
    return tuple(notes)


def _invoices_seen(views: tuple[InvoiceView, ...]) -> str:
    if not views:
        return "invoices: none"
    return "; ".join(
        f"{v.invoice_id} total {_usd2(v.total_cents)} balance {_usd2(v.balance_cents)} lines "
        f"{' / '.join(_usd2(ln.amount_cents) for ln in v.lines)}"
        for v in views
    )


def _refused(name: str, scope: ToolCallScope) -> ToolResult:
    return ToolResult(
        ok=False,
        for_model=ToolError(code=ToolErrorCode.NOT_VERIFIED, message=NOT_VERIFIED_MESSAGE, retryable=False),
        captured=None,
        lookup=LookupEntry(
            tool=name,
            record_ids=(),
            passage_ids=(),
            result_seen="refused:not_verified",
            message_id=scope.message_id,
            turn_id=scope.ids.turn_id,
        ),
        lookup_written=False,
    )


def _result(
    name: str,
    for_model: dict[str, JsonValue],
    captured: AccountCapture,
    record_ids: tuple[str, ...],
    seen: str,
    scope: ToolCallScope,
) -> ToolResult:
    return ToolResult(
        ok=True,
        for_model=for_model,
        captured=captured,
        lookup=LookupEntry(
            tool=name,
            record_ids=record_ids,
            passage_ids=(),
            result_seen=seen,
            message_id=scope.message_id,
            turn_id=scope.ids.turn_id,
        ),
        lookup_written=False,
    )


def account_tools(uow: UnitOfWorkFactory) -> tuple[ToolDef, ...]:
    """(read_invoices, read_membership, read_warranty), each bound to ``scope.customer_id`` (R-14)."""

    def read_invoices(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, ReadInvoicesArgs):
            raise TypeError("read_invoices expects ReadInvoicesArgs")
        cid = scope.customer_id
        if cid is None:
            return _refused(READ_INVOICES_NAME, scope)
        with uow() as tx:
            row = tx.core.reads.customer(cid)
            if row is None:
                raise LookupError("customer row missing")
            if args.invoice_number is None:
                views = tx.identity.invoices_for(cid)
            else:
                one = tx.identity.invoice(cid, args.invoice_number)
                views = (one,) if one is not None else ()
            tier = row.membership_tier
        notes = tuple(n for v in views for n in staff_notes_for(v, tier))
        return _result(
            READ_INVOICES_NAME,
            {"invoices": [v.model_dump(mode="json") for v in views]},
            AccountCapture(invoices=views, staff_notes=notes),
            tuple(str(v.invoice_id) for v in views),
            _invoices_seen(views),
            scope,
        )

    def read_membership(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, ReadMembershipArgs):
            raise TypeError("read_membership expects ReadMembershipArgs")
        cid = scope.customer_id
        if cid is None:
            return _refused(READ_MEMBERSHIP_NAME, scope)
        with uow() as tx:
            row = tx.core.reads.customer(cid)
            if row is None:
                raise LookupError("customer row missing")
            view = MembershipView(tier=row.membership_tier, renewal_date=row.membership_renewal_date)
        renewal = view.renewal_date.isoformat() if view.renewal_date else "none"
        return _result(
            READ_MEMBERSHIP_NAME,
            {"membership": view.model_dump(mode="json")},
            AccountCapture(membership=view),
            (str(cid),),
            f"membership tier {view.tier} renewal {renewal}",
            scope,
        )

    def read_warranty(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, ReadWarrantyArgs):
            raise TypeError("read_warranty expects ReadWarrantyArgs")
        cid = scope.customer_id
        if cid is None:
            return _refused(READ_WARRANTY_NAME, scope)
        with uow() as tx:
            row = tx.core.reads.customer(cid)
            if row is None:
                raise LookupError("customer row missing")
            install = row.system_install_date
            brand = row.system_brand
        if install is None:
            return _result(
                READ_WARRANTY_NAME,
                {"warranty": None},
                AccountCapture(),
                (str(cid),),
                "warranty install none",
                scope,
            )
        view = WarrantyView(install_date=install, equipment_brand=brand, sentence=WARRANTY_TERM_SENTENCE)
        return _result(
            READ_WARRANTY_NAME,
            {"warranty": view.model_dump(mode="json")},
            AccountCapture(warranty=view),
            (str(cid),),
            f"warranty install {install.isoformat()} brand {(brand or 'none')[:40]}",
            scope,
        )

    return (
        ToolDef(
            name=READ_INVOICES_NAME,
            description=_INVOICES_DESCRIPTION,
            args_model=ReadInvoicesArgs,
            kind=ToolKind.ACCOUNT_READ,
            effect="read",
            requires_verified=True,
            executor=read_invoices,
        ),
        ToolDef(
            name=READ_MEMBERSHIP_NAME,
            description=_MEMBERSHIP_DESCRIPTION,
            args_model=ReadMembershipArgs,
            kind=ToolKind.ACCOUNT_READ,
            effect="read",
            requires_verified=True,
            executor=read_membership,
        ),
        ToolDef(
            name=READ_WARRANTY_NAME,
            description=_WARRANTY_DESCRIPTION,
            args_model=ReadWarrantyArgs,
            kind=ToolKind.ACCOUNT_READ,
            effect="read",
            requires_verified=True,
            executor=read_warranty,
        ),
    )
