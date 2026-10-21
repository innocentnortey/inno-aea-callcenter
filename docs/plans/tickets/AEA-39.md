## [AEA-39] graph: act node (fan-out, escalation, handoff)

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

> **US-14:** "As a **homeowner** whose request needs a person, I need a reference number, the exact promise (who gets back
> to me and by when), and a choice of email or phone and a time window, so that I know what happens next and never repeat
> my story." (Also US-12: "when it's inside 24 hours, to explain the $49 fee, record my request and tell me the original
> visit stands until a person confirms".)

**Example pair (WP-4).** MHC-57204, tune-up today 12:00–16:00, clock Fri 2026-10-16 10:00, nobody online. The scheduling
specialist returns `status="staff_change_request"` with a `ChangeRequestDraft`. Expected output: the escalation node's
`decide_escalation` gives `outcome="escalate"`, `reason="fee_bearing_change"`, priority **P2**, `rule_id="R21.fee_bearing"`;
the handoff node calls `deps.handoff.open(HandoffRequest(trigger="escalation", reason=fee_bearing_change, priority=P2,
change_request=…), ctx)` and writes the `HandoffResult`. Inside the service (AEA-29), the case's internal due is the window
start, 12:00 today, while the customer promise is `R26.unstaffed`, due Monday 19:00, with the can't-guarantee line
(window start < promise due) and the phone-support line (phone support open Friday 10:00) (cases.md §3.2;
`alert = "supervisor_now"`). The appointment row is untouched; no text comes from a model.

**Second pair (WP-7, WP-8).** "I want a full refund on the repair. It didn't fix anything and I had to call another
company." → policy word `refund` → escalate, **P3**, promise row `R26.refund` ("A representative will get to your refund
request within 2 business days.", due Tuesday 19:00, plus "I can't promise an outcome."). WP-8 "I want to cancel my
Comfort Club membership." → planner `membership_cancel` → escalate, `rule_id="D4.membership_cancel"`, **P3** because the
renewal date (2026-11-03) is after the promise due (CAS-14; worked-pairs WP-8 step 4).

**The behaviour.** `agent/nodes/act.py` replaces AEA-21's stubs with three node functions (graph-nodes §9.5; update
types §9.1):

- **`run_specialist(payload: SpecialistSend, runtime, *, deps) -> SpecialistUpdate`** (`specialist_results`,
  `check_events`, `halt`): one call per `Send` that AEA-21's `route_act_plan` builds (graph-core §11; one per
  `PlannedTask`, or the open task a card choice resumes), run in parallel; results are appended to `specialist_results` by
  its `operator.add` reducer (DO-3 §5.2). The `Send` payload is `SpecialistSend(planned: PlannedTask, state)` (graph-nodes
  §9.1, R-G-12); `route_act_plan` only fans out. `run_specialist` builds the task with the pure
  `build_specialist_task(planned, state, ctx, *, scheduling, limits)` in `agent/nodes/act.py` (graph-nodes §9.5, R-G-12),
  then calls `deps.specialists.run(task, scope_for(payload["state"], ctx), ctx)` (`SpecialistRunner`, graph-tools §2,
  GRT-6, which replaces DO-4 §5's `run_specialist(spec, task, ctx)`). A verified scheduling task's slice inputs come from
  `deps.scheduling.slice_inputs(customer_id)` (`SchedulingService`, cases.md §4, R-G-19; zone, member and appointments in
  one read, structural double in tests until AEA-28 merges), and that read closes before the run (DO-3 §2.3 rule 1); any
  other task passes `scheduling=None`.
  `scope_for` binds the verified customer only when identity is `verified`, the shown slot ids, `ctx.now` and
  `turn_input.message_id`. Each `SpecialistTask` carries `customer_text` and `task_messages` in the SONNET profile and
  only the slice that specialist needs (R-45): no chat window, no `customer_id` in `SchedulingSlice` (DO-4 §5);
  `offer_quick_checks=True` only under graph-tools §6's three conditions (scheduling `BOOK_NEW` with no
  `resumes_task_id`; service type `hvac_repair`, `plumbing` or unknown; gate `FREE_TEXT` and no danger raise). After the
  run: a `result.brake` in `BRAKE_HALTS` writes `Halt(reason, node)`, a `CheckEvent.from_halt` `brake` event and a
  `brake_fired` signal; a `DEADLINE` or `PROVIDER_SPEND_CAP` brake writes the halt only (no event, no node signal); a
  `failed` result with no brake emits `specialist_failed` (`cause` = `failure.kind`, or `tool_error` when `failure` is
  None) (graph-nodes §1, §4). The runner itself emits nothing. No unit of work is open while a specialist runs (DO-3 §2.3
  rule 1).
