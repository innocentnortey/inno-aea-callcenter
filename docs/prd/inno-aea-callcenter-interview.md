# PRD interview — inno-aea-callcenter (Meridian AI service agent)

> Skill: `prd-interview` v2.1.0 · Coverage checklist: `system-design-readiness/CHECKLIST.md`
> (inspected 2026-10-20) · Question pack: `ai-agent-app` (every pack question is mapped below)
> This document records the interview. Each answer names the document that owns it; when they
> disagree, the owner wins and this record is corrected. Format:
> `prd-interview/references/interview-document.md`.
> Location: `docs/prd/inno-aea-callcenter-interview.md`, next to the PRD (skill step 1, rule 4; zero-to-hero
> ARTIFACT-MAP §4 allows "where `prd-interview` records it"). Setup run by Claude (Opus 5.5), 2026-10-20.

## Resume here

- **Interview state:** setup done. Four questions are open for Innocent; six facts wait on research.
- **Current stage:** S3 — Workload and data (S1 and S2 have nothing to ask Innocent; every answer was carried).
- **Next batch:** Q-029 (text in *Next batch*). Then, one stage per turn: Q-045 (S6), Q-050 (S7), Q-054 (S8).
- **Blocked on:**
  - SD-1.5 partner deadline: Gauntlet staff (GQ-20). Does not block design: the internal target (Wed 2026-10-21 06:00 CT) is earlier than the Thu 2026-10-22 interview.
  - SD-4.2, SD-5.4, SD-5.6, SD-6.3, SD-7.4 vendor and framework facts: Claude researches them from dated docs before spike SP-1 (Q-033). The Anthropic key's rate-limit tier needs Innocent's console or one probe call's rate-limit headers.
- **PRD approval:** **given by Innocent, 2026-10-20 ("yes i approve"), PRD 0.4 (Stage 4 gate).** Next (S9 Close): `system-design-readiness` reads this document, then the System track (§5 SP-1 → §6 design). The UX track runs in a separate session.
- **Readiness verdict:** **READY** (2026-10-20, `docs/design/readiness-report.md`); ticket ready: no (all DO rows `planned`).
- **Last updated:** 2026-10-20, batch 0 (setup).

## Sources read

| Source | Location | Authority | Revision or date read |
|---|---|---|---|
| Issued briefing: portal page (Part A) and PDF (Part B) | `docs/source/aea-call-center-briefing.md` (S-100, S-101) | ISSUED. What gets graded; outranks everything | Portal Version 1 (10/16/2026); read 2026-10-20 |
| PRD | `docs/prd/inno-aea-callcenter-prd.md` | Owns scope, requirements R-1…R-47, NFRs (§5), architecture outline (§6), approval and the five foundation answers (§10), review log incl. Stage 3 choices (§11) | v0.2 (2026-10-20 19:25 CT, edited through the Stage 3 close); read 2026-10-20 |
| Consolidated handoff direction | `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md` | The project's **decision record** for product decisions: OD-1…OD-6 (§8), round-2/3 decisions (§9), LangGraph needs (§10), status table (§11) | 2026-10-20; read 2026-10-20 |
| Brief audit | `docs/analysis/2026-10-20-brief-audit.md` | Owns traps C-, K-, D-1…D-10, E-, L-, G-; DEC-1…DEC-5; Q-1…Q-4; the problem behind the brief | 2026-10-20; read 2026-10-20 |
| Two-layer framing and metrics tree | `docs/delivery/2026-10-20-angle-and-demo-framing.md` | Owns north star, value metrics V1–V5, health list, targets (signed 2026-10-20) | 2026-10-20; read 2026-10-20 |
| Hard-problem register | `docs/design/hard-problems.md` | Owns HP-1…HP-4 (all chosen), SP-1 (approved), the walk of the system-design questions | 2026-10-20 (Stage 3 gate signed); read 2026-10-20 |
| Worked pairs | `docs/data/worked-pairs.md` | Owns WP-1…WP-8 (uncertain pairs checked by Innocent) | 2026-10-20; read 2026-10-20 |
| Data README (samples, selection matrix) | `docs/data/README.md` | Owns samples S1–S14 and data findings D-11…D-13 | 2026-10-20; read 2026-10-20 |
| Handoff information inventory | `docs/data/handoff-information-inventory.md` | Owns call-driver counts (420 calls), source inventory, handoff matrix | 2026-10-20; read 2026-10-20 (headings, §3.1 and §5.3 via PRD citations) |
| Company and service profile | `docs/analysis/2026-10-20-meridian-company-service-profile.md` | DERIVED research: customer, service journey, UX inputs; not an answer source | 2026-10-20; read 2026-10-20 (headings and PRD trace table) |
| SUBMISSION.md | `SUBMISSION.md` | Owns deliverables D-1…D-7, dates, goal-to-evidence map | 2026-10-20; read 2026-10-20 |
| Project checklist | `PROJECT-CHECKLIST.md` | Owns stage and gates (Stages 1–3 signed 2026-10-20; §4 open) | 2026-10-20; read 2026-10-20 |
| Setup profile | `.claude/reference/setup-profile.md` | Owners, locations, adopted rules, model keys | 2026-10-20; read 2026-10-20 |
| Project rules | `.claude/rules/` (source-authority, verification-evals-observability, system-design-questioning, system-design-conversation, gauntlet-hosting-default, hiring-partner-framing) | Constraints. `verification-evals-observability.md` rule 18 names an LLM-aware trace backend (Langfuse or LangSmith) | Copies dated 2026-10-14 / 2026-10-20; read 2026-10-20 |
| Gauntlet open questions | `Gauntlet AI/open-questions.md` | GQ-20 (partner deadline, unconfirmed); GQ-26 closed (data received) | Read 2026-10-20 |
| Dev log | `Gauntlet AI/devlogs/aea-callcenter/` | Run history; latest entry Stage 3 gate signed | Read 2026-10-20 (latest three files) |

## Artifact map

| Work | Owner document | Location | State |
|---|---|---|---|
| Product requirements | PRD | `docs/prd/inno-aea-callcenter-prd.md` | exists (v0.2; Stage 1 approved, Stage 4 approval pending) |
| Decisions | Consolidated handoff direction §11 (product decisions); PRD §10 (foundation answers); hard-problem register (HP choices) | `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md#11-decision-status`; `docs/prd/inno-aea-callcenter-prd.md#10-approval-granted-by-innocent-2026-10-20-yes-to-all`; `docs/design/hard-problems.md` | exists |
| Open questions | Gauntlet open-questions list (partner/staff facts); audit §8 (partner questions, all answered by Innocent) | `Gauntlet AI/open-questions.md`; `docs/analysis/2026-10-20-brief-audit.md#8-open-questions-for-gauntlet--aea` | exists |
| Design inputs | Readiness report | planned: `docs/design/readiness-report.md` (written by `system-design-readiness` after this interview) | planned |
| Implementation planning | Slice plan, then GitLab issues | planned: `docs/plans/slice-plan.md` (zero-to-hero §7a); GitLab `innocentnortey/inno-aea-callcenter` (not created yet) | planned |
| Coverage audit | `to-tickets` coverage audit | planned: `docs/plans/coverage-audit.md` | planned |

### Design outputs

<!-- Required. The seven outputs every design produces (system-design-readiness/DESIGN-OUTPUTS.md).
Locations follow zero-to-hero ARTIFACT-MAP §6 (default `docs/design/`; Claude drafts, Innocent reviews).
Light mode: one system-design document with named sections, plus the contract folder and the area map. -->

