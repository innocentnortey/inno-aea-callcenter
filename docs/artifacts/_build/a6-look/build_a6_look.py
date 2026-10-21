"""Build the A6 look sheet: reference shots, palette swatches and static mockups (UX-2, quick look before any prototype).

Run from anywhere: python3 docs/artifacts/_build/a6-look/build_a6_look.py
Same four mockups and copy as the A4 and A5 sheets, plus one plain chat turn (greeting, question, sourced answer)
and an "A5 vs A6" strip that renders A5's handoff card from build_a5_look.py beside A6's.
Palette values are sampled with Pillow from Innocent's pick (dr-35, Customer Service Workspace) and its kin; they are
adjusted only where a pair fails WCAG AA. UX-3 design.md makes them exact. The build fails if any text pair is under
4.5:1 or any UI edge under 3:1.
"""
import base64
import html
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # docs/
REFS = ROOT / "design" / "references"
OUT = ROOT / "artifacts" / "2026-10-20-a6-look-sheet.html"
A5_BUILD = HERE.parent / "a5-look" / "build_a5_look.py"

SHOTS = [
    ("dr-35-servicehub-customer-service-workspace.jpg", "Customer Service Workspace", "Kendall McMillan", "https://dribbble.com/shots/27664920-Customer-Service-Workspace", "Your pick. Navy band, white cards on a pale grey page, one bank blue for actions, label-value grids, a navy assistant panel holding the conversation"),
    ("dr-36-mcmillan-digital-rewards.jpg", "Digital Rewards Experience", "Kendall McMillan", "https://dribbble.com/shots/27105816-Digital-Rewards-Experience", "Same designer, same system on the customer side: navy nav strip, blue links, a white confirmation pop-over"),
    ("dr-37-swiftbank-freeze-card-chat.jpg", "swiftbank: AI Digital Banking Assistant – Freeze Digital Card", "finterface", "https://dribbble.com/shots/25111067-swiftbank-AI-Digital-Banking-Assistant-Freeze-Digital-Card-UI", "A bank's customer chatbot: deep-blue customer bubble, the assistant's answer as a white card with a titled inner panel and actions"),
    ("dr-38-swiftbank-request-payment-dark.jpg", "swiftbank: AI Digital Banking Chatbot – Request Money", "finterface", "https://dribbble.com/shots/25111058-swiftbank-AI-Digital-Banking-Chatbot-Request-Money-UI", "The same chatbot dark: label-value rows with icons inside the reply card; our dark theme's source"),
    ("dr-39-tavares-assistant-widget.jpg", "AI Agent Chat Animation", "W1sdom Prod.", "https://dribbble.com/shots/25848974-AI-Agent-Chat-Animation", "Plain enterprise assistant widget: navy-blue title band with a status line, flat grey assistant bubble"),
    ("dr-40-walmart-helper-widget.jpg", "Chat Widget", "Fuzeberg", "https://dribbble.com/shots/25787185-Chat-Widget", "Big-company helper: brand band, then white list rows with chevrons; utility first"),
    ("dr-41-city-service-center-chatbot.jpg", "AI Chatbot for a City Service Center", "W1sdom Prod.", "https://dribbble.com/shots/25849368-AI-Chatbot-for-a-City-Service-Center", "A civic chatbot that answers in plain paragraphs and links its source inline"),
]

