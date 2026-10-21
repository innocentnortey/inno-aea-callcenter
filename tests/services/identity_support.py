"""Shared helpers for the AEA-27 frozen identity tests. Synthetic values only; no phone, code or secret is typed here.

AEA-27's own modules are imported lazily (importlib) so the suite collects before they exist.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib
import re
import secrets
import sqlite3
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import SecretStr

from meridian.adapters.sqlite.migrate import ISSUED_TABLES
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.domain.identity import Locator
from meridian.domain.tools import ToolCallScope
from meridian.domain.turn import TurnIds
from meridian.policy.limits import IdentityLimits
from tests.fixtures.sqlite import TempStore
from tests.unit.adapters.sqlite.helpers import new_thread, new_turn

NOW: datetime = DEMO_START
OMAR = "MHC-10002"
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def new_secret() -> SecretStr:
    return SecretStr(secrets.token_urlsafe(32))


def make_service(
    store: TempStore, *, secret: SecretStr | None = None, limits: IdentityLimits | None = None
) -> Any:
    module = importlib.import_module("meridian.services.identity")
    return module.IdentityService(
        store.uow,
        session_secret=secret if secret is not None else new_secret(),
        limits=limits or IdentityLimits(),
    )


def turn_ids(thread_id: Any) -> TurnIds:
    return TurnIds.model_validate(
        {
            "thread_id": str(thread_id),
            "turn_id": str(new_turn()),
            "request_id": str(uuid4()),
            "run_tag": "live",
            "run_id": None,
            "agent_version": "test",
        }
    )


def customer_contact(store: TempStore, customer_id: str) -> tuple[str, str]:
    """(name, phone) of an issued customer, read from the temp working copy at run time."""
    conn = sqlite3.connect(store.db_path)
    try:
        row = conn.execute(
            "SELECT name, phone FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return str(row[0]), str(row[1])


def raw_rows(store: TempStore, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(store.db_path)
    try:
        return [tuple(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def insert_customer(store: TempStore, row: dict[str, object | None]) -> None:
    cols = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    conn = sqlite3.connect(store.db_path)
    try:
        conn.execute(f"INSERT INTO customers ({cols}) VALUES ({marks})", tuple(row.values()))  # noqa: S608
        conn.commit()
    finally:
        conn.close()


def insert_omar_twin(store: TempStore) -> None:
    """Duplicate identity: a second customer with Omar's name and phone."""
    conn = sqlite3.connect(store.db_path)
    try:
        conn.execute(
            "INSERT INTO customers (customer_id, name, phone, email, service_address, city, zip, membership_tier) "
            "SELECT 'MHC-99991', name, phone, email, service_address, city, zip, 'none' FROM customers "
            "WHERE customer_id = ?",
            (OMAR,),
        )
        conn.commit()
    finally:
        conn.close()


def insert_no_contact(store: TempStore) -> None:
    insert_customer(
        store,
        {
            "customer_id": "MHC-99992",
            "name": "Synthetic Nocontact",
            "phone": "",
            "email": None,
            "service_address": "synthetic address",
            "city": "Austin",
            "zip": "78701",
            "membership_tier": "none",
        },
    )


def insert_email_only(store: TempStore) -> str:
    email = "s" + uuid4().hex[:8] + "@example.test"
    insert_customer(
        store,
        {
            "customer_id": "MHC-99993",
            "name": "Synthetic Mailonly",
            "phone": "",
            "email": email,
            "service_address": "synthetic address",
            "city": "Austin",
            "zip": "78701",
            "membership_tier": "none",
        },
    )
    return email


def locator(**fields: object) -> Locator:
    return Locator.model_validate(fields)


def omar_by_id() -> Locator:
    return locator(customer_id=OMAR)


def locate_and_send(svc: Any, thread: Any, session: str, now: datetime, loc: Locator | None = None) -> Any:
    """Locate (Omar by customer id unless given) then send one code; returns the send result."""
    located = svc.locate(thread, loc or omar_by_id(), now)
    assert located.kind == "located", located
    return svc.send_code(thread, session, now)


def latest_digits(svc: Any, session: str, now: datetime) -> str:
    """The digits of the newest inbox message, as the CON-6 route would read them."""
    msgs = svc.inbox(session, now)
    assert msgs and msgs[0].code is not None
    return str(msgs[0].code.get_secret_value())


def only_code(svc: Any, session: str, now: datetime) -> str:
    active = [m for m in svc.inbox(session, now) if m.status == "active"]
    assert len(active) == 1
    assert active[0].code is not None
    return str(active[0].code.get_secret_value())


def wrong(digits: str) -> str:
    return f"{(int(digits) + 1) % 1_000_000:06d}"


def count(store: TempStore, table: str) -> int:
    return int(raw_rows(store, f"SELECT COUNT(*) FROM {table}")[0][0])  # noqa: S608


def non_issued_text(store: TempStore, *, skip_columns: tuple[str, ...] = ("code_hmac",)) -> str:
    """Every value of every non-issued table, joined; uuids blanked so a random id cannot mimic a code."""
    conn = sqlite3.connect(store.db_path)
    parts: list[str] = []
    try:
        tables = [
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            if r[0] not in ISSUED_TABLES and r[0] != "sqlite_sequence" and not str(r[0]).startswith("sqlite_")
        ]
        for table in tables:
            cols = [
                c[1]
                for c in conn.execute(f"PRAGMA table_info({table})").fetchall()
                if c[1] not in skip_columns
            ]
            if not cols:
                continue
            for row in conn.execute(f"SELECT {', '.join(cols)} FROM {table}").fetchall():  # noqa: S608
                parts.extend(str(v) for v in row if v is not None)
    finally:
        conn.close()
    return _UUID.sub("<id>", "\n".join(parts))


def hmac_hex(secret: SecretStr, digits: str) -> str:
    key = secret.get_secret_value().encode("utf-8")
    return hmac.new(key, digits.encode("utf-8"), hashlib.sha256).hexdigest()


def scope_for_customer(customer_id: str | None, *, message_id: int = 1) -> ToolCallScope:
    return ToolCallScope.model_validate(
        {
            "ids": turn_ids(new_thread()),
            "customer_id": customer_id,
            "shown_slot_ids": frozenset(),
            "now": NOW,
            "message_id": message_id,
        }
    )
