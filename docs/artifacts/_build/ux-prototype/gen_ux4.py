"""Generate docs/artifacts/2026-10-21-ux-prototype.html: the UX-4 prototype gate review page.

Run from the project root:  python3 docs/artifacts/_build/ux-prototype/gen_ux4.py .
Then:  python3 -I ../.claude/skills/zero-to-hero/scripts/stamp_review_page.py docs/artifacts/2026-10-21-ux-prototype.html
       python3 -I ../.claude/skills/zero-to-hero/scripts/check_review_page.py docs/artifacts/2026-10-21-ux-prototype.html

The CSS is taken from the zero-to-hero template so the page keeps the house look. Screenshots are read from
docs/ux/04-prototype/screenshots/ and embedded as base64 so the file stands alone. Hand-written prose below;
the scenario ids come from apps/web/src/dev/scenarios/*.ts (checked when this was written, 2026-10-21).
Placeholder blocks are marked  PLACEHOLDER:  so a later pass can find them with grep.
"""
import base64
import html
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUT = ROOT / "docs/artifacts/2026-10-21-ux-prototype.html"
SHOTS = ROOT / "docs/ux/04-prototype/screenshots"
TEMPLATE = ROOT.parent / ".claude/skills/zero-to-hero/templates/visual-review-page.html"
E = html.escape

SOURCES = [
    ("docs/ux/04-prototype/PROTOTYPE_PLAN.md", "the UX-4 plan, run notes and checks"),
    ("docs/ux/04-prototype/groups/g1-chat-core.md", "G1 group record, chat core"),
    ("docs/ux/04-prototype/groups/g2-chat-cards.md", "G2 group record, chat cards"),
    ("docs/ux/04-prototype/groups/g3-demo-pages.md", "G3 group record, demo pages"),
    ("docs/ux/04-prototype/groups/g4-staff-queue-case.md", "G4 group record, queue and case"),
    ("docs/ux/04-prototype/groups/g5-oversight-reads.md", "G5 group record, oversight and reads"),
]

css = re.search(r"<style>(.*?)</style>", TEMPLATE.read_text(), re.S).group(1)
css += """
.steps{margin:0 0 var(--space-3);padding-left:22px} .steps li{margin:6px 0}
.scn{font:0.86em var(--font-mono);background:var(--surface-2);padding:1px 5px;border-radius:5px;white-space:nowrap}
.shots{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,1fr);gap:var(--space-3);align-items:start;margin-top:var(--space-3)}
.shots figure{margin:0;padding:var(--space-2)}
.shots img{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff}
.shots figcaption{margin-top:6px}
@media (max-width:640px){.shots{grid-template-columns:1fr}.shots figure.phone{max-width:240px}}
.opt{background:var(--surface-2);border-radius:8px;padding:var(--space-2) var(--space-3);margin:var(--space-2) 0}
.opt p{margin:0 0 4px} .opt .rec{font-weight:700;color:var(--accent)}
.decision-line{border-left:4px solid var(--awaiting);padding:var(--space-2) var(--space-3);background:var(--surface);font-weight:600;margin-top:var(--space-3)}
.placeholder{border:2px dashed var(--unknown);border-radius:var(--radius);padding:var(--space-3);background:var(--unknown-bg)}
pre{background:var(--surface-2);padding:var(--space-3);border-radius:8px;overflow-x:auto;font:0.9em var(--font-mono);margin:0 0 var(--space-3)}
.screen-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:var(--space-3);margin:var(--space-3) 0}
.screen-card h3{font-size:19px}
"""


def badge(s, label=None):
    names = {"fact": "Fact", "decision": "Your decision", "proposal": "Proposal", "unknown": "Unknown", "awaiting": "Awaiting you"}
    return f'<span class="st {s}">{label or names[s]}</span>'


def sc(*ids):
    return " ".join(f'<span class="scn">{E(i)}</span>' for i in ids)


def shot(name, label):
    parts = []
    for dev, cls in (("desktop", ""), ("phone", " phone")):
        f = SHOTS / f"{name}.default--{dev}--light.png"
        if not f.exists():
            parts.append(f'<figure class="{cls.strip()}"><p class="src">Missing screenshot: {E(f.name)}</p></figure>')
            continue
        b64 = base64.b64encode(f.read_bytes()).decode()
        w = "wide laptop view" if dev == "desktop" else "phone view"
        parts.append(
            f'<figure class="{cls.strip()}"><img loading="lazy" alt="{E(label)}, {w}, light theme, default state" '
            f'src="data:image/png;base64,{b64}"><figcaption>{E(label)}: {dev}, light, default state.</figcaption></figure>')
    return '<div class="shots">' + "".join(parts) + "</div>"


def screen(sid, title, what, steps, scenarios, shotname, route):
    li = "".join(f"<li>{s}</li>" for s in steps)
    return f"""<article class="screen-card" id="{sid.lower()}">
<h3>{sid} · {E(title)}</h3>
<p>{what} Route: <code>{E(route)}</code>.</p>
<ol class="steps">{li}</ol>
<p class="src"><b>Scenario ids you can paste after <code>?signedin=1&amp;scenario=</code>:</b> {scenarios}</p>
{shot(shotname, f"{sid} {title}")}
</article>"""


def ask(aid, title, context, problem, hard, why_asked, options, rec, line):
    opts = "".join(f'<div class="opt"><p><b>{E(n)}.</b> {t}</p><p class="src">{c}</p></div>' for n, t, c in options)
    return f"""<article class="card" data-status="awaiting" data-ask="{aid}" id="{aid.lower()}">
<h3>{aid} · {E(title)} {badge("awaiting")}</h3>
<div class="part" data-part="context"><h3>Where this comes up</h3><p>{context}</p></div>
<div class="part" data-part="problem"><h3>What is open</h3><p>{problem}</p></div>
<div class="part" data-part="why-hard"><h3>Why it is not obvious</h3><p>{hard}</p></div>
<div class="part" data-part="why-asked"><h3>Why you are asked</h3><p>{why_asked}</p></div>
{opts}
<p class="rec">{rec}</p>
<p class="decision-line"><b>Decision needed:</b> {line}</p>
</article>"""


