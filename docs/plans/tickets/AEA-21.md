## [AEA-21] graph: spine, routers, context, compose

_Conventions for every inno-aea-callcenter issue (from the approved breakdown, `docs/plans/slice-plan.md`):_
repository `/home/linuxuser/workspaces/inno-aea-callcenter` (package `src/meridian/`, tests `tests/`, eval `eval/`); GitLab
`innocentnortey/inno-aea-callcenter`. Read first: `CLAUDE.md`, `.claude/README.md`, `.claude/reference/area-map.md`, the
slice plan's row for this issue, `docs/design/code-design.md` (DO-3) and `docs/design/contracts/internal-components.md`
(DO-4: exact types and signatures). Vocabulary: PRD R-n, US-n, WP-n, HP-n, WF-n, CAP-n, E-n, M-n, CON-n as their owner
documents define them. Workflow: `lane::build-loop` issues run plan (`fanout-planner`, plan meets
`to-tickets/templates/implementation-plan.md`) → implement (`fanout-implementer`) → test → `code-review-agent`; affected tests
only (`.claude/rules/build-loop-test-scope.md`); `risk::security` issues get frozen failing tests first and the security
agent at their wave merge. **Siblings in the same or a later wave are called through their DO-4 signature by injection
(constructor, `GraphDeps`, or `web/deps.py`) and tested with a double; a plan that needs more than that signature records
`blocked-on AEA-NN` instead of inventing behaviour.** Never: edit the briefing, issued data or `docs/archive/`; edit
`docs/ux/03-structure/ui-contracts.openapi.yaml` or `UI_CONTRACTS.md` (a needed change stops the issue and goes to
Innocent); touch `apps/web/**` or `docs/ux/**`; edit another issue's owned file (collision map, slice plan §3); put a
secret, verification code, card-like number or full phone number in code, logs, traces, fixtures or test names; call a
paid model in a default test (mark `live`); bind ports 4019 or 5184; `git add -A`. Evidence: every criterion names its
test or command and the result a reviewer should see; numbers come from runs, never from targets.

### What to build

> **US-17.** As a **homeowner** mid-booking, I need "what about Monday?" to apply to the visit we were just arranging, so
> that I don't start over every message. *(Acceptance: the follow-up resolves against the open task; a 20-turn chat keeps
> my verified identity and the open task; a safety phrase mid-chat still comes first.)*

**What it does in practice.** This ticket draws the fixed shape of one customer turn, runs it, and builds what the
customer sees at the end. The shape is static (DO-3 §5.4): `load_context` → `gates` → one of the fixed paths (paused,
safety, person, identity, card choice, or planner ∥ danger classifier → `plan_join`) → specialists → escalation →
handoff → `facts` → responder ∥ brief → checks → `compose`. No model chooses an edge the routers don't list. A halted
turn takes the halt path: a brake goes once through escalation (so an `ai_failure` case opens), a deadline or spend
halt goes straight to `compose`, and compose builds a code reply. The five node groups other tickets own
(`load_context` AEA-34, `front` AEA-36, `plan` AEA-37, `act` AEA-39, `reply` AEA-38) exist here as stubs with their
final signatures that raise `NotImplementedError`, so those tickets fill them in parallel against a compiled graph.
`run_graph` hands `TurnService` (AEA-40) one `GraphOutcome`: the reply, the turn row's decision codes, this turn's
check events and the halt.

**Owned modules:**
- `agent/context.py`: `GraphDeps` (graph-core §1, §4; GRC-6, GRC-15): DO-4 §2's nine fields (`gateway`,
  `retrieval`, `uow`, `identity`, `scheduling`, `handoff`, `brief`, `demo`, `limits`) plus `trace: TraceSink`,
  `specialists: SpecialistRunner`, `cases: CaseService` and `ledger: ModelsStatus`; and, beside it, the one-method
  `ModelsStatus(Protocol)` (`models_disabled() -> bool`), which the container's `LedgerService` satisfies structurally
  and the escalation node (AEA-39) reads as `EscalationInputs.models_disabled` (graph-core §4, R-G-13). Nothing else:
  `TurnContext`, `TurnIds`, `TurnBudget`, `SpanHandle` live in `domain/turn.py` (AEA-02, GRC-10).
