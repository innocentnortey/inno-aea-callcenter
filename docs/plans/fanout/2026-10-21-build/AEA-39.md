# Plan — [AEA-39] graph: act node (fan-out, escalation, handoff)

**Status:** **READY** (refresh 3). The §9.1 question is answered: Innocent chose option A on 2026-10-21 ("just do
whatever you recommend"), so `SpecialistTask`, `KnowledgeSlice` and `AccountSlice` live in `src/meridian/domain/tools.py`,
built by **AEA-35b**. Merge order before this ticket builds: **AEA-35b, then AEA-35** (`scope_for`, a real import);
step 0 checks both and stops if either is missing. Every other name this plan uses is on `main` and was checked; every
decision is made below.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/39 (spec copy:
`docs/plans/tickets/AEA-39.md`) · **Base revision:** `main` at `8a205b2` plus AEA-35b's branch `aea-35b-specialist-types`
at `68f7f19` (refresh 3; refresh 2 at `2ec19ad`; refresh 1 at `b559c75`; first written at `96096be` plus AEA-21's
then-unmerged branch `aea-21-graph-spine`) · **Lane:**
`lane::build-loop`, no `risk::security` · **Wave:** 2 · **Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21 ·
**Implementer:** `fanout-implementer` on Sonnet.

Read this whole file before writing code. Every decision is already made here (§8.1 lists them). If the code on `main`
disagrees with a name in this plan, **the code on `main` wins**: follow it and say so in your report. If a name this plan
needs is **missing** on `main`, stop and report `blocked-on` (step 0 lists the checks). Never invent a missing type.

**Refresh 3 (2026-10-21, `main` at `8a205b2`; AEA-35b at `68f7f19`).** What changed since refresh 2, and what it does to
this plan:

1. **§9.1 answered: option A.** Innocent, 2026-10-21: "just do whatever you recommend". AEA-35b (branch
   `aea-35b-specialist-types`, commit `68f7f19`, not yet on `main`; the orchestrator merges it before this ticket builds)
   adds exactly the three types to `src/meridian/domain/tools.py` with the shape this plan expected: `KnowledgeSlice` and
   `AccountSlice` carry only `kind` and construct with no arguments; `SpecialistTask(task, customer_text, task_messages,
   slice: KnowledgeSlice | AccountSlice | SchedulingSlice, offer_quick_checks=False)`. The code is copied in §4.2. It also
   adds a home note under graph-tools §2. Step 0 item 2 now checks `domain/tools.py` and reports `blocked-on AEA-35b`.
2. **AEA-35 is still unmerged** (`src/meridian/agent/specialists/` holds only `__init__.py`; ledger row `blocked`,
   NEEDS-DECISION on the same question, now answered). `scope_for` is a module-level function this node imports, so
   AEA-35 stays a real blocker. AEA-35's plan §4.6 `scope_for` body was re-read and still matches §4.2.
3. **AEA-29 merged** (`ef561fc`). `HandoffService.open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult`
   (`services/handoff.py` line 106) retries the write once and raises `CaseWriteFailed(attempts=2)`; `_alert` in
   `services/cases.py` line 101 returns `"supervisor_now"` for P0, P1 or `FEE_BEARING_CHANGE`; joining an open case returns
   `created=False` (and may raise the case's priority). The unit tests keep §6.2's `HandoffDouble`. **J-4 now runs the
   real `HandoffService` on a temp SQLite copy** (§6.3, PD-14), using AEA-29's test helpers (`tests/services/_case_fixtures.py`:
   `services`, `new_thread`, `summary_of`), so the journey checks the stored P2 case row and an unchanged appointment row.
4. **AEA-40 merged** (`f466ff7`): CON-2 `submitTurn` exists, but the graph is wired into the turn only by AEA-51. The
   journeys stay `mock-tested`; *Blocked by* is now **AEA-51** alone (AEA-34's merged `tests/journeys/j3/test_aea_34.py`
   says the same).
5. **AEA-34 and AEA-38 merged** (real `load_context` and reply nodes). `tests/graph/_spine_doubles.py` is unchanged:
   `install_doubles` still replaces all 14 node functions, so §6.2's harness is unchanged apart from a `thread` parameter
   (for the J-4 database thread).
6. Unchanged since `2ec19ad` (checked by `git diff 2ec19ad..main`): `domain/*`, `policy/*`,
   `agent/{context,routers,graph,signals}.py`, the 33-line `act.py` stub, `tests/graph/_spine_doubles.py`,
   `tests/journeys/affected.py`. Context rows: the area-map A7b row and `code-design.md` line 299
   (`… stub AEA-21 6df4f4c`) are unchanged; the last *Routes verified* row in `icm-progress.md` is now AEA-50's.
7. The build ledger row AEA-39 still reads `blocked`, NEEDS-DECISION (plan), blockers `AEA-11,AEA-14,AEA-21`; §8.3 R-3
   now asks for `AEA-35b,AEA-35` to be added.

**Refresh 2 (2026-10-21, `main` at `2ec19ad`).** One commit since refresh 1, `2ec19ad`, and it changes only
`docs/plans/fanout/2026-10-21-build/AEA-29.md` (its implementer's deviations). No source or test file this plan reads has
changed. Re-checked on `2ec19ad`:

1. `agent/nodes/act.py` is still AEA-21's 33-line stub with the three signatures of §4.4.
2. `grep -rn "^class SpecialistTask\|^class KnowledgeSlice\|^class AccountSlice" src/` still finds nothing;
   `domain/specialists.py`'s docstring still says they are "Not built here"; `domain/turn.py` line 44 still imports
   `domain/specialists.py` (the cycle in §9.1 stands). No sign-off decision, 7b ruling, ledger row or issue for the
   types follow-up exists; `stage7-signoff.md` D-4…D-15 do not cover it. The §9.1 question is still open.
3. `agent/specialists/` holds only `__init__.py`: `scope_for` (AEA-35) is still missing; the ledger shows AEA-35
   `blocked`, NEEDS-DECISION (the same §9.1 question).
4. AEA-29 is still unmerged (branch `aea-29-aea-29-cases-handoff` exists). Its updated plan keeps
   `HandoffService.open(req: HandoffRequest, ctx: TurnContext) -> HandoffResult`, `CaseWriteFailed`, the
   `_alert` rule (P0, P1 or `FEE_BEARING_CHANGE` → `"supervisor_now"`) and "second open returns the open case with
   `created=False`" (it may raise the open case's priority; AC-10 asserts only the reference and `created`). §6.2's
   `HandoffDouble` still mirrors it; no change.
5. Spot-checked unchanged: `Presence = Literal["nobody_online", "simulated_on_shift"]` (`domain/common.py`),
   `TextId.FEE_CANT_GUARANTEE` / `FEE_PHONE_SUPPORT_OPEN` (`policy/texts.py`), `PROMISE_TABLE`, `promise_for`,
   `case_due_at`, `priority_for`, `decide_escalation`, `CheckEvent.from_halt` / `from_gate`, and the
   `tests/graph/_spine_doubles.py` helpers §6.2 imports.
6. The build ledger row AEA-39 still reads `ready` with blockers `AEA-11,AEA-14,AEA-21` (§8.3 R-3 still applies).

Readiness at refresh 2 (superseded by refresh 3): NEEDS-DECISION (§9.1), then BLOCKED-ON the specialist task types follow-up and AEA-35.

**Refresh 1 (2026-10-21, `main` at `b559c75`).** What changed since `96096be`, and what it does to this plan:

1. **AEA-21 merged** (`5531664`). Every name §4.2 listed for it is on `main` with the signature this plan copies:
   `GraphDeps`, `ModelsStatus` (`agent/context.py`; `scheduling`, `handoff`, `specialists` are still typed through `Any`
   aliases), `emit_signal`, `SIGNAL_LOGGER` (`agent/signals.py`), `BRAKE_HALTS`, `route_act_plan` (`agent/routers.py`),
   `NodeFn`, `CompiledGraph`, `timed_node`, `build_graph`, `run_graph` (`agent/graph.py`), `ReplyComposer`, `turn_trace`
   (`agent/nodes/compose.py`) and `tests/graph/_spine_doubles.py` (`THREAD`, `REQ`, `DEMO_NOW`, `RecordingSink`,
   `UowDouble`, `make_deps`, `make_ctx`, `make_input`, `no_rules`, `default_doubles`, `install_doubles`, `Harness`).
   `agent/nodes/act.py` is the 33-line stub whose three bodies raise `NotImplementedError`.
2. **The merged "AEA-02b" (`5305d57`) is not the follow-up this plan waited for.** It adds only `domain/views.py` (case
   and demo views for AEA-29/30). `grep -rn "^class SpecialistTask\|^class KnowledgeSlice\|^class AccountSlice" src/`
   still finds nothing, and `domain/specialists.py`'s docstring still says they are "Not built here". This plan now
   calls the prerequisite **the specialist task types follow-up**, the same one AEA-35's plan §8.3 R-1 asks for. Its
   signed home (`domain/specialists.py`, graph-tools §2) is a circular import, checked at `b559c75`: `domain/turn.py`
   line 44 imports `domain/specialists.py`, and `SpecialistTask.task` is a `PlannedTask` from `domain/turn.py` line 302.
   So placing it needs Innocent's yes (§9.1). No issue, branch or ledger row for it exists yet.
3. **`ConversationState.pending_change` is no longer a blocker.** It is still not on `main`, and AEA-38's plan (PD-4)
   has the `facts` node write no `pending_change`, so nothing sets it this wave. Step 2 reads it with
   `getattr(state, "pending_change", None) is not None` (PD-13): `False` today, and right with no edit here once the
   field lands.
4. **AEA-28 merged** (`2c2e8c5`). `SchedulingService.slice_inputs(customer_id) -> SchedulingSliceInputs` opens and
   closes its own read unit of work (`services/scheduling.py` line 335), as step 3 assumes. This ticket still injects a
   double (`GraphDeps.scheduling` is typed `Any`).
5. **AEA-57 merged** (`bd79a29`). The harness exists, but the integrated J-3/J-4 legs need CON-2 `submitTurn` (AEA-40)
   and the wired turn (AEA-51). The journey files stay `mock-tested` and the record's *Blocked by* is now **AEA-40,
   AEA-51**, as AEA-28's merged `tests/journeys/j4/test_aea_28.py` states.
6. **AEA-14 re-checked.** `decide_escalation`'s rule ids on `main`: `R2.person`, `R24.<reason>`, `R21.fee_bearing`,
   `D4.membership_cancel`, `D4.unsupported`, `D4.late_technician`, `R7.burning_ruled_out`, `R16.identity_unverified`,
   `AI.halt` / `AI.specialist_failed` / `AI.models_disabled` / `AI.planner_failed`, `OD6.two_misses` /
   `OD6.two_timeouts`, `none`. CAS-16 is settled by D-14 (option A: `BURNING_RULED_OUT` → P2 in `_PRIORITY`); this node
   still asserts no priority on that path. `promise_for` for WP-4 at `WORKED_PAIRS_NOW` returns
   `policy_row="R26.unstaffed"`, `due_label="Monday, October 19, 7:00 pm"` and the two extra lines §6.3 lists (checked
   by a scratch import, not a test).
7. **AEA-29 and AEA-35 are not merged.** `services/handoff.py` and `agent/specialists/runner.py` do not exist.
   `HandoffService.open` stays a double (injected; no edge). `scope_for` is a module-level function this node imports,
   so AEA-35 stays a real blocker (§8.3 R-2). AEA-35 is itself blocked on the same types follow-up.
8. **`CompletedAction` gained `source: Literal["actions_table"] = "actions_table"`** (defaulted); the doubles in §6.2 need
   no change. The build ledger row for AEA-39 says `ready` with blockers `AEA-11,AEA-14,AEA-21`; that is wrong (§8.3 R-3).

---

## 1. Goal and sources

### 1.1 Goal (from the issue's *What to build*)

> **US-14:** "As a **homeowner** whose request needs a person, I need a reference number, the exact promise (who gets back
> to me and by when), and a choice of email or phone and a time window, so that I know what happens next and never repeat
> my story." (Also US-12.)

Replace AEA-21's three stubs in `src/meridian/agent/nodes/act.py` with real bodies, and add the pure
`build_specialist_task`:

- **`run_specialist(payload, runtime, *, deps) -> SpecialistUpdate`**: one call per `Send` that AEA-21's `route_act_plan`
  builds. It reads the scheduling slice inputs (scheduling task, verified customer only), builds the `SpecialistTask`, calls
  `deps.specialists.run(task, scope_for(state, ctx), ctx)`, appends the result, and turns a brake or failure into a halt,
  a `brake` check event and a `signal` log record.
- **`escalation(state, runtime, *, deps) -> EscalationUpdate`**: builds `EscalationInputs` (with
  `models_disabled = deps.ledger.models_disabled()` and `now = ctx.now`) and returns `decide_escalation(inputs)`.
- **`handoff(state, runtime, *, deps) -> HandoffNodeUpdate`**: for an `escalate` decision, or for the `PERSON` gate (first
  ask, R-2), it builds one `HandoffRequest` from code values only and calls `deps.handoff.open(request, ctx)` once.

**What it does, concretely (WP-4).** Fri 2026-10-16 10:00, nobody online. MHC-57204 (verified) asks to move today's 12:00–4:00
tune-up. The plan has one scheduling `RESCHEDULE` task. `run_specialist` reads `deps.scheduling.slice_inputs(MHC-57204)`
(zone `central`, not a member, appointment 1 today 12:00–16:00), builds the task (SONNET-masked text, the scheduling slice,
no `customer_id`), and the runner returns `SchedulingResult(status="staff_change_request", change_request=<draft>)`.
`escalation` returns `outcome="escalate"`, `reason=fee_bearing_change`, `priority=P2`, `rule_id="R21.fee_bearing"`. `handoff`
calls `deps.handoff.open(HandoffRequest(trigger="escalation", reason=fee_bearing_change, priority=P2,
rule_id="R21.fee_bearing", change_request=<draft>, …), ctx)` and writes the returned `HandoffResult`. The promise, the case
due time and the alert are the service's (AEA-29), never this node's. No text comes from a model.

### 1.2 Context (why now)

AEA-21 built the graph spine with stubs of the five node modules (`act.py` raises `NotImplementedError`). AEA-14 built
`decide_escalation` and `priority_for`. This ticket fills the act group so the graph can run specialists in parallel,
decide escalation and open the one case per turn. Its collaborators (AEA-35 runner, AEA-29 handoff service, AEA-28
scheduling service) are injected through `GraphDeps` and tested with doubles here.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-39.md` (= issue #39) | AC-1…AC-17 (§3.1) |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-39 (blocked by 11, 14, 21; owns `nodes/act.py`; collaborators 35, 29, 28), §0a journey map J-3, J-4, §3 collision map | One file per journey (`tests/journeys/j3/test_aea_39.py`, `tests/journeys/j4/test_aea_39.py`); never edit another ticket's file |
| Node signatures and update types | `docs/design/contracts/stage7/graph-nodes.md` §9.1, §9.5 | Exact signatures (§4.4 here); each node returns only its own keys |
| Check events and signals | graph-nodes §1 (`CheckEvent.from_halt`), §4 (`specialist_failed`, `brake_fired`; the runner emits nothing) | §5 step 3 |
| Runner, `scope_for`, quick-check rule | `docs/design/contracts/stage7/graph-tools.md` §2, §3 (`SchedulingSliceInputs`, `AppointmentView`), §6 | §4.2, §5 step 2 |
| `GraphDeps`, `BRAKE_HALTS`, router edges | `docs/design/contracts/stage7/graph-core.md` §2, §4, §5, §8, §11; AEA-21 code | §4.3 |
| Escalation rule table, priority, promise | `docs/design/contracts/stage7/cases.md` §3.2, §3.3, §3.4 (rows 4, 6, 7; residual notes R-G-14, R-G-15), §4 (`slice_inputs`), §5 (`HandoffService.open`) | The node never computes priority, promise or due time |
| DO-4 | `docs/design/contracts/internal-components.md` §5 (`SpecialistTask`, `SchedulingSlice`, `ToolCallScope`), §6, §7 (`HandoffRequest`, `HandoffResult`, one open case per thread), §11 (*A brake fired*, provider-failure rows) | §4 |
| DO-3 | `docs/design/code-design.md` §2.3 rule 1 (no transaction across a model call), §5.2–§5.4 (keys, writers, skeleton), §3 module map row `nodes/act.py` | AC-12; AC-17 row edit |
| Residual rulings | `docs/plans/7b-decisions/residuals-graph.md` R-G-12 (act node builds every task), R-G-13 (`deps.ledger`), R-G-14 (`R2.person`, `trigger="gate"`), R-G-15 (`EscalationInputs.now`), R-G-19 (`slice_inputs`) | Settled; built as written |
| Stage 7 sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | D-14 keeps CAS-16 option A (`burning_ruled_out` → P2 in AEA-14's `priority_for`); nothing here answers it differently |
| Sibling plans (read only) | `AEA-02.md` §8.2 (types not built), `AEA-21.md`, `AEA-29.md` (`HandoffService.open`, `CaseWriteFailed`), `AEA-35.md` §4.6 (`scope_for`), `AEA-38.md` PD-4 (`facts` writes no `pending_change`); AEA-35b's commit `68f7f19` (the three task types, option A) | §4.1, §4.2, §8.3 |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`, `agent-architecture.md` rules 12, 16; workspace `code-structure.md` (file size), `async-safety.md` rule 1 | §7 |
| Evaluation / observability / metrics | DO-5 E-1 (WP-4, WP-7, WP-8), E-3/E-4, E-6; DO-6 WF-1 (specialists, escalation check), WF-2 (handoff node); DO-7 M-10, M-15, M-19…M-24 | Kept computable (AC-14); no eval run in this ticket |

### 1.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | WF-1 internals and WF-2's graph handoff only (CON-1/CON-2 are AEA-40; CON-4 is AEA-42) | — | — |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files the implementer may create or edit)

| File | Current | Change |
|---|---|---|
| `src/meridian/agent/nodes/act.py` | AEA-21 stub (33 lines) | **Replace the bodies** in place; keep the three signatures exactly; add `build_specialist_task` and private helpers. Target ≤ 300 lines |
| `tests/unit/agent/nodes/test_act.py` | — | **Create**: the 17 tests of §7.1. ≤ 500 lines |
| `tests/unit/agent/nodes/act_fixtures.py` | — | **Create**: builders and doubles (§6.2). ≤ 500 lines |
| `tests/journeys/j3/test_aea_39.py` | — | **Create** (AC-15, J-3) |
| `tests/journeys/j4/test_aea_39.py` | — | **Create** (AC-15, J-4) |
| `docs/testing/journeys/<run-date>-AEA-39.md` | — | **Create** (AC-15 record; `<run-date>` = the day you run it, `YYYY-MM-DD`) |
| `.claude/reference/area-map.md` | A7b row | Append this ticket's mention only (§5 step 9) |
| `.claude/state/icm-progress.md` | *Routes verified…* rows | Add one row (§5 step 9) |
| `docs/design/code-design.md` | §3 module-map line for `nodes/act.py` | Status suffix only (§5 step 9) |

`tests/unit/agent/nodes/__init__.py` already exists (AEA-21). `tests/journeys/j3/__init__.py` and `j4/__init__.py` exist on
`main`. Do not create or edit them.

### 2.2 Shared surfaces: read, never edit

`src/meridian/domain/*` (AEA-02 / AEA-02b), `src/meridian/policy/{escalation,handoff,limits,texts}.py`,
`src/meridian/privacy/redact.py`, `src/meridian/agent/{context,graph,routers,signals}.py` and `agent/nodes/compose.py`
(AEA-21), `src/meridian/agent/specialists/runner.py` (AEA-35; import `scope_for` only), `tests/graph/_spine_doubles.py`
(AEA-21; import its helpers), `tests/fakes/*` (AEA-11), `tests/conftest.py`, `tests/journeys/affected.py` (AEA-01),
`src/meridian/domain/tools.py` (AEA-35b; import `SpecialistTask`, `KnowledgeSlice`, `AccountSlice`, `ToolCallScope`),
`tests/services/_case_fixtures.py` (AEA-29; J-4 imports `services`, `new_thread`, `summary_of`), `tests/fixtures/sqlite.py`
(`temp_sqlite`, `ISSUED_DB`), `src/meridian/services/{handoff,cases}.py` (AEA-29; J-4 runs them, never edits them).

### 2.3 Owned by other tickets — must not touch

`policy/escalation.py`, `policy/handoff.py` (AEA-14); `services/handoff.py`, `services/cases.py` (AEA-29);
`services/scheduling.py` (AEA-28); `agent/specialists/*`, `agent/prompts/specialists.py` (AEA-35); `agent/routers.py`,
`agent/graph.py`, `agent/context.py`, `agent/signals.py`, `nodes/compose.py` (AEA-21); `nodes/{front,plan,reply,load_context}.py`
(AEA-36, 37, 38, 34); `domain/*` (AEA-02/02b); `tests/journeys/support/` (AEA-57); every `apps/web/**`, `docs/ux/**`,
`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, the briefing, issued data, `docs/archive/`, `docs/parked/`.

---

## 3. Requirements table

### 3.1 Acceptance criteria (issue IDs) → implementation → verification

All tests are in `tests/unit/agent/nodes/test_act.py` unless named otherwise. Run: `uv run pytest
tests/unit/agent/nodes/test_act.py -q`.

| AC | Requirement (short; full text in the issue) | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | Three `Send`s → three `run_specialist` calls in one superstep; results in `PlannedTask.order` (account, scheduling, knowledge); each call gets `scope_for(payload["state"], ctx)` | §5 step 3 (`run_specialist`) | `test_fanout_three_tasks_parallel` (§7.1) |
| AC-2 [invariant] | Each task carries only its slice; no `customer_id`, no chat window; `scope_for` gives `customer_id=None` unless verified; `offer_quick_checks` per graph-tools §6; false on the burning-"no" booking | §5 step 2 (`build_specialist_task`, `_offers_quick_checks`) | `test_specialist_task_slices_and_quick_check_offer` |
| AC-3 [invariant] | WP-4: `staff_change_request` → escalate, `fee_bearing_change`, P2, `R21.fee_bearing`; one `HandoffRequest` with the draft; no write reaches scheduling | §5 steps 4–5 | `test_wp4_fee_bearing_escalates_p2` |
| AC-4 [invariant] | WP-7 refund → P3 `refund` (`R24.refund`); WP-8 → `D4.membership_cancel`, P3; inputs' `now == ctx.now` | §5 step 4 | `test_wp7_refund_p3`, `test_wp8_membership_cancel_d4` |
| AC-5 [invariant] | `PERSON` gate → handoff on the first ask: `customer_requested_person`, P3, `R2.person`, `trigger="gate"`; 0 runner, 0 gateway calls | §5 step 5 (`_person_request`) | `test_person_gate_first_ask` (compiled graph) |
| AC-6 [failure/refusal] | Rule 6: halt / one failed result / `models_disabled` / `planner_failed` and no tasks → escalate, `ai_failure`, P3, `degraded=True`, ids `AI.halt` / `AI.specialist_failed` / `AI.models_disabled` / `AI.planner_failed`; one handoff request each | §5 steps 4–5 | `test_rule6_degraded_handoff` (4 parametrised cases) |
| AC-7 [failure/refusal] | `BRAKE_TOOL_ROUNDS` → halt + 1 `brake` event + 1 `brake_fired`; `DEADLINE` → halt only; `failed` no brake → 1 `specialist_failed` (`cause` = failure kind or `tool_error`) | §5 step 3 | `test_brakes_and_failures_emit_events_and_signals` |
| AC-8 [failure/refusal] | `not_verified` / `locked` with a private task → `identity_unverified`, P3; the update holds no account data | §5 step 4 | `test_not_verified_escalates_reveals_nothing` |
| AC-9 [invariant] | Rule 7 → `offer` (`OD6.two_misses` / `OD6.two_timeouts`); no handoff call | §5 steps 4–5 | `test_two_misses_or_timeouts_offer` |
| AC-10 [invariant] | Second escalation with an open case → service's `created=False`, same reference; a repeat of the same turn sends an equal request (same `ActionKey`) | §5 step 5 | `test_second_handoff_same_reference` |
| AC-11 [negative] | No model text in a `HandoffRequest`, in `handoff`, in check events or in `meridian.signal` records | §5 steps 3, 5 | `test_handoff_request_has_no_model_text` |
| AC-12 [invariant] | No transaction open across a specialist run | §5 step 3 (read closes before the run; `act.py` never calls `deps.uow`) | `test_no_uow_during_specialists`; `grep -n "uow(" src/meridian/agent/nodes/act.py` prints nothing |
| AC-13 [invariant] | Each node returns only its own update keys; type check clean | §4.4 return types | `test_act_nodes_write_only_own_keys`; `uv run mypy` |
| AC-14 [capture] | Decision leaves `rule_id`, `reason`, `priority`, `degraded`; results keep `kind`; every `escalate` → exactly one `open` | §5 steps 4–5 | `test_escalation_record_fields_and_case_per_escalate` |
| AC-15 [journey] | Extends J-3 and J-4 | §5 step 8 | `uv run pytest -m journey tests/journeys/j3/test_aea_39.py tests/journeys/j4/test_aea_39.py`; level **`mock-tested`** (J-4 stores its case through the real `HandoffService` on a temp SQLite copy), *Blocked by* AEA-51 (the ticket names AEA-57; it and AEA-40 have merged; record §7.4) |
| AC-16 [invariant] | `build_specialist_task` is pure: SONNET-masked texts, DO-4 §5 slice, no `customer_id`, slice inputs from the argument (`None` → `None` / `False` / `()`), same inputs → equal task, no I/O | §5 step 2 | `test_build_specialist_task` |
| AC-17 [regression/context] | Area-map A7b, ICM row, DO-3 §3 row updated; only this ticket's rows | §5 step 9 | `git diff --name-only main...HEAD` shows the three docs; `git diff` of each shows one changed line/row |

### 3.2 Plan-added criteria (the orchestrator may post them on the issue)

| ID | Criterion | Verified by |
|---|---|---|
| PA-1 | `bookings_left` is `max(0, Limits.booking.max_per_conversation − counters.bookings)`; never negative | `test_build_specialist_task` (case *bookings*) |
| PA-2 | A failure of `deps.handoff.open` is not swallowed: the exception leaves the node unchanged (no halt written, no retry here; the service already retried once) | `test_handoff_open_failure_propagates` |
| PA-3 | When this turn's results hold a staff change request draft, the `HandoffRequest` carries it, whatever reason won | `test_wp4_fee_bearing_escalates_p2` (draft present); `test_escalation_record_fields_and_case_per_escalate` (WP-7 row: `change_request is None`) |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Node signatures `(state|payload, runtime, *, deps)` | graph-nodes §9.5 | yes | in-ticket (AC-13) | §4.4 |
| `build_specialist_task(planned, state, ctx, *, scheduling, limits)` pure | graph-nodes §9.5, R-G-12 | yes | in-ticket (AC-16) | step 2 |
| `customer_text = redact(state.turn_input.text_store, SONNET).text` | graph-nodes §9.5 | yes | in-ticket (AC-16) | step 2 |
| `task_messages` = the open task's customer messages, SONNET | DO-4 §5, graph-nodes §9.5 | yes (no derivation given) | **added** (PD-1) | step 2 |
| `SchedulingSlice.pending_change = state.pending_change is not None` | graph-nodes §9.5 | yes | **added** (PD-13): `ConversationState.pending_change` is not on `main` (AEA-02 §8.2) and nothing writes it this wave (AEA-38 PD-4); read with `getattr`, `False` until it lands | step 2 |
| `SpecialistTask`, `KnowledgeSlice`, `AccountSlice` exist | DO-4 §5, graph-tools §2 (+ AEA-35b home note) | yes (named as AEA-02's) | **other-ticket AEA-35b**: option A (Innocent, 2026-10-21) puts them in `domain/tools.py`; merged before this ticket builds | step 0 item 2 |
| `scope_for` imported from `agent/specialists/runner.py` | graph-tools §2 | yes | **blocked-on AEA-35** (module not on `main`; a free function cannot be injected) | step 0 |
| `GraphDeps`, `emit_signal`, `BRAKE_HALTS`, stub file | graph-core §4, §5; graph-nodes §4 | yes | in-ticket (on `main` since AEA-21 merged, `5531664`) | step 0 (sanity check) |
| Slice inputs read closes before the run | DO-3 §2.3 rule 1, R-G-19 | yes | in-ticket (AC-12) | step 3 |
| `offer_quick_checks` three conditions | graph-tools §6 | yes | in-ticket (AC-2) | step 2 |
| Brake → halt + event + signal; DEADLINE / PROVIDER_SPEND_CAP → halt only | graph-nodes §1, §4 | yes | in-ticket (AC-7) | step 3 |
| Other non-brake halts from the runner (e.g. `SPEND_CAP`) | graph-nodes §1 (`from_halt` raises for them) | no | **added** (PD-9: halt only) | step 3 |
| `models_disabled` from `deps.ledger`, `now` from `ctx.now` | R-G-13, R-G-15 | yes | in-ticket (AC-4, AC-6) | step 4 |
| Person-gate request (`R2.person`, `trigger="gate"`, P3 via `priority_for`) | cases §3.4, R-G-14 | yes | in-ticket (AC-5) | step 5 |
| One `open` per turn, idempotent on the turn's `ActionKey` | graph-nodes §9.5; DO-4 §7 | yes | in-ticket (AC-10); the key's idempotency is the service's (AEA-29), this node sends an equal request on a repeat | step 5 |
| `offer` / `none` open nothing | ticket *The behaviour* | yes | in-ticket (AC-9) | step 5 |
| Case write failure on a non-safety handoff | DO-1 §8.2 names `case_write_failed` for the safety node only (graph-nodes §4) | no | **added** (PA-2, PD-6: propagate) | step 5 |
| Promise text, priority, due time never set by the node | DO-4 §7; cases §3.2, §3.3 | yes | in-ticket (AC-11) | step 5 |
| Turn record fields for `turn_trace` | graph-core §2 | yes | in-ticket (AC-14); `turn_trace` is AEA-21's | step 4 |
| CAS-16 burning-"no" priority | cases §3.3; D-14 (option A) | yes | in-ticket: pass through `decide_escalation`; assert **no** priority level on that path | step 4 |
| Journey J-3, J-4 | slice plan §0a; integrated-journeys §3–§4 | yes | in-ticket (AC-15); integrated steps **other-ticket** AEA-51 (AEA-57's harness and AEA-40's CON-2 have merged) | step 8 |
| Context rows | context-maintenance; collision map | yes | in-ticket (AC-17) | step 9 |
| Dev-log entry | context-maintenance *At the end of a run* | no | **other-ticket**: the orchestrator writes it (outside owned files) | §8.3 R-4 |

---

## 4. Shared code to use (exact; verify each in step 0)

### 4.1 Types and functions on `main` now (`8a205b2`; unchanged since `b559c75`)

```python
# meridian.domain.state (AEA-02)
class ConversationState(MeridianModel):
    thread_id: ThreadId
    settled: Settled | None = None
    controller: Controller
    identity: IdentityState
    open_tasks: list[OpenTask]; shown_slots: list[ShownSlot]; counters: FailureCounters
    burning_card_id: str | None = None
    turn_input: TurnInput
    chat_window: list[ChatLine]
    gate: GateDecision | None = None; planner: PlannerOutcome | None = None; danger: DangerAssessment | None = None
    plan: Plan | None = None; identity_step: IdentityStep | None = None
    specialist_results: Annotated[list[SpecialistResult], operator.add]
    escalation: EscalationDecision | None = None; handoff: HandoffResult | None = None
    facts, draft, brief_extraction, checked, reply: ... | None = None
    halt: Annotated[Halt | None, first_halt] = None
    check_events: Annotated[tuple[CheckEvent, ...], add_turn_events] = ()
    # pending_change: NOT on main (AEA-02 §8.2); read with getattr (PD-13), never required
class OpenTask(MeridianModel):
    task_id: str; specialist: SpecialistKind; intent: TaskIntent; opened_turn: TurnId; details: TaskDetails
    status: Literal["open", "waiting_identity", "done"]
class TaskDetails(MeridianModel):
    zip: str | None = None; city: str | None = None; service_type: ServiceType | None = None
    wanted_text: str | None = None; appointment_id: int | None = None
class ChatLine(MeridianModel):
    speaker: Literal["customer", "assistant", "representative", "event"]; text: str; turn_id: TurnId | None; at: datetime
def first_halt(left: Halt | None, right: Halt | None) -> Halt | None
def add_turn_events(left: tuple[CheckEvent, ...], right: tuple[CheckEvent, ...]) -> tuple[CheckEvent, ...]
class SpecialistSend(TypedDict):  planned: PlannedTask; state: ConversationState
class SpecialistUpdate(TypedDict, total=False):
    specialist_results: list[SpecialistResult]; check_events: tuple[CheckEvent, ...]; halt: Halt
class EscalationUpdate(TypedDict, total=False):  escalation: EscalationDecision
class HandoffNodeUpdate(TypedDict, total=False):  handoff: HandoffResult; halt: Halt

# meridian.domain.turn (AEA-02)
SpecialistKind = Literal["knowledge", "account", "scheduling"]
class TaskIntent(StrEnum): ANSWER_QUESTION, READ_INVOICE, READ_MEMBERSHIP, READ_APPOINTMENTS, READ_WARRANTY,
                           BOOK_NEW = "book_new", RESCHEDULE, CANCEL, CONFIRM
class PlannedTask(MeridianModel):
    order: int = Field(ge=1, le=3); specialist: SpecialistKind; intent: TaskIntent; needs_identity: bool
    resumes_task_id: str | None = None
class Plan(MeridianModel):
    mode: Literal["talk", "act"]; tasks: tuple[PlannedTask, ...] (max 3); handoff_request: HandoffReason | None
    topic: Literal["booking", "membership", "billing", "warranty", "other"]
    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]; planner_failed: bool = False
