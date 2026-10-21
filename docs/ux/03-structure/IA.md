# UX-3 · Information architecture — Meridian AI service agent

> Status: DRAFT · Date: 2026-10-20 (**R-48 pass 2026-10-21:** demo login SCR-12, SCR-4 is the role switch, SCR-10 and SCR-11 behind the login) · Chosen concept: **C2** (chat thread + "what's settled" panel) and **S2** (queue → brief → evidence), built in direction **A5 Service desk, light mode first** (Innocent ✓ 2026-10-21, UX-2 gate: "alright we're going with A5").
> Inputs: [`USER_STORIES.md`](../01-planning/USER_STORIES.md), [`USER_FLOWS.md`](../01-planning/USER_FLOWS.md), [`SITEMAP.md`](../01-planning/SITEMAP.md), [`CONCEPTS.md`](../02-concepts/CONCEPTS.md), [`REFERENCES.md`](../02-concepts/REFERENCES.md), [`DESIGN-DIRECTIONS.md`](../../design/DESIGN-DIRECTIONS.md) (A5 anatomy and review notes), PRD v0.4.
> Companion: [`SCREEN_SPECS.md`](SCREEN_SPECS.md) (regions, states, copy, contracts). Contracts: [`UI_CONTRACTS.md`](UI_CONTRACTS.md) (written in parallel; CON IDs here are the UX-1 drafts, now CON-1…CON-22).

## What this file decides

For every screen, which content comes first (**primary**), which supports it (**secondary**) and which the person
opens only when they need it (**on demand**), and what must be on screen without scrolling on a phone.

