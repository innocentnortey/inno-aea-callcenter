# Setup profile — inno-aea-callcenter

> Extracted from: `CLAUDE.md`, `PROJECT-CHECKLIST.md`, the briefing, the brief audit and the files listed below.
> As of: 2026-10-20, Mac working copy (local git; snapshot commit `ed4ca89`, later changes uncommitted).
> Authority: each linked owner wins. Refresh this profile when an owner, location or adoption choice changes.

Semantic configuration only: who owns what, where it lives, and which reused methods are in force.
Context maturity is in [`state/icm-progress.md`](../state/icm-progress.md); product stage is in
[`PROJECT-CHECKLIST.md`](../../PROJECT-CHECKLIST.md).

## Identity and authority

| Item | Value / owner |
|---|---|
| Purpose | AEA FDE Challenge, AI Call Center Agent ([briefing](../../docs/source/aea-call-center-briefing.md)) |
| Kind | Hiring-partner coding project (Gauntlet AI); zero-to-hero **light** mode |
| Domain | *Meridian Home Comfort* (fictional): inbound calls, KB answers, booking, escalation |
| Decision owner | Innocent (scope, ★ gates, every DEC-N). Claude drafts and proposes |
| Source ranking | [source-authority](../rules/source-authority.md) |
| Open decisions | [consolidated handoff direction §11](../../docs/analysis/2026-10-20-human-handoff-consolidated-direction.md) (owns the status of OD-1…6, D1–D6, DEC-1…5, Q-1…3); audit §9 rows record the DEC decisions; `Gauntlet AI/open-questions.md` (GQ-20 partner deadline) |

## Locations and environment

| Item | Value |
|---|---|
| Work home | **VPS** `claude-vultr:/home/linuxuser/workspaces/inno-aea-callcenter` from 2026-10-21 (moved after the Stage 6 gate; rsync, identical by content). The Mac copy `~/Desktop/Nortorious-Technologies/inno-aea-callcenter` is a snapshot of that date. History: SP-1 ran on the VPS; UX-1…UX-3 and §6 ran on the Mac. No automatic sync |
| Remote | Planned GitLab `innocentnortey/inno-aea-callcenter` (Innocent creates it); see [project-provenance](../rules/project-provenance.md) |
| Host | Railway (Gauntlet default): **its own dedicated Railway project** (Innocent, 2026-10-20); not yet created |
| Model keys | `ANTHROPIC_API_KEY` and `OPENROUTER_API_KEY` in this repo's git-ignored `.env`, copied 2026-10-20 from the VPS YourAI `.env` (`SCP_LLM_API_KEY`, `SCP_OPENROUTER_API_KEY`) at Innocent's instruction; the same values go into Railway variables. Values are never printed |
| Dev log | `Gauntlet AI/devlogs/aea-callcenter/` ([contract](dev-log.md)); pre-pivot runs in `…/aea-onboarding/` |
| Assistants | Claude Code (this entry), Codex (via `AGENTS.md`) |
| Concurrent writers | `docs/analysis/2026-10-20-service-team-ideation.md` came from another session. Preserve its ownership; cite rather than rewrite it |

## Reused methods (adoption record)

| Method | Source / version | Disposition | Local adaptation |
|---|---|---|---|
| zero-to-hero | workspace `.claude/skills/zero-to-hero` **1.9.0** | Adopt | Checklist template still reads v1.6.0 and lacks the *Build loop* row; follow `ARTIFACT-MAP.md` §0 |
| icm-project | `~/.claude/skills/icm-project` **1.5.0** | Adopt | Dev-log home is central (`Gauntlet AI/devlogs/`), not `docs/devlog/` |
| Principles `docs/principles/` | `Gauntlet AI/principles/`, copied 2026-10-20 (GP-1–GP-144) | Adopt | — |
| General rules: agent-architecture, agent-tools, retrieval-and-context, verification-evals-observability, safe-validation-errors, synthetic-test-data | `Gauntlet AI/.claude/rules/`, 2026-10-14 | Adopt | `safe-validation-errors` paths (`agent/**`) assume a layout not yet designed; revisit at Stage 6 |
| design-doc-defense | same, 2026-10-14 | Adapt | Scope line names this project |
| system-design-conversation, system-design-questioning, problem-framing, business-metrics | same, 2026-10-20 | Adopt | — |
| hiring-partner-framing | same, 2026-10-20 | Adapt | Interview-feedback link re-pointed to `../../../Gauntlet AI/prep/` |
| gauntlet-hosting-default | same, 2026-10-14 | Adopt | — |
| html-files-not-artifacts | same, 2026-10-14 | Adapt | Output path `docs/artifacts/` |
| gauntlet-gitlab-versioning | same | Adapt (short form) | Carried as [project-provenance](../rules/project-provenance.md), per that rule's spin-off note |
| build-loop-test-scope | workspace `.claude/rules/`, 2026-10-20 | Adopt | — |
| legacy-integration-constraints | `Gauntlet AI/.claude/rules/` | Exclude | OpenEMR-only |
| source-authority, context-maintenance | local | Own | — |
