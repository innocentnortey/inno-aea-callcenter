# Context maintenance — keep the map true while working

Project-wide and deliberately unscoped; `CLAUDE.md` requires reading it on any task that moves a file,
an owner or a route. Created 2026-10-20 by `icm-project` 1.5.0 (zero-to-hero 1.9.0 Stage 0 retrofit).
It works while you work. It is not a background watcher.

## In the same task as the change

1. **Fix the owner, then the routes.** When an intent, domain meaning, boundary, contract, location,
   workflow or recurring lesson changes, update the record that owns it (briefing, audit, PRD,
   source register, checklist) and every route or rule that points at it: `.claude/README.md` rows,
   `CLAUDE.md` task table, rule `paths:`.
2. **The entry is not a map.** `CLAUDE.md` only routes. It holds no stage, progress, dates, decision
   summaries, history or listing of the code; those belong to the checklist, resume note, decision
   owners, dev log and area map. It changes only when identity, a boundary or a route changes.
3. **Planned is not built.** Label planned paths as planned. Keep *proposed / decided / implemented /
   verified* distinct, and link each claim to its source or evidence.
4. **Never edit** `docs/source/aea-call-center-briefing.md`'s issued text, `docs/source/*.pdf`,
   `docs/data/issued/meridian_dataset/` or `docs/archive/`. Corrections go in our own analysis.
5. **New outside source → new row** in `docs/source/source-register.md` (next free `S-N`, authority,
   review date) before a document cites it.
6. **ICM progress checklist** (`.claude/state/icm-progress.md`): when a design, scaffold, slice or test
   changes what a route can be checked against, update the affected row. *Replace* its evidence link;
   keep rows ≤400 characters. The narrative goes in the dev log.
7. **Product stage** lives only in `PROJECT-CHECKLIST.md`. Tick an item when its artifact exists; a ★
   gate needs `Innocent ✓ YYYY-MM-DD`.
8. **Shared copies:** files with a *Provenance* line are copies. Change the original in
   `Gauntlet AI/` or the workspace `.claude/` first, then re-copy; keep the local adaptations listed in
   the setup profile.
9. **Reopen intake** when a change invalidates the brief audit or product direction. Say so to Innocent
   instead of quietly working around it.

## At the end of a run

- **Dev log:** one entry per meaningful outcome in `Gauntlet AI/devlogs/aea-callcenter/`, per
  `.claude/reference/dev-log.md`. One writer per run file.
- **Resume note:** update `.claude/state/resume.md` with the next action and open choices. Don't copy
  checklist status into it.
- **Check:** run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL.
