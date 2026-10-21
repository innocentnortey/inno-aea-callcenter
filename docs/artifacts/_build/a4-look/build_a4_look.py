"""Build the A4 look sheet: reference shots, palette swatches and static mockups (UX-2, quick look before any prototype).

Run from anywhere: python3 docs/artifacts/_build/a4-look/build_a4_look.py
Palette values are a proposal for review; UX-3 design.md makes them exact.
"""
import base64
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # docs/
REFS = ROOT / "design" / "references"
OUT = ROOT / "artifacts" / "2026-10-20-a4-look-sheet.html"

SHOTS = [
    ("dr-16-energy-update-statement.jpg", "Renewable Energy (Utility company)", "Eugen Eşanu", "https://dribbble.com/shots/27783586-Renewable-Energy-Utility-company", "Warm off-white ground, white rounded panels, no borders; the bill-like statement"),
    ("dr-17-public-grid-utility-setup.jpg", "Onboarding for utility management app", "Never Before Seen", "https://dribbble.com/shots/26917835-Onboarding-for-utility-management-app", "Quiet progress line over a step; one steady primary"),
    ("dr-18-two-tone-greeting-slots.jpg", "Mobile design for medical app", "Hyperactive Design", "https://dribbble.com/shots/27240331--Mobile-design-for-medical-app-Hyperactive", "Two-tone headline; slot grid with taken slots sunk grey"),
    ("dr-19-support-claim-timeline.jpg", "AI-Powered Insurance – Support Mobile App UI", "Farhan", "https://dribbble.com/shots/26546097-AI-Powered-Insurance-Support-Mobile-App-UI", "Reference chip; dated claim timeline in an inset"),
    ("dr-20-visit-summary-next-steps.jpg", "Empowering Health Care Mobile App", "Design Veli", "https://dribbble.com/shots/26677835-Empowering-Health-Care-Mobile-App", "Visit summary rows with icons, then next steps"),
    ("dr-21-payno-bills-mist.jpg", "Payno — Personal Finance & Payment Dashboard", "Orbix Studio LLC", "https://dribbble.com/shots/27586374-Payno-Personal-Finance-Payment-Dashboard-UI-Design", "Soft surfaces, nothing outlined; quiet due lines"),
    ("dr-22-perch-support-inbox.jpg", "Support Inbox Page — Perch", "Potara Studio", "https://dribbble.com/shots/27608234-Support-Inbox-Page-Perch", "Calm inbox: name and time captions, soft tinted turns"),
    ("dr-23-newfront-things-to-look-into.jpg", "Newfront Dashboard – Before & After", "Saasfactor", "https://dribbble.com/shots/26584579-Newfront-Dashboard-Before-After-Redesign", "Sections as quiet white panels with heading rows"),
    ("dr-24-regions-loans-summary.jpg", "Loans Summary", "Unfold", "https://dribbble.com/shots/21476886-Loans-Summary", "Two-line rows with a quiet 'Due in 12 days' line"),
]

# Proposal palette (light primary, dark secondary). Contrast is computed below, not asserted.
LIGHT = {
    "ground": "#F5F2EC", "panel": "#FFFFFF", "well": "#EDF1F4", "selected": "#DCE5EC",
    "ink": "#1E2A33", "ink2": "#56626C", "ink3": "#8A949C", "primary": "#2E5E7E",
    "on-primary": "#FFFFFF", "danger": "#B42318", "on-danger": "#FFFFFF",
}
DARK = {
    "ground": "#161E26", "panel": "#1E2832", "well": "#26323E", "selected": "#30404F",
    "ink": "#ECEFF2", "ink2": "#AAB5BE", "ink3": "#7B8792", "primary": "#8DB4D2",
    "on-primary": "#10202C", "danger": "#C8312F", "on-danger": "#FFFFFF",
}


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


PAIRS = [("ink", "ground"), ("ink", "panel"), ("ink", "well"), ("ink2", "panel"), ("ink2", "well"),
         ("ink2", "ground"), ("on-primary", "primary"), ("primary", "panel"), ("on-danger", "danger")]


