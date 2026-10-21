"""Generate docs/artifacts/2026-10-21-ux-structure.html: the UX-3 Structure review page (ux-pipeline §4b).

Run from the project root:  python3 docs/artifacts/_build/ux-structure/gen_ux3.py . [--accept-changes]

PARSED from the sources at every build (ux3_sources.py), so it cannot go stale:
  the token swatches, the computed contrast (and re-computed here to cross-check design.md), the type scale and its
  live specimens, the mint table, the texture check, every IA row, every region and state of every screen card, the
  11 x 8 state matrix (n/a reasons from each card), flow-state coverage, the contract map, the operations (from the
  OpenAPI file), both named-error tables, the data classes, the N-1..N-27 landing table and the DO-4 (UXR) table.
HAND-MAINTAINED below (and so guarded by a snapshot of each source as last accepted): the story, the "why" prose, the
region -> state hover notes, the pin positions on the screenshots, the SVG layout, the decision and ask cards, and
the list of places where the sources disagree. If a source changed, the build prints the diff and stops; read it,
update the hand-written parts it touches, then re-run with --accept-changes. Never just re-stamp the hashes.

Screenshots: the A5 wireframes in docs/ux/02-concepts/wireframes/ are used when they exist. If a wireframe is missing,
a crop of the A5 look sheet (img/ls-*.png, made with headless Chrome from 2026-10-20-a5-look-sheet.html) is used and
the page says so. Images are compressed to WebP (cwebp) and embedded as data URIs. Keep the page under about 6 MB.
"""
import base64
import hashlib
import html
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import ux3_sources as SRC  # noqa: E402

ROOT = Path(sys.argv[1]).resolve()
ACCEPT = "--accept-changes" in sys.argv
OUT = ROOT / "docs/artifacts/2026-10-21-ux-structure.html"
S_IA = "docs/ux/03-structure/IA.md"
S_SP = "docs/ux/03-structure/SCREEN_SPECS.md"
S_UC = "docs/ux/03-structure/UI_CONTRACTS.md"
S_OA = "docs/ux/03-structure/ui-contracts.openapi.yaml"
S_DS = "docs/design/design.md"
S_DD = "docs/design/DESIGN-DIRECTIONS.md"
S_CK = "PROJECT-CHECKLIST.md"
REVIEW = [S_IA, S_SP, S_UC, S_OA, S_DS]
SOURCES = REVIEW + [S_DD, S_CK]
SRC.snapshot_guard(ROOT, SOURCES, HERE / "snapshots", ACCEPT)
TXT = {s: (ROOT / s).read_text() for s in SOURCES}
SHA = {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES}
E = html.escape
PROBLEMS = []  # cross-source checks that failed; printed at the end and shown on the page where hand-listed

IA = SRC.parse_ia(TXT[S_IA])
SP = SRC.parse_specs(TXT[S_SP])
UC = SRC.parse_contracts(TXT[S_UC])
OPS, OA_VER = SRC.parse_openapi(TXT[S_OA])
DS = SRC.parse_design(TXT[S_DS])
SCREENS = sorted(IA["screens"].keys(), key=lambda x: int(x[4:]))
assert set(SP["cards"]) == set(SCREENS), "screen sets differ between IA and SCREEN_SPECS"
SP["cards"] = {k: SP["cards"][k] for k in SCREENS}


# ------------------------------------------------------------------ helpers
def md(s):
    s = re.sub(r"\bdecided\b", "settled", s)
    s = re.sub(r"\bDecided\b", "Settled", s)
    s = re.sub(r"\bconfirmed\b", "checked", s)
    s = E(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])", r"<i>\1</i>", s)
    return s


def mdc(s):
    """md() plus CON-n links to the contract table anchors."""
    return re.sub(r"\b(CON-\d+)\b", lambda m: f'<a href="#con-{m.group(1)[4:]}">{m.group(1)}</a>', md(s))


def badge(s, label=None):
    names = {"fact": "Fact", "decision": "Your decision", "proposal": "Proposal",
             "unknown": "Unknown", "awaiting": "Awaiting you"}
    return f'<span class="st {s}">{label or names[s]}</span>'


def _rel(path):
    return "../" + path[5:] if path.startswith("docs/") else "../../" + path


def src_link(path, text=None):
    return f'<a href="{_rel(path)}">{E(text or Path(path).name)}</a>'


