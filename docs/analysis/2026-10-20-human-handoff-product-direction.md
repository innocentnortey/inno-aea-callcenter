# Human handoff: product direction and ideation

**Date:** 2026-10-20, America/Chicago. **Status:** research synthesis and product ideas, **not a PRD**.
Nothing here is an approved requirement; open decisions stay open. **Builds on:** the
[service-team ideation note](2026-10-20-service-team-ideation.md) written earlier the same day. This
pass tests its three candidates against primary evidence and changes the ranking (§5). It doesn't
edit that note. **Sources:** S-100…S-105 (issued), the [brief audit](2026-10-20-brief-audit.md), and
outside research S-138…S-168 in the [source register](../source/source-register.md).

### How claims are labelled

Every claim carries one of four tags. They are not interchangeable.

| Tag | Means | Example |
|---|---|---|
| **[Brief]** | Required by the issued brief (portal page + PDF, S-100/S-101) | "hands off with enough context that a human can pick up without starting over" |
| **[Meridian]** | Observed in the issued Meridian dataset (S-102…S-105). Meridian is fictional; these are facts *about the dataset* | 0 of 420 calls is a live transfer |
| **[Research]** | Outside evidence about real agents or customers, with its source, sample and limits | A field experiment with 647 agents |
| **[Idea]** | Our product idea, to validate. Not evidence | "Show the same promise to the customer and the agent" |

No outside source describes Meridian's agents. Where research says "agents want X", that is a
statement about the surveyed population, not a Meridian preference.

---

## 1. Purpose

The business wants routine calls handled without adding staff **[Brief]**. Every call the AI can't
finish becomes work for a person. The brief already requires that this handoff is "graceful":
"hands off with enough context that a human can pick up without starting over" **[Brief]**.

This document asks the question the brief leaves open: **what does the person receiving that work
actually need, and what is the smallest thing we can build in 2–3 days that demonstrably gives it to
them?** It ranks three features, describes the handoff workflow end to end, and separates what
belongs in the challenge prototype from a later product.

**Why it matters for the grade, concretely.** The reviewer will "try to break it" and "watch the agent
escalate" **[Brief]**. Today an escalation in most prototypes ends in a chat bubble saying "a human
will help you". That proves nothing about the handoff. A handoff the reviewer can open, check and
close is the visible proof of "clean failure", one of the five things the reviewer is looking for
**[Brief]**.

---

## 2. Users and their jobs

| User | Job when a handoff arrives | What success feels like |
|---|---|---|
| **Caller** | Get the problem solved, or know exactly what happens next | Doesn't repeat the story; the promise made is kept |
| **Frontline representative** (Meridian's transcripts show *billing supervisor* and *service manager* roles taking callbacks **[Meridian]**) | Understand the case fast, check the facts, act, record what happened | Can act without re-asking the customer, and without trusting an unchecked summary |
| **Supervisor / service manager** | Make sure nothing urgent or overdue is sitting unowned; spot what the AI keeps getting wrong | Sees risk, not a wall of metrics |
| **Business owner / exec** | Know whether the AI reduces load *without* hurting customers | Containment that is real (resolved, not abandoned), plus where the handoffs come from |
| **Reviewer (grader)** | Probe edge cases and see the escalation behave | Can follow one escalation from the chat into the staff view and back out |

---

## 3. Evidence and its limits

### What Meridian's own data shows **[Meridian]**

Keyword counts over 420 transcripts. They are rough, and Stage 2 will verify them.

- **Every handoff is asynchronous.** About **54 of 420 calls (13%)** end with a callback, a
  supervisor follow-up or a safety instruction. **None is a live transfer.** All 8 "transfer" mentions
  are warranty transfers. The staffed reality in the data is *callback*, not *takeover*.
- **Callback promises are inconsistent with policy and with each other.** For the same supervisor
  escalation, human agents say:
  - "within one business day" (billing disputes, 16 calls);
  - "She'll call you back **today**" and "I've marked it urgent" (technician-conduct complaints, 16);
  - "within **two** business days" (refunds, 8).

  The knowledge base says supervisor escalation is a "callback within 1 business day", and "Do not
  promise a specific outcome" (`policies/escalation_and_safety.md`).
- **The handoff record the KB asks for isn't captured.** The KB says "Log the case with the
  customer's preferred callback window." **No agent asks for one (0 calls), and no agent gives a case
  or reference number (0 calls).** The customer leaves with a promise they can't trace.
- **Identity is checked by name and phone** in about 256 calls. That's weak on a public web app (audit
  D-6).