def contrast_rows(pal):
    out = []
    for fg, bg in PAIRS:
        r = ratio(pal[fg], pal[bg])
        ok = "AA" if r >= 4.5 else ("AA large" if r >= 3 else "FAIL")
        out.append(f"<tr><td>{fg} on {bg}</td><td class='num'>{r:.2f}:1</td><td>{ok}</td></tr>")
    return "".join(out)


def swatches(pal):
    names = ["ground", "panel", "well", "selected", "ink", "ink2", "ink3", "primary", "danger"]
    return "".join(f"<div class='sw'><span style='background:{pal[n]}'></span><b>{n}</b><code>{pal[n]}</code></div>" for n in names)


def img(name):
    data = base64.b64encode((REFS / name).read_bytes()).decode()
    return f"data:image/jpeg;base64,{data}"


def css_vars(pal):
    return ";".join(f"--{k}:{v}" for k, v in pal.items())


shots_html = "".join(
    f"<figure class='shot'><img src='{img(f)}' alt='{t} by {d}' loading='eager'><figcaption><b>{f[:5]}</b> · {t} — {d}<br>"
    f"<span class='why'>{why}</span><br><a href='{u}'>{u}</a></figcaption></figure>"
    for f, t, d, u, why in SHOTS)

PHONE_SLOTS = """
<div class="phone"><div class="topbar"><b>Meridian Home Comfort</b><span>Automated assistant</span></div>
<div class="demo">Fri Oct 16 · demo date · nobody online</div>
<div class="log">
 <p class="cap">You · 2:03 pm</p><div class="me">My AC stopped cooling. Can someone come out? I'm in Kyle, 78640.</div>
 <p class="cap">Meridian assistant · automated · 2:04 pm</p>
 <p class="ai">Here are the arrival windows in your area this week. You only pay the diagnostic fee if you book.</p>
 <div class="panel">
  <h3><span class="lt">Choose a window ·</span> this week</h3>
  <div class="days"><span>Mon<b>19</b></span><span class="on">Tue<b>20</b></span><span>Wed<b>21</b></span><span>Thu<b>22</b></span></div>
  <div class="wins"><span>8:00 am – 12:00 pm</span><span class="taken">12:00 – 4:00 pm<i>Taken</i></span><span class="pick">1:00 – 5:00 pm</span><span>4:00 – 7:00 pm</span></div>
  <div class="row"><span>Diagnostic visit</span><b class="num">$89</b></div>
  <button class="pri">Continue with this window</button>
  <p class="fine">Windows are shown, not held. Members' fees appear after the code.</p>
 </div>
</div>
<div class="dock"><a class="person">☏ Talk to a person</a><div class="field">Type a message</div></div></div>"""

PHONE_HANDOFF = """
<div class="phone"><div class="topbar"><b>Meridian Home Comfort</b><span>Automated assistant · Reference MHC-C-0007</span></div>
<div class="demo">Fri Oct 16 · demo date · nobody online</div>
<div class="log">
 <p class="cap">Meridian assistant · automated · 2:14 pm</p>
 <p class="ai">I can't change or remove charges, but a person can review this with you.</p>
 <div class="panel">
  <p class="eyebrow">Your request <span class="ref">MHC-C-0007</span></p>
  <h3><span class="lt">A representative will get back to you</span> within 1 business day.</h3>
  <div class="well">
   <div class="row"><span>Due</span><b class="num">Mon Oct 19, 7:00 pm</b></div>
   <div class="row"><span>Status</span><b><span class="tag">◷ Waiting for a representative</span></b></div>
  </div>
  <p class="q">We'll follow up by email unless you'd prefer a phone call.</p>
  <div class="choices"><span class="on">Email<small>the address on your account</small></span><span>Phone call<small>the number ending in 02</small></span></div>
  <button class="pri">Save my choice</button>
 </div>
</div>
<div class="dock"><a class="person">☏ Talk to a person</a><div class="field">Type a message</div></div></div>"""

