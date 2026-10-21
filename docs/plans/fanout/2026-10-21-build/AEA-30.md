# Plan — [AEA-30] demo: clock, staffing, scheduler job

**Status:** planned · **READY** (every prerequisite is merged on `main`; nothing to wait for).
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #30 (= `docs/plans/tickets/AEA-30.md`; no comments on the issue as of
this refresh) · **Base revision:** `dd1b110` (main, 2026-10-21, after the AEA-02b, 17, 18, 21, 27 and 28 merges).
**Lane / risk:** `lane::build-loop` · no `risk::security` (slice plan row: not **Sec**). Normal loop: the implementer writes the
code **and** the tests named in §7 together. No test-writer, no frozen tests, no security agent.
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21, third refresh. **Implementer:** `fanout-implementer` on Sonnet.
**Worktree / branch:** whatever the orchestrator gives you (convention: `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-30`,
branch `aea-30-aea-30-demo-clock-sched`). That worktree **already holds two unreviewed commits** from the earlier plan;
step 0.0 says how to use them. All paths below are relative to the repository root.

**Third refresh (2026-10-21, checked against `main` at `dd1b110`). What changed, and why:**

- **T-1. AEA-02b merged (`5305d57`): the four view types now live in `src/meridian/domain/views.py`.**
  - `ClockView`, `ClockAdvanced`, `StaffingView` and `StaffingChange` have exactly the fields this plan had.
  - Decision D-P1 is retired. `services/demo.py` imports the four types and defines none of them (§4.5).
  - A new test pins this: `tests/unit/services/test_demo_imports.py::test_view_types_come_from_domain_views`.
  - The ledger's last blocker (AEA-02b) is cleared, so nothing blocks this ticket.
