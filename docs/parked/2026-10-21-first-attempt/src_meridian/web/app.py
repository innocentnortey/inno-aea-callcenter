"""FastAPI app: customer chat, demo inbox, staff console, supervisor/owner views, monitoring (PRD R-1, R-30…R-35)."""
from __future__ import annotations

import json
import secrets
import statistics
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from meridian import cases, db, seed
from meridian.agent import graph
from meridian.config import SETTINGS, now

HERE = Path(__file__).parent
app = FastAPI(title="Meridian Home Comfort assistant")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
T = Jinja2Templates(directory=HERE / "templates")
STAFF_TOKENS: set[str] = set()
_RATE: dict[str, list[float]] = defaultdict(list)


@app.on_event("startup")
def startup() -> None:
    db.ensure()
    seed.seed()
    from meridian.kb import retrieve
    retrieve._index()


def _ctx(request: Request, **kw):
    return {"request": request, "today": now().strftime("%a %b %-d, %Y · %-I:%M %p"), "staffed": cases.staffed(),
            "emergency": SETTINGS.emergency_number, **kw}


def _rate_ok(key: str, per_min: int = 20) -> bool:
    t = time.time()
    _RATE[key] = [x for x in _RATE[key] if t - x < 60]
    if len(_RATE[key]) >= per_min:
        return False
    _RATE[key].append(t)
    return True


def _staff(request: Request) -> bool:
    return request.cookies.get("staff") in STAFF_TOKENS


# ---------------------------------------------------------------- customer
@app.get("/", response_class=HTMLResponse)
def chat_page(request: Request):
    return T.TemplateResponse(request, "chat.html", _ctx(request))


@app.post("/api/chat")
async def api_chat(request: Request):
    body = await request.json()
    tid = str(body.get("thread_id") or "")[:64] or secrets.token_hex(8)
    text = str(body.get("text") or "").strip()[:1500]
    ip = request.client.host if request.client else "x"
    if not text:
        raise HTTPException(400, "empty")
    if not _rate_ok(ip) or not _rate_ok("t:" + tid, 12):
        return JSONResponse({"thread_id": tid, "replies": ["You're sending messages quickly. Please wait a moment."]})
    replies = graph.handle(tid, text)
    return {"thread_id": tid, "replies": replies, **_thread_status(tid)}


def _thread_status(tid: str) -> dict:
    with db.connect() as conn:
        conv = conn.execute("SELECT controller, case_id FROM conversations WHERE thread_id=?", (tid,)).fetchone()
    return {"controller": conv["controller"] if conv else "ai", "case_id": conv["case_id"] if conv else None,
            "staffed": cases.staffed()}


@app.get("/api/thread/{tid}")
def api_thread(tid: str, after: int = 0):
    with db.connect() as conn:
        rows = conn.execute("SELECT id, role, author, text FROM messages WHERE thread_id=? AND id>? ORDER BY id",
                            (tid, after)).fetchall()
    return {"messages": [dict(r) for r in rows], **_thread_status(tid)}


@app.get("/demo/inbox", response_class=HTMLResponse)
def demo_inbox(request: Request):
    with db.connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM demo_inbox ORDER BY id DESC LIMIT 30")]
    return T.TemplateResponse(request, "inbox.html", _ctx(request, items=rows))


# ---------------------------------------------------------------- staff
@app.get("/staff/login", response_class=HTMLResponse)
def staff_login_page(request: Request):
    return T.TemplateResponse(request, "login.html", _ctx(request, password_hint=SETTINGS.staff_password))


@app.post("/staff/login")
def staff_login(password: str = Form(...)):
    if password != SETTINGS.staff_password:
        return RedirectResponse("/staff/login?bad=1", status_code=303)
    tok = secrets.token_hex(16)
    STAFF_TOKENS.add(tok)
    r = RedirectResponse("/staff", status_code=303)
    r.set_cookie("staff", tok, httponly=True, samesite="lax")
    return r


def _need_staff(request: Request):
    if not _staff(request):
        raise HTTPException(303, headers={"Location": "/staff/login"})


@app.get("/staff", response_class=HTMLResponse)
def staff_home(request: Request):
    _need_staff(request)
    with db.connect() as conn:
        open_cases = [dict(r) for r in conn.execute(
            "SELECT * FROM cases WHERE state NOT IN ('resolved','closed_unresolved') ORDER BY "
            "CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END, due_at")]
        closed = [dict(r) for r in conn.execute(
            "SELECT * FROM cases WHERE state IN ('resolved','closed_unresolved') ORDER BY updated_at DESC LIMIT 20")]
    al = cases.alerts()
    return T.TemplateResponse(request, "staff.html", _ctx(request, open_cases=open_cases, closed=closed, alerts=al,
                                                  owner=_owner_metrics()))


