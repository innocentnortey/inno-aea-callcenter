# Plan — [AEA-22] tools: dispatch, guard, lookup log

**Status:** planned — READY to build once AEA-02 is merged on `main` (the only import still missing; §9).
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/22 · **Base revision:** `16ca639` (main
at the refresh). On main: AEA-01 (scaffold, `pyproject.toml`, `tests.journeys.affected`; merge `07924f5`), AEA-03, AEA-04
(`privacy/redact.py`; merge `ef03e05`), AEA-08, AEA-25. **Not on main:** AEA-02. Its worktree
`inno-aea-callcenter-wt/AEA-02` (branch `aea-02-aea-02-domain-ports`, `de9bb42`) holds frozen tests only; `domain/` and
`ports/` on main are empty package markers.
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21. First planned against `5f2e1bb`; refreshed against `16ca639`
the same day (header, §1.2, §1.3, §2.1 ICM row, §3.1 rows 27–28, §3.2 S-10, §5 steps 4–5 and 8, §6, §7, §8 R-10–R-12,
§9). **Implementer:** `fanout-implementer` on Sonnet.
**Risk:** `risk::security` → `test-writer-agent` freezes the tests in §3.2 **before** the implementer starts;
`security-privacy-agent` reads this diff at the wave-1 merge. **Lane:** `lane::build-loop`. **Wave:** 1. **Gates:** none.

---

## 1. Goal and sources

### 1.1 Goal (issue *What to build*, `docs/plans/tickets/AEA-22.md`)

> **US-8.** As a **homeowner** asking about my bill, I need to receive a one-time code at the phone or email on my account
> and type it in the chat, so that nobody else can read my account by guessing my name. *(Also serves US-19.)*

**What it does in practice.** A specialist model may *ask* for a tool; code decides whether it runs. Every tool request
passes through one dispatcher (`src/meridian/agent/tools/dispatch.py`). It sends the model schemas generated from each
tool's `args_model`, checks each request (known tool → allowed for this specialist → valid arguments → `requires_verified`
against the verified customer that code bound into `ToolCallScope`), and only then calls the executor the owning area
supplied. Whatever happens, the model gets back JSON with its `tool_call_id`, never an exception, and **every call, run or
refused, leaves exactly one `lookup_log` row** (R-29).

**Worked pair (WP-2, graph-tools §1).** The account specialist asks for `read_invoices` for `INV-204411` before the code
turn (`scope.customer_id = None`, `kinds = {account_read}`) → a `DispatchedCall` whose content is
`ToolError(code=not_verified)` for that `tool_call_id`, the executor never called, no account value in the content, one
`lookup_log` row with `result_seen = "refused:not_verified"`. After the correct code, the same request with
`scope.customer_id = MHC-10002` runs the executor and returns the invoice as billed (issued 2026-10-02, due 2026-11-01,
$478.00 unpaid: diagnostic $89, contactor replacement $245, after-hours dispatch $144), and one `lookup_log` row records
the tool, record id `INV-204411`, the snapshot, the `message_id` and the `turn_id`.
Test: `tests/unit/agent/tools/test_dispatch.py::test_wp2_invoice_read_before_and_after_code`.

### 1.2 Context

