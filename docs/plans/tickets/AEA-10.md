## [AEA-10] storage: SQLite core, shared case tables, migrations, checkpointer

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

> **US-17 · Have follow-ups understood in context.** "As a homeowner mid-booking, I need 'what about Monday?' to apply to
> the visit we were just arranging, so that I don't start over every message." Acceptance includes: "a 20-turn chat keeps
> my verified identity and the open task".

This ticket gives every later ticket the one place conversation facts, cases and the working copy of the issued
scheduling database live. "What has this conversation done" has one authority: the `actions` table, read at the start of
every turn (DO-3 §1, §5.1; DO-1 §11 decision 3). The final shapes are `docs/design/contracts/stage7/cases.md` §1 (cited
below as *cases §n*), which wins over DO-4 where they differ (DO-4 §16). Concretely it builds:

- **`adapters/sqlite/db.py`** (cases §1.0, CAS-35): `connect(path, *, read_only=False)` (WAL, `busy_timeout` 5000 ms [A],
  `foreign_keys=ON`, explicit `BEGIN`, `check_same_thread=False`; `read_only` opens `file:…?mode=ro`);
  `format_wall` / `parse_wall`, the one wall-time formatter (tz-aware in, UTC ISO-8601 with `+00:00` out; a naive
  datetime → `ValueError`; merge MC-20); `SqliteUnitOfWork(conn)`, which builds all seven repositories as `Repo(conn)`
  over one connection (the shells of `repos_{spend,identity,booking,staff,ops}.py` come from AEA-02 with exactly that
  constructor), `commit()` idempotent; `SqliteUnitOfWorkFactory(db_path)(*, write=False, exclusive=False)`: a new
  connection per unit of work; `write=False` → `BEGIN DEFERRED` + `PRAGMA query_only=ON`, `write=True` → `BEGIN
  IMMEDIATE`, `exclusive=True` → `BEGIN EXCLUSIVE`; rollback on exit unless `commit()` ran; an exception always rolls
  back and propagates. The port `ports/runtime.py` imports the repository types under `TYPE_CHECKING` only (DO-4 §13, RB-1).
