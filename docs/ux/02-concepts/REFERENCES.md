# UX-2 · Reference research: Meridian AI service agent

> **Status:** DRAFT · Date: 2026-10-20 · Internal design reference only. Never in the product, the demo or published
> material.
> **Method:** light mode (phases.md): one product per core flow, four in total. They were driven in the Chrome DevTools MCP
> in an isolated browser context (`aea-callcenter-ux`):
> - **customer flows at 390 px** (phone, touch emulation);
> - **staff-console references at 1280 px.**
>
> **Observe only:** no form submitted, no message sent, nothing booked, no text typed anywhere, no personal data entered.
> The only clicks were navigation and dismissing cookie or notice banners in the isolated context.
> **Tags:** **[O]** observed live on 2026-10-20 · **[D]** vendor-documented · **[P]** our proposal.
> **Sources:** S-181…S-185 in [`../../source/source-register.md`](../../source/source-register.md). Texture research
> (Dribbble) is separate: [`../../design/DESIGN-DIRECTIONS.md`](../../design/DESIGN-DIRECTIONS.md).

## What was examined, and how

| Product | Why chosen (which job it solves) | Driven live at | Date |
|---|---|---|---|
| **R1 · Strand Brothers Service Experts (Austin)**: home page and its "Schedule the Experts" widget, a ServiceTitan Scheduling Pro iframe (S-181), plus **Housecall Pro's booking documentation** (S-182) for the slot mechanics the widget never showed | Booking a home-services visit on a real Austin HVAC and plumbing company's site: FLOW-5 | 390 px. Opened the widget twice and stopped at its first screen each time. The scheduler URL opened on its own renders blank (it needs its host page), so slot behaviour comes from Housecall Pro's docs [D] | 2026-10-20 |
| **R2 · Texas Gas Service** (Austin's gas utility): the *Report Emergency* modal and the *When You Smell Gas* page (S-183) | The safety instruction a homeowner meets first, from the authority Meridian's own policy points to ("call 911 or their gas utility from outside"): FLOW-2 | 390 px. Read only | 2026-10-20 |
| **R3 · Intercom Messenger with Fin**, on Intercom's own help site, plus the *Set your reply time* help article (S-184) | An AI support chat with a human team behind it: how it says it is an AI, how a person is reached, what wait it promises: FLOW-1, FLOW-7, FLOW-8 | 390 px. Opened the messenger, read the greeting and the home screen; **typed and sent nothing** | 2026-10-20 |
| **R4 · Zendesk Agent Workspace**: the customer context panel and the SLA column, from Zendesk's documentation images (S-185) | A help-desk agent's case view and queue: FLOW-9, FLOW-10, SCR-5, SCR-6 | Not driven live (needs an agent login): documentation pages opened at 1280 px and their images composed at 1280 px. All findings tagged [D] | 2026-10-20 |

## Captured images (`references/`)

| File | Shows | Why kept |
|---|---|---|
| `bh-01-serviceexperts-austin-home-390.png` | The Austin home page at phone width: offer bar ("$0 Diagnostic with paid repair"), logo, call icon, menu | The real starting point of a booking on a phone |
| `bh-02-serviceexperts-schedule-contact-first-390.png` | First click on "Schedule the Experts": a "Send us an email" form asking for first name, last name, phone, text consent, service and email before anything else; a red **Next** | Contact details before any time is shown (finding R1-1) |
| `bh-03-serviceexperts-help-hub-ai-chat-390.png` | Second visit, same button: "How can we help?" with three red tiles (Text with Us, Call Me, Email Us) and "Chat with Strand Brothers Service Experts **AI**" | Channel hub and AI disclosure by badge (R1-2, R1-3) |
| `bh-04-texasgasservice-report-emergency-390.png` | The *Report Emergency* modal: "To report a natural gas odor or emergency, leave the area immediately and then call 911 and 800‑959‑5325", numbers as links, an orange **Ok**; above it, an orange ⚠ banner about a billing PO box | Action-first wording; alarm styling spent on a routine notice (R2-1, R2-3) |
| `bh-05-texasgasservice-if-you-smell-gas-390.png` | *When You Smell Gas*: the same sentence as a large heading, then the "DON'T" list including "DON'T use your phone, tablet, computer or other mobile devices" | The rule that shapes our safety card on a phone (R2-2) |
| `bh-06-intercom-fin-messenger-disclosure-390.png` | Fin's greeting "You are now speaking with Fin", the meta line "Fin · AI Agent · Just now", header "The team can also help", composer "Ask a question…" | Disclosure in words and per message; no person button (R3-1, R3-2) |
| `bh-07-zendesk-sla-countdown-view-1280.png` | Zendesk's documentation image of the admin step that adds the **SLA** column to a view (not the badge itself) | Evidence that time-to-breach is a standard queue column (R4-2); the badge behaviour is from the docs text |
| `bh-08-zendesk-customer-context-1280.png` | Composed from Zendesk's documentation images: requester essentials card (label/value rows), the Interactions list with letter-in-colour status squares (P, S, O), and the hover preview of a ticket | Model and warning for SCR-6's identity and other-cases regions (R4-1) |

## Analysis

### R1 · Strand Brothers Service Experts (ServiceTitan widget) + Housecall Pro docs

- **What a visitor experiences.**
  - [O] "Schedule the Experts" appears **six times** in the Austin home page's accessibility tree, plus a call icon in the
    header and a "Call" option in the floating help widget.
  - [O] On the first click, the widget opened straight onto **"Send us an email · Please enter your name and contact
    info"**: first name, last name, phone, "Can we text you?", service and email are all required, with a consent
    paragraph and **Next** (bh-02).
  - [O] After a reload, the same button opened **"How can we help?"**: three large tiles (Text with Us, Call Me, Email
    Us) and a chat box headed "Chat with Strand Brothers Service Experts **AI**" (bh-03).
  - [O] No date, time or arrival window was offered on either path before personal details.
  - [O] The page carries the Texas licence number in the footer ("License #TACLB29616C") and "Open 24 Hours", and an offer
    with its condition in the same block ("$0 Diagnostic with paid repair … applies only when recommended repair is
    completed and paid at time of service").
  - [D] Housecall Pro's booking can offer any open slot in **30-minute increments**, or a fixed start time. An **arrival
    window** is "a range of time in which to expect your arrival". A *Manual* mode **hides time selection** and creates
    unscheduled jobs (S-182).
- **How it is built.**
  - [O] The widget is a cross-origin iframe from `scheduler.servicetitan.com`. Opened on its own it renders a blank page,
    so its later steps could not be observed without entering personal data.
  - [O] Every action in the widget uses the brand red.
- **Why it works (for them).** [P] Capturing contact first guarantees a lead even if the customer drops out. Offering
  text, call and chat side by side lets the customer pick the channel they trust.
- **What does not fit us.**
  - [P] **Identity before value.** We show the windows Meridian can offer, and the fee that applies, before asking who the
    customer is wherever the PRD allows it (zone from the address, member-reserved windows labelled). The one-time code
    is asked only when a private record is needed (FLOW-3). A lead form would also contradict "never repeat my story"
    (US-14).
  - [O→P] **Red on every action.** Our colour roles reserve red for safety and forbid red or orange primary actions
    (profile §7).
  - [P] **"AI" as a badge only.** We say it in words in the greeting and on every assistant turn (US-1). A small "AI"
    mark is easy to miss.
  - [P] **Licence number.** The cue is real (S-175), but Meridian's data has no licence number. We do **not** invent one.
    Noted as an open item for the company profile, not shown.
  - [D→P] **Start times in 30-minute steps.** Meridian books **arrival windows** by zone (8–12, 12–4 and 1–5, all 4 hours, plus a 3-hour 4–7 pm window on Tue/Thu) (`SCHEMA.md`), so we show windows
    and call them arrival windows, never start times.

### R2 · Texas Gas Service

- **What a visitor experiences.**
  - [O] *Report Emergency* is a modal with one sentence: "To report a natural gas odor or emergency, **leave the area
    immediately and then call 911 and 800‑959‑5325**." Both numbers are tappable links. A single **Ok** closes it (bh-04).
  - [O] *When You Smell Gas* repeats that sentence as the page's largest heading, then lists "DON'T" rules. One of them is
    "**DON'T use your phone, tablet, computer or other mobile devices**", along with light switches, doorbells, matches,
    windows and garage doors, and starting a vehicle (bh-05).
  - [O] At 390 px, "Report Emergency" sits **inside the menu**. The top of every page is an orange banner with a ⚠ icon
    about a **billing PO box** (bh-04, bh-05).
- **How it is built.** [O] The modal opens from a URL parameter (`?action=report-emergency`) and the menu link. No signal
  word ("DANGER") appears.
- **Why it works.** [P] Action first, reason later: the first words are the thing to do. The numbers are a tap away.
- **What does not fit us.**
  - [O→P] **The phone is part of the danger.** Our customer is typing on a phone, possibly indoors. Meridian's own policy
    says to call "**from outside**" (`policies/escalation_and_safety.md`).
    - So our safety card must make **leaving the first action** and must not invite more typing indoors.
    - **Resolved 2026-10-20 in FLOW-2:** the card is Meridian's instruction word for word, with no field, question or
      prompt; the optional contact offer is one quiet line addressed to "once you're outside and safe" (R2-2 below).
      No "I'm outside" tap: a tap is still phone use indoors, and it would add a step Meridian's policy doesn't have.
    - A tap-to-call button is labelled "Call 911 (from outside)".
  - [O→P] **Hidden emergency path.** We never put the safety instruction, the emergency number or "Talk to a person"
    behind a menu at phone width (US-2, US-3).
  - [O→P] **Alarm styling spent on routine news.** The same orange ⚠ banner announces a mailing address. Our safety styling
    appears **only** for safety. The demo bar, the simulated-staffing banner and limit notices use neutral styling.
  - [O→P] **Dismissible with "Ok".** Our safety card is pinned and not dismissible, and it carries a signal word and an
    icon as well as colour (ANSI Z535 via S-180).

### R3 · Intercom Messenger with Fin

- **What a visitor experiences.**
  - [O] The messenger opens on Fin: "Hi there 👋 You are now speaking with Fin. How can I help?", under it the meta line
    "**Fin · AI Agent · Just now**". The header reads "Fin · **The team can also help**" (bh-06).
  - [O] There is **no visible control to reach a person**. The composer offers attach, emoji, GIF and voice only. The home
    tab shows "No messages · Messages from the team will be shown here" and **no reply time** in this workspace.
  - [D] Reply time can be set as **fixed** ("In a few minutes / hours / a day"), a custom number of hours, or **dynamic**:
    "your team's median first reply time over the past 7 days". Teams with balanced assignment can **show queue position**
    instead. Outside office hours, customers "will be shown office hours". After transfer to a person, customers see
    "**Waiting for a teammate**" (S-184).
- **How it is built.** [D] Reply-time text is configuration, by workspace or team, and partly derived from measured
  replies. Fin's own expectation-setting can override the notice.
- **Why it works.** [P]
  - Labelling every assistant message, not only the greeting, keeps disclosure true deep into a conversation.
  - "The team can also help" tells the customer a person exists without promising one now.
- **What does not fit us.**
  - [O→P] **No person button.** Reaching a person only by asking in words is the pattern our research says customers fear
    (consolidated direction P8). US-2 requires a visible "Talk to a person" that works the first time.
  - [D→P] **Dynamic reply time.** A 7-day median assumes real staff and real history. We have neither (the default is
    unstaffed), so **our promise comes only from the policy table**, with a due date: "within 1 business day, by Mon Oct
    19, 7:00 pm" (FLOW-7).
  - [D→P] **Queue position.** It is rejected: we can't measure it, and it is a wait estimate in disguise (consolidated
    direction, Live-queued: "a wait estimate only if measured").
  - [D→P] **"Waiting for a teammate".** It is adapted only for the simulated staffed state, worded "A representative will
    join this chat when available", with no time (US-15).
  - [P] The same mistake appears on Dribbble ("3 Agents online · Our team typically replies in minutes"). Presence and
    speed claims are not shown unless true and measured.

### R4 · Zendesk Agent Workspace (documentation)

- **What a visitor experiences** (an agent, per the docs).
  - [D] A requester **essentials card** of label/value rows: local time, IDs, email, phone, organisation, language.
  - [D] An **Interactions** list of the requester's recent tickets and events, each with a **single-letter status square in
    colour** (P, S, O). Hovering previews the ticket.
  - [D] The context panel **starts closed** and opens from an icon (S-185).
  - [D] An **SLA column** in queue views shows the time left before the next target breaches. Breached targets show a
    negative value (e.g. "-15m"), and paused targets show a pause icon.
  - [D] Green, amber and red thresholds are cited only in a community comment, so they are **unverified**.
- **How it is built.** [D] SLA is a column an admin adds to a view. Context comes from integrated apps.
- **Why it works.** [P]
  - The label/value essentials card is fast to scan.
  - Seeing a customer's other cases stops duplicate work.
  - A due-time column lets a queue sort itself by urgency.
- **What does not fit us.**
  - [D→P] **Panel closed by default.** It is rejected: the brief must be readable in about a minute (US-19), so identity
    status and the brief are open by default on SCR-6.
  - [D→P] **Status as a coloured letter.** It is adapted: our states are words (Unassigned, Waiting …), never a letter or a
    colour alone (WCAG 1.4.1, S-180). Zendesk's red "O" for Open would also spend our safety red.
  - [D→P] **A countdown that goes negative and red.** It is adapted: SCR-5 shows the **due time** ("Mon 7:00 pm · in 2 h",
    tabular). Overdue is the word "Overdue" with a clock icon, never red. "Waiting" shows its wake-up time (US-21),
    which echoes Zendesk's pause icon.
  - [D→P] **Third-party profiles** in the context panel are out of scope: no outside enrichment of customer data (source
    authority rule 8).

## Reference → product mapping

| # | Pattern (finding) | Source | Our application | Maps to | Why | Confidence | Kept / rejected |
|---|---|---|---|---|---|---|---|
| R1-1 | Contact details demanded before any time is shown | R1 [O] | Show windows and the fee that applies before identity; ask for the code only when a private record is needed | FLOW-5, FLOW-3 · SCR-1 slot card · US-10, US-8 | Value first; customers never repeat themselves | High | **Rejected** (inverted) |
| R1-2 | Channel hub: text / call / email / AI chat side by side | R1 [O] | One chat with a persistent "Talk to a person"; no channels we don't run (SMS, call-me) | FLOW-7 · SCR-1 · US-2 | We can't promise channels we don't staff | Medium | **Rejected** |
| R1-3 | "AI" shown as a badge next to the company name | R1 [O] | Disclosure in words in the greeting and on every assistant turn | FLOW-1 · SCR-1 · US-1 | Badges are missed under stress | High | **Adapted** |
| R1-4 | Brand red on every action | R1 [O] | Red only on the safety card; primary in a non-red, non-orange hue | all · SCR-1 · profile §7 | Keeps the safety signal unspent | High | **Rejected** |
| R1-5 | Offer with its condition in the same block; licence number in the footer | R1 [O] | Fees shown with their rule beside them (e.g. the $89 diagnostic with Meridian's credit rule, quoted from the fee schedule, not paraphrased). No licence number: Meridian has none on record | FLOW-1, FLOW-5 · slot and confirmation cards · US-6, US-10 | Fair, checkable money (profile §6 Q3) | Medium | **Adapted** (no invented licence) |
| R1-6 | 30-minute start-time slots vs an arrival window | R1 [D] S-182 | Show Meridian's arrival windows by zone (4 hours, or 3 for the Tue/Thu 4–7 pm window), labelled "arrival window" | FLOW-5 · SCR-1 slot card · US-10, US-11 | Matches the DB and sets honest expectations | High | **Adapted** |
| R2-1 | One action-first sentence; numbers as tap targets | R2 [O] | Safety card leads with Meridian's KB sentence verbatim, "Leave the home immediately and call 911 or your gas utility from outside" (numbered layout allowed, words unchanged; corrected 2026-10-20 from "now"); tap-to-call labelled "(from outside)" | FLOW-2 · SCR-1 safety card · US-3 | First words are the action | High | **Kept** |
| R2-2 | "DON'T use your phone, tablet, computer or other mobile devices" | R2 [O] | Safety card is Meridian's instruction word for word and invites no typing (no field, question or prompt). The optional contact offer is one quiet line for "once you're outside and safe". **Applied to FLOW-2, 2026-10-20 (proposal)** | FLOW-2 · SCR-1 · US-3 | The chat itself is a phone in use near a leak; Meridian's policy says "from outside" | High | **Kept; FLOW-2 updated** |
| R2-3 | Emergency link inside the menu at 390 px; ⚠ orange banner used for a billing notice | R2 [O] | Safety, emergency number and "Talk to a person" are never behind a menu. Safety styling only for safety; demo and staffing banners neutral | FLOW-2, FLOW-7, FLOW-12 · SCR-1, SCR-3 · US-2, US-3, US-25 | An alarm used for routine news stops working | High | **Rejected** (inverted) |
| R2-4 | Dismissible modal with "Ok", no signal word | R2 [O] | Pinned, non-dismissible card with the signal word DANGER, an icon and numbered text | FLOW-2 · SCR-1 · US-3 | Colour never alone; stays visible on scroll | High | **Adapted** |
| R3-1 | "You are now speaking with Fin" plus "Fin · AI Agent" on every message | R3 [O] | "Meridian assistant · automated" label on every assistant turn; "Riley · representative (demo)" on staff turns; a "Riley has joined" event line | FLOW-1, FLOW-8 · SCR-1 · US-1, US-15 | Answers "is this a person?" on every line | High | **Kept** |
| R3-2 | No visible person control; ask in words only | R3 [O] | Persistent "Talk to a person" button, honoured on the first tap or the first ask in words | FLOW-7 · SCR-1 · US-2 | Customers fear losing access to a person (P8) | High | **Rejected** (inverted) |
| R3-3 | "The team can also help" in the header | R3 [O] | Header subline: whether anyone is online now, in plain words, from the staffing state | FLOW-7, FLOW-8 · SCR-1 · US-2, US-15 | Honest presence without a promise | Medium | **Adapted** |
| R3-4 | Dynamic reply time (7-day median); queue position | R3 [D] | Promise text and due date only from the policy table; no queue position, no wait estimate | FLOW-7 · SCR-1 handoff card · US-14 | We can't measure it; honesty rules | High | **Rejected** |
| R3-5 | "Waiting for a teammate" after transfer | R3 [D] | Only in simulated staffed mode: "A representative will join this chat when available" | FLOW-8 · SCR-1 · US-15 | Truthful about the live path; no time | High | **Adapted** |
| R4-1 | Essentials card (label/value rows) + other cases with hover preview | R4 [D] | SCR-6 "Who they are" section as label/value rows with identity status; "Other cases for this customer" by reference, with status in words | FLOW-9 · SCR-6 · US-19 | Fast scan; avoids duplicate cases | Medium | **Adapted** |
| R4-2 | SLA column: time to next breach, negative when breached, pause icon | R4 [D] | SCR-5 "Due" column with the due time and a relative hint; "Overdue" word plus icon; Waiting shows its wake-up time | FLOW-9, FLOW-10 · SCR-5, SCR-7 · US-18, US-22 | Sort by urgency without countdown pressure or red | High | **Adapted** |
| R4-3 | Status as a coloured single letter (red O = Open) | R4 [D] | States in words; no red outside safety | SCR-5, SCR-6, SCR-8 · US-18 | WCAG 1.4.1; reserved red | High | **Rejected** |
| R4-4 | Context panel closed by default | R4 [D] | Brief and identity open by default | SCR-6 · US-19 | One-minute read | High | **Rejected** |

## Notes for the orchestrating session (report, not edited here)

- **FLOW-2 step 2 (UX-1). Resolved 2026-10-20:** the orchestrating session kept Meridian's wording exact (no added
  "stop using the phone" line, which is not in the KB) and replaced the contact prompt with one quiet line for after
  the customer is outside. The System-track session confirmed this still meets R-6 (an offer, never a gate).
- **The demo bar and simulated-staffing banner (SCR-1, SCR-3)** must not use warning styling (R2-3). This is a styling
  note for UX-3 `design.md`, not a flow change.
