"""Generate docs/artifacts/2026-10-20-ux-concepts.html: the UX-2 gate record (direction A5, concepts C2 + S2).

Run from the project root:  python3 docs/artifacts/_build/ux-concepts/gen_ux2.py . [--accept-changes]

REWRITTEN 2026-10-21 (v2): the page was a three-direction ask (A1-A3, D1-D3 pending). Innocent decided at the gate,
so it is now the record of that decision.

Parsed from the Markdown at every build: the "Idea in one line" of C2 and S2 (CONCEPTS.md) and the Feeling line of
A3-A6 (DESIGN-DIRECTIONS.md). HAND-MAINTAINED below: the story, the decision cards and his quoted words, the
timeline, the candidate and dropped-direction cards, the alt texts, the lesson and the UX-3 hand-over. So the build
keeps a snapshot of each source as last built (snapshots/); if a source changed it prints the diff and stops. Update
the hand-written parts the diff touches, then re-run with --accept-changes. Never just re-stamp the hashes.

Images: look-sheet screenshots (headless Chrome, 1280 px wide) were cropped and compressed to WebP with cwebp into
img/gate-*.webp (A3's come from its prototype). They are embedded as data URIs. Keep the page under about 6 MB.
"""
import base64
import hashlib
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import ux2_sources as SRC  # noqa: E402

ROOT = Path(sys.argv[1]).resolve()
ACCEPT = "--accept-changes" in sys.argv
OUT = ROOT / "docs/artifacts/2026-10-20-ux-concepts.html"
SOURCES = [
    "docs/design/DESIGN-DIRECTIONS.md",
    "docs/ux/02-concepts/CONCEPTS.md",
    "PROJECT-CHECKLIST.md",
]
SRC.snapshot_guard(ROOT, SOURCES, HERE / "snapshots", ACCEPT)
TXT = {s: (ROOT / s).read_text() for s in SOURCES}
SHA = {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES}
E = html.escape


def badge(s, label=None):
    names = {"fact": "Fact", "decision": "Your decision", "proposal": "Proposal",
             "unknown": "Unknown", "awaiting": "Awaiting you"}
    return f'<span class="st {s}">{label or names[s]}</span>'


def img(name):
    return "data:image/webp;base64," + base64.b64encode((HERE / "img" / f"gate-{name}.webp").read_bytes()).decode()


# ---- facts parsed from the sources (the build fails loudly if they are gone)
DD, CO, CK = (TXT[s] for s in SOURCES)
assert "going with A5" in DD and "going with A5" in CK, "the pick is no longer recorded in both sources"
assert "A3 Dispatcher" in DD and "## A6 · Branch office" in DD


def idea(text, head):
    m = re.search(rf"^### {head}.*?\n- \*\*Idea in one line:\*\* ([^\n]+)$", text, re.M | re.S)
    return m.group(1).strip().replace("**", "").replace("`", "")


IDEA = {"C2": idea(CO, "C2 ·"), "S2": idea(CO, "S2 ·")}


def feeling(did):
    m = re.search(rf"^## {did} · .+?^- \*\*Feeling:\*\* ([^\n]+)$", DD, re.M | re.S)
    return m.group(1).strip().strip('"').strip("“”")


FEEL = {d: feeling(d) for d in ("A1", "A2", "A3", "A4", "A5", "A6")}

