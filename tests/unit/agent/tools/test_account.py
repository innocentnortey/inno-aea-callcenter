"""AEA-27 (risk::security) frozen tests: account_tools executors and staff_notes_for.

Failure modes guarded: refusal (unverified scope, another account's invoice reads exactly like a missing one),
invariant (values as billed, staff notes never reach the model or the lookup record, no customer field in any args
model, member allowance rows are not prices). Temp SQLite copies only; no `.env`, no paid call.
AEA-27's module is imported lazily so the suite collects before it exists.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterator
from typing import Any

import pytest
from pydantic import TypeAdapter

from meridian.adapters.sqlite import repos_core_aux
from meridian.agent.tools.dispatch import _MESSAGES, ToolRegistry
from meridian.domain.common import CustomerId, InvoiceId, ToolErrorCode, ToolKind
from meridian.domain.specialists import InvoiceView, StaffNote
from meridian.domain.tools import ToolCallScope
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.identity_support import OMAR, raw_rows, scope_for_customer

_INVOICE: TypeAdapter[InvoiceId] = TypeAdapter(InvoiceId)
_CUSTOMER: TypeAdapter[CustomerId] = TypeAdapter(CustomerId)
NOTE_1 = (
    "INV-204411 bills After-hours dispatch at $144.00; the 2026 fee schedule lists $149.00 for non-members."
)
NOTE_2 = (
    "INV-204411 bills the $89 diagnostic visit beside a repair with no credit line; the FAQ credits the diagnostic "
    "when the repair is approved at the same visit (the record does not say whether it was)."
)
WARRANTY = (
    "Meridian's labor warranty on a full system installation is 2 years; 5 years if you were a member at "
    "installation; a representative can confirm."
)


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def _account() -> Any:
    return importlib.import_module("meridian.agent.tools.account")


def _run(store: TempStore, tool: int, args: Any, scope: ToolCallScope) -> Any:
    return _account().account_tools(store.uow)[tool].executor(args, scope)


def _view(invoice_id: str, lines: list[tuple[str, int]]) -> InvoiceView:
    total = sum(c for _, c in lines)
    return InvoiceView.model_validate(
        {
            "invoice_id": invoice_id,
            "lines": [{"description": d, "amount_cents": c} for d, c in lines],
            "total_cents": total,
            "balance_cents": total,
            "issued_on": "2026-10-01",
            "due_on": "2026-10-31",
            "paid": False,
        }
    )


def test_account_tool_defs_and_cross_account_invoice(store: TempStore) -> None:
    """[refusal] Flags, no customer field, and another account's invoice reads as 'none', same as a missing one."""
    account = _account()
    defs = account.account_tools(store.uow)
    assert tuple(d.name for d in defs) == ("read_invoices", "read_membership", "read_warranty")
    for d in defs:
        assert d.kind == ToolKind.ACCOUNT_READ and d.effect == "read" and d.requires_verified is True
        props = set(d.args_model.model_json_schema().get("properties", {}))
        assert not props & set(ToolCallScope.model_fields)
        assert not any("customer" in p for p in props)
    ToolRegistry(defs)
    other = raw_rows(
        store, "SELECT invoice_id FROM invoices WHERE customer_id <> ? ORDER BY invoice_id LIMIT 1", (OMAR,)
    )
    assert other
    assert raw_rows(store, "SELECT 1 FROM invoices WHERE invoice_id = 'INV-999999'") == []
    scope = scope_for_customer(OMAR)
    foreign = defs[0].executor(
        account.ReadInvoicesArgs(invoice_number=_INVOICE.validate_python(other[0][0])), scope
    )
    missing = defs[0].executor(
        account.ReadInvoicesArgs(invoice_number=_INVOICE.validate_python("INV-999999")), scope
    )
    for r in (foreign, missing):
        assert r.ok is True and r.for_model == {"invoices": []}
    assert foreign.model_dump_json() == missing.model_dump_json()
    refused = defs[0].executor(account.ReadInvoicesArgs(), scope_for_customer(None))
    assert refused.ok is False and refused.for_model.code == ToolErrorCode.NOT_VERIFIED
    assert refused.for_model.message == _MESSAGES[ToolErrorCode.NOT_VERIFIED]