- `agent/graph.py`: `build_graph(deps)`, compiled with the checkpointer it is given, `context_schema=TurnContext`
  (langgraph 1.2.16; the `config["configurable"]` fallback may never carry `intake`, graph-core §2 rule 2) and an
  explicit `recursion_limit` of **25** [A, DO-3 §5.4]. Every node is registered as
  `timed_node(name, partial(fn, deps=deps), deps)` with `NodeFn` as graph-core §4 (GRC-6, GRC-23): it calls
  `deps.trace.node(ctx.span, name, elapsed_ms, status)` in `finally`, status `ok` / `halted` / `error`, no text or values;
  nodes never call the sink. `run_graph`, the `RunGraph = Callable[[TurnInput, TurnContext], GraphOutcome]` that AEA-51
  binds (graph-core §2, §11; GRC-20, GRC-21): it builds `GraphOutcome.check_events` from the final state's
  `check_events` filtered to this `turn_id` plus `checked.events`, sets `turn_trace = turn_trace(state, reply)` and
  `halt`. On `GraphRecursionError` it reads the last checkpoint (`graph.get_state`), filters its events the same way,
  appends `CheckEvent.from_halt(turn_id, <RECURSION_LIMIT halt>)` and emits `brake_fired` (graph-nodes §1, §4), and
  returns `composer.halt_reply(halt, core.settled_for(thread_id, ctx.now), ctx)` with `halt` set. `run_graph` also sets
  `GraphOutcome.closed_every_open_task` (graph-core §2, R-G-21 = web R-W-5): True when the final state's plan is an `act`
  plan with at least one task and, after `facts`, no `state.open_tasks` item has status ≠ `done`; False on a halt or
  `GraphRecursionError`; computed purely from the final state, beside `turn_trace` (AEA-40 applies web.md §9's outcome
  table to it and never reads state). In tests the graph
  compiles with LangGraph's in-memory saver (slice plan §2: no storage dependency).
