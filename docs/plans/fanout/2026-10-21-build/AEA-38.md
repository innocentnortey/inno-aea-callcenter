# Plan — [AEA-38] graph: reply node (facts, responder, brief, checks)

**Status:** planned — **READY**; **already built on its branch** (see *Build state* below). Nothing blocks: AEA-21 is
merged (`5531664`), so the stub file, `GraphDeps` and `emit_signal` are on `main`.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/38 (spec copy:
`docs/plans/tickets/AEA-38.md`) · **Base revision:** `main` `2ec19ad` (first written against `96096be`, refreshed on
`19e046b`, re-checked 2026-10-21 on `2ec19ad`) · **Planner:** fanout-planner on `claude-opus-5-5` · **Slug / branch:**
`graph-reply-node` → `aea-38-graph-reply-node` · **Implementer:** `fanout-implementer` on Sonnet · **Lane:**
`lane::build-loop` · **Risk:** none (no `risk::security`): no test-writer; the implementer writes the tests named in §7
with the code (rule `build-loop-test-scope`).

**Build state at this re-check (2ec19ad).** Branch `aea-38-graph-reply-node`, worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-38`, cut from `b559c75`, holds two commits: `ec94722`
(`feat(agent): reply node - facts, responder, brief, R-46 checks (AEA-38)`) and `72b1152` (`docs(AEA-38): journey record
and context rows for the reply node`). They touch exactly the §2.1 files (15 files). The record
`docs/testing/journeys/2026-10-21-AEA-38.md` reports: reply test folders 64 passed; affected set 362 passed, 4 failed (the
four `test_stubs_raise_loudly[...reply-*]` cases, R-1); J-2 file `1 passed, 2 skipped` (`blocked-on AEA-40, AEA-51`);
affected journeys `1 passed, 2 skipped`. Sizes: `nodes/reply.py` 385 lines, `prompts/reply.py` 442 lines (over the
400-line aim of Step 2, under the 600 hard cap: acceptable, do not split). Ledger row AEA-38 still reads `ready` (not
merged). `main..b559c75` differs only in `docs/plans/fanout/2026-10-21-build/AEA-29.md`, so the branch needs no rebase.

**Re-check at `2ec19ad` (this pass).** `git diff --stat 19e046b..main` touches only `.claude/state/build-ledger.md` and
the AEA-03b / AEA-29 plan files: no source, test or contract changed, so every name in §4 still holds. AEA-29's branch
(`b54fed9`, not merged) still has `open_case_for_thread(thread_id) -> CaseSummary | None`, `attach_brief(case_ref, brief)
-> None` raising `ValueError("brief belongs to another case")` on mismatch, `assemble(case, state, lookups) -> Brief`
and `attach_extraction(brief, extraction, check, *, customer_messages=None) -> Brief`; it does not edit
`agent/context.py`, so `GraphDeps.brief` / `.cases` stay `Any` aliases and the §6 doubles type-check after it merges.
`tests/graph/test_spine.py::test_stubs_raise_loudly` (parametrize lines 117–120, test line 123) is unchanged: R-1 is
still open.

**What the `19e046b` refresh changed (everything else held and is unchanged; all still true on `2ec19ad`):**
1. **AEA-21 is on `main`.** The four stub signatures, `GraphDeps` (13 fields, same order) and `emit_signal` are identical
   to the branch copy the first plan used. New detail: `emit_signal` raises `ValueError("signal record is for another
   turn")` when the record's `turn_id` / `thread_id` differ from `ids`; `_signal` (§5 step 4) always builds both from
   `ctx.ids`, so it never trips.
2. **AEA-57's journey harness is on `main`** (`tests/journeys/support/`, the `journey` fixture, `needs` / `operations`
   blocking). PD-12 changed: this ticket now **creates `tests/journeys/j2/test_aea_38.py`** with one runnable
   `mock-tested` step and two integrated steps declared with their needs, which report `blocked-on AEA-40, AEA-51`
   until those land (the pattern of AEA-27's `j3/test_aea_27.py` and AEA-34's `j3/test_aea_34.py`).
3. **AEA-27's account executor is on `main`.** Its lookup snapshot (`agent/tools/account.py` `_invoices_seen`) is
   `"INV-204411 total $478.00 balance $478.00 lines $89.00 / $245.00 / $144.00"`: staff notes never go into it (GRT-4).
   The WP-2 fixture now uses that exact format (scratch-checked: the "$149" sentence is removed, the billed sentence
   stays). The old R-4 is closed; a new R-4 covers the FAQ passage that *does* say "$149", with one responder rule added
   (PD-15).
4. **Merges follow the wave tree, not one ticket at a time** (Innocent, 2026-10-21: "we shouldnt be merging 1 ticket at a
   time, we should merge in accordance to the tree"). The `test_stubs_raise_loudly` fix (R-1) lands once, at the wave
   merge, for every node ticket in it. The implementer never merges and never pushes.
5. **Fixture module renamed** `tests/unit/agent/nodes/reply_fixtures.py` (was `_reply_doubles.py`), matching the folder's
   `compose_fixtures.py` and AEA-34's `load_context_fixtures.py`.
6. **AEA-29's branch** (`aea-29-aea-29-cases-handoff`, not merged) confirms the DO-4 signatures this plan calls. Its
   `attach_extraction` adds an optional keyword `customer_messages`; this plan calls the DO-4 three-argument form only
   (R-9). Its `attach_brief` raises `ValueError` when `brief.case_ref != case_ref`; the double mirrors that.
7. **Context rows (AC-15):** the `docs/design/code-design.md` tree row for `nodes/reply.py` now ends `stub AEA-21
   6df4f4c`; Step 9 replaces that suffix and also appends a `**Built:**` line (the AEA-27 / AEA-28 pattern).

**Drift check at this refresh:** `git log 96096be..main` over `src/meridian/{domain,ports,privacy,checks.py}`,
`agent/gateway.py`, `policy/limits.py`, `adapters/sqlite/repos_core*.py`, `tests/fakes`, `tests/fixtures/sqlite.py`,
`tests/unit/agent/_gateway_doubles.py`, `tests/conftest.py` shows only `policy/texts.py` (AEA-13, AEA-03b) and
`domain/views.py` (AEA-02b), neither used here. Every name in §4 was re-read on `19e046b`.

---

## 1. Goal and sources

### 1.1 Goal (issue `docs/plans/tickets/AEA-38.md`, *What to build*)

> **US-16:** "As a **homeowner**, I need the assistant never to say "done", "cancelled" or "refunded" unless it really did
> it, and to hand me to a person when it hits a limit, so that I can believe what it says." (Also US-4, US-7, US-17.)

`agent/nodes/reply.py` replaces AEA-21's four stubs with the real `facts`, `responder`, `brief` and `checks` node
functions. `agent/prompts/reply.py` holds the responder and brief wording, the model-facing input types and the trimmed
output schemas. Concretely, for one turn:

- **Input (WP-4F turn 4):** Linda Foster (fictional, `MHC-10001`) types "Yes, please." Turn 3 already stored a `moved`
  row (appointment 159 → Monday 2026-10-19, 08:00–12:00, Marta Kowalski).
- **Process:** `facts` re-reads `settled` from the DB (`core.settled_for(thread_id, ctx.now)`) and finds the `moved`
  row. `responder` sends Sonnet that row under "ALREADY DONE IN THIS CONVERSATION" and gets the draft "Yes, it's moved:
  Monday, October 19, 8:00 am to 12:00 pm with Marta.". `checks` runs `check_completion` (the claim "moved" matches the
  stored row, SDQ-8 = A) and `check_facts` ("October 19", "8:00", "12:00" are in the evidence).
- **Output:** `checked = CheckedReply(text=<the draft, unchanged>, removals=(), fallback_used=False, events=(completion
  pass, fact pass))`, which AEA-21's compose turns into the reply.

### 1.2 Context (why this ticket exists)

SP-1 found the seam bug this ticket closes: a follow-up turn could not see what an earlier turn had done, so the model
either denied a completed move or claimed one that never happened. DO-3 makes `facts` re-read `settled` from the DB every
turn and makes R-46's checks (AEA-15, on `main`) the gate between the model's words and the customer. Wave 2; its
siblings AEA-34/36/37/39 fill the other node stubs in parallel, AEA-29 builds the case and brief services, and AEA-51
(wave 3) wires the whole graph into CON-2.

