# Plan — [FU-person-request] PersonRequestService: a held write lock gives 503 HANDOFF_FAILED; CON-4 emits a timed child span

**Status:** planned, **READY** (refreshed 2026-10-22: AEA-51 is now on `main`, so the un-xfail step is no longer blocked)
**Issue:** wave-fix item, no issue. Source: AEA-51 findings F-4 and F-5 (`docs/plans/fanout/2026-10-21-build/AEA-51.md`,
"Seam defects found and kept as strict xfails", item 3; AC-46 and AC-48 rows of its test table) · **Base revision:**
`main` at `8785135` ("ledger: AEA-51 merged"; AEA-51 merge commit `5539bca`)
**Lane:** `lane::build-loop` (changes `src/`). **Not** `risk::security`: no test-writer, no frozen manifest, no security agent.
**Planner model:** claude-opus-5-5. **Implementer:** Sonnet.

**Refresh note (2026-10-22).** The first version was written against `main` at `dffedf7`, before AEA-51 merged.
Re-checked against `8785135`: `git diff --stat dffedf7 main` is **empty** for `services/person_request.py`,
`web/routes/handoff.py`, `ports/runtime.py`, `adapters/tracing_langfuse.py`, `adapters/sqlite/db.py`,
`services/handoff.py`, `services/turn.py`, `agent/graph.py`, `tests/fakes/trace.py`, `tests/services/person_request_support.py`,
`tests/api/handoff_support.py`, `tests/api/web_shell_support.py`, `tests/fixtures/sqlite.py`,
`tests/services/test_person_request.py` and `tests/api/test_handoff_routes.py`, so every line number and signature below
still holds. What changed: `tests/capture/test_cap3_handoff.py` is now on `main` with the two strict xfails at the line
numbers given in step 6; step 6 needs no merge and is no longer blocked; the slice worktree and branch now exist; the
affected-test list was rebuilt from the true importers on `main`.

## Goal

Fix two defects in `PersonRequestService.request()` (AEA-42, `src/meridian/services/person_request.py`), minimally and
with the existing conventions, then turn AEA-51's two strict xfails into real passing tests:

- **F-4.** `request()` opens its first write transaction (the turn claim, lines 106–120) outside any `try`. When another
  connection holds the SQLite write lock past `busy_timeout`, `SqliteUnitOfWorkFactory.__call__` raises
  `sqlite3.OperationalError` ("database is locked") straight out of the service, the route catches only
  `HandoffWriteFailed`, and CON-4 answers **HTTP 500** instead of the documented **503 `HANDOFF_FAILED`** (AC-48, second half).