- **Every `schema/*.sql`** (slice plan §0 deviation 1; MC-10), applied in numeric order: `00_core.sql` (`conversations`
  with `run_tag`, `outcome`, `last_customer_wall_at`, `controller`, `live_state`, `live_since`; `ended_threads`;
  `messages`; `turns` holding the `TurnIds` fields, `received_at` and every `TurnRecord` / `TurnTrace` field of
  stage7/graph-core.md §2 (GRC-21) plus `response`; `actions`; `lookup_log` with `message_id NOT NULL REFERENCES
  messages(id)` (CAS-38); `check_events` = every `CheckEvent` field of stage7/graph-nodes.md §1 plus `thread_id`, `at`;
  `events` with `id INTEGER PRIMARY KEY AUTOINCREMENT` (CAS-1)); `20_spend.sql` exactly as stage7/models.md §6;
  `40_identity.sql` exactly as stage7/graph-tools.md §5 (`identity_threads`, `identity_codes`, `demo_inbox`; C-4);
  `50_booking.sql` for whatever cases §4.1 needs over the issued booking tables (it lists no new column); `60_cases.sql`
  (`cases` with the case `due_at`, `seed`; `promises` with the customer `due_at` and `status`; `followups`;
  `activities`; the brief rows; `demo_state` (one row); `demo_events` (CAS-5); `job_runs`; `reset_events` incl.
  `asked_by_role`, `asked_by_session`, `checkpoints_cleared`; `seed_events`); `90_staff.sql` exactly as stage7/staff.md §3
  (`staff_sessions` with `role_reset_pending`, `flags.id` AUTOINCREMENT; MC-11); `95_ops.sql` (`health_events`,
  `deploy_records`, `eval_runs`, `eval_case_results` with data.md §6's fields; CAS-27). Column lists: cases §1.1. No
  table a reset keeps carries a foreign key to a table a reset clears; no `ingest_runs` and no experiments table (DAT-12).
- **`adapters/sqlite/migrate.py`**: first boot copies the issued `docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite`
  to the working copy when it is missing, then applies the schema (DO-1 §9). `restore_working_copy(tx: UnitOfWork) ->
  None` (cases §1.4, CAS-1) replaces DO-4's `Callable[[], None]`: it reads the issued file through a separate read-only
  connection (`mode=ro&immutable=1`) and, inside the caller's transaction, deletes and re-inserts the five issued tables
  and sets their `sqlite_sequence` rows to the issued maximum. Only first boot copies the file.
- **`repos_core.py`**: DO-4 §13's methods (`actions.record` idempotent on `ActionKey`, `actions.for_thread`,
  `lookup_log.append`, `events.append` / `events.after`, `turns.begin` / `turns.finish`) plus every method of cases §1.2:
  `conversations.lookup` (→ `ConversationRow | EndedThread | None`, CAS-32), `reads.invoice` / `appointment` /
  `customer` (CAS-19), `reads.identity_state`, `reads.new_flags_count`, `reset.clear_demo_tables(reset_id) -> Cleared`
  (CAS-1, CAS-3), `events.latest_of` (MC-8), `turns.timeouts_for`, `messages.recent`, `messages.append`,
  `messages.belongs_to_case`, `messages.handoff_anchor` (CAS-38), `check_events.append`, `lookup_log.for_thread`,
  `cases_ro.owner`, `turns.fail_running() -> tuple[TurnId, ...]` (cases §1.2; web.md §9 restart sweep; R-W-4, R-G-22:
  one `UPDATE turns SET status='failed', path='degraded', outcome='degraded_handoff', degrade_reason='timeout' WHERE
  status='running'`, returning the ids, other columns untouched, no age test), and `settled_for(thread_id, read_at) ->
  Settled`, the one builder of `Settled` (stage7/graph-core.md §6, GRC-12). `lookup_log.append` copies `thread_id` from
  the message row the entry names, in the same transaction. The `EndedThread` and `Cleared` shapes are cases §1.2's;
  `core.lookup_log.for_thread` returns `domain.tools.LookupRow` (cases §1.2 fields, CAS-38), which AEA-02 writes in
  `domain/tools.py` beside `LookupEntry` and `repos_core.py` imports (R-G-8).
- **`repos_cases.py`** (slice plan §0): the names cases §1.2 lists for AEA-29/30/31 (`cases.*`, `case_events.append` /
  `exists`, `promises.*` incl. `list_open_past`, `followups.*`, `activities.*`, `demo_state.get` / `set_now` /
  `set_staffing` / `reset`, `demo_events.insert`, `job_runs.start` / `finish` / `latest`, `records.reset_event` /
  `seed_event` / `seed_rows_present`, `refs.next_case_ref`), and the constant `DEMO_START` = 2026-10-16 10:00
  America/Chicago (CAS-23). Bodies are AEA-10's; the semantics (case lifecycle, scheduling rules) are the callers'.
- **`clear_demo_tables`** restores nothing and clears, updates and keeps exactly cases §1.3: each open conversation is
  first copied to `ended_threads`; the *Cleared* tables lose every row (sequences kept); `staff_sessions` rows with
  `role != 'customer'` get `role = 'customer', role_reset_pending = 1` (none deleted; staff.md §4); the *Kept* tables are
  untouched. It returns `Cleared` (open threads, case streams read before the events go, `roles_reset`, rows per table).
- **`adapters/checkpointer.py`**: the LangGraph `SqliteSaver` factory over its own file `checkpoints.sqlite` (DO-1 §4, §9);
  `Checkpointer.prune(keep=2) -> int` [Decided SDQ-10], `clear()`, and `clearing() -> ContextManager[None]` (own
  connection, `BEGIN IMMEDIATE`, delete every saver table, commit on clean exit, roll back on exception; CAS-2).