**Example of how a level is decided.** On the chat (SCR-1), the reference number and the promise ("A representative will
get back to you within 1 business day, by Monday, October 19, 7:00 pm") are *primary*, even though they arrive late in the
conversation. A homeowner writes them down, and losing them to scroll is the exact failure C2 was chosen to prevent
(CONCEPTS C2). The source chip under an answer is *on demand*: it matters for trust, but most people never open it, so it
is one tap away, not expanded.

**How "visible without scrolling on a phone" is measured.** The viewport is **390 × 700 px** (an iPhone-class width, with
the browser's own bars already taken out). A "yes" means the item is inside that box in the screen's default state with no
scroll and no tap. "Collapsed" means a one-line summary is visible and the detail opens on tap.

## Rules that apply to every screen

These come from REFERENCES and the PRD; each screen below assumes them.

| Rule | Source | What it means for the hierarchy |
|---|---|---|
| A label on every message | R3-1, US-1 | Every turn carries its speaker label ("Meridian assistant · automated", "You", "Riley · representative (demo)"). The label is part of the message, never on demand |
| "Talk to a person" is always visible on the chat | R3-2, US-2, R-2 | It is primary on SCR-1 in every state, including safety, limits and while waiting. It sits in the composer bar, which stays on screen when the phone keyboard opens |
| No wait times, no queue positions | R3-4, R-26 | No region anywhere shows "about 5 minutes", "you are 3rd" or "agents online: 2". Staffing is a word ("Nobody online"), not a count |
| Demo bar and staffing banner are neutral | R2-3 | They are secondary on every screen and never use warning colour or a ⚠ icon |
| Red only for the safety card | R1-4, R2-3 | Overdue, errors, limits and P0 queue rows use words, icons and ink weight, not red. Red appears only on the SCR-1 safety card |
| Windows and the standard fee before identity; the code before the booking write | R1-1, FLOW-5, R-15 | On SCR-1 the slot card is primary before any code prompt exists; the code prompt appears only after a window is chosen |
| 12-hour times everywhere | UX-2 gate condition | "7:00 pm", "8:00 am – 12:00 pm", never "19:00". Headline times use the display face at 28 px (design.md §3.3) |
| The demo login gates every screen | R-48, US-28 | Nothing is readable without the login (SCR-12) except `/healthz`. No screen shows the credentials; they live in the README only |
| The role switch is always visible and shows the current role | R-48, US-28, SCR-4 | A shared header control on **every** screen after login: four options, the current one marked, one click to change. It is secondary in the hierarchy but never collapsed into a menu, never hidden by scroll, and never missing in any state, including errors and ended chats. It is labelled as a demo control ("Acting as"), neutral in colour, and sits with the demo bar, not inside the chat's own chrome. Sign out sits beside it |
| Plain sentence-case labels, with a one-line hint on customer screens | UX-2 gate condition (A5 form) | "Arrival windows" is followed by "The technician arrives any time in the window you pick". The hint is secondary text, shown on SCR-1, SCR-2 and SCR-3 wherever the screen spec gives one |

## Layout breakpoints (from C2 and S2)

| Surface | ≥ 1100 px | 900–1099 px | 700–899 px | < 700 px (phone) |
|---|---|---|---|---|
| SCR-1 chat (C2) | Thread + "what's settled" panel side by side | same | Thread only; panel becomes the strip under the top bar | Strip under the top bar, collapsed by default |
| SCR-6 case (S2) | Queue · brief · evidence, three columns | Queue becomes a drawer; brief · evidence | same | Queue drawer; brief and evidence become two tabs |
| Other staff screens | Full table or lanes | same | Tables reflow to stacked rows | Stacked rows |

---

## Per screen

### SCR-1 · Customer chat
Stories US-1…US-17, US-25, US-26, US-28 · Flows FLOW-1…FLOW-8, FLOW-12.

**Phone height budget (390 × 700), default state.** Top bar with the assistant label and the demo bar: 76 px · **role switch row (R-48): 44 px** · "What's
settled" strip, collapsed: 40 px · composer with "Talk to a person" and the message field: 100 px · thread: about 440 px
(about 408 px while the simulated-staffing banner shows). The safety card, when present, is pinned at the top of the
thread and takes about 280 px of it; the strip's one line then reads "DANGER · Leave the home immediately".

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Safety card**, when triggered: signal word DANGER, Meridian's two instructions, "Call 911 (from outside)" (CON-2) | Leaving the home is the only thing that matters in that moment (US-3, R-5). It outranks everything, including the latest turn | **yes**, pinned at the top of the thread; strip summary also switches to the danger line |
| Primary | **"Talk to a person"** button (CON-4) | One tap to a person, first time, every state (US-2, R-2) | **yes**, in the composer bar |
| Primary | **The latest turn** with its speaker label, and any card it carries: slot card, code prompt, account card, confirmation, change request, handoff card, limit notice (CON-2, CON-3) | It is the thing being answered or decided now | **yes**, the thread scrolls to it; a tall card shows its header and first action |
| Primary | **Message field and send** (CON-2) | The way to continue | **yes** |
| Primary | **"What's settled" summary**: the visit (date, window), the request (reference and due time), identity status (CON-2, CON-4, CON-5) | The four things a homeowner checks: who comes, when, what it costs, who gets back to them by when (C2) | **collapsed**: one line, e.g. "Wed Oct 21 · 8:00 am – 12:00 pm · MHC-C-0007 · due Mon 7:00 pm" |
| Primary | **Who is replying**: "Meridian assistant · automated" or "Riley (demo representative). Assistant paused." (CON-1, CON-3) | Answers "is this a person?" at a glance (US-1, US-15) | **yes**, in the top bar |
| Secondary | **Demo bar**: "Fri Oct 16, 2026 (demo date)", staffing word ("Nobody online" / "Simulated staff on shift (demo)"), "Demo guide" link (CON-1, CON-3) | The reviewer must never be misled about date or staffing (US-25, R-3, R-30), but a homeowner does not act on it | **yes**, one neutral line under the brand |
| Secondary | **Role switch** (shared header, SCR-4): "Acting as" with Customer · Rep · Supervisor · Owner, Customer marked (CON-10) | The reviewer flips to staff and back in one click (US-28); a homeowner never needs it, so it is neutral and secondary | **yes**, its own 44 px row under the demo bar |
| Secondary | **Simulated-staffing banner** "Simulated staffing (demo). No Meridian employee is online." (CON-1, CON-3) | Required whenever the simulation is on (R-30); neutral, not a warning | **yes** when the simulation is on |
| Secondary | **Earlier turns** | Context, already read | no, scroll up |
| Secondary | **"What's settled" panel, expanded**: visit block (date, window, technician, fee), request block (reference, promise text, due, follow-up choice, "original stays" line for a change request), identity row, who is replying (CON-2, CON-4, CON-5) | The detail behind the one-line summary | no, one tap on the strip (desktop: always visible beside the thread) |
| Secondary | **Quiet contact line** after a safety card: "Once you're outside and safe, you can leave a number here if you'd like." (CON-2) | An offer, never a prompt (R-6, R2-2) | yes, directly under the safety card, in body size, no field |
| On demand | **Source chip expansion**: file, section, version date, the quoted passage (CON-2) | Trust check most people skip (US-6) | no, tap the chip |
| On demand | **Quick checks list** (R-44), offered once with "Skip" as the first-class action (CON-2) | Very optional; never blocks booking | the offer line and "Skip" are visible; the list opens on tap |
| On demand | **"Open the demo inbox"** link on the code card → SCR-2 in a new tab | Only the reviewer needs it | yes, inside the code card |
| On demand | **Slot card day tabs** beyond the first visible days (CON-2) | The first open day is enough to start | first 3–4 day tabs visible; the rest scroll sideways inside the card |

### SCR-2 · Demo delivery inbox
Stories US-8, US-25, US-28 · Flows FLOW-3, FLOW-12.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Header statement** "Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification." | The page exists only because it is a simulation; it must say so first (US-25) | **yes** |
| Primary | **Newest code message**: recipient masked ("To ···02"), time, the 6-digit code in large tabular type, expiry ("Expires 2:17 pm") (CON-6) | The one thing the reviewer came for | **yes** |
| Secondary | **"Copy code"** and "Back to the chat" | Saves retyping; the chat is in the other tab | yes |
| Secondary | **Role switch** (shared header, SCR-4) (CON-10) | Always visible, current role marked (R-48) | yes, in the header |
| Secondary | **Older code messages**, each marked Used or Expired (CON-6) | History for a second attempt | no, scroll |
| On demand | "What this inbox is not": no follow-ups, codes only (OD-5) | Answers a reviewer's question once | no, a short note at the foot |

### SCR-3 · Demo guide and controls
Stories US-25, US-26, US-15, US-28 · Flows FLOW-8, FLOW-12.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **What is real and what is simulated**: real — the assistant, the knowledge base, the bookings in a working copy, what you type as Riley; simulated — the date, staffing, the code inbox, follow-ups ("Demo: recorded, not sent") | The reviewer's honesty question is answered before any control (US-25) | **yes**, as a two-column list collapsed to two short groups on a phone |
| Primary | **Staffing control**: current state in words, and the switch "Demo: simulate staff on shift" (CON-7) | The single control that changes the customer's experience most (FLOW-8) | **yes** |
| Secondary | **Role switch** (shared header, SCR-4) (CON-10) | Always visible, current role marked (R-48) | yes, in the header |
| Secondary | **How to play both roles**: use the role switch in this tab (customer, then representative), or keep the chat in one tab and the console in another; step list | Needed once per reviewer | partly: first step visible |
| Secondary | **Links**: chat, demo inbox, staff queue, monitoring, evaluation | Navigation to every surface (SITEMAP) | no, below the fold |
| Secondary | **Demo date** "Fri Oct 16, 2026 (demo date)" and how the clock moves (only the supervisor's "advance simulated time") (CON-8) | Explains the clock without offering a second control | no |
| On demand | **Reset the demo** with its consequence line and a confirm step (CON-9) | Destructive; must not be a first tap | no, at the foot, behind a confirm |

### SCR-4 · Role switch
Stories US-18, US-22, US-24, US-25, US-28 · Flows FLOW-8…FLOW-12. **R-48:** this screen no longer signs anyone in; the login (SCR-12) does. SCR-4 is a control in the shared header of every screen, plus an optional full page (`/role`, proposed) that explains each role.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **The switch itself**: "Acting as" with four options, Customer · Representative · Supervisor · Owner (on a phone: Customer · Rep · Supervisor · Owner), the current one marked with a tick and the word "current" in its accessible name (CON-10) | The whole point: flip sides in one click, and always know which side you are on (US-28) | **yes**, on every screen, in the header (SCR-1 on a phone: its own 44 px row) |
| Primary | **Current-role line** on staff screens: "Riley · demo representative", "Demo supervisor", "Demo business owner" (CON-10) | Names who you are acting as, in the staff chrome's own words | **yes**, in the console header |
| Secondary | **Full page, optional**: what each role sees, one line each, with the statement "These are demo roles, not real accounts. There is no second password." (CON-10) | Answers "what does Owner do?" once; the header switch is enough afterwards | n/a: its own page |
| Secondary | **Sign out** beside the switch (CON-22) | The way back to the login | yes |
| Secondary | **Simulated-staffing banner** when on (CON-7) | Required on staff screens too (R-30) | yes, when on |
| On demand | Why monitoring and evaluation open in every role (they are aggregates, behind the login like everything else) | Answers a reviewer's question | no, on the full page |

### SCR-12 · Demo login
Stories US-25, US-28 · Flows FLOW-12. The first screen of the deployment: nothing else answers without it. Phone first, one column.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Plain statement**: "Demo access · this is a demonstration of Meridian's assistant. These are not Meridian accounts, and everything here is fictional." | The reviewer must never think this is a real Meridian sign-in (US-25, HP-4) | **yes** |
| Primary | **Username and password fields, and "Sign in"** (CON-22) | The only thing to do on the page | **yes** |
| Primary | **Error line** when a login is refused: one message whatever the cause (CON-22) | A different message per cause would reveal which part was right | **yes**, directly above the fields |
| Secondary | **Where to find the login**: "The username and password are in the README that came with the submission." (no values) | Tells a reviewer who forgot where they are | yes, under the button |
| Secondary | **Session-ended line** when the visitor was sent back after a session expired (CON-22) | Explains why they are here again | yes, above the fields |
| On demand | **Show password** toggle | Typing a pasted password blind is the common failure | yes, beside the field |

### SCR-5 · Representative queue
Stories US-18, US-20 · Flows FLOW-7, FLOW-8, FLOW-9, FLOW-12.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **"Needs my action" list**, ordered P0 and P1 first, then due time, overdue first. Each row: priority tag ("P0 · Safety"), reference, reason, due time in 12-hour form with "Overdue" word and clock icon when past, owner, customer name (CON-11) | Picking the right next case is the job (US-18) | **yes**, the first 4–5 rows as stacked rows |
| Primary | **Live queue** section while simulated staff are on shift: live-queued customers, oldest first, P0/P1 on top, each with "Claim and join" (CON-11, CON-7) | A waiting customer outranks async work (FLOW-8) | **yes** when staffing is on (above "Needs my action"); hidden with a one-line explanation when nobody is online |
| Secondary | **Row details**: follow-up preference short form ("Phone · mornings"), Waiting wake-up time, "Demo seed" tag (CON-11) | Helps choose between two similar rows | yes, as a second line in each row |
| Secondary | **Console header**: the role switch with the current role marked ("Riley · demo representative"), demo date, staffing word, sign out (CON-10, CON-22, CON-7, CON-8) | Orientation, not action | yes |
| On demand | **Keyboard help** (J / K to move, Enter to open) | Power use on a laptop | no, a hint line under the list header on laptops; hidden on phones |
| On demand | **Filters** (mine, unowned) | The default order is already right | no |

### SCR-6 · Case view
Stories US-19, US-20, US-21 (also US-18, US-23, US-24 as the destination of their links) · Flows FLOW-8, FLOW-9, FLOW-10, FLOW-11.

**Laptop (≥ 1100 px).** Left: queue (SCR-5's list, compact). Centre: the brief. Right: the evidence column with the
*Sources* and *Conversation* tabs; the live-chat box sits under *Conversation* while joined. Read left to right: what's
next → what happened and what you decide → the proof (S2).

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Case header**: reason and priority ("Billing dispute · P3 Standard"), "REF MHC-C-0007", **due time as the headline** ("Due Mon Oct 19 · 7:00 pm"), "Overdue" when past, owner or "Unassigned, nobody owns it yet", "Demo seed" when seeded (CON-12) | What it is, how urgent, whose it is (US-19) | **yes** |
| Primary | **Promise shown to the customer** with the **follow-up preference beside it** (channel, destination and whether on record, best time) and the promise status (open, kept, missed, changed) (CON-12) | The commitment the representative must keep (R-26, R-27, consolidated §6) | **yes** |
| Primary | **The next action** for this state: Claim; or Join chat (live-queued); or Log a call / email, Set waiting, Resolve, Close unresolved, Release (CON-13, CON-14, CON-15) | The brief is for acting (US-19, US-20) | **yes**, a sticky action bar at the foot of the brief on a phone |
| Primary | **Brief, eight numbered sections** in fixed order: Why this came to you · What the customer needs · What we know for sure · What the customer says (not checked) · What the AI did · What we told the customer · What you need to decide · Who they are and how to reach them (CON-12) | The one-minute read (R-28) | partly: sections 1–2 visible, the rest scroll |
| Primary | **Live chat** while joined: the customer's messages and the reply box, labelled "You are replying as Riley (demo representative). The assistant is paused." (CON-14, CON-3) | The customer is waiting now | **yes** on a phone while joined: the Evidence tab opens on Conversation automatically, with the reply box pinned |
| Secondary | **Lifecycle line** (Unassigned → Claimed → In progress → Waiting → Resolved / Closed unresolved; Live-queued on the staffed path) (CON-12) | Where the case is in its life | yes, one compact row |
| Secondary | **Sources tab**: each pertinent source as a card, "what the AI saw" vs "now", with "Changed since" where they differ (CON-12) | Verify-in-place (R-29); secondary because the brief already states the facts | no on a phone (Evidence tab); yes on a laptop |
| Secondary | **Fact-check flag** on any section where the check removed something (CON-12) | Tells the reader the section is incomplete (US-19) | inside its section |
| Secondary | **Identity status** inside section 8 ("Entered the code sent to the phone on file. Demo simulation, not real ID proof.") (CON-12) | Needed before sharing private details | inside section 8 |
| On demand | **Conversation tab** (the full chat, with labels and times) (CON-12) | Full context, one click away (R-28) | no |
| On demand | **Flag** form (answer, brief or escalation; reason) (CON-16) | Used when something is wrong | no, a secondary button in the action bar |
| On demand | **Activity log** (claims, releases, recorded contacts with "Demo: recorded, not sent") (CON-12, CON-15) | Audit trail | no, under the actions |
| On demand | **Other cases for this customer**, by reference, status in words (CON-12) | Avoids duplicate work (R4-1) | no |
| On demand | **Assign / change priority** (supervisor only) (CON-13) | Supervisor action reached from SCR-7 | no |

### SCR-7 · Supervisor oversight
Stories US-22, US-23 · Flows FLOW-8, FLOW-10.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Alert lines** at the top, as decision lines: "P0 safety case MHC-C-0008 created at 2:16 pm, unowned. Assign it." · "Simulated shift ended with 1 customer waiting. Their case now has the 1-business-day promise." (CON-17) | Shift start "in under a minute" (profile §6) | **yes** |
| Primary | **Five lanes in fixed order**: P0 and P1 · Overdue · Due soon · Unowned · Stuck waiting. Each lane: count, then compact rows with reference, reason, owner, age, due, follow-up preference, and "Assign" (CON-17, CON-13) | The supervisor's whole job is that none of these is left (US-22) | **yes**: lane headers with counts and the first lane's rows |
| Secondary | **Demo controls strip**, labelled "Demo controls": simulated shift on/off (CON-7) and "Advance simulated time" (CON-8), with the current demo time | Supervisor actions in the story, clearly marked as demo | yes, one neutral strip under the header, collapsed to one line on a phone |
| Secondary | **Live queue length** while staffed ("2 customers waiting in chat"), no wait estimate (CON-17) | Staffing decision input | yes when staffed |
| Secondary | **Link to the review list** with its count of new flags (CON-16) | Quality work, after urgent work | no |
| On demand | **Assign / reassign / change priority** dialog with a required reason (CON-13) | One action at a time | no, opens from a row |

### SCR-8 · Review list of flags
Stories US-21, US-23 · Flows FLOW-9, FLOW-10.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Flags, newest first**: kind (answer, brief, escalation), reason, case reference link, the flagged message link, who flagged, when, status (New / Reviewed) (CON-16) | Someone has to decide each fix (US-23) | **yes**, first 4 rows as stacked rows |
| Primary | **Statement** "Nothing on this list changes the knowledge base, prompts or tests. People decide each fix." | R-37: the loop is human; the page must not imply automation | **yes**, under the title |
| Secondary | **Mark reviewed** with an optional note (supervisor) (CON-16) | Closes the loop | yes, per row |
| On demand | The flagged message's text, expanded inline (CON-16) | Context without leaving the list | no |

### SCR-9 · Business-owner outcomes
Stories US-24 · Flows FLOW-11.

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Headline numbers**, each with its denominator underneath: in-scope correct resolution as a labelled **estimate** from live chats ("n of N in-scope conversations"; the measured number is the held-out run on SCR-11), promises kept on time ("n of N promises due"), handoffs ("n of N conversations") (CON-18) | The owner's question: does the AI cut load without hurting customers (US-24) | **yes**, three stacked tiles |
| Primary | **Where the numbers come from**: "From stored conversations and cases, as of Fri Oct 16, 2:20 pm (demo time). Includes N demo seed cases." Never a target (CON-18) | A number without its basis is an opinion (business-metrics rule 1) | **yes**, one line under the tiles |
| Secondary | **Outcomes table**: resolved by AI, escalated → resolved by staff, escalated → open, abandoned, failed; each with count and denominator (CON-18) | Explains the headline | no |
| Secondary | **Handoffs by reason**, each reason opening its cases (CON-18) | Input to KB or scope changes | no |
| Secondary | **Missed promises**, by reference (CON-18) | The measured failure (consolidated §6) | no |
| On demand | **Cases behind a number**: a list of references opening SCR-6 (CON-18, CON-12) | Every number opens its cases | no, tap a number |
| On demand | **Link to Monitoring and Evaluation** (health kept apart, R-35) | Health is a different question | no, at the foot |

### SCR-10 · Monitoring
Stories US-27 · Flows FLOW-11. Behind the demo login, readable in any role (R-48 reversed the earlier open-access proposal).

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Alerts as decision lines** ("If p95 latency stays over 12.5 s per turn, check the model route"), firing ones first (CON-19) | Alerts live on this page; there is no push channel (R-35) | **yes** |
| Primary | **Health group**: volume, failures, latency p50 and p95, spend today against the $30 daily cap, last health-check restart (CON-19) | Does it run (business-metrics rule 2) | **yes**: the first three tiles |
| Primary | **Data age line**: "Updated 2:20 pm (demo time) · redacted · traces are not shown here" (CON-19) | Honesty about freshness and privacy (R-36) | **yes** |
| Secondary | **Correctness group**, visibly separate: containment (correct resolution, labelled an estimate) with denominator, escalations by reason (CON-19) | Health and correctness never share a row (R-35) | no |
| On demand | **Per-measure definitions** (what counts as a failure, what latency is measured) | Reviewer checks | no |

### SCR-11 · Evaluation report
Stories US-27 · Flows FLOW-11. Behind the demo login, readable in any role (R-48 reversed the earlier open-access proposal).

| Priority | Content | Why at this level | Visible without scrolling on a phone? |
|---|---|---|---|
| Primary | **Headline from the sealed held-out split**: correct-resolution rate with "n of N held-out cases", run ID and date, and the line "Held-out split: scored only, never tuned against" (CON-20) | The README number must be the honest one (R-38) | **yes** |
| Primary | **Run identity**: run ID, date, split sizes, test-set mix summary (CON-20) | Every number names its run (R-39) | **yes**, one line |
| Secondary | **Measures table, per split**: accuracy on handled drivers, escalation recall, false escalation, wrong-answer rate, retrieval hit rate (top 3), safety-first and request-honoured gates, promise consistency, each with denominator; dev-split columns labelled "Dev (we read and fixed these, so it overstates)" (CON-20) | Explains the headline (R-39) | no |
| Secondary | **Test-set mix** by category and source (transcript-derived vs labelled synthetic) (CON-20) | Shows the set reflects real calls (source-authority rule 6) | no |
| On demand | **Failure examples** from the dev split only, redacted (CON-20) | Shows what was fixed; held-out answers stay sealed | no |

---

## Cross-screen links (where each screen's next step lands)

| From | Action | Lands on |
|---|---|---|
| SCR-1 | "Demo guide" | SCR-3 |
| SCR-1 code card | "Open the demo inbox" | SCR-2, new tab |
| Any screen | Role switch: Customer | SCR-1 (the same chat, resumed) |
| Any screen | Role switch: Representative / Supervisor / Owner | SCR-5 / SCR-7 / SCR-9 (on SCR-2, SCR-3, SCR-10, SCR-11 the screen stays and the role changes) |
| SCR-12 | Sign in | The page that was asked for, else SCR-1 as the customer |
| Any screen | Session ended | SCR-12 |
| Any screen | Sign out | SCR-12 |
| SCR-5, SCR-7, SCR-8, SCR-9 | Open a case | SCR-6 |
| SCR-9, SCR-3 | Monitoring, Evaluation | SCR-10, SCR-11 |
| SCR-6 | Back to queue | SCR-5 (or the screen it came from) |