The Stage 7 slice plan moved `dispatch.py` from area A7b (area wave 3) to ticket wave 1 so the executors (AEA-27, 28,
33, wave 2) and the runner (AEA-35) build against a real dispatcher. Redaction (AEA-04) and tooling (AEA-01) are on
main; the shared types come from AEA-02, which is still being built. Storage (`core.lookup_log.append`, AEA-10) lands in the same wave and
is reached through its DO-4 §13 signature only (§4.4, §8 R-1).

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-22.md` (= issue #22) | AC-1…AC-13, WP-2, scope boundary, must-not-edit list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-22 (wave 1, Sec, blocked by 02, 04; owns `agent/tools/dispatch.py`; calls executors 27, 28, 33 by name); §3 collision map rows `agent/tools/*.py`, `.claude/reference/area-map.md`…, `tests/journeys/` | One file per ticket under `agent/tools/`; each ticket edits only its own context row |
| Component contract (wins) | `docs/design/contracts/stage7/graph-tools.md` §1 (GRT-1: `ToolKind`, `ToolErrorCode` 13 values, `ToolSchema`, `ToolCall`, `ToolCallRecord`, `ToolRegistry`, `DispatchedCall`, `ToolDispatcher`, registration by factory); §2 (runner calls `schemas` + `dispatch`; R-G-17: dispatcher emits no span) | Exact public API (§4.3) |
| Component contract | `docs/design/contracts/internal-components.md` (DO-4) §0 (`MeridianModel`, `LLMFacing`, errors never carry values), §5 (`ToolCallScope`, `LookupEntry`, `ToolError`, `ToolResult`, `ToolDef`, *Lookup-log rule*, runner rules), §13 (`UnitOfWorkFactory`, `core.lookup_log.append(entry) -> int`), §16 (addenda win) | Types consumed; lookup-log rule |
| Storage contract | `stage7/cases.md` §1.0 (unit of work: `ROLLBACK unless commit()`; exception rolls back and propagates), §1.2 (`core.lookup_log.append(entry: LookupEntry) -> int`, `thread_id` copied from the message row) | `_append_lookup` (§5 step 2.7) |
| Redaction contract | `stage7/data.md` §1 (`redact(text, profile) -> Redacted`; STORE replaces card-like numbers and 6-digit codes only; AEA-22 named as a consumer for lookup-log snapshots), §4 (`KbSearchArgs.query` 1–300; `knowledge_tools` binds `kb_search`, `requires_verified False`), §9 item 5 | STORE on `result_seen` |
| Graph contract | `stage7/graph-core.md` §2 (`TurnRecord.tool_calls` = this turn's `lookup_log` rows), §8 GRC-13 (`tool_failures` counts a `ToolCallRecord` that ended in a `ToolErrorCode`) | One row per call; typed `error` |
| Decision ledger | `docs/plans/7b-decisions/graph-tools.md` GRT-1 | Registration by factory; no global registry |
| Code design | `docs/design/code-design.md` (DO-3) §2.1 (agent → core, ports; never adapters), §2.3 rule 1 (no transaction open across a call out), §4.5 row `agent/tools/dispatch.py`, §6 S-13, §7 rows R-14, R-29 | Dependency direction; no uow around executors |
| Requirements | PRD R-14 (public questions unverified: only `kb_search` and the zone-only window search are open), R-15, R-16, R-29 (lookup log, snapshot vs current); US-8, US-19 | Guard; lookup rows |
| Evaluation plan (DO-5) | Ticket *Evaluation*: no checks added; E-1 trajectory and E-6 brief facts read these rows; M-21 rests on AC-1 | n/a beyond the rows (other tickets own the evals) |
| Observability (DO-6) | `docs/design/observability-contract.md` *Records* `lookup_log` (line 114), *Missing instrumentation* "A tool call left no lookup-log row" (line 229), *Content and redaction* (codes and card-like numbers never in DB, logs never hold free text), CAP-1 (line 256) | One row per call; logs carry IDs and codes only |
| Metrics (DO-7) | M-7, M-12 (computed from lookup rows), M-21 (identity rule), M-24 (tool-error share from `error`) | Typed codes; one row per call |
| Rules | `.claude/rules/agent-tools.md` rules 3–7; `.claude/rules/safe-validation-errors.md` rules 1, 2, 5; `.claude/rules/build-loop-test-scope.md` (+ AEA addition); `.claude/rules/integrated-journeys.md` §3 rule 1, §4; `.claude/rules/context-maintenance.md` | Every branch handled; no value in any error; negative tests; journey record at `mock-tested` |
| Sibling plans (for exact import paths) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4 (type homes, re-exports, import order), §4.9 `domain/tools.py`, §4.12 `ports/models.py`, §4.13 `ports/runtime.py`, §4.15 repo shells; `AEA-01.md` §4.1 (pyproject tool config), §4.5 (affected-journeys command); `AEA-10.md` (`LookupLogRepo.append`, `StorageError`) | §4 |
| Sibling plans (consumers, executors) | `AEA-35.md` *Doubles* (`ScriptedDispatcher(ToolDispatcher)` overrides `schemas` and `dispatch` and never calls `super().__init__`, PD-14; its `dispatched(...)` helper renders content exactly as §5 step 2.6); `AEA-28.md` §5.2–5.4 and AC-15 (reads return `lookup_written=False`; successful writes `True`; service refusals `False` with a `refused:<code>` entry; a lock timeout raises); `AEA-27.md` AC-12, `AEA-33.md` AC-5 (their flags and args fields pass S-1 and S-2) | §5 steps 4–5; §8 R-10, R-11 |
| Code on main (`16ca639`) | `src/meridian/privacy/redact.py` (`redact`, `RedactionProfile.STORE` = card + code rules; probed: `ok 4000 4000 4000 4000 148291` → `ok [card number removed] [code]`, `no_such_tool_148291` → `no_such_tool_[code]`, the WP-2 snapshot unchanged); `pyproject.toml` `[tool.mypy]` (strict, `pydantic.mypy`, `init_typed`); `tests/journeys/affected.py` (`--base`, `--list-only`); `web/container.py` `register_tool_dispatch` no-op stub (line 190); `tests/unit/test_import_direction.py` | §4, §7 |
| Stage 7 sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | None touches AEA-22 |

---

## 2. Boundary

### 2.1 Files this slice owns (the only files the implementer or test-writer may create or edit)

| File | Action | Who writes it |
|---|---|---|
| `src/meridian/agent/tools/dispatch.py` | create | implementer |
| `tests/unit/agent/tools/__init__.py` | create (empty, 0 bytes) | test-writer |
| `tests/unit/agent/tools/dispatch_doubles.py` | create | test-writer (frozen) |
| `tests/unit/agent/tools/test_dispatch.py` | create | test-writer (frozen) |
| `tests/unit/agent/tools/test_registry.py` | create | test-writer (frozen) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-22.md` | create (date = the day you run it, America/Chicago) | implementer |
| `.claude/reference/area-map.md` | modify **only** the `agent/tools/dispatch.py` mention in the A7b row | implementer |
| `.claude/state/icm-progress.md` | add **one** new row *Routes verified against code and tests* below the last existing row of that name (AEA-04 and AEA-03 each added their own; the merges kept both), and update the *Last reconciled* line | implementer |
| `docs/design/code-design.md` | modify **only** the §3 tree line `│   ├── tools/dispatch.py …` | implementer |
| `docs/design/contracts/internal-components.md` | add **one** note line under `## 5. Specialist contracts` | implementer |
| `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<YYYY-MM-DD>-aea-22-tool-dispatch-claude-01.md` | create (outside this repo; do not commit it from this repo) | implementer |

`src/meridian/agent/tools/__init__.py` already exists (AEA-01 marker). Do not touch it.

### 2.2 Shared surfaces: read, never edit

`src/meridian/domain/*` and `src/meridian/ports/*` and `src/meridian/config.py` (AEA-02); `src/meridian/privacy/redact.py`
(AEA-04); `src/meridian/web/container.py` (AEA-01 stub `register_tool_dispatch` **stays a no-op**: GRT-1 says AEA-51 builds
the registry and dispatcher in `register_graph`); `src/meridian/adapters/sqlite/*` (AEA-02 shells, AEA-10 bodies);
`pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/unit/test_import_direction.py`, `tests/journeys/**` (AEA-01, 57).

### 2.3 Owned by other tickets — must not touch

`agent/tools/{knowledge,account,scheduling}.py` (AEA-33, 27, 28), `agent/specialists/*` and `agent/prompts/*` (AEA-35),
`adapters/sqlite/repos_core.py` (AEA-10), `tests/fakes/` (AEA-11), `tests/fixtures/sqlite.py` (AEA-10),
`docs/ux/**`, `apps/web/**`, `docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, the briefing, issued data,
`docs/archive/`, `docs/parked/`, every `docs/design/contracts/stage7/*.md`.

---

## 3. Requirements and how each is verified

### 3.1 Source-contract reconciliation

| # | Obligation | Source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|---|
| 1 | `requires_verified` guard; only `kb_search` and the zone-only window search open | R-14; DO-4 §5; GRT-1 | AC-1 | in-ticket | §5 step 3.5 |
| 2 | Guard order unknown → not_allowed → bad_arguments → not_verified; refused never executes | GRT-1 | AC-2 | in-ticket | §5 step 3.2–3.5 |
| 3 | Same length/order, never raises, `tool_failed` on exception, log type name only, content ≤ 4,000 | GRT-1; DO-4 §5; agent-tools 5, 6 | AC-3 | in-ticket | §5 steps 3.6, 2.6 |
| 4 | Schemas from `args_model`, trimmed, `strict=True`, no scope field, by name, cached per kind set | GRT-1; agent-tools 3 | AC-4 | in-ticket | §5 steps 2.2, 4 |
| 5 | Registry rejects duplicate / bad names at construction; `check_covers` | GRT-1 | AC-5 | in-ticket | §5 step 3 (registry) |
| 6 | One `lookup_log` row per call; stamped `message_id`, `turn_id`; `lookup_id` = row id | GRT-1; DO-4 §5 lookup-log rule; DO-6 line 229 | AC-6 | in-ticket | §5 steps 3.7, 3.8 |
| 7 | Failed lookup write: logged, `lookup_id None`, content unchanged | GRT-1 | AC-7 | in-ticket | §5 step 2.7 |
| 8 | `ToolCallRecord` fields per call | GRT-1 | AC-8 | in-ticket | §5 step 3.9 |
| 9 | Rejected and private values absent from error, content, row, record, logs | safe-validation-errors 1, 5; DO-6 *Content and redaction* | AC-9 | in-ticket | §5 steps 2.3, 2.4, 2.5 |
| 10 | Scope from code; executor receives the bound scope unchanged | agent-tools 4; DO-4 §5 | AC-10 | in-ticket | §5 step 3.6 |
| 11 | No unit of work open while an executor runs | DO-3 §2.3 rule 1 | AC-11 | in-ticket | §5 step 3.7 |
| 12 | Journey record at `mock-tested`, Blocked by AEA-57, names J-2, J-3 | integrated-journeys §3 r1, §4 | AC-12 | in-ticket | §5 step 8 |
| 13 | Context reconciled in the same change | context-maintenance | AC-13 | in-ticket | §5 step 8 |
| 14 | `result_seen` after STORE profile | data.md §1 consumer list; ticket *What to build* | (text, not an AC) | **added** S-6 | §5 step 2.5 |
| 15 | `result_seen` "no free text over 80 characters" for **executed** reads | DO-4 §5 `LookupEntry` comment | AC-9 (partly) | **other-ticket** for executor snapshots: AEA-27, 28, 33 build `result_seen`; AEA-51 CAP-1 checks the stored rows. Dispatch-built entries are the constants `refused:<code>` / `failed` (≤ 22 chars) | AEA-27/28/33; §8 R-6 |
| 16 | A scope field can never appear in a schema (by construction, not by luck) | GRT-1 "never a scope field"; AC-4 | AC-4 | **added** S-1: registry rejects an `args_model` whose JSON schema has a property named like a `ToolCallScope` field | §5 step 3 (registry) |
| 17 | R-14 by construction: an account or write kind with `requires_verified=False` must not start | R-14; DO-4 §5 `requires_verified` comment | AC-1 (flag-driven) | **added** S-2 | §5 step 3 (registry) |
| 18 | `bad_arguments` message names declared fields + error type only; a model-invented key is never echoed | safe-validation-errors 1–2 (a key the model invents is model-controlled text) | AC-9 | **added** S-3 | §5 step 2.4 |
| 19 | Content over 4,000 chars becomes valid, truncated JSON (outcome stays `ok`; a completed write is not reported as failed) | DO-4 §5 "≤ 4,000 chars rendered" | AC-3 | **added** S-4 | §5 step 2.6 |
| 20 | An unknown tool name is STORE-redacted before the 64-char cut (record and row) | DO-6: codes and card-like numbers never in DB | AC-8 | **added** S-5 | §5 step 2.3 |
| 21 | Dispatch imports no adapter, service or web module | DO-3 §2.1 | — | **added** S-7 | test only |
| 22 | `lookup_id` for a row the scheduling service wrote (`lookup_written=True`) | GRT-1 comment "None only if its write failed" vs `ToolResult` carrying no row id | AC-6 | **added** S-8 (contract gap, engineering resolution): `lookup_id = None`; no consumer reads it (grep of docs/design, docs/plans) | §5 step 3.8; §8 R-2 |
| 23 | An executor returning something that is not a `ToolResult` is a `tool_failed`, not a crash | agent-tools 6 | AC-3 | **added** S-9 | §5 step 3.6 |
| 24 | No span from the dispatcher; `elapsed_ms` measured for AEA-35's `tool:<name>` span | R-G-17 | ticket *Observability* | in-ticket (AC-8 `elapsed_ms`) | §5 step 3.9 |
| 25 | No specialist loop, brakes, identical-call stop, business refusals, SQL/shell/file tool, global registry | ticket scope boundary; agent-tools 7 | scope | in-ticket (not built) | §6 *must not* |
| 26 | `thread_id` on every lookup row | DO-6 line 143 | — | **other-ticket**: AEA-10's `append` copies it from the message row (cases.md §1.2) | AEA-10 |
| 27 | A result whose `for_model` cannot be rendered as JSON becomes `tool_failed` and still leaves exactly one row: render runs before the row write, and a service-written write row is never doubled | agent-tools 6; GRT-1 "never raises", AC-6 | AC-3, AC-6 | **added** S-10 | §5 step 5.7 |
| 28 | `ToolDispatcher` stays subclassable by AEA-35's `ScriptedDispatcher` (no `super().__init__` call) | AEA-35 plan *Doubles* (PD-14) | — | in-ticket constraint (no criterion; mypy over AEA-35's tests proves it) | §5 step 4 |

Plan-added criteria S-1…S-10 go to the issue as one comment proposing them (the orchestrator posts it; §9).

**Entry-point registration:** None. This slice adds no route, CLI, job or experiment; the dispatcher is reached only
through AEA-35's runner inside WF-1 (DO-6 line 76), whose evaluation (E-1, E-6) and metrics (M-7, M-12, M-21, M-24) it
inherits.

### 3.2 Acceptance criteria → frozen tests (the test-writer writes these first; the implementer must not edit them)

All tests live in `tests/unit/agent/tools/`. Run: `uv run pytest tests/unit/agent/tools -q`.

| AC | Criterion (ticket, abridged) | Test | What it asserts |
|---|---|---|---|
| WP-2 | Worked pair, before and after the code | `test_dispatch.py::test_wp2_invoice_read_before_and_after_code` | Call 1 (`customer_id=None`, kinds `{ACCOUNT_READ}`, tool `read_invoices`, args `{"invoice_number": "INV-204411"}`): `len(result)==1`; `result[0].tool_call_id == "toolu_wp2_1"`; `json.loads(content)["error"]["code"] == "not_verified"`, `["error"]["retryable"] is False`, `["error"]["message"]` a non-empty str (its exact wording is not asserted); `"INV-204411" not in content` and `"478" not in content`; executor double `.calls == []`; exactly one appended entry with `tool == "read_invoices"`, `result_seen == "refused:not_verified"`, `record_ids == ()`, `passage_ids == ()`, `message_id == 41`, `turn_id == scope.ids.turn_id`. Call 2 (same call, `customer_id=CustomerId("MHC-10002")`): executor called once; its `args.invoice_number == "INV-204411"`; its scope `is` the passed scope; `json.loads(content) == WP2_INVOICE_FOR_MODEL`; one new appended entry with `record_ids == ("INV-204411",)`, `result_seen == WP2_SNAPSHOT`, `message_id == 41`, `turn_id` from scope; `record.outcome == "ok"`, `record.lookup_id` == the id the double returned |
| AC-1 | `requires_verified` enforced for every `ToolDef` that sets it; `kb_search` and the zone-only window search run unverified | `test_dispatch.py::test_requires_verified_guard` (parametrised over **every** `ToolKind`, ids = `kind.value`) | For kind `k`: one def `tool_<k.value>` (e.g. `tool_kb_search`), `args_model=EmptyArgs`, `effect="write"` for BOOK/MOVE/CANCEL/CHANGE_REQUEST else `"read"`, `requires_verified = k not in {ToolKind.KB_SEARCH, ToolKind.SLOT_SEARCH}`. Unverified scope, `kinds=frozenset(ToolKind)`, args `{}`: if requires → `ToolError.code == "not_verified"` in content, executor `.calls == []`, `record.outcome == "refused"`; else executor called once, `record.outcome == "ok"`. Then the same call with a verified scope → executor called once for every kind |
| AC-2 | Guard order and codes; earlier code wins; `ToolError` with its `tool_call_id`; no execution | `test_dispatch.py::test_guard_order_and_codes` (parametrised, ids below) | Registry: `read_invoices` (ACCOUNT_READ, `InvoiceArgs`, requires True) and `kb_search` (KB_SEARCH, `KbArgs`, requires False). Unverified scope unless stated. Cases: `unknown_with_bad_args` name `no_such_tool`, args `None` → `unknown_tool`; `not_allowed_beats_bad_args` name `read_invoices`, kinds `{KB_SEARCH}`, args `None` → `not_allowed`; `bad_args_none_beats_not_verified` `read_invoices`, kinds `{ACCOUNT_READ}`, args `None` → `bad_arguments`; `bad_args_invalid` `kb_search`, kinds `{KB_SEARCH}`, args `{"query": ""}` → `bad_arguments`; `not_verified` `read_invoices`, args `{}` → `not_verified`. Each: content's `error.code` as stated; `dispatched.tool_call_id == call.id`; `record.error == code`; every executor double `.calls == []`; `retryable is True` only for `bad_arguments` |
| AC-3 | Every call answered in order; never raises; exception → `tool_failed`, retryable False; log names type only; content ≤ 4,000 | `test_dispatch.py::test_every_call_answered_in_order` | Calls `[c1 kb_search ok, c2 no_such_tool, c3 boom (executor raises Boom with a message holding a run-time card-like value), c4 kb_search ok]` → 4 results; `[d.tool_call_id for d in out] == ["c1","c2","c3","c4"]`; c3 content `error.code == "tool_failed"`, `retryable is False`, `record.outcome == "failed"`; exactly one caplog record whose message starts `"tool_failed "` and contains `"Boom"` and not the card-like value; every `len(d.content) <= 4000`; `dispatch([], …) == ()`. A second sub-check: an executor returning the string `"not a ToolResult"` → `tool_failed` |
| AC-3 / S-4 | Oversized result becomes truncated valid JSON | `test_dispatch.py::test_oversized_result_is_truncated_json` | Executor `for_model = {"text": "x" * 10_000}` → `len(content) <= 4000`; `json.loads(content)["truncated"] is True`; `record.outcome == "ok"`; one caplog record starting `"tool_result_truncated "` |
| S-10 | Unrenderable result → `tool_failed`, still one row | `test_dispatch.py::test_unrenderable_result_is_tool_failed` (parametrised, ids `read`, `service_written_write`) | Executor double with `unrenderable=True` (§6). `read` (`kb_search`, KB_SEARCH, effect read): content `error.code == "tool_failed"`; `record.outcome == "failed"`; exactly one appended entry, `result_seen == "failed"`, empty ids; `record.lookup_id` == that append's id. `service_written_write` (`book_slot`, BOOK, effect write, verified scope, `lookup_written=True`; the double writes its own row through the same `RecordingUow`): content `error.code == "tool_failed"`; `record.outcome == "failed"`; `len(uow.appended) == 1` (the double's own row only); `record.lookup_id is None`; `record.record_ids` == the double's entry's. Both: exactly one caplog record whose message starts `"tool_failed "` and contains `"error_type=bad_result"` |
| AC-4 | Schemas generated from `args_model`, trimmed, strict, no scope field, filtered by kind, ordered by name, cached | `test_dispatch.py::test_schemas_generated_without_scope_fields` | Registry `{b_read (ACCOUNT_READ, InvoiceArgs), a_read (ACCOUNT_READ, TitledArgs), kb_search (KB_SEARCH, KbArgs)}`. `s = d.schemas(frozenset({ToolKind.ACCOUNT_READ}))`: `[x.name for x in s] == ["a_read", "b_read"]`; each `x.strict is True`; `x.description == def.description`; `x.input_schema == strip_titles(def.args_model.model_json_schema())` (helper in `dispatch_doubles.py`, same rule as §5 step 2.2); `TitledArgs` keeps its property named `title`; no property name anywhere in `x.input_schema` is in `ToolCallScope.model_fields`; `d.schemas(frozenset({ToolKind.ACCOUNT_READ})) is s` (a new, equal frozenset returns the same object); `d.schemas(frozenset({ToolKind.KB_SEARCH}))` holds only `kb_search` |
| AC-5 | Registry start-up checks | `test_registry.py::test_registry_rejects_bad_defs` (parametrised) | `ToolRegistry(defs)` raises `ValueError` for: duplicate `kb_search`; names `""`, `"Read"`, `"read-invoices"`, `"read invoices"`, `"r1"`, `"a" * 65`. `ToolRegistry([kb]).check_covers(frozenset({ToolKind.BOOK}))` raises `ValueError`; `check_covers(frozenset({ToolKind.KB_SEARCH}))` returns `None`. A registry that built fine never raises from `dispatch` (one call each of ok / unknown) |
| S-1, S-2 | Plan-added start-up checks | `test_registry.py::test_registry_rejects_scope_fields_and_open_private_kinds` (parametrised) | `ValueError` for an `args_model` with a field named `customer_id`, one named `message_id`, and one nesting a model with a field `shown_slot_ids`; `ValueError` for each of ACCOUNT_READ, BOOK, MOVE, CANCEL, CHANGE_REQUEST with `requires_verified=False`; **no** error for KB_SEARCH or SLOT_SEARCH with `requires_verified=False` |
| Registry API | `get`, `for_kinds` | `test_registry.py::test_registry_get_and_for_kinds` | `get("kb_search") is kb_def`; `get("nope") is None`; `for_kinds` returns defs of those kinds sorted by name; `for_kinds(frozenset())` == `()` |
| AC-6 | One `lookup_log` row per call; executed reads by dispatch in their own `uow(write=True)`; write with `lookup_written=True` not written twice; refused/failed rows built by dispatch; `message_id`/`turn_id` from scope; `lookup_id` = row id | `test_dispatch.py::test_one_lookup_row_per_call` | Verified scope. Calls `[r1 kb_search ok, r2 no_such_tool, r3 boom raises, r4 book_slot (BOOK, effect write) whose executor double writes its own row through the **same** `RecordingUow` and returns `lookup_written=True`]` → `len(uow.appended) == 4 == len(calls)`; exactly one appended entry with `tool == "book_slot"`; r2's entry `result_seen == "refused:unknown_tool"`, ids empty; r3's `== "failed"`, ids empty; every entry `message_id == 41` and `turn_id == scope.ids.turn_id` (the executor doubles put `message_id=0` and a different `turn_id` in their own entries, so stamping is proven for r1); r1/r2/r3 `record.lookup_id` equal the ids the double returned for those appends; r4 `record.lookup_id is None` (S-8) |
| AC-7 | Failed lookup write logged; `lookup_id None`; content unchanged; other rows written | `test_dispatch.py::test_lookup_write_failure_does_not_change_result` | Baseline: call A (`kb_search`) with a healthy uow → content `X`. Then `RecordingUow(fail_on_appends={1})` (1st append raises `sqlite3.OperationalError` whose message holds a run-time card-like value), calls `[A, B]` → A content `== X`; A `record.lookup_id is None`; B row appended and B `record.lookup_id` is its id; exactly one caplog record starting `"lookup_write_failed "` containing `"OperationalError"`, not containing the card-like value |
| AC-8 | `ToolCallRecord` per call | `test_dispatch.py::test_tool_call_records` (parametrised) | `ok`: outcome `ok`, error `None`, kind set, `record_ids`/`passage_ids` == the executor entry's (`("INV-204411",)`, `(PassageId("faq/x.md#3"),)`); `guard_refused`: outcome `refused`, error `not_verified`; `executor_refused` (executor returns `ToolError(code=not_shown)`): outcome `refused`, error `not_shown`, row = executor's entry; `executor_tool_failed` (executor returns `ToolError(code=tool_failed)`): outcome `failed`; `raised`: outcome `failed`, error `tool_failed`; `unknown_long_name` (name = `"z" * 100`): `kind is None`, `name == "z" * 64`, outcome `refused`, error `unknown_tool`. All: `isinstance(elapsed_ms, int) and elapsed_ms >= 0`; error is `None` exactly when outcome is `ok` |
| AC-9 | Rejected and private values absent; `result_seen` no free text > 80, no card-like number or code | `test_dispatch.py::test_rejected_values_absent` | Values built at run time by `dispatch_doubles` makers (`foreign_customer_id()`, `full_phone()`, `card_like()`, `six_digit_code()`), never literals, never in test names. Cases: (a) unknown tool, args hold all four values; (b) `read_invoices` args `{"customer_id": foreign, <full_phone>: "x", "invoice_number": card_like}` → `bad_arguments`, message contains `"invoice_number: "` and `"unexpected_field: extra_forbidden"`; (c) executor raises with all four values in its message; (d) `kb_search` executed, executor's entry `result_seen` = `f"ok {card_like} {code}"` → stored `result_seen` contains neither (STORE). For every case: none of the four values in `ToolError.message`, `d.content`, `d.model_dump_json()` (covers result, lookup and record), any appended entry's `model_dump_json()`, `caplog.text`, any `record.getMessage()`; dispatch-built `result_seen` values are exactly `refused:<code>` or `failed` (≤ 80 chars). (e) unknown tool **name** holding `six_digit_code()` → record `name` and row `tool` do not contain it (S-5) |
| AC-10 | Scope comes from code | `test_dispatch.py::test_scope_bound_by_code` | `NoteArgs(note: str)` tool (ACCOUNT_READ, requires True); verified scope `customer_id=MHC-10002`; args `{"note": f"use {foreign_customer_id()} instead"}` → executor's received scope `is` the passed scope and `.customer_id == "MHC-10002"` |
| AC-11 | No unit of work open while an executor runs | `test_dispatch.py::test_lookup_write_outside_executor` | Two `kb_search` calls `a`, `b` sharing one `Recorder`: `recorder.events == ["execute:a", "enter:write", "append", "commit", "exit", "execute:b", "enter:write", "append", "commit", "exit"]`; each executor double recorded `uow.depth == 0` at call time |
| S-7 | Import direction | `test_dispatch.py::test_dispatch_imports_no_adapters` | `ast` walk of `src/meridian/agent/tools/dispatch.py`: no import starting with `meridian.adapters`, `meridian.services`, `meridian.web`, `meridian.agent.specialists`, `sqlite3`, `anthropic`, `httpx`, `langfuse`, `fastembed` |
| AC-12 | `[journey]` runs no journey yet; record at `mock-tested` | the record + `uv run python -m tests.journeys.affected --base main --list-only` | Prints `0 journeys affected`; record Level `mock-tested`, Blocked by AEA-57 (and AEA-51), journeys J-2, J-3 |
| AC-13 | Context reconciled | `git diff --name-only main...HEAD` | Shows the four context paths + the journey record |

**Red for the right reason (test-writer).** Every test module imports the module under test through a fixture, the AEA-04
pattern, so the files collect before `dispatch.py` exists:

```python
@pytest.fixture(scope="module")
def dispatch() -> ModuleType:
    return importlib.import_module("meridian.agent.tools.dispatch")
```

Before the implementation each test errors with `ModuleNotFoundError: No module named 'meridian.agent.tools.dispatch'`.
`dispatch_doubles.py` must **not** import `meridian.agent.tools.dispatch` (so it imports cleanly). Collect-only proof:
`uv run pytest --collect-only -q tests/unit/agent/tools` exits 0.

---

## 4. Shared code to use (exact imports; verify they resolve before writing code, §5 step 0)

### 4.1 Imports for `dispatch.py`

```python
from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final, Literal, Protocol, cast

from pydantic import JsonValue, ValidationError

from meridian.domain.common import LLMFacing, MeridianModel, ToolErrorCode
from meridian.domain.tools import (
    LookupEntry, ToolCallRecord, ToolCallScope, ToolDef, ToolError, ToolKind, ToolResult,
)
from meridian.ports.models import ToolCall, ToolSchema
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.privacy.redact import RedactionProfile, redact
```

Homes (AEA-02 plan §4 table): `ToolKind` and `ToolCallRecord` are defined in `domain/common.py` and re-exported from
`domain/tools.py`; import them from `domain/tools.py`. `ToolErrorCode`, `LLMFacing`, `MeridianModel` from
`domain/common.py`. `ToolCall`, `ToolSchema` from `ports/models.py`. `UnitOfWorkFactory` from `ports/runtime.py`.

### 4.2 Types consumed (copied from AEA-02 plan §4.1, §4.9, §4.12; graph-tools §1; DO-4 §5)

```python
class ToolErrorCode(StrEnum):   # 13 values
    NOT_ALLOWED = "not_allowed"; BAD_ARGUMENTS = "bad_arguments"; UNKNOWN_TOOL = "unknown_tool"
    NOT_VERIFIED = "not_verified"; NOT_SHOWN = "not_shown"; FEE_BEARING = "fee_bearing"
    OUTSIDE_SERVICE_AREA = "outside_service_area"; SLOT_TAKEN = "slot_taken"; BOOKING_CAP = "booking_cap"
    IDENTICAL_CALL = "identical_call"; TOOL_FAILED = "tool_failed"
    WRONG_SERVICE_TYPE = "wrong_service_type"; NOT_OWNED = "not_owned"

class ToolKind(StrEnum):        # 7 values
    KB_SEARCH = "kb_search"; ACCOUNT_READ = "account_read"; SLOT_SEARCH = "slot_search"
    BOOK = "book"; MOVE = "move"; CANCEL = "cancel"; CHANGE_REQUEST = "change_request"

class ToolCallRecord(MeridianModel):
    tool_call_id: str
    name: str = Field(max_length=64)
    kind: ToolKind | None
    outcome: Literal["ok", "refused", "failed"]
    error: ToolErrorCode | None
    record_ids: tuple[str, ...]
    passage_ids: tuple[PassageId, ...]
    lookup_id: int | None
    elapsed_ms: int

class ToolCallScope(MeridianModel):
    ids: TurnIds                      # TurnIds: thread_id, turn_id, request_id, run_tag, run_id, agent_version
    customer_id: CustomerId | None
    shown_slot_ids: frozenset[int]
    now: dt.datetime
    message_id: int

class LookupEntry(MeridianModel):
    tool: str; record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]
    result_seen: str; message_id: int; turn_id: TurnId

class ToolError(MeridianModel):      code: ToolErrorCode; message: str; retryable: bool

class ToolResult(MeridianModel):
    ok: bool
    for_model: ToolError | JsonValue = Field(union_mode="left_to_right")
    captured: Capture | None
    lookup: LookupEntry
    lookup_written: bool

class ToolDef(MeridianModel):
    name: str; description: str
    args_model: type[LLMFacing]
    kind: ToolKind
    effect: Literal["read", "write"]
    requires_verified: bool
    executor: Callable[[LLMFacing, ToolCallScope], ToolResult] = Field(exclude=True)

class ToolSchema(MeridianModel):  name: str; description: str; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolCall(MeridianModel):    id: str; name: str; args: dict[str, JsonValue] | None

class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
# UnitOfWork: core: CoreRepos; …; def commit(self) -> None  (AEA-02 shell: CoreRepos has only __init__(conn))
```

`MeridianModel` config: `extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True`.

### 4.3 What this slice produces (graph-tools §1, exact)

```python
class ToolRegistry:
    def __init__(self, defs: Iterable[ToolDef]) -> None: ...
    def get(self, name: str) -> ToolDef | None: ...
    def for_kinds(self, kinds: frozenset[ToolKind]) -> tuple[ToolDef, ...]: ...   # stable order: by name
    def check_covers(self, kinds: frozenset[ToolKind]) -> None: ...

class DispatchedCall(MeridianModel):
    tool_call_id: str
    content: str                     # JSON text the model receives, ≤ 4,000 chars
    result: ToolResult               # ToolError inside for_model on refusal
    record: ToolCallRecord

class ToolDispatcher:
    def __init__(self, registry: ToolRegistry, uow: UnitOfWorkFactory) -> None: ...
    def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]: ...
    def dispatch(self, calls: Sequence[ToolCall], *, kinds: frozenset[ToolKind],
                 scope: ToolCallScope) -> tuple[DispatchedCall, ...]: ...
```

No other public name. `__all__ = ["MAX_CONTENT_CHARS", "DispatchedCall", "ToolDispatcher", "ToolRegistry"]`.

### 4.4 Storage call (DO-4 §13; cases.md §1.2; AEA-10 body, same wave)

`tx.core.lookup_log.append(entry: LookupEntry) -> int` inside `with uow(write=True) as tx:` followed by `tx.commit()`.
The unit of work rolls back unless `commit()` was called, and an exception inside rolls back and propagates
(cases.md §1.0). AEA-02's `CoreRepos` shell has no `lookup_log` attribute until AEA-10 merges, so reach it through a
**private structural type** (allowed by DO-4 §0: "a builder may add a private helper"):

```python
class _LookupLogAppend(Protocol):
    def append(self, entry: LookupEntry) -> int: ...

class _HasLookupLog(Protocol):
    lookup_log: _LookupLogAppend

def _append_lookup(uow: UnitOfWorkFactory, entry: LookupEntry) -> int:
    # CoreRepos.lookup_log is AEA-10's (cases.md §1.2); typed structurally so this module builds before it lands.
    with uow(write=True) as tx:
        row_id = cast(_HasLookupLog, tx.core).lookup_log.append(entry)
        tx.commit()
    return row_id
```

### 4.5 Redaction (AEA-04, built)

`redact(text: str, profile: RedactionProfile) -> Redacted`; use `redact(x, RedactionProfile.STORE).text`. STORE replaces
card-like numbers (`[card number removed]`) and standalone six-digit codes (`[code]`) only; it leaves `INV-204411`,
`MHC-10002`, dates and amounts alone.

---

## 5. Steps

Work in your worktree (for example `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-22`, branch
`aea-22-tool-dispatch`), created from `main` **after** AEA-02 is merged (AEA-01 and AEA-04 already are). `export UV_LINK_MODE=hardlink`
in every shell. Never copy a venv; no `node_modules`.

**Step 0 — preflight (import check, no suite).**
`uv sync` then:
```
uv run python -c "from meridian.domain.tools import ToolDef, ToolCallScope, LookupEntry, ToolError, ToolResult, ToolKind, ToolCallRecord; from meridian.domain.common import ToolErrorCode, LLMFacing, MeridianModel; from meridian.ports.models import ToolCall, ToolSchema; from meridian.ports.runtime import UnitOfWorkFactory; from meridian.privacy.redact import redact, RedactionProfile; print('ok')"
```
Prints `ok`. If any name fails to import, **stop and report BLOCKED-ON AEA-02 / AEA-04**; never add or patch a type in
`domain/`, `ports/` or `privacy/`. Then confirm the frozen tests are present and red for the right reason:
`uv run pytest tests/unit/agent/tools -q` → every test errors with `ModuleNotFoundError … meridian.agent.tools.dispatch`.

**Step 1 — module header** in `src/meridian/agent/tools/dispatch.py`: docstring (one paragraph: what it does; cite
graph-tools §1 GRT-1, DO-4 §5), the imports of §4.1, then:

```python
_log = logging.getLogger(__name__)                    # "meridian.agent.tools.dispatch"
MAX_CONTENT_CHARS: Final = 4_000                       # DO-4 §5: what the model sees, rendered
_NAME_RE: Final = re.compile(r"[a-z_]{1,64}")          # used with fullmatch
_MUST_VERIFY: Final = frozenset({ToolKind.ACCOUNT_READ, ToolKind.BOOK, ToolKind.MOVE,
                                 ToolKind.CANCEL, ToolKind.CHANGE_REQUEST})   # R-14 (S-2)
_SCOPE_FIELDS: Final = frozenset(ToolCallScope.model_fields)  # ids, customer_id, shown_slot_ids, now, message_id
_NO_RECURSE: Final = frozenset({"default", "examples", "const", "enum"})
_MESSAGES: Final[Mapping[ToolErrorCode, str]] = {
    ToolErrorCode.UNKNOWN_TOOL: "No tool with that name is available. Use only the tools you were given.",
    ToolErrorCode.NOT_ALLOWED: "That tool is not available for this task.",
    ToolErrorCode.BAD_ARGUMENTS: "The arguments did not match the tool's input schema.",
    ToolErrorCode.NOT_VERIFIED: ("The customer has not been verified yet. Account tools work only after the "
                                 "one-time code is entered."),
    ToolErrorCode.TOOL_FAILED: "The tool could not complete this request.",
}
```
Wrap `_MESSAGES` in `types.MappingProxyType` (immutable module constant; AEA-02 convention 6). Use these five strings
exactly; no test asserts their wording (tests assert codes, `retryable`, and the absence of values).

**Step 2 — private helpers** (module-level functions; each has one job).

2.1 `_elapsed_ms(t0: float) -> int`: `max(0, int((time.perf_counter() - t0) * 1000))`.

2.2 `_trimmed_schema(args_model: type[LLMFacing]) -> dict[str, JsonValue]`: `raw = args_model.model_json_schema()`; return
`cast(dict[str, JsonValue], _strip_titles(raw))`. `_strip_titles(node: Any) -> Any`:
- dict → new dict; for each `(key, value)`: skip when `key == "title" and isinstance(value, str)`; when `key` is
  `"properties"` or `"$defs"` and `value` is a dict → `{name: _strip_titles(sub) for name, sub in value.items()}`
  (property and definition **names** are kept, so a field named `title` survives); when `key in _NO_RECURSE` → copy
  `value` unchanged; else `_strip_titles(value)`.
- list → `[_strip_titles(v) for v in node]`; anything else → unchanged.
*Invariant:* the result differs from `model_json_schema()` only by removed schema-level `title` strings, so the schema
stays generated from the model (agent-tools rule 3). `additionalProperties: false` (from `extra="forbid"`) stays.

2.3 `_property_names(schema: Any) -> set[str]`: every key of every `"properties"` dict at any depth (walk dicts and
lists). `_unknown_name(name: str) -> str`: `redact(name, RedactionProfile.STORE).text[:64]` (redact **then** cut; S-5).

2.4 `_bad_args_message(exc: ValidationError | None, args_model: type[LLMFacing]) -> str`:
- `exc is None` (the provider's arguments did not parse): `_MESSAGES[BAD_ARGUMENTS] + " The arguments could not be read as JSON."`
- else, for the first 5 entries of `exc.errors(include_url=False, include_context=False, include_input=False)`:
  `first = err["loc"][0] if err["loc"] else ""`; `field = first` when `isinstance(first, str) and first in
  args_model.model_fields`, else `"unexpected_field"` when `err["type"] == "extra_forbidden"`, else `"arguments"`;
  part = `f"{field}: {err['type']}"`. Message = `_MESSAGES[BAD_ARGUMENTS] + " Problems: " + "; ".join(parts) + "."`
*Invariant (safe-validation-errors 1–2):* only declared field names and pydantic/our stable error types appear; never
`err["msg"]`, never `err["input"]`, never a key the model invented.

2.5 `_stamped(entry: LookupEntry, tool: str, scope: ToolCallScope) -> LookupEntry`: a **new** `LookupEntry(tool=tool,
record_ids=entry.record_ids, passage_ids=entry.passage_ids, result_seen=redact(entry.result_seen,
RedactionProfile.STORE).text, message_id=scope.message_id, turn_id=scope.ids.turn_id)`. *Invariant:* every row dispatch
writes carries the scope's ids and no card-like number or code (AC-6, AC-9, S-6).

2.6 `_render(for_model: ToolError | JsonValue) -> tuple[str, int]` (content, length of the untruncated JSON text;
truncated exactly when that length > `MAX_CONTENT_CHARS`):
- `ToolError` → `json.dumps({"error": for_model.model_dump(mode="json")}, ensure_ascii=False, separators=(",", ":"))`
  (decoded shape: `{"error": {"code": "...", "message": "...", "retryable": false}}`);
- otherwise `json.dumps(for_model, ensure_ascii=False, separators=(",", ":"))`.
- `_render` may raise (`TypeError` / `ValueError` from `json.dumps` when an executor built its result without
  validation, e.g. `ToolResult.model_construct`); it does not catch that itself: step 5.7 does.
- If `len(text) <= MAX_CONTENT_CHARS` → `(text, len(text))`. Else (S-4): `keep = MAX_CONTENT_CHARS - 64`; loop: `candidate =
  json.dumps({"truncated": True, "partial": text[:keep]}, ensure_ascii=False, separators=(",", ":"))`; if
  `len(candidate) <= MAX_CONTENT_CHARS` return `(candidate, len(text))`; else `keep = max(0, keep - (len(candidate) -
  MAX_CONTENT_CHARS))`. *Invariant:* content is always valid JSON and ≤ 4,000 chars.

2.7 `_append_lookup` exactly as §4.4, and the method `ToolDispatcher._write_lookup(self, entry, log_tool: str, scope) ->
int | None`: `try: return _append_lookup(self._uow, entry)` / `except Exception as exc:` →
`_log.error("lookup_write_failed tool=%s error_type=%s turn_id=%s", log_tool, type(exc).__name__, scope.ids.turn_id)`;
`return None`. *Invariant (AC-7):* a storage failure changes nothing the model receives and never raises.

**Step 3 — `ToolRegistry`.** Constructor, in this order; every failure is `ValueError` at construction (start-up):
1. `defs = tuple(defs)`; `self._by_name: dict[str, ToolDef] = {}`.
2. For each `d`: `_NAME_RE.fullmatch(d.name)` else `ValueError(f"tool name must match [a-z_]{{1,64}}: {d.name!r}")`
   (names come from our code, so naming them is safe).
3. `d.name in self._by_name` → `ValueError(f"duplicate tool name: {d.name}")`.
4. S-2: `d.kind in _MUST_VERIFY and not d.requires_verified` → `ValueError(f"tool {d.name}: kind {d.kind.value} must
   set requires_verified (R-14)")`.
5. S-1: `try: schema = _trimmed_schema(d.args_model)` / `except Exception as exc: raise ValueError(f"tool {d.name}:
   args_model has no JSON schema") from exc`; `bad = _property_names(schema) & _SCOPE_FIELDS`; if `bad` →
   `ValueError(f"tool {d.name}: arguments may not include scope fields: {', '.join(sorted(bad))}")`.
6. `self._by_name[d.name] = d`. After the loop: `self._kinds = frozenset(d.kind for d in defs)`.

`get(name)` → `self._by_name.get(name)`. `for_kinds(kinds)` → `tuple(sorted((d for d in self._by_name.values() if d.kind
in kinds), key=lambda d: d.name))`. `check_covers(kinds)`: `missing = sorted(k.value for k in kinds if k not in
self._kinds)`; if `missing` → `ValueError("no tool registered for kinds: " + ", ".join(missing))`.

**Step 4 — `DispatchedCall` and `ToolDispatcher.__init__` / `schemas`.** `DispatchedCall(MeridianModel)` with the four
fields of §4.3 (plain `content: str`; no `Field(max_length=…)`, because a validator that raises would break "never
raises"; the bound is enforced by `_render`). `__init__` stores `self._registry`, `self._uow`, `self._schema_cache:
dict[frozenset[ToolKind], tuple[ToolSchema, ...]] = {}`, `self._lock = threading.Lock()`. `schemas(kinds)`: `key =
frozenset(kinds)`; under `self._lock`: return the cached tuple if present, else build `tuple(ToolSchema(name=d.name,
description=d.description, input_schema=_trimmed_schema(d.args_model), strict=True) for d in
self._registry.for_kinds(key))`, store, return. *Invariant:* the same kind set always returns the same tuple object
(AC-4); the cache is safe across request threads.
Do **not** mark `ToolRegistry`, `ToolDispatcher` or any of their methods `@final`, and add no `__slots__`: AEA-35's
`ScriptedDispatcher(ToolDispatcher)` overrides `schemas` and `dispatch` and never calls `super().__init__` (its plan,
*Doubles*). So nothing outside `__init__`, `schemas`, `dispatch` and the private methods they call may rely on an
attribute (no `__init_subclass__`, no class-level registry, no property that reads `self._uow` on its own).

**Step 5 — `ToolDispatcher.dispatch` and its per-call path.** `dispatch` returns `tuple(self._dispatch_one(c, kinds,
scope) for c in calls)` (empty `calls` → `()`). No unit of work is opened in `dispatch` itself.

`_dispatch_one(call, kinds, scope) -> DispatchedCall`: `t0 = time.perf_counter()`; `try: return self._run(call, kinds,
scope, t0)` / `except Exception as exc:` (last resort; a bug in dispatch must still answer the call) →
`defn = self._registry.get(call.name)` (a dict lookup; cannot raise), then
`_log.error("dispatch_internal_error tool=%s error_type=%s turn_id=%s", defn.name if defn else "unknown",
type(exc).__name__, scope.ids.turn_id)` and `return self._refuse(call, defn, ToolErrorCode.TOOL_FAILED, scope, t0)`.

`_run(call, kinds, scope, t0)`, in this order (each refusal returns at once; nothing below it runs):
1. `defn = self._registry.get(call.name)`.
2. `defn is None` → `self._refuse(call, None, UNKNOWN_TOOL, scope, t0)`.
3. `defn.kind not in kinds` → `NOT_ALLOWED`.
4. `call.args is None` → `BAD_ARGUMENTS` with message `_bad_args_message(None, defn.args_model)`. Else
   `try: args = defn.args_model.model_validate(call.args)` / `except ValidationError as exc:` → `BAD_ARGUMENTS` with
   `_bad_args_message(exc, defn.args_model)` / `except Exception as exc:` (a validator bug, not the model's fault) →
   log `tool_failed` (below) and `TOOL_FAILED`.
5. `defn.requires_verified and scope.customer_id is None` → `NOT_VERIFIED`.
6. Execute **with no unit of work open**: `try: result = defn.executor(args, scope)` — pass the **same** `scope` object
   the caller gave (AC-10) — `except Exception as exc:` →
   `_log.warning("tool_failed tool=%s error_type=%s turn_id=%s", defn.name, type(exc).__name__, scope.ids.turn_id)`
   and `TOOL_FAILED`. If `not isinstance(result, ToolResult)` → same log line with `error_type="bad_result"` and
   `TOOL_FAILED` (S-9). Never log `str(exc)`, `repr(exc)`, `exc_info` or the arguments.
7. Render **before** any row is written (S-10): `service_wrote = defn.effect == "write" and result.lookup_written`.
   `try: content, full_len = _render(result.for_model)` / `except Exception:` →
   `_log.warning("tool_failed tool=%s error_type=bad_result turn_id=%s", defn.name, scope.ids.turn_id)` and
   `return self._refuse(call, defn, ToolErrorCode.TOOL_FAILED, scope, t0, existing=result.lookup if service_wrote else
   None)`. If `full_len > MAX_CONTENT_CHARS` →
   `_log.warning("tool_result_truncated tool=%s chars=%d turn_id=%s", defn.name, full_len, scope.ids.turn_id)`.
8. Lookup row, **after** the executor returned (AC-11): if `service_wrote` → `stored = result.lookup`, `lookup_id = None`
   (the scheduling service wrote it in the booking's transaction; S-8). Otherwise `stored = _stamped(result.lookup,
   defn.name, scope)` and `lookup_id = self._write_lookup(stored, defn.name, scope)`. *Invariant:* after this write
   nothing runs except building the two models in step 9 from values that are already validated, so the last-resort
   handler in `_dispatch_one` cannot add a second row for a call whose row is already written.
9. Outcome: `for_model` is a `ToolError` with code `TOOL_FAILED` → `("failed", TOOL_FAILED)`; any other `ToolError` →
   `("refused", its code)`; otherwise `("ok", None)`. Record: `ToolCallRecord(tool_call_id=call.id, name=defn.name,
   kind=defn.kind, outcome=…, error=…, record_ids=stored.record_ids, passage_ids=stored.passage_ids,
   lookup_id=lookup_id, elapsed_ms=_elapsed_ms(t0))`. Return `DispatchedCall(tool_call_id=call.id, content=content,
   result=result.model_copy(update={"lookup": stored}), record=record)`.

`_refuse(call, defn: ToolDef | None, code: ToolErrorCode, scope, t0, *, message: str | None = None, existing: LookupEntry | None = None) -> DispatchedCall`:
1. `name = defn.name if defn is not None else _unknown_name(call.name)`; `log_tool = defn.name if defn else "unknown"`.
2. Unless `code is TOOL_FAILED` (already logged by the caller): `_log.info("tool_refused tool=%s code=%s turn_id=%s",
   log_tool, code.value, scope.ids.turn_id)`.
3. `err = ToolError(code=code, message=message or _MESSAGES[code], retryable=(code is ToolErrorCode.BAD_ARGUMENTS))`.
4. If `existing is not None` (only from step 7, for a service-written write whose result could not be rendered):
   `entry = existing`, `lookup_id = None`, and **no** row is written (the service already wrote this call's one row).
   Otherwise `entry = LookupEntry(tool=name, record_ids=(), passage_ids=(), result_seen=("failed" if code is
   TOOL_FAILED else f"refused:{code.value}"), message_id=scope.message_id, turn_id=scope.ids.turn_id)` and
   `lookup_id = self._write_lookup(entry, log_tool, scope)`.
5. `content, _ = _render(err)` (a `ToolError` always renders); record with `kind = defn.kind if defn else None`,
   `outcome = "failed" if code is TOOL_FAILED else "refused"`, `error = code`, `record_ids=entry.record_ids`,
   `passage_ids=entry.passage_ids` (empty for a dispatch-built entry), `lookup_id`, `_elapsed_ms(t0)`.
6. `result = ToolResult(ok=False, for_model=err, captured=None, lookup=entry, lookup_written=False)`; return the
   `DispatchedCall`.

*Invariants of step 5:* exactly one row per call (refused and failed calls write in `_refuse`; executed calls in step 8;
service-written writes skipped); a refused call never reaches `defn.executor`; no `uow(...)` block encloses an executor
call; nothing raised escapes `dispatch`.

**Step 6 — iterate to green.** `uv run pytest tests/unit/agent/tools -q`. If a frozen test looks wrong, **do not edit it**;
stop and report the test name and why (it goes back to the test-writer / orchestrator).

**Step 7 — fast gates, then commit the code.** Cheapest first (§7). Commit with explicit paths:
`git add src/meridian/agent/tools/dispatch.py` → message
`feat(agent): tool dispatch, verified guard and lookup log (AEA-22)` + blank line + body (one line per AC group) +
blank line + `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` as the **last** line. (The frozen tests were
committed by the test-writer; never `git add -A`.)

**Step 8 — context, record, dev log (AC-12, AC-13); second commit.** Use the code commit's short SHA as `<sha>`.
1. `.claude/reference/area-map.md`, A7b row, *Owns* cell: replace `` `agent/tools/dispatch.py` `` with
   `` `agent/tools/dispatch.py` (**actual**, AEA-22 `<sha>`; built in ticket wave 1, ahead of A7b's area wave 3) ``.
   Change nothing else in the file (the row's Status stays `planned`: its other files are unbuilt).
2. `docs/design/code-design.md` §3 tree: on the line `│   ├── tools/dispatch.py                        schemas from
   ToolDef; guard; every branch; lookup-log rows  A7b   3`, append `   built AEA-22 <sha> (ticket wave 1)`.
3. `docs/design/contracts/internal-components.md`: directly under `## 5. Specialist contracts`, before the existing
   `> Superseded at Stage 7:` note, add one line:
   `> Stage 7: the dispatcher's public API and executor registration (`ToolRegistry`, `ToolDispatcher.schemas` / `dispatch`, `DispatchedCall`, `ToolCallRecord`) are defined in [stage7/graph-tools.md](stage7/graph-tools.md) §1 (GRT-1); built by AEA-22 in `agent/tools/dispatch.py`.`
   followed by a blank line.
4. `.claude/state/icm-progress.md`: directly below the **last** existing row named *Routes verified against code and
   tests* (main has two, AEA-04's and AEA-03's), insert one new row (≤ 400 chars), exactly:
   `| Routes verified against code and tests | provisional | <date>: area map A7b → `agent/tools/dispatch.py` checked against `tests/unit/agent/tools/` (AEA-22, `<sha>`; <N> pass) | Each slice adds its route; verified when every area-map row is actual |`
   Edit no existing row. Then change the line `Last reconciled: 2026-10-21 — AEA-01 scaffold (scaffold row); earlier, …`
   to `Last reconciled: <date> — AEA-22 dispatch built (routes row); earlier, AEA-01 scaffold (scaffold row); earlier, …`
   (insert the new lead clause; keep everything after it unchanged). If another slice changed the lead first, insert
   the same clause in front of whatever lead is there.
5. `docs/testing/journeys/<date>-AEA-22.md` with the §4 table of `integrated-journeys.md`:
   - Claim: AEA-22 `agent/tools/dispatch.py` (guard, guard order, one lookup row per call, safe errors) per AC-1…AC-11. No journey run.
   - Level: `mock-tested`
   - Tested revision: `<sha>`
   - Environment: VPS, Python 3.12, no server, no DB (a recording `UnitOfWorkFactory` double), executor doubles, no model
   - Command: `uv run pytest tests/unit/agent/tools -q -rP` and `uv run python -m tests.journeys.affected --base main --list-only`
   - Result: `<N> passed`; affected command printed `0 journeys affected`
   - Evidence location: GitLab issue #22 comment; this file
   - Remaining limitations: real `LookupLogRepo` (AEA-10) and real executors (AEA-27, 28, 33) not exercised; `lookup_id` is `None` for service-written rows (S-8); executor snapshot free-text length is the executors' contract
   - Blocked by: AEA-57 (journey harness, wave 2); AEA-51 (graph wiring, wave 3)
   - Journeys that will exercise this code: J-2 (account read before and after the code: the verified guard, `lookup_log` rows) and J-3 (booking: the write tool's single row), once AEA-57 and AEA-51 land (pattern C, `docs/plans/ux-join/backend-amendments.md` §3)
6. Commit: `git add .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md
   docs/design/contracts/internal-components.md docs/testing/journeys/<date>-AEA-22.md` → message
   `docs(AEA-22): journey record and context for agent/tools/dispatch.py` + blank line +
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
7. Dev log (outside this repo; not committed from here): create
   `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<date>-aea-22-tool-dispatch-claude-01.md` per
   `.claude/reference/dev-log.md`: header (project, date America/Chicago, topic, writer `fanout-implementer` on the model
   that actually ran, VPS, branch and base), one entry with **Changed / Why / Checked / Remaining** (50–100 words; name
   S-8 and the AEA-10 cast as Remaining).

**Step 9 — report.** Per AC: the test or command and its result; the two commit SHAs; the fast-gate output; the
`git diff --name-only main...HEAD` list (must equal the owned repo files of §2.1).

---

## 6. Data and fixtures (synthetic; source named)

All doubles live in `tests/unit/agent/tools/dispatch_doubles.py` (test-writer). It imports domain and port types only,
never `meridian.agent.tools.dispatch`. Types for mypy: pass doubles to typed parameters with
`cast(UnitOfWorkFactory, uow)`; executor doubles define `__call__(self, args: LLMFacing, scope: ToolCallScope) -> ToolResult`.

| Name | What it is | Source |
|---|---|---|
| `THREAD`, `TURN`, `REQUEST` | Fixed lower-case UUID4 strings, e.g. `"3f0c2a4e-8b1d-4c2e-9a6f-1b2c3d4e5f60"` (v4 pattern) | synthetic |
| `make_ids()` | `TurnIds(thread_id=ThreadId(THREAD), turn_id=TurnId(TURN), request_id=RequestId(REQUEST), run_tag="live", run_id=None, agent_version="dev")` | AEA-02 §4 `TurnIds` |
| `make_scope(customer_id: str | None)` | `ToolCallScope(ids=make_ids(), customer_id=CustomerId(customer_id) if customer_id else None, shown_slot_ids=frozenset(), now=datetime(2026, 10, 15, 9, 0, tzinfo=ZoneInfo("America/Chicago")), message_id=41)` | synthetic; `message_id` 41 is distinctive |
| `OTHER_TURN` | A second UUID4 string; executor doubles put `turn_id=TurnId(OTHER_TURN)`, `message_id=0` in their own entries (proves stamping) | synthetic |
| `EmptyArgs(LLMFacing)` | no fields | test-local |
| `KbArgs(LLMFacing)` | `query: str = Field(min_length=1, max_length=300)` | mirrors data.md §4 `KbSearchArgs` |
| `InvoiceArgs(LLMFacing)` | `invoice_number: InvoiceId | None = None` | mirrors graph-tools §4 `ReadInvoicesArgs` |
| `TitledArgs(LLMFacing)` | `title: str` | edge case for `_strip_titles` |
| `NoteArgs(LLMFacing)` | `note: str` | AC-10 |
| `ScopeLeakArgs` etc. | for S-1: one model with `customer_id: str`, one with `message_id: int`, one with `inner: Inner` where `Inner(LLMFacing)` has `shown_slot_ids: list[int]` | test-local |
| `Recorder` | `events: list[str]` shared by the uow double and executor doubles | test-local |
| `RecordingUow(recorder, fail_on_appends: frozenset[int] = frozenset())` | `__call__(*, write=False, exclusive=False)` is a `contextlib.contextmanager`: appends `"enter:write"`/`"enter:read"`, `depth += 1`, yields a `_Tx`; in `finally` `depth -= 1` and appends `"exit"`. `_Tx.core.lookup_log.append(entry)` increments an append counter `n` (1-based); if `n in fail_on_appends` raise `sqlite3.OperationalError("database is locked " + card_like())`; else appends `"append"`, stores `entry` in `appended: list[LookupEntry]`, returns `100 + n`. `_Tx.commit()` appends `"commit"`. Exposes `appended`, `depth`, `returned_ids: list[int]` | DO-4 §13 shape; cases.md §1.0 semantics |
| `ExecutorDouble(name, recorder, uow=None, *, for_model=..., record_ids=(), passage_ids=(), result_seen="ok", lookup_written=False, raises: BaseException | None = None, returns_raw: object | None = None, unrenderable: bool = False)` | On call: append `f"execute:{name}"`, store `(args, scope)` in `calls`, record `uow.depth` if a uow was given; if `raises` → raise it; if `returns_raw` → return it (for S-9); if `lookup_written` → write its own entry through `uow(write=True)` and `commit()` (the scheduling-service stand-in); return `ToolResult(ok=not isinstance(for_model, ToolError), for_model=for_model, captured=None, lookup=LookupEntry(tool=name, record_ids=record_ids, passage_ids=passage_ids, result_seen=result_seen, message_id=0, turn_id=TurnId(OTHER_TURN)), lookup_written=lookup_written)`. With `unrenderable=True` (S-10): build the result with `ToolResult.model_construct(...)` (same field values) and `for_model={"when": object()}`, after its own row write when `lookup_written` | test-local |
| `make_def(name, kind, args_model, executor, *, requires_verified=None, effect=None)` | `ToolDef(name=…, description=f"Test tool {name}. Returns test data. Do not use for real requests.", …)`; `requires_verified` defaults to `kind not in {KB_SEARCH, SLOT_SEARCH}`; `effect` defaults to `"write"` for BOOK/MOVE/CANCEL/CHANGE_REQUEST else `"read"` | test-local |
| `Boom(RuntimeError)` | raised by the failing executor; its message holds `card_like()` and `full_phone()` | test-local |
| `WP2_INVOICE_FOR_MODEL` | `{"invoices": [{"invoice_id": "INV-204411", "issued_on": "2026-10-02", "due_on": "2026-11-01", "paid": False, "total_cents": 47800, "balance_cents": 47800, "lines": [{"description": "Diagnostic visit", "amount_cents": 8900}, {"description": "Contactor replacement", "amount_cents": 24500}, {"description": "After-hours dispatch", "amount_cents": 14400}]}]}` | ticket WP-2 text; view field names from graph-tools §3 `InvoiceView` (amounts in integer cents) |
| `WP2_SNAPSHOT` | `"INV-204411 issued 2026-10-02 due 2026-11-01 total 47800 balance 47800 unpaid"` (≤ 80 chars, ids and values only) | synthetic from WP-2 |
| WP-2 executor double | returns `WP2_INVOICE_FOR_MODEL`, `record_ids=("INV-204411",)`, `result_seen=WP2_SNAPSHOT` | stands in for AEA-27's `read_invoices` |
| `foreign_customer_id()` | `"MHC-" + str(90000 + 9999)` → a distinctive id never in issued data | built at run time |
| `full_phone()` | `"-".join(("512", "555", str(1000 + 77)))` | built at run time |
| `card_like()` | `" ".join(["4000"] * 4)` | built at run time |
| `six_digit_code()` | `str(100000 + 48291)` | built at run time |
| `strip_titles(schema)` | the §5 step 2.2 rule, re-implemented in the doubles for the AC-4 comparison | test-local |

No literal full phone number, card-like number or six-digit code appears in any source file; only the issued, fictional
WP-2 identifiers (`MHC-10002`, `INV-204411`) appear as literals. No customer name appears. Fixtures stay inside
`tests/unit/agent/tools/`.

---

## 7. Checks (what to run, and what passing looks like)

Every command runs in the worktree root with `export UV_LINK_MODE=hardlink`. No paid model call; no port bound; pytest
serial (never more than `-n 2`; this slice does not need xdist).

| When | Command | Passing looks like |
|---|---|---|
| Test-writer, red | `uv run pytest tests/unit/agent/tools -q` | every test errors with `ModuleNotFoundError: No module named 'meridian.agent.tools.dispatch'` |
| Test-writer, collect | `uv run pytest --collect-only -q tests/unit/agent/tools` | exit 0 |
| Implementer, iterate | `uv run pytest tests/unit/agent/tools -q` | all pass |
| Affected-test sweep | `grep -rl "meridian.agent.tools.dispatch" tests/ eval/ src/` | only `tests/unit/agent/tools/test_dispatch.py`, `test_registry.py` (no other importer exists in wave 1) |
| Gate 1: lint | `uv run ruff check src/meridian/agent/tools/dispatch.py tests/unit/agent/tools` | `All checks passed!` |
| Gate 2: format | `uv run ruff format --check src/meridian/agent/tools/dispatch.py tests/unit/agent/tools` | `… files already formatted` (run `uv run ruff format <same paths>` first if needed) |
| Gate 3: types | `uv run mypy` (the project's configured files: `src/meridian`, `tests`, `eval`, strict + `pydantic.mypy`) | `Success: no issues found` |
| Gate 4: affected tests | `uv run pytest tests/unit/agent/tools -q -rP` | `<N> passed`, 0 failed, 0 errors (record N) |
| Gate 5: affected journeys | `uv run python -m tests.journeys.affected --base main --list-only` | prints `changed files: <k> (base main)` then `0 journeys affected`; exit 0 |
| Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no `FAIL` |
| Scope check | `git diff --name-only main...HEAD` | exactly the repo files in §2.1 (dev log is outside the repo) |

Full suite: **not** run. None of the full-suite triggers applies (no shared fixture, settings, dependency, lockfile or
widely imported module changes; `dispatch.py` has no importer yet). Capture verification for WF-1 (CAP-1) is AEA-51's;
here AC-6 and AC-9 are the capture evidence. Evaluation: N/A (ticket *Evaluation*: no checks added).

**Must not (implementer and test-writer):**
- edit any file outside §2.1, including `web/container.py` (`register_tool_dispatch` stays a no-op), `domain/*`,
  `ports/*`, `privacy/redact.py`, `adapters/sqlite/*`, `pyproject.toml`, `uv.lock`, `tests/conftest.py`,
  `tests/unit/test_import_direction.py`, any `docs/design/contracts/stage7/*.md`, `docs/ux/**`, `apps/web/**`;
- add a module-level registry, a self-registering decorator, or any import-time side effect;
- mark `ToolRegistry`, `ToolDispatcher` or their methods `@final`, or add `__slots__` (AEA-35 subclasses the dispatcher);
- write the lookup row before the result is rendered (S-10), or write a dispatch row for a write the service already logged;
- emit a trace span or take a `TraceSink` (R-G-17); build the specialist loop, brakes, round counting or the
  identical-call stop (AEA-35); add business refusals (`not_shown`, `fee_bearing`, `not_owned`… are executor results that
  dispatch only passes through);
- open a `uow(...)` around an executor call, or one transaction around several calls;
- put arguments, exception text, `repr(exc)`, `exc_info`, an unknown tool name, `result_seen` or content in any log line;
- echo any argument value or model-invented key into a `ToolError.message`;
- let any exception escape `dispatch`, or raise from `dispatch` for anything (start-up `ValueError`s belong to
  `ToolRegistry.__init__` / `check_covers` only);
- write a literal full phone number, card-like number or verification code anywhere; call a paid model; bind 4019 or 5184;
- `git add -A`, push, or force-push; edit frozen tests.

---

## 8. Risks and requests

- **R-1 (same-wave storage).** `tx.core.lookup_log` exists only once AEA-10 merges; AEA-02's `CoreRepos` shell has just
  a constructor. The private `_HasLookupLog` cast (§4.4) lets this slice type-check and merge independently, through the
  DO-4 §13 name. It stays correct after AEA-10 lands (a cast to a compatible Protocol is not "redundant" to mypy). AEA-51
  proves the real repository; if AEA-10 ever renamed `append`, AEA-51's integration fails loudly. Optional follow-up
  after AEA-10: drop the cast. **Not** a blocker.
- **R-2 (contract gap, S-8).** `ToolResult` carries no row id, so for a write whose service already wrote the row
  (`lookup_written=True`) dispatch cannot know `lookup_id`; this plan sets it to `None`. graph-tools §1's comment says
  "None only if its write failed". No consumer reads `lookup_id` (grep of `docs/design`, `docs/plans`). **Request to the
  orchestrator:** post S-8 on the issue; if a consumer later needs it, a small follow-up adds `lookup_id: int | None =
  None` to `ToolResult` (AEA-02) filled by AEA-28. Not a product decision.
- **R-3 (plan-added start-up checks S-1, S-2).** A sibling `ToolDef` that sets `requires_verified=False` on an account or
  write kind, or names an argument like a scope field, will fail `ToolRegistry(...)` at AEA-51's start-up. That is the
  intent (R-14 and "never a scope field" by construction); AEA-27/28/33 should know before they build. **Request:** the
  orchestrator posts S-1…S-10 on issue #22 and a one-line note on #27, #28, #33.
- **R-4 (shared context lines).** The A7b row in `area-map.md` also lists files of AEA-14 (wave 1), AEA-35, AEA-39; the
  ICM *Routes verified* row and the *Last reconciled* line are rewritten by every slice. Concurrent wave-1 merges can
  conflict on these lines; the merge step keeps both slices' facts. Keep the edit to the exact substrings in §5 step 8.
- **R-5 (test package marker).** This slice creates `tests/unit/agent/tools/__init__.py` (empty). AEA-27, 28, 33 (wave 2)
  add tests in the same folder and must not recreate it; an identical empty file merges cleanly anyway.
- **R-6 (80-character free-text rule).** For executed reads, `result_seen` is the executor's snapshot; dispatch applies
  STORE (cards, codes) and stamps ids but does not parse free text. Executors AEA-27/28/33 own "ids and values, no free
  text over 80 characters"; AEA-51's CAP-1 checks stored rows.
- **R-7 (write executor that commits then raises).** If a scheduling executor raises **after** its service committed the
  booking and its row, dispatch writes a second, `failed` row. Executors must not raise after a commit (AEA-28's
  contract: return `ToolResult`, never raise). Recorded for the security reviewer.
- **R-8 (truncated write result).** A write result over 4,000 chars stays `ok` with truncated JSON content, so a
  completed booking is never reported to the model as failed. The scheduling executor's `for_model` is far smaller.
- **R-9 (no shared primitive requested).** Nothing new is needed from AEA-01/02/04/10/11.
- **R-10 (STORE over executor snapshots).** STORE's card rule matches 13–19 digits joined by single spaces or dashes, with
  no checksum. An executor snapshot listing numeric ids separated by **spaces** (`slots 57204 57205 57206`) would be stored
  as `[card number removed]`. AEA-28 joins ids with commas and AEA-27's snapshots hold `INV-` ids and amounts, so neither
  is hit. **Request (orchestrator, a note on #27, #28, #33):** join numeric ids in `result_seen` with commas, never
  spaces. Not a blocker.
- **R-11 (AEA-35 subclasses the dispatcher).** AEA-35's `ScriptedDispatcher(ToolDispatcher)` skips `super().__init__`.
  §5 step 4 keeps that legal (no `@final`, no `__slots__`, no hidden attribute use). A future change that adds a required
  base-class attribute would break AEA-35's tests, not production.
- **R-12 (AEA-02 still building).** `dispatch_doubles.py` imports `meridian.domain.tools`, so before AEA-02 merges the
  frozen tests would fail for the wrong reason (`No module named 'meridian.domain.tools'`). The test-writer starts only
  after AEA-02 merges. If AEA-02 lands a field name or home that differs from §4.2, step 0 stops the slice: do not
  adapt to it here; report it.
- **Disk:** `/home` at 83% (2026-10-21); one worktree, hardlinked venv.

---

## 9. Readiness

**READY** — no product decision, no signed-contract change, and no conflict with D-4…D-15.

**Blocked on (merge prerequisite; the imports are truly needed):**
- **AEA-02** — `domain/tools.py` (`ToolDef`, `ToolCallScope`, `LookupEntry`, `ToolError`, `ToolResult`, `ToolKind`,
  `ToolCallRecord`), `domain/common.py` (`ToolErrorCode`, `LLMFacing`, `MeridianModel`), `ports/models.py` (`ToolCall`,
  `ToolSchema`), `ports/runtime.py` (`UnitOfWorkFactory`).

**Already on main, no longer blockers:** AEA-04 `privacy/redact.py` (`redact`, `RedactionProfile`; merge `ef03e05`);
AEA-01 `pyproject.toml` tool config, package markers, `tests.journeys.affected` (merge `07924f5`).

**Not blocked on:** AEA-10 (storage reached through its DO-4 §13 signature, R-1), AEA-27/28/33 (executors are doubles),
AEA-35 and AEA-51 (consumers), AEA-57 (the journey record says *Blocked by*).

**Order for the orchestrator:** after AEA-02 merges (AEA-01 and AEA-04 already have), `test-writer-agent` freezes §3.2 in the worktree and
commits it (`test(agent): frozen failing tests for AEA-22`), then `fanout-implementer` runs §5 steps 0–9. Post S-1…S-10 on
issue #22 (and the R-3 and R-10 notes on #27, #28, #33). `security-privacy-agent` reads this diff at the wave-1 merge.