- **`escalation(state, runtime, *, deps) -> EscalationUpdate`** (`escalation`): builds `EscalationInputs` (gate, plan,
  results, counters, identity, halt, `models_disabled` from `deps.ledger.models_disabled()` (`GraphDeps.ledger:
  ModelsStatus`, graph-core §4, R-G-13), and `now = ctx.now` (cases.md §3.4, R-G-15)) and calls the pure `decide_escalation` (`policy/escalation.py`,
  AEA-14), first match wins (DO-4 §6 as revised by cases.md §3.4): person → policy word (D4) → `staff_change_request`
  (`fee_bearing_change`, P2, R-21/R-22) → plan `handoff_request` (D4 rows incl. `D4.membership_cancel`, `D4.unsupported`
  P4, `D4.late_technician` P2) → identity `not_verified` or `locked` with a private task (P3, R-16) → rule 6: a brake
  `halt`, **any** specialist `failed`, `models_disabled`, or `plan.planner_failed and not plan.tasks` → `ai_failure` P3,
  `degraded=True`, rule ids `AI.halt` / `AI.specialist_failed` / `AI.models_disabled` / `AI.planner_failed` → rule 7:
  `failed_answers ≥ 2`, `corrections ≥ 2` or `timeouts ≥ 2` → `offer` (`OD6.two_misses` / `OD6.two_timeouts`) → none. It
  receives brake halts from `halt_route` (graph-core §5) and both-planners-failed plans from router edge 1 (§11).
- **`handoff(state, runtime, *, deps) -> HandoffNodeUpdate`** (`handoff`, `halt`): for `outcome="escalate"` and for the
  `person` gate (the node builds `HandoffRequest(reason=customer_requested_person, priority=priority_for(…) = P3,
  rule_id="R2.person", trigger="gate")` on the **first** request, R-2; cases.md §3.4, graph-nodes §9.5, R-G-14) calls `deps.handoff.open(request, ctx)` once per turn, idempotent on the turn's `ActionKey` (graph-nodes §9.5). One open
  case per thread: a second reason returns the same reference with `created=False` (CON-4 `already_open`). The node never
  writes promise text, priority or due time itself: priority comes from `decide_escalation` / `policy/handoff.py`, the
  promise from `promise_for` inside the service. `offer` and `none` open nothing.

### Source

- DO-4 §2 (`GraphDeps`), §5 (`SpecialistTask`, slices, `ToolCallScope`), §6 (`EscalationInputs`, `EscalationDecision`,
  rule order), §7 (`HandoffReason`, `Priority`, `Promise`, `HandoffRequest`, `HandoffResult`, `HandoffService.open`: one
  unit of work, case + promise + action + event together), §11 (*A brake fired*, specialist failure rows), §16 (addenda
  win).
- `docs/design/contracts/stage7/graph-tools.md` §2 (`SpecialistRunner.run`, `scope_for`, `SpecialistTask.offer_quick_checks`),
  §6 (the quick-check rule for the act node).
- `docs/design/contracts/stage7/graph-nodes.md` §1 (`brake` events), §4 (`specialist_failed`, `brake_fired`; the runner
  emits nothing), §9.1 (`SpecialistUpdate`, `EscalationUpdate`, `HandoffNodeUpdate`, `SpecialistSend(planned, state)`),
  §9.5 (node signatures; `build_specialist_task`).
- `docs/design/contracts/stage7/graph-core.md` §2 (`TurnInput.message_id`), §4 (`GraphDeps.specialists`, `.handoff`,
  `.scheduling`, `.ledger: ModelsStatus`, `timed_node`), §5 (`BRAKE_HALTS`, `halt_route`), §8 (`FailureCounters`), §11
  (`route_act_plan`, edge 1).