- **Safety calls follow the protocol, then become callbacks.** About 9 calls: "leave the house …
  call your gas utility or 911 from outside … call us back and we'll get an emergency tech
  dispatched. I'm putting a priority note on your account."
- **The scheduling database has no table for cases, callbacks or owners** (`SCHEMA.md`). Any handoff
  record is new state, outside the issued data.
- **The seeded test customers create handoffs.** INV-204411 doesn't reconcile with the fee rules
  (audit D-8). A dispute about it must go to a supervisor, so a reviewer is likely to produce exactly
  this handoff.

### Outside research: what it can and can't tell us **[Research]**

About 40 sources were checked by three research passes on 2026-10-20. The strongest are a few field
experiments and regulator reports. The rest are vendor surveys (useful, but they sell the fix), surveys
of **managers** describing agents, or evidence from other fields (hospital handoffs, emergency triage)
used by analogy.

| Strength | What we have |
|---|---|
| **Strong, direct** | Field experiments with real service agents: [Brynjolfsson, Li & Raymond, QJE 2025](https://arxiv.org/abs/2304.11771), 5,172 agents (S-138); [Wang et al. 2026, Alibaba](https://arxiv.org/abs/2605.14830), 647 agents and 680,676 chats (S-139); [Zhang & Narayandas 2025](https://aiinstitute.hbs.edu/?p=29426), 138 agents and 250k+ chats, read from the summary only (S-153). Callback behaviour: [Hathaway, Emadi & Deshpande 2021](https://pubsonline.informs.org/doi/10.1287/mnsc.2020.3621) (S-151). Regulators: [CFPB 2023](https://files.consumerfinance.gov/f/documents/cfpb_chatbot-issue-spotlight_2023-06.pdf) (S-149), [FCA 2024](https://www.fca.org.uk/publication/external-research/vulnerability-review-improving-outcomes-consumers-engaging-financial-services-firms.pdf) (S-150) |
| **Moderate** | One company's production study: [Airbnb incremental notes, EMNLP 2025](https://arxiv.org/abs/2510.06677) (S-140). Summary benchmarks: [TofuEval, NAACL 2024](https://aclanthology.org/2024.naacl-long.251) (S-158), [Ramprasad et al., ACL 2024](https://aclanthology.org/2024.acl-long.677) (S-159). Vendor benchmark on 2,500 real calls: [Observe.AI, EMNLP 2025](https://aclanthology.org/2025.emnlp-industry.91/) (S-141). Customer survey: [Gartner 2024, n=5,728](https://www.gartner.com/en/newsroom/press-releases/2024-07-09-gartner-survey-finds-64-percent-of-customers-would-prefer-that-companies-didnt-use-ai-for-customer-service) (S-154) |
| **Analogous** | Hospital handoffs: [I-PASS, NEJM 2014](https://doi.org/10.1056/NEJMsa1405556) (S-156); [AI-written emergency handoff notes, JAMA Netw Open 2024](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2827336) (S-157). Named ownership: [Song et al., Mgmt Sci 2015](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2014.2118) (S-164). Cherry-picking: [Ibanez et al. 2018](https://pubsonline.informs.org/doi/suppl/10.1287/mnsc.2017.2810) (S-165). Triage error: [Sax et al. 2023](https://pubmed.ncbi.nlm.nih.gov/36930151/) (S-169) |
| **Weak or vendor** | Agent surveys: [UJET 2026, 250 US agents](https://assets.ujet.cx/resource-center-pdfs/UJET-Agent_Survey_Report.pdf) (S-143); [Salesforce State of Service 7th ed.](https://www.salesforce.com/en-us/wp-content/uploads/sites/4/documents/PDF/state-of-service-7th-edition.pdf) (S-144); [Calabrio 2025, managers](https://www.silicon.co.uk/press-release/98-of-contact-centers-are-using-ai-and-61-are-experiencing-more-difficult-conversations-according-to-new-calabrio-research) (S-145); [CCW/Liveops 2025, leaders](https://liveops.com/wp-content/uploads/2026/05/WP_CCW-Liveops-Market-Study-Tech-vs-Humanity-Redefining-the-Agent-Role-compressed.pdf) (S-147); [n=152 agent survey, No Jitter 2025](https://www.nojitter.com/contact-centers/what-agents-really-think-about-ai-in-customer-service) (S-148) |

**Limitations that change how far to lean on this:**

- **No independent study measures AI-written handoff briefs in customer service**, or how often
  agents correct AI summaries. For the brief we lean on a hospital analogy and on dialogue-summary
  benchmarks.
- **Survey wording swings the answer.** In a vendor survey of 250 agents, 93% "feel the need to
  double-check" AI output (S-143). In a 152-agent survey, 20% "frequently double-check" it (S-148).
  Both can be true; neither is a measured behaviour.
- **Manager and agent views differ.** Several popular "agent" statistics are manager perceptions
  (Calabrio S-145, CCW S-147). The sharpest example: in a Five9 vendor survey, 96% of decision-makers
  say context is preserved at handoff, while 35% of consumers "often or always" repeat themselves
  ([CMSWire, 2026](https://www.cmswire.com/customer-experience/customers-the-ai-handoff-is-broken-contact-center-leaders-wont-hear-it/), S-146).
- **Untraceable figures were dropped.** Examples: the CFPB's often-quoted "78% needed a human" is a
  UJET vendor figure via Forbes. Several "customers repeat themselves X%" numbers have no primary
  source. The earlier ideation note's Zendesk "74% find repeating frustrating" (S-132) was not
  re-confirmed in this pass.
- **Most samples are chat, banking, e-commerce or telecoms, not home services.**

---

## 4. Frontline pain points

Ranked by strength of evidence, with what each implies.

| # | Pain | Evidence | Strength |
|---|---|---|---|
| P1 | **Escalated contacts are harder, and lateness makes them worse** | Alibaba RCT: chats escalated because the AI couldn't handle them took 19.1% longer. Escalations triggered by frustration took **40.8% longer**, had 6 percentage points more repeat contacts, and ratings 0.93 lower (1–5 scale). **Early, agent-initiated intervention** cut the damage: +9.5% time, −0.52 rating (S-139). | Strong (direct RCT; e-commerce, China) |
| P2 | **Customers arrive having to repeat themselves** | Five9 2026 (vendor, 3,000 consumers): 35% often or always repeat after AI→human ([release](https://finviz.com/news/402484/), S-155). UJET agents: 65% say customers complain about repeating "on most or every call" (S-143, vendor). The UK FCA's qualitative interviews describe "having to talk to multiple people and repeat things" (S-150). **[Meridian]** can't show this: each transcript is one call, and no customer says "I already told you" | Moderate (consistent direction; mostly vendor numbers) |
| P3 | **AI summaries drop or invent specifics** | 2,500 real calls × 20 models: summaries kept only **53.67% of named entities** and 67.46% of agent actions (S-141, vendor benchmark). In dialogue summaries, 40–50% had at least one factual inconsistency for most models, with errors clustering in secondary details (S-158). About 23% of GPT-4 dialogue summaries had inconsistencies; 38% of errors were plausible-but-unsupported inferences (S-159). In a hospital test, AI handoff notes were rated "marginally inferior" by physicians even though automatic scores favoured them (S-157) | Strong on the error rates (benchmarks); direct contact-center evidence is vendor |
| P4 | **Agents must verify AI output, and links can mislead** | Agents adopted only **38%** of AI suggestions (S-138). Showing citations raised trust "even when the citations were random", and trust fell when people actually checked (S-162). Explanations increase acceptance of wrong answers (S-161). Over-reliance drops only when checking is cheaper than redoing the work (S-161). Complacency rises under multitasking and isn't cured by training (S-160) | Strong (experiments; mostly lab or analogous) |
| P5 | **Promises and ownership slip** | Only **37%** of bank callers accepted a callback, though waiting for one is 3–6× less unpleasant than holding; distrust that their place is kept was a reason. Guaranteed windows cut hold time by up to 71% in simulation (S-151). Telling customers their queue position reduced abandonment (S-167). Named-owner queues cut emergency-department stays 17% vs a pooled queue (S-164, analogous). Penalising transfers makes agents hold cases they should pass on (S-166). **[Meridian]**: three different callback promises, no reference numbers, no callback window | Strong for callbacks (direct); ownership by analogy; the Meridian evidence is direct |
| P6 | **Tool switching and information hunting** | Representatives spend only 46% of their time with customers (S-144, vendor). 81% of agents use more than 4 tools at once (S-143, vendor). Leaders say 73% of agents face friction across systems (S-147, leader perception). Interrupted work carries "more stress, higher frustration" (S-163, analogous, older). **No independent measurement of what a unified desktop saves** | Weak to moderate (vendor and leader-reported) |
| P7 | **More information can become a burden** | 13 call-center representatives: AI-prefilled tickets needed "a lot of editing"; extra AI information "became a burden"; emotion alerts were ignored (S-142, qualitative, one site) | Weak (small) but specific |
| P8 | **Customers fear losing access to a person** | 64% would prefer companies not use AI for service; the top concern is that it makes it harder to reach a person (Gartner, n=5,728, S-154). Inviting access to a human raised loan uptake 24%, though few used it (S-152, field experiment). Trust in AI goes from 26% with no human option to 55% when one is reachable (S-155, vendor). The CFPB documents chatbot "doom loops" (S-149) | Strong (customer side) |

**What the pain points add up to.** Most of the pain sits at the moment of transfer. The customer
loses confidence, the person receiving has to rebuild context from an unreliable summary, and nobody
tracks the promise. Better *desk tools* (P6) have the weakest evidence.

---

## 5. Ranked features

### How the three candidates fared

| Candidate (as given) | Verdict | Why |
|---|---|---|
| 1. Intervention queue (reason, urgency, ownership, next action) | **Kept, re-ranked #2, sharpened** into a *commitment queue* | The ownership evidence is analogous; callback credibility (P5) and Meridian's broken promises are direct. What's missing from "queue" is the **promise**: what the customer was told, and by when |
| 2. Verifiable handoff brief | **Promoted to #1** | Most direct evidence (P2, P3, P4), the brief's own words ("without starting over"), and a seeded test case (INV-204411) that exercises it |
| 3. Unified agent workspace | **Replaced** by a narrow *resolution and correction record* | Tool-switching evidence is the weakest (P6). Meridian shows **zero live takeovers**. A broad live console in a 2–3 day build would imply staffing that doesn't exist. What survives is the part with real support: verify-in-place, record the true outcome, flag AI errors for review |

### #1. Verifiable handoff brief

**Agent pain addressed:** P2 (customer repeats themselves), P3 (summaries drop or invent specifics),
P4 (unverifiable AI output).

**Evidence:**
- **[Brief]** requires context "without starting over".
- **[Research]**: summaries omit about half of named entities (S-141). Errors cluster in secondary
  details and plausible inferences (S-158, S-159). A structured handoff format cut preventable adverse
  events 30% with no added handoff time (I-PASS, S-156, analogous). AI handoff notes need human
  review (S-157). Citations raise trust even when random (S-162), so links must go to the *exact
  supporting line*.
- **[Meridian]**: the INV-204411 dispute needs the invoice lines, the fee rule and the fact that
  nothing was promised in one place.

**Smallest useful experience [Idea]:** one panel, generated at the moment of escalation, with fixed
fields rather than prose:

1. **Why the AI stopped:** the escalation reason, from a fixed list (safety, policy requires a person,
   out of scope, low confidence, customer asked for a person), plus the rule that fired.
2. **What the customer wants:** in the customer's own words, quoted from the conversation.
3. **Verified facts:** each fact linked to its record or KB passage (invoice line, appointment, policy
   paragraph). The link opens the exact line.
4. **Customer claims (unverified):** kept separate, e.g. "the tech quoted me $129".
5. **What the AI already did:** answers given, with their sources; tools called; the booking state
   (*confirmed* with slot ID, *attempted and failed* with reason, or *none*).
6. **What the customer was told will happen next:** the exact promise (see #2).
7. **The open question:** the one thing a person needs to decide.
8. **Full conversation:** one click away, never replaced by the summary.

Only fields 2 and 7 need model wording. Fields 1, 3, 5 and 6 can be **assembled from structured
state** the agent already holds (tool calls, rule hits, booking result). That's the cheapest defence
against P3.

**Information needed:** conversation log; escalation reason and rule; tool-call log; booking or
invoice records touched; KB passage IDs used; the promise text.

**What could go wrong:**
- A wrong or over-confident summary. Mitigation: facts come from records, claims stay labelled as
  claims, and the conversation is always available.
- Links that look like verification but don't support the line (S-162).
- Showing account data to a role that shouldn't see it (audit G-2, G-9).
- An over-long brief that becomes a burden (S-142).

**How we'd know it helped:**
- **Faithfulness:** share of brief statements supported by the conversation or records, labelled by
  a human on a sample.
- **Key-entity coverage:** invoice ID, appointment, address and amount present when relevant
  (checklist, as in S-141).
- **Re-ask rate:** in a walkthrough, how often the receiving person has to ask the customer for
  something already in the conversation.
- **Time to first action** from opening the case.

### #2. Commitment queue (intervention queue + the promise)

**Agent pain addressed:** P5 (promises and ownership slip), P1 (urgent cases waiting), P8 (customer
confidence).

**Evidence:**
- **[Meridian]**: three inconsistent callback promises for the same escalation type; zero reference
  numbers; zero callback windows, though the KB asks for them.
- **[Research]**: callbacks fail on credibility, not convenience (37% acceptance, S-151). Showing
  progress reduces abandonment (S-167); accurate delay information shifts expectations (S-168).
  Named ownership beats a pool, and free picking hurts (S-164, S-165, analogous). Early intervention
  limits frustration damage (S-139). Triage scales still mis-assign about a third of urgent cases
  (S-169, analogous), so urgency comes from **rules**, not model judgement, and stays re-classifiable
  by a person.
- **[Brief]**: "tells the caller what is happening".

**Smallest useful experience [Idea]:** each escalation creates one **case**. The *same* commitment
record is shown to the customer and to the staff member:

- **To the customer:**
  - a reference number;
  - what happens next, in policy wording ("A billing supervisor will call you back within one business
    day");
  - the callback window they chose;
  - what to do if it's urgent.
- **In the queue:**
  - reason;
  - urgency, from rules (safety → immediate; dispute or refund → supervisor, 1 business day; out of
    scope → redirect);
  - due time, computed from policy and the fixed clock (audit C-9);
  - owner (unassigned / named);
  - status: new → claimed → contacted → resolved / closed-unresolved;
  - next action.

Sorted by due time, not by age or preference. Overdue items are visually distinct.

**Information needed:** escalation reason; the policy table mapping reason → owner role → promise →
due rule; the configured "today"; staff list; case events.

**What could go wrong:**
- **Promising what nobody staffs.** Mitigation: promises are generated only from the policy table,
  never by the model.
- Mis-assigned urgency. Mitigation: rules plus a human override with a recorded reason.
- Cherry-picking, if staff can freely pick cases.
- A queue that becomes a second, invisible backlog.
- Penalising escalation in metrics, which pushes the AI or staff to hold cases (S-166).

**How we'd know it helped:**
- **Promise consistency:** 100% of customer promises match the policy table. Deterministic and
  testable.
- **Commitments kept:** cases resolved or contacted before due ÷ cases due.
- **Overdue count and age**, and **unowned time**.
- **Repeat contact:** the same customer re-contacts about the same case before it closes.
- In the prototype: every escalation in the test set produces a case with a valid promise.

### #3. Resolution and correction record (replaces the broad workspace)

**Agent pain addressed:** P4 (agents silently fix AI mistakes), P6 (hunting for the current record),
and the business's need for honest outcomes.

**Evidence:**
- **[Brief]**: "Logged conversations, flagged failures, or human corrections should feed back into
  improving the system". Monitoring must show escalations and failures. Containment must be real.
- **[Research]**: Airbnb designed agent edits as a quality signal (S-140). Leaders and customers see
  handoff quality very differently (S-146), so recorded outcomes beat impressions. Microsoft's own bot
  dashboard counts abandoned conversations as "deflected" (S-137), the trap this record avoids.
  Tool-switching evidence (P6) is weak, so this stays **narrow**.
- **[Meridian]**: no case store exists today.

**Smallest useful experience [Idea]:** inside the case, beside the brief:

- **Verify in place:** the *current* state of the records the case touches, read live from the
  working DB (the appointment, the invoice, the governing KB passage). Not a general search console.
- **Record the outcome**, from a fixed list:
  - resolved on callback;
  - booking changed (via the same booking tool the AI uses, with the same rules);
  - customer unreachable;
  - escalated further;
  - closed, no action needed.
- **Flag the AI:** "AI answer was wrong / brief was wrong / escalation was unnecessary / KB document is
  wrong", with a short note. Flags go to a **review list**. They never change the KB, prompts or eval
  set automatically (audit G-6, C-13).

**Information needed:** case and brief; read access to the working DB and KB; the booking tool;
outcome and flag enums; an author identity for each action.

**What could go wrong:**
- It grows into a full staff platform. Keep it to one case view.
- Staff bypassing the booking rules. Mitigation: they use the same tool and checks as the AI.
- Flags that nobody reviews.
- Adversarial reviewer input entering a training path.

**How we'd know it helped:**
- **Outcome coverage:** every closed case has an outcome.
- **Containment computed from outcomes**, with resolved, escalated, abandoned and failed reported
  separately.
- **Flag rate by type,** and the time a flag waits for review.
- **Correction yield:** flags that led to a KB fix or a new eval case.

### Ranking rationale in one line each

1. **Brief.** It acts on the moment of transfer, where the strongest evidence of pain sits. The issued
   brief names it, and a seeded case tests it.
2. **Commitment queue.** Meridian's data shows the promise and ownership gap directly, and the
   callback research says credibility is the lever.
3. **Resolution and correction record.** Its direct agent-pain evidence is thinnest, but it is required
   in spirit by the brief's feedback loop and honest-containment criteria, and it is cheap once #1 and
   #2 exist.

---

## 6. A concrete handoff story

Omar Patel (seeded customer MHC-10002) opens the chat. The dataset's "today" is 2026-10-16.

1. **AI turn.** Omar asks why invoice INV-204411 is $478. The AI verifies identity (audit DEC-3,
   open). It explains each line from the invoice record: diagnostic $89, contactor $245, after-hours
   dispatch $144. It cites the current fee schedule.
2. **Trigger.** Omar says: "That's not what I was told. Take the after-hours fee off." Two rules fire:
   a fee dispute requires a supervisor (KB `escalation_and_safety.md`), and the invoice's $144 doesn't
   match the $149 fee rule (audit D-8). The AI doesn't adjudicate, doesn't promise a refund, and
   doesn't waive (audit E-4).
3. **Commitment shown to Omar:**
   > I can't change charges, but a billing supervisor can review this. They'll call you back within
   > one business day, by end of day Monday Oct 19. What time window works best for a call? …
   > Your reference is **MHC-C-0007**. If anything changes, mention that reference.

   No claim that anyone is available *now*.
4. **Case created.**
   - **Reason:** billing dispute.
   - **Urgency:** supervisor, 1 business day.
   - **Due:** 2026-10-19 17:00.
   - **Owner:** unassigned.
   - **Brief:**
     - *Customer wants:* "Take the after-hours fee off."
     - *Verified facts:* invoice lines (link to record); fee schedule says $149 after-hours (link to
       KB line); the invoice shows $144.
     - *Customer claims:* "That's not what I was told" (unverified).
     - *AI did:* explained lines; promised nothing.
     - *Open question:* is the $144 line correct, and is any adjustment warranted?
5. **Supervisor review.** The supervisor claims the case. The verify-in-place panel shows the live
   invoice. They notice the diagnostic fee was billed alongside an approved repair (the FAQ says it's
   credited). That's a judgement for them, not the AI.
6. **Callback (asynchronous path).** In the prototype, the call itself is out of scope. The supervisor
   records *contacted at 10:40, outcome: adjustment approved, $89 credited* and flags *"KB fee rule
   and invoice disagree"* for review.
7. **Closure.** Omar's case shows *Resolved*. The manager view counts it as **escalated → resolved by
   staff**, not as AI containment.

**Live staffed takeover is a different path, not shown above.** It exists only if someone is on shift.
The case would show *"Available now: Dana (billing)"*. On claim, the AI stops replying, the customer
sees "Dana from billing has joined", and the same thread continues. When nobody is staffed, the
customer is never offered "connecting you now".

One research caution for the live path: in a field experiment, very fast human replies after a
handoff made customers think they were still talking to a bot, which carried the bot's failure over
to the human (S-153). A visible "a person has joined" marker matters more than speed.

---

## 7. The workflow, escalation to closure

```
AI conversation
  │
  ├─ Safety trigger (gas, CO, sparks) ──► safety instruction FIRST, in the same turn ──► case (urgency: immediate)
  │
  └─ Other escalation trigger ──► AI tells customer the policy promise + reference, asks callback window
                                     │
                                     ▼
                              CASE created: reason · urgency (rules) · due · owner · brief · promise
                                     │
             ┌───────────────────────┴───────────────────────┐
     Staffed now? (explicit setting)                   Not staffed
             │                                                │
   LIVE TAKEOVER [later product]                     ASYNC CALLBACK [prototype]
   staff claims → AI paused → "a person has joined"  staff claims → reviews brief → verifies in place
   → same thread                                     → contacts customer by the promised time
             │                                                │
             └───────────────► OUTCOME recorded ◄─────────────┘
                     (resolved / booking changed / unreachable / escalated / no action)
                                     │
                             FLAGS → review list (human-gated)
                                     │
                         CLOSED · re-opens if the customer returns with the reference
```

**Rules for both paths [Idea]:**
- The staffing state is an explicit setting, shown in the customer UI and the staff UI. The default
  in the demo is **not staffed**.
- The AI never tells a customer a person is available unless the staffing state says so.
- A customer's explicit request for a person always creates a case (audit E-1). In the async path,
  the customer gets the honest promise, not a fake transfer.

---

## 8. What each audience needs to see

| Frontline representative | Supervisor / manager | Business owner |
|---|---|---|
| My open cases, sorted by due time | **At risk:** overdue or due-soon commitments, unowned cases | Containment from outcomes: resolved by AI / escalated / abandoned / failed, each with its denominator |
| The brief, with verifiable links | Escalations by reason, last 7 days (where the AI hands off most) | Escalation share, and the share of escalations kept on time |
| The live record (appointment, invoice, policy line) | Flags awaiting review, by type | Top handoff reasons as a signal of knowledge gaps or scope |
| Outcome and flag buttons | Re-assign, override urgency (with a reason) | Latency, error rate, spend (the brief's monitoring list) |

**Small management view [Idea]:** only two panels earn their place in the prototype:

1. **"Needs attention"**: overdue, due-soon or unowned cases. It drives an action: assign or chase.
2. **"Why the AI hands off"**: escalation reasons plus open flags. It drives a decision: fix a KB
   document or widen scope.

Charts beyond that are monitoring (the brief's own requirement) and belong in the monitoring page,
not the staff view.

---

## 9. Challenge prototype vs later product

| In the 2–3 day prototype (candidates; the PRD decides) | Later product |
|---|---|
| Case created on every escalation, with reference and policy promise | Live takeover with AI pause, presence and staffing schedules |
| Handoff brief assembled from structured state + quoted customer words | Incremental notes during the conversation (S-140) |
| One queue list: reason, urgency (rules), due, owner, status | Skills-based routing, auto-assignment, workload balancing |
| One case view: brief, verify-in-place, outcome, flag | Full agent desktop, cross-channel history, CRM integration |
| Staffing state explicit; demo default "not staffed"; callbacks recorded, not placed | Telephony callbacks, SMS reminders (consent rules, audit L-9) |
| Two-panel manager view | QA sampling, coaching, agent performance analytics |
| Flags into a review list | A reviewed-correction pipeline into KB fixes and eval cases |

**Explicitly not requirements:** LangGraph, a message broker, a hosted vector-database service, live
voice, or a staff platform. None is needed to demonstrate these three features. A table or two in the
app's own working store is enough. Any of them may come back in design only if a measured need
appears.

**Constraints carried from the audit:**
- The safety instruction precedes any queueing (K-12, E-3).
- Promises come from policy text (C-7, E-5).
- The issued DB is never written; the case store sits beside the working copy (G-7).
- Briefs and logs keep PII to the role that needs it (G-2, G-9).
- No fee waivers by the AI (E-4).
- The fixed "today" (C-9).

---

## 10. Measures of agent effort and handoff quality

| Measure | What it tells us | Prototype-measurable? |
|---|---|---|
| Brief faithfulness: share of statements supported | Whether the brief can be trusted | Yes, a human-labelled sample from test-set escalations |
| Key-entity coverage (invoice, appointment, amount, address, promise) | Omission, the commonest summary failure (S-141) | Yes, checklist per case |
| Promise consistency with policy | Whether customers are told the truth | Yes, deterministic, should be 100% |
| Escalation reason accuracy (staff re-classification rate) | Whether routing makes sense | Partly: reviewer walkthrough |
| Re-ask rate (staff asks for info already given) | The "repeat yourself" pain (P2) | Only in a scripted walkthrough |
| Time to first action from case open | Agent effort | Only in a scripted walkthrough |
| Commitments kept on time; overdue count; unowned time | Ownership (P5) | Only with simulated time; real in a pilot |
| Outcome coverage; containment from outcomes | Honest business metric | Yes |
| Flag rate by type; flag review time; correction yield | Whether the feedback loop works | Partly |
| Repeat contact on an open case | Whether the handoff actually resolved | Pilot only |

**The honest limit:** without real staff, the agent-effort measures can only be approximated with
scripted walkthroughs. The demo should say so, not invent handle-time savings.

---

## 11. Risks and open questions

**Risks:**
- **Automation bias in the brief.** A clean-looking brief invites trust (S-160, S-161, S-162).
  Separating facts from claims and linking to the exact line is necessary but not proven sufficient.
- **Implying staffing.** Any "connecting you now" in an unstaffed demo is a false promise (audit E-5)
  and a reviewer trap.
- **Scope creep.** These three features plus the core agent must fit 2–3 days. If time runs short, cut
  #3 to "outcome + flag" before cutting #1 or #2.
- **Late escalation.** If the AI escalates only after repeated failures, the case arrives hot (S-139).
  Escalation triggers should fire early on the policy rules and on explicit requests.
- **Evidence transfer.** Most of the research is chat, banking, e-commerce or hospital settings. The
  HVAC and home-services context is untested.
- **Measuring escalation as failure.** If dashboards treat every handoff as a loss, the system will be
  tuned to hold cases it should pass on (S-166).

**Open questions (decisions stay open):**
1. **Which promise wins** when policy and practice disagree: the KB's "1 business day" for all
   supervisor cases, or the transcripts' "today" for conduct complaints and "two business days" for
   refunds? This needs a recorded decision (the KB is the current written policy).
2. **Does the challenge prototype include a staff view at all,** or only the case record and brief
   surfaced in monitoring? The brief requires context-rich escalation and monitoring, not a staff UI.
3. **Where the case store lives:** new tables in the working copy of the scheduling DB, or a separate
   store. This is a design-stage choice.
4. **Identity before a case shows account data** (audit DEC-3).
5. **Whether to demonstrate live takeover at all**, and if so, how it is labelled as simulated.
6. **Which escalation reasons get their own lane** depends on the Stage 2 driver analysis. The
   reasons listed here come from the KB escalation policy and keyword counts, not from a full driver
   analysis.
7. **Real-staff validation:** no outside source describes Meridian's staff. One conversation with a
   working contact-center agent would test these rankings better than another survey.
