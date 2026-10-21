"""One-time code identity: locate, send, verify and the demo inbox (AEA-27; DO-4 section 14, graph-tools section 5).

Decisions: GRT-2 (the six digits live only in this process's ``_held`` map and, as an HMAC, in ``identity_codes``),
GRT-3 (``NotVerified`` has no fields and ``verify`` never returns it). Nothing here logs, prints or traces, and no
exception message carries a value.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import uuid
from datetime import datetime, timedelta
from typing import Literal

from pydantic import SecretStr

from meridian.adapters.sqlite.repos_identity import ContactRow, IdentityThreadRow
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import ThreadId
from meridian.domain.identity import (
    CodeCapReached,
    CodeExpired,
    CodeLocked,
    CodeSent,
    CodeWrong,
    InboxMessage,
    Located,
    Locator,
    NotVerified,
    Verified,
)
from meridian.domain.turn import TurnIds
from meridian.policy.limits import IdentityLimits
from meridian.ports.runtime import UnitOfWorkFactory

_DIGITS = "0123456789"
_DOTS = "···"
_ELLIPSIS = "…"


def _digits(text: str) -> str:
    return "".join(ch for ch in text if ch in _DIGITS)


def _norm_name(text: str) -> str:
    return " ".join(text.split()).casefold()


def _mask(contact: ContactRow) -> tuple[Literal["phone", "email"], str, str] | None:
    """(channel, hint, to_masked) from the usable contact, phone first; only 2 digits or 1 letter leave."""
    if contact.phone is not None and len(d := _digits(contact.phone.get_secret_value())) >= 10:
        return ("phone", f"the phone ending in {d[-2:]}", f"{_DOTS}{d[-2:]}")
    if contact.email is not None:
        email = contact.email.get_secret_value()
        local = email.split("@", 1)[0]
        if "@" in email and local:
            return ("email", f"the email at {local[0]}{_DOTS}@{_ELLIPSIS}", f"{local[0]}{_DOTS}@{_ELLIPSIS}")
    return None


def _new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class IdentityService:
    """Prove a caller owns an account with a one-time code, per conversation (R-14, R-15, R-16)."""

    def __init__(self, uow: UnitOfWorkFactory, *, session_secret: SecretStr, limits: IdentityLimits) -> None:
        if not session_secret.get_secret_value():
            raise ValueError("session secret is empty")
        if not 1 <= limits.tries <= 3 or not 1 <= limits.max_sends <= 3 or limits.code_ttl_s <= 0:
            raise ValueError("identity limits outside the domain bounds")
        self._uow = uow
        self._secret = session_secret
        self._limits = limits
        self._boot_id = str(uuid.uuid4())
        self._held: dict[int, tuple[SecretStr, datetime]] = {}
        self._lock = threading.Lock()

    @property
    def boot_id(self) -> str:
        return self._boot_id

    def _hmac(self, digits: str) -> str:
        key = self._secret.get_secret_value().encode("utf-8")
        return hmac.new(key, digits.encode("utf-8"), hashlib.sha256).hexdigest()

    def _sends_left(self, codes_sent: int) -> int:
        return max(0, min(2, self._limits.max_sends - codes_sent))

    @staticmethod
    def _check_now(now: datetime) -> None:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")

    def _prune(self, now: datetime) -> None:
        with self._lock:
            for key in [k for k, (_, exp) in self._held.items() if exp <= now]:
                del self._held[key]

    def _hold(self, inbox_id: int, digits: SecretStr, expires_at: datetime) -> None:
        with self._lock:
            self._held[inbox_id] = (digits, expires_at)

    def _held_code(self, inbox_id: int) -> SecretStr | None:
        with self._lock:
            entry = self._held.get(inbox_id)
        return None if entry is None else entry[0]

    def _drop(self, inbox_id: int) -> None:
        with self._lock:
            self._held.pop(inbox_id, None)

    def locate(self, thread_id: ThreadId, locator: Locator, now: datetime) -> Located | NotVerified:
        """A locator is not proof: it only finds the account and returns a masked hint."""
        self._check_now(now)
        self._prune(now)
        with self._uow(write=True) as tx:
            tid = thread_id
            thread = tx.identity.thread(tid)
            if thread is not None and thread.status == "locked":
                return NotVerified()
            matches: list[ContactRow] = []
            if locator.customer_id is not None:
                c = tx.identity.contact(locator.customer_id)
                matches = [c] if c is not None else []
            elif locator.invoice_number is not None:
                inv = tx.core.reads.invoice(locator.invoice_number)
                c = tx.identity.contact(inv.customer_id) if inv is not None else None
                matches = [c] if c is not None else []
            elif locator.phone is not None and locator.name is not None:
                want = _digits(locator.phone.get_secret_value())
                if len(want) >= 10:
                    want10 = want[-10:]
                    want_name = _norm_name(locator.name)
                    matches = [
                        c
                        for c in tx.identity.contacts()
                        if c.phone is not None
                        and len(d := _digits(c.phone.get_secret_value())) >= 10
                        and d[-10:] == want10
                        and _norm_name(c.name) == want_name
                    ]
            mask = _mask(matches[0]) if len(matches) == 1 else None
            if mask is None:
                tx.identity.save_thread(
                    IdentityThreadRow(
                        thread_id=tid,
                        status="not_verified",
                        customer_id=None,
                        masked_hint=None,
                        channel=None,
                        verified_at=None,
                        updated_at=now,
                    )
                )
                tx.commit()
                return NotVerified()
            channel, hint, _ = mask
            tx.identity.save_thread(
                IdentityThreadRow(
                    thread_id=tid,
                    status="located",
                    customer_id=matches[0].customer_id,
                    masked_hint=hint,
                    channel=channel,
                    verified_at=None,
                    updated_at=now,
                )
            )
            tx.commit()
            return Located(masked_hint=hint)

    def send_code(
        self, thread_id: ThreadId, demo_session: str, now: datetime
    ) -> CodeSent | NotVerified | CodeCapReached:
        self._check_now(now)
        self._prune(now)
        tid = thread_id
        with self._uow(write=True) as tx:
            thread = tx.identity.thread(tid)
            if (
                thread is None
                or thread.status in ("not_checked", "not_verified")
                or thread.customer_id is None
            ):
                return NotVerified()
            if thread.status == "locked":
                return CodeCapReached()
            sent = tx.identity.codes_sent(tid)
            if sent >= self._limits.max_sends:
                tx.identity.save_thread(thread.model_copy(update={"status": "locked", "updated_at": now}))
                tx.commit()
                return CodeCapReached()
            contact = tx.identity.contact(thread.customer_id)
            mask = _mask(contact) if contact is not None else None
            if mask is None:
                return NotVerified()
            channel, hint, to_masked = mask
            digits = _new_code()
            expires_at = now + timedelta(seconds=self._limits.code_ttl_s)
            previous = tx.identity.newest_code(tid)
            inbox_id = tx.identity.add_inbox(demo_session, tid, to_masked, now, expires_at)
            tx.identity.add_code(
                tid,
                thread.customer_id,
                self._hmac(digits),
                self._boot_id,
                now,
                expires_at,
                inbox_id,
                tries_left=self._limits.tries,
            )
            tx.identity.save_thread(
                IdentityThreadRow(
                    thread_id=tid,
                    status="code_sent",
                    customer_id=thread.customer_id,
                    masked_hint=hint,
                    channel=channel,
                    verified_at=None,
                    updated_at=now,
                )
            )
            self._hold(inbox_id, SecretStr(digits), expires_at)
            try:
                tx.commit()
            except BaseException:
                self._drop(inbox_id)
                raise
        if previous is not None:
            self._drop(previous.inbox_message_id)
        return CodeSent(masked_hint=hint, expires_at=expires_at, sends_left=self._sends_left(sent + 1))

    def verify(
        self, ids: TurnIds, digits: SecretStr, now: datetime
    ) -> Verified | CodeWrong | CodeExpired | CodeLocked:
        """Never returns NotVerified (GRT-3): a failed code is a different customer card from no match."""
        self._check_now(now)
        self._prune(now)
        with self._uow(write=True) as tx:
            thread = tx.identity.thread(ids.thread_id)
            if thread is not None and thread.status == "verified" and thread.customer_id is not None:
                existing = next(
                    (
                        a
                        for a in tx.core.actions.for_thread(ids.thread_id)
                        if a.kind == ActionKind.VERIFIED and a.key.record_id == str(thread.customer_id)
                    ),
                    None,
                )
                if existing is not None:
                    return Verified(customer_id=thread.customer_id, action=existing)
            if (
                thread is None
                or thread.status in ("not_checked", "not_verified", "locked")
                or thread.customer_id is None
            ):
                return CodeLocked()
            left = self._sends_left(tx.identity.codes_sent(ids.thread_id))
            expired = CodeExpired(resend_offered=left > 0, sends_left=left)
            if thread.status == "located":
                return expired
            code = tx.identity.newest_code(ids.thread_id)
            if code is None or code.customer_id != thread.customer_id or code.used_at is not None:
                return expired
            if code.tries_left == 0:
                return CodeLocked()
            if (
                now >= code.expires_at
                or code.held_by != self._boot_id
                or self._held_code(code.inbox_message_id) is None
            ):
                return expired
            ok = hmac.compare_digest(self._hmac(digits.get_secret_value()), code.code_hmac)
            if ok:
                action = CompletedAction(
                    key=ActionKey(
                        thread_id=ids.thread_id,
                        turn_id=ids.turn_id,
                        kind=ActionKind.VERIFIED,
                        record_id=str(code.customer_id),
                    ),
                    kind=ActionKind.VERIFIED,
                    records={"customer": str(code.customer_id)},
                    at=now,
                )
                stored = tx.core.actions.record(action)
                tx.identity.mark_used(code.id, now)
                tx.identity.save_thread(
                    thread.model_copy(update={"status": "verified", "verified_at": now, "updated_at": now})
                )
                tx.commit()
                self._drop(code.inbox_message_id)
                return Verified(customer_id=code.customer_id, action=stored)
            tries_left = tx.identity.spend_try(code.id)
            if tries_left == 0:
                tx.identity.save_thread(thread.model_copy(update={"status": "locked", "updated_at": now}))
                tx.commit()
                self._drop(code.inbox_message_id)
                return CodeLocked()
            tx.commit()
            return CodeWrong(tries_left=tries_left)

    def inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]:
        """This login session's messages, newest first. `active` only while this process holds the digits (GRT-2)."""
        self._check_now(now)
        self._prune(now)
        out: list[InboxMessage] = []
        with self._uow() as tx:
            for row in tx.identity.inbox_for(demo_session):
                code = tx.identity.code_for_inbox(row.id)
                held = self._held_code(row.id)
                status: Literal["active", "used", "expired"]
                if code is not None and code.used_at is not None:
                    status = "used"
                elif code is None or now >= row.expires_at or code.held_by != self._boot_id or held is None:
                    status = "expired"
                else:
                    status = "active"
                out.append(
                    InboxMessage(
                        id=str(row.id),
                        at=row.sent_at,
                        to_masked=row.to_masked,
                        code=held if status == "active" else None,
                        status=status,
                        expires_at=row.expires_at,
                    )
                )
        return tuple(out)
