# Plan — [AEA-35] specialists: specs, braked tool loop, wording

**Status:** planned; **READY**. The open question of earlier refreshes (where `SpecialistTask`, `KnowledgeSlice` and
`AccountSlice` live) was answered by Innocent on 2026-10-21 ("just do whatever you recommend": option A of §9.1). They
live in `src/meridian/domain/tools.py`, built by the small ticket **AEA-35b** (branch `aea-35b-specialist-types`, commit
`68f7f19`), which merges into `main` before this ticket builds. Step 0.2 checks that it has.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/35 (spec copy:
`docs/plans/tickets/AEA-35.md`) · **Base revision:** `main` at `f466ff7` plus AEA-35b `68f7f19` (fifth refresh
2026-10-21; earlier `dd1b110`, `e22aebb`, `775f591`, first written at `16ca639`) · **Lane:** `lane::build-loop`, no
`risk::security` · **Wave:** 2 · **Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21 · **Implementer:**
`fanout-implementer` on Sonnet.

Read this whole file before writing code. Every decision is already made here (§8.1 lists them). If the code on `main`
disagrees with a name in this plan, **the code on `main` wins**: follow it, and say so in your report. If a name this
plan needs is **missing** on `main`, stop and report (do not invent it).

**Refresh 5 (2026-10-21, `main` at `f466ff7`; AEA-35b at `68f7f19`). Where Refreshes 1–4 below disagree with this
block, this block wins; they are kept as history.**

1. **Decision taken; the blocker is AEA-35b.** `git show aea-35b-specialist-types:src/meridian/domain/tools.py` defines,
   right after `ToolCallScope`: `KnowledgeSlice(MeridianModel)` with only `kind: Literal["knowledge"] = "knowledge"`,
   `AccountSlice(MeridianModel)` with only `kind: Literal["account"] = "account"`, and `SpecialistTask(MeridianModel)`
   with `task: PlannedTask`, `customer_text: str`, `task_messages: tuple[str, ...]`, `slice: KnowledgeSlice |
   AccountSlice | SchedulingSlice`, `offer_quick_checks: bool = False`: exactly R-1's sketch. AEA-35b also adds the
   home note to graph-tools §2 and its own area-map and ICM rows. Every import of `SpecialistTask` in this plan is now
   `from meridian.domain.tools import SpecialistTask` (§4.4–§4.6), and `_doubles.py` builds the slices as
   `KnowledgeSlice()` and `AccountSlice()` (§6.2). §9.1 is answered and kept as history.
2. **Nothing else this plan imports changed.** `git diff --stat dd1b110 main` on `src/meridian/{domain,ports,privacy}`,
   `policy/limits.py`, `agent/gateway.py`, `agent/tools/dispatch.py` and `tests/fakes/` is empty, so §4 holds name for
   name. `src/meridian/agent/specialists/` still holds only `__init__.py`.
3. **`tests/unit/agent/prompts/__init__.py` now exists on `main`** (AEA-38, with `test_reply_prompts.py` and
   `test_reply_prompt_turns.py`). It is no longer an owned file: do not create or edit it; it is out of the commit list
   (§2.1, step 6, step 10).
4. **AEA-38 merged** (`ec94722`): `agent/prompts/reply.py` and `tests/journeys/j2/test_aea_38.py`, a `mock-tested`
   J-2 file and the nearest precedent for this ticket's journey file. **AEA-40 merged** (`f466ff7`). AC-15's
   integrated level still waits on AEA-51 only.
5. **AEA-39's plan** imports only `scope_for` from `agent/specialists/runner.py` and calls
   `deps.specialists.run(task, scope_for(state, ctx), ctx)`; both stay exactly as §4.6 defines them.
6. Ruff config on `main`: `line-length = 110`, rules `E, W, F, I, B, UP, S, RUF` (tests ignore `S101, S105, S106,
   S603, S607, S311`); mypy `strict = true` over `src/meridian`, `tests`, `eval` (tests may leave defs untyped).

**Refresh 4 (2026-10-21, `main` at `dd1b110`; history).** 37 commits since `e22aebb`. `git diff --stat e22aebb dd1b110` on
`src/meridian/{domain,ports,privacy}`, `policy/limits.py`, `agent/gateway.py`, `agent/tools/dispatch.py` and
`tests/fakes/` shows only the new `domain/views.py` (AEA-02b), so §4 still holds name for name. What changed:

1. **Still blocked, still undecided.** `grep -rn "^class SpecialistTask" src/` finds nothing; the
   `domain/specialists.py` docstring still says "Not built here … blocked on the AEA-02b follow-up". AEA-02b merged
   (`5305d57`) with `domain/views.py` only. The build ledger row reads `blocked | NEEDS-DECISION (plan)`; issue #35 has
   no answer from Innocent. The cycle that rules out the signed home was re-checked at `dd1b110`: `domain/turn.py`
   line 44 imports `domain/specialists.py`; `domain/tools.py` imports `turn.py` and `specialists.py`, and no `domain/`
   module imports `tools.py`. §9.1 is unchanged.
2. **AEA-21 merged** (`5531664`): `agent/context.py` types `GraphDeps.specialists` through
   `SpecialistRunner: TypeAlias = Any` until this module lands; AEA-51 swaps in the real import. `agent/nodes/act.py`
   is AEA-21's stub (`run_specialist(payload: SpecialistSend, runtime, *, deps)` raises `NotImplementedError`); AEA-39
   fills it. Nothing here changes; neither file is owned by this ticket.
3. **AEA-27 merged** (`13adc86`): `agent/tools/account.py` defines `READ_INVOICES_NAME = "read_invoices"`,
   `READ_MEMBERSHIP_NAME = "read_membership"`, `READ_WARRANTY_NAME = "read_warranty"` (the names the account wording
   uses, §4.4) and its not-verified refusal returns `captured=None` with `ToolError(code=NOT_VERIFIED)`, which is the
   case `build_account_result` step 5 reads from `ToolCallRecord.error`. Confirmed.
4. **AEA-28 merged** (`2c2e8c5`): scheduling tool names are `find_windows`, `book_visit`, `move_visit`,
   `cancel_visit`, `request_visit_change` (the wording still names none of them, PD-11). Every executor refusal returns
   `SchedulingCapture(refused=<code>)` and dispatch copies the same code into `ToolCallRecord.error`
   (`dispatch.py` around line 353), so `build_scheduling_result` step 4's record-based map gives the same answer as
   reading `SchedulingCapture.refused`, and also covers the dispatch guard's `not_verified`, which has no capture. A
   `slot_taken` refusal captures the fresh alternatives in `windows`, so the result is `status="slot_taken"` with those
   windows. `request_visit_change` on a fee-free visit refuses with `not_allowed` (not in the status map: the status
   falls through to windows or `failed`). Doubles in §6.2 stay as written.
5. **AEA-17 merged** (`0a85270`): `adapters/models/anthropic.py` `AnthropicAdapter` has `start` and `append`, the
   real `ToolTranscript` AEA-51 will pass as `transcript` (R-3). Tests here still use AEA-11's `FakeToolModel`.
6. Step 0, step 9.3 and §9 are updated for `dd1b110`.

**Refresh 3 (2026-10-21, `main` at `e22aebb`).** Between `775f591` and `e22aebb` nothing changed in
`src/meridian/{domain,ports,policy/limits.py,privacy}`, `agent/gateway.py`, `agent/tools/dispatch.py` or `tests/fakes/`
(`git diff --stat 775f591 e22aebb` on those paths is empty), so §4 still holds name for name. What changed:

1. **The blocker is still open, and its name now misleads.** A ticket was cut and built as "AEA-02b" (branch
   `aea-02b-case-views`, commit `db85ec4`, not merged), but it adds only `src/meridian/domain/views.py`: the case,
   queue, oversight, staffing, clock and reset views for AEA-29 and AEA-30. It does **not** add `SpecialistTask`,
   `KnowledgeSlice` or `AccountSlice`; `grep -rn "^class SpecialistTask" src/` finds nothing on `main` or on that
   branch, and the `domain/specialists.py` docstring still reads "Not built here … blocked on the AEA-02b follow-up".
   **Merging AEA-02b will not unblock this ticket.** This plan now calls the missing prerequisite "the specialist task
   types follow-up" (§8.3 R-1). Because the only home the signed contract names for it is impossible (an import cycle,
   R-1), unblocking needs Innocent's yes on a home change: §9.1.
2. **AEA-57 (journey harness) is merged** (`bd79a29`). AC-15's integrated level now waits only on AEA-51, which wires
   the graph the harness drives and lands J-2. The journey file stays `mock-tested`, as AEA-26's and AEA-48's merged
   journey files do for paths not wired yet (§7.1, §7.4).
3. **AEA-33 is merged** (`a45e3c2`): `agent/tools/knowledge.py` defines `KB_SEARCH_NAME: Final = "kb_search"`, which
   matches the quick-check call name here. This ticket still uses a dispatcher double, not the executor.
4. **The ICM convention changed:** every merged ticket now **adds** its own *Routes verified against code and tests*
   row instead of replacing the first one. Step 9.3 follows that.
5. Step 0 and the gate commands are updated for `e22aebb`; the affected-journeys gate now also runs AEA-57's harness
   journey (a loopback server on an OS-assigned port).

Earlier refresh (at `775f591`) still stands: no turn id in the scheduling state JSON (§4.4 `_user`, PD-16, AC-22),
because a digit-heavy UUID such as `TURN_1` matches the SONNET card rule and would reach the model as
`[card number removed]`.

---

## 1. Goal and sources

### 1.1 Goal (from the issue's *What to build*)

> **US-6:** "As a **homeowner**, I need answers about membership, billing fees, warranty, services, hours and the service
> area that come from Meridian's current documents and show where they came from, so that I can trust the number I'm
> given." (Also US-9, US-10, US-11, US-12, US-13.)

Three new modules:

- `src/meridian/agent/specialists/specs.py`: `RunOutcome`, `SpecialistSpec`, `SPECS` (one spec per kind: knowledge,
  account, scheduling), the three result builders, `report_facts_schema`.
- `src/meridian/agent/specialists/runner.py`: `SpecialistRunner` (the braked tool loop) and the pure `scope_for`.
- `src/meridian/agent/prompts/specialists.py`: each specialist's wording as `(system_prefix, system_dynamic, user)`.

**What it does, concretely (WP-2).** The act node (AEA-39, not this ticket) hands the runner a finished
`SpecialistTask` for `read_invoice`, a `ToolCallScope` with `customer_id=MHC-10002`, and the turn context. The runner
renders the account wording, starts a fresh provider message list with the task text, asks the gateway for one model
step, sends the model's `read_invoices` call to the dispatcher, appends the result under its `tool_call_id`, asks for
the next step, and stops when the model calls `report_facts`. The account spec's builder then copies the captured
`InvoiceView` (INV-204411, lines 8900 / 24500 / 14400 cents, as billed) and the staff note into `AccountResult`.
Nothing in the result is read from model text. The runner emits one `tool:read_invoices` node span, logs nothing, and
returns; it never raises.

**Worked pairs this ticket proves:** WP-1 (knowledge, membership, stale twin), WP-2 (account, invoice as billed; staff
note kept apart), WP-4 (fee-bearing move → staff change request, `write=None`), WP-4F (fee-free move → `written`).

### 1.2 Context (why now)

The specialist layer is the middle of DO-2's two-layer turn: planner (Jev) → **specialists (Sonnet, tools)** →
responder. Stage 7 replaced DO-4 §5's free function `run_specialist(spec, task, ctx)` with an injected
`SpecialistRunner` (GRT-6), fixed "zero valid points → `no_current_source`" (GRT-7), added code-built quick checks
(GRT-8) and tool spans from the runner (R-G-17). The gateway (AEA-20), dispatcher (AEA-22) and fakes (AEA-11) are
wave 1; the executors (AEA-27, 28, 33) and the act node (AEA-39) are siblings in wave 2 and are doubled here.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-35.md` | AC-1…AC-16; owned files; must-nots; observability and metrics notes |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-35 (blocked by 11, 20, 22; owns `agent/specialists/{specs,runner}.py`, `prompts/specialists.py`), §0a J-2 row, §3 collision map | One journey file `tests/journeys/j2/test_aea_35.py`; never edit another ticket's file |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §5 (specialist contracts, report models, runner rules), §11 (`HaltReason`, `ProviderFailure`, failure rows), §12 (`ToolStepRequest`, `ToolStep`, `CallRecord`, `ToolCallingModel`, `ModelGateway.tool_step`, `ModelOutcome`), §16 (addenda win) | Exact shapes and runner rules |
| Addendum graph-tools | `stage7/graph-tools.md` §1 (`ToolDispatcher`, `DispatchedCall`, `ToolCallRecord`, `ToolKind`, `ToolErrorCode`), §2 (`ToolTranscript`, `RunOutcome`, `SpecialistSpec`, `SPECS`, `SpecialistRunner`, `scope_for`, `offer_quick_checks`), §3 (captures, `StaffNote`, `SchedulingResult.quick_checks`), §4 (account tool names), §6 (quick checks), C-1, C-7, C-8, C-9 | The runner's signature and every loop rule |
| Addendum models | `stage7/models.md` §1 (`ProviderMessages` = provider, model, items; never logged/traced/stored; `append` refuses foreign lists), §4 (`TraceSink.node`, `SpanHandle`), §5 (gateway rules: halts it returns) | What the runner passes through untouched |
| Addendum graph-core | `stage7/graph-core.md` §1 (type homes), §2 (`TurnInput.message_id`, `TurnContext.span`), §4 (`GraphDeps.specialists`) | `scope_for` reads `turn_input.message_id`; spans go under `ctx.span` |
| Addendum graph-nodes | `stage7/graph-nodes.md` §4 (signals: the runner emits none), §9.5 (how AEA-39 calls `run`; `build_specialist_task` is AEA-39's) | No signal, no check event here |
| Addendum data | `stage7/data.md` §1 (SONNET placeholders `[code]`, `[card number removed]`, `[phone ending NN]`, `[email]`, `[address]`), §4 (`kb_search`, `KbSearchArgs.query` 1–300 chars) | Quick-check call shape; redaction tokens |
| Decisions | `docs/plans/7b-decisions/graph-tools.md` GRT-6…GRT-9; `graph-nodes.md` GRN-4; `residuals-graph.md` R-G-17 | Settled; nothing here waits on Innocent |
| Code design | DO-3 `docs/design/code-design.md` §3 (three tree rows), §4.5 (specialists as data; no `if spec.kind`), §6 S-12, S-13, S-14 | Layering and the "no kind branch" rule |
| System design | DO-2 §A.1 (brakes: 3 tasks, 2 tool rounds, 6 Sonnet calls), §A.3 ("Each model sees only its slice"); SDQ-7 = A (keep SP-1's call shape) | Two tool rounds; per-run message list |
| SP-1 wording | `docs/plans/fanout/2026-10-20-sp1/build.md` step 8 (measured prompts and loop); `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md` §4 (12-month minimum gap) | Starting wording (§4.4 below); SP-1's top-3 fallback is **not** carried (GRT-7) |
| Requirements | PRD R-13 (sources only, no prices, no cards), R-17 (as billed), R-18…R-23 (booking rules; R-21/R-22 fee-bearing changes), R-41 (brakes), R-44 (quick checks), R-45 (each model sees its slice) | Wording rules and loop brakes |
| Rules | `integrated-journeys.md` §4 (record fields, levels); `build-loop-test-scope.md` + AEA addition; workspace `context-management-multi-turn.md` rules 1, 3, 4; `agent-architecture.md` rules 5, 6; `agent-tools.md` rule 6; `code-design-solid-modularity.md` | Turn-2+ prompt test; four brakes; every dispatch branch; layering |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` E-1 (trajectory), E-7 (booking validity) | Kept passing when AEA-51 runs the compiled graph; scored runs are Stage 9 → other-ticket |
| Observability | DO-6 `docs/design/observability-contract.md` WF-1, rule 18 (tool call is a timed span), *Missing instrumentation* "a tool call left no lookup-log row"; CAP-1 | One span per dispatched call; one dispatch per call; CAP-1 is AEA-51 |
| Metrics | DO-7 `docs/design/key-metrics-registry.md` M-7, M-8, M-9, M-21, M-24, M-25 | Stay computable: passage ids in lookup rows, every `CallRecord` on the result, brake/failure on the result. No target set here |
| Sibling plans (read only) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0–§4.13, §8.2; `AEA-11.md` §4–§5; `AEA-20.md` §4.5; `AEA-22.md` §4.3, §5 | Exact homes and names of the types used here; `SpecialistTask`, `KnowledgeSlice`, `AccountSlice` are AEA-35b's (`domain/tools.py`), not AEA-02's |
| Journey harness | `tests/journeys/support/README.md` (AEA-57, merged `bd79a29`); precedents `tests/journeys/j10/test_aea_48.py`, `tests/journeys/j9/test_aea_26.py` and their records | Harness steps need the wired graph (`run_graph`, `turn_service`: AEA-51, AEA-40); until then a ticket's journey file is `mock-tested` and names the landing ticket |

### 1.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (the runner is reached only through the act node, AEA-39, inside WF-1's CON-2 turn) | WF-1 | yes (DO-6 WF-1) | E-1, E-7; M-7, M-8, M-9, M-21, M-24, M-25 |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files the implementer may create or edit)

