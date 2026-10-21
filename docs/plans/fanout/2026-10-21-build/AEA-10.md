# Plan — [AEA-10] storage: SQLite core, shared case tables, migrations, checkpointer

**Status:** planned; **refreshed 2026-10-21 against `main` at `16ca639`**. AEA-01 is merged (`07924f5`, code
`893b825`); **AEA-02 is not** (its plan exists, its code does not). Implementation starts only after AEA-02 merges
(blocked-on: imports, see §9). No product decision is open.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/10 (spec copy:
`docs/plans/tickets/AEA-10.md`) · **Base revision:** `16ca639` (re-base on the commit that merged AEA-02) ·
**Planner:** claude-opus-5-5, 2026-10-21 (first pass 09:53; refresh after AEA-01 merged) · **Implementer:**
`fanout-implementer` on Sonnet.

**Refresh log (what changed against the first pass, and why).** Checked against the code on `main` (`16ca639`) and AEA-02's
plan as it stood at 12:08:
1. AEA-01's real container API is now known (`Container.provide(Key[T](name), factory)`, `on_close`, imports inside each
   hunk's body): §5 step 9 is now exact code; the key names `"uow_factory"`, `"checkpointer"`, `"restore_working_copy"` are
   the ones the AEA-23/26/29/30/31 plans already use.
2. AEA-01's `test_every_register_stub_present` asserts every hunk stays empty; filling `register_storage` turns it red →
   a two-line edit identical to the AEA-17 plan's (§8 R-13).
3. `StreamKey` is not defined by AEA-02 (nor by any contract): AEA-10 defines it with `thread_stream()` / `case_stream()`
   (§4.3, R-9). `EventId` is an `Annotated[int]` alias, so no `EventId(...)` call; ids come from a new `last_row_id`.
4. AEA-02's `FollowUp.window` is required (as OpenAPI `FollowUpView.window` is): `followups.contact_window` is `NOT NULL`
   and `FollowupRow.window` required. ID types are strict-pattern `str` subclasses: built through `TypeAdapter`, never by
   direct call. `MeridianModel` strips whitespace.
5. Paths fixed to the merged layout: `tests/fixtures/__init__.py` exists; the hunk test moves to
   `tests/unit/web/test_register_storage.py`; `tests/unit/adapters/sqlite/__init__.py` is new.