- **T-2. An implementation branch already exists.**
  - Branch `aea-30-aea-30-demo-clock-sched`, in worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-30`, holds
    `5f4e879` (code and tests) and `339d410` (journey record and context rows).
  - They were built from the second-refresh plan on base `0a85270`. That base already had AEA-02b, so the code already
    imports the views.
  - They were never reviewed and are not in the build ledger (AEA-30 is still `ready` there).
  - They are a **starting point, not evidence**. Step 0.0 merges `main` into the branch, step 9 fixes the stale context
    text ("view types local until AEA-02b"), and every check in §7 runs again on the merged head.
- **T-3. AEA-29's plan asks two things of this ticket. Both are declined here, with reasons** (§8 R-16).
  - *"Build `DemoService` with `c.get(deps.CASE_SERVICE)`" (its R-3 note):* declined.
    - `case_service` is still unbound on `main` (AEA-29 is unmerged), so an eager read would break every app start.
    - `DeferredCases` works in either merge order and costs nothing once AEA-29 binds the key.
  - *"Use `services/cases.staffing_view(mode)` instead of `STAFFING_LABELS`" (its R-16):* declined for now.
    - It would make this file import `services/cases.py`. PA-6 forbids that, and the module is not on `main`.
    - The strings are identical; the request goes back to AEA-29.
- **T-4. AEA-29's R-7: a promise converted at a shift end is stored as `changed`, so it can never be marked `missed`.**
  - This ticket follows the signed rule through AEA-10's `list_open_past`: cases §5 marks a promise `missed` when the
    scheduler "finds it `open`".
  - The fix belongs on AEA-29's side. It is raised as a request (§8 R-17), not decided here.
- **T-5. Line numbers moved** on `dd1b110`:
  - `register_demo` is now lines 495–499 of `web/container.py`;
  - the A6 ICM row is line 32;
  - the last `**Built:**` line in DO-3 is line 192 (AEA-28);
  - the area-map A6 row is still line 31.

  Find each one with the `grep` given in step 9, not by its number.
- **T-6. Merges now follow the dependency tree** (Innocent, 2026-10-21: "we should merge in accordance to the tree").
  - This ticket may be merged in one batch with other wave-3 tickets (AEA-29, 40, 43, 45 …), not alone.
  - Nothing in the build changes. The plan already avoids depending on merge order (`DeferredCases`, the forwarders in
    other hunks, journey steps that report as blocked).
  - The shared context rows are resolved as the union (R-11, R-19).
- **T-7. R-3 still holds.**
  - The newly merged hunks (`register_identity`, `register_scheduling`, `register_jev`, `register_anthropic`) and their
    tests do not read `"demo_clock"`.
  - Two harnesses provide `"demo_clock"` themselves: `tests/api/handoff_support.py` and `staff_session_support.py`'s
    custom build. Neither calls the real `register_demo`.

**Second refresh (checked against `main` at `e22aebb`). It still holds except where T-1…T-7 say otherwise:**

1. **Every prerequisite is merged:** AEA-10 (`dc65bc5`), AEA-11 (`36f896a`), AEA-14 (`551b13c`), AEA-23 (`1e6889a`), AEA-31,
   AEA-32, AEA-41, AEA-42, AEA-44, AEA-46, AEA-47, AEA-57 (journey harness), AEA-59. §4 is now copied from **merged code**,
   not from sibling plans.
2. ~~The four view types are defined in `services/demo.py`, not waited for (decision D-P1).~~ *Superseded by T-1.* The earlier plan stopped
   at "blocked-on AEA-02b". No AEA-02b ticket was ever cut, and the ledger shows AEA-30 sat blocked for a whole wave on it.
   Meanwhile AEA-31 merged with the same pattern (`ResetClock` in `services/reset.py`, "same fields as AEA-30's ClockView"), and
   AEA-47's merged route reads our result with `ClockAdvanceResponse.model_validate(result, from_attributes=True)`, which
   accepts any object with the three attributes (prototyped: it works on a local `MeridianModel`).
3. **`DeferredCases` fails with the house error.** When `case_service` is not bound, the resolver in the hunk raises
   `RuntimeError("not bound: case_service")`, the same form AEA-42/44/46's forwarders use and AEA-59's contract driver
   recognises. The earlier plan let a `ContainerError` escape.
4. **Journeys now run on AEA-57's harness.** The earlier mock-level journey files (doubles inside `tests/journeys/`) are
   replaced. The harness README forbids doubles, monkeypatching `meridian` and `dependency_overrides` in journey files. J-6's
   clock-advance and scheduler steps can run **integrated with a scripted model** today (`advanceDemoClock` is routed by
   AEA-47). J-6's Overdue-lane step and every J-7 step are written against the OpenAPI and are reported **blocked** by the
   harness until AEA-29, AEA-40, AEA-43 and AEA-45 land.
5. **This merge un-skips existing tests that build the real app.** Login reads `Key("demo_clock")`, which only this ticket
   provides (wave-2 seam finding 1: "login returns a bare 500 on the integrated app"). After this merge, J-1's login steps,
   the harness's wall-clock test, `tests/api/test_staff_session_capture.py`, and the contract driver's `advanceDemoClock` cases
   all run for real. They are in the affected set (§7.2) and become plan-added criterion PA-8.
6. **Test helper renamed** `tests/services/demo_support.py` (the folder's convention is `<x>_support.py`).
7. **Context rows match today's files:** the A6 area-map row that already carries AEA-31's clause, the A6 ICM row (line 30 then, 32 now; T-5),
   and a new `**Built:**` line in DO-3 §3. Each ticket now gets its own `**Built:**` line.

---

## 1. Goal and sources

### 1.1 Goal (quoted from the issue, *What to build*)

> Three pieces. Case due times run on the **demo clock**, never the server clock (R-3); operations (the abandonment sweep,
> the daily prune, `job_runs` times) run on the wall clock, UTC (api-con-mapping §4; merge MC-20). Shapes are
> `docs/design/contracts/stage7/cases.md` §6 (it revises DO-4 §14's `SchedulerJob` constructor, CAS-29).
>
> - **`services/demo.py` — `DemoClock(uow)`** … `ClockStep` … `format_clock(dt) -> (label, date_label)` …
> - **`services/demo.py` — `DemoService(uow, clock: DemoClock, cases: CaseService)`** … `presence`, `staffing`, `set_staffing`,
>   `clock_view`, `advance_clock` …
> - **`services/scheduler.py` — `SchedulerJob(uow, cases, clock, prune_checkpoints, wall_clock)`** and `JobRun` … `tick() -> JobRun`,
>   every 60 s … on a thread started by this ticket's `register_demo()` hunk.
>
> This ticket writes **services only**; `repos_cases.py` …, every `.sql` and `checkpointer.py` are AEA-10's.

**What it does, in practice.**

- **The demo clock.** The demo starts on Friday 2026-10-16 at 10:00 in Chicago. That moment is a row in `demo_state`, not
  the server's clock. `DemoClock.now()` reads the row, so every due time in chat and on the staff console is measured
  against the same simulated "now". The clock moves only when a supervisor presses +1 hour, +4 hours or "next business
  morning", and only forward.
- **Staffing.** By default nobody is online. Anyone signed in can turn on "simulated staff on shift". Turning it off ends
  the shift: every customer still waiting in a live queue gets the written 1-business-day promise instead. AEA-29's
  `convert_live_queued` does that part, inside our transaction. Every open chat gets a `staffing_changed` event.
- **The scheduler.** Every 60 seconds a background thread runs `tick()`.
  - On the demo clock it writes one alert row (`case_events`) the first time a case becomes due soon, overdue, stuck waiting
    or unowned, and it marks a passed promise `missed`.
  - On the real clock it marks a live chat `abandoned` after 30 minutes with no customer message, and once a day it prunes
    old LangGraph checkpoints.
  - Each tick writes one `job_runs` row, so the business can see the job ran.

**Worked pair (the ticket's CON-8 + WF-7 example; the plan's test is `tests/services/test_demo.py::test_example_pair_con8_wf7`).**
- **Input:** a case shaped like seed MHC-C-0007 (billing dispute, P3, created Fri 2026-10-16 09:24, case due = promise due
  Mon 2026-10-19 19:00, unowned), with the demo clock at `DEMO_START`. A supervisor calls
  `advance_clock("next_business_morning")` (Mon 07:00), then `plus_4h` three times (19:00), then `plus_1h` (20:00), then
  `tick()`.
- **Output:**
  - one `demo_events` row and one `clock_changed` event per advance;
  - `became_overdue` is `0` on the step to 19:00 (19:00 is not before 19:00) and `1` on the `plus_1h` step;
  - the `tick()` writes a `job_runs` row (status `completed`, `overdue = 1`, `promises_missed = 1`), one `case_event`
    `overdue` for the case, and sets the promise status to `missed`;
  - a second `tick()` adds a `job_runs` row and no second `overdue` event.
- **Checked by prototype:** `promise_for(BILLING_DISPUTE, "nobody_online", Fri 09:24)` gives `R26.unstaffed`, due
  `2026-10-19 19:00-05:00`; `case_due_at` is the same instant.

### 1.2 Context

Wave 2, area A6 (DO-3 §8). The wave-2 context note (`.claude/state/resume.md`, "wave 2 context upkeep") says: **land AEA-30
first**, because the demo clock unblocks login on the integrated app, the strict contract run and J-1's steps. AEA-29
(`CaseService`) is still unmerged on `main` (its branch holds frozen tests only). It is called through one method by injection
and tested with a double. It is never imported.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-30.md` (= issue #30) | AC-1…AC-15; owned files; *Agent handoff* refusals |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-30 (blocked by 10, 11, 14; calls `CaseService` (29) by injection); §0a J-6/J-7 *proposed* 30; §3: `web/container.py` own hunk only, `tests/journeys/` one file per ticket per journey, context docs own row only, `domain/*` frozen (AEA-02) | Own hunk only; no edit to `domain/` |
| Component contracts (win over DO-4) | `docs/design/contracts/stage7/cases.md` §1.1, §1.2, §3.1 (`is_business_day`), §3.3, §5 rules table (due_state, lanes, unowned alert only on shift, promise missed "any case state"; `convert_live_queued(now, tx)`), **§6 (this ticket's classes)**, cross-topic A-2 | Exact signatures in §4 |
| Component contracts | `docs/design/contracts/internal-components.md` §13 (`Clock`, `UnitOfWork`, events rule), §14 (superseded by cases §6), §16 | `Clock.now()` tz-aware Chicago, never the wall clock |
| Staff addendum | `stage7/staff.md` §1 (`DemoRole`, `StaffActor`), §8 (CON-8 calls `advance_clock(step, actor=actor, request_id=ctx.request_id)`) | `demo_events.role = actor.role.value` |
| Web addendum | `stage7/web.md` §4 (one UTC wall clock, MC-20), §11 (demo-wide events once per open thread, in the writer's tx), §15 (`ContainerOverrides.wall_clock`, D-13) | Hunk reads `deps.WALL_CLOCK` |
| Graph addendum | `stage7/graph-core.md` line 681 row *cases A-2* ("Accepted (AEA-02 follow-up)"); cases.md line 866 A-2 (fallback: "If graph declines, these services return plain dicts shaped as the OpenAPI schema") | History only: the types now live in `domain/views.py` (AEA-02b) |
| View types (AEA-02b, merged `5305d57`) | `src/meridian/domain/views.py`: `StaffingView`, `StaffingChange`, `ClockView`, `ClockAdvanced` | Import them; define none (§4.2, §4.5) |
| Sibling plan | `docs/plans/fanout/2026-10-21-build/AEA-29.md` R-3 note, R-7, R-15, R-16; its Step 5 (`convert_live_queued`) | §8 R-2, R-16, R-17 |
| Data addendum | `stage7/data.md` §8a (`FixedClock`, DAT-32); residual R-G-9 | Tests use `FixedClock(...)`; one `SchedulerJob` per demo moment |
| Decision ledgers | `docs/plans/7b-decisions/cases.md` CAS-5, 10, 18, 20, 22, 23, 29; `merge-clashes.md` MC-13, MC-20; `residuals-web.md` R-W-17 | `ClockAdvanced` has no `date_label` |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` schemas `Staffing`, `StaffingResponse`, `StaffingRequest`, `DemoClock`, `ClockAdvanceResponse`, `EvStaffingChanged`, `EvClockChanged`, `Speaker`, `OversightResponse`, `Lane`, `QueueRow`; operations `setStaffing` (PUT `/api/demo/staffing`), `advanceDemoClock` (POST `/api/demo/clock`), `getOversight` (GET `/api/staff/oversight`), `switchRole` (PUT `/api/session/role`), `startChatSession`, `requestPerson` (POST `/api/chat/sessions/{thread_id}/handoff`) | Field names and label strings |
| UI contracts / screen specs (read only) | `UI_CONTRACTS.md` CON-7, CON-8; `SCREEN_SPECS.md` lines 30, 44, 130 | Labels "Nobody online" / "Simulated staff on shift (demo)"; banner from `policy/texts.py` |
| Code design | `docs/design/code-design.md` §2.1 (services never import other adapters), §4.4 rows for both modules, §6 S-8, S-19 (one in-process thread, no runner port), S-20 (no Protocols in front of our services; a not-yet-built service is reached through an **injected callable**) | `DeferredCases` wraps an injected callable |
| System design | `docs/design/system-design.md` §8.2 ("Runs every 60 s [A]; a missed run is caught up by the next one (idempotent)"), §9 *Growth* (SDQ-10: prune to 2 per thread, daily) | `TICK_INTERVAL_S = 60.0` [A] |
| Requirements | PRD R-3, R-30, R-33 | Clock never the server's; default nobody online |
| Evaluation plan (DO-5) | Ticket *Evaluation*: N/A (demo controls score nothing; R-33 is proven at AEA-52, CAP-5) | No eval case |
| Observability contract (DO-6) | `docs/design/observability-contract.md` rows WF-5, WF-7 | `demo_event` per change with `request_id`; `job_run` per tick; `job_run_id` on every case_event; IDs and counts only |
| Key-metrics registry (DO-7) | `docs/design/key-metrics-registry.md` M-13, M-18 (30-minute end rule, wall clock), M-27 | `abandoned` only by the 30-minute rule |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md` rule 6; workspace `code-design-solid-modularity.md`, `async-safety.md` §2 | Affected tests + fast gates + affected journeys; every thread names its closer |
| Merged neighbours (read only) | `web/routes/staff_clock.py` + `web/schemas/staff_clock.py` (AEA-47: `ClockStepName`, `ClockAdvanceResponse`, `from_attributes=True`), `services/reset.py` (AEA-31: `ResetClock` precedent; lazy `format_clock` import in `register_reset`), `web/container.py` hunks of AEA-42/44/46 (lazy `"demo_clock"` forwarders), `tests/journeys/support/` (AEA-57), `tests/contract/` (AEA-59) | §4 |
| Wave-2 audit | `.claude/state/resume.md` "Open findings (wave 2)" 1, 2, 8 | PA-8; gate 7 (strict contract count) |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer may create or edit)

| File | Change | What |
|---|---|---|
| `src/meridian/services/demo.py` | create | Constants, `format_clock`, `next_demo_time`, `DemoClock`, `LiveQueueConverter`, `DeferredCases` and `DemoService`; imports and re-exports the four view types from `domain/views.py` (§4.5) |
| `src/meridian/services/scheduler.py` | create | `TICK_INTERVAL_S`, `ABANDON_AFTER`, kind constants, `JobRun`, `SchedulerJob`, `SchedulerThread` (§4.6) |
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_demo`** (lines 495–499 on `dd1b110`) | §5 step 6 |
| `tests/services/demo_support.py` | create | Test helpers (builders, raw row readers, `CaseService` doubles). Not a test module |
| `tests/services/test_demo.py` | create | AC-1…AC-6, AC-12 (WF-5), worked pair, PA-4, PA-7, PA-9 |
| `tests/services/test_scheduler.py` | create | AC-7…AC-13 (WF-7), PA-2 |
| `tests/unit/services/test_format_clock.py` | create | AC-6 pure formatter, PA-5 |
| `tests/unit/services/test_demo_steps.py` | create | Pure step math (PA-3) |
| `tests/unit/services/test_demo_imports.py` | create | Import direction (PA-6) |
| `tests/unit/web/test_register_demo.py` | create | The hunk (PA-1, PA-7) |
| `tests/journeys/j6/test_aea_30.py` | create | AC-14, J-6 steps on the harness |
| `tests/journeys/j7/test_aea_30.py` | create | AC-14, J-7 steps on the harness (blocked today) |
| `docs/testing/journeys/<run-date>-AEA-30.md` | create (`<run-date>` = `date +%F` on the run day) | AC-14 record |
| `.claude/reference/area-map.md` | modify the Status cell of **the A6 row that already holds AEA-31's clause** (line 31 today) | AC-15 |
| `.claude/state/icm-progress.md` | modify **the A6 row** (line 32 on `dd1b110`) | AC-15 |
| `docs/design/code-design.md` | add **one** `**Built:**` line after the last one (line 192 on `dd1b110`) | AC-15 |

### 2.2 Shared surfaces you read and never edit

- AEA-10's storage: everything in `src/meridian/adapters/sqlite/` (incl. `repos_cases.py`, `repos_cases_state.py`,
  `repos_core.py`, `repos_core_aux.py`, `rows.py`, `db.py`, every `schema/*.sql`) and `src/meridian/adapters/checkpointer.py`.
- `src/meridian/domain/*` (AEA-02; `domain/views.py` is AEA-02b's), `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02).
- `src/meridian/policy/*` (AEA-01, AEA-03, AEA-13, AEA-14).
- AEA-23's web shell: `src/meridian/web/deps.py`, `web/middleware.py`, `web/app.py`, `web/logging.py`.
- `web/routes/*`, `web/schemas/*`, and every other `register_*` hunk in `web/container.py`.
- `src/meridian/services/reset.py` and the other existing services.
- Test infrastructure:
  - `tests/fakes/` (AEA-11) and `tests/fixtures/sqlite.py` (AEA-10);
  - `tests/conftest.py`, `tests/unit/web/test_container.py` and `tests/unit/test_import_direction.py` (AEA-01);
  - `tests/journeys/support/` (AEA-57) and `tests/contract/` (AEA-59);
  - the `tests/api/*_support.py` helpers.
- `pyproject.toml`, `uv.lock`.
- Signed and frozen documents: the OpenAPI, `UI_CONTRACTS.md`, `docs/ux/**`, `apps/web/**`, the briefing, issued data,
  `docs/archive/`, `docs/parked/`.

### 2.3 Owned by other tickets: do not create or implement

- AEA-29 / AEA-51: `CaseService` and every case lifecycle rule, `convert_live_queued` itself, the `register_cases` body, and
  the binding of `case_service`.
- AEA-31: `ResetService` and every caller of `demo_state.reset()`.
- AEA-32: the stale-tick `health_event` and the `scheduler_last_run` signal (CAS-22).
- The routes: CON-7 and the CON-8 read (AEA-43); the CON-8 advance (AEA-47, merged); `getOversight` (AEA-45).
- AEA-23: the `web/deps.py` keys and providers.
- AEA-02b (merged): the view types in `domain/views.py`. Never redefine one.
- AEA-29's open branch `aea-29-aea-29-cases-handoff` (frozen tests in `tests/services/test_cases.py`): never edit it.
- AEA-10: `StreamKey`, `StreamEvent`, `thread_stream`, `DEMO_START`.
- AEA-11: `FixedClock`.

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's, by ID) → implementation → verification

TD = `tests/services/test_demo.py`, TS = `tests/services/test_scheduler.py`. All of them run with
`uv run pytest tests/services/test_demo.py tests/services/test_scheduler.py tests/unit/services -q`.

| AC | Requirement (short; full text in the issue) | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `DemoClock.now()` tz-aware America/Chicago, read from `demo_state`, `DEMO_START` on a fresh store, never the server clock | `DemoClock` (§5 step 3) | TD `::test_clock_starts_at_demo_start`, `::test_clock_ignores_wall_clock` |
| AC-2 [failure/refusal] | Only forward by `plus_1h`, `plus_4h`, `next_business_morning` (Fri 10:00 → Mon 07:00; Wed 2026-11-25 → Mon 2026-11-30 07:00); any other step rejected; nothing moves | `next_demo_time`; `advance_clock` step 1 guard | TD `::test_advance_steps`, `::test_unknown_step_rejected`; `tests/unit/services/test_demo_steps.py` |
| AC-3 [invariant] | `became_overdue` = open cases with `old_now <= d < new_now`; `ClockAdvanced` has exactly `now`, `label`, `became_overdue`; one `demo_events` row (`clock_advanced`, `step`, `demo_before`, `demo_after`, `became_overdue`, `request_id`, `role = actor.role.value`) and one `clock_changed` per open chat, in one tx | `advance_clock` (§5 step 4) | TD `::test_advance_counts_became_overdue`; worked pair `::test_example_pair_con8_wf7` |
| AC-4 [invariant] | Default `nobody_online`; same mode writes nothing; off calls `convert_live_queued(now, tx)` once in the same tx and returns its count; one `demo_events` row (`staffing_changed`, `mode`, `converted_cases`, `request_id`, `role`) and `staffing_changed` to every open chat; a raising converter rolls everything back | `set_staffing` (§5 step 4) | TD `::test_staffing_default_and_toggle`, `::test_shift_end_commits_with_conversions` |
| AC-5 [negative] | Banner = the fixed `policy/texts.py` string, None while nobody online; never composed | `staffing()` uses `TEXTS[TextId.STAFFING_BANNER]` | TD `::test_staffing_banner_is_fixed_text` |
| AC-6 [invariant] | `format_clock(DEMO_START)` → ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)"); `clock_view`, `advance_clock` (label only) and `clock_changed` carry its output | `format_clock` (§5 step 1) | `tests/unit/services/test_format_clock.py::test_format_clock_demo_start`; TD `::test_views_use_format_clock` |
| AC-7 [invariant] | One `job_runs` row per `tick()` (UTC `+00:00` wall times, `demo_now`, `started` → `completed`/`failed` + `error_kind`, no free text; counts in `counts_json`); `job_run_id` on every case_event it writes | `SchedulerJob.tick` (§5 step 5) | TS `::test_tick_writes_job_run`, `::test_failed_tick_records_failed` |
| AC-8 [invariant] | **WF-7:** overdue (case due), missed (promise due), fee-bearing case due vs promise due, stuck waiting, due soon, unowned only on shift, P0 never overdue | tick alert rules (§5 step 5 table) | TS `::test_overdue_and_missed`, `::test_fee_bearing_case_due_vs_promise_due`, `::test_stuck_waiting`, `::test_due_soon`, `::test_unowned_only_on_shift`, `::test_p0_never_overdue` |
| AC-9 [invariant] | Idempotent catch-up: no duplicate alert per (case, kind, due/wake-up value) | `case_events.exists(case_ref, kind, key)` before each append | TS `::test_tick_idempotent` |
| AC-10 [invariant] | Abandonment sweep on the wall clock: `live` + `open` + `last_customer_wall_at <= wall_now − 30 min` → `abandoned`, ended at `last + 30 min`; 29 min stays open; eval/load/seed and set outcomes untouched; `JobRun.abandoned` = count | tick sweep step | TS `::test_abandonment_sweep` |
| AC-11 [invariant] | Prune once per wall-clock day through the injected callable; count in `JobRun.pruned` on that tick only | tick prune step | TS `::test_prune_once_per_day` |
| AC-12 [capture] | WF-5/WF-7 records carry IDs (`demo_event_id`, `request_id`; `job_runs` per tick; `case_ref` + `job_run_id` per alert; a case_event per promise status change) | §5 steps 4–5 | TD `::test_wf5_records`; TS `::test_wf7_records` |
| AC-13 [negative] | `job_runs`, `demo_events`, alert `case_event` rows hold IDs, kinds, statuses, counts and times only | detail dicts hold only ids and times | TS `::test_records_hold_no_pii` |
| AC-14 [journey] | J-7 (staffing on → live-queued; off → converted, `shift_ended`) and J-6 (clock advance → Overdue lane) in `tests/journeys/j7/test_aea_30.py`, `tests/journeys/j6/test_aea_30.py` on AEA-57's harness | §5 step 8 | `uv run pytest -m journey tests/journeys/j6/test_aea_30.py tests/journeys/j7/test_aea_30.py -rs --journey-record=AEA-30`. Expected **today**: J-6 steps "1 scheduler ran at start" and "2 supervisor advances the clock" **pass** at `integrated with a scripted model`; J-6 step "3 overdue lane" and every J-7 step are **blocked** (skipped, naming AEA-29, AEA-40, AEA-43, AEA-45) |
| AC-15 [regression/context] | Area-map A6 row, the A6 ICM row, the DO-3 `**Built:**` line | §5 step 9 | `git diff --name-only main...HEAD` lists exactly the §2.1 files |

### 3.2 Plan-added criteria (post them as one comment on issue #30 if the orchestrator allows; otherwise list them in the report)

| ID | Criterion | Why the issue needs it | Verified by |
|---|---|---|---|
| PA-1 | On an app with `app.state.web_shell`, `register_demo` provides `Key("demo_clock")`, `deps.DEMO_SERVICE` (`"demo_service"`), `Key("scheduler_job")` and `Key("scheduler_thread")`, built from `deps.UOW_FACTORY`, `Key("checkpointer")` and `deps.WALL_CLOCK`. The thread starts at `build()` and stops at `close()` **before** the checkpointer closes. Prune is called with `keep=2`. On a bare `FastAPI()` it provides nothing | The ticket names the hunk but no AC tests it | `tests/unit/web/test_register_demo.py::test_register_demo_wires_and_runs_the_thread`, `::test_register_demo_ignores_app_without_web_shell`, `::test_thread_stops_before_storage_closes` |
| PA-2 | `SchedulerThread` runs the first tick at once, then every interval. A raising tick is logged (exception type only) and the loop continues. `stop()` ends it within the timeout | System design §8.2 (catch-up after a restart); async-safety §2 (every thread names its closer) | TS `::test_scheduler_thread_runs_and_stops`, `::test_scheduler_thread_survives_a_raising_tick` |
| PA-3 | `next_demo_time` adds elapsed time (DST-safe); `next_business_morning` always lands on a later calendar date at 07:00; every step from any start moves strictly forward | AC-2 "no step moves it backwards" as a property, not a sample | `tests/unit/services/test_demo_steps.py::test_steps_from_examples`, `::test_plus_hours_is_elapsed_time_across_dst`, `::test_every_step_moves_forward`, `::test_unknown_step_raises` |
| PA-4 | Staffing labels and the `staffing_changed` lines are fixed constants: on = `TEXTS[TextId.STAFFING_CHANGED_ON_SHIFT]`, off = `STAFFING_CHANGED_OFF_LINE` | Copy gap: no signed wording for the "off" line (§8 R-4) | TD `::test_staffing_default_and_toggle` asserts both lines and labels |
| PA-5 | `format_clock` refuses a naive datetime; noon and midnight read "12:00 pm" / "12:00 am"; the OpenAPI examples reproduce | Formatter correctness at the edges | `tests/unit/services/test_format_clock.py::test_format_clock_examples`, `::test_format_clock_refuses_naive` |
| PA-6 | `services/demo.py` and `services/scheduler.py` import nothing from `meridian.web`, `meridian.agent`, `meridian.services.cases`, `meridian.services.handoff`, `meridian.adapters.checkpointer`, `meridian.adapters.models`, `sqlite3`, `anthropic`, `httpx`, `langgraph`, `langfuse`, `fastembed` | DO-3 §2.1 ("services never import other adapters"; prune is injected). Also, the four view types come from `meridian.domain.views` (AEA-02b): `meridian.services.demo.ClockView is meridian.domain.views.ClockView`, and the same for the other three | `tests/unit/services/test_demo_imports.py::test_demo_and_scheduler_import_direction`, `::test_view_types_come_from_domain_views` |
| PA-7 | `DeferredCases` resolves the case service only when `convert_live_queued` is called, never at construction. A container **without** `deps.CASE_SERVICE` builds and starts; turning staffing **on** works; turning it **off** fails with `RuntimeError("not bound: case_service")` and rolls back, so staffing stays on (fail closed, R-30) | `case_service` stays unbound until AEA-29/AEA-51; resolving it at build would break every app start | TD `::test_deferred_cases_resolves_at_call_time`; `tests/unit/web/test_register_demo.py::test_shift_end_without_case_service_fails_closed` |
| PA-8 | With this merge, `POST /api/login` through the real `build_container` answers 200, sets `mhc_session` and writes one `staff_sessions` row (wave-2 seam finding 1) | Login reads `Key("demo_clock")`, which only this hunk provides | `uv run pytest -m journey tests/journeys/j1/test_aea_57.py::test_j1_guards_and_login -rs -v` **passes** (before this merge it was skipped "blocked-on AEA-30"); `tests/api/test_staff_session_capture.py::test_wf4_session_entry_points_emit_records` passes through the real `register_demo` |
| PA-9 | AEA-47's merged route accepts our result unchanged: `ClockAdvanceResponse.model_validate(result, from_attributes=True).model_dump(mode="json")` gives exactly `{"now", "label", "became_overdue"}` with a `-05:00`/`-06:00` offset; `get_args(ClockStep) == CLOCK_STEP_NAMES` | The route and the service were built apart (MC-13, R-W-17) | TD `::test_advance_result_fits_con8_route` |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Clock never the server's (R-3) | PRD R-3; DO-4 §13 `Clock` | AC-1 | in-ticket | step 3 |
| One demo clock; forward only; reset returns to start | CON-8; cases §6 | AC-1, AC-2 | in-ticket (reset is AEA-31's, merged) | step 4 |
| Default nobody online (R-30) | PRD R-30; OD-1 | AC-4 | in-ticket | step 4 |
| `staffing_changed` / `clock_changed` once per **open** thread, in the writer's tx | web.md §11 | AC-3, AC-4 | in-ticket | step 4 |
| Event payload = the OpenAPI `Ev*` fields minus `event_id`, `type`, `at` (AEA-41's `chat_event_data` sends the stored payload unchanged) | OpenAPI `EvStaffingChanged`, `EvClockChanged`, `Speaker`; `web/schemas/events.py` | — | **added** (payloads fixed in §4.5) | step 4 |
| `demo_events.at_wall` needs a wall time; the signed `DemoService` constructor has none | cases §1.1 MC-20 | — | **added**: optional keyword `wall_clock` (§8 R-6) | steps 4, 6 |
| Prune day boundary | cases §1.1 ("Chicago is applied only for display, day bounds") | AC-11 | in-ticket (rule fixed here: Chicago date of the wall clock) | step 5 |
| `case_service` unbound until AEA-29/51 | cases §6; DO-3 S-20 | — | **added**: `DeferredCases` (PA-7) | steps 4, 6 |
| View types in `domain/` | cases A-2; graph-core line 681; AEA-02b (`domain/views.py`, merged) | *What to build* names them | in-ticket: imported from `meridian.domain.views` (D-P1 retired, T-1) | §4.5; PA-6 |
| Missed tick → `health_event` | DO-6 WF-7; CAS-22 | — | other-ticket: AEA-32 (merged; reads `job_runs.latest()`) | — |
| CAP-5 at the real CON-8 entry point and a running scheduler | DO-6 CAP-5 | AC-12 note | other-ticket: AEA-52 | — |
| R-33 end to end | PRD R-33 | Evaluation note | other-ticket: AEA-52; lanes on read: AEA-29/45 | — |
| Route role checks (supervisor-only advance) | OpenAPI `advanceDemoClock` x-roles | *Agent handoff* | other-ticket: AEA-47 (merged) | — |
| Staffing labels and the "off" line as fixed text | SCREEN_SPECS lines 30, 130; OpenAPI `Staffing.label` | — | **added** as constants in `services/demo.py` | step 4; §8 R-4 |
| No PII in WF-5/WF-7 records | coverage audit R-36 row (D-11) | AC-13 | in-ticket | step 5 |
| The scheduler thread has a closer, and it runs before storage closes | async-safety §2; AEA-10's hunk registers `checkpointer.close` inside its factory | — | **added** (PA-1, PA-2) | steps 5, 6 |
| Login on the integrated app | wave-2 seam finding 1 | — | **added** (PA-8) | step 6, gate 6 |
| Readiness check failing while a login key is unbound | wave-2 seam finding 1, second half | — | other-ticket: an AEA-23/32 follow-up (not this ticket's files) | — |
| AEA-01's stub test stays green | `tests/unit/web/test_container.py::test_every_register_stub_present` (skips hunks without "No-op until") | — | **added**: docstring drops "No-op until", keeps "AEA-30" | step 6 |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `SchedulerJob.tick()` on the 60 s thread started by `register_demo` | WF-7 | DO-6 WF-7 row | CAP-5 (AEA-52); M-13, M-27 |
| `DemoService.set_staffing` / `advance_clock` (behind CON-7 / CON-8: routes AEA-43, AEA-47) | WF-5 | DO-6 WF-5 row | CAP-5 (AEA-52); evaluation n/a (DO-6) |

---

## 4. Shared code to use (copied from `main` at `dd1b110`)

### 4.1 `web/container.py` (AEA-01) and `web/deps.py`, `web/middleware.py` (AEA-23)

```python
# meridian.web.container
class ContainerError(RuntimeError): ...   # messages: "not provided: <name>", "get after close: <name>", "already provided: <name>"
@dataclass(frozen=True)
class Key[T]:
    name: str                             # two keys are equal when their names are
class Container:
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...  # refused after build; twice → "already provided"
    def get[T](self, key: Key[T]) -> T: ...                                            # lazy, memoised; raises after close
    def on_start(self, starter: Callable[[], None]) -> None: ...  # refused after build; build() runs starters after every object
    def on_close(self, closer: Callable[[], None]) -> None: ...   # allowed until close(); closers run NEWEST FIRST
    def build(self) -> None: ...          # resolves EVERY provided factory, in provide order, then runs the starters
    def close(self) -> None: ...          # pops and runs closers; errors collected into an ExceptionGroup
def register_demo(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-30 demo: DemoClock, staffing, the scheduler job thread (cases.md §6).

    No-op until AEA-30 fills it.
    """
# build_container calls register_storage FIRST and register_demo 14th (after register_cases, before register_reset).

# meridian.web.deps
UOW_FACTORY: Key[UnitOfWorkFactory] = Key("uow_factory")     # provided by register_storage (AEA-10)
CASE_SERVICE: Key[Any] = Key("case_service")                 # NOT provided on main (AEA-29 / AEA-51)
DEMO_SERVICE: Key[Any] = Key("demo_service")                 # provided HERE; get_demo_service reads it
WALL_CLOCK: Key[Callable[[], datetime]] = Key("wall_clock")  # provided by register_web from shell.wall_clock (D-13 override)

# meridian.web.middleware
@dataclass(frozen=True)
class WebShellState:                       # app.state.web_shell, set by create_app
    settings: Settings
    wall_clock: Callable[[], datetime]
    public_paths: PublicPaths
class PublicPaths:
    def __init__(self) -> None: ...
```

- `container.py`'s module-level imports must not change (`tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`).
  The hunk imports inside its own function body, like every other hunk.
- `register_storage` provides `Key("checkpointer")`. Its factory calls `c.on_close(checkpointer.close)`, so that closer is
  registered **during `build()`**.
- Three merged hunks read `Key("demo_clock")` lazily through forwarders and raise `RuntimeError("not bound: demo_clock")`
  until this hunk provides it: `register_staff_session`, `register_person_request` and `register_staff_live`.
- `register_reset` imports `meridian.services.demo.format_clock` lazily.

### 4.2 Domain, ports, policy (AEA-02, AEA-03, AEA-14)

```python
# meridian.domain.common
class MeridianModel(BaseModel): ...       # extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
class ThreadId(_PatternId): ...  # UUID4 lower case      class RequestId(_PatternId): ...  # UUID4
class CaseRef(_PatternId): ...   # ^MHC-C-[0-9]{4}$       class CustomerId(_PatternId): ...  # ^MHC-[0-9]{5}$
class HandoffReason(StrEnum): ...         # SAFETY, BILLING_DISPUTE, FEE_BEARING_CHANGE, CUSTOMER_REQUESTED_PERSON, …
class Priority(StrEnum): ...              # P0 … P4
Presence = Literal["nobody_online", "simulated_on_shift"]   # line 303

# meridian.domain.staff
class DemoRole(StrEnum): CUSTOMER = "customer"; REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
class StaffRole(StrEnum): REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
class StaffActor(MeridianModel): role: StaffRole; name: str; signature: str
def actor_for(role: StaffRole) -> StaffActor: ...

# meridian.ports.runtime
class Clock(Protocol):
    def now(self) -> dt.datetime: ...
class UnitOfWork(Protocol): core: CoreRepos; …; cases: CaseRepos; …; def commit(self) -> None: ...
class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...

# meridian.policy.texts
TEXTS[TextId.SHIFT_ENDED]               == "The simulated shift ended before a representative joined."
TEXTS[TextId.STAFFING_CHANGED_ON_SHIFT] == "Staffing changed: simulated staff on shift (demo)."
TEXTS[TextId.STAFFING_BANNER]           == "Simulated staffing (demo). No Meridian employee is online."

# meridian.policy.handoff
HOLIDAYS_CLOSED: Final[frozenset[date]]    # includes date(2026, 11, 26), date(2026, 11, 27)
def is_business_day(d: date) -> bool: ...  # d.weekday() < 5 and d not in HOLIDAYS_CLOSED
DUE_SOON_WINDOW: Final = timedelta(hours=4)    # [A] CAS-20
UNOWNED_AFTER: Final = timedelta(minutes=30)   # [A] CAS-20
def promise_for(reason, presence, now, window_start=None) -> Promise: ...    # tests only
def case_due_at(reason, promise, window_start) -> datetime | None: ...       # tests only

# meridian.domain.views (AEA-02b, merged 5305d57): pure types; each field = the OpenAPI schema named beside it
class StaffingView(MeridianModel):   mode: Presence; label: str; banner: str | None          # = OpenAPI Staffing
class StaffingChange(MeridianModel): mode: Presence; label: str; converted_cases: int        # = OpenAPI StaffingResponse
class ClockView(MeridianModel):      now: dt.datetime; label: str; date_label: str           # = OpenAPI DemoClock
class ClockAdvanced(MeridianModel):  now: dt.datetime; label: str; became_overdue: int       # = OpenAPI ClockAdvanceResponse (R-W-17)
# The same module also holds QueueView, OversightView, ResetDone (AEA-29 / AEA-31's); this ticket uses only the four above.
```

**Writing IDs under mypy strict and the pydantic plugin (`init_typed = true`).** A model field typed `CaseRef` does not
accept a plain `str` literal under mypy. Use one of two forms:
- `CaseRow.model_validate({"case_ref": "MHC-C-0007", …})` with plain strings; or
- module-level `TypeAdapter`s (`THREAD: TypeAdapter[ThreadId] = TypeAdapter(ThreadId)`, then
  `THREAD.validate_python(str(uuid4()))`).

Never call `ThreadId("…")` directly. Enum fields take members (`HandoffReason.BILLING_DISPUTE`).

### 4.3 Storage (AEA-10, merged)

```python
# meridian.adapters.sqlite.db
def format_wall(dt: datetime) -> str: ...   # tz-aware → dt.astimezone(UTC).isoformat(); naive → ValueError("naive datetime")
BUSY_TIMEOUT_MS = 5000
# SqliteUnitOfWorkFactory(db_path): `with uow(write=True) as tx:` BEGIN IMMEDIATE; `with uow() as tx:` read-only (query_only).
# Leaving the block without tx.commit() rolls back; an exception inside the block rolls back and re-raises.

# meridian.adapters.sqlite.rows
StreamKey = NewType("StreamKey", str)
def thread_stream(thread_id: ThreadId) -> StreamKey: ...   # the bare thread id
class StreamEvent(MeridianModel): type: str (1..40 chars); payload: dict[str, JsonValue] = {}; at: datetime   # at = demo clock
class EventRow(MeridianModel): id: EventId; stream: str; type: str; payload: dict[str, JsonValue]; at: datetime
class ConversationRow(MeridianModel):
    thread_id: ThreadId; demo_session: str; run_tag: Literal["live", "eval", "load", "seed"]; run_id: str | None = None
    agent_version: str; started_at: datetime; started_wall_at: datetime | None = None
    staffing_at_start: Literal["nobody_online", "simulated_on_shift"] | None = None
    outcome: Literal["ai_resolved", "handed_off", "safety_reply", "abandoned", "open"] = "open"
    ended_wall_at: datetime | None = None; last_customer_wall_at: datetime | None = None
    controller: Controller = <ai>; live_state: Literal["not_live", "queued", "joined", "handed_back", "closed"] = "not_live"
    live_since: datetime | None = None
class CaseRow(MeridianModel):
    case_ref: CaseRef; thread_id: ThreadId; turn_id: TurnId | None = None; customer_id: CustomerId | None = None
    reason: HandoffReason; priority: Priority; rule_id: str; trigger: str
    lifecycle: Literal["live_queued", "unassigned", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved"]
    owner_role: StaffRole | None = None; owner_since: datetime | None = None
    due_at: datetime | None = None          # the CASE due (CAS-10)
    wake_up_at: datetime | None = None; version: int = 1; seed: bool = False; safety_kind: str | None = None
    change_request: dict[str, JsonValue] | None = None; alert: Literal["supervisor_now"] | None = None
    created_at: datetime; updated_at: datetime; resolved_at: datetime | None = None; queued_at: datetime | None = None
class CaseEventRow(MeridianModel):
    id: int | None = None; case_ref: CaseRef; kind: str (1..40 chars); key: str = ""
    actor_role: Literal["representative", "supervisor", "owner", "ai", "system"]
    job_run_id: str | None = None; detail: dict[str, JsonValue] = {}; at: datetime
class PromiseRow(MeridianModel):
    id: int; case_ref: CaseRef; promise: Promise; status: Literal["open", "kept", "missed", "changed"]
    created_at: datetime; status_at: datetime | None = None; status_reason: str | None = None
class DemoStateRow(MeridianModel): demo_now: datetime; staffing: Literal["nobody_online", "simulated_on_shift"]
class DemoEventRow(MeridianModel):
    demo_event_id: str; at_wall: datetime; kind: Literal["clock_advanced", "staffing_changed"]
    step: str | None = None; mode: str | None = None
    demo_before: str; demo_after: str      # clock: format_wall of the demo times; staffing: the modes
    became_overdue: int | None = None; converted_cases: int | None = None; request_id: str; role: str
class JobRunRow(MeridianModel):
    job_run_id: str; started_wall_at: datetime; finished_wall_at: datetime | None; demo_now: datetime
    status: Literal["started", "completed", "failed"]; error_kind: str | None; counts: dict[str, int | None]

# meridian.adapters.sqlite.repos_cases   (re-exports DEMO_START from repos_cases_state)
DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
CLOSED_LIFECYCLES = ("resolved", "closed_unresolved")

# Through a unit of work only (tx = what `with uow(...) as tx:` yields):
tx.cases.demo_state.get() -> DemoStateRow                  # no row → DemoStateRow(DEMO_START, "nobody_online"); demo_now comes back in UTC
tx.cases.demo_state.set_now(dt: datetime) -> None
tx.cases.demo_state.set_staffing(mode: str) -> None
tx.cases.demo_events.insert(row: DemoEventRow) -> None
tx.cases.job_runs.start(job_run_id: str, *, started_wall_at: datetime, demo_now: datetime) -> None
tx.cases.job_runs.finish(job_run_id: str, status: str, counts: Mapping[str, int | None], error_kind: str | None, *,
                         finished_wall_at: datetime | None = None) -> None   # ALWAYS pass finished_wall_at (else it reads datetime.now)
tx.cases.job_runs.latest() -> JobRunRow | None
tx.cases.cases.insert(row: CaseRow) -> None
tx.cases.cases.get(case_ref: CaseRef) -> CaseRow | None
tx.cases.cases.list_open() -> tuple[CaseRow, ...]         # lifecycle not in CLOSED_LIFECYCLES, by created_at, case_ref
tx.cases.cases.update_versioned(case_ref, expected_version, **changes) -> int | None   # columns incl. lifecycle, updated_at
tx.cases.case_events.append(event: CaseEventRow) -> int   # unique (case_ref, kind, event_key) when key != "" → StorageError
tx.cases.case_events.exists(case_ref: CaseRef, kind: str, key: str) -> bool
tx.cases.case_events.list_for_case(case_ref: CaseRef) -> tuple[CaseEventRow, ...]
tx.cases.promises.insert(case_ref: CaseRef, promise: Promise, at: datetime) -> int     # status 'open'
tx.cases.promises.current(case_ref: CaseRef) -> PromiseRow | None
tx.cases.promises.set_status(case_ref: CaseRef, status: str, at: datetime, reason: str) -> bool   # current row only
tx.cases.promises.list_open_past(now: datetime) -> list[PromiseRow]   # current rows, status 'open', due_at < now, any case state
tx.core.conversations.insert(row: ConversationRow) -> None
tx.core.conversations.lookup(thread_id: str) -> ConversationRow | EndedThread | None
tx.core.conversations.set_outcome(thread_id: ThreadId, outcome: str, *, ended_wall_at: datetime | None = None) -> None
tx.core.conversations.set_live_state(thread_id: ThreadId, live_state: str, live_since: datetime | None) -> None
tx.core.conversations.open_thread_ids() -> tuple[ThreadId, ...]   # live_state <> 'closed'
tx.core.conversations.idle_live(cutoff_wall: datetime) -> tuple[tuple[ThreadId, datetime], ...]
    # run_tag='live' AND outcome='open' AND last_customer_wall_at IS NOT NULL AND last_customer_wall_at <= cutoff
tx.core.messages.append(thread_id, role, text_redacted, at, *, turn_id=None, kind=None, card_id=None, choice_option=None) -> int
tx.core.events.append(stream: StreamKey, event: StreamEvent) -> EventId
tx.core.events.after(stream: StreamKey, last: EventId) -> list[EventRow]
tx.core.reads.customer(customer_id: CustomerId) -> CustomerRow | None   # .name, .phone, .email
tx.commit() -> None

# meridian.adapters.checkpointer (the container hunk only; services never import it)
class Checkpointer:
    def prune(self, keep: int = 2) -> int: ...   # opens its own connection; [Decided SDQ-10]
    def close(self) -> None: ...

# tests/fixtures/sqlite.py
@dataclass(frozen=True)
class TempStore: data_dir: Path; db_path: Path; issued_path: Path; uow: SqliteUnitOfWorkFactory
@contextmanager
def temp_sqlite(*, issued_path: Path = ISSUED_DB) -> Iterator[TempStore]: ...   # migrated copy of the issued DB, no seeds

# tests/fakes/clock.py
CHICAGO = ZoneInfo("America/Chicago"); WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=CHICAGO)
class FixedClock:
    def __init__(self, at: datetime = WORKED_PAIRS_NOW) -> None: ...   # Chicago ZoneInfo only
    def now(self) -> datetime: ...
    def advanced(self, by: timedelta) -> FixedClock: ...
```

### 4.4 Merged consumers this ticket must fit

```python
# meridian.web.schemas.staff_clock (AEA-47)
ClockStepName = Literal["plus_1h", "plus_4h", "next_business_morning"]
CLOCK_STEP_NAMES: Final[tuple[str, ...]] = get_args(ClockStepName)
class ClockAdvanceResponse(MeridianModel): now: dt.datetime; label: str; became_overdue: int
# meridian.web.routes.staff_clock: result = demo.advance_clock(body.step, actor=actor, request_id=ctx.request_id)
#                                  ClockAdvanceResponse.model_validate(result, from_attributes=True).model_dump(mode="json")
# meridian.web.schemas.events (AEA-41): chat_event_data(row) = {"event_id", "type", "at"} + the stored payload unchanged
#   (keys event_id/type/at in the payload are dropped)
```

### 4.5 What this ticket exports: `src/meridian/services/demo.py`

```python
"""The one demo clock, simulated staffing and the forward-only clock advance (stage7/cases.md §6; DO-3 §4.4)."""
from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, time, timedelta
from types import MappingProxyType
from typing import Final, Literal, Protocol, get_args
from zoneinfo import ZoneInfo

from pydantic import JsonValue                     # only to type the event payload dicts

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.rows import DemoEventRow, StreamEvent, thread_stream
from meridian.domain.common import Presence, RequestId
from meridian.domain.staff import DemoRole, StaffActor
from meridian.domain.views import ClockAdvanced, ClockView, StaffingChange, StaffingView   # AEA-02b; never redefine
from meridian.policy.handoff import is_business_day
from meridian.policy.texts import TEXTS, TextId
from meridian.ports.runtime import UnitOfWork, UnitOfWorkFactory
# Nothing else.

_CHICAGO: Final = ZoneInfo("America/Chicago")
BUSINESS_MORNING: Final = time(7, 0)    # [Source: OpenAPI advanceDemoClock "next business morning (Mon 7:00 am)"]

ClockStep = Literal["plus_1h", "plus_4h", "next_business_morning"]   # = OpenAPI ClockAdvanceRequest.step
CLOCK_STEPS: Final[tuple[str, ...]] = get_args(ClockStep)
STAFFING_MODES: Final[tuple[str, ...]] = get_args(Presence)

STAFFING_LABELS: Final[Mapping[str, str]] = MappingProxyType({
    "nobody_online": "Nobody online",                         # [Source: OpenAPI Staffing.label; SCREEN_SPECS line 30]
    "simulated_on_shift": "Simulated staff on shift (demo)",  # same sources
})
STAFFING_CHANGED_OFF_LINE: Final = "Staffing changed: nobody online."
# Provisional copy (plan §8 R-4): the specs give only the "on" line; this matches apps/web's dev fixture "staffing-off".

__all__ = [  # mypy strict needs __all__ to re-export; the four views are the SAME classes as meridian.domain.views'
    "BUSINESS_MORNING", "CLOCK_STEPS", "STAFFING_CHANGED_OFF_LINE", "STAFFING_LABELS", "STAFFING_MODES",
    "ClockAdvanced", "ClockStep", "ClockView", "DeferredCases", "DemoClock", "DemoService", "LiveQueueConverter",
    "StaffingChange", "StaffingView", "format_clock", "next_demo_time",
]
# The four demo views (cases A-2) belong to meridian.domain.views (AEA-02b). Never define a class with one of those
# names in this file (PA-6, test_view_types_come_from_domain_views).

def _utc_now() -> datetime:            # default wall clock for demo_events.at_wall ONLY; DemoClock never calls it.
    return datetime.now(UTC)           # Defined above DemoService (it is a default argument value).

def format_clock(dt: datetime) -> tuple[str, str]: ...
    # ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)"); the ONE formatter for CON-1, CON-8, clock_changed.
def next_demo_time(old: datetime, step: ClockStep) -> datetime: ...   # pure; §5 step 2

class DemoClock:                       # implements ports.runtime.Clock
    def __init__(self, uow: UnitOfWorkFactory) -> None: ...
    def now(self) -> datetime: ...     # demo_state.demo_now in America/Chicago; DEMO_START on a fresh store

class LiveQueueConverter(Protocol):    # the ONE CaseService method DemoService calls (stage7/cases §5)
    def convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int: ...
    # A typing aid: AEA-29's CaseService satisfies it structurally; this file never imports services/cases.py.

class DeferredCases:                   # PA-7; DO-3 S-20 ("an injected callable")
    """The case service, looked up when a shift ends rather than when the container builds.

    case_service is bound only once AEA-29 / AEA-51 land; resolving it at build time would stop every app start until
    then. An unbound case service fails the shift end (and rolls it back), never the boot.
    """
    def __init__(self, resolve: Callable[[], LiveQueueConverter]) -> None: ...   # stores resolve; calls nothing
    def convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int:
        return self._resolve().convert_live_queued(now, tx)

class DemoService:                     # stage7/cases §6 (CAS-18)
    def __init__(self, uow: UnitOfWorkFactory, clock: DemoClock, cases: LiveQueueConverter, *,
                 wall_clock: Callable[[], datetime] = _utc_now) -> None: ...
        # wall_clock: plan-added optional keyword (MC-20; §8 R-6), used only for demo_events.at_wall.
    def presence(self, tx: UnitOfWork | None = None) -> Presence: ...
    def staffing(self) -> StaffingView: ...
    def set_staffing(self, mode: Presence, *, request_id: RequestId, role: DemoRole) -> StaffingChange: ...
    def clock_view(self) -> ClockView: ...
    def advance_clock(self, step: ClockStep, *, actor: StaffActor, request_id: RequestId) -> ClockAdvanced: ...
```

Keep the `from datetime import … datetime …` import style exactly. AC-1's test patches `meridian.services.demo.datetime`.

**Event payloads.** Store them with `tx.core.events.append(thread_stream(thread_id), StreamEvent(...))`. AEA-41 sends them
unchanged after adding `event_id`, `type` and `at` from the row. Every demo event line has the speaker
`{"kind": "event", "display_name": None}` (OpenAPI `Speaker`: "Event lines have no name"). Build a **fresh dict per event**.

| Event `type` | `at` (StreamEvent) | `payload` |
|---|---|---|
| `staffing_changed` | demo now | `{"speaker": {"kind": "event", "display_name": None}, "staffing": {"mode": mode, "label": STAFFING_LABELS[mode], "banner": <TEXTS[TextId.STAFFING_BANNER] if mode == "simulated_on_shift" else None>}, "line": <on: TEXTS[TextId.STAFFING_CHANGED_ON_SHIFT]; off: STAFFING_CHANGED_OFF_LINE>}` |
| `clock_changed` | the new demo time | `{"speaker": {"kind": "event", "display_name": None}, "demo_clock": {"now": new.isoformat(), "label": label, "date_label": date_label}}` (from `format_clock(new)`; `new` is in Chicago) |

### 4.6 What this ticket exports: `src/meridian/services/scheduler.py`

```python
"""The 60 s background job: demo-clock alerts, missed promises, the wall-clock abandonment sweep and the daily
checkpoint prune (stage7/cases.md §6; DO-3 §4.4; system design §8.2). Demo-clock rules move only with the demo clock;
the sweep and the prune move only with the wall clock (MC-20, D-13)."""
from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Final, Literal
from zoneinfo import ZoneInfo

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.rows import CaseEventRow
from meridian.domain.common import MeridianModel
from meridian.policy.handoff import DUE_SOON_WINDOW, UNOWNED_AFTER
from meridian.ports.runtime import Clock, UnitOfWorkFactory

_log = logging.getLogger(__name__)
_CHICAGO: Final = ZoneInfo("America/Chicago")
TICK_INTERVAL_S: Final = 60.0                  # [A] system design §8.2 "Runs every 60 s"
ABANDON_AFTER: Final = timedelta(minutes=30)   # [Decided] DO-7 M-18 end rule, Innocent 2026-10-21 (CAS-29)
ALERT_KINDS: Final = ("overdue", "due_soon", "stuck_waiting", "unowned")
PROMISE_MISSED_KIND: Final = "promise_missed"
PROMISE_MISSED_REASON: Final = "past_due"      # promises.status_reason code (no free text)
ERROR_KINDS: Final = ("alerts_failed", "sweep_failed", "prune_failed")

class JobRun(MeridianModel):                   # internal, not serialised (cases §6, field for field)
    job_run_id: str
    started_wall_at: datetime
    finished_wall_at: datetime | None
    demo_now: datetime
    status: Literal["started", "completed", "failed"]
    error_kind: str | None
    overdue: int
    promises_missed: int
    due_soon: int
    stuck_waiting: int
    unowned: int
    abandoned: int
    pruned: int | None                         # set only on the once-a-day tick

@dataclass
class _Counts:                                 # private mutable tally; one per tick
    overdue: int = 0
    promises_missed: int = 0
    due_soon: int = 0
    stuck_waiting: int = 0
    unowned: int = 0
    abandoned: int = 0
    pruned: int | None = None
    def as_json(self) -> dict[str, int | None]: ...   # the seven keys above, in this order

def _utc_now() -> datetime:
    return datetime.now(UTC)

class SchedulerJob:                            # cases §6, constructor revised (CAS-29)
    def __init__(self, uow: UnitOfWorkFactory, cases: object, clock: Clock,
                 prune_checkpoints: Callable[[], int],
                 wall_clock: Callable[[], datetime] = _utc_now) -> None: ...
        # `cases` is the CaseService slot of cases §6, kept by name and position. The tick calls none of its methods
        # (every read and write goes through the unit of work, cases §1.2), so it is typed `object` and only stored (R-7).
    def tick(self) -> JobRun: ...

class SchedulerThread:                         # S-19: one in-process thread, no runner port
    def __init__(self, tick: Callable[[], object], *, interval_s: float = TICK_INTERVAL_S,
                 name: str = "meridian-scheduler") -> None: ...
    def start(self) -> None: ...               # daemon thread; a second start() raises RuntimeError("scheduler already started")
    def stop(self, timeout_s: float = 5.0) -> None: ...   # sets the stop event, joins; safe if never started; safe twice
    @property
    def alive(self) -> bool: ...
```

Container keys this ticket provides (name them in the hunk docstring):
- `Key[DemoClock]("demo_clock")`;
- `deps.DEMO_SERVICE` (`"demo_service"`);
- `Key[SchedulerJob]("scheduler_job")`;
- `Key[SchedulerThread]("scheduler_thread")`.

Keys consumed:
- `deps.UOW_FACTORY` and `Key("checkpointer")`, from AEA-10;
- `deps.WALL_CLOCK`, from AEA-23;
- `deps.CASE_SERVICE`, read **only at a shift end**, through `DeferredCases`.

---

## 5. Steps (build order; each step ends with a check)

**Module boundaries** (DO-3 §2.1, rule `code-design-solid-modularity`):
- Both new files are **services**. They reach storage only through `tx.<repo>.<method>`.
- They may import `adapters/sqlite` row types, `thread_stream` and `format_wall`. That is the allowed services → SQL edge,
  and `services/reset.py` and `services/live_chat.py` already use it.
- The interface this ticket implements is `Clock` (`DemoClock`).
- The interface it consumes from the sibling is one method (`LiveQueueConverter`), reached at runtime through
  `DeferredCases`.
- No other new seam: the runner thread is a concrete class (S-19 deferred).

### Step 0: environment and preconditions

0. **Starting point (T-2).** Work in the worktree the orchestrator gives you. If it is
   `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-30` on branch `aea-30-aea-30-demo-clock-sched`, with commits
   `5f4e879` and `339d410`:
   1. `git status --short` (in the worktree) must be clean. If it is not, stop and report: it is someone else's
      uncommitted work.
   2. `git merge --no-edit main`. Never rebase and never force-push.
      - Expected conflicts, resolved as the **union** (keep every other ticket's line, then add this ticket's):
        - `docs/design/code-design.md`: keep AEA-27's and AEA-28's `**Built:**` lines, and put AEA-30's after the last one;
        - `.claude/reference/area-map.md` and `.claude/state/icm-progress.md`: keep every other ticket's text in the A6
          cells.
      - A conflict anywhere else means `main` moved under this ticket (for example, `web/container.py` outside
        `register_demo`). Take `main`'s side outside `register_demo`, keep the branch's `register_demo`, and report it.
      - If git opens no editor, amend the merge commit's message so that its last line is the `Co-Authored-By` line
        (step 10). Never amend any other commit.
   3. Treat the branch's code and tests as a draft to check against this plan, **not** as evidence.
      - Go through steps 1–9, compare each with what is there, and fix any difference.
      - The known differences: step 9's context text still says "view types local until AEA-02b", and the test
        `test_view_types_come_from_domain_views` is missing.
      - Run every check in §7 on the merged head.

   If you are given a fresh worktree from `main` instead, build everything from steps 1–9. Do not cherry-pick from the
   old branch.
1. `export UV_LINK_MODE=hardlink`, then `uv sync`. Never copy a venv; no `node_modules` in this worktree.
2. Import check (no baseline suite):
   `uv run python -c "import meridian.adapters.sqlite.repos_cases, meridian.policy.handoff, meridian.web.deps, tests.fakes.clock, tests.fixtures.sqlite"`.
3. Confirm the merged names you call; report any drift (merged code wins over §4):
   `grep -n "def open_thread_ids\|def idle_live\|def set_outcome\|def set_live_state" src/meridian/adapters/sqlite/repos_core.py`;
   `grep -n "def exists\|def list_open_past\|def set_status\|def list_open\b" src/meridian/adapters/sqlite/repos_cases.py`;
   `grep -n "def start\|def finish\|def set_now\|def set_staffing" src/meridian/adapters/sqlite/repos_cases_state.py`;
   `grep -n "UOW_FACTORY\|CASE_SERVICE\|DEMO_SERVICE\|WALL_CLOCK" src/meridian/web/deps.py`.
4. `grep -n "^class ClockView\|^class ClockAdvanced\|^class StaffingView\|^class StaffingChange" src/meridian/domain/views.py`
   prints four lines (AEA-02b). Import those four types and never define them (T-1). Afterwards,
   `grep -n "^class \(ClockView\|ClockAdvanced\|StaffingView\|StaffingChange\)" src/meridian/services/demo.py` must print nothing.
5. Read `register_demo` in `src/meridian/web/container.py` (lines 495–499 on `dd1b110`). On `main` it must still be the stub; if another ticket
   filled it, stop and report.

### Step 1: `format_clock` (`services/demo.py`), for AC-6 and PA-5

1. `if dt.tzinfo is None or dt.utcoffset() is None: raise ValueError("format_clock needs a tz-aware datetime")`.
2. `local = dt.astimezone(_CHICAGO)`.
3. English names come from fixed tuples, never `%a`/`%b` (those follow the locale):
   - `_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")`, indexed by `local.weekday()`;
   - `_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")`, indexed by
     `local.month - 1`.
4. `hour12 = local.hour % 12 or 12`; `ampm = "am" if local.hour < 12 else "pm"`.
5. `date_part = f"{day} {month} {local.day}, {local.year}"` (day of month without a leading zero).
6. Return `(f"{date_part} · {hour12}:{local.minute:02d} {ampm}", f"{date_part} (demo date)")`. The separator is a space,
   U+00B7 MIDDLE DOT, then a space, byte for byte as the OpenAPI examples.

Invariant protected: one formatter. Every label in CON-1, CON-8 and `clock_changed` is this function's output.
Check: `uv run pytest tests/unit/services/test_format_clock.py -q`.

### Step 2: `next_demo_time(old, step)` (pure), for AC-2 and PA-3

1. If `step not in CLOCK_STEPS`, raise `ValueError("unknown clock step")`. Put no value in the message.
2. If `old` is naive, raise `ValueError("next_demo_time needs a tz-aware datetime")`.
3. `plus_1h` / `plus_4h` add **elapsed** time: `(old.astimezone(UTC) + timedelta(hours=n)).astimezone(_CHICAGO)`. This is
   the same rule as `FixedClock.advanced`; adding to the local wall time would land an hour off across 2026-11-01.
4. `next_business_morning`:
   - `d = old.astimezone(_CHICAGO).date() + timedelta(days=1)`;
   - `while not is_business_day(d): d += timedelta(days=1)`;
   - return `datetime.combine(d, BUSINESS_MORNING, tzinfo=_CHICAGO)`.

   Decided here: the result is always a **later calendar date**, so the step moves forward even before 07:00 (Mon 06:00 →
   Tue 07:00). Examples:
   - Fri 2026-10-16 10:00 → Mon 2026-10-19 07:00;
   - Wed 2026-11-25 → Mon 2026-11-30 07:00 (Thu 26 and Fri 27 are in `HOLIDAYS_CLOSED`; Sat and Sun are not business days).

Invariant protected: every result is strictly later than `old`.
Check: `uv run pytest tests/unit/services/test_demo_steps.py -q`.

### Step 3: `DemoClock`, for AC-1

1. `__init__` stores the factory only. No read at construction, and no module-level instance.
2. `now()`: `with self._uow() as tx: row = tx.cases.demo_state.get()`, then return `row.demo_now.astimezone(_CHICAGO)`. This
   is a read-only unit of work with no commit.
3. Nothing in the class touches `datetime.now`, `datetime.utcnow`, `date.today` or `time.time`.

Invariant protected: R-3 (the demo clock is the database row, never the server clock).

### Step 4: `DeferredCases` and `DemoService`, for AC-2…AC-6, AC-12, PA-4, PA-7 and PA-9

**`DeferredCases`.** `__init__` stores `resolve` and calls nothing. `convert_live_queued(now, tx)` calls `self._resolve()`
once per call, forwards both arguments unchanged, returns the result and lets every exception propagate.

**`presence(tx=None)`.** With `tx`, return `tx.cases.demo_state.get().staffing`. Without `tx`, open its own read unit of
work and do the same read. AEA-29's `HandoffService` calls it inside its write transaction, so a shift end cannot
interleave.

**`staffing()`.** `mode = self.presence()`; return `StaffingView(mode=mode, label=STAFFING_LABELS[mode],
banner=_banner(mode))`. `_banner(mode)` returns `TEXTS[TextId.STAFFING_BANNER]` for `"simulated_on_shift"` and `None`
otherwise (AC-5).

**`clock_view()`.** `now = self._clock.now()`; `label, date_label = format_clock(now)`; return
`ClockView(now=now, label=label, date_label=date_label)`.

**`set_staffing(mode, *, request_id, role)`** runs in one transaction:
1. `if mode not in STAFFING_MODES: raise ValueError("unknown staffing mode")`, before opening anything.
2. `with self._uow(write=True) as tx:`
3. `state = tx.cases.demo_state.get()`; `now = state.demo_now.astimezone(_CHICAGO)`; `before = state.staffing`.
4. `if before == mode: return StaffingChange(mode=mode, label=STAFFING_LABELS[mode], converted_cases=0)`. No write and no
   commit (CON-7 "Idempotent"; AC-4).
5. `tx.cases.demo_state.set_staffing(mode)`.
6. `converted = 0`. If `before == "simulated_on_shift" and mode == "nobody_online"`, set
   `converted = self._cases.convert_live_queued(now, tx)`.
   - Call it exactly once, with **this** `tx`, so the conversions commit with the shift end (R-30: zero live-queued while
     nobody is online).
   - Any exception propagates, including `RuntimeError("not bound: case_service")` from an unbound `DeferredCases`. The
     unit of work then rolls back, so staffing, events and `demo_events` stay as they were (AC-4, PA-7).
7. For each `thread_id in tx.core.conversations.open_thread_ids()`, call
   `tx.core.events.append(thread_stream(thread_id), StreamEvent(type="staffing_changed", at=now, payload=<§4.5 table>))`.
   This runs after step 6, so an affected chat sees `shift_ended` (written by the converter) before `staffing_changed`.
8. Insert the `demo_events` row:
   `tx.cases.demo_events.insert(DemoEventRow(demo_event_id=str(uuid.uuid4()), at_wall=self._wall_clock(),
   kind="staffing_changed", step=None, mode=mode, demo_before=before, demo_after=mode, became_overdue=None,
   converted_cases=converted, request_id=str(request_id), role=role.value))`.
9. `tx.commit()`; return `StaffingChange(mode=mode, label=STAFFING_LABELS[mode], converted_cases=converted)`.

**`advance_clock(step, *, actor, request_id)`** runs in one transaction:
1. `if step not in CLOCK_STEPS: raise ValueError("unknown clock step")`, **before** opening a unit of work. AC-2: a rejected
   step leaves `demo_state`, `demo_events` and `events` unchanged.
2. Open `with self._uow(write=True) as tx:`, then:
   - `old = tx.cases.demo_state.get().demo_now.astimezone(_CHICAGO)`;
   - `new = next_demo_time(old, step)`;
   - `if new <= old: raise RuntimeError("clock step did not move forward")`. This guards the never-backwards invariant at
     the write.
3. `tx.cases.demo_state.set_now(new)`.
4. `became = sum(1 for c in tx.cases.cases.list_open() if c.due_at is not None and old <= c.due_at < new)`.
   - This uses the **case** due (`cases.due_at`).
   - "Open" means not resolved and not closed_unresolved, which `list_open` already excludes.
   - Aware datetimes compare correctly across UTC and Chicago.
5. `label, date_label = format_clock(new)`. For each open thread, append
   `StreamEvent(type="clock_changed", at=new, payload=<§4.5 table>)`.
6. Insert the `demo_events` row (MC-13):
   `tx.cases.demo_events.insert(DemoEventRow(demo_event_id=str(uuid.uuid4()), at_wall=self._wall_clock(),
   kind="clock_advanced", step=step, mode=None, demo_before=format_wall(old), demo_after=format_wall(new),
   became_overdue=became, converted_cases=None, request_id=str(request_id), role=actor.role.value))`.
7. `tx.commit()`; return `ClockAdvanced(now=new, label=label, became_overdue=became)`. That is three fields only (R-W-17),
   and `now` is in Chicago, so AEA-47's route renders `-05:00`/`-06:00`.

The service does **not** check the actor's role (AEA-47's route does), and it writes no due state (due states are
recomputed on read).
Check: `uv run pytest tests/services/test_demo.py -q`.

### Step 5: `SchedulerJob.tick()` and `SchedulerThread`, for AC-7…AC-13 and PA-2

**`__init__`.** Store every argument. Set `self._pruned_on: date | None = None`, so the first tick of a process prunes
(catch-up after a restart; prune is idempotent).

`tick()` runs three short write transactions plus one injected call:
1. Set up:
   - `wall_start = self._wall_clock()`;
   - `demo_now = self._clock.now()`;
   - `job_run_id = str(uuid.uuid4())`;
   - `counts = _Counts()`.
2. **Start row** (own transaction):
   `with self._uow(write=True) as tx: tx.cases.job_runs.start(job_run_id, started_wall_at=wall_start, demo_now=demo_now);
   tx.commit()`. An exception here propagates: no row exists to mark failed, and the thread logs it.
3. `step = "alerts"`; then `try:`

   a. **Alerts** run in their own write transaction on the demo clock, with `n = demo_now`. Keep local per-kind tallies
      and copy them into `counts` **only after** `tx.commit()`.
      - Read `staffing = tx.cases.demo_state.get().staffing`.
      - For each `c in tx.cases.cases.list_open()`, apply the table below in row order. For each row whose condition holds:
        - `key = format_wall(<value>)`;
        - if `not tx.cases.case_events.exists(c.case_ref, kind, key)`, append
          `CaseEventRow(case_ref=c.case_ref, kind=kind, key=key, actor_role="system", job_run_id=job_run_id,
          detail={<value name>: key}, at=n)` and add 1 to that kind's tally.

      | kind | condition | value (key) and detail |
      |---|---|---|
      | `overdue` | `c.due_at is not None and c.due_at < n` | `c.due_at`; detail `{"due_at": key}` |
      | `due_soon` | `c.due_at is not None and n <= c.due_at <= n + DUE_SOON_WINDOW` | `c.due_at`; detail `{"due_at": key}` |
      | `stuck_waiting` | `c.lifecycle == "waiting" and c.wake_up_at is not None and c.wake_up_at < n` | `c.wake_up_at`; detail `{"wake_up_at": key}` |
      | `unowned` | `staffing == "simulated_on_shift" and c.lifecycle == "unassigned" and c.owner_role is None and n - c.created_at >= UNOWNED_AFTER` | `c.created_at`; detail `{"created_at": key}` |

      Then the promises. For each `p in tx.cases.promises.list_open_past(n)`:
      - if `tx.cases.promises.set_status(p.case_ref, "missed", n, PROMISE_MISSED_REASON)` is `True`, add 1 to the
        `promises_missed` tally;
      - `due = p.promise.due_at`; `assert due is not None` (list_open_past returns dated rows only; the assert is for
        mypy); `key = format_wall(due)`;
      - if not `exists(p.case_ref, PROMISE_MISSED_KIND, key)`, append `CaseEventRow(case_ref=p.case_ref,
        kind=PROMISE_MISSED_KIND, key=key, actor_role="system", job_run_id=job_run_id, detail={"promise_id": p.id,
        "due_at": key}, at=n)`.

      Invariants protected:
      - Overdue uses the **case** due and missed uses the **promise** due (CAS-10): a fee-bearing case due at its window
        start goes overdue while its promise stays open.
      - A case with no due (a P0 safety case, a live-queued case) never goes overdue or due soon.
      - There is one event per (case, kind, value), so a catch-up tick after a gap writes nothing twice. The unique index
        `ux_case_events_key` is the backstop.
      - `unowned` alerts are written only while staffed (cases §5 rules table).
      - The detail holds IDs and times only (AC-13).

   b. `step = "sweep"`. **Abandonment** runs in its own write transaction, on the wall clock.
      - `cutoff = wall_start - ABANDON_AFTER`.
      - For each `(thread_id, last) in tx.core.conversations.idle_live(cutoff)`, call
        `tx.core.conversations.set_outcome(thread_id, "abandoned", ended_wall_at=last + ABANDON_AFTER)` and count it.
      - Commit, then set `counts.abandoned`.
      - It writes only `abandoned`, never another outcome (cases A-7). `idle_live` already excludes eval/load/seed threads
        and outcomes that are already set.

   c. `step = "prune"`. **Prune** runs once per wall-clock day.
      - `today = wall_start.astimezone(_CHICAGO).date()` (Chicago day bounds, cases §1.1).
      - If `self._pruned_on != today`: `counts.pruned = self._prune_checkpoints()`, then `self._pruned_on = today`. Set the
        day only after success.

   d. `status, error_kind = "completed", None`.

   `except Exception as exc:` set `status, error_kind = "failed", f"{step}_failed"`.
   - The values are `alerts_failed`, `sweep_failed` or `prune_failed`: a fixed vocabulary, never the exception text.
   - Log once (below).
   - Counts of steps that committed are kept; the failed step's counts stay as they were.
4. `wall_end = self._wall_clock()`. **Finish row** (own transaction):
   `tx.cases.job_runs.finish(job_run_id, status, counts.as_json(), error_kind, finished_wall_at=wall_end)`, then commit.
5. Return `JobRun(job_run_id=job_run_id, started_wall_at=wall_start, finished_wall_at=wall_end, demo_now=demo_now,
   status=status, error_kind=error_kind, overdue=counts.overdue, promises_missed=counts.promises_missed,
   due_soon=counts.due_soon, stuck_waiting=counts.stuck_waiting, unowned=counts.unowned, abandoned=counts.abandoned,
   pruned=counts.pruned)`. Pass each field explicitly; never `**dict`.

`SchedulerJob` writes `job_runs` and the case and conversation rows above only. It writes **no** `health_event` (AEA-32,
CAS-22).

**Logging** follows `services/reset.py`'s style: a fixed message, with `extra` holding IDs and kinds only. AEA-23's
allow-list formatter reduces unknown records to their length.
- Failed tick step: `_log.warning("scheduler tick step failed", extra={"job_run_id": job_run_id, "error_kind": error_kind,
  "exc_type": type(exc).__name__})`.
- Thread loop: `_log.warning("scheduler tick raised", extra={"exc_type": type(exc).__name__})`.
- Never `exc_info`, never `str(exc)`, never message text or a customer value.

**`SchedulerThread`:**
1. `__init__` stores `tick`, `interval_s` and `name`, plus `self._stop = threading.Event()` and
   `self._thread: threading.Thread | None = None`. Nothing starts at construction.
2. `start()`: if a thread was already created, raise `RuntimeError("scheduler already started")`. Otherwise create
   `threading.Thread(target=self._run, name=self._name, daemon=True)` and start it.
3. `_run()` loops:
   - `try: self._tick()` / `except Exception as exc:` log as above;
   - then `if self._stop.wait(self._interval_s): return`.

   The first tick runs at once (system design §8.2: a missed run is caught up by the next).
4. `stop(timeout_s=5.0)`: `self._stop.set()`; if a thread exists, `join(timeout_s)`. It is safe to call twice or without
   `start()`.
5. `alive`: `self._thread is not None and self._thread.is_alive()`.

Check: `uv run pytest tests/services/test_scheduler.py -q`.

### Step 6: the `register_demo` hunk in `src/meridian/web/container.py`, for PA-1, PA-7 and PA-8

Edit **only** this function. Keep its name and parameters. Replace its docstring and empty body with:

```python
def register_demo(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-30 demo: DemoClock, staffing, the scheduler job thread (cases.md §6).

    Provides Key("demo_clock") (the one Clock every service and node receives), deps.DEMO_SERVICE ("demo_service",
    behind get_demo_service), Key("scheduler_job") and Key("scheduler_thread"). Reads deps.UOW_FACTORY and
    Key("checkpointer") (AEA-10) and deps.WALL_CLOCK (AEA-23); reaches deps.CASE_SERVICE (AEA-29 / AEA-51) only when a
    shift ends, and until it is bound that shift end raises RuntimeError("not bound: case_service") and rolls back. The
    thread starts after every object is built and stops before storage closes. An app that create_app did not build has
    no web shell, so this does nothing.
    """
    from meridian.adapters.checkpointer import Checkpointer
    from meridian.services.demo import DeferredCases, DemoClock, DemoService, LiveQueueConverter
    from meridian.services.scheduler import SchedulerJob, SchedulerThread
    from meridian.web import deps
    from meridian.web.middleware import WebShellState

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return

    clock_key = Key[DemoClock]("demo_clock")
    job_key = Key[SchedulerJob]("scheduler_job")
    thread_key = Key[SchedulerThread]("scheduler_thread")

    def resolve_cases() -> LiveQueueConverter:
        try:
            found: LiveQueueConverter = container.get(deps.CASE_SERVICE)
        except ContainerError as exc:
            if str(exc) == f"not provided: {deps.CASE_SERVICE.name}":
                raise RuntimeError(f"not bound: {deps.CASE_SERVICE.name}") from None
            raise
        return found

    cases = DeferredCases(resolve_cases)  # PA-7: resolved at a shift end, never at build

    def build_demo(c: Container) -> DemoService:
        return DemoService(c.get(deps.UOW_FACTORY), c.get(clock_key), cases, wall_clock=c.get(deps.WALL_CLOCK))

    def build_job(c: Container) -> SchedulerJob:
        checkpointer = c.get(Key[Checkpointer]("checkpointer"))
        return SchedulerJob(
            c.get(deps.UOW_FACTORY),
            cases,  # the cases §6 slot; the tick never calls it
            c.get(clock_key),
            lambda: checkpointer.prune(keep=2),  # SDQ-10: keep 2
            c.get(deps.WALL_CLOCK),
        )

    container.provide(clock_key, lambda c: DemoClock(c.get(deps.UOW_FACTORY)))
    container.provide(deps.DEMO_SERVICE, build_demo)
    container.provide(job_key, build_job)
    container.provide(thread_key, lambda c: SchedulerThread(c.get(job_key).tick))

    def start_thread() -> None:
        thread = container.get(thread_key)
        container.on_close(thread.stop)  # registered after build → runs before checkpointer.close (newest first)
        thread.start()

    container.on_start(start_thread)
```

Why each line is there:
- **The web-shell guard.** It matches every other filled hunk. `deps.WALL_CLOCK` exists only when `register_web` saw the
  shell. The docstring no longer says "No-op until", so `test_every_register_stub_present` skips this hunk; keep the token
  `AEA-30` (the same test checks it).
- **`resolve_cases`.** `build()` resolves every factory, and `case_service` is unbound on `main`, so a direct
  `c.get(deps.CASE_SERVICE)` would break every app start. The `RuntimeError("not bound: …")` form is what AEA-59's contract
  driver and the harness treat as "blocked", not "broken".
- **`container.on_close(thread.stop)` inside the starter.** AEA-10's checkpointer factory calls
  `c.on_close(checkpointer.close)` while `build()` runs. A closer registered at hunk time would be older and would run
  **after** the checkpointer closed. Registered in the starter, it is newer and runs first.
- **Tests that suppress starters** (`tests/api/web_shell_support.py::suppress_container_starters`) never start the thread
  and never register its closer. That is correct: nothing to stop.
- If binding needs any edit to `web/deps.py`, `web/app.py` or `web/middleware.py`, do not make it: report it.

Check: `uv run pytest tests/unit/web tests/unit/test_import_direction.py -q`.

### Step 7: tests (§7.1), written alongside steps 1–6

Iterate with `uv run pytest tests/services/test_demo.py tests/services/test_scheduler.py tests/unit/services tests/unit/web/test_register_demo.py -q`.

### Step 8: journeys and record (AC-14, PA-8)

1. Write `tests/journeys/j6/test_aea_30.py` and `tests/journeys/j7/test_aea_30.py` (§7.1).
2. Run `uv run pytest -m journey tests/journeys/j6/test_aea_30.py tests/journeys/j7/test_aea_30.py -rs --journey-record=AEA-30`.
   - Expected: `test_j6_scheduler_ran_at_start` and `test_j6_clock_advance_on_the_real_server` **pass**;
     `test_j6_case_in_overdue_lane` is skipped as blocked (AEA-29, AEA-45). Each J-6 step is its own test function (§7.1),
     so the blocked step never hides the passing ones.
   - `test_j7_shift_end_converts_queued_case` is skipped as blocked (its first step needs `setStaffing`, AEA-43).
   - The `--journey-record` flag writes `docs/testing/journeys/<run-date>-AEA-30.md`.
3. Run `uv run python -m tests.journeys.affected --base main`. Any change under `tests/journeys/` selects **every** journey.
   - All must pass or be skipped as blocked, except the known pre-existing red listed in §7.2.
   - Confirm that J-1's "3 login" steps now **pass** (PA-8): `-rs` shows them no longer skipped with "blocked-on AEA-30".
4. Edit the generated record (§7.4): replace the `Claim`, `Remaining limitations` and `Journeys that will exercise this
   code` cells, and append the service-level result line to `Result`. Keep the generated `Level`, `Tested revision`,
   `Environment`, `Command`, `Evidence location` and `Blocked by` cells.

### Step 9: context docs (AC-15; `context-maintenance.md` rule 6; slice plan §3 "each ticket changes only its own row")

- **`.claude/reference/area-map.md`.** In the **A6** row whose Status cell already contains
  `services/reset.py actual (AEA-31, …)` (line 31 today), insert this ticket's clause before "; the rest planned":
  `; services/demo.py, services/scheduler.py actual (AEA-30, <feat sha>; signatures stage7/cases §6; view types from
  domain/views.py, AEA-02b)`. On the existing branch, replace the clause it already wrote ("view types local until
  AEA-02b") with this one, and update the sha.
  - Leave the older duplicate A6 row (line 32) alone; wave-2 finding 9 owns that cleanup.
  - If only one A6 row exists by then, edit that one.
- **`.claude/state/icm-progress.md`.** Replace the A6 row (line 32 on `dd1b110`; find it with `grep -n 'area map A6' .claude/state/icm-progress.md`; it starts
  `| Routes verified against code and tests | provisional | 2026-10-21: area map A6 →`) with:
  `| Routes verified against code and tests | provisional | 2026-10-21: area map A6 → `services/reset.py` (AEA-31, `8192d2b`; 26 pass in `tests/services/test_reset.py`), `services/demo.py`, `services/scheduler.py` (AEA-30, `<sha>`; <N> pass in `tests/services/test_demo.py`, `test_scheduler.py`) | Integrated level when AEA-43, AEA-45, AEA-50, AEA-52 land |`.
  Keep it ≤ 400 characters (check with `awk 'NR==<that line>{print length($0)}' .claude/state/icm-progress.md`) and touch no other row.
- **`docs/design/code-design.md`.** Directly after the last `**Built:**` line (line 192 on `dd1b110`; find it with
  `grep -n '^\*\*Built:\*\*' docs/design/code-design.md | tail -1`), add one line:
  ``**Built:** `services/demo.py`, `services/scheduler.py` (AEA-30, `<sha>`; signatures stage7/cases.md §6; the four demo view types are imported from `domain/views.py`, AEA-02b).``
  On the existing branch, replace the line it already added, which ends "…are local until AEA-02b).".
  Make no other edit.

### Step 10: gates and commit

Run §7.3's gates once, cheapest first, and paste the results in the report. Then:
1. Stage and commit the code:
   `git add src/meridian/services/demo.py src/meridian/services/scheduler.py src/meridian/web/container.py tests/services/demo_support.py tests/services/test_demo.py tests/services/test_scheduler.py tests/unit/services/test_format_clock.py tests/unit/services/test_demo_steps.py tests/unit/services/test_demo_imports.py tests/unit/web/test_register_demo.py tests/journeys/j6/test_aea_30.py tests/journeys/j7/test_aea_30.py`.
   Commit as `feat(demo): demo clock, staffing, scheduler job (AEA-30)`, with a body listing the ACs and PAs.
2. Stage and commit the docs:
   `git add docs/testing/journeys/<run-date>-AEA-30.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`.
   Commit as `docs(AEA-30): journey record and context for services/demo.py, services/scheduler.py`.
3. Every commit message ends with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
4. Never `git add -A`. Do not push (only the merge step pushes `main`), and never force-push.

---

## 6. Data and fixtures (synthetic or issued only)

- **Store.** Every service test opens `temp_sqlite()` (AEA-10): a temp copy of the issued scheduling DB with every
  `schema/*.sql` applied and **no seeds**, so cases exist only when a test inserts them. Each test module has:
  ```python
  @pytest.fixture
  def store() -> Iterator[TempStore]:
      with temp_sqlite() as s:
          yield s
  ```
- **IDs** (in `demo_support.py`):
  - module-level adapters `THREAD = TypeAdapter(ThreadId)`, `CASE_REF = TypeAdapter(CaseRef)`,
    `REQUEST = TypeAdapter(RequestId)`, `CUSTOMER = TypeAdapter(CustomerId)`;
  - `new_thread_id() -> ThreadId` (`THREAD.validate_python(str(uuid4()))`) and `new_request_id() -> RequestId`.
- **Clocks:**
  - `chi(y, m, d, h, mi=0)` → `datetime(..., tzinfo=CHICAGO)` (`CHICAGO` from `tests/fakes/clock.py`);
  - scheduler tests use `FixedClock(at)` with **one `SchedulerJob` per demo moment** (R-G-9);
  - wall clocks are a small mutable `WallClock` class in `demo_support.py` (attribute `now: datetime`; `__call__` returns it;
    constructor refuses a naive or non-UTC value).
- **Conversations:**
  `ConversationRow.model_validate({"thread_id": str(tid), "demo_session": "test-session", "run_tag": run_tag,
  "agent_version": "test", "started_at": DEMO_START, "outcome": outcome, "last_customer_wall_at": last, "live_state":
  live_state})`.
- **The example-pair case (MHC-C-0007 shape):**
  - `reason=HandoffReason.BILLING_DISPUTE`, `priority=Priority.P3`, `lifecycle="unassigned"`, `owner_role=None`;
  - `created_at=updated_at=chi(2026,10,16,9,24)`, `rule_id="R24.billing_dispute"`, `trigger="planner"`, `seed=False`;
  - promise `promise_for(HandoffReason.BILLING_DISPUTE, "nobody_online", created_at)` (→ `R26.unstaffed`, due Mon 2026-10-19
    19:00); case due `case_due_at(reason, promise, None)`;
  - `case_ref="MHC-C-0007"`.

  Insert the case, then `tx.cases.promises.insert(case_ref, promise, created_at)`. Assert the built promise's
  `due_at == chi(2026,10,19,19,0)`, so a change in AEA-14's table fails loudly here.
- **Fee-bearing case:** `FEE_BEARING_CHANGE`, `P2`, window start Fri 2026-10-16 12:00.
  - Promise: `promise_for(FEE_BEARING_CHANGE, "nobody_online", chi(2026,10,16,10,0), window_start=chi(2026,10,16,12,0))`,
    due Mon 19:00 (prototyped).
  - Case due: `case_due_at(...)` = Fri 12:00.
  - Assert both values in the test.
- **P0 safety case:** `SAFETY`, `P0`, promise `promise_for(SAFETY, "nobody_online", …)` (`R26.safety_none`, due None),
  `due_at=None`.
- **PII seed for AC-13:** customer `MHC-10002` from the issued DB.
  - Read the name, phone and email at test time with `tx.core.reads.customer(CUSTOMER.validate_python("MHC-10002"))`.
  - **Never type the phone number, the name or the email into a test file** (project rule).
  - Store one customer message `f"Hi, this is {customer.name}, call me on {customer.phone}"` with
    `tx.core.messages.append(thread_id, "customer", text, at)` on the case's thread, and set `customer_id` on the case.
  - Assert `len([ch for ch in customer.phone if ch.isdigit()]) == 10`, so the check means something.
- **Doubles for `CaseService` (in `demo_support.py`):**
  - `ConvertingCases` implements `convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int` the way
    stage7/cases §5 says:
    - assert `tx is not None`, and record `(now, tx)` in `self.calls`;
    - for each `c` in `tx.cases.cases.list_open()` with `lifecycle == "live_queued"`:
      `update_versioned(c.case_ref, c.version, lifecycle="unassigned", updated_at=now)`,
      `tx.core.conversations.set_live_state(c.thread_id, "not_live", None)`, and
      `tx.core.events.append(thread_stream(c.thread_id), StreamEvent(type="shift_ended", at=now,
      payload={"speaker": {"kind": "event", "display_name": None}, "line": TEXTS[TextId.SHIFT_ENDED]}))`;
    - return the count.
  - `RaisingCases`: `convert_live_queued` records the call and raises `RuntimeError("converter failed")`.
- **Raw row readers** (tests may use `sqlite3`; services may not):
  - `rows(store, table) -> list[dict[str, object]]` opens `sqlite3.connect(store.db_path)` with
    `row_factory = sqlite3.Row` and runs `SELECT * FROM <table>`, for a table in a fixed allow-list (`job_runs`,
    `demo_events`, `case_events`, `events`, `promises`, `demo_state`, `conversations`);
  - `count(store, table) -> int` works the same way;
  - close the connection in `finally`.
- **Helpers (all in `demo_support.py`):**
  - `WallClock`, `chi`, `new_thread_id`, `new_request_id`;
  - `add_conversation(store, *, run_tag="live", outcome="open", last_customer_wall_at=None, live_state="not_live") -> ThreadId`;
  - `add_case(store, *, ref, reason, priority, lifecycle, created_at, due_at, promise: Promise | None, wake_up_at=None, owner_role=None, thread_id=None, customer_id=None) -> CaseRow`
    (creates a conversation when `thread_id` is None);
  - `set_demo(store, *, now=None, staffing=None)` (uses `demo_state.set_now` / `set_staffing` and commits);
  - `stream_events(store, thread_id) -> list[EventRow]` (`tx.core.events.after(thread_stream(thread_id), 0)`);
  - `ConvertingCases`, `RaisingCases`, `rows`, `count`;
  - `make_demo(store, cases, wall=WallClock(datetime(2026,10,21,19,0,tzinfo=UTC))) -> DemoService`.
- **Journeys** use the harness's own disposable DB copy (first boot of the real app). They insert nothing: `journey.db` is
  read-only. Case rows appear only once AEA-29's first-boot seed lands, which is why the lane and J-7 steps declare
  `case_service` as a need.

---

## 7. Checks

### 7.1 Tests the implementer writes (names are binding)

**`tests/unit/services/test_format_clock.py`**
- `test_format_clock_demo_start` (AC-6): `format_clock(DEMO_START) == ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)")`.
- `test_format_clock_examples` (PA-5):
  - `chi(2026,10,16,14,20)` → `"Fri Oct 16, 2026 · 2:20 pm"`;
  - `chi(2026,10,19,7,0)` → `("Mon Oct 19, 2026 · 7:00 am", "Mon Oct 19, 2026 (demo date)")`;
  - noon → `"… · 12:00 pm"`; midnight → `"… · 12:00 am"`;
  - `datetime(2026,10,19,12,0,tzinfo=UTC)` → `"Mon Oct 19, 2026 · 7:00 am"`.
- `test_format_clock_refuses_naive` (PA-5): `pytest.raises(ValueError)` on `datetime(2026,10,16,10,0)`.

**`tests/unit/services/test_demo_steps.py`** (PA-3)
- `test_steps_from_examples`:
  - Fri 10:00 + `plus_1h` → Fri 11:00; Fri 10:00 + `plus_4h` → Fri 14:00;
  - `next_business_morning` → Mon 2026-10-19 07:00; Wed 2026-11-25 10:00 → Mon 2026-11-30 07:00;
  - Sat 2026-10-17 15:00 → Mon 2026-10-19 07:00; Mon 06:00 → Tue 07:00;
  - every result has `tzinfo.key == "America/Chicago"`.
- `test_plus_hours_is_elapsed_time_across_dst`: `chi(2026,11,1,0,30)`, then `plus_1h` twice, gives an elapsed 2 h in UTC.
- `test_every_step_moves_forward`: for every step in `CLOCK_STEPS`, from each hour of 2026-10-16…2026-10-19 and of
  2026-11-25…2026-11-30, the result is `> start`.
- `test_unknown_step_raises`: `next_demo_time(DEMO_START, cast(ClockStep, "minus_1h"))` raises `ValueError`.

**`tests/unit/services/test_demo_imports.py`** (PA-6)
- `test_demo_and_scheduler_import_direction`:
  - `ast.parse` both files (`Path(__file__).resolve().parents[3] / "src/meridian/services"`), and collect every absolute
    `import`/`from` module name;
  - none may start with `meridian.web`, `meridian.agent`, `meridian.services.cases`, `meridian.services.handoff`,
    `meridian.adapters.checkpointer` or `meridian.adapters.models`;
  - no top-level name may be `sqlite3`, `anthropic`, `httpx`, `langgraph`, `langfuse` or `fastembed`.
- `test_view_types_come_from_domain_views` (PA-6, T-1):
  - for each name in `("ClockView", "ClockAdvanced", "StaffingView", "StaffingChange")`,
    `getattr(meridian.services.demo, name) is getattr(meridian.domain.views, name)`;
  - `ast.parse` of `services/demo.py` contains no `ClassDef` with one of those names.

**`tests/services/test_demo.py`** (all use `store`; `actor = actor_for(StaffRole.SUPERVISOR)`; the wall clock is fixed UTC)
- `test_clock_starts_at_demo_start` (AC-1): `DemoClock(store.uow).now() == DEMO_START`; `now.tzinfo.key == "America/Chicago"`;
  `(year, month, day, hour, minute) == (2026, 10, 16, 10, 0)`.
- `test_clock_ignores_wall_clock` (AC-1):
  - define `class _Tomorrow(datetime)` whose classmethods `now(tz=None)`, `utcnow()` and `today()` return the real value
    plus 1 day;
  - `monkeypatch.setattr("meridian.services.demo.datetime", _Tomorrow)`, then `DemoClock(store.uow).now() == DEMO_START`;
  - static check: in `inspect.getsource(DemoClock)` none of `"datetime.now"`, `"utcnow"`, `"date.today"`, `"time.time"`
    appears.
- `test_advance_steps` (AC-2):
  - `plus_1h` → `chi(2026,10,16,11,0)`; `plus_4h` → 15:00; `next_business_morning` → Mon 2026-10-19 07:00;
  - then `set_demo(store, now=chi(2026,11,25,10,0))`, and `next_business_morning` → `chi(2026,11,30,7,0)`;
  - `DemoClock(store.uow).now()` equals each returned `now`.
- `test_unknown_step_rejected` (AC-2): with one open thread, `pytest.raises(ValueError)` on
  `advance_clock(cast(ClockStep, "minus_1h"), …)`. Afterwards:
  - `rows(store, "demo_state")` is unchanged (no row);
  - `count(store, "demo_events") == 0` and `count(store, "events") == 0`;
  - `DemoClock(store.uow).now() == DEMO_START`.
- `test_advance_counts_became_overdue` (AC-3): the example-pair case, two open threads and one closed thread
  (`live_state="closed"`); steps `next_business_morning`, `plus_4h` ×3, `plus_1h`.
  - `became_overdue` per step is `[0, 0, 0, 0, 1]`;
  - each result's `model_dump().keys() == {"now", "label", "became_overdue"}`;
  - 5 `demo_events` rows, each with `kind == "clock_advanced"`, `role == "supervisor"`, `step` in order, the passed
    `request_id`, `demo_before`/`demo_after` == `format_wall` of the old/new times, and `became_overdue` as above;
  - each open thread has 5 `clock_changed` events; the closed thread has 0.
- `test_example_pair_con8_wf7` (**worked pair**, CON-8 + WF-7): the ticket's pair end to end.
  - `DemoService` steps, then `SchedulerJob(store.uow, object(), DemoClock(store.uow), lambda: 0, wall)`.
  - First `tick()`: `status == "completed"`, `overdue == 1`, `promises_missed == 1`. `list_for_case(MHC-C-0007)` holds one
    `overdue` and one `promise_missed` event with that `job_run_id`, and `promises.current(...).status == "missed"`.
  - A second `SchedulerJob(...).tick()`: `count(store, "job_runs") == 2`, still exactly one `overdue` event.
- `test_advance_result_fits_con8_route` (PA-9):
  - `ClockAdvanceResponse.model_validate(result, from_attributes=True).model_dump(mode="json")` equals
    `{"now": "2026-10-19T07:00:00-05:00", "label": "Mon Oct 19, 2026 · 7:00 am", "became_overdue": 0}` for a
    `next_business_morning` from a fresh store;
  - `get_args(ClockStep) == CLOCK_STEP_NAMES` (import both from their modules).
- `test_staffing_default_and_toggle` (AC-4, PA-4):
  - On a fresh store, `presence() == "nobody_online"` and
    `staffing() == StaffingView(mode="nobody_online", label="Nobody online", banner=None)`.
  - Setting the same mode (`set_staffing("nobody_online", role=DemoRole.CUSTOMER, …)`) gives `converted_cases == 0`,
    0 `demo_events` and 0 `events`.
  - Add two open threads and one closed thread. Turning on gives label `"Simulated staff on shift (demo)"` and one
    `demo_events` row (`kind="staffing_changed"`, `mode="simulated_on_shift"`, `demo_before="nobody_online"`,
    `demo_after="simulated_on_shift"`, `converted_cases=0`, `role="customer"`).
  - Each open thread gets one `staffing_changed` event with `line == TEXTS[TextId.STAFFING_CHANGED_ON_SHIFT]` and
    `staffing.mode == "simulated_on_shift"`; the closed thread gets none; the converter's `calls == []`.
  - The same mode again leaves one `demo_events` row.
  - Turning off (with `ConvertingCases`, no queued case) gives a payload with `line == STAFFING_CHANGED_OFF_LINE` and
    `staffing.banner is None`.
- `test_shift_end_commits_with_conversions` (AC-4):
  - Staffing on; a `live_queued` case (promise `promise_for(CUSTOMER_REQUESTED_PERSON, "simulated_on_shift", DEMO_START)`,
    due None) on thread T1 with `live_state="queued"`.
  - Off with `ConvertingCases` → `converted_cases == 1`; `len(cases.calls) == 1`; `calls[0][0] == DEMO_START`;
    `calls[0][1] is not None`; the case is now `unassigned`; T1's last two events are `["shift_ended", "staffing_changed"]`;
    staffing is `nobody_online`.
  - On again. Then a `DemoService` built with `RaisingCases`: off raises `RuntimeError`; staffing stays
    `simulated_on_shift`; the `demo_events` and `events` counts are unchanged.
- `test_deferred_cases_resolves_at_call_time` (PA-7):
  - A counting resolver that returns a `ConvertingCases`. Constructing `DeferredCases(resolver)` makes 0 calls. Staffing on
    makes 0 calls; off makes exactly 1 and returns the double's count.
  - A second resolver that raises `RuntimeError("not bound: case_service")`: on works; off raises that error; staffing stays
    `simulated_on_shift`; no new `demo_events` row.
- `test_staffing_banner_is_fixed_text` (AC-5): on → `staffing().banner == TEXTS[TextId.STAFFING_BANNER]`; off → `None`;
  `"No Meridian employee" not in Path(meridian.services.demo.__file__).read_text()`.
- `test_views_use_format_clock` (AC-6):
  - `clock_view() == ClockView(now=DEMO_START, label=…, date_label=…)` from `format_clock(DEMO_START)`;
  - after `advance_clock("plus_1h")`, `result.label == format_clock(result.now)[0]`, and the open thread's newest
    `clock_changed` payload has
    `demo_clock == {"now": result.now.isoformat(), "label": label, "date_label": date_label}`.
- `test_wf5_records` (AC-12): one staffing change and one clock advance with distinct request ids give two `demo_events`
  rows, each with a 36-character `demo_event_id` and its own `request_id`.

**`tests/services/test_scheduler.py`**. A helper `job(store, at, *, prune=lambda: 0, wall=WallClock(...)) -> SchedulerJob`
builds `SchedulerJob(store.uow, object(), FixedClock(at), prune, wall)`.
- `test_tick_writes_job_run` (AC-7):
  - one tick gives one `job_runs` row;
  - the raw `started_wall_at` and `finished_wall_at` end with `"+00:00"`; `status == "completed"`; `error_kind is None`;
  - `json.loads(counts_json)` has exactly the keys `{"overdue", "promises_missed", "due_soon", "stuck_waiting", "unowned",
    "abandoned", "pruned"}`, and the returned `JobRun` fields equal the row;
  - with one overdue case, its `overdue` event's `job_run_id` equals the row's.
- `test_failed_tick_records_failed` (AC-7): one overdue case; the prune double raises `RuntimeError("secret detail xyz")`.
  - Returned: `status == "failed"`, `error_kind == "prune_failed"`, `overdue == 1` (alerts committed first).
  - The row has the same status and `error_kind`; `"secret detail"` is absent from every `job_runs` column; exactly one
    `job_runs` row exists.
- `test_overdue_and_missed` (AC-8): a case created Thu 2026-10-15 10:00 with
  `promise_for(BILLING_DISPUTE, "nobody_online", Thu 10:00)` (assert its due is Fri 2026-10-16 19:00), case due = promise
  due. A tick at `FixedClock(chi(2026,10,16,20,0))` gives one `overdue` event, the promise `missed`, `overdue == 1` and
  `promises_missed == 1`.
- `test_fee_bearing_case_due_vs_promise_due` (AC-8): the fee-bearing case of §6. A tick at Fri 13:00 gives one `overdue`
  event, `promises.current(...).status == "open"` and `promises_missed == 0`.
- `test_stuck_waiting` (AC-8): a `waiting` case (`owner_role=StaffRole.REPRESENTATIVE`) with wake-up Fri 11:00, and a second
  waiting case with wake-up Fri 13:00. A tick at Fri 12:00 gives one `stuck_waiting` event, for the first case only.
- `test_due_soon` (AC-8): unassigned cases due Fri 13:00, Fri 14:00 (exactly 4 h) and Fri 15:00. A tick at Fri 10:00 gives
  `due_soon` events for the first two only, and `due_soon == 2`.
- `test_unowned_only_on_shift` (AC-8): an unassigned case created Fri 09:00, a claimed case created 09:00
  (`owner_role=REPRESENTATIVE`, `lifecycle="claimed"`), and an unassigned case created 09:45.
  - A tick at Fri 10:00 with nobody online gives no `unowned` event.
  - Then `set_demo(store, staffing="simulated_on_shift")`, and a new job's tick at 10:00 gives one `unowned` event, for the
    09:00 unassigned case only.
- `test_p0_never_overdue` (AC-8): a P0 safety case. A tick at Mon 2026-10-19 20:00 writes no case_event for it, and its
  promise stays `open`.
- `test_tick_idempotent` (AC-9): overdue and due-soon cases.
  - Two ticks at the same Fri 20:00: the alert events are unchanged after the second, and `job_runs` grows by 1.
  - Then one tick at Mon 2026-10-19 10:00 (a skipped interval): still no duplicate `overdue` for the same due value.
- `test_abandonment_sweep` (AC-10): `wall_now = datetime(2026,10,21,19,0,tzinfo=UTC)`. Conversations:
  - A: live/open, last = now − 30 min;
  - B: live/open, last = now − 29 min;
  - C: live/open, last None;
  - eval/open −2 h; load/open −2 h; seed/open −2 h; live/handed_off −2 h.

  The tick gives `abandoned == 1`. A has `outcome == "abandoned"` and `ended_wall_at == last + 30 min`. Every other row's
  `outcome` and `ended_wall_at` are unchanged (read with `lookup`).
- `test_prune_once_per_day` (AC-11): one `SchedulerJob` with a `WallClock` and a counting prune double returning 7. Ticks at:
  - 2026-10-21 14:00 UTC → pruned 7;
  - 20:00 UTC → None;
  - 2026-10-22 03:00 UTC (22:00 Chicago on 10-21) → None;
  - 2026-10-22 05:00 UTC (00:00 Chicago on 10-22) → 7.

  Prune is called twice, and each row's `counts_json` `pruned` matches.
- `test_wf7_records` (AC-12): an overdue case with an open promise past due, and one tick. One `job_runs` row. The
  `overdue` event has `case_ref` and `job_run_id`. The promise status change has a `promise_missed` case_event with the
  same `job_run_id` and `detail["promise_id"]` equal to the promise row id.
- `test_records_hold_no_pii` (AC-13): the MHC-10002 case of §6 (due passed) on a thread holding the customer message. Run
  `advance_clock("plus_4h")`, `set_staffing("simulated_on_shift")` and one tick. No column of any row in `job_runs`,
  `demo_events` or `case_events` contains the name parts, the phone or the email.
- `test_scheduler_thread_runs_and_stops` (PA-2): `SchedulerThread(counter, interval_s=0.01)`; `start()`; poll until
  `counter.n >= 2` (deadline 2 s); `stop()`. Then `alive is False`, the count is unchanged 0.05 s later, and a second
  `start()` raises `RuntimeError`.
- `test_scheduler_thread_survives_a_raising_tick` (PA-2): a tick that raises `RuntimeError("tick secret")` on the first call,
  then counts. Poll until the count is ≥ 1, then `stop()`. With `caplog` at WARNING, the message `"scheduler tick raised"`
  is present and `"tick secret"` is absent from `caplog.text`.

**`tests/unit/web/test_register_demo.py`** (PA-1, PA-7). Mirror `tests/unit/web/test_register_staff_live.py`. Shared set-up
`_wired(tmp_path, store, *, case_service=None)`:
- `c = Container(settings=make_settings(tmp_path), limits=Limits())` (`make_settings` from `tests/api/web_shell_support.py`);
- `app = FastAPI()`;
- `app.state.web_shell = WebShellState(settings=make_settings(tmp_path), wall_clock=wall, public_paths=PublicPaths())`;
- `c.provide(Key[Any]("uow_factory"), lambda _c: store.uow)`;
- a fake checkpointer with `prune(self, keep: int = 2) -> int` (records `keep`, returns 3) and `close()` (appends
  `"checkpointer"` to a shared `log` list), provided under `Key[Any]("checkpointer")` **with `c.on_close(fake.close)` called
  inside its factory**, exactly as AEA-10's factory does;
- `c.provide(Key[Any]("wall_clock"), lambda _c: wall)` with `wall = lambda: datetime(2026,10,21,19,0,tzinfo=UTC)`;
- if `case_service` is given, `c.provide(Key[Any]("case_service"), lambda _c: case_service)`;
- finally `register_demo(c, app, settings=c.settings, limits=c.limits)`.

Tests:
- `test_register_demo_wires_and_runs_the_thread`: with `ConvertingCases()`, call `c.build()`. Then:
  - `c.get(Key[Any]("demo_clock")).now() == DEMO_START`, `isinstance(c.get(DEMO_SERVICE), DemoService)`, and the
    thread is `alive`;
  - poll (≤ 2 s) until `count(store, "job_runs") >= 1`; that row's `started_wall_at == "2026-10-21T19:00:00+00:00"`; the
    fake prune saw `keep == 2`;
  - `c.close()` → the thread is not alive;
  - `"AEA-30" in register_demo.__doc__` and `"No-op until" not in register_demo.__doc__`.
- `test_thread_stops_before_storage_closes`: monkeypatch `SchedulerThread.stop` with a wrapper that appends `"thread"` to
  `log` and then calls the original; `c.build()`; `c.close()`; then `log == ["thread", "checkpointer"]`.
- `test_register_demo_ignores_app_without_web_shell`: a bare `FastAPI()`; `register_demo(...)`; `c.build()` succeeds;
  `c.get(DEMO_SERVICE)` raises `ContainerError` matching `"not provided: demo_service"`.
- `test_shift_end_without_case_service_fails_closed` (PA-7): `_wired` with **no** case service.
  - `c.build()` succeeds and the thread starts. `demo = c.get(DEMO_SERVICE)`.
  - `demo.set_staffing("simulated_on_shift", …)` succeeds.
  - `pytest.raises(RuntimeError, match="not bound: case_service")` on `demo.set_staffing("nobody_online", …)`.
  - `demo.presence() == "simulated_on_shift"`; `count(store, "demo_events") == 1`.
  - `c.close()`.

**`tests/journeys/j6/test_aea_30.py`** (AC-14). Use `pytestmark = pytest.mark.journey`, the `journey` fixture
(`tests/journeys/support/run.py::JourneyRun`), and **no** doubles, monkeypatching of `meridian` or `dependency_overrides`
(harness README). Module docstring:

> J-6 (proposed extension, slice plan §0a): the supervisor advances the one demo clock on the real server; the scheduler
> runs on it; a case past its case due shows in the Overdue lane. API level on AEA-57's harness with the scripted model.
> The lane step is blocked until AEA-29 (case service and first-boot seed) and AEA-45 (getOversight) land.

Helpers in the file:
- `_open_dues(journey) -> list[datetime]`: `parse_wall` of every
  `journey.db.rows("SELECT due_at FROM cases WHERE lifecycle NOT IN ('resolved','closed_unresolved') AND due_at IS NOT NULL")`
  value;
- `_became(dues, old, new) -> int`: `sum(old <= d < new for d in dues)`;
- `_wait_for(predicate, timeout_s=10.0)`: poll every 0.05 s, `AssertionError` on timeout.

Tests (one test function per step that can be blocked on its own, so the runnable steps show as passed):
- `test_j6_scheduler_ran_at_start(journey)`:
  `with journey.step("J-6", "1 scheduler ran at start", needs=("demo_clock",)):`
  - `_wait_for(lambda: journey.db.count("job_runs", "status = ?", ("completed",)) >= 1)`;
  - the earliest row (`ORDER BY started_wall_at LIMIT 1`) has `demo_now == "2026-10-16T15:00:00+00:00"` (the demo clock at
    `DEMO_START`), `started_wall_at` ending `"+00:00"`, `error_kind` NULL, and `json.loads(counts_json).keys()` equal to the
    seven keys.
- `test_j6_clock_advance_on_the_real_server(journey)`:
  `with journey.step("J-6", "2 supervisor advances the clock", needs=("login_sessions", "staff_access", "demo_service", "demo_clock"), operations=("login", "switchRole", "advanceDemoClock")):`
  - `signed = journey.login()`;
    `r = signed.client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "supervisor"})`, and
    `r.json()["role"] == "supervisor"`.
  - Walk `steps = ["next_business_morning", "plus_4h", "plus_4h", "plus_4h", "plus_1h"]`. For each step:
    - read `old`: `found = journey.db.rows("SELECT demo_now FROM demo_state WHERE id = 1")`, then
      `old = parse_wall(found[0]["demo_now"]) if found else DEMO_START` (a fresh store has no row until the first write);
    - `r = signed.client.call("POST", "/api/demo/clock", operation_id="advanceDemoClock", body={"step": s})`, with status
      200;
    - `new = datetime.fromisoformat(r.json()["now"])`, and `r.json()["became_overdue"] == _became(_open_dues(journey), old,
      new)`.
  - What the user sees on the last response: `now == "2026-10-19T20:00:00-05:00"`, `label == "Mon Oct 19, 2026 · 8:00 pm"`.
    The first response is `now == "2026-10-19T07:00:00-05:00"`, `label == "Mon Oct 19, 2026 · 7:00 am"`.
  - What is stored:
    - `demo_state.demo_now == "2026-10-20T01:00:00+00:00"`;
    - `journey.db.count("demo_events", "kind = ?", ("clock_advanced",)) == 5`;
    - the first such row (`ORDER BY at_wall, demo_event_id` is not stable, so select by `step = 'next_business_morning'`)
      has `role == "supervisor"`, `request_id` equal to that response's `X-Request-ID` header,
      `demo_before == "2026-10-16T15:00:00+00:00"` and `demo_after == "2026-10-19T12:00:00+00:00"`.
- `test_j6_case_in_overdue_lane(journey)`:
  `with journey.step("J-6", "3 overdue lane", needs=("login_sessions", "staff_access", "demo_service", "case_service"), operations=("login", "switchRole", "advanceDemoClock", "getOversight")):`
  - log in as supervisor (as above); advance `next_business_morning`, `plus_4h` ×3, `plus_1h`;
  - `o = signed.client.call("GET", "/api/staff/oversight", operation_id="getOversight")` returns 200;
  - `refs = [row["reference"] for row in o.json()["lanes"]["overdue"]["rows"]]`; `"MHC-C-0007" in refs` (seed case,
    cases.md §7);
  - stored: `parse_wall(journey.db.scalar("SELECT due_at FROM cases WHERE case_ref = 'MHC-C-0007'")) < parse_wall(<demo_now>)`.
  - Blocked today (skipped, naming AEA-29 and AEA-45).

**`tests/journeys/j7/test_aea_30.py`** (AC-14; same rules). Module docstring:

> J-7 (proposed extension): with staffing on, a person request is live-queued; turning staffing off converts the case and
> tells the chat. API level on AEA-57's harness. Blocked today on AEA-43 (setStaffing), AEA-40 (startChatSession) and
> AEA-29 (handoff and case services); the service-level behaviour is in tests/services/test_demo.py
> (test_shift_end_commits_with_conversions, mock-tested).

- `test_j7_shift_end_converts_queued_case(journey)` has three steps in one test:
  1. `"1 staffing on"`, with `needs=("login_sessions", "demo_service")` and `operations=("login", "setStaffing")`:
     - `PUT /api/demo/staffing` with `{"mode": "simulated_on_shift"}` returns
       `{"mode": "simulated_on_shift", "label": "Simulated staff on shift (demo)", "converted_cases": 0}`;
     - stored: `demo_state.staffing == "simulated_on_shift"`, and one `demo_events` row with `kind = 'staffing_changed'`,
       `role = 'customer'` and `request_id` = the response's `X-Request-ID`.
  2. `"2 person request live-queued"`, with `needs=("session_service", "handoff_service", "person_requests")` and
     `operations=("startChatSession", "requestPerson")`:
     - `thread_id = POST /api/chat/sessions (startChatSession).json()["thread_id"]`;
     - `POST /api/chat/sessions/{thread_id}/handoff` with `{"turn_id": str(uuid.uuid4())}` gives `result == "live_queued"`;
     - stored: one case for the thread with `lifecycle = 'live_queued'`, and `conversations.live_state == 'queued'`; keep
       its `case_ref` and `created_at`.
  3. `"3 staffing off converts"`, with `needs=("case_service", "demo_service")` and `operations=("setStaffing",)`:
     - `PUT` `{"mode": "nobody_online"}` returns `converted_cases == 1` and `label == "Nobody online"`;
     - stored: the case has the same `case_ref` and `created_at` and `lifecycle == 'unassigned'`;
       `conversations.live_state == 'not_live'`;
     - `[r["type"] for r in journey.db.rows("SELECT type FROM events WHERE stream = ? ORDER BY id", (thread_id,))]` ends
       with `["shift_ended", "staffing_changed"]`;
     - `journey.db.count("demo_events", "kind = ?", ("staffing_changed",)) == 2`.

### 7.2 Existing tests that must stay green (this merge un-skips several of them)

- `tests/unit/web/` (all; `test_container.py::test_every_register_stub_present` skips filled hunks),
  `tests/unit/test_import_direction.py`, `tests/unit/policy/`, `tests/unit/adapters/`, `tests/unit/fakes/`.
- **Every test that builds the real app**, because after this merge `create_app` runs this hunk and the starter starts the
  thread wherever starters are not suppressed:
  - `tests/api/` (all; `test_staff_session_capture.py` and `test_staff_session_routes.py::test_register_staff_binds_providers`
    now use the real `register_demo`, since their stand-in keys off the "No-op until" docstring);
  - `tests/contract/` (the `advanceDemoClock` cases now run against the real `DemoService`);
  - `tests/services/` (all);
  - `tests/journeys/` (all; J-1 "3 login" steps and `tests/journeys/support/test_support.py::test_wall_clock_control_expires_session`
    now run).
- **Known pre-existing red on `main`, not caused by this ticket:**
  `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0` (wave-0 finding 5). Report it; do not
  fix it (not owned).

### 7.3 Gates (cheapest first; stop at the first red)

Let `F` be the owned Python files:

```bash
F="src/meridian/services/demo.py src/meridian/services/scheduler.py src/meridian/web/container.py \
tests/services/demo_support.py tests/services/test_demo.py tests/services/test_scheduler.py tests/unit/services \
tests/unit/web/test_register_demo.py tests/journeys/j6/test_aea_30.py tests/journeys/j7/test_aea_30.py"
```

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check $F` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check $F` (run `uv run ruff format $F` first if not) | `… files already formatted` |
| 3 | Type check | `uv run mypy` | `Success: no issues found in N source files` |
| 4 | No server clock in the demo clock | `grep -n "datetime.now\|utcnow\|time.time" src/meridian/services/demo.py` | only the `_utc_now` line |
| 5 | Affected tests | `uv run pytest tests/services tests/unit/services tests/unit/web tests/unit/test_import_direction.py tests/api tests/contract -q` (serial; if slow, `uv run --with pytest-xdist pytest -n 2 …` adds xdist without a dependency change; never more than `-n 2`) | all passed or skipped; 0 failed |
| 6 | Affected journeys | `uv run pytest -m journey tests/journeys/j6/test_aea_30.py tests/journeys/j7/test_aea_30.py -rs --journey-record=AEA-30`; then `uv run python -m tests.journeys.affected --base main` | J-6 steps 1–2 pass; J-6 step 3 and J-7 skipped as blocked with the owning tickets; J-1 "3 login" steps pass (PA-8); no other journey fails |
| 7 | Strict contract count (report only) | `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -q 2>&1 \| grep -c "not bound: demo_clock\|not bound: get_demo_service"` | `0` (wave-2 finding 2; the other unbound keys stay failures in strict mode and are not this ticket's) |
| 8 | Diff scope | `git diff --name-only main...HEAD` | only §2.1 files |
| 9 | Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` (from the worktree root) | no `FAIL`; report any `WARN` that names a §2.1 file |

Full suite: **not** required. Nothing here is a shared fixture, settings, dependency or lock change. `container.py` changes
in one hunk, and every test that builds the real app is in gate 5. Iterate with gate 5's first two folders. Run all the
gates once before the final commit and paste the results.

### 7.4 Journey record: `docs/testing/journeys/<run-date>-AEA-30.md`

Generated by gate 6's `--journey-record=AEA-30`. Then edit only these cells:

| Field | Value |
|---|---|
| Claim | AEA-30 `services/demo.py`, `services/scheduler.py` (AC-1…AC-13, PA-1…PA-9). J-6 at API level on the real app: the scheduler ran at start on the demo clock, and the supervisor's five advances moved the one demo clock with `became_overdue` matching the stored case dues, five `clock_advanced` rows with the supervisor role and request ids. J-7 shift-end behaviour at service level only (tests/services) |
| Result | keep the generated per-step lines; append: `service level: <N> passed (tests/services/test_demo.py, test_scheduler.py, tests/unit/services, tests/unit/web/test_register_demo.py)` and `J-1 3 login: pass (PA-8)` |
| Remaining limitations | No CON-7 route (AEA-43), so J-7 is not driven over HTTP; no real `convert_live_queued` (AEA-29), and a real shift end answers "not bound: case_service" until AEA-29/51; no Overdue lane read (AEA-45); no browser leg (AEA-58/62); event payloads reach the stream unchanged but are not yet validated against `EvStaffingChanged`/`EvClockChanged` in a journey |
| Journeys that will exercise this code | J-6 and J-7 at `integrated with a scripted model` once AEA-29, 40, 43, 45 land; J-1 (login reads the demo clock; CON-1 reads clock and staffing, AEA-40); J-8 (reset returns the clock, AEA-31/43) |

---

## 8. Risks and requests

| ID | Risk / request | What to do |
|---|---|---|
| R-1 (retired) | ~~D-P1: define the view types locally.~~ AEA-02b merged `domain/views.py` (T-1). | Import them. PA-6's `test_view_types_come_from_domain_views` stops a second copy from appearing. |
| R-2 | **`case_service` is unbound until AEA-29/AEA-51.** Between this merge and then, a real shift end raises `RuntimeError("not bound: case_service")` and rolls back, so staffing stays on. That fails closed: there is never a live-queued case left while nobody is online. CON-7 itself arrives with AEA-43. | **Tell the AEA-51 / AEA-29 planners:** providing `deps.CASE_SERVICE` is all this hunk needs. **Tell AEA-43's planner:** a 500 on CON-7 "off" is expected until then. |
| R-3 | **Container keys cross tickets.** This ticket provides `"demo_clock"`, `"demo_service"`, `"scheduler_job"` and `"scheduler_thread"`. Three merged hunks already read `"demo_clock"` lazily. | No edit outside this hunk. A test harness that provides `"demo_clock"` itself **and** calls the real `register_demo` would get "already provided"; none does on `main` (checked: `tests/api/*_support.py` either build their own container without `register_demo` or use the real one). |
| R-4 | **Copy gap (UX-owned words).** SCREEN_SPECS gives one `staffing_changed` line, written for "on"; there is no signed "off" line. `apps/web`'s dev fixture uses "Staffing changed: nobody online." with the comment "the spec gives only the 'on' wording". | Decided (an obvious default that matches the built frontend): `STAFFING_CHANGED_OFF_LINE = "Staffing changed: nobody online."`, plus the two labels, as constants in `services/demo.py` citing their source. **Request:** the UX session confirms the off line; moving it to `policy/texts.py` later is an AEA-03 follow-up and a one-line change here. |
| R-5 | **Thread closer order.** | Handled in step 6 and proven by `test_thread_stops_before_storage_closes`. |
| R-6 | **`DemoService` gains an optional keyword `wall_clock`**, beyond cases §6's constructor. Positional parameters, names and methods are unchanged. | **Request:** one pointer sentence in `stage7/cases.md` §6 at the next docs pass (not this ticket's file). |
| R-7 | **`SchedulerJob.cases` is unused** (typed `object`). | Kept by name and position as cases §6 says; a later contract pass may drop it. |
| R-8 | **Case-event kind names cross AEA-29.** This ticket writes `overdue`, `due_soon`, `stuck_waiting`, `unowned` and `promise_missed` (actor `system`). | **Tell AEA-29's and AEA-53's planners** the kind `promise_missed`, so a resolve-time miss and the M-13 reader agree. |
| R-9 | **The thread now runs in every real app whose starters run:** the journey harness, AEA-59's contract driver and `create_app` tests without `suppress_container_starters`. Its first tick runs at once and may write alerts (for seed cases, once AEA-29 lands) or abandon idle live chats by the injected wall clock. During a reset's exclusive transaction (AEA-31), a tick waits on the 5 s busy timeout or fails one step (`failed`, logged, retried at the next tick). | That is the product path. §7.2 makes the implementer run those suites. A journey that moves the wall clock by ≥ 30 minutes with an open live chat will see it abandoned; that is M-18's rule. |
| R-10 | **Two clocks.** Promise-missed runs on the demo clock; abandonment and prune run on the wall clock (D-13). A journey that moves only one clock sees only one of them. | Stated in the scheduler module docstring. |
| R-11 | **Shared context rows.** AEA-29 edits the same A6 area-map cell and ICM row; there are two A6 area-map rows today (wave-2 finding 9). | Expect a textual merge conflict on those lines; the merge agent keeps every ticket's clause. Do not delete the duplicate row. |
| R-12 | **`LiveQueueConverter` is a Protocol in a service file**, while DO-3 S-20 defers Protocols in front of our services. | It is a one-method typing aid with no second implementation. Once AEA-29 is merged, a reviewer may retype `cases` as `CaseService` under `TYPE_CHECKING`. |
| R-13 | **Journey bodies for blocked steps cannot be run today.** J-6 step 3 and J-7 are written against the OpenAPI and the seed table. | When AEA-29/40/43/45 merge, their merge gates run all journeys (`tests/journeys/` changes select all; the wave merge runs all). A failure there is a fix in this file through the same pair, not in theirs. |
| R-14 | **Pre-existing red** `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0`. | Not owned; report, do not fix. |
| R-15 | **J-1 step "4 start session" (AEA-57's file) reads `journey.db.scalar("SELECT demo_now FROM demo_state WHERE id = 1")`**, which raises when the row does not exist. A fresh store has no `demo_state` row until the first staffing toggle or clock advance (AEA-10's `get()` returns the default without writing; cases §1.1), and nothing on `main` or in this plan writes one at boot. The step is blocked on AEA-40 today, so nothing fails now. | **Tell the AEA-40 planner (and AEA-57's owner):** when that step un-blocks, either `SessionService.open` reads the clock through `DemoClock` and the step compares against `DEMO_START` when the row is absent, or a small AEA-10 follow-up adds an insert-if-missing method that the `register_demo` starter calls. This plan does neither: `set_now(DEMO_START)` at boot would overwrite an advanced clock after a restart. |
| R-16 | **AEA-29's plan makes two requests of this ticket.** (a) Its R-3 note: build `DemoService` with an eager `c.get(deps.CASE_SERVICE)`. (b) Its R-16: use its `services/cases.staffing_view(mode)` instead of `STAFFING_LABELS`. | **Both declined (T-3).** (a) An eager read fails every app start while `case_service` is unbound, and with tree-ordered merges this ticket may land first. `DeferredCases` reaches the same object at the first shift end once AEA-29 binds the key. (b) It would add an import from `services/cases.py` (PA-6), a module not on `main`. **Request to the orchestrator and AEA-29's implementer:** keep one producer for the labels. Either AEA-29 imports `STAFFING_LABELS` from `meridian.services.demo` (merged first or in the same batch), or an AEA-03 follow-up moves both labels to `policy/texts.py` and both files import them. Until then the strings are identical, and each side's tests pin them to the OpenAPI examples. |
| R-17 | **A converted promise can never be marked missed (AEA-29 R-7).** AEA-29's `convert_live_queued` (its Step 5, item 2.3) inserts the new 1-business-day promise and then marks that new current row `changed`. The signed rule (cases §5 rules table: missed when the scheduler "finds it `open` with promise due < demo now") and AEA-10's `list_open_past` (`status = 'open'`, current row only) both skip such a row, so a shift-ended customer's promise drops out of M-13's misses. | This ticket follows the signed rule and does not widen it: no change to `list_open_past`, and no `changed` handling in `tick`. **Request to the orchestrator for AEA-29** (recommended; no contract change): mark only the superseded row `changed` and leave the new current row `open`, which is how cases §5's row "Promise `changed`: `convert_live_queued` (new text from the table)" reads. If Innocent prefers the other reading, M-13's definition needs his decision, not this ticket's. |
| R-18 | **Unreviewed branch work (T-2).** The existing commits were built from an older plan and never went through review or the ledger. | Step 0.0: merge `main` in, re-check every step, re-run every gate on the merged head, and refresh the journey record's `Tested revision`. The reviewer reviews `main...HEAD` as a whole. |
| R-19 | **Tree-ordered merges (T-6).** AEA-30 may merge in one batch with AEA-29, 40, 43 and 45. | The merge gate runs the union of the affected tests, plus all journeys (any `tests/journeys/` change selects every journey). The blocked journey steps in §7.1 un-block as their owners land in the same batch. If one then fails, the fix goes into this ticket's journey files through the same planner → implementer pair. |

**What you must not do:**
- Edit any file outside §2.1, or touch: `adapters/sqlite/*`, `checkpointer.py`, `policy/*`, `domain/*`, `ports/*`,
  `config.py`, `web/deps.py`, `web/middleware.py`, `web/app.py`, `web/logging.py`, any route or schema file, another
  `register_*` hunk, `test_container.py`, `tests/fakes/`, `tests/fixtures/`, `tests/conftest.py`, `tests/journeys/support/`,
  `tests/contract/`, `tests/api/`, `pyproject.toml`, `uv.lock`.
- Add anything to `domain/`, or define `StreamKey`, `thread_stream` or a repository method.
- Import `services/cases.py`, `services/handoff.py`, `sqlite3`, `meridian.web` or `meridian.adapters.checkpointer` in a
  service, or resolve `deps.CASE_SERVICE` at build time.
- Read the server clock in `DemoClock` or use it for any case due.
- Move the clock backwards, or accept a step outside `ClockStep`.
- Write a `health_event`, or write any outcome other than `abandoned` in the sweep.
- Compose or reword the banner.
- Put a name, phone, email, message text or exception text in `job_runs`, `demo_events`, `case_events` or a log record, or
  log `exc_info`.
- Type a full phone number, a customer name or an email into a test, or call `ThreadId("…")` directly.
- Use doubles, `dependency_overrides` or monkeypatching of `meridian` inside `tests/journeys/`.
- Call a paid model, bind ports 4019 or 5184, `git add -A`, push, or force-push.

---

## 9. Readiness

**READY.** Every import is on `main` at `dd1b110`:
- AEA-10 — storage, `rows.py`, `DEMO_START`, `Checkpointer.prune`, `temp_sqlite`;
- AEA-11 — `FixedClock`;
- AEA-14 — `is_business_day`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`, `promise_for`, `case_due_at`;
- AEA-23 — the `deps` keys and `WebShellState`;
- AEA-02b — `domain/views.py` (the four view types);
- AEA-57 — the journey harness.

Siblings called only by injection and not waited for:
- **AEA-29** (`convert_live_queued`): a double in the tests, resolved lazily at runtime, bound by AEA-29/51.
- **AEA-43, AEA-45, AEA-40**: the journey steps that need them report as blocked.

No `NEEDS-DECISION`:
- No signed contract changes (OpenAPI, `UI_CONTRACTS.md`).
- No decision in `docs/plans/stage7-signoff.md` D-4…D-15 is answered differently. D-13's wall-clock override is honoured
  through `deps.WALL_CLOCK`.
- D-P1 is retired: the view types belong to AEA-02b and are imported (T-1).
- AEA-29's two requests (R-16) and its `changed`-promise note (R-17) are answered by the signed contract as written.
  R-17's fix is a request to AEA-29, not a decision this ticket takes.
  The off-line copy (R-4) follows the built frontend's own default and is flagged for the UX session.

## Gates

None (no human, external, paid or live gate). The merge gate is: lint and format, type check, the affected tests of §7.3
gate 5, then every journey (a `tests/journeys/` change selects all).
