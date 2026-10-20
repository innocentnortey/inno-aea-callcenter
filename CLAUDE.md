# CLAUDE.md — inno-aea-onboarding

**Start here:** the [router](.claude/README.md) maps each task to what to load. Where the project
stands: [`PROJECT-CHECKLIST.md`](PROJECT-CHECKLIST.md); the first unticked gate is the current
stage.

## What this repo is

The **AEA Investors hiring-partner project** (via Gauntlet AI), built against AEA's *Project 1:
AI-Powered Onboarding Assistant* brief. The brief covers four flows: guided chat intake, ID or
document OCR with user confirmation, appointment booking, and supportive content at friction points.

**Phase:** research, as of 2026-10-14. Documentation and research context only. **Don't write the
PRD, design, tickets or code until Innocent says research is done.**

**Chosen niche:** administrative patient intake across multiple practices, with a reusable core.
This is a research choice; the brief itself is general (`docs/analysis/portfolio-fit-review.md`).

## ⚠️ Evidence discipline — read before writing anything about a company

[`.claude/rules/source-authority.md`](.claude/rules/source-authority.md) loads automatically. In
short:
- The brief is ISSUED and never edited.
- Company pages show what a company publishes, not how it operates.
- An AEA "Current" label is not control or permission to deploy.
- Count platforms, not practices.
- An existing tool at a company is not evidence that it fails.
- Intake is administrative, never clinical.

## Where facts live (one owner each)

| Fact | Owner |
|---|---|
| Requirements, rubric, metrics | `docs/source/aea-proj1-onboarding-assistant.md` (ISSUED) |
| Sources, authority, review dates | `docs/source/source-register.md` |
| AEA strategies and portfolio counts | `docs/analysis/company-research/aea-investors.md` |
| Industry comparison and recommendation | `docs/analysis/portfolio-fit-review.md` |
| Per-company evidence | `docs/analysis/company-research/<company>.md` |
| Onboarding research report (template Parts 1–10, 12 sections) + annexes | `docs/analysis/2026-10-15-onboarding-research-report.md` (config spec and demo blueprint annexes alongside) |
| Public review evidence | `docs/analysis/2026-10-15-google-review-sentiment.md` (raw extracts local, git-ignored) |
| Solution candidates (SOL-N), ranking rubric, shortlist and Innocent's selection record | `docs/analysis/2026-10-15-solution-selection-and-evidence-matrix.md` |
| Unknowns (RQ-N) | `docs/analysis/research-questions.md` |
| Partner questions (open GQ-18 and GQ-20; resolved GQ-19) | `Gauntlet AI/open-questions.md` |
| Brief audit, risks (T1–T23) and consistency (C1–C11) | `docs/analysis/2026-10-14-brief-audit.md` (owns the reviewed T1–T13 and additional findings) |
| Deliverables and dates | `SUBMISSION.md` |
| Stage and gates | `PROJECT-CHECKLIST.md` |
| Engineering and system-design principles (GP-N) | `docs/principles/` (copy of `Gauntlet AI/principles/`) |
| Work history | `Gauntlet AI/devlogs/aea-onboarding/` ([contract](.claude/reference/dev-log.md)) |

## Working rules

1. **Follow `zero-to-hero`.** The sequence is in `../.claude/skills/zero-to-hero/` (mode: light).
   Stage 2 (data reality), Stage 3 (hard problems) and Stage 4 (interview) come before design or
   tickets. In Stages 3–6, walk the questions in `docs/principles/system-design.md` and raise the
   open ones as options.
2. **Two layers of success** (`.claude/rules/hiring-partner-framing.md`). Open with AEA's business
   value, prove the brief, and close on how the system moves the metric.
3. **Audit the brief, then write our own PRD.** Partner briefs contain traps. A deviation is
   documented with its source, never silent.
4. **Synthetic data only.** No real IDs or patient data, ever.
5. **Log milestones** in the dev log as work happens.
6. **Version control and hosting** follow `.claude/rules/project-provenance.md`. Commit and push
   only when asked.
7. **HTML is a local file** in `docs/artifacts/`, never a published Artifact.
8. **Riverside** is deferred for this AEA research. The portal partner is The Riverside Company: its legal disclosures identify Riverside Partners L.L.C. as doing business under that name (GQ-19 resolved 2026-10-15). The separate Boston Riverside Partners rebranded as RS2 Healthcare Partners. Shared-submission permission remains GQ-18; Riverside does not shape AEA's product framing here.
