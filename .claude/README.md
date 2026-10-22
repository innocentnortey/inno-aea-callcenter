# .claude router — inno-aea-callcenter

What to load for each kind of task. `CLAUDE.md` and `rules/source-authority.md` (no `paths:`
filter) load automatically in Claude; path-scoped rules load when matching files are touched.
Codex starts from `AGENTS.md` and reads routed files explicitly.

**Common context for every task:** [maintenance rule](rules/context-maintenance.md) (read on any task
that moves a file, owner or route) · [ICM progress checklist](state/icm-progress.md) ·
[resume note](state/resume.md) · [setup profile](reference/setup-profile.md).

## Layout (actual unless marked planned)

```
inno-aea-callcenter/
├── CLAUDE.md · AGENTS.md · README.md       ← entry points
├── PROJECT-CHECKLIST.md                    ← zero-to-hero stages and gates (owns stage)
├── SUBMISSION.md                           ← deliverables, evidence, dates (owns dates)
├── docs/source/                            ← ISSUED briefing (portal + PDF) + source register
├── docs/data/issued/meridian_dataset/      ← ISSUED data, read-only: transcripts, KB, scheduling DB
├── docs/delivery/                         ← two-layer framing + metrics tree (2026-10-20)
├── docs/analysis/                          ← brief audit, handoff product direction (+ consolidated direction), company/service profile, AEA context, ideation notes
├── docs/evidence/                          ← AEA portfolio inventory JSON (byte copy)
├── docs/principles/                        ← Gauntlet principles GP-1 – GP-144 (copy)
├── docs/archive/project-1-onboarding/      ← FROZEN Project 1 history
├── docs/data/                              ← handoff-information-inventory.md (+ handoff-inventory-call-map.csv, scripts/) EXISTS;
│                                              samples/, README.md (matrix), worked-pairs.md ← Stage 2 (2026-10-20)
├── docs/prd/ · docs/artifacts/              ← PRD 0.3 + interview doc + review pages (2026-10-20)
├── docs/design/                            ← hard-problems.md ← Stage 3 (2026-10-20); system design PLANNED, Stage 6
├── docs/ux/                                ← UX track (§4b, ux-pipeline): 01-planning/ EXISTS, gate closed 2026-10-20; 02-concepts/ IN PROGRESS; 03 EXISTS, 04 BUILT (gate unsigned), 05 PLANNED
├── apps/web/                               ← EXISTS (2026-10-21): UX-4 prototype = the real frontend; built, gate unsigned; serving its dist/ is planned (AEA-49)
├── docs/ux/04-prototype/                   ← EXISTS (2026-10-21): PROTOTYPE_PLAN.md, groups/
├── docs/plans/fanout/2026-10-21-ux4/       ← EXISTS: foundation + g1…g5 slice plans
├── docs/artifacts/_build/                  ← generators: ux-planning/, ux-concepts/ (review pages), direction-prototypes/ (A1/A2)
└── .claude/ rules/ · reference/ · state/   ← context system
```

No backend code exists yet. The backend is mapped in [`reference/area-map.md`](reference/area-map.md) (2026-10-21, from DO-3); every backend path in it is **planned**. The one built piece of product code is the UX-4 frontend `apps/web/` (React 19 + Vite + TypeScript + Tailwind + shadcn/ui, built 2026-10-21; **UX-4 gate not signed**).

## Task → load

