# Meridian Home Comfort: company and service-context profile

**Date:** 2026-10-20, America/Chicago. **Writer:** Claude (Opus 5.5). **Status:** DERIVED reference for UX/UI research and
product design. Not a PRD, not a design system, not an approved requirement. **Audience:** whoever runs the UX track
(zero-to-hero §4b) and the product-design work after the PRD is approved.

**Builds on:** the [handoff information inventory](../data/handoff-information-inventory.md) (call counts and call IDs),
the [brief audit](2026-10-20-brief-audit.md) (KB conflicts K-1…K-18) and the
[handoff product direction](2026-10-20-human-handoff-product-direction.md) (handoff features and research).
**New outside sources:** S-170…S-180 in the [source register](../source/source-register.md); S-130 and S-131 reused.

## How to read the labels

Every factual sentence carries one of three labels. They are not interchangeable.

| Label | Means | Cites |
|---|---|---|
| **Meridian fact** | Stated in the issued data. Transcripts prove only what a caller or agent *said*, never that an agent's answer was correct. | An exact file, table/field or call ID |
| **Industry context** | True of residential HVAC or plumbing service in general, from an outside source. **Not assumed to be true of Meridian.** | `S-N` |
| **Design inference** | Our interpretation or proposal. Not established, not approved. | — |

Paths: KB files are under `docs/data/issued/meridian_dataset/knowledge_base/`; DB tables are in
`scheduling_db/meridian_scheduling.sqlite` (`SCHEMA.md` beside it). Call IDs omit the `CALL-` prefix. Call counts come
from the inventory's reproducible scripts over all 420 transcripts.

---

## 1. Company at a glance

**In one paragraph.** Meridian Home Comfort is a fictional residential heating, cooling and plumbing company serving the
Austin, Texas metro. Homeowners call it to fix a system that stopped working, to book seasonal tune-ups, to replace an
ageing system, and to manage a paid maintenance membership called the Comfort Club. Its call center cannot keep up with
call volume, which is why an AI agent is wanted. *(Meridian fact: dataset `README.md`; `services/service_catalog.md`;
`membership/comfort_club_overview.md`.)*

| Topic | What the issued data says | Source (**Meridian fact**) |
|---|---|---|
| **Business problem** | "Its call center is capacity constrained and the exec team wants an AI agent to handle the bulk of routine inbound calls." | dataset `README.md` |
| **Where it works** | Residential service in ZIP groups for Austin (787xx), Round Rock, Cedar Park/Leander, Pflugerville/Hutto, Georgetown and Kyle/Buda. Dripping Springs (78620) and Manor (78653) were "newly added April 2026". | `policies/service_area.md` (updated 2026-04-01) |
| **Where it doesn't** | San Marcos, Bastrop, Elgin and Lakeway west of 620. "We do not travel outside the service area." | `policies/service_area.md`; `faq/customer_faq.md` |
| **How work is organized** | Three zones (north, central, south). The scheduling DB has six field technicians (HVAC, plumbing, or both) and two Comfort Advisors for estimates. | `SCHEMA.md` zone map; `technicians` table |
| **Customers** | 154 residential customers in the DB across nine cities. One system per customer, six brands (Trane 31, Rheem 28, Goodman 27, American Standard 27, Lennox 24, Carrier 17), installed 2011 to 2026. | `customers` (`city`, `system_brand`, `system_install_date`) |
| **Membership** | Comfort Club Standard ($189/yr or $16.99/mo with a 12-month minimum) and Plus ($269/yr). 56 of 154 DB customers are members: 38 Standard, 18 Plus. | `membership/comfort_club_overview.md`; `2026_fee_schedule.pdf`; `customers.membership_tier` |
| **Services** | HVAC diagnosis and repair; seasonal tune-ups; system replacement through a free in-home estimate; residential plumbing (water heaters, drain clearing, leak detection, water-heater flush). | `services/service_catalog.md` |
| **Emergency support** | "After-hours emergency line: available 24/7 for no-heat, no-cool, and active water leaks." $149 after-hours dispatch, waived for members; $199 holiday dispatch. | `faq/customer_faq.md`; `2026_fee_schedule.pdf`; `policies/holiday_hours_2026.png` No KB file gives the emergency line's phone number (all 17 files checked) |
| **Safety protocol** | Gas smell, CO alarm, sparks/smoke/flames, or a burning smell with tripped breakers: leave the home, call 911 or the gas utility from outside, then flag the account as a priority emergency. | `policies/escalation_and_safety.md` (Rev 2026-01) |
| **Phone hours** | Mon–Fri 7am–7pm, Sat 8am–4pm, closed Sunday. | `faq/customer_faq.md` |
| **Not offered** | Commercial HVAC (referred to Meridian Commercial), duct cleaning (third-party referral; the referral process is an unwritten stub), window or portable AC, appliance repair. | `services/service_catalog.md`; `services/duct_cleaning.md` |

