## [AEA-11] test support: scripted fakes

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

No user story applies: this is test infrastructure every later ticket uses to test against the DO-4 ports without a
paid call, a model download or a network.

`tests/fakes/` (DO-3 §9; slice plan row AEA-11) holds six doubles, each honouring its port exactly as DO-4 §12–§13 and
the Stage 7 addenda define it, so a test that passes on a fake means the same as it would on the real adapter (DO-3 S-1,
S-4, S-8, S-10):

- **`FakeChoiceModel`**, **`FakeStructuredModel`**, **`FakeToolModel`**: scripted implementations of `ChoiceModel`,
  `StructuredModel` and `ToolCallingModel` (DO-4 §12 method signatures, unchanged). Each returns the scripted `Attempt`
  per call in order, never raises, and always carries a **`ProviderCall`** in `Attempt.record` (no `role`, no `attempt`;
  the gateway wraps it as `CallRecord.from_provider`), also on a scripted failure, with the failure as a
  `ProviderFailure` of the scripted `ProviderFailureKind` (stage7/models.md §1, MOD-1; merge-clashes MC-28; DO-4 §11).
  Each exposes the read-only `provider: ProviderName` attribute the three port Protocols gain (models.md cross-topic 2),
  `"anthropic"` or `"openrouter_jev"`. The choice fake reports a choice outside its field's options as
  `invalid_output`, as the adapters do (DO-4 §12 contract; models.md §3). `FakeToolModel.start` / `append` build and
  extend a `ProviderMessages(provider, model, items)` (MOD-17) and `append` raises `ValueError` when the messages'
  `provider` or `model` is not its own, as models.md §1 says the adapters do. Each fake records every request it
  receives, so a test can assert the full prompt on turns 1, 2 and 5 (workspace rule
  `context-management-multi-turn.md` rule 3).
- **`FixedClock`** (`tests/fakes/clock.py`): exactly stage7/data.md §8a (DAT-32): `FixedClock(at=WORKED_PAIRS_NOW)`
  where `WORKED_PAIRS_NOW` is Friday 2026-10-16 10:00 America/Chicago (`docs/data/worked-pairs.md` header; the same
  instant as cases.md `DEMO_START`); `now()` returns `at` on every call; `advanced(by)` returns a **new** clock at
  `at + by` and this one never moves; a naive `at` or one whose tzinfo is not America/Chicago is a `ValueError` (R-3).
- **`FakeIndex`**: the `RetrievalIndex` port (DO-4 §13); `search(query, *, k, min_score)` returns configured passages
  that clear `min_score`, at most `k`, sets `below_floor` when none do, and `info()` answers the DO-4 `IndexInfo`
  shape; loads no embedding model.
- **`InMemoryTraceSink`**: the `TraceSink` port as models.md §4 changes it: `turn(ids)` yields a `SpanHandle`
  (`domain/turn.py`, graph-core §1), `model_call(parent, record: CallRecord, masked_input, masked_output)`,
  `node(parent, name, elapsed_ms, status)`, and `export_status(turn: SpanHandle) -> ExportStatus` (MOD-9). It is kept
  in memory for the capture tests (DO-3 §4.2) and stores exactly what callers pass: it masks nothing itself, so a
  caller that forgot to mask is caught by CAP-1 rather than hidden by the fake (DO-6 *Capture verification*: masking
  runs as in production, in the caller).

`temp_sqlite()` is not in this ticket: it is AEA-10's, in `tests/fixtures/sqlite.py` (slice plan §3; DAT-10, CAS-4).

**Example pair:** none — pure test infrastructure; it encodes no customer behaviour.