def _owner_metrics() -> dict:
    with db.connect() as conn:
        convs = [dict(r) for r in conn.execute("SELECT * FROM conversations WHERE thread_id NOT LIKE 'seed-%'")]
        cs = [dict(r) for r in conn.execute("SELECT * FROM cases WHERE demo_seed=0")]
        lat = [r["value"] for r in conn.execute("SELECT value FROM metrics WHERE kind='turn_latency_s'")]
        tok = conn.execute("SELECT coalesce(sum(value),0) FROM metrics WHERE kind='tokens'").fetchone()[0]
        errs = conn.execute("SELECT count(*) FROM metrics WHERE kind IN ('model_error','tool_error')").fetchone()[0]
        turns = conn.execute("SELECT count(*) FROM metrics WHERE kind='turn'").fetchone()[0]
        flags = conn.execute("SELECT count(*) FROM flags WHERE reviewed=0").fetchone()[0]
    total = len(convs)
    escalated = sum(1 for c in convs if c["case_id"])
    by_reason = defaultdict(int)
    for c in cs:
        by_reason[c["reason"]] += 1
    due = [c for c in cs if c["promise_status"] in ("kept", "missed")]
    kept = sum(1 for c in due if c["promise_status"] == "kept")
    lat_sorted = sorted(lat)
    return {"conversations": total, "ai_only": total - escalated, "escalated": escalated,
            "by_reason": dict(sorted(by_reason.items(), key=lambda x: -x[1])),
            "promises_due": len(due), "promises_kept": kept,
            "p50": round(statistics.median(lat_sorted), 1) if lat_sorted else None,
            "p95": round(lat_sorted[int(0.95 * (len(lat_sorted) - 1))], 1) if lat_sorted else None,
            "tokens": int(tok), "errors": errs, "turns": turns, "flags": flags}


@app.get("/staff/case/{case_id}", response_class=HTMLResponse)
def staff_case(request: Request, case_id: str):
    _need_staff(request)
    with db.connect() as conn:
        c = conn.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        if not c:
            raise HTTPException(404)
        c = dict(c)
        msgs = [dict(r) for r in conn.execute("SELECT * FROM messages WHERE thread_id=? ORDER BY id", (c["thread_id"],))]
        events = [dict(r) for r in conn.execute("SELECT * FROM case_events WHERE case_id=? ORDER BY id", (case_id,))]
        logs = [dict(r) for r in conn.execute("SELECT * FROM lookup_log WHERE thread_id=? ORDER BY id", (c["thread_id"],))]
        sources = _sources(conn, logs)
    brief = json.loads(c["brief"])
    return T.TemplateResponse(request, "case.html", _ctx(request, c=c, brief=brief, msgs=msgs, events=events, sources=sources))


def _sources(conn, logs: list[dict]) -> list[dict]:
    """Snapshot (what the AI saw) beside the current record, with a changed-since marker (C4, D6)."""
    out = []
    for l in logs:
        res = json.loads(l["result"] or "{}")
        if l["tool"] == "get_invoices":
            for inv in res.get("invoices", []):
                cur = conn.execute("SELECT balance_cents FROM invoices WHERE invoice_id=?", (inv["invoice_id"],)).fetchone()
                now_bal = cur["balance_cents"] / 100 if cur else None
                out.append({"label": f"Invoice {inv['invoice_id']}", "snapshot": f"balance ${inv['balance']:.2f}; "
                            + ", ".join(f"{x['desc']} ${x['amount']:.0f}" for x in inv["lines"]),
                            "current": f"balance ${now_bal:.2f}" if now_bal is not None else "not found",
                            "changed": now_bal is not None and abs(now_bal - inv["balance"]) > 0.001, "at": l["at"]})
        elif l["tool"] == "get_appointments":
            for a in res.get("appointments", []):
                cur = conn.execute("SELECT a.status, s.slot_date, s.window FROM appointments a JOIN appointment_slots s "
                                   "USING(slot_id) WHERE appointment_id=?", (a["appointment_id"],)).fetchone()
                now_s = f"{cur['status']} {cur['slot_date']} {cur['window']}" if cur else "not found"
                was = f"scheduled {a['slot_date']} {a['window']}"
                out.append({"label": f"Appointment {a['appointment_id']}", "snapshot": was, "current": now_s,
                            "changed": now_s != was, "at": l["at"]})
        elif l["tool"] == "search_kb":
            out.append({"label": "Knowledge base search", "snapshot": "; ".join(sorted(set(res.get("sources", [])))),
                        "current": "current documents only (archive and old copies excluded)", "changed": False,
                        "at": l["at"]})
    return out


