# Plan — [AEA-36] graph: front node (gates, safety, identity)

**Status:** planned — READY; every prerequisite is on `main` (§9). **A build of this plan already exists** on branch
`aea-36-aea-36-front-node` (head `118e0a1`, which merges `main` `b559c75`), in the worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-36`. The build workflow **resumes** it: there is no test-writer
this round, and the implementer runs §0 role A. Read §0 first.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/36 · **Base revision:** `8a205b2`
(main at this refresh: "Merge fix: typing-only edits to AEA-29's frozen tests"). Since the last refresh, AEA-29, 30, 34,
38, 40 and 43 have merged, and `d724301` dropped the stale reply rows from `test_stubs_raise_loudly`. Refresh history:
first planned on `16ca639`; refreshed against `775f591` + `0a5b703`, `5531664`, `a81f59d` and `dd1b110`; fifth refresh
2026-10-21 against `8a205b2`. §10–§14 list what changed each time; §15 holds the deviations. **Planner:**
fanout-planner on `claude-opus-5-5`, 2026-10-21. **Test-writer:** `test-writer-agent` (Sonnet); done in `76fe4c2`.
**Implementer:** `fanout-implementer` (Sonnet).
**Lane:** `lane::build-loop`. **Risk:** `risk::security`. The test-writer froze `tests/unit/agent/nodes/test_front.py`
(every test in §7.1) in `76fe4c2`, before the implementer started. `security-privacy-agent` reads this diff at the
wave-2 merge.

Read this whole file before touching anything. Every name below was checked on 2026-10-21 against the code on `main`
`5531664`, and re-checked on `a81f59d`, `dd1b110` and `8a205b2`. §14 lists what moved on `8a205b2`. None of it changes
a name or signature this plan uses:
- `git diff b559c75 8a205b2` touches no file under `src/meridian/{domain,gates,policy}/` and none of
  `src/meridian/agent/{context,signals,routers,graph}.py`;
- AEA-29's real `HandoffService.open` has §4.4's signature;
- `tests/graph/test_spine.py` still holds the three `front` stub rows (§15 D-1 deletes them).

**Before coding, run §5 step 0. If a name differs on `main`, stop and report. Never write a local copy of a missing
type or function.**

---

## 0. Existing build on the branch (read first; rewritten in the fifth refresh)

An earlier run carried this plan through the test-writer and the implementer. A later run merged `main` `b559c75` and
re-ran the gates. The build workflow (`build8.js`, resume entry for ticket 36) now resumes the branch: **no
test-writer is dispatched**, and the implementer gets a resume note. What exists, checked by the planner on 2026-10-21
against `main` `8a205b2` (read only; the planner ran no test):

| Commit on `aea-36-aea-36-front-node` | Role | Content |
|---|---|---|
| `76fe4c2` `test(graph): frozen tests for the front node (AEA-36)` | test-writer | `tests/unit/agent/nodes/test_front.py` (1,043 lines; 16 test functions, 21 collected tests: §7.1). **Frozen.** `git log --format=%h -- tests/unit/agent/nodes/test_front.py` prints only `76fe4c2`. |
| `712b9e9` `feat(graph): front node — gates, safety, identity (AEA-36)` | implementer | `src/meridian/agent/nodes/front.py`. The planner read it line by line on this refresh: it matches §4.1 and §4.6–§4.8. It uses the `_as_locate` / `_as_send` / `_as_verify` variant that §4.8 allows, and a private `_signal()` builder for `SignalRecord`. |
| `377fa73` | implementer | J-5 journey file `tests/journeys/j5/test_aea_36.py` (= §7.6), the journey record `docs/testing/journeys/2026-10-21-AEA-36.md`, the area-map A7d row, the ICM routes row, the `**Built:**` line |
| `1c12482` | implementer | `docs/design/code-design.md` module-tree line → `built AEA-36 712b9e9` |
| `6a79b5a` | implementer | merge of `main` `dd1b110` |
| `20575f8` | implementer | merge of `main` `b559c75` (AEA-03b) |
| `118e0a1` `docs(AEA-36): journey record re-run after merging main` | implementer | Result line: on `20575f8`, `test_front.py` 21 passed; `tests/unit/agent tests/graph` 308 passed and 3 failed (the three `front` stub rows, R-1); J-5 `1 skipped` (`blocked-on AEA-30`) |

**Main has moved again** (`b559c75` → `8a205b2`; `git merge-base --is-ancestor main aea-36-aea-36-front-node` is false).
The planner ran `git merge-tree` on this merge. Its prediction:
- **One text conflict, in `.claude/reference/area-map.md` only.** Main changed the A7c row (AEA-38: `nodes/reply.py`,
  `prompts/reply.py` actual). The branch changed the A7d row directly below it.
- `.claude/state/icm-progress.md` and `docs/design/code-design.md` merge cleanly. The `**Built:** agent/nodes/front.py
  (AEA-36, 712b9e9).` line lands among main's new `**Built:**` lines.
- No source or test file conflicts.

**Role A: the implementer, in the existing worktree** `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-36`, on
`aea-36-aea-36-front-node`. In every shell: `export UV_LINK_MODE=hardlink`. First, `df -h /home`: under 4 GB free means
stop and return `LOW-DISK` (16 GB were free at this refresh). Then:

1. **Tamper check.** `git diff 76fe4c2 HEAD -- tests/unit/agent/nodes/test_front.py` prints nothing, and `git log
   --format=%h -- tests/unit/agent/nodes/test_front.py` prints only `76fe4c2`. Anything else: stop and report.
2. **Merge main.** `git status --short` must be empty. Run exactly `git merge --no-ff main -m "Merge main into
   aea-36-aea-36-front-node" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"`. Never rebase, amend or
   force-push.
   - Expected: exactly one conflict, in `.claude/reference/area-map.md`.
   - Resolve it to these two consecutive rows, and nothing else in the file changes:
     - main's A7c row, verbatim: ``| 3 | **A7c Reply** | Turn facts, responder, brief extraction, R-46 checks |
       `agent/nodes/reply.py`, `checks.py`, `agent/prompts/reply.py` | AEA-15, 38 | `checks.py` actual (AEA-15,
       `57883e6`); `nodes/reply.py`, `prompts/reply.py` actual (AEA-38, `ec94722`) |``
     - the branch's A7d row, verbatim: ``| 3 | **A7d Front** | Gate, safety, identity, planner and classifier nodes |
       `agent/nodes/{front,plan}.py`, `agent/prompts/routing.py` | AEA-36, 37 | planned; `agent/nodes/front.py`
       actual (AEA-36, `712b9e9`) |``
   - If main's A7d row has meanwhile changed (AEA-37 merged first), keep its words and append `; agent/nodes/front.py
     actual (AEA-36, `712b9e9`)`.
   - Then `grep -c '^<<<<<<<\|^>>>>>>>' .claude/reference/area-map.md` prints `0`.
   - Then `git add .claude/reference/area-map.md` and `git commit -m "Merge main into aea-36-aea-36-front-node" -m
     "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"`.
   - A conflict in any other file: run `git merge --abort`, stop and report the file.
   - After the merge, check three things. `grep -c 'AEA-36' docs/design/code-design.md` is at least 2: the module-tree
     line ends `built AEA-36 712b9e9`, and the `**Built:**` line appears exactly once. The ICM row whose evidence starts
     ``2026-10-21: area map A1 → `gates/gate.py` (AEA-12`` still names A7d and `712b9e9`. `git diff --name-only
     main...HEAD` lists exactly seven files: `src/meridian/agent/nodes/front.py`,
     `tests/unit/agent/nodes/test_front.py`, `tests/journeys/j5/test_aea_36.py`,
     `docs/testing/journeys/2026-10-21-AEA-36.md`, `.claude/reference/area-map.md`, `.claude/state/icm-progress.md` and
     `docs/design/code-design.md`. After step 4, `tests/graph/test_spine.py` makes eight.
3. **Step 0 (§5) on the merged tree.** Then `git diff 712b9e9 HEAD -- src/meridian/agent/nodes/front.py` must print
   nothing. Read `front.py` against §4.6–§4.8. Change nothing that already matches. If a line differs from §4 in
   behaviour, fix `front.py` only (never the frozen file). Commit it with the I-7 message shape and report what changed.
4. **Stale stub rows (deviation D-1, §15; standing permission relayed by the orchestrator).** Edit
   `tests/graph/test_spine.py`. Delete exactly these three lines of the `test_stubs_raise_loudly` parametrize list:
   ```
           (front, "gates", "front.py"),
           (front, "safety", "front.py"),
           (front, "identity", "front.py"),
   ```
   - Then change line 17 from `from meridian.agent.nodes import act, front, plan` to `from meridian.agent.nodes import
     act, plan`. `front` has no other use in that file; `grep -nw front tests/graph/test_spine.py` must print nothing
     afterwards.
   - If AEA-37 has merged first and line 17 already reads `from meridian.agent.nodes import act, front`, the line
     becomes `from meridian.agent.nodes import act`.
   - Change nothing else in the file (the `plan` and `act` rows stay while they are stubs). Never touch
     `tests/graph/_spine_doubles.py`: it still uses `front` as a module map.
   - Check: `uv run pytest tests/graph/test_spine.py -q` is all green.
   - Commit it alone with `git add tests/graph/test_spine.py`. Message: `test(graph): drop stale front-node rows from
     test_stubs_raise_loudly (AEA-36)`. Body: one paragraph saying AEA-36 (`712b9e9`) built gates, safety and identity,
     so they no longer raise "stub from AEA-21"; the three rows and the now-unused `front` import are removed; the plan
     and act rows are unchanged; no other assertion is touched; same pattern as `d724301`. Then a blank line, `Refs
     #36`, a blank line, and the Co-Authored-By line last.
   - Append the SHA to §15 D-1 of this plan file at
     `/home/linuxuser/workspaces/inno-aea-callcenter/docs/plans/fanout/2026-10-21-build/AEA-36.md` (main checkout; the
     orchestrator commits plan files). Do not commit the plan file.
5. **Gates G-1…G-7 (§7.3), cheapest first; stop at the first red.**
6. **Journey record.** Update `docs/testing/journeys/2026-10-21-AEA-36.md`:
   - Keep *Tested revision* `712b9e9`, unless step 3 changed `front.py`; then use the new SHA.
   - Append to *Result*: `Re-run on <merge sha> (main 8a205b2 merged; stale front stub rows removed in <D-1 sha>): <G-4
     line>; <G-5 line>; <G-6 line>; <G-7 line>.`
   - Set *Blocked by* from G-7's reason. It is expected to be `AEA-51 (reply_composer, run_graph)`, followed by `AEA-29,
     AEA-30 and AEA-40 are merged; AEA-57 is merged`.
   - Add to *Command* `uv run pytest tests/graph/test_spine.py -q`.
   - Commit it alone: `git add docs/testing/journeys/2026-10-21-AEA-36.md`, message `docs(AEA-36): journey record
     re-run after merging main 8a205b2`, then a blank line, `Refs #36`, a blank line, and the Co-Authored-By line last.
   - The context rows (I-9) stay as they are, unless step 3 changed `front.py`. In that case, update the three `712b9e9`
     SHAs (A7d row, ICM row, module-tree line and `**Built:**` line) to the new one in this same commit.
7. **Report per §7.5.**
   - Return `DONE` with the last commit SHA, and an `acResults` entry for each of AC-1…AC-14 with the command and the
     key line.
   - AC-13 is `verified=false` while G-7 is skipped (level `mock-tested`, blocked by AEA-51). Say so; this is the
     honest state, not a failure.

Steps I-2…I-10 and the test-writer's T-1…T-4 are already done on this branch. Do not redo them.

**Role B: a fresh worktree from `main` (only if the orchestrator discards the branch).** Follow §5 in full: T-1…T-4
(test-writer), then I-1…I-10 (implementer), then §0 step 4 (D-1). Do not cherry-pick from the old branch: the
frozen-test rule needs the test-writer's own commit on the new branch.

Either way, the orchestrator updates the ledger row; no role here edits `.claude/state/build-ledger.md`. **Neither role
merges into `main` or pushes.** The orchestrator merges this branch with the rest of its wave, following the dependency
tree in the slice plan (Innocent, 2026-10-21: merges follow the tree, not one ticket at a time). The merge-gate tests
then cover the union of the wave's diffs (rule `build-loop-test-scope`).

## 1. Goal and sources

### 1.1 Goal (the issue's *What to build*, `docs/plans/tickets/AEA-36.md`)

> **US-3:** "As a **homeowner** who smells gas, hears a CO alarm or sees sparks, smoke or flames, I need the safety
> instruction before anything else, so that I leave the home before I'm asked for a name or an account." (Also US-2,
> US-4, US-5, US-8.)

`src/meridian/agent/nodes/front.py` replaces AEA-21's stub in place with three LangGraph node functions:

- **`gates`** runs on every turn first: it asks AEA-12's `decide_gate` what kind of turn this is (safety phrase,
  burning smell, danger words, person, code, locate form, card choice, free text), records one `gate` check event, sets
  or clears the burning-question card id, and on a burning "no" writes a code-built booking plan.
