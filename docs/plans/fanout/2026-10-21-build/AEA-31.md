# Plan — [AEA-31] reset: all-or-nothing reset and demo seed

**Status:** planned (READY). Implementation starts once **AEA-10, AEA-14 and AEA-23 are merged on `main`** (the
ticket's own blockers; true imports, §9). AEA-02 is already merged. No product decision is open.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/31 (spec copy:
`docs/plans/tickets/AEA-31.md`) · **Base revision when refreshed:** `b095d6c` (main: AEA-01, 02, 03, 04, 25 merged;
no `adapters/sqlite/rows.py`, `db.py`, `migrate.py`, `checkpointer.py`, `policy/handoff.py`, `services/reset_gate.py`
or `web/deps.py` yet) · **Planner:** claude-opus-5-5, first written 2026-10-21 10:53, refreshed 2026-10-21 after
AEA-02 merged and the AEA-10/14/23 plans were refreshed · **Implementer:** `fanout-implementer` on Sonnet.
**Lane:** `lane::build-loop` · **Risk:** none (no `risk::security`: no frozen tests, no security review). The
implementer writes the tests named here together with the code. Wave 2.

**What changed in this refresh (read if you saw the earlier version):**
1. AEA-02's merged code fixed the module homes (§4.1 now gives the exact import block, checked on `main`).
2. `StreamKey`, `thread_stream()`, `case_stream()` are AEA-10's (`meridian.adapters.sqlite.rows`); the old
   "find the StreamKey mechanism or stop" step is gone. All storage row types are imported from `rows.py`.
3. AEA-29's `BriefAssembler` gained an optional `staff_guidance` constructor argument and an optional keyword
   `customer_messages` on `attach_extraction`; this ticket passes neither (§4.3).
4. `FollowupRow.window` is required (no `None`).
5. The J-8 journey step (AC-14) now models **two clients on one login** (two tabs sharing one session), plus a second
   login, as staff.md §4 and the UX join audit (B3) describe; the old plan used two separate logins.
6. AC-11's six-digit check strips canonical UUIDs first (a UUID starting with six digits made it flaky).
7. Lint and type notes for test code (ruff E731 and S608; strict mypy on `tests/`).

## Goal

Quoted from the issue's *What to build* (`docs/plans/tickets/AEA-31.md`):

> **US-25:** As a **reviewer**, I need a demo (reached with the demo login) where the date, the empty staffing, the code
> inbox and the "recorded, not sent" follow-ups are all labelled as demo simulations … Acceptance: … a reset restores the
> demo …
>
> Shapes are `docs/design/contracts/stage7/cases.md` §7 (it revises DO-4 §14's `ResetService`: CAS-1, CAS-2, CAS-3; merge
> MC-19, MC-20) over the storage of §1.1–§1.4 that AEA-10 writes.

Concretely: `services/reset.py` with `ResetService.reset(...)`. It runs one exclusive transaction that:
- restores the five issued tables;
- clears the demo tables;
- resets the clock and staffing;
- ends open chats;
- re-seeds;
- records `reset_events` and `seed_events`;
- then clears checkpoints.

If anything fails before the commit, it changes nothing and returns `ResetFailed`. The ticket also delivers the demo
seed loader `seed_demo` (the four seed cases MHC-C-0005…0008), the first-boot seed, and the `register_reset()`
container hunk.

## Context

Reviewers test against our one deployed copy (brief Q-2), so whatever they break must be restorable in one call. Stage 7
fixed the shapes:
- the reset rewrites the issued tables in place, because a file copy would erase the kept ops tables (CAS-1);
- it clears checkpoints in a second SQLite file that commits after the main one (CAS-2);
- web's `ResetGate` serialises it (CAS-3).

The seed gives the staff screens something to show at the demo start (SCR-5, SCR-7). This ticket is wave 2; storage
(AEA-10), the gate (AEA-23) and the promise table (AEA-14) land in waves 0–1.

---

## 1. Goal and sources

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-31.md` AC-1…AC-15, Agent handoff | Everything in §3 |
| Requirements | PRD R-19 ("A one-command reset restores the copy"), R-33 (demo seed cases); consolidated direction §8 | Restore + seeds |
| Component contracts (win over DO-4) | `docs/design/contracts/stage7/cases.md` §1.1 (tables), §1.2 (`clear_demo_tables`, `Cleared`, `EndedThread`, `demo_state.reset`, `records.*`, `refs.next_case_ref`), §1.3 (restored / cleared / updated / kept), §1.4 (the two callables), §3.2 (`promise_for`, `case_due_at`), §3.3 (`priority_for`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`), §5 (lane rules), §6 (`format_clock`), §7 (this ticket) | Signatures, order, seed set |
| Web addendum | `stage7/web.md` §4 (`owned_thread`, `get_wall_clock`, providers, `RESET_SERVICE`), §5 (`reset_wait_s`), §7 (`ResetGate`, `ResetAlreadyRunning`), §15 (`ContainerOverrides.wall_clock`) | Gate; 410 path; wall clock |
| Staff addendum | `stage7/staff.md` §1 (`LoginSessionId`, `DemoRole`, `LoginSession`, `RoleRefusal`), §4 (staff state on reset: rows kept, `role='customer'`, `role_reset_pending=1`), §7 (CON-21 starts after newest `demo_reset`; `CeDemoReset`) | Roles reset; case-stream event |
| Data addendum | `stage7/data.md` §7 (operator script calls `reset(..., session_id=None, role=None)`) | NULL asker columns |
| DO-4 | `docs/design/contracts/internal-components.md` §7 (`CaseSummary`, `Brief`, `BriefExtraction`, `Quote`, `BriefAssembler`), §13 (`UnitOfWork`, `UnitOfWorkFactory`), §14 (old `ResetService`, superseded), §16 (addenda win) | Types |
| DO-3 | `docs/design/code-design.md` §2.1 (services call `tx.<repo>.<method>`, never SQL, never `sqlite3`; never import other adapters — storage row types are the bounded exception), §4.4 row `services/reset.py`, §6 S-20 (injected callables), §11 S-3 | Module boundary |
| Decision ledger | `docs/plans/7b-decisions/cases.md` CAS-1, 2, 3, 23, 24, 31, 32; `merge-clashes.md` MC-7, 8, 9, 11, 15, 19, 20, 27; `residuals-web.md` R-W-11; `docs/plans/stage7-signoff.md` D-4…D-15 (none answered differently here) | Basis |
| Merged code (on `main` at `b095d6c`) | `src/meridian/domain/*`, `src/meridian/ports/runtime.py` (AEA-02); `src/meridian/policy/texts.py` (AEA-03); `src/meridian/web/container.py` (AEA-01); `tests/journeys/` skeleton, `tests/journeys/affected.py` (AEA-01) | §4.1 imports verified by grep and a scratch construct |
| Sibling plans (shapes not yet on main) | `docs/plans/fanout/2026-10-21-build/AEA-10.md` §4.3 (exact repo/row signatures, refreshed 12:14), step 5, step 7, step 9; `AEA-14.md` §4 (refreshed 12:10); `AEA-23.md` §4.3, step 1, step 5, step 9 (refreshed 12:16); `AEA-29.md` §4 (`BriefAssembler`), §8 R-3, R-4; `AEA-30.md` §4.3, §8 R-1 | Exact names (re-verify after merge, §5 step 0) |
| Wire contract (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `resetDemo`, `ResetResponse` {ok, open_chats_ended, roles_reset, clock}, `DemoClock` {now, label, date_label}, `EvDemoReset` {event_id, type, at, speaker, line}, `CeDemoReset` {event_id, type, at, line}, `Speaker` {kind: event, display_name: null}, `FollowUpView` | Payload and result shapes |
| Screens | SCREEN_SPECS SCR-5 / SCR-7 default states (seed rows and lanes), SCR-1 reset line | Seed placement |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-15 (reset_event, `reset_id`), WF-16 (seed_event, `deploy_id` or `reset_id`), *Storage and access* (demo tables cleared, ops tables kept) | AC-12, AC-13 |
| Evaluation (DO-5) | E-7 DB-copy check compares against the copy AC-1 restores; no scoring suite here | n/a beyond AC-1 |
| Metrics (DO-7) | M-3, M-13, M-27 (seeds a named segment), M-22 (drop explained by `reset_events`), M-26, M-28 (records survive) | `seed = 1`, `run_tag = 'seed'`; kept tables |
| Journey rule | `.claude/rules/integrated-journeys.md` §3–§5; slice plan §0a J-8 (*proposed:* 31); `tests/journeys/README.md` | AC-14 at `mock-tested` |
| Issued data (read-only, checked 2026-10-21 with `mode=ro&immutable=1`) | `docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite` | Seed customers and invoices exist; max `appointment_id` 159; slot 56 `open`; no AUTOINCREMENT on issued tables |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer may create or edit)