# --------------------------------------------------------------------------- screens by role
SCREENS = {
 "customer": [
  screen("SCR-1", "Customer chat",
   "The page a homeowner uses. They type a problem (no cooling, a burning smell), the assistant answers from the knowledge base, offers booking windows, and can hand the customer to a person.",
   ["Open <code>/?signedin=1&amp;scenario=scr01-core.default</code>. Check the greeting, the demo bar at the top (date and whether anyone is online) and the strip that says what is settled so far.",
    "Safety first: open <code>scr01-cards.safety-takeover</code>, then send any message. The reply should put safety ahead of everything and lock the booking path.",
    "Booking: open <code>scr01-cards.slot-card</code>, send a message, and pick a window. Then try <code>scr01-core.success-booked</code> to see the booked card and the settled panel.",
    "Talking to a person: <code>scr01-core.success-live-queued</code> (staff on shift) and <code>scr01-core.success-handoff</code> (nobody online). The wording should be honest about who is, or is not, coming.",
    "Trouble: <code>scr01-core.error-send-failed</code>, <code>scr01-core.flow-limit-rate</code>, <code>scr01-core.flow-session-ended</code>, <code>scr01-core.disabled-chat-closed</code>."],
   sc("scr01-core.default", "scr01-core.empty", "scr01-core.loading-replying", "scr01-core.success-booked", "scr01-core.success-change-request", "scr01-core.flow-safety-takeover", "scr01-cards.safety-takeover", "scr01-cards.slot-card", "scr01-cards.code-sent", "scr01-cards.no-window-fits", "scr01-cards.out-of-area"),
   "scr01-core", "/"),
  screen("SCR-2", "Demo delivery inbox",
   "A fake inbox that stands in for the text message or email carrying the 6-digit verification code. It exists only because this is a demonstration.",
   ["Open <code>scr02.default</code>: one live code with a Copy button. Press Copy; it should say Copied for two seconds.",
    "Try <code>scr02.empty</code>, <code>scr02.stale-used-and-expired</code> (old codes greyed out) and <code>scr02.error</code>."],
   sc("scr02.default", "scr02.empty", "scr02.stale-new-code", "scr02.success-copied", "scr02.disabled-used-expired", "scr02.error"),
   "scr02", "/demo/inbox"),
  screen("SCR-3", "Demo guide and controls",
   "The page that explains what is real and what is simulated, and holds the two big switches: simulated staff on or off, and Reset the demo.",
   ["Open <code>scr03.default</code> (staff off) and <code>scr03.default-on</code> (staff on). Read the four cards for plain words.",
    "Turn staff off while a customer is waiting: <code>scr03.success-off-waiting</code>. Then <code>scr03.success-reset</code> to see the reset confirm step and its result line.",
    "Failures: <code>scr03.error-reset-in-progress</code>, <code>scr03.error-staffing-write</code>."],
   sc("scr03.default", "scr03.default-on", "scr03.success-off-waiting", "scr03.success-off-none", "scr03.success-reset", "scr03.error-reset-in-progress", "scr03.disabled-resetting"),
   "scr03", "/demo"),
 ],
 "representative": [
  screen("SCR-5", "Representative queue",
   "The staff laptop view: customers waiting in chat, cases to work, overdue ones. Rows update while you watch.",
   ["Switch the role to Representative (header control), or open <code>scr05.default</code>.",
    "Live customers: <code>scr05.live-queued</code> and <code>scr05.new-handoff</code> show a customer arriving. Claim a row.",
    "A claim that works but whose chat join fails shows the sentence in <a href=\"#d-2\">D-2</a>. Compare <code>scr05.success-claimed-row</code>.",
    "Empty and trouble: <code>scr05.empty</code>, <code>scr05.shift-ended</code>, <code>scr05.overdue-after-advance</code>, <code>scr05.error</code>."],
   sc("scr05.default", "scr05.empty", "scr05.live-queued", "scr05.new-handoff", "scr05.success-claimed-row", "scr05.overdue-after-advance", "scr05.shift-ended", "scr05.stale-cases-changed"),
   "scr05", "/staff/queue"),
  screen("SCR-6", "Case view",
   "One case: the brief the assistant wrote, the sources it used, the conversation, the promise made to the customer, and the buttons to claim, join the chat, contact, flag, release and close.",
   ["Open <code>scr06.default</code>. Work down the page: header, promise card, brief, evidence, activity.",
    "Claim and join: <code>scr06.success-claimed</code>, then <code>scr06.flow-live-joined</code> and <code>scr06.flow-chat-closed</code>.",
    "Fee-bearing change: <code>scr06.flow-fee-bearing</code> (see <a href=\"#d-8\">D-8</a> for the date question). Safety case: <code>scr06.flow-safety</code>.",
    "Edges: <code>scr06.error-owner-readonly</code>, <code>scr06.stale-version-conflict</code>, <code>scr06.partial-source-unavailable</code>, <code>scr06.empty-nothing-recorded</code>."],
   sc("scr06.default", "scr06.success-claimed", "scr06.flow-live-joined", "scr06.flow-fee-bearing", "scr06.flow-safety", "scr06.error-owner-readonly", "scr06.stale-version-conflict", "scr06.partial-source-unavailable"),
   "scr06", "/staff/cases/:reference"),
 ],
 "supervisor": [
  screen("SCR-7", "Supervisor oversight",
   "Five lanes of cases for the person running the shift, the demo clock buttons (+1 hour, +4 hours, next morning), and Assign.",
   ["Open <code>scr07.default</code>. Press +1 hour and watch what moves to overdue.",
    "Assign: pick a row, Assign, choose a person or change priority, give a reason. <code>scr07.error-version-conflict</code> shows the clash message.",
    "Shift ending: <code>scr07.success-shift-ended</code>. Live customers: <code>scr07.staffed-live-queue</code>."],
   sc("scr07.default", "scr07.empty", "scr07.success-advanced", "scr07.success-assigned", "scr07.error-version-conflict", "scr07.staffed-live-queue", "scr07.stale-lanes-updated"),
   "scr07", "/staff/oversight"),
  screen("SCR-8", "Review list of flags",
   "Every case a representative flagged for a second look. The supervisor marks each one reviewed.",
   ["Open <code>scr08.default</code>; press Mark reviewed on one flag. <code>scr08.disabled-rep</code> shows what a representative sees (no button).",
    "<code>scr08.error-flag-gone</code> shows a flag cleared by a reset."],
   sc("scr08.default", "scr08.empty", "scr08.success-reviewed", "scr08.disabled-rep", "scr08.error-review-forbidden", "scr08.error-flag-gone", "scr08.stale-new-flag"),
   "scr08", "/staff/flags"),
 ],
 "owner": [
  screen("SCR-9", "Business-owner outcomes",
   "The owner's page: are customers getting helped, and what are the promises kept and missed. Tiles open the cases behind them.",
   ["Open <code>scr09.default</code>. Open a tile and check the cases it lists.",
    "A measure with no denominator: <code>scr09.partial</code> and <code>scr09.disabled-zero-denominator</code>. Is it clear why a number is missing?"],
   sc("scr09.default", "scr09.empty", "scr09.partial", "scr09.disabled-zero-denominator", "scr09.stale-clock-moved", "scr09.error"),
   "scr09", "/staff/owner"),
 ],
 "monitoring and evaluation": [
  screen("SCR-10", "Monitoring",
   "Read-only health of the running assistant: traffic, failures, latency, spend and alerts. Open to any role once signed in.",
   ["Open <code>scr10.default</code>, then <code>scr10.alerts-cap-and-latency</code> and <code>scr10.alert-failure-and-trace</code> to see alerts.",
    "Open the \"What each measure counts\" disclosure. Plain enough?",
    "<code>scr10.stale-data-age</code> shows old data; <code>scr10.partial-too-few-turns</code> shows too little data."],
   sc("scr10.default", "scr10.alerts-cap-and-latency", "scr10.alert-zero-traffic", "scr10.alert-failure-and-trace", "scr10.partial-too-few-turns", "scr10.stale-data-age", "scr10.error-resetting"),
   "scr10", "/monitoring"),
  screen("SCR-11", "Evaluation report",
   "Read-only report of how the assistant scored on the test set, with the dev set and the sealed set kept apart.",
   ["Open <code>scr11.default</code>. Look for how a score is explained.",
    "<code>scr11.partial-dev-only</code> (sealed set not run), <code>scr11.stale-run-version</code>, <code>scr11.empty</code>."],
   sc("scr11.default", "scr11.partial-dev-only", "scr11.stale-run-version", "scr11.empty", "scr11.error"),
   "scr11", "/eval"),
 ],
 "login and role switch": [
  screen("SCR-12", "Demo login",
   "The front door to the whole deployment. One shared demo username and password. It says plainly that this is a demonstration, never a Meridian account.",
   ["Open <code>scr12.default</code>. In mock mode any non-empty username and password is accepted, so type anything (the real values will be set on Railway and given in the README; the screen, hints and screenshots never show them).",
    "Wrong login: <code>scr12.error-refused</code> shows the single refusal sentence (see <a href=\"#d-4\">D-4</a>). Also <code>scr12.error-unreachable</code>, <code>scr12.stale-session-ended</code>, <code>scr12.stale-already-signed-in</code>.",
    "Keyboard only: Tab through the form and press Enter. The Sign in button stays off until both fields are filled."],
   sc("scr12.default", "scr12.error-refused", "scr12.error-rate-limited", "scr12.error-unreachable", "scr12.stale-session-ended", "scr12.success-asked-page", "scr12.disabled-empty-fields"),
   "scr12", "/login"),
  screen("SCR-4", "Role switch",
   "A one-click control in the header of every screen to act as customer, representative, supervisor or owner. There is no second password. The page at /role explains each role.",
   ["Sign in, then click each of the four roles. Customer lands on the chat, Representative on the queue, Supervisor on oversight, Owner on outcomes. On Demo, Inbox, Monitoring and Evaluation the page stays put.",
    "As Customer, open <code>/staff/queue</code>: you should see a gentle line, not staff data (<code>scr04.stale-staff-as-customer</code>; wording is a proposal).",
    "Reset the demo from SCR-3, then look at the role: it returns to Customer and the login stays (<code>scr04.stale-role-reset</code>, <a href=\"#d-3\">D-3</a>)."],
   sc("scr04.default", "scr04.success-lands-on-home", "scr04.success-stays", "scr04.stale-staff-as-customer", "scr04.stale-role-reset", "scr04.error-network", "scr04.disabled-during-switch"),
   "scr04", "/role"),
 ],
}