- `docs/design/contracts/stage7/cases.md` §3.2 (promise rows, `case_due_at`), §3.3 (`priority_for`, CAS-14), §3.4 (rule
  table rows 4, 6, 7; residual notes: `EscalationInputs.now`, rule ids `R2.person` / `R24.<reason>` /
  `R16.identity_unverified`), §4 (`SchedulingService.slice_inputs`), §5 (`HandoffService.open`), closing rows A-5, A-6;
  `docs/design/contracts/stage7/graph-tools.md` §3 (`SchedulingSliceInputs`, `AppointmentView`).
- Residual rulings `docs/plans/7b-decisions/residuals-graph.md` R-G-12, R-G-13, R-G-14, R-G-15, R-G-19.
- Decision ledgers: `docs/plans/7b-decisions/graph-tools.md` GRT-6, GRT-8; `docs/plans/7b-decisions/graph-nodes.md` GRN-2,
  GRN-4, GRN-11; `docs/plans/7b-decisions/graph-core.md` GRC-7, GRC-15, GRC-18; `docs/plans/7b-decisions/cases.md` CAS-12,
  CAS-13, CAS-14, CAS-15, CAS-16.
- DO-3 §2.3 rule 1, §5.2–§5.4, §7 rows R-21, R-22, R-24, R-25, R-26. DO-2 `system-design.md` §A.1, §8.2 (*Handoff* row).
- PRD R-2, R-16, R-21, R-22, R-24, R-25, R-26, R-41, R-44; HP-3, HP-4; WP-4 (revised at Stage 3), WP-7, WP-8
  (`docs/data/worked-pairs.md`); consolidated direction §9.3, §9.4 (D4).
- Slice plan §0a (Amendment 1, journeys J-3, J-4) and rule `.claude/rules/integrated-journeys.md` §3–§4.
- Slice plan row AEA-39; area-map row A7b (Act); ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Escalation must be graceful: the agent recognizes it is out of scope, tells the caller what is
  happening, and hands off with enough context that a human can pick up without starting over"; touches nothing out of
  scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Three `Send` payloads run three `run_specialist` calls in one superstep and all three results are in `specialist_results` in `PlannedTask.order` (account, scheduling, knowledge); each call passes `scope_for(payload["state"], ctx)` to `deps.specialists.run` — verify: `tests/unit/agent/nodes/test_act.py::test_fanout_three_tasks_parallel` — evidence: runner double called 3 times in one step with the expected scopes; 3 results appended.