PHONE_SAFETY = """
<div class="phone dim"><div class="topbar"><b>Meridian Home Comfort</b><span>Automated assistant</span></div>
<div class="safety"><div class="band">⚠ DANGER</div>
 <ol><li>Leave the home immediately.</li><li>Call 911 or your gas utility from outside.</li></ol>
 <p>Don't flip any light switches, open windows near the furnace, or restart any equipment.</p></div>
<p class="quiet">Once you're outside and safe, you can leave a number here if you'd like.</p>
<div class="log faded"><p class="cap">You · 2:31 pm</p><div class="me">The kitchen smells like rotten eggs</div></div>
<div class="dock"><a class="person">☏ Talk to a person</a><div class="field">Type a message</div></div></div>"""

CONSOLE = """
<div class="console">
 <div class="col q"><h4>Needs attention first</h4>
  <div class="qrow"><b>Gas smell reported in chat</b><span class="tag">Safety</span><small>Omar Patel · MHC-C-0008 · no due time</small></div>
  <h4>By due time</h4>
  <div class="qrow"><b>Refund request</b><span class="tag strong">◷ Overdue</span><small>Linda Foster · MHC-C-0005 · Thu 7:00 pm</small></div>
  <div class="qrow sel"><b>Billing dispute · INV-204411</b><span class="tag">P3 Standard</span><small>Omar Patel · MHC-C-0007 · Due Mon 7:00 pm, in 3 days</small></div>
 </div>
 <div class="col b"><h2><span class="lt">Billing dispute ·</span> due Mon Oct 19, 7:00 pm</h2>
  <div class="panel"><p class="eyebrow">Promise shown to the customer</p><p class="big">A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.</p>
   <div class="well"><div class="row"><span>Follow up by</span><b>Phone, his choice</b></div><div class="row"><span>Best time</span><b>Mornings</b></div></div></div>
  <div class="panel"><p class="eyebrow">What we know for sure</p>
   <div class="row"><span>Invoice INV-204411</span><b class="num">$478.00 · unpaid</b></div>
   <div class="row"><span>After-hours dispatch on invoice</span><b class="num">$144.00</b></div>
   <div class="row"><span>Fee schedule, Jan 1 2026</span><b class="num">$149.00</b></div>
   <div class="claims"><p class="eyebrow">Customer says · not checked</p><p>The tech said it would be $89 to come out.</p></div></div>
 </div>
 <div class="col e"><h4>Evidence</h4><div class="panel"><p class="eyebrow">Invoice INV-204411</p>
  <div class="row"><span>What the AI saw · 2:10 pm</span><b class="num">$478.00</b></div><div class="row"><span>Now · 2:20 pm</span><b class="num">$478.00</b></div>
  <p class="fine">✓ No change since the snapshot.</p></div></div>
</div>"""

