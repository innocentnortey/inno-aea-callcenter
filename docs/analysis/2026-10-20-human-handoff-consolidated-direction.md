# Human handoff: consolidated product direction

**Date:** 2026-10-20, America/Chicago. **Writer:** Claude (Opus 5.5). **Status:** decision-ready synthesis, **not a PRD**,
not approved, and nothing described here has been built. **Supersedes for planning:** §5 "Ranked features" of the
[original handoff direction](2026-10-20-human-handoff-product-direction.md). That note stays as the research record and is
not edited. **Inputs:** the [issued briefing](../source/aea-call-center-briefing.md), the
[brief audit](2026-10-20-brief-audit.md), the [handoff information inventory](../data/handoff-information-inventory.md)
and the [company and service profile](2026-10-20-meridian-company-service-profile.md). Outside research is cited by the
`S-N` IDs in the [source register](../source/source-register.md) and was not re-run for this document.

**Updated later on 2026-10-20: Innocent's decisions recorded, in two rounds.** Round 1: OD-1, OD-2, OD-3 (= audit DEC-3)
and OD-6 decided (§8). Round 2: urgent comfort cases and safety (OD-4, D2, D5), the follow-up channel (OD-5), the
reschedule fee and waivers (D3 = DEC-2), unsupported requests (D4), chat history (D6), scope (DEC-1, DEC-4, DEC-5),
partner questions Q-1–Q-3, the internal deadline and LangGraph (§9, §10). Round 3 (same day) settled the rest of OD-4,
D6, the DEC-1 order, DEC-4's scheduling guide, repository visibility, the zone mapping and the profile items. The full
status table is §11. **Stage 2 check (2026-10-20):** OD-4 (ii) was narrowed; the urgent path runs only when the
customer says someone is in danger (§9.1). These are
**product choices, not implemented capabilities**. No code exists, and no stage gate moved.

## How claims are labelled

| Label | Means | Example |
|---|---|---|
| **[Issued]** | Required or stated by the issued brief (Part A portal page, Part B PDF) | "hands off with enough context that a human can pick up without starting over" (Part B §4) |
| **[Meridian]** | Observed in the issued Meridian data (transcripts, KB, DB). Transcripts show what was *said*, not that it was right | 0 of 420 calls end in a live transfer (inventory §1) |
| **[Research]** | Outside evidence, with its `S-N` and limits; not about Meridian | Escalations triggered by frustration took 40.8% longer (S-139) |
| **[Innocent]** | Innocent's product direction for this revision (P1/P8, P2, P5, P6, P7 as given on 2026-10-20) | "Offer human help early" |
| **[Inference]** | My design interpretation or proposal | "A fixed eight-heading brief" |

Section references such as "direction §5" mean the original note; "inventory §7" means the handoff information inventory;
"profile §4" means the company profile; "audit E-5" means a finding in the brief audit.

---

## 1. Product direction in one page

**What the brief asks for.** The agent must recognize when it is out of scope, tell the caller what is happening, and hand
off "with enough context that a human can pick up without starting over"; it must not guess **[Issued]** (Part B §4). The
reviewer will "watch the agent escalate" and judges "clean failure" **[Issued]** (Part B §6, "What we are looking for").
The baseline is chat; voice is extra credit **[Issued]** (Part B, Extra credit).

**What Meridian's data adds.** Every human handoff in the 420 calls is a promised callback, never a live transfer. No agent
collected a callback window or gave a reference number, and the same kind of case received three different promises
**[Meridian]** (inventory §1, §5.3). There is no case, callback, staff or shift record anywhere in the issued data
**[Meridian]** (inventory §5.2). So every handoff mechanism below is **new, proposed state**, not something Meridian runs.

**The experience we are aiming for [Innocent, refined by Inference]:**

