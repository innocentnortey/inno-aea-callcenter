## [AEA-35] specialists: specs, braked tool loop, wording

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

> **US-6:** "As a **homeowner**, I need answers about membership, billing fees, warranty, services, hours and the service
> area that come from Meridian's current documents and show where they came from, so that I can trust the number I'm
> given." (Also US-9, US-10, US-11, US-12, US-13.)

**Example pair 1 (WP-1, knowledge).** Input: a `SpecialistTask` for `PlannedTask(specialist="knowledge",
intent=answer_question)` with customer text "What does the Comfort Club membership actually include?". Output:
`KnowledgeResult(status="answered")` whose every point cites a `passage_id` that `kb_search` returned **in this run** from
`membership/comfort_club_overview.md` (two tune-ups a year, priority scheduling, $89 diagnostic fee waived, 15% off
repairs, no after-hours dispatch fee, reminders; $189/year or $16.99/month with a 12-month minimum), and none of the
archive values ($149, $12.99, $219, "10% off").

**Example pair 2 (WP-4, scheduling).** Input: verified MHC-57204, tune-up appointment today 12:00–16:00 (two hours away on
the demo clock, Fri 2026-10-16 10:00), customer text "I have a tech coming … but something came up. Can I move it?".
Output: the move is refused by code (`ToolErrorCode.FEE_BEARING`, AEA-28's `Refused.code` mapped one-to-one by its
executor, graph-tools C-7) and the result is `SchedulingResult(status="staff_change_request",
change_request=ChangeRequestDraft(change="move", hours_before=2.0, …))` with `write=None`: the appointment is never
moved, even on a yes (R-21).

**The behaviour**, exactly as `docs/design/contracts/stage7/graph-tools.md` §2, §3 and §6 sign it (GRT-6, GRT-7, GRT-8):

- **`agent/specialists/specs.py`**: `RunOutcome` (what the runner hands a builder; never leaves the run), `SpecialistSpec`
  (`kind`, `tool_kinds`, `report_model`, `render`, `build_result`) and `SPECS`, one spec per kind: knowledge
  `{kb_search}`, account `{account_read}`, scheduling `{slot_search, book, move, cancel, change_request}`; report models
  `KnowledgeReport`, `AccountReport`, `SchedulingReport` (DO-4 §5). Each `build_result` folds `RunOutcome.captured` (from
  `ToolResult.captured`, in order) into `KnowledgeResult`, `AccountResult` or `SchedulingResult` and **never reads model
  text for a record value**; `report_facts` adds only the fields its report model names. Knowledge: a `KnowledgePoint`
  must cite a passage returned this run; zero valid points (or a below-floor search) → `status="no_current_source"`, no
  points, the passages kept for the record; SP-1's top-3 fallback is not carried over (GRT-7, R-13).
  `KnowledgeResult.quick_checks` keeps DO-4's meaning: ids of `faq/troubleshooting_before_you_call.md` passages returned
  this run. Account: invoices, membership and warranty from `AccountCapture`; `staff_notes` copied for the brief and the
  case view only (HP-3); a `not_verified` refusal → `status="not_verified"`. Scheduling: windows, `WriteResult`,
  `ChangeRequestDraft` and the refusal code from `SchedulingCapture` decide the status (`windows_shown`, `written`,
  `staff_change_request`, `not_verified`, and the refusals by the same names); `SchedulingResult.quick_checks` carries
  the offered troubleshooting passages (graph-tools §3, §6). Every builder copies `tools`, `calls`, `brake` and `failure`
  from `RunOutcome`. No `if spec.kind == …` in the runner: `spec = specs[task.task.specialist]` is a lookup (DO-3 §4.5).