**Design inference.** The customer is a household dealing with the comfort, water or safety of the place they live, not
a business buyer. Almost every interaction is tied to a physical system at a physical address. That makes the
**address, the equipment and the appointment window** the three objects the experience is built around.

---

## 2. Value proposition

The issued data contains **no mission statement, tagline or brand promise**, and this report does not invent one. What it
does contain are concrete commitments to homeowners. They are separated below from what we read into them.

### Explicit commitments in the issued data (**Meridian fact**)

| Commitment | Wording or rule | Source |
|---|---|---|
| Help is reachable outside office hours for urgent comfort and water problems | 24/7 line for "no-heat, no-cool, and active water leaks" | `faq/customer_faq.md` |
| Know who is coming and when | A text "the morning of your appointment with the technician's name and photo, and another text when the tech is 30 minutes away" | `faq/customer_faq.md` |
| You are not punished for a late technician | "Customers are not required to wait past the window. A missed window is never charged as a no-show." | `services/technician_arrival_and_etas.md` |
| Price before work | "Exact pricing is quoted by the technician on site before work begins." Typical ranges published | `services/service_catalog.md`; `pricing/repair_price_book_2026.csv` |
| The diagnostic fee is not wasted if you repair | $89, "applied as credit toward the repair if you approve the repair during the same visit" | `faq/customer_faq.md` |
| Your card stays off the phone | "Card numbers are never taken over the phone"; a secure link valid for 24 hours | `faq/customer_faq.md` |
| Work is backed | 1-year labor warranty on the repaired part; 2-year install labor (5 years if a member at install); every install registered with the manufacturer within 30 days | `warranty/warranty_policy.md` (effective 2025-06-15) |
| Members get looked after first | Two tune-ups a year, priority scheduling, diagnostic fee waived, 15% off repairs, no after-hours fee | `membership/comfort_club_overview.md` |
| Replacing a system is advised, not pushed by phone | Free in-home estimate with a Comfort Advisor; financing on repairs over $1,000 and all replacements | `services/service_catalog.md`; `faq/customer_faq.md` |
| A complaint reaches a person | Supervisor callback within 1 business day for disputes, refunds, conduct and manager requests | `policies/escalation_and_safety.md` |

### Our reading of them (**Design inference**)

- The offer is **predictable home comfort**: timely repair, prices you can see in advance, and a membership that buys
  priority when everyone else is waiting. The membership looks like the company's main relationship and retention device.
- The company's weakest promises are about **time**. Arrival windows are four hours, and the late-technician procedure
  exists because windows get missed. That is where trust is won or lost.
- **Industry context:** this shape is common. Maintenance plans with two seasonal tune-ups, priority service and 10–20%
  repair discounts are typical, and larger firms offer three or four tiers (S-176). Meridian's plan should therefore be
  read as an ordinary category feature, not a differentiator, unless research shows otherwise.

---

## 3. How service works

One customer journey, from a problem at home to follow-up. Each step says what the **issued data supports**, what is
**industry context**, and what is missing.