- `agent/routers.py`: pure conditional-edge functions over typed `ConversationState` fields only (agent-architecture rule
  13): the edges of DO-3 §5.4 plus the two of graph-core §11 (GRC-18): after `plan_join`, `plan.planner_failed and not
  plan.tasks` → `escalation` (order: `halt_route` → danger raised → this edge → DO-3 §5.4 edges); after `gates`,
  `BURNING_ANSWER` with `burning_answer == "no"` → `route_act_plan(state)`, the same function `plan_join` uses for an
  `act` plan (identity needed and missing → `identity`, else one `Send` per task). `route_act_plan` returns
  `[Send("run_specialist", SpecialistSend(planned=t, state=state)) for t in state.plan.tasks]`; it builds no
  `SpecialistTask` (the act node's `build_specialist_task` does, graph-nodes §9.5), and `agent/routers.py` never imports
  `agent/nodes/act.py` (graph-core §11, graph-nodes §9.1, R-G-12). **Every router calls
  `halt_route(state)` first** (graph-core §5, GRC-7): a halt in `BRAKE_HALTS` with `state.escalation is None` →
  `escalation`; any other halt (`DEADLINE`, `SPEND_CAP`, `PROVIDER_SPEND_CAP`), or a brake after escalation ran →
  `compose`; after `facts`, a halted state skips responder, brief and checks.
- `agent/signals.py` (new, GRC-17): `emit_signal(ids, record)` exactly as graph-nodes §4: one `signal` LOG record
  through `logging.getLogger("meridian.signal")`, IDs and codes only.
- `agent/nodes/compose.py` (GRC-21, GRC-24, graph-nodes §9.7): the `compose` node (`{"reply":
  composer.compose(state, ctx)}`), the pure `turn_trace(state, reply) -> TurnTrace` (the one builder; `gate_result` is
  the classifier's label when `state.danger.raised`, else `state.gate.gate_result()`), and `ReplyComposer` as
  graph-core §13: `compose`, `halt_reply`, `handoff_block(result) -> HandoffBlock | LiveQueuedBlock` (pure, usable outside
  a graph turn, X-9) and `settled_view(settled, identity, controller) -> SettledView` (= OpenAPI `Settled`; identity
  `located` shown as `not_checked`). Blocks in DO-4 §9 order; every customer sentence from `policy/texts.py` (AEA-03);
  card ids minted only with graph-core §3's prefixes (`burn-<turn_id>` via `gates.gate.burning_card_id`, `code-<turn_id>`,
  `locate-<turn_id>`, `<task_id>.<n>`). The handoff card (promise text, reference, due label) comes **only** from
  `HandoffResult`, after the checks (R-26). Quick checks: on a turn with non-empty `TurnFacts.quick_checks`, one
  `QuickChecksBlock` with `checks` inline (graph-nodes §8, GRN-10). On the P1 unstaffed path, `OD4.danger_review` goes in
  `EmergencyLineBlock.separate_line` and no second `R26.unstaffed` promise is shown (GRC-19, cases A-13). Halt replies per
  graph-core §5 / DO-4 §11 (table below); `CheckedReply.fallback_used` → the facts' fixed fields plus a person offer.
- Stubs: `agent/nodes/{load_context,front,plan,act,reply}.py` with the function signatures of graph-nodes §9 (each
  returning its update `TypedDict`), each raising `NotImplementedError` naming its path (async-safety rule 1).

| Halt (graph-core §5) | Path | Reply (DO-4 §11) | `outcome` / `degrade_reason` |
|---|---|---|---|
| `BRAKE_*` | escalation → handoff → facts → compose | handoff reply with what is settled; `ai_failure` P3 case | `degraded_handoff` / `brake` |
| `DEADLINE` | compose | `TURN_TIMEOUT` notice, "This is taking longer than it should.", settled, *Try again* (same `turn_id`) and *Talk to a person* | `degraded_handoff` / `timeout` |
| `SPEND_CAP`, `PROVIDER_SPEND_CAP` | compose | `SPEND_CAP_REACHED` notice ("I can't answer more questions right now. A person can pick this up.") + person key | `degraded_handoff` / `spend_cap` |
| `RECURSION_LIMIT` | `run_graph` catches `GraphRecursionError` | as a brake, no case | `degraded_handoff` / `brake` |
| `controller = human` (not a halt) | paused | `AI_PAUSED` notice, `delivered_to_representative: true` | `to_staff` |

**Example pair (WP-4F, turn 4: the SP-1 seam bug, DO-3 §1).** Input: turn 3 moved Linda Foster's visit to Monday 8–12
with Marta (an `actions` row of kind `moved`); turn 4 is "Yes, please." State reaching `compose`: `settled` holding that
`moved` action, this turn's facts empty, and a checked text "Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with
Marta." Expected `ComposedReply`: those words in a text block, a `SettledView` whose visit (built by
`Settled.current_visit()`, graph-core §14) shows Monday, October 19, 08:00–12:00, Marta, from the same `settled`;
`writes` empty (nothing written this turn); outcome `answered`; no notice. `turn_trace` for it: `gate_result="clear"`,
`outcome="answered"`, `degrade_reason=None`.

### Source
- stage7/graph-core.md §1 (`domain/turn.py` home), §2 (`TurnInput`, `TurnContext.span`/`intake`, `TurnTrace`,
  `TurnRecord`, `GraphOutcome`, `RunGraph`, rules for "never in state"), §3 (card prefixes), §4 (`GraphDeps`,
  `timed_node`, `NodeFn`, `agent/signals.py`), §5 (`halt_route`, `BRAKE_HALTS`), §6 (`settled_for`), §11 (`check_events`
  key, two router edges, `route_act_plan`), §13 (`ReplyComposer`), §14 (`VisitView`); its closing table (A-13, data 6);
  ledger `docs/plans/7b-decisions/graph-core.md` GRC-3, GRC-6, GRC-7, GRC-10, GRC-11, GRC-15…GRC-21, GRC-23, GRC-24.
- stage7/graph-nodes.md §1 (`CheckEvent.from_halt`), §4 (`SignalRecord`, `emit_signal`, `brake_fired`), §8 (quick
  checks, GRN-10), §9 (node signatures, update `TypedDict`s, §9.7 compose).
- stage7/graph-tools.md §2 (`SpecialistRunner`, GRT-6); stage7/models.md §4 (MOD-10, span on `TurnContext`), §5 *Halt →
  customer*; stage7/cases.md §3.4 (escalation rule 6).