- **`tests/fixtures/sqlite.py` `temp_sqlite()`** (CAS-4): a temporary working copy with every `schema/*.sql` applied,
  removed afterwards, so service tests run on real SQLite (code-design S-6). AEA-11 keeps `tests/fakes/`.

The planner derives any further method from the consumers the slice plan and cases §1.2 name (AEA-26…32, 34, 38, 40, 41,
44, 46, 51…53) and lists it as `added` in the plan. After wave 1, `db.py`, `repos_core.py`, `repos_cases.py`,
`migrate.py` and `schema/*.sql` are frozen (slice plan §3): a missing method or column is a small follow-up merged first.

**Example pair.** Input: WP-4F, turn 3 moves Linda Foster's visit and records a `moved` action keyed
(thread, turn 3, `moved`, appointment id); turn 4 is "Yes, please." Expected output: `actions.for_thread(thread)` and
`settled_for(thread, read_at)` at turn 4 return the turn-3 `moved` action with its before/after values, so the turn-4
reply can say it is moved (DO-3 §1). A retried turn 3 with the same key writes nothing new and returns the existing row
(DO-1 §8.1 *Try again is idempotent*). Input: a reset after slot 56 was booked in the copy. Expected output: slot 56 is
`open` again, the spend ledger row written that morning is still there, and the thread now answers `EndedThread`.

### Source
- stage7/cases.md §1.0–§1.5 (CAS-1…5, 19, 23, 32, 35, 38), §7 (how `ResetService` calls the callables), §5 (staff-guidance
  rows via `handoff_anchor`); decision ledger `docs/plans/7b-decisions/cases.md`; merge-clashes MC-8, MC-10, MC-11, MC-15,
  MC-16, MC-20; stage7/graph-core.md §2 (`TurnRecord`, GRC-21), §6 (`settled_for`, GRC-12); stage7/graph-nodes.md §1
  (`CheckEvent` columns); residuals R-G-8, R-G-22 (`residuals-graph.md`), R-W-4 (`residuals-web.md`); journey criterion
  `docs/plans/ux-join/backend-amendments.md` §3; stage7/staff.md §3–§4; stage7/models.md §6 (`spend_ledger`); stage7/graph-tools.md §5 (identity
  DDL); stage7/data.md §6 (eval run fields); stage7/web.md §4, §9 (`owned_thread`, the turn path's writes).
- DO-3 code-design §2.1, §3, §4.3, §5.1, §8, §9, §11 RB-1, S-6; DO-4 §1 (`ActionKey`, `CompletedAction`, `Settled`), §5
  (`LookupEntry`), §13 (`UnitOfWork`, methods), §16 (addenda win).
- DO-1 system-design §9 (durability, first boot), §8.2 (lock timeout), §A.5, §11 decisions 2 and 3; DO-6
  observability-contract *Records*, *Correlation*, *Storage and access*, *Missing instrumentation*, WF-16 row. PRD R-19,
  R-33, R-45. Issued `scheduling_db/SCHEMA.md`; `docs/data/issued/README.md`.
- Slice plan §0 deviations 1–2, §1 row AEA-10, §3 collision map rows `adapters/sqlite/*`, `schema/*.sql`, `tests/fixtures/sqlite.py`.
- **Brief check:** serves "Mock scheduling database with availability check and booking write capability" (writes land
  on a working copy, R-19) and "system should be able to run unmanned for a month, failures should be observable"
  (records survive restart); touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] With no working copy present, first boot copies the issued DB and applies every `schema/*.sql` in numeric order; the five issued tables keep the issued row counts (customers 154, technicians 8, appointment_slots 528, appointments 159, invoices 81; DO-1 §9 [M]) — verify: `tests/unit/adapters/sqlite/test_migrate.py::test_first_boot_copies_issued_db_and_applies_schema` — evidence: the table list contains every table of cases §1.1 across `00_core` … `95_ops`; the five counts equal the issued file's.