| Task | Load | Done when |
|---|---|---|
| PRD and the Stage 1 review | `docs/prd/inno-aea-callcenter-prd.md` (0.4; approved at Stage 4, 2026-10-20; interview `docs/prd/inno-aea-callcenter-interview.md`) → page `docs/artifacts/2026-10-20-inno-aea-callcenter-prd.html` | Page rebuilt and re-checked whenever a source changes |
| Requirements or grading | `docs/source/aea-call-center-briefing.md`, `rules/source-authority.md`, `docs/analysis/2026-10-20-brief-audit.md` §2 | The answer cites the briefing part (A/B) it rests on |
| Which KB document wins; safety, escalation, payment, legal limits | Audit §3 (K-), §5–§7 | Winner and basis named, or escalation chosen |
| Stage 2 data reality: samples, coverage matrix, worked pairs | `docs/data/README.md`, `docs/data/worked-pairs.md`, `docs/data/samples/` → page `docs/artifacts/2026-10-20-data-reality.html` | Uncertain pairs carry Innocent ✓ before the §2 gate |
| Stage 3 hard problems: HP-1…HP-4, handled-by-default list, system-design questions walked | `docs/design/hard-problems.md` → page `docs/artifacts/2026-10-20-hard-problems.html` | Every hard worked pair maps to a card; recommendations stay proposals until Innocent chooses |
| Stage 5 spikes (System track, run on the VPS copy) | `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md` (brief, harness SHA, results); `docs/analysis/spikes/HANDOFF-SP1-VPS.md` (who owns which files on Mac vs VPS) | The pass line is fixed before runs; spike code is never merged |
| Stage 6 design (System track, Mac) | `docs/design/`: `readiness-report.md`, `system-design.md` (DO-1, DO-2, SDQ-1…10), `code-design.md` (DO-3), `contracts/` (DO-4), `evaluation-plan.md`, `observability-contract.md`, `key-metrics-registry.md` (DO-5–7), `reviews/` | Register statuses in the interview; `design_outputs.py --gate tickets` |
| Where a piece of code will live; which build area owns it | `reference/area-map.md` → its DO-3 section | Path and area named; planned until built |
| Area A0 foundation (types, policy, ports, SQLite base) · A1 gates and privacy · A2 models and gateway · A3 retrieval | `reference/area-map.md` § Areas → `docs/design/code-design.md` | Module and interface found in DO-3 |
| Area A4 identity · A5 scheduling · A6 cases and handoff · A7 graph | `reference/area-map.md` § Areas → `docs/design/code-design.md`, `contracts/internal-components.md` | Module and contract found |
| Area A8 customer API · A9 staff console · A10 observability and reads · A11 eval harness · A12 deploy | `reference/area-map.md` § Areas → `contracts/api-con-mapping.md` (CON per route), `docs/design/evaluation-plan.md`, `observability-contract.md` | Route ↔ CON row found |
| Call-driver discovery, transcripts, test set (Stage 2) | `docs/data/issued/README.md`, `docs/data/handoff-information-inventory.md` (all 420 calls classified; `docs/data/scripts/`), `rules/synthetic-test-data.md`, audit §4 (D-), `docs/principles/agent-evaluation.md` | Counts reproducible by a script; issued folder untouched |
| Problem framing, metrics, PRD (Stage 1) | `rules/problem-framing.md`, `rules/business-metrics.md`, `rules/hiring-partner-framing.md`, `docs/principles/problem-framing.md`, `business-metrics.md` | GP IDs cited; open choices go to Innocent as options |
| Escalation, handoff, staff/manager views, callbacks | `docs/analysis/2026-10-20-human-handoff-product-direction.md` (earlier note `2026-10-20-service-team-ideation.md`), audit C-7, E-1, E-5 | Live takeover vs async callback kept distinct |
| Handoff product direction for planning (ranked capabilities C1–C5, brief format, case lifecycle, spike proposal) | `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md` (supersedes the original note's §5 for planning; the original stays as research) | Not a PRD; urgent, safety, fee, unsupported-request and scope decisions in §9; LangGraph in §10; decision status in §11 |
| What a representative needs at handoff; snapshot vs link; which requests need a person | `docs/data/handoff-information-inventory.md` §3, §6–§8, then the direction note | Evidence labelled [T]/[I]/[C]/[P]; proposals not treated as requirements |
| Hard problems, interview, design docs (Stages 3–6) | `rules/system-design-conversation.md`, `rules/system-design-questioning.md`, `docs/principles/system-design.md`, `rules/design-doc-defense.md` | Foundation questions asked before dependent drafts |
| KB, chunking, retrieval eval (later) | `rules/retrieval-and-context.md`, `docs/principles/context-and-rag.md` | Retrieval evaluated on its own |
| Scheduling tools, escalation, agent loop (later) | `rules/agent-architecture.md`, `agent-tools.md`, `safe-validation-errors.md` | — |
| Containment metrics, monitoring, feedback loop (later) | `rules/verification-evals-observability.md`, `docs/principles/evals-and-observability.md` | — |
| Build loop: which tests each role runs; merging in batches in tree order (Stage 8) | `rules/build-loop-test-scope.md` (*Merge in batches*; its *AEA addition*: journeys in the merge gate) | — |
| Planning: giving a planner a context pack instead of a search (Stage 8) | `rules/planning-context-packs.md` | — |
| Journeys, contract boundary checks, prompt ↔ consumer checks, live smoke, any "verified" claim (Stage 8 on) | `rules/integrated-journeys.md` (§1 inventory, §5 who runs what) → `rules/build-loop-test-scope.md` | Record in `docs/testing/journeys/` names revision, environment, command, result, evidence, limits, level |
| UX track (§4b): stories, flows, CON drafts, concepts, directions, prototypes | `docs/ux/`, `docs/design/DESIGN-DIRECTIONS.md`, `design.md`; pages `docs/artifacts/2026-10-2*-ux-*.html`, `…-direction-A5-*.html`; generators `docs/artifacts/_build/`; skill `ux-pipeline` | `trace_check.py` passes; pages rebuilt by generator; CONs owned here |
| Who Meridian serves, how service works, UX research inputs, brand/colour direction | `docs/analysis/2026-10-20-meridian-company-service-profile.md`, then `skills/ux-pipeline` when §4b starts | Meridian fact / industry context / design inference kept apart; no official palette declared |
| Two-layer framing, north star, metrics tree, best objection, demo order | `docs/delivery/2026-10-20-angle-and-demo-framing.md`; why-chain in the audit's *The problem behind this brief* | Every target labelled measured / issued / ours / assumption |
| Framing, demo, interview answers | `rules/hiring-partner-framing.md`, `docs/analysis/aea-investors.md`, `SUBMISSION.md` | Two-layer order |
| A source to add or check | `docs/source/source-register.md` | New row with authority and review date |
| What a `[GP-N]` citation means | `docs/principles/README.md` | — |
| Remote, hosting | `rules/project-provenance.md`, `rules/gauntlet-hosting-default.md` | — |
| Writing a dev-log entry | `reference/dev-log.md` | Entry in `Gauntlet AI/devlogs/aea-callcenter/` |
| The old onboarding work | `docs/archive/project-1-onboarding/README.md` | History only; never a requirement |

**Do not load** for current work: `docs/archive/` (except the line above), the raw transcripts in bulk
(use counts or a script), or `docs/principles/` files the task's rules don't cite.

**Unmapped or ambiguous task:** read the briefing and the audit section closest to it, ask Innocent
if a meaning choice is genuinely open, then add the route here in the same change.