- DO-3 §1 (WP-4F walk-through), §2.1, §2.2 (parallel branches [A], timing test), §2.3 rule 1, §4.5, §5.1–§5.4, §6 S-12,
  §10 C-5, C-6, C-7. DO-4 §1, §2, §3 (`GateDecision.gate_result`), §9 (`ComposedReply`, `CheckedReply`), §11.
- DO-1 §8.1, §8.2, §11 decision 3; SDQ-1, SDQ-2, SDQ-6; PRD R-5, R-26, R-31, R-41, R-45, §6.1–§6.2; HP-1; US-17;
  SCREEN_SPECS N-8, N-26, N-27 (via DO-4). DO-6 *Records* `turn`, *Status values*, line 65 rule 18.
- `agent-architecture.md` rules 10–16, 18; workspace rule `context-management-multi-turn.md` rule 1; `async-safety.md` rule 1.
- **Brief check:** serves "Everything the agent cannot handle must escalate cleanly to a human."; touches nothing out of
  scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] Routers follow DO-3 §5.4 plus graph-core §11's two edges exactly: each listed edge is taken for its typed condition and no other edge exists; `plan_join` with `planner_failed` and no tasks → `escalation`; `gates` with `BURNING_ANSWER`/`"no"` → `route_act_plan` (identity when needed and missing, else one `Send` per task, each carrying `SpecialistSend(planned=t, state=state)` and no `SpecialistTask`, R-G-12); `"yes"` and `"unsure"` → `safety` — verify: `tests/unit/agent/test_routers.py` (one parametrised case per edge, incl. `::test_planner_failed_goes_to_escalation`, `::test_burning_no_routes_act_plan` and `::test_route_act_plan_sends_planned_tasks`) — evidence: the edge table reproduced as passing cases; each `Send` payload's keys are exactly `planned` and `state`; `agent/routers.py` imports nothing from `agent/nodes/act.py` (AST scan in the same test).