| File | Create / modify | What |
|---|---|---|
| `src/meridian/services/reset.py` | create | `ResetClock`, `ResetDone`, `ResetFailed`, seed constants and `SEED_CASES`, `seed_demo`, `seed_first_boot`, `ResetService` (§4.4) |
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_reset`** | §5 step 4 |
| `tests/services/reset_support.py` | create (**plan-added helper module**, not collected by pytest) | Store/checkpointer fixtures, the "dirty demo" builder, snapshots, the recording assembler double (§7.1) |
| `tests/services/test_reset.py` | create | AC-1…AC-13 tests + PA tests (§7.1) |
| `tests/unit/web/test_register_reset.py` | create (plan-added) | PA-4 (§7.1) |
| `tests/journeys/j8/test_aea_31.py` | create | AC-14 journey step at `mock-tested` (§7.1) |
| `docs/testing/journeys/<run-date>-AEA-31.md` | create | AC-14 record (`<run-date>` = `TZ=America/Chicago date +%F`) |
| `.claude/reference/area-map.md` | modify the **A6 row's Status cell only** | AC-15 |
| `.claude/state/icm-progress.md` | **add one row** after the last *Routes verified against code and tests* row | AC-15 |
| `docs/design/code-design.md` | modify **two lines only**: the §3 tree line `│   ├── reset.py …` (line ~254) and the §4 table row `services/reset.py` (line ~394) | AC-15 |

`tests/services/__init__.py` and `tests/unit/web/__init__.py` already exist on `main`; do not recreate them.

### 2.2 Shared surfaces read, never edited

`src/meridian/domain/*`, `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02); `src/meridian/adapters/sqlite/*`
(incl. `rows.py`, `db.py`, `migrate.py`, `repos_core.py`, `repos_cases.py`, every `schema/*.sql`),
`src/meridian/adapters/checkpointer.py`, `tests/fixtures/sqlite.py` (AEA-10); `src/meridian/policy/handoff.py`
(AEA-14); `src/meridian/policy/texts.py` (AEA-03); `src/meridian/services/reset_gate.py`,
`src/meridian/web/{deps,errors,middleware,app}.py` (AEA-23); the rest of `web/container.py`, `policy/limits.py`,
`tests/conftest.py`, `tests/journeys/affected.py`, `tests/journeys/README.md`, `pyproject.toml`, `uv.lock` (AEA-01);
`tests/unit/web/test_container.py` and `tests/unit/test_import_direction.py` (AEA-01/02; your hunk must keep them green,
§5 step 4).

### 2.3 Owned by other tickets — never create or edit

- AEA-10: `migrate.py`, `checkpointer.py`, `rows.py`, any repository or `.sql` file.
- AEA-30: `services/demo.py`, `services/scheduler.py`.
- AEA-29: `services/cases.py`, `services/handoff.py`.
- AEA-23: `services/reset_gate.py`, `web/deps.py`.
- Every other `register_*` hunk.
- AEA-43: `routes/demo.py` (the CON-9 route).
- AEA-50: `scripts/reset.py`, and `tests/capture/` (CAP-9).
- AEA-57: `tests/journeys/support/`.
- Never edit: the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
  `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`.

### 2.4 Must not

- Write SQL or import `sqlite3` in `src/meridian/services/reset.py`.
- Import any of these in that file: `meridian.adapters.sqlite.db`, `meridian.adapters.sqlite.migrate`,
  `meridian.adapters.checkpointer`, `meridian.web`, `meridian.agent`, `meridian.services.handoff`,
  `meridian.services.demo`, or any model SDK (DO-3 §2.1, S-3).
- Row types, `thread_stream`, `case_stream` come from `meridian.adapters.sqlite.rows`, and `DEMO_START` from
  `meridian.adapters.sqlite.repos_cases`. These are the allowed service → storage edge.
- Write `Promise(` or `Settled(` anywhere under `src/`. Only `policy/handoff.py` constructs `Promise`, and only
  `core.settled_for` builds `Settled` (graph-core §6, §10).
- Call `datetime.now()` in `services/reset.py`. Every time is a parameter or a seed constant.
- Clear a *Kept* table (§1.3), write the issued DB file, or leave a partial reset under any failure.
- Put a code, card-like number, full phone number, secret or customer name in code literals, logs, test names or
  fixture literals. Tests that need Omar Patel's name or phone **read them from the issued DB at run time**.
- Call a paid model, bind ports 4019 or 5184, run `git add -A`, push, force-push, copy a venv, or run pytest with more
  than `-n 2`. Never read `.env`.
- Edit `tests/unit/web/test_container.py` (if your hunk turns it red, see §8 R-4).

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's, by ID; the issue text governs) and plan-added obligations

| ID | Requirement (short) | How | Verified by |
|---|---|---|---|
| AC-1 [invariant] | After `reset`, the five issued tables equal the issued file row for row; their `sqlite_sequence` rows equal the issued file's (none today: not AUTOINCREMENT); next appointment id = issued max + 1 (160); the issued file's bytes unchanged | Step 1.8 calls the injected `restore_working_copy(tx)` | `tests/services/test_reset.py::test_reset_restores_working_copy` |
| AC-2 [invariant] | All-or-nothing: a failure injected into each step (restore, `clear_demo_tables`, `demo_state.reset`, the `demo_reset` appends, `seed_demo`, the record writes, the meridian commit) leaves every table of `meridian.sqlite` and `checkpoints.sqlite` as before and returns `ResetFailed` | One `with uow(write=True, exclusive=True) as tx, clear_checkpoints():`; any exception before `tx.commit()` → both roll back → `ResetFailed` (§5 step 1.8) | `::test_reset_all_or_nothing` (parametrised, 8 cases) |
| AC-3 [failure/refusal] | Checkpoint commit fails after meridian committed → `ResetDone`, `reset_events.checkpoints_cleared = 0`, only checkpoints of tombstoned threads remain | `committed` flag; residual branch writes `set_checkpoints_cleared(reset_id, False)` in a new uow | `::test_checkpoint_commit_failure_residual_window` |
| AC-4 [failure/refusal] | Second reset while the gate is held raises `ResetAlreadyRunning`, changes nothing; a writer in flight waits for the exclusive lock | `with self._gate.hold():` outermost, outside the try; `exclusive=True` uow | `::test_concurrent_reset_refused`, `::test_writer_waits_for_reset_lock` |
| AC-5 [invariant] | One `demo_reset` per `cleared.open_threads` and per `cleared.case_streams` stream, ids higher than any before; `open_chats_ended == len(open_threads)`; `roles_reset == cleared.roles_reset`; `lookup(old_thread)` → `EndedThread(reason="demo_reset", reset_id=…)` | Step 1.8 appends; counts from `Cleared` | `::test_reset_ends_open_chats` |
| AC-6 [failure/refusal] | A later call on a reset thread answers 410 `SESSION_ENDED` (`details.reason = "demo_reset"`) for the same login session; another session gets the identical 404 | Tombstones from `clear_demo_tables`; AEA-23's `owned_thread` | `::test_ended_thread_answers_session_ended` |
| AC-7 [invariant] | Clock back to `DEMO_START`, staffing `nobody_online`; `ResetDone.clock` = `format_clock(DEMO_START)` | `tx.cases.demo_state.reset()`; `ResetClock` built from the injected `format_clock(DEMO_START)` | `::test_reset_restores_clock_and_staffing` |
| AC-8 [negative] | Codes, inbox, identity threads, flags cleared; `spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`, `job_runs`, `demo_events` unchanged in count; `reset_events` +1, `seed_events` +1, `ended_threads` + (conversations before) | `clear_demo_tables` (AEA-10); reset only adds its two rows | `::test_reset_clears_codes_keeps_ops_records` |
| AC-9 [invariant] | `seed_demo` writes exactly the four seeds (`seed = 1`, `run_tag = 'seed'`, `created_at < DEMO_START`, promise = `promise_for(reason, "nobody_online", created_at)`, quotes are exact substrings), returns 4; first boot loads once; next live case MHC-C-0009 | `SEED_CASES` + `seed_demo` + `seed_first_boot` | `::test_seed_cases_labelled_and_counted`, `::test_seed_promises_from_table`, `::test_first_boot_seeds_once`, `::test_next_live_ref_after_seeds` |
| AC-10 [invariant] | At `DEMO_START`: MHC-C-0008 P0 and P1, MHC-C-0005 Overdue, MHC-C-0006 and 0007 Unowned; 0007 follow-up phone, mornings | Seed constants; lanes checked by a test-local double of cases §5's lane rules | `::test_seed_lanes_at_demo_start` |
| AC-11 [negative] | Seeds hold only issued or fictional values: no 13–19-digit run, no 6-digit code pattern, every seeded `customer_id` exists in the issued file; no model-written text | Constants only; customers read from the DB | `::test_seed_holds_no_codes_or_cards` |
| AC-12 [capture] | One `reset_events` row per reset with every field; operator call stores NULL askers; one `seed_events` row per load, `reset_id` set in a reset, NULL at first boot, label "demo seed", `at_wall` UTC `+00:00` | Step 1.8 records; `seed_first_boot` | `::test_reset_and_seed_events` |
| AC-13 [negative] | `reset_events` / `seed_events` hold IDs, roles, counts, times only: no session token, customer name, phone, message text | `ResetEventRow` holds only those fields; `restored` = table → count | `::test_reset_records_hold_no_pii` |
| AC-14 [journey] | Extends J-8: a reset from one client sends every staff call of **both clients on that login** to 403 `role_reset` until a role switch, ends the open chat (`demo_reset` on its stream, 410 on its thread), restores the issued tables. Level `mock-tested`; *Blocked by* AEA-57, AEA-52 | Mock-level journey step (no server) | `uv run pytest -m journey tests/journeys/j8/test_aea_31.py -q`; record `docs/testing/journeys/<run-date>-AEA-31.md` |
| AC-15 [regression/context] | Area-map A6 row, one ICM row, DO-3 status for `services/reset.py` (seed loader there; seed list stage7/cases §7) | §5 step 6 | `git diff --name-only main...HEAD` |
| PA-1 (plan-added) | The gate is released after every outcome (done, failed, residual) and a failed reset can be followed by a successful one | `with gate.hold()` context | inside `::test_reset_all_or_nothing` (after `monkeypatch.undo()`) |
| PA-2 (plan-added) | `services/reset.py` imports no SQL, no `db`, `migrate`, `checkpointer`, `web`, `agent`, sibling service (DO-3 S-3) | Imports as §4.4 | `::test_reset_module_imports_no_adapter_callables` |
| PA-3 (plan-added) | A naive `now` is a programming error, raised before the gate is taken | `ValueError` at the top of `reset` | `::test_reset_rejects_naive_now` |
| PA-4 (plan-added) | `register_reset` binds `RESET_SERVICE` and runs the first-boot seed once; a bare `FastAPI()` gets nothing (keeps AEA-01's stub test green) | §5 step 4 | `tests/unit/web/test_register_reset.py::test_register_reset_binds_service_and_seeds_first_boot`, `::test_register_reset_skips_bare_app` |

### 3.2 Source-contract reconciliation (obligations the issue does not state outright)

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| Reset order restore → clear → demo_state → demo_reset → seed → records → commit | cases.md §7 | AC-2 | in-ticket | step 1.8 |
| `demo_reset` payload shape on thread vs case streams | OpenAPI `EvDemoReset` / `CeDemoReset`; staff.md §7 | no | **added**: thread payload `{"speaker": {"kind": "event", "display_name": None}, "line": TEXTS[TextId.DEMO_RESET]}`; case payload `{"line": TEXTS[TextId.DEMO_RESET]}`; `at` = the **pre-reset** demo time (keeps the chat transcript in time order) | step 1.8; tested in AC-5 test |
| Stream naming | AEA-10 plan §4.3 `rows.py` (`thread_stream` = bare id, `case_stream` = `case:<ref>`) | no | in AEA-10; this ticket only calls the two helpers | step 1.8 |
| Tombstone wall time from the caller | AEA-10 step 7 (`ended_at` keyword) | no | **added**: `clear_demo_tables(reset_id, ended_at=now)` | step 1.8 |
| `ResetDone.clock` needs the one formatter (AEA-30, same wave) | cases.md §6, §7; ticket *Agent handoff* ("injected") | yes | **added**: keyword-only constructor argument `format_clock: Callable[[datetime], tuple[str, str]]` (§8 R-2) | step 1.7 |
| `ClockView` has no home (cases A-2 follow-up never cut; AEA-02 merged without it) | cases.md A-2; AEA-30 plan §8 R-1 | no | **added**: local `ResetClock` with OpenAPI `DemoClock` fields, unless a `ClockView` with the same three fields exists in `src/meridian/domain/` at implementation time (§5 step 0.4; §8 R-3) | step 1.2 |
| `BriefAssembler` injected into `seed_demo` (AEA-29, same wave) | ticket *Agent handoff* | yes | in-ticket: `seed_demo(tx, *, assembler)`; container binds `functools.partial` (same pattern as AEA-10's `restore_working_copy(tx, *, issued_path)`) | steps 1.5, 4 |
| Seed threads must not count as open chats (example pair: `open_chats_ended=1` with seeds present; AEA-10 `open_threads` = `live_state <> 'closed'`) | ticket example pair; AEA-10 step 7 | implied | **added**: seed conversations stored with `live_state='closed'`, `outcome='handed_off'` (`'safety_reply'` for 0008) (§8 R-5) | step 1.5 |
| Seed thread ids never reused (ended_threads PK; web.md §11 "thread ids are never reused") | web.md §11; cases.md §1.1 | no | **added**: a fresh `uuid4()` thread and turn id per seed per load | step 1.5 |
| Seed rows the staff views read beyond §7's list (`actions(case_opened)`, brief upsert, `alert` on the P0 seed) | DO-4 §7 `HandoffResult`; AEA-29 AC-1 | no | **added**: one `actions(case_opened)` row per seed; `cases.alert='supervisor_now'` on MHC-C-0008 (R-21: P0) | step 1.5 |
| First-boot seed event `deploy_id` | DO-6 WF-16 (`deploy_id` or `reset_id`) | no | **added**: optional `deploy_id` keyword on `seed_first_boot` (None from this ticket's hunk; AEA-50/51 may pass it) | step 1.6 |
| `seed_event` / `reset_event` written inside the same transaction as the work | cases.md §7 | AC-2, AC-12 | in-ticket | step 1.8 |
| No `ResetBusy` type; `ResetAlreadyRunning` propagates | cases.md §7; web.md §7 | AC-4 | in-ticket | step 1.8 |
| Role reset is per **login session** (all tabs on that login share it) | staff.md §4; `docs/plans/ux-join/audit-staff.md` B3 | AC-14 | in-ticket: J-8 step uses two clients on one session | §7.1 journey test |
| CON-9 route, operator script, CAP-9 at real entry points | ticket *Scope boundary* | — | other-ticket: AEA-43, AEA-50 | — |
| Real `BriefAssembler` and `CaseService.oversight` over the seeds | AEA-29 AC-11, AC-15 | AC-9/10 note | other-ticket: AEA-29 (its own seed-shaped tests), AEA-52 (integration) | §8 R-6 |

### 3.3 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `ResetService.reset` (behind CON-9 / AEA-43 and `scripts/reset.py` / AEA-50) | WF-15 | DO-6 *Covered workflows* WF-15 | CAP-9 (AEA-50); M-22 drop explained |
| `seed_first_boot` from `register_reset()` on start-up; `seed_demo` inside every reset | WF-16 | DO-6 WF-16 | CAP-9 (AEA-50); M-3, M-13, M-27 seed segment |

---

## 4. Shared code to use

§4.1 is **on `main` now** (verified 2026-10-21 at `b095d6c`). §4.2–§4.3 are copied from the refreshed sibling plans and
are **not on `main` yet**; §5 step 0 tells you how to confirm each one after the merges. If a name differs, use the
merged name and record the difference in your report; if a *shape* differs (a missing method or field), stop and
report `blocked-on AEA-NN` — never invent it.

### 4.1 Domain, ports and texts (on `main`) — use exactly this import block in `services/reset.py`

```python
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import CaseRef, CustomerId, InvoiceId, MeridianModel, RequestId, SafetyKind, ThreadId, TurnId
from meridian.domain.handoff import Brief, BriefExtraction, CaseSummary, FollowUp, HandoffReason, Quote
from meridian.domain.identity import IdentityState
from meridian.domain.staff import DemoRole, LoginSessionId
from meridian.domain.state import ConversationState
from meridian.domain.tools import LookupEntry, LookupRow
from meridian.domain.turn import CheckResult, TurnInput
from meridian.policy.texts import TEXTS, TextId, render
from meridian.ports.runtime import UnitOfWork, UnitOfWorkFactory
```

Shapes you rely on (copied from the merged code):

| Name | Module | Shape |
|---|---|---|
| `ThreadId`, `TurnId`, `RequestId` | `domain.common` | `str` subclasses checked against a lower-case UUID4 pattern when a model validates; `ThreadId(str(uuid.uuid4()))` builds one (checked: a model accepts it, and rejects `ThreadId("bad")`) |
| `CustomerId`, `InvoiceId`, `CaseRef` | `domain.common` | `^MHC-[0-9]{5}$`, `^INV-[0-9]{6}$`, `^MHC-C-[0-9]{4}$`; `CaseRef("MHC-C-0005")` |
| `EventId` | `domain.common` | `Annotated[int, Field(ge=0)]` — an alias, **not callable** |
| `HandoffReason` | defined `domain.common`, re-exported `domain.handoff` | `REFUND="refund"`, `COMPLAINT_OR_MANAGER="complaint_or_manager"`, `BILLING_DISPUTE="billing_dispute"`, `SAFETY="safety"` (16 values) |
| `Priority` | same | `P0`…`P4` |
| `Presence` | same | `Literal["nobody_online", "simulated_on_shift"]` |
| `Promise` | same | `policy_row: str; text: str; due_at: datetime \| None; due_label: str \| None; extra_lines: tuple[str, ...] = (); live_queued: bool = False` (never construct it) |
| `FollowUp` | same | `channel: Literal["email","phone"]; destination_label: str; on_record: bool; window: Literal["morning","afternoon","any"]` (**required**); `saved_line: str` |
| `SafetyKind` | `domain.common` | `GAS = "gas"`, `CO`, `SPARKS_SMOKE_FLAMES`, `BURNING_WITH_BREAKER` |
| `CaseSummary` | `domain.handoff` | `case_ref; reason; priority; state: CaseState; created_at; promise; followup: FollowUp \| None; version: int; seed: bool = False; due_at: datetime \| None` (required, may be None) |
| `Brief` | `domain.handoff` | `case_ref; thread_id; assembled_at; status: Literal["ready","being_written","failed"]; headings: tuple[BriefHeading, ...]` (validator: exactly 8 headings numbered 1–8 with `BRIEF_TITLES`, `BRIEF_KEYS`, `BRIEF_ORIGINS`; heading 4 never `checked`; only headings 2, 4, 7 may be `not_generated`) |
| `BriefHeading`, `BriefItem`, `SourceRef`, `BRIEF_TITLES`, `BRIEF_KEYS`, `BRIEF_ORIGINS` | `domain.handoff` | `BriefHeading(number, key, title, origin, checked, items, trimmed, trim_note, not_generated)` (tests only) |
| `Quote` | `domain.handoff` (`LLMFacing`) | `message_id: int; text: str (max 300)` |
| `BriefExtraction` | `domain.handoff` (`LLMFacing`) | `needs: list[Quote]` (1–2); `claims: list[Quote]` (≤5); `open_decision: str` (≤200) |
| `ActionKind`, `ActionKey`, `CompletedAction` | `domain.actions` | `ActionKind.CASE_OPENED = "case_opened"`; `ActionKey(thread_id, turn_id, kind, record_id: str)`; `CompletedAction(key, kind, records: dict[Literal["appointment","slot","old_slot","case","customer","promise"], str], before=None, after=None, at, source="actions_table")` |
| `IdentityState` | `domain.identity` | `status: Literal["not_checked","located","code_sent","verified","not_verified","locked"]; customer_id; masked_hint; code_expires_at; tries_left: int (0–3); codes_sent: int (0–3); verified_at` — all fields required |
| `TurnInput` | `domain.turn` | `turn_id; message_id: int; kind: Literal["text","choice","code","form"]; text_store: str; card_id=None; choice=None; card_number_seen=False; received_at` |
| `CheckResult` | `domain.turn` | `text; removals; passed` (type only; you pass `None`) |
| `ConversationState` | `domain.state` | only `thread_id` and `turn_input` are required; set `settled=` and `identity=` too |
| `LookupEntry`, `LookupRow` | `domain.tools` | `LookupEntry(tool: str, record_ids: tuple[str, ...], passage_ids: tuple[PassageId, ...], result_seen: str, message_id: int, turn_id: TurnId)`; `LookupRow(LookupEntry)` + `id: int`, `thread_id: ThreadId` |
| `DemoRole`, `LoginSessionId`, `LoginSession`, `StaffRole`, `RoleRefusal`, `StaffActor`, `actor_for` | `domain.staff` | `DemoRole` customer/representative/supervisor/owner; `LoginSessionId = NewType(str)`; `LoginSession(session_id, role: DemoRole, role_reset: bool, signed_in_at, expires_at)`; `RoleRefusal(role: DemoRole, needs: tuple[StaffRole, ...], reason: Literal["wrong_role","role_reset"])`; `actor_for(role: StaffRole) -> StaffActor` |
| `UnitOfWork`, `UnitOfWorkFactory` | `ports.runtime` | `UnitOfWorkFactory.__call__(*, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]`; `UnitOfWork.commit() -> None`; attributes `core: CoreRepos`, `cases: CaseRepos`, `spend`, `identity`, `booking`, `staff`, `ops` |
| `TEXTS`, `TextId`, `render` | `policy.texts` (AEA-03) | `TEXTS[TextId.DEMO_RESET] == "The demo was reset, so this chat has ended. Nothing from it was kept."`; `TEXTS[TextId.GREETING]`; `render(TextId.FOLLOWUP_SAVED_PHONE, digits=..., window=...)` → `"Follow-up saved: phone call, the number ending in {digits}, {window}."` |

### 4.2 Storage (AEA-10) — call only these

```python
# meridian.adapters.sqlite.rows  (import every row type and both stream helpers from HERE)
StreamKey = NewType("StreamKey", str)
CASE_STREAM_PREFIX = "case:"
def thread_stream(thread_id: ThreadId) -> StreamKey: ...    # StreamKey(str(thread_id))
def case_stream(case_ref: CaseRef) -> StreamKey: ...        # StreamKey("case:" + str(case_ref))
# row models (MeridianModel, frozen): ConversationRow, EndedThread, Cleared, StreamEvent, EventRow, CaseRow, PromiseRow,
#   FollowupRow, DemoStateRow, ResetEventRow, SeedEventRow, CustomerRow, InvoiceRow
# meridian.adapters.sqlite.repos_cases
DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
SEED_REF_MAX = 8

# tx.core (repos_core.CoreRepos)
tx.core.conversations.insert(row: ConversationRow) -> None
tx.core.conversations.lookup(thread_id: str) -> ConversationRow | EndedThread | None
tx.core.messages.append(thread_id: ThreadId, role: str, text_redacted: str, at: datetime, *, turn_id: TurnId | None = None,
                        kind: str | None = None, card_id: str | None = None, choice_option: str | None = None) -> int
tx.core.lookup_log.append(entry: LookupEntry) -> int        # message_id must exist (thread copied from it)
tx.core.lookup_log.for_thread(thread_id: ThreadId) -> tuple[LookupRow, ...]
tx.core.actions.record(action: CompletedAction) -> CompletedAction
tx.core.events.append(stream: StreamKey, event: StreamEvent) -> EventId
tx.core.reads.invoice(invoice_id: InvoiceId) -> InvoiceRow | None
tx.core.reads.customer(customer_id: CustomerId) -> CustomerRow | None
tx.core.reset.clear_demo_tables(reset_id: str, *, ended_at: datetime | None = None) -> Cleared
tx.core.settled_for(thread_id: ThreadId, read_at: datetime) -> Settled
# tx.cases (repos_cases.CaseRepos)
tx.cases.cases.insert(row: CaseRow) -> None
tx.cases.promises.insert(case_ref: CaseRef, promise: Promise, at: datetime) -> int
tx.cases.promises.current(case_ref: CaseRef) -> PromiseRow | None          # tests
tx.cases.followups.upsert(row: FollowupRow) -> None
tx.cases.briefs.upsert(brief: Brief, at: datetime) -> None
tx.cases.briefs.get(case_ref: CaseRef) -> Brief | None                     # tests
tx.cases.demo_state.get() -> DemoStateRow            # no row → DEMO_START / nobody_online
tx.cases.demo_state.set_now(dt: datetime) -> None; tx.cases.demo_state.set_staffing(mode: str) -> None   # tests
tx.cases.demo_state.reset() -> None
tx.cases.records.reset_event(row: ResetEventRow) -> None
tx.cases.records.seed_event(row: SeedEventRow) -> None
tx.cases.records.seed_rows_present() -> bool
tx.cases.records.set_checkpoints_cleared(reset_id: str, cleared: bool) -> None
tx.cases.records.latest_reset_event() -> ResetEventRow | None; tx.cases.records.latest_seed_event() -> SeedEventRow | None
tx.cases.refs.next_case_ref() -> CaseRef               # max(existing numeric part, 8) + 1
```

Row fields you fill (AEA-10 §4.3, verbatim):

```python
class ConversationRow: thread_id: ThreadId; demo_session: str; run_tag: Literal["live","eval","load","seed"]; run_id: str | None = None
    agent_version: str; started_at: datetime; started_wall_at: datetime | None = None
    staffing_at_start: Literal["nobody_online","simulated_on_shift"] | None = None
    outcome: Literal["ai_resolved","handed_off","safety_reply","abandoned","open"] = "open"; ended_wall_at=None
    last_customer_wall_at=None; controller: Controller = Controller(kind="ai")
    live_state: Literal["not_live","queued","joined","handed_back","closed"] = "not_live"; live_since=None
class EndedThread: thread_id; demo_session: str; ended_wall_at: datetime; reason: str; reset_id: str | None
class Cleared: open_threads: tuple[ThreadId, ...]; case_streams: tuple[CaseRef, ...]; roles_reset: int; rows_cleared: dict[str, int]
class StreamEvent: type: str (1–40 chars); payload: dict[str, JsonValue] = {}; at: datetime   # demo clock
class CaseRow: case_ref; thread_id; turn_id: TurnId | None = None; customer_id: CustomerId | None = None; reason; priority
    rule_id: str; trigger: str; lifecycle: Lifecycle; owner_role=None; owner_since=None; due_at: datetime | None = None
    wake_up_at=None; version: int = 1; seed: bool = False; safety_kind: str | None = None; change_request=None
    alert: Literal["supervisor_now"] | None = None; created_at: datetime; updated_at: datetime; resolved_at=None; queued_at=None
class FollowupRow: case_ref; thread_id; channel: Literal["email","phone"]; destination_label: str; destination: str | None = None
    on_record: bool; window: Literal["morning","afternoon","any"]; saved_line: str; updated_at: datetime
class DemoStateRow: demo_now: datetime; staffing: Literal["nobody_online","simulated_on_shift"]
class ResetEventRow: reset_id: str; at_wall: datetime; asked_by_role: DemoRole | None = None; asked_by_session: str | None = None
    request_id: str | None = None; restored: dict[str, int] = {}; open_chats_ended: int = 0; roles_reset: int = 0
    checkpoints_cleared: bool | None = None
class SeedEventRow: seed_event_id: str; at_wall: datetime; reset_id: str | None = None; deploy_id: str | None = None
    seed_count: int (ge 0); label: str = "demo seed"
```

What `clear_demo_tables` does (AEA-10 step 7), so you know what the reset relies on: reads `open_threads`
(`live_state <> 'closed'`) and `case_streams` (`events.stream LIKE 'case:%'`) first; tombstones **every** conversation
into `ended_threads` (reason `demo_reset`, the `reset_id`, `ended_wall_at = ended_at`); sets every non-customer
`staff_sessions` row to `role='customer', role_reset_pending=1` (rows kept; count = `roles_reset`); then deletes, children
first: `lookup_log, check_events, actions, turns, messages, events, case_briefs, activities, followups, promises,
case_events, cases, conversations, flags, identity_codes, demo_inbox, identity_threads` (counts → `rows_cleared`). It
never touches issued, kept or `demo_state` rows.

Callables the container passes (you never import them in `services/reset.py`):
`functools.partial(restore_working_copy, issued_path=…)` (`meridian.adapters.sqlite.migrate`; requires a
`SqliteUnitOfWork` with an open write transaction, never commits) and `Checkpointer.clearing` (`meridian.adapters.checkpointer`,
a bound method returning `ContextManager[None]`: own connection, `BEGIN IMMEDIATE`, deletes every saver table, commits on
clean exit, rolls back and re-raises on exception).

Container keys AEA-10 provides (its step 9): `Key[SqliteUnitOfWorkFactory]("uow_factory")`,
`Key[Checkpointer]("checkpointer")`, `Key[Callable[..., None]]("restore_working_copy")`.

Test fixture: `from tests.fixtures.sqlite import ISSUED_DB, TempStore, temp_sqlite` — `TempStore(data_dir, db_path,
issued_path, uow: SqliteUnitOfWorkFactory)`; `temp_sqlite()` is a plain context manager. `SqliteUnitOfWork.connection`
(property) gives tests raw SQL access. `from meridian.adapters.checkpointer import CHECKPOINTS_DB_NAME, Checkpointer`
(`Checkpointer(path)` with `.saver`, `.path`, `.clearing()`, `.close()`). `from meridian.adapters.sqlite.migrate import
restore_working_copy`.

### 4.3 Policy, gate and web (AEA-14, AEA-23)

```python
# meridian.policy.handoff (AEA-14)
def promise_for(reason: HandoffReason, presence: Presence, now: datetime, window_start: datetime | None = None) -> Promise
def case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None
def priority_for(reason: HandoffReason, *, promise_due: datetime | None = None, renewal_date: date | None = None) -> Priority
DUE_SOON_WINDOW: Final = timedelta(hours=4); UNOWNED_AFTER: Final = timedelta(minutes=30)
# meridian.services.reset_gate (AEA-23)
class ResetAlreadyRunning(Exception): ...
class ResetGate:
    def held(self) -> bool: ...
    def hold(self) -> ContextManager[None]: ...   # raises ResetAlreadyRunning on enter when already held (threading.Lock, non-blocking)
# meridian.web.deps (AEA-23) — keys and providers (container hunk and tests only; never from services/)
RESET_SERVICE = Key[Any]("reset_service"); RESET_GATE = Key[ResetGate]("reset_gate")
UOW_FACTORY = Key[UnitOfWorkFactory]("uow_factory"); WALL_CLOCK = Key[Callable[[], datetime]]("wall_clock")
class StaffAccess(Protocol):
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal: ...
def owned_thread(thread_id: str, session: LoginSession = Depends(get_login_session),
                 uow: UnitOfWorkFactory = Depends(get_uow_factory)) -> ThreadId
    # tombstone of my session → 410 SESSION_ENDED details {"reason": <reason>}; otherwise identical 404 SESSION_NOT_FOUND
def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]
    # RoleRefusal → 403 ROLE_NOT_ALLOWED details {"role", "needs", "reason"}
def get_login_session(ctx: RequestContext = Depends(get_request_context)) -> LoginSession
def get_uow_factory(request: Request) -> UnitOfWorkFactory; def get_staff_access(request: Request) -> StaffAccess
# meridian.web.errors (AEA-23)
class ApiProblem(Exception); async def handle_api_problem(request, exc) -> Response
    # request_id = request.state.request_id or a fresh uuid4 (works without the middleware);
    # body {"error": {"code", "field", "constraint", "details"}, "request_id"}
# meridian.web.middleware (AEA-23)
class PublicPaths: ...   # PublicPaths() with no arguments
@dataclass(frozen=True) class WebShellState: settings: Settings; wall_clock: Callable[[], datetime]; public_paths: PublicPaths
# meridian.web.container (AEA-01, on main)
class Container(*, settings: Any, limits: Limits); class Key[T](name); Container.provide(key, factory); .get(key); .on_start(fn)
    .on_close(fn); .build(); .close(); private dict ._factories
# meridian.policy.limits (AEA-01, on main): class Limits (no-argument constructor)
```

Siblings in the **same wave** (never imported by `services/reset.py`; reached through injection):

```python
# meridian.services.handoff (AEA-29)
class BriefAssembler:
    def __init__(self, staff_guidance: Mapping[PassageId, StaffGuidance] | None = None) -> None: ...
    def assemble(self, case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]) -> Brief: ...
    def attach_extraction(self, brief: Brief, extraction: BriefExtraction | None, check: CheckResult | None,
                          *, customer_messages: Mapping[int, str] | None = None) -> Brief: ...
# meridian.services.demo (AEA-30)
def format_clock(dt: datetime) -> tuple[str, str]: ...
    # ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)") for DEMO_START
```

This ticket calls `BriefAssembler()` with no argument and `attach_extraction(brief, extraction, None)` without
`customer_messages` (AEA-29 R-4: both optional "so AEA-31's seeds … compile unchanged").

### 4.4 What this ticket exports (`src/meridian/services/reset.py`) — exact

```python
"""Demo reset and demo seed (AEA-31; stage7/cases.md §7, CAS-1…3, CAS-24).

ResetService restores the demo all-or-nothing; seed_demo writes the four seed cases; seed_first_boot loads them once.
Adapters arrive as injected callables (DO-3 S-3); this module writes no SQL.
"""
from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Protocol
from zoneinfo import ZoneInfo

from pydantic import Field

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.adapters.sqlite.rows import (
    CaseRow, ConversationRow, FollowupRow, ResetEventRow, SeedEventRow, StreamEvent, case_stream, thread_stream,
)
# + the §4.1 block
from meridian.policy.handoff import case_due_at, priority_for, promise_for
from meridian.services.reset_gate import ResetGate

CHICAGO = ZoneInfo("America/Chicago")
SEED_DEMO_SESSION = "demo-seed"            # conversations.demo_session of seed threads; no login session matches it
SEED_AGENT_VERSION = "demo-seed"           # conversations.agent_version of seed threads
SEED_COUNT = 4

class ResetClock(MeridianModel):           # = OpenAPI DemoClock; same fields as AEA-30's ClockView (cases A-2, §8 R-3)
    now: datetime
    label: str
    date_label: str

class ResetDone(MeridianModel):            # = OpenAPI ResetResponse (CAS-31)
    ok: Literal[True] = True
    open_chats_ended: int = Field(ge=0)
    roles_reset: int = Field(ge=0)
    clock: ResetClock

class ResetFailed(MeridianModel):
    code: Literal["RESET_FAILED"] = "RESET_FAILED"

@dataclass(frozen=True)
class SeedCase:                            # one row of cases.md §7's seed table (CAS-24)
    ref: str                               # "MHC-C-0005"
    reason: HandoffReason
    rule_id: str                           # "R24.refund", "R5.gas", …
    trigger: Literal["escalation", "safety"]
    safety_kind: SafetyKind | None
    customer_id: str | None                # issued customer (None = unmatched caller)
    invoice_id: str | None                 # read_invoices lookup row when set
    created_at: datetime                   # Chicago, before DEMO_START
    outcome: Literal["handed_off", "safety_reply"]
    alert: Literal["supervisor_now"] | None
    messages: tuple[str, ...]              # fixed customer messages, in order
    needs: tuple[str, ...]                 # heading 2 quotes (each an exact substring of one message)
    claims: tuple[str, ...]                # heading 4 quotes
    open_decision: str                     # heading 7 (≤ 200 chars)
    followup_window: Literal["morning"] | None   # phone follow-up on record (MHC-C-0007 only)

SEED_CASES: tuple[SeedCase, ...]           # §6.1, in ref order

class _BriefAssembler(Protocol):           # private typing of the injected AEA-29 object (not a new seam; §8 R-7)
    def assemble(self, case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]) -> Brief: ...
    def attach_extraction(self, brief: Brief, extraction: BriefExtraction | None,
                          check: CheckResult | None) -> Brief: ...

def seed_demo(tx: UnitOfWork, *, assembler: _BriefAssembler) -> int: ...
    # the container binds functools.partial(seed_demo, assembler=BriefAssembler()) = Callable[[UnitOfWork], int]
def seed_first_boot(uow: UnitOfWorkFactory, seed: Callable[[UnitOfWork], int], now: datetime, *,
                    deploy_id: str | None = None) -> int: ...      # 4 on an empty store, 0 when seed rows exist

class ResetService:                        # cases.md §7 constructor + one keyword (§8 R-2)
    def __init__(self, uow: UnitOfWorkFactory, gate: ResetGate,
                 restore_working_copy: Callable[[UnitOfWork], None],
                 clear_checkpoints: Callable[[], AbstractContextManager[None]],
                 seed_demo: Callable[[UnitOfWork], int], *,
                 format_clock: Callable[[datetime], tuple[str, str]]) -> None: ...
    def reset(self, now: datetime, *, request_id: RequestId, session_id: LoginSessionId | None,
              role: DemoRole | None) -> ResetDone | ResetFailed: ...
```

Use `contextlib.AbstractContextManager` (not `typing.ContextManager`; ruff UP035). Let `ruff format` and `ruff check
--fix` (isort, `I`) order the import block; the grouping above is content, not layout.

---

## 5. Steps (build order; each step checkable)

Module boundary: `services/reset.py` is an A6 service. It **implements** nothing from a port; it **consumes**
`UnitOfWorkFactory`/`UnitOfWork` (port), `ResetGate` (services, AEA-23), the policy functions (AEA-14, AEA-03), three
injected callables, one injected assembler and one injected formatter. Dependency direction: `web/container.py` →
`services/reset.py` → `policy`, `domain`, `ports`, `services/reset_gate.py`, storage row types. Nothing in `services/`
imports `web/`.

### Step 0 — environment, preconditions, confirm shapes (no code)

1. `cd /home/linuxuser/workspaces/inno-aea-callcenter && export UV_LINK_MODE=hardlink && uv sync` (no venv copy, no
   `node_modules`).
2. Confirm the blockers are merged:
   `ls src/meridian/adapters/sqlite/rows.py src/meridian/adapters/sqlite/db.py src/meridian/adapters/sqlite/migrate.py src/meridian/adapters/checkpointer.py tests/fixtures/sqlite.py src/meridian/policy/handoff.py src/meridian/services/reset_gate.py src/meridian/web/deps.py src/meridian/web/errors.py src/meridian/web/middleware.py`.
   Any missing → stop, report `blocked-on AEA-10 / AEA-14 / AEA-23` (whichever).
3. Confirm the §4.2–§4.3 names:
   - `grep -n "^def thread_stream\|^def case_stream\|^class StreamEvent\|^class ConversationRow\|^class CaseRow\|^class FollowupRow\|^class ResetEventRow\|^class SeedEventRow\|^class Cleared\|^class EndedThread" src/meridian/adapters/sqlite/rows.py`
   - `grep -n "def clear_demo_tables\|def set_checkpoints_cleared\|def seed_rows_present\|def upsert\|def settled_for\|def next_case_ref\|^DEMO_START" src/meridian/adapters/sqlite/*.py`
   - `grep -n "^def promise_for\|^def case_due_at\|^def priority_for\|^DUE_SOON_WINDOW\|^UNOWNED_AFTER" src/meridian/policy/handoff.py`
   - `grep -n "class ResetGate\|class ResetAlreadyRunning" src/meridian/services/reset_gate.py`
   - `grep -n "^RESET_SERVICE\|^RESET_GATE\|^UOW_FACTORY\|^WALL_CLOCK\|^def owned_thread\|^def require_staff\|^def get_login_session\|^def get_uow_factory\|^def get_staff_access" src/meridian/web/deps.py`

   Handling:
   - If `clear_demo_tables` has no `ended_at` keyword, call it without (note it).
   - If `set_checkpoints_cleared`, `briefs.upsert`, `thread_stream` or `case_stream` is missing → stop,
     `blocked-on AEA-10` (follow-up).
   - If the row types live in a different module than `rows.py` (for example only re-exported from `repos_core`),
     import them from wherever `grep -rn "^class ConversationRow" src/meridian` finds them. Record that in your report.
4. **ClockView.** Run `grep -rn "^class ClockView" src/meridian/domain src/meridian/services`.
   - If it finds a class in `src/meridian/domain/` with exactly the fields `now: datetime`, `label: str`,
     `date_label: str`: import it and write `ResetClock = ClockView` instead of the class in §4.4. Tests keep using
     `ResetClock`.
   - Otherwise (including when the only hit is `services/demo.py`, which this module must not import): define
     `ResetClock` as §4.4.
5. Read `tests/unit/web/test_container.py::test_every_register_stub_present` (AEA-01's, line ~64). Note whether
   AEA-10's two-line guard (its §8 R-13: skip hunks whose docstring lacks "No-op until") is there. Your hunk's
   bare-app guard keeps the test green either way.

### Step 1 — `src/meridian/services/reset.py`

1. Module docstring, imports and constants exactly as §4.4. `_log = logging.getLogger(__name__)`.
2. `ResetClock` (or the alias, step 0.4), `ResetDone`, `ResetFailed` as §4.4.
3. `SeedCase` and `SEED_CASES` with the values of §6.1, character for character. Add a private `_check_seed_table()`
   called once at module level. It checks, for every seed:
   - every `needs`/`claims` quote is a substring of at least one of its `messages`;
   - `1 <= len(needs) <= 2`, `len(claims) <= 5`, `len(open_decision) <= 200`, every quote ≤ 300 chars;
   - refs are `MHC-C-0005…0008` in order.

   On failure: `raise RuntimeError(f"seed table invalid: {seed.ref}")` (names only). Invariant: a bad edit to the seed
   table fails at import, not in the demo.
4. Private helpers:
   - `_quote(text: str, messages: tuple[str, ...], message_ids: list[int]) -> Quote`: `i` = the index of the first
     message containing `text`; return `Quote(message_id=message_ids[i], text=text)`.
   - `_last_two_digits(phone: str) -> str`: `digits = "".join(c for c in phone if c.isdigit())`; return `digits[-2:]`.
     Never log or return the full number.
5. `seed_demo(tx, *, assembler) -> int` — for each `seed` in `SEED_CASES`, in order. The invariant each step protects
   is in brackets.
   1. `thread_id = ThreadId(str(uuid.uuid4()))`, `turn_id = TurnId(str(uuid.uuid4()))` [thread ids are never reused
      across loads; `ended_threads.thread_id` is a primary key].
   2. `t0 = seed.created_at - timedelta(minutes=3)`. Insert the conversation:
      ```python
      tx.core.conversations.insert(ConversationRow(thread_id=thread_id, demo_session=SEED_DEMO_SESSION,
          run_tag="seed", agent_version=SEED_AGENT_VERSION, started_at=t0, staffing_at_start="nobody_online",
          outcome=seed.outcome, live_state="closed"))
      ```
      [`live_state='closed'` keeps seed threads out of `open_thread_ids` and `Cleared.open_threads`, so
      `open_chats_ended` counts real chats only; `run_tag='seed'` keeps them out of live metrics.]
   3. Write the messages:
      - `tx.core.messages.append(thread_id, "assistant", TEXTS[TextId.GREETING], t0)`.
      - For `i, text in enumerate(seed.messages)`: `at = seed.created_at - timedelta(minutes=len(seed.messages) - i)`;
        `mid = tx.core.messages.append(thread_id, "customer", text, at, turn_id=turn_id, kind="text")`.
      - Keep the lists `message_ids` and `message_ats`.

      [Quotes point at customer messages of this thread.]
   4. If `seed.customer_id`: `customer = tx.core.reads.customer(CustomerId(seed.customer_id))`; `None` →
      `raise LookupError("seed customer missing")` [seeds use issued customers only, AC-11].
   5. If `seed.invoice_id`:
      - `inv = tx.core.reads.invoice(InvoiceId(seed.invoice_id))`; `None` → `raise LookupError("seed invoice missing")`.
      - Append the lookup row:
        ```python
        tx.core.lookup_log.append(LookupEntry(tool="read_invoices", record_ids=(seed.invoice_id,), passage_ids=(),
            result_seen=f"{inv.invoice_id} amount_cents={inv.amount_cents} balance_cents={inv.balance_cents}",
            message_id=message_ids[0], turn_id=turn_id))
        ```

      [Ids and amounts only, graph-tools §4. It reads from the restored copy, so `changed` stays false.]
   6. `promise = promise_for(seed.reason, "nobody_online", seed.created_at)`; `priority = priority_for(seed.reason)`;
      `due = case_due_at(seed.reason, promise, None)` [promise at the seed's own `created_at`, never recomputed].
   7. Insert the case:
      ```python
      ref = CaseRef(seed.ref)
      tx.cases.cases.insert(CaseRow(case_ref=ref, thread_id=thread_id, turn_id=turn_id,
          customer_id=CustomerId(seed.customer_id) if seed.customer_id else None, reason=seed.reason, priority=priority,
          rule_id=seed.rule_id, trigger=seed.trigger, lifecycle="unassigned", due_at=due, seed=True,
          safety_kind=seed.safety_kind.value if seed.safety_kind else None, alert=seed.alert,
          created_at=seed.created_at, updated_at=seed.created_at))
      ```
   8. `tx.cases.promises.insert(ref, promise, seed.created_at)`.
   9. Follow-up, only when `seed.followup_window` is set:
      ```python
      digits = _last_two_digits(customer.phone)
      label = f"the number ending in {digits}"
      line = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window="mornings")
      tx.cases.followups.upsert(FollowupRow(case_ref=ref, thread_id=thread_id, channel="phone",
          destination_label=label, destination=None, on_record=True, window="morning", saved_line=line,
          updated_at=seed.created_at))
      followup = FollowUp(channel="phone", destination_label=label, on_record=True, window="morning", saved_line=line)
      ```
      Otherwise `followup = None`. [Only two digits are ever stored.] mypy note: `customer` is only bound when
      `seed.customer_id` is set; assert `customer is not None` before reading `customer.phone`. The seed table
      guarantees it (only MHC-C-0007 has a window, and it names a customer).
   10. Record the action:
       ```python
       action = CompletedAction(key=ActionKey(thread_id=thread_id, turn_id=turn_id, kind=ActionKind.CASE_OPENED,
           record_id=seed.ref), kind=ActionKind.CASE_OPENED, records={"case": seed.ref}, at=seed.created_at)
       tx.core.actions.record(action)
       ```
   11. `summary = CaseSummary(case_ref=ref, reason=seed.reason, priority=priority, state="unassigned",
       created_at=seed.created_at, promise=promise, followup=followup, version=1, seed=True, due_at=due)`.
   12. `identity`:
       - when `seed.customer_id`: `IdentityState(status="verified", customer_id=CustomerId(seed.customer_id),
         masked_hint=None, code_expires_at=None, tries_left=3, codes_sent=1,
         verified_at=seed.created_at - timedelta(minutes=2))`;
       - else `IdentityState(status="not_checked", customer_id=None, masked_hint=None, code_expires_at=None,
         tries_left=3, codes_sent=0, verified_at=None)`.
   13. Build the conversation state:
       ```python
       state = ConversationState(thread_id=thread_id, turn_input=TurnInput(turn_id=turn_id,
           message_id=message_ids[-1], kind="text", text_store=seed.messages[-1], received_at=message_ats[-1]),
           settled=tx.core.settled_for(thread_id, seed.created_at), identity=identity)
       ```
   14. `extraction = BriefExtraction(needs=[_quote(q, seed.messages, message_ids) for q in seed.needs],
       claims=[_quote(q, seed.messages, message_ids) for q in seed.claims], open_decision=seed.open_decision)`.
   15. Assemble and store the brief:
       ```python
       brief = assembler.assemble(summary, state, tx.core.lookup_log.for_thread(thread_id))
       brief = assembler.attach_extraction(brief, extraction, None)
       tx.cases.briefs.upsert(brief, seed.created_at)
       ```
       [In production the real assembler builds the brief from hand-written quotes; no model call.]

   Return `len(SEED_CASES)`. Never commits (the caller owns the transaction).
6. `seed_first_boot(uow, seed, now, *, deploy_id=None) -> int`:
   1. `if now.tzinfo is None or now.utcoffset() is None: raise ValueError("seed needs an aware wall-clock time")`.
   2. `with uow(write=True) as tx:` [one write transaction: the presence check and the writes are atomic, so two starts
      can never both seed].
   3. `if tx.cases.records.seed_rows_present(): return 0`.
   4. `n = seed(tx)`; then
      `tx.cases.records.seed_event(SeedEventRow(seed_event_id=str(uuid.uuid4()), at_wall=now, reset_id=None,
      deploy_id=deploy_id, seed_count=n))`; `tx.commit()`; return `n`.
7. `ResetService.__init__`: store the six arguments on private attributes (`self._uow`, `self._gate`, `self._restore`,
   `self._clear_checkpoints`, `self._seed`, `self._format_clock`); nothing else.
8. `ResetService.reset(now, *, request_id, session_id, role)`:
   1. `if now.tzinfo is None or now.utcoffset() is None: raise ValueError("reset needs an aware wall-clock time")`
      [PA-3; raised before the gate].
   2. `with self._gate.hold(): return self._run(now, request_id, session_id, role)` [`ResetAlreadyRunning` propagates
      to the caller untouched: CON-9 maps it to 409; the gate is released on every exit, PA-1].
   3. `_run(self, now: datetime, request_id: RequestId, session_id: LoginSessionId | None, role: DemoRole | None)
      -> ResetDone | ResetFailed`:
      ```python
      label, date_label = self._format_clock(DEMO_START)        # before any write: nothing fallible after commit
      clock = ResetClock(now=DEMO_START, label=label, date_label=date_label)
      reset_id = str(uuid.uuid4())
      step = "begin"
      committed = False
      opened = roles = 0
      try:
          with self._uow(write=True, exclusive=True) as tx, self._clear_checkpoints():
              before = tx.cases.demo_state.get().demo_now                      # pre-reset demo time for event `at`
              step = "restore"
              self._restore(tx)
              step = "clear"
              cleared = tx.core.reset.clear_demo_tables(reset_id, ended_at=now)
              step = "demo_state"
              tx.cases.demo_state.reset()
              step = "demo_reset_events"
              line = TEXTS[TextId.DEMO_RESET]
              for tid in cleared.open_threads:
                  tx.core.events.append(thread_stream(tid), StreamEvent(type="demo_reset",
                      payload={"speaker": {"kind": "event", "display_name": None}, "line": line}, at=before))
              for ref in cleared.case_streams:
                  tx.core.events.append(case_stream(ref), StreamEvent(type="demo_reset", payload={"line": line}, at=before))
              step = "seed"
              n = self._seed(tx)
              step = "records"
              opened, roles = len(cleared.open_threads), cleared.roles_reset
              tx.cases.records.reset_event(ResetEventRow(reset_id=reset_id, at_wall=now, asked_by_role=role,
                  asked_by_session=str(session_id) if session_id is not None else None, request_id=str(request_id),
                  restored=dict(cleared.rows_cleared), open_chats_ended=opened, roles_reset=roles,
                  checkpoints_cleared=True))
              tx.cases.records.seed_event(SeedEventRow(seed_event_id=str(uuid.uuid4()), at_wall=now,
                  reset_id=reset_id, seed_count=n))
              step = "commit"
              tx.commit()
              committed = True                                       # meridian is final from here
      except Exception as exc:
          if not committed:
              _log.warning("demo reset failed", extra={"reset_id": reset_id, "step": step,
                                                        "error_kind": type(exc).__name__})
              return ResetFailed()
          self._mark_checkpoints_not_cleared(reset_id, exc)          # residual window (AC-3)
      return ResetDone(open_chats_ended=opened, roles_reset=roles, clock=clock)
      ```
      Invariants:
      - (a) Both files roll back on any exception before `tx.commit()`: the `with` exits the checkpoint context with
        the exception → ROLLBACK, then the uow → ROLLBACK.
      - (b) `committed` is set only after the meridian COMMIT returned, so an exception in the checkpoint context's
        exit is the only way into the residual branch.
      - (c) The exception message is never logged (IDs only), and there is no traceback (`warning`, not `exception`).
   4. `_mark_checkpoints_not_cleared(self, reset_id: str, exc: Exception) -> None`:
      - `_log.warning("demo reset: checkpoint clear did not commit", extra={"reset_id": reset_id, "error_kind": type(exc).__name__})`.
      - Then `try:` `with self._uow(write=True) as tx: tx.cases.records.set_checkpoints_cleared(reset_id, False);
        tx.commit()`.
      - `except Exception as e2:` `_log.warning("demo reset: could not record checkpoints_cleared",
        extra={"reset_id": reset_id, "error_kind": type(e2).__name__})`.

      It returns nothing, and the reset still answers `ResetDone`: the meridian side is complete, and the stale
      checkpoints belong to tombstoned, unreachable threads that the next prune or reset removes.
9. Check: `uv run ruff check src/meridian/services/reset.py && uv run ruff format --check src/meridian/services/reset.py
   && uv run mypy src/meridian/services/reset.py`. Keep the file ≤ 600 lines (service cap, `code-structure.md`);
   expected ~380.

### Step 2 — `tests/services/reset_support.py` (helpers; §7.1 lists them)

Write the helpers of §7.1 first, then the tests that use them. No `test_` functions in this module.

### Step 3 — `tests/services/test_reset.py`

Write the tests of §7.1 in the order listed; run `uv run pytest tests/services/test_reset.py -q` after each group.

### Step 4 — `register_reset` hunk in `src/meridian/web/container.py` (body and docstring only)

The stub on `main` (line ~225) is:

```python
def register_reset(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-31 reset: ResetService and the demo seed (cases.md §7).

    No-op until AEA-31 fills it.
    """
```

Replace it with exactly this:

```python
def register_reset(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-31 reset: ResetService and the demo seed (cases.md §7).

    Binds the reset service (restore and checkpoint clear from storage, the reset gate, the seed with AEA-29's
    BriefAssembler, AEA-30's format_clock) and loads the demo seed once at first boot. An app create_app did not build
    has no web shell, so this does nothing.
    """
    import functools
    import importlib

    from meridian.services.reset import ResetService, seed_demo, seed_first_boot
    from meridian.web.deps import RESET_GATE, RESET_SERVICE, UOW_FACTORY, WALL_CLOCK
    from meridian.web.middleware import WebShellState

    shell = getattr(app.state, "web_shell", None)
    if not isinstance(shell, WebShellState):
        return

    def sibling(module: str, name: str) -> Any:
        # Same-wave siblings (AEA-29, AEA-30), resolved when the container builds, not at import (§8 R-1).
        return getattr(importlib.import_module(module), name)

    def seed() -> Callable[[Any], int]:
        return functools.partial(seed_demo, assembler=sibling("meridian.services.handoff", "BriefAssembler")())

    def build(c: Container) -> ResetService:
        checkpointer = c.get(Key[Any]("checkpointer"))
        return ResetService(
            c.get(UOW_FACTORY),
            c.get(RESET_GATE),
            c.get(Key[Any]("restore_working_copy")),
            checkpointer.clearing,
            seed(),
            format_clock=sibling("meridian.services.demo", "format_clock"),
        )

    container.provide(RESET_SERVICE, build)
    container.on_start(lambda: seed_first_boot(container.get(UOW_FACTORY), seed(), container.get(WALL_CLOCK)()))
```

Notes:
- Key names: `"checkpointer"` and `"restore_working_copy"` are AEA-10's (its step 9). If AEA-10 exported key
  constants (`grep -n "Key\[" src/meridian/web/container.py src/meridian/web/deps.py`), import and use those instead;
  equal names are equal keys either way. `UOW_FACTORY`, `RESET_GATE`, `WALL_CLOCK`, `RESET_SERVICE` are AEA-23's.
- `on_start` takes `Callable[[], None]`; the lambda returns an `int`. If mypy rejects it, wrap it in a nested
  `def first_boot() -> None: seed_first_boot(...)` and pass `first_boot`.
- Keep the first docstring line and the token `AEA-31` (AEA-01's test checks it). Remove the "No-op until" sentence.
- `Callable` and `Any` are already imported at module level in `container.py`; `Key` and `Container` are defined there.
  Add **no** module-level import (AEA-01's `test_container_imports_only_policy_limits`).
- Check: `uv run pytest tests/unit/web/test_container.py tests/unit/test_import_direction.py tests/unit/web/test_register_reset.py -q`.

### Step 5 — journey step and record (AC-14)

Write `tests/journeys/j8/test_aea_31.py` (§7.1) and run `uv run pytest -m journey tests/journeys/j8/test_aea_31.py -q`.
Write `docs/testing/journeys/<run-date>-AEA-31.md` with the `integrated-journeys.md` §4 fields (§7.4 gives the values;
copy the table layout of `docs/testing/journeys/2026-10-21-AEA-02.md`).

### Step 6 — context docs (AC-15), after the code commit (so the SHA exists)

- `.claude/reference/area-map.md`, A6 row (line ~31), Status cell:
  - change `planned` to `partly built: services/reset.py actual (AEA-31, \`<sha>\`), incl. the demo seed loader (seed
    list: stage7/cases.md §7); the rest planned`.
  - If another A6 ticket already changed the cell, insert your clause after theirs, separated with `; `.
  - Change nothing else in the file.
- `.claude/state/icm-progress.md`: add one row directly below the last *Routes verified against code and tests* row
  (≤ 400 characters; `<n>` from your run):
  `| Routes verified against code and tests | provisional | 2026-10-21: area map A6 → \`services/reset.py\` checked against \`tests/services/test_reset.py\` (AEA-31, \`<sha>\`; <n> pass) | Integrated level when AEA-43, AEA-50, AEA-52, AEA-57 land |`
- `docs/design/code-design.md`:
  - (a) §3 tree line `│   ├── reset.py                                 all-or-nothing reset; injected restore/clear callables      A6    1`:
    append `   built AEA-31 <sha>` (same style as line 206, `privacy/redact.py … built AEA-04 9145044`).
  - (b) §4 row `| \`services/reset.py\` | Restore the demo all-or-nothing. | …`: in the second cell, after "Restore the
    demo all-or-nothing.", append ` Also holds the demo seed loader (\`seed_demo\`, \`seed_first_boot\`); the seed list is stage7/cases.md §7. Built (AEA-31, \`<sha>\`).`
  - No other edit.

### Step 7 — gates, then commits

Run §7.3 in order (stop at the first red). Then:
1. Code commit:
   `git add src/meridian/services/reset.py src/meridian/web/container.py tests/services/reset_support.py tests/services/test_reset.py tests/unit/web/test_register_reset.py tests/journeys/j8/test_aea_31.py`
   → commit `feat(reset): all-or-nothing demo reset and demo seed (AEA-31)` with a body listing AC-1…AC-14 and PA-1…PA-4.
2. Step 6 edits + the journey record:
   `git add docs/testing/journeys/<run-date>-AEA-31.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`
   → commit `docs(AEA-31): journey record and context rows for services/reset.py`.

Each message ends with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Commit on your branch
only; do not push.

---

## 6. Data and fixtures

All values are issued (scheduling DB, read-only) or fictional; nothing is model-written. Re-checked against the issued
file on 2026-10-21 (`mode=ro&immutable=1`):
- MHC-94339 (Pflugerville, tier none), MHC-39394 (Leander, tier none) and MHC-10002 (Kyle) exist.
- INV-200037 belongs to MHC-94339: paid, line "Condensate drain clearing", issued 2026-08-28.
- INV-204411 belongs to MHC-10002: unpaid, line "After-hours dispatch" of 14400 cents.
- MHC-10002's phone ends in `02`.
- The appointments max id is 159, and slot 56 is `open` on 2026-10-19.
- No issued table uses AUTOINCREMENT.

### 6.1 The seed table (`SEED_CASES`) — copy exactly

| Field | MHC-C-0005 | MHC-C-0006 | MHC-C-0007 | MHC-C-0008 |
|---|---|---|---|---|
| reason | `HandoffReason.REFUND` | `HandoffReason.COMPLAINT_OR_MANAGER` | `HandoffReason.BILLING_DISPUTE` | `HandoffReason.SAFETY` |
| rule_id / trigger | `"R24.refund"` / `"escalation"` | `"R24.complaint_or_manager"` / `"escalation"` | `"R24.billing_dispute"` / `"escalation"` | `"R5.gas"` / `"safety"` |
| safety_kind | None | None | None | `SafetyKind.GAS` |
| customer_id | `"MHC-94339"` | `"MHC-39394"` | `"MHC-10002"` | None (unmatched caller) |
| invoice_id | `"INV-200037"` | None | `"INV-204411"` | None |
| created_at (Chicago) | `datetime(2026, 10, 13, 10, 0, tzinfo=CHICAGO)` | `datetime(2026, 10, 16, 9, 14, tzinfo=CHICAGO)` | `datetime(2026, 10, 16, 9, 24, tzinfo=CHICAGO)` | `datetime(2026, 10, 16, 9, 56, tzinfo=CHICAGO)` |
| outcome / alert | `"handed_off"` / None | `"handed_off"` / None | `"handed_off"` / None | `"safety_reply"` / `"supervisor_now"` |
| messages | `"I paid invoice INV-200037 for a condensate drain clearing in August, and the leak came back two weeks later."`, `"I would like a refund for that repair."` | `"The technician who came to my house last month was rude to my mother and left before the job was finished."`, `"I want to talk to a manager about how we were treated."` | `"My invoice INV-204411 has a $144.00 after-hours dispatch charge on it."`, `"Nobody told me the visit would be after hours, and I want that charge taken off."` | `"I smell gas near my furnace."` (issued line SAF-GAS) |
| needs | `"I would like a refund for that repair"` | `"I want to talk to a manager about how we were treated"` | `"I want that charge taken off"` | `"I smell gas near my furnace"` |
| claims | `"the leak came back two weeks later"` | `"was rude to my mother"`, `"left before the job was finished"` | `"Nobody told me the visit would be after hours"` | (none) |
| open_decision | `"Decide whether INV-200037 gets a refund or a free return visit for the leak."` | `"Decide who calls the customer back about the technician's conduct, and what to offer."` | `"Decide whether to remove or reduce the after-hours dispatch charge on INV-204411."` | `"Call back to confirm the customer is safe and arrange an emergency visit."` |
| followup_window | None | None | `"morning"` | None |

The two customers not named in the ticket (MHC-94339, MHC-39394) are issued customers outside MHC-10001…10004 and
MHC-57204, as the ticket requires; `SEED_CASES` is "the seed file" the ticket mentions.

Expected derived values (from AEA-14's rules; assert them in tests):
- **Promises:** 0005 is `R26.refund`, due Thu 2026-10-15 19:00 Chicago (Tue + 2 business days). 0006 and 0007 are
  `R26.unstaffed`, due Mon 2026-10-19 19:00. 0008 is `R26.safety_none`, due None.
- **Priorities:** P3, P3, P3, P0. The case due equals the promise due.
- **Follow-up:** MHC-10002's phone ends in `02`, so the label is `"the number ending in 02"` and the saved line is
  `"Follow-up saved: phone call, the number ending in 02, mornings."`.
- **At `DEMO_START` (Fri 10:00):** 0006 is 46 min old and 0007 is 36 min old (both ≥ `UNOWNED_AFTER`); 0005's due is
  past; 0008 is P0.

### 6.2 Test data (built in `reset_support.py` at run time)

- Store: `temp_sqlite()`; checkpointer: `Checkpointer(store.data_dir / CHECKPOINTS_DB_NAME)` (closed in the fixture).
- Wall clock: `WALL = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)` (a fixed aware UTC time; `from datetime import UTC`).
- IDs: `uuid4()` at run time. Hashes: `uuid4().hex`. Never a code-shaped or card-shaped literal.
- "Dirty demo" (`make_dirty_demo`, the ticket's example pair). It builds, in order:
  - seeds loaded first (`seed_first_boot`);
  - a booking by raw SQL through `tx.connection`: `UPDATE appointment_slots SET status='booked' WHERE slot_id=56`,
    then `INSERT INTO appointments (slot_id, customer_id, issue_description, created_at) VALUES (56, 'MHC-10004',
    'synthetic', '2026-10-16')` (`status` defaults to `scheduled`);
  - open live chats;
  - case MHC-C-0009 with a promise and a `case_changed` event on its case stream;
  - identity, inbox and code rows;
  - staff sessions and a flag;
  - an advanced clock and staffing;
  - kept-table rows;
  - two checkpoints per open chat.

  Exact SQL columns are AEA-10's DDL (`40_identity.sql`, `90_staff.sql`, `20_spend.sql`, `95_ops.sql`); read them from
  the merged files.

---

## 7. Checks

### 7.1 Tests the implementer writes (with the code)

**Lint and type rules that bite test code here** (ruff selects `E, W, F, I, B, UP, S, RUF`; `tests/**` ignores only
`S101, S105, S106, S603, S607, S311`; mypy is `strict` over `tests/` with untyped defs allowed):
- Define injections and doubles as nested `def`s. Never assign a lambda to a name (E731).
- f-string SQL over table names read from `sqlite_master` needs `# noqa: S608` on that line, with a trailing comment
  saying the names come from `sqlite_master`. Parametrise every value with `?`.
- Set attributes on a fake module with `monkeypatch.setattr(mod, "Name", value, raising=False)`, not `mod.Name = …` or
  `setattr(mod, "Name", …)` (mypy attr error / B010).
- Pass a non-`Settings` settings object as `cast(Any, types.SimpleNamespace())`.

**`tests/services/reset_support.py`** (helpers; imported as `from tests.services.reset_support import …`)

- `CHICAGO`, `WALL`, and a function `new_request_id() -> RequestId` (`RequestId(str(uuid4()))` per call).
- `@contextmanager def demo_store() -> Iterator[tuple[TempStore, Checkpointer]]`: `temp_sqlite()` + a `Checkpointer`;
  closes it on exit.
- `class RecordingAssembler`:
  - `__init__(self, staff_guidance: object = None)` (so the container can call it like `BriefAssembler()`).
  - `assemble(case, state, lookups)` records `(case, state, tuple(lookups))` and returns
    `fake_brief(case.case_ref, state.thread_id, case.created_at)`.
  - `attach_extraction(brief, extraction, check)` records `extraction` and `check`, and returns
    `brief.model_copy(update={"status": "ready"})`.
- `fake_brief` builds a valid `Brief` with 8 headings from `BRIEF_TITLES`, `BRIEF_KEYS`, `BRIEF_ORIGINS`
  (`meridian.domain.handoff`):
  - `number=i + 1`, empty `items=()`, `trimmed=False`, `trim_note=None`, `not_generated=False`;
  - heading 4 `checked=False`, the others `checked=True`;
  - status `"being_written"`.
- `def fake_format_clock(dt: datetime) -> tuple[str, str]`: `(f"label {dt.isoformat()}", f"date {dt.date().isoformat()}")`.
- `def seed_fn(assembler: RecordingAssembler | None = None) -> Callable[[UnitOfWork], int]`:
  `functools.partial(seed_demo, assembler=assembler or RecordingAssembler())`.
- `def make_service(store, cp, *, gate=None, restore=None, clearing=None, seed=None) -> tuple[ResetService, ResetGate]`.
  Defaults: `ResetGate()`, `functools.partial(restore_working_copy, issued_path=store.issued_path)`, `cp.clearing`,
  `seed_fn()`, and `format_clock=fake_format_clock`.
- `def login_session(role: DemoRole) -> LoginSession`: session id `LoginSessionId(str(uuid4()))`, `role_reset=False`,
  `signed_in_at=DEMO_START`, `expires_at=WALL + timedelta(hours=12)`.
- `@dataclass class Dirty`: `open_threads: list[ThreadId]`, `sessions: dict[str, LoginSession]` (keys `customer`,
  `representative`, `supervisor`), `case_ref: CaseRef`, `max_event_id: int`.
- `def make_dirty_demo(store, cp, *, open_chats: int = 1, customer_message: str = "Hi, my AC is making a noise.") -> Dirty`:
  1. `seed_first_boot(store.uow, seed_fn(), WALL)` (its own uow).
  2. In one `with store.uow(write=True) as tx:`:
     - the booking SQL (§6.2);
     - `open_chats` live conversations: `ConversationRow(thread_id=ThreadId(str(uuid4())),
       demo_session=str(sessions["customer"].session_id), run_tag="live", agent_version="test",
       started_at=DEMO_START)`, each with a greeting (`"assistant"`) and one `"customer"` message
       (`customer_message`, `turn_id=<uuid4>`, `kind="text"`);
     - on the first chat, a case `tx.cases.refs.next_case_ref()` (= MHC-C-0009) with `REFUND`/P3/`"R24.refund"`/
       `"escalation"`/`"unassigned"`, `created_at=updated_at=DEMO_START`, its
       `promise_for(HandoffReason.REFUND, "nobody_online", DEMO_START)` inserted with `promises.insert`, and
       `tx.core.events.append(case_stream(ref), StreamEvent(type="case_changed", payload={}, at=DEMO_START))`;
     - raw SQL rows, with columns from the merged DDL:
       - `identity_threads`: the first chat, status `code_sent`, customer `MHC-10004`, `updated_at` an ISO wall time;
       - `identity_codes`: `code_hmac=uuid4().hex`, `held_by='demo_inbox'`, `tries_left=3`, `inbox_message_id=1`,
         ISO times;
       - `demo_inbox`: `to_masked='e***@example.com'`;
       - three `staff_sessions` rows with roles `customer`, `representative`, `supervisor`, using each
         `LoginSession`'s `session_id`, `token_hash=uuid4().hex` and `role_reset_pending=0`;
       - one `flags` row (`status='new'`);
       - one row each in `spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`,
         `job_runs` and `demo_events`;
       - a prior `reset_events` row and a prior `ended_threads` row (synthetic ids).
     - `tx.cases.demo_state.set_now(datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO))` and
       `tx.cases.demo_state.set_staffing("simulated_on_shift")`;
     - `tx.commit()`.
  3. Two checkpoints per open chat:
     `cp.saver.put({"configurable": {"thread_id": tid, "checkpoint_ns": ""}}, empty_checkpoint(), {"source": "loop", "step": i, "parents": {}}, {})`
     (`from langgraph.checkpoint.base import empty_checkpoint`; reuse AEA-10's `tests/unit/adapters/test_checkpointer.py`
     call if the API differs).
  4. Record `max_event_id = SELECT MAX(id) FROM events`.
- `def snapshot(store, cp) -> dict[str, list[tuple[object, ...]]]`:
  - for each of the two files (`store.db_path`, `cp.path`), open `sqlite3.connect(path)`;
  - read every table in `sqlite_master` (type `table`, sorted, incl. `sqlite_sequence`) with
    `SELECT * FROM "<t>" ORDER BY rowid`;
  - key each result `"<file>:<table>"`; close the connections.
- `def rows(path, sql, params=()) -> list[tuple[Any, ...]]` and `def count(path, table) -> int` (raw read-only helpers).
- `def issued_rows(issued_path, table)`: through `sqlite3.connect(f"{issued_path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)`.
- `def sha256_file(path) -> str`.

**`tests/services/test_reset.py`** (no `print` of values; IDs and counts only)

| # | Test | Setup | Assertions |
|---|---|---|---|
| 1 | `test_reset_restores_working_copy` (AC-1) | `demo_store()`; `h0 = sha256_file(store.issued_path)`; `make_dirty_demo`; reset (role supervisor) | `ResetDone`; each of the five tables `SELECT * ORDER BY rowid` equals `issued_rows`; for each issued table, the copy's `sqlite_sequence` row equals the issued file's (issued has none → copy has none); in a write uow `INSERT INTO appointments (slot_id, customer_id, created_at) VALUES (1, 'MHC-10004', '2026-10-16')` → `lastrowid == max(issued appointment_id) + 1` (160), then leave without commit; `sha256_file(issued) == h0` |
| 2 | `test_reset_all_or_nothing` (AC-2, PA-1), parametrised `step` ∈ `restore`, `clear_demo_tables`, `demo_state_reset`, `demo_reset_append`, `seed_demo`, `reset_event`, `seed_event`, `commit` | `make_dirty_demo`; build the injection for `step` (below); `before = snapshot(...)` | `result == ResetFailed()` (`code == "RESET_FAILED"`); `snapshot(...) == before` (meridian **and** checkpoint tables, incl. `sqlite_sequence`); `gate.held() is False`; then `monkeypatch.undo()` and a second reset with the defaults returns `ResetDone` |
| 3 | `test_checkpoint_commit_failure_residual_window` (AC-3) | `make_dirty_demo`; `clearing` = a `@contextmanager` that `yield`s then `raise RuntimeError("checkpoint commit failed")` (deletes nothing) | `ResetDone`; `reset_events` newest row `checkpoints_cleared == 0`; MHC-C-0009 gone, seeds present, five issued tables equal the issued file, `demo_state` default; every `thread_id` left in `checkpoints` is in `ended_threads`; `gate.held() is False` |
| 4 | `test_concurrent_reset_refused` (AC-4) | seed double: `def blocking(tx): started.set(); release.wait(10); return seed_fn()(tx)`; T1 = `threading.Thread` running `svc.reset(...)` and storing its result | after `started.wait(5)`: `pytest.raises(ResetAlreadyRunning)` on a second `svc.reset(...)`; `release.set()`; `T1.join(10)`; T1 result is `ResetDone`; exactly **one** new `reset_events` row |
| 5 | `test_writer_waits_for_reset_lock` (AC-4) | same blocking seed; T1 reset; T2 = writer `with store.uow(write=True) as tx: tx.core.conversations.insert(<new live row W>); tx.commit()` then `done.set()` | after `started.wait(5)`, start T2, `time.sleep(0.5)`: `done.is_set() is False`; `release.set()`; join both (10 s); W's `lookup` is a `ConversationRow` (not a tombstone, not missing); the reset's `reset_events` row exists; record `time.monotonic()` at T1 return and at `done.set()` and assert reset ≤ writer |
| 6 | `test_reset_ends_open_chats` (AC-5) | `make_dirty_demo(open_chats=2)` | `done.open_chats_ended == 2`, `done.roles_reset == 2`; for each open thread exactly one `events` row `type='demo_reset'` on its stream (`stream = str(thread_id)`), payload `{"speaker": {"kind": "event", "display_name": None}, "line": TEXTS[TextId.DEMO_RESET]}`, `id > dirty.max_event_id`; one `demo_reset` on `case:MHC-C-0009` with payload `{"line": …}`; no `demo_reset` on any seed thread stream; `tx.core.conversations.lookup(old)` is `EndedThread` with `reason == "demo_reset"` and `reset_id` == the stored `reset_events.reset_id` |
| 7 | `test_ended_thread_answers_session_ended` (AC-6) | minimal `FastAPI()`; `app.add_exception_handler(ApiProblem, handle_api_problem)`; route `@app.get("/t/{thread_id}") def r(thread_id: ThreadId = Depends(owned_thread)) -> dict[str, str]: return {"ok": "yes"}`; `app.dependency_overrides[get_uow_factory] = lambda: store.uow`; `app.dependency_overrides[get_login_session]` = a nested `def` returning `holder["session"]` (a mutable dict switched per call); `TestClient(app)` | before reset, owner session → 200; after reset: owner session → 410, body `error.code == "SESSION_ENDED"`, `error.details == {"reason": "demo_reset"}`; another session → 404 `SESSION_NOT_FOUND`; its body minus `request_id` equals the body for an unknown thread id (`str(uuid4())`) minus `request_id` |
| 8 | `test_reset_restores_clock_and_staffing` (AC-7) | `make_dirty_demo` (clock Mon 07:00, on shift) | `tx.cases.demo_state.get().demo_now == DEMO_START` (aware instants compare equal across zones) and `.staffing == "nobody_online"`; `done.clock == ResetClock(now=DEMO_START, label=fake_format_clock(DEMO_START)[0], date_label=fake_format_clock(DEMO_START)[1])` |
| 9 | `test_reset_clears_codes_keeps_ops_records` (AC-8) | `make_dirty_demo`; counts before; `convs = count(conversations)` | `identity_codes`, `demo_inbox`, `identity_threads`, `flags` count 0; each of `spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`, `job_runs`, `demo_events` count unchanged; `reset_events` +1, `seed_events` +1, `ended_threads` + `convs`; `staff_sessions`: 3 rows, all `role='customer'`, the two staff rows `role_reset_pending=1` |
| 10 | `test_seed_cases_labelled_and_counted` (AC-9) | fresh store; `rec = RecordingAssembler()`; `with store.uow(write=True) as tx: n = seed_demo(tx, assembler=rec); tx.commit()` | `n == 4 == SEED_COUNT`; `SELECT case_ref FROM cases ORDER BY case_ref` == the four refs, all `seed=1`, `lifecycle='unassigned'`; each case's conversation `run_tag='seed'`, `live_state='closed'`, `demo_session == SEED_DEMO_SESSION`; every `created_at < DEMO_START`; one promise and one `case_briefs` row per case (`tx.cases.briefs.get(ref)` equals the double's output); `lookup_log` rows: 0005 → `("INV-200037",)`, 0007 → `("INV-204411",)`, none for 0006/0008, `tool == "read_invoices"`; follow-up only on 0007 (`channel='phone'`, `contact_window='morning'`, `on_record=1`, `destination IS NULL`, label ends with the last two digits of MHC-10002's phone read from the DB); `rec` saw 4 `attach_extraction` calls with `check is None`, and every quote's `message_id` is a `role='customer'` message of that case's thread whose text contains `quote.text` |
| 11 | `test_seed_promises_from_table` (AC-9) | first `demo_state.set_now(datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO))` and commit, then seed | for each seed, `tx.cases.promises.current(ref).promise == promise_for(seed.reason, "nobody_online", seed.created_at)` and `cases.due_at == case_due_at(...)`; 0005 due == `datetime(2026, 10, 15, 19, 0, tzinfo=CHICAGO)`; 0006, 0007 due == Mon 10-19 19:00; 0008 due None; priorities P3, P3, P3, P0 (the advanced clock changed nothing) |
| 12 | `test_first_boot_seeds_once` (AC-9) | fresh store; `seed_first_boot(store.uow, seed_fn(), WALL)` twice | first returns 4, second 0; counts of `cases`, `conversations`, `messages`, `seed_events` unchanged by the second call; the one `seed_events` row has `reset_id IS NULL`, `seed_count=4`, `label='demo seed'` |
| 13 | `test_next_live_ref_after_seeds` (AC-9) | seed; then a dirty demo + reset | `tx.cases.refs.next_case_ref() == "MHC-C-0009"` after seeding and again after the reset |
| 14 | `test_seed_lanes_at_demo_start` (AC-10) | seed | Test-local `lane_for(case: CaseRow, now) -> str \| None` implementing cases.md §5's rules, in this order: `"p0_p1"` if priority is P0 or P1; elif `due` and `due < now` → `"overdue"`; elif `due` and `due - now <= DUE_SOON_WINDOW` → `"due_soon"`; elif lifecycle is `unassigned` and `now - created_at >= UNOWNED_AFTER` → `"unowned"`; elif `wake_up` and `wake_up < now` → `"stuck_waiting"`; else None. Rows come from `tx.cases.cases.get(ref)`. At `DEMO_START`: 0008 `p0_p1`, 0005 `overdue`, 0006 and 0007 `unowned`; 0007's follow-up is phone + morning. (Docstring: replace by `CaseService.oversight` when AEA-29 is on main — AEA-52's job, not this ticket's.) |
| 15 | `test_seed_holds_no_codes_or_cards` (AC-11) | seed | Read, as `str`, every column of every row of: `conversations` (seed), `messages`, `lookup_log`, `cases` (`seed=1`), `promises`, `followups`, `case_briefs`, and `actions` of the seed threads. First remove canonical UUIDs with `re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "", text)` (they are ids, not codes). Then assert: no match of `re.compile(r"[0-9]{13,19}")`; no match of `re.compile(r"(?<![0-9A-Za-z-])[0-9]{6}(?![0-9])")` (excludes `INV-204411`); every non-NULL seeded `cases.customer_id` is in `issued_rows(…, "customers")`; every stored customer message and every quote text of a seed equals or is contained in a `SEED_CASES` constant (no model-written text) |
| 16 | `test_reset_and_seed_events` (AC-12) | dirty demo; reset with `session_id=sup.session_id, role=DemoRole.SUPERVISOR`; then a second reset with `session_id=None, role=None` | raw `reset_events` rows: the first has `asked_by_role='supervisor'`, `asked_by_session == str(sup.session_id)`, `request_id` as passed, `restored_json` parses to a dict of table → int including `conversations`, `open_chats_ended=1`, `roles_reset=2`, `checkpoints_cleared=1`, `at_wall` ends with `+00:00`; the second has `asked_by_role IS NULL AND asked_by_session IS NULL`; `seed_events`: one with `reset_id IS NULL` (first boot) and one per reset with that `reset_id`, `seed_count=4`, `label='demo seed'` |
| 17 | `test_reset_records_hold_no_pii` (AC-13) | read MHC-10002's `name`, `phone` from the issued DB; `token = secrets.token_urlsafe(16)`; dirty demo with `customer_message=f"This is {name}, call me on {phone}"`; one extra `staff_sessions` row with `token_hash = hashlib.sha256(token.encode()).hexdigest()` | for both newest rows (`reset_events`, `seed_events`): `"\|".join(str(v) for v in row)` contains neither `name.split()[0]`, `phone`, the phone's digits only, `token`, nor the customer message text |
| 18 | `test_reset_module_imports_no_adapter_callables` (PA-2) | AST of `src/meridian/services/reset.py` | no import of `sqlite3`, `meridian.adapters.sqlite.db`, `meridian.adapters.sqlite.migrate`, `meridian.adapters.checkpointer`, `meridian.web*`, `meridian.agent*`, `meridian.services.handoff`, `meridian.services.demo`, `anthropic`, `httpx`; no string constant matching `(?i)\b(SELECT\|INSERT\|UPDATE\|DELETE)\b\s`; no call whose function is the attribute `now` of a name `datetime` (`datetime.now`) |
| 19 | `test_reset_rejects_naive_now` (PA-3) | service with a fresh gate | `pytest.raises(ValueError)` for `datetime(2026, 10, 21, 19, 0)`; `gate.held() is False`; no new `reset_events` row |

Injections for test 2 are each defined inside the test as nested `def`s, never assigned lambdas. Read the classes from
a probe uow: `with store.uow() as tx:`.

| step | injection |
|---|---|
| `restore` | `def restore(tx): real_restore(tx); raise _Boom` — runs the real restore, then raises |
| `clear_demo_tables` | `monkeypatch.setattr(type(tx.core.reset), "clear_demo_tables", after(orig))`, where `after(orig)` returns `def wrapped(self, *a, **k): orig(self, *a, **k); raise _Boom` |
| `demo_state_reset` | same pattern on `type(tx.cases.demo_state)`, attribute `"reset"` |
| `demo_reset_append` | same on `type(tx.core.events)`, attribute `"append"`, raising only when `event.type == "demo_reset"` (after the original call) |
| `seed_demo` | seed double: `def seed(tx): seed_fn()(tx); raise _Boom` |
| `reset_event` | same pattern on `type(tx.cases.records)`, attribute `"reset_event"` |
| `seed_event` | same pattern on `type(tx.cases.records)`, attribute `"seed_event"` |
| `commit` | `def boom_commit(self): raise _Boom`; `monkeypatch.setattr(type(tx), "commit", boom_commit)` (does **not** call the original) |

`class _Boom(Exception)` is test-local. Apply class patches **after** `make_dirty_demo` (which commits) and before
`snapshot`.

**`tests/unit/web/test_register_reset.py`** (PA-4)

- `test_register_reset_binds_service_and_seeds_first_boot`:
  1. Open `demo_store()`.
  2. Fake the two sibling modules (the hunk resolves them through `importlib`):
     - `fake_handoff = types.ModuleType("meridian.services.handoff")` with
       `monkeypatch.setattr(fake_handoff, "BriefAssembler", RecordingAssembler, raising=False)`;
     - `fake_demo = types.ModuleType("meridian.services.demo")` with `format_clock = fake_format_clock` set the same
       way;
     - `monkeypatch.setitem(sys.modules, …)` for both.
  3. Build the container and app:
     - `settings = cast(Any, types.SimpleNamespace())`; `c = Container(settings=settings, limits=Limits())`;
       `app = FastAPI()`;
     - `app.state.web_shell = WebShellState(settings=settings, wall_clock=lambda: WALL, public_paths=PublicPaths())`.
  4. Provide the keys this hunk reads:
     - `c.provide(UOW_FACTORY, lambda _c: store.uow)`;
     - `c.provide(Key[Any]("checkpointer"), lambda _c: cp)`;
     - `c.provide(Key[Any]("restore_working_copy"), lambda _c: functools.partial(restore_working_copy, issued_path=store.issued_path))`;
     - `c.provide(RESET_GATE, lambda _c: ResetGate())`;
     - `c.provide(WALL_CLOCK, lambda _c: lambda: WALL)`.

     (Lambdas passed as arguments are fine; E731 only flags assignment.)
  5. `register_reset(c, app, settings=settings, limits=c.limits)`; `c.build()`.
  6. Assert:
     - `isinstance(c.get(RESET_SERVICE), ResetService)`;
     - 4 seed cases and one `seed_events` row with `reset_id IS NULL`;
     - `c.get(RESET_SERVICE).reset(WALL, request_id=new_request_id(), session_id=None, role=None)` is a `ResetDone`.
  7. Build a **second** container the same way on the same store: still one first-boot `seed_events` row (no second
     seed).
  8. Close both containers. Do not close `cp` in a container closer; `demo_store()` closes it.
- `test_register_reset_skips_bare_app`: fresh `Container`; `register_reset(c, FastAPI(), settings=…, limits=…)`;
  `c.build()`; `c._factories == {}` and `c._starters == []`.

**`tests/journeys/j8/test_aea_31.py`** (AC-14; `pytestmark = pytest.mark.journey`)

Module docstring: "J-8 (proposed extension, slice plan §0a): a demo reset from one client. Level today: mock-tested
(real ResetService, real AEA-23 owned_thread and require_staff on a minimal FastAPI app over a temp SQLite copy; no
server, no login, a StaffAccess double that reads the stored role_reset_pending flag). Integrated level blocked by
AEA-57 (harness) and AEA-52 (J-8)."

`test_j8_reset_ends_chat_resets_roles_restores_tables`:

1. **Setup.** `demo_store()`; `dirty = make_dirty_demo(store, cp)`; `svc, _ = make_service(store, cp)`.
   - Logins: `rep = dirty.sessions["representative"]` (login L1), `sup = dirty.sessions["supervisor"]` (login L2),
     `cust = dirty.sessions["customer"]` (owner of the open chat).
   - **Clients:** client A and client B are two tabs on login L1 (both send header `X-Test-Session: <L1 session id>`);
     client C is login L2.
2. **App.** `FastAPI()` with:
   - routes `GET /t/{thread_id}` (`Depends(owned_thread)`) and `GET /staff`
     (`Depends(require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR))`), each returning `{"ok": "yes"}`;
   - `app.add_exception_handler(ApiProblem, handle_api_problem)`.
3. **Overrides.**
   - `get_uow_factory` → `store.uow`.
   - `get_login_session` → a nested `def session_from_header(request: Request) -> LoginSession`. It reads header
     `X-Test-Session` and builds a `LoginSession` from that session's stored `staff_sessions` row:
     `role=DemoRole(row.role)`, `role_reset=bool(row.role_reset_pending)`, `signed_in_at=DEMO_START`,
     `expires_at=WALL + timedelta(hours=12)`.
   - `get_staff_access` → a double class with `actor_for(session, needs)` that returns:
     - `RoleRefusal(role=session.role, needs=needs, reason="role_reset")` when `session.role_reset`;
     - `RoleRefusal(role=session.role, needs=needs, reason="wrong_role")` when `session.role` is not one of `needs`
       (compare by `.value`);
     - otherwise `actor_for(StaffRole(session.role.value))`.
4. **Steps and assertions.**
   1. A, B and C `GET /staff` → 200.
   2. Client A calls `svc.reset(WALL, request_id=new_request_id(), session_id=rep.session_id,
      role=DemoRole.REPRESENTATIVE)` → `ResetDone` with `roles_reset == 2` and `open_chats_ended == 1`.
   3. A, B and C `GET /staff` → 403, `error.code == "ROLE_NOT_ALLOWED"`, `error.details.reason == "role_reset"`.
   4. The customer (`X-Test-Session: <cust id>`) `GET /t/<dirty.open_threads[0]>` → 410 `SESSION_ENDED`.
   5. The chat's stream (`stream = str(thread_id)`) has exactly one `demo_reset` event.
   6. The five issued tables equal the issued file.
   7. **Role switch on login L1.** Stand in for CON-10 with `UPDATE staff_sessions SET role='representative',
      role_reset_pending=0 WHERE session_id=?` for L1. Add a comment: "CON-10 `switchRole` is AEA-44's; this raw
      UPDATE stands in for it at mock level."
   8. A and B `GET /staff` → 200 (the role is per login, shared by both tabs); C still 403 `role_reset`.

The test may import `tests.services.reset_support`, so a change there selects J-8 in the affected-journeys command.

### 7.2 Existing tests that must stay green

- `tests/unit/web/test_container.py` (all) and `tests/unit/test_import_direction.py` (all).
- AEA-10's `tests/unit/adapters/` storage tests and `tests/unit/adapters/test_checkpointer.py`.
- AEA-23's `tests/unit/web/test_deps.py` and `tests/unit/web/test_reset_gate.py`.
- AEA-14's `tests/unit/policy/test_handoff*.py` (whatever names it merged).

Run the ones that import a module you changed:
`grep -rln "services.reset\b\|services import reset\|web.container\|web import container\|tests.services.reset_support" tests/`.

### 7.3 Gates (cheapest first; stop at the first red)

Run from `/home/linuxuser/workspaces/inno-aea-callcenter` with `export UV_LINK_MODE=hardlink`. `PY` below =
`src/meridian/services/reset.py src/meridian/web/container.py tests/services/reset_support.py tests/services/test_reset.py tests/unit/web/test_register_reset.py tests/journeys/j8/test_aea_31.py`.

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check $PY` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check $PY` | `6 files already formatted` |
| 3 | Type check | `uv run mypy` (project config: `src/meridian`, `tests`, `eval`) | `Success: no issues found` |
| 4 | Affected tests | `uv run pytest tests/services/test_reset.py tests/unit/web/ tests/unit/test_import_direction.py -q` plus any file the §7.2 grep adds | all pass; `test_reset_all_or_nothing` shows 8 parametrised passes |
| 5 | Journey step | `uv run pytest -m journey tests/journeys/j8/test_aea_31.py -q` | `1 passed` |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | selects every journey file present (a change under `tests/journeys/` selects all) and they pass |

While iterating, run only the file you are working on. pytest at most `-n 2` (`uv run --with pytest-xdist pytest -n 2 …`);
the threading tests are fine serially. **No full suite** here: `container.py` gains one hunk that nothing else imports,
and no shared fixture, setting or dependency changes (build-loop-test-scope).

### 7.4 Journey record values (`docs/testing/journeys/<run-date>-AEA-31.md`)

| Field | Value |
|---|---|
| Claim | AEA-31 `services/reset.py`: all-or-nothing reset and demo seed (AC-1…AC-13); J-8 reset step at mock level (two tabs on one login and a second login go to 403 `role_reset`; the chat ends with 410; issued tables restored) |
| Level | `mock-tested` |
| Tested revision | the code commit SHA |
| Environment | VPS, Python 3.12, `temp_sqlite()` copy of the issued DB, real `Checkpointer`, no server, no model; `BriefAssembler` and `format_clock` are doubles (AEA-29, AEA-30 same wave) |
| Command | the gate 4 and gate 5 commands |
| Result | pass counts from your run |
| Evidence location | this file; the implementer report |
| Remaining limitations | No CON-9 route (AEA-43), no operator script / CAP-9 (AEA-50), no real BriefAssembler or `CaseService.oversight` over the seeds (AEA-29, AEA-52); the role switch is a raw UPDATE standing in for CON-10 (AEA-44); seed threads have no `identity_threads` row (§8 R-6) |
| Blocked by | AEA-57 (journey harness), AEA-52 (J-8) for the journey; AEA-43, AEA-50 for the integrated entry points |

---

## 8. Risks and requests

- **R-1 · Merge order inside wave 2 (request to the orchestrator).**
  - `services/reset.py` and its tests need nothing from AEA-29 or AEA-30.
  - The `register_reset` hunk resolves `meridian.services.handoff.BriefAssembler` and
    `meridian.services.demo.format_clock` when a real app builds. It does this through `importlib`, so mypy and the
    hunk tests pass without them.
  - **Merge AEA-31 after AEA-29 and AEA-30**, or any real app start (AEA-57's journey harness) fails at container build
    with `ModuleNotFoundError`.
  - This is not a `blocked-on`: no file of this ticket imports them.
- **R-2 · `ResetService` gains one keyword-only argument `format_clock` (deviation from cases.md §7's constructor).**
  - The ticket calls for `format_clock` "injected" for `ResetDone.clock`; cases.md §7's constructor has no slot for it.
  - It is keyword-only and required. The only constructors are this ticket's hunk and AEA-50's `scripts/reset.py`
    (wave 3, reads the code).
  - **Request to AEA-50's planner:** pass `format_clock=meridian.services.demo.format_clock`.
  - **Request to the integrator:** note it in cases.md §7 at the next contract pass (no wire change, so no
    signed-contract stop).
- **R-3 · `ClockView` still has no owner.**
  - cases.md A-2 homes the demo view types in an "AEA-02 follow-up" that was never cut, and AEA-02 merged without them
    (checked on `main`). AEA-30's plan R-1 asks the orchestrator to cut that follow-up.
  - `ResetDone.clock` uses a local `ResetClock` with the OpenAPI `DemoClock` fields (`now`, `label`, `date_label`),
    unless a `domain/` `ClockView` with the same fields exists when you implement (step 0.4).
  - AEA-43 serialises either identically. When the follow-up lands later, the swap is one line.
- **R-4 · AEA-01's `test_every_register_stub_present`.**
  - It calls every hunk on a bare `FastAPI()` and asserts nothing is provided; the web-shell guard keeps it green.
  - AEA-10's plan (§8 R-13, wave 1, merged before this ticket) also inserts a two-line guard there that skips hunks
    whose docstring no longer says "No-op until", so a filled hunk passes either way.
  - If it nevertheless fails because of `register_reset`, do not edit it. Report "request: AEA-01 follow-up to exempt
    filled hunks" to the orchestrator.
- **R-5 · Seed threads stored `live_state='closed'`.**
  - Required so that `Cleared.open_threads` (AEA-10: `live_state <> 'closed'`) excludes them and the example pair's
    `open_chats_ended=1` holds, and so that AEA-30's `staffing_changed` / `clock_changed` fan-out skips them.
  - **Request to AEA-29:** the lifecycle × live-state `allowed_actions` table must give an `unassigned` case on a
    `closed` thread the same non-live actions as on `not_live` (claim, assign, …), never `claim_and_join` /
    `join_chat`. AEA-52 checks it on the seeds.
- **R-6 · Seed identity.**
  - The brief state for MHC-C-0005…0007 says `verified`: they name an issued customer, and 0005 and 0007 carry a
    `read_invoices` lookup, which is a verified-only tool.
  - No `identity_threads` row is written, because that table's write methods are AEA-27's and not in AEA-10's
    repository. So CON-12's identity line (AEA-29, from `core.reads.identity_state`) will read "not checked" for seeds.
  - **Request to AEA-52 / AEA-27:** if the staff view must show seeds as verified, add a seed-identity write in a
    follow-up merged before AEA-52. This is recorded in the journey record.
- **R-7 · A private `_BriefAssembler` Protocol.**
  - It only types the injected AEA-29 object for mypy. It is not exported and adds no seam (DO-3 S-20 defers Protocols
    in front of services; the injection itself is the ticket's).
  - AEA-29's extra optional keyword (`customer_messages`) and constructor argument (`staff_guidance`) keep the real
    class compatible with it.
- **R-8 · `StreamKey` (resolved since the first version).** AEA-10's plan now defines `StreamKey`, `thread_stream` and
  `case_stream` in `rows.py` (its R-9). Step 0.3 confirms them after the merge; a missing helper means
  `blocked-on AEA-10`.
- **R-9 · Seed staff guidance.**
  - `HandoffService.open` attaches `staff_guidance` lookup rows for refund, billing and complaint cases (CAS-33). Seeds
    do not, because the passage ids are minted at index build (AEA-16) and would be guessed here.
  - So heading 7 of the seed briefs carries only the hand-written open decision. AEA-52 may add the guidance once the
    index ids are stable.
- **R-10 · Collision surfaces.**
  - `web/container.py`: own hunk only.
  - `.claude/reference/area-map.md`: the A6 row's Status cell, which AEA-14, 29 and 30 also edit.
  - `.claude/state/icm-progress.md`: one new row.
  - `docs/design/code-design.md`: two lines.
  - The merge agent resolves cell-level conflicts; no other shared file is touched.
- **No signed-contract change and no product decision.**
  - Nothing here changes `ui-contracts.openapi.yaml` or `UI_CONTRACTS.md`.
  - No decision of `stage7-signoff.md` D-4…D-15 is answered differently. D-13's wall clock reaches `reset(now)` through
    `get_wall_clock()` in AEA-43; the operator script passes `datetime.now(UTC)`. D-8 (start fresh after signing in
    again) is untouched.

---

## 9. Readiness

**READY.** Implementation is **blocked-on the ticket's own earlier-wave blockers merging to `main`**:
- AEA-10: rows incl. `StreamKey` helpers, repositories, `restore_working_copy`, `Checkpointer.clearing`, `temp_sqlite()`.
- AEA-14: `promise_for`, `priority_for`, `case_due_at`, lane thresholds.
- AEA-23: `ResetGate`, `ResetAlreadyRunning`, `owned_thread`, `require_staff`, `ApiProblem`, deps keys, `WebShellState`.

AEA-02 (domain types, ports, `domain/staff.py`) is merged and verified. The same-wave siblings AEA-29 (`BriefAssembler`)
and AEA-30 (`format_clock`) are injected and tested with doubles (merge-order request R-1). No `NEEDS-DECISION`.

## Gates

None (no human, external, paid or live gate). Merge gate: lint and format, type check, the affected tests of §7.3, the
affected journeys; no full suite.

## Deviations

- Implementer (2026-10-21): none to the code design. Notes: (1) the issued DB has no `sqlite_sequence`, so the
  `issued_rows` helper returns `[]` for that table. (2) The monotonic-clock ordering assertion in
  `test_writer_waits_for_reset_lock` was dropped (racy: the reset's stamp is taken after its return); the live,
  non-tombstoned row W proves the writer committed after the reset. (3) `register_reset` uses the nested
  `first_boot()` form. (4) With the hunk filled, `tests/api/test_app.py::test_wall_clock_not_settable_from_settings_env_or_http`
  and `tests/api/test_gate.py::test_every_api_route_but_login_requires_session` fail with
  `ModuleNotFoundError: meridian.services.handoff` until AEA-29 and AEA-30 are on main (plan R-1: merge AEA-31 after them).
