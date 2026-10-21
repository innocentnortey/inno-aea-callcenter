## [AEA-31] reset: all-or-nothing reset and demo seed

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

> **US-25:** As a **reviewer**, I need a demo (reached with the demo login) where the date, the empty staffing, the code
> inbox and the "recorded, not sent" follow-ups are all labelled as demo simulations … Acceptance: … a reset restores the
> demo …

Shapes are `docs/design/contracts/stage7/cases.md` §7 (it revises DO-4 §14's `ResetService`: CAS-1, CAS-2, CAS-3; merge
MC-19, MC-20) over the storage of §1.1–§1.4 that AEA-10 writes.

- **`services/reset.py` — `ResetService(uow, gate: ResetGate, restore_working_copy, clear_checkpoints, seed_demo)`**:
  `reset(now, *, request_id, session_id: LoginSessionId | None, role: DemoRole | None) -> ResetDone | ResetFailed`.
  `now` is the wall clock (`reset_events.at_wall`, UTC). CON-9 passes the caller's session id and role; `None, None` is
  the operator script on a stopped service (data.md §7, AEA-50), stored as NULL `asked_by_role` / `asked_by_session`.
  The order, exactly as stage7/cases §7:
  1. `with gate.hold():` — web's `ResetGate` (web.md §7, AEA-23); raises `ResetAlreadyRunning` when already held (the
     route answers 409 `RESET_IN_PROGRESS`); while held, the middleware answers 503 `RESET_IN_PROGRESS` on the
     documented operations.
  2. `with uow(write=True, exclusive=True) as tx, clear_checkpoints():` — turns in flight wait for the exclusive lock
     (SQLite `busy_timeout` 5 s [A]; `limits.web.reset_wait_s`, web.md §5).
  3. `restore_working_copy(tx)` rewrites the five issued tables in place (CAS-1, §1.4); `cleared =
     tx.core.reset.clear_demo_tables(reset_id)` clears and tombstones per §1.3 (incl. identity codes, inbox, flags and
     staff roles back to customer with `role_reset_pending = 1`, staff.md §4; CAS-3); `tx.cases.demo_state.reset()`
     (clock to `DEMO_START`, staffing `nobody_online`).
  4. `demo_reset` appended to each `cleared.open_threads` stream and each `cleared.case_streams` stream (new, higher
     ids; MC-7, MC-8).
  5. `n = seed_demo(tx)`; one `reset_events` row (`reset_id`, `at_wall`, `asked_by_role`, `asked_by_session`,
     `request_id`, `restored_json` from `cleared.rows_cleared`, `open_chats_ended`, `roles_reset`,
     `checkpoints_cleared`) and one `seed_events` row (`reset_id`, `seed_count = n`, label "demo seed").
  6. `tx.commit()` — meridian commits first; the checkpoint clear commits on exit. Any exception before the meridian
     commit rolls back both → `ResetFailed` (`RESET_FAILED`). **All-or-nothing: nothing is ever half-reset.** The one
     residual window (the checkpoint commit failing after meridian committed) leaves only checkpoints of tombstoned,
     unreachable threads, recorded as `checkpoints_cleared = false` and removed by the next prune or reset.

  `ResetDone(ok=True, open_chats_ended, roles_reset, clock: ClockView)` = OpenAPI `ResetResponse` (CAS-31). A reset never
  clears `spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`, `job_runs`, `demo_events`,
  `reset_events`, `seed_events` or `ended_threads` (§1.3 *Kept*).
