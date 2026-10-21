# Technical documentation: Meridian AI service agent

**Deliverable D-4** of the AEA FDE Challenge (AI Call Center Agent). Written 2026-10-21 from the decision records and the
final Stage 7 contracts, **before the build finishes**. It describes the system as designed. Where the built code
differs, the code and its tests are the truth and this page is corrected in the same change.

**How to read the labels.** Every choice carries the status its own record gives it.

| Label | Meaning |
|---|---|
| *Decided* (who, date) | Innocent chose it, or a source document settles it. |
| **[T]** | A target Innocent set. A target is never a result. |
| **[A]** | An engineering default that a named measurement will replace. |
| **[M]** | Measured. Either on the 420 issued calls, or in a named spike or pre-build check. |
| *Proposed, awaiting Innocent* | The design is built on the recommended option; his answer may change it. |
| `pending: <who fills it>` | A number this page cannot state yet. The ticket or stage that produces it replaces the line. |

**Nothing here is a result of the built system.** Every eval number, the built index's chunk count and the live URL read
`pending`. The only measurements on this page come from the issued data (the 420 calls, the 17 knowledge-base files, the
scheduling database) and from two pre-build checks that are named where they appear (the retrieval floor check and the
SP-1 spike).

**Sections.** 1 The problem behind the brief · 2 Discovery: call drivers · 3 Scope decision · 4 Data traps we caught ·
5 Knowledge base · 6 How one turn works · 7 Scheduling · 8 Escalation and handoff · 9 Monitoring and the feedback loop ·
10 Evaluation method · 11 Production thinking · 12 Known gaps and assumptions · 13 What we chose not to build.

---

## 1. The problem behind the brief

**Sources:** [angle and demo framing](delivery/2026-10-20-angle-and-demo-framing.md) §1–§3 ·
[brief audit](analysis/2026-10-20-brief-audit.md#the-problem-behind-this-brief) *The problem behind this brief* ·
[key-metrics registry](design/key-metrics-registry.md) M-1, M-4, M-5 (DO-7) · [PRD](prd/inno-aea-callcenter-prd.md) §1.

**Brief said X.** AEA wants Meridian's call center to "expand call center coverage without adding headcount by deflecting a
majority of calls to an AI agent" (brief Part A, Business Context). The brief's own target is 60–75% containment, and it
asks for an agent that resolves routine calls "while gracefully escalating anything it cannot handle".

**We found Y.**
- All 420 issued calls were phone calls handled by a person. The median call is 111 seconds [M]. The problem is volume, not
  slow agents.
- Most of that volume is routine: a repair booked, a bill explained, a membership or warranty question answered. Every one
  needs a person to read a messy knowledge base or a scheduling database that customers cannot reach.
- Handing off is not the hard part. **Keeping the promise after the handoff** is. In the transcripts, every handoff is a
  callback, no reference number is given, and three different callback promises are used [M, inventory §1 and §5.3].

**We built Z.** A public chat agent for Meridian's homeowners. It:
- answers the main routine questions from the **current** knowledge base, with a source on every policy answer;
- books directly against a working copy of the scheduling database;
- gives the safety instruction first when it matters;
- hands everything else to a person with a short brief, its sources and a promise that comes from a policy table.

A staff console lets a (simulated) representative take over the same chat. A business-owner view shows outcomes. An
evaluation built from the transcripts reports the numbers honestly.

**The north star, and why containment is reported as coverage times correct resolution.**
- **North star: in-scope correct resolution** (M-1) = in-scope conversations the AI resolved correctly with no human needed,
  divided by all in-scope conversations. "In scope" is fixed by gold labels written before any run, never by the agent
  itself, so the agent cannot raise its score by calling hard cases out of scope.
- The brief's **containment** is still reported (M-5). It is the product of two parts: **scope coverage** (M-4, how much of
  the call volume our scope covers) times in-scope correct resolution. Containment cannot exceed coverage, so a high
  containment number from a narrow scope would only mean we chose easy calls, and a 60% target cannot be reached by a
  better prompt if the scope covers less than 60% of calls. We report both parts so the reader can see which one moved.
- Containment is counted only when the customer's need was **correctly** met. A wrong, abandoned or wrongly escalated
  conversation counts as a failure, so the number the business sees is one it can stake a decision on.

| Measure | Baseline | Aspiration and bar | Result |
|---|---|---|---|
| In-scope correct resolution (M-1) | 0% today: 420 of 420 issued calls were handled by people [M] | Aim 100%; at least 90% per topic before the topic counts as ready [T] (framing §2) | `pending: Stage 9` |
| Scope coverage (M-4) | 0% today | 58.3% of the issued call volume tonight [M]; roadmap in section 3 | Computed on the issued calls; the eval report restates it on the test set, `pending: Stage 9` |
| Containment (M-5) = coverage × resolution | 0% today [M] | The brief's 60–75% is the **brief's target**, not ours and not a result | `pending: Stage 9` |

**How the system drives the business metric.** Each correctly resolved conversation is about 111 seconds of staff talk time
not spent (median, measured; wrap-up time is not measured and is an assumption **[A]**, replaced by real staff timing). Each handoff arrives with a brief, so
staff time goes to the calls that need a person. The success surface (section 9) reads stored outcomes and never
recomputes them for display.

**Rejected explanations** (audit why-chain): "agents are slow" (calls are short), "add staff or hours" (the brief excludes
headcount), "a better phone menu" (it routes calls but resolves nothing).

---

## 2. Discovery: call drivers

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) §3.1 ·
[handoff information inventory](data/handoff-information-inventory.md) §2, §3.1–§3.4, §10.3, §11.1 ·
[classifier](data/scripts/classify_calls.py) and its output [call_classification.csv](data/scripts/call_classification.csv) ·
[per-call table](data/handoff-inventory-call-map.csv).

**Drivers ranked by volume** (all 420 calls; one primary category per call, shares use 420 as the denominator) [M]:

| Rank | Driver family | Calls | Share |
|---:|---|---:|---:|
| 1 | New service booking (HVAC repair, plumbing, tune-up, burning-smell visit) | 132 | 31.4% |
| 2 | Billing information and payments | 67 | 16.0% |
| 3 | Comfort Club membership | 57 | 13.6% |
| 4 | Warranty | 45 | 10.7% |
| 5 | Managing an existing appointment | 38 | 9.0% |
| — | Disputes and refunds 24 · complaints 16 · out of scope 16 · estimates 12 · safety 9 · two-part 4 | 81 | 19.3% |

Ranking depends on grouping. Merging disputes and refunds into billing would make billing 91 calls (21.7%) and second. The
inventory does not choose the brief's "top 4 to 5"; the choice is in section 3.

**Method: how every one of the 420 calls was classified.** Three layers, in this order
([classify_calls.py](data/scripts/classify_calls.py)):
1. **Initial need.** Skip filler turns ("can you hear me", "I'm driving", "my dog is barking"), take the first substantive
   customer turn, strip speech-to-text filler, and match it to exactly one category by an ordered rule list. A call that
   matches no rule raises an error, so nothing was silently dropped: 0 of 420 unclassified [M].
2. **Events.** Separately, a pattern pass over the *agent's* lines records what the human said or did (read a balance, offered
   a slot, promised a callback, and so on).
3. **Emergent escalations.** A search of every customer turn after the opening request for dispute, refund, manager, legal or
   safety language. It found none outside the escalation categories.

**Why it is trustworthy enough.** The two views were built independently and agree: the 37 categories (built from the
customer's words) correspond to 25 distinct agent-side event signatures (built from the agent's words), with 0 exceptions
beyond ordinary variants. 57 transcripts were read in full, at least one for every category [M].

**Reproduce it** (read-only on the issued data):

```
cd docs/data/scripts
python3 -I classify_calls.py            # writes call_classification.csv, prints families, support levels, events
python3 -I checks_handoff_inventory.py  # prints every other number in the inventory (checks C1 to C12)
```

