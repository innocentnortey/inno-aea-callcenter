"""AEA-27 PA-6: IdentityRepos round trips, cross-account invoice reads and value-free storage errors."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Literal

import pytest

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.repos_identity import IdentityThreadRow
from meridian.domain.common import CustomerId, ThreadId
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.adapters.sqlite.helpers import customer_id, invoice_id, new_thread

NOW = DEMO_START
_Status = Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]


def _row(thread_id: ThreadId, status: _Status, cust: CustomerId | None = None) -> IdentityThreadRow:
    return IdentityThreadRow(
        thread_id=thread_id,
        status=status,
        customer_id=cust,
        masked_hint=None,
        channel=None,
        verified_at=None,
        updated_at=NOW,
    )


def test_thread_upsert_and_code_rows() -> None:
    with temp_sqlite() as store:
        t = new_thread()
        with store.uow(write=True) as tx:
            tx.identity.save_thread(_row(t, "located", customer_id("MHC-10002")))
            tx.identity.save_thread(_row(t, "locked"))
            got = tx.identity.thread(t)
            assert got is not None and got.status == "locked" and got.customer_id is None
            inbox = tx.identity.add_inbox("s", t, "···02", NOW, NOW + timedelta(minutes=10))
            c1 = tx.identity.add_code(
                t, customer_id("MHC-10002"), "h" * 64, "boot", NOW, NOW + timedelta(minutes=10), inbox
            )
            c2 = tx.identity.add_code(
                t,
                customer_id("MHC-10002"),
                "g" * 64,
                "boot",
                NOW,
                NOW + timedelta(minutes=10),
                inbox,
                tries_left=2,
            )
            newest = tx.identity.newest_code(t)
            assert newest is not None and newest.id == c2 and newest.tries_left == 2
            first = tx.identity.code_for_inbox(inbox)
            assert first is not None and first.id == c2
            assert tx.identity.codes_sent(t) == 2
            assert [tx.identity.spend_try(c1) for _ in range(4)] == [2, 1, 0, 0]
            tx.identity.mark_used(c1, NOW)
            with pytest.raises(StorageError) as err:
                tx.identity.spend_try(99999)
            assert err.value.table == "identity_codes"
            with pytest.raises(StorageError):
                tx.identity.mark_used(99999, NOW)


def test_inbox_rows_newest_first_per_session() -> None:
    with temp_sqlite() as store:
        t = new_thread()
        with store.uow(write=True) as tx:
            a = tx.identity.add_inbox("s1", t, "···02", NOW, NOW)
            b = tx.identity.add_inbox("s1", t, "···02", NOW, NOW)
            tx.identity.add_inbox("s2", t, "···02", NOW, NOW)
            assert [r.id for r in tx.identity.inbox_for("s1")] == [b, a]
            assert tx.identity.inbox_for("none") == ()


def test_invoice_views_as_billed_and_cross_account_none() -> None:
    with temp_sqlite() as store, store.uow() as tx:
        view = tx.identity.invoice(customer_id("MHC-10002"), invoice_id("INV-204411"))
        assert view is not None
        assert [ln.amount_cents for ln in view.lines] == [8900, 24500, 14400]
        assert view.total_cents == 47800 and view.issued_on == date(2026, 10, 2) and not view.paid
        assert tx.identity.invoice(customer_id("MHC-10003"), invoice_id("INV-204411")) is None
        assert any(v.invoice_id == "INV-204411" for v in tx.identity.invoices_for(customer_id("MHC-10002")))


def test_malformed_line_items_hides_value() -> None:
    sentinel = "sentinel-not-json"
    with temp_sqlite() as store:
        conn = sqlite3.connect(store.db_path)
        conn.execute("UPDATE invoices SET line_items = ? WHERE invoice_id = 'INV-204411'", (sentinel,))
        conn.commit()
        conn.close()
        with store.uow() as tx, pytest.raises(StorageError) as err:
            tx.identity.invoice(customer_id("MHC-10002"), invoice_id("INV-204411"))
        assert sentinel not in str(err.value)


def test_contacts_wrap_secrets() -> None:
    with temp_sqlite() as store, store.uow() as tx:
        contacts = tx.identity.contacts()
        assert len(contacts) == 154
        one = tx.identity.contact(customer_id("MHC-10002"))
        assert one is not None and one.phone is not None and one.email is not None
        text = repr(one)
        assert one.phone.get_secret_value() not in text
        assert one.email.get_secret_value() not in text