@app.post("/staff/case/{case_id}/action")
def staff_action(request: Request, case_id: str, action: str = Form(...), text: str = Form(""),
                 outcome: str = Form(""), name: str = Form("Riley (demo representative)")):
    _need_staff(request)
    with db.connect() as conn:
        c = dict(conn.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone())
    if action == "claim":
        cases.transition(case_id, name, "claimed", "claimed", owner=name)
    elif action == "join":
        cases.transition(case_id, name, "in_progress", "joined the live chat; AI paused", owner=name)
        with db.connect() as conn:
            conn.execute("UPDATE conversations SET controller='human' WHERE thread_id=?", (c["thread_id"],))
        cases.add_message(c["thread_id"], "assistant", "system", f"{name} has joined the chat. The automated assistant is paused.")
    elif action == "reply" and text.strip():
        cases.add_message(c["thread_id"], "assistant", name, text.strip()[:1500])
        with db.connect() as conn:
            conn.execute("INSERT INTO case_events(case_id,at,actor,event,detail) VALUES(?,?,?,?,?)",
                         (case_id, now().isoformat(timespec="seconds"), name, "replied", text.strip()[:200]))
    elif action == "handback":
        with db.connect() as conn:
            conn.execute("UPDATE conversations SET controller='ai' WHERE thread_id=?", (c["thread_id"],))
        cases.add_message(c["thread_id"], "assistant", "system", f"{name} handed the chat back to the automated assistant.")
        cases.transition(case_id, name, "waiting", "handed back to the AI", owner=name)
    elif action == "followup":
        with db.connect() as conn:
            conn.execute("INSERT INTO case_events(case_id,at,actor,event,detail) VALUES(?,?,?,?,?)",
                         (case_id, now().isoformat(timespec="seconds"), name, "followup_recorded",
                          f"Demo: recorded, not sent. {text.strip()[:300]}"))
        cases.transition(case_id, name, "in_progress", "follow-up contact recorded (demo, not sent)", owner=name)
    elif action in ("resolve", "close"):
        to = "resolved" if action == "resolve" else "closed_unresolved"
        if c["state"] == "in_progress":
            cases.add_message(c["thread_id"], "assistant", "system", f"{name} closed the chat.")
        cases.transition(case_id, name, to, outcome or action, owner=c["owner"] or name, outcome=outcome or action)
    elif action == "flag":
        with db.connect() as conn:
            conn.execute("INSERT INTO flags(case_id,thread_id,at,kind,note) VALUES(?,?,?,?,?)",
                         (case_id, c["thread_id"], now().isoformat(timespec="seconds"), outcome or "ai_wrong", text[:300]))
    return RedirectResponse(f"/staff/case/{case_id}", status_code=303)


@app.post("/staff/staffing")
def staff_staffing(request: Request, on: str = Form(...)):
    _need_staff(request)
    cases.set_staffing(on == "on")
    return RedirectResponse("/staff", status_code=303)


@app.post("/staff/advance")
def staff_advance(request: Request, minutes: int = Form(...)):
    _need_staff(request)
    db.set_setting("sim_minutes_offset", str(db.get_setting_int("sim_minutes_offset", 0) + int(minutes)))
    return RedirectResponse("/staff", status_code=303)


@app.post("/admin/reset")
def admin_reset(request: Request, token: str = Form("")):
    if not (_staff(request) or (SETTINGS.admin_token and token == SETTINGS.admin_token)):
        raise HTTPException(403)
    db.reset()
    seed.seed()
    graph.reset_graph()
    return RedirectResponse("/staff", status_code=303)


@app.get("/healthz")
def healthz():
    return {"ok": True, "today": now().isoformat(), "staffed": cases.staffed()}


@app.get("/monitor", response_class=HTMLResponse)
def monitor(request: Request):
    m = _owner_metrics()
    evalp = Path(SETTINGS.var_dir) / "eval_report.json"
    report = json.loads(evalp.read_text()) if evalp.exists() else None
    return T.TemplateResponse(request, "monitor.html", _ctx(request, m=m, report=report))