**Limits of the evidence.**
1. Transcripts record speech, not system actions. "Moved" is something an agent said; whether a record changed is not shown.
2. Callers cannot be matched to the database, so we cannot check whether the human's reading of an account was right.
3. The classifier is ours. It was built after reading exemplars and is valid for this templated corpus. It would not
   generalise to natural calls without being rebuilt.
4. The calls are generated from templates (46 opening templates behind 37 categories [M]). Counts show the generator's mix,
   not a real-world rate.
5. Timestamps are synthetic: calls exist on Sundays, on Labor Day and after hours. We use them at face value only where
   stated.
6. No repeat contacts can be measured, because no identifier repeats across calls.

**Uncertain classifications** (inventory §10.3, each with the effect if wrong):

| Category | Why uncertain | Effect if wrong |
|---|---|---|
| Burning-smell visit (16 calls) | "Safety-ambiguous" is our label; the knowledge base is silent about it | Moves 16 calls between booking and a handoff type |
| Late technician (9) | A service failure with a fee-waiver question, not a supervisor escalation | Counted as "person required" because the waiver is staff discretion |
| Repeat-repair and warranty-claim calls (20) | Counted as warranty; each also includes a booking | Booking-side share rises by up to 20 calls |
| Warranty parts (7) | A warranty question plus a dropped scheduling request | Strict multi-request count would be 10 instead of 17 |
| Duplicate charge (11) | Could be read as a dispute; humans treated it as information | Information versus dispute handling |
| Commercial and hiring (11) | Redirects, not escalations to a supervisor | A handoff row but no case record |
| Membership discount (4) | Membership is a self-declared claim | Assumes the claim is not acted on |

---

## 3. Scope decision: the right 3, not just the top 3

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) §3.2–§3.3 ·
[consolidated handoff direction](analysis/2026-10-20-human-handoff-consolidated-direction.md) §9.4 (D4), §9.7 ·
[brief audit](analysis/2026-10-20-brief-audit.md) DEC-1…DEC-5, C-2, C-4.

**The question the brief asks.** "Did you pick the **right** 3 drivers to handle and the right ones to escalate?" Volume
ranks the drivers; judgment chooses. By volume, billing (rank 2) includes payments that the supplied systems cannot take and
disputes that policy keeps with a supervisor. We handle the **answerable part** of each driver and escalate the rest.

**What is handled** (PRD §3.2; the three RAG drivers are labelled *Proposed* there and were approved with PRD 0.4 at the
Stage 4 gate, Innocent 2026-10-20):

| Competency | Drivers | Why these | Calls it can answer |
|---|---|---|---|
| **Scheduling** (brief-required; DEC-1 decided) | New service booking and replacement estimates; then reschedule (fee-free only), confirm, cancel as time allows | Largest driver; required competency | 116 + 12 booking and estimate calls [M]; then reschedule 15 (14 of them fee-bearing), confirm 8, cancel 6 |
| **RAG driver A: membership** (*Proposed*) | What is included, price, discounts, renewal date and terms | Rank 3; fully covered by the current knowledge base; the archive copy is the classic trap | 38 of 57 [M] (cancel and upgrade need systems that do not exist) |
| **RAG driver B: billing questions** (*Proposed*) | Balance, "what is this invoice for", duplicate-charge explanation | Rank 2; answerable from invoices plus the FAQ; payments go to staff | 39 of 67 [M] |
| **RAG driver C: warranty** (*Proposed*) | Install and repair warranty terms, parts coverage, transfer | Rank 4; answerable from the warranty policy plus customer fields | 29 of 45 [M] |

**What escalates by design** (*Decided*, Innocent 2026-10-20; policy and D4): billing disputes, refund requests, complaints
and manager requests, commercial work, a late technician, safety reports (instruction first), and the actions the supplied
systems cannot perform: payment links, autopay, changing auto-renew, upgrades that need a payment, registration records. An
unfinished task always gets a case; only a question that can be fully answered within limits ends without one, and the
customer is still offered a person.

**Coverage per step, measured on the 420 issued calls** (PRD §3.3). Coverage is the share of call volume our scope is built to
resolve. Inside it, the aim is that every request is resolved correctly.

| Step | What it adds | Calls covered (cumulative) | Coverage |
|---|---|---:|---:|
| **Tonight's scope** | Booking (excluding the burning-smell cases), membership, billing and warranty answers, estimates, redirects | 245 | **58.3%** |
| Appointment changes, as time allows | Fee-free reschedule, then confirm, then cancel | 246, 254, 260 | 58.6%, 60.5%, 61.9% |
| A payment system | Payment links, autopay | 288 | 68.6% |
| Membership billing | Auto-renew changes, upgrades, join-and-book | 311 | 74.0% |
| Meridian's own records | Manufacturer registration, repair history | 327 | 77.9% |
| **With people by design or policy** | Disputes, refunds, complaints, safety, commercial, late technician (79 calls); reschedules inside 24 hours, which carry the $49 fee (14 calls) | 93 | **22.1%** |

Five calls in tonight's scope are "wrong number" calls that count as resolved. **Excluding them, tonight's coverage is
57.8%.** Both figures are reported. The earlier figures (65.2%, 81.2%, 18.8%) were superseded on 2026-10-20 when Innocent
decided that the AI never makes a fee-bearing change (14 of the 15 reschedule calls are inside 24 hours).

**Against the brief's target.** The brief asks for 60–75% containment. Containment cannot exceed coverage times resolution,
and tonight's coverage is 58.3%. We report the honest number and say why, and we do not bend the test set or the definition to
reach the brief's target (audit C-4). The roadmap shows where the next points come from: connecting payments, membership
billing and Meridian's records, not a better prompt. The last 22.1% should stay with people.

**The decisions that fixed the scope** (all *Decided*, Innocent 2026-10-20; audit and consolidated §9.7):

| ID | Decision |
|---|---|
| DEC-1 | Build the availability check and booking first; then reschedule, confirm and cancel, in that order, as time allows. |
| DEC-2 | The AI grants no waivers, discounts or refunds. Only a human may. |
| DEC-3 | Identity for private details uses a simulated one-time code delivered to a labelled demo inbox (section 6). |
| DEC-4 | Outdated copies are excluded from the retrieval corpus; the issued files are not edited. |
| DEC-5 | Voice is out of scope. It may be revisited only if everything required finishes early. |

---

## 4. Data traps we caught

**Sources:** [brief audit](analysis/2026-10-20-brief-audit.md) §1–§4 (C-, K-, D-) ·
[PRD](prd/inno-aea-callcenter-prd.md) R-10 ·
[inventory](data/handoff-information-inventory.md) §5.3, §10.2 ·
[stage7 data contract](design/contracts/stage7/data.md) §3 · [data decisions](plans/7b-decisions/data.md) DAT-13, DAT-18.

The brief asks whether we "looked at what was actually in the knowledge base and transcripts, or assumed". Each trap below
has a location, what it is, and what the system does about it. Undocumented handling does not count as catching a trap.