| File | Create / modify | What |
|---|---|---|
| `src/meridian/agent/prompts/specialists.py` | create | Wording constants, `TASK_LABELS`, `render_knowledge`, `render_account`, `render_scheduling` (§4.4, step 1) |
| `src/meridian/agent/specialists/specs.py` | create | `TROUBLESHOOTING_FILE`, `RunOutcome`, `SpecialistSpec`, `report_facts_schema`, three builders, `SPECS` (§4.5, step 2) |
| `src/meridian/agent/specialists/runner.py` | create | `SpecialistRunner`, `scope_for` (§4.6, step 3) |
| `tests/unit/agent/specialists/__init__.py` | create | empty (0 bytes) |
| `tests/unit/agent/specialists/_doubles.py` | create | test builders and the two doubles (§6.2) |
| `tests/unit/agent/specialists/test_runner.py` | create | runner tests (§7.1) |
| `tests/unit/agent/specialists/test_specs.py` | create | spec/builder tests, WP-1/WP-4/WP-4F, static checks (§7.1) |
| `tests/unit/agent/prompts/test_specialist_prompts.py` | create | AC-11 and wording tests (§7.1) |
| `tests/unit/agent/prompts/test_specialist_prompt_turns.py` | create | AC-12 turn 1/2/5 test (§7.1) |
| `tests/journeys/j2/test_aea_35.py` | create | AC-15 journey steps at `mock-tested` level (§7.1) |
| `docs/testing/journeys/<run-date>-AEA-35.md` | create | AC-15 evidence record (§7.4) |
| `.claude/reference/area-map.md` | modify | A7b row only (AC-16, step 9) |
| `.claude/state/icm-progress.md` | modify | one new *Routes verified against code and tests* row only (AC-16, step 9.3) |
| `docs/design/code-design.md` | modify | §3 tree lines for the three files only (AC-16, step 9) |

`src/meridian/agent/specialists/__init__.py` and `src/meridian/agent/prompts/__init__.py` already exist (AEA-01);
**do not edit them** (consumers import from the submodules). `tests/unit/agent/prompts/__init__.py` (AEA-38) and
`tests/journeys/j2/__init__.py` (AEA-01) already exist too: do not create or edit them.

### 2.2 Shared surfaces: read, never edit

