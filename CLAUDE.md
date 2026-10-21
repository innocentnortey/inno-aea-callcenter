# inno-aea-callcenter — project entry

## What this project is

AEA Investors' hiring-partner challenge via Gauntlet AI: the **AEA FDE Challenge — AI Call Center
Agent**. Acting as a Forward Deployed Engineer for *Meridian Home Comfort* (a fictional Austin HVAC
and plumbing company), we discover the top call drivers from unlabeled transcripts. We answer the
top 3 by RAG over a messy knowledge base, book against a mock scheduling DB, escalate the rest with
handoff context, prove containment on a transcript-built test set, and deploy publicly with
monitoring. Hosting defaults to Railway. Innocent decides scope and signs off every ★ gate.

## System boundaries

| Area | Owns | Home |
|---|---|---|
| Agent and service (planned) | The two-layer chat agent, staff console API, case store, demo controls | `src/meridian/`; detail in the [area map](.claude/reference/area-map.md) |
| Screens and UI contracts | Customer chat, staff console, the CON cards; the UX track | `docs/ux/`; the prototype is the real frontend: `apps/web/` (built 2026-10-21, awaiting the UX-4 gate) |
| Evaluation (planned) | Test cases (dev and sealed held-out), harness, reports | `eval/`; plan in [`docs/design/evaluation-plan.md`](docs/design/evaluation-plan.md) |
| Design | System design, code design, contracts, metrics, observability | `docs/design/` |

## Non-negotiable boundaries

- **The issued brief and Meridian data are never edited.** The agent writes to a *copy* of the DB. Rule: [source-authority](.claude/rules/source-authority.md).
- **Meridian is fictional; AEA context is framing only.** No requirement comes from AEA's real portfolio. Rule: [source-authority](.claude/rules/source-authority.md).
- **Numbers come from runs on a stated test set.** A target (60–75% containment) is never a result. Rule: [verification-evals-observability](.claude/rules/verification-evals-observability.md).
- **A confident wrong answer is worse than a handoff.** Safety instructions come first; promises come from policy. Rule: [source-authority](.claude/rules/source-authority.md).
- **`docs/archive/` is frozen Project 1 history.** Never cite it as requirements; never edit it. Rule: [context-maintenance](.claude/rules/context-maintenance.md).
- **No product code before its zero-to-hero gate.** The current gate is in the checklist. Rule: [new-project-zero-to-hero](../.claude/rules/new-project-zero-to-hero.md).
- **Commit or push only when Innocent asks; HTML is a local file.** Rules: [project-provenance](.claude/rules/project-provenance.md), [html-files-not-artifacts](.claude/rules/html-files-not-artifacts.md).

**Every task that moves a file, owner or route reads [context-maintenance](.claude/rules/context-maintenance.md) first.**

## Read only what the task needs

**Start at the router: [`.claude/README.md`](.claude/README.md).** These are ordinary links, not imports.

| Task | Read |
|---|---|
| Which document wins a disagreement | [source-authority](.claude/rules/source-authority.md) (ranking table) |
| What the brief requires; deliverables | [briefing](docs/source/aea-call-center-briefing.md), [`SUBMISSION.md`](SUBMISSION.md) |
| Anything touching the transcripts, KB or scheduling DB | [issued-data README](docs/data/issued/README.md), [brief audit](docs/analysis/2026-10-20-brief-audit.md) §3–§4 |
| Traps, legal, ethical or safety limits | [brief audit](docs/analysis/2026-10-20-brief-audit.md) |
| Escalation, handoff, staff or manager views | [consolidated handoff direction](docs/analysis/2026-10-20-human-handoff-consolidated-direction.md) (planning), [original handoff direction](docs/analysis/2026-10-20-human-handoff-product-direction.md) (research), [handoff information inventory](docs/data/handoff-information-inventory.md) (call drivers, sources, payload) |
| Who the customer is, how service works, UX and brand research inputs | [company and service profile](docs/analysis/2026-10-20-meridian-company-service-profile.md) |
| Framing, demo, interview answers | [hiring-partner-framing](.claude/rules/hiring-partner-framing.md), [AEA context](docs/analysis/aea-investors.md) |
| System design, sizing, failure handling, model calls | [system design](docs/design/system-design.md) (DO-1, DO-2), [`docs/design/`](docs/design/) for DO-5–DO-7 |
| Where code goes; module interfaces; API ↔ CON cards | [area map](.claude/reference/area-map.md) → [code design](docs/design/code-design.md), [contracts](docs/design/contracts/README.md) |
| Proving a feature works end to end; what a "verified" claim must record | [integrated-journeys](.claude/rules/integrated-journeys.md), then [build-loop-test-scope](.claude/rules/build-loop-test-scope.md) |
| What stage we're in; what's next | [`PROJECT-CHECKLIST.md`](PROJECT-CHECKLIST.md) |
| Start or resume work | [`.claude/state/resume.md`](.claude/state/resume.md), then the checklist |

## How this project is governed

Entry points **route**, rules **prohibit**, references **explain**, canonical documents **prove**.

| Concern | Owner |
|---|---|
| Where anything is, what to load | [router](.claude/README.md) |
| How to keep context true while working | [maintenance rule](.claude/rules/context-maintenance.md) |
| Context-system maturity | [ICM progress checklist](.claude/state/icm-progress.md) |
| Product stage and gates | [`PROJECT-CHECKLIST.md`](PROJECT-CHECKLIST.md) (zero-to-hero) |
| Requirements | [briefing](docs/source/aea-call-center-briefing.md) (ISSUED); our [PRD](docs/prd/inno-aea-callcenter-prd.md) (Stage 4 interview: [interview doc](docs/prd/inno-aea-callcenter-interview.md)) |
| Sources and their authority | [source register](docs/source/source-register.md) |
| Decisions | Product: [consolidated direction §11](docs/analysis/2026-10-20-human-handoff-consolidated-direction.md); foundation answers: PRD §10; design choices: [system design SDQ](docs/design/system-design.md); hard problems: [register](docs/design/hard-problems.md) |
| Design outputs and their status | *Design outputs* register in the [interview doc](docs/prd/inno-aea-callcenter-interview.md) |
| Code layout (planned until built) | [area map](.claude/reference/area-map.md) |
| Deliverables and dates | [`SUBMISSION.md`](SUBMISSION.md) |
| Setup choices, adopted rules, collaborators | [setup profile](.claude/reference/setup-profile.md) |
| Where we left off | [`.claude/state/resume.md`](.claude/state/resume.md) |
| Run history | dev log in `Gauntlet AI/devlogs/aea-callcenter/` ([contract](.claude/reference/dev-log.md)) |
| Which document wins | Issued briefing → issued data → Gauntlet staff answers → our analysis; full table in [source-authority](.claude/rules/source-authority.md) |