- **F-5.** `request()` opens the `turn` span but emits no child span, so the CON-4 trace has no timed step (AC-46: "the
  turn span with a timed child").

Acceptance (from the orchestrator): both tests pass un-xfailed; the AEA-42 tests stay green; the 503 body validates
against the OpenAPI; no raw exception text in logs; ruff and mypy clean.

## Context

AEA-42 (merged, `55b5e7c`) built `PersonRequestService`. AEA-51 (customer path) found F-4 and F-5 while writing the CAP-3
capture tests and kept them as **strict** xfails in `tests/capture/test_cap3_handoff.py`; AEA-51 is merged
(`5539bca`, ledger `8785135`). `pyproject.toml` line 44 sets `xfail_strict = true`, so once the fix lands both tests
would XPASS(strict) = fail unless the decorators are removed **in the same branch** (step 6).

The slice worktree already exists: `/home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-person-request`, branch
`aea-fu-person-request-fu-person-request`, at `8785135` (same as `main`). Work there.

## Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Requirements (ticket ACs) | AEA-51 plan test table rows "AC-46 \| capture" and "AC-48 \| invariant" (`docs/plans/fanout/2026-10-21-build/AEA-51.md` lines 310 and 312) | AC-46: CON-4 turn row has `agent_version`, `server_ms ≥ 0`, a `trace_id` whose trace holds the `turn` span **with timed children** (`elapsed_ms` metadata); 0 ledger rows; 0 model calls. AC-48: a write lock held beyond the retry → 503 `HANDOFF_FAILED`, neither `cases` nor `events(case_created)` row |
| Component contracts (stage7 addendum, wins over DO-4) | `docs/design/contracts/stage7/web.md` §8 "CON-4 person request" | `class HandoffWriteFailed(Exception): ...  # HandoffService failed after its one retry → 503 HANDOFF_FAILED`; steps 2–5 run inside `with trace.turn(ids) as span:`; step 1 `core.turns.begin`; step 6 `core.turns.finish` after the span closes. No admission, no SpendGuard, no rate limit, no model. **Signatures unchanged by this fix.** |
| Component contracts (DO-4) | `docs/design/contracts/internal-components.md` (TraceSink, models.md §4) as implemented in `src/meridian/ports/runtime.py` | `TraceSink.node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None` is the port's only child-span call; this fix uses it and adds nothing to the port |
| Code design (DO-3) | `docs/design/code-design.md` §2.1 import direction | `services/` may not import `adapters/` concretes or `agent/`; so the service catches `Exception`, never `sqlite3.OperationalError` (same as `HandoffService.open`, `services/handoff.py` lines 111–119). `tests/unit/test_import_direction.py` enforces it |
| Signed UI contract | `docs/ux/03-structure/ui-contracts.openapi.yaml`, `requestPerson` (line ~2553), 503 response (line ~2755: "503 HANDOFF_FAILED: the case write failed and was retried once. The person key stays visible; tap again.") | The 503 body is produced by the existing route (`ApiProblem(503, ApiErrorCode.HANDOFF_FAILED, details={"retry_after_ms": HANDOFF_RETRY_AFTER_MS})`); this fix only makes the lock path reach it. **No contract change** |
| Observability contract (DO-6) | `docs/design/observability-contract.md` WF-2 row (line 77): "API, handoff node, case store, promise table"; *Content and redaction* | The child span is the WF-2 "handoff node" step; its name and status carry no value (only `"handoff"`, `"ok"`/`"error"`). No exception text in logs or spans |
| Request log | `src/meridian/web/errors.py` line 68 (`request.state.error_kind = exc.code.value`) | The 503 request record carries `error_kind = "HANDOFF_FAILED"`, so CAP-1's `test_status_values_within_lists` (which repeats the held-lock step and asserts `status >= 500` with `error_kind` set) stays green |
| Evaluation plan (DO-5) | n/a | No model, no eval case changes |
| Key-metrics registry (DO-7) | n/a | No metric reads spans; `server_ms` and `turns` rows are unchanged |

## Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| A held write lock on the turn claim → 503 `HANDOFF_FAILED`, no row written | AC-48; web.md §8 `HandoffWriteFailed → 503` | yes (F-4) | in-ticket | Step 1 |
| CON-4 trace has a timed child span (`elapsed_ms`) | AC-46; DO-6 WF-2 | yes (F-5) | in-ticket | Step 2 |
| The span is emitted also when `HandoffService.open` raises (one span per run) | `agent/graph.py` `timed_node` docstring: "Exactly one trace span per node run, also when the node raises" | no | added | Step 2 (`finally`) |
| A lock that arrives **after** the claim (failed-turn write or completed-turn write) must not turn the 503 into a 500 either | AC-48 "a write lock held beyond the retry answers 503"; same defect class as F-4 in the same method | no | added | Steps 3 and 4 |
| The 503 body validates against the OpenAPI | OpenAPI `requestPerson` 503; orchestrator acceptance | yes | in-ticket | Step 5b route test (`assert_matches(resp, "requestPerson")`) |
| No raw exception text in logs or the body | DO-6 *Content and redaction*; `HandoffWriteFailed` docstring "The message carries no value" | yes | in-ticket | Steps 1, 3, 4 (fixed messages, `from exc` chain only); Step 5b log check |
| Remove exactly the two xfail markers | orchestrator authorisation | yes | in-ticket | Step 6 |
| `HandoffWriteFailed`, `PersonRequestService.__init__`/`request` signatures unchanged | web.md §8 | — | in-ticket | All steps |

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (CON-4 `POST /api/chat/sessions/{thread_id}/handoff` already exists; unchanged route) | WF-2 | yes, DO-6 line 77 | CAP-3; E-6; M-10…M-13, M-15 |

## Boundary

**Owned files (the only files the implementer may create or edit):**

| File | Action |
|---|---|
| `src/meridian/services/person_request.py` | modify (234 lines now; ~255 after; cap 600) |
| `tests/services/test_person_request_lock_span.py` | create (~170 lines; cap 500) |
| `tests/api/test_handoff_lock.py` | create (~75 lines) |
| `tests/capture/test_cap3_handoff.py` | modify **only** to delete the two `@pytest.mark.xfail(...)` decorators (step 6; 249 lines now) |
| `docs/testing/journeys/2026-10-22-FU-person-request.md` | create (journey evidence record, integrated-journeys §4) |

**Shared surfaces, read only (never edit):** `src/meridian/web/routes/handoff.py`, `src/meridian/web/errors.py`,
`src/meridian/web/middleware.py`, `src/meridian/ports/runtime.py`, `src/meridian/adapters/tracing_langfuse.py`,
`src/meridian/adapters/sqlite/db.py`, `src/meridian/services/handoff.py`, `tests/fakes/trace.py`,
`tests/services/person_request_support.py`, `tests/api/handoff_support.py`, `tests/api/web_shell_support.py`,
`tests/fixtures/sqlite.py`, `tests/services/test_person_request.py`, `tests/api/test_handoff_routes.py` (already 515
lines, over its cap: do **not** add to it), `tests/integration/*` (incl. `customer_support.py`, `customer_api.py`),
`tests/capture/*` other than the two-decorator deletion above (incl. `test_cap1_customer_chat.py`), `docs/ux/**`,
`apps/web/**`, the OpenAPI, `UI_CONTRACTS.md`, `docs/archive/`, `docs/parked/`, the briefing and issued data.

**Owned by other slices, must not touch:** other plan files under `docs/plans/fanout/2026-10-21-build/` (including
`AEA-51.md`), the ledger, the area map and ICM rows (the merge step writes those), the `AEA-40` and `AEA-61` worktrees.

## Requirements table

| # | Requirement | How it is implemented | How it is verified |
|---|---|---|---|
| R-1 (AC-48 2nd half, F-4) | Write lock held during the claim → 503 `HANDOFF_FAILED`; neither `cases` nor `events(case_created)` row | Step 1: wrap the claim `with self._uow(write=True)` in `try`; any `Exception` other than `HandoffWriteFailed` → `raise HandoffWriteFailed("turn claim failed") from exc` | `tests/capture/test_cap3_handoff.py::test_con4_held_write_lock_gives_503` (un-xfailed); `tests/api/test_handoff_lock.py::test_held_write_lock_gives_503_matching_openapi`; `tests/services/test_person_request_lock_span.py::test_claim_lock_raises_handoff_write_failed_and_writes_nothing` |
| R-2 (AC-46, F-5) | CON-4 trace: `turn` span with ≥1 child carrying `elapsed_ms` | Step 2: `self._trace.node(span, HANDOFF_SPAN, elapsed_ms, node_status)` around `self._handoff.open(req, ctx)`, in `finally` | `tests/capture/test_cap3_handoff.py::test_wf2_turn_has_timed_children` (un-xfailed); `test_person_request_lock_span.py::test_open_emits_one_timed_handoff_span` and `::test_failed_open_still_emits_handoff_span` |
| R-3 (added) | A lock during the failed-turn write still gives `HandoffWriteFailed` (503), not a raw error | Step 3: that write becomes best effort (`contextlib.suppress(Exception)`) | `test_person_request_lock_span.py::test_lock_on_failed_turn_write_still_raises_handoff_write_failed` |
| R-4 (added) | A lock during the completed-turn write gives `HandoffWriteFailed` (503), not a raw error | Step 4: wrap it; `except Exception as exc: raise HandoffWriteFailed("turn write failed") from exc` | `test_person_request_lock_span.py::test_lock_on_completed_turn_write_raises_handoff_write_failed` |
| R-5 | 503 body validates against the OpenAPI | Unchanged route mapping | `tests/api/test_handoff_lock.py::test_held_write_lock_gives_503_matching_openapi` (`assert_matches(resp, "requestPerson")`) |
| R-6 | No raw exception text in logs or body | Fixed `HandoffWriteFailed` messages; route raises `ApiProblem ... from None`; no new logging | Same route test: `"database is locked"` and `"OperationalError"` absent from `app_log_text(caplog)`, `caplog.text` and `resp.text`; service tests: `"locked" not in str(excinfo.value)` |
| R-7 | AEA-42 tests stay green | No signature or behaviour change on the success path | Affected-test command, *Checks* step 3 |
| R-8 [journey] | J-7 CON-4 step still passes; the CAP-3 path is exercised through the real app | Unchanged success path | `uv run pytest -m journey tests/journeys/j7/test_aea_42.py -q` at level **mock-tested** (its own docstring level), plus the un-xfailed CAP-3 tests at level **integrated with a scripted model** (API level: real app, real DB copy, scripted model, no browser) |
| R-9 | Worked pair stays green | — | AEA-42 example pair 1 `tests/api/test_handoff_routes.py::test_example_pair_1_case_created_then_already_open`; CAP-3 WP-7 drive `tests/capture/test_cap3_handoff.py::test_cap3_records` |
| R-10 | CAP-1 forced-5xx record still produced | 503 still ≥ 500; `errors.py` line 68 sets `error_kind = "HANDOFF_FAILED"` | `tests/capture/test_cap1_customer_chat.py::test_status_values_within_lists` |

## Shared code to use (copied from `main` at `8785135`)

`src/meridian/ports/runtime.py`:

```python
class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> AbstractContextManager[SpanHandle]: ...
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...

class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
```

Langfuse adapter `node()` (`adapters/tracing_langfuse.py` line 580) starts a child observation of the open turn
observation with `metadata={"elapsed_ms": elapsed_ms, "node_status": ...}` and never raises (it catches and logs the
exception **type name** only). The capture test reads it with `span_meta(s, "elapsed_ms")`
(`tests/integration/customer_support.py` line 391, attribute `langfuse.observation.metadata.elapsed_ms`).
`NullTraceSink.node` returns `None`. `InMemoryTraceSink.node` (`tests/fakes/trace.py` line 77) appends
`RecordedNode(name: str, elapsed_ms: int, status: str)` to that turn's `.nodes`.

The convention being copied — `agent/graph.py` lines 175–188 (`timed_node`):

```python
t0 = time.monotonic()
status = "error"
try:
    update = fn(state, runtime)
    ...
    status = "halted" if halted else "ok"
    return update
finally:
    deps.trace.node(runtime.context.span, name, int((time.monotonic() - t0) * 1000), status)
```

The failure convention being copied — `services/handoff.py` lines 111–119 (catches `Exception`, chains it, no text),
and `services/turn.py` lines 502–503 (best-effort failed-turn write):

```python
with contextlib.suppress(Exception), self._uow(write=True) as tx2:
    tx2.core.turns.finish(...)
```

Lock behaviour — `adapters/sqlite/db.py` `SqliteUnitOfWorkFactory.__call__`: `conn.execute("BEGIN IMMEDIATE")` raises
`sqlite3.OperationalError` after `busy_timeout_ms` (default `BUSY_TIMEOUT_MS = 5000`, line 25) **before the caller's
block runs**, so nothing is written. Constructor (line 143): `SqliteUnitOfWorkFactory(db_path: Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS)`.

Route (unchanged, `web/routes/handoff.py` lines 60–67):

```python
try:
    outcome = service.request(cmd)
except HandoffWriteFailed:
    raise ApiProblem(503, ApiErrorCode.HANDOFF_FAILED, details={"retry_after_ms": HANDOFF_RETRY_AFTER_MS}) from None
```

Test helpers (read only; exact names, all verified on `8785135`):

- `tests/fixtures/sqlite.py`: `temp_sqlite()` → `TempStore(data_dir: Path, db_path: Path, issued_path: Path, uow: SqliteUnitOfWorkFactory)` (frozen dataclass, positional fields in that order).
- `tests/services/person_request_support.py`: `WALL_T0`, `WallClock(start)`, `open_thread(store, *, demo_session)`,
  `RecordingHandoffService(uow, *, presence="nobody_online", fail=False)` (attrs `.calls`, `.fail`),
  `RecordingComposer()`, `make_service(store, *, handoff, composer, trace=None, clock=None, wall=None)`,
  `person_request(thread_id, *, demo_session, turn_id=None)`.
- `tests/fakes/clock.py`: `FixedClock()`. `tests/fakes/trace.py`: `InMemoryTraceSink(*, status="sent")`, `RecordedNode`.
- `tests/api/handoff_support.py`: `handoff_app(monkeypatch, tmp_path, db, *, presence=..., handoff_fails=False, trace=None, limiter=None) -> HandoffHarness`
  (fields `app, store, db, handoff, composer, cases, demo, trace, wall, limiter`; it binds `UOW_FACTORY` to `db.uow`, and
  the login-session store is the in-memory `FakeSessionStore`, so nothing writes the DB before the service), `customer_token(h)`,
  `thread_for(h, token)`, `HANDOFF_PATH = "/api/chat/sessions/{thread_id}/handoff"`.
- `tests/api/web_shell_support.py`: `make_client(app)`, `cookie_header(token)`, `error_body(response, status, code)`, `assert_matches(response, operation_id)`, `app_log_text(caplog)`.

## Steps

All production edits are in `src/meridian/services/person_request.py`. Keep every existing line not named here.

1. **F-4: the claim transaction.** Add `import contextlib` to the stdlib imports. Wrap the existing block at lines
   106–120 (from `with self._uow(write=True) as tx:` to `tx.commit()`) as below; the body is unchanged except
   indentation:

   ```python
           try:
               with self._uow(write=True) as tx:
                   row = tx.core.conversations.lookup(str(cmd.thread_id))
                   ...                                    # unchanged lines 107-119
                   tx.commit()
           except HandoffWriteFailed:
               raise
           except Exception as exc:
               # F-4: a write lock held past busy_timeout (or any store error) before the turn is claimed. Nothing
               # was written, so 503 "tap again" is safe; the cause is chained, never put in the message.
               raise HandoffWriteFailed("turn claim failed") from exc
   ```

   Invariant: the `except HandoffWriteFailed: raise` clause comes first so the existing "thread is not open" failure is
   not re-wrapped. Do not catch `BaseException`. Do not import `sqlite3` (DO-3 §2.1; `test_import_direction.py`).
   mypy: `ids`, `begin`, `identity` are bound inside the `try`; both `except` branches raise, so they are bound after it.

2. **F-5: the child span.** Add a module constant next to `CON4_RULE_ID`:

   ```python
   HANDOFF_SPAN: Final = "handoff"  # DO-6 WF-2 "handoff node": the one timed child of the CON-4 turn span (F-5)
   ```

   Replace lines 152–157 (`try: result = self._handoff.open(req, ctx)` … `failure = exc`) with:

   ```python
               t0 = time.monotonic()
               node_status = "error"
               try:
                   result = self._handoff.open(req, ctx)
                   node_status = "ok"
               except Exception as exc:
                   # CaseWriteFailed (AEA-29) is the documented failure after its one retry and is not importable here;
                   # any failure must still leave the turn row failed so the next tap re-runs.
                   failure = exc
               finally:
                   # F-5: exactly one timed child span per run, also when open raises (agent/graph.py timed_node).
                   self._trace.node(span, HANDOFF_SPAN, int((time.monotonic() - t0) * 1000), node_status)
   ```

   Invariants: the call stays inside `with self._trace.turn(ids) as span:` (the adapter only writes a child while the
   turn observation is open); name and status are fixed literals, never data; one call per `request()` run that reaches
   the span (the `completed` and `running` early returns open no span and emit none).

3. **Failed-turn write becomes best effort (R-3).** Change the `if outcome is None:` block's write (lines 171–194) from
   `with self._uow(write=True) as tx:` to:

   ```python
           with contextlib.suppress(Exception), self._uow(write=True) as tx:
               tx.core.turns.finish(...)   # unchanged TurnRecord(status="failed", ...)
               tx.commit()
           raise HandoffWriteFailed("case write failed") from failure
   ```

   The `raise` line stays **outside** (after) the `with`, unchanged. Invariant: the caller always gets
   `HandoffWriteFailed` on this path; if the write itself failed, the turn row stays `running`, which `_await_stored`
   already answers with `HandoffWriteFailed` on a repeat tap of the same `turn_id`.

4. **Completed-turn write (R-4).** Wrap the final block (lines 197–219, `with self._uow(write=True) as tx:` through
   `tx.commit()`) in:

   ```python
           try:
               with self._uow(write=True) as tx:
                   ...                                    # unchanged finish(completed) + set_outcome + commit
           except Exception as exc:
               raise HandoffWriteFailed("turn write failed") from exc
           return outcome
   ```

   Keep `return outcome` after the `try`. Update the `HandoffWriteFailed` docstring to:
   `"""The turn or case could not be written (a held write lock included), or a duplicate press never finished. The message carries no value."""`

5. **Tests written with the code** (see *Data and fixtures* for inputs).

   5a. Create `tests/services/test_person_request_lock_span.py` (module docstring: "FU-person-request (AEA-51 F-4, F-5):
   PersonRequestService under a held write lock, and its timed handoff child span. Synthetic data; no model.").
   Imports: `sqlite3`, `typing.Any`, `pytest`; `from meridian.services.person_request import HANDOFF_SPAN, HandoffWriteFailed, PersonRequestService`;
   `from tests.fakes.clock import FixedClock`; `from tests.fakes.trace import InMemoryTraceSink`;
   `from tests.fixtures.sqlite import TempStore, temp_sqlite`; `from tests.services.person_request_support import RecordingComposer, RecordingHandoffService, WALL_T0, WallClock, open_thread, person_request`.
   Define in the file:

   ```python
   SESSION = "sess-fu-person-request"

   class LockOnWrite:
       """Wraps a UnitOfWorkFactory; write transaction number `n` (1-based) fails as a busy SQLite lock does."""
       def __init__(self, inner: Any, n: int) -> None:
           self._inner = inner
           self._n = n
           self.writes = 0
       def __call__(self, *, write: bool = False, exclusive: bool = False) -> Any:
           if write or exclusive:
               self.writes += 1
               if self.writes == self._n:
                   raise sqlite3.OperationalError("database is locked")
           return self._inner(write=write, exclusive=exclusive)

   def _service(uow: Any, handoff: Any, trace: InMemoryTraceSink) -> PersonRequestService:
       return PersonRequestService(uow, handoff, RecordingComposer(), trace, FixedClock(), WallClock(WALL_T0))
   ```

   Write order inside `request()` (what `n` hits): write 1 = the claim; write 2 = the failed-turn or completed-turn
   write. `RecordingHandoffService` must be built on `store.uow` (the unwrapped factory) so its own writes are not
   counted. Tests (each opens `temp_sqlite()` and `open_thread(store, demo_session=SESSION)` **before** wrapping;
   `cmd = person_request(thread_id, demo_session=SESSION)`):

   - `test_claim_lock_raises_handoff_write_failed_and_writes_nothing`: `LockOnWrite(store.uow, 1)`; `pytest.raises(HandoffWriteFailed)`; `"locked" not in str(excinfo.value)`; `handoff.calls == []`; no turn recorded in the trace sink; `with store.uow() as tx: assert tx.core.turns.get(cmd.turn_id) is None`; `SELECT COUNT(*) FROM cases WHERE thread_id = ?` == 0 (plain `sqlite3.connect(store.db_path)`).
   - `test_open_emits_one_timed_handoff_span`: plain `store.uow`; success; exactly one recorded turn; `[node] = <that turn>.nodes`; `node.name == HANDOFF_SPAN == "handoff"`, `node.status == "ok"`, `node.elapsed_ms >= 0`.
   - `test_failed_open_still_emits_handoff_span`: `RecordingHandoffService(store.uow, fail=True)`; raises `HandoffWriteFailed`; `[node] = <turn>.nodes`; `node.status == "error"`; turn row `status == "failed"` (unchanged AEA-42 behaviour).
   - `test_lock_on_failed_turn_write_still_raises_handoff_write_failed`: `fail=True`, `LockOnWrite(store.uow, 2)`; raises `HandoffWriteFailed` (not `sqlite3.OperationalError`); turn row exists with `status == "running"`; one `"error"` node.
   - `test_lock_on_completed_turn_write_raises_handoff_write_failed`: `fail=False`, `LockOnWrite(store.uow, 2)`; raises `HandoffWriteFailed`; `"locked" not in str(excinfo.value)`; turn row `status == "running"`; one `"ok"` node.

   Read `tests/fakes/trace.py` once for the exact attribute that lists recorded turns (the first plan wrote
   `trace.turns`); use whatever that class exposes, do not edit it.

   5b. Create `tests/api/test_handoff_lock.py` (module docstring: "FU-person-request F-4 through the real app, middleware
   and AEA-42 hunk: a held SQLite write lock answers 503 HANDOFF_FAILED matching the OpenAPI, with no raw error text.
   Synthetic data."). One test:

   ```python
   def test_held_write_lock_gives_503_matching_openapi(
       monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
   ) -> None:
   ```

   Body, in order: `caplog.set_level(logging.DEBUG)`; `with temp_sqlite() as db:`; `fast = TempStore(db.data_dir,
   db.db_path, db.issued_path, SqliteUnitOfWorkFactory(db.db_path, busy_timeout_ms=200))` (import
   `SqliteUnitOfWorkFactory` from `meridian.adapters.sqlite.db`; tests may import adapters); `h = handoff_app(monkeypatch,
   tmp_path, fast)`; `token = customer_token(h)`; `thread = str(thread_for(h, token))`; `turn_id = str(uuid.uuid4())`;
   `with make_client(h.app) as client:` then `holder = sqlite3.connect(str(db.db_path), isolation_level=None,
   timeout=0)`; `holder.execute("BEGIN IMMEDIATE")`; `try: resp = client.post(HANDOFF_PATH.format(thread_id=thread),
   json={"turn_id": turn_id}, headers=cookie_header(token))` `finally: holder.execute("ROLLBACK"); holder.close()`.
   Then assert: `data = error_body(resp, 503, "HANDOFF_FAILED")`; `data["error"]["details"]["retry_after_ms"] > 0`;
   `assert_matches(resp, "requestPerson")`; `h.handoff.calls == []`; with a plain `sqlite3.connect(db.db_path)`:
   `SELECT COUNT(*) FROM cases WHERE thread_id = ?` == 0 and `SELECT COUNT(*) FROM turns WHERE turn_id = ?` == 0; for
   each needle in `("database is locked", "OperationalError")`: not in `app_log_text(caplog)`, not in `caplog.text`,
   not in `resp.text`. The client is entered **before** the lock is taken (so app start-up never meets the lock).

   Run 5a and 5b, plus `tests/services/test_person_request.py`, until green.

6. **Un-xfail.** In `tests/capture/test_cap3_handoff.py` (on the branch now, from `main` `8785135`) delete exactly
   these two decorators and nothing else:

   ```python
   @pytest.mark.xfail(
       strict=True,
       reason="blocked-on an AEA-42 follow-up (finding F-5): PersonRequestService opens the turn span but emits no child "
       "span, so the CON-4 trace has no timed step",
   )
   ```
   (lines 142–146, directly above `def test_wf2_turn_has_timed_children`) and

   ```python
   @pytest.mark.xfail(
       strict=True,
       reason="blocked-on an AEA-42 follow-up (finding F-4): PersonRequestService.request() opens its first write "
       "transaction outside the try block, so a held write lock gives HTTP 500, not 503 HANDOFF_FAILED",
   )
   ```
   (lines 218–222, directly above `def test_con4_held_write_lock_gives_503`). Keep two blank lines between top-level
   defs so `ruff format --check` is clean. Do not touch the test bodies, docstrings or any other line.

7. **Evidence record.** Create `docs/testing/journeys/2026-10-22-FU-person-request.md` in the nine-field format of
   `.claude/rules/integrated-journeys.md` §4 (copy the layout of `docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md`):
   Claim (F-4 and F-5 fixed; J-7 CON-4 step; CAP-3 AC-46/AC-48), Level (`integrated with a scripted model` for the
   un-xfailed CAP-3 tests, API level; `mock-tested` for J-7 and the new route test), Tested revision (the commit SHA),
   Environment, Command (the exact commands from *Checks*), Result (counts, any red quoted), Evidence location,
   Remaining limitations (no browser leg; the completed-write lock path leaves the turn row `running`), Blocked by
   (`none`). No secrets, no demo password, no phone numbers.

8. **Commit** in the existing worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-person-request` on branch
   `aea-fu-person-request-fu-person-request` (do not create another worktree or branch). `git add` the five owned paths
   explicitly (never `-A`). Suggested messages: `fix(FU-person-request): held write lock gives 503 HANDOFF_FAILED; CON-4 handoff child span (AEA-51 F-4, F-5)`
   (steps 1–5) and `test(FU-person-request): un-xfail CAP-3 AC-46 and AC-48; journey record` (steps 6–7). Last line of
   every message: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push (only the merge step pushes `main`).

## Data and fixtures

Synthetic only. The DB is `temp_sqlite()`'s per-test copy of the issued scheduling DB (never the issued file). Threads
come from `open_thread(store, demo_session=SESSION)` (AEA-42 support; synthetic UUIDs, the fixed `"test-agent-0"`
agent version). Turn and request ids are fresh `uuid.uuid4()`. The demo clock is `FixedClock()`
(`tests/fakes/clock.py`); the wall clock `WallClock(WALL_T0)`. The lock is a second `sqlite3` connection holding
`BEGIN IMMEDIATE` (the same technique as AEA-51's AC-48 test) or the `LockOnWrite` double raising
`sqlite3.OperationalError("database is locked")` (the exact error class and text the real factory raises; the text is
only ever asserted **absent**). No phone numbers, codes, card-like numbers or customer names in any new file.

## Checks

Environment for every command: run inside the slice worktree; `export UV_LINK_MODE=hardlink`; never copy a venv; no
`node_modules`; pytest `-n 2` at most; do not bind ports 4019 or 5184; never read `.env`. No test here calls a model.

While iterating:

```bash
uv run pytest tests/services/test_person_request_lock_span.py tests/api/test_handoff_lock.py tests/services/test_person_request.py -q
```

Once before the final commit, cheapest first, stop at the first red:

1. Lint and format: `uv run ruff check src tests && uv run ruff format --check src tests` → no findings.
2. Type check: `uv run mypy` (configured: `src/meridian`, `tests`, `eval`; strict) → `Success`.
3. Affected tests (mirrors of `services/person_request.py` and every test file on `main` that imports it, its support
   modules or drives CON-4, plus the import-direction guard):

   ```bash
   uv run --with pytest-xdist pytest -n 2 -q \
     tests/services/test_person_request.py tests/services/test_person_request_lock_span.py \
     tests/api/test_handoff_routes.py tests/api/test_handoff_lock.py tests/api/test_handoff_capture.py \
     tests/api/test_contract_cases_handoff.py tests/contract \
     tests/unit/web/test_register_person_request.py tests/unit/web/test_register_tracing_override.py \
     tests/unit/web/test_middleware.py tests/unit/test_import_direction.py
   ```

   Then, serially (they hold a real lock for ~5 s each and run the real app):

   ```bash
   uv run pytest -q tests/capture/test_cap3_handoff.py \
     tests/capture/test_cap1_customer_chat.py::test_status_values_within_lists \
     tests/integration/test_customer_failures.py
   ```

   Passing: all green; `test_wf2_turn_has_timed_children` and `test_con4_held_write_lock_gives_503` reported **PASSED**
   (not XPASS, not xfail). Known reds on `main` that are not this slice's (AEA-51 report item 5):
   `test_no_journey_yet_prints_zero_and_exits_0`, `test_wf15_reset_script`, and a `-n 2` timing flake
   `test_wf13_wrong_project_keys_turn_export_off[right]` (green alone); none is in the lists above. A contract-drive skip
   is not a failure.
4. Affected journeys: `uv run python -m tests.journeys.affected --base main`, run whatever it lists, and at least
   `uv run pytest -m journey tests/journeys/j7/test_aea_42.py tests/journeys/j7/test_aea_30.py -q`. Browser journeys error
   without `apps/web/dist` in a backend worktree (no `node_modules`): report them as not run, with that reason; any
   assertion failure is red.

Tests that must stay green unchanged: every test in `tests/services/test_person_request.py` (notably
`test_handoff_request_fields`, `test_idempotent_turn_id`, `test_running_turn_waits_then_fails`,
`test_failed_open_marks_turn_failed_and_retry_reruns`), `tests/api/test_handoff_routes.py` (notably
`test_handoff_failed_503`, `test_example_pair_1_case_created_then_already_open`), `tests/api/test_handoff_capture.py`,
J-7, and in CAP-3 `test_cap3_records`, `test_wf2_turn_records`, `test_wf2_forbidden_values_absent`,
`test_con4_event_in_handoff_commit`; CAP-1 `test_status_values_within_lists`.

No full suite: this change reaches one service module, not a shared fixture, settings, dependency or cross-package
seam (`build-loop-test-scope.md`).

**Do not:** edit, skip or weaken any test or assertion other than deleting the two named decorators; change
`HandoffWriteFailed`'s class, the service's constructor or `request()` signature; edit the route, the trace port,
either trace adapter, `tests/fakes/trace.py` or any support module; add logging (no `str(exc)`, no `repr(exc)` anywhere);
catch `BaseException`; import `sqlite3` or anything from `meridian.adapters` in `services/`; add a new
`TraceSink` method or span helper; put any value in the span name or status; touch `docs/ux/**`, `apps/web/**`, the
OpenAPI or `UI_CONTRACTS.md`; push, force-push or `git add -A`; create another worktree.

## Risks and requests

- **Strict xfails and merge order.** With `xfail_strict = true`, steps 1–5 without step 6 turn both CAP-3 tests into
  XPASS(strict) failures. Both land on this branch, so the merge carries them together; do not split them across commits
  that merge separately.
- **Completed-write path (R-4) leaves the turn `running`.** If the lock arrives after the case is written, the customer
  gets 503 "tap again" although the case exists; a new press (new `turn_id`) answers `already_open`, and a repeat of the
  same `turn_id` waits 3 s then 503s (as today for a stuck `running` row). This is better than today's 500 and needs no
  contract change; a stale-`running` reclaim is out of scope and is noted in the record.
- **Wait time.** The real-lock capture tests wait `busy_timeout` (5 s); the new route test waits 0.2 s. Run the capture
  tests serially, not under `-n`.
- **No shared-primitive request; no spec gap; no contract problem.** The OpenAPI 503 text ("the case write failed and
  was retried once … tap again") is a description, not a constraint on cause; the body shape is unchanged.

## Gates

None human, external, paid or live. No blockers: AEA-42 and AEA-51 are both on `main`.

## Readiness

**READY.** All steps can run on the existing worktree at `8785135`. No `NEEDS-DECISION`, no `BLOCKED-ON`.
