"""Generate docs/artifacts/2026-10-20-ux-planning.html (UX-1 visual review page).

Run: python3 gen_ux1.py <project_root> [--accept-changes]

READ BEFORE RE-RUNNING AFTER A SOURCE CHANGE. Tables and journeys are parsed from the three
Markdown sources at every build (ux1_sources.py), and each hand-drawn flowchart is checked against
its Mermaid. The rest is HAND-MAINTAINED: the sitemap and summary diagrams, the flows' "why"
paragraphs and numbered text equivalents, the story and gate prose. So the build keeps a snapshot of
each source as last built (snapshots/); if a source has changed, it prints the diff and stops.
Update the hand-written parts the diff touches, then re-run with --accept-changes. Re-stamping the
hashes without that diff review makes the page stale while it still passes check_review_page.py.
"""
import hashlib
import html
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ux1_sources as SRC  # noqa: E402

ROOT = Path(sys.argv[1])
ACCEPT = "--accept-changes" in sys.argv
SNAPDIR = Path(__file__).parent / "snapshots"
OUT = ROOT / "docs/artifacts/2026-10-20-ux-planning.html"
SOURCES = [
    "docs/ux/01-planning/USER_STORIES.md",
    "docs/ux/01-planning/USER_FLOWS.md",
    "docs/ux/01-planning/SITEMAP.md",
]
SRC.snapshot_guard(ROOT, SOURCES, SNAPDIR, ACCEPT)
TXT = {s: (ROOT / s).read_text() for s in SOURCES}
FLOWS_SRC = SRC.parse_flows(TXT[SOURCES[1]])
SHA = {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES}
E = html.escape


def wrap(t, n):
    return textwrap.wrap(t, n, break_long_words=False, break_on_hyphens=False) or [""]


def badge(s, label=None):
    names = {"fact": "Fact", "decision": "Your decision", "proposal": "Proposal",
             "unknown": "Unknown", "awaiting": "Awaiting you"}
    return f'<span class="st {s}">{label or names[s]}</span>'


# ---------------------------------------------------------------- flowchart renderer
CW, NW, PADX, PADY, GAP, LH = 200, 172, 20, 14, 52, 15
CH = {"step": 23, "dec": 19, "link": 22, "err": 23}