- **The demo seed loader**, in `services/reset.py`: `seed_demo(tx) -> int` (= DO-4's `Callable[[UnitOfWork], int]`),
  run at first boot when `cases.records.seed_rows_present()` is False (triggered from this ticket's `register_reset()`
  hunk) and inside every reset. It writes the **four seeds of stage7/cases §7** (CAS-24), each a thread with
  `run_tag = 'seed'`, fixed customer messages, `lookup_log` rows, a brief built by `BriefAssembler` from a hand-written
  `BriefExtraction` whose quotes are exact substrings of the seed messages, `cases.seed = 1`, and a promise from
  `promise_for` **at the seed's own `created_at`** (never recomputed at the demo start):

  | Ref | Reason, priority | Customer | `created_at` | Promise → case due | At `DEMO_START` |
  |---|---|---|---|---|---|
  | MHC-C-0005 | refund, P3 | an issued customer (seed file) | Tue 2026-10-13 10:00 | R26.refund → Thu 10-15 19:00 | unassigned, Overdue lane |
  | MHC-C-0006 | complaint_or_manager (conduct), P3 | an issued customer (seed file) | Fri 2026-10-16 09:14 | R26.unstaffed → Mon 10-19 19:00 | Unowned lane |
  | MHC-C-0007 | billing_dispute, P3, INV-204411 | MHC-10002 Omar Patel | Fri 2026-10-16 09:24 | R26.unstaffed → Mon 10-19 19:00 | Unowned lane; follow-up phone, mornings |
  | MHC-C-0008 | safety (gas smell), P0 | none (unmatched caller) | Fri 2026-10-16 09:56 | R26.safety_none → no due | P0 and P1 lane |

  The two customers not named are issued customers outside MHC-10001…10004 and MHC-57204 (the worked pairs' customers),
  recorded in the seed file. Live cases then number from MHC-C-0009 (`refs.next_case_ref`). Returns 4.

This ticket writes services only: `migrate.py` (`restore_working_copy(tx)`), `checkpointer.py` (`Checkpointer.clearing()`),
`repos_cases.py`, `repos_core.py` (`clear_demo_tables`, tombstones) and every `.sql` are AEA-10's; `ResetGate` is
AEA-23's. Produces `ResetService` for AEA-43 (CON-9 route) and AEA-50 (the operator reset script), and the seed set
every staff view, AEA-52's walkthrough and AEA-53's `seed_count` start from.

**Example pair (CON-9):** input — after a session where WP-3's booking wrote appointment rows, the WP-7 refund case
MHC-C-0009 opened, a code was issued to the demo inbox, the representative role was taken and the clock was advanced
to Mon 2026-10-19 07:00, CON-9 calls `reset(now, request_id=r, session_id=s, role=supervisor)` → output:
`ResetDone(ok=True, open_chats_ended=1, roles_reset=1, clock=<format_clock(DEMO_START)>)`; the working copy's
`appointment_slots` and `appointments` equal the issued file's again (the next appointment id is the issued maximum + 1);
MHC-C-0009, the code and the inbox row are gone; the thread is an `ended_threads` tombstone (reason `demo_reset`); seeds
MHC-C-0005…0008 are back with `seed = 1`; one `reset_events` row (`asked_by_role = supervisor`) and one `seed_events`
row (`seed_count = 4`); the `spend_ledger` row count is unchanged.

### Source

- `docs/design/contracts/stage7/cases.md` §1.1 (`ended_threads`, `events` AUTOINCREMENT, `reset_events`, `seed_events`,
  `conversations.run_tag`, `cases.seed`, wall-time storage), §1.2 (`core.reset.clear_demo_tables`, `Cleared`,
  `core.conversations.lookup` → `EndedThread`, `cases.demo_state.reset`, `cases.records.*`, `refs.next_case_ref`), §1.3
  (restored / cleared / updated / kept), §1.4 (the two callables), §3.2 (`promise_for`), §7 (this ticket); `stage7/web.md`
  §4 (`owned_thread` 410), §5 (`reset_wait_s`), §7 (`ResetGate`); `stage7/staff.md` §1 (`LoginSessionId`, `DemoRole`),
  §4 (staff state on reset), §7 (CON-21 starts after the newest `demo_reset`); `stage7/data.md` §7 (operator script);
  DO-4 §14, §16.
- Decision ledger `docs/plans/7b-decisions/cases.md`: CAS-1, CAS-2, CAS-3, CAS-23, CAS-24, CAS-31, CAS-32; merge
  `merge-clashes.md` MC-7, MC-8, MC-9, MC-11, MC-15, MC-19, MC-20, MC-27; `residuals-web.md` R-W-11 (AEA-23 blocker).
- DO-3 §4.4 (`services/reset.py`), §6 S-20 and §11 S-3 (injected callables); system design §8.2 (*Demo reset* row:
  exclusive lock, 5 s wait [A], all-or-nothing, open chats ended), §9 (*First boot and reset*), §A.4, §A.5.
- UI_CONTRACTS CON-9, CON-10 and OpenAPI `resetDemo` / `ResetResponse` ("Restores the working DB copy, cases, seeds and
  codes"; "All-or-nothing"; "Open chats end (`demo_reset` event, SESSION_ENDED on later calls)"); SCREEN_SPECS SCR-5 and
  SCR-7 default states (the seed rows), SCR-1 "The demo was reset, so this chat has ended. Nothing from it was kept.".
- PRD R-19 ("A one-command reset restores the copy"), R-33 (demo seed cases); consolidated direction §8; DO-6 WF-15,
  WF-16, CAP-9, *Storage and access*; DO-7 M-3, M-13, M-27 seed segment.
- **Brief check:** serves "a reviewer should be able to type questions, probe edge cases, and watch the agent escalate"
  (they test against our deployed copy, Q-2, so it must be restorable); touches nothing out of scope; weakens nothing →
  proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] After `reset`, the working copy's five issued tables (`customers`, `technicians`, `appointment_slots`, `appointments`, `invoices`) equal the issued file row for row, their `sqlite_sequence` rows equal the issued maximum, and the issued file's bytes are unchanged — verify: `tests/services/test_reset.py::test_reset_restores_working_copy` (`temp_sqlite()` from `tests/fixtures/sqlite.py`, a booking written first; checksum of the issued fixture before and after) — evidence: row diff empty; next appointment id = issued max + 1; checksum equal.
- [ ] AC-2 [invariant] **WF-15 and WF-16 (the seed load inside a reset, which DO-6 WF-16 stamps with `reset_id`):** All-or-nothing: a failure injected into each step in turn (restore, `clear_demo_tables`, `demo_state.reset`, the `demo_reset` appends, `seed_demo`, the record writes, the meridian commit; for each step after `seed_demo` the real `seed_demo` runs first, so its rows must roll back too) leaves the pre-reset state readable — cases, codes, inbox, clock, staffing, staff roles, checkpoints — and returns `ResetFailed` (`RESET_FAILED`) — verify: `tests/services/test_reset.py::test_reset_all_or_nothing` (parametrised over the failing step with raising doubles and a real `Checkpointer.clearing()` on a temp `checkpoints.sqlite`) — evidence: for every step, a post-failure read equals the pre-reset snapshot, checkpoint rows included.
- [ ] AC-3 [failure/refusal] A checkpoint commit that fails after meridian committed returns `ResetDone`, records `reset_events.checkpoints_cleared = 0`, and leaves only checkpoints of tombstoned threads — verify: `tests/services/test_reset.py::test_checkpoint_commit_failure_residual_window` (a `clearing()` double that raises on exit) — evidence: meridian rows equal a completed reset's; the flag is 0; every remaining checkpoint's thread is in `ended_threads`.
- [ ] AC-4 [failure/refusal] A second reset while one holds the gate raises `ResetAlreadyRunning` and changes nothing; a writer in flight waits for the exclusive lock rather than writing into a half-reset store — verify: `tests/services/test_reset.py::test_concurrent_reset_refused` and `::test_writer_waits_for_reset_lock` (two threads, temp SQLite, the real `ResetGate` from AEA-23) — evidence: one `reset_events` row; the second call raises; the writer's row lands after the reset or not at all.
- [ ] AC-5 [invariant] Reset ends every open chat and resets roles: one `demo_reset` event per `cleared.open_threads` stream and per `cleared.case_streams` stream, each with an id higher than any before the reset; `ResetDone.open_chats_ended` equals the open-thread count; `ResetDone.roles_reset` equals `cleared.roles_reset`; afterwards `core.conversations.lookup(old_thread)` returns an `EndedThread` with `reason = "demo_reset"` and the `reset_id` — verify: `tests/services/test_reset.py::test_reset_ends_open_chats` (two open chats, one representative and one supervisor session) — evidence: counts 2 and 2; one `demo_reset` per stream; the tombstone row.
- [ ] AC-6 [failure/refusal] A later call on a reset thread answers 410 `SESSION_ENDED`, not 404 (CAS-32, MC-16) — verify: `tests/services/test_reset.py::test_ended_thread_answers_session_ended` (AEA-23's `owned_thread` dependency on a minimal FastAPI app over the reset store, same login session) — evidence: 410 `SESSION_ENDED` with `details.reason = "demo_reset"`; another session's id for the same thread gets the identical 404.
- [ ] AC-7 [invariant] **WF-15 (`ResetService.reset`, the operation CON-9 and the reset script both call):** Reset returns the demo clock to `DEMO_START` (Fri 2026-10-16 10:00 Chicago) and staffing to `nobody_online`, and `ResetDone.clock` equals `format_clock(DEMO_START)` — verify: `tests/services/test_reset.py::test_reset_restores_clock_and_staffing` — evidence: `demo_state` equals a fresh store's; the clock labels match.
- [ ] AC-8 [negative] Reset clears every verification code, inbox row, identity thread and flag, and keeps every operational record: `spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`, `job_runs`, `demo_events`, `reset_events`, `seed_events`, `ended_threads` unchanged in count (plus the new reset and seed rows) — verify: `tests/services/test_reset.py::test_reset_clears_codes_keeps_ops_records` — evidence: `identity_codes`, `demo_inbox`, `identity_threads` and `flags` empty; every kept table's count equal before and after.
- [ ] AC-9 [invariant] **WF-16 (the seed loader):** `seed_demo(tx)` writes exactly the four seeds of stage7/cases §7 with `seed = 1`, `run_tag = 'seed'`, each `created_at` before `DEMO_START`, each promise equal to `promise_for(reason, "nobody_online", created_at)` (never free text, never recomputed at the demo start), each brief assembled from quotes that are exact substrings of the seed messages, and returns 4; at first boot it loads once and a restart with seed rows present loads none; the next live case is MHC-C-0009 — verify: `tests/services/test_reset.py::test_seed_cases_labelled_and_counted`, `::test_seed_promises_from_table`, `::test_first_boot_seeds_once`, `::test_next_live_ref_after_seeds` — evidence: refs MHC-C-0005…0008; MHC-C-0005 promise due Thu 2026-10-15 19:00; second start adds 0 rows; next ref MHC-C-0009.
- [ ] AC-10 [invariant] **WF-16 (seed load, timed against `DEMO_START`):** At `DEMO_START` the seeds sit where SCREEN_SPECS SCR-5 and SCR-7 show them: MHC-C-0008 in P0 and P1, MHC-C-0005 Overdue, MHC-C-0006 and MHC-C-0007 Unowned, MHC-C-0007's follow-up phone, mornings — verify: `tests/services/test_reset.py::test_seed_lanes_at_demo_start` (`CaseService.oversight` double honouring stage7/cases §5's lane rules, or the real one once AEA-29 has merged) — evidence: lane membership as stated.
- [ ] AC-11 [negative] Seed data holds only issued or fictional values: seeded customers come from the issued DB's records, no card-like number and no code, and no seed text is written by a model — verify: `tests/services/test_reset.py::test_seed_holds_no_codes_or_cards` — evidence: no 13–19 digit run and no 6-digit code pattern in any seeded row; every seeded `customer_id` exists in the issued file.
- [ ] AC-12 [capture] WF-15 and WF-16 records: one `reset_events` row per reset with `reset_id`, `at_wall` (UTC `+00:00`), `asked_by_role`, `asked_by_session`, `request_id`, `restored_json`, `open_chats_ended`, `roles_reset`, `checkpoints_cleared`; the operator-script call (`session_id=None, role=None`) stores NULL for both asker columns; one `seed_events` row per seed load with `seed_count` and label "demo seed", `reset_id` set inside a reset and NULL at first boot — verify: `tests/services/test_reset.py::test_reset_and_seed_events` — evidence: rows with those fields. (CAP-9's reset and seed-load checks at the real entry points are AEA-50's, which owns that `tests/capture/` file.)
- [ ] AC-13 [negative] `reset_events` and `seed_events` hold IDs, roles, counts and times only — no session token, customer name, phone or message text — verify: `tests/services/test_reset.py::test_reset_records_hold_no_pii` (a reset after a seeded MHC-10002 conversation with phone 512-555-0102) — evidence: "Omar", "512-555-0102" and the token's test value absent from both rows.
- [ ] AC-14 [journey] Extends J-8 (slice plan §0a journey map; J-8 is a proposed addition to the map, from the join audits; backend-amendments §3): a `resetDemo` from one client sends every staff call of both clients on that login to 403 `role_reset` until a role switch, ends the open chat (`demo_reset` on its stream, 410 on its thread) and restores the issued tables row for row; asserting what the user sees and what is stored, in `tests/journeys/j8/test_aea_31.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j8/test_aea_31.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-31.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-15 [regression/context] Same change updates: the area-map row for `services/reset.py` (planned → built, commit); the `.claude/state/icm-progress.md` row whose evidence this module changes; DO-3 code-design status for `services/reset.py` (planned → built), noting that the seed loader lives there and the seed list is stage7/cases §7 — verify: `git diff --name-only` — evidence: those files in the diff, only this ticket's rows.

### Observability

- Responsibilities: WF-15 — one `reset_events` row per reset with `reset_id`, who asked and open chats ended, plus a
  `demo_reset` event on every cleared thread and case stream; WF-16 — one `seed_events` row per seed load with the seed
  count and the "demo seed" label; signal `demo_reset` (system design §8.2). These explain a drop to zero on the pages
  (DO-6 WF-15 row). IDs, roles and counts only (AC-13).
- Capture evidence: AC-12 at the service boundary; CAP-9 (reset; seed load) at the real entry points is AEA-50's.

### Evaluation

- Checks: no scoring suite runs here ("a reset restores the demo state; it is logged so a drop to zero on the pages is
  explained", DO-6 WF-15). Kept passing: the E-7 DB-copy check after an eval run (AEA-24) compares against the copy AC-1
  restores; the seed cases are the named segment DO-6 WF-16 requires (SCR-9's basis line counts them; M-3, M-13 and M-27
  report with and without them).
- Expected-answer authority: the issued scheduling DB file for the restored tables (system design §A.5); SCREEN_SPECS
  SCR-5 and SCR-7 default states and the policy table for the seed set (CAS-24).

### Metrics

- References: M-3, M-13, M-27 (seed cases are a named segment: reported with and without them, DO-6 WF-16); M-22 volume
  (conversations are demo data and are cleared; the drop is explained by `reset_events`, DO-6 WF-15); M-26 and M-28 (their
  records survive a reset).
- Acceptance conditions: every seed row carries `seed = 1` (and `run_tag = 'seed'` on its thread, so live counts never
  include it) and is counted by `seed_events`, so the owner page's basis line can name the seed count (CON-18
  `seed_count` = 4); spend and health records survive a reset so M-26 and M-28 stay computable.

### Blocked by

AEA-10 (`restore_working_copy(tx)`, `Checkpointer.clearing()`, `clear_demo_tables`, tombstones, `repos_cases` incl.
`demo_state.reset`, reset/seed records), AEA-23 (`ResetGate`, `ResetAlreadyRunning`, `owned_thread` for AC-6; web.md §7,
MC-27, R-W-11: the slice plan row still lists 10 only and is the orchestrator's to update to "10, 23"; AEA-23 is wave 1,
so no wave moves). Also imports, from waves 0–1 that land before wave 2: `promise_for` (AEA-14), `domain/staff.py`
(AEA-02). The `[journey]` AC-14's integrated level only (not this ticket's merge): AEA-57 (harness) and AEA-52 (lands
J-8, wave 3).

### Agent handoff

- Area / owner: A6 Cases and handoff; owns `src/meridian/services/reset.py` (incl. the seed loader and its seed data),
  its tests, and its own `register_reset()` hunk in `web/container.py` (builds `ResetService` with the container's
  `ResetGate` and AEA-10's callables; runs the first-boot seed when `seed_rows_present()` is False).
- Contracts and shared surfaces: consumes `UnitOfWorkFactory(write=True, exclusive=True)` and stage7/cases §1.2–§1.4
  (AEA-10), `ResetGate` (AEA-23), `promise_for` (AEA-14); calls through their stage7 signatures (same wave, injected,
  tested with doubles): `BriefAssembler` (AEA-29, bound into the `seed_demo` callable by the container) and
  `format_clock` (AEA-30) for `ResetDone.clock` — a plan that needs more than those signatures records
  `blocked-on AEA-29` / `blocked-on AEA-30`. Produces `ResetService` and `seed_demo` for AEA-43 (CON-9), AEA-50 (reset
  script, CAP-9), AEA-52, AEA-53 (`seed_count`). Must not edit `migrate.py`, `checkpointer.py`, any repository or `.sql`
  file, `services/demo.py`, `services/reset_gate.py` (clock and staffing are reset through `demo_state.reset()`, not
  AEA-30's code).
- Scope boundary / refusal: never writes the issued DB file; never clears a *Kept* table of §1.3; no partial reset under
  any failure; no route (AEA-43) and no script (AEA-50).
- Evidence level (`.claude/rules/integrated-journeys.md` §4): these service tests are `mock-tested`; the reset
  through the real CON-9 route is AEA-43's and CAP-9 is AEA-50's; record `Blocked by: AEA-43, AEA-50` for the
  integrated level. The J-8 journey step (AC-14) records `mock-tested` and `Blocked by: AEA-57, AEA-52` until both
  merge.
- Wave and gates: wave 2; no human or external gate.
- Lane: build-loop — changes source and tests (ticket-lanes).
- Risk: None (slice plan row; codes and inbox rows are deleted through AEA-10's method, and AC-13 keeps the records free
  of values).
- Entry points added or changed: WF-15 (the reset service behind CON-9 and the operator script, whose entry points are
  AEA-43 and AEA-50) and WF-16 (the first-boot seed load, started from this ticket's `register_reset()` hunk).