6. Exact gate commands (`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, the affected-journey
   command) and the AC-25 edits in the styles the context files now use; two commits (code, then context citing it).
Everything else (DDL, signatures, algorithms, tests) holds and is unchanged; the stage7 addenda and DO-4 changed only in
wording since the first pass (`c0621de`).
**Lane:** `lane::build-loop` · **Risk:** none (no `risk::security`: no frozen tests, no security review; the
implementer writes the tests below together with the code).

## Goal

Quoted from the issue's *What to build* (`docs/plans/tickets/AEA-10.md`):

> **US-17 · Have follow-ups understood in context.** "As a homeowner mid-booking, I need 'what about Monday?' to apply to
> the visit we were just arranging, so that I don't start over every message." Acceptance includes: "a 20-turn chat keeps
> my verified identity and the open task".
>
> This ticket gives every later ticket the one place conversation facts, cases and the working copy of the issued
> scheduling database live. "What has this conversation done" has one authority: the `actions` table, read at the start of
> every turn (DO-3 §1, §5.1; DO-1 §11 decision 3). The final shapes are `docs/design/contracts/stage7/cases.md` §1, which
> wins over DO-4 where they differ (DO-4 §16).

## Context

SP-1 showed the agent forgetting a move it had made one turn earlier (WP-4F). The design answer (R-45) is that completed
writes live in database rows, not in the chat transcript or the checkpoint. Stage 7 cut 62 tickets; this is the wave-1
storage ticket on the critical path (AEA-02 → **10** → 29 → 51 → 62 → 55 → 56). Every wave-2 service, node and route
ticket builds against the tables, repositories and `temp_sqlite()` fixture this ticket lands, and after wave 1 these files
are frozen (slice plan §3): anything missing later costs a follow-up ticket merged first.

---

## 1. Goal and sources

What the slice delivers, concretely: a working copy of the issued scheduling DB created on first boot; every
`schema/*.sql` applied in order; one unit-of-work object that opens one SQLite transaction and hands out all seven
repositories; the bodies of the two shared repositories (`repos_core`, `repos_cases`); the in-place reset helpers
(`restore_working_copy`, `clear_demo_tables`); the LangGraph checkpointer with prune/clear; and the `temp_sqlite()` test
fixture.

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-10.md` (AC-1…AC-25) | Everything below; AC text is quoted in §3 |
| Storage addendum (wins over DO-4) | `docs/design/contracts/stage7/cases.md` §1.0 (db.py), §1.1 (tables), §1.2 (methods, `EndedThread`, `Cleared`, `LookupRow`), §1.3 (reset table list), §1.4 (reset callables, checkpointer), §1.5 (fixture home), §7 (how `ResetService` calls the callables) | Signatures, columns, reset semantics |
| Turn record | `stage7/graph-core.md` §2 (`TurnRecord`, `TurnTrace`, `PlannerTrace`), §6 (`settled_for`), §7 (window, read by AEA-34), §8 (`timeouts_for`) | `turns` columns; `settled_for` |
| Check events | `stage7/graph-nodes.md` §1 (`CheckEvent`) | `check_events` columns |
| Identity DDL | `stage7/graph-tools.md` §5 | `40_identity.sql` exactly; `reads.identity_state` derivation |
| Spend DDL | `stage7/models.md` §6 | `20_spend.sql` exactly |
| Staff DDL and reset | `stage7/staff.md` §3, §4 | `90_staff.sql` exactly; role reset in `clear_demo_tables` |
| Eval rows | `stage7/data.md` §6 (`EvalRunRecord`, `EvalCaseResult`) | `95_ops.sql` eval columns |
| Web callers | `stage7/web.md` §4 (`owned_thread` → `conversations.lookup`), §8, §9 (turn path writes, restart sweep), §14 (`SessionService` greeting row, history) | `conversations` / `messages` / `turns` writes |
| Component contracts | `docs/design/contracts/internal-components.md` (DO-4) §0, §1 (`ActionKey`, `CompletedAction`, `Settled`, `OpenCase`, `Controller`, `IdentityState`), §5 (`LookupEntry`), §7 (`Promise`, `Brief`), §13 (`UnitOfWork`, method list), §16 | Types this code reads and writes |
| Code design | `docs/design/code-design.md` (DO-3) §2.1 (layers: services may call `tx.<repo>.<method>`, never SQL), §2.3 rule 6, §3, §4.3, §5.1, §8, §9, §11 RB-1, S-6 | Module homes; full suite when `repos_core.py` changes |
| Merge clashes | `docs/plans/7b-decisions/merge-clashes.md` MC-8, MC-10, MC-11, MC-15, MC-16, MC-20 | Wall-time formatter; `latest_of`; tombstones |
| Residuals | `docs/plans/7b-decisions/residuals-graph.md` R-G-8, R-G-22; `residuals-web.md` R-W-4 | `LookupRow` home; `fail_running` |
| Decision ledger | `docs/plans/7b-decisions/cases.md` CAS-1…5, 19, 23, 24, 29, 32, 35, 38 | Basis for the shapes |
| Observability (DO-6) | `docs/design/observability-contract.md` *Status values*, *Records*, *Correlation*, *Storage and access*, WF-1/2/5/7/15/16 | Columns and correlation IDs (AC-21) |
| Evaluation (DO-5) | `docs/design/evaluation-plan.md` (E-1 WP-4F state seam, E-7 DB-copy check) | Issued file pristine (AC-3); WP-4F (AC-13) |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-3, M-9, M-10, M-12, M-13, M-18, M-22…M-24, M-27, M-29 | Columns stay computable (AC-18, AC-21) |
| Journey rule | `.claude/rules/integrated-journeys.md` §3–§4; `docs/plans/ux-join/backend-amendments.md` §3 (AEA-10 row, pattern C) | AC-24 record |
| Card-answer amendment | `backend-amendments.md` AEA-40-3 | `messages.kind`, `card_id`, `choice_option` columns (added, so AEA-40 is not blocked on a follow-up) |
| Issued data | `docs/data/issued/meridian_dataset/scheduling_db/{SCHEMA.md,meridian_scheduling.sqlite}` | Never written; five tables; counts 154 / 8 / 528 / 159 / 81 |

**Facts checked against the issued file on 2026-10-21 (read-only, `mode=ro&immutable=1`):** the five tables use
`INTEGER PRIMARY KEY` **without** `AUTOINCREMENT`, so the issued file has **no `sqlite_sequence` table**; `PRAGMA
foreign_key_check` is clean; `journal_mode` is `delete`; slot 56 is `2026-10-19 08:00-12:00`, tech 5 (Marta Kowalski),
north, `hvac_repair`, `open`; Linda Foster `MHC-10001` has appointment 159 on slot 159 (`2026-10-22 08:00-12:00`, tech 5);
max `appointment_id` is 159; every customer and invoice id matches `MHC-\d{5}` / `INV-\d{6}`; every `line_items` value
parses as JSON; every `invoices.appointment_id` is NULL. **Re-checked at the refresh:** unchanged; also `INV-204411` has
`amount_cents` 47800 (customer `MHC-10002`); `MHC-10001` is Linda Foster, tier `standard`; every date column parses with
`date.fromisoformat`; every `line_items` value is a JSON array of objects. Installed `langgraph-checkpoint-sqlite` is
**3.1.2** (LangGraph 1.2.16); `SqliteSaver.setup()` creates `checkpoints(thread_id, checkpoint_ns, checkpoint_id,
parent_checkpoint_id, type, checkpoint, metadata)` and `writes(thread_id, checkpoint_ns, checkpoint_id, task_id,
task_path, idx, channel, type, value)`; `saver.put(cfg, empty_checkpoint(), {"source": "loop", "step": i, "parents": {}},
{})` five times, reusing the returned config, leaves 5 rows (tried in a scratch in-memory DB).

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Create / modify | What |
|---|---|---|
| `src/meridian/adapters/sqlite/db.py` | create | `connect`, `format_wall`, `parse_wall`, `StorageError`, `integrity_errors`, `SqliteUnitOfWork`, `SqliteUnitOfWorkFactory` |
| `src/meridian/adapters/sqlite/rows.py` | create (**new file, see §8 R-1**) | Every row model `repos_core` and `repos_cases` return (keeps both files under the 600-line adapter cap) |
| `src/meridian/adapters/sqlite/repos_core.py` | modify (AEA-02 shell → body) | `CoreRepos` and its sub-repositories; re-exports the core row models |
| `src/meridian/adapters/sqlite/repos_cases.py` | modify (AEA-02 shell → body) | `CaseRepos` and its sub-repositories, `DEMO_START`; re-exports the case row models |
| `src/meridian/adapters/sqlite/migrate.py` | create | `WORKING_DB_NAME`, `schema_files`, `migrate`, `restore_working_copy`, the table-effect constants |
| `src/meridian/adapters/sqlite/schema/00_core.sql`, `20_spend.sql`, `40_identity.sql`, `50_booking.sql`, `60_cases.sql`, `90_staff.sql`, `95_ops.sql` | create | All DDL (§5 step 2) |
| `src/meridian/adapters/checkpointer.py` | create | `CHECKPOINTS_DB_NAME`, `Checkpointer` |
| `src/meridian/web/container.py` | modify **only `register_storage`'s docstring and body** (AEA-01's stub, the first hunk in the file; every other line is AEA-01's or another ticket's) | §5 step 9 |
| `tests/fixtures/sqlite.py` (`tests/fixtures/__init__.py` already exists, AEA-01; do not touch it) | create | `ISSUED_DB`, `TempStore`, `temp_sqlite()` |
| `tests/unit/adapters/sqlite/__init__.py` (0 bytes; the test tree uses package markers) and `tests/unit/adapters/sqlite/test_migrate.py`, `test_uow.py`, `test_repos_core.py`, `test_repos_core_rows.py`, `test_repos_cases.py`, `test_schema.py` | create | §7 |
| `tests/unit/web/test_register_storage.py` | create | PA-6 (mirrors `web/container.py`, as AEA-19's planned `test_register_tracing.py` does) |
| `tests/unit/web/test_container.py` | modify **two inserted lines only** (AEA-01's file; §8 R-13), and only if they are not already on `main` | lets filled hunks pass `test_every_register_stub_present` |
| `tests/unit/adapters/test_checkpointer.py` | create | AC-19 |
| `tests/unit/adapters/test_repo_shells.py` | modify **one assertion only** (AEA-02's file; §8 R-2), and only if not already done on `main` | Apply the "no public member" check only to shells whose docstring still says `AEA-02 creates the constructor only` |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-10.md` | create | AC-24 record |
| `.claude/reference/area-map.md` | modify the A0 row only | AC-25 |
| `.claude/state/icm-progress.md` | modify the row *Routes verified against code and tests* only | AC-25 |
| `docs/design/code-design.md` | modify the §3 status note only | AC-25 |

### Shared surfaces read, never edited

`src/meridian/domain/*`, `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02); `src/meridian/policy/limits.py`,
`tests/conftest.py`, `tests/journeys/**` (incl. `affected.py`), `tests/unit/test_import_direction.py`, `pyproject.toml`,
`uv.lock`, the rest of `web/container.py` and of `tests/unit/web/test_container.py` (AEA-01); `tests/fakes/` (AEA-11);
`repos_{spend,identity,booking,staff,ops}.py` (AEA-02 shells; bodies are AEA-26/27/28/44/32); the issued dataset;
`docs/ux/**`, `apps/web/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`; `docs/archive/`, `docs/parked/`.

### Must not

- Edit any file above that is not in the owned table, or another ticket's `register_*()` hunk.
- Write a repository body for spend, identity, booking, staff or ops (their **DDL** is this ticket's; their **methods**
  are not). The reset's `staff_sessions` UPDATE and `flags`/identity DELETEs are inside `clear_demo_tables` (staff.md §4,
  graph-tools §5) — that is the only touch.
- Put service logic here: no case lifecycle rules, due-state math, promise selection, scheduler selection rules beyond the
  plain queries named in §4, reset ordering, seed content, or clock advance (AEA-29/30/31).
- Open the issued file for writing in any code path. Copy it with `shutil.copyfile` (reads it `rb`) and read it only
  through `file:…?mode=ro&immutable=1`. Never run a PRAGMA that writes (e.g. `journal_mode`) on that connection.
- Put a code, card-like number, full phone number or secret in any test name, fixture literal or log. Use issued rows by id
  and synthetic sentinels built at run time (`"sentinel-" + uuid4().hex`).
- Call `datetime.now()` anywhere except the two documented fallbacks (`clear_demo_tables(ended_at=None)`,
  `job_runs.finish(finished_wall_at=None)`).
- `git add -A`, push, force-push, bind ports 4019/5184, copy a venv, or run pytest with more than `-n 2`.
- Add a module-level import, constant or helper to `web/container.py`. Its docstring says module-level imports never
  change after AEA-01, and `test_container_imports_only_policy_limits` enforces the `meridian` part. Every import the
  hunk needs goes inside `register_storage`'s body.
- Construct an ID type by calling it (`CaseRef("…")`, `ThreadId("…")`): that skips its pattern check. Validate through a
  `TypeAdapter`, or pass plain strings into `Model.model_validate({...})` (§4.1).
- Read `.env`, or put a secret, code, card-like number or full phone number in code, a log, a test name or a fixture.

---

## 3. Requirements table

Every acceptance criterion of the issue (verbatim IDs; the full text is in the issue), then the obligations the sources add
(**plan-added**). "Step" points at §5; "Test" at §7.

| ID | Requirement (short; issue text governs) | How it is implemented | Verified by |
|---|---|---|---|
| AC-1 | First boot copies the issued DB and applies every `schema/*.sql` in numeric order; five issued counts kept (154/8/528/159/81) | `migrate()` step 4 | `tests/unit/adapters/sqlite/test_migrate.py::test_first_boot_copies_issued_db_and_applies_schema` |
| AC-2 | Existing working copy survives a boot (conversation, action, case read back unchanged) | `migrate()` copies only when the file is missing; DDL is all `IF NOT EXISTS` | `test_migrate.py::test_existing_working_copy_survives_restart` |
| AC-3 | Issued file never written: same SHA-256 after first boot, a uow write and `restore_working_copy(tx)`; a sentinel is in the copy and not in the issued file | step 4, step 5 | `test_migrate.py::test_issued_file_never_written` |
| AC-4 | `restore_working_copy(tx)` restores the five tables in the caller's tx; slot back to `open`; next appointment id 160; kept tables survive | step 5 | `test_migrate.py::test_restore_working_copy_restores_issued_tables` |
| AC-5 | Restore inside a uow that then raises leaves the copy unchanged | restore never commits; factory rolls back | `test_migrate.py::test_restore_rolls_back_with_caller` |
| AC-6 | `clear_demo_tables(reset_id)` clears/updates/keeps exactly cases §1.3; tombstones; roles reset; `Cleared` fields | step 7 (`ResetRepo`) | `test_migrate.py::test_clear_demo_tables_matches_table_list` |
| AC-7 | After a clear, event ids keep rising; `lookup` → `EndedThread` (reason, reset_id) / `None` | AUTOINCREMENT; `ConversationsRepo.lookup` | `tests/unit/adapters/sqlite/test_repos_core.py::test_ids_not_reused_and_tombstone_lookup` |
| AC-8 | WAL, busy_timeout 5000, FKs on; no commit → rollback; exception → rollback + propagate; write in `write=False` uow fails | step 1 | `tests/unit/adapters/sqlite/test_uow.py::test_pragmas_commit_and_rollback` |
| AC-9 | `write=True` blocked by a held `exclusive=True` gives up at `BEGIN` after the busy timeout; no partial write | step 1 (`BEGIN IMMEDIATE` inside `__enter__`) | `test_uow.py::test_lock_timeout_writes_nothing` |
| AC-10 | `SqliteUnitOfWork` exposes the seven repos over one connection; importing `meridian.ports.runtime` loads no `meridian.adapters*` | step 1; subprocess import check | `test_uow.py::test_seven_repos_and_port_imports_no_adapter` |
| AC-11 | `format_wall` / `parse_wall`: `2026-10-16 10:00 Chicago` → `2026-10-16T15:00:00+00:00`; round trip; naive → `ValueError` | step 1 | `test_uow.py::test_wall_time_formatter` |
| AC-12 | `actions.record` idempotent on `ActionKey` (second call returns the stored row, writes nothing) | step 6 `ActionsRepo.record` | `test_repos_core.py::test_action_record_idempotent_on_key` |
| AC-13 | **WP-4F**: `actions.for_thread` and `settled_for(thread, read_at)` at turn 4 return the turn-3 `moved` action with before/after; open case + promise; `read_at` as given | step 6 `CoreRepos.settled_for` | `test_repos_core.py::test_settled_for_returns_earlier_turn_move` |
| AC-14 | `turns.begin` → new / completed(+response) / running / failed; `finish` stores every `TurnRecord` field; `timeouts_for` counts `timeout` rows | step 6 `TurnsRepo` | `test_repos_core.py::test_turn_begin_finish_and_timeouts` |
| AC-15 | `events.append` ids increase; `after(stream, last)` only that stream, later, in order; `latest_of(stream, kind)` newest id or `None` | step 6 `EventsRepo` | `test_repos_core.py::test_events_after_and_latest_of` |
| AC-16 | `lookup_log.append` copies the message's `thread_id`; `for_thread` returns `LookupRow`s id ascending; unknown message rejected; `handoff_anchor` newest customer message else greeting | step 6 | `test_repos_core.py::test_lookup_log_and_handoff_anchor` |
| AC-17 | `reads.invoice/appointment/customer` current row; `reads.identity_state` per graph-tools §5 | step 6 `ReadsRepo` | `test_repos_core.py::test_cross_ticket_reads` |
| AC-18 | `repos_cases` round trips (both dues, promise text, `policy_row`, `version`, `seed`, case events + `exists`, `demo_state` defaults/reset, `demo_events`, `job_runs.latest`, reset/seed records, `next_case_ref` → MHC-C-0009 after seeds) | step 8 | `tests/unit/adapters/sqlite/test_repos_cases.py` (tests listed in §7) |
| AC-19 | Checkpointer on `checkpoints.sqlite`; `prune(keep=2)` 5 → 2, returns 3; `clear()` → 0; `clearing()` rolls back on raise, commits on clean exit | step 10 | `tests/unit/adapters/test_checkpointer.py` |
| AC-20 | A storage error names table and constraint only; a distinctive `record_id` is absent from the exception text and `caplog` | `StorageError` + `integrity_errors`; `actions.record` conflict rule (step 6, §8 R-3) | `test_repos_core.py::test_storage_error_hides_value` |
| AC-21 | Tables hold every DO-6 / cases §1.1 field with correlation ids | DDL step 2 | `tests/unit/adapters/sqlite/test_schema.py::test_do6_fields_present` |
| AC-22 | `temp_sqlite()` builds a copy with every schema applied and removes it afterwards | step 11 | `test_schema.py::test_temp_sqlite_applies_all_schema` |
| AC-23 | `turns.fail_running()` fails every `running` row only (status failed, path degraded, outcome degraded_handoff, degrade_reason timeout); returns the ids | step 6 | `test_repos_core.py::test_fail_running_sweeps_every_running_row` |
| AC-24 [journey] | No journey yet (wave 1, before AEA-57); record at level `mock-tested`, *Blocked by* AEA-57, names J-1…J-10; affected-journey command prints "0 journeys affected" | step 13 | the record + AEA-01's affected-journey command |
| AC-25 | Area map A0 row, ICM row, DO-3 §3 status updated | step 14 | `git diff --name-only` shows the three files |
| PA-1 (plan-added) | Every table in the working copy has exactly one reset effect (issued / cleared / updated / kept), and no kept table has a FK to a cleared table (cases §1.1 last line) | constants in `migrate.py`; DDL | `test_schema.py::test_every_table_has_one_reset_effect`, `::test_no_kept_table_references_cleared_table` |
| PA-2 (plan-added) | Conversation-row writes the consumers need (AEA-29/30/40/42/46): insert, outcome, last customer wall time, controller + live state, live state, open thread ids, idle live threads | step 6 `ConversationsRepo` (added methods, §4) | `tests/unit/adapters/sqlite/test_repos_core_rows.py::test_conversation_writes` |
| PA-3 (plan-added) | `messages.recent(thread, turns)` returns the lines of the last *n* turn ids plus null-turn lines since the oldest kept turn (graph-core §7) | step 6 | `test_repos_core_rows.py::test_messages_recent_window` |
| PA-4 (plan-added) | `check_events.append` stores every `CheckEvent` field, `at` from the turn's `received_at` | step 6 | `test_repos_core_rows.py::test_check_events_append_round_trip` |
| PA-5 (plan-added) | `cases.update_versioned` bumps the version on a match and changes nothing on a stale version | step 8 | `test_repos_cases.py::test_update_versioned_conflict` |
| PA-6 (plan-added) | `register_storage()` migrates the working copy and exposes the factory, checkpointer and bound restore callable | step 9 | `tests/unit/web/test_register_storage.py::test_register_storage_migrates_and_exposes_factory` |
| PA-7 (plan-added) | A `turn_id` already stored for another thread never returns that thread's response (`begin` answers `running`, writes nothing) | step 6 `TurnsRepo.begin` | `test_repos_core.py::test_turn_begin_finish_and_timeouts` (extra case) |
| PA-8 (plan-added) | One `StreamKey` with a thread form (the bare thread id) and a case form (`case:<CaseRef>`), built only by `thread_stream()` / `case_stream()` (DO-4 §13 names the type; staff.md §7 the case form) | `rows.py` (§4.3, R-9) | `test_repos_core.py::test_events_after_and_latest_of` (asserts both forms) |

### Source-contract reconciliation (obligations not already an AC)

| Obligation | Source | Disposition | Step / owner |
|---|---|---|---|
| `messages` must give a turn's `card_id` and chosen option for history card answers | backend-amendments AEA-40-3 | **added**: columns `turn_id`, `kind`, `card_id`, `choice_option` + keyword args on `messages.append` | step 2, 6 |
| `ThreadHistory`/CON-12 need every message, every turn, newest event id | web.md §14; AEA-29-5 | **added**: `messages.all_for_thread`, `turns.for_thread`, `turns.get`, `events.latest_id` | step 6 |
| AEA-29 brief upsert per case; CON-12 sources, other cases, history | cases.md §5; OpenAPI `CaseDetail` | **added**: `cases.briefs.upsert/get`, `cases.cases.list_for_thread/list_for_customer`, `case_events.list_for_case`, `promises.current/history` | step 8 |
| AEA-31 must record `checkpoints_cleared = false` after a failed checkpoint commit | cases.md §7 | **added**: `records.set_checkpoints_cleared(reset_id, cleared)`; also `records.latest_reset_event/latest_seed_event` | step 8 |
| `ended_threads.ended_wall_at` and `job_runs.finished_wall_at` need a wall time the signatures do not pass | cases.md §1.1–§1.2 | **added**: optional keywords `ended_at` / `finished_wall_at` (fallback `datetime.now(UTC)`); request to AEA-31/30 to pass their wall clock | step 7, 8; §8 R-5 |
| `restore_working_copy` needs the issued path | cases.md §1.4; `Settings.issued_db_path` | **added**: required keyword `issued_path`; the container binds `functools.partial(..., issued_path=settings.issued_db_path)` so callers still see `Callable[[UnitOfWork], None]` | step 5, 9 |
| `StreamKey` construction (thread and case variants) | DO-4 §13 names it; staff.md §7 gives `case:<CaseRef>`; no addendum sketches it; AEA-02 does not define it | **added**: `StreamKey = NewType("StreamKey", str)`, `thread_stream`, `case_stream` in `rows.py` | step 3; §8 R-9 |
| `conversations.started_wall_at` for M-22 zero-traffic | DO-6 *Records* (start time); cases.md §8 | **added** nullable column + `conversations.last_started_wall()`; `SessionService` (AEA-40) has no wall clock today → §8 R-6 | step 2, 6 |
| `lookup_log` "time" | DO-6 *Records* | **n/a as a column**: §1.1 lists the columns exactly; the time is the named message's `at` (join on `message_id`) | — |
| Repository Protocols | DO-3 §2.1 | **n/a**: concrete classes by design until the Postgres step | — |
| Seed content, reset ordering, scheduler rules, abandonment rule | cases.md §5–§7 | **other-ticket**: AEA-29, 30, 31 | — |
| `fail_running()` called at start-up | web.md §9 | **other-ticket**: AEA-40's hunk | — |
| Card-like / code values never stored | DO-6 *Content and redaction* | **other-ticket** (AEA-12/40 redact before storage); this ticket adds no column for a code or full phone beyond the sibling DDL | — |

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| Start-up migration step (first-boot copy + schema) | WF-16 "Case-store table creation and demo seed load" | DO-6 *Covered workflows* WF-16 | CAP-9 (AEA-50); seed half is AEA-31 |

---

## 4. Shared code to use

### 4.1 Imports from AEA-02 (wave 0) — use exactly these names

Find each module with `grep -rn "^class <Name>\|^<Name> =" src/meridian/domain src/meridian/ports` after AEA-02 merges;
the homes below are AEA-02's plan (`docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0–§4.15, read at 12:08 on
2026-10-21 while it was still being refreshed). Confirm each with the grep after AEA-02 merges and import from where the
merged code puts it (§8 R-14).

| Name | Expected module | Used for |
|---|---|---|
| `MeridianModel`, `ThreadId`, `TurnId`, `RequestId`, `CustomerId`, `InvoiceId`, `CaseRef`, `PassageId`, `EventId` | `meridian.domain.common` | base model; IDs. `EventId` is `Annotated[int, Field(ge=0)]`: an alias, **not callable**, so return plain `int` |
| `ActionKind`, `ActionKey`, `CompletedAction`, `OpenCase`, `Settled` | `meridian.domain.actions` | actions, `settled_for` |
| `HandoffReason`, `Priority`, `Promise`, `FollowUp`, `CaseState`, `Brief` | `meridian.domain.handoff` (some are defined in `common.py` and re-exported from `handoff`) | cases, promises, follow-ups, briefs |
| `Controller`, `IdentityState` | `meridian.domain.state` (`IdentityState` is defined in `identity.py`, re-exported from `state`) | conversations, identity read |
| `TurnIds`, `TurnRecord`, `TurnTrace`, `PlannerTrace`, `CheckEvent`, `ExportStatus`, `RunTag` | `meridian.domain.turn` | turns, check events |
| `LookupEntry`, `LookupRow` | `meridian.domain.tools` | lookup log (R-G-8: `LookupRow` is AEA-02's) |
| `DemoRole`, `StaffRole` | `meridian.domain.staff` | roles |
| `UnitOfWork`, `UnitOfWorkFactory` | `meridian.ports.runtime` (`ExportStatus` is re-exported there too) | restore signature; the factory Protocol (type check only) |
| `CoreRepos`, `CaseRepos` (class names and `__init__(self, conn: sqlite3.Connection) -> None` kept) | `meridian.adapters.sqlite.repos_core`, `.repos_cases` (shells) | bodies |
| `SpendRepo`, `IdentityRepos`, `BookingRepos`, `StaffRepos`, `OpsRepos` | `meridian.adapters.sqlite.repos_{spend,identity,booking,staff,ops}` | built by `SqliteUnitOfWork` only |

**Defined by this ticket, not by AEA-02.** AEA-02's ticket says a type DO-4 names without a sketch belongs to the
owning topic, and its plan's §2.3 lists `EndedThread`, `Cleared` and `SqliteUnitOfWork` as AEA-10's. So `rows.py` defines
`StreamKey`, `StreamEvent`, `TurnBegin`, `EventRow`, `ConversationRow`, `MessageRow`, `EndedThread`, `Cleared` and the
other row models of §4.3. **If the merged AEA-02 defines any of them** in `domain/` or `ports/`: do not define a second
one. Import theirs if its fields match §4.3; otherwise stop and report it to the orchestrator (a duplicate would split
the contract).

**Building `Promise`, `OpenCase`, `PlannerTrace`, `TurnRecord` from rows:** use `<Type>.model_validate({...})` with plain
dicts (stored enum values as strings). Never write `Promise(` in `src/` (graph-core §10 grep test: only
`policy/handoff.py` and tests may). Building `OpenCase` from a dict also validates its nested `promise`, `followup` and
`state` without importing `FollowUp` or `CaseState`.

**Domain facts that shape the code (AEA-02's plan):**
- ID types (`ThreadId`, `TurnId`, `RequestId`: canonical lower-case uuid4; `CustomerId` `MHC-[0-9]{5}`; `InvoiceId`
  `INV-[0-9]{6}`; `CaseRef` `MHC-C-[0-9]{4}`; `PassageId` `<path>#<n>`) are `str` subclasses checked by a strict pattern
  schema when a model validates. Reading a row: pass the stored plain strings into `Model.model_validate({...})`.
  Building one alone (`next_case_ref`): a module-level `_CASE_REF: TypeAdapter[CaseRef] = TypeAdapter(CaseRef)`, then
  `_CASE_REF.validate_python(text)`.
- `MeridianModel` is `frozen=True, extra="forbid", hide_input_in_errors=True, str_strip_whitespace=True`. A stored string
  with leading or trailing spaces comes back stripped, so test sentences have none.
- `FollowUp.window` is required (`"morning" | "afternoon" | "any"`; OpenAPI `FollowUpView` requires it too). So
  `followups.contact_window` is `NOT NULL` and `FollowupRow.window` is required.
- `TurnPath` includes `"degraded"`; `RunTag` is `"live" | "eval" | "load"`; `CaseState` is the seven lifecycle strings
  of `Lifecycle` below.
- `CompletedAction.records` keys are `Literal["appointment", "slot", "old_slot", "case", "customer", "promise"]`;
  `before` and `after` are `dict[str, str] | None`.

### 4.2 Third-party

- `sqlite3` (stdlib); `pydantic` (`Field`, `JsonValue`, `TypeAdapter` if needed); `zoneinfo.ZoneInfo`.
- `from langgraph.checkpoint.sqlite import SqliteSaver` (package `langgraph-checkpoint-sqlite`, pinned by AEA-01 with
  LangGraph 1.2.16). Tests: `from langgraph.checkpoint.base import empty_checkpoint`.

### 4.3 What this ticket exports (exact signatures; consumers build against these)

**`adapters/sqlite/db.py`**

```python
BUSY_TIMEOUT_MS = 5000                      # [A] DO-3 §4.3 "busy_timeout 5 s"; replaced by the Stage 9 load re-measure

class StorageError(Exception):
    """A storage failure naming the table and the constraint kind, never a value (safe-validation-errors)."""
    def __init__(self, table: str, constraint: str) -> None: ...   # str(exc) == f"{table}: {constraint}"
    table: str; constraint: str

@contextmanager
def integrity_errors(table: str) -> Iterator[None]: ...
    # catches sqlite3.IntegrityError and raises StorageError(table, kind) FROM NONE, kind by message prefix:
    # "UNIQUE" | "FOREIGN KEY" | "CHECK" | "NOT NULL" | else "INTEGRITY". Never copies the sqlite message.

def connect(path: Path, *, read_only: bool = False, busy_timeout_ms: int = BUSY_TIMEOUT_MS) -> sqlite3.Connection: ...
def format_wall(dt: datetime) -> str: ...   # tz-aware → dt.astimezone(UTC).isoformat(); naive → ValueError("naive datetime")
def parse_wall(text: str) -> datetime: ...  # datetime.fromisoformat(text) → tz-aware; .astimezone(UTC); naive text → ValueError
def last_row_id(cur: sqlite3.Cursor, table: str) -> int: ...   # added: cur.lastrowid; None → StorageError(table, "no row id")

class SqliteUnitOfWork:                     # implements ports.runtime.UnitOfWork
    core: CoreRepos; spend: SpendRepo; identity: IdentityRepos; booking: BookingRepos
    cases: CaseRepos; staff: StaffRepos; ops: OpsRepos
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    @property
    def connection(self) -> sqlite3.Connection: ...   # added: restore_working_copy and tests
    @property
    def committed(self) -> bool: ...
    def commit(self) -> None: ...           # COMMIT once; a second call is a no-op

class SqliteUnitOfWorkFactory:              # implements ports.runtime.UnitOfWorkFactory
    def __init__(self, db_path: Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS) -> None: ...
    @property
    def db_path(self) -> Path: ...
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> ContextManager[SqliteUnitOfWork]: ...
```

**`adapters/sqlite/rows.py`** — every class subclasses `MeridianModel` (frozen, `extra="forbid"`). Datetimes are
tz-aware (read back through `parse_wall`, so UTC-aware; equality with a Chicago-aware value holds).

```python
StreamKey = NewType("StreamKey", str)                       # DO-4 §13 names it, nothing sketches it; AEA-10 owns `events`
CASE_STREAM_PREFIX = "case:"
def thread_stream(thread_id: ThreadId) -> StreamKey: ...    # StreamKey(str(thread_id)): the thread form is the bare id
def case_stream(case_ref: CaseRef) -> StreamKey: ...        # StreamKey(CASE_STREAM_PREFIX + str(case_ref)) (staff.md §7)

class ConversationRow(MeridianModel):
    thread_id: ThreadId; demo_session: str
    run_tag: Literal["live", "eval", "load", "seed"]; run_id: str | None = None; agent_version: str
    started_at: datetime                                    # demo clock
    started_wall_at: datetime | None = None                 # wall clock, UTC
    staffing_at_start: Literal["nobody_online", "simulated_on_shift"] | None = None
    outcome: Literal["ai_resolved", "handed_off", "safety_reply", "abandoned", "open"] = "open"
    ended_wall_at: datetime | None = None
    last_customer_wall_at: datetime | None = None
    controller: Controller = Field(default_factory=lambda: Controller(kind="ai"))
    live_state: Literal["not_live", "queued", "joined", "handed_back", "closed"] = "not_live"
    live_since: datetime | None = None

class EndedThread(MeridianModel):                           # cases.md §1.2, verbatim fields
    thread_id: ThreadId; demo_session: str; ended_wall_at: datetime; reason: str; reset_id: str | None

class Cleared(MeridianModel):                               # cases.md §1.2, verbatim fields
    open_threads: tuple[ThreadId, ...]; case_streams: tuple[CaseRef, ...]
    roles_reset: int; rows_cleared: dict[str, int]

class MessageRow(MeridianModel):
    id: int; thread_id: ThreadId; role: Literal["customer", "assistant", "representative"]
    text: str; at: datetime; turn_id: TurnId | None = None
    kind: Literal["text", "choice", "code", "form"] | None = None
    card_id: str | None = None; choice_option: str | None = None

class TurnBegin(MeridianModel):                             # DO-4 §13 "new | completed(stored response) | running | failed"
    status: Literal["new", "completed", "running", "failed"]
    response: str | None = None                             # set only for "completed"

class TurnRow(MeridianModel):                               # one turns row as stored
    turn_id: TurnId; thread_id: ThreadId; request_id: RequestId
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; agent_version: str
    sequence: int; received_at: datetime; status: Literal["running", "completed", "failed"]
    gate_result: str | None = None; path: str | None = None; outcome: str | None = None
    degrade_reason: str | None = None; planner: PlannerTrace | None = None
    danger_raised: bool | None = None; specialists_run: tuple[str, ...] = ()
    replied_at: datetime | None = None; server_ms: int | None = None
    model_calls: int | None = None; input_tokens: int | None = None; output_tokens: int | None = None
    cost_usd: float | None = None; tool_calls: int | None = None
    trace_id: str | None = None; trace_export: ExportStatus | None = None; response: str | None = None
    def as_record(self) -> TurnRecord | None: ...           # None while running or when a TurnRecord field is NULL
                                                            #   (e.g. a row fail_running swept); else
                                                            #   TurnRecord.model_validate({...})

class StreamEvent(MeridianModel):                           # what a writer appends (DO-4 §13 named it, no sketch)
    type: str = Field(min_length=1, max_length=40)          # OpenAPI ChatEvent / CaseEvent type, e.g. "demo_reset"
    payload: dict[str, JsonValue] = Field(default_factory=dict)   # the event's data fields, writer-shaped
    at: datetime                                            # demo clock

class EventRow(MeridianModel):
    id: EventId; stream: str; type: str; payload: dict[str, JsonValue]; at: datetime

class CustomerRow(MeridianModel):                           # issued columns (SCHEMA.md)
    customer_id: CustomerId; name: str; phone: str; email: str | None
    service_address: str; city: str; zip: str
    membership_tier: Literal["none", "standard", "plus"]
    membership_renewal_date: date | None; system_brand: str | None; system_install_date: date | None

class InvoiceRow(MeridianModel):                            # issued columns; line_items parsed from JSON
    invoice_id: InvoiceId; customer_id: CustomerId; appointment_id: int | None
    issued_date: date; due_date: date; amount_cents: int; balance_cents: int
    line_items: tuple[dict[str, JsonValue], ...]

class AppointmentRow(MeridianModel):                        # issued appointment + its slot + technician; never issue_description
    appointment_id: int; slot_id: int; customer_id: CustomerId
    status: Literal["scheduled", "completed", "cancelled", "no_show"]; is_warranty_visit: bool; created_at: date
    slot_date: date; window: str; zone: str; service_type: str; tech_id: int; technician: str

class CaseOwnerRow(MeridianModel):                          # cases.md §1.2 "(thread_id, owner_role, owner_since, lifecycle)"
    thread_id: ThreadId; owner_role: StaffRole | None; owner_since: datetime | None; lifecycle: str

# --- case store rows (repos_cases) ---
Lifecycle = Literal["live_queued", "unassigned", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved"]

class CaseRow(MeridianModel):
    case_ref: CaseRef; thread_id: ThreadId; turn_id: TurnId | None = None; customer_id: CustomerId | None = None
    reason: HandoffReason; priority: Priority; rule_id: str; trigger: str
    lifecycle: Lifecycle; owner_role: StaffRole | None = None; owner_since: datetime | None = None
    due_at: datetime | None = None                          # the CASE due (CAS-10)
    wake_up_at: datetime | None = None; version: int = Field(default=1, ge=1); seed: bool = False
    safety_kind: str | None = None; change_request: dict[str, JsonValue] | None = None
    alert: Literal["supervisor_now"] | None = None
    created_at: datetime; updated_at: datetime; resolved_at: datetime | None = None; queued_at: datetime | None = None

class CaseEventRow(MeridianModel):
    id: int | None = None; case_ref: CaseRef; kind: str = Field(min_length=1, max_length=40)
    key: str = ""                                           # idempotency key (scheduler); "" = none
    actor_role: Literal["representative", "supervisor", "owner", "ai", "system"]
    job_run_id: str | None = None; detail: dict[str, JsonValue] = Field(default_factory=dict); at: datetime

class PromiseRow(MeridianModel):
    id: int; case_ref: CaseRef; promise: Promise            # promise.due_at = the CUSTOMER due (CAS-10)
    status: Literal["open", "kept", "missed", "changed"]
    created_at: datetime; status_at: datetime | None = None; status_reason: str | None = None

class FollowupRow(MeridianModel):                           # OpenAPI FollowUpView fields + storage keys
    case_ref: CaseRef; thread_id: ThreadId; channel: Literal["email", "phone"]
    destination_label: str; destination: str | None = None  # raw destination for staff; never in a log
    on_record: bool; window: Literal["morning", "afternoon", "any"]; saved_line: str; updated_at: datetime

class ActivityRow(MeridianModel):
    id: int | None = None; case_ref: CaseRef; kind: Literal["call", "email"]
    outcome: Literal["reached", "no_answer", "left_message"]; note: str | None = None
    actor_role: StaffRole; at: datetime

class DemoStateRow(MeridianModel):
    demo_now: datetime; staffing: Literal["nobody_online", "simulated_on_shift"]

class DemoEventRow(MeridianModel):                          # cases.md §1.1 demo_events, verbatim columns
    demo_event_id: str; at_wall: datetime; kind: Literal["clock_advanced", "staffing_changed"]
    step: str | None = None; mode: str | None = None
    demo_before: str; demo_after: str                       # clock: format_wall of the demo times; staffing: the modes
    became_overdue: int | None = None; converted_cases: int | None = None; request_id: str; role: str

class JobRunRow(MeridianModel):
    job_run_id: str; started_wall_at: datetime; finished_wall_at: datetime | None; demo_now: datetime
    status: Literal["started", "completed", "failed"]; error_kind: str | None; counts: dict[str, int | None]

class ResetEventRow(MeridianModel):
    reset_id: str; at_wall: datetime; asked_by_role: DemoRole | None = None; asked_by_session: str | None = None
    request_id: str | None = None; restored: dict[str, int] = Field(default_factory=dict)
    open_chats_ended: int = 0; roles_reset: int = 0; checkpoints_cleared: bool | None = None

class SeedEventRow(MeridianModel):
    seed_event_id: str; at_wall: datetime; reset_id: str | None = None; deploy_id: str | None = None
    seed_count: int = Field(ge=0); label: str = "demo seed"
```

**`adapters/sqlite/repos_core.py`** — every sub-repository takes the uow's connection; none commits. "added" = derived
from a consumer, not in cases.md §1.2.

```python
class ConversationsRepo:                                    # tx.core.conversations
    def insert(self, row: ConversationRow) -> None: ...                                 # added (AEA-40 open, AEA-31 seeds)
    def lookup(self, thread_id: str) -> ConversationRow | EndedThread | None: ...       # any string, never raises on a
                                                                                        #   malformed id (web.md §4)
    def set_outcome(self, thread_id: ThreadId, outcome: str, *,
                    ended_wall_at: datetime | None = None) -> None: ...                 # added (AEA-30, 40, 42)
    def set_last_customer_wall_at(self, thread_id: ThreadId, at_wall: datetime) -> None: ...   # added (AEA-40)
    def set_controller(self, thread_id: ThreadId, controller: Controller, *,
                       live_state: str, live_since: datetime | None) -> None: ...       # added (AEA-46)
    def set_live_state(self, thread_id: ThreadId, live_state: str,
                       live_since: datetime | None) -> None: ...                        # added (AEA-29)
    def open_thread_ids(self) -> tuple[ThreadId, ...]: ...    # added: live_state <> 'closed', by started_at, thread_id
    def idle_live(self, cutoff_wall: datetime) -> tuple[tuple[ThreadId, datetime], ...]: ...   # added (AEA-30 sweep):
        # run_tag='live' AND outcome='open' AND last_customer_wall_at IS NOT NULL AND last_customer_wall_at <= cutoff
    def last_started_wall(self) -> datetime | None: ...      # added (AEA-32 zero-traffic): MAX(started_wall_at), live only
    # every set_* raises StorageError("conversations", "no row") when no row matched

class MessagesRepo:                                         # tx.core.messages
    def append(self, thread_id: ThreadId, role: str, text_redacted: str, at: datetime, *,
               turn_id: TurnId | None = None, kind: str | None = None, card_id: str | None = None,
               choice_option: str | None = None) -> int: ...   # cases.md §1.2 + keywords (AEA-40-3)
    def recent(self, thread_id: ThreadId, turns: int) -> tuple[MessageRow, ...]: ...    # §5 step 6 algorithm
    def all_for_thread(self, thread_id: ThreadId) -> tuple[MessageRow, ...]: ...        # added; id ascending
    def belongs_to_case(self, message_id: int | str, case_ref: CaseRef) -> bool: ...
    def handoff_anchor(self, thread_id: ThreadId) -> int: ...

class TurnsRepo:                                            # tx.core.turns
    def begin(self, ids: TurnIds, received_at: datetime) -> TurnBegin: ...
    def finish(self, turn_id: TurnId, record: TurnRecord) -> None: ...
    def timeouts_for(self, thread_id: ThreadId) -> int: ...
    def fail_running(self) -> tuple[TurnId, ...]: ...
    def get(self, turn_id: TurnId) -> TurnRow | None: ...                               # added
    def for_thread(self, thread_id: ThreadId) -> tuple[TurnRow, ...]: ...               # added; by sequence

class ActionsRepo:                                          # tx.core.actions
    def record(self, action: CompletedAction) -> CompletedAction: ...
    def for_thread(self, thread_id: ThreadId) -> tuple[CompletedAction, ...]: ...       # id ascending

class LookupLogRepo:                                        # tx.core.lookup_log
    def append(self, entry: LookupEntry) -> int: ...
    def for_thread(self, thread_id: ThreadId) -> tuple[LookupRow, ...]: ...             # id ascending

class CheckEventsRepo:                                      # tx.core.check_events
    def append(self, event: CheckEvent, thread_id: ThreadId, *, at: datetime | None = None) -> int: ...
        # at None → the turns.received_at of event.turn_id (NULL when no turn row)
    def for_thread(self, thread_id: ThreadId) -> tuple[CheckEvent, ...]: ...            # added; id ascending

class EventsRepo:                                           # tx.core.events
    def append(self, stream: StreamKey, event: StreamEvent) -> EventId: ...
    def after(self, stream: StreamKey, last: EventId) -> list[EventRow]: ...
    def latest_of(self, stream: StreamKey, kind: str) -> EventId | None: ...
    def latest_id(self, stream: StreamKey) -> EventId: ...                              # added; 0 when the stream has none

class ReadsRepo:                                            # tx.core.reads (read-only queries)
    def invoice(self, invoice_id: InvoiceId) -> InvoiceRow | None: ...
    def appointment(self, appointment_id: int) -> AppointmentRow | None: ...
    def customer(self, customer_id: CustomerId) -> CustomerRow | None: ...
    def identity_state(self, thread_id: ThreadId) -> IdentityState: ...
    def new_flags_count(self) -> int: ...

class ResetRepo:                                            # tx.core.reset
    def clear_demo_tables(self, reset_id: str, *, ended_at: datetime | None = None) -> Cleared: ...

class CasesReadRepo:                                        # tx.core.cases_ro
    def owner(self, case_ref: CaseRef) -> CaseOwnerRow | None: ...

class CoreRepos:                                            # AEA-02 shell name; = UnitOfWork.core
    conversations: ConversationsRepo; messages: MessagesRepo; turns: TurnsRepo; actions: ActionsRepo
    lookup_log: LookupLogRepo; check_events: CheckEventsRepo; events: EventsRepo
    reads: ReadsRepo; reset: ResetRepo; cases_ro: CasesReadRepo
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def settled_for(self, thread_id: ThreadId, read_at: datetime) -> Settled: ...      # graph-core §6
```

**`adapters/sqlite/repos_cases.py`**

```python
DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))   # CAS-23, verbatim
SEED_REF_MAX = 8                                            # seeds hold MHC-C-0005…0008 (cases.md §7, CAS-24)
CLOSED_LIFECYCLES = ("resolved", "closed_unresolved")

class CasesRepo:                                            # tx.cases.cases
    def insert(self, row: CaseRow) -> None: ...
    def get(self, case_ref: CaseRef) -> CaseRow | None: ...
    def get_for_thread_open(self, thread_id: ThreadId) -> CaseRow | None: ...    # newest non-closed case of the thread
    def list_open(self) -> tuple[CaseRow, ...]: ...                              # non-closed, by created_at, case_ref
    def list_for_thread(self, thread_id: ThreadId) -> tuple[CaseRow, ...]: ...   # added
    def list_for_customer(self, customer_id: CustomerId) -> tuple[CaseRow, ...]: ...   # added (CON-12 other_cases)
    def update_versioned(self, case_ref: CaseRef, expected_version: int, **changes: object) -> int | None: ...
        # one UPDATE … SET <changes>, version = version + 1 WHERE case_ref = ? AND version = ?; returns the new
        # version, or None when no row matched (stale version or unknown case). Allowed keys: lifecycle, owner_role,
        # owner_since, due_at, wake_up_at, priority, reason, resolved_at, queued_at, alert, customer_id, updated_at;
        # any other key → ValueError("unknown case column") (no value in the message). Empty changes → ValueError.

class CaseEventsRepo:                                       # tx.cases.case_events
    def append(self, event: CaseEventRow) -> int: ...
    def exists(self, case_ref: CaseRef, kind: str, key: str) -> bool: ...
    def list_for_case(self, case_ref: CaseRef) -> tuple[CaseEventRow, ...]: ...  # added; id ascending

class PromisesRepo:                                         # tx.cases.promises
    def insert(self, case_ref: CaseRef, promise: Promise, at: datetime) -> int: ...   # status 'open'
    def current(self, case_ref: CaseRef) -> PromiseRow | None: ...               # added: newest row of the case
    def history(self, case_ref: CaseRef) -> tuple[PromiseRow, ...]: ...          # added: id ascending
    def set_status(self, case_ref: CaseRef, status: str, at: datetime, reason: str) -> bool: ...
        # updates the CURRENT row only; False when the case has no promise
    def list_open_past(self, now: datetime) -> list[PromiseRow]: ...
        # current rows with status 'open' AND due_at IS NOT NULL AND due_at < format_wall(now)

class FollowupsRepo:                                        # tx.cases.followups
    def upsert(self, row: FollowupRow) -> None: ...
    def get(self, case_ref: CaseRef) -> FollowupRow | None: ...

class ActivitiesRepo:                                       # tx.cases.activities
    def insert(self, row: ActivityRow) -> int: ...
    def list_for_case(self, case_ref: CaseRef) -> tuple[ActivityRow, ...]: ...   # at, then id ascending

class BriefsRepo:                                           # tx.cases.briefs — added ("the brief rows", attach_brief upsert)
    def upsert(self, brief: Brief, at: datetime) -> None: ...                    # replaces the stored brief of brief.case_ref
    def get(self, case_ref: CaseRef) -> Brief | None: ...

class DemoStateRepo:                                        # tx.cases.demo_state
    def get(self) -> DemoStateRow: ...                      # no row → DemoStateRow(demo_now=DEMO_START, staffing="nobody_online")
    def set_now(self, dt: datetime) -> None: ...            # upsert row id 1, keeps staffing
    def set_staffing(self, mode: str) -> None: ...          # upsert row id 1, keeps demo_now (DEMO_START when no row)
    def reset(self) -> None: ...                            # demo_now = DEMO_START, staffing = 'nobody_online'

class DemoEventsRepo:                                       # tx.cases.demo_events
    def insert(self, row: DemoEventRow) -> None: ...

class JobRunsRepo:                                          # tx.cases.job_runs
    def start(self, job_run_id: str, *, started_wall_at: datetime, demo_now: datetime) -> None: ...   # status 'started'
    def finish(self, job_run_id: str, status: str, counts: Mapping[str, int | None], error_kind: str | None, *,
               finished_wall_at: datetime | None = None) -> None: ...      # None → datetime.now(UTC) (§8 R-5)
    def latest(self) -> JobRunRow | None: ...               # newest started_wall_at, then job_run_id

class RecordsRepo:                                          # tx.cases.records
    def reset_event(self, row: ResetEventRow) -> None: ...
    def seed_event(self, row: SeedEventRow) -> None: ...
    def seed_rows_present(self) -> bool: ...                # EXISTS (SELECT 1 FROM cases WHERE seed = 1)
    def set_checkpoints_cleared(self, reset_id: str, cleared: bool) -> None: ...  # added (cases.md §7 residual window)
    def latest_reset_event(self) -> ResetEventRow | None: ...                     # added
    def latest_seed_event(self) -> SeedEventRow | None: ...                       # added

class RefsRepo:                                             # tx.cases.refs
    def next_case_ref(self) -> CaseRef: ...                 # max(max numeric part of cases.case_ref, SEED_REF_MAX) + 1

class CaseRepos:                                            # AEA-02 shell name; = UnitOfWork.cases
    cases: CasesRepo; case_events: CaseEventsRepo; promises: PromisesRepo; followups: FollowupsRepo
    activities: ActivitiesRepo; briefs: BriefsRepo; demo_state: DemoStateRepo; demo_events: DemoEventsRepo
    job_runs: JobRunsRepo; records: RecordsRepo; refs: RefsRepo
    def __init__(self, conn: sqlite3.Connection) -> None: ...
```

**`adapters/sqlite/migrate.py`**

```python
WORKING_DB_NAME = "meridian.sqlite"
SCHEMA_DIR: Path                                            # Path(__file__).with_name("schema")
ISSUED_TABLES = ("customers", "technicians", "appointment_slots", "appointments", "invoices")   # parents first
CLEARED_TABLES = ("lookup_log", "check_events", "actions", "turns", "messages", "events", "case_briefs",
                  "activities", "followups", "promises", "case_events", "cases", "conversations", "flags",
                  "identity_codes", "demo_inbox", "identity_threads")           # children first (delete order)
UPDATED_TABLES = ("staff_sessions", "demo_state")
KEPT_TABLES = ("spend_ledger", "health_events", "deploy_records", "eval_runs", "eval_case_results", "job_runs",
               "demo_events", "reset_events", "seed_events", "ended_threads")
def schema_files() -> tuple[Path, ...]: ...                 # every SCHEMA_DIR/NN_name.sql, sorted by int(NN)
def migrate(db_path: Path, *, issued_path: Path) -> bool: ...   # True when this call copied the issued file
def restore_working_copy(tx: UnitOfWork, *, issued_path: Path) -> None: ...
```
(`ResetRepo.clear_demo_tables` imports `CLEARED_TABLES` from `migrate.py`; `migrate.py` must not import `repos_core.py`.)

**`adapters/checkpointer.py`**

```python
CHECKPOINTS_DB_NAME = "checkpoints.sqlite"
class Checkpointer:
    def __init__(self, path: Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS) -> None: ...
    @property
    def saver(self) -> SqliteSaver: ...                     # what AEA-51 compiles the graph with
    @property
    def path(self) -> Path: ...
    def prune(self, keep: int = 2) -> int: ...              # [Decided SDQ-10]
    def clear(self) -> None: ...
    def clearing(self) -> ContextManager[None]: ...
    def close(self) -> None: ...                            # idempotent
    @property
    def closed(self) -> bool: ...                           # added: True after close() (test_register_storage)
```

**`tests/fixtures/sqlite.py`**

```python
ISSUED_DB: Path   # Path(__file__).resolve().parents[2] / "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
@dataclass(frozen=True)
class TempStore:
    data_dir: Path; db_path: Path; issued_path: Path; uow: SqliteUnitOfWorkFactory
@contextmanager
def temp_sqlite(*, issued_path: Path = ISSUED_DB) -> Iterator[TempStore]: ...
```

---

## 5. Steps (build order; each step checkable)

Module boundary: everything lives in `adapters/sqlite/` and `adapters/checkpointer.py` (DO-3 §3, §4.3). The interfaces
this slice **implements** are `ports.runtime.UnitOfWork` / `UnitOfWorkFactory`; it **consumes** only `domain/*` types. No
new abstraction or Protocol is introduced. Import graph (must stay acyclic at import time): `rows.py` → `domain`, `db.py`
(formatters); `repos_core.py` / `repos_cases.py` → `db.py`, `rows.py`, `migrate.py` (table constants only), `domain`;
`migrate.py` → `db.py`, `ports.runtime` (type only); `checkpointer.py` → `db.py` (`BUSY_TIMEOUT_MS`); `db.py` → `domain`
only at module level, and the seven repository classes **inside** `SqliteUnitOfWork.__init__` (step 1.4). Nothing here
imports `services/`, `agent/`, `web/` or `config.py` (the container hands paths in).

Environment first: `export UV_LINK_MODE=hardlink`; `uv sync` (no venv copy, no `node_modules`).

### Step 1 — `db.py` (AC-8, AC-9, AC-10, AC-11, AC-20 mechanism)

1. `connect(path, *, read_only=False, busy_timeout_ms=BUSY_TIMEOUT_MS)`:
   - `read_only=False`: `sqlite3.connect(str(path), timeout=busy_timeout_ms / 1000, isolation_level=None,
     check_same_thread=False)`; then `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=<busy_timeout_ms>`,
     `PRAGMA foreign_keys=ON`.
   - `read_only=True`: same, but the target is `f"{path.resolve().as_uri()}?mode=ro"` with `uri=True`, and **no**
     `journal_mode` PRAGMA (a read-only connection must not try to change the file).
   - Invariant protected: every connection waits ≤ 5 s for a lock and enforces FKs; transactions are only the explicit
     `BEGIN`s the factory issues.
2. `format_wall(dt)`: `if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError("naive datetime")`; return
   `dt.astimezone(timezone.utc).isoformat()` (whole seconds print as `…T15:00:00+00:00`). `parse_wall(text)`:
   `d = datetime.fromisoformat(text)`; naive → `ValueError("naive timestamp")`; return `d.astimezone(timezone.utc)`.
   One format everywhere keeps TEXT comparison in SQL equal to time order.
3. `StorageError` and `integrity_errors(table)` exactly as §4.3. The message is `f"{table}: {constraint}"`; raise with
   `from None`.
4. `SqliteUnitOfWork.__init__(conn)`: store `conn`; build `CoreRepos(conn)`, `SpendRepo(conn)`, `IdentityRepos(conn)`,
   `BookingRepos(conn)`, `CaseRepos(conn)`, `StaffRepos(conn)`, `OpsRepos(conn)`. **Import the seven classes inside
   `__init__`** (one local import block; the project's ruff rule sets do not flag local imports; with the comment "repositories import this
   module's helpers; a top-level import would be circular"), and import them again under `if TYPE_CHECKING:` at module
   top for the attribute annotations. Reason: `repos_core`, `repos_cases` and the owners' bodies (AEA-26/27/28/32/44)
   import `format_wall`, `parse_wall` and `integrity_errors` from `db.py`. `commit()`: if not committed →
   `conn.execute("COMMIT")`, set the flag; else return.
5. `SqliteUnitOfWorkFactory.__call__` as a generator-based context manager:
   1. `conn = connect(self._db_path, busy_timeout_ms=self._busy_timeout_ms)`.
   2. If `exclusive`: `BEGIN EXCLUSIVE`; elif `write`: `BEGIN IMMEDIATE`; else `PRAGMA query_only=ON` then
      `BEGIN DEFERRED`. **If this `BEGIN` raises (lock timeout), close the connection and re-raise before yielding** —
      the caller's block never runs, so no statement executes (AC-9; DO-1 §8.2 "lock timeout → no write").
   3. `uow = SqliteUnitOfWork(conn)`; `yield uow`.
   4. On any exception from the block: `if conn.in_transaction: conn.execute("ROLLBACK")`; re-raise.
   5. `finally`: if not `uow.committed` and `conn.in_transaction`: `ROLLBACK`; `conn.close()`.
   - Invariant: a unit of work commits only when `commit()` ran and nothing raised after; one connection per uow; a read
     uow can never write (`query_only`).
6. `last_row_id(cur, table)`: `rid = cur.lastrowid`; `None` → `raise StorageError(table, "no row id")`; else `int(rid)`.
   Every `append` / `insert` that returns an id uses it.
7. **Ruff `S608`** (the project selects the `S` rules) flags SQL built with an f-string. In this slice an f-string may
   interpolate only a module constant: a table name from `ISSUED_TABLES` / `CLEARED_TABLES`, a column list read from the
   issued file's `cursor.description`, or a column name from `update_versioned`'s allow-list. Put `# noqa: S608` on that
   line, with the reason in the same comment. Values always go through `?` parameters.

### Step 2 — DDL files (AC-1, AC-21, PA-1)

Every statement is `CREATE TABLE IF NOT EXISTS` / `CREATE [UNIQUE] INDEX IF NOT EXISTS`, so re-applying on every boot is
safe. Times are TEXT written by `format_wall`; dates are ISO `YYYY-MM-DD`; booleans INTEGER 0/1; JSON is TEXT. Column
names avoid SQL keywords (`check_kind`, `before_json`, `event_key`, `contact_window`, `handoff_trigger`, `git_commit`).
Write each file with a one-line header comment naming the owner (AEA-10) and the source section.

**`00_core.sql`**

```sql
CREATE TABLE IF NOT EXISTS conversations (
  thread_id TEXT PRIMARY KEY,
  demo_session TEXT NOT NULL,
  run_tag TEXT NOT NULL CHECK (run_tag IN ('live','eval','load','seed')),
  run_id TEXT,
  agent_version TEXT NOT NULL,
  started_at TEXT NOT NULL,
  started_wall_at TEXT,
  staffing_at_start TEXT CHECK (staffing_at_start IN ('nobody_online','simulated_on_shift')),
  outcome TEXT NOT NULL DEFAULT 'open' CHECK (outcome IN ('ai_resolved','handed_off','safety_reply','abandoned','open')),
  ended_wall_at TEXT,
  last_customer_wall_at TEXT,
  controller TEXT NOT NULL DEFAULT 'ai' CHECK (controller IN ('ai','human')),
  controller_name TEXT,
  controller_case_ref TEXT,
  live_state TEXT NOT NULL DEFAULT 'not_live' CHECK (live_state IN ('not_live','queued','joined','handed_back','closed')),
  live_since TEXT
);
CREATE INDEX IF NOT EXISTS ix_conversations_idle ON conversations (run_tag, outcome, last_customer_wall_at);
CREATE TABLE IF NOT EXISTS ended_threads (
  thread_id TEXT PRIMARY KEY,
  demo_session TEXT NOT NULL,
  ended_wall_at TEXT NOT NULL,
  reason TEXT NOT NULL,
  reset_id TEXT
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('customer','assistant','representative')),
  text TEXT NOT NULL,
  at TEXT NOT NULL,
  turn_id TEXT,
  kind TEXT CHECK (kind IN ('text','choice','code','form')),
  card_id TEXT,
  choice_option TEXT
);
CREATE INDEX IF NOT EXISTS ix_messages_thread ON messages (thread_id, id);
CREATE TABLE IF NOT EXISTS turns (
  turn_id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL,
  request_id TEXT NOT NULL,
  run_tag TEXT NOT NULL CHECK (run_tag IN ('live','eval','load')),
  run_id TEXT,
  agent_version TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  received_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running','completed','failed')),
  gate_result TEXT CHECK (gate_result IN ('clear','safety','burning_unclear','danger','person_requested','ai_paused')),
  path TEXT,
  outcome TEXT CHECK (outcome IN ('answered','acted','safety_reply','handed_off','to_staff','degraded_handoff')),
  degrade_reason TEXT CHECK (degrade_reason IN ('model_error','tool_error','timeout','brake','spend_cap','rate_limit')),
  planner_model TEXT,
  planner_fallback_used INTEGER,
  planner_failure TEXT,
  plan_mode TEXT,
  plan_source TEXT,
  plan_intents TEXT,
  plan_handoff_request TEXT,
  plan_topic TEXT,
  planner_failed INTEGER,
  danger_raised INTEGER,
  specialists_run TEXT NOT NULL DEFAULT '[]',
  replied_at TEXT,
  server_ms INTEGER,
  model_calls INTEGER,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd REAL,
  tool_calls INTEGER,
  trace_id TEXT,
  trace_export TEXT CHECK (trace_export IN ('off','sent','failed')),
  response TEXT
);
CREATE INDEX IF NOT EXISTS ix_turns_thread ON turns (thread_id, sequence);
CREATE INDEX IF NOT EXISTS ix_turns_status ON turns (status);
CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  turn_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('booked','moved','cancelled','change_request_sent','case_opened','followup_saved','verified')),
  record_id TEXT NOT NULL,
  records_json TEXT NOT NULL,
  before_json TEXT,
  after_json TEXT,
  at TEXT NOT NULL,
  UNIQUE (thread_id, turn_id, kind, record_id)
);
CREATE INDEX IF NOT EXISTS ix_actions_thread ON actions (thread_id, id);
CREATE TABLE IF NOT EXISTS lookup_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  turn_id TEXT NOT NULL,
  message_id INTEGER NOT NULL REFERENCES messages(id),
  tool TEXT NOT NULL,
  record_ids TEXT NOT NULL,
  passage_ids TEXT NOT NULL,
  result_seen TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_lookup_thread ON lookup_log (thread_id, id);
CREATE TABLE IF NOT EXISTS check_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL,
  at TEXT,
  check_kind TEXT NOT NULL CHECK (check_kind IN ('completion','fact','brief_fact','brief_quote','gate','classifier','brake')),
  turn_id TEXT NOT NULL,
  result TEXT NOT NULL CHECK (result IN ('pass','trimmed','fallback','fired','raised')),
  removed INTEGER NOT NULL DEFAULT 0,
  claim_kinds TEXT NOT NULL DEFAULT '[]',
  codes TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS ix_check_events_thread ON check_events (thread_id, id);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stream TEXT NOT NULL,
  type TEXT NOT NULL,
  payload TEXT NOT NULL,
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_events_stream ON events (stream, id);
CREATE INDEX IF NOT EXISTS ix_events_stream_type ON events (stream, type, id);
```

**`20_spend.sql`** — models.md §6, exactly:

```sql
CREATE TABLE IF NOT EXISTS spend_ledger (
  id INTEGER PRIMARY KEY,
  recorded_at TEXT NOT NULL,
  thread_id TEXT, turn_id TEXT, request_id TEXT,
  run_tag TEXT CHECK (run_tag IN ('live','eval','load')), run_id TEXT, agent_version TEXT,
  role TEXT, provider TEXT, model TEXT, attempt INTEGER, latency_ms INTEGER,
  input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER, cache_write_tokens INTEGER, thinking_tokens INTEGER,
  cost_usd REAL, cost_source TEXT, status TEXT, failure_kind TEXT, http_status INTEGER,
  provider_request_id TEXT, stop_reason TEXT
);
CREATE INDEX IF NOT EXISTS ix_spend_recorded_at ON spend_ledger (recorded_at);
CREATE INDEX IF NOT EXISTS ix_spend_turn ON spend_ledger (turn_id);
CREATE INDEX IF NOT EXISTS ix_spend_thread ON spend_ledger (thread_id);
```

**`40_identity.sql`** — graph-tools §5, exactly (plus one index):

```sql
CREATE TABLE IF NOT EXISTS identity_threads (
  thread_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('not_checked','located','code_sent','verified','not_verified','locked')),
  customer_id TEXT NULL, masked_hint TEXT NULL,
  channel TEXT NULL CHECK (channel IN ('phone','email')),
  verified_at TEXT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS identity_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, customer_id TEXT NOT NULL,
  code_hmac TEXT NOT NULL, held_by TEXT NOT NULL, sent_at TEXT NOT NULL, expires_at TEXT NOT NULL,
  tries_left INTEGER NOT NULL CHECK (tries_left BETWEEN 0 AND 3), used_at TEXT NULL, inbox_message_id INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_identity_codes_thread ON identity_codes (thread_id, id);
CREATE TABLE IF NOT EXISTS demo_inbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT, demo_session TEXT NOT NULL, thread_id TEXT NOT NULL,
  to_masked TEXT NOT NULL, sent_at TEXT NOT NULL, expires_at TEXT NOT NULL
);
```

**`50_booking.sql`** — no new column (cases.md §4.1 lists none); indexes for the queries AEA-28 and `reads` run:

```sql
CREATE INDEX IF NOT EXISTS ix_slots_search ON appointment_slots (zone, service_type, status, slot_date);
CREATE INDEX IF NOT EXISTS ix_appointments_customer ON appointments (customer_id);
CREATE INDEX IF NOT EXISTS ix_invoices_customer ON invoices (customer_id);
```

**`60_cases.sql`**

```sql
CREATE TABLE IF NOT EXISTS cases (
  case_ref TEXT PRIMARY KEY CHECK (case_ref GLOB 'MHC-C-[0-9][0-9][0-9][0-9]'),
  thread_id TEXT NOT NULL,
  turn_id TEXT,
  customer_id TEXT,
  reason TEXT NOT NULL,
  priority TEXT NOT NULL CHECK (priority IN ('P0','P1','P2','P3','P4')),
  rule_id TEXT NOT NULL,
  handoff_trigger TEXT NOT NULL,
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('live_queued','unassigned','claimed','in_progress','waiting','resolved','closed_unresolved')),
  owner_role TEXT CHECK (owner_role IN ('representative','supervisor','owner')),
  owner_since TEXT,
  due_at TEXT,
  wake_up_at TEXT,
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  seed INTEGER NOT NULL DEFAULT 0 CHECK (seed IN (0,1)),
  safety_kind TEXT,
  change_request_json TEXT,
  alert TEXT CHECK (alert IN ('supervisor_now')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  resolved_at TEXT,
  queued_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_cases_thread ON cases (thread_id, created_at);
CREATE INDEX IF NOT EXISTS ix_cases_lifecycle ON cases (lifecycle);
CREATE INDEX IF NOT EXISTS ix_cases_customer ON cases (customer_id);
CREATE TABLE IF NOT EXISTS case_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT NOT NULL REFERENCES cases(case_ref),
  kind TEXT NOT NULL,
  event_key TEXT NOT NULL DEFAULT '',
  actor_role TEXT NOT NULL CHECK (actor_role IN ('representative','supervisor','owner','ai','system')),
  job_run_id TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}',
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_case_events_case ON case_events (case_ref, id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_case_events_key ON case_events (case_ref, kind, event_key) WHERE event_key <> '';
CREATE TABLE IF NOT EXISTS promises (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT NOT NULL REFERENCES cases(case_ref),
  policy_row TEXT NOT NULL,
  text TEXT NOT NULL,
  due_at TEXT,
  due_label TEXT,
  extra_lines TEXT NOT NULL DEFAULT '[]',
  live_queued INTEGER NOT NULL DEFAULT 0 CHECK (live_queued IN (0,1)),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','kept','missed','changed')),
  created_at TEXT NOT NULL,
  status_at TEXT,
  status_reason TEXT
);
CREATE INDEX IF NOT EXISTS ix_promises_case ON promises (case_ref, id);
CREATE TABLE IF NOT EXISTS followups (
  case_ref TEXT PRIMARY KEY REFERENCES cases(case_ref),
  thread_id TEXT NOT NULL,
  channel TEXT NOT NULL CHECK (channel IN ('email','phone')),
  destination_label TEXT NOT NULL,
  destination TEXT,
  on_record INTEGER NOT NULL CHECK (on_record IN (0,1)),
  contact_window TEXT NOT NULL CHECK (contact_window IN ('morning','afternoon','any')),
  saved_line TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT NOT NULL REFERENCES cases(case_ref),
  kind TEXT NOT NULL CHECK (kind IN ('call','email')),
  outcome TEXT NOT NULL CHECK (outcome IN ('reached','no_answer','left_message')),
  note TEXT,
  actor_role TEXT NOT NULL CHECK (actor_role IN ('representative','supervisor','owner')),
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_activities_case ON activities (case_ref, at, id);
CREATE TABLE IF NOT EXISTS case_briefs (
  case_ref TEXT PRIMARY KEY REFERENCES cases(case_ref),
  thread_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ready','being_written','failed')),
  brief_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS demo_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  demo_now TEXT NOT NULL,
  staffing TEXT NOT NULL CHECK (staffing IN ('nobody_online','simulated_on_shift'))
);
CREATE TABLE IF NOT EXISTS demo_events (
  demo_event_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('clock_advanced','staffing_changed')),
  step TEXT NULL, mode TEXT NULL,
  demo_before TEXT NOT NULL, demo_after TEXT NOT NULL,
  became_overdue INTEGER NULL, converted_cases INTEGER NULL,
  request_id TEXT NOT NULL, role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job_runs (
  job_run_id TEXT PRIMARY KEY,
  started_wall_at TEXT NOT NULL,
  finished_wall_at TEXT,
  demo_now TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('started','completed','failed')),
  error_kind TEXT,
  counts_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_job_runs_started ON job_runs (started_wall_at);
CREATE TABLE IF NOT EXISTS reset_events (
  reset_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  asked_by_role TEXT NULL CHECK (asked_by_role IN ('customer','representative','supervisor','owner')),
  asked_by_session TEXT NULL,
  request_id TEXT,
  restored_json TEXT NOT NULL DEFAULT '{}',
  open_chats_ended INTEGER NOT NULL DEFAULT 0,
  roles_reset INTEGER NOT NULL DEFAULT 0,
  checkpoints_cleared INTEGER CHECK (checkpoints_cleared IN (0,1))
);
CREATE TABLE IF NOT EXISTS seed_events (
  seed_event_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  reset_id TEXT NULL,
  deploy_id TEXT NULL,
  seed_count INTEGER NOT NULL,
  label TEXT NOT NULL DEFAULT 'demo seed'
);
```

**`90_staff.sql`** — staff.md §3, exactly:

```sql
CREATE TABLE IF NOT EXISTS staff_sessions (
  token_hash TEXT PRIMARY KEY,
  session_id TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('customer','representative','supervisor','owner')),
  role_reset_pending INTEGER NOT NULL DEFAULT 0,
  signed_in_demo TEXT,
  created_real TEXT,
  expires_real TEXT
);
CREATE TABLE IF NOT EXISTS flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_ref TEXT,
  target TEXT CHECK (target IN ('answer','brief','escalation')),
  message_id TEXT NULL, note TEXT NULL, reason TEXT NULL,
  flagged_by_role TEXT, flagged_at TEXT,
  status TEXT CHECK (status IN ('new','reviewed')),
  reviewed_by_role TEXT NULL, reviewed_note TEXT NULL, reviewed_at TEXT NULL
);
```

**`95_ops.sql`** — cases.md §1.1 + §8 `HealthEvent` / `DeployRecord`; data.md §6 for eval:

```sql
CREATE TABLE IF NOT EXISTS health_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at_wall TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('check_ok','check_failed','restart','alert_fired','alert_cleared')),
  alert_type TEXT NULL, reason_code TEXT NULL, value REAL NULL, threshold REAL NULL,
  agent_version TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_health_events_at ON health_events (at_wall);
CREATE TABLE IF NOT EXISTS deploy_records (
  deploy_id TEXT PRIMARY KEY,
  at_wall TEXT NOT NULL,
  agent_version TEXT NOT NULL,
  git_commit TEXT,
  image_digest TEXT,
  config_hash TEXT,
  trace_export_on INTEGER CHECK (trace_export_on IN (0,1)),
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('started','completed','failed','incomplete'))
);
CREATE TABLE IF NOT EXISTS eval_runs (
  run_id TEXT PRIMARY KEY,
  suite TEXT NOT NULL CHECK (suite IN ('worked-pairs','retrieval','e2e','load')),
  split TEXT CHECK (split IN ('dev','held-out')),
  agent_version TEXT NOT NULL,
  harness_commit TEXT NOT NULL, harness_digest TEXT NOT NULL,
  experiment_id TEXT,
  repeats INTEGER NOT NULL,
  started_at TEXT NOT NULL, finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('started','completed','failed','incomplete')),
  cases_expected INTEGER NOT NULL, cases_scored INTEGER NOT NULL,
  index_manifest_hash TEXT,
  judge_spend_usd REAL NOT NULL DEFAULT 0,
  summary_json TEXT NOT NULL DEFAULT '{}',
  loaded_at TEXT
);
CREATE TABLE IF NOT EXISTS eval_case_results (
  run_id TEXT NOT NULL, case_id TEXT NOT NULL, repeat INTEGER NOT NULL,
  thread_id TEXT,
  passed_hard INTEGER NOT NULL CHECK (passed_hard IN (0,1)),
  items TEXT NOT NULL DEFAULT '[]',
  outcome TEXT NOT NULL CHECK (outcome IN ('resolved','handed_off','degraded','environment_error')),
  in_scope INTEGER, topic TEXT,
  top3 TEXT NOT NULL DEFAULT '[]',
  below_floor INTEGER,
  PRIMARY KEY (run_id, case_id, repeat)
);
```

Check after this step: `uv run python -c` that opens a scratch copy in `/tmp`, runs every file, and lists `sqlite_master`
(no error).

### Step 3 — `rows.py`

Transcribe §4.3's row models and the `StreamKey` block (`from typing import NewType`). Add private helpers here (used by both repos files): `_j(value) -> str`
(`json.dumps(value, separators=(",", ":"), sort_keys=True)`), `_dt(text: str | None) -> datetime | None` (via
`parse_wall`), `_d(text: str | None) -> date | None`, `_w(dt: datetime | None) -> str | None` (via `format_wall`).
Implement `TurnRow.as_record()`: return `None` if `status == "running"` or any of `gate_result`, `path`, `outcome`,
`replied_at`, `server_ms`, `model_calls`, `input_tokens`, `output_tokens`, `cost_usd`, `tool_calls`, `trace_export`,
`response` is `None`; else `TurnRecord.model_validate({"status": status, "trace": {"gate_result", "path", "outcome",
"degrade_reason", "planner": planner, "danger_raised": bool(danger_raised), "specialists_run": specialists_run},
"replied_at", "server_ms", "model_calls", "input_tokens", "output_tokens", "cost_usd", "tool_calls", "trace_id",
"trace_export", "response"})`.

### Step 4 — `migrate.py`: first boot and schema (AC-1, AC-2, AC-3)

1. `schema_files()`: `sorted(SCHEMA_DIR.glob("*.sql"), key=lambda p: int(p.name.split("_", 1)[0]))`; assert each name
   matches `^\d{2}_[a-z_]+\.sql$` (raise `ValueError("bad schema file name")` otherwise).
2. `migrate(db_path, *, issued_path)`:
   1. `copied = False`. If `not db_path.exists()`: `db_path.parent.mkdir(parents=True, exist_ok=True)`;
      `tmp = db_path.with_name(db_path.name + ".tmp")`; `shutil.copyfile(issued_path, tmp)`; `os.replace(tmp, db_path)`;
      `copied = True`. (Atomic: a crash mid-copy never leaves a half file at `db_path`.)
   2. `conn = connect(db_path)` (turns the copy to WAL). For each file in `schema_files()`:
      `conn.executescript("BEGIN;\n" + text + "\nCOMMIT;")` — each file applies whole or not at all.
   3. `conn.close()`; return `copied`.
   - Invariant: an existing working copy is never replaced (AC-2); the issued file is only read.

### Step 5 — `restore_working_copy(tx, *, issued_path)` (AC-3, AC-4, AC-5)

1. `if not isinstance(tx, SqliteUnitOfWork): raise TypeError("restore_working_copy needs a SqliteUnitOfWork")`;
   `dst = tx.connection`. Require `dst.in_transaction` (else `RuntimeError("restore needs an open write transaction")`)
   — it must ride the caller's transaction (CAS-1, CAS-2).
2. Read the issued rows through a **separate** connection:
   `src = sqlite3.connect(f"{issued_path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)`; for each table in
   `ISSUED_TABLES`: `cur = src.execute(f"SELECT * FROM {table} ORDER BY rowid")`; keep `cols = [d[0] for d in
   cur.description]` and `rows = cur.fetchall()`; then `src.close()` (in `finally`). No PRAGMA on `src`.
3. In `dst`: `DELETE FROM` each table in **reverse** `ISSUED_TABLES` order (invoices → … → customers), then
   `executemany(f"INSERT INTO {table} ({cols}) VALUES ({?,…})", rows)` in `ISSUED_TABLES` order (parents first, so FKs
   hold with `foreign_keys=ON`).
4. Sequences: if `dst` has a `sqlite_sequence` table, `UPDATE sqlite_sequence SET seq = ? WHERE name = ?` with the
   issued maximum primary key of each table. Today this updates no row: the issued tables are not `AUTOINCREMENT`
   (checked 2026-10-21), and SQLite then gives the next row `max(rowid) + 1`, so the next appointment is 160 either way.
   Keep the step so the rule holds if a later schema ever adds AUTOINCREMENT.
5. Never `COMMIT`, never touch any other table. Invariant: the restore commits or rolls back with the caller (AC-5).

### Step 6 — `repos_core.py` (AC-7, AC-12…AC-17, AC-20, AC-23, PA-2…PA-4, PA-7)

Each sub-repository: `__init__(self, conn)` stores `self._conn = conn`. Wrap every INSERT/UPDATE/DELETE in
`with integrity_errors("<table>"):`. Write datetimes with `format_wall`, read with `parse_wall`; enums by `.value`.
Re-export the core row models (`__all__`).

- **ConversationsRepo.** `insert`: one INSERT of every `ConversationRow` field (controller → `controller`,
  `controller_name` = `representative_name`, `controller_case_ref` = `case_ref`). `lookup(thread_id: str)`: SELECT from
  `conversations`; found → `ConversationRow`; else SELECT from `ended_threads` → `EndedThread`; else `None`. Never
  validates the input string (a malformed id simply matches nothing). Setters: one UPDATE each, `rowcount == 0` →
  `StorageError("conversations", "no row")`. `open_thread_ids`: `WHERE live_state <> 'closed' ORDER BY started_at,
  thread_id`. `idle_live` and `last_started_wall` as §4.3.
- **MessagesRepo.** `append`: INSERT, return `last_row_id(cur, "messages")`. `recent(thread_id, turns)`: `turns < 1` →
  `ValueError("turns must be >= 1")`. Algorithm:
  1. `ids = SELECT turn_id FROM messages WHERE thread_id=? AND turn_id IS NOT NULL GROUP BY turn_id ORDER BY MIN(id) DESC`.
  2. If `len(ids) <= turns`: return every message of the thread, `ORDER BY id`.
  3. Else `start = SELECT MIN(id) FROM messages WHERE thread_id=? AND turn_id IN (<first `turns` of ids>)`; return
     messages with `id >= start`, `ORDER BY id` (null-turn representative/greeting lines after `start` are kept).
  Character caps are AEA-34's (graph-core §7). `handoff_anchor`: newest `role='customer'` id; else `MIN(id)` of the
  thread (the greeting `SessionService.open` writes first); no message at all → `StorageError("messages", "no anchor")`.
  `belongs_to_case(message_id, case_ref)`: `int(message_id)` (a non-numeric string → `False`); True iff the message's
  `thread_id` equals `cases.thread_id` of that `case_ref`.
- **TurnsRepo.**
  - `begin(ids, received_at)`:
    1. `row = SELECT thread_id, status, response FROM turns WHERE turn_id=?`.
    2. No row → INSERT `turn_id, thread_id, request_id, run_tag, run_id, agent_version, received_at, status='running'`,
       `sequence = (SELECT COALESCE(MAX(sequence), 0) + 1 FROM turns WHERE thread_id=?)` → `TurnBegin(status="new")`.
    3. Row whose `thread_id != ids.thread_id` → `TurnBegin(status="running")`, **write nothing, never return its
       response** (PA-7: a client-chosen `turn_id` must not read another thread's reply).
    4. `completed` → `TurnBegin(status="completed", response=row.response)`; `running` → `TurnBegin(status="running")`.
    5. `failed` → UPDATE `status='running', request_id=?, received_at=?` (re-arm, so a concurrent duplicate now sees
       `running`) → `TurnBegin(status="failed")` (callers run on `new` or `failed`, DO-4 §14).
  - `finish(turn_id, record)`: one UPDATE writing `status = record.status` and every `TurnRecord` / `TurnTrace` /
    `PlannerTrace` field into the columns of step 2 (`planner` None → all planner columns NULL; `plan_intents` and
    `specialists_run` as JSON arrays of values; booleans 0/1). `rowcount == 0` → `StorageError("turns", "no row")`.
  - `timeouts_for`: `SELECT COUNT(*) … WHERE thread_id=? AND degrade_reason='timeout'`.
  - `fail_running`: in the caller's transaction, `ids = SELECT turn_id FROM turns WHERE status='running' ORDER BY
    received_at, turn_id`; then one `UPDATE turns SET status='failed', path='degraded', outcome='degraded_handoff',
    degrade_reason='timeout' WHERE status='running'`; return `tuple(ids)`. No age test (web.md §9).
  - `get` / `for_thread` build `TurnRow` (planner: `PlannerTrace.model_validate` when `planner_model IS NOT NULL`).
- **ActionsRepo.**
  - `record(action)`:
    1. Look up the row by `(thread_id, turn_id, kind, record_id)` from `action.key`.
    2. Found: if its stored `records`, `before`, `after` equal the new action's (compare parsed JSON) → return the
       stored action (AC-12: one row, idempotent retry). If they differ → `raise StorageError("actions", "UNIQUE
       (thread_id, turn_id, kind, record_id)")` (§8 R-3): one key cannot name two different completed writes.
       `at` is not compared (a retry reads the clock again).
    3. Not found: INSERT under `integrity_errors("actions")`; re-select and return the stored action.
    - Never log anything; the error text holds the table and constraint only (AC-20).
  - `for_thread`: `ORDER BY id`; each row → `CompletedAction.model_validate({"key": {...}, "kind", "records",
    "before", "after", "at"})`.
- **LookupLogRepo.** `append(entry)`: one statement `INSERT INTO lookup_log (thread_id, turn_id, message_id, tool,
  record_ids, passage_ids, result_seen) SELECT m.thread_id, ?, m.id, ?, ?, ?, ? FROM messages m WHERE m.id = ?` under
  `integrity_errors`; `rowcount == 0` → `StorageError("lookup_log", "FOREIGN KEY")` (CAS-38: every row names a message;
  `thread_id` is copied in the same transaction). Return `last_row_id(cur, "lookup_log")`. `for_thread` → `LookupRow.model_validate(...)`
  id ascending.
- **CheckEventsRepo.** `append(event, thread_id, *, at=None)`: INSERT with `at` = `format_wall(at)` when given, else
  `(SELECT received_at FROM turns WHERE turn_id = ?)`; `claim_kinds`, `codes` as JSON arrays. `for_thread` →
  `CheckEvent.model_validate` (column `check_kind` → field `check`).
- **EventsRepo.** `append`: INSERT `(str(stream), event.type, _j(event.payload), format_wall(event.at))` →
  `last_row_id(cur, "events")` (`EventId` is an alias of `int`, not a constructor). `after`: `WHERE stream=? AND id>? ORDER BY id`. `latest_of`: `SELECT MAX(id) … WHERE stream=?
  AND type=?` → `EventId` or `None`. `latest_id`: same without type, `0` when none.
- **ReadsRepo.** `invoice` / `customer`: SELECT the issued row; parse dates and `line_items` (JSON; a non-JSON value →
  `StorageError("invoices", "line_items not JSON")`). `appointment`: `appointments a JOIN appointment_slots s USING
  (slot_id) JOIN technicians t ON t.tech_id = s.tech_id`; never select `issue_description`. `identity_state(thread_id)`
  (graph-tools §5): status/customer_id/masked_hint/verified_at from `identity_threads` (no row → `not_checked`, `None`s);
  `codes_sent = COUNT(*)` of the thread's `identity_codes`; `code_expires_at`, `tries_left` from the newest code row
  (`ORDER BY id DESC LIMIT 1`; no row → `None`, `3`) → `IdentityState.model_validate(...)`. `new_flags_count`:
  `COUNT(*) FROM flags WHERE status='new'`.
- **CasesReadRepo.owner** → `CaseOwnerRow` from `cases`.
- **CoreRepos.settled_for(thread_id, read_at)** (graph-core §6; the one builder of `Settled`):
  1. `actions = self.actions.for_thread(thread_id)`.
  2. `case = SELECT … FROM cases WHERE thread_id=? AND lifecycle NOT IN ('resolved','closed_unresolved') ORDER BY
     created_at DESC, case_ref DESC LIMIT 1`.
  3. If a case: its current promise row (`SELECT … FROM promises WHERE case_ref=? ORDER BY id DESC LIMIT 1`; none →
     `StorageError("promises", "no promise for open case")`) and its `followups` row (or `None`). Build
     `open_case = OpenCase.model_validate({"case_ref", "reason", "priority", "state": lifecycle, "promise": {
     "policy_row", "text", "due_at", "due_label", "extra_lines", "live_queued"}, "followup": {"channel",
     "destination_label", "on_record", "window", "saved_line"} | None, "live_queued": lifecycle == "live_queued"})`.
  4. `return Settled(actions=actions, open_case=open_case, read_at=read_at)`.
  - Invariant: `Settled` comes only from `actions` + `cases`/`promises`/`followups` rows (DO-4 §1); `read_at` is the
    caller's reading, never a clock read here.

### Step 7 — `ResetRepo.clear_demo_tables(reset_id, *, ended_at=None)` (AC-6, CAS-1, CAS-3, CAS-32, staff.md §4)

Runs inside the caller's (exclusive) transaction; reads before it deletes:

1. `open_threads = SELECT thread_id FROM conversations WHERE live_state <> 'closed' ORDER BY started_at, thread_id`.
2. `case_streams = SELECT DISTINCT substr(stream, 6) FROM events WHERE stream LIKE 'case:%' ORDER BY 1` (read **before**
   the events go; `case:` is 5 characters).
3. Tombstones for **every** conversation (open or not, so every cleared thread answers 410 `SESSION_ENDED`, not 404):
   `INSERT INTO ended_threads (thread_id, demo_session, ended_wall_at, reason, reset_id) SELECT thread_id, demo_session,
   ?, 'demo_reset', ? FROM conversations`, with `format_wall(ended_at or datetime.now(timezone.utc))`.
4. `roles_reset = UPDATE staff_sessions SET role='customer', role_reset_pending=1 WHERE role <> 'customer'` →
   `rowcount`. No staff row is deleted.
5. For each table in `CLEARED_TABLES` (that order: children before parents): `n = SELECT COUNT(*)`, then `DELETE FROM
   <table>`; `rows_cleared[table] = n`. `DELETE` keeps `sqlite_sequence`, so no id is reused.
6. Return `Cleared.model_validate({"open_threads": …, "case_streams": …, "roles_reset": …, "rows_cleared": …})` from the
   plain strings read (this validates every id). Touches no issued, kept or `demo_state` row
   (`demo_state.reset()` is AEA-31's separate call).

### Step 8 — `repos_cases.py` (AC-18, PA-5)

Same conventions as step 6. Notes per class:
- `CasesRepo.insert`: every `CaseRow` field (`trigger` → `handoff_trigger`; `change_request` → JSON). `get_for_thread_open`
  and `list_open` exclude `CLOSED_LIFECYCLES`. `update_versioned` as §4.3, values converted (datetime → `format_wall`,
  enum → `.value`, bool → 0/1, `None` → NULL).
- `CaseEventsRepo.append`: `key` → `event_key`, `detail` → `detail_json`; a duplicate non-empty key raises
  `StorageError("case_events", "UNIQUE")` (scheduler idempotency also checked by `exists`).
- `PromisesRepo.insert(case_ref, promise, at)`: store `policy_row, text, due_at, due_label, extra_lines (JSON),
  live_queued` from the `Promise`, `status='open'`, `created_at=at`. `current`, `history`, `set_status`,
  `list_open_past` as §4.3; "current" = `id = (SELECT MAX(id) FROM promises p2 WHERE p2.case_ref = promises.case_ref)`.
  Rows rebuild `Promise` with `Promise.model_validate({...})`. The text is stored and returned word for word (M-10).
- `FollowupsRepo.upsert`: `INSERT … ON CONFLICT(case_ref) DO UPDATE SET …` (`window` → `contact_window`).
- `BriefsRepo.upsert(brief, at)`: `INSERT … ON CONFLICT(case_ref) DO UPDATE` with `thread_id = brief.thread_id`,
  `status = brief.status`, `brief_json = brief.model_dump_json()`; `get` → `Brief.model_validate_json`.
- `DemoStateRepo` as §4.3 (upsert `ON CONFLICT(id) DO UPDATE`); `get()` with no row returns `DEMO_START` /
  `nobody_online` without writing.
- `JobRunsRepo.finish`: UPDATE `finished_wall_at`, `status`, `counts_json`, `error_kind`; no row →
  `StorageError("job_runs", "no row")`.
- `RecordsRepo`, `RefsRepo` as §4.3. `next_case_ref`: `SELECT MAX(CAST(substr(case_ref, 7) AS INTEGER)) FROM cases`
  (`MHC-C-` is 6 characters) → `n = max(value or 0, SEED_REF_MAX) + 1` → `_CASE_REF.validate_python(f"MHC-C-{n:04d}")` (module-level `_CASE_REF =
  TypeAdapter(CaseRef)`; §4.1).
- Re-export the case row models and `DEMO_START` from `repos_cases.py`.

### Step 9 — the `register_storage` hunk in `web/container.py` (PA-6, WF-16)

AEA-01's stub (on `main`): `def register_storage(container: Container, app: FastAPI, *, settings: Any, limits: Limits) ->
None:` with a two-paragraph docstring, "AEA-10 storage: SQLite unit of work, migrations and first boot, checkpointer
(cases.md §1)." then "No-op until AEA-10 fills it.". `build_container` calls it **first**. Keep the signature. Replace the docstring and
body with exactly this (names fixed; the sibling plans AEA-23/26/29/30/31 already read these keys):

```python
def register_storage(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-10 storage: SQLite unit of work, migrations and first boot, checkpointer (cases.md §1).

    Provides Key("uow_factory") (SqliteUnitOfWorkFactory; building it migrates the working copy, WF-16),
    Key("checkpointer") (Checkpointer over checkpoints.sqlite, closed with the container) and
    Key("restore_working_copy") (restore_working_copy bound to settings.issued_db_path; cases.md §1.4).
    """
    import functools
    from pathlib import Path

    from meridian.adapters.checkpointer import CHECKPOINTS_DB_NAME, Checkpointer
    from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
    from meridian.adapters.sqlite.migrate import WORKING_DB_NAME, migrate, restore_working_copy

    data_dir = Path(settings.data_dir)
    issued_path = Path(settings.issued_db_path)
    db_path = data_dir / WORKING_DB_NAME

    def make_uow_factory(_c: Container) -> SqliteUnitOfWorkFactory:
        migrate(db_path, issued_path=issued_path)          # first boot copies the issued file; DDL every boot
        return SqliteUnitOfWorkFactory(db_path)

    def make_checkpointer(c: Container) -> Checkpointer:
        checkpointer = Checkpointer(data_dir / CHECKPOINTS_DB_NAME)
        c.on_close(checkpointer.close)
        return checkpointer

    container.provide(Key[SqliteUnitOfWorkFactory]("uow_factory"), make_uow_factory)
    container.provide(Key[Checkpointer]("checkpointer"), make_checkpointer)
    container.provide(
        Key[Callable[..., None]]("restore_working_copy"),
        lambda _c: functools.partial(restore_working_copy, issued_path=issued_path),
    )
```

Notes the implementer must keep:
1. The docstring keeps the token `AEA-10` (AEA-01's test checks it) and **loses** "No-op until AEA-10 fills it." (the
   R-13 edit skips hunks without that phrase).
2. No import is added at module level (`Callable`, `Container`, `Key`, `Any`, `Limits`, `FastAPI` are already there).
3. Nothing does I/O in the hunk body itself; `migrate` runs when `build()` resolves `uow_factory`, which is the first
   provider because this hunk runs first. A failed build closes what was opened (AEA-01's `build_container`).
4. `settings` is typed `Any` (AEA-01 §8 note 4); only `data_dir` and `issued_db_path` are read (AEA-02 `Settings`
   fields, defaults `var` and the issued path).
5. `app` and `limits` are unused; leave them (the signature is AEA-01's).

### Step 10 — `checkpointer.py` (AC-19)

1. `__init__(path, *, busy_timeout_ms)`: `path.parent.mkdir(parents=True, exist_ok=True)`; `self._conn =
   sqlite3.connect(str(path), check_same_thread=False, timeout=busy_timeout_ms / 1000)`; `PRAGMA journal_mode=WAL`;
   `PRAGMA busy_timeout=<ms>`; `self._saver = SqliteSaver(self._conn)`; `self._saver.setup()` (tables exist before
   any prune/clear).
2. `_own()` (private): a second connection to the same file with `isolation_level=None`, `timeout`, `busy_timeout`.
3. `prune(keep=2)`: `keep < 1` → `ValueError`. On `_own()`: `BEGIN IMMEDIATE`;
   `DELETE FROM checkpoints WHERE rowid IN (SELECT rowid FROM (SELECT rowid, ROW_NUMBER() OVER (PARTITION BY thread_id,
   checkpoint_ns ORDER BY checkpoint_id DESC) AS rn FROM checkpoints) WHERE rn > ?)` → `removed = rowcount`; then
   `DELETE FROM writes WHERE NOT EXISTS (SELECT 1 FROM checkpoints c WHERE c.thread_id = writes.thread_id AND
   c.checkpoint_ns = writes.checkpoint_ns AND c.checkpoint_id = writes.checkpoint_id)`; `COMMIT`; return `removed`
   (rollback + re-raise on error; always close). LangGraph checkpoint ids are time-ordered (uuid6), so `DESC` keeps the
   newest. Verify the table and column names against the installed `langgraph-checkpoint-sqlite` (`PRAGMA table_info`)
   and adjust only the names if they differ.
4. `clearing()` (context manager): `c = _own()`; `BEGIN IMMEDIATE`; for each `name` in `SELECT name FROM sqlite_master
   WHERE type='table' AND name NOT LIKE 'sqlite_%'`: `DELETE FROM "<name>"`; `yield`; clean exit → `COMMIT`; exception
   → `ROLLBACK` and re-raise; `finally c.close()`. (CAS-2: entered inside the meridian transaction by AEA-31; meridian
   commits first.)
5. `clear()`: `with self.clearing(): pass`. `close()`: close `self._conn`.

### Step 11 — `tests/fixtures/sqlite.py` (AC-22)

`temp_sqlite()`: `data_dir = Path(tempfile.mkdtemp(prefix="meridian-test-"))`; `db_path = data_dir / WORKING_DB_NAME`;
`migrate(db_path, issued_path=issued_path)`; `yield TempStore(data_dir, db_path, issued_path,
SqliteUnitOfWorkFactory(db_path))`; `finally: shutil.rmtree(data_dir, ignore_errors=True)`. No pytest import needed;
test modules wrap it in their own fixture:

```python
@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s
```
Import path: `from tests.fixtures.sqlite import TempStore, temp_sqlite` (`tests/__init__.py` and
`tests/fixtures/__init__.py` exist, AEA-01; `pythonpath = ["."]` in `pyproject.toml`).

### Step 12 — tests (§7), written alongside steps 1–11

Write each test right after the step it proves; run the affected test file each time.

### Step 13 — journey record (AC-24)

Create `docs/testing/journeys/<YYYY-MM-DD>-AEA-10.md` (date of the run) with the §4 fields of
`integrated-journeys.md`: Claim "storage for J-1…J-10 (every journey reads and writes the working copy)"; Level
`mock-tested`; Tested revision (commit SHA); Environment (local, `temp_sqlite()`, no server, no model); Command (the unit
test command and the affected-journey command); Result (unit/contract tests pass; "0 journeys affected"); Evidence
location (the test output in the implementer's report); Remaining limitations (no journey yet; the real entry points are
CAP-1…3 AEA-51, CAP-5 AEA-52, CAP-9 AEA-50); **Blocked by: AEA-57** (and AEA-51, 52, 53 for the journeys that will run
this code). Run AEA-01's affected-journey command on the diff: `uv run python -m tests.journeys.affected --base main`. Expected:
`changed files: N (base main)`, then `0 journeys affected`, exit 0 (no `tests/journeys/j<N>/test_*.py` exists before
AEA-57). Copy the layout of `docs/testing/journeys/2026-10-21-AEA-01.md` (a two-column `Field | Value` table: Claim,
Level, Tested revision, Environment, Command, Result, Evidence location, Remaining limitations, Blocked by) and add a row
*Journeys that will exercise this code*: J-1…J-10.

### Step 14 — context docs (AC-25), in a second commit after the code commit

The SHA these edits cite is the **code commit's** (step 15, commit 1), the way AEA-01 did it (`893b825` code, `90757d3`
context).

- `.claude/reference/area-map.md`, the row that starts `| 0 | **A0 Foundation** |`, only:
  - paths cell: `adapters/sqlite/{db,migrate,repos_core,repos_cases}.py` → `adapters/sqlite/{db,migrate,rows,repos_core,repos_cases}.py`;
  - status cell (it starts `partly built:`): just before its closing `; the rest planned`, insert
    `; AEA-10 (`<code sha>`): `adapters/sqlite/{db,migrate,rows,repos_core,repos_cases}.py`, every
    `adapters/sqlite/schema/*.sql` (AEA-10 writes all DDL and owns `repos_cases.py`, slice plan §0 deviation 1),
    `adapters/checkpointer.py`, `tests/fixtures/sqlite.py` actual`. Nothing else in the file.
- `.claude/state/icm-progress.md`: two rows are named *Routes verified against code and tests* (a merge kept both). Edit
  only the **first** one (its evidence starts `2026-10-21: first backend slice AEA-04`): replace its evidence cell with
  `2026-10-21: A0 storage AEA-10 (`<code sha>`): `tests/unit/adapters/sqlite/`, `tests/unit/adapters/test_checkpointer.py`,
  `tests/unit/web/test_register_storage.py` pass (<N> passed)`. Keep status `provisional` and the last cell; the row stays
  ≤ 400 characters. Leave the second row alone.
- `docs/design/code-design.md` §3: directly under the line `**Built:** `policy/texts.py` (AEA-03, `2689582`).` add one line:
  `**Built:** `adapters/sqlite/{db,migrate,rows,repos_core,repos_cases}.py`, every `adapters/sqlite/schema/*.sql`,
  `adapters/checkpointer.py`, `tests/fixtures/sqlite.py` (AEA-10, `<code sha>`).` No other edit.

### Step 15 — gates and commits

Run §7.2's final gates, cheapest first. Then make two commits on the branch the orchestrator gave, with `git add <path>`
for each path (never `-A`):

1. **Code:** every owned file under `src/` and `tests/` in §2. Message `feat(storage): SQLite core, case tables,
   migrations, checkpointer (AEA-10)`; the body lists AC-1…AC-23 and PA-1…PA-8 with their tests; last line
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
2. **Context:** `docs/testing/journeys/<date>-AEA-10.md`, `.claude/reference/area-map.md`, `.claude/state/icm-progress.md`,
   `docs/design/code-design.md` (steps 13–14, citing commit 1's SHA). Message `docs(context): AEA-10 storage built paths
   and journey record`; same last line.

Do not push (only the merge step pushes `main`); nobody force-pushes.

---

## 6. Data and fixtures

All data is the **issued** scheduling DB (read-only, copied per test by `temp_sqlite()`) plus synthetic values built in
the test. No real personal data, no codes, no card-like numbers, no full phone numbers in test names or literals.

| Fixture | Source | Used by |
|---|---|---|
| Issued DB copy | `docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite` via `temp_sqlite()` | every test |
| WP-4F (AC-13) | Issued rows: Linda Foster `MHC-10001`, appointment **159** on slot **159** (`2026-10-22`, `08:00-12:00`, tech 5 Marta Kowalski); new slot **56** (`2026-10-19`, `08:00-12:00`, tech 5). Thread id `uuid4()`; turn 3 and turn 4 ids `uuid4()`. Action: `kind=moved`, key `(thread, turn3, moved, "159")`, `records={"appointment": "159", "slot": "56", "old_slot": "159"}`, `before={"date": "2026-10-22", "window": "08:00-12:00", "technician": "Marta Kowalski"}`, `after={"date": "2026-10-19", "window": "08:00-12:00", "technician": "Marta Kowalski", "service_type": "hvac_repair", "fee_line": "Diagnostic fee: waived for members"}` (synthetic sentence; the real text is AEA-13's), `at = DEMO_START`. Read at turn 4 with `read_at = DEMO_START + timedelta(minutes=2)` | `test_settled_for_returns_earlier_turn_move` |
| Open case for AC-13 | Synthetic `CaseRow(case_ref="MHC-C-0009", thread_id=<thread>, reason=HandoffReason.FEE_BEARING_CHANGE, priority=Priority.P2, rule_id="D4.fee_bearing", trigger="escalation", lifecycle="unassigned", due_at=<window start>, created_at=updated_at=DEMO_START)` and a promise built in the test with `Promise(policy_row="R26.unstaffed", text=<any fixed test sentence>, due_at=<Mon 2026-10-19 19:00 Chicago>, due_label=None)` (tests may construct `Promise`, graph-core §10) | AC-13, AC-18 |
| Reset example (AC-4, issue example pair 2) | In a write uow on the copy: `UPDATE appointment_slots SET status='booked' WHERE slot_id=56` and `INSERT INTO appointments (slot_id, customer_id, issue_description, created_at) VALUES (56, 'MHC-10004', 'synthetic', '2026-10-16')` (raw SQL through `tx.connection`: the booking repository is AEA-28's); a `spend_ledger` row (raw SQL) and a `reset_events` row as kept rows | AC-4, AC-5, AC-6 |
| Seeds for `next_case_ref` | Four `CaseRow`s `MHC-C-0005…0008` with `seed=True` | AC-18 |
| IDs | `str(uuid4())` for thread, turn and request ids (canonical lower-case uuid4, as the pattern needs). Pass them as plain strings inside `model_validate` dicts; where a repository argument is typed `ThreadId` / `TurnId`, build it with `TypeAdapter(ThreadId).validate_python(str(uuid4()))` | every test |
| Lookup entries | `LookupEntry.model_validate({"tool": "kb_search", "record_ids": [], "passage_ids": ["kb/sample.md#1"], "result_seen": "synthetic", "message_id": <id>, "turn_id": <uuid4 str>})` (a `PassageId` matches `^[^#\s]+#[0-9]+$`) | AC-16 |
| Sentinels | `"sentinel-" + uuid4().hex` built at run time (never a literal) | AC-3, AC-20 |
| Checkpoints | `empty_checkpoint()` put 5 times on thread `"t-prune"` via `saver.put(cfg, cp, {"source": "loop", "step": i, "parents": {}}, {})`, `cfg = {"configurable": {"thread_id": ..., "checkpoint_ns": ""}}`, reusing the returned config each time. If the installed API differs, compile a one-node `StateGraph` with the saver and `invoke` it until the thread has 5 checkpoints | AC-19 |
| Staff rows for AC-6 | Raw INSERTs into `staff_sessions` (roles customer, representative, supervisor) and `flags` (one `new` row) with synthetic hashes `uuid4().hex` | AC-6, AC-17 |

---

## 7. Checks

### 7.1 Tests the implementer writes (with the code)

Paths follow DO-3 §9 (`tests/unit/` mirrors `src/meridian/`). Every DB test uses its own `temp_sqlite()` copy.

**`tests/unit/adapters/sqlite/test_uow.py`**
- `test_pragmas_commit_and_rollback` (AC-8): read `PRAGMA journal_mode` (`wal`), `busy_timeout` (`5000`), `foreign_keys`
  (`1`) inside a uow; insert a conversation without `commit()` → 0 rows after; insert then `raise RuntimeError` inside
  the block → `pytest.raises(RuntimeError)` and 0 rows; a `write=False` uow insert raises `sqlite3.OperationalError`;
  `commit()` twice is a no-op; a committed row is visible from a new uow.
- `test_lock_timeout_writes_nothing` (AC-9): factory A (default) holds `exclusive=True`; factory B built with
  `busy_timeout_ms=200` enters `write=True` → `pytest.raises(sqlite3.OperationalError)`; a flag set inside B's block stays
  `False` (the block never ran); counts of `conversations` and `events` equal before/after; elapsed ≥ 0.15 s.
- `test_seven_repos_and_port_imports_no_adapter` (AC-10): `isinstance` of all seven attributes against the declared
  classes; for each attribute exposing `_conn`, it `is uow.connection`; a `subprocess.run([sys.executable, "-c",
  "import sys, meridian.ports.runtime; print(sorted(m for m in sys.modules if m.startswith('meridian.adapters')))"])`
  prints `[]`; and `factory: UnitOfWorkFactory = SqliteUnitOfWorkFactory(path)` in the test body type-checks (mypy
  proves the Protocol match).
- `test_wall_time_formatter` (AC-11): `format_wall(datetime(2026,10,16,10,0,tzinfo=ZoneInfo("America/Chicago"))) ==
  "2026-10-16T15:00:00+00:00"`; `parse_wall(...)` equals the input and is tz-aware; a naive datetime →
  `pytest.raises(ValueError)`; plan-added: lexicographic order of formatted values equals time order across a
  microsecond case.

**`tests/unit/adapters/sqlite/test_migrate.py`**
- `test_first_boot_copies_issued_db_and_applies_schema` (AC-1): `migrate(tmp/"meridian.sqlite", issued_path=ISSUED_DB)`
  returns `True`; `sqlite_master` tables ⊇ `ISSUED_TABLES + CLEARED_TABLES + UPDATED_TABLES + KEPT_TABLES`; counts
  customers 154, technicians 8, appointment_slots 528, appointments 159, invoices 81; `schema_files()` names in the order
  `00, 20, 40, 50, 60, 90, 95`.
- `test_existing_working_copy_survives_restart` (AC-2): write a conversation, an action and a case (+ promise), commit;
  `migrate(...)` again returns `False`; read all three back equal.
- `test_issued_file_never_written` (AC-3): SHA-256 of `ISSUED_DB` before; first boot; a uow write of a conversation whose
  `demo_session` is a run-time sentinel (commit); `restore_working_copy(tx, issued_path=ISSUED_DB)` in a write uow
  (commit); SHA-256 after is equal; the sentinel is found by `SELECT` in the working copy and is absent from
  `ISSUED_DB.read_bytes()`; `ISSUED_DB` has no `-wal`/`-shm`/`-journal` sibling created by the test.
- `test_restore_working_copy_restores_issued_tables` (AC-4): the reset example of §6; restore + commit; slot 56 is
  `open`; `MAX(appointment_id)` is 159; a new appointment INSERT gets id **160**; `sqlite_sequence` has no row for the
  five issued tables (or, if it has, `seq` equals the issued max); the kept `spend_ledger` and `reset_events` rows are
  still there; the five table contents equal the issued file's row for row (compare `SELECT * ORDER BY rowid`).
- `test_restore_rolls_back_with_caller` (AC-5): slot 56 booked and committed; then a write uow calls
  `restore_working_copy` and raises → slot 56 still `booked`, appointment 160 still present.
- `test_clear_demo_tables_matches_table_list` (AC-6): seed one row in every cleared table (via the repos where they exist,
  raw SQL for identity/flags/case tables as needed), two conversations (one `live_state='closed'`), case-stream events on
  `case:MHC-C-0009`, staff sessions (customer, representative, supervisor), and one row in every kept table; call
  `tx.core.reset.clear_demo_tables(reset_id, ended_at=<aware dt>)`; commit; assert: every `CLEARED_TABLES` table has 0
  rows; `ended_threads` has a row for **each** conversation with `reason='demo_reset'` and the `reset_id`; both staff
  rows now `customer` with `role_reset_pending=1`, 3 rows still present; every `KEPT_TABLES` row count unchanged;
  `cleared.open_threads` = the non-closed thread; `cleared.case_streams == ("MHC-C-0009",)`; `cleared.roles_reset == 2`;
  `cleared.rows_cleared[t]` equals the seeded count for each table; `demo_state` untouched.

**`tests/unit/adapters/sqlite/test_repos_core.py`**
- `test_ids_not_reused_and_tombstone_lookup` (AC-7): append 3 events; clear; append → id > every earlier id;
  `lookup(cleared_thread)` is `EndedThread` with `reason == "demo_reset"` and the `reset_id`; `lookup(str(uuid4()))` and
  `lookup("not-a-uuid")` are `None`; `lookup(live_thread)` is a `ConversationRow` before the clear.
- `test_action_record_idempotent_on_key` (AC-12): `record(a)` twice → one `actions` row; second return equals the first.
- `test_settled_for_returns_earlier_turn_move` (AC-13, **WP-4F worked pair**): §6 fixture; `for_thread` holds the
  turn-3 `moved` action with its `before`/`after`; `settled_for(thread, read_at)` has the same action, `open_case`
  `MHC-C-0009` with the promise text and both dues (case `due_at` on the case row, promise `due_at` on `open_case.promise`),
  and `read_at` equal to the argument; a retried turn-3 `record` with the same key writes nothing new (issue example).
- `test_turn_begin_finish_and_timeouts` (AC-14, PA-7): first `begin` → `new` (row `running`, `sequence` 1); second →
  `running`; `finish(completed TurnRecord with a PlannerTrace)` → `begin` → `completed` with the stored `response`;
  `get(turn).as_record() == record`; another turn finished `failed` with `degrade_reason="timeout"` → `begin` → `failed`
  and the row is `running` again; `timeouts_for(thread) == 1`; a `begin` with the same `turn_id` but another
  `thread_id` → `running`, `response is None`, nothing written.
- `test_events_after_and_latest_of` (AC-15, PA-8): streams `case_stream("MHC-C-0009")` and `thread_stream(<thread>)`
  (assert `case_stream(ref) == "case:MHC-C-0009"` and `thread_stream(t) == t`); ids strictly increasing;
  `after(case_stream, first_id)` returns only later case events in order; `latest_of(case_stream, "demo_reset")` is the
  newest `demo_reset` id; `latest_of(case_stream, "nope")` is `None`; `latest_id(empty_stream) == 0`.
- `test_lookup_log_and_handoff_anchor` (AC-16): greeting (assistant) then two customer messages; `append(LookupEntry
  (message_id=<2nd customer>))` stores that message's `thread_id`; `for_thread` returns `LookupRow`s id ascending;
  `append` naming message id 999999 → `StorageError` with `table == "lookup_log"`; `handoff_anchor` = newest customer
  message; a thread with only the greeting → the greeting id.
- `test_cross_ticket_reads` (AC-17): `UPDATE invoices SET amount_cents = amount_cents + 100 WHERE invoice_id =
  'INV-204411'` (raw, committed) → `reads.invoice("INV-204411").amount_cents == 47900`; `reads.appointment(159)` has slot
  159, `technician == "Marta Kowalski"`, no `issue_description` field; `reads.customer("MHC-10001").membership_tier ==
  "standard"`; `identity_state` for a thread with no rows → `not_checked`, `tries_left 3`, `codes_sent 0`; with an
  `identity_threads` row `verified` + two `identity_codes` rows (synthetic HMAC strings) → status, `codes_sent 2`,
  newest row's `tries_left`/`expires_at`; `new_flags_count()` counts only `new` flags.
- `test_storage_error_hides_value` (AC-20): `record(a)` with `key.record_id = sentinel`; `record(a2)` same key, different
  `after` → `pytest.raises(StorageError)`; `str(exc)` and `repr(exc)` contain `actions` and `UNIQUE` and not the
  sentinel; `caplog.text` (level DEBUG) does not contain the sentinel; `exc.__context__ is None` and `exc.__cause__ is
  None`.
- `test_fail_running_sweeps_every_running_row` (AC-23): two `running` rows + one `completed`; `fail_running()` returns
  the two ids; both rows `failed` / `degraded` / `degraded_handoff` / `timeout`; the completed row unchanged; print the
  three rows' status, path, outcome, degrade_reason (evidence).

**`tests/unit/adapters/sqlite/test_repos_core_rows.py`** (plan-added)
- `test_conversation_writes` (PA-2): insert, each setter, `open_thread_ids`, `idle_live` (29 vs 30 minutes cutoff,
  `eval`/`seed` threads excluded), `last_started_wall`; a setter on an unknown thread → `StorageError`.
- `test_messages_recent_window` (PA-3): greeting + 12 turns (customer + assistant line each, one representative line
  with `turn_id=None` after turn 6) → `recent(thread, 10)` starts at turn 3's first message and includes the
  representative line; `recent(thread, 20)` returns every message incl. the greeting.
- `test_check_events_append_round_trip` (PA-4): append a `CheckEvent` with `codes` and `claim_kinds` → `for_thread`
  equals it; `at` equals the turn's `received_at`.

**`tests/unit/adapters/sqlite/test_repos_cases.py`** (AC-18, PA-5)
- `test_case_round_trip_keeps_both_dues` · `test_case_events_append_and_exists` · `test_promise_text_history_and_list_open_past`
  (word-for-word text; `set_status` on current only; history after a `changed` + new insert; `list_open_past(now)`)
  · `test_followups_and_activities` · `test_briefs_upsert_replaces` (two upserts → one row, the second brief) ·
  `test_demo_state_defaults_and_reset` (fresh → `DEMO_START`, `nobody_online`; `set_now`/`set_staffing`; `reset()` →
  defaults) · `test_demo_events_and_job_runs_latest` · `test_reset_and_seed_records` (incl. `seed_rows_present`,
  `set_checkpoints_cleared`, `latest_*`, `label == "demo seed"`) · `test_next_case_ref_after_seeds` (empty → 0009; with
  0005…0008 → 0009; with 0009 → 0010) · `test_update_versioned_conflict` (PA-5: match → new version 2; stale → `None`
  and no change; unknown key → `ValueError`).

**`tests/unit/adapters/sqlite/test_schema.py`**
- `test_do6_fields_present` (AC-21): `PRAGMA table_info` per table ⊇ a dict of expected columns: `turns` (turn_id,
  thread_id, request_id, run_tag, run_id, agent_version, sequence, received_at, status, gate_result, path, outcome,
  degrade_reason, planner_model, planner_fallback_used, planner_failure, plan_mode, plan_source, plan_intents,
  plan_handoff_request, plan_topic, planner_failed, danger_raised, specialists_run, replied_at, server_ms, model_calls,
  input_tokens, output_tokens, cost_usd, tool_calls, trace_id, trace_export, response); `conversations` (thread_id,
  run_tag, run_id, agent_version, outcome, started_at, started_wall_at, ended_wall_at, staffing_at_start,
  last_customer_wall_at, live_state); `check_events` (`CheckEvent.model_fields` with `check`→`check_kind`, plus
  thread_id, at); `lookup_log` (`LookupRow.model_fields` + thread_id); `cases` (case_ref, thread_id, turn_id, due_at,
  seed, priority, lifecycle); `promises` (case_ref, text, due_at, status, policy_row); `case_events` (case_ref, kind,
  actor_role, job_run_id); `job_runs.job_run_id`; `demo_events.demo_event_id`; `reset_events` (reset_id, asked_by_role,
  asked_by_session, checkpoints_cleared); `seed_events` (reset_id, deploy_id, seed_count, label with default
  `'demo seed'`); `spend_ledger`, `identity_*`, `staff_sessions`, `flags` exactly the addenda columns. Print each
  table's column list (evidence).
- `test_temp_sqlite_applies_all_schema` (AC-22): inside the context every expected table exists; after it,
  `data_dir.exists()` is `False`.
- `test_every_table_has_one_reset_effect` (PA-1): the set of `sqlite_master` tables (excluding `sqlite_%`) equals the
  disjoint union of the four constants.
- `test_no_kept_table_references_cleared_table` (PA-1): for every kept/updated table, `PRAGMA foreign_key_list` targets
  are not in `CLEARED_TABLES`.

**`tests/unit/adapters/test_checkpointer.py`** (AC-19)
- `test_uses_own_file` (saver tables exist in `checkpoints.sqlite` and not in `meridian.sqlite` of the same data dir) ·
  `test_prune_keeps_last_two` (5 → 2, returns 3; the two kept are the newest; another thread untouched) ·
  `test_clear_empties` · `test_clearing_rolls_back_on_raise_and_commits_on_clean_exit`.

**`tests/unit/web/test_register_storage.py`** (PA-6)
- `test_register_storage_migrates_and_exposes_factory(tmp_path)`: `settings = SimpleNamespace(data_dir=tmp_path / "data",
  issued_db_path=ISSUED_DB)`; `c = Container(settings=settings, limits=Limits())`; `register_storage(c, FastAPI(),
  settings=settings, limits=c.limits)` returns `None`; `c.build()`; `uow = c.get(Key[Any]("uow_factory"))` is a
  `SqliteUnitOfWorkFactory`; `tmp_path/"data"/"meridian.sqlite"` exists with the five issued counts; `with uow() as tx:
  tx.core.reads.customer("MHC-10001")` is not `None`; `cp = c.get(Key[Any]("checkpointer"))` has `cp.path ==
  tmp_path/"data"/"checkpoints.sqlite"`; `restore = c.get(Key[Any]("restore_working_copy"))`; in `with uow(write=True)
  as tx:` call `restore(tx)` then `tx.commit()` (no error); `c.close()` → `cp.closed is True`; the docstring of
  `register_storage` contains `AEA-10` and not `No-op until`.

**`tests/unit/web/test_container.py`** (AEA-01's file; §8 R-13): if the guard is not already on `main`, insert as the
first two lines inside `for name, func in originals.items():`

```python
        if "No-op until" not in (func.__doc__ or ""):
            continue  # filled by its ticket, whose own test covers the hunk
```
Nothing else in that file changes.

**`tests/unit/adapters/test_repo_shells.py`** (AEA-02's file; §8 R-2): if not already scoped on `main`, put the
public-name assertion `[n for n in vars(cls) if not n.startswith("_")] == []` under
`if "AEA-02 creates the constructor only" in (cls.__doc__ or ""):`. Keep the constructor-hints and `"__init__" in
vars(cls)` assertions for all seven. AEA-10's `CoreRepos` and `CaseRepos` docstrings drop that phrase (e.g. "Repositories
for 00_core and the cross-ticket reads; body AEA-10 (cases.md §1.2).").

### 7.2 Commands

Run from `/home/linuxuser/workspaces/inno-aea-callcenter` (or the worktree the orchestrator gives) with
`export UV_LINK_MODE=hardlink`. Never copy a venv; no `node_modules`; pytest `-n 2` at most.

While iterating (affected tests only):

```bash
uv run pytest -q tests/unit/adapters/sqlite/test_uow.py                       # one file at a time
uv run --with pytest-xdist pytest -n 2 -q tests/unit/adapters tests/unit/web   # the whole slice
grep -rlE "adapters\.sqlite|adapters\.checkpointer|fixtures\.sqlite|web\.container" tests eval   # other importers
```

Once before the final commit, cheapest first, stop at the first red:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy                                       # strict; files = src/meridian, tests, eval (pyproject.toml)
uv run --with pytest-xdist pytest -n 2 -q -rP tests/unit/adapters tests/unit/web tests/unit/ports \
    tests/unit/test_import_direction.py tests/unit/test_skeleton.py \
    $(grep -rlE "adapters\.sqlite|adapters\.checkpointer|fixtures\.sqlite|web\.container" tests eval | tr '\n' ' ')
uv run python -m tests.journeys.affected --base main   # expected: "0 journeys affected", exit 0
```

**Existing tests that must stay green:** `tests/unit/web/test_container.py` (all of it, with the R-13 guard);
`tests/unit/test_import_direction.py`, above all `test_container_imports_only_policy_limits` (no module-level import added
to `container.py`); `tests/unit/test_skeleton.py`; AEA-02's `tests/unit/adapters/test_repo_shells.py` (with the R-2 guard)
and its `tests/unit/ports/` tests.

**Passing looks like:** ruff clean; format clean; type check clean; every test above passes; the direction scans pass;
the journey command prints `0 journeys affected`. The implementer's report pastes these outputs plus the AC-23 printed
rows and the AC-21 column lists.

**Full suite:** not the implementer's job. It is required at this ticket's **merge**, because `repos_core.py` is a module
imported across the codebase (DO-3 §9; `build-loop-test-scope.md` "a module imported across the codebase"). At wave 1 the
suite is small: `uv run --with pytest-xdist pytest -n 2`.

**Journeys:** none exist before AEA-57 (AEA addition: "until AEA-57 lands the harness, there is no journey gate to run");
AC-24's record says so.

---

## 8. Risks and requests

- **R-1 · New file `adapters/sqlite/rows.py` (collision-map addition).** `repos_core.py` with every row model would
  pass the 600-line adapter hard cap (`code-structure.md`). The row models move to `rows.py`, owned by AEA-10 alone and
  re-exported from `repos_core` / `repos_cases`, so consumers can import `EndedThread`, `ConversationRow`, `CaseRow` etc.
  from the repository modules as cases.md implies. No other ticket edits it. **Request to the orchestrator:** add it to
  the slice plan §3 row `adapters/sqlite/{db,repos_core,repos_cases}.py` (frozen after wave 1). If `repos_core.py` still
  passes 600 lines, split its private SQL helpers into `rows.py`, not into a new module.
- **R-2 · AEA-02's shell test goes red once `CoreRepos.settled_for` exists.** AEA-02's planned
  `tests/unit/adapters/test_repo_shells.py::test_seven_shells_one_constructor` asserts `[n for n in vars(cls) if not
  n.startswith("_")] == []` for all seven shells. **Edit (one assertion, §7.1):** guard it with `if "AEA-02 creates the
  constructor only" in (cls.__doc__ or ""):`, the phrase AEA-02's shell docstrings carry; AEA-10's `CoreRepos` and
  `CaseRepos` docstrings drop it. Later body owners (AEA-26/27/28/32/44) then need no edit. **Collision with AEA-02**;
  request to the orchestrator: accept this guard, or have AEA-02 ship it. If the merged test already scopes the check,
  make no edit.
- **R-3 · `actions.record` conflict rule (refinement of DO-4 §1, needed by AC-20).** Same key + same
  `records`/`before`/`after` → returns the stored row (DO-4); same key + different content → `StorageError`. A retried
  turn that re-derives a *different* write is a bug that must be loud, not hidden. **Request to AEA-27/28/29 planners:**
  on a retried `turn_id`, read the existing `actions` row (or `settled_for`) before recomputing a write, so a retry never
  sends different `before`/`after` values under the same key.
- **R-4 · `sqlite_sequence` for the issued tables (AC-4 evidence wording).** The issued tables are not
  `AUTOINCREMENT`, so no `sqlite_sequence` row exists for them; the "same next ids" goal holds through SQLite's
  `max(rowid)+1` rule (next appointment 160, tested). The sequence UPDATE is kept for robustness and affects no row
  today. Engineering reading of CAS-1, not a product question.
- **R-5 · Wall-clock fallbacks.** `clear_demo_tables(reset_id)` and `job_runs.finish(...)` as signed have no wall time,
  but `ended_threads.ended_wall_at` and `job_runs.finished_wall_at` need one. Optional keywords `ended_at` /
  `finished_wall_at` fall back to `datetime.now(UTC)`. **Request to AEA-31:** call `clear_demo_tables(reset_id,
  ended_at=now)` with `ResetService.reset`'s `now`; **to AEA-30:** pass `finished_wall_at=wall_clock()`. That keeps the
  D-13 journey wall-clock override effective.
- **R-6 · `conversations.started_wall_at` has no writer yet.** DO-6 wants a start time and AEA-32's zero-traffic alert
  needs the wall time of the last live conversation start; `SessionService` (AEA-40, web.md §14) gets no wall clock in
  its constructor. The column is nullable and `last_started_wall()` exists. **Request to AEA-40 / AEA-32 planners:**
  either pass `get_wall_clock()` into `SessionService` and set `started_wall_at`, or let AEA-32 use another signal.
  Not a contract change here.
- **R-7 · Container shape (now known; AEA-01 merged).** Hunks provide through `Container.provide(Key[T](name),
  factory)`, release through `on_close`, and import inside their own body; `register_storage` is called first by
  `build_container`. The keys fixed here, `"uow_factory"`, `"checkpointer"` and `"restore_working_copy"`, are the ones the
  AEA-23/26/29/30/31 plans already read. Binding `web/deps.py`'s `get_uow_factory()` to `uow_factory` is AEA-23's.
- **R-8 · Types this ticket defines.** `StreamKey`, `StreamEvent`, `TurnBegin`, `EventRow` and the row models live in
  `rows.py`: no contract sketches them and AEA-02 does not define them (its plan, re-read 2026-10-21 12:08). Consumers
  (AEA-29/30/31/34/40/41/46) import them from `meridian.adapters.sqlite.rows`, or from the re-exports in `repos_core` /
  `repos_cases`. That is DO-3 §2.1's bounded storage exception (services call `tx.<repo>.<method>`, never `sqlite3`).
  If `OpenCase.model_validate` rejects the stored lifecycle or follow-up shape (AEA-02's `CaseState` or `FollowUp`
  differs from §4.1), AC-13 fails → report `blocked-on AEA-02 follow-up`; do not adapt the DDL.
- **R-9 · `StreamKey` format (decided here; engineering, not product).** Thread form = the bare thread id; case form =
  `case:<CaseRef>` (staff.md §7). Built only through `thread_stream()` / `case_stream()`. This matches the fallback the
  AEA-30 plan wrote (`StreamKey(str(thread_id))`) and the `case:` prefix `clear_demo_tables` reads; the AEA-29/31 plans
  find the helpers with `grep -rn StreamKey src/meridian`. **Request to the orchestrator:** give the two helper names to
  the AEA-29/30/31/41/46 implementers.
- **R-10 · Turn-row read for history.** `getChatThread` (AEA-40) rebuilds history from `messages`, `turns` and `events`;
  it needs assistant reply messages stored **with their `turn_id`**. **Request to AEA-40:** pass `turn_id=` on both the
  customer message and the reply message.
- **R-11 · Later readers (AEA-53 metrics, AEA-45 views).** Their aggregate queries are not derivable today; they arrive as
  small follow-ups on `repos_core`/`repos_cases` merged first (slice plan §3). The DDL above already holds every column
  they name (AC-21).
- **R-12 · Schema files in the wheel.** `migrate.py` reads `schema/*.sql` next to itself. With AEA-01's build backend
  this works in the editable install; AEA-50 (Dockerfile) must copy them (hatchling includes non-Python files under the
  package by default; check once with `uv build` only if AEA-01's config excludes them).
- **R-13 · AEA-01's stub test goes red once any hunk is filled.** `tests/unit/web/test_container.py::
  test_every_register_stub_present` calls every real `register_*` with `SimpleNamespace(name="stand-in")` settings and
  asserts `not fresh._factories`. AEA-10 fills the first hunk. **Edit (two lines, §7.1), word for word the AEA-17 plan's
  §3.5,** so whichever ticket lands first makes it and the others skip it; `register_storage`'s docstring drops "No-op
  until AEA-10 fills it." and keeps the `AEA-10` token. **Collision with AEA-01 (merged) and every hunk ticket**;
  request to the integrator: settle it once, at this merge.
- **R-14 · AEA-02 is not merged and its plan was still changing.** §4.1's homes come from AEA-02's plan as read at
  12:08. After AEA-02 merges, confirm each import with the grep in §4.1 before writing code. A type found in another
  module is imported from there (no other change); a type that is missing or has different fields is a stop and a report
  (`blocked-on AEA-02 follow-up`).
- **No contract change, no product decision.** Nothing here alters `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md` or a
  decision in `stage7-signoff.md` D-4…D-15. The additions are optional keywords, added read/write methods and columns
  derived from named consumers, listed for the reviewer in §3.

---

## 9. Readiness

**READY**, with **BLOCKED-ON AEA-02** for the start of implementation (true imports: every domain type,
`ports/runtime.py` and the seven repository shells). AEA-01 is merged (`07924f5`): `pyproject.toml` / `uv.lock` with
`langgraph-checkpoint-sqlite` 3.1.2, `tests/conftest.py`, the `register_storage` stub and the affected-journey command are
on `main`. No other sibling is imported (callers in waves 2–3 use this ticket, not the reverse). No `NEEDS-DECISION`: the
new `rows.py` (R-1) and the two test-file guards (R-2, R-13) are collision requests for the orchestrator, not product
decisions, and no signed contract or D-4…D-15 decision changes.

## Gates

None (no human, external, paid or live gate). Merge gate: lint and format, type check, affected tests, then the **full
suite** (repos_core.py is imported across the codebase); no journey gate exists before AEA-57.

## Deviations

Recorded by the implementer, 2026-10-21 (code commit `ff4b9bd`, context commit `135ad75` on `aea-10-aea-10-storage`).

1. **Three extra source files and one test helper.** `repos_core.py` (about 920 lines once formatted) and `repos_cases.py` (about 716) passed the 600-line adapter cap (`code-structure.md`), and the plan's R-1 split (row models to `rows.py`) was not enough. Added, all AEA-10-private and re-exported so consumers see the same names: `adapters/sqlite/repos_core_aux.py` (LookupLog, CheckEvents, Events, Reads, Reset, CasesRead repos), `adapters/sqlite/repos_cases_state.py` (DemoState, DemoEvents, JobRuns, Records, Refs repos; defines `DEMO_START` and `SEED_REF_MAX`, re-exported by `repos_cases`), and `turn_row`/`TURN_COLS` moved into `rows.py`. `repos_core.py` is 598 lines, `repos_cases.py` 503. Also `tests/unit/adapters/sqlite/helpers.py` (shared synthetic builders). Request to the orchestrator: add the three files to the slice plan section 3 collision row.
2. **ICM row edited.** `main` now has AEA-02's evidence in the first *Routes verified against code and tests* row (not AEA-04's); that row was replaced, the second left alone. The row is 315 characters.
3. **Area-map and code-design wording.** The A0 status cell and the DO-3 section 3 *Built* line list the extra modules of item 1. Because AEA-02's *Built* line has changed since the plan, the new `**Built:**` line sits directly under it.
4. **R-2 and R-13 guards applied as planned** (`test_repo_shells.py`, `test_container.py`); neither was on `main`.
5. **Test-lint pragmas.** `test_migrate.py` carries a file-level `# ruff: noqa: S608` (table names come from module constants); `pyproject.toml` was not touched.
6. **Test count.** The slice's affected command ran 89 tests; the full suite ran once as a check (412 passed, `-n 2`), though the plan reserves it for the merge.