class GateKind(StrEnum): AI_PAUSED, SAFETY, BURNING_ASK, BURNING_ANSWER, DANGER_RULE, PERSON, CODE_ENTRY, LOCATE,
                         CARD_CHOICE, FREE_TEXT = "free_text"
class RuleMatches(MeridianModel):
    safety: SafetyKind | None; burning_unclear: bool; danger_words: bool; person: bool
    policy_trigger: HandoffReason | None; rule_ids: tuple[str, ...]; correction: bool
class GateDecision(MeridianModel):
    kind: GateKind; rules: RuleMatches; burning_answer: Literal["yes", "no", "unsure"] | None = None
    resume_task_id: str | None = None
class DangerAssessment(MeridianModel):
    label: Literal["normal", "burning_unclear", "danger"]; raised: bool; confidence: float | None = None
    failure: ProviderFailure | None
class EscalationInputs(MeridianModel):
    gate: GateDecision; plan: Plan | None; results: tuple[SpecialistResult, ...]; counters: FailureCounters
    identity: IdentityState; halt: Halt | None; models_disabled: bool; now: datetime
class EscalationDecision(MeridianModel):
    outcome: Literal["none", "offer", "escalate"]; reason: HandoffReason | None; priority: Priority | None
    rule_id: str; degraded: bool = False