screens_html = ""
for role, items in SCREENS.items():
    screens_html += f'<h3 class="roleh">{E(role.title())}</h3>' + "".join(items)

# --------------------------------------------------------------------------- decisions
DECISIONS = [
 ask("D-1", "Wording when a claim worked but joining the chat did not (case view)",
  "A representative opens a case on SCR-6 and presses Claim. The claim goes through, so the case is theirs. Then the second step, joining the customer's live chat, fails (the chat just closed, or the network blinked).",
  "The spec has no sentence for this half-success. Without one, the screen would say nothing, or would call the whole thing a failure and tempt the representative to claim again. A reviewer would find that confusing. The build session wrote a proposed sentence so the screen is not blank.",
  "It is two facts at once: you own the case, and you are not in the chat. The wording has to say both without alarm and point to the one thing that fixes it, the Join chat button.",
  "Copy is yours to judge: it is the staff voice the Meridian demo speaks in. The build session may not invent customer-visible or staff-visible wording on its own (SCREEN_SPECS lists every string).",
  [("A", "Use the proposed sentence: <i>\"You claimed this case, but joining the chat didn't go through. Try Join chat.\"</i>", "Ships as built. Plain, names the button."),
   ("B", "Rewrite it (you give the words)", "One short pass, then the string in <code>errorCopy.ts</code> changes."),
   ("C", "Drop the sentence and show a generic error", "Simplest, but loses the fact that the claim worked.")],
  "Recommended: A. It says what happened and what to press.",
  "Should the SCR-6 sentence be A (as proposed), B (your words) or C (generic error)?"),
 ask("D-2", "Wording when a claim worked but joining the chat did not (queue)",
  "The same half-success, but the claim was made from a row on the queue (SCR-5) instead of from inside the case.",
  "A second sentence was proposed for the queue, because the representative is not on the case page yet. It says to open the case first: <i>\"You claimed the case, but joining the chat didn't go through. Open it and try Join chat.\"</i>",
  "The two screens differ by one step (open the case), so the sentences differ by a few words. Keeping them separate is a choice; one shared sentence would be shorter but wrong on one of the screens.",
  "Same reason as D-1, and it is a separate choice. One yes to D-1 does not answer this one.",
  [("A", "Use the proposed queue sentence as built", "Accurate for the queue."),
   ("B", "Rewrite it (you give the words)", "Same small pass as D-1."),
   ("C", "Use the SCR-6 sentence on both screens", "One string to maintain; slightly off on the queue because it does not say to open the case.")],
  "Recommended: A.",
  "Should the SCR-5 sentence be A (as proposed), B (your words) or C (reuse the SCR-6 sentence)?"),
 ask("D-3", "After a demo reset, which role does the reviewer have?",
  "You are acting as Supervisor on SCR-7 and press Reset the demo on SCR-3 to start a clean run. The reset ends all open chats and clears case state.",
  "SCREEN_SPECS (N-14, SCR-3 R6) says the reset keeps your role. The signed OpenAPI file and CON-9 say the role goes back to Customer, and the login stays. The two documents disagree. The build followed the OpenAPI file, because the mock is generated from it and the backend will be too. After a reset the page re-reads the session and adds a sentence saying the role changed.",
  "Both are defensible. Keeping the role saves one click. Going back to Customer matches a fresh start and what the backend contract says. Changing the contract would reopen UX-3, which is signed.",
  "This is a conflict between two documents you signed at UX-3, so the build could not settle it quietly in the screen's favour.",
  [("A", "Keep what is built: role returns to Customer, login stays; fix SCREEN_SPECS to match the contract", "No contract change. The reviewer clicks one role button after a reset."),
   ("B", "Change the contract so the role is kept", "Nicer after a reset, but it reopens CON-9 and the backend plan.")],
  "Recommended: A. It costs one click and avoids reopening a signed contract.",
  "After Reset the demo, should the role return to Customer (A, as built) or stay as it was (B)?"),
 ask("D-4", "One sentence for every login refusal",
  "On SCR-12 someone types a wrong username, a wrong password, or tries too many times, or the form is incomplete.",
  "The spec allows one refusal sentence for the first three: <i>\"That username or password didn't work. Check the README and try again.\"</i> The contract also has a separate rate-limit sentence (UI_CONTRACTS differs from SCREEN_SPECS here). The build used the one sentence for every failure so nothing reveals which part was wrong or that a throttle kicked in.",
  "Telling someone they are rate limited is helpful to a real person but tells an attacker something. In a demo with one shared login the attacker risk is small. It is a copy and security-posture call.",
  "It trades helpfulness for sameness, and the spec and the contract disagree. That needs a ruling, not a quiet pick.",
  [("A", "One sentence for every refusal (as built)", "Same sentence, same timing; matches SCREEN_SPECS."),
   ("B", "Keep the one sentence for wrong credentials but show the contract's own rate-limit sentence when throttled", "Friendlier; one more string; reveals the throttle.")],
  "Recommended: A.",
  "Should every login failure give the same sentence (A) or should a throttle get its own (B)?"),
 ask("D-5", "The demo-date explainer on SCR-3",
  "On the demo guide page, IA.md lists a line saying what the demo date is and how the clock moves (it is Fri Oct 16, 2026 at the start and moves when the supervisor presses +1 hour).",
  "SCREEN_SPECS has no wording for it, so the build did not make it up. The demo bar at the top of every screen already shows the date.",
  "Without the line, a first-time reviewer sees a date that is not today with no reason given, until they read the guide cards. With it, SCR-3 gets one more paragraph that someone must write.",
  "Wording for a page the reviewer reads is your call, and leaving it out is a departure from the information architecture you signed.",
  [("A", "Leave it out; the demo bar is enough", "No work. Risk: the odd date looks like a bug."),
   ("B", "Write one sentence and add it to SCR-3 (you or Claude drafts, you approve)", "Small change; clears up the date.")],
  "Recommended: B, drafted by Claude for your review.",
  "Add a demo-date explainer to SCR-3 (B) or leave it out (A)?"),
 ask("D-6", "Owner navigation: \"Outcomes · Review list\"",
  "The business owner needs a way to move between their outcomes page (SCR-9) and the flag review list (SCR-8) in the staff header.",
  "The information architecture gives no navigation for the owner. The UX-4 plan proposes two links, <i>Outcomes</i> and <i>Review list</i>. It is the plan's own choice, not yours or the spec's.",
  "Fewer links keep the owner's header calm; more links make the review list easy to find. It is cheap to change later, but it is a visible piece of the interface.",
  "Navigation labels shape how the owner reads the product, and nobody signed them.",
  [("A", "Keep \"Outcomes · Review list\" as built", "No work."),
   ("B", "Outcomes only; the review list is reached from the outcomes page", "Simpler header; one fewer way in."),
   ("C", "You give the labels", "One short pass.")],
  "Recommended: A.",
  "Which owner navigation should we keep: A (Outcomes and Review list), B (Outcomes only) or C (yours)?"),
 ask("D-7", "Contract gaps the prototype ran into",
  "While building against the signed OpenAPI file, the groups found places where the screen needs something the contract does not provide, so the mock uses a stand-in. They are listed in <code>docs/ux/04-prototype/groups/*.md</code> and PROTOTYPE_PLAN.md. They are: <b>QueueRow.version</b> (so Assign needs no extra read), <b>Flag.message_text</b> (to expand a flagged message inline), <b>EvalMeasure.definition</b> (so measure definitions come from the data), <b>SettledVisit start and end as ISO times</b> (so the visit window can be a proper time element), <b>retry_turn_id on the timeout notice</b> (so Retry knows which turn), the <b>emergency-window label</b> (a note on the slot card saying it is a regular booking, not emergency service), <b>CANCELLED.settled.actions</b> (the cancel write is missing, so the live mock shows only \"There's no fee.\"), and a few missing examples (quick checks, setStaffing off with nobody waiting, the owner read-only case, SUPERVISOR and OWNER sessions).",
  "Each gap has a stand-in in the dev layer, so the prototype looks right now. The real backend (Stage 7) will not have the stand-ins. If the contract stays as is, those screens will lose detail or need extra calls.",
  "The contract is signed (UX-3). A change to it reopens UX-3 and breaks the generated types UX-4 pinned. Some gaps are small (a field), some change what a screen can show.",
  "The contract owners are you and the Stage 7 build. The build session may not edit the OpenAPI file, so it only reports the gaps.",
  [("A", "Send all the gaps to the contract owners as one change request after UX-4 closes, before Stage 7 builds the matching endpoints", "One contract revision; screens lose their stand-ins cleanly."),
   ("B", "Fix only the ones that change behaviour now (retry_turn_id, CANCELLED.settled.actions, QueueRow.version) and defer the rest", "Smaller change; some screens stay trimmed."),
   ("C", "Leave the contract alone and keep the stand-ins as documented limits", "No reopening; the real UI is a little poorer than the prototype.")],
  "Recommended: B, with the others queued for the same change request if you want them.",
  "How should we handle the contract gaps: A (all), B (only the behaviour ones), or C (none)?"),
 ask("D-8", "Fee-bearing change: due Friday Oct 16 or Saturday Oct 17?",
  "The fee-bearing change case (<span class=\"scn\">scr06.flow-fee-bearing</span>, case MHC-C-0009) shows a due time at the top of the case view. This is the case where a customer asks to change a booked visit in a way that carries a fee, so a person must handle it.",
  "SCREEN_SPECS prints the due time as <i>\"Due Fri Oct 16 · 12:00 pm\"</i>. The signed OpenAPI example says <i>\"Sat Oct 17 · 12:00 pm, the window start\"</i> (due_at 2026-10-17T12:00). The prototype shows what the contract example says, because the screen reads it from the data. So the build and the spec disagree by one day.",
  "The demo date is Fri Oct 16, and the visit window starts at noon the next day, so Saturday is plausible and the spec may be the one that is wrong. Fixing the spec is a small edit; fixing the example means touching the signed contract file.",
  "Both documents are signed (UX-3), so the build cannot choose between them on its own, and a reviewer who sees both will think one of them is a bug.",
  [("A", "Saturday is right: correct the SCREEN_SPECS text to match the example", "No contract change; one line in the spec."),
   ("B", "Friday is right: correct the OpenAPI example (goes into D-7's change request)", "Touches the contract file."),
   ("C", "Leave both and note it as a known difference", "No edit; the mismatch stays in the record.")],
  "Recommended: A, because the example matches the visit window start.",
  "Should the fee-bearing due date be Saturday (A, fix the spec), Friday (B, fix the example) or left noted (C)?"),
 ask("D-9", "Inter font: single-storey \"a\" is not applied",
  "The design asks for the font Inter with its <code>cv11</code> setting, which should give a single-storey letter a (this is the plan's reading of the feature). The prototype loads Inter from the @fontsource latin files.",
  "Those files do not contain the cv11 feature, so the setting does nothing and every a is double-storey. Self-hosting the full Inter file would fix it, at the cost of a bigger font download. The plan defers this to UX-5.",
  "It is a small visual difference that few people would notice, but the design asks for it (design.md section 3.1 asks for the fonts at UX-4), and a bigger font file slows the first load on a phone.",
  "Whether the single-storey a is worth the extra weight is a look-and-feel judgement.",
  [("A", "Defer to UX-5 as planned", "No change now; you see the double-storey a in the prototype."),
   ("B", "Self-host the full Inter file now", "Matches design.md; bigger download."),
   ("C", "Drop the cv11 requirement from design.md", "No download cost; the design text changes.")],
  "Recommended: A.",
  "Should the Inter cv11 gap be deferred (A), fixed now (B) or dropped from the design (C)?"),
]

