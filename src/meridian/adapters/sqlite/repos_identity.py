"""Repository shell for identity and verification codes (AEA-02 shell; body: AEA-27, graph-tools section 5).

Every method runs on the unit of work's connection inside the caller's transaction and none commits. Times are
demo-clock readings written with ``format_wall`` (MC-20). No error text carries a stored value.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from typing import Literal

from pydantic import Field, SecretStr

from meridian.adapters.sqlite.db import StorageError, format_wall, integrity_errors, last_row_id, parse_wall
from meridian.domain.common import CustomerId, InvoiceId, MeridianModel, ThreadId
from meridian.domain.specialists import InvoiceView

__all__ = ["ContactRow", "IdentityCodeRow", "IdentityRepos", "IdentityThreadRow", "InboxRow"]


class IdentityThreadRow(MeridianModel):
    thread_id: ThreadId
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None
    masked_hint: str | None
    channel: Literal["phone", "email"] | None
    verified_at: datetime | None
    updated_at: datetime


class IdentityCodeRow(MeridianModel):
    """code_hmac never leaves the service."""

    id: int
    thread_id: ThreadId
    customer_id: CustomerId
    code_hmac: str
    held_by: str
    sent_at: datetime
    expires_at: datetime
    tries_left: int = Field(ge=0, le=3)
    used_at: datetime | None
    inbox_message_id: int


class InboxRow(MeridianModel):
    """No code and no body column."""

    id: int
    demo_session: str
    thread_id: ThreadId
    to_masked: str
    sent_at: datetime
    expires_at: datetime


class ContactRow(MeridianModel):
    """The locate inputs; contacts are wrapped so they never travel unwrapped."""

    customer_id: CustomerId
    name: str
    phone: SecretStr | None
    email: SecretStr | None


_CODE_COLUMNS = "id, thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, tries_left, used_at, inbox_message_id"
_INVOICE_COLUMNS = "invoice_id, issued_date, due_date, amount_cents, balance_cents, line_items"


def _opt_wall(text: str | None) -> datetime | None:
    return None if text is None else parse_wall(text)


def _code(r: tuple[object, ...]) -> IdentityCodeRow:
    return IdentityCodeRow.model_validate(
        {
            "id": r[0],
            "thread_id": r[1],
            "customer_id": r[2],
            "code_hmac": r[3],
            "held_by": r[4],
            "sent_at": parse_wall(str(r[5])),
            "expires_at": parse_wall(str(r[6])),
            "tries_left": r[7],
            "used_at": _opt_wall(None if r[8] is None else str(r[8])),
            "inbox_message_id": r[9],
        }
    )


def _inbox(r: tuple[object, ...]) -> InboxRow:
    return InboxRow.model_validate(
        {
            "id": r[0],
            "demo_session": r[1],
            "thread_id": r[2],
            "to_masked": r[3],
            "sent_at": parse_wall(str(r[4])),
            "expires_at": parse_wall(str(r[5])),
        }
    )


def _contact(r: tuple[object, ...]) -> ContactRow:
    return ContactRow.model_validate(
        {
            "customer_id": r[0],
            "name": r[1],
            "phone": SecretStr(str(r[2])) if r[2] else None,
            "email": SecretStr(str(r[3])) if r[3] else None,
        }
    )


def _view(row: tuple[object, ...]) -> InvoiceView:
    """An invoice as billed (R-17). A malformed line_items value raises StorageError without the value."""
    try:
        items = json.loads(str(row[5]))
    except (TypeError, ValueError):
        raise StorageError("invoices", "line_items not JSON") from None
    if not isinstance(items, list):
        raise StorageError("invoices", "line_items shape") from None
    lines: list[dict[str, object]] = []
    for item in items:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("desc"), str)
            or not isinstance(item.get("cents"), int)
            or isinstance(item.get("cents"), bool)
        ):
            raise StorageError("invoices", "line_items shape") from None
        lines.append({"description": item["desc"], "amount_cents": item["cents"]})
    return InvoiceView.model_validate(
        {
            "invoice_id": row[0],
            "lines": lines,
            "total_cents": row[3],
            "balance_cents": row[4],
            "issued_on": date.fromisoformat(str(row[1])),
            "due_on": date.fromisoformat(str(row[2])),
            "paid": row[4] == 0,
        }
    )


class IdentityRepos:
    """Repositories for 40_identity (identity_threads, identity_codes, demo_inbox) and the invoice reads; body AEA-27 (graph-tools §5, GRT-10)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def thread(self, thread_id: ThreadId) -> IdentityThreadRow | None:
        r = self._conn.execute(
            "SELECT thread_id, status, customer_id, masked_hint, channel, verified_at, updated_at "
            "FROM identity_threads WHERE thread_id = ?",
            (str(thread_id),),
        ).fetchone()
        if r is None:
            return None
        return IdentityThreadRow.model_validate(
            {
                "thread_id": r[0],
                "status": r[1],
                "customer_id": r[2],
                "masked_hint": r[3],
                "channel": r[4],
                "verified_at": _opt_wall(r[5]),
                "updated_at": parse_wall(r[6]),
            }
        )

    def save_thread(self, row: IdentityThreadRow) -> None:
        with integrity_errors("identity_threads"):
            self._conn.execute(
                "INSERT INTO identity_threads "
                "(thread_id, status, customer_id, masked_hint, channel, verified_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(thread_id) DO UPDATE SET status=excluded.status, customer_id=excluded.customer_id, "
                "masked_hint=excluded.masked_hint, channel=excluded.channel, "
                "verified_at=excluded.verified_at, updated_at=excluded.updated_at",
                (
                    str(row.thread_id),
                    row.status,
                    None if row.customer_id is None else str(row.customer_id),
                    row.masked_hint,
                    row.channel,
                    None if row.verified_at is None else format_wall(row.verified_at),
                    format_wall(row.updated_at),
                ),
            )

    def add_code(
        self,
        thread_id: ThreadId,
        customer_id: CustomerId,
        code_hmac: str,
        held_by: str,
        sent_at: datetime,
        expires_at: datetime,
        inbox_message_id: int,
        *,
        tries_left: int = 3,
    ) -> int:
        with integrity_errors("identity_codes"):
            cur = self._conn.execute(
                "INSERT INTO identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, "
                "tries_left, used_at, inbox_message_id) VALUES (?,?,?,?,?,?,?,NULL,?)",
                (
                    str(thread_id),
                    str(customer_id),
                    code_hmac,
                    held_by,
                    format_wall(sent_at),
                    format_wall(expires_at),
                    tries_left,
                    inbox_message_id,
                ),
            )
        return last_row_id(cur, "identity_codes")

    def newest_code(self, thread_id: ThreadId) -> IdentityCodeRow | None:
        r = self._conn.execute(
            f"SELECT {_CODE_COLUMNS} FROM identity_codes WHERE thread_id = ? ORDER BY id DESC LIMIT 1",  # noqa: S608
            (str(thread_id),),
        ).fetchone()
        return None if r is None else _code(r)

    def codes_sent(self, thread_id: ThreadId) -> int:
        r = self._conn.execute(
            "SELECT COUNT(*) FROM identity_codes WHERE thread_id = ?", (str(thread_id),)
        ).fetchone()
        return int(r[0])

    def spend_try(self, code_id: int) -> int:
        cur = self._conn.execute(
            "UPDATE identity_codes SET tries_left = MAX(tries_left - 1, 0) WHERE id = ?", (code_id,)
        )
        if cur.rowcount == 0:
            raise StorageError("identity_codes", "no row")
        r = self._conn.execute("SELECT tries_left FROM identity_codes WHERE id = ?", (code_id,)).fetchone()
        return int(r[0])

    def mark_used(self, code_id: int, used_at: datetime) -> None:
        cur = self._conn.execute(
            "UPDATE identity_codes SET used_at = ? WHERE id = ?", (format_wall(used_at), code_id)
        )
        if cur.rowcount == 0:
            raise StorageError("identity_codes", "no row")

    def add_inbox(
        self, demo_session: str, thread_id: ThreadId, to_masked: str, sent_at: datetime, expires_at: datetime
    ) -> int:
        with integrity_errors("demo_inbox"):
            cur = self._conn.execute(
                "INSERT INTO demo_inbox (demo_session, thread_id, to_masked, sent_at, expires_at) "
                "VALUES (?,?,?,?,?)",
                (demo_session, str(thread_id), to_masked, format_wall(sent_at), format_wall(expires_at)),
            )
        return last_row_id(cur, "demo_inbox")

    def inbox_for(self, demo_session: str) -> tuple[InboxRow, ...]:
        rows = self._conn.execute(
            "SELECT id, demo_session, thread_id, to_masked, sent_at, expires_at "
            "FROM demo_inbox WHERE demo_session = ? ORDER BY id DESC",
            (demo_session,),
        ).fetchall()
        return tuple(_inbox(r) for r in rows)

    def code_for_inbox(self, inbox_message_id: int) -> IdentityCodeRow | None:
        r = self._conn.execute(
            f"SELECT {_CODE_COLUMNS} FROM identity_codes WHERE inbox_message_id = ? ORDER BY id DESC LIMIT 1",  # noqa: S608
            (inbox_message_id,),
        ).fetchone()
        return None if r is None else _code(r)

    def invoices_for(self, customer_id: CustomerId) -> tuple[InvoiceView, ...]:
        rows = self._conn.execute(
            f"SELECT {_INVOICE_COLUMNS} FROM invoices WHERE customer_id = ? "  # noqa: S608
            "ORDER BY issued_date DESC, invoice_id DESC",
            (str(customer_id),),
        ).fetchall()
        return tuple(_view(r) for r in rows)

    def invoice(self, customer_id: CustomerId, invoice_id: InvoiceId) -> InvoiceView | None:
        """Another account's number reads None, the same as a missing one (GRT-10)."""
        r = self._conn.execute(
            f"SELECT {_INVOICE_COLUMNS} FROM invoices WHERE invoice_id = ? AND customer_id = ?",  # noqa: S608
            (str(invoice_id), str(customer_id)),
        ).fetchone()
        return None if r is None else _view(r)

    def contact(self, customer_id: CustomerId) -> ContactRow | None:
        r = self._conn.execute(
            "SELECT customer_id, name, phone, email FROM customers WHERE customer_id = ?", (str(customer_id),)
        ).fetchone()
        return None if r is None else _contact(r)

    def contacts(self) -> tuple[ContactRow, ...]:
        rows = self._conn.execute(
            "SELECT customer_id, name, phone, email FROM customers ORDER BY customer_id"
        ).fetchall()
        return tuple(_contact(r) for r in rows)
