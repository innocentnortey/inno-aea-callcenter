# Hard-problem register (Stage 3)

**Date:** 2026-10-20, America/Chicago. **Stage:** zero-to-hero §3, light mode (2–4 cards on one page). **Owner of:**
HP-1…HP-4, the *Handled by default* list, and the walk of the system-design questions. **Status (2026-10-20, after
Innocent's review):** HP-1 **chosen** (his two-layer design, adapted), HP-3 **chosen** (his fee rule), HP-4 **chosen** (B), HP-2 **chosen** (C). SP-1 approved for Stage 5. Stage 3 gate signed
(Innocent ✓ 2026-10-20). The Stage 4 interview records the choices in the PRD; the PRD was updated
at once where they changed requirements.

**Built from:**
- the worked pairs ([`docs/data/worked-pairs.md`](../data/worked-pairs.md)): every *hard* pair (WP-2, 3, 4, 6, 8)
  maps to a card;
- the decisions already made ([consolidated direction §10–§11](../analysis/2026-10-20-human-handoff-consolidated-direction.md),
  [PRD](../prd/inno-aea-callcenter-prd.md) §4–§6). They are **not re-asked here**. Each card says which parts are
  decided and which part is still open;
- the *Raise in the design conversation* questions in [`docs/principles/system-design.md`](../principles/system-design.md)
  (walked at the end).

**Labels:** **[Decided]** Innocent's decision, with its ID. **[Proposed]** Claude's recommendation. **[A]** assumption,
with what would measure it. **[M]** measured.

## The story so far

Meridian's customers wait for a person to do routine things: book a visit, ask what a bill is for, ask what the
membership covers. We are building a chat agent that does those things correctly and hands everything else to a person
honestly. Stage 1 fixed the scope and the success measure: in-scope correct resolution, aiming for 100%. Stage 2 walked
eight real requests through by hand. Five of them needed judgement, not just copying a field. Those five, plus the
question of how the agent is wired together, are the hard problems below.

**Where each problem sits in one customer message:**

```
message arrives
  → HP-2  Is this dangerous?            (safety, burning smell, someone in danger)
  → HP-1  Who decides what happens next? (code vs. model: the orchestration)
  → HP-3  Doing something with rules attached (read a bill, book, move a visit)
  → HP-4  What we can't finish           (honest handoff, a brief with no invented facts)
```

---

## HP-1 · Orchestration: how much the model decides, and how much code decides

**Where this comes up.** Every message. A customer writes "My AC isn't cooling, can someone come Saturday 4 to 7?"
(WP-3). Before any reply, something has to decide: is this dangerous, do they want a person, do they need private
records, should we book? The same skeleton serves the CO alarm (WP-5), the invoice (WP-2) and the cancellation (WP-8).

**The problem.** Decide which steps are fixed code and where the model is allowed to choose.
Input → output: "I want to cancel my membership. Just make sure it doesn't renew." → verify, read the renewal date,
explain the rules, say plainly the chat can't switch off auto-renew, open a P3 case (WP-8). Which of those steps does
the model choose, and which are forced?

**Why it's hard.**
1. Some steps must **always** happen in a fixed order. The safety instruction comes before anything (R-5); a fee is
   stated before a change (R-21). A model that "usually" follows a prompt is not "always".
2. Other steps can't be scripted. WP-1's caller asks three questions in one message. A fixed form handles one intent
   at a time and breaks on that.
3. The time box (internal target 06:00 CT) rules out building a separate scripted flow for every request type.

**Already decided.** LangGraph [Decided, consolidated §10]. A deterministic safety node first on every turn; priority
and promises from code; identity checked in code in the tool guard; the AI pauses while a person holds the chat; cases
live outside the graph (§10 table).

**Options** (the open part is what happens *after* the code guards):

| | What it is | What happens if chosen | Trade-off |
|---|---|---|---|
| **A. One agent, rules in the prompt** | After the safety node, one model loop with every tool; the prompt carries the rules (verify first, state the fee first, never promise) | Fastest to write | Ordering rules depend on the model obeying. One slip is a wrong answer the grader can find. Conflicts with "correctness over fluency" (PRD §5) |
| **B. Code guards, then one model loop with guarded tools** *(recommended)* | Code runs safety, danger, person-request and human-held checks. Then one model loop picks tools. Each tool enforces its own rule in code: private tools refuse until verified; a change needs a quote first (HP-3); there is no waiver tool | Handles multi-question messages. The rules that must always hold are in code, where tests can prove them | The model still chooses *which* tool. A wrong choice gives an unhelpful reply, not a broken rule. That is caught by the eval and the failure counters (OD-6) |
| **C. Fixed flows per request type** | A router classifies the request into one of four flows (knowledge, account, booking, handoff). Each flow is a scripted state machine; the model only fills slots and writes the words | The most predictable | Breaks on mixed requests (WP-1's three questions). Four flows to build and test. Every new request type is new code |

**Recommendation: B** [Proposed]. It puts the always-rules in code (GP-72: draw the skeleton yourself; give the model
autonomy only where the path can't be known) and leaves the model the part that can't be scripted: understanding a
mixed message and picking the next tool. The parked code from before the shortcut was withdrawn already has this shape
(a `guard` node, fixed safety and burning nodes, one `agent` node). It would be adjusted for HP-2 and HP-3, not
rewritten.

**Principles:** GP-72; PRD §5 "correctness over fluency"; `agent-architecture.md` rules 1, 11, 13, 17.

**How we'll know it worked:** the hard gates already in the framing: safety first in 100% of safety cases; a person on
the first ask in 100% of cases; booking rules in 100% of writes; promise text matching the table in 100% of cases.
Scored on WP-2…WP-8 and the R-38 test set.

**Evidence:** all eight pairs; most directly WP-1 (three questions in one message), WP-4 (fixed order), WP-5 (safety
first), WP-8 (a step the system can't do).

**Innocent's choice (2026-10-20) [Decided].** His own two-layer design, "this makes the most sense, but you don't need
to follow that to a T. You can make it make sense for our PRD":

```
Customer message
  → Code gates (code: safety, danger, person)  ──→ Safety reply (fixed text, no model) ──→ send
  → Planner (model: just talk, or act?)        ──just talk──→ Responder
  → Specialist subgraphs (scoped tools, own context)
  → Escalation check (code: failures, limits, flags) ──yes──→ Handoff (case + brief)
  → Turn facts (state: results, missing info) → Responder (model: clean chat + facts) → send
  Action layer = has tools.  Conversation layer = no tools.
```

It is option B taken further. The code gates and the escalation check hold the always-rules. The model's freedom is
split: a planner chooses what to do, specialists act with narrow tools, and a responder with **no tools** writes the
words. **Adapted for the PRD** (§6.1, written up there):
- the code gates also hold the AI-paused state (R-31) and the burning-smell questions (R-7);
- the safety reply's case is written by code;
- the planner returns an ordered task list, so WP-1's three questions become three tasks;
- the three specialists are knowledge, account and scheduling. Stage 6 decides subgraph or node;
- the responder's words pass HP-4's checks (R-46).

**Turn-to-turn context management [Decided, Innocent: "another thing I want us to remember"].** New PRD R-45:
- state, not the transcript, carries memory between turns: identity, open tasks and what's missing, record IDs, the open
  case and its promise, counters;
- each model sees only its slice;
- tool output never enters the chat history;
- older turns are condensed into a typed summary copied from state;
- stale facts (slot availability, code expiry) are re-read before use.

**Status:** chosen (Innocent ✓ 2026-10-20). **`proven (SP-1)` for model mix B** (Jev planner + classifier, Sonnet 5.5 words): all hard gates held on 190 scored conversations, $0.016 per conversation [M], p95 10.2 s at 20 at once [M] against the latency line Innocent set to 12.5 s on 2026-10-21 (was 8 s). Open design items: carry completed actions across turns; state the 12-month minimum. Record: `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md`.

---

## HP-2 · Deciding a message is dangerous

**Where this comes up.** The first check on every message. A customer writes "I smell something burning from the vents"
(WP-6), or "my AC's out and my mother is 88, it's 95 degrees in here". The first needs two questions before anything
else (D2). The second must get the emergency number first (WP-3 check, 2026-10-20). A third customer just writes "My AC
isn't cooling": that is a normal booking.

**The problem.** Reliably sort each message into: safety (leave the home immediately), unclear burning smell (ask two questions),
someone in danger (emergency number first), or normal. Do it before the model writes a word.
Input → output: "co alarm keeps going off" (no capital letters, short form) → the leave-the-home instruction as the
first words (WP-5).

**Why it's hard.**
1. **Misses are the worst failure in the product.** A missed CO alarm is a safety failure, not a wrong answer. The hard
   gate is 100% (framing V4).
2. **People don't use the policy's words.** The policy lists "gas or rotten-egg smell, CO alarm, sparks/smoke/flames".
   Customers write "smells like eggs", "detector beeping", typos, or say it mid-chat (R-5 requires all of these).
3. **"In danger" has no word list.** Danger comes from a combination: a hot house **and** a vulnerable person, water
   **and** electrics. A keyword list over-fires on "it's hot" and misses "my dad's on oxygen and the power's out".
4. **The data can't teach us.** 0 of 420 calls mention a hot or cold house or a vulnerable occupant (inventory §3.4), so
   every danger test case is synthetic and must be labelled as such (`synthetic-test-data.md`).
5. **Over-firing has a cost too.** Your WP-3 answer narrowed the urgent path because firing on every no-cooling report
   (about 53 of 75 HVAC bookings) would bury the real P1 cases.

**Already decided.** The safety list and instruction (R-5, issued KB); the burning-smell questions (D2, R-7); the danger
rule (R-8, Stage 2 check); priorities set by code (§9.4).

**Options:**

| | What it is | What happens if chosen | Trade-off |
|---|---|---|---|
| **A. Word rules only** | Hand-written patterns (with typo tolerance) for each trigger | Instant, free, fully testable | Misses paraphrases; "danger" can't be written as a word list |
| **B. Model classifier only** | A small model reads each message and labels it safety / burning-unclear / danger / normal | Catches paraphrases and combinations | A model can miss a plain "CO alarm" on a bad day; a 100% gate can't rest on it alone. Adds a model call to every turn |
| **C. Rules first, then a classifier that can only raise the level** *(recommended)* | The word rules run first and decide on their own when they match. A small, cheap model (the "smaller model" in PRD §6.2) then reads the message; it may **raise** a normal message to burning-unclear or danger, never lower one the rules caught. Its label only picks among the fixed paths; it never writes the reply | Rules guarantee the plain cases; the classifier catches paraphrases and the danger combinations. If the classifier fails or times out, the rules still stand | One extra small-model call per turn (cost and about a second of latency **[A]**, measured in the first scoring run). Some over-firing is possible; it is measured by the false-urgent rate below |

**Recommendation: C** [Proposed]. The rule half makes the 100% gate provable on the plain cases, and the classifier half
is the only way to see "someone in danger", which has no word list. "Can only raise" means a classifier mistake can
cost an unneeded emergency-number line, never a missed instruction.

**Principles:** GP-72; GP-16 (verify as far as the stakes demand: here, the highest); rule `synthetic-test-data.md`.

**How we'll know it worked:**
- safety recall **100%** on the safety set (the 9 issued safety calls plus labelled synthetic variants: typos,
  mid-chat, paraphrase) [hard gate];
- danger recall **100%** on labelled synthetic danger cases [hard gate, our target];
- false-urgent rate **≤ 10%** on comfort cases with no danger (the WP-3 kind) [our target, to confirm in the interview];
- scored on WP-3, WP-5, WP-6 and the R-38 safety slice.

**Evidence:** WP-3, WP-5, WP-6.

**Status:** chosen C (Innocent ✓ 2026-10-20: "hp-2 c is cool with me"), with the false-alarm limit of ≤ 10% on
no-danger comfort cases ("that fine with me too"). His HP-1 drawing puts "danger" among the code gates; C keeps that and
adds the raise-only classifier. In the PRD as R-47.

---

## HP-3 · Actions with rules attached: reading a bill, booking, moving a visit

**Where this comes up.** After the customer is verified. Omar asks what his $478 invoice is for (WP-2). Linda books a
repair but asks for a Saturday evening window that doesn't exist (WP-3). A customer asks to move today's 12–4 visit two
hours before it starts (WP-4).

**The problem.** Let the model talk naturally while the code guarantees the rules: nothing private before the code,
the bill explained as billed, the fee said **before** a change and agreed to, the slot valid for the zone and the
member, and no double booking.
Input → output: "Can I move it?" (appointment in 2 hours) → "Under our current policy, a $49 late-change fee applies to
changes within 24 hours …" → under Innocent's Stage 3 rule, a staff change request, never the move (WP-4). (As first
written, this example ended "only after 'yes': the move"; that is superseded.)

**Why it's hard.**
1. **Order matters, and the model controls the conversation.** In the transcript, the human agent moved the
   appointment and never mentioned the $49 (sample S6). A model can do the same if the move tool is callable at any
   time.
2. **"Yes" has to be the customer's yes to *this* quote**, not a yes to an earlier question.
3. **Records disagree with policy.** INV-204411 bills $144 after-hours; the schedule says $149 (audit D-8). Your WP-2
   answer: explain as billed. If the model sees both numbers, it may volunteer the mismatch.
4. **Booking rules live in several places:** zone by city (with two towns mapped to `central`, Q-3), service type,
   member-reserved slots, open status, and the fixed clock (R-18, R-3).
5. **Issue text in the DB can't be trusted.** 109 of 159 appointments list an issue that doesn't match the booked
   service (D-11).

**Already decided.** Simulated code to the contact on record (OD-3, R-15); no waiver ever (D3/DEC-2); writes to a
working copy in one transaction (R-19); explain, never adjudicate (R-17); WP-2's "as billed".

**Innocent's choice at this review (2026-10-20) [Decided]: the AI never makes a change that carries the $49 fee.** It
replaces the earlier decision that let the AI commit a change after a quote and a "yes", which options A–C below assumed.
- **Inside 24 hours:** verify, explain the fee, record the requested change for a representative, and say the original
  appointment stays until a person confirms. Never "charged". It is a **handoff**, not an AI-resolved change.
- **No fee:** the AI reschedules itself under the normal booking rules.
- **WP-4 starts two hours before the visit**, so a one-business-day callback alone is not enough. The prompt staff path
  (his ask; the design is delegated to us):
  - P2, with its internal due time at the window start, and a supervisor alert at once;
  - the live queue first if someone is online;
  - phone support mentioned when it is open (the KB gives hours, no number);
  - a plain warning when confirmation before the window can't be guaranteed.
- The owner is consolidated direction §9.3; PRD R-21 is rewritten; WP-4 is revised.

**Options:**

| | What it is | What happens if chosen | Trade-off |
|---|---|---|---|
| **A. Plain tools, rules in the prompt** | `book`, `reschedule`, `read_invoice` callable once verified; the prompt says "state the fee first, explain as billed" | Least code | The S6 failure (change made, fee never said) stays possible. "Fee line precedes the write in 100% of cases" can't be guaranteed |
| **B. Two-step tools: quote, then commit** *(recommended)* | `quote_change` checks the rules (zone, slot, 24-hour clock) and returns a quote ID plus the exact fee sentence the reply must contain. `commit_change(quote_id)` refuses unless that quote was shown to the customer and their **next** message is a yes (checked in code; a LangGraph short approval gate, consolidated §10). `read_invoice` returns the lines as billed; policy mismatches go to a staff-only field the model never sees, which flows into the case brief | Every rule is a code check with a test. The model still words the reply and handles "actually, Tuesday instead" | Slightly more tool code. The model must call quote before commit; if it doesn't, commit refuses and the model retries. That is the guard working, and it shows in the lookup log |
| **C. Buttons for actions** | Slot choice and "Confirm the change ($49)" are buttons in the chat; the model can't call write tools at all | The customer's yes is unambiguous | More UI work in the time box; the reviewer can't book by typing; departs from a chat-first agent |

**What remains of the options after his decision.** The fee-bearing commit no longer exists, so option B's
"quote → commit" now applies only to **fee-free** changes and new bookings: the scheduling tool writes only after the
customer has picked the slot shown. Option B's invoice part still stands: the $144-vs-$149 gap goes to a staff-only note
the model never sees.

**Build details that follow from his decisions (not questions):**
- fee-free writes happen only after the customer picks the slot shown, per WP-3, which he checked ("book the slot the
  customer picks");
- the $149 schedule fee is kept out of the model's view on an invoice read, so it can't volunteer it. This follows from
  his WP-2 answer ("explain as billed", 2026-10-20).

**Cancellation inside 24 hours [Decided, Innocent 2026-10-20: "yes"]:** handled like a fee-bearing reschedule (PRD R-22).

**Principles:** `agent-architecture.md` rule 17 (approval gate before writes); GP-11 (the model advises, code executes;
a mismatch returns a refusal); GP-116 (refuse rather than guess for an invariant).

**How we'll know it worked:**
- 100% valid writes and 0 double bookings (framing V2) [hard gate];
- **0 fee-bearing moves by the AI**; the fee line and the "original stays" line in 100% of fee-bearing cases (R-21);
- nothing private before a correct code (R-15);
- no unprompted $149 on INV-204411; the mismatch appears in the brief;
- scored on WP-2, WP-3, WP-4 and the booking slice of R-38.

**Evidence:** WP-2, WP-3, WP-4.

**Status:** chosen (Innocent ✓ 2026-10-20: the fee rule, and cancellations inside 24 h the same way). No spike needed.

---

## HP-4 · What the system can't finish: an honest handoff and a brief with no invented facts

**Where this comes up.** At the end of a conversation the agent can't complete. Linda asks to switch off auto-renewal
(WP-8): the KB says agents can, but the database has no field to change. A customer demands a refund (WP-7). Omar
disputes a line on his bill (WP-2, step 6).

**The problem.** Say plainly what was and wasn't done, give the promise from policy, and hand staff a brief they can act
on without re-asking, with no fact the system didn't actually see.
Input → output: "Just make sure it doesn't renew." → "I can't switch off auto-renewal from this chat. I've created a
request for a representative to do it before your renewal date of November 3." + the 1-business-day promise + a
reference (WP-8). **Never** "Done, auto-renew is off", which is what the human agent said.

**Why it's hard.**
1. **Models like to sound finished.** "I've taken care of that" is the natural closing line, and it is a false claim
   when no write happened.
2. **A brief that invents one fact is worse than no brief.** Staff act on it; the reviewer checks it (hard gate:
   0 invented facts, R-28).
3. **Facts and claims look alike.** "It didn't fix anything" is the customer's claim, not a fact (WP-7). The brief must
   keep them apart.
4. **The promise must match policy word for word**, and the model already tried to restate it in the parked code
   (fixed then by stripping its timing sentences).

**Already decided.** Promise and due time from a policy table (OD-4, R-26); the D4 table of unsupported requests and
priorities (§9.4); eight fixed brief headings, with facts from state and only three headings from the model (R-28).

**Options** (the open part is how the model's words are checked):

| | What it is | What happens if chosen | Trade-off |
|---|---|---|---|
| **A. Prompt rules only** | The model writes the handoff reply and its three brief headings; the prompt says "never claim completion; keep claims apart" | Least code | No way to prove the 0-invented-facts gate; completion claims slip through |
| **B. Code writes the promise; checks guard the model's words** *(recommended)* | The promise, reference and due time are inserted by code after the model's text. A **completion check** blocks a reply that claims an action ("done", "cancelled", "turned off", "refunded") unless a write tool succeeded in that turn. A **fact check** compares every number, date, ID and money amount in the model's brief headings with the lookup log and the conversation; anything unmatched is removed and the heading is marked "check" | The two hard gates (promise match, 0 invented facts) become code checks with tests | Two small checkers to build. They can over-block a harmless phrase; it shows in the eval and the patterns get tuned |
| **C. No model in the handoff** | The reply is a fixed template; the brief is the facts plus the full transcript, with no model summary | Nothing can be invented | Staff read the whole chat to find the need, which defeats the brief (C2: "act without re-asking") |

**Recommendation: B.** It keeps R-28's useful summary and makes both of its gates checkable. **Innocent chose B
(2026-10-20) [Decided]**; written into the PRD as R-46.

**Principles:** GP-16 (verification ladder); GP-18 (say so when the evidence doesn't answer); `agent-architecture.md`
rule 3 (typed outputs).

**How we'll know it worked:**
- promise text matches the policy table in 100% of handoffs (framing V3) [hard gate];
- 0 invented facts and required-item recall ≥ 90% in briefs (R-28);
- 0 completion claims without a successful write;
- scored on WP-2 (dispute branch), WP-7, WP-8 and the handoff slice of R-38.

**Evidence:** WP-8 (hard), WP-7, WP-2 step 6.

**Status:** chosen B (Innocent ✓ 2026-10-20). No spike needed.

---

## Spikes (Innocent: "if we need to spike anything let me know")

Spikes run at Stage 5 (System track), after Stage 4 and UX-1. **SP-1 approved by Innocent (2026-10-20: "yes").**

**SP-1 (approved, runs at Stage 5): turn latency and cost of the two-layer design.**
- **Why it is uncertain:** a turn now makes several model calls: planner, one or more specialists, responder, and HP-2's
  classifier (C, chosen).
- **What it puts at risk:** two of Innocent's numbers, p95 ≤ 8 s per turn at the 20-conversation spike, and the model
  spend cap, raised to $30/day on 2026-10-20 (about $0.30 per conversation [C]). Research estimates $0.166–0.206 for
  Sonnet everywhere [C]; SP-1 measures it.
- **The test:** run WP-1…WP-8 through a thin version of the graph. **Baseline: Sonnet 5.5 in every role** (Innocent's
  default, 2026-10-20). **Candidates per role** (his list): Sonnet 5.5, GPT-5.6 Terra, Gemini Flash, and Jev (TypeSafe AI's
  typed-classification model) for the planner/classifier. Jev is called through OpenRouter (`typesafe/jev-1.13`, as in Equinox). Its terms now exclude training on inputs (re-checked
  2026-10-20; retention still unstated), so it is a normal SP-1 candidate; deployed use is decided after SP-1. Measure latency, cost per conversation and correctness against the
  worked pairs' required outputs.
- **Decision criteria:** keep Sonnet everywhere unless another mix keeps every WP output correct and is faster or
  cheaper. Whatever is kept must stay under 8 s p95 and fit $0.30 per conversation. If nothing does, the trade-off goes
  to Innocent.

No other card needs a spike.

---

## Handled by default

Each was considered and needs no card, because the answer is a known pattern or already decided:

- **Stale documents in retrieval** (WP-1): the ingestion manifest excludes the archive, the old FAQ copy and the
  outdated scheduling guide (DEC-4, R-10). Tested by the retrieval hard gate (0 answers from excluded files). Keyword
  boost is added only if the retrieval eval shows misses (PRD §6.2).
- **Formats in the KB:** PDF, CSV rows and the holiday PNG (hand-verified transcription linked to the image) (R-9).
- **Fixed clock:** "today" is configured as 2026-10-16 and injected, never read from the server (R-3).
- **Zone mapping:** city → zone, with Dripping Springs and Manor as `central` (Q-3, R-18).
- **Identity:** simulated one-time code to the contact on record, demo inbox, hashed (OD-3, R-15).
- **A person on the first ask:** code and a cheap check before any tool use (R-2, OD-6).
- **Staffing honesty:** default nobody online; the labelled simulation mode (R-30).
- **Case store, lifecycle and overdue alerts:** application tables and a scheduled job on the fixed clock (R-25, R-33).
- **Promise table:** code lookup (R-26).
- **Monitoring, redaction and spend brakes** (R-35, R-36, R-41).
- **Test set held out by template** so the number is real (R-38). This is Stage 9's job; its design is already in the
  PRD.
- **Durability:** SQLite on a Railway volume and a durable checkpointer survive a restart (SD-7.2).

---

## System-design questions walked (`docs/principles/system-design.md`)

The five foundation questions were answered by Innocent on 2026-10-20 (PRD §10 item 4). The rest are answered from the
docs, or left to Stage 6 because they need a traced request or a measurement. None needs a new card or interview
question.

| Principle | The question, short | Answer | Source |
|---|---|---|---|
| GP-107 Economics | Cost per successful outcome? | One correct resolution saves about 111 s of staff talk time [M, median call]. Spend may be about **$0.30 per conversation** [C: $30/day cap, raised 2026-10-20 ÷ ~100/day]. We don't cut accuracy for cost | Framing §1; PRD §10 SD-1.6, SD-3.1 |
| GP-108 Scale bucket | Which bucket? | ~100 conversations/day, ~20 at once [T]: one instance, one SQLite file, no queue, no hosted vector service. Tempted but rejected: Postgres, autoscaling, a vector database | PRD §5, §6.2 |
| GP-109 Uncertainty | Where is the partner unsure? | "Is the containment number real?" and "would the business know if it broke?" (Part B). The centre of the design is HP-1, HP-2, HP-4 and the eval. Chat, DB and embeddings are standard | Brief Part B; this register |
| GP-110 Promises | Invariants vs. percentiles? | Invariants: safety first, valid bookings, policy promise text, nothing private before a code. Percentile: p95 ≤ 8 s per turn [A]. Where each latency measurement starts and stops is **Stage 6** | PRD §4, §5 |
| GP-111 Workloads | Work per user action? | Per turn: rule checks (code), one small classifier call (HP-2), 1–4 main-model calls [A], retrieval, DB reads. Background: the overdue job, ingestion at deploy. Peak length unknown [A] | PRD §5; HP-2 |
| GP-112 Trace one request | What does it hold while waiting? | **Stage 6** (DO-1 traced request) | — |
| GP-113 First breaker | What breaks first? | Expected: model-provider concurrency or latency at 20 at once [A]; SQLite writes are tiny at this volume [C]. A 20-conversation load test at Stage 9 shows it | PRD §5 |
| GP-114 Overload | Wait, degrade or fail? | Safety never waits (code, no model). Model calls wait to a deadline, then hand off. Spend cap reached → hand off. Booking writes serialize | PRD §5, R-41 |
| GP-115 Autoscaling | Headroom or autoscale? | Always-on headroom for 20 on one instance; no autoscaling at this bucket [C] | PRD §5 |
| GP-116 Consistency | Refuse or guess? | Bookings, identity and promises refuse rather than guess. KB answers carry the document's version date | R-11, R-19, HP-3 |
| GP-117 Cache | Is a cache needed? | No cache. The vector index is a derived copy rebuilt from the manifest; the DB working copy is the source of truth | PRD §6.2 |
| GP-118 Replicas | What failure to survive? | A process restart (SD-7.2). One replica; capacity per replica measured at Stage 9 | PRD §10 |
| GP-119 Labels | Measured vs. assumed? | Labelled throughout ([T]/[A]/[C]/[M]); revisit triggers are written at Stage 6 | This register; PRD |