# --------------------------------------------------------------------------- page
src_meta = "\n".join(f'<meta name="review-source" content="{p}|0">' for p, _ in SRC if False) if False else "\n".join(
    f'<meta name="review-source" content="{p}|0">' for p, _ in SOURCES)
src_dd = "\n".join(
    f'<dd><a href="../{p[5:]}"><code>{p}</code></a> · {d} · SHA-256 <code data-sha-for="{p}">0</code></dd>' for p, d in SOURCES)

evidence_rows = [
 ("Lint (<code>npm run lint</code>)", "fact", "Passes", "PROTOTYPE_PLAN.md, Checks"),
 ("Type check (<code>npm run typecheck</code>)", "fact", "Passes", "PROTOTYPE_PLAN.md, Checks"),
 ("Unit and screen tests", "fact", "2,614 pass, 1 skipped (130 files), rerun by the orchestrator 2026-10-21 after the integration tests were added. All are mock-only or fake-transport tests; none ran against a real backend", "<code>npm test</code>"),
 ("Contract smoke (<code>npm run smoke:mock</code>)", "fact", "Prism smoke: 273 requests, 0 failures", "build session report"),
 ("Production build has no dev layer (<code>check:dist</code>)", "fact", "Clean", "PROTOTYPE_PLAN.md, Checks"),
 ("Code review", "fact", "Done; 4 medium issues found and fixed", "build session report"),
 ("Browser sweep: every scenario, axe accessibility check at 1280 and 390 px, light and dark", "fact", "Desktop 494 passed, 0 failed (237 scenarios, light and dark, plus 4 flows and the booking-to-handoff rehearsal). Phone 257 passed, 0 failed, 237 skipped (dark runs desktop only). Mock only", "<code>apps/web/tests/e2e/sweep.spec.ts</code>, run alone with nothing else touching the checkout"),
 ("A human looking at it (you)", "awaiting", "This page asks for that. Not done.", "UX-4 gate"),
]
ev_html = "".join(
    f'<tr data-status="{s}"><td>{n}</td><td>{badge(s, {"fact": "Verified", "unknown": "Not verified", "awaiting": "Awaiting you"}[s])}</td><td>{r}</td><td>{src}</td></tr>'
    for n, s, r, src in evidence_rows)

