## [AEA-30] demo: clock, staffing, scheduler job

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

> **US-22:** As a **supervisor**, I need one view of P0/P1, unowned, due-soon, overdue and stuck-waiting cases with owner,
> age and follow-up preference, and to assign or reassign with a reason, so that no promise is missed. In the demo I also
> start or end the simulated shift and advance the simulated clock.
>
> **US-25:** As a **reviewer**, I need a demo … where the date, the empty staffing, the code inbox and the "recorded, not
> sent" follow-ups are all labelled as demo simulations …

Three pieces. Case due times run on the **demo clock**, never the server clock (R-3); operations (the abandonment sweep,
the daily prune, `job_runs` times) run on the wall clock, UTC (api-con-mapping §4; merge MC-20). Shapes are
`docs/design/contracts/stage7/cases.md` §6 (it revises DO-4 §14's `SchedulerJob` constructor, CAS-29).

- **`services/demo.py` — `DemoClock(uow)`** (implements the `Clock` port, DO-4 §13; tz-aware America/Chicago):
  `now()` reads `demo_state.demo_now`, which is `DEMO_START` = Fri 2026-10-16 10:00 Chicago on a fresh store
  (stage7/cases §1.1, CAS-23). One demo clock for chat and staff; it moves **only** when advanced and **only forward**;
  a reset (AEA-31) returns it to `DEMO_START` through `demo_state.reset()`. Also here: `ClockStep =
  Literal["plus_1h", "plus_4h", "next_business_morning"]` and `format_clock(dt) -> (label, date_label)`, the **one**
  formatter for CON-1, CON-8 and `clock_changed` (("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)")).
- **`services/demo.py` — `DemoService(uow, clock: DemoClock, cases: CaseService)`** (stage7/cases §6, CAS-18):
  `presence(tx=None) -> Presence`, `staffing() -> StaffingView`, `set_staffing(mode, *, request_id, role: DemoRole)
  -> StaffingChange`, `clock_view() -> ClockView`, `advance_clock(step: ClockStep, *, actor: StaffActor, request_id)
  -> ClockAdvanced` (the owner's signature, merge MC-13). Staffing defaults to **nobody online** (R-30). `set_staffing`
  is one transaction: `demo_state`, one `demo_events` row (kind `staffing_changed`, CAS-5), `staffing_changed` to every
  open chat, and on `simulated_on_shift → nobody_online` `cases.convert_live_queued(now, tx)` (AEA-29), whose count is
  `converted_cases`; the same mode again writes nothing. `advance_clock` is one transaction: `demo_state`, one
  `demo_events` row (kind `clock_advanced`, `demo_events.role = actor.role.value`), `clock_changed` to every open chat;
  `next_business_morning` is 07:00 on the next business day (`is_business_day`, stage7/cases §3.1); `became_overdue` =
  open cases (not resolved or closed) whose **case** due `d` satisfies `old_now <= d < new_now`. Any logged-in role may
  toggle staffing (OpenAPI `setStaffing`); the route checks roles for the clock (AEA-47).
- **`services/scheduler.py` — `SchedulerJob(uow, cases, clock, prune_checkpoints, wall_clock)`** and `JobRun`
  (stage7/cases §6, CAS-29): `tick() -> JobRun`, every 60 s [A, system design §8.2] on a thread started by this ticket's
  `register_demo()` hunk. On the demo clock: `overdue` (case due, `cases.due_at`), `promises_missed` (promise due,
  `promises.due_at`, status `open` → `missed`; CAS-10), `due_soon` (within `DUE_SOON_WINDOW` = 4 h), `stuck_waiting`
  (wake-up passed), `unowned` (unassigned, age ≥ `UNOWNED_AFTER` = 30 min, written only while staffing is
  `simulated_on_shift`; stage7/cases §5 rules table, CAS-20 [A]) — one `case_event` per (case, kind, due or wake-up
  value), checked with `cases.case_events.exists(case_ref, kind, key)`, so catch-up is idempotent. On the wall clock:
  the **abandonment sweep** — `run_tag = 'live'`, `outcome = 'open'` and `last_customer_wall_at <= wall_now − 30 min` →
  `outcome = 'abandoned'`, ended at `last_customer_wall_at + 30 min` (DO-7 M-18 end rule, Innocent 2026-10-21; CAS-29);
  once per wall-clock day, `prune_checkpoints()` (keep 2, SDQ-10) with its count in `JobRun.pruned`. One `job_runs` row
  per tick (`started` → `completed` or `failed` with `error_kind`, counts in `counts_json`). `SchedulerJob` writes
  `job_runs` only: the missed-tick `health_event` is AEA-32's stale check (CAS-22).

This ticket writes **services only**; `repos_cases.py` (incl. `DEMO_START`, `demo_state`, `demo_events`, `job_runs`,
`case_events.exists`), every `.sql` and `checkpointer.py` are AEA-10's. Produces: `DemoClock` (the `Clock` every service
and node receives, wired at AEA-51/52), `DemoService` (AEA-29 presence, AEA-40 session greeting and CON-1 staffing,
AEA-43 CON-7 staffing and the CON-8 read, AEA-47 CON-8 advance), `format_clock` (AEA-31 `ResetDone.clock`, AEA-40, 43,
47), `SchedulerJob` (started here; proven running at AEA-52).

**Example pair (CON-8 + WF-7):** input — a case shaped like seed MHC-C-0007 (billing dispute, P3, created Fri 2026-10-16
09:24, case due = promise due Mon 2026-10-19 19:00, unowned), demo clock at `DEMO_START`; a supervisor calls
`advance_clock("next_business_morning")` (Mon 07:00), `plus_4h` three times (19:00), then `plus_1h` (20:00), then
`tick()` → output: one `demo_events` row and one `clock_changed` event per advance; `became_overdue = 0` on the step to
19:00 (19:00 is not before 19:00) and `1` on the `plus_1h` step; the `tick()` writes a `job_runs` row (status
`completed`, `overdue = 1`, `promises_missed = 1`), one `case_event` `overdue` for the case and promise status `missed`;
a second `tick()` adds a `job_runs` row and no second `overdue` event.

### Source

- `docs/design/contracts/stage7/cases.md` §1.1 (`DEMO_START`, `demo_state`, `demo_events`, `job_runs`,
  `conversations.run_tag` / `outcome` / `last_customer_wall_at`, wall-time storage), §1.2 (`cases.demo_state.*`,
  `demo_events.insert`, `job_runs.start/finish`, `case_events.exists`, `promises.list_open_past`), §3.1
  (`is_business_day`), §3.3 (`DUE_SOON_WINDOW`, `UNOWNED_AFTER`), §5 (rules table; `convert_live_queued(now, tx)`), §6
  (this ticket's classes); `stage7/staff.md` §1 (`DemoRole`, `StaffActor`), §8 (CON-8 call); `stage7/web.md` §4
  (`get_wall_clock()` UTC); DO-4 §13 (`Clock` port; events rule), §14, §16.
- Decision ledger `docs/plans/7b-decisions/cases.md`: CAS-5, CAS-10, CAS-18, CAS-20, CAS-22, CAS-23, CAS-29; merge
  `merge-clashes.md` MC-13, MC-20; residuals `7b-decisions/residuals-graph.md` R-G-9 (`FixedClock`) and
  `7b-decisions/residuals-web.md` R-W-17 (`ClockAdvanceResponse` has no `date_label`); join amendments §3 `[journey]`
  row for AEA-30 (`docs/plans/ux-join/backend-amendments.md`).
- DO-3 §4.4 (`services/demo.py`, `services/scheduler.py`), §6 S-8 (Clock), S-19 (in-process scheduler thread), S-20,
  §2.1 ("services never import other adapters").
- System design §8.2 (scheduler row: every 60 s [A], missed run caught up), §9 (*Growth*: prune to the last 2 per
  thread once a day, SDQ-10), §A.4 (Clock, Presence, Scheduler rows).
- Consolidated direction §6 (alerts table, transitions: live-queued → unassigned at shift end), §8 OD-1 (default
  unstaffed, labelled simulation), §10 ("Due-soon and overdue alerts come from a scheduled job on the fixed clock").
- PRD R-3, R-30, R-33; UI_CONTRACTS CON-7, CON-8 and OpenAPI `setStaffing`, `advanceDemoClock` (wire shapes win);
  SCREEN_SPECS staffing banner "Simulated staffing (demo). No Meridian employee is online."; api-con-mapping CON-3
  writers and §4; DO-6 WF-5, WF-7, CAP-5, *Missing instrumentation*; DO-7 M-13, M-18 (§4 end rule), M-27.
- **Brief check:** serves "Production thinking. Could this run for a month without you? Would the business know if it
  broke?" and "watch the agent escalate"; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

Clock tests use `FixedClock(...)` / `.advanced(...)` from `tests/fakes/clock.py` (stage7/data.md §8a, DAT-32; no second
clock fake), and a scheduler test that moves the demo clock builds one `SchedulerJob` per tick (its idempotency lives in
`case_events`, not in the object) (cases §6, R-G-9).

- [ ] AC-1 [invariant] `DemoClock.now()` is tz-aware America/Chicago, read from `demo_state`, equal to `DEMO_START` (Fri 2026-10-16 10:00) on a fresh store, and never reads the server clock — verify: `tests/services/test_demo.py::test_clock_starts_at_demo_start` and `::test_clock_ignores_wall_clock` (`temp_sqlite()`; wall clock patched forward a day) — evidence: `now()` unchanged by the wall clock; tzinfo America/Chicago; value 2026-10-16 10:00.
- [ ] AC-2 [failure/refusal] `advance_clock` moves only forward by `plus_1h`, `plus_4h` or `next_business_morning` (Fri 2026-10-16 10:00 → Mon 2026-10-19 07:00; from Wed 2026-11-25 → Mon 2026-11-30 07:00, skipping Thanksgiving); a step outside `ClockStep` is rejected and the clock does not move; no step moves it backwards — verify: `tests/services/test_demo.py::test_advance_steps` and `::test_unknown_step_rejected` — evidence: exact resulting datetimes; the rejected step leaves `demo_state`, `demo_events` and `events` unchanged.
- [ ] AC-3 [invariant] `advance_clock` returns `became_overdue` = open cases whose case due `d` satisfies `old_now <= d < new_now`, and its `ClockAdvanced` (= OpenAPI `ClockAdvanceResponse`) carries exactly `now`, `label` (from `format_clock`) and `became_overdue`, with no `date_label` key (cases §6; staff.md §8; R-W-17), and writes one `demo_events` row (kind `clock_advanced`, `step`, `demo_before`, `demo_after`, `became_overdue`, `request_id`, `role = actor.role.value`) and one `clock_changed` event per open chat in the same transaction — verify: `tests/services/test_demo.py::test_advance_counts_became_overdue` (the example pair's fixture) — evidence: count 0 for the step to Mon 19:00 and 1 for the step to 20:00; one `demo_events` row per step with the supervisor role.
- [ ] AC-4 [invariant] Staffing defaults to `nobody_online`; `set_staffing` to the same mode writes nothing; turning it off calls `cases.convert_live_queued(now, tx)` once inside the same transaction and returns its count as `converted_cases`; each change writes one `demo_events` row (kind `staffing_changed`, `mode`, `converted_cases`, `request_id`, `role`) and a `staffing_changed` event to every open chat — verify: `tests/services/test_demo.py::test_staffing_default_and_toggle` and `::test_shift_end_commits_with_conversions` (`CaseService` double honouring stage7/cases §5, then a double that raises) — evidence: fresh store reads `nobody_online`; same-mode set adds no row; off-with-queued returns the double's count; a raising double leaves staffing `simulated_on_shift` and no `demo_events` row.
- [ ] AC-5 [negative] No staffing state ever reads as a real employee: the staffing view's banner is the fixed `policy/texts.py` string "Simulated staffing (demo). No Meridian employee is online." (AEA-03, `demo` group), never composed or model text, and is absent while nobody is online — verify: `tests/services/test_demo.py::test_staffing_banner_is_fixed_text` — evidence: banner equals the texts constant for `simulated_on_shift` and is None for `nobody_online`.
- [ ] AC-6 [invariant] `format_clock` is the one clock formatter: `DEMO_START` → ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)"), and `clock_view()`, `advance_clock` and the `clock_changed` event all carry its output (`advance_clock` its `label` only, AC-3) — verify: `tests/unit/services/test_format_clock.py::test_format_clock_demo_start` and `tests/services/test_demo.py::test_views_use_format_clock` — evidence: exact strings; each output's label (and, where the schema has one, date label) equals `format_clock(now)`'s.
- [ ] AC-7 [invariant] `tick()` writes exactly one `job_runs` row per call (`job_run_id`, `started_wall_at` and `finished_wall_at` in UTC ISO `+00:00`, `demo_now`, status `started` → `completed`, or `failed` with an `error_kind` and no free text, counts in `counts_json`) and stamps its `job_run_id` on every `case_event` it writes — verify: `tests/services/test_scheduler.py::test_tick_writes_job_run` and `::test_failed_tick_records_failed` — evidence: one row per call; a forced failure leaves status `failed`.
- [ ] AC-8 [invariant] **WF-7 (`SchedulerJob.tick()`, the job's entry point):** On the demo clock, `tick()` raises `overdue` for an open case whose case due has passed and sets an `open` promise past its promise due to `missed`; for a `fee_bearing_change` case (case due 12:00 window start, promise due Mon 19:00) at Fri 13:00 it raises `overdue` and leaves the promise `open`; `stuck_waiting` for a waiting case past its wake-up; `due_soon` within `DUE_SOON_WINDOW`; `unowned` for an unassigned case aged ≥ `UNOWNED_AFTER` only while staffing is `simulated_on_shift`; a P0 safety case (no due) never goes overdue — verify: `tests/services/test_scheduler.py::test_overdue_and_missed`, `::test_fee_bearing_case_due_vs_promise_due`, `::test_stuck_waiting`, `::test_due_soon`, `::test_unowned_only_on_shift`, `::test_p0_never_overdue` — evidence: one `case_event` per condition; promise statuses as stated; no event for the P0 row; no `unowned` event while nobody is online.
- [ ] AC-9 [invariant] Idempotent catch-up: running `tick()` twice at the same demo time, or once after a skipped interval, writes no duplicate alert `case_event` for the same (case, kind, due or wake-up value) — verify: `tests/services/test_scheduler.py::test_tick_idempotent` — evidence: alert event count unchanged on the second call; `job_runs` count +1.
- [ ] AC-10 [invariant] Abandonment sweep on the wall clock (CAS-29): a `live` conversation still `open` with `last_customer_wall_at` 30 or more wall-clock minutes ago becomes `abandoned`, ended at `last_customer_wall_at + 30 min`; one at 29 minutes stays `open`; `eval`, `load` and `seed` threads and any conversation whose `outcome` is already set (e.g. `handed_off`) are never touched — verify: `tests/services/test_scheduler.py::test_abandonment_sweep` (wall clock injected, UTC) — evidence: exactly the qualifying row changes; `JobRun.abandoned` equals that count.
- [ ] AC-11 [invariant] Checkpoint pruning runs once per wall-clock day through the injected `prune_checkpoints()`, and its returned count is recorded as `JobRun.pruned` on that tick only — verify: `tests/services/test_scheduler.py::test_prune_once_per_day` (callable double, wall clock injected) — evidence: called once across many ticks in a day, again after the day changes; `pruned` None on every other tick.
- [ ] AC-12 [capture] WF-5 and WF-7 records carry their IDs: every staffing or clock change has a `demo_events` row with `demo_event_id` and `request_id`; every tick a `job_runs` row; every alert a `case_event` with `case_ref` and `job_run_id`; every promise status change a `case_event` — verify: `tests/services/test_demo.py::test_wf5_records` and `tests/services/test_scheduler.py::test_wf7_records` — evidence: rows present with those IDs. (CAP-5 through the real CON-8 entry point and a running scheduler is AEA-52's.)
- [ ] AC-13 [negative] `job_runs`, `demo_events` and alert `case_event` rows hold IDs, kinds, statuses, counts and times only — no customer name, phone, email or message text — verify: `tests/services/test_scheduler.py::test_records_hold_no_pii` (seeded MHC-10002 Omar Patel case, phone 512-555-0102) — evidence: "Omar", "Patel", "512-555-0102" absent from those rows.
- [ ] AC-14 [journey] **WF-2 (J-7's `requestPerson`):** Extends J-7 and J-6 (slice plan §0a journey map; both are proposed additions to the map for this ticket, from the join audits; `backend-amendments.md` §3): J-7, with staffing switched on (`setStaffing`) a person request is live-queued, and switching it off converts the case and writes `shift_ended` to the chat (AC-4); J-6, advancing the demo clock past a case due puts the case in the Overdue lane (AC-3, AC-8); asserting what the user sees and what is stored, in `tests/journeys/j7/test_aea_30.py` and `tests/journeys/j6/test_aea_30.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j7/test_aea_30.py tests/journeys/j6/test_aea_30.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-30.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-15 [regression/context] Same change updates: the area-map row for `services/demo.py` and `services/scheduler.py` (planned → built, commit); the `.claude/state/icm-progress.md` row whose evidence these modules change; DO-3 code-design status for both modules (planned → built), citing stage7/cases §6 as the signature source — verify: `git diff --name-only` — evidence: those files in the diff, only this ticket's rows.

### Observability

- Responsibilities: WF-5 — one `demo_events` row per staffing or clock change (`request_id`, role, before and after,
  counts) and its CON-3 event (`staffing_changed`, `clock_changed`). WF-7 — one `job_runs` row per tick with
  `job_run_id` on every `case_event` it writes (`due_soon`, `overdue`, `stuck_waiting`, `unowned`) and on each promise
  status change; the `scheduler_last_run` signal is read from `cases.job_runs.latest()` (AEA-32 stale check, AEA-53
  tile; CAS-22). IDs, kinds and counts only (AC-13).
- Capture evidence: AC-12 at the service boundary; CAP-5 (advance the demo clock past a due time; `demo_event`,
  `job_run`, promise marked) is AEA-52's at the real entry point.

### Evaluation

N/A — demo controls and the scheduler change the simulation and mark case state; they score no case. DO-6's WF-5 row
says "demo controls change the simulation, not an outcome; their effect is measured through WF-1 and WF-6", and WF-7
inherits metrics only (M-13, M-27). The overdue and missed rules are held by AC-8 and AC-9; R-33 ("Simulated clock shows
overdue correctly") is proven at AEA-52 (CAP-5).

### Metrics

- References: M-13 promises kept on time, M-18 abandonment, M-27 unowned and overdue cases.
- Acceptance conditions: M-13's denominator ("promises whose due time has passed") stays computable from
  `promises.status` and `promises.due_at` on the demo clock; M-27's overdue count from `cases.due_at` and the WF-7
  `case_events`, with `job_runs` proving the job ran; M-18 from `conversations.outcome`, which this ticket sets to
  `abandoned` only by the 30-minute rule; seed cases stay a segment. Targets are DO-7's (M-13 ≥ 90%, M-18 ≤ 10%),
  measured at Stage 9.

### Blocked by

AEA-10 (`repos_cases` incl. `DEMO_START`, `demo_state`, `demo_events`, `job_runs`; `repos_core` `events`; the checkpointer
`prune(keep=2)`), AEA-14 (`policy/handoff.py` `is_business_day`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`; wave 1). Also
imports, from waves 0–1 that land before wave 2: `policy/texts.py` (AEA-03), `domain/staff.py` (AEA-02), `FixedClock` in
`tests/fakes/clock.py` (AEA-11; R-G-9) — no wave moves.

AC-14's journey record names AEA-57 (harness, wave 2) and AEA-52 (the integrated staff side and running scheduler) as
*Blocked by* for its integrated level only (`integrated-journeys.md` §4); they are evidence-level dependencies, not merge
blockers, so no wave moves.

### Agent handoff

- Area / owner: A6 Cases and handoff; owns `src/meridian/services/demo.py`, `src/meridian/services/scheduler.py`, their
  tests, and its own `register_demo()` hunk in `web/container.py` (builds `DemoClock`, `DemoService`, `SchedulerJob`
  with `get_wall_clock()` and AEA-10's prune callable; starts and stops the 60 s runner thread).
- Contracts and shared surfaces: consumes the `Clock` port and DO-4 §13–§14 types (AEA-02), stage7/cases §1.2
  repositories (AEA-10), `prune_checkpoints` (AEA-10, injected by the container), `CaseService.convert_live_queued(now,
  tx)` (AEA-29, same wave: injected double honouring stage7/cases §5), policy constants (AEA-14), fixed strings (AEA-03).
  Produces `DemoClock` for every service and node, `DemoService` for AEA-29, 40, 43, 47, `format_clock` for AEA-31, 40,
  43, 47, and `SchedulerJob` for AEA-52. Must not edit `repos_cases.py`, any `.sql`, `checkpointer.py`, `policy/*`,
  any route.
- Scope boundary / refusal: no route (CON-7 is AEA-43, CON-8 advance AEA-47), no reset (AEA-31), no case lifecycle rules
  (AEA-29), no `health_event` (AEA-32); never the server clock for case due times; never a backwards step; never implies
  a real employee is online; the sweep writes only `abandoned`, never another outcome (stage7/cases A-7).
- Evidence level (`.claude/rules/integrated-journeys.md` §4): these service tests are `mock-tested`; AC-14 extends J-7
  (staffing on → live-queued; off → converted, `shift_ended`) and J-6 (clock advance → Overdue lane) in
  `tests/journeys/j7/test_aea_30.py` and `tests/journeys/j6/test_aea_30.py`; until AEA-57 and AEA-52 land, the record
  states `mock-tested` and *Blocked by* AEA-57, AEA-52. CAP-5 at the real CON-8 entry point stays AEA-52's.
- `ClockAdvanced` carries the OpenAPI's three fields only (`now`, `label`, `became_overdue`; cases §6, staff.md §8,
  R-W-17); `format_clock` still returns `(label, date_label)` for CON-1 and the CON-8 read.
- Wave and gates: wave 2; no human or external gate.
- Lane: build-loop — changes source and tests (ticket-lanes).
- Risk: None (slice plan row; it reads case state and writes IDs and counts only, AC-13).
- Entry points added or changed: WF-7 (the scheduler job, a background thread started here) and WF-5 (services behind
  CON-7 and CON-8, whose HTTP entry points are AEA-43 and AEA-47).
