# Handoff · Run spike SP-1 on the VPS (System track)

**Written:** 2026-10-20, late evening CT, by the Mac session (`aea-investor-planning`). **For:** a Claude Code session
opened on the VPS in `/home/linuxuser/workspaces/inno-aea-callcenter`, on the **same model as the Mac session, Opus 5.5**
(`~/.claude/rules/match-model-on-vps.md`).

> **Update 2026-10-21, later:** after the Stage 6 gate the whole working copy moved to the VPS; the Mac copy is a snapshot. The ownership split below is history.
>
> **Update 2026-10-21 (Mac session):** SP-1 is done and synced back to the Mac. Innocent chose to run the §6 design on the
> **Mac** copy, so `docs/design/system-design.md` and the other §6 files are now Mac-owned. The VPS copy stays available for
> CPU-heavy runs; copy files across by hand when one is needed.

## Why the work is split this way

Innocent (2026-10-20): "sync this project to the vps' workspace, i will continue the ux session on here but i want to
use the vps cpu to run the spike". So:

| Copy | Track | Owns (writes) |
|---|---|---|
| **Mac** `~/Desktop/Nortorious-Technologies/inno-aea-callcenter` | UX track (session `aea-call-center-ux-stages`) and planning | `docs/ux/**`, `docs/artifacts/*ux*`, `docs/artifacts/_build/ux-planning/**`, the CON cards in `docs/ux/01-planning/USER_FLOWS.md` |
| **VPS** `/home/linuxuser/workspaces/inno-aea-callcenter` | System track: §5 spike SP-1, then §6 design | `docs/analysis/spikes/**`, `spikes/sp1/**`, spike branches `spike/SP-1-*`, later `docs/design/system-design.md` |

**Shared files** are the PRD, `PROJECT-CHECKLIST.md`, `.claude/state/resume.md`, the source register and
`docs/design/hard-problems.md`. Edit them on **one** side, then copy the change to the other in the same sitting. Say in
the dev log which side wrote. Nothing syncs automatically. The VPS copy was made by `rsync` from the Mac at the same
commit (`ed4ca89`) with identical uncommitted changes, and its `.venv` was rebuilt with `uv sync`.

## Read first

1. `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md`: the brief, options, measures and pass line. **Don't
   change the pass line.**
2. `docs/prd/inno-aea-callcenter-prd.md` (0.4, approved): §4 R-5–R-8, R-10/R-11, R-15–R-21, R-26, R-45–R-47, §5,
   §6.1–§6.2.
3. `docs/data/worked-pairs.md`: the *Required output* of WP-1…WP-8, including the revised WP-3, WP-4 and WP-6.
4. `docs/research/2026-10-20-vendor-and-framework-facts.md`:
   - prices (§2);
   - no forced `tool_choice` on Sonnet 5.5 (§1);
   - thinking on by default (§1);
   - a sync graph inside an `async def` endpoint blocks (§3);
   - the SDK's uncapped `retry-after` (§4).
5. `docs/design/hard-problems.md`: HP-1…HP-4 and *Spikes*.
6. Workspace rules: `.claude/rules/fanout-plan-then-implement.md`, `build-loop-test-scope.md` (light testing for
   spikes).

## Do

1. **Paid calls:** Innocent allowed **$10 in total** for SP-1 (2026-10-20). Follow the brief's run order (dry run with
   mocks first, then one live pass per option, then 20 at once, then repeats), and stop at the cap.
2. **Harness first** (spikes.md step 2): `spikes/sp1/harness/` runs any option config over the scripted conversations and
   prints the measures. Add a smoke test. Commit it on branch `spike/SP-1-base`. Committing is allowed by the spike
   procedure for spike branches only, never on `main`. Record its SHA in the brief §2.
3. **One build** (the options differ only in config): a `fanout-planner` writes `docs/plans/fanout/2026-10-20-sp1/build.md`,
   then a `fanout-implementer` builds `spikes/sp1/` on `spike/SP-1-build` (a worktree is allowed for spikes).
4. **Sweep:** run options A–D over the scripted pairs in the brief's run order, inside the $10 cap. **The orchestrator re-runs the harness itself**; builders' summaries are not trusted (tamper check:
   harness SHA unchanged).
5. **Write results** into the brief §3–§4: one table, option × measure, pass line marked. Write the recommendation using
   the decision rule. Append a dev-log entry in `Gauntlet AI/devlogs/aea-callcenter/` on the VPS, named
   `2026-10-20-sp1-vps-claude-01.md`.
6. **Report to Innocent** in plain words; he reads the result before Stage 6.

## Keys and services

- `.env` is copied, owner-only (600). It holds the Anthropic and OpenRouter keys (Terra, Gemini Flash and Jev go through
  OpenRouter). **Never print key values.**
- Measured on 2026-10-20: the Anthropic key is on the Start tier, with 1,000 requests, 2M input and 400K output tokens per
  minute, and a $500/month spend cap.
- Langfuse v4 runs on this VPS at `localhost:3100` (the YourAI stack). Tracing is optional for SP-1; don't put spike
  traces into YourAI's Langfuse project.
- Other projects' servers run here too. **Kill by PID, never by pattern** (memory `kill-by-pid-never-pattern-on-vps`).

## Don't

- Merge anything from a spike branch, or touch `main`'s product code.
- Edit the UX files or the CON cards: request changes from the UX session.
- Change the pass line, the PRD's decided requirements, or Innocent's decisions.
