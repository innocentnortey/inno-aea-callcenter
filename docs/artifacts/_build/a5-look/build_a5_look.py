"""Build the A5 look sheet: reference shots, palette swatches and static mockups (UX-2, quick look before any prototype).

Run from anywhere: python3 docs/artifacts/_build/a5-look/build_a5_look.py
Same four mockups and the same copy as the A4 sheet (build_a4_look.py), so only the look changes.
Palette values are sampled from Innocent's pick (dr-25, Kirridesk) and its kin with Pillow, then adjusted only where
a text pair failed WCAG AA. UX-3 design.md makes them exact. The build fails if any text pair is under 4.5:1.
"""
import base64
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # docs/
REFS = ROOT / "design" / "references"
OUT = ROOT / "artifacts" / "2026-10-20-a5-look-sheet.html"

SHOTS = [
    ("dr-25-kirridesk-ai-customer-service.jpg", "Kirridesk – AI customer service with reply regeneration", "Bagus Fikri for Fikri Studio", "https://dribbble.com/shots/27624722-Kirridesk-AI-customer-service-with-reply-regeneration", "Your pick. Blue-grey canvas framing a white app; mint AI draft block; deep-green primary; charcoal secondary; name lines instead of bubbles"),
    ("dr-26-kirridesk-chat-widget.jpg", "KirriDesk – Chat Widget for SaaS Customer Service", "Fikri Studio", "https://dribbble.com/shots/23066276-KirriDesk-Chat-Widget-for-SaaS-Customer-Service-Management", "The customer-facing side of the same system: grey assistant bubbles, mint customer bubbles, option tiles, charcoal Send"),
    ("dr-27-kirridesk-auto-reply-activity.jpg", "Kirridesk – AI Auto Reply Activity", "Fikri Studio", "https://dribbble.com/shots/27469681-Kirridesk-AI-Auto-Reply-Activity-in-SaaS-Customer-Service", "The assistant's steps as a checked list in a hairline card; 'Press to take over and reply'"),
    ("dr-28-kirridesk-refund-details.jpg", "KirriDesk – AI Suggestions in SaaS Customer Service", "Fikri Studio", "https://dribbble.com/shots/27451034-KirriDesk-AI-Suggestions-in-SaaS-Customer-Service", "Reference header with a status word; label-over-value rows; a totals block"),
    ("dr-29-kirridesk-conversation-summary.jpg", "KirriDesk – AI Conversation Summary", "Fikri Studio", "https://dribbble.com/shots/27473219-KirriDesk-AI-Conversation-Summary-in-SaaS-Customer-Service", "Summary in a tinted block marked 'Not visible to' the customer; a mint 'Waiting for…' line"),
    ("dr-30-ai-support-analytics-green.jpg", "AI Customer Support Analytics Dashboard", "achmadkikikarisma", "https://dribbble.com/shots/27535301-AI-Customer-Support-Analytics-Dashboard", "Same green-on-white mood from another designer: white cards on a pale grey canvas, one green action"),
    ("dr-31-myalice-multichannel-inbox.jpg", "MyAlice Multichannel Inbox Redesign", "Shah Md. Sakil", "https://dribbble.com/shots/20506922-MyAlice-Multichannel-Inbox-Redesign", "Mint 'Close Chat' button; system events as quiet centred lines in the thread"),
    ("dr-32-myalice-order-creation.jpg", "MyAlice Inbox Order Creation", "Shah Md. Sakil", "https://dribbble.com/shots/20537424-MyAlice-Inbox-Order-Creation", "Green primary beside a hairline secondary; label-value summary rows"),
    ("dr-33-agento-customer-service-inbox.jpg", "AI Agent: Customer Service Dashboard", "Mohammad Saju", "https://dribbble.com/shots/26510156-AI-Agent-Customer-Service-Dashboard", "White three-pane inbox on a cool grey canvas; profile facts as right-aligned rows"),
    ("dr-34-keitoto-mobile-inbox-thread.jpg", "Customer Support Dashboard: Inbox & Thread Collaboration", "Keitoto", "https://dribbble.com/shots/26778695-Customer-Support-Dashboard-Inbox-Thread-Collaboration", "The same help-desk construction held at phone width"),
]