# Sampled from dr-35 (Pillow): page #F7F7F7, cards #FFFFFF, band #002A54, assistant panel #013A6F, buttons/links/tab
# #056DAE, agent bubble #DBDBDB with text #565656, all other text #666666, light-blue edge #C0DAEB, divider #F1F1F1.
# Adjusted: field/secondary-button edges (#C0DAEB, ~#DBDBDB) fail 3:1 -> 'edge' #8C8C8C and primary borders.
# Added from kin: selected tint #E4EEF8 (dr-40); dark theme from dr-38 (#0F172A card, #0567A4 customer bubble).
LIGHT = {
    "ground": "#F7F7F7", "panel": "#FFFFFF", "well": "#F1F1F1", "bubble": "#DBDBDB", "selected": "#E4EEF8",
    "edge": "#8C8C8C", "navy": "#002A54", "navy2": "#013A6F", "on-navy": "#FFFFFF", "navy-sub": "#C0DAEB",
    "strong": "#002A54", "ink": "#565656", "ink2": "#666666", "primary": "#056DAE", "on-primary": "#FFFFFF",
    "danger": "#B42318", "on-danger": "#FFFFFF",
}
DARK = {
    "ground": "#02060F", "panel": "#0F172A", "well": "#172238", "bubble": "#22304A", "selected": "#13304D",
    "edge": "#6B7A90", "navy": "#0B1E38", "navy2": "#0E2747", "on-navy": "#FFFFFF", "navy-sub": "#A9C6E0",
    "strong": "#F2F6FA", "ink": "#D5DCE6", "ink2": "#AAB4C3", "primary": "#5AA9E6", "on-primary": "#04131F",
    "danger": "#C8312F", "on-danger": "#FFFFFF",
}
# The customer's own bubble: navy (#002A54) in the shot; dr-38's #0567A4 in the dark theme.
BUBBLE_ME = {"light": ("#002A54", "#FFFFFF"), "dark": ("#0567A4", "#FFFFFF")}


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# Every pair where text sits in the mockups (>= 4.5:1).
TEXT_PAIRS = [("strong", "panel"), ("strong", "ground"), ("strong", "selected"), ("ink", "panel"), ("ink", "ground"),
              ("ink", "well"), ("ink", "bubble"), ("ink", "selected"), ("ink2", "panel"), ("ink2", "ground"),
              ("ink2", "well"), ("ink2", "selected"), ("primary", "panel"), ("primary", "ground"), ("primary", "selected"),
              ("on-primary", "primary"), ("on-navy", "navy"), ("on-navy", "navy2"), ("navy-sub", "navy"),
              ("navy-sub", "navy2"), ("on-danger", "danger")]
# Control edges and the safety band (>= 3:1).
UI_PAIRS = [("edge", "panel"), ("primary", "panel"), ("danger", "panel"), ("primary", "selected")]


def me_pairs():
    return [(f"you-bubble text ({k})", fg, bg) for k, (bg, fg) in BUBBLE_ME.items()]


def contrast_rows(pal, theme):
    out = []
    for fg, bg in TEXT_PAIRS:
        r = ratio(pal[fg], pal[bg])
        out.append(f"<tr><td>{fg} on {bg}</td><td class='num'>{r:.2f}:1</td><td>{'AA text' if r >= 4.5 else 'FAIL'}</td></tr>")
    bg, fg = BUBBLE_ME[theme]
    r = ratio(fg, bg)
    out.append(f"<tr><td>text on your bubble {bg}</td><td class='num'>{r:.2f}:1</td><td>{'AA text' if r >= 4.5 else 'FAIL'}</td></tr>")
    for fg, bg in UI_PAIRS:
        r = ratio(pal[fg], pal[bg])
        out.append(f"<tr class='ui'><td>{fg} edge on {bg}</td><td class='num'>{r:.2f}:1</td><td>{'AA UI part' if r >= 3 else 'FAIL'}</td></tr>")
    return "".join(out)


def swatches(pal, theme):
    names = ["ground", "panel", "well", "bubble", "selected", "edge", "navy", "navy2", "strong", "ink", "ink2", "primary", "danger"]
    sw = "".join(f"<div class='sw'><span style='background:{pal[n]}'></span><b>{n}</b><code>{pal[n]}</code></div>" for n in names)
    bg = BUBBLE_ME[theme][0]
    return sw + f"<div class='sw'><span style='background:{bg}'></span><b>you-bubble</b><code>{bg}</code></div>"


def img(name):
    return "data:image/jpeg;base64," + base64.b64encode((REFS / name).read_bytes()).decode()


def css_vars(pal, theme):
    v = ";".join(f"--{k}:{val}" for k, val in pal.items())
    bg, fg = BUBBLE_ME[theme]
    return f"{v};--me:{bg};--on-me:{fg}"