class Flow:
    def __init__(self, fid, nodes, edges, ncols, extra_right=0, extra_left=0):
        self.fid, self.nodes, self.edges = fid, nodes, edges
        self.ncols, self.er, self.el = ncols, extra_right, extra_left

    def layout(self):
        rows = {}
        for k, n in self.nodes.items():
            kind = n.get("k", "step")
            lines = wrap(n["t"], CH[kind])
            if kind == "err":
                lines = ["Error branch"] + lines
            h = len(lines) * LH + (26 if kind == "dec" else 16)
            n.update(lines=lines, h=h, kind=kind)
            rows[n["r"]] = max(rows.get(n["r"], 0), h)
        y, tops = PADY, {}
        for r in sorted(rows):
            tops[r] = y
            y += rows[r] + GAP
        self.H = y - GAP + PADY + 6
        self.W = self.el + PADX * 2 + self.ncols * CW + self.er
        for n in self.nodes.values():
            cx = self.el + PADX + n["c"] * CW + CW / 2
            top = tops[n["r"]] + (rows[n["r"]] - n["h"]) / 2
            n.update(cx=cx, x=cx - NW / 2, y=top, cy=top + n["h"] / 2,
                     right=cx + NW / 2, left=cx - NW / 2, bottom=top + n["h"])

    def route(self, e):
        a, b = self.nodes[e["a"]], self.nodes[e["b"]]
        mode = e.get("m", "auto")
        if mode == "bus":
            gy = a["bottom"] + 24
            return [(a["cx"], a["bottom"]), (a["cx"], gy), (b["cx"], gy), (b["cx"], b["y"])], None
        if mode == "elbow":
            side = b["left"] if b["cx"] > a["cx"] else b["right"]
            return [(a["cx"], a["bottom"]), (a["cx"], b["cy"]), (side, b["cy"])], 0
        if mode == "under":
            gy = max(a["bottom"], b["bottom"]) + 16
            bx = b["cx"] + e.get("bx", 0)
            return [(a["cx"], a["bottom"]), (a["cx"], gy), (bx, gy), (bx, b["bottom"])], 1
        if mode == "lane":
            side = e.get("side", "right")
            off = e.get("off", 14)
            if side == "right":
                lx = max(a["right"], b["right"]) + off
                return [(a["right"], a["cy"]), (lx, a["cy"]), (lx, b["cy"]), (b["right"], b["cy"])], 1
            lx = min(a["left"], b["left"]) - off
            return [(a["left"], a["cy"]), (lx, a["cy"]), (lx, b["cy"]), (b["left"], b["cy"])], 1
        if a["r"] == b["r"]:
            if b["c"] < a["c"]:
                return [(a["left"], a["cy"]), (b["right"], b["cy"])], 0
            return [(a["right"], a["cy"]), (b["left"], b["cy"])], 0
        if a["c"] == b["c"]:
            return [(a["cx"], a["bottom"]), (b["cx"], b["y"])], 0
        side = a["left"] if b["c"] < a["c"] else a["right"]
        return [(side, a["cy"]), (b["cx"], a["cy"]), (b["cx"], b["y"])], 0

    def svg(self, title, desc):
        self.layout()
        mid = f"ah-{self.fid.lower()}"
        o = [f'<svg viewBox="0 0 {self.W:.0f} {self.H:.0f}" role="img" aria-labelledby="{mid}-t {mid}-d" '
             f'style="max-width:{self.W:.0f}px;min-width:{min(self.W, 900):.0f}px">',
             f'<title id="{mid}-t">{E(title)}</title><desc id="{mid}-d">{E(desc)}</desc>',
             f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
             f'orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>']
        labels = []
        for e in self.edges:
            pts, lseg = self.route(e)
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            o.append(f'<path class="arrow" d="{d}" marker-end="url(#{mid})"/>')
            if e.get("l"):
                seg = e.get("seg", lseg if lseg is not None else 0)
                (x1, y1), (x2, y2) = pts[seg], pts[seg + 1]
                f = e.get("lp", 0.5)
                lx, ly = x1 + (x2 - x1) * f + e.get("dx", 0), y1 + (y2 - y1) * f + e.get("dy", 0)
                labels.append((lx, ly, wrap(e["l"], e.get("lw", 18))))
        for n in self.nodes.values():
            k = n["kind"]
            x, y, w, h = n["x"], n["y"], NW, n["h"]
            if k == "dec":
                p = 14
                o.append(f'<path class="fnode dec" d="M{x+p},{y} L{x+w-p},{y} L{x+w},{y+h/2} L{x+w-p},{y+h} '
                         f'L{x+p},{y+h} L{x},{y+h/2} Z"/>')
            elif k == "link":
                o.append(f'<rect class="fnode link" x="{x}" y="{y}" width="{w}" height="{h}" rx="{min(18, h/2)}"/>')
            elif k == "err":
                o.append(f'<rect class="fnode err" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
            else:
                o.append(f'<rect class="fnode" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
            ty = y + h / 2 - (len(n["lines"]) - 1) * LH / 2 + 4.5
            cls = {"link": "linktext", "dec": "strong"}.get(k, "")
            for i, line in enumerate(n["lines"]):
                c = "errtag" if (k == "err" and i == 0) else cls
                o.append(f'<text x="{n["cx"]:.1f}" y="{ty + i*LH:.1f}" text-anchor="middle" class="{c}">{E(line)}</text>')
        for lx, ly, lines in labels:
            w = max(len(s) for s in lines) * 6.3 + 10
            h = len(lines) * 13 + 6
            o.append(f'<rect class="lblbg" x="{lx-w/2:.1f}" y="{ly-h/2:.1f}" width="{w:.1f}" height="{h}" rx="4"/>')
            for i, s in enumerate(lines):
                o.append(f'<text class="elabel" x="{lx:.1f}" y="{ly - h/2 + 13 + i*13:.1f}" text-anchor="middle">{E(s)}</text>')
        o.append("</svg>")
        return "\n".join(o)


def N(t, c, r, k="step"):
    return {"t": t, "c": c, "r": r, "k": k}


# ---------------------------------------------------------------- the 12 flows (from USER_FLOWS.md)
FLOWS = []

FLOWS.append(dict(
    id="FLOW-1", title="Ask a question and get a sourced answer (or an honest “I don’t know”)",
    stories="US-1, US-6, US-7, US-17, US-26", hp="HP-1 (two-layer orchestration)",
    start="SCR-1 opened after the demo login (SCR-12)", end="SCR-1, answer shown with its source, or the person offer",
    cons=["CON-1", "CON-2"],
    why="Most customer questions are about fees, membership, hours and the service area. The help files hold old copies next to current ones (WP-1’s “stale twin”), a trap the brief asks us to catch. So every answer shows its source, and a missing source gets an honest “I don’t know”.",
    flow=Flow("FLOW-1", {
        "A": N("Open chat: greeting says automated assistant, demo date chip, staffing status", 1, 0),
        "B": N("Customer types a question", 1, 1),
        "G": N("Safety gate first, every turn", 1, 2, "dec"),
        "LIM": N("Plain limit message + Talk to a person", 3, 2, "err"),
        "S": N("FLOW-2", 0, 3, "link"),
        "P": N("Planner: just talk, or act?", 1, 3, "dec"),
        "R": N("Current source found?", 1, 4, "dec"),
        "V": N("FLOW-3 verify", 3, 4, "link"),
        "ANS": N("Answer with exact numbers and a source chip: file, section, version date", 0, 5),
        "IDK": N("I don’t have that information + Talk to a person", 2, 5),
        "F": N("Follow-up resolves against the open topic", 0, 6),
        "H": N("FLOW-7 if the customer accepts", 2, 6, "link"),
    }, [
        dict(a="A", b="B"), dict(a="B", b="G"),
        dict(a="B", b="LIM", l="rate limit or spend cap", lp=0.55),
        dict(a="G", b="S", l="safety words"), dict(a="G", b="P", l="clear"),
        dict(a="P", b="R", l="act: knowledge"), dict(a="P", b="V", l="private detail needed", lp=0.55),
        dict(a="R", b="ANS", l="yes"), dict(a="R", b="IDK", l="no"),
        dict(a="ANS", b="F"), dict(a="IDK", b="H"),
        dict(a="LIM", b="H", m="lane", side="right", off=16),
    ], 4, extra_right=24),
    words=["The chat opens: the greeting says it is an automated assistant, with a demo-date chip and the staffing status.",
           "The customer types a question.",
           "The safety gate runs first, every turn. Safety words send the turn to FLOW-2; a clear message goes on.",
           "The planner decides: just talk, or act. Acting on knowledge looks for a current source. If a private detail is needed, the customer goes to FLOW-3 to verify.",
           "Current source found: the answer gives exact numbers and a source chip (file, section, version date). A follow-up resolves against the open topic.",
           "No source: “I don’t have that information” plus Talk to a person; FLOW-7 if the customer accepts.",
           "Error branch: a rate limit or spend cap gives a plain limit message plus Talk to a person, then FLOW-7."],
))

FLOWS.append(dict(
    id="FLOW-2", title="Safety and danger interrupt (any turn)",
    stories="US-3, US-4, US-5", hp="HP-2 (rules first, a raise-only classifier)",
    note=("Why the contact offer waits (UX-2 finding R2-2, 2026-10-20)", "Meridian\u2019s policy says to leave \u201cimmediately\u201d and call \u201cfrom outside\u201d. The gas utility\u2019s own page says not to use a phone indoors. So the card is Meridian\u2019s instruction word for word, with no field, no question and no prompt. The optional offer (R-6, WP-5) is one line meant for after they are outside. This changes when the offer appears, not the requirement.", "USER_FLOWS.md, the paragraph after FLOW-2\u2019s step table; REFERENCES R2-2."),
    start="SCR-1, any message, including mid-booking", end="SCR-1, safety card pinned; P0 or P1 case written",
    cons=["CON-2"],
    why="A homeowner who smells gas must be told to leave before anything else. Word rules decide first; a small classifier may only raise the risk, never lower it. If the classifier fails, the rules still stand.",
    flow=Flow("FLOW-2", {
        "M": N("Customer message", 1, 0),
        "W": N("Word rules match?", 1, 1, "dec"),
        "SAFE": N("Safety card first: Meridian’s instruction, fixed text", 0, 2),
        "ASK": N("Ask: breakers already tripped? smoke, sparks, flames?", 1, 2),
        "CL": N("Classifier may only raise", 3, 2, "dec"),
        "OFFER": N("P0 case written by code. Below the card, one quiet line: once you are outside and safe, you can leave a number here. No field opened, no question asked, no follow-up time", 0, 3),
        "COND": N("Conditional instruction + emergency number + P1 case", 1, 3),
        "URG": N("Urgent booking + priority case: FLOW-5", 2, 3, "link"),
        "DANG": N("Someone in danger from no heat, cooling or a leak", 3, 3),
        "F1": N("Normal turn", 4, 3, "link"),
        "EM": N("Emergency number first, P1 case, separate 1-business-day line only if nobody is online", 3, 4),
    }, [
        dict(a="M", b="W"),
        dict(a="W", b="SAFE", l="gas, CO alarm, sparks, smoke, flames, burning + tripped breakers", lw=20, lp=0.5, dy=-4),
        dict(a="W", b="ASK", l="burning smell, no breaker info", lw=22),
        dict(a="W", b="CL", l="no match", lp=0.5),
        dict(a="ASK", b="SAFE", l="yes"),
        dict(a="ASK", b="COND", l="unclear"),
        dict(a="ASK", b="URG", l="both ruled out", lp=0.55),
        dict(a="CL", b="DANG", l="raised to danger"),
        dict(a="CL", b="F1", l="normal", lp=0.5),
        dict(a="SAFE", b="OFFER"), dict(a="DANG", b="EM"),
    ], 5),
    words=["A customer message arrives.",
           "Word rules check it first.",
           "Gas, CO alarm, sparks, smoke, flames, or burning with tripped breakers: the safety card comes first, with Meridian’s fixed instruction. Code writes a P0 case. Below the card sits one quiet line: once you are outside and safe, you can leave a number here. No field opens, no question is asked, and no follow-up time is given.",
           "Burning smell with no breaker information: the assistant asks whether breakers already tripped, or there is smoke, sparks or flames. Yes leads to the safety card. Unclear gives a conditional instruction, the emergency number and a P1 case. Both ruled out gives an urgent booking and a priority case (FLOW-5).",
           "No rule match: a classifier may only raise the risk. Raised to danger (someone in danger from no heat, cooling or a leak) gives the emergency number first, a P1 case, and a separate 1-business-day line only if nobody is online. Otherwise it is a normal turn.",
           "Error branch: if the classifier fails or times out, the rules’ result stands."],
))

FLOWS.append(dict(
    id="FLOW-3", title="Verify with a one-time code",
    stories="US-8, US-25", hp="HP-3 (actions with rules attached)",
    start="SCR-1, a question needing private data", end="SCR-1 verified for this customer and session, or a handoff that reveals nothing",
    cons=["CON-2", "CON-6"],
    why="A name is easy to guess, so it is not proof. The code goes to the phone or email on the account. In the demo, that phone is a labelled demo inbox the reviewer opens in a second tab.",
    flow=Flow("FLOW-3", {
        "Q": N("Private question: bill, appointment, membership dates", 1, 0),
        "L": N("Ask for name + phone, customer ID or invoice number", 1, 1),
        "F": N("Exactly one record found with a usable contact?", 1, 2, "dec"),
        "C": N("Code sent to the phone ending in 02: masked hint only", 1, 3),
        "IN": N("Reviewer opens the demo inbox in another tab and reads the code", 1, 4),
        "E": N("Customer types the code in chat", 1, 5),
        "K": N("Correct and not expired?", 1, 6, "dec"),
        "OK": N("Verified for this customer and session: FLOW-4", 1, 7, "link"),
        "NR": N("I can’t confirm your account here. A representative will help: FLOW-7", 2, 7, "err"),
        "RS": N("Offer: send a new code", 0, 7),
    }, [
        dict(a="Q", b="L"), dict(a="L", b="F"),
        dict(a="F", b="NR", l="no match, ambiguous, no contact", lw=16, seg=1, lp=0.3),
        dict(a="F", b="C", l="yes"), dict(a="C", b="IN"), dict(a="IN", b="E"), dict(a="E", b="K"),
        dict(a="K", b="OK", l="yes"),
        dict(a="K", b="E", l="wrong, attempts left", m="lane", side="left", off=70, lw=12),
        dict(a="K", b="RS", l="expired after 10 minutes, under the code cap", lw=14, seg=1, lp=0.5, dx=-6),
        dict(a="RS", b="C", m="lane", side="left", off=14),
        dict(a="K", b="NR", l="3 wrong, or expired with the cap reached", lw=16, seg=1, lp=0.5, dx=0),
    ], 3, extra_left=40),
    words=["A private question arrives: bill, appointment or membership dates.",
           "The assistant asks for name plus phone, customer ID or invoice number.",
           "If not exactly one record with a usable contact is found (no match, ambiguous, no contact): “I can’t confirm your account here. A representative will help” (FLOW-7). Nothing reveals whether an account exists.",
           "If one is found: a code is sent to “the phone ending in 02” (a masked hint only).",
           "The reviewer opens the demo inbox in another tab and reads the code. The customer types it in chat.",
           "Correct and not expired: verified for this customer and session (FLOW-4). Wrong with attempts left: type again. Expired after 10 minutes while under the per-conversation code cap: the assistant offers to send a new code, and the attempts start again (a proposal; the cap is set at the design stage). Three wrong, or expired with the cap already reached: the same handoff."],
))

FLOWS.append(dict(
    id="FLOW-4", title="Account answers after the code (invoice, membership, warranty)",
    stories="US-9, US-16", hp="HP-3",
    start="SCR-1 verified", end="SCR-1 answer shown, or FLOW-7 when the customer disputes or asks for an action the systems can’t do",
    cons=["CON-2"],
    why="After the code, the assistant can read the account out loud in plain numbers. It never judges whether a bill is right, and it never says it did something it can’t do.",
    flow=Flow("FLOW-4", {
        "V": N("Verified", 1, 0),
        "T": N("What is asked?", 1, 1, "dec"),
        "I": N("Each line as billed: $89, $245, $144; fee types sourced to the 2026 schedule", 0, 2),
        "MB": N("Tier and renewal date", 2, 2),
        "WA": N("Install date, 2-year labor; 5 years if a member at install: a representative can confirm", 3, 2),
        "D": N("Dispute, refund or waiver asked?", 0, 3, "dec"),
        "X": N("Cancel, upgrade, autopay, payment?", 2, 3, "dec"),
        "DONE": N("Answered", 0, 4),
        "H": N("No verdict, no promise about the bill: FLOW-7", 1, 4, "link"),
        "NA": N("Never claims it was done; explains a person must do it: FLOW-7", 2, 4, "link"),
    }, [
        dict(a="V", b="T"),
        dict(a="T", b="I", l="invoice"),
        dict(a="T", b="MB", l="membership", lp=0.45),
        dict(a="T", b="WA", l="warranty", lp=0.88),
        dict(a="I", b="D"), dict(a="D", b="DONE", l="no"),
        dict(a="D", b="H", l="yes", lp=0.5),
        dict(a="MB", b="X"), dict(a="X", b="NA", l="yes"),
    ], 4),
    words=["The customer is verified. What is asked?",
           "Invoice: each line as billed ($89, $245, $144), with fee types sourced to the 2026 schedule. If a dispute, refund or waiver is asked: no verdict and no promise about the bill (FLOW-7). If not: answered.",
           "Membership: tier and renewal date. A cancel, upgrade, autopay or payment request is never claimed as done; the assistant explains a person must do it (FLOW-7).",
           "Warranty: install date and 2-year labor; 5 years if a member at install, which a representative can confirm."],
))

FLOWS.append(dict(
    id="FLOW-5", title="Book a repair, tune-up or estimate",
    note=("Why the code comes after the windows (UX-2 finding R1-1, 2026-10-20)",
          "A real Austin HVAC booking widget asked for name, phone and email before showing any time. Showing the arrival windows and the standard fee first costs nothing private: the zone comes from a ZIP or city the customer types. A booking is an account change, so the code still comes before the write (R-15; consolidated \u00a78 step 2). The member fee and member-reserved windows need the verified record, so they appear after the code.",
          "USER_FLOWS.md, the paragraph after FLOW-5\u2019s step table; REFERENCES R1-1."),
    why="Booking is where the AI changes real data. First the customer sees open windows and the standard fee for their ZIP or city, and nothing private is asked. The code comes just before the booking is written. Then the member fee applies if they are a member. The slot is checked again at the moment of writing, so two people can never get the same window.",
    flow=Flow("FLOW-5", {
        "N": N("Need described", 1, 0),
        "QC": N("Non-urgent repair?", 1, 1, "dec"),
        "CHK": N("Offer quick checks: very optional, one tap to skip", 1, 2),
        "F2": N("FLOW-2", 2.3, 3, "link"),
        "UQ": N("No heat, cooling or leak? Two skippable urgency questions", 1, 3),
        "WH": N("Where is the visit? ZIP or city", 1, 4),
        "Z": N("Address in a served zone?", 1, 5, "dec"),
        "SL": N("Slot cards: open arrival windows in the zone, standard fee shown; estimate slots for replacements", 1, 6),
        "OUT": N("Honest no + Talk to a person", 2, 6, "err"),
        "NONE": N("Nearest alternatives, or a person", 0, 7),
        "PICK": N("Customer taps a window, or says \u2018what about Monday?\u2019", 1, 7),
        "ID": N("Verify before writing: FLOW-3, the code to the contact on record", 1, 8, "link"),
        "MEM": N("Member fee applies; member-reserved windows offered too", 0, 9),
        "NOID": N("No booking; FLOW-7 without revealing whether an account exists", 2, 9, "err"),
        "W": N("Still open at write time?", 1, 10, "dec"),
        "CONF": N("Confirmation card: date, window, technician, fee for this tier", 1, 11),
        "ALT": N("Sorry, that window just went: here are the next ones", 2, 11, "err"),
    }, [
        dict(a="N", b="QC"), dict(a="QC", b="CHK", l="yes"),
        dict(a="QC", b="F2", l="urgent or safety", seg=0, lp=0.55),
        dict(a="CHK", b="UQ"), dict(a="UQ", b="F2", l="someone in danger", lw=10),
        dict(a="UQ", b="WH", l="no danger or skipped"),
        dict(a="WH", b="Z"),
        dict(a="Z", b="OUT", l="no, e.g. Lakeway west of 620", lw=16, seg=0, lp=0.55),
        dict(a="Z", b="SL", l="yes"),
        dict(a="SL", b="NONE", l="none fit"),
        dict(a="SL", b="PICK"), dict(a="PICK", b="ID"),
        dict(a="ID", b="MEM", l="verified member", lw=10),
        dict(a="ID", b="NOID", l="no match or failed code", lw=12),
        dict(a="ID", b="W", l="verified"),
        dict(a="MEM", b="W", m="elbow"),
        dict(a="W", b="CONF", l="yes"),
        dict(a="W", b="ALT", l="taken meanwhile", lp=0.55),
        dict(a="ALT", b="PICK", m="lane", side="right", off=40),
    ], 3, extra_right=50),
    words=["The customer describes the need. Is it a non-urgent repair? Urgent or safety: FLOW-2.",
           "Non-urgent: offer quick checks (very optional, one tap to skip), then two skippable urgency questions for no heat, cooling or a leak. Someone in danger: FLOW-2.",
           "No danger, or skipped: \u201cWhere is the visit?\u201d The customer gives a ZIP or city. Is it in a served zone? No (for example Lakeway west of 620): an honest no plus Talk to a person.",
           "Yes: slot cards show open arrival windows in the zone, with the standard fee; estimate slots for replacements. If none fit: nearest alternatives, or a person.",
           "The customer taps a window, or says \u201cwhat about Monday?\u201d. Before anything is written, they verify with the code sent to the contact on record (FLOW-3).",
           "Verified member: the member fee applies, and member-reserved windows are offered too. Verified: go on. No match or a failed code: no booking, and a handoff (FLOW-7) that never reveals whether an account exists.",
           "Is the window still open at write time? Yes: the confirmation card (date, window, technician, fee for this tier). Taken meanwhile: \u201cSorry, that window just went: here are the next ones\u201d, and the customer picks again."],
))

FLOWS.append(dict(
    id="FLOW-6", title="Change an appointment: reschedule, confirm, cancel",
    stories="US-12, US-13", hp="HP-3 (no fee-bearing change by the AI)",
    start="SCR-1, verified, “can I move my Saturday visit?”", end="SCR-1 new confirmation, or a staff change request with “your original appointment stays”",
    cons=["CON-2"],
    why="A move or cancel inside 24 hours carries a $49 fee. You chose at Stage 3 that the AI never makes that change. It explains the fee, records the request, and says the original visit stays until a person acts.",
    flow=Flow("FLOW-6", {
        "R": N("Change asked", 1, 0),
        "V": N("Verify: FLOW-3", 1, 1, "link"),
        "K": N("Which change?", 1, 2, "dec"),
        "CF": N("Shows the booked date, window, technician", 0, 3),
        "H": N("More than 24 hours before the window?", 1, 3, "dec"),
        "SL": N("Slot cards, customer picks: moved under the booking rules", 2, 4),
        "CX": N("Cancelled, no fee", 3, 4),
        "FEE": N("The $49 fee applies under current policy. The assistant never moves or cancels it", 1, 4),
        "REQ": N("Records the wanted time, slots shown but not held, reason", 1, 5),
        "STAY": N("Your original appointment stays until a representative confirms", 1, 6),
        "HO": N("FLOW-7: P2 case, due at the window start; can’t-guarantee line if needed", 1, 7, "link"),
    }, [
        dict(a="R", b="V"), dict(a="V", b="K"),
        dict(a="K", b="CF", l="confirm"),
        dict(a="K", b="H", l="move or cancel"),
        dict(a="H", b="SL", l="yes, move", lp=0.3),
        dict(a="H", b="CX", l="yes, cancel", lp=0.85),
        dict(a="H", b="FEE", l="no: the $49 fee applies", lw=14),
        dict(a="FEE", b="REQ"), dict(a="REQ", b="STAY"), dict(a="STAY", b="HO"),
    ], 4),
    words=["A change is asked. The customer verifies (FLOW-3). Which change?",
           "Confirm: the assistant shows the booked date, window and technician.",
           "Move or cancel more than 24 hours before the window: a move uses slot cards and the booking rules; a cancel goes through with no fee.",
           "Inside 24 hours: “The $49 fee applies under current policy.” The assistant never moves or cancels it. It records the wanted time, the slots shown (not held) and the reason.",
           "It says “Your original appointment stays until a representative confirms”, then hands off (FLOW-7): a P2 case, due at the window start, with a can’t-guarantee line if needed."],
))

FLOWS.append(dict(
    id="FLOW-7", title="Handoff when nobody is online (the default)",
    stories="US-2, US-14, US-16", hp="HP-4 (honest handoff, brief with no invented facts)",
    start="SCR-1, “Talk to a person”, a policy trigger, a failure signal or an unsupported action",
    end="SCR-1 handoff card (reference, promise, follow-up choice); case Unassigned on SCR-5",
    cons=["CON-4", "CON-2", "CON-5"],
    why="Meridian has no staff online in the demo. So the honest default is a written promise from the policy table, a reference number, and the customer’s choice of how to be contacted. Nothing says a message was sent.",
    flow=Flow("FLOW-7", {
        "T": N("Trigger: button, words, policy, failure, unsupported action, fee-bearing change", 1, 0),
        "P": N("Staffing state", 1, 1, "dec"),
        "CASE": N("Case created; priority and promise from the policy table", 1, 2),
        "F8": N("FLOW-8", 2, 2, "link"),
        "CARD": N("Handoff card: No representative is online right now. A representative will get back to you within 1 business day, by Mon Oct 19, 7:00 pm. Reference MHC-C-0007", 1, 3),
        "FU": N("We’ll follow up by email unless you’d prefer a phone call: channel, on-record destination, time window", 1, 4),
        "KEEP": N("Card stays at the top of the chat; customer may keep asking other questions", 1, 5),
    }, [
        dict(a="T", b="P"),
        dict(a="P", b="CASE", l="nobody online, default"),
        dict(a="P", b="F8", l="simulated staff on shift", lw=14, seg=1, lp=0.5),
        dict(a="CASE", b="CARD"), dict(a="CARD", b="FU"), dict(a="FU", b="KEEP"),
    ], 3),
    words=["A trigger arrives: the button, the words, a policy, a failure, an unsupported action or a fee-bearing change.",
           "Staffing state: if simulated staff are on shift, FLOW-8.",
           "Nobody online (the default): a case is created, with priority and promise from the policy table.",
           "The handoff card says: “No representative is online right now. A representative will get back to you within 1 business day, by Mon Oct 19, 7:00 pm. Reference MHC-C-0007.”",
           "“We’ll follow up by email unless you’d prefer a phone call”: channel, on-record destination, time window.",
           "The card stays at the top of the chat; the customer may keep asking other questions."],
))

FLOWS.append(dict(
    id="FLOW-8", title="Live handoff when staff are on shift (simulated), and same-chat takeover",
    stories="US-15, US-20, US-25", hp="HP-4",
    start="SCR-3, reviewer turns on “Demo: simulate staff on shift”; SCR-1 customer asks for a person",
    end="SCR-1 back with the assistant or closed; case Resolved or In progress",
    cons=["CON-7", "CON-4", "CON-10", "CON-11", "CON-13", "CON-14", "CON-3"],
    why="The brief wants the grader to “watch the agent escalate”. With one click on the role switch (or two tabs), the reviewer plays the customer and Riley, the demo representative, and sees one conversation pass from the AI to a person and back.",
    flow=Flow("FLOW-8", {
        "STON": N("Reviewer turns on simulated staffing: banner on chat and console", 1, 0),
        "ASK": N("Customer asks for a person", 1, 1),
        "Q": N("Live-queued: A representative will join this chat when available", 1, 2),
        "ASYNC": N("Same 1-business-day promise and reference as FLOW-7; supervisor alert", 2, 3, "err"),
        "CONS": N("Reviewer, second tab: staff console, queue shows the case on top", 1, 3),
        "CL": N("Claim and join", 1, 4),
        "J": N("Customer sees: Riley, demo representative, has joined. AI paused", 1, 5),
        "CHAT": N("Riley and the customer talk in the same chat", 1, 6),
        "CH": N("Riley chooses", 1, 7, "dec"),
        "AI": N("Customer sees the assistant is back", 0, 8),
        "CLOSED": N("Chat closed, outcome recorded", 2, 8),
    }, [
        dict(a="STON", b="ASK"), dict(a="ASK", b="Q"), dict(a="Q", b="CONS"),
        dict(a="Q", b="ASYNC", l="shift ends before a claim", lw=14, seg=1, lp=0.45),
        dict(a="CONS", b="CL"), dict(a="CL", b="J"), dict(a="J", b="CHAT"), dict(a="CHAT", b="CH"),
        dict(a="CH", b="AI", l="hand back"), dict(a="CH", b="CLOSED", l="close"),
    ], 3),
    words=["The reviewer turns on simulated staffing; a banner shows on chat and console.",
           "The customer asks for a person and is live-queued: “A representative will join this chat when available.”",
           "Error branch: if the shift ends before a claim, the customer gets the same 1-business-day promise and reference as FLOW-7, and the supervisor gets an alert.",
           "In a second tab, the reviewer opens the staff console; the queue shows the case on top. Claim and join.",
           "The customer sees “Riley, demo representative, has joined”; the AI is paused. Riley and the customer talk in the same chat.",
           "Riley chooses: hand back (the customer sees the assistant is back) or close (chat closed, outcome recorded)."],
))

FLOWS.append(dict(
    id="FLOW-9", title="Representative works a case after the chat (async)",
    stories="US-18, US-19, US-21", hp="HP-4",
    start="SCR-4 switch role to representative → SCR-5 queue", end="SCR-6 case Resolved or Closed unresolved; promise Kept or Missed",
    cons=["CON-10", "CON-11", "CON-12", "CON-13", "CON-15", "CON-16"],
    why="The promise made in the chat only counts if a person keeps it. The representative needs the brief, the sources and the chat in one place, and every contact is labelled “recorded, not sent” because no message really leaves the demo.",
    flow=Flow("FLOW-9", {
        "S": N("Switch to the representative role", 1, 0),
        "Q": N("Queue: P0 and P1 first, then due time, overdue first", 1, 1),
        "O": N("Open case", 1, 2),
        "B": N("Read the eight-heading brief: facts and claims apart; promise with follow-up preference beside it", 1, 3),
        "FL": N("Flag: goes to the review list", 2, 4),
        "SRC": N("Open a fact’s source: snapshot the AI saw vs current value, changed-since marker", 1, 4),
        "CL": N("Claim", 1, 5),
        "ACT": N("Next action", 1, 6, "dec"),
        "WT": N("Waiting, with a required wake-up time", 0, 7),
        "LOG": N("Log a call or email: Demo, recorded, not sent", 1, 7),
        "REL": N("Release with a reason", 2, 7),
        "OUT": N("Resolve with an outcome, or close unresolved with a reason", 1, 8),
    }, [
        dict(a="S", b="Q"), dict(a="Q", b="O"), dict(a="O", b="B"), dict(a="B", b="SRC"),
        dict(a="B", b="FL", l="brief wrong or missing something", lw=14, seg=1, lp=0.5),
        dict(a="SRC", b="CL"), dict(a="CL", b="ACT"),
        dict(a="ACT", b="LOG", l="contact"), dict(a="ACT", b="WT", l="blocked"),
        dict(a="ACT", b="REL", l="not mine"), dict(a="LOG", b="OUT"),
    ], 3),
    words=["The representative signs in. The queue shows P0 and P1 first, then due time, overdue first.",
           "They open a case and read the eight-heading brief: facts and claims kept apart; the promise with the follow-up preference beside it.",
           "If the brief is wrong or missing something: flag it; the flag goes to the review list.",
           "They open a fact’s source: the snapshot the AI saw versus the current value, with a changed-since marker. Then claim.",
           "Next action: contact (log a call or email, “Demo, recorded, not sent”), blocked (waiting, with a required wake-up time), or not mine (release with a reason).",
           "Resolve with an outcome, or close unresolved with a reason."],
))

FLOWS.append(dict(
    id="FLOW-10", title="Supervisor oversight and the demo clock",
    stories="US-22, US-23", hp="HP-4",
    start="SCR-4 switch role to supervisor → SCR-7", end="SCR-7 every P0/P1 and overdue case owned; flags reviewed on SCR-8",
    cons=["CON-17", "CON-13", "CON-8", "CON-7", "CON-16", "CON-12"],
    why="A promise with nobody watching it gets missed. The supervisor sees what is urgent, unowned or late. In the demo, a clock button moves time forward so the grader can watch a case turn overdue.",
    flow=Flow("FLOW-10", {
        "S": N("Switch to the supervisor role", 2, 0),
        "OV": N("Oversight: P0 and P1, unowned, due soon, overdue, stuck waiting", 2, 1),
        "AS": N("Assign or reassign with a reason", 0, 2),
        "PR": N("Change priority with a reason", 1, 2),
        "TIME": N("Advance simulated time: a seeded case turns overdue", 2, 2),
        "SHIFT": N("Start or end the simulated shift", 3, 2),
        "FL": N("Review list of flags", 4, 2),
        "CASE": N("Open the case behind a flag", 4, 3),
    }, [
        dict(a="S", b="OV"),
        dict(a="OV", b="AS", m="bus"), dict(a="OV", b="PR", m="bus"), dict(a="OV", b="TIME", m="bus"),
        dict(a="OV", b="SHIFT", m="bus"), dict(a="OV", b="FL", m="bus"),
        dict(a="FL", b="CASE"),
    ], 5),
    words=["The reviewer, already signed in, switches to the supervisor role and sees oversight: P0 and P1, unowned, due soon, overdue, stuck waiting.",
           "From there: assign or reassign with a reason; change priority with a reason; advance simulated time (a seeded case turns overdue); start or end the simulated shift; review the list of flags.",
           "From a flag, open the case behind it."],
))

FLOWS.append(dict(
    id="FLOW-11", title="Business owner and reviewer read outcomes, health and the evaluation",
    stories="US-24, US-27", hp="none",
    start="SCR-4 switch role to owner (or the reviewer, already signed in)", end="SCR-9 / SCR-10 / SCR-11, any number opened down to its cases or its run",
    cons=["CON-18", "CON-19", "CON-20"],
    why="AEA judges the project on containment, accuracy and monitoring. Every number here shows what it was divided by, and opens down to the cases or the test run behind it, so nobody has to take it on trust.",
    flow=Flow("FLOW-11", {
        "S": N("Switch to the business-owner role", 1, 0),
        "OW": N("Outcomes: in-scope correct resolution, promises kept, outcomes with denominators, handoffs by reason", 0, 1),
        "MON": N("Monitoring: volume, containment, escalations, failures, latency p50 and p95, spend against the daily cap, alerts on the page, last health-check restart", 1, 1),
        "EV": N("Evaluation report: test-set mix, retrieval hit rate, accuracy, escalation recall, false escalation, wrong answers, gates", 2, 1),
        "CS": N("Open the cases behind a number: SCR-6", 0, 2),
        "RUN": N("Each number names its run, date, denominator and split: the headline from the sealed held-out split, dev numbers labelled dev", 2, 2),
    }, [
        dict(a="S", b="OW", m="bus"), dict(a="S", b="MON", m="bus"), dict(a="S", b="EV", m="bus"),
        dict(a="OW", b="CS"), dict(a="EV", b="RUN"),
    ], 3),
    words=["The business owner role is picked with the role switch. (Monitoring and evaluation open in any role once signed in with the demo login.)",
           "Outcomes: in-scope correct resolution, promises kept, outcomes with denominators, handoffs by reason. Any number opens the cases behind it (SCR-6).",
           "Monitoring: volume, containment, escalations, failures, latency p50 and p95, spend against the daily cap, alerts on the page (no push channel), and when the health check last restarted the service. No traces: they stay in Langfuse on the VPS.",
           "Evaluation report: test-set mix, retrieval hit rate, accuracy, escalation recall, false escalation, wrong answers, gates. Each number names its run, date, denominator and split: the headline comes from the sealed held-out split; dev-split numbers are labelled dev."],
))

FLOWS.append(dict(
    id="FLOW-12", title="Reviewer signs in, sets up and resets the demo",
    stories="US-25, US-26, US-28", hp="HP-4 (never imply real staffing)",
    start="the deployment URL → SCR-12 demo login", end="SCR-1 and SCR-5 open side by side (the chat ignores the role, so a customer tab keeps working while another tab is staff); demo restorable",
    cons=["CON-1", "CON-7", "CON-9", "CON-10", "CON-22"],
    why="The grader arrives cold, and nothing answers until they sign in once with the demo login from the README. After that, one guide page says what is real and what is simulated, and a role switch in every header lets them play customer and staff without second accounts. A reset puts everything back to Fri Oct 16 so the demo can run again.",
    flow=Flow("FLOW-12", {
        "U": N("Deployment URL", 1.5, 0),
        "LG": N("SCR-12 demo login: username and password from the README", 1.5, 1),
        "LE": N("One message for every cause: That username or password didn\u2019t work", 3, 1, "err"),
        "C": N("SCR-1 chat as the customer, with a thin demo bar: demo date, nobody online, Demo guide", 1.5, 2),
        "G": N("SCR-3 demo guide: what is simulated, how to play staff, links", 1.5, 3),
        "IN": N("Open the demo inbox: SCR-2", 0, 4),
        "ST": N("Switch to a staff role in the header: SCR-4", 1, 4),
        "TG": N("Toggle simulated staffing", 2, 4),
        "RS": N("Reset the demo: working DB copy, cases, clock back to Fri Oct 16", 3, 4),
    }, [
        dict(a="U", b="LG"),
        dict(a="LG", b="LE", l="wrong login", lw=8),
        dict(a="LE", b="LG", m="under", bx=40),
        dict(a="LG", b="C"), dict(a="C", b="G"),
        dict(a="C", b="LG", l="session expired", lw=9, m="lane", side="left", off=24, seg=1, lp=0.5),
        dict(a="G", b="IN", m="bus"), dict(a="G", b="ST", m="bus"), dict(a="G", b="TG", m="bus"), dict(a="G", b="RS", m="bus"),
    ], 4),
    words=["The reviewer opens the deployment URL. Nothing answers except the login and the health check.",
           "SCR-12, the demo login: one username and password, given in the README. A wrong login gets one message for every cause, and the login screen shows again.",
           "On success the reviewer lands on SCR-1, the chat, as the customer, with a thin demo bar: demo date, nobody online, Demo guide. If the session ends later, any screen sends the reviewer back to the login.",
           "SCR-3, the demo guide, says what is simulated and how to play staff, with links.",
           "From the guide: open the demo inbox (SCR-2); switch to a staff role in the header (SCR-4, one click, no second password); toggle simulated staffing; reset the demo (working DB copy, cases, clock back to Fri Oct 16; the login and role stay).",
           "Error branch: a reset while a live chat is open ends that chat with a notice."],
))

# ---------------------------------------------------------------- journeys (from USER_FLOWS.md mermaid)
JOURNEYS = SRC.parse_journeys(TXT[SOURCES[1]])
assert len(JOURNEYS) == 7, len(JOURNEYS)


def journey_svg(i, title, sections):
    SW, G, L = 128, 10, 54
    steps = [(s, t, sc, a) for s, items in sections for (t, sc, a) in items]
    W = L + len(steps) * (SW + G) + 10
    top, step_y = 44, 22
    chart_bot = top + 4 * step_y
    box_y = chart_bot + 26
    box_lines = [wrap(t, 16) for _, t, _, _ in steps]
    bh = max(len(x) for x in box_lines) * 15 + 16
    act_lines = [wrap(a, 20) for *_, a in steps]
    H = box_y + bh + max(len(x) for x in act_lines) * 14 + 14
    jid = f"jr{i}"
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="{jid}-t {jid}-d" style="max-width:{W}px;min-width:{min(W, 900)}px">',
         f'<title id="{jid}-t">Journey {i}: {E(title)}</title>',
         f'<desc id="{jid}-d">{len(steps)} steps in {len(sections)} sections; the line above the steps shows the feeling we aim for at each step, from 1 (bad) to 5 (good). The numbered list below the diagram says the same.</desc>']
    # sections band
    x = L
    for s, items in sections:
        w = len(items) * (SW + G) - G
        o.append(f'<rect class="secband" x="{x}" y="6" width="{w}" height="24" rx="5"/>')
        o.append(f'<text x="{x + 8}" y="23" class="strong">{E(s)}</text>')
        x += w + G
    # axis
    for v in range(1, 6):
        y = top + (5 - v) * step_y
        o.append(f'<line class="grid" x1="{L - 6}" y1="{y}" x2="{W - 10}" y2="{y}"/>')
        lab = {5: "5 good", 1: "1 bad"}.get(v, str(v))
        o.append(f'<text x="{L - 10}" y="{y + 4}" text-anchor="end" class="small">{lab}</text>')
    pts = []
    for k, (_, t, sc, a) in enumerate(steps):
        cx = L + k * (SW + G) + SW / 2
        pts.append((cx, top + (5 - sc) * step_y))
    o.append('<polyline class="aimline" points="' + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + '"/>')
    for k, (cx, cy) in enumerate(pts):
        sc = steps[k][2]
        o.append(f'<circle class="aimdot" cx="{cx:.0f}" cy="{cy:.0f}" r="10"/>')
        o.append(f'<text x="{cx:.0f}" y="{cy + 4:.0f}" text-anchor="middle" class="dotnum">{sc}</text>')
    for k, (_, t, sc, a) in enumerate(steps):
        bx = L + k * (SW + G)
        o.append(f'<rect class="fnode" x="{bx}" y="{box_y}" width="{SW}" height="{bh}" rx="6"/>')
        for j, line in enumerate(box_lines[k]):
            o.append(f'<text x="{bx + 8}" y="{box_y + 19 + j * 15}">{E(line)}</text>')
        for j, line in enumerate(act_lines[k]):
            o.append(f'<text x="{bx + 4}" y="{box_y + bh + 15 + j * 14}" class="small">{E(line)}</text>')
    o.append("</svg>")
    words = "".join(f"<li>{E(s)}: {E(t)}. <span class=\"aim\">(aim {sc}; {E(a.lower())})</span></li>"
                    for s, t, sc, a in steps)
    return "\n".join(o), words, len(steps)


# ---------------------------------------------------------------- sitemap svg
def sitemap_svg():
    # Hand-drawn from SITEMAP.md's Mermaid (five groups, 19 edges). Re-check it by eye when SITEMAP.md changes.
    B = {  # x, y, w, h, label lines
        "S1": (40, 70, 180, 56, ["SCR-1", "Chat"]),
        "S3": (40, 250, 180, 56, ["SCR-3", "Demo guide and controls"]),
        "S2": (40, 400, 180, 56, ["SCR-2", "Demo delivery inbox"]),
        "S4": (318, 166, 176, 56, ["SCR-4", "Role switch, every header"]),
        "S5": (548, 70, 186, 56, ["SCR-5", "Representative queue"]),
        "S7": (548, 166, 186, 56, ["SCR-7", "Supervisor oversight"]),
        "S9": (548, 262, 186, 56, ["SCR-9", "Business-owner outcomes"]),
        "S6": (800, 70, 196, 56, ["SCR-6", "Case view"]),
        "S8": (800, 166, 196, 56, ["SCR-8", "Review list of flags"]),
        "S10": (590, 436, 186, 56, ["SCR-10", "Monitoring"]),
        "S11": (800, 436, 196, 56, ["SCR-11", "Evaluation report"]),
    }
    DY = 96  # everything but the login group is drawn 96 px lower to make room for SCR-12 on top
    B = {k: (x, y + DY, w, h, t) for k, (x, y, w, h, t) in B.items()}
    S12 = (40, 36, 180, 56, ["SCR-12", "Demo login"])

    def c(k):
        x, y, w, h, _ = B[k]
        return dict(l=x, r=x + w, t=y, b=y + h, cx=x + w / 2, cy=y + h / 2)

    o = ['<svg viewBox="0 0 1030 690" role="img" aria-labelledby="sm-t sm-d" style="max-width:1030px;min-width:900px">',
         '<title id="sm-t">Sitemap: one demo login, three surfaces and two report pages, twelve screens</title>',
         '<desc id="sm-d">The demo login SCR-12 gates everything and leads to the customer chat SCR-1. The chat links to the demo guide SCR-3, and its code hint points to the demo inbox SCR-2. The demo guide links to the inbox, the role switch SCR-4 and the two reports, monitoring SCR-10 and evaluation SCR-11. The role switch, which sits in every header, leads back to the chat and on to the queue, oversight and owner outcomes; these lead to the case view and the flag list. Owner outcomes also link to both reports.</desc>',
         '<defs><marker id="ahs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>',
         '<rect class="surf pub" x="16" y="14" width="228" height="88" rx="10"/><text x="44" y="30" class="strong">Demo login: gates everything</text>',
         '<rect class="surf pub" x="16" y="118" width="228" height="136" rx="10"/><text x="44" y="142" class="strong">Customer chat</text>',
         '<rect class="surf demo" x="16" y="292" width="228" height="300" rx="10"/><text x="44" y="580" class="strong">Demo tools: labelled simulation</text>',
         '<rect class="surf staff" x="290" y="118" width="724" height="320" rx="10"/><text x="304" y="142" class="strong">Staff console</text>',
         '<rect class="surf ro" x="570" y="480" width="444" height="128" rx="10"/><text x="584" y="504" class="strong">Read-only reports: behind the demo login</text>',
         ]

    def arrow(pts, dash=False, label=None, lpos=None):
        d = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts)
        o.append(f'<path class="arrow{" dash" if dash else ""}" d="{d}" marker-end="url(#ahs)"/>')
        if label:
            lx, ly = lpos
            w = len(label) * 6.3 + 10
            o.append(f'<rect class="lblbg" x="{lx - w/2:.0f}" y="{ly - 10}" width="{w:.0f}" height="18" rx="4"/>')
            o.append(f'<text class="elabel" x="{lx:.0f}" y="{ly + 3}" text-anchor="middle">{E(label)}</text>')

    x12, y12, w12, h12, l12 = S12
    o.append(f'<rect class="fnode scr" x="{x12}" y="{y12}" width="{w12}" height="{h12}" rx="7"/>')
    o.append(f'<text x="{x12 + 10}" y="{y12 + 22}" class="strong">{E(l12[0])}</text><text x="{x12 + 10}" y="{y12 + 41}">{E(l12[1])}</text>')
    s1, s2, s3, s4 = c("S1"), c("S2"), c("S3"), c("S4")
    arrow([(200, y12 + h12), (200, s1["t"])])
    arrow([(s4["l"], s4["cy"] - 14), (250, s4["cy"] - 14), (250, s1["cy"]), (s1["r"], s1["cy"])])
    s5, s6, s7, s8, s9, s10, s11 = (c(k) for k in ("S5", "S6", "S7", "S8", "S9", "S10", "S11"))
    arrow([(s1["cx"] + 40, s1["b"]), (s1["cx"] + 40, s3["t"])], label="demo bar", lpos=(s1["cx"] + 40, 272))
    arrow([(s3["cx"] + 30, s3["b"]), (s3["cx"] + 30, s2["t"])])
    arrow([(s1["l"], s1["cy"]), (28, s1["cy"]), (28, s2["cy"]), (s2["l"], s2["cy"])], dash=True,
          label="code hint", lpos=(78, 452))
    arrow([(s3["r"], s3["cy"] - 6), (268, s3["cy"] - 6), (268, s4["cy"]), (s4["l"], s4["cy"])])
    # demo guide -> both read-only reports, along the bottom
    arrow([(s3["r"], s3["cy"] + 10), (282, s3["cy"] + 10), (282, 656), (s10["cx"], 656), (s10["cx"], s10["b"])], dash=True,
          label="guide links", lpos=(420, 656))
    arrow([(s10["cx"], 656), (s11["cx"], 656), (s11["cx"], s11["b"])], dash=True)
    # role switch fans out
    arrow([(s4["r"], s4["cy"] - 10), (522, s4["cy"] - 10), (522, s5["cy"]), (s5["l"], s5["cy"])])
    arrow([(s4["r"], s4["cy"]), (s7["l"], s7["cy"])])
    arrow([(s4["r"], s4["cy"] + 10), (522, s4["cy"] + 10), (522, s9["cy"]), (s9["l"], s9["cy"])])
    # to the case view and the flag list
    arrow([(s5["r"], s5["cy"]), (s6["l"], s6["cy"])])
    arrow([(s7["r"], s7["cy"] - 10), (764, s7["cy"] - 10), (764, s6["cy"] + 12), (s6["l"], s6["cy"] + 12)])
    arrow([(s7["r"], s7["cy"] + 6), (s8["l"], s8["cy"] + 6)])
    arrow([(s8["cx"], s8["t"]), (s8["cx"], s6["b"])])
    arrow([(s9["r"], s9["cy"]), (750, s9["cy"]), (750, s6["cy"] + 22), (s6["l"], s6["cy"] + 22)])
    # owner outcomes -> both reports
    arrow([(s9["cx"] - 20, s9["b"]), (s9["cx"] - 20, s10["t"])])
    arrow([(s9["cx"] + 30, s9["b"]), (s9["cx"] + 30, 466), (s11["cx"], 466), (s11["cx"], s11["t"])])
    for k, (x, y, w, h, lines) in B.items():
        o.append(f'<rect class="fnode scr" x="{x}" y="{y}" width="{w}" height="{h}" rx="7"/>')
        o.append(f'<text x="{x + 10}" y="{y + 22}" class="strong">{E(lines[0])}</text>')
        o.append(f'<text x="{x + 10}" y="{y + 41}">{E(lines[1])}</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- summary svg
def summary_svg():
    items = [("5", "users"), ("28", "stories"), ("12", "flows"), ("12", "screens"), ("21", "draft contracts")]
    o = ['<svg viewBox="0 0 1000 250" role="img" aria-labelledby="sum-t sum-d" style="max-width:1000px;min-width:700px">',
         '<title id="sum-t">What UX-1 produced: from people to contracts</title>',
         '<desc id="sum-d">Five users lead to 28 stories, which lead to 12 flows, 12 screens and 21 draft contracts. One demo login gates everything. The screens sit on three surfaces, customer chat, demo tools and staff console, plus two read-only report pages.</desc>',
         '<defs><marker id="ahsum" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>']
    for i, (n, lab) in enumerate(items):
        x = 10 + i * 198
        o.append(f'<rect class="fnode sumbox" x="{x}" y="10" width="160" height="92" rx="10"/>')
        o.append(f'<text x="{x + 80}" y="58" text-anchor="middle" class="bignum">{n}</text>')
        o.append(f'<text x="{x + 80}" y="86" text-anchor="middle">{lab}</text>')
        if i < 4:
            o.append(f'<path class="arrow" d="M{x + 162},56 L{x + 196},56" marker-end="url(#ahsum)"/>')
    surf = [("Customer chat", "SCR-1 \u00b7 phone first", "pub"),
            ("Demo tools: simulation", "SCR-2, SCR-3 \u00b7 login: SCR-12", "demo"),
            ("Staff console + role switch", "SCR-4 to SCR-9 \u00b7 laptop first", "staff"),
            ("Read-only reports", "SCR-10, SCR-11 \u00b7 behind login", "ro")]
    for i, (a_, b_, cls) in enumerate(surf):
        x = 10 + i * 248
        o.append(f'<rect class="surf {cls}" x="{x}" y="150" width="232" height="80" rx="10"/>')
        o.append(f'<text x="{x + 14}" y="182" class="strong">{E(a_)}</text>')
        o.append(f'<text x="{x + 14}" y="206">{E(b_)}</text>')
    o.append('<path class="arrow dash" d="M802,104 L802,146" marker-end="url(#ahsum)"/>')
    o.append('<text x="812" y="132" class="small">where the screens live</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- tables data
REQ = SRC.parse_coverage(TXT[SOURCES[0]])
STORIES = [(d["id"], d["user"], d["title"], d["pri"], d["hp"]) for d in SRC.parse_stories(TXT[SOURCES[0]])]
SCREENS = SRC.parse_screens(TXT[SOURCES[2]])
CONS = SRC.parse_cons(TXT[SOURCES[1]])
ERRORS = SRC.parse_errors(TXT[SOURCES[1]])
assert (len(REQ), len(STORIES), len(SCREENS), len(CONS)) == (46, 28, 12, 21), (len(REQ), len(STORIES), len(SCREENS), len(CONS))

# flow metadata and contracts come from USER_FLOWS.md; the hand-drawn diagrams are checked against the Mermaid
_problems = []
for f in FLOWS:
    src = FLOWS_SRC[f["id"]]
    f.update(title=src["title"], stories=src["stories"], hp=src["hp"], start=src["start"], end=src["end"], cons=src["cons"])
    _problems += SRC.check_flow(f["id"], src["mermaid"], f["flow"].nodes, f["flow"].edges)
assert len(FLOWS) == len(FLOWS_SRC) == 12
if _problems:
    raise SystemExit("\n".join(_problems))


# ---------------------------------------------------------------- build sections
src_links = "<br>\n".join(
    f'<a href="../ux/01-planning/{Path(s).name}"><code>{s}</code></a> · <code data-sha-for="{s}">{SHA[s][:12]}</code>'
    for s in SOURCES)
meta_src = "\n".join(f'<meta name="review-source" content="{s}|{SHA[s]}">' for s in SOURCES)

journeys_html = []
for i, (title, secs) in enumerate(JOURNEYS, 1):
    svg, words, n = journey_svg(i, title, secs)
    journeys_html.append(f'''<figure class="journey" data-status="proposal">
  <h3 id="j{i}">Journey {i} · {E(title)} {badge("proposal", "Proposal: feeling we aim for")}</h3>
  <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
  <div class="scroll" tabindex="0" aria-label="Journey {i} diagram, scrolls sideways">
{svg}
  </div>
  <figcaption>{n} steps. The dots are the feeling we aim for at each step, from 1 (bad) to 5 (good). They are a design proposal, not measured data; the UX-5 walkthrough is where we would first see how it really feels.</figcaption>
  <ol class="words">{words}</ol>
</figure>''')

flow_index = "".join(
    f'<li><a href="#{f["id"].lower()}">{f["id"]}</a> {E(f["title"])}</li>' for f in FLOWS)

flows_html = []
for f in FLOWS:
    fl = f["flow"]
    svg = fl.svg(f'{f["id"]}: {f["title"]}', "Flowchart redrawn from the Mermaid source in USER_FLOWS.md. The numbered list below the diagram says the same thing.")
    words = "".join(f"<li>{E(w)}</li>" for w in f["words"])
    cons = ", ".join(f["cons"])
    note_html = ""
    if f.get("note"):
        nt, nb = f["note"][:2]
        note_html = (f'<div class="flownote" data-status="proposal"><h4>{E(nt)} {badge("proposal")}</h4>'
                     f'<p>{E(nb)}</p><p class="src">{E(f["note"][2])}</p></div>\n  ')
    flows_html.append(f'''<article class="card flowcard" data-status="proposal" id="{f["id"].lower()}">
  <h3><span>{f["id"]} · {E(f["title"])}</span> {badge("proposal", "Proposal: draft flow")}</h3>
  <p class="why">{E(f["why"])}</p>
  <dl class="flowmeta">
    <dt>Stories</dt><dd>{f["stories"]}</dd>
    <dt>Hard problem</dt><dd>{E(f["hp"])}</dd>
    <dt>Starts</dt><dd>{E(f["start"])}</dd>
    <dt>Ends</dt><dd>{E(f["end"])}</dd>
    <dt>Contracts used</dt><dd>{cons} <span class="muted">(from the flow’s step table)</span></dd>
  </dl>
  {note_html}<figure>
    <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="{f["id"]} flowchart, scrolls sideways">
{svg}
    </div>
    <figcaption>Redrawn by hand from the Mermaid in <code>USER_FLOWS.md</code>. Shapes: box = a step; six-sided box = a question with branches; rounded pill = a jump to another flow; dashed box = an error branch.</figcaption>
    <ol class="words">{words}</ol>
  </figure>
</article>''')

req_cells = "".join(f'<li><b>{r}</b> <span>{s}</span></li>' for r, s in REQ)

story_rows = "".join(
    f'<tr><td><b>{i}</b></td><td>{u}</td><td>{E(t)}</td><td>{p}</td><td>{h}</td></tr>' for i, u, t, p, h in STORIES)

fl_head = "".join(f'<th scope="col"><abbr title="FLOW-{n}">F{n}</abbr></th>' for n in range(1, 13))
fs_rows = []
for sid, *_rest in SCREENS:
    flows = _rest[2]
    cells = []
    for n in range(1, 13):
        if n in flows:
            cells.append('<td class="hit" aria-label="yes"><span aria-hidden="true">●</span></td>')
        else:
            cells.append('<td class="none" aria-label="no"></td>')
    fs_rows.append(f'<tr><th scope="row">{sid}</th>{"".join(cells)}</tr>')

CONIDS = [int(c[0].split("-")[1]) for c in CONS]
con_head = "".join(f'<th scope="col"><abbr title="CON-{n}">{n}</abbr></th>' for n in CONIDS)
sc_rows = []
for sid, *_rest in SCREENS:
    cs = _rest[3]
    cells = "".join('<td class="hit" aria-label="yes"><span aria-hidden="true">●</span></td>' if n in cs
                    else '<td class="none" aria-label="no"></td>' for n in CONIDS)
    sc_rows.append(f'<tr><th scope="row">{sid}</th>{cells}</tr>')

screen_rows = "".join(
    f'<tr data-status="proposal"><td><b>{sid}</b></td><td>{E(surf)}</td><td>{E(reach)}</td>'
    f'<td>{", ".join(f"FLOW-{n}" for n in flows)}</td><td>{", ".join(f"CON-{n}" for n in cs)}</td><td>{E(notes)}</td>'
    f'<td>{badge("proposal")}</td></tr>'
    for sid, surf, reach, flows, cs, notes in SCREENS)

con_rows = "".join(
    f'<tr data-status="proposal"><td><b>{c}</b></td><td><code>{E(op)}</code></td><td>{E(carries)}</td><td>{used}</td><td>{badge("proposal", "Draft")}</td></tr>'
    for c, op, carries, used in CONS)

err_rows = "".join(f'<tr data-status="proposal"><td>{E(e)}</td><td>{f}</td><td>{badge("proposal")}</td></tr>' for e, f in ERRORS)

# ---------------------------------------------------------------- page
CSS = (Path(__file__).parent / "ux1.css").read_text()

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meridian AI Agent — UX-1 Planning Review</title>
<meta name="review-stage" content="UX-1 · Planning (ux-pipeline §4b)">
<meta name="review-status" content="DRAFT — UX-1 gate closed by Claude with no sign-off stop (standing policy, Innocent 2026-10-20); re-checked against PRD v0.4 (its Stage 4 gate passed, Innocent 2026-10-20)">
<meta name="review-date" content="2026-10-21">
{meta_src}
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <p class="kicker">ux-pipeline · UX-1 · Planning (zero-to-hero §4b) · local visual review · Markdown is the source of truth</p>
  <h1>Meridian AI service agent: who uses it, the paths they take, and the screens they land on</h1>
  <div class="status-banner draft" role="status"><span class="st proposal">DRAFT</span>
    <div><strong>Draft, updated 2026-10-21.</strong> Drafted on PRD v0.2 beside Stage 4, re-checked against PRD v0.4, which you approved at Stage 4, then updated for R-48 (one demo login, a one-click role switch). Claude closes this gate itself (your standing policy), so nothing here waits on you. Read it whenever you like; anything you raise sends the work back to UX-1.</div></div>
  <dl class="meta">
    <dt>Stage</dt><dd>UX-1 · Planning (ux-pipeline §4b): user stories, journeys, flows, sitemap, draft contracts</dd>
    <dt>Review date</dt><dd>2026-10-21 (rebuilt after the R-48 demo-login pass; first built 2026-10-20, late evening CT)</dd>
    <dt>Sources (full documents)</dt><dd>
{src_links}</dd>
    <dt>Context it rests on</dt><dd><a href="../prd/inno-aea-callcenter-prd.md"><code>docs/prd/inno-aea-callcenter-prd.md</code></a> (v0.4, approved at Stage 4) · <a href="../design/hard-problems.md"><code>docs/design/hard-problems.md</code></a> · <a href="../data/worked-pairs.md"><code>docs/data/worked-pairs.md</code></a></dd>
    <dt>Refresh</dt><dd>If a source changes, this page is rebuilt and re-checked before anyone relies on it.</dd>
  </dl>
  <ul class="legend" data-legend aria-label="Status legend">
    <li><span class="st fact" data-legend-item="fact">Fact</span> a source or a check says it</li>
    <li><span class="st decision" data-legend-item="decision">Your decision</span> you chose it, with a date</li>
    <li><span class="st proposal" data-legend-item="proposal">Proposal</span> Claude’s draft; not yours yet</li>
    <li><span class="st unknown" data-legend-item="unknown">Unknown</span> not established</li>
    <li><span class="st awaiting" data-legend-item="awaiting">Awaiting you</span> waits on your approval</li>
  </ul>
</div></header>
<main id="main" class="wrap">

<nav class="toc" aria-label="On this page"><ol>
  <li><a href="#early-h">Early start</a></li><li><a href="#sum-h">At a glance</a></li><li><a href="#story-h">The story so far</a></li>
  <li><a href="#users-h">Users and stories</a></li><li><a href="#jour-h">Journeys</a></li><li><a href="#flows-h">Flows</a></li>
  <li><a href="#map-h">Sitemap</a></li><li><a href="#cov-h">Coverage</a></li><li><a href="#err-h">Error branches</a></li>
  <li><a href="#con-h">Draft contracts</a></li><li><a href="#prop-h">Proposals</a></li><li><a href="#gate-h">The gate and the fork</a></li>
</ol></nav>

<section aria-labelledby="early-h">
  <h2 id="early-h">Early start: UX-1 runs beside Stage 4</h2>
  <div class="grid two">
    <article class="card" data-status="decision"><h3>You started the UX stages early {badge("decision")}</h3>
      <p>On 2026-10-20 at about 21:05 CT you wrote: <q>while i settle things with aea investors stage 4 lets start the ux stages</q>.</p>
      <p>So UX-1 was drafted on PRD v0.2 while the Stage 4 interview is still open. It is an overlap, not a skip: Stage 4 still runs in full.</p>
      <p class="src">Source: the status lines of all three UX-1 files; <code>PROJECT-CHECKLIST.md</code> §4b.</p></article>
    <article class="card" data-status="decision"><h3>You approved the PRD at Stage 4: v0.4 {badge("decision")}</h3>
      <p>You approved PRD v0.4 at the Stage 4 gate on 2026-10-20. UX-1 was reopened and re-checked against it the same night.</p>
      <p>Three changes reached the screens: alerts stay on the monitoring page, and a health check restarts the service (R-35). Traces stay in Langfuse on your VPS, not on the demo’s pages (R-36). The evaluation has a dev split and a sealed held-out split, and the headline number comes from the held-out one (R-38). Monitoring also shows spend against the daily cap. The other 0.4 changes (models, the tracing host) change no screen.</p>
      <p class="src">Source: PRD v0.4 header and rows R-35, R-36, R-38; the status lines of the three UX-1 files.</p></article>
  </div>
</section>

<section aria-labelledby="sum-h" data-visual="summary"><h2 id="sum-h">At a glance</h2>
  <p class="section-sub">Five kinds of people use the product. Their needs became 28 stories. The stories became 12 flows, the flows land on 12 screens, and each screen talks to the backend through draft contracts. A new rule, R-48, puts one demo login in front of everything.</p>
  <figure data-status="fact">
    <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="Summary diagram, scrolls sideways">
{summary_svg()}
    </div>
    <figcaption>{badge("fact")} counts from <code>trace_check.py</code> at <code>--upto CON</code>: 0 fails; 46 requirements in scope; US=28, FLOW=12, SCR=12, CON=22 (21 of them are listed in USER_FLOWS.md; CON-21 is added later, at UX-3).</figcaption>
    <ol class="words"><li>5 users lead to 28 stories, 12 flows, 12 screens and 21 listed draft contracts.</li><li>Everything sits behind one demo login (SCR-12). Behind it are three surfaces plus two report pages: the customer chat (SCR-1, phone first), the demo tools (SCR-2, SCR-3), the staff console (SCR-5 to SCR-9, laptop first, with the role switch SCR-4 in every header), and the read-only reports (SCR-10, SCR-11).</li></ol>
  </figure>
  <div class="grid three">
    <article class="card" data-status="fact"><h3>Every requirement has a story {badge("fact")}</h3><p class="big">46 of 46 in scope.</p><p class="src">R-42 and R-43 are deliverables with no screen (repo, docs, video).</p></article>
    <article class="card" data-status="fact"><h3>Every flow ends on a screen {badge("fact")}</h3><p class="big">12 of 12.</p><p class="src">SITEMAP.md, “Every flow ends on a screen”.</p></article>
    <article class="card" data-status="proposal"><h3>Contracts are drafts {badge("proposal")}</h3><p class="big">CON-1 to CON-20, and CON-22.</p><p class="src">Names, fields and errors get settled and signed at UX-3.</p></article>
  </div>
</section>

<section aria-labelledby="story-h" data-visual="story"><h2 id="story-h">The story so far</h2>
  <p class="lede">AEA wants Meridian’s call center to <q>expand call center coverage without adding headcount by deflecting a majority of calls to an AI agent</q>. Meridian is a made-up Austin heating, cooling and plumbing company.</p>
  <p>So we are building a chat agent for Meridian’s homeowners. It answers the routine questions from the <em>current</em> help files. It books visits. It gives the safety instruction first when someone is at risk. Everything else goes to a person, honestly: a reference number and a promise it can keep.</p>
  <div class="grid three">
    <article class="card" data-status="fact"><h3>Who uses it {badge("fact")}</h3>
      <ul class="tight"><li><b>Homeowner:</b> uses the chat.</li><li><b>Representative:</b> picks up a handoff.</li><li><b>Supervisor:</b> makes sure nothing urgent or late is left.</li><li><b>Business owner:</b> asks if the AI cuts load without hurting customers.</li><li><b>Reviewer:</b> AEA’s grader, who will <q>try to break it</q> and <q>watch the agent escalate</q>.</li></ul>
      <p class="src">PRD §2; USER_STORIES.md. In the demo, the reviewer signs in once with the demo login and plays every role through a one-click, labelled role switch (OD-1, OD-2, R-48).</p></article>
    <article class="card" data-status="decision"><h3>What Stages 1 to 3 settled {badge("decision")}</h3>
      <ul class="tight"><li><b>Stage 1:</b> the PRD 0.2 scope and targets (“yes to all”, 2026-10-20).</li>
      <li><b>HP-1:</b> your two-layer design. Code guards run first; a planner picks tasks; a responder with no tools writes the words.</li>
      <li><b>HP-2:</b> rules first for danger; a small classifier may only raise the risk.</li>
      <li><b>HP-3:</b> the AI never makes a change that carries the $49 fee.</li>
      <li><b>HP-4:</b> a completion check and a fact check on every reply.</li></ul>
      <p class="src">PRD v0.4 header; hard-problems.md (all four chosen, Innocent ✓ 2026-10-20).</p></article>
    <article class="card" data-status="fact"><h3>How this stage was made {badge("fact")}</h3>
      <p>Claude read the PRD, the eight worked examples (WP-1 to WP-8) and the four hard-problem choices. From them it wrote 28 user stories, each tied to a PRD requirement. Then came 7 journeys, 12 flows, 12 screens and 21 listed draft contracts.</p>
      <p>A script, <code>trace_check.py</code>, then checked the chain: requirement → story → flow → screen → contract. It found 0 breaks.</p>
      <p>One late rule changed the picture on 2026-10-21. R-48 (you, Stage 6: <q>it should be password-gated in general</q>) puts one demo login in front of the whole deployment. Reviewers need to act as both customer and staff, so the old staff sign-in became a one-click role switch. That added story US-28, screen SCR-12 and contract CON-22.</p>
      <p class="src">The three UX-1 files; trace_check output, 2026-10-21.</p></article>
  </div>
  <p>Two words you’ll see a lot. A <b>flow</b> is the path one person takes to finish one job. A <b>contract</b> (CON) is the request a screen sends to the backend, like an order slip passed to the kitchen. Most customer flows happen on one screen, the chat. Every message and every button on a reply card goes through the same contract, CON-2.</p>
</section>

<section aria-labelledby="users-h"><h2 id="users-h">Users and their 28 stories</h2>
  <p class="section-sub">A story says who needs what, and why. Priority follows the PRD: P0 is a Must, P1 a Should, P2 a Could. Each story’s full text and acceptance check are in <a href="../ux/01-planning/USER_STORIES.md"><code>USER_STORIES.md</code></a>.</p>
  <div class="table-scroll" tabindex="0" aria-label="Stories table, scrolls sideways" data-status="proposal">
  <table><caption>28 stories {badge("proposal", "Proposal: draft stories")}</caption>
  <thead><tr><th scope="col">Story</th><th scope="col">User</th><th scope="col">Need</th><th scope="col">Priority</th><th scope="col">Hard problem</th></tr></thead>
  <tbody>{story_rows}</tbody></table></div>
</section>

<section aria-labelledby="jour-h"><h2 id="jour-h">Journeys: one per user type</h2>
  <p class="section-sub">A journey follows one person from start to finish. The line above each journey is how we <em>aim</em> for them to feel at each step, from 1 (bad) to 5 (good). The low points are on purpose: they are the moments the design has to carry, like a gas smell or a surprise fee.</p>
{"".join(journeys_html)}
</section>

<section aria-labelledby="flows-h"><h2 id="flows-h">Flows: the 12 paths, step by step</h2>
  <p class="section-sub">Each flow shows the steps, the questions that branch it, the error branches, where it starts and ends, and the contracts it uses. All four hard-problem cards were chosen at Stage 3, so no flow rests on an open card. The clock is fixed at the dataset’s “today”, Fri 2026-10-16 (R-3).</p>
  <ol class="flowindex">{flow_index}</ol>
{"".join(flows_html)}
</section>

<section aria-labelledby="map-h"><h2 id="map-h">Sitemap: one login, three surfaces, two report pages, twelve screens</h2>
  <p class="section-sub">The product is one app. Nothing answers without the demo login (SCR-12), except a health check. Behind it are three surfaces and two read-only report pages. The chat is the default. The demo tools exist so a grader can see what is simulated. Staff screens have their own header and look. A role switch (SCR-4) sits in every header, so one click moves the reviewer between customer and staff, with no second password. The two reports, monitoring and evaluation, hold only redacted totals and open in any role. The chat is built phone first; the staff console laptop first, still usable on a phone.</p>
  <figure data-status="proposal">
    <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="Sitemap diagram, scrolls sideways">
{sitemap_svg()}
    </div>
    <figcaption>{badge("proposal", "Proposal: draft sitemap")} Redrawn from the Mermaid in <code>SITEMAP.md</code>. Dashed arrows: the code hint and the guide’s links. The role switch is a label, not security: the login is the only gate.</figcaption>
    <ol class="words">
      <li>The demo login SCR-12 leads to the customer chat SCR-1.</li>
      <li>Chat SCR-1 links to the demo guide SCR-3 through its demo bar. Its code hint points to the demo inbox SCR-2.</li>
      <li>The demo guide SCR-3 links to the inbox SCR-2, the role switch SCR-4, and both read-only reports: monitoring SCR-10 and evaluation SCR-11.</li>
      <li>The role switch SCR-4 leads back to the chat SCR-1 and on to the representative queue SCR-5, supervisor oversight SCR-7 and business-owner outcomes SCR-9.</li>
      <li>The queue, oversight, the flag list SCR-8 and owner outcomes all open the case view SCR-6. Oversight opens the flag list.</li>
      <li>Owner outcomes SCR-9 also link to both read-only reports. The reports sit outside the staff console, behind the same demo login as everything else.</li>
    </ol>
  </figure>
  <div class="table-scroll" tabindex="0" aria-label="Screens table, scrolls sideways">
  <table class="screens"><caption>The 12 screens (draft)</caption>
  <thead><tr><th scope="col">Screen</th><th scope="col">Surface</th><th scope="col">Reached from</th><th scope="col">Flows</th><th scope="col">Contracts</th><th scope="col">What it holds</th><th scope="col">Status</th></tr></thead>
  <tbody>{screen_rows}</tbody></table></div>
</section>

<section aria-labelledby="cov-h"><h2 id="cov-h">Coverage: nothing in the PRD is left without a home</h2>
  <p class="section-sub">These grids answer one question each. Does every requirement have a story? Does every flow land on a screen? Does every screen have the contracts it needs? A gap here would mean a part of the product nobody designed.</p>
  <h3>Requirement → stories {badge("fact")}</h3>
  <ul class="reqgrid" data-status="fact" aria-label="Requirement to stories">{req_cells}</ul>
  <p class="note" data-status="fact">{badge("fact")} <b>No screen:</b> R-42 (public repository) and R-43 (README, technical documentation, deployment guide, test results, video). They are deliverables, not product surfaces; <code>SUBMISSION.md</code> tracks them.</p>
  <h3>Flow × screen {badge("fact")}</h3>
  <div class="table-scroll" tabindex="0" aria-label="Flow by screen matrix, scrolls sideways" data-status="fact">
  <table class="matrix"><caption>● = the screen lists that flow in SITEMAP.md’s Flows column.</caption>
  <thead><tr><th scope="col">Screen</th>{fl_head}</tr></thead><tbody>{"".join(fs_rows)}</tbody></table></div>
  <h3>Screen × contract {badge("fact")}</h3>
  <div class="table-scroll" tabindex="0" aria-label="Screen by contract matrix, scrolls sideways" data-status="fact">
  <table class="matrix"><caption>● = the screen uses that draft contract (SITEMAP.md, Contracts in the Notes column). Column numbers are CON-1 to CON-20 and CON-22.</caption>
  <thead><tr><th scope="col">Screen</th>{con_head}</tr></thead><tbody>{"".join(sc_rows)}</tbody></table></div>
</section>

<section aria-labelledby="err-h"><h2 id="err-h">Error branches: where each failure goes</h2>
  <p class="section-sub">The brief asks for “clean failure”. So every way a request can go wrong has a flow that handles it. The usual answer is a plain message and a way to reach a person, never a crash or a guess.</p>
  <div class="table-scroll" tabindex="0" aria-label="Error branches table">
  <table><thead><tr><th scope="col">Error branch</th><th scope="col">Flow</th><th scope="col">Status</th></tr></thead><tbody>{err_rows}</tbody></table></div>
</section>

<section aria-labelledby="con-h"><h2 id="con-h">Draft contracts CON-1 to CON-20 and CON-22</h2>
  <p class="section-sub">These are the requests the screens make. They are <strong>drafts</strong>: names, fields and errors get settled at UX-3 and signed there. Then they go to the System track as its starting set of component contracts.</p>
  <div class="table-scroll" tabindex="0" aria-label="Draft contracts table, scrolls sideways">
  <table><thead><tr><th scope="col">CON</th><th scope="col">Draft operation</th><th scope="col">Carries</th><th scope="col">Used by</th><th scope="col">Status</th></tr></thead><tbody>{con_rows}</tbody></table></div>
</section>

<section aria-labelledby="prop-h"><h2 id="prop-h">Proposals still open in these drafts</h2>
  <p class="section-sub">These choices are Claude’s, made while drafting. They get settled at UX-3, or sooner if you object to one.</p>
  <div class="grid two">
    <article class="card" data-status="proposal"><h3>The role switch is a label, not a gate {badge("proposal")}</h3>
      <p>SCR-4 keeps its ID but is now a control in a shared header, with an optional full page. We assume the role is held per browser tab while the login cookie is shared, so a reviewer can keep a customer tab and a staff tab open. Monitoring and evaluation are no longer proposed as open without sign-in: they sit behind the same login, after your <q>it should be password-gated in general</q>.</p>
      <p class="src">Settles at UX-3. SITEMAP.md, Proposals; USER_STORIES.md US-28.</p></article>
    <article class="card" data-status="proposal"><h3>One demo guide page {badge("proposal")}</h3>
      <p>SCR-3 holds the staffing toggle and the reset. The supervisor view repeats the staffing toggle and adds the clock, because those are supervisor actions in the story.</p>
      <p class="src">Settles at UX-3. SITEMAP.md, Proposals (consolidated §6).</p></article>
    <article class="card" data-status="proposal"><h3>The handoff reference stays in the chat {badge("proposal")}</h3>
      <p>There is no separate “my request” page. A returning customer quotes the reference in the chat.</p>
      <p class="src">Settles at UX-3. SITEMAP.md, Proposals (consolidated §6 transitions).</p></article>
    <article class="card" data-status="proposal"><h3>Stack note: the pages stay light {badge("proposal")}</h3>
      <p>PRD §6.2 proposes server-rendered pages with light JavaScript and no separate frontend build. The ux-pipeline’s default prototype is React, Vite and TypeScript. The project’s stack wins.</p>
      <p>So the contracts stay JSON endpoints that the pages’ JavaScript calls (the chat turn, the event stream, staff actions). Whether staff pages render on the server or from the same JSON is a UX-3 / §6 choice, not a UX-1 one.</p>
      <p class="src">Settles at UX-3 or §6. USER_FLOWS.md, “Note for UX-3 and the System track”.</p></article>
  </div>
</section>

<section aria-labelledby="gate-h"><h2 id="gate-h">The gate, and the fork</h2>
  <div class="grid two">
    <article class="card" data-status="decision"><h3>Claude closes this gate, with no stop for you {badge("decision")}</h3>
      <p>Your standing policy, 2026-10-20: <q>skip need approval on the flow diagram … i trust the flow that you’ve been building</q>.</p>
      <p>So Claude closes UX-1 once the checks below hold and this page passes its own check. You can read it whenever you choose. Anything you raise sends the work back to UX-1 and reopens what depends on it.</p>
      <p class="src">ux-pipeline <code>references/phases.md</code>, UX-1 gate. UX-2 to UX-5 still need your sign-off.</p></article>
    <article class="card" data-status="fact"><h3>What the gate checks {badge("fact")}</h3>
      <ul class="checks">
        <li>Every in-scope requirement has at least one story: 46 of 46.</li>
        <li>Every story maps to at least one flow: 28 stories, 12 flows.</li>
        <li>Every flow ends on a reachable screen: 12 of 12.</li>
        <li>Every named error branch has a flow: {len(ERRORS)} rows in the error table.</li>
        <li><code>trace_check --upto FLOW</code>: 0 fails, 46 requirements, US=28, FLOW=12.</li>
        <li><code>--upto SCR</code> and <code>--upto CON</code> also pass, with SCR=12 and CON=22.</li>
      </ul>
      <p class="src">trace_check.py run on the three UX-1 files, 2026-10-21.</p></article>
  </div>
  <div class="fork" data-status="proposal">
    <h3>The fork: two sessions from here {badge("proposal", "Next step")}</h3>
    <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="Fork diagram, scrolls sideways">
    <svg viewBox="0 0 900 190" role="img" aria-labelledby="fk-t fk-d" style="max-width:900px;min-width:700px">
      <title id="fk-t">The fork after UX-1</title>
      <desc id="fk-d">UX-1 splits into two tracks. This session continues with UX-2 to UX-5. A second session starts the System track with section 5 spikes and section 6 design. They join at section 7 tickets.</desc>
      <defs><marker id="ahf" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>
      <rect class="fnode" x="10" y="66" width="150" height="56" rx="8"/><text x="85" y="92" text-anchor="middle" class="strong">UX-1 planning</text><text x="85" y="110" text-anchor="middle" class="small">this page</text>
      <rect class="fnode" x="240" y="14" width="430" height="56" rx="8"/><text x="256" y="38" class="strong">UX track (this session)</text><text x="256" y="58">UX-2 concepts → UX-3 structure → UX-4 prototype → UX-5 verify</text>
      <rect class="fnode" x="240" y="118" width="430" height="56" rx="8"/><text x="256" y="142" class="strong">System track (a second session)</text><text x="256" y="162">§5 spikes → §6 design</text>
      <rect class="fnode" x="750" y="66" width="140" height="56" rx="8"/><text x="820" y="92" text-anchor="middle" class="strong">§7 tickets</text><text x="820" y="110" text-anchor="middle" class="small">the tracks join</text>
      <path class="arrow" d="M160,86 L200,86 L200,42 L240,42" marker-end="url(#ahf)"/>
      <path class="arrow" d="M160,102 L200,102 L200,146 L240,146" marker-end="url(#ahf)"/>
      <path class="arrow" d="M670,42 L710,42 L710,86 L750,86" marker-end="url(#ahf)"/>
      <path class="arrow" d="M670,146 L710,146 L710,102 L750,102" marker-end="url(#ahf)"/>
    </svg></div>
    <ol class="words"><li>This session carries on with UX-2.</li><li>A second session starts the System track: §5 spikes, then §6 design.</li><li>The two tracks join at §7 tickets. The UI contracts are what they agree on.</li></ol>
    <p><b>What the System-track session reads first:</b> the <a href="../prd/inno-aea-callcenter-prd.md">PRD</a>, <a href="../ux/01-planning/USER_STORIES.md"><code>USER_STORIES.md</code></a>, the draft CONs at the end of <a href="../ux/01-planning/USER_FLOWS.md"><code>USER_FLOWS.md</code></a>, <a href="../design/hard-problems.md"><code>hard-problems.md</code></a> and <a href="../data/worked-pairs.md"><code>worked-pairs.md</code></a>. It runs on the same machine as the working copy and the same model as this session.</p>
  </div>
  <div class="notasked" data-status="fact">
    <h3>What this page does not ask you to approve {badge("fact")}</h3>
    <ul class="tight"><li>Nothing. There is no approval stop at UX-1.</li>
    <li>The draft contracts, screens and flows are not yours yet. They get settled at UX-3, which does need your sign-off.</li>
    <li>The PRD itself: you approved v0.4 at Stage 4 (see the top of the page).</li></ul>
  </div>
</section>
</main>
<footer class="wrap">Local file, not published. Markdown is the source of truth; this page is a synthesis built after the three UX-1 files. If any source changes, rebuild the page and run the zero-to-hero <code>check_review_page.py</code> before relying on it.</footer>
</body>
</html>
'''
OUT.write_text(page)
SRC.accept_snapshots(ROOT, SOURCES, SNAPDIR)
print("wrote", OUT, len(page), "bytes")
