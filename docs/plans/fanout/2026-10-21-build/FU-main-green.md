# Plan — [FU-main-green] main green: wf15 reset fixture row, stale affected-journeys test, tracing timing flake

**Status:** planned (READY) · **Lane:** `lane::build-loop` · **Risk:** none of its own (test-only diff; touches files of
`risk::security` tickets AEA-50 and AEA-19, see *Frozen files*)
**Issue:** wave-fix item, no issue · **Base revision:** `main` at `8669ed0` (2026-10-22)
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-22. **Implementer:** `fanout-implementer` (Sonnet).

## Goal

Three reds on integrated `main` block the pre-deploy full suite. Fix each at its cause; never skip, deselect or loosen.

1. `tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_script` finds two `reset_events` rows, expects one.
2. `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0` runs against the real repo and now
   prints `38 journeys affected`.
3. `tests/unit/adapters/test_tracing_langfuse.py::test_export_never_blocks_hanging_exporter` asserts a per-call
   wall-clock worst case `< 0.050 s`; under load it measured `0.0558 s`.

Acceptance: all three pass; 10 consecutive runs of (3) under `-n 2` pass; the owning tickets' other tests stay green;
ruff, format and mypy clean.

## Context

Found by the wave 2, 3 and 4 seam audits and the AEA-51 merge gate (`.claude/state/resume.md` lines ~416, 438, 459, 508;
`build-ledger.md` rows AEA-45, AEA-51, AEA-19-F1, FU-person-request all list `test_wf15_reset_script` as red on main).
`CLAUDE.md` *Hosting* records: "Innocent declined changing the frozen test (2026-10-21)" for `test_wf15_reset_script`.
This plan honours that: fix (1) changes the **test setup** (AEA-31's helper), not the frozen AEA-50 test file.

## Root causes (traced, not guessed)

### (1) The second `reset_events` row comes from the test setup, not from seeding or the script

- `tests/services/reset_support.py::make_dirty_demo` (AEA-31's helper, **not frozen**: AEA-31 is
  `Risk: none`) deliberately inserts an earlier reset, line ~265:
  `conn.execute("INSERT INTO reset_events (reset_id, at_wall) VALUES (?, ?)", (str(uuid4()), stamp))`.
  The schema defaults (`src/meridian/adapters/sqlite/schema/60_cases.sql`, `reset_events`) give exactly the observed
  row: `request_id` NULL, `restored_json '{}'`, `open_chats_ended 0`. The AEA-31 plan asked for it
  (`docs/plans/fanout/2026-10-21-build/AEA-31.md` line ~958: "a prior `reset_events` row and a prior `ended_threads`
  row (synthetic ids)") so AEA-31's tests can prove the reset keeps that table.
- Seeding writes **no** reset_event: `seed_first_boot` (`src/meridian/services/reset.py`) writes only a
  `SeedEventRow(..., reset_id=None, deploy_id=deploy_id, seed_count=n)`. That is correct per the observability contract
  (`docs/design/observability-contract.md` WF-15: reset → `reset_event`; WF-16: seed load → `seed_event` keyed by
  `deploy_id` or `reset_id`) and AEA-31 AC-12 ("one `seed_events` row per load, `reset_id` ... NULL at first boot").
- The reset service is correct to keep the earlier row: `docs/design/contracts/stage7/cases.md` §1.3 lists
  `reset_events` under **Kept** ("never touched by a reset"); `KEPT_TABLES` in
  `src/meridian/adapters/sqlite/migrate.py` includes `"reset_events"`. `scripts/reset.py` writes exactly one row via
  `ResetService._run` → `tx.cases.records.reset_event(ResetEventRow(...))`.
- The frozen AEA-50 test (`_reset_run` → `make_dirty_demo(store, cp, open_chats=1, customer_message=message)`) then
  asserts `len(reset) == 1` over the whole table. AEA-50 AC-10 means "the script writes one reset_event"; the setup it
  borrowed already held one.

**Decision:** no production code changes. Fix the **test setup**: `make_dirty_demo` gains a keyword
`prior_reset_event: bool = False`; the earlier `reset_events` row is inserted only when it is `True`. The two AEA-31
tests whose assertions depend on that earlier row opt in with `prior_reset_event=True`, so none of their assertions
change or weaken. The frozen AEA-50 file is not edited (Innocent's 2026-10-21 decline). The WF-15 capture scenario
becomes "a dirty demo with no earlier reset", which AC-10 permits (it names a live conversation, a case and spend rows,
not prior resets). Rejected alternative (record it): rewrite the frozen assertion to "rows for this `request_id` == 1 and
earlier rows unchanged". That is the stronger test, but it edits the frozen AEA-50 file Innocent declined to change; it
is a one-step switch if he lifts that.

Which AEA-31 tests depend on the earlier row (checked in `tests/services/test_reset.py` on `8669ed0`):

| Test (line ~) | Assertion | Needs the earlier row? |
|---|---|---|
| `test_writer_waits_for_reset_lock` (254) | `count(store.db_path, "reset_events") >= 2` after **one** reset | **Yes**: 1 without it. Opt in |
| `test_reset_clears_codes_keeps_ops_records` (399) | `reset_events == resets + 1` (AC-8, kept table) | **Yes for strength**: without an earlier row a reset that wiped the table and added one would still pass. Opt in |
| `test_concurrent_reset_refused` (234) | `== before + 1` | No (delta) |
| `test_reset_ends_open_chats` (301) | one row with `open_chats_ended = 2 AND roles_reset = 2` | No |
| test at ~615 (supervisor + operator reset) | `request_id != ? AND asked_by_role IS NULL` (NULL `request_id` rows never match `!=`) | No |
| ~193/203 newest row `checkpoints_cleared` | `ORDER BY at_wall DESC, rowid DESC` first row | No (the reset's own row is newest either way) |
| `tests/journeys/j8/test_aea_31.py` | no `reset_events` assertion | No |

### (2) A test that hard-codes "this repo has no journeys"

`test_no_journey_yet_prints_zero_and_exits_0` calls `main([... "--root", str(REPO)])` with `REPO` = the real checkout,
which now holds `tests/journeys/j1..j10` and `tests/journeys/browser/`. `pyproject.toml` is an always-input, so every
journey is selected. Fix: run it against a temporary tree with no journey files (the file already has `_tree` and
`FILES`), keep the assertions (exit 0, `0 journeys affected`).

### (3) A wall-clock bound under shared CPUs

The worst of ~1,653 timed calls is compared with 50 ms; one scheduler stall under `-n 2` load breaks it. The property
AC-3 protects is "a call never waits on the exporter". Prove it structurally: drive the turn while the exporter is
provably stuck inside `export()` and never released; a call that waited on export could not finish until the release,
which only happens after the check. Keep AC-3's 50 ms number as a load-robust check on the **median** call time
(a median over 1,651 calls cannot be moved by a few stalls), and print the worst case as before.

## Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Requirements | AEA-50 AC-10 (`docs/plans/fanout/2026-10-21-build/AEA-50.md` line 126); AEA-31 AC-8, AC-12 (`AEA-31.md` lines 165, 169); AEA-19 AC-3 (`docs/plans/tickets/AEA-19.md` line 117; `AEA-19.md` line 112, §6.4); AEA-01 AC-9 (`tests/journeys/affected.py` docstring) | The behaviours the three tests prove; nothing may weaken |
| Component contracts | `docs/design/contracts/stage7/cases.md` §1.3 (Kept tables); `stage7/data.md` line 455 (`scripts/reset.py` calls `ResetService.reset(<wall now>, request_id=<new UUID4>, session_id=None, role=None)`) | Reset keeps `reset_events`; no code change |
| Evaluation plan | n/a: no eval case, prompt or model touched | — |
| Observability contract | `docs/design/observability-contract.md` WF-15 (reset_event per reset), WF-16 (seed_event per seed load) | Seeding writes no reset_event: confirmed in code |
| Key-metrics registry | M-22 (drop explained by `reset_events`), via AEA-31 | Unchanged: kept-table behaviour untouched |
| Build loop | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `.claude/rules/integrated-journeys.md` rule 5 (reproduce first), §4 (record) | Affected tests and journeys only; a journey record |

## Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Reset keeps `reset_events` | cases.md §1.3 | yes (finding 1) | in-ticket: no code change | Step 2 (no edit to `src/`) |
| Seeding writes only a seed_event | DO-6 WF-16, AEA-31 AC-12 | yes ("decide whether seeding should write a reset_event") | in-ticket: decided **no** | Root causes (1) |
| Frozen AEA-50 test unchanged | Innocent 2026-10-21 (`CLAUDE.md` *Hosting*) | not in the item | added: fix via setup | Steps 2-3 |
| AEA-31 kept-table proof keeps its earlier row | AEA-31 AC-8 | not in the item | added: opt in | Step 3 |
| AC-3 "never blocks" proven; 50 ms number kept | AEA-19 AC-3 | yes | in-ticket | Step 5 |
| Bug fix reproduces first | integrated-journeys rule 5 | not in the item | added | Step 1 |
| Journey record says which fix | the item | yes | in-ticket | Step 7 |

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test-only diff) | — | — | — |

## Acceptance criteria

- **AC-1** `tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_script` passes unedited (file byte-identical to
  `main`: `git diff main -- tests/capture/test_cap9_runtime_ops.py` is empty), and so do `test_wf15_reset_holds_no_values`
  and `test_ops_output_has_no_values[reset]`.
- **AC-2** every test in `tests/services/test_reset.py` and `tests/unit/web/test_register_reset.py` passes, with no
  assertion line changed (only two `make_dirty_demo(...)` call sites gain `prior_reset_event=True`).
- **AC-3** `tests/unit/test_affected_journeys.py` passes, including `test_no_journey_yet_prints_zero_and_exits_0`
  against a temporary tree with zero journeys.
- **AC-4** `tests/unit/adapters/test_tracing_langfuse.py::test_export_never_blocks_hanging_exporter` passes 10
  consecutive runs of the whole file under `-n 2`; by construction it fails within 15 s (never hangs) when a call
  waits on the exporter (Step 5.4 invariants).
- **AC-5** ruff check, ruff format --check, mypy clean on every changed file.
- **AC-6 [journey]** (plan-added): `uv run python -m tests.journeys.affected --base main` selects
  `tests/journeys/j8/test_aea_31.py` (it imports `tests.services.reset_support`) and it passes. **Level:**
  `mock-tested` (the J-8 file's own stated level: real `ResetService`, temp SQLite copy, no server, no login). AC-1's
  WF-15 run is the integrated evidence for the script path: the real `scripts.reset` entry point as a subprocess on a
  real SQLite working copy, no model.
- **WP-N worked pair:** none applies: no conversation path, prompt or graph is touched. The WF-15 capture (AC-1) is
  this fix's worked case.

## File map (owned files; nothing else may be edited)

| File | Current | Change |
|---|---|---|
| `tests/services/reset_support.py` | 393 lines; AEA-31 helper, not frozen | `make_dirty_demo` gains `prior_reset_event: bool = False`; the earlier `reset_events` INSERT runs only when `True` |
| `tests/services/test_reset.py` | AEA-31 tests, not frozen | Two call sites: `make_dirty_demo(store, cp, prior_reset_event=True)` in `test_writer_waits_for_reset_lock` and `test_reset_clears_codes_keeps_ops_records` |
| `tests/unit/test_affected_journeys.py` | 153 lines; AEA-01, not frozen | Rewrite one test to use a temp tree; delete the now-unused `REPO` constant |
| `tests/unit/adapters/test_tracing_langfuse.py` | 411 lines; AEA-19, **frozen** (see Risks) | Rewrite one test body; add one test-local exporter subclass and two constants; add imports |
| `docs/testing/journeys/2026-10-22-FU-main-green.md` | absent | Create: journey record (Step 7) |

**Read only, never edit:** `tests/capture/test_cap9_runtime_ops.py` (frozen AEA-50), `tests/unit/adapters/_tracing_doubles.py`
(frozen AEA-19), `tests/deploy/**`, `tests/journeys/**`, everything under `src/`, `scripts/`, `docs/design/**`, `apps/web/**`,
`docs/ux/**`, the briefing, issued data, `docs/archive/`, `docs/parked/`.

## Shared code to use (copied from `main` at `8669ed0`)

```python
# tests/services/reset_support.py (current signature)
def make_dirty_demo(
    store: TempStore,
    cp: Checkpointer,
    *,
    open_chats: int = 1,
    customer_message: str = "Hi, my AC is making a noise.",
) -> Dirty: ...
def rows(path: Path, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]: ...
def count(path: Path, table: str) -> int: ...

# tests/unit/test_affected_journeys.py (existing helpers in the same file)
FILES: dict[str, str]                      # contains tests/journeys/j1/... and tests/journeys/j2/... entries
def _tree(tmp_path: Path, files: dict[str, str]) -> Path: ...
# tests/journeys/affected.py
def journey_files(root: Path) -> list[str]: ...
def main(argv: Sequence[str] | None = None) -> int: ...   # prints "<n> journeys affected"; returns 0 when none selected

# tests/unit/adapters/_tracing_doubles.py (frozen, import only)
class HangingExporter(SpanExporter):
    def __init__(self) -> None:            # self.release = threading.Event(); self.spans: list[ReadableSpan] = []
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:   # self.release.wait(timeout=30); extend; SUCCESS
    def shutdown(self) -> None:            # self.release.set()
def build_sink(registry: list[Any], *, exporter: SpanExporter | None = None, ..., **overrides: Any
               ) -> tuple[Any, SpanExporter, ProjectsStub, list[object]]: ...   # batch_interval_s=3600.0 by default
def close_all(registry: list[Any]) -> None: ...  # sets .release on any HangingExporter (subclasses included), closes sinks
def call_record(**overrides: object) -> CallRecord: ...
def turn_ids(run_id: str | None = None, turn_id: str | None = None) -> TurnIds: ...

# src/meridian/adapters/tracing_langfuse.py (read only): LangfuseTraceSink
#   turn(ids) -> context manager yielding SpanHandle; node(parent, name, elapsed_ms, status) -> None;
#   model_call(handle, record, input, output); export_status(handle) -> ExportStatus; dropped_spans() -> int; flush()
#   _EXPORT_BATCH_SPANS = 512 (Langfuse flush_at: the BSP worker exports once 512 spans are queued)
#   _admit(): pending counter capped at queue_max_spans (1024); excess counted in dropped_spans()
```

Test-file imports already present in `test_tracing_langfuse.py`: `threading`, `time`, `Iterator`, `Any`, `pytest`,
`InMemorySpanExporter`, and from `_tracing_doubles`: `HangingExporter`, `build_sink`, `call_record`, `turn_ids`, etc.
`LIMIT_S = 0.050` and `class Timer` (fields `worst`; method `call(fn, *args)`) exist at module level.

## Steps

1. **Reproduce first** (rule 5; record the output in the report):
   ```bash
   cd <worktree>; export UV_LINK_MODE=hardlink
   uv run pytest -q tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_script \
     tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0
   ```
   Expect two failures: `assert 2 == 1` (line ~494) and `0 journeys affected` not in output (`38 journeys affected`).
   (3) is load-dependent; run `uv run --with pytest-xdist pytest -q -n 2 tests/unit/adapters/test_tracing_langfuse.py`
   a few times and note whether it reproduced; do not loop on it.

2. **`tests/services/reset_support.py`: make the earlier reset opt-in.**
   - Signature becomes:
     ```python
     def make_dirty_demo(
         store: TempStore,
         cp: Checkpointer,
         *,
         open_chats: int = 1,
         customer_message: str = "Hi, my AC is making a noise.",
         prior_reset_event: bool = False,
     ) -> Dirty:
     ```
   - Wrap only the existing line
     `conn.execute("INSERT INTO reset_events (reset_id, at_wall) VALUES (?, ?)", (str(uuid4()), stamp))`
     in `if prior_reset_event:` with a one-line comment:
     `# an earlier reset, for tests proving the reset keeps reset_events (cases.md §1.3); off by default so a WF-15 run sees only its own row`.
   - Leave the `ended_threads` prior row, every other insert, and the order of statements unchanged.
   - Invariant: with `prior_reset_event=True` the helper produces byte-for-byte the same rows as today.

3. **`tests/services/test_reset.py`: opt in where the earlier row is load-bearing.** Change exactly two calls:
   - in `test_writer_waits_for_reset_lock`: `make_dirty_demo(store, cp)` → `make_dirty_demo(store, cp, prior_reset_event=True)`;
   - in `test_reset_clears_codes_keeps_ops_records`: same change.
   No other line in the file changes. Run `uv run pytest -q tests/services/test_reset.py tests/journeys/j8 tests/unit/web/test_register_reset.py`
   → all pass.

4. **`tests/unit/test_affected_journeys.py`: zero-journey tree.** Replace the test body and delete the module constant
   `REPO = Path(__file__).resolve().parents[2]` (its only use was this test):
   ```python
   def test_no_journey_yet_prints_zero_and_exits_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
       """A tree with no journey files: any change selects none, prints 0 and exits 0 (whatever the real repo holds)."""
       no_journeys = {
           rel: text for rel, text in FILES.items() if not rel.startswith(("tests/journeys/j1/", "tests/journeys/j2/"))
       }
       root = _tree(tmp_path, no_journeys)
       assert affected.journey_files(root) == []
       code = main(
           ["--files", "pyproject.toml", "src/meridian/policy/limits.py", "--list-only", "--root", str(root)]
       )
       assert code == 0
       assert "0 journeys affected" in capsys.readouterr().out.splitlines()
   ```
   `affected` is already imported (`from tests.journeys import affected`). Keep the line under 110 characters
   (ruff `line-length = 110`). Run `uv run pytest -q tests/unit/test_affected_journeys.py` → all pass.

5. **`tests/unit/adapters/test_tracing_langfuse.py`: structural non-blocking proof.**
   5.1 Imports: change `from collections.abc import Iterator` to `from collections.abc import Iterator, Sequence`; add
   `from opentelemetry.sdk.trace import ReadableSpan` and `from opentelemetry.sdk.trace.export import SpanExportResult`
   (keep ruff's isort order; `ruff check --fix` may sort them).
   5.2 Module constants, after `LIMIT_S = 0.050`:
   ```python
   STUCK_WAIT_S = 5.0  # time allowed for the export worker to take the first 512-span batch and hang in export()
   DRIVER_BUDGET_S = 15.0  # half HangingExporter's own 30 s release: a call that waited on export cannot finish within it
   ```
   5.3 Test-local exporter (after `class Timer`), so the frozen `_tracing_doubles.py` stays untouched:
   ```python
   class _ObservedHangingExporter(HangingExporter):
       """HangingExporter that also records that the export worker is inside export() and stuck there."""

       def __init__(self) -> None:
           super().__init__()
           self.entered = threading.Event()

       def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
           self.entered.set()
           return super().export(spans)
   ```
   5.4 Replace the body of `test_export_never_blocks_hanging_exporter` (keep its name and docstring first line; extend
   the docstring with: "Proven structurally: every call completes while the exporter is stuck inside export() and not
   yet released; the median call stays under 50 ms."):
   ```python
   exporter = _ObservedHangingExporter()
   sink, _e, _stub, _alerts = build_sink(sinks, exporter=exporter)
   sink.start()
   timer = Timer()
   durations: list[float] = []
   handles: list[Any] = []
   stuck: list[bool] = []
   failures: list[BaseException] = []
   done = threading.Event()

   def timed(fn: Any, *args: Any) -> Any:
       start = time.perf_counter()
       try:
           return timer.call(fn, *args)
       finally:
           durations.append(time.perf_counter() - start)

   def drive() -> None:
       try:
           cm = sink.turn(turn_ids())
           handle = timed(cm.__enter__)
           handles.append(handle)
           for i in range(600):  # past 512 queued spans: the worker takes a batch and hangs in export()
               timed(sink.node, handle, f"n{i}", 1, "ok")
           stuck.append(exporter.entered.wait(STUCK_WAIT_S))
           for i in range(600, 1600):  # every call from here runs while export() is stuck
               timed(sink.node, handle, f"n{i}", 1, "ok")
           for _ in range(50):
               timed(sink.model_call, handle, call_record(), "in", "out")
           timed(cm.__exit__, None, None, None)
       except BaseException as exc:  # surfaced below; a thread's exception would otherwise vanish
           failures.append(exc)
       finally:
           done.set()

   driver = threading.Thread(target=drive, name="aea19-turn-driver", daemon=True)
   driver.start()
   finished = done.wait(DRIVER_BUDGET_S)
   released_during_turn = exporter.release.is_set()
   if not finished:
       exporter.release.set()
       driver.join(DRIVER_BUDGET_S)
       pytest.fail("a turn call waited on the hanging exporter (the turn did not finish while export() was stuck)")
   assert not failures, f"a turn call raised: {type(failures[0]).__name__}"
   assert stuck == [True], "export() was never entered: the test cannot prove the calls ran while it hung"
   assert not released_during_turn
   durations.sort()
   median = durations[len(durations) // 2]
   print("max call ms", round(timer.worst * 1000, 2), "median call ms", round(median * 1000, 3))
   assert median < LIMIT_S
   handle = handles[0]
   dropped = sink.dropped_spans()
   assert dropped > 0
   assert dropped >= 1651 - (1024 + 512)
   assert sink.export_status(handle) == "failed"
   exporter.release.set()
   driver.join(DRIVER_BUDGET_S)
   sink.flush()
   assert len(exporter.spans) + dropped == 1651
   ```
   Invariants each part protects:
   - `entered` + `not released_during_turn` + `finished`: the 1,000 nodes, 50 model calls and turn exit all ran while
     the worker was blocked inside `export()`; any call that waited on export (a lock shared with the worker, a blocking
     queue put, a synchronous flush) would block until `release`, which is set only after the check, so `finished` would be
     False and the test fails in 15 s instead of hanging (HangingExporter self-releases at 30 s).
   - `stuck == [True]` fails closed: if a future Langfuse/OTel version stops exporting at 512 spans, the test says it can
     no longer prove anything rather than passing vacuously.
   - `median < LIMIT_S` keeps AC-3's 50 ms figure in the assertion; one scheduler stall cannot move a median over 1,651
     calls. The worst case is printed, not asserted (it measured the machine's load, not the sink).
   - The drop and count assertions (`dropped >= 115`, `exported + dropped == 1651`) and `export_status == "failed"` are
     unchanged from the frozen original, in the same order (status read before release).
   5.5 Do not touch `test_export_never_blocks_small_cap_counts_drops`, `..._erroring_exporter`, `..._client_failure`,
   `Timer`, `LIMIT_S` or any other test.
   5.6 No self-check that edits `src/` or the frozen doubles: the invariants above are the proof, and the reviewer
   re-reads them.

6. **Gates and affected tests** (Checks below), then the 10-run loop for (3).

7. **Journey record** `docs/testing/journeys/2026-10-22-FU-main-green.md`, in the §4 format of
   `.claude/rules/integrated-journeys.md` (copy the table shape of `docs/testing/journeys/2026-10-21-AEA-50.md`):
   - Claim: FU-main-green fixes three reds; name each test.
   - **Say which fix for (1):** "test setup, not code: `make_dirty_demo` wrote an earlier `reset_events` row on purpose
     (AEA-31's kept-table proof); the reset service correctly keeps it (cases.md §1.3); seeding writes only a seed_event
     (WF-16), so no reset_event at first boot. The earlier row is now opt-in (`prior_reset_event=True`) for the two AEA-31
     tests that rely on it; the frozen AEA-50 test is unedited (Innocent declined changing it, 2026-10-21)."
   - (2): temp tree with no journeys. (3): structural proof plus median; worst case printed.
   - Level: AC-1 integrated script entry point on a real SQLite copy (no model); J-8 `mock-tested` (its file's level);
     others unit.
   - Tested revision: the commit SHA; Command: the exact commands below; Result: counts per command, the 10-run tally.
   - Remaining limitations: `test_export_never_blocks_small_cap_counts_drops` and `..._erroring_exporter` still assert
     the worst call `< 50 ms` over 22 and 7 calls (lower flake odds, same cause; not in this item's scope).
   - Blocked by: none.

8. **Commit** on the slice branch (factory mode; never on `main`, never push, never force-push):
   ```bash
   git add tests/services/reset_support.py tests/services/test_reset.py tests/unit/test_affected_journeys.py \
     tests/unit/adapters/test_tracing_langfuse.py docs/testing/journeys/2026-10-22-FU-main-green.md
   git commit -m "test(FU-main-green): wf15 sees only its own reset_event; zero-journey tree; structural export check" \
     -m "<three short lines: cause and fix per red>" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
   ```
   Explicit paths only, never `git add -A`. The Co-Authored-By line is the last line of the message.

## Data and fixtures

Synthetic only, all existing: `make_dirty_demo`'s rows (synthetic ids, `e***@example.com`, `MHC-10004` from the issued
DB copy); `_tracing_doubles` keys `pk-lf-test-<uuid>` and the seeded generator; `FILES` in the affected-journeys test.
No new values; no phone, code, card-like number or secret anywhere. No paid model call: no test here reaches a provider.

## Checks

Run from the worktree with `export UV_LINK_MODE=hardlink`; never more than `-n 2`; cheapest first, stop at first red.

| Check | Command | Passing looks like |
|---|---|---|
| Lint | `uv run ruff check tests/services/reset_support.py tests/services/test_reset.py tests/unit/test_affected_journeys.py tests/unit/adapters/test_tracing_langfuse.py` | `All checks passed!` |
| Format | `uv run ruff format --check <same four files>` | `4 files already formatted` |
| Type check | `uv run mypy <same four files> tests/capture/test_cap9_runtime_ops.py` | `Success: no issues found` |
| Affected tests | `uv run --with pytest-xdist pytest -q -n 2 tests/capture/test_cap9_runtime_ops.py tests/services tests/unit/web/test_register_reset.py tests/unit/test_affected_journeys.py tests/unit/adapters` | 0 failed; `test_wf15_reset_script`, `test_wf15_reset_holds_no_values`, `test_ops_output_has_no_values[reset]` passed; deploy-marked tests skipped as on `main` |
| Frozen file untouched | `git diff main --stat -- tests/capture/test_cap9_runtime_ops.py tests/unit/adapters/_tracing_doubles.py tests/deploy src scripts` | empty |
| (3) ×10 under load | `for i in $(seq 10); do uv run --with pytest-xdist pytest -q -n 2 tests/unit/adapters/test_tracing_langfuse.py -k never_blocks_hanging -p no:cacheprovider \|\| { echo "FAIL run $i"; break; }; done` then the same loop **without** `-k` (whole file, so two workers load the CPUs) | 10/10 and 10/10 passed; record the printed `max call ms` / `median call ms` range |
| Affected journeys | `uv run python -m tests.journeys.affected --base main` | lists `tests/journeys/j8/test_aea_31.py` and it passes (exit 0) |

No full suite: nothing here reaches everything (no `conftest.py`, settings, dependency or shared-module change); the
pre-deploy full suite is the orchestrator's.

## Risks and requests

- **Frozen file edited, by the item's instruction:** `tests/unit/adapters/test_tracing_langfuse.py` is AEA-19's frozen
  test file (`AEA-19.md` §6.4, `risk::security`). The wave-fix item directs this change; it replaces a load-dependent bound
  with a stronger structural proof and keeps the drop/count assertions. The reviewer must confirm no other test in it
  changed. If the orchestrator reads Innocent's 2026-10-21 decline ("declined changing the frozen test", said of
  `test_wf15_reset_script`) as covering every frozen test, item (3) must go to him before the merge; items (1) and (2)
  do not depend on that answer.
- **Shared helper default changed:** `make_dirty_demo`'s default no longer writes the earlier reset. Every current caller
  was checked (table in *Root causes*); a future AEA-31-style kept-table test must pass `prior_reset_event=True`. This
  departs from the AEA-31 plan's helper description (line ~958): note it in the journey record; the AEA-31 plan is history,
  not edited.
- **Size cap:** `tests/services/test_reset.py` and `test_cap9_runtime_ops.py` are over the 500-line test cap; this
  diff is under 50 lines per file, so no split (code-structure rule).
- **Latent same-cause flakes** in two sibling AEA-19 tests (worst-call `< 50 ms` over 22 and 7 calls): out of scope;
  listed in the journey record for a follow-up.
- **Collisions:** no other open slice is known to own these five files; `tests/services/reset_support.py` is imported by
  `tests/journeys/j8/test_aea_31.py`, which this slice runs but does not edit.

## Gates

None (no human, paid or live gate). Factory mode: commit on the slice branch only; the merge step pushes `main`.

## Readiness

**READY.** No production code, contract or signed document changes. blockedOn: none.
