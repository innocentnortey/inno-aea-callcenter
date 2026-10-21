## [AEA-22] tools: dispatch, guard, lookup log

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

> **US-8.** As a **homeowner** asking about my bill, I need to receive a one-time code at the phone or email on my account
> and type it in the chat, so that nobody else can read my account by guessing my name. *(Also serves US-19: "every fact
> opens its source".)*

**What it does in practice.** A specialist model may *ask* for a tool; code decides whether it runs (agent-tools rule 4:
"the model advises; code executes"). Every tool request from every specialist passes through one dispatcher. It sends
the model schemas generated from each tool's `args_model`, checks each request (known tool, allowed for this specialist,
valid arguments, and `requires_verified` against the verified customer that code bound into `ToolCallScope`), and only
then calls the executor the owning area supplied. Whatever happens, the model gets back JSON with its `tool_call_id`,
never an exception, and **every call, run or refused, leaves exactly one `lookup_log` row** (R-29), so the brief's facts
can open their sources and the turn's tool count matches the log.

**`agent/tools/dispatch.py`**, exactly as stage7/graph-tools.md §1 (GRT-1):
- **`ToolRegistry(defs)`**: raises `ValueError` at start-up (never at turn time) on a duplicate name or a name outside
  `[a-z_]{1,64}`; `get(name)`; `for_kinds(kinds)` in stable order by name; `check_covers(kinds)` fails start-up when a
  kind a spec names has no tool. Built by AEA-51 from the three executor factories `knowledge_tools(retrieval)` (AEA-33),
  `account_tools(uow)` (AEA-27), `scheduling_tools(scheduling)` (AEA-28); nothing registers itself at import time.
- **`ToolDispatcher(registry, uow)`** with `schemas(kinds) -> tuple[ToolSchema, ...]` (generated from `args_model`,
  trimmed, `strict=True`, never a scope field such as `customer_id`; cached per kind set) and
  `dispatch(calls, *, kinds, scope) -> tuple[DispatchedCall, ...]`: same length and order as `calls`, never raises.
- **Guard order, per call, before any executor runs:** unknown name → `unknown_tool`; kind not in `kinds` →
  `not_allowed`; `args is None` or invalid against `args_model` → `bad_arguments`; `requires_verified` and
  `scope.customer_id is None` → `not_verified` (R-14: only `kb_search` and the zone-only window search are open). A
  refused call never executes.
- **Execute:** `executor(args_model instance, scope)` with no unit of work open (DO-3 §2.3 rule 1); an exception →
  `ToolError(tool_failed, retryable=False)`, logged by exception type name only. `DispatchedCall.content` is the JSON
  text the model receives, ≤ 4,000 characters (DO-4 §5).
