# UX-1 · User stories — Meridian AI service agent

> **Status:** DRAFT 2026-10-20 · UX-1 (ux-pipeline pilot) · **PRD:** [`docs/prd/inno-aea-callcenter-prd.md`](../../prd/inno-aea-callcenter-prd.md) **v0.4, approved at the Stage 4 gate (Innocent, 2026-10-20)**. Drafted on v0.2, re-checked against 0.4 the same night (R-35, R-36, R-38 changes applied).
> **Early start (Innocent, 2026-10-20, 21:05 CT):** "while i settle things with aea investors stage 4 lets start the ux stages". The UX track runs beside the Stage 4 interview. **Any PRD change from Stage 4 reopens this file and everything that depends on it.**
> Flows: [`USER_FLOWS.md`](USER_FLOWS.md) · Screens: [`SITEMAP.md`](SITEMAP.md) · Worked pairs: [`docs/data/worked-pairs.md`](../../data/worked-pairs.md) · Hard problems: [`docs/design/hard-problems.md`](../../design/hard-problems.md) (all four cards chosen at Stage 3).

**Who the users are** (PRD §2): the **homeowner** (customer) using the chat; the **representative** who picks up a
handoff; the **supervisor** who makes sure nothing urgent, unowned or overdue is left; the **business owner** who wants to
know whether the AI cuts load without hurting customers; and the **reviewer** (AEA's grader), who will "ask their own
questions and try to break it" and "watch the agent escalate". In the demo, the reviewer plays every staff role through a
labelled role switch (OD-1, OD-2) behind one demo login that gates the whole deployment (R-48).

**Priority** follows the PRD's M/S/C (§4): **P0** = a Must requirement, **P1** = Should, **P2** = Could.

## Requirement coverage

Every PRD requirement with something a person sees or does. Two have no screen at all and are listed after the table.

| Requirement | Stories |
|---|---|
| R-1 | US-1 |
| R-2 | US-2 |
| R-3 | US-1, US-25 |
| R-4 | US-6 |
| R-5 | US-3 |
| R-6 | US-3 |
| R-7 | US-4 |
| R-8 | US-5 |
| R-9 | US-6 |
| R-10 | US-6 |
| R-11 | US-6 |
| R-12 | US-27 |
| R-13 | US-6, US-7 |
| R-14 | US-6, US-8 |
| R-15 | US-8, US-25 |
| R-16 | US-8 |
| R-17 | US-9 |
| R-18 | US-10 |
| R-19 | US-10 |
| R-20 | US-10 |
| R-21 | US-12 |
| R-22 | US-13 |
| R-23 | US-11 |
| R-24 | US-2, US-14 |
| R-25 | US-14 |
| R-26 | US-14 |
| R-27 | US-14 |
| R-28 | US-19 |
| R-29 | US-19 |
| R-30 | US-2, US-15, US-22, US-25 |
| R-31 | US-15, US-20 |
| R-32 | US-18, US-22, US-24 |
| R-33 | US-18, US-20, US-21, US-22 |
| R-34 | US-14, US-21, US-25 |
| R-35 | US-27 |
| R-36 | US-27 |
| R-37 | US-21, US-23 |
| R-38 | US-27 |
| R-39 | US-24, US-27 |
| R-40 | US-25 |
| R-41 | US-16, US-26, US-27 |
| R-44 | US-10 |
| R-45 | US-17 |
| R-46 | US-16, US-19 |
| R-47 | US-3, US-4, US-5 |
| R-48 | US-25, US-28 |

**No screen (System track and delivery only):** R-42 (public repository) and R-43 (README, technical documentation,
deployment guide, test results, video). They are deliverables, not product surfaces; `SUBMISSION.md` tracks them.

---

## Stories — homeowner (customer chat)

### US-1 · Know it's an automated assistant, and what "today" is
As a **homeowner**, I need the chat to say plainly that it is Meridian's automated assistant and to show the date it is
working from, so that I never think I'm talking to a person and every "tomorrow" or "Friday" means what I think it means.
- Requirements: R-1, R-3
- Evidence: audit E-6, L-6, C-9 · Hard problem: none
- Acceptance: the greeting says "automated assistant"; "are you a person?" gets a truthful no; a date chip shows "Fri Oct 16, 2026 (demo date)".
- Priority: P0

### US-2 · Ask for a person at any moment, and get one on the first ask
As a **homeowner**, I need a "Talk to a person" control that is always visible and works the first time (button or words),
so that I never have to argue with a bot to reach someone.
- Requirements: R-2, R-24, R-30
- Evidence: WP-7 · Hard problem: HP-4
- Acceptance: one tap or one "I want a person" starts the handoff; I'm told honestly whether anyone is online.
- Priority: P0

### US-3 · Get the safety instruction first
As a **homeowner** who smells gas, hears a CO alarm or sees sparks, smoke or flames, I need the safety instruction before
anything else, so that I leave the home before I'm asked for a name or an account.
- Requirements: R-5, R-6, R-47
- Evidence: WP-5 · Hard problem: HP-2
- Acceptance: the first reply is Meridian's instruction verbatim ("leave the home immediately and call 911 or your gas utility from outside…"), even mid-chat or with typos; contact details are offered afterwards, never required; no follow-up time is promised.
- Priority: P0

### US-4 · Burning smell, unclear risk: asked, not told to check
As a **homeowner** who reports a burning smell from the vents, I need to be asked whether the breakers have already tripped
or there is smoke, sparks or flames, so that I get the right path without being sent to poke at an electrical panel.
- Requirements: R-7, R-47
- Evidence: WP-6 · Hard problem: HP-2
- Acceptance: yes → the safety instruction; unclear → a conditional instruction, the emergency number and a priority case; both ruled out → an urgent booking.
- Priority: P0

### US-5 · No heat, no cooling or a leak: book normally, unless someone is in danger
As a **homeowner** with no cooling on a hot day, I need to book a visit like any repair, with a couple of skippable
urgency questions, and to be given the emergency number first if I say someone is in danger, so that I'm neither
frightened needlessly nor left waiting when it matters.
- Requirements: R-8, R-47
- Evidence: WP-3 · Hard problem: HP-2
- Acceptance: without danger, the urgency answers go into the booking note; with danger, the emergency number (512) 555-0199 (demo placeholder) comes first and any "within 1 business day" line is separate.
- Priority: P0

### US-6 · Ask a policy question and get the current answer, with its source
As a **homeowner**, I need answers about membership, billing fees, warranty, services, hours and the service area that come
from Meridian's current documents and show where they came from, so that I can trust the number I'm given.
- Requirements: R-4, R-9, R-10, R-11, R-13, R-14
- Evidence: WP-1 · Hard problem: HP-1
- Acceptance: the answer quotes exact fees and terms and names its source and version date (for example the 2026 fee schedule PDF or the holiday-hours image); never an archived copy; no code needed for public questions.
- Priority: P0

### US-7 · Hear "I don't know" when the documents don't say
As a **homeowner** asking something Meridian's files don't cover, I need the assistant to say it doesn't have that
information and offer a person, so that I'm never given a confident guess.
- Requirements: R-13
- Evidence: PRD §4.3a ("Questions the files can't answer") · Hard problem: HP-4
- Acceptance: "How long have you been in business?" → "I don't have that information" plus the "Talk to a person" offer.
- Priority: P0

### US-8 · Prove it's my account with a code before private details
As a **homeowner** asking about my bill, I need to receive a one-time code at the phone or email on my account and type it
in the chat, so that nobody else can read my account by guessing my name.
- Requirements: R-14, R-15, R-16
- Evidence: WP-2 · Hard problem: HP-3
- Acceptance: I see only a masked hint ("the phone ending in 02"); the code never appears in the chat; no match, a wrong code three times or an expired code ends in a person without revealing whether an account exists.
- Priority: P0

### US-9 · Understand my invoice, membership or warranty after the code
As a **verified homeowner**, I need my invoice lines, membership tier and renewal date, or my install date and warranty term
explained in plain numbers, so that I know what I'm paying for and what's covered.
- Requirements: R-17
- Evidence: WP-2, WP-8 · Hard problem: HP-3
- Acceptance: INV-204411 lines read as billed ($89, $245, $144); no verdict on whether the bill is right; a dispute starts a handoff (US-14).
- Priority: P0

### US-10 · Book a repair or tune-up that fits my area, my membership and my day
As a **homeowner**, I need to see open windows in my zone (member-reserved ones if I'm a member), pick one, and get a
confirmation with the date, window, technician and the fee that applies to me, so that I know exactly who is coming,
when, and for how much.
- Requirements: R-18, R-19, R-20, R-44
- Evidence: WP-3 · Hard problem: HP-3
- Acceptance: arrival windows and the standard fee are shown before any identity step (the zone comes from a ZIP or city); the code is asked before the booking is written, and the member fee or member-reserved windows appear after it; only valid slots are offered; a slot taken meanwhile gives alternatives, never a double booking; out-of-area gets an honest no; the optional quick checks can be declined in one tap.
- Priority: P0

### US-11 · Book a replacement estimate with a Comfort Advisor
As a **homeowner** thinking about a new system, I need to book an estimate visit, so that an advisor can quote on site.
- Requirements: R-23
- Evidence: inventory §3.1 (12 estimate calls) · Hard problem: HP-3
- Acceptance: only `estimate` slots are offered; the confirmation names the Comfort Advisor.
- Priority: P0

### US-12 · Move my visit: myself when it's free, through a person when it costs $49
As a **homeowner** who needs a different time, I need the assistant to move the visit when there's no fee, and, when it's
inside 24 hours, to explain the $49 fee, record my request and tell me the original visit stands until a person
confirms, so that I'm never charged or moved by surprise.
- Requirements: R-21
- Evidence: WP-4 · Hard problem: HP-3
- Acceptance: a fee-free move confirms the new window; a fee-bearing request shows "the $49 fee applies under current policy", "your original appointment stays until a representative confirms", and a reference.
- Priority: P1

### US-13 · Confirm or cancel my visit
As a **homeowner**, I need to confirm my appointment, or cancel it when it's more than 24 hours away, so that I don't have
to call.
- Requirements: R-22
- Evidence: inventory §5.3 (confirm 8, cancel 6) · Hard problem: HP-3
- Acceptance: confirm shows the booked window; a cancel inside 24 hours is handled like US-12's fee-bearing path.
- Priority: P2

### US-14 · When it hands me off: a reference, an honest promise, and my choice of follow-up
As a **homeowner** whose request needs a person, I need a reference number, the exact promise (who gets back to me and by
when), and a choice of email or phone and a time window, so that I know what happens next and never repeat my story.
- Requirements: R-24, R-25, R-26, R-27, R-34
- Evidence: WP-7, WP-8, WP-2 · Hard problem: HP-4
- Acceptance: nobody online → "A representative will get back to you within 1 business day" with the due date and reference; refund → "within 2 business days" (a response, not a refund); nothing says a message was sent.
- Priority: P0

### US-15 · When someone is on shift: wait in the chat and see a person join
As a **homeowner** during staffed hours (simulated in the demo), I need to wait in the same chat and see clearly when a
person has joined and the assistant has stopped, so that I know who I'm talking to.
- Requirements: R-30, R-31
- Evidence: consolidated §4 Branch A · Hard problem: HP-4
- Acceptance: "A representative will join this chat when available"; "Riley (demo representative) has joined"; the hand-back to the assistant is announced; if the shift ends first, I get the same 1-business-day promise and reference.
- Priority: P1

### US-16 · Never be told something happened when it didn't
As a **homeowner**, I need the assistant never to say "done", "cancelled" or "refunded" unless it really did it, and to hand
me to a person when it hits a limit, so that I can believe what it says.
- Requirements: R-41, R-46
- Evidence: WP-8 · Hard problem: HP-4
- Acceptance: "cancel my membership" → no completion claim, a case with a promise; a rate or spend limit → a handoff, not an error page.
- Priority: P0

### US-17 · Have follow-ups understood in context
As a **homeowner** mid-booking, I need "what about Monday?" to apply to the visit we were just arranging, so that I don't
start over every message.
- Requirements: R-45
- Evidence: WP-1 (three questions in one message), WP-3 · Hard problem: HP-1
- Acceptance: the follow-up resolves against the open task; a 20-turn chat keeps my verified identity and the open task; a safety phrase mid-chat still comes first.
- Priority: P0

## Stories — representative (staff console)

### US-18 · See what needs my action, most urgent first
As a **representative**, I need a queue with safety and danger cases (P0/P1) on top, then by due time, and the live queue
when staff are on shift, so that I pick up the right case next.
- Requirements: R-32, R-33
- Evidence: consolidated §6 · Hard problem: HP-4
- Acceptance: overdue and P0/P1 cases are first; each row shows reason, priority, due time and owner.
- Priority: P1

### US-19 · Understand a case in about a minute, and check any fact
As a **representative**, I need an eight-heading brief that keeps facts and customer claims apart, the pertinent sources
(what the AI saw and the current value), the promise with the follow-up preference beside it, and the full chat one
click away, so that I can act without re-asking the customer.
- Requirements: R-28, R-29, R-46
- Evidence: WP-2 (brief example in consolidated §5) · Hard problem: HP-4
- Acceptance: every fact opens its source; a changed value shows "changed since"; a heading where the fact check removed something is flagged.
- Priority: P0

### US-20 · Claim a live case, join the same chat, then hand it back or close it
As a **representative** on a simulated shift, I need to claim a live-queued case, reply in the customer's chat while the
assistant is paused, and hand back or close explicitly, so that the customer has one conversation, not two.
- Requirements: R-31, R-33
- Evidence: consolidated §4 Branch A, §8 · Hard problem: HP-4
- Acceptance: the claim pauses the AI; my messages reach the customer's chat; hand-back resumes the AI and the customer sees it.
- Priority: P1

### US-21 · Record what I did, close the case, and flag the AI's mistakes
As a **representative**, I need to log a contact attempt (clearly "recorded, not sent"), set the outcome, put a case in
waiting with a wake-up time, and flag a wrong AI answer, brief or escalation, so that the promise is tracked and the AI
can be corrected by people.
- Requirements: R-33, R-34, R-37
- Evidence: consolidated §4 step 6 · Hard problem: HP-4
- Acceptance: the activity reads "Demo: recorded, not sent"; the promise shows kept or missed against its due time; a flag appears on the review list.
- Priority: P1

## Stories — supervisor

### US-22 · At shift start, see what's urgent, unowned, due soon, overdue or stuck, and assign it
As a **supervisor**, I need one view of P0/P1, unowned, due-soon, overdue and stuck-waiting cases with owner, age and
follow-up preference, and to assign or reassign with a reason, so that no promise is missed. In the demo I also start or
end the simulated shift and advance the simulated clock.
- Requirements: R-30, R-32, R-33
- Evidence: consolidated §6 alerts; §8 seeded oversight data · Hard problem: HP-4
- Acceptance: advancing time moves a seeded case into "overdue"; ending the shift with someone live-queued converts them to the async promise and raises an alert.
- Priority: P1

### US-23 · Review what staff flagged as AI mistakes
As a **supervisor**, I need a list of flagged answers, briefs and escalations with the case behind each, so that someone
decides the fix; nothing changes the knowledge base or prompts automatically.
- Requirements: R-37
- Evidence: audit G-6, C-13 · Hard problem: none
- Acceptance: each flag links to its case and message; nothing on the list edits the KB.
- Priority: P1

## Stories — business owner

### US-24 · Know whether the AI cuts load without hurting customers
As a **business owner**, I need the in-scope correct-resolution rate, promises kept on time, outcomes with their
denominators, and handoffs by reason, each opening the cases behind it, so that I can decide what to fix or widen next.
- Requirements: R-32, R-39
- Evidence: framing §1–§3 · Hard problem: none
- Acceptance: every number shows its denominator; a handoff is not counted as containment; numbers come from stored data or a named eval run, never a target.
- Priority: P2

## Stories — reviewer (AEA's grader)

### US-25 · Use the demo without being misled about what's simulated
As a **reviewer**, I need a demo (reached with the demo login) where the date, the empty staffing, the code inbox and the
"recorded, not sent" follow-ups are all labelled as demo simulations, and a one-click role switch that lets me play the
representative without separate accounts, so that I can "watch the agent escalate" and judge it honestly.
- Requirements: R-3, R-15, R-30, R-34, R-40, R-48
- Evidence: audit E-5 (implied staffing trap); consolidated §8 · Hard problem: HP-4
- Acceptance: the staffing banner shows on both chat and console whenever the simulation is on; the demo inbox says "Simulated messages. Nothing is sent to anyone."; a reset restores the demo; the role switch (US-28) is how the reviewer becomes the representative.
- Priority: P0

### US-26 · Try to break it and see it fail cleanly
As a **reviewer**, I need prompt injection, account fishing and spam to meet limits that end in a polite handoff, so that I
see "clean failure", not a crash or a leak.
- Requirements: R-41
- Evidence: audit G-2, G-5 · Hard problem: HP-4
- Acceptance: a rate limit or booking cap shows a plain message and the person option; no account existence is revealed.
- Priority: P0

### US-27 · See the system's health and the evaluation behind the containment number
As a **reviewer** (and the business owner), I need a monitoring page (volume, containment, escalations, failures,
latency, spend against the daily cap, alerts as decision lines, and when the health check last restarted the service)
and the evaluation report (test-set mix, retrieval hit rate, accuracy and escalation rates, each with its denominator,
and which split each number comes from), with no codes or card numbers in what's shown, so that I can check the claims
myself.
- Requirements: R-12, R-35, R-36, R-38, R-39, R-41
- Evidence: Part B §7; framing §2; PRD 0.4 Stage 4 answers Q-045 (alerts on the page), Q-054 (dev and held-out splits) · Hard problem: none
- Acceptance: health is shown separately from correctness; alerts live on the page (no push channel); the headline number comes from the **sealed held-out split** and says so, dev-split numbers are labelled as dev; the report names its run, date and split sizes; redaction holds on seeded data; traces stay in Langfuse on Innocent's VPS and are not exposed on the public pages.
- Priority: P0

### US-28 · Sign in once, then switch between customer and staff in one click
As a **reviewer**, I need to sign in once with the demo login given in the README and then switch between acting as the
customer and acting as a representative, supervisor or business owner in one click from any screen, so that I can play
both sides of a handoff without separate accounts or passcodes.
- Requirements: R-48
- Evidence: Innocent, 2026-10-21 (Stage 6): "it should be password-gated in general … we're going to need to be able to act as staff and act as the customer … make that easy for the reviewer" · Hard problem: none
- Acceptance: nothing except the login and `/healthz` answers without the login; one username and password (from Railway variables, shown only in the README) opens everything; after login a role switch showing the current role is on every screen and changes role in one click with no second password; reset and the staffing toggle need the login; a wrong login gets one message whatever the cause; an expired session returns to the login.
- Priority: P0
