# Project Checklist — inno-aea-onboarding

Sequence: `zero-to-hero` v1.0.0 (`Nortorious-Technologies/.claude/skills/zero-to-hero/`).
Artifact paths: that skill's `ARTIFACT-MAP.md` (§ numbers below match).

| Field | Value |
|---|---|
| Project | inno-aea-onboarding — AEA Investors Project 1, AI-Powered Onboarding Assistant |
| Kind | hiring partner (AEA Investors, via Gauntlet AI) |
| Mode | light (3-day brief timebox) |
| Started | 2026-10-14 (folder and research context; research phase continues before the PRD) |
| Deadline / internal cutoff | partner deadline **unconfirmed** (GQ-20) / internal target 2026-10-17 22:00 CT — details in `SUBMISSION.md` |
| Layout substitutions | GitLab rule carried as short `.claude/rules/project-provenance.md` (per that rule's 2026-09-19 note) · company research in `docs/analysis/company-research/` · source register `docs/source/source-register.md` · portfolio inventory in `docs/evidence/` · open questions `docs/analysis/research-questions.md` · dev log central in `Gauntlet AI/devlogs/aea-onboarding/` |

**How to use.** Tick an item when its artifact exists at the mapped path. A gate line is passed
only with evidence, and a ★ gate only with `Innocent ✓ YYYY-MM-DD`. The first unticked gate is
where the project is. A stage skipped goes under *Skips* with its reason.

---

## 0 · Scaffold  (§0)
- [x] `PROJECT-CHECKLIST.md` (this file) filled in — 2026-10-14
- [x] `CLAUDE.md` entry point (+ `AGENTS.md` if Codex works here) — 2026-10-14
- [x] Principles pack copied to `.claude/rules/`, provenance line in each: general · Gauntlet policy · hiring partner · legacy (OpenEMR only) — 2026-10-14; legacy not applicable
- [x] Principles half of the pack: `Gauntlet AI/principles/` → `docs/principles/` (GP-1 – GP-119, incl. `system-design.md`) + rule `system-design-conversation` — 2026-10-14 (missed at first scaffold; zero-to-hero §0 now requires both halves)
- [ ] Remote and host set per policy (Gauntlet: GitLab `origin`, Railway) — *local `git init` only (no commit); GitLab project not created (Innocent); GitHub mirror needs his yes; Railway not set up*
- [x] `SUBMISSION.md` opened (Gauntlet) — 2026-10-14
- **Gate:** ☑ pack present, checklist filled — 2026-10-14 (remote/host item still open; it does not block research)

## 1 · Frame  (§1)
- [x] Sources converted and ranked in `docs/source/` — 2026-10-14: brief (already Markdown, unchanged copy) + `source-register.md` with authority labels. No portal page captured for AEA; add one if it exists
- [x] *(Pipeline step 1, before the audit)* Company research: AEA context, five company profiles, portfolio fit review, research questions — `docs/analysis/` (2026-10-14). Research continues; not signed off
- [x] Onboarding research report against `docs/aea-portfolio-research.md` (Parts 1–10, 12 sections, five platforms) with configuration and demo-blueprint annexes and corrected review evidence — `docs/analysis/2026-10-15-onboarding-research-report.md` (2026-10-15). Not signed off; company discovery questions open (RQ-38…RQ-43)
- [x] Patient journey and standard onboarding research supplement — `docs/analysis/2026-10-15-patient-journeys-and-onboarding-baseline.md` (2026-10-15). Reference journeys and candidate evaluation criteria; no PRD or research sign-off. RQ-44…RQ-46 remain open.
- [x] Review pitfalls synthesis — `docs/analysis/2026-10-15-review-pitfalls-and-solution-opportunities.md` (2026-10-15). Interpretation only; no scope selected.
- [x] Solution selection matrix (proposed, **not selected**) — `docs/analysis/2026-10-15-solution-selection-and-evidence-matrix.md` (2026-10-15): mandatory baseline M-01…M-15, 19 discretionary candidates SOL-001…SOL-019, shortlist of 8, 11 parked. Innocent's selection of ~4 is pending; the 2026-10-15 reconciliation pass updated the report, profiles, register, annexes and RQs to match. Research is **not** signed off.
- [x] Brief audit: traps, real problem, real guideline — `docs/analysis/2026-10-14-brief-audit.md`, 2026-10-14. T1–T13 reviewed; T14–T23 and consistency review C1–C11 added. Recommendations and framing sign-off remain open
- [ ] Two-layer success framing + metrics tree
- [ ] PRD draft — `docs/prd/<project>-prd.md`
- **Gate:** ☐ audit + framing signed off — Innocent ✓ ____

## 2 · Data reality ★  (§2)
- [ ] Samples in `docs/data/samples/` (full 20–50 · light ~10)
- [ ] Selection matrix: every source, every type, the strange ones — `docs/data/README.md`
- [ ] Worked pairs `WP-1…` in `docs/data/worked-pairs.md` (full 5–10 · light 3), each marked easy/hard and sure/uncertain
- [ ] Synthetic stand-ins labelled with their assumption
- **Gate:** ☐ every core workflow has pairs; every uncertain pair checked — Innocent ✓ ____

## 3 · Hard problems ★  (§3)
- [ ] Register `docs/design/hard-problems.md`: HP-1 orchestration + one card per hard problem + *Handled by default* list
- [ ] Every `hard` worked pair maps to a card
- [ ] Each card: evidence pairs, why hard, options with diagrams, recommendation, principles, success measure
- [ ] Page rendered — `docs/artifacts/…-hard-problems.html`
- **Gate:** ☐ Innocent has worked through the page — Innocent ✓ ____

## 4 · Interview ★  (§4)
- [ ] `prd-interview` run *after* §3, fed the register (page choices recorded, not re-asked)
- [ ] Every HP choice in the decision record
- **Gate:** ☐ PRD approved — Innocent ✓ ____

## 5 · Spikes  (§5)
- [ ] `SP-N` record for every card not yet `chosen`, scored on the worked pairs
- **Gate:** ☐ no HP card is `open`

## 6 · Design  (§6)
- [ ] `system-design-readiness` READY
- [ ] DO-1…DO-7 written at their mapped locations
- [ ] DO-5 eval plan: worked pairs as the first dev set, HP success measures as criteria, error-analysis-first rule
- **Gate:** ☐ `design_outputs.py check … --gate tickets` passes; Innocent reviewed DO-1/DO-2 ✓ ____

## 7 · Tickets — four passes ★  (§7)
- [ ] 7a Slice plan `docs/plans/slice-plan.md` — Innocent ✓ ____
- [ ] 7b Spec one wave at a time; each issue has an example pair (WP-N) and its HP link
- [ ] 7c Coverage audit clean
- [ ] 7d Published to GitLab, waves labelled
- **Gate:** ☐ all four passes done

## 8 · Build  (§8)
- [ ] Each ticket's WP-N written as its first failing test before implementation
- [ ] Review gates per ticket; seam audit per wave
- **Gate:** ☐ waves merged, seam audits clean

## 9 · Experiment ★  (§9)
- [ ] Kickoff page generated from code (flow, prompts with versions, approach, failure types)
- [ ] Error-analysis round: ~20 traces, first failure each, `FT-N` taxonomy, models × failures table — Innocent ✓ ____
- [ ] Every `XP-N` targets one `FT-N`, one change, scored on the frozen set
- **Gate:** ☐ no tuning change without a named failure type

## 10 · Ship & defend  (§10)
- [ ] `SUBMISSION.md` walked; every row's evidence at the expected path
- [ ] Demo script (two-layer order) and interview prep
- [ ] Retro written; lessons fed back to `Gauntlet AI/principles/` and `zero-to-hero`
- **Gate:** ☐ shipped — Innocent ✓ ____

---

## Skips

| Stage | Reason | Decided by | Date |
|---|---|---|---|

## ID registers (quick index)

| Prefix | Where | Count |
|---|---|---|
| RQ | `docs/analysis/research-questions.md` (project-local addition) | 46 |
| M · SOL · P | `docs/analysis/2026-10-15-solution-selection-and-evidence-matrix.md` (mandatory baseline · discretionary candidates · parked ideas) | 15 · 19 · 11 |
| T | `docs/analysis/2026-10-14-brief-audit.md` | 23 |
| C | `docs/analysis/2026-10-14-brief-audit.md` (internal consistency) | 11 |
| WP | `docs/data/worked-pairs.md` | |
| HP | `docs/design/hard-problems.md` | |
| SP | `docs/analysis/spikes/` | |
| FT | `docs/testing/error-analysis/` | |
| XP | `docs/testing/experiments/` | |
