# Development log contract

> Source: `Gauntlet AI/artifacts/ICM Rework/module/icm-project/references/dev-log.md` (shared ICM owner), copied 2026-10-14. Refresh this copy from the shared owner. **Local destination:** `Gauntlet AI/devlogs/aea-callcenter/` (relative to this repo: `../Gauntlet AI/devlogs/aea-callcenter/`), matching Equinox and Cerbo. Runs from before the 2026-10-20 pivot stay in `Gauntlet AI/devlogs/aea-onboarding/` as history. If the folder is absent on a host, stage the run file in `docs/devlog/` and move it later.


A dev log preserves the useful story of a work run: what changed, why, what was checked, and what remains. It supports explanation and resumption. Product decisions, ticket status, acceptance evidence and AI disclosure stay in their existing owners; link to them rather than copying their full records.

## Establish the home

Every ICM project has a development/work log appropriate to its domain. Reuse an existing equivalent. Otherwise use `docs/devlog/`; honor a user-selected central workspace instead. Record the destination and its relative path from each run environment in the setup profile. Link the log from the entry and router, and embed its upkeep in the ordinary maintenance instruction and build workflow.

For file-based logs, use one file per run, named `YYYY-MM-DD-<topic>-<unique-run-id>.md`, dated in the user's timezone. Each run has one writer. Workers return short notes to that writer or own separate files; they never append concurrently to a shared file. A project index links to its run folder, not every entry, so writing a run does not require editing a common index. Preserve established naming where equivalent.

## Write during work

Create the run file at the first meaningful outcome. Append after a completed ticket or coherent wave, an important decision, a discovered failure/override, a blocker, or a handoff; do not wait until the whole run ends. Group routine successes with the same purpose. Skip command-by-command narration, repeated checks, unchanged status and empty entries. Usually 50–100 words per milestone is enough; expand only when a decision would otherwise be hard to defend.

A run header names the project, date/timezone, topic, writer/assistant (actual model only when known), host/view and branch/base revision when relevant. Use the same four fields for each entry:

```markdown
## Matching boundary fix

- **Changed:** Preserved the inclusive threshold in normalization.
- **Why:** Dropping equality could change which outcomes pay YES.
- **Checked:** Focused boundary tests passed on the stated revision; link to evidence.
- **Remaining:** Live integration has not yet been checked.
```

Use `Remaining: None for this change` when appropriate. Name what actually happened: proposed, approved, implemented, integrated or verified. A user-approved decision still awaits application until its product owner and implementation are reconciled. Record failed checks, reversals and AI overrides as well as passes. Label second-hand reports and historical backfills with source and scope; never turn them into verified results. Avoid broad history reconstruction unless requested.

## Keep the log useful

At the end or interruption, append a brief handoff only if the next action is not already clear. Read the relevant run file or recent entries; search by ticket, decision or topic rather than loading all history. Link detailed traces, issue evidence and decision owners. Keep secrets, raw restricted captures and private payloads out of log text; apply each project's export rules before sharing it.

The destination being absent on another host does not block product work. Stage the same run file in the project's `docs/devlog/` with the central destination noted; move it when available and leave a pointer if needed, not two independently maintained histories. Report a pending sync explicitly. Append corrections referencing earlier entries rather than silently rewriting settled history.

## Verify adoption

Check entry → router → maintenance/workflow → log destination and owner links. Record establishment and route evidence in the existing ICM checklist; verify actual in-run upkeep only after a real run produces entries. Logging is part of active work, not an unattended process or permission to spend, deploy, commit, push or message others. AI usage requirements remain independently satisfied.
