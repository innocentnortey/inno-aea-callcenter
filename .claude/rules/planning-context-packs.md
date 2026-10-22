> **Provenance:** copy of `Nortorious-Technologies/.claude/rules/planning-context-packs.md` (workspace rule, Build loop set), copied 2026-10-22. Change the original first, then re-copy.

# Planning → Give the Planner a Context Pack, Not a Search

Recorded 2026-10-21 at Innocent's instruction, after he saw planning agents using about 300,000 tokens each on
tickets that already hold a lot of information: "what context I need to give it so that it doesn't need to spend so
much time planning ... a Haiku explorer ... maybe a fan out explore agent ... cost is most important." Applies to every
project under Nortorious-Technologies whenever a planner (`fanout-planner`, `cerbo-ticket-planner`,
`equinox-ticket-planner`, a workflow script's `plan:` step) writes a plan for a ticket.

## What it looks like in practice

**Input:** ticket AEA-53 (a metrics reader). Its text cites about 250 KB of material: design sections, three OpenAPI
operations, decision records, the code it will sit beside.

**Old process:** one Opus planner searched for all of it. Measured on 53 AEA planners: about 106 turns, with the context
growing from 35k to about 300k tokens (AEA-53: 453k), and every turn re-reading the whole context so far, so about 10 million
tokens processed per planner (24.0M for AEA-53), 96% of it re-reading. Most reading went through hundreds of small
`sed` slices, and 17% of it was the planner reading back its own plan file.

**New process:** four Haiku explorers, each with its own set of paths, collect the material in parallel (2.8M tokens in
total). A script assembles one pack from their exact line spans. One Opus planner reads the ticket and the pack once and
writes the plan once: 14 turns, 2.5M tokens (AEA-53). About 5.2M tokens in all against 24.0M, and about 90% fewer Opus
tokens.

**Output:** the same kind of plan (it found the same blocker as the old plan), smaller (62 KB against 101 KB).

## The rules

1. **The cost is context times turns.** Every turn re-reads everything before it, so the cheap fix is keeping raw
   reading out of the planner's context, not a shorter plan.
2. **Explorers fan out by disjoint surface** and may read nothing outside their own paths. The ticket is the only file all
   of them read. A usable split: (a) contracts and the OpenAPI, (b) code signatures and table definitions from the code, (c)
   tests, repo state and file sizes, (d) decision records that *override* the ticket. Give each a short prompt.
3. **Use the built-in `Explore` agent type on Haiku.** It does not load `CLAUDE.md` or the rules, so its base context is
   about 24k, against 67k for a general-purpose agent. Check the model that actually ran (the agent's transcript records
   it): Haiku sweeps have silently run on another model before.
4. **Explorers return span indexes, not retyped text.** `Explore` is read-only and cannot write files. Each lists exact
   `path:start-end` ranges (and what each is for); a script assembles the pack by copying those lines. A hand-typed block
   is a defect: two SQL schema blocks were retyped in the first test and could not be trusted.
5. **Signatures come from the code, not from the contracts.** The contract form was wrong for two of eight signatures
   in the AEA-40 plan. For each module the ticket touches, the pack carries the real `class` and `def` lines from `main`
   (and from the ticket's branch when one exists), and a list of names that are in the ticket or a contract but not in code.
6. **Scope to the ticket's own surfaces.** The PRD, the coverage audit and the whole decision ledger are out. The ticket's
   acceptance criteria already encode them (the AEA-53 ticket cites R-35 four times and R-39 five times). Keep only decision
   entries that were changed at a later merge (the `Changed at merge` notes), because those can contradict the ticket. If a
   planner has to open the PRD to plan, that is a **ticket defect**: say so, add what was missing to the ticket, and do not
   widen the pack.
7. **State and sizes are part of the pack.** The explorer reports `git log` for `main` and the ticket's branch, which
   blockers have merged, existing tests with their skip reasons, and `wc -l` of every file touched against the size
   caps. Without these a planner writes "unverified" and misses a 1,002-line test file.
8. **A size target, never "no cap".** An explorer with no cap produced 574 KB (about 150,000 tokens) in one test.
   Aim for about 150 KB. Whole-document citations (all of DO-4) are dropped from the pack and listed under `DEFERRED`
   with exact line ranges, so the planner can open one span when it truly needs it.
9. **The planner works to a budget.** Read the ticket and the pack once, whole; read a deferred span only when needed, one
   read per span; no re-reading anything, including `CLAUDE.md`; write the plan once with a single Write call and never
   read it back; about 30 turns; a fact still missing goes under *Open items*, not into more exploring. Prefer one
   whole-file read to many slices.
10. **Verify the plan's signatures** before the implementer starts: a cheap agent checks every signature, path and test
    name in the plan against the code on `main` and the branch.
11. **Do not refresh a plan that still holds.** A refresh against a moved `main` edits only what changed. The AEA-53 refresh
    still cost 14.1M tokens.

## At ticket creation (the cheaper place to fix it)

A ticket should carry a **context manifest**: the exact documents and sections the planner must read, named by heading
or anchor (not line numbers, which drift), plus the symbols and tables it touches. Check at the end of ticket creation
that every entry resolves. Six ids cited by the AEA-53 ticket (OBS-18, 24, 26, 29, 31, 40) exist nowhere in the design
documents, and a check at creation would have caught that. A script can then resolve the manifest into the pack with no
model; the explorers cover only what the manifest cannot (current code, repo state, tests).

## What this does not change

- The plan is still implementer-ready: exact paths, copied signatures, named tests, every decision made.
- Plans still go to `NEEDS-DECISION` when they need an answer only Innocent can give.
- Fail-closed rules, frozen-test tamper checks and every project rule about secrets and live calls.

## Evidence and limits

Measured 2026-10-21 on the AEA Stage 8 build (token counts are from agent transcripts, re-reads included):

| Ticket | Old planner | New (pack) | Notes |
|---|---|---|---|
| AEA-40 | 100 turns, 29.3M tokens, final context 499k | 10 turns, 1.0M | single Haiku explorer, 5.7M; a reviewer judged the plan *sufficient with gaps* |
| AEA-53 | 89 turns, 24.0M, final context 453k | 14 turns, 2.5M | four Haiku explorers, 2.8M; plan found the same blocker as the old plan |

Limits: only two tickets were measured; the AEA-40 job was smaller than the old plan's (a merge and re-verify, as the branch was
already built); only AEA-40's plan was reviewed for quality; the AEA-53 pack was larger than it needs to be. Re-measure
when changing the pack, and revise this file with the numbers.

## How to apply

- **Orchestrators and workflow scripts** build the pack before dispatching the planner and pass its path in the planner's
  prompt, with rule 9 as the planner's instructions.
- **Ticket cutters** (`to-tickets`) add the context manifest and check that it resolves.
- **Projects** get a copy at zero-to-hero Stage 0 with the *Build loop* set. Change this original first, then re-copy.