- **`safety`** sends no model call and touches no identity or lookup. It emits `safety_reply_sent`, then opens the P0
  or P1 case by code through `deps.handoff.open`, retrying once; the instruction goes out whether or not the case write
  works. (The words themselves are composed later by AEA-21's compose from `policy/texts.py`.)
- **`identity`** turns a locate form or a code entry into the identity service's calls, passes the service's result
  through unchanged as `identity_step`, and re-reads `identity` from the database. The code digits and the form's name
  and phone are read only from `ctx.intake` and never copied anywhere.

**Worked pair WP-5 (what the code must do, concretely).** Input text `"My carbon monoxide detector is going off."` →
`gates` returns `gate = GateDecision(kind=SAFETY, rules.safety=CO, rules.rule_ids=("R5.co",))`, `check_events =
(CheckEvent(check="gate", turn_id=<this turn>, result="fired", codes=("safety", "R5.co")),)`, `burning_card_id = None`.
The router (AEA-21) sends the turn to `safety`, which emits one `signal` log record `{"record": "signal", "name":
"safety_reply_sent", "node": "safety", "cause": "safety", …ids…}` and calls `deps.handoff.open` exactly once with
`HandoffRequest(trigger="safety", reason=HandoffReason.SAFETY, priority=Priority.P0, safety_kind=SafetyKind.CO,
rule_id="R5.co", …)`; it returns `{"handoff": <HandoffResult>}`. Zero gateway, identity, retrieval, specialist-runner
and unit-of-work calls. Test: `tests/unit/agent/nodes/test_front.py::test_wp5_safety_p0_no_model_no_identity`.

**Second pair WP-6.** `"I need to schedule a service call. I smell something burning from the vents."` → `BURNING_ASK`,
`burning_card_id = "burn-<turn_id>"`, no case. A later `choice` with option `"not_sure"` on that card →
`BURNING_ANSWER` / `unsure` → the safety node opens a **P1** `burning_unclear` case. Option `"no"` → the gates node
writes the code-built plan (§4.6). Test: `::test_burning_and_danger_paths`, `::test_burning_no_writes_code_built_plan`.

### 1.2 Context

Wave 2, `risk::security` (the identity node handles the verification code and the locate form's name and phone, R-15).
Blocked by AEA-11, 12, 14, 21 in the slice plan. **All are merged (checked on `5531664` and again on `a81f59d`)** (AEA-21 at the merge commit itself;
its stub, `GraphDeps`, `emit_signal`, routers and compose match §4 exactly). AEA-57's harness is merged too, so this
ticket now writes its own J-5 journey file (§7.6), whose step reports *blocked* until AEA-51 binds `reply_composer` and
`run_graph` (AEA-29, AEA-30 and AEA-40 are merged on `8a205b2`). This plan does not use AEA-11's fakes (§9). `IdentityService` (AEA-27, **merged** at `13adc86`:
`src/meridian/services/identity.py`; its `locate`, `send_code`, `verify` signatures equal §4.4) and `HandoffService`
(AEA-29, **merged** at `ef561fc`: `src/meridian/services/handoff.py`; `open(self, req, ctx)` equals §4.4; it retries
once itself and raises `CaseWriteFailed`, §8 R-4) are still reached only through `GraphDeps` (whose `identity` and `handoff` fields stay `Any`
aliases on `8a205b2`) and are tested with doubles honouring DO-4 §14, §7 and graph-tools §5; `front.py` never imports
`meridian.services` (PA-1). GRC-3 and CAS-16 stand on option A (sign-off D-14).

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-36.md` (= issue #36) | AC-1…AC-14, owned files, WP-5, WP-6, WP-2 |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-36, §0a (J-5 "First landed by AEA-51; extended by 36, 37"), §3 collision map (`agent/nodes/*`: stub from 21, then one owner each) | Owned files; journey J-5; no edits to others' files |
| Code design (DO-3) | `docs/design/code-design.md` §2.1 (layers), §3 (`nodes/front.py`), §5.3 (key ownership: `gate` by gates; `handoff` also by `safety`; `identity_step`; `identity` again after a DB write), §5.4 (`G -->|safety · burning_ask · burning_answer · danger_rule| SF[safety]`), §7 rows R-5…R-8, R-15, R-16 | Node responsibilities, routing it relies on |
| Component contracts (DO-4) | `docs/design/contracts/internal-components.md` §1 (`IdentityState`, `CompletedAction`), §3 (`SafetyKind`, `RuleMatches`, `FormValues`, `Intake`, `GateKind`, `GateDecision`), §4 (`Plan`, `PlannedTask`, `TaskIntent`), §7 (`HandoffReason`, `HandoffRequest`, `HandoffResult`, `HandoffService.open`), §11 failure table, §14 (`IdentityService`), §16 (addenda win) | Every shape used |
| Addenda (win over DO-4) | `stage7/graph-nodes.md` §1 (`CheckEvent.from_gate`), §4 (`SignalRecord`, `safety_reply_sent`, `case_write_failed`), §6 (burning "no"), §7 (CAP-2), §9.1 (`GatesUpdate`, `SafetyUpdate`, `IdentityNodeUpdate`), §9.3 (signatures); `stage7/graph-core.md` §2 (`TurnContext.intake`, rules 1–4), §3 (`GateFlags`, card ids, `decide_gate` order, `gate_result()` table, R-G-11), §4 (`GraphDeps`, `timed_node`, `agent/signals.py`), §8, §11 (`check_events`, edge 2, `route_act_plan`); `stage7/graph-tools.md` §5 (`Locator`, result types, CON-2 codes, GRT-3); `stage7/cases.md` §1.2 (`core.reads.identity_state`), §1.5 (`temp_sqlite`), §3.2–§3.3 (`promise_for`, `priority_for`), §5 (`HandoffService.open`, idempotent per thread) | Signatures, event and signal shapes, priorities |
| Decision ledgers | `docs/plans/7b-decisions/graph-core.md` GRC-3, 4, 5, 6, 10, 18; `graph-nodes.md` GRN-2, 4, 5, 6, 9, 11; `graph-tools.md` GRT-3, 5; `cases.md` CAS-16; `residuals-graph.md` R-G-11 | Folded into the addenda |
| Decisions taken | `docs/plans/stage7-signoff.md` D-14 (Innocent, 2026-10-21: "ill take all your recommendations") | GRC-3 = A (safety before AI-paused), CAS-16 = A (`burning_ruled_out`, P2 in AEA-14) |
| Sibling plans (read only) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0–§4.10; `AEA-05.md` PD-6 (rule ids, safety first); `AEA-10.md` §4 (`ReadsRepo.identity_state`, `TempStore`, `temp_sqlite`), step 6, DDL `40_identity.sql`; `AEA-12.md` §4, algorithm D (D-1…D-12), C; `AEA-14.md` step 4 (`_PRIORITY`), R-4 (`R7.burning_ruled_out`); `AEA-21.md` §4.4 (`GraphDeps`, PD-7 `Any` aliases), §4.5 (`emit_signal`), §4.7 (routers), §4.10 (compose reads), §4.12 (stub signatures), §6, §7.1 (`test_stubs_raise_loudly`); `AEA-27.md` R-5, R-6; `AEA-29.md` step 4 (`HandoffService.open` retries once, raises `CaseWriteFailed`), §3b O-17, R-6; `AEA-34.md` R-1 (stub-test guard); `AEA-37.md` step 12 (shared A7d row) | Exact import paths and behaviours |
| Requirements | PRD R-2, R-5, R-6, R-7, R-8, R-15, R-16, R-47; HP-2; WP-2, WP-5, WP-6 | Safety first; no contact ask; burning paths; identical `NOT_VERIFIED` |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` E-1 (WP-5, WP-6 hard gates; "nothing private before the code" for WP-2), E-5 (safety slice) | Kept passing at AEA-51; nothing run here |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-1 *Records* `check_event`, `turn.gate_result`; CAP-2 | One `gate` event per turn; signals codes-only; no model span on the safety path (proved by AEA-51) |
| Key metrics (DO-7) | M-14, M-15, M-16, M-17, M-21, M-22 | Computable from `gate`, the `gate` event and the P0/P1 case rows; no target here |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md` 3, 6; workspace `code-design-solid-modularity`, `context-management-multi-turn` | Frozen tests first; affected tests only; journey record; context rows |

**Context-management rule 3 does not apply:** these three nodes render no model prompt (no gateway call at all).

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files any role may create or edit)

| File | Who | Create / modify | What |
|---|---|---|---|
| `tests/unit/agent/nodes/test_front.py` | **test-writer** (frozen after its commit) | create | every test in §7.1, with its doubles and builders inside the file |
| `tests/unit/agent/nodes/__init__.py` | test-writer | create **only if absent**, 0 bytes (`touch`) | package marker (AEA-21 normally creates it) |
| `src/meridian/agent/nodes/front.py` | implementer | modify (replace AEA-21's stub in place) | `gates`, `safety`, `identity` and private helpers (§4.6–§4.8) |
| `tests/journeys/j5/test_aea_36.py` | implementer (not frozen: it is AC-13's journey, not a security test) | create | the J-5 step of §7.6 on AEA-57's harness |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-36.md` | implementer | create (date = `TZ=America/Chicago date +%F`) | AC-13 record (§7.4) |
| `.claude/reference/area-map.md` | implementer | edit the **A7d row's Status cell** only | AC-14 |
| `.claude/state/icm-progress.md` | implementer | edit the **evidence cell of one "Routes verified against code and tests" row** only | AC-14 |
| `docs/design/code-design.md` | implementer | edit the **`**Built:**` line under `## 3`** only | AC-14 |
| `tests/graph/test_spine.py` | implementer | modify **only**: delete the three `front` rows of `test_stubs_raise_loudly` and drop `front` from the line-17 import (§0 step 4) | deviation D-1 (§15) |

### 2.2 Shared surfaces read, never edited

`pyproject.toml`, `uv.lock`, `tests/conftest.py`, every `__init__.py` other than the marker above,
`src/meridian/domain/*`, `src/meridian/ports/*`, `src/meridian/policy/*` (incl. `handoff.py`, `texts.py`, `limits.py`),
`src/meridian/gates/*`, `src/meridian/agent/{graph,routers,context,signals}.py`, `src/meridian/agent/nodes/{compose,
load_context,plan,act,reply}.py`, `src/meridian/adapters/**`, `src/meridian/services/**`, `src/meridian/web/**`
(incl. `container.py`: **this ticket has no `register_<x>()` hunk**), `tests/fixtures/sqlite.py`, `tests/fakes/**`,
`tests/graph/**` (except §2.1's `test_spine.py` row), `tests/journeys/**`, `docs/design/contracts/**`, the OpenAPI file, `UI_CONTRACTS.md`, `docs/ux/**`,
`apps/web/**`, the briefing, issued data, `docs/archive/**`, `docs/parked/**`.

### 2.3 Owned by other tickets — do not create or change

Routing (`route_after_gates`, `route_act_plan`, … — AEA-21), every customer sentence and block (compose, AEA-21;
texts, AEA-03), `decide_gate` / `parse_intake` / `flags_from_state` / `burning_card_id` (AEA-12), the word rules
(AEA-05), `priority_for` / `promise_for` (AEA-14), the person-request handoff (AEA-39's `handoff` node), planner and
classifier (AEA-37), booking (AEA-28/35/39), `IdentityService` (AEA-27), `HandoffService` / `CaseService` (AEA-29),
`load_context` (AEA-34), `GraphDeps` fields (AEA-21), `tests/journeys/support/**` (AEA-57; a missing helper is a
follow-up on AEA-57, never an edit here), `tests/journeys/j5/__init__.py` (exists), every other `tests/journeys/j*/` file.

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's) → implementation → verification

All tests are in `tests/unit/agent/nodes/test_front.py`, written and frozen by the test-writer (§7.1). Command for every
row: `uv run pytest tests/unit/agent/nodes/test_front.py -q -rA` (or `::<name>`).

| AC | Requirement (issue text abridged; full text in the issue) | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | Gates runs `decide_gate(ctx.intake, flags_from_state(state))` every turn, returns only `GatesUpdate` keys; a typo'd CO phrase on turn 5 of a booking chat with an open task → `SAFETY` | §4.6 G-1…G-6 | `::test_gate_first_every_turn_mid_chat` (real AEA-12 `decide_gate`) |
| AC-2 [invariant] | Exactly one `CheckEvent` (`check="gate"`, this turn, `codes=(GateKind value, *rule_ids)`; `fired` WP-5, `pass` plain text); `burning_card_id` = `"burn-<turn_id>"` after `BURNING_ASK`, None after any other | §4.6 G-3, G-4 | `::test_gate_event_and_burning_card_id` |
| AC-3 [invariant] | Burning "no" → the code-built plan; no other gate writes `plan` | §4.6 G-5, `_burning_ruled_out_plan` | `::test_burning_no_writes_code_built_plan` |
| AC-4 [invariant] | WP-5: one `deps.handoff.open` with `trigger="safety"`, `reason="safety"`, `priority="P0"`, `safety_kind="co"`; zero gateway, identity, retrieval, runner calls; returns the `HandoffResult` | §4.7 S-1…S-6 | `::test_wp5_safety_p0_no_model_no_identity` (**WP-5 worked pair**) |
| AC-5 [invariant] | Burning yes → P0 `safety`; unsure → P1 `burning_unclear`; `DANGER_RULE` → P1 `danger`; classifier `danger` → P1 `danger`; classifier `burning_unclear` → P1 `burning_unclear`; `BURNING_ASK` opens no case | §4.7 `_safety_path` table | `::test_burning_and_danger_paths` (table-driven, real AEA-14 `priority_for`; **WP-6 worked pair** rows) |
| AC-6 [failure/refusal] | Failed write retried once; recovered → result + `case_write_failed(attempt=2, recovered=True)`; both fail → no `handoff`, no `halt`, `case_write_failed(recovered=False)`, `safety_reply_sent` still emitted | §4.7 S-5 `_open_case` | `::test_safety_case_write_retried_once_instruction_kept` (caplog on `meridian.signal`) |
| AC-7 [invariant] | GRC-3 A: `controller.kind == "human"` + CO alarm → safety node, one `open`, idempotent `created=False` result returned | §4.6 (real `decide_gate`, A order), §4.7 | `::test_safety_while_representative_owns_chat` |
| AC-8 [invariant] | WP-2: locate form → `Locator.from_form` → `locate` → `send_code` in one turn; `identity_step` = `CodeSent` (hint "the phone ending in 02"); code turn → `verify(ctx.ids, digits, ctx.now)` → `Verified`; `identity` = `core.reads.identity_state` in a read-only unit of work | §4.8 I-1…I-7 | `::test_wp2_locate_send_verify` (**WP-2 worked pair**; identity double; AEA-10 `temp_sqlite()`) |
| AC-9 [failure/refusal] | No match / ambiguous / no contact / incomplete form → byte-identical `NotVerified`; `CodeWrong`, `CodeExpired`, `CodeLocked`, `CodeCapReached` passed through; `new_code` → `send_code`, not `verify` | §4.8 I-3, I-4, `_checked` | `::test_identity_results_passed_through` |
| AC-10 [negative] | Code digits and the form's phone and name never in state, a return value, a signal or a log; 0 gateway calls | §4.8 I-6 (read only from `ctx.intake`), no logging in `front.py` | `::test_code_and_form_values_never_leave_intake` (caplog) |
| AC-11 [invariant] | Key ownership: gates ⊆ {`gate`, `check_events`, `burning_card_id`, `plan`(burning "no" only)}; safety ⊆ {`handoff`}; identity ⊆ {`identity_step`, `identity`} | §4.6–§4.8 return statements | `::test_front_nodes_write_only_own_keys` |
| AC-12 [capture] | `gate` event codes-only; `safety_reply_sent` carries `turn_id`, `thread_id`, `request_id`, `run_tag`, `node="safety"`, cause (`safety` / `danger`); a sentinel phrase absent from both | §4.6 G-3, §4.7 S-3 | `::test_check_event_and_signal_records` (caplog) |
| AC-13 [journey] | Extends J-5 in `tests/journeys/j5/test_aea_36.py` on AEA-57's harness at level `integrated with a scripted model`; until the services it needs are bound, the record states `mock-tested` and *Blocked by* their owners | §7.6 journey file (AEA-57 is merged; the step is reported blocked by the harness until AEA-51 binds `reply_composer` and `run_graph`; AEA-29, 30, 40 are merged); §7.4 record | `uv run pytest -m journey tests/journeys/j5/test_aea_36.py -rs` (1 skipped `blocked-on AEA-NN`, 0 failed; or 1 passed once all are bound); `docs/testing/journeys/<date>-AEA-36.md` |
| AC-14 [regression/context] | Area map A7d row, ICM row, DO-3 §3 `**Built:**` line in the diff, only this ticket's rows | §5 step I-9 | `git diff --name-only main...HEAD` and `git diff main...HEAD -- .claude/ docs/design/code-design.md` |

### 3.2 Plan-added criteria (the issue gets a comment proposing them; the test-writer freezes them too)

| ID | Criterion | Why | Test |
|---|---|---|---|
| PA-1 | `front.py` imports only the allowed modules (§4.1), imports `decide_gate`, `flags_from_state`, `burning_card_id`, `priority_for`, `emit_signal`, and never imports `logging`, `sqlite3`, `meridian.services`, `meridian.adapters`, nor calls `print` | AC-10 holds by construction (no log path exists); DO-3 §2.1 (nodes reach services only through `deps`) | `::test_front_module_imports` |
| PA-2 | Identity node reached with no locate form and no code (gate `FREE_TEXT`, `CARD_CHOICE` or burning "no" through `route_act_plan`; or a code-card choice other than `new_code`) calls no service and returns `{}` | The router sends plans that need identity to this node (AEA-21 `route_act_plan`); compose then shows the locate prompt (AEA-21 §4.10 D-6). No service call without the customer's own form or code | `::test_identity_without_form_or_code_calls_nothing` |
| PA-3 | Safety node on an impossible route (`FREE_TEXT` with no raise; `BURNING_ANSWER` "no") raises `ValueError` and makes no call; on `BURNING_ASK` it returns `{}` with no call and no signal | AC-5's "BURNING_ASK opens no case" given that DO-3 §5.4 / AEA-21 route `BURNING_ASK` through `safety` (R-1); a router bug fails loudly instead of opening a wrong case | `::test_safety_refuses_non_safety_paths` |
| PA-4 | The safety case's `rule_id`: first fired rule id for `SAFETY` / `DANGER_RULE`; `R7.burning_yes`, `R7.burning_unsure`, `R47.classifier_danger`, `R47.classifier_burning_unclear` where no rule fired | Ticket: "a stable id the plan names"; AEA-05 PD-6 style `^(R\d+|OD\d+)\.[a-z_]+$` | asserted in `::test_burning_and_danger_paths` and `::test_wp5_safety_p0_no_model_no_identity` |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Gate first on every turn, typos, mid-chat | R-5, R-47; graph-core §3 | yes | in-ticket AC-1 | §4.6 |
| One `gate` event per turn, codes only | graph-nodes §1, GRN-2/5; DO-6 `check_event` | yes | in-ticket AC-2, AC-12 | §4.6 G-3 |
| `burning_card_id` only writer, set/cleared | graph-core §3 GRC-4, R-G-11 | yes | in-ticket AC-2 | §4.6 G-4 |
| Burning "no" code-built plan, `needs_identity=True`, `burning_ruled_out` | graph-nodes §6, GRN-6, GRC-18; CAS-16 A (D-14) | yes | in-ticket AC-3 | §4.6 G-5 |
| No model, no identity, no lookup on the safety path; no contact ask | R-6, CAP-2, graph-nodes §7 | yes | in-ticket AC-4; CAP-2 at the real entry point is other-ticket AEA-51 | §4.7 |
| P0/P1 by `priority_for`, never typed here | cases §3.3 | yes | in-ticket AC-4, AC-5 | §4.7 S-4 |
| `safety_reply_sent` before the case; `case_write_failed` after one retry | graph-nodes §4 table; DO-1 §8.2 | yes | in-ticket AC-6, AC-12 | §4.7 S-3, S-5 |
| Instruction sent even if the case write fails (no halt) | DO-1 §8.2 *Safety turn*; DO-4 §7 | yes | in-ticket AC-6 | §4.7 S-5, S-6 |
| GRC-3 A: safety beats AI-paused | graph-core §3 step 0; D-14 | yes | in-ticket AC-7 (order lives in AEA-12's tuple) | §4.6 (no own logic) |
| Who retries the safety case write: AEA-29's `HandoffService.open` retries once and raises `CaseWriteFailed` (its step 4, AC-6); the node also retries once | DO-4 §7 comment under `HandoffService`; graph-nodes §4 (the node emits after "the one retry") | AC-6 | **in-ticket** AC-6 kept as written: the node catches `Exception` (never imports `CaseWriteFailed`); the stacked-retry cost is accepted by AEA-29 R-6 and reported in R-4 | §4.7 S-5; §8 R-4 |
| `BURNING_ASK` reaches the safety node by DO-3 §5.4 routing | DO-3 §5.4 diagram; AEA-21 §4.7 step 4 | contradicts AC-5's wording "never reaches" | **added** PA-3 (node returns `{}`, no case, no signal: AC-5's evidence holds); issue comment | §4.7 S-2 |
| Identity node reached via `route_act_plan` without a form or code | graph-core §11 edge 2; AEA-21 `route_act_plan` | no | **added** PA-2 | §4.8 I-5 |
| `rule_id` where no rule fired | ticket ("a stable id the plan names") | partly | **added** PA-4 | §4.7 `_safety_path` |
| Identity results never re-grouped; CON-2 mapping in compose | graph-tools §5, GRT-3 | yes | in-ticket AC-9; mapping is other-ticket AEA-21 (PA-1 of its plan) | §4.8 |
| Digits/form values only from `ctx.intake`; never in state, return, log, trace | R-15; graph-core §2 rules 1–3, GRC-10 | yes | in-ticket AC-10; checkpoint-wide sentinel test is other-ticket AEA-51 (graph-core §2 rule 4) | §4.8 I-6; PA-1 |
| `identity` re-read after the service's write, read-only tx | DO-3 §5.3; cases §1.2 | yes | in-ticket AC-8 | §4.8 I-7 |
| `send_code` gets the conversation's own `demo_session` | AEA-27 R-6; DO-4 §14 | yes | in-ticket (`ctx.demo_session`) | §4.8 I-3, I-4 |
| `identity_failures` counted from `identity_step` | graph-core §8 | n/a here | other-ticket AEA-38 (facts) | — |
| CON-2 error codes, blocks, wording | graph-tools §5; `policy/texts.py` | no wording here | other-ticket AEA-21 / AEA-03 | — |
| Node spans | graph-core §4 `timed_node` | yes | other-ticket AEA-21 (nodes never call `TraceSink`) | — |
| E-1 / E-5 slices, CAP-2 | DO-5, DO-6 | yes | other-ticket AEA-51 (kept passing there) | — |
| AEA-21 `test_stubs_raise_loudly` goes red when the front stub is replaced | AEA-21 plan §7.1 | no | **resolved by deviation D-1** (§15): the three `front` rows are deleted on this branch | §0 step 4 |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (graph nodes inside WF-1, reached through CON-2 → `run_graph`) | WF-1 | yes (DO-6 WF-1) | E-1, E-5; M-14…M-17, M-21, M-22 |

---

## 4. Shared code to use (exact shapes)

### 4.0 Module rules for `front.py`

1. Module docstring first, then `from __future__ import annotations`. Absolute imports only. One statement per line
   (ruff E702). Mypy strict with `init_typed = true`: build enums with members (`HandoffReason.SAFETY`), IDs with their
   classes.
2. No module-level instances other than immutable constants (strings, tuples, `MappingProxyType`). No clock read, no
   settings, no logger, no `print`, no `logging` import (PA-1).
3. Errors this module raises carry codes and names only, never a customer value, never `ctx.intake` content.
4. `__all__ = ["gates", "identity", "safety"]`.

### 4.1 Imports `front.py` uses (and nothing else; PA-1 checks the module set)

```python
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.signals import emit_signal
from meridian.domain.handoff import HandoffReason, HandoffRequest, HandoffResult
from meridian.domain.identity import (
    CodeCapReached,
    CodeExpired,
    CodeLocked,
    CodeSent,
    CodeWrong,
    IdentityStep,
    Located,
    Locator,
    NotVerified,
    Verified,
)
from meridian.domain.state import ConversationState, GatesUpdate, IdentityNodeUpdate, SafetyUpdate
from meridian.domain.turn import (
    CheckEvent,
    DangerAssessment,
    GateDecision,
    GateKind,
    Plan,
    PlannedTask,
    SignalName,
    SignalRecord,
    TaskIntent,
    TurnContext,
)
from meridian.gates.gate import burning_card_id, decide_gate, flags_from_state
from meridian.policy.handoff import priority_for
```

**Allowed module set (PA-1):** `__future__`, `dataclasses`, `types`, `typing`, `langgraph.runtime`,
`meridian.agent.context`, `meridian.agent.signals`, `meridian.domain.handoff`, `meridian.domain.identity`,
`meridian.domain.state`, `meridian.domain.turn`, `meridian.gates.gate`, `meridian.policy.handoff`. If AEA-02 put a
listed name in a different `meridian.domain.*` module, import it from there and report it; the test-writer's allowlist
treats any `meridian.domain.*` module as allowed (§7.1 PA-1).

### 4.2 Types consumed (AEA-02; copied from its plan §4.1–§4.10 and the addenda)

```python
# domain/common.py, re-exported from domain/handoff.py
class HandoffReason(StrEnum):   # 16 values incl. BURNING_RULED_OUT = "burning_ruled_out" (CAS-16 A)
    SAFETY = "safety"; DANGER = "danger"; BURNING_UNCLEAR = "burning_unclear"; ...; BURNING_RULED_OUT = "burning_ruled_out"
class Priority(StrEnum): P0 = "P0"; P1 = "P1"; P2 = "P2"; P3 = "P3"; P4 = "P4"
class SafetyKind(StrEnum): GAS = "gas"; CO = "co"; SPARKS_SMOKE_FLAMES = "sparks_smoke_flames"; BURNING_WITH_BREAKER = "burning_with_breaker"
    # re-exported from domain/turn.py

# domain/handoff.py
class HandoffRequest(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    reason: HandoffReason
    priority: Priority
    rule_id: str
    trigger: Literal["gate", "escalation", "con4", "safety"]
    identity: IdentityState
    change_request: ChangeRequestDraft | None = None
    safety_kind: SafetyKind | None = None
class HandoffResult(MeridianModel):
    case: CaseSummary
    created: bool
    action: CompletedAction
    alert: Literal["supervisor_now"] | None
class CaseSummary(MeridianModel):   # tests only
    case_ref: CaseRef; reason: HandoffReason; priority: Priority; state: CaseState; created_at: dt.datetime
    promise: Promise; followup: FollowUp | None; version: int; seed: bool = False; due_at: dt.datetime | None

# domain/identity.py
class FormValues(MeridianModel): name: str | None = None; phone: SecretStr | None = None
    customer_id: CustomerId | None = None; invoice_number: InvoiceId | None = None; zip_or_city: str | None = None
class Locator(MeridianModel):
    name: str | None = None; phone: SecretStr | None = None
    customer_id: CustomerId | None = None; invoice_number: InvoiceId | None = None
    @classmethod
    def from_form(cls, form: FormValues) -> Locator | None: ...   # None when no complete locator; never raises
class Located(MeridianModel):        kind: Literal["located"] = "located"; masked_hint: str
class NotVerified(MeridianModel):    kind: Literal["not_verified"] = "not_verified"          # no other field
class CodeSent(MeridianModel):       kind: Literal["code_sent"] = "code_sent"; masked_hint: str; expires_at: dt.datetime; sends_left: int = Field(ge=0, le=2)
class CodeCapReached(MeridianModel): kind: Literal["code_cap_reached"] = "code_cap_reached"
class Verified(MeridianModel):       kind: Literal["verified"] = "verified"; customer_id: CustomerId; action: CompletedAction
class CodeWrong(MeridianModel):      kind: Literal["code_wrong"] = "code_wrong"; tries_left: int = Field(ge=1, le=2)
class CodeExpired(MeridianModel):    kind: Literal["code_expired"] = "code_expired"; resend_offered: bool; sends_left: int = Field(ge=0, le=2)
class CodeLocked(MeridianModel):     kind: Literal["code_locked"] = "code_locked"
IdentityStep = Annotated[Located | NotVerified | CodeSent | CodeCapReached | Verified | CodeWrong | CodeExpired | CodeLocked,
                         Field(discriminator="kind")]
class IdentityState(MeridianModel):  # re-exported from domain/state.py
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None; masked_hint: str | None; code_expires_at: dt.datetime | None
    tries_left: int = Field(ge=0, le=3); codes_sent: int = Field(ge=0, le=3); verified_at: dt.datetime | None

# domain/turn.py
class CardChoice(MeridianModel): card_id: str; option: str
class Intake(MeridianModel):
    kind: Literal["text", "choice", "code", "form"]; text_store: str; code_digits: SecretStr | None
    form: FormValues | None; card_number_seen: bool; choice: CardChoice | None; card_id: str | None = None
class TurnIds(MeridianModel): thread_id: ThreadId; turn_id: TurnId; request_id: RequestId
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; agent_version: str
@dataclass(frozen=True)
class TurnContext: ids: TurnIds; budget: TurnBudget; now: dt.datetime; demo_session: str; span: SpanHandle
    intake: Intake | None = None
class RuleMatches(MeridianModel): safety: SafetyKind | None; burning_unclear: bool; danger_words: bool; person: bool
    policy_trigger: HandoffReason | None; rule_ids: tuple[str, ...]; correction: bool
class GateKind(StrEnum): AI_PAUSED = "ai_paused"; SAFETY = "safety"; BURNING_ASK = "burning_ask"
    BURNING_ANSWER = "burning_answer"; DANGER_RULE = "danger_rule"; PERSON = "person"; CODE_ENTRY = "code_entry"
    LOCATE = "locate"; CARD_CHOICE = "card_choice"; FREE_TEXT = "free_text"
class GateDecision(MeridianModel): kind: GateKind; rules: RuleMatches
    burning_answer: Literal["yes", "no", "unsure"] | None = None; resume_task_id: str | None = None
    def gate_result(self) -> GateResult: ...   # SAFETY→"safety"; BURNING_ASK→"burning_unclear";
        # BURNING_ANSWER yes→"safety", unsure→"burning_unclear", no→"clear"; DANGER_RULE→"danger"; PERSON→
        # "person_requested"; AI_PAUSED→"ai_paused"; CODE_ENTRY, LOCATE, CARD_CHOICE, FREE_TEXT→"clear"
class DangerAssessment(MeridianModel): label: Literal["normal", "burning_unclear", "danger"]; raised: bool
    confidence: float | None = None; failure: ProviderFailure | None
class TaskIntent(StrEnum): ...; BOOK_NEW = "book_new"; ...
class PlannedTask(MeridianModel): order: int = Field(ge=1, le=3); specialist: Literal["knowledge", "account", "scheduling"]
    intent: TaskIntent; needs_identity: bool; resumes_task_id: str | None = None
class Plan(MeridianModel): mode: Literal["talk", "act"]; tasks: tuple[PlannedTask, ...] = Field(max_length=3)
    handoff_request: HandoffReason | None; topic: Literal["booking", "membership", "billing", "warranty", "other"]
    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]; planner_failed: bool = False
class CheckEvent(MeridianModel): check: CheckKind; turn_id: TurnId; result: Literal["pass", "trimmed", "fallback", "fired", "raised"]
    removed: int = 0; claim_kinds: tuple[str, ...] = (); codes: tuple[str, ...] = ()
    @classmethod
    def from_gate(cls, turn_id: TurnId, gate: GateDecision) -> CheckEvent: ...
        # check="gate"; result "fired" if gate.kind ∉ {FREE_TEXT, CODE_ENTRY, LOCATE, CARD_CHOICE} or rule_ids
        # non-empty, else "pass"; codes = (gate.kind.value, *gate.rules.rule_ids)
class SignalName(StrEnum): SAFETY_REPLY_SENT = "safety_reply_sent"; CASE_WRITE_FAILED = "case_write_failed"; ...
class SignalRecord(MeridianModel):
    record: Literal["signal"] = "signal"; name: SignalName; turn_id: TurnId; thread_id: ThreadId; request_id: RequestId
    run_tag: Literal["live", "eval", "load"]; node: str; cause: str | None = None
    role: Literal["planner", "classifier", "specialist", "responder", "brief"] | None = None
    specialist: Literal["knowledge", "account", "scheduling"] | None = None
    attempt: int | None = None; recovered: bool | None = None

# domain/state.py
class Controller(MeridianModel): kind: Literal["ai", "human"]; representative_name: str | None = None; case_ref: CaseRef | None = None
class ConversationState(MeridianModel):   # keys read here: thread_id, controller, identity, open_tasks,
    # burning_card_id, turn_input, gate, danger. identity defaults to not_checked; controller to Controller(kind="ai").
    # All 25 keys on 775f591, in order: thread_id, settled, controller, identity, open_tasks, shown_slots, counters,
    # burning_card_id, turn_input, chat_window, gate, planner, danger, plan, identity_step, specialist_results,
    # escalation, handoff, facts, draft, brief_extraction, checked, reply, halt, check_events.
    # turn_input is REQUIRED (no default): every test state must set it (§6 `_state`).
class GatesUpdate(TypedDict, total=False):
    gate: GateDecision; check_events: tuple[CheckEvent, ...]; plan: Plan; halt: Halt; burning_card_id: str | None
class SafetyUpdate(TypedDict, total=False):
    handoff: HandoffResult; halt: Halt
class IdentityNodeUpdate(TypedDict, total=False):
    identity: IdentityState; identity_step: IdentityStep; halt: Halt
```

### 4.3 Functions consumed (signatures copied)

```python
# meridian.gates.gate (AEA-12) — pure
def flags_from_state(state: ConversationState) -> GateFlags: ...
def decide_gate(intake: Intake, flags: GateFlags) -> GateDecision: ...   # graph-core §3 order; GRC-3 A tuple GATE_ORDER_HEAD
def burning_card_id(turn_id: TurnId) -> str: ...                           # "burn-<turn_id>"
def parse_intake(payload: TurnPayload) -> Intake: ...                       # tests only (builds realistic intakes)

# meridian.policy.handoff (AEA-14) — pure
def priority_for(reason: HandoffReason, *, promise_due: datetime | None = None,
                 renewal_date: date | None = None) -> Priority: ...       # SAFETY P0; DANGER, BURNING_UNCLEAR P1
def promise_for(reason: HandoffReason, presence: Presence, now: datetime,
                window_start: datetime | None = None) -> Promise: ...      # tests only (to build HandoffResult doubles)

# meridian.agent.signals (AEA-21)
def emit_signal(ids: TurnIds, record: SignalRecord) -> None: ...
    # raises ValueError if record.turn_id/thread_id differ from ids; logs logger "meridian.signal", message "signal",
    # extra={"signal": record.model_dump(mode="json")}

# meridian.agent.context (AEA-21)
@dataclass(frozen=True)
class GraphDeps:   # fields in this order: gateway, retrieval, uow, identity, scheduling, handoff, brief, demo, limits,
                   #   trace, specialists, cases, ledger. identity and handoff are typed `Any` aliases until AEA-27/29/51.
```

### 4.4 Injected services (DO-4 §14, §7; graph-tools §5) — called only through `deps`

```python
# deps.identity — IdentityService (AEA-27); each method opens and commits its own transaction
def locate(self, thread_id: ThreadId, locator: Locator, now: datetime) -> Located | NotVerified: ...
def send_code(self, thread_id: ThreadId, demo_session: str, now: datetime) -> CodeSent | NotVerified | CodeCapReached: ...
def verify(self, ids: TurnIds, digits: SecretStr, now: datetime) -> Verified | CodeWrong | CodeExpired | CodeLocked: ...

# deps.handoff — HandoffService (AEA-29); one write transaction; idempotent per thread (created=False → existing case)
def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ...

# deps.uow — UnitOfWorkFactory (ports/runtime.py); default write=False → BEGIN DEFERRED + query_only
def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
# tx.core.reads.identity_state(thread_id: ThreadId) -> IdentityState      (AEA-10, cases §1.2)
```

### 4.5 Node signatures (graph-nodes §9.3; must stay exactly as AEA-21's stub has them)

```python
def gates(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> GatesUpdate: ...
def safety(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> SafetyUpdate: ...
def identity(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> IdentityNodeUpdate: ...
```

Parameter names `state`, `runtime`, `deps` are load-bearing (LangGraph injects `runtime` by name; AEA-21 binds
`deps` with `functools.partial`). `ctx = runtime.context` is the `TurnContext`.

### 4.6 `gates` — algorithm (invariant in *italics*)

- **G-1.** `ctx = runtime.context`. If `ctx.intake is None` → `raise ValueError("gates node needs this turn's intake")`.
  *A CON-2 turn always carries its intake (graph-core §2 rule 1); no turn is gated on guesses.*
- **G-2.** `gate = decide_gate(ctx.intake, flags_from_state(state))`. Call both through the names imported from
  `meridian.gates.gate` at call time (no default-argument binding). *The safety rule is checked first on every turn,
  wherever the phrase sits in the chat (R-5, R-47); the GRC-3 order lives only in AEA-12's tuple.*
- **G-3.** `event = CheckEvent.from_gate(ctx.ids.turn_id, gate)`. *One `gate` event per turn, codes only (GRN-5).*
- **G-4.** `card = burning_card_id(ctx.ids.turn_id) if gate.kind is GateKind.BURNING_ASK else None`. *This node is
  the key's only writer: set on `BURNING_ASK`, cleared on every other result (GRC-4).*
- **G-5.** `update: GatesUpdate = {"gate": gate, "check_events": (event,), "burning_card_id": card}`. If
  `gate.kind is GateKind.BURNING_ANSWER and gate.burning_answer == "no"`: `update["plan"] = _burning_ruled_out_plan()`.
  *`plan` is written by this node on the burning-"no" path only (GRC-18 edge 2).*
- **G-6.** `return update`. Never returns `halt` (the gate never halts).

```python
def _burning_ruled_out_plan() -> Plan:
    """graph-nodes §6 (GRN-6) with CAS-16 option A: both dangers ruled out → the booking task, identity first."""
    return Plan(
        mode="act",
        tasks=(PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=True),),
        handoff_request=HandoffReason.BURNING_RULED_OUT,
        topic="booking",
        source="rules_only",
    )
```

### 4.7 `safety` — algorithm

Private module constants and type:

```python
_SAFETY_NODE: Final = "safety"
_RULE_SAFETY_FALLBACK: Final = "R5.safety"            # a SAFETY gate whose rule_ids is empty (never expected)
_RULE_DANGER_FALLBACK: Final = "R8.danger_words"      # a DANGER_RULE gate whose rule_ids is empty (never expected)
_RULE_BURNING_YES: Final = "R7.burning_yes"           # PA-4: no word rule fires on a card answer
_RULE_BURNING_UNSURE: Final = "R7.burning_unsure"
_RULE_CLASSIFIER: Final = MappingProxyType({"danger": "R47.classifier_danger",
                                            "burning_unclear": "R47.classifier_burning_unclear"})
_CAUSE_WRITE_ERROR: Final = "write_error"

@dataclass(frozen=True)
class _SafetyPath:
    reason: HandoffReason
    cause: str        # the turn's gate result: danger.label when the classifier raised, else gate.gate_result()
    rule_id: str
```

`_safety_path(gate: GateDecision, danger: DangerAssessment | None) -> _SafetyPath | None` — first match:

| # | Condition | `reason` | `cause` | `rule_id` |
|---|---|---|---|---|
| 1 | `gate.kind is SAFETY` | `SAFETY` | `gate.gate_result()` (= `"safety"`) | `gate.rules.rule_ids[0]` if non-empty else `_RULE_SAFETY_FALLBACK` |
| 2 | `BURNING_ANSWER`, `burning_answer == "yes"` | `SAFETY` | `gate.gate_result()` (= `"safety"`) | `_RULE_BURNING_YES` |
| 3 | `BURNING_ANSWER`, `burning_answer == "unsure"` | `BURNING_UNCLEAR` | `gate.gate_result()` (= `"burning_unclear"`) | `_RULE_BURNING_UNSURE` |
| 4 | `BURNING_ANSWER`, any other answer (`"no"`, `None`) | — | — | `raise ValueError("safety node: a burning 'no' routes to booking")` |
| 5 | `gate.kind is DANGER_RULE` | `DANGER` | `gate.gate_result()` (= `"danger"`) | `gate.rules.rule_ids[0]` if non-empty else `_RULE_DANGER_FALLBACK` |
| 6 | `gate.kind is BURNING_ASK` | return `None` (no instruction, no case: the R-7 question card only) | | |
| 7 | `gate.kind is FREE_TEXT and danger is not None and danger.raised and danger.label in ("danger", "burning_unclear")` | `HandoffReason(danger.label)` | `danger.label` | `_RULE_CLASSIFIER[danger.label]` |
| 8 | anything else | — | — | `raise ValueError("safety node reached without a safety path")` |

*Invariants:* the reason and priority never come from a model (classifier raises only raise, R-47); the "first fired
rule id" is used only where the rule that fired **is** the reason (rows 1, 5; AEA-05 PD-6 puts safety then danger
first), so a policy word in the same message can never become a safety case's id (PA-4).

`safety(state, runtime, *, deps)`:
- **S-1.** `ctx = runtime.context`. `gate = state.gate`; `None` → `raise ValueError("safety node: no gate decision")`.
- **S-2.** `path = _safety_path(gate, state.danger)`. If `path is None` → `return {}`. *`BURNING_ASK` opens no case and
  sends no `safety_reply_sent` (AC-5; PA-3).*
- **S-3.** `emit_signal(ctx.ids, SignalRecord(name=SignalName.SAFETY_REPLY_SENT, turn_id=ctx.ids.turn_id,
  thread_id=ctx.ids.thread_id, request_id=ctx.ids.request_id, run_tag=ctx.ids.run_tag, node=_SAFETY_NODE,
  cause=path.cause))`. *Emitted before any case write, so it exists whatever the write does (graph-nodes §4).*
- **S-4.** `request = HandoffRequest(thread_id=ctx.ids.thread_id, turn_id=ctx.ids.turn_id, reason=path.reason,
  priority=priority_for(path.reason), rule_id=path.rule_id, trigger="safety", identity=state.identity,
  safety_kind=gate.rules.safety)`. *Priority only from AEA-14 (P0 safety; P1 danger, burning_unclear). No contact
  detail is asked or added (R-6). Under GRC-3 A this runs even while `controller.kind == "human"`; the service's
  per-thread idempotency returns the open case (`created=False`).*
- **S-5.** `result = _open_case(deps, request, ctx)`:
  1. `try: first: HandoffResult = deps.handoff.open(request, ctx)` → `return first`.
     `except Exception:` fall through (do **not** write `pass`; ruff S110 — set a local flag or restructure).
  2. `try: retried: HandoffResult | None = deps.handoff.open(request, ctx)` `except Exception: retried = None`.
     *Exactly one retry (DO-1 §8.2); never catch `BaseException`; never log or keep the exception text (it may hold a
     value).*
  3. `emit_signal(ctx.ids, SignalRecord(name=SignalName.CASE_WRITE_FAILED, turn_id=…, thread_id=…, request_id=…,
     run_tag=…, node=_SAFETY_NODE, cause=_CAUSE_WRITE_ERROR, attempt=2, recovered=retried is not None))`.
  4. `return retried`.
  Assign the service's return to an annotated variable before returning it (mypy `warn_return_any`, since
  `GraphDeps.handoff` is typed through the `Any` alias `HandoffService` on AEA-21's `context.py`).
  In production the exception is AEA-29's `CaseWriteFailed` (raised after the service's own two attempts; its message
  carries no value). Catch it as `Exception`; never import it (PA-1 forbids `meridian.services`); never read its
  attributes. The stacked retry is a known, accepted cost (§8 R-4).
- **S-6.** `return {"handoff": result} if result is not None else {}`. *Never a `halt`: compose still renders the
  instruction (DO-1 §8.2 *Safety turn*).*

### 4.8 `identity` — algorithm

Private module constants:

```python
_NEW_CODE: Final = "new_code"                                              # AEA-12 AC-8, AEA-21 PD-10
_LOCATE_RESULTS: Final = (Located, NotVerified)
_SEND_RESULTS: Final = (CodeSent, NotVerified, CodeCapReached)
_VERIFY_RESULTS: Final = (Verified, CodeWrong, CodeExpired, CodeLocked)
```

`_checked(result: object, allowed: tuple[type, ...]) -> IdentityStep`: if `isinstance(result, allowed)` return it
**unchanged** (same object); else `raise TypeError("identity service returned an unexpected result type")`. *Results
are passed through, never re-grouped or rebuilt (GRT-3); the guard also narrows `Any` for mypy.* (Write it with the
typed tuples above; if mypy cannot narrow a tuple-of-types to `IdentityStep`, use three small functions
`_as_locate`, `_as_send`, `_as_verify` with explicit `isinstance` chains instead. Same behaviour.)

`identity(state, runtime, *, deps)`:
- **I-1.** `ctx = runtime.context`; `gate = state.gate`; `None` → `raise ValueError("identity node: no gate
  decision")`. `intake = ctx.intake`; `None` → `raise ValueError("identity node needs this turn's intake")`.
  `thread_id = ctx.ids.thread_id`. `step: IdentityStep | None = None`; `called = False`.
- **I-2.** `gate.kind is GateKind.LOCATE`:
  1. `locator = Locator.from_form(intake.form) if intake.form is not None else None`.
  2. `locator is None` → `step = NotVerified()`; **no service call**. *An incomplete form gives the same step as no
     match (R-16: identical for every cause).*
  3. else `found = _checked(deps.identity.locate(thread_id, locator, ctx.now), _LOCATE_RESULTS)`; `called = True`.
     If `isinstance(found, Located)` → `step = _checked(deps.identity.send_code(thread_id, ctx.demo_session,
     ctx.now), _SEND_RESULTS)` (same turn; WP-2). Else `step = found` (the `NotVerified` as returned).
     *`Located` itself is never the step: on a match the code goes out in the same turn.*
- **I-3.** `gate.kind is GateKind.CODE_ENTRY`:
  1. `intake.code_digits is not None` → `step = _checked(deps.identity.verify(ctx.ids, intake.code_digits, ctx.now),
     _VERIFY_RESULTS)`; `called = True`. *The `SecretStr` is handed straight to the service; it is never unwrapped,
     copied or logged here.*
  2. elif `intake.choice is not None and intake.choice.option == _NEW_CODE` → `step = _checked(
     deps.identity.send_code(thread_id, ctx.demo_session, ctx.now), _SEND_RESULTS)`; `called = True`.
     *"Send a new code" is `send_code`, never `verify` (GRT-3).*
  3. else → no call (PA-2).
- **I-4.** `ctx.demo_session` is the conversation's own login session (AEA-27 R-6); never another value.
- **I-5.** Any other gate kind (`FREE_TEXT`, `CARD_CHOICE`, `BURNING_ANSWER` "no" — reached through AEA-21's
  `route_act_plan` because a plan needs identity) → no call (PA-2). *No service call happens without the customer's
  own form or code; compose shows the locate prompt from `identity_step is None` (AEA-21 §4.10 D-6).*
- **I-6.** Build the update from `step` and the re-read only. **Never** put `intake`, `intake.form`, a `Locator`,
  `intake.code_digits` or any of their values into the update, an exception message, or anything else that outlives
  the call (R-15; graph-core §2 rules 1–3).
- **I-7.** If `called`: `with deps.uow() as tx: fresh = tx.core.reads.identity_state(thread_id)` (no arguments to
  `deps.uow()`: read-only); return `{"identity_step": step, "identity": fresh}` (if `step` is `None` here — it cannot
  be when `called` — return `{"identity": fresh}`). Elif `step is not None` (the incomplete-form case): return
  `{"identity_step": step}`. Else return `{}`. *`identity` is re-read only after the service's own write (DO-3 §5.3);
  no transaction is held across a service call (DO-3 §2.3 rule 1).*
- Exceptions from `deps.identity` or the read propagate unchanged (AEA-21's `timed_node` records `error`; TurnService
  owns the failed turn). Do not add a retry or a catch here.

---

## 5. Steps (build order; each step ends with a check)

Setup for both roles: the worktree and branch the orchestrator gives you (e.g. `aea-36-front-node` from `main`). In every
shell: `export UV_LINK_MODE=hardlink`. Never copy a venv, no `node_modules`, pytest with `-n 2` at most (serial is fine),
never bind ports 4019 or 5184, never read `.env`.

### Step 0 (both roles) — pre-flight: the prerequisites are on the base

```bash
uv sync
uv run python -c "from meridian.domain.handoff import HandoffReason, HandoffRequest, HandoffResult, CaseSummary; print(HandoffReason.BURNING_RULED_OUT.value)"
uv run python -c "from meridian.domain.identity import Locator, Located, NotVerified, CodeSent, CodeCapReached, Verified, CodeWrong, CodeExpired, CodeLocked, IdentityStep, FormValues; print('identity ok')"
uv run python -c "from meridian.domain.state import ConversationState, GatesUpdate, SafetyUpdate, IdentityNodeUpdate, Controller, OpenTask, TaskDetails; print(sorted(GatesUpdate.__annotations__))"
uv run python -c "from meridian.domain.turn import CheckEvent, DangerAssessment, GateDecision, GateKind, Plan, PlannedTask, SignalName, SignalRecord, TaskIntent, TurnContext, TurnIds, TurnBudget, SpanHandle, Intake, TurnInput, TextPayload, ChoicePayload, CodePayload, FormPayload; print('turn ok')"
uv run python -c "from meridian.gates.gate import burning_card_id, decide_gate, flags_from_state, parse_intake; print('gate ok')"
uv run python -c "from meridian.policy.handoff import priority_for, promise_for; from meridian.domain.handoff import HandoffReason as R; print(priority_for(R.SAFETY), priority_for(R.DANGER), priority_for(R.BURNING_UNCLEAR))"
uv run python -c "from meridian.agent.context import GraphDeps; from meridian.agent.signals import emit_signal; import dataclasses; print([f.name for f in dataclasses.fields(GraphDeps)])"
uv run python -c "from tests.fixtures.sqlite import temp_sqlite, TempStore; from meridian.adapters.sqlite.db import format_wall; print('sqlite ok')"
uv run python -c "import inspect; from meridian.services.identity import IdentityService as S; print([list(inspect.signature(getattr(S, m)).parameters) for m in ('locate', 'send_code', 'verify')])"
uv run python -c "import inspect; from meridian.services.handoff import HandoffService as H; print(list(inspect.signature(H.open).parameters))"
grep -n "stub from AEA-21" src/meridian/agent/nodes/front.py
```

Expected: `burning_ruled_out`; `identity ok`; the `GatesUpdate` keys include `burning_card_id`, `check_events`, `gate`,
`halt`, `plan`; `turn ok`; `gate ok`; `P0 P1 P1`; the 13 `GraphDeps` field names; `sqlite ok`;
`[['self', 'thread_id', 'locator', 'now'], ['self', 'thread_id', 'demo_session', 'now'], ['self', 'ids', 'digits',
'now']]` (AEA-27's real service; a check only, never an import in `front.py`); `['self', 'req', 'ctx']` (AEA-29's real
`HandoffService.open`; a check only); three stub lines **on a fresh worktree
from main** (role B). **On the existing branch (role A) the grep prints nothing**, because `front.py` is already
filled; that is expected there. On any
failure **stop and report** `blocked-on AEA-02` (domain), `AEA-12` (gate), `AEA-14` (policy), `AEA-21` (agent, stub),
`AEA-10` (sqlite). **Planner's check, 2026-10-21 on `main` `5531664` (the files it imports are byte-identical on
`a81f59d` and on `dd1b110`; the `IdentityService` line was read from `dd1b110`'s source):** every line passes with exactly the expected
output (`burning_ruled_out`; `['burning_card_id', 'check_events', 'gate', 'halt', 'plan']`; `P0 P1 P1`; the 13 fields
in §4.3's order; three stub lines). Any failure on your base means drift: stop and report. Then read
`src/meridian/domain/{turn,state,identity,handoff}.py`, `src/meridian/gates/gate.py`,
`src/meridian/agent/{context,signals,routers}.py` and the current `front.py` stub; if any name or signature in §4
differs, stop and report rather than adapting silently.

### Steps T-1…T-4 (test-writer, first; `risk::security`)

- **T-1.** `test -e tests/unit/agent/nodes/__init__.py || touch tests/unit/agent/nodes/__init__.py`. Create
  `tests/unit/agent/nodes/test_front.py` with the module header, constants, builders and doubles of §6.
- **T-2.** Write every test in §7.1 with exactly the names listed (reviewers and the record cite them). Import the node
  functions **inside each test or through a fixture** (`from meridian.agent.nodes import front` at module top is fine:
  the stub exists and has the final signatures).
- **T-3.** Red for the right reason: `uv run pytest tests/unit/agent/nodes/test_front.py -q -rA`. Every test must fail,
  and each failure must be the stub's `NotImplementedError("src/meridian/agent/nodes/front.py <name>: stub from
  AEA-21; AEA-36 fills it")`, except `test_front_module_imports`, which fails on its "required import missing" assertion.
  No test may pass, error at collection, or fail for another reason (a wrong builder, a missing fixture). Then
  `uv run pytest --collect-only -q` exits 0, and `uv run ruff check tests/unit/agent/nodes/test_front.py`,
  `uv run ruff format --check tests/unit/agent/nodes/test_front.py`, `uv run mypy tests/unit/agent/nodes/test_front.py`
  pass. If an AEA-12 / AEA-05 phrase in §6 does not gate as stated, stop and report (that is their behaviour).
- **T-4.** Commit: `git add tests/unit/agent/nodes/test_front.py` (plus the `__init__.py` only if you created it).
  Message: `test(graph): frozen tests for the front node (AEA-36)` + blank line + `Refs #36` + blank line +
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` as the **last** line. Report the SHA (the orchestrator
  records it in the frozen-test manifest).

### Steps I-1…I-10 (implementer; never edit `test_front.py`)

- **I-1.** Pre-flight (step 0). Confirm the frozen file is present and unchanged: `git log --oneline --
  tests/unit/agent/nodes/test_front.py` shows only the test-writer's commit.
- **I-2.** Replace the stub module docstring and bodies in `src/meridian/agent/nodes/front.py`: docstring (one
  paragraph: the three nodes, AEA-36, graph-nodes §9.3), imports (§4.1), `__all__`, constants (§4.7, §4.8).
- **I-3.** `gates` and `_burning_ruled_out_plan` (§4.6). Check: `uv run pytest tests/unit/agent/nodes/test_front.py -q
  -k "gate_first or gate_event or burning_no"`.
- **I-4.** `_SafetyPath`, `_safety_path`, `_open_case`, `safety` (§4.7). Check: `-k "wp5 or burning_and_danger or
  retried or representative or refuses or check_event"`.
- **I-5.** `_checked` (or the three `_as_*` helpers) and `identity` (§4.8). Check: `-k "wp2 or passed_through or
  never_leave or without_form"`.
- **I-6.** Whole file green: `uv run pytest tests/unit/agent/nodes/test_front.py -q -rA` (and `-k
  "only_own_keys or module_imports"`). If a frozen test fails and you believe the test is wrong, **stop and report** the
  test name, the input and the two values; do not edit the test, do not bend `front.py` away from §4 to satisfy it.
- **I-7.** Fast gates and affected tests, cheapest first (§7.3 G-1…G-6). Commit 1: `git add
  src/meridian/agent/nodes/front.py`; message `feat(graph): front node — gates, safety, identity (AEA-36)` + blank line
  + one paragraph (what the three nodes do; retry-once rule; digits and form values read only from `ctx.intake`) +
  blank line + `Refs #36` + blank line + `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` last. Note the
  short SHA as `<sha>`.
- **I-8.** Journey file (§7.6): create `tests/journeys/j5/test_aea_36.py` exactly as specified there; run G-1…G-3 on it
  and G-7. Then the journey record (§7.4).
- **I-9.** Context rows (AC-14), each edit limited to this ticket's text (shapes as on `775f591` + AEA-21's `0a5b703`):
  - **`.claude/reference/area-map.md`, row `| 3 | **A7d Front** | … | AEA-36, 37 | <status> |`:** change only the
    Status cell. If it reads `planned`, write `planned; agent/nodes/front.py actual (AEA-36, <sha>)` (the A6 row's
    style: ``planned; `policy/handoff.py` actual (AEA-14, `af848c9`)``). If AEA-37 already changed it, keep its words and
    append `; agent/nodes/front.py actual (AEA-36, <sha>)`.
  - **`docs/design/code-design.md`**, two one-line edits, nothing else:
    1. In the §3 module tree, the line starting `│   ├── nodes/front.py` (AEA-21 ends it with `stub AEA-21 6df4f4c`):
       replace that trailing `stub AEA-21 6df4f4c` with `built AEA-36 <sha>`. If the line has no status column, append
       three spaces and `built AEA-36 <sha>`.
    2. Directly after the **last** `**Built:**` line under `## 3. The module map`, insert a new line
       ``**Built:** `agent/nodes/front.py` (AEA-36, `<sha>`).`` (its own line, so parallel tickets do not collide).
  - **`.claude/state/icm-progress.md`:** in the `Routes verified against code and tests` row whose evidence names
    `gates/gate.py` (AEA-12, `40dd865`; 131 pass), replace the evidence cell with `2026-10-21: area map A1 →
    gates/gate.py (AEA-12, 40dd865; 131 pass) and A7d → agent/nodes/front.py checked against
    tests/unit/agent/nodes/test_front.py (AEA-36, <sha>; <n> pass)` (≤ 400 characters; the gate is the function this
    node runs first). Then in the `Last reconciled:` line, replace its first `2026-10-21 — ` with `2026-10-21 — AEA-36
    front node (routes row); earlier, `. Change nothing else.
- **I-10.** Commit 2: `git add tests/journeys/j5/test_aea_36.py docs/testing/journeys/<date>-AEA-36.md
  .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`; message
  `test(journey): J-5 safety step; docs(AEA-36): journey record and context` +
  blank line + `Refs #36` + blank line + Co-Authored-By line last. Then `git diff --name-only main...HEAD` must list
  exactly: `src/meridian/agent/nodes/front.py`, `tests/unit/agent/nodes/test_front.py` (test-writer's commit), possibly
  `tests/unit/agent/nodes/__init__.py` (it already exists on `5531664`, so normally absent), the journey file, the
  journey record, and the three context files.

**Commits:** explicit `git add <paths>` only (never `-A`); commit only on your own branch; never push `main`; never
force-push.

### Do not

- Edit any file outside §2.1. In `tests/graph/test_spine.py`, change nothing beyond §0 step 4 (three rows and one
  import name); never touch `tests/graph/_spine_doubles.py`.
- Edit `test_front.py` after the test-writer's commit (implementer).
- Call a model, the gateway, retrieval, the specialist runner, scheduling, `deps.cases` or `deps.brief` from any node
  here; open a unit of work in `gates` or `safety`.
- Import `logging`, `sqlite3`, anything under `meridian.services`, `meridian.adapters`, `meridian.web`, or another node
  module; print anything; write any customer sentence or block (compose's).
- Unwrap `SecretStr` (`get_secret_value`) in `front.py`; copy `ctx.intake`, the form, the `Locator` or the digits into
  state, a return value, an exception message, a signal or a log.
- Retry the identity service; retry the handoff more than once; catch `BaseException`; return a `halt`.
- Re-group identity results (e.g. turn `CodeLocked` into `NotVerified`) or rebuild them.
- Type a priority (always `priority_for`), a promise, or a case reason other than §4.7's table.
- Put a phone number, verification code, card-like number or secret literal in source or tests (§6 builds sentinels
  at run time).
- Add a dependency, a state key, a `register_*` hunk, `# type: ignore`, or a `configurable` value.
- Run the full suite (no shared fixture, setting or dependency changes here).

---

## 6. Data and fixtures (synthetic or issued only; all inside `test_front.py`)

**Constants** (synthetic UUID4s; version nibble 4, variant 8–b):
`THREAD = ThreadId("6a7b8c9d-0e1f-4a2b-8c3d-4e5f6a7b8c9d")`, `TURN = TurnId("7b8c9d0e-1f2a-4b3c-9d4e-5f6a7b8c9d0e")`,
`TURN_PREV = TurnId("8c9d0e1f-2a3b-4c4d-ae5f-6a7b8c9d0e1f")`, `TURN_CODE = TurnId("9d0e1f2a-3b4c-4d5e-bf6a-7b8c9d0e1f2a")`,
`REQ = RequestId("0e1f2a3b-4c5d-4e6f-8a7b-8c9d0e1f2a3b")`,
`NOW = dt.datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))` (`DEMO_START`, CAS-23).

**Phrases** (verified by the planner on `775f591` through the real `parse_intake` + `decide_gate`; if one does not gate
as stated on your base, stop and report):
| Name | Text | Gate |
|---|---|---|
| `WP5` | `"My carbon monoxide detector is going off."` | `SAFETY`, `rules.safety is CO`, `rule_ids == ("R5.co",)` |
| `CO_TYPO` | `"my carbon monoxid alarm is going off"` | `SAFETY`, CO |
| `WP6` | `"I need to schedule a service call. I smell something burning from the vents."` | `BURNING_ASK`, `rule_ids == ("R7.burning_unclear",)` |
| `DANGER_WORDS` | `"My son can't breathe"` | `DANGER_RULE`, `rule_ids[0] == "R8.danger_words"` |
| `DANGER_FREE` | `"my mother is 88 and it's 95 degrees in here"` | `FREE_TEXT` (no rule; graph-nodes §7) |
| `PLAIN` | `"When will the technician arrive?"` | `FREE_TEXT`, no rule |
| `NOT_SURE` | `"not sure"` | no rule; `BURNING_ANSWER`/`unsure` while a burn card is pending |

**Gate preconditions the builders must set** (`flags_from_state` on `775f591`; without them the turn gates as
`FREE_TEXT`):
- A choice on a `burn-<id>` card gives `BURNING_ANSWER` (`"yes"` → yes, `"no"` → no, anything else → unsure) whatever the
  state; free text gives `BURNING_ANSWER`/`unsure` **only** while `state.burning_card_id` is set.
- A choice on a `code-<id>` card (`"new_code"`, `"something_else"`) gives `CODE_ENTRY` **only** when
  `state.identity.status == "code_sent"`. A `CodePayload` gives `CODE_ENTRY` always.
- `ChoicePayload(card_id="t-1.1", option="56")` gives `CARD_CHOICE` **only** when `state.open_tasks` holds an
  `OpenTask(task_id="t-1", status != "done")`.
- A `FormPayload` on a `locate-<id>` card gives `LOCATE` even with a name only (that is the "incomplete" case:
  `Locator.from_form(FormValues(name="Omar Patel"))` is `None`).
- With `controller.kind == "human"`, a CO phrase still gives `SAFETY` (GRC-3 A: `GATE_ORDER_HEAD = (SAFETY, AI_PAUSED)`).

**Builders** (plain functions, no side-effect fixtures):
- `_intake(payload) -> Intake` = `parse_intake(payload)` (AEA-12, real). Payloads: `TextPayload(text=…)`,
  `ChoicePayload(card_id=…, option=…)`, `CodePayload(card_id=f"code-{TURN_CODE}", code=SecretStr(code))`,
  `FormPayload(card_id=f"locate-{TURN}", values=FormValues(name=…, phone=SecretStr(…)))`.
- `_state(turn_id, intake, **kw) -> ConversationState`: `ConversationState(thread_id=THREAD, turn_input=TurnInput(
  turn_id=turn_id, message_id=1, kind=intake.kind, text_store=intake.text_store, card_id=intake.card_id,
  choice=intake.choice, card_number_seen=intake.card_number_seen, received_at=NOW), **kw)`.
- `_ctx(turn_id, intake) -> TurnContext`: `TurnContext(ids=TurnIds(thread_id=THREAD, turn_id=turn_id, request_id=REQ,
  run_tag="live", run_id=None, agent_version="test"), budget=TurnBudget(started=t0, deadline=t0 + 60.0) with t0 =
  time.monotonic(), now=NOW, demo_session="demo-session-36", span=SpanHandle(turn_id=turn_id, trace_id=None),
  intake=intake)`. `_rt(ctx) = Runtime(context=ctx)` (`from langgraph.runtime import Runtime`; all its other fields
  default).
- `_apply(state, update) -> ConversationState` = `state.model_copy(update=dict(update))` (no reducer; tests apply one
  node's update at a time).
- `_gated(text_or_payload, *, turn_id=TURN, **state_kw) -> tuple[ConversationState, TurnContext]`: builds intake,
  state, ctx; runs `front.gates(state, _rt(ctx), deps=_deps())`; returns `(_apply(state, update), ctx)` — the state a
  router would hand to `safety` / `identity`.
- `_booking_task() -> OpenTask`: `OpenTask(task_id="t-1", specialist="scheduling", intent=TaskIntent.BOOK_NEW,
  opened_turn=TURN_PREV, details=TaskDetails(), status="open")`.
- `_verified() -> IdentityState`: `IdentityState(status="verified", customer_id=CustomerId("MHC-10002"),
  masked_hint="the phone ending in 02", code_expires_at=None, tries_left=3, codes_sent=1, verified_at=NOW)`.
- `_handoff_result(reason, *, created=True, case_ref="MHC-C-0009") -> HandoffResult`: `CaseSummary(case_ref=
  CaseRef(case_ref), reason=reason, priority=priority_for(reason), state="unassigned", created_at=NOW,
  promise=promise_for(reason, "nobody_online", NOW), followup=None, version=1, due_at=None)`; `action=CompletedAction(
  key=ActionKey(thread_id=THREAD, turn_id=TURN, kind=ActionKind.CASE_OPENED, record_id=case_ref),
  kind=ActionKind.CASE_OPENED, records={"case": case_ref}, at=NOW)`; `alert="supervisor_now"`.

**Doubles:**
- `_Rec(name, log: list[tuple[str, str]])`: `__getattr__(attr)` appends `(name, attr)` to `log` **on access** and
  returns a function that appends `(name, f"{attr}()")` and raises `AssertionError(f"{name}.{attr} must not be used")`;
  `__call__` appends `(name, "__call__")` and raises the same. Used for every `GraphDeps` field a test does not drive.
- `_deps(log=None, **over) -> GraphDeps`: `GraphDeps(**{f.name: over.get(f.name, _Rec(f.name, log)) for f in
  dataclasses.fields(GraphDeps)})` (build the dict as `dict[str, Any]` so mypy accepts it). `_used(log, *names)` →
  entries whose first item is in `names`.
- `_HandoffDouble(outcomes: list[HandoffResult | Exception])`: `.calls: list[HandoffRequest]`; `open(req, ctx)` appends
  `req`, pops the first outcome, raises it if it is an `Exception`, else returns it.
- `_IdentityDouble(locate=…, send=…, verify=…, writer=None)`: each argument a result object (or a callable producing
  one); `.calls: list[str]` in order (`"locate"`, `"send_code"`, `"verify"`); `.args: list[tuple]` the arguments
  received (locator object, `demo_session`, `ids`, the `SecretStr`, `now`). If `writer` is given (AC-8), each method
  first calls `writer(method_name)` to write the identity rows the real service would write (below).
- `_UowDouble(state: IdentityState)`: callable `(*, write=False, exclusive=False)` recording `(write, exclusive)` in
  `.opened` and returning `contextlib.nullcontext(SimpleNamespace(core=SimpleNamespace(reads=SimpleNamespace(
  identity_state=<records thread_id in .reads, returns state>))))`.
- `_SpyUow(inner)`: wraps `store.uow` (AC-8); records each call's kwargs in `.opened`, delegates.

**AC-8 database** (AEA-10 `temp_sqlite()`, a disposable copy of the **issued** scheduling DB; pytest fixture
`store` = `with temp_sqlite() as s: yield s`): Omar Patel is the issued customer `MHC-10002` (WP-2). His phone is
**read from the temp copy at run time** (`SELECT phone FROM customers WHERE customer_id = 'MHC-10002'` through
`sqlite3.connect(store.db_path)`), never typed. The identity double's `writer` simulates AEA-27's own writes with raw
SQL on a separate `sqlite3.connect(store.db_path)` (commit, close), times via `format_wall` from
`meridian.adapters.sqlite.db`:
- `locate`: `INSERT OR REPLACE INTO identity_threads (thread_id, status, customer_id, masked_hint, channel,
  verified_at, updated_at) VALUES (THREAD, 'located', 'MHC-10002', 'the phone ending in 02', 'phone', NULL,
  format_wall(NOW))`.
- `send_code`: `UPDATE identity_threads SET status='code_sent', updated_at=… WHERE thread_id=THREAD`; `INSERT INTO
  identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, tries_left, used_at,
  inbox_message_id) VALUES (THREAD, 'MHC-10002', 'synthetic-hmac-36', 'test-boot', format_wall(NOW),
  format_wall(NOW + 10 min), 3, NULL, 1)`. Returns `CodeSent(masked_hint="the phone ending in 02",
  expires_at=NOW + 10 min, sends_left=2)`.
- `verify`: `UPDATE identity_threads SET status='verified', verified_at=format_wall(NOW), updated_at=… WHERE
  thread_id=THREAD`; `UPDATE identity_codes SET used_at=format_wall(NOW) WHERE thread_id=THREAD`. Returns
  `Verified(customer_id=CustomerId("MHC-10002"), action=CompletedAction(key=ActionKey(thread_id=THREAD,
  turn_id=TURN_CODE, kind=ActionKind.VERIFIED, record_id="MHC-10002"), kind=ActionKind.VERIFIED,
  records={"customer": "MHC-10002"}, at=NOW))`.

**Sentinels (AC-10, AC-12; built at run time, never literals):** `rng = random.Random(36)`.
- Code: six digits from `rng.randrange(10)`; regenerate while the string is a substring of any constant above, of
  `NOW.isoformat()` or of `format_wall(NOW)` (AEA-27 R-8's collision guard).
- Phone: `f"512-555-01{rng.randrange(100):02d}"` (fictional reserved range) and its digits-only form.
- Name: `"Sentinelname " + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))`.
- Phrase (AC-12): `"zqsentinel" + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))`, appended after
  `WP5` / `DANGER_WORDS` with a space.

---

## 7. Checks

### 7.1 Frozen tests (`tests/unit/agent/nodes/test_front.py`; test-writer writes them first; names are binding)

Every assertion message names the case id, never message text. Print one line per case (case id → kind / keys / call
list) so the report can quote it.

| Test | AC | Setup | Assertions |
|---|---|---|---|
| `test_gate_first_every_turn_mid_chat` | AC-1 | Three cases, each `TextPayload(CO_TYPO)` on `TURN` with state: (a) `open_tasks=[_booking_task()]`, `identity=_verified()`; (b) same plus `burning_card_id=burning_card_id(TURN_PREV)`; (c) same as (a) plus `controller=Controller(kind="human", representative_name="Riley (demo representative)", case_ref=CaseRef("MHC-C-0009"))` | `update["gate"].kind is GateKind.SAFETY`; `.rules.safety is SafetyKind.CO`; `.resume_task_id is None`; `update["gate"] == decide_gate(ctx.intake, flags_from_state(state))` (same real function); `set(update) <= {"gate", "check_events", "burning_card_id"}` |
| `test_gate_event_and_burning_card_id` | AC-2 | Cases: `WP5`; `WP6`; `PLAIN`; then a `ChoicePayload(card_id=burning_card_id(TURN_PREV), option="no")` with state `burning_card_id=burning_card_id(TURN_PREV)` | each: `len(update["check_events"]) == 1`, `ev.check == "gate"`, `ev.turn_id == TURN`, `ev.codes == (gate.kind.value, *gate.rules.rule_ids)`. WP5: `ev.result == "fired"`, `ev.codes == ("safety", "R5.co")`, `update["burning_card_id"] is None`. WP6: `ev.result == "fired"`, `ev.codes[0] == "burning_ask"`, `update["burning_card_id"] == f"burn-{TURN}"`. PLAIN: `ev.result == "pass"`, `ev.codes == ("free_text",)`, `burning_card_id is None`. Choice "no": `"burning_card_id" in update and update["burning_card_id"] is None` (cleared) |
| `test_burning_no_writes_code_built_plan` | AC-3 | "no" choice on `burning_card_id(TURN_PREV)` (state has that card pending); then, for "no plan" cases: `WP5`, `WP6`, `PLAIN`, `DANGER_WORDS`, choice `"yes"`, choice `"not_sure"`, text `NOT_SURE` with the card pending, a locate form, a code payload | "no": `update["plan"] == Plan(mode="act", tasks=(PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=True),), handoff_request=HandoffReason.BURNING_RULED_OUT, topic="booking", source="rules_only")` and `plan.planner_failed is False`; every other case: `"plan" not in update` |
| `test_wp5_safety_p0_no_model_no_identity` | AC-4, PA-4 (**WP-5**) | `state, ctx = _gated(TextPayload(WP5))`; `log = []`; `h = _HandoffDouble([_handoff_result(HandoffReason.SAFETY)])`; `front.safety(state, _rt(ctx), deps=_deps(log, handoff=h))` | `len(h.calls) == 1`; `req.trigger == "safety"`, `req.reason is HandoffReason.SAFETY`, `req.priority is Priority.P0`, `req.safety_kind is SafetyKind.CO`, `req.rule_id == "R5.co"`, `req.thread_id == THREAD`, `req.turn_id == TURN`, `req.identity == state.identity`, `req.change_request is None`; `update == {"handoff": <the double's result>}`; `log == []` (no access to gateway, retrieval, uow, identity, scheduling, brief, demo, limits, trace, specialists, cases, ledger); print the zero counts for gateway, identity, retrieval, specialists |
| `test_burning_and_danger_paths` | AC-5, PA-4 (**WP-6**) | Table rows (case id → how built): `burn_yes` choice `"yes"` on pending card; `burn_unsure` choice `"not_sure"`; `burn_text_unsure` text `NOT_SURE` with card pending; `danger_rule` text `DANGER_WORDS`; `clf_danger` text `DANGER_FREE` then `state = _apply(state, {"danger": DangerAssessment(label="danger", raised=True, confidence=0.9, failure=None)})`; `clf_burning` same with `label="burning_unclear"`; `burning_ask` text `WP6` | expected (reason, priority, rule_id, cause): `burn_yes` (SAFETY, P0, `"R7.burning_yes"`, `"safety"`); `burn_unsure` and `burn_text_unsure` (BURNING_UNCLEAR, P1, `"R7.burning_unsure"`, `"burning_unclear"`); `danger_rule` (DANGER, P1, `"R8.danger_words"`, `"danger"`); `clf_danger` (DANGER, P1, `"R47.classifier_danger"`, `"danger"`); `clf_burning` (BURNING_UNCLEAR, P1, `"R47.classifier_burning_unclear"`, `"burning_unclear"`). Each: one `open` call; `req.priority == priority_for(req.reason)` **and** equals the literal; `req.safety_kind is None`; `req.trigger == "safety"`; one `safety_reply_sent` record with that cause (caplog). `burning_ask`: `update == {}`, zero `open` calls, zero signal records. Print the table |
| `test_burning_ask_opens_no_case` | AC-5, PA-3 | text `WP6` → `_gated` → `front.safety` with `_HandoffDouble([])`; caplog on `meridian.signal` | `update == {}`; zero `open` calls; zero signal records. (The frozen file `76fe4c2` holds the `burning_ask` row here instead of inside the table test above, whose six other rows are `pytest.mark.parametrize("case_id", …)`.) |
| `test_safety_case_write_retried_once_instruction_kept` | AC-6 | WP5 state; `caplog.set_level(logging.INFO, logger="meridian.signal")`. (a) `_HandoffDouble([sqlite3.OperationalError("database is locked"), _handoff_result(SAFETY)])`; (b) `_HandoffDouble([sqlite3.OperationalError("database is locked"), sqlite3.OperationalError("database is locked")])`; (c) one success first time | (a) `len(calls) == 2`; `update == {"handoff": result}`; signal names in order `["safety_reply_sent", "case_write_failed"]`; the second has `attempt == 2`, `recovered is True`, `cause == "write_error"`, `node == "safety"`. (b) no exception; `len(calls) == 2`; `update == {}` (`"handoff"` and `"halt"` absent); same two records with `recovered is False`. (c) one call; only `safety_reply_sent` (no `case_write_failed`). Records read as `r.signal` on records with `r.name == "meridian.signal"` |
| `test_safety_while_representative_owns_chat` | AC-7 | state with `controller=Controller(kind="human", representative_name="Riley (demo representative)", case_ref=CaseRef("MHC-C-0009"))`; `_gated(TextPayload(WP5), controller=…)`; handoff double returns `_handoff_result(SAFETY, created=False, case_ref="MHC-C-0009")` | `state.gate.kind is GateKind.SAFETY` (GRC-3 A); one `open` call; `update["handoff"].created is False`; `update["handoff"].case.case_ref == state.controller.case_ref` |
| `test_wp2_locate_send_verify` | AC-8 (**WP-2**) | `store` fixture; phone read from the copy; turn 1: `FormPayload(card_id=f"locate-{TURN}", values=FormValues(name="Omar Patel", phone=SecretStr(phone)))` → `_gated` → `front.identity(state, _rt(ctx), deps=_deps(identity=idd, uow=spy))` with `idd = _IdentityDouble(locate=Located(masked_hint="the phone ending in 02"), send=<CodeSent above>, verify=<Verified above>, writer=<§6 SQL>)`, `spy = _SpyUow(store.uow)`. Turn 2: code built by the sentinel helper; `CodePayload(card_id=f"code-{TURN_CODE}", code=SecretStr(code))`, state `identity=<turn-1 identity>` | turn 1: `idd.calls == ["locate", "send_code"]`; the locate argument is a `Locator` with `customer_id is None`, `invoice_number is None`, `name == "Omar Patel"`; `send_code` got `(THREAD, "demo-session-36", NOW)`; `isinstance(update["identity_step"], CodeSent)`, `.masked_hint == "the phone ending in 02"`; `update["identity"] == <a fresh read: with store.uow() as tx: tx.core.reads.identity_state(THREAD)>`; `.status == "code_sent"`, `.codes_sent == 1`, `.customer_id == "MHC-10002"`. Turn 2: `idd.calls[2:] == ["verify"]`; verify got `ctx.ids` (equal to turn-2 ids), a `SecretStr` whose value equals the code, and `NOW`; `isinstance(update["identity_step"], Verified)`; `update["identity"].status == "verified"` and equals a fresh read. Every `spy.opened` entry has no `write=True` and no `exclusive=True` |
| `test_identity_results_passed_through` | AC-9 | `_UowDouble(<not_checked IdentityState>)` for every case. NotVerified causes: `no_match`, `ambiguous`, `no_contact` (the double's `locate` returns a fresh `NotVerified()` each), `incomplete` (form with `name` only → `from_form` → None). Code results: `CodeWrong(tries_left=2)`, `CodeExpired(resend_offered=True, sends_left=1)`, `CodeLocked()` from `verify`; `CodeCapReached()` from `send_code` after `Located` (locate turn) and from a `new_code` choice on `f"code-{TURN_PREV}"` with state `identity.status == "code_sent"` | the four `update["identity_step"].model_dump_json()` strings are equal and equal `NotVerified().model_dump_json()`; `incomplete`: double `calls == []`, `"identity" not in update`; each code result: `update["identity_step"] is <the object the double returned>`; `new_code`: `calls == ["send_code"]` (no `"verify"`); the locate-then-cap case: `calls == ["locate", "send_code"]`, step `is` the `CodeCapReached` returned |
| `test_code_and_form_values_never_leave_intake` | AC-10 | sentinels (§6); `caplog.set_level(logging.DEBUG)`; `log = []`; locate turn with `FormValues(name=NAME, phone=SecretStr(PHONE))` and a code turn with `CodePayload(code=SecretStr(CODE))`; identity double returning `Located`→`CodeSent`, then `Verified`; `_UowDouble`; run `gates` then `identity` on each turn, collecting every returned update and the applied states | for each sentinel `s` in `(CODE, PHONE, digits(PHONE), NAME)`: `s not in state.model_dump_json()` for every applied state; `s not in TypeAdapter(Any).dump_json(update).decode()` and `s not in repr(update)` for every update; for every `caplog.records` `r`: `s not in r.getMessage()`, `s not in repr(getattr(r, "signal", None))`, `s not in repr(r.args)`; `_used(log, "gateway") == []` |
| `test_front_nodes_write_only_own_keys` | AC-11 | Drive: gates over `WP5`, `WP6`, `PLAIN`, `DANGER_WORDS`, burn `"no"`, burn `"yes"`, locate form, code payload; safety over WP5 (success), WP5 (both writes fail), `burning_ask`; identity over locate (Located→CodeSent), incomplete form, code (CodeWrong), `FREE_TEXT` gate | gates: `set(u) <= {"gate", "check_events", "burning_card_id", "plan"}` and `"plan" in u` only for burn "no"; safety: `set(u) <= {"handoff"}`; identity: `set(u) <= {"identity_step", "identity"}`; no update from any of the three nodes contains `halt`, `planner`, `reply`, `open_tasks`, `settled`, `facts`, `draft`, `checked`, `specialist_results`, `escalation`, `controller`, `counters`, `shown_slots`, `chat_window`, `brief_extraction`, `danger`, `turn_input`, `thread_id` |
| `test_check_event_and_signal_records` | AC-12 | `caplog.set_level(logging.INFO, logger="meridian.signal")`; text `WP5 + " " + PHRASE` → gates → safety (success); text `DANGER_WORDS + " " + PHRASE` → gates → safety (success) | gate events: codes only (`("safety", "R5.co")` and `("danger_rule", "R8.danger_words")`), `PHRASE not in ev.model_dump_json()`; signal record per turn: `name == "safety_reply_sent"`, `turn_id == str(TURN)`, `thread_id == str(THREAD)`, `request_id == str(REQ)`, `run_tag == "live"`, `node == "safety"`, `cause == "safety"` / `"danger"`; `PHRASE not in json.dumps(r.signal)` and not in `r.getMessage()` |
| `test_front_module_imports` | PA-1 | `ast.parse(Path("src/meridian/agent/nodes/front.py").read_text())` | every imported module is in the §4.1 allowed set or starts with `meridian.domain.`; **required**: names `decide_gate`, `flags_from_state`, `burning_card_id` from `meridian.gates.gate`, `priority_for` from `meridian.policy.handoff`, `emit_signal` from `meridian.agent.signals`, `Locator` from a `meridian.domain.*` module (assert message `"required import missing: <name>"`); **forbidden**: `logging`, `sqlite3`, any `meridian.services*`, `meridian.adapters*`, `meridian.web*`, `meridian.agent.nodes*`, and no `ast.Call` whose func is `Name(id="print")`, and no attribute call named `get_secret_value` |
| `test_identity_without_form_or_code_calls_nothing` | PA-2 | identity node with a recording `_IdentityDouble` and `_UowDouble`, for: `PLAIN` text (FREE_TEXT gate); a `CARD_CHOICE` (`ChoicePayload(card_id="t-1.1", option="56")` with `open_tasks=[_booking_task()]`); burn `"no"`; a choice `"something_else"` on `f"code-{TURN_PREV}"` with `identity.status == "code_sent"` (CODE_ENTRY gate) | `update == {}`; `idd.calls == []`; `uow.opened == []` |
| `test_safety_refuses_non_safety_paths` | PA-3 | safety node with a `_HandoffDouble([])` on: `PLAIN` (FREE_TEXT, `danger=None`); `DANGER_FREE` with `DangerAssessment(label="normal", raised=False, failure=None)`; burn `"no"` | each `pytest.raises(ValueError)`; zero `open` calls; zero signal records |

### 7.2 Existing tests that must stay green

`tests/unit/` and `tests/graph/` files on `main` that touch `agent/`: AEA-21's `tests/unit/agent/test_*.py`,
`tests/unit/agent/nodes/test_compose*.py`, `tests/graph/test_spine.py`, `tests/graph/test_run_graph.py` (`test_spine.py`
and `_spine_doubles.py` import `meridian.agent.nodes.front` directly; the graph tests replace its functions with
doubles). **No known exception any more:** D-1 (§0 step 4) deletes `test_stubs_raise_loudly`'s three `front` rows, so
`tests/unit/agent tests/graph` must be fully green. Tests that AEA-34, AEA-38 and AEA-40 added under
`tests/unit/agent/nodes/` and `tests/graph/` run in G-5 too; they import no `front` symbol.

### 7.3 Gates (cheapest first; stop at the first red)

| # | Command | Passing looks like |
|---|---|---|
| G-1 | `uv run ruff check src/meridian/agent/nodes/front.py tests/unit/agent/nodes/test_front.py tests/graph/test_spine.py tests/journeys/j5/test_aea_36.py` | `All checks passed!` |
| G-2 | `uv run ruff format --check src/meridian/agent/nodes/front.py tests/unit/agent/nodes/test_front.py tests/graph/test_spine.py tests/journeys/j5/test_aea_36.py` | `4 files already formatted` |
| G-3 | `uv run mypy src/meridian/agent tests/unit/agent/nodes/test_front.py tests/graph/test_spine.py tests/journeys/j5/test_aea_36.py` | `Success: no issues found` (whole-repo mypy is 0 errors on `8a205b2` since the AEA-29 typing fix; if you also run plain `uv run mypy`, it must stay at 0) |
| G-4 | `uv run pytest tests/unit/agent/nodes/test_front.py -q -rA` | `21 passed` (16 functions; `test_burning_and_danger_paths` collects 6 rows); report the count and time |
| G-5 | `grep -rlE "agent\.nodes(\.front| import .*front)|nodes import .*front" tests eval` then `uv run pytest tests/unit/agent tests/graph -q -n 2` | the grep lists `tests/graph/_spine_doubles.py`, `tests/graph/test_spine.py` (before D-1; after D-1 only `_spine_doubles.py`) and `tests/unit/agent/nodes/test_front.py`; pytest: **all passed, 0 failed** (D-1 removed the three R-1 reds; the earlier runs saw `298 passed, 3 failed` and `308 passed, 3 failed`). Report the line verbatim |
| G-6 | `uv run python -m tests.journeys.affected --base main --list-only`, then the same without `--list-only` | prints the changed-file count and the affected journeys; every listed journey passes or is skipped `blocked-on AEA-NN`; none fails |
| G-7 | `uv run pytest -m journey tests/journeys/j5/test_aea_36.py -rs -q` | `1 skipped` with a reason naming `blocked-on AEA-NN`; on `8a205b2` expected `blocked-on AEA-51` (`reply_composer` / `run_graph`; AEA-29, 30, 40 and 44 are merged). `1 passed` if every need is bound. Never a failure or a collection error. Quote the line |

No full suite (no shared fixture, setting or dependency change). No paid model call anywhere.

### 7.4 Journey record (AC-13): `docs/testing/journeys/<YYYY-MM-DD>-AEA-36.md`

Same table shape as `docs/testing/journeys/2026-10-21-AEA-04.md`:

| Field | Value |
|---|---|
| Claim | AEA-36 `agent/nodes/front.py`: gate first on every turn, one `gate` event, burning card id, burning-"no" plan; safety node P0/P1 case with no model, identity or lookup call and one retry; identity node passes service results through and never copies the code or form values (AC-1…AC-12). Extends **J-5** (safety: CO alarm → approved instruction first, P0 case; DANGER → P1). No journey run. |
| Level | `mock-tested` |
| Tested revision | the `feat(graph)` commit SHA |
| Environment | VPS, Python 3.12 via `uv run`; node functions called directly with doubles; AEA-10 `temp_sqlite()` for AC-8; no server, no graph, no model |
| Command | G-4, G-5, G-6 and G-7 verbatim |
| Result | counts and time from G-4/G-5; the G-6 and G-7 output quoted (the J-5 step's blocked reason) |
| Evidence location | this file; GitLab issue #36 comment |
| Remaining limitations | Nodes run outside the compiled graph; routing (AEA-21), wording (compose/AEA-03), the real `HandoffService` (AEA-29) and `IdentityService` (AEA-27) are doubles; CAP-2 at the real entry point and the checkpoint-wide sentinel test are AEA-51's |
| Blocked by | the owner G-7 names. On `8a205b2` that is expected to be AEA-51 (`reply_composer`, `run_graph` and the graph wiring). AEA-29 (`handoff_service`), AEA-30 (`demo_clock`), AEA-40 (`turn_service`, `submitTurn`) and AEA-57 are merged and no longer block |
| Journeys that will exercise this code | J-5 (`tests/journeys/j5/test_aea_36.py`, this ticket, §7.6), J-3 (identity step before booking), J-1 (every turn passes the gate) |

### 7.6 J-5 journey file (AC-13): `tests/journeys/j5/test_aea_36.py` (implementer writes it; harness rules in `tests/journeys/support/README.md`)

API level on AEA-57's harness, modelled on `tests/journeys/j1/test_aea_57.py` (copy its call shapes). Rules: mark the
module `pytestmark = pytest.mark.journey`; never edit `tests/journeys/support/`; no `dependency_overrides`, no
monkeypatch of `meridian`, no `TestClient`, no doubles; every `/api` call names its `operation_id`; assert what the
client sees **and** what was stored. Module docstring (one triple-quoted string): `J-5 (slice plan section 0a), AEA-36 step: a CO-alarm message
gets the safety card first and one P0 case row, with no model call. API level on AEA-57's harness; the step is reported
blocked until AEA-40, AEA-51 and AEA-29 bind their services.`

```python
from __future__ import annotations

import uuid

import pytest

from meridian.policy.texts import TEXTS, TextId
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J5 = "J-5"
SIGN_IN_NEEDS = ("login_sessions", "demo_clock")
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
SAFETY_TURN_NEEDS = (*CHAT_NEEDS, "turn_service", "run_graph", "handoff_service")
WP5 = "My carbon monoxide detector is going off."
```

One test, `test_j5_co_alarm_instruction_first_and_p0_case(journey: JourneyRun) -> None`, three steps:

1. `with journey.step(J5, "1 login", needs=SIGN_IN_NEEDS, operations=("login",)):` `signed = journey.login()`.
2. `with journey.step(J5, "2 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):` `start =
   signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")`; assert `start.status_code ==
   201`; `thread_id = start.json()["thread_id"]`.
3. `turn_id = str(uuid.uuid4())`; `with journey.step(J5, "3 CO alarm: instruction first, P0 case",
   needs=SAFETY_TURN_NEEDS, operations=("submitTurn",)):`
   - `calls_before = len(journey.script.calls)` (script **nothing**: the safety path makes no model call);
   - `r = signed.client.call("POST", f"/api/chat/sessions/{thread_id}/turns", operation_id="submitTurn",
     body={"turn_id": turn_id, "payload": {"kind": "text", "text": WP5}})`; assert `r.status_code == 200`;
   - what the user sees: `first = r.json()["blocks"][0]`; `first["type"] == "safety"`; `list(first["steps"]) ==
     [TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH]]` (the words come from `policy/texts.py`; never type
     them);
   - no model before the reply: `len(journey.script.calls) == calls_before`; `journey.script.problems() == ()`;
     `journey.db.count("spend_ledger", "turn_id = ?", (turn_id,)) == 0`;
   - what was stored: `journey.db.count("cases", "thread_id = ?", (thread_id,)) == 1`; `case = journey.db.one("SELECT *
     FROM cases WHERE thread_id = ?", (thread_id,))`; `case["reason"] == "safety"`, `case["priority"] == "P0"`,
     `case["safety_kind"] == "co"`, `case["handoff_trigger"] == "safety"`, `case["rule_id"] == "R5.co"`,
     `case["turn_id"] == turn_id`; `first["case_reference"] == case["case_ref"]`; `turn = journey.db.one("SELECT * FROM
     turns WHERE turn_id = ?", (turn_id,))`; `turn["gate_result"] == "safety"`;
   - print one line: `step 3: block=safety case=<case_ref> priority=P0 model_calls=0`.

Column names checked on `5531664` (`schema/60_cases.sql`: `case_ref`, `thread_id`, `turn_id`, `reason`, `priority`,
`rule_id`, `handoff_trigger`, `safety_kind`; `schema/00_core.sql` `turns.gate_result`). If a step is blocked the harness
skips the test there (`pytest.skip("blocked-on AEA-NN")`), so later steps never run with unbound names. If, once
unblocked, an assertion fails because a sibling stores a value differently from DO-4 (e.g. `handoff_trigger`), that is a
seam finding for AEA-51's merge, not a reason to loosen the assertion.

### 7.5 Evidence to report back

Test-writer: the T-3 red output (one line per test with its failure reason), collect-only exit code, the commit SHA.
Implementer: G-1…G-7 output lines, the per-case lines the tests print, the two commit SHAs, the journey record path,
whether `test_stubs_raise_loudly` was red (R-1), and any name in §4 that differed on `main` (if any, you should have
stopped).

---

## 8. Risks and requests

- **R-1 · Collision with AEA-21's `test_stubs_raise_loudly`: resolved by deviation D-1 (§15).** The test
  parametrizes `(front, "gates" | "safety" | "identity", "front.py")` and expects the stub's `NotImplementedError`.
  With the nodes built, those three cases raise `AttributeError`. On `8a205b2` they are still present: `d724301` removed
  only the reply rows. Under the standing permission the orchestrator relayed, the implementer deletes the three
  `front` rows and the unused import in its own commit (§0 step 4). This ticket changes nothing else in `tests/graph/`.
- **R-2 · Journey file written now, blocked by the harness (AC-13; changed in the second refresh).** AEA-57 is merged,
  and its `journey.step(needs=…)` reports a step whose service is unbound as *blocked* (skipped, never passed, never
  red). So this ticket writes `tests/journeys/j5/test_aea_36.py` (§7.6) instead of deferring it; it turns into
  integrated evidence by itself once AEA-40, AEA-51 and AEA-29 bind `turn_service`, `run_graph` and `handoff_service`.
  AEA-51 still "first lands J-5" (slice plan §0a) with its own file; the two files never collide (one file per ticket).
- **R-3 · AC-5 wording vs routing (issue comment, no decision needed).** AC-5 says "`BURNING_ASK` never reaches the
  safety node", but DO-3 §5.4 and AEA-21's `route_after_gates` (step 4) send `BURNING_ASK` to `safety`. The node returns
  `{}` there (no case, no signal), so AC-5's evidence ("opens no case") holds either way; PA-3 tests it. Post on issue
  #36: "AC-5 last clause read as: a `BURNING_ASK` turn reaching the safety node opens no case and emits no
  `safety_reply_sent`."
- **R-4 · Two retries stacked (accepted; reported, no request blocks this ticket).** AEA-29's plan (step 4, its AC-6,
  R-6) retries inside `HandoffService.open` and raises `CaseWriteFailed` after two attempts, following DO-4 §7; this node
  keeps AC-6's own one retry, following graph-nodes §4. What that means once both are wired (AEA-51):
  (a) a persistent failure costs up to 4 rolled-back attempts; with SQLite's 5 s busy timeout
  (`adapters/sqlite/db.py` `BUSY_TIMEOUT_MS = 5000`) a fully locked database delays the safety instruction by up to about
  20 s instead of 10 s, still inside the 60 s turn deadline; (b) a failure that the service's own retry recovers emits
  no `case_write_failed`, because the service emits nothing. Neither changes a contract or what the customer sees (the
  instruction is sent either way). **Request to the orchestrator for AEA-51:** choose one owner of the safety-path retry.
  Recommended: keep the service's (CON-4 needs it too) and make this node skip its own retry when the exception reports
  `attempts >= 2`, as a short follow-up on `front.py` once `CaseWriteFailed` is on `main`. Not done here, because it
  would rely on AEA-29's exception shape, which is beyond the DO-4 signature.
  **Update on `8a205b2`:** `CaseWriteFailed` is now on `main` (`services/handoff.py`, carrying `.attempts = 2` and
  `.cause = "write_error"`). The node still keeps its own retry, for three reasons: AC-6 and the frozen tests require
  it; PA-1 forbids importing `meridian.services`; and reading attributes beyond DO-4 by duck typing would invent a
  contract. The request to AEA-51 / the orchestrator stands as written.
- **R-5 · Engineering choices made here (reversible, reported):** PA-4 rule ids (`R7.burning_yes`,
  `R7.burning_unsure`, `R47.classifier_danger`, `R47.classifier_burning_unclear`, fallbacks `R5.safety`,
  `R8.danger_words`); PA-2 no service call without a form or code; PA-3 `ValueError` on impossible routes;
  `identity` re-read only after a service call; identity-service exceptions propagate. None changes a contract.
- **R-6 · Sibling shape drift.** If `main`'s `domain/*`, `gates/gate.py`, `policy/handoff.py` or `agent/{context,
  signals}.py` differ from §4 in any name, stop and report (`blocked-on` the owner). The AEA-05 phrases in §6 are
  AEA-05/12 behaviour: if one does not gate as listed, stop and report.
- **R-7 · Shared context rows.** The A7d row is shared with AEA-37, and the `**Built:**` line and ICM row with every
  ticket: edit only this ticket's text; trivial text conflicts at merge are expected and resolved by keeping both
  sides.
- **R-8 · Disk** (`/` 83% used, 16 GB free at the fifth refresh, 2026-10-21; 6 worktrees exist): one worktree, hardlinked venv, no `node_modules`; AC-8's temp DB copies are
  removed by `temp_sqlite()`.
- **R-9 · AEA-37 edits the same lines of `test_spine.py` (merge-step note, no request).** AEA-37's resume note gives
  it the same permission for the `plan` rows. Its rows (110–112) sit right below this ticket's (107–109), and both
  tickets edit line 17's import. So whichever branch merges second gets a text conflict there. The correct union is:
  line 17 = `from meridian.agent.nodes import act`; the parametrize keeps only the three `act` rows; nothing else
  changes. The orchestrator's merge step resolves it that way and re-runs `tests/graph`. The other A7d edits shared
  with AEA-37 (area-map row, ICM row) follow R-7.
- **No contract change, no decision reopened.** Nothing here alters `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, DO-4
  or addenda types, or D-4…D-15. GRC-3 A and CAS-16 A are built as decided.

---

## 9. Readiness

**READY.** No product decision is open (GRC-3 and CAS-16 decided as recommended, D-14). Prerequisites (imports this
plan truly needs) — **all merged (`5531664`; unchanged on `a81f59d`, `dd1b110` and `8a205b2`)**; nothing is `blocked-on`:

- **AEA-02** — every domain type in §4.2 (incl. `HandoffReason.BURNING_RULED_OUT`, `GatesUpdate.burning_card_id`).
- **AEA-12** — `decide_gate`, `flags_from_state`, `burning_card_id` (and `parse_intake` in tests); transitively AEA-04,
  AEA-05.
- **AEA-14** — `priority_for` (and `promise_for` in tests).
- **AEA-21** — the `front.py` stub, `GraphDeps`, `emit_signal`, `tests/unit/agent/nodes/__init__.py`.
- **AEA-57** — the journey harness `tests/journeys/support/` (AC-13's file, §7.6; its steps report blocked, which is
  not a prerequisite for this merge).
- **AEA-10** — `temp_sqlite()`, `TempStore`, `SqliteUnitOfWorkFactory`, `core.reads.identity_state`, `format_wall`
  (AC-8 only; the node reaches the read through `deps.uow`).

AEA-11 (fakes) is in the slice-plan row but not needed: the tests carry their own doubles. AEA-27 and AEA-29 (both
merged) are injected (`deps.identity`, `deps.handoff`) and replaced by doubles. **Gates:** none (no human, paid or live gate).
**Security:** frozen tests first; `security-privacy-agent` reads this diff at the wave-2 merge.

---

## 10. Refresh log (2026-10-21, `16ca639` → `775f591` + AEA-21 `0a5b703`)

- **Checked, unchanged:** the ticket, slice-plan row and the `stage7/` addenda (no edits since `16ca639`); every §4 name
  and signature on `main` (AEA-02, 10, 12, 14) and on the AEA-21 branch; every §6 phrase gates as listed; Omar Patel is
  `MHC-10002` in the issued DB copy, phone ending in `02`; `tx.core.reads.identity_state` exists (AEA-10,
  `repos_core_aux.py`); ruff selects `S` (so S110 applies) and not `BLE`; `tests/**` ignores S101, S105, S106, S311.
- **Changed in this plan:** header and §1.2 (what is merged); §4.2 (all 25 `ConversationState` keys; `turn_input`
  required); §4.7 S-5 (production exception is AEA-29's `CaseWriteFailed`, caught as `Exception`); §3.3 and §8 R-4
  (AEA-29 now retries inside the service: stacked retry accepted, cost stated); §6 (gate preconditions the builders must
  set); AC-11 row (five more forbidden keys); step I-9 (the context rows as they look now: per-ticket `**Built:**` line,
  AEA-21's status column in the module tree, the AEA-12 ICM row); G-5 (the four affected test files); R-1 (still open;
  same guard as AEA-34 R-1); §9 (only AEA-21 outstanding).

## 11. Refresh log (2026-10-21, second refresh: `775f591` + `0a5b703` → `main` `5531664`)

- **Checked, unchanged:** the ticket, slice-plan row (§1 line 171) and collision map; step 0's import checks all pass on
  `5531664` with the expected output; the stub's three signatures and messages; `GraphDeps` 13 fields in order with
  `identity`/`handoff` still `Any` aliases; `emit_signal` logs `meridian.signal` with `extra={"signal": …}`;
  `route_after_gates` sends `SAFETY`, `BURNING_ASK`, `DANGER_RULE` and burning yes/unsure to `safety` and burning "no"
  through `route_act_plan` (so PA-3 and R-3 stand); `route_after_plan_join` sends a classifier raise to `safety`; every
  §6 phrase gates as listed through the real `parse_intake` + `decide_gate`; the A7d area-map row reads `planned`, the
  module-tree line ends `stub AEA-21 6df4f4c`, the AEA-12 ICM row is unchanged; `tests/unit/agent/nodes/__init__.py`
  exists.
- **Changed:** header, §1.2 and §9 (AEA-21 and AEA-57 merged; no `blocked-on`); §2.1 adds
  `tests/journeys/j5/test_aea_36.py`; §2.3; AC-13 row; step 0 note; I-8 and I-10; §7.2; G-5 (affected files on
  `5531664`, `-n 2`), G-6, new G-7; §7.4 *Blocked by*; new §7.6 (journey file spec; compose renders a `safety` block
  whose `steps` are `TEXTS[SAFETY_LEAVE_NOW]`, `TEXTS[SAFETY_DONT_TOUCH]`); R-1 (still open on main), R-2 (journey written
  now), R-8 (disk 90%).

## 12. Refresh log (2026-10-21, third refresh: `5531664` → `main` `a81f59d`)

- **Checked, unchanged:** `git diff 5531664 a81f59d` touches none of `src/meridian/{domain,gates,policy,agent}/`,
  `tests/{graph,journeys,fixtures,unit/agent}/`, `docs/plans/tickets/`, `docs/plans/slice-plan.md` (row line 171),
  `docs/design/contracts/`, `docs/plans/7b-decisions/` or `docs/plans/stage7-signoff.md`; so §3–§7's names, signatures,
  phrases and gate preconditions stand. Main gained AEA-17 (`adapters/models/anthropic.py`, `web/container.py`, contract
  tests) and one line each in the A2 area-map row, a new ICM routes row and the first `**Built:**` line; none is a row
  this ticket edits (A7d still `planned`; module-tree line still `stub AEA-21 6df4f4c`; the AEA-12 ICM row intact).
  R-1 still open. AEA-27, AEA-29, AEA-30, AEA-37 still unmerged (injected or not needed).
- **Changed:** header; new §0 (the existing branch build, merge-tree clean, roles for an existing vs a fresh worktree);
  §1.2, step 0 and §9 (re-checked on `a81f59d`); §7.1 adds `test_burning_ask_opens_no_case` (the frozen file's own
  split); G-4 expects 21 tests; G-5 records the earlier `298 passed, 3 failed`; §7.4 *Blocked by* names AEA-30
  (`demo_clock`) first; R-1 and R-8 figures.

## 13. Refresh log (2026-10-21, fourth refresh: `a81f59d` → `main` `dd1b110`)

- **Checked, unchanged:** `git diff a81f59d dd1b110` touches none of `src/meridian/{domain,gates,policy}/`,
  `src/meridian/agent/{context,signals,routers,graph}.py`, `src/meridian/agent/nodes/`, `tests/{graph,fixtures,
  unit/agent/nodes}/`, `tests/journeys/support/`, `src/meridian/adapters/sqlite/schema/`, `repos_core_aux.py`,
  `docs/plans/tickets/AEA-36.md`, `docs/plans/slice-plan.md`, `docs/design/contracts/`, `docs/plans/7b-decisions/` or
  `docs/plans/stage7-signoff.md`; so §3–§7's names, signatures, phrases, gate preconditions and AC-8's raw SQL stand.
  Main gained AEA-18 (Jev adapter), AEA-28 (scheduling; `agent/tools/scheduling.py`, J-3/J-4 journey files) and AEA-27
  (`services/identity.py`, `repos_identity.py` body, `agent/tools/account.py`, `register_identity` in
  `web/container.py`, `tests/journeys/j3/test_aea_27.py`). `GraphDeps.identity`/`.handoff` are still `Any` aliases.
  `test_stubs_raise_loudly` still has no guard (R-1 open). The G-5 grep still lists `tests/graph/_spine_doubles.py`
  and `tests/graph/test_spine.py`. J-5's `SAFETY_TURN_NEEDS` does not include an identity need, so AEA-27's
  `register_identity` does not unblock the J-5 step; `demo_clock` (AEA-30) is still the first unbound need.
- **Changed:** header (base `dd1b110`, branch head `6a79b5a`); §0 (the branch already merged main in `6a79b5a`, with two
  context-file conflicts resolved correctly; role A step 2 becomes a check; the post-merge re-run in step 5 is still
  owed; neither role merges to main: the orchestrator merges by wave along the dependency tree); §1.2 (AEA-27 merged,
  still injected); step 0 (an `IdentityService` signature check; the stub grep prints nothing on the existing branch);
  §7.4 *Blocked by*; R-1, R-8 figures; §9.

## 14. Refresh log (2026-10-21, fifth refresh: `dd1b110` / branch `118e0a1` → `main` `8a205b2`)

**Checked, unchanged.**
- `git diff b559c75 8a205b2` touches none of `src/meridian/{domain,gates,policy}/`,
  `src/meridian/agent/{context,signals,routers,graph}.py`, `src/meridian/agent/nodes/front.py`, `tests/fixtures/`,
  `tests/journeys/support/`, `docs/plans/tickets/AEA-36.md`, `docs/plans/slice-plan.md`, `docs/plans/7b-decisions/` or
  `docs/plans/stage7-signoff.md`. So §3–§7's names, signatures, phrases and gate preconditions stand.
- `GraphDeps.identity` and `.handoff` are still `Any` aliases.
- The branch's `front.py` (`712b9e9`, unchanged at `118e0a1`) matches §4.
- The frozen `test_front.py` is unchanged since `76fe4c2`; it is the only commit on that path.
- The worktree is clean.

**What moved on main.**
- AEA-29 merged (`ef561fc`). `services/handoff.py` `HandoffService.open(self, req, ctx)` matches §4.4. It retries once
  inside and raises `CaseWriteFailed(attempts=2)`, which has `.attempts` and `.cause = "write_error"`.
- `stage7/cases.md` gained §5a, the list of AEA-29's built additions. Nothing in it is a type or signature this ticket
  uses.
- AEA-30, 34, 38, 40 and 43 merged. They added tests under `tests/unit/agent/nodes/`, `load_context.py` and
  `reply.py` bodies, and the chat routes.
- `d724301` dropped the stale reply rows and the `reply` import from `test_stubs_raise_loudly`. The three `front` rows
  remain.

**Changed in this plan.**
- Header and §0: role A this round is merge main (one predicted area-map conflict, exact resolution), D-1 stub rows,
  gates, record. No test-writer.
- §1.2: AEA-29 merged; the J-5 blocker is now AEA-51 only.
- §2.1: new owned row `tests/graph/test_spine.py` (D-1). §2.2 updated to match.
- §3.1: AC-13 row. §3.3: the collision row is resolved by D-1.
- Step 0: `HandoffService.open` signature check.
- §5 *Do not*: the `test_spine.py` limit.
- §7.2: no known exception left.
- G-1…G-3 cover `test_spine.py` and the J-5 file. G-5 expects 0 failed. G-7 expects `blocked-on AEA-51`.
- §7.4: *Blocked by*.
- §8: R-1 resolved, R-4 updated, R-8 disk figure, new R-9 (AEA-37's edit to the same lines of `test_spine.py`).
- §9; new §15.

## 15. Deviations

- **D-1 · `tests/graph/test_spine.py` (AEA-21's file) gets one narrow edit on this branch.**
  - **The edit.** Delete the three `front` rows of `test_stubs_raise_loudly` and the now-unused `front` import (§0 step
    4). Nothing else.
  - **Basis.** The orchestrator's resume note for ticket 36 relays Innocent's standing permission of 2026-10-21 ("just
    do whatever you recommend"): when a graph-node ticket is built, the now-stale stub rows of that node are deleted,
    plus an import that becomes unused, and nothing else in the file. Same pattern as the merged `d724301` (reply
    rows).
  - **Why.** Once `front.py` is built, those rows call `fn(None, None, deps=None)` and get `AttributeError` instead of
    the stub's `NotImplementedError`. That makes three permanent reds, which would block every merge gate that runs
    `tests/graph`.
  - **Risk.** It is a test-only edit and weakens no assertion about built code. The `plan` and `act` rows stay until
    their tickets land.
  - **Commit:** _(implementer appends the SHA here)_.
- **D-2 · AC-5 wording vs routing** (unchanged from R-3). `BURNING_ASK` does reach the safety node (DO-3 §5.4,
  `route_after_gates`). The node returns `{}` there: no case, no signal (PA-3). AC-5's evidence holds.

- **D-1 applied:** rows removed in commit `a3874c8` on `aea-36-aea-36-front-node` (standing permission, Innocent 2026-10-21). Deviation: merging main (beyond 8a205b2) also conflicted in `.claude/state/icm-progress.md` (the "Last reconciled" line); resolved by keeping main's line and prepending the AEA-36 entry.
