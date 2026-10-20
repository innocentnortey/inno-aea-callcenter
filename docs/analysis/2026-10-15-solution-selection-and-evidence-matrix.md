# Solution Selection and Evidence Matrix

**Date:** 2026-10-15 · **Revised:** 2026-10-15, reconciliation pass (see the [revision log](#revision-log)).
**Status:** research shortlist for Innocent's selection. **Nothing here is selected, built, demonstrated or validated.** This file is not a PRD and does not set final scope. Research is not signed off.

**What this file owns:** the mandatory-baseline list (`M-NN`), the discretionary candidate inventory (`SOL-NNN`), the parked ideas (`P-NN`), the ranking rubric and scores, the shortlist evidence cards, and the selection and audit-trail record. It cites facts; it does not own them:
- company facts: [company profiles](company-research/);
- sources, URLs and review dates: [source register](../source/source-register.md) (`S-N`);
- review excerpts, counts and patient status: [review evidence](2026-10-15-google-review-sentiment.md);
- reference journey and guidance: [patient journeys and baseline](2026-10-15-patient-journeys-and-onboarding-baseline.md);
- review interpretation: [review pitfalls](2026-10-15-review-pitfalls-and-solution-opportunities.md);
- company comparison and first-pass recommendations: [research report](2026-10-15-onboarding-research-report.md);
- unknowns: [research questions](research-questions.md) (`RQ-N`).

**Interactive view:** [`docs/artifacts/2026-10-15-solution-selection-dashboard.html`](../artifacts/2026-10-15-solution-selection-dashboard.html) — a local, self-contained dashboard of this file's candidates, evidence chains, journeys, comparison and a draft-selection tool. It reads nothing at runtime. Selections made there are browser-local drafts; **this file's §6 and ledger remain the record.** If this file changes, regenerate or re-check the dashboard.

The superseded first-pass configuration checklist is not used as authority. Citations point to sections, not line numbers, so they survive edits to the owner files.

**Three meanings of "baseline", kept apart in every card:**
1. **Reference baseline:** what professional guidance says a good process should support (S-108…S-118). It does **not** show that a company falls short of it.
2. **Company current state:** what a company publishes, or what a reviewer reports, at a named location on a stated date. A review does **not** establish a technical cause, a frequency or a network-wide pattern. Several cited reviews concern established patients ([review report §7](2026-10-15-google-review-sentiment.md#7-patient-status-and-journey-stage-of-the-cited-complaints)).
3. **Measured baseline:** real completion, time, error, workload or revenue figures. **Unknown for every company** (RQ-2, RQ-3, RQ-38). Synthetic results are never company data, and a synthetic demonstration cannot establish a real company's revenue improvement.

---

## 1. Decision overview

### The opportunity, in plain English
Across the five platforms, reviewers usually praise the clinical work. The problems they report sit mostly in the administrative stretch around a visit: getting a call back, knowing what is pending, not repeating details, and arriving at the right time with the right instructions. The research turns that into four questions a patient needs answered ([review pitfalls, "The strongest product opportunity"](2026-10-15-review-pitfalls-and-solution-opportunities.md#the-strongest-product-opportunity-to-investigate)):
1. Was my information received?
2. What is missing?
3. Who handles the next action?
4. What happens next?

**The reviews align most strongly with five problems:**
- unreturned calls and unclear ownership;
- uncertainty about status and next steps;
- repeated administrative entry;
- scheduling changes and missing instructions;
- automation without a working recovery or human route.

**Behaviours worth preserving:** reviewers praise listening, explanations, reminders, pre-visit check-in calls, insurance and payment help, and personal follow-through. Candidates should support the people who do this, not assume they can be removed.

**Existing tools are not failures.** Every platform publishes digital tools, and they do different jobs: contact capture, scheduling, administrative onboarding or ongoing coordination ([baseline, "What a published tool can and cannot establish"](2026-10-15-patient-journeys-and-onboarding-baseline.md#what-a-published-tool-can-and-cannot-establish)). AdaCare's scheduler, for example, shows New Patient Visit slots before any personal details (S-83, re-read 2026-10-15). Each candidate below names the job it addresses and is framed as a complement.

**The business hypothesis:** clearer steps, less repeated entry and usable staff handoffs could reduce administrative effort and help more patients reach a first visit. Completion, attendance, retention and revenue are **outcomes to measure, not established benefits**. The brief's 50% → 70% completion figure is illustrative (S-1).

**What an intake assistant cannot fix on its own:** staffing, payer decisions, treatment outcomes, appointment capacity or equipment repairs.

### Numbers for this decision
| Item | Count | Rule |
|---|---|---|
| Mandatory baseline (from the issued brief) | 15 requirements (M-01…M-15) | Always in scope; your selection cannot remove them |
| Eligible discretionary candidates (the denominator) | **19** (SOL-001…SOL-019) | Overlapping ideas merged; nothing split to reach a round number |
| Shortlist shown (≈40%) | **8** | 40% × 19 = 7.6 → rounded to the nearest whole number = 8 |
| Selections for you (≈20%) | **4** | 20% × 19 = 3.8 → rounded to the nearest whole number = 4 |
| Parked (unsupported or out of scope) | 11 (P-01…P-11) | Not ranked and not in the denominator |

### Mandatory baseline (not selectable)
Source: the issued brief (S-1, [`docs/source/aea-proj1-onboarding-assistant.md`](../source/aea-proj1-onboarding-assistant.md)). Risks and ambiguities in these requirements are owned by the [brief audit](2026-10-14-brief-audit.md) (T1–T23, C1–C11).

| ID | Requirement | Brief section |
|---|---|---|
| M-01 | Guided LLM chat that fills a structured record; handles every listed intent (including express-distress, whose escalation route is RQ-22); graceful fallback | Core #1; AI Metrics |
| M-02 | ID/document OCR for name, DOB and address (≥90% on a 30-item synthetic golden set); confirmation before saving; partial extraction; manual fallback | Core #2; Edge cases; AI Metrics |
| M-03 | Book from available slots; confirmation; double-booking rejected; persists across sessions | Core #3 |
| M-04 | Supportive content shown at defined triggers, and never without one | Core #4 |
| M-05 | Logged consent before upload or processing; revocation; verifiable deletion | Security; Edge cases |
| M-06 | Data minimisation; image discarded after confirmation; TLS and encryption at rest; private storage; retention policy | Security |
| M-07 | Per-user access; role-scoped, audit-logged staff access | Security |
| M-08 | Server-side upload validation (type, size, corrupt) | Edge cases |
| M-09 | No PII in logs, traces or analytics | Edge cases |
| M-10 | LLM, OCR and dependency failure fallback; no hallucinated commitment; no unhandled 500s | Edge cases; Code quality |
| M-11 | p95 targets under the stated k6 load; uptime evidence | Performance |
| M-12 | Committed eval harness (OCR golden set and intent set) with scorecard | AI Metrics |
| M-13 | ≥80% tests on core logic, CI with linters, health check, migrations and seed, `.env.example`, accessibility baseline | Code quality |
| M-14 | Repository with README and `AI_USAGE.md`, grader quick-start, deployed URL, documentation, demo video | Submission; AI disclosure |
| M-15 | Regulatory note (HIPAA for a healthcare domain); disclosure of the model and data boundary | Security |

**Project rules also always apply:** synthetic data only, and the administrative-only boundary (`.claude/rules/source-authority.md` rules 7–8). There is no diagnosis, urgency triage, treatment recommendation, insurance approval, coverage promise or referral bypass.

---

## 2. Complete candidate inventory

**Type:**
- **Complete:** a patient or staff behaviour that addresses a problem on its own.
- **Supporting:** makes another candidate or a mandatory feature work better, but solves no problem alone.

**Job** (from the journey baseline): **Contact** = contact capture · **Sched** = scheduling · **Admin** = administrative onboarding · **Coord** = ongoing coordination. Clinical assessment is never a job for the product.

**Evidence strength (E), 1–5:**
- **5:** direct attributed reports at two or more platforms, plus published workflow.
- **4:** direct reports at one platform, or a published requirement at three or more platforms, plus guidance.
- **3:** published workflow or guidance, with indirect or single reports.
- **2:** derived from the brief or our analysis only.
- **1:** speculative.

| ID · name | Type · job | Specific problem addressed | Company / practice (examples) | E | Expected patient / business value | Effort · dependency | Rank · status |
|---|---|---|---|---|---|---|---|
| **SOL-001** Patient readiness status | Complete · Admin/Coord | The patient can't see what was received, what's missing, who handles it or what's next | CPS Louisville South and Elizabethtown; NUM Nashville (adjacent) | 5 | Less uncertainty; fewer status calls; fewer silent drop-offs (hypothesis) | M · **needs SOL-002** | 1 · **Shortlist** |
| **SOL-007** Confirmation and visit-logistics package | Complete · Sched | Confirmations missing directions or preparation; arriving at the wrong time or unprepared | MVC Forest Hills; CPS Louisville South | 4 | Arrive at the right place, time and prepared; better attendance (hypothesis) | L · builds on M-03 | 2 · **Shortlist** |
| **SOL-002** Owned staff handoff queue | Complete · Contact/Coord | Requests and callbacks with no visible owner; automation without a human route | CPS Louisville South and Elizabethtown; FOH Naples; NUM Nashville | 5 | Fewer lost requests; less duplicated calling (hypothesis) | M · owner unknown (RQ-4, RQ-27) | 3 · **Shortlist** |
| **SOL-004** Insurance capture with OCR and confirmation | Complete · Admin | Typing insurer, member ID, policyholder and secondary insurance; data unavailable before scheduling | All five platforms (published requirements) | 4 | Less typing; earlier verification (hypothesis) | M · builds on M-02, M-05 | 4 · **Shortlist** |
| **SOL-003** Collect-once record and staff summary | Complete · Admin | Administrative answers re-asked; submitted updates not visible at check-in | CPS Louisville South and Elizabethtown; FOH Naples | 4 | Less retyping; shorter check-in (hypothesis) | M · staff must see it (SOL-018 or integration) | 5 · **Shortlist** |
| **SOL-005** Staged, resumable administrative packet | Complete · Admin | Long packets presented at once (14-page FOH, 4-page AdaCare paper); no resume or assisted route | FOH; AdaCare; MVC (4-field benchmark) | 3 | Lower starting effort; the brief's completion hypothesis | M · company "required before booking" rules (RQ-6, RQ-45) | 6 · **Shortlist** |
| **SOL-011** Published cost and policy transparency | Complete · Admin | Price, fee and self-pay rules found only on FAQ pages; estimate requests unclear | CPS (company-wide); AdaCare; MVC | 4 | Fewer cost surprises; informed booking (hypothesis) | L · content refresh; estimates routed to SOL-002 | 7 · **Shortlist** |
| **SOL-006** Prerequisite-aware next step | Complete · Sched | Clinical booking while a referral, authorisation, records or physician visit is still pending | CPS Louisville South; FOH Naples; NUM Nashville; AdaCare as the no-prerequisite contrast | 4 | A real next step without a referral bypass; fewer wasted visits (hypothesis) | M–H · builds on M-03; needs SOL-002; rules unknown (RQ-7, RQ-39) | 8 · **Shortlist** |
| SOL-014 Company-sourced help library | Supporting (feeds M-04) · all | Help content invented, or not specific to the company | All five (published FAQ and preparation text) | 3 | Accurate help at friction points | L · reuse permission (RQ-10) | 9 · Eligible |
| SOL-010 Distinct notices and communication choices | Supporting (extends M-05) · Admin | One blanket checkbox for privacy, upload, SMS/email and records release | FOH packet; AdaCare packet; MVC SMS terms | 3 | Clear choices; handling of a declined consent | L · RQ-46 | 10 · Eligible |
| SOL-008 Pre-visit messaging: reminders, missing-item nudges, change notices | Complete · Coord | Changed or cancelled times not communicated; preserve praised reminder calls | MVC Forest Hills; AdaCare (positive) | 4 | Better attendance; fewer wrong-time arrivals (hypothesis) | M · needs SOL-007, consent, a message channel | 11 · Eligible |
| SOL-018 Portable handoff export | Supporting · Admin | Staff can't use a summary their systems can't receive | All (no integration access) | 2 | Usable without integration | L · RQ-25 | 12 · Eligible |
| SOL-009 Records-release and outside-records task | Complete · Admin | Outside records and transfer documents not tracked; patient becomes the messenger | FOH Naples; CPS (records request on the form) | 4 | Records arrive before the visit (hypothesis) | M · staff ownership (SOL-002) | 13 · Eligible |
| SOL-012 Language and access preference capture | Supporting · Admin | Language and access needs not visible to staff | MVC Forest Hills; FOH packet | 3 | Staff can arrange support | L | 14 · Eligible |
| SOL-015 Multi-company configuration packs | Supporting (demo strategy) · all | Proving one core serves several platforms | CPS plus AdaCare/ADC | 3 | A portfolio reuse story | M · doubles configuration and test work | 15 · Eligible |
| SOL-016 Representative or caregiver completion | Complete · Admin | A family member, guardian or clinician completes intake | NUM; FOH packet; AdaCare form and scheduler ("Booking for … Someone Else", S-83) | 3 | Correct authority recorded | M · RQ-16 | 16 · Eligible |
| SOL-019 Onboarding funnel analytics | Supporting (brief stretch #7) · all | No measurement of drop-off, step time or OCR corrections | All | 2 | Makes improvement measurable later | M | 17 · Eligible |
| SOL-013 Spanish-language assistant | Complete (brief stretch #5) · all | Spanish speakers served in English only | MVC (Spanish site); FOH (Spanish documents) | 3 | Access for Spanish speakers | H · translation and content approval; needs SOL-012 | 18 · Eligible |
| SOL-017 Attendance-barrier capture routed to coordination | Complete · Admin/Coord | Transport, cost or caregiving barriers surface late | FOH (care coordination, S-97) | 3 | Earlier help with barriers (hypothesis) | M · RQ-44 boundary | 19 · Eligible |

### Dependencies to check before choosing
- **SOL-001 without SOL-002 is incomplete.** A status page needs someone who owns and updates each step; otherwise it shows invented progress.
- **SOL-006 needs SOL-002.** Pending prerequisites must land with an owner. It is strongest with SOL-001.
- **SOL-003 delivers most of its value through a staff view.** SOL-002 or SOL-018 provides one.
- **SOL-004 builds on M-02 and M-05.** It adds a card golden set and more sensitive fields.
- **SOL-007 and SOL-006 both extend M-03.** SOL-008 needs SOL-007 plus a consented channel.
- **SOL-011 needs somewhere to send an estimate request.** That is SOL-002.
- **SOL-013 needs SOL-012** and approved translations.

### Parked (not ranked)
| ID | Idea | Why parked |
|---|---|---|
| P-01 | Pass clinical patient-reported context (other conditions, prior treatment, sleep, pregnancy, nutrition) to clinicians | Administrative-only rule; **RQ-44 unresolved** — the configuration annex excludes medical history while report §7 and the ⚑ scenarios in the demo blueprint collect it. Your decision on RQ-44 could un-park it |
| P-02 | Sentiment-adaptive tone (brief stretch #6) | No research evidence of need; the brief audit flags emotion-inference risk (RQ-29, T5/T6/T21). You may override, but it is unsupported here |
| P-03 | Numotion equipment order and repair status tracker | Separate product; Numotion's public app guide already documents order status, notifications, appointments, service requests and chat (S-106 — documented capability, not tested). The reviews concern established customers in ongoing service, not first-visit onboarding |
| P-04 | Live integration with athenahealth, Jarvis, HubSpot, OncoEMR or myNumotion | No access; visible tools are not integration evidence (RQ-18, RQ-25) |
| P-05 | Booking into real company calendars, or self-booking clinical visits where the company has not published it | Synthetic slots only (M-03 is met with synthetic slots). AdaCare **does** publish self-scheduling for a New Patient Visit (S-83); CPS, FOH and MVC publish staff-scheduled entry. Real booking permissions remain RQ-8 and RQ-26 |
| P-06 | Provider matching or preferred-clinician choice | No problem evidence; matching rules unpublished |
| P-07 | Existing-patient or duplicate-record flag | Only the CPS "seen before?" field (S-75) and AdaCare's New/Existing choice (S-83); no problem evidence |
| P-08 | Fixing in-office waits or overbooking | Intake cannot solve staffing or schedule capacity ([review pitfalls, "What the reviews support less directly"](2026-10-15-review-pitfalls-and-solution-opportunities.md#what-the-reviews-support-less-directly)) |
| P-09 | Urgency triage, eligibility or coverage decisions, referral bypass, treatment suggestions, AI price estimates | Prohibited by the administrative-only rule and the brief's "no hallucinated commitment" |
| P-10 | Replacing an existing chatbot, virtual agent, scheduler or portal | An existing tool is not a failure (source-authority rule 5) |
| P-11 | Ongoing-care coordination (established-patient rescheduling, prescriptions, results follow-up) | Separate from first-time onboarding; many cited reviews concern established patients ([review report §7](2026-10-15-google-review-sentiment.md#7-patient-status-and-journey-stage-of-the-cited-complaints)). Whether the scope extends past the first visit is RQ-45 |

---

## 3. Ranked top-40% shortlist

### Rubric
Each criterion is scored 1–5. Score = Σ(weight × score ÷ 5); maximum 100. **This is a research judgement, not measured ROI.**

| Criterion | Weight | What 5 means |
|---|---|---|
| E · Evidence strength and directness | 20 | Direct reports at ≥2 platforms plus published workflow |
| P · Importance of the problem | 20 | Blocks or delays getting to a first visit, or damages trust |
| F · Fit with the brief and administrative scope | 20 | Directly serves a brief requirement or stated problem; no clinical judgement |
| D · Demonstrable within the 3-day timebox with synthetic data | 15 | A clear pass/fail demo, little extra infrastructure |
| R · Reuse across portfolio companies | 15 | Applies to all five platforms |
| I · Low effort and low integration/operational dependency | 10 | Small build; works without company systems or new staff processes |

### Scores (all 19)
| Rank | ID | E | P | F | D | R | I | Score |
|---|---|---|---|---|---|---|---|---|
| 1 | SOL-001 | 5 | 5 | 5 | 4 | 5 | 3 | **93** |
| 2 | SOL-007 | 4 | 4 | 5 | 5 | 5 | 4 | **90** |
| 3 | SOL-002 | 5 | 5 | 4 | 4 | 5 | 3 | **89** |
| 4 | SOL-004 | 4 | 4 | 5 | 4 | 5 | 4 | **87** |
| 5 | SOL-003 | 4 | 4 | 5 | 4 | 5 | 3 | **85** |
| 6 | SOL-005 | 3 | 4 | 5 | 4 | 5 | 4 | **83** |
| 7 | SOL-011 | 4 | 4 | 4 | 4 | 5 | 4 | **83** |
| 8 | SOL-006 | 4 | 4 | 5 | 4 | 4 | 3 | **82** |
| 9 | SOL-014 | 3 | 3 | 5 | 5 | 5 | 4 | 82 |
| 10 | SOL-010 | 3 | 3 | 5 | 4 | 5 | 4 | 79 |
| 11 | SOL-008 | 4 | 4 | 4 | 3 | 5 | 2 | 76 |
| 12 | SOL-018 | 2 | 3 | 4 | 5 | 5 | 5 | 76 |
| 13 | SOL-009 | 4 | 4 | 4 | 4 | 3 | 3 | 75 |
| 14 | SOL-012 | 3 | 3 | 4 | 5 | 4 | 4 | 75 |
| 15 | SOL-015 | 3 | 3 | 4 | 3 | 5 | 4 | 72 |
| 16 | SOL-016 | 3 | 3 | 4 | 3 | 4 | 4 | 69 |
| 17 | SOL-019 | 2 | 3 | 4 | 3 | 5 | 4 | 68 |
| 18 | SOL-013 | 3 | 3 | 4 | 2 | 3 | 4 | 63 |
| 19 | SOL-017 | 3 | 3 | 3 | 4 | 3 | 3 | 63 |

**Tie-breaks:**
- SOL-005 is ahead of SOL-011 (both 83) on brief fit (F 5 vs 4).
- SOL-006 is ahead of SOL-014 (both 82). It is a complete solution with stronger problem evidence (E 4 vs 3), and SOL-014 mainly supplies content for the mandatory M-04.
- SOL-008 is ahead of SOL-018 (both 76) on evidence.
- SOL-009 is ahead of SOL-012 (both 75) on evidence and importance.
- SOL-013 is ahead of SOL-017 (both 63) because it is a brief stretch item.

**Sensitivity.** The cut between rank 8 (82) and rank 9 (82) is a tie broken by judgement. SOL-014 is the closest excluded candidate; much of it is delivered anyway by the mandatory M-04, which needs help content.

### Problem confidence vs solution confidence
Confidence that a problem exists is separate from confidence that our proposal would improve it.

| ID | Problem confidence | Solution confidence | Why they differ |
|---|---|---|---|
| SOL-001 | Medium-high: reports at 2 platforms plus published multi-step paths. Most CPS status reports concern established patients between procedures; Numotion is adjacent ongoing service | Medium | Only helps if the status is accurate and kept current |
| SOL-007 | Medium: a few reports at 2 locations, including a pre-first-visit logistics report at Forest Hills | Medium-high | Mostly content and display; cannot stop clinic-side time changes |
| SOL-002 | Medium-high: the most frequent reported theme; two clear new-patient reports (CPS, FOH) | Medium | Visibility does not create staff capacity |
| SOL-004 | High that the data is required (published at all 5); low-medium that typing it is a reported pain | Medium-high | OCR accuracy is testable; real cards vary |
| SOL-003 | Low-medium for **administrative** retyping specifically: one clear case (an insurance update not used at check-in, established patient); two other reports may describe clinical forms or clinical confirmation | Medium | Staff must actually use the summary; necessary clinical re-confirmation remains |
| SOL-005 | Low-medium: little direct review evidence of abandonment | Medium | Guidance supports staging; company rules may require the full packet first |
| SOL-011 | Medium: published rules; reviews mostly about post-visit billing | Medium-high | Displaying published facts is reliable; patient-specific estimates are out of scope |
| SOL-006 | Medium: published prerequisites plus authorisation reports (mostly established patients) | Medium-low | Company referral and booking rules are unknown, and they differ: AdaCare publishes direct self-scheduling |

### Tradeoffs in the shortlist
- **SOL-001, SOL-002 and SOL-006 form one chain** (see it, own it, act on it). They are the most persuasive story but carry the most operational dependency. Choosing all three uses three of your four picks.
- **SOL-007, SOL-004 and SOL-011 are the lowest-risk to demonstrate.** They rest on published facts and extend mandatory features. Their problem evidence is less dramatic.
- **SOL-003 and SOL-005 shape the data-entry experience.** SOL-003 has more direct (though partly ambiguous) evidence; SOL-005 is closer to the brief's completion metric but has weaker evidence.

---

## 4. Evidence cards (shortlist)

Each card follows this chain:
**AEA platform → practice/branch → journey stage → reference baseline → evidenced problem → proposed solution → improvement mechanism → proof → outcome to measure.**

**How sources are cited:**
- `S-N` IDs resolve to URLs and review dates in the [source register](../source/source-register.md). Company pages were read on 2026-10-15 unless the register says otherwise.
- Review evidence cites the [review report](2026-10-15-google-review-sentiment.md) section; dates are relative to the read date (2026-10-15). Google review dialogs have no stable URL; the URL given is the Google search route to the listing. Patient status comes from the review report §7.
- Profile citations name the profile file and section.
- Every card's portfolio connection uses an AEA listing source (S-10, S-13, S-17, S-20, S-22) plus a first-party link from the company to the named practice or branch.

### SOL-001 · Patient readiness status (rank 1)
- **Chain:** Commonwealth Pain & Spine → Louisville South (and Elizabethtown) → request to first visit, and between procedures → progress and owned referral work → status not visible → readiness status → visible progress and responsibility → synthetic referral-pending patient → status calls and request-to-visit days.
- **Problem:** A referred pain patient submits a request and then hears nothing for a while. They don't know whether the referral arrived, whether insurance or authorisation is pending, or what happens next, so they call to find out.
- **Portfolio connection:** Commonwealth Pain & Spine, AEA Current · Elevate (S-10, https://www.aeainvestors.com/portfolio/commonwealth-pain-spine/). Adjacent: Numotion, Current · Middle Market (S-22).
- **Practice/branch:** **Louisville South**, 4420 Dixie Hwy, the office Google labels "Shively" (S-69, S-70, https://www.mypainsolution.com/louisville-south/; `commonwealth-pain-spine.md` §1.1). Elizabethtown (S-69). Adjacent: Numotion Nashville branch, LaVergne TN (S-105; `numotion.md` §1.1).
- **Journey stage:** "Arrange the next appointment" and the wait between request and first visit ([baseline, "The common first visit journey"](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey), stage 3).
- **Reference baseline (guidance):**
  - Referral work has clear responsibilities and tracking — AHRQ Tool 21 (S-114).
  - Multi-step processes show progress and what remains — W3C (S-115).
  - Received, reviewed and approved are separate states — derived ([baseline, "Candidate baseline"](2026-10-15-patient-journeys-and-onboarding-baseline.md#candidate-baseline-for-evaluating-our-assistant)).
- **Company current state:**
  - *Published fact:* the CPS path "We'll Connect With Your Physician" → "Once your physician's referral is received, we'll reach out to schedule your initial appointment" (S-70; profile §1.2). Three phrasings of the scheduling aim (S-12, S-68, S-70; profile §1.4).
  - *Attributed reviews:* authorisation status not communicated and next steps unclear — Louisville South and Elizabethtown, dated about 9 months to 8 years before 2026-10-15 (S-77; review report §1 items 4–5). **These are mostly established patients between procedures** (review report §7). One new-patient report describes a referral-to-first-visit interval of over six weeks, about 5 years ago.
  - *Adjacent:* Numotion reviewers report chasing progress on repairs and funding (S-107; review report §5). Established customers; Numotion's app documents status features (S-106).
  - Search routes: https://www.google.com/search?q=Commonwealth+Pain+%26+Spine+reviews ; https://www.google.com/search?q=Numotion+Nashville+TN (read 2026-10-15).
- **Evidence type:** published fact + attributed review + general guidance.
- **Proposed behaviour:**
  - The patient sees the company's own step names with a state for each: Received / With our team / Reviewed / Done / Not needed.
  - They see what is missing, which team role handles it, and the next step.
  - Company aims appear only as labelled aims.
  - Staff change each state; the patient view updates.
- **Why it could address the problem:** visible progress and named responsibility replace guesswork. Keeping "received" separate from "reviewed" prevents false readiness.
- **Business-value mechanism (hypothesis):** fewer "where is my request?" calls → lower staff effort; fewer silent drop-offs between request and first visit → more completed intakes → more attended first visits.
- **Synthetic demonstration:** a referral-pending patient based on SIM-CPS-1 ([demo blueprint §1](2026-10-15-demo-blueprint.md#1-commonwealth-pain--spine)). **Pass if:**
  1. every pending item shows one owning role and one next step;
  2. an uploaded referral never shows "Reviewed" until a staff action exists;
  3. no date is shown unless a company aim is configured, and then it is labelled "aim";
  4. a staff state change appears on the patient view at the next load;
  5. insurance is never shown as "approved".
- **Metric and measured baseline:**
  - *Synthetic:* whether a tester correctly states what's missing and who acts (yes/no); status-related staff actions.
  - *Company:* status calls per new patient; days from request to first visit against the company aim.
  - *Measured baseline:* **unknown** (RQ-2, RQ-38).
- **Dependencies and limits:** requires SOL-002. Cannot speed referring offices, payers or staffing. Status is only as accurate as staff updates or a future integration. It does not create appointment availability. Numotion's funding stages are outside first-visit scope (P-03).
- **Reason to choose:** the most direct answer to the four patient questions and to the brief's "uncertainty about next steps", with evidence at two platforms.
- **Reason to defer:** it requires SOL-002; it risks "status theatre" if no one owns updates; much of its review support concerns established patients.
- **Selection:** ☐ (Innocent)

### SOL-007 · Confirmation and visit-logistics package (rank 2)
- **Chain:** Metro Vein Centers → Queens–Forest Hills → prepare for the visit → appointment logistics → missing directions, changed times → record-backed confirmation package → everything needed to arrive in one place → SIM-MVC-1 → wrong-time arrivals.
- **Problem:** A patient gets a booking but no address, directions, arrival time or what to bring. They arrive at the wrong time, or find the appointment is not recognised.
- **Portfolio connection:** Metro Vein Centers, AEA Current · Elevate (S-17, https://www.aeainvestors.com/portfolio/metro-vein-centers/). Secondary: Commonwealth (S-10).
- **Practice/branch:** **Queens–Forest Hills** (S-89, S-90, https://www.metroveincenters.com/locations/new-york/queens-forest-hills; `metro-vein-centers.md` §1.1). Secondary: CPS Louisville South (S-70).
- **Journey stage:** "Prepare for the visit" ([baseline journey](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey), stage 5).
- **Reference baseline (guidance):** appointment logistics are part of pre-registration (AMA, S-108); "Give appointment logistics" ([baseline, "Candidate baseline"](2026-10-15-patient-journeys-and-onboarding-baseline.md#candidate-baseline-for-evaluating-our-assistant)).
- **Company current state:**
  - *Published fact:* Forest Hills hours (S-90). SMS reminders and reschedule-by-text exist (S-19, S-86; profile §1.2). CPS arrival times and what-to-bring list (S-12; CPS profile §1.5).
  - *Attributed reviews:* at Forest Hills, a booked patient who did not attend reported that expected email and text, address and instructions did not arrive (about a year before 2026-10-15); others reported times changed without notice or at arrival (about 2 months and about a year before) (S-91; review report §3). At Louisville South, an established patient reported an automated confirmation that was not in the system at arrival (about a month before; review report §1 item 2). **The cause is not established.** https://www.google.com/search?q=Metro+Vein+Centers+Forest+Hills+NY
- **Evidence type:** published fact + attributed review + general guidance.
- **Proposed behaviour:**
  - The confirmation is generated only from a stored booking.
  - It shows the visit type (for example "free evaluation", not treatment), the office address and hours, the date and time, and arrival and what-to-bring text from approved company content.
  - It also shows the published cancellation policy and how to reschedule.
  - Staff see the same record.
- **Why it could address the problem:** one durable, record-backed confirmation puts everything needed to arrive correctly in one place.
- **Business-value mechanism (hypothesis):** fewer wrong-time and unprepared arrivals → more on-time, attended visits; fewer reschedules.
- **Synthetic demonstration:** SIM-MVC-1 ([demo blueprint §3](2026-10-15-demo-blueprint.md#3-metro-vein-centers)). **Pass if:**
  1. no confirmation exists without a stored booking;
  2. its fields match the booking record;
  3. the visit type is explicit;
  4. reloading preserves it, and double-booking is rejected (M-03);
  5. missing company content shows "ask our team" rather than invented text.
- **Metric and measured baseline:**
  - *Synthetic:* field-match rate; tester can name the place, time and what to bring.
  - *Company:* wrong-time arrivals; same-day reschedules.
  - *Measured baseline:* **unknown**.
- **Dependencies and limits:** cannot prevent clinic-side schedule changes or overbooking (P-08). Real SMS or email delivery needs a vendor and consent (SOL-008, SOL-010). Slots are synthetic (P-05).
- **Reason to choose:** low effort, extends a mandatory feature, reusable everywhere.
- **Reason to defer:** the reports are few and from two locations; it may read as basic.
- **Selection:** ☐ (Innocent)

### SOL-002 · Owned staff handoff queue (rank 3)
- **Chain:** Commonwealth and AON/FOH → Louisville South, Elizabethtown, Naples → request to first contact → owned referral work and recovery routes → unreturned calls, automation without a human → owned, ageing queue with context-preserving escalation → every request visible and owned → SIM-CPS-2, SIM-FOH-2 → time to first human contact.
- **Problem:** A new-patient or referral request goes into voicemail or an automated system, and nobody visibly owns the next action. The patient repeats themselves, or goes elsewhere.
- **Portfolio connection:** Commonwealth Pain & Spine (S-10); American Oncology Network, AEA Current · Elevate (S-20, https://www.aeainvestors.com/portfolio/american-oncology-network/). Adjacent: Numotion (S-22).
- **Practice/branch:** CPS **Louisville South** and **Elizabethtown** (S-69). **Florida Oncology & Hematology, Naples**, linked from AON's own practice page (S-21, https://www.aoncology.com/practices/florida-oncology-and-hematology/); FOH forms say "a division of American Oncology Partners" (S-98; `american-oncology-network.md` §1.2). Adjacent: Numotion Nashville (S-105).
- **Journey stage:** "Find and request care" through "Arrange the next appointment", plus reaching a person at any stage ([baseline journey](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey), stages 1–3).
- **Reference baseline (guidance):** referral responsibilities and tracking (AHRQ, S-114); successful submission and recovery routes are communicated (W3C, S-116); "Keep referral work owned" ([baseline, "Candidate baseline"](2026-10-15-patient-journeys-and-onboarding-baseline.md#candidate-baseline-for-evaluating-our-assistant)).
- **Company current state:**
  - *Published fact:* CPS advertises a virtual agent that will "connect you with the appropriate member of your care team when needed" (S-66; profile §1.1). At FOH, "a Patient Services Specialist will contact you" (S-96).
  - *Attributed reviews (keyword counts in each Lowest sample):* callback and reach-a-person themes — Louisville South 10/58, Elizabethtown 4/41, FOH Naples 3/6, Numotion 3/27 (review report §6).
  - *Clear new-patient reports:* a referred CPS patient who waited two weeks for a call (Louisville South, about 5 months before 2026-10-15; paraphrased, review report §1 item 1) and an FOH new patient whose calls to new-patient scheduling went unreturned over two weeks and who went elsewhere (Naples, about 9 months before; paraphrased, review report §4).
  - *Other reports* concern established patients or rescheduling, and automated routes without a human (review report §1 items 1–2; vendor and cause **not established**).
  - Search routes: as SOL-001, plus https://www.google.com/search?q=%22Florida+Oncology+%26+Hematology%22+Cape+Coral+Naples+Fort+Myers.
- **Evidence type:** attributed review + published fact + general guidance.
- **Proposed behaviour:**
  - On submit, the patient gets an acknowledgement and a reference.
  - The request appears once in a staff queue with an owning role, a status and its age against the company's stated aim (for CPS, "ten business days", S-68).
  - "Talk to a person" in the chat creates a queue item carrying the conversation, so nothing is re-entered.
  - The patient is told the request was sent, never that someone has replied until a staff action exists.
- **Why it could address the problem:** every request becomes visible and owned; ageing exposes stalls before the patient has to chase.
- **Business-value mechanism (hypothesis):** fewer lost requests and referrals → more completed intakes → more attended first visits; less duplicated calling.
- **Synthetic demonstration:** SIM-CPS-2 and SIM-FOH-2 ([demo blueprint §1](2026-10-15-demo-blueprint.md#1-commonwealth-pain--spine) and [§4](2026-10-15-demo-blueprint.md#4-american-oncology-network-florida-oncology--hematology)). **Pass if:**
  1. each request appears exactly once, with an owner role;
  2. escalation keeps prior answers;
  3. no message implies a human response before one exists;
  4. items past a configured age are flagged;
  5. staff access is role-scoped and audit-logged (M-07).
- **Metric and measured baseline:**
  - *Synthetic:* requests with an owner (%); re-entered fields at escalation (target 0).
  - *Company:* time to first human contact; repeat calls per request.
  - *Measured baseline:* **unknown** (RQ-4, RQ-27, RQ-38).
- **Dependencies and limits:** does not add staff capacity. Who owns intake is unknown. Phone and voicemail systems are untouched. No CRM or practice-management integration (P-04).
- **Reason to choose:** answers the most frequent reported theme, including the two clearest new-patient reports, and is a prerequisite for SOL-001 and SOL-006.
- **Reason to defer:** its value depends on staff behaviour and is less visible in a patient-side demo.
- **Selection:** ☐ (Innocent)

### SOL-004 · Insurance capture with OCR and confirmation (rank 4)
- **Chain:** Commonwealth (and Numotion) → company-wide request form; Nashville branch → establish the record, administrative packet → collect once; insurance checks in pre-registration → typing and missing insurance data → card OCR with confirmation → less typing, earlier verification → synthetic card golden set → coverage verified before visit.
- **Problem:** A patient types insurer, member ID, group, policyholder and sometimes secondary insurance — or a Medicare number — from a card. Missing or mistyped data delays verification.
- **Portfolio connection:** Commonwealth (S-10); Numotion (S-22). Also published at Metro Vein (S-17), ADC via AdaCare (S-13) and AON via FOH (S-20).
- **Practice/branch:** CPS's company-wide request form, used for any of its 33 offices including Louisville South (S-75; `commonwealth-pain-spine.md` §1.2). Numotion Nashville branch (S-105).
- **Journey stage:** "Establish the patient record" and "Complete the administrative packet" ([baseline journey](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey), stages 2 and 4).
- **Reference baseline (guidance):** insurance checks belong in pre-registration (AMA, S-108). Collect needed information once (AHRQ, S-112).
- **Company current state:**
  - *Published fact:* CPS requires the insurance company and member ID on its request form and says to bring the cards (S-75, S-12). Numotion asks for primary and secondary insurance and the MBI for standard Medicare, and says missing details cause delays (S-102; `numotion.md` §1.2). MVC quotes the first visit when insurance is given at scheduling (S-87). AdaCare's packet has two dental insurances (S-82). FOH's packet has insurance with policyholder details (S-98).
  - *Attributed review (indirect):* an established Louisville South patient reported that an insurance update sent before the visit was not available at check-in (about 2 years before 2026-10-15; review report §1 item 3). It is about data carrying through, not typing.
- **Evidence type:** published fact + general guidance + one indirect attributed review.
- **Proposed behaviour:**
  - Photograph the front and back of a synthetic card; extract the carrier, member ID, group and policyholder; the patient confirms or edits each field.
  - A secondary-insurance option; an MBI field when Medicare is chosen (Numotion configuration).
  - The status reads "coverage check pending", never "covered".
- **Why it could address the problem:** less typing and fewer transcription errors; insurance is available before scheduling, so staff can verify early.
- **Business-value mechanism (hypothesis):** earlier verification → fewer day-of coverage surprises and cancellations; less staff keying.
- **Synthetic demonstration:** a card golden set with fictional carriers and layouts (RQ-17). **Pass if:**
  1. field-level accuracy meets a threshold set in advance (we suggest matching the brief's 90%);
  2. every field is shown for confirmation;
  3. partially read cards leave blanks rather than guesses;
  4. no "approved" state appears;
  5. the image is discarded after confirmation (M-06).
- **Metric and measured baseline:**
  - *Synthetic:* field accuracy; fields corrected; seconds to enter.
  - *Company:* coverage verified before the visit (%); keying minutes.
  - *Measured baseline:* **unknown**.
- **Dependencies and limits:** builds on M-02 and M-05. Does not check eligibility or benefits (no payer API). Real card formats vary. Adds sensitive data, so minimisation and consent apply (M-05, M-06).
- **Reason to choose:** extends the brief's core OCR with data every platform publishes as needed.
- **Reason to defer:** extra golden-set work and more sensitive data; the direct "typing is painful" evidence is thin.
- **Selection:** ☐ (Innocent)

### SOL-003 · Collect-once administrative record and staff summary (rank 5)
- **Chain:** Commonwealth and AON/FOH → Louisville South, Elizabethtown, Naples → record, packet, arrival → collect once; usable staff summary → administrative details re-asked or not seen at check-in → one record pre-filling later steps plus a staff summary → reuse removes retyping → SIM-CPS-1, SIM-ADA-1 → re-keyed fields and check-in minutes.
- **Problem:** A patient supplies administrative details online, then is asked the same questions again, or finds their update was not seen at check-in.
- **Portfolio connection:** Commonwealth (S-10); AON (S-20).
- **Practice/branch:** CPS **Louisville South** and **Elizabethtown** (S-69, S-77). FOH Naples (S-21, S-100).
- **Journey stage:** "Establish the patient record", "Complete the administrative packet" and "Arrive and reconcile" ([baseline journey](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey), stages 2, 4 and 6).
- **Reference baseline (guidance):** collect need-to-know information once (AHRQ, S-112). "Reuse administrative answers" and "Produce a usable staff summary" ([baseline, "Candidate baseline"](2026-10-15-patient-journeys-and-onboarding-baseline.md#candidate-baseline-for-evaluating-our-assistant)).
- **Company current state:**
  - *Attributed reviews:* repeated-question keyword hits — Louisville South 4/58, Elizabethtown 2/41 (S-77; review report §1 item 3 and §6). **Read the patient status before relying on them** (review report §7): the clearest administrative case is an established patient's insurance update not available at check-in (about 2 years before 2026-10-15). One report refers to "medical forms" (about 9 months before) and one to questions asked again by clinical staff (about 3 years before); both may be clinical confirmation, which is not waste. FOH Naples: "System to collect info was hard to fill out" (4★, about 7 months before; review report §4).
  - *Published fact:* long administrative packets — FOH's 14 pages (S-98), AdaCare's 4 pages (S-82).
- **Evidence type:** attributed review + published fact + general guidance.
- **Proposed behaviour:**
  - Each administrative fact is entered or confirmed once; later steps pre-fill it; a correction anywhere updates the staff summary.
  - The summary separates confirmed, missing and pending items and the patient's preferences.
  - Clinical questions are excluded and are **not** counted as repetition ([baseline, "Clinical information and the administrative boundary"](2026-10-15-patient-journeys-and-onboarding-baseline.md#clinical-information-and-the-administrative-boundary)).
- **Why it could address the problem:** reuse removes administrative retyping and makes what was submitted visible at arrival.
- **Business-value mechanism (hypothesis):** shorter check-in; fewer staff re-keying minutes; a better first impression → retention.
- **Synthetic demonstration:** SIM-CPS-1 and SIM-ADA-1 ([demo blueprint §1](2026-10-15-demo-blueprint.md#1-commonwealth-pain--spine) and [§2](2026-10-15-demo-blueprint.md#2-american-dental-companies-adacare-meridian-id)). **Pass if:**
  1. an address confirmed in the record step is pre-filled in the packet and in the summary;
  2. a packet correction updates the summary;
  3. no administrative field is asked twice;
  4. the summary lists missing items.
- **Metric and measured baseline:**
  - *Synthetic:* duplicate administrative prompts (target 0); fields re-entered by staff.
  - *Company:* check-in minutes; re-keyed fields.
  - *Measured baseline:* **unknown**.
- **Dependencies and limits:** cannot remove repetition inside company systems without integration (P-04). Clinical reconciliation stays. Arrival staff need access (SOL-018 or a future integration).
- **Reason to choose:** low risk; it improves every other candidate's data.
- **Reason to defer:** the direct administrative evidence is one established-patient report; much of the value is staff-side; it is partly implied by the mandatory structured record (M-01).
- **Selection:** ☐ (Innocent)

### SOL-005 · Staged, resumable administrative packet (rank 6)
- **Chain:** AON/FOH and ADC/AdaCare → FOH, AdaCare Meridian → request through packet → streamlined forms, progress, preserved data; before or at arrival → long packets presented at once → staged, resumable packet with an assisted route → lower starting effort → simulated packet comparison → administrative completion before arrival.
- **Problem:** A new patient faces a long packet at once (for example a 14-page oncology packet). They cannot save and return, or must arrive early to finish on paper.
- **Portfolio connection:** AON (S-20); American Dental Companies, AEA Current · Elevate (S-13, https://www.aeainvestors.com/portfolio/american-dental-companies/).
- **Practice/branch:** **FOH**: its 14-page packet (S-98; `american-oncology-network.md` §1.2). **AdaCare, Meridian ID**: listed on ADC's partner page (S-14), and its booking URL contains `american-dental-companies` (S-16, S-83). Its 4-page paper packet is print-ahead or "arrive 10 minutes early" (S-82, S-16; `american-dental-companies.md` §1.2). Contrast benchmark: MVC's 4-field form (S-88).
- **Journey stage:** stages 1–4 of the [baseline journey](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey). At AdaCare, scheduling is already self-service with visible slots (S-83), so this candidate concerns the packet after booking, not booking itself.
- **Reference baseline (guidance):** streamline forms and ask what's needed (AHRQ, S-112); logical steps, progress, and data preserved when going back (W3C, S-115); registration before the visit **or** at arrival (AMA, S-108).
- **Company current state:**
  - *Published fact:* packet lengths and formats (above).
  - *Attributed reviews:* **no direct review evidence that length causes abandonment** at these locations ([review pitfalls, "What the reviews support less directly"](2026-10-15-review-pitfalls-and-solution-opportunities.md#what-the-reviews-support-less-directly); review report §7). The brief states the abandonment hypothesis (S-1).
- **Evidence type:** published fact + general guidance + brief hypothesis.
- **Proposed behaviour:**
  - Start with only what's needed to begin.
  - Later administrative sections appear when relevant (for example, records release only for transfers).
  - Save and resume; going back never loses answers; field errors say how to fix them.
  - Staff can finish with the patient on arrival.
- **Why it could address the problem:** lower starting effort and fewer dead ends → more patients reach a complete administrative record.
- **Business-value mechanism (hypothesis):** the brief's completion metric (illustrative 50% → 70%, S-1) → completed intakes → attended visits.
- **Synthetic demonstration:** compare a **simulated** conventional packet with the staged flow, using identical required information and both labelled simulated ([baseline, "How to evaluate the proposed improvement"](2026-10-15-patient-journeys-and-onboarding-baseline.md#how-to-evaluate-the-proposed-improvement)). **Pass if:**
  1. a tester can start within a defined small number of questions;
  2. closing and resuming keeps answers;
  3. going back preserves data;
  4. a staff-assisted path completes the same record.
- **Metric and measured baseline:**
  - *Synthetic:* completion time; abandonment points; fields corrected.
  - *Company:* administrative completion before arrival (%).
  - *Measured baseline:* **unknown**. What counts as "complete" is open (RQ-45).
- **Dependencies and limits:** weak direct evidence that packet length is the problem. Companies may require the full packet before booking (RQ-6, RQ-45). It cannot shorten what a company legally needs. Whether FOH's packet can already be done in CareSpace is unknown (RQ-42).
- **Reason to choose:** sits closest to the brief's own success metric and reuses everywhere.
- **Reason to defer:** the weakest direct problem evidence in the shortlist.
- **Selection:** ☐ (Innocent)

### SOL-011 · Published cost and policy transparency (rank 7)
- **Chain:** Commonwealth, ADC/AdaCare, Metro Vein → company-wide CPS policies, AdaCare, MVC → before booking and preparation → cost questions routed to staff, no invented prices → policies found only on FAQ pages → published notices at the relevant step plus an estimate-request task → informed booking → SIM-CPS-2, SIM-MVC-3 → late cancellations.
- **Problem:** An uninsured or cost-worried patient learns about self-pay rules, cancellation fees or prices only if they find an FAQ, or at the visit.
- **Portfolio connection:** Commonwealth (S-10); ADC (S-13); Metro Vein (S-17).
- **Practice/branch:** CPS company-wide policies (S-12; `commonwealth-pain-spine.md` §1.3), which apply at any office including Louisville South. AdaCare Meridian: "$89 New Patient Exam and X-rays" (S-16; `american-dental-companies.md` §1.2) and fees in the forms (S-82). MVC: "$425 per session" for cosmetic care and a $425–$1,500 self-pay range (S-86; `metro-vein-centers.md` §1.3).
- **Journey stage:** "Arrange the next appointment" and "Prepare for the visit" ([baseline journey](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey), stages 3 and 5).
- **Reference baseline (guidance):** good-faith estimates for people not using insurance, under conditions (CMS, S-118); "Support cost questions" through a staff route, without invented prices ([baseline, "Candidate baseline"](2026-10-15-patient-journeys-and-onboarding-baseline.md#candidate-baseline-for-evaluating-our-assistant)).
- **Company current state:**
  - *Published fact:* CPS self-pay "to accommodate uninsured patients only" and a $50 fee for cancelling with less than 24 hours' notice (S-12). The prices above.
  - *Attributed reviews:* billing or charge themes — Louisville South 9/58, Elizabethtown 3/41, FOH 2/6, AdaCare 3/5 (review report §6). These are **mostly post-visit billing, so only indirectly about onboarding.** AdaCare's low reviews mention price (review report §2).
- **Evidence type:** published fact + general guidance + indirect review.
- **Proposed behaviour:**
  - At the relevant step, show the company's published prices, self-pay rules, fees and payment options, each with its source date.
  - Show "coverage check pending" where relevant.
  - "Request an estimate" creates a billing task (SOL-002). No price is generated.
- **Why it could address the problem:** patients decide with known costs and policies, before they book.
- **Business-value mechanism (hypothesis):** fewer cancellations and no-shows driven by cost surprise; fewer billing disputes.
- **Synthetic demonstration:** SIM-CPS-2 (work-injury and cost-concern notices) and SIM-MVC-3 (cosmetic price) ([demo blueprint](2026-10-15-demo-blueprint.md)). SIM-MVC-3 also contains ⚑ RQ-44 questions; only its price notice is used here. **Pass if:**
  1. every amount shown matches its configured source exactly, with date;
  2. nothing is shown where nothing is published;
  3. an estimate request creates a staff task;
  4. coverage is never stated.
- **Metric and measured baseline:**
  - *Synthetic:* correct notice shown per branch (%).
  - *Company:* late cancellations; cost-related questions.
  - *Measured baseline:* **unknown**.
- **Dependencies and limits:** needs SOL-002 for estimate requests. No patient-specific estimates. Published prices change, so the content needs a refresh process. Legal estimate duties need company confirmation (RQ-33, RQ-46).
- **Reason to choose:** published, low effort, three platforms.
- **Reason to defer:** the review evidence is mostly about after the visit.
- **Selection:** ☐ (Innocent)

### SOL-006 · Prerequisite-aware next step (rank 8)
- **Chain:** Commonwealth, AON/FOH, Numotion → Louisville South, FOH, Nashville → arrange the next appointment → referral ownership; a coordination appointment as the bookable next step, never a bypass → bookings attempted while prerequisites are pending → prerequisite-aware booking with a coordination slot → prevents failing bookings while giving a next step → SIM-CPS-2, SIM-FOH-1 → visits cancelled for missing prerequisites.
- **Problem:** A patient whose referral, workers'-comp authorisation, outside records or physician face-to-face visit is still pending either books a clinical visit that can't go ahead, or gets no next step at all.
- **Portfolio connection:** Commonwealth (S-10); AON (S-20); Numotion (S-22). Contrast: ADC via AdaCare (S-13).
- **Practice/branch:**
  - CPS **Louisville South**: its published path depends on the physician's referral (S-70; profile §1.2). Plan-dependent referral wording conflicts (profile §1.3). "Treatment for worker’s compensation needs authorization before scheduling" (S-12).
  - **FOH**: entry by "physician's referral or transfer" (S-95; `american-oncology-network.md` §1.2).
  - Numotion Nashville branch: a referral, and a face-to-face physician visit for complex chairs (S-102; `numotion.md` §1.2).
  - **Contrast, AdaCare Meridian:** a New Patient Visit is self-bookable with visible slots (S-83, re-read 2026-10-15). The rule therefore has to be configurable per company and appointment type, including "no prerequisite".
- **Journey stage:** "Arrange the next appointment" ([baseline journey](2026-10-15-patient-journeys-and-onboarding-baseline.md#the-common-first-visit-journey), stage 3).
- **Reference baseline (guidance):** referral responsibilities and tracking (AHRQ, S-114); a visit with prerequisites may make a staff-coordination appointment the bookable next step, never a referral bypass ([baseline, "Requirements that come from the issued brief"](2026-10-15-patient-journeys-and-onboarding-baseline.md#requirements-that-come-from-the-issued-brief)); received, reviewed and approved are separate ([baseline, "Candidate baseline"](2026-10-15-patient-journeys-and-onboarding-baseline.md#candidate-baseline-for-evaluating-our-assistant)).
- **Company current state:**
  - *Published fact:* the prerequisites above.
  - *Attributed reviews:* authorisation status not communicated, and arriving to find treatment not authorised (Louisville South about a year before 2026-10-15; Elizabethtown about 8 years before) (S-77; review report §1 item 4). **These concern established patients' procedures, not first visits** (review report §7).
- **Evidence type:** published fact + attributed review + general guidance.
- **Proposed behaviour:**
  - While a prerequisite is pending, clinical slot types are not offered. The patient books a staff-coordination call (a real, stored and confirmed booking).
  - Staff mark the prerequisite reviewed, which unlocks clinical booking.
  - Where the company publishes direct booking (AdaCare), the clinical slot is offered at once.
  - Work-injury, motor-vehicle and uninsured branches show the company's own text.
- **Why it could address the problem:** it prevents bookings that would fail, while still giving a concrete next step and an owner.
- **Business-value mechanism (hypothesis):** fewer day-of cancellations for missing authorisation; fewer wasted slots; conversion kept by a real next step.
- **Synthetic demonstration:** SIM-CPS-2 (work injury) and SIM-FOH-1 ([demo blueprint](2026-10-15-demo-blueprint.md)), with SIM-ADA-1 as the no-prerequisite contrast. **Pass if:**
  1. with a prerequisite pending, no clinical slot is offered;
  2. a coordination slot can be booked and confirmed (M-03);
  3. only a staff action unlocks clinical booking;
  4. the product never marks a referral or authorisation approved;
  5. there is no bypass path;
  6. a configuration with no prerequisite offers clinical slots directly.
- **Metric and measured baseline:**
  - *Synthetic:* blocked invalid clinical bookings (target 100%).
  - *Company:* visits cancelled for missing prerequisites.
  - *Measured baseline:* **unknown**.
- **Dependencies and limits:** needs SOL-002. The real referral and booking rules are unknown (RQ-7, RQ-8, RQ-35, RQ-39). Coordination appointments may not exist at the companies. It does not speed payers or referring offices.
- **Reason to choose:** reconciles the mandatory booking with the administrative-only boundary — a strong, defensible story that also shows per-company configuration.
- **Reason to defer:** the rules are assumptions until a company confirms them; its review support concerns established patients; complexity is medium-high.
- **Selection:** ☐ (Innocent)

---

## 5. Interview explanations and audit trail

Research-tense wording: what inspired each idea and what we would show. **Nothing is built, deployed or proven.** At this stage it is defensible to say "a public report or published requirement inspired a capability meant to address a particular failure mode". After implementation, describe only the behaviour built and demonstrated. Claim a company improvement only when company-level measurement exists.

| ID | What inspired it | Portfolio example | What it is meant to address | What would count as proof | What remains unproven |
|---|---|---|---|---|---|
| SOL-001 | Reports of not knowing authorisation status or next steps (mostly established patients), plus Commonwealth's published three-step path | Commonwealth, Louisville South and Elizabethtown (S-10, S-70, S-77) | A patient's uncertainty between request and first visit | Synthetic: the five pass conditions in its card. Real: fewer status calls and shorter request-to-visit time against a measured baseline | Whether status stays accurate in a real office, and whether it reduces calls or drop-off |
| SOL-007 | Forest Hills reports of missing directions and changed times; Commonwealth's published arrival instructions | Metro Vein, Forest Hills; Commonwealth, Louisville South (S-17, S-90, S-91, S-12) | Arriving unprepared, at the wrong time, or without a recognised booking | Synthetic: confirmation only from a stored booking, matching fields. Real: fewer wrong-time arrivals | Effect on attendance; clinic-side schedule changes remain |
| SOL-002 | The most frequent reported theme (callbacks), including two clear new-patient reports at Commonwealth and FOH; AHRQ referral guidance | Commonwealth (two offices); AON via FOH Naples (S-10, S-20, S-77, S-100, S-114) | Requests with no visible owner | Synthetic: every request appears once, owned and ageing, with context-preserving escalation. Real: shorter time to first human contact | Staff capacity and adoption; real owner routing |
| SOL-004 | Insurance requirements published by all five platforms; the brief's OCR requirement | Commonwealth request form (company-wide); Numotion Nashville (S-10, S-22, S-75, S-102) | Typing and missing insurance data before scheduling | Synthetic: card OCR accuracy at the preset threshold, confirmation of every field. Real: more coverage verified before the visit | Accuracy on real cards; effect on verification time |
| SOL-003 | One Commonwealth report of an insurance update unused at check-in, other repeated-question reports (partly clinical), and AHRQ collect-once guidance | Commonwealth, Louisville South and Elizabethtown (S-10, S-77, S-112) | Administrative retyping and invisibility at arrival | Synthetic: zero duplicate administrative prompts; corrections flow to the summary. Real: fewer re-keyed fields | Whether real check-in staff would use it; integration needs |
| SOL-005 | Published packet lengths (FOH 14 pages; AdaCare paper), W3C and AHRQ form guidance, and the brief's abandonment hypothesis | AON via FOH; ADC via AdaCare Meridian (S-20, S-13, S-98, S-82) | Up-front form burden | Synthetic: staged, resumable completion against a simulated conventional packet. Real: higher completion before arrival | That length causes abandonment at these locations; company "required before booking" rules |
| SOL-011 | Published self-pay, fee and price rules; CMS estimate guidance | Commonwealth (company-wide); ADC via AdaCare; Metro Vein (S-12, S-16, S-86, S-118) | Cost and policy surprises | Synthetic: exact published notices per branch; estimate request routed to staff. Real: fewer cost-driven cancellations | Effect on cancellations; whether companies approve showing prices |
| SOL-006 | Published referral, authorisation and face-to-face prerequisites; authorisation reports (established patients); AdaCare's direct self-scheduling as the contrast | Commonwealth Louisville South; AON via FOH; Numotion Nashville; ADC via AdaCare (S-12, S-70, S-95, S-102, S-83, S-77) | Booking a visit that cannot go ahead | Synthetic: coordination booking while a prerequisite is pending; clinical booking unlocked only by staff; direct booking where configured. Real: fewer cancellations for missing prerequisites | The companies' real rules; whether coordination slots exist |

### Evidence-status ledger
Fill these columns in later; never rewrite a hypothesis as a past result. "Validated in a real company workflow" requires company data and access; nothing in this project yet provides either.

| ID | Inspired by evidence | Proposed | Selected by Innocent | Implemented | Demonstrated with synthetic data | Validated in a real company workflow |
|---|---|---|---|---|---|---|
| SOL-001 | Yes — S-70, S-77, S-114 (2026-10-15) | Yes — this file | ☐ pending | pending | pending | pending |
| SOL-007 | Yes — S-90, S-91, S-12, S-108 | Yes | ☐ pending | pending | pending | pending |
| SOL-002 | Yes — S-77, S-100, S-114, S-66 | Yes | ☐ pending | pending | pending | pending |
| SOL-004 | Yes — S-75, S-102, S-87, S-82, S-108 | Yes | ☐ pending | pending | pending | pending |
| SOL-003 | Yes — S-77, S-100, S-112 | Yes | ☐ pending | pending | pending | pending |
| SOL-005 | Yes — S-98, S-82, S-112, S-115, S-1 | Yes | ☐ pending | pending | pending | pending |
| SOL-011 | Yes — S-12, S-16, S-86, S-118 | Yes | ☐ pending | pending | pending | pending |
| SOL-006 | Yes — S-12, S-70, S-95, S-102, S-83, S-77 | Yes | ☐ pending | pending | pending | pending |

---

## 6. My selection area

**How to record your choice.** Tick about four boxes below (change `[ ]` to `[x]`), or tell Claude the IDs and they will be recorded for you. Then add the date to the matching "Selected by Innocent" cell in the ledger above. The mandatory baseline (M-01…M-15) is already in. Selecting is not a PRD decision; the PRD comes after you say research is done.

- [ ] **SOL-001 Patient readiness status** — answers "what's missing, who handles it, what's next?". *Tradeoff:* needs SOL-002; status must be kept current; much review support is established patients. *Depends on:* SOL-002.
- [ ] **SOL-007 Confirmation and visit-logistics package** — arrive right, on time, prepared; easy to show. *Tradeoff:* thinner evidence; looks basic. *Depends on:* M-03.
- [ ] **SOL-002 Owned staff handoff queue** — nothing gets lost; a human route with context. *Tradeoff:* value is staff-side and depends on staffing. *Depends on:* owner roles (RQ-4, RQ-27; simulated in the demo).
- [ ] **SOL-004 Insurance capture with OCR** — less typing; earlier verification; extends the required OCR. *Tradeoff:* card golden set; more sensitive data. *Depends on:* M-02, M-05.
- [ ] **SOL-003 Collect-once record and staff summary** — no administrative retyping. *Tradeoff:* direct administrative evidence is one report; staff-side value; partly implied by M-01. *Depends on:* SOL-002 or SOL-018 for a staff view.
- [ ] **SOL-005 Staged, resumable packet** — closest to the brief's completion metric. *Tradeoff:* weakest direct evidence. *Depends on:* RQ-45 definition of "complete".
- [ ] **SOL-011 Published cost and policy transparency** — no surprises; low effort. *Tradeoff:* the reviews are mostly about billing after the visit. *Depends on:* SOL-002 for estimate requests.
- [ ] **SOL-006 Prerequisite-aware next step** — respects referrals and authorisations while still giving a next step. *Tradeoff:* rules are assumptions; needs SOL-002. *Depends on:* SOL-002, M-03.

**Combination notes (information only, not a recommendation):**
- Choosing **SOL-001** or **SOL-006** without **SOL-002** leaves an unowned step. Count SOL-002 as part of either.
- **SOL-001 + SOL-002 + SOL-006** make one "see it, own it, act on it" chain and use three picks.
- **SOL-004 + SOL-003** strengthen the data-entry story around the mandatory OCR and record.
- **SOL-007** and **SOL-011** are independent, low-dependency additions.

**Open decisions that sit next to this choice (not part of it):** RQ-44 (whether any optional clinical-adjacent context is collected; P-01) and RQ-45 (where intake ends, and whether established-patient problems are in scope; P-11).

**The single decision you need to make:** which four of these eight candidates go into scope, given that SOL-001 and SOL-006 each bring SOL-002 with them?

---

## Appendix — Evidence-chain audit (2026-10-15)

Each shortlisted card was checked for every link in the chain. ✓ means present, with a source.

| ID | Platform | Practice | Stage | Reference baseline | Company state | Patient status labelled | Measured baseline | Solution | Mechanism | Demo pass/fail | Outcome metric |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SOL-001 | ✓ S-10 | ✓ S-70 | ✓ | ✓ S-114, S-115 | ✓ S-70, S-77 | ✓ mostly established | unknown (stated) | ✓ | ✓ | ✓ | ✓ |
| SOL-007 | ✓ S-17 | ✓ S-90 | ✓ | ✓ S-108 | ✓ S-90, S-91 | ✓ mixed | unknown (stated) | ✓ | ✓ | ✓ | ✓ |
| SOL-002 | ✓ S-10, S-20 | ✓ S-69, S-21 | ✓ | ✓ S-114, S-116 | ✓ S-77, S-100 | ✓ two new-patient reports | unknown (stated) | ✓ | ✓ | ✓ | ✓ |
| SOL-004 | ✓ S-10, S-22 | ✓ S-75, S-105 | ✓ | ✓ S-108, S-112 | ✓ S-75, S-102 | ✓ established (indirect) | unknown (stated) | ✓ | ✓ | ✓ | ✓ |
| SOL-003 | ✓ S-10, S-20 | ✓ S-69, S-21 | ✓ | ✓ S-112 | ✓ S-77, S-100 | ✓ established / uncertain | unknown (stated) | ✓ | ✓ | ✓ | ✓ |
| SOL-005 | ✓ S-20, S-13 | ✓ S-21, S-14 | ✓ | ✓ S-112, S-115, S-108 | ✓ S-98, S-82 | n/a (no review basis) | unknown (stated) | ✓ | ✓ | ✓ | ✓ |
| SOL-011 | ✓ S-10, S-13, S-17 | ✓ S-12 (company-wide), S-16, S-86 | ✓ | ✓ S-118 | ✓ S-12, S-16, S-86 | ✓ post-visit billing | unknown (stated) | ✓ | ✓ | ✓ | ✓ |
| SOL-006 | ✓ S-10, S-20, S-22 | ✓ S-70, S-21, S-105 | ✓ | ✓ S-114 | ✓ S-12, S-95, S-102, S-83 | ✓ established | unknown (stated) | ✓ | ✓ | ✓ | ✓ |

**Repairs made during the first audit:**
- **SOL-004:** its only review evidence is about data carrying through, not typing, so it is labelled indirect.
- **SOL-005:** marked as having no direct review evidence.
- **SOL-011:** its billing reviews are marked post-visit.
- **SOL-001:** Numotion evidence is labelled adjacent ongoing service.

No reviewer names or identifiable health narratives appear in this file. Health narratives are cited only as the review report's paraphrases.

## Revision log

- **2026-10-15, first version** (Claude Code run `2026-10-15-solution-selection-claude-02`): inventory, rubric, shortlist, cards, ledger and blank selection area.
- **2026-10-15, reconciliation pass** (run `2026-10-15-research-reconciliation-claude-03`). **No ID, score, rank or shortlist membership changed, and no selection was made.** Changes:
  - Replaced 71 line-number citations with section citations, so they survive edits to the owner files.
  - Labelled each card's review evidence by patient status, using the new [review report §7](2026-10-15-google-review-sentiment.md#7-patient-status-and-journey-stage-of-the-cited-complaints). This lowered SOL-003's stated problem confidence (some repeated-question reports may be clinical confirmation) and noted that SOL-001's and SOL-006's review support is mostly established patients.
  - Added the AdaCare Jarvis recheck (S-83: New Patient Visit slots shown before personal details) to SOL-006 as a no-prerequisite contrast, to SOL-005's stage note, and to P-05 and P-07.
  - Labelled Numotion's app features as documented capability (S-106) in P-03.
  - Used Innocent's wording for the third patient question ("Who handles the next action?") and listed the five aligned problems and the behaviours to preserve in §1.
  - Added a "job" label (contact capture, scheduling, administrative onboarding, coordination) to each candidate.
  - Renamed rubric criterion I to include effort explicitly (its scores already reflected effort), and added a sensitivity note on the rank-8/9 tie.
  - Added a demonstration condition 6 to SOL-006 (direct booking where configured), proof columns to §5, dependencies to §6, and the adjacent open decisions RQ-44 and RQ-45.