DIAGRAM = """<figure>
<p class="scroll-hint">Diagram: swipe sideways. The numbered list under it says the same thing.</p>
<div class="scroll" tabindex="0" aria-label="Diagram, scrolls sideways">
<svg viewBox="0 0 1040 250" role="img" aria-labelledby="rt rd">
<title id="rt">How the prototype runs on the server and reaches your laptop</title>
<desc id="rd">Your laptop browser connects through an SSH tunnel to Vite on port 5184 on the server. Vite serves the app with the dev layer and forwards API calls to Prism on port 4019, which answers from the signed OpenAPI file.</desc>
<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="lane-family" x="0" y="10" width="1040" height="90" rx="8"/>
<rect class="lane-staff" x="0" y="110" width="1040" height="130" rx="8"/>
<text class="lane-label" x="12" y="32">YOUR LAPTOP</text>
<text class="lane-label" x="12" y="132">THE SERVER (claude-vultr)</text>
<rect class="node fact" x="60" y="40" width="250" height="50" rx="8"/><text x="72" y="62" class="strong">Browser</text><text x="72" y="80" class="small">http://127.0.0.1:5184</text>
<rect class="node fact" x="60" y="160" width="250" height="62" rx="8"/><text x="72" y="182" class="strong">Vite (port 5184)</text><text x="72" y="200" class="small">the app + the dev panel</text>
<rect class="node fact" x="420" y="160" width="250" height="62" rx="8"/><text x="432" y="182" class="strong">Dev layer</text><text x="432" y="200" class="small">scenarios, fake staff, fake clock</text>
<rect class="node fact" x="780" y="160" width="230" height="62" rx="8"/><text x="792" y="182" class="strong">Prism (port 4019)</text><text x="792" y="200" class="small">answers from the OpenAPI file</text>
<path class="arrow dash" d="M185,90 L185,160" marker-end="url(#ah)"/>
<text class="small" x="195" y="130">ssh -L 5184:127.0.0.1:5184 claude-vultr</text>
<path class="arrow" d="M310,191 L420,191" marker-end="url(#ah)"/>
<path class="arrow" d="M670,191 L780,191" marker-end="url(#ah)"/>
</svg>
</div>
<figcaption>Everything here is mock. No real backend exists yet. <span class="st fact">Fact</span> from PROTOTYPE_PLAN.md, Run it.</figcaption>
<ol class="words"><li>On the server, one terminal runs Prism, the second runs Vite.</li><li>From your laptop, the SSH tunnel makes port 5184 on your laptop reach port 5184 on the server.</li><li>The browser opens the app; the dev layer decides which fake situation to show.</li><li>Calls to <code>/api</code> go through Vite to Prism, which answers from the signed OpenAPI file.</li></ol>
</figure>"""

