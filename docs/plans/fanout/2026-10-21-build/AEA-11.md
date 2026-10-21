# Plan — [AEA-11] test support: scripted fakes

**Status:** planned. READY once AEA-02 is on `main` (AEA-01 already is). See §9.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/11 · **Base revision:** `16ca639`
(main when refreshed, 2026-10-21. AEA-01, 03, 04, 08 and 25 are merged; AEA-02 is planned but not built.)
**Planner:** fanout-planner on `claude-opus-5-5`. First written at `9c3e7e7`, refreshed at `16ca639` against AEA-01's merged
scaffold and AEA-02's final plan. **Implementer:** fanout-implementer on Sonnet. **Lane:** build-loop. **Risk:** none (no
`risk::security`, so no test-writer and no security review).
**Slug / branch:** `test-support-fakes` → branch `aea-11-test-support-fakes`, worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-11` (the orchestrator creates it).

**What changed in the 2026-10-21 refresh (read this if you saw the first version):**
1. AEA-02's plan (§4.12, decision D-4) declares `provider: ClassVar[ProviderName]` on the three model Protocols, and
   models.md §2's adapters do the same. So a fake's provider is now a **class variable**, not a constructor argument.
   The Anthropic choice fake is the subclass `FakeAnthropicChoiceModel` (PD-9). There is no `provider=` keyword any more.
2. The defining modules are now known from AEA-02 §4.0: `ProviderFailure`, `ProviderFailureKind`, `ProviderName`,
   `ProviderCall`, `CallRecord` and `Role` are in `meridian.domain.common`. `RetrievalResult` and `Passage` are in
   `meridian.domain.records`. `ExportStatus`, `SpanHandle` and `TurnIds` are in `meridian.domain.turn`. `ProviderTurn`
   is `JsonValue`. Generics use PEP 695 `[T: BaseModel]` (PD-14, §4).
3. How to build `Attempt[T]` in the structured fake, proved in a scratch run with mypy 2.4 strict, the pydantic plugin
   and pydantic 2.14.1 (PD-16).
4. AEA-01's tooling as merged (`pyproject.toml` on `main`), and the current text of the area-map A0 cell and the ICM rows
   (§5 step 10).

---

## 1. Goal and sources

### Goal

From the issue (`docs/plans/tickets/AEA-11.md`, *What to build*): "`tests/fakes/` (DO-3 §9; slice plan row AEA-11) holds
six doubles, each honouring its port exactly as DO-4 §12–§13 and the Stage 7 addenda define it, so a test that passes on
a fake means the same as it would on the real adapter". The six are `FakeChoiceModel` (plus its Anthropic subclass),
`FakeStructuredModel`, `FakeToolModel`, `FixedClock`, `FakeIndex` and `InMemoryTraceSink`. None of them makes a paid
call, downloads a model or opens a network connection.

**What it does, concretely.**

- **A graph test scripts the planner.**
  `FakeChoiceModel([ChoiceAnswer(choices={"intent": "book"}, probabilities=None), ScriptedFailure(ProviderFailureKind.BODY_ERROR, http_status=503)])`.
  - Call 1 returns `Attempt(value=<that answer>, record=ProviderCall(provider="openrouter_jev", model="typesafe/jev-1.13", status="ok", …), failure=None)`.
  - Call 2 returns `Attempt(value=None, record=ProviderCall(status="error", failure=<f>, …), failure=<f>)`, with
    `f.kind == BODY_ERROR` and `f.retryable is True` (503 is in the retryable set).
  - Call 3 raises `ScriptExhaustedError`. Even a `try/except Exception` in the code under test cannot swallow it.
- **A choice outside the options.** If the script holds `ChoiceAnswer(choices={"intent": "cancel_everything"})` and the
  request's `intent` field offers only `book` and `other`, the fake returns `INVALID_OUTPUT`, as the real Jev adapter
  does.
- **The Anthropic choice fake.** `FakeAnthropicChoiceModel([...]).provider == "anthropic"`, with default model
  `"claude-sonnet-5-5"`. It is the planner-fallback stand-in.
- **The clock.** `FixedClock()` reads Friday 2026-10-16 10:00 America/Chicago every time.
  `.advanced(timedelta(hours=1))` is a second clock at 11:00, and the first one still reads 10:00.
- **The trace sink.**
  - `with sink.turn(ids) as span:` yields `SpanHandle(turn_id=ids.turn_id, trace_id="000…01")`.
  - `sink.model_call(span, record, "masked in", "masked out")` is stored verbatim under that turn.
  - `sink.export_status(span)` returns `"sent"`, also after the block has closed.

**How it works, in one line.** Each model fake takes the next script entry under a lock, records the request, and turns
the entry into an `Attempt` whose `record` is a `ProviderCall` (never a `CallRecord`). The other three fakes are small,
deterministic objects with the port's exact method signatures.

### Context

This is wave 1 of the Stage 8 build. Every later build ticket (AEA-12…AEA-53) tests against the DO-4 ports through these
fakes. Sibling plans already code against this plan's API (AEA-20, 29, 30, 33, 34, 35), so names and behaviour stay as
first planned except for `provider` (refresh note 1).

Stage 7 changed the shapes the fakes must honour:
- adapters now return `ProviderCall`, and the gateway wraps it (MOD-1, MC-28);
- `ProviderMessages` gained fields (MOD-17, R-G-4);
- `TraceSink.export_status` takes the turn handle (MOD-9);
- `FixedClock` has a signed definition (DAT-32, R-G-9).

AEA-02 writes the types; this ticket only consumes them.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-11.md` (= issue #11) | AC-1…AC-14; six fakes; no `temp_sqlite()`; example pair: none |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-11 (blockers 01, 02; owns `tests/fakes/`); §3 collision rows `tests/fakes/` → 11, `tests/conftest.py` → 01, `tests/fixtures/sqlite.py` → 10; dependency row "AEA-11 → 29, 30" (`FixedClock` in `tests/fakes/clock.py`) | Owned folder; `conftest.py` and `fixtures/` are not ours |
| Requirements | PRD R-3 (never the server wall clock), via data.md §8a | `FixedClock` refuses naive and non-Chicago datetimes |
| Code design | DO-3 `docs/design/code-design.md` §4.2 (port table: test implementations); §6 S-1, S-4, S-8, S-10, S-20; §9 (test layout; full suite when `tests/fakes/` changes) | One fake per port; services are not faked (S-20) |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §11 (`ProviderFailureKind`, `ProviderFailure`), §12 (model ports and their contract), §13 (`RetrievalIndex`, `RetrievalResult`, `IndexInfo`, `Clock`, `TraceSink`, plus its *Superseded* note: `export_status(turn)`), §5 (`Passage`), §2 (`TurnIds`), §16 (addenda win). Unchanged for these shapes by AEA-08's reconcile (`c0621de`) | Exact signatures (copied in §4) |
| Stage 7 addenda | `stage7/models.md` §1 (`ProviderName`, `ProviderCall`, `CallRecord(ProviderCall)`, `Attempt.record: ProviderCall`, `ProviderMessages`, MOD-1, MOD-17); §2 (adapters: `provider: ClassVar[ProviderName]`; `AnthropicAdapter` implements all three ports, `JevAdapter` **implements `ChoiceModel` only**; price-table model IDs `claude-sonnet-5-5`, `typesafe/jev-1.13`; cost rule for failed attempts); §3 (failure mapping, `retryable` rule); §4 (`SpanHandle`, `ExportStatus`, `export_status(turn)`, MOD-9; it is called *after* the `with` block closes); §5 / cross-topic 2 (read-only `provider`). `stage7/data.md` §8a (`FixedClock`, DAT-32). `stage7/graph-core.md` §1 (`SpanHandle` lives in `domain/turn.py`). `stage7/graph-tools.md` §1 (`ToolSchema`, `ToolCall`), §2 (`ToolTranscript`; tool spans are `node` spans) | The Stage 7 shapes win over DO-4 |
| Sibling plan (the types) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0 (defining module vs re-export table; PEP 695 generics; `init_typed` rule 9), §4.1 (`common.py`), §4.2 (`records.py`), §4.8 (`turn.py`), §4.12 (`ports/models.py`, D-4 `ClassVar`), §4.13 (`ports/runtime.py`) | Import lines (§4); `ClassVar` provider (PD-9) |
| Decision ledgers | `docs/plans/7b-decisions/merge-clashes.md` MC-28; `residuals-graph.md` R-G-4 (`items`, not `payload`), R-G-9 (`FixedClock` immutable; CAS-37 withdrawn); `7b-decisions/data.md` DAT-32 | No `set()` / `advance()` mutators; field name `items` |
| Observability contract | DO-6 `docs/design/observability-contract.md` *Capture verification* (in-memory exporter; masking runs in the caller as in production) | The sink stores exactly what it is given and masks nothing |
| Evaluation plan | DO-5 | n/a: the fakes decide no expected answer (ticket *Evaluation*) |
| Key-metrics registry | DO-7 M-23…M-26 | n/a: no metric comes from fake output (ticket *Metrics*) |
| Journey rule | `.claude/rules/integrated-journeys.md` §4 (record fields, levels); `docs/plans/ux-join/backend-amendments.md` §3 (row AEA-11 → pattern **D**, "no journey path") | AC-13 record, level `mock-tested`, "no journey path" |
| Build loop | `.claude/rules/build-loop-test-scope.md` (+ AEA addition) | Affected tests; fast gates; journey command |
| Multi-turn rule | workspace `.claude/rules/context-management-multi-turn.md` rule 3 | Recording fake: every request kept in order, so turn 1, 2 and 5 prompts can be asserted (AEA-35's `test_stable_prefix_turns_1_2_5` relies on it) |
| Scaffold (merged) | `pyproject.toml` on `main` (AEA-01): mypy `strict`, `pydantic.mypy` with `init_typed`, `files = ["src/meridian", "tests", "eval"]`, `tests.*` override `disallow_untyped_defs = false`; ruff `E,W,F,I,B,UP,S,RUF`, ignore `E501, RUF001-003, UP040`, tests ignore `S101,S105,S106,S603,S607,S311`, line length 110; pytest `pythonpath = ["."]`, `--strict-markers --strict-config`, markers `journey`, `live`. `tests/journeys/affected.py` (`--base`, `--list-only`). `tests/fakes/__init__.py` exists and is empty | Tooling the §7 commands rely on |
| Context rules | `.claude/rules/context-maintenance.md` rules 3, 6 | AC-14 rows: planned → actual; replace the evidence link |

---

## 2. Boundary

### Files this slice owns (the only files the implementer may create or edit)

| File | Create / modify | Change |
|---|---|---|
| `tests/fakes/__init__.py` | **modify** (on `main`, empty, from AEA-01) | Re-export the public names with `__all__` (§5 step 6) |
| `tests/fakes/models.py` | **create** | `ScriptExhaustedError`, `ScriptedFailure`, `provider_call`, `FakeChoiceModel`, `FakeAnthropicChoiceModel`, `FakeStructuredModel`, `FakeToolModel` (§5 step 2) |
| `tests/fakes/clock.py` | **create** | `CHICAGO`, `WORKED_PAIRS_NOW`, `FixedClock` (§5 step 3) |
| `tests/fakes/index.py` | **create** | `FakeIndex` (§5 step 4) |
| `tests/fakes/trace.py` | **create** | `RecordedModelCall`, `RecordedNode`, `RecordedTurn`, `InMemoryTraceSink` (§5 step 5) |
| `tests/unit/fakes/__init__.py` | **create** (empty, 0 bytes) | Package marker; every `tests/unit/*` folder on `main` has one |
| `tests/unit/fakes/test_fakes.py` | **create** | All AC-1…AC-12 tests plus the plan-added tests (§7.1) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-11.md` | **create** (date = day of the run) | AC-13 record |
| `.claude/reference/area-map.md` | modify **one cell** | A0 row status (AC-14) |
| `.claude/state/icm-progress.md` | modify **one row** | *Routes verified against code and tests* (AC-14) |
| `docs/design/code-design.md` | modify: **add one line** in §9 | *Built on `main`* line (AC-14) |

### Shared surfaces read only (never edit)

- `src/meridian/ports/models.py`, `src/meridian/ports/runtime.py`, `src/meridian/domain/*.py` (AEA-02).
- `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/__init__.py`, `tests/unit/__init__.py`,
  `tests/journeys/affected.py`, and the ruff / mypy / pytest configuration (AEA-01).

### Owned by other slices: do not touch

- `tests/fixtures/sqlite.py` (AEA-10; `temp_sqlite()` is not in this ticket).
- `tests/unit/test_import_direction.py` (AEA-01 and the tickets that append to it; this ticket adds no function there).
- `tests/unit/ports/**` (AEA-02), `tests/contract/**` (AEA-17, 18, 19: recorded provider fixtures are theirs).
- `src/meridian/**` entirely, `apps/web/**`, `docs/ux/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`.
- `docs/archive/`, `docs/parked/`, the briefing and the issued data.
- `.claude/state/build-ledger.md` (the orchestrator's).

Nothing here starts a server. Never bind ports 4019 or 5184.

---

## 3. Requirements table

### 3.1 Decisions this plan makes (the implementer applies them; none is a product decision)

| ID | Decision | Basis |
|---|---|---|
| **PD-1** | **What a script entry can be.** One of three forms. (a) A **bare value**: for choice, a `ChoiceAnswer`; for structured, a pydantic model instance **or** a `Mapping` of raw output; for tool, a `ToolStep`. (b) A **`ScriptedFailure`**. (c) A **prebuilt `Attempt`**, returned unchanged. For (a) and (b) the fake builds the `ProviderCall` itself. | Ticket: "returns the scripted `Attempt` per call in order … always carries a `ProviderCall` … also on a scripted failure, with the failure as a `ProviderFailure` of the scripted kind". Prebuilt Attempts let AEA-20 and AEA-26 tests script token counts and costs. |
| **PD-2** | **Prebuilt Attempts are checked at construction.** A `record` that is a `CallRecord` raises `ValueError` (a fake never builds one, MOD-1). A `record.provider` other than the class's `provider`, or a `record.model` other than the instance's `model`, raises `ValueError`. Any entry of another type raises `TypeError`. | MC-28; the ticket's "a fake never builds a `CallRecord`". Failing at construction points at the test's own mistake. |
| **PD-3** | **An exhausted script raises `ScriptExhaustedError`, a subclass of `BaseException`** (not `Exception`). | AC-3: "fails the test with a named error". The gateway, runner and nodes "never raise" and may wrap calls in `except Exception`. A `BaseException` passes through them, as pytest's own `Failed` outcome does, and pytest reports it as a failure. |
| **PD-4** | **Default `ProviderCall` for a record the fake builds:** `latency_ms=0`, all six token counts `0`, `cost_usd=0.0`, `cost_source="price_table"`, `provider_request_id=None`. `stop_reason` is: choice `None`; structured `"end_turn"`; tool, the scripted `ToolStep.stop_reason`; failures `None`, except `REFUSAL` → `"refusal"` and `MAX_TOKENS` → `"max_tokens"`. | models.md §2 cost rule: a failed attempt with no usage is `0.0`, all tokens `0`, `price_table`. Zero cost keeps fakes from moving any spend total. |
| **PD-5** | **`ScriptedFailure.retryable=None` means "use the adapters' rule"** (models.md §3, DO-4 §11): `True` for `TIMEOUT`, `CONNECTION`, `RATE_LIMITED`, `OVERLOADED` and `SERVER`; for `BODY_ERROR`, `True` only when `http_status` is in {408, 429, 500, 502, 503, 504, 529}; `False` otherwise. An explicit bool overrides the rule. | Same rule as the adapters, so gateway retry tests mean the same thing on fakes. |
| **PD-6** | **`FakeChoiceModel` checks a bare `ChoiceAnswer` against the request.** The set of `choices` keys must equal the set of `req.fields` names, and each value must be a key of that field's `options`. A mismatch (missing, extra, or outside the options) returns `INVALID_OUTPUT` with `http_status=200` and `retryable=False`. Prebuilt Attempts are not checked (PD-1: they are returned unchanged). | DO-4 §12 ("validated against each field's options by the adapter"); models.md §3 Jev row: "a field missing or a choice outside its options → `INVALID_OUTPUT`". |
| **PD-7** | **`FakeStructuredModel` validates against `req.output_model`.** A bare model instance passes unchanged when `isinstance(value, req.output_model)`. An instance of another model class returns `INVALID_OUTPUT`. A `Mapping` is validated with `req.output_model.model_validate(dict(value))`, and a `pydantic.ValidationError` returns `INVALID_OUTPUT`. | models.md §3: "output fails `output_model` validation → `INVALID_OUTPUT`". Lets tests script raw invalid output. |
| **PD-8** | **`FakeToolModel`'s `items` format** (only the fake reads it, MOD-17). `start(user)` returns `({"role": "user", "content": user},)`. `append` adds `{"role": "assistant", "text": step.text, "tool_calls": [{"id", "name", "args"}…]}` and, when `results` is not empty, `{"role": "tool_results", "results": [{"tool_call_id", "content"}…]}`. `append` raises `ValueError` when `messages.provider` or `messages.model` differs from its own. `tool_step` does not check the messages. | models.md §1: `items` are the provider's own objects, only the builder reads them, and `append` refuses foreign messages. AEA-35 asserts `requests[i].messages.items == ({"role": "user", "content": …},)`. |
| **PD-9** | **`provider` is a class variable, not a constructor argument.** Each model fake declares `provider: ClassVar[ProviderName]`: `FakeChoiceModel` `"openrouter_jev"`, `FakeAnthropicChoiceModel(FakeChoiceModel)` `"anthropic"`, `FakeStructuredModel` `"anthropic"`, `FakeToolModel` `"anthropic"`. Each also declares `DEFAULT_MODEL: ClassVar[str]` (`"typesafe/jev-1.13"` for the Jev choice fake, `"claude-sonnet-5-5"` for the other three). The constructor takes `model: str \| None = None`, meaning "use `DEFAULT_MODEL`". `model` is a read-only `@property`. There are **no** Jev structured or Jev tool fakes. | AEA-02 §4.12 D-4: the Protocols declare `provider: ClassVar[ProviderName]`, and "every double must do the same". models.md §2: `JevAdapter` implements `ChoiceModel` only. Rule `code-design-solid-modularity`: no double for a variant nobody uses. The scratch run (refresh note 3) proved `c: ChoiceModel = FakeAnthropicChoiceModel([])` type-checks with the subclass overriding the ClassVar. |
| **PD-10** | Each fake guards its mutable state (script position, recorded requests, recorded spans) with one `threading.Lock`. | DO-3 §2.2: parallel specialists run on threads in a sync graph, and a shared fake must not lose or duplicate an entry. Order across threads stays nondeterministic, so tests that need order give each role its own fake. |
| **PD-11** | **`FixedClock` accepts only America/Chicago.** It requires `isinstance(at.tzinfo, ZoneInfo)` with `key == "America/Chicago"`. A naive datetime, a fixed-offset `timezone`, or another zone raises `ValueError` with a fixed message that contains no value. `advanced(by)` adds **elapsed** time: `FixedClock((self._at.astimezone(UTC) + by).astimezone(CHICAGO))`. | data.md §8a; R-3. Elapsed-time arithmetic is what a real clock does across the 2026-11-01 DST change; wall-clock `+` would land an hour off. It is identical to `at + by` on every day without a DST change, which covers all worked-pair dates. AEA-30's plan cites this rule. |
| **PD-12** | **`FakeIndex` signature and ranking.** `FakeIndex(passages=(), *, by_query=None, info=None)`. Search steps: 1. the pool is `by_query[query]` when the query is a key, else `passages`; 2. keep passages with `score >= min_score`; 3. sort by score, descending and stable (ties keep configured order); 4. return the first `max(k, 0)`; 5. set `below_floor = (no passage cleared)`. Every search is recorded as `(query, k, min_score)`. Default `info()`: `embedding_model="BAAI/bge-small-en-v1.5"`, `dimension=384`, `chunks` = distinct `passage_id`s over `passages` and every `by_query` list, `manifest_hash="fake-index"`, `files=17`. | DO-4 §13 ("top k", "nothing cleared the relevance floor"); `files == 17` is the readiness rule; bge-small-en-v1.5 is 384-dimensional. AEA-33's plan copies this signature. |
| **PD-13** | **`InMemoryTraceSink` handles.** `InMemoryTraceSink(*, status: ExportStatus = "sent")`. `turn(ids)` creates a `RecordedTurn` and yields `SpanHandle(turn_id=ids.turn_id, trace_id=format(n, "032x"), native=<that RecordedTurn>)`, where `n` is the 1-based turn count. It sets `closed=True` on exit, also when the block raises (the exception propagates). `model_call`, `node`, `export_status` and `spans_for` raise `ValueError` for a handle whose `native` is not one of this sink's turns. They accept a handle whose turn has already closed. | models.md §4: `native` is "the sink's own span; opaque to every caller", so the sink keeps its record there. `export_status` is called after the block closes (AEA-40). A foreign handle is a wiring mistake and must fail loudly in a test. Deterministic trace IDs keep assertions stable. |
| **PD-14** | Import every shared type from its **defining** module, per AEA-02 §4.0 (exact lines in §4). | mypy strict sets `implicit_reexport = False`. AEA-02 re-exports with `as Name`, so either home works, but the defining module always does. |
| **PD-15** | Test-only helper names (`ScriptedFailure`, `provider_call`, `Recorded*`) live in `tests/fakes/`. They are **not** ports or production seams. | DO-3 S-20 and rule `code-design-solid-modularity`: no new production abstraction. |
| **PD-16** | **How to build an Attempt.** The choice and tool fakes write the type out: `Attempt[ChoiceAnswer](...)` and `Attempt[ToolStep](...)`. The structured fake builds it **unparametrised**: on success `return Attempt(value=v, record=…, failure=None)`, where `v` was narrowed to `T` by `isinstance(v, req.output_model)` or comes from `req.output_model.model_validate(...)`. On failure it writes `attempt: Attempt[T] = Attempt(value=None, record=call, failure=f)` and then `return attempt`. A prebuilt entry is `return cast("Attempt[T]", entry)`. Do **not** write `Attempt[T](...)` (at runtime it builds `Attempt[TypeVar]`) or `Attempt[req.output_model](...)` (it needs a `type: ignore`). | Scratch run 2026-10-21 (mypy 2.4.0 strict + pydantic plugin, pydantic 2.14.1, `-W error`): the unparametrised form type-checks with no ignore, keeps `value is v`, and `model_dump()` emits the subclass fields. |

### 3.2 Requirement → implementation → verification

| # | Requirement (source) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 | Each fake satisfies its port Protocol structurally, incl. the read-only `provider` (DO-4 §12–§13; models.md cross-topic 2; AEA-02 D-4) | Signatures copied from §4; PD-9 | `uv run mypy` (covers `tests/`) clean, plus `tests/unit/fakes/test_fakes.py::test_fakes_satisfy_protocols` |
| AC-2 | Scripted Attempts come back in order and never raise; `ProviderCall` (not `CallRecord`) on success and failure; `provider` set; scripted kind in `Attempt.failure` (MC-28) | PD-1, PD-4, PD-5, PD-16 | `test_scripted_attempts_in_order_with_provider_call` |
| AC-3 | Exhausted script fails the test with a named error (DO-5: a model is never its own authority) | PD-3 | `test_exhausted_script_fails_loudly` |
| AC-4 | Choice outside the field's options → `invalid_output` (DO-4 §12; models.md §3) | PD-6 | `test_choice_outside_options_is_invalid_output` |
| AC-5 | `FakeToolModel.append` refuses foreign messages with `ValueError` (models.md §1, MOD-17) | PD-8 | `test_tool_fake_append_refuses_foreign_messages` |
| AC-6 | Every request recorded in order (multi-turn rule 3) | `requests`, `timeouts`, `starts`, `appends` lists under the lock | `test_requests_recorded_in_order` |
| AC-7 | `FixedClock()` default, constant `now()`, `advanced` returns a new clock (data.md §8a) | PD-11 | `test_fixed_clock` |
| AC-8 | `FixedClock` refuses naive and foreign-tz datetimes (R-3) | PD-11 | `test_fixed_clock_refuses_naive_and_foreign_tz` |
| AC-9 | `FakeIndex.search` floor, k and `below_floor`; `info()` model name (DO-4 §13) | PD-12 | `test_fake_index_floor_and_info` |
| AC-10 | `InMemoryTraceSink` handle, spans grouped, `export_status(span)` (models.md §4) | PD-13 | `test_trace_sink_handle_and_export_status` |
| AC-11 | Importing `tests/fakes` loads none of `anthropic`, `httpx`, `langfuse`, `fastembed` | Fakes import only the standard library, `pydantic`, and `meridian.domain.*` / `meridian.ports.*` | `test_fakes_import_no_vendor_sdk` (subprocess) |
| AC-12 | Fakes write nothing to logs, stdout or disk; the sink stores values verbatim (DO-6 *Capture verification*) | No `logging`, `print`, `open` or file writes in `tests/fakes/` | `test_fakes_leak_nothing_and_sink_does_not_mask` |
| AC-13 [journey] | Level **`mock-tested`**; pattern D (backend-amendments §3, row AEA-11): no deterministic journey reaches `tests/fakes/`; the affected-journey command selects 0 | Journey record (§5 step 9) | `uv run python -m tests.journeys.affected --base main --list-only` prints `0 journeys affected` and exits 0; the record's Level and Blocked-by fields |
| AC-14 | Docs updated in the same change | §5 step 10 | `git diff --name-only main...HEAD` lists the three docs |
| S-1 (plan-added) | Structured fake validates against `output_model` (models.md §3) | PD-7 | `test_structured_fake_validates_output_model` |
| S-2 (plan-added) | Failure defaults follow the adapters' `retryable` rule (models.md §3) | PD-5 | `test_scripted_failure_retryable_defaults` |
| S-3 (plan-added) | Prebuilt Attempts pass through; wrong ones are refused at construction (MOD-1) | PD-2 | `test_prebuilt_attempts_checked_at_construction` |
| S-4 (plan-added) | `advanced` adds elapsed time across DST | PD-11 | `test_fixed_clock_advances_by_elapsed_time` |
| S-5 (plan-added) | `FakeIndex` per-query pools; searches recorded | PD-12 | `test_fake_index_by_query_and_records_searches` |
| S-6 (plan-added) | Sink refuses a handle it did not open; closes on exception; answers after close | PD-13 | `test_trace_sink_refuses_foreign_handle_and_closes_on_error` |
| S-7 (plan-added) | Fakes never read the server wall clock (R-3) | No `datetime.now`, `utcnow`, `date.today` or `time.time` in `tests/fakes/` | `test_fakes_read_no_wall_clock` |
| S-8 (plan-added) | A shared model fake is safe under threads (PD-10) | Lock | `test_model_fake_is_thread_safe` |
| S-9 (plan-added) | `provider` is a ClassVar with the PD-9 values, and the Anthropic choice subclass behaves like its parent | PD-9 | `test_provider_classvars_and_default_models` |

**Worked pair (WP-N): none.** The ticket says "**Example pair:** none — pure test infrastructure; it encodes no customer
behaviour." The concrete input → output examples in §1 play that role for the reviewer.

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Model fakes return `ProviderCall`, never `CallRecord` | models.md §1, MOD-1, MC-28 | AC-2 | in-ticket | Step 2 |
| `provider` attribute, read-only, on the three model fakes | models.md cross-topic 2; AEA-02 D-4 (`ClassVar`) | AC-1 | in-ticket (form refined: ClassVar + subclass) | PD-9, step 2 |
| Structured output validated against `output_model` | models.md §3 | — | added (S-1) | PD-7 |
| `retryable` follows the adapters' rule | models.md §3, DO-4 §11 | — | added (S-2) | PD-5 |
| `FixedClock.advanced` across DST | data.md §8a ("at + by"), R-3 | AC-7 | added (S-4), engineering reading | PD-11 |
| Sink answers `export_status` after the turn closes | models.md §4 (AEA-40 calls it after the block) | AC-10 | added (S-6) | PD-13 |
| Tool spans go through `node` | graph-tools §2 (R-G-17) | — | n/a: no new method; `node` stores any name | Step 5 |
| Recorded provider fixtures | DO-3 §9 `contract/` | — | other-ticket (AEA-17, 18, 19) | — |
| `temp_sqlite()` | DO-3 §9 (moved), DAT-10 | — | other-ticket (AEA-10) | — |
| Capture evidence at real entry points | DO-6 CAP-1…CAP-6 | — | other-ticket (AEA-51, 52, 53) | — |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — (test support only; no production code path runs it) |

---

## 4. Shared code to use

These shapes are copied from DO-4, the Stage 7 addenda and AEA-02's plan §4.1–§4.13. **AEA-02 writes these files; read the
real ones before coding (§5 step 1).** If a name differs from this copy, follow the code on `main` and note the
difference in the report. If a *shape* differs (a field missing, a different `provider` declaration), stop and send the
slice back to the planner.

```python
# meridian/domain/common.py (AEA-02 §4.1; defined here, re-exported from ports/models.py with `as Name`)
class MeridianModel(BaseModel):          # extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
class LLMFacing(MeridianModel): ...
class ThreadId(_PatternId) / TurnId / RequestId   # canonical lower-case uuid4 pattern
class PassageId(_PatternId): PATTERN = r"^[^#\s]+#[0-9]+$"

class ProviderFailureKind(StrEnum):
    TIMEOUT = "timeout"; CONNECTION = "connection"; RATE_LIMITED = "rate_limited"; OVERLOADED = "overloaded"
    SERVER = "server"; PROVIDER_SPEND_CAP = "provider_spend_cap"; OUR_SPEND_LIMIT = "our_spend_limit"
    BAD_REQUEST = "bad_request"; AUTH = "auth"; NOT_FOUND = "not_found"; BODY_ERROR = "body_error"
    REFUSAL = "refusal"; MAX_TOKENS = "max_tokens"; INVALID_OUTPUT = "invalid_output"

ProviderName = Literal["anthropic", "openrouter_jev"]

class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind
    provider: ProviderName
    http_status: int | None
    retry_after_s: float | None
    retryable: bool
    provider_request_id: str | None

class Role(StrEnum):
    PLANNER = "planner"; CLASSIFIER = "classifier"; PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST = "specialist"; RESPONDER = "responder"; BRIEF = "brief"

class ProviderCall(MeridianModel):
    provider: ProviderName
    model: str
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    thinking_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    cost_source: Literal["reported", "price_table"]
    status: Literal["ok", "error"]
    failure: ProviderFailure | None                   # set exactly when status == "error"
    provider_request_id: str | None
    stop_reason: str | None

class CallRecord(ProviderCall):
    role: Role
    attempt: int = Field(ge=1, le=2)
    @classmethod
    def from_provider(cls, call: ProviderCall, *, role: Role, attempt: int) -> CallRecord: ...
```

```python
# meridian/ports/models.py (AEA-02 §4.12; DO-4 §12 + models.md §1; graph-tools §1, §2)
ProviderTurn = JsonValue
class ChoiceField(MeridianModel):    name: str; instructions: str; options: dict[str, str] = Field(max_length=255)
class ChoiceRequest(MeridianModel):  system: str; state: dict[str, JsonValue]; fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel):   choices: dict[str, str]; probabilities: dict[str, dict[str, float]] | None
class StructuredRequest[T: BaseModel](MeridianModel):
    system_prefix: str; system_dynamic: str; user: str
    output_model: type[T]
    max_tokens: int; effort: Literal["low", "medium", "high"] | None
class ToolSchema(MeridianModel):     name: str; description: str; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolCall(MeridianModel):       id: str; name: str; args: dict[str, JsonValue] | None
class ProviderMessages(MeridianModel): provider: ProviderName; model: str; items: tuple[JsonValue, ...]
class ToolStepRequest(MeridianModel):
    system_prefix: str; system_dynamic: str
    messages: ProviderMessages
    tools: tuple[ToolSchema, ...]; max_tokens: int; effort: Literal["low", "medium", "high"] | None
class ToolStep(MeridianModel):       text: str; tool_calls: tuple[ToolCall, ...]; raw: ProviderTurn; stop_reason: str | None
class Attempt[T: BaseModel](MeridianModel):
    value: T | None
    record: ProviderCall
    failure: ProviderFailure | None

class ChoiceModel(Protocol):
    provider: ClassVar[ProviderName]
    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...
class StructuredModel(Protocol):
    provider: ClassVar[ProviderName]
    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...
class ToolCallingModel(Protocol):
    provider: ClassVar[ProviderName]
    def start(self, user: str) -> ProviderMessages: ...
    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...   # (tool_call_id, JSON text)
class ToolTranscript(Protocol):      # graph-tools §2: start + append only
    def start(self, user: str) -> ProviderMessages: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...
```

```python
# meridian/domain/records.py (AEA-02 §4.2)
class Passage(MeridianModel):
    passage_id: PassageId; file: str; section: str
    version_label: str; version_date: dt.date | None; text: str; score: float
class RetrievalResult(MeridianModel):          # re-exported from ports/runtime.py
    passages: tuple[Passage, ...]; below_floor: bool

# meridian/domain/turn.py (AEA-02 §4.8; models.md §4, graph-core §1)
ExportStatus = Literal["off", "sent", "failed"]                  # re-exported from ports/runtime.py
class TurnIds(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; agent_version: str
@dataclass(frozen=True)
class SpanHandle:                                                # re-exported from ports/runtime.py
    turn_id: TurnId
    trace_id: str | None
    native: object = field(default=None, compare=False, repr=False)

# meridian/ports/runtime.py (AEA-02 §4.13; DO-4 §13 + models.md §4)
class IndexInfo(MeridianModel):
    embedding_model: Literal["BAAI/bge-small-en-v1.5"]; dimension: int; chunks: int; manifest_hash: str; files: int
class RetrievalIndex(Protocol):
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult: ...
    def info(self) -> IndexInfo: ...
class Clock(Protocol):
    def now(self) -> dt.datetime: ...                            # tz-aware America/Chicago (R-3)
class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> AbstractContextManager[SpanHandle]: ...
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...
```

**Import lines for `tests/fakes/*.py` (PD-14).** Each file imports only what it uses:

```python
from meridian.domain.common import CallRecord, ProviderCall, ProviderFailure, ProviderFailureKind, ProviderName
from meridian.domain.records import Passage, RetrievalResult
from meridian.domain.turn import ExportStatus, SpanHandle, TurnIds
from meridian.ports.models import (Attempt, ChoiceAnswer, ChoiceRequest, ProviderMessages, StructuredRequest, ToolStep,
                                   ToolStepRequest)
from meridian.ports.runtime import IndexInfo
```

**In the test file**, also import `Role` and `LLMFacing` (`meridian.domain.common`); `ChoiceField` and `ToolCall`
(`meridian.ports.models`); and the Protocols `ChoiceModel`, `StructuredModel`, `ToolCallingModel` and `ToolTranscript`
(`meridian.ports.models`) and `Clock`, `RetrievalIndex` and `TraceSink` (`meridian.ports.runtime`).

**Allowed imports in `tests/fakes/*.py`:** the standard library, `pydantic`, and `meridian.domain.*` /
`meridian.ports.*`. Nothing else: no `pytest`, no `logging`, no `meridian.adapters`, `agent`, `services`, `web` or
`config`. Start each file with a one-line docstring, then `from __future__ import annotations`.

---

## 5. Steps

This slice **implements** these interfaces: `ChoiceModel`, `StructuredModel`, `ToolCallingModel` (and so
`ToolTranscript`), `Clock`, `RetrievalIndex` and `TraceSink`. It **consumes** nothing else and adds no new seam.

### Step 1. Preconditions (stop and report if any fails)

Run in the worktree with `export UV_LINK_MODE=hardlink`.

1. `git log --oneline main -8` shows AEA-02 merged (AEA-01 is already there: `893b825`). `uv sync` exits 0.
2. `ls tests/__init__.py tests/fakes/__init__.py tests/unit/__init__.py tests/journeys/affected.py` all exist (AEA-01).
3. This command exits 0:
   ```
   uv run python -c "import meridian.ports.models, meridian.ports.runtime, meridian.domain.common, meridian.domain.records, meridian.domain.turn"
   ```
4. **How `provider` is declared.** Run `grep -n "provider" src/meridian/ports/models.py`. Each of `ChoiceModel`,
   `StructuredModel` and `ToolCallingModel` must show `provider: ClassVar[ProviderName]`. If it is a `@property` or a
   plain annotation instead, **stop** and send the slice back to the planner: PD-9 depends on the ClassVar form.
5. **Defining modules.** Run
   ```
   grep -rn "^class ProviderFailure\b\|^class ProviderCall\b\|^class CallRecord\b\|^ProviderName\|^class RetrievalResult\b\|^class Passage\b\|^ExportStatus\|^class SpanHandle\b\|^class TurnIds\b" src/meridian
   ```
   Every name should be in the module §4 gives it. If one is elsewhere, import it from where it is defined and note it
   in the report.
6. **`ProviderTurn`:** `grep -n "ProviderTurn" src/meridian/ports/models.py` should show `ProviderTurn = JsonValue`.
   The tests then use `_RAW: JsonValue = {"role": "assistant"}`. If it is a model class instead, build it from its
   required fields with neutral values and note it.
7. **The structured type parameter:** `structured` must read
   `def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]`. The fake copies it
   exactly.

### Step 2. `tests/fakes/models.py`

Module docstring: "Scripted model-port fakes (AEA-11). No vendor SDK, no network, no logging."

1. **`ScriptExhaustedError(BaseException)`.**
   - Docstring: "A model fake was called more often than its script allows. Derives from BaseException so
     `except Exception` in the code under test cannot hide it (PD-3)."
   - Message: `f"{owner} script exhausted after {n} calls"`. Only the class name and the count; never request text.
2. **`ScriptedFailure`**: `@dataclass(frozen=True)` with these fields:
   - `kind: ProviderFailureKind`
   - `http_status: int | None = None`
   - `retry_after_s: float | None = None`
   - `retryable: bool | None = None`
3. **`provider_call(...) -> ProviderCall`** (public, so tests can build prebuilt Attempts). Full signature:
   ```python
   def provider_call(*, provider: ProviderName, model: str, failure: ProviderFailure | None = None,
                     stop_reason: str | None = None, latency_ms: int = 0, input_tokens: int = 0,
                     output_tokens: int = 0, cache_read_tokens: int = 0, cache_write_tokens: int = 0,
                     thinking_tokens: int = 0, cost_usd: float = 0.0,
                     cost_source: Literal["reported", "price_table"] = "price_table",
                     provider_request_id: str | None = None) -> ProviderCall
   ```
   It returns a `ProviderCall` with `status = "error" if failure is not None else "ok"` and every other field as given.
4. **Private helpers.**
   - `_RETRYABLE_KINDS = frozenset({TIMEOUT, CONNECTION, RATE_LIMITED, OVERLOADED, SERVER})` and
     `_BODY_RETRYABLE_CODES = frozenset({408, 429, 500, 502, 503, 504, 529})`.
   - `_default_retryable(kind, http_status) -> bool` (PD-5).
   - `_failure(provider, model, kind, *, http_status, retry_after_s, retryable) -> tuple[ProviderFailure, ProviderCall]`.
     It builds:
     - `ProviderFailure(kind=kind, provider=provider, http_status=http_status, retry_after_s=retry_after_s, retryable=<given or default>, provider_request_id=None)`;
     - `provider_call(provider=…, model=…, failure=f, stop_reason=…)`, where `stop_reason` is `"refusal"` for `REFUSAL`,
       `"max_tokens"` for `MAX_TOKENS`, and `None` otherwise.
   - `_invalid_output(provider, model)` = `_failure(…, INVALID_OUTPUT, http_status=200, retry_after_s=None, retryable=False)`.
   - `_check_prebuilt(entry: Attempt[Any], provider: ProviderName, model: str) -> None` (PD-2):
     - `isinstance(entry.record, CallRecord)` → `ValueError("scripted Attempt carries a CallRecord; fakes return a ProviderCall")`;
     - `entry.record.provider != provider or entry.record.model != model` →
       `ValueError("scripted Attempt is for another provider or model")`.
   - `class _Script[E]`: holds a `list[E]`, an index and the owner name. `take() -> E` raises `ScriptExhaustedError`
     when the list is used up. Also a `remaining` property. The **caller** holds the fake's lock around `take()` and
     the recording (PD-10).
5. **`FakeChoiceModel`**
   - Class variables: `provider: ClassVar[ProviderName] = "openrouter_jev"` and
     `DEFAULT_MODEL: ClassVar[str] = "typesafe/jev-1.13"`.
   - Constructor:
     ```python
     def __init__(self, script: Sequence[ChoiceAnswer | ScriptedFailure | Attempt[ChoiceAnswer]], *,
                  model: str | None = None) -> None
     ```
     Set `self._model = model if model is not None else self.DEFAULT_MODEL`. Check each entry: any other type →
     `TypeError`; Attempts go through `_check_prebuilt(entry, self.provider, self._model)`.
   - Public lists: `requests: list[ChoiceRequest]` and `timeouts: list[float]`.
   - Read-only properties: `model` and `remaining: int`.
   - `choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]`, under the lock:
     1. `entry = self._script.take()`. This may raise `ScriptExhaustedError`, and an exhausted call records nothing.
        Then append `req` to `requests` and `timeout_s` to `timeouts`.
     2. An `Attempt` → return it unchanged.
     3. A `ScriptedFailure` → `f, call = _failure(…)`, then
        `return Attempt[ChoiceAnswer](value=None, record=call, failure=f)`.
     4. A `ChoiceAnswer` → run the PD-6 check. On a mismatch, return the `_invalid_output` Attempt. Otherwise
        `return Attempt[ChoiceAnswer](value=entry, record=provider_call(provider=self.provider, model=self._model), failure=None)`.
6. **`FakeAnthropicChoiceModel(FakeChoiceModel)`**: only `provider: ClassVar[ProviderName] = "anthropic"` and
   `DEFAULT_MODEL: ClassVar[str] = "claude-sonnet-5-5"`, with a docstring ("The Anthropic `ChoiceModel` stand-in, e.g.
   for the planner fallback"). No other override.
7. **`FakeStructuredModel`**
   - Class variables: `provider: ClassVar[ProviderName] = "anthropic"` and
     `DEFAULT_MODEL: ClassVar[str] = "claude-sonnet-5-5"`.
   - Constructor:
     ```python
     def __init__(self, script: Sequence[BaseModel | Mapping[str, Any] | ScriptedFailure | Attempt[Any]], *,
                  model: str | None = None) -> None
     ```
     Same checks as the choice fake. Public lists `requests: list[StructuredRequest[Any]]` and `timeouts`.
   - `def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]`. Same flow as
     `choose`. Bare values follow PD-7; a success has `stop_reason="end_turn"`. Build Attempts as PD-16 says.
   - **Check order matters:** test `isinstance(entry, Attempt)` first, then `isinstance(entry, ScriptedFailure)`, then
     `isinstance(entry, BaseModel)`, then `Mapping`. An `Attempt` is itself a `BaseModel`.
8. **`FakeToolModel`**
   - Class variables: `provider: ClassVar[ProviderName] = "anthropic"` and
     `DEFAULT_MODEL: ClassVar[str] = "claude-sonnet-5-5"`.
   - Constructor:
     ```python
     def __init__(self, script: Sequence[ToolStep | ScriptedFailure | Attempt[ToolStep]], *,
                  model: str | None = None) -> None
     ```
   - Public lists:
     - `requests: list[ToolStepRequest]`
     - `timeouts: list[float]`
     - `starts: list[str]`
     - `appends: list[tuple[ProviderMessages, ToolStep, tuple[tuple[str, str], ...]]]`
   - `start(self, user: str) -> ProviderMessages`: record `user` in `starts`, then return
     `ProviderMessages(provider=self.provider, model=self._model, items=({"role": "user", "content": user},))`.
   - `tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]`: same flow as `choose`. A bare
     `ToolStep` gives `Attempt[ToolStep](value=entry, record=provider_call(..., stop_reason=entry.stop_reason), failure=None)`.
   - `append(self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]) -> ProviderMessages`:
     1. If `messages.provider != self.provider or messages.model != self._model`, raise
        `ValueError("ProviderMessages were built for another provider or model")`. Nothing is recorded.
     2. Record `(messages, step, tuple(results))` in `appends`.
     3. Build the new items (PD-8). Annotate to help mypy:
        `calls: list[JsonValue] = [{"id": c.id, "name": c.name, "args": c.args} for c in step.tool_calls]`.
        If mypy still rejects a literal, wrap it in `cast(JsonValue, …)`.
     4. `return ProviderMessages(provider=self.provider, model=self._model, items=messages.items + tuple(new_items))`.
   - No method of any fake calls `print`, `logging`, `open`, `time.*` or `datetime.now`.

### Step 3. `tests/fakes/clock.py` (data.md §8a exactly, plus PD-11)

```python
CHICAGO = ZoneInfo("America/Chicago")
WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=CHICAGO)
    # [Source: docs/data/worked-pairs.md header "Friday 2026-10-16, 10:00"]; same instant as cases.md DEMO_START

class FixedClock:                                     # implements Clock (DO-4 §13)
    def __init__(self, at: datetime = WORKED_PAIRS_NOW) -> None: ...
    def now(self) -> datetime: ...                    # returns `at`, the same object on every call
    def advanced(self, by: timedelta) -> FixedClock: ...     # a NEW clock; this one never moves
```

1. `__init__`:
   - if `at.tzinfo is None or at.utcoffset() is None` → `ValueError("FixedClock needs a tz-aware datetime (R-3)")`;
   - if `not isinstance(at.tzinfo, ZoneInfo) or at.tzinfo.key != "America/Chicago"` →
     `ValueError("FixedClock needs America/Chicago (R-3)")`;
   - store `self._at = at`. No setter, no `set`, no `advance` (R-G-9 withdrew them).
2. `now()` returns `self._at`.
3. `advanced(by)` returns `FixedClock((self._at.astimezone(UTC) + by).astimezone(CHICAGO))` (`from datetime import UTC`).
4. `__repr__` returns `f"FixedClock({self._at.isoformat()})"`. It helps assertion output, and dates are not personal data.

### Step 4. `tests/fakes/index.py`

`FakeIndex`, following PD-12:

- Constructor:
  ```python
  def __init__(self, passages: Sequence[Passage] = (), *, by_query: Mapping[str, Sequence[Passage]] | None = None,
               info: IndexInfo | None = None) -> None
  ```
  Store tuples. Add a public `searches: list[tuple[str, int, float]]` and a lock.
- `search(self, query: str, *, k: int, min_score: float) -> RetrievalResult`, under the lock:
  1. Record `(query, k, min_score)`.
  2. `pool = self._by_query[query] if query in self._by_query else self._passages`.
  3. `cleared = [p for p in pool if p.score >= min_score]`.
  4. `ranked = sorted(cleared, key=lambda p: p.score, reverse=True)` (stable).
  5. `return RetrievalResult(passages=tuple(ranked[: max(k, 0)]), below_floor=not cleared)`.

  Passages come back as configured: the same objects, scores untouched.
- `info(self) -> IndexInfo` returns the given `info`, else the PD-12 default. Constants: `FAKE_INDEX_DIMENSION = 384`,
  `FAKE_INDEX_FILES = 17`.
- It imports nothing from `fastembed`, `numpy` or `meridian.adapters`.

### Step 5. `tests/fakes/trace.py`

```python
@dataclass(frozen=True)
class RecordedModelCall:
    record: CallRecord; masked_input: str; masked_output: str

@dataclass(frozen=True)
class RecordedNode:
    name: str; elapsed_ms: int; status: str

@dataclass(eq=False)                                  # identity equality: a handle's native is THIS object
class RecordedTurn:
    ids: TurnIds
    trace_id: str
    model_calls: list[RecordedModelCall] = field(default_factory=list)
    nodes: list[RecordedNode] = field(default_factory=list)
    closed: bool = False

class InMemoryTraceSink:                              # implements TraceSink (models.md §4)
    def __init__(self, *, status: ExportStatus = "sent") -> None: ...
    @property
    def turns(self) -> tuple[RecordedTurn, ...]: ...  # in opening order
    def spans_for(self, handle: SpanHandle) -> RecordedTurn: ...
    @contextmanager
    def turn(self, ids: TurnIds) -> Iterator[SpanHandle]: ...   # satisfies -> AbstractContextManager[SpanHandle]
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...
```

Put one field per line in the real file (the `;` above is shorthand; ruff `E702` rejects it).

1. **`turn(ids)`.** Under the lock: `n = len(self._turns) + 1`, then
   `rec = RecordedTurn(ids=ids, trace_id=format(n, "032x"))`, then append it. Build
   `handle = SpanHandle(turn_id=ids.turn_id, trace_id=rec.trace_id, native=rec)`. Then `try: yield handle` with
   `finally: rec.closed = True`. Use `@contextlib.contextmanager`. The scratch run confirmed that it satisfies a
   Protocol member returning `AbstractContextManager[...]`.
2. **`_own(handle) -> RecordedTurn`.** Return `handle.native` if it **is** (identity) one of `self._turns`. Otherwise raise
   `ValueError("span handle was not opened by this sink")`. A closed turn is still owned.
3. **`model_call` / `node`.** Call `_own(parent)`, then append `RecordedModelCall(record, masked_input, masked_output)` or
   `RecordedNode(name, elapsed_ms, status)` under the lock. **Store the strings exactly as given. Never mask, trim or pass
   them through any redaction** (DO-6 *Capture verification*).
4. **`export_status(turn)`.** Call `_own(turn)`, then return `self._status`.
5. **`spans_for(handle)`.** Return `_own(handle)`.

### Step 6. `tests/fakes/__init__.py`

- Docstring: "Shared test doubles for the DO-4 ports (AEA-11). Import from here: `from tests.fakes import FixedClock`."
- Re-export with explicit `from tests.fakes.models import (...)` lines (and the same for `clock`, `index` and `trace`).
- Add an `__all__` listing these names, sorted as ruff `RUF022` wants:
  `CHICAGO`, `WORKED_PAIRS_NOW`, `FakeAnthropicChoiceModel`, `FakeChoiceModel`, `FakeIndex`, `FakeStructuredModel`,
  `FakeToolModel`, `FixedClock`, `InMemoryTraceSink`, `RecordedModelCall`, `RecordedNode`, `RecordedTurn`,
  `ScriptExhaustedError`, `ScriptedFailure`, `provider_call`.
- If ruff orders them differently, take ruff's fix (`uv run ruff check --fix tests/fakes/__init__.py`).

### Step 7. Tests

Create `tests/unit/fakes/__init__.py` (empty) and write `tests/unit/fakes/test_fakes.py` (§7.1). Iterate with §7.3
rows 1–4.

If a §7.1 expectation fails, fix the fake toward this plan; **do not change an expected value**. If the plan looks wrong
(for example, an AEA-02 shape differs), stop and send it back to the planner.

### Step 8. Commit 1 (code and tests)

```
git add tests/fakes/__init__.py tests/fakes/models.py tests/fakes/clock.py tests/fakes/index.py tests/fakes/trace.py tests/unit/fakes/__init__.py tests/unit/fakes/test_fakes.py
```

Message:

```
test: scripted fakes for the DO-4 ports (AEA-11)

FakeChoiceModel (+ FakeAnthropicChoiceModel), FakeStructuredModel,
FakeToolModel (ProviderCall records, scripted failures, loud
exhaustion), FixedClock, FakeIndex, InMemoryTraceSink. No vendor SDK,
network or disk.
Refs #11

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

Note the short SHA (`git rev-parse --short HEAD`); steps 9 and 10 cite it.

### Step 9. Journey record `docs/testing/journeys/<YYYY-MM-DD>-AEA-11.md` (AC-13)

The folder exists on `main`. Follow the layout of `docs/testing/journeys/2026-10-21-AEA-04.md` and fill in each `<…>`:

```markdown
# Journey record: AEA-11 test support fakes

| Field | Value |
|---|---|
| Claim | The DO-4 port fakes in `tests/fakes/` honour their ports (AEA-11 AC-1…AC-12). No deterministic journey reaches this code (pattern D, `docs/plans/ux-join/backend-amendments.md` §3): journeys use AEA-57's scripted adapter at the provider boundary, not these fakes. |
| Level | `mock-tested` |
| Tested revision | `<commit-1 short SHA>` |
| Environment | VPS worktree `inno-aea-callcenter-wt/AEA-11`; Python 3.12 via `uv`; no server, no database, no model, no network |
| Command | `uv run pytest tests/unit/fakes/test_fakes.py -q`; `uv run python -m tests.journeys.affected --base main --list-only` |
| Result | <N passed in Xs>; `0 journeys affected` |
| Evidence location | GitLab issue #11 comment; this file. Proved instead by `tests/unit/fakes/test_fakes.py` and, later, by every unit, service and graph test that imports `tests.fakes` |
| Remaining limitations | Fakes prove shape compatibility only; real-adapter behaviour is proved by AEA-17/18/19 contract tests on recorded fixtures |
| Blocked by | none (no journey path by design; pattern D) |
```

Put no secrets, phone numbers or transcript text in it.

### Step 10. Context (AC-14) and commit 2

1. **`.claude/reference/area-map.md`, A0 row** (`| 0 | **A0 Foundation** | …`). Change **only its last cell**. On `main`
   at `16ca639` the cell reads
   `partly built: `policy/texts.py` actual (AEA-03, `2689582`); `privacy/redact.py` actual (AEA-04, `9145044`); AEA-01 (…); the rest planned`.
   AEA-02 and AEA-10 may have extended it since. Insert `` `tests/fakes/` actual (AEA-11, `<sha>`); `` immediately
   before `the rest planned`. If the cell no longer contains `the rest planned`, append
   `` ; `tests/fakes/` actual (AEA-11, `<sha>`) `` at the end. Touch no other cell.
2. **`.claude/state/icm-progress.md`, row *Routes verified against code and tests*.** On `main` there are **two** rows
   with that name: one ending `… verified at the wave-0 seam audit |` (AEA-04) and one ending
   `… verified when every area-map row is actual |` (AEA-03). Edit **only the second**: the one whose last cell starts
   `Each slice adds its route`. If only one such row exists by then, edit that one. Keep its status, and **replace only
   its evidence cell** (context-maintenance rule 6) with:
   `2026-10-21: area map A0 → [`tests/fakes/`](../../tests/fakes/) checked by [`tests/unit/fakes/test_fakes.py`](../../tests/unit/fakes/test_fakes.py) (AEA-11, `<sha>`; <N> pass)`.
   Use the run date if it is not 2026-10-21. The whole row must stay ≤ 400 characters. Do not merge or delete the
   duplicate row (§8 reports it).
3. **`docs/design/code-design.md` §9 ("## 9. Test layout").** Add one line directly after the closing ```` ``` ```` of
   the test-layout tree and before the line starting `- **What each role runs:**`, with a blank line before and after:
   `**Built on `main`:** `tests/fakes/` (AEA-11, `<sha>`); the rest of this tree is planned.`
   If a `**Built on `main`:**` line already exists in §9, insert `` `tests/fakes/` (AEA-11, `<sha>`); `` right after its
   colon instead. Touch nothing else in DO-3.
4. **Commit 2:**
   ```
   git add docs/testing/journeys/<YYYY-MM-DD>-AEA-11.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md
   ```
   Message: `docs: AEA-11 journey record and context rows`, a blank line, `Refs #11`, a blank line, then
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
5. `git diff --name-only main...HEAD` lists exactly the §2 owned files (AC-14 evidence).

### What the implementer must NOT do

- **Types:** don't define or redefine any port or domain type (`ProviderCall`, `Attempt`, `SpanHandle`, `ExportStatus`,
  …); import them.
- **`CallRecord`:** don't build one anywhere in `tests/fakes/` (that is the gateway's job, MOD-1). Tests may build one to
  feed the sink.
- **`provider`:** don't add a `provider=` constructor argument, a per-instance `provider` attribute or a `@property`
  named `provider` (PD-9). Don't add Jev structured or Jev tool fakes.
- **Imports:** don't import `anthropic`, `httpx`, `langfuse`, `fastembed`, `numpy`, `pytest` or `logging` in
  `tests/fakes/`, or anything from `meridian.adapters`, `meridian.agent`, `meridian.services`, `meridian.web`,
  `meridian.config` or `docs/parked/**`.
- **Scope:** don't add `temp_sqlite()`, recorded provider fixtures, a fake for a service (S-20), a mutating clock (`set`,
  `advance`), or a default answer when a script runs out.
- **Sink:** don't mask, trim or redact anything in `InMemoryTraceSink`.
- **Side effects:** a fake never reads the wall clock (`datetime.now`, `utcnow`, `date.today`, `time.time`) or writes
  files, logs or stdout.
- **Data:** never put a secret, verification code, card-like number or full phone number in any fixture, test id or
  message.
- **Files and git:** don't edit `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/__init__.py`, `src/**`, another
  ticket's tests, `apps/web/**`, `docs/ux/**`, the OpenAPI file or `.claude/state/build-ledger.md`. Don't use
  `git add -A`, push, force-push, download `pytest-xdist`, or run `pytest -n` above 2.

---

## 6. Data and fixtures

Everything is synthetic and written inline in the test file. No seeds are needed (fixed literals), and nothing comes
from the issued data or transcripts.

- **IDs.** `str(uuid.uuid4())` for `thread_id`, `turn_id` and `request_id` (canonical lower-case uuid4, matching
  AEA-02's pattern). Build ID-bearing models with `model_validate({...})`.
  - Helper `_ids() -> TurnIds`:
    `TurnIds.model_validate({"thread_id": …, "turn_id": …, "request_id": …, "run_tag": "live", "run_id": None, "agent_version": "test"})`.
- **Passages.** Helper `_passage(n: int, score: float, text: str = "Synthetic passage") -> Passage`:
  ```python
  Passage.model_validate({"passage_id": f"policies/fake_policy.md#{n}", "file": "policies/fake_policy.md",
                          "section": f"Section {n}", "version_label": "undated", "version_date": None,
                          "text": text, "score": score})
  ```
  This matches `PassageId`'s `^[^#\s]+#[0-9]+$`.
- **Choice request.**
  ```python
  ChoiceRequest(system="Pick the intent.", state={},
                fields=(ChoiceField(name="intent", instructions="Which intent?",
                                    options={"book": "Book a visit", "other": "Anything else"}),))
  ```
  `answer_ok = ChoiceAnswer(choices={"intent": "book"}, probabilities=None)`.
- **Structured output models** (test-local):
  - `class _Out(LLMFacing): answer: str`;
  - `class _Other(LLMFacing): note: str`, for the wrong-class case;
  - the request: `StructuredRequest[_Out](system_prefix="P", system_dynamic="D", user="U", output_model=_Out, max_tokens=200, effort=None)`.
- **Tool step.**
  `ToolStep(text="", tool_calls=(ToolCall(id="call_1", name="kb_search", args={"query": "fees"}),), raw=_RAW, stop_reason="tool_use")`,
  with `_RAW` per step 1.6.
- **Tool request.**
  `ToolStepRequest(system_prefix="P", system_dynamic="D", messages=<from fake.start("u")>, tools=(), max_tokens=500, effort=None)`.
- **Call record for the sink.**
  `CallRecord.from_provider(provider_call(provider="anthropic", model="claude-sonnet-5-5"), role=Role.RESPONDER, attempt=1)`.
- **Reading a `JsonValue` item.** `ProviderMessages.items` is `tuple[JsonValue, ...]`, which mypy will not index. Use a
  helper `_item(m: ProviderMessages, i: int) -> dict[str, JsonValue]` that does `item = m.items[i]`,
  `assert isinstance(item, dict)`, `return item`.
- **Sentinel (AC-12).** `"zq" + uuid.uuid4().hex[:12]`.
- **Whitespace.** `MeridianModel` strips string whitespace (`str_strip_whitespace=True`). Never put leading or trailing
  spaces in an expected request string.

---

## 7. Checks

### 7.1 `tests/unit/fakes/test_fakes.py`: the tests to write with the code

- Annotate every test `-> None`, and annotate fixture parameters: `capsys: pytest.CaptureFixture[str]`,
  `caplog: pytest.LogCaptureFixture`, `monkeypatch: pytest.MonkeyPatch`, `tmp_path: Path`.
- Define `REPO = Path(__file__).resolve().parents[3]`.
- Import the fakes from `tests.fakes` (the package API). Import the port Protocols and types from the modules §4 names.

| Test | What it does and asserts |
|---|---|
| `test_fakes_satisfy_protocols` (AC-1) | **Static half.** Typed assignments that mypy checks: `c1: ChoiceModel = FakeChoiceModel([])`, `c2: ChoiceModel = FakeAnthropicChoiceModel([])`, `s: StructuredModel = FakeStructuredModel([])`, `t: ToolCallingModel = FakeToolModel([])`, `tt: ToolTranscript = FakeToolModel([])`, `ck: Clock = FixedClock()`, `ix: RetrievalIndex = FakeIndex()`, `ts: TraceSink = InMemoryTraceSink()`. **Runtime half.** Write a helper `_assert_structural(proto: type, impl: object)`: (1) collect public member names over `proto.__mro__`, skipping `object`, `typing.Protocol` and `typing.Generic`, from `vars(klass)` and `klass.__dict__.get("__annotations__", {})`, ignoring names that start with `_`; (2) assert each name exists on `impl`; (3) for each name that is a function on the Protocol, assert `[(p.name, p.kind) for p in inspect.signature(...).parameters.values()]` is equal for `getattr(proto, name)` and `getattr(type(impl), name)`. Run it for the eight pairs. Also assert `c1.provider == "openrouter_jev"`, `c2.provider == "anthropic"` and `s.provider == t.provider == "anthropic"` |
| `test_scripted_attempts_in_order_with_provider_call` (AC-2) | **Choice fake** (Jev), script `[answer_ok, ScriptedFailure(TIMEOUT), ScriptedFailure(BODY_ERROR, http_status=503)]`; the three calls return in order. Call 1: `value is answer_ok`, `failure is None`, `type(record) is ProviderCall`, `record.status == "ok"`, `record.provider == "openrouter_jev"`, `record.model == "typesafe/jev-1.13"`. Calls 2 and 3: `value is None`; `failure.kind` is `TIMEOUT` / `BODY_ERROR`; `record.failure == failure`; `record.status == "error"`; `type(record) is ProviderCall`; `not isinstance(record, CallRecord)`; `not hasattr(record, "role")`; `not hasattr(record, "attempt")`; `failure.provider == "openrouter_jev"`. **The same pattern once each**, provider `"anthropic"`, for `FakeStructuredModel` (`[_Out(answer="a"), ScriptedFailure(OVERLOADED)]`) and `FakeToolModel` (`[step, ScriptedFailure(RATE_LIMITED, retry_after_s=2.0)]`, asserting `failure.retry_after_s == 2.0`). No call raises |
| `test_exhausted_script_fails_loudly` (AC-3) | `FakeChoiceModel([answer_ok])`: the first call is ok; the second raises (`pytest.raises(ScriptExhaustedError)`). A wrapper `def swallow() -> object: try: return fake.choose(req, timeout_s=3.0) except Exception: return None` still raises `ScriptExhaustedError`, which proves `except Exception` cannot hide it. Assert `issubclass(ScriptExhaustedError, BaseException)` and `not issubclass(ScriptExhaustedError, Exception)`. `FakeStructuredModel([])` and `FakeToolModel([])` raise it on the first `structured` / `tool_step`. The error message contains the class name and no request text (`"Pick the intent" not in str(err)`) |
| `test_choice_outside_options_is_invalid_output` (AC-4) | Script `[ChoiceAnswer(choices={"intent": "cancel_everything"}, probabilities=None), ChoiceAnswer(choices={}, probabilities=None), ChoiceAnswer(choices={"intent": "book", "extra": "x"}, probabilities=None)]`. Each returns `value is None`, `failure.kind is ProviderFailureKind.INVALID_OUTPUT`, `failure.retryable is False` and `record.status == "error"`. A fourth entry, `ChoiceAnswer(choices={"intent": "book"}, …)`, returns ok |
| `test_tool_fake_append_refuses_foreign_messages` (AC-5) | `fake = FakeToolModel([step])`. `m0 = fake.start("hello")` → `m0.provider == "anthropic"`, `m0.model == "claude-sonnet-5-5"`, `len(m0.items) == 1`. `m1 = fake.append(m0, step, [("call_1", '{"ok": true}')])` → `m1.items[:1] == m0.items`, `len(m1.items) == 3`, `_item(m1, 1)["role"] == "assistant"`, `_item(m1, 2)["role"] == "tool_results"`. `fake.append(m1, step, [])` adds exactly 1 item. **Foreign messages:** `ProviderMessages(provider="anthropic", model="claude-opus-x", items=())` and `ProviderMessages(provider="openrouter_jev", model="claude-sonnet-5-5", items=())` each raise `ValueError` (`pytest.raises`). Afterwards `len(fake.appends) == 2` (refused calls are not recorded) |
| `test_requests_recorded_in_order` (AC-6) | Choice fake with 3 entries and three distinct requests (`system="turn 1"`, `"turn 2"`, `"turn 5"`), `timeout_s` 3.0, 2.5, 1.0 → `fake.requests == [r1, r2, r3]`, `fake.requests[i] is r_i`, `fake.timeouts == [3.0, 2.5, 1.0]`, `fake.remaining == 0`. The same for structured (3 requests) and for tool (`tool_step` × 3; `starts == ["u"]` after one `start`) |
| `test_fixed_clock` (AC-7) | `c = FixedClock()`. Assert: `c.now() == datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))`; `c.now() is c.now()`; `isinstance(c.now().tzinfo, ZoneInfo) and c.now().tzinfo.key == "America/Chicago"`; `c.now().strftime("%A") == "Friday"`. Then `d = c.advanced(timedelta(hours=1))` → `d is not c`, `d.now().hour == 11`, `c.now().hour == 10`. Finally `WORKED_PAIRS_NOW == c.now()` |
| `test_fixed_clock_refuses_naive_and_foreign_tz` (AC-8) | `pytest.raises(ValueError)` for each of: `FixedClock(datetime(2026, 10, 16, 10, 0))`, `FixedClock(datetime(2026, 10, 16, 15, 0, tzinfo=UTC))`, `FixedClock(datetime(2026, 10, 16, 10, 0, tzinfo=timezone(timedelta(hours=-5))))`, `FixedClock(datetime(2026, 10, 16, 11, 0, tzinfo=ZoneInfo("America/New_York")))`. Four refusals: the AC's two plus two foreign-zone variants |
| `test_fake_index_floor_and_info` (AC-9) | `ix = FakeIndex([_passage(1, 0.5), _passage(2, 0.9), _passage(3, 0.7)])`. **Hit case:** `search("fees", k=2, min_score=0.6)` → scores `(0.9, 0.7)`, `below_floor is False`. **Cap:** `k=1` → one passage (0.9). **Floor case:** `min_score=0.95` → `passages == ()`, `below_floor is True`. **Equal to the floor:** `min_score=0.7, k=5` → `(0.9, 0.7)`. **`info()`:** `embedding_model == "BAAI/bge-small-en-v1.5"`, `dimension == 384`, `files == 17`, `chunks == 3`. An `info=` passed to the constructor is returned unchanged |
| `test_trace_sink_handle_and_export_status` (AC-10) | `sink = InMemoryTraceSink()`. Open turn A; record `model_call(span_a, rec, "in A", "out A")` and `node(span_a, "gates", 3, "ok")`. Open turn B; record one node. Assert: `span_a.turn_id == ids_a.turn_id`; `span_a.trace_id == "0" * 31 + "1"` and `span_b.trace_id == "0" * 31 + "2"`; `sink.spans_for(span_a).model_calls == [RecordedModelCall(rec, "in A", "out A")]` and `.nodes == [RecordedNode("gates", 3, "ok")]`; B holds only its own node; both turns have `closed is True` after their blocks. After the blocks closed: `sink.export_status(span_a) == "sent"`, and the value is in `("off", "sent", "failed")`. `InMemoryTraceSink(status="failed").export_status(<its handle>) == "failed"`. `[t.ids for t in sink.turns] == [ids_a, ids_b]` |
| `test_fakes_import_no_vendor_sdk` (AC-11) | Run `subprocess.run([sys.executable, "-I", "-c", CODE], cwd=REPO, capture_output=True, text=True, check=False, timeout=120)`. `CODE` does three things: inserts `str(REPO)` and `str(REPO / "src")` at the front of `sys.path`; imports `tests.fakes` and constructs each of the seven fake classes once; prints `json.dumps(sorted(m for m in ("anthropic", "httpx", "langfuse", "fastembed") if m in sys.modules))`. Assert `returncode == 0` (show `stderr` in the message) and `json.loads(stdout.strip().splitlines()[-1]) == []` |
| `test_fakes_leak_nothing_and_sink_does_not_mask` (AC-12) | Setup: `caplog.set_level(logging.DEBUG)` and `monkeypatch.chdir(tmp_path)`. **Pass the sentinel through every fake:** choice request `system=f"S {sentinel}"`; structured `user=f"U {sentinel}"` with script `[_Out(answer=sentinel)]`; tool `start(sentinel)`, `tool_step` with `system_dynamic=sentinel`, and `append(..., [("call_1", sentinel)])`; index `search(sentinel, k=3, min_score=0.0)` over a passage whose text holds the sentinel; clock `now()` and `advanced(...)`; sink `model_call(span, rec, f"in {sentinel}", f"out {sentinel}")` and `node(span, "n", 1, "ok")`. **Nothing leaked:** `out, err = capsys.readouterr()`; the sentinel is not in `out`, not in `err`, not in `caplog.text` and not in any `r.getMessage()`; `list(tmp_path.iterdir()) == []`. **The sink holds it verbatim:** `sink.spans_for(span).model_calls[0].masked_input == f"in {sentinel}"` and `.masked_output == f"out {sentinel}"`. **Source scan** (`ast`) of every `REPO / "tests/fakes" / *.py`: no `import logging` / `from logging`; no call to a bare `print` or `open`; no attribute call named `write_text`, `write_bytes`, `mkdir`, `touch` or `unlink` |
| `test_structured_fake_validates_output_model` (S-1) | Script `[{"answer": "from dict"}, {"wrong": 1}, _Other(note="n"), _Out(answer="kept")]` on `StructuredRequest[_Out]`. Call 1 → `isinstance(value, _Out)` and `value.answer == "from dict"`. Calls 2 and 3 → `INVALID_OUTPUT`, `value is None`. Call 4 → `value is` the scripted `_Out` instance, and `attempt.model_dump()["value"] == {"answer": "kept"}` |
| `test_scripted_failure_retryable_defaults` (S-2) | Parametrised over `(kind, http_status, expected)`: `TIMEOUT, None, True`; `CONNECTION, None, True`; `RATE_LIMITED, None, True`; `OVERLOADED, 529, True`; `SERVER, 500, True`; `BODY_ERROR, 503, True`; `BODY_ERROR, 400, False`; `BODY_ERROR, None, False`; `BAD_REQUEST, 400, False`; `PROVIDER_SPEND_CAP, 402, False`; `REFUSAL, None, False` (and `record.stop_reason == "refusal"`); `MAX_TOKENS, None, False` (and `"max_tokens"`). Plus an override: `ScriptedFailure(TIMEOUT, retryable=False)` → `False`. Give readable `ids=` |
| `test_prebuilt_attempts_checked_at_construction` (S-3) | An own-provider prebuilt `Attempt[ChoiceAnswer](value=answer_ok, record=provider_call(provider="openrouter_jev", model="typesafe/jev-1.13", input_tokens=120, cost_usd=0.000005, cost_source="reported"), failure=None)` comes back **unchanged** (`is`). These raise `ValueError` at construction: an Attempt whose record is `CallRecord.from_provider(...)`; one with `provider="anthropic"` given to `FakeChoiceModel`; one with another model. The same `provider="anthropic"` Attempt with model `"claude-sonnet-5-5"` is **accepted** by `FakeAnthropicChoiceModel`. `FakeChoiceModel(["not an entry"])` raises `TypeError` (add `# type: ignore[list-item]`) |
| `test_fixed_clock_advances_by_elapsed_time` (S-4) | `start = FixedClock(datetime(2026, 11, 1, 0, 30, tzinfo=CHICAGO))`; `later = start.advanced(timedelta(hours=2)).now()`. Assert `later.astimezone(UTC) == datetime(2026, 11, 1, 7, 30, tzinfo=UTC)`, `later.utcoffset() == timedelta(hours=-6)` and `later.tzinfo.key == "America/Chicago"`. Also `FixedClock().advanced(timedelta(days=3)).now() == datetime(2026, 10, 19, 10, 0, tzinfo=CHICAGO)` (a Monday). The planner checked the DST arithmetic: 00:30 CDT + 2 h = 01:30 CST = 07:30 UTC |
| `test_fake_index_by_query_and_records_searches` (S-5) | `FakeIndex([_passage(1, 0.9)], by_query={"gas": [_passage(7, 0.8)]})`: `search("gas", k=3, min_score=0.5)` returns passage 7; `search("other", k=3, min_score=0.5)` returns passage 1; `ix.searches == [("gas", 3, 0.5), ("other", 3, 0.5)]`; `info().chunks == 2` |
| `test_trace_sink_refuses_foreign_handle_and_closes_on_error` (S-6) | A handle from another `InMemoryTraceSink`, and a bare `SpanHandle(turn_id=ids.turn_id, trace_id=None)`, each raise `ValueError` from `model_call`, `node`, `export_status` and `spans_for`. `with sink.turn(ids) as span: raise RuntimeError("boom")`, inside `pytest.raises(RuntimeError)`, leaves `sink.spans_for(span).closed is True`, and `sink.export_status(span) == "sent"` afterwards |
| `test_fakes_read_no_wall_clock` (S-7) | `ast` scan of `tests/fakes/*.py`: no call whose function is the attribute `now`, `utcnow` or `today` on a name `datetime` or `date`, and no `time.time` / `time.time_ns` call |
| `test_model_fake_is_thread_safe` (S-8) | `FakeChoiceModel([answer_ok] * 200)`. 8 threads (`concurrent.futures.ThreadPoolExecutor(max_workers=8)`) each call `choose` 25 times → 200 ok Attempts, `len(fake.requests) == 200`, `fake.remaining == 0`. One more call, in the main thread, raises `ScriptExhaustedError` |
| `test_provider_classvars_and_default_models` (S-9) | `FakeChoiceModel.provider == "openrouter_jev"`, `FakeAnthropicChoiceModel.provider == "anthropic"`, `FakeStructuredModel.provider == FakeToolModel.provider == "anthropic"` (read on the **class**). `"provider" not in vars(FakeChoiceModel([]))` (not an instance attribute). Default models: `FakeChoiceModel([]).model == "typesafe/jev-1.13"`; the other three `== "claude-sonnet-5-5"`; `FakeToolModel([], model="claude-x").model == "claude-x"`. `issubclass(FakeAnthropicChoiceModel, FakeChoiceModel)`. A `FakeAnthropicChoiceModel([answer_ok])` call returns a record with `provider == "anthropic"` and `model == "claude-sonnet-5-5"`, and a `ScriptedFailure` on it gives `failure.provider == "anthropic"` |

### 7.2 Affected scope

At this ticket's base, nothing imports `tests.fakes` yet, so the affected tests are `tests/unit/fakes/test_fakes.py`
only. Prove it with:

```
grep -rln "tests.fakes\|tests/fakes" tests/ src/ eval/ --include=*.py
```

It should list only files under `tests/fakes/` and `tests/unit/fakes/test_fakes.py`. If a merged wave-1 sibling already
imports `tests.fakes`, add its test files to row 4 below.

### 7.3 Commands (cheapest first; stop at the first red)

Run from the worktree root with `export UV_LINK_MODE=hardlink`:

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check tests/fakes tests/unit/fakes` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check tests/fakes tests/unit/fakes` | `… files already formatted` (run without `--check` to fix, then re-run) |
| 3 | Type check (while iterating) | `uv run mypy tests/fakes tests/unit/fakes` | `Success: no issues found in N source files` |
| 4 | Affected tests (while iterating) | `uv run pytest tests/unit/fakes/test_fakes.py -q` | all pass, no skips |
| 5 | Type check gate (once, before the final commit) | `uv run mypy` (the configured `files`: `src/meridian`, `tests`, `eval`) | `Success: no issues found` |
| 6 | Full suite (once, before the final commit) | `uv run pytest -q` (serial; do not add `pytest-xdist`) | all pass |
| 7 | Affected journeys | `uv run python -m tests.journeys.affected --base main --list-only`, then `uv run pytest -m journey --collect-only -q` | `0 journeys affected`; both exit 0 (no journey file exists until AEA-57) |
| 8 | Diff scope | `git diff --name-only main...HEAD` | exactly the §2 owned files |

**Why the full suite (row 6):** DO-3 §9 names `tests/fakes/` among the changes that run it, and `build-loop-test-scope`
counts a shared test fixture as "a change that reaches everything". It is small at this base (wave-0 tests plus AEA-02's).

No test calls a model, a network or a database, and no test uses the `live` marker.

### 7.4 Evidence the implementer reports, per criterion

- AC-1: the mypy line and the test pass.
- AC-2…AC-12 and S-1…S-9: the pass lines (`pytest -v` names).
- AC-11: the subprocess's `[]`.
- AC-13: the `0 journeys affected` output, the record path, and its Level and Blocked-by lines.
- AC-14: the `git diff --name-only` output.
- The step 1.4–1.7 findings: the `provider` ClassVar, the defining modules, `ProviderTurn`, and the `structured`
  signature.
- The four gate outputs (lint, format, mypy, tests) and the full-suite line, each with its command.

The verification level for every claim is `mock-tested`.

---

## 8. Risks and requests

**Collisions with other slices**

- **`tests/fakes/__init__.py`** is on `main`, empty (AEA-01). Filling it here is a plain modification, not a conflict.
- **Shared context rows.** `.claude/state/icm-progress.md` (*Routes verified…*), the A0 status cell of
  `.claude/reference/area-map.md`, and a `**Built on `main`:**` line in DO-3 may also be touched by AEA-02, 05, 10 and
  other wave-1 tickets. Step 10 inserts into the existing text rather than replacing it; at merge, keep both sides'
  entries.
- **The ICM file holds two rows named *Routes verified against code and tests*** (AEA-04's and AEA-03's, from their
  merges). Step 10 edits only the second and leaves the duplicate alone. **Request to the orchestrator:** fold the two
  into one row in a `lane::direct` housekeeping commit.
- **`docs/testing/journeys/`:** many tickets add their own dated file; no file is shared.

**API notes for sibling plans (the orchestrator relays them; nothing blocks)**

- **AEA-35** §4.3's comment lists `FakeToolModel(script, *, provider="anthropic", model="claude-sonnet-5-5")`. The
  `provider=` keyword no longer exists (PD-9). AEA-35's actual calls (`FakeToolModel([...steps...])`) pass no
  `provider`, so nothing breaks. Its implementer should simply not pass one.
- **AEA-20** builds its own adapter doubles (`JevChoice`, `SonnetChoice(JevChoice)`, …) with the same ClassVar pattern.
  This is consistent with these fakes and is no collision.
- **AEA-29, 30, 33, 34** use `FixedClock`, `FakeIndex` and `InMemoryTraceSink` exactly as planned here. Nothing changed
  for them.

**Shared primitives needed (from AEA-02; nothing new)**

- The §4 types with these exact names and homes. Step 1 confirms them.
- `provider` must be `ClassVar` on the Protocols. If AEA-02 lands another form, the slice comes back here.

**Behaviour recorded so reviewers don't read it as a bug**

- `ScriptExhaustedError` derives from `BaseException` on purpose (PD-3).
- A shared model fake is thread-safe but not order-deterministic across threads (PD-10). Graph tests with parallel
  specialists should give each role its own fake.
- `FakeIndex` ignores the query unless `by_query` names it. It never ranks by text similarity.
- `InMemoryTraceSink.export_status` returns one configured value for every turn it opened; it does not simulate a
  dropped span. AEA-40's `failed` path can build the sink with `status="failed"`.
- `FixedClock.advanced` adds elapsed time (PD-11). This only matters across 2026-11-01 02:00 CDT.
- No Jev structured or Jev tool fakes exist, because `JevAdapter` implements `ChoiceModel` only (models.md §2).

**Spec gaps (none blocking)**

- data.md §8a's comments cite "AEA-11 AC-6" for the constant `now()`. In the current ticket that criterion is AC-7 (the
  numbers shifted when AC-1 was added). No effect on the build.
- DO-4 §13's `export_status(self)` (no argument) is superseded by models.md §4 (`export_status(turn)`), as DO-4 §13's
  own *Superseded* note says. This plan follows the addendum.
- The ticket's *What to build* says the choice fake must report outside-options choices as `invalid_output`. It does not
  say what a missing or extra field does. PD-6 follows models.md §3's Jev row ("a field missing … → `INVALID_OUTPUT`").
- The ticket says each model fake exposes `provider` "`"anthropic"` or `"openrouter_jev"`". With ClassVar (AEA-02 D-4),
  that becomes one class per provider where a real adapter exists (PD-9). Same observable behaviour.

**Contract problems:** none. No signed contract (OpenAPI, `UI_CONTRACTS.md`) is touched, and no decision D-4…D-15 in
`docs/plans/stage7-signoff.md` is answered differently.

**Gates:** none (no human, external, paid or live gate).

---

## 9. Readiness

**READY**, with one merge-order prerequisite, which is a true import rather than a convenience: **blocked-on AEA-02** for
every type the fakes implement or return (`ports/models.py`, `ports/runtime.py`, `domain/{common,records,turn}.py`).

AEA-01 (package markers, mypy / ruff / pytest configuration, the affected-journey command) is merged on `main`. AEA-02 is
wave 0 and this ticket is wave 1, so no wave changes.

Start the implementer when AEA-02 is on `main`; step 1 stops it cleanly otherwise. There is no `NEEDS-DECISION`. Every
open choice is an engineering decision made in §3.1, inside the ticket's stated latitude: script entry forms, the
exhaustion error type, defaults, DST arithmetic, index ranking, sink handle identity, the ClassVar subclass, and how
Attempts are built.