class TurnInput(MeridianModel):
    turn_id: TurnId; message_id: int; kind: Literal["text", "choice", "code", "form"]; text_store: str
    card_id: str | None = None; choice: CardChoice | None = None; card_number_seen: bool = False; received_at: datetime
class TurnIds(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId; run_tag: Literal["live", "eval", "load"]
    run_id: str | None; agent_version: str
@dataclass(frozen=True) class TurnBudget: started: float; deadline: float
@dataclass(frozen=True) class SpanHandle: turn_id: TurnId; trace_id: str | None; native: object = None
@dataclass(frozen=True) class TurnContext:
    ids: TurnIds; budget: TurnBudget; now: datetime; demo_session: str; span: SpanHandle; intake: Intake | None = None
class CheckEvent(MeridianModel):
    check: CheckKind; turn_id: TurnId; result: Literal["pass","trimmed","fallback","fired","raised"]
    removed: int = 0; claim_kinds: tuple[str, ...] = (); codes: tuple[str, ...] = ()
    @classmethod
    def from_halt(cls, turn_id: TurnId, halt: Halt) -> CheckEvent:
        # ValueError unless halt.reason in BRAKE_* or RECURSION_LIMIT; result="fired", codes=(reason.value, halt.node)
class SignalName(StrEnum): ... SPECIALIST_FAILED = "specialist_failed"; BRAKE_FIRED = "brake_fired"; ...
class SignalRecord(MeridianModel):
    record: Literal["signal"] = "signal"; name: SignalName
    turn_id: TurnId; thread_id: ThreadId; request_id: RequestId; run_tag: RunTag; node: str
    cause: str | None = None
    role: Literal["planner", "classifier", "specialist", "responder", "brief"] | None = None
    specialist: SpecialistKind | None = None; attempt: int | None = None; recovered: bool | None = None

# meridian.domain.common (AEA-02)
class HaltReason(StrEnum): DEADLINE = "deadline"; BRAKE_TASKS = "brake_tasks"; BRAKE_TOOL_ROUNDS = "brake_tool_rounds"
    BRAKE_SONNET_CALLS = "brake_sonnet_calls"; BRAKE_IDENTICAL_CALL = "brake_identical_call"
    RECURSION_LIMIT = "recursion_limit"; SPEND_CAP = "spend_cap"; PROVIDER_SPEND_CAP = "provider_spend_cap"
class Halt(MeridianModel): reason: HaltReason; node: str; elapsed_ms: int
class ProviderFailureKind(StrEnum): TIMEOUT = "timeout"; ...   # 14 values
class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind; provider: Literal["anthropic", "openrouter_jev"]; http_status: int | None
    retry_after_s: float | None; retryable: bool; provider_request_id: str | None
class FailureCounters(MeridianModel):
    failed_answers: int = 0; tool_failures: int = 0; identity_failures: int = 0; corrections: int = 0
    timeouts: int = 0; bookings: int = 0
class CustomerId(str)  # ^MHC-[0-9]{5}$ ; CaseRef ^MHC-C-[0-9]{4}$ ; ThreadId/TurnId/RequestId = UUID4 (lowercase)

# meridian.domain.handoff (AEA-02; re-exports HandoffReason, Priority, Presence, Promise from common)
class HandoffReason(StrEnum): SAFETY, DANGER, BURNING_UNCLEAR, CUSTOMER_REQUESTED_PERSON = "customer_requested_person",
    REFUND = "refund", BILLING_DISPUTE, COMPLAINT_OR_MANAGER, LEGAL_OR_CHARGEBACK, COMMERCIAL, LATE_TECHNICIAN,
    FEE_BEARING_CHANGE = "fee_bearing_change", MEMBERSHIP_CANCEL = "membership_cancel", UNSUPPORTED_ACTION,
    IDENTITY_UNVERIFIED = "identity_unverified", AI_FAILURE = "ai_failure", BURNING_RULED_OUT = "burning_ruled_out"
class Priority(StrEnum): P0 … P4
class HandoffRequest(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; reason: HandoffReason; priority: Priority; rule_id: str
    trigger: Literal["gate", "escalation", "con4", "safety"]; identity: IdentityState
    change_request: ChangeRequestDraft | None = None; safety_kind: SafetyKind | None = None
class CaseSummary(MeridianModel):
    case_ref: CaseRef; reason: HandoffReason; priority: Priority; state: CaseState; created_at: datetime
    promise: Promise; followup: FollowUp | None; version: int; seed: bool = False; due_at: datetime | None
class HandoffResult(MeridianModel):
    case: CaseSummary; created: bool; action: CompletedAction; alert: Literal["supervisor_now"] | None

# meridian.domain.actions (AEA-02)
class ActionKind(StrEnum): BOOKED = "booked"; MOVED; CANCELLED; CHANGE_REQUEST_SENT; CASE_OPENED = "case_opened"; ...
class ActionKey(MeridianModel): thread_id: ThreadId; turn_id: TurnId; kind: ActionKind; record_id: str
class CompletedAction(MeridianModel):
    key: ActionKey; kind: ActionKind
    records: dict[Literal["appointment", "slot", "old_slot", "case", "customer", "promise"], str]
    before: dict[str, str] | None = None; after: dict[str, str] | None = None; at: datetime
    source: Literal["actions_table"] = "actions_table"
class Settled(MeridianModel): actions: tuple[CompletedAction, ...]; open_case: OpenCase | None; read_at: datetime

# meridian.domain.identity (AEA-02)
class IdentityState(MeridianModel):
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None; masked_hint: str | None; code_expires_at: datetime | None
    tries_left: int (0..3); codes_sent: int (0..3); verified_at: datetime | None

# meridian.domain.specialists (AEA-02)
class ChangeRequestDraft(MeridianModel):
    appointment_id: int; change: Literal["move", "cancel"]; wanted_text: str; windows_shown: tuple[int, ...]
    hours_before: float; window_start: datetime
class AppointmentView(MeridianModel):
    appointment_id: int; date: date; window: Window; service_type: ServiceType; technician: str | None
    is_warranty_visit: bool
class SchedulingSliceInputs(MeridianModel):
    zone: Zone | None; member: bool; appointments: tuple[AppointmentView, ...] = ()
class SchedulingSlice(MeridianModel):
    customer_zone: Zone | None; member: bool; appointments: tuple[AppointmentView, ...]
    shown_slots: tuple[ShownSlot, ...]; pending_change: bool; bookings_left: int
class KnowledgePoint(MeridianModel): text: str (≤500); passage_id: PassageId
class KnowledgeResult(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"; status: Literal["answered", "no_current_source", "failed"]
    passages: tuple[Passage, ...]; points: tuple[KnowledgePoint, ...]; quick_checks: tuple[PassageId, ...] = ()
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None
class AccountResult(MeridianModel):
    kind: Literal["account"] = "account"; status: Literal["read", "not_verified", "failed"]
    invoices: tuple[InvoiceView, ...] = (); membership: MembershipView | None = None; warranty: WarrantyView | None = None
    staff_notes: tuple[StaffNote, ...] = (); tools; calls; brake = None; failure = None
class MembershipView(MeridianModel): tier: Literal["none", "standard", "plus"]; renewal_date: date | None
class SchedulingResult(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    status: Literal["windows_shown", "written", "staff_change_request", "slot_taken", "out_of_area", "no_fit",
                    "not_verified", "booking_cap", "failed"]
    windows: tuple[ShownSlot, ...] = (); write: WriteResult | None = None; change_request: ChangeRequestDraft | None = None
    quick_checks: tuple[Passage, ...] = (); tools; calls; brake = None; failure = None
SpecialistResult = Annotated[KnowledgeResult | AccountResult | SchedulingResult, Field(discriminator="kind")]
class WriteResult(MeridianModel): action: CompletedAction; confirmation: ConfirmationView
class ConfirmationView(MeridianModel): date: date; window: Window; technician: str; fee_note: FeeNote

# meridian.domain.records (AEA-02)
Zone = Literal["north", "central", "south"]
Window = Literal["08:00-12:00", "12:00-16:00", "13:00-17:00", "16:00-19:00"]
ServiceType = Literal["hvac_repair", "hvac_tune_up", "plumbing", "estimate"]
class FeeNote(MeridianModel): service_type: ServiceType; tier: MembershipTier; fee_row: str | None
    amount_cents: int (≥0); waived: bool; line: str (1..120)
class ShownSlot(MeridianModel): slot_id: int; date: date; window: Window; technician: str; service_type: ServiceType
    zone: Zone; member_reserved: bool; shown_turn: TurnId

# meridian.domain.tools (AEA-02)
class ToolCallScope(MeridianModel):
    ids: TurnIds; customer_id: CustomerId | None; shown_slot_ids: frozenset[int]; now: datetime; message_id: int

# meridian.policy.escalation (AEA-14)
def decide_escalation(inputs: EscalationInputs) -> EscalationDecision    # pure; first match wins (cases §3.4)
# meridian.policy.handoff (AEA-14)
def priority_for(reason: HandoffReason, *, promise_due: datetime | None = None,
                 renewal_date: date | None = None) -> Priority           # CUSTOMER_REQUESTED_PERSON → P3
def promise_for(reason: HandoffReason, presence: Presence, now: datetime, window_start: datetime | None = None) -> Promise
def case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None
def due_label(dt: datetime) -> str                                         # "Monday, October 19, 7:00 pm"
PROMISE_TABLE: Mapping[PolicyRow, str]   # "R26.unstaffed", "R26.refund", ...
# meridian.policy.texts (AEA-03)
class TextId(StrEnum): FEE_CANT_GUARANTEE = "fee_change.cant_guarantee"; FEE_PHONE_SUPPORT_OPEN = ...; ...
def render(text_id: TextId, **values: str) -> str
# meridian.policy.limits (AEA-01)
@dataclass(frozen=True) class Limits: ...; booking: BookingLimits  # BookingLimits.max_per_conversation: int = 3
# meridian.privacy.redact (AEA-04)
class RedactionProfile(StrEnum): STORE, SONNET = "sonnet", JEV, TRACE, LOG
@dataclass(frozen=True) class Redacted: text: str; replaced: Mapping[RedactionKind, int]; length: int
def redact(text: str, profile: RedactionProfile) -> Redacted

# tests.fakes (AEA-11)
CHICAGO = ZoneInfo("America/Chicago"); WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=CHICAGO)
```

### 4.2 AEA-21's names (on `main`), AEA-35b's types and AEA-35's `scope_for` (step 0 checks the last two)

```python
# AEA-21 — ON MAIN since 5531664 (re-checked at b559c75)
# meridian.agent.context
class ModelsStatus(Protocol):
    def models_disabled(self) -> bool: ...
@dataclass(frozen=True)
class GraphDeps:   # fields in this order; scheduling, handoff, specialists are typed through `Any` aliases (PD-7 of AEA-21)
    gateway: ModelGateway; retrieval: RetrievalIndex; uow: UnitOfWorkFactory; identity: IdentityService
    scheduling: SchedulingService; handoff: HandoffService; brief: BriefAssembler; demo: DemoService; limits: Limits
    trace: TraceSink; specialists: SpecialistRunner; cases: CaseService; ledger: ModelsStatus
# meridian.agent.signals
SIGNAL_LOGGER = "meridian.signal"
def emit_signal(ids: TurnIds, record: SignalRecord) -> None   # ValueError if record.turn_id/thread_id differ from ids
    # logging.getLogger("meridian.signal").info("signal", extra={"signal": record.model_dump(mode="json")})
# meridian.agent.routers
BRAKE_HALTS: Final[frozenset[HaltReason]] = frozenset({BRAKE_TASKS, BRAKE_TOOL_ROUNDS, BRAKE_SONNET_CALLS,
                                                        BRAKE_IDENTICAL_CALL})
def route_act_plan(state: ConversationState) -> Literal["identity"] | list[Send]
    # [Send("run_specialist", SpecialistSend(planned=t, state=state)) for t in plan.tasks] when identity is fine
# meridian.agent.graph
NodeFn = Callable[[NodeInput, Runtime[TurnContext]], NodeUpdate]
def timed_node(name: str, fn: NodeFn, deps: GraphDeps) -> NodeFn
def build_graph(deps: GraphDeps, *, checkpointer: BaseCheckpointSaver[Any] | None, composer: ReplyComposer) -> CompiledGraph
def run_graph(graph, turn_input: TurnInput, ctx: TurnContext, *, deps: GraphDeps, composer: ReplyComposer) -> GraphOutcome
# meridian.agent.nodes.compose
class ReplyComposer: ...   # ReplyComposer() takes no arguments
# tests.graph._spine_doubles (test helpers AEA-21 publishes for later tickets)
THREAD = ThreadId("6f1c2d3e-4b5a-4c6d-8e7f-0a1b2c3d4e5f"); REQ = RequestId("3c4d5e6f-7a8b-4c9d-8e0f-2a3b4c5d6e7f")
class RecordingSink: nodes: list[tuple[str, int, str]]       # a TraceSink
class UowDouble: ...                                          # core.settled_for only
def make_deps(sink: RecordingSink, uow: UowDouble | None = None) -> GraphDeps
def make_input(turn_id: TurnId, text_store: str = "Yes, please.") -> TurnInput   # message_id=1
def no_rules() -> RuleMatches
def default_doubles() -> dict[str, Callable[..., Any]]
def install_doubles(monkeypatch, visits: list[str], **overrides: Callable[..., Any]) -> None
    # replaces the 14 stub node functions (module attributes) with doubles that append their name to `visits`;
    # an override is any callable (state, runtime, *, deps)

# NOT YET ON MAIN — AEA-35, agent/specialists/runner.py (its plan §4.6; merges after AEA-35b, before this ticket)
def scope_for(state: ConversationState, ctx: TurnContext) -> ToolCallScope
    # customer_id = state.identity.customer_id only when status == "verified", else None;
    # shown_slot_ids = frozenset(s.slot_id for s in state.shown_slots); now = ctx.now; ids = ctx.ids;
    # message_id = state.turn_input.message_id
class SpecialistRunner:
    def run(self, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext) -> SpecialistResult  # never raises

# AEA-35b — meridian.domain.tools (branch aea-35b-specialist-types, 68f7f19; merged before this ticket builds).
# Copied from that commit. MeridianModel is frozen: build each object once, never assign to a field.
class KnowledgeSlice(MeridianModel):
    """AEA-35b: kind-only marker. The knowledge specialist sees only the customer's text (graph-tools section 2)."""
    kind: Literal["knowledge"] = "knowledge"
class AccountSlice(MeridianModel):
    """AEA-35b: kind-only marker. Account tools get the verified customer from code (`ToolCallScope`), not from here."""
    kind: Literal["account"] = "account"
class SpecialistTask(MeridianModel):
    task: PlannedTask
    customer_text: str
    task_messages: tuple[str, ...]
    slice: KnowledgeSlice | AccountSlice | SchedulingSlice
    offer_quick_checks: bool = False
# ConversationState.pending_change is NOT needed (PD-13)

# AEA-28 (merged, services/scheduling.py:335) / AEA-29 (merged ef561fc, services/handoff.py:106) — injected only
# (GraphDeps.scheduling / .handoff are `Any` aliases), never imported by act.py
SchedulingService.slice_inputs(customer_id: CustomerId) -> SchedulingSliceInputs    # opens and closes its own read UoW
HandoffService.open(req: HandoffRequest, ctx: TurnContext) -> HandoffResult
    # one write transaction; retries once; raises services.handoff.CaseWriteFailed(attempts=2) after the 2nd failure;
    # alert "supervisor_now" for P0, P1 or FEE_BEARING_CHANGE (services/cases.py _alert); joining the thread's open case
    # returns created=False with the same case_ref (it may raise the case's priority)
```

### 4.3 How the graph reaches these nodes (AEA-21, for orientation only)

- `gates` → `route_after_gates`: `PERSON` → `"handoff"` (escalation is skipped; `state.escalation is None`);
  `BURNING_ANSWER` + `"no"` → `route_act_plan` (the gates node wrote a scheduling `BOOK_NEW` plan with
  `handoff_request=burning_ruled_out`).
- `plan_join` → `route_after_plan_join`: `planner_failed and not tasks` → `"escalation"`; no tasks + `handoff_request` →
  `"escalation"`; an act plan → `route_act_plan` (identity first if needed, else one `Send` per task).
- `run_specialist` → `route_after_specialists`: a brake halt in `BRAKE_HALTS` → `"escalation"` once; other halts →
  `"compose"`; else `"escalation"`.
- `escalation` → `route_after_escalation`: `escalate` → `"handoff"`; otherwise `"facts"`. `handoff` → `facts` (plain edge).
- `build_graph` registers each node as `timed_node(name, functools.partial(fn, deps=deps), deps)`.

### 4.4 The exact module to write: `src/meridian/agent/nodes/act.py`

Module docstring: `"""The act nodes: specialist fan-out, escalation decision and handoff (A7b; graph-nodes section 9.5)."""`

Imports (exact):

```python
from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Final

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.routers import BRAKE_HALTS
from meridian.agent.signals import emit_signal
from meridian.agent.specialists.runner import scope_for
from meridian.domain.common import Halt
from meridian.domain.handoff import HandoffReason, HandoffRequest, HandoffResult
from meridian.domain.specialists import (
    AccountResult,
    ChangeRequestDraft,
    KnowledgeResult,
    SchedulingResult,
    SchedulingSlice,
    SchedulingSliceInputs,
)
from meridian.domain.state import (
    ConversationState,
    EscalationUpdate,
    HandoffNodeUpdate,
    OpenTask,
    SpecialistSend,
    SpecialistUpdate,
)
from meridian.domain.tools import AccountSlice, KnowledgeSlice, SpecialistTask  # AEA-35b (option A, Innocent 2026-10-21)
from meridian.domain.turn import (
    CheckEvent,
    EscalationInputs,
    GateKind,
    PlannedTask,
    SignalName,
    SignalRecord,
    SpecialistKind,
    TaskIntent,
    TurnContext,
)
from meridian.policy.escalation import decide_escalation
from meridian.policy.handoff import priority_for
from meridian.policy.limits import Limits
from meridian.privacy.redact import RedactionProfile, redact
```

`decide_escalation` and `emit_signal` must be **module-level names called by name** (tests monkeypatch
`meridian.agent.nodes.act.decide_escalation` to record its inputs). `__all__ = ["PERSON_RULE_ID", "QUICK_CHECK_SERVICE_TYPES",
"build_specialist_task", "escalation", "handoff", "run_specialist"]`.

Public signatures (copied from graph-nodes §9.5; the three node signatures are unchanged from AEA-21's stub):

```python
PERSON_RULE_ID: Final = "R2.person"                                   # cases §3.4 residual note (R-G-14)
QUICK_CHECK_SERVICE_TYPES: Final[frozenset[str]] = frozenset({"hvac_repair", "plumbing"})   # graph-tools §6 rule 2
_NODE: Final = "run_specialist"

def run_specialist(payload: SpecialistSend, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> SpecialistUpdate: ...
def build_specialist_task(planned: PlannedTask, state: ConversationState, ctx: TurnContext, *,
                          scheduling: SchedulingSliceInputs | None, limits: Limits) -> SpecialistTask: ...
def escalation(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> EscalationUpdate: ...
def handoff(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> HandoffNodeUpdate: ...
```

`ctx` is unused inside `build_specialist_task`; keep the parameter (contract signature). Ruff's selected rules
(`E,W,F,I,B,UP,S,RUF`) do not flag an unused argument.

---

## 5. Steps (build order; each step ends with a check)

Work in your worktree from the repo root. `export UV_LINK_MODE=hardlink`. Never copy a venv; no `node_modules`.

**Step 0 — prerequisites (stop if any fails; report `blocked-on <ticket>` and do nothing else).**

1. Sanity check (AEA-21 merged at `5531664`): `git log --oneline main | grep -i "AEA-21"` shows the merge, and `grep -n "NotImplementedError"
   src/meridian/agent/nodes/act.py` shows the three stubs. `grep -n "^class GraphDeps\|^class ModelsStatus"
   src/meridian/agent/context.py`, `grep -n "^def emit_signal" src/meridian/agent/signals.py`, `grep -n "^BRAKE_HALTS\|^def
   route_act_plan" src/meridian/agent/routers.py`, `grep -n "^def timed_node\|^def build_graph\|^def run_graph"
   src/meridian/agent/graph.py`, `ls tests/graph/_spine_doubles.py` all print. Else → `blocked-on AEA-21`.
2. `grep -n "^class SpecialistTask\|^class KnowledgeSlice\|^class AccountSlice" src/meridian/domain/tools.py` prints all
   three (AEA-35b; `git log --oneline main | grep -i "35b"` shows its merge). `SpecialistTask` must have exactly the fields
   `task`, `customer_text`, `task_messages`, `slice`, `offer_quick_checks`, and `KnowledgeSlice()` / `AccountSlice()` must
   construct with **no arguments** (check: `uv run python -c "from meridian.domain.tools import KnowledgeSlice,
   AccountSlice, SpecialistTask; print(KnowledgeSlice(), AccountSlice(), sorted(SpecialistTask.model_fields))"`). Else →
   `blocked-on AEA-35b` (if the slices need constructor arguments, that is a plan change: return to the planner).
   `pending_change` is **not** checked (PD-13).
3. `grep -n "^def scope_for" src/meridian/agent/specialists/runner.py` prints. Else → `blocked-on AEA-35`.
4. `uv run python -c "import meridian.agent.graph"` succeeds (import check; no baseline suite).

**Step 1 — module skeleton.** Write the imports, constants and `__all__` of §4.4 into `act.py`, keep the three stubs
raising for now. Check: `uv run ruff check src/meridian/agent/nodes/act.py` and `uv run mypy src/meridian/agent/nodes/act.py`.

**Step 2 — `build_specialist_task` (pure) and its helpers.** Numbered rules, with the invariant each protects:

1. `customer_text = redact(state.turn_input.text_store, RedactionProfile.SONNET).text`. *Protects:* codes, card-like numbers,
   emails, street addresses and full phones never reach Sonnet (DO-4 §5 as superseded by data.md §1).
2. `task_messages = tuple(redact(t, RedactionProfile.SONNET).text for t in _task_message_texts(planned, state))` where
   `_task_message_texts(planned: PlannedTask, state: ConversationState) -> tuple[str, ...]` is (PD-1):
   1. `task = _open_task(planned, state)`; if `task is None` → `()`. (`_open_task` returns the `OpenTask` in
      `state.open_tasks` whose `task_id == planned.resumes_task_id`, or `None` when `resumes_task_id is None` or no match.)
   2. `lines = [line for line in state.chat_window if line.speaker == "customer" and line.turn_id is not None and
      line.turn_id != state.turn_input.turn_id]` (chat order is oldest first, as `load_context` builds it).
   3. `start` = index of the first line in `lines` whose `turn_id == task.opened_turn`; if no line matches, `start = 0`
      (the task opened before the oldest line kept in the window, so every kept customer line came after it).
   4. return `tuple(line.text for line in lines[start:])`.
   *Protects:* R-45 (only this task's own customer messages, never the assistant's or a representative's lines, never the
   chat window), and the current message is never sent twice (it is `customer_text`).
3. The slice, by `planned.specialist` (no `customer_id` anywhere; DO-4 §5):
   - `"knowledge"` → `KnowledgeSlice()`; `"account"` → `AccountSlice()`;
   - `"scheduling"` →
     ```python
     SchedulingSlice(
         customer_zone=None if scheduling is None else scheduling.zone,
         member=False if scheduling is None else scheduling.member,
         appointments=() if scheduling is None else scheduling.appointments,
         shown_slots=tuple(state.shown_slots),
         pending_change=_has_pending_change(state),                                        # PD-13
         bookings_left=max(0, limits.booking.max_per_conversation - state.counters.bookings),   # PA-1
     )
     ```
   `_has_pending_change(state: ConversationState) -> bool` is one line, `return getattr(state, "pending_change", None) is
   not None`, with the comment `# graph-nodes 9.5; ConversationState has no pending_change yet (AEA-02 8.2), so False
   until it lands`. Do not add the field, and do not write `state.pending_change` directly (mypy would reject it).
   Dispatch with a `match planned.specialist:` on the three literals (mypy checks exhaustiveness; no `else` branch needed —
   if mypy asks for one, add `case _: raise ValueError("unknown specialist")`).
4. `offer_quick_checks = _offers_quick_checks(planned, state)`, true only when **all** hold (graph-tools §6):
   1. `planned.specialist == "scheduling" and planned.intent is TaskIntent.BOOK_NEW and planned.resumes_task_id is None`;
   2. `service = None if (task := _open_task(planned, state)) is None else task.details.service_type`;
      `service is None or service in QUICK_CHECK_SERVICE_TYPES` (PD-2);
   3. `state.gate is not None and state.gate.kind is GateKind.FREE_TEXT and not (state.danger is not None and
      state.danger.raised)`.
   *Protects:* the offer appears once, only on the turn a non-urgent repair booking opens; the burning-"no" booking
   (gate `BURNING_ANSWER`) and any danger turn never offer it.
5. `return SpecialistTask(task=planned, customer_text=..., task_messages=..., slice=..., offer_quick_checks=...)`.
   No I/O, no clock read, no `deps`. *Protects:* AC-16 purity; equal inputs → equal task.

Check: `uv run pytest tests/unit/agent/nodes/test_act.py -k "build_specialist_task or quick_check_offer" -q` once those
two tests exist (write them now, §7.1).

**Step 3 — `run_specialist`.**

```python
def run_specialist(payload, runtime, *, deps):
    ctx = runtime.context
    planned, state = payload["planned"], payload["state"]
    inputs = _slice_inputs(planned, state, deps)          # the ONLY I/O before the run; the service opens and closes its UoW
    task = build_specialist_task(planned, state, ctx, scheduling=inputs, limits=deps.limits)
    result: KnowledgeResult | AccountResult | SchedulingResult = deps.specialists.run(task, scope_for(state, ctx), ctx)
    update: SpecialistUpdate = {"specialist_results": [result]}
    if result.brake is not None:
        halt = Halt(reason=result.brake, node=_NODE, elapsed_ms=_elapsed_ms(ctx))
        update["halt"] = halt
        if result.brake in BRAKE_HALTS:
            update["check_events"] = (CheckEvent.from_halt(ctx.ids.turn_id, halt),)
            _signal(ctx, SignalName.BRAKE_FIRED, cause=result.brake.value, specialist=planned.specialist)
    elif result.status == "failed":
        cause = "tool_error" if result.failure is None else result.failure.kind.value
        _signal(ctx, SignalName.SPECIALIST_FAILED, cause=cause, specialist=planned.specialist)
    return update
```

Helpers:

- `_slice_inputs(planned, state, deps) -> SchedulingSliceInputs | None`: `None` unless `planned.specialist == "scheduling"`
  and `state.identity.status == "verified"` and `state.identity.customer_id is not None`; then
  `inputs: SchedulingSliceInputs = deps.scheduling.slice_inputs(state.identity.customer_id)`; `return inputs` (assign to a
  typed local first: `deps.scheduling` is `Any`, and strict mypy rejects returning `Any`).
- `_elapsed_ms(ctx) -> int`: `max(0, int((time.monotonic() - ctx.budget.started) * 1000))` (PD-8; the same arithmetic as
  AEA-21's recursion halt).
- `_signal(ctx, name, *, cause: str, specialist: SpecialistKind) -> None`:
  `emit_signal(ctx.ids, SignalRecord(name=name, turn_id=ctx.ids.turn_id, thread_id=ctx.ids.thread_id,
  request_id=ctx.ids.request_id, run_tag=ctx.ids.run_tag, node=_NODE, cause=cause, role="specialist",
  specialist=specialist))` (PD-10). Codes only: never task text, report text or a result value.

Invariants: (a) **no `deps.uow` call anywhere in `act.py`** (DO-3 §2.3 rule 1; AC-12); (b) a brake outside `BRAKE_HALTS`
(`DEADLINE`, `PROVIDER_SPEND_CAP`, `SPEND_CAP`, anything else) writes the halt only — never call `CheckEvent.from_halt` for it
(it raises for three of them) and never signal it (PD-9); (c) a result with a brake never also emits `specialist_failed`;
(d) the runner is called exactly once per payload; nothing is retried here.

Check: `uv run pytest tests/unit/agent/nodes/test_act.py -k "fanout or brakes or no_uow" -q`.

**Step 4 — `escalation`.**

```python
def escalation(state, runtime, *, deps):
    gate = state.gate
    if gate is None:
        raise ValueError("escalation node: no gate decision")
    inputs = EscalationInputs(
        gate=gate, plan=state.plan, results=tuple(state.specialist_results), counters=state.counters,
        identity=state.identity, halt=state.halt, models_disabled=deps.ledger.models_disabled(),
        now=runtime.context.now,
    )
    return {"escalation": decide_escalation(inputs)}
```

No rule logic here: first-match order, rule ids and priorities are AEA-14's. Return only the `escalation` key (AC-8: no
account data in the update). Check: `-k "wp7 or wp8 or rule6 or not_verified or two_misses" -q`.

**Step 5 — `handoff`.**

```python
def handoff(state, runtime, *, deps):
    ctx = runtime.context
    request = _handoff_request(state, ctx)
    if request is None:
        return {}
    result: HandoffResult = deps.handoff.open(request, ctx)
    return {"handoff": result}
```

`_handoff_request(state, ctx) -> HandoffRequest | None`, first match:

1. `decision = state.escalation`; if `decision is not None and decision.outcome == "escalate"`: if `decision.reason is None
   or decision.priority is None` → `raise ValueError("escalate decision without reason or priority")`; else
   `HandoffRequest(thread_id=ctx.ids.thread_id, turn_id=ctx.ids.turn_id, reason=decision.reason,
   priority=decision.priority, rule_id=decision.rule_id, trigger="escalation", identity=state.identity,
   change_request=_change_request(state.specialist_results))`.
2. elif `state.gate is not None and state.gate.kind is GateKind.PERSON` (first ask, R-2; the gate path skipped
   `decide_escalation`): `reason = HandoffReason.CUSTOMER_REQUESTED_PERSON`; `HandoffRequest(thread_id=ctx.ids.thread_id,
   turn_id=ctx.ids.turn_id, reason=reason, priority=priority_for(reason), rule_id=PERSON_RULE_ID, trigger="gate",
   identity=state.identity)`.
3. else `None` (`offer` and `none` open nothing).

`_change_request(results: Sequence[KnowledgeResult | AccountResult | SchedulingResult]) -> ChangeRequestDraft | None`:
the `change_request` of the **first** `SchedulingResult` in `results` (list order = `PlannedTask.order`) whose `status ==
"staff_change_request"` and `change_request is not None`; else `None` (PA-3, PD-4).

Invariants: one `open` call per node run; the node never builds promise text, a due time, a reference or a priority of its
own (the only priority it computes is `priority_for(CUSTOMER_REQUESTED_PERSON)`, the policy function); ids come from
`ctx.ids` (PD-5); **do not catch** exceptions from `open` (PA-2, PD-6); never write `halt` here.

Check: `-k "wp4 or person or second_handoff or model_text or propagates" -q`.

**Step 6 — remaining unit tests.** Write the rest of §7.1 (`test_act_nodes_write_only_own_keys`,
`test_escalation_record_fields_and_case_per_escalate`). Check: `uv run pytest tests/unit/agent/nodes/test_act.py -q` →
all 17 pass (AC-6 counts 4 parametrised cases, so pytest reports 20).

**Step 7 — AEA-21 regression.** `uv run pytest tests/graph tests/unit/agent -q` (AEA-21's spine tests patch the act
functions with doubles; they must stay green with the real bodies in place).

**Step 8 — journeys (AC-15).** Write `tests/journeys/j3/test_aea_39.py` and `tests/journeys/j4/test_aea_39.py` (§7.1, §6.3).
Check: `uv run pytest -m journey tests/journeys/j3/test_aea_39.py tests/journeys/j4/test_aea_39.py -q` (2 pass) and
`uv run python -m tests.journeys.affected --base main` (lists and runs both).

**Step 9 — gates, commit 1, context docs, commit 2.**

1. Run §7.2 in order; all green.
2. Commit 1 (code and tests only):
   `git add src/meridian/agent/nodes/act.py tests/unit/agent/nodes/test_act.py tests/unit/agent/nodes/act_fixtures.py
   tests/journeys/j3/test_aea_39.py tests/journeys/j4/test_aea_39.py`
   Message: `feat(graph): act node — specialist fan-out, escalation, handoff (AEA-39)`, a short body (what each node does,
   the test counts), last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Note its short SHA as `<sha>`.
3. Context docs (AC-17), each a one-line change:
   - `.claude/reference/area-map.md`, row `| 3 | **A7b Act** | …`: in the last cell, after
     ``…`policy/escalation.py` actual (AEA-14, `af848c9`; built in wave 1, slice plan §2)`` append
     ``; `agent/nodes/act.py` actual (AEA-39, `<sha>`)``. Change nothing else in the row (AEA-22 and AEA-35 edit the same row).
   - `.claude/state/icm-progress.md`: add one row directly after the last existing `| Routes verified against code and
     tests |` row: `| Routes verified against code and tests | provisional | <run-date>: area map A7b → `agent/nodes/act.py`
     checked against `tests/unit/agent/nodes/test_act.py` (AEA-39, `<sha>`; <N> passed) | Each slice adds its route; verified
     when every area-map row is actual |` (≤ 400 characters; `<N>` from your run).
   - `docs/design/code-design.md` §3, the line `│   ├── nodes/act.py …  A7b   3   stub AEA-21 6df4f4c`: replace the suffix
     `stub AEA-21 6df4f4c` with `built AEA-39 <sha>` (if the line has no suffix, append `   built AEA-39 <sha>`).
   - Create `docs/testing/journeys/<run-date>-AEA-39.md` (§7.4).
4. Commit 2: `git add .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md
   docs/testing/journeys/<run-date>-AEA-39.md`; message `docs(AEA-39): journey record and context for agent/nodes/act.py`,
   last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
5. `git diff --name-only main...HEAD` lists exactly the nine owned files (§2.1). Do not push; the merge step pushes `main`.

---

## 6. Data and fixtures (synthetic or worked-pair values only)

### 6.1 Values

| Name | Value | Source |
|---|---|---|
| `T1`, `T2`, `T3` | `TurnId("1f0e2d3c-4b5a-4c69-8a7b-6c5d4e3f2a10")`, `TurnId("2a3b4c5d-6e7f-4a8b-9c0d-1e2f3a4b5c6d")`, `TurnId("3b4c5d6e-7f80-4a9b-8c1d-2e3f4a5b6c7d")` | synthetic UUID4s (lowercase hex; third group starts `4`, fourth `8`/`9`/`a`/`b`) |
| `THREAD`, `REQ` | import from `tests.graph._spine_doubles` | AEA-21 |
| `NOW` | `tests.fakes.WORKED_PAIRS_NOW` (Fri 2026-10-16 10:00 America/Chicago) | AEA-11; worked pairs |
| WP-4 customer | `CustomerId("MHC-57204")`, zone `"central"`, not a member | worked-pairs WP-4 |
| WP-4 appointment | `AppointmentView(appointment_id=1, date=date(2026, 10, 16), window="12:00-16:00", service_type="hvac_tune_up", technician=None, is_warranty_visit=False)` | WP-4 ("appointment 1 today, 12pm–4pm") |
| WP-4 draft | `ChangeRequestDraft(appointment_id=1, change="move", wanted_text="Monday morning", windows_shown=(), hours_before=2.0, window_start=datetime(2026, 10, 16, 12, 0, tzinfo=CHICAGO))` | WP-4 |
| WP-4 text | `"I have a tech coming but something came up. Can I move it?"` | WP-4 input |
| WP-7 text | `"I want a full refund on the repair. It didn't fix anything and I had to call another company."` | WP-7 input |
| WP-8 | `CustomerId("MHC-10001")`; `MembershipView(tier="standard", renewal_date=date(2026, 11, 3))`; variant renewal `date(2026, 10, 19)` → P2 | WP-8; cases §3.4 residual note |
| Card-like number (AC-16 only) | built at run time: `card = " ".join(["4242"] * 4)` | synthetic; never a literal |
| Phone (AC-16 only) | built at run time: `phone = "-".join(("512", "555", "01" + "40"))` | synthetic; never a literal |
| Model text (AC-11) | report point text `"we'll refund you, ref " + "MHC-C-" + "9999"` | synthetic |

No six-digit code, card-like number or full phone number appears as a literal anywhere.

### 6.2 `tests/unit/agent/nodes/act_fixtures.py` (module docstring: `"""Builders and doubles for the AEA-39 act-node tests.
Synthetic values only."""`)

Import the real node functions **at module import time, before any test patches them**:
`from meridian.agent.nodes.act import escalation as real_escalation, handoff as real_handoff, run_specialist as
real_run_specialist`.

Builders (plain functions, keyword-only options, all values from §6.1):

```python
def act_ctx(turn_id: TurnId = T1, *, now: datetime = WORKED_PAIRS_NOW, thread: ThreadId = THREAD) -> TurnContext
    # started = time.monotonic(); TurnContext(ids=TurnIds(thread_id=thread, turn_id=turn_id, request_id=REQ,
    #   run_tag="live", run_id=None, agent_version="test"), budget=TurnBudget(started=started, deadline=started + 60.0),
    #   now=now, demo_session="demo-session-1", span=SpanHandle(turn_id=turn_id, trace_id=None))
def rt(ctx: TurnContext) -> Runtime[TurnContext]          # Runtime(context=ctx)  (langgraph.runtime; other fields default)
def gate(kind: GateKind = GateKind.FREE_TEXT, *, policy: HandoffReason | None = None,
         burning_answer: Literal["yes", "no", "unsure"] | None = None) -> GateDecision
    # rules = no_rules() with policy_trigger=policy and person=(kind is GateKind.PERSON) (model_copy(update=...))
def verified(customer: str = "MHC-57204") -> IdentityState
    # status="verified", customer_id=CustomerId(customer), masked_hint=None, code_expires_at=None, tries_left=3,
    # codes_sent=1, verified_at=WORKED_PAIRS_NOW
def unverified(status: Literal["not_verified", "locked", "not_checked"]) -> IdentityState
    # customer_id=None, masked_hint=None, code_expires_at=None, tries_left=0 if status == "locked" else 3,
    # codes_sent=1, verified_at=None
def task(order: int, specialist: SpecialistKind, intent: TaskIntent, *, needs_identity: bool | None = None,
         resumes: str | None = None) -> PlannedTask   # needs_identity defaults to (specialist != "knowledge")
def act_plan(*tasks: PlannedTask, handoff_request: HandoffReason | None = None, topic: Topic = "booking") -> Plan
    # Plan(mode="act", tasks=tasks, handoff_request=handoff_request, topic=topic, source="planner")
def talk_plan() -> Plan                                    # mode="talk", tasks=(), handoff_request=None, topic="other"
def make_state(*, turn_id: TurnId = T1, text: str = "Hello", gate_: GateDecision | None = None, plan: Plan | None = None,
               identity: IdentityState | None = None, results: Sequence[SpecialistResult] = (),
               counters: FailureCounters | None = None, halt: Halt | None = None, danger: DangerAssessment | None = None,
               open_tasks: Sequence[OpenTask] = (), chat: Sequence[ChatLine] = (),
               escalation: EscalationDecision | None = None) -> ConversationState
    # ConversationState(thread_id=THREAD, settled=Settled(actions=(), open_case=None, read_at=WORKED_PAIRS_NOW),
    #   identity=identity or verified(), turn_input=TurnInput(turn_id=turn_id, message_id=412, kind="text",
    #   text_store=text, received_at=WORKED_PAIRS_NOW), gate=gate_ or gate(), plan=plan,
    #   specialist_results=list(results), counters=counters or FailureCounters(), halt=halt, danger=danger,
    #   open_tasks=list(open_tasks), chat_window=list(chat), escalation=escalation)
def apply(state: ConversationState, update: Mapping[str, Any]) -> ConversationState
    # the graph's reducers, for chaining nodes in unit tests:
    # specialist_results → [*old, *new]; check_events → add_turn_events(old, new); halt → first_halt(old, new);
    # every other key replaces; return state.model_copy(update=merged)
def knowledge(status="answered", *, brake=None, failure=None, points=()) -> KnowledgeResult   # passages=(), tools=(), calls=()
def account(status="read", *, renewal: date | None = None, brake=None, failure=None) -> AccountResult
    # membership=MembershipView(tier="standard", renewal_date=renewal) when renewal is given, else None
def scheduling(status="windows_shown", *, change_request=None, write=None, brake=None, failure=None) -> SchedulingResult
def failure(kind: ProviderFailureKind = ProviderFailureKind.TIMEOUT) -> ProviderFailure
    # provider="anthropic", http_status=None, retry_after_s=None, retryable=True, provider_request_id=None
WP4_APPOINTMENT, WP4_DRAFT, WP4_INPUTS (= SchedulingSliceInputs(zone="central", member=False, appointments=(WP4_APPOINTMENT,)))
WP4_TEXT, WP7_TEXT        # the §6.1 WP-4 and WP-7 texts, as module constants (unit tests and J-4 use them)
def booked_write(turn_id: TurnId) -> WriteResult    # J-3 only, synthetic:
    # WriteResult(action=CompletedAction(key=ActionKey(thread_id=THREAD, turn_id=turn_id, kind=ActionKind.BOOKED,
    #   record_id="101"), kind=ActionKind.BOOKED, records={"appointment": "101", "slot": "4401"}, at=WORKED_PAIRS_NOW),
    #   confirmation=ConfirmationView(date=date(2026, 10, 19), window="08:00-12:00", technician="Technician One",
    #   fee_note=FeeNote(service_type="hvac_repair", tier="none", fee_row=None, amount_cents=8900, waived=False,
    #   line="Synthetic test line: diagnostic fee")))
```

Doubles:

```python
class UowCounter:                    # a UnitOfWorkFactory double: counts open units of work
    open_count: int = 0; entered: int = 0
    @contextlib.contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[object]:
        # open_count += 1; entered += 1; try: yield object() finally: open_count -= 1

class SchedulingDouble:              # SchedulingService.slice_inputs only — it has NO write method
    def __init__(self, inputs: SchedulingSliceInputs = WP4_INPUTS, *, uow: UowCounter | None = None) -> None
    calls: list[str]; customer_ids: list[CustomerId]
    def slice_inputs(self, customer_id: CustomerId) -> SchedulingSliceInputs:
        # calls.append("slice_inputs"); customer_ids.append(customer_id);
        # if uow is not None: `with self.uow(): pass`  (opens and closes a read, like the service); return inputs

class RunnerDouble:                  # SpecialistRunner.run
    def __init__(self, results: Mapping[SpecialistKind, SpecialistResult], *,
                 delays: Mapping[SpecialistKind, float] | None = None, uow: UowCounter | None = None) -> None
    calls: list[tuple[SpecialistTask, ToolCallScope, TurnContext]]; uow_open_at_call: list[int]
    def run(self, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext) -> SpecialistResult:
        # calls.append((task, scope, ctx)); if uow: uow_open_at_call.append(uow.open_count);
        # time.sleep(delays.get(task.task.specialist, 0.0)); return results[task.task.specialist]

class LedgerDouble:                  # ModelsStatus
    def __init__(self, disabled: bool = False) -> None;  calls: int
    def models_disabled(self) -> bool  # calls += 1; return disabled

class GatewayDouble:                 # fails loudly if any gateway method is used
    accessed: list[str]
    def __getattr__(self, name: str) -> Any:
        # if name.startswith("_"): raise AttributeError(name)
        # accessed.append(name); raise AssertionError(f"gateway.{name} used")

class HandoffDouble:                 # HandoffService.open, built on the REAL policy functions (AEA-14)
    def __init__(self, presence: Presence = "nobody_online", *, error: Exception | None = None) -> None
    requests: list[HandoffRequest]
    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult:
        # requests.append(req); if error: raise error
        # key = (req.thread_id, req.turn_id); a key seen before → return the stored result (idempotent per turn)
        # thread already has an open case → stored = that result.model_copy(update={"created": False}); store under key
        # else: window_start = req.change_request.window_start if req.change_request else None
        #   promise = promise_for(req.reason, presence, ctx.now, window_start)
        #   ref = CaseRef(f"MHC-C-{n:04d}") with n = 1, 2, … per new case
        #   case = CaseSummary(case_ref=ref, reason=req.reason, priority=req.priority, state="unassigned",
        #          created_at=ctx.now, promise=promise, followup=None, version=1,
        #          due_at=case_due_at(req.reason, promise, window_start))
        #   action = CompletedAction(key=ActionKey(thread_id=req.thread_id, turn_id=req.turn_id,
        #          kind=ActionKind.CASE_OPENED, record_id=str(ref)), kind=ActionKind.CASE_OPENED,
        #          records={"case": str(ref)}, at=ctx.now)
        #   alert = "supervisor_now" if req.priority in (Priority.P0, Priority.P1)
        #           or req.reason is HandoffReason.FEE_BEARING_CHANGE else None
        #   result = HandoffResult(case=case, created=True, action=action, alert=alert); store as open and under key
```

Graph helpers:

```python
def deps_for(*, runner: RunnerDouble, scheduling_: SchedulingDouble | None = None, handoff_: Any = None,
             ledger: LedgerDouble | None = None, gateway: GatewayDouble | None = None,
             uow: UowCounter | None = None) -> GraphDeps
    # handoff_ is a HandoffDouble in unit tests, or AEA-29's real HandoffService in J-4 (typed Any; GraphDeps.handoff is Any)
    # dataclasses.replace(make_deps(RecordingSink()), gateway=cast("ModelGateway", gateway or GatewayDouble()),
    #   uow=cast(UnitOfWorkFactory, uow or UowCounter()), specialists=runner, scheduling=scheduling_ or SchedulingDouble(),
    #   handoff=handoff_ or HandoffDouble(), ledger=ledger or LedgerDouble())

def fanout_graph(deps: GraphDeps) -> CompiledGraph        # AC-1: Send fan-out only, production node wrapper
    # builder: StateGraph[Any, Any, Any, Any] = StateGraph(ConversationState, context_schema=TurnContext)
    # node: Any = timed_node("run_specialist", cast(NodeFn, functools.partial(real_run_specialist, deps=deps)), deps)
    # builder.add_node("run_specialist", node)
    # builder.add_conditional_edges(START, route_act_plan, ["run_specialist"])
    # builder.add_edge("run_specialist", END); return builder.compile()

def state_input(state: ConversationState) -> dict[str, Any]   # {name: getattr(state, name) for name in ConversationState.model_fields}

@dataclass
class ActHarness:                    # the REAL build_graph with the real act nodes and AEA-21's doubles elsewhere
    graph: CompiledGraph; deps: GraphDeps; composer: ReplyComposer; visits: list[str]; thread: ThreadId = THREAD
    def run(self, turn_id: TurnId, text: str, *, now: datetime = WORKED_PAIRS_NOW) -> GraphOutcome:
        # run_graph(self.graph, make_input(turn_id, text), act_ctx(turn_id, now=now, thread=self.thread), deps=self.deps,
        #           composer=self.composer)
    def values(self) -> dict[str, Any]:   # dict(self.graph.get_state({"configurable": {"thread_id": str(self.thread)}}).values)

def act_harness(monkeypatch: pytest.MonkeyPatch, deps: GraphDeps, *, thread: ThreadId = THREAD,
                **overrides: Callable[..., Any]) -> ActHarness
    # visits: list[str] = []
    # install_doubles(monkeypatch, visits, run_specialist=real_run_specialist, escalation=real_escalation,
    #                 handoff=real_handoff, **overrides)
    # composer = ReplyComposer(); graph = build_graph(deps, checkpointer=InMemorySaver(), composer=composer)
    # return ActHarness(graph, deps, composer, visits, thread)

def verified_load_context(customer: str) -> Callable[..., Any]   # an override for "load_context"
    # (state, runtime, *, deps) -> {"settled": Settled(actions=(), open_case=None, read_at=runtime.context.now),
    #   "chat_window": [ChatLine(speaker="customer", text="hello", turn_id=runtime.context.ids.turn_id,
    #   at=runtime.context.now)], "identity": verified(customer)}
def plan_join_returning(plans: Mapping[TurnId, Plan]) -> Callable[..., Any]      # an override for "plan_join"
    # (state, runtime, *, deps) -> {"plan": plans[runtime.context.ids.turn_id]}
def gates_returning(decision: GateDecision) -> Callable[..., Any]                # an override for "gates"
    # -> {"gate": decision, "check_events": (CheckEvent.from_gate(runtime.context.ids.turn_id, decision),)}
```

Imports for these helpers: `functools`, `contextlib`, `dataclasses`, `time`; `from langgraph.checkpoint.memory import
InMemorySaver`; `from langgraph.graph import END, START, StateGraph`; `from meridian.agent.graph import CompiledGraph, NodeFn,
build_graph, run_graph, timed_node`; `from meridian.agent.routers import route_act_plan`; `from meridian.agent.nodes.compose
import ReplyComposer`; `from tests.graph._spine_doubles import REQ, THREAD, RecordingSink, install_doubles, make_deps,
make_input, no_rules`; `from tests.fakes import CHICAGO, WORKED_PAIRS_NOW`; policy `promise_for`, `case_due_at`. Use
`TYPE_CHECKING` for `ModelGateway` as `_spine_doubles.py` does.

### 6.3 Journey scenarios (mock-tested; the doubles are §6.2's)

- **J-3** `tests/journeys/j3/test_aea_39.py::test_j3_booking_write_then_yes_please_no_new_write`: module docstring states
  the level (`mock-tested`: real `build_graph`, real act nodes, AEA-21's doubles for the other nodes, no server, no DB) and
  that the integrated steps (confirmation card on screen, appointment row stored, the follow-up reply naming the new
  window) are blocked by AEA-51 (it wires the graph into AEA-40's merged CON-2 `submitTurn` on AEA-57's harness).
  `pytestmark = pytest.mark.journey`. Runner: `{"scheduling":
  scheduling("written", write=booked_write(T1))}`. Overrides: `load_context=verified_load_context("MHC-57204")`,
  `plan_join=plan_join_returning({T1: act_plan(task(1, "scheduling", TaskIntent.BOOK_NEW)), T2: talk_plan()})`.
  Turn 1 `"My AC stopped cooling, can someone come out Monday morning?"` → after it, `h.values()["escalation"].outcome ==
  "none"`, `[r.kind for r in h.values()["specialist_results"]] == ["scheduling"]`, the result's `write.action.kind is
  ActionKind.BOOKED`, `out1.turn_trace.specialists_run == ("scheduling",)`. Turn 2 `"Yes, please."` →
  `out2.turn_trace.specialists_run == ()`, `"run_specialist"` appears once in `h.visits` over both turns, `len(runner.calls)
  == 1`, `handoff.requests == []`, `scheduling_double.calls == ["slice_inputs"]`.
- **J-4** `tests/journeys/j4/test_aea_39.py::test_j4_wp4_fee_bearing_change_p2_case_policy_promise(monkeypatch)`:
  docstring states the level (`mock-tested`: real `build_graph`, real act nodes, **AEA-29's real `HandoffService` and
  `CaseService` on a temp SQLite copy of the issued DB**, AEA-21's doubles for the other nodes, runner and scheduling
  doubles, no server, no model) and that the integrated steps (the CON-2 response and the case on screen through the
  wired turn) are blocked by AEA-51. `pytestmark = pytest.mark.journey`. Imports beyond §6.2's: `hashlib`; `from
  tests.fixtures.sqlite import ISSUED_DB, temp_sqlite`; `from tests.services._case_fixtures import new_thread, services,
  summary_of`; `from meridian.domain.blocks import HandoffBlock`; `from meridian.policy.handoff import PROMISE_TABLE,
  promise_for`. Steps, in this order (PD-14):
  1. `issued_before = hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest()`.
  2. `with temp_sqlite() as db:` then, inside it:
     - `with db.uow(write=True) as tx: thread, _ = new_thread(tx, customer_text=WP4_TEXT); tx.commit()` (the conversation
       row the case needs; `new_thread` makes a fresh UUID4 thread);
     - `with db.uow() as tx: appt_before = tx.booking.appointments.get(1)`;
     - `_, handoff_svc, _, _ = services(db.uow)` (`FixedClock(WORKED_PAIRS_NOW)`; presence from the DB, default
       `nobody_online`);
     - `runner = RunnerDouble({"scheduling": scheduling("staff_change_request", change_request=WP4_DRAFT)})`,
       `sched = SchedulingDouble()`, `deps = deps_for(runner=runner, scheduling_=sched, handoff_=handoff_svc)`;
     - `h = act_harness(monkeypatch, deps, thread=thread, load_context=verified_load_context("MHC-57204"),
       plan_join=plan_join_returning({T1: act_plan(task(1, "scheduling", TaskIntent.RESCHEDULE))}))`;
     - `out = h.run(T1, WP4_TEXT)`; `values = h.values()`; `result = values["handoff"]`;
     - `with db.uow() as tx: stored = summary_of(tx, result.case.case_ref); appt_after = tx.booking.appointments.get(1)`.
  3. Assert (after the `with` block; keep the values in locals):
     - the runner got one task whose `slice` is a `SchedulingSlice` with `customer_zone == "central"`, `member is False`,
       `appointments == (WP4_APPOINTMENT,)`; `sched.calls == ["slice_inputs"]` (the double has no write method);
     - `values["escalation"]` has `outcome == "escalate"`, `reason is HandoffReason.FEE_BEARING_CHANGE`, `priority is
       Priority.P2`, `rule_id == "R21.fee_bearing"`;
     - `result.created is True`, `result.alert == "supervisor_now"`;
     - **what is stored:** `stored.reason is HandoffReason.FEE_BEARING_CHANGE`, `stored.priority is Priority.P2`,
       `stored.due_at == WP4_DRAFT.window_start` (case due = window start, CAS-10), `stored.promise.policy_row ==
       "R26.unstaffed"`, `stored.promise.text == PROMISE_TABLE["R26.unstaffed"]`, `stored.promise.due_label == "Monday,
       October 19, 7:00 pm"`, `len(stored.promise.extra_lines) == 2`, and `stored.promise == promise_for(
       HandoffReason.FEE_BEARING_CHANGE, "nobody_online", WORKED_PAIRS_NOW, WP4_DRAFT.window_start)`;
     - `appt_after == appt_before` (the appointment row is untouched) and
       `hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest() == issued_before`;
     - **what the user sees:** exactly one `HandoffBlock` in `out.reply.blocks`, with `promise_text ==
       PROMISE_TABLE["R26.unstaffed"]` and `reference == str(result.case.case_ref)`; `out.turn_trace.outcome ==
       "handed_off"`.
  If an assertion on the composed reply fails because compose renders the block differently (for example the reference
  format), read `nodes/compose.py`, match what it renders and say so in the report; never edit compose (G-5). If the
  stored promise differs from `promise_for(...)`, stop and report it: that is a seam finding against AEA-29, not a reason
  to loosen the assertion.

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (names are binding)

`tests/unit/agent/nodes/test_act.py` (imports from `tests.unit.agent.nodes.act_fixtures`; signals captured with
`caplog.set_level(logging.INFO, logger="meridian.signal")` and read as `r.__dict__["signal"]` for `r in caplog.records if
r.name == "meridian.signal"`, the pattern AEA-21's `test_spine.py` uses):

| Test | Setup → assertions |
|---|---|
| `test_fanout_three_tasks_parallel` (AC-1) | State: `verified()`, plan `act_plan(task(1,"account",READ_INVOICE), task(2,"scheduling",BOOK_NEW), task(3,"knowledge",ANSWER_QUESTION))`. Runner results `{account: account(), scheduling: scheduling(), knowledge: knowledge()}`, delays `{account: 0.9, scheduling: 0.6, knowledge: 0.3}` (completion order is the reverse of `order`). `graph = fanout_graph(deps)`; run `graph.invoke(state_input(state), context=ctx)` inside a `threading.Thread` and `join()` (as AEA-21's timing test does), timing it with `time.monotonic()`. Assert: `len(runner.calls) == 3`; `elapsed < 1.5` (serial would be ≥ 1.8; print it); `[r.kind for r in ConversationState.model_validate(out).specialist_results] == ["account", "scheduling", "knowledge"]`; every recorded scope `== scope_for(state, ctx)`; `scheduling_double.customer_ids == [CustomerId("MHC-57204")]` (one read, scheduling task only) |
| `test_specialist_task_slices_and_quick_check_offer` (AC-2) | (a) Offer table, one `build_specialist_task` call per row on `make_state(gate_=…, danger=…)` with `scheduling=None`: scheduling/BOOK_NEW/no resume/FREE_TEXT/no danger → True; same with `danger=DangerAssessment(label="normal", raised=False, failure=None)` → True; resumes `"task-1"` → False; RESCHEDULE → False; knowledge/ANSWER_QUESTION → False; gate `BURNING_ANSWER` with `burning_answer="no"` → False; `danger.raised=True` (label `"danger"`) → False; gate `CARD_CHOICE` → False. (b) Scheduling task with `WP4_INPUTS`: `"MHC-57204" not in task.model_dump_json()`; `"chat_window" not in task.model_dump()`; an assistant line in `chat` (`"assistant text"`) is absent from the JSON. (c) Knowledge task: `isinstance(task.slice, KnowledgeSlice)`, `set(task.slice.model_dump()) <= {"kind"}`, `task.customer_text` set, `task.task_messages == ()`. (d) `scope_for(make_state(identity=unverified("not_verified")), ctx).customer_id is None`; with `verified()` it is `CustomerId("MHC-57204")` |
| `test_wp4_fee_bearing_escalates_p2` (AC-3, PA-3) | WP-4 state (`verified()`, plan RESCHEDULE task, text WP-4). `run_specialist` with runner `{scheduling: scheduling("staff_change_request", change_request=WP4_DRAFT)}` → `apply`; `escalation` → `apply`; `handoff`. Assert decision `("escalate", FEE_BEARING_CHANGE, P2, "R21.fee_bearing", False)`; `len(handoff.requests) == 1` with `reason`, `priority`, `rule_id`, `trigger == "escalation"`, `change_request == WP4_DRAFT`, `identity == verified()`; returned update `{"handoff": <the double's result>}`; `scheduling_double.calls == ["slice_inputs"]` |
| `test_wp7_refund_p3` (AC-4) | Monkeypatch `meridian.agent.nodes.act.decide_escalation` with a wrapper that appends its `inputs` to a list and returns the real `decide_escalation(inputs)`. State: WP-7 text, `gate(policy=HandoffReason.REFUND)`, plan `Plan(mode="act", tasks=(), handoff_request=HandoffReason.REFUND, topic="billing", source="rules_only")`. Assert decision `reason is REFUND`, `priority is P3`, `rule_id == "R24.refund"`; `recorded[0].now == ctx.now`. Then `handoff` with `HandoffDouble()`: `case.promise.text == PROMISE_TABLE["R26.refund"]`, `due_label == "Tuesday, October 20, 7:00 pm"` |
| `test_wp8_membership_cancel_d4` (AC-4) | Same recording wrapper. `verified("MHC-10001")`; plan `act_plan(task(1,"account",READ_MEMBERSHIP), handoff_request=MEMBERSHIP_CANCEL, topic="membership")`; results `(account(renewal=date(2026, 11, 3)),)` → `rule_id == "D4.membership_cancel"`, `P3`, `recorded[0].now == ctx.now`. Variant renewal `date(2026, 10, 19)` → `P2` |
| `test_person_gate_first_ask` (AC-5) | `act_harness` with `gates=gates_returning(gate(GateKind.PERSON))`, `GatewayDouble()`, runner with no results needed (`{}`), `HandoffDouble()`. One turn (`"Can I talk to a person?"`). Assert `handoff.requests` has one request: `reason is CUSTOMER_REQUESTED_PERSON`, `priority is P3`, `rule_id == "R2.person"`, `trigger == "gate"`; `runner.calls == []`; `gateway.accessed == []`; `"planner" not in h.visits`, `"run_specialist" not in h.visits`, `"escalation" not in h.visits`, `"handoff" in h.visits`; `out.turn_trace.outcome == "handed_off"` |
| `test_rule6_degraded_handoff` (AC-6) | `@pytest.mark.parametrize` ids `halt`, `specialist_failed`, `models_disabled`, `planner_failed`. Common: `verified()`, FREE_TEXT gate. `halt`: plan with a knowledge task, `halt=Halt(reason=BRAKE_TOOL_ROUNDS, node="run_specialist", elapsed_ms=5)` → `AI.halt`. `specialist_failed`: results `(knowledge("failed"),)` → `AI.specialist_failed`. `models_disabled`: `LedgerDouble(disabled=True)`, results `(knowledge(),)` → `AI.models_disabled`. `planner_failed`: plan `Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)` → `AI.planner_failed`. Each: `escalation` then `handoff` with a fresh `HandoffDouble`; decision `("escalate", AI_FAILURE, P3, <id>, True)`; exactly one request, `reason is AI_FAILURE`, `trigger == "escalation"` |
| `test_brakes_and_failures_emit_events_and_signals` (AC-7) | One knowledge task, `run_specialist` per case, fresh `caplog` read per case (`caplog.clear()`). (a) `knowledge("failed", brake=BRAKE_TOOL_ROUNDS)` → `update["halt"].reason is BRAKE_TOOL_ROUNDS`, `.node == "run_specialist"`, `update["check_events"] == (CheckEvent(check="brake", turn_id=T1, result="fired", codes=("brake_tool_rounds", "run_specialist")),)`, signals `[("brake_fired", "brake_tool_rounds")]` (name, cause), and the record's `role == "specialist"`, `specialist == "knowledge"`. (b) `brake=DEADLINE` → halt present, `"check_events" not in update`, no signal. (c) `brake=PROVIDER_SPEND_CAP` → same as (b). (d) `knowledge("failed", failure=failure(TIMEOUT))` → no halt, no events, signals `[("specialist_failed", "timeout")]`. (e) `knowledge("failed")` (failure None) → `[("specialist_failed", "tool_error")]`. (f) `knowledge()` → `set(update) == {"specialist_results"}`, no signal |
| `test_not_verified_escalates_reveals_nothing` (AC-8) | For `status in ("not_verified", "locked")`: `identity=unverified(status)`, plan `act_plan(task(1,"account",READ_INVOICE))`, no results → decision `("escalate", IDENTITY_UNVERIFIED, P3, "R16.identity_unverified", False)`; `set(update) == {"escalation"}`; `"INV-" not in json.dumps(update["escalation"].model_dump(mode="json"))` |
| `test_two_misses_or_timeouts_offer` (AC-9) | `counters=FailureCounters(failed_answers=2)` → `("offer", "OD6.two_misses")`; `corrections=2` → `OD6.two_misses`; `timeouts=2` → `OD6.two_timeouts` (talk plan, verified, FREE_TEXT). For each, `handoff(apply(state, update), …)` returns `{}` and `HandoffDouble.requests == []` |
| `test_second_handoff_same_reference` (AC-10) | One shared `HandoffDouble`. Turn `T1`: WP-7 refund state → `handoff` → `created is True`, ref `r1`. Turn `T2`: state with `escalation=EscalationDecision(outcome="escalate", reason=LATE_TECHNICIAN, priority=P2, rule_id="D4.late_technician")` (ctx `T2`) → `created is False`, `case.case_ref == r1`. Repeat turn `T2` (same state, same ctx) → `requests[2] == requests[1]` and the two returned `action.key`s are equal; one distinct `case_ref` across all three |
| `test_handoff_request_has_no_model_text` (AC-11) | `secret = "we'll refund you, ref " + "MHC-C-" + "9999"`. Runner returns `knowledge("failed", points=(KnowledgePoint(text=secret, passage_id=PassageId("faq/customer_faq.md#1")),))` → `run_specialist` (emits `specialist_failed`) → `escalation` (rule 6) → `handoff`. Assert `secret` and `"MHC-C-9999"` absent from `requests[0].model_dump_json()`, from the `handoff` result JSON, from every check-event JSON in the state, and from `json.dumps` of every `meridian.signal` record; at least one signal record exists |
| `test_no_uow_during_specialists` (AC-12) | `uow = UowCounter()`; `SchedulingDouble(uow=uow)`, `RunnerDouble(..., uow=uow)`, `deps_for(..., uow=uow)`. Run `run_specialist` for a verified scheduling task → `uow.entered == 1` (the service's read), `runner.uow_open_at_call == [0]`. Also read `src/meridian/agent/nodes/act.py` as text: `"uow(" not in source` and `"deps.uow" not in source` |
| `test_act_nodes_write_only_own_keys` (AC-13) | `allowed = T.__required_keys__ | T.__optional_keys__` for each update TypedDict. `run_specialist` (plain, BRAKE_TOOL_ROUNDS, DEADLINE) ⊆ `SpecialistUpdate` keys and equal to `{"specialist_results"}`, `{"specialist_results", "halt", "check_events"}`, `{"specialist_results", "halt"}`; `escalation` → `{"escalation"}`; `handoff` escalate → `{"handoff"}`, offer → `set()` |
| `test_escalation_record_fields_and_case_per_escalate` (AC-14, PA-3) | Scenario states (one `HandoffDouble` each, results present where named): WP-4 (scheduling result), WP-7, WP-8, rule-6 failed knowledge, identity locked, offer (two misses), none (talk plan, no results). For each: `escalation` → `apply` → `handoff`. Assert every decision has a non-empty `rule_id` and a `bool` `degraded`; `reason` and `priority` are set exactly when `outcome == "escalate"`; `tuple(r.kind for r in state.specialist_results)` equals the scenario's kinds (`("scheduling",)` for WP-4); total `escalate` decisions == total `requests` across doubles (5 == 5); WP-7's request has `change_request is None` |
| `test_build_specialist_task` (AC-16, PA-1) | Built-at-runtime `card` and `phone` (§6.1). (a) Scheduling BOOK_NEW, `text = f"Book me Monday. Card {card}, call {phone}"`, `scheduling=WP4_INPUTS`, `counters=FailureCounters(bookings=1)`: `card not in json`, `phone not in json`, slice zone/member/appointments from `WP4_INPUTS`, `bookings_left == 2`, `pending_change is False`. (b) Same call twice → equal tasks. (c) `scheduling=None` → `customer_zone is None`, `member is False`, `appointments == ()`. (d) `bookings=5` → `bookings_left == 0`. (e) Resumed scheduling task: `open_tasks=[OpenTask(task_id="task-1", specialist="scheduling", intent=TaskIntent.BOOK_NEW, opened_turn=T1, details=TaskDetails(), status="open")]`, `planned=task(1, "scheduling", BOOK_NEW, resumes="task-1")`, current turn `T3`, `chat=[customer T1 "first", assistant T1 "reply", customer T2 "second", customer T3 "current"]` → `task_messages == ("first", "second")`, `offer_quick_checks is False`. (f) Window lacks the opening turn (chat only `[customer T2 "second"]`) → `("second",)`. (g) A `UowCounter` and a `GatewayDouble` built in the test stay untouched (`entered == 0`, `accessed == []`). (h) `"MHC-57204" not in json` for every case |
| `test_handoff_open_failure_propagates` (PA-2) | `HandoffDouble(error=RuntimeError("write failed"))`; WP-7 decision state → `pytest.raises(RuntimeError)` around `handoff(...)`; `len(requests) == 1` |

Journeys: `tests/journeys/j3/test_aea_39.py::test_j3_booking_write_then_yes_please_no_new_write`,
`tests/journeys/j4/test_aea_39.py::test_j4_wp4_fee_bearing_change_p2_case_policy_promise` (§6.3).

Test style: no paid model call, no `live` marker, no port binding, no network; mypy-clean (`tests.*` allows untyped defs but
still type-checks calls; use `cast(...)` where a double stands in for a typed field).

### 7.2 Gates (cheapest first; stop at the first red). From the worktree root, `export UV_LINK_MODE=hardlink`.

```bash
FILES="src/meridian/agent/nodes/act.py tests/unit/agent/nodes/test_act.py tests/unit/agent/nodes/act_fixtures.py tests/journeys/j3/test_aea_39.py tests/journeys/j4/test_aea_39.py"
uv run ruff format --check $FILES          # pass: "5 files already formatted"
uv run ruff check $FILES                   # pass: "All checks passed!"
uv run mypy                                # pass: "Success: no issues found in N source files" (project config: strict)
grep -n "uow(" src/meridian/agent/nodes/act.py    # pass: no output (AC-12 review grep)
uv run pytest tests/unit/agent/nodes/test_act.py -q                       # pass: 20 passed
grep -rl "nodes.act\|nodes import act\|meridian.agent.nodes" tests/       # the affected test files
uv run pytest tests/unit/agent tests/graph tests/unit/policy/test_escalation.py tests/unit/policy/test_handoff.py \
  tests/unit/test_import_direction.py -q                                  # affected tests; pass: 0 failed
uv run pytest -m journey tests/journeys/j3/test_aea_39.py tests/journeys/j4/test_aea_39.py -q   # pass: 2 passed
uv run python -m tests.journeys.affected --base main                      # pass: lists and runs both new journeys, exit 0
```

Known pre-existing red, not caused by this ticket: `test_no_journey_yet_prints_zero_and_exits_0` (build ledger rows AEA-06,
AEA-44, AEA-47, AEA-57). It is not in the affected set above; if a broader run shows it, report it as pre-existing.

Run the pytest commands serially (no `-n`): the AC-1 test measures wall time and the affected set is small. If a run is
slow, `uv run --with pytest-xdist pytest -n 2 …` is allowed for the non-timing files only. The full suite is not run: no
shared fixture, setting, dependency or cross-package seam changes here (`build-loop-test-scope.md`).

### 7.3 Existing tests that must stay green

`tests/graph/test_spine.py`, `tests/graph/test_run_graph.py`, `tests/unit/agent/test_routers.py`,
`tests/unit/agent/test_signals.py`, `tests/unit/agent/test_context.py`, `tests/unit/agent/nodes/test_compose.py`,
`tests/unit/agent/nodes/test_compose_blocks.py` (AEA-21); `tests/unit/policy/test_escalation.py`,
`tests/unit/policy/test_handoff.py` (AEA-14); `tests/unit/domain/test_specialist_task.py` (AEA-35b);
AEA-35's `tests/unit/agent/specialists/`; `tests/journeys/j3/test_aea_{27,28,34,43}.py`, `tests/journeys/j4/test_aea_28.py`;
`tests/unit/test_import_direction.py`.

### 7.4 Journey record (AC-15): `docs/testing/journeys/<run-date>-AEA-39.md`

Title `# Journey record: AEA-39 act node (fan-out, escalation, handoff)`, then the `integrated-journeys.md` §4 table:

| Field | Value to write |
|---|---|
| Claim | AEA-39 AC-15: J-3 (booking turn writes once; "Yes, please." adds no write) and J-4 (WP-4: P2 `fee_bearing_change` case, policy-table promise with the can't-guarantee and phone-support lines, no scheduling write) through the real `build_graph` with the real act nodes |
| Level | `mock-tested` |
| Tested revision | commit 1's SHA |
| Environment | worktree path; Python 3.12 via `uv run`; LangGraph 1.2.16, in-memory saver; AEA-21's node doubles for the other nodes; runner, scheduling and ledger doubles; J-3 uses the handoff double, J-4 AEA-29's real `HandoffService` / `CaseService` on a temp SQLite copy of the issued DB (`temp_sqlite()`); no server, no model |
| Command | the two journey commands and the unit command of §7.2 |
| Result | pass/fail per test with counts from your run |
| Evidence location | this record; the command output |
| Remaining limitations | No CON-2 response, no server, no browser; J-3 checks no DB row; J-4's appointment check proves the handoff path leaves the row alone, but the scheduling read is a double; the runner is a double (AEA-35's real loop is not exercised); compose's change-request card is not shown because the facts double sends no draft |
| Blocked by | AEA-51 (it wires the graph into AEA-40's merged CON-2 `submitTurn`: integrated J-3 and J-4 on AEA-57's merged harness) |

### 7.5 Capture and evaluation checks

- Capture (WF-1, WF-2): AC-7 (events and signals as codes), AC-11 (no model text in the request, the case result, events or
  signal records), AC-14 (fields for `turn_trace`). The CAP-1/CAP-3 runs through real entry points are AEA-51's.
- Evaluation: E-1 (WP-4, WP-7, WP-8) is mirrored at node level by AC-3, AC-4 and J-4; the real E-runs are Stage 9 work
  (D-10). No number is reported from this ticket.

---

## 8. Risks and requests

### 8.1 Decisions made in this plan (engineering; each reversible by a small follow-up)

| ID | Decision | Basis |
|---|---|---|
| PD-1 | `task_messages`: the customer lines of `chat_window` from the open task's `opened_turn` on, excluding the current turn; `()` for a new task; all windowed customer lines when the opening turn fell out of the window | DO-4 §5 "the customer's messages for this open task"; R-45; `OpenTask` has no message list |
| PD-2 | Quick-check rule 2 reads `details.service_type` of the resumed open task; a new task has no details, so its service type is "unknown" (passes) | graph-tools §6 rule 2 ("or unknown"); at offer time no type is captured yet (§8.4 G-1) |
| PD-3 | `bookings_left` clamped at 0 | a negative budget has no meaning for the specialist; R-41 cap |
| PD-4 | The first `staff_change_request` draft in this turn's results rides on any escalation request | code-captured data the staff need; harmless for other reasons (`promise_for` and `case_due_at` read it only for fee-bearing / burning-ruled-out) |
| PD-5 | `HandoffRequest.thread_id` / `turn_id` from `ctx.ids` | `run_graph` already checks `turn_input.turn_id == ctx.ids.turn_id` |
| PD-6 | A failing `deps.handoff.open` propagates (no catch, no halt) | `case_write_failed` is the safety node's signal (graph-nodes §4); no `HaltReason` fits a write error; AEA-40 handles a failed turn |
| PD-7 | `escalation` raises `ValueError` without a gate; `handoff` raises `ValueError` on an `escalate` decision lacking reason or priority | `async-safety.md` rule 1 (fail loudly); both are graph-wiring bugs, never customer states |
| PD-8 | `Halt.elapsed_ms` from `ctx.budget.started` | same arithmetic as AEA-21's recursion halt |
| PD-9 | A runner brake outside `BRAKE_HALTS` writes the halt only (DEADLINE, PROVIDER_SPEND_CAP and also SPEND_CAP) | graph-nodes §1 (`from_halt` raises for them), §4 ("signalled outside the nodes") |
| PD-10 | Signals carry `role="specialist"` and `specialist=<kind>` | `SignalRecord` fields; graph-nodes §4 |
| PD-11 | Test builders live in `act_fixtures.py` beside `test_act.py` | 500-line test cap (`code-structure.md`); AEA-21's `compose_fixtures.py` precedent |
| PD-12 | J-3/J-4 run the real `build_graph` with AEA-21's node doubles and the real act nodes, level `mock-tested` | integrated-journeys §4: AEA-57's harness and AEA-40's CON-2 have merged, but the graph is not wired into the turn before AEA-51 |
| PD-14 | J-4 opens its case through AEA-29's real `HandoffService` on a temp SQLite copy (its own `services()` / `new_thread()` / `summary_of()` helpers, imported, never edited), with the graph run on that database thread | AC-15 asks for "a P2 `fee_bearing_change` case row" and "the appointment row unchanged"; AEA-29 merged, so the stored effect is checkable now at no new cost. The unit tests keep the `HandoffDouble` (AC-10 needs a scripted second open) |
| PD-13 | `SchedulingSlice.pending_change` is `getattr(state, "pending_change", None) is not None` | graph-nodes §9.5 names the field; it is not on `ConversationState` (AEA-02 §8.2) and AEA-38 (PD-4) writes none this wave, so the value is `False` either way; `getattr` keeps this file right when the field lands, with no edit and no blocker |

### 8.2 Collisions with sibling tickets

| Surface | Sibling | Handling |
|---|---|---|
| `src/meridian/agent/nodes/act.py` | AEA-21 created the stub | Replace in place after AEA-21 merges (collision map: "stubs replaced in place") |
| `tests/unit/agent/nodes/` | AEA-21 (`compose_fixtures.py`, `test_compose*.py`) | Add new files only |
| `tests/graph/_spine_doubles.py` | AEA-21 (published helpers) | Import only; if a helper is missing, report it, never edit |
| `agent/specialists/runner.py` | AEA-35 | Import `scope_for` only |
| `.claude/reference/area-map.md` A7b row | AEA-22, AEA-35, AEA-14 | Append only this ticket's mention; trivial text conflict expected at merge |
| `SpecialistTask`, `KnowledgeSlice`, `AccountSlice` | AEA-35b owns them (`domain/tools.py`); AEA-35 imports them too | Import only; neither AEA-35 nor AEA-39 may define or edit them |
| `tests/services/_case_fixtures.py`, `services/{handoff,cases}.py` | AEA-29 (merged) | J-4 imports the helpers and runs the services; never edit them. If a helper's signature differs from §6.3, follow the code and report it |
| `.claude/state/icm-progress.md`, `docs/design/code-design.md` §3 | every build ticket | One added row; one suffix change |
| `docs/testing/journeys/` | every ticket | One file per ticket |
| `tests/journeys/j3/`, `j4/` | AEA-28, AEA-34, AEA-51 | One file per ticket (`test_aea_39.py`) |

### 8.3 Requests to the orchestrator

- **R-1 (resolved).** Innocent chose option A on 2026-10-21; AEA-35b (`aea-35b-specialist-types`, `68f7f19`) puts
  `SpecialistTask`, `KnowledgeSlice` and `AccountSlice` in `domain/tools.py` with the shape §4.2 copies. Request: merge
  AEA-35b before AEA-35 and AEA-39. If its merged shape differs from §4.2 (e.g. the slices gain fields), send this plan
  back to the planner.
- **R-2 (merge order, the dependency tree).** AEA-35b → AEA-35 → AEA-39. AEA-39 imports `scope_for` from AEA-35's
  `runner.py`; a module-level function cannot be injected through `GraphDeps`, so this is a real import edge. AEA-28 and
  AEA-29 (both merged) stay injected-only in `act.py`. Hand this plan to its implementer the moment AEA-35 merges.
- **R-3 (ledger and slice plan).** The build ledger row AEA-39 reads `blocked`, NEEDS-DECISION (plan), blockers
  `AEA-11,AEA-14,AEA-21`; it should read `blocked` (a blocker is not merged) with blockers
  `AEA-11,AEA-14,AEA-21,AEA-35b,AEA-35` and lose the NEEDS-DECISION note. The slice plan row AEA-39 (`blocked by 11, 14,
  21`) needs the same two additions at AEA-08's next reconcile.
- **R-4 (dev log).** One entry in `Gauntlet AI/devlogs/aea-callcenter/` per `.claude/reference/dev-log.md`, written by
  the orchestrator (outside this ticket's files).

### 8.4 Spec gaps and other risks

- **G-1 (quick-check rule 2 is vacuous at offer time).** The offer happens on the turn a new booking task opens
  (`resumes_task_id is None`), before any service type is captured, so rule 2 always passes there. The code still reads it
  (PD-2); if a later ticket puts a service type on `PlannedTask`, rule 2 starts to bite with no change here except reading
  that field.
- **G-2 (non-safety case write failure).** No contract names a signal or halt for it (PD-6). If Innocent or AEA-40 wants a
  degraded reply instead of a failed turn, that is a follow-up.
- **G-3 (superstep proof).** AC-1's "one superstep" is shown by wall time, the method AEA-21 validated on LangGraph 1.2.16.
  If the timing is flaky on a loaded machine, raise the delays (keep `elapsed < 0.8 × serial sum`); do not drop the check.
- **G-4 (result order under parallel writes).** AC-1 relies on LangGraph applying parallel writes in task (Send) order, not
  completion order; the reversed delays prove it. If the order assertion fails, stop and report: the fix is not in
  `act.py`.
- **G-5 (compose in journeys).** J-3/J-4 run AEA-21's real `ReplyComposer`. If compose raises on these states, report it as a
  seam finding against AEA-21; do not edit compose and do not weaken the journey.
- **Security surface (reviewer note).** Untrusted customer text reaches a tool-calling model through this node; it is
  SONNET-masked here (and again by AEA-35's render). Not labelled `risk::security` in the slice plan; if `code-review-agent`
  judges otherwise, the orchestrator adds the label.

### 8.5 What the implementer must not do

- Do not define or stand in for `SpecialistTask`, `KnowledgeSlice`, `AccountSlice`, `pending_change`, `scope_for` or any
  other missing name; stop and report (step 0).
- Do not edit any file outside §2.1, including `policy/*`, `domain/*`, `agent/{routers,graph,context,signals}.py`,
  `nodes/compose.py`, `tests/graph/_spine_doubles.py`, `tests/fakes/*`, `tests/conftest.py`.
- No escalation rule, priority, promise text, due time or case reference computed in `act.py` (only
  `priority_for(CUSTOMER_REQUESTED_PERSON)` for the person gate). No `deps.uow` call. No retry of `open`.
- No `if`/`match` on result types to decide escalation; `decide_escalation` decides.
- Never log or put in a signal any task text, report text, customer text or result value; signals carry codes only.
- No literal six-digit code, card-like number or full phone number; no paid model call; no `live` test; no port binding
  (never 4019 or 5184); no `node_modules`; never copy a venv; `pytest -n 2` at most.
- Never read `.env`; never `git add -A`; never push or force-push; last commit-message line
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Never edit the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
  `ui-contracts.openapi.yaml` or `UI_CONTRACTS.md`. A needed change to a signed contract stops the work (report
  NEEDS-DECISION).

---

## 9. Readiness

**READY.** Every decision is made, and the one product question (§9.1) is answered. Step 0 enforces the merge order:

1. **AEA-35b** (`SpecialistTask`, `KnowledgeSlice`, `AccountSlice` in `domain/tools.py`; branch `aea-35b-specialist-types`,
   `68f7f19`, not yet on `main`). `build_specialist_task` returns a `SpecialistTask`, so nothing here type-checks without it.
2. **AEA-35** (`scope_for` in `agent/specialists/runner.py`; not merged; its plan was waiting on the same answer).

On `main` at `8a205b2` and checked: AEA-11, AEA-14, AEA-21 (the ticket's listed blockers), AEA-01, AEA-02, AEA-04,
AEA-28, AEA-29, AEA-34, AEA-38, AEA-40, AEA-57. `HandoffService` and `slice_inputs` are injected in `act.py` and doubled in
the unit tests; J-4 runs the real `HandoffService`. `pending_change` is not a blocker (PD-13). The `[journey]`
criterion's integrated level waits on AEA-51 (not a merge blocker; the record says so). No sign-off decision D-4…D-15 is
answered differently: CAS-16 stays on D-14's option A inside AEA-14. No signed contract changes in this ticket (the home
note under graph-tools §2 is AEA-35b's). **Gates:** none (no human, paid or live gate). No security review unless the
reviewer adds `risk::security` (§8.4).

### 9.1 Decision for Innocent: answered

**Asked:** may `SpecialistTask`, `KnowledgeSlice` and `AccountSlice` live in `domain/tools.py` instead of the signed
`domain/specialists.py` (which would import `domain/turn.py` and close an import cycle)? **Answered 2026-10-21:** option A
("just do whatever you recommend"), built by AEA-35b. Options B (a deferred import in `specialists.py`) and C (the types in
`agent/specialists/specs.py`) were not taken. AEA-08 reconciles the file name in graph-tools §2.

## Deviations

- **Test file sizes.** `tests/unit/agent/nodes/test_act.py` (about 720 lines) and `act_fixtures.py` (about 610 lines) exceed the plan's 500-line target after `ruff format` (project line length). Not split, to keep the plan's binding test names and file list; a follow-up may split by AC group.
- **AC-2 test.** `test_specialist_task_slices_and_quick_check_offer` is parametrised for the offer table; the slice, knowledge-slice and `scope_for` checks sit in `test_specialist_task_offer_other_cases_and_slices`, and the resumed-task offer check in `test_resumed_task_with_other_service_type_does_not_offer` (31 tests reported rather than 20).
- **`decide_escalation` recording.** Tests patch `meridian.agent.nodes.act.decide_escalation` with `monkeypatch.setattr(act_mod, ...)` and import the real function from `meridian.policy.escalation` (mypy rejects reading it off `act`, which does not re-export it).