CSS = """
*{box-sizing:border-box}body{margin:0;font:16px/1.5 'Atkinson Hyperlegible Next','Atkinson Hyperlegible',system-ui,sans-serif;background:#F5F2EC;color:#1E2A33}
.page{max-width:1240px;margin:0 auto;padding:24px 16px 64px}h1,h2,h3{font-family:Manrope,system-ui,sans-serif}
h1{font-weight:600;font-size:28px;margin:0 0 4px}.lede{color:#56626C;margin:0 0 24px;max-width:70ch}
section{margin:32px 0}section>h2{font-size:20px;margin:0 0 4px}.note{color:#56626C;margin:0 0 14px;max-width:80ch}
.badge{display:inline-block;background:#EDF1F4;border-radius:6px;padding:2px 8px;font-size:13px;color:#1E2A33}
.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.shot{margin:0;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 8px 24px rgba(30,42,51,.06)}
.shot img{width:100%;display:block}.shot figcaption{padding:10px 12px;font-size:13px}.shot .why{color:#56626C}.shot a{color:#2E5E7E;word-break:break-all;font-size:12px}
.palettes{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.pal{border-radius:16px;padding:16px}.pal h3{margin:0 0 10px;font-size:16px}
.sws{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.sw{font-size:12px;display:flex;flex-direction:column;gap:2px}
.sw span{height:44px;border-radius:10px;box-shadow:inset 0 0 0 1px rgba(127,127,127,.18)}.sw code{opacity:.75}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:12px}td{padding:3px 6px;border-top:1px solid rgba(127,127,127,.2)}
.num{font-variant-numeric:tabular-nums}
.mocks{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}
/* --- mockup system (uses the palette variables) --- */
.m{background:var(--ground);color:var(--ink);border-radius:20px;padding:14px}
.phone{color:var(--ink);width:360px;max-width:100%;background:var(--ground);border-radius:28px;overflow:hidden;box-shadow:0 12px 32px rgba(30,42,51,.12);display:flex;flex-direction:column;min-height:720px;position:relative}
.topbar{background:var(--panel);padding:14px 16px;display:flex;flex-direction:column}.topbar b{font-family:Manrope,sans-serif;font-weight:600}.topbar span{font-size:13px;color:var(--ink2)}
.demo{font-size:12px;color:var(--ink2);text-align:center;padding:8px;border-bottom:1px solid rgba(127,127,127,.15)}
.log{padding:12px 14px;flex:1}.cap{font-size:12px;color:var(--ink2);margin:14px 0 4px}.ai{margin:0 0 10px;font-size:16px}
.me{background:var(--well);border-radius:14px;padding:10px 12px;margin-left:56px}
.panel{background:var(--panel);border-radius:20px;padding:16px;box-shadow:0 8px 24px rgba(20,30,40,.06);margin:8px 0}
.panel h3{font-weight:600;font-size:19px;line-height:1.3;margin:0 0 12px}.lt{font-weight:300;color:var(--ink2)}
.eyebrow{font-size:13px;color:var(--ink2);margin:0 0 6px;display:flex;justify-content:space-between;align-items:center}
.ref{font-family:'Atkinson Hyperlegible Mono',ui-monospace,monospace;background:var(--well);border-radius:6px;padding:2px 8px;color:var(--ink)}
.days{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:8px}.days span{background:var(--well);border-radius:12px;padding:6px;text-align:center;font-size:13px;color:var(--ink2)}
.days b{display:block;font-size:17px;color:var(--ink);font-variant-numeric:tabular-nums}.days .on{background:var(--selected)}
.wins{display:grid;grid-template-columns:1fr 1fr;gap:6px}.wins span{background:var(--panel);box-shadow:inset 0 0 0 1px var(--selected);border-radius:12px;padding:10px 8px;font-size:14px;font-variant-numeric:tabular-nums;text-align:center}
.wins .taken{background:var(--well);box-shadow:none;color:var(--ink3)}.wins .taken i{display:block;font-style:normal;font-size:12px;color:var(--ink2)}
.wins .pick{background:var(--primary);color:var(--on-primary);box-shadow:none}
.row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px dotted var(--ink3);font-size:15px}.row:last-child{border-bottom:0}.row span{color:var(--ink2)}
.well{background:var(--well);border-radius:12px;padding:4px 12px;margin:10px 0}
.tag{display:inline-block;background:var(--well);border-radius:6px;padding:2px 8px;font-size:13px;font-weight:600;color:var(--ink)}.tag.strong{background:var(--selected)}
.q{font-size:15px;margin:10px 0 6px}.choices{display:grid;grid-template-columns:1fr 1fr;gap:6px}.choices span{background:var(--well);border-radius:12px;padding:10px;font-weight:600;font-size:14px}
.choices small{display:block;font-weight:400;color:var(--ink2);font-size:12px}.choices .on{background:var(--selected);box-shadow:inset 0 0 0 2px var(--primary)}
.pri{margin-top:12px;width:100%;height:48px;border:0;border-radius:12px;background:var(--primary);color:var(--on-primary);font:600 16px Manrope,sans-serif}
.fine{font-size:12px;color:var(--ink2);margin:8px 0 0}
.dock{background:var(--panel);padding:10px 14px 16px}.person{display:block;font-size:14px;color:var(--primary);font-weight:600;margin-bottom:8px;text-decoration:underline}
.field{background:var(--well);border-radius:14px;padding:12px;color:var(--ink2);font-size:15px}
.safety{background:var(--panel);margin:0}.band{background:var(--danger);color:var(--on-danger);font:700 15px Manrope,sans-serif;letter-spacing:.08em;padding:10px 16px}
.safety ol{margin:12px 0 4px;padding:0 16px 0 36px;font:600 20px/1.35 Manrope,sans-serif}.safety p{padding:0 16px 14px;margin:6px 0 0;font-size:15px}
.quiet{font-size:13px;color:var(--ink2);padding:10px 16px;margin:0}.faded{opacity:.45}
.console{color:var(--ink);display:grid;grid-template-columns:260px 1fr 300px;gap:16px;background:var(--ground);border-radius:20px;padding:16px;width:100%;box-shadow:0 12px 32px rgba(30,42,51,.10);font-size:14px}
.console h4{font-size:13px;color:var(--ink2);margin:6px 0 8px;font-weight:600}.console h2{font-size:20px;margin:4px 0 10px;font-weight:600}
.qrow{background:transparent;border-radius:12px;padding:10px;display:grid;grid-template-columns:1fr auto;gap:2px 8px;margin-bottom:4px}.qrow small{grid-column:1/-1;color:var(--ink2);font-variant-numeric:tabular-nums}
.qrow.sel{background:var(--panel);box-shadow:0 6px 18px rgba(20,30,40,.06)}.big{font:600 17px/1.4 Manrope,sans-serif;margin:0 0 6px}
.claims{background:var(--well);border-radius:12px;padding:8px 12px;margin-top:10px}.claims p{margin:2px 0}
@media (max-width:900px){.console{grid-template-columns:1fr}}
"""


