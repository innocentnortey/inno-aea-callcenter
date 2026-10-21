# Plan — [AEA-21] graph: spine, routers, context, compose

**Status:** planned — READY; **refreshed 2026-10-21 against `main` at `16ca639`** (first planned at `49e190b`).
AEA-01 (`07924f5`, code `893b825`: scaffold, `langgraph==1.2.16`, `policy/limits.py`, package markers, the
affected-journeys command) and AEA-03 (`60617f9`, `policy/texts.py`) are on `main`. **Build starts when AEA-02 is on
`main`** (every domain type and port; today its worktree holds only its frozen tests). Two single dependencies wait on
wave-1 siblings and are done **last** (§5 steps 14–15): the import `gates.gate.burning_card_id` (AEA-12) and the
method `CoreRepos.settled_for`, called through the injected `deps.uow` (AEA-10; needed only so mypy accepts that one
call). The specs (ticket, slice plan, DO-3, DO-4, stage7 addenda, sign-off) have not changed since `49e190b`; the
refresh re-checked every name below against AEA-02's refreshed plan and `main`'s code.
**What the refresh changed:** blockers (AEA-01 is merged); §4.1 re-export note and test-helper types; §4.10 the expired
code card's `hint` and the `fallback_used` degrade row (AC-12); §5 setup and step 18 (the ICM file now has two
"Routes verified" rows; DO-3 tree-row annotations); §6 required fields of `TurnFacts`/`OpenTask` in the doubles, and the
helper names AEA-37 reuses; §7.1 one more AC-12 case; §7.3 G-4 without `-p no:randomly`; §8.4; §9.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/21 · **Base revision:** `16ca639`
(re-base on the commit that merges AEA-02). **Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (refresh the
same day). **Slug / branch:** `graph-spine` → branch `aea-21-graph-spine`. **Implementer:** `fanout-implementer`
on Sonnet. **Lane:** `lane::build-loop`. **Risk:** none (no `risk::security`): no test-writer; the implementer writes
the named tests with the code (rule `build-loop-test-scope`). Reviewer note from the ticket: AC-7 guards that code digits
and form values never reach a checkpoint; if `code-review-agent` finds another path, the orchestrator adds the label.

Scratch prototypes the planner ran on langgraph 1.2.16 (AEA-01 worktree venv, `/tmp/aea21-scratch/`, not in the repo)
settled five facts this plan relies on; each is quoted where it is used: **(P1)** `invoke` returns a `dict`, not the
pydantic model; **(P2)** `Overwrite(v)` written to a reducer channel that has **no value yet** is stored as the raw
`Overwrite` object (a LangGraph bug in `BinaryOperatorAggregate.update`), so the first turn of a thread must send a plain
value; **(P3)** `runtime.context` is the very object passed as `context=`, and it never appears in any checkpoint blob or
metadata; **(P4)** two branch nodes that sleep 1 s each in one superstep finished in **1.005 s** when invoked from a
worker thread; **(P5)** a node returning `Command(goto=<itself>)` loops until `GraphRecursionError` at step 25, after
which `graph.get_state(config).values` (a `dict`) holds the last checkpoint. **Re-checked at the refresh**
(`/tmp/aea21-scratch2/p.py`, pydantic frozen state with a required field): `Overwrite([])` on the `operator.add` list
channel is safe on a fresh thread (a list channel starts with `[]`), while `Overwrite(None)` on the `first_halt`
channel of a fresh thread fails pydantic validation; on turn 2 both reset (P2 holds; §4.8 step 3 follows it).
Also: mypy strict rejects LangGraph's
`add_node`/`invoke` overloads for our union node type, so the builder is typed `Any` at exactly those two calls (§4.6).

---

## 1. Goal and sources

### 1.1 Goal (the issue's *What to build*, `docs/plans/tickets/AEA-21.md`)

> **US-17.** As a **homeowner** mid-booking, I need "what about Monday?" to apply to the visit we were just arranging, so
> that I don't start over every message. *(Acceptance: the follow-up resolves against the open task; a 20-turn chat keeps
> my verified identity and the open task; a safety phrase mid-chat still comes first.)*

This ticket draws the fixed shape of one customer turn (DO-3 §5.4 plus graph-core §5, §11), runs it (`run_graph`), and
builds what the customer sees at the end (`ReplyComposer`). The five node groups other tickets own exist here as stubs
with their final signatures that raise `NotImplementedError`, so AEA-34, 36, 37, 38, 39 fill them in parallel against a
compiled graph. `run_graph` hands `TurnService` (AEA-40) one `GraphOutcome`.

**Worked pair (WP-4F, turn 4: the SP-1 seam bug, DO-3 §1).** Input: turn 3 moved Linda Foster's (fictional,
`MHC-10001`) visit, appointment 159, to Monday 2026-10-19 08:00–12:00 with Marta Kowalski (an `actions` row of kind
`moved`); turn 4 is "Yes, please." State reaching `compose`: `settled` holding that `moved` action, this turn's facts
empty, checked text "Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta." Expected `ComposedReply`:
those words in a `TextBlock`; a `SettledView` whose `visit` (from `Settled.current_visit()`) shows 2026-10-19,
`08:00-12:00`, window label `8:00 am – 12:00 pm`, Marta Kowalski, status `moved`, built from the same `settled`;
`writes == ()`; `outcome="answered"`, `path="talk"`; `notice is None`. `turn_trace`: `gate_result="clear"`,
`outcome="answered"`, `degrade_reason=None`. Test: `tests/unit/agent/nodes/test_compose.py::test_wp4f_settled_view_matches_words`.

### 1.2 Context

