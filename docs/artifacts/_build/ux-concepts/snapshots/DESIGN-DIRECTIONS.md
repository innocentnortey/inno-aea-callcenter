# Design directions from Dribbble: Meridian AI service agent (UX-2, step 1)

> **DECISION (Innocent, 2026-10-21, UX-2 gate):** "alright we're going with A5, use parallelization as much as possible to finish (use sonnet)". **A5 Service desk**, light first, on concepts C2 and S2. A6 is not taken forward. UX-3 `design.md` makes A5 exact.
> **Before the pick (Innocent, ~00:00 CT 2026-10-21):** "drop everything except for A5 thats really goot lets do one more". **A1–A4 are dropped** (kept below as history). **In play: A5 Service desk and A6 Branch office**, both shown as look sheets; awaiting his pick.
> **Decision changed (Innocent, 2026-10-20, ~23:05 CT, superseded):** "ill be honest i actually didnt like either of the uis you showed me A1 and A2 were very similar i want to go with A3 its nicer on the eyes". **A3 Dispatcher's log**, light mode first (carried
> over from the earlier choice). A1 and A2 read alike at a glance; A3 is softer. An A3 prototype is built for him to confirm.
> **Earlier the same night (superseded):** "lets go with A2 light mode and yeah you have my approval": **A2 Route sheet, light mode first.** Over A1 (Claude's
> recommendation) and A3. Conditions carried to UX-3 `design.md`: 12-hour times everywhere ("7:00 pm", not "19:00"),
> keeping the headline size and weight; soften A2's cold risk for homeowners with sentence-case glosses under mono labels.
> **Status (research, kept as written):** PROPOSAL 2026-10-20 · UX-2 Concepts, step 1 (texture research). No direction was chosen then; the ★ UX-2 gate
> (*which direction and which concept?*) is Innocent's. Since this file was written, A1 and A2 were built as clickable
> direction prototypes (`docs/artifacts/2026-10-20-direction-A1-work-order.html`, `…-A2-route-sheet.html`) on the
> recommended concepts C2 and S2 ([CONCEPTS.md](../ux/02-concepts/CONCEPTS.md)); see *Review notes from the built screens*.
> **Starting point (Innocent, 2026-10-20):** he chose family **A, "Dependable dispatch"** from the company profile
> ([§7](../analysis/2026-10-20-meridian-company-service-profile.md#7-brand-and-color-direction)): competent, organized, on
> time; structured and information-dense; clear timelines for windows and promises; status as labelled steps; a sturdy
> sans with tabular numbers. Its two risks to test: **it can feel cold to a stressed homeowner**, and **density may hurt on
> a phone**. So the three directions below are all takes on dependable dispatch. They differ in **texture and component
> construction**, not colour. Colour values are UX-3's job (`design.md`), inside the profile's colour roles.
> **Method:** Dribbble searched live in the Chrome DevTools MCP, isolated context `aea-callcenter-ux`, 2026-10-20. Twelve
> searches: "dispatch dashboard", "field service app", "hvac app", "home services booking", "customer support chat",
> "help desk inbox", "ticket queue dashboard", "appointment booking mobile", "chat assistant mobile", "service request
> tracking", "support ticket web app", "technician scheduling dashboard". That gave **547 unique shots** (raw lists in
> `references/search/*.json`, merged in `references/search/all-shots.json`), all reviewed as 19 numbered contact sheets.
> 36 were opened at 1200×900, and **15 are kept** below.
> **Internal design reference only** (S-186): these are other designers' work, credited beside every use, never copied into
> the product, the demo or anything published.

**What stays fixed whichever direction wins:**

- the UX-1 planning set: stories, flows and sitemap ([`../ux/01-planning/`](../ux/01-planning/));
- the colour roles from profile §7:
  - safety red is reserved for safety;
  - the primary action is never red or orange;
  - status is never shown by colour alone;
  - times and amounts use tabular numerals;
  - light and dark themes are both designed;
- WCAG 2.2 contrast (S-180);
- the honesty rules:
  - no countdowns, queue positions or wait estimates we can't measure;
  - the promise text comes from the policy table;
  - "recorded, not sent" for demo contact.

Times, fees and references in the anatomy tables (8 am – 12 pm, $89, MHC-C-0007, Mon Oct 19, 7:00 pm) only show the
construction. They are illustrative. Real windows come from the scheduling DB, real fees from the fee schedule, and the
promise wording from the policy table.

## Recommendation (historical: written for A1–A3 on 2026-10-20; Innocent picked A5 on 2026-10-21)

**A1 · Work order.** It carries Innocent's brief for this family almost word for word, at both widths, without changing
how things are built:

- **status as labelled steps:** a numbered step rail;
- **timelines for windows and promises:** a time bar with a "now" marker;
- **dense but readable records:** label-over-value field grids.

The phone references (dr-07 Handsel, dr-10, dr-08) show this construction holds up one-handed. The console references
(dr-06, dr-09, dr-11) show the same parts carrying a case view.

It answers the "cold" risk with plain-language step labels and sentences ("Your technician arrives between 8 and
noon"), not with decoration. It answers the "density" risk by stacking the same field grid into one column on a phone.

**A2 · Route sheet** is the boldest and most "dispatch" of the three, and the strongest for the staff console. Its mono
labels and ticket stubs are the most likely to feel cold to a homeowner.

**A3 · Dispatcher's log** is the hedge if A1 still feels cold in a prototype. It leads with who is speaking, and is the
least dense.

If Innocent wants to choose by using them (phases.md step 4), build **A1 and A2** as clickable direction prototypes: they
are the two furthest apart in construction.

---

## A1 · Work order (recommended)

- **Feeling:** "someone has opened a proper job for me, and I can see every step of it."
- **Idea:** every reply that matters is a small **work-order sheet**: an ID, a field grid and a numbered step rail. The
  conversation sits between the sheets. Exceptions arrive as full-width **banner rows**.
- **Why it fits the homeowner (stressed, phone in hand):**
  - each sheet answers the four trust questions in fixed places: who is coming, when, what it costs, who calls back by
    when (profile §6);
  - the step rail shows what happens next without the customer having to ask;
  - one column, large tabular times.
- **Why it fits the staff console (dense, laptop):**
  - the eight-heading brief *is* a work order: headings as numbered sections, facts as field rows;
  - sources sit beside each fact;
  - case state is the same rail the customer saw.

### Component anatomy

| Part | Construction | From |
|---|---|---|
| Canvas | Cool steel-grey ground; content sits on white **sheets** with a 1px ink top rule and squared 4px corners. The console background carries a faint 24px grid. Not cream, not a card grid | dr-06, dr-09 |
| Navigation / steps | A **numbered step rail**: filled check discs for done steps, a ring on the current one, hollow for future ones, each with a plain label and a tabular timestamp on the right ("Request submitted · 2:45 pm"). On the phone it sits inside the relevant sheet; on the console it heads the case | dr-10, dr-06 (Service timeline: Reported → Reviewed → Assigned → In progress) |
| Headline | Condensed sans display (IBM Plex Sans at width 85, 600) for sheet titles ("Repair visit", "Request MHC-C-0007"); never a hero headline on the chat | dr-06 ("WO-4821 · Intermittent power fault") |
| Conversation | A single column of turns between sheets. The chat header shows "Meridian assistant · automated" and the demo date chip "Fri Oct 16, 2026 (demo date)" | dr-07 (single-column task screens) |
| Bubbles / transcript | Assistant turns are text on the canvas with no bubble and a small label line. Customer turns are an ink-filled block at the right. Sheets break the rhythm, so the eye lands on facts, not chatter | dr-12 (speaker label above each turn) |
| Input | A docked bar: text field plus a square send button. **"Talk to a person"** is a persistent text button in the bar's top edge, never hidden in a menu | dr-07 (sticky footer action), REFERENCES R2/R3 findings |
| Slot card | Day chips in a row (Thu 22, Fri 23 …), then **arrival windows as a two-column grid** of 4-hour ranges ("8 am – 12 pm"). Taken windows are struck through and say "Taken"; member-reserved windows say "Members". A summary footer gives "Thu Oct 22 · 8 am – 12 pm · $89 diagnostic" and **Book this window** | dr-07 (Handsel "Arrival window" grid + footer), dr-08 (date chips, time-slot grid) |
| Confirmation | A sheet titled with the booking ID. Field grid: Date · Window · Technician · Fee that applies · Address. A **time bar** from 8 am to 12 pm with the window filled. The rail reads "Booked ✓ → Confirm reminder → Visit" | dr-07 ("Marisol is on her way" time bar), dr-10 |
| Handoff card | A sheet headed by the reference "MHC-C-0007" (mono). Line 1 is the exact promise ("A representative will get back to you within 1 business day"). Line 2 is a **promise bar**: "Now · Fri 2:14 pm" → "Due · Mon Oct 19, 7:00 pm", with no countdown. Below: the follow-up choice (email / phone, window) as two segmented rows. It stays pinned at the top of the chat after it is shown | dr-10 (Request #DUN-0042 with progress), dr-11 (First due / Resolution due fields) |
| **Safety card** | The only full-bleed block in the product: a red band with the signal word **DANGER** and a warning icon, then Meridian's fixed instruction as **numbered actions** ("1 Leave the home immediately. 2 Call 911 or your gas utility from outside." — the KB's words, split only into numbered lines; corrected 2026-10-20 from "now"). Pinned above everything. No rail, no fee, no booking on it | dr-06 (full-width exception bar), REFERENCES R2 |
| Status / priority | Priority is a **filled square tag with its word**: "P0 Safety", "P1 Emergency", "P2 Time-sensitive", "P3 Standard", "P4 Routine". Case states sit on the rail (Live-queued → Unassigned → Claimed → In progress → Waiting → Resolved / Closed unresolved). Overdue is a word plus a clock icon, never colour alone | dr-09 (Severity & SLA due column), dr-11 (Ticket ID / First due / Priority fields) |
| Staff queue rows | Table rows: priority tag · reference (mono) · reason · customer · **due** (tabular, "Mon 7:00 pm · in 2 h") · owner. P0/P1 rows sit in a separate band at the top, headed "Safety and danger" | dr-09 (Urgent Attention band above the table) |
| Brief layout | Eight numbered sections in the fixed order, each a field grid. Facts carry a source link; customer claims sit under their own heading in italic with "not checked". The promise is section 6, with the follow-up preference beside it | dr-06 (Asset information grid, Technician notes & handoff), dr-11 (activity + properties) |
| Buttons | Rectangular, 6px radius, filled ink-blue primary, quiet secondary text buttons. One primary per sheet | dr-06 ("Start service" / "Assign") |
| Iconography | 1.5px line icons, 20px, only beside field labels and in banner rows | dr-06, dr-11 |
| Typography | **IBM Plex Sans** (OFL; digits tabular by default; a width axis gives the condensed display cut in the same family) with **IBM Plex Mono** (OFL) for references and IDs. Checked 2026-10-20 with fontTools: Plex Sans and Plex Mono digits are equal width | — |
| Motion | The rail's next disc fills when a step completes (200 ms). A new sheet slides up 8 px. The promise bar draws left to right once. All of it is off under `prefers-reduced-motion` | dr-10 |

- **Safety stays unmistakable:**
  - red appears in exactly one component, the safety card;
  - no other banner, tag or button uses the red family: overdue uses an icon plus words, and P0 uses the word "Safety"
    with a neutral ink tag;
  - the card always carries the signal word, an icon and numbered text (S-180).
- **House-texture check (reject if more than 2):**
  1. Cream canvas with serif heading: **no** (steel grey, condensed sans).
  2. Coloured left-border cards, thin grey outlines, identical 10–12px radii in an even grid: **watch.** The sheets use a
     top ink rule and 4px corners, not left borders or a card grid. Field dividers are hairlines, so this could drift if
     built carelessly.
  3. Outlined pill badges on everything: **no** (filled square tags, step rail).
  4. Muted sage, teal or forest as the only accent: **no.**
  5. One safe sans everywhere, no display face: **no** (condensed display cut, mono IDs). **Watch on the built screens:**
     the condensed Plex cut is subtle at 18–26 px, so headings can read as one plain sans.
  6. Flat, no texture, depth or motion: **no** (lifted sheets, grid ground, rail motion).
  7. The previous project's skeleton recoloured: **no** for the texture research (a single-column chat with inline
     sheets). **Watch on the built screens:** built on concepts C2 and S2, the chat has two columns and the console three,
     a shell close to Riverside's and to generic help desks. The texture differs; the skeleton is shared.

  **Result: 0 matches, 3 watches (2, 5, 7) → passes.**
- **Scanning check:**
  - **Top → bottom on the phone:** greeting and date chip → conversation → the latest sheet → the input. The sheet's
    primary button (Book this window, Choose follow-up) is the last thing in the sheet, right above the input.
  - **Left → right on the console (SCR-6):** queue context (priority, reference, due) → the brief (why, what they need,
    facts) → the conversation and sources. The column headings sit on one baseline. Clicking a fact highlights its
    source on the right, so the eye's move is caused by what was on the left.
  - **Motion:** only for the next step: the rail fill and the sheet arrival.
- **Wireframe impact:**
  - **SCR-1:** reply cards become sheets with field grids and a rail. The handoff card gains a promise bar and pins to the
    top. The safety card becomes a full-bleed numbered block.
  - **SCR-6:** the brief becomes eight numbered field-grid sections, with the case-state rail as the header.
  - The IA (which regions exist) does not change.

**References:**

- **Legacy Application Modernization — Medical Equipment Service** — Insoftex · https://dribbble.com/shots/27732907-Legacy-Application-Modernization-Medical-Equipment-Service · `references/dr-06-insoftex-work-order.jpg` (search: "field service app")
- **Handsel: Home Services Booking App for Android** — Lynon Solutions · https://dribbble.com/shots/27762553-Handsel-Home-Services-Booking-App-for-Android · `references/dr-07-handsel-home-services.jpg` (search: "home services booking")
- **Home Services App Design** — Mamunur Rashid · https://dribbble.com/shots/27770100-Home-Services-App-Design · `references/dr-08-home-services-steps-slots.jpg` (search: "home services booking")
- **PropOpsAI — AI Maintenance Triage for Real Estate Operations** — Mayura Consultancy Services (MCS) · https://dribbble.com/shots/27146438-PropOpsAI-AI-Maintenance-Triage-for-Real-Estate-Operations · `references/dr-09-propops-ai-triage.jpg` (search: "ticket queue dashboard")
- **Service Request Mobile App UI/UX** — Juice Lab UI/UX Development Agency · https://dribbble.com/shots/27651506-Service-Request-Mobile-App-UI-UX · `references/dr-10-service-request-tracking.jpg` (search: "service request tracking")
- **Helpdesk — Ticket management** — Jayaprakash · https://dribbble.com/shots/27632504-Helpdesk-Ticket-management · `references/dr-11-helpdesk-ticket-activity.jpg` (search: "support ticket web app")

**Do not carry over from these shots:**

- dr-08's red "Need it urgently?" surcharge chip: red is safety-only, and urgency is asked, not sold;
- dr-09's colour-only severity chips;
- dr-06's red "Out of service" pill;
- dr-07's star ratings and "Book again" marketplace parts (out of scope).

---

## A2 · Route sheet

- **Feeling:** "dispatch has this; here is the plan, to the minute."
- **Idea:** the product reads like a dispatcher's **route sheet and ticket stubs**:
  - mono caps labels ("ARRIVAL WINDOW", "REF");
  - **big tabular times** as the hero numbers;
  - torn-off **stub cards** that carry the reference;
  - a **numbered stop timeline** for every sequence.
- **Why it fits the homeowner:** the window and the reference are the two things a customer writes down, and here they
  are the biggest things on screen. The stub is a physical metaphor for "keep this".
- **Why it fits the staff console:** this is the most information-dense of the three. Keyboard-triage queue rows,
  priority blocks and due times in mono give a supervisor the "under a minute at shift start" read (profile §6, Q12).
- **Risk:** the coldest of the three. Mono caps cost reading effort for a stressed person. It needs sentence-case body text
  everywhere except labels and IDs.

### Component anatomy

| Part | Construction | From |
|---|---|---|
| Canvas | Pale cool "map paper" with faint hairline route lines and a fine grid. The console can run as a dark ink board, with the light theme designed alongside | dr-04 (Arcline: grid paper, route hairlines, dark command centre), dr-01 |
| Navigation / steps | A **route-stop timeline**: START and END blocks, numbered stop discs on a vertical line, each stop with a labelled state chip ("Completed", "En route", "Scheduled") and planned versus actual times | dr-01 (Growth Dispatch route panel) |
| Headline | Mono caps eyebrow ("REPAIR VISIT · MHC-A-0142"), then the **time as the headline** in Barlow Semi Condensed 700, e.g. "8:00 → 12:00" | dr-02 (16:10 → 16:40 arrival window hero) |
| Conversation | A narrow transcript column on the map-paper ground. Stub cards break out slightly wider than the text column | dr-02 |
| Bubbles / transcript | No bubbles. Each turn is a block with a mono caps speaker label ("ASSISTANT · AUTOMATED", "YOU", "RILEY · REP (DEMO)") and a tabular timestamp right-aligned on the same line | dr-03 (mono metadata lines), dr-04 |
| Input | A full-width bar with an ink square send key. "Talk to a person" is a labelled key at the left of the bar | dr-03 (composer bar with keyboard hint) |
| Slot card | A **dark stub**: day header in mono, windows as rows "08:00 – 12:00 · OPEN", "12:00 – 16:00 · TAKEN" (struck), "MEMBERS" tag. The chosen row inverts. The stub's tear-off end shows the fee | dr-02 (slot / was rows, "RELEASED"), dr-04 (BW-48213 stub "15:00–15:30 · 3 parcels") |
| Confirmation | A white **ticket stub** with a perforated divider. Main part: big window time, date, technician, fee. Stub part: the reference in mono and a decorative reference strip (aria-hidden) | dr-04 (barcode stub), dr-02 ("New window sent · 16:10 – 16:40" confirmation bar) |
| Handoff card | A stub headed "REF MHC-C-0007". The promise line in sentence case, then "DUE · MON OCT 19 · 19:00" in big tabular type. Follow-up choice as two mono option rows | dr-04, dr-02 |
| **Safety card** | Breaks the stub pattern entirely: a full-width red sheet with no perforation and no mono, the signal word **DANGER**, an icon, Meridian's instruction as numbered actions in large sentence-case type. Pinned | contrast with dr-02/dr-04 (deliberately unlike every other card) |
| Status / priority | **Square priority blocks** in mono ("P0", "P1" …) with the word beside them ("P0 · SAFETY"). Case state is a stop on the route timeline | dr-04 ("Needs attention": P1/P2 tags), dr-03 (URGENT / HIGH / NORMAL blocks) |
| Staff queue rows | Keyboard-triage rows: priority block · "#MHC-C-0007" in mono · reason · customer initials disc · **due** in mono, right-aligned ("MON 19:00"). J/K to move, Enter to open. The selected row lifts | dr-03 (QueueBase "Clear the queue" inbox sorted by SLA), dr-04 |
| Brief layout | Eight numbered **stops** down the left, each a block with a mono label and sentence-case content. Sources open as stubs in the right rail | dr-01, dr-05 (Amara Osei: TIME / CLINICIAN / ROOM / LIVE STATUS label grid; readiness checklist; contact history "delivered … not opened") |
| Buttons | Rectangular, 4px radius, mono caps labels for console actions ("CLAIM", "JOIN CHAT"), sentence case for customer actions ("Book this window") | dr-03, dr-04 |
| Iconography | Minimal: stop discs, a pin, a clock. Numbers do the work | dr-01 |
| Typography | **Barlow** (OFL; a DIN-like highway-signage sans; `tnum` feature present, checked 2026-10-20) with Barlow Semi Condensed for display, and **JetBrains Mono** (OFL; monospaced digits) for labels, IDs and times | — |
| Motion | The route line draws to the current stop. A new stub "tears in" with a 6 px slide. Reduced motion: none | dr-02 (dotted route curve) |

- **Safety stays unmistakable:**
  - everything else is a stub or a mono block, and the safety card is the only plain, full-width, red, sentence-case
    sheet, so it is unlike everything around it in form as well as colour;
  - dr-03's dark-red canvas is **rejected** for us: red ground anywhere would spend the safety signal.
- **House-texture check:**
  1. Cream with serif: **no**.
  2. Left-border cards, grey outlines, identical radii in a grid: **no** (stubs, perforations, blocks).
  3. Outlined pills everywhere: **no** (square mono blocks).
  4. Muted sage, teal or forest: **no**.
  5. One safe sans: **no** (Barlow plus mono).
  6. Flat: **no** (route lines, grid paper, stubs, depth).
  7. Previous skeleton: **no**.

  **Result: 0 matches → passes.**
- **Scanning check:**
  - **Top → bottom:** eyebrow → big time → stop timeline → the action at the stub's foot.
  - **Left → right on SCR-6:** the stop list (brief sections) → the open stop's content → the source stub. The rail of
    stop numbers lines the column baselines up naturally.
  - **Motion:** only the route line advancing to the current stop.
- **Wireframe impact:**
  - **SCR-1:** reply cards become stubs. The latest window and the reference become the largest type on screen.
  - **SCR-6:** the brief becomes a stop list with a detail pane, which is a two-level layout, not one long page. The
    queue (SCR-5) gains keyboard triage.
  - The IA is unchanged.

**References:**

- **Growth Dispatch — Dashboard** — Borkat Ullah · https://dribbble.com/shots/25055087-Growth-Dispatch-Dashboard · `references/dr-01-growth-dispatch-route.jpg` (search: "dispatch dashboard")
- **Field Service Dispatch Mobile iOS App Design** — Purrweb UI/UX Agency · https://dribbble.com/shots/27613480-Field-Service-Dispatch-Mobile-iOS-App-Design · `references/dr-02-purrweb-dispatch-board.jpg` (search: "field service app")
- **Customer Support Inbox Web App Design** — Purrweb Web Design · https://dribbble.com/shots/27681874-Customer-Support-Inbox-Web-App-Design · `references/dr-03-queuebase-clear-the-queue.jpg` (search: "help desk inbox")
- **Arcline — Autonomous Fleet Command Center (Web App)** — Asaad Habib · https://dribbble.com/shots/27789554-Arcline-Autonomous-Fleet-Command-Center-Web-App · `references/dr-04-arcline-command-center.jpg` (search: "ticket queue dashboard")
- **Clinic Scheduling Dashboard** — Mahima Mahajan · https://dribbble.com/shots/27620977-Clinic-Scheduling-Dashboard · `references/dr-05-clinic-appointment-exception.jpg` (search: "technician scheduling dashboard")

**Do not carry over from these shots:**

- dr-03's **SLA countdown timers** ("04:32"): the brief's honesty rules forbid countdowns, so we show the due time instead;
- dr-03's red canvas;
- dr-02's "+38 MIN OVER" red tag;
- dr-04's red "Critical" chip.

---

## A3 · Dispatcher's log

- **Feeling:** "a calm person on the line is writing this down with me."
- **Idea:** the conversation is a **log**:
  - every turn says who wrote it;
  - system events are dated dividers;
  - the assistant's working steps appear as small **step cards** that show what it is doing and offer "Talk to a person"
    beside the main choice;
  - appointments are **label-value rows with icons**, not grids.
- **Why it fits the homeowner:**
  - the least dense of the three: it reads like a text thread, the format a phone user already knows;
  - "who is speaking" is answered on every line, which is exactly the "is this a person?" question (profile §6, Q8;
    US-1, US-15).
- **Why it fits the staff console:**
  - a three-pane log: activity log in the middle, the case properties and brief on the right;
  - the representative reads the same log the customer saw, plus internal notes.
- **Risk:** the least "dispatch" of the three. Its density comes from rows, not grids. It is the closest to a generic chat
  app, so its texture must come from the log construction, not from rounded bubbles alone.

### Component anatomy

| Part | Construction | From |
|---|---|---|
| Canvas | A single white log column on a soft cool-grey ground. Day dividers ("Today", "Fri Oct 16 · demo date") centred on the log | dr-14 (Solea in-app chat: "Today" divider, map snippet in thread) |
| Navigation / steps | No rail. Progress is written into the log as **event lines** ("Window held · Thu 8 am – 12 pm", "Case MHC-C-0007 created"), each with an icon and a tabular time | dr-11 (activity log with "View 2 changes", system events) |
| Headline | The chat header names the parties: "Meridian Home Comfort · Automated assistant". The reference appears in the header once a case exists ("Reference MHC-C-0007") | dr-12 ("Agent: Skylar (Nimbus Tech Support) · Reference Number: NC-20250412-K8Z3R1") |
| Conversation | Turns grouped by speaker, a **name line above each group** with time beneath, generous 16 px spacing | dr-12 |
| Bubbles / transcript | Soft rounded blocks (16 px). The assistant's are tinted neutral, the customer's ink-tinted at the right, the representative's carry a "Representative (demo)" name line and a different shape (squared top-left). Never an avatar that looks like a person for the assistant | dr-12, dr-14 |
| Input | A rounded field with a round send button in the primary colour. "Talk to a person" is a chip that is always present above the field | dr-14 (composer with suggestion text) |
| Slot card | **Label-value rows with icons:** Service · Window · Duration · Address · Fee. Then "This week · Oct 19 – 23" and, per day, **time-range chips** ("8:00 to 12:00", "12:00 to 16:00"). The chosen chip fills | dr-15 (Solea "New appointment": Service Type / Time "Between 8:00 to 17:00" / Duration / Location rows, day groups with time-range chips) |
| Confirmation | The same label-value rows, now with a "Booked" event line above them in the log. No separate sheet | dr-15, dr-11 |
| Handoff card | An **assistant step card** in the log: title "Passing this to a person", the reason in one sentence, the promise sentence, "Due Mon Oct 19, 7:00 pm", the reference, then the follow-up choice as two radio rows and a **Confirm** button with "Change" beside it | dr-13 ("AI STEP · Classify intent": reasoning text, radio choices, "Confirm and continue / Route to a human") |
| **Safety card** | **Interrupts the log:** it is not a turn but a pinned panel above the log, red band, signal word **DANGER**, icon, numbered actions. The log below it greys out while the card shows; under it, one quiet line offers contact for once the customer is outside (FLOW-2) | contrast with dr-12 / dr-14 |
| Status / priority | Status as a **sentence with an icon** in event lines ("Waiting for a representative · due Mon 7:00 pm"). Priority on the console as a small filled tag with its word | dr-11 (properties: Priority "Medium" with bars icon, First due / Resolution due) |
| Staff queue rows | Inbox list: customer name, the one-line reason, priority tag, due time, a two-line preview of the last customer message | dr-11, dr-14 |
| Brief layout | Right-hand properties panel holds the brief's eight headings as collapsible sections. The centre is the full log, with internal notes visibly different (tinted, "Internal note" label) | dr-11 (activity centre + properties right) |
| Buttons | Fully rounded primary for customer actions; compact 8 px for console actions | dr-14, dr-13 |
| Iconography | Icon per label row (calendar, clock, pin, receipt) and per event line | dr-15, dr-11 |
| Typography | **Bricolage Grotesque** (OFL, display, `tnum` present) for the header and card titles, **Public Sans** (OFL; the US Web Design System face; `tnum` present, checked 2026-10-20) for everything else | — |
| Motion | A "Riley has joined" divider slides in. The step card's Confirm button gains focus with a single pulse. Reduced motion: none | dr-14 |

- **Safety stays unmistakable:**
  - the safety panel is the only element that sits *outside* the log, and the only red;
  - greying the log below it says "stop chatting" without a word, and the words say it too.
- **House-texture check:**
  1. Cream with serif: **no** (cool grey, grotesque display).
  2. Left-border cards, grey outlines, identical radii in a grid: **no** (log column, mixed radii).
  3. Outlined pills on everything: **watch.** Divider and suggestion chips are pills; keep them filled and limited to
     events and the person chip.
  4. Muted sage, teal or forest: **no**.
  5. One safe sans: **no** (Bricolage display).
  6. Flat: **no** (soft depth, event motion).
  7. Previous skeleton: **watch.** The console's three panes (list · log · properties) are close to the generic help-desk
     layout and to Riverside's three-column construction. The meaning differs (queue · conversation · brief), but it
     must not be the same shell recoloured.

  **Result: 0 matches, 2 watches → passes, narrowly.**
- **Scanning check:**
  - **Top → bottom:** header with parties and reference → log in time order → the latest step card's Confirm → the input.
  - **Left → right on SCR-6:** queue list → the log → the brief/properties. The baseline is shared, and selecting a brief
    fact scrolls the log to the turn it came from.
  - **Motion:** only for the join event and the Confirm focus.
- **Wireframe impact:**
  - **SCR-1:** sheets and stubs become log rows and step cards. The safety card moves out of the log into a pinned panel.
  - **SCR-6:** the brief moves to a right properties panel, and the conversation becomes the centre of the case view.
    This changes the emphasis of the IA (a UX-3 question), not its regions.

**References:**

- **Customer Support Chat** — Mikadifo · https://dribbble.com/shots/26069240-Customer-Support-Chat · `references/dr-12-support-chat-reference.jpg` (search: "customer support chat")
- **Design Case Study #7 — when the AI stops and asks** — DΞNYS SΞRGUSHKIN® · https://dribbble.com/shots/27713288-Design-Case-Study-7-when-the-AI-stops-and-asks · `references/dr-13-ai-step-route-to-human.jpg` (search: "support ticket web app")
- **AI Services CRM · Solea AI · In-app chat** — Pixel One · https://dribbble.com/shots/27719693-AI-Services-CRM-B2B2C-UI-UX-Solea-AI-In-app-chat · `references/dr-14-solea-in-app-chat.jpg` (search: "technician scheduling dashboard")
- **AI Services CRM · Solea AI · Light/dark** — Pixel One · https://dribbble.com/shots/27719706-AI-Services-CRM-B2B2C-UI-UX-Solea-AI-Light-dark · `references/dr-15-solea-new-appointment.jpg` (search: "technician scheduling dashboard")
- also cites dr-11 (A1's list)

**Do not carry over from these shots:**

- dr-13's "62% confident" figure: we have no calibrated confidence to show, and a number would read as a promise;
- dr-14's orange send button: the primary action is never orange;
- dr-12's typing indicator for an assistant that is not a person.

---

## A4 · Account statement

> **Added 2026-10-20 (late), proposal, after Innocent's feedback on A1–A3.** He found A1 and A2 "very similar" and
> preferred A3 because it is "nicer on the eyes". He asked for a fourth direction: "styles that are utility
> professionally but soft on the eyes". A4 is still dependable dispatch (profile §7), told the way a good utility,
> bank or insurer tells it. It is built to differ from A1–A3 **at a glance**, not just in construction: different
> palette temperature, density, shape language and type (see the table at the end of this section).
> **Method:** Dribbble searched live in the Chrome DevTools MCP, isolated context `aea-callcenter-ux`, 2026-10-20, with
> fourteen new searches: "utility dashboard", "energy utility app", "utility mobile app", "customer portal soft",
> "calm dashboard", "soft ui dashboard light", "muted dashboard", "field service app light", "banking app minimal",
> "support inbox light", "appointment booking soft ui", "service app pastel", "insurance app", "insurance web app".
> That gave 672 results and **645 shots not used in dr-01…dr-15** (raw lists in `references/search/a4-batch.json` and
> `a4-shots.json`). All were reviewed as 18 numbered contact sheets; 29 were opened at 1200×900 and **9 are kept**
> (dr-16…dr-24). Internal design reference only (S-227), credited below, never copied into the product or the demo.

- **Feeling:** "this company has my account in order, and nothing on the screen is shouting at me."
- **Idea:** every reply that settles something is a quiet **statement panel**, the way a utility shows a bill:
  - a two-tone sentence headline (the plain lead in a light grey, the fact that matters in dark semibold);
  - label–value rows split by dotted hairlines;
  - one calm action at the panel's foot.
  - Panels are separated by **surface steps, not outlines**: a warm porcelain ground, white panels on it, and pale mist
    wells inside the panels for the facts.
- **Why it fits the homeowner (stressed, phone in hand):**
  - it borrows the look of the screens people already trust with money and service, such as a utility bill, a bank
    loan summary or an insurance claim (dr-16, dr-17, dr-24, dr-19);
  - the two-tone headline gives the answer in one sentence before any detail ("Your visit is booked for
    **Thursday, 8:00 am – 12:00 pm.**");
  - the four trust questions (who is coming, when, what it costs, who calls back by when; profile §6) are label–value
    rows in fixed places;
  - the warm, low-glare ground, larger body text (17 px) and wide spacing make it the calmest of the four to read.
- **Why it fits the staff console (laptop):**
  - the brief becomes a stack of statement panels, promise first, each heading a panel of facts with its source at
    the row end;
  - queue rows read like a bank's loan summary: the reason, then a quiet line with the customer, the reference and
    "Due Mon 7:00 pm, in 2 days" (dr-24);
  - case state is a dated timeline, like a claim's progress (dr-19).
- **Risk:**
  - Soft can slide into low contrast or into "consumer fintech". Text keeps WCAG AA on every surface step; the soft
    parts are the surfaces and shapes, never the text.
  - The console is less dense than A1 or A2. One case still has to fit in about a minute, so rows stay two lines and
    the brief panels stay compact.
  - The warm ground is the nearest of the four to the cream house texture (trait 1, a watch below).

### Component anatomy

| Part | Construction | From |
|---|---|---|
| Canvas | A **warm porcelain ground**: off-white, very low chroma, never cream or beige, never pure white. Content sits on white **statement panels** with 20 px corners, **no outline**, and one wide, very faint shadow. Facts sit in **inset wells** one step darker (pale mist blue-grey, 12 px corners). That gives three surface steps, ground → panel → well, and the console uses the same three | dr-16 (warm off-white ground, white rounded panels, no borders), dr-21 (soft surfaces, nothing outlined), dr-19 (a panel holding an inset field block) |
| Navigation / steps | Two quiet forms. **(1) A progress line** in multi-step tasks: a 4 px track with a soft filled segment and a sentence above it ("Step 2 of 3 · Choose a window"). **(2) A dated timeline** for case state: small soft discs (a check for done, a ring for the current step, hollow for later steps) in an inset well, each label with its date and time under it ("Request created" / "Fri Oct 16, 2:14 pm") | dr-17 (Public Grid set-up: progress bar over the step), dr-19 (claim timeline: "Claim submission" with "12 Nov 2025" under it) |
| Headline | A **two-tone sentence** in Manrope: the lead words in a light weight and mid-grey, the fact in semibold ink ("A representative will get back to you **within 1 business day.**"). The one number that matters (the window or the fee) can be set large and tabular, the way a bill shows the amount due. No hero headline on the chat | dr-18 ("Welcome, Jane. Here's a quick look at your health today."), dr-16 ("$234.34 Outstanding") |
| Conversation | One centred column (about 620 px wide on desktop) on the porcelain ground, with 24 px of air between turn groups. A white top bar reads "Meridian Home Comfort · Automated assistant". The demo date is quiet text on a hairline ("Fri Oct 16 · demo date"), not a pill | dr-16 (greeting and sub-line over panels), dr-22 ("Today" on a hairline) |
| Bubbles / transcript | **No assistant bubbles:** the assistant's turns are plain 17 px text on the ground, with a small caption only at the start of a group ("Meridian assistant · automated · 2:14 pm"). Customer turns are **pale mist blocks** (14 px corners) at the right. A representative's turns sit on white with "Riley · Representative (demo)" and an initial disc. Anything settled appears as a statement panel, never as a chat bubble | dr-22 (name and time caption above each turn, soft tinted blocks), dr-18 |
| Input | A docked white bar: a field on the well tone with 14 px corners (not a pill) and a send button in the primary colour. **"Talk to a person"** is always above the field, as a quiet text button with a headset icon | dr-22 (composer panel with "Send"), dr-19 (a quiet secondary button beside the main one) |
| Slot card | A statement panel headed "Choose a window · **this week**". **Day tiles** (weekday over date, tabular figures, 12 px corners). Then **window tiles** in two columns ("8:00 am – 12:00 pm"). Taken windows **sink into the well tone** with lighter text and the word "Taken"; member-held windows say "Members". The chosen tile fills with the primary colour. Below a dotted rule, a label–value row ("Diagnostic visit · $89"), then **Book this window** | dr-18 (slot grid: open slots white, taken slots sunk grey; date tiles), dr-16 (label–value rows under a dotted rule) |
| Confirmation | A statement panel: two-tone headline, then label–value rows split by dotted hairlines (**Date · Window · Technician · Fee that applies · Address**), values right-aligned, semibold and tabular. Under it, **"What happens next"**: two or three short steps with soft discs. In C2 it lands in the panel's *Your visit* block | dr-20 (Visit summary rows with icons, then "Next steps"), dr-16 ("Next due day / May 5, 2026" rows) |
| Handoff card | A statement panel titled **Your request**. The reference "MHC-C-0007" in Atkinson Hyperlegible Mono sits in a well chip with a copy icon. The promise is the two-tone headline, word for word from the policy table. Rows: **Due** · "Mon Oct 19, 7:00 pm"; **Follow-up** · Email / Phone as two soft choice tiles; **Status** · "Waiting for a representative" with a clock icon. No countdown and no progress bar. In C2 it is pinned in the panel's *Your request* block | dr-19 (claim number chip, "Request status"), dr-21 (bill rows with "Due tomorrow"), dr-24 ("Due in 12 days" as a quiet line) |
| **Safety card** | **The only hard object in a soft system:** full width, square corners, no shadow, no well, no tint. A solid red signal band carries the word **DANGER** and a warning icon. Below it, Meridian's instruction as numbered actions in large ink type on white (the KB's words, split only into numbered lines). No rows, no fee, no booking. It leads the thread and takes over C2's panel, and the rest of the screen dims to the ground tone | deliberately unlike dr-16 / dr-21; REFERENCES R2 |
| Status / priority | Status is a **soft filled tag**: a 6 px-cornered rectangle (not a pill, never outlined) with an icon and a word ("Booked", "Waiting for a representative", "Overdue" with a clock icon and semibold ink). On the console, priority is the same tag with its word ("P1 Emergency"); P0 reads "Safety" in neutral ink. Tag fills are steps of the neutral ramp, not hues | dr-16 ("Searching" tag; "Enabled" with an icon), dr-24 (quiet due lines) |
| Staff queue rows | **Comfortable two-line rows** (about 64 px). Line 1 is the reason in medium weight plus the priority tag. Line 2 is quiet grey: "Ruth Ruiz · MHC-C-0007 · Due Mon 7:00 pm, in 2 days", tabular. The owner disc sits on the right. Rows are separated by space and a hover lift to white, not by lines. P0 and P1 sit in their own panel at the top, titled "Needs attention first" | dr-22 (conversation list: name, time, two-line preview, selected row tinted), dr-24 (due line under each amount), dr-23 ("Things to look into" with one action per row) |
| Brief layout | The centre column is a **stack of statement panels**. The case header is two-tone ("Billing dispute · **due Mon Oct 19, 7:00 pm**"). The promise panel comes first, then the eight headings as panels of label–value rows, each fact with its source link at the row end. Customer claims sit in their own well, labelled "Customer says · not checked". The lifecycle is the dated timeline in a well. Actions sit at the foot: one primary and quiet secondaries | dr-23 ("Good morning, John": sections as quiet white panels with a heading row; "Your servicing team"), dr-19 (inset field pairs), dr-20 |
| Buttons | **12 px corners, never pills**; 48 px tall on the phone, 40 px on the console. One primary per panel, filled in the calm primary. Secondaries are well-tinted with ink text, not outlined. Tertiary actions are underlined text links in a row | dr-17 (one full-width steady primary, a quiet "Setup on my own" secondary), dr-16 ("Billing history · Account details · Report an outage" link row) |
| Iconography | 1.5 px rounded line icons at 20 px, each inside a 32 px soft round well, only on label rows (calendar, clock, pin, receipt, headset) and on status tags | dr-20 (an icon per Visit summary row), dr-21 (bill icons in soft wells) |
| Typography | **Manrope** (OFL) for two-tone headlines and big figures, weights 300 and 600. **Atkinson Hyperlegible Next** (OFL; the Braille Institute's low-vision face) for body and UI, 17 px on the phone and 15 px on the console. **Atkinson Hyperlegible Mono** (OFL) for references and IDs. Checked 2026-10-20 with fontTools: Manrope has `tnum`. Atkinson Hyperlegible Next has `tnum`, but its default digits are proportional, so times, fees and tables need `font-variant-numeric: tabular-nums`. Atkinson Hyperlegible Mono digits are all 632 units, the same width as Next's tabular digits, so a reference beside a time lines up. Urbanist, the face dr-18 resembles, is rejected because it has no `tnum` | — |
| Motion | A settled fact **lands**: its row fades into its panel, and the matching row in C2's panel takes a mist highlight that fades over 600 ms. The progress line fills in 240 ms, ease-out. No slide over 8 px, no bounce. Under `prefers-reduced-motion` nothing moves, and the highlight shows as a static tint | dr-21 |

**Palette intent (temperature: warm-neutral ground, cool accents; values are UX-3's).** A1, A2 and A3 all sit on cool
greys. A4 is the only one on a **warm-neutral** ground:

- **Surface steps:** ground (warm porcelain) → panel (white) → well (pale mist, a faint blue-grey) → selected (a deeper
  mist). Each step is small, a few points of lightness. That keeps glare low: no large pure-white field sits on pure
  white, and nothing is set apart by a dark line.
- **Text greys:** soft near-black ink for content. A secondary grey that passes 4.5:1 on **both** the panel and the well
  (the well is the darker one, so it decides). A tertiary grey only for taken or disabled items, always beside a word.
- **One calm primary:** a muted, slightly greyed **harbour blue**, mid-dark. It is used for the primary button, the
  chosen tile, the current step, links and the focus ring. White text on it passes 4.5:1. There is no second accent
  hue: the references' lime, purple and green are not carried.
- **Warmth:** carried by the ground and the words ("Riley has joined"), not by a hue, so it can't be confused with the
  urgency or danger families.
- **Urgency (no heat, no cooling, active water):** a word and an icon on a neutral tag in semibold ink. A pale ochre
  tint may be tried at UX-3, but only if the safety card still stands alone.
- **Demo banner:** a neutral well-tone strip.
- **Dark theme:** a deep blue-slate ground, panels one step lighter, off-white text (never pure white), and the same
  primary lifted for contrast.

- **Safety stays unmistakable:**
  - it is the only red, the only square-cornered object, the only full-bleed block and the only thing without a soft
    shadow or well, so the soft system makes it *more* distinct in form, not less;
  - it always carries the signal word, an icon and numbered text (S-180);
  - overdue, P0 rows and errors use words, icons and ink weight, never the red family.
- **House-texture check (reject if more than 2):**
  1. Cream canvas with serif heading: **watch.** The warm porcelain ground is the closest of the four to cream. No serif
     is used anywhere, the ground's chroma stays very low and the panels are white, so it should read as daylight
     paper, not beige. Compare it beside a review page on the built screens.
  2. Coloured left-border cards, thin grey outlines, identical 10–12px radii in an even grid: **no.** There are no
     borders or outlines at all; separation is by surface step. Corners are deliberately unequal (20 / 12 / 6 px, and
     square for safety), and panels stack in one column. dr-23's left-border rows are not carried.
  3. Outlined pill badges on everything: **no.** Tags are filled 6 px rectangles with an icon and a word.
  4. Muted sage, teal or forest as the only accent: **no.** The one accent is harbour blue.
  5. One safe sans everywhere, no display face: **no.** Manrope two-tone headlines are the display voice, with
     Atkinson Next for body and Atkinson Mono for IDs.
  6. Flat, no texture, depth or motion: **watch.** No outlines and soft surfaces can read as flat. Depth has to come
     from the surface steps and the one wide shadow, and motion from the "landing" highlight. There is no imagery.
  7. The previous project's skeleton recoloured: **watch**, as for A1–A3. The C2 chat with its panel and the S2
     three-column console come from the concepts, not the direction.

  **Result: 0 matches, 3 watches (1, 6, 7) → passes.**
- **Scanning check:**
  - **Top → bottom on the phone:** top bar and C2's strip (the latest settled fact as one line, "Thu Oct 22 · 8:00 am –
    12:00 pm") → the conversation → the latest statement panel, headline first → its single primary at the panel's foot
    → the input.
  - **Left → right on the desktop chat (C2):** thread → *What's settled* (*Your visit*, *Your request*, *Identity* as
    statement panels). When a panel in the thread settles something, the matching row on the right takes the mist
    highlight.
  - **Left → right on the console (SCR-6):** queue ("Needs attention first", then by due time) → brief panels (promise
    first) → evidence. Each column opens with a panel heading at the same top offset, so the headings share a baseline.
    Clicking a source link highlights that source's panel with the same mist tint.
  - **Motion:** only to show where something landed.
- **Wireframe impact:**
  - **SCR-1:**
    - reply cards become statement panels with two-tone headlines and dotted label–value rows;
    - the slot card becomes the tile grid with sunk "Taken" tiles;
    - the handoff becomes the *Your request* panel with a mono reference chip;
    - the safety card becomes the only square, red, full-bleed block;
    - C2's phone strip shows the latest settled fact as one line and expands into the same panels.
  - **SCR-6:**
    - the centre becomes a stack of statement panels;
    - R5 "Promise shown to the customer" is the first panel;
    - R4 lifecycle stops become the dated timeline in a well;
    - R3 becomes a two-tone header;
    - the queue (R2, and SCR-5) becomes two-line comfortable rows.
  - If A4 is chosen, UX-3 swaps the A2 conventions in `SCREEN_SPECS.md` (mono caps labels such as
    "BILLING DISPUTE · P3 STANDARD") for sentence-case labels. The IA (which regions exist) does not change.

**References:**

- **Renewable Energy (Utility company)** — Eugen Eşanu · https://dribbble.com/shots/27783586-Renewable-Energy-Utility-company · `references/dr-16-energy-update-statement.jpg` (search: "energy utility app")
- **Onboarding for utility management app** — Never Before Seen · https://dribbble.com/shots/26917835-Onboarding-for-utility-management-app · `references/dr-17-public-grid-utility-setup.jpg` (search: "utility mobile app")
- **Mobile design for medical app | Hyperactive** — Hyperactive Design · https://dribbble.com/shots/27240331--Mobile-design-for-medical-app-Hyperactive · `references/dr-18-two-tone-greeting-slots.jpg` (search: "appointment booking soft ui")
- **AI-Powered Insurance - Support Mobile App UI** — Farhan — Design Engineer · https://dribbble.com/shots/26546097-AI-Powered-Insurance-Support-Mobile-App-UI · `references/dr-19-support-claim-timeline.jpg` (search: "insurance app")
- **Empowering Health Care Mobile App** — Design Veli · https://dribbble.com/shots/26677835-Empowering-Health-Care-Mobile-App · `references/dr-20-visit-summary-next-steps.jpg` (search: "field service app light")
- **Payno — Personal Finance & Payment Dashboard UI Design** — Orbix Studio LLC · https://dribbble.com/shots/27586374-Payno-Personal-Finance-Payment-Dashboard-UI-Design · `references/dr-21-payno-bills-mist.jpg` (search: "calm dashboard")
- **Support Inbox Page - Perch** — Potara Studio · https://dribbble.com/shots/27608234-Support-Inbox-Page-Perch · `references/dr-22-perch-support-inbox.jpg` (search: "support inbox light")
- **Newfront Dashboard – Before & After Redesign** — Saasfactor | SaaS Design Agency · https://dribbble.com/shots/26584579-Newfront-Dashboard-Before-After-Redesign · `references/dr-23-newfront-things-to-look-into.jpg` (search: "muted dashboard")
- **Loans Summary** — Unfold · https://dribbble.com/shots/21476886-Loans-Summary · `references/dr-24-regions-loans-summary.jpg` (search: "customer portal soft")

**Do not carry over from these shots:**

- dr-16's neon-lime "Pay bill" button and purple chart bars: one calm primary only, and no second hue;
- dr-18's 24-hour slot times ("14:00") and its black pill button: times are 12-hour, and buttons are never pills;
- dr-19's white text on a pale-blue button: it fails 4.5:1, and soft must never mean low-contrast text;
- dr-23's coloured left-border rows (house-texture trait 2) and its red "//" mark;
- dr-22's red "4" on "Breaching SLA", its purple primary, and green online dots used as the only status signal;
- dr-21's frosted-glass blur: take the tone, not the blur (it costs contrast and phone performance);
- dr-24's bank-green action buttons and promotional card; dr-20's lime gradient checkout button.

### How A4 differs from A1, A2 and A3 at a glance

| Trait | A1 · Work order | A2 · Route sheet | A3 · Dispatcher's log | **A4 · Account statement** |
|---|---|---|---|---|
| Softness | Firm: ink top rules, lifted sheets, grid ground | Hardest: mono caps, perforated stubs, grid paper | Soft: rounded bubbles, soft depth | **Softest:** no outlines, surface steps, one faint wide shadow, low-glare ground |
| Density | High: field grids, step rails | Highest: big times, keyboard-triage rows | Low: a text thread with event lines | **Lowest on the phone** (one panel per reply, 17 px body); comfortable two-line rows on the console |
| Shapes | Squared 4 px sheets, filled square tags | 4 px stubs, perforations, square mono blocks | 16 px bubbles, fully rounded buttons, pill chips | **20 px panels, 12 px wells and buttons, 6 px tags**; the safety block is the only square object |
| Palette temperature | Cool steel grey with ink blue | Cool map paper (optionally a dark ink board) | Cool grey ground, white log | **Warm-neutral porcelain ground**, pale mist wells, one muted harbour blue |
| Type | IBM Plex Sans (condensed cut) + Plex Mono | Barlow / Semi Condensed + JetBrains Mono | Bricolage Grotesque + Public Sans | **Manrope two-tone headlines + Atkinson Hyperlegible Next / Mono** |

---

## A5 · Service desk

> **Added 2026-10-20 (late), proposal, after Innocent's feedback on A1–A4.** He said he doesn't like the colours of the
> directions so far, pointed at one Dribbble shot, *Kirridesk – AI customer service with reply regeneration*
> (dr-25), and asked for "more stuff like this". A5 is that shot's look applied to Meridian. It stays dependable
> dispatch (profile §7): organised, timed, status in words. What changes is the palette and the build: a cool
> blue-grey canvas framing clean white surfaces, hairline cards, one deep emerald for the action, mint for the
> customer's side of the chat and for anything the assistant wrote, charcoal for Send.
> **Method:** his shot opened in the Chrome DevTools MCP, isolated context `aea-callcenter-ux`, 2026-10-20; full-size
> image pulled from its `og:image` (1600×1200). Its other attachments are the studio's testimonial slides, not
> product UI, so they are not kept. Then eight searches by same-origin `fetch` + `DOMParser` ("ai support desk",
> "helpdesk inbox", "ai agent copilot", "customer service dashboard", "ai reply suggestion", "support ticket ai",
> "ai customer support", "kirridesk"), plus Fikri Studio's profile and the shot's "You might also like": 380 unique
> search results (raw list `references/search/a5-batch.json`, profile and related in `a5-profile-related.json`).
> 297 shots were reviewed as 9 numbered contact sheets and 22 were opened at 1200×900. **10 are kept** (his shot,
> four more from the same designer that share the look, five from other designers). Hex values were sampled from
> the images with Pillow. Internal design reference only (S-228), credited below, never copied into the product
> or the demo.
> **Look sheet:** [`../artifacts/2026-10-20-a5-look-sheet.html`](../artifacts/2026-10-20-a5-look-sheet.html)
> (generator `docs/artifacts/_build/a5-look/build_a5_look.py`). Same four mockups and the same copy as the A4 sheet.

### What his shot actually shows (dr-25, observed)

- **Canvas and surfaces, light only.** The app sits as one white window with 24 px corners on a **cool blue-grey
  canvas `#E5E9F0`**. Inside, the content area is **white `#FFFFFF`** and the left navigation rail is a barely-grey
  **`#F5F6F7`**. Pills, the composer header and the "has connected" system line sit on **`#F3F5F7`**. The selected
  nav row reuses the canvas tone `#E5E9F0`. There is no dark mode in the shot or in the designer's series.
- **Accents.** One saturated **emerald `#00BC6F`** for the primary split button ("Submit as Closed"), the active tab
  underline and text, the online dot and the assistant's mark (a green rounded square, `#00B157`; its send icon
  `#009357`). The AI-drafted reply sits in a **mint block `#E2F8EF`** that glows deeper at its top-left corner
  (`#B0EBD0`–`#B4EDD5`), so the machine-written part of the screen is one tinted area. A **charcoal `#202629`** button
  carries the second action ("Accept & Send"). Avatars are **indigo** (`#2A2663` studio disc, `#6A63BB` customer).
  The only red is a notification count (`#FC303D`).
- **Text.** Body and names are near-black (`#000000`–`#101216` at the stroke cores). Captions, labels and section
  headers are a cool grey around **`#7D878E`–`#869096`**, which is only about **3.4–3.7:1 on white**: they fail
  WCAG AA as body text.
- **Type.** A neutral grotesque close to Inter or SF Pro (the family can't be confirmed from pixels): regular body
  at ~15 px, semibold names and headings, no display face, no mono. Hierarchy comes from weight and grey, not size.
- **Shapes and density.** Crisp, not soft: 1 px hairlines, 8 px corners on buttons, inputs and chips, 12 px on the
  composer and popovers, no visible shadow except a faint one under the popover. Customer messages are **not
  bubbles**: a round avatar, a name line ("Santi Cazorla • 11:12 AM • Via WhatsApp"), then the text on white. A
  dotted rule splits the original from its translation. Date and system events are centred quiet lines ("Sunday,
  04 November", "Raihan Fikri has connected to handle the ticket"). Medium-high density: a desktop help desk with a
  nav rail, tabs, a right icon rail.
- **Reply suggestions.** The draft reply is the mint block, headed by the assistant's mark and "Thought for 2s",
  with "Was this helpful?" thumbs at the right. "Regenerate Reply" opens a white popover over it: a header row
  (icon, title, close), a text field holding the agent's instruction, a "Macros" dropdown, a mic and a green send.
  The second attachment shows the same draft with a menu: *Send & Edit* (Edit & Send, Schedule Send), *KiriOne
  Control* (Regenerate Reply, Shorten, Lengthen, Translate to, Adjust Tone), *Utility* (Save as Macro, Copy to
  Clipboard, Discard Draft). The composer header carries "Via WhatsApp", "From Fikri Studio Support" and an
  "Auto Reply" toggle.

The designer's other shots (dr-26…dr-29) show the same system's customer-facing **chat widget** and its
staff-side summary, activity and detail panels; the five other shots (dr-30…dr-34) show the same palette mood or
the same help-desk construction from other designers, including one held at phone width.

- **Feeling:** "a well-run service desk has my case, and I can see exactly where it stands."
- **Idea:** the chat is a **service desk you can see into**:
  - the assistant's turns are quiet grey; the homeowner's turns are mint, so "what I said" and "what they said"
    separate at a glance (dr-26);
  - anything that settles something arrives as a **hairline card** with a tinted header row (icon, title, the
    reference at the right), then label–value rows and one emerald action at its foot (dr-25 popover, dr-28);
  - on the console, everything the assistant wrote (the promise, the brief) sits in **one mint block**, so staff
    always know which words came from the machine (dr-25, dr-29).
- **Why it fits the homeowner (stressed, phone in hand):**
  - it looks like the support chat of a competent modern company: white, clean, one green, nothing decorative;
  - the mint/grey split answers "which of these did I say?" without reading captions;
  - the action is always the one green button in a card, and Send is always the charcoal button in the composer, so
    the two never compete;
  - the safety card is the only red and the only square object, which in this clean system makes it impossible to
    miss.
- **Why it fits the staff console (laptop):**
  - it is a help desk, which is what the console is: queue rail at the left, the case with tabs in the centre,
    evidence at the right (dr-25, dr-33);
  - the mint block marks AI-written text, which is exactly what a representative needs before repeating the
    promise to a customer;
  - the header carries the case reference in mono, the reason in a pill and a green split button whose words come
    from FLOW-9 ("Claim", with release and resolve in its menu).
- **Risk:**
  - **It is the most "SaaS help desk" of the five.** For the console that is right; for the homeowner it can read
    as generic. The texture has to come from the card construction and the mint/grey split, not from the palette
    alone.
  - **Mint means two things:** the homeowner's own turns on the phone (dr-26), and "the assistant wrote this" on the
    console (dr-25). They never share a screen, but UX-3 should confirm it, or move the console's AI block to a
    different tint.
  - The shot's green and greys fail contrast as used. A5 darkens both (see the palette); the result is a deeper
    emerald than the shot's on the light theme.
  - The cool canvas is the same temperature family as A1–A3; the difference has to come from the emerald accent,
    the white-on-tint framing and the hairline construction (see the at-a-glance table).

### Component anatomy

| Part | Construction | From |
|---|---|---|
| Canvas | **Framed:** the product sits as one white surface with 24 px corners on the **cool blue-grey canvas**. On the phone the canvas shows only as the device edge and the demo strip; on the console it frames the whole app. Inside: white content, a barely-grey rail for navigation or the queue, grey pills for meta. Three surface steps, canvas → rail → white | dr-25 (white app on `#E5E9F0`, rail `#F5F6F7`), dr-33 (white three-pane on cool grey), dr-30 |
| Navigation / steps | **Tabs with an emerald underline:** on the phone, the day picker is a tab row ("Mon 19 · Tue 20 · Wed 21 · Thu 22") with a 2 px emerald underline under the chosen day. On the console, "Brief · Conversation" tabs under the case header. Case state over time is a dated activity list (icon, sentence, time), not a stepper | dr-25 (Conversation · Task · Activity Logs · Notes, green underline), dr-30 (activity list with dates) |
| Headline | No hero. The **top bar names the parties**: a back button, the assistant's mark (a mint rounded square with a ticket glyph, never a face) and "Meridian Home Comfort / Automated assistant", plus "Reference MHC-C-0007" in Geist Mono once a case exists. On the console the header reads `MHC-C-0007` in mono, then the reason in a grey pill ("Billing dispute · due Mon Oct 19, 7:00 pm") | dr-25 ("#TC-192" + title pill), dr-26 (chat widget header with the bot mark) |
| Conversation | One column on white. Each turn group opens with a **name line**: "**Meridian assistant** · automated · 2:04 pm" with the small mark, or "**You** · 2:03 pm" at the right. Date and system events are centred quiet lines on hairlines. The demo date sits in a neutral grey strip under the top bar ("Fri Oct 16 · demo date · nobody online") | dr-25 (name · time · via line; centred "Sunday, 04 November"), dr-31 (system events as centred lines) |
| Bubbles / transcript | **Phone:** assistant turns in **grey `#F3F5F7`** blocks, homeowner turns in **mint `#E2F8EF`** at the right, both 12 px with one 4 px corner toward the speaker. A representative's turns carry an indigo initial disc and "Riley · Representative (demo)". **Console:** the transcript is unbubbled, avatar + name line + text, as in the shot | dr-26 (grey bot bubbles, mint customer bubbles), dr-25 (unbubbled staff transcript), dr-34 (the same at phone width) |
| Input | A docked composer: a **"Talk to a person"** option tile (white, hairline, headset icon) always above it, then a grey well with "Type a message" and a **charcoal Send** button at its lower right | dr-26 (option tiles; grey composer with charcoal "Send"), dr-25 ("Accept & Send" in charcoal) |
| Slot card | A hairline card. **Header row** on the rail tone: calendar icon, "Choose a window", "this week" at the right. Then the **day tabs**, then **window tiles** in two columns (8 px, hairline, tabular figures). A taken window sinks to the grey well, its time struck through, with the word "Taken". The chosen tile is **mint with a 2 px emerald edge and a check**. A dashed rule, "Diagnostic visit · $89", then **Continue with this window** in emerald, full width, 8 px | dr-25 (popover header row), dr-26 (selected rating tile: green edge on mint), dr-32 (green primary under summary rows) |
| Confirmation | The same card, headed "Your visit": label–value rows (Date · Window · Technician · Fee that applies · Address) split by dashed hairlines, values right-aligned, semibold and tabular, then "What happens next" as a short checked list | dr-28 (refund details: header with status word, label–value rows, totals), dr-27 (checked step list) |
| Handoff card | A hairline card. Header row: ticket icon, **Your request**, and `MHC-C-0007` in Geist Mono with a copy icon at the right. Then the promise as an 18 px semibold sentence, word for word from the policy table. Rows: **Due** · "Mon Oct 19, 7:00 pm"; **Status** · a grey tag with a clock icon, "Waiting for a representative". The follow-up choice as two option tiles with radios (the chosen one mint with an emerald edge), then **Save my choice**. No countdown, no queue position | dr-28 (reference + status in the header), dr-29 (the "Waiting for…" line), dr-26 (option tiles) |
| **Safety card** | **The only hard object:** full width, square corners, no hairline card, no tint. A solid red band with a warning icon and **DANGER**; Meridian's instruction as numbered lines in 20 px semibold ink on white; the second sentence in body size; a 4 px red rule closes it. It replaces the top of the thread, the rest dims, and one quiet grey line follows: "Once you're outside and safe, you can leave a number here if you'd like." | deliberately unlike dr-25 / dr-26; REFERENCES R2 |
| Status / priority | **Filled grey tags** (6 px corners, never outlined pills) with an icon and a word: "Waiting for a representative", "P3 Standard", "Safety" with a warning icon in ink (not red), "Overdue" with a clock icon, a darker fill and a thin ink edge. Never a coloured dot alone | dr-25 ("Auto Reply" chip), dr-28 ("Completed" word beside the reference) |
| Staff queue rows | On the grey rail: an uppercase section label ("NEEDS ATTENTION FIRST", "BY DUE TIME"), then two-line rows: the reason in semibold with its tag at the right, and a grey line "Omar Patel · `MHC-C-0007` · Due Mon 7:00 pm, in 3 days". The selected row takes the canvas tone, as the shot's selected nav does. The representative's indigo disc and name sit at the rail's top | dr-25 (rail, section labels, selected row), dr-33 (inbox rows with a meta line) |
| Brief layout | Centre column under the tabs. First, the **mint block** "Promise shown to the customer" (assistant mark, the promise in 17 px semibold, then Follow up by / Best time rows): mint because the assistant wrote it. Then hairline sections ("What we know for sure") with label–value rows, and the customer's claims in a grey well labelled "Customer says · not checked". Evidence in a right column with the snapshot rows ("What the AI saw · 2:10 pm" / "Now · 2:20 pm") | dr-25 (mint AI draft), dr-29 (summary block marked not visible to the customer), dr-33 (right-aligned profile facts) |
| Buttons | **8 px corners**, never pills. One emerald primary per card or header (44 px on the phone; the console's is a split button "Claim ▾"). Charcoal only for Send. Secondaries are white with a hairline. Tertiary actions are plain text | dr-25 ("Submit as Closed ▾" split; charcoal "Accept & Send"), dr-32 (green primary beside a hairline secondary) |
| Iconography | 1.8 px rounded line icons at 14–18 px in the ink colour, emerald only inside card header rows and on the assistant's mark. One icon per header row, per tag and per label row | dr-25, dr-27 |
| Typography | **Instrument Sans** (OFL) for the top-bar name, card titles, the promise and the safety lines, semibold, slightly narrowed (`wdth` 96). **Inter** (OFL) for body and UI at 15 px on the phone, 14 px on the console; it is the closest open face to the shot's grotesque. **Geist Mono** (OFL) for references and IDs. Checked 2026-10-20 with fontTools: Inter has `tnum` (tabular digits 1328/2048 em) but proportional default digits, so times, fees and tables set `font-variant-numeric: tabular-nums`; Instrument Sans has `tnum` (600/1000 em); Geist Mono digits are all 600/1000 em, the same width as Instrument Sans's tabular digits. A display face (Instrument Sans) is kept on purpose: Inter alone would be house-texture trait 5 | — |
| Motion | A settled card's header row takes a brief mint wash (400 ms) when it lands; the chosen tile's check draws in 160 ms; the "Riley has joined" system line fades in. No typing indicator, no sliding. Under `prefers-reduced-motion` nothing moves | dr-25 |

**Palette (sampled from the references with Pillow; light primary, dark secondary).** Each value is the shot's own
unless the note says otherwise. The roles map to the profile §7 colour roles.

| Token | Light | Dark | Where it came from | §7 role |
|---|---|---|---|---|
| ground (canvas) | `#E5E9F0` | `#0B0F12` | dr-25 canvas `#E5E9F0` (dr-26 `#DAE1E7`) | Trust / base |
| panel | `#FFFFFF` | `#151A1E` | dr-25 app, dr-26 widget | Trust / base |
| rail | `#F5F6F7` | `#11161A` | dr-25 nav rail | Trust / base |
| well (assistant turns, pills, composer) | `#F3F5F7` | `#20272C` | dr-25 pills `#F3F5F7`, dr-26 bot bubble `#F4F5F7` | Trust / base |
| selected | `#E5E9F0` | `#2A3238` | dr-25 selected nav row | Status (with words) |
| hair | `#E3E7EB` | `#2C343A` | proposal (the shot's rules sit between `#E4E6EE` and `#ECF0F3`) | — |
| mint (homeowner turns; AI-written block) | `#E2F8EF` | `#0F3326` | dr-25 draft `#E2F8EF`, dr-26 customer bubble `#EDFFEF` | Warmth (the homeowner's side) |
| mint-edge (decoration only) | `#B4EDD5` | `#17513C` | dr-25 draft glow `#B0EBD0`–`#B4EDD5` | — |
| ink | `#101216` | `#E9EDF0` | dr-25 text cores | Readability |
| ink2 | `#5B656D` | `#A7B1B9` | **adjusted:** the shot's `#7D878E`–`#869096` captions are ~3.7:1 on white | Readability |
| primary | `#007847` | `#00BC6F` | **adjusted on light:** dr-25 `#00BC6F` carries white text at only 2.49:1, so the light fill is darkened at the same hue (155°); the dark theme uses the shot's own `#00BC6F` with near-black text | Primary action (green, never red or orange) |
| charcoal (Send only) | `#202629` | `#DDE3E8` | dr-25 "Accept & Send" `#202629`, dr-26 Send `#212528` | — |
| person (a representative's disc) | `#2A2663` | `#A9A4F0` | dr-25 studio avatar `#2A2663` | Warmth (a person joined) |
| danger | `#B42318` | `#C8312F` | the same red as A4; the shot's `#FC303D` badge red is **not** carried | Safety / danger, reserved |

- **Urgency** (no heat, no cooling, active water) uses no hue: a word, an icon and semibold ink on a darker grey tag.
- **Status** is always a word with an icon; the emerald appears in a status only beside its word.
- **Contrast (computed by the generator, which fails the build below 4.5:1 for any text pair or 3:1 for a UI
  edge):** light, lowest text pair **ink2 on ground 4.89:1**; ink2 on panel 5.95, ink2 on mint 5.36, on-primary on
  primary 5.56, primary on mint 5.01, on-danger on danger 6.57. Dark, lowest **on-danger on danger 5.34:1**; ink2
  on well 6.94, on-primary on primary 7.59. Every pair passes; the full table is on the look sheet.

**Safety stays unmistakable:**

- it is the only red in the system, the only square-cornered object, the only full-bleed block and the only thing
  outside the hairline-card construction;
- it always carries the signal word, an icon and numbered text (S-180), in Meridian's exact words;
- "Safety" rows on the console, overdue items and errors use words, icons and weight, never the red family.

**House-texture check (reject if more than 2):**

1. Cream canvas with serif heading: **no.** The canvas is a cool blue-grey, and there is no serif anywhere.
2. Coloured left-border cards, thin grey outlines, identical 10–12 px radii in an even grid: **watch.** Cards do have
   1 px hairline outlines, the main thing this direction borrows. Radii are mixed (24 frame / 12 card / 8 tile and
   button / 6 tag / square safety), there are no coloured left borders, and cards stack in a thread, not a grid.
3. Outlined pill status badges on everything: **no.** Tags are filled 6 px rectangles with an icon and a word.
4. Muted sage, teal or forest as the only accent: **watch.** The accent is green, but a saturated emerald (the
   shot's `#00BC6F`, deepened only for contrast), not a muted sage; the mint is a surface tint, not an accent. Check
   on the sheet that the light-theme `#007847` doesn't read as forest.
5. One safe sans everywhere, no display face: **watch.** Inter is the closest face to the shot and is a "safe" sans;
   Instrument Sans is kept as the display voice so the system isn't Inter alone.
6. Flat, no texture, depth or motion: **no.** Depth comes from the framed canvas, the three surface steps and the
   mint glow; motion marks where a card landed.
7. The previous project's skeleton recoloured: **watch**, as for A1–A4: the C2 chat with its panel and the S2
   three-column console come from the concepts, not the direction.

**Result: 0 matches, 4 watches (2, 4, 5, 7) → passes,** but it carries the most watches of the five. Traits 2 and 4
are the price of matching the shot he chose; the sheet is where he judges them.

**Scanning check:**

- **Top → bottom on the phone:** top bar (who, and the reference once a case exists) → demo strip → the thread in time
  order → the latest card, header row first → its one emerald action at the card's foot → "Talk to a person" →
  the composer with Send.
- **Left → right on the desktop chat (C2):** thread → *What's settled* (*Your visit*, *Your request*, *Identity*) as
  the same hairline cards. When a card settles in the thread, the matching card's header row on the right takes the
  mint wash.
- **Left → right on the console (SCR-6):** queue rail ("Needs attention first", then by due time) → the case
  (header with reference, reason and Claim; tabs; the mint promise block first) → evidence. The header row spans
  the case and evidence columns, so their headings share a baseline. Clicking a source in the brief highlights its
  evidence card in mint.
- **Motion:** only to show where something landed.

**Wireframe impact:**

- **SCR-1:** reply cards become hairline cards with tinted header rows; the slot card becomes day tabs and
  mint-selected tiles; the handoff becomes the *Your request* card with a mono reference; turns become grey
  (assistant) and mint (homeowner) blocks with name lines; the safety card stays the only square, red block.
- **SCR-6:** the header gains the mono reference, the reason pill and the "Claim" split button; the brief gains tabs;
  the promise moves into the mint "written by the assistant" block; the queue becomes two-line rows on a grey rail.
- If A5 is chosen, UX-3 swaps the A2 conventions in `SCREEN_SPECS.md` (mono caps labels) for sentence-case labels,
  as for A4. The IA (which regions exist) does not change.

**References** (internal reference only, S-228; images in `references/`):

- **Kirridesk – AI customer service with reply regeneration** *(Innocent's pick)* — Bagus Fikri for Fikri Studio · https://dribbble.com/shots/27624722-Kirridesk-AI-customer-service-with-reply-regeneration · `references/dr-25-kirridesk-ai-customer-service.jpg`
- **KirriDesk – Chat Widget for SaaS Customer Service Management** — Fikri Studio · https://dribbble.com/shots/23066276-KirriDesk-Chat-Widget-for-SaaS-Customer-Service-Management · `references/dr-26-kirridesk-chat-widget.jpg` (designer's profile)
- **Kirridesk – AI Auto Reply Activity in SaaS Customer Service** — Fikri Studio · https://dribbble.com/shots/27469681-Kirridesk-AI-Auto-Reply-Activity-in-SaaS-Customer-Service · `references/dr-27-kirridesk-auto-reply-activity.jpg` (designer's profile)
- **KirriDesk – AI Suggestions in SaaS Customer Service** — Fikri Studio · https://dribbble.com/shots/27451034-KirriDesk-AI-Suggestions-in-SaaS-Customer-Service · `references/dr-28-kirridesk-refund-details.jpg` (designer's profile)
- **KirriDesk – AI Conversation Summary in SaaS Customer Service** — Fikri Studio · https://dribbble.com/shots/27473219-KirriDesk-AI-Conversation-Summary-in-SaaS-Customer-Service · `references/dr-29-kirridesk-conversation-summary.jpg` (designer's profile)
- **AI Customer Support Analytics Dashboard** — achmadkikikarisma · https://dribbble.com/shots/27535301-AI-Customer-Support-Analytics-Dashboard · `references/dr-30-ai-support-analytics-green.jpg` (search: "ai customer support")
- **MyAlice Multichannel Inbox Redesign** — Shah Md. Sakil · https://dribbble.com/shots/20506922-MyAlice-Multichannel-Inbox-Redesign · `references/dr-31-myalice-multichannel-inbox.jpg` (search: "helpdesk inbox")
- **MyAlice Inbox Order Creation** — Shah Md. Sakil · https://dribbble.com/shots/20537424-MyAlice-Inbox-Order-Creation · `references/dr-32-myalice-order-creation.jpg` (search: "helpdesk inbox")
- **AI Agent: Customer Service Dashboard** — Mohammad Saju · https://dribbble.com/shots/26510156-AI-Agent-Customer-Service-Dashboard · `references/dr-33-agento-customer-service-inbox.jpg` ("You might also like" on his shot)
- **Customer Support Dashboard: Inbox & Thread Collaboration** — Keitoto · https://dribbble.com/shots/26778695-Customer-Support-Dashboard-Inbox-Thread-Collaboration · `references/dr-34-keitoto-mobile-inbox-thread.jpg` (search: "customer service dashboard")

**Do not carry over from these shots:**

- **AI confidence and thinking theatre:** dr-25's "Thought for 2s" and dr-27's "Thought for 10 sec" timers and
  step-by-step "Understanding the customer issue" reasoning; we have no calibrated confidence and no reason to show
  thinking time to a homeowner;
- **typing indicators for the assistant:** dr-26's "•••" bubble; the assistant is not a person;
- **fake or unmeasurable waits:** dr-26's running chat timer ("2:02") and "Connecting with agent" spinner, and any
  queue position or wait estimate (the honesty rules above); "Waiting for a representative" stays a status with a
  due time, never a countdown;
- **the shot's text colours as used:** white on `#00BC6F` (2.49:1) and the `#7D878E` grey captions (~3.7:1);
- **dr-25's notification red `#FC303D`** and dr-30's red/green "+12.5% / −4.5%" deltas: red is reserved for safety,
  and status is never colour alone;
- **the "Auto Reply" toggle and "Regenerate Reply / Adjust Tone" controls:** staff don't steer the assistant's wording
  in this product; the promise text comes from the policy table;
- **"Rate AI translation" / "Was this helpful?" thumbs** as shown: the brief's feedback loop is a UX-3 question, not
  a carried pattern;
- dr-30's satisfaction gauge ("Good") and dr-31's orange bot avatar; dr-34's saturated blue bubbles; dr-26's purple
  robot mark (the assistant's mark is a plain mint square, never a face or a robot).

### How A5 differs from A1–A4 at a glance

| Trait | A1 · Work order | A2 · Route sheet | A3 · Dispatcher's log | A4 · Account statement | **A5 · Service desk** |
|---|---|---|---|---|---|
| Softness | Firm: ink top rules, lifted sheets, grid ground | Hardest: mono caps, perforated stubs, grid paper | Soft: rounded bubbles, soft depth | Softest: no outlines, surface steps, one faint wide shadow | **Crisp:** 1 px hairlines, no shadow, a framed white app on a tinted canvas |
| Density | High: field grids, step rails | Highest: big times, keyboard-triage rows | Low: a text thread with event lines | Lowest on the phone (17 px body); comfortable two-line rows | **Medium on the phone (15 px), medium-high on the console** (help-desk rail, tabs, 14 px) |
| Shapes | Squared 4 px sheets, filled square tags | 4 px stubs, perforations, square mono blocks | 16 px bubbles, fully rounded buttons, pill chips | 20 px panels, 12 px wells and buttons, 6 px tags | **24 px frame, 12 px hairline cards with tinted header rows, 8 px tiles and buttons, a split button, tabs with an underline**; safety the only square |
| Palette temperature | Cool steel grey with ink blue | Cool map paper | Cool grey ground, white log | Warm-neutral porcelain, harbour blue | **Cool blue-grey canvas, white, emerald + mint, charcoal**: the only green direction |
| Type | IBM Plex Sans (condensed cut) + Plex Mono | Barlow / Semi Condensed + JetBrains Mono | Bricolage Grotesque + Public Sans | Manrope two-tone + Atkinson Hyperlegible Next / Mono | **Instrument Sans headings + Inter body + Geist Mono** |

**Against A3** it shares only the cool temperature family: it is crisp where A3 is soft, denser, built from hairline
cards and tabs rather than bubbles and pills, and set in different faces. **Against A4** it shares nothing: cool
where A4 is warm, outlined where A4 has no outlines, emerald where A4 is harbour blue, denser, and a different type
pairing. Against A1 it shares the cool temperature and a fairly high console density (two traits); the accent hue,
shapes and type differ. It passes the three-trait rule against every direction.

---

## A6 · Branch office

> **Added 2026-10-20 (late), proposal.** Innocent liked A5 ("thats really good") and dropped A1–A4 (relayed by the
> orchestrating session). He then pointed at a second shot, *Customer Service Workspace* (dr-35), for one more
> direction: "i love the color and theme on this one, feels like the perfect balance between polished and utility
> 'boringness'… the issue will be turning it into a chatbot look." A6 is that shot's look. The staff console (S2)
> follows the shot closely; the homeowner chat (C2) is a translation, set out in *Turning a workspace into a chatbot*
> below. It stays dependable dispatch (profile §7), told the way a bank's service desk tells it.
> **Method:** his shot opened in the Chrome DevTools MCP, isolated context `aea-callcenter-ux`, 2026-10-20; the image
> pulled from its `og:image` at full size (1566×1352; its one attachment is the same screen). The designer's profile
> (`/kendallgoldstein_`, 12 shots) holds one more product screen in the same system (dr-36); the rest are branding and
> print. Then ten searches by same-origin `fetch` + `DOMParser`, aimed at the gap he named, **customer-facing chat**:
> "chat widget", "customer support chat", "chatbot ui", "support chat widget", "banking chat", "help center chat",
> "messenger widget", "live chat widget", "virtual assistant chat", "enterprise dashboard navy". That gave 451
> results, **438 not already reviewed for A5** (raw list `references/search/a6-batch.json`), reviewed as 13 numbered
> contact sheets; 16 were opened at 1200×900 and **7 are kept** (his shot, one more by the same designer, five
> customer-facing chats). Hex values were sampled with Pillow. Internal design reference only (S-231), credited below,
> never copied into the product or the demo.
> **Look sheet:** [`../artifacts/2026-10-20-a6-look-sheet.html`](../artifacts/2026-10-20-a6-look-sheet.html)
> (generator `docs/artifacts/_build/a6-look/build_a6_look.py`). Same four mockups and copy as the A4 and A5 sheets,
> plus a plain chat turn and an A5-vs-A6 strip of the handoff card.

### What his shot actually shows (dr-35, observed)

- **Canvas and surfaces, light only.** A full-width **navy band `#002A54`** carries a letterspaced wordmark
  ("SERVICEHUB"), the product name, the date and time, and an outlined "Log Out" button in white. Below it a
  **pale grey page `#F7F7F7`** holds **white cards `#FFFFFF`** with ~4 px corners and a soft drop shadow, no borders.
  Inner dividers are `#F1F1F1`.
- **The assistant panel.** The left column is a **navy panel `#013A6F`** titled "Support Assistant" in white. Inside
  it sit white cards: a search field, "RECOMMENDED ACTION" (an amber bolt icon `#EEC326`, "Card Replacement Flow", a
  blue "Begin" button), a "Conversation" card and "Helpful Resources" (external-link icons beside underlined blue
  links).
- **Accent.** One **bank blue `#056DAE`** for every action: filled buttons ("Save", "Begin", "Customize View"), links
  ("OFFER", "Support Guide") and the active tab's underline ("Overview"). A secondary button ("Clear") is white with
  a light-blue edge (`#C0DAEB`). There is no other hue except the amber bolt.
- **Text.** Almost all text is one mid grey, **`#666666`** (5.74:1 on white, so it passes AA): names, labels, values
  and card titles. Hierarchy comes from weight and case, not colour: bold labels on the left, regular values on the
  right, values often in caps ("ACTIVE", "CONFIRMED", "ENABLED"). Placeholder text is `#BDBDBD` and a disabled
  "× Email" is `#9F9F9F`; both fail AA.
- **Type.** A geometric sans close to Gotham (the family can't be confirmed from pixels): a letterspaced caps
  wordmark, medium-weight titles, book-weight values, bold labels, a mono-like regularity in numbers.
- **Conversation construction.** Inside the "Conversation" card, the staff side's lines are **grey bubbles
  `#DBDBDB`** at the right with italic text `#565656`; the customer's are **navy bubbles `#002A54`** at the left with
  white italic text. Each has a small time under it ("10:20 AM"). The bubbles have 4–6 px corners, no tails.
- **Data construction.** Cards are collapsible: a blue chevron and a title ("Account Details", "Financial
  Information"), then a **two-column label-value grid** with generous ~45 px rows and no dividers. Status is a word
  ("ACTIVE"), and consent is a list of ticks and crosses with words ("✓ Call ✓ Text × Email").
- **Density.** Medium. A desktop workspace with plenty of air: large rows, wide gutters, nothing tinted except the
  navy. It is deliberately plain: "utility boringness", in his words.

The designer's **Digital Rewards Experience** (dr-36) shows the same system on a customer-facing page (navy nav
strip, blue links, a white confirmation pop-over). The five other kept shots are customer chats in the same mood:
**swiftbank** (dr-37 light, dr-38 dark), a bank's AI assistant whose customer bubble is a deep bank blue (`#026AA1`,
`#0567A4` dark) and whose answers arrive as white cards with titled inner panels and label-value rows; a plain
enterprise **assistant widget** with a navy-blue title band (dr-39); **Walmart's helper** widget, a brand band over
white list rows with chevrons (dr-40); and a **city service-center chatbot** that answers in plain paragraphs with its
source linked inline (dr-41).

- **Feeling:** "I'm talking to my bank's service desk: steady, plain, and nothing is being sold to me."
- **Idea:** a **branch office**: an institutional navy frame, plain grey forms inside it, and one blue for anything
  you can do.
  - The navy band is the institution: it names Meridian and the assistant, and it never changes.
  - Inside, everything is white cards with soft shadows and grey label-value grids, like a statement or an account
    page.
  - One bank blue marks every action and every link; nothing else is coloured, except the red safety card.
- **Why it fits the homeowner (stressed, phone in hand):**
  - it looks like the most trusted customer-service screens people use, a bank's or a utility's: competent and
    unexciting, which is what a stressed person wants from the company that holds the fix;
  - the navy "you" bubble against the grey assistant bubble separates the two speakers by tone, not hue;
  - every action is the same blue, so "what can I tap?" never needs learning.
- **Why it fits the staff console (laptop):**
  - it *is* a customer-service workspace; the console can follow the shot almost one for one: navy band, the queue
    in the navy assistant column, the brief as collapsible cards with label-value grids, tabs with a blue underline,
    one blue "Claim" at the right of the tabs;
  - the grey-on-white grids put facts in fixed places, which is how a representative reads a case in a minute.
- **Risk:**
  - **The chat is the translation.** The shot is a staff workspace; the homeowner sees a chatbot. If the translation
    is literal (cards and grids everywhere), the chat reads as a form. See the next section.
  - **One grey for all text** is calm but flat on a phone in daylight. A6 keeps the shot's greys for labels and body
    and uses the band's navy for the few lines that must be read first (the promise, the safety lines, card choices).
  - **It is close to the generic bank look.** The difference from any bank template has to come from Meridian's
    words, the promise card and the safety card, not the palette.
  - The navy band plus blue buttons put two blues on every screen; the navy must stay a frame, never an action.

### Turning a workspace into a chatbot

His concern is the right one: the shot is a three-column staff tool, and the homeowner gets one narrow chat. The rule
used here: **carry the materials (palette, card, grid, type), translate the layout, and drop the tooling.**

**Carried over as they are**

| Shot part | In the customer chat |
|---|---|
| Navy band `#002A54` with the letterspaced wordmark | The chat's top bar: "MERIDIAN" letterspaced, then "Meridian Home Comfort / Automated assistant", and the reference once a case exists |
| Pale grey page `#F7F7F7`, white cards with a soft shadow | The thread's background and every card in it (slot card, handoff card, confirmation) |
| Bank blue `#056DAE` for every action | Book, Save my choice, Continue, Send, links, the selected day's underline |
| Collapsible card header (blue chevron + title) | Card headers in the thread ("Choose a window", "Your request"), collapsible in the history |
| Two-column label-value grid, bold label / regular value | Due, Status, Fee, Window, Technician rows in cards |
| Status as a word, consent as ✓/× with words | "Waiting for a representative" with a clock icon; "Taken" as a word plus strike-through |
| The grey and navy bubbles, 4 px corners, a time under each | The assistant's turns are grey `#DBDBDB` bubbles with `#565656` text; the homeowner's are navy bubbles with white text |
| "Helpful Resources": external-link icon + underlined blue link | **The source chip:** "Where this comes from", then the link "Customer FAQ · Fees" and the file and version date under it (FLOW-1's chip, R-1) |
| Outlined secondary button ("Clear") | "Talk to a person" as a full-width outlined blue button, always above the composer |

**Translated, and how**

| Shot part | Translation | Why |
|---|---|---|
| The three-column page (assistant panel · account cards · customer info) | One column: band → demo strip → thread → composer. The account cards become **cards inside the thread**, arriving as replies (dr-37: an answer is a white card with a titled inner panel) | A phone has one column; the chat is the timeline |
| Side panels (Customer Information, Financial Information) | C2's **"What's settled"** panel on desktop and the **phone strip**, built as the same collapsible cards with label-value grids (*Your visit*, *Your request*, *Identity*) | The shot's right column is "facts so far"; that is what C2's panel is |
| Bubble sides | Mirrored: the homeowner is the speaker, so **"You" sits at the right** in navy and the assistant at the left in grey | In the shot the staff member is "me"; in the chat the homeowner is |
| Italic bubble text | Upright text | Italic body text is harder to read at phone size |
| Caps values ("ACTIVE") | Sentence case for the homeowner ("Waiting for a representative"); caps stay on the console's short status words ("OVERDUE", "P3 STANDARD") | Caps sentences slow a stressed reader; caps single words scan well for staff |
| One grey for all text | Grey for body and labels as in the shot; **navy `#002A54` for the lines read first** (the promise, the safety lines, the chosen option) | Keeps the shot's calm and gives the phone one strong level |
| Checkbox ("Secondary account holder") | Window rows with a square check box; the chosen row fills with the pale blue tint and a blue edge | A familiar control from the same system; a radio-like single choice |
| Pale field and button edges (`#C0DAEB`, ~`#DBDBDB`) | `#8C8C8C` field edges and blue-edged secondary buttons | The shot's edges fail 3:1 |

**Not carried over (agent-only)**

- **Agent density and tooling:** the session timer ("Session Time 08:36"), "Add a note…" with Save/Clear,
  "Customize View", the right icon rail, the search box in the assistant panel. A homeowner has no use for any of it.
- **"RECOMMENDED ACTION" with "Begin"** and its amber bolt: next-best-action is staff tooling, and the amber sits too
  close to the orange family the primary may never use.
- **Internal labels and fields:** "Multi Relationship", "NPSL Product", "Email Suppression", "Large Purch
  Notification", masked account numbers. The homeowner sees only Meridian's plain words.
- **Upsell slots** ("Available Offers · OFFER OFFER OFFER"): nothing is sold in a support chat.
- **"Log Out" in the band:** the chat has no account session to end; the band names the parties instead.
- **The date and clock in the band:** the demo date lives in the neutral demo strip under the band ("Fri Oct 16 ·
  demo date · nobody online"), and no clock ticks anywhere.

### Component anatomy

| Part | Construction | From |
|---|---|---|
| Canvas | A **navy band** on top, then the **pale grey page**; content in **white cards with ~4 px corners and a soft shadow**, no outlines. On the phone the device edge is navy too, so the band reads as the frame. The console is the shot's layout: band, then a navy column at the left and cards on grey | dr-35 (band `#002A54`, page `#F7F7F7`, white cards), dr-36 |
| Navigation / steps | **Text tabs with a 3 px blue underline**: the day picker on the phone ("Mon 19 · Tue 20 · Wed 21 · Thu 22"), "Brief · Conversation" on the console. Case state on the console as the shot's activity-style rows; no stepper | dr-35 ("Overview · Activity · Interactions · Account") |
| Headline | No hero. The **band names the parties**: "MERIDIAN" letterspaced (Montserrat 700, 0.28em), a hairline divider, "Meridian Home Comfort / Automated assistant" and the reference in DM Mono once a case exists. On the console: "MERIDIAN · Home Comfort · Service desk", the demo date and "Riley · Representative (demo)" at the right | dr-35 ("SERVICEHUB Customer Support"), dr-39 (title band with a status line) |
| Conversation | One column on the grey page; turns in time order, a small grey time line under each ("Meridian assistant · automated · 2:04 pm", "You · 2:03 pm"). System events as quiet centred lines. The demo strip is a white bar under the band | dr-35 (time under each bubble), dr-41 (plain paragraphs) |
| Bubbles / transcript | **Assistant:** grey `#DBDBDB` bubble, 4 px corners, no tail, text `#565656`, left. **Homeowner:** navy `#002A54` bubble, white text, right (dark theme `#0567A4`). **Representative:** a white card-bubble with "Riley · Representative (demo)" on top. The assistant never gets a face | dr-35 (grey and navy bubbles), dr-37 (blue customer bubble), dr-39 (flat grey assistant bubble) |
| Input | Docked on white: **"Talk to a person"** as a full-width outlined blue button with a headset icon, then a field with a `#8C8C8C` edge, 4 px corners, an italic placeholder ("Type a message") and a square blue send button | dr-35 ("Clear" outlined button; "Add a note…" field), dr-37 |
| Answer with source | The answer in a grey bubble with the key figure in bold ("**$89**"); under it, inside the bubble, a white **source box**: "WHERE THIS COMES FROM" in small caps, an underlined blue link with an external-link icon ("Customer FAQ · Fees"), and "faq/customer_faq.md · updated Mar 2, 2026". It expands to the quoted passage (SCREEN_SPECS SCR-1) | dr-35 ("Helpful Resources" links), dr-41 (source linked inline) |
| Slot card | A white card: chevron header "Choose a window" with "this week" at the right; the day tabs; **window rows** (full width, 4 px, `#8C8C8C` edge, a square check box at the left, tabular times); a taken row sinks to `#F1F1F1`, struck through, with "TAKEN" in small caps at the right; the chosen row fills with `#E4EEF8`, a 2 px blue edge and a filled blue box with a tick. Then a grid row "Diagnostic visit · $89" and **Continue with this window** in blue | dr-35 (card header, checkbox, grid), dr-40 (white list rows) |
| Confirmation | A white card headed "Your visit": the label-value grid (Date · Window · Technician · Fee that applies · Address), then "What happens next" as ✓ rows with words | dr-35 (grids; ✓ Call ✓ Text), dr-38 (label-value rows with icons inside a reply card) |
| Handoff card | A white card: chevron header "Your request" with the reference in DM Mono at the right; the promise in **navy semibold** (word for word from the policy table); the grid "Due · Mon Oct 19, 7:00 pm" / "Status · ◷ Waiting for a representative"; the follow-up choice as two option boxes with radios (the chosen one tinted with a blue edge); **Save my choice**. No countdown, no queue position | dr-35 (card + grid), dr-37 (titled inner panel in a reply) |
| **Safety card** | **The only hard object, and the only colour besides the blue:** full width, square corners, no shadow, a solid red band with a warning icon and **DANGER** letterspaced, Meridian's instruction as numbered lines in navy Montserrat 19 px bold, the second sentence in body size, a 4 px red rule closing it. The thread dims under it; one quiet line follows | deliberately unlike dr-35; REFERENCES R2 |
| Status / priority | **A word in small caps with an icon**, no chip, no fill: "◷ OVERDUE", "⚠ SAFETY" (in grey, never red), "P3 STANDARD" on the console; sentence case with an icon for the homeowner. Ticks and crosses always carry their word | dr-35 ("ACTIVE", "✓ Call", "× Email") |
| Staff queue rows | Inside the **navy assistant column**, white cards titled "NEEDS ATTENTION FIRST" and "BY DUE TIME" (small caps, grey); rows with the reason in navy semibold, the status word at the right and a grey meta line ("Omar Patel · `MHC-C-0007` · Due Mon 7:00 pm, in 3 days"); the selected row is tinted `#E4EEF8` | dr-35 (navy "Support Assistant" column with white cards inside) |
| Brief layout | Cards on the grey page, two columns as in the shot: **"Promise shown to the customer"** first, with a small navy tag "Written by the assistant"; then "What we know for sure" as a grid, with the customer's claims in a grey well "Customer says · not checked"; evidence in the right column. Tabs "Brief · Conversation" with the blue **Claim** button at the right, where the shot has "Customize View" | dr-35 (Account Details / Financial Information cards; tab row with a button at the right) |
| Buttons | **4 px corners**, never pills. Primary: filled `#056DAE`, white Montserrat 700. Secondary: white with a 1.5 px blue edge and blue text. Send: a square blue icon button. One primary per card | dr-35 ("Save", "Begin", "Clear", "Customize View") |
| Iconography | 1.8 px line icons at 15–18 px: a blue chevron on card headers, external-link icons on sources, clock and warning icons on status words, a headset on "Talk to a person" | dr-35 |
| Typography | **Montserrat** (OFL) for the wordmark, card titles, the promise, buttons and the safety lines; it is the closest open geometric face to the shot's Gotham-like sans. **Figtree** (OFL) for body and UI at 15 px on the phone, 14 px on the console. **DM Mono** (OFL) for references and IDs. Checked 2026-10-20 with fontTools: Montserrat has `tnum` (tabular digits 700/1000 em) and Figtree has `tnum` (620/1000 em), both with proportional default digits, so times, fees and grids set `font-variant-numeric: tabular-nums`; DM Mono digits are all 600/1000 em | — |
| Motion | A settled card's header row gets a brief pale-blue wash when it lands; a collapsed card opens in 160 ms. No typing indicator for the assistant; the "replying" line is text (SCREEN_SPECS). Under `prefers-reduced-motion` nothing moves | — |

**Palette (sampled from the references with Pillow; light primary, dark secondary).**

| Token | Light | Dark | Where it came from | §7 role |
|---|---|---|---|---|
| ground (page) | `#F7F7F7` | `#02060F` | dr-35 page; dark from dr-38 background `#02060F` | Trust / base |
| panel (cards) | `#FFFFFF` | `#0F172A` | dr-35 cards; dr-38 reply card `#0F172A` | Trust / base |
| well (dividers, taken rows, claims) | `#F1F1F1` | `#172238` | dr-35 inner divider | Trust / base |
| bubble (assistant turns) | `#DBDBDB` | `#22304A` | dr-35 staff bubble | Trust / base |
| selected | `#E4EEF8` | `#13304D` | dr-40 list row tint `#E4EEF8` (the shot has no selected state) | Status (with words) |
| edge (field and control edges) | `#8C8C8C` | `#6B7A90` | **adjusted:** the shot's `#C0DAEB` button edge is 1.45:1 and its pale field borders also fail 3:1 | — |
| navy (band; the homeowner's bubble) | `#002A54` | `#0B1E38` (band); bubble `#0567A4` | dr-35 band and customer bubble; dark bubble from dr-38 | Trust / base; Warmth is carried by the words |
| navy2 (console queue column) | `#013A6F` | `#0E2747` | dr-35 "Support Assistant" panel | — |
| navy-sub (secondary text on navy) | `#C0DAEB` | `#A9C6E0` | dr-35 light blue, used as text on navy (9.9:1), never as an edge | Readability |
| strong (lines read first) | `#002A54` | `#F2F6FA` | dr-35 navy, used as text | Readability |
| ink (body) | `#565656` | `#D5DCE6` | dr-35 bubble text | Readability |
| ink2 (labels, meta) | `#666666` | `#AAB4C3` | dr-35, nearly all its text | Readability |
| primary | `#056DAE` | `#5AA9E6` | dr-35 buttons, links, tab underline (white on it 5.52:1, unchanged); dark lifted for contrast | Primary action (blue, never red or orange) |
| danger | `#B42318` | `#C8312F` | the same red as A4/A5; the shot has none | Safety / danger, reserved |

- **Warmth** (greetings, "Riley has joined") is carried by the words and the representative's named card-bubble, not
  by a hue; the shot's amber bolt `#EEC326` is not carried (too close to the orange family).
- **Urgency** (no heat, no cooling, active water) uses a word in small caps and an icon, no hue.
- **Contrast (computed by the generator, which fails the build below 4.5:1 for any text pair or 3:1 for a control
  edge):** light, lowest text pair **primary on selected 4.70:1** (ink2 on selected 4.89, ink on bubble 5.30, ink2 on
  well 5.08, on-primary on primary 5.52, white on the navy bubble 14.39); control edge `#8C8C8C` on white 3.36. Dark,
  lowest **primary on selected 5.30:1**, on-danger on danger 5.34, white on the `#0567A4` bubble 6.03. Every pair
  passes. The shot's own text needed no change; only its control edges did.

**Safety stays unmistakable:**

- it is the only red, the only full-bleed square block and the only thing besides the blue that carries colour, in a
  system that is otherwise navy, grey and white;
- it always carries the signal word, an icon and numbered text (S-180), in Meridian's exact words;
- the console's "SAFETY" status is a grey word with a warning icon, never red.

**House-texture check (reject if more than 2):**

1. Cream canvas with serif heading: **no.** Pale neutral grey, navy band, no serif.
2. Coloured left-border cards, thin grey outlines, identical 10–12 px radii in an even grid: **watch.** Cards are
   borderless with a shadow and 4 px corners, but the console's cards do sit in an even two-column grid, as in the shot.
3. Outlined pill status badges on everything: **no.** Status is a bare word with an icon.
4. Muted sage, teal or forest as the only accent: **no.** Navy and bank blue.
5. One safe sans everywhere, no display face: **watch.** Montserrat carries the wordmark, titles and buttons as the
   display voice, but it is a familiar "safe" geometric; the letterspaced caps wordmark is what keeps it from reading
   as a default.
6. Flat, no texture, depth or motion: **no.** Depth comes from the navy frame and the card shadows.
7. The previous project's skeleton recoloured: **watch**, as for every direction: C2 and S2 come from the concepts.

**Result: 0 matches, 3 watches (2, 5, 7) → passes.**

**Scanning check:**

- **Top → bottom on the phone:** navy band (who; the reference once a case exists) → demo strip → the thread → the
  latest card, chevron header first → its one blue action → "Talk to a person" → the composer.
- **Left → right on the desktop chat (C2):** thread → "What's settled" as the same collapsible cards; when a card in
  the thread settles something, the matching card's header gets the pale-blue wash.
- **Left → right on the console (SCR-6):** navy queue column → the case (tabs with Claim, the promise card first) →
  evidence. Card headers in both columns sit on the same baseline under the tab row.
- **Motion:** only to show where something landed.

**Wireframe impact:**

- **SCR-1:** the top bar becomes the navy band; turns become grey (assistant) and navy (you) bubbles with a time line
  under each; reply cards become white shadowed cards with chevron headers and label-value grids; source chips
  become the "Where this comes from" box; the slot card becomes day tabs and checkbox rows.
- **SCR-6:** the shot's layout almost as is: band, navy queue column, tabs with Claim at the right, collapsible
  brief cards in two columns.
- If A6 is chosen, UX-3 swaps the A2 conventions in `SCREEN_SPECS.md` (mono caps labels) for sentence case on
  customer screens and small-caps status words on the console. The IA does not change.

**References** (internal reference only, S-231; images in `references/`):

- **Customer Service Workspace** *(Innocent's pick)* — Kendall McMillan · https://dribbble.com/shots/27664920-Customer-Service-Workspace · `references/dr-35-servicehub-customer-service-workspace.jpg`
- **Digital Rewards Experience** — Kendall McMillan · https://dribbble.com/shots/27105816-Digital-Rewards-Experience · `references/dr-36-mcmillan-digital-rewards.jpg` (designer's profile)
- **swiftbank: AI Digital Banking Assistant – Freeze Digital Card UI** — finterface · https://dribbble.com/shots/25111067-swiftbank-AI-Digital-Banking-Assistant-Freeze-Digital-Card-UI · `references/dr-37-swiftbank-freeze-card-chat.jpg` (search: "banking chat")
- **swiftbank: AI Digital Banking Chatbot – Request Money UI** — finterface · https://dribbble.com/shots/25111058-swiftbank-AI-Digital-Banking-Chatbot-Request-Money-UI · `references/dr-38-swiftbank-request-payment-dark.jpg` (search: "banking chat")
- **AI Agent Chat Animation** — W1sdom Prod. · https://dribbble.com/shots/25848974-AI-Agent-Chat-Animation · `references/dr-39-tavares-assistant-widget.jpg` (search: "virtual assistant chat")
- **Chat Widget** — Fuzeberg · https://dribbble.com/shots/25787185-Chat-Widget · `references/dr-40-walmart-helper-widget.jpg` (search: "chat widget")
- **AI Chatbot for a City Service Center** — W1sdom Prod. · https://dribbble.com/shots/25849368-AI-Chatbot-for-a-City-Service-Center · `references/dr-41-city-service-center-chatbot.jpg` (search: "virtual assistant chat")

**Do not carry over from these shots:**

- the agent tooling and internal labels listed under *Not carried over* above (session timer, notes, Customize View,
  Recommended Action, offers, internal field names, Log Out);
- the amber bolt `#EEC326`; the light-blue control edges `#C0DAEB`; the `#BDBDBD` placeholder and `#9F9F9F` disabled
  text (both fail AA);
- italic bubble text and caps sentences on customer screens;
- swiftbank's emoji in replies, its "read" double ticks, its voice-note bubble and its credit-score gauge (dr-37,
  dr-38); Walmart's promotional tile (dr-40);
- typing indicators for the assistant, confidence figures, and any wait time or queue position (the honesty rules
  at the top of this file).

### How A6 differs from A5 at a glance

A5 and A6 are the two directions still in play; the look sheet shows the same handoff card in both, side by side.

| Trait | **A5 · Service desk** | **A6 · Branch office** |
|---|---|---|
| Softness | Crisp: 1 px hairline cards, no shadow | Soft-institutional: borderless cards with a soft drop shadow |
| Density | Medium on the phone, medium-high on the console | Medium everywhere: generous 40–45 px grid rows, wide gutters |
| Shapes | 24 px frame, 12 px cards with tinted header rows, 8 px tiles and buttons | 4 px everything, a full-width navy band, collapsible cards with chevrons, checkbox rows |
| Palette temperature | Cool blue-grey canvas, white, **emerald + mint**, charcoal Send | Neutral pale grey, white, **navy frame + bank blue**, grey text |
| Type | Instrument Sans + Inter + Geist Mono | Montserrat + Figtree + DM Mono |

They share no trait: A5 reads as a modern SaaS help desk, A6 as a bank's or utility's service desk. Against the
dropped A1 (cool steel grey with ink blue) A6 shares the blue family and the density but not the shapes, softness or
type.

---

## Review notes from the built screens (2026-10-20, proposal)

Seen on the clickable prototypes and wireframes (`docs/ux/02-concepts/wireframes/`), not in the Dribbble research:
- **A1:** identical 4 px sheet stacks in the panel and queue (trait 2 watch); a subtle condensed cut (trait 5 watch).
- **A2:** headline times are 24-hour ("MON OCT 19 · 19:00", "14:14"). US homeowners read 12-hour times, so if A2 is
  chosen, UX-3 switches it to "7:00 pm" and keeps the size and weight.
- **Both:** the C2 chat + panel and the S2 three-column console share one shell (trait 7 watch for both). That comes
  from the concepts, not the direction.

## Questions this file leaves for the UX-2 gate and UX-3

> **Answered 2026-10-21:** the direction is **A5 Service desk** (light first) on C2 and S2. Question 1 below is closed; the contact-offer question was resolved in FLOW-2; colour values are now in `docs/design/design.md` (UX-3).

1. **Direction:** A1, A2 or A3, or A1 for the customer chat with A2's queue rows for the console. A mixed choice would
   need its own house-texture check.
2. **Contact offer after a safety card (resolved 2026-10-20, FLOW-2):** no "I'm outside" tap. The card keeps
   Meridian's words exactly and invites no typing; the optional offer is one quiet line for "once you're outside and
   safe". All three directions follow this; see [`../ux/02-concepts/REFERENCES.md`](../ux/02-concepts/REFERENCES.md) R2-2.
3. **Colour values** for each role, in both themes, are UX-3 (`design.md`). The one constraint already fixed here is that
   none of the three directions uses the red family outside the safety card.