# ---------------------------------------------------------------- summary diagram
def summary_svg():
    steps = [("A1 + A2", "built as prototypes", "dropped"), ("A3", "chosen, prototype built", "dropped"),
             ("A4", "look sheet", "dropped"), ("A5", "look sheet", "picked"), ("A6", "look sheet", "dropped")]
    o = ['<svg viewBox="0 0 1000 250" role="img" aria-labelledby="sum-t sum-d" style="max-width:1000px;min-width:900px">',
         '<title id="sum-t">How the direction was narrowed on the night of 2026-10-20</title>',
         '<desc id="sum-d">A1 and A2 were built first. He chose A2, then A3, asked for A4, then A5, and asked for A6. On 2026-10-21 he picked A5. A1, A2, A3, A4 and A6 are dropped.</desc>',
         '<defs><marker id="ahsum" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>',
         '<text x="10" y="22" class="small">THE ORDER THINGS HAPPENED (tonight to this morning)</text>']
    for i, (n, how, st) in enumerate(steps):
        x = 10 + i * 196
        cls = "node decision" if st == "picked" else "node"
        o.append(f'<rect class="{cls}" x="{x}" y="36" width="168" height="96" rx="10"/>')
        o.append(f'<text x="{x + 84}" y="74" text-anchor="middle" class="strong" style="font-size:22px">{n}</text>')
        o.append(f'<text x="{x + 84}" y="98" text-anchor="middle">{how}</text>')
        o.append(f'<text x="{x + 84}" y="118" text-anchor="middle" class="small">{"PICKED 2026-10-21" if st == "picked" else "dropped"}</text>')
        if i < len(steps) - 1:
            o.append(f'<path class="arrow" d="M{x + 170},84 L{x + 194},84" marker-end="url(#ahsum)"/>')
    o.append('<rect class="node decision" x="10" y="160" width="980" height="70" rx="10"/>')
    o.append('<text x="26" y="188" class="strong">Decision: A5 Service desk + chat concept C2 + case-view concept S2, light mode first</text>')
    o.append('<text x="26" y="212">UX-3 now turns A5 into exact tokens in design.md and writes the screen specs.</text>')
    o.append("</svg>")
    return "\n".join(o)