- **Lookup log (DO-4 §5 *Lookup-log rule*, graph-tools §1):** an executed **read** tool → `ToolResult.lookup` appended in
  its own short `uow(write=True)` after the executor returns; a **write** tool with `lookup_written=True` → skipped (the
  scheduling service wrote it in the booking's transaction); a **refused or failed** call → dispatch builds
  `LookupEntry(tool=name, record_ids=(), passage_ids=(), result_seen="refused:<code>" | "failed",
  message_id=scope.message_id, turn_id=scope.ids.turn_id)`. A failed lookup write is logged, leaves
  `ToolCallRecord.lookup_id = None` and does not change what the model receives. `result_seen` holds ids and values, no
  free text over 80 characters, after the STORE profile (stage7/data.md §1 lists AEA-22's lookup-log snapshots as a
  `redact` consumer).
- **`ToolCallRecord`** per call (graph-tools §1): `tool_call_id`, `name` as sent (an unknown name kept to ≤ 64
  characters), `kind` (`None` for `unknown_tool`), `outcome` `ok` / `refused` / `failed`, `error`, the entry's
  `record_ids` and `passage_ids`, `lookup_id`, `elapsed_ms`. Graph-core GRC-13 counts `tool_failures` from `error`.

**Example pair (WP-2, graph-tools §1).** Input: the account specialist's model asks for an invoice read for INV-204411
**before** the code turn (`scope.customer_id = None`, `kinds = {account_read}`). Expected: a `DispatchedCall` whose
content is `ToolError(code=not_verified)` for that `tool_call_id`, the executor never called, no account value in the
content, and one `lookup_log` row with `result_seen = "refused:not_verified"`. After Omar Patel (MHC-10002) types the
correct code, the same request with `scope.customer_id = MHC-10002` runs the executor and returns the invoice as billed
(issued 2026-10-02, due 2026-11-01, $478.00 unpaid: diagnostic $89, contactor replacement $245, after-hours dispatch
$144), and one `lookup_log` row records the tool, the record id `INV-204411`, the snapshot seen, the `message_id` and the
`turn_id`.

### Source
- stage7/graph-tools.md §1 (`ToolKind`, `ToolErrorCode` 13 values, `ToolSchema`, `ToolCall`, `ToolCallRecord`,
  `ToolRegistry`, `DispatchedCall`, `ToolDispatcher`, registration by factory), §2 (the runner that calls it); ledger
  `docs/plans/7b-decisions/graph-tools.md` GRT-1.
- stage7/graph-core.md §2 (`TurnInput.message_id`, `TurnRecord.tool_calls` = this turn's `lookup_log` rows), §8 (GRC-13
  `tool_failures`); stage7/data.md §1 (`redact`, STORE profile) and §9 item 5; stage7/cases.md §1.2
  (`core.lookup_log.append`).
- PRD R-14 (public questions unverified), R-15, R-16, R-29 (lookup log, snapshot vs current); US-8, US-19.
- DO-3 §4.5 (`agent/tools/dispatch.py`: "Generate tool schemas from `ToolDef`; validate, scope-check, execute and log
  every call"), §6 S-13, §7 rows R-14 and R-29, §2.3 rule 1.
- DO-4 §5 (`ToolCallScope`, `LookupEntry`, `ToolError`, `ToolResult`, `ToolDef`, *Lookup-log rule*), §13
  (`UnitOfWorkFactory`).
- DO-6 *Records* `lookup_log`, line 65 rule 18, *Missing instrumentation* row "A tool call left no lookup-log row",
  *Content and redaction*, CAP-1. DO-1 §10 *Prompt injection*.
- `agent-tools.md` rules 3–7; `safe-validation-errors.md`; WP-2; HP-3.
- **Brief check:** serves "They will ask their own questions and try to break it, so make sure edge cases and escalation
  behave."; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [failure/refusal] `requires_verified` is enforced for **every** `ToolDef` that sets it: with `scope.customer_id = None` the call returns `not_verified` and the executor is never invoked; `kb_search` and the zone-only window search run unverified — verify: `tests/unit/agent/tools/test_dispatch.py::test_requires_verified_guard` (parametrised over every `ToolKind`; executor doubles that record calls) — evidence: zero executor calls on the refused cases; the WP-2 pre-code case returns `not_verified`.
- [ ] AC-2 [failure/refusal] Guard order and codes: unknown name → `unknown_tool`; a kind outside `kinds` → `not_allowed`; `args=None` or schema-invalid arguments → `bad_arguments`; a call failing two guards gets the earlier code; each returns a `ToolError` with its `tool_call_id` and no execution — verify: `::test_guard_order_and_codes` — evidence: code per case asserted.
- [ ] AC-3 [invariant] `dispatch` answers every call and never raises: several calls in one step return results of the same length and order with matching `tool_call_id`; an executor that raises becomes `ToolError(tool_failed, retryable=False)` and the log line names the exception type only; `content` is ≤ 4,000 characters — verify: `::test_every_call_answered_in_order` — evidence: results list asserted; no exception escapes; captured log line asserted.
- [ ] AC-4 [invariant] Schemas are generated from `args_model` (`input_schema` equals the trimmed `model_json_schema()`, `strict=True`) and never contain `customer_id` or any `ToolCallScope` field; `schemas(kinds)` returns only those kinds' tools, by name, and is cached per kind set — verify: `::test_schemas_generated_without_scope_fields` — evidence: generated schema compared with the model's; no scope field present; second call returns the same object.
- [ ] AC-5 [failure/refusal] Registry start-up checks: a duplicate tool name, or a name outside `[a-z_]{1,64}`, raises `ValueError` when `ToolRegistry` is built; `check_covers` raises when a kind has no tool — verify: `tests/unit/agent/tools/test_registry.py::test_registry_rejects_bad_defs` — evidence: each error raised at construction or `check_covers`, never during `dispatch`.
- [ ] AC-6 [capture] **Each** dispatched call, executed or refused or failed, leaves exactly one `lookup_log` row: executed read tools written by dispatch in their own `uow(write=True)` after the executor returns; write tools with `lookup_written=True` not written twice; refused and failed calls get the dispatch-built entry (`result_seen` `refused:<code>` / `failed`, empty ids); every row carries `message_id` and `turn_id` from scope, and each `ToolCallRecord.lookup_id` is that row's id — verify: `::test_one_lookup_row_per_call` (a `UnitOfWorkFactory` double per DO-4 §13 recording `lookup_log.append`) — evidence: row count equals call count in a mixed step (read, refused, failed, write with `lookup_written`).
- [ ] AC-7 [failure/refusal] A failed lookup write is logged, leaves `lookup_id = None` on that call's `ToolCallRecord`, and changes neither the content the model receives nor the other calls' rows — verify: `::test_lookup_write_failure_does_not_change_result` — evidence: content identical to the success case; one log line; other rows written.
- [ ] AC-8 [invariant] `ToolCallRecord` per call: `outcome` `ok` / `refused` / `failed` with `error` set exactly when not `ok`; `kind=None` and the name cut to 64 characters for `unknown_tool`; `record_ids` and `passage_ids` equal the lookup entry's; `elapsed_ms ≥ 0` — verify: `::test_tool_call_records` — evidence: fields asserted per case.
- [ ] AC-9 [negative] Rejected and private values stay out: a distinctive customer id the model puts in its arguments (`MHC-99999`), a full phone number and a synthetic card-like number in the arguments are absent from the `ToolError` message, the `DispatchedCall.content`, the `lookup_log` row, the `ToolCallRecord` and captured log output; `result_seen` holds no free text over 80 characters and no card-like number or code — verify: `::test_rejected_values_absent` (values generated at run time, never in test names) — evidence: absence asserted over the error, content, appended entry, record and `caplog`.
- [ ] AC-10 [invariant] Scope comes from code, not the model: the executor receives the `ToolCallScope` the caller bound (verified customer, shown slot ids, clock reading, `message_id`, ids), unchanged by anything in the arguments — verify: `::test_scope_bound_by_code` — evidence: the executor double receives the bound scope even when the arguments name another customer.
- [ ] AC-11 [invariant] No unit of work is open while an executor runs: the read-tool lookup row is written after the executor returns, in its own short unit of work — verify: `::test_lookup_write_outside_executor` (double records the order of `uow` enter/exit and executor calls) — evidence: the asserted order.
- [ ] AC-12 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-22.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-2 and J-3 (tool dispatch, the verified guard, lookup-log rows) as the journeys that will exercise this code once AEA-57 and AEA-51 land, so the seam audit knows where to look (pattern C, `docs/plans/ux-join/backend-amendments.md` §3) — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-13 [regression/context] In the same change: `.claude/reference/area-map.md` `agent/tools/dispatch.py` row (planned → actual + commit, noting the move from A7b/wave 3 to wave 1); `.claude/state/icm-progress.md` affected row; DO-4 §5 links stage7/graph-tools.md §1 (GRT-1) for the dispatcher and registration; DO-3 code-design status for `dispatch.py`; a dev-log entry — verify: `git diff --name-only` — evidence: those paths in the diff.

### Observability
- Responsibilities: for WF-1 (and its `eval`/`load`-tagged turns under WF-9 and WF-10): one `lookup_log` row per tool
  call with tool, record or passage ids, result seen, `message_id` and `turn_id` (DO-6 *Records*), which DO-6's check
  "tool calls counted on the `turn` record = lookup-log rows for that `turn_id`" relies on (graph-core §2
  `TurnRecord.tool_calls`); one `ToolCallRecord` per call with `outcome`, `error` and `elapsed_ms` for the runner's
  capture and GRC-13's `tool_failures` count, and from which AEA-35's runner emits one `tool:<name>` span per call
  (R-G-17; DO-6 rule 18). This module emits no span itself. Refusals are typed codes, never message text.
- Capture evidence: AC-6 (one row per call) and AC-9 (forbidden values absent) here; AEA-51's CAP-1 drives CON-2 through
  WP-2 and finds the `lookup_log` rows for the invoice read with the code, the card-like number and the full phone
  number absent.

### Evaluation
- Checks: none added to a suite; E-1's trajectory items ("which specialist and tool, in order") and E-6's brief facts
  read the rows this writes; M-21's "nothing private before a correct code" rests on AC-1.
- Expected-answer authority: R-14/R-15 (identity decisions) decide which tools need a verified customer; DO-4 §5 and
  graph-tools §1 decide the codes and the lookup-log rule (evaluation plan *Expected-answer authority*, rows "Account
  reads" and "Handoff brief").

### Metrics
- References: M-21 (action-rule violations: nothing private before the code), M-7 (answers citing an excluded file:
  counted from `lookup_log` passage ids), M-12 (invented brief facts: judged against the lookup log), M-24 (tool errors
  feeding `degraded_handoff` / `tool_error`).
- Acceptance conditions: one row per call (AC-6) keeps M-7 and M-12 computable; AC-1 holds M-21's identity rule at 0 by
  construction; typed `error` codes (AC-8) keep M-24's tool-error share countable. No target set here.

### Blocked by
- AEA-02 (`domain/tools.py` incl. `ToolKind`, `ToolErrorCode`, `ToolCallScope`, `LookupEntry`; `ports/models.py`
  `ToolSchema`, `ToolCall`; `UnitOfWorkFactory`), AEA-04 (`privacy/redact.py`).
- Not a merge blocker: AC-12's journey record names *Blocked by* AEA-57 (harness, wave 2) and AEA-51 (journey landing,
  wave 3); this issue merges on its unit and contract tests.

### Agent handoff
- Area / owner: tool dispatch (A7b module, wave 1 per slice plan); file `src/meridian/agent/tools/dispatch.py`, tests
  `tests/unit/agent/tools/test_dispatch.py` and `test_registry.py`; no `register_` hunk for tools (GRT-1: AEA-51 builds
  the registry and dispatcher in the graph-wiring hunk).
- Contracts and shared surfaces: **consumes** `domain/tools.py` and `ports/models.py` types (AEA-02), the
  `UnitOfWorkFactory` port and `core.lookup_log.append` by their DO-4 §13 / stage7/cases.md §1.2 signatures (real
  storage AEA-10, a double here), `redact` (AEA-04). Executors arrive as `ToolDef`s from AEA-27, AEA-28, AEA-33's
  factories (doubles here). **Produces** `ToolRegistry`, `ToolDispatcher`, `DispatchedCall` for AEA-35 (the runner calls
  `schemas` and `dispatch` for every step) and AEA-51 (start-up `check_covers`); the `lookup_log` rows AEA-29 (brief
  sources), AEA-38 (fact-check evidence) and AEA-53 (M-7) read. **Must not edit:** `domain/tools.py`, `ports/*`
  (AEA-02), the executor modules (27, 28, 33), `agent/specialists/*` (AEA-35), `adapters/sqlite/repos_core.py` (AEA-10).
- Scope boundary / refusal: no executor bodies; no specialist loop, brakes or identical-call stop (AEA-35, DO-4 §5
  runner rules); no business refusals such as fee-bearing, not-shown or not-owned (`SchedulingService.Refused`, AEA-28);
  no generic SQL, shell or file tool (agent-tools rule 7); no global or import-time registry.
- Wave and gates: wave 1; gates None.
- Lane: `lane::build-loop` — source and tests the turn path runs.
- Risk: **security** (`risk::security`, slice plan §1 row AEA-22) — a bug here could show one customer's account to an
  unverified caller, or let model-chosen identifiers reach an executor (R-14, R-15; untrusted model input reaching a data
  read). Frozen failing tests first (AC-1, AC-9, AC-10 among them); `security-privacy-agent` at the wave merge.
- Entry points added or changed: None
- Settled R-G-17 (graph-tools §2; `docs/plans/7b-decisions/residuals-graph.md`): this ticket records
  `ToolCallRecord.elapsed_ms` and emits no span; AEA-35's runner turns each record into a `tool:<name>` span. The
  dispatcher stays trace-free (`ToolDispatcher(registry, uow)` unchanged; no `SpanHandle` on `ToolCallScope`).
