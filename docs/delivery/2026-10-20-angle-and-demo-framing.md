# AEA call center: two layers of success, metrics tree, and how we present it

**Date:** 2026-10-20, America/Chicago. **Status:** signed off by Innocent, 2026-10-20 ("yes to all"): framing, north star and targets.
**Owns:** the two-layer success framing, the metrics tree (north star, value and health metrics, with their decision
lines), the strongest objection and the demo order. It adds **no requirement**. Scope stays with the PRD (planned,
`docs/prd/`), and product decisions stay in the
[consolidated handoff direction §11](../analysis/2026-10-20-human-handoff-consolidated-direction.md).
**Built on:** the [problem behind this brief](../analysis/2026-10-20-brief-audit.md#the-problem-behind-this-brief) (audit),
the [handoff information inventory](../data/handoff-information-inventory.md) and the
[company profile](../analysis/2026-10-20-meridian-company-service-profile.md). Rules: `hiring-partner-framing.md`,
`problem-framing.md`, `business-metrics.md`.

**Labels for targets (GP-119, GP-142):** **measured** (from issued data or a run), **issued target** (from the brief),
**our target** (proposed here; Innocent signs it off at the Stage 1 gate), **assumption**.

---

## 1. The two layers of success

**Layer 2: why the partner wrote the brief (open with this).** AEA's portfolio initiative is to "expand call center
coverage without adding headcount by deflecting a majority of calls to an AI agent" (Part A, Business Context). The
partner told us how it will judge that: "Containment rate … accuracy on handled call drivers, escalation rate on
out-of-scope calls, retrieval accuracy … and production monitoring metrics such as volume, containment, escalations,
failures, and latency" (Part A, Impact Metrics). The reviewer's own questions are "Is the containment number real?" and
"Would the business know if it broke?" (Part B).

**Layer 1: the project's problem (prove this).** Meridian's homeowners can only get routine things done by waiting for a
person. We build a chat agent that:
- answers the main routine questions from the **current** knowledge base;
- books directly against the scheduling database;
- gives the safety instruction first when it matters;
- hands everything else to a person, with a brief, its sources and an honest promise.

The full chain is in the audit's why-chain.

**How the system drives layer 2 (close with this).** Every correctly resolved conversation is about 111 seconds of staff
talk time not spent (median call, measured). Every handoff arrives ready, so staff time goes to the calls that need a
person. Containment is counted only when the customer's need was **correctly** met, so the number the business sees is
one it can stake a decision on.

**The angle we present [Innocent's framing, 2026-10-20].** We speak from our capacity, never from a shortfall.
- **The story:** "We chose a scope we could build well in the time we had, and we aimed to resolve **100%** of the
  requests inside it correctly."
- **The number we lead with is in-scope correct resolution.**
- **The brief's containment number is still reported,** as the product of two parts: how much of the call volume our
  scope covers, times how well we resolve it. **Coverage** tonight is 58.3% of the issued call volume, measured.
- **More time and systems widen coverage step by step:**

| Step | What it adds | Coverage of call volume |
|---|---|---:|
| Tonight's scope | Booking, membership, billing and warranty answers, estimates, redirects | 58.3% |
| Appointment changes | Fee-free reschedule, confirm, cancel | 61.9% |
| A payment system | Payment links and autopay | 68.6% |
| Membership billing | Auto-renew changes, upgrades, join-and-book | 74.0% |
| Records Meridian holds | Manufacturer registration and repair history | 77.9% |
| **Belongs with people by design or policy** | Disputes, refunds, complaints, safety, commercial and late-technician calls (policy or safety), and reschedules that carry the $49 fee (Innocent, Stage 3) | **22.1%, never automated** |

(Recomputed 2026-10-20 after the Stage 3 decision that the AI never makes a fee-bearing change: 14 of the 15 reschedule
calls are inside 24 hours. Earlier figures 65.2%, 81.2% and 18.8% are superseded. The cumulative order is in [PRD §3.3](../prd/inno-aea-callcenter-prd.md). All shares are measured on the issued calls,
inventory §6.)

The FDE recommendation to the exec team follows from it: **the next ~16 points come from connecting payments,
membership billing and Meridian's records, not from a better prompt.** The last 22.1% should stay human.

---

## 2. The metrics tree

**North star (one).** **In-scope correct resolution** = in-scope conversations the AI resolved correctly with no human
needed ÷ all in-scope conversations.
- **"In scope"** is fixed by the test set's gold labels, written before any run, never by the agent itself. That stops
  the agent improving its score by calling hard cases out of scope (guarded by V5).
- **Unit:** conversations.
- **Segments:** handled topic (booking, membership, billing questions, warranty); staffed vs unstaffed.
- **Guards:** wrong, abandoned and wrongly escalated conversations count as failures; always shown beside the
  wrong-answer rate (audit E-1).

**Always reported with it** (the brief's own metric, decomposed, never hidden):
- **Scope coverage:** in-scope conversations ÷ all conversations. 58.3% of the issued calls tonight, measured.
- **Containment:** coverage × in-scope correct resolution, i.e. correctly resolved ÷ all conversations (Part A).

| Measure | Baseline | Aspiration | Hard gate |
|---|---|---|---|
| In-scope correct resolution | **0%** today. **Measured:** 420 of 420 calls were handled by people | **100%** (Innocent's framing) | **≥ 90%** (our target) before we call a topic ready; a topic below it goes to people until fixed |
| Scope coverage | 0% today | 58.3% tonight → 61.9% with appointment changes → 77.9% with the systems in the roadmap above (measured shares) | — |

**Decision line:** if in-scope correct resolution on the test set falls below 90% for a topic, we run error analysis
on that topic before anything else (Stage 9 rule: no tuning without a named failure type). If it stays below, the topic
goes to people. **Review:** at every evaluation run, and weekly in production.

### Value metrics (did the customer benefit?)

| Branch | Leading (alerts) | Lagging (settles it) | Unit / denominator | Baseline · aspiration · hard gate | Decision line | How the system produces it |
|---|---|---|---|---|---|---|
| **V1 Correct answers** | **Retrieval current-document hit rate**: the right *current* document in the top 3, including the stale-copy trap cases (C-14, DEC-4) | **Wrong-answer rate** on conversations the AI handled | Retrieval: eval queries. Wrong answers: AI-handled test conversations | No baseline · **our target** ≥ 90% hit rate · **hard gate: 0** answers sourced from excluded or stale files; wrong-answer rate ≤ 5% (**our target**; the brief says a confident wrong answer is worse than a handoff) | Wrong answers above 5% on a driver → that driver escalates instead of answering until fixed | Retrieval eval run; per-turn source log (C4 lookup log) |
| **V2 Correct bookings** | Booking-rule checks pass (zone, member-reserved slots, open status, fixed clock) | Bookings correctly written; no double booking | Booking attempts | **Hard gate: 100%** valid writes, 0 double bookings (G-7) | Any failure blocks the deploy | Booking tool's validation results; DB-copy check after the test run |
| **V3 Handoff that keeps its promise** | Brief required-item recall; 0 invented facts (validation spike, consolidated §7) | **Promises kept on time**: contacted before due ÷ promises due | Cases | No baseline (0 references and 0 windows in the transcripts, **measured**) · **hard gate:** promise text matches the policy table in 100% of cases · **our target** ≥ 90% kept on time (prototype: simulated clock) | Promises missed → supervisor view alerts; repeated misses → change staffing or the promise, never hide it | Case store: promise record, due time, status |
| **V4 Access and safety** | Direct request for a person → handoff on the **first** request; safety instruction first | **Abandonment rate**: conversations that ended with neither resolution nor handoff | Conversations | **Hard gates: 100%** and **100%** on the leading pair · abandonment: no baseline; **our target** ≤ 10% | Any miss on a hard gate blocks the deploy | Conversation log; safety-node and handoff events |
| **V5 Right things escalated** (Part A's "escalation rate on out-of-scope calls") | Escalation **recall** on out-of-scope test cases | **False escalation** on in-scope cases | Test cases, split in-scope / out-of-scope | **Our targets:** recall ≥ 95%; false escalation ≤ 10% | Recall below target → widen the escalation triggers; false escalation above → inspect trigger thresholds (OD-6) | Eval run labels |

**V4 addition (Innocent, 2026-10-20, Stage 3 HP-2):** danger is caught on **100%** of labelled synthetic danger cases
(hard gate), and false alarms stay at **≤ 10%** on no-danger comfort cases (decided target). Decision line: above 10% →
tighten the classifier's raise rule before anything else. Measured in the first eval run and in spike SP-1.

**How each supporting metric explains the north star (GP-139):**
- **V1:** wrong answers and stale retrieval pull it down directly, because a wrong answer is not a resolution.
- **V2:** a failed or invalid booking turns a resolvable call into a failure.
- **V3:** does not move the north star, because handoffs are not containment. It explains whether the *escalated* share
  is handled well, which is the brief's "clean failure".
- **V4:** abandonment is the hidden failure that would otherwise flatter the north star.
- **V5:** false escalation lowers it, while missed escalation inflates it dishonestly. Both are tracked.

### Health metrics (does it run?)

| Metric | Unit | Decision line | Source |
|---|---|---|---|
| Volume (conversations, handoffs by reason) | per day | **Zero traffic** for an expected window → alert (it may be down) | Conversation log |
| Latency p50 / p95 per turn | seconds | p95 above **12.5 s** at 20 conversations at once (**decided**, Innocent 2026-10-21 after SP-1, which measured 10.2 s; was 8 s, an assumption) → check the model and retrieval steps | Trace timings |
| Tool and model failure rate | per 100 turns | Above **2%** → alert and fall back to handoff | Error log |
| Spend per conversation and per day | dollars | Daily cap reached → the agent hands off and stops calling models (a design brake) | Model usage log |
| Unowned and overdue cases | count, with age | Any overdue case → supervisor alert (C3) | Case store |

Health and value are reported separately. "It's up" never stands in for "it's right" (audit G-5).

### The strongest objection, and the answer (GP-143)

> **"The brief asked for most calls to be handled. Yours handles about half."**

We chose the scope we could build **correctly** in the time we had, and inside it we aim for every request to be
resolved right.
- **Coverage is a roadmap, not a ceiling on quality.** Appointment changes, a payment system and membership billing take
  it from 58.3% to 77.9% of call volume.
- **The remaining 22.1% belongs with people by design or policy:** disputes, refunds, complaints, safety, and
  reschedules that carry a fee.
- Reaching for more tonight by answering disputes or pretending to send payment links would produce the confident wrong
  answers the brief warns against.

---

## 3. The success surface

**Business-owner view (decided, OD-1).** It reads **stored** outcomes and never recomputes them for display:
- the north star and its guards (wrong answers, abandonment), each with its denominator;
- promises kept on time;
- handoffs by reason, linked to example cases;
- the health list.

**The use signal (GP-128).** Volume and outcomes over time. A view with no use signal is on the cut list.

---

## 4. Demo order (outline; the full script is Stage 10)

1. **The problem in the partner's words:** coverage without headcount; the reviewer's "is the number real?"
2. **What success means:** the two layers; 100% correct within the scope we chose; the coverage roadmap.
3. **The flow, narrated by what the partner cares about:**
   - a membership question answered from the current document (with the stale-copy trap avoided);
   - a booking written;
   - a CO alarm getting the safety instruction first;
   - a billing dispute handed off with a brief and an honest one-business-day promise;
   - the reviewer joining the same chat as the labelled demo representative.
4. **The success surface:** the owner view on the evaluation run.
5. **Decisions, cuts, candour:**
   - the emergency number is a placeholder;
   - payments are not connected;
   - voice is out;
   - the test set is split by template.

---

## 5. What this document does not decide

- **The PRD's scope and the handled drivers.** Those are for the PRD (Stage 1) and its approval (Stage 4).
- **"Our targets" above** were signed off by Innocent at the Stage 1 gate (2026-10-20); the HP-2 false-alarm target was added at Stage 3.
- **Production numbers.** Every number here is either measured on the issued data or a stated target. No result exists
  until an evaluation run (`source-authority.md` rule 5).