| Step | Meridian fact (issued data) | Industry context | Gap or design inference |
|---|---|---|---|
| **1. Problem at home** | Booked issues in the DB: replacement estimate 23, water at indoor unit 18, blank thermostat 17, tune-up 17, water-heater pilot out 15, kitchen drain 15, grinding noise 15, furnace won't start 13, AC not cooling 13, blower warranty recall 12 (`appointments.issue_description`) | Austin's normal highs stay at or above 90°F from May 26 to Sep 23 (S-171) | **Inference:** cooling failures dominate the season these calls come from (July–Sept, `call_transcripts_index.csv`) |
| **2. Self-check** | "Agents should walk customers through these before booking a non-emergency visit" (filter, breaker, thermostat, float switch) | ENERGY STAR advises monthly filter checks in heavy-use seasons (S-172) | **Meridian fact:** 0 of 132 booking calls include these checks (inventory §5.3). Whether to offer them is a product choice |
| **3. Contact** | Phone hours and a 24/7 emergency line (`faq/customer_faq.md`). All 420 calls are inbound phone calls (`call_transcripts_index.csv`) | 91% of US adults own a smartphone; 16% rely on it for internet (S-178) | No chat, SMS-inbound or web channel exists in the data. The AI chat is new |
| **4. Triage** | Safety triggers and supervisor triggers (`policies/escalation_and_safety.md`). An "emergency" definition (no-cool above 85°F indoors, no-heat below 55°F, active leak) exists only in the outdated `services/scheduling_guide.md` (Rev 2024-11) | CDC: air conditioning is the main protection against heat illness; older adults are at higher risk (S-170) | Indoor temperature and vulnerable occupants were never asked in any call (inventory §3.4). **Inference:** urgency is the most under-specified part of the flow |
| **5. Account lookup** | Agents ask for account number + name (131 calls), name + phone (125) or name + service address (107) | — | Nothing in the transcripts proves a check against a record; identity method is open (audit DEC-3) |
| **6. Information** | 17 KB files of mixed currency: current FAQ, outdated copies, an internal-only doc, an image-only holiday table (audit §3) | — | **Inference:** source freshness must be visible to staff, not just handled silently |
| **7. Scheduling** | Four-hour windows (`08:00-12:00`, `12:00-16:00`, `13:00-17:00`; `16:00-19:00` Tue/Thu only), zone matching, member-reserved slots (`SCHEMA.md`). Cancel or reschedule inside 24 hours: $49 (`faq/customer_faq.md`, `2026_fee_schedule.pdf`) | ENERGY STAR: book cooling checks in spring, heating in fall, "contractors get busy once summer and winter come" (S-172) | No waitlist or same-day overflow exists in the DB, though the outdated guide mentions both |
| **8. Escalation** | Supervisor callback within 1 business day; department redirects (`policies/escalation_and_safety.md`) | — | No case, callback or owner record exists in the DB (inventory §5.2) |
| **9. Technician visit** | Morning-of text and 30-minute heads-up (`faq/customer_faq.md`); price confirmed on site (`services/service_catalog.md`); late-tech procedure (`services/technician_arrival_and_etas.md`). "Technicians do not enter a home without an adult present" appears only in the outdated scheduling guide | Customers want to know about lateness before the window starts, and favour live ETA (S-177, 2014, dated) | No dispatch or ETA data exists in the DB |
| **10. Billing** | Invoices with line items and balances (`invoices`); payment by secure link, no cards by phone, no checks or cash in the field; financing (`faq/customer_faq.md`) | Texas AC contractors must print the licence number and TDLR notice on proposals and invoices (S-175) | No payment system; `invoices.appointment_id` is NULL in all 81 rows, so an invoice cannot be traced to its visit |
| **11. Follow-up** | Renewal reminder email 30 days before renewal (`membership/comfort_club_overview.md`); manufacturer registration within 30 days and repair labor warranty (`warranty/warranty_policy.md`) | Trane: register within 60 days for the longer parts warranty; dealers often register but "never assume" they did (S-174) | No feedback survey, repair history or registration record in the data |