def page():
    lt, dk = css_vars(LIGHT), css_vars(DARK)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>A4 Look Sheet</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;600;700&family=Atkinson+Hyperlegible+Next:wght@400;600&family=Atkinson+Hyperlegible+Mono&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main class="page">
<p class="badge">UX-2 · quick look before any prototype · proposal · 2026-10-20</p>
<h1>A4 · Account statement</h1>
<p class="lede">Utility-professional, soft on the eyes: every reply that settles something reads like a calm statement panel on a warm, low-glare ground. These are fast static mockups so you can judge the colours and feel. Nothing here is clickable; the full prototype gets built only after you pick. Source: <code>docs/design/DESIGN-DIRECTIONS.md</code> § A4. Fonts load from Google Fonts with a system fallback.</p>
<section><h2>Mockups in light mode (the primary theme)</h2><p class="note">Booking a window · the handoff with its honest promise · the safety card (the only square, red object) · the staff case view.</p>
<div class="mocks" style="{lt}">{PHONE_SLOTS}{PHONE_HANDOFF}{PHONE_SAFETY}</div>
<div class="mocks" style="{lt};margin-top:20px">{CONSOLE}</div></section>
<section><h2>The same, dark (secondary theme)</h2><div class="mocks" style="{dk}">{PHONE_HANDOFF}</div></section>
<section><h2>Palette (proposal; UX-3 makes it exact)</h2><p class="note">Warm porcelain ground → white panel → pale mist well: three small surface steps instead of outlines. One harbour-blue accent. Red only for safety. Contrast below is computed from these values.</p>
<div class="palettes"><div class="pal" style="background:{LIGHT['ground']};color:{LIGHT['ink']}"><h3>Light</h3><div class="sws">{swatches(LIGHT)}</div><table>{contrast_rows(LIGHT)}</table></div>
<div class="pal" style="background:{DARK['ground']};color:{DARK['ink']}"><h3>Dark</h3><div class="sws">{swatches(DARK)}</div><table>{contrast_rows(DARK)}</table></div></div></section>
<section><h2>The 9 Dribbble references behind A4</h2><p class="note">Other designers' published work, used as internal reference only (source S-227). Not copied into the product.</p>
<div class="shots">{shots_html}</div></section>
<p class="note">Local file, not published. Rebuild: <code>python3 docs/artifacts/_build/a4-look/build_a4_look.py</code></p>
</main></body></html>"""


if __name__ == "__main__":
    OUT.write_text(page())
    print(OUT, f"{OUT.stat().st_size/1e6:.2f} MB")
    for name, pal in (("light", LIGHT), ("dark", DARK)):
        worst = min(ratio(pal[a], pal[b]) for a, b in PAIRS)
        print(name, "lowest pair", f"{worst:.2f}:1")