# Sampled from dr-25 / dr-26 (Pillow): canvas #E5E9F0, app #FFFFFF, rail #F5F6F7, pills #F3F5F7, AI draft #E2F8EF,
# charcoal button #202629, avatar indigo #2A2663, ink ~#101216, green #00BC6F, captions #7D878E-#869096.
# Adjusted for contrast: primary #00BC6F -> #007847 (same hue; white on #00BC6F is only 2.49:1);
# ink2 #7D878E -> #5B656D (the shot's captions are ~3.7:1 on white).
LIGHT = {
    "ground": "#E5E9F0", "panel": "#FFFFFF", "rail": "#F5F6F7", "well": "#F3F5F7", "selected": "#E5E9F0",
    "hair": "#E3E7EB", "mint": "#E2F8EF", "mint-edge": "#B4EDD5",
    "ink": "#101216", "ink2": "#5B656D", "primary": "#007847", "on-primary": "#FFFFFF", "signal": "#00BC6F",
    "charcoal": "#202629", "on-charcoal": "#FFFFFF", "person": "#2A2663", "on-person": "#FFFFFF",
    "danger": "#B42318", "on-danger": "#FFFFFF",
}
DARK = {
    "ground": "#0B0F12", "panel": "#151A1E", "rail": "#11161A", "well": "#20272C", "selected": "#2A3238",
    "hair": "#2C343A", "mint": "#0F3326", "mint-edge": "#17513C",
    "ink": "#E9EDF0", "ink2": "#A7B1B9", "primary": "#00BC6F", "on-primary": "#03140C", "signal": "#00BC6F",
    "charcoal": "#DDE3E8", "on-charcoal": "#101216", "person": "#A9A4F0", "on-person": "#14123A",
    "danger": "#C8312F", "on-danger": "#FFFFFF",
}


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# Every pair where text actually sits in the mockups. All must be >= 4.5:1.
TEXT_PAIRS = [("ink", "ground"), ("ink", "panel"), ("ink", "rail"), ("ink", "well"), ("ink", "mint"), ("ink", "selected"),
              ("ink2", "ground"), ("ink2", "panel"), ("ink2", "rail"), ("ink2", "well"), ("ink2", "mint"),
              ("primary", "panel"), ("primary", "mint"), ("on-primary", "primary"), ("on-charcoal", "charcoal"),
              ("on-person", "person"), ("on-danger", "danger")]
# Non-text parts (control edges, the safety band against the page) need 3:1.
UI_PAIRS = [("primary", "panel"), ("primary", "mint"), ("danger", "panel"), ("charcoal", "panel")]


def contrast_rows(pal):
    out = []
    for fg, bg in TEXT_PAIRS:
        r = ratio(pal[fg], pal[bg])
        ok = "AA text" if r >= 4.5 else "FAIL"
        out.append(f"<tr><td>{fg} on {bg}</td><td class='num'>{r:.2f}:1</td><td>{ok}</td></tr>")
    for fg, bg in UI_PAIRS:
        r = ratio(pal[fg], pal[bg])
        ok = "AA UI part" if r >= 3 else "FAIL"
        out.append(f"<tr class='ui'><td>{fg} edge on {bg}</td><td class='num'>{r:.2f}:1</td><td>{ok}</td></tr>")
    return "".join(out)


def swatches(pal):
    names = ["ground", "panel", "rail", "well", "hair", "mint", "ink", "ink2", "primary", "charcoal", "person", "danger"]
    return "".join(f"<div class='sw'><span style='background:{pal[n]}'></span><b>{n}</b><code>{pal[n]}</code></div>" for n in names)


def img(name):
    data = base64.b64encode((REFS / name).read_bytes()).decode()
    return f"data:image/jpeg;base64,{data}"


def css_vars(pal):
    return ";".join(f"--{k}:{v}" for k, v in pal.items())