def table(head, rows, cls="", caption=None, scope_first=False, min_w=None):
    h = "".join(f'<th scope="col">{c}</th>' for c in head)
    body = []
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            cells.append(f'<th scope="row">{c}</th>' if (scope_first and i == 0) else f"<td>{c}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    st = f' style="min-width:{min_w}px"' if min_w else ""
    return (f'<div class="table-scroll" tabindex="0" role="region" aria-label="{E(re.sub("<[^>]+>", "", caption or "table"))}">'
            f'<table class="{cls}"{st}>{cap}<thead><tr>{h}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def sid_num(s):
    return int(s.split("-")[1])


def short_title(t):
    t = re.sub(r"\(.*?\)", "", t)
    t = re.split(r"[:,]", t)[0]
    return t.strip().strip('"')


# ------------------------------------------------------------------ colour maths (cross-check design.md)
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


TOK = {}  # name -> {"light": hex, "dark": hex, "job": ..}
for r in DS["semantic"]:
    name = r[0].strip("`").replace("--color-", "")
    lh = re.search(r"#[0-9A-Fa-f]{6}", r[1])
    dh = re.search(r"#[0-9A-Fa-f]{6}", r[2])
    TOK[name] = {"light": lh.group(0) if lh else None, "dark": dh.group(0) if dh else None,
                 "light_raw": r[1], "dark_raw": r[2], "job": r[3], "role": r[4] if len(r) > 4 else ""}


def contrast_rows(rows, need):
    out, bad = [], 0
    for r in rows:
        m = re.match(r"`([a-z-]+)` on `([a-z-]+)`", r[0])
        a, b = m.group(1), m.group(2)
        cells = []
        for k, col in (("light", r[1]), ("dark", r[2])):
            listed = float(col.split(":")[0])
            calc = ratio(TOK[a][k], TOK[b][k])
            if abs(calc - listed) > 0.011:
                PROBLEMS.append(f"design.md contrast {a} on {b} ({k}): listed {listed}, recomputed {calc:.2f}")
            ok = listed >= need
            bad += 0 if ok else 1
            cells.append(f'<span class="ratio {"ok" if ok else "bad"}">{listed:.2f}:1 {"✓" if ok else "✗"}</span>')
        out.append([f"<code>{a}</code> on <code>{b}</code>"] + cells)
    return out, bad


TEXT_ROWS, TEXT_BAD = contrast_rows(DS["text_pairs"], 4.5)
UI_ROWS, UI_BAD = contrast_rows(DS["ui_pairs"], 3.0)


# ------------------------------------------------------------------ images
def webp_b64(png: Path, width=None, q=72):
    out = HERE / "img" / (png.stem + ".webp")
    cmd = ["cwebp", "-quiet", "-q", str(q), str(png), "-o", str(out)]
    if width:
        cmd[1:1] = ["-resize", str(width), "0"]
    subprocess.run(cmd, check=True)
    return "data:image/webp;base64," + base64.b64encode(out.read_bytes()).decode(), out.stat().st_size


SHOTS = [("chat-390", "Customer chat on a phone (390 px)", "SCR-1"),
         ("chat-1280", "Customer chat on a laptop (1280 px)", "SCR-1"),
         ("case-1280", "Case view on a laptop (1280 px)", "SCR-6")]
IMG = {}  # (key, theme) -> (data uri, bytes, source label)
for key, _, _ in SHOTS:
    for theme in ("light", "dark"):
        wf = ROOT / f"docs/ux/02-concepts/wireframes/A5-{key}-{theme}.png"
        ls = HERE / "img" / f"ls-{key}-{theme}.png"
        if wf.exists():
            uri, n = webp_b64(wf, width=1280 if "1280" in key else 780)
            IMG[(key, theme)] = (uri, n, "wireframe")
        elif ls.exists():
            uri, n = webp_b64(ls, width=1280 if "1280" in key else 780)
            IMG[(key, theme)] = (uri, n, "look sheet crop")
SHOT_SOURCES = sorted({v[2] for v in IMG.values()})
print("screenshot sources:", SHOT_SOURCES or "none", file=sys.stderr)

FONTS_CSS = ""
for fam, f, w in (("A5 Display", "a5-display", "100 900"), ("A5 Sans", "a5-sans", "100 900"), ("A5 Mono", "a5-mono", "100 900")):
    b = base64.b64encode((HERE / "img" / f"{f}.woff2").read_bytes()).decode()
    FONTS_CSS += (f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{b}) format('woff2');"
                  f"font-weight:{w};font-display:swap}}\n")
CSS = (HERE / "ux3.css").read_text() + "\n" + FONTS_CSS

# ------------------------------------------------------------------ counts used on the page
N_ROWS_STATE = sum(len(m["cells"]) for m in SP["matrix"].values())
NA = {(sid, st) for sid, m in SP["matrix"].items() for st, v in m["cells"].items() if v.strip().lower() == "n/a"}
NA_CARD = {(sid, st) for sid, c in SP["cards"].items() for st, v in c["states"].items() if v["looks"].lower().startswith("n/a")}
if NA != NA_CARD:
    PROBLEMS.append(f"state matrix n/a cells {sorted(NA - NA_CARD)} vs card n/a cells {sorted(NA_CARD - NA)} differ")
for sid, c in SP["cards"].items():
    if len(c["states"]) != 8:
        PROBLEMS.append(f"{sid} has {len(c['states'])} state rows, not 8")
m = re.search(r"(\d+) cells.*?(\d+) real states, (\d+) n/a", SP["count_line"])
if (int(m.group(1)), int(m.group(2)), int(m.group(3))) != (N_ROWS_STATE, N_ROWS_STATE - len(NA), len(NA)):
    PROBLEMS.append(f"SCREEN_SPECS count line {m.groups()} vs computed {(N_ROWS_STATE, N_ROWS_STATE - len(NA), len(NA))}")
N_REAL = N_ROWS_STATE - len(NA)
N_FLOWSTATES = sum(len(c["flow_states"]) for c in SP["cards"].values())
CON_IDS = sorted(UC["cons"], key=lambda c: int(c[4:]))
XCON = sorted({o.get("con") for o in OPS}, key=lambda c: int(c[4:]))
if XCON != CON_IDS:
    PROBLEMS.append(f"x-con values {XCON} differ from CON cards {CON_IDS}")
if UC["stated_ops"] != len(OPS):
    PROBLEMS.append(f"UI_CONTRACTS says {UC['stated_ops']} operations, OpenAPI has {len(OPS)}")
OP_BY_ID = {o["id"]: o for o in OPS}
map_ops = [o for r in UC["map"] for o in r["ops"]]
if set(map_ops) != set(OP_BY_ID):
    PROBLEMS.append(f"contract map ops differ from OpenAPI: {sorted(set(map_ops) ^ set(OP_BY_ID))}")
# the CON a map row names must be the x-con of its operations (primary + extra)
for r in UC["map"]:
    allowed = set(r["cons"]) | set(r["extra"])
    for o in r["ops"]:
        if OP_BY_ID.get(o, {}).get("con") not in allowed:
            PROBLEMS.append(f"{r['screen']}: op {o} has x-con {OP_BY_ID.get(o, {}).get('con')}, map row names {sorted(allowed)}")
OPS_PER_CON = {c: [o for o in OPS if o["con"] == c] for c in CON_IDS}
# SCREEN_SPECS 'Contracts' line vs the contract map
MAP_CONS = {}
for r in UC["map"]:
    MAP_CONS.setdefault(r["screen"].split(" ")[0], set()).update(r["cons"] + r["extra"])
for sid, c in SP["cards"].items():
    spec_cons = set(re.findall(r"CON-\d+", c["contracts"]))
    mp = MAP_CONS.get(sid, set())
    if spec_cons != mp:
        PROBLEMS.append(f"{sid}: SCREEN_SPECS lists {sorted(spec_cons, key=lambda x: int(x[4:]))}; the contract map lists {sorted(mp, key=lambda x: int(x[4:]))}")
UXR_ADOPTED = sum(1 for r in UC["uxr"] if r[1].startswith("Adopted"))
UXR_ADAPTED = sum(1 for r in UC["uxr"] if r[1].startswith("Adapted"))
if len(UC["uxr"]) != UXR_ADOPTED + UXR_ADAPTED:
    PROBLEMS.append("a UXR row is neither adopted nor adapted")
N_BLOCKS = UC["block_types"]
NEEDS = {}
for r in SP["needs"]:
    NEEDS[r[0]] = r
LAND = {}
for r in UC["landing"]:
    for n in re.findall(r"N-\d+", r[0]):
        LAND[n] = r
for n in NEEDS:
    if n not in LAND and not n.endswith("resolved"):
        PROBLEMS.append(f"{n} has no row in the UI_CONTRACTS landing table")
N_NEEDS = len([n for n in NEEDS if not n.endswith("resolved")])
IDS = {"stories": "US-1…US-27"}
PHONE = IA["screens"]["SCR-1"]["budget"]


def bud(pat):
    mm = re.search(pat, PHONE)
    assert mm, f"phone budget pattern {pat!r} not found"
    return int(mm.group(1))


B_TOP, B_STRIP, B_COMP = bud(r"demo bar: (\d+) px"), bud(r"collapsed: (\d+) px"), bud(r"message field: (\d+) px")
B_ROLE = bud(r"role switch row[^:]*: (?:\*\*)?(\d+) px")
B_THREAD, B_THREAD_BANNER, B_SAFE = bud(r"thread: about (\d+) px"), bud(r"about (\d+) px while"), bud(r"takes about (\d+) px")
if B_TOP + B_ROLE + B_STRIP + B_COMP + B_THREAD != 700:
    PROBLEMS.append(f"IA phone budget parts add to {B_TOP + B_ROLE + B_STRIP + B_COMP + B_THREAD}, not 700")

# ------------------------------------------------------------------ SVGs
def summary_svg():
    boxes = [("PRD 0.4", "what to build", 20, "fact"), ("UX-1 flows", "who does what", 190, "fact"),
             ("UX-2 look + layout", "A5 · C2 · S2", 360, "decision"), ("UX-3 structure", "this page", 530, "awaiting")]
    o = ['<svg viewBox="0 0 960 250" role="img" aria-labelledby="sm-t sm-d" style="min-width:760px">',
         '<title id="sm-t">Where UX-3 sits in the UX track</title>',
         '<desc id="sm-d">Four steps run left to right: the product requirements, the flows, the look and layout choice, and this structure step. '
         'After sign-off the contracts go two ways: to the System track, where they become agreed at the design gate, and to UX-4, a clickable prototype on a mock of the contracts. UX-5 then checks the prototype.</desc>',
         '<defs><marker id="sm-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>']
    for i, (t, sub, x, kind) in enumerate(boxes):
        o.append(f'<rect class="node {kind}" x="{x}" y="30" width="150" height="62" rx="8"/>')
        o.append(f'<text class="strong" x="{x + 75}" y="58" text-anchor="middle">{E(t)}</text>')
        o.append(f'<text class="small" x="{x + 75}" y="78" text-anchor="middle">{E(sub)}</text>')
        if i < 3:
            o.append(f'<path class="arrow" d="M{x + 150},61 L{x + 170},61" marker-end="url(#sm-ah)"/>')
    # fork
    o.append('<path class="arrow" d="M680,61 L725,61 L725,150 L790,150" marker-end="url(#sm-ah)"/>')
    o.append('<path class="arrow" d="M680,61 L725,61 L725,210 L790,210" marker-end="url(#sm-ah)"/>')
    o.append('<rect class="node proposal" x="790" y="120" width="150" height="60" rx="8"/>')
    o.append('<text class="strong" x="865" y="147" text-anchor="middle">System track §6</text>')
    o.append('<text class="small" x="865" y="165" text-anchor="middle">contracts become agreed</text>')
    o.append('<rect class="node proposal" x="790" y="182" width="150" height="56" rx="8"/>')
    o.append('<text class="strong" x="865" y="207" text-anchor="middle">UX-4 prototype</text>')
    o.append('<text class="small" x="865" y="224" text-anchor="middle">on a mock of the contracts</text>')
    o.append('<text class="small" x="530" y="130">Signing UX-3 opens both of these.</text>')
    o.append('<text class="small" x="530" y="148">UX-5 (check the prototype) comes after UX-4.</text>')
    o.append('</svg>')
    return "".join(o)


def budget_svg():
    parts = [("Top bar + demo bar", B_TOP, "var(--surface-2)"), ("Role switch row", B_ROLE, "var(--lane-family)"), ("What's settled strip", B_STRIP, "var(--lane-assistant)"),
             ("Thread", B_THREAD, "var(--surface)"), ("Composer", B_COMP, "var(--lane-staff)")]
    o = ['<svg viewBox="0 0 560 300" role="img" aria-labelledby="bd-t bd-d" style="min-width:420px">',
         '<title id="bd-t">The phone screen height budget for the customer chat</title>',
         f'<desc id="bd-d">A 700 pixel tall phone screen, top to bottom: top bar and demo bar {B_TOP} pixels, the collapsed settled strip {B_STRIP}, '
         f'the thread {B_THREAD} ({B_THREAD_BANNER} while the simulated staffing banner shows), and the composer {B_COMP}. A pinned safety card takes about {B_SAFE} of the thread.</desc>']
    y, sc = 10, 280 / 700
    for name, h, fill in parts:
        hh = h * sc
        o.append(f'<rect x="20" y="{y:.1f}" width="150" height="{hh:.1f}" class="surf" style="fill:{fill}"/>')
        ty = y + 14 if name == "Thread" else y + hh / 2 + 4
        o.append(f'<text x="186" y="{ty:.1f}">{E(name)} · {h} px</text>')
        y += hh
    sy = 10 + (B_TOP + B_ROLE + B_STRIP) * sc
    o.append(f'<rect x="28" y="{sy + 4:.1f}" width="134" height="{B_SAFE * sc:.1f}" class="propzone" style="stroke:var(--awaiting)"/>')
    o.append(f'<text class="small" x="186" y="{sy + 4 + B_SAFE * sc / 2 + 4:.1f}">pinned safety card, about {B_SAFE} px of the thread</text>')
    o.append(f'<text class="small" x="186" y="{y - B_COMP * sc - 14:.1f}">thread is about {B_THREAD_BANNER} px while the staffing banner shows</text>')
    o.append('</svg>')
    return "".join(o)


def contract_svg():
    cons = CON_IDS
    sc_ids = [r["screen"] for r in UC["map"]]
    # one node per screen (the map has one row per screen/contract pair, so merge)
    screens = []
    for r in UC["map"]:
        sid = r["screen"].split(" ")[0]
        if sid not in screens:
            screens.append(sid)
    names = {r["screen"].split(" ")[0]: " ".join(r["screen"].split(" ")[1:]) for r in UC["map"]}
    edges = []
    for r in UC["map"]:
        sid = r["screen"].split(" ")[0]
        for c in r["cons"]:
            edges.append((sid, c, False))
        for c in r["extra"]:
            edges.append((sid, c, True))
    H = 30 * len(cons) + 20
    ly = {s: 24 + i * (H - 48) / (len(screens) - 1) for i, s in enumerate(screens)}
    ry = {c: 20 + i * 30 for i, c in enumerate(cons)}
    o = [f'<svg viewBox="0 0 990 {H}" role="img" aria-labelledby="cm-t cm-d" style="min-width:820px">',
         '<title id="cm-t">Contract map: screens on the left, contracts on the right</title>',
         f'<desc id="cm-d">Each of the {len(screens)} screens is joined to the contracts it reads or writes. Solid lines are the screen\'s own contracts; dashed lines are '
         'contracts it borrows for a header or an action. CON-2, the one-turn contract of the customer chat, is drawn thick: it is the main seam with the System track. The table below lists the same links with their operations.</desc>']
    for s, c, dashed in edges:
        x1, y1, x2, y2 = 250, ly[s], 640, ry[c]
        cls = "arrow"
        extra = ""
        if c == "CON-2":
            extra = ' style="stroke:var(--awaiting);stroke-width:4"'
        elif dashed:
            cls = "arrow dash"
        o.append(f'<path class="{cls}"{extra} d="M{x1},{y1:.1f} C{x1 + 200},{y1:.1f} {x2 - 200},{y2:.1f} {x2},{y2:.1f}"/>')
    for s in screens:
        o.append(f'<rect class="node" x="10" y="{ly[s] - 18:.1f}" width="240" height="36" rx="6"/>')
        o.append(f'<text class="strong" x="22" y="{ly[s] + 5:.1f}">{E(s)} · {E(names[s])}</text>')
    for c in cons:
        n = len(OPS_PER_CON[c])
        main = c == "CON-2"
        cls = "node awaiting" if main else ("node proposal" if c in ("CON-21", "CON-22") else "node")
        o.append(f'<rect class="{cls}" x="640" y="{ry[c] - 13}" width="340" height="26" rx="5"/>')
        o.append(f'<text class="{"strong" if main else ""}" x="650" y="{ry[c] + 5}">{c} · {E(short_title(UC["cons"][c]["title"]))} · {n} op{"s" if n != 1 else ""}</text>')
    o.append('</svg>')
    return "".join(o)


# ------------------------------------------------------------------ sections
HIDE = {"hint": "A decision card or fact card"}


def section_summary():
    cards = [
        (f"{len(SCREENS)} screens", "each with 8 states, every region and every flow situation", "fact", f"{S_SP}"),
        (f"{N_ROWS_STATE} state cells", f"{N_REAL} real, {len(NA)} n/a with a reason", "fact", S_SP),
        (f"{len(CON_IDS)} contracts, {len(OPS)} operations", f"OpenAPI {OA_VER}; {N_BLOCKS} reply block types on the chat contract", "fact", S_OA),
        (f"{N_NEEDS} contract needs", "raised by the screen specs, each traced to where it landed", "fact", S_UC),
        (f"{len(UC['uxr'])} System-track requests", f"{UXR_ADOPTED} adopted, {UXR_ADAPTED} adapted, {'0 rejected' if UC['rejected_none'] else 'some rejected'}", "fact", S_UC),
        (DS["tally"].split("= ")[-1].replace(" in all.", " design tokens").replace("**", ""), "colours, type, spacing, radii, lines, elevation, motion, components", "fact", S_DS),
    ]
    g = "".join(f'<article class="card" data-status="{k}"><h3>{E(t)} {badge(k)}</h3><p>{E(d)}</p><p class="src">{src_link(s)}</p></article>' for t, d, k, s in cards)
    return f'''<section aria-labelledby="sum-h" data-visual="summary"><h2 id="sum-h">At a glance</h2>
  <p class="section-sub">UX-3 turns the look you picked into exact screens and exact agreements with the backend. The picture shows where it sits. The list under it says the same thing in words.</p>
  <figure data-status="awaiting">
    <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="UX track diagram, scrolls sideways">{summary_svg()}</div>
    <figcaption>{badge("awaiting")} the order is from the ux-pipeline phases; the pick at UX-2 is {badge("decision")}.</figcaption>
    <ol class="words"><li>The requirements (PRD 0.4) fed the flows (UX-1), and the flows fed the look and layout choice (UX-2).</li>
    <li>UX-3, this page, makes that choice exact: every screen, every state, the design file and the contracts.</li>
    <li>If you sign UX-3, the contracts go to the System track and to UX-4 at the same time. UX-5 checks the prototype after that.</li></ol>
  </figure>
  <div class="grid three">{g}</div>
</section>'''


def section_story():
    return f'''<section aria-labelledby="story-h" data-visual="story"><h2 id="story-h">The story so far</h2>
  <p class="lede">Meridian Home Comfort is a fictional heating, cooling and plumbing company. We are building a chat agent that its homeowners talk to, and a staff console behind it. A homeowner writes that the heat has stopped. The agent answers from the company's own documents or books a visit. When it cannot finish the job, a person picks the case up. In the demo that person is Riley.</p>
  <div class="grid three">
    <article class="card" data-status="fact"><h3>Where UX-1 ended {badge("fact")}</h3>
      <p>UX-1 drew who uses the product and the paths they take: {len(SCREENS)} screens, twelve flows, and a first list of contracts. It was closed against PRD 0.4 on 2026-10-20 after the PRD change reopened it once.</p>
      <p class="src">{src_link(S_CK)} §4 (UX-1 gate lines).</p></article>
    <article class="card" data-status="decision"><h3>What UX-2 picked {badge("decision")}</h3>
      <p>After six directions (A1 to A6), you chose <b>A5 Service desk</b>, light mode first, with <b>C2</b> for the chat (the conversation plus a "What's settled" panel) and <b>S2</b> for the case view (queue, brief and proof, side by side). Your words: "alright we're going with A5".</p>
      <p class="src">Innocent, 2026-10-21. {src_link(S_DD)}, top status line; {src_link(S_CK)} §4b.</p></article>
    <article class="card" data-status="decision"><h3>What the System track settled {badge("decision")}</h3>
      <p>While we drew screens, the System track settled how the backend behaves, and the contracts now follow it. A reply that takes 60 seconds becomes a <code>TURN_TIMEOUT</code> card. More than 30 replies at once gets <code>BUSY</code>. Replies arrive whole, with no streaming. The demo has one clock that every screen follows.</p>
      <p class="src">Decided 2026-10-21 (section 6). {src_link(S_SP)} N-26 resolved; {src_link(S_UC)} UXR-4, UXR-13; {src_link(S_CK)} §6.</p></article>
  </div>
  <article class="card" data-status="decision" id="r48"><h3>One demo login for the whole deployment {badge("decision")}</h3>
    <p>Tonight you decided that a single demo login gates everything (PRD R-48). The contracts and screens changed to match. There is a new first screen, SCR-12, the demo login. The old staff sign-in, SCR-4, is now a role switch in the header of every screen: "Acting as" Customer, Representative, Supervisor or Owner, one click to change. The Monitoring and Evaluation pages now also sit behind the login. A new contract, CON-22, carries login and sign-out. This also closed the two questions that waited on you: the staff passcode (none, the login is the gate) and reset gating (none beyond the login).</p>
    <p class="src">Decided 2026-10-21 (PRD R-48). {src_link(S_IA)} rules table and SCR-4, SCR-12; {src_link(S_SP)} SCR-12; {src_link(S_UC)} Closed by R-48.</p></article>
  <p>Two words you will see. A <b>contract</b> is a written agreement about one request between a screen and the backend: what the screen sends, what it gets back, and every way it can fail. If a screen can show a state, some contract must be able to produce it. A <b>state</b> is how a screen looks in one situation: empty, loading, in error, and so on. There are eight standard ones.</p>
  <p>UX-3 wrote five things tonight. This page is a summary of them. Each is linked in full at the top, and the Markdown files stay the source of truth.</p>
  <p class="note" data-status="fact">{badge("fact")} Question for this gate: <b>is the information organised correctly?</b> That means the right thing is first on every screen, every state has a real answer, and every screen has a contract behind it. Sections below show each of these.</p>
</section>'''


def section_a5():
    # ---- token tables, both themes
    rows = []
    for name, t in TOK.items():
        def sw(k):
            h = t[k]
            if not h:
                return f'<span class="swatch" style="background:rgb(16 18 22/.5)"></span><code>{E(t[k + "_raw"].split(" · ")[0].strip("`"))}</code>'
            return f'<span class="swatch" style="background:{h}"></span><code>{h}</code>'
        rows.append([f"<code>--color-{E(name)}</code>", sw("light"), sw("dark"), md(t["job"])])
    tok_tbl = table(["Token", "Light", "Dark", "Its one job"], rows, caption=f"The {len(TOK)} semantic colour tokens, light and dark (design.md §4.2)", min_w=620)
    # ---- live preview panels
    def panel(mode):
        v = {k: TOK[k][mode] for k in ("canvas", "surface", "surface-rail", "surface-well", "surface-selected", "border-hair", "border-control",
                                        "customer", "text", "text-muted", "accent", "on-accent", "send", "on-send", "person", "on-person", "safety", "on-safety")}
        style = ";".join(f"--p-{k}:{h}" for k, h in v.items())
        return f'''<div class="tp" style="{style}" data-theme-preview="{mode}">
  <div class="tp-label">{mode.capitalize()}</div>
  <div class="tp-frame">
    <div class="tp-top"><b>Meridian Home Comfort</b><span>Meridian assistant · automated</span></div>
    <div class="tp-demo">Fri Oct 16, 2026 (demo date) · Nobody online</div>
    <div class="tp-body">
      <div class="tp-name"><b>Meridian assistant · automated</b> · 2:04 pm</div>
      <div class="tp-turn asst">Hi, I'm Meridian Home Comfort's automated assistant, not a person.</div>
      <div class="tp-name r"><b>You</b> · 2:05 pm</div>
      <div class="tp-turn cust">8:00 am – 12:00 pm</div>
      <div class="tp-card"><div class="tp-ch">Choose a window</div>
        <div class="tp-tiles"><span>8:00 am – 12:00 pm</span><span class="sel">✓ 12:00 pm – 4:00 pm</span><span class="taken">4:00 pm – 8:00 pm</span></div>
        <div class="tp-btnrow"><span class="tp-primary">Continue with this window</span></div></div>
      <div class="tp-name"><span class="tp-disc">R</span><b>Riley · representative (demo)</b> · 2:09 pm</div>
      <div class="tp-turn rep">I can see your request. I'll take it from here.</div>
      <div class="tp-claim"><span class="tp-tag">? Customer says · not checked</span> "It started after the storm."</div>
      <div class="tp-safe"><div class="tp-band">⚠ DANGER</div><div class="tp-safebody">1. Leave the home immediately and call 911 or your gas utility from outside.</div></div>
    </div>
    <div class="tp-comp"><span class="tp-field">Message</span><span class="tp-person">Talk to a person</span><span class="tp-send">Send</span></div>
  </div></div>'''
    # ---- type
    fam_map = {"Instrument Sans": "A5 Display", "Inter": "A5 Sans", "Geist Mono": "A5 Mono"}
    samples = {"caption": "Taken", "section": "Needs my action", "small": "Riley · representative (demo)", "ui": "Billing dispute · P3 Standard",
               "body": "Hi, I'm Meridian Home Comfort's automated assistant, not a person.", "card-title": "Choose a window",
               "name": "Meridian Home Comfort", "lead": "A representative will get back to you within 1 business day",
               "title": "Leave the home immediately", "signal": "DANGER", "code": "482913", "ref": "MHC-C-0007"}

    def spec_style(size_cell, fam_cell):
        sz = re.search(r"(\d+) / (\d+) px", size_cell)
        fam = next((f for f in fam_map if f in fam_cell), "Inter")
        wt = re.search(rf"{fam} (\d+)", fam_cell)
        st = f"font-family:'{fam_map[fam]}',system-ui,sans-serif;font-size:{sz.group(1)}px;line-height:{sz.group(2)}px;font-weight:{wt.group(1) if wt else 400}"
        tr = re.search(r"([+-]?\.\d+)em", fam_cell)
        if tr:
            st += f";letter-spacing:{tr.group(1)}em"
        if "uppercase" in fam_cell:
            st += ";text-transform:uppercase"
        return st
    trows = []
    for r in DS["type_scale"]:
        tk = r[0].strip("`").replace("--text-", "")
        trows.append([f"<code>{E(r[0].strip('`'))}</code>", E(r[1]), md(r[2]),
                      f'<span class="spec" style="{spec_style(r[1], r[2])}">{E(samples.get(tk, tk))}</span>', md(r[3])])
    type_tbl = table(["Token", "Size / line", "Family · weight · tracking", "Live specimen", "Used for"], trows, caption="The type scale (design.md §3.2), set in the real fonts", min_w=760)
    time_rows = []
    for r in DS["time_styles"]:
        ex = r[4].strip("*")
        time_rows.append([f"<code>{E(r[0].strip('`'))}</code>", E(r[1]), f'<span class="spec" style="{spec_style(r[1], r[2])};font-variant-numeric:tabular-nums">{E(ex)}</span>', md(r[3])])
    time_tbl = table(["Token", "Size / line", "Example", "Where"], time_rows, caption="The four time styles (design.md §3.3)", min_w=640)
    # ---- mint
    mint_tbl = table(["Where", "Before (look sheet)", "After (design.md)"], [[md(c) for c in r] for r in DS["mint_rows"]], caption="Mint: before and after (design.md §4.6)", min_w=620)
    # ---- control edge
    edge_rows = [r for r in DS["ui_pairs"] if r[0].startswith("`border-control`")]
    edge_tbl = table(["Pair", "Light", "Dark"], [[md(r[0]), E(r[1]), E(r[2])] for r in edge_rows], caption="The control edge, measured on each surface (design.md §4.3)", min_w=420)
    hair = [r for r in DS["ui_pairs"] if False]
    hair_row = [r for r in SRC.table_rows(SRC.section(TXT[S_DS], r"^#### Decorative lines and tints", r"^#### |^### |^## ").splitlines()) if r[0].startswith("`border-hair` on `surface`")][0]
    tex_rows = [[E(r[0]), md(r[1]), f'<span class="verdict {"watch" if r[2].strip("*") == "Watch" else "no"}">{E(r[2].strip("*"))}</span>', md(r[3])] for r in DS["texture"]]
    tex_tbl = table(["#", "Trait to avoid", "Verdict", "Why"], tex_rows, caption="House-texture check on the final spec (design.md §12)", min_w=720)
    return f'''<section aria-labelledby="a5-h"><h2 id="a5-h">A5 made exact</h2>
  <p class="section-sub">UX-2 chose a look in pictures. <code>design.md</code> turns it into numbers a developer can build from. Everything in this section is read from that file, and the contrast figures were recomputed here from the hex values (they match, see the note under the tables).</p>
  <p>A <b>token</b> is a named value, like "the colour of the customer's own messages". Components read tokens and never raw hex codes, so changing a token changes every place it is used. A5 has {E(DS["tally"].split("= ")[-1].replace(" in all.", "").replace("**", ""))} in all.</p>

  <h3 id="a5-preview">A live preview of the tokens, light and dark</h3>
  <p class="section-sub">This is not a screen. It is one small chat built only from the tokens below, so you can see how the colours work together. The two copies use the light and the dark values.</p>
  <div class="tp-pair" data-status="fact">{panel("light")}{panel("dark")}</div>
  <p class="note" data-status="fact">{badge("fact")} Sample words only. The fonts are the real A5 fonts (Instrument Sans, Inter, Geist Mono), embedded for this section. Source: {src_link(S_DS)} §4.2 and §8. The dark theme is defined and passes contrast; it has had less visual polish and is finished last, at UX-5 ({src_link(S_DS)} header).</p>

  <h3>The semantic colours</h3>
  <p class="section-sub">One row per job. A swatch with its hex is shown so the meaning does not rest on colour alone. Light is primary.</p>
  <article class="card" data-status="proposal">{tok_tbl}<p class="src">{badge("proposal")} All values are PROPOSED in design.md until you sign UX-3. Source: {src_link(S_DS)} §4.2.</p></article>

  <h3>Computed contrast</h3>
  <p class="section-sub">Contrast is how clearly text or an edge stands out from what is behind it. The web accessibility standard (WCAG 2) wants 4.5 to 1 for text and 3 to 1 for edges and icons. Every pair passes, both themes: {len(TEXT_ROWS) + len(UI_ROWS)} pairs, {TEXT_BAD + UI_BAD} failures.</p>
  <article class="card" data-status="fact"><h3>Lowest values {badge("fact")}</h3><p>{E(DS["lowest"].replace("Lowest values: ", ""))}</p>
    <p class="src">{src_link(S_DS)} §4.3. Recomputed here from the hex values in §4.2: {"every figure matches within 0.01" if not [p for p in PROBLEMS if p.startswith("design.md contrast")] else "MISMATCHES, see the report"}.</p></article>
  <div class="grid two">
    <div>{table(["Text pair (needs 4.5:1)", "Light", "Dark"], TEXT_ROWS, caption="Text pairs", min_w=380)}</div>
    <div>{table(["Edge, icon or state fill (needs 3:1)", "Light", "Dark"], UI_ROWS, caption="Edges, icons, focus rings and fills", min_w=380)}</div>
  </div>

  <h3>The type scale</h3>
  <p class="section-sub">Three typefaces with three jobs. Instrument Sans carries names, card titles, the promise and the big times. Inter carries everything you read. Geist Mono is only for references, IDs and codes. The customer chat reads at 15 px and the console at 14 px.</p>
  {type_tbl}
  {time_tbl}
  <p class="note" data-status="unknown">{badge("unknown")} <b>Not measured yet:</b> design.md estimates that "8:00 am → 12:00 pm" fits on a 360 px phone at 28 px. The estimate came from font widths, not from a rendered page. UX-4 measures it and records the result ({src_link(S_DS)} §3.3).</p>

  <h3>The mint decision</h3>
  <article class="card" data-status="proposal" id="decision-mint">
    <h3>Mint means the customer's own words and choices, and nothing else {badge("proposal")}</h3>
    <p data-part-note="story">{E(DS["mint_conflict"])}</p>
    <p>{E(DS["mint_why"])}</p>
    <div class="mintdemo" aria-label="Mint compared with the other speakers">
      <div class="tp" style="--p-surface-well:{TOK["surface-well"]["light"]};--p-customer:{TOK["customer"]["light"]};--p-surface:{TOK["surface"]["light"]};--p-person:{TOK["person"]["light"]};--p-on-person:{TOK["on-person"]["light"]};--p-text:{TOK["text"]["light"]};--p-text-muted:{TOK["text-muted"]["light"]};--p-border-hair:{TOK["border-hair"]["light"]}">
        <div class="tp-turn asst">The assistant: grey</div><div class="tp-turn cust">The customer: mint</div><div class="tp-turn rep">A representative: white, with an indigo initial</div></div></div>
    {mint_tbl}
    <p class="src">{badge("proposal")} The design file calls this a decision. It was made by the design session. Your own call on it is not recorded in any source, so it stays a proposal until you sign. Source: {src_link(S_DS)} §4.6.</p>
  </article>

  <h3>The new control-edge grey</h3>
  <article class="card" data-status="proposal">
    <h3><span class="swatch lg" style="background:{TOK["border-control"]["light"]}"></span> <code>--color-border-control</code> {TOK["border-control"]["light"]} {badge("proposal")}</h3>
    <p>The look sheet drew text fields with the thin light line used for card edges. That line is {E(hair_row[1])} against white, far under the 3 to 1 an input boundary needs (WCAG 1.4.11). So design.md adds one mid-grey that holds 3 to 1 on every surface, in both themes. It draws fields, unchecked radio rings, the dashed edge of the customer's claims and the selected queue row. Buttons and tiles keep the thin line, because their text names them.</p>
    {edge_tbl}
    <p class="src">{src_link(S_DS)} §4.3 and §13 row 2. The look sheet did not have it, so it is the one new colour of this step.</p>
  </article>

  <h3>The house-texture result</h3>
  <article class="card" data-status="fact">
    <h3>Seven traits that make a screen look like "default AI output" {badge("fact")}</h3>
    <p>{E(DS["texture_result"].replace("Result: ", "Result: "))}</p>
    {tex_tbl}
    <p class="src">{src_link(S_DS)} §12. "Watch" means the trait is partly present and the file says how it is reduced; "No" means absent.</p>
  </article>
</section>'''


# ---- callouts on the annotated screenshots
PINS = {  # key -> {region id: (x%, y%)}; hand-set against the images as viewed 2026-10-21 (regions not drawn in a shot have no pin)
    "chat-390": {"R1": (62, 7.5), "R2": (95, 16.3), "R4": (4, 21.5), "R6": (95, 46), "R7": (4, 92)},
    "chat-1280": {"R1": (40, 10.6), "R2": (50, 16.9), "R4": (86, 22), "R6": (60, 40), "R7": (45, 86.5)},
    "case-1280": {"R1": (45, 10.4), "R2": (3, 42), "R3": (45, 18.5), "R4": (59, 33.5), "R5": (62, 42), "R6": (62, 75), "R8": (80, 22),
                  "R8a": (80, 52), "R8b": (92, 32.5)},
}
SHOT_NOTES = {
    "chat-390": "R3 (staffing banner) and R5 (the pinned safety card) are state-dependent and not drawn here: this shot is the default, nobody-online state with a handoff card. The wireframe predates the demo-login decision (R-48), so it has no role switch (R2b) and no login screen; UX-4 follows the specs and design.md.",
    "chat-1280": "On a laptop the \"What's settled\" panel (R4) is always open beside the thread. R3 and R5 are state-dependent and not drawn. This wireframe predates the demo-login decision (R-48): the role switch (R2b) is not in it.",
    "case-1280": "R7 (action bar) and R9 (other cases) sit below the fold in this crop. This prototype predates the demo-login decision (R-48): it shows the old Demo staff sign-in header, not the role switch. Its promise card is tinted mint, which predates the mint decision: design.md section 4.6 reserves mint for the customer's own words and choices, so the promise becomes a plain hairline card. UX-4 follows design.md. The promise-card text here still says \"his\" (see Where the sources do not quite agree).",
}
REGION_STATES = {  # region id -> the states it changes in (checked by hand against the card's state and flow-state tables)
    "SCR-1": {"R1": ["default", "success"], "R2": ["default", "stale"], "R2b": ["default", "error", "disabled"], "R3": ["stale", "default"], "R4": ["empty", "default", "partial", "success"],
              "R5": ["success"], "R6": ["loading", "partial", "error", "success", "disabled"], "R7": ["default", "error", "disabled"]},
    "SCR-6": {"R1": ["default"], "R2": ["default"], "R3": ["default", "stale", "success"], "R4": ["default", "success"], "R5": ["default", "stale"],
              "R6": ["default", "empty", "loading", "partial"], "R7": ["disabled", "error", "success", "stale"], "R8": ["default", "partial", "stale"],
              "R8a": ["partial", "stale"], "R8b": ["success", "error", "disabled"], "R9": ["default"]},
}
SHOT_REGIONS = {"chat-390": ("SCR-1", ["R1", "R2", "R2b", "R3", "R4", "R5", "R6", "R7"]), "chat-1280": ("SCR-1", ["R1", "R2", "R2b", "R3", "R4", "R5", "R6", "R7"]),
                "case-1280": ("SCR-6", ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R8a", "R8b", "R9"])}


def pill_states(sid, states):
    return " ".join(f'<span class="stp" title="{E(SP["cards"][sid]["states"][s]["looks"][:260])}">{s}</span>' for s in states)


def section_screens():
    out = ['<section aria-labelledby="scr-h"><h2 id="scr-h">The core screens, annotated</h2>',
           '<p class="section-sub">Two screens carry most of the product: the customer chat (SCR-1) and the case view a representative works in (SCR-6). Below, the A5 wireframes with each region numbered. Each number says which contract feeds the region and which of the eight states changes it.</p>']
    if IMG:
        kinds = " and ".join(SHOT_SOURCES)
        out.append(f'<p class="note" data-status="fact">{badge("fact")} Screenshot source: <b>{E(kinds)}</b>. '
                   + ("These are the A5 wireframes in <code>docs/ux/02-concepts/wireframes/</code>." if SHOT_SOURCES == ["wireframe"] else
                      "The A5 wireframes were not ready when this page was built, so the images are cropped from the A5 look sheet (<code>2026-10-20-a5-look-sheet.html</code>). They show the approved look, not the final structure. Rebuild the page when the wireframes exist.")
                   + "</p>")
    else:
        out.append(f'<p class="note" data-status="unknown">{badge("unknown")} <b>No screenshot is available yet.</b> The A5 wireframes and the look-sheet crops were both missing when this page was built. The region lists below are complete.</p>')
    for key, label, sid in SHOTS:
        regs = SHOT_REGIONS[key][1]
        card = SP["cards"][sid]
        rmap = {r["id"].split(" ")[0]: r for r in card["regions"]}
        figs = []
        for theme in ("light", "dark"):
            if (key, theme) in IMG:
                uri, n, srcl = IMG[(key, theme)]
                pins = "".join(f'<span class="pin" style="left:{x}%;top:{y}%" aria-hidden="true">{E(rid[1:])}</span>' for rid, (x, y) in PINS[key].items())
                figs.append(f'<figure class="shot {key}"><div class="shotbox"><img src="{uri}" alt="{E(label)} in the A5 {theme} theme ({srcl}). Numbered regions are listed below." loading="lazy">{pins}</div><figcaption>{E(label)} · {theme} · {srcl}</figcaption></figure>')
        lst = []
        for rid in regs:
            r = rmap.get(rid)
            if not r:
                PROBLEMS.append(f"{sid} has no region {rid}")
                continue
            cons = re.findall(r"CON-\d+", r["con"])
            conhtml = " ".join(f'<a class="conlink" href="#con-{c[4:]}">{c}</a>' for c in cons) or "<span class='muted'>no contract (static)</span>"
            sts = REGION_STATES[sid].get(rid, [])
            for s in sts:
                assert s in card["states"], f"{sid} {rid}: unknown state {s}"
            nopin = "" if rid in PINS[key] else ' <span class="tag">not drawn in this shot</span>'
            lst.append(f'<li><span class="pinno">{E(rid[1:])}</span><div><b>{E(r["id"].split(" ", 1)[1])}</b> {conhtml}{nopin}<br><span class="regtxt">{md(r["content"])}</span><br><span class="muted">States it changes in:</span> {pill_states(sid, sts)}</div></li>')
        out.append(f'<article class="card shotcard" data-status="proposal"><h3><span>{E(label)}</span> {badge("proposal")}</h3>'
                   f'<div class="shotpair{" wide" if "1280" in key else ""}">{"".join(figs)}</div><p class="note">{E(SHOT_NOTES[key])}</p><ol class="regions">{"".join(lst)}</ol>'
                   f'<p class="src">Regions and contracts: {src_link(S_SP)} {sid} card. Hover a state name for what it looks like. Status: specified in UX-3, not signed.</p></article>')
    out.append('</section>')
    return "\n".join(out)


def phone_badge(cell):
    c = strip(cell)
    low = c.lower()
    kind = "yes" if low.startswith("yes") else "partly" if low.startswith("partly") else "collapsed" if low.startswith("collapsed") else "no" if low.startswith("no") else "other"
    lab = {"yes": "On the phone screen", "partly": "Partly on screen", "collapsed": "One line, tap to open", "no": "Not without scrolling or a tap"}.get(kind, "See note")
    rest = re.sub(r"^(yes|partly|collapsed|no)\b[,:]?\s*", "", c, flags=re.I)
    return f'<span class="ph {kind}">{lab}</span>' + (f'<span class="phnote">{E(rest[:170])}</span>' if rest else "")


def strip(s):
    return SRC.strip_md(s)


def section_ia():
    out = ['<section aria-labelledby="ia-h"><h2 id="ia-h">What comes first on each screen</h2>',
           '<p class="section-sub">For every screen, the content is sorted three ways. <b>Primary</b> is what the person came to do or see. <b>Secondary</b> supports it. <b>On demand</b> waits until they ask. Each row says why it sits at its level, and whether it is on screen without scrolling on a 390 by 700 px phone. All 11 screens are here, with every row from IA.md.</p>']
    rules = table(["Rule", "Source", "What it means for the order"], [[md(r[0]), E(r[1]), md(r[2])] for r in IA["rules"]], caption=f"Rules that apply on every screen ({len(IA['rules'])})", min_w=640)
    out.append(f'<details class="fold"><summary>Rules that apply on every screen ({len(IA["rules"])})</summary>{rules}</details>')
    out.append(f'<details class="fold"><summary>Layout breakpoints</summary>{table([E(h) for h in IA["breaks_hdr"]], [[md(c) for c in r] for r in IA["breaks"]], caption="Layout breakpoints (IA.md)", min_w=720)}</details>')
    out.append(f'<figure data-status="fact" id="ia-budget"><h3>The phone height budget for the customer chat {badge("fact")}</h3><p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p><div class="scroll" tabindex="0" aria-label="Phone height budget diagram, scrolls sideways">{budget_svg()}</div>'
               f'<ol class="words"><li>Top bar and demo bar: {B_TOP} px. The role switch row: {B_ROLE} px. The settled strip, collapsed: {B_STRIP} px.</li><li>Thread: about {B_THREAD} px ({B_THREAD_BANNER} px while the staffing banner shows). Composer: {B_COMP} px.</li><li>A pinned safety card takes about {B_SAFE} px of the thread, so the strip then reads "DANGER · Leave the home immediately".</li></ol>'
               f'<figcaption>{src_link(S_IA)}, SCR-1 height budget. The five parts add to 700 px.</figcaption></figure>')
    for sid in SCREENS:
        ia, c = IA["screens"][sid], SP["cards"][sid]
        lanes = {"Primary": [], "Secondary": [], "On demand": []}
        for r in ia["rows"]:
            lanes.setdefault(r["level"], []).append(r)
        cols = []
        for lv, rows in lanes.items():
            items = "".join(f'<li><div>{mdc(r["content"])}</div><div class="why">{mdc(r["why"])}</div><div>{phone_badge(r["phone"])}</div></li>' for r in rows)
            cols.append(f'<div class="lane lane-{lv.lower().replace(" ", "-")}"><h4>{lv} <span class="muted">({len(rows)})</span></h4><ul>{items}</ul></div>')
        extra = ""
        if ia["laptop"]:
            extra = f'<p class="note">{md(ia["laptop"])}</p>'
        out.append(f'<article class="card iacard" data-status="proposal" id="ia-{sid.lower()}"><h3><span>{sid} · {E(ia["title"])}</span> {badge("proposal")}</h3>'
                   f'<p class="muted">{E(ia["meta"])} Route: {E(c["route"])}</p><p>{E(c["purpose"].capitalize() if c["purpose"] else "")}</p>{extra}'
                   f'<div class="lanes">{"".join(cols)}</div><p class="src">{src_link(S_IA)} ({sid}); purpose and route from {src_link(S_SP)}.</p></article>')
    out.append('</section>')
    return "\n".join(out)


def section_matrix():
    head = ["Screen"] + [s.capitalize() for s in SRC.STATES]
    foot = []
    rows = []
    for sid in SCREENS:
        m = SP["matrix"][sid]
        cells = [f'<b>{sid}</b> {E(m["name"])}']
        for st in SRC.STATES:
            txt = m["cells"][st]
            if (sid, st) in NA:
                reason = SP["cards"][sid]["states"][st]["looks"]
                reason = re.sub(r"^n/a:?\s*", "", reason, flags=re.I).strip()
                foot.append((sid, st, reason))
                n = len(foot)
                cells.append(f'<span class="na" title="n/a: {E(reason)}">n/a<sup><a href="#na-{n}">{n}</a></sup></span>')
            else:
                looks = SP["cards"][sid]["states"][st]["looks"]
                cells.append(f'<span class="real" title="{E(strip(looks)[:420])}">{E(txt)}</span>')
        rows.append(cells)
    tbl = table(head, rows, cls="smatrix", caption=f"State matrix: {len(SCREENS)} screens by 8 states ({N_ROWS_STATE} cells)", scope_first=True, min_w=1000)
    notes = "".join(f'<li id="na-{i + 1}"><b>{sid} · {st}</b>: {md(r)}</li>' for i, (sid, st, r) in enumerate(foot))
    cov = table(["What the brief asked to see", "Where it shows", "State column"], [[md(r[0]), md(r[1]), md(r[2])] for r in SP["coverage"]], caption="Flow-state coverage (SCREEN_SPECS)", min_w=640)
    return f'''<section aria-labelledby="sm-h"><h2 id="sm-h">The state matrix</h2>
  <p class="section-sub">Every screen has to look right in eight situations: the normal one (default), nothing to show (empty), waiting (loading), half there (partial), something wrong (error), out of date (stale), it worked (success), and a control switched off (disabled). A cell is either a real state with a short name, or "n/a" with the reason. Hover or tap a cell to read what it looks like.</p>
  <article class="card" data-status="proposal"><h3>{len(SCREENS)} × 8 = {N_ROWS_STATE} cells: {N_REAL} real, {len(NA)} n/a {badge("proposal")}</h3>
    <p>Each real cell is backed by a row in that screen's card, and the card also lists {N_FLOWSTATES} named flow situations (for example "Slot taken at write" or "Shift ended before a claim") mapped onto these eight. The count line in SCREEN_SPECS and the {len(NA)} n/a cells were cross-checked against the cards when this page was built.</p>
    {tbl}
    <h3>Why each n/a is n/a</h3><ol class="notes">{notes}</ol>
    <p class="src">{src_link(S_SP)}, State matrix and each card's States table.</p></article>
  <h3>Where each required situation shows</h3>
  <article class="card" data-status="proposal">{cov}<p class="src">{src_link(S_SP)}, Flow-state coverage.</p></article>
</section>'''


def op_html(o):
    return f'<code class="op"><b>{o["method"]}</b> {E(o["path"])}</code> {E(o["id"])}' + (' <span class="tag">demo only</span>' if o.get("demo") else "")


def section_contracts():
    rows = []
    for r in UC["map"]:
        sid = r["screen"].split(" ")[0]
        nm = " ".join(r["screen"].split(" ")[1:])
        for c in r["cons"] + r["extra"]:
            ops = [OP_BY_ID[o] for o in r["ops"] if OP_BY_ID[o]["con"] == c]
            kind = "own" if c in r["cons"] else "borrowed"
            hi = ' class="seam"' if c == "CON-2" else ""
            rows.append([f'<b>{sid}</b> {E(nm)}', f'<a href="#con-{c[4:]}">{c}</a> {E(short_title(UC["cons"][c]["title"]))}{" <span class=tag>borrowed</span>" if kind == "borrowed" else ""}',
                         "<br>".join(op_html(o) for o in ops) or "<span class='muted'>(none of its own)</span>"])
    # a borrowed row may name ops under the primary row; show them there instead
    cmap_tbl = table(["Screen", "Contract", "Operations (method, path, operationId)"], rows, cls="cmap", caption="Screen to contract to operation", min_w=760)
    ctable = []
    for c in CON_IDS:
        cd = UC["cons"][c]
        scr = re.sub(r" · Flows:.*", "", cd["screens"])
        ctable.append([f'<span id="con-{c[4:]}"><b>{c}</b></span>', E(short_title(cd["title"])), str(len(OPS_PER_CON[c])), md(scr), md(cd["access"]), md(cd["timing"]) or "—", E(cd["status"])])
    ctbl = table(["Contract", "What it is", "Ops", "Screens", "Who may call it", "Timing budget", "Status"], ctable, caption=f"The {len(CON_IDS)} contracts", min_w=980)
    cls_hdr, cls_rows = UC["classes"]
    cls_tbl = table([md(h) for h in cls_hdr], [[md(c) for c in r] for r in cls_rows], caption="Data classes (UI_CONTRACTS)", min_w=780)
    nv = next(r for r in UC["composed"] if r[0] == "NOT_VERIFIED")
    d3 = next(r for r in cls_rows if r[0].startswith("D3"))
    need_rows = []
    for n in sorted(NEEDS, key=lambda x: (int(re.search(r"\d+", x).group()), x)):
        r = NEEDS[n]
        lid = LAND.get(n.replace(" resolved", ""))
        need_rows.append([E(n), mdc(r[1]), md(r[2]), md(r[3]) if len(r) > 3 else "", md(lid[1]) if lid else "—", md(lid[2]) if lid else ""])
    need_tbl = table(["N", "Contract it touches", "What the screen needed", "Why", "Landed in", "Note"], need_rows, caption=f"Contract needs N-1 to N-27 and where each landed", min_w=1000)
    return f'''<section aria-labelledby="cm-h"><h2 id="cm-h">The contract map</h2>
  <p class="section-sub">The picture shows which contract each screen uses. Solid lines are a screen's own contracts. Dashed lines are contracts it borrows, for a header or an action. The table below it lists the same links with the real operations from the OpenAPI file.</p>
  <figure data-status="proposal">
    <p class="scroll-hint">Diagram: swipe sideways. The table below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="Contract map diagram, scrolls sideways">{contract_svg()}</div>
    <figcaption>{badge("proposal")} {len(SCREENS)} screens, {len(CON_IDS)} contracts, {len(OPS)} operations. CON-2 is drawn thick. CON-21 and CON-22 (new) are dashed-edged. Source: {src_link(S_UC)} Contract map; operations counted from {src_link(S_OA)} (OpenAPI {OA_VER}).</figcaption>
  </figure>
  <article class="card seamcard" data-status="proposal" id="seam"><h3>CON-2 is the main seam with the System track {badge("proposal")}</h3>
    <p><b>Where this comes up.</b> Every sentence the homeowner reads, and every card they tap, travels through one request, <code>submitTurn</code>. The screen sends a message or a choice. The backend sends back a list of "blocks" (a text answer, a slot card, a safety card, a handoff card) and a <code>settled</code> summary that fills the "What's settled" panel.</p>
    <p><b>Why it is the seam.</b> The System track owns what is true inside the reply: the model, the checks, the booking, the promise. UX owns how each block looks and which states exist. CON-2 is where both must agree exactly. A change on either side shows up here first.</p>
    <ul class="tight">
      <li>{N_BLOCKS} reply block types, each with a speaker and a time. The screen never invents wording for a fixed text such as the safety card or the promise: those arrive as words from code ({src_link(S_UC)} CON-2).</li>
      <li>Deadline 60 seconds, then a <code>TURN_TIMEOUT</code> card with Try again and Talk to a person. More than 30 replies in flight gets <code>BUSY</code>. No streaming and no progress events: the reply arrives whole. The target is p95 12.5 s; SP-1 measured 10.2 s with 20 chats at once.</li>
      <li><code>settled</code> is built from the whole conversation's completed writes, never only the last turn. A completion word like "booked" may appear only when the reply's <code>writes[]</code> or <code>settled.actions</code> says it happened.</li>
      <li>Every refusal for a limit is still HTTP 200 with a <code>notice</code> and <code>settled</code>, so the panel stays true. "Talk to a person" (CON-4) works under every limit and is never disabled.</li>
    </ul>
    <p class="src">{src_link(S_UC)} CON-2 Guarantees, UXR-1 and UXR-4; {src_link(S_SP)} N-26 resolved and N-27.</p></article>
  <article class="card seamcard" data-status="fact" id="boundary"><h3>The data boundary {badge("fact")}</h3>
    <p><b>The one-time code never reaches the model.</b> It appears in exactly two places: the customer types it in a CON-2 <code>code</code> payload, and the demo inbox (CON-6) shows it. The backend compares it by code against a stored hash. The data-class table marks it {md(d3[0])}: {md(d3[2])} to the model, {md(d3[3])} in logs and traces.</p>
    <p><b>{E(nv[0])} is identical for every cause.</b> {md(re.sub(r"^\*\*Identical for every cause\*\*\s*", "", nv[2]))}. This is so that nobody can find out, by trying, whether an account exists.</p>
    <p class="src">{src_link(S_UC)} Data classes, Named errors, CON-2 Guarantees.</p></article>
  <h3>Screen to contract to operation</h3>
  <article class="card" data-status="proposal">{cmap_tbl}<p class="src">{src_link(S_UC)} Contract map; method and path from {src_link(S_OA)}.</p></article>
  <h3>All {len(CON_IDS)} contracts at a glance</h3>
  <article class="card" data-status="proposal">{ctbl}<p class="src">Every card's full reads, writes, guarantees and mock examples are in {src_link(S_UC)}. Timing budgets marked [A] are assumptions, listed further down.</p></article>
  <h3>Who may see what: the data classes</h3>
  <article class="card" data-status="proposal">{cls_tbl}<p class="src">{src_link(S_UC)} How to read this file, Data classes.</p></article>
  <h3>What each screen needed, and where it landed</h3>
  <p class="section-sub">While drawing the screens we found states the first contract list could not produce. We wrote each as a numbered need. Here is each one with the contract that now answers it.</p>
  <article class="card" data-status="proposal">{need_tbl}<p class="src">{src_link(S_SP)} Contract needs; {src_link(S_UC)} where each landed.</p></article>
</section>'''


def section_errors():
    comp = table(["Code", "Block it comes in", "What the chat does"], [[f"<code>{E(r[0])}</code>", md(r[1]), md(r[2])] for r in UC["composed"]], cls="errs", caption=f"{len(UC['composed'])} named errors the server composes (HTTP 200)", min_w=720)
    http = table(["Code", "HTTP", "Where", "What the screen does"], [[f"<code>{E(r[0])}</code>", E(r[1]), md(r[2]), md(r[3])] for r in UC["http"]], cls="errs", caption=f"{len(UC['http'])} errors for requests that could not be processed", min_w=760)
    return f'''<section aria-labelledby="er-h"><h2 id="er-h">Named errors, and what each screen does</h2>
  <p class="section-sub">An error is only useful if the screen knows what to say. The contracts keep two kinds apart. When the server decides what to say, such as "that window just went", it answers normally (HTTP 200) with an error block and the up-to-date summary. When it cannot process the request at all, it answers with an error status and never echoes the rejected value.</p>
  <article class="card" data-status="proposal"><h3>Composed outcomes (200) {badge("proposal")}</h3>{comp}
    <p class="src">{src_link(S_UC)} Named errors. Red is never used for these: only the safety card is red ({src_link(S_DS)} §4.5).</p></article>
  <article class="card" data-status="proposal"><h3>Requests the server could not process (4xx, 5xx) {badge("proposal")}</h3>{http}
    <p class="src">{src_link(S_UC)} Named errors. {md(UC["renamed"])}</p></article>
</section>'''


def section_do4():
    rows = []
    for r in UC["uxr"]:
        k = "adopted" if r[1].startswith("Adopted") else "adapted"
        rows.append([f"<b>{E(r[0])}</b>", f'<span class="outcome {k}">{md(r[1])}</span>', md(r[2])])
    t = table(["Request", "Outcome", "Reason"], rows, caption=f"DO-4 requests UXR-1 to UXR-{len(UC['uxr'])}", min_w=720)
    return f'''<section aria-labelledby="do4-h"><h2 id="do4-h">What the System track asked for (DO-4)</h2>
  <p class="section-sub">While we wrote contracts, the System track's own API design (called DO-4) asked for {len(UC["uxr"])} changes. "Adopted" means taken as asked. "Adapted" means taken with a change and a stated reason. Nothing was rejected.</p>
  <article class="card" data-status="proposal"><h3>{UXR_ADOPTED} adopted, {UXR_ADAPTED} adapted, {'0 rejected' if UC['rejected_none'] else 'see file for rejections'} {badge("proposal")}</h3>{t}
    <p class="src">{src_link(S_UC)} DO-4 requests. The System track reads these answers at its design gate (section 6).</p></article>
</section>'''


def section_decisions():
    cards = [
        ("owner", "The business owner can read cases, but not change them",
         "Every demo staff role may open any case. The owner gets it read-only, with no action buttons and a quiet line \"Read-only for the business owner role\". The first screen draft refused the owner outright.",
         f'{src_link(S_UC)} CON-12 Guarantees (orchestrator, 2026-10-21, labelled a proposal) and Other notes; {src_link(S_SP)} SCR-6 error state. Reason: the owner opens the cases behind a number (FLOW-11).',
         "If you disagree, SCR-6 shows the owner a refusal again and CON-12 returns an error for that role."),
        ("heading8", 'Brief heading 8 reads "Who they are and how to reach them"',
         "The case brief has eight fixed headings. Heading 8 is worded without a pronoun. The earlier example said \"he\" because it described one case.",
         f'{src_link(S_UC)} Other notes; {src_link(S_DS)} §8.9 heading table.',
         "If you disagree, one heading string changes in the brief and the contract's fixed text."),
        ("split", "The case header has one split button: Claim, then Resolve, with the rest in its menu",
         "While a case is unassigned the button says Claim (Claim and join when the customer is waiting in chat). Once claimed it says Resolve, and its menu holds Release, Set waiting and Close unresolved. Log a call, Log an email and Flag stay as plain buttons under the brief. This is placement only: which actions are allowed in which state did not change.",
         f'{src_link(S_DS)} §8.9 and §14 item 7 ("a layout decision made here"); {src_link(S_SP)} SCR-6 Interactions.',
         "If you disagree, the header gets a different action layout, and design.md and the SCR-6 card change. The contracts do not."),
        ("mint", "Mint means the customer's own words and choices, and nothing else",
         "On the phone the customer's messages are mint, the assistant's are grey. On the console, the old look sheet tinted the assistant's promise block mint as well. That block is now a plain hairline card, so a representative can tell the customer's words from the assistant's at a glance.",
         f'{src_link(S_DS)} §4.6 and §13 row 1; it resolves the "Mint means two things" risk in {src_link(S_DD)} (A5 section).',
         "If you disagree, the console promise block could keep a tint, and the rule \"mint is the customer\" gets two exceptions."),
        ("claimtag", 'Section 4 of the brief carries the visible tag "Customer says · not checked"',
         "What the customer claims is kept apart from what the record proves. Claims sit on a grey well with a dashed edge, carry no source chip, and wear this tag. It is one of four differences, so it survives greyscale and screen readers.",
         f'{src_link(S_SP)} SCR-6 Copy notes; {src_link(S_DS)} §4.5 rule 3 and §8.9 (the four differences).',
         "If you disagree, the tag wording changes. The dashed edge, the grey fill and the missing chip still carry the meaning."),
    ]
    out = []
    for cid, title, what, basis, ifno in cards:
        out.append(f'<article class="card" data-status="proposal" id="dec-{cid}"><h3><span>{E(title)}</span> {badge("proposal")}</h3><p>{what}</p>'
                   f'<p><b>Basis:</b> {basis}</p><p><b>If you would rather not:</b> {ifno}</p></article>')
    return f'''<section aria-labelledby="dec-h"><h2 id="dec-h">Decisions made tonight that you may want to see</h2>
  <p class="section-sub">These five calls were made while writing UX-3. None is recorded as your decision, so each is shown as a proposal with its basis. Signing UX-3 would accept all five. If one bothers you, say so and it changes without touching the rest.</p>
  <div class="grid two">{"".join(out)}</div>
</section>'''


def section_loose():
    items = [
        ("The case copy says \"he\" and \"his\" for one example case", "SCR-6 has an identity line \"He entered the code…\" and a default promise-card example \"his choice … his record\". Heading 8 was made gender-neutral. The two lines need the same treatment.", f"{S_SP} SCR-6 copy notes and default state; {S_UC} Other notes"),
        ("The emergency-line card is deliberately not red", "A card for \"someone may be in danger\" uses a heavier ink edge and its position, size and phone number for urgency, so red stays rare. The specs call this a design call for this gate.", f"{S_SP} note 8; {S_DS} §4.5"),
        ("The specs' contract lists are broader than the contract map for some screens", "The cards list header contracts such as CON-7, CON-8 and CON-10 that the contract map leaves out (it shows only the main ones plus a few borrowed). The page cross-checks both; the differences are reported to the build session.", f"{S_SP} Contracts lines; {S_UC} Contract map"),
    ]
    miss = [n for n in NEEDS if n not in LAND and not n.endswith("resolved")]
    if miss:
        items.append((f"New needs not yet in the landing table ({', '.join(miss)})", "The login pass added these needs to the screen specs. The contracts file's table of where each need landed has no row for them yet. The contracts themselves (CON-22, the reshaped CON-10) carry the answers.", f"{S_SP} Contract needs; {S_UC} Contract needs N-1…N-27"))
    g = "".join(f'<article class="card" data-status="fact"><h3>{E(t)} {badge("fact")}</h3><p>{E(d)}</p><p class="src">Seen in: {E(s)}.</p></article>' for t, d, s in items)
    return f'''<section aria-labelledby="loose-h"><h2 id="loose-h">Where the sources do not quite agree</h2>
  <p class="section-sub">We did not edit any source tonight. These are the small mismatches we found while reading them side by side. None changes a screen's structure. Each should be fixed in its owner file; the first three matter most for the prototype.</p>
  <div class="grid two">{g}</div>
</section>'''


def section_ask():
    return f'''<section aria-labelledby="ask-h"><h2 id="ask-h">Your sign-off: UX-3</h2>
  <div class="ask" data-ask="UX3-SIGN" data-status="awaiting" id="ask-ux3">
    <h2 style="color:var(--awaiting)">{badge("awaiting")} Sign UX-3: the structure</h2>
    <div class="part" data-part="context"><h3>Where this comes up in the project</h3>
      <p>A homeowner writes to the Meridian chat, and Riley picks up what the chat cannot finish. Those two people use {len(SCREENS)} screens. You chose how they should look (A5 Service desk, with C2 and S2). UX-3 is the step that says, screen by screen, what is first, what every state looks like, and what each screen asks the backend for. The five documents are the information architecture ({src_link(S_IA)}), the screen specs ({src_link(S_SP)}), the design file ({src_link(S_DS)}), and the UI contracts ({src_link(S_UC)} with {src_link(S_OA)}).</p></div>
    <div class="part" data-part="problem"><h3>The problem we're solving</h3>
      <p>We need your yes or no on whether the information is organised correctly, before anyone builds on it. Example: on the chat, the reference number and the promise to call back ("by Monday, October 19, 7:00 pm") are first, even though they arrive late in the conversation, because a homeowner writes them down. If that order is wrong, we want to hear it now.</p></div>
    <div class="part" data-part="why-hard"><h3>Why it's hard</h3>
      <p>Each document is only right if it agrees with the others. A screen state needs a contract that can produce it, and a contract needs a screen that uses it. We cross-checked what we could: all {N_ROWS_STATE} state cells, the {len(OPS)} operations, and the contrast numbers all line up. We cannot check by reading whether the order feels right to a homeowner under stress. Only you can say that.</p></div>
    <div class="part" data-part="why-asked"><h3>Why we're asking you, and what your answer changes</h3>
      <p>Signing hands the contracts to the System track, where they become agreed at the design gate and replace its draft. It also starts UX-4: the real frontend, running against a mock built from the OpenAPI file. A change after that is dearer. A changed contract reopens the System track's design step, and a changed screen means rebuilding prototype screens. Changing now costs a few edits to documents.</p></div>
    <h3>Your options</h3>
    <ol class="opts">
      <li><b>A. Sign UX-3 as written.</b> The contracts go to the System track and UX-4 starts on the mock. You gain the most time. You accept the five proposals above, the signed specs' wording (including "immediately" on the safety card), and an emergency card that is not red. <span class="rec">Recommended: nothing in the sources contradicts the structure, and the loose ends above are wording, not structure.</span></li>
      <li><b>B. Sign with changes you name.</b> Say which items (for example the mint rule, the split button, or the emergency card colour). We edit the owning file, rebuild this page and start UX-4 on the changed version. Small cost, small delay.</li>
      <li><b>C. Do not sign yet; reopen a part.</b> Name the part: the order on a screen (information architecture), a screen spec, the design file, or the contracts. That document changes first and later steps wait. A contract change also goes to the System track.</li>
    </ol>
    <p class="decision-needed"><b>Decision needed:</b> Do you sign UX-3 (the information architecture, the screen specs, design.md and the UI contracts) as written (A), with named changes (B), or not yet (C)?</p>
    <p class="src">Gate wording: {src_link(S_CK)} §4b UX-3; ux-pipeline phases.md UX-3 and the contract hand-over. Your reply gets recorded in the checklist with the date.</p>
  </div>
</section>'''


def section_not():
    wait = UC["waiting"]
    items = "".join(f"<li>{md(w)}</li>" for w in wait)
    unk_card = ""
    if UC["unknown"]:
        unk_card = (f'<article class="card" data-status="unknown"><h3>An open unknown {badge("unknown")}</h3><p>{md(UC["unknown"])}</p>'
                    f'<p class="src">{src_link(S_UC)}.</p></article>')
    else:
        unk_card = (f'<article class="card" data-status="fact"><h3>No open unknown remains in the contracts {badge("fact")}</h3>'
                    f'<p>The last one, the clock on the Monitoring page\'s "Updated" line, is now settled: it uses wall-clock time. Spend and alert timers also run on real time, and the demo clock drives the business date only. The contracts file lists this under "Settled at section 6", dated 2026-10-21.</p>'
                    f'<p class="src">{src_link(S_UC)} Settled at §6.</p></article>')
    return f'''<section aria-labelledby="not-h"><h2 id="not-h">What is not being approved here</h2>
  <div class="grid two">
    <article class="card" data-status="awaiting"><h3>The real frontend (UX-4) {badge("awaiting")}</h3>
      <p>UX-4 builds the clickable prototype in the project's own frontend folder, against a mock of these contracts. It starts only after this gate. Its measurements, such as whether "8:00 am → 12:00 pm" fits a 360 px phone, are not part of this sign-off.</p>
      <p class="src">{src_link(S_CK)} §4b UX-4; {src_link(S_DS)} §3.3.</p></article>
    <article class="card" data-status="awaiting"><h3>Verification (UX-5) {badge("awaiting")}</h3>
      <p>UX-5 checks the prototype: traceability, browser tests at 1280 and 390 px in light and dark, accessibility and a walkthrough. Dark-theme polish and the dark APCA check wait for it.</p>
      <p class="src">{src_link(S_CK)} §4b UX-5; {src_link(S_DS)} §14 item 8.</p></article>
    <article class="card" data-status="proposal"><h3>The assumptions still marked [A] {badge("proposal")}</h3>
      <p>These stay assumptions in the contracts. They are numbers to tune at build time. Signing UX-3 does not settle them. The two that waited on you, the staff passcode and the reset gating, were closed by the demo-login decision (R-48), see the story.</p>
      <ul class="tight">{items}</ul>
      <p class="src">{src_link(S_UC)} Still open.</p></article>
    {unk_card}
  </div>
</section>'''


# ------------------------------------------------------------------ page
meta_src = "\n".join(f'<meta name="review-source" content="{s}|{SHA[s]}">' for s in SOURCES)
src_rows = "\n".join(f'      <a href="{_rel(s)}">{s}</a> <span class="muted">sha {SHA[s][:8]}</span><br>' for s in SOURCES)
toc = [("sum-h", "At a glance"), ("story-h", "The story so far"), ("a5-h", "A5 made exact"), ("scr-h", "Core screens"), ("ia-h", "What comes first"),
       ("sm-h", "State matrix"), ("cm-h", "Contract map"), ("er-h", "Named errors"), ("do4-h", "DO-4 requests"), ("dec-h", "Decisions tonight"),
       ("loose-h", "Loose ends"), ("ask-h", "Your sign-off"), ("not-h", "Not approved here")]
toc_html = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc)

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meridian AI Agent — UX-3 Structure Review</title>
<meta name="review-stage" content="UX-3 · Structure (ux-pipeline §4b)">
<meta name="review-status" content="AWAITING — UX-3 sign-off requested (IA, screen specs, design.md, UI contracts); not signed">
<meta name="review-date" content="2026-10-21">
{meta_src}
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <p class="kicker">ux-pipeline · UX-3 · Structure (zero-to-hero §4b) · local review page · Markdown is the source of truth</p>
  <h1>Meridian AI service agent: is the information organised correctly?</h1>
  <div class="status-banner" role="status"><span class="st awaiting">Awaiting you</span>
    <div><strong>One decision is waiting:</strong> sign UX-3 (the information architecture, the screen specs, design.md and the UI contracts). It is in the section "Your sign-off". Nothing built after UX-3 has started.</div></div>
  <dl class="meta">
    <dt>Stage</dt><dd>UX-3 · Structure (ux-pipeline §4b). The ★ question: is the information organised correctly?</dd>
    <dt>Review date</dt><dd>2026-10-21. Built after UX-2's pick of A5 + C2 + S2 (2026-10-21).</dd>
    <dt>Sources (full documents, with hashes)</dt><dd>
{src_rows}    </dd>
    <dt>Context read</dt><dd>{src_link(S_CK, "PROJECT-CHECKLIST.md")} §4b; {src_link(S_DD, "DESIGN-DIRECTIONS.md")} (A5); <a href="2026-10-20-ux-concepts.html">the UX-2 gate record</a>.</dd>
    <dt>Refresh</dt><dd>If a source changes, this page is rebuilt (the build stops and shows the diff first) and re-checked before you rely on it.</dd>
  </dl>
  <ul class="legend" data-legend aria-label="Status legend">
    <li><span class="st fact" data-legend-item="fact">Fact</span> a source or a check says it</li>
    <li><span class="st decision" data-legend-item="decision">Your decision</span> you chose it, with a date</li>
    <li><span class="st proposal" data-legend-item="proposal">Proposal</span> Claude's draft; not yours yet</li>
    <li><span class="st unknown" data-legend-item="unknown">Unknown</span> not established</li>
    <li><span class="st awaiting" data-legend-item="awaiting">Awaiting you</span> your choice is needed</li>
  </ul>
</div></header>
<main id="main" class="wrap">
<nav class="toc" aria-label="On this page"><ol>{toc_html}</ol></nav>
{section_summary()}
{section_story()}
{section_a5()}
{section_screens()}
{section_ia()}
{section_matrix()}
{section_contracts()}
{section_errors()}
{section_do4()}
{section_decisions()}
{section_loose()}
{section_ask()}
{section_not()}
</main>
<footer class="wrap">Local file, not published. Markdown is the source of truth; this page is a synthesis built after the sources listed at the top. If any source changes, rebuild it with <code>python3 docs/artifacts/_build/ux-structure/gen_ux3.py .</code> (it stops and shows the diff first) and run the zero-to-hero <code>check_review_page.py</code> before relying on it.</footer>
</body>
</html>
'''
OUT.write_text(page)
SRC.accept_snapshots(ROOT, SOURCES, HERE / "snapshots")
print("wrote", OUT, f"{len(page) / 1e6:.2f} MB", file=sys.stderr)
if PROBLEMS:
    print("\nCROSS-SOURCE PROBLEMS:", file=sys.stderr)
    for p in PROBLEMS:
        print(" -", p, file=sys.stderr)
