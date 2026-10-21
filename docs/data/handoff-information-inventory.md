# Handoff information inventory: what customers ask for, and what a person needs when the AI hands off

**Date:** 2026-10-20, America/Chicago. **Writer:** Claude (Sonnet 5.5). **Status:** discovery evidence, **DERIVED** (see
[source-authority](../../.claude/rules/source-authority.md)). It is not a PRD, not a scope decision and not a gate
approval. Every "candidate" below is a proposal for Innocent to accept, change or reject.
**Feeds:** Stage 2 data reality and the Stage 1 PRD. **Does not change:** the brief audit's decisions DEC-1…DEC-5, which
stay open. **Reproduce:** [Audit trail](#11-audit-trail).

### How claims are labelled

Four tags, never interchangeable. Where a sentence carries no tag, it is connective prose.

| Tag | Means | Example |
|---|---|---|
| **[T]** | Observed in the 420 transcripts (S-102). Says what was *said*, not what the company's systems did. | "Agent says 'Moved. New confirmation text is on its way.'" |
| **[I]** | Stated in the issued knowledge base, scheduling DB, `SCHEMA.md` or dataset README (S-103…S-105). | "`customer_faq.md`: inside 24 hours there is a $49 late-cancellation fee." |
| **[C]** | A check I computed (script and output named in §11). Reproducible. | "0 of 131 account numbers in the calls exist in `customers`." |
| **[P]** | My proposal. Not evidence, not a requirement. | "Show the rep a saved copy of what the AI read." |

A human agent's statement in a transcript is **[T]** evidence that it was said. It is never **[I]** evidence that it is
true (audit D-5). KB paths below are relative to `docs/data/issued/meridian_dataset/knowledge_base/`.

---

## 1. Executive answer

**What customers call about.** The 420 calls fall into **37 categories** of opening request, grouped into **11 families**. New
service booking is the largest (132 calls, 31.4%), then billing information and payments (67, 16.0%), Comfort Club
membership (57, 13.6%), warranty (45, 10.7%) and managing an existing appointment (38, 9.0%). The corpus is built from
templates, so these shares describe this dataset's mix, not a natural call center's (§2).

**What actually reaches a person.** **54 of 420 calls (12.9%)** open with something the KB sends to a person or a safety
response: 9 safety reports, 16 invoice disputes, 8 refund demands, 16 service complaints and 5 commercial quote requests.
In every one of the 54, that trigger is in the caller's *first* request. **No call starts as a routine request and
turns into a dispute, refund demand, manager request or safety report later (0 of 420)** **[C]**. A test of mid-call
escalation therefore needs synthetic cases (labelled as such); the transcripts cannot supply them.

**The seven findings that matter most for handoff design**

1. **Every human handoff is a callback, never a live transfer.** No call ends with "connecting you now" **[T]**. The
   promise differs for the same kind of case: invoice disputes get "one business day" (16 calls), refunds "two business
   days" (8), and technician or service complaints "today", "marked urgent" (16). The KB says one business day for all of
   them and "Do not promise a specific outcome" (`policies/escalation_and_safety.md`). **[T][I]**
2. **The handoff record the KB asks for was never created.** The KB says "Log the case with the customer's preferred
   callback window." No agent asks for a callback window or number (0 of 420) and none gives a reference number (0 of 420)
   **[C]**. In the 54 handoff calls a phone number is spoken in only 22; the other 32 callers would have to be reached
   through the customer record. All nine safety callers are never identified (no name, account or number), so the
   "priority note on your account" the agent promises has no account to attach to **[T][C]**.
3. **The issued database cannot verify any caller in the transcripts.** None of the 131 account numbers, 130 phone numbers
   or 42 invoice numbers spoken in the calls exists in the DB, and none repeats across calls **[C]**. The calls give us
   *questions and what humans said*, not records. Only the four seeded customers (`SCHEMA.md`) and invoice INV-204411
   are verifiable, and no transcript mentions them.
4. **74 calls (17.6%) were completed by a human using something the issued materials do not contain**: sending payment
   links and setting up autopay (28), turning off auto-renew (13), opening a card-processor ticket (11), confirming a
   manufacturer registration (10), upgrading a plan with a payment (6), and checking repair history (6). The DB has five
   tables and none of them can do these things. An AI that said "Done, auto-renew is off" would be inventing an action.
   Each such call is either a simulated action (labelled) or an honest handoff **[C][I]**.
5. **Several things human agents said do not match the current KB**, so transcripts cannot be an answer key (§5.3):
   the $60 invoice-vs-quote gap that agents explain as an "after-hours", "permit" or "disposal" fee (no fee in the KB is
   $60); 14 of 15 reschedules inside 24 hours with no mention of the $49 fee; tune-up bookings quoted the $89
   diagnostic fee, not the $129 tune-up price (16 of 16); warranty periods quoted from the retired rule ("under a year").
6. **Safety is only partly covered by policy.** The nine gas, CO and sparks calls follow the KB protocol. Sixteen *other*
   calls report "something burning from the vents", and human agents booked all 16 as routine repairs without asking
   about breakers. The KB's burning-smell rule applies only "combined with tripped breakers" **[T][I]**. That is a policy
   gap, not an agent error, and it needs a decision (§10.4, D2).
7. **For invoice questions, the DB cannot answer "why was I charged the diagnostic fee too?".** All 45 invoices that
   bill a diagnostic visit also bill a repair, none has a credit line, and `invoices.appointment_id` is NULL for all 81
   invoices. `customer_faq.md` says the $89 is credited if the repair is approved at the same visit. Whether it was
   cannot be shown from the data, so that question becomes a handoff. **[C][I]**

**The smallest handoff payload that lets a person act without making the customer start over** **[P]**: eight blocks,
fixed fields, not prose.

| # | Block | Plain-English content | Where it comes from |
|---|---|---|---|
| 1 | **Why the AI stopped** | One reason from a fixed list plus the rule that fired | Rule table, not the model |
| 2 | **What was promised, and by when** | The exact sentence the customer was shown, and the due time worked out from policy and the fixed clock (2026-10-16 in this dataset) | Policy table + configured date |
| 3 | **What the customer asked for** | Their own words, short, quoted | Conversation |
| 4 | **Who they are, and how sure we are** | Customer ID if matched, what identity check was done and its result, a callback number and window *the customer chose* | DB + conversation |
| 5 | **Verified facts** | Each fact with its source: record, field, value, time read; or KB file, passage, version date | DB reads; KB passage |
| 6 | **Claims, kept apart** | What the customer said that no source confirms ("the tech quoted me $89") | Conversation, labelled |
| 7 | **What the AI already did** | Answers given with their sources, tool calls and results, the booking attempt and its result | Tool log |
| 8 | **The open decision** | The one thing only a person can settle, plus a link to the full conversation | Rule + model wording |

Only blocks 3 and 8 need model-written wording. Blocks 1, 2, 5 and 7 can be assembled from state the system already holds,
which is the cheapest defence against a summary that drops or invents details (see the research in the
[handoff direction note](../analysis/2026-10-20-human-handoff-product-direction.md) §4 P3).

---

## 2. Method and coverage

### What was read and how

| What | How | Count |
|---|---|---|
| Transcripts | Every call parsed by script; index CSV checked against each file's header (ID, timestamp, agent, duration): 0 mismatches. All 420 are `Direction: Inbound`, 2026-07-06 to 2026-09-19. | 420 of 420 |
| Knowledge base | All 17 files read in full. The PDF with `pdftotext`; the PNG viewed as an image. | 17 of 17 |
| Scheduling DB | Opened read-only (`mode=ro`); schema, all five tables and the seeded customers checked. | 5 of 5 tables |
| Required project docs | `AGENTS.md`, `CLAUDE.md`, router, the three always-read rules, resume note, checklist, briefing, dataset README, `SCHEMA.md`, brief audit, handoff direction note. | all |

### How all 420 calls were classified

Three layers, in this order. The code is `docs/data/scripts/classify_calls.py`.

1. **Initial need.** Skip filler turns ("Can you hear me okay?", "Sorry, I'm driving", "my dog is barking"), take the
   first substantive customer turn, strip speech-to-text filler ("um", "uh") and match it to exactly one category by
   an ordered rule list. A call that matches no rule raises an error, so nothing was silently dropped: **0 unclassified**.
2. **Events.** Separately, a regex pass over the *agent's* lines records what the human said or did: read a balance,
   offered a slot, said "You're booked", sent a link, promised a callback and so on (32 event types).
3. **Emergent escalations.** A search of every customer turn *after* the opening request for dispute, refund, manager,
   legal or safety language, outside the escalation categories.

**Why this is trustworthy enough.** The two views were built independently and agree. The 37 categories (built from
the customer's words) produce 25 distinct agent-side event signatures (built from the agent's words), and every call carries
the signature expected for its category, with 0 exceptions beyond ordinary variants (for example, "waitlist offered" is
attached to booking calls where the customer asked for an earlier slot). Categories that share a signature differ only in
the customer's symptom (for example HVAC repair vs plumbing vs tune-up).

### Counting convention

- **One primary category per call.** Shares use **420** as the denominator and sum to 100%.
- **Second requests are counted separately as "mentions"**, never by changing the primary count. Eight kinds were found
  (§3.3). A call is **multi-request in the strict sense** when the customer makes a second request in a *different*
  family: 17 calls (4.0%): the 4 "two things" calls, 7 compressor-warranty calls that ask to schedule, and 6 repeat-repair
  calls that ask for a visit.
- **Initial need vs later escalation** are different questions. The first is the category. The second is the
  emergent search (layer 3), which found none.

### How examples were checked

I read **57 transcripts in full**: at least one for every one of the 37 categories, plus the unusual ones (the shortest
and longest calls, calls with two kinds of noise, the compressor calls, the "two things" calls, the 16 burning-smell calls
in detail, and the calls that first looked like exceptions to the rules and turned out to be regex misses on filler words).
The list is in §11.4. Every distinct agent-side script variant inside a category was compared; the remaining differences
are names, numbers, brand names, filler, line-item combinations and window labels.

### Near-duplicates

The 420 calls open with **109 distinct normalized lines** including noise. Removing the noise and the "I'd like to book a
repair / what's the soonest" wrappers leaves **46 opening templates**, which become the 37 categories, and **139 distinct
agent-side scripts** once names and numbers are removed. Seventeen templates have 12 or more calls. Consequences:

- Counts here show the generator's mix. Do not read "75 AC and furnace calls" as a rate in the real world.
- A random split of these calls into train and test would put near-copies on both sides (audit D-1). Any test set built
  from them should split by template.
- **92 calls (21.9%) contain one or more noise interjections**: "you cut out" (27), "I'm driving" (25), "can you hear me" (25) and "my dog
  is barking" (21). They carry no meaning and are ignored by classification.

### Limits of this evidence

1. **Transcripts record speech, not system actions.** "Moved" is something an agent said. Whether any record changed is
   not shown anywhere.
2. **Callers cannot be matched to the DB**, so I cannot check whether the agent's reading of an account was right.
3. **The classifier is mine.** It was built after reading exemplars, and it is valid for this templated corpus. It would
   not generalize to natural calls without being rebuilt.
4. **Timestamps are synthetic.** Calls on Sundays, on Labor Day and after 7pm exist (§10.2). I used call timestamps at face
   value only where I say so.
5. **"Current" means dated and not contradicted**, applying `source-authority.md` rule 4. Undated documents are labelled
   unknown.
6. **No outside source was used.** The research in the direction note is cited for context only.

---

## 3. Call-driver inventory

### 3.1 Families (denominator 420)

Ranking depends on grouping. For example, merging disputes and refunds into billing would make billing 91 calls (21.7%)
and second. This report does not choose the brief's "top 4 to 5 drivers"; that stays a Stage 2 decision for Innocent.

| Family | Calls | Share |
|---|---:|---:|
| F1 New service booking (HVAC repair, plumbing, tune-up, burning-smell visit) | 132 | 31.4% |
| F3 Billing information and payments | 67 | 16.0% |
| F5 Comfort Club membership | 57 | 13.6% |
| F6 Warranty | 45 | 10.7% |
| F2 Managing an existing appointment | 38 | 9.0% |
| F4 Billing disputes and refunds | 24 | 5.7% |
| F8 Service complaints | 16 | 3.8% |
| F10 Out of residential scope (commercial, hiring, wrong number) | 16 | 3.8% |
| F7 System-replacement estimate | 12 | 2.9% |
| F9 Safety | 9 | 2.1% |
| F11 Two-part request (booking + membership) | 4 | 1.0% |
| **Total** | **420** | **100%** |

### 3.2 Categories

**Confidence** = how sure I am that the category's *label* is right: **High** when the rule, the agent-side signature and a
full read agree; **Medium** when the label involves my interpretation. Outcomes are **[T]**: what the transcript shows
was said. Examples are call IDs without the `CALL-` prefix; the first was read in full. Each category's complete call list is in §11.3.

| Category | Definition | n | Share | Examples | Observed outcome [T] | Conf. |
|---|---|---:|---:|---|---|---|
| **SCH-HVAC** | Reports an HVAC fault and wants a visit: furnace won't start 19, blank thermostat 13, water at the indoor unit 16, AC runs but warm 11, grinding noise 9, AC not cooling 7 | 75 | 17.9% | 20260814-0003, 20260714-0178, 20260830-0269 | ID step, asks day and window, offers a slot, customer accepts, "You're booked", quotes $89 diagnostic "applied toward the repair", asks brand, promises morning-of text and 30-minute heads-up. 16 asked for an earlier slot and were offered a waitlist. | High |
| **SCH-PLUMB** | Wants a plumbing visit: sink backing up 18, water-heater pilot light 7 | 25 | 6.0% | 20260709-0365, 20260810-0088, 20260718-0360 | Same pattern as SCH-HVAC, same $89 diagnostic quote. 9 waitlist offers. | High |
| **SCH-TUNEUP** | Asks for the annual tune-up | 16 | 3.8% | 20260711-0109, 20260720-0371, 20260721-0110 | Same booking pattern, but the agent quotes the **$89 diagnostic fee**, never the $129 tune-up price or membership inclusion (16 of 16). 4 waitlist offers. | High |
| **SCH-BURNING** | Reports a burning smell from the vents and wants a visit | 16 | 3.8% | 20260706-0101, 20260706-0182, 20260916-0311 | Booked as an ordinary "non-emergency" visit in 16 of 16; no safety instruction; no breaker question (0 of 16 mention breakers). 5 waitlist offers. | **Medium**: the "safety-ambiguous" label is my judgement; the KB is silent |
| **SCH-RESCHED** | Has an appointment "tomorrow" and asks to move it | 15 | 3.6% | 20260902-0001, 20260711-0063, 20260725-0112 | Agent reads the appointment, offers a new day, says "Moved. New confirmation text is on its way." Fee never mentioned (0 of 15), though 14 of 15 are inside 24 hours **[C]**. | High |
| **SCH-CONFIRM** | Asks to confirm a visit "Thursday" | 8 | 1.9% | 20260710-0124, 20260730-0183, 20260805-0154 | Agent states day, window and purpose ("for a water heater inspection"). | High |
| **SCH-CANCEL** | Cancels because the problem was fixed another way | 6 | 1.4% | 20260707-0002, 20260724-0325, 20260726-0220 | "Since it's more than 24 hours out there's no cancellation fee. You're all set." The visit date is never stated, so the 24-hour claim cannot be checked. | High |
| **SCH-LATE** | Window has passed, "nobody's here and nobody's called" | 9 | 2.1% | 20260721-0261, 20260725-0355, 20260806-0284 | Agent says the previous job ran long, tech is "about 25 minutes out", "I'll have him call you directly", notes the account so the diagnostic fee is waived. | High |
| **BILL-BALANCE** | "What's my current balance?" | 15 | 3.6% | 20260708-0255, 20260710-0121, 20260715-0021 | Agent reads the open balance, invoice number and due date. All 15 customers then say they will pay "through the portal". | High |
| **BILL-PAY** | Wants to pay a named invoice over the phone | 14 | 3.3% | 20260708-0115, 20260709-0356, 20260717-0359 | "We don't take card numbers over the phone", then a secure payment link is texted. | High |
| **BILL-AUTOPAY** | Wants autopay for the membership | 14 | 3.3% | 20260709-0347, 20260710-0254, 20260713-0036 | Agent points to "the customer portal under Payment Methods" or sends a link ("expires in 24 hours"). | High |
| **BILL-EXPLAIN** | Got an invoice and "isn't sure what it's for" | 13 | 3.1% | 20260710-0373, 20260728-0193, 20260805-0244 | Agent names the visit date and the line items ("the diagnostic fee plus the refrigerant recharge"), then emails an itemized copy. | High |
| **BILL-DUP** | Thinks they were charged twice | 11 | 2.6% | 20260709-0129, 20260725-0288, 20260726-0331 | Agent "sees two authorizations", one a pending hold dropping in 3 to 5 business days; if still there after five, "we'll open a ticket with the processor". | High |
| **BILL-DISPUTE** | Says the tech quoted one price and the invoice is higher | 16 | 3.8% | 20260714-0246, 20260718-0111, 20260729-0278 | Agent compares "the quote and the invoice", names a fee "which wasn't on the verbal quote", customer says "Nobody told me", agent flags a billing supervisor, **one business day**. The gap is exactly $60 in 16 of 16 **[C]**. | High |
| **BILL-REFUND** | Demands a full refund for a repair that "didn't fix anything" | 8 | 1.9% | 20260710-0136, 20260715-0100, 20260812-0169 | "Refund requests go to our billing supervisor … I'll open a case", **two business days**. Customer: "I'd better." | High |
| **MEM-CANCEL** | Cancels the Comfort Club membership | 13 | 3.1% | 20260710-0364, 20260713-0287, 20260718-0349 | Agent says the plan is annual, no refund if a tune-up was used, "it won't renew". Customer: "just make sure it doesn't renew." "Done. Auto-renew is off." | High |
| **MEM-RENEW** | Got a renewal email, asks when it charges | 14 | 3.3% | 20260707-0096, 20260707-0392, 20260710-0135 | Agent reads the term end and "$189". Customer asks "can I still cancel before then?"; "any time before the renewal date". | High |
| **MEM-INCLUDE** | What does the membership include | 12 | 2.9% | 20260707-0148, 20260718-0045, 20260718-0060 | Plan benefits, then price, then "does it cover plumbing" (Plus only). All 12 end with "let me think about it". No account lookup. | High |
| **MEM-PRICE** | How much is the maintenance plan | 8 | 1.9% | 20260712-0104, 20260716-0006, 20260721-0108 | Agent quotes $189, $16.99 and $269 Plus. Customer: "I thought it was $149?"; agent: "that was the old pricing". | High |
| **MEM-UPGRADE** | Move from the regular plan to Plus mid-year | 6 | 1.4% | 20260713-0314, 20260714-0019, 20260803-0056 | Agent quotes a prorated amount ($36 to $72) and says "You're upgraded", sends a payment link. | High |
| **MEM-DISCOUNT** | A self-declared member asks about a discount on a new system | 4 | 1.0% | 20260713-0285, 20260727-0300, 20260730-0048 | "15 percent off repairs … flat $500 off [replacement] plus the extended labor warranty." Membership is a claim; nobody checks. | Medium (n = 4) |
| **WAR-CLAIM** | Install "from last year" stopped working | 14 | 3.3% | 20260711-0248, 20260712-0227, 20260714-0326 | "Since it's under a year, both parts and labor are covered", warranty diagnostic at no charge, slot offered and accepted. No "booked" confirmation is spoken. | High |
| **WAR-REPEAT** | Same repair fails again | 6 | 1.4% | 20260712-0007, 20260716-0317, 20260722-0064 | "1 year labor warranty on the same part. March is within that." Then "let me book that as a warranty recall." **No slot is named.** | High |
| **WAR-PARTS** | Compressor died in a "three year old" system | 7 | 1.7% | 20260709-0315, 20260719-0153, 20260720-0292 | Agent states install age, manufacturer parts cover "if registered, which yours is", labor billable, "$600 to $900". Customer: "Let's schedule it then." **Agent asks "anything else?"; no booking (7 of 7)** **[C]**. | High |
| **WAR-TRANSFER** | Bought a house; does the warranty transfer | 8 | 1.9% | 20260722-0161, 20260730-0346, 20260803-0086 | Manufacturer parts warranty may transfer once with a fee; "our labor warranty does not transfer"; looks up the install by address; emails the transfer form. | High |
| **WAR-REGISTER** | "Did you register my new unit with the manufacturer?" | 10 | 2.4% | 20260707-0053, 20260709-0010, 20260712-0195 | "We register every install within 30 days. I see it was registered on the [date]. I'll resend the confirmation." | High |
| **EST-REPLACE** | Old system; what would replacement cost | 12 | 2.9% | 20260709-0134, 20260810-0237, 20260711-0030 | Free in-home estimate, "ballpark" $8,000 to $16,000, an advisor slot offered and accepted. | High |
| **COMPLAINT-CONDUCT** | Asks for a manager: rude tech, mud through the house | 6 | 1.4% | 20260718-0062, 20260722-0198, 20260729-0041 | "Escalate this to our service manager. She'll call you back **today**." Customer: "Today. Not next week." "I've marked it urgent." | High |
| **COMPLAINT-OPINION** | A second opinion contradicts the recommended repair ($4,000 replacement vs a $200 capacitor) | 5 | 1.2% | 20260710-0335, 20260726-0189, 20260830-0286 | Same "service manager, today, urgent" script. | High |
| **COMPLAINT-REPEAT** | "I've called three times and nobody has called me back" | 5 | 1.2% | 20260724-0391, 20260730-0223, 20260730-0306 | Same script. The three earlier calls are not verifiable. | High |
| **SAF-GAS** | "I smell gas near my furnace" | 3 | 0.7% | 20260712-0046, 20260728-0264, 20260822-0185 | Instruction first: leave the house, call the gas utility or 911 from outside, don't flip switches. Then "call us back … emergency tech", "priority note on your account". | High |
| **SAF-CO** | Carbon monoxide detector alarming | 5 | 1.2% | 20260721-0093, 20260805-0290, 20260816-0038 | Same instruction and follow-up. | High |
| **SAF-SPARK** | Sparks from the outdoor unit | 1 | 0.2% | 20260717-0180 | Same instruction and follow-up. | High (n = 1) |
| **COMMERCIAL** | Quote for a strip center or rooftop units | 5 | 1.2% | 20260728-0089, 20260730-0396, 20260819-0228 | Redirected to the commercial division; name and phone taken; "an estimator" within one business day. | High |
| **HIRING** | Asks about HVAC technician jobs | 6 | 1.4% | 20260712-0067, 20260714-0366, 20260715-0351 | Careers page, no applications by phone, "I'll pass along that you called". | High |
| **WRONG-NO** | "Is this Meridian Dental?" | 5 | 1.2% | 20260813-0031, 20260820-0374, 20260904-0186 | "No, this is Meridian Home Comfort." Call ends in about 40 to 60 seconds. | High |
| **MULTI-REPAIR-PLAN** | "Two things": book an AC visit and ask whether the plan would save money | 4 | 1.0% | 20260710-0081, 20260724-0308, 20260917-0332 | Agent explains the plan waives the $89 and gives 15% off, "Want me to add it?", adds membership, books a slot. | High |
| | | **420** | **100%** | | | |

### 3.3 Second requests and the initial-vs-later question

**Initial need versus a later dispute, safety issue or escalation.** I searched every customer turn after the opening request,
in all 420 calls, for manager, supervisor, refund, gas, smell, carbon, sparks, smoke, fire, breaker, lawyer, chargeback,
dispute and "someone in charge" **[C, check C7]**. Outside the nine escalation-type categories there were **0 hits**. The only
later turn that resembles a switch is 14 membership-renewal callers asking "can I still cancel before then?", which is a question
about an option, and which agents answer with policy ("any time before the renewal date"). So:

- Escalation-type problems are **always the initial need** in this corpus (54 calls).
- **Not observed:** a routine call that becomes a dispute, a customer who asks for "a person" (0 of 420; 11 customers ask for a *manager* or "someone in charge"), a safety phrase mid-call, a legal threat or chargeback (0). These cases still have to be
  designed for, but with synthetic tests labelled as synthetic (`synthetic-test-data.md`).

**Second requests inside a call** (a call can have more than one; the primary count is unchanged):

| Second request | Mentions | Attaches to | What happened [T] |
|---|---:|---|---|
| Wants an earlier slot | 34 | Booking categories | "That's the earliest I have for a non-emergency", waitlist offered, customer says "do that. And book the slot" |
| Price question (membership cost; labor cost) | 19 | MEM-INCLUDE 12, WAR-PARTS 7 | Answered from the plan or a range ("$600 to $900") |
| Asks to schedule after a warranty answer | 17 | WAR-PARTS 7, WAR-REPEAT 6, MULTI 4 | MULTI booked (4), WAR-REPEAT "booked" with no slot (6), **WAR-PARTS ignored (7)** |
| "Nobody told me about that" | 16 | BILL-DISPUTE | The unverified claim behind every dispute |
| "Can I still cancel before then?" | 14 | MEM-RENEW | Answered: yes, before the renewal date |
| Wants an itemized copy by email | 13 | BILL-EXPLAIN | "Sending that to the email on file now" |
| "Does it cover plumbing?" | 12 | MEM-INCLUDE | Plus only |
| Customer cites the old $149 price | 8 | MEM-PRICE | "That was the old pricing" |

### 3.4 Topics checked and absent

A request type is listed only if the calls support it. I searched all customers' words for these plausible topics and found
**no calls (0 of 420)** for each: password, login or account access; financing; business hours; holiday hours; service
area or ZIP questions (including the towns the KB adds or excludes); duct cleaning; legal threats or chargebacks;
late-cancellation or no-show fee questions; diagnostic-fee questions; a customer who says the house is hot or cold or names
a vulnerable occupant; and a customer asking to be called back or left a voicemail. They are not categories here **[C, check C12]**.
(The KB covers several of these; the point is that callers did not ask.)

---

## 4. What the human agent did, by request type

"**Shows**" is **[T]**: spoken in the call. "**Infer**" is my reading and is marked as such. The last column is what no
transcript can show.

| Request type (n) | Looked up (shows) | Explained (shows) | Changed or did (said) | Promised or passed on (shows) | Cannot be shown / my inference |
|---|---|---|---|---|---|
| **New booking** (132) | "I see the account" after ID; availability ("I have a … window") | $89 diagnostic credited toward repair; brand asked; text morning-of and 30-minute heads-up | "You're booked" | Waitlist offered to 34. Nothing passed on. | Which slot was written; zone and member-slot rules; whether the customer was a member (never asked, 0 of 132). *Infer:* a scheduling tool was used |
| **Reschedule** (15) | Appointment: "I see the appointment tomorrow 8 to 12" | Nothing about fees | "Moved. New confirmation text is on its way." | Nothing | Whether the old slot was freed. $49 fee (14 of 15 within 24h) never raised |
| **Confirm / cancel** (8 / 6) | Day, window, purpose (confirm) | "More than 24 hours out, no cancellation fee" (cancel) | "You're all set" | Nothing | The cancelled visit's date; whether a slot was released |
| **Late technician** (9) | "The tech's previous job ran long … 25 minutes out" | Apology and an ETA | "I'm noting the account so the diagnostic fee is waived" | "I'll have him call you directly" (passed to the technician) | Any dispatch data. *Infer:* the ETA came from the agent's own source, which the issued materials do not contain |
| **Balance** (15) | "Open balance of $X on INV-… due on the Nth" | Nothing further | Nothing | Nothing | Whether the invoice exists (0 of 42 invoice numbers are in the DB) |
| **Pay / autopay** (14 / 14) | Nothing | "We don't take card numbers over the phone"; autopay is "in the customer portal under Payment Methods" | Payment link texted, "expires in 24 hours" | Nothing | A payment system. The portal is not described in any KB file |
| **Explain invoice** (13) | Visit date and line items | "The diagnostic fee plus the refrigerant recharge" | "Sending that to the email on file now" | Nothing | Whether the explanation matches the invoice. Diagnostic credit never discussed |
| **Duplicate charge** (11) | "I do see two authorizations" | Pending hold; 3 to 5 business days | Nothing | "If it's still there after five business days, call us back and we'll open a ticket with the processor" | Any card-processor data. The explanation matches `customer_faq.md` word for word |
| **Billing dispute** (16) | "I see the quote and the invoice" | The $60 gap is "the permit fee / after-hours rate / disposal fee which wasn't on the verbal quote" | Nothing | Billing supervisor callback, **1 business day** | Any quote record exists. No fee in the KB is $60 **[C]** |
| **Refund demand** (8) | Identity only | "Refund requests go to our billing supervisor" | "I'll open a case" | Callback in **2 business days** | A case record (none exists in the DB) |
| **Cancel membership** (13) | Nothing | "If you've already used a tune-up this term there's no refund … it won't renew" | "Done. Auto-renew is off", confirmation email | Nothing | An auto-renew field (none exists). Whether a tune-up was used was never looked up |
| **Renewal** (14) | "Your term ends on the Nth … renews at $189" | Cancel any time before the renewal date | Nothing | Nothing | Plan cadence, price paid and enrollment date (none in the DB). Every call quotes $189 |
| **Membership info** (24) | Nothing | Benefits, prices, plan differences, member discounts | Nothing | Nothing | Whether a "member" is one (4 self-declared) |
| **Upgrade** (6) | Nothing visible | "We prorate the difference … about $50 today" | "You're upgraded", payment link | Nothing | The months remaining the agent used. KB says the $80 difference is prorated for the months left |
| **Warranty claim / repeat** (14 / 6) | Install age; the March repair | "Under a year, parts and labor covered"; "1 year labor on the same part" | "I'll book a warranty diagnostic at no charge"; "book that as a warranty recall" | Nothing | Install date, prior repair (no completed visits exist in the DB), a confirmation |
| **Compressor** (7) | Install age; "registered, which yours is" | Part covered, labor billable, "$600 to $900" | **Nothing** after "Let's schedule it then" | Nothing | Registration status (no field). *Infer:* the scheduling request was dropped |
| **Transfer / registration** (8 / 10) | Install by address; "registered on the Nth" | Transfer rules; 30-day registration policy | Email the transfer form; "resend the confirmation" | Nothing | Any registration record (no field) |
| **Estimate** (12) | Nothing | Free estimate; $8,000 to $16,000 | Advisor slot "Saturday at 4pm" | Nothing | The slot is not in any DB window (estimate windows are 08:00-12:00, 12:00-16:00, 13:00-17:00) |
| **Complaint / manager** (16) | Identity only | Apology | "Marked it urgent" | Service manager **"today"** (passed to service manager) | Whether a manager exists or called back. KB says 1 business day |
| **Safety** (9) | Nothing; no identity at all | Leave the house; 911 or the gas utility from outside; don't flip switches | "Priority note on your account" | "Call us back and we'll get an emergency tech dispatched" | Which account. No dispatch exists in the DB |
| **Commercial / hiring / wrong number** (16) | Name and phone (commercial) | Department redirect; careers page | Nothing | Estimator within 1 business day (commercial); "pass along that you called" (hiring) | A hiring or estimator queue |
| **Two-part** (4) | Nothing | Plan saves the $89 and gives 15% off | Adds the membership; books a visit | Nothing | Whether the waiver applies to a plan joined the same day (no KB text says so) |

---

## 5. Source inventory

### 5.1 What exists in the issued materials

Status uses the five labels from the question. **Current** = dated and not contradicted by a newer source;
**outdated** = superseded; **contradictory** = disagrees with a current source; **internal-only** = marked not for
customers; **unknown** = undated or unverifiable.

| Source | What it contains | Needed by | Status and authority notes | Access limits |
|---|---|---|---|---|
| `faq/customer_faq.md` (updated 2026-03-02) | Phone hours, after-hours fee $149, windows, 24-hour cancel/reschedule rule and $49 fee, no-show, diagnostic $89 and credit rule, payment ("card numbers are never taken"), duplicate charges, service-area cities | Booking, reschedule, cancel, pay, duplicate charge, fee quoting | **Current.** Gaps: its after-hours line omits the member waiver (the PDF has it); its city list pre-dates `service_area.md`; no mention of a portal or autopay | Customer-facing |
| `faq/faq_old_copy.md` (undated) | Same topics with $79, $129, shorter hours | none (must not be used) | **Outdated and contradictory**: diag $79 vs $89, after-hours $129 vs $149 | Exclude from answers |
| `faq/troubleshooting_before_you_call.md` (undated) | Four quick-check lists; says agents should walk callers through them "before booking a non-emergency visit" | Booking | **Unknown date**, not contradicted. 0 of 132 booking calls use it | Customer-facing |
| `policies/escalation_and_safety.md` (Rev 2026-01, "Internal — Call Center") | Safety protocol; supervisor callback within 1 business day; department redirects; "what agents can resolve directly" | Every handoff type | **Current**, internal label. It is the owner of triggers and promises | Staff-facing; quote the *promise*, not the document |
| `policies/service_area.md` (updated 2026-04-01) | ZIP groups; adds Dripping Springs 78620 and Manor 78653; excludes Lakeway west of 620 | none observed (0 calls) | **Current** for coverage; disagrees with the DB zone map and with its own "Austin: 787xx (all)" | Customer-facing |
| `policies/holiday_hours_2026.png` | Holiday closures, $199 holiday dispatch fee | none observed (0 calls) | **Current**, image only. Six calls fall on Labor Day ("Emergency only") | Needs OCR with provenance to the image |
| `pricing/2026_fee_schedule.pdf` (effective 2026-01-01, "supersedes all prior") | Fees by tier, no-show ($89 / $0 / $0), discounts, membership prices | Booking, reschedule, membership | **Current. Highest authority for fees** | Customer-facing |
| `pricing/repair_price_book_2026.csv` | SKUs, low/high price, member-discount flag, notes | Estimates, compressor labor | **Current**; ranges only ("technician confirms") | Customer-facing |
| `services/service_catalog.md` (updated 2026-02-10) | Services, ranges, replacement $8,000 to $16,000, not offered | Estimates, tune-up, duct cleaning | **Current** | Customer-facing |
| `services/scheduling_guide.md` (Rev 2024-11) | 48-hour cancel rule, waitlist, same-day "overflow" slots, "always confirm gate code, pets, adult" | Booking | **Outdated and contradictory** (48h vs 24h). The **only** KB mention of a waitlist | Staff-facing |
| `services/technician_arrival_and_etas.md` (undated) | Late-tech procedure; agents may waive the diagnostic fee for delays over 30 minutes | Late technician | **Unknown date.** Duplicates a rule in the internal notes | Treat as internal-leaning |
| `services/duct_cleaning.md` | A "TODO" stub | none (0 calls) | **Incomplete** | — |
| `membership/comfort_club_overview.md` (effective 2026-01-01) | Plans, prices, billing, cancellation and refund rules, upgrade ($80 prorated), transfer | All membership calls | **Current** | Customer-facing |
| `archive/comfort_club_overview.md` | Old prices ($149, $12.99, $219), refund any time, transferable | none | **Outdated and contradictory.** 8 callers quote its $149 price | Exclude (DEC-4) |
| `archive/warranty_terms_2023.txt` | 90-day repair, 1-year install | none | **Outdated and contradictory** | Exclude (DEC-4) |
| `warranty/warranty_policy.md` (effective 2025-06-15) | 1-year repair labor on the same part; 2-year install labor (5 if a member *at install*); registration within 30 days; transfer rules | All warranty calls | **Current** | Customer-facing |
| `internal/agent_discretion_notes.md` | Agents may waive the $49 fee once a year, waive the diagnostic after a 30-minute delay, give a 10% courtesy discount; may not refund | Late tech, reschedule fee, disputes | **Internal-only** ("Do not read this document to customers") | Never quote to customers |
| DB `customers` | `customer_id`, `name`, `phone`, `email`, `service_address`, `city`, `zip`, `membership_tier`, `membership_renewal_date`, `system_brand`, `system_install_date` | Identity, tier, renewal, warranty, zone | **Exists.** 154 customers. One system per customer. No enrollment date, plan cadence, price, auto-renew flag, tune-up history or payment method | PII; role-limited |
| DB `appointments` | `appointment_id`, `slot_id`, `customer_id`, `issue_description`, `created_at`, `status`, `is_warranty_visit` | Confirm, reschedule, cancel, warranty visits | **Exists.** 159 rows, **all `scheduled`; no completed visit exists**. `created_at` is later than 2026-10-16 in 87 rows | PII |
| DB `appointment_slots` | `slot_id`, `slot_date`, `window`, `tech_id`, `zone`, `service_type`, `status` | Booking | **Exists.** Mon to Sat, 2026-10-16 to 2026-11-05. `16:00-19:00` only Tue/Thu | Write path needed |
| DB `invoices` | `invoice_id`, `customer_id`, `appointment_id`, `issued_date`, `due_date`, `amount_cents`, `balance_cents`, `line_items` | Balance, explain, dispute | **Exists.** 81 invoices, 26 open, 15 past due. **`appointment_id` is NULL in all 81.** No payment history | PII and money |
| DB `technicians` | `tech_id`, `name`, `skills`, `home_zone` (8 rows incl. two Comfort Advisors) | Booking | **Exists.** No schedule, location or ETA | Internal |
| `SCHEMA.md`, dataset `README.md` | Status values, zone map, expected behavior, "today is 2026-10-16" | Booking, dates | **Current** (issued) | — |

### 5.2 What the calls mention that does **not** exist in the issued materials

None of these appears in any KB file or DB table. Counts are calls where a human agent or customer relies on it **[T]**.

| Missing source or system | Used in | Calls | What it would hold |
|---|---|---:|---|
| Customer portal and autopay | BILL-AUTOPAY, BILL-BALANCE | 29 | Payment methods, autopay setting |
| Payment-link / messaging system | BILL-PAY, BILL-AUTOPAY, MEM-UPGRADE (also "confirmation text", "email on file") | 28 + 6 | A way to send a link or email |
| Card-processor records | BILL-DUP | 11 | Authorizations and posted charges |
| Auto-renew setting | MEM-CANCEL | 13 | A flag to switch off |
| Membership billing detail | MEM-RENEW, MEM-UPGRADE, MEM-CANCEL | 33 | Price paid, annual or monthly, enrollment date, tune-up used |
| Manufacturer-registration records | WAR-REGISTER, WAR-PARTS | 17 | Registration date per unit |
| Repair history | WAR-REPEAT | 6 | Past visits ("you fixed my blower in March") |
| Verbal-quote records | BILL-DISPUTE | 16 | What a tech quoted |
| Dispatch / ETA feed | SCH-LATE | 9 | Technician location and ETA |
| Case or callback log, account notes and flags | All 54 handoff calls | 54 | A place to put the case; "priority note on your account" |
| Waitlist | Booking categories | 34 | A cancellation waitlist |
| Emergency dispatch | SAF-* | 9 | "An emergency tech dispatched" |
| Staff roster and roles (billing supervisor, service manager, commercial estimator; Comfort Advisors do exist in `technicians`) | BILL-DISPUTE, BILL-REFUND, COMPLAINT-*, COMMERCIAL | 45 | Who exists, who is on shift |
| Careers inbox | HIRING | 6 | Where "I'll pass along that you called" goes |

### 5.3 Checks of what human agents said against the current sources

These are the reasons transcripts cannot be an answer key. "Differs" is **[C]** from the calls compared to **[I]**.

| # | What the calls show [T] | What the current source says [I] | Calls |
|---|---|---|---:|
| 1 | Reschedule "tomorrow"; fee never mentioned. 14 of 15 start inside 24 hours if the call timestamp is taken at face value | `faq/customer_faq.md`: inside 24 hours there is a $49 fee. `2026_fee_schedule.pdf`: $49 for every tier | 14 of 15 |
| 2 | Invoice $60 above the verbal quote, explained as a permit, after-hours or disposal fee | After-hours is $149; permit $85 to $185; disposal $75 to $150. No fee is $60 | 16 |
| 3 | Refund callback in "two business days" | `escalation_and_safety.md`: supervisor callback within 1 business day | 8 |
| 4 | Complaint callback "today" and "I've marked it urgent" | Same file: 1 business day; "Do not promise a specific outcome" | 16 |
| 5 | Warranty claim: "since it's under a year, both parts and labor are covered" | `warranty_policy.md`: install labor 2 years (5 if a member at install). The retired 2023 text says 1 year | 14 |
| 6 | Tune-up booked with "the diagnostic fee is $89 … applied toward the repair" | `service_catalog.md` and price book `HV-TUNE`: tune-up is $129 for non-members and included for members | 16 |
| 7 | Diagnostic fee quoted without asking about membership (0 of 132 mention it) | `2026_fee_schedule.pdf`: waived for members. DB: 56 of 154 customers are members | 132 |
| 8 | "No refund if you've already used a tune-up", not looked up; no mention of the 60-day prorated refund or the monthly-plan balance | `membership/comfort_club_overview.md` § Cancellation | 13 |
| 9 | Compressor: "installed N years ago" differs from the customer's own "three years" in 4 of 7 calls; "registered, which yours is" | `warranty_policy.md`; no registration field in the DB (audit K-10) | 7 |
| 10 | No breaker question before booking a "burning" smell | `escalation_and_safety.md`: "Electrical burning smell combined with tripped breakers" | 16 |
| 11 | "Call us back and we'll get an emergency tech dispatched"; caller never identified | Same file: "flag the account as priority emergency"; no dispatch is promised | 9 |
| 12 | Late tech: waiver promised, "I'll have him call you directly" | `technician_arrival_and_etas.md`: dispatch texts an ETA; reschedule at no charge *or* keep the visit with the fee waived | 9 |
| 13 | Booking offers whose label contradicts the hours ("morning window … 12 to 4") | `SCHEMA.md` windows: 08:00-12:00, 12:00-16:00, 13:00-17:00, 16:00-19:00 | 74 of 132 |
| 14 | 23 callers asked for 4 to 7pm after work; none was offered a 16:00-19:00 window | `SCHEMA.md`: that window exists only Tue/Thu | 23 |
| 15 | Advisor "Saturday at 4pm" | Estimate slots start 08:00, 12:00 or 13:00 | 12 |
| 16 | Duplicate-charge answer ("3 to 5 business days", "open a ticket with the processor") | `customer_faq.md` § Duplicate charges says the same | 11 (matches) |
| 17 | Caller cites the old $149 plan; agent says it changed | `membership/comfort_club_overview.md`: $189 | 8 (matches) |

---

## 6. Which requests are answerable, need a lookup, an action, a person, or are unsupported

These are **candidates by primary category**, based on what the issued KB and DB can support. They are **not** an approved
scope and not the brief's "top three". "Permitted action" refers to what `escalation_and_safety.md` lists human agents
as able to resolve directly (schedule, reschedule, cancel, confirm; explain invoice lines; send payment links; Comfort
Club enrollment, upgrades, renewal and cancelling auto-renew; warranty questions and warranty diagnostics). **Whether the AI
inherits any of those permissions is open (audit DEC-2).**

| Candidate level | Categories | Calls | Share | Needs |
|---|---|---:|---:|---|
| **A. Answerable from the current KB alone** | MEM-INCLUDE, MEM-PRICE, MEM-DISCOUNT, WAR-TRANSFER, HIRING, WRONG-NO | 43 | 10.2% | `membership/comfort_club_overview.md`, `2026_fee_schedule.pdf`, `warranty_policy.md`, `escalation_and_safety.md` (redirects). Any "I'm a member" claim stays unverified |
| **B. A database read plus the KB** | BILL-BALANCE, BILL-EXPLAIN, SCH-CONFIRM, MEM-RENEW, WAR-CLAIM, WAR-PARTS | 71 | 16.9% | `invoices`, `appointments`+`appointment_slots`, `customers` (tier, renewal date, brand, install date). **Identity first (audit DEC-3).** Email-a-copy, warranty-visit booking and any registration claim need more (see level F) |
| **C. A database write (a booking) plus the KB** | SCH-HVAC, SCH-PLUMB, SCH-TUNEUP, SCH-RESCHED, SCH-CANCEL, EST-REPLACE, MULTI-REPAIR-PLAN | 153 | 36.4% | `appointment_slots` (status, zone, service type, member-reserved), `appointments`, `customers.city`/`membership_tier`; the 24-hour fee rule; a fixed clock. Estimates use `estimate` slots |
| **D. A person, by policy** | BILL-DISPUTE, BILL-REFUND, COMPLAINT-CONDUCT, COMPLAINT-OPINION, COMPLAINT-REPEAT, COMMERCIAL, SCH-LATE | 54 | 12.9% | `escalation_and_safety.md` § Supervisor escalation and § Department redirects; `agent_discretion_notes.md` for what *only* a human may waive; `technician_arrival_and_etas.md` for late techs |
| **E. Safety protocol: instruction first, then flag** | SAF-GAS, SAF-CO, SAF-SPARK | 9 | 2.1% | `escalation_and_safety.md` § Immediate safety escalation. Deterministic; no lookup first |
| **F. Needs something the issued materials lack** | BILL-PAY, BILL-AUTOPAY, MEM-CANCEL, MEM-UPGRADE, BILL-DUP, WAR-REGISTER, WAR-REPEAT | 74 | 17.6% | Payment links, autopay, an auto-renew flag, processor records, registration records, repair history (§5.2). Honest options: simulate and label, hand off, or answer policy only |
| **G. Policy gap** | SCH-BURNING | 16 | 3.8% | The KB's burning-smell rule needs "tripped breakers"; callers did not mention breakers |
| | **Total** | **420** | **100%** | |

Level D also totals 54, the same number as the escalation-type calls in §1, by coincidence: level D swaps the 9 safety
calls (level E) for the 9 late-technician calls.

**Two cautions on reading this table.**
- A + B + C = 267 calls (63.6%) are the calls whose *topic* the supplied sources could support. That is a ceiling on scope,
  **not a containment estimate**: it ignores identity checks, answer accuracy and the calls (in A to C) where the transcript
  shows a human skipping a rule the AI would have to apply (the reschedule fee, the member check).
- Level F is the most important surprise. Those calls look routine ("send me a payment link") and a human did them in
  under two minutes, but nothing in the issued materials can do the action. Treating them as "answerable" would produce
  confident wrong confirmations.

**Calls inside level C that carry a hidden handoff.** The 15 reschedules need the $49 rule, and a customer who says "I can't
pay that" is then in the dispute path. In 34 booking calls the customer wanted something earlier than offered, and the only
mention of a waitlist is in the outdated scheduling guide.

---

## 7. Handoff information matrix

One row per meaningful handoff type, grounded in the transcripts. Counts are the primary-category calls. "Verified" always
names a source; if the source does not exist for these callers, the cell says so. Promises come from the KB, never from
the model. **[P]** applies to the "what should reach the rep" content as a whole; the triggers and promises are **[I]**.

| Handoff type (n) | Trigger [I] | Customer request [T] | Verified facts and exact sources | Unverified claims | AI actions and tool outputs to carry | Promise or next step | What the rep must decide |
|---|---|---|---|---|---|---|---|
| **H1 Safety** (9) | `escalation_and_safety.md` § Immediate safety escalation: gas or rotten eggs, CO alarm, sparks/smoke/flames, burning smell *with tripped breakers* | "My carbon monoxide detector is going off" (all in the first sentence) | Which rule bullet matched, the exact words, the time. A customer record only if the caller later identifies | That the hazard is real and continuing; that they are outside | The instruction text and the turn it appeared in; no lookup, booking or troubleshooting before it | KB: tell them to leave and call 911 or the gas utility, then "flag the account as priority emergency". No dispatch promise in the KB (the humans promised one) | Whether to contact, dispatch, and confirm the caller is safe |
| **H2 Billing dispute** (16) | § Supervisor escalation: "billing disputes where the customer disagrees with an invoice amount" | Quote $X vs invoice $X + $60, "not what I agreed to" | Invoice: `invoices.invoice_id`, `amount_cents`, `balance_cents`, `line_items`, `issued_date`; fee lines in `2026_fee_schedule.pdf` and `repair_price_book_2026.csv`; the diagnostic-credit rule in `customer_faq.md` § Fees. **The transcripts' invoice IDs are absent from the DB; when testing against the DB, INV-204411 (customer MHC-10002) is the case of this shape** | What the tech quoted ("$89"); "nobody told me about that" | Lines read aloud and the KB lines cited; no adjustment offered; no adjudication | KB: callback within 1 business day; do not promise an outcome | Is the invoice right, does the diagnostic credit apply (45 of 81 invoices bill it beside a repair), any discretionary adjustment |
| **H3 Refund** (8) | § Supervisor escalation: "refund requests of any amount" | "Full refund on the repair; it didn't fix anything and I had to call another company" | The repair invoice and visit; `warranty_policy.md` repair-labor terms; `agent_discretion_notes.md` (agents may not refund) | That the repair failed; that another company was hired and at what cost | The refund request recorded; no promise of any outcome | KB: 1 business day (humans said 2) | Refund yes or no and how much; or a warranty recall instead |
| **H4 Service complaint** (16) | § Supervisor escalation: conduct or workmanship complaints, requests for a manager | Rude tech and mud (6); a $4,000 replacement vs a $200 capacitor (5); "called three times, nobody called back" (5) | The visit and technician from `appointments`/`technicians` when matched. **A record of earlier calls does not exist in the issued DB** | Everything about conduct, the second opinion and the earlier calls | Verbatim complaint; urgency from rule | KB: 1 business day (humans said "today", "urgent") | Whether and how to remedy; whether to review the technician's recommendation |
| **H5 Commercial redirect** (5) | § Department redirects: commercial projects | "12-unit strip center … four rooftop units" | None needed beyond the redirect | The property and scope as described | Name, number and scope captured | KB: estimator callback within 1 business day | Meridian Commercial estimates |
| **H6 Late technician** (9) | `technician_arrival_and_etas.md`: the tech will miss the window | "My window was 12 to 4 and it's 4:30" | The appointment window from `appointments`+`appointment_slots`; the fee rule (waiver over 30 minutes) | The tech's location and ETA (no feed exists) | Apology; the KB options: reschedule at no charge or keep the visit with the fee waived | KB: dispatch texts an updated ETA | Actual ETA; waiver (a staff discretion today); reassign |
| **H7 Burning smell** (16) | **None in the KB** (policy gap) | "I smell something burning from the vents" | The rule text and the fact that no breaker information was collected | Whether breakers tripped; whether it is electrical | Whether the one clarifying question was asked and answered | Depends on Innocent's decision (§10.4, D2) | Dispatch priority; call back; treat as safety |
| **H8 Action the system cannot perform** (74) | The request needs a payment link, autopay, an auto-renew switch, a processor ticket, a registration record or repair history (§5.2) | "I want to set up autopay"; "cancel my membership"; "did you register my unit" | What *was* read (for example the balance, `customers.membership_renewal_date`) | Anything the customer asserts about prior payments or visits | What the AI said it could and could not do; no confirmation of an action that did not happen | A staff action with an honest expectation; no card data requested | Perform the action in the real system; confirm to the customer |
| **H9 Booking cannot be completed or customer wants earlier** (34 asked; 0 failed) | No slot matches, or the caller wants earlier | "Can you do anything earlier?" | `appointment_slots` rows searched; `customers.city` → zone | The caller's urgency (no indoor temperature collected) | The search criteria and result, what was offered, any write attempted | No waitlist exists in the data; the outdated guide mentions one | Whether to expedite; the urgency class (§10.4, D2) |
| **H10 Not observed** | Customer asks for "a person" (0), identity mismatch (0), AI error or low confidence (n/a), question not in the KB (0) | — | — | — | — | — | Needed by the design anyway; test with synthetic, labelled cases |

**Notes on the matrix**
- Four things are missing from every transcripted handoff and a rep would need them: **a callback number the customer
  chose, a callback window, a reference the customer can quote, and an owner.** The KB asks for the window; no call
  collects it.
- **Identity and callbacks.** In 22 of the 54 handoff calls a number was spoken. For the rest the rep would use the
  number in the customer record, which the customer never confirmed, so the payload should say whether the number was
  *customer-supplied in this conversation* or *read from the record*.
- Rows H2 to H4 are the three places where the humans' promised timing differs from the KB. A reviewer who tries a dispute
  will see whichever promise the system makes; the payload should carry the promise as a stored value, not re-derive it.

---

## 8. When the rep should see a saved snapshot, a live link, or both

**The principle in plain English.** A **snapshot** answers "what did the AI see and say at that moment?", which a rep
needs to judge what the customer was told and to catch an AI error. A **link** answers "what is true now?", which a rep
needs before acting. A record that can change after the handoff, and that the rep might change, needs **both**, shown side
by side with a visible "changed since" marker. A statement the customer already heard needs a **snapshot only**.

| Source type | Snapshot of what the AI saw | Link to the current record | Why | Access and copy limits |
|---|---|---|---|---|
| **Conversation** | **Yes, immutable** | Link to the stored transcript | It is the record of what was said and promised | Staff role; redact card-like numbers; the summary never replaces it |
| **Invoice** (`invoices`) | **Yes**: the fields the AI read and quoted (`invoice_id`, `line_items`, `amount_cents`, `balance_cents`, due date) with the read time | **Yes** | In a dispute the rep must know what the customer was told *and* see today's balance, which may have changed | Billing role. Copy only the invoice involved, not the customer's other invoices. Keep amounts in cents with a display format |
| **Appointment and slot** (`appointments`, `appointment_slots`) | **Yes**: what was offered, the write attempted and its result, including failures with the reason | **Yes** | The slot can be reassigned or cancelled after the chat; the write is also what the rep might undo | Scheduling role |
| **Customer record** (`customers`) | **Minimal**: only the facts the answer used (tier, renewal date, brand, install date), with read time | **Yes, the default** | Name, phone, email and address change and are sensitive; copying them multiplies PII | Staff role plus identity status. Do not copy address or email into a case body; carry the ID |
| **Policy passage** (KB) | **Yes**: exact passage text, file, version marker (date or "Rev"), a content hash, and a passage ID | **Yes** | The AI's answer and promise depend on that version. If the policy changes later, the rep must see both | Never link `archive/` or `faq_old_copy.md` as authority. Mark `internal/` and `policies/escalation_and_safety.md` as staff-only and never put their text in a customer message |
| **Fee schedule PDF, price book CSV, holiday PNG** | **Yes**: the extracted value with its location (page, row, or image) | Yes, to the original | The extraction (especially OCR of the PNG) is where errors enter | Customer-facing documents |
| **Tool results** (availability search, booking write) | **Yes** | No (ephemeral) | Reproduces what the AI saw. Link instead to the record it created | Staff role |
| **The promise** (timing, owner) | **Yes**: exact sentence, the policy row it came from, the due time worked out from the fixed clock | No | The customer heard it. It must match the policy table (research item P5) | — |
| **Safety instruction** | **Yes**: exact text, the phrase that triggered it, the turn and time | No | Proves the instruction was given first | — |
| **Customer claims** | **Yes**, as short quotes tagged "unverified" | No | They are statements, not records | Keep them apart from verified facts |

**Do not show or copy unless the rep needs it:** card numbers (the system should never collect them; patterns in logs
should be redacted), the internal discretion text in anything customer-facing, other customers' records, full address,
email and phone beyond the callback contact, and an AI-written paragraph that stands in for the facts.

**Two more constraints from the data.**
- Identity today is "name and phone" or "account number and name", with no check against a record. The payload
  should say **what was asserted, what was matched, and what was not**, so a rep does not disclose account details on a
  callback to an unverified person (audit DEC-3).
- A snapshot should store the **fixed clock the system used** (2026-10-16 in this dataset), so the 24-hour rule and due times can
  be re-derived later.

---

## 9. Worked handoff examples

Each example uses call IDs from the corpus and cites the source location. Personal details are omitted. The "what the rep
needs" lists are **[P]**; the quotes and facts are **[T]** and **[I]**.

### E1 Billing dispute: `CALL-20260714-0246` (BILL-DISPUTE)

- **Customer words [T]:** the tech quoted $89, the invoice says $149, "that's not what I agreed to." Later: "Nobody told me
  about that."
- **What the human did [T]:** asked for name and phone, said "I see the quote and the invoice", attributed the $60 gap to
  "the after-hours rate which wasn't on the verbal quote", flagged a billing supervisor, promised a callback within one business day.
- **Check [C]:** the gap is $60. After-hours in `2026_fee_schedule.pdf` and the price book is **$149**, not $60. The
  agent's explanation does not reconcile, and no quote record exists in the issued systems.
- **Verified for a rep [P]:** the invoice record (`invoices` fields above) and the fee lines, each with source and read time.
- **Unverified:** the quote of $89; "nobody told me". **AI did:** read lines, cited fee schedule, made no adjustment.
- **Promise:** one business day (KB). **Decision left:** whether the invoice is right; whether a credit applies.

### E2 Refund request: `CALL-20260710-0136` (BILL-REFUND)

- **Customer words [T]:** "I want a full refund on the repair. It didn't fix anything and I had to call another company."
- **Human [T]:** "Refund requests go to our billing supervisor … I'll open a case and you'll hear back within two business days." Customer: "I'd better."
- **Checks:** KB says one business day, and `agent_discretion_notes.md` says agents "may NOT issue refunds of any kind."
  The "case" the agent says it opened has no table in the DB.
- **Rep needs [P]:** the repair invoice and visit; the repair-labor warranty text (`warranty_policy.md`, 1 year on the same part) so a warranty recall can be weighed;
  the claim that the repair failed, kept as a claim; the promised timing from the policy table. **Decision:** refund, partial refund,
  warranty recall or none.

### E3 Booking-related issue (a): `CALL-20260719-0153` (WAR-PARTS), asks to schedule and nothing happens

- **Customer words [T]:** "My Goodman compressor died and the system is only three years old. Is that under warranty?"
  Later: "Okay. Let's schedule it then."
- **Human [T]:** states "installed 4 years ago" (the customer said three), parts covered "if registered, which yours is",
  "labor would be billable", "$600 to $900". After the scheduling request: "Anything else I can do for you?" **No booking
  step in 7 of 7 compressor calls [C].**
- **Verified for a rep [P]:** `customers.system_brand`, `customers.system_install_date`, tier, `warranty_policy.md` (parts 10 years if registered; labor 2 years).
  **Not verifiable:** registration (no field), the customer's age claim vs the record.
- **The handoff exists because a request was dropped.** A rep needs the request itself ("book a compressor repair"),
  the coverage answer given and its source, and the open decision: whether the visit is billable.

### E3 Booking-related issue (b): `CALL-20260902-0001` (SCH-RESCHED), a fee nobody mentioned

- **Customer words [T]:** a tech is coming tomorrow, "something came up", can it move.
- **Human [T]:** read the appointment ("tomorrow 8 to 12"), moved it to Friday 8 to 12, "New confirmation text is on its way."
- **Check [C]:** the call is at 10:37 on 2026-09-02; the window starts at 08:00 the next day, about **21.4 hours** later. `customer_faq.md`
  and `2026_fee_schedule.pdf` set a **$49** fee inside 24 hours for every tier. It was not mentioned. (Timestamp taken at face value.)
- **Why it matters for handoff:** an AI that states the fee may be told "I won't pay that". The waiver is a human discretion
  (`agent_discretion_notes.md`: once per customer per year with a documented reason). So the handoff needs the appointment
  (snapshot and link), the hours-before calculation and the clock used, and the fee wording shown.

### E4 Safety: `CALL-20260721-0093` (SAF-CO)

- **Customer words [T]:** "My carbon monoxide detector is going off." (First sentence.)
- **Human [T]:** instruction first: leave, call 911 or the gas utility from outside, don't flip switches. Customer: "Okay, we're going outside."
  Then: "Once it's safe, call us back and we'll get an emergency tech dispatched. I'm putting a priority note on your account now."
- **Checks:** matches the KB protocol. But **no identity was taken (0 of 9 safety calls)**, so the note has no account, and
  "emergency tech dispatched" is not in the KB or any table.
- **Rep needs [P]:** the trigger phrase and rule bullet, the exact instruction and time, any contact the caller
  *volunteered after* the instruction, and a clear note that nothing was looked up. **Decision:** whether to follow up and how.
  *Design note:* the instruction must not wait for identity.

### E5 Safety-ambiguous: `CALL-20260706-0182` (SCH-BURNING)

- **Customer words [T]:** "I smell something burning from the vents" and wants a visit.
- **Human [T]:** booked it as "the earliest I have for a non-emergency", waitlist offered; no breaker question.
- **Check [C][I]:** 0 of 16 burning-smell calls mention breakers; the KB rule is "electrical burning smell combined with tripped breakers."
- **Rep needs [P]** if this became a handoff: the words, whether the breaker question was asked and the answer, whether any
  instruction was given. **Decision (Innocent):** see §10.4, D2. This is a policy gap; no transcript shows harm.

### E6 Complaint with unverifiable history: `CALL-20260724-0391` (COMPLAINT-REPEAT)

- **Customer words [T]:** "I've called three times about the same problem and nobody has called me back. I'm done."
- **Human [T]:** "escalate this to our service manager. She'll call you back today … I've marked it urgent."
- **Checks:** no repeated account or phone appears anywhere in the corpus, and the DB holds no call history, so "three times" can neither
  be confirmed nor denied. KB: one business day.
- **Rep needs [P]:** the quote of the complaint, the promised timing from policy, which problem it concerns (the AI may not know),
  and a note that earlier contacts are not recorded. **Decision:** who calls, and by when.

### E7 Action the system cannot perform: `CALL-20260710-0364` (MEM-CANCEL)

- **Customer words [T]:** cancel the Comfort Club membership. "Just make sure it doesn't renew."
- **Human [T]:** warned about no refund after a used tune-up, then "Done. Auto-renew is off and you'll get a confirmation email."
- **Check [I]:** `customers` has `membership_tier` and `membership_renewal_date` only. There is no auto-renew field and no email
  system. The KB lists "cancelling auto-renew" as something agents can do, but the issued materials give no way to do it.
- **Rep needs [P] if handed off:** the request, the renewal date read from the record (verified, with read time), what the AI
  told the customer, and the one-line instruction to perform the cancellation in the real system. **No refund promise.**

### E8 Late technician: `CALL-20260721-0261` (SCH-LATE)

- **Customer words [T]:** "My window was 12 to 4 and it's 4:30. Nobody's here and nobody's called."
- **Human [T]:** "The tech's previous job ran long, he's about 25 minutes out, I'll have him call you directly … the diagnostic fee is waived for the delay."
- **Checks:** the 25-minute ETA has no source in the issued materials. `technician_arrival_and_etas.md` says dispatch texts an
  ETA and offers reschedule at no charge or the fee waived; the waiver is documented there and in the internal notes (DEC-2).
- **Rep needs [P]:** the appointment from `appointments`+`appointment_slots` (snapshot and link), the minutes past the window and the
  clock used, the customer's request ("should I wait?"), and the two KB options. **Decision:** ETA, waiver, reassign.

---

## 10. Gaps and decisions

### 10.1 Missing systems and records (what a handoff cannot rely on)

Case or callback store; owner and status; account notes and flags; payment, autopay, link and email systems; processor
records; auto-renew flag; membership billing detail; registration records; repair and call history; quote records;
dispatch feed; waitlist; staff roster and shift. All are in §5.2. **Any handoff record is new state outside the issued data.**

### 10.2 Contradictions and data oddities worth knowing

- **Sources:** KB conflicts K-1…K-18 are in the [brief audit](../analysis/2026-10-20-brief-audit.md) §3. New for this work:
  `technician_arrival_and_etas.md` (undated) repeats the waiver rule that also sits in the internal-only notes; and no KB
  file describes a portal or autopay although 29 calls depend on one.
- **Transcripts vs sources:** §5.3 (17 rows).
- **DB:** `invoices.appointment_id` NULL in all 81 rows; 45 of 45 diagnostic invoices lack a credit line (**[I]** FAQ says
  credited when the repair is approved the same visit); `appointments` has no completed visit; 87 of 159 `created_at` values
  are later than the configured "today"; INV-204411's after-hours line is $144 vs the $149 fee (audit D-8).
- **Call timing:** 66 calls are on a Sunday (`customer_faq.md`: closed Sunday), 13 are after 7pm, 13 are on Saturday outside
  8 to 4, and 6 are on Labor Day 2026-09-07 when `holiday_hours_2026.png` says "Emergency only" **[C]**. The timestamps look
  synthetic, so they do not show how the real operation behaves; they do mean "one business day" cannot be computed
  from them without a stated clock and calendar.
- **Corrections to our earlier analysis (not edited; recorded here):** the direction note's "identity is checked by name
  and phone in about 256 calls" does not reproduce. Measured: an identity step in **363** calls, by method
  *account number + name* 131, *name + service address* 107, *name + phone* 125, and none in 57 (all explained: membership
  info, safety, hiring, wrong number, commercial, warranty transfer). The audit's "~40 mention a manager or supervisor"
  matches the 40 calls where an *agent* line names one; **11** customers ask for a manager or "someone in charge." The audit's
  "~21 refund" is consistent with 8 refund demands plus 13 membership cancellations where the agent says "no refund." Nothing here invalidates the audit or
  the direction note; the 54-call, no-live-transfer, three-promises and no-reference-number findings **reproduce exactly**.

### 10.3 Uncertain classifications

| Category | Why uncertain | Effect if wrong |
|---|---|---|
| SCH-BURNING (16) | "Safety-ambiguous" is my label; KB silent | Moves 16 calls (3.8%) between booking and a handoff type |
| SCH-LATE (9) | A service failure with a tech callback and a fee waiver, not a supervisor escalation | Counted in F2 and in "person required" (level D) because the waiver is staff discretion |
| WAR-REPEAT, WAR-CLAIM (20) | Counted as warranty; each also includes a booking | Booking-side share rises by up to 20 (4.8%) |
| WAR-PARTS (7) | Warranty question plus a dropped scheduling request | Strict multi-request count (17) would be 10 without it |
| BILL-DUP (11) | Could be read as a dispute; humans treated it as information | Level F vs D |
| COMMERCIAL, HIRING (11) | Redirects, not escalations to a supervisor | A handoff row but no case record |
| MEM-DISCOUNT (4) | Membership is a self-declared claim | Level A assumes the claim is not acted on |

### 10.4 Decisions for Innocent

> **All six were decided by Innocent on 2026-10-20.** The questions below are kept as they were asked, for history.
> Each heading carries its status. The live record is the [consolidated direction §11](../analysis/2026-10-20-human-handoff-consolidated-direction.md).

These are proposals. None is approved.

**D1. Which callback promise does the system make?** *(Status 2026-10-20: decided. One business day when nobody is online; refund requests get a representative within 2 business days (a response, not a refund); complaints and disputes keep one business day; the role is always "a representative"; safety gets no follow-up time; the emergency number and a P1 case only when the customer says someone is in danger from no heat, no cooling or a leak (Stage 2 check, WP-3). See [consolidated direction §8 OD-4](../analysis/2026-10-20-human-handoff-consolidated-direction.md).)*
*The story.* Human agents promised three different things for the same kind of escalation: one business day for 16 invoice
disputes, two business days for 8 refunds, and "today, marked urgent" for 16 complaints. The KB says one business day for all
of them and "do not promise a specific outcome." If the AI invents a faster promise, the customer expects a call a
business may not make; if it copies the humans, it breaks the KB.
*Options.* (A) **The KB's one business day for all**, stored in a policy table and shown verbatim. Consistent; the "today"
customers hear a longer wait than they did. (B) Keep type-specific promises. Closer to what callers heard; contradicts
the KB and needs a policy owner. (C) One business day, with complaints flagged "urgent" internally only. Honest to the customer, urgent for staff.
*Recommended: A (or C).* It is the only wording the issued policy supports.
**Decision needed:** Which promise does the system state for disputes, refunds and complaints: A, B or C?

**D2. Burning smell without a breaker mention: what should happen?** *(Status 2026-10-20, Innocent: decided as direction. Ask whether breakers have already tripped and whether there is smoke, sparks or flames; give the safety instruction if yes; take a cautious escalation path if unclear; book only when ruled out. A proposed handling of a policy gap. See [consolidated direction §9 and §11](../analysis/2026-10-20-human-handoff-consolidated-direction.md).)*
*The story.* 16 callers report a burning smell from the vents; human agents booked every one as routine, never asking about
breakers. The KB's rule only fires for "burning smell combined with tripped breakers."
*Options.* (A) Ask the one breaker question, and give the safety instruction if tripped; otherwise book as urgent. Matches
the KB wording; adds a turn. (B) Always give the safety instruction. Safest; may send safe callers outside. (C) Book as
routine, as the humans did. Fastest; the riskiest if the smell is electrical.
*Recommended: A.* It follows the KB's own condition. **Decision needed:** For a burning smell with no breaker information, A, B or C?

**D3. Reschedule inside 24 hours: does the AI state the $49 fee or hand off?** *(Status 2026-10-20, Innocent: decided, option A, **revised at Stage 3 the same day**: the AI explains the $49 fee but never makes a fee-bearing change; it sends a staff change request and the original appointment stays; a contested fee goes to staff; the AI never waives. Same decision as audit DEC-2. See [consolidated direction §9 and §11](../analysis/2026-10-20-human-handoff-consolidated-direction.md).)*
*The story.* 14 of 15 reschedule callers were inside the 24-hour window and no human mentioned the fee. The KB sets $49 for every tier;
waiving it is human discretion (`agent_discretion_notes.md`). This is the same question as audit DEC-2.
*Options.* (A) State the fee and hand off any waiver request. Policy-correct; some friction. (B) State the fee and let
the AI waive once per customer per year. Matches the notes; gives money away on a model's say-so. (C) Reschedule without mentioning it, as the humans did. Smoothest; conflicts with the FAQ and fee schedule.
*Recommended: A.* **Decision needed:** Inside 24 hours, does the AI state the fee and hand off waivers (A), waive itself (B) or stay silent (C)?

**D4. Actions the issued systems cannot perform (payment links, autopay, auto-renew, upgrade payment).** *(Status 2026-10-20, Innocent: decided. Serious cases get human priority; questions are answered within limits; unfinished tasks get a case; the full request list with wording and priority is in §9.4. See [consolidated direction §9 and §11](../analysis/2026-10-20-human-handoff-consolidated-direction.md).)*
*The story.* 74 calls were finished by a human using systems we do not have. The brief expects a working demo and also
forbids confident wrong answers.
*Options.* (A) Simulate each action with a visible "simulated" label (the audit already says "sending a payment link can only be simulated").
Demo flows; adds scope and a label to maintain. (B) Hand all of them off honestly. Simplest; lowers what the demo can do. (C) A thin stub store for these few actions, labelled.
Middle path; new state to build and defend.
*Recommended: B for the first slice, with A for payment links if time allows.* **Decision needed:** For actions with no real system behind them, A, B or C?

**D5. Safety before identity: how do we get contact details?** *(Status 2026-10-20, Innocent: decided, option A. Instruction first, contact offered after, priority case even with no match. See [consolidated direction §9 and §11](../analysis/2026-10-20-human-handoff-consolidated-direction.md).)*
*The story.* All nine safety callers were told to leave and were never identified, so the "priority note" has no account.
*Options.* (A) Instruction first, then offer to take a callback number *after*, never as a gate. (B) Instruction only, no follow-up capture. (C) Ask for identity first (rejected: delays the instruction; audit E-3).
*Recommended: A.* **Decision needed:** After the safety instruction, do we offer to capture a number (A) or not (B)?

**D6. Snapshot retention.** *(Status 2026-10-20, Innocent: decided. Full chat history in staff views; minimal snapshots of the fields the AI used, deleted 90 days after the case closes (Claude's recommendation, delegated by Innocent). See [consolidated direction §9 and §11](../analysis/2026-10-20-human-handoff-consolidated-direction.md).)* The case view needs saved copies of what the AI read (invoice lines, policy text). That creates a stored copy of customer data and
policy text. (A) Store the minimal fields and passage text with a retention limit and a "changed since" marker. (B) Store references only. Smaller exposure; the rep cannot see what the customer was told if the record changes.
*Recommended: A with minimal fields.* **Decision needed:** Do we store snapshots (A) or links only (B)?

**Already open elsewhere (not repeated):** the identity method (DEC-3), fee waivers (DEC-2), scheduling scope (DEC-1) and whether
the prototype has a staff view or live takeover ([handoff direction note](../analysis/2026-10-20-human-handoff-product-direction.md) §11).
**Not decided here:** which families become the brief's top 4 to 5 drivers.

---

## 11. Audit trail

### 11.1 Reproduce

```
cd inno-aea-callcenter/docs/data/scripts
python3 -I classify_calls.py          # writes ../handoff-inventory-call-map.csv; prints families, support levels, events
python3 -I checks_handoff_inventory.py # prints every other number in this report (checks C1 to C12)
```

Both scripts are read-only on `docs/data/issued/meridian_dataset/` (the SQLite file is opened `mode=ro`). The per-call table is
`docs/data/handoff-inventory-call-map.csv` (420 rows: ID, family, category, support level, second requests, events, flags, noise, template).

### 11.2 Calculations

- **Shares** = category count ÷ 420, one decimal. Families sum the categories in §3.1; sums are 420.
- **Escalation-type calls (54)** = 9 safety (3+5+1) + 16 dispute + 8 refund + 16 complaint (6+5+5) + 5 commercial.
- **Strict multi-request (17)** = 4 MULTI + 7 WAR-PARTS + 6 WAR-REPEAT.
- **Candidate levels (§6)** = sums of §3.2 counts: A 12+8+4+8+6+5 = 43; B 15+13+8+14+14+7 = 71; C 75+25+16+15+6+12+4 = 153;
  D 16+8+6+5+5+5+9 = 54; E 9; F 14+14+13+6+11+10+6 = 74; G 16; total 420. A+B+C = 267 = 63.6%.
- **Phone spoken in handoff calls (22 of 54)** = dispute 7/16, refund 4/8, complaint 6/16, commercial 5/5, safety 0/9.
- **Reschedule hours (C5):** hours between the call timestamp and 08:00, 12:00, 13:00 or 16:00 the next day, by the window the agent names.
- **Dispute gap (C4):** invoice amount minus quoted amount, from the customer's sentence; 16 of 16 equal $60.
- **Identity matches (C2):** every `MHC-` number, phone and `INV-` number in any transcript tested against `customers.customer_id`, `customers.phone` and `invoices.invoice_id`.

### 11.3 Category to call-ID mapping

IDs are shown without the `CALL-` prefix. Source: `handoff-inventory-call-map.csv`, column `initial`.

- **SCH-HVAC** (75): 20260707-0170, 20260709-0103, 20260711-0380, 20260713-0320, 20260714-0178, 20260715-0061, 20260716-0020, 20260716-0107, 20260716-0240, 20260716-0367, 20260718-0319, 20260720-0157, 20260720-0279, 20260721-0242, 20260721-0333, 20260723-0172, 20260725-0293, 20260725-0378, 20260726-0141, 20260728-0050, 20260728-0094, 20260728-0281, 20260730-0372, 20260731-0047, 20260801-0334, 20260807-0011, 20260807-0401, 20260808-0159, 20260808-0322, 20260809-0117, 20260810-0210, 20260810-0296, 20260810-0414, 20260812-0302, 20260813-0018, 20260813-0398, 20260814-0003, 20260814-0122, 20260814-0420, 20260817-0330, 20260817-0354, 20260818-0072, 20260819-0147, 20260819-0245, 20260822-0212, 20260823-0022, 20260824-0408, 20260825-0005, 20260825-0370, 20260826-0095, 20260830-0130, 20260830-0269, 20260902-0027, 20260904-0265, 20260905-0357, 20260906-0348, 20260906-0399, 20260907-0143, 20260907-0221, 20260907-0232, 20260907-0393, 20260908-0052, 20260908-0205, 20260910-0150, 20260910-0400, 20260912-0218, 20260913-0044, 20260913-0196, 20260913-0250, 20260913-0273, 20260916-0336, 20260916-0338, 20260918-0071, 20260918-0294, 20260919-0402
- **SCH-PLUMB** (25): 20260709-0365, 20260718-0360, 20260720-0216, 20260730-0054, 20260801-0024, 20260802-0015, 20260802-0016, 20260802-0282, 20260810-0025, 20260810-0058, 20260810-0088, 20260811-0305, 20260811-0369, 20260812-0116, 20260814-0123, 20260818-0206, 20260822-0175, 20260822-0383, 20260826-0390, 20260827-0344, 20260830-0090, 20260908-0352, 20260913-0012, 20260917-0126, 20260919-0037
- **SCH-TUNEUP** (16): 20260711-0109, 20260720-0371, 20260721-0110, 20260801-0176, 20260807-0312, 20260816-0368, 20260818-0184, 20260826-0277, 20260828-0211, 20260907-0140, 20260910-0166, 20260910-0236, 20260911-0179, 20260912-0361, 20260914-0070, 20260918-0384
- **SCH-BURNING** (16): 20260706-0101, 20260706-0182, 20260709-0082, 20260710-0028, 20260713-0075, 20260714-0234, 20260715-0289, 20260725-0329, 20260806-0377, 20260810-0239, 20260820-0013, 20260904-0418, 20260906-0032, 20260908-0029, 20260915-0133, 20260916-0311
- **SCH-RESCHED** (15): 20260711-0063, 20260721-0258, 20260725-0112, 20260801-0208, 20260825-0192, 20260826-0309, 20260827-0091, 20260827-0149, 20260829-0049, 20260902-0001, 20260902-0229, 20260903-0026, 20260911-0171, 20260917-0023, 20260917-0395
- **SCH-CONFIRM** (8): 20260710-0124, 20260730-0183, 20260805-0154, 20260806-0102, 20260823-0412, 20260830-0209, 20260908-0158, 20260911-0034
- **SCH-CANCEL** (6): 20260707-0002, 20260724-0325, 20260726-0220, 20260902-0152, 20260904-0340, 20260909-0416
- **SCH-LATE** (9): 20260721-0261, 20260725-0355, 20260806-0284, 20260808-0271, 20260813-0247, 20260816-0097, 20260818-0151, 20260830-0388, 20260916-0098
- **BILL-BALANCE** (15): 20260708-0255, 20260710-0121, 20260715-0021, 20260718-0419, 20260727-0080, 20260731-0301, 20260803-0190, 20260816-0313, 20260819-0131, 20260821-0310, 20260901-0410, 20260908-0164, 20260910-0203, 20260912-0083, 20260914-0074
- **BILL-PAY** (14): 20260708-0115, 20260709-0356, 20260717-0359, 20260718-0262, 20260719-0272, 20260721-0125, 20260723-0035, 20260724-0040, 20260727-0138, 20260730-0233, 20260809-0197, 20260810-0008, 20260819-0014, 20260820-0043
- **BILL-AUTOPAY** (14): 20260709-0347, 20260710-0254, 20260713-0036, 20260713-0263, 20260715-0213, 20260719-0059, 20260719-0226, 20260806-0077, 20260807-0202, 20260811-0275, 20260825-0118, 20260826-0304, 20260906-0055, 20260909-0137
- **BILL-EXPLAIN** (13): 20260710-0373, 20260728-0193, 20260805-0244, 20260821-0199, 20260825-0066, 20260825-0145, 20260825-0266, 20260830-0165, 20260905-0201, 20260905-0363, 20260907-0204, 20260908-0257, 20260915-0303
- **BILL-DUP** (11): 20260709-0129, 20260725-0288, 20260726-0331, 20260806-0207, 20260810-0219, 20260825-0415, 20260831-0362, 20260901-0238, 20260910-0358, 20260912-0099, 20260914-0381
- **BILL-DISPUTE** (16): 20260714-0246, 20260718-0111, 20260729-0278, 20260805-0214, 20260810-0078, 20260810-0162, 20260811-0299, 20260815-0345, 20260816-0224, 20260817-0241, 20260828-0267, 20260901-0127, 20260902-0168, 20260906-0283, 20260909-0119, 20260910-0387
- **BILL-REFUND** (8): 20260710-0136, 20260715-0100, 20260812-0169, 20260816-0191, 20260818-0092, 20260821-0353, 20260823-0068, 20260827-0065
- **MEM-CANCEL** (13): 20260710-0364, 20260713-0287, 20260718-0349, 20260719-0217, 20260723-0251, 20260804-0188, 20260806-0230, 20260809-0376, 20260815-0270, 20260828-0120, 20260902-0386, 20260906-0087, 20260908-0017
- **MEM-RENEW** (14): 20260707-0096, 20260707-0392, 20260710-0135, 20260713-0253, 20260714-0200, 20260726-0307, 20260809-0128, 20260816-0106, 20260821-0181, 20260830-0259, 20260831-0167, 20260908-0407, 20260913-0342, 20260913-0382
- **MEM-INCLUDE** (12): 20260707-0148, 20260718-0045, 20260718-0060, 20260719-0413, 20260808-0146, 20260813-0156, 20260816-0268, 20260819-0163, 20260820-0252, 20260826-0073, 20260828-0316, 20260912-0394
- **MEM-PRICE** (8): 20260712-0104, 20260716-0006, 20260721-0108, 20260831-0231, 20260911-0235, 20260912-0139, 20260915-0385, 20260916-0397
- **MEM-UPGRADE** (6): 20260713-0314, 20260714-0019, 20260803-0056, 20260806-0174, 20260812-0405, 20260904-0144
- **MEM-DISCOUNT** (4): 20260713-0285, 20260727-0300, 20260730-0048, 20260829-0404
- **WAR-CLAIM** (14): 20260711-0248, 20260712-0227, 20260714-0326, 20260723-0042, 20260727-0215, 20260813-0350, 20260815-0114, 20260823-0295, 20260824-0033, 20260826-0225, 20260827-0084, 20260902-0375, 20260910-0291, 20260914-0009
- **WAR-REPEAT** (6): 20260712-0007, 20260716-0317, 20260722-0064, 20260729-0324, 20260906-0132, 20260909-0327
- **WAR-PARTS** (7): 20260709-0315, 20260719-0153, 20260720-0292, 20260723-0276, 20260730-0274, 20260803-0004, 20260811-0085
- **WAR-TRANSFER** (8): 20260722-0161, 20260730-0346, 20260803-0086, 20260809-0039, 20260816-0389, 20260823-0142, 20260829-0057, 20260830-0105
- **WAR-REGISTER** (10): 20260707-0053, 20260709-0010, 20260712-0195, 20260722-0249, 20260728-0194, 20260730-0323, 20260805-0173, 20260815-0406, 20260822-0343, 20260904-0069
- **EST-REPLACE** (12): 20260709-0134, 20260711-0030, 20260721-0321, 20260724-0113, 20260724-0337, 20260727-0076, 20260803-0155, 20260810-0237, 20260818-0243, 20260831-0297, 20260908-0160, 20260911-0256
- **COMPLAINT-CONDUCT** (6): 20260718-0062, 20260722-0198, 20260729-0041, 20260729-0260, 20260730-0222, 20260802-0079
- **COMPLAINT-OPINION** (5): 20260710-0335, 20260726-0189, 20260830-0286, 20260831-0339, 20260906-0411
- **COMPLAINT-REPEAT** (5): 20260724-0391, 20260730-0223, 20260730-0306, 20260819-0177, 20260831-0051
- **SAF-GAS** (3): 20260712-0046, 20260728-0264, 20260822-0185
- **SAF-CO** (5): 20260721-0093, 20260805-0290, 20260816-0038, 20260822-0341, 20260905-0318
- **SAF-SPARK** (1): 20260717-0180
- **COMMERCIAL** (5): 20260728-0089, 20260730-0396, 20260819-0228, 20260916-0403, 20260917-0187
- **HIRING** (6): 20260712-0067, 20260714-0366, 20260715-0351, 20260716-0379, 20260818-0298, 20260828-0409
- **WRONG-NO** (5): 20260813-0031, 20260820-0374, 20260904-0186, 20260906-0280, 20260918-0417
- **MULTI-REPAIR-PLAN** (4): 20260710-0081, 20260712-0328, 20260724-0308, 20260917-0332

### 11.4 Transcripts read in full (57)

20260708-0255, 20260709-0347, 20260711-0248, 20260710-0373, 20260714-0246, 20260707-0096, 20260707-0148, 20260708-0115, 20260709-0134, 20260710-0364, 20260709-0129, 20260711-0063, 20260707-0053, 20260722-0161, 20260721-0261, 20260709-0365, 20260712-0104, 20260710-0124, 20260710-0136, 20260712-0007, 20260712-0067, 20260721-0093, 20260707-0002, 20260728-0089, 20260813-0031, 20260713-0314, 20260718-0062, 20260724-0391, 20260709-0315, 20260710-0081, 20260710-0335, 20260712-0046, 20260717-0180, 20260713-0285, 20260902-0001, 20260814-0003, 20260720-0279, 20260722-0198, 20260821-0353, 20260706-0101, 20260706-0182, 20260724-0308, 20260917-0332, 20260719-0153, 20260720-0292, 20260723-0276, 20260916-0311, 20260810-0237, 20260711-0109, 20260714-0178, 20260820-0374, 20260906-0280, 20260830-0269, 20260810-0088, 20260709-0103, 20260913-0342, 20260818-0092

Coverage: 37 of 37 categories have at least one call read in full.