### 1.3 Sources (each one opened for this plan)

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-38.md` | AC-1…AC-15 (§3 below), WP-4F / WP-8 / WP-7 pairs, scope boundary, must-not-edit list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-38 (owned `nodes/reply.py`, `prompts/reply.py`; blockers 10, 11, 15, 21; calls gateway 20, brief assembler 29), §0a J-2 (first landed by AEA-51; extended by 33, 35, 38), §3 collision map (`agent/nodes/*`, `agent/prompts/*`: one owner each; `tests/journeys/`: each build ticket adds only `j<N>/test_aea_<NN>.py`) | Owned files; journey J-2; file ownership |
| Requirements (PRD) | `docs/prd/inno-aea-callcenter-prd.md` R-4, R-13, R-28, R-44, R-45, R-46; HP-1, HP-4 | Exact numbers from tools; no completion claim without a write; eight-heading brief; quick checks; typed state; R-46 checks |
| Worked pairs | `docs/data/worked-pairs.md` WP-1, WP-2 (✓ "wp2 144": explain the line as billed, $144; the agent does not raise $149 on its own), WP-3, WP-4F, WP-7, WP-8 | Test data and the PD-15 responder rule |
| Code design DO-3 | `docs/design/code-design.md` §1 (WP-4F turn), §3 tree rows `nodes/reply.py`, `prompts/reply.py`, §4.5, §5.1–§5.4 | `facts` is the one committer of durable task state; responder ∥ brief, then checks, then compose |
| Component contracts DO-4 | `docs/design/contracts/internal-components.md` §1 (`Settled`, `ChatLine`), §7 (brief types, `BriefAssembler`; staff-only text never in a `ResponderInput`), §8 (`TurnFacts`), §9 (`ResponderInput`, `ResponderDraft`, `CheckedReply`), §10 (R-46, SDQ-8 A), §11 (*Responder* failure row), §12 (`StructuredRequest`, roles, caps), §13 (`CaseService`), §16 (addenda win) | Exact types and signatures in §4 |
| Stage 7 addenda (win over DO-4) | `stage7/graph-nodes.md` §1, §2, §3, §4, §8, §9.1, §9.6; `stage7/graph-core.md` §4, §5, §6, §7, §8, §11; `stage7/cases.md` §1.2, §5; `stage7/graph-tools.md` §3, §6 | `CheckEvent` builders, brief flow, signals, quick checks, node signatures, counters, halt routing |
| Decisions | `docs/plans/7b-decisions/graph-nodes.md` GRN-1…4, GRN-8, GRN-10, GRN-11; `graph-core.md` GRC-7, GRC-12…15; `docs/plans/stage7-signoff.md` D-4…D-15 (none concerns this ticket) | Followed as written; no signed decision is answered differently |
| AEA-02 plan §8.2 | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §8.2 | `ResponderInput` (needs `SettledForModel`, `ResponderRules`), `AccountFactsView`, `LastLookups`, `ChangeRequestRef`, `MissingInfo`, `NoticeCode` were **not built**; owning topic "graph-nodes / AEA-38". AEA-02b (merged) built only `domain/views.py`. This plan settles the three prompt-side types inside its own module (PD-1…PD-3) and records the rest as R-2 |
| Rules | project `.claude/rules/build-loop-test-scope.md` (+ *AEA addition*: affected journeys before the final commit), `integrated-journeys.md` §3–§4, `context-maintenance.md`; workspace `context-management-multi-turn.md` rules 1–4; `agent-architecture.md` rules 3, 4, 12; `pydantic-ai-agents.md` §3, §4 | Tests per role; journey file and record; turn-2+ prompt test; one module owns wording; trimmed schema in the prompt |
| Evaluation DO-5 | `docs/design/evaluation-plan.md` via the ticket's *Evaluation* | E-1 hard gate "no completion claim without a successful write" (SDQ-8 A); E-1 must-say / must-not-say for WP-1, WP-2; E-6 brief invented facts. Run at AEA-51 (other-ticket) |
| Observability DO-6 | via the ticket's *Observability* (WF-1) | R-46 `check_event`s in `checked.events`; `brake` event in `check_events`; `signal` LOG records; codes and counts only |
| Metrics DO-7 | via the ticket's *Metrics* | M-8, M-12, M-21 computable from the events; no target set |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer may create or edit)

| File | On `main` (`2ec19ad`; on the branch all exist) | Change |
|---|---|---|
| `src/meridian/agent/nodes/reply.py` | AEA-21 stub (33 lines) | **Replace the four stub bodies**; keep the four signatures byte-for-byte; add private helpers (§5 steps 3–6) |
| `src/meridian/agent/prompts/reply.py` | missing (package `agent/prompts/__init__.py` exists) | **Create** (§5 step 2) |
| `tests/unit/agent/nodes/reply_fixtures.py` | missing | **Create**: builders and doubles for the reply tests (§6) |
| `tests/unit/agent/nodes/test_reply_facts.py` | missing | **Create** (§7.1) |
| `tests/unit/agent/nodes/test_reply_checks.py` | missing | **Create** (§7.1) |
| `tests/unit/agent/nodes/test_reply_brief.py` | missing | **Create** (§7.1) |
| `tests/unit/agent/nodes/test_reply_keys.py` | missing | **Create** (§7.1) |
| `tests/unit/agent/prompts/__init__.py` | missing | **Create**, empty |
| `tests/unit/agent/prompts/test_reply_prompts.py` | missing | **Create** (§7.1) |
| `tests/unit/agent/prompts/test_reply_prompt_turns.py` | missing | **Create** (§7.1) |
| `tests/journeys/j2/test_aea_38.py` | missing (`tests/journeys/j2/__init__.py` exists, empty) | **Create** (§7.2, AC-14) |
| `docs/testing/journeys/<YYYY-MM-DD of the run>-AEA-38.md` | missing | **Create** (AC-14 record, §5 step 8) |
| `.claude/reference/area-map.md` | exists | **Only** the A7c row's *Status* cell (AC-15) |
| `.claude/state/icm-progress.md` | exists | **Append one** "Routes verified against code and tests" row (AC-15) |
| `docs/design/code-design.md` | exists | **Only** the two §3 tree rows `nodes/reply.py` and `prompts/reply.py`, plus one appended `**Built:**` line (AC-15) |

`tests/unit/agent/nodes/__init__.py` and `tests/journeys/j2/__init__.py` exist; do not create or edit them.

### 2.2 Shared surfaces: read only, never edit

`src/meridian/checks.py` (AEA-15), `agent/nodes/compose.py`, `agent/graph.py`, `agent/routers.py`, `agent/context.py`,
`agent/signals.py`, `agent/nodes/{load_context,front,plan,act}.py` (AEA-21/34/36/37/39), `agent/gateway.py` (AEA-20),
`agent/tools/*` (AEA-22/27/28/33), `services/*`, `domain/*`, `ports/*`, `policy/*`, `privacy/*`, `adapters/**` (incl.
every `repos_*.py`), `config.py`, `web/**`, `tests/fakes/*`, `tests/fixtures/*`, `tests/conftest.py`,
`tests/unit/agent/_gateway_doubles.py`, `tests/unit/agent/nodes/compose_fixtures.py`, `tests/unit/test_checks.py`,
`tests/graph/*` (AEA-21; see R-1), `tests/journeys/support/**`, `tests/journeys/affected.py`, every other
`tests/journeys/j*/test_aea_*.py`, `pyproject.toml`, `uv.lock`, `.claude/state/build-ledger.md`. **Never:** the briefing,
`docs/data/issued/**`, `docs/archive/**`, `docs/parked/**`, `docs/ux/**`, `apps/web/**`,
`docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`.

### 2.3 Other slices this one must not touch

AEA-21 (spine, compose, `tests/graph/test_spine.py::test_stubs_raise_loudly`), AEA-29 (`services/{cases,handoff}.py`,
`BriefAssembler`, `CaseService`), AEA-34 (`load_context`, which builds `chat_window`), AEA-36/37/39 (other node files),
AEA-40 (TurnService persists `check_events`), AEA-51 (container `register_graph`, its own J-2 file), AEA-57 (journey
harness).

---

## 3. Requirements table

| ID | Requirement (ticket verbatim or cited) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 [invariant] | `settled` comes from the database: a specialist result reporting a `booked` write puts it in `settled` only because the `actions` row exists (read through `core.settled_for(thread_id, ctx.now)`); a result claiming a write with no row adds nothing | `facts` step F-2: one read-only unit of work, `tx.core.settled_for(...)`; `writes_this_turn` and `bookings` come from that `Settled`, never from `SchedulingResult.write` | `tests/unit/agent/nodes/test_reply_facts.py::test_settled_reread_from_db` — `settled.actions` equals the stored rows in both cases |
| AC-2 [invariant] | WP-4F turn 4: "it's moved" passes against `settled` and is kept; the same draft with no `moved` row is removed | `checks` step C-3 (`check_completion`, then `check_facts` on its result) | `tests/unit/agent/nodes/test_reply_checks.py::test_wp4f_turn4_claim_backed_by_settled` — `removals == ()` vs one `no_completed_action` removal |
| AC-3 [failure/refusal] | WP-8: "Done, auto-renew is off." removed; "Done, your visit is booked." kept with a `booked` action; event `completion`/`trimmed`, `removed=1`, `claim_kinds=("completion",)`, no removed text | Same step; `CheckEvent.from_check("completion", …)` | `test_reply_checks.py::test_wp8_generic_done_removed` |
| AC-4 [failure/refusal] | WP-2: "$149" sentence removed (`not_in_evidence`) when evidence holds billed "$144"; the $89 / $245 / $144 sentence stays | C-3 with `build_evidence(facts, settled, lookups)`, lookups from `tx.core.lookup_log.for_thread` | `test_reply_checks.py::test_unmatched_amount_removed` |
| AC-5 [failure/refusal] | Responder failure after its retry → `fallback_used=True`, a `fallback` check event, `responder_fallback` with `cause` = failure kind; every sentence removed → `fallback_used=True`, signal `cause="all_removed"`; neither raises; no model text in `checked.text` | Responder step R-5 emits the failure signal; checks C-2/C-3 set `fallback_used` and emit `all_removed` (PD-8) | `test_reply_checks.py::test_responder_failure_and_empty_draft_fallback` |
| AC-6 [failure/refusal] | Brief only when `deps.cases.open_case_for_thread` returns a case; `attach_brief` first with `being_written`, again with final; failed extraction → headings 2, 4, 7 `not_generated`, 1, 3, 5, 6, 8 stay, `brief_failed`; `attach_brief` raising → `brief_failed`/`write_error`, turn completes | Brief steps B-1…B-9, checks C-4, `_store_brief` (PD-6, PD-9) | `tests/unit/agent/nodes/test_reply_brief.py::test_brief_only_when_case_opened`, `::test_brief_stored_twice`, `::test_brief_failure_not_generated`, `::test_attach_brief_failure_does_not_fail_turn` |
| AC-7 [invariant] | WP-7 quotes "It didn't fix anything", "I had to call another company" kept as exact substrings; a paraphrase removed (`quote_not_found`); a number in `open_decision` in neither lookups nor chat removed; events `brief_quote`, `brief_fact` with counts | C-4: `check_quotes(ext, shown)`, `check_facts(open_decision, build_evidence(facts, settled, lookups, chat))` | `test_reply_brief.py::test_brief_quote_and_fact_checks` |
| AC-8 [negative] | `ResponderInput` for WP-2 holds no staff note, no `agent_discretion_notes` text, no raw tool output, no promise text, no case reference, no code, no card-like number; `ResponderDraft` has no promise/reference field; no check event and no `signal` record holds draft or message text | Projections in `prompts/reply.py` (PD-2, PD-3, PD-11, PD-13); signals carry codes only | `tests/unit/agent/prompts/test_reply_prompts.py::test_responder_input_excludes_staff_tool_output_and_promise` |
| AC-9 [invariant] | Turn-2+ full prompt: recording fake model on turns 1, 2, 5 (WP-3 → WP-4F); stable `system_prefix` (automated assistant, not a person; the rules) byte-identical and complete; `settled` and this turn's facts under their labels; window = `state.chat_window` as given, within graph-core §7 caps | `RESPONDER_SYSTEM_PREFIX` is a module constant; `responder_input` never reads `messages` | `tests/unit/agent/prompts/test_reply_prompt_turns.py::test_stable_prefix_turns_1_2_5` |
| AC-10 [invariant] | Counters per graph-core §8 (`failed_answers`, `corrections`, `identity_failures`, `bookings`; `timeouts` untouched); quick checks: two passages (one repeated) → two ids in order, both passages in `TurnFacts.passages` | Facts F-6…F-9, `_next_counters` | `test_reply_facts.py::test_failure_counters_rules`, `::test_quick_checks_into_turn_facts` |
| AC-11 [failure/refusal] | Gateway `BRAKE_SONNET_CALLS` on the responder → `Halt(reason=BRAKE_SONNET_CALLS, node="responder")`, one `brake` event `codes=("brake_sonnet_calls","responder")`, one `brake_fired` | Responder R-4 (the gateway already names the node `"responder"`) | `test_reply_checks.py::test_sonnet_brake_on_responder` |
| AC-12 [invariant] | Each node returns only its `TypedDict`'s keys; type check passes | Return types annotated as the `TypedDict`s | `tests/unit/agent/nodes/test_reply_keys.py::test_reply_nodes_write_only_own_keys` + `uv run mypy` |
| AC-13 [capture] | `checked.events` holds one event per check run (`completion`, `fact`; on a brief turn `brief_quote`, `brief_fact`) with `pass`/`trimmed`/`fallback`; signals carry `turn_id`, `thread_id`, `request_id`, `run_tag`, `node` and codes only | C-2…C-5; `_signal` helper | `test_reply_checks.py::test_check_events_and_signals_emitted` |
| AC-14 [journey] | Extends J-2 in `tests/journeys/j2/test_aea_38.py` with the scripted adapter (WP-2 billed $89 / $245 / $144 with source chip, no "$149", stored `completion` and `fact` rows; WP-1 cites the current membership document); until AEA-51's J-2 lands, the record states level `mock-tested` and *Blocked by* | **PD-12:** the journey file holds one runnable mock-tested step (real `facts` → `responder` → `checks` through `timed_node`, real gateway over a scripted fake, real `ReplyComposer`, temp DB copy) and two integrated steps declared with `needs` / `operations` that report `blocked-on AEA-40, AEA-51` | `uv run pytest -m journey tests/journeys/j2/test_aea_38.py -q -rs` → `1 passed, 2 skipped`; record `docs/testing/journeys/<date>-AEA-38.md` at level `mock-tested`, *Blocked by* AEA-40, AEA-51 |
| AC-15 [regression/context] | Area-map A7c row, ICM *Routes verified* row, DO-3 §3 rows for both files marked built, in the same change | §5 step 9 | `git diff --name-only main...HEAD` shows the three docs; only these rows changed |
| (plan-added) PA-1 | `facts` is the one committer of `open_tasks` and `shown_slots` (DO-3 §5.3); no contract states the rules, so this plan fixes them (PD-5) | `_next_open_tasks`, `_next_shown_slots` | `test_reply_facts.py::test_open_tasks_lifecycle`, `::test_shown_slots_replaced_and_cleared` |
| (plan-added) PA-2 | `facts` still runs on a halted state (graph-core §5) | No early return on `state.halt` | `test_reply_facts.py::test_facts_runs_on_halted_state` |
| (plan-added) PA-3 | A `DEADLINE` halt on the responder writes the halt, no `brake` event, no signal (graph-nodes §1: `from_halt` is only for brakes) | Responder R-4 | `test_reply_checks.py::test_deadline_halt_on_responder_no_brake_event` |
| (plan-added) PA-4 | `BRAKE_SONNET_CALLS` on the brief writes halt + `brake` event + `brake_fired` (graph-nodes §1 table) | Brief B-7 | `test_reply_brief.py::test_brief_sonnet_brake` |
| (plan-added) PA-5 | Staff-only `internal/` passages never reach the responder (DO-4 §7, HP-3) | `facts_for_model` drops them (PD-11) | `test_reply_prompts.py::test_internal_passages_never_rendered` |
| (plan-added) PA-6 | The prompt names the exact labels and its trimmed schema matches `ResponderDraft` / `BriefExtraction` (integrated-journeys rule 4, prompt ↔ consumer) | `trimmed_schema` generated from the models | `test_reply_prompts.py::test_labels_and_schema_in_requests` |
| (plan-added) PA-7 | WP-2 ruling "wp2 144": the agent explains the line as billed and does not raise $149 on its own (worked-pairs WP-2) | One responder rule (PD-15) | `test_reply_prompts.py::test_labels_and_schema_in_requests` asserts the rule line is in `RESPONDER_SYSTEM_PREFIX` |

### 3.1 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| `settled` re-read from the DB after this turn's writes | graph-core §6, GRC-12, DO-3 §5.1 | AC-1 | in-ticket | F-2 |
| `facts` is the one committer of durable task state (`open_tasks`, `shown_slots`) | DO-3 §5.3 | partly (keys named, rules not) | added (PA-1) | F-10, F-11, PD-5 |
| `facts` runs on a halted state | graph-core §5 | text only | added (PA-2) | F-1 |
| `last_lookups`, `pending_change`, `TurnFacts.account` / `missing` / `notices` | DO-4 §8, graph-nodes §9.1 | named in *What to build* | blocked-on a domain follow-up; not invented here | R-2 (PD-3, PD-4) |
| Completion and fact checks, SDQ-8 A | DO-4 §10, GRN-1 | AC-2, AC-3, AC-4 | in-ticket | C-3 |
| Responder failure → fallback and `degraded_handoff` / `model_error` | DO-4 §11 | AC-5 | in-ticket (the outcome itself is compose's, AEA-21) | R-5, C-2; R-3 |
| Brief assembled, stored twice, extraction checked | graph-nodes §3, GRN-8, cases.md §5 | AC-6, AC-7 | in-ticket | B-1…B-9, C-4 |
| Brake events: `from_halt` only for brakes | graph-nodes §1 | AC-11 (responder) | in-ticket + added (PA-3, PA-4) | R-4, B-7 |
| Staff-only text never in `ResponderInput` | DO-4 §7, HP-3 | AC-8 | in-ticket + added (PA-5) | PD-11 |
| Prompt ↔ consumer (labels, schema) | integrated-journeys §3 rule 4 | no | added (PA-6); the cross-module check is AEA-60's | Step 2 |
| WP-2 "wp2 144" ruling | worked-pairs WP-2 | no | added (PA-7) | PD-15 |
| Window caps (≤ 10 turns, 600 chars per line, 8,000 total) | graph-core §7 | AC-9 asserts them | other-ticket (AEA-34 applies them; this node never cuts) | — |
| Persist `check_events` rows | graph-core §11 | AC-13 note | other-ticket (AEA-40 TurnService; CAP-1 at AEA-51) | — |
| E-1 / E-6 eval runs | DO-5 | *Evaluation* | other-ticket (AEA-24 harness, AEA-51 run) | — |
| CON-12 shows the stored brief | DO-4 §13 | *Observability* | other-ticket (AEA-45) | — |
| Streaming | SDQ-2 A | scope boundary | n/a (no streaming by decision) | — |

No row is `needs-decision`.

### 3.2 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None — WF-1 internals only (its CON-1/CON-2 entry is AEA-40) | WF-1 | yes (DO-6 WF-1, emitters "responder, R-46 checks") | M-1, M-7, M-8, M-11, M-12, M-21, M-23…M-26 as the ticket lists |

### 3.3 Gates

None: no human, paid or live gate. Every test uses fakes or the scripted model; no `live` marker.

---

## 4. Shared code to use (copied from the current code on `19e046b`)

### 4.1 The four signatures to keep (`src/meridian/agent/nodes/reply.py`, AEA-21 stub on `main`)

```python
from langgraph.runtime import Runtime
from meridian.agent.context import GraphDeps
from meridian.domain.state import BriefUpdate, ChecksUpdate, ConversationState, FactsUpdate, ResponderUpdate
from meridian.domain.turn import TurnContext

def facts(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> FactsUpdate: ...
def responder(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ResponderUpdate: ...
def brief(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> BriefUpdate: ...
def checks(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ChecksUpdate: ...
```

`ctx = runtime.context` (a `TurnContext`: `.ids: TurnIds` (`thread_id`, `turn_id`, `request_id`, `run_tag`, `run_id`,
`agent_version`), `.budget: TurnBudget`, `.now`, `.demo_session`, `.span`, `.intake`). `build_graph`
(`agent/graph.py` line 198) binds `deps` with `functools.partial(fn, deps=deps)` and wraps each node in
`timed_node(name, fn, deps)` (one span per node; nodes never call the trace sink). `route_after_facts` (`agent/routers.py`)
sends a halted state to `compose`, a state with `handoff.created` to `["responder", "brief"]`, else to `["responder"]`.

### 4.2 `GraphDeps` (`agent/context.py`, field names and order exactly)

```python
@dataclass(frozen=True)
class GraphDeps:
    gateway: ModelGateway; retrieval: RetrievalIndex; uow: UnitOfWorkFactory
    identity: IdentityService; scheduling: SchedulingService; handoff: HandoffService
    brief: BriefAssembler; demo: DemoService; limits: Limits
    trace: TraceSink; specialists: SpecialistRunner; cases: CaseService; ledger: ModelsStatus
```
`BriefAssembler`, `CaseService` (and four others) are `TypeAlias = Any` until AEA-29 is on `main` (AEA-21 PD-7), so the
reply code calls them by their DO-4 names; mypy accepts any call. Use only these methods:

```python
deps.cases.open_case_for_thread(thread_id: ThreadId) -> CaseSummary | None      # DO-4 §13
deps.cases.attach_brief(case_ref: CaseRef, brief: Brief) -> None                  # upsert per case (cases.md §5);
                                                                                  # AEA-29 raises ValueError on case_ref mismatch
deps.brief.assemble(case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]) -> Brief   # DO-4 §7
deps.brief.attach_extraction(brief: Brief, extraction: BriefExtraction | None, check: CheckResult | None) -> Brief
deps.gateway.structured(role: StructuredRole, req: StructuredRequest[T], ctx: TurnContext) -> ModelOutcome[T]
deps.uow() -> AbstractContextManager[UnitOfWork]      # read-only by default (SQLite query_only); never write=True here
deps.limits.context.window_turns (10) · .window_line_chars (600) · .window_total_chars (8000)   # policy/limits.py ContextLimits
deps.limits.brakes.sonnet_calls                                                  # policy/limits.py Brakes
```

### 4.3 Storage reads through `tx.core` (AEA-10, `adapters/sqlite/repos_core.py`, `repos_core_aux.py`)

```python
tx.core.settled_for(thread_id: ThreadId, read_at: datetime) -> Settled          # the one Settled builder (graph-core §6)
tx.core.lookup_log.for_thread(thread_id: ThreadId) -> tuple[LookupRow, ...]      # ordered by id
tx.core.messages.recent(thread_id: ThreadId, turns: int) -> tuple[MessageRow, ...]
# MessageRow fields: id: int, thread_id, role: "customer" | "assistant" | "representative", text: str, at, turn_id,
#   kind, card_id, choice_option. Read them by attribute; do NOT import MessageRow (it lives in adapters/).
```

Writes used **only by the test fixtures** (§6): `tx.core.messages.append(thread_id, role, text, at, *, turn_id=...,
kind=...) -> int`, `tx.core.lookup_log.append(entry: LookupEntry) -> int`, `tx.core.actions.record(action:
CompletedAction) -> CompletedAction`, inside `store.uow(write=True)` with `tx.commit()`. `LookupEntry` / `LookupRow` live
in `meridian.domain.tools` (`tool`, `record_ids`, `passage_ids`, `result_seen`, `message_id`, `turn_id`; the row adds
`id`, `thread_id`).

### 4.4 Gateway (AEA-20, `agent/gateway.py`) and model ports (`ports/models.py`)

```python
from meridian.agent.gateway import ModelOutcome          # value: T | None; calls: tuple[CallRecord, ...];
                                                          # failure: ProviderFailure | None; halt: Halt | None
from meridian.ports.models import Role, StructuredRequest  # Role.RESPONDER, Role.BRIEF
class StructuredRequest[T: BaseModel](MeridianModel):
    system_prefix: str; system_dynamic: str; user: str; output_model: type[T]
    max_tokens: int; effort: Literal["low", "medium", "high"] | None
```
Gateway facts this plan relies on (read in the code): it never raises on a provider failure; it returns
`halt=Halt(reason=..., node=role.value, elapsed_ms=...)` for `PROVIDER_SPEND_CAP` (admission refused or cap failure),
`DEADLINE` (less than 1 s left: `TurnBudget.timeout_for` returns `None`) and `BRAKE_SONNET_CALLS` (the turn already made
`Limits.brakes.sonnet_calls` Anthropic calls); it SONNET-redacts the three text parts and **replaces `max_tokens` and
`effort` with the role's `RoleSpec`** (so the values the prompt module sets are placeholders); it retries a retryable
failure once.

### 4.5 Domain types (exact names; modules on `main`, unchanged since `96096be`)

- `meridian.domain.actions`: `ActionKind` (`BOOKED`, `MOVED`, `CANCELLED`, `CHANGE_REQUEST_SENT`, `CASE_OPENED`,
  `FOLLOWUP_SAVED`, `VERIFIED`), `CompletedAction` (`key: ActionKey` (`thread_id`, `turn_id`, `kind`, `record_id`),
  `kind`, `records`, `before`, `after`, `at`), `Settled` (`actions`, `open_case: OpenCase | None`, `read_at`; `.has()`,
  `.current_visit()`, `.only_turn()`).
- `meridian.domain.state`: `ConversationState` (fields used here: `thread_id`, `settled`, `identity` (`.status`),
  `open_tasks`, `shown_slots`, `counters`, `turn_input`, `chat_window: list[ChatLine]`, `gate`, `plan`, `identity_step`,
  `specialist_results`, `escalation`, `handoff`, `facts`, `draft`, `brief_extraction`, `checked`, `halt`, `check_events`),
  `ChatLine` (`speaker: Literal["customer", "assistant", "representative", "event"]`, `text`, `turn_id: TurnId | None`,
  `at`), `OpenTask` (`task_id`, `specialist`, `intent`, `opened_turn`, `details: TaskDetails`, `status: "open" |
  "waiting_identity" | "done"`; **no `missing`**), `TaskDetails` (`zip`, `city`, `service_type`, `wanted_text`,
  `appointment_id`, all optional), `FailureCounters` (re-export), `ShownSlot` (re-export), and the update types:

```python
class FactsUpdate(TypedDict, total=False):      # on main: NO last_lookups, NO pending_change (AEA-02 §8.2; R-2)
    facts: TurnFacts; settled: Settled; open_tasks: list[OpenTask]; shown_slots: list[ShownSlot]; counters: FailureCounters
class ResponderUpdate(TypedDict, total=False):
    draft: ResponderDraft | None; check_events: tuple[CheckEvent, ...]; halt: Halt
class BriefUpdate(TypedDict, total=False):
    brief_extraction: BriefExtraction | None; check_events: tuple[CheckEvent, ...]; halt: Halt
class ChecksUpdate(TypedDict, total=False):
    checked: CheckedReply
```
- `meridian.domain.turn`: `TurnContext`, `TurnIds`, `TurnBudget` (`started`, `deadline`; `.remaining()`,
  `.timeout_for()`), `SpanHandle`, `TurnInput` (`turn_id`, `message_id`, `kind`, `text_store`, `card_id`, `choice`,
  `card_number_seen`, `received_at`), `GateKind`, `GateDecision` (`kind`, `rules: RuleMatches`, …), `RuleMatches`
  (`safety`, `burning_unclear`, `danger_words`, `person`, `policy_trigger`, `rule_ids`, `correction`), `Plan` (`mode`,
  `tasks`, `handoff_request`, `topic`, `source`, `planner_failed`), `PlannedTask` (`order`, `specialist`, `intent`,
  `needs_identity`, `resumes_task_id`), `TaskIntent`, `EscalationDecision` (`outcome: "none" | "offer" | "escalate"`, …),
  `TurnFacts` (**on main:** `turn_id`, `gate_kind`, `plan_mode`, `points`, `passages`, `no_source_tasks`,
  `windows_shown`, `writes_this_turn`, `change_request`, `handoff`, `escalation`, `identity_step`, `quick_checks=()`;
  **no `account`, `missing`, `notices`** — R-2), `ResponderDraft(LLMFacing)` (`text: str`, 1…1200), `CheckedReply`
  (`text`, `removals`, `fallback_used`, `events`), `Removal`, `CheckResult`, `CheckEvent` with classmethods:

```python
CheckEvent.from_check(check: Literal["completion", "fact", "brief_fact", "brief_quote"], turn_id: TurnId,
                      removals: Sequence[Removal], *, fallback: bool = False) -> CheckEvent
    # fallback → "fallback"; no removals → "pass"; else "trimmed"; removed=len; claim_kinds=sorted distinct kinds
CheckEvent.from_halt(turn_id: TurnId, halt: Halt) -> CheckEvent
    # only BRAKE_* and RECURSION_LIMIT; ValueError for DEADLINE, SPEND_CAP, PROVIDER_SPEND_CAP; codes=(reason, node)
class SignalName(StrEnum): ... BRAKE_FIRED = "brake_fired"; RESPONDER_FALLBACK = "responder_fallback"; BRIEF_FAILED = "brief_failed"
class SignalRecord(MeridianModel):
    record: Literal["signal"] = "signal"; name: SignalName; turn_id: TurnId; thread_id: ThreadId; request_id: RequestId
    run_tag: RunTag; node: str; cause: str | None = None
    role: Literal["planner", "classifier", "specialist", "responder", "brief"] | None = None
    specialist: SpecialistKind | None = None; attempt: int | None = None; recovered: bool | None = None
```
- `meridian.domain.common`: `Halt` (`reason`, `node`, `elapsed_ms`), `HaltReason` (`DEADLINE`, `BRAKE_TASKS`,
  `BRAKE_TOOL_ROUNDS`, `BRAKE_SONNET_CALLS`, `BRAKE_IDENTICAL_CALL`, `RECURSION_LIMIT`, `SPEND_CAP`,
  `PROVIDER_SPEND_CAP`), `ProviderFailureKind` (incl. `INVALID_OUTPUT = "invalid_output"`, `OVERLOADED`), `PassageId`,
  `TurnId`, `ThreadId`, `RequestId`, `CaseRef`, `HandoffReason`, `Priority`, `Promise`, `FailureCounters`,
  `MeridianModel`.
- `meridian.domain.identity`: `NotVerified`, `CodeWrong` (both have `.kind`), `IdentityStep` (union; every member has
  `kind: Literal[...]`).
- `meridian.domain.specialists`: `KnowledgeResult` (`status: "answered" | "no_current_source" | "failed"`, `passages:
  tuple[Passage, ...]`, `points: tuple[KnowledgePoint, ...]`, `quick_checks: tuple[PassageId, ...] = ()` (**not** used
  here), `tools`, `calls`, …), `KnowledgePoint` (`text` ≤ 500, `passage_id`), `AccountResult` (`status: "read" |
  "not_verified" | "failed"`, `invoices: tuple[InvoiceView, ...]`, `membership: MembershipView | None`, `warranty:
  WarrantyView | None`, **`staff_notes`** (never to the responder), `tools`, `calls`), `SchedulingResult` (`status` one
  of `windows_shown`, `written`, `staff_change_request`, `slot_taken`, `out_of_area`, `no_fit`, `not_verified`,
  `booking_cap`, `failed`; `windows`, `write`, `change_request: ChangeRequestDraft | None`, `quick_checks: tuple[Passage,
  ...]`, `tools`, `calls`), `InvoiceView` (`invoice_id`, `lines: tuple[InvoiceLineView(description, amount_cents)]`,
  `total_cents`, `balance_cents`, `issued_on`, `due_on`, `paid`), `MembershipView` (`tier`, `renewal_date`),
  `WarrantyView` (`install_date`, `equipment_brand`, `sentence`), `ChangeRequestDraft` (`appointment_id`, `change`,
  `wanted_text`, …), `WriteResult`, `ConfirmationView`, `StaffNote`, `SpecialistResult` (discriminated on `kind`:
  `"knowledge" | "account" | "scheduling"`). `ToolCallRecord.error: ToolErrorCode | None` (`domain.common`).
- `meridian.domain.records`: `Passage` (`passage_id`, `file`, `section`, `version_label`, `version_date`, `text`,
  `score`), `ShownSlot` (`slot_id`, `date`, `window`, `technician`, `service_type`, `zone`, `member_reserved`,
  `shown_turn`), `FeeNote`.
- `meridian.domain.handoff`: `CaseSummary` (`case_ref`, `reason`, `priority`, `state`, `created_at`, `promise`,
  `followup`, `version`, `seed`, `due_at`), `HandoffResult` (`case`, `created`, `action`, `alert`), `Brief`
  (`case_ref`, `thread_id`, `assembled_at`, `status: "ready" | "being_written" | "failed"`, `headings` — exactly 8,
  numbered 1…8, titles `BRIEF_TITLES`), `BriefHeading`, `BriefItem`, `BRIEF_TITLES`, `BRIEF_KEYS`, `BRIEF_ORIGINS`,
  `Quote` (`message_id`, `text`), `BriefExtraction(LLMFacing)` (`needs: list[Quote]` 1…2, `claims: list[Quote]` ≤5,
  `open_decision: str` ≤200).

### 4.6 Checks (AEA-15, `src/meridian/checks.py`) — call, never edit

```python
from meridian.checks import build_evidence, check_completion, check_facts, check_quotes
check_completion(text: str, settled: Settled) -> CheckResult
check_facts(text: str, evidence: EvidenceSet) -> CheckResult
build_evidence(facts: TurnFacts, settled: Settled, lookups: Sequence[LookupRow],
               chat: Sequence[ChatLine] | None = None) -> EvidenceSet
check_quotes(extraction: BriefExtraction, shown: Mapping[int, str]) -> QuoteCheck   # needs, claims, removals, passed
```

### 4.7 Other helpers

```python
from meridian.agent.signals import emit_signal            # emit_signal(ids: TurnIds, record: SignalRecord) -> None
                                                           # logger "meridian.signal"; extra={"signal": dict};
                                                           # ValueError if record.turn_id/thread_id != ids'
from meridian.privacy.redact import RedactionProfile, redact   # redact(text, profile).text; idempotent
from meridian.policy.texts import format_usd               # format_usd(8900) == "$89"; format_usd(1250) == "$12.50"
# For the journey step and fixtures only:
from meridian.agent.graph import NodeFn, timed_node        # timed_node(name: str, fn: NodeFn, deps: GraphDeps) -> NodeFn
from meridian.agent.nodes.compose import ReplyComposer     # ReplyComposer().compose(state, ctx) -> ComposedReply (.blocks)
```

---

## 5. Steps (build order; each step ends with something checkable)

**Setup.** Work in the existing worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-38` on branch
`aea-38-graph-reply-node`; `export UV_LINK_MODE=hardlink`. Import check only (no baseline suite): `uv run python -c
"import meridian.agent.graph"`. If any name in §4 differs from the code, stop and report it; never adapt the plan silently.

**Which mode you are in (decide before Step 1):**
- **Re-dispatch on the existing build (the case at `2ec19ad`).** `git log --oneline main..HEAD` shows `ec94722` and
  `72b1152`. Do **not** rebuild, reset or rewrite them. Run the §7.3 gates G-1…G-8 on the branch as it stands and compare
  each §3 row (AC-1…AC-15, PA-1…PA-7) and each §7.1 test name with the code. Fix only what is red or missing, in a new
  commit on top (`fix(AEA-38): …`, explicit paths, the Co-Authored-By line); if nothing is red or missing, make no commit
  and report the gate results with counts. If `main` has moved and touches a §2.1 file or a §4 name, merge `main` into
  the branch (`git merge main`, never rebase, never force-push) and re-run G-1…G-8.
- **Fresh build (only if the branch has no AEA-38 commits).** Confirm `src/meridian/agent/nodes/reply.py` still holds the
  four AEA-21 stubs (if any body is filled and the branch has no AEA-38 commit, stop and report: another build exists),
  then follow Steps 1–10.

### Step 1 — the plan decisions this build follows (read, do not re-decide)

| ID | Decision | Why |
|---|---|---|
| PD-1 | `ResponderInput`, `SettledForModel`, `ResponderRules` and the small projections they need live in `agent/prompts/reply.py`, not `domain/` | AEA-02 §8.2 left them unbuilt and named this topic their owner; DO-4 §9 says the prompt module renders them; no other component reads their fields; this ticket may not edit `domain/*` |
| PD-2 | `ResponderInput.this_turn` is `FactsForModel` (a projection of `TurnFacts`), not `TurnFacts` | `TurnFacts.handoff` carries the case reference and the promise text; AC-8 requires the input to hold neither (R-26, R-46) |
| PD-3 | `ResponderInput` adds `account: AccountForModel | None` and `latest_message: str` | `TurnFacts.account` (DO-4 §8) is not on `main` (R-2); graph-core §7 sends the newest customer message separately. When the domain gains `TurnFacts.account`, a follow-up moves it |
| PD-4 | `facts` writes no `last_lookups` / `pending_change`; `TurnFacts` has no `account` / `missing` / `notices` | Not in `ConversationState` / `TurnFacts` on `main` (R-2) |
| PD-5 | Open-task and shown-slot rules of §5 step 3 (F-10, F-11) | No contract states them; DO-3 §5.3 makes `facts` their only writer |
| PD-6 | `checks` rebuilds the case, lookups, assembled brief and `shown` itself (same calls as `brief`) | `BriefUpdate` carries only `brief_extraction`, `check_events`, `halt`; the state may not gain keys |
| PD-7 | The brief prompt shows customer messages read from `tx.core.messages.recent(...)`, each SONNET-redacted and cut to `window_line_chars`; `shown` is that exact mapping | `Quote.message_id` needs message ids and `ChatLine` has none; redaction is idempotent, so `shown` equals what the model saw after the gateway's own redaction |
| PD-8 | Draft missing (failure or halt) → `completion` and `fact` events with result `fallback`, `removed=0`. Every sentence removed → the two events keep `trimmed`; `fallback_used=True`, `text=""` and a `responder_fallback` (`cause="all_removed"`) | One `completion` and one `fact` event per responder turn keeps M-21's denominator; "fallback" means "nothing was checked" |
| PD-9 | Brief halts: `BRAKE_SONNET_CALLS` → `halt` + `brake` event + `brake_fired` + `brief_failed`; `DEADLINE` / `PROVIDER_SPEND_CAP` → `brief_failed` (cause = reason) and **no** `halt` | graph-nodes §1 names the brief as a brake writer; the brief is off the critical path (DO-1 §8.2), so it never ends the turn for a timeout |
| PD-10 | Responder halts: always write `halt` and `draft=None`; `brake` event + `brake_fired` only for `BRAKE_SONNET_CALLS`; `responder_fallback` only for a provider failure (never for a halt) | `from_halt` raises for non-brakes; other halts are signalled outside the nodes (graph-nodes §4) |
| PD-11 | Points and passages whose file starts with `internal/` are never put in `FactsForModel` | DO-4 §7: staff-only text never in a `ResponderInput` (HP-3) |
| PD-12 | **(refreshed)** `tests/journeys/j2/test_aea_38.py` is created now: one runnable step at level `mock-tested` and two integrated steps declared with `needs=("session_service", "turn_service", "run_graph", "reply_composer")`, `operations=("startChatSession", "submitTurn")`, whose bodies are a `pytest.skip` naming AEA-51 (the harness reports them `blocked-on AEA-40, AEA-51` first). The record states level `mock-tested` | AEA-57's harness is on `main`; AEA-40 (CON-1/CON-2) and AEA-51 (`run_graph`, `reply_composer`, the scripted outputs of every other role) are not, so an integrated body cannot be written without inventing other roles' outputs. Same pattern as AEA-27 and AEA-34 |
| PD-13 | Chat-window line texts and the latest message are SONNET-redacted when copied into `ResponderInput` | Makes "holds no card-like number" true of the object itself; idempotent, so clean text is unchanged |
| PD-14 | `check_facts` runs on `check_completion`'s output text | Removals are counted once and the final text is consistent |
| PD-15 | **(new)** One responder rule implements WP-2's ruling "wp2 144": "When an invoice line and a document give different amounts for the same fee, give only the invoice amount and do not mention the document's amount." | `faq/customer_faq.md` (lines 6 and 17) says the after-hours fee is $149; WP-2 says explain fee types from the FAQ, so that passage can be in the evidence and `check_facts` would then accept "$149" (R-4). The rule is the only lever this ticket owns; a code guard would be a new check rule in AEA-15's file |

### Step 2 — create `src/meridian/agent/prompts/reply.py`

Module docstring, one paragraph: "Responder and brief wording, the model-facing input types, and the trimmed output
schemas (DO-3 §4.5, DO-4 §9; plan AEA-38 PD-1). Pure: no I/O, no clock, no model call." Imports allowed: standard
library, `pydantic`, `meridian.domain.*`, `meridian.ports.models` (`StructuredRequest`), `meridian.privacy.redact`,
`meridian.policy.texts` (`format_usd`). **Never import `meridian.adapters`, `meridian.services`, `meridian.agent.nodes`.**
`__all__` lists every public name below.

**2a. Constants (exact strings).**

```python
LABEL_THIS_TURN: Final = "WHAT HAPPENED THIS TURN"
LABEL_SETTLED: Final = "ALREADY DONE IN THIS CONVERSATION"
LABEL_ACCOUNT: Final = "ACCOUNT (the customer's own records, read this turn)"
LABEL_CHAT: Final = "RECENT CHAT"
LABEL_LATEST: Final = "LATEST CUSTOMER MESSAGE"
LABEL_MESSAGES: Final = "CUSTOMER MESSAGES"
STAFF_ONLY_PREFIX: Final = "internal/"
REQUEST_MAX_TOKENS: Final = 1024        # placeholder: the gateway replaces it with RoleSpec.max_tokens
RESPONDER_RULES: Final[tuple[str, ...]] = (
    "You are Meridian Home Comfort's automated assistant, not a person. Never say or suggest that you are a person.",
    "Write only the words of your reply. Cards, buttons, confirmations, the case reference and any promise about when "
    "a person will reply are added by the system after you. Never write them.",
    "Never write a case reference, a promise of when someone will reply, or a due time.",
    "Never say that the customer was charged, refunded or credited, or that money is owed to them.",
    "Never say that something is done, booked, moved, cancelled, sent, saved or verified unless it is listed under "
    "ALREADY DONE IN THIS CONVERSATION.",
    "Use only the numbers, prices, dates, times and IDs shown under WHAT HAPPENED THIS TURN, ALREADY DONE IN THIS "
    "CONVERSATION or ACCOUNT. Never add a price or fee that is not shown there.",
    "Explain amounts exactly as billed. Never say a bill is wrong.",
    "When an invoice line and a document give different amounts for the same fee, give only the invoice amount and do "
    "not mention the document's amount.",
    "If WHAT HAPPENED THIS TURN says no source answers part of the question, say you don't have that information. "
    "Do not guess.",
    "If a person was offered or will follow up, say so briefly, with no time and no reference.",
    "Write plain, short sentences. Write times in 12-hour form, such as 8:00 am. Stay under 1200 characters.",
)
BRIEF_RULES: Final[tuple[str, ...]] = (
    "You prepare notes for a Meridian Home Comfort staff member who will take over this conversation.",
    "needs: one or two quotes of what the customer is asking for. Copy each quote exactly, character for character, "
    "from one customer message, and give that message's id.",
    "claims: up to five quotes of things the customer says happened that nobody has checked. Copy each exactly and "
    "give its message id.",
    "open_decision: one sentence naming what the staff member must decide. Use no number, date, price or ID unless it "
    "appears in the customer messages.",
    "Never invent, shorten or reword a quote.",
)
```

**2b. Pure formatters (exact behaviour).**

- `trimmed_schema(model: type[BaseModel]) -> str`: `model.model_json_schema()`, remove every key named `"title"` at
  every depth (recursive over dicts and lists), then `json.dumps(..., sort_keys=True, separators=(",", ":"))`.
  Deterministic (AC-9 relies on it).
- `date_label(day: dt.date) -> str`: `f"{day:%A}, {day:%B} {day.day}"` → `"Monday, October 19"`.
- `today_label(now: dt.datetime) -> str`: `f"{now:%A}, {now:%B} {now.day}, {now.year}"` → `"Friday, October 16, 2026"`.
- `window_label(window: str) -> str | None`: `None` unless `re.fullmatch(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})", window)`;
  each end → 12-hour: hour 0 → `12:MM am`, 1–11 → `H:MM am`, 12 → `12:MM pm`, 13–23 → `(H-12):MM pm`; joined with
  `" to "` → `"08:00-12:00"` → `"8:00 am to 12:00 pm"`.
- `_iso_date_label(value: str | None) -> str | None`: `None` when `value` is `None` or `dt.date.fromisoformat` raises
  `ValueError`; else `date_label(...)`.

**2c. Model-facing types** (all `MeridianModel` from `meridian.domain.common`; frozen, `extra="forbid"`):

```python
class DoneItem(MeridianModel):            # one stored action, without ids, references, customer ids or fee lines
    kind: ActionKind
    when: Literal["this_turn", "earlier"]
    date_label: str | None = None
    window_label: str | None = None
    technician: str | None = None
    service_type: str | None = None
    change: str | None = None             # CHANGE_REQUEST_SENT only
    wanted_text: str | None = None        # CHANGE_REQUEST_SENT only

class PointForModel(MeridianModel):
    text: str
    source: str                           # f"{passage.file}, {passage.version_label}", or str(point.passage_id)

class WindowForModel(MeridianModel):
    date_label: str
    window_label: str
    technician: str

class FactsForModel(MeridianModel):       # ResponderInput.this_turn (PD-2)
    plan_mode: Literal["talk", "act"] | None
    points: tuple[PointForModel, ...]
    no_source: bool
    windows_shown: tuple[WindowForModel, ...]
    done_this_turn: tuple[DoneItem, ...]
    change_wanted: str | None
    handed_to_person: bool
    handoff_reason: str | None             # HandoffReason value only
    person_offered: bool
    identity_step: str | None              # IdentityStep.kind only
    quick_checks_offered: bool

class SettledForModel(MeridianModel):     # DO-4 §9 `settled`
    done: tuple[DoneItem, ...]
    case_open: bool                        # never the case reference, promise text or due time

class AccountForModel(MeridianModel):     # stands in for DO-4 §8 TurnFacts.account (PD-3); never staff_notes
    invoices: tuple[InvoiceView, ...]
    membership: MembershipView | None
    warranty: WarrantyView | None

class ResponderRules(MeridianModel):
    lines: tuple[str, ...]

class ResponderInput(MeridianModel):      # DO-4 §9 fields + account, latest_message (PD-3)
    chat_window: tuple[ChatLine, ...]
    latest_message: str
    this_turn: FactsForModel
    account: AccountForModel | None
    settled: SettledForModel
    identity_status: str
    today_label: str
    rules: ResponderRules
```

If `Plan.mode`'s type is not exactly `Literal["talk", "act"]` on `main`, type `plan_mode` as `Plan.mode`'s annotation
plus `| None` (read it from `domain/turn.py`); do not widen it to `str`.

**2d. Builders (pure; exact rules).**

1. `done_item(action: CompletedAction, turn_id: TurnId) -> DoneItem`: `when = "this_turn" if action.key.turn_id ==
   turn_id else "earlier"`; `src = (action.before or action.after) if action.kind is ActionKind.CANCELLED else
   action.after`; when `src` is `None` → only `kind` and `when`. Else `date_label = _iso_date_label(src.get("date"))`,
   `window_label = window_label(src["window"]) if "window" in src else None`, `technician = src.get("technician")`,
   `service_type = src.get("service_type")`; for `CHANGE_REQUEST_SENT` also `change = src.get("change")`, `wanted_text =
   src.get("wanted_text")`. **Never read `action.records`, `action.key.record_id` or `"fee_line"`.** (Invariant: no
   appointment id, case reference or customer id reaches the model.)
2. `settled_for_model(settled: Settled, turn_id: TurnId) -> SettledForModel`: `done = tuple(done_item(a, turn_id) for
   a in settled.actions)` (stored order); `case_open = settled.open_case is not None`.
3. `facts_for_model(facts: TurnFacts) -> FactsForModel`: `by_id = {p.passage_id: p for p in facts.passages}`;
   `points` = for each `pt in facts.points`: skip when `str(pt.passage_id).startswith(STAFF_ONLY_PREFIX)` or (passage
   found and `passage.file.startswith(STAFF_ONLY_PREFIX)`); `source = f"{p.file}, {p.version_label}"` when found else
   `str(pt.passage_id)`. `no_source = bool(facts.no_source_tasks)`. `windows_shown = tuple(WindowForModel(date_label=
   date_label(s.date), window_label=window_label(s.window) or s.window, technician=s.technician) for s in
   facts.windows_shown)`. `done_this_turn = tuple(done_item(a, facts.turn_id) for a in facts.writes_this_turn)`.
   `change_wanted = facts.change_request.wanted_text if facts.change_request else None`. `handed_to_person =
   facts.handoff is not None`; `handoff_reason = facts.handoff.case.reason.value if facts.handoff else None`.
   `person_offered = facts.escalation is not None and facts.escalation.outcome == "offer"`. `identity_step =
   facts.identity_step.kind if facts.identity_step is not None else None`. `quick_checks_offered =
   bool(facts.quick_checks)`.
4. `account_for_model(results: Sequence[SpecialistResult]) -> AccountForModel | None`: the first `AccountResult` with
   `status == "read"`; `None` if none. Copy `invoices`, `membership`, `warranty` only. **Never `staff_notes`, never
   `tools`.**
5. `responder_input(state: ConversationState, ctx: TurnContext) -> ResponderInput`: requires `state.facts` and
   `state.settled` (raise `RuntimeError("responder input needs facts and settled")` if either is `None`).
   `chat_window = tuple(line.model_copy(update={"text": redact(line.text, RedactionProfile.SONNET).text}) for line in
   state.chat_window)` (PD-13; **never read `messages`, never cut or drop lines** — AEA-34 applied the caps);
   `latest_message = redact(state.turn_input.text_store, RedactionProfile.SONNET).text`; `this_turn =
   facts_for_model(state.facts)`; `account = account_for_model(state.specialist_results)`; `settled =
   settled_for_model(state.settled, ctx.ids.turn_id)`; `identity_status = state.identity.status`; `today_label =
   today_label(ctx.now)`; `rules = ResponderRules(lines=RESPONDER_RULES)`.
6. `RESPONDER_SYSTEM_PREFIX: Final[str] = "\n".join(RESPONDER_RULES) + "\n\nOUTPUT: one JSON object matching this
   schema: " + trimmed_schema(ResponderDraft)` (built once at import; byte-identical every turn — AC-9).
7. `render_responder_dynamic(inp: ResponderInput) -> str`, lines joined with `"\n"`, exactly in this order:
   - `f"TODAY: {inp.today_label}"`, `f"IDENTITY: {inp.identity_status}"`, `""`
   - `f"{LABEL_SETTLED}:"`, then one `_done_line(item)` per `inp.settled.done`, or `"- nothing yet"`; then, when
     `inp.settled.case_open`, `"A person has this conversation's case: yes"`; then `""`
   - `f"{LABEL_THIS_TURN}:"`, `f"Mode: {inp.this_turn.plan_mode or 'none'}"`, then only the lines that apply:
     `"Answer points:"` + `f"- {p.text} [source: {p.source}]"` each; `"No source answers part of the question: yes"`;
     `"Windows shown:"` + `f"- {w.date_label}, {w.window_label}, with {w.technician}"` each; `"Done this turn:"` +
     `_done_line` each; `f"Change request for a person: {change_wanted}"`; `f"Handed to a person: yes (reason:
     {handoff_reason})"`; `"A person was offered: yes"`; `f"Identity step: {identity_step}"`; `"Quick checks offered:
     yes"`. If none of these optional lines applied: `"Nothing else happened this turn."`
   - when `inp.account` is not `None`: `""`, `f"{LABEL_ACCOUNT}:"`, then per invoice `f"- Invoice {inv.invoice_id}:
     issued {date_label(inv.issued_on)}, due {date_label(inv.due_on)}, total {format_usd(inv.total_cents)}, balance
     {format_usd(inv.balance_cents)}, {'paid' if inv.paid else 'unpaid'}"` and per line `f"  - {line.description}:
     {format_usd(line.amount_cents)}"`; membership `f"- Membership: {m.tier}, renews {date_label(m.renewal_date)}"`
     (or `f"- Membership: {m.tier}, renewal date not on record"` when `renewal_date` is `None`); warranty `f"-
     Warranty: installed {date_label(w.install_date)}" + (f", {w.equipment_brand}" if w.equipment_brand else "") +
     f": {w.sentence}"`.
   - `_done_line(item)`: parts = `[date_label, window_label, f"with {technician}", service_type, f"change: {change}",
     f"wanted: {wanted_text}"]` keeping only non-`None` sources; `f"- {item.kind.value}: {', '.join(parts)}"` (or
     `f"- {item.kind.value}"` when no parts) `+ (" (this turn)" if item.when == "this_turn" else " (earlier turn)")`.
8. `render_responder_user(inp: ResponderInput) -> str`: `f"{LABEL_CHAT}:"`, then `f"{line.speaker}: {line.text}"` per
   `inp.chat_window` (or `"(none)"`), `""`, `f"{LABEL_LATEST}:"`, `inp.latest_message`; joined with `"\n"`.
9. `responder_request(inp: ResponderInput) -> StructuredRequest[ResponderDraft]`: `StructuredRequest[ResponderDraft](
   system_prefix=RESPONDER_SYSTEM_PREFIX, system_dynamic=render_responder_dynamic(inp),
   user=render_responder_user(inp), output_model=ResponderDraft, max_tokens=REQUEST_MAX_TOKENS, effort=None)`.
10. `brief_shown(customer_lines: Sequence[tuple[int, str]], line_chars: int) -> dict[int, str]`: insertion-ordered;
    for each `(message_id, text)`: `t = redact(text, RedactionProfile.SONNET).text`; when `len(t) > line_chars`: `t =
    t[: line_chars - 1] + "…"`; `out[message_id] = t`. (Invariant: this mapping is exactly what the extraction model is
    shown, so `check_quotes` compares against the right text — PD-7.)
11. `BRIEF_SYSTEM_PREFIX: Final[str] = "\n".join(BRIEF_RULES) + "\n\nOUTPUT: one JSON object matching this schema: " +
    trimmed_schema(BriefExtraction)`.
12. `brief_request(case: CaseSummary, shown: Mapping[int, str]) -> StructuredRequest[BriefExtraction]`:
    `system_prefix=BRIEF_SYSTEM_PREFIX`, `system_dynamic = f"CASE REASON: {case.reason.value}\nPRIORITY:
    {case.priority.value}"` (never `case_ref`, never the promise); `user = f"{LABEL_MESSAGES}:\n" + "\n".join(f"[message
    {mid}] {text}" for mid, text in shown.items())`; `output_model=BriefExtraction`, `max_tokens=REQUEST_MAX_TOKENS`,
    `effort=None`.

**Check:** `uv run ruff check src/meridian/agent/prompts/reply.py && uv run mypy src/meridian/agent/prompts/reply.py`.
Keep the file under 400 lines (hard cap 600).

### Step 3 — `facts` (in `src/meridian/agent/nodes/reply.py`)

Replace the module docstring with: "The reply nodes (graph-nodes §9.6): facts, responder, brief, checks (AEA-38)."
Imports (module level): `langgraph.runtime.Runtime`; `meridian.agent.context.GraphDeps`; `meridian.agent.prompts.reply`
(`brief_request`, `brief_shown`, `responder_input`, `responder_request`); `meridian.agent.signals.emit_signal`;
`meridian.checks` (`build_evidence`, `check_completion`, `check_facts`, `check_quotes`); domain names of §4.5;
`meridian.ports.models.Role`. No import of `services`, `adapters` or other node modules.

`facts` steps (invariant per step):

- **F-1** `ctx = runtime.context`; `turn_id = ctx.ids.turn_id`; `thread_id = ctx.ids.thread_id`. **Do not return early
  on `state.halt`** (graph-core §5: facts runs on a halted state; the router then skips to compose).
- **F-2** `with deps.uow() as tx: settled = tx.core.settled_for(thread_id, ctx.now)` — read-only, no model or service
  call inside the block. *Invariant (AC-1): the DB is the authority; `state.settled` and `SchedulingResult.write` are
  never used to build `settled` or the writes.*
- **F-3** `writes = tuple(a for a in settled.actions if a.key.turn_id == turn_id)`.
- **F-4** Split `state.specialist_results` by `isinstance` into `knowledge: list[KnowledgeResult]`, `account:
  list[AccountResult]`, `scheduling: list[SchedulingResult]` (keep order).
- **F-5** `points = tuple(p for r in knowledge if r.status == "answered" for p in r.points)`.
- **F-6** `passages`: walk `[p for r in knowledge for p in r.passages] + [p for r in scheduling for p in
  r.quick_checks]`, keep the first of each `passage_id`, in order (graph-nodes §8).
- **F-7** `quick_checks = tuple(dict.fromkeys(p.passage_id for r in scheduling for p in r.quick_checks))` (order kept,
  duplicates dropped — AC-10). `KnowledgeResult.quick_checks` is **not** read (graph-nodes §8 names only the scheduling
  result).
- **F-8** `windows`: walk `w for r in scheduling for w in r.windows`, keep the first of each `slot_id`, in order.
  `change_request = next((r.change_request for r in scheduling if r.change_request is not None), None)`.
  `no_source_tasks = tuple(_knowledge_intent(state) for r in knowledge if r.status == "no_current_source")`, where
  `_knowledge_intent(state)` = the `intent` of the first `state.plan.tasks` item with `specialist == "knowledge"`, else
  `TaskIntent.ANSWER_QUESTION`.
- **F-9** Build `TurnFacts(turn_id=turn_id, gate_kind=state.gate.kind if state.gate is not None else GateKind.FREE_TEXT,
  plan_mode=state.plan.mode if state.plan is not None else None, points=points, passages=passages,
  no_source_tasks=no_source_tasks, windows_shown=windows, writes_this_turn=writes, change_request=change_request,
  handoff=state.handoff, escalation=state.escalation, identity_step=state.identity_step, quick_checks=quick_checks)`.
  `counters = _next_counters(state, knowledge, writes)` — start from `state.counters` and `model_copy(update=...)`:
  - `failed_answers` +1 if any `r.status in ("no_current_source", "failed")` in `knowledge`;
  - `tool_failures` +1 if any result in `state.specialist_results` has `status == "failed"` or any `t.error is not
    None` for `t in r.tools`;
  - `identity_failures` +1 if `isinstance(state.identity_step, NotVerified | CodeWrong)`;
  - `corrections` +1 if `state.gate is not None and state.gate.rules.correction`;
  - `bookings` += `sum(1 for a in writes if a.kind is ActionKind.BOOKED)`;
  - **`timeouts` is never in the update** (load_context owns it). Each of the first four rises at most 1 per turn.
- **F-10** `open_tasks = _next_open_tasks(state, turn_id)` (PD-5):
  1. `tasks = list(state.open_tasks)`; `touched: set[str] = set()`.
  2. If `state.plan is not None and state.plan.mode == "act"`, for each `planned` in `state.plan.tasks` (in order):
     a. `result` = the first item of `state.specialist_results` whose `kind == planned.specialist`, else `None`.
     b. `status` = `_task_status(planned, result, state.identity.status)`:
        `None` result → `"waiting_identity"` if `planned.needs_identity and identity_status != "verified"` else `"open"`;
        `KnowledgeResult` → `"done"`; `AccountResult` → `"waiting_identity"` if `status == "not_verified"` else
        `"done"`; `SchedulingResult` → `"open"` if `status in ("windows_shown", "slot_taken")`, `"waiting_identity"` if
        `status == "not_verified"`, else `"done"`.
     c. `details_update = {"appointment_id": cr.appointment_id, "wanted_text": cr.wanted_text}` when `result` is a
        `SchedulingResult` with `cr := result.change_request` not `None`, else `{}`.
     d. If `planned.resumes_task_id` names a task in `tasks`: replace it in place with
        `t.model_copy(update={"status": status, "details": t.details.model_copy(update=details_update)})`, and
        `task_id = t.task_id`.
     e. Else: `task_id = f"task-{str(turn_id)[:8]}-{planned.order}"` (matches gate.py's card pattern
        `[A-Za-z0-9._-]+`, no dot, no `burn-`/`code-`/`locate-` prefix); build `OpenTask(task_id=task_id,
        specialist=planned.specialist, intent=planned.intent, opened_turn=turn_id,
        details=TaskDetails(**details_update), status=status)`; replace an existing task with the same id (a repeated
        turn), else append.
     f. `touched.add(task_id)`.
  3. Return `[t for t in tasks if t.status != "done" or t.task_id in touched]` (a task closed in an earlier turn is
     dropped; one closed this turn stays for `run_graph`'s `closed_every_open_task`).
- **F-11** `shown_slots = _next_shown_slots(state, scheduling, windows)`: `list(windows)` if `windows`; else `[]` if any
  `r.status in ("written", "staff_change_request")` in `scheduling`; else `list(state.shown_slots)`.
- **F-12** `return {"facts": facts_obj, "settled": settled, "open_tasks": open_tasks, "shown_slots": shown_slots,
  "counters": counters}` annotated `-> FactsUpdate`. Nothing else.

### Step 4 — `responder`

- **R-1** `ctx = runtime.context`; `turn_id = ctx.ids.turn_id`; if `state.facts is None or state.settled is None`:
  `raise RuntimeError("responder ran before facts")` (unreachable by the graph shape; loud, never silent).
- **R-2** `req = responder_request(responder_input(state, ctx))`.
- **R-3** `outcome = deps.gateway.structured(Role.RESPONDER, req, ctx)`.
- **R-4** If `outcome.halt is not None`: `update: ResponderUpdate = {"draft": None, "halt": outcome.halt}`; if
  `outcome.halt.reason is HaltReason.BRAKE_SONNET_CALLS`: `update["check_events"] = (CheckEvent.from_halt(turn_id,
  outcome.halt),)` and `_signal(ctx, SignalName.BRAKE_FIRED, "responder", cause=outcome.halt.reason.value,
  role="responder")`. Return `update`. (PD-10; AC-11; PA-3.)
- **R-5** If `outcome.value is None`: `cause = outcome.failure.kind.value if outcome.failure is not None else
  ProviderFailureKind.INVALID_OUTPUT.value`; `_signal(ctx, SignalName.RESPONDER_FALLBACK, "responder", cause=cause,
  role="responder", attempt=len(outcome.calls) or None)`; return `{"draft": None}`.
- **R-6** Return `{"draft": outcome.value}`.

`_signal(ctx, name, node, *, cause=None, role=None, attempt=None) -> None` builds `SignalRecord(name=name,
turn_id=ctx.ids.turn_id, thread_id=ctx.ids.thread_id, request_id=ctx.ids.request_id, run_tag=ctx.ids.run_tag,
node=node, cause=cause, role=role, attempt=attempt)` and calls `emit_signal(ctx.ids, record)`. `role` is typed
`Literal["responder", "brief"] | None`. *Invariant: no text, draft or value ever goes into a signal; both ids come from
`ctx.ids`, so `emit_signal`'s mismatch check never fires.*

### Step 5 — `brief`

- **B-1** `ctx = runtime.context`; `thread_id = ctx.ids.thread_id`; `turn_id = ctx.ids.turn_id`; `case =
  deps.cases.open_case_for_thread(thread_id)`; if `None`: return `{"brief_extraction": None}` (no gateway call, no
  attach — AC-6).
- **B-2** `with deps.uow() as tx: lookups = tx.core.lookup_log.for_thread(thread_id); rows =
  tx.core.messages.recent(thread_id, turns=deps.limits.context.window_turns)` — read only; the service call of B-1
  happens **before** this block, never inside it (DO-3 §2.3 rule 1).
- **B-3** `draft_brief = deps.brief.assemble(case, state, lookups)` (status `being_written`).
- **B-4** `_store_brief(deps, ctx, case.case_ref, draft_brief, node="brief")`: `try: deps.cases.attach_brief(case_ref,
  brief)` `except Exception: _signal(ctx, SignalName.BRIEF_FAILED, node, cause="write_error", role="brief")`. Never
  re-raise (GRN-8: the brief is off the critical path). Catch `Exception`, not `BaseException`.
- **B-5** `shown = brief_shown([(r.id, r.text) for r in rows if r.role == "customer"],
  deps.limits.context.window_line_chars)`; if `shown` is empty, return `{"brief_extraction": None}` (unreachable on a
  graph turn: TurnService stores this turn's customer message first).
- **B-6** `outcome = deps.gateway.structured(Role.BRIEF, brief_request(case, shown), ctx)`.
- **B-7** If `outcome.halt is not None`: `_signal(ctx, BRIEF_FAILED, "brief", cause=outcome.halt.reason.value,
  role="brief")`; if the reason is `BRAKE_SONNET_CALLS`: also `_signal(ctx, BRAKE_FIRED, "brief",
  cause=outcome.halt.reason.value, role="brief")` and return `{"brief_extraction": None, "halt": outcome.halt,
  "check_events": (CheckEvent.from_halt(turn_id, outcome.halt),)}`; otherwise return `{"brief_extraction": None}`
  (PD-9).
- **B-8** If `outcome.value is None`: `_signal(ctx, BRIEF_FAILED, "brief", cause=<failure kind value, or
  "invalid_output">, role="brief", attempt=len(outcome.calls) or None)`; return `{"brief_extraction": None}`.
- **B-9** Return `{"brief_extraction": outcome.value}`.

### Step 6 — `checks`

- **C-1** `ctx`, `thread_id`, `turn_id` as above. `brief_turn = state.handoff is not None and state.handoff.created`;
  `case = deps.cases.open_case_for_thread(thread_id) if brief_turn else None` (before any unit of work). Then `with
  deps.uow() as tx: lookups = tx.core.lookup_log.for_thread(thread_id); rows = tx.core.messages.recent(thread_id,
  turns=deps.limits.context.window_turns) if case is not None else ()`. `events: list[CheckEvent] = []`.
- **C-2** Draft missing (`state.draft is None`): `text = ""`, `removals = ()`, `fallback = True`; `events +=
  [CheckEvent.from_check("completion", turn_id, (), fallback=True), CheckEvent.from_check("fact", turn_id, (),
  fallback=True)]`. No signal here (the responder already emitted its own, or a halt was signalled). (PD-8.)
- **C-3** Draft present: require `state.settled` and `state.facts` (else `RuntimeError("checks ran before facts")`).
  `c1 = check_completion(state.draft.text, state.settled)`; `c2 = check_facts(c1.text, build_evidence(state.facts,
  state.settled, lookups))` (PD-14); `removals = c1.removals + c2.removals`; `events += [from_check("completion",
  turn_id, c1.removals), from_check("fact", turn_id, c2.removals)]`; `fallback = not c2.text.strip()`; `text = "" if
  fallback else c2.text`; if `fallback`: `_signal(ctx, SignalName.RESPONDER_FALLBACK, "checks", cause="all_removed",
  role="responder")`.
- **C-4** If `case is not None` (brief turn): `draft_brief = deps.brief.assemble(case, state, lookups)`; `ext =
  state.brief_extraction`.
  - `ext is None` → `final = deps.brief.attach_extraction(draft_brief, None, None)`; no `brief_*` events (no extraction
    returned — graph-nodes §1).
  - else → `shown = brief_shown([(r.id, r.text) for r in rows if r.role == "customer"],
    deps.limits.context.window_line_chars)`; `q = check_quotes(ext, shown)`; `facts_ck = check_facts(ext.open_decision,
    build_evidence(state.facts, state.settled, lookups, state.chat_window))` (both must be non-`None`; same
    `RuntimeError`); `kept = ext.model_copy(update={"needs": list(q.needs), "claims": list(q.claims)})` (`model_copy`
    does not re-validate, so zero needs is allowed); `final = deps.brief.attach_extraction(draft_brief, kept,
    facts_ck)` (the DO-4 three-argument form; **do not pass AEA-29's optional `customer_messages`**, R-9); `events +=
    [from_check("brief_quote", turn_id, q.removals), from_check("brief_fact", turn_id, facts_ck.removals)]`.
  - `_store_brief(deps, ctx, case.case_ref, final, node="checks")` (second store; upsert).
- **C-5** Return `{"checked": CheckedReply(text=text, removals=tuple(removals), fallback_used=fallback,
  events=tuple(events))}`. Event order is always `completion`, `fact`, then `brief_quote`, `brief_fact`.

**Check after steps 3–6:** `uv run ruff check src/meridian/agent && uv run mypy`. `reply.py` under 500 lines (hard cap
600); if it would exceed 600, stop and report (do not create another source file).

### Step 7 — tests (§7.1) and the journey file (§7.2), written with the code; run them while iterating (§7.3 G-4).

### Step 8 — journey record (AC-14, PD-12)

Run G-6 and G-7 (§7.3), then create `docs/testing/journeys/<YYYY-MM-DD of the run>-AEA-38.md` by hand in the
`integrated-journeys.md` §4 table, titled `# Journey record — AEA-38 (agent/nodes/reply.py, agent/prompts/reply.py)`
(the AEA-27 record's shape; do **not** use `--journey-record`, which writes the harness-only template and would claim
the wrong level). Fields:
- `Claim` = "AEA-38 reply nodes (facts, responder, brief, checks) and `agent/prompts/reply.py` per AC-1…AC-13,
  PA-1…PA-7; J-2 WP-2 reply step at mock level (`tests/journeys/j2/test_aea_38.py`)".
- `Level` = "`mock-tested`. The J-2 step runs the real nodes through `timed_node`, the real `ModelGateway` over a
  scripted `FakeStructuredModel` and the real `ReplyComposer` on a `temp_sqlite()` copy; no server, no route".
- `Tested revision` = the feature commit SHA.
- `Environment` = worktree path, Python 3.12 via `uv`, temporary SQLite copy of the issued scheduling DB, fake models
  only, the harness's own loopback server for the two blocked steps, no paid call.
- `Command` = the G-4, G-6 and G-7 commands exactly as run.
- `Result` = pass counts; the J-2 file's `1 passed, 2 skipped` with the skip reason quoted (`blocked-on AEA-40, AEA-51:
  …`); the affected-journeys summary line.
- `Evidence location` = this file + GitLab issue #38 comment.
- `Remaining limitations` = "Real CaseService/BriefAssembler (AEA-29) are doubles; `TurnFacts.account`,
  `last_lookups`, `pending_change` wait on a domain follow-up (plan R-2); the WP-2 turn through CON-2 with stored
  `check_events` rows and the WP-1 current-document answer are not exercised; the FAQ's $149 passage is left out of the
  mock step's evidence on purpose (plan R-4)".
- `Blocked by` = "AEA-40 (`startChatSession`, `submitTurn`, `turn_service`), AEA-51 (`run_graph`, `reply_composer`;
  lands J-2)".
Then one paragraph under the table: the integrated J-2 steps to write once both land (copy §7.2's two blocked-step
descriptions).

### Step 9 — context rows (AC-15), in a second commit after the feature commit (it needs the feature SHA)

- `.claude/reference/area-map.md`, row `| 3 | **A7c Reply** | …`, *Status* cell only. Now: ``checks.py` actual
  (AEA-15, `57883e6`); `nodes/reply.py`, `prompts/reply.py` planned``. Becomes: ``checks.py` actual (AEA-15,
  `57883e6`); `nodes/reply.py`, `prompts/reply.py` actual (AEA-38, `<feature sha>`)``.
- `.claude/state/icm-progress.md`: append one row directly after the last "Routes verified against code and tests" row:
  ``| Routes verified against code and tests | provisional | <date>: area map A7c → `agent/nodes/reply.py`,
  `agent/prompts/reply.py` checked against `tests/unit/agent/nodes/test_reply_*.py`, `tests/unit/agent/prompts/`
  (AEA-38, `<feature sha>`; <N> pass); record docs/testing/journeys/<date>-AEA-38.md | Each slice adds its route;
  verified when every area-map row is actual |`` (≤ 400 characters; `<N>` = the G-4 pass count).
- `docs/design/code-design.md`:
  - §3 tree, the `nodes/reply.py` row: replace the trailing `stub AEA-21 6df4f4c` with `built AEA-38 <feature sha>`
    (keep the column spacing).
  - §3 tree, the `prompts/reply.py` row: append `   built AEA-38 <feature sha>` at the end of the line.
  - Append one line directly after the last `**Built:**` line (now line 192, AEA-28's): ``**Built:**
    `agent/nodes/reply.py` (four node bodies), `agent/prompts/reply.py` (AEA-38, `<feature sha>`).``
- Then run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in these three files only.

### Step 10 — final gates (§7.3 G-1…G-8), then commit

Two commits on the slice branch, each with explicit paths (`git add <path> ...`, **never `git add -A`**), a message body
naming the ACs, and **`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` as the last line**:
1. `feat(agent): reply node — facts, responder, brief, R-46 checks (AEA-38)`: the two source files, the test files of
   §2.1 and `tests/journeys/j2/test_aea_38.py`.
2. `docs(AEA-38): journey record and context rows for the reply node`: the journey record, area map, ICM progress,
   code design.

Do not merge, do not push, do not force-push. Merges follow the wave tree (Innocent, 2026-10-21): this branch is merged
with its wave siblings by the merge step, which also applies R-1's fix once. Do not edit the build ledger.

### What the implementer must NOT do

- Edit any file outside §2.1 — including `checks.py`, `compose.py`, `graph.py`, `routers.py`, `domain/*`,
  `services/*`, `repos_*.py`, `tests/graph/*` (even when `test_stubs_raise_loudly` turns red: R-1), `tests/fakes/*`,
  `tests/journeys/support/*`.
- Add a key to any `*Update` return beyond its `TypedDict`; add fields to `ConversationState` or `TurnFacts`.
- Build `settled` or the turn's writes from a `SchedulingResult`; read `messages` in the responder; cut or drop window
  lines (AEA-34's job).
- Put a promise text, case reference, due time, `records` value, fee line, staff note, `internal/` passage, tool output
  or code digits into anything the responder sees; put any text into a `CheckEvent` or `SignalRecord`.
- Write new check rules (AEA-15 owns them), stream (SDQ-2 A), or call a real provider (no `live` test).
- Invent the scripted outputs of other roles (planner, classifier, specialists) in the journey file; the integrated
  bodies stay a `pytest.skip` naming AEA-51 (PD-12).
- Put a real-looking secret, verification code, card-like number or full phone number as a literal in code or tests
  (build them from parts at run time, §6); bind ports 4019 or 5184; run pytest with more than `-n 2`; copy a venv;
  install `node_modules`.

---

## 6. Data and fixtures (synthetic only)

All values are fictional, from `docs/data/worked-pairs.md` (WP-2, WP-3, WP-4F, WP-7, WP-8), the AEA-15 tests
(`tests/unit/test_checks.py`, read only) and AEA-27's executor snapshot format (`agent/tools/account.py`
`_invoices_seen`). **`tests/unit/agent/nodes/reply_fixtures.py`** provides (names exact):

- **IDs:** `THREAD = ThreadId("3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10")`; `TURN_1 =
  TurnId("0b6d1f3a-5c2e-4a71-9d84-1e2f3a4b5c61")`, `TURN_2 = TurnId("1c7e2a4b-6d3f-4b82-8e95-2f3a4b5c6d72")`, `TURN_3 =
  TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")`, `TURN_4 = TurnId("a2b4c6d8-1e3f-4a5b-8c7d-9e0f1a2b3c4d")`, `TURN_5 =
  TurnId("2d8f3b5c-7e4a-4c93-9fa6-3a4b5c6d7e83")` (all UUID4-shaped); `NOW = WORKED_PAIRS_NOW` from `tests.fakes`
  (Friday 2026-10-16 10:00 America/Chicago); `CASE_REF = CaseRef("MHC-C-0042")`.
- `turn_ctx(*, thread=THREAD, turn=TURN_4, now=NOW, seconds_left=60.0) -> TurnContext`: `TurnIds(thread_id=thread,
  turn_id=turn, request_id=RequestId(str(uuid4())), run_tag="live", run_id=None, agent_version="test")`, `TurnBudget(
  started=time.monotonic(), deadline=time.monotonic() + seconds_left)`, `demo_session="demo-test"`,
  `span=SpanHandle(turn_id=turn, trace_id="0" * 32)` (the shape of `tests/unit/agent/_gateway_doubles.py::context`).
- `run(ctx) -> Runtime[TurnContext]`: `Runtime(context=ctx)` (verified on langgraph 1.2.16).
- `turn_input(*, turn=TURN_4, message_id=1, text="Yes, please.") -> TurnInput` (`kind="text"`, `received_at=NOW`).
- `rules(*, correction=False) -> RuleMatches` (all other fields falsy / `None` / `()`); `gate(kind=GateKind.FREE_TEXT,
  *, correction=False) -> GateDecision`.
- `action(kind, record_id, *, turn=TURN_3, records=None, before=None, after=None) -> CompletedAction` (`at=NOW`; built
  with `CompletedAction.model_validate({"key": {"thread_id": THREAD, "turn_id": turn, "kind": kind, "record_id":
  record_id}, ...})`, as `tests/unit/test_checks.py::_action` does).
- `MOVED_T3 = action(ActionKind.MOVED, "159", records={"appointment": "159", "slot": "56", "old_slot": "159"},
  before={"date": "2026-10-22", "window": "08:00-12:00"}, after={"date": "2026-10-19", "window": "08:00-12:00",
  "technician": "Marta Kowalski", "service_type": "hvac_repair"})` (WP-4F).
- `booked(turn) -> CompletedAction`: `action(ActionKind.BOOKED, "160", turn=turn, records={"appointment": "160"},
  after={"date": "2026-10-20", "window": "12:00-16:00", "technician": "Marta Kowalski", "service_type":
  "hvac_repair"})`.
- `write_result(action) -> WriteResult`: `WriteResult(action=action, confirmation=ConfirmationView(date=dt.date(2026, 10,
  20), window="12:00-16:00", technician="Marta Kowalski", fee_note=FeeNote(service_type="hvac_repair", tier="standard",
  fee_row=None, amount_cents=0, waived=True, line="Diagnostic fee waived (member)")))` (`ConfirmationView`,
  `WriteResult` from `meridian.domain.specialists`; `FeeNote` from `meridian.domain.records`). If a field name differs,
  read the model and build it with the real names; report the difference.
- `tool_record(*, error: ToolErrorCode | None = None) -> ToolCallRecord`: `ToolCallRecord(tool_call_id="call-1",
  name="kb_search", kind=ToolKind.KB_SEARCH, outcome="failed" if error else "ok", error=error, record_ids=(),
  passage_ids=(), lookup_id=None, elapsed_ms=5)`; the tool-failure case uses `error=ToolErrorCode.TOOL_FAILED`.
- `passage(file, n, text) -> Passage`: `Passage(passage_id=PassageId(f"{file}#{n}"), file=file, section="Test",
  version_label="2026", version_date=None, text=text, score=0.9)`; quick-check P1/P2 use
  `"troubleshooting/ac_not_cooling.md"` chunks 1 and 2.
- `settled(*actions, open_case=None) -> Settled` (`read_at=NOW`); `facts(**overrides) -> TurnFacts` (same base as
  `tests/unit/test_checks.py::_facts`, `turn_id=TURN_4`).
- `state(**overrides) -> ConversationState`: base `thread_id=THREAD`, `turn_input=turn_input()`, `gate=gate()`,
  `settled=settled()`; overrides by keyword (`ConversationState.model_validate({**base, **overrides})`).
- **WP-2:** `invoice_204411() -> InvoiceView` (`invoice_id="INV-204411"`, issued 2026-10-02, due 2026-11-01,
  `total_cents=47800`, `balance_cents=47800`, `paid=False`, lines `("Diagnostic visit", 8900)`, `("Contactor
  replacement", 24500)`, `("After-hours dispatch", 14400)`); `staff_note_149() -> StaffNote`
  (`kind="billed_differs_from_schedule"`, `record_id="INV-204411"`, `source_file="pricing/2026_fee_schedule.pdf"`,
  `text` built as `"Billed after-hours " + "$" + "144" + "; fee schedule says " + "$" + "1" + "49"`; if `StaffNote`'s
  fields differ, use the real ones and keep the text built from parts); `account_read() -> AccountResult(status="read",
  invoices=(invoice_204411(),), staff_notes=(staff_note_149(),), tools=(), calls=())`;
  **`WP2_LOOKUP_TEXT = "INV-204411 total $478.00 balance $478.00 lines $89.00 / $245.00 / $144.00"`** (exactly what
  AEA-27's `read_invoices` executor stores; scratch-checked on `19e046b`: with this row as evidence, `check_facts`
  removes "The after-hours fee is $149." and keeps "Your invoice shows a $89 diagnostic, $245 for the repair and a $144
  after-hours fee."); `WP2_QUESTION = "I got an invoice and I'm not sure what it's for."`; `WP2_KEPT = "Your invoice
  shows a $89 diagnostic, $245 for the repair and a $144 after-hours fee."`; `wp2_draft() -> str` returns `WP2_KEPT + "
  The after-hours fee is " + "$" + "1" + "49" + "."`; `FAQ_DIAG = passage("faq/customer_faq.md", 3, "The diagnostic fee
  is credited toward the repair if you approve the repair at the same visit.")` (a synthetic excerpt **without** the
  FAQ's $149 line, R-4) and `knowledge_answered() -> KnowledgeResult(status="answered", passages=(FAQ_DIAG,),
  points=(KnowledgePoint(text=FAQ_DIAG.text, passage_id=FAQ_DIAG.passage_id),), tools=(), calls=())`.
- **WP-7:** `WP7_MESSAGE = "I want a full refund on the repair. It didn't fix anything and I had to call another
  company."`; `case_summary(reason=HandoffReason.REFUND, priority=Priority.P3) -> CaseSummary` (`case_ref=CASE_REF`,
  `state="unassigned"`, `created_at=NOW`, `promise=Promise(policy_row="R26.refund", text="A representative will get
  to your refund request within 2 business days.", due_at=None, due_label=None)`, `followup=None`, `version=1`,
  `due_at=None`; use the real field names if any differ); `handoff_result(case) -> HandoffResult(case=case,
  created=True, action=action(CASE_OPENED, CASE_REF, turn=TURN_4, records={"case": CASE_REF}), alert=None)`.
- **Seeding the temp DB** — `seed(store, *, customer: Sequence[tuple[TurnId, str]] = (), lookups:
  Sequence[tuple[TurnId, int, str, tuple[str, ...]]] = (), actions: Sequence[CompletedAction] = ()) -> list[int]`:
  one `store.uow(write=True)` block: `tx.core.messages.append(THREAD, "customer", text, NOW, turn_id=turn,
  kind="text")` per customer line (collect the ids); `tx.core.lookup_log.append(LookupEntry(tool="account_read",
  record_ids=record_ids, passage_ids=(), result_seen=text, message_id=<the id at that index>, turn_id=turn))` per lookup
  (the int is the index into the collected message ids); `tx.core.actions.record(a)` per action; `tx.commit()`; return
  the message ids. Use `temp_sqlite()` from `tests.fixtures.sqlite` as a context manager in each test (never the issued
  DB); `store.uow` is the `UnitOfWorkFactory` to put in `GraphDeps`.
- **Doubles honouring DO-4 §7, §13 and cases.md §5:**
  - `FakeCaseService(case: CaseSummary | None, *, fail_attach: bool = False)`: `open_case_for_thread(thread_id)` returns
    `case` and appends `thread_id` to `self.opened`; `attach_brief(case_ref, brief)` raises `ValueError("brief belongs
    to another case")` when `brief.case_ref != case_ref` (as AEA-29 does), appends `(case_ref, brief)` to
    `self.attached`, then, if `fail_attach`, raises `RuntimeError("case store unavailable (test)")`.
  - `FakeBriefAssembler()`: `assemble(case, state, lookups) -> Brief` returns `make_brief(case.case_ref,
    status="being_written", not_generated=False)` and appends `len(lookups)` to `self.assembled`;
    `attach_extraction(brief, extraction, check) -> Brief` appends `(extraction, check)` to `self.extractions` and
    returns `make_brief(brief.case_ref, status="ready" if extraction is not None else "failed",
    not_generated=extraction is None)`.
  - `make_brief(case_ref, *, status, not_generated) -> Brief`: eight `BriefHeading`s, `number=i+1`,
    `key=BRIEF_KEYS[i]`, `title=BRIEF_TITLES[i]`, `origin=BRIEF_ORIGINS[i]`, `checked = i != 3`, `items=()`,
    `trimmed=False`, `trim_note=None`, `not_generated = not_generated and i in (1, 3, 6)`; `thread_id=THREAD`,
    `assembled_at=NOW` (read `BriefHeading`'s fields on `main` and set every required one).
- **Gateway:** `gateway(*, responder=None, brief=None, limits=None) -> tuple[ModelGateway, Doubles]`: `d =
  default_doubles(**{k: v for k, v in {"responder": responder, "brief": brief}.items() if v is not None})`; `return
  ModelGateway(**gateway_kwargs(d, limits)), d` (from `tests.unit.agent._gateway_doubles`, read only). Pass
  `tests.fakes.FakeStructuredModel([...])` as `responder` / `brief` to record requests (`.requests`). `ScriptedFailure`
  is `tests.fakes.models.ScriptedFailure(kind, http_status=None, retry_after_s=None, retryable=None)`. A
  `FakeStructuredModel` called past its script raises `ScriptExhaustedError` (a `BaseException`), which no node catches.
- `deps(*, uow, gw, cases=None, brief=None, limits=None) -> GraphDeps`: `GraphDeps(gateway=gw,
  retrieval=cast(Any, None), uow=uow, identity=None, scheduling=None, handoff=None, brief=brief or
  FakeBriefAssembler(), demo=None, limits=limits or Limits(), trace=RecordingSink(), specialists=None, cases=cases or
  FakeCaseService(None), ledger=RecordingLedger())` (`RecordingSink`, `RecordingLedger` from
  `tests.unit.agent._gateway_doubles`).
- `no_uow` — a callable that raises `AssertionError("this node must not open a unit of work")` when called (proves the
  responder never reads the DB).
- `signals(caplog) -> list[dict[str, Any]]`: `[r.__dict__["signal"] for r in caplog.records if r.name ==
  "meridian.signal"]`; each test sets `caplog.set_level(logging.INFO, logger="meridian.signal")`.
- Sensitive-looking seeds come from `tests.unit.agent._gateway_doubles`: `card_like()`, `six_digit_code()` (built at
  run time; never literals, never in test names).

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (all default-run, no paid call, no `live` marker)

**`tests/unit/agent/nodes/test_reply_facts.py`**
- `test_settled_reread_from_db` (AC-1): temp DB with `booked(TURN_4)` stored; state with a `SchedulingResult(
  status="written", write=write_result(booked(TURN_4)), tools=(), calls=())` and a **stale** `state.settled` holding
  `MOVED_T3` (not in the DB) → `update["settled"].actions` equals the stored row (compare `kind`, `key` and the instant
  of `at`; R-6 of AEA-34: stored datetimes come back UTC-aware), `facts.writes_this_turn` equal, `counters.bookings ==
  1`. Second case: same result, **no** row stored → `settled.actions == ()`, `writes_this_turn == ()`, `bookings == 0`.
- `test_failure_counters_rules` (AC-10): `state.counters = FailureCounters(timeouts=2)`; results
  `KnowledgeResult(status="no_current_source", passages=(), points=(), tools=(), calls=())`; `gate(correction=True)`;
  `identity_step=NotVerified()` (use its real required fields); one `BOOKED` row for `TURN_4` in the DB →
  `failed_answers == 1`, `corrections == 1`, `identity_failures == 1`, `bookings == 1`, `tool_failures == 0`, `timeouts
  == 2`. Second case: a `SchedulingResult(status="failed", tools=(), calls=())` plus a `KnowledgeResult` with a tool
  record whose `error` is set → `tool_failures == 1` (once).
- `test_quick_checks_into_turn_facts` (AC-10): `SchedulingResult(status="windows_shown", quick_checks=(P1, P2, P1),
  tools=(), calls=())` → `facts.quick_checks == (P1.passage_id, P2.passage_id)`; `facts.passages` contains P1 and P2 once
  each, in that order.
- `test_open_tasks_lifecycle` (PA-1): act plan with a scheduling task (`order=1`) and result `windows_shown` → one new
  task `task-a2b4c6d8-1`, status `open`; next turn (TURN_5) resumes it with result `written` → status `done`, kept this
  turn; a third turn with no plan → the `done` task is dropped; an account task with `needs_identity=True`, no result,
  identity `not_checked` → `waiting_identity`.
- `test_shown_slots_replaced_and_cleared` (PA-1): windows this turn replace `shown_slots`; a `written` result clears
  them; no scheduling result keeps them.
- `test_facts_runs_on_halted_state` (PA-2): `state.halt = Halt(reason=HaltReason.DEADLINE, node="run_specialist",
  elapsed_ms=60000)` → the update still has all five keys.

**`tests/unit/agent/nodes/test_reply_checks.py`** (checks node with `uow=store.uow` of a temp DB; responder via the
real gateway)
- `test_wp4f_turn4_claim_backed_by_settled` (AC-2): draft `ResponderDraft(text="Yes, it's moved: Monday, October 19,
  8:00 am to 12:00 pm with Marta.")`, `settled(MOVED_T3)`, `facts()` → `checked.removals == ()`, `text` equals the
  draft, `fallback_used is False`. Then `settled()` (empty) → exactly one removal, `reason == "no_completed_action"`.
- `test_wp8_generic_done_removed` (AC-3): draft `"Done, auto-renew is off. Done, your visit is booked."`,
  `settled(booked(TURN_4))` → text `"Done, your visit is booked."`; the `completion` event has `result="trimmed"`,
  `removed=1`, `claim_kinds=("completion",)`; `"auto-renew"` not in `event.model_dump_json()`.
- `test_unmatched_amount_removed` (AC-4): lookup row `WP2_LOOKUP_TEXT` seeded for the thread; draft `wp2_draft()` → one
  removal `not_in_evidence`; `checked.text == WP2_KEPT`.
- `test_responder_failure_and_empty_draft_fallback` (AC-5): responder fake `FakeStructuredModel([ScriptedFailure(
  ProviderFailureKind.OVERLOADED, retry_after_s=0.0), ScriptedFailure(ProviderFailureKind.OVERLOADED,
  retry_after_s=0.0)])` → responder returns `{"draft": None}`, two model requests (retry happened), one
  `responder_fallback` signal with `cause == "overloaded"`, `attempt == 2`; checks on that state → `fallback_used`,
  `text == ""`, both events `result == "fallback"`. Second case: draft `"Done!"` with empty `settled` → `fallback_used`,
  `text == ""`, signal `cause == "all_removed"`, `node == "checks"`. Neither raises.
- `test_sonnet_brake_on_responder` (AC-11): `gateway(responder=FakeStructuredModel([]), limits=Limits(
  brakes=Brakes(sonnet_calls=0)))` → `update["halt"].reason is HaltReason.BRAKE_SONNET_CALLS`, `.node ==
  "responder"`; `update["check_events"] == (one event with check="brake", result="fired",
  codes=("brake_sonnet_calls", "responder"))` (compare the fields `from_halt` sets; read `CheckEvent` for the exact
  field names); exactly one `brake_fired` signal; the fake was never called. (`Limits` and `Brakes` are frozen
  dataclasses in `policy/limits.py`; build them with keyword arguments.)
- `test_deadline_halt_on_responder_no_brake_event` (PA-3): `turn_ctx(seconds_left=0.5)` → halt `DEADLINE`, no
  `check_events` key, no signal.
- `test_check_events_and_signals_emitted` (AC-13): (a) passing draft → events `[("completion","pass"),
  ("fact","pass")]`; (b) brief turn (case present, extraction present) → four events in order completion, fact,
  brief_quote, brief_fact; (c) the AC-5 and AC-11 signals each have exactly the keys of `SignalRecord` with
  `turn_id`, `thread_id`, `request_id`, `run_tag`, `node` set, and no draft or message substring in
  `json.dumps(signals)`.

**`tests/unit/agent/nodes/test_reply_brief.py`** (temp DB seeded with `WP7_MESSAGE` for `TURN_4` and one lookup row;
`state(handoff=handoff_result(case_summary()))`)
- `test_brief_only_when_case_opened` (AC-6): `FakeCaseService(None)` → `{"brief_extraction": None}`, brief fake has
  no requests, `attached == []`; checks node on the same state attaches nothing.
- `test_brief_stored_twice` (AC-6): extraction returned → `attached[0][1].status == "being_written"`, after the checks
  node `attached[1][1].status == "ready"`, both with `CASE_REF`.
- `test_brief_failure_not_generated` (AC-6): brief fake returns `{"needs": [], "claims": [], "open_decision": "x"}`
  (fails validation → `invalid_output`; the fake marks invalid output `retryable=False`, so the gateway makes one
  attempt: script exactly one entry) → `brief_extraction is None`, one `brief_failed` signal `cause ==
  "invalid_output"`, `attempt == 1`; after checks the stored
  final brief has `not_generated` True on headings 2, 4, 7 only, status `failed`; `attach_extraction` got `(None,
  None)`.
- `test_attach_brief_failure_does_not_fail_turn` (AC-6): `FakeCaseService(case, fail_attach=True)` → brief and checks
  both return normally; two `brief_failed` signals with `cause == "write_error"` (nodes `brief`, `checks`); `checked`
  present.
- `test_brief_quote_and_fact_checks` (AC-7): extraction `needs=[Quote(message_id=<id>, text="I want a full refund on
  the repair")]`, `claims=[Quote(<id>, "It didn't fix anything"), Quote(<id>, "I had to call another company"),
  Quote(<id>, "The repair made it worse")]`, `open_decision="Decide on a refund, a warranty recall or neither. The
  repair cost $310."` → `attach_extraction` received `kept` with 1 need and the 2 exact claims, and a `CheckResult`
  with one `not_in_evidence` removal; events `brief_quote` (`trimmed`, `removed=1`, `claim_kinds=("quote",)`) and
  `brief_fact` (`trimmed`, `removed=1`, `claim_kinds=("amount",)`).
- `test_brief_sonnet_brake` (PA-4): `Limits(brakes=Brakes(sonnet_calls=0))` → halt `BRAKE_SONNET_CALLS` node `brief`,
  one `brake` event, signals `brief_failed` and `brake_fired`.

**`tests/unit/agent/nodes/test_reply_keys.py`**
- `test_reply_nodes_write_only_own_keys` (AC-12): run each node once (normal path, plus the halt path for responder
  and brief) and assert `set(update) <= <Update>.__optional_keys__` for `FactsUpdate`, `ResponderUpdate`,
  `BriefUpdate`, `ChecksUpdate` respectively; `checks` returns exactly `{"checked"}`.

**`tests/unit/agent/prompts/test_reply_prompts.py`**
- `test_responder_input_excludes_staff_tool_output_and_promise` (AC-8): WP-2 state: `account_read()` (with the $149
  staff note), a `KnowledgeResult` whose tool record `name` is a sentinel `"for_model:" + uuid4().hex[:8]`, an
  `internal/agent_discretion_notes.md` passage and point whose text is `"Waive the " + "$" + "49 late-cancellation fee
  once per customer per year"`, `handoff=handoff_result(case_summary())`, `settled` with the `CASE_OPENED` action and
  `open_case` carrying the promise, a chat line containing `card_like()`, the turn input text containing
  `six_digit_code()`. Assert none of: staff note text, discretion text, sentinel, promise text, `CASE_REF`,
  `card_like()`, `six_digit_code()` appears in `responder_input(...).model_dump_json()`, in the fake model's captured
  request (`system_prefix + system_dynamic + user`), in any `CheckEvent.model_dump_json()` of the following checks
  run, or in the `meridian.signal` caplog; and `set(ResponderDraft.model_fields) == {"text"}`.
- `test_internal_passages_never_rendered` (PA-5): a point from `internal/...` is absent from `facts_for_model(...)` and
  from the rendered dynamic text; a normal point is present with its `[source: file, version_label]`.
- `test_labels_and_schema_in_requests` (PA-6, PA-7): the dynamic text contains `"ALREADY DONE IN THIS CONVERSATION:"` and
  `"WHAT HAPPENED THIS TURN:"`; `RESPONDER_SYSTEM_PREFIX` contains `trimmed_schema(ResponderDraft)` and every
  `RESPONDER_RULES` line, including the PD-15 line; `json.loads(trimmed_schema(ResponderDraft))["properties"].keys() ==
  {"text"}`; `brief_request(...)` user lists `"[message <id>]"` for each shown id and its `system_dynamic` lacks
  `CASE_REF`.

**`tests/unit/agent/prompts/test_reply_prompt_turns.py`**
- `test_stable_prefix_turns_1_2_5` (AC-9): one `FakeStructuredModel` scripted with three `ResponderDraft`s through one
  real gateway; drive the `responder` node (with `uow=no_uow`) for three states: turn 1 (WP-3: "I need to schedule a
  service call. My AC isn't cooling.", window of 1 line, empty `settled`), turn 2 ("This Saturday if possible, 4 to 7,
  after work.", window of 3 lines), turn 5 (WP-4F "Yes, please.", window of 9 lines, `settled(MOVED_T3)`). Assert:
  three captured requests; `hashlib.sha256(system_prefix)` equal for all three and equal to
  `RESPONDER_SYSTEM_PREFIX`'s; the R-1 line and every rule line present; each `system_dynamic` has both labels and turn
  5 shows the `moved` line; each `user` contains exactly the lines of that state's `chat_window` in order and no line
  from another turn's window (a sentinel line seeded only in turn 2's window is absent from turn 5's request); every
  window ≤ 10 distinct turn ids, each line ≤ 600 chars, total ≤ 8,000.

### 7.2 The journey file (AC-14, PD-12): `tests/journeys/j2/test_aea_38.py`

Module docstring: "J-2 (slice plan §0a; WP-2, WP-1), extended by AEA-38. Level today: mock-tested (real facts,
responder and checks nodes through AEA-21's `timed_node`, the real `ModelGateway` over a scripted `FakeStructuredModel`,
the real `ReplyComposer`, on a temp SQLite copy of the issued DB; no server, no route). The integrated steps (CON-2 on
AEA-57's harness with the scripted model) are blocked by AEA-40 (`startChatSession`, `submitTurn`) and AEA-51
(`run_graph`, `reply_composer`; it lands J-2)." `pytestmark = pytest.mark.journey`. Imports: `functools`, `hashlib`,
`typing.cast`, `pytest`, `from meridian.agent.graph import NodeFn, timed_node`, `from meridian.agent.nodes import reply`,
`from meridian.agent.nodes.compose import ReplyComposer`, `from meridian.domain.blocks import TextBlock` (or `import
meridian.domain.blocks as b`, as `tests/graph/test_spine.py` does), `from tests.fixtures.sqlite import ISSUED_DB,
temp_sqlite`, `from tests.journeys.support.run import JourneyRun`, the §6 builders from
`tests.unit.agent.nodes.reply_fixtures`, `FakeStructuredModel` from `tests.fakes`.

1. `test_j2_wp2_reply_keeps_billed_amounts_mock() -> None` (no `journey` fixture; runs today):
   1. `before = hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest()`.
   2. `with temp_sqlite() as store:` `ids = seed(store, customer=[(TURN_4, WP2_QUESTION)], lookups=[(TURN_4, 0,
      WP2_LOOKUP_TEXT, ("INV-204411",))])`.
   3. `fake = FakeStructuredModel([ResponderDraft(text=wp2_draft())])`; `gw, _ = gateway(responder=fake)`; `d =
      deps(uow=store.uow, gw=gw)`; `ctx = turn_ctx()`; `rt = run(ctx)`.
   4. `st = state(turn_input=turn_input(message_id=ids[0], text=WP2_QUESTION), chat_window=[ChatLine(speaker="customer",
      text=WP2_QUESTION, turn_id=TURN_4, at=NOW)], specialist_results=[account_read(), knowledge_answered()])`.
   5. For `name, fn` in `(("facts", reply.facts), ("responder", reply.responder), ("checks", reply.checks))`: `node =
      timed_node(name, cast(NodeFn, functools.partial(fn, deps=d)), d)`; `st = st.model_copy(update=dict(node(st,
      rt)))`. (Invariant: the same binding `build_graph` uses.)
   6. `out = ReplyComposer().compose(st, ctx)`.
   7. Assert: `st.checked.text == WP2_KEPT`; `[(e.check, e.result) for e in st.checked.events] == [("completion",
      "pass"), ("fact", "trimmed")]`; `st.checked.removals[0].reason == "not_in_evidence"`; one `TextBlock` in
      `out.blocks` has `text == WP2_KEPT` and its `sources` hold one chip with `file == "faq/customer_faq.md"`; `"$" +
      "149"` is not in `out.model_dump_json()` and not in any event's `model_dump_json()` (never test the bare digits:
      random UUIDs can contain them); `len(fake.requests) == 1` and the staff-note text is not in that request's
      `system_dynamic + user`.
   8. After the `with` block: `hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest() == before`.
2. `test_j2_wp2_invoice_turn_through_con2(journey: JourneyRun) -> None`: `with journey.step("J-2", "reply 1 WP-2 invoice
   turn: billed $89 / $245 / $144 with a source chip, no $149, completion and fact check_events stored",
   needs=("session_service", "turn_service", "run_graph", "reply_composer"), operations=("startChatSession",
   "submitTurn")):` then `pytest.skip("J-2 WP-2 body is written when AEA-51 lands the scripted graph outputs (AEA-38 plan
   R-8)")`. Today the step itself skips first with `blocked-on AEA-40, AEA-51: …`.
3. `test_j2_wp1_cites_current_membership_document(journey: JourneyRun) -> None`: same `needs` / `operations`; step name
   `"reply 2 WP-1 answer cites membership/comfort_club_overview.md, never archive/comfort_club_overview.md"`; same
   `pytest.skip` body naming AEA-51.

Function names must not contain any number that looks like a secret; the strings above are fine.

### 7.3 Commands (cheapest first; stop at the first red)

Run from the worktree root with `export UV_LINK_MODE=hardlink`. Files `F` = `src/meridian/agent/nodes/reply.py
src/meridian/agent/prompts/reply.py tests/unit/agent/nodes tests/unit/agent/prompts tests/journeys/j2/test_aea_38.py`.

| # | Check | Command | Passing looks like |
|---|---|---|---|
| G-1 | Format | `uv run ruff format --check F` | "N files already formatted" (run without `--check` to fix) |
| G-2 | Lint | `uv run ruff check F` | "All checks passed!" |
| G-3 | Type check (the project's checker, mypy strict, per AEA-01) | `uv run mypy` | "Success: no issues found" |
| G-4 | This ticket's tests (while iterating) | `uv run pytest tests/unit/agent/nodes/test_reply_facts.py tests/unit/agent/nodes/test_reply_checks.py tests/unit/agent/nodes/test_reply_brief.py tests/unit/agent/nodes/test_reply_keys.py tests/unit/agent/prompts -q` | all pass |
| G-5 | Affected tests (once before the commit) | `grep -rlE "agent\.nodes(\.reply\| import .*reply)\|nodes import .*reply\|agent\.prompts\|meridian\.checks" tests eval` (on `19e046b` it lists `tests/graph/test_spine.py`, `tests/graph/_spine_doubles.py`, `tests/unit/test_skeleton.py`, `tests/unit/test_checks.py`, plus this ticket's files), then `uv run pytest tests/unit/agent tests/graph tests/unit/test_checks.py tests/unit/test_skeleton.py tests/unit/test_import_direction.py -q` (add `--with pytest-xdist` … `-n 2` only if slow; never more than 2) | all pass, **except** the four `reply` cases of `tests/graph/test_spine.py::test_stubs_raise_loudly` (R-1): if those four are the only failures, quote their ids in the report and carry on (the wave merge applies R-1's fix); any other red is yours to fix |
| G-6 | This ticket's journey file | `uv run pytest -m journey tests/journeys/j2/test_aea_38.py -q -rs` | `1 passed, 2 skipped`; both skip reasons start `blocked-on AEA-40, AEA-51` (owner order as the harness prints it) |
| G-7 | Affected journeys (AEA addition: before the final commit) | `uv run python -m tests.journeys.affected --base main -- -q -rs` | the selection includes `tests/journeys/j2/test_aea_38.py` plus any journey whose imports reach the changed modules; no failure; every skip is a `blocked-on` / `blocked:` reason. Quote the summary line in the record |
| G-8 | Context shape | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL |

The full suite is **not** run (no shared fixture, settings, dependency or cross-package seam changes; rule
`build-loop-test-scope`). Report G-1…G-8 results with counts in the final message and in the issue #38 comment.

---

## 8. Risks and requests

- **R-1 · Collision with AEA-21's `test_stubs_raise_loudly` (request to the wave-merge step; still open on
  `19e046b`).** `tests/graph/test_spine.py` lines 117–120 parametrize `(reply, "facts" | "responder" | "brief" |
  "checks", "reply.py")` and call `fn(None, None, deps=None)` expecting `NotImplementedError("… stub from AEA-21")`. Once
  this ticket fills them, those four cases fail (`AttributeError`). The collision map gives `tests/graph/*` no owner after
  AEA-21, so this ticket may not edit it. **Request (same as AEA-34/36/37 R-1):** merges follow the wave tree, so the
  wave merge that first includes a node ticket applies the fix once for all of them: add as the first line of the test
  body `if "stub from AEA-21" not in inspect.getsource(fn): pytest.skip("filled by its node ticket")` (`inspect` is
  already imported). G-5 tells the implementer to report these four and carry on.
- **R-2 · Domain types not yet built (request to the orchestrator: a small domain follow-up, owner AEA-02).** On `main`,
  `TurnFacts` has no `account` / `missing` / `notices`, and `ConversationState` / `FactsUpdate` have no `last_lookups` /
  `pending_change` (AEA-02 §8.2; AEA-02b built only `domain/views.py`; `agent/graph.py` already lists the two durable
  keys "once AEA-02b builds them"). This plan does not invent them: PD-3 carries the account view on
  `ResponderInput.account` (fields `invoices`, `membership`, `warranty`; never `staff_notes`) and PD-4 omits the rest.
  **Ask:** when the follow-up is cut, give `AccountFactsView` exactly `AccountForModel`'s three fields so a one-line
  change moves it into `TurnFacts.account`. Nothing in this ticket blocks on it.
- **R-3 · Compose treats every fallback as degraded (AEA-21 owner; unchanged on `main`).** `ReplyComposer._path`
  (`compose.py` line 634) returns `("degraded", "degraded_handoff", "model_error")` whenever `checked.fallback_used`, but
  graph-nodes §4 says `all_removed` has no outcome effect (only a responder failure is `model_error`). `CheckedReply` has
  no cause field, so this ticket cannot tell compose which one happened. Flag for the wave seam audit; no change here.
- **R-4 · The FAQ says "$149" (new; seam with AEA-33/35 retrieval and AEA-15 checks).** The old R-4 is closed: AEA-27's
  lookup snapshot holds the billed amounts only. But `faq/customer_faq.md` (issued, lines 6 and 17) says the after-hours
  dispatch fee is $149, and WP-2 says explain fee types from the FAQ. If retrieval puts that chunk in
  `TurnFacts.passages`, "$149" is in the evidence and `check_facts` keeps a "$149" sentence. This ticket adds the PD-15
  responder rule (the WP-2 ruling) and keeps the FAQ's $149 line out of the mock step's evidence, saying so in the
  record. **Request:** AEA-51's J-2 script and E-1's WP-2 must-not-say ("$149") must run with the real FAQ chunk in
  evidence; if a code guard is wanted ("an invoice amount beats a document amount for the same fee"), it is a new check
  rule in `checks.py`, a follow-up on AEA-15, which the orchestrator may cut. Not a blocker.
- **R-5 · Open-task rules decided here (PD-5).** Readers: `gates.flags_from_state` (status ≠ `done`), AEA-37's
  `_last_open_task`, AEA-21 compose's quick-check card id `f"{task.task_id}.1"`, and `run_graph`'s
  `closed_every_open_task`. The `task-<8 hex>-<order>` id fits gate.py's card regex. A sibling that assumes another id
  shape only reads ids, so nothing breaks.
- **R-6 · The brief reads `messages` (PD-7).** DO-3/graph-core forbid the **responder** from re-reading `messages`;
  the brief needs message ids for quotes, which `ChatLine` lacks. Not a contract change; noted for the reviewer.
- **R-7 · Placement of `ResponderInput` (PD-1).** If a domain follow-up later moves these types into `domain/`, it is a
  move-only change; AEA-60's rendered-prompt checks should import `responder_input` / `responder_request` from
  `meridian.agent.prompts.reply`.
- **R-8 · AC-14's integrated steps wait on AEA-40 and AEA-51 (PD-12).** The two blocked steps in
  `tests/journeys/j2/test_aea_38.py` get their bodies when AEA-51 lands the scripted outputs of every role: AEA-51
  writes them (it may edit this ticket's journey file only by reopening AEA-38, or it lands the same assertions in its
  own `j2/test_aea_51.py`); the orchestrator chooses. Assertions to carry: the WP-2 reply text holds "$89", "$245",
  "$144" with a `faq/…` or `pricing/…` source chip, no "$149"; the turn's stored `check_events` rows include `completion`
  and `fact`; WP-1's chip names `membership/comfort_club_overview.md`, never an `archive/` file.
- **R-9 · AEA-29's `attach_extraction` has an extra optional keyword (no change needed).** On branch
  `aea-29-aea-29-cases-handoff`, `BriefAssembler.attach_extraction(brief, extraction, check, *, customer_messages=None)`
  keeps every quote when `customer_messages` is `None`. This ticket already filters quotes with `check_quotes` and calls
  the DO-4 three-argument form, so the two agree. Noted for the AEA-29/38 seam at the wave merge.
- **R-10 · Shared context docs at the wave merge (expected, trivial).** `.claude/state/icm-progress.md` (appended row)
  and `docs/design/code-design.md` (appended `**Built:**` line) are append points every slice uses; keep every sibling's
  line. The A7c area-map cell and the two tree rows are this ticket's alone.
- **R-11 · Merge mode (for the orchestrator; observed on `main` at `2ec19ad`).** The plan assumes merges follow the wave
  tree (Innocent, 2026-10-21), and R-1's one-time fix depends on that. `main`'s history still shows ticket-by-ticket
  merges after that instruction: `13adc86 Merge AEA-27 identity: one-time code` and `19e046b Merge AEA-03b: history texts
  refuse values`, each followed by its own ledger commit. If AEA-38 is merged on its own instead of with its wave, the
  merge step must still apply R-1's `inspect.getsource` skip in the same merge, or the four `reply` cases of
  `test_stubs_raise_loudly` turn main red. This ticket's branch never merges itself.
- No shared primitive is requested; no signed contract changes; no `docs/plans/stage7-signoff.md` decision (D-4…D-15) is
  touched.

---

## 9. Readiness

**READY.** Every decision is made above (PD-1…PD-15); nothing needs Innocent. Nothing blocks: AEA-10, 11, 15, 20 and 21
are on `main`; AEA-29 (`BriefAssembler`, `CaseService`) is called only through `GraphDeps` and tested with doubles whose
signatures were re-checked against AEA-29's branch `b54fed9`; AEA-34 (`chat_window`) is read as given; AEA-40 and AEA-51
only gate the two integrated journey steps, which report `blocked-on` by design. The build already exists on
`aea-38-graph-reply-node` (`ec94722`, `72b1152`) and its record shows the gates passing except R-1's four expected cases;
a re-dispatched implementer verifies it (Setup, *re-dispatch*) rather than rebuilding. Collisions to manage at the merge:
R-1 (`tests/graph/test_spine.py`), R-10 (append-only context docs), R-11 (merge mode). Requests: R-1, R-2 (domain
follow-up), R-3 (compose), R-4 (FAQ $149 seam), R-8 (J-2 bodies), R-11.