Wave 1, blocked by AEA-02 (types) and AEA-03 (texts, merged). It is the hinge between the foundation and the wave-2
node tickets: AEA-34/36/37/38/39 replace this ticket's stubs, AEA-40 consumes `GraphOutcome` through an injected
`run_graph`, AEA-42 consumes `ReplyComposer.handoff_block`/`settled_view`, AEA-51 wires the real services. The 7b
specs left five routing conditions and the typing of not-yet-built services undecided; this plan decides them (§8.1).

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-21.md` (= issue #21) | AC-1…AC-16, owned files, halt table, WP-4F |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-21, §0a (journey map), §2, §3 collision map | Owned files; stubs then one owner each; `agent/nodes/*` row; journeys J-1…J-10 |
| Code design (DO-3) | `docs/design/code-design.md` §1 (WP-4F), §2.1, §2.2 [A], §2.3 rule 1, §4.5, §5.1–§5.4, §6 S-12, S-20, §10 C-5…C-7 | Static skeleton, writer table, parallel branches, recursion limit, no tx across a model call |
| Component contracts (DO-4) | `docs/design/contracts/internal-components.md` §1, §2, §3 (`gate_result`), §6, §7, §9 (`ComposedReply`, `CheckedReply`), §11 (halts, notices), §13, §14 | Shapes; DO-4 §16: addenda win |
| Addenda (win over DO-4) | `stage7/graph-core.md` §1–§6, §11, §13, §14, closing table (A-13, data 6); `stage7/graph-nodes.md` §1, §4, §8, §9; `stage7/graph-tools.md` §2, §5; `stage7/cases.md` §3.2, §3.4; `stage7/models.md` §4 | `GraphDeps`, `ModelsStatus`, `timed_node`, `NodeFn`, `halt_route`, `BRAKE_HALTS`, routers, `route_act_plan`, `run_graph`, `GraphOutcome`, `ReplyComposer`, `turn_trace`, `emit_signal`, node signatures, identity → CON-2 codes |
| Decision ledgers | `docs/plans/7b-decisions/graph-core.md` GRC-3, 6, 7, 10, 11, 15–21, 23, 24; `residuals-graph.md` R-G-12, R-G-13 | Already folded into the addenda |
| Decisions taken | `docs/plans/stage7-signoff.md` D-14 | GRC-3 stays on option A (safety before AI-paused) and CAS-16 on A: AC-11 as written |
| Signed wire contract (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` (CON-2 `submitTurn` examples), `UI_CONTRACTS.md` CON-2 | Block field values, labels, notice actions; nothing edited |
| Code on `main` (`16ca639`) | `pyproject.toml` (ruff `E,W,F,I,B,UP,S,RUF`, line 110, `UP040` ignored; mypy strict + pydantic plugin; pytest `--strict-markers --strict-config`; no `pytest-randomly`, no `pytest-xdist`), `src/meridian/policy/limits.py` (`Limits()` frozen, no arguments), `src/meridian/web/container.py` (`register_graph` stub is AEA-51's), `tests/conftest.py`, `tests/journeys/affected.py`, `tests/unit/test_import_direction.py`, `docs/testing/journeys/2026-10-21-AEA-01.md` | Gate commands; no container hunk; journey record shape |
| Sibling plans (read only) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` (refreshed against `16ca639`: §4.0 import order and re-exports, §4.3–§4.8, §4.10, §4.11, Appendix A block fields, §8.2 blocked types), `AEA-10.md` (`settled_for(self, thread_id: ThreadId, read_at: datetime) -> Settled`), `AEA-12.md` (`burning_card_id(turn_id: TurnId) -> str` = `f"burn-{turn_id}"`), `AEA-14.md` (rule ids `AI.halt`, `AI.models_disabled`, `AI.planner_failed`, `AI.specialist_failed`), `AEA-20.md` (its `CallLedger` precedent); consumers `AEA-34.md`, `AEA-36.md`, `AEA-37.md` (they import `GraphDeps`, `emit_signal`, `NodeFn`, `timed_node`, `build_graph`, `run_graph`, `ReplyComposer` and the `tests/graph/_spine_doubles.py` helpers by the names in this plan) | Exact import paths and names |
| Texts (on main) | `src/meridian/policy/texts.py` (`TextId`, `TEXTS`, `render`) | Every customer sentence compose uses |
| Requirements | PRD R-5, R-7, R-8, R-26, R-31, R-41, R-45; US-17 | Safety first; promise from policy; paused; brakes; typed state |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` *State seam*; E-1, E-5 | WP-4F (E-1) answerable once AEA-34/38 land; E-5 "safety first" held at compose (AC-11) |
| Observability (DO-6) | `docs/design/observability-contract.md` *Status values*, *Records* `turn`, `check_event`, rule 18 | `turn_trace` values; one node span per node; `RECURSION_LIMIT` brake event |
| Key metrics (DO-7) | M-3, M-14, M-16, M-18, M-22, M-24 | Computable from `turn_trace` and `closed_every_open_task`; no target here |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`; workspace `code-design-solid-modularity`, `context-management-multi-turn` rule 1, `async-safety` rule 1, `agent-architecture` rules 10–16 | Affected tests only; journey record at `mock-tested`; no growing message list; stubs raise |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files the implementer may create or edit)

| File | Create / modify | What |
|---|---|---|
| `src/meridian/agent/context.py` | create | `GraphDeps`, `ModelsStatus`, the service type aliases (§4.4) |
| `src/meridian/agent/signals.py` | create | `emit_signal` (§4.5) |
| `src/meridian/agent/routers.py` | create | `BRAKE_HALTS`, `halt_route`, `route_act_plan`, six routers (§4.7) |
| `src/meridian/agent/graph.py` | create | `NodeInput`, `NodeUpdate`, `NodeFn`, `CompiledGraph`, `RECURSION_LIMIT`, `NODE_NAMES`, `TURN_SCOPED_KEYS`, `DURABLE_KEYS`, `timed_node`, `build_graph`, `run_graph`, `bind_run_graph` (§4.6, §4.8) |
| `src/meridian/agent/nodes/compose.py` | create | `compose` node, `turn_trace`, `ReplyComposer` (§4.9–§4.11) |
| `src/meridian/agent/nodes/load_context.py` | create (stub) | `load_context` (AEA-34 replaces) |
| `src/meridian/agent/nodes/front.py` | create (stub) | `gates`, `safety`, `identity` (AEA-36 replaces) |
| `src/meridian/agent/nodes/plan.py` | create (stub) | `planner`, `danger_classifier`, `plan_join` (AEA-37 replaces) |
| `src/meridian/agent/nodes/act.py` | create (stub) | `run_specialist`, `escalation`, `handoff` (AEA-39 replaces) |
| `src/meridian/agent/nodes/reply.py` | create (stub) | `facts`, `responder`, `brief`, `checks` (AEA-38 replaces) |
| `tests/unit/agent/test_context.py` | create | §7.1 |
| `tests/unit/agent/test_signals.py` | create | §7.1 |
| `tests/unit/agent/test_routers.py` | create | §7.1 |
| `tests/unit/agent/nodes/__init__.py` | create **only if absent**, 0 bytes (`touch`) | package marker (AEA-01 has no marker for this folder; wave-2 node tickets may add the same empty file, which merges cleanly) |
| `tests/unit/agent/nodes/compose_fixtures.py` | create | builders shared by the two compose test files (§6) |
| `tests/unit/agent/nodes/test_compose.py` | create | §7.1 |
| `tests/unit/agent/nodes/test_compose_blocks.py` | create | §7.1 (plan-added) |
| `tests/graph/_spine_doubles.py` | create | node doubles, deps doubles, context builder (§6) |
| `tests/graph/test_spine.py` | create | §7.1 |
| `tests/graph/test_run_graph.py` | create | §7.1 |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-21.md` | create | AC-15 journey record (§7.4) |
| `.claude/reference/area-map.md` | edit the **A7a row** only | AC-16 |
| `.claude/state/icm-progress.md` | edit **one** "Routes verified against code and tests" row (the one whose evidence starts "2026-10-21: area map A0 → `policy/texts.py`") and the `Last reconciled:` line only | AC-16 |
| `docs/design/code-design.md` | edit the status sentence on line 7 (`**Built so far …**`), §2.2 paragraph, the `**Built:**` line under `## 3`, the §3 tree rows for `agent/{graph,routers,context,signals}.py` and `agent/nodes/{load_context,compose,front,plan,act,reply}.py`, the §5.4 closing paragraph, and the §10 row C-5 only | AC-16 |
| `../Gauntlet AI/devlogs/aea-callcenter/2026-10-21-aea-21-graph-spine-claude-01.md` | create (outside this repo; **not committed** by the implementer; report its path) | AC-16 dev-log entry |

### 2.2 Shared surfaces read, never edited

`pyproject.toml`, `uv.lock`, every `__init__.py` AEA-01 creates, `tests/conftest.py`, `src/meridian/domain/*`,
`src/meridian/ports/*`, `src/meridian/policy/*` (incl. `texts.py`, `limits.py`), `src/meridian/gates/*`,
`src/meridian/adapters/**` (incl. `checkpointer.py`), `src/meridian/web/**` (incl. `container.py`: **this ticket has no
`register_<x>()` hunk**; AEA-51 completes `register_graph`), `tests/journeys/**`, `tests/fakes/**`, the OpenAPI file,
`UI_CONTRACTS.md`, `docs/ux/**`, `apps/web/**`, `docs/design/contracts/**`, the issued data, `docs/archive/**`,
`docs/parked/**`.

### 2.3 Owned by other tickets — do not create

`build_specialist_task`, `scope_for` (AEA-39 / AEA-35), `SpecialistRunner` (AEA-35), `ModelGateway`, `ModelOutcome`
(AEA-20), `LedgerService` (AEA-26), every `services/*` class, `join_plan` (AEA-37), `decide_escalation` (AEA-14),
`check_*` (AEA-15), `register_graph` body (AEA-51), `tests/fakes/*` (AEA-11: do **not** import them; this ticket has
its own doubles in its own test folders). After this ticket merges, the five stub files belong to their owners
(collision map); this ticket never edits them again.

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's) → implementation → verification

| AC | Requirement (full text in the issue) | Implemented by (step) | Verified by |
|---|---|---|---|
| AC-1 [invariant] | Routers follow DO-3 §5.4 + graph-core §11 exactly; `plan_join` `planner_failed` & no tasks → escalation; gates `BURNING_ANSWER`/`no` → `route_act_plan` (identity when needed and missing, else one `Send` per task carrying `SpecialistSend(planned=t, state=state)`, no `SpecialistTask`); `yes`/`unsure` → safety; `routers.py` imports nothing from `nodes/act.py` | `routers.py` (§4.7, step 5); path maps in `graph.py` (§4.8, step 7) | `tests/unit/agent/test_routers.py` (`::test_gates_edges`, `::test_plan_join_edges`, `::test_identity_edges`, `::test_specialists_edges`, `::test_escalation_edges`, `::test_facts_edges`, `::test_card_choice_resumes_open_task`, `::test_planner_failed_goes_to_escalation`, `::test_burning_no_routes_act_plan`, `::test_route_act_plan_sends_planned_tasks`, `::test_routers_never_import_act`); `tests/graph/test_spine.py::test_compiled_edges_match_table` |
| AC-2 [failure/refusal] | Every router calls `halt_route` first; brake + no escalation → escalation; brake after escalation → compose; deadline/spend → compose; after `facts`, a halted state skips responder, brief, checks | `halt_route` + every router (§4.7) | `test_routers.py::test_halt_route_from_every_router`; `test_spine.py::test_brake_runs_escalation_once` |
| AC-3 [invariant] | Skeleton compiles and runs with node doubles and the in-memory saver; five stub modules have graph-nodes §9 signatures (mypy) and raise naming their path | `graph.py`, stubs (steps 3, 7) | `test_spine.py::test_skeleton_compiles_and_runs`, `::test_stubs_raise_loudly`; `uv run mypy src/meridian/agent` |
| AC-4 [invariant] | Turn-scoped keys (incl. `specialist_results`, `check_events`) do not survive into the next invocation; durable keys persist; no growing message list | `run_graph` turn update (§4.8 algorithm step 3) | `test_spine.py::test_turn_scoped_keys_reset_and_durable_keys_persist` |
| AC-5 [failure/refusal] | `recursion_limit` 25 explicit; 3-task turn under it; a looping node double → `GraphRecursionError` caught → `GraphOutcome` with `RECURSION_LIMIT` halt, `halt_reply` from `settled_for`, last checkpoint's events + one `brake` event, one `brake_fired` signal, no exception | `build_graph`, `run_graph` recursion branch (§4.8 step 7) | `test_spine.py::test_three_task_turn_under_limit`, `::test_recursion_limit_returns_graph_outcome` |
| AC-6 [invariant] | Parallel branches run in parallel on langgraph 1.2.16 sync runner from a worker thread (≈1 s, not 2 s); result written into DO-3 §2.2 | real `build_graph` + sleeping doubles | `test_spine.py::test_two_node_parallel_timing` (prints the elapsed time); DO-3 §2.2 edit (step 18) |
| AC-7 [negative] | `TurnContext` reaches every node as `runtime.context`; `intake` (sentinels `"914276"`, `"512-555-0199"`) never in a checkpoint blob/metadata, the outcome, or logs | `run_graph` passes `context=ctx` and a config with `thread_id` only (§4.8) | `test_spine.py::test_turn_context_reaches_nodes`, `::test_intake_never_checkpointed` |
| AC-8 [capture] | Every node runs inside `timed_node`: one `trace.node(ctx.span, name, elapsed_ms, status)` per run, `ok`/`halted`/`error` (exception propagates), no text or values | `timed_node` (§4.6) | `test_spine.py::test_every_node_emits_one_span` |
| AC-9 [invariant] | `GraphOutcome(reply, turn_trace, check_events, halt)`: events filtered to this turn + `checked.events`; `turn_trace` per DO-6; `gate_result` from classifier label when raised else `gate.gate_result()`; `specialists_run` in order | `run_graph`, `turn_trace` (§4.8, §4.11) | `test_spine.py::test_graph_outcome_fields`; `test_compose.py::test_turn_trace_values_match_do6` |
| AC-10 [invariant] | Compose: WP-4F words + `SettledView` from the same `settled`; `writes` this turn only; handoff card only from `HandoffResult`; `LiveQueuedBlock` for `live_queued`; R-7 card id = `burning_card_id(turn_id)`; one `QuickChecksBlock` with `checks` inline; P1 unstaffed `separate_line`, no second promise | `ReplyComposer` (§4.9–§4.10) | `test_compose.py::test_wp4f_settled_view_matches_words`, `::test_handoff_card_only_from_handoff_result`, `::test_card_ids_use_prefixes`, `::test_quick_checks_inline`, `::test_p1_unstaffed_separate_line` |
| AC-11 [invariant] | `SAFETY` gate → first block is the fixed safety instruction, also with `controller = human` (GRC-3 A) | compose step A (§4.10) | `test_compose.py::test_safety_instruction_first[ai]`, `[human]` |
| AC-12 [failure/refusal] | Halt and fallback replies per the halt table; `fallback_used` → fixed fields + person offer, `model_error`; `planner_failed` → handoff reply, `model_error`; `halt_reply` works with no graph state | compose steps C, F (§4.10) | `test_compose.py::test_halt_and_fallback_replies` (one case per row) |
| AC-13 [negative] | No staff note or code in any block, `SettledView`, `TurnTrace`, span or signal | compose reads no `staff_notes`; spans/signals carry codes | `test_compose.py::test_no_staff_note_or_code_in_reply`; `test_spine.py::test_signal_and_span_carry_codes_only` |
| AC-14 [invariant] | `closed_every_open_task` per graph-core §2 (five cases) | `run_graph` (§4.8 step 6) | `tests/graph/test_run_graph.py::test_closed_every_open_task` |
| AC-15 [journey] | Runs no journey yet; record at `mock-tested`, *Blocked by* AEA-57 (and AEA-51), journeys J-1…J-5 and J-9 named; affected command prints "0 journeys affected" | journey record (step 17) | the record file; `uv run python -m tests.journeys.affected --base main` |
| AC-16 [regression/context] | Area map A7a row, ICM row, DO-3 §2.2/§5.4 [A]s replaced by measurements, §5.4 links graph-core §5/§11, DO-3 status, dev-log entry | context commit (step 18) | `git diff --name-only main...HEAD` lists the three context files; dev-log path reported |

### 3.2 Plan-added criteria (the reconciliation found them; the issue gets a comment proposing them)

| ID | Obligation | Source | Verified by |
|---|---|---|---|
| PA-1 | Identity results reach the customer as exactly the CON-2 code graph-tools §5 lists (`NotVerified`→`NOT_VERIFIED`+handoff, `CodeWrong`→`CODE_WRONG`+code prompt `wrong`, `CodeExpired`→`CODE_EXPIRED`+code prompt `expired`, `CodeLocked`/`CodeCapReached`→error+handoff) | graph-tools §5 table; AEA-36 ("compose maps each to its CON-2 code") | `test_compose_blocks.py::test_identity_steps_map_to_con2_codes` |
| PA-2 | `SettledView` mapping: identity `located` shown as `not_checked`; hint only for `code_sent`/`verified`; `request` from the open case's promise; `actions[]` = every action with a fixed summary; `replying` from the controller | graph-core §13; OpenAPI `Settled` | `test_compose_blocks.py::test_settled_view_identity_and_request`, `::test_write_cards_and_summaries` |
| PA-3 | This turn's `BOOKED`/`MOVED` writes → `ConfirmationBlock`; `CANCELLED` → `CancelledBlock`; a fee-bearing change → `ChangeRequestBlock` (no second handoff card) | OpenAPI BOOKED, CANCELLED, CHANGE_REQUEST examples; R-20, R-21 | `test_compose_blocks.py::test_write_cards_and_summaries`, `::test_change_request_block` |
| PA-4 | Scheduling result `out_of_area` → `ErrorBlock OUT_OF_AREA`; `booking_cap` → `BOOKING_CAP` notice; escalation `offer` → `FailureOfferBlock` | DO-4 §11; OpenAPI OUT_OF_AREA, BOOKING_CAP, FAILURE_OFFER | `test_compose_blocks.py::test_scheduling_result_errors_and_booking_cap`, `::test_failure_offer_on_escalation_offer` |
| PA-5 | `GraphDeps` field names and order exactly graph-core §4; a structural double satisfies `ModelsStatus` | graph-core §4, R-G-13 | `test_context.py::test_graph_deps_fields`, `::test_models_status_is_structural` |
| PA-6 | `emit_signal` logs exactly one `meridian.signal` record whose `signal` extra is the record's JSON dump; refuses a record for another turn | graph-nodes §4 | `test_signals.py::test_emit_signal_logs_one_record_codes_only`, `::test_emit_signal_rejects_other_turn` |
| PA-7 | Every key of `ConversationState` is classified turn-scoped, durable or identity; every turn-scoped key exists | DO-3 §5.1–§5.3 | `test_spine.py::test_turn_scoped_keys_reset_and_durable_keys_persist` (first asserts) |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| Static skeleton, routers pure over typed fields | DO-3 §5.4; agent-architecture 11–13 | AC-1 | in-ticket | steps 5, 7 |
| A tasks-less plan carrying `handoff_request` (WP-7 refund) must reach escalation; DO-3 §5.4 sends `talk` to `facts` and an empty fan-out ends the graph | DO-4 §6 rules 2, 4; AEA-39 AC-4; AEA-51 AC-13 | no | **added** (PD-1, PD-2): plan_join router → `escalation` / `facts` | step 5; reported to AEA-08 |
| Identity failure must produce "error + handoff" (UI_CONTRACTS), but DO-3 sends identity → facts, bypassing escalation | graph-tools §5; DO-4 §6 rule 5 | no | **added** (PD-3): identity router → `escalation` on `not_verified`/`code_locked`/`code_cap_reached` | step 5 |
| `CARD_CHOICE` → specialists fan-out with no `plan` in state | DO-3 §5.4; AEA-37 ("card choices never reach these nodes"); AEA-39 ("the open task a card choice resumes") | no | **added** (PD-4): router builds a resumed `PlannedTask` from the open task | step 5 |
| `DEADLINE`/spend halts from a specialist must not reach `decide_escalation` (X-5) though DO-3 has a plain `run_specialist → escalation` edge | graph-core §5, X-5 | AC-2 (implicit) | added: `route_after_specialists` (PD-5) | step 5 |
| Brake path escalation → handoff → facts → compose although `halt_route` says "brake after escalation ran → compose" | graph-core §5 table; AC-2 | AC-2 | added (PD-6): the escalation router lets a brake through to `handoff` once | step 5 |
| `GraphDeps` fields typed by classes that do not exist until waves 1–2 | graph-core §4 vs slice plan wave order | no | **added** (PD-7): typed aliases to `Any` until the owning module is on `main` | step 2; request R-3 |
| Turn-scoped reducer keys reset per invocation | AEA-02 plan §8.3; AC-4 | AC-4 | in-ticket; uses `Overwrite`, plain value on a fresh thread (P2) | step 8 |
| Block wire shapes and labels | OpenAPI CON-2 examples | AC-10…AC-12 | in-ticket; labels copied from the examples (PD-9) | steps 9–13 |
| Every customer sentence from `policy/texts.py` | ticket; data.md §2 | yes | in-ticket | steps 9–13 |
| Cards that need types AEA-02 does not build yet (`TurnFacts.account`, `missing`, `notices`) or AEA-13's fee note (slot card) | AEA-02 plan §8.2; AEA-13 (NEEDS-DECISION) | no | **other-ticket / request**: follow-up "AEA-21b compose cards" (R-2) | §8 |
| Capture checks CAP-1…CAP-3; E-1 graph runs | DO-6, DO-5 | indirectly | other-ticket: AEA-51 | — |
| The `register_graph` hunk and container wiring | slice plan §3 | yes | other-ticket: AEA-51 | — |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (`run_graph` is reached only through AEA-40's CON-2 route, WF-1) | — | — | — |

---

## 4. Shared code to use (exact shapes)

### 4.0 Module rules (every file this ticket creates)

1. First line after the module docstring: `from __future__ import annotations`. Dates as `import datetime as dt`.
2. Absolute imports only. `agent/routers.py` imports only: stdlib, `langgraph.types` (`Send`), `meridian.domain.*`.
   It must **never** import `meridian.agent.nodes` (any module), `meridian.agent.graph`, services or adapters.
3. `agent/nodes/compose.py` imports only: stdlib, `langgraph.runtime`, `meridian.domain.*`, `meridian.policy.texts`,
   `meridian.gates.gate` (`burning_card_id`), and `meridian.agent.context` (`GraphDeps`, for the node signature).
4. No module-level instances except immutable constants (`MappingProxyType`, tuples, frozensets, strings). No clock
   read, no logger call, no settings at import.
5. One statement per line (ruff E702). PEP 695 generics if any. Mypy strict with the pydantic plugin and
   `init_typed = true`: build ID fields with their classes (`TurnId("…")`), enums with members.
6. Errors raised by this code carry codes and names only, never a customer value.

### 4.1 Types this ticket imports (all from AEA-02 unless marked; paths are binding)

```python
from meridian.domain.common import Halt, HaltReason, ProviderFailure          # also re-exported where AEA-02 says
from meridian.domain.actions import ActionKind, CompletedAction, OpenCase, Settled, VisitView
from meridian.domain.handoff import CaseSummary, HandoffResult, Priority, Promise, BRIEF_TITLES  # BRIEF_TITLES unused here
from meridian.domain.identity import (CodeCapReached, CodeExpired, CodeLocked, CodeSent, CodeWrong, IdentityState,
                                      Located, NotVerified, Verified)
from meridian.domain.records import Passage, ShownSlot
from meridian.domain.specialists import KnowledgeResult, AccountResult, SchedulingResult, SpecialistResult
from meridian.domain.turn import (CheckEvent, GateDecision, GateKind, GateResult, GraphOutcome, PlannerTrace, Plan,
                                  PlannedTask, SignalName, SignalRecord, TurnContext, TurnIds, TurnInput, TurnPath,
                                  TurnOutcome, DegradeReason, TurnTrace, ComposedReply, CheckedReply, TurnFacts,
                                  EscalationDecision)
from meridian.domain.state import (ConversationState, Controller, OpenTask, SpecialistSend, LoadContextUpdate,
                                   GatesUpdate, SafetyUpdate, IdentityNodeUpdate, PlannerUpdate, DangerUpdate,
                                   PlanJoinUpdate, SpecialistUpdate, EscalationUpdate, HandoffNodeUpdate, FactsUpdate,
                                   ResponderUpdate, BriefUpdate, ChecksUpdate, ComposeUpdate)
from meridian.domain.blocks import (ReplyBlock, Speaker, SourceChip, Option, Money, Notice, SettledView, SettledVisit,
                                    SettledRequest, SettledIdentity, SettledReplying, Write, CallKey, QuickCheck,
                                    ShownWindow, FollowUpOptions, FollowUpChannelOption, FollowUpWindowOption,
                                    TextBlock, SafetyBlock, ConditionalSafetyBlock, BurningCheckBlock,
                                    EmergencyLineBlock, QuickChecksBlock, LocatePromptBlock, CodePromptBlock,
                                    ConfirmationBlock, CancelledBlock, ChangeRequestBlock, HandoffBlock,
                                    LiveQueuedBlock, FailureOfferBlock, NoInfoBlock, NoticeBlock, ErrorBlock)
from meridian.domain.staff import STAFF_PERSONAS, StaffRole
from meridian.ports.runtime import RetrievalIndex, TraceSink, UnitOfWorkFactory, SpanHandle   # SpanHandle re-export
from meridian.policy.limits import Limits                                                     # AEA-01
from meridian.policy.texts import TEXTS, TextId, render                                       # AEA-03 (on main)
from meridian.gates.gate import burning_card_id                                               # AEA-12 (step 14)
```

`HandoffReason`, `Priority`, `Promise`, `FollowUp`, `CaseState` are **defined** in `domain/common.py` and
re-exported from `domain/handoff.py` as `import X as X` (AEA-02 §4.0 rule 5); either import path is the same object.
`SpanHandle` is defined in `domain/turn.py` and re-exported from `ports/runtime.py`. `ShownSlot` (records) and
`IdentityState` (identity) are re-exported from `domain/state.py`.

Extra names the **test helpers** use (§6): `from meridian.domain.state import ChatLine, TaskDetails`;
`from meridian.domain.turn import Intake, FormValues, RuleMatches, PlannerOutcome, DangerAssessment, ResponderDraft,
TaskIntent, TurnBudget`; `from meridian.domain.specialists import KnowledgePoint, StaffNote`;
`from meridian.domain.actions import ActionKey`; `from meridian.domain.common import CaseRef, ThreadId, TurnId,
RequestId, PassageId`; `from langgraph.checkpoint.memory import InMemorySaver`; `from langgraph.types import Command`.

Shapes copied from AEA-02's plan (binding; re-read `src/meridian/domain/*.py` on `main` before coding and stop if a
name differs):

```python
class TurnContext:          # frozen dataclass: ids: TurnIds; budget: TurnBudget; now: dt.datetime; demo_session: str;
                            #   span: SpanHandle; intake: Intake | None = None
class TurnInput:            # turn_id, message_id: int, kind, text_store, card_id, choice, card_number_seen, received_at
class GraphOutcome:         # reply: ComposedReply; turn_trace: TurnTrace; check_events: tuple[CheckEvent, ...] = ();
                            #   halt: Halt | None = None; closed_every_open_task: bool = False
RunGraph = Callable[[TurnInput, TurnContext], GraphOutcome]          # domain/turn.py
class ComposedReply:        # blocks: tuple[ReplyBlock, ...]; settled_view: SettledView; writes: tuple[CompletedAction, ...];
                            #   notice: Notice | None; path: TurnPath; outcome: TurnOutcome; degrade_reason: DegradeReason | None
class TurnTrace:            # gate_result: GateResult; path; outcome; degrade_reason=None; planner: PlannerTrace | None = None;
                            #   danger_raised: bool = False; specialists_run: tuple[Literal["knowledge","account","scheduling"], ...] = ()
class PlannerTrace:         # model; fallback_used; failure: ProviderFailureKind | None; plan_mode; plan_source; intents=();
                            #   handoff_request=None; topic=None; planner_failed=False
class SignalRecord:         # record="signal"; name: SignalName; turn_id; thread_id; request_id; run_tag; node: str;
                            #   cause: str | None = None; role=None; specialist=None; attempt=None; recovered=None
CheckEvent.from_halt(turn_id, halt) -> CheckEvent        # check="brake", result="fired", codes=(reason, node)
GateDecision.gate_result() -> GateResult                 # graph-core §3 table (AEA-02)
TurnPath = Literal["safety", "burning_questions", "burning_unclear", "danger", "person", "talk", "act", "handoff",
                   "code", "paused", "degraded"]
```

`ConversationState` keys (AEA-02 §4.10): `thread_id`, `settled: Settled | None = None`, `controller`, `identity`,
`open_tasks`, `shown_slots`, `counters`, `burning_card_id`, `turn_input`, `chat_window`, `gate`, `planner`, `danger`,
`plan`, `identity_step`, `specialist_results` (`operator.add`), `escalation`, `handoff`, `facts`, `draft`,
`brief_extraction`, `checked`, `reply`, `halt` (`first_halt`), `check_events` (`add_turn_events`). **`last_lookups` and
`pending_change` are not built by AEA-02** (its §8.2); this plan tolerates both their absence and their later arrival.

### 4.2 The texts compose uses (`policy/texts.py`, on main; ids are `TextId` members)

| Use | `TextId` | Notes |
|---|---|---|
| Safety steps | `SAFETY_LEAVE_NOW`, `SAFETY_DONT_TOUCH` | `SafetyBlock.steps` in that order |
| Safety contact line | `SAFETY_CONTACT_LINE` | |
| R-7 question | `BURNING_QUESTION` | `BurningCheckBlock.question` |
| Conditional card | `WARNING_TEXT`, `EMERGENCY_NUMBER_LINE` | `ConditionalSafetyBlock.text`, `.emergency_line` |
| Emergency line card | `EMERGENCY_LINE_LEAD`; number and note parsed from `EMERGENCY_NUMBER_LINE` (§4.10 E-4) | no phone literal in compose |
| Timeout / spend / paused / cap | `TURN_TIMEOUT`, `SPEND_CAP_REACHED`, `AI_PAUSED_NOTICE` (`rep_name`), `BOOKING_CAP` | notice blocks |
| Person offer | `FAILURE_OFFER` | `FailureOfferBlock.text` |
| No source | `NO_INFORMATION` | `NoInfoBlock.text` |
| Identity | `VERIFIED`, `CODE_WRONG` (`n`), `CODE_EXPIRED`, `NOT_VERIFIED`, `IDENTITY_NEEDED` | error blocks and the locate prompt |
| Booking | `FREE_CHANGE_NOTE`, `CANCELLED_NO_FEE`, `QUICK_CHECKS_OFFER`, `OUT_OF_AREA`, `FEE_ORIGINAL_STAYS` | cards |
| Follow-up legend | `FOLLOWUP_LEGEND` | handoff chooser |

Always `TEXTS[TextId.X]` for a text with no placeholder and `render(TextId.X, name=value)` for one with placeholders.
Never type a customer sentence.

### 4.3 Labels compose uses that are not sentences (copied from the OpenAPI CON-2 examples; module constants)

```python
_ASSISTANT = Speaker(kind="assistant", display_name="Meridian assistant")    # every example's speaker
_WINDOW_LABELS: Mapping[str, str] = MappingProxyType({
    "08:00-12:00": "8:00 am – 12:00 pm", "12:00-16:00": "12:00 pm – 4:00 pm",
    "13:00-17:00": "1:00 pm – 5:00 pm", "16:00-19:00": "4:00 pm – 7:00 pm"})
_DOW3 = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")                    # date.weekday() index
_MON3 = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_SAFETY_SIGNAL_WORD = "DANGER"
_SAFETY_CALL_KEY = CallKey(label="Call 911 (from outside)", number="911")    # OpenAPI SAFETY example
_BURNING_OPTIONS = (Option(option="yes", label="Yes", disabled=False, reason=None),
                    Option(option="no", label="No", disabled=False, reason=None),
                    Option(option="not_sure", label="Not sure", disabled=False, reason=None))   # GRC-4 values
_QUICK_CHECK_OPTIONS = (Option(option="skip_and_book", label="Skip and book", disabled=False, reason=None),
                        Option(option="show_checks", label="Show the checks", disabled=False, reason=None))
_NEW_CODE_OPTION = Option(option="new_code", label="Send a new code", disabled=False, reason=None)
    # option value "new_code" (graph-core §2, AEA-12 AC-8, AEA-36) — NOT the example's "resend" (PD-10)
_INBOX_LINK = "/demo/inbox"
_LOCATE_FIELD_SETS = (("name", "phone"), ("customer_id",), ("invoice_number",))
_TIMELINE_TAIL = ("Technician arrives in the window", "Repair approved or declined at the visit")
_GENERAL_FOLLOWUP = FollowUpOptions(
    legend=TEXTS[TextId.FOLLOWUP_LEGEND],
    channels=(FollowUpChannelOption(channel="email", label="Email", on_record=False),
              FollowUpChannelOption(channel="phone", label="Phone call", on_record=False)),
    windows=(FollowUpWindowOption(window="morning", label="Mornings"),
             FollowUpWindowOption(window="afternoon", label="Afternoons"),
             FollowUpWindowOption(window="any", label="Any time")),
    general_only=True)                                                       # PD-11
_VARIANT: Mapping[str, str] = MappingProxyType({"R26.unstaffed": "nobody_online", "R26.refund": "refund",
                                                "R26.staffed": "staffed", "R26.safety_none": "nobody_online",
                                                "OD4.danger_review": "nobody_online"})
_EXCERPT_CHARS = 300
```

If a constant above cannot be a module-level model instance under AEA-02's classes (it can: they are frozen), build it
in a private function instead. Keep exactly these values.

### 4.4 `src/meridian/agent/context.py` (graph-core §4, R-G-13; PD-7)

```python
"""Constructor dependencies of the graph (GraphDeps) and the one-method ModelsStatus port (graph-core §4)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias

from meridian.policy.limits import Limits
from meridian.ports.runtime import RetrievalIndex, TraceSink, UnitOfWorkFactory

__all__ = ["GraphDeps", "ModelsStatus"]

# PD-7: these services are built by later tickets. Until the named module is on main, the field is typed through an
# alias to Any; AEA-51 (or the follow-up of R-3) replaces each alias with the real import. If a module below IS on main
# when you build, import its class under `if TYPE_CHECKING:` instead of declaring the alias (no other change).
ModelGateway: TypeAlias = Any       # meridian.agent.gateway.ModelGateway        (AEA-20)
IdentityService: TypeAlias = Any    # meridian.services.identity.IdentityService (AEA-27)
SchedulingService: TypeAlias = Any  # meridian.services.scheduling.SchedulingService (AEA-28)
HandoffService: TypeAlias = Any     # meridian.services.handoff.HandoffService   (AEA-29)
BriefAssembler: TypeAlias = Any     # meridian.services.handoff.BriefAssembler   (AEA-29)
DemoService: TypeAlias = Any        # meridian.services.demo.DemoService         (AEA-30)
SpecialistRunner: TypeAlias = Any   # meridian.agent.specialists.runner.SpecialistRunner (AEA-35)
CaseService: TypeAlias = Any        # meridian.services.cases.CaseService        (AEA-29)


class ModelsStatus(Protocol):
    """LedgerService.models_disabled (models.md §6): our cap reached or any provider circuit open (R-G-13)."""
    def models_disabled(self) -> bool: ...


@dataclass(frozen=True)
class GraphDeps:                    # field names and order exactly graph-core §4
    gateway: ModelGateway
    retrieval: RetrievalIndex
    uow: UnitOfWorkFactory
    identity: IdentityService
    scheduling: SchedulingService
    handoff: HandoffService
    brief: BriefAssembler
    demo: DemoService
    limits: Limits
    trace: TraceSink
    specialists: SpecialistRunner
    cases: CaseService
    ledger: ModelsStatus
```

### 4.5 `src/meridian/agent/signals.py` (graph-nodes §4)

```python
SIGNAL_LOGGER = "meridian.signal"

def emit_signal(ids: TurnIds, record: SignalRecord) -> None:
    """One `signal` LOG record, IDs and codes only (graph-nodes §4). web/logging.py's allow-list formats it."""
    # 1. if record.turn_id != ids.turn_id or record.thread_id != ids.thread_id:
    #        raise ValueError("signal record is for another turn")          # invariant: a record never crosses turns
    # 2. logging.getLogger(SIGNAL_LOGGER).info("signal", extra={"signal": record.model_dump(mode="json")})
```

`logging.getLogger` is called inside the function (rule 4.0.4). Nothing else is logged.

### 4.6 `src/meridian/agent/graph.py` — types and `timed_node` (graph-core §4, GRC-6, GRC-23)

```python
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langgraph.types import Overwrite

NodeInput = ConversationState | SpecialistSend
NodeUpdate = (LoadContextUpdate | GatesUpdate | SafetyUpdate | IdentityNodeUpdate | PlannerUpdate | DangerUpdate
              | PlanJoinUpdate | SpecialistUpdate | EscalationUpdate | HandoffNodeUpdate | FactsUpdate
              | ResponderUpdate | BriefUpdate | ChecksUpdate | ComposeUpdate)
NodeFn = Callable[[NodeInput, Runtime[TurnContext]], NodeUpdate]
CompiledGraph: TypeAlias = CompiledStateGraph[Any, Any, Any, Any]
RECURSION_LIMIT: Final = 25            # DO-3 §5.4; set explicitly (agent-architecture rule 15)

def timed_node(name: str, fn: NodeFn, deps: GraphDeps) -> NodeFn:
    def _run(state: NodeInput, runtime: Runtime[TurnContext]) -> NodeUpdate:
        # 1. t0 = time.monotonic(); status = "error"
        # 2. try: update = fn(state, runtime)
        #         status = "halted" if isinstance(update, dict) and cast(Mapping[str, object], update).get("halt")
        #                  is not None else "ok"
        #         return update
        # 3. finally: deps.trace.node(runtime.context.span, name, int((time.monotonic() - t0) * 1000), status)
        #    Invariant: exactly one span per node run, also when fn raises (the exception propagates unchanged);
        #    the span gets the name, a whole-millisecond time and the status, never state or text.
    return _run
```

The wrapper's two parameters **must be named `state` and `runtime`** (LangGraph injects `runtime` by name; P3).

### 4.7 `src/meridian/agent/routers.py` (graph-core §5, §11; DO-3 §5.4; PD-1…PD-6)

```python
BRAKE_HALTS: Final[frozenset[HaltReason]] = frozenset({HaltReason.BRAKE_TASKS, HaltReason.BRAKE_TOOL_ROUNDS,
                                                       HaltReason.BRAKE_SONNET_CALLS, HaltReason.BRAKE_IDENTICAL_CALL})
RouterResult: TypeAlias = str | list[str] | list[Send]
_FAN_OUT_NODE: Final = "run_specialist"
_IDENTITY_FAILURES: Final = frozenset({"not_verified", "code_locked", "code_cap_reached"})

def halt_route(state: ConversationState) -> Literal["escalation", "compose"] | None: ...
def route_act_plan(state: ConversationState) -> Literal["identity"] | list[Send]: ...
def route_after_gates(state: ConversationState) -> RouterResult: ...
def route_after_identity(state: ConversationState) -> RouterResult: ...
def route_after_plan_join(state: ConversationState) -> RouterResult: ...
def route_after_specialists(state: ConversationState) -> RouterResult: ...
def route_after_escalation(state: ConversationState) -> RouterResult: ...
def route_after_facts(state: ConversationState) -> RouterResult: ...
```

Algorithms (pure; read typed fields only; first match wins; the invariant each protects in *italics*):

`halt_route(state)`:
1. `halt = state.halt`; `None` → return `None`.
2. `halt.reason in BRAKE_HALTS and state.escalation is None` → `"escalation"`. *A brake goes once through escalation so
   an `ai_failure` case opens.*
3. Otherwise → `"compose"`. *Deadline and spend halts never reach `decide_escalation` (X-5).*

Private helpers:
- `_route_planned(planned: Sequence[PlannedTask], state) -> Literal["identity"] | list[Send]`: if
  `any(t.needs_identity for t in planned) and state.identity.status != "verified"` → `"identity"`; else
  `[Send(_FAN_OUT_NODE, SpecialistSend(planned=t, state=state)) for t in planned]`. *The router builds no
  `SpecialistTask` and does no I/O (R-G-12).*
- `_resumed(tasks: Sequence[OpenTask]) -> list[PlannedTask]`: for `i, t in enumerate(tasks[:3])`:
  `PlannedTask(order=i + 1, specialist=t.specialist, intent=t.intent, needs_identity=(t.status == "waiting_identity"),
  resumes_task_id=t.task_id)`. *PD-4: the open task's own status says whether it waits on identity; the dispatch guard
  (R-14) still refuses an unverified write.*
- `_open(state) -> list[OpenTask]` = `[t for t in state.open_tasks if t.status != "done"]`.

`route_act_plan(state)`: `plan = state.plan`; if `plan is None or not plan.tasks` → `raise ValueError("route_act_plan
needs an act plan with tasks")` (callers check first); else `_route_planned(plan.tasks, state)`.

`route_after_gates(state)`:
1. `routed = halt_route(state)`; not `None` → return it.
2. `gate = state.gate`; `None` → `raise ValueError("gates router: no gate decision")`.
3. `AI_PAUSED` → `"compose"`.
4. `SAFETY`, `BURNING_ASK`, `DANGER_RULE` → `"safety"`.
5. `BURNING_ANSWER`: `gate.burning_answer == "no"` → `route_act_plan(state)` (GRC-18 edge 2); else → `"safety"`.
6. `PERSON` → `"handoff"`.
7. `CODE_ENTRY`, `LOCATE` → `"identity"`.
8. `CARD_CHOICE` → `task = next(t for t in _open(state) if t.task_id == gate.resume_task_id)`; if none →
   `raise ValueError("card choice resumes a task that is not open")` (impossible by `decide_gate` step 10); else
   `_route_planned(_resumed([task]), state)`. *PD-4.*
9. `FREE_TEXT` → `["planner", "danger_classifier"]`.

`route_after_identity(state)`:
1. `halt_route` first.
2. `step = state.identity_step`; `step is not None and step.kind in _IDENTITY_FAILURES` → `"escalation"`. *PD-3:
   escalation rule 5 decides the case; compose shows error + handoff.*
3. `state.identity.status == "verified"`: if `state.plan is not None and state.plan.mode == "act" and state.plan.tasks`
   → `route_act_plan(state)`; elif `_open(state)` → `_route_planned(_resumed(_open(state)), state)`.
4. → `"facts"`.

`route_after_plan_join(state)` (order: GRC-18):
1. `halt_route` first.
2. `state.danger is not None and state.danger.raised` → `"safety"`.
3. `plan = state.plan`; `None` → `"facts"`.
4. `plan.planner_failed and not plan.tasks` → `"escalation"` (GRC-18 edge 1).
5. `not plan.tasks and plan.handoff_request is not None` → `"escalation"`. *PD-1: WP-7 refund, WP-8 cancel.*
6. `plan.mode == "talk"` → `"facts"`.
7. `not plan.tasks` → `"facts"`. *PD-2: an empty fan-out would end the graph with no reply.*
8. → `route_act_plan(state)`.

`route_after_specialists(state)`: `halt_route` first; else `"escalation"`. *PD-5.*

`route_after_escalation(state)`:
1. `routed = halt_route(state)`; if `routed is not None and not (state.halt is not None and state.halt.reason in
   BRAKE_HALTS and state.handoff is None)` → return `routed`. *PD-6: a brake whose case is not yet opened continues to
   `handoff` (graph-core §5 path); a brake after the handoff, or any other halt, goes to compose.*
2. `state.escalation is None` → `"facts"`.
3. `state.escalation.outcome == "escalate"` → `"handoff"`; else → `"facts"`.

`route_after_facts(state)`:
1. `halt_route(state) is not None` → `"compose"`. *Graph-core §5: after facts, a halted state skips responder, brief and
   checks.*
2. `state.handoff is not None and state.handoff.created` → `["responder", "brief"]`; else → `["responder"]`. *DO-3 §5.4
   "brief, only if a case opened this turn".*

### 4.8 `src/meridian/agent/graph.py` — building and running (graph-core §2, §4, §11)

```python
NODE_NAMES: Final = ("load_context", "gates", "safety", "identity", "planner", "danger_classifier", "plan_join",
                     "run_specialist", "escalation", "handoff", "facts", "responder", "brief", "checks", "compose")
TURN_SCOPED_KEYS: Final = ("chat_window", "gate", "planner", "danger", "plan", "identity_step", "specialist_results",
                           "escalation", "handoff", "facts", "draft", "brief_extraction", "checked", "reply", "halt")
DURABLE_KEYS: Final = ("settled", "controller", "identity", "open_tasks", "shown_slots", "last_lookups",
                       "pending_change", "counters", "burning_card_id")    # the last-lookups/pending ones may be absent
_IDENTITY_KEYS: Final = ("thread_id", "turn_input")                         # check_events: reducer-reset (graph-core §11)

GATES_PATHS: Final = ("compose", "safety", "handoff", "identity", "run_specialist", "planner", "danger_classifier",
                      "escalation")
IDENTITY_PATHS: Final = ("escalation", "compose", "run_specialist", "facts")
PLAN_JOIN_PATHS: Final = ("escalation", "compose", "safety", "facts", "identity", "run_specialist")
SPECIALISTS_PATHS: Final = ("escalation", "compose")
ESCALATION_PATHS: Final = ("handoff", "facts", "compose")
FACTS_PATHS: Final = ("compose", "responder", "brief")

def build_graph(deps: GraphDeps, *, checkpointer: BaseCheckpointSaver[Any] | None,
                composer: ReplyComposer) -> CompiledGraph: ...
def run_graph(graph: CompiledGraph, turn_input: TurnInput, ctx: TurnContext, *, deps: GraphDeps,
              composer: ReplyComposer) -> GraphOutcome: ...
def bind_run_graph(graph: CompiledGraph, *, deps: GraphDeps, composer: ReplyComposer) -> RunGraph: ...
```

Import the node modules as modules and read their functions **inside** `build_graph` (tests replace them with
`monkeypatch.setattr`): `from meridian.agent.nodes import act as act_nodes, compose as compose_nodes, front as
front_nodes, load_context as load_context_nodes, plan as plan_nodes, reply as reply_nodes`.

`build_graph` steps:
1. `builder: StateGraph[Any, Any, Any, Any] = StateGraph(ConversationState, context_schema=TurnContext)`.
2. A local `add(name, fn)` does `action: Any = timed_node(name, fn, deps)` then `builder.add_node(name, action)`
   (`Any` is required: P-mypy, §0). Register, in `NODE_NAMES` order, each as
   `cast(NodeFn, functools.partial(<module>.<fn>, deps=deps))`; `compose` is
   `functools.partial(compose_nodes.compose, deps=deps, composer=composer)`.
3. Edges: `START → load_context`; `load_context → gates`; `safety → compose`; `planner → plan_join`;
   `danger_classifier → plan_join`; `handoff → facts`; `responder → checks`; `brief → checks`; `checks → compose`;
   `compose → END`. Conditional: `gates` (`route_after_gates`, `list(GATES_PATHS)`), `identity`
   (`route_after_identity`, `list(IDENTITY_PATHS)`), `plan_join` (`route_after_plan_join`, `list(PLAN_JOIN_PATHS)`),
   `run_specialist` (`route_after_specialists`, `list(SPECIALISTS_PATHS)`), `escalation` (`route_after_escalation`,
   `list(ESCALATION_PATHS)`), `facts` (`route_after_facts`, `list(FACTS_PATHS)`).
4. `return builder.compile(checkpointer=checkpointer).with_config(recursion_limit=RECURSION_LIMIT)`.
   *Invariant: no `configurable` default is set, so `intake` can never reach checkpoint metadata (graph-core §2 rule 2).*

`run_graph` steps (graph-core §2, §11; GRC-20, 21):
1. If `turn_input.turn_id != ctx.ids.turn_id` → `raise ValueError("turn input and context disagree on the turn")`.
2. `config: Any = {"configurable": {"thread_id": str(ctx.ids.thread_id)}}` — **nothing else** in it, ever.
3. `fresh = not graph.get_state(config).values`. Build the update: `{"thread_id": ctx.ids.thread_id,
   "turn_input": turn_input}` plus, for every key in `TURN_SCOPED_KEYS`: `"chat_window": []`, `"specialist_results":
   Overwrite([])`, `"halt": None if fresh else Overwrite(None)`, every other key `None`. Do **not** put
   `check_events` or any `DURABLE_KEYS` in it. *Invariant: turn-scoped keys reset each invocation (DO-3 §5.1), durable
   keys persist, the first turn of a thread never stores a raw `Overwrite` (P2).*
4. `result = graph.invoke(update, config, context=ctx)` inside `try:`; `except GraphRecursionError: return
   _recursion_outcome(graph, config, ctx, deps=deps, composer=composer)`. Other exceptions propagate.
5. `state = ConversationState.model_validate(result)` (P1: `result` is a dict). `state.reply is None` →
   `raise RuntimeError("graph ended without a reply")`.
6. Return `GraphOutcome(reply=state.reply, turn_trace=turn_trace(state, state.reply),
   check_events=_turn_events(state, ctx.ids.turn_id), halt=state.halt,
   closed_every_open_task=_closed_every_open_task(state))`, where
   - `_turn_events(state, turn_id) = tuple(e for e in state.check_events if e.turn_id == turn_id) +
     (tuple(state.checked.events) if state.checked is not None else ())`;
   - `_closed_every_open_task(state) = state.halt is None and state.plan is not None and state.plan.mode == "act" and
     len(state.plan.tasks) >= 1 and all(t.status == "done" for t in state.open_tasks)`.
7. `_recursion_outcome(graph, config, ctx, *, deps, composer)`:
   1. `values = graph.get_state(config).values`; `last = ConversationState.model_validate(values) if values else None`;
      if `last is not None and last.turn_input.turn_id != ctx.ids.turn_id` → `last = None`.
   2. `halt = Halt(reason=HaltReason.RECURSION_LIMIT, node="run_graph", elapsed_ms=max(0, int((time.monotonic() -
      ctx.budget.started) * 1000)))`.
   3. `with deps.uow() as tx: settled = tx.core.settled_for(ctx.ids.thread_id, ctx.now)` (read-only; no model call
      inside). *DO-3 §2.3 rule 1.*
   4. `reply = composer.halt_reply(halt, settled, ctx)`.
   5. `events = (_turn_events(last, turn_id) if last else ()) + (CheckEvent.from_halt(ctx.ids.turn_id, halt),)`.
   6. `emit_signal(ctx.ids, SignalRecord(name=SignalName.BRAKE_FIRED, turn_id=ctx.ids.turn_id,
      thread_id=ctx.ids.thread_id, request_id=ctx.ids.request_id, run_tag=ctx.ids.run_tag, node="run_graph",
      cause=HaltReason.RECURSION_LIMIT.value))`.
   7. `trace = turn_trace(last, reply) if last else TurnTrace(gate_result="clear", path=reply.path,
      outcome=reply.outcome, degrade_reason=reply.degrade_reason)`.
   8. Return `GraphOutcome(reply=reply, turn_trace=trace, check_events=events, halt=halt,
      closed_every_open_task=False)`. *No exception reaches the caller.*

`bind_run_graph` returns a nested `def bound(turn_input: TurnInput, ctx: TurnContext) -> GraphOutcome` calling
`run_graph(graph, turn_input, ctx, deps=deps, composer=composer)`.

### 4.9 `src/meridian/agent/nodes/compose.py` — signatures (graph-core §13, graph-nodes §9.7)

```python
def compose(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps,
            composer: ReplyComposer) -> ComposeUpdate:
    return {"reply": composer.compose(state, runtime.context)}

def turn_trace(state: ConversationState, reply: ComposedReply) -> TurnTrace: ...

class ReplyComposer:                         # one concrete class, stateless, no I/O, no model, no clock read
    def __init__(self) -> None: ...
    def compose(self, state: ConversationState, ctx: TurnContext) -> ComposedReply: ...
    def halt_reply(self, halt: Halt, settled: Settled, ctx: TurnContext) -> ComposedReply: ...
    def handoff_block(self, result: HandoffResult) -> HandoffBlock | LiveQueuedBlock: ...
    def settled_view(self, settled: Settled, identity: IdentityState, controller: Controller) -> SettledView: ...
```

`turn_trace(state, reply)`:
1. `gate_result`: if `state.danger is not None and state.danger.raised`: `"danger"` when `state.danger.label ==
   "danger"`, else `"burning_unclear"`; elif `state.gate is not None`: `state.gate.gate_result()`; else `"clear"`.
2. `planner = None if state.planner is None else PlannerTrace(model=state.planner.model,
   fallback_used=state.planner.fallback_used, failure=state.planner.failure.kind if state.planner.failure else None,
   plan_mode=p.mode if p else None, plan_source=p.source if p else None,
   intents=tuple(t.intent for t in p.tasks) if p else (), handoff_request=p.handoff_request if p else None,
   topic=p.topic if p else None, planner_failed=p.planner_failed if p else False)` with `p = state.plan`.
3. `TurnTrace(gate_result=…, path=reply.path, outcome=reply.outcome, degrade_reason=reply.degrade_reason,
   planner=planner, danger_raised=bool(state.danger and state.danger.raised),
   specialists_run=tuple(r.kind for r in state.specialist_results))`.

### 4.10 `ReplyComposer.compose(state, ctx)` — the algorithm

Common values: `turn_id = ctx.ids.turn_id`; block ids from a local counter: the *k*-th block of this reply gets
`f"blk-{turn_id}-{k}"` (k from 1), `at=ctx.now`, `speaker=_ASSISTANT` (a private `_BlockIds` helper class or a closure;
never module state). The handoff card always comes from `self.handoff_block(result)` unchanged (its own id, §4.11).

**Effective settled.** `base = state.settled or Settled(actions=(), open_case=None, read_at=ctx.now)`. If
`state.handoff is not None` and `state.handoff.action.key` is not among `{a.key for a in base.actions}` →
`settled = Settled(actions=base.actions + (state.handoff.action,), open_case=_open_case(state.handoff.case),
read_at=base.read_at)` with `_open_case(c) = OpenCase(case_ref=c.case_ref, reason=c.reason, priority=c.priority,
state=c.state, promise=c.promise, followup=c.followup, live_queued=c.promise.live_queued)`; else `settled = base`.
*On the safety path `facts` does not re-read, yet the panel and `writes` must show the case just opened (OpenAPI
SAFETY example).* Then `writes = tuple(a for a in settled.actions if a.key.turn_id == turn_id)` and
`view = self.settled_view(settled, state.identity, state.controller)`.

Decide in this order (first match); each yields `(blocks, notice, path, outcome, degrade_reason)`:

**A. Safety lead** (`lead = _safety_lead(state, ctx, ids)`; non-empty ends here):
| Condition | Block | `path` |
|---|---|---|
| `gate.kind == SAFETY`, or `BURNING_ANSWER` with `"yes"` | `SafetyBlock(signal_word=_SAFETY_SIGNAL_WORD, steps=(TEXTS[SAFETY_LEAVE_NOW], TEXTS[SAFETY_DONT_TOUCH]), call_key=_SAFETY_CALL_KEY, contact_line=TEXTS[SAFETY_CONTACT_LINE], case_reference=<ref or None>)` | `"safety"` |
| `BURNING_ANSWER` with `"unsure"`; or `FREE_TEXT` and `danger.raised` with label `burning_unclear` | `ConditionalSafetyBlock(text=TEXTS[WARNING_TEXT], emergency_line=TEXTS[EMERGENCY_NUMBER_LINE], case_reference=<ref or None>)` | `"burning_unclear"` |
| `BURNING_ASK` | `BurningCheckBlock(card_id=burning_card_id(turn_id), options=_BURNING_OPTIONS, answered=None, question=TEXTS[BURNING_QUESTION])` | `"burning_questions"` |
| `DANGER_RULE`; or `danger.raised` with label `danger` | `EmergencyLineBlock(lead_text=TEXTS[EMERGENCY_LINE_LEAD], number=<E-4>, number_note=<E-4>, separate_line=<promise.text if state.handoff and state.handoff.case.promise.policy_row == "OD4.danger_review" else None>, case_reference=<ref or "">)` | `"danger"` |

`<ref>` = `state.handoff.case.case_ref` when `state.handoff` is set. Result: `blocks = lead`, `notice=None`,
`outcome="safety_reply"`, `degrade_reason=None`. **No handoff card, no text, no notice is added on these turns** (the
card carries the reference; A-13: no second `R26.unstaffed` promise). This holds whatever `controller` is (GRC-3 A) and
even if `state.halt` is set (DO-1 §8.2: the instruction is sent either way). (E-4) number and note:
`m = re.search(r"(\(\d{3}\) \d{3}-\d{4}) (\(demo number\))", TEXTS[TextId.EMERGENCY_NUMBER_LINE])`; `m is None` →
`raise RuntimeError("emergency number line changed shape")`; `number, number_note = m.group(1), m.group(2)`.

**B. Paused**: `gate.kind == AI_PAUSED` → `name = state.controller.representative_name or
STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name`; `NoticeBlock(code="AI_PAUSED", text=render(TextId.AI_PAUSED_NOTICE,
rep_name=name), person_key=True)`; `notice = Notice(code="AI_PAUSED", actions=(), retry_turn_id=None,
delivered_to_representative=True)`; `path="paused"`, `outcome="to_staff"`, `degrade_reason=None`.

**C. Halt** (`state.halt is not None`): `self._halt_parts(state.halt, state.handoff, ctx, ids)`:
| `halt.reason` | Blocks | `notice` | `degrade_reason` |
|---|---|---|---|
| `DEADLINE` | `NoticeBlock(code="TURN_TIMEOUT", text=TEXTS[TURN_TIMEOUT], person_key=True)` | `Notice(code="TURN_TIMEOUT", actions=("try_again", "talk_to_person"), retry_turn_id=str(turn_id), delivered_to_representative=False)` | `"timeout"` |
| `SPEND_CAP`, `PROVIDER_SPEND_CAP` | `NoticeBlock(code="SPEND_CAP_REACHED", text=TEXTS[SPEND_CAP_REACHED], person_key=True)` | `Notice(code="SPEND_CAP_REACHED", actions=("talk_to_person",), retry_turn_id=None, delivered_to_representative=False)` | `"spend_cap"` |
| any of `BRAKE_HALTS` | `[self.handoff_block(handoff)]` if `handoff` else `[FailureOfferBlock(text=TEXTS[FAILURE_OFFER], person_key=True)]` | `None` | `"brake"` |
| `RECURSION_LIMIT` | `[FailureOfferBlock(text=TEXTS[FAILURE_OFFER], person_key=True)]` (no case can exist) | `None` | `"brake"` |
All rows: `path="degraded"`, `outcome="degraded_handoff"`.

**D. Everything else** — assemble in this order (each item may add nothing):
1. **Identity error** (from `state.identity_step`, PA-1): `NotVerified` → `ErrorBlock(code="NOT_VERIFIED",
   text=TEXTS[NOT_VERIFIED], tries_left=None, fresh_windows=None, person_key=True)`; `CodeLocked` → same with
   `code="CODE_LOCKED"`; `CodeCapReached` → same with `code="CODE_CAP_REACHED"`; `CodeWrong(tries_left=n)` →
   `ErrorBlock(code="CODE_WRONG", text=render(TextId.CODE_WRONG, n=str(n)), tries_left=n, fresh_windows=None,
   person_key=False)`; `CodeExpired` → `ErrorBlock(code="CODE_EXPIRED", text=TEXTS[CODE_EXPIRED], tries_left=None,
   fresh_windows=None, person_key=True)`.
2. **Verified**: `Verified` → `TextBlock(text=TEXTS[VERIFIED], sources=())`.
3. **Main text**: `fallback = state.checked is None or state.checked.fallback_used` (a failed responder reaches
   `checks` with `draft=None` and comes back as `fallback_used=True`; define no separate `responder_failed` variable). If not `fallback` and
   `state.checked.text.strip()` → `TextBlock(text=state.checked.text, sources=_chips(state.facts))`. If `fallback` →
   `FailureOfferBlock(text=TEXTS[FAILURE_OFFER], person_key=True)` (the person offer; the code cards below are the
   facts' fixed fields).
   `_chips(facts)`: `None` → `()`; else for each `point in facts.points` in order, the `Passage` in `facts.passages`
   with `passage_id == point.passage_id`, de-duplicated by id, mapped by `_chip(p) = SourceChip(passage_id=str(p.passage_id),
   file=p.file, section=p.section, version_date=p.version_date, excerpt=_excerpt(p.text), audience="customer",
   version_label=p.version_label)`; `_excerpt(t) = t if len(t) <= _EXCERPT_CHARS else t[: _EXCERPT_CHARS - 1] + "…"`.
4. **No source**: `state.facts and state.facts.no_source_tasks` → `NoInfoBlock(text=TEXTS[NO_INFORMATION], person_key=True)`.
5. **Code prompt** (`step` kinds): `CodeSent(masked_hint, expires_at, sends_left)` → `CodePromptBlock(card_id=f"code-{turn_id}",
   options=(), answered=None, state="sent", hint=masked_hint, tries_left=state.identity.tries_left,
   expires_at=expires_at, resend_offered=False, resends_left=sends_left, inbox_link=_INBOX_LINK)`;
   `CodeWrong(tries_left=n)` → same card with `state="wrong"`, `hint=state.identity.masked_hint or ""`,
   `tries_left=n`, `expires_at=state.identity.code_expires_at`, `resends_left=None`; `CodeExpired(resend_offered,
   sends_left)` → `state="expired"`, `hint=state.identity.masked_hint or ""` (`CodePromptBlock.hint` is a required
   string), `options=(_NEW_CODE_OPTION,) if resend_offered else ()`, `tries_left=None`,
   `expires_at=state.identity.code_expires_at`, `resend_offered=resend_offered`, `resends_left=sends_left`.
6. **Locate prompt**: `state.identity_step is None and state.identity.status == "not_checked" and state.plan is not
   None and state.plan.mode == "act" and any(t.needs_identity for t in state.plan.tasks)` →
   `LocatePromptBlock(card_id=f"locate-{turn_id}", options=(), answered=None, reason_text=TEXTS[IDENTITY_NEEDED],
   field_sets=_LOCATE_FIELD_SETS)`.
7. **Write cards** (PA-3), for `a in writes` in order: `BOOKED`/`MOVED` with `a.after` holding `date`, `window`,
   `technician`, `fee_line` → `ConfirmationBlock(appointment_id=int(a.records["appointment"]),
   date=dt.date.fromisoformat(after["date"]), window_label=_window_label(after["window"]), technician=after["technician"],
   fee_line=after["fee_line"], timeline=(("Booked" if a.kind is ActionKind.BOOKED else "Moved"),) + _TIMELINE_TAIL,
   free_change_note=TEXTS[FREE_CHANGE_NOTE])`; `CANCELLED` with a date in `a.before` or `a.after` →
   `CancelledBlock(appointment_id=int(a.records["appointment"]), date=<that date>, fee_line=TEXTS[CANCELLED_NO_FEE])`.
   An action missing a needed key gets no card (never a crash on display).
8. **Quick checks** (graph-nodes §8, GRN-10): if `state.facts and state.facts.quick_checks` and a booking task exists
   (`task = first t in state.open_tasks with t.status != "done", t.specialist == "scheduling", t.intent ==
   TaskIntent.BOOK_NEW`) → one `QuickChecksBlock(card_id=f"{task.task_id}.1", options=_QUICK_CHECK_OPTIONS,
   answered=None, offer_text=TEXTS[QUICK_CHECKS_OFFER], checks=tuple(QuickCheck(text=p.text, source=_chip(p)) for p in
   <the Passages of facts.passages whose ids are in facts.quick_checks, in quick_checks order>))`. No booking task → no
   block. *`n` is the 1-based order of that task's cards in this reply; this ticket mints one (PD-8).*
9. **Scheduling results** (PA-4), for each `SchedulingResult` in `state.specialist_results`: `out_of_area` →
   `ErrorBlock(code="OUT_OF_AREA", text=TEXTS[OUT_OF_AREA], tries_left=None, fresh_windows=None, person_key=True)`;
   `booking_cap` → set `notice = Notice(code="BOOKING_CAP", actions=("talk_to_person",), retry_turn_id=None,
   delivered_to_representative=False)` and add `NoticeBlock(code="BOOKING_CAP", text=TEXTS[BOOKING_CAP],
   person_key=True)` (once).
10. **Change request** (PA-3): `draft = state.facts.change_request if state.facts else None`; if `draft` and
    `state.handoff` → `ChangeRequestBlock(change=draft.change, fee_line=<after["fee_line"] of the CHANGE_REQUEST_SENT
    write whose records["appointment"] == str(draft.appointment_id), else "">, original_stays_line=TEXTS[FEE_ORIGINAL_STAYS],
    wanted_text=draft.wanted_text, windows_shown=tuple(ShownWindow(slot_id=str(s.slot_id),
    window_label=_window_label(s.window), date=s.date) for s in state.shown_slots if s.slot_id in draft.windows_shown),
    reference=c.case_ref, promise_text=c.promise.text, due_at=c.promise.due_at, due_label=c.promise.due_label,
    extra_lines=c.promise.extra_lines, cant_guarantee_line=None, phone_support_line=None)` with `c =
    state.handoff.case`. Mark `handoff_shown = True` (PD-12).
11. **Offer**: `state.escalation and state.escalation.outcome == "offer"` and no `FailureOfferBlock` yet →
    `FailureOfferBlock(text=TEXTS[FAILURE_OFFER], person_key=True)`.
12. **Handoff card last** (R-26, after the checks): `state.handoff` and not `handoff_shown` →
    `self.handoff_block(state.handoff)`.

`notice` = the BOOKING_CAP notice or `None`. Then path / outcome / degrade_reason, first match:
| Condition | `path` | `outcome` | `degrade_reason` |
|---|---|---|---|
| `fallback` (= `state.checked is None or state.checked.fallback_used`; covers `responder_failed` and a checks fallback with a draft present; AC-12 "`fallback_used` → … `degrade_reason = model_error`") | `"degraded"` | `"degraded_handoff"` | `"model_error"` |
| `state.escalation and state.escalation.degraded` | `"degraded"` | `"degraded_handoff"` | `_DEGRADE_BY_RULE.get(rule_id, "model_error")`, where `"AI.planner_failed"`→`"model_error"`, `"AI.models_disabled"`→`"spend_cap"`, `"AI.halt"`→`"brake"`, `"AI.specialist_failed"`→`"tool_error"` if every failed result has `failure is None` else `"model_error"` |
| `gate.kind == PERSON` | `"person"` | `"handed_off"` | `None` |
| `state.handoff is not None` | `"handoff"` | `"handed_off"` | `None` |
| `gate.kind in {CODE_ENTRY, LOCATE}` | `"code"` | `"acted"` if a finished specialist (below) else `"answered"` | `None` |
| any `r` in `state.specialist_results` with `r.status != "failed"` | `"act"` | `"acted"` | `None` |
| otherwise | `"talk"` | `"answered"` | `None` |
Return `ComposedReply(blocks=tuple(blocks), settled_view=view, writes=writes, notice=notice, path=…, outcome=…,
degrade_reason=…)`. **Compose never reads `AccountResult.staff_notes`, `ctx.intake`, `state.turn_input.text_store` or
`state.draft` text except through `state.checked.text`** (AC-13).

### 4.11 `halt_reply`, `handoff_block`, `settled_view`

`halt_reply(halt, settled, ctx)`: blocks and fields from the §4.10 C table with `handoff=None`;
`writes = tuple(a for a in settled.actions if a.key.turn_id == ctx.ids.turn_id)`;
`view = self._view(settled, status=("verified" if settled.has(ActionKind.VERIFIED) else "not_checked"), hint=None,
controller=Controller(kind="ai"))`. Works with no graph state (AC-12).

`handoff_block(result)` (pure; also CON-4's card, X-9): `p = result.case.promise`;
`block_id = f"blk-{result.action.key.turn_id}-handoff"`, `at = result.action.at`, `speaker = _ASSISTANT`.
`p.live_queued` → `LiveQueuedBlock(reference=result.case.case_ref, promise_text=p.text)`; else
`HandoffBlock(card_id=f"handoff-{result.case.case_ref}", options=(), answered=None, reference=result.case.case_ref,
variant=_VARIANT.get(p.policy_row, "nobody_online"), promise_text=p.text, due_at=p.due_at, due_label=p.due_label,
extra_lines=p.extra_lines, followup_chooser=_GENERAL_FOLLOWUP)`. *Promise text, reference and due label come only from
`HandoffResult` (R-26); nothing from a draft.*

`settled_view(settled, identity, controller)`: `status = "not_checked" if identity.status == "located" else
identity.status`; `hint = identity.masked_hint if status in ("code_sent", "verified") else None`; then
`self._view(settled, status=status, hint=hint, controller=controller)`.

`_view(settled, *, status, hint, controller) -> SettledView`:
- `visit`: `v = settled.current_visit()`; `None` → `None`; else
  `SettledVisit.model_validate({**v.model_dump(), "window_label": _window_label(v.window)})`.
- `request`: `settled.open_case` → `SettledRequest(reference=oc.case_ref, promise_text=oc.promise.text,
  due_at=oc.promise.due_at, due_label=oc.promise.due_label, extra_lines=oc.promise.extra_lines,
  live_queued=oc.live_queued, followup=oc.followup)`; else `None`.
- `identity=SettledIdentity(status=status, hint=hint)`;
  `replying=SettledReplying(kind=controller.kind, display_name=controller.representative_name if controller.kind ==
  "human" else None)`.
- `actions=tuple(Write(kind=a.kind.value, summary=_write_summary(a, settled), turn_id=str(a.key.turn_id), at=a.at)
  for a in settled.actions)`.

`_window_label(w) = _WINDOW_LABELS.get(w, w)`. `_day(d) = f"{_DOW3[d.weekday()]} {_MON3[d.month - 1]} {d.day}"`.
`_write_summary(a, settled)` (OpenAPI examples; PD-9): `ref = a.records.get("case") or a.key.record_id`;
| `kind` | Summary |
|---|---|
| `BOOKED` | `f"Booked {_day(date)}, {_window_label(window)}"` from `a.after`; missing keys → `"Booked a visit"` |
| `MOVED` | `f"Moved to {_day(date)}, {_window_label(window)}"`; missing → `"Moved a visit"` |
| `CANCELLED` | `f"Cancelled {_day(date)} visit"` (date from `before` then `after`); missing → `"Cancelled a visit"` |
| `CHANGE_REQUEST_SENT` | `f"Change request {ref} sent to staff"` |
| `CASE_OPENED` | `f"{oc.priority.value} case {ref} opened"` when `settled.open_case` has `case_ref == ref` and priority P0/P1; else `f"Case {ref} opened"` |
| `FOLLOWUP_SAVED` | `"Follow-up preference saved"` |
| `VERIFIED` | `"Verified for this chat"` |

### 4.12 The five stub modules (graph-nodes §9.2–§9.6; async-safety rule 1)

Each function has exactly the signature below and its body is one `raise NotImplementedError("<path> <name>: stub
from AEA-21; AEA-NN fills it")`, e.g. `"src/meridian/agent/nodes/front.py gates: stub from AEA-21; AEA-36 fills it"`.
Module docstring names the owner. Imports: `Runtime` from `langgraph.runtime`, `GraphDeps` from
`meridian.agent.context`, the update types and `ConversationState`/`SpecialistSend` from `meridian.domain.state`,
`TurnContext` from `meridian.domain.turn`.

| File | Functions (`fn(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> <Update>`) | Owner |
|---|---|---|
| `load_context.py` | `load_context -> LoadContextUpdate` | AEA-34 |
| `front.py` | `gates -> GatesUpdate`, `safety -> SafetyUpdate`, `identity -> IdentityNodeUpdate` | AEA-36 |
| `plan.py` | `planner -> PlannerUpdate`, `danger_classifier -> DangerUpdate`, `plan_join -> PlanJoinUpdate` | AEA-37 |
| `act.py` | `run_specialist(payload: SpecialistSend, runtime, *, deps) -> SpecialistUpdate`, `escalation -> EscalationUpdate`, `handoff -> HandoffNodeUpdate` | AEA-39 |
| `reply.py` | `facts -> FactsUpdate`, `responder -> ResponderUpdate`, `brief -> BriefUpdate`, `checks -> ChecksUpdate` | AEA-38 |

Do **not** stub `build_specialist_task` (its `SpecialistTask` type is not built yet; AEA-39 adds it).

---

## 5. Steps (build order; each ends with a check)

Setup: work in the worktree the orchestrator gives you (pattern `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-21`),
on branch `aea-21-graph-spine` from a `main` that holds AEA-02. `export UV_LINK_MODE=hardlink`; `uv sync`; never copy
a venv; no `node_modules`. Confirm AEA-02 is on `main` (AEA-01 already is, `07924f5`):
`uv run python -c "import meridian.domain.state, meridian.domain.blocks, meridian.ports.runtime, meridian.policy.limits, langgraph"`.
If it fails, stop and report BLOCKED-ON AEA-02. Then read `src/meridian/domain/{common,actions,identity,specialists,handoff,blocks,turn,state,staff}.py`
and `src/meridian/ports/runtime.py`, and stop if a name in §4.1 differs. Check whether AEA-12 (`git log main --oneline
| grep "AEA-12"`; `src/meridian/gates/gate.py` defines `burning_card_id`) and AEA-10 (`src/meridian/adapters/sqlite/repos_core.py`
defines `settled_for`) are already on `main`; if so, do steps 14–15 in place instead of last.

1. **Package marker.** `test -e tests/unit/agent/nodes/__init__.py || touch tests/unit/agent/nodes/__init__.py`.
2. **`agent/context.py`** per §4.4 (decide each alias by whether its module exists on `main`). Write
   `tests/unit/agent/test_context.py`. Check: `uv run pytest tests/unit/agent/test_context.py -q`.
3. **Five stubs** per §4.12. Check: `uv run mypy src/meridian/agent/nodes`.
4. **`agent/signals.py`** per §4.5 + `tests/unit/agent/test_signals.py`. Check: its tests pass.
5. **`agent/routers.py`** per §4.7 + `tests/unit/agent/test_routers.py`. Check: router tests pass; `grep -n "nodes"
   src/meridian/agent/routers.py` prints nothing.
6. **`agent/nodes/compose.py` part 1**: constants (§4.3), `_view`, `settled_view`, `handoff_block`, `halt_reply`,
   `turn_trace`, the `compose` node function. Use a temporary local `_burning_card_id` **only if AEA-12 is not on
   main**, and replace it in step 14 (do not commit it).
7. **`agent/graph.py`**: types, `timed_node`, constants, `build_graph` (§4.6, §4.8). Check: `uv run python -c "from
   meridian.agent.graph import build_graph"`.
8. **`run_graph`, `bind_run_graph`** (§4.8 steps 1–6 and 7; in step 7.3 call `tx.core.settled_for` — if AEA-10 is not
   on main yet, finish everything else first and do this line in step 15).
9. **Compose part 2**: §4.10 A, B, C.
10. **Compose part 3**: §4.10 D items 1–6 (identity, text, no source, prompts).
11. **Compose part 4**: §4.10 D items 7–12 and the path/outcome table.
12. **Test support + compose tests**: `tests/unit/agent/nodes/compose_fixtures.py`, `test_compose.py`,
    `test_compose_blocks.py` (§6, §7.1). Iterate until green.
13. **Graph tests**: `tests/graph/_spine_doubles.py`, `test_spine.py`, `test_run_graph.py`. Iterate until green.
14. **AEA-12 import** (when `src/meridian/gates/gate.py` with `burning_card_id` is on `main`; rebase first):
    `from meridian.gates.gate import burning_card_id`; delete any temporary helper. Re-run `test_card_ids_use_prefixes`.
15. **AEA-10 call** (when `CoreRepos.settled_for` is on `main`; rebase first): the `tx.core.settled_for(...)` line.
    Re-run `test_recursion_limit_returns_graph_outcome`. **Never add `# type: ignore`** to bridge a missing sibling.
16. **Gates**: §7.3 in order, cheapest first.
17. **Journey record** §7.4; run the affected-journeys command.
18. **Context commit** (AC-16; `<sha>` = the feature commit's short SHA): (a) area map A7a row: the Owns cell keeps
    its paths; the Status cell (today `planned`) becomes exactly `partly built (AEA-21, <sha>):
    agent/{graph,routers,context,signals}.py, nodes/compose.py; stubs of nodes/load_context.py (AEA-34), front.py
    (AEA-36), plan.py (AEA-37), act.py (AEA-39), reply.py (AEA-38)`; (b) ICM: the file has **two** rows named "Routes verified against code and
    tests" (AEA-04 added one). Edit only the row whose evidence starts "2026-10-21: area map A0 → `policy/texts.py`":
    replace its evidence cell with `2026-10-21: A7a → agent/{graph,routers,context,signals}.py, nodes/compose.py checked
    against tests/unit/agent/ and tests/graph/test_{spine,run_graph}.py (AEA-21, <sha>; <n> pass)` (row ≤ 400 chars);
    prefix the `Last reconciled:` line's text with `2026-10-21 — AEA-21 graph spine (routes row); earlier, `. Leave the
    other row alone; (c) DO-3 §2.2:
    replace "[A: verify on the pinned `langgraph` 1.2.16 with a two-node timing test before the A7a ticket merges]" with
    "[M: two 1 s branch nodes in one superstep, invoked from a worker thread, took <elapsed> s on langgraph 1.2.16;
    `tests/graph/test_spine.py::test_two_node_parallel_timing`, AEA-21]"; §10 row C-5 last cell becomes "§2.2;
    arithmetic unchanged; measured <elapsed> s (AEA-21)"; (d) DO-3 §5.4 closing paragraph: replace "[A: the longest
    path is 14 steps; a test runs a 3-task turn under it]" with "[M: a 3-task turn finished at step <n>;
    `test_three_task_turn_under_limit`, AEA-21]", and append one paragraph: "**Built (AEA-21):** halt routing as
    [graph-core §5](contracts/stage7/graph-core.md) and the two added edges as graph-core §11; plus the routing
    conditions in `docs/plans/fanout/2026-10-21-build/AEA-21.md` §8.1 PD-1…PD-6 (a tasks-less plan with a handoff
    request or an act plan without tasks; identity failures to escalation; card choices resume the open task; a halted
    specialist turn; the brake passing escalation → handoff once)."; (e) DO-3 status: the `**Built:**` line under `## 3` gains
    `; agent/{graph,routers,context,signals}.py, agent/nodes/compose.py and the five node stubs (AEA-21, <sha>)`; the
    line-7 sentence `**Built so far (AEA-01, …)…**` gains `AEA-21 (<sha>): agent/{graph,routers,context,signals}.py,
    agent/nodes/compose.py, node stubs;` before "every other path below is planned"; in the §3 tree, append (after
    the wave column, as AEA-04 did for `privacy/redact.py`) `   built AEA-21 <sha>` to the `graph.py`, `routers.py`,
    `context.py`, `signals.py`, `nodes/compose.py` rows and `   stub AEA-21 <sha>` to the `nodes/load_context.py`,
    `nodes/front.py`, `nodes/plan.py`, `nodes/act.py`, `nodes/reply.py` rows; (f) the journey record (§7.4).
    Commit these in a separate `docs(context)` commit. Then write the dev-log run file (outside the repo, not committed).

**Commits:** explicit `git add <paths>` only (never `-A`); messages like `feat(graph): spine, routers, context, compose
(AEA-21)` and `docs(context): AEA-21 built paths, measurements and journey record`; last line of every message:
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Commit only on your branch; never push `main`; never
force-push.

**Do not:** edit any file outside §2.1; add a dependency; edit `web/container.py`; add a `register_*` hunk; import
`tests/fakes/*`; add a state key; add a customer sentence (a missing one is an AEA-03 follow-up: report it); put a
phone number, code or secret literal in source (sentinels in tests only as §6 says); call a model or open a database in
any test; add `# type: ignore`; use `configurable` for anything but `thread_id`; make `routers.py` import a node
module; let compose read `staff_notes`, `ctx.intake` or `turn_input.text_store`; run the full suite (no shared fixture,
settings or dependency changes here); bind ports 4019 or 5184; run pytest with more than `-n 2`.

---

## 6. Data and fixtures (synthetic only)

All IDs are synthetic UUID4 strings written as constants (version nibble `4`, variant `8`–`b`), e.g.
`THREAD = ThreadId("6f1c2d3e-4b5a-4c6d-8e7f-0a1b2c3d4e5f")`, `TURN3 = TurnId("1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d")`,
`TURN4 = TurnId("2b3c4d5e-6f7a-4b8c-9d0e-1f2a3b4c5d6e")`, `REQ = RequestId("3c4d5e6f-7a8b-4c9d-8e0f-2a3b4c5d6e7f")`.
`DEMO_NOW = dt.datetime(2026, 10, 16, 14, 20, tzinfo=ZoneInfo("America/Chicago"))`.

**WP-4F** (source: issued scheduling DB rows as AEA-10's plan §6 records them; synthetic thread and turn ids):
`CompletedAction(key=ActionKey(thread_id=THREAD, turn_id=TURN3, kind=ActionKind.MOVED, record_id="159"),
kind=ActionKind.MOVED, records={"appointment": "159", "slot": "56", "old_slot": "159"},
before={"date": "2026-10-22", "window": "08:00-12:00", "technician": "Marta Kowalski"},
after={"date": "2026-10-19", "window": "08:00-12:00", "technician": "Marta Kowalski", "service_type": "hvac_repair",
"fee_line": "Diagnostic fee: waived for members"}, at=DEMO_NOW - dt.timedelta(minutes=2))` (the fee line is synthetic;
the real one is AEA-13's). Checked text: `"Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta."`.

**Handoff results:** `Promise` built in the test from `TEXTS`/`render` (e.g. `render(TextId.PROMISE_UNSTAFFED,
due_label="Monday, October 19, 7:00 pm", case_ref="MHC-C-0007")`, `policy_row="R26.unstaffed"`); live-queued from
`TEXTS[PROMISE_STAFFED]` with `live_queued=True`; P1 danger from `TEXTS[PROMISE_DANGER_REVIEW]`,
`policy_row="OD4.danger_review"`. `CaseSummary(case_ref=CaseRef("MHC-C-0007"), …, version=1, due_at=…)`;
`HandoffResult(case=…, created=True, action=<CASE_OPENED action for this turn>, alert=None)`.

**Sentinels (AC-7, AC-13; mandated by the ticket and graph-core §2 rule 4; synthetic, from the reserved 555-01xx
range):** code digits `"914276"`, form phone `"512-555-0199"`, staff note `"SENTINEL-STAFF-NOTE-7731"`. Define each
once as a module constant in the test file that uses it.

**`tests/graph/_spine_doubles.py`** (no pytest fixtures with side effects; plain helpers):
- `RecordingSink`: `turn(ids)` → `contextlib.nullcontext(SpanHandle(turn_id=ids.turn_id, trace_id=None))`;
  `model_call(...)` records; `node(parent, name, elapsed_ms, status)` appends `(name, elapsed_ms, status)` to
  `self.nodes`; `export_status(turn)` → `"off"`.
- `UowDouble(settled: Settled)`: callable `(*, write=False, exclusive=False)` returning a context manager whose value has
  `.core.settled_for(thread_id, read_at)` recording `(thread_id, read_at)` in `self.calls` and returning `settled`.
- `make_deps(sink, uow=None) -> GraphDeps`: every `Any` field `object()`; `retrieval=cast(RetrievalIndex, object())`;
  `uow=cast(UnitOfWorkFactory, uow or UowDouble(empty_settled))`; `limits=Limits()`; `trace=sink`;
  `ledger=_LedgerDouble()` (`models_disabled() -> False`).
- `make_ctx(turn_id, *, intake=None) -> TurnContext` (budget `TurnBudget(started=time.monotonic(),
  deadline=started + 60.0)`; `span=SpanHandle(turn_id=turn_id, trace_id=None)`; `demo_session="demo-session-1"`;
  ids with `run_tag="live"`, `run_id=None`, `agent_version="test"`).
- `make_input(turn_id, text_store="Yes, please.") -> TurnInput` (`message_id=1`, `kind="text"`, `received_at=DEMO_NOW`).
- `install_doubles(monkeypatch, visits: list[str], **overrides)`: sets every node function in the five stub modules
  to a double `def _d(state, runtime, *, deps)` that appends its node name to `visits` and returns the default update,
  unless `overrides[name]` is given (called with the same arguments). Defaults:
  `load_context` → `{"settled": Settled(actions=(), open_case=None, read_at=runtime.context.now), "chat_window":
  [ChatLine(speaker="customer", text="hello", turn_id=runtime.context.ids.turn_id, at=runtime.context.now)]}`;
  `gates` → `{"gate": g, "check_events": (CheckEvent.from_gate(turn_id, g),)}` with `g = GateDecision(kind=FREE_TEXT,
  rules=no_rules())`; `safety`, `identity`, `handoff`, `brief` → `{}`; `planner` → `{"planner":
  PlannerOutcome(choices=None, probabilities=None, model="jev-test", fallback_used=False, failure=None)}`;
  `danger_classifier` → `{"danger": DangerAssessment(label="normal", raised=False, failure=None), "check_events":
  (CheckEvent.from_danger(turn_id, <that>),)}`; `plan_join` → `{"plan": Plan(mode="talk", tasks=(),
  handoff_request=None, topic="other", source="planner")}`; `run_specialist` → `{"specialist_results":
  [KnowledgeResult(status="answered", passages=(), points=(), tools=(), calls=())]}`; `escalation` →
  `{"escalation": EscalationDecision(outcome="none", reason=None, priority=None, rule_id="none")}`; `facts` →
  `{"facts": <minimal TurnFacts for this turn>}`; `responder` → `{"draft": ResponderDraft(text="Hello from the
  double.")}`; `checks` → `{"checked": CheckedReply(text=<draft text or "">, removals=(), fallback_used=state.draft is
  None, events=(CheckEvent.from_check("completion", turn_id, ()),))}`. `compose` is never replaced except in AC-8's
  error case.
- `no_rules() -> RuleMatches` = `RuleMatches(safety=None, burning_unclear=False, danger_words=False, person=False,
  policy_trigger=None, rule_ids=(), correction=False)`.
- The default `facts` double builds every **required** `TurnFacts` field (none but `quick_checks` has a default):
  `TurnFacts(turn_id=ctx.ids.turn_id, gate_kind=state.gate.kind if state.gate else GateKind.FREE_TEXT,
  plan_mode=state.plan.mode if state.plan else None, points=(), passages=(), no_source_tasks=(), windows_shown=(),
  writes_this_turn=(), change_request=None, handoff=state.handoff, escalation=state.escalation,
  identity_step=state.identity_step)`.
- Every `OpenTask` built in a test or double fills all six fields: `OpenTask(task_id="t-1", specialist="scheduling",
  intent=TaskIntent.BOOK_NEW, opened_turn=<turn id>, details=TaskDetails(), status="open")`.
- **These helper names and signatures are a contract with AEA-37** (its J-5 journey test imports them):
  `RecordingSink()`, `make_deps(sink, uow=None) -> GraphDeps`, `make_ctx(turn_id, *, intake=None) -> TurnContext`,
  `make_input(turn_id, text_store="Yes, please.") -> TurnInput`, `install_doubles(monkeypatch, visits, **overrides)`
  where an override is any callable `(state, runtime, *, deps)` (AEA-37 passes the real node functions). Keep them
  exactly; module constants `THREAD`, `DEMO_NOW` live in the same file.

**`tests/unit/agent/nodes/compose_fixtures.py`** (no import from `tests/graph/`; duplicate the two small builders
instead): the WP-4F action, `make_ctx`, `no_rules`, `gate(kind, **kw)`,
`state(**kw) -> ConversationState` (fills `thread_id`, `turn_input`, defaults), `facts(**kw) -> TurnFacts`,
`handoff_result(policy_row, text, *, live_queued=False, priority=Priority.P3, due=…) -> HandoffResult`,
`passage(pid, text) -> Passage`, `open_booking_task(task_id="t-1") -> OpenTask`.

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (names are binding)

**`tests/unit/agent/test_context.py`**
- `test_graph_deps_fields`: `[f.name for f in dataclasses.fields(GraphDeps)] == ["gateway", "retrieval", "uow",
  "identity", "scheduling", "handoff", "brief", "demo", "limits", "trace", "specialists", "cases", "ledger"]`; frozen.
- `test_models_status_is_structural`: a class with only `models_disabled()` assigned to a `ModelsStatus` variable (mypy)
  and called.

**`tests/unit/agent/test_signals.py`**
- `test_emit_signal_logs_one_record_codes_only` (`caplog` at INFO on `meridian.signal`): one record, message
  `"signal"`, `record.signal == SignalRecord(...).model_dump(mode="json")`.
- `test_emit_signal_rejects_other_turn`: `ValueError`, no record logged.

**`tests/unit/agent/test_routers.py`** (states built directly; no graph)
- `test_gates_edges` (parametrised): `AI_PAUSED`→`"compose"`; `SAFETY`, `BURNING_ASK`, `DANGER_RULE`→`"safety"`;
  `BURNING_ANSWER` `yes`/`unsure`→`"safety"`; `PERSON`→`"handoff"`; `CODE_ENTRY`, `LOCATE`→`"identity"`;
  `FREE_TEXT`→`["planner", "danger_classifier"]`.
- `test_burning_no_routes_act_plan`: with the code-built plan (one scheduling `BOOK_NEW`, `needs_identity=True`):
  identity `not_checked` → `"identity"`; `verified` → one `Send` to `"run_specialist"`.
- `test_route_act_plan_sends_planned_tasks`: 3 tasks, verified → 3 `Send`s, `node == "run_specialist"`,
  `set(arg) == {"planned", "state"}`, `arg["planned"] is` the plan's task, `arg["state"] is state`; `route_act_plan` on a
  plan with no tasks raises `ValueError`.
- `test_planner_failed_goes_to_escalation`: `Plan(mode="act", tasks=(), …, planner_failed=True)` → `"escalation"`; and
  danger raised beats it (→ `"safety"`).
- `test_plan_join_edges` (parametrised): danger raised → `"safety"`; tasks-less plan with `handoff_request=REFUND`
  (mode talk and act) → `"escalation"` (PD-1); talk → `"facts"`; act without tasks → `"facts"` (PD-2); act needing
  identity, not verified → `"identity"`; act → `Send`s.
- `test_identity_edges` (parametrised): step `NotVerified`/`CodeLocked`/`CodeCapReached` → `"escalation"`; verified +
  act plan → `Send`s for the plan; verified + one open `waiting_identity` task and no plan → one `Send` with
  `resumes_task_id` set; not verified → `"facts"`; verified with nothing open → `"facts"`.
- `test_card_choice_resumes_open_task`: `CARD_CHOICE`, `resume_task_id="t-1"`, open task t-1 `status="open"` → one
  `Send` whose planned task has `resumes_task_id == "t-1"`, `needs_identity is False`, `order == 1`; same with
  `status="waiting_identity"` and identity `not_checked` → `"identity"`.
- `test_specialists_edges`: no halt → `"escalation"`.
- `test_escalation_edges` (parametrised): `escalate` → `"handoff"`; `offer`, `none` → `"facts"`.
- `test_facts_edges`: no halt, no handoff → `["responder"]`; handoff `created=True` → `["responder", "brief"]`;
  `created=False` → `["responder"]`.
- `test_halt_route_from_every_router` (parametrised over the six routers × the seven halt reasons × escalation
  `None`/set): expected destination:

  | Router | brake, escalation `None` | brake, escalation set, handoff set | `DEADLINE`, `SPEND_CAP`, `PROVIDER_SPEND_CAP` |
  |---|---|---|---|
  | gates, identity, plan_join, specialists | `"escalation"` | `"compose"` | `"compose"` |
  | escalation (state has escalation `escalate`; handoff `None` in col 1) | `"handoff"` | `"compose"` | `"compose"` |
  | facts | `"compose"` | `"compose"` | `"compose"` |
  Also `halt_route` itself: no halt → `None`.
- `test_routers_never_import_act`: AST-scan `src/meridian/agent/routers.py`; no `Import`/`ImportFrom` names
  `meridian.agent.nodes` (or any submodule) or `meridian.agent.graph`; print the import list.

**`tests/unit/agent/nodes/test_compose.py`**
- `test_wp4f_settled_view_matches_words` (**WP-4F worked pair**, §1.1 expectations, incl. `turn_trace`).
- `test_handoff_card_only_from_handoff_result`: draft/checked text "Your reference is MHC-C-9999 and someone will call
  within the hour."; reply's `HandoffBlock` has `reference == "MHC-C-0007"`, `promise_text`, `due_label`,
  `extra_lines` equal to the result's promise; is the last block; `handoff_block(<live_queued result>)` is a
  `LiveQueuedBlock` with the staffed text; `card_id == "handoff-MHC-C-0007"`.
- `test_card_ids_use_prefixes`: burning ask → `burning_card_id(turn_id)` and `== f"burn-{turn_id}"`; `CodeSent` →
  `f"code-{turn_id}"`; locate state → `f"locate-{turn_id}"`; quick checks → `"t-1.1"`; every `card_id` of every reply
  matches `^(burn|code|locate)-<uuid>$|^[A-Za-z0-9_-]+\.[0-9]+$|^handoff-MHC-C-[0-9]{4}$`.
- `test_quick_checks_inline`: two passages → exactly one `QuickChecksBlock`, options `skip_and_book`/`show_checks`,
  `offer_text == TEXTS[QUICK_CHECKS_OFFER]`, `checks` texts and sources in `quick_checks` order.
- `test_p1_unstaffed_separate_line`: danger raised (label `danger`) + P1 result `OD4.danger_review` → first block
  `EmergencyLineBlock`, `separate_line == TEXTS[PROMISE_DANGER_REVIEW]`, `case_reference == "MHC-C-0010"`,
  `number` and `number_note` are substrings of `TEXTS[EMERGENCY_NUMBER_LINE]`; no `HandoffBlock`/`LiveQueuedBlock`;
  `TEXTS[PROMISE_UNSTAFFED]`'s first sentence absent from `reply.model_dump_json()`; `outcome == "safety_reply"`.
- `test_safety_instruction_first[ai]`, `[human]`: `SAFETY` gate, P0 handoff, `controller` ai / human
  (`representative_name="Riley"`) → `blocks[0]` is `SafetyBlock` with `steps == (TEXTS[SAFETY_LEAVE_NOW],
  TEXTS[SAFETY_DONT_TOUCH])`, `case_reference == "MHC-C-0008"`; `outcome == "safety_reply"`; `writes` holds the
  `case_opened` action; `settled_view.request.reference == "MHC-C-0008"`.
- `test_halt_and_fallback_replies` (parametrised rows; assert notice code, text, actions, `retry_turn_id`, blocks'
  types, `path`, `outcome`, `degrade_reason`): brake with handoff; `DEADLINE`; `SPEND_CAP`; `PROVIDER_SPEND_CAP`;
  `RECURSION_LIMIT` via `halt_reply(halt, settled, ctx)` with a verified action in `settled` (identity shows
  `verified`); paused (`controller` human, gate `AI_PAUSED`; text `render(AI_PAUSED_NOTICE, rep_name="Riley")`,
  `delivered_to_representative is True`, `outcome == "to_staff"`); responder failed (`draft=None`, `checked` fallback)
  → `FailureOfferBlock`, `model_error`; checks fallback with a draft present (`draft` set, `checked.fallback_used=True`)
  → `FailureOfferBlock`, `degraded_handoff`/`model_error`; planner failed (escalation `degraded=True`, `rule_id="AI.planner_failed"`,
  handoff) → `HandoffBlock`, `degraded_handoff`/`model_error`.
- `test_no_staff_note_or_code_in_reply`: `AccountResult` with a `StaffNote` holding the staff sentinel in
  `specialist_results`, ctx `intake` with code sentinel; neither string in `reply.model_dump_json()`,
  `turn_trace(...).model_dump_json()`.
- `test_turn_trace_values_match_do6` (parametrised): danger label `danger`/`burning_unclear` raised → that value;
  `CODE_ENTRY`, `LOCATE`, `CARD_CHOICE`, `FREE_TEXT` → `"clear"`; planner trace fields copied; `specialists_run ==
  ("account", "knowledge")` for results in that order; every value in `typing.get_args` of `GateResult`, `TurnOutcome`,
  `DegradeReason`.

**`tests/unit/agent/nodes/test_compose_blocks.py`** (plan-added)
- `test_identity_steps_map_to_con2_codes` (parametrised over the eight steps; PA-1; `CodeExpired` with
  `resend_offered=True` has one option `"new_code"`).
- `test_write_cards_and_summaries` (PA-2, PA-3): a `BOOKED` and a `CANCELLED` write this turn → `ConfirmationBlock`
  (window label, timeline starts `"Booked"`, `free_change_note`) and `CancelledBlock`; `settled_view.actions` summaries
  `"Booked Mon Oct 19, 8:00 am – 12:00 pm"`, `"Cancelled Thu Oct 22 visit"`, `"Verified for this chat"`,
  `"P0 case MHC-C-0008 opened"`.
- `test_settled_view_identity_and_request` (PA-2): `located` → `not_checked`, hint `None`; `code_sent` keeps the hint;
  `locked` hint `None`; open case → `request` fields equal the promise; human controller → `replying.display_name`.
- `test_change_request_block` (PA-3): `facts.change_request` + handoff → one `ChangeRequestBlock` with the shown
  windows' labels, `reference`, promise fields, `fee_line` from the `CHANGE_REQUEST_SENT` write; no `HandoffBlock`.
- `test_scheduling_result_errors_and_booking_cap` (PA-4).
- `test_failure_offer_on_escalation_offer` (PA-4): escalation `offer` → one `FailureOfferBlock`.

**`tests/graph/test_spine.py`** (real `build_graph`, `InMemorySaver()`, node doubles via `install_doubles`)
- `test_compiled_edges_match_table`: `{(e.source, e.target) for e in graph.get_graph().edges}` equals the set from §4.8
  (static edges + every path-map target), with `__start__`/`__end__`; print it.
- `test_skeleton_compiles_and_runs`: free-text talk turn → visits `load_context, gates, {planner, danger_classifier},
  plan_join, facts, responder, checks, compose` (compare the parallel pair as a set); reply `TextBlock` "Hello from the
  double."
- `test_stubs_raise_loudly`: each of the 14 stub functions (no doubles installed) raises `NotImplementedError` whose
  message contains its file path (e.g. `"src/meridian/agent/nodes/front.py"`).
- `test_brake_runs_escalation_once`: act plan (1 task), `run_specialist` returns a `BRAKE_TOOL_ROUNDS` halt + its
  brake event; `escalation` returns `escalate`/`degraded`/`AI.halt`; `handoff` returns a P3 `ai_failure` result →
  visits contain `escalation` once, then `handoff`, `facts`, `compose`; no `responder`, `brief`, `checks`; reply has the
  `HandoffBlock`, `degrade_reason == "brake"`.
- `test_turn_scoped_keys_reset_and_durable_keys_persist` (AC-4, PA-7): first assert every `TURN_SCOPED_KEYS` entry is in
  `ConversationState.model_fields`, the union of turn-scoped, durable, `thread_id`, `turn_input`, `check_events` covers
  every field, `"messages" not in model_fields`, and the only `Annotated` reducer fields are `specialist_results`,
  `halt`, `check_events`. Turn 1 (act plan, specialist result, `facts` writes `open_tasks`, `shown_slots`, `counters`;
  `gates` writes `burning_card_id`; `responder` writes a `DEADLINE` halt). Turn 2 on the same `thread_id` (talk, gates
  writes no `burning_card_id` key so it persists): `graph.get_state(config).values` → `specialist_results == []`,
  `halt is None`, every `check_events` item has turn 2's id, `plan.mode == "talk"`, `chat_window` equals turn 2's double
  value, durable keys equal turn 1's (plus `last_lookups`/`pending_change` only if present in `model_fields`).
- `test_three_task_turn_under_limit`: act plan with 3 tasks → 3 `run_specialist` visits, `specialists_run` has 3 items;
  `step = graph.get_state(config).metadata["step"]`; assert `step < 25`; print `"3-task turn finished at step {step}"`.
- `test_recursion_limit_returns_graph_outcome`: `load_context` double returns `Command(goto="load_context",
  update={})` → `run_graph` returns (no exception); `halt.reason == RECURSION_LIMIT`; `uow.calls == [(THREAD,
  ctx.now)]`; reply is the recursion `halt_reply` (FailureOfferBlock, `brake`); `check_events[-1].check == "brake"`,
  `codes == ("recursion_limit", "run_graph")`; earlier events all this turn's; `caplog` has exactly one
  `meridian.signal` record with `signal["name"] == "brake_fired"`, `signal["cause"] == "recursion_limit"`;
  `closed_every_open_task is False`.
- `test_two_node_parallel_timing` (AC-6): `importlib.metadata.version("langgraph") == "1.2.16"`; `planner` and
  `danger_classifier` doubles each `time.sleep(1.0)`; run `run_graph` inside a `threading.Thread`; measure around it;
  assert `0.95 <= elapsed < 1.6`; print `f"parallel superstep: {elapsed:.3f} s"`.
- `test_turn_context_reaches_nodes`: every double records `runtime.context`; all are `is ctx`; `now`, `budget`, `span`
  identical.
- `test_intake_never_checkpointed`: two turns with intakes holding the code sentinel (`kind="code"`) and the phone
  sentinel (`kind="form"`, `FormValues(phone=SecretStr(...))`); `gates` double reads
  `runtime.context.intake.code_digits.get_secret_value()` to prove delivery; neither sentinel in
  `repr(saver.storage) + repr(saver.writes) + repr(saver.blobs)`, in `str([c.metadata for c in
  saver.list(config)])`, in either `outcome.model_dump_json()`, or in `caplog.text`.
- `test_every_node_emits_one_span`: talk turn → `sink.nodes` names equal the visit list, each `"ok"`, each tuple has 3
  items (name, int, status); a `responder` returning a `DEADLINE` halt → its span `"halted"`; a `facts` double raising
  `RuntimeError("boom")` → `pytest.raises(RuntimeError)` from `run_graph` and the `facts` span is `"error"`.
- `test_graph_outcome_fields`: turn 1 then turn 2 whose `gates` double writes **no** event: `outcome2.check_events`
  holds only turn 2's events (`checks` double's `completion` event) — turn 1's excluded; `turn_trace.gate_result ==
  "clear"`; a danger-raised turn → `"danger"`, `danger_raised is True`; `specialists_run` in result order.
- `test_signal_and_span_carry_codes_only`: recursion run with ctx intake (code sentinel) and a staff-note sentinel in a
  double's `AccountResult` → neither in `sink.nodes` (repr) nor in any `meridian.signal` record's `signal` dict.

**`tests/graph/test_run_graph.py`**
- `test_closed_every_open_task` (parametrised, AC-14): booking turn whose only task `done` (facts double writes
  `open_tasks=[<task status "done">]`) → `True`; talk turn → `False`; act turn leaving a task `open` → `False`; halted
  turn (`responder` returns `DEADLINE`) → `False`; recursion path → `False`.

### 7.2 Existing tests that must stay green

`tests/unit/policy/test_texts.py`, `tests/unit/test_import_direction.py` and whatever AEA-01/AEA-02 add — this ticket
changes none of their inputs. Do not run them unless a gate below asks.

### 7.3 Gates (cheapest first; stop at the first red; `export UV_LINK_MODE=hardlink`)

| # | Command | Passing looks like |
|---|---|---|
| G-1 | `uv run ruff format --check src/meridian/agent tests/unit/agent tests/graph` | "N files already formatted" |
| G-2 | `uv run ruff check src/meridian/agent tests/unit/agent tests/graph` | "All checks passed!" |
| G-3 | `uv run mypy src/meridian/agent tests/unit/agent tests/graph/_spine_doubles.py tests/graph/test_spine.py tests/graph/test_run_graph.py` | "Success: no issues found" |
| G-4 | `uv run pytest tests/unit/agent tests/graph/test_spine.py tests/graph/test_run_graph.py -q` (serial: the timing test must not share CPUs; `pytest-xdist` is not a dependency, so no `-n`) | all pass; report the count |
| G-5 | `uv run pytest tests/graph/test_spine.py::test_two_node_parallel_timing tests/graph/test_spine.py::test_three_task_turn_under_limit tests/graph/test_spine.py::test_compiled_edges_match_table -s -q` | prints the elapsed time, the step number and the edge set (evidence for AC-6, AC-5, AC-1) |
| G-6 | `grep -rln "meridian.agent" tests/ \| sort` | only this ticket's test files (the affected set) |
| G-7 | `uv run python -m tests.journeys.affected --base main` | `0 journeys affected`, exit 0 |
| G-8 | `uv run python -c "import meridian.agent.graph, meridian.agent.nodes.compose"` | no output |

Also run `uv run pytest tests/unit/test_skeleton.py tests/unit/test_import_direction.py -q` once before the final
commit (they import the packages this ticket adds modules to; expect them unchanged and green). The full suite is
**not** run (rule `build-loop-test-scope`: no
shared fixture, setting, dependency or cross-codebase module changed).

### 7.4 Journey record (AC-15): `docs/testing/journeys/<YYYY-MM-DD>-AEA-21.md`

Same table shape as `docs/testing/journeys/2026-10-21-AEA-01.md` (fields: Claim, Level, Tested revision, Environment,
Command, Result, Evidence location, Remaining limitations, Blocked by):
- **Claim:** "AEA-21: the graph spine compiles and routes per DO-3 §5.4 + graph-core §5/§11 and this plan's PD-1…PD-6;
  `run_graph` returns `GraphOutcome`; compose builds the CON-2 blocks named in plan §4.10. No journey runs: wave 1
  precedes AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1). Journeys that will exercise this code:
  **J-1** (one turn), **J-2** (grounded answer with source), **J-3** (booking and the WP-4F follow-up), **J-4**
  (fee-bearing change), **J-5** (safety first), **J-9** (timeout, busy, degraded states)."
- **Level:** `mock-tested`. **Tested revision:** the feature commit SHA. **Environment:** worktree path; Python 3.12
  via `uv run`; LangGraph 1.2.16 in-memory saver; node doubles; no server, DB or model.
- **Command:** G-4 and G-5 verbatim. **Result:** counts, elapsed seconds, step number.
- **Remaining limitations:** node behaviour is doubles; compose cards deferred to R-2; container wiring AEA-51.
- **Blocked by:** AEA-57 (harness); AEA-51 (graph wiring, turn steps of J-1…J-5, J-9); AEA-34, 36–39 (nodes).

### 7.5 Evidence to report back

G-1…G-8 output lines; the parallel elapsed time and 3-task step number; the edge set; whether each `context.py` alias
was a real import or `Any`; whether steps 14–15 were done (SHA of `main` they rebased on); the journey record and
dev-log paths; any name in §4.1 that differed on `main` (if any, you should have stopped).

---

## 8. Risks and requests

### 8.1 Plan decisions (engineering; each reversible; reported to AEA-08 for DO-3 §5.4)

| ID | Decision | Basis |
|---|---|---|
| PD-1 | `plan_join` router: a plan with no tasks and a `handoff_request` → `escalation` | DO-4 §6 rules 2 and 4 need the escalation node; DO-3's `talk → facts` and an empty fan-out never reach it (WP-7, WP-8; AEA-39 AC-4; AEA-51 AC-13) |
| PD-2 | `act` plan with no tasks (and none of the above) → `facts` | An empty `Send` list ends the graph with no reply |
| PD-3 | `identity` router: `not_verified`, `code_locked`, `code_cap_reached` → `escalation` | graph-tools §5: these show "error + handoff"; only escalation (rule 5) opens that case |
| PD-4 | `CARD_CHOICE` → the router builds a resumed `PlannedTask` (order 1, `needs_identity = task.status == "waiting_identity"`, `resumes_task_id`) and fans out | DO-3 §5.4 card-choice edge; AEA-37 "card choices never reach these nodes"; no plan exists on this path; the R-14 guard still refuses unverified writes |
| PD-5 | `run_specialist` exit is a router (`halt_route`, else `escalation`) | X-5: deadline and spend halts never reach `decide_escalation` |
| PD-6 | The escalation router lets a brake whose case is not open yet continue to `handoff` | graph-core §5's brake path (escalation → handoff → facts → compose) and AC-2's "escalation once"; `halt_route` alone would skip the handoff |
| PD-7 | `GraphDeps` fields whose classes are built in waves 1–2 are typed through `TypeAlias = Any` until their module is on `main` | The classes cannot be imported before they exist; inventing Protocols would add seams DO-3 S-20 defers (AEA-20 chose a Protocol for its ledger; see R-3) |
| PD-8 | Task card ids are `f"{task_id}.{n}"`, `n` the 1-based order of that task's cards in this reply | graph-core §3 prefixes; uniqueness across turns is not needed (the gate routes by task id) |
| PD-9 | Labels, timeline steps and write summaries copied from the OpenAPI CON-2 examples as module constants (not sentences) | No `policy/texts.py` entry exists for them; the wire examples are the UX-owned source |
| PD-10 | The resend option value is `"new_code"`, label "Send a new code" | graph-core §2, AEA-12 AC-8 and AEA-36 match on `new_code`; the example's `"resend"` would be read as a stale card |
| PD-11 | `handoff_block` shows the general follow-up chooser (`general_only=True`, no on-record channels) | graph-core §13's signature carries no identity, and offering "on record" to an unverified customer gets 409 at CON-5 |
| PD-12 | A fee-bearing change shows `ChangeRequestBlock` instead of the handoff card; its `cant_guarantee_line` and `phone_support_line` are `None`, the lines stay in `extra_lines` | The promise carries them inside `extra_lines` (cases.md §3.2); splitting them by text matching would be fragile |
| PD-13 | Safety-lead turns ignore a halt and add no notice; `GraphOutcome.halt` still carries it | DO-1 §8.2: the instruction is sent either way |
| PD-14 | `halt_reply` with no state shows identity `verified` iff `settled` has a `VERIFIED` action, else `not_checked`; controller `ai` | Its signature has no identity; a stored action is the only evidence |

### 8.2 Requests to the orchestrator

- **R-1 (AEA-02b):** AEA-02 does not build `LastLookups`, `ChangeRequestRef`, `MissingInfo`, `NoticeCode`,
  `AccountFactsView` (its §8.2). This plan tolerates their absence. When AEA-02b adds required fields to `TurnFacts` or
  `OpenTask`, this ticket's test builders (`compose_fixtures.py`, `_spine_doubles.py`) need the new fields: AEA-02b must
  update them (one small edit each) or default the new fields.
- **R-2 (follow-up "AEA-21b compose cards", before AEA-51):** compose here does **not** build `SlotCardBlock` (its
  `standard_fee` needs AEA-13's `fee_note`, and AEA-13 is NEEDS-DECISION), `ErrorBlock SLOT_TAKEN` (needs the slot card
  for `fresh_windows`), `AccountCardBlock` (`TurnFacts.account`, R-1), `WherePromptBlock` and `UrgencyQuestionsBlock`
  (`MissingInfo`, R-1), `AppointmentBlock` (no confirm-result view), the card-number notice (`NoticeCode`) and the
  `no_fit` text. J-3 (booking) cannot pass without the slot card, so the follow-up must merge before AEA-51 and AEA-62.
- **R-3 (tighten `GraphDeps`):** once AEA-20, 27, 28, 29, 30, 35 are on `main`, replace the eight `Any` aliases in
  `agent/context.py` with `TYPE_CHECKING` imports (AEA-51 or a one-line-per-type follow-up). Alternative the
  orchestrator may prefer: narrow Protocols per service, as AEA-20 did for its ledger.
- **R-4 (AEA-08 reconcile):** record PD-1…PD-6 in DO-3 §5.4 and graph-core §5/§11; add the `handoff-<case_ref>` card
  prefix (PD-11's card; `card_target` reads it as `unknown` → `FREE_TEXT`, harmless) to graph-core §3; note
  `"new_code"` (PD-10) beside the OpenAPI example; consider an optional `identity` argument on `handoff_block` so a
  verified customer sees on-record channels (PD-11).
- **R-5 (AEA-40):** `TurnService` step 6 turns a returned `DEADLINE` halt into the `TURN_TIMEOUT` reply. On a safety
  turn with a deadline halt (PD-13) that would drop the safety instruction; step 6 should keep `outcome.reply` when
  `outcome.reply.outcome == "safety_reply"` (compose already built the right reply for every halt).
- **R-6 (AEA-10 / AEA-51, checkpointer):** LangGraph 1.2.16 logs "Deserializing unregistered type …" for our pydantic
  state and will block it in a future version; the `SqliteSaver` serializer should allow the `meridian.domain` types
  (`JsonPlusSerializer(allowed_msgpack_modules=…)`). Also P2 (raw `Overwrite` on an empty reducer channel): `run_graph`
  handles it with the fresh-thread check; anyone writing `Overwrite` to `halt` elsewhere must do the same.
- **R-7 (AEA-03):** if UX wants the labels of PD-9 under text ids, AEA-03 adds them and a follow-up swaps the constants.

### 8.3 Collisions with sibling tickets

| Surface | Sibling | Handling |
|---|---|---|
| `tests/unit/agent/nodes/__init__.py` | AEA-34, 36–39 may create the same 0-byte marker | identical empty files merge cleanly |
| `tests/graph/` | AEA-51 adds its own files there | this ticket adds no `conftest.py`; its helpers live in `_spine_doubles.py` |
| `.claude/reference/area-map.md` A7a row | AEA-34 shares the row | edit only the Status cell text for this ticket's files; expect a trivial text conflict at merge |
| `docs/design/code-design.md` `**Built:**` line, `icm-progress.md` row | every wave-1 ticket | append only; trivial conflicts expected |
| The five stub files | AEA-34, 36–39 replace them in wave 2 | they must keep the function names and signatures in §4.12 (the graph reads them by name) |

### 8.4 Other risks

- **Sibling shape drift:** if `main`'s `domain/*` differs from AEA-02's plan in a name this plan uses, stop and report.
- **Timing flake:** AC-6 needs two idle CPUs; run G-4/G-5 serially, not beside another test run. If it fails once
  under load, re-run once and report both numbers.
- **Sentinels:** AC-7's `"512-555-0199"` and `"914276"` are the ticket's mandated synthetic sentinels (the phone is in
  the reserved fictional 555-01xx range), in tests only, never in source, logs or traces; their purpose is to prove they
  never leak. Define each once per test file as `_CODE_SENTINEL` / `_PHONE_SENTINEL`. Note the emergency line in
  `policy/texts.py` is `(512) 555-0199`, a different string; the absence assertions match the sentinel exactly.
- **Compose size:** expect 550–650 lines; the hard cap is 700 (`code-structure`). If you exceed it, stop and report;
  do not create new modules (a split is a design change).

---

## 9. Readiness

**READY** (refreshed 2026-10-21 against `16ca639`). No product decision is open: GRC-3 and CAS-16 stand on their
recommended options (sign-off D-14); every routing and typing gap is decided in §8.1 as engineering and reported (R-4);
no signed contract changes. Prerequisites the orchestrator schedules:
- AEA-01 and AEA-03 are merged (`07924f5`, `60617f9`): no longer blockers.
- **blocked-on AEA-02** (every domain type, `ports/runtime.py`, the `CoreRepos` shell): nothing compiles without it.
- **blocked-on AEA-12** for `compose.py`'s `burning_card_id` import only (step 14) and **AEA-10** for the one
  `tx.core.settled_for` call in `run_graph` (step 15; the call goes through the injected `deps.uow` and is tested with
  `UowDouble`, but mypy needs the method on `CoreRepos`). Everything else builds and tests before them; the ticket
  merges after both. Both are wave-1 siblings; nothing else from a same- or later-wave ticket is imported (services are
  `Any` aliases in `GraphDeps`, PD-7, and tests use this ticket's own doubles).

**Gates:** none (no human, paid or live gate). No security review (not `risk::security`).