- [ ] AC-2 [invariant] A boot with an existing working copy keeps every row written before it (SD-7.2 restart survival, DO-1 §9) — verify: `test_migrate.py::test_existing_working_copy_survives_restart` — evidence: a conversation, an action and a case written before the second boot are read back unchanged.
- [ ] AC-3 [negative] The issued file is never written (R-19; issued README): its SHA-256 is identical before and after first boot, a write through the unit of work, and `restore_working_copy(tx)`; a distinctive value written through the unit of work is absent from the issued file — verify: `test_migrate.py::test_issued_file_never_written` — evidence: equal hashes; the value found in the working copy and not in the issued file.
- [ ] AC-4 [invariant] `restore_working_copy(tx)` returns the five issued tables to the issued rows inside the caller's transaction (a slot booked in the copy is `open` again; the next appointment insert gets id 160), and a row in each *Kept* table of cases §1.3 survives it (CAS-1) — verify: `test_migrate.py::test_restore_working_copy_restores_issued_tables` — evidence: slot status back to the issued value; `sqlite_sequence` at the issued maximum; the kept rows present.
- [ ] AC-5 [failure/refusal] `restore_working_copy(tx)` called in a unit of work that then raises leaves the copy exactly as before (the reset is all-or-nothing, CAS-2) — verify: `test_migrate.py::test_restore_rolls_back_with_caller` — evidence: the booked slot is still `booked` after the raised block.
- [ ] AC-6 [invariant] `clear_demo_tables(reset_id)` clears, updates and keeps exactly the tables of cases §1.3: every *Cleared* table is empty, each open conversation has an `ended_threads` row carrying `reset_id`, every non-customer `staff_sessions` row is `customer` with `role_reset_pending = 1` and none is deleted, every *Kept* table keeps its rows, and the returned `Cleared` lists the open threads, the case streams that had events and `roles_reset` (CAS-1, CAS-3, CAS-32; staff.md §4) — verify: `test_migrate.py::test_clear_demo_tables_matches_table_list` — evidence: one assertion per table in §1.3 and per `Cleared` field.
- [ ] AC-7 [invariant] After a clear, `events.append` returns ids higher than any id before the clear (AUTOINCREMENT, CAS-1) and `conversations.lookup` returns an `EndedThread` with `reason` and `reset_id` for a cleared thread, `None` for an unknown one (CAS-32) — verify: `tests/unit/adapters/sqlite/test_repos_core.py::test_ids_not_reused_and_tombstone_lookup` — evidence: the new id is greater; the three lookup results.
- [ ] AC-8 [invariant] Every connection runs WAL with `busy_timeout` 5000 ms and foreign keys on; a unit of work left without `commit()` rolls back; an exception inside it rolls back every write and propagates; a write inside a `write=False` unit of work fails (`query_only`) (CAS-35) — verify: `tests/unit/adapters/sqlite/test_uow.py::test_pragmas_commit_and_rollback` — evidence: the three PRAGMA values; zero rows after the uncommitted and the raised block; the read-only write raises.
- [ ] AC-9 [failure/refusal] A `write=True` unit of work blocked by a held `exclusive=True` one gives up after the busy timeout at `BEGIN`, before any statement, and leaves no partial write (DO-1 §8.2 *Booking write*: lock timeout → no write) — verify: `test_uow.py::test_lock_timeout_writes_nothing` — evidence: a lock error raised to the caller; row counts unchanged.
- [ ] AC-10 [invariant] `SqliteUnitOfWork` exposes all seven repositories built over its one connection; importing `meridian.ports.runtime` imports no `meridian.adapters` module at runtime (DO-4 §13, RB-1) — verify: `test_uow.py::test_seven_repos_and_port_imports_no_adapter` — evidence: seven attributes of the declared classes sharing one connection; no `meridian.adapters*` key in `sys.modules` after importing the port alone.
- [ ] AC-11 [invariant] `format_wall` turns a tz-aware datetime into UTC ISO-8601 ending `+00:00`, `parse_wall` returns it tz-aware and equal, and a naive datetime raises `ValueError` (MC-20) — verify: `test_uow.py::test_wall_time_formatter` — evidence: the string for 2026-10-16 10:00 Chicago is `2026-10-16T15:00:00+00:00`; round trip equal; the raise.
- [ ] AC-12 [invariant] `actions.record` is idempotent on `ActionKey`: a second record with the same key returns the existing row and writes nothing (DO-4 §1, §13) — verify: `test_repos_core.py::test_action_record_idempotent_on_key` — evidence: one row; the returned action equals the first.
- [ ] AC-13 [invariant] `actions.for_thread` and `settled_for(thread_id, read_at)` return every completed action of the thread from earlier turns too, with the thread's open case and promise and `read_at` as given (WP-4F turn-3 `moved` read at turn 4; R-45; GRC-12) — verify: `test_repos_core.py::test_settled_for_returns_earlier_turn_move` — evidence: the `moved` action with its before/after values in both results; `Settled.read_at` equals the argument.
- [ ] AC-14 [invariant] `turns.begin(ids, received_at)` writes the turn row on receipt and returns new, completed (with the stored opaque response), running or failed; `turns.finish(turn_id, record)` stores every `TurnRecord` field; `turns.timeouts_for` counts the thread's rows with degrade reason `timeout` (DO-4 §13; GRC-21; graph-core X-3) — verify: `test_repos_core.py::test_turn_begin_finish_and_timeouts` — evidence: each of the four begin results reached; the stored record equal to the one written; the timeout count.
- [ ] AC-15 [invariant] `events.append` returns increasing ids per stream, `events.after(stream, last)` returns only later events of that stream in order, and `events.latest_of(stream, kind)` returns the newest event id of that kind or `None` (code-design S-11; MC-8) — verify: `test_repos_core.py::test_events_after_and_latest_of` — evidence: ids strictly increasing; other streams excluded; the latest `demo_reset` id.
- [ ] AC-16 [invariant] `lookup_log.append` stores the `thread_id` of the message its entry names and `for_thread` returns `meridian.domain.tools.LookupRow`s (R-G-8) id ascending; an entry naming no existing message is rejected; `messages.handoff_anchor` returns the newest customer message id, else the greeting row's id (CAS-38) — verify: `test_repos_core.py::test_lookup_log_and_handoff_anchor` — evidence: the copied thread id; the order; the foreign-key failure; both anchor cases.
- [ ] AC-17 [invariant] `reads.invoice`, `reads.appointment`, `reads.customer` return the current working-copy row read-only, and `reads.identity_state` derives the thread's identity state from the `40_identity.sql` rows as stage7/graph-tools.md §5 states (CAS-19; slice plan §0) — verify: `test_repos_core.py::test_cross_ticket_reads` — evidence: a changed invoice amount read back; an `IdentityState` for a seeded identity row.
- [ ] AC-18 [invariant] `repos_cases` round-trips a case with its case `due_at` and its promise's customer `due_at` (both kept, CAS-10), promise text word for word, `policy_row`, `version`, `seed`, case events with `actor_role` and `case_events.exists`, plus `demo_state` (a fresh store reads `DEMO_START`; `reset()` returns it and `nobody_online`), `demo_events`, `job_runs.latest`, reset and seed records, and `refs.next_case_ref` (after the seeds MHC-C-0005…0008 → MHC-C-0009) (cases §1.1–§1.2; CAS-5, CAS-23) — verify: `tests/unit/adapters/sqlite/test_repos_cases.py` — evidence: each field read back equal to what was written; the next ref.
- [ ] AC-19 [invariant] The checkpointer uses `checkpoints.sqlite`, separate from `meridian.sqlite`; `prune(keep=2)` leaves each thread its last two checkpoints and returns the number removed; `clear()` empties it; `clearing()` rolls back its delete when the block raises and commits it otherwise [Decided SDQ-10; CAS-2] — verify: `tests/unit/adapters/test_checkpointer.py` — evidence: 5 checkpoints on a thread → 2 left, 3 returned; 0 after clear; checkpoints present after a raised `clearing()` block, absent after a clean one.
- [ ] AC-20 [negative] A storage error carries no values: a duplicate action whose `record_id` is a distinctive string raises with table and constraint only, and the string is absent from the exception text and the captured log (system-design §10 *Errors*; `safe-validation-errors.md`) — verify: `test_repos_core.py::test_storage_error_hides_value` — evidence: the assertion on message and `caplog` passes.
- [ ] AC-21 [capture] The tables hold every field DO-6 *Records* and cases §1.1 assign to them, with their correlation ids: `turns` (the `TurnIds` fields, `received_at`, every `TurnRecord` / `TurnTrace` field incl. `server_ms`, `gate_result`, `outcome`, `degrade_reason`, call counts, tokens, cost, `trace_id`, `trace_export`), `conversations` (`run_tag`, `outcome`, `last_customer_wall_at`, `live_state`), `check_events` (every `CheckEvent` field + `thread_id`, `at`), `lookup_log` (+ `thread_id`, `message_id`), `cases` / `promises` keyed by `case_ref` and `thread_id`, `job_runs.job_run_id`, `demo_events.demo_event_id`, `reset_events.reset_id`, `seed_events` (`reset_id`, `deploy_id`, `seed_count`, `label` default `demo seed`) — verify: `tests/unit/adapters/sqlite/test_schema.py::test_do6_fields_present` (reads `PRAGMA table_info`) — evidence: the column list per table. (Real-entry capture is CAP-1…CAP-3 in AEA-51, CAP-5 in AEA-52, CAP-9 in AEA-50.)
- [ ] AC-22 [invariant] `temp_sqlite()` builds a temporary working copy with every `schema/*.sql` applied and removes it afterwards (CAS-4) — verify: `test_schema.py::test_temp_sqlite_applies_all_schema` — evidence: all tables present; no file left behind.
- [ ] AC-23 [invariant] `core.turns.fail_running()` fails every `running` row and nothing else: two `running` rows and one `completed` row → the two ids returned, both `failed` with path `degraded`, outcome `degraded_handoff`, degrade reason `timeout`; the completed row unchanged (cases §1.2; web.md §9; R-W-4, R-G-22) — verify: `tests/unit/adapters/sqlite/test_repos_core.py::test_fail_running_sweeps_every_running_row` — evidence: the two returned ids; the three rows' status, path, outcome and degrade reason printed.
- [ ] AC-24 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-10.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-10 (every journey reads and writes the working copy) as the journeys that will exercise this code once AEA-57, AEA-51, AEA-52 and AEA-53 land, so the seam audit knows where to look (`backend-amendments.md` §3, pattern C) — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-25 [regression/context] Docs updated in the same change: `.claude/reference/area-map.md` A0 row (this ticket's files planned → actual with the commit; `repos_cases.py`, every `schema/*.sql` and `tests/fixtures/sqlite.py` marked as AEA-10's per the slice plan §0 deviation), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 status of these modules planned → built — verify: `git diff --name-only` — evidence: the three files in the diff.