**Settled R-G-9** (`docs/plans/7b-decisions/residuals-graph.md`): data.md §8a is the definition; cases.md §6 points to
it (CAS-37's mutating sketch is withdrawn). A test that needs a moving clock builds a new consumer per moment from
`FixedClock(...)` / `.advanced(...)` (a `SchedulerJob` per tick is safe: its idempotency is in `case_events`), never a
second fake.

### Source

- DO-3 §9 (test layout, `tests/fakes/`), §4.2 (ports and their test implementations), §6 S-1, S-4, S-8, S-10, S-20
- DO-4 §11 (`ProviderFailureKind`, `ProviderFailure`), §12 (model ports and their contract), §13 (`RetrievalIndex`,
  `IndexInfo`, `RetrievalResult`, `Clock`, `TraceSink`); internal-components §16 (addenda win)
- stage7/models.md §1 (`ProviderName`, `ProviderCall`, `Attempt.record`, `ProviderMessages`, MOD-1, MOD-17), §3
  (failure mapping), §4 (`SpanHandle`, `ExportStatus`, `TraceSink.export_status(turn)`, MOD-9), cross-topic 2
- stage7/data.md §8a (`FixedClock`, DAT-32), §9 item 8 (MC-28); merge-clashes MC-28; ledger
  `docs/plans/7b-decisions/data.md` DAT-10, DAT-32
- stage7/graph-core.md §1 (`SpanHandle` in `domain/turn.py`, re-exported by `ports/runtime.py`)
- DO-6 observability-contract *Capture verification* (in-memory exporter, masking in production position)
- Workspace rule `.claude/rules/context-management-multi-turn.md` rule 3 (recording fake model); worked-pairs clock
- Slice plan §1 row AEA-11; §3 rows `tests/fakes/`, `tests/conftest.py`
- Residuals R-G-4 (`ProviderMessages.items`), R-G-9 (`FixedClock`) in `docs/plans/7b-decisions/residuals-graph.md`;
  journey criterion `docs/plans/ux-join/backend-amendments.md` §3
- **Brief check:** serves "Show the numbers, not just the claim." (every later criterion is proved by a test that runs
  without paid calls); touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Each fake satisfies its port Protocol structurally, including the model ports' read-only `provider` attribute — verify: the project's type check (as AEA-01 configures it) over `tests/fakes/` plus `tests/unit/fakes/test_fakes.py::test_fakes_satisfy_protocols` (assigns each fake to a variable typed by its Protocol) — evidence: type check clean; test passes.
- [ ] AC-2 [invariant] Scripted model fakes return their scripted `Attempt`s in order, never raise, and carry a `ProviderCall` (not a `CallRecord`: no `role`, no `attempt`) on success and on a scripted failure, with `provider` set and the scripted `ProviderFailureKind` in `Attempt.failure` (MC-28) — verify: `test_fakes.py::test_scripted_attempts_in_order_with_provider_call` — evidence: a `timeout` and a `body_error` script come back as `Attempt.failure` with `record` a `ProviderCall` whose `status` is `error`.
- [ ] AC-3 [failure/refusal] A model fake whose script is exhausted fails the test with a named error instead of answering by default (a model is never its own authority, DO-5) — verify: `test_fakes.py::test_exhausted_script_fails_loudly` — evidence: the named error raised in the test, not an answer.
- [ ] AC-4 [invariant] `FakeChoiceModel` returns a scripted choice that is not among the field's options as `invalid_output`, matching the adapters (DO-4 §12; models.md §3) — verify: `test_fakes.py::test_choice_outside_options_is_invalid_output` — evidence: `Attempt.value` None, failure kind `invalid_output`.
- [ ] AC-5 [failure/refusal] `FakeToolModel.append` refuses messages built for another provider or model with `ValueError` (a wiring bug, not an `Attempt.failure`; models.md §1, MOD-17) — verify: `test_fakes.py::test_tool_fake_append_refuses_foreign_messages` — evidence: `ValueError` raised; own messages extended in order.
- [ ] AC-6 [invariant] Each model fake records every request received, in order, readable by the test — verify: `test_fakes.py::test_requests_recorded_in_order` — evidence: three calls → three recorded requests equal to those sent.
- [ ] AC-7 [invariant] `FixedClock()` defaults to 2026-10-16 10:00 America/Chicago, `now()` returns the same value on every call, and `advanced(timedelta(hours=1))` returns a new clock at 11:00 while the original still reads 10:00 (data.md §8a) — verify: `test_fakes.py::test_fixed_clock` — evidence: `tzinfo` key America/Chicago; equal values; two clocks, two readings.
- [ ] AC-8 [failure/refusal] `FixedClock` refuses a naive datetime and a datetime in another time zone with `ValueError` (R-3: never a server wall clock) — verify: `test_fakes.py::test_fixed_clock_refuses_naive_and_foreign_tz` — evidence: two `ValueError`s.
- [ ] AC-9 [invariant] `FakeIndex.search` returns only configured passages at or above `min_score`, at most `k`, with `below_floor` True when none clear; `info()` returns `IndexInfo` with `embedding_model` `BAAI/bge-small-en-v1.5` — verify: `test_fakes.py::test_fake_index_floor_and_info` — evidence: the floor case and the hit case.
- [ ] AC-10 [invariant] `InMemoryTraceSink.turn(ids)` yields a `SpanHandle` carrying the turn id, the model-call and node spans recorded under it are readable by the test, and `export_status(span)` takes that handle and returns an `ExportStatus` value (models.md §4) — verify: `test_fakes.py::test_trace_sink_handle_and_export_status` — evidence: spans grouped by handle; status in `off | sent | failed`.
- [ ] AC-11 [negative] Importing `tests/fakes` loads none of `anthropic`, `httpx`, `langfuse`, `fastembed` (no paid call, no network, no model download in a default test) — verify: `test_fakes.py::test_fakes_import_no_vendor_sdk` — evidence: none of the four in `sys.modules` after a clean import in a subprocess.
- [ ] AC-12 [negative] The fakes write nothing to logs, stdout or disk: a distinctive value passed through every fake is absent from captured stdout, stderr and log records, and `InMemoryTraceSink` holds it verbatim (no masking of its own) — verify: `test_fakes.py::test_fakes_leak_nothing_and_sink_does_not_mask` — evidence: absent from `capsys`/`caplog`; present unchanged in the sink's recorded span.
- [ ] AC-13 [journey] No deterministic journey reaches this code (`tests/fakes/` serves unit tests; journeys use AEA-57's scripted adapter at the provider boundary), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-11.md` says so and names where it is proved instead (the unit tests that import the fakes) (`backend-amendments.md` §3, pattern D) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.
- [ ] AC-14 [regression/context] Docs updated in the same change — verify: `git diff --name-only` — evidence: `.claude/reference/area-map.md` A0 row (`tests/fakes/` planned → actual with the commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §9 status planned → built, all three in the diff.

### Observability

N/A — test support only; no production code path runs it. It supplies `InMemoryTraceSink`, which the capture tests of
AEA-51 (CAP-1…CAP-3), AEA-52 (CAP-4, CAP-5) and AEA-53 (CAP-6) use to find records; those tickets own the capture
evidence at the real entry points.

### Evaluation

N/A — the fakes decide no expected answer; scored evaluations run the real agent over HTTP with real models (DO-5
*Scoring*, harness HTTP only). Graph tests that use these fakes are tests, not E-n suites.

### Metrics

N/A — no metric is computed from fake output; M-23…M-26 come from real `spend_ledger` and `turn` rows, never from a
fake's `ProviderCall`.

### Blocked by

AEA-02; AEA-01 (the `journey` marker and affected-journey command AC-13 runs; wave 0, so no wave change)

### Agent handoff

- Area / owner: A0 test support (`tests/fakes/`).
- Contracts and shared surfaces: consumes the port Protocols and types in `ports/{models,runtime}.py` and `domain/*`
  (AEA-02, which transcribes models.md §1 and §4 and graph-core §1). Produces the six fakes for every later build ticket
  (AEA-12…AEA-53 test with them; AEA-29's promise tests build one `FixedClock` before and one after a due time; AEA-51
  uses `FixedClock` for the `Clock` port in 27, 28, 29, 40). Consumes AEA-01's affected-journey command for AC-13. Must not edit `tests/conftest.py` (AEA-01), `ports/*` or
  `domain/*` (AEA-02), or `tests/fixtures/sqlite.py` (AEA-10).
- Scope boundary / refusal: no `temp_sqlite()`; no test of any product module; no recorded provider fixtures (those are
  AEA-17, AEA-18 contract tests); a fake never imports a vendor SDK; a fake never builds a `CallRecord` (the gateway's
  job, MOD-1).
- Wave and gates: wave 1; no gate.
- Lane: build-loop — test fixtures that other tests read.
- Risk: None.
- Entry points added or changed: None
