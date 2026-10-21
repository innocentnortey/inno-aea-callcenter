"""Tools the agent may call. Identity and booking rules are enforced here, in code (agent-architecture rule 17).

Every call is written to lookup_log (PRD R-29): tool, record, args, the result the AI saw.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from meridian import db, identity, policy
from meridian.config import now
from meridian.kb import retrieve

SERVICE_TYPES = {"hvac_repair", "hvac_tune_up", "plumbing", "estimate"}


def _log(thread_id: str, tool: str, args: dict, result, record_ref: str | None = None) -> None:
    with db.connect() as conn:
        conn.execute("INSERT INTO lookup_log(thread_id,at,tool,record_ref,args,result) VALUES(?,?,?,?,?,?)",
                     (thread_id, now().isoformat(timespec="seconds"), tool, record_ref,
                      json.dumps({k: v for k, v in args.items() if k != "code"}), json.dumps(result)[:4000]))


def _require_verified(thread_id: str) -> str | None:
    st = identity.status(thread_id)
    return st["customer_id"] if st["verified"] else None


DENIED = {"error": "not_verified", "message": "Private details need the one-time code first (locate_customer → send_code → verify_code)."}


def search_kb(thread_id: str, query: str) -> dict:
    hits = retrieve.search(query, k=4)
    res = {"passages": [{"id": h["id"], "source": h["file"], "section": h["section"], "version": h["version"],
                         "text": h["text"]} for h in hits]}
    _log(thread_id, "search_kb", {"query": query}, {"ids": [h["id"] for h in hits],
                                                    "sources": [h["file"] for h in hits]}, ",".join(h["id"] for h in hits))
    return res


def locate_customer(thread_id: str, name: str | None = None, phone: str | None = None,
                    customer_id: str | None = None, invoice_id: str | None = None) -> dict:
    res = identity.locate(thread_id, name, phone, customer_id, invoice_id)
    _log(thread_id, "locate_customer", {"by": [k for k, v in {"name": name, "phone": phone, "customer_id": customer_id,
                                                              "invoice_id": invoice_id}.items() if v]}, {"found": res["found"]})
    return res


def send_code(thread_id: str, channel: str = "phone") -> dict:
    res = identity.send_code(thread_id, channel)
    _log(thread_id, "send_code", {"channel": channel}, {"sent": res.get("sent")})
    return res


def verify_code(thread_id: str, code: str) -> dict:
    res = identity.verify(thread_id, code)
    _log(thread_id, "verify_code", {}, {"verified": res.get("verified")})
    return res


def get_account(thread_id: str) -> dict:
    cid = _require_verified(thread_id)
    if not cid:
        return DENIED
    with db.connect() as conn:
        c = conn.execute("SELECT * FROM customers WHERE customer_id=?", (cid,)).fetchone()
    inst = c["system_install_date"]
    years = None
    if inst:
        d = date.fromisoformat(inst)
        years = round((now().date() - d).days / 365.25, 1)
    res = {"customer_id": cid, "first_name": c["name"].split()[0], "city": c["city"], "zip": c["zip"],
           "service_zone": policy.zone_for(c["city"], c["zip"]), "membership_tier": c["membership_tier"],
           "membership_renewal_date": c["membership_renewal_date"], "system_brand": c["system_brand"],
           "system_install_date": inst, "system_age_years": years,
           "install_labor_warranty_note": ("Install labor: 2 years (5 years if a Comfort Club member at the time of "
                                           "installation; the record has no enrollment date, so staff can confirm)."),
           "within_2yr_install_labor": (years is not None and years < 2)}
    _log(thread_id, "get_account", {}, {k: res[k] for k in ("membership_tier", "membership_renewal_date", "system_brand",
                                                            "system_install_date")}, f"customers:{cid}")
    return res


def get_invoices(thread_id: str) -> dict:
    cid = _require_verified(thread_id)
    if not cid:
        return DENIED
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM invoices WHERE customer_id=? ORDER BY issued_date DESC", (cid,)).fetchall()
    inv = [{"invoice_id": r["invoice_id"], "issued_date": r["issued_date"], "due_date": r["due_date"],
            "amount": r["amount_cents"] / 100, "balance": r["balance_cents"] / 100,
            "lines": [{"desc": li["desc"], "amount": li["cents"] / 100} for li in json.loads(r["line_items"])]}
           for r in rows]
    res = {"invoices": inv, "note": "Explain lines only; never adjudicate or promise a credit, refund or waiver."}
    _log(thread_id, "get_invoices", {}, res, ",".join(f"invoices:{i['invoice_id']}" for i in inv))
    return res


def get_appointments(thread_id: str) -> dict:
    cid = _require_verified(thread_id)
    if not cid:
        return DENIED
    with db.connect() as conn:
        rows = conn.execute("""SELECT a.appointment_id, a.issue_description, a.status, a.is_warranty_visit, s.slot_date,
                               s.window, s.service_type, t.name AS tech FROM appointments a JOIN appointment_slots s
                               USING(slot_id) JOIN technicians t ON t.tech_id=s.tech_id
                               WHERE a.customer_id=? AND a.status='scheduled' ORDER BY s.slot_date""", (cid,)).fetchall()
    n = now()
    appts = [{**dict(r), "window_label": policy.WINDOW_LABELS.get(r["window"], r["window"]),
              "hours_until_window": round(policy.hours_until(r["slot_date"], r["window"], n), 1),
              "late_change_fee_applies": policy.late_fee_applies(r["slot_date"], r["window"], n)} for r in rows]
    res = {"appointments": appts, "late_change_fee": policy.LATE_FEE}
    _log(thread_id, "get_appointments", {}, res, ",".join(f"appointments:{a['appointment_id']}" for a in appts))
    return res


def find_slots(thread_id: str, service_type: str, preferred_date: str | None = None,
               preferred_window: str | None = None) -> dict:
    cid = _require_verified(thread_id)
    if not cid:
        return DENIED
    if service_type not in SERVICE_TYPES:
        return {"error": f"service_type must be one of {sorted(SERVICE_TYPES)}"}
    with db.connect() as conn:
        c = conn.execute("SELECT * FROM customers WHERE customer_id=?", (cid,)).fetchone()
        zone = policy.zone_for(c["city"], c["zip"])
        if not zone:
            res = {"error": "outside_service_area", "message": "This address is not in a bookable zone; hand off."}
            _log(thread_id, "find_slots", {"service_type": service_type}, res)
            return res
        member = c["membership_tier"] in ("standard", "plus")
        statuses = ("open", "reserved_members") if member else ("open",)
        today = now().date().isoformat()
        rows = conn.execute(f"""SELECT s.slot_id, s.slot_date, s.window, s.status, t.name AS tech FROM appointment_slots s
                               JOIN technicians t ON t.tech_id=s.tech_id WHERE s.zone=? AND s.service_type=?
                               AND s.status IN ({','.join('?'*len(statuses))}) AND s.slot_date>=?
                               ORDER BY s.slot_date, s.window""", (zone, service_type, *statuses, today)).fetchall()
    n = now()
    opts = [dict(r) for r in rows if policy.hours_until(r["slot_date"], r["window"], n) > 2]

    def score(o):
        s = 0
        if preferred_date and o["slot_date"] == preferred_date:
            s -= 10
        if preferred_window and o["window"] == preferred_window:
            s -= 5
        return (s, o["slot_date"], o["window"])

    exact = [o for o in opts if (not preferred_date or o["slot_date"] == preferred_date)
             and (not preferred_window or o["window"] == preferred_window)]
    ranked = sorted(opts, key=score)[:5]
    for o in ranked:
        o["window_label"] = policy.WINDOW_LABELS.get(o["window"], o["window"])
        o["weekday"] = date.fromisoformat(o["slot_date"]).strftime("%A")
    res = {"zone": zone, "member": member, "exact_match_available": bool(exact), "options": ranked,
           "note": "Offer the closest options; if none match the request, say so and offer these alternatives."}
    _log(thread_id, "find_slots", {"service_type": service_type, "preferred_date": preferred_date,
                                   "preferred_window": preferred_window}, {"options": [o["slot_id"] for o in ranked]})
    return res


def book_slot(thread_id: str, slot_id: int, issue_description: str) -> dict:
    cid = _require_verified(thread_id)
    if not cid:
        return DENIED
    with db.connect() as conn:
        conv = conn.execute("SELECT bookings FROM conversations WHERE thread_id=?", (thread_id,)).fetchone()
        from meridian.config import SETTINGS
        if conv and conv["bookings"] >= SETTINGS.max_sessions_bookings:
            return {"error": "booking_limit", "message": "Booking limit for this chat reached; hand off."}
        dup = conn.execute("SELECT appointment_id FROM appointments WHERE customer_id=? AND slot_id=? AND status='scheduled'",
                           (cid, slot_id)).fetchone()
        if dup:
            return {"booked": True, "appointment_id": dup["appointment_id"], "idempotent": True}
        c = conn.execute("SELECT * FROM customers WHERE customer_id=?", (cid,)).fetchone()
        s = conn.execute("SELECT s.*, t.name AS tech FROM appointment_slots s JOIN technicians t ON t.tech_id=s.tech_id "
                         "WHERE slot_id=?", (slot_id,)).fetchone()
        member = c["membership_tier"] in ("standard", "plus")
        ok_status = ("open", "reserved_members") if member else ("open",)
        if not s or s["zone"] != policy.zone_for(c["city"], c["zip"]) or s["status"] not in ok_status:
            res = {"booked": False, "message": "That slot can't be booked for this customer (taken, wrong zone, or "
                                                "member-only). Search again and offer alternatives."}
            _log(thread_id, "book_slot", {"slot_id": slot_id}, res)
            return res
        cur = conn.execute("UPDATE appointment_slots SET status='booked' WHERE slot_id=? AND status IN ('open','reserved_members')",
                           (slot_id,))
        if cur.rowcount != 1:
            return {"booked": False, "message": "Slot was just taken; search again."}
        ap = conn.execute("INSERT INTO appointments(slot_id,customer_id,issue_description,created_at,status,is_warranty_visit)"
                          " VALUES(?,?,?,?, 'scheduled', 0)",
                          (slot_id, cid, issue_description[:200], now().isoformat(timespec="seconds")))
        conn.execute("UPDATE conversations SET bookings=bookings+1 WHERE thread_id=?", (thread_id,))
    fee = "waived (Comfort Club member)" if member else "$89, credited toward the repair if approved the same visit"
    if s["service_type"] == "hvac_tune_up":
        fee = "included for Comfort Club members" if member else "$129 tune-up"
    if s["service_type"] == "estimate":
        fee = "free in-home estimate"
    res = {"booked": True, "appointment_id": ap.lastrowid, "date": s["slot_date"],
           "weekday": date.fromisoformat(s["slot_date"]).strftime("%A"),
           "window": policy.WINDOW_LABELS.get(s["window"], s["window"]), "technician": s["tech"],
           "service_type": s["service_type"], "fee_note": fee,
           "texts": "A text the morning of the visit with the technician's name and photo, and another when they are 30 minutes away."}
    _log(thread_id, "book_slot", {"slot_id": slot_id}, res, f"appointments:{ap.lastrowid}")
    return res


def _owned_appt(conn, cid: str, appointment_id: int):
    return conn.execute("""SELECT a.*, s.slot_date, s.window, s.zone, s.service_type FROM appointments a
                           JOIN appointment_slots s USING(slot_id) WHERE a.appointment_id=? AND a.customer_id=?
                           AND a.status='scheduled'""", (appointment_id, cid)).fetchone()


def reschedule_appointment(thread_id: str, appointment_id: int, new_slot_id: int, fee_acknowledged: bool = False) -> dict:
    cid = _require_verified(thread_id)
    if not cid:
        return DENIED
    with db.connect() as conn:
        a = _owned_appt(conn, cid, appointment_id)
        if not a:
            return {"rescheduled": False, "message": "No scheduled appointment with that ID for this customer."}
        if policy.late_fee_applies(a["slot_date"], a["window"], now()) and not fee_acknowledged:
            res = {"rescheduled": False, "needs_fee_acknowledgement": True, "fee": policy.LATE_FEE,
                   "say": "Under our current policy, a $49 late-change fee applies to changes within 24 hours of your "
                          "appointment window. Would you like to go ahead?"}
            _log(thread_id, "reschedule_appointment", {"appointment_id": appointment_id}, res)
            return res
        s = conn.execute("SELECT s.*, t.name AS tech FROM appointment_slots s JOIN technicians t ON t.tech_id=s.tech_id "
                         "WHERE slot_id=?", (new_slot_id,)).fetchone()
        c = conn.execute("SELECT * FROM customers WHERE customer_id=?", (cid,)).fetchone()
        member = c["membership_tier"] in ("standard", "plus")
        ok_status = ("open", "reserved_members") if member else ("open",)
        if not s or s["zone"] != a["zone"] or s["service_type"] != a["service_type"] or s["status"] not in ok_status:
            return {"rescheduled": False, "message": "New slot not available for this appointment; search again."}
        conn.execute("UPDATE appointment_slots SET status='booked' WHERE slot_id=?", (new_slot_id,))
        conn.execute("UPDATE appointment_slots SET status='open' WHERE slot_id=?", (a["slot_id"],))
        conn.execute("UPDATE appointments SET slot_id=? WHERE appointment_id=?", (new_slot_id, appointment_id))
    res = {"rescheduled": True, "date": s["slot_date"], "weekday": date.fromisoformat(s["slot_date"]).strftime("%A"),
           "window": policy.WINDOW_LABELS.get(s["window"], s["window"]), "technician": s["tech"],
           "late_fee_note": (f"A ${policy.LATE_FEE} late-change fee applies under current policy (not charged in this chat)"
                             if fee_acknowledged else None)}
    _log(thread_id, "reschedule_appointment", {"appointment_id": appointment_id, "new_slot_id": new_slot_id}, res,
         f"appointments:{appointment_id}")
    return res


def cancel_appointment(thread_id: str, appointment_id: int, fee_acknowledged: bool = False) -> dict:
    cid = _require_verified(thread_id)
    if not cid:
        return DENIED
    with db.connect() as conn:
        a = _owned_appt(conn, cid, appointment_id)
        if not a:
            return {"cancelled": False, "message": "No scheduled appointment with that ID for this customer."}
        if policy.late_fee_applies(a["slot_date"], a["window"], now()) and not fee_acknowledged:
            res = {"cancelled": False, "needs_fee_acknowledgement": True, "fee": policy.LATE_FEE,
                   "say": "Under our current policy, a $49 late-cancellation fee applies within 24 hours of your "
                          "appointment window. Would you like to go ahead?"}
            _log(thread_id, "cancel_appointment", {"appointment_id": appointment_id}, res)
            return res
        conn.execute("UPDATE appointments SET status='cancelled' WHERE appointment_id=?", (appointment_id,))
        conn.execute("UPDATE appointment_slots SET status='open' WHERE slot_id=?", (a["slot_id"],))
    res = {"cancelled": True, "appointment_id": appointment_id,
           "late_fee_note": (f"A ${policy.LATE_FEE} late-cancellation fee applies under current policy (not charged in this chat)"
                             if fee_acknowledged else None)}
    _log(thread_id, "cancel_appointment", {"appointment_id": appointment_id}, res, f"appointments:{appointment_id}")
    return res