- [ ] AC-2 [invariant] Each `SpecialistTask` carries only its slice: the scheduling task has no `customer_id` and no chat window; the knowledge task carries `customer_text` and `task_messages` only; `scope_for` gives `customer_id=None` when identity is not `verified`; `offer_quick_checks` is true only for a new `BOOK_NEW` scheduling task of type `hvac_repair`, `plumbing` or unknown on a `FREE_TEXT` turn with no danger raise (graph-tools §6), false on the burning-"no" booking (gate `BURNING_ANSWER`) — verify: `test_act.py::test_specialist_task_slices_and_quick_check_offer` — evidence: serialised tasks and scopes as stated; the offer table passes.
- [ ] AC-3 [invariant] WP-4: a `staff_change_request` result → `escalate`, `fee_bearing_change`, P2, `rule_id="R21.fee_bearing"`; the handoff double receives one `HandoffRequest` with the `ChangeRequestDraft`; no write request reaches scheduling — verify: `test_act.py::test_wp4_fee_bearing_escalates_p2` — evidence: decision and request fields as stated.
- [ ] AC-4 [invariant] WP-7 (policy word `refund`) → P3 `refund`; WP-8 (plan `handoff_request="membership_cancel"`, renewal 2026-11-03 after the promise due) → `D4.membership_cancel`, P3; the `EscalationInputs` the node passes carry `now == ctx.now` (R-G-15) — verify: `test_act.py::test_wp7_refund_p3`, `::test_wp8_membership_cancel_d4` — evidence: decisions as stated; the recorded inputs' `now` equals the context's.
- [ ] AC-5 [invariant] The `person` gate reaches the handoff node on the first request with `customer_requested_person`, P3, `rule_id == "R2.person"`, `trigger == "gate"` (cases.md §3.4, R-G-14), and no specialist or gateway call (R-2) — verify: `test_act.py::test_person_gate_first_ask` — evidence: 1 handoff call with those four fields, 0 runner calls, 0 gateway calls.
- [ ] AC-6 [failure/refusal] Rule 6 (cases.md §3.4): a brake halt, **one** `failed` specialist result, `models_disabled`, or a plan with `planner_failed=True` and no tasks each give `escalate`, `ai_failure`, P3, `degraded=True` with rule ids `AI.halt`, `AI.specialist_failed`, `AI.models_disabled`, `AI.planner_failed`, and a handoff request (PRD §5 *Reliability*: never a dead end) — verify: `test_act.py::test_rule6_degraded_handoff` (one case per trigger) — evidence: decision fields as stated; one handoff request per case.
- [ ] AC-7 [failure/refusal] Brakes and failures from the runner (graph-nodes §1, §4): a result with `brake=BRAKE_TOOL_ROUNDS` writes `Halt(reason=BRAKE_TOOL_ROUNDS, node="run_specialist")`, one `brake` check event and one `brake_fired` signal; `brake=DEADLINE` writes the halt with no event and no signal; a `failed` result with no brake emits one `specialist_failed` signal with `cause` = its failure kind, or `tool_error` when `failure` is None — verify: `test_act.py::test_brakes_and_failures_emit_events_and_signals` — evidence: halts, events and signals as stated.
- [ ] AC-8 [failure/refusal] Identity `not_verified` or `locked` with a private task open → `identity_unverified`, P3; the state written contains no account data (R-16) — verify: `test_act.py::test_not_verified_escalates_reveals_nothing` — evidence: decision as stated; no invoice, membership or appointment values in the returned keys.
- [ ] AC-9 [invariant] Rule 7: `failed_answers = 2`, `corrections = 2` or `timeouts = 2` with no earlier rule → `outcome="offer"` (`OD6.two_misses` / `OD6.two_timeouts`) and no handoff call — verify: `test_act.py::test_two_misses_or_timeouts_offer` — evidence: rule ids as stated; 0 handoff calls.
- [ ] AC-10 [invariant] A second escalation in a thread that already has an open case writes the service's `created=False` result with the same reference; the node opens nothing else, and a repeat of the same turn calls `open` with the same `ActionKey` — verify: `test_act.py::test_second_handoff_same_reference` — evidence: one reference across both turns; identical keys on the repeat.
- [ ] AC-11 [negative] No model text reaches a handoff: every `HandoffRequest` field comes from code (gate, decision, identity, captured change request), and the node writes no promise text, due time or reference; no `signal` record or check event holds specialist report text — verify: `test_act.py::test_handoff_request_has_no_model_text` — evidence: a specialist report containing "we'll refund you" and a made-up reference never appears in the request, in `handoff`, in the events or in the `meridian.signal` log capture.
- [ ] AC-12 [invariant] No transaction is open across a specialist run (DO-3 §2.3 rule 1) — verify: `test_act.py::test_no_uow_during_specialists` (a UoW double that fails if entered while the runner double is running) and the review grep `grep -n "uow(" src/meridian/agent/nodes/act.py` — evidence: test passes; grep shows no `uow(` block around a runner call.
- [ ] AC-13 [invariant] Key ownership (graph-nodes §9.1): `run_specialist` returns only `SpecialistUpdate` keys, `escalation` only `EscalationUpdate`, `handoff` only `HandoffNodeUpdate`; the project's type check (the checker AEA-01 chose) passes on `agent/nodes/act.py` — verify: `test_act.py::test_act_nodes_write_only_own_keys` and the type-check command — evidence: returned key sets as stated; type check clean.
- [ ] AC-14 [capture] The decision leaves what the turn record needs: `escalation.rule_id`, `reason`, `priority` and `degraded`, and `specialist_results` with each result's `kind`, so AEA-21's `turn_trace` sets `outcome` (`handed_off` or `degraded_handoff`), `degrade_reason` and `specialists_run` (graph-core §2); every `escalate` outcome produced exactly one `HandoffService.open` call (DO-6 check "a handoff left no case" expects 0) — verify: `test_act.py::test_escalation_record_fields_and_case_per_escalate` — evidence: fields present; escalate count == handoff calls.
- [ ] AC-15 [journey] Extends J-3 and J-4 (slice plan §0a journey map): J-3, a booking turn whose scheduling specialist writes, then "Yes, please." with no new write; J-4, WP-4 through CON-2 with the appointment row unchanged, a P2 `fee_bearing_change` case row and the policy-table promise on screen; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_39.py` and `tests/journeys/j4/test_aea_39.py` with the scripted model adapter — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_39.py tests/journeys/j4/test_aea_39.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57's harness and AEA-51's J-3/J-4 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-39.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-16 [invariant] `build_specialist_task` is pure (graph-nodes §9.5, R-G-12): `customer_text` and `task_messages` are SONNET-masked; each specialist gets only its DO-4 §5 slice; no `customer_id` anywhere in the task; `SchedulingSlice` zone, member and appointments come from the `scheduling` argument (`deps.scheduling.slice_inputs`, R-G-19) and are `None` / `False` / `()` when it is `None` (identity not verified, or not a scheduling task); `offer_quick_checks` per graph-tools §6; the same inputs give an equal task twice and no I/O double is touched — verify: `test_act.py::test_build_specialist_task` (`tests/unit/agent/nodes/test_act.py`) — evidence: tasks as stated per case; a card-like number and a phone built in the test from parts are absent from the task; 0 calls on the UoW and gateway doubles.
- [ ] AC-17 [regression/context] Context-management rule 3 does not apply: this node renders no model prompt. In the same change: the area-map row A7b for `agent/nodes/act.py` (planned → actual + commit), the ICM progress row *Routes verified against code and tests*, DO-3 §3's `agent/nodes/act.py` row marked built — verify: `git diff --name-only` — evidence: those docs in the diff, only this ticket's rows changed.

### Observability

- Responsibilities: WF-1 (customer chat turn, its internals; DO-6 emitters "specialists, escalation check") and WF-2's
  emitter "handoff node" (the graph handoff; WF-2's CON-4/CON-5 entry is AEA-42). The `case`, `case_event`, `promise`,
  `actions(case_opened)` and `events(case_created)` rows are written by `HandoffService` (AEA-29) in one transaction; this
  ticket guarantees every `escalate` reaches it once (AC-14) and leaves `degraded`, reason and rule id in state for
  `turn.outcome` / `turn.degrade_reason` (DO-6 status values, via `TurnTrace`, graph-core §2). It emits `brake` check
  events into `check_events` (persisted by AEA-40 from `GraphOutcome.check_events`) and the `signal` LOG records
  `specialist_failed` and `brake_fired` (graph-nodes §4; web.md §10). Model and tool spans come from the gateway and the
  dispatcher; node spans from `timed_node` (AEA-21). Codes only.
- Capture evidence: AC-14 and AC-7 at component level, AC-11 for the forbidden values; CAP-1 and CAP-3 (AEA-51) drive the
  real entry points and find the case, case events and the policy-table promise.

### Evaluation

- Checks: E-1 WP-4 (appointment row untouched, P2, fee and "original stays" lines), WP-7, WP-8 hard gates; E-6 promise
  text equals the policy table; E-3/E-4 escalation recall on out-of-scope cases and false escalation on in-scope cases;
  kept passing at AEA-51.
- Expected-answer authority: the policy table (exact strings) and the D4 priority table, never the model (PRD R-24, R-26;
  OD-4; consolidated §9.4); Innocent's Stage 3 rule for fee-bearing changes (R-21, R-22) (DO-5 *Expected-answer
  authority*).

### Metrics

- References: WF-1 inherits M-1, M-3, M-4, M-6, M-7, M-8, M-9, M-14, M-16, M-17, M-18, M-19, M-20, M-21, M-22, M-23, M-24,
  M-25, M-26, M-29; WF-2 inherits M-10, M-11, M-12, M-13, M-15. **Affected here:** M-10 (promise text consistency: the
  promise comes only from the service's table), M-15 (person on the first request), M-19 (escalation recall), M-20 (false
  escalation), M-21 (no fee-bearing move or cancel by the AI), M-22 (handoffs by reason), M-24 (degraded turns: rule 6),
  M-9 (writes go only through the scheduling specialist's tools), M-23 (specialists run in parallel), M-3 and M-18 (a
  handoff ends the conversation `handed_off`, so it is never counted as abandoned). **Kept computable, not changed by this
  ticket:** M-1, M-4, M-6, M-7, M-8, M-11, M-12, M-13, M-14, M-16, M-17, M-25, M-26, M-29.
- Acceptance conditions: each escalation leaves a case row with its reason and priority, and the turn outcome is
  derivable from state (AC-14). No target set or changed here.

### Blocked by

AEA-11, AEA-14, AEA-21 (slice plan). Calls (injected): `SpecialistRunner` (AEA-35) through `GraphDeps.specialists`,
`HandoffService` (AEA-29) through `GraphDeps.handoff`, `SchedulingService.slice_inputs` (AEA-28, wave 2) through
`GraphDeps.scheduling` (R-G-19), and `ModelsStatus.models_disabled` through `GraphDeps.ledger` (the field and Protocol
are AEA-21's, R-G-13), each tested with a double honouring graph-tools §2–§3, DO-4 §7 and cases.md §4–§5. Types
`SpecialistSend(planned, state)`, `SchedulingSliceInputs` and `EscalationInputs.now` are AEA-02's (wave 0, R-G-12,
R-G-15, R-G-19). No new blocking edge: AEA-28 is a same-wave runtime collaborator (slice plan row AEA-39's collaborators
gain "scheduling (28)", the orchestrator's edit).

### Agent handoff

- Area / owner: A7b Act (`agent/nodes/act.py`).
- Contracts and shared surfaces: consumes `SpecialistRunner.run` and `scope_for` (AEA-35, double), `HandoffService.open`
  (AEA-29, double), `SchedulingService.slice_inputs` (AEA-28, double, R-G-19), `GraphDeps.ledger: ModelsStatus`
  (AEA-21, double, R-G-13), `decide_escalation` and `policy/handoff.py` `priority_for` (AEA-14), `Limits.brakes` (AEA-01),
  `redact` with `RedactionProfile.SONNET` (AEA-04), the `*Update` types, `SpecialistSend(planned, state)`,
  `SchedulingSliceInputs`, `EscalationInputs` (with `now`), `CheckEvent` builders and `SignalRecord` (AEA-02),
  `emit_signal`, `timed_node` and `route_act_plan` (AEA-21; it builds no `SpecialistTask`, R-G-12). Produces
  `build_specialist_task` (pure, in `agent/nodes/act.py`). Produces `specialist_results`, `escalation`, `handoff` and `check_events` entries for AEA-38
  (facts, brief), AEA-21 (routers, compose, `turn_trace`) and AEA-40 (turn record via `GraphOutcome`). Must not edit
  `policy/escalation.py`, `services/handoff.py`, `agent/specialists/*`, `routers.py`, `domain/*`, other node files.
- Scope boundary / refusal: no escalation rules (AEA-14), no promise, priority or due-time logic (AEA-14, AEA-29), no
  specialist internals (AEA-35), no CON-4 route (AEA-42), no safety case (AEA-36's safety node opens it).
- Awaiting Innocent: CAS-16 — built on the recommended option (A: reason `burning_ruled_out`, P2, set by AEA-14's
  `priority_for`); the burning-"no" booking reaches this node with that `handoff_request`, and this ticket passes through
  whatever `decide_escalation` returns and asserts no priority level on that path (graph-nodes §6: until he answers,
  `priority_for` raises `NotImplementedError` there). If he picks B (P1) or C (P3), only AEA-14's priority row and AEA-02's
  reason value change; this ticket does not.
- Settled (formerly needs-decision 1–3; `docs/plans/7b-decisions/residuals-graph.md`): the act node builds every
  `SpecialistTask` with `build_specialist_task` (R-G-12, AC-16); `models_disabled` comes from `deps.ledger` (R-G-13);
  the person-gate request carries `rule_id="R2.person"`, `trigger="gate"` (R-G-14, AC-5).
- Wave and gates: wave 2; no gate.
- Lane: build-loop — it changes source and tests (`ticket-lanes.md`).
- Risk: None per the slice plan.
- Entry points added or changed: None — WF-1 internals and WF-2's graph handoff only (CON-1/CON-2 are AEA-40; CON-4 is
  AEA-42).
