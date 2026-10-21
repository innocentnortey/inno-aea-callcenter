"""Handoff cases: creation, the 8-heading brief, lifecycle, staffing state (PRD R-24…R-34; consolidated §5–§6)."""
from __future__ import annotations

import json
import re
from datetime import datetime

from meridian import db, policy
from meridian.config import now

REASON_LABELS = {
    "safety": "Safety report: instruction given first", "urgent_comfort": "Urgent comfort: no heat, no cooling or a leak",
    "burning_unclear": "Burning smell, risk unclear", "refund": "Refund request (policy: a person decides)",
    "billing_dispute": "Billing dispute (policy: a person decides)", "complaint": "Service complaint (policy: a person)",
    "manager_request": "Asked for a manager", "legal_or_chargeback": "Legal threat or chargeback (policy: a person)",
    "commercial": "Commercial project (policy: Meridian Commercial)", "late_technician": "Technician late (time-sensitive)",
    "fee_contested": "Customer contests the $49 late-change fee", "time_sensitive_action": "Action needed before a deadline",
    "unsupported_action": "Task the chat system can't complete", "customer_requested_person": "Customer asked for a person",
    "ai_failure": "The AI couldn't answer", "identity_unverified": "Couldn't verify identity", "out_of_scope": "Out of scope",
}
STATES = ("live_queued", "unassigned", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved")


def staffed() -> bool:
    return db.get_setting("staffing", "off") == "on"


def set_staffing(on: bool) -> list[str]:
    """Turn the labelled simulation on/off. Ending a shift converts live-queued cases to follow-up (OD-5)."""
    db.set_setting("staffing", "on" if on else "off")
    converted = []
    if not on:
        with db.connect() as conn:
            rows = conn.execute("SELECT * FROM cases WHERE state='live_queued'").fetchall()
            for r in rows:
                pri, text, due = policy.promise_for(r["reason"], False, now())
                conn.execute("UPDATE cases SET state='unassigned', promise_text=?, due_at=?, promise_status='changed', "
                             "updated_at=? WHERE case_id=?", (text, due, now().isoformat(timespec="seconds"), r["case_id"]))
                _event(conn, r["case_id"], "system", "staffing_ended", "converted to follow-up; customer told: " + text)
                _add_message(conn, r["thread_id"], "assistant", "system",
                             "Our team has gone offline before reaching you. " + text + f" Your reference is {r['case_id']}.")
                converted.append(r["case_id"])
    return converted


def _event(conn, case_id: str, actor: str, event: str, detail: str = "") -> None:
    conn.execute("INSERT INTO case_events(case_id,at,actor,event,detail) VALUES(?,?,?,?,?)",
                 (case_id, now().isoformat(timespec="seconds"), actor, event, detail))


def _add_message(conn, thread_id: str, role: str, author: str, text: str, meta: dict | None = None) -> None:
    conn.execute("INSERT INTO messages(thread_id,role,author,text,created_at,meta) VALUES(?,?,?,?,?,?)",
                 (thread_id, role, author, text, now().isoformat(timespec="seconds"), json.dumps(meta) if meta else None))
    conn.execute("UPDATE conversations SET last_activity=? WHERE thread_id=?", (now().isoformat(timespec="seconds"), thread_id))


def add_message(thread_id: str, role: str, author: str, text: str, meta: dict | None = None) -> None:
    with db.connect() as conn:
        conn.execute("INSERT OR IGNORE INTO conversations(thread_id, created_at) VALUES(?,?)",
                     (thread_id, now().isoformat(timespec="seconds")))
        _add_message(conn, thread_id, role, author, text, meta)


def open_case_for(thread_id: str):
    with db.connect() as conn:
        return conn.execute("SELECT * FROM cases WHERE thread_id=? AND state NOT IN ('resolved','closed_unresolved') "
                            "ORDER BY created_at DESC LIMIT 1", (thread_id,)).fetchone()


def _next_id(conn) -> str:
    n = conn.execute("SELECT count(*) FROM cases").fetchone()[0] + 1
    return f"MHC-C-{n:04d}"


def _facts_from_log(conn, thread_id: str) -> tuple[list[dict], list[str]]:
    """Verified facts and AI actions, assembled from the lookup log (not written by the model)."""
    facts, actions = [], []
    for r in conn.execute("SELECT * FROM lookup_log WHERE thread_id=? ORDER BY id", (thread_id,)):
        res = json.loads(r["result"] or "{}")
        t = r["tool"]
        if t == "get_invoices":
            for inv in res.get("invoices", []):
                lines = ", ".join(f"{li['desc']} ${li['amount']:.0f}" for li in inv["lines"])
                facts.append({"text": f"Invoice {inv['invoice_id']}: ${inv['amount']:.2f}, balance ${inv['balance']:.2f}, "
                                      f"due {inv['due_date']}. Lines: {lines}.", "source": f"invoices:{inv['invoice_id']}",
                              "read_at": r["at"]})
            actions.append("Read the customer's invoices and explained the lines.")
        elif t == "get_account":
            facts.append({"text": f"Membership: {res.get('membership_tier')}; renewal {res.get('membership_renewal_date') or '—'}; "
                                  f"system {res.get('system_brand')} installed {res.get('system_install_date')}.",
                          "source": r["record_ref"], "read_at": r["at"]})
            actions.append("Read the account record.")
        elif t == "get_appointments":
            for a in res.get("appointments", []):
                facts.append({"text": f"Appointment {a['appointment_id']}: {a['slot_date']} {a['window_label']}, "
                                      f"{a['service_type']}, technician {a['tech']}; {a['hours_until_window']} h until the window"
                                      f"{' (inside 24 h: $49 late-change fee applies)' if a['late_change_fee_applies'] else ''}.",
                              "source": f"appointments:{a['appointment_id']}", "read_at": r["at"]})
            actions.append("Looked up scheduled appointments.")
        elif t == "search_kb":
            actions.append(f"Searched the knowledge base ({', '.join(sorted(set(res.get('sources', []))))}).")
        elif t == "book_slot" and res.get("booked"):
            actions.append(f"Booked {res.get('weekday')} {res.get('date')} {res.get('window')} with {res.get('technician')}.")
        elif t in ("reschedule_appointment", "cancel_appointment"):
            if res.get("needs_fee_acknowledgement"):
                actions.append("Stated the $49 late-change fee under current policy before any change.")
            elif res.get("rescheduled") or res.get("cancelled"):
                actions.append(f"{t.split('_')[0].capitalize()}d appointment {r['record_ref'] or ''}.")
        elif t == "verify_code" and res.get("verified"):
            actions.append("Verified identity with the one-time code (demo simulation).")
    seen, uniq = set(), []
    for a in actions:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return facts, uniq


def _quotes_in(conn, thread_id: str, candidates: list[str]) -> list[str]:
    """Keep only quotes that appear in the customer's own messages (no invented words)."""
    text = " ".join(r["text"] for r in conn.execute("SELECT text FROM messages WHERE thread_id=? AND role='user'", (thread_id,)))
    norm = re.sub(r"\s+", " ", text.lower())
    out = []
    for q in candidates or []:
        qn = re.sub(r"\s+", " ", q.strip().strip('"').lower())
        if qn and qn in norm:
            out.append(q.strip().strip('"'))
    return out


def create_case(thread_id: str, reason: str, extraction: dict | None = None) -> dict:
    """Create (or return) the open case for this conversation; the promise comes from the policy table."""
    existing = open_case_for(thread_id)
    if existing:
        return {"case_id": existing["case_id"], "promise": existing["promise_text"], "state": existing["state"],
                "existing": True}
    is_staffed = staffed() and reason != "safety"
    priority, promise, due = policy.promise_for(reason, is_staffed, now())
    with db.connect() as conn:
        conn.execute("INSERT OR IGNORE INTO conversations(thread_id, created_at) VALUES(?,?)",
                     (thread_id, now().isoformat(timespec="seconds")))
        conv = conn.execute("SELECT * FROM conversations WHERE thread_id=?", (thread_id,)).fetchone()
        case_id = _next_id(conn)
        facts, actions = _facts_from_log(conn, thread_id)
        ex = extraction or {}
        needs = _quotes_in(conn, thread_id, ex.get("customer_needs", []))
        if not needs:
            last = conn.execute("SELECT text FROM messages WHERE thread_id=? AND role='user' ORDER BY id DESC LIMIT 1",
                                (thread_id,)).fetchone()
            needs = [last["text"][:200]] if last else []
        claims = _quotes_in(conn, thread_id, ex.get("claims", []))
        identity_status = ("Identity confirmed with a one-time code sent to the contact on record (demo simulation, not "
                           "production verification)." if conv["verified"] else
                           ("Record found, code not confirmed. No private details were shown." if conv["customer_id"]
                            else "Not identified."))
        brief = {
            "why": REASON_LABELS.get(reason, reason), "reason": reason, "customer_needs": needs,
            "facts": facts, "claims": claims, "ai_did": actions or ["Answered in chat; no records read."],
            "told_customer": promise, "due_at": due,
            "decide": ex.get("open_decision") or _default_decision(reason),
            "who": {"customer_id": conv["customer_id"] if conv["verified"] else None, "identity": identity_status},
        }
        state = "live_queued" if is_staffed else "unassigned"
        t = now().isoformat(timespec="seconds")
        conn.execute("""INSERT INTO cases(case_id,thread_id,created_at,reason,priority,state,next_action,due_at,promise_text,
                        customer_id,identity_status,brief,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (case_id, thread_id, t, reason, priority, state, brief["decide"], due, promise,
                      conv["customer_id"] if conv["verified"] else None, identity_status, json.dumps(brief), t))
        conn.execute("UPDATE conversations SET case_id=?, outcome='escalated' WHERE thread_id=?", (case_id, thread_id))
        _event(conn, case_id, "ai", "created", f"{reason} · {priority} · promise: {promise}")
    db.log_metric("handoff", 1, thread_id, {"reason": reason, "priority": priority, "staffed": is_staffed})
    return {"case_id": case_id, "promise": promise, "priority": priority, "state": state, "due_at": due, "existing": False}


def _default_decision(reason: str) -> str:
    return {"refund": "Whether a refund or a warranty recall is warranted.",
            "billing_dispute": "Whether the disputed charge stands, and any adjustment.",
            "complaint": "How to resolve the complaint, and who calls the customer.",
            "safety": "Whether to follow up and dispatch once the customer is safe.",
            "urgent_comfort": "Whether to expedite help beyond the emergency line.",
            "late_technician": "The actual ETA, and whether the diagnostic fee is waived for the delay (staff discretion).",
            "fee_contested": "Whether the $49 late-change fee stands (staff discretion: once per customer per year).",
            }.get(reason, "What the customer needs next, and who follows up.")


def set_followup(thread_id: str, channel: str, destination: str | None, window: str | None) -> dict:
    """OD-5: email by default, phone if preferred; private details only to a destination on record."""
    case = open_case_for(thread_id)
    if not case:
        return {"saved": False, "message": "No open case."}
    channel = "phone" if channel and channel.lower().startswith("p") else "email"
    with db.connect() as conn:
        conv = conn.execute("SELECT * FROM conversations WHERE thread_id=?", (thread_id,)).fetchone()
        on_record = None
        dest = destination
        if conv["customer_id"] and conv["verified"]:
            cust = conn.execute("SELECT phone,email FROM customers WHERE customer_id=?", (conv["customer_id"],)).fetchone()
            rec = cust["phone"] if channel == "phone" else cust["email"]
            if not destination or destination.lower() in ("on file", "on record", "same", "the one on file"):
                dest, on_record = rec, 1
            else:
                on_record = 1 if re.sub(r"\D", "", destination)[-10:] == re.sub(r"\D", "", rec)[-10:] or \
                    destination.strip().lower() == (rec or "").lower() else 0
        conn.execute("UPDATE cases SET followup_channel=?, followup_destination=?, destination_on_record=?, "
                     "followup_window=?, updated_at=? WHERE case_id=?",
                     (channel, dest, on_record, window, now().isoformat(timespec="seconds"), case["case_id"]))
        _event(conn, case["case_id"], "ai", "followup_preference", f"{channel} · window {window or '—'} · "
                                                                     f"on record: {on_record}")
    return {"saved": True, "channel": channel, "on_record": on_record}


def transition(case_id: str, actor: str, to: str, detail: str = "", owner: str | None = None,
               outcome: str | None = None) -> None:
    assert to in STATES
    with db.connect() as conn:
        case = conn.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        sets, vals = ["state=?", "updated_at=?"], [to, now().isoformat(timespec="seconds")]
        if owner is not None:
            sets.append("owner=?")
            vals.append(owner)
        if outcome:
            sets.append("outcome=?")
            vals.append(outcome)
        if to in ("resolved", "closed_unresolved") and case["promise_status"] == "open":
            kept = (not case["due_at"]) or now().isoformat(timespec="minutes") <= case["due_at"]
            sets.append("promise_status=?")
            vals.append("kept" if kept else "missed")
        conn.execute(f"UPDATE cases SET {', '.join(sets)} WHERE case_id=?", (*vals, case_id))
        _event(conn, case_id, actor, to, detail)
        if to == "in_progress" and case["state"] in ("live_queued", "claimed", "unassigned") and staffed():
            conn.execute("UPDATE conversations SET controller='human' WHERE thread_id=?", (case["thread_id"],))
        if to in ("resolved", "closed_unresolved"):
            conn.execute("UPDATE conversations SET controller='ai', outcome=? WHERE thread_id=?",
                         ("escalated_resolved" if to == "resolved" else "escalated_unresolved", case["thread_id"]))


def alerts() -> dict:
    """Supervisor view data: P0/P1, unowned, due soon, overdue, stuck (consolidated §6)."""
    t = now()
    soon = (t.replace(microsecond=0)).isoformat(timespec="minutes")
    with db.connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM cases WHERE state NOT IN ('resolved','closed_unresolved')")]
    def due_dt(r):
        return datetime.fromisoformat(r["due_at"]) if r["due_at"] else None
    out = {"priority": [r for r in rows if r["priority"] in ("P0", "P1")],
           "unowned": [r for r in rows if not r["owner"]],
           "overdue": [r for r in rows if due_dt(r) and due_dt(r) < t],
           "due_soon": [r for r in rows if due_dt(r) and t <= due_dt(r) <= t.replace(hour=23, minute=59)],
           "live_queue": [r for r in rows if r["state"] == "live_queued"]}
    out["now"] = soon
    return out