def ico(path, size=16):
    return (f"<svg class='i' width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            f"stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>{path}</svg>")


I_HEAD = ico("<path d='M4 14v-2a8 8 0 0 1 16 0v2'/><rect x='3' y='14' width='4' height='6' rx='1.5'/><rect x='17' y='14' width='4' height='6' rx='1.5'/>")
I_CAL = ico("<rect x='3.5' y='5' width='17' height='15' rx='2'/><path d='M3.5 10h17M8 3v4M16 3v4'/>")
I_CLOCK = ico("<circle cx='12' cy='12' r='8.5'/><path d='M12 7.5V12l3 2'/>", 15)
I_TICKET = ico("<path d='M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4z'/>")
I_UP = ico("<path d='M6 15l6-6 6 6'/>", 15)
I_CHECK = ico("<path d='M5 12.5l4.5 4.5L19 7.5'/>", 15)
I_WARN = ico("<path d='M12 3.5L2.5 20h19z'/><path d='M12 10v4.5M12 17.2v.3'/>", 18)
I_EXT = ico("<path d='M14 4h6v6M20 4l-9 9'/><path d='M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5'/>", 15)
I_SEND = ico("<path d='M4 12l16-8-6 16-2.5-6.5z'/>", 17)
I_CHAT = ico("<path d='M4 5h16v11H9l-5 4z'/><path d='M8 9.5h8M8 12.5h5'/>", 15)

TOP = """<div class="band"><span class="word">MERIDIAN</span><div><b>Meridian Home Comfort</b><span>Automated assistant</span></div></div>"""
TOP_REF = """<div class="band"><span class="word">MERIDIAN</span><div><b>Meridian Home Comfort</b><span>Automated assistant · Reference <code class="mono">MHC-C-0007</code></span></div></div>"""
DEMO = '<div class="demo">Fri Oct 16 · demo date · nobody online</div>'
DOCK = f"""<div class="dock"><div class="sec-btn">{I_HEAD} Talk to a person</div><div class="composer"><span>Type a message</span><b class="send" aria-label="Send">{I_SEND}</b></div></div>"""

PHONE_CHAT = f"""
<div class="phone">{TOP}{DEMO}
<div class="log">
 <div class="ai">Hi, I'm Meridian Home Comfort's automated assistant, not a person. I can answer questions about our services, book a visit, and look up your account once you've confirmed it's you. If you'd like a person at any point, tap Talk to a person.</div>
 <p class="ts">Meridian assistant · automated · 2:01 pm</p>
 <div class="me">How much is the diagnostic fee?</div>
 <p class="ts right">You · 2:02 pm</p>
 <div class="ai">The diagnostic visit is <b class="num">$89</b>. If you approve the repair during the same visit, the $89 is applied as credit toward it. Comfort Club members don't pay it.
  <div class="src"><span class="lbl">Where this comes from</span><a>{I_EXT} Customer FAQ · Fees</a><small>faq/customer_faq.md · updated Mar 2, 2026</small></div></div>
 <p class="ts">Meridian assistant · automated · 2:02 pm</p>
</div>{DOCK}</div>"""

PHONE_SLOTS = f"""
<div class="phone">{TOP}{DEMO}
<div class="log">
 <div class="me">My AC stopped cooling. Can someone come out? I'm in Kyle, 78640.</div>
 <p class="ts right">You · 2:03 pm</p>
 <div class="ai">Here are the arrival windows in your area this week. You only pay the diagnostic fee if you book.</div>
 <p class="ts">Meridian assistant · automated · 2:04 pm</p>
 <div class="card">
  <div class="chead"><span class="chev">{I_UP}</span>Choose a window<span class="right">this week</span></div>
  <div class="tabs"><span>Mon <b class="num">19</b></span><span class="on">Tue <b class="num">20</b></span><span>Wed <b class="num">21</b></span><span>Thu <b class="num">22</b></span></div>
  <div class="wins"><span><em class="box"></em>8:00 am – 12:00 pm</span><span class="taken"><em class="box"></em><s>12:00 – 4:00 pm</s><i>Taken</i></span><span class="pick"><em class="box">{I_CHECK}</em>1:00 – 5:00 pm</span><span><em class="box"></em>4:00 – 7:00 pm</span></div>
  <div class="grid"><b>Diagnostic visit</b><span class="num">$89</span></div>
  <button class="pri">Continue with this window</button>
  <p class="fine">Windows are shown, not held. Members' fees appear after the code.</p>
 </div>
</div>{DOCK}</div>"""

PHONE_HANDOFF = f"""
<div class="phone">{TOP_REF}{DEMO}
<div class="log">
 <div class="ai">I can't change or remove charges, but a person can review this with you.</div>
 <p class="ts">Meridian assistant · automated · 2:14 pm</p>
 <div class="card">
  <div class="chead"><span class="chev">{I_UP}</span>Your request<span class="right"><code class="mono">MHC-C-0007</code></span></div>
  <p class="promise">A representative will get back to you within 1 business day.</p>
  <div class="grid"><b>Due</b><span class="num">Mon Oct 19, 7:00 pm</span><b>Status</b><span class="stat">{I_CLOCK} Waiting for a representative</span></div>
  <p class="q">We'll follow up by email unless you'd prefer a phone call.</p>
  <div class="choices"><span class="on"><em class="radio"></em>Email<small>the address on your account</small></span><span><em class="radio"></em>Phone call<small>the number ending in 02</small></span></div>
  <button class="pri">Save my choice</button>
 </div>
</div>{DOCK}</div>"""

PHONE_SAFETY = f"""
<div class="phone dim">{TOP}
<div class="safety" role="alert"><div class="sband">{I_WARN} DANGER</div>
 <ol><li>Leave the home immediately.</li><li>Call 911 or your gas utility from outside.</li></ol>
 <p>Don't flip any light switches, open windows near the furnace, or restart any equipment.</p></div>
<p class="quiet">Once you're outside and safe, you can leave a number here if you'd like.</p>
<div class="log faded"><div class="me">The kitchen smells like rotten eggs</div><p class="ts right">You · 2:31 pm</p></div>
{DOCK}</div>"""

CONSOLE = f"""
<div class="console">
 <div class="cband"><span class="word big">MERIDIAN</span><span class="sub">Home Comfort · Service desk</span><span class="rt">Fri Oct 16 · demo date <i>|</i> Riley · Representative (demo)</span></div>
 <div class="cbody">
 <aside class="assist"><h3>Queue</h3>
  <div class="qcard"><p class="qh">NEEDS ATTENTION FIRST</p>
   <div class="qrow"><b>Gas smell reported in chat</b><span class="st">{I_WARN} SAFETY</span><small>Omar Patel · <code class="mono">MHC-C-0008</code> · no due time</small></div></div>
  <div class="qcard"><p class="qh">BY DUE TIME</p>
   <div class="qrow"><b>Refund request</b><span class="st">{I_CLOCK} OVERDUE</span><small>Linda Foster · <code class="mono">MHC-C-0005</code> · Thu 7:00 pm</small></div>
   <div class="qrow sel"><b>Billing dispute · INV-204411</b><span class="st">P3 STANDARD</span><small>Omar Patel · <code class="mono">MHC-C-0007</code> · Due Mon 7:00 pm, in 3 days</small></div></div>
 </aside>
 <section class="cmain">
  <div class="tabrow"><span class="on">Brief</span><span>Conversation</span><b class="pri sm">Claim</b></div>
  <div class="ccols">
   <div class="ccol">
    <div class="card"><div class="chead"><span class="chev">{I_UP}</span>Promise shown to the customer<span class="right"><span class="who">{I_CHAT} Written by the assistant</span></span></div>
     <p class="promise">A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.</p>
     <div class="grid"><b>Follow up by</b><span>Phone, his choice</span><b>Best time</b><span>Mornings</span></div></div>
    <div class="card"><div class="chead"><span class="chev">{I_UP}</span>What we know for sure</div>
     <div class="grid"><b>Invoice INV-204411</b><span class="num">$478.00 · UNPAID</span><b>After-hours dispatch on invoice</b><span class="num">$144.00</span><b>Fee schedule, Jan 1 2026</b><span class="num">$149.00</span></div>
     <div class="claims"><b>Customer says · not checked</b><p>The tech said it would be $89 to come out.</p></div></div>
   </div>
   <div class="ccol">
    <div class="card"><div class="chead"><span class="chev">{I_UP}</span>Evidence · Invoice INV-204411</div>
     <div class="grid"><b>What the AI saw · 2:10 pm</b><span class="num">$478.00</span><b>Now · 2:20 pm</b><span class="num">$478.00</span></div>
     <p class="okline">{I_CHECK} No change since the snapshot.</p></div>
   </div>
  </div>
 </section></div>
</div>"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700&family=Figtree:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">')

CSS = """
:root{--page-bg:#F7F7F7;--page-ink:#2B2B2B;--page-ink2:#666666;--page-card:#FFFFFF;--page-hair:#DBDBDB;--page-link:#056DAE}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--page-bg:#02060F;--page-ink:#E6EBF2;--page-ink2:#AAB4C3;--page-card:#0F172A;--page-hair:#22304A;--page-link:#5AA9E6}}
:root[data-theme="dark"]{--page-bg:#02060F;--page-ink:#E6EBF2;--page-ink2:#AAB4C3;--page-card:#0F172A;--page-hair:#22304A;--page-link:#5AA9E6}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 Figtree,system-ui,-apple-system,'Segoe UI',sans-serif;background:var(--page-bg);color:var(--page-ink)}
.page{max-width:1240px;margin:0 auto;padding:24px 16px 64px}
h1,h2,h3{font-family:Montserrat,Figtree,system-ui,sans-serif}
h1{font-weight:600;font-size:28px;margin:0 0 4px}.lede{color:var(--page-ink2);margin:0 0 20px;max-width:74ch}
section.s{margin:36px 0}section.s>h2{font-size:19px;margin:0 0 4px;font-weight:600}.note{color:var(--page-ink2);margin:0 0 14px;max-width:84ch}
.badge{display:inline-block;background:var(--page-card);border:1px solid var(--page-hair);border-radius:4px;padding:2px 8px;font-size:13px}
code{font-family:'DM Mono',ui-monospace,Menlo,monospace;font-size:.92em}.num{font-variant-numeric:tabular-nums}
.vs{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}.vs figure{margin:0}.vs figcaption{font-size:13px;color:var(--page-ink2);margin-top:6px;max-width:372px}
.vs iframe{width:372px;max-width:100%;height:800px;border:0;border-radius:28px;display:block;background:transparent}
.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}
.shot{margin:0;background:var(--page-card);border:1px solid var(--page-hair);border-radius:6px;overflow:hidden}
.shot.first{grid-column:1/-1}.shot.first img{max-height:700px;object-fit:contain;background:#F7F7F7}
.shot img{width:100%;display:block}.shot figcaption{padding:10px 12px;font-size:13px}.shot .why{color:var(--page-ink2)}.shot a{color:var(--page-link);word-break:break-all;font-size:12px}
.palettes{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.pal{border-radius:6px;padding:16px;border:1px solid var(--page-hair)}.pal h3{margin:0 0 10px;font-size:16px}
.sws{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.sw{font-size:12px;display:flex;flex-direction:column;gap:2px;min-width:0}
.sw span{height:40px;border-radius:4px;box-shadow:inset 0 0 0 1px rgba(127,127,127,.3)}.sw code{opacity:.85;font-size:11px}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:12px}td{padding:3px 6px;border-top:1px solid rgba(127,127,127,.22)}tr.ui td{font-style:italic}
.mocks{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
.i{flex:none;vertical-align:-3px}
/* ---------- mockup system: every container sets its own colour ---------- */
.phone{color:var(--ink);background:var(--ground);width:360px;max-width:100%;border-radius:28px;overflow:hidden;border:6px solid var(--navy);display:flex;flex-direction:column;min-height:740px;font-size:15px}
.phone .mono,.console .mono{font-family:'DM Mono',ui-monospace,Menlo,monospace;font-size:.9em;white-space:nowrap}
.band{color:var(--on-navy);background:var(--navy);padding:12px 14px 12px;display:flex;align-items:center;gap:12px}
.band div{display:flex;flex-direction:column;line-height:1.3;min-width:0}.band b{font:600 15px Montserrat,Figtree,sans-serif}.band span{font-size:12.5px;color:var(--navy-sub)}
.band .mono{color:var(--on-navy)}
.word{font:700 11px Montserrat,sans-serif;letter-spacing:.28em;color:var(--on-navy);border-right:1px solid var(--navy-sub);padding-right:12px}
.demo{color:var(--ink2);background:var(--panel);font-size:12px;text-align:center;padding:6px 8px;box-shadow:0 1px 0 var(--bubble)}
.log{color:var(--ink);padding:12px 14px;flex:1}
.ai{color:var(--ink);background:var(--bubble);border-radius:4px;padding:10px 12px;margin:10px 40px 2px 0}
.me{color:var(--on-me);background:var(--me);border-radius:4px;padding:10px 12px;margin:10px 0 2px 56px}
.ts{font-size:11.5px;color:var(--ink2);margin:0 0 6px}.ts.right{text-align:right}
.src{margin-top:8px;background:var(--panel);border-radius:4px;padding:8px 10px;display:flex;flex-direction:column;gap:1px}
.src .lbl{font:600 11px Montserrat,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2)}
.src a{color:var(--primary);text-decoration:underline;font-weight:600;display:inline-flex;gap:5px;align-items:center}.src small{color:var(--ink2);font-size:12px}
.card{color:var(--ink);background:var(--panel);border-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,.14);padding:2px 14px 14px;margin:8px 0}
.chead{display:flex;align-items:center;gap:8px;padding:12px 0 8px;font:600 15px Montserrat,Figtree,sans-serif;color:var(--ink2)}
.chev{color:var(--primary);display:inline-flex}.chead .right{margin-left:auto;font:500 13px Figtree,sans-serif;color:var(--ink2)}
.tabs{display:flex;margin:0 0 8px}.tabs span{flex:1;text-align:center;padding:6px 0 6px;font-size:13px;color:var(--ink2);border-bottom:3px solid transparent}
.tabs b{display:block;font-size:16px;color:var(--ink2);font-weight:600}.tabs .on{color:var(--strong);font-weight:700;border-bottom-color:var(--primary)}.tabs .on b{color:var(--strong)}
.wins{display:grid;grid-template-columns:1fr;gap:6px}
.wins span{display:flex;align-items:center;gap:10px;flex-wrap:wrap;color:var(--ink);background:var(--panel);box-shadow:inset 0 0 0 1px var(--edge);border-radius:4px;padding:10px 12px;font-variant-numeric:tabular-nums;font-size:14.5px}
.box{width:18px;height:18px;border-radius:3px;box-shadow:inset 0 0 0 1.5px var(--edge);display:inline-flex;align-items:center;justify-content:center;flex:none;color:var(--on-primary)}
.wins .taken{background:var(--well);box-shadow:none;color:var(--ink2)}.wins .taken i{margin-left:auto;font-style:normal;font:600 11px Montserrat,sans-serif;letter-spacing:.08em;text-transform:uppercase}
.wins .pick{background:var(--selected);box-shadow:inset 0 0 0 2px var(--primary);color:var(--strong);font-weight:600}.wins .pick .box{background:var(--primary);box-shadow:none}
.grid{display:grid;grid-template-columns:auto 1fr;gap:10px 18px;margin:12px 0 2px;font-size:14px;align-items:baseline}.grid b{font-weight:600;color:var(--ink2)}.grid span{color:var(--ink);text-align:right}
.stat{display:inline-flex;gap:5px;align-items:center;justify-content:flex-end;font-weight:600}
.promise{font:600 17px/1.4 Montserrat,Figtree,sans-serif;color:var(--strong);margin:2px 0 4px}
.q{font-size:14px;margin:14px 0 6px;color:var(--ink)}.choices{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.choices span{position:relative;color:var(--ink);background:var(--panel);box-shadow:inset 0 0 0 1px var(--edge);border-radius:4px;padding:9px 10px 9px 32px;font-weight:600;font-size:14px}
.choices small{display:block;font-weight:400;color:var(--ink2);font-size:12px}.choices .on{background:var(--selected);box-shadow:inset 0 0 0 2px var(--primary);color:var(--strong)}
.radio{position:absolute;left:10px;top:12px;width:14px;height:14px;border-radius:50%;box-shadow:inset 0 0 0 1.5px var(--edge)}.on .radio{box-shadow:inset 0 0 0 4px var(--primary)}
.pri{margin-top:14px;width:100%;height:46px;border:0;border-radius:4px;background:var(--primary);color:var(--on-primary);font:700 15px Montserrat,Figtree,sans-serif;letter-spacing:.01em}
.pri.sm{margin:0 0 0 auto;width:auto;height:auto;padding:9px 22px;display:inline-block}
.fine{font-size:12px;color:var(--ink2);margin:8px 0 0}
.dock{color:var(--ink);background:var(--panel);padding:10px 12px 14px;box-shadow:0 -1px 0 var(--bubble)}
.sec-btn{display:flex;align-items:center;justify-content:center;gap:6px;border-radius:4px;box-shadow:inset 0 0 0 1.5px var(--primary);color:var(--primary);font:700 14px Montserrat,Figtree,sans-serif;padding:9px;margin-bottom:8px}
.composer{display:flex;align-items:center;justify-content:space-between;border-radius:4px;box-shadow:inset 0 0 0 1px var(--edge);padding:6px 6px 6px 12px;background:var(--panel)}.composer span{color:var(--ink2);font-size:14px;font-style:italic}
.send{display:inline-flex;align-items:center;justify-content:center;width:40px;height:36px;border-radius:4px;background:var(--primary);color:var(--on-primary)}
.safety{color:var(--ink);background:var(--panel);border-bottom:4px solid var(--danger)}
.sband{background:var(--danger);color:var(--on-danger);font:700 15px Montserrat,sans-serif;letter-spacing:.14em;padding:10px 16px;display:flex;align-items:center;gap:8px}
.safety ol{margin:14px 0 4px;padding:0 16px 0 38px;font:700 19px/1.35 Montserrat,Figtree,sans-serif;color:var(--strong)}.safety li{margin-bottom:4px}
.safety p{padding:0 16px 16px;margin:8px 0 0;font-size:15px;color:var(--ink)}
.quiet{font-size:13px;color:var(--ink2);padding:12px 16px;margin:0}.faded{opacity:.4}.phone.dim .dock{opacity:.55}
/* console: follows the shot closely */
.console{color:var(--ink);background:var(--ground);border-radius:6px;overflow:hidden;width:100%;box-shadow:0 0 0 1px var(--bubble);font-size:14px}
.cband{color:var(--on-navy);background:var(--navy);display:flex;align-items:center;gap:14px;padding:16px 22px;flex-wrap:wrap}
.cband .big{font-size:15px;border:0;padding:0}.cband .sub{font-size:14px;color:var(--on-navy)}.cband .rt{margin-left:auto;font-size:13px;color:var(--navy-sub)}.cband i{font-style:normal;margin:0 8px}
.cbody{display:grid;grid-template-columns:290px 1fr;gap:18px;padding:18px}
.assist{color:var(--on-navy);background:var(--navy2);border-radius:4px;padding:16px 14px;box-shadow:0 2px 6px rgba(0,0,0,.16)}
.assist h3{margin:2px 4px 12px;font-size:18px;font-weight:600;color:var(--on-navy)}
.qcard{color:var(--ink);background:var(--panel);border-radius:4px;padding:2px 12px 8px;margin-bottom:10px}
.qh{font:700 12px Montserrat,sans-serif;letter-spacing:.08em;color:var(--ink2);margin:10px 0 6px;padding-bottom:8px;box-shadow:0 1px 0 var(--well)}
.qrow{display:grid;grid-template-columns:1fr auto;gap:3px 8px;padding:8px 6px;border-radius:4px}.qrow b{font-weight:600;color:var(--strong)}.qrow small{grid-column:1/-1;color:var(--ink2);font-size:12.5px;font-variant-numeric:tabular-nums}
.qrow.sel{background:var(--selected)}
.st{display:inline-flex;gap:4px;align-items:center;font:700 11px Montserrat,sans-serif;letter-spacing:.06em;color:var(--ink2);white-space:nowrap}
.cmain{min-width:0}.tabrow{display:flex;align-items:center;gap:30px;margin-bottom:12px}.tabrow span{font:600 15px Montserrat,sans-serif;color:var(--ink2);padding-bottom:4px;border-bottom:3px solid transparent}.tabrow .on{color:var(--strong);border-bottom-color:var(--primary)}
.ccols{display:grid;grid-template-columns:1.25fr 1fr;gap:18px}.ccol .card{margin:0 0 18px}
.who{white-space:nowrap;display:inline-flex;gap:5px;align-items:center;background:var(--navy);color:var(--on-navy);border-radius:3px;padding:2px 8px;font-size:12px}
.claims{color:var(--ink);background:var(--well);border-radius:4px;padding:8px 12px;margin-top:12px}.claims b{color:var(--ink2);font-size:13px}.claims p{margin:2px 0}
.okline{display:flex;gap:6px;align-items:center;margin:10px 0 0;color:var(--ink)}
@media (max-width:900px){.cbody{grid-template-columns:1fr}.ccols{grid-template-columns:1fr}}
@media (max-width:420px){.sws{grid-template-columns:repeat(3,1fr)}}
"""


def a5_strip():
    """Render A5's handoff card (from its own generator) as an isolated srcdoc frame."""
    spec = importlib.util.spec_from_file_location("a5", A5_BUILD)
    a5 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a5)
    a5_doc = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>{FONTS.replace('Montserrat', 'Instrument+Sans:wdth,wght@75..100,400..700&family=Inter:wght@400;500;600;700&family=Geist+Mono:wght@400;600&family=Montserrat')}"
              f"<style>{a5.CSS}body{{margin:0;background:transparent}}</style></head><body>"
              f"<div class='mocks' style='{a5.css_vars(a5.LIGHT)}'>{a5.PHONE_HANDOFF}</div></body></html>")
    a6_doc = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>{FONTS}<style>{CSS}body{{margin:0;background:transparent}}</style></head><body>"
              f"<div class='mocks' style='{css_vars(LIGHT, 'light')}'>{PHONE_HANDOFF}</div></body></html>")
    return (f"<figure><iframe title='A5 handoff card' srcdoc=\"{html.escape(a5_doc, quote=True)}\"></iframe><figcaption><b>A5 · Service desk</b>: blue-grey canvas, mint and emerald, hairline cards, charcoal Send.</figcaption></figure>"
            f"<figure><iframe title='A6 handoff card' srcdoc=\"{html.escape(a6_doc, quote=True)}\"></iframe><figcaption><b>A6 · Branch office</b>: navy band, pale grey page, white shadowed cards, bank blue, grey label-value grids.</figcaption></figure>")


def page():
    lt, dk = css_vars(LIGHT, "light"), css_vars(DARK, "dark")
    shots_html = "".join(
        f"<figure class='shot{' first' if k == 0 else ''}'><img src='{img(f)}' alt='{t} by {d}' loading='eager'><figcaption><b>{f[:5]}</b>"
        f"{' · <b>your pick</b>' if k == 0 else ''} · {t} — {d}<br><span class='why'>{why}</span><br><a href='{u}'>{u}</a></figcaption></figure>"
        for k, (f, t, d, u, why) in enumerate(SHOTS))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>A6 Look Sheet</title>{FONTS}<style>{CSS}</style></head><body><main class="page">
<p class="badge">UX-2 · quick look before any prototype · proposal · 2026-10-20</p>
<h1>A6 · Branch office</h1>
<p class="lede">The Customer Service Workspace look you pointed at: a navy band, a pale grey page, white cards with a soft shadow, one bank blue for every action, and plain grey label-value grids. The staff console follows the shot closely; the homeowner chat is the translation (see "Turning a workspace into a chatbot" in <code>docs/design/DESIGN-DIRECTIONS.md</code> § A6). Same four screens and the same words as the A4 and A5 sheets, plus one plain chat turn. Nothing here is clickable; the prototype gets built only after you pick. Fonts load from Google Fonts with a system fallback.</p>
<section class="s"><h2>A5 vs A6: the same handoff card</h2><p class="note">A5 is the other direction still in play. Same card, same words, both light.</p><div class="vs">{a5_strip()}</div></section>
<section class="s"><h2>Mockups in light mode (the primary theme)</h2><p class="note">A plain chat turn with its source · booking a window · the handoff with its honest promise · the safety card (the only square, red object) · the staff case view.</p>
<div class="mocks" style="{lt}">{PHONE_CHAT}{PHONE_SLOTS}{PHONE_HANDOFF}{PHONE_SAFETY}</div>
<div class="mocks" style="{lt};margin-top:20px">{CONSOLE}</div></section>
<section class="s"><h2>The same, dark (secondary theme)</h2><p class="note">Your shot is light only. The dark theme comes from dr-38 (swiftbank's dark chatbot): slate cards #0F172A on near-black, the customer's bubble #0567A4, the bank blue lifted for contrast.</p><div class="mocks" style="{dk}">{PHONE_CHAT}{PHONE_HANDOFF}</div></section>
<section class="s"><h2>Palette (sampled from the shots; UX-3 makes it exact)</h2><p class="note">Sampled with Pillow from dr-35: page #F7F7F7, cards #FFFFFF, band #002A54, assistant panel #013A6F, buttons and links #056DAE, staff bubble #DBDBDB with text #565656, every other text #666666. All of the shot's text already passes AA, so text is unchanged. Two things fail as drawn: its light-blue button edge #C0DAEB (1.45:1) and its pale field borders, so control edges use #8C8C8C or the blue itself. The selected tint #E4EEF8 comes from dr-40. Red only for safety. The build fails if any text pair is under 4.5:1 or a control edge under 3:1.</p>
<div class="palettes"><div class="pal" style="background:{LIGHT['panel']};color:#2B2B2B"><h3>Light</h3><div class="sws">{swatches(LIGHT, 'light')}</div><table>{contrast_rows(LIGHT, 'light')}</table></div>
<div class="pal" style="background:{DARK['ground']};color:{DARK['ink']}"><h3>Dark</h3><div class="sws">{swatches(DARK, 'dark')}</div><table>{contrast_rows(DARK, 'dark')}</table></div></div></section>
<section class="s"><h2>The {len(SHOTS)} Dribbble references behind A6 (your shot first)</h2><p class="note">Other designers' published work, used as internal reference only (source S-231). Not copied into the product.</p>
<div class="shots">{shots_html}</div></section>
<p class="note">Local file, not published. Rebuild: <code>python3 docs/artifacts/_build/a6-look/build_a6_look.py</code></p>
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
        bg, fg = BUBBLE_ME[name]
        if ratio(fg, bg) < 4.5:
            failures.append(f"{name}: text on your bubble {ratio(fg, bg):.2f}:1")
    if failures:
        print("CONTRAST FAIL\n" + "\n".join(failures))
        sys.exit(1)
    OUT.write_text(page())
    print(OUT, f"{OUT.stat().st_size/1e6:.2f} MB")
    for name, pal in (("light", LIGHT), ("dark", DARK)):
        worst = min((ratio(pal[a], pal[b]), f"{a} on {b}") for a, b in TEXT_PAIRS)
        print(name, "lowest text pair", f"{worst[1]} {worst[0]:.2f}:1")
