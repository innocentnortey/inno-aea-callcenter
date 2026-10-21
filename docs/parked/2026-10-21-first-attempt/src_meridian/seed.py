"""Labelled demo seed cases so the supervisor and owner views have work to show (consolidated §8; PRD R-33)."""
from __future__ import annotations

import json

from meridian import db
from meridian.config import now

SEEDS = [
    ("MHC-C-D001", "refund", "P3", "unassigned", "2026-10-15T19:00", "A representative will get to your refund request within 2 business days.",
     ["I want a full refund on the repair. It didn't fix anything and I had to call another company."],
     ["The repair didn't fix anything", "Had to call another company"], "Whether a refund or a warranty recall is warranted.",
     "Seeded from transcript CALL-20260710-0136 (customer words); due time set in the past to show an overdue case."),
    ("MHC-C-D002", "complaint", "P3", "unassigned", "2026-10-16T19:00", "A representative will get back to you within 1 business day.",
     ["I've called three times about the same problem and nobody has called me back."], ["Called three times before"],
     "Who calls the customer, and how to resolve the repeated problem.", "Seeded from CALL-20260724-0391; due today."),
    ("MHC-C-D003", "late_technician", "P2", "claimed", "2026-10-19T19:00", "A representative will get back to you within 1 business day.",
     ["My window was 12 to 4 and it's 4:30. Nobody's here and nobody's called."], [],
     "The actual ETA, and whether the diagnostic fee is waived for the delay (staff discretion).", "Seeded from CALL-20260721-0261."),
]


def seed() -> None:
    t = now().isoformat(timespec="seconds")
    with db.connect() as conn:
        if conn.execute("SELECT count(*) FROM cases WHERE demo_seed=1").fetchone()[0]:
            return
        for cid, reason, pri, state, due, promise, needs, claims, decide, note in SEEDS:
            tid = f"seed-{cid}"
            conn.execute("INSERT OR IGNORE INTO conversations(thread_id, created_at, outcome, case_id) VALUES(?,?,?,?)",
                         (tid, t, "escalated", cid))
            for q in needs:
                conn.execute("INSERT INTO messages(thread_id,role,author,text,created_at) VALUES(?,?,?,?,?)",
                             (tid, "user", "customer", q, t))
            brief = {"why": reason.replace("_", " ").capitalize(), "reason": reason, "customer_needs": needs, "facts": [],
                     "claims": claims, "ai_did": ["Demo seed case: no records were read."], "told_customer": promise,
                     "due_at": due, "decide": decide, "who": {"customer_id": None, "identity": "Demo seed: not identified."},
                     "seed_note": note}
            conn.execute("""INSERT OR IGNORE INTO cases(case_id,thread_id,created_at,reason,priority,state,owner,next_action,due_at,
                            promise_text,identity_status,brief,demo_seed,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1,?)""",
                         (cid, tid, t, reason, pri, state, "Sam (demo)" if state == "claimed" else None, decide, due,
                          promise, "Demo seed: not identified.", json.dumps(brief), t))
