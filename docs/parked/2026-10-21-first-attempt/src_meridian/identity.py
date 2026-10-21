"""Simulated contact-code verification (OD-3 = audit DEC-3; PRD R-14…R-16).

Locate a record (a locator is not proof), send a one-time code to the phone or email already on that record —
delivered only to the labelled demo inbox — then verify. Codes are stored hashed and never returned to the model.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import timedelta

from meridian import db
from meridian.config import now

CODE_TTL_MIN = 10
MAX_ATTEMPTS = 3
MAX_SENDS = 3


def _digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")[-10:]


def _norm_name(s: str | None) -> str:
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def mask_phone(p: str) -> str:
    d = _digits(p)
    return f"(***) ***-**{d[-2:]}" if d else "unknown"


def mask_email(e: str) -> str:
    if not e or "@" not in e:
        return "unknown"
    user, dom = e.split("@", 1)
    return f"{user[0]}•••@{dom}"


def _conv(conn, thread_id: str):
    conn.execute("INSERT OR IGNORE INTO conversations(thread_id, created_at) VALUES(?,?)",
                 (thread_id, now().isoformat(timespec="seconds")))
    return conn.execute("SELECT * FROM conversations WHERE thread_id=?", (thread_id,)).fetchone()


def status(thread_id: str) -> dict:
    with db.connect() as conn:
        c = _conv(conn, thread_id)
        return {"customer_id": c["customer_id"], "verified": bool(c["verified"])}


def locate(thread_id: str, name: str | None = None, phone: str | None = None, customer_id: str | None = None,
           invoice_id: str | None = None) -> dict:
    """Find exactly one record. Returns only whether it was found and masked contacts — never account details."""
    with db.connect() as conn:
        _conv(conn, thread_id)
        row = None
        if customer_id:
            row = conn.execute("SELECT * FROM customers WHERE upper(customer_id)=upper(?)", (customer_id.strip(),)).fetchone()
        elif invoice_id:
            row = conn.execute("SELECT c.* FROM invoices i JOIN customers c USING(customer_id) WHERE upper(i.invoice_id)=upper(?)",
                               (invoice_id.strip(),)).fetchone()
        elif name and phone:
            rows = [r for r in conn.execute("SELECT * FROM customers").fetchall()
                    if _digits(r["phone"]) == _digits(phone) and _norm_name(r["name"]) == _norm_name(name)]
            row = rows[0] if len(rows) == 1 else None
        if not row:
            return {"found": False, "message": "No single matching record. Do not reveal whether an account exists; "
                                               "offer a representative instead."}
        conn.execute("UPDATE conversations SET customer_id=?, verified=0 WHERE thread_id=?", (row["customer_id"], thread_id))
        return {"found": True, "contacts": {"phone": mask_phone(row["phone"]), "email": mask_email(row["email"])}}


def send_code(thread_id: str, channel: str = "phone") -> dict:
    channel = "email" if channel == "email" else "phone"
    with db.connect() as conn:
        c = _conv(conn, thread_id)
        if not c["customer_id"]:
            return {"sent": False, "message": "Locate the customer's record first."}
        sends = conn.execute("SELECT count(*) FROM verification_codes WHERE thread_id=?", (thread_id,)).fetchone()[0]
        if sends >= MAX_SENDS:
            return {"sent": False, "message": "Code limit reached; hand off to a representative."}
        cust = conn.execute("SELECT * FROM customers WHERE customer_id=?", (c["customer_id"],)).fetchone()
        dest_full = cust["phone"] if channel == "phone" else cust["email"]
        masked = mask_phone(dest_full) if channel == "phone" else mask_email(dest_full)
        code = f"{secrets.randbelow(10**6):06d}"
        t = now()
        conn.execute("INSERT INTO verification_codes(thread_id,customer_id,channel,destination_masked,code_hash,created_at,expires_at)"
                     " VALUES(?,?,?,?,?,?,?)",
                     (thread_id, cust["customer_id"], channel, masked, hashlib.sha256(code.encode()).hexdigest(),
                      t.isoformat(timespec="seconds"), (t + timedelta(minutes=CODE_TTL_MIN)).isoformat(timespec="seconds")))
        conn.execute("INSERT INTO demo_inbox(at,channel,destination,body) VALUES(?,?,?,?)",
                     (t.isoformat(timespec="seconds"), "SMS" if channel == "phone" else "Email",
                      f"{cust['name']} · {masked}",
                      f"Meridian Home Comfort verification code: {code}. It expires in {CODE_TTL_MIN} minutes."))
    return {"sent": True, "destination": masked, "channel": channel,
            "note": "Delivered to the labelled demo inbox only (simulation); never show or repeat a code in chat."}


def verify(thread_id: str, code: str) -> dict:
    code = re.sub(r"\D", "", code or "")
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM verification_codes WHERE thread_id=? AND used=0 ORDER BY id DESC LIMIT 1",
                           (thread_id,)).fetchone()
        if not row:
            return {"verified": False, "message": "No active code; send one first."}
        if now().isoformat(timespec="seconds") > row["expires_at"]:
            return {"verified": False, "message": "Code expired; send a new one."}
        if row["attempts"] >= MAX_ATTEMPTS:
            return {"verified": False, "locked": True, "message": "Too many attempts; hand off to a representative."}
        ok = hashlib.sha256(code.encode()).hexdigest() == row["code_hash"]
        conn.execute("UPDATE verification_codes SET attempts=attempts+1, used=? WHERE id=?", (1 if ok else 0, row["id"]))
        if ok:
            conn.execute("UPDATE conversations SET verified=1, customer_id=? WHERE thread_id=?", (row["customer_id"], thread_id))
            return {"verified": True}
        left = MAX_ATTEMPTS - row["attempts"] - 1
        return {"verified": False, "attempts_left": left, "locked": left <= 0}