def chain_svg():
    boxes = [("A5 + C2 + S2", "picked 2026-10-21", "node decision"), ("UX-3", "IA, screen specs, design.md, contracts", "node proposal"),
             ("UX-4", "clickable prototype on mocks", "node proposal"), ("UX-5", "verified evidence", "node proposal")]
    o = ['<svg viewBox="0 0 1000 120" role="img" aria-labelledby="ch-t ch-d" style="max-width:1000px;min-width:760px">',
         '<title id="ch-t">What the pick feeds</title>',
         '<desc id="ch-d">The pick A5 with C2 and S2 feeds UX-3, which writes the structure and design document, then UX-4, a prototype on mocks, then UX-5, verified evidence.</desc>',
         '<defs><marker id="ahch" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>']
    for i, (a, b, c) in enumerate(boxes):
        x = 10 + i * 250
        o.append(f'<rect class="{c}" x="{x}" y="14" width="220" height="90" rx="10"/>')
        o.append(f'<text x="{x + 110}" y="50" text-anchor="middle" class="strong">{a}</text>')
        o.append(f'<text x="{x + 110}" y="76" text-anchor="middle" class="small">{b}</text>')
        if i < 3:
            o.append(f'<path class="arrow" d="M{x + 222},59 L{x + 248},59" marker-end="url(#ahch)"/>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- candidates
def cand(did, name, picked, feeling_line, shots, note, is_history=False):
    figs = "".join(f'<img src="{img(k)}" alt="{E(alt)}" width="{w}" height="{h}" loading="lazy">' for k, alt, w, h in shots)
    st = "decision" if picked else "fact"
    lab = badge("decision", "Picked") if picked else badge("fact", "Look sheet" if not is_history else "Prototype, history")
    return f'''<figure class="cand{" picked" if picked else ""}" data-status="{st}">
  <h3><span>{did} · {E(name)}</span> {lab}</h3>
  <p class="feeling">“{E(feeling_line)}”</p>
  {figs}
  <figcaption>{note}</figcaption>
</figure>'''


CANDS = "\n".join([
    cand("A4", "Account statement", False, FEEL["A4"], [
        ("a4-chat", "A4 Account statement look sheet, phone mockups in light mode: a warm porcelain ground, white panels, a muted harbour blue button, and a red square danger card on the right.", 880, 670),
        ("a4-case", "A4 Account statement look sheet, staff case view: a three-column page on a warm ground with white statement panels, label and value rows and a two-tone headline reading Billing dispute, due Mon Oct 19, 7:00 pm.", 880, 400)],
         "Warm and very soft. Dropped on the night. Look sheet: <a href=\"2026-10-20-a4-look-sheet.html\">a4-look-sheet.html</a>."),
    cand("A5", "Service desk", True, FEEL["A5"], [
        ("a5-chat", "A5 Service desk look sheet, phone mockups in light mode: a framed white app on a cool blue-grey canvas, mint blocks for the customer's messages, an emerald Save my choice button, a charcoal Send button, and a red square danger card.", 880, 665),
        ("a5-case", "A5 Service desk look sheet, staff case view: a help-desk page with a grey queue rail, a Brief and Conversation tab pair, a green Claim split button, a mint block holding the promise, and an evidence card with the invoice.", 880, 420)],
         "Cool blue-grey canvas, white hairline cards, one emerald, mint, charcoal Send. <b>This is the one he picked.</b> Look sheet: <a href=\"2026-10-20-a5-look-sheet.html\">a5-look-sheet.html</a>."),
    cand("A6", "Branch office", False, FEEL["A6"], [
        ("a6-chat", "A6 Branch office look sheet, phone mockups in light mode: a navy band with the letterspaced wordmark MERIDIAN, grey bubbles, white cards with a bank-blue Save my choice button, and an outlined Talk to a person button.", 880, 700),
        ("a6-case", "A6 Branch office look sheet, staff case view: a navy header band, a navy queue panel with white cards, a Brief tab with a Written by the assistant tag on the promise, and a bank-blue Claim button.", 880, 430)],
         "Navy band, pale grey page, bank blue. He asked for it and then picked A5. Look sheet: <a href=\"2026-10-20-a6-look-sheet.html\">a6-look-sheet.html</a>."),
])

HIST = "\n".join([
    cand("A3", "Dispatcher's log", False, FEEL["A3"], [
        ("a3-answer", "A3 Dispatcher's log clickable prototype, customer chat at laptop width: a cool grey ground, rounded grey and lilac bubbles, a source chip under the answer, and a What's settled panel on the right with Your visit, Your request and Identity.", 880, 550),
        ("a3-case", "A3 Dispatcher's log clickable prototype, staff case view: a queue on the left with P0 Safety and P3 Standard tags, the billing dispute in the centre with the promise and due time, and an Evidence panel with Sources and Conversation tabs.", 880, 550)],
         "Built as a prototype for him to confirm, after he switched to it. Prototype: <a href=\"2026-10-20-direction-A3-dispatchers-log.html\">direction-A3-dispatchers-log.html</a>.", True),
])

# ---------------------------------------------------------------- timeline
TL = [
    ("2026-10-20, evening", "decision", "He chose family A, and the first pick was A2",
     "From the company profile he picked family A, “dependable dispatch”. A1 and A2 were built as clickable prototypes. His first pick was A2: “lets go with A2 light mode and yeah you have my approval”."),
    ("2026-10-20, about 23:05 CT", "decision", "He switched to A3",
     "He looked at the built screens and changed his mind: “ill be honest i actually didnt like either of the uis you showed me A1 and A2 were very similar i want to go with A3 its nicer on the eyes”. A3 had no built screens, so an A3 prototype was built for him to confirm."),
    ("2026-10-20, about 23:20 CT", "decision", "He asked for A4",
     "The gate reopened. He wanted “styles that are utility professionally but soft on the eyes”. A4 Account statement was made as a look sheet, a quick static page, not a prototype."),
    ("2026-10-20, late", "decision", "He disliked the colours and pointed at Kirridesk",
     "As recorded in the sources, he said he did not like the colours so far and pointed at the Dribbble shot “Kirridesk: AI customer service with reply regeneration” (“more stuff like this”). That became A5 Service desk, again as a look sheet."),
    ("2026-10-21, about 00:00 CT", "decision", "He dropped everything except A5 and asked for A6",
     "“drop everything except for A5 thats really goot lets do one more”, and then he pointed at the shot “Customer Service Workspace”: “the issue will be turning it into a chatbot look”. A6 Branch office was made as a look sheet with a chatbot translation."),
    ("2026-10-21", "decision", "He picked A5",
     "“alright we’re going with A5, use parallelization as much as possible to finish (use sonnet)”. The concepts stay C2 and S2, light mode first."),
]


def timeline_html():
    return "<ol class=\"timeline\">" + "".join(
        f'<li data-status="{st}"><span class="when">{E(w)}</span><span><b>{E(t)}</b> {badge(st)}</span><span>{E(b)}</span></li>'
        for w, st, t, b in TL) + "</ol>"


# ---------------------------------------------------------------- dropped list
DROPPED = [
    ("A1", "Work order", "decision", "2026-10-20, about 23:05 CT", "“A1 and A2 were very similar”. He did not like either UI he was shown.",
     "It had been Claude’s recommendation. It was never chosen."),
    ("A2", "Route sheet", "decision", "2026-10-20, about 23:05 CT", "“A1 and A2 were very similar”. It was his first pick the same evening, then he changed it.",
     "His 12-hour-times condition for A2 still carries over (see the hand-over below)."),
    ("A3", "Dispatcher’s log", "decision", "2026-10-21, about 00:00 CT", "“drop everything except for A5”. He had picked it an hour earlier because it was “nicer on the eyes”.",
     "He gave no separate reason for dropping A3. The sources record only the narrowing to A5."),
    ("A4", "Account statement", "decision", "2026-10-21, about 00:00 CT", "“drop everything except for A5”. Before that, as recorded, he did not like the colours of the directions so far.",
     "The sources do not quote his words on A4 itself."),
    ("A6", "Branch office", "decision", "2026-10-21", "“alright we’re going with A5”. He had asked for A6 himself (“i love the color and theme on this one”) and then chose A5 over it.",
     "He gave no separate reason; the sources say only that A6 is not taken forward."),
]


def dropped_html():
    return "<ul class=\"droplist\">" + "".join(
        f'<li data-status="{st}"><b>{d} · {E(n)}</b> {badge(st, "Dropped")} <span class="muted">{E(w)}</span><br>{E(r)}<br><span class="muted">{E(x)}</span></li>'
        for d, n, st, w, r, x in DROPPED) + "</ul>"


# ---------------------------------------------------------------- page
CSS = (HERE / "ux2.css").read_text()
src_links = "<br>\n".join(
    f'<a href="../{s[5:]}"><code>{s}</code></a> · <code data-sha-for="{s}">{SHA[s][:12]}</code>' if s.startswith("docs/")
    else f'<a href="../../{s}"><code>{s}</code></a> · <code data-sha-for="{s}">{SHA[s][:12]}</code>' for s in SOURCES)
meta_src = "\n".join(f'<meta name="review-source" content="{s}|{SHA[s]}">' for s in SOURCES)

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meridian AI Agent — UX-2 Gate Record</title>
<meta name="review-stage" content="UX-2 · Concepts (ux-pipeline §4b)">
<meta name="review-status" content="DECIDED — Innocent picked A5 + C2 + S2 on 2026-10-21; UX-3 may start">
<meta name="review-date" content="2026-10-21">
{meta_src}
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <p class="kicker">ux-pipeline · UX-2 · Concepts (zero-to-hero §4b) · local gate record · Markdown is the source of truth</p>
  <h1>Meridian AI service agent: the look is chosen, A5 Service desk</h1>
  <div class="status-banner" role="status"><span class="st decision">Your decision</span>
    <div><strong>Decided 2026-10-21:</strong> direction A5 Service desk, chat concept C2, case-view concept S2, light mode first. Nothing is waiting on you here. UX-3 starts from this pick.</div></div>
  <dl class="meta">
    <dt>Stage</dt><dd>UX-2 · Concepts (ux-pipeline §4b), the gate record</dd>
    <dt>Review date</dt><dd>2026-10-21 (this page replaces the 2026-10-20 version, which asked you to choose between A1, A2 and A3)</dd>
    <dt>Sources (full documents)</dt><dd>
{src_links}</dd>
    <dt>Refresh</dt><dd>If a source changes, this page is rebuilt and re-checked before you rely on it.</dd>
  </dl>
  <ul class="legend" data-legend aria-label="Status legend">
    <li><span class="st fact" data-legend-item="fact">Fact</span> a source or a check says it</li>
    <li><span class="st decision" data-legend-item="decision">Your decision</span> you chose it, with a date</li>
    <li><span class="st proposal" data-legend-item="proposal">Proposal</span> Claude’s draft; not yours yet</li>
    <li><span class="st unknown" data-legend-item="unknown">Unknown</span> not established</li>
    <li><span class="st awaiting" data-legend-item="awaiting">Awaiting you</span> your choice is needed</li>
  </ul>
</div></header>
<main id="main" class="wrap">

<nav class="toc" aria-label="On this page"><ol>
  <li><a href="#sum-h">At a glance</a></li><li><a href="#story-h">The story so far</a></li><li><a href="#dec-h">The decision</a></li>
  <li><a href="#path-h">How we got here</a></li><li><a href="#cand-h">The final candidates</a></li><li><a href="#drop-h">Dropped</a></li>
  <li><a href="#lesson-h">The lesson</a></li><li><a href="#next-h">What UX-3 gets</a></li>
</ol></nav>

<section aria-labelledby="sum-h" data-visual="summary"><h2 id="sum-h">At a glance</h2>
  <p class="section-sub">One night, six changes of mind, one pick. The picture shows the order. The list under it says the same thing in words.</p>
  <figure data-status="decision">
    <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="Summary diagram, scrolls sideways">
{summary_svg()}
    </div>
    <figcaption>{badge("decision")} the order comes from PROJECT-CHECKLIST.md §4b and the status lines at the top of DESIGN-DIRECTIONS.md.</figcaption>
    <ol class="words"><li>A1 and A2 were built as clickable prototypes. He picked A2, then switched to A3.</li><li>He asked for A4, then pointed at a Dribbble shot, which became A5, then asked for A6.</li><li>On 2026-10-21 he picked A5. A1, A2, A3, A4 and A6 are dropped.</li></ol>
  </figure>
  <div class="grid three">
    <article class="card" data-status="decision"><h3>Direction: A5 {badge("decision")}</h3><p class="big">Service desk: hairline cards on a cool canvas, emerald and mint.</p><p class="src">2026-10-21.</p></article>
    <article class="card" data-status="decision"><h3>Chat: C2 {badge("decision")}</h3><p class="big">Thread plus a “what’s settled” panel.</p><p class="src">Unchanged since 2026-10-20.</p></article>
    <article class="card" data-status="decision"><h3>Case view: S2 {badge("decision")}</h3><p class="big">Queue, story and proof side by side.</p><p class="src">Unchanged since 2026-10-20.</p></article>
  </div>
</section>

<section aria-labelledby="story-h" data-visual="story"><h2 id="story-h">The story so far</h2>
  <p class="lede">We are building a chat agent for Meridian Home Comfort’s homeowners, and a staff console behind it. A homeowner whose air conditioner stopped writes to the chat. A representative, Riley in the demo, picks up what the chat could not finish. UX-2 asks how those screens should look.</p>
  <div class="grid three">
    <article class="card" data-status="fact"><h3>Where we started {badge("fact")}</h3>
      <p>UX-1 drew who uses the product and the paths they take. On 2026-10-20 you chose family A, “dependable dispatch”: competent, organised, on time. The family can be built in many ways, so UX-2 made several, called directions.</p>
      <p class="src">DESIGN-DIRECTIONS.md, status lines.</p></article>
    <article class="card" data-status="fact"><h3>What went wrong {badge("fact")}</h3>
      <p>We built clickable prototypes of A1 and A2 before you had seen their colours. You said they looked alike and you did not like either. We then built A3, also as a prototype, before showing you anything.</p>
      <p class="src">DESIGN-DIRECTIONS.md status lines; PROJECT-CHECKLIST.md §4b.</p></article>
    <article class="card" data-status="fact"><h3>What fixed it {badge("fact")}</h3>
      <p>From A4 on, each direction was a look sheet: a static page with the screens drawn in that direction’s colours. A look sheet is quick to make, so you could see colour first. A5 came from a shot you pointed at, and you picked it.</p>
      <p class="src">DESIGN-DIRECTIONS.md, A4 to A6.</p></article>
  </div>
  <p>Two words you will see. A <b>direction</b> is a look: colours, shapes and type, like choosing between a clipboard form and a bank statement. A <b>concept</b> is a layout: where things sit on the screen. You choose them separately. The concepts were settled first and did not change.</p>
</section>

<section aria-labelledby="dec-h"><h2 id="dec-h">The decision</h2>
  <p class="section-sub">This is the gate: which direction, which chat layout, which case-view layout. All three are answered.</p>
  <article class="card" data-status="decision" id="d-direction">
    <h3><span>Direction: A5 Service desk</span> {badge("decision")}</h3>
    <blockquote class="quote">“alright we’re going with A5, use parallelization as much as possible to finish (use sonnet)”<br><span class="muted">Innocent, 2026-10-21, UX-2 gate</span></blockquote>
    <p>A5 is the look of the Kirridesk shot you pointed at, applied to Meridian: a cool blue-grey canvas around clean white surfaces, thin-lined cards, one deep emerald for the action, mint for the customer’s side of the chat and for anything the assistant wrote, and charcoal for Send. {E(FEEL["A5"])}</p>
    <p class="src">Recorded in DESIGN-DIRECTIONS.md (top status line) and PROJECT-CHECKLIST.md §4b. Light mode comes first, as you chose earlier the same night.</p>
  </article>
  <div class="grid two">
    <article class="card" data-status="decision" id="d-chat"><h3><span>Chat: C2</span> {badge("decision")}</h3>
      <p>{E(IDEA["C2"])}</p>
      <p class="src">Unchanged since 2026-10-20 (PROJECT-CHECKLIST.md §4b: “C2 + S2 unchanged”). CONCEPTS.md.</p></article>
    <article class="card" data-status="decision" id="d-case"><h3><span>Case view: S2</span> {badge("decision")}</h3>
      <p>{E(IDEA["S2"])}</p>
      <p class="src">Unchanged since 2026-10-20 (PROJECT-CHECKLIST.md §4b). CONCEPTS.md.</p></article>
  </div>
</section>

<section aria-labelledby="path-h"><h2 id="path-h">How we got here</h2>
  <p class="section-sub">Each step is a thing you said, with the time the sources record. Quotes are exactly as written, typos included.</p>
{timeline_html()}
</section>

<section aria-labelledby="cand-h"><h2 id="cand-h">The final candidates, side by side</h2>
  <p class="section-sub">These are the three look sheets that were still in play: A4, A5 and A6. The pictures are crops of each sheet’s light-mode mockups: the customer chat on a phone, and Riley’s case view on a laptop. The words and numbers are the same in all three, so only the look differs. A5 is the one picked.</p>
  <div class="cands three">
{CANDS}
  </div>
  <h3>History: A3’s prototype screens</h3>
  <p class="section-sub">A3 was the only dropped direction that got a clickable prototype after A1 and A2. These screens are from that prototype, not from a look sheet.</p>
  <div class="cands">
{HIST}
  </div>
  <p class="note" data-status="fact">{badge("fact")} A1 and A2 stay on disk as clickable prototypes (<a href="2026-10-20-direction-A1-work-order.html">A1</a>, <a href="2026-10-20-direction-A2-route-sheet.html">A2</a>). They are not shown here, because they were dropped before the look sheets existed.</p>
</section>

<section aria-labelledby="drop-h"><h2 id="drop-h">What was dropped, and why</h2>
  <p class="section-sub">One line each, in his words where the sources have them. Where they do not, this page says so rather than guess a reason.</p>
{dropped_html()}
</section>

<section aria-labelledby="lesson-h"><h2 id="lesson-h">The lesson: look sheets before prototypes</h2>
  <article class="card" data-status="fact">
    <h3>What we learned {badge("fact")}</h3>
    <p>The first three directions each took a full clickable prototype. You judged them on colour and feel, and a prototype is a slow way to show colour. The look sheets for A4, A5 and A6 were saved about ten to fifteen minutes apart (file times 23:29, 23:45 and 23:56), and each one gave you something to react to.</p>
    <p>You said it plainly when the zero-to-hero rule was written: “screenshots or fast light mockups before showing me so i can see the colors then you can build the full full protoype”.</p>
    <p><b>The rule now.</b> Every design direction gets a quick static look sheet first: credited references, a light and a dark palette with contrast checked, and three or four mockups of the core screens on real flow copy. Only the direction you pick gets a clickable prototype. Directions must also differ at a glance, in softness, density, shape, colour temperature and type, so two of them are never mistaken for one another. Nothing unbuilt is shown next to built things.</p>
    <p class="src">zero-to-hero 1.13.0, SKILL.md and ARTIFACT-MAP.md; ux-pipeline phases.md UX-2 and templates/LOOK_SHEET.md. The file times are the look-sheet files’ own timestamps.</p>
  </article>
</section>

<section aria-labelledby="next-h"><h2 id="next-h">What the pick hands to UX-3</h2>
  <p class="section-sub">UX-3 writes the information architecture, the screen specs with every state, <code>docs/design/design.md</code> and the signed UI contracts. These items come from the A5 section of DESIGN-DIRECTIONS.md. They are a hand-over list from Claude, not decisions you have made.</p>
  <figure data-status="proposal">
    <p class="scroll-hint">Diagram: swipe sideways. The list below says the same thing.</p>
    <div class="scroll" tabindex="0" aria-label="Chain diagram, scrolls sideways">
{chain_svg()}
    </div>
    <figcaption>{badge("proposal")} the order of the UX phases is from the ux-pipeline skill; the pick is {badge("decision")}.</figcaption>
    <ol class="words"><li>The pick goes into UX-3.</li><li>UX-3 writes the structure, the design document and the contracts.</li><li>UX-4 builds a clickable prototype on mocks, and UX-5 checks it.</li></ol>
  </figure>
  <div class="grid two">
    <article class="card" data-status="proposal"><h3>Make the colours exact {badge("proposal")}</h3>
      <ul class="tight">
        <li>The shot is light only, so the dark theme is ours. Both themes are designed.</li>
        <li>The shot’s emerald with white text is 2.49 to 1 and its grey captions about 3.7 to 1. Both fail WCAG AA as used, so A5 darkens the emerald and the greys. UX-3 sets the exact values.</li>
        <li>Red stays reserved for safety, and the safety card is the only red and the only square object.</li>
      </ul></article>
    <article class="card" data-status="proposal"><h3>Check the two watch items {badge("proposal")}</h3>
      <ul class="tight">
        <li>Mint means two things: the homeowner’s own turns on the phone, and “the assistant wrote this” on the console. They never share a screen, but UX-3 should confirm it, or give the console block a different tint.</li>
        <li>A5 passes the house-texture check with four watches (items 2, 4, 5 and 7). It is also the most “SaaS help desk” of the five, so the texture has to come from the card construction and the mint and grey split, not the palette alone.</li>
      </ul></article>
    <article class="card" data-status="proposal"><h3>Update the specs {badge("proposal")}</h3>
      <ul class="tight">
        <li>Reply cards become thin-lined cards with tinted header rows. The slot card becomes day tabs with mint-selected tiles. The handoff becomes a “Your request” card with a mono reference.</li>
        <li>The case view header gains the mono reference, a reason pill and a green “Claim” split button. The promise moves into a mint block marked as written by the assistant.</li>
        <li>The old A2 mono-caps labels in SCREEN_SPECS.md become sentence-case labels. Times keep your earlier condition: 12-hour, like “7:00 pm”.</li>
      </ul></article>
    <article class="card" data-status="proposal"><h3>Do not carry over from the shots {badge("proposal")}</h3>
      <ul class="tight">
        <li>Thinking-time timers, typing dots and any chat timer or wait estimate: we cannot measure them and the honesty rules forbid them.</li>
        <li>The notification red, red and green delta numbers, the “Auto Reply” toggle, “Regenerate Reply” and tone controls, and the thumbs ratings.</li>
        <li>A face or robot for the assistant. Its mark is a plain mint square.</li>
      </ul></article>
  </div>
  <div class="notasked" data-status="unknown"><p>{badge("unknown")} <b>Not established:</b> the final colour values, the contract set (CON-1 to CON-20 stay drafts until UX-3 signs them), and the real frontend, which UX-4 builds on mocks of the contracts. Nothing on this page approves them. The sources do not yet record a built A5 prototype, so UX-3 works from the look sheet and the C2 and S2 wireframes.</p></div>
</section>
</main>
<footer class="wrap">Local file, not published. Markdown is the source of truth; this page is a synthesis built after the three source files. If any source changes, rebuild it with <code>python3 docs/artifacts/_build/ux-concepts/gen_ux2.py .</code> (it stops and shows the diff first) and run the zero-to-hero <code>check_review_page.py</code> before relying on it.</footer>
</body>
</html>
'''
OUT.write_text(page)
SRC.accept_snapshots(ROOT, SOURCES, HERE / "snapshots")
print("wrote", OUT, f"{len(page) / 1e6:.2f} MB")