def test_invoice_read_as_billed_staff_note_apart(store: TempStore) -> None:
    """[invariant] INV-204411 reads as billed; no verdict, no schedule figure, no staff note in model-facing text."""
    account = _account()
    res = _run(
        store, 0, account.ReadInvoicesArgs(invoice_number=_INVOICE.validate_python("INV-204411")),
        scope_for_customer(OMAR),
    )  # fmt: skip
    inv = res.for_model["invoices"][0]
    assert (inv["issued_on"], inv["due_on"]) == ("2026-10-02", "2026-11-01")
    assert inv["total_cents"] == 47800 and inv["balance_cents"] == 47800 and inv["paid"] is False
    assert [(ln["description"], ln["amount_cents"]) for ln in inv["lines"]] == [
        ("Diagnostic visit", 8900),
        ("Contactor replacement", 24500),
        ("After-hours dispatch", 14400),
    ]
    seen = json.dumps(res.for_model) + res.lookup.result_seen
    assert "149" not in seen
    for word in ("wrong", "incorrect", "overcharg", "error", "mistake", "should", "differ", "schedule"):
        assert word not in seen.lower(), word
    assert NOTE_1 not in seen and NOTE_2 not in seen
    assert [n.text for n in res.captured.staff_notes] == [NOTE_1, NOTE_2]


def test_staff_notes_rules(store: TempStore) -> None:
    """[invariant] Exactly the two facts for a non-member on INV-204411; none for a Plus member billed $0 diagnostic."""
    with store.uow() as tx:
        inv = tx.identity.invoice(_CUSTOMER.validate_python(OMAR), _INVOICE.validate_python("INV-204411"))
    assert inv is not None
    notes = _account().staff_notes_for(inv, "none")
    assert notes == (
        StaffNote.model_validate(
            {
                "kind": "billed_differs_from_schedule",
                "record_id": "INV-204411",
                "text": NOTE_1,
                "source_file": "pricing/2026_fee_schedule.pdf",
            }
        ),
        StaffNote.model_validate(
            {
                "kind": "diagnostic_without_credit",
                "record_id": "INV-204411",
                "text": NOTE_2,
                "source_file": "faq/customer_faq.md",
            }
        ),
    )
    plus = _view("INV-900001", [("Diagnostic visit", 0), ("Contactor replacement", 24500)])
    assert _account().staff_notes_for(plus, "plus") == ()


def test_membership_and_warranty_reads(store: TempStore, monkeypatch: pytest.MonkeyPatch) -> None:
    """[invariant] Membership and warranty equal the working copy's row and are read through core.reads.customer."""
    account = _account()
    calls: list[str] = []
    original = repos_core_aux.ReadsRepo.customer

    def spy(self: Any, customer_id: Any) -> Any:
        calls.append(str(customer_id))
        return original(self, customer_id)

    monkeypatch.setattr(repos_core_aux.ReadsRepo, "customer", spy)
    row = raw_rows(
        store,
        "SELECT membership_tier, membership_renewal_date, system_brand, system_install_date FROM customers "
        "WHERE customer_id = 'MHC-10003'",
    )[0]
    scope = scope_for_customer("MHC-10003")
    mem = _run(store, 1, account.ReadMembershipArgs(), scope)
    assert mem.for_model == {"membership": {"tier": row[0], "renewal_date": row[1]}}
    war = _run(store, 2, account.ReadWarrantyArgs(), scope)
    w = war.for_model["warranty"]
    assert w["install_date"] == row[3] == "2025-11-30" and w["equipment_brand"] == row[2] == "Lennox"
    assert w["sentence"] == account.WARRANTY_TERM_SENTENCE == WARRANTY
    assert len(calls) >= 2


def test_tune_up_member_no_note() -> None:
    """[invariant] A member allowance row is not compared as a price; a non-member's tune-up still is."""
    notes_for = _account().staff_notes_for
    member = _view("INV-900002", [("Seasonal tune-up", 12900)])
    assert notes_for(member, "standard") == () and notes_for(member, "plus") == ()
    billed = _view("INV-900003", [("Seasonal tune-up", 11900)])
    notes = notes_for(billed, "none")
    assert len(notes) == 1 and notes[0].kind == "billed_differs_from_schedule"
    assert notes[0].text == (
        "INV-900003 bills Seasonal tune-up at $119.00; the 2026 fee schedule lists $129.00 for non-members."
    )