### Observability
- Responsibilities: owns WF-16's migration step (the case-store table creation, DO-6 WF-16 row) and holds the stored
  records DO-6 assigns to SQLite: WF-1 (`conversation`, `turn`, `lookup_log`, `check_event`), WF-2 (`case`, `case_event`,
  `promise`), WF-5 (`demo_event`, CAS-5), WF-7 (`job_run`, promise status), WF-15 (`reset_event`) and WF-16
  (`seed_event`), each keyed by its correlation id (DO-6 *Correlation*). The turn row exists from receipt, so the restart
  sweep (AEA-40, through `core.turns.fail_running()`, AC-23; R-W-4) finds unfinished turns; `seed_event` and `reset_event` survive a reset (cases §1.3), so a drop to zero on
  the pages stays explained. Writes no log record of its own except value-free errors (AC-20).
- Capture evidence: AC-21 (every DO-6 field and correlation id present), AC-14 (row on receipt); records at the real entry
  points: CAP-1…CAP-3 (AEA-51), CAP-5 (AEA-52), CAP-9 incl. `seed_event` (AEA-50).

### Evaluation
- Checks: keeps E-7's DB-copy check possible (the issued file stays pristine to compare against, AC-3; reset restores it,
  AC-4) and E-1's WP-4F state-seam case (AC-13); WF-16's seed segment stays separable (`seed` flag and `run_tag = 'seed'`,
  AC-18, AC-21).
