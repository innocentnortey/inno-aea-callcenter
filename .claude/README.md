# .claude router — inno-aea-onboarding

What to load for each kind of task. `CLAUDE.md` and `rules/source-authority.md` (no `paths:`
filter) load automatically in Claude. Codex starts from `AGENTS.md` and reads routed files
explicitly.

## Layout (actual unless marked planned)

```
inno-aea-onboarding/
├── README.md · CLAUDE.md · AGENTS.md      ← purpose, entry points
├── PROJECT-CHECKLIST.md                    ← zero-to-hero stages and gates (owns stage)
├── SUBMISSION.md                           ← deliverables, evidence, dates (owns dates)
├── docs/source/                            ← ISSUED brief (unchanged) + source register
├── docs/evidence/                          ← portfolio inventory JSON (byte copy)
├── docs/analysis/                          ← fit review, research questions
│   └── company-research/                   ← AEA context + one profile per company
├── docs/analysis/2026-10-14-brief-audit.md ← legal, ethical, engineering and consistency audit (T1–T23; C1–C11)
├── docs/delivery/                          ← PLANNED: two-layer framing, demo script
├── docs/prd/ · docs/data/ · docs/design/   ← PLANNED (Stages 1–6)
├── docs/artifacts/                         ← PLANNED: local HTML outputs
├── docs/principles/                       ← Gauntlet principles GP-1 – GP-119 (copy)
└── .claude/rules/ · .claude/reference/     ← rules half of the pack, provenance, dev-log contract
```

## Task → load

| Task | Load |
|---|---|
| Any research or writing about a company | `rules/source-authority.md`, `docs/source/source-register.md`, the company profile |
| Adding or closing an open question | `docs/analysis/research-questions.md` |
| Solution candidates, shortlist or Innocent's selection | `docs/analysis/2026-10-15-solution-selection-and-evidence-matrix.md` (owner of SOL/M/P IDs), the review pitfalls synthesis, journey baseline, `rules/source-authority.md`, `rules/hiring-partner-framing.md` |
| Revisiting the niche or company choice | `docs/analysis/portfolio-fit-review.md`, `company-research/aea-investors.md` |
| Brief audit (T1–T23; C1–C11) | `docs/analysis/2026-10-14-brief-audit.md` (owner), the brief, source register, research questions, `rules/source-authority.md`; historical hypotheses in `Gauntlet AI/artifacts/2026-10-13-partner-projects-todo.md` Project 1 §2 |
| Framing, demo or interview answers | `rules/hiring-partner-framing.md`, `SUBMISSION.md` |
| Samples, golden sets, fixtures | `rules/synthetic-test-data.md` |
| LLM or agent code (later) | `rules/agent-architecture.md`, `agent-tools.md`, `verification-evals-observability.md`, `safe-validation-errors.md` |
| PRD, interview, hard problems or design docs | `rules/system-design-conversation.md` + `docs/principles/system-design.md` (questions to raise); `rules/design-doc-defense.md` |
| What a `[GP-N]` citation means | `docs/principles/` (`README.md` indexes the files) |
| Remote, hosting | `rules/project-provenance.md`, `rules/gauntlet-hosting-default.md` |
| Writing a dev-log entry | `reference/dev-log.md` |

## Principles pack (zero-to-hero §0)

| File | Source |
|---|---|
| `docs/principles/*.md` (GP-1 – GP-119, incl. `system-design.md`) | `Gauntlet AI/principles/`; the reasoning the rules cite |
| `agent-architecture` · `agent-tools` · `retrieval-and-context` · `verification-evals-observability` · `safe-validation-errors` · `synthetic-test-data` · `design-doc-defense` (scope line adapted) · `system-design-conversation` | `Gauntlet AI/.claude/rules/`, general engineering set |
| `gauntlet-hosting-default` · `html-files-not-artifacts` (location adapted) | Gauntlet policy set |
| `project-provenance` | Short policy form of `gauntlet-gitlab-versioning` (that file recommends this for spin-offs) |
| `hiring-partner-framing` | Hiring-partner set |
| `source-authority` | Local to this project |

`legacy-integration-constraints` is not copied; it applies to OpenEMR projects only.