| ID | Output | Owner | Location | Sources | Status | Notes |
|---|---|---|---|---|---|---|
| DO-1 | System design | Innocent | docs/design/system-design.md | SD-1.6, SD-1.7, SD-1.9, SD-2.3, SD-3.1, SD-3.4, SD-6.1, SD-7.2; PRD §5, §10; hard-problems GP walk; Q-029; SP-1 §3–§4 | ready | Drafted 2026-10-21 (Stage 6); SDQ-1…10 and EVQ-1 decided by Innocent |
| DO-2 | Architecture | Innocent | docs/design/system-design.md#Architecture | SD-4.1, SD-4.3, SD-4.4, SD-4.7; PRD §6.1–§6.2; HP-1; consolidated §10; Q-039; SP-1 §4 | ready | Drafted 2026-10-21 (Stage 6); SDQ-1…10 and EVQ-1 decided by Innocent |
| DO-3 | Code design | Innocent | docs/design/code-design.md (mirrored to .claude/reference/area-map.md) | SD-4.3, SD-4.5; HP-1…HP-4; rule code-design-solid-modularity; SP-1 §4 Stage 6 items | ready | Drafted 2026-10-21 (Stage 6); SDQ-1…10 and EVQ-1 decided by Innocent |
| DO-4 | Component contracts | Innocent | docs/design/contracts/ (starts from the draft CON-1…CON-20 in docs/ux/01-planning/USER_FLOWS.md) | SD-4.2, SD-4.5, SD-5.5, SD-6.2, SD-6.3; R-15, R-19, R-25, R-28, R-29; Q-033; SP-1 §4 | ready | Drafted 2026-10-21; metz review PASS (DO-3/DO-4); DO-4 agrees with UX-3 on 18/21 CONs, CON-7/9/10 follow UXR-27 (carried to §7 by Innocent's decision) |
| DO-5 | Evaluation plan | Innocent | docs/design/evaluation-plan.md | SD-8.1, SD-8.8, SD-8.9, SD-2.7; R-12, R-38, R-39; framing §2; WP-1…WP-8; Q-052, Q-054; SP-1 §2–§3 | ready | Drafted 2026-10-21 (Stage 6); SDQ-1…10 and EVQ-1 decided by Innocent |
| DO-6 | Observability contract | Innocent | docs/design/observability-contract.md | SD-1.10, SD-2.8, SD-3.7, SD-4.7, SD-6.6, SD-7.6, SD-8.4, SD-8.7; R-29, R-35, R-36; Q-010, Q-030, Q-045, Q-050, Q-062 | ready | Drafted 2026-10-21 (Stage 6); SDQ-1…10 and EVQ-1 decided by Innocent |
| DO-7 | Key-metrics registry | Innocent | docs/design/key-metrics-registry.md | SD-2.9, SD-2.8, SD-2.7; framing §2 (north star, V1–V5, health list); R-39; PRD §5 | ready | Drafted 2026-10-21 (Stage 6); SDQ-1…10 and EVQ-1 decided by Innocent |

## Stage map

| Stage | Topics | Checklist items | Depends on | Depth | State |
|---|---|---|---|---|---|
| S1 Frame | Users, what is judged, non-goals, stack, deadline, spend, economics, data limits, telemetry policy, hardest uncertainty | SD-1.1 – SD-1.10 | — | full | prepared — nothing to ask Innocent; SD-1.5 waits on GQ-20 (staff) |
| S2 Requirements and promises | Key operations, invariants, latency, freshness, availability, recovery, AI quality metrics, operational success vs correctness, key metrics | SD-2.1 – SD-2.9 | S1 | full | done — every item carried |
| S3 Workload and data | Load and peak (decided), scale path, request mix, background work, sizes, every workflow and entry point | SD-3.1 – SD-3.7 | S1, S2 | light (100/day, 20 at once: one instance, no queue) | active — Q-029 |
| S4 Flow and dependencies | Data authority, external dependencies, model decision points, run stages and run ID, half-success | SD-4.1 – SD-4.7 | S2 | full (HP-1 decided) | prepared — SD-4.2 research only (Q-033) |
| S5 Resources and cost | CPU, DB and model work per turn; model prices and limits; runtime concurrency | SD-5.1 – SD-5.6, SD-7.4 | S3, S4 | light (spike SP-1 measures it) | prepared — research only (Q-033); measurements via SP-1 (Q-040) |
| S6 Failure, overload and security | Overload, timeouts and retries, dependency failures, stale data, security, failure and recovery signals | SD-6.1 – SD-6.6 | S4 | full (safety-critical) | prepared — Q-045 |
| S7 Deployment and operations | Railway, failure to survive, capacity per replica, what one person operates, where telemetry lives | SD-7.1 – SD-7.3, SD-7.5, SD-7.6 | S1, S5 | light | prepared — Q-050 |
| S8 Validation and evidence | Ground truth, test data, held-out separation, load test, traces, redesign triggers | SD-8.1 – SD-8.9 | S2, S6 | full (SD-1.9: every number honest) | prepared — Q-054 |
| S9 Close | Stage 4 PRD approval, register check, `system-design-readiness`, handoff to the System track | — | S1–S8 | — | provisional |

**Depth basis.** SD-1.9 (Innocent, 2026-10-20, PRD §10 item 4): the hardest thing to prove is "that every number we report is
honest". That puts full depth on S2 and S8. Load is small and decided (SD-3.1, SD-3.4), so S3, S5 and S7 are light.

## Next batch

**Stage S3 — Workload and data.** Carried answers to review (accept in a word or reopen one):
- Q-027 Load: "about 100 per day" interacting with the agent [T] (PRD §10, SD-3.1).
- Q-028 Peak: "a 20-user spike", about 20 conversations at once [T] (PRD §10, SD-3.4).
- Q-030 Workflows: the full list of entry points, compiled from decided requirements (see Q-030).
- Q-031 Background work: the overdue/due-soon job on the fixed clock, ingestion and index build at deploy (consolidated §10; PRD §6.2).
- Assumed until measured: turns per conversation, model calls per turn and the topic mix (SD-3.2, SD-3.3; plan: SP-1 and the first eval run).

1. **Q-029 — Which larger load should the design write a path for?** (text in the question block)

**Later batches, one stage per turn:** S6 Q-045 (where alerts go) → S7 Q-050 (where traces live) → S8 Q-054 (dev versus
held-out cases). Each block below carries its story, options and recommendation.

## Questions

### Q-001 — Users and what a useful result is
- Stage: S1
- Layer: product
- Purpose: Fixes who the system serves and what success looks like for each.
- Sources: SD-1.1; pack:ai-agent-app/domain; pack:ai-agent-app/use-cases-functional
- Depends on: —
- Status: carried
- Evidence: Brief Part A §PRD and Part B §Overview ("resolve the majority of routine inbound calls … gracefully escalating"); PRD §2 users table (homeowner, representative, supervisor, business owner, reviewer); OD-1 (consolidated §8)
- Answer: Homeowners get a routine thing done or know exactly what happens next; staff pick up handoffs without re-asking; supervisors see urgent, unowned and overdue work; the owner sees outcomes; the reviewer can probe and watch escalation.
- Decision: OD-1
- Affects: PRD §2
- History:
  - 2026-10-20 setup — carried from PRD §2 and the brief

### Q-002 — What the project must prove and how it is judged
- Stage: S1
- Layer: product
- Purpose: Sets the bar every design choice is judged against.
- Sources: SD-1.2
- Depends on: —
- Status: carried
- Evidence: Brief Part B §What we are looking for (judgment on scope, honesty about data, evidence-backed confidence, production thinking, clean failure) and §Deliverables; Part A §Required Deliverables; audit C-1 (satisfy both lists); `SUBMISSION.md` D-1…D-7
- Answer: Deployed URL, 3–4 minute design-reasoning video, source repo with eval set and README; plus technical docs, deployment guide and test results.
- Decision: audit C-1
- Affects: `SUBMISSION.md`; PRD R-43
- History:
  - 2026-10-20 setup — carried

### Q-003 — What is ruled out
- Stage: S1
- Layer: product
- Purpose: Keeps the design from building what scope excludes.
- Sources: SD-1.3
- Depends on: —
- Status: carried
- Evidence: PRD §7 (voice DEC-5, real SMS/email, payments, multi-tenant staff accounts, real staffing, emergency dispatch, commercial work, fee waivers DEC-2, edits to issued data); source-authority rule 1
- Answer: As PRD §7.
- Decision: DEC-2, DEC-5
- Affects: PRD §7
- History:
  - 2026-10-20 setup — carried

### Q-004 — Required stack and integrations
- Stage: S1
- Layer: design-input
- Purpose: Fixes the building blocks the design must use.
- Sources: SD-1.4; pack:ai-agent-app/agent-framework; pack:ai-agent-app/data-sources
- Depends on: —
- Status: carried
- Evidence: Brief Part A §Technology (RAG with embeddings and vector retrieval; mock scheduling DB with availability check and booking write; observability tooling); LangGraph decided (consolidated §10, §11); FastAPI, SQLite working copy, in-process vector index (PRD §6.2); Railway own project (PRD R-40); local embeddings `BAAI/bge-small-en-v1.5` (PRD R-11)
- Answer: Python, LangGraph two-layer agent, FastAPI server-rendered pages, SQLite working copy plus case-store tables, in-process vector index, paid Claude models, Railway.
- Decision: LangGraph (consolidated §11); HP-1
- Affects: PRD §6.2
- History:
  - 2026-10-20 setup — carried

### Q-005 — Partner submission deadline
- Stage: S1
- Layer: design-input
- Purpose: Confirms the time box the design must fit.
- Sources: SD-1.5
- Depends on: —
- Status: deferred
- Evidence: Brief Part A "Time Constraints: 2-3 days"; `SUBMISSION.md` §Dates (partner deadline unknown; interview Thu 2026-10-22; internal target Wed 2026-10-21 06:00 CT); `Gauntlet AI/open-questions.md` GQ-20 (open)
- Answer: —
- Decision: Deferred to Gauntlet staff through GQ-20. The internal target (Innocent, 2026-10-20) is earlier than the interview, so design proceeds on it.
- Affects: `SUBMISSION.md` §Dates when staff answer
- History:
  - 2026-10-20 setup — deferred to GQ-20 (needs-research; not Innocent's to answer)

### Q-006 — Spending ceiling
- Stage: S1
- Layer: design-input
- Purpose: Bounds model spend and hosting.
- Sources: SD-1.6
- Depends on: —
- Status: carried
- Evidence: PRD §10 item 4 SD-1.6 (Innocent, 2026-10-20): Railway on the existing plan; model spend capped at $10/day, re-checked against ~100 conversations/day once cost is measured; PRD R-41 (cap falls back to handoff)
- Answer: $10/day model cap; Railway $0 incremental on the existing plan.
- Decision: PRD §10 SD-1.6
- Affects: PRD §5, R-41
- History:
  - 2026-10-20 setup — carried

### Q-007 — Economics of one successful outcome
- Stage: S1
- Layer: design-input
- Purpose: Sets the cost budget per resolved conversation.
- Sources: SD-1.7
- Depends on: Q-006
- Status: carried
- Evidence: Framing §1 (each correct resolution saves about 111 s of staff talk time [M], median call); hard-problems GP-107 (about $0.10 per conversation [C] = $10/day ÷ ~100/day)
- Answer: ~111 s of staff time saved per correct resolution; spend budget ~$0.10 per conversation; accuracy is not cut for cost.
- Decision: framing §1; hard-problems GP-107
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-008 — Data-handling limits
- Stage: S1
- Layer: design-input
- Purpose: Fixes what data may be used and kept.
- Sources: SD-1.8; pack:ai-agent-app/audit
- Depends on: —
- Status: carried
- Evidence: source-authority rules 1 and 8 (fictional company; no real personal data); `docs/data/README.md` ("All data is Meridian's issued, fictional data"); D6 (consolidated §9.6: snapshots and history deleted 90 days after case close in production; demo resets); R-15 (code hashed, never logged)
- Answer: Issued fictional data and labelled synthetic cases only; production retention 90 days after case close; demo resets.
- Decision: D6
- Affects: PRD §5 Privacy
- History:
  - 2026-10-20 setup — carried

### Q-009 — The hardest uncertainty
- Stage: S1
- Layer: design-input
- Purpose: Sets the depth of every later stage.
- Sources: SD-1.9
- Depends on: —
- Status: carried
- Evidence: PRD §10 item 4 SD-1.9 (Innocent, 2026-10-20)
- Answer: "That every number we report is honest: correct answers, correct escalations, no stale-document answers."
- Decision: PRD §10 SD-1.9
- Affects: Stage map depth
- History:
  - 2026-10-20 setup — carried

### Q-010 — What logs and traces may hold
- Stage: S1
- Layer: design-input
- Thread: observability
- Purpose: The telemetry policy every record and export must obey.
- Sources: SD-1.10; SD-1.8
- Depends on: —
- Status: carried
- Evidence: PRD R-36 (traces and logs redacted: no codes, no card-like numbers, minimal PII); R-15 (code hashed, never in model context, logs or traces); D6 (full chat history in staff and monitoring views, role-limited, card-like numbers masked; 90-day retention after close); audit G-9 and project rule `verification-evals-observability.md` 19 (redact before export)
- Answer: Never: verification codes, card-like numbers. Redacted before any export. Readable by staff roles only. Kept 90 days after a case closes (production), reset in the demo. What actually leaves the environment depends on Q-050.
- Decision: R-36, D6
- Affects: DO-6 Content and redaction
- History:
  - 2026-10-20 setup — carried

### Q-011 — Audience, reading level and tone
- Stage: S1
- Layer: product
- Purpose: Fixes how replies and briefs are written.
- Sources: pack:ai-agent-app/audience-tone
- Depends on: —
- Status: carried
- Evidence: PRD R-1 (says it is an automated assistant), R-4 (plain, short, exact numbers, sources shown), R-28 (about grade-5 wording in briefs); PRD §5 Accessibility (WCAG 2.2 AA); company profile §6–§7
- Answer: Plain, short, exact numbers; honest about being automated; WCAG 2.2 AA.
- Decision: PRD R-1, R-4
- Affects: PRD §4.1, §5
- History:
  - 2026-10-20 setup — carried

### Q-012 — Motion profile of the UI
- Stage: S1
- Layer: design
- Purpose: How much animation the interface uses.
- Sources: pack:ai-agent-app/motion-profile
- Depends on: —
- Status: deferred
- Evidence: Brand direction A "dependable dispatch" (company profile §8; PRD §6.2)
- Answer: —
- Decision: Deferred to the UX track (ux-pipeline UX-3 `docs/design/design.md`); a product profile follows from direction A.
- Affects: UX-3 design doc
- History:
  - 2026-10-20 setup — deferred (UI detail, not a product input)

### Q-013 — The operations that matter most
- Stage: S2
- Layer: product
- Purpose: The operations every promise, metric and trace is defined for.
- Sources: SD-2.1; pack:ai-agent-app/use-cases-functional
- Depends on: Q-001
- Status: carried
- Evidence: PRD §3.2 (scheduling; RAG drivers membership, billing questions, warranty) and §4; hard-problems "where each problem sits"
- Answer: (1) safety check and instruction; (2) knowledge answer from current KB; (3) verified account read; (4) availability check and booking; (5) handoff with case, brief and promise; (6) staff takeover.
- Decision: PRD §3.2 (Stage 1 approval)
- Affects: PRD §3–§4
- History:
  - 2026-10-20 setup — carried

### Q-014 — What must never happen
- Stage: S2
- Layer: design-input
- Purpose: The invariants the design proves in code, not prompts.
- Sources: SD-2.2; pack:ai-agent-app/reliability
- Depends on: Q-013
- Status: carried
- Evidence: Framing §2 hard gates (V2 100% valid writes, 0 double bookings; V3 promise text matches policy 100%; V4 safety first 100%, person on first ask 100%; V1 0 answers from excluded files); PRD R-5, R-13, R-15, R-19, R-21 (0 fee-bearing moves), R-46 (0 completion claims without a write; 0 invented facts)
- Answer: As the hard gates listed.
- Decision: framing §2 (signed 2026-10-20); HP-3, HP-4
- Affects: DO-5 acceptance conditions
- History:
  - 2026-10-20 setup — carried

### Q-015 — Latency target
- Stage: S2
- Layer: design-input
- Purpose: The percentile the design sizes against.
- Sources: SD-2.3; pack:ai-agent-app/scale
- Depends on: Q-027, Q-028
- Status: carried
- Evidence: PRD §5 (p95 ≤ 8 s per turn at the 20-conversation spike); framing §2 health list (signed 2026-10-20); hard-problems SP-1 (calls it one of Innocent's numbers, measured at Stage 5)
- Answer: p95 ≤ 8 s per turn at about 20 conversations at once; tuned after SP-1.
- Decision: framing §2; PRD §5
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried (PRD labels it [A], hard-problems calls it a target: label mismatch queued in the batch log)

### Q-016 — Where per-turn timing starts and stops
- Stage: S2
- Layer: design
- Thread: observability
- Purpose: Makes the 8 s target measurable the same way every time.
- Sources: SD-2.3; SD-4.7
- Depends on: Q-015
- Status: deferred
- Evidence: hard-problems GP-110 ("Where each latency measurement starts and stops is Stage 6")
- Answer: —
- Decision: Deferred to DO-1 (traced request) and DO-6 (timed boundaries).
- Affects: DO-1, DO-6
- History:
  - 2026-10-20 setup — deferred

### Q-017 — How fresh data must be
- Stage: S2
- Layer: design-input
- Purpose: Says which facts must be re-read before use.
- Sources: SD-2.4
- Depends on: —
- Status: carried
- Evidence: PRD R-45 (slot availability re-read before any write; code expiry checked); R-29 (snapshot plus current value with a "changed since" marker); R-11 (index rebuilt from the manifest); hard-problems GP-116 (KB answers carry the document's version date)
- Answer: As cited.
- Decision: R-45 (HP-1 choice)
- Affects: DO-2
- History:
  - 2026-10-20 setup — carried

### Q-018 — What keeps working when a dependency is down
- Stage: S2
- Layer: design-input
- Purpose: Availability per operation.
- Sources: SD-2.5; pack:ai-agent-app/failure-modes
- Depends on: Q-013
- Status: carried
- Evidence: PRD §5 Reliability ("Every model or tool failure ends in a handoff with context"); R-47 (if the classifier fails, the word rules stand); hard-problems GP-114 (safety never waits: code, no model; spend cap → handoff)
- Answer: Safety and the person-request path never depend on a model; everything else degrades to a handoff.
- Decision: PRD §5; R-47
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-019 — Recovery: data loss and time to recover
- Stage: S2
- Layer: design-input
- Purpose: RPO and RTO.
- Sources: SD-2.6
- Depends on: Q-048
- Status: carried
- Evidence: PRD §10 SD-7.2 (survive a process restart without losing conversations or cases; SQLite on a Railway volume; durable checkpointer; not a zone outage); R-19 (one-command reset of the working copy)
- Answer: No committed conversation or case is lost on a restart; a lost volume or zone is not survived; recovery time is Railway's restart, with no separate target (light depth).
- Decision: PRD §10 SD-7.2
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-020 — Quality metrics for model output
- Stage: S2
- Layer: design-input
- Thread: observability
- Purpose: Says how "was it right" is measured, with targets.
- Sources: SD-2.7; pack:ai-agent-app/eval-approach
- Depends on: Q-013
- Status: carried
- Evidence: Framing §2 V1 (retrieval current-document hit ≥ 90%; wrong answers ≤ 5%), V5 (escalation recall ≥ 95%; false escalation ≤ 10%), V4 addition (danger recall 100%; false alarms ≤ 10%); PRD R-28 (brief recall ≥ 90%; 0 invented facts); baselines "none yet" (framing §2)
- Answer: As cited; signed 2026-10-20.
- Decision: framing §2; R-47
- Affects: DO-5, DO-7
- History:
  - 2026-10-20 setup — carried

### Q-021 — "Did it run" kept apart from "was it right"
- Stage: S2
- Layer: design-input
- Thread: observability
- Purpose: Operational success has its own signal.
- Sources: SD-2.8
- Depends on: Q-013
- Status: carried
- Evidence: Framing §2 health list (volume, latency, tool and model failure rate, spend, unowned and overdue cases) "reported separately … 'It's up' never stands in for 'it's right'"; PRD R-35 ("Health shown separately from correctness"); PRD §5 (a failure becomes a handoff)
- Answer: Health and correctness are separate groups; a run that fails or hits a brake ends in a handoff and is counted as a health event, never as a resolution.
- Decision: framing §2
- Affects: DO-6, DO-7
- History:
  - 2026-10-20 setup — carried

### Q-022 — Operational outcome values per operation
- Stage: S2
- Layer: design
- Thread: observability
- Purpose: The exact status values a turn and a run record (completed, degraded to handoff, timed out, failed).
- Sources: SD-2.8
- Depends on: Q-021
- Status: deferred
- Evidence: Policy settled in Q-021
- Answer: —
- Decision: Deferred to DO-6 (record fields).
- Affects: DO-6
- History:
  - 2026-10-20 setup — deferred

### Q-023 — Key metrics and the decisions they inform
- Stage: S2
- Layer: design-input
- Purpose: Which numbers drive which decisions, over what population.
- Sources: SD-2.9
- Depends on: Q-020, Q-021
- Status: carried
- Evidence: Framing §2: north star in-scope correct resolution (100% aim, ≥ 90% bar per topic), scope coverage and containment reported beside it, V1–V5 each with unit, denominator, decision line; health list with decision lines (signed 2026-10-20)
- Answer: As the framing doc.
- Decision: framing §2
- Affects: DO-7
- History:
  - 2026-10-20 setup — carried

### Q-024 — When a chat counts as ended or abandoned
- Stage: S2
- Layer: design
- Purpose: Abandonment (V4) needs an end point; a web chat has no hang-up.
- Sources: SD-2.9
- Depends on: Q-023
- Status: deferred
- Evidence: Framing §2 V4 ("conversations that ended with neither resolution nor handoff")
- Answer: —
- Decision: Deferred to DO-7 (formula and population).
- Affects: DO-7
- History:
  - 2026-10-20 setup — deferred

### Q-025 — Acceptance criteria per capability
- Stage: S2
- Layer: product
- Purpose: Each requirement has a testable check.
- Sources: pack:ai-agent-app/acceptance
- Depends on: Q-013
- Status: carried
- Evidence: PRD §4 acceptance column for R-1…R-47
- Answer: As the PRD.
- Decision: PRD §4
- Affects: PRD §4
- History:
  - 2026-10-20 setup — carried

### Q-026 — Where a human is in the loop
- Stage: S2
- Layer: product
- Purpose: Which decisions only people make.
- Sources: pack:ai-agent-app/human-in-loop
- Depends on: —
- Status: carried
- Evidence: OD-1…OD-6 (consolidated §8); D3/DEC-2 and HP-3 (fee-bearing changes go to staff); D4 table (§9.4); PRD R-24, R-31
- Answer: Disputes, refunds, complaints, fee-bearing changes, unsupported actions and any direct request go to a person; a person can take over the same chat.
- Decision: OD-1…OD-6; D4
- Affects: PRD §4.6
- History:
  - 2026-10-20 setup — carried

### Q-027 — Load it is built for
- Stage: S3
- Layer: design-input
- Purpose: The daily volume the design sizes against.
- Sources: SD-3.1
- Depends on: —
- Status: carried
- Evidence: PRD §10 SD-3.1 (Innocent, 2026-10-20): "about 100 per day" interacting with the agent, Meridian treated as a big company for its region [T]; PRD §5
- Answer: About 100 agent conversations per day.
- Decision: PRD §10 SD-3.1
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-028 — Peak at the same moment
- Stage: S3
- Layer: design-input
- Purpose: Concurrency the single instance must hold.
- Sources: SD-3.4
- Depends on: Q-027
- Status: carried
- Evidence: PRD §10 SD-3.4 (Innocent, 2026-10-20): "a 20-user spike" [T]; PRD §5 design consequences [C]
- Answer: About 20 conversations at once.
- Decision: PRD §10 SD-3.4
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-029 — Which larger load should the design write a path for?
- Stage: S3
- Layer: design-input
- Purpose: Decides whether DO-1 carries a written scale path, and to what size. `system-design-questioning.md` asks this as the second half of SD-3.1 ("what larger load needs a written path?"); it was not asked with the load question.
- Sources: SD-3.1; project
- Depends on: Q-027, Q-028
- Status: answered
- Evidence: batch 1, 2026-10-20 (Innocent: "A")
- Answer: A. A written path to 10× (about 1,000 conversations a day, about 200 at once); nothing built
- Proposed default: none (a foundation-type question; no default)
- Decision: PRD §10 table (SD-3.1, scale path) and §5 load bullet
- Affects: PRD §5 (load), DO-1 scale-path section
- History:
  - 2026-10-20 setup — drafted
  - 2026-10-20 batch 1 — answered A (Innocent)

**The story.** You set the build load: about 100 conversations a day with a spike of about 20 at once. At that size the
design is one service, one SQLite file and no queue (hard-problems GP-108). The questioning rule also asks what larger
load needs a *written* path. That is the YourAI lesson: you reopened "built for 50 users … how we would scale it to 1000"
yourself. AEA's story is "expand coverage without adding headcount" across a portfolio, so "what happens at 10×?" is a
likely interview probe. A written path changes nothing we build tonight. It is one DO-1 section saying what breaks first
and what we would change.

- **A. A written path to 10× (about 1,000 conversations a day, about 200 at once). Recommended.** DO-1 names what breaks
  first (the model provider's rate limits, then SQLite's single writer on one volume, then one process) and the change
  for each (a higher provider tier, Postgres, several instances sharing the checkpointer). Nothing is built. About 30
  minutes of writing. Gain: a ready answer to the scale probe. Cost: that half hour.
- **B. No written path.** The README says the design is sized for 100 a day and 20 at once, and anything bigger is a
  redesign. No time spent; the scale question gets answered live, without a written basis.
- **C. A portfolio path (several companies on one system).** Adds tenancy, per-company knowledge bases and data
  separation the brief never asks for. More speculative and more time; it invents requirements.

*Recommended: A.* It is cheap, and it is the question a PE reviewer is most likely to ask after "is the number real?".

**Decision needed:** Should the design include a written scale path, and to what size: 10× (A), none (B) or portfolio (C)?

### Q-030 — Every workflow and entry point
- Stage: S3
- Layer: design-input
- Thread: observability
- Purpose: Each must be covered by the observability contract and the evaluation plan, or excluded with a reason.
- Sources: SD-3.7
- Depends on: Q-013
- Status: carried
- Evidence: Compiled from decided requirements. User operations: customer chat turn (R-1…R-47), talk-to-a-person (R-2), code entry (R-15), demo delivery inbox (R-15), staff console claim/reply/hand-back/close/flag/assign (R-31…R-33, R-37), simulated staffing toggle (R-30), simulated clock control (R-33), monitoring page and owner panel (R-35, R-32). Background: due-soon/overdue job on the fixed clock (consolidated §10). Validation: retrieval eval (R-12), end-to-end eval run (R-38, R-39). Development experiments: SP-1 (hard-problems *Spikes*), Stage 9 error-analysis and XP runs (checklist §9). Runtime operations: deploy (R-40), KB ingestion and index build (R-9, R-11), working-copy reset (R-19), case-store table creation and demo seed load (R-25, R-33)
- Answer: All of these are covered; none is excluded. The WF-n registry is written in DO-6.
- Decision: Follows from the requirements cited; any exclusion would be a new question.
- Affects: DO-6 Covered workflows; DO-5
- History:
  - 2026-10-20 setup — carried (list compiled from decided requirements)

### Q-031 — Work that runs without users
- Stage: S3
- Layer: design-input
- Purpose: Background load and its size.
- Sources: SD-3.5
- Depends on: —
- Status: carried
- Evidence: Consolidated §10 ("Due-soon and overdue alerts come from a scheduled job on the fixed clock"); PRD §6.2 and hard-problems GP-111 (ingestion at deploy; 17 KB files)
- Answer: One small scheduled job and a deploy-time ingestion; both tiny at this size.
- Decision: consolidated §10
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-032 — Who owns each record
- Stage: S4
- Layer: design-input
- Purpose: Data authority.
- Sources: SD-4.1
- Depends on: —
- Status: carried
- Evidence: Issued DB read-only, writes to the working copy (PRD R-19; source-authority; Q-2 reviewer uses our copy); case store new tables (R-25; consolidated §9.7); current KB files are the answer authority (R-10, DEC-4); vector index is a derived copy (hard-problems GP-117); presence state lives in the application (consolidated §10)
- Answer: As cited.
- Decision: Q-2, DEC-4, case store (consolidated §11)
- Affects: DO-2
- History:
  - 2026-10-20 setup — carried

### Q-033 — Vendor and framework facts (research)
- Stage: S4
- Layer: design-input
- Purpose: The external facts DO-4 and SP-1 need: model API auth, schemas, error and rate-limit responses, prices, context limits, the key's tier; LangGraph and FastAPI concurrency behaviour at the pinned versions; Railway volume pricing.
- Sources: SD-4.2; SD-5.4; SD-5.6; SD-6.3; SD-7.4
- Depends on: —
- Status: answered
- Evidence: Not in any project source. Railway plan facts exist (`gauntlet-hosting-default.md`, read 2026-10-10) but not volume pricing or model prices
- Answer: researched 2026-10-20: `docs/research/2026-10-20-vendor-and-framework-facts.md`; sources S-187…S-226 in the source register
- Decision: Deferred to Claude's research before SP-1 (Stage 5): provider pricing, rate-limit and error docs (dated), the key's tier from one probe call's rate-limit headers or Innocent's console, LangGraph/FastAPI docs for the pinned versions. Not a question for Innocent. Added at batch 3: Langfuse self-hosting requirements (services it needs, version) and their Railway cost and setup time, from dated docs.
- Affects: DO-4; SP-1 brief; readiness report
- History:
  - 2026-10-20 setup — deferred (needs-research)
  - 2026-10-20 batch 7 — researched (subagent), recorded

### Q-034 — Where a model decides
- Stage: S4
- Layer: design-input
- Purpose: Every model decision point and why code would not do.
- Sources: SD-4.3
- Depends on: —
- Status: carried
- Evidence: PRD §6.1 (planner: just talk or act, ordered task list; specialists: tool choice; responder: wording, no tools; code gates and escalation check in code); R-47 (raise-only classifier, label only picks a fixed path); R-28 (three brief headings by constrained extraction); HP-1, HP-2 choices
- Answer: As cited.
- Decision: HP-1, HP-2
- Affects: DO-2
- History:
  - 2026-10-20 setup — carried

### Q-035 — During, before and after a request
- Stage: S4
- Layer: design-input
- Purpose: What runs in the turn and what runs outside it.
- Sources: SD-4.4
- Depends on: —
- Status: carried
- Evidence: Before: ingestion and index build (R-9, R-11). During: gates → planner → specialists → escalation check → responder (PRD §6.1). After: case due/overdue job (consolidated §10); follow-up recorded, never sent (R-34); evals offline (R-39)
- Answer: As cited.
- Decision: PRD §6.1
- Affects: DO-1, DO-2
- History:
  - 2026-10-20 setup — carried

### Q-036 — When a multi-step operation half succeeds
- Stage: S4
- Layer: design-input
- Purpose: Partial-failure policy.
- Sources: SD-4.5
- Depends on: —
- Status: carried
- Evidence: R-19 (check and slot update in one transaction; idempotent retries; no double booking); consolidated §10 (handoff node creates the case idempotently); R-46 (no completion claim without a successful write); PRD §5 (failure ends in a handoff)
- Answer: As cited.
- Decision: R-19, R-46
- Affects: DO-4
- History:
  - 2026-10-20 setup — carried

### Q-037 — Run stages and the run ID
- Stage: S4
- Layer: design-input
- Thread: observability
- Purpose: What one run passes through and how it is linked end to end.
- Sources: SD-4.7
- Depends on: Q-034
- Status: carried
- Evidence: PRD §6.1 stages; consolidated §10 (one durable thread per conversation keyed by `thread_id`); R-29 (lookup-log row per tool call with the message that used it)
- Answer: Conversation = `thread_id`; each turn and tool call linked to it. Which boundaries are timed is Q-016.
- Decision: PRD §6.1; consolidated §10
- Affects: DO-6 Correlation across boundaries
- History:
  - 2026-10-20 setup — carried

### Q-038 — Tools the agent needs
- Stage: S4
- Layer: design-input
- Purpose: The tool set and its guards.
- Sources: pack:ai-agent-app/tools
- Depends on: Q-034
- Status: carried
- Evidence: PRD §6.1 specialists (knowledge R-9…R-13; account R-15…R-17; scheduling R-18…R-23); consolidated §10 (identity checked in code in the tool guard; no waiver tool; the scheduling tool refuses a change inside 24 hours)
- Answer: As cited; per-tool error handling ends in a handoff.
- Decision: HP-1, HP-3
- Affects: DO-4
- History:
  - 2026-10-20 setup — carried

### Q-039 — Handoff lanes
- Stage: S4
- Layer: design
- Purpose: How handoffs are routed between lanes.
- Sources: project
- Depends on: —
- Status: deferred
- Evidence: Consolidated §9.7 and §11 ("Handoff lanes: delegated to Claude; decide after Stage 2")
- Answer: —
- Decision: Deferred to DO-2 (delegated to Claude by Innocent).
- Affects: DO-2
- History:
  - 2026-10-20 setup — deferred

### Q-040 — Model mix, calls, tokens and cost per turn
- Stage: S5
- Layer: design-input
- Purpose: The measurements that confirm the 8 s and $10/day numbers.
- Sources: SD-5.1; SD-5.2; SD-5.3; pack:ai-agent-app/llm-selection
- Depends on: Q-033
- Status: answered
- Evidence: Hard-problems *Spikes* SP-1 (approved by Innocent, 2026-10-20): two model mixes over WP-1…WP-8; pick the cheapest mix that keeps outputs correct, under 8 s p95 and $0.10 per conversation; otherwise bring the trade-off to Innocent. PRD §6.2 ("a paid Claude model … and a smaller one … confirmed at design")
- Answer: Innocent, 2026-10-20 (raised by him; it had not been asked): **every model role defaults to Claude Sonnet 5.5 for now.** SP-1 experiments across Sonnet 5.5, GPT-5.6 Terra, Gemini Flash and Jev, TypeSafe AI's typed-classification model, for routing and classification (identified by a web search 2026-10-20; sourced in the research note), to see whether a mix beats Sonnet-everywhere on correctness, the 8 s p95 and $0.10 per conversation. The measurements themselves stay with SP-1
- Decision: PRD §6.2 *Models* and §10 table; hard-problems SP-1 candidate list. Measurements deferred to SP-1 (Stage 5). If no mix fits, it returns to Innocent as a new question (system-design-questioning rule 8).
- Affects: DO-1; PRD §5
- History:
  - 2026-10-20 setup — deferred to SP-1
  - 2026-10-20 batch 6 — model direction given by Innocent: Sonnet default; SP-1 candidates Sonnet, Terra, Gemini Flash, Jev (TypeSafe AI, routing)

### Q-041 — Behaviour under overload
- Stage: S6
- Layer: design-input
- Purpose: Wait, degrade, throttle or fail per operation.
- Sources: SD-6.1
- Depends on: —
- Status: carried
- Evidence: Hard-problems GP-114 (safety never waits; model calls wait to a deadline, then hand off; spend cap → hand off; booking writes serialize); PRD R-41 (rate limits per session and IP, booking cap, loop brakes)
- Answer: As cited.
- Decision: hard-problems GP-114 (Stage 3 gate signed); R-41
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-042 — Timeouts, retries and safe repeats
- Stage: S6
- Layer: design-input
- Purpose: Retry policy per dependency.
- Sources: SD-6.2
- Depends on: Q-041
- Status: carried
- Evidence: R-19 (idempotent retries); consolidated §10 (idempotent case creation; explicit recursion, iteration, time and spend brakes); GP-114 (wait to a deadline, then hand off)
- Answer: Writes are idempotent; model calls get a deadline inside the 8 s budget, then hand off. Exact values are design (DO-1, DO-4).
- Decision: R-19; consolidated §10
- Affects: DO-1, DO-4
- History:
  - 2026-10-20 setup — carried (values deferred)

### Q-043 — Stale or unreachable data
- Stage: S6
- Layer: design-input
- Purpose: Serve labelled, or refuse.
- Sources: SD-6.4
- Depends on: Q-017
- Status: carried
- Evidence: R-45 (re-read slots before a write); R-29 ("changed since" marker); GP-116 (bookings, identity and promises refuse rather than guess)
- Answer: As cited.
- Decision: R-45
- Affects: DO-2
- History:
  - 2026-10-20 setup — carried

### Q-044 — Security and privacy failures
- Stage: S6
- Layer: design-input
- Purpose: Injection, account fishing, abuse, secrets.
- Sources: pack:ai-agent-app/security
- Depends on: —
- Status: carried
- Evidence: R-15, R-16 (code to the contact on record; no-match reveals nothing); R-41 (rate and spend limits); R-10 (internal notes never quoted); audit G-2, G-3, G-10; R-40 (secrets in Railway variables)
- Answer: As cited.
- Decision: OD-3; audit G-2
- Affects: DO-4, DO-6
- History:
  - 2026-10-20 setup — carried

### Q-045 — Where operator alerts go when something breaks
- Stage: S6
- Layer: design-input
- Thread: observability
- Purpose: Decides who notices a failure when nobody is looking at the monitoring page.
- Sources: SD-6.6; SD-7.6
- Depends on: Q-021
- Status: answered
- Evidence: batch 2, 2026-10-20 (Innocent: "A")
- Answer: A. Alerts stay on the monitoring page, plus a health check that restarts the service; no push channel tonight (roadmap)
- Decision: PRD R-35 and §10 table
- Affects: PRD R-35 (and the §8 cut order if it is cut); DO-6
- History:
  - 2026-10-20 setup — drafted
  - 2026-10-20 batch 2 — answered A (Innocent)

**The story.** The brief asks "Could this run for a month without you? Would the business know if it broke?" (Part B).
What is decided: a monitoring page with alert lines (R-35): failure rate above 2%, the spend cap reached, zero traffic
in an expected window, overdue cases (framing health list). What is not decided: whether any of those alerts leaves the
page. The audit's own warning is "A dashboard nobody watches doesn't count" (G-5). Staff notifications about cases are
already "later product" (consolidated §8); this question is only about the operator learning that the system is down,
failing or out of budget.

- **A. Page only, plus a health check that restarts the service.** No extra work. Nobody is told; the operator finds out
  on the next visit to the page.
- **B. Page, plus a push of the hard alerts to one channel you read (email or a chat webhook), plus the health check.
  Recommended.** One small outbound call and one secret in Railway variables, about 30–45 minutes. Gives the "would the
  business know?" answer something real to point at. Which channel is a short follow-up if you pick B.
- **C. Page, plus an external uptime monitor pinging a readiness endpoint.** Catches "it's down" from outside the
  process, for little work. Misses "it's up but failing" and "spend cap reached".

*Recommended: B,* cut to A at Checkpoint B if time slips (that would add a line to PRD §8's cut order).

**Decision needed:** Should operator alerts stay on the page (A), also be pushed to a channel you read (B), or be covered
by an outside uptime check (C)?

### Q-046 — Burning-smell gap: policy-owner confirmation
- Stage: S6
- Layer: product
- Purpose: D2's handling of a policy gap is ours, not Meridian's.
- Sources: project
- Depends on: —
- Status: deferred
- Evidence: Consolidated §11 D2 "Still open: policy owner confirmation of the gap handling"; §9.2
- Answer: —
- Decision: Deferred to the technical documentation's known-gaps list (D-4) as a labelled assumption. Meridian is fictional, so no policy owner exists to confirm it; the handling itself is decided (D2, R-7).
- Affects: Technical documentation (D-4)
- History:
  - 2026-10-20 setup — deferred

### Q-047 — Where it must run
- Stage: S7
- Layer: design-input
- Purpose: Hosting.
- Sources: SD-7.1; pack:ai-agent-app/deployment
- Depends on: —
- Status: carried
- Evidence: Brief Part B §6 (public URL, interactive); PRD R-40 (Railway, its own dedicated project, Innocent 2026-10-20); `gauntlet-hosting-default.md`
- Answer: Railway, dedicated project, public URL.
- Decision: R-40
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-048 — The failure the deployment must survive
- Stage: S7
- Layer: design-input
- Purpose: Replicas and durability.
- Sources: SD-7.2
- Depends on: —
- Status: carried
- Evidence: PRD §10 SD-7.2 (Innocent, 2026-10-20): a process restart without losing conversations or cases (SQLite on a Railway volume, durable checkpointer); not a zone outage
- Answer: As cited.
- Decision: PRD §10 SD-7.2
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-049 — What one person can operate
- Stage: S7
- Layer: design-input
- Purpose: Keeps the design inside what Innocent runs alone.
- Sources: SD-7.5
- Depends on: Q-047
- Status: carried
- Evidence: Hard-problems GP-108 (one instance, one SQLite file, no queue, no hosted vector service; Postgres, autoscaling and a vector database rejected); PRD §6.2 (no separate frontend build); `gauntlet-hosting-default.md` ("One operator, one dashboard, one billing line")
- Answer: One Railway service, one volume, the app's own pages.
- Decision: hard-problems GP-108 (Stage 3 gate signed)
- Affects: DO-1
- History:
  - 2026-10-20 setup — carried

### Q-050 — Where traces, logs and metrics live
- Stage: S7
- Layer: design-input
- Thread: observability
- Purpose: Chooses the trace backend and what leaves the environment.
- Sources: SD-7.6; SD-8.4; SD-8.7; pack:ai-agent-app/observability
- Depends on: Q-010
- Status: answered
- Evidence: batch 3, 2026-10-20 (Innocent: "C")
- Answer: C, revised by Q-062 (2026-10-20): self-hosted Langfuse, namely the v4 instance already on the VPS; nothing new to host; rule 18 met
- Decision: PRD §6.2 (components), R-36, §10 table
- Affects: PRD §6.2 (components), R-35, R-36; DO-6 Storage and access; setup profile if rule 18 is waived
- History:
  - 2026-10-20 setup — drafted
  - 2026-10-20 batch 3 — answered C (Innocent)
  - 2026-10-20 batch 7 — revisit: research shows self-hosted Langfuse v4 needs six services, ~$29–81/month on Railway, and Railway templates deploy v3 (SDK mismatch); exceeds SD-1.6 "existing plan" → Q-062

**The story.** The monitoring page reads our own stored data (R-35), and the lookup log is a table in our database (R-29).
What is open is where the model and agent **traces** go: the record of each turn's steps, what each model saw and
produced, tokens, cost and latency. The project rule we adopted (`verification-evals-observability.md` rule 18) says
"a trace in an LLM-aware backend (Langfuse or LangSmith)". R-36 says traces are redacted before any export: no codes,
no card-like numbers, minimal personal data. The data is fictional, but whatever we choose decides whether names and
phone numbers from the seeded customers leave our Railway project. Railway's own logs keep 7 days on Hobby
(`gauntlet-hosting-default.md`, read 2026-10-10).

- **A. LangSmith (hosted) for traces; our own tables for the monitoring page and evals. Recommended.** LangGraph sends
  traces with configuration and little code, nested per run, which is the shape the rule asks for. Redacted data leaves
  for LangChain's cloud. Its free-tier limits and terms need a dated check before we rely on them.
- **B. Langfuse Cloud (hosted) for traces; our own tables for the rest.** Same shape; a callback handler to wire in.
  Open-source, so it could move in-house later. Same export and free-tier check.
- **C. Langfuse self-hosted inside our Railway project.** Nothing leaves our environment. Adds several services to run
  and pay for, and setup time we likely don't have before 06:00.
- **D. No trace backend: our own step records in SQLite plus JSON logs, and a simple trace page.** Nothing leaves; no
  vendor. It breaks rule 18, so it needs your explicit waiver, and we build the trace view ourselves.

*Recommended: A.* LangGraph is already decided, so its native tracing is the cheapest path that meets rule 18 in the time
box; the business numbers still come only from our own stored records.

**Decision needed:** Where should model and agent traces live: LangSmith (A), Langfuse Cloud (B), self-hosted Langfuse (C)
or our own tables with a rule waiver (D)?
  - 2026-10-20 batch 8 — re-confirmed through Q-062: VPS Langfuse

### Q-051 — Release and rollback
- Stage: S7
- Layer: design
- Purpose: How a bad deploy is undone.
- Sources: pack:ai-agent-app/deployment
- Depends on: Q-047
- Status: deferred
- Evidence: PRD R-43 (deployment guide is a deliverable); `SUBMISSION.md` D-5
- Answer: —
- Decision: Deferred to the deployment guide (D-5) and DO-1: single environment, redeploy of the previous Railway deployment.
- Affects: Deployment guide
- History:
  - 2026-10-20 setup — deferred

### Q-052 — Who decides a correct answer, and where cases come from
- Stage: S8
- Layer: design-input
- Purpose: Ground truth and case provenance.
- Sources: SD-8.1; SD-8.8; pack:ai-agent-app/eval-approach; pack:ai-agent-app/verification
- Depends on: —
- Status: carried
- Evidence: PRD R-38 (expected outcomes from the current KB and DB, not the human agent's answer; labelled synthetic cases); audit D-5; framing §2 ("in scope" fixed by gold labels written before any run); `synthetic-test-data.md`; worked pairs WP-1…WP-8 checked by Innocent; promise wording from OD-4
- Answer: The current KB and DB, plus Innocent's recorded decisions, decide the expected answer; each case records its transcript call ID or "synthetic" with its assumption.
- Decision: R-38; framing §2
- Affects: DO-5 Expected-answer authority, Case provenance
- History:
  - 2026-10-20 setup — carried

### Q-053 — Test data that is realistic and allowed
- Stage: S8
- Layer: design-input
- Purpose: The cases the numbers come from.
- Sources: SD-8.2
- Depends on: Q-052
- Status: carried
- Evidence: PRD R-38 (stratified across all 37 categories in proportion to the corpus; synthetic cases for safety phrasing, person requests, failure signals, identity, prompt injection); PRD §8 (about 60 transcript cases plus about 15 synthetic); source-authority rule 6
- Answer: As cited.
- Decision: R-38
- Affects: DO-5
- History:
  - 2026-10-20 setup — carried

### Q-054 — Which cases we may look at while fixing, and which give the reported number
- Stage: S8
- Layer: design-input
- Purpose: Development versus held-out separation, so the README number stays honest (SD-1.9).
- Sources: SD-8.9
- Depends on: Q-052, Q-053
- Status: answered
- Evidence: batch 4, 2026-10-20 (Innocent: "A")
- Answer: A. Two splits by template: a dev split (failures read and fixed against) and a sealed held-out split (scored only; gives the README number). Both stratified by category; builder agents never see the held-out answer key
- Decision: PRD R-38, §8 plan line, §10 table
- Affects: PRD R-38, §8 plan; DO-5 Development and held-out separation
- History:
  - 2026-10-20 setup — drafted
  - 2026-10-20 batch 4 — answered A (Innocent)

**The story.** R-38 says the test set is "held out by template", and the audit asks for "a sealed holdout split by
template" (G-8). But the build plan then runs "error analysis on the failures" of that same eval (PRD §8, 00:30–01:30),
and Stage 9 reads about 20 failing traces. If we read the failures of the cases that produce the README number and fix
against them, that number stops being a fair test. You named honest numbers as the hardest thing to prove (SD-1.9). The
transcripts give plenty of material: 420 calls from about 108 request templates (audit D-1). The worked pairs are already
the first dev set (checklist §6), but eight cases are thin for error analysis.

- **A. Two splits by template. Recommended.** Split the templates into a **dev split** (we read failures and fix against
  them) and a **sealed held-out split** (scored only; it gives the README number). Both stratified by category. Builder
  agents never see the held-out answer key. Cost: more cases to label before the first run.
- **B. One set, as planned now.** The README reports the **first run before any fix** as the honest number; later runs
  are labelled "after fixes on this set". No extra cases; the improved numbers are weaker evidence.
- **C. One sealed set; error analysis only on the worked pairs, synthetic cases and demo chats.** The reported number
  stays clean, but the material for finding and fixing failures is thin.

*Recommended: A.* It keeps the number clean and still gives the error analysis real calls to learn from.

**Decision needed:** How should the test cases be split: separate dev and held-out splits (A), one set with the first run
reported (B), or one sealed set with no transcript dev cases (C)?
  - 2026-10-21 Stage 6 — refined by EVQ-1 = A (Innocent): balance by driver family and support level, not category (34 of 37 categories have one template)


### Q-055 — Load test
- Stage: S8
- Layer: design-input
- Purpose: How capacity per replica and the 8 s target are checked.
- Sources: SD-8.3; SD-7.3
- Depends on: Q-028
- Status: carried
- Evidence: Hard-problems GP-113 ("A 20-conversation load test at Stage 9 shows it") and GP-118 (capacity per replica measured at Stage 9); SD-3.4 (20 at once)
- Answer: A 20-conversation load test at Stage 9. Tool, environment and spend handling are design (DO-5).
- Decision: hard-problems GP-113, GP-118
- Affects: DO-5
- History:
  - 2026-10-20 setup — carried (tool and environment deferred to DO-5)

### Q-056 — What is captured while it runs
- Stage: S8
- Layer: design-input
- Thread: observability
- Purpose: Runtime capture and what one agent run's trace holds.
- Sources: SD-8.4; SD-8.7
- Depends on: Q-010, Q-037
- Status: carried
- Evidence: Project rule `verification-evals-observability.md` 18 (correlation ID; ordered steps, per-step latency, tool calls and failures, retrieved documents, tokens and cost) and 21 (each model call holds the full rendered context and raw output, nested under one request); R-29 (lookup log); R-35 (volume, containment, escalations by reason, failures, latency p50/p95, spend); R-36 (redaction); consolidated §10 (checkpoint history is not the audit log)
- Answer: As cited; where it is stored is Q-050.
- Decision: project rule 18, 21; R-29, R-35, R-36
- Affects: DO-6
- History:
  - 2026-10-20 setup — carried

### Q-057 — Where each claim's evidence goes
- Stage: S8
- Layer: design-input
- Purpose: Maps evidence to graded items.
- Sources: SD-8.5
- Depends on: —
- Status: carried
- Evidence: `SUBMISSION.md` "Required goals → where the evidence will live"
- Answer: As cited.
- Decision: SUBMISSION.md
- Affects: SUBMISSION.md
- History:
  - 2026-10-20 setup — carried

### Q-058 — Which measurement triggers a redesign
- Stage: S8
- Layer: design-input
- Purpose: Redesign triggers.
- Sources: SD-8.6
- Depends on: Q-023
- Status: carried
- Evidence: Framing §2 decision lines (topic below 90% → error analysis, then people; wrong answers above 5% → driver escalates; p95 above 8 s → check model and retrieval; failure rate above 2%; false alarms above 10% → tighten the classifier); SP-1 decision criteria; hard-problems GP-113 (first breaker expected: model-provider concurrency)
- Answer: As cited.
- Decision: framing §2; SP-1
- Affects: DO-1, DO-7
- History:
  - 2026-10-20 setup — carried

### Q-059 — Feedback and learning loop
- Stage: S8
- Layer: product
- Purpose: How flagged failures improve the system.
- Sources: pack:ai-agent-app/iteration
- Depends on: —
- Status: carried
- Evidence: PRD R-37 (staff flag → review list; nothing changes the KB, prompts or eval set automatically); audit G-6, C-13; project rule 20 (only reviewed traces become eval cases)
- Answer: As cited.
- Decision: R-37
- Affects: DO-5, DO-6
- History:
  - 2026-10-20 setup — carried

### Q-060 — Testing strategy
- Stage: S8
- Layer: design-input
- Purpose: Unit, flow, adversarial and regression testing.
- Sources: pack:ai-agent-app/testing
- Depends on: —
- Status: carried
- Evidence: `build-loop-test-scope.md` (affected tests; test-first only for `risk::security`); PRD R-38 (synthetic injection and identity cases), R-39; framing hard gates; each HP card's "How we'll know it worked"
- Answer: As cited.
- Decision: build-loop-test-scope rule; R-38, R-39
- Affects: DO-5
- History:
  - 2026-10-20 setup — carried

## Observability map

| Stage | What must be known | Items | Questions | Disposition | Evidence, reason or plan |
|---|---|---|---|---|---|
| S1 | What may be recorded raw / redacted / never; who reads it; retention; export | SD-1.8, SD-1.10 | Q-010 | answered | R-36, R-15, D6: no codes or card-like numbers ever; redact before export; staff roles read; 90 days after close in production, reset in the demo. What leaves the environment follows Q-050 |
| S2 | Operational success per operation, kept apart from output correctness | SD-2.8, SD-2.7 | Q-020, Q-021, Q-022 | answered | Framing §2 health list vs value metrics V1–V5; R-35 shows them apart; failures end in a handoff counted as a health event. Exact status values deferred to DO-6 (Q-022) |
| S3 | Every workflow and entry point to cover; volumes to count | SD-3.1 – SD-3.7 | Q-030, Q-031 | answered | Q-030 lists user operations, the scheduled job, eval runs, SP-1 and Stage 9 experiments, deploy, ingestion, reset and seeding; none excluded. Volumes: ~100/day, 20 at once [T] |
| S4 | Run stages, waits and queues, timed boundaries, one run ID | SD-4.7, SD-4.3 | Q-034, Q-037, Q-016 | answered | Stages from PRD §6.1; `thread_id` per conversation; lookup-log row per tool call (R-29); model decision points named (Q-034). Timed boundaries deferred to DO-1/DO-6 (Q-016) |
| S5 | Time and resource use per stage; tokens and cost per outcome (AI) | SD-5.1 – SD-5.3 | Q-040 | assumed | Assumed 1 classifier call plus 1–4 main-model calls per turn, about $0.10 per conversation [C]. Plan: SP-1 records latency, tokens and cost per step over WP-1…WP-8 for two model mixes |
| S6 | Failure, overload and recovery signals | SD-6.6, SD-6.3, SD-6.5 | Q-045, Q-041 | answered | Signals are decided (framing health list, R-35). Who is told: Q-045 = A (Innocent, batch 2, 2026-10-20), the monitoring page plus a restarting health check; push alerts are roadmap. Dependency failures end in a handoff (PRD §5); the dependency facts behind SD-6.3 are research (Q-033) |
| S7 | Where telemetry lives, who operates it, the constraint that chose it | SD-7.6, SD-7.5 | Q-050, Q-049 | answered | Q-050 = C (Innocent, batch 3, 2026-10-20): Langfuse self-hosted; then Q-062 (batch 8): the Langfuse v4 already on the VPS, so traces stay on Innocent's server (rule 18, R-36). Operator: Innocent alone. The deployed app needs a public HTTPS route at deploy (SDQ-3, Innocent's yes) |
| S8 | Runtime capture, model/agent run trace (AI), redesign triggers | SD-8.4, SD-8.7, SD-8.6 | Q-056, Q-058, Q-059 | answered | Rule 18 and 21 trace contents, R-29 lookup log, R-36 redaction; reviewed traces only become eval cases (rule 20, R-37); triggers from framing decision lines and SP-1 |

### Q-061 — Model spend: the measured-by-estimate cost is over the $10/day cap
- Stage: S5
- Layer: design-input
- Purpose: Re-ask SD-1.6 because the numbers undercut it (system-design-questioning rule 8).
- Sources: SD-1.6; SD-5.4; research §2c
- Depends on: Q-040, Q-033
- Status: answered
- Evidence: research §2c [C]: Sonnet in all roles ≈ $0.166 per conversation (5 turns, no thinking tokens); ≈ $0.206 with 200 thinking tokens per call; Jev for routing + half of Sonnet input cached ≈ $0.083; Start tier spend cap $500/month
- Answer: Innocent, 2026-10-20: "lets even up it to 30": the model cap becomes $30/day (about $0.30 per conversation at ~100/day [C]); Sonnet everywhere fits the estimate. The Anthropic Start tier ($500/month) binds first at sustained full load
- Decision: —
- Affects: PRD §5 spend, §10 SD-1.6; SP-1 decision criteria
- History:
  - 2026-10-20 batch 7 — drafted (re-ask)
  - 2026-10-20 batch 8 — answered: $30/day (Innocent)

### Q-062 — Tracing: self-hosted Langfuse costs more than the "existing plan" answer allows
- Stage: S7
- Layer: design-input
- Purpose: Re-ask Q-050 = C because the numbers undercut it (system-design-questioning rule 8).
- Sources: SD-7.6; SD-1.6; research §6
- Depends on: Q-050
- Status: answered
- Evidence: research §6: Langfuse v4 = web, worker, Postgres, ClickHouse, Redis, blob storage; ≥ 2 vCPU / 4 GB (Railway template) to 4 cores / 16 GiB (Langfuse); ≈ $29–81/month [C]; Railway templates deploy v3 while SDK 5.x needs server v4.59+
- Answer: Innocent, 2026-10-20: "langfuse is already running on our vps": use that Langfuse v4 instance (YourAI stack), in its own Langfuse project; no Railway-hosted Langfuse. Localhost-bound: local runs use it directly; the Railway app needs a public HTTPS route, a deploy-time step done with Innocent's yes
- Decision: —
- Affects: PRD §6.2 Tracing, R-36, §10; Q-050
- History:
  - 2026-10-20 batch 7 — drafted (re-ask)
  - 2026-10-20 batch 8 — answered: existing VPS Langfuse (Innocent)

## Checklist coverage

| ID | Kind | Tier | Stage | Disposition | Evidence, reason or plan | Questions |
|---|---|---|---|---|---|---|
| SD-1.1 | Issued | Core | S1 | answered | Brief Part A §PRD, Part B §Overview; PRD §2; OD-1 | Q-001 |
| SD-1.2 | Issued | Core | S1 | answered | Brief Part B §What we are looking for, §Deliverables; Part A §Required Deliverables; audit C-1; SUBMISSION.md | Q-002 |
| SD-1.3 | Issued | Core | S1 | answered | PRD §7 (DEC-2, DEC-5); source-authority rule 1 | Q-003 |
| SD-1.4 | Issued | Core | S1 | answered | Brief Part A §Technology; LangGraph (consolidated §10, §11); PRD §6.2, R-11, R-40 | Q-004 |
| SD-1.5 | Issued | Core | S1 | answered | Innocent, 2026-10-20 ("dont worry about it lets keep our eyes on the prize"): the partner deadline (GQ-20) is not pursued; the internal target, Wed 2026-10-21 06:00 CT (SUBMISSION.md), governs. The brief's own time box is "2-3 days" | Q-005 |
| SD-1.6 | Issued → Decision if silent | Core | S1 | answered | PRD §10 SD-1.6: $30/day model cap (Innocent, Q-061, 2026-10-20; was $10/day); Railway existing plan; tracing on the existing VPS Langfuse (Q-062) | Q-006, Q-061, Q-062 |
| SD-1.7 | Issued / External | Full | S1 | answered | Framing §1: ~111 s staff time per correct resolution [M]; hard-problems GP-107: ~$0.10 per conversation [C] | Q-007 |
| SD-1.8 | Issued | Core | S1 | answered | Fictional issued data (dataset README via docs/data/README.md); source-authority rule 8; D6 retention; R-15 | Q-008 |
| SD-1.9 | Decision | Core | S1 | answered | PRD §10 SD-1.9 (Innocent, 2026-10-20): every reported number honest | Q-009 |
| SD-1.10 | Issued → Decision if silent | Core | S1 | answered | R-36, R-15, D6 (consolidated §9.6), audit G-9, project rule 19 | Q-010 |
| SD-2.1 | Decision (from the PRD's use cases) | Core | S2 | answered | PRD §3.2, §4 (Stage 1 approval 2026-10-20) | Q-013 |
| SD-2.2 | Issued + Decision | Core | S2 | answered | Framing §2 hard gates; PRD R-5, R-13, R-15, R-19, R-21, R-26, R-46 | Q-014 |
| SD-2.3 | Issued → Decision if silent | Core | S2 | answered | p95 ≤ 12.5 s per turn at 20 at once (PRD §5; Innocent 2026-10-21 after SP-1 measured 10.2 s; was 8 s). Start/stop points deferred to DO-1 (Q-016) | Q-015, Q-016 |
| SD-2.4 | Decision | Core if data changes after ingestion | S2 | answered | R-45 (re-read slots and code expiry), R-29 (changed-since marker), R-11 (index rebuilt from manifest) | Q-017 |
| SD-2.5 | Decision | Core | S2 | answered | PRD §5 Reliability; R-47; hard-problems GP-114 | Q-018 |
| SD-2.6 | Decision | Full | S2 | answered | PRD §10 SD-7.2: no conversation or case lost on restart; no zone recovery; no separate RTO target (light depth) | Q-019 |
| SD-2.7 | Decision | AI | S2 | answered | Framing §2 V1, V4 addition, V5; R-28; baselines none yet, first eval run sets them | Q-020 |
| SD-2.8 | Decision | Core | S2 | answered | Framing §2 health vs value; R-35; PRD §5 (failure → handoff). Status values deferred to DO-6 (Q-022) | Q-021, Q-022 |
| SD-2.9 | Decision | Core | S2 | answered | Framing §2 north star, V1–V5, health list with units, denominators, decision lines, signed targets | Q-023, Q-024 |
| SD-3.1 | Issued | Full; Core if the brief gives any number | S3 | answered | PRD §10 SD-3.1 (Innocent, 2026-10-20): about 100 conversations per day [T]; scale path to 10× (~1,000/day, ~200 at once), written in DO-1, nothing built (Q-029 = A, batch 1) | Q-027, Q-029 |
| SD-3.2 | Measure | Full | S3 | assumed | Assumed ~100 conversations/day, about 5–8 turns each, 1 classifier + 1–4 main-model calls per turn (hard-problems GP-111). Plan: SP-1 and the first eval run count turns and calls | Q-040 |
| SD-3.3 | Measure | Full | S3 | assumed | Assumed the corpus topic mix (inventory §3.1: booking 31.4%, billing 16.0%, membership 13.6%, warranty 10.7% …). Plan: monitoring page volume by topic and the first eval run's per-topic counts | Q-030 |
| SD-3.4 | Issued → Decision if silent | Full | S3 | answered | PRD §10 SD-3.4 (Innocent, 2026-10-20): a 20-user spike [T] | Q-028 |
| SD-3.5 | External | Core if any exists | S3 | answered | Consolidated §10 scheduled due/overdue job; ingestion and index build at deploy (PRD §6.2; 17 KB files) | Q-031 |
| SD-3.6 | External / Measure | Full | S3 | answered | Issued sizes: 17 KB files, 154 customers, 528 slots, 159 appointments (audit D-9, §3); retention 90 days after case close, demo resets (D6) | Q-031 |
| SD-3.7 | Decision | Core | S3 | answered | Full workflow list compiled from decided requirements; none excluded (Q-030) | Q-030 |
| SD-4.1 | Issued for legacy, otherwise Decision | Core | S4 | answered | R-19 and Q-2 (working copy), R-25 case store, R-10/DEC-4 KB authority, GP-117 derived index | Q-032 |
| SD-4.2 | External | Core | S4 | answered | `docs/research/2026-10-20-vendor-and-framework-facts.md` §1 (S-187…, read 2026-10-20): auth, tool-use round trip, error shape; forcing a tool call returns 400 on Sonnet 5.5 (use `auto` + `strict` or `output_config.format`); thinking on by default and billed as output → design notes for DO-4 | Q-033 |
| SD-4.3 | Decision | AI | S4 | answered | PRD §6.1 (HP-1), R-47 (HP-2), R-28 | Q-034 |
| SD-4.4 | Decision | Core | S4 | answered | PRD §6.1; R-9, R-11; consolidated §10; R-34, R-39 | Q-035 |
| SD-4.5 | Decision | Core | S4 | answered | R-19, R-46; consolidated §10 idempotent case creation | Q-036 |
| SD-4.6 | External + Decision | Legacy | S4 | n/a | Legacy tier does not apply: greenfield, no existing system extended (setup profile excludes legacy-integration-constraints) | — |
| SD-4.7 | Decision | Core | S4 | answered | PRD §6.1 stages; consolidated §10 thread_id; R-29. Timed boundaries deferred (Q-016) | Q-037, Q-016 |
| SD-5.1 | Measure | Full | S5 | assumed | Assumed small CPU per turn (rule checks, SQLite reads, one local query embedding) next to model wait time. Plan: SP-1 step timings, then the Stage 9 load test | Q-040 |
| SD-5.2 | Measure | Full | S5 | assumed | Assumed a few SQLite reads per turn and one short write transaction per booking. Plan: lookup-log counts in SP-1 and the first eval run | Q-040 |
| SD-5.3 | Measure | AI | S5 | assumed | Assumed 1 classifier + 1–4 main-model calls per turn, ~$0.10 per conversation [C]. Plan: SP-1 measures tokens, calls, latency and cost per conversation for two model mixes | Q-040 |
| SD-5.4 | External | AI | S5 | answered | `docs/research/2026-10-20-vendor-and-framework-facts.md` §2: Sonnet 5.5 $2/$10 per M tokens, cache hit $0.10, 1M context; Haiku 5.5 $0.10/$0.50; key on the Start tier [M probe]: 1,000 RPM, 2M ITPM, 400K OTPM, **$500/month spend cap**; cost per conversation [C] Sonnet-everywhere ≈ $0.166 (over the $0.10 budget; see Q-061) | Q-033, Q-061 |
| SD-5.5 | External | Core if any | S5 | answered | Option B routes Jev through OpenRouter on every turn: OpenRouter limits and errors S-229, S-230 (read 2026-10-20; readiness report §4). Otherwise none: embeddings run locally (R-11); no SMS, email or payment vendor (PRD §7, R-34) | Q-033 |
| SD-5.6 | External | Full | S5 | answered | `docs/research/2026-10-20-vendor-and-framework-facts.md` §3: uvicorn 1 worker, sync endpoints on a 40-thread pool; SqliteSaver not for async calls; fastembed in a thread is fine. Finding for build: `async def` chat endpoint calling the sync graph blocks the event loop; make it `def` | Q-033 |
| SD-6.1 | Decision | Core | S6 | answered | Hard-problems GP-114; R-41 | Q-041 |
| SD-6.2 | Decision | Core | S6 | answered | R-19 idempotent writes; consolidated §10 brakes and idempotent case; GP-114 deadline then handoff. Values deferred to DO-1/DO-4 | Q-042 |
| SD-6.3 | External | Core | S6 | answered | `docs/research/2026-10-20-vendor-and-framework-facts.md` §4: 429/500/504/529 and the spend-cap 429 without retry-after; SDK 1.17.0 retries 2× with 0.5–8 s backoff, honours retry-after uncapped → we set our own per-turn deadline | Q-033 |
| SD-6.4 | Decision | Core if there's external data | S6 | answered | R-45, R-29; GP-116 refuse rather than guess | Q-043 |
| SD-6.5 | Decision | Full | S6 | answered | No job queue (GP-108). The only backlog is cases, aged by due-soon and overdue alerts (consolidated §6, R-33) | Q-041 |
| SD-6.6 | Decision | Core | S6 | answered | Q-045 = A (Innocent, batch 2, 2026-10-20): alerts on the monitoring page (R-35) plus a restarting health check; no push channel tonight | Q-045 |
| SD-7.1 | Issued | Core | S7 | answered | Brief Part B §6; PRD R-40 (Railway, dedicated project) | Q-047 |
| SD-7.2 | Decision | Full | S7 | answered | PRD §10 SD-7.2 (Innocent, 2026-10-20) | Q-048 |
| SD-7.3 | Measure | Full | S7 | assumed | Assumed one instance holds 20 conversations at once [C from SD-3.4]. Plan: the Stage 9 20-conversation load test (hard-problems GP-113, GP-118) | Q-055 |
| SD-7.4 | External | Core | S5 | answered | `docs/research/2026-10-20-vendor-and-framework-facts.md` §5: Railway Hobby $5/month incl. $5 usage; RAM $10/GB-month, CPU $20/vCPU-month, volume $0.15/GB-month; Hobby volume ≤ 5 GB, one per service, no replicas with a volume | Q-033 |
| SD-7.5 | Decision | Core | S7 | answered | Hard-problems GP-108; PRD §6.2; hosting rule "one operator" | Q-049 |
| SD-7.6 | Decision | Core | S7 | answered | Q-050/Q-062 (Innocent, 2026-10-20): the Langfuse v4 already on the VPS; own tables for the monitoring page and evals; alerts on the page (Q-045 = A) | Q-050, Q-062 |
| SD-8.1 | External / Decision | Core | S8 | answered | R-38 (current KB and DB as answer key); audit D-5 | Q-052 |
| SD-8.2 | Issued / External | Core | S8 | answered | R-38; PRD §8 (~60 transcript + ~15 synthetic cases); synthetic-test-data rule | Q-053 |
| SD-8.3 | Decision | Full | S8 | answered | Hard-problems GP-113: 20-conversation load test at Stage 9. Tool and environment deferred to DO-5 | Q-055 |
| SD-8.4 | Decision | Core | S8 | answered | R-35, R-29, project rule 18; storage location is SD-7.6 | Q-056 |
| SD-8.5 | Issued | Core | S8 | answered | SUBMISSION.md goal-to-evidence table | Q-057 |
| SD-8.6 | Decision | Core | S8 | answered | Framing §2 decision lines; SP-1 criteria; GP-113 | Q-058 |
| SD-8.7 | Decision | AI | S8 | answered | Project rule 18 and 21; R-29, R-36; consolidated §10 (checkpoints are not the audit log) | Q-056 |
| SD-8.8 | Issued → Decision if silent | Core | S8 | answered | R-38, framing §2 gold labels before any run, synthetic labels with assumptions, WP checks by Innocent | Q-052 |
| SD-8.9 | Decision | AI | S8 | answered | Q-054 = A (Innocent, batch 4, 2026-10-20): dev split and sealed held-out split by template; only the held-out split gives the README number (R-38) | Q-054 |

## Batch log

| Batch | Date | Stage | Questions | Consequential inference | Reconciled into |
|---|---|---|---|---|---|
| 0 | 2026-10-20 | setup | — | Stages 1–3 and the PRD §10 foundation answers settle almost everything: 43 of 60 items are answered from sources, 4 product/design-input questions remain (Q-029 scale path, Q-045 alert delivery, Q-050 trace location, Q-054 dev vs held-out), and 6 vendor/framework facts are research for Claude before SP-1 | Nothing edited. **Queued for owners (Claude, the PRD and context owner; Innocent approves):** (1) PRD §3.3 has a stray table fragment after the roadmap note with superseded numbers (18.8%, "missing systems 67 (16.0%)"): remove. (2) PRD R-11 labels the `bge-small` embedding choice "[Issued] Part A": the brief names embeddings, not the model; relabel. (3) PRD §5 labels the 8 s p95 "[A]" while the framing (signed) and hard-problems SP-1 treat it as Innocent's target: make one label. (4) PRD §6.1 says it replaces "the earlier flow (PRD 0.2)" while the header still reads 0.2: bump the version. (5) hard-problems HP-3 status line still says R-22 "awaiting" (decided 2026-10-20). (6) Stale routes: `CLAUDE.md` "our PRD will live in docs/prd/ (planned)", router "PRD draft 0.1, not approved", PROJECT-CHECKLIST §1 "0.1", `.claude/state/resume.md` "first open gate is Stage 1". (7) SUBMISSION.md goal 1 evidence "docs/data/ (planned)" now exists. (8) Framing §5 still calls "our targets" proposals; they were signed. (9) When Q-029/045/050/054 are answered: record in PRD §10 (decision table) and §5/§6.2/R-35/R-38 as unapproved revisions, and in the dev log; if Q-050 = D, record the rule-18 exception in the setup profile. (10) PROJECT-CHECKLIST §4 first item can be ticked once this interview runs its first batch |
| 1 | 2026-10-20 | S3 | Q-029 | Innocent chose A: DO-1 gets a written 10× scale path (about 1,000 a day, about 200 at once) naming what breaks first and the change for each; nothing is built for it | PRD §10 table (SD-3.1 row) and §5 load bullet; dev log. Batch-0 queue: items 2, 4–8 applied; (1) and (3) rejected (the §3.3 row is the current breakdown; the signed framing also labels 8 s an assumption) |
| 2 | 2026-10-20 | S6 | Q-045 | Innocent chose A: alerts stay on the monitoring page with a restarting health check; nobody is pushed a message, so "would the business know?" is answered by the page plus the health check, and a push channel is roadmap | PRD R-35, §10 table; dev log |
| 3 | 2026-10-20 | S7 | Q-050 | Innocent chose C: traces go to Langfuse run inside our Railway project, so nothing leaves our environment and rule 18 holds without a waiver. It adds services to run; their count, setup time and cost are researched before SP-1, and if they threaten the 06:00 build that comes back to Innocent as a question, not a quiet change | PRD §6.2, R-36, §10 table; Q-033 research list; dev log |
| 4 | 2026-10-20 | S8 | Q-054 | Innocent chose A: the test cases are split by template into a dev split (read and fixed against) and a sealed held-out split (scored only, the README number); error analysis in the build plan runs on the dev split | PRD R-38, §8 plan line, §10 table; dev log |
| 5 | 2026-10-20 | S1 | SD-1.5 | Innocent: "dont worry about it lets keep our eyes on the prize". The partner deadline is not pursued; the internal 06:00 target governs. Also measured [M], one probe call per model on 2026-10-20: Sonnet 5.5 and Haiku 5.5 each allow 1,000 requests, 2,000,000 input tokens and 400,000 output tokens per minute on this key (feeds SD-5.4; prices and the rest come from the research note) | SUBMISSION.md unchanged; dev log |
| 6 | 2026-10-20 | S5 | Q-040 | Innocent raised the model choice himself ("one thing you never asked me"): Sonnet 5.5 in every role by default; SP-1 tests Sonnet, GPT-5.6 Terra, Gemini Flash and Jev (TypeSafe AI; routing/classification). The earlier "smaller model for classification" in PRD §6.2 is superseded | PRD §6.2, §10 table; hard-problems SP-1; research agent asked to price the candidates |
| 7 | 2026-10-20 | S4–S7 | Q-033 (research) | Research recorded (`docs/research/2026-10-20-vendor-and-framework-facts.md`, S-187…S-226). Two answers are undercut by the numbers and are re-asked: model spend (Q-061) and self-hosted Langfuse (Q-062). Build notes: no forced tool_choice on Sonnet 5.5; thinking on by default; `def` (not `async def`) chat endpoint; own per-turn deadline over SDK retries. Jev: training on inputs now excluded in writing; retention still unstated | coverage SD-4.2/5.4/5.6/6.3/7.4 answered; SD-1.6 and Q-050 marked revisit; dev log |
| 8 | 2026-10-20 | S5, S7 | Q-061, Q-062 | Model cap $30/day (Innocent; the record had $10/day). Tracing uses the Langfuse v4 already running on the VPS; it is localhost-bound, so the deployed app needs a public HTTPS route at deploy time (with Innocent's yes) | PRD §10 SD-1.6, §5 spend, §6.2 Tracing, R-36; hard-problems SP-1 and GP-107; dev log |
| 9 | 2026-10-20 | S9 | — (readiness run) | `system-design-readiness` verdict **READY**: 0 Go find, 0 Decide, 1 Assumed (SD-7.3, Stage 9 load test). SP-1 replaced SD-3.2/3.3/5.1/5.2/5.3 with measurements; SD-2.3 is now 12.5 s (Innocent, 2026-10-21); SD-5.5 n/a → answered for the Jev/OpenRouter route (S-229, S-230). Register: DO-3 → `docs/design/code-design.md`, DO-5 → `docs/design/evaluation-plan.md`, DO-6 → `docs/design/observability-contract.md`, DO-7 → `docs/design/key-metrics-registry.md`; DO-4 starts from draft CON-1…CON-20 in `docs/ux/01-planning/USER_FLOWS.md`; stale Q-029/033/045/050/054 and SP-1 notes cleared; `design_outputs.py --gate readiness` holds | `docs/design/readiness-report.md`; this register and coverage rows SD-2.3, SD-5.5; source register S-229, S-230 |