- Expected-answer authority: issued `SCHEMA.md` and the issued DB file (DO-5 *Expected-answer authority*, bookings row);
  cases §1.3 for what a reset keeps.

### Metrics
- References: M-3 and M-18 (`conversation.outcome`, `run_tag`, end time), M-9 (DB-copy check), M-10 (`promise.text` stored
  word for word), M-12 (`check_event`), M-13 (`promise` status and customer due), M-22, M-23 (`turn.server_ms`), M-24
  (`turn.outcome`, `degrade_reason`), M-27 (`case` due, `promise`, `job_run`), M-29 (`turn.trace_export`).
- Acceptance conditions: each stays computable from the stored columns (AC-18, AC-21), and M-3, M-13 and M-27 can be
  reported with and without seed cases (`cases.seed`, `conversations.run_tag`; WF-16); no target is set here.

### Blocked by
AEA-01, AEA-02

### Agent handoff
- Area / owner: A0 Foundation storage (`src/meridian/adapters/sqlite/{db,migrate,repos_core,repos_cases}.py`, every
  `src/meridian/adapters/sqlite/schema/*.sql`, `src/meridian/adapters/checkpointer.py`, `tests/fixtures/sqlite.py`), by
  the slice plan §0 deviations.
- Contracts and shared surfaces: consumes `domain/*` and `ports/runtime.py` and the five repository shells (AEA-02),
  `policy/limits.py` and `tests/conftest.py` (AEA-01). Produces `SqliteUnitOfWork(Factory)`, `format_wall` / `parse_wall`,
  the DDL every repository owner fills against (AEA-26, 27, 28, 32, 44), `repos_core` (AEA-21, 29, 34, 38, 40 incl.
  `turns.fail_running`, 41, 42, 44, 46, 53), `repos_cases` and `DEMO_START` (AEA-29, 30, 31, 32, 52, 53), `restore_working_copy` and
  `clear_demo_tables` (AEA-31), `Checkpointer.prune` / `clearing` (AEA-30, AEA-31), the saver (AEA-51), `temp_sqlite()`
  (every service ticket). Fills only its own `register_<area>()` hunk in `web/container.py`. Must not edit `domain/*`,
  `ports/*`, `tests/fakes/` (AEA-11), or any other `repos_*.py` body.
- Scope boundary / refusal: no service logic (case lifecycle, reset ordering and gate, seed content, scheduler rules,
  clock advance are AEA-29, 30, 31); no repository bodies for spend, identity, booking, staff or ops; never opens the
  issued file for writing; never stores a verification code, card-like number or full phone number in any column it
  defines beyond what the sibling addenda specify.
- Wave and gates: wave 1; no gate. On the critical path (AEA-02 → 10 → 29 → 51 → 55 → 56): its planner may split steps
  inside the ticket, not the ticket.
- Lane: build-loop — source, DDL and test fixtures that code and tests read.
- Risk: None (slice plan).
- Entry points added or changed: WF-16 (migration step creating the case-store tables)
- Resolved R-G-8 (`docs/plans/7b-decisions/residuals-graph.md`): `LookupRow` lives in `domain/tools.py` beside
  `LookupEntry` (AEA-02, wave 0); `core.lookup_log.for_thread` returns `domain.tools.LookupRow`. Resolved R-G-22 / R-W-4:
  `core.turns.fail_running()` is this ticket's (AC-23); AEA-40 calls it once while the container is built.