`src/meridian/domain/*` (AEA-02; `domain/tools.py` also holds AEA-35b's `SpecialistTask`, `KnowledgeSlice`, `AccountSlice`), `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02); `src/meridian/policy/limits.py`
(AEA-01, `Brakes`); `src/meridian/privacy/redact.py` (AEA-04); `src/meridian/agent/gateway.py` (AEA-20);
`src/meridian/agent/tools/dispatch.py` (AEA-22); `tests/fakes/*` (AEA-11); `tests/conftest.py`,
`tests/journeys/affected.py`, `tests/journeys/README.md` (AEA-01); `tests/journeys/support/` (AEA-57, merged);
`src/meridian/agent/tools/knowledge.py` (AEA-33, merged); `tests/unit/test_import_direction.py` (shared; this
ticket adds its import checks in its own test file instead).

### 2.3 Owned by other tickets — must not touch

`agent/tools/{knowledge,account,scheduling}.py` (AEA-33, AEA-27, AEA-28, all merged: executors, tool names, `for_model` content);
`agent/nodes/act.py` (AEA-39: `run_specialist`, `build_specialist_task`, `offer_quick_checks` rule, signals, check
events); `agent/context.py` (AEA-21: `GraphDeps.specialists`); `web/container.py` (AEA-51 wires the runner);
`src/meridian/domain/views.py`, `domain/tools.py` and every other `domain/*` file (AEA-02, AEA-02b, AEA-35b); `agent/prompts/reply.py`, `tests/unit/agent/prompts/test_reply_*.py`, `tests/unit/agent/prompts/__init__.py`, `tests/journeys/j2/test_aea_38.py` (AEA-38);
`tests/contract/test_prompts_vs_consumers.py` (AEA-60); `apps/web/**`,
`docs/ux/**`, the OpenAPI, the briefing, issued data, `docs/archive/`, `docs/parked/`.

---

## 3. Requirements table

### 3.1 Acceptance criteria (issue verbatim IDs) → implementation → verification

All test paths are under `tests/unit/agent/` unless written in full. "Runner" = `SpecialistRunner.run`.

| AC | Requirement (short; full text in the issue) | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | At most `brakes.tool_rounds` (2) tool rounds; a third round → `brake = BRAKE_TOOL_ROUNDS`, no third dispatch | runner step-loop rule 6 (§4.6) | `specialists/test_runner.py::test_two_tool_rounds_brake` → 2 dispatch batches; `result.brake == "brake_tool_rounds"`; 3 model requests |
| AC-2 [invariant] | Identical call → `BRAKE_IDENTICAL_CALL`, dispatched once; no tool call → final-answer branch; `report_facts` ends the run, never dispatched | rules 4, 5, 7, 8 | `::test_identical_call_breaker`, `::test_final_answer_branch`, `::test_report_facts_ends_loop_not_dispatched` |
| AC-3 [invariant] | Each dispatched call's `content` appended under its own `tool_call_id`; each run starts a fresh list holding only that task's text | rules 2, 6c | `::test_results_keep_tool_call_ids`, `::test_message_list_is_per_run` |
| AC-4 [failure/refusal] | `run` never raises: gateway `failure` → `status="failed"`, `failure` set, no further step; gateway `halt` (DEADLINE, BRAKE_SONNET_CALLS, PROVIDER_SPEND_CAP) → `brake`; a `tool_failed` `DispatchedCall` reaches the model and the run goes on | rule 3; PD-1 | `::test_never_raises_on_failure`, `::test_gateway_halt_stops_run` (parametrised over the three halts), `::test_tool_failed_content_reaches_model` |
| AC-5 [invariant] | Results come from `ToolResult.captured`, never from `report_facts` | builders (§4.5) | `specialists/test_specs.py::test_results_from_captured_not_report` |
| AC-6 [failure/refusal] | GRT-7: one point citing an unreturned passage while 3 were returned → `no_current_source`, no points, 3 passages kept; below-floor search → same | `build_knowledge_result` | `test_specs.py::test_zero_valid_points_no_current_source`, `::test_below_floor_no_current_source` |
| AC-7 [invariant] | WP-4: `fee_bearing` move + captured `ChangeRequestDraft` → `staff_change_request`, `write=None`; WP-4F → `written` with the captured `WriteResult` | `build_scheduling_result` (PD-4), through the real runner with doubles | `test_specs.py::test_wp4_fee_bearing_becomes_change_request`, `::test_wp4f_fee_free_move_written` |
| AC-8 [invariant] | Quick checks: one code-built `kb_search`, id `qc-<turn_id>`, `kinds={kb_search}`, before the first model step, not a tool round; only troubleshooting passages reach `SchedulingResult.quick_checks`; `False` makes none; `KnowledgeResult.quick_checks` = troubleshooting ids returned this run | runner step 3 (§4.6); `build_knowledge_result` | `specialists/test_runner.py::test_quick_checks_offer`, `specialists/test_specs.py::test_knowledge_quick_checks_only_from_troubleshooting` |
| AC-9 [invariant] | `scope_for`: verified-only `customer_id`; shown slot ids; `now`, `ids` from ctx; `message_id` from `state.turn_input` | `scope_for` | `test_runner.py::test_scope_for` (parametrised over the six identity statuses) |
| AC-10 [negative] | No staff-note text, scope `customer_id` or `ProviderMessages` payload in any `ToolStepRequest` or log record; serialised result holds no `ProviderMessages`, no `for_model`, no `ChatLine` | runner passes only render output + `content`; logs nothing on the normal path | `test_runner.py::test_no_staff_notes_transcript_or_scope_leak` (caplog) |
| AC-11 [negative] | Rendered requests carry no 6-digit run, no 13–19-digit run, no full phone; `system_dynamic` holds `ctx.now`'s date | prompts (§4.4), PD-10 | `prompts/test_specialist_prompts.py::test_requests_carry_no_secret_values` (parametrised over the three kinds) |
| AC-12 [invariant] | Turn 1, 2, 5 of WP-1: `system_prefix` byte-identical and complete; only `system_dynamic` and user text differ | prompts constants | `prompts/test_specialist_prompt_turns.py::test_stable_prefix_turns_1_2_5` |
| AC-13 [capture] | Every non-`report_facts` call and the quick check reach dispatch exactly once; one `ToolCallRecord` per dispatched call; every gateway `CallRecord` in `calls` | runner `_take` | `test_runner.py::test_lookup_and_call_records` |
| AC-14 [capture] | One node span per dispatched call (quick check included), `tool:<registry name>` or `tool:unknown`, record's `elapsed_ms` and outcome; no args/result text; no span for `report_facts` | runner `_take` | `test_runner.py::test_tool_spans` |
| AC-15 [journey] | Extends J-2: billing and warranty answers stay inside the brakes and show the invoice / warranty source; level `mock-tested`, *Blocked by* AEA-57, AEA-51 | journey file | `uv run pytest -m journey tests/journeys/j2/test_aea_35.py -q` → 2 passed; record §7.4 |
| AC-16 [regression/context] | Area map A7b row, ICM row, DO-3 §3 rows updated, only this ticket's rows | step 9 | `git diff --name-only main...HEAD` shows exactly the files in §2.1 |

### 3.2 Plan-added criteria (reconciliation found them; the orchestrator may post them on the issue)

| AC | Requirement | Source | Verified by |
|---|---|---|---|
| AC-17 [invariant] (plan-added, WP-1 pair) | WP-1 through the runner: every point cites a `passage_id` a `kb_search` returned **in this run** from `membership/comfort_club_overview.md`; a point citing `archive/comfort_club_overview.md#0` is dropped; no point text holds `$149`, `$12.99`, `$219` or `10% off` | Ticket example pair 1; build-loop-test-scope "the WP-N worked pair is one of them" | `test_runner.py::test_wp1_knowledge_run_cites_current_file` and `test_specs.py::test_wp1_points_cite_only_this_runs_passages` |
| AC-18 [invariant] (plan-added) | The runner holds no `if spec.kind == …` branch and no specialist-kind string literal; the three modules import only the layers DO-3 allows | DO-3 §4.5 ("the runner holds no `if spec.kind == …`"); DO-3 §2.1 | `test_specs.py::test_runner_never_branches_on_kind`, `::test_modules_import_only_allowed_layers` |
| AC-19 [invariant] (plan-added) | `SPECS` covers exactly the three kinds with the tool kinds and report models of graph-tools §2, is read-only; `report_facts_schema(spec)` is `report_facts`, strict, with `input_schema == spec.report_model.model_json_schema()` | graph-tools §2; AEA-60 AC-5 | `test_specs.py::test_specs_cover_every_kind`, `::test_report_facts_schema_from_report_model` |
| AC-20 [failure/refusal] (plan-added) | An exception inside a run (e.g. a collaborator bug) still returns a result: `status="failed"`, `failure=None`, what was gathered kept, one log record holding only the exception type name; an invalid `report_facts` is ignored (no report), never raised | DO-4 §5 "never raises"; safe-validation-errors | `test_runner.py::test_unexpected_error_returns_failed_result`, `::test_invalid_report_is_ignored` |
| AC-21 [invariant] (plan-added) | Per-turn budget (context-management rule 4): the user text holds at most the last 6 task messages, each cut to 1,000 characters | workspace rule `context-management-multi-turn` 4 | `prompts/test_specialist_prompts.py::test_user_text_budget` |
| AC-22 [negative] (plan-added, refresh) | The scheduling state JSON carries no `shown_turn`: no turn id reaches the model, and a digit-heavy UUID is never masked into a fake card number | R-45; `privacy/redact.py` `_CARD` | `prompts/test_specialist_prompts.py::test_scheduling_state_omits_turn_ids` |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| `SpecialistRunner(*, gateway, transcript, dispatcher, specs, brakes, trace)`, `run(task, scope, ctx)` | graph-tools §2 (GRT-6, R-G-17) | yes | in-ticket | step 3 |
| `scope_for(state, ctx)` | graph-tools §2 | AC-9 | in-ticket | step 3 |
| Tools = `dispatcher.schemas(spec.tool_kinds)` + `report_facts` from `spec.report_model` | graph-tools §2 | AC-2 | in-ticket | step 2 (`report_facts_schema`), step 3 |
| Fresh message list per run; never logged, traced or stored | DO-4 §5; models.md §1; GRT-9 | AC-3, AC-10 | in-ticket | step 3 |
| Gateway halt → `brake`; failure → `failure`; stop | graph-tools §2; DO-4 §11 | AC-4 | in-ticket | step 3 |
| Two tool rounds; identical call; final-answer branch; `report_facts` exit | DO-4 §5 runner rules; agent-architecture 5, 6 | AC-1, AC-2 | in-ticket | step 3 |
| Every result returned with its `tool_call_id` | agent-tools 6; DO-4 §5 | AC-3 | in-ticket | step 3 |
| Never raises | DO-4 §5 | AC-4 | in-ticket + **added** AC-20 (unexpected exception path) | step 3 |
| Results captured by code, not from the report | DO-4 §5; GRT-6 | AC-5 | in-ticket | step 2 |
| `KnowledgePoint` "must be a passage returned in this run" | DO-4 §5; AEA-02 plan §8.3 defers it here | AC-6 | in-ticket | step 2 |
| GRT-7 no top-3 fallback | GRT-7; R-13 | AC-6 | in-ticket | step 2 |
| Quick checks (code-built, not a round, troubleshooting only) | GRT-8; graph-tools §6 | AC-8 | in-ticket | step 3 |
| Tool spans, trace-free dispatcher | R-G-17; DO-6 rule 18 | AC-14 | in-ticket | step 3 |
| No signal, no check event from the runner | GRN-4; graph-nodes §4 | yes | in-ticket (nothing emitted; asserted by AC-10's empty caplog) | step 3 |
| Wording rules: report only tool output; never guess; no charge judgement (R-17); no firm repair prices, no cards (R-13); no fee-bearing move/cancel (R-21, R-22); 12-month minimum (SP-1 §4); date from `ctx.now` (R-3) | ticket; PRD | AC-11, AC-12 | in-ticket | step 1 |
| Turn-2+ full-prompt test | context-management rule 3 | AC-12 | in-ticket | step 6 |
| Fixed per-turn budget | context-management rule 4 | no | **added** AC-21 | step 1 |
| WP-1 worked pair test | build-loop-test-scope; ticket example 1 | no (pair stated, no test named) | **added** AC-17 | step 6 |
| No `if spec.kind` in the runner | DO-3 §4.5 | no | **added** AC-18 | step 3, step 6 |
| `SPECS` complete; report schema = report model's | graph-tools §2; AEA-60 AC-5 | no | **added** AC-19 | step 2 |
| `SpecialistTask` (with `offer_quick_checks`), `KnowledgeSlice`, `AccountSlice` exist in `domain/` | DO-4 §5; graph-tools §2 ("domain/specialists.py (AEA-02)"); AEA-02 ticket row | no | **resolved:** AEA-35b builds them in `domain/tools.py` (option A, Innocent 2026-10-21); it merges before this ticket builds | step 0.2 |
| `SpecialistTask` assembly, `offer_quick_checks` rule, signals, check events, `specialist_results` state key | graph-nodes §4, §9.5; GRT-8 | yes (scope boundary) | other-ticket: AEA-39 (its AC-7 covers signals; `test_act.py::test_quick_checks_rule`) | — |
| Executors, tool names, `for_model` content | graph-tools §1, §4; data.md §4 | yes | other-ticket: AEA-27, AEA-28, AEA-33 | — |
| Wiring (`GraphDeps.specialists`, `runner.transcript is` the gateway's adapter, `runner.trace is` the sink) | graph-tools §2; AEA-51 AC-1 | yes | other-ticket: AEA-51 (this ticket exposes the attributes, PD-8) | — |
| CAP-1 (real entry point captures) | DO-6 | yes | other-ticket: AEA-51 | — |
| E-1 trajectory, E-7 booking validity | DO-5 | yes | other-ticket: AEA-51 (compiled graph with fakes); scored runs Stage 9 | — |
| Prompt ↔ consumer checks | integrated-journeys rule 4 | no | other-ticket: AEA-60 (this ticket exposes `SPECS`, `report_facts_schema`, the rule constants) | — |
| `specs: Mapping[str, SpecialistSpec]` vs `SPECS: Mapping[Literal[…], …]` (mypy: `Mapping` keys are invariant, so the literal-keyed `SPECS` cannot be passed as `Mapping[str, …]`) | graph-tools §2 | no | decided here (PD-7): both typed `Mapping[SpecialistKind, SpecialistSpec]`; reported to AEA-08 (§8.3 R-4) | step 2, 3 |

---

## 4. Shared code to use (exact; verify on `main` in step 0)

### 4.1 Types and where to import them from (AEA-02 homes, per its plan §4.0 table)

```python
# meridian.domain.common (AEA-02)
class MeridianModel(BaseModel)   # extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
class LLMFacing(MeridianModel)
class PassageId(str)             # "<file path>#<chunk n>", pattern ^[^#\s]+#[0-9]+$
class CustomerId(str)            # ^MHC-[0-9]{5}$
class InvoiceId(str)             # ^INV-[0-9]{6}$
class ThreadId(str); class TurnId(str); class RequestId(str)   # canonical lower-case UUID4
class ToolErrorCode(StrEnum)     # not_allowed, bad_arguments, unknown_tool, not_verified, not_shown, fee_bearing,
                                 #   outside_service_area, slot_taken, booking_cap, identical_call, tool_failed,
                                 #   wrong_service_type, not_owned
class ProviderFailureKind(StrEnum)   # timeout, connection, rate_limited, overloaded, server, provider_spend_cap,
                                     #   our_spend_limit, bad_request, auth, not_found, body_error, refusal, max_tokens,
                                     #   invalid_output
class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind; provider: ProviderName; http_status: int | None
    retry_after_s: float | None; retryable: bool; provider_request_id: str | None
class HaltReason(StrEnum):
    DEADLINE = "deadline"; BRAKE_TASKS = "brake_tasks"; BRAKE_TOOL_ROUNDS = "brake_tool_rounds"
    BRAKE_SONNET_CALLS = "brake_sonnet_calls"; BRAKE_IDENTICAL_CALL = "brake_identical_call"
    RECURSION_LIMIT = "recursion_limit"; SPEND_CAP = "spend_cap"; PROVIDER_SPEND_CAP = "provider_spend_cap"
class Halt(MeridianModel): reason: HaltReason; node: str; elapsed_ms: int

# meridian.domain.records (AEA-02)
class Passage(MeridianModel):
    passage_id: PassageId; file: str; section: str; version_label: str; version_date: dt.date | None
    text: str; score: float
class RetrievalResult(MeridianModel): passages: tuple[Passage, ...]; below_floor: bool
class ShownSlot(MeridianModel):
    slot_id: int; date: dt.date; window: Window; technician: str; service_type: ServiceType; zone: Zone
    member_reserved: bool; shown_turn: TurnId
Window = Literal["08:00-12:00", "12:00-16:00", "13:00-17:00", "16:00-19:00"]
ServiceType = Literal["hvac_repair", "hvac_tune_up", "plumbing", "estimate"]
Zone = Literal["north", "central", "south"]
class FeeNote(MeridianModel):
    service_type: ServiceType; tier: Literal["none", "standard", "plus"]; fee_row: str | None
    amount_cents: int = Field(ge=0); waived: bool; line: str = Field(min_length=1, max_length=120)

# meridian.domain.actions (AEA-02)
class ActionKind(StrEnum): BOOKED, MOVED, CANCELLED, CHANGE_REQUEST_SENT, CASE_OPENED, FOLLOWUP_SAVED, VERIFIED
class ActionKey(MeridianModel): thread_id: ThreadId; turn_id: TurnId; kind: ActionKind; record_id: str
class CompletedAction(MeridianModel):
    key: ActionKey; kind: ActionKind
    records: dict[Literal["appointment", "slot", "old_slot", "case", "customer", "promise"], str]
    before: dict[str, str] | None = None; after: dict[str, str] | None = None; at: dt.datetime
    source: Literal["actions_table"] = "actions_table"

# meridian.domain.specialists (AEA-02)
class ConfirmationView(MeridianModel): date: dt.date; window: Window; technician: str; fee_note: FeeNote
class WriteResult(MeridianModel): action: CompletedAction; confirmation: ConfirmationView
class ChangeRequestDraft(MeridianModel):
    appointment_id: int; change: Literal["move", "cancel"]; wanted_text: str; windows_shown: tuple[int, ...]
    hours_before: float; window_start: dt.datetime
class KnowledgePoint(MeridianModel): text: str = Field(max_length=500); passage_id: PassageId
class InvoiceLineView(MeridianModel): description: str; amount_cents: int
class InvoiceView(MeridianModel):
    invoice_id: InvoiceId; lines: tuple[InvoiceLineView, ...]; total_cents: int; balance_cents: int
    issued_on: dt.date; due_on: dt.date; paid: bool
class MembershipView(MeridianModel): tier: Literal["none", "standard", "plus"]; renewal_date: dt.date | None
class WarrantyView(MeridianModel): install_date: dt.date; equipment_brand: str | None; sentence: str
class StaffNote(MeridianModel):
    kind: Literal["billed_differs_from_schedule", "diagnostic_without_credit"]; record_id: InvoiceId
    text: str = Field(max_length=300)
    source_file: Literal["pricing/2026_fee_schedule.pdf", "faq/customer_faq.md"]
class KnowledgeCapture(MeridianModel): kind: Literal["knowledge"] = "knowledge"; result: RetrievalResult
class AccountCapture(MeridianModel):
    kind: Literal["account"] = "account"; invoices: tuple[InvoiceView, ...] = ()
    membership: MembershipView | None = None; warranty: WarrantyView | None = None
    staff_notes: tuple[StaffNote, ...] = ()
class SchedulingCapture(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"; windows: tuple[ShownSlot, ...] = ()
    write: WriteResult | None = None; change_request: ChangeRequestDraft | None = None
    refused: ToolErrorCode | None = None
class AppointmentView(MeridianModel):
    appointment_id: int; date: dt.date; window: Window; service_type: ServiceType; technician: str | None
    is_warranty_visit: bool
class SchedulingSlice(MeridianModel):
    customer_zone: Zone | None; member: bool; appointments: tuple[AppointmentView, ...]
    shown_slots: tuple[ShownSlot, ...]; pending_change: bool; bookings_left: int
class KnowledgeResult(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"; status: Literal["answered", "no_current_source", "failed"]
    passages: tuple[Passage, ...]; points: tuple[KnowledgePoint, ...]; quick_checks: tuple[PassageId, ...] = ()
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None
class AccountResult(MeridianModel):
    kind: Literal["account"] = "account"; status: Literal["read", "not_verified", "failed"]
    invoices: tuple[InvoiceView, ...] = (); membership: MembershipView | None = None
    warranty: WarrantyView | None = None; staff_notes: tuple[StaffNote, ...] = ()
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None
class SchedulingResult(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    status: Literal["windows_shown", "written", "staff_change_request", "slot_taken", "out_of_area", "no_fit",
                    "not_verified", "booking_cap", "failed"]
    windows: tuple[ShownSlot, ...] = (); write: WriteResult | None = None
    change_request: ChangeRequestDraft | None = None; quick_checks: tuple[Passage, ...] = ()
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None
SpecialistResult = Annotated[KnowledgeResult | AccountResult | SchedulingResult, Field(discriminator="kind")]
class ReportedPoint(LLMFacing): text: str = Field(max_length=500); passage_id: PassageId
class KnowledgeReport(LLMFacing): points: list[ReportedPoint] = Field(max_length=5); answered: bool
class AccountReport(LLMFacing): summary: str = Field(max_length=300)
class SchedulingReport(LLMFacing): appointment_id: int; wanted_time: str; note: str = Field(max_length=200)

# meridian.domain.tools (AEA-35b, `68f7f19`; home chosen by Innocent 2026-10-21, option A). Copied from the branch.
class KnowledgeSlice(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"          # kind-only marker: the knowledge specialist sees only the text
class AccountSlice(MeridianModel):
    kind: Literal["account"] = "account"              # kind-only marker: account tools get the customer from scope
class SpecialistTask(MeridianModel):
    task: PlannedTask
    customer_text: str                                # SONNET profile
    task_messages: tuple[str, ...]                    # same profile
    slice: KnowledgeSlice | AccountSlice | SchedulingSlice
    offer_quick_checks: bool = False
# This plan reads ONLY these five fields, and reads `slice` only through `slice.model_dump(mode="json")`.

# meridian.domain.turn (AEA-02)
SpecialistKind = Literal["knowledge", "account", "scheduling"]
class TaskIntent(StrEnum):
    ANSWER_QUESTION = "answer_question"; READ_INVOICE = "read_invoice"; READ_MEMBERSHIP = "read_membership"
    READ_APPOINTMENTS = "read_appointments"; READ_WARRANTY = "read_warranty"; BOOK_NEW = "book_new"
    RESCHEDULE = "reschedule"; CANCEL = "cancel"; CONFIRM = "confirm"
class PlannedTask(MeridianModel):
    order: int = Field(ge=1, le=3); specialist: SpecialistKind; intent: TaskIntent; needs_identity: bool
    resumes_task_id: str | None = None
class TurnIds(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId; run_tag: Literal["live", "eval", "load"]
    run_id: str | None; agent_version: str
@dataclass(frozen=True)
class TurnBudget: started: float; deadline: float          # remaining(), timeout_for(cap_s, min_call_s=1.0)
@dataclass(frozen=True)
class SpanHandle: turn_id: TurnId; trace_id: str | None; native: object = field(default=None, compare=False, repr=False)
@dataclass(frozen=True)
class TurnContext:
    ids: TurnIds; budget: TurnBudget; now: dt.datetime; demo_session: str; span: SpanHandle
    intake: Intake | None = None
class TurnInput(MeridianModel):
    turn_id: TurnId; message_id: int; kind: Literal["text", "choice", "code", "form"]; text_store: str
    card_id: str | None = None; choice: CardChoice | None = None; card_number_seen: bool = False
    received_at: dt.datetime

# meridian.domain.identity (re-exported by meridian.domain.state)
class IdentityState(MeridianModel):
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None; masked_hint: str | None; code_expires_at: dt.datetime | None
    tries_left: int = Field(ge=0, le=3); codes_sent: int = Field(ge=0, le=3); verified_at: dt.datetime | None

# meridian.domain.state (AEA-02) — only thread_id and turn_input are required (AEA-02 D-9)
class ConversationState(MeridianModel):
    thread_id: ThreadId; identity: IdentityState = <not_checked default>; shown_slots: list[ShownSlot] = []
    turn_input: TurnInput; ...                       # other keys have defaults; this ticket reads only these three

# meridian.domain.tools (AEA-02; ToolKind and ToolCallRecord re-exported from domain.common)
class ToolKind(StrEnum):
    KB_SEARCH = "kb_search"; ACCOUNT_READ = "account_read"; SLOT_SEARCH = "slot_search"
    BOOK = "book"; MOVE = "move"; CANCEL = "cancel"; CHANGE_REQUEST = "change_request"
class ToolCallRecord(MeridianModel):
    tool_call_id: str; name: str = Field(max_length=64); kind: ToolKind | None
    outcome: Literal["ok", "refused", "failed"]; error: ToolErrorCode | None
    record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]; lookup_id: int | None; elapsed_ms: int
class ToolCallScope(MeridianModel):
    ids: TurnIds; customer_id: CustomerId | None; shown_slot_ids: frozenset[int]; now: dt.datetime; message_id: int
class LookupEntry(MeridianModel):
    tool: str; record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]; result_seen: str
    message_id: int; turn_id: TurnId
class ToolError(MeridianModel): code: ToolErrorCode; message: str; retryable: bool
Capture = Annotated[KnowledgeCapture | AccountCapture | SchedulingCapture, Field(discriminator="kind")]
class ToolResult(MeridianModel):
    ok: bool; for_model: ToolError | JsonValue = Field(union_mode="left_to_right"); captured: Capture | None
    lookup: LookupEntry; lookup_written: bool

# meridian.ports.models (AEA-02; Role, ProviderName, ProviderCall, CallRecord re-exported from domain.common)
class Role(StrEnum): PLANNER; CLASSIFIER; PLANNER_FALLBACK; SPECIALIST = "specialist"; RESPONDER; BRIEF
ToolRole = Literal[Role.SPECIALIST]
class ToolSchema(MeridianModel): name: str; description: str; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolCall(MeridianModel): id: str; name: str; args: dict[str, JsonValue] | None
class ProviderMessages(MeridianModel): provider: ProviderName; model: str; items: tuple[JsonValue, ...]
class ToolStepRequest(MeridianModel):
    system_prefix: str; system_dynamic: str; messages: ProviderMessages; tools: tuple[ToolSchema, ...]
    max_tokens: int; effort: Literal["low", "medium", "high"] | None
class ToolStep(MeridianModel): text: str; tool_calls: tuple[ToolCall, ...]; raw: ProviderTurn; stop_reason: str | None
ProviderTurn = JsonValue
class CallRecord(ProviderCall): role: Role; attempt: int = Field(ge=1, le=2)   # + from_provider(call, *, role, attempt)
class ToolTranscript(Protocol):
    def start(self, user: str) -> ProviderMessages: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...

# meridian.ports.runtime (AEA-02)
class TraceSink(Protocol):
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...   # (+ turn, model_call, export_status)
```

### 4.2 Collaborators (wave 1)

```python
# meridian.agent.gateway (AEA-20)
class ModelOutcome[T: BaseModel](MeridianModel):
    value: T | None; calls: tuple[CallRecord, ...]; failure: ProviderFailure | None; halt: Halt | None
class ModelGateway:
    def tool_step(self, role: ToolRole, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[ToolStep]: ...
    # Never raises on a provider failure. Returns halt=DEADLINE / BRAKE_SONNET_CALLS / PROVIDER_SPEND_CAP (the last
    #   one may come WITH failure set). Replaces req.max_tokens and req.effort with the role's RoleSpec values and
    #   SONNET-redacts system_prefix and system_dynamic; passes `messages` and `tools` through untouched.

# meridian.agent.tools.dispatch (AEA-22)
class DispatchedCall(MeridianModel):
    tool_call_id: str; content: str; result: ToolResult; record: ToolCallRecord
class ToolDispatcher:
    def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]: ...     # cached per kind set, by name
    def dispatch(self, calls: Sequence[ToolCall], *, kinds: frozenset[ToolKind],
                 scope: ToolCallScope) -> tuple[DispatchedCall, ...]: ...           # same length/order; never raises;
                                                                                    #   one lookup_log row per call

# meridian.policy.limits (AEA-01, on main)
@dataclass(frozen=True)
class Brakes: tasks_per_turn: int = 3; tool_rounds: int = 2; sonnet_calls: int = 6

# meridian.privacy.redact (AEA-04, on main)
class RedactionProfile(StrEnum): STORE, SONNET = "sonnet", JEV, TRACE, LOG
def redact(text: str, profile: RedactionProfile) -> Redacted          # Redacted.text; idempotent
```

### 4.3 Test support (AEA-11, `tests/fakes`)

```python
from tests.fakes import (CHICAGO, WORKED_PAIRS_NOW, FakeToolModel, InMemoryTraceSink, ScriptedFailure,
                         provider_call)
# WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=CHICAGO)
# FakeToolModel(script: Sequence[ToolStep | ScriptedFailure | Attempt[ToolStep]], *, provider="anthropic",
#               model="claude-sonnet-5-5")
#   .start(user) -> ProviderMessages(items=({"role": "user", "content": user},)); records user in .starts
#   .tool_step(req, *, timeout_s) -> Attempt[ToolStep]; records req in .requests
#   .append(messages, step, results) -> ProviderMessages; records (messages, step, tuple(results)) in .appends
#   an exhausted script raises ScriptExhaustedError (a BaseException: `except Exception` never hides it)
# InMemoryTraceSink(): `with sink.turn(ids) as span:` yields SpanHandle; sink.spans_for(span).nodes ->
#   list[RecordedNode(name, elapsed_ms, status)]; node() raises ValueError for a handle it did not open
# provider_call(*, provider, model, failure=None, ...) -> ProviderCall
```

### 4.4 `src/meridian/agent/prompts/specialists.py` — exact content of the wording (decided here)

Module docstring (one paragraph): "Specialist wording (AEA-35; DO-3 S-14; graph-tools §2). Each `render_*` returns
`(system_prefix, system_dynamic, user)`: a stable, cache-controlled prefix that never changes between turns, a per-run
line with today's demo-clock date, and the task text. Starts from SP-1's measured wording (build step 8)."

Imports (exactly these; absolute):

```python
from __future__ import annotations

import json
from types import MappingProxyType
from typing import Final
from zoneinfo import ZoneInfo

from pydantic.main import IncEx                               # pydantic 2.14: the type of model_dump's `exclude`

from meridian.domain.tools import SpecialistTask               # AEA-35b (§4.1)
from meridian.domain.turn import TaskIntent, TurnContext
from meridian.privacy.redact import RedactionProfile, redact
```

Constants (copy the strings **exactly**; one statement per line; the triple-quoted layout below is for reading — build
each with parenthesised string concatenation):

```python
REPORT_FACTS_TOOL: Final = "report_facts"
REPORT_FACTS_DESCRIPTION: Final = (
    "Report what your tools returned, then stop. Call it exactly once, after your other tools. "
    "Use only values the tools returned for this task; leave out anything they did not return."
)

RULE_NEVER_TALK: Final = "You never talk to the customer; another step writes the reply."
RULE_USE_TOOLS: Final = "Use your tools, then call report_facts exactly once with what you found."
RULE_REPORT_ONLY: Final = "Report only what the tools returned; never guess."
RULE_NO_FIRM_PRICES: Final = (
    "Never state a firm price for a repair; the technician confirms pricing on site. "
    "Published fees and membership prices may be reported exactly as a tool returned them."
)
RULE_NO_CARDS: Final = "Never ask for or accept a card number; payments are never taken in chat."
RULE_MASKED: Final = (
    "Text in square brackets, such as [code] or [email], was hidden before you saw it; "
    "never ask for the hidden value."
)

KNOWLEDGE_RULES: Final = (
    "Call kb_search with a short query for each question in the task, at most 2 searches. "
    "Report up to 5 points that answer the task. Copy each point closely from one passage and give that "
    "passage's passage_id exactly as kb_search returned it. "
    "If the passages do not answer the task, report answered=false and no points. "
    "When you report the Comfort Club monthly price, also report its 12-month minimum."
)
ACCOUNT_RULES: Final = (
    "Call the read tool that matches the task once: read_invoices, read_membership or read_warranty. "
    "Then call report_facts with a one-sentence summary. "
    "Report invoice amounts exactly as billed. Never judge whether a charge is right, never say a charge is wrong "
    "or that money is owed back, and never compare a bill with a price list; a person reviews any question about "
    "a charge."
)
SCHEDULING_RULES: Final = (
    "Service types: hvac_repair (repairs; AC or heat not working), hvac_tune_up, plumbing, estimate "
    "(new system quotes). Windows: 08:00-12:00, 12:00-16:00, 13:00-17:00, and 16:00-19:00 on Tuesday and "
    "Thursday only. "
    "For a new booking: search for open windows that match the customer's wanted days and times; book only a "
    "slot in STATE.shown_slots that the customer has picked. "
    "For a change to an existing visit: STATE.appointments lists the customer's visits; choose the one they mean. "
    "A move or cancel within 24 hours of the visit's window start carries the late-change fee: never move or "
    "cancel that visit. You may search for windows to show, then record a change request with the customer's "
    "wanted time in their own words. "
    "Otherwise move a visit only to a slot in STATE.shown_slots that the customer has picked, and cancel only "
    "when the customer has asked to cancel. "
    "Code refuses any booking or move to a slot not yet shown to the customer and any move or cancel that "
    "carries the fee; when a tool refuses, do not repeat the same call. "
    "In report_facts give appointment_id (0 if none), wanted_time (the customer's words, or an empty string) "
    "and a one-line note."
)

def _prefix(kind: str, rules: str) -> str:
    return "\n".join((
        f"You are the {kind} specialist inside Meridian Home Comfort's chat system.",
        RULE_NEVER_TALK, RULE_USE_TOOLS, RULE_REPORT_ONLY, RULE_NO_FIRM_PRICES, RULE_NO_CARDS, RULE_MASKED,
        "", rules,
    ))

KNOWLEDGE_PREFIX: Final = _prefix("knowledge", KNOWLEDGE_RULES)
ACCOUNT_PREFIX: Final = _prefix("account", ACCOUNT_RULES)
SCHEDULING_PREFIX: Final = _prefix("scheduling", SCHEDULING_RULES)

TASK_LABELS: Final = MappingProxyType({
    TaskIntent.ANSWER_QUESTION: "answer the customer's question from the knowledge base",
    TaskIntent.READ_INVOICE: "read the customer's invoices",
    TaskIntent.READ_MEMBERSHIP: "read the customer's membership",
    TaskIntent.READ_APPOINTMENTS: "read the customer's appointments",
    TaskIntent.READ_WARRANTY: "read the customer's warranty",
    TaskIntent.BOOK_NEW: "book a new visit",
    TaskIntent.RESCHEDULE: "move an existing visit",
    TaskIntent.CANCEL: "cancel an existing visit",
    TaskIntent.CONFIRM: "confirm an existing visit",
})

MAX_TASK_MESSAGES: Final = 6          # [A] per-turn budget (context-management rule 4); replaced by the E-1 run
MAX_MESSAGE_CHARS: Final = 1_000      # [A] each task message cut to this with "…"
_SCHEDULING_STATE_EXCLUDE: Final[IncEx] = {"shown_slots": {"__all__": {"shown_turn"}}}   # PD-16: no turn id
_CHICAGO: Final = ZoneInfo("America/Chicago")
```

Why the scheduling wording names no scheduling tool: those names are AEA-28's choice (graph-tools §1 "names are
AEA-28's choice"); the model routes by each tool's own description (agent-tools rule 2), and AEA-60 checks that every
tool name the wording mentions is among the tools sent (AEA-60 AC-5). Knowledge names `kb_search` (data.md §4) and
account names `read_invoices`, `read_membership`, `read_warranty` (graph-tools §4): both are fixed by contracts.

Functions (pure; no I/O, no clock, no logging):

```python
def render_knowledge(task: SpecialistTask, ctx: TurnContext) -> tuple[str, str, str]:
    return KNOWLEDGE_PREFIX, _dynamic(ctx), _user(task)
def render_account(task: SpecialistTask, ctx: TurnContext) -> tuple[str, str, str]:
    return ACCOUNT_PREFIX, _dynamic(ctx), _user(task)
def render_scheduling(task: SpecialistTask, ctx: TurnContext) -> tuple[str, str, str]:
    return SCHEDULING_PREFIX, _dynamic(ctx), _user(task, exclude=_SCHEDULING_STATE_EXCLUDE)
```

`_dynamic(ctx)` (R-3: the demo clock, never `datetime.now()` and never a fixed string):
1. `now = ctx.now.astimezone(_CHICAGO)`.
2. Return `f"Today is {now:%A}, {now:%B} {now.day}, {now.year}, {now:%H:%M} (America/Chicago)."`
   Example: WORKED_PAIRS_NOW → `"Today is Friday, October 16, 2026, 10:00 (America/Chicago)."`

`_user(task: SpecialistTask, *, exclude: IncEx | None = None) -> str` (R-45: only the task's slice; context-management rule 4:
bounded):
1. `messages = list(task.task_messages[-MAX_TASK_MESSAGES:])`.
2. If `not messages or messages[-1] != task.customer_text`: append `task.customer_text`, then keep the last
   `MAX_TASK_MESSAGES` again. *Invariant:* the latest message is always present, at most once.
3. Cut each: `m if len(m) <= MAX_MESSAGE_CHARS else m[: MAX_MESSAGE_CHARS - 1] + "…"`.
4. `state = json.dumps(task.slice.model_dump(mode="json", exclude=exclude), ensure_ascii=False, sort_keys=True,
   indent=1)`. *Invariant:* the model sees the slice's values, never a turn id (PD-16; only `render_scheduling`
   passes an `exclude`, because only `SchedulingSlice` holds `ShownSlot`s).
5. Text, lines joined with `"\n"`:
   `f"TASK: {TASK_LABELS[task.task.intent]}"`, `"CUSTOMER MESSAGES FOR THIS TASK (oldest first):"`, then one line
   `f"- {m}"` per message, then `"STATE (JSON):"`, then `state`.
6. Return `redact(text, RedactionProfile.SONNET).text`. *Invariant:* even if a caller passes unmasked text, no code,
   card-like number, full phone, email or street line reaches the model; SONNET is idempotent, so already-masked text
   is unchanged (data.md §1). The runner adds no value of its own (GRT-9).

### 4.5 `src/meridian/agent/specialists/specs.py`

Module docstring: "The three specialists as data (AEA-35; DO-3 §4.5, S-12; graph-tools §2–§3, GRT-6, GRT-7). Each
`SpecialistSpec` names its tool kinds, report model, wording and result builder. Builders fold what the tools
captured into the result and never read model text for a record value."

Imports (ruff `I` sorts them; drop any name ruff `F401` reports unused, e.g. `ShownSlot`, `InvoiceView`, `StaffNote` if a builder does not name them):

```python
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from meridian.agent.prompts.specialists import (
    REPORT_FACTS_DESCRIPTION,
    REPORT_FACTS_TOOL as REPORT_FACTS_TOOL,
    render_account,
    render_knowledge,
    render_scheduling,
)
from meridian.domain.common import HaltReason, LLMFacing, PassageId, ProviderFailure, ToolErrorCode
from meridian.domain.records import Passage, ShownSlot
from meridian.domain.specialists import (
    AccountCapture, AccountReport, AccountResult, InvoiceView, KnowledgeCapture, KnowledgePoint, KnowledgeReport,
    KnowledgeResult, SchedulingCapture, SchedulingReport, SchedulingResult, SpecialistResult, StaffNote,
)
from meridian.domain.tools import SpecialistTask, ToolCallRecord, ToolKind
from meridian.domain.turn import SpecialistKind, TurnContext
from meridian.ports.models import CallRecord, ToolSchema
```

Public names (`__all__`, sorted): `REPORT_FACTS_TOOL`, `SPECS`, `TROUBLESHOOTING_FILE`, `RunOutcome`,
`SpecialistSpec`, `build_account_result`, `build_knowledge_result`, `build_scheduling_result`, `report_facts_schema`.

```python
TROUBLESHOOTING_FILE: Final = "faq/troubleshooting_before_you_call.md"   # graph-tools §6; DO-4 §5 quick_checks

Capture = KnowledgeCapture | AccountCapture | SchedulingCapture         # module-private alias name: _Capture

@dataclass(frozen=True)
class RunOutcome:                     # graph-tools §2, fields exactly; never leaves the run
    task: SpecialistTask
    captured: tuple[KnowledgeCapture | AccountCapture | SchedulingCapture, ...]  # model rounds only, in order
    passages_returned: tuple[Passage, ...]   # every passage a model-requested kb_search returned, de-duplicated by
                                             #   passage_id, first occurrence kept (quick-check passages excluded, PD-3)
    report: LLMFacing | None                 # the validated report_facts args, or None
    quick_checks: tuple[Passage, ...]        # graph-tools §6; () unless the task asked for the offer
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None
    failure: ProviderFailure | None

@dataclass(frozen=True)
class SpecialistSpec:                 # graph-tools §2, fields exactly
    kind: SpecialistKind
    tool_kinds: frozenset[ToolKind]
    report_model: type[LLMFacing]
    render: Callable[[SpecialistTask, TurnContext], tuple[str, str, str]]
    build_result: Callable[[RunOutcome], SpecialistResult]

def report_facts_schema(spec: SpecialistSpec) -> ToolSchema:
    return ToolSchema(name=REPORT_FACTS_TOOL, description=REPORT_FACTS_DESCRIPTION,
                      input_schema=spec.report_model.model_json_schema(), strict=True)
    # PD-9: the report model's own schema, untrimmed (AEA-60 AC-5 compares it to spec.report_model's).
```

`input_schema` is typed `dict[str, JsonValue]`; `model_json_schema()` returns `dict[str, Any]`. If mypy rejects the
assignment, wrap it: `cast("dict[str, JsonValue]", spec.report_model.model_json_schema())` (import `cast` from
`typing`, `JsonValue` from `pydantic`).

**`build_knowledge_result(outcome: RunOutcome) -> KnowledgeResult`** (GRT-7, R-13). Steps:
1. `caps = [c for c in outcome.captured if isinstance(c, KnowledgeCapture)]`.
2. `citable: set[PassageId] = {p.passage_id for c in caps if not c.result.below_floor for p in c.result.passages}`.
   *Invariant:* a passage counts only if a search **this run** returned it above the floor.
3. `report = outcome.report if isinstance(outcome.report, KnowledgeReport) else None`.
4. `points: tuple[KnowledgePoint, ...] = ()`; if `report is not None and report.answered`:
   `points = tuple(KnowledgePoint(text=p.text, passage_id=p.passage_id) for p in report.points if p.passage_id in citable)`.
   *Invariant:* a point citing a passage not returned this run is dropped, never repaired.
5. `quick = tuple(p.passage_id for p in outcome.passages_returned if p.file == TROUBLESHOOTING_FILE and p.passage_id in citable)`.
6. Status: `outcome.failure is not None` → `"failed"` (and `points = ()`); else `points` non-empty → `"answered"`;
   else `"no_current_source"` (and `points = ()`). *Invariant:* no SP-1 top-3 fallback (GRT-7).
7. Return `KnowledgeResult(status=…, passages=outcome.passages_returned, points=points, quick_checks=quick,
   tools=outcome.tools, calls=outcome.calls, brake=outcome.brake, failure=outcome.failure)`.

**`build_account_result(outcome: RunOutcome) -> AccountResult`** (R-17, HP-3). Steps:
1. `caps = [c for c in outcome.captured if isinstance(c, AccountCapture)]`.
2. `invoices`: every `InvoiceView` of every cap, in order, de-duplicated by `invoice_id` (first kept).
3. `membership` = the last non-None `c.membership`; `warranty` = the last non-None `c.warranty`.
4. `staff_notes`: every note of every cap, in order, de-duplicated by `(kind, record_id, text)` (first kept).
   *Invariant:* staff notes are copied for the brief and case view only; they never enter wording or a request (HP-3).
5. Status: `failure` → `"failed"`; else `caps` non-empty → `"read"`; else any `r.error == ToolErrorCode.NOT_VERIFIED`
   in `outcome.tools` → `"not_verified"`; else `"failed"`.
6. Return `AccountResult(status, invoices, membership, warranty, staff_notes, tools, calls, brake, failure)`.
   `AccountReport.summary` is not copied anywhere (AccountResult names no such field; DO-4 §5).

**`build_scheduling_result(outcome: RunOutcome) -> SchedulingResult`** (R-18…R-22, WP-4). Steps:
1. `caps = [c for c in outcome.captured if isinstance(c, SchedulingCapture)]`.
2. `write` = last non-None `c.write`; `change_request` = last non-None `c.change_request`.
3. `windows` = the `windows` of the **last** cap whose `windows` is non-empty, else `()`. *Invariant:* the latest
   search is the offer; values are the captured `ShownSlot`s exactly (AC-5).
4. `refusal`: walk `outcome.tools` in order; for each record whose `error` is a key of
   `_REFUSAL_STATUS = MappingProxyType({ToolErrorCode.NOT_VERIFIED: "not_verified", ToolErrorCode.SLOT_TAKEN:
   "slot_taken", ToolErrorCode.OUTSIDE_SERVICE_AREA: "out_of_area", ToolErrorCode.BOOKING_CAP: "booking_cap"})`,
   set `refusal` to the mapped value (the last one wins). Records carry both the dispatch guard's `not_verified` and
   the executor's `Refused.code` (AEA-28 maps it one-to-one into `ToolError` and `SchedulingCapture.refused`, C-7).
5. `searched_empty` = any cap with `not c.windows and c.write is None and c.change_request is None and c.refused is None`.
6. Status, first match: `failure` → `"failed"`; `write` → `"written"`; `change_request` → `"staff_change_request"`;
   `refusal` → `refusal`; `windows` → `"windows_shown"`; `searched_empty` → `"no_fit"`; else `"failed"`.
   *Invariant:* a fee-bearing request is never a write (WP-4: `write=None`, R-21).
7. Return `SchedulingResult(status, windows, write, change_request, quick_checks=outcome.quick_checks, tools, calls,
   brake, failure)`. `SchedulingReport` fields are not copied (SchedulingResult names none of them).

```python
SPECS: Final[Mapping[SpecialistKind, SpecialistSpec]] = MappingProxyType({
    "knowledge": SpecialistSpec(kind="knowledge", tool_kinds=frozenset({ToolKind.KB_SEARCH}),
                                report_model=KnowledgeReport, render=render_knowledge,
                                build_result=build_knowledge_result),
    "account": SpecialistSpec(kind="account", tool_kinds=frozenset({ToolKind.ACCOUNT_READ}),
                              report_model=AccountReport, render=render_account, build_result=build_account_result),
    "scheduling": SpecialistSpec(kind="scheduling",
                                 tool_kinds=frozenset({ToolKind.SLOT_SEARCH, ToolKind.BOOK, ToolKind.MOVE,
                                                       ToolKind.CANCEL, ToolKind.CHANGE_REQUEST}),
                                 report_model=SchedulingReport, render=render_scheduling,
                                 build_result=build_scheduling_result),
})
```

Builders are pure and cannot raise on valid inputs (every value they build comes from already-validated models with
the same constraints). Keep the file ≤ 400 lines.

### 4.6 `src/meridian/agent/specialists/runner.py`

Module docstring: "The braked tool loop for one specialist task (AEA-35; DO-4 §5 runner rules; graph-tools §2, §6;
R-G-17). Never raises; emits no signal and no check event; logs no message text; the provider message list lives for
one run only."

Imports:

```python
from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final

from pydantic import ValidationError

from meridian.agent.gateway import ModelGateway
from meridian.agent.specialists.specs import (
    REPORT_FACTS_TOOL, TROUBLESHOOTING_FILE, RunOutcome, SpecialistSpec, report_facts_schema,
)
from meridian.agent.tools.dispatch import DispatchedCall, ToolDispatcher
from meridian.domain.common import HaltReason, LLMFacing, ProviderFailure
from meridian.domain.records import Passage
from meridian.domain.specialists import (
    AccountCapture, KnowledgeCapture, SchedulingCapture, SpecialistResult,
)
from meridian.domain.state import ConversationState
from meridian.domain.tools import SpecialistTask, ToolCallRecord, ToolCallScope, ToolKind
from meridian.domain.turn import SpecialistKind, TurnContext
from meridian.policy.limits import Brakes
from meridian.ports.models import CallRecord, ProviderMessages, Role, ToolCall, ToolStep, ToolStepRequest, ToolTranscript
from meridian.ports.runtime import TraceSink
```

Module constants:

```python
_log = logging.getLogger(__name__)                      # "meridian.agent.specialists.runner"
_QC_PREFIX: Final = "qc-"
_QC_KINDS: Final = frozenset({ToolKind.KB_SEARCH})
_QC_QUERY_CHARS: Final = 300                            # KbSearchArgs.query max_length (data.md §4)
_REQUEST_MAX_TOKENS: Final = 3_000                      # placeholder: the gateway replaces it with RoleSpec.max_tokens
_REQUEST_EFFORT: Final = None                           #   and RoleSpec.effort (AEA-20 _redact_tool; PD-12)
```

`__all__ = ["SpecialistRunner", "scope_for"]`.

**`scope_for(state: ConversationState, ctx: TurnContext) -> ToolCallScope`** (pure; GRC-10):

```python
return ToolCallScope(
    ids=ctx.ids,
    customer_id=state.identity.customer_id if state.identity.status == "verified" else None,
    shown_slot_ids=frozenset(s.slot_id for s in state.shown_slots),
    now=ctx.now,
    message_id=state.turn_input.message_id,
)
```

**Private accumulator** (one per run; never shared between runs):

```python
@dataclass
class _Run:
    captured: list[KnowledgeCapture | AccountCapture | SchedulingCapture] = field(default_factory=list)
    passages: dict[str, Passage] = field(default_factory=dict)      # passage_id -> first Passage (insertion order)
    quick_checks: list[Passage] = field(default_factory=list)
    tools: list[ToolCallRecord] = field(default_factory=list)
    calls: list[CallRecord] = field(default_factory=list)
    report: LLMFacing | None = None
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None
    broken: bool = False                                            # an exception or an empty step: status "failed"

    def outcome(self, task: SpecialistTask) -> RunOutcome: ...      # tuples of every list; passages.values()
```

**`class SpecialistRunner`**:

```python
def __init__(self, *, gateway: ModelGateway, transcript: ToolTranscript, dispatcher: ToolDispatcher,
             specs: Mapping[SpecialistKind, SpecialistSpec], brakes: Brakes, trace: TraceSink) -> None:
    self.gateway = gateway          # public read-only by convention: AEA-51 asserts `runner.transcript is` the
    self.transcript = transcript    #   gateway's SPECIALIST adapter and `runner.trace is` the container's sink (PD-8)
    self.dispatcher = dispatcher
    self.specs = specs
    self.brakes = brakes
    self.trace = trace
```

`run(self, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext) -> SpecialistResult`:

1. `spec = self.specs[task.task.specialist]` — a lookup, never a branch on the kind (DO-3 §4.5). This line sits
   **outside** the `try`: a missing kind is a wiring bug that AEA-51's start-up check and AC-19 exclude.
2. `run = _Run()`.
3. `try: self._loop(spec, task, scope, ctx, run)` / `except Exception as exc:` → `run.broken = True` and
   `_log.error("specialist_run_error kind=%s error_type=%s turn_id=%s", spec.kind, type(exc).__name__,
   ctx.ids.turn_id)`. Never log `str(exc)`, `repr(exc)` or `exc_info` (they may hold message text). *Invariant:*
   never raises (DO-4 §5); `ScriptExhaustedError` (a `BaseException`, AEA-11) still escapes in tests, on purpose.
4. `result = spec.build_result(run.outcome(task))`.
5. If `run.broken`: `result = result.model_copy(update={"status": "failed"})` ("failed" is a legal status for all
   three kinds; `failure` stays None, so AEA-39 reports cause `tool_error`).
6. Return `result`.

`_loop(self, spec, task, scope, ctx, run) -> None` — the numbered loop rules (each protects the invariant named):

1. **Tools sent.** `tools = (*self.dispatcher.schemas(spec.tool_kinds), report_facts_schema(spec))`. `report_facts` is
   offered to the model but is never passed to `dispatch` (AC-2).
2. **Wording and a fresh list.** `prefix, dynamic, user = spec.render(task, ctx)`; `messages =
   self.transcript.start(user)`. *Invariant:* each run starts a new `ProviderMessages` holding only this task's text
   (R-45, GRT-9); it is a local variable, never stored on `self`, logged, traced or returned (AC-3, AC-10).
3. **Quick check (GRT-8)**, only when `task.offer_quick_checks` is True, before the first model step:
   1. `qc = ToolCall(id=f"{_QC_PREFIX}{ctx.ids.turn_id}", name="kb_search", args={"query": task.customer_text[:_QC_QUERY_CHARS]})`.
   2. `dispatched = self.dispatcher.dispatch((qc,), kinds=_QC_KINDS, scope=scope)`.
   3. `self._take(dispatched, ctx, run, model_round=False)` (record + span; not captured, not citable, PD-3).
   4. For each `d` in `dispatched`: if `isinstance(d.result.captured, KnowledgeCapture) and not
      d.result.captured.result.below_floor`: extend `run.quick_checks` with the passages whose `file ==
      TROUBLESHOOTING_FILE`. *Invariant:* nothing is offered when no troubleshooting passage clears the floor.
   It is **not** a tool round, is not added to `seen`, and its `content` is not appended (no model asked for it).
4. `rounds = 0`; `seen: set[tuple[str, str]] = set()`.
5. `for _ in range(self.brakes.tool_rounds + 1):` (a hard bound: at most 2 rounds + 1 final step)
   1. `out = self.gateway.tool_step(Role.SPECIALIST, ToolStepRequest(system_prefix=prefix, system_dynamic=dynamic,
      messages=messages, tools=tools, max_tokens=_REQUEST_MAX_TOKENS, effort=_REQUEST_EFFORT), ctx)`.
   2. `run.calls.extend(out.calls)` (every attempt's `CallRecord`, AC-13).
   3. If `out.halt is not None`: `run.brake = out.halt.reason`. If `out.failure is not None`: `run.failure =
      out.failure`. If either was set: `return` (no further step; AC-4).
   4. `step = out.value`; if `step is None`: `run.broken = True`; `return` (a contract breach by the gateway).
   5. `reports = [c for c in step.tool_calls if c.name == REPORT_FACTS_TOOL]`;
      `calls = [c for c in step.tool_calls if c.name != REPORT_FACTS_TOOL]`.
   6. If `run.report is None`: for each `c` in `reports`: if `c.args is not None`, try
      `run.report = spec.report_model.model_validate(c.args)` and `break`; on `ValidationError`, continue (an invalid
      report is ignored, never raised; AC-20).
   7. If `not calls`: `return` (final-answer branch, or a report-only step; AC-2).
   8. If `rounds >= self.brakes.tool_rounds`: `run.brake = HaltReason.BRAKE_TOOL_ROUNDS`; `return` (nothing from this
      step is dispatched; AC-1).
   9. Split by identity: `new, dup = [], []`; for each `c` in `calls`: `key = (c.name, json.dumps(c.args,
      sort_keys=True, separators=(",", ":"), ensure_ascii=False))`; if `key in seen` → `dup.append(c)`; else
      `seen.add(key)` and `new.append(c)`. *Invariant:* the same name with the same canonical arguments is never
      dispatched twice in a run (AC-2), including twice inside one step.
   10. If `new`: `dispatched = self.dispatcher.dispatch(tuple(new), kinds=spec.tool_kinds, scope=scope)`;
       `self._take(dispatched, ctx, run, model_round=True)`; `rounds += 1`; `messages = self.transcript.append(messages,
       step, [(d.tool_call_id, d.content) for d in dispatched])`. *Invariant:* every dispatched call's `content`
       goes back under its own `tool_call_id` (AC-3); a `tool_failed` content reaches the model like any other (AC-4).
   11. If `dup`: `run.brake = HaltReason.BRAKE_IDENTICAL_CALL`; `return`.
   12. If `reports`: `return` (`report_facts` ends the run after its sibling calls were dispatched).
6. After the `for` loop: nothing (unreachable in practice: the last iteration either returns at 5.7 or brakes at 5.8).

`_take(self, dispatched: Sequence[DispatchedCall], ctx: TurnContext, run: _Run, *, model_round: bool) -> None`:
for each `d` in order:
1. `run.tools.append(d.record)` (one `ToolCallRecord` per dispatched call, AC-13).
2. `self.trace.node(ctx.span, _span_name(d.record), d.record.elapsed_ms, d.record.outcome)` (R-G-17, AC-14; no
   arguments, no result text).
3. If `model_round and d.result.captured is not None`: `run.captured.append(d.result.captured)`; if it is a
   `KnowledgeCapture`: for each passage, `run.passages.setdefault(str(p.passage_id), p)`.

`_span_name(record: ToolCallRecord) -> str`: `"tool:" + record.name if record.kind is not None else "tool:unknown"`.
*Invariant:* a model-supplied unknown name (kind None) never becomes a span name.

Keep the file ≤ 300 lines. No `if spec.kind`, no string literal `"knowledge"`, `"account"` or `"scheduling"` anywhere
in `runner.py` (AC-18).

---

## 5. Steps (build order; each step ends with a check)

Work in the worktree and branch the orchestrator gives you (for example
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-35`, branch `aea-35-specialists`). Before any `uv` command:
`export UV_LINK_MODE=hardlink`. Never copy a venv; no `node_modules`; never read `.env`; bind no port.

**Step 0 — preflight (no code).** On the branch, with `main` merged in:
1. `git log --oneline -1 main` and confirm AEA-02, AEA-11, AEA-20, AEA-22 are merged (they are at `f466ff7`):
   `ls src/meridian/agent/gateway.py src/meridian/agent/tools/dispatch.py tests/fakes/models.py tests/fakes/trace.py`.
2. `grep -n "^class SpecialistTask\|^class KnowledgeSlice\|^class AccountSlice" src/meridian/domain/tools.py` must
   print three lines (AEA-35b merged). Then
   `uv run python -c "from meridian.domain.tools import AccountSlice, KnowledgeSlice, SpecialistTask; print(KnowledgeSlice(), AccountSlice(), sorted(SpecialistTask.model_fields))"`
   → `kind='knowledge' kind='account' ['customer_text', 'offer_quick_checks', 'slice', 'task', 'task_messages']`.
   **If the grep prints nothing: `git merge main` once more; if `main` still lacks the three classes, stop and report
   `blocked-on AEA-35b`. Never define these types anywhere, and never merge the `aea-35b-specialist-types` branch
   yourself.**
3. `uv run python -c "from meridian.agent.gateway import ModelGateway, ModelOutcome; from meridian.agent.tools.dispatch import DispatchedCall, ToolDispatcher; from meridian.ports.models import ToolTranscript, ToolStepRequest; from meridian.domain.specialists import KnowledgeReport, SchedulingCapture; from tests.fakes import FakeToolModel, InMemoryTraceSink"`
   → no output. If a name differs, follow `main` and note it in your report.

**Step 1 — `agent/prompts/specialists.py`** per §4.4. Check: `uv run python -c "from meridian.agent.prompts.specialists import KNOWLEDGE_PREFIX; print(len(KNOWLEDGE_PREFIX))"`.

**Step 2 — `agent/specialists/specs.py`** per §4.5. Check: `uv run python -c "from meridian.agent.specialists.specs import SPECS; print(sorted(SPECS))"` → `['account', 'knowledge', 'scheduling']`.

**Step 3 — `agent/specialists/runner.py`** per §4.6. Check: `uv run mypy` → no errors in the three new files.

**Step 4 — test doubles** `tests/unit/agent/specialists/__init__.py` (empty) and `_doubles.py` per §6.2.

**Step 5 — `test_runner.py` and `test_specs.py`** per §7.1. Iterate with
`uv run pytest tests/unit/agent/specialists -q` until green. If a test expectation in this plan fails, fix the code
toward the plan; do not change an expected value. If the plan itself looks wrong, stop and send it back.

**Step 6 — prompt tests** (`tests/unit/agent/prompts/__init__.py` already exists; do not touch it) `test_specialist_prompts.py`,
`test_specialist_prompt_turns.py` per §7.1. `uv run pytest tests/unit/agent/prompts -q`.

**Step 7 — journey** `tests/journeys/j2/test_aea_35.py` per §7.1; `uv run pytest -m journey tests/journeys/j2/test_aea_35.py -q` → 2 passed.

**Step 8 — gates** (§7.2), cheapest first; stop at the first red.

**Step 9 — context (AC-16)**, after the feature commit exists (you need its SHA):
1. `.claude/reference/area-map.md`, A7b row (line starting `| 3 | **A7b Act** |`): in the *Owns* cell replace
   `` `agent/specialists/{specs,runner}.py` `` with `` `agent/specialists/{specs,runner}.py` (**actual**, AEA-35 `<feat sha>`) ``
   and `` `agent/prompts/specialists.py` `` with `` `agent/prompts/specialists.py` (**actual**, AEA-35 `<feat sha>`) ``.
   If another ticket already edited the *Status* cell, leave it; change nothing else on the row.
2. `docs/design/code-design.md` §3 tree: on the three lines starting `│   ├── specialists/specs.py`,
   `│   ├── specialists/runner.py`, `│   ├── prompts/specialists.py`, append `   built AEA-35 <feat sha> (ticket wave 2)` (the form AEA-22 used on `tools/dispatch.py`) at the end of
   the line. Nothing else.
3. `.claude/state/icm-progress.md`: **add one new row** directly after the last row titled *Routes verified against
   code and tests* (whichever such row is last in the table when you get there), the form every wave-2 ticket used (AC-16's "evidence link" is this row's evidence cell):
   `| Routes verified against code and tests | provisional | <run-date>: area map A7b → \`agent/specialists/{specs,runner}.py\`, \`agent/prompts/specialists.py\` (AEA-35, \`<feat sha>\`) checked against \`tests/unit/agent/specialists/\`, \`tests/unit/agent/prompts/test_specialist_prompt*.py\` (<N> passed); record docs/testing/journeys/<run-date>-AEA-35.md | Each slice adds its route; verified when every area-map row is actual |`
   (evidence cell ≤ 400 characters). Change no other row and not the *Last reconciled* line.
4. Write the journey record §7.4.
5. `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL.

**Step 10 — commits** (explicit `git add <paths>`, never `-A`; the last line of every message is
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`):
1. `feat(agent): specialist specs, braked runner and wording (AEA-35)` —
   `git add src/meridian/agent/prompts/specialists.py src/meridian/agent/specialists/specs.py src/meridian/agent/specialists/runner.py tests/unit/agent/specialists/__init__.py tests/unit/agent/specialists/_doubles.py tests/unit/agent/specialists/test_runner.py tests/unit/agent/specialists/test_specs.py tests/unit/agent/prompts/test_specialist_prompts.py tests/unit/agent/prompts/test_specialist_prompt_turns.py tests/journeys/j2/test_aea_35.py`
2. `docs(AEA-35): journey record and context for the specialist runner` —
   `git add docs/testing/journeys/<run-date>-AEA-35.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`

Do not push (the merge step pushes `main`). Do not force-push.

---

## 6. Data and fixtures (synthetic or issued values only)

### 6.1 Values (source named; no secret, code, card-like number or full phone number appears as a literal)

| Name | Value | Source |
|---|---|---|
| Thread / turn / request ids | `ThreadId("11111111-1111-4111-8111-111111111111")`; `TURN_1 = TurnId("22222222-2222-4222-8222-222222222201")`, `TURN_2 = …-222222222202`, `TURN_5 = …-222222222205`; `RequestId("33333333-3333-4333-8333-333333333333")` | synthetic |
| Demo clock | `WORKED_PAIRS_NOW` (Fri 2026-10-16 10:00 America/Chicago) from `tests.fakes` | worked-pairs header |
| WP-1 passages | `membership/comfort_club_overview.md#0` text "Includes two seasonal tune-ups per year, priority scheduling, the $89 diagnostic fee waived, 15% off all repairs, no after-hours dispatch fee, and reminders."; `#1` "Price: $189 per year per system, or $16.99 per month."; `#2` "Monthly plans require a 12-month minimum commitment." (`version_label="Effective 2026-01-01"`, `version_date=date(2026, 1, 1)`, `section="Comfort Club (Standard)"`, scores 0.82, 0.78, 0.71) | `docs/data/samples/kb-2026-10-20-membership-current.md` (paraphrased lines) |
| WP-1 stale id | `PassageId("archive/comfort_club_overview.md#0")` — never returned by any double | worked-pairs WP-1 *Must not* |
| Troubleshooting passage | `faq/troubleshooting_before_you_call.md#0`, text "Check that the thermostat is set to Cool and the breaker is on before booking a visit." (synthetic paraphrase), score 0.74 | KB file name from graph-tools §6 |
| Other FAQ passage | `faq/customer_faq.md#3`, text "Our diagnostic fee is credited toward the repair when you approve it at the same visit.", score 0.70 | synthetic paraphrase |
| WP-2 invoice | `InvoiceView(invoice_id=InvoiceId("INV-204411"), lines=(InvoiceLineView(description="Diagnostic visit", amount_cents=8900), InvoiceLineView(description="Contactor replacement", amount_cents=24500), InvoiceLineView(description="After-hours dispatch", amount_cents=14400)), total_cents=47800, balance_cents=47800, issued_on=date(2026, 10, 2), due_on=date(2026, 11, 1), paid=False)` | worked-pairs WP-2 |
| WP-2 staff note | `StaffNote(kind="billed_differs_from_schedule", record_id=InvoiceId("INV-204411"), text="INV-204411 bills After-hours dispatch at $144.00; the 2026 fee schedule lists $149.00 for non-members.", source_file="pricing/2026_fee_schedule.pdf")` | graph-tools §4 rule 1 wording |
| Verified customer | `CustomerId("MHC-10002")` (WP-2), `CustomerId("MHC-57204")` (WP-4) | worked pairs |
| Warranty | `WarrantyView(install_date=date(2019, 5, 14), equipment_brand="Carrier", sentence="Parts are covered for 10 years from the install date when the system was registered.")` | synthetic (label it so in the test docstring) |
| WP-4 appointment | `AppointmentView(appointment_id=1, date=date(2026, 10, 16), window="12:00-16:00", service_type="hvac_tune_up", technician="Marta Kowalski", is_warranty_visit=False)` | worked-pairs WP-4 |
| Shown slots | `ShownSlot(slot_id=44, date=date(2026, 10, 19), window="08:00-12:00", technician="Marta Kowalski", service_type="hvac_tune_up", zone="central", member_reserved=False, shown_turn=TURN_1)` and the same with `slot_id=61, window="12:00-16:00"` | worked-pairs WP-4 step 4 |
| WP-4 draft | `ChangeRequestDraft(appointment_id=1, change="move", wanted_text="Monday morning", windows_shown=(44, 61), hours_before=2.0, window_start=datetime(2026, 10, 16, 12, 0, tzinfo=CHICAGO))` | AEA-28 plan WP-4 test values |
| WP-4F write | `WriteResult(action=CompletedAction(key=ActionKey(thread_id=THREAD, turn_id=TURN_1, kind=ActionKind.MOVED, record_id="2"), kind=ActionKind.MOVED, records={"appointment": "2", "slot": "44", "old_slot": "12"}, before={"date": "2026-10-21", "window": "12:00-16:00"}, after={"date": "2026-10-19", "window": "08:00-12:00", "technician": "Marta Kowalski", "service_type": "hvac_tune_up", "fee_line": ""}, at=WORKED_PAIRS_NOW), confirmation=ConfirmationView(date=date(2026, 10, 19), window="08:00-12:00", technician="Marta Kowalski", fee_note=FeeNote(service_type="hvac_tune_up", tier="none", fee_row="Seasonal tune-up", amount_cents=12900, waived=False, line="The seasonal tune-up is $129.")))` | synthetic (WP-4F variant) |
| Generated secrets (AC-11 only) | six-digit code `f"{secrets.randbelow(10**6):06d}"`; 16-digit card `"4" + "".join(str(secrets.randbelow(10)) for _ in range(15))`; phone `"512-555-" + f"{secrets.randbelow(10**4):04d}"` — built at run time, never written as literals | AC-11 "generated in the test" |
| Sentinels | `"SENTINEL-ARG-7731"` (an argument value, AC-14); `"made_up_tool"` (an unknown model-supplied name, AC-14) | synthetic |

### 6.2 `tests/unit/agent/specialists/_doubles.py` (test-only builders; module docstring "Builders and doubles for the AEA-35 specialist tests. Synthetic values only.")

Imports from `meridian.*` as in §4 (`KnowledgeSlice`, `AccountSlice`, `SpecialistTask` from `meridian.domain.tools`) and `from tests.fakes import CHICAGO, WORKED_PAIRS_NOW, FakeToolModel, InMemoryTraceSink, provider_call`.

Constants: `THREAD`, `TURN_1`, `TURN_2`, `TURN_5`, `REQUEST` (§6.1); the passages and views of §6.1 as module
constants (`WP1_INCLUDES`, `WP1_PRICE`, `WP1_MINIMUM`, `ARCHIVE_ID`, `TROUBLESHOOTING`, `FAQ_CREDIT`, `INV_204411`,
`STAFF_NOTE`, `WARRANTY`, `APPT_WP4`, `SLOT_44`, `SLOT_61`, `DRAFT_WP4`, `WRITE_WP4F`).

Builders (each a small function with full type hints):

```python
def turn_ids(turn_id: TurnId = TURN_1) -> TurnIds:
    # TurnIds(thread_id=THREAD, turn_id=turn_id, request_id=REQUEST, run_tag="eval", run_id=None, agent_version="test")

@contextmanager
def turn_ctx(sink: InMemoryTraceSink, *, turn_id: TurnId = TURN_1,
             now: datetime = WORKED_PAIRS_NOW) -> Iterator[TurnContext]:
    # ids = turn_ids(turn_id); with sink.turn(ids) as span: started = time.monotonic();
    # yield TurnContext(ids=ids, budget=TurnBudget(started=started, deadline=started + 60.0), now=now,
    #                   demo_session="demo-test", span=span)

def scope(ctx: TurnContext, *, customer_id: CustomerId | None = None,
          shown: frozenset[int] = frozenset(), message_id: int = 412) -> ToolCallScope

def knowledge_slice() -> KnowledgeSlice      # return KnowledgeSlice()  (AEA-35b: kind-only)
def account_slice() -> AccountSlice          # return AccountSlice()    (AEA-35b: kind-only)
def scheduling_slice(*, appointments: tuple[AppointmentView, ...] = (),
                     shown: tuple[ShownSlot, ...] = ()) -> SchedulingSlice:
    # SchedulingSlice(customer_zone="central", member=False, appointments=appointments, shown_slots=shown,
    #                 pending_change=False, bookings_left=3)

def make_task(specialist: SpecialistKind, intent: TaskIntent, text: str, *, messages: tuple[str, ...] = (),
              offer_quick_checks: bool = False, slice_: KnowledgeSlice | AccountSlice | SchedulingSlice | None = None
              ) -> SpecialistTask:
    # PlannedTask(order=1, specialist=specialist, intent=intent, needs_identity=(specialist != "knowledge"));
    # slice_ defaults to the slice builder of that specialist (a dict lookup in this test module is fine)

def passage(file: str, n: int, text: str, *, score: float = 0.8) -> Passage
def tool_call(call_id: str, name: str, **args: JsonValue) -> ToolCall        # ToolCall(id=..., name=..., args=dict(args))
def report_call(call_id: str, **args: JsonValue) -> ToolCall                 # name="report_facts"
def step(*calls: ToolCall, text: str = "") -> ToolStep
    # ToolStep(text=text, tool_calls=calls, raw={"stub": True}, stop_reason="tool_use" if calls else "end_turn")

def lookup(ctx: TurnContext, tool: str, *, record_ids: tuple[str, ...] = (),
           passage_ids: tuple[PassageId, ...] = (), seen: str = "ok") -> LookupEntry
def dispatched(call: ToolCall, ctx: TurnContext, *, kind: ToolKind | None, for_model: JsonValue | ToolError,
               captured: KnowledgeCapture | AccountCapture | SchedulingCapture | None = None,
               record_ids: tuple[str, ...] = (), passage_ids: tuple[PassageId, ...] = (),
               elapsed_ms: int = 3, name: str | None = None) -> DispatchedCall:
    # outcome/error: ToolError with code TOOL_FAILED → ("failed", code); other ToolError → ("refused", code);
    #   else ("ok", None). content = json.dumps({"error": err.model_dump(mode="json")}) for a ToolError, else
    #   json.dumps(for_model) (separators=(",", ":"), ensure_ascii=False). record.name = name or call.name;
    #   lookup_id=1. ToolResult(ok=<outcome == "ok">, for_model=for_model, captured=captured,
    #   lookup=lookup(ctx, record.name, ...), lookup_written=False).
def kb_dispatched(call, ctx, passages: Sequence[Passage], *, below_floor: bool = False) -> DispatchedCall
    # kind KB_SEARCH; for_model={"below_floor": below_floor, "passages": [{"passage_id": p.passage_id, "file": p.file,
    #   "text": p.text} for p in passages]}; captured=KnowledgeCapture(result=RetrievalResult(passages=tuple(passages),
    #   below_floor=below_floor)); passage_ids = ids
def refused_dispatched(call, ctx, code: ToolErrorCode, *, kind: ToolKind | None,
                       captured: SchedulingCapture | None = None, name: str | None = None) -> DispatchedCall
    # for_model=ToolError(code=code, message="refused", retryable=False)
def failed_dispatched(call, ctx, *, kind: ToolKind) -> DispatchedCall   # ToolError(code=TOOL_FAILED, ...)
```

Doubles (subclass the real classes so the runner's signature keeps the contract types; do **not** call
`super().__init__`; PD-14):

```python
class ScriptedGateway(ModelGateway):
    """Gateway double: forwards each tool step to a FakeToolModel, or returns scripted outcomes first."""
    def __init__(self, model: FakeToolModel | None = None, *,
                 outcomes: Sequence[ModelOutcome[ToolStep]] = (), retried_steps: frozenset[int] = frozenset()) -> None:
        # self.model, self._outcomes = list(outcomes), self._retried = retried_steps, self.requests = [], self.roles = []
    def tool_step(self, role: ToolRole, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[ToolStep]:
        # 1. n = len(self.requests); append req and role.
        # 2. if self._outcomes: return self._outcomes.pop(0).
        # 3. attempt = self.model.tool_step(req, timeout_s=8.0)  (assert self.model is not None)
        # 4. calls = []; if n in self._retried: calls.append(CallRecord.from_provider(provider_call(provider="anthropic",
        #    model="claude-sonnet-5-5", failure=ProviderFailure(kind=ProviderFailureKind.OVERLOADED, provider="anthropic",
        #    http_status=529, retry_after_s=None, retryable=True, provider_request_id=None)), role=Role.SPECIALIST, attempt=1))
        # 5. calls.append(CallRecord.from_provider(attempt.record, role=Role.SPECIALIST, attempt=len(calls) + 1))
        # 6. return ModelOutcome[ToolStep](value=attempt.value, calls=tuple(calls), failure=attempt.failure, halt=None)

class ScriptedDispatcher(ToolDispatcher):
    """Dispatcher double: records every batch; answers each call with handler(call)."""
    def __init__(self, handler: Callable[[ToolCall], DispatchedCall], *,
                 schemas: tuple[ToolSchema, ...] = ()) -> None:
        # self._handler, self._schemas, self.batches: list[tuple[tuple[ToolCall, ...], frozenset[ToolKind], ToolCallScope]] = [],
        # self.schema_requests: list[frozenset[ToolKind]] = []
    def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]   # records kinds; returns self._schemas
    def dispatch(self, calls: Sequence[ToolCall], *, kinds: frozenset[ToolKind],
                 scope: ToolCallScope) -> tuple[DispatchedCall, ...]          # records; tuple(handler(c) for c in calls)
    @property
    def dispatched_calls(self) -> tuple[ToolCall, ...]                       # every call of every batch, in order

def make_runner(gateway: ModelGateway, transcript: ToolTranscript, dispatcher: ToolDispatcher,
                trace: InMemoryTraceSink, *, brakes: Brakes = Brakes()) -> SpecialistRunner:
    # SpecialistRunner(gateway=gateway, transcript=transcript, dispatcher=dispatcher, specs=SPECS, brakes=brakes, trace=trace)
```

The usual wiring in a test (mirrors AEA-51: the **same** fake is the transcript and the gateway's model):

```python
sink = InMemoryTraceSink(); model = FakeToolModel([...steps...])
gateway = ScriptedGateway(model); dispatcher = ScriptedDispatcher(handler)
runner = make_runner(gateway, model, dispatcher, sink)
with turn_ctx(sink) as ctx:
    result = runner.run(task, scope(ctx, customer_id=...), ctx)
```

A `handler` is a local function in each test that maps `call.name` (and args) to a `dispatched(...)` builder; build
the `DispatchedCall` with the `ctx` of the run (the handler is created inside the `with` block).

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (names are binding)

**`tests/unit/agent/specialists/test_runner.py`**

| Test | Setup | Assertions |
|---|---|---|
| `test_two_tool_rounds_brake` (AC-1) | knowledge task; model script: `step(tool_call("c1","kb_search",query="a"))`, `step(tool_call("c2","kb_search",query="b"))`, `step(tool_call("c3","kb_search",query="c"))`; handler → `kb_dispatched(call, ctx, [WP1_INCLUDES])` | `len(dispatcher.batches) == 2`; `"c3" not in [c.id for c in dispatcher.dispatched_calls]`; `result.brake == HaltReason.BRAKE_TOOL_ROUNDS` and `result.brake == "brake_tool_rounds"`; `len(model.requests) == 3` |
| `test_identical_call_breaker` (AC-2) | two cases (parametrise `ids=["across_rounds","within_step"]`): (a) `step(tool_call("c1","kb_search",query="same"))`, `step(tool_call("c2","kb_search",query="same"))`; (b) one step with `tool_call("c1","x_tool",a=1,b=2)` and `ToolCall(id="c2", name="x_tool", args={"b": 2, "a": 1})` | the duplicate never reaches dispatch: `[c.id for c in dispatcher.dispatched_calls] == ["c1"]`; `result.brake == HaltReason.BRAKE_IDENTICAL_CALL`; in (a) `len(model.requests) == 2` |
| `test_final_answer_branch` (AC-2) | knowledge task; script: `step(text="Nothing to look up.")` | `dispatcher.batches == []`; `len(model.requests) == 1`; `result.status == "no_current_source"`; `result.brake is None and result.failure is None` |
| `test_report_facts_ends_loop_not_dispatched` (AC-2) | knowledge task; script: `step(tool_call("c1","kb_search",query="comfort club"))`, `step(report_call("r1", points=[{"text":"Two tune-ups a year.","passage_id":"membership/comfort_club_overview.md#0"}], answered=True))` | no dispatched call named `report_facts`; `len(dispatcher.batches) == 1`; `len(model.requests) == 2`; `result.status == "answered"`; also: the tool names sent in `model.requests[0].tools` end with `"report_facts"` and the rest equal the dispatcher's `schemas` |
| `test_invalid_report_is_ignored` (AC-20) | knowledge task; kb round then `step(report_call("r1", points=[{"text":"x","passage_id":"membership/comfort_club_overview.md#0"}]*6, answered=True))` (6 > max 5) | no exception; `result.status == "no_current_source"`; `result.points == ()`; `len(model.requests) == 2` |
| `test_results_keep_tool_call_ids` (AC-3) | knowledge task; script: step with `c1` and `c2` (two `kb_search` with different queries), step with `c3`, then `step(report_call("r1", points=[], answered=False))` | `[r for r, _ in model.appends[0][2]] == ["c1","c2"]`, `[r for r, _ in model.appends[1][2]] == ["c3"]`; each appended content equals that call's `DispatchedCall.content` (keep the handler's returns in a dict by id); `len(model.appends) == 2` |
| `test_message_list_is_per_run` (AC-3) | the same runner and model run two knowledge tasks in turn (`TURN_1` text "What does the Comfort Club membership actually include?", `TURN_2` text "And how much is it?"); each script: one `step(report_call(...answered=False))` | `len(model.starts) == 2`; `"And how much is it?" in model.starts[1]` and `"actually include" not in model.starts[1]`; `model.requests[1].messages.items == ({"role": "user", "content": model.starts[1]},)` (a fresh list, nothing carried over) |
| `test_never_raises_on_failure` (AC-4) | `ScriptedGateway(outcomes=[ModelOutcome[ToolStep](value=None, calls=(rec1, rec2), failure=ProviderFailure(kind=SERVER, provider="anthropic", http_status=503, retry_after_s=None, retryable=True, provider_request_id=None), halt=None)])` where `rec1`, `rec2` = failed `CallRecord`s (attempt 1, 2) | no exception; `result.status == "failed"`; `result.failure.kind == ProviderFailureKind.SERVER`; `len(result.calls) == 2`; `len(gateway.requests) == 1`; `dispatcher.batches == []` |
| `test_gateway_halt_stops_run` (AC-4, `@pytest.mark.parametrize("reason", [DEADLINE, BRAKE_SONNET_CALLS, PROVIDER_SPEND_CAP], ids=lambda r: r.value)`) | outcomes `[ModelOutcome[ToolStep](value=None, calls=(), failure=None, halt=Halt(reason=reason, node="specialist", elapsed_ms=0))]` | `result.brake == reason`; `len(gateway.requests) == 1`; `dispatcher.batches == []`; no exception |
| `test_tool_failed_content_reaches_model` (AC-4) | knowledge task; `c1` → `failed_dispatched`; then `step(report_call("r1", points=[], answered=False))` | `'"tool_failed"' in model.appends[0][2][0][1]`; `len(model.requests) == 2`; `result.tools[0].outcome == "failed"`; `result.brake is None` |
| `test_quick_checks_offer` (AC-8) | scheduling task `BOOK_NEW`, `offer_quick_checks=True`, text = `"My AC stopped cooling, can someone come out? " * 10` (> 300 chars); handler: `kb_search` → `kb_dispatched(call, ctx, [TROUBLESHOOTING, FAQ_CREDIT])`; `find_windows` → `dispatched(..., kind=SLOT_SEARCH, for_model={"windows":[44, 61]}, captured=SchedulingCapture(windows=(SLOT_44, SLOT_61)))`; script: `step(tool_call("c1","find_windows",service_type="hvac_repair"))`, `step(tool_call("c2","find_windows",service_type="hvac_repair",day="monday"))`, `step(report_call("r1", appointment_id=0, wanted_time="", note="windows shown"))`. Second case: `offer_quick_checks=False`. Third case: troubleshooting search `below_floor=True` | case 1: `dispatcher.batches[0] == ((ToolCall(id=f"qc-{TURN_1}", name="kb_search", args={"query": text[:300]}),), frozenset({ToolKind.KB_SEARCH}), <scope>)`; `len(dispatcher.batches) == 3` (quick check + 2 model rounds); `result.brake is None`; `result.quick_checks == (TROUBLESHOOTING,)`; `result.status == "windows_shown"`; no `qc-` id in `model.appends`. Case 2: no dispatched id starts with `"qc-"`; `result.quick_checks == ()`. Case 3: `result.quick_checks == ()` |
| `test_scope_for` (AC-9, parametrise over `("not_checked", None)`, `("located", "MHC-10002")`, `("code_sent", "MHC-10002")`, `("verified", "MHC-10002")`, `("not_verified", "MHC-10002")`, `("locked", "MHC-10002")`) | `ConversationState(thread_id=THREAD, turn_input=TurnInput(turn_id=TURN_1, message_id=412, kind="text", text_store="Can I move it?", received_at=WORKED_PAIRS_NOW), identity=IdentityState(status=s, customer_id=<id or None>, masked_hint=None, code_expires_at=None, tries_left=3, codes_sent=1, verified_at=None), shown_slots=[SLOT_44, SLOT_61])` | `scope.customer_id == CustomerId("MHC-10002")` only for `verified`, else `None`; `scope.shown_slot_ids == frozenset({44, 61})`; `scope.now is ctx.now`; `scope.ids == ctx.ids`; `scope.message_id == 412` |
| `test_no_staff_notes_transcript_or_scope_leak` (AC-10) | `caplog.set_level(logging.DEBUG)`; account task `READ_INVOICE` text "I got an invoice and I'm not sure what it's for."; scope `customer_id=MHC-10002`; `read_invoices` → `dispatched(kind=ACCOUNT_READ, for_model={"invoices":[INV_204411.model_dump(mode="json")]}, captured=AccountCapture(invoices=(INV_204411,), staff_notes=(STAFF_NOTE,)), record_ids=("INV-204411",))`; script: read, then `step(report_call("r1", summary="One unpaid invoice."))` | for every `req` in `gateway.requests`: `STAFF_NOTE.text not in req.model_dump_json()` and `"MHC-10002" not in req.model_dump_json()`; for every log record `r`: `STAFF_NOTE.text`, `"MHC-10002"` and the task text are not in `r.getMessage()` nor in `str(r.__dict__)`; `dump = result.model_dump_json()`: `'"items"' not in dump`, `'"for_model"' not in dump`, `'"speaker"' not in dump`, `"MHC-10002" not in dump`; `result.staff_notes == (STAFF_NOTE,)`; `result.status == "read"`; `caplog.records == []` (the normal path logs nothing) |
| `test_lookup_and_call_records` (AC-13) | scheduling task with `offer_quick_checks=True`; gateway `retried_steps=frozenset({0})`; script: round 1 with two calls (`find_windows`, `x_read`), round 2 one call, then report | `len(dispatcher.dispatched_calls) == 4` (1 quick check + 3 model calls); `len(result.tools) == 4`; ids of `result.tools` == ids of dispatched calls in order; `len(result.calls) == 4` (3 steps + 1 retry attempt) and `[c.attempt for c in result.calls][:2] == [1, 2]` |
| `test_tool_spans` (AC-14) | scheduling task, `offer_quick_checks=True`; round 1: `tool_call("c1","find_windows",service_type="hvac_repair")` and `tool_call("c2","made_up_tool",x=1)` (handler → `refused_dispatched(..., ToolErrorCode.UNKNOWN_TOOL, kind=None)`); round 2: `tool_call("c3","find_windows",wanted="SENTINEL-ARG-7731")`; then report | `nodes = sink.spans_for(ctx.span).nodes`: `[n.name for n in nodes] == ["tool:kb_search", "tool:find_windows", "tool:unknown", "tool:find_windows"]`; for each `(n, r)` in `zip(nodes, result.tools)`: `n.elapsed_ms == r.elapsed_ms`, `n.status == r.outcome`; no node name contains `"made_up_tool"`, `"report_facts"` or `"SENTINEL-ARG-7731"`; no node status contains the sentinel; `len(nodes) == len(result.tools) == 4` |
| `test_wp1_knowledge_run_cites_current_file` (AC-17) | knowledge `ANSWER_QUESTION`, text "What does the Comfort Club membership actually include?"; `kb_search` → `[WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM]`; report points: one per returned passage (texts from §6.1) plus one citing `ARCHIVE_ID` with text "$149 a year, 10% off repairs" | `result.status == "answered"`; `len(result.points) == 3`; every `p.passage_id` in the returned ids and starts with `"membership/comfort_club_overview.md#"`; joined point text contains none of `"$149"`, `"$12.99"`, `"$219"`, `"10% off"` |
| `test_unexpected_error_returns_failed_result` (AC-20) | `caplog.set_level(logging.DEBUG)`; knowledge task; a dispatcher subclass whose `dispatch` raises `RuntimeError("boom with secret text")` | no exception; `result.status == "failed"`; `result.failure is None`; exactly one log record on logger `meridian.agent.specialists.runner` whose message contains `"RuntimeError"` and not `"boom"` |

**`tests/unit/agent/specialists/test_specs.py`**

| Test | Assertions |
|---|---|
| `test_specs_cover_every_kind` (AC-19) | `set(SPECS) == {"knowledge","account","scheduling"}`; tool kinds exactly as §4.5; report models `KnowledgeReport`, `AccountReport`, `SchedulingReport`; each `spec.kind` equals its key; `isinstance(SPECS, MappingProxyType)`; each `render` returns three `str` |
| `test_report_facts_schema_from_report_model` (AC-19) | for each spec: `s = report_facts_schema(spec)`; `s.name == "report_facts"`; `s.strict is True`; `s.input_schema == spec.report_model.model_json_schema()`; `s.description == REPORT_FACTS_DESCRIPTION` |
| `test_results_from_captured_not_report` (AC-5) | builder level. (a) account: `RunOutcome(captured=(AccountCapture(invoices=(INV_204411,)),), report=AccountReport(summary="Total $999.00, due tomorrow"), …)` → `result.invoices == (INV_204411,)` and `"999" not in result.model_dump_json()`. (b) scheduling: captured windows `(SLOT_44, SLOT_61)`, report `SchedulingReport(appointment_id=999, wanted_time="slot 77", note="booked slot 77")` → `result.windows == (SLOT_44, SLOT_61)`, `result.write is None`, `"77" not in` the windows' ids, `result.status == "windows_shown"` |
| `test_zero_valid_points_no_current_source` (AC-6) | captured one `KnowledgeCapture` with 3 passages (`WP1_*`); report `KnowledgeReport(points=[ReportedPoint(text="x", passage_id=ARCHIVE_ID)], answered=True)` → `status == "no_current_source"`, `points == ()`, `passages == (WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM)` |
| `test_below_floor_no_current_source` (AC-6) | captured `KnowledgeCapture(result=RetrievalResult(passages=(), below_floor=True))`; report citing `membership/comfort_club_overview.md#0` → `status == "no_current_source"`, `points == ()` |
| `test_knowledge_quick_checks_only_from_troubleshooting` (AC-8) | passages returned `(TROUBLESHOOTING, FAQ_CREDIT)` → `quick_checks == (TROUBLESHOOTING.passage_id,)`; with only `FAQ_CREDIT` → `()` |
| `test_wp1_points_cite_only_this_runs_passages` (AC-17) | builder level: 3 WP-1 passages returned; report with 3 valid points + 1 citing `ARCHIVE_ID` → `status == "answered"`, 3 points, none citing the archive |
| `test_wp4_fee_bearing_becomes_change_request` (AC-7, **WP-4**) | real runner + `SPECS`; scheduling `RESCHEDULE` task, text "I have a tech coming … but something came up. Can I move it?", slice `scheduling_slice(appointments=(APPT_WP4,), shown=(SLOT_44, SLOT_61))`; scope `customer_id=MHC-57204`, `shown=frozenset({44, 61})`; script: `step(tool_call("c1","move_visit",appointment_id=1,new_slot_id=44))` → `refused_dispatched(..., FEE_BEARING, kind=MOVE, captured=SchedulingCapture(refused=FEE_BEARING))`; `step(tool_call("c2","request_visit_change",appointment_id=1,change="move",wanted_text="Monday morning"))` → `dispatched(kind=CHANGE_REQUEST, for_model={"recorded": True}, captured=SchedulingCapture(change_request=DRAFT_WP4))`; `step(report_call("r1", appointment_id=1, wanted_time="Monday morning", note="change request recorded"))` | `result.status == "staff_change_request"`; `result.change_request == DRAFT_WP4`; `result.write is None`; `[t.outcome for t in result.tools] == ["refused","ok"]`; `result.tools[0].error == ToolErrorCode.FEE_BEARING` |
| `test_wp4f_fee_free_move_written` (AC-7, WP-4F) | same wiring; `move_visit` → `dispatched(kind=MOVE, for_model={"moved": True}, captured=SchedulingCapture(write=WRITE_WP4F))`; then report | `result.status == "written"`; `result.write == WRITE_WP4F`; `result.change_request is None` |
| `test_runner_never_branches_on_kind` (AC-18) | read `src/meridian/agent/specialists/runner.py`; `ast` walk: no `ast.Constant` whose value is `"knowledge"`, `"account"` or `"scheduling"`; no `ast.Compare` whose left side or comparator is an `ast.Attribute` named `kind` on `ast.Name` `spec` |
| `test_modules_import_only_allowed_layers` (AC-18) | `ast` imports of the three files (top-level `meridian.*` modules): `prompts/specialists.py` ⊆ `{meridian.domain.*, meridian.privacy.redact}`; `specs.py` ⊆ `{meridian.domain.*, meridian.ports.models, meridian.agent.prompts.specialists}`; `runner.py` ⊆ `{meridian.domain.*, meridian.ports.*, meridian.policy.limits, meridian.agent.gateway, meridian.agent.tools.dispatch, meridian.agent.specialists.specs}`; none imports `meridian.services`, `meridian.web`, `meridian.adapters`, `anthropic`, `httpx`, `langgraph`, `sqlite3`; no relative imports |

**`tests/unit/agent/prompts/test_specialist_prompts.py`**

| Test | Assertions |
|---|---|
| `test_requests_carry_no_secret_values` (AC-11; parametrise over the three kinds, `ids=["knowledge","account","scheduling"]`) | generate `code`, `card`, `phone` (§6.1). Task text `redact(f"my code is {code}, card {card}, call {phone}", RedactionProfile.SONNET).text`; `task_messages=("[code entered]", "[card number removed]", "[phone ending 02]")`; scheduling slice with `(SLOT_44,)`. `now = datetime(2031, 3, 4, 9, 30, tzinfo=CHICAGO)`. Render through `SPECS[kind].render(task, ctx)`; `whole = "\n".join((prefix, dynamic, user))`: `code not in whole`, `card not in whole`, `phone not in whole`, `re.search(r"(?<!\d)\d{6}(?!\d)", whole) is None`, `re.search(r"\d(?:[ -]?\d){12,18}", whole) is None`, `re.search(r"\d{3}[ .-]?\d{3}[ .-]?\d{4}", whole) is None`; `"Tuesday, March 4, 2031" in dynamic`; today's server date (`f"{datetime.now(CHICAGO):%B} {datetime.now(CHICAGO).day}, {datetime.now(CHICAGO).year}"`) not in `dynamic`. Second half: render a task whose `customer_text` is the **raw** string (not redacted) and assert the same absences (render's own SONNET pass) |
| `test_prefix_rules_present` | each of `KNOWLEDGE_PREFIX`, `ACCOUNT_PREFIX`, `SCHEDULING_PREFIX` contains `RULE_NEVER_TALK`, `RULE_REPORT_ONLY`, `RULE_NO_FIRM_PRICES`, `RULE_NO_CARDS`, `"report_facts"`; knowledge contains `"12-month minimum"` and `"kb_search"`; account contains `"read_invoices"`, `"as billed"` and `"Never judge whether a charge is right"`; scheduling contains `"never move or cancel that visit"` and none of `"move_visit"`, `"book_visit"`, `"find_windows"`; no prefix contains a `$` amount (`re.search(r"\$\d", prefix) is None`) |
| `test_task_labels_cover_every_intent` | `set(TASK_LABELS) == set(TaskIntent)`; every label non-empty |
| `test_scheduling_state_omits_turn_ids` (AC-22) | scheduling `BOOK_NEW` task with `slice_=scheduling_slice(shown=(SLOT_44, SLOT_61))`; `_, _, user = SPECS["scheduling"].render(task, ctx)` → `"shown_turn" not in user`; `str(TURN_1) not in user`; `"[card number removed]" not in user`; `'"slot_id": 44' in user` and `'"slot_id": 61' in user` (json `indent=1` writes `": "`) |
| `test_user_text_budget` (AC-21) | knowledge task with `task_messages` = 10 messages `m0`…`m9` of 1,500 chars each (`f"m{i} " + "x" * 1495`) and `customer_text="latest question"` → the message lines are exactly `m5`…`m9` (cut to 1,000 chars, ending in `…`) followed by `latest question` (6 lines; rule: keep the last 6, append the latest, keep the last 6); no line is longer than `len("- ") + 1000` |

**`tests/unit/agent/prompts/test_specialist_prompt_turns.py`**

| Test | Assertions |
|---|---|
| `test_stable_prefix_turns_1_2_5` (AC-12; context-management rule 3) | one `FakeToolModel` and one runner (real `SPECS`, `ScriptedGateway(model)`, `ScriptedDispatcher` answering `kb_search` with `[WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM]`); three runs with `TURN_1` "What does the Comfort Club membership actually include?", `TURN_2` "And how much is it?" (messages `("What does the Comfort Club membership actually include?",)`), `TURN_5` "Does it cover plumbing?"; each script: kb round then report. Take the **first** recorded request of each run (`model.requests[0]`, `[2]`, `[4]`): `hashlib.sha256(prefix.encode()).hexdigest()` equal on all three; prefix contains the role line `"You are the knowledge specialist"`, `RULE_NEVER_TALK`, `RULE_REPORT_ONLY`, `RULE_NO_FIRM_PRICES`, `RULE_NO_CARDS`; `tools` names identical across the three; the three `messages.items[0]["content"]` differ and each contains its own turn text |

**`tests/journeys/j2/test_aea_35.py`** (`pytestmark = pytest.mark.journey`). Import the builders and doubles with
`from tests.unit.agent.specialists._doubles import (...)` (absolute; `tests` is a package and `pythonpath = ["."]`). Module docstring: "J-2 (slice plan §0a),
AEA-35 steps: billing and warranty answers stay inside the specialist brakes and show the source they used. Level
today: mock-tested (real SpecialistRunner and SPECS; gateway, dispatcher and executors are doubles; no server, no DB).
The integrated steps (the answer's source on the real turn; the lookup_log rows in the harness's DB copy) are blocked by
AEA-51 (integrated customer path; it wires the graph that AEA-57's merged harness drives and lands J-2). Synthetic
values only."
This file does not use the harness `journey` fixture: the harness steps need `run_graph` and `turn_service`, which are
unbound until AEA-51 and AEA-40 merge, and the README's "no doubles above the model ports" rule governs those
integrated steps. It follows the merged `mock-tested` precedents (`j2/test_aea_38.py`, `j10/test_aea_48.py`, `j9/test_aea_26.py`). Do not
import anything from `tests/journeys/support/`.

| Test | Assertions |
|---|---|
| `test_j2_billing_answer_shows_invoice_source` | account `READ_INVOICE` run as in AC-10 (WP-2): `result.status == "read"`; `result.invoices[0].invoice_id == "INV-204411"`; `[l.amount_cents for l in result.invoices[0].lines] == [8900, 24500, 14400]` (as billed); `result.tools[0].record_ids == ("INV-204411",)`; `len(dispatcher.batches) <= Brakes().tool_rounds`; `result.brake is None`; one dispatched call per lookup row (`len(dispatcher.dispatched_calls) == len(result.tools) == 1`) |
| `test_j2_warranty_answer_shows_warranty_source` | account `READ_WARRANTY`; `read_warranty` → `dispatched(kind=ACCOUNT_READ, for_model={"warranty": WARRANTY.model_dump(mode="json")}, captured=AccountCapture(warranty=WARRANTY), record_ids=("customer:MHC-10002",))`; then report: `result.status == "read"`; `result.warranty == WARRANTY`; `result.tools[0].record_ids == ("customer:MHC-10002",)`; `result.brake is None` |

### 7.2 Gates (cheapest first; stop at the first red). Run from the worktree root with `UV_LINK_MODE=hardlink`.

Affected tests = this ticket's test folders plus any test importing a changed module:
`grep -rlE "agent\.specialists|prompts\.specialists|agent/specialists|prompts/specialists" tests/ eval/` (expect only
this ticket's files; if another file appears, add it to the pytest command).

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/agent/specialists src/meridian/agent/prompts/specialists.py tests/unit/agent/specialists tests/unit/agent/prompts tests/journeys/j2/test_aea_35.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check src/meridian/agent/specialists src/meridian/agent/prompts/specialists.py tests/unit/agent/specialists tests/unit/agent/prompts tests/journeys/j2/test_aea_35.py` | `N files already formatted` (run `uv run ruff format <same paths>` first if needed) |
| 3 | Types | `uv run mypy` | `Success: no issues found in N source files` |
| 4 | Affected tests | `uv run pytest tests/unit/agent/specialists tests/unit/agent/prompts tests/unit/test_import_direction.py -q` | all pass, 0 failed, 0 skipped (the folder also holds AEA-38's reply-prompt tests; they must stay green) |
| 5 | Journey file | `uv run pytest -m journey tests/journeys/j2/test_aea_35.py -q` | `2 passed` |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | selects every journey file present (any change under `tests/journeys/` selects all, `affected.py` ALWAYS_PREFIXES); passes and skips only (each skip prints `blocked-on AEA-NN` or a stale reason already on `main`); AEA-57's harness journey starts a loopback server on an OS-assigned port (never 4019 or 5184) |

The full suite is **not** run: no shared fixture, settings, dependency or cross-codebase module changes
(`build-loop-test-scope.md`). Never use more than `-n 2` if you add xdist (not needed here).

### 7.3 Existing tests that must stay green

`tests/unit/test_import_direction.py`, `tests/unit/test_skeleton.py` (package skeleton), and AEA-20's
`tests/unit/agent/test_gateway.py`, AEA-22's `tests/unit/agent/tools/` (this ticket imports their modules but changes
nothing in them; run them once at gate 4 if they exist:
`uv run pytest tests/unit/agent -q`).

### 7.4 Journey record (AC-15): `docs/testing/journeys/<run-date>-AEA-35.md`

```markdown
# Journey record: AEA-35 specialists (J-2 steps)

| Field | Value |
|---|---|
| Claim | J-2 (AEA-35 steps): billing and warranty specialist runs stay inside the two-round brake and return the invoice / warranty they read, with the record ids in the tool record; staff notes stay out of every model request |
| Level | `mock-tested` |
| Tested revision | `<feat sha>` |
| Environment | VPS, Python 3.12; no server, no DB; real `SpecialistRunner` + `SPECS`; `ScriptedGateway` over AEA-11 `FakeToolModel`; `ScriptedDispatcher`; `InMemoryTraceSink` |
| Command | `uv run pytest -m journey tests/journeys/j2/test_aea_35.py -q`; `uv run pytest tests/unit/agent/specialists tests/unit/agent/prompts -q` |
| Result | <N> passed (journey: 2 passed); affected journeys <P> passed, <S> skipped |
| Evidence location | this file; GitLab issue #35 comment |
| Remaining limitations | Executors (AEA-27, 28, 33) are merged but doubled here; no lookup_log rows in a DB, no browser; prompts were never sent to a live model |
| Blocked by | AEA-51 (integrated customer path; wires the graph AEA-57's merged harness drives; lands J-2) |
| Journeys that will exercise this code | J-2 at API level (AEA-51), J-2 in the browser (AEA-62), J-3 scheduling (AEA-51) |
```

### 7.5 Capture and evaluation checks

| Check | Command | Evidence |
|---|---|---|
| Capture verification (WF-1, component level) | `uv run pytest tests/unit/agent/specialists/test_runner.py -k "lookup_and_call_records or tool_spans or leak" -q` | 3 passed; CAP-1 at the real entry point is AEA-51 |
| Evaluation check | n/a here: E-1 trajectory and E-7 run when AEA-51 compiles the graph; scored runs are Stage 9 | — |

---

## 8. Risks and requests

### 8.1 Decisions made in this plan (engineering; each reversible by a follow-up)

| ID | Decision | Basis |
|---|---|---|
| PD-1 | Status rules: a provider `failure` makes every kind `"failed"` (captured data still folded in); a `brake` does not change the status (the act node reads `brake`); an exception or an empty gateway value makes `"failed"` with `failure=None` | AC-4; graph-nodes §4 (AEA-39 emits `specialist_failed` for `failed` with no brake, cause `tool_error` when `failure` is None); cases.md §3.4 rule 6 |
| PD-2 | Per step: the report is taken first; non-report calls go through the round check, then the identical-call split; new calls are dispatched and appended; duplicates then brake; a report then ends the run | DO-4 §5 runner rules; AC-1…AC-3; agent-tools 6 |
| PD-3 | The quick-check call is recorded and spanned but not captured, not citable, not in `seen`, and not appended (the model never asked for it) | GRT-8 ("not a model tool round"); GRT-7 (cite only what this run's model saw) |
| PD-4 | Scheduling: `windows` = last non-empty search; refusal statuses from `ToolCallRecord.error` via a four-entry map; `no_fit` = a capture with nothing in it; precedence write > change request > refusal > windows > no_fit > failed | DO-4 §5 statuses; graph-tools §3, C-7; WP-4 |
| PD-5 | Account: invoices de-duplicated by id; last membership and warranty; notes de-duplicated; `not_verified` from the dispatch guard's record | graph-tools §4; R-14 |
| PD-6 | Knowledge: invalid points dropped; `answered` needs `report.answered` and ≥ 1 valid point; citable = passages from captures not below the floor | GRT-7; R-13 |
| PD-7 | `specs` and `SPECS` typed `Mapping[SpecialistKind, SpecialistSpec]` (contract says `Mapping[str, …]` for the parameter; mypy's invariant `Mapping` keys reject passing the literal-keyed `SPECS`) | graph-tools §2; mypy strict |
| PD-8 | Constructor arguments kept as public attributes (`gateway`, `transcript`, `dispatcher`, `specs`, `brakes`, `trace`) | AEA-51 AC-1 asserts `runner.transcript is …`, `runner.trace is …` |
| PD-9 | `report_facts` schema = `spec.report_model.model_json_schema()` untrimmed; exposed as `report_facts_schema(spec)` | graph-tools §2; AEA-60 AC-5 |
| PD-10 | Render runs SONNET over the whole user text (idempotent defence); user budget 6 messages × 1,000 chars [A] | data.md §1; context-management rule 4 |
| PD-11 | Scheduling wording names no scheduling tool | graph-tools §1 (names are AEA-28's); AEA-60 AC-5 |
| PD-12 | `ToolStepRequest.max_tokens=3000`, `effort=None` placeholders; the gateway replaces both with the role's `RoleSpec` | AEA-20 plan `_redact_tool` ("the spec is authoritative for the role") |
| PD-13 | One `except Exception` at the run boundary; log the exception type name only | DO-4 §5 "never raises"; AEA-11 PD-3 keeps test-script errors visible |
| PD-14 | Test doubles subclass `ModelGateway` / `ToolDispatcher` (no `super().__init__`) so the runner's signature keeps the contract's concrete types | graph-tools §2 signature; mypy strict |
| PD-15 | `spec = specs[...]` outside the `try` (a missing kind is a wiring bug excluded by AC-19 and AEA-51's start-up check) | DO-3 §4.5 |
| PD-16 | The scheduling state JSON leaves out `shown_slots[*].shown_turn` (`_SCHEDULING_STATE_EXCLUDE`); every other slice field is sent | R-45 (only what the specialist needs); SONNET `_CARD` masks dash-separated 13–19-digit runs with no checksum |

### 8.2 Collisions with sibling tickets

| Surface | Sibling | Handling |
|---|---|---|
| `tests/unit/agent/prompts/` | AEA-38 (merged: `__init__.py`, `test_reply_*.py`), AEA-37 | this ticket adds only `test_specialist_prompts.py` and `test_specialist_prompt_turns.py` |
| `tests/journeys/j2/` | AEA-38 (`test_aea_38.py`, merged), AEA-51 | one file per ticket: `test_aea_35.py` |
| `.claude/reference/area-map.md` A7b row | AEA-22, AEA-39, AEA-14 share the row | edit only this ticket's two path mentions; expect a trivial text conflict at merge |
| `.claude/state/icm-progress.md` *Routes verified…* rows, `docs/design/code-design.md` §3 | every build ticket | add one row / append to three lines only, as step 9 says; trivial conflicts expected |
| `docs/testing/journeys/` | every ticket | one file per ticket |
| `SpecialistTask`, `KnowledgeSlice`, `AccountSlice` | AEA-35b (owner, `domain/tools.py`); AEA-39 consumes them too | resolved: AEA-35b owns them; neither AEA-35 nor AEA-39 defines or edits them |

### 8.3 Requests to the orchestrator

- **R-1 (resolved 2026-10-21).** The specialist task types were the blocker of earlier refreshes. Innocent chose option A
  (§9.1); AEA-35b builds `SpecialistTask`, `KnowledgeSlice` and `AccountSlice` in `domain/tools.py` exactly as sketched
  here (branch `aea-35b-specialist-types`, `68f7f19`). The orchestrator merges AEA-35b before dispatching this
  ticket's implementer; step 0.2 checks it.
- **R-2 (AEA-60).** Rendered specialist requests and the tool sets are reachable as `SPECS[kind].render(task, ctx)`,
  `dispatcher.schemas(SPECS[kind].tool_kinds)` and `report_facts_schema(SPECS[kind])`; the rule constants are public in
  `agent/prompts/specialists.py`.
- **R-3 (AEA-51).** Wire `SpecialistRunner(gateway=…, transcript=<the SPECIALIST adapter object>, dispatcher=…,
  specs=SPECS, brakes=limits.brakes, trace=<the container's sink>)`; the attributes are public (PD-8).
- **R-4 (AEA-08 reconcile).** AEA-35b already added the home note to graph-tools §2; AEA-08 reconciles the file names there. graph-tools §2: `specs: Mapping[str, SpecialistSpec]` → `Mapping[SpecialistKind,
  SpecialistSpec]` (PD-7). DO-4 §5 still shows `run_specialist(spec, task, ctx)` (AEA-02 plan §8.4 item 4 already lists it).
- **R-5 (dev log).** The ticket's run gets one dev-log entry in `Gauntlet AI/devlogs/aea-callcenter/` per
  `.claude/reference/dev-log.md`; that folder is outside this ticket's owned files, so the orchestrator writes it.

### 8.4 Spec gaps and other risks

- **Gateway behaviour on `halt` with `failure`** (`PROVIDER_SPEND_CAP` + failure): both are copied (PD-1 makes the
  status `failed`); the act node writes the halt only (graph-nodes §4).
- **Reviewer note (security surface).** Untrusted customer text reaches a tool-calling model here. It is SONNET-masked
  twice (by AEA-39 and by render, PD-10), and every argument is validated and scope-checked by dispatch (AEA-22). If
  `code-review-agent` judges this a security surface, the orchestrator adds `risk::security` (`build-loop-test-scope.md`).
- **mypy on `SPECS`'s literal keys.** If mypy infers the dict literal inside `MappingProxyType({...})` as
  `dict[str, SpecialistSpec]` and rejects the `Final[Mapping[SpecialistKind, SpecialistSpec]]` annotation, build it in
  two statements: `_SPECS: dict[SpecialistKind, SpecialistSpec] = {...}` then `SPECS: Final[Mapping[SpecialistKind,
  SpecialistSpec]] = MappingProxyType(_SPECS)`. Do not loosen the key type to `str`.
- **mypy on `ModelOutcome[ToolStep](…)`** in tests: AEA-20 prototyped runtime parametrisation with PEP 695; if mypy
  complains, build it as `ModelOutcome[ToolStep].model_validate({...})`.
- **`ToolSchema.input_schema` type** vs `model_json_schema()` (`dict[str, Any]`): use the `cast` in §4.5.
- **File sizes:** runner ≤ 300, specs ≤ 400, prompts ≤ 250, each test file ≤ 500 lines. If `test_runner.py` passes 500,
  move `test_wp1_knowledge_run_cites_current_file` and `test_unexpected_error_returns_failed_result` into
  `tests/unit/agent/specialists/test_runner_cases.py` (owned; add it to the commit).

### 8.5 What the implementer must not do

- Do not define `SpecialistTask`, `KnowledgeSlice`, `AccountSlice` (AEA-35b's, in `domain/tools.py`) or any other type
  in `domain/*`, `ports/*`, or in this ticket's modules as a stand-in. If they are missing, stop and report (step 0.2).
- Do not edit `agent/gateway.py`, `agent/tools/*`, `agent/nodes/*`, `domain/*`, `ports/*`, `policy/limits.py`,
  `tests/fakes/*`, `tests/conftest.py`, `tests/unit/test_import_direction.py`, `tests/journeys/support/`.
- No `if spec.kind == …` and no kind string literal in `runner.py`; no signal, no check event, no customer-facing
  text, no `SpecialistTask` assembly, no tool executor, no fee/zone/slot rule.
- Never log, trace or store `ProviderMessages`, message text, tool arguments or tool results; never log `str(exc)`.
- No literal six-digit code, card-like number or full phone number anywhere in code or tests (generate them at run time
  in the AC-11 test only). No paid model call; no `live` test here. No port binding.
- Never `git add -A`; never push or force-push; never read `.env`.

---

## 9. Readiness

**READY.** Every decision is made; the one product question (§9.1) was answered by Innocent on 2026-10-21 (option A).

- **Prerequisite, merged before this ticket builds:** AEA-35b (`SpecialistTask`, `KnowledgeSlice`, `AccountSlice` in
  `domain/tools.py`; branch `aea-35b-specialist-types`, `68f7f19`). The orchestrator's note says it merges first; step
  0.2 stops the implementer if it has not.
- Already on `main` at `f466ff7` and verified: AEA-01 (`Brakes`), AEA-02 (every other domain and port type), AEA-04
  (`redact`), AEA-11 (`FakeToolModel`, `InMemoryTraceSink`, `provider_call`, `WORKED_PAIRS_NOW`), AEA-20
  (`ModelGateway`, `ModelOutcome`), AEA-22 (`ToolDispatcher`, `DispatchedCall`), AEA-33 (`kb_search`), AEA-57 (harness),
  AEA-17 (Anthropic `ToolTranscript`), AEA-21 (`GraphDeps`, act stub), AEA-27 and AEA-28 (executors, doubled here),
  AEA-38 (reply prompts; `tests/unit/agent/prompts/__init__.py`).

Siblings (AEA-39 act node, AEA-51 wiring) are called by injection or tested with doubles, not waited on. The `[journey]`
criterion's integrated level waits on AEA-51 (not a merge blocker; the record says so). No sign-off decision D-4…D-15 is
touched; GRT-6…GRT-9 are settled. **Gates:** none (no human, paid or live gate). No security review unless the reviewer
adds `risk::security`.

### 9.1 Decision for Innocent (answered 2026-10-21: option A; kept as history)

**The story.** The specialists are the middle of every customer turn: the planner picks a task, a specialist looks
things up with tools (the knowledge base, the invoice, the calendar), and the responder writes the reply. The runner
that drives them takes one input, a `SpecialistTask` ("this task, this customer text, this slice of state"). The
signed Stage 7 contract says that type lives in `domain/specialists.py`, built by AEA-02. AEA-02 merged without it,
because it cannot live there: `SpecialistTask` contains the planner's `PlannedTask`, which lives in `domain/turn.py`,
and `turn.py` already imports `specialists.py`. Putting it where the contract says would make two files import each
other, and Python fails on that. AEA-02 asked for a small follow-up; the follow-up that was cut as AEA-02b went to the
case views instead. So AEA-35 (specialists), AEA-39 (act node), and behind them AEA-51 (the integrated customer path,
J-2 and J-3) and AEA-60 (prompt checks) are all waiting on three small types nobody owns. As of `dd1b110` every other
wave-1 and wave-2 dependency of this ticket has merged, so this is the only thing holding it. The two slice types were also never sketched in any
contract; the recommendation is that they carry only a `kind` marker, because the knowledge specialist needs nothing
but the text and the account tools get the verified customer from code. Cheap to reverse later: it is one small file
and a test.

**Option A: put the three types in `domain/tools.py` (recommended).** A ~30-minute follow-up ticket adds them next to
`ToolCallScope`, the runner's other input; AEA-08 notes the home change against graph-tools §2. AEA-35 and AEA-39 then
build exactly as planned. Gives up only the signed file location.
**Option B: keep the signed home with a deferred import.** The types go in `domain/specialists.py`, importing
`PlannedTask` only for type checking and finishing the model from `turn.py`. Keeps the contract text as written, but
`SpecialistTask` then fails at runtime in any process that has not yet imported `turn.py`: a subtle, order-dependent
bug class.
**Option C: let AEA-35 define them in its own `agent/specialists/specs.py`.** No new ticket; AEA-35 can start now. But
a domain type then lives in the agent layer, against DO-3's layering, and AEA-39 and AEA-51 import it from there. The
slice shapes would be decided inside a feature ticket.
*Recommended: A.* It is the only option that is cycle-free, keeps domain types in `domain/`, and needs no change to
any ticket's owned files except the new follow-up's.

**Decision needed:** May the specialist task types (`SpecialistTask`, plus `KnowledgeSlice` and `AccountSlice` as
`kind`-only markers) live in `domain/tools.py` instead of the signed `domain/specialists.py` (option A), or do you
want B or C?
