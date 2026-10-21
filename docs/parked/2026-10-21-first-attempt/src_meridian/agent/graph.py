"""The Meridian agent as a LangGraph graph (PRD §6.1).

Deterministic checks run first (safety, burning smell, urgent comfort, person request, human ownership); only then the
Claude tool loop. Promises and references are added by code from the policy table, never written by the model.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from datetime import date
from typing import TypedDict

import anthropic
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from meridian import cases, db, tools, triggers
from meridian.agent.prompt import TOOLS, system_prompt
from meridian.config import SETTINGS, now

_CORRECTION = re.compile(r"(that'?s not what i (asked|meant|said)|that'?s (wrong|not right|incorrect)|you'?re (wrong|not "
                         r"listening|not helping)|not helpful|useless|doesn'?t answer|you didn'?t answer)", re.I)
_FAILED = re.compile(r"(don'?t have (that|this) information|not able to (answer|find)|couldn'?t find|i'?m not sure)", re.I)
_YES = re.compile(r"\b(yes|yeah|yep|it did|they did|tripped|smoke|sparks?|flames?|fire)\b", re.I)
_NO_BOTH = re.compile(r"\b(no|nope|not|none|didn'?t|haven'?t)\b", re.I)
_UNSURE = re.compile(r"(not sure|don'?t know|no idea|can'?t tell|unsure|maybe)", re.I)
DAILY_TOKEN_CAP = int(os.getenv("MERIDIAN_DAILY_TOKEN_CAP", "4000000"))  # [A] backstop for SD-1.6 ($10/day); tune once measured


class S(TypedDict, total=False):
    thread_id: str
    user_text: str
    route: str
    reply: list
    signals: dict
    burning_pending: bool
    urgent_noticed: bool
    failed_answers: int
    tool_failures: int
    offered_person: bool
    handed_off: bool


def _today_label() -> str:
    d = now()
    return d.strftime("%A, %B %-d, %Y")


def _client():
    return anthropic.Anthropic()


# ---------------------------------------------------------------- nodes
def guard(state: S) -> S:
    tid, text = state["thread_id"], state["user_text"]
    with db.connect() as conn:
        conv = conn.execute("SELECT controller FROM conversations WHERE thread_id=?", (tid,)).fetchone()
    if conv and conv["controller"] == "human":
        return {"route": "human_held", "reply": []}
    sig = triggers.check(text)
    out: S = {"signals": sig.__dict__, "reply": []}
    if state.get("burning_pending"):
        if sig.safety or (_YES.search(text) and not re.search(r"\bno\b", text, re.I)):
            out.update(route="safety", burning_pending=False)
        elif _UNSURE.search(text) or not _NO_BOTH.search(text):
            out.update(route="burning_cautious", burning_pending=False)
        else:
            out.update(route="agent", burning_pending=False)
            out["signals"] = {**sig.__dict__, "burning_ruled_out": True}
        return out
    if sig.safety:
        out["route"] = "safety"
    elif sig.burning_unclear:
        out["route"] = "burning_ask"
    elif sig.wants_person:
        out["route"] = "person"
    elif sig.urgent_comfort and not state.get("urgent_noticed"):
        out["route"] = "urgent"
    else:
        out["route"] = "agent"
    return out


def safety(state: S) -> S:
    tid = state["thread_id"]
    case = cases.create_case(tid, "safety")
    msg = (triggers.SAFETY_INSTRUCTION + "\n\nOnce you're safely outside: if you'd like our team to follow up, you can "
           f"leave a phone number here. That's optional. Your reference is {case['case_id']}.")
    db.log_metric("safety_first", 1, tid)
    return {"reply": [msg], "handed_off": True}


def burning_ask(state: S) -> S:
    return {"burning_pending": True, "reply": [
        "A burning smell can be serious, so two quick questions first. Do you already know whether a circuit breaker "
        "has tripped? Please don't go to the panel to check. And do you see any smoke, sparks or flames?"]}


def burning_cautious(state: S) -> S:
    case = cases.create_case(state["thread_id"], "burning_unclear")
    msg = ("To be safe: if you smell gas, see smoke, sparks or flames, or a breaker has tripped, leave the home now and "
           "call 911 from outside. Please turn the system off at the thermostat and don't restart it.\n\n"
           f"For urgent help, call Meridian's 24/7 emergency number: {SETTINGS.emergency_number}.\n\n"
           f"I've also logged this for our team as an urgent request (reference {case['case_id']}). {case['promise']}")
    return {"reply": [msg], "handed_off": True}


def urgent(state: S) -> S:
    case = cases.create_case(state["thread_id"], "urgent_comfort")
    msg = (f"For no heat, no cooling or an active leak, please call Meridian's 24/7 emergency number now: "
           f"{SETTINGS.emergency_number}.\n\nI've also logged this for our team as an emergency-priority request "
           f"(reference {case['case_id']}). {case['promise']}\n\nA few quick questions help them: is it very hot or "
           "cold in your home right now, is any water still running, and is anyone at higher risk, like an older "
           "person, a baby or someone unwell? You can skip these. I can also look for the earliest regular "
           "appointment if you'd like.")
    return {"reply": [msg], "urgent_noticed": True}


def _followup_ask(staffed: bool) -> str:
    if staffed:
        return "You can keep chatting with me while you wait, if you like."
    return "We'll follow up by email unless you'd prefer a phone call. Which works best, and is there a good time?"


def person(state: S) -> S:
    case = cases.create_case(state["thread_id"], "customer_requested_person")
    st = case["state"] == "live_queued"
    msg = (f"Of course. I'm connecting you with our team. {case['promise']} Your reference is {case['case_id']}. "
           + _followup_ask(st))
    return {"reply": [msg], "handed_off": True}


def human_held(state: S) -> S:
    return {"reply": []}


def _history(tid: str, limit: int = 24) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute("SELECT role, author, text FROM messages WHERE thread_id=? ORDER BY id DESC LIMIT ?",
                            (tid, limit)).fetchall()
    msgs = []
    for r in reversed(rows):
        role = "user" if r["role"] == "user" else "assistant"
        text = r["text"] if r["author"] in ("customer", "ai", "system") else f"[Representative {r['author']}]: {r['text']}"
        if msgs and msgs[-1]["role"] == role:
            msgs[-1]["content"] += "\n\n" + text
        else:
            msgs.append({"role": role, "content": text})
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    return msgs


def _tokens_today() -> int:
    day = date.today().isoformat()  # wall-clock day for spend, not the dataset clock
    if db.get_setting("spend_day") != day:
        db.set_setting("spend_day", day)
        db.set_setting("tokens_today", "0")
    return db.get_setting_int("tokens_today", 0)


def _add_tokens(n: int) -> None:
    db.set_setting("tokens_today", str(_tokens_today() + n))


def agent(state: S) -> S:
    tid = state["thread_id"]
    reply_prefix = list(state.get("reply") or [])
    if _tokens_today() > DAILY_TOKEN_CAP:
        case = cases.create_case(tid, "ai_failure")
        return {"reply": reply_prefix + [f"I can't help further in chat right now. {case['promise']} Your reference is "
                                         f"{case['case_id']}."], "handed_off": True}
    staffed = cases.staffed()
    sysmsg = system_prompt(_today_label(), staffed)
    sig = state.get("signals") or {}
    notes = []
    if sig.get("escalation"):
        notes.append(f"Policy signal in the customer's message: {sig['escalation']}. Follow the policy limits.")
    if sig.get("burning_ruled_out"):
        notes.append("Burning smell: the customer says no breaker tripped and no smoke, sparks or flames. You may offer "
                     "the earliest repair booking, marked urgent in the issue description.")
    if state.get("urgent_noticed") and state.get("route") == "agent":
        notes.append("The emergency number and urgent case were already given; you may help with a regular booking.")
    if notes:
        sysmsg += "\n\nNOTES FOR THIS TURN:\n- " + "\n- ".join(notes)
    msgs = _history(tid)
    client = _client()
    handed = dict(state)
    tool_failures = state.get("tool_failures", 0)
    final_text = ""
    handoff_info = None
    t0 = time.time()
    for _ in range(SETTINGS.max_tool_iterations):
        try:
            resp = client.messages.create(model=SETTINGS.llm_model, max_tokens=900, system=sysmsg, tools=TOOLS,
                                          messages=msgs)
        except anthropic.APIError as e:
            db.log_metric("model_error", 1, tid, {"error": str(e)[:200]})
            case = cases.create_case(tid, "ai_failure")
            return {"reply": reply_prefix + [f"Sorry, I'm having trouble right now. {case['promise']} Your reference is "
                                             f"{case['case_id']}."], "handed_off": True, "tool_failures": tool_failures + 1}
        _add_tokens(resp.usage.input_tokens + resp.usage.output_tokens)
        db.log_metric("tokens", resp.usage.input_tokens + resp.usage.output_tokens, tid)
        texts = [b.text for b in resp.content if b.type == "text"]
        uses = [b for b in resp.content if b.type == "tool_use"]
        if not uses:
            final_text = "\n".join(texts).strip()
            break
        msgs.append({"role": "assistant", "content": [b.model_dump() for b in resp.content]})
        results = []
        for u in uses:
            out = _run_tool(tid, u.name, u.input or {})
            if isinstance(out, dict) and (out.get("error") and out.get("error") != "not_verified"):
                tool_failures += 1
            if u.name == "request_handoff":
                handoff_info = out
                out = {"handed_off": True, "note": "The system adds the promise, reference and follow-up question "
                                                   "itself. Do not state any timing, reference or follow-up question."}
            results.append({"type": "tool_result", "tool_use_id": u.id, "content": json.dumps(out)[:6000]})
        msgs.append({"role": "user", "content": results})
    else:
        final_text = "I'm sorry, I couldn't finish that. Let me connect you with our team."
        handoff_info = cases.create_case(tid, "ai_failure")
    db.log_metric("agent_latency_s", round(time.time() - t0, 2), tid)
    if handoff_info and final_text:
        final_text = _strip_promises(final_text)
    reply = reply_prefix + ([final_text] if final_text else [])
    if handoff_info and not handoff_info.get("existing"):
        st = handoff_info.get("state") == "live_queued"
        reply.append(f"{handoff_info['promise']} Your reference is {handoff_info['case_id']}. " + _followup_ask(st))
        handed["handed_off"] = True
    return {"reply": reply, "tool_failures": tool_failures, "handed_off": handed.get("handed_off", False)}


_PROMISE_SENT = re.compile(r"[^.?!\n]*(business days?|reference|MHC-C-\d+|follow up by|email or (a )?phone|time window|"
                           r"call you back|get back to you|will (contact|reach out))[^.?!\n]*[.?!]?", re.I)


def _strip_promises(text: str) -> str:
    """Promises and references come from code only; drop any the model wrote itself."""
    out = _PROMISE_SENT.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def _run_tool(tid: str, name: str, args: dict):
    try:
        if name == "request_handoff":
            reason = args.get("reason", "out_of_scope")
            return cases.create_case(tid, reason, {"customer_needs": args.get("customer_needs", []),
                                                   "claims": args.get("claims", []),
                                                   "open_decision": args.get("open_decision")})
        if name == "set_followup":
            return cases.set_followup(tid, args.get("channel", "email"), args.get("destination"), args.get("window"))
        fn = getattr(tools, name, None)
        if fn is None:
            return {"error": f"unknown tool {name}"}
        return fn(tid, **args)
    except TypeError as e:
        return {"error": f"bad arguments: {e}"}
    except Exception as e:  # never crash the chat; the failure is logged and counted
        db.log_metric("tool_error", 1, tid, {"tool": name, "error": str(e)[:200]})
        return {"error": "tool_failed", "message": "That lookup failed. Offer a representative."}


def post(state: S) -> S:
    text = state["user_text"]
    reply = list(state.get("reply") or [])
    failed = state.get("failed_answers", 0) + (1 if reply and _FAILED.search(reply[-1]) else 0)
    corrected = bool(_CORRECTION.search(text))
    out: S = {"failed_answers": failed}
    if (not state.get("offered_person") and not state.get("handed_off")
            and (failed >= 2 or corrected or state.get("tool_failures", 0) >= 2)):
        reply.append("I'm sorry this isn't working. Would you like me to connect you with a representative?")
        out["offered_person"] = True
        db.log_metric("failure_offer", 1, state["thread_id"])
    out["reply"] = reply
    return out


def _route(state: S) -> str:
    return state["route"]


def build(checkpoint_path=None):
    g = StateGraph(S)
    for name, fn in [("guard", guard), ("safety", safety), ("burning_ask", burning_ask),
                     ("burning_cautious", burning_cautious), ("urgent", urgent), ("person", person),
                     ("human_held", human_held), ("agent", agent), ("post", post)]:
        g.add_node(name, fn)
    g.set_entry_point("guard")
    g.add_conditional_edges("guard", _route, {"safety": "safety", "burning_ask": "burning_ask",
                                              "burning_cautious": "burning_cautious", "urgent": "urgent",
                                              "person": "person", "human_held": "human_held", "agent": "agent"})
    g.add_edge("urgent", "agent")
    for n in ("safety", "burning_ask", "burning_cautious", "person", "human_held"):
        g.add_edge(n, END)
    g.add_edge("agent", "post")
    g.add_edge("post", END)
    path = checkpoint_path or SETTINGS.checkpoint_path
    saver = SqliteSaver(sqlite3.connect(str(path), check_same_thread=False))
    return g.compile(checkpointer=saver)


_GRAPH = None


def handle(thread_id: str, text: str) -> list[str]:
    """One customer turn: persist the message, run the graph, persist the reply."""
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build()
    cases.add_message(thread_id, "user", "customer", text)
    t0 = time.time()
    out = _GRAPH.invoke({"thread_id": thread_id, "user_text": text, "reply": [], "handed_off": False},
                        config={"configurable": {"thread_id": thread_id}, "recursion_limit": 25})
    replies = [r for r in out.get("reply", []) if r]
    for r in replies:
        cases.add_message(thread_id, "assistant", "ai", r)
    db.log_metric("turn_latency_s", round(time.time() - t0, 2), thread_id)
    db.log_metric("turn", 1, thread_id, {"route": out.get("route")})
    return replies


def reset_graph() -> None:
    global _GRAPH
    _GRAPH = None