**Design inference.** Steps 4, 7 and 10 are where the AI can help most and where it can do most harm. Triage decides
whether someone in a hot house waits days. Scheduling decides whether the promise of a window is kept. Billing is where
disputes start.

---

## 4. Customer situations

What matters to the customer in each situation, what they need to know, and where urgency changes the flow. Counts are
primary call categories out of 420 (inventory §3.2). Emotions are **design inference** unless a transcript quote is shown.

| Situation | Meridian facts | Industry context | What the customer needs to know | Where urgency changes the flow (**Design inference** unless cited) |
|---|---|---|---|---|
| **Routine maintenance** (tune-ups 16; membership questions 57) | Tune-up $129 or included for members; two per year (`services/service_catalog.md`, `membership/comfort_club_overview.md`). Example calls 20260711-0109, 20260707-0148 | Seasonal timing, spring and fall (S-172); plans with priority and discounts are common (S-176) | Price or inclusion, the next open window, whether membership pays for itself | Low urgency. Good fit for self-service and for plainly stated membership terms. Tune-up callers were quoted the $89 diagnostic fee instead (inventory §5.3) |
| **Loss of cooling** (AC not cooling, warm air, water at unit; within SCH-HVAC 75) | 24/7 line covers "no-cool" (`faq/customer_faq.md`). Calls in July–Sept. Example 20260714-0178 | Austin highs ≥90°F late May to late Sept (S-171); AC is the main protection against heat illness; don't rely on fans; older adults at higher risk (S-170) | When someone can come; what to do meanwhile; the fee | **Changes the flow** when the home is hot or someone vulnerable is there. Meridian's current rule for that ("no-cool above 85°F indoor") is in the outdated guide only. Callers asked for earlier slots in 34 booking calls ("Can you do anything earlier?", 20260714-0178) **Decided product handling (Innocent, 2026-10-20; not a Meridian capability; narrowed at the Stage 2 check):** a normal booking, with the urgency questions in the booking note. **Only when the customer says someone is in danger because of it:** emergency number first (a fictional placeholder in the demo), an emergency-priority case, and a separate one-business-day review statement if nobody is online. ([consolidated direction §9](2026-10-20-human-handoff-consolidated-direction.md)) |
| **Loss of heating** (furnace won't start: 19 calls) | 24/7 line covers "no-heat". Example 20260709-0103 | — | Same as cooling | Same rule (no-heat below 55°F) sits in the outdated guide. The furnace troubleshooting list says to stop and follow the safety protocol "if you smell gas at any point" (`faq/troubleshooting_before_you_call.md`) **Decided product handling (Innocent, 2026-10-20; not a Meridian capability):** same rule as cooling: a normal booking unless someone is stated to be in danger. ([consolidated direction §9](2026-10-20-human-handoff-consolidated-direction.md)) |
| **Active leaks** (water at indoor unit 16; sink backing up 18; water-heater pilot 7) | 24/7 line covers "active water leaks"; for water at the indoor unit, "turn the system off to prevent overflow damage and book a visit" (`faq/troubleshooting_before_you_call.md`) | Austin Water: know where the shutoff valve is; turn off water at the shutoff if a pipe bursts; renters ask the property manager (S-173) | How to stop the damage now; when help arrives | **Changes the flow** when water is actively flowing. *Inference:* the first useful message is a containment step, then booking. Meridian's KB gives no whole-house shutoff guidance **Decided product handling (Innocent, 2026-10-20; not a Meridian capability):** same rule as cooling (urgent path only when someone is stated to be in danger); no shutoff advice beyond the KB step for water at the indoor unit. ([consolidated direction §9](2026-10-20-human-handoff-consolidated-direction.md)) |
| **Appointment changes** (reschedule 15, confirm 8, cancel 6, late tech 9) | $49 inside 24 hours; late-tech options: reschedule free, or keep the visit with the fee waived (`faq/customer_faq.md`; `services/technician_arrival_and_etas.md`). "My window was 12 to 4 and it's 4:30. Nobody's here and nobody's called." (20260721-0261) | Customers want lateness notice before the window and live ETA (S-177, dated) | Whether a fee applies; the new window; whether to keep waiting | A late technician turns a routine record lookup into a service failure. "I just need to know if I should wait" (20260721-0261) is the core need |
| **Warranty questions** (45) | Repair, install and manufacturer terms; registration within 30 days (`warranty/warranty_policy.md`). Example 20260719-0153 | Manufacturer registration windows and base vs registered coverage differ by brand (S-174, one brand) | Am I covered; will I pay labor; can you come | Mostly not urgent, but a dead compressor in summer is a no-cool case. In 7 of 7 compressor calls the request to schedule was not acted on (inventory §3.2) |
| **Billing disputes and refunds** (24) | Supervisor callback within 1 business day; "Do not promise a specific outcome" (`policies/escalation_and_safety.md`). Customers: "Nobody told me about that" (20260714-0246); "I'd better." (20260710-0136) | — | Who will review it, by when, and what happens to the bill meanwhile | Not physically urgent, but emotionally charged. *Inference:* honesty about timing matters more than speed |
| **Safety** (gas 3, CO 5, sparks 1; plus 16 burning-smell calls the KB does not clearly cover) | Leave, call 911 or the gas utility from outside; don't flip switches, open windows near the furnace or restart equipment (`policies/escalation_and_safety.md`). "My carbon monoxide detector is going off" (20260721-0093) | Gas utility and CDC guidance match the KB protocol (S-130, S-131) | What to do right now, in one instruction | **Overrides everything**: no identity check, lookup or booking before the instruction. The burning-smell-from-vents case is a policy gap (inventory D2) **Decided product handling (Innocent, 2026-10-20; not a Meridian capability):** instruction first; contact offered only afterwards; for a burning smell, ask about breakers already tripped and smoke, sparks or flames, with a cautious escalation path if unclear. ([consolidated direction §9](2026-10-20-human-handoff-consolidated-direction.md)) |

**Design inference: the information pattern.** Across situations, customers ask the same four things in different
orders: *Is this an emergency? When can someone come? What will it cost? What happens next?* The experience should be
able to answer each one, or say plainly who will.

---

## 5. Representative and supervisor context

**What exists today (Meridian fact).** The KB tells human agents what they may resolve (scheduling, explaining invoice
lines, payment links, membership changes, warranty questions, service area and hours) and what goes to a supervisor
(`policies/escalation_and_safety.md`). It also gives them internal discretion (waive the $49 fee once a year, waive the
diagnostic for a late technician, 10% courtesy discount; no refunds) in `internal/agent_discretion_notes.md`. The
transcripts name a "billing supervisor" and a "service manager" (e.g. 20260714-0246, 20260718-0062). **There is no case,
callback, owner, staff-roster or shift data anywhere in the issued materials** (inventory §5.2). Every handoff in the
calls is a promised callback, none a live transfer (inventory §1).

**What a person needs when the AI hands off (Design inference, from the inventory §1 and §7).**

| Block | Why the person needs it |
|---|---|
| Why the AI stopped (fixed reason + the rule that fired) | To know at a glance whether this is safety, policy or a gap |
| The customer's own words | So the customer does not have to repeat the story |
| Verified records with source and time read (appointment, invoice, customer tier) | To act without re-checking, and to see if the record changed since |
| Policy passages used, with file and version date | Because the KB contains outdated copies; staff must see which version the AI used |
| Customer claims kept apart ("the tech quoted me $89") | So claims are not mistaken for facts |
| What the AI already did and its results | To avoid duplicate bookings or contradicting the AI |
| The promise made and its due time | So the promise is kept, and staff know what the customer expects |
| The one unresolved question | So the first action is obvious |

**Two different modes. Neither exists at Meridian today.** Both began as proposals (Design inference). On 2026-10-20 Innocent
decided both for the product and the demo, as product choices, not Meridian capabilities. The default is the
asynchronous path, and the live path appears only inside a labelled simulation ([consolidated direction §8–§9](2026-10-20-human-handoff-consolidated-direction.md)).

| | Proposed **live-chat queue** (staff on shift) | Proposed **asynchronous follow-up** (nobody available) |
|---|---|---|
| When | An explicit "staffed now" setting is on | Default; after hours; Sundays (closed per `faq/customer_faq.md`) |
| What the customer is told | "A person from billing has joined", only when someone has actually claimed the case | "A representative will get back to you within 1 business day", a reference, and the customer's follow-up choice: email by default, or phone, with a time window (decided 2026-10-20) |
| What staff see | A queue sorted by urgency, a claim action, the case, then the same conversation thread | A queue sorted by due time, owner, overdue marker, outcome recording |
| Main risk | Promising a person who is not there; slow pickup | A promise nobody tracks; a callback to an unverified number |

**Supervisor needs (Design inference, based on direction note §8).** What is overdue or due soon, what is unowned,
why the AI hands off most (a sign of KB gaps or scope), and which flagged AI answers await review. Not a wall of metrics.

---

## 6. UX/UI research implications

These are research inputs, not screen specifications.

### How the home-services setting shapes the experience (Design inference, with cited context)

- **Clarity.** The customer is often standing next to a broken unit or a leak, sometimes stressed and hot. Messages should
  lead with the one thing to do or know, and keep fees and windows in plain numbers. Austin's long hot season (S-171) and
  the health risk of losing cooling (S-170) raise the stakes of vague answers.
- **Urgency.** Urgency comes from the situation (gas, active water, heat with vulnerable people), not from the topic.
  Safety must interrupt everything. Comfort urgency must be asked about, because callers in the data never volunteered
  temperatures or vulnerable occupants (inventory §3.4).
- **Trust.** Trust rests on four things the customer can check: who is coming, when, what it will cost, and who will call
  back by when. Texas requires the contractor licence number on invoices and proposals (S-175), a cue customers may look for.
  The AI should show its sources for policy answers and never claim an action it cannot perform.
- **Scheduling.** Four-hour windows, zone limits and member-reserved slots constrain what can be offered (`SCHEMA.md`).
  23 callers asked for after-work 4–7pm slots that exist only Tue/Thu (inventory §5.3). Lateness is the most emotional
  scheduling moment (S-177, dated).
- **Mobile use.** Most adults have a smartphone and some depend on it (S-178). *Inference:* expect one-handed use, poor
  signal at the unit outside, photos of equipment labels as a possible input, and switching between chat and a phone call.

### Research questions

**Customer chat**
1. When something breaks, what do homeowners try first: search, the company's site, a call, a text? What makes them
   abandon a chat for the phone?
2. How should the chat ask about urgency (temperature, vulnerable people, water flowing) without feeling like a form?
3. How should a fee be presented before booking so it reads as fair, not a trap (diagnostic $89, credit rule, $49 late change)?
4. What proof of identity feels acceptable on a phone, and when does it feel like a barrier?
5. Does showing the KB source behind an answer increase trust, or is it noise for customers? (Research caution: citations
   raise trust even when random, direction note P4.)

**Human handoff**
6. What wording makes an asynchronous callback credible, given that callbacks fail on credibility (direction note P5)?
7. What does the customer need to keep after the chat (reference, promise, time, what to do if urgent)?
8. When a person joins live, how does the customer know it is a person and not the AI?

**Staff case view**
9. In what order do representatives read a case: reason, promise, facts, or the conversation?
10. How much verification do they do in practice, and how cheap must "check the record" be for them to do it?
11. What would make them flag an AI error rather than silently fix it?
12. What does a supervisor need to see in under a minute at the start of a shift?

### Principles to test (Design inference)

- **Safety first, every turn.** The safety instruction is the first thing shown, with no lookup or identity step before it.
- **One promise, one source.** The same promise text appears to the customer and on the staff case.
- **Never confirm an action that did not happen.** If a payment link or auto-renew change cannot be performed, say so.
- **Facts and claims look different.** Verified records and customer claims are visually and verbally distinct for staff.
- **Show the clock.** The dataset's "today" is fixed (2026-10-16, dataset `README.md`); dates and fees depend on it.

---

## 7. Brand and color direction

**The issued data provides no official visual identity.** It has no logo, colour palette, typeface, tone-of-voice guide
or brand description. *(Meridian fact: none of the 17 KB files, the README, `SCHEMA.md` or the briefing contain one.)*
The only visual artefact is `policies/holiday_hours_2026.png`, a plain table with a dark slate-blue header band and white
heading text. That is one internal document's styling, **not evidence of a brand system**. Nothing below is borrowed from
a competitor, and nothing here is an official palette.

### Exploratory directions (Design inference)

**Chosen for UX-2 (Innocent, 2026-10-20): direction A, dependable dispatch.** B and C stay on record as alternatives. This chooses what to explore; it is not an official palette or brand system.

Each direction differs in **construction** (layout, type, density, how status is shown), not just colour. Per Innocent's
standing practice, visual directions are chosen later from texture research and clickable prototypes (UX-2), so these are
starting hypotheses for that step.

| Direction | Feeling it should convey | How it is built | Risks to test |
|---|---|---|---|
| **A. Dependable dispatch** | Competent, organized, on time | Structured, information-dense layout; clear timelines for windows and promises; status shown as labelled steps; a sturdy sans-serif with tabular numbers | Can feel cold or bureaucratic to a stressed homeowner; density may hurt on a phone |
| **B. Neighborly home comfort** | Warm, human, reassuring | Conversational layout, generous spacing, softer shapes, plain-language headings; photos of real equipment rather than illustrations | Warmth can read as casual about safety or money; must avoid the cream-and-serif "house texture" the workspace rules reject (`ui-anti-slop.md`) |
| **C. Calm climate control** | Quiet precision, "we've got it handled" | Minimal surfaces, one strong accent, typography-led hierarchy, a thermostat-like clarity for times and temperatures | Too minimal for urgent moments; hot/cold colour coding can collide with status and safety colours |

### Colour roles (no values declared)

| Role | Purpose | Constraint |
|---|---|---|
| **Trust / base** | The everyday surface and text that carries most of the experience | Readable first: 4.5:1 for body text, 3:1 for UI components and large text (S-180) |
| **Warmth** | Human moments: greetings, confirmations, the person who joined | Must not be the same hue family as urgency or danger |
| **Primary action** | Book, confirm, send | One primary action per view; never red or orange (reserved below) |
| **Urgency / comfort-critical** | No heat, no cool, active water | Distinct from safety; always paired with a text label |
| **Safety / danger** | Gas, CO, sparks: "leave the home immediately" (KB wording) | **Reserved for safety only.** Never decorative. Red family is the conventional DANGER signal (ANSI Z535 signal words, S-180); always with text and an icon |
| **Status** | Booked, pending callback, overdue, resolved | Never colour alone: WCAG 1.4.1 (S-180). About 1 in 12 men have a colour-vision deficiency, red–green most common (S-179) |
| **Readability** | Body text, data, fees, times | Tabular numerals for times and amounts; both light and dark themes designed from the start (`ui-typography-and-color.md`) |

**Priority order (Design inference):** accessibility and an unmistakable safety state come before any decorative or brand
colour. If a brand direction needs a red or orange accent, it fails this test unless safety states remain unmistakable.

---

## 8. Unknowns and decisions

### What the dataset cannot tell us

- Who the customers are beyond address, tier and equipment: age, renters vs owners, language, accessibility needs.
- Whether customers want chat at all, and on which device.
- Real staffing: who is on shift, what roles exist, how callbacks are made and tracked.
- What actually happened after any call: no visit outcomes, completed appointments, payments or surveys exist.
- Meridian's brand, tone of voice and visual identity.
- Whether the outdated scheduling guide's emergency thresholds (85°F / 55°F) are still policy.
- Whether timestamps (66 Sunday calls, 6 on Labor Day) reflect real operations (inventory §10.2).

### What would need validation with a real service team

- How representatives read a handoff, and what they re-check.
- Realistic callback times by case type, and whether "1 business day" is kept.
- What makes a homeowner trust an AI's answer about money, warranty or safety.
- How urgent comfort cases are prioritized when the schedule is full in summer.

### Decisions that belong to Innocent

1. ~~Whether the chat asks an explicit urgency question~~ **Decided 2026-10-20: yes**, for no heat, no cooling or leaks, skippable, asked in the booking; an answer that someone is in danger starts the urgent path (narrowed at the Stage 2 check, WP-3) ([consolidated direction §9.1](2026-10-20-human-handoff-consolidated-direction.md)).
2. ~~Which brand direction goes into UX-2~~ **Decided 2026-10-20: direction A, dependable dispatch.** It is still exploratory; UX-2 texture research and prototypes refine it.
3. ~~Whether the prototype includes a staff case view, a live-chat mode, or only the asynchronous follow-up.~~ **Decided 2026-10-20:** all four audience views, plus a labelled simulated staffed state in which the reviewer joins the same chat; the default is unstaffed ([consolidated direction §8](2026-10-20-human-handoff-consolidated-direction.md), OD-1, OD-2).
4. ~~Whether the chat offers the KB's self-checks~~ **Decided 2026-10-20: offered, very optional**, never required, and skipped for urgent cases.
5. ~~The open handoff decisions (inventory D1–D6, audit DEC-1…DEC-5)~~: mostly decided 2026-10-20; status in the [consolidated direction §11](2026-10-20-human-handoff-consolidated-direction.md). All profile decisions are now made. Note: the KB gives no emergency-line number; the demo uses a fictional placeholder, (512) 555-0199.

---

## 9. Source notes

**Issued (Meridian fact).** S-100/S-101 briefing; S-102 transcripts (cited only for what was said or asked, never as
proof an answer was correct); S-103 KB (files named inline); S-104 DB and `SCHEMA.md` (tables named inline); S-105
dataset `README.md`.

| Claim | Source |
|---|---|
| Capacity-constrained call center; AI for routine calls | S-105 `README.md` |
| Service area and exclusions | `policies/service_area.md`; `faq/customer_faq.md` |
| Zones, technicians, Comfort Advisors | `SCHEMA.md`; `technicians` |
| 154 customers, cities, brands, install years, tiers | `customers` |
| Services, ranges, not offered | `services/service_catalog.md`; `pricing/repair_price_book_2026.csv` |
| Membership terms | `membership/comfort_club_overview.md`; `pricing/2026_fee_schedule.pdf` |
| 24/7 line, fees, texts, hours, payment | `faq/customer_faq.md`; `pricing/2026_fee_schedule.pdf`; `policies/holiday_hours_2026.png` |
| Safety, supervisor escalation, what agents can resolve | `policies/escalation_and_safety.md` |
| Late-technician procedure | `services/technician_arrival_and_etas.md` |
| Warranty and registration | `warranty/warranty_policy.md` |
| Emergency thresholds, waitlist, adult present (outdated) | `services/scheduling_guide.md` (Rev 2024-11) |
| Booked issues | `appointments.issue_description` |
| Call counts, examples, gaps | Inventory §3.2, §5.2, §5.3, §10.2 (scripts over S-102) |
| Austin summer heat | S-171 |
| Heat health risk, AC as protection | S-170 |
| Seasonal maintenance timing | S-172 |
| Water shutoff in a burst pipe | S-173 |
| Manufacturer registration | S-174 (Trane only) |
| Texas licence number on invoices | S-175 |
| Typical maintenance plans | S-176 |
| Arrival-window and ETA expectations | S-177 (2014; dated) |
| Smartphone use | S-178 |
| Colour-vision deficiency | S-179 |
| WCAG colour and contrast; ANSI safety colours | S-180 |
| Gas and CO guidance | S-130, S-131 |