| # | Trap | Location | What it is | What the system does | Status |
|---|---|---|---|---|---|
| 1 | Stale membership terms | `archive/comfort_club_overview.md` (K-6) | Old price and terms, and a promise of "cancel any time for a full prorated refund" that the company no longer offers | Excluded from retrieval; the current file (effective 2026-01-01) and the fee PDF win. Quoting the archive would be a liability | *Decided* (DEC-4, 2026-10-20) |
| 2 | Stale warranty terms | `archive/warranty_terms_2023.txt` (K-8, K-9, K-10) | 90-day repair warranty and older install and registration terms | Excluded; repair labor is 1 year and install labor 2 years (5 if a member at installation), from `warranty/warranty_policy.md` | *Decided* (DEC-4) |
| 3 | Old FAQ copy | `faq/faq_old_copy.md` (K-1, K-2, K-4) | Old diagnostic fee, after-hours fee and phone hours, undated | Excluded; the dated FAQ, the price book and the 2026 fee PDF agree and win | *Decided* (DEC-4) |
| 4 | Outdated scheduling guide | `services/scheduling_guide.md`, Rev 2024-11 (K-5, C-8) | A 48-hour cancellation rule that contradicts the current 24-hour rule, and "same-day overflow slots" that the database does not have | Excluded. Its useful content (emergency thresholds, waitlist mention) is kept as labelled known gaps, never as an answer source | *Decided* (DEC-4, round 3) |
| 5 | Staff-only notes | `internal/agent_discretion_notes.md` (K-15) | "Do not read this document to customers." Lets *human* agents waive fees and give courtesy discounts | Never in any customer index (DAT-13). It is written to a separate staff file and informs handoff briefs and staff views only. The bot grants no waivers | *Decided* (R-10, DEC-2); mechanism DAT-13 |
| 6 | Duct-cleaning stub | `services/duct_cleaning.md` (K-14) | A single "TODO" line | Never indexed (DAT-18). "Do you do duct cleaning?" is answered from the service catalog ("not offered", a staff referral on request) | *Decided* (R-10; DAT-18 settled by source) |
| 7 | Holiday hours as a picture | `policies/holiday_hours_2026.png` (K-13) | The text exists only as an image; a text-only pipeline silently loses it | Transcribed by hand once, verified, stored with a link to the image, and indexed through the transcription | *Decided* (R-9) |
| 8 | Contradictions the data carries | Invoice INV-204411 (D-8); K-9; K-10; K-3 | The invoice bills after-hours dispatch at $144 where the fee schedule says $149; membership *now* does not decide the install warranty; the database has no registration field; whether members pay the holiday fee is unresolved | Invoice lines are explained **as billed** and never adjudicated; the mismatch goes to staff-only fields. The warranty answer states the 2-year term and offers a staff confirmation. Registration is stated as policy, never confirmed for a unit. The holiday fee answer says it applies and the technician confirms | *Decided* (WP-2, Innocent 2026-10-20; R-17) |
| 9 | Service-area gaps | `policies/service_area.md` (K-11) | Adds Dripping Springs 78620 and Manor 78653, but the schema maps no zone to them; Lakeway "west of 620" conflicts with the blanket 787xx rule | Both added towns are bookable in the `central` zone, configured in code (*Decided*, Q-3, Innocent 2026-10-20). Lakeway ZIPs are treated as not served: **[A]** a two-ZIP list, replaced by a check of the full USPS list at Stage 9 (CAS-8) | Q-3 *Decided*; Lakeway **[A]** |
| 10 | Actions the systems cannot do | Inventory §5.2 | 74 calls look routine ("send me a payment link") but no payment link, autopay or auto-renew flag exists | The agent never pretends. It states what it can do, creates a case for the unfinished task, and says so plainly | *Decided* (D4, 2026-10-20) |
| 11 | Transcripts are not answer keys | Inventory §5.3 (17 rows) | Human agents quoted a reschedule with no fee, an invoice $60 above a quote, a "two business days" refund callback where policy says one, and so on | Expected answers in the eval come from the current knowledge base and database. A transcript supplies only the question and the right *kind* of outcome | *Decided* (audit D-5) |
| 12 | Templates, noise and a synthetic calendar | Inventory §2, §10.2 | The 420 calls come from 46 opening templates; 92 calls carry noise ("you cut out", "I'm driving"); 66 calls fall on a Sunday; timestamps look synthetic | The test set is split by template (section 10); filler turns are ignored in discovery and the agent must cope with the same noise typed by a reviewer; "one business day" is computed from a stated clock and calendar | *Decided* (EVQ-1) |
| 13 | The real clock | Dataset README (C-9) | The dataset says to treat 2026-10-16 as "today"; review happens later | A configured demo clock, shown in the UI. Relative dates and the 24-hour rule are computed from it, never from the server clock | *Decided* (R-3) |
| 14 | Identity is "name and phone" | Inventory §10.2 (D-6) | Human agents disclose an account after hearing a name and a phone number; on a public site that enables account fishing | Locate is not proof. A simulated one-time code goes only to the contact on record, in a labelled demo inbox (section 6). No match, an ambiguous match or a failed code all look the same to the customer | *Decided* (DEC-3, R-15, R-16) |
| 15 | Prompt injection | Audit D-10 | No instruction-like text was found in the transcripts or the knowledge base, so injection will come from the reviewer | Retrieved and database text is quoted, never obeyed; tool output never enters the stored chat; the responder has no tools (section 6) | *Decided* (R-45, R-46) |

---

## 5. Knowledge base: ingestion, chunking, retrieval

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) R-9…R-13, §4.3a ·
[system design](design/system-design.md) (DO-1) §11 decision 10 · [evaluation plan](design/evaluation-plan.md) (DO-5) E-2 ·
[stage7 data contract](design/contracts/stage7/data.md) §3, §4 ·
[data decisions](plans/7b-decisions/data.md) DAT-11, DAT-12, DAT-17, DAT-18.