- **Customer.** Can ask for a person at any moment, and is never made to "earn" one by getting frustrated first. If someone
  is on shift, they can wait in a live queue and a person joins the *same* conversation. If nobody is staffed, they are
  told so plainly: a representative will get back to them within one business day, with a reference, using the contact
  details they give: email by default, or a phone call if they prefer (OD-5). For no heat, no cooling or an active
  leak, they book normally unless they say someone is in danger because of it; then they are first directed to
  Meridian's 24/7 emergency number (§9.1). To see or change private account details, they enter a
  one-time code sent to the phone or email already on their record (simulated in the demo, OD-3). Public questions and
  safety help need no code. In a safety situation, the instruction ("leave the home immediately…", the KB's words) comes before anything else.
  They never repeat their story.
- **Representative.** Opens a case and sees, in about a minute, a short brief told as a small story: what happened, what the
  customer needs, what the AI did, and what is left to decide. Verified records and customer claims look different.
  Every fact can be checked in one click against a saved copy of what the AI saw and the current record. The full
  conversation is always one click away.
- **Supervisor and business owner.** See what needs action, not just counts: cases nobody owns, cases due soon, cases
  overdue, and promises not kept. Can assign or reassign from the same view. The business owner sees whether the AI
  reduces load *without* breaking promises, and why handoffs happen.

**What the design refuses to do [Inference, from audit E-1, E-5, C-7].** Pretend a person is available, show a queue
position or wait time it did not measure, promise a follow-up nobody will make, count a handed-off or abandoned
conversation as "contained", or present a customer's claim as a verified fact.

---

## 2. What changed from the original §5

| Original item (direction §4–§5) | Revised treatment | Why |
|---|---|---|
| **#1 Verifiable handoff brief** | **Split and kept.** Becomes **C2 Triage brief** (what to extract, fixed readable format) plus **C4 Source trail** (lookup log, snapshot and current record). Its eight fields survive as the brief's headings | [Innocent] asks for case-specific triage extraction (P2) and a readable format (P7); [Meridian] inventory §7 defines what each handoff type needs; source handling grew enough to stand alone (P6) |
| **#2 Commitment queue** | **Kept and made operational** as **C3 Case ownership and oversight**: explicit states, owners, next actions, due times, promise-kept tracking, and intervention views. Staffing-aware routing moves to **C1** | [Innocent] P5: cases must not sit untouched; the original queue had states but no rule for unowned or overdue work or for staffing ending |
| **#3 Resolution and correction record** | **Retained, narrowed, ranked last** as **C5 Outcome and correction record**. Its "verify in place" part moves to C4 | [Issued] Part B §7 asks for a feedback loop ("describe how the loop works even if you only implement the first step"); cheapest once C3 exists; first to cut if time runs short (direction §11) |
| Unified agent workspace (candidate 3, already replaced in direction §5) | **Stays replaced.** Not revived | Weakest evidence (P6, S-143, S-144, S-147); one case view is enough |
| Live takeover (direction §7, §9: "later product") | **Promoted to a designed path** in C1 as a **proposed live-chat queue**. **Decided (OD-1, OD-2):** the demo shows it inside a clearly labelled simulated staffed state that the reviewer enters on purpose; the reviewer can claim the case and reply in the same conversation | [Innocent] P1/P8 and OD-1/OD-2; [Meridian] Meridian has no live queue today, so it must never be presented as existing |
| "Explicitly not requirements: LangGraph…" (direction §9) | **Superseded for planning.** LangGraph is the decided framework for conversation state, tool use and handoff; the service needs are defined independently and mapped onto it in §10 (confirmed by Innocent, round 2) | [Innocent] 2026-10-20; the original note stays as history |
| **P1** escalated contacts are harder, lateness worse | **C1:** offer a person early, using observable failure signals as well as direct requests | [Research] S-139: frustration-triggered escalations cost more; early, agent-initiated intervention cut the damage |
| **P2** customers repeat themselves | **C2:** per-reason triage extraction plus full log; **C1:** same conversation thread on live join | [Innocent]; [Issued] Part B §4 |
| **P3** summaries drop or invent specifics | **Carried as a protection in C2 and C4:** facts assembled from records, not written by the model; exact amounts copied, not paraphrased; claims kept apart | [Research] S-141, S-158, S-159 |
| **P4** agents must verify; links can mislead | **Carried in C4:** links go to the exact passage or record field, with a saved snapshot; spike tests whether cited sources truly support the claim | [Research] S-138, S-161, S-162 |
| **P5** promises and ownership slip | **C3** | [Research] S-151, S-164, S-165; [Meridian] three inconsistent promises, no references |
| **P6** tool switching and hunting | **C4:** only the sources pertinent to this handoff, from the lookup log | [Innocent]; evidence for P6 is weak (direction §4), so C4 stays narrow |
| **P7** more information becomes a burden | **C2:** fixed, skimmable eight-heading format at about a fifth-grade reading level, tested for comprehension and time to first action | [Innocent]; [Research] S-142 (small, qualitative) |
| **P8** customers fear losing access to a person | **C1:** a visible "talk to a person" control, honoured immediately | [Research] S-154, S-152, S-155 |
| Measures (direction §10) | **Kept**, reassigned to each capability's evaluation and to §7's spike | Same measures, now tied to pass criteria |
| Risks and open questions (direction §11) | **Kept**; resolved where the inventory answered them; the rest in §8 | Inventory confirmed the 54-call, no-transfer, three-promise findings |

**Revised ranking (one line each) [Inference].** C1 and C2 are co-required: without C1 there is no honest way to reach a
person, and without C2 the person starts over. C3 makes the handoff survive past the chat. C4 makes the brief checkable.
C5 closes the loop. **Cut order if time runs short:** C5 to "outcome only", then C4 to links without snapshots, then C3
without the business-owner view. C1 and C2 are not cut.

---

## 3. Revised ranked capabilities

### C1. Honest human access and staffing-aware routing (P1, P8)

**Problem.** Customers fear that AI service makes it harder to reach a person **[Research]** (S-154: 64% would prefer
companies not use AI for service, n = 5,728). Escalations that wait for frustration cost more and land worse
**[Research]** (S-139). In Meridian's calls, 11 customers ask for a manager or "someone in charge" and none for "a person",
because they were already talking to one **[Meridian]** (inventory §3.3). A chat changes that.

**Innocent's direction.** A visible way to request a representative; a live-chat queue when someone is on shift but busy,
with the person joining the same conversation; an honest asynchronous follow-up when nobody is staffed; early offers of
help when observable signs show the interaction is failing; never make the customer wait for frustration before honouring
a direct request **[Innocent]**.

**Smallest useful experience [Inference].**

1. **A persistent "Talk to a person" control** in the chat, always visible, plus recognition of typed requests ("can I
   talk to someone", "manager", "real person"). Either one creates a handoff **immediately**. The AI may then *offer*
   to keep helping while the customer waits ("I can still look up your invoice while you wait, if you'd like"). That
   offer is optional and never replaces the handoff.
2. **Safety first.** If a safety trigger fires (`policies/escalation_and_safety.md`: gas, CO alarm, sparks/smoke/flames,
   burning smell with tripped breakers), the safety instruction is shown in the same turn, before any queue, identity or
   lookup step **[Meridian]** (K-12; audit E-3). The person-request control stays available after it. Contact details are
   *offered* only after the instruction and never gate it; a safety-priority case is created even for an unmatched caller
   (D5, §9.2). Urgent comfort reports (no heat, no cooling, active leak) follow §9.1: a normal booking, unless the customer
   says someone is in danger, which brings the 24/7 emergency line plus an emergency-priority case.
3. **Observable failure signals** (not guessed emotion) that make the AI *offer* a person early:
   - the customer repeats or rephrases the same request after an unsuccessful answer (two attempts);
   - the AI cannot find a supporting current source, or a tool call fails, twice in one conversation;
   - identity matching fails twice;
   - the customer corrects the AI ("that's not what I asked", "that's wrong");
   - explicit complaint language, such as the corpus phrases "I'm done", "I'd better", "Today. Not next week."
     **[Meridian]** (20260724-0391, 20260710-0136, 20260718-0062);
   - a request in the KB's supervisor list (dispute, refund, conduct, manager, legal threat or chargeback) **[Meridian]**
     (`policies/escalation_and_safety.md`; K-16).
   **Decided (OD-6):** Innocent accepted these two-attempt thresholds as **starting hypotheses**, to be tested on labelled
   synthetic cases and changed after evaluation. They are not patterns found in the Meridian transcripts, which contain no
   mid-call escalations (inventory §3.3). A direct request for a person still triggers on the first request, and safety
   still comes first.
4. **Staffing-aware routing.** The system reads an explicit **representative-presence state** (who is online and their
   current load). It never infers staffing from time of day alone. In the demo this state is "nobody online" unless the
   reviewer enters the labelled simulation (OD-1).

| Staffing state | What the customer is shown | What happens |
|---|---|---|
| **A person is free now** | "A person from [team] can join this chat. Connect now?" | The case is claimed; the AI pauses; "Dana from billing has joined" appears in the same thread |
| **On shift but all busy** | "Our team is helping other customers. You can wait here for the next person, or choose a follow-up instead." A queue position or wait estimate is shown **only** if it is computed from the live queue and measured handling times | The case enters the live queue with its brief ready. The AI may keep helping if the customer opts in |
| **Nobody online** | No queue and no "someone will join shortly". "No representative is online right now. A representative will get back to you within 1 business day. Your reference is …" (Refund requests: "within 2 business days", OD-4 iv) Then a request for the contact details and time window to use | A follow-up case is created with a due time from the written policy (OD-4, OD-5) |
| **Staffing ends before the case is claimed** | If the customer is still in the chat: "Our team has gone offline before reaching you. A representative will get back to you within 1 business day," with the same reference, then contact capture if not already given. If they have left: the case converts and the same commitment stands | The case moves from the live queue to the follow-up queue, keeps its original creation time, and alerts a supervisor (C3) |

5. **Customer keeps the promise.** Every handoff ends with a reference number, the exact promise text, the time window the
   customer chose, and what to do if it becomes urgent **[Inference]** (direction §5 #2; inventory §7 notes).

**Information required.** Staffing state (who, team, load); handoff reason from a fixed list; the policy table (reason →
owner role → promise text → due rule); the fixed clock (2026-10-16 in this dataset, audit C-9); the customer's contact
preference. **None of these exist in the issued data**; the policy table is derived from
`policies/escalation_and_safety.md` and the staffing state is new **[Meridian]** (inventory §5.2).

**Evidence.** [Issued] Part B §4 ("tells the caller what is happening"); [Research] S-139 (early intervention), S-154,
S-152 (inviting human contact raised uptake), S-155 (trust 26% → 55% when a human is reachable; vendor), S-153 (very fast
human replies after a handoff read as a bot, so the "has joined" marker matters more than speed), S-167 and S-168 (queue
position and accurate delay information affect abandonment). [Meridian] no live transfers; Sunday and after-hours calls
exist in the data, so the unstaffed path is not an edge case (inventory §10.2).

**Risks.**
- Implying staffing in the reviewer environment, where nobody is staffed (audit E-5). This is the most likely reviewer trap.
- Fake precision: a queue position or wait estimate computed from nothing.
- Failure triggers that fire too often and annoy, or too late. The corpus has **no** mid-call escalations (0 of 420,
  inventory §3.3), so the thresholds can only be tuned on synthetic cases.
- A retention-style loop that keeps the customer with the AI after they asked for a person (audit E-1, E-2).

**How to evaluate.**
- A direct request for a person creates a handoff in 100% of test cases, on the first request.
- 0 unsupported availability claims ("connecting you now" when the staffing state says nobody).
- The safety instruction appears before any queue or identity text in 100% of safety cases, including phrases buried mid-chat
  (audit E-3).
- Synthetic failure-signal cases (labelled per `synthetic-test-data.md`) produce an offer within the stated threshold.
- The staffing-ends transition preserves the case and shows the one-business-day commitment (OD-5).
- With nobody online, no live queue is ever offered (OD-5).

### C2. Triage brief: the right statements, in a readable format (P2, P3, P7)

**Problem.** If the person who picks up has to re-ask, the handoff failed the brief's own test **[Issued]** (Part B §4).
AI summaries drop named entities and agent actions, and add plausible inferences **[Research]** (S-141: 53.67% entity
retention, vendor benchmark; S-158; S-159). More information can become a burden **[Research]** (S-142, small study).

**Innocent's direction.** Keep the full running log. For each handoff reason, extract the customer statements that matter
for *that* situation's triage, alongside account or service background the system already has. Give the representative
a short, useful brief and the full conversation. Separate verified records from claims. Never imply an identity or
account fact was verified when it was not. Use a fixed, skimmable format with clear headings and short bullets, about a
fifth-grade reading level, preserving exact amounts, dates and sources, told as a small story **[Innocent]**.

**Smallest useful experience [Inference].** The brief has **eight fixed headings, always in this order**. Empty
headings say "None", so a missing fact is visible rather than silently absent:

1. **Why this came to you:** reason from a fixed list + the rule that fired.
2. **What the customer needs:** one or two short quotes in their own words.
3. **What we know for sure:** verified facts, each with its source.
4. **What the customer says (not checked):** their claims.
5. **What the AI did:** answers given, lookups, actions tried and their results.
6. **What we told the customer:** the exact promise and its due time.
7. **What you need to decide:** the open question.
8. **Who they are and how to reach them:** identity status, contact and window.

A "Full conversation" link sits above heading 1. Headings 1, 3, 5, 6 and 8 are **assembled from stored state**, not
written by the model. Headings 2, 4 and 7 use model selection or wording, constrained to quoting and to the reason's
extraction list below. This keeps the model away from the facts a representative will act on (P3).

**What to extract, by handoff reason [Inference, built on inventory §7].** "Background" means fields the system already
read during the conversation; nothing is fetched just to fill the brief.

| Handoff reason | Customer statements to extract (triage) | Background to include | Leave out |
|---|---|---|---|
| **Safety** (gas, CO, sparks; inventory H1) | The hazard words exactly; whether they said they are outside; anyone else in the home | Instruction text shown and its time; rule bullet matched; contact details offered *after* the instruction (D5); matched record only if one exists | Account history, billing, membership |
| **Urgent comfort** (no heat, no cooling, active leak, **with someone stated to be in danger**; §9.1) | What has failed, since when, whether water is flowing, who is in danger and why, in their words | That the emergency-line direction was shown; any KB containment step given; the separate one-business-day statement if unstaffed | Billing history |
| **Billing dispute** (H2) | The amount they expected, the amount they were billed, what they say they were told ("Nobody told me about that") | Invoice ID, line items, balance, due date (`invoices`); the fee lines cited; the diagnostic-credit rule (`faq/customer_faq.md`) | Other invoices; payment method; unrelated appointments |
| **Refund request** (H3) | What they want refunded, why ("didn't fix anything"), whether they say another company was paid | The related invoice or visit if matched; repair-warranty terms (`warranty/warranty_policy.md`); "agents may NOT issue refunds" as context for the decision | Membership details unless the refund is about membership |
| **Service complaint / manager request** (H4) | What happened, when, which visit or technician they mean, what outcome they ask for, prior contacts they mention | Matched appointment and technician (`appointments`, `technicians`); "prior contacts: not recorded" when they claim earlier calls | Invoices unless money is in the complaint |
| **Late technician** (H6) | Window and current time as they state it; whether they will wait | Appointment window (`appointments` + `appointment_slots`); minutes past window by the fixed clock; the two KB options (`services/technician_arrival_and_etas.md`) | Billing history |
| **Burning smell, breakers unknown** (H7, policy gap) | The smell words; the answers to "already tripped?" and "smoke, sparks or flames?" (or "can't tell") | Which path was taken (§9.2): instruction, cautious escalation, or urgent booking | Unrelated account details |
| **Reschedule fee contested** (§9.3) | Their reason, in their words | Appointment and window; hours before the window by the fixed clock; the exact fee statement shown; whether they went ahead | Payment details |
| **Action the system cannot perform** (H8: payment link, autopay, auto-renew, registration) | The exact action requested | The record fields read (e.g. `customers.membership_renewal_date`); what the AI said it could not do | Card details (never collected, audit L-4) |
| **Booking cannot be completed / wants earlier** (H9) | Requested date, window and reason for urgency (heat, water, vulnerable occupant) | Search criteria and results; zone from `customers.city`; tier | Invoices |
| **Direct request for a person (any topic)** | The request itself and the topic so far | Whatever the conversation already touched | Anything not yet touched |
| **Observed failure** | The question the AI failed to answer, in their words | The attempts made and why they failed (no current source, tool error) | — |

**Identity, stated plainly.** Heading 8 always says *how* the customer was identified and what matched. With the decided
demo method (OD-3, §8), it reads, for example: "Found by name and phone. Confirmed with a one-time code sent to the phone
on record (demo simulation, not production verification)." If the code was not completed, it says so: "Record found by
name and phone. Code not confirmed. No private details were shown." **[Inference]** It never says "verified" for a match
alone. In Meridian's calls, identity was name plus a phone, account number or address, with no visible check against a
record **[Meridian]** (inventory §10.2).

**Reading level.** Target about fifth-grade wording **[Innocent]**: short sentences, common words, one idea per bullet.
Exact values are copied, never rounded or paraphrased: "$144", "INV-204411", "Mon 2026-10-19, 7:00 pm", "1 business day".
Plain wording must not erase a distinction that changes the decision: "1 business day" is not "soon", "the customer
says" is not "the invoice shows". **Readability alone does not solve P7.** It is tested together with comprehension and
time to first action (§7).

**Information required.** Full conversation log; handoff reason and rule; extraction list per reason; stored lookup
results (C4); promise record (C3); identity-check record.

**Evidence.** [Issued] Part B §4; [Research] S-141, S-158, S-159 (omission and invention), S-156 (a structured handoff
format cut preventable adverse events 30% with no added time; hospital, analogous), S-157 (AI handoff notes rated
marginally worse by physicians), S-142 (extra AI information became a burden; one site, 13 reps). [Meridian] each handoff
type needs different facts (inventory §7, §9 E1–E8).

**Risks.** Extraction picks filler ("Can you hear me okay?" appears in 92 calls, inventory §2); a quote taken out of
context; simplified wording that changes meaning; a heading that reads as "verified" when it is a claim; a brief that
grows back into a transcript.

**How to evaluate.** Required-item recall per reason against gold labels written before the run; zero invented facts;
zero claims placed under "What we know for sure"; estimated reading grade; comprehension and time to first action in a
scripted walkthrough (§7).

### C3. Case ownership and oversight (P5)

**Problem.** In Meridian's calls, the same kind of case got three different promises; no reference, no window, no owner
**[Meridian]** (inventory §1). Callbacks fail on credibility **[Research]** (S-151: 37% acceptance at one bank). Named
ownership beats pooled queues, and free picking hurts throughput **[Research]** (S-164, S-165, analogous).

**Innocent's direction.** Rework the commitment queue so cases cannot sit untouched: clear states, an owner, next action
and due time; representatives see what needs action; supervisors and business owners see unowned, due-soon and overdue
cases; record the exact promise and whether it was kept; monitoring supports assignment and intervention rather than
displaying counts; define what happens when the live queue is staffed, all staff are busy, and staffing ends before a
claim **[Innocent]**.

**Smallest useful experience [Inference].** One case per handoff, with a lifecycle (§6), a promise record, and three views
(representative, supervisor, business owner) that each lead to an action. Every count on a supervisor or owner view opens
the list of cases behind it, with an assign or reassign action.

**Information required.** Case store (new state, beside the working DB copy, never in the issued file; audit G-7); staff
list and roles; policy table; fixed clock; case event history (who did what, when).

**Evidence.** [Meridian] inventory §1, §5.2; [Research] S-151, S-164, S-165, S-166 (penalising transfers makes agents hold
cases), S-139 (early intervention). [Issued] Part B §7 monitoring list (volume, containment, escalations, failures,
latency) and "Would the business know if it broke?".

**Risks.** A queue that becomes a second, invisible backlog; alert fatigue; cherry-picking; measuring every handoff as a
failure, which pushes the system to hold cases (S-166); a promise that the policy table does not support.

**How to evaluate.** Promise text matches the policy table in 100% of cases (deterministic). In a simulated-clock test,
every unowned, due-soon and overdue case appears in the supervisor view at the right time; staffing-end conversion
preserves the case; promise-kept is computed correctly.

### C4. Source trail and verify-in-place (P6, P4)

**Problem.** Representatives must check AI output, and a citation can make a wrong claim look trustworthy **[Research]**
(S-162: citations raised trust even when random; S-161: explanations raise acceptance of wrong answers; over-reliance
drops only when checking is cheaper than redoing the work). Meridian's KB holds outdated copies beside current ones,
and its records change after a chat **[Meridian]** (audit K-1…K-18; inventory §8).

**Innocent's direction.** Keep an auditable log of each tool lookup (tool, record or passage ID, time, result the AI saw,
and the answer or action that used it). Surface only the sources pertinent to this handoff. Show a saved snapshot and a
route to the current record. Apply role-appropriate access. Start from the inventory's source list and handoff matrix;
invent no tools or records **[Innocent]**.

**Smallest useful experience [Inference].**

- **Lookup log (behind the scenes):** one row per lookup: tool, the record or passage ID, time (fixed clock and wall clock), the
  result the AI saw, and the message or action that used it. Retrieved text is stored as data, never as instructions
  (audit G-3).
- **In the brief:** each fact under "What we know for sure" carries a small source tag that opens a side panel. The panel
  shows **the snapshot** (what the AI saw) and **the current value**, with a "changed since" marker when they differ.
- **Only pertinent sources:** the sources used by facts in this brief, not every lookup in the conversation.
- **Policy passages** show the file, the version marker (date or "Rev") and the exact passage. Archived or old-copy files are
  never shown as authority (audit DEC-4); internal-only files are marked "staff only".

**Tools and records that exist, and those that don't [Meridian].** Only these can be sourced: KB passages (17 files),
`customers`, `appointments`, `appointment_slots`, `invoices`, `technicians`, `SCHEMA.md` and the dataset `README.md`
(inventory §5.1). Payment, autopay, auto-renew, processor, registration, repair-history, quote, dispatch, waitlist and
case records **do not exist** (inventory §5.2). A brief that needs one says "No record available".

**Snapshot vs current record, by source type** (from inventory §8):

| Source | Snapshot | Current record | Access [Inference] |
|---|---|---|---|
| Conversation | Yes, immutable | Link to the stored log | Staff on the case |
| Invoice | Fields read and quoted | Yes | Billing roles |
| Appointment and slot | What was offered or written, and the result | Yes | Scheduling roles |
| Customer record | Only fields used (tier, renewal date, brand, install date) | Yes, by ID | Staff on the case; not copied into the brief beyond contact |
| KB passage | Text, file, version, hash | Yes | Customer-facing files to all staff; internal files staff-only, never in customer messages |
| Tool result | Yes | No (link the record it produced) | Staff on the case |
| Promise and safety instruction | Exact text and time | No | Staff on the case |

**Evidence.** [Research] S-161, S-162, S-138 (agents adopted 38% of suggestions); [Meridian] audit §3, inventory §5,
§8; [Issued] Part A "retrieval accuracy (correct documents returned)" as an impact metric.

**Risks.** Links that look like verification but point at a passage that does not support the line; stale snapshots read as
current; access leaks of customer details to roles that do not need them (audit G-2, G-9); log bloat.

**How to evaluate.** Every fact in a brief has a working snapshot and current link; a human check finds the cited source
supports the fact in ≥95% of sampled facts; an injected record change shows "changed since" in 100% of cases; an
injected unsupported citation is caught by a reviewer (§7).

### C5. Outcome and correction record (feedback loop)

**Status: retained, narrowed, ranked last [Inference].**

**Problem.** The brief asks that logged conversations, flagged failures or human corrections feed back into improving the
system **[Issued]** (Part B §7). Without recorded outcomes, containment cannot be honest **[Inference]** (audit E-1).

**Smallest useful experience [Inference].** When a case closes, the representative picks an outcome (resolved on contact,
booking changed via the same booking tool and rules the AI uses, customer unreachable, escalated further, closed with no
action) and may flag the AI ("answer wrong", "brief wrong", "handoff unnecessary", "KB document wrong") with a note.
Flags go to a review list. **Nothing changes the KB, prompts or eval set automatically** (audit G-6, C-13).

**Why it is ranked last.** Its direct pain evidence is thinnest (direction §5), it depends on C3's case record, and it is
the first thing to cut to "outcome only" if time runs short (direction §11).

**How to evaluate.** Every closed case has an outcome; containment is computed from outcomes, with resolved, escalated,
abandoned and failed reported separately; flag review time is visible.

---

## 4. One end-to-end handoff story

**This is a seeded scenario, not a transcript.** It uses the issued test customer **MHC-10002** and invoice
**INV-204411** (`SCHEMA.md`, `invoices`), because no transcript invoice exists in the DB (inventory §1). The customer's
lines are **synthetic**, modelled on the 16 billing-dispute calls (e.g. 20260714-0246), which follow the same pattern:
"the tech quoted me … that's not what I agreed to" and "Nobody told me about that". The clock is the dataset's fixed
"today", Friday 2026-10-16.

**1. Customer view, AI turn.** Omar opens the chat and asks why his bill is $478. The bill is private, so the AI first
locates his record from his name and phone (MHC-10002). It does not treat that match as proof. It says: "I'll send a
6-digit code to the phone number on your account, ending in 02. Please type it here." The code appears only in the
separate, labelled **demo delivery inbox** (§8, OD-3), never in the chat. Omar enters it. Only then does the AI read
INV-204411 and explain each line: Diagnostic visit $89, Contactor replacement $245, After-hours dispatch $144. It cites the
2026 fee schedule for the fee types.

**2. Trigger.** Omar writes: "The tech said it was $89 to come out. Nobody told me about an after-hours fee. I want that
taken off." Two rules fire: a disputed invoice amount goes to a supervisor (`policies/escalation_and_safety.md`), and the
AI may not waive fees (audit E-4, DEC-2). The AI does not adjudicate. A deterministic check also records that the
invoice's $144 after-hours line differs from the $149 fee in `2026_fee_schedule.pdf` (audit D-8). That is a
note for staff; the AI does not say "you were overcharged" to the customer.

**3. Offer of a person (default: nobody online).** The AI says it cannot change charges and that a person can review this.
The "Talk to a person" control was visible throughout. The representative-presence state reads **nobody online** (the
honest default in the reviewer environment, OD-1), so no queue is offered:

> No representative is online right now. A representative will get back to you within 1 business day, by Monday,
> October 19, 7:00 pm. Your reference is MHC-C-0007. What's the best way and time to reach you?

(The "within 1 business day" wording is the settled part of OD-4. The due time assumes the FAQ phone hours, Mon–Fri
7am–7pm.) The AI then asks the OD-5 question: "We'll follow up by email unless you'd prefer a phone call. Which works best?"
Omar chooses a phone call to the number on his account, mornings. The case stores phone, the record's number (on record)
and "mornings". The AI offers, optionally, to answer any other question while the case is open.

**Branch A: the reviewer enters the simulated staffed state (OD-1, OD-2).** Before step 3, the reviewer switches on the
labelled simulation ("Demo: simulated staff on shift"). Omar's request now enters the live queue: "A representative will
join this chat when available. You can keep chatting with me while you wait, if you like." The reviewer opens the staff
console in a second tab, signs in as the labelled demo representative, sees the case at the top of the queue, and claims it.
The AI stops replying. Omar's chat shows "Riley (demo representative) has joined." The messages "Riley" sends are typed
by the reviewer: real actions in the demo, not scripted ones. When Riley returns the chat to the assistant or closes it, the
customer sees that too.

**Branch B: staffing ends before a claim.** In the simulation, the reviewer ends the shift while Omar waits. The case is
kept, moves to the follow-up queue with its original creation time, Omar sees the same one-business-day commitment and
reference as in step 3, and a supervisor alert fires (§6).

**4. Case and brief.** The case is created as **Unassigned**, reason *Billing dispute*, urgency *Supervisor, 1 business day*,
due Mon 2026-10-19 19:00. The brief is §5's example.

**5. Ownership.** On Monday morning the supervisor view shows the case under "Due today, unowned". A billing supervisor
claims it (**Claimed** → **In progress**). In the source panel, the invoice snapshot and the current invoice still match.
The fee-schedule passage shows $149 for after-hours, version "Effective January 1, 2026". The diagnostic-credit rule in
`faq/customer_faq.md` is shown beside the invoice, which bills the diagnostic next to a repair with no credit line.

**6. Outcome.** The supervisor phones Omar inside his morning window, the channel he chose (OD-5). In the prototype the call
is **recorded as an activity labelled "Demo: recorded, not placed"**; no call is made.
She records **Resolved**: "Adjustment approved: diagnostic credited." She flags "KB fee rule and invoice disagree" to the
review list. The promise record shows **Kept** (contacted before the due time). The business-owner view counts this case as
*escalated → resolved by staff*, not as AI containment.

---

## 5. Handoff brief format

The example below is the brief for §4's seeded case. It shows the intended tone: plain, short, exact. Facts, claims, the
promise and the open decision stay apart. Bracketed tags are links in the case view.

> **Billing dispute: INV-204411 · Ref MHC-C-0007 · Due Mon Oct 19, 7:00 pm** · [Full conversation]
>
> **Why this came to you**
> - The customer disputes a charge on his bill. Billing disputes go to a supervisor. [policy: escalation_and_safety.md]
>
> **What the customer needs**
> - "Nobody told me about an after-hours fee. I want that taken off."
>
> **What we know for sure**
> - Invoice INV-204411 is $478. Nothing is paid yet. Due Nov 1. [invoice]
> - The lines are: diagnostic visit $89, contactor $245, after-hours dispatch $144. [invoice]
> - Our fee schedule says after-hours dispatch is $149, not $144. [fee schedule, Jan 1 2026]
> - Our FAQ says the $89 diagnostic is credited if the repair is approved at the same visit. [FAQ, Mar 2 2026]
> - The invoice has no credit line. It does not say which visit it is for. [invoice]
>
> **What the customer says (not checked)**
> - The tech said it would be $89 to come out.
> - Nobody told him about an after-hours fee.
>
> **What the AI did**
> - Read the invoice and explained each line.
> - Did not change, waive or promise anything about the bill.
>
> **What we told the customer**
> - "A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm."
>
> **What you need to decide**
> - Should the after-hours charge stay?
> - Should the $89 diagnostic be credited?
>
> **Who he is and how to reach him**
> - Record MHC-10002, found by name and phone.
> - He entered the code sent to the phone on file. (Demo simulation. Not real ID proof.)
> - Follow up by: phone, his choice (email is our default). Number: the one on his record, ending 02. Best time: mornings.

**Notes on the format [Inference].**

- **The story in the bullets.** Read top to bottom, the bullets tell what happened (a disputed bill), what he needs (the fee
  removed), what the AI did (explained, promised nothing), and what is open (two decisions).
- **Reading level.** A simple Flesch–Kincaid estimate over the 17 bullets (source tags, identifiers and amounts removed)
  gives **about grade 3.6**: 7.5 words per sentence, 1.38 syllables per word. Treat that as a rough check, not proof. The
  formula is unreliable on very short bullets and says nothing about whether a reader finds the right fact, which is why
  §7 tests comprehension and time to first action as well. Exact identifiers and amounts stay even when they make reading
  harder.
- **What is deliberately absent.** Address, email, card details, other invoices, the AI's reasoning, and any judgement about
  whether the customer is right.
- **Mismatch noted as fact, not verdict.** "$149, not $144" is a fact from two sources. "He was overcharged" would be a
  conclusion, and it belongs to the supervisor.

---

## 6. Case lifecycle and oversight

### States [Inference]

| State | Means | Owner | Next action | Due |
|---|---|---|---|---|
| **Live-queued** *(live path only; never offered when nobody is online)* | Customer is waiting in chat for a person | None yet | Next free person claims and joins | No time promise beyond "when available"; a wait estimate only if measured |
| **Unassigned** | Case exists, nobody owns it | None | Claim it | From the policy table (e.g. 1 business day) |
| **Claimed** | Someone has taken responsibility | Named person | Open and act | Same due time |
| **In progress** | The owner is working it, or a person has joined the live chat. **While a person owns the live chat, the AI is paused** | Named person | Contact the customer or decide; hand the chat back to the AI or close it | Same due time |
| **Waiting** | Blocked on the customer, another team or a scheduled follow-up window | Named person | The stated wake-up action and time | A wake-up time is required; no open-ended waiting |
| **Resolved** | The customer's need was met | Named person | Record outcome (C5) | — |
| **Closed unresolved** | Ended without meeting the need (unreachable, out of scope, declined) | Named person | Record the reason | — |

**Transitions that matter.** Live-queued → Unassigned when staffing ends before a claim (the case keeps its creation time and
the customer gets the same one-business-day commitment as the no-one-online path). Claimed → Unassigned on release, with a recorded reason. Resolved or closed →
Unassigned if the customer returns quoting the reference.

### Priority

Every case carries a priority from code, never from the model (§9.4):
- **P0 safety:** gas, CO, sparks, smoke, flames, or a burning smell with tripped breakers;
- **P1 emergency-priority:** no heat, no cooling or an active leak **where the customer says someone is in danger**, or a
  burning smell with unclear risk;
- **P2 time-sensitive**;
- **P3 standard:** policy requires a person;
- **P4 routine follow-up.**

P0 and P1 sit above everything in every queue. Priority sets the order and the alerts. It is not a promise of response
time.

### The promise record

Each case stores:
- the **exact promise text shown to the customer**;
- the policy row it came from;
- the due time, worked out with the fixed clock and business hours;
- the **follow-up preference** (channel, destination and whether it is on record, contact window; §9.5);
- the **promise status**: *open*, *kept*
(contacted before due), *missed*, or *changed* (a new promise given, with the reason and the new text shown to the customer).

### Alerts (proposed thresholds, to tune) [Inference]

| Alert | Fires when | Goes to |
|---|---|---|
| **Safety (P0) or emergency-priority (P1) case** | Created | Supervisor immediately; top of every list |
| **Unowned** | Unassigned longer than a set time while staff are on shift | Supervisor |
| **Due soon** | Within a set window of the due time and not resolved | Owner, then supervisor |
| **Overdue** | Past due and the promise not kept | Owner and supervisor; counted against promise-kept |
| **Stuck waiting** | Wake-up time passed in "Waiting" | Owner |
| **Staffing ended with live-queued cases** | Shift ends with anyone still queued | Supervisor |

### What each audience sees and does (decided for the demo, OD-1)

These are needs, not screen designs.

| Audience | Needs to see | Needs to do |
|---|---|---|
| **Customer (chat)** | A visible "Talk to a person" control; whether anyone is online; for no heat, no cooling or a leak where someone is in danger, the emergency-line direction first; in the live path, when a person has joined and that the assistant is paused; the reference, the exact commitment and what to do if it becomes urgent; for private details, where the code was sent (masked) | Ask questions; request a person at any time; enter a contact code; give contact details and a time window; keep chatting with the AI while waiting, only if they choose |
| **Representative (queue and case view)** | "Needs my action": P0 and P1 first, then by due time, overdue first; the live queue when online, oldest first, P0 and P1 on top; the case: brief, pertinent sources (snapshot and current), full conversation, identity status, the promise **with the follow-up preference beside it** | Claim or release a case (with a reason); join the live chat and reply; hand the chat back to the AI or close it; record the outcome and contact attempts; flag an AI error |
| **Supervisor** | **P0 and P1 cases** (always shown); **unowned**, **due soon**, **overdue** and **stuck waiting** cases, with owner, age and follow-up preference; the live queue length while staffed; cases converted when staffing ended; flags awaiting review | Assign or reassign (with a reason); change urgency (with a reason); start or end the simulated shift in the demo; open any case |
| **Business owner** | **Promises kept on time** as a share of promises due, with the missed ones; outcomes (resolved by AI, escalated, abandoned, failed) with denominators; handoffs by reason linked to example cases; operating measures from the brief: volume, escalations, failures, latency [Issued] Part B §7 | Open the cases behind any number; see why handoffs happen, as an input to KB or scope changes |

**Monitoring that leads to action [Inference].** Every number opens the cases behind it. A supervisor can act on what they
see without leaving the view. Handoffs are not scored as failures; the measured failure is a **missed promise** or an
**abandoned** conversation (S-166; audit E-1).

---

## 7. Validation spike proposal

**This is a proposal for a later spike.** It is not a formal Stage 5 `SP-N`, it does not advance any gate, and its
reviewers are not real Meridian staff. Results would be reported with their sample size and limits (`source-authority.md`
rule 5).

### Cases (15)

| # | Case | Source | Tests |
|---|---|---|---|
| 1 | Billing dispute, quote vs invoice | 20260714-0246 | Extraction, readability, sources |
| 2 | Seeded dispute, INV-204411 | `SCHEMA.md` seed, synthetic customer lines | Sources (snapshot vs current), full lifecycle |
| 3 | Refund request | 20260710-0136 | Extraction, promise mapping |
| 4 | Complaint with unverifiable earlier calls | 20260724-0391 | "Not recorded" handling |
| 5 | Conduct complaint, manager request | 20260718-0062 | Promise mapping ("today" vs policy) |
| 6 | Carbon monoxide alarm | 20260721-0093 | Safety before everything; no identity |
| 7 | Burning smell, no breaker information | 20260706-0182 | Policy-gap handling |
| 8 | Late technician | 20260721-0261 | Extraction, fixed-clock arithmetic |
| 9 | Compressor warranty, scheduling request | 20260719-0153 | A dropped request caught in "What the customer needs" |
| 10 | Cancel membership (action not supported) | 20260710-0364 | "No record available"; no false confirmation |
| 11 | Direct request for a person in the middle of a booking | **Synthetic** (no transcript has one) | C1 immediate handoff |
| 12 | Two failed answers, then "that's not what I asked" | **Synthetic** | C1 failure-signal offer (OD-6 thresholds) |
| 13 | Private request: right code, wrong code three times, and a name with no matching record | Seeded MHC-10001 plus **synthetic** inputs | OD-3: nothing private shown before the code; the code never appears in the chat; the no-match path routes to a person without revealing whether an account exists |
| 14 | No cooling, reported with nobody online | 20260814-0003 (customer words) + **synthetic** staffing state | §9.1: nobody stated in danger → a normal booking, no emergency line, no P1 case (WP-3) |
| 14b | No cooling, and "my mother is 88 and it's 95 degrees in here" | **Synthetic** variant of 20260814-0003 | §9.1: emergency-line direction with the placeholder number first; emergency-priority case; the one-business-day line is separate and never framed as the emergency wait |
| 15 | Reschedule inside 24 hours, then the customer contests the fee | 20260902-0001 + **synthetic** contest | §9.3 (revised): fee explained; the appointment is **not** moved, even on a yes; a P2 staff change request due at the window start; "original stays" and "can't promise before your appointment" lines; no waiver; nothing called "charged" |

The transcripts give the customer's words. Expected facts come from the current KB and DB, never from the human agent's
answer (audit D-5). Gold labels are written before any run.

### What is tested, pass criteria and likely failure modes

| Test | How | Pass criteria | Likely failure modes |
|---|---|---|---|
| **Triage extraction** | Generate the brief for each case; compare with gold labels per reason (C2 table) | ≥90% of required items present; **0 invented facts**; **0 claims under "What we know for sure"**; reason correct in 15 of 15 | Filler quoted as a need; the compressor case's "Let's schedule it then" missed; paraphrased amounts ("about $60"); a claim promoted to a fact |
| **Brief readability and use** | Flesch–Kincaid estimate on bullet text (exact identifiers excluded); then a scripted walkthrough: 3–5 readers (Innocent and peers, labelled as non-staff) answer four questions per brief: what does the customer want, what is verified, what was promised, what must you decide; and say their first action | Mean estimated grade ≤6; ≥90% of answers correct; median time to first action ≤60 s; readers ask for information already in the conversation in ≤1 of 15 cases | Simplified wording that changes meaning ("1 business day" → "soon"); headings ignored under time pressure; the score passes but answers fail |
| **Source verification** | For each fact, open snapshot and current record; a person checks the source supports the fact; inject one record change after snapshot and one unsupported citation | ≥95% of facts supported by their cited source; injected change shows "changed since" in 100%; the injected bad citation is caught by ≥2 of 3 readers | Archived passage cited (audit K-6, K-8); passage-level link too coarse to verify; stale snapshot read as current |
| **Case visibility** | Create the 15 cases with a simulated clock; toggle staffing (on, busy, ending); advance time | Every unowned, due-soon and overdue case appears in the supervisor list at the right time; staffing-end converts live-queued cases and shows the one-business-day commitment; with nobody online, no live queue is offered (0 occurrences); the AI sends nothing while a person owns the chat; promise-kept correct in 100%; promise text matches the policy table in 100% | Clock or time-zone mismatch; weekend and business-hour errors in due times (2026-10-16 is a Friday); fake queue position; a case lost in transition |

**The honest limit.** Readers are not Meridian representatives, and every time is simulated. The spike can show the format
is understandable and the mechanics are correct. It cannot show real handle-time savings. The demo and README should say
so (direction §10).

---

## 8. Prototype versus later product, risks and decisions

### How the reviewer environment works (decided: OD-1, OD-2, OD-3) [Innocent, detailed by Inference]

**Honest default.** The representative-presence state is **nobody online**. A reviewer who never touches the simulation sees
exactly what a customer would see after hours: the follow-up commitment, a reference and contact capture. No queue, no
"someone will join shortly".

**Entering the simulation.** A clearly labelled control ("Demo: simulate staff on shift") turns on a simulated staffed
state. While it is on, a persistent banner in **both** the customer chat and the staff console says "Simulated staffing
(demo). No Meridian employee is online." The reviewer can end the simulated shift at any time, which exercises the
staffing-ended path.

**Playing both roles.** The reviewer uses **two sessions**: the customer chat in one tab, the staff console in another
(a split view or a role switch is a fallback for small screens). Customer and staff access stay visibly distinct:
- **Separate entry points**, e.g. the chat at the public URL and the console at a staff route behind a demo staff sign-in.
- **Different chrome:** the console has its own header and label ("Staff console · demo representative"), so the two
  are never confused.
- **Customer sessions cannot reach staff data**; the staff console needs the demo staff sign-in.

The demo representative has a labelled name ("Riley (demo representative)"). What the reviewer types as Riley is sent for
real into the same conversation. Only the staffing is simulated.

**Same conversation, AI paused (OD-2).** When the reviewer claims a live-queued case and joins:
- the customer sees "Riley (demo representative) has joined";
- the AI stops generating replies;
- customer messages go to the representative;
- the representative sees the brief, the pertinent sources and the full conversation.

Handing the chat back to the AI, or closing it, is an explicit action that the customer can see.

**Contact-code verification (OD-3 = audit DEC-3).**
1. **Public questions and safety need no code.** Prices, membership terms, hours, service area and the safety instruction
   are always available.
2. **Locate, then verify.** For private details (invoices, appointments, membership dates) or account changes (booking,
   rescheduling, cancelling), the AI first locates the record from what the customer gives: name with phone, a customer
   ID or an invoice reference. **A locator is not proof of identity.**
3. **Send a code to a contact already on the record.** The system generates a one-time code for the phone or email in
   `customers.phone` / `customers.email`. Every one of the 154 records has both (`customers`). The customer sees only a
   masked hint ("the phone ending in 02"). Showing the hint is a design default to test against the risk that it confirms an
   account exists.
4. **Simulated delivery.** No real SMS or email is sent. The code is delivered to a separate, clearly labelled **demo
   delivery inbox** ("Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete
   verification."). It is never shown in the customer chat.
5. **Entry and limits [Inference].** The customer types the code in chat. Proposed defaults:
   - the code expires after 10 minutes;
   - 3 wrong attempts end the attempt;
   - a cap on codes sent per conversation;
   - verification lasts for the session and covers only that customer ID;
   - the code is stored hashed and never placed in model context, logs or traces (audit G-9).
6. **No match, ambiguous match, no usable contact, or failed code:** route to a person without revealing whether an
   account exists or showing any account detail ("I can't confirm your account here. A representative will help").
7. **Labelling.** This is a **demo simulation of contact-based verification, not production-grade identity proof.**
   Production would need real delivery with consent (audit L-9), fraud controls and a security review. The verification
   inbox carries codes only; it is **not** a follow-up channel (OD-5).

**Seeded oversight data [Inference].** For the supervisor and business-owner views to show unowned, due-soon and overdue
work, the case store starts with a few labelled demo cases (built from inventory cases, marked "demo seed"). The views run
on the fixed clock (2026-10-16), with a labelled "advance simulated time" control in the supervisor view.

### Prototype versus later product

| Capability | In the prototype (the PRD still decides scope) | Later product |
|---|---|---|
| C1 Human access | Visible "Talk to a person"; immediate handoff; failure-signal offers (OD-6 hypotheses). **Default nobody online**; the live queue only inside the labelled simulation (OD-1) | Real presence and shifts; measured wait estimates; routing by skill |
| Same-conversation takeover | **In scope (OD-2):** reviewer claims, joins, replies; AI paused; hand-back | Multiple concurrent representatives; transfer between teams |
| Identity | **Simulated contact code to the record's phone or email, demo inbox (OD-3)** | Real SMS or email delivery with consent; stronger verification; fraud controls |
| C2 Triage brief | Eight-heading brief from state plus constrained extraction; full log link | Incremental notes during long conversations (S-140) |
| C3 Ownership | Case store beside the working DB copy; states, promise record; supervisor and owner views on seeded and live cases; simulated clock | Notifications, workload balancing, staffing forecasts |
| C4 Sources | Lookup log; snapshot and current values for invoice, appointment, customer fields and KB passages; demo staff sign-in | Role-based access tied to real staff accounts; retention rules |
| C5 Outcomes | Outcome on close and a flag list | Reviewed corrections promoted into KB fixes and eval cases |
| Follow-up delivery | Commitment, reference and the customer's channel choice (email default, or phone), destination and window captured; the representative's follow-up activity is **recorded and labelled "Demo: recorded, not sent"** (§9.5) | Real email and phone follow-up, with consent where needed |
| Urgent comfort | When someone is stated to be in danger: emergency-line direction using the placeholder emergency number (512) 555-0199; emergency-priority case (§9.1) | Meridian's real emergency number in place of the placeholder |
| Voice | **Out of scope here.** The baseline is chat (Part B). If voice is attempted, the same case and brief apply, with recording-consent and identity issues (audit L-5) | Telephony |

**Never shown as real in the reviewer environment:**
- a Meridian employee being online (the only person who joins is the reviewer, labelled as a demo representative);
- a queue position or wait estimate without measured data;
- a real SMS or email (the inbox is labelled as simulation);
- a follow-up call or message being made;
- a payment link or auto-renew change being performed (inventory §5.2).

### Risks

- **Implied staffing.** Mitigated by the default and the banner, but the most likely reviewer trap (audit E-5).
- **The demo inbox is visible to anyone using the demo.** Acceptable only because the data is fictional and the
  mechanism is labelled; it must never be described as identity proof.
- **Masked-contact hints** can confirm that an account exists. Test the wording (§7 case 13).
- **Automation bias** in the brief (S-160, S-161, S-162). §7 tests it.
- **The emergency number is a fictional placeholder** ((512) 555-0199). It is safe in the demo because the 555-01xx range
  reaches no one, but it must be replaced before real use (§9.1).
- **Scope creep:** OD-1 and OD-2 add a staff console and a takeover path to a 2–3 day build. The cut order in §2 still
  applies, and takeover cannot be cut without reopening OD-2.
- **Synthetic-only triggers and evidence transfer** (unchanged from the original §11).

### Decisions (as of 2026-10-20)

**OD-1. Reviewer simulation and audience views. Decided.** The reviewer can explore a clearly labelled simulated staffed
state as well as the unstaffed path. The default is unstaffed. The prototype includes customer chat, the representative
queue and case view, the supervisor view and the business-owner view (§6 table, this section). [Innocent]

**OD-2. A person joins the same chat. Decided, in scope for the intended demo.** The reviewer starts as a customer, requests
a person, enters the representative experience, claims the handoff and replies in the same conversation. The AI pauses
visibly. Only staffing is simulated. [Innocent]

**OD-3 (= audit DEC-3). Simulated contact-code verification. Decided for the demo.** It replaces the earlier recommendation
of "name + phone + one more fact". Mechanism above. [Innocent]

**OD-4. Promise wording. Decided** (rounds 1–3, Innocent, 2026-10-20).
- **(i)** When nobody is online, including when staffing ends before a claim: "A representative will get back to you within
  1 business day" (`policies/escalation_and_safety.md`).
- **(ii)** No heat, no cooling or an active leak **where the customer says someone is in danger because of it**: direct the
  customer to the 24/7 emergency number, create an emergency-priority case, and, if nobody is online, state
  **separately** that the online case will be reviewed within 1 business day, never as the emergency wait. Without a
  stated danger, it is a normal booking (§9.1). *Narrowed at the Stage 2 check, Innocent, 2026-10-20 (WP-3).*
- **(iii)** Safety: the instruction comes before anything; contact capture is offered afterwards; **no follow-up time is
  promised** (round 3).
- **(iv)** **Refund requests:** "A representative will get to your refund request within 2 business days" (round 3). This
  is the time for a person to **respond**, not a promise to refund or about the refund's outcome. It departs from the
  written KB, which says supervisor callback within 1 business day for refunds (`policies/escalation_and_safety.md`).
  This is Innocent's product choice, recorded as such.
- **(v)** **Complaints, disputes and manager requests** keep the written 1 business day [Inference: Innocent gave no
  different time for these, so the policy stands].
- **(vi)** **Staffed path and role label:** "A representative will join this chat when available", with no time unless
  measured. The customer is always told "a representative", never a specific role title (round 3).
- **(vii)** **Active plumbing leaks:** no containment advice beyond the KB's indoor-unit step; point to the emergency
  number (round 3).
- **(viii)** Emergency number: the fictional placeholder (512) 555-0199 for the demo; the real number is needed before
  real use.
- **(ix)** No refund, waiver, technician arrival time or emergency-line response time is promised without policy support.

**OD-5. Follow-up. Decided** (round 2, Innocent, 2026-10-20).
- When nobody is online: a follow-up case, the commitment, a reference and contact capture.
- **Email is the default follow-up**; the customer is asked to choose phone or email.
- The choice, the destination and the window are stored on the case and shown beside the commitment.
- The prototype records follow-up activity, labelled as a demo, and never sends anything (§9.5).
- *Still open:* none at product level. The privacy rule for destinations not on record is a proposal (§9.5).

**OD-6. Failure-signal thresholds. Decided as a starting point.** The two-attempt thresholds (C1) are hypotheses for
labelled synthetic tests and may change after evaluation. A direct request for a person triggers on the first request.
Safety comes first. [Innocent]

**Round-2 decisions** (D2–D6, DEC-1, DEC-2, DEC-4, DEC-5, Q-1–Q-3, the deadline, LangGraph and process items) are in §9
and §11.

---

## 9. Urgent cases, safety, fees, unsupported requests and scope (decided 2026-10-20)

Innocent made these choices on 2026-10-20. Each subsection keeps four things apart: **issued policy [Meridian]**,
**transcript observations [Meridian]**, **Innocent's choice [Innocent]** and **my proposed handling [Inference]**. Nothing
here is implemented.

### 9.1 Urgent comfort cases: no heat, no cooling, active leak (OD-4)

**Issued policy [Meridian].** "After-hours emergency line: available 24/7 for no-heat, no-cool, and active water leaks"
(`faq/customer_faq.md`). After-hours dispatch is $149 for non-members and waived for members (`2026_fee_schedule.pdf`). **No
KB file gives the emergency line's phone number**, and none states its response time (checked across all 17 files).
**Transcripts [Meridian]:** 132 booking calls; no caller states an indoor temperature or a vulnerable occupant, and agents
book these as "non-emergency" (inventory §3.2, §3.4).

**Innocent's choice, as narrowed at the Stage 2 check [Innocent, 2026-10-20].** The urgent path applies "only … if
they're stating its an emergency as in someone is in danger as a result of the conditions described" (WP-3 check).

- **No heat, no cooling or a leak, and nobody stated to be in danger:** a **normal booking**. No emergency number, no
  emergency-priority case. The agent may still say the 24/7 line exists if the customer asks about after-hours help
  (it is a public KB fact).
- **Someone stated to be in danger because of the conditions** (for example an older person in a very hot house, a
  baby in the cold, water reaching electrics), the agent:
  1. tells them Meridian has a 24/7 emergency line for this and directs them to contact it;
  2. creates an **emergency-priority case**, visible at the top of the representative and supervisor views;
  3. if no representative is online, states **separately** that someone will review the online case within one business
     day, without implying that this is the wait for urgent help or dispatch.

**Why it changed.** The first version (round 2) sent every such report down the urgent path. About 53 of the 75 HVAC
booking calls report no heat, no cooling or water pooling (inventory §3.2), so most bookings would have become P1
cases for staff to review, and the emergency number would have been shown to customers who only needed a visit.

**Customer wording on the urgent path (proposal) [Inference]:**

> Because someone may be in danger, please call Meridian's 24/7 emergency number now: **(512) 555-0199**.
> I've also logged this for our team as an emergency-priority request. No representative is online right now, so someone
> will review this online request within 1 business day. That is not the wait for emergency help; for that, please use
> the emergency line.

**Urgency questions (round 3, Innocent: yes; place changed at the Stage 2 check).** In the booking for no heat, no
cooling or a leak, the agent asks briefly, and the customer can skip them:
- "Is it very hot or very cold in your home right now?"
- "Is water still running?"
- "Is anyone at higher risk, like an older person, a baby or someone unwell?"

Answers go into the booking note. If the answer says someone is in danger, the urgent path above runs at once. A
customer who says so unprompted gets the urgent path without the questions.

**Proposed handling [Inference].**
- **The emergency number is a fictional placeholder** (Innocent, 2026-10-20, later the same session): **(512)
  555-0199**.
  - The issued KB gives no number, so one was chosen. Numbers 555-0100 to 555-0199 are reserved for fictional use and
    reach no one; the dataset's seeded customers use the same style (`SCHEMA.md`).
  - Customers see it simply as "the emergency number". It is one configuration value, recorded here as a placeholder.
  - It must be replaced with Meridian's real line before any real use. A call button may point to it in the demo.
- On the urgent path, if a representative is online, the case goes to the top of the live queue and the customer is
  offered a person immediately.
- The agent may state the after-hours fee if asked (it is policy).
- It promises **no** arrival time, dispatch time or emergency-line response time (none is in policy).
- For water at the indoor unit, it may repeat the KB step "Turn the system off to prevent overflow damage"
  (`faq/troubleshooting_before_you_call.md`).
- For other active leaks it gives no shutoff advice, because the KB has none (see OD-4 open item (f)).
- Offering the earliest regular appointment as an *additional* option is allowed. It must be labelled as a regular
  booking, not emergency service.

### 9.2 Safety cases and the burning-smell gap (D2, D5)

**Issued policy [Meridian].** Gas or rotten-egg smell, CO alarm, visible sparks/smoke/flames, or "electrical burning smell
combined with tripped breakers": leave the home immediately, call 911 or the gas utility from outside, flag the account
as a priority emergency; do not flip switches, open windows near the furnace or restart equipment
(`policies/escalation_and_safety.md`).

**Safety order [Innocent].** The safety instruction comes **before** chat triage, identity checks, a queue or a Meridian
case.

**After the instruction (D5) [Innocent]:**
- The agent offers to take a callback number or other contact details. This is never a condition for the instruction.
- A **safety-priority case** is created even when the caller cannot be matched to an account. Its brief carries the
  trigger words, the instruction shown and its time.

**Burning smell with no breaker information (D2) [Innocent].** This is a proposed handling of a **policy gap**. The
transcripts don't establish it: all 16 such calls were booked as routine, and none mentions breakers (inventory §3.2).
1. Ask whether any breakers have **already** tripped, and whether they see smoke, sparks or flames. Do **not** ask them to
   inspect or flip anything: "Do you already know whether a breaker has tripped? Please don't go to the panel to check.
   Do you see any smoke, sparks or flames?"
2. **Yes to either:** give the KB safety instruction immediately, then follow D5.
3. **Can't tell, and the risk stays unclear:** the cautious path [Inference]:
   - say plainly that a burning smell can be serious;
   - give the KB's trigger list as a conditional instruction ("If you smell gas, see smoke, sparks or flames, or a breaker
     has tripped, leave the home immediately and call 911 from outside");
   - direct them to the 24/7 emergency line;
   - create an emergency-priority case.
   It is never treated as routine.
4. **Only when both are clearly ruled out:** offer the earliest booking, marked urgent, and create a priority case so
   staff see it.

### 9.3 Reschedule fee and no waivers (D3 = DEC-2, one decision)

**Issued policy [Meridian].** Cancelling or rescheduling inside 24 hours of the window costs $49, for every tier
(`faq/customer_faq.md`, `2026_fee_schedule.pdf`). The internal notes let **human** agents waive it once per customer per
year for a documented reason, waive the diagnostic fee for a technician more than 30 minutes late, and give a 10%
courtesy discount (`internal/agent_discretion_notes.md`). **Transcripts [Meridian]:** 14 of 15 reschedules were inside
24 hours and no agent mentioned the fee (inventory §5.3).

**Innocent's choice [Innocent]. The AI never grants a fee waiver or a discount, of any kind** (round 2; unchanged).

**Revised at the Stage 3 review (Innocent, 2026-10-20): the AI never makes a change that carries the fee.** This replaces
round 2's "state the fee, ask whether to go ahead, then make the change". For a reschedule inside the 24-hour window
(computed from the fixed clock and the window start), the AI:
1. verifies the customer (OD-3);
2. explains the fee: "Under our current policy, a $49 late-change fee applies to changes within 24 hours of your
   appointment window." It never says the fee "has been charged";
3. **does not move the appointment, even if the customer says yes.** It records the requested change for a
   representative: the appointment (`appointments` + `appointment_slots`), the time the customer wants instead, any open
   slots it showed (shown, **not held**), the customer's reason and the hours before the window;
4. says plainly that the original appointment stays in place until a person confirms a change;
5. hands off. **A request sent to staff is a handoff, not an AI-resolved appointment change**, and it counts as an
   escalation in every metric;
6. if the customer contests the fee: staff can review the circumstances, no promise that it will be lifted, and the
   reason goes into the same case.

**Changes with no fee** (more than 24 hours before the window): the AI reschedules itself, under the normal booking rules
(PRD R-18, R-19).

**The prompt staff path [Innocent asked for it; design Proposed, delegated].** In WP-4 the visit starts two hours after
the chat, so the one-business-day promise alone can't help. Where possible, the request reaches a person sooner:
- **The due time is the window start.** The case is **P2 time-sensitive**, and its internal due time is the start of the
  appointment window, not one business day. The supervisor view alerts at once, and the case sorts above other P2 cases
  by due time. This is a staff target, not a promise to the customer.
- **Someone online (the labelled simulation):** the customer is offered the live queue first; the case sits at the top
  after P0 and P1.
- **Phone support open:** if phone support is open at that moment (`faq/customer_faq.md`: Monday–Friday 7:00am–7:00pm,
  Saturday 8:00am–4:00pm), the reply adds that they can also call phone support. The KB gives no phone number, so none
  is shown or invented.
- **Nobody online (the default):** the customer gets the standard promise from the policy table *and* a plain warning
  whenever the window starts before that promise could be met.

**Customer wording, WP-4, nobody online (proposal) [Inference]:**

> Under our current policy, a $49 late-change fee applies to changes within 24 hours of your appointment window. I can't
> make that change from this chat, so I've sent your request to move it to Monday morning to a representative, marked
> urgent. Your appointment today, 12–4pm, stays in place until a representative confirms a change. Your appointment starts in about 2 hours and nobody is online right now, so I can't promise anyone will
> confirm a change before then. Until they do, please plan on the technician arriving 12–4pm. Phone support is open until
> 7pm today if you'd like to call. A representative will get back to you within 1 business day. Your reference is …

**Cancellation inside 24 hours [Innocent, 2026-10-20: "yes"]:** handled the same way. The same $49 applies, so the AI
explains the fee, never cancels, sends a staff request, and says the appointment stays until a person confirms. A
cancellation more than 24 hours out is free, and the AI makes it. (All 6 issued cancel calls were more than 24 hours out,
inventory §4, so coverage is unchanged.)

**Not a waiver [Inference].** When a technician has *already missed* the window, `services/technician_arrival_and_etas.md`
says to offer a reschedule at no charge. That is the written outcome for a missed window, not discretion, so the AI may
offer it. It may **not** offer the diagnostic-fee waiver from the same file; that goes to staff.

### 9.4 Requests the issued systems cannot complete (D4)

**Innocent's choice [Innocent].** Serious cases get human priority. An informational limit does not become an urgent case.
An explicit request for a person is always honoured. An unfinished customer task never ends with only "Sorry, I don't have
access."

**The boundary with the brief.** Part B §4 says "Anything outside the handled call drivers routes to a human." This
section keeps that: every **unfinished task** gets a case. Only questions that can be **fully answered within limits**
end without one, and the customer is still offered a person. Nothing here silently narrows the brief.

**Priority classes [Inference]:**
- **P0 safety:** immediate;
- **P1 emergency-priority:** urgent comfort with someone stated to be in danger, or a burning smell with unclear risk;
- **P2 time-sensitive:** a deadline the customer could miss;
- **P3 standard:** policy says a person;
- **P4 routine follow-up:** an unfinished action, no deadline;
- **No case:** fully answered.

When nobody is online, every case-creating row also tells the customer "within 1 business day" (OD-4 settled wording).

| Request (inventory evidence) | What the AI can truthfully do | What is unavailable | Kind | Customer wording (proposal) | Case |
|---|---|---|---|---|---|
| **Pay an invoice** (BILL-PAY 14; §5.2) | After the code: read the balance and due date (`invoices`); say cards are never taken in chat (`faq/customer_faq.md`) | Payment links, any payment system | Unfinished service action (FAQ: agents send links) | "I can't send a payment link from this chat. I've asked a representative to send you a secure payment link." | **P4**; due date in the brief; P2 if the invoice is past due |
| **Set up autopay** (BILL-AUTOPAY 14) | Say the KB has no autopay information | Autopay setup; any portal (not in the KB) | Unfinished action, no policy | "I can't set up autopay here, and I don't have details on autopay options. Would you like a representative to follow up?" | **P4 only if the customer accepts** |
| **Turn off auto-renew** (MEM-CANCEL 13) | After the code: read `membership_renewal_date` and tier; explain the cancellation rules (`membership/comfort_club_overview.md`) | An auto-renew flag; any membership-billing record | Unfinished action that policy says agents can do; no obstruction (audit E-2) | "I can't switch off auto-renewal from this chat. I've created a request for a representative to do it before your renewal date of [date]." | **P2** if renewal falls within the follow-up window, else **P3** |
| **Upgrade to Plus** (MEM-UPGRADE 6) | Explain the $80 difference, prorated for months left (membership doc) | Collecting the prorated payment; the term start needed to prorate exactly | Unfinished sale | "A representative can complete the upgrade and the prorated payment." | **P4**; the AI does not change `membership_tier` without payment |
| **Duplicate charge** (BILL-DUP 11) | Give the FAQ explanation: a pending hold usually drops in 3–5 business days; if both post, a case is opened with the processor | Card or processor records | Limited answer; becomes a case if both have posted | Explanation first; if both posted: "I've asked our billing team to open a case with our payment processor." | **None** at first; **P3** if both posted; a dispute → supervisor (P3) |
| **Registration check** (WAR-REGISTER 10; WAR-PARTS 7) | State the policy: registered within 30 days; registration needed for the full parts term (`warranty/warranty_policy.md`) | Any registration record | Limited answer, plus an optional confirmation request | "I can't see registration records. Our policy is to register every install within 30 days. Want a representative to confirm yours?" | **P4 only if accepted** |
| **Repeat repair under warranty** (WAR-REPEAT 6) | State the 1-year same-part labor warranty; book a diagnostic visit (`appointment_slots`), noting the claimed earlier repair in `issue_description` | Repair history (no completed appointments in the DB) | Booking possible; coverage needs a person | "I've booked the visit. The technician confirms warranty coverage; if it isn't covered, the standard $89 diagnostic applies." | **P4** for staff to check history; the AI does not set `is_warranty_visit` on a claim |
| **Install-warranty term** (WAR-CLAIM 14) | Read `system_install_date`; state 2-year install labor, and 5 years if a member *at install* | Membership enrollment date | Limited answer | "You're within the 2-year install labor warranty. If you were a member when it was installed, it may be 5 years; a representative can confirm." | **None** unless a booking or a confirmation is wanted |
| **Itemized copy by email** (BILL-EXPLAIN 13) | After the code: show the line items in chat | Sending email | Limited answer is enough | Line items in chat; "I can't email it from here. A representative can, if you'd like." | **P4 only if accepted** |
| **Late technician** (SCH-LATE 9) | Read the window; quote policy: not required to wait past the window, never charged as a no-show; offer a reschedule at no charge (§9.3) | Dispatch, ETA, the fee-waiver decision | Time-sensitive service failure | "I can't see where the technician is. Under our policy you don't have to wait past your window. I can reschedule you at no charge, and I've flagged this for our team." | **P2** |
| **Waitlist / earlier slot** (34 booking calls) | Offer the earliest matching slot and alternatives | A waitlist (only in the outdated scheduling guide) | Limited answer; urgent ones go to §9.1 | "That's the earliest I can book. I can't add you to a waitlist from here." | **None**, unless urgent (P1) or the customer asks for a person |
| **Quote vs invoice** (BILL-DISPUTE 16) | Explain the invoice lines | Verbal-quote records | Policy requires a supervisor | §5 brief example | **P3** |
| **Refund** (BILL-REFUND 8) | Nothing beyond routing | Refund authority (the AI may not refund) | Policy requires a person | "A representative will get to your refund request within 2 business days. I can't promise an outcome." | **P3** |
| **Commercial quote** (COMMERCIAL 5) | Redirect per policy | A link to the commercial division | Safe redirect with a policy callback | "Commercial projects are handled by Meridian Commercial. I've passed on your details for an estimator." | **P3**, routed to commercial |
| **Job inquiry** (HIRING 6) | Careers-page redirect; applications aren't taken by chat (policy) | A careers inbox | Safe redirect | "Please apply through the careers page on our website." | **None** |

**Also in the KB but in 0 calls:** duct-cleaning referral (catalog says ask for a referral; the process is a stub) and
financing (FAQ). For both: a limited answer plus an optional P4 case. They are listed for completeness, not as
observed demand.

### 9.5 Follow-up channel (OD-5)

**Innocent's choice [Innocent].** In the intended product, **email is the default follow-up**, and the customer is asked
whether they prefer **phone or email**. The case stores the choice, the destination and any callback window. The
representative and supervisor views show them **beside the exact commitment**.

**Customer wording (proposal):** "We'll follow up by email unless you'd prefer a phone call. Which works best?" Then confirm
the destination.

**Privacy rule for the destination [Inference]:**
- If the follow-up will contain **private account information**, it goes only to a phone or email **already on the record**
  after the code (OD-3), or staff verify the customer again before sharing.
- A new destination given in chat is stored and marked **"not on record"** in the case.
- For an unmatched or unverified customer, the follow-up stays general until staff verify.

**Prototype [Inference].**
- Nothing is sent or placed. The case records the selected channel and the representative's follow-up activity, labelled
  "Demo: recorded, not sent".
- The interface never says an email was sent or a call was placed.
- The **OD-3 code inbox is a different thing**: it carries verification codes only, never follow-ups.

### 9.6 Conversation history and source snapshots (D6)

**Decided [Innocent].** The **full chat history** is available in the staff case and the monitoring views. Access is limited
by role, and redaction is applied:
- card-like numbers are masked;
- verification codes are never stored in the transcript.

**Snapshots (round 3, delegated to Claude's recommendation).** Store a minimal snapshot of only the fields the AI
used (invoice lines and amounts, appointment window, the policy passage text with file and version, tool results) on the
case. Keep it for the life of the case, then **delete it 90 days after the case closes**. The full chat history follows
the same retention unless a later policy sets another. This is a proposed default for the product; in the prototype the
demo data is reset instead.

### 9.7 Scope, corpus and project decisions

- **DEC-1 scheduling (partly decided) [Innocent].** Build and verify the required availability check, booking and
  alternatives flow first. Then add **reschedule, then confirm, then cancel**, in that order, as time allows (round 3, delegated to Claude's
  recommendation; transcript counts 15 / 8 / 6, inventory §3.2). A reschedule follows the §9.3 fee rule.
- **DEC-4 corpus (decided) [Innocent].**
  - Exclude `archive/comfort_club_overview.md`, `archive/warranty_terms_2023.txt` and `faq/faq_old_copy.md` from the
    **retrieval corpus**. The issued files are not edited or deleted.
  - An ingestion manifest records each excluded file and the reason (audit K-1, K-2, K-4, K-6–K-10).
  - Eval cases must prove the agent never answers from them, for example:
    - "How much is the Comfort Club?" → $189 (not $149);
    - "How long is the repair warranty?" → 1 year (not 90 days);
    - "What's the diagnostic fee?" → $89 (not $79);
    - "Can I cancel any time for a full refund?" → current rules;
    - "What are your phone hours?" → Mon–Fri 7–7, Sat 8–4.
  - **`services/scheduling_guide.md` (Rev 2024-11) is excluded too** (round 3). Its useful content, the emergency
    thresholds (no-cool above 85°F indoors, no-heat below 55°F) and the waitlist mention, is kept in our own notes as
    **labelled known gaps**, never as an answer source. Its 48-hour cancellation rule contradicts the current 24-hour
    rule.
- **DEC-5 voice (decided) [Innocent].** Out of the current scope. Revisit only if the chat agent, the handoff flow and the
  required evaluation finish early. Voice may not delay the baseline.
- **Partner questions, answered by Innocent (no partner answer recorded) [Innocent]:**
  - **Q-1:** yes, include the issued dataset in the submitted repository, and the repository is **public** (round 3).
    *Risk on record:* the dataset carries no licence and nothing in the brief grants redistribution (audit L-8).
    Publishing it is Innocent's call. It is noted here so it is a known choice, not an oversight.
  - **Q-2:** the reviewer tests against **our deployed database copy**, so we own its reset path.
  - **Q-3:** yes, Dripping Springs (78620) and Manor (78653) are bookable. Because `SCHEMA.md` maps no zone for them, the
    booking code needs a zone for each. **Decided (round 3):** both map to `central`, configured in our code;
    the issued schema is not edited.
- **Deadline (GQ-20).** Innocent's internal target is to finish by **Wed 2026-10-21, 06:00 CT**, recorded in
  `SUBMISSION.md`. The partner's own deadline is still unconfirmed.
- **Delegated or accepted [Innocent]:**
  - **LangGraph:** confirmed (§10).
  - **Case store:** new tables beside the working DB copy (accepted).
  - **Handoff lanes:** Claude decides after Stage 2 ("whatever makes sense").
  - **Demo defaults** (code expiry, attempts, hint format): the proposed defaults stand ("don't worry about that").

---

## 10. Service-agent needs and the LangGraph design

**Status. Decided:** LangGraph is the framework for conversation state, tool use and human handoff (Innocent, 2026-10-20,
confirmed in round 2). It supersedes the original note's "LangGraph … explicitly not a requirement" (direction §9) for
planning. **Nothing is built.**
The needs below were defined independently of the framework (§3–§8). This section notes only where they shape the graph.
API names are LangGraph's general concepts. Confirm each against the pinned version at Stage 6 design, where the
decided framework is written up as a design decision with its rejected alternative.

| Service-agent need | Where it comes from | What it means for the LangGraph design [Inference] |
|---|---|---|
| **One durable conversation across AI and human turns** | OD-2; C2 (full log) | One thread per conversation, with a durable checkpointer keyed by `thread_id`, so the conversation survives a handoff, a pause and a resume (`agent-architecture.md` rule 18). The customer, the AI and the representative all write to the same message history |
| **The AI pauses while a person owns the chat** | OD-2; §6 "In progress" | Model control as a **typed state field** (e.g. `controller: ai \| human`) read by a pure router at graph entry (rules 12–13). While `human`, a customer message is appended and routed to the staff side; no model node runs. Representative messages are written into the same thread, for example with a state update. Prefer this to holding one graph run suspended for hours with `interrupt()`. Keep `interrupt()` for short approval gates such as confirming a booking write (rule 17) |
| **Safety before everything** | K-12; E-3; C1 | A deterministic safety-check node first on every turn, before any model, tool or queue node (rules 1, 13). Its output is the instruction text, not a model paraphrase |
| **A direct request for a person on the first ask** | C1; OD-6 | Detected by code and a cheap classifier before tool use. It routes straight to the handoff node, never through a retry loop |
| **Failure signals** | C1; OD-6 | Counters in typed state (failed answers, tool failures, identity failures, corrections), each bounded (rule 15). Thresholds come from configuration, so they can change after evaluation without editing nodes |
| **Identity gates private reads and writes** | OD-3 | Verification state in graph state (`unverified → code_sent → verified(customer_id, expires)`). Tools that read private records or change bookings check it **in code** in the tool guard node, not in the prompt (rule 17; `agent-tools.md`). The model sees only the status, never the code. Code generation and the demo inbox are an application service the graph calls |
| **Honest presence and routing** | C1; OD-1; OD-5 | The representative-presence state lives in the application, outside the graph. A routing node reads it at handoff time and branches: live queue, or follow-up commitment. With nobody online, the live-queue branch is unreachable |
| **Cases outlive conversations** | C3 | Cases, the promise record, owners, due times and alerts live in the **application's case store**, not in graph state. The graph's handoff node creates the case (idempotently, rule 18) and links the `thread_id`. Due-soon and overdue alerts come from a scheduled job on the fixed clock, not from a graph run |
| **Auditable lookup log** | C4 | Every tool call goes through one wrapper that writes a lookup-log row: tool, record or passage ID, time, result seen, message ID. The checkpoint history holds full state and is **not** the audit log; it has different retention and privacy needs (audit G-9) |
| **A brief assembled from state** | C2 | A handoff node builds a typed `Brief` object (rule 3): headings 1, 3, 5, 6 and 8 from state and the lookup log, and 2, 4 and 7 from a constrained structured-output extraction step. The brief is stored with the case, not regenerated on each view |
| **The promise comes from policy** | C3; OD-4 | A policy-table lookup in code (rule 1) produces the promise text and due time from the reason, the presence state and the fixed clock. The model may not write the promise |
| **Priority and urgent routing** | §9.1, §9.2, §9.4 | Priority (P0–P4) set by a deterministic node from typed triggers, before any model wording; the urgent-comfort and burning-smell paths are fixed branches, not model choices (rules 1, 13) |
| **A fee-bearing change is never written by the AI** | §9.3 (revised at Stage 3) | The 24-hour check is code on the fixed clock. The scheduling tool refuses a change inside 24 hours and returns a "staff change request" flag, which the escalation check turns into a P2 handoff due at the window start. Fee-free changes are written after the customer confirms the slot. No waiver tool exists for the model to call |
| **Follow-up preference on the case** | §9.5 | Captured as typed fields (channel, destination, on-record flag, window) and written to the case store, not left in free text |
| **Fixed clock** | Audit C-9 | The clock is injected through run configuration, never read from the server inside nodes |
| **Brakes and cost** | Rules 5, 15, 20 | Explicit `recursion_limit`, iteration, time and spend brakes per run. Handoff is the graceful outcome when a brake fires |
| **Voice later** | Part B extra credit | The same graph and case flow should serve a voice front end later. Nothing in the chat design should depend on screen-only features |

**What the framework does not decide.** Who owns a case, what is promised, what counts as verified, and what a
representative sees are product rules. They are enforced by application code and the policy table. Whichever framework is
used, they stay the same.

---

## 11. Decision status

All choices are Innocent's, 2026-10-20. "Recorded in" names the owning document and section.

| ID | Status | Innocent's choice | Still open | Recorded in |
|---|---|---|---|---|
| **OD-1** Simulation and views | Decided | Default unstaffed; labelled simulated staffed state; customer, representative, supervisor and owner views | — | This doc §6, §8 |
| **OD-2** Same-chat takeover | Decided | Reviewer claims and replies as a labelled demo representative; AI paused | — | §4, §6, §8 |
| **OD-3 / DEC-3** Identity | Decided (demo) | Simulated one-time code to the record's phone or email; labelled demo inbox | Demo defaults delegated (proposed values stand) | §8; audit §9 |
| **OD-4** Promises | Decided | Unstaffed: 1 business day; refund requests: a representative gets to them within 2 business days (response, not refund); complaints and disputes: 1 business day; staffed: "a representative will join when available"; role always "a representative"; urgent path (emergency number, P1) only when the customer says someone is in danger (narrowed at the Stage 2 check, WP-3); safety: no follow-up time; no leak advice beyond the KB | Real emergency number before real use | §8 OD-4, §9.1 |
| **OD-5** Follow-up | Decided | Email default; customer chooses phone or email; stored and shown beside the commitment; prototype records only | — | §8 OD-5, §9.5 |
| **OD-6** Failure thresholds | Decided (starting point) | Two-attempt hypotheses, tested on synthetic cases | Tuning after evaluation | §3 C1, §8 |
| **D2** Burning smell | Decided (direction); handling proposed | Ask about breakers *already* tripped and smoke, sparks or flames; instruct if yes; cautious escalation if unclear; booking only when ruled out | Policy owner confirmation of the gap handling | §9.2; inventory §10.4 |
| **D3 = DEC-2** Fees and waivers | Decided (revised at Stage 3, 2026-10-20) | Inside 24h the AI explains the $49 fee but never moves the appointment: it records a P2 staff change request due at the window start and says the original stays; fee-free changes are made by the AI; a cancellation inside 24h is handled the same way (Innocent, 2026-10-20); the AI never grants waivers or discounts | — | §9.3; inventory §10.4; audit §9 |
| **D4** Unsupported requests | Decided (principle + list) | Serious cases get priority; limited answers allowed; unfinished tasks get a case; requests for a person honoured | Priority thresholds tuned in testing | §9.4; inventory §10.4 |
| **D5** Contact after safety | Decided | Instruction first; contact offered after; priority case even without a match | — | §9.2; inventory §10.4 |
| **D6** History and snapshots | Decided | Full chat history in staff views; minimal snapshots of fields used, deleted 90 days after case close (Claude's recommendation, delegated) | — | §9.6 |
| **DEC-1** Scheduling scope | Decided | Required flow first; then reschedule, confirm, cancel in that order as time allows (delegated) | How far down that list time allows | §9.7; audit §9 |
| **DEC-4** Old documents | Decided | Exclude archive, old-copy and `scheduling_guide.md` from retrieval; useful gaps kept in our notes; eval cases prove it | — | §9.7; audit §9 |
| **DEC-5** Voice | Decided | Out of scope; revisit only if everything required finishes early | — | §9.7; audit §9 |
| **Q-1** Dataset and repository | Decided by Innocent (no partner answer) | Include the dataset; repository public | Licence risk on record (audit L-8) | §9.7; audit §8 |
| **Q-2** Reviewer database | Decided by Innocent | Reviewer uses our deployed copy; we own resets | — | §9.7; audit §8 |
| **Q-3** Dripping Springs, Manor | Decided by Innocent | Bookable; both mapped to `central` | — | §9.7; audit §8, K-11 |
| **GQ-20** Deadline | Internal target set | Finish by Wed 2026-10-21, 06:00 CT | Partner deadline unconfirmed | `SUBMISSION.md`; checklist |
| **LangGraph** | Decided | Framework for conversation state, tools and handoff | Written up at Stage 6 with its alternative | §10 |
| **Case store** | Decided | New tables beside the working DB copy | — | §9.7 |
| **Handoff lanes** | Delegated to Claude | Decide after Stage 2 driver selection | — | §9.7 |
| **Stage 3 choices** | Decided 2026-10-20 | HP-1: Innocent's two-layer design (action layer with tools, conversation layer without) plus turn-to-turn context management; HP-3: the fee rule above; HP-4: option B; HP-2: option C (word rules first, a small classifier that can only raise the level; false alarms ≤ 10%); cancel inside 24h like a fee-bearing reschedule; spike SP-1 approved for Stage 5 | — | `docs/design/hard-problems.md` |
| **Demo access** | Decided 2026-10-21 | One demo login gates the whole deployment; once signed in, the reviewer switches freely between customer and staff roles; reset behind the same login (PRD R-48) | Change the password after the demo (Innocent: in about a week) | System design §10 |
| **Profile §8 items** | Decided (round 3) | Ask urgency questions for no heat, no cooling or leaks (in the booking; a stated danger triggers the urgent path, Stage 2 check); brand direction **A** (dependable dispatch) goes to UX-2; self-checks offered but very optional (skipped for urgent cases) | — | Company profile §7–§8 |