- [ ] AC-2 [failure/refusal] Halt routing (GRC-7): every router calls `halt_route` first; each `BRAKE_*` halt with no escalation yet → `escalation`, and a brake after escalation ran → `compose`; `DEADLINE`, `SPEND_CAP`, `PROVIDER_SPEND_CAP` → `compose`; after `facts`, a halted state skips responder, brief and checks — verify: `tests/unit/agent/test_routers.py::test_halt_route_from_every_router` (parametrised over routers × halt reasons) and `tests/graph/test_spine.py::test_brake_runs_escalation_once` — evidence: the destination per (router, reason) asserted; node-double visit order shows escalation once and no responder on a halted turn.
- [ ] AC-3 [invariant] The compiled skeleton runs end to end with node doubles and the in-memory saver; the five stub modules have graph-nodes §9's signatures (mypy) and raise `NotImplementedError` naming their path when called — verify: `tests/graph/test_spine.py::test_skeleton_compiles_and_runs` and `::test_stubs_raise_loudly`; `uv run mypy src/meridian/agent` — evidence: a free-text turn visits the expected node sequence; each stub raises; mypy clean.
- [ ] AC-4 [invariant] Turn-scoped keys do not survive into the next invocation on the same thread, including `specialist_results` (an `operator.add` reducer) and `check_events` (reset by its `add_turn_events` reducer on the next turn's first event, never by `load_context`), while durable keys (`open_tasks`, `shown_slots`, `last_lookups`, `pending_change`, `counters`, `burning_card_id`) persist; the state has no growing message list (no `messages` key with an append reducer; `chat_window` replaced each turn) — verify: `tests/graph/test_spine.py::test_turn_scoped_keys_reset_and_durable_keys_persist` (two invocations, same `thread_id`) — evidence: turn-2 state asserted key by key.
- [ ] AC-5 [failure/refusal] `recursion_limit` is 25 and set explicitly: a 3-task turn completes under it; a node double that loops raises `GraphRecursionError` inside `run_graph`, which returns a `GraphOutcome` with `halt.reason == RECURSION_LIMIT`, `composer.halt_reply`'s reply built from `core.settled_for(thread_id, ctx.now)` (a `uow` double), `turn_trace` from the last checkpoint, the last checkpoint's events plus one `brake` event, one `brake_fired` signal, and no exception to the caller — verify: `tests/graph/test_spine.py::test_three_task_turn_under_limit` and `::test_recursion_limit_returns_graph_outcome` — evidence: step count of the 3-task turn; the outcome fields asserted.
- [ ] AC-6 [invariant] Parallel branches run in parallel on the pinned `langgraph` 1.2.16 sync runner: two branch nodes that each sleep 1 s in one superstep finish in about 1 s, not 2 s, when invoked from a worker thread — verify: `tests/graph/test_spine.py::test_two_node_parallel_timing` — evidence: measured elapsed time in the test output; the result written into DO-3 §2.2 in place of its [A].
- [ ] AC-7 [negative] `TurnContext` reaches every node as `runtime.context` (one `now` per turn, the caller's `budget` and `span`), and `intake` never enters state or a checkpoint: with an `Intake` whose `code_digits` are the sentinel `"914276"` and whose form phone is `"512-555-0199"`, neither string appears in any in-memory-saver checkpoint blob or metadata, in the returned `GraphOutcome`, or in captured logs — verify: `tests/graph/test_spine.py::test_turn_context_reaches_nodes` and `::test_intake_never_checkpointed` — evidence: node double reads the passed values; absence asserted over the saver's storage, the serialised outcome and `caplog`.
- [ ] AC-8 [capture] Node spans: every registered node runs inside `timed_node`, which calls `trace.node(ctx.span, name, elapsed_ms, status)` exactly once per node run with `ok`, `halted` (the node returned a halt) or `error` (it raised; the exception propagates), and the span carries no text or values — verify: `tests/graph/test_spine.py::test_every_node_emits_one_span` (in-memory sink double) — evidence: one `node` call per visited node with the expected status; recorded arguments contain only name, time and status.
- [ ] AC-9 [invariant] `run_graph` returns `GraphOutcome(reply, turn_trace, check_events, halt)`: `check_events` = the final state's events for this `turn_id` (a previous turn's events excluded) plus `checked.events`; `turn_trace = turn_trace(state, reply)`; `gate_result` is `danger` / `burning_unclear` when the classifier raised and `GateDecision.gate_result()` otherwise (`code_entry`, `locate`, `card_choice`, `free_text` → `clear`, C-6); `specialists_run` lists each this-turn result's `kind` in order — verify: `tests/graph/test_spine.py::test_graph_outcome_fields` and `tests/unit/agent/nodes/test_compose.py::test_turn_trace_values_match_do6` — evidence: every produced value is in DO-6's *Status values* table; event filtering asserted across two turns.
- [ ] AC-10 [invariant] Compose: the WP-4F turn-4 example gives the words and a `SettledView` from the same `settled`; `writes` equals this turn's writes only; the handoff card's promise text and reference equal `HandoffResult`'s even when the draft says otherwise, and `handoff_block` returns `LiveQueuedBlock` for a `live_queued` promise; the R-7 card id is `burning_card_id(turn_id)`; a quick-checks turn carries one `QuickChecksBlock` with `checks` inline; the P1 unstaffed reply puts `OD4.danger_review` in `separate_line` with no second `R26.unstaffed` promise — verify: `tests/unit/agent/nodes/test_compose.py` (`::test_wp4f_settled_view_matches_words`, `::test_handoff_card_only_from_handoff_result`, `::test_card_ids_use_prefixes`, `::test_quick_checks_inline`, `::test_p1_unstaffed_separate_line`) — evidence: blocks asserted.
- [ ] AC-11 [invariant] Safety first (R-5; E-5): with a `SAFETY` gate the first block is the fixed safety instruction from `policy/texts.py`, before any other block, including when `controller = human` (GRC-3 option A: safety card, outcome `safety_reply`; the message still reaches the representative through AEA-36/AEA-40) — verify: `tests/unit/agent/nodes/test_compose.py::test_safety_instruction_first` (parametrised over `controller` ai / human) — evidence: first block asserted in both cases.
- [ ] AC-12 [failure/refusal] Halt and fallback replies follow the table above: one case per row, plus `fallback_used` → facts' fixed fields and a person offer with `degrade_reason = model_error`, and `planner_failed` → handoff reply with `model_error`; `halt_reply` works with no graph state (only `halt`, `settled`, `ctx`) — verify: `tests/unit/agent/nodes/test_compose.py::test_halt_and_fallback_replies` — evidence: notice code, sentence id, keys, `outcome` and `degrade_reason` asserted per row.
- [ ] AC-13 [negative] Nothing staff-only or secret reaches a customer block, a span or a signal: a distinctive staff-note sentinel placed in the state's account result and a six-digit code in the turn input never appear in any `ComposedReply` block, `SettledView`, `TurnTrace`, node-span argument or `signal` record — verify: `tests/unit/agent/nodes/test_compose.py::test_no_staff_note_or_code_in_reply` and `tests/graph/test_spine.py::test_signal_and_span_carry_codes_only` — evidence: both values absent from the serialised reply, trace and captured records.
- [ ] AC-14 [invariant] `run_graph` sets `GraphOutcome.closed_every_open_task` by graph-core §2 (R-G-21 = web R-W-5): True after a booking turn whose only task finishes `done` and leaves no open task; False after a no-task turn, after a turn that leaves a task open, after a halted turn and after the `GraphRecursionError` path — verify: `tests/graph/test_run_graph.py::test_closed_every_open_task` (node doubles, in-memory saver) — evidence: the five cases with their asserted value.
- [ ] AC-15 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-21.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-5 and J-9 (the graph spine, routers and compose) as the journeys that will exercise this code once AEA-57 and AEA-51 land, so the seam audit knows where to look (pattern C, `docs/plans/ux-join/backend-amendments.md` §3) — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-16 [regression/context] In the same change: `.claude/reference/area-map.md` A7a row (`agent/{graph,routers,context,signals}.py`, `nodes/compose.py` planned → actual + commit; the five stubs noted with their owners 34, 36–39); `.claude/state/icm-progress.md` affected row; DO-3 §2.2 and §5.4 [A]s replaced by the measured results (AC-6, AC-5); DO-3 §5.4 links graph-core §5 and §11 for the halt routing and the two added edges; DO-3 code-design status for these modules; a dev-log entry — verify: `git diff --name-only` — evidence: those paths in the diff.

### Observability
- Responsibilities: for WF-1 (and its `eval`/`load`-tagged turns under WF-9 and WF-10): one timed `node` span per node
  under the turn's span (`timed_node`, DO-6 rule 18, GRC-6); the `turn` record's decision fields `gate_result`, `path`,
  `outcome`, `degrade_reason`, planner trace, `danger_raised` and `specialists_run` through `GraphOutcome.turn_trace`
  (DO-6 *Records* `turn`, *Status values*; AEA-40 writes the row); this turn's `check_event`s through
  `GraphOutcome.check_events`, including the `RECURSION_LIMIT` `brake` event; the `signal` LOG record helper
  `emit_signal` for every node's DO-1 §8.2 signals (graph-nodes §4), with `brake_fired` emitted here for
  `RECURSION_LIMIT`. Codes only, never text or values.
- Capture evidence: AC-8 (node spans), AC-9 (turn decision fields and events), AC-13 (forbidden values absent) here;
  AEA-51 drives CON-2 through the full graph for CAP-1, CAP-2 and CAP-3 and finds the `turn` records, nested spans and
  `check_event` rows with these values.

### Evaluation
- Checks: adds `tests/graph/test_spine.py`, the router and compose tests; keeps the E-5 invariant "the safety instruction
  is the first text of the reply" true at the composition step (AC-11) and the WP-4F state seam (E-1) answerable once
  AEA-34 and AEA-38 land. E-1 graph runs of WP-1…WP-8, WP-4F, DANGER, NODANGER are AEA-51's.
- Expected-answer authority: the worked pairs (WP-4F, WP-5) and DO-4 §11 with `policy/texts.py` (UX-owned copy, DAT-6)
  decide the expected blocks (evaluation plan *Expected-answer authority*).

### Metrics
- References: M-14 (safety instruction first), M-16 (danger recall: `gate_result` from the classifier label), M-22
  (handoffs by reason), M-24 (turns ending `degraded_handoff` by reason), M-3 and M-18 (conversation outcomes built from
  turn outcomes).
- Acceptance conditions: each stays computable from the `turn_trace` values `run_graph` returns (AC-9) and the halt
  replies (AC-12); M-18's end rule "a turn that closes every open task" is the `closed_every_open_task` flag (AC-14),
  which AEA-40 turns into `conversations.outcome`; no degraded turn is ever reported as `answered` or `acted` (DO-6: a brake or failure is a health
  event, never a resolution). No target here.

### Blocked by
- AEA-02 (`domain/turn.py` types incl. `GraphOutcome` with `closed_every_open_task` (R-G-21), `TurnTrace`, `CheckEvent`,
  `SignalRecord`; `domain/state.py` with the update `TypedDict`s, `SpecialistSend(planned, state)` (R-G-12) and
  `add_turn_events`; `domain/blocks.py`; ports), AEA-03 (`policy/texts.py`).
- Not a merge blocker: AC-15's journey record names *Blocked by* AEA-57 (harness, wave 2) and AEA-51 (journey landing,
  wave 3); this issue merges on its unit and contract tests.