body = f"""
<section aria-labelledby="sum-h" data-visual="summary">
  <h2 id="sum-h">At a glance</h2>
  <div class="grid three">
    <article class="card" data-status="fact"><h3>What exists {badge("fact")}</h3><p class="big">All 12 screens are clickable on a mock.</p><p class="src">PROTOTYPE_PLAN.md, What is clickable. All five build groups landed; the integrator pass is done.</p></article>
    <article class="card" data-status="unknown"><h3>What is not checked yet {badge("unknown")}</h3><p class="big">The full browser sweep is still running.</p><p class="src">Its result is a marked placeholder in section 5. Nothing there is claimed.</p></article>
    <article class="card" data-status="awaiting"><h3>Asked of you now {badge("awaiting")}</h3><p class="big">Is it understandable and visually appropriate?</p><p class="src">Plus nine small decisions in section 6. This page does not tick the UX-4 gate.</p></article>
  </div>
</section>

<section aria-labelledby="story-h" data-visual="story">
  <h2 id="story-h">1 · The story: what UX-4 is and what you are asked</h2>
  <p class="lede">Meridian Home Comfort is a made-up heating and cooling company. This project builds an assistant that talks to its customers, books visits, and hands the customer to a person when it should.</p>
  <div class="part" data-part="context"><h3>Where we were</h3><p>Over the last two days we wrote down what the screens should say and do (UX-1 to UX-3). UX-3 gave 12 screen specs, a look called A5 Service desk, and a signed list of calls between the screens and the back end (CON-1 to CON-22 and an OpenAPI file). You signed UX-3 on 2026-10-21.</p></div>
  <div class="part" data-part="problem"><h3>What UX-4 is</h3><p>UX-4 is a clickable version of those 12 screens, built in the real front-end folder (<code>apps/web/</code>) but talking to a mock, not a real server. A mock is a stand-in that answers from the signed contract file. Fake staff, a fake clock and scripted situations (a safety message, a failed join, an overdue case) are added by a dev layer that only exists while you test and is left out of the real build. Five build groups made the screens; an integrator pass joined them.</p></div>
  <div class="part" data-part="why-hard"><h3>Why a person has to look</h3><p>Tests can show that a button exists and a sentence matches the spec. They cannot show whether a sentence is clear to a stranger, whether the safety message stands out, or whether the queue feels calm or cluttered. For that, someone has to click through it, in the same order a customer, a representative, a supervisor and an owner would.</p></div>
  <div class="part" data-part="why-asked"><h3>What you are asked</h3><p><b>Is it understandable and visually appropriate?</b> Work through section 3 and say what feels wrong. Then answer the nine decisions in section 6, some of which are wording only you can judge. This page does not sign UX-4, and the checklist is not ticked.</p></div>
</section>

<section aria-labelledby="run-h">
  <h2 id="run-h">2 · How to run it</h2>
  <p class="section-sub">Two terminals on the server, one tunnel from your laptop. {badge("fact")} PROTOTYPE_PLAN.md and apps/web/README.md.</p>
  <pre>cd apps/web
npm run mock        # Prism on http://127.0.0.1:4019 (terminal 1)
npm run dev:mock    # Vite on http://127.0.0.1:5184 (terminal 2)

# from your laptop, in a third terminal:
ssh -L 5184:127.0.0.1:5184 claude-vultr</pre>
  <p>Then open <b>http://127.0.0.1:5184</b>. On the server itself, the same address works.</p>
  {DIAGRAM}
  <div class="grid two">
    <article class="card" data-status="fact"><h3>Logging in {badge("fact")}</h3>
      <p>The first page is the demo login (SCR-12). <b>In mock mode any non-empty username and password is accepted.</b> The real shared demo username and password are not written in <code>apps/web/README.md</code> yet: the spec says the README holds placeholders (<code>&lt;DEMO_USERNAME&gt;</code>, <code>&lt;DEMO_PASSWORD&gt;</code>) until the real ones are set on Railway. Nothing is invented here.</p>
      <p class="src">SCREEN_SPECS SCR-12; PROTOTYPE_PLAN.md, What is faked.</p></article>
    <article class="card" data-status="fact"><h3>Address bar shortcuts {badge("fact")}</h3>
      <p><code>?signedin=1</code> skips the login. <code>?scenario=&lt;id&gt;</code> opens one prepared situation. <code>?role=customer|representative|supervisor|owner</code> sets the role. <code>?staffing=on|off</code> turns simulated staff on or off. <code>?theme=light|dark</code> picks a theme. Combine them: <code>/?signedin=1&amp;scenario=scr05.live-queued&amp;theme=dark</code>.</p>
      <p class="src">apps/web/README.md, Mock-mode URL parameters. The URL rewrites itself to reproduce the state.</p></article>
  </div>
  <h3>The dev panel (the bar at the bottom that says "Prototype only")</h3>
  <p>It collapses to a small pill. Open it and you get five tabs. It is only in the mock build.</p>
  <div class="grid">
    <article class="card" data-status="fact"><h3>States</h3><p>Jump to a screen, then pick one of its scenarios, grouped by the eight standard states (default, empty, loading, partial, error, stale, success, disabled). Greyed cells are states that do not apply, with the reason. Also "Anywhere" scenarios such as a session ending or going offline.</p></article>
    <article class="card" data-status="fact"><h3>Session</h3><p>Fake sign-in, role, expire the session, refuse the next login, reset the role, restart, theme and a delay slider.</p></article>
    <article class="card" data-status="fact"><h3>Calls</h3><p>Every request the screen made: operation, status, which example answered, time. A row marked Drift means a reply broke the contract.</p></article>
    <article class="card" data-status="fact"><h3>Stream</h3><p>The live chat events, with buttons to drop and reconnect the stream.</p></article>
    <article class="card" data-status="fact"><h3>Look</h3><p>The component kit at <code>/__kit</code>: buttons, cards and fields in one place.</p></article>
  </div>
</section>

<section aria-labelledby="walk-h">
  <h2 id="walk-h">3 · Click-through script, by role</h2>
  <p class="section-sub">Each screen lists what to do and which prepared situations to open. Open a situation with <code>http://127.0.0.1:5184/?signedin=1&amp;scenario=&lt;id&gt;</code>. At each one, ask: do I know what this says, what to do next, and does it look right? {badge("fact")}: the scenario ids were read from <code>apps/web/src/dev/scenarios/</code>. The screenshots are the default state, light theme, only.</p>
  {screens_html}
</section>

<section aria-labelledby="ev-h">
  <h2 id="ev-h">4 · What has been checked</h2>
  <p class="section-sub">Honest list. Green means a command ran and passed. Nothing below is a human judgement, and nothing is signed off.</p>
  <div class="table-scroll"><table><thead><tr><th>Check</th><th>Status</th><th>Result</th><th>Source</th></tr></thead><tbody>{ev_html}</tbody></table></div>
  <p class="src">Note on the screenshots in section 3: they were taken by the build groups, default state, light theme only. Dark and other states have not been captured for this page.</p>
</section>

<section aria-labelledby="sweep-h">
  <h2 id="sweep-h">5 · Browser sweep result</h2>
  <div id="browser-sweep">
    <h3>Browser sweep result {badge("fact")}</h3>
    <p>Every scenario was opened in Chrome with the accessibility checker (axe, WCAG 2 A/AA) at 1280 and 390 pixels wide, and in dark on desktop. <b>All of it ran against the Prism mock and the dev layer, not a real backend.</b></p>
    <ul class="tight">
      <li>Desktop: <b>494 passed, 0 failed.</b> Phone: <b>257 passed, 0 failed</b> (237 skipped: dark runs on desktop only).</li>
      <li>Checked on each scenario: no uncaught errors, no contract-drift line, exactly one h1, no sideways scroll, zero axe violations.</li>
      <li>The first sweep found 66 failing scenarios (labels that did not contain their visible text), one screen with no heading and a missing favicon. All fixed and re-run clean.</li>
      <li>15 timed scenarios (10 s, 60 s, 65 s) have only their opening state asserted.</li>
      <li>Four browser flows pass: chat reply, staff claim, role switch, login return. So does the rehearsal of chat, booking slot conflict, person request, staff claim and join, representative message, hand back and close. In that rehearsal the live messages are injected by the dev layer, so it proves the screens render them, not that a server delivers them.</li>
      <li>Not verified: anything against a real backend. See <code>docs/ux/04-prototype/INTEGRATION_HANDOFF.md</code>.</li>
      <li>One thing for you to look at: on a 390 px phone, after "Claim and join" the case stays on the Brief tab and the reply box is under Evidence. A representative must tap Evidence before replying.</li>
    </ul>
  </div>
</section>

<section aria-labelledby="dec-h">
  <h2 id="dec-h">6 · The decisions that need your answer</h2>
  <p class="section-sub">Nine choices. Each tells the story first, then the options, and ends with one question. Answer each on its own. None is answered yet. D-1 and D-2 are wording; D-3 to D-6 are conflicts or gaps in the spec; D-7 to D-9 go to the contract owners.</p>
  {"".join(DECISIONS)}
</section>

<section aria-labelledby="ask-h">
  <div class="ask" data-status="awaiting">
    <h2 id="ask-h">7 · What you are asked to review now</h2>
    <p>{badge("awaiting")} <strong>UX-4 gate:</strong> after clicking through section 3, say whether the prototype is understandable and visually appropriate, and answer D-1 to D-9. Sources: <a href="../ux/04-prototype/PROTOTYPE_PLAN.md">PROTOTYPE_PLAN.md</a> and the five group records linked at the top.</p>
    <p><strong>Your answer would mean</strong> the screens can go on to UX-5. <strong>It would not</strong> ship anything, change a contract by itself, or settle the browser sweep. Not yet reviewed by you, and the checklist line for UX-4 stays unticked.</p>
  </div>
</section>
"""

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AEA call center: UX-4 prototype review</title>
<meta name="review-stage" content="Zero-to-hero UX-4 · Prototype">
<meta name="review-status" content="DRAFT: not approved; awaiting Innocent's UX-4 review">
<meta name="review-date" content="2026-10-21">
{src_meta}
<style>{css}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <p class="kicker">Zero-to-hero UX-4 · Clickable prototype · local visual review · Markdown is the source of truth</p>
    <h1>Meridian assistant: does the prototype look and read right?</h1>
    <div class="status-banner" role="status">
      <span class="st awaiting">Awaiting your review</span>
      <div><strong>DRAFT: not signed off.</strong> Nothing here counts as reviewed because it exists. You are asked to click through the prototype and to answer nine decisions. The browser sweep is still running (section 5).</div>
    </div>
    <dl class="meta">
      <dt>Review date</dt><dd>2026-10-21 (built after the group notes were written)</dd>
      <dt>Sources</dt>
      {src_dd}
      <dt>Refresh</dt><dd>If a source changes, or the browser sweep lands, this page is rebuilt (<code>docs/artifacts/_build/ux-prototype/gen_ux4.py</code>), stamped and re-checked.</dd>
    </dl>
    <ul class="legend" data-legend aria-label="Status legend">
      <li><span class="st fact" data-legend-item="fact">Fact</span> established; a source is cited</li>
      <li><span class="st decision" data-legend-item="decision">Your decision</span> decided by you, with date or rule</li>
      <li><span class="st proposal" data-legend-item="proposal">Proposal</span> Claude proposes; not settled</li>
      <li><span class="st unknown" data-legend-item="unknown">Unknown</span> not established yet</li>
      <li><span class="st awaiting" data-legend-item="awaiting">Awaiting you</span> asked of you at this gate</li>
    </ul>
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="wrap">Local file, not published. The Markdown sources are the source of truth; this page is a synthesis built after them. Screenshots are embedded so the file stands alone.</footer>
</body>
</html>
"""
OUT.write_text(page)
print(f"wrote {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")