# --- tiny inline icons (stroke = currentColor) ---
def ico(path, size=16):
    return (f"<svg class='i' width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            f"stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>{path}</svg>")


I_BACK = ico("<path d='M15 18l-6-6 6-6'/>")
I_HEAD = ico("<path d='M4 14v-2a8 8 0 0 1 16 0v2'/><rect x='3' y='14' width='4' height='6' rx='1.5'/><rect x='17' y='14' width='4' height='6' rx='1.5'/>")
I_CAL = ico("<rect x='3.5' y='5' width='17' height='15' rx='2'/><path d='M3.5 10h17M8 3v4M16 3v4'/>")
I_CLOCK = ico("<circle cx='12' cy='12' r='8.5'/><path d='M12 7.5V12l3 2'/>")
I_TICKET = ico("<path d='M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4z'/><path d='M14 7v10' stroke-dasharray='2 2'/>")
I_COPY = ico("<rect x='8' y='8' width='12' height='12' rx='2'/><path d='M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3'/>", 14)
I_CHECK = ico("<path d='M5 12.5l4.5 4.5L19 7.5'/>", 14)
I_WARN = ico("<path d='M12 3.5L2.5 20h19z'/><path d='M12 10v4.5M12 17.2v.3'/>", 18)
I_SPARK = ico("<path d='M12 4v4M12 16v4M4 12h4M16 12h4M7 7l2 2M15 15l2 2M17 7l-2 2M9 15l-2 2'/>", 14)
I_DOC = ico("<path d='M7 3.5h7l4 4V20.5H7z'/><path d='M14 3.5v4h4M10 12h5M10 15.5h5'/>", 14)
I_CHEV = ico("<path d='M6 9l6 6 6-6'/>", 14)
MARK = f"<span class='mark' aria-hidden='true'>{ico('<path d=\"M5 7.5h14v9H5z\"/><path d=\"M9 11.5h6\"/>', 14)}</span>"

TOP = f"""<div class="topbar"><span class="back">{I_BACK}</span>{MARK}<div><b>Meridian Home Comfort</b><span>Automated assistant</span></div></div>"""
TOP_REF = f"""<div class="topbar"><span class="back">{I_BACK}</span>{MARK}<div><b>Meridian Home Comfort</b><span>Automated assistant · Reference <code class="mono">MHC-C-0007</code></span></div></div>"""
DEMO = '<div class="demo">Fri Oct 16 · demo date · nobody online</div>'
DOCK = f"""<div class="dock"><div class="opt person">{I_HEAD} Talk to a person</div><div class="composer"><span>Type a message</span><b class="send">Send</b></div></div>"""

PHONE_SLOTS = f"""
<div class="phone">{TOP}{DEMO}
<div class="log">
 <p class="cap right"><b>You</b> · 2:03 pm</p><div class="me">My AC stopped cooling. Can someone come out? I'm in Kyle, 78640.</div>
 <p class="cap">{MARK}<b>Meridian assistant</b> · automated · 2:04 pm</p>
 <div class="ai">Here are the arrival windows in your area this week. You only pay the diagnostic fee if you book.</div>
 <div class="card">
  <div class="cardhead">{I_CAL}<b>Choose a window</b><span>this week</span></div>
  <div class="tabs"><span>Mon <b class="num">19</b></span><span class="on">Tue <b class="num">20</b></span><span>Wed <b class="num">21</b></span><span>Thu <b class="num">22</b></span></div>
  <div class="wins"><span>8:00 am – 12:00 pm</span><span class="taken"><s>12:00 – 4:00 pm</s><i>Taken</i></span><span class="pick">{I_CHECK}1:00 – 5:00 pm</span><span>4:00 – 7:00 pm</span></div>
  <div class="row"><span>Diagnostic visit</span><b class="num">$89</b></div>
  <button class="pri">Continue with this window</button>
  <p class="fine">Windows are shown, not held. Members' fees appear after the code.</p>
 </div>
</div>{DOCK}</div>"""

PHONE_HANDOFF = f"""
<div class="phone">{TOP_REF}{DEMO}
<div class="log">
 <p class="cap">{MARK}<b>Meridian assistant</b> · automated · 2:14 pm</p>
 <div class="ai">I can't change or remove charges, but a person can review this with you.</div>
 <div class="card">
  <div class="cardhead">{I_TICKET}<b>Your request</b><span class="ref"><code class="mono">MHC-C-0007</code>{I_COPY}</span></div>
  <div class="cardbody">
  <h3>A representative will get back to you within 1 business day.</h3>
  <div class="row"><span>Due</span><b class="num">Mon Oct 19, 7:00 pm</b></div>
  <div class="row"><span>Status</span><b><span class="tag">{I_CLOCK} Waiting for a representative</span></b></div>
  <p class="q">We'll follow up by email unless you'd prefer a phone call.</p>
  <div class="choices"><span class="on"><em class="radio"></em>Email<small>the address on your account</small></span><span><em class="radio"></em>Phone call<small>the number ending in 02</small></span></div>
  <button class="pri">Save my choice</button>
  </div>
 </div>
</div>{DOCK}</div>"""

PHONE_SAFETY = f"""
<div class="phone dim">{TOP}
<div class="safety" role="alert"><div class="band">{I_WARN} DANGER</div>
 <ol><li>Leave the home immediately.</li><li>Call 911 or your gas utility from outside.</li></ol>
 <p>Don't flip any light switches, open windows near the furnace, or restart any equipment.</p></div>
<p class="quiet">Once you're outside and safe, you can leave a number here if you'd like.</p>
<div class="log faded"><p class="cap right"><b>You</b> · 2:31 pm</p><div class="me">The kitchen smells like rotten eggs</div></div>
{DOCK}</div>"""

CONSOLE = f"""
<div class="console"><div class="app">
 <aside class="q"><div class="who"><span class="disc">R</span><div><b>Riley</b><small>Representative (demo)</small></div></div>
  <h4>Needs attention first</h4>
  <div class="qrow"><b>Gas smell reported in chat</b><span class="tag">{I_WARN} Safety</span><small>Omar Patel · <code class="mono">MHC-C-0008</code> · no due time</small></div>
  <h4>By due time</h4>
  <div class="qrow"><b>Refund request</b><span class="tag strong">{I_CLOCK} Overdue</span><small>Linda Foster · <code class="mono">MHC-C-0005</code> · Thu 7:00 pm</small></div>
  <div class="qrow sel"><b>Billing dispute · INV-204411</b><span class="tag">P3 Standard</span><small>Omar Patel · <code class="mono">MHC-C-0007</code> · Due Mon 7:00 pm, in 3 days</small></div>
 </aside>
 <section class="main">
  <div class="bar"><code class="mono id">MHC-C-0007</code><span class="titlepill">Billing dispute · due Mon Oct 19, 7:00 pm</span><span class="split"><b>Claim</b><i>{I_CHEV}</i></span></div>
  <div class="tabs2"><span class="on">Brief</span><span>Conversation</span></div>
  <div class="cols">
  <div class="b">
   <div class="draft"><div class="dhead">{I_SPARK}<b>Promise shown to the customer</b></div>
    <p class="big">A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.</p>
    <div class="row"><span>Follow up by</span><b>Phone, his choice</b></div><div class="row"><span>Best time</span><b>Mornings</b></div></div>
   <div class="sec"><h5>What we know for sure</h5>
    <div class="row"><span>Invoice INV-204411</span><b class="num">$478.00 · unpaid</b></div>
    <div class="row"><span>After-hours dispatch on invoice</span><b class="num">$144.00</b></div>
    <div class="row"><span>Fee schedule, Jan 1 2026</span><b class="num">$149.00</b></div>
    <div class="claims"><p class="lbl">Customer says · not checked</p><p>The tech said it would be $89 to come out.</p></div></div>
  </div>
  <div class="e"><h4>Evidence</h4><div class="sec"><p class="lbl">{I_DOC} Invoice INV-204411</p>
   <div class="row"><span>What the AI saw · 2:10 pm</span><b class="num">$478.00</b></div><div class="row"><span>Now · 2:20 pm</span><b class="num">$478.00</b></div>
   <p class="fine ok">{I_CHECK} No change since the snapshot.</p></div></div>
  </div>
 </section>
</div></div>"""

CSS = """
:root{--page-bg:#EEF1F5;--page-ink:#101216;--page-ink2:#5B656D;--page-card:#FFFFFF;--page-hair:#E3E7EB;--page-link:#007847}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--page-bg:#0B0F12;--page-ink:#E9EDF0;--page-ink2:#A7B1B9;--page-card:#151A1E;--page-hair:#2C343A;--page-link:#00BC6F}}
:root[data-theme="dark"]{--page-bg:#0B0F12;--page-ink:#E9EDF0;--page-ink2:#A7B1B9;--page-card:#151A1E;--page-hair:#2C343A;--page-link:#00BC6F}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 Inter,system-ui,-apple-system,'Segoe UI',sans-serif;background:var(--page-bg);color:var(--page-ink);font-feature-settings:'cv11'}
.page{max-width:1240px;margin:0 auto;padding:24px 16px 64px}
h1,h2,h3,h4,h5{font-family:'Instrument Sans',Inter,system-ui,sans-serif;font-stretch:96%}
h1{font-weight:600;font-size:30px;margin:0 0 4px;letter-spacing:-.01em}.lede{color:var(--page-ink2);margin:0 0 24px;max-width:72ch}
section.s{margin:36px 0}section.s>h2{font-size:20px;margin:0 0 4px;font-weight:600}.note{color:var(--page-ink2);margin:0 0 14px;max-width:82ch}
.badge{display:inline-block;background:var(--page-card);border:1px solid var(--page-hair);border-radius:6px;padding:2px 8px;font-size:13px}
code{font-family:'Geist Mono',ui-monospace,Menlo,monospace;font-size:.92em}
.num{font-variant-numeric:tabular-nums}
.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}
.shot{margin:0;background:var(--page-card);border:1px solid var(--page-hair);border-radius:12px;overflow:hidden}
.shot.first{grid-column:1/-1}.shot.first img{max-height:640px;object-fit:contain;background:#E5E9F0}
.shot img{width:100%;display:block}.shot figcaption{padding:10px 12px;font-size:13px}.shot .why{color:var(--page-ink2)}.shot a{color:var(--page-link);word-break:break-all;font-size:12px}
.palettes{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.pal{border-radius:16px;padding:16px;border:1px solid var(--page-hair)}.pal h3{margin:0 0 10px;font-size:16px}
.sws{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.sw{font-size:12px;display:flex;flex-direction:column;gap:2px;min-width:0}
.sw span{height:40px;border-radius:8px;box-shadow:inset 0 0 0 1px rgba(127,127,127,.25)}.sw code{opacity:.85;font-size:11px}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:12px}td{padding:3px 6px;border-top:1px solid rgba(127,127,127,.22)}tr.ui td{font-style:italic}
.mocks{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
.i{flex:none;vertical-align:-3px}
/* ---------- mockup system: every container sets its own colour from the palette ---------- */
.phone{color:var(--ink);background:var(--panel);width:360px;max-width:100%;border-radius:28px;overflow:hidden;border:6px solid var(--ground);box-shadow:0 0 0 1px var(--hair);display:flex;flex-direction:column;min-height:740px;font-size:15px}
.phone .mono,.console .mono{white-space:nowrap;font-family:'Geist Mono',ui-monospace,Menlo,monospace;font-size:.9em;color:var(--ink)}
.topbar{color:var(--ink);background:var(--panel);padding:12px 14px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--hair)}
.topbar div{display:flex;flex-direction:column;line-height:1.3}.topbar b{font:600 16px 'Instrument Sans',Inter,sans-serif}.topbar span{font-size:12.5px;color:var(--ink2)}
.back{display:inline-flex;width:30px;height:30px;border-radius:8px;background:var(--well);align-items:center;justify-content:center;color:var(--ink)}
.mark{display:inline-flex;width:24px;height:24px;border-radius:7px;background:var(--mint);color:var(--primary);align-items:center;justify-content:center;flex:none;box-shadow:inset 0 0 0 1px var(--mint-edge)}
.topbar .mark{width:30px;height:30px;border-radius:8px}
.demo{color:var(--ink2);background:var(--well);font-size:12px;text-align:center;padding:6px 8px}
.log{color:var(--ink);padding:10px 14px;flex:1}
.cap{font-size:12px;color:var(--ink2);margin:14px 0 5px;display:flex;align-items:center;gap:6px}.cap b{color:var(--ink);font-weight:600}.cap .mark{width:18px;height:18px;border-radius:5px}.cap.right{justify-content:flex-end}
.ai{color:var(--ink);background:var(--well);border-radius:4px 12px 12px 12px;padding:10px 12px;margin:0 36px 10px 0}
.me{color:var(--ink);background:var(--mint);border-radius:12px 4px 12px 12px;padding:10px 12px;margin-left:56px}
.card{color:var(--ink);background:var(--panel);border:1px solid var(--hair);border-radius:12px;overflow:hidden;margin:6px 0 4px}
.cardhead{display:flex;align-items:center;gap:8px;padding:9px 12px;background:var(--rail);border-bottom:1px solid var(--hair);font-size:14px;color:var(--ink)}
.cardhead .i{color:var(--primary)}.cardhead span{margin-left:auto;color:var(--ink2);font-size:13px;display:inline-flex;align-items:center;gap:6px}
.cardhead .ref{color:var(--ink2)}
.card>.tabs,.card>.wins,.card>.row,.card>.pri,.card>.fine{margin-left:12px;margin-right:12px}.cardbody{padding:4px 12px 12px}
.tabs{display:flex;gap:0;border-bottom:1px solid var(--hair);margin-top:4px}.tabs span{flex:1;text-align:center;padding:8px 0 7px;font-size:13px;color:var(--ink2);border-bottom:2px solid transparent;margin-bottom:-1px}
.tabs b{display:block;font-size:16px;color:var(--ink);font-weight:500}.tabs .on{color:var(--ink);border-bottom-color:var(--primary);font-weight:600}.tabs .on b{font-weight:700}
.wins{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:10px}
.wins span{color:var(--ink);background:var(--panel);border:1px solid var(--hair);border-radius:8px;padding:9px 6px;font-size:13.5px;font-variant-numeric:tabular-nums;text-align:center;display:flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap}
.wins .taken{background:var(--well);border-color:var(--well);color:var(--ink2)}.wins .taken s{text-decoration-thickness:1px}.wins .taken i{flex-basis:100%;font-style:normal;font-size:12px;font-weight:600;color:var(--ink2)}
.wins .pick{background:var(--mint);border:2px solid var(--primary);padding:8px 5px;font-weight:600}.wins .pick .i{color:var(--primary)}
.row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px dashed var(--hair);font-size:14px;color:var(--ink)}.row:last-child{border-bottom:0}.row>span{color:var(--ink2)}.row b{font-weight:600;text-align:right}
.tag{display:inline-flex;align-items:center;gap:4px;background:var(--well);color:var(--ink);border-radius:6px;padding:2px 7px;font-size:12.5px;font-weight:600;white-space:nowrap}.tag.strong{background:var(--selected);box-shadow:inset 0 0 0 1px var(--ink2)}
.cardbody h3{font:600 18px/1.3 'Instrument Sans',Inter,sans-serif;margin:8px 0 6px;color:var(--ink)}
.q{font-size:14px;margin:10px 0 6px;color:var(--ink)}.choices{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.choices span{color:var(--ink);background:var(--panel);border:1px solid var(--hair);border-radius:8px;padding:9px 10px;font-weight:600;font-size:14px;position:relative;padding-left:32px}
.choices small{display:block;font-weight:400;color:var(--ink2);font-size:12px}.choices .on{background:var(--mint);border:2px solid var(--primary);padding:8px 9px 8px 31px}
.radio{position:absolute;left:10px;top:12px;width:14px;height:14px;border-radius:50%;border:1.5px solid var(--ink2)}.on .radio{border:4px solid var(--primary)}
.pri{margin-top:12px;width:100%;height:44px;border:0;border-radius:8px;background:var(--primary);color:var(--on-primary);font:600 15px Inter,system-ui,sans-serif}
.card>.pri{width:calc(100% - 24px)}
.fine{font-size:12px;color:var(--ink2);margin:8px 12px 12px}.fine.ok{margin:8px 0 0;display:flex;gap:4px;align-items:center;color:var(--ink)}
.dock{color:var(--ink);background:var(--panel);padding:8px 12px 14px;border-top:1px solid var(--hair)}
.opt{display:inline-flex;align-items:center;gap:6px;background:var(--panel);border:1px solid var(--hair);border-radius:8px;padding:6px 10px;font-size:13.5px;font-weight:600;color:var(--ink);margin-bottom:8px}
.composer{display:flex;align-items:flex-end;justify-content:space-between;background:var(--well);border-radius:10px;padding:10px 10px 10px 12px;min-height:72px}.composer span{color:var(--ink2);font-size:14px;align-self:flex-start}
.send{background:var(--charcoal);color:var(--on-charcoal);border-radius:7px;padding:7px 16px;font-size:13.5px}
.safety{color:var(--ink);background:var(--panel);margin:0;border-bottom:4px solid var(--danger)}
.band{background:var(--danger);color:var(--on-danger);font:700 15px 'Instrument Sans',Inter,sans-serif;letter-spacing:.1em;padding:10px 16px;display:flex;align-items:center;gap:8px}
.safety ol{margin:14px 0 4px;padding:0 16px 0 38px;font:600 20px/1.35 'Instrument Sans',Inter,sans-serif;color:var(--ink)}.safety li{margin-bottom:4px}
.safety p{padding:0 16px 16px;margin:8px 0 0;font-size:15px;color:var(--ink)}
.quiet{font-size:13px;color:var(--ink2);padding:12px 16px;margin:0}.faded{opacity:.4}
.phone.dim .dock{opacity:.55}
/* console */
.console{color:var(--ink);background:var(--ground);border-radius:20px;padding:18px;width:100%}
.app{color:var(--ink);background:var(--panel);border-radius:16px;display:grid;grid-template-columns:270px 1fr;overflow:hidden;box-shadow:0 0 0 1px var(--hair);font-size:14px;min-height:460px}
aside.q{color:var(--ink);background:var(--rail);border-right:1px solid var(--hair);padding:14px 10px}
.who{display:flex;gap:10px;align-items:center;padding:0 6px 12px;border-bottom:1px solid var(--hair);margin-bottom:6px}.who div{display:flex;flex-direction:column;line-height:1.25}.who small{color:var(--ink2);font-size:12px}
.disc{width:32px;height:32px;border-radius:50%;background:var(--person);color:var(--on-person);display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:13px}
.console h4{font-size:12px;color:var(--ink2);margin:12px 6px 6px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;font-family:Inter,sans-serif}
.qrow{color:var(--ink);border-radius:8px;padding:9px 8px;display:grid;grid-template-columns:1fr auto;gap:3px 8px;margin-bottom:2px}.qrow b{font-weight:600}.qrow small{grid-column:1/-1;color:var(--ink2);font-variant-numeric:tabular-nums;font-size:12.5px}
.qrow.sel{background:var(--selected)}
.main{color:var(--ink);display:flex;flex-direction:column;min-width:0}
.bar{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--hair);flex-wrap:wrap}.bar .id{font-weight:600;font-size:15px}
.titlepill{background:var(--well);border-radius:6px;padding:3px 9px;font-weight:500}
.split{margin-left:auto;display:inline-flex;border-radius:8px;overflow:hidden;background:var(--primary);color:var(--on-primary);font-weight:600}.split b{padding:7px 16px}.split i{display:inline-flex;align-items:center;padding:0 9px;border-left:1px solid rgba(255,255,255,.35)}
.tabs2{display:flex;gap:22px;padding:0 16px;border-bottom:1px solid var(--hair)}.tabs2 span{padding:9px 0;color:var(--ink2);border-bottom:2px solid transparent;margin-bottom:-1px}.tabs2 .on{color:var(--ink);font-weight:600;border-bottom-color:var(--primary)}
.cols{display:grid;grid-template-columns:1fr 270px;flex:1}
.b{padding:14px 16px;display:flex;flex-direction:column;gap:12px}.e{padding:2px 14px 14px;border-left:1px solid var(--hair)}
.draft{color:var(--ink);background:linear-gradient(135deg,var(--mint-edge) 0%,var(--mint) 22%,var(--mint) 100%);border-radius:12px;padding:12px 14px}
.dhead{display:flex;gap:6px;align-items:center;font-size:13px;margin-bottom:4px}.dhead .i{color:var(--primary)}
.draft .row{border-bottom-color:var(--mint-edge)}
.big{font:600 17px/1.4 'Instrument Sans',Inter,sans-serif;margin:2px 0 6px}
.sec{color:var(--ink);border:1px solid var(--hair);border-radius:12px;padding:10px 14px;background:var(--panel)}
.sec h5{font-size:14px;margin:2px 0 4px;font-weight:600}
.lbl{font-size:12.5px;color:var(--ink2);margin:0 0 4px;display:flex;align-items:center;gap:5px}
.claims{color:var(--ink);background:var(--well);border-radius:8px;padding:8px 12px;margin-top:10px}.claims p{margin:2px 0}
@media (max-width:900px){.app{grid-template-columns:1fr}.cols{grid-template-columns:1fr}.e{border-left:0;border-top:1px solid var(--hair)}aside.q{border-right:0;border-bottom:1px solid var(--hair)}}
@media (max-width:420px){.sws{grid-template-columns:repeat(3,1fr)}}
"""


def page():
    lt, dk = css_vars(LIGHT), css_vars(DARK)
    shots_html = "".join(
        f"<figure class='shot{' first' if k == 0 else ''}'><img src='{img(f)}' alt='{t} by {d}' loading='eager'><figcaption><b>{f[:5]}</b>"
        f"{' · <b>your pick</b>' if k == 0 else ''} · {t} — {d}<br><span class='why'>{why}</span><br><a href='{u}'>{u}</a></figcaption></figure>"
        for k, (f, t, d, u, why) in enumerate(SHOTS))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>A5 Look Sheet</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wdth,wght@75..100,400..700&family=Inter:wght@400;500;600;700&family=Geist+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main class="page">
<p class="badge">UX-2 · quick look before any prototype · proposal · 2026-10-20</p>
<h1>A5 · Service desk</h1>
<p class="lede">The Kirridesk look you pointed at, applied to Meridian: a cool blue-grey canvas framing clean white surfaces, hairline cards, one deep emerald for the action, mint for the customer's side of the chat and for anything the assistant wrote, charcoal for Send. Same four screens and the same words as the A4 sheet, so you are only comparing colour and feel. Nothing here is clickable; the full prototype gets built only after you pick. Source: <code>docs/design/DESIGN-DIRECTIONS.md</code> § A5. Fonts load from Google Fonts with a system fallback.</p>
<section class="s"><h2>Mockups in light mode (the primary theme)</h2><p class="note">Booking a window · the handoff with its honest promise · the safety card (the only square, red object) · the staff case view.</p>
<div class="mocks" style="{lt}">{PHONE_SLOTS}{PHONE_HANDOFF}{PHONE_SAFETY}</div>
<div class="mocks" style="{lt};margin-top:20px">{CONSOLE}</div></section>
<section class="s"><h2>The same, dark (secondary theme)</h2><p class="note">Your shot is light only; the dark theme is ours. The emerald brightens back to Kirridesk's own #00BC6F, with near-black text on it.</p><div class="mocks" style="{dk}">{PHONE_HANDOFF}{PHONE_SLOTS}</div></section>
<section class="s"><h2>Palette (sampled from the shots; UX-3 makes it exact)</h2><p class="note">Sampled with Pillow from dr-25 and dr-26: canvas #E5E9F0, app #FFFFFF, side rail #F5F6F7, pills #F3F5F7, AI draft mint #E2F8EF, charcoal button #202629, avatar indigo #2A2663. Two values were darkened because they fail as text: Kirridesk's green #00BC6F carries white text at only 2.49:1, so the button green is #007847 (same hue); its grey captions (#7D878E) are about 3.7:1, so secondary text is #5B656D. Red only for safety. Contrast below is computed from these values, and the build fails if any text pair is under 4.5:1.</p>
<div class="palettes"><div class="pal" style="background:{LIGHT['panel']};color:{LIGHT['ink']}"><h3>Light</h3><div class="sws">{swatches(LIGHT)}</div><table>{contrast_rows(LIGHT)}</table></div>
<div class="pal" style="background:{DARK['ground']};color:{DARK['ink']}"><h3>Dark</h3><div class="sws">{swatches(DARK)}</div><table>{contrast_rows(DARK)}</table></div></div></section>
<section class="s"><h2>The {len(SHOTS)} Dribbble references behind A5 (your shot first)</h2><p class="note">Other designers' published work, used as internal reference only (source S-228). Not copied into the product.</p>
<div class="shots">{shots_html}</div></section>
<p class="note">Local file, not published. Rebuild: <code>python3 docs/artifacts/_build/a5-look/build_a5_look.py</code></p>
</main></body></html>"""


if __name__ == "__main__":
    failures = []
    for name, pal in (("light", LIGHT), ("dark", DARK)):
        for fg, bg in TEXT_PAIRS:
            if ratio(pal[fg], pal[bg]) < 4.5:
                failures.append(f"{name}: {fg} on {bg} {ratio(pal[fg], pal[bg]):.2f}:1 (text needs 4.5)")
        for fg, bg in UI_PAIRS:
            if ratio(pal[fg], pal[bg]) < 3:
                failures.append(f"{name}: {fg} edge on {bg} {ratio(pal[fg], pal[bg]):.2f}:1 (UI part needs 3)")
    if failures:
        print("CONTRAST FAIL\n" + "\n".join(failures))
        sys.exit(1)
    OUT.write_text(page())
    print(OUT, f"{OUT.stat().st_size/1e6:.2f} MB")
    for name, pal in (("light", LIGHT), ("dark", DARK)):
        worst = min((ratio(pal[a], pal[b]), f"{a} on {b}") for a, b in TEXT_PAIRS)
        print(name, "lowest text pair", f"{worst[1]} {worst[0]:.2f}:1")