### Agent handoff
- Area / owner: A7a Graph spine; files `src/meridian/agent/{graph,routers,context,signals}.py`,
  `agent/nodes/compose.py`, the five stub files, tests under `tests/unit/agent/` and `tests/graph/test_spine.py`; only
  its own `register_<x>()` stub in `web/container.py` (AEA-51 completes `register_graph`, binds `run_graph` and wires
  `GraphDeps.ledger` to the container's `LedgerService`, R-G-13). Tests also include `tests/graph/test_run_graph.py` (AC-14).
- Contracts and shared surfaces: **consumes** `domain/{turn,state,blocks,actions}.py` and ports (AEA-02),
  `policy/texts.py` (AEA-03), `policy/limits.py` (AEA-01), `core.settled_for` through `deps.uow` (AEA-10, double), and
  every `GraphDeps` service by its DO-4 §14 / stage7 signature as doubles (real ones wired at AEA-51).
  `gates.gate.burning_card_id` (AEA-12, same wave) is imported by its graph-core §3 signature; if AEA-12 has not merged
  when this merges, the plan records `blocked-on AEA-12` for that import only. **Produces** `build_graph`, `run_graph`,
  the routers, `GraphDeps`, `ModelsStatus` (AEA-39's escalation node), `timed_node`, `emit_signal`, `ReplyComposer`,
  `turn_trace` and `GraphOutcome.closed_every_open_task` (read by AEA-40, web.md §9) for AEA-34 (replaces the
  `load_context` stub), AEA-36 (`front`), AEA-37 (`plan`), AEA-38 (`reply`), AEA-39 (`act`), AEA-40 (`GraphOutcome`
  through the injected `run_graph`), AEA-42 (`handoff_block`, `settled_view`) and AEA-51 (wiring). **Must not edit:** the
  stub files after this ticket merges (one owner each, collision map), `domain/*`, `policy/*`, `gates/*`,
  `adapters/checkpointer.py` (AEA-10), `web/logging.py` (AEA-23).
- Scope boundary / refusal: no node logic beyond `compose` (gates, planner, specialists, escalation, facts, responder,
  checks belong to 34/36–39); no database access except `core.settled_for` on the `RECURSION_LIMIT` path; no model call;
  no new customer sentence (a missing one is a small AEA-03 follow-up); no new state key outside DO-3 §5.2 and graph-core
  §3, §9, §11; never `intake` in `configurable`.
- Wave and gates: wave 1; gates None.
- Lane: `lane::build-loop` — source and tests that every turn runs.
- Risk: None (slice plan §1 row AEA-21). Reviewer note: AC-7 is the guard that code digits and form values never reach a
  checkpoint; if `code-review-agent` finds another path, the orchestrator adds `risk::security`.
- Entry points added or changed: None
- Awaiting Innocent: GRC-3 — built on the recommended option (A: safety before AI-paused, so a safety message while a
  representative owns the chat gets the safety card, AC-11); if he picks B, compose returns the `AI_PAUSED` reply for
  that case and AC-11's `controller = human` case flips; if C, the burning-smell and danger-word replies also compose
  under `controller = human`.