**Where answers come from.** The knowledge base is issued by Meridian, not generated by us: 17 files. The agent answers
company questions only from those files and from the scheduling database. A question the files cannot answer ("Who owns
Meridian?") gets an honest "I don't have that information" and an offer of a person; the agent never fills the gap from
general knowledge. The PRD §4.3a knowledge map assigns every kind of question to its current source and its excluded twin,
and doubles as the retrieval eval's answer key.

**Every format and how it is parsed** (R-9; one manifest row per file, 17 in total):

| Format | Files | How it is parsed |
|---|---|---|
| Markdown | policies, FAQ, catalog, membership, warranty and the other prose files | Split at headings; the heading path becomes the chunk's `section` |
| Plain text | the archived 2023 warranty text (excluded) | Parsed and recorded in the manifest as excluded; paragraph groups if it were indexed |
| PDF | `pricing/2026_fee_schedule.pdf` | Text extracted from the PDF, then paragraph groups |
| CSV | `pricing/repair_price_book_2026.csv` | **One row per chunk**, so a price lookup returns exactly one row |
| PNG | `policies/holiday_hours_2026.png` | Through its hand-verified transcription, stored with a link to the image |

**What is excluded, and why** (R-10; the manifest records each row's status and reason, and `chunks` is 0 for every row that
is not current):
- **Excluded** (stale or contradicted): `archive/*`, `faq/faq_old_copy.md`, `services/scheduling_guide.md` (section 4, rows 1–4).
- **Staff-only**, never embedded and never quoted to customers: `internal/agent_discretion_notes.md` (kept in a separate staff
  file, DAT-13).
- **Stub**, never answered from: `services/duct_cleaning.md` (DAT-18).
- The issued files are never edited.

**The chunking method, and why it comes from the knowledge base's own shape** (DAT-11, **[A]** until the first E-2 run):
- Split at Markdown headings; the heading path is the chunk's `section`, which becomes the citation.
- A section over 1,100 characters is cut at paragraph breaks into pieces of about 900 characters.
- No overlap, because sections in this knowledge base are self-contained.
- Why not a default ~500-token split: every file in the knowledge base is at most 2.1 KB with 1 to 8 headings [M], so a
  default split would make most files a single chunk and lose the section citation that R-11 requires. The rule
  `source-authority` 2 says chunking must come from what is actually in the corpus.
- Replaced by: the first E-2 retrieval run (hit rate at 3 per query). A change is made only for a named failure type.

**Embeddings and the index.** `BAAI/bge-small-en-v1.5`, run locally, cosine similarity on normalised vectors. The index is
built once at `docker build` from the ingestion manifest and ships inside the image, so the served index always matches the
deployed manifest (DO-1 decision 10). The corpus is 17 files, so a hosted vector service is unnecessary. The ingestion run
record sits beside the index (DAT-12).
**Built index chunk count:** `pending: AEA-16 index record`

**`k` and the relevance floor** (DAT-17, **[A]**): `k = 3` and a cosine floor of 0.60. They were chosen from one pre-build
check **[M]**: the parked chunker over the issued knowledge base (61 chunks, 60 of them current) and the cached
`bge-small-en-v1.5`, scored on 12 in-corpus and 8 off-corpus questions. Top-1 scores for the in-corpus questions ran
0.616–0.842. The off-corpus questions ran 0.399–0.649, and the example in user story US-7 ("How long have you been in
business?") scored 0.563. So 0.60 keeps all 12 in-corpus questions and refuses US-7's example.
**The stated limit:** the two score ranges overlap, so the floor alone cannot refuse every off-corpus question. R-13
("answers come only from retrieved current text") and the R-46 fact check still carry those refusals. The same check also
showed "Do you service Manor?" ranking the FAQ first rather than the service-area policy; that is flagged for the first
E-2 run and not changed here. This check was not run on the built index. **Replaced by:** the first E-2 run (hit rate with
no floor, plus the off-corpus below-floor rate): `pending: AEA-24 E-2 run`.

**Citations.** Every policy answer carries the file, the section and the file's version date, so the customer and the
reviewer can see which current document it came from.

**Why retrieval is evaluated on its own (E-2).** "Correct document" means the **current** one. Returning the archived
membership page for a price question is a retrieval failure even though the text matches. The retrieval eval therefore has
queries where a stale copy is the closest text match, and it counts excluded-file hits separately. It runs before the
end-to-end eval, so a wrong answer can be traced to retrieval or to the model. Target: hit rate at 3 of at least 90% [T,
framing V1]. Result: `pending: Stage 9`.

---

## 6. How one turn works

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) §6.1 ·
[system design](design/system-design.md) (DO-2) §A.1, §A.2, §A.6 and (DO-1) §3.2, §10 *What each vendor sees*, §11
decisions 3, 6, 7, 9 · [hard problems](design/hard-problems.md) HP-1, HP-4 ·
[SP-1 spike](analysis/spikes/SP-1-two-layer-turn-latency-cost.md) §3–§4 · [stage7 data contract](design/contracts/stage7/data.md) §1.

**What it does in practice.** A customer message enters the graph. Code checks run first and can finish the turn alone
(safety, a request for a person, the AI paused, a code entry). Otherwise a planner decides "just talk" or "act", specialists
do the acting with narrow tools, code decides whether to escalate, the turn's facts are gathered, and a responder with no
tools writes the reply. Code checks that reply before the customer sees it, and code appends the promise and reference.

**The two-layer shape** (HP-1, *Decided*, Innocent 2026-10-20, his own design):
- **Action layer, has tools:** code gates, the planner, the specialists (knowledge, account, scheduling), the escalation
  check, the handoff.
- **Conversation layer, no tools:** the safety reply (fixed text, no model), the turn facts, and the responder.

**Every place a model chooses, and why code still decides the rest** (DO-2 §A.6):

| What is chosen | Model | Why a rule would not do | What code still decides |
|---|---|---|---|
| Whether a message the rules passed is dangerous | Jev | Rules miss paraphrase and combinations ("my mother is 88 and it's 95 degrees in here") | The rules decide alone when they match; the label may only **raise**, never lower, and only picks a fixed path |
| Talk or act, and which specialists in what order | Jev | A keyword router breaks on mixed messages (a customer asking three things at once) | Safety, a person request, AI paused and code entry never reach the planner |
| Which tool, with what arguments, inside a task | Sonnet | Fixed flows break on variations ("actually Tuesday instead") | Every rule inside the tool: identity, zone, slot status, the 24-hour check. There is no waiver tool |
| The words of the reply | Sonnet | Templates cannot answer from passages | Promise, reference and safety text; the completion and fact checks |
| The brief's "what the customer needs", claims and open decision | Sonnet | A transcript-only brief makes staff re-read the chat | The other five headings come from state; the fact check |
| Which passages are similar to a question | embeddings | Similarity, not a decision | Which files may be indexed at all |

**Model mix B** (*Decided*, Innocent 2026-10-21, after the SP-1 spike): Jev (`typesafe/jev-1.13`, reached through
OpenRouter) does the planner and the danger classifier; Claude Sonnet 5.5 does the specialists, the responder and the brief.
In the SP-1 spike on a throwaway build, this mix measured **[M]** about $0.016 per conversation on average and a 95th
percentile turn time of 10.2 s with 20 conversations at once. Across all four mixes the spike tried, there were 0
hard-gate failures in 190 scored conversations.
Those are spike numbers, not results from the built system: `pending: Stage 9` re-measures against the 12.5 s line.
Model names live in configuration, so a role can change without code changes.

**Turn-to-turn context is rebuilt each turn** (R-45, *Decided*, Innocent 2026-10-20). State is typed and durable per
conversation: identity status, open tasks and what is still missing, the record and passage IDs from the latest lookups,
any pending change request or open case with its promise, failure counters, and who controls the chat. Each model sees only
its slice: the planner sees the recent clean chat plus a state summary, a specialist sees its task and the state it needs,
and the responder sees the recent clean chat plus this turn's facts. Tool output never enters the chat history. The window is
about 10 turns **[A]**, replaced by the multi-turn cases in the dev set. **Completed actions are re-read from the database at
the start of every turn.** The SP-1 spike showed why: a reschedule done in turn 3 was denied in turn 4 when the responder
saw only that turn's facts (DO-1 decision 3).

**Checks on the model's words** (R-46, HP-4 option B, *Decided*, Innocent 2026-10-20):
- A **completion check** blocks any reply claiming an action ("done", "cancelled", "moved", "refunded") unless a write tool
  succeeded in that turn.
- A **fact check** compares every number, date, ID and amount in the reply and in the brief headings with the turn facts and
  the lookup log, removes anything unmatched, and flags the heading.
- Replies are sent whole, not streamed, because both checks need the whole reply first (*Decided*, SDQ-2, Innocent 2026-10-21).

**Identity.** Public questions and safety need no verification. For private details, the agent locates the record by name and
phone, customer ID or invoice number (a locator is not proof). It then sends a **simulated** one-time code to the contact on
the record, delivered only to a labelled demo inbox, never shown in chat. The code expires after 10 minutes and allows 3
attempts; it is stored hashed and never logged. The code-entry turn is checked by code with no model call, and the stored
chat keeps "[code entered]", never the digits (R-15, *Decided*; the numbers are the defaults Innocent accepted).

**What each vendor sees** (DO-1 §3.2 and §10; *Decided*):
- **Anthropic (Sonnet)** gets redacted text and the task's own fields: card-like numbers and verification codes masked, email
  addresses and street addresses masked, and phone numbers reduced to their last two digits (the SONNET profile, DAT-5,
  settled by the system design). Names, customer and invoice IDs and account facts stay, because the specialist needs them.
  Anthropic's terms exclude training on inputs.
- **Jev through OpenRouter** gets redacted text only (names, phones, emails, addresses, customer and invoice IDs, codes and
  card-like numbers replaced by placeholders) plus **typed flags** (verified yes or no, open task kinds, who controls the
  chat), never account values. Every request sends `provider.data_collection: "deny"`. TypeSafe states that training on
  inputs is excluded, but states no retention period; that is an **accepted known limit** (section 12).
- **Langfuse** (on Innocent's own server) gets spans masked in our process before export (section 9).
- Card numbers are never asked for or accepted. One typed in chat is masked before storage and before any model, and the
  reply says cards are not taken in chat.

**How loose names in free chat are handled (DAT-1): Proposed, awaiting Innocent.** The built redaction recommends option A:
introduction patterns ("my name is …", "this is …", "I'm …" followed by capitalised words) and a street-address pattern,
with the limit written down: a name typed loosely in free chat ("Omar here, my AC died", "my mother Jane is 88") may reach
Jev (under `data_collection: deny`) and Innocent's own Langfuse. The locate step uses a form payload that never reaches a
model, which is the main place a name and address arrive. If he picks option B, the located customer's own values are also
masked wherever they appear (a change to the model gateway's interface); if he picks option C, a name-recognition model is
added to the image. What the redaction function replaces per profile is in the
[data contract](design/contracts/stage7/data.md) §1.

---

## 7. Scheduling

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) §4.5 (R-18…R-23) · [hard problems](design/hard-problems.md) HP-3 ·
[consolidated handoff direction](analysis/2026-10-20-human-handoff-consolidated-direction.md) §9.3 ·
[stage7 cases contract](design/contracts/stage7/cases.md) §2, §4.

**What it does in practice.** The agent finds the windows that fit the customer's zone and service type, books the one they
pick, and confirms the date, window, technician and fee. If the request cannot be met, it says so and offers the nearest
alternatives. It writes only to a **working copy** of the scheduling database, never the issued file, and a one-command
reset restores the copy.

**Booking rules** (R-18; *Decided*, with Q-3 settled by Innocent 2026-10-20):
- A slot matches when its zone equals the customer's zone: **north**, **central** or **south**, by city or ZIP. Dripping
  Springs (78620) and Manor (78653) are bookable in `central` (configured in code; the issued schema is not edited). San
  Marcos, Bastrop, Elgin and Lakeway are not served (Lakeway's ZIPs: **[A]**, section 4).
- The slot must be `open`, match the service type, and be member-reserved only for members.
- Estimates book `estimate` slots with a Comfort Advisor. Before a non-urgent repair, the knowledge base's quick checks may be
  *offered* and are never required, and are skipped for urgent and safety cases (R-44, optional).
- The date is the **configured demo clock** (Friday 2026-10-16), not the server clock (R-3), so "tomorrow" and the 24-hour
  rule behave the same on any review day.

**Fees by tier** (R-20; from the fee schedule and the membership document; a single table in code, never typed into a
sentence): the diagnostic visit is $89 for non-members and waived for members; a seasonal tune-up is $129 for non-members and
included for members; an estimate is free. The 24-hour rule: a change or cancellation **more than** 24 hours before the window
is free; **inside** 24 hours it carries a $49 fee.

**One transaction, with a re-read** (R-19, DO-1 §2.1 and §9). The availability check, the slot update, the action record
and the lookup-log row commit in **one** SQLite transaction. A slot shown earlier is re-read inside that transaction, never
trusted from a cached list; if it was taken meanwhile, the customer gets fresh alternatives. Retries are idempotent, and no
slot can be double-booked. SQLite allows one writer at a time, which is fine at the design load (section 11).

**Fee-bearing changes become staff requests** (R-21, R-22; *Decided*, Innocent 2026-10-20, Stage 3):
- A reschedule or cancellation inside 24 hours is **never** done by the AI, even if the customer says yes.
- The agent verifies the customer, explains that "the $49 fee applies under current policy" (never "charged"), records the
  requested change (wanted time, slots shown but not held, reason, hours before the window), and says the original
  appointment stays until a person confirms.
- It hands off as a **P2** case with an internal due time at the window start and an immediate supervisor alert. If
  confirmation before the window cannot be guaranteed, the customer is told so plainly. The fee is never waived by the AI.
- It counts as an escalation, not a resolution. A fee-free move passes the normal booking rules.
- Order of delivery (DEC-1): booking first, then fee-free reschedule, then confirm, then cancel, as time allows.

---

## 8. Escalation and handoff

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) §4.2, §4.6 · [hard problems](design/hard-problems.md) HP-2, HP-4 ·
[consolidated handoff direction](analysis/2026-10-20-human-handoff-consolidated-direction.md) §4–§6, §9.1–§9.5 ·
[stage7 cases contract](design/contracts/stage7/cases.md) §3 ·
[graph-core contract](design/contracts/stage7/graph-core.md) §3 (GRC-3 ledger) ·
[cases decisions](plans/7b-decisions/cases.md) CAS-16 · [graph-core decisions](plans/7b-decisions/graph-core.md) GRC-3.

**Safety first** (R-5…R-8, *Decided*, Innocent 2026-10-20). A deterministic check runs first on every turn. A gas or
rotten-egg smell, a carbon-monoxide alarm, sparks, smoke or flames, or a burning smell with tripped breakers gets Meridian's
own written instruction in the same turn, word for word and with no model: leave the home and call 911 or the gas utility
from outside. Then the agent offers to take contact details (never a gate) and opens a **P0** case even with no account
match, with **no follow-up time promised**.

**Danger detection** (R-47, HP-2 option C, *Decided*). Typo-tolerant word rules run first and decide alone when they match.
Then a small, cheap classifier reads the message and may only **raise** it, never lower it. Its label only picks a fixed
path, it never writes the reply, and if it fails or times out the rules stand. Targets **[T]**: danger recall 100% on labelled
synthetic cases; false alarms at most 10% on no-danger comfort cases. Result: `pending: Stage 9`.

**No heat, no cooling or an active leak** (R-8, *Decided*, Innocent 2026-10-20, narrowed at the Stage 2 check) is a normal
booking with skippable urgency questions. Only when the customer says someone is in danger because of the conditions does the
agent give the 24/7 emergency number first (a **placeholder** in the demo, because Meridian is fictional), open a **P1**
case, and, if nobody is online, add a *separate* "reviewed within 1 business day" line that is never framed as the emergency wait.

**When a representative holds the chat: does safety still come first? (GRC-3) Proposed, awaiting Innocent.** The sources
disagree: R-5 says the safety check runs first on every turn, while the design put "AI paused" first. The build uses the
recommended option A: for the safety phrases only, the fixed safety card still shows in the same turn while the representative
stays in charge, and everything else goes only to the representative. If he picks B (paused first), the message goes only to
the representative, and the safety instruction depends on how fast a person reads; if he picks C, every code-only safety gate
runs first. The order is one tuple in the gate code, so a change is one line.

**The burning-smell paths** (R-7, *Decided*; each path was checked by Innocent on 2026-10-20). The agent asks whether breakers
have **already** tripped and whether there is smoke, sparks or flames (it never asks the customer to go and check).
1. "Yes" to either: the P0 safety path above.
2. "Not sure": a conditional safety instruction, the emergency number and a **P1** case.
3. "Clearly no to both": the earliest repair booking marked urgent, plus a priority case.

**The priority of path 3 (CAS-16) is Proposed, awaiting Innocent.** Every source says "a priority case" and none says which
level. The build uses the recommended option A: **P2** (time-sensitive), with a new reason `burning_ruled_out` and an internal
due time at the urgent booking's window start, so staff look before the technician arrives. It sorts after P0 and P1 and does
not count as an emergency, which keeps the false-alarm rate honest. If he picks B (P1, the same as "unclear"), every burning
smell is emergency priority; option C would make it a routine case. The priority table is one row in the handoff policy, so a
change is one row plus its tests. The policy-owner confirmation of the gap handling itself is deferred to section 12 as a
labelled assumption (interview Q-046).

**What escalates, and what priority.** Triggers (R-24, *Decided*, OD-6): a policy list (billing dispute, refund, conduct or
manager request, legal threat or chargeback), safety, a direct request for a person, failure signals, D4's unfinished tasks,
and a fee-bearing change request. Informational limits answer without a case. Priority is set by **code**, never the model:
P0 safety, P1 emergency-priority (danger, or a burning smell with unclear risk), P2 time-sensitive, P3 standard (policy says a
person), P4 routine follow-up (an unfinished action, no deadline). A request for a person is honoured on the **first** ask (R-2),
by button or words, and the button needs no model at all.
Failure signals use two-attempt thresholds that Innocent accepted as **starting hypotheses** to be tested on labelled
cases (**[A]**, OD-6); the escalation triggers rest on synthetic cases, which is listed in section 12.

**The promise table, and why the model never writes it** (R-26, *Decided*, OD-4). The promise text and due time come from a
fixed policy table: nobody online means a representative will get back within 1 business day; a refund request means a
representative will get to it within 2 business days (a response, not a refund, and no outcome is promised); when a
representative is on shift, a representative will join the chat when available; and no time at all is promised for safety,
emergency response, arrival or outcomes. A reference number is given every time. A fee-bearing change request adds a line
saying that nobody can promise a confirmation before the appointment starts. A model that writes a promise can invent a time
or an outcome, and the transcripts show how much damage inconsistent promises do. So the model is told nothing to promise;
code appends the policy-table text and the reference after the model's words, and the eval checks the match word for word
(hard gate, M-10).

**The brief and its fact check** (R-28, R-46, *Decided*). Each handoff carries a brief with eight fixed headings, plain words
and exact numbers: why this came to you; what the customer needs; what we know for sure; what the customer says (not checked);
what the AI did; what we told the customer; what you need to decide; who they are and how to reach them. Facts, the promise,
the AI's actions and identity come from state. Only "what the customer needs", the claims and the open decision use a
constrained model call, and every number, date, ID and amount in the brief is checked against the lookup log. A mismatch
between two sources is stated as a fact ("the fee schedule says $149, the invoice says $144"), never as a verdict ("he was
overcharged"), which belongs to the supervisor. Each brief links to the full chat and to its sources (R-29).

**Staffing and same-chat takeover** (R-30, R-31, *Decided*, OD-1, OD-2). Default: **nobody is online**, so the async promise
applies. A labelled "Demo: simulated staff on shift" mode shows a banner on the customer and staff screens. In simulation, the
reviewer opens the staff console, claims the case and replies in the **same** conversation; the AI pauses visibly and the
hand-back or close is explicit. No live queue is ever offered while nobody is online.

**What the customer sees.** The reference number and the promise, a follow-up preference (the default is email, unless they
prefer a phone call; the case stores the channel, destination and any callback window; private details only go to a contact
on the record after the code), and a plain statement of what happens next. Follow-ups and calls are **recorded, never sent**,
and are labelled "Demo: recorded, not sent" (R-27, R-34).

---

## 9. Monitoring and the feedback loop

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) R-35…R-37 ·
[observability contract](design/observability-contract.md) (DO-6): records, *Content and redaction*, *Open items* ·
[key-metrics registry](design/key-metrics-registry.md) (DO-7) M-22…M-29 ·
[consolidated handoff direction](analysis/2026-10-20-human-handoff-consolidated-direction.md) C5 ·
[stage7 models contract](design/contracts/stage7/models.md) §4 (MOD-6 project check) ·
[system design](design/system-design.md) SDQ-3 · [data decisions](plans/7b-decisions/data.md) DAT-4.

**The monitoring page** (SCR-10, R-35) reads stored data and never recomputes it. It shows:
- volume: conversations, turns and handoffs by reason (M-22);
- containment (correct resolution) and escalations by reason (M-1, M-5);
- failures: turns ended by a model or tool error or timeout, per 100 turns (M-24);
- latency at the 50th and 95th percentile (M-23);
- spend today against the daily cap, and cost per conversation (M-25, M-26);
- unowned and overdue cases with their age (M-27);
- health-check restarts (M-28);
- trace export, as "sent n of N" or "off" (M-29).

Alerts are shown **as decision lines**, each one saying what to do:

| Signal | Line | Label |
|---|---|---|
| Volume | No new live conversation for 4 hours, not counted between 10pm and 6am Austin time | *Decided*, Innocent 2026-10-21; the hours are a config value |
| Failure rate | Above 2 per 100 turns: alert, and the agent falls back to handoff | **[T]**, Q-058 |
| Spend | $30 per day reached: the agent hands off and stops calling models; the day runs midnight to midnight Austin time | **[T]**, Q-061; day boundary *Decided* 2026-10-21 |
| Overdue cases | Any overdue case alerts the supervisor view | *Decided*, C3 |
| Latency | 95th percentile above 12.5 s at 20 conversations at once: check the model and retrieval spans | **[T]**, Innocent 2026-10-21 |

Health and correctness are shown **separately**: "it is up" never stands in for "it is right". Alerts stay on this page and a
health check restarts the service if it stops responding (*Decided*, Q-045 = A, Innocent 2026-10-20). Pushing alerts to a
channel is a roadmap item, not built.

**Traces go to the self-hosted Langfuse on Innocent's VPS** (*Decided*, Q-050 revised by Q-062, 2026-10-20), so traces stay
on his own server. Details:
- Spans are masked **in our process** before export (Langfuse's `mask_otel_spans` hook) and exported from a background thread
  with a bounded queue, so tracing is never on the request path. If the VPS is unreachable, spans are dropped and counted, and the
  turn is unaffected.
- Export turns on only when all four Langfuse settings are present **and** the server confirms that the keys belong to
  exactly one project whose ID matches this app's (MOD-6). Anything else leaves export off, and every turn then records
  `trace_export = off`, so the monitoring page shows the `trace_export_failed` alert for as long as the app runs that way.
- The deployed app (on Railway) reaches the VPS through a TLS reverse proxy that exposes **only** the ingestion path; the UI
  stays on localhost behind an SSH tunnel. The method is *Decided* (SDQ-3, 2026-10-21).
- **Opening that route, and on which hostname, is Proposed, awaiting Innocent (DAT-4).** The recommended option A is a yes on
  a subdomain he names, so a reviewer's live session is traceable. If he picks B, deployed trace export stays off and the page says
  so; local runs on the VPS still trace.
- Trace retention follows the 90-day bound that applies to case data (*Decided*, 2026-10-21).

**What a record may hold.** Verification codes are never stored raw anywhere (hash and expiry only). Card-like numbers are
masked at intake. Names, phones, emails and addresses are raw only in the database and staff views by role, masked in traces
(a phone keeps its last two digits), and never in logs. Logs hold IDs, statuses, timings and counts only, and message text
reaches a log as a length. The monitoring and evaluation pages show aggregates; the evaluation page also shows redacted
dev-split failure examples. A seeded-value test proves the absence of a name, phone, card-like number and code in the HTTP
body, the log and the exported trace (R-36).

**The feedback loop** (R-37, brief Part B goal 7: "Describe how the loop works even if you only implement the first step").
1. Staff (a representative or supervisor) **flag** an AI answer, brief or escalation as wrong in the case view.
2. The flag appears on a **review list**. That is the first step, and the one this build implements.
3. A human reads the flagged trace. Only after that, and only if Innocent has confirmed the expected output from the sources,
   can it be **promoted** to an evaluation case (an unreviewed trace is never a case).
4. A fix is made only against a named failure type, and scored on the frozen dev cases before and after.

**What is deliberately not automatic** (audit C-13, G-6). Nothing reaches the knowledge base, the prompts or the evaluation
set without human review. The reviewer's attack inputs will be in those logs; an automatic loop would turn "try to break it"
into a poisoning path. R-37 is a "should" item (priority S): it ships after the Must items pass their checks.

---

## 10. Evaluation method

**Sources:** [evaluation plan](design/evaluation-plan.md) (DO-5), all sections ·
[PRD](prd/inno-aea-callcenter-prd.md) R-38, R-39 · [stage7 data contract](design/contracts/stage7/data.md) §5, §6 ·
[data decisions](plans/7b-decisions/data.md) DAT-2, DAT-16, DAT-27.

**The test set comes from the transcripts, and the answer key does not.** Expected outputs are written *before* the run that
scores them, from the current knowledge base, the database and Innocent's recorded decisions, never from what the human agent
said (audit D-5) and never by a model grading itself. A case whose answer no source settles is not scored until he decides.

**Where cases come from, in the order they are built:**
1. The first dev set: the eight worked pairs, a fee-free variant of the reschedule pair, and two labelled synthetic danger cases.
2. Transcript-derived cases, in proportion to the corpus, with a seeded customer substituted where the caller is not in the
   database. Planned size: about 60 **[T]**.
3. Labelled **synthetic** cases for what the transcripts do not contain: safety phrasing variants, a direct request for a
   person, failure signals, identity edge cases, prompt injection, and danger and no-danger comfort cases (0 of 420 calls
   mention a vulnerable occupant [M]). Planned size: about 15 **[T]**. Each is made by changing one named dimension of a clean
   case, and its label states the assumption it encodes. Synthetic cases are never mixed into a number without saying so.
4. Retrieval queries: one per knowledge-map row and per stale-twin trap.
5. Promoted traces, only after a human review (section 9).

**Dev against sealed held-out, split by template** (*Decided*, Q-054 = A, Innocent 2026-10-20; refined by EVQ-1 = A, Innocent
2026-10-21):
- The 420 calls come from 46 opening templates, so a random split would put near-copies of one call on both sides and measure
  memory of the dev set. Every template therefore goes whole into one split.
- **34 of the 37 categories have exactly one template** [M, call map], so splitting by template and stratifying by category
  cannot both hold. Innocent chose to stratify by **driver family and support level** instead, with a seeded draw whose seed is
  recorded. The report lists which categories sit in each split, so nobody reads a category's absence as a result.
- The **dev split** is where we read failures and fix. The **sealed held-out split** is scored only, once, on the agent version
  that will be submitted, and it alone gives the README number. A fix made after reading a held-out result turns that split
  into a dev split, and the report must say so.

**How the held-out key is kept from build agents until scoring (DAT-2): Proposed, awaiting Innocent.** The repository is
public and every build agent works inside it, so nothing yet excludes the key, and a shell search bypasses a read deny rule.
The build uses the recommended option B: scripts (the customer's turns) stay in `eval/cases/heldout/`; the answer keys sit in a
folder **outside** the workspace, under a deny rule, written by an agent that takes no later build ticket; the keys' SHA-256 is
recorded at sealing; after the held-out scoring run the keys are copied into the repository so reviewers can audit them and the
hash proves nothing changed. If he picks A, the keys sit in the repository behind a deny rule only; if he picks C, he writes
or seals the keys himself. Until he answers, no held-out key file is written.

**The case-file format** (DAT-27, *Decided*, engineering). One JSON file per case script and one per answer key, so a key can
sit apart from its script. A script records the case ID, provenance, source reference, template, category, split, seeded
customer (an ID, never a phone or email), the demo clock the case assumes, the customer turns, and whether and how it is
synthetic. A key records the gold `in_scope` label, the topic, and the checklist (`must_do`, `must_say`, `must_not_say`), each
item citing its source file or decision, plus any items only a judge can score. Contact values in a script are tokens the
runner fills from the working copy at run time; no verification digits ever appear in a file.

**How a case is scored.** Cheapest grader first: assertion, invariant, trajectory, judge, human.
- Every required sentence and forbidden phrase is a **code check**, never a judge item. The judge only sees free-text meaning,
  such as "said plainly that the original appointment stays".
- The judge is **advisory until calibrated**: it enters a gate only after agreeing with about 20 of Innocent's blind labels at
  0.8 or better **[T]**. Its model is the same family that writes the replies, which is not independent; that is open (EVQ-2).
- The judge has its own spend cap of $5 per Chicago day **[A]** (DAT-16), which partitions the decided $30 daily cap and
  spends nothing new; the preflight refuses a paid run if today's spend plus the estimate plus the judge cap would pass $30.
  Replaced by the first E-1 run's measured judge spend.
- The harness is frozen before the runs it scores: its commit and a digest are recorded, a tamper check compares them, and a
  dry run on mocked responses comes first.
- Each suite runs 3 times **[A]** (SP-1's repeat count, replaced if the measured spread is too wide to read a move); the
  report shows the pooled rate with its spread, and a move smaller than the spread is not a result.

**How containment is computed.** On the test set, **containment = conversations correctly resolved ÷ all conversations**
(M-5), shown beside scope coverage (M-4) and in-scope correct resolution (M-1), because containment is their product. A
conversation ended in a handoff because a model or tool failed counts as a failure for the north star and is filed apart from
wrong answers (operational degrade). Every report line is "n of N" with its split, run ID, agent version and date. A target
(the brief's 60–75%, our at-least-90%) never appears as a result; if shown, it sits in its own column labelled "Target".

**Results.**
- Link to the test results (deliverable D-6): `pending: D-6 test results, filled by Stage 9`.
- Every number: `pending: Stage 9` (first dev-set run, retrieval hit rate, end-to-end dev and held-out runs, load run).
- What exists today is the SP-1 spike baseline, measured on a throwaway build and reported in the evaluation plan's
  *Baselines* table; it is not a result of the built system.

---

## 11. Production thinking

**Sources:** [system design](design/system-design.md) (DO-1) §2.3, §6–§9, §11 decisions 1, 2, 4, 5, 11 ·
[PRD](prd/inno-aea-callcenter-prd.md) R-41, R-48 · [stage7 web contract](design/contracts/stage7/web.md) §5, §6 ·
[web decisions](plans/7b-decisions/web.md) WEB-1, WEB-2 · [data decisions](plans/7b-decisions/data.md) DAT-3, DAT-19.

**Load the design is built for** (*Decided*, Innocent 2026-10-20): about 100 agent conversations a day and a spike of about 20
at once **[T]**. At that load, one process holds 20 at once with every resource under half its limit **[C]**; the first thing
to watch is the latency tail. Cost per conversation is a **[M]** spike figure (section 6), far under the daily cap.

**What survives a restart** (*Decided*, SD-7.2). Conversations, cases, promises and completed actions live on a Railway volume
(`/data`): the working copy of the database plus our tables in one SQLite file, and the conversation checkpoints in a second.
A turn commits its business transaction first and its checkpoint second; if the process dies between them, nothing is lost,
because the next turn rebuilds completed actions from the action table and an idempotency key stops a repeated write. A
reply in flight at the moment of restart is lost; the browser shows "That didn't send" and the customer retries with the same
turn ID. The knowledge-base index lives in the image, not the volume. **It does not survive losing the volume itself**
(stated, accepted); for the demo, reset rebuilds everything from the image. Checkpoints are pruned to the last 2 per thread
once a day (*Decided*, SDQ-10), because they are the only table that grows fast.

**The watchdog.** A health check (`/healthz`) restarts the service if it stops responding. Restart policy: on failure, with
at most 10 retries **[A]** (DAT-19, Railway's own default; replaced by the restart count on the monitoring page). One replica
only: Railway volumes forbid replicas.

**Abuse limits** (R-41):
- A daily model-spend cap of **$30/day** (*Decided*, Q-061). When it is reached, new chats hand off by design instead of
  calling a model.
- Rate limits **[A]** (WEB-2, WEB-4), all "set above 20" so they never bite a 20-at-once run, replaced by the Stage 9 load
  re-measure (0 limited responses) and abuse seen in the logs: 20 chat turns per minute per conversation, 600 per minute per
  login session and per IP; 120 reads per minute per session and 240 per IP; 10 rejected login attempts per IP per 10
  minutes, after which even the right pair gets a "try again later" answer.
- A "Talk to a person" request is never rate-limited and never needs a model.

**Deadline and admission** (*Decided*, Innocent 2026-10-21, SDQ-1 and SDQ-9). Every turn has a hard **60 s** deadline measured
from server receipt (he chose it over the recommended 20 s: "just in case there are some heavy operations"). Past it, the
customer gets a code-built "try again" reply with a "Talk to a person" button. At most **30** turns run at once; turn 31 is
refused at once with a person offer, never queued silently, and this should never happen at 20 at once. Each provider call
gets one bounded retry inside the deadline, with the SDK's own retries off.

**The one demo login** (R-48, *Decided*, Innocent 2026-10-21). One username and password from deployment variables
(`MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`) gate every route except the login page and `/healthz`; a signed cookie
follows. Once signed in, a visible switch moves between the customer view and the three staff roles with no second password;
reset and the staffing toggle sit behind the same login. The role switch is a demo convenience, not a security boundary: the
data is fictional, and the README says so.
- **Which static files may load before the login (WEB-1): Proposed, awaiting Innocent.** The login screen belongs to the same
  React app, so it needs its built script and style files and fonts. The build uses the recommended option A: `/login` plus the
  `/assets/` and `/fonts/` files are public and everything else, including every `/api` call, needs the login; that departs
  from R-48's wording only for files that are already public in the repository. If he picks B, a separate self-contained login
  page is built (about half a day); if he picks C, the whole app shell is public and only `/api` is gated. The sign-off page
  records him taking his own recommendations in bulk on 2026-10-21; this document keeps the item labelled proposed until
  the decision ledger row records his answer, because a bundled "yes" does not settle several separate items.
- **Where the reviewer gets the login (DAT-3): Proposed, awaiting Innocent.** R-48 says the README gives it; the repository is
  public (R-42), so anyone could sign in and spend model budget. The recommended option B: the README says where the login is
  given (the submission form or notes) and holds no value; until he answers, the README holds no value. This page holds no
  value either.

**The 10× scale path (written, not built)** (*Decided*, Q-029 = A; [system design](design/system-design.md) §6.3 and §7). At
about 1,000 conversations a day and about 200 at once **[T]**, what breaks first is, in order: the model provider's token
limit on the current spending tier (about 130 conversations at once **[C]**), then the single process's 40-thread pool, then the
one-replica ceiling that SQLite on a volume forces, then the $30 daily cap, which is a business choice rather than a limit. The
written steps, each with the measurement that triggers it: cache the stable prompt prefix and lower effort on chat roles;
pace requests client-side; move the key to a higher provider tier (lead time unknown); ask Innocent to raise the cap; move
durable state to Postgres; go async and run 2–3 replicas; fan events out across replicas; sample traces on the VPS. A second
region and autoscaling are deliberately not on the path. Nothing here is built.

---

## 12. Known gaps and assumptions

**Sources:** interview Q-046 in the [PRD interview](prd/inno-aea-callcenter-interview.md) · [PRD](prd/inno-aea-callcenter-prd.md) §9 risks ·
[system design](design/system-design.md) §9 · [code design](design/code-design.md) §10 ·
[7b decision records](plans/7b-decisions/data.md) (and the web, cases and graph-core records in the same folder).

**The open owner decisions: Proposed, awaiting Innocent.** Each is built on its recommended option; what changes if he picks
differently is in the section named.

| ID | Question | Built on | If he picks differently | Section |
|---|---|---|---|---|
| DAT-1 | How much name and address masking before text goes to Jev and Langfuse | A: introduction and street-address patterns, limit written down | B adds the located customer's values; C adds a name-recognition model | 6 |
| DAT-2 | Where the sealed held-out answer key lives until it is scored | B: outside the repository until scoring, then committed with its hash | A keeps it in the repository behind a deny rule; C: he writes it | 10 |
| DAT-4 | Opening the ingestion-only trace route, and on which hostname | A: yes, on a subdomain he names | B: no route, deployed trace export off, the `trace_export_failed` alert shows | 9 |
| WEB-1 | Which files may load before the demo login | A: `/login` plus `/assets/` and `/fonts/` | B: a separate self-contained login page; C: the whole shell public | 11 |
| CAS-16 | Priority of a burning smell once both dangers are ruled out | A: P2, reason `burning_ruled_out` | B: P1; C: a routine case | 8 |
| GRC-3 | Safety order when a representative owns the chat | A: safety first, then paused | B: paused first; C: all code-only gates first | 8 |
| DAT-3 | Whether the README holds the demo login values | B: the README points to where it is given | A: the README holds it; C: hold it until grading ends | 11 |

DAT-3 is not in the ticket's six, but it is open in the same ledger, so it is listed here rather than hidden.

**Assumptions, with the measurement or check that replaces each:**

| Assumption | Why it is an assumption | What replaces it |
|---|---|---|
| Jev's retention is unstated (an **accepted known limit**, *Decided* by Innocent 2026-10-21) | TypeSafe excludes training on inputs in writing but states no retention period; Jev gets redacted text and typed flags only | A published retention period, or replacing Jev |
| Losing the volume loses reviewer-created cases (stated, accepted, SD-7.2) | Railway volume backups are not stated for this plan | A nightly copy to the VPS, a cheap later step |
| Escalation thresholds are tested on synthetic cases only | The transcripts contain no repeated-failure conversations; OD-6's two-attempt thresholds are hypotheses | Labelled synthetic cases now; real traffic later |
| Wrap-up time per call is unmeasured | Only talk time (median 111 s) is in the data | Real staff timing |
| Repeat contacts cannot be measured | No identifier repeats across the 420 calls | Production data |
| Chunk sizes (1,100 and about 900 characters), no overlap | Chosen from the knowledge base's shape; DAT-11 | The first retrieval eval |
| `k = 3`, floor 0.60 | Pre-build check on 20 questions; the ranges overlap; DAT-17 | The first retrieval eval; R-13 and the fact check carry what the floor cannot |
| Conversation window of about 10 turns; about 5 turns per conversation; 30 s think time | Planning values, not measured on traffic | The multi-turn dev cases; the Stage 9 load run |
| Rate limits, login throttle, restart retries | WEB-2, WEB-4, DAT-19 | The Stage 9 load re-measure; the deploy logs |
| Due-soon window of 4 hours and unowned-after 30 minutes, on the demo clock | CAS-20 | The Stage 9 staff walkthrough |
| Lakeway's two ZIPs (and Lakeway as a city) are not served | CAS-8; the exclusion wins over the blanket 787xx rule | A check of the full USPS list at Stage 9 |
| The zero-traffic window (4 hours outside 10pm–6am) | A config value Innocent can change | Real traffic |
| The judge model is not independent of the reply model | EVQ-2 is open | Innocent naming another approved model, or accepting it |
| The Railway proxy allows a 65 s turn without a 502 | Staff answers on the community forum; DAT-20 | The deployed smoke test or load run logging any proxy error |
| Burning-smell gap handling is ours, not Meridian's | Meridian is fictional, so no policy owner exists to confirm (Q-046, deferred to this list) | A real policy owner, if Meridian were real |
| The emergency number is a **placeholder** | Meridian's real number is not issued | Replace before any real use |
| The issued dataset goes into a **public** repository without a licence | Innocent's accepted choice (Q-1, audit L-8) | A licence from the dataset's owner |
| This document describes the design, not the build | Nothing is measured on the built system yet | The build, then Stage 9 |

**Conflicts still open in the code design** ([code design](design/code-design.md) §10, reported, not edited). They are
documentation drift between design documents, and none changes behaviour: C-1 (the planner's output shape versus Jev's
interface), C-2 (a classifier failure: "the rules stand" per R-47, versus "fail toward raise" in the readiness report), C-4 (one
moving demo clock versus a chat-fixed date), C-6 (two gate paths missing from the observability record), C-9 (the 20 s versus
60 s deadline text in DO-1), C-10 (an event-bus description versus polling), C-12 (the spend day in DO-7), and C-13 (one
timeout sentence). The PRD's own §6.2 still says "server-rendered pages" while the UX track chose the React app in `apps/web`;
the PRD is not edited without Innocent (slice plan Q-5).

---

## 13. What we chose not to build

**Sources:** [PRD](prd/inno-aea-callcenter-prd.md) §7 (out of scope), §8 (cut order).

**Out of scope** (PRD §7):
- **Voice** (*Decided*, DEC-5).
- Real SMS or email: follow-ups and calls are recorded, never sent.
- Payments, autopay and auto-renew changes: the systems do not exist (D4). The agent explains the limit and creates a case.
- Multi-tenant staff accounts, and real Meridian staffing.
- Emergency dispatch.
- Commercial work, and duct-cleaning referrals beyond a limited answer.
- Fee waivers or discounts by the AI (*Decided*, DEC-2).
- Any edit to the issued dataset.
- Written but not built: the 10× scale path (section 11), pushing alerts to a channel (section 9), and a fully automatic feedback
  loop (section 9).

**Cut order if a checkpoint slips** (PRD §8; Must items are never cut). Cut from the first line down:
1. The owner panel, replaced by numbers in the README.
2. Cancel, then confirm.
3. The lookup-log snapshot panel, replaced by source links only.
4. The supervisor list, leaving the representative queue only.
5. Same-chat takeover. Cutting it reverses decision OD-2, so it needs Innocent's yes at the checkpoint.

Which of these were cut in the finished build is recorded in the README and the test results, `pending: Stage 9`.