- **`agent/specialists/runner.py`**: `SpecialistRunner(*, gateway, transcript, dispatcher, specs, brakes, trace)` (`trace:
  TraceSink`, models.md §4; added by R-G-17, graph-tools §2) with
  `run(task, scope, ctx) -> SpecialistResult` (it replaces DO-4 §5's free `run_specialist`), and the pure
  `scope_for(state, ctx) -> ToolCallScope` (`customer_id` only when `state.identity.status == "verified"`, else None;
  `shown_slot_ids` from `state.shown_slots`; `now = ctx.now`; `ids = ctx.ids`; `message_id = state.turn_input.message_id`,
  graph-core §2). `run` never raises and follows DO-4 §5's runner rules:
  - tools sent = `dispatcher.schemas(spec.tool_kinds)` plus a `report_facts` schema generated from `spec.report_model`;
    `report_facts` is handled by the runner and never dispatched;
  - `transcript.start(user)` builds a fresh `ProviderMessages` from the SONNET-profile text `SpecialistTask` already holds
    (the runner adds no value of its own); the list lives for this run only and is never logged, traced or stored (GRT-9);
  - each model step is `gateway.tool_step(Role.SPECIALIST, ToolStepRequest(...), ctx)`; its `calls` go to
    `result.calls`; its `halt` (`DEADLINE`, `BRAKE_SONNET_CALLS`, `PROVIDER_SPEND_CAP`, or any other) becomes `brake` and
    stops the run; its `failure` becomes `failure` and stops the run;
  - the step's tool calls go to `dispatcher.dispatch(calls, kinds=spec.tool_kinds, scope=scope)`; each `DispatchedCall`'s
    `content` is appended under its own `tool_call_id` with `transcript.append`, its `result` captured and its `record`
    kept in `tools`; dispatch writes the one `lookup_log` row per call (graph-tools §1);
  - stops at: a step with no tool call (final-answer branch), `report_facts`, a third tool round (`brakes.tool_rounds = 2`,
    `Limits.brakes`, AEA-01 → `BRAKE_TOOL_ROUNDS`), an identical call (same name and canonical args →
    `BRAKE_IDENTICAL_CALL`, not dispatched again), a gateway halt or a failure;
  - quick checks (R-44, GRT-8): when `task.offer_quick_checks` is True, before the loop it dispatches one code-built
    `ToolCall(id="qc-<turn_id>", name="kb_search", args={"query": task.customer_text[:300]})` with `kinds={kb_search}`;
    it is not a model tool round and does not count against `brakes.tool_rounds`; only passages from
    `faq/troubleshooting_before_you_call.md` go to `RunOutcome.quick_checks`; nothing is offered if none clears the floor;
  - tool spans (R-G-17, graph-tools §2): after every dispatch (model rounds and the quick-check call), one
    `trace.node(ctx.span, name, record.elapsed_ms, record.outcome)` per `DispatchedCall`, `name` = `"tool:" +
    record.name` when `record.kind` is not None, else `"tool:unknown"` (the name comes from the registry; a model-supplied
    unknown name never becomes a span name); no arguments and no result text. The dispatcher (AEA-22) stays trace-free;
  - it emits no signal and writes no check event: `brake` and `failure` travel on the result and AEA-39 emits
    `specialist_failed` / `brake_fired` (graph-nodes §4, GRN-4).
- **`agent/prompts/specialists.py`**: each role's wording as `(system_prefix, system_dynamic, user)` returned by the spec's
  `render(task, ctx)`: a stable `system_prefix` (cache-controlled) and a per-run `system_dynamic` (today's date from
  `ctx.now`, never a fixed string or the server clock, R-3). Start from SP-1's measured wording
  (`docs/plans/fanout/2026-10-20-sp1/build.md` step 8) and keep its rules: report only what tools returned; never guess;
  the account specialist never judges a charge (INV-204411's $144 is explained as billed, R-17); no firm repair prices
  ("the technician confirms pricing on site", R-13); never ask for or accept card numbers (R-13); scheduling never calls a
  move or cancel when the late-change fee applies (R-21, R-22); state the 12-month minimum (SP-1 §4).

Produces `SpecialistRunner` (wired as `GraphDeps.specialists` by AEA-51 with the same SPECIALIST adapter object as the
gateway's tool map, graph-tools §2), `scope_for` and `SPECS` for the act node (AEA-39), and `SpecialistResult` for the facts
node (AEA-38) and `decide_escalation` (AEA-14, rules 3 and 6).

### Source

- `docs/design/contracts/stage7/graph-tools.md` §1 (`ToolDispatcher.schemas/dispatch`, `DispatchedCall`, `ToolCallRecord`,
  `ToolKind`, `ToolErrorCode`), §2 (`ProviderMessages`, `ToolTranscript`, `RunOutcome`, `SpecialistSpec`, `SPECS`,
  `SpecialistRunner`, `scope_for`, `SpecialistTask.offer_quick_checks`), §3 (capture shapes, `StaffNote`,
  `SchedulingResult.quick_checks`), §6 (quick checks), C-1, C-7, C-8, C-9; `stage7/graph-nodes.md` §4 (signals; the
  runner emits none), §9.5 (how the act node calls `run`); `stage7/graph-core.md` §2 (`TurnInput.message_id`), §4
  (`GraphDeps.specialists`); `stage7/data.md` §1 (SONNET placeholders), §4 (`KbSearchArgs`); DO-4 §5 (specialist contracts,
  runner rules, report models), §11 (`HaltReason`, failure rows *Provider rate limit or 5xx/529*, *A brake fired*), §12
  (`ToolCallingModel`, `ToolStepRequest`, `ModelGateway.tool_step`, `RoleSpec` specialist cap 8 s), §16.
- Decisions: `docs/plans/7b-decisions/graph-tools.md` GRT-1, GRT-6, GRT-7, GRT-8, GRT-9; `graph-nodes.md` GRN-4;
  `graph-core.md` GRC-10; `residuals-graph.md` R-G-17 (tool spans from the runner).
- DO-3 §3 (`agent/specialists/{specs,runner}.py`, `agent/prompts/specialists.py`), §4.5 (specialists as data), §5.3
  (`specialist_results` is written by the act node), §6 S-12, S-13, S-14.
- DO-2 `system-design.md` §A.1 (specialist rows; brakes: 3 tasks, 2 tool rounds, 6 Sonnet calls), §A.2, §A.3 ("Each model
  sees only its slice"), §A.6, §8.2 *Specialist* row; SDQ-7 = A (keep SP-1's call shape).
- PRD R-13, R-17, R-18–R-23, R-41, R-44, R-45; HP-3; SP-1 §4.
- Rule `context-management-multi-turn.md` (rules 1, 3, 4).
- Router rows: area map A7b Act; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Build a retrieval pipeline over the knowledge base that lets the agent answer the top 3 call
  drivers accurately" and "Handle the full flow: the caller asks for an appointment, the agent checks availability, and
  either confirms the booking or offers alternatives"; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] A specialist makes at most `brakes.tool_rounds` (2) tool rounds: a scripted tool model asking for a third round ends the run with `brake = HaltReason.BRAKE_TOOL_ROUNDS` and no third dispatch — verify: `tests/unit/agent/specialists/test_runner.py::test_two_tool_rounds_brake` (AEA-11 `FakeToolModel` behind a gateway double; dispatcher double) — evidence: 2 dispatch calls; `result.brake == "brake_tool_rounds"`.
- [ ] AC-2 [invariant] Loop exits: an identical call (same name and canonical args) stops the run with `BRAKE_IDENTICAL_CALL` and is dispatched once; a step with no tool call ends the run through the final-answer branch; `report_facts` ends the run and is never passed to the dispatcher — verify: `test_runner.py::test_identical_call_breaker`, `::test_final_answer_branch`, `::test_report_facts_ends_loop_not_dispatched` — evidence: three passing tests; dispatch call counts as stated.
- [ ] AC-3 [invariant] Every dispatched call's `content` is appended with its own `tool_call_id` through `transcript.append`, and each run starts a fresh list with `transcript.start` holding only that task's text (no earlier run's messages) — verify: `test_runner.py::test_results_keep_tool_call_ids`, `::test_message_list_is_per_run` — evidence: ids match one-to-one; the second run's `start` receives only its own task text.
- [ ] AC-4 [failure/refusal] `run` never raises: a gateway double returning `failure` (kind `server`, after its one retry) gives `status="failed"` with `failure` set and no further step; a gateway `halt` of `DEADLINE`, `BRAKE_SONNET_CALLS` or `PROVIDER_SPEND_CAP` stops the run with that reason in `brake`; a dispatcher double returning a `tool_failed` `DispatchedCall` reaches the model as that content and the run goes on — verify: `test_runner.py::test_never_raises_on_failure`, `::test_gateway_halt_stops_run` (parametrised over the three halts), `::test_tool_failed_content_reaches_model` — evidence: no exception escapes; result fields as stated.
- [ ] AC-5 [invariant] Results come from `ToolResult.captured`, never from `report_facts`: a report naming an amount not in the captured invoice or a slot never shown changes nothing in the result; invoice lines, windows and writes equal the captured records exactly — verify: `tests/unit/agent/specialists/test_specs.py::test_results_from_captured_not_report` — evidence: result fields equal the captures.
- [ ] AC-6 [failure/refusal] GRT-7: a knowledge report with one point citing a passage not returned this run, while 3 passages were returned, gives `status="no_current_source"` with no points and the 3 passages kept; a below-floor search (`RetrievalResult.below_floor`) gives the same status with no points (R-13) — verify: `test_specs.py::test_zero_valid_points_no_current_source` and `::test_below_floor_no_current_source` — evidence: status, empty points, passages as stated.
- [ ] AC-7 [invariant] WP-4: given a dispatcher double whose `move` call returns a `fee_bearing` refusal and a `change_request` call capturing a `ChangeRequestDraft`, the scheduling result is `status="staff_change_request"` with that draft and `write=None`; WP-4F (visit more than 24 h away, slot picked from `shown_slots`) returns `status="written"` with the captured `WriteResult` — verify: `test_specs.py::test_wp4_fee_bearing_becomes_change_request`, `::test_wp4f_fee_free_move_written` — evidence: two passing tests.
- [ ] AC-8 [invariant] Quick checks (GRT-8): `offer_quick_checks=True` makes exactly one dispatched `kb_search` with id `qc-<turn_id>` and `kinds={kb_search}` before the first model step, not counted as a tool round (two model tool rounds still allowed after it), and only `faq/troubleshooting_before_you_call.md` passages reach `SchedulingResult.quick_checks`; `False` makes none; `KnowledgeResult.quick_checks` lists only troubleshooting passage ids returned this run and is empty when none were — verify: `test_runner.py::test_quick_checks_offer` and `test_specs.py::test_knowledge_quick_checks_only_from_troubleshooting` — evidence: dispatch log and result fields as stated.
- [ ] AC-9 [invariant] `scope_for`: `customer_id` is the state's customer only when `identity.status == "verified"` (None for `located`, `code_sent`, `not_verified`, `locked`); `shown_slot_ids` equals the shown slots' ids; `now`, `ids` and `message_id` come from `ctx` and `state.turn_input.message_id` — verify: `test_runner.py::test_scope_for` — evidence: one row per identity status; field values as stated.
- [ ] AC-10 [negative] Nothing the runner holds beyond the task text and each call's `content` reaches a model request, a log or the result: a captured `StaffNote` text ("after-hours line $144 vs schedule $149" on WP-2's INV-204411), the scope's `customer_id` and the `ProviderMessages` payload are absent from every `ToolStepRequest` the recording gateway double receives and from every captured log record; the serialised `SpecialistResult` holds no `ProviderMessages`, no `for_model` JSON and no `ChatLine` — verify: `test_runner.py::test_no_staff_notes_transcript_or_scope_leak` (caplog) — evidence: each value absent; the staff note present only in `AccountResult.staff_notes`.
- [ ] AC-11 [negative] Rendered specialist requests (`system_prefix` + `system_dynamic` + user text) for a task whose stored text carries a prior code turn (`[code entered]`), a card turn (`[card number removed]`) and a SONNET phone hint (`[phone ending 02]`, data.md §1) contain no 6-digit run, no 13–19-digit run and no full phone number, and `system_dynamic` holds `ctx.now`'s date, not the server clock — verify: `tests/unit/agent/prompts/test_specialist_prompts.py::test_requests_carry_no_secret_values` (the synthetic code and card number are generated in the test and appear only redacted) — evidence: none of the raw values appears; the date equals the demo clock's.
- [ ] AC-12 [invariant] Turn-2+ full prompt (context-management rule 3): a recording fake tool model drives the runner for the knowledge task on turns 1, 2 and 5 of a WP-1 conversation; the stable `system_prefix` is byte-identical and complete (role, never-talk-to-the-customer line, report-only-what-tools-returned, no-prices and no-card rules) on each, and only `system_dynamic` and the user text differ — verify: `tests/unit/agent/prompts/test_specialist_prompt_turns.py::test_stable_prefix_turns_1_2_5` — evidence: three captured requests; prefix hashes equal.
- [ ] AC-13 [capture] Every dispatched call (every tool call except `report_facts`, plus the quick-check call) reaches the dispatcher exactly once, so dispatch writes exactly one `lookup_log` row per call, and the result carries one `ToolCallRecord` per dispatched call in `tools` and every gateway attempt's `CallRecord` in `calls` — verify: `test_runner.py::test_lookup_and_call_records` — evidence: dispatch calls == tool calls; `len(result.tools)` == dispatch calls; `len(result.calls)` == gateway attempts. (The real-entry-point capture is CAP-1 in AEA-51.)
- [ ] AC-14 [capture] Tool spans (R-G-17, graph-tools §2): with AEA-11's `InMemoryTraceSink` as `trace`, a run with two model tool rounds plus the quick-check call records one node span per dispatched call (quick check included), named `tool:<registry name>` with the record's `elapsed_ms` and outcome as status; a call to a name the registry does not know is recorded as `tool:unknown`, never under the model-supplied name; no span holds tool arguments or result text, and `report_facts` gets no span — verify: `tests/unit/agent/specialists/test_runner.py::test_tool_spans` — evidence: span count == dispatched calls; names, timings and statuses equal the `ToolCallRecord`s; the model-supplied name and a sentinel argument value absent from every span.
- [ ] AC-15 [journey] Extends J-2 (slice plan §0a journey map; backend-amendments §3): the billing and warranty specialists stay inside their brakes and each answer shows the invoice or warranty source it used; asserting what the user sees and what is stored, in `tests/journeys/j2/test_aea_35.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j2/test_aea_35.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-35.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-16 [regression/context] Docs updated in the same change — verify: `git diff --name-only` — evidence: `.claude/reference/area-map.md` A7b row (`agent/specialists/{specs,runner}.py`, `agent/prompts/specialists.py` planned → actual with the commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 rows for the three files status planned → built, all three in the diff with only this ticket's rows changed.

### Observability

- Responsibilities (WF-1): the specialist's `model_call` spans and `spend_ledger` rows are written by the gateway (AEA-20)
  on every attempt; this ticket passes every `CallRecord` through to `result.calls`, routes every tool call (and the
  quick-check call) through dispatch (AEA-22) so DO-6's *Missing instrumentation* check "a tool call left no lookup-log
  row" holds, keeps one `ToolCallRecord` per call in `result.tools` (`TurnRecord.tool_calls` and GRC-13's
  `tool_failures` read them), and reports a brake in `result.brake` and a failure in `result.failure` so the act node
  (AEA-39) emits `specialist_failed` / `brake_fired` and writes the `brake` check event (GRN-4). The runner emits one
  `tool:<name>` node span per dispatched call, quick check included (DO-6 rule 18; R-G-17, AC-14). The runner itself logs
  no message text and no `ProviderMessages` (AC-10).
- Capture evidence: AC-13 and AC-14 at component level; CAP-1 (AEA-51) drives the real CON-2 entry point and finds the nested tool
  and model spans and the `lookup_log` rows for the WP-2 invoice read.

### Evaluation

- Checks: E-1 trajectory items (which specialist and which tool, in order) for WP-1, WP-2, WP-3, WP-4, WP-4F and WP-8, and
  E-7 booking validity (every write meets zone, service, status and member-slot rules), kept passing when AEA-51 runs the
  compiled graph with fake models; the scored runs are Stage 9's.
- Expected-answer authority (DO-5 *Expected-answer authority*): the current KB file named by PRD §4.3a for knowledge
  answers; the issued database, invoices explained as billed (R-17; WP-2 ✓ Innocent 2026-10-20) for account reads;
  `SCHEMA.md` rules for bookings (R-18, R-19); Innocent's Stage 3 rule for fee-bearing changes (R-21, R-22; WP-4).

### Metrics

- References: M-7 (answers citing an excluded file: passage ids in `lookup_log`), M-8 (wrong-answer rate), M-9
  (booking-rule validity), M-21 (no fee-bearing move or cancel by the AI), M-24 (degraded turns from model or tool
  failure), M-25 (cost per conversation).
- Acceptance conditions: each stays computable from the records: every cited passage is in `lookup_log` (AC-13), every
  model attempt has a `CallRecord` for `spend_ledger`, and a failure or brake is on the result for
  `turn.degrade_reason`. No target is set or changed here.

### Blocked by

AEA-11 (scripted fakes, `InMemoryTraceSink`), AEA-20 (gateway), AEA-22 (dispatcher) — slice plan row. Domain types and the
`TraceSink` port (AEA-02, `ports/runtime.py`, models.md §4) and `Limits.brakes` (AEA-01) are earlier waves; R-G-17 adds no
new edge. The `[journey]` AC-15's integrated level only (not this ticket's merge): AEA-57 (harness) and AEA-51 (lands
J-2, wave 3).

### Agent handoff

- Area / owner: A7b Act, specialists part; owns `src/meridian/agent/specialists/{specs,runner}.py`,
  `src/meridian/agent/prompts/specialists.py` and their tests under `tests/unit/agent/specialists/` and
  `tests/unit/agent/prompts/`.
- Contracts and shared surfaces: consumes `ModelGateway.tool_step` (AEA-20), `ToolTranscript` / `ProviderMessages`
  (AEA-02; the adapter is AEA-17's), `ToolDispatcher` (AEA-22) and, through dispatch, the tools from AEA-27
  (`account_tools`), AEA-28 (`scheduling_tools`) and AEA-33 (`knowledge_tools`), all as doubles honouring graph-tools §1,
  §2 and DO-4 §12; `Limits.brakes` (AEA-01); domain types, `SpecialistTask.offer_quick_checks` and
  `SchedulingResult.quick_checks` (AEA-02); `TraceSink.node` (AEA-02, models.md §4; tested with AEA-11's
  `InMemoryTraceSink`; AEA-51 passes the container's sink, R-G-17). Produces `SpecialistRunner`, `scope_for` and `SPECS`
  for AEA-39 and AEA-51,
  and `SpecialistResult` for AEA-38 and AEA-14. §5.3 state keys: none written here (the act node writes
  `specialist_results`). Must not edit `agent/gateway.py`, `agent/tools/*`, `agent/nodes/*`, `domain/*`, `ports/*`,
  `policy/limits.py`.
- Scope boundary / refusal: no tool executors, no write rules (fee, zone, slot checks are AEA-13/AEA-28's), no escalation
  decision, no signals or check events, no customer-facing text, no card ids, no `SpecialistTask` assembly and no
  decision to offer quick checks (AEA-39 sets `offer_quick_checks`, graph-tools §6).
- Evidence level (`.claude/rules/integrated-journeys.md` §4): the runner and spec tests are `mock-tested`; the J-2
  journey step (AC-15) records `mock-tested` and `Blocked by: AEA-57, AEA-51` until both merge.
- Wave and gates: wave 2; no gate.
- Lane: build-loop — it changes source and tests (`ticket-lanes.md`).
- Risk: None per the slice plan. Reviewer note: untrusted customer text reaches a tool-calling model here (already
  SONNET-redacted, and every tool argument is validated and scope-checked by dispatch); if `code-review-agent` judges this
  a security surface, the orchestrator adds `risk::security` (`build-loop-test-scope.md`).
- Entry points added or changed: None
