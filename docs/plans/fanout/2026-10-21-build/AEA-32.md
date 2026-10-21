# Plan — [AEA-32] ops: health events, heartbeat, watchdog, alerts

**Status:** planned — **BLOCKED-ON AEA-10 and AEA-23** (both wave 1, real imports; neither is merged on `main` yet), with one
in-wave merge-order edge: AEA-26 merges before AEA-32 (§8 R-3). Every product decision is made; nothing needs Innocent. See §9.
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #32 (= `docs/plans/tickets/AEA-32.md`) · **Base revision:** `2b46a59` (main, 2026-10-21)
**Refreshed 2026-10-21** (first draft against `16ca639`). Since then: AEA-02 merged, and its `OpsRepos` shell matches §4.1;
AEA-10 is **built on branch `aea-10-aea-10-storage` at `135ad75`** but not merged, and every AEA-10 name below was checked against
that branch; AEA-19 is built on its branch (`2d5b692`) and already calls `alert_writer.fire(...)`; AEA-23 has not started
(its names below still come from its plan). The ticket, `stage7/cases.md` §8, DO-4 and the signed OpenAPI did not change.
**Lane / risk:** `lane::build-loop` · no `risk::security` (slice plan row AEA-32). Normal loop: the implementer writes the code **and** the tests named in §7 together. No test-writer, no frozen tests, no security agent.
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21. **Implementer:** `fanout-implementer` on Sonnet.
**Worktree / branch:** whatever the orchestrator gives you (convention: `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-32`, branch `aea-32-ops-health`). All paths below are relative to the repository root.

---

## 1. Goal and sources

### 1.1 Goal (quoted from the issue, *What to build*)

> **US-27:** As a **reviewer** (and the business owner), I need a monitoring page (volume, containment, escalations,
> failures, latency, spend against the daily cap, alerts as decision lines, and when the health check last restarted the
> service) and the evaluation report (…), with no codes or card numbers in what's shown, so that I can check the claims
> myself.
>
> "Would the business know if it broke?" — the records that answer it. Shapes are `docs/design/contracts/stage7/cases.md`
> §8 (CAS-22, CAS-25, CAS-26, CAS-27, CAS-30); the tables are created by AEA-10's `95_ops.sql`.
> - `adapters/sqlite/repos_ops.py` (the body of AEA-02's shell, constructor `__init__(self, conn)`, CAS-35) …
> - `services/health.py` — `AlertSettings` (frozen dataclass, the **one** place alert lines live) …
> - `services/health.py` — `Heartbeat`, `Watchdog`, `AlertWriter`, `AlertEvaluator`, `load_eval_reports` …
> (full text: `docs/plans/tickets/AEA-32.md` *What to build*)

**What it does, concretely.**
- **Heartbeat.** Every 5 s a small task on the web server's event loop runs an empty function on a worker thread and then
  records "beat at time T". `/healthz` (AEA-23) answers 200 while the last beat is at most 30 s old. A stuck event loop or a
  full worker pool stops the beats, so `/healthz` starts answering 503.
- **Watchdog.** A background thread asks `/healthz` every 15 s and writes one `health_events` row per answer
  (`check_ok` / `check_failed`). After three failures in a row it writes a `restart` row and ends the process with exit
  code 1; Railway's restart policy starts it again.
- **Alerts.** Every 60 s the watchdog asks the `AlertEvaluator` to compare stored rows with the alert lines in
  `AlertSettings` (spend cap, p95 latency, failure rate, zero traffic, a restart today, trace export, a stale scheduler).
  It writes `alert_fired` / `alert_cleared` rows **only when a state changes**. The monitoring page (AEA-53) reads those
  rows and never re-applies a line.
- **Eval reports.** `load_eval_reports` copies every `eval/reports/*.json` the harness wrote into `eval_runs` /
  `eval_case_results`, once per `run_id`.

**Example pair (the ticket's; WF-17; there is no WP-N pair for this ticket).** Input: `/healthz` answers OK, then the
heartbeat stops advancing for three probes. Output: one `health_event` per probe (`check_ok`, `check_failed`,
`check_failed`, `check_failed`), then a `restart` `health_event` with `at_wall` and a `reason_code`, then `exit(1)` (in
tests the injected exit callable is called once with 1). On the next start, `evaluate()` writes `alert_fired` for
`health_check_restart`, and `ops.health.restarts_by_day("America/Chicago")` returns one restart for that day (M-28).
Test: `tests/services/test_health_capture.py::test_example_pair_wf17`.

### 1.2 Context

Wave 2, area A10a (DO-3 §8). On `main` at `2b46a59` the following are merged: AEA-01 (`policy/limits.py`; `web/container.py`
with 27 no-op stubs including `register_ops`), AEA-02 (domain, ports, `config.Settings`, the seven repository shells
including `repos_ops.py`), AEA-03, 04, 05, 11, 14, 15, 16, 20 and 25. This ticket still needs **AEA-10** (`db.py`, `95_ops.sql`,
`SqliteUnitOfWork`, `temp_sqlite()`, the `repos_core` / `repos_cases` reads; built at `135ad75`, awaiting merge) and **AEA-23**
(`web/deps.py` keys, `web/middleware.py` `WebShellState`, `web/app.py` `create_app` and its async `/healthz`; not started).
AEA-23's names below come from its plan (`docs/plans/fanout/2026-10-21-build/AEA-23.md`). **If merged code differs from a
name below, the merged code wins**: use the merged name and note it in your report.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-32.md` | AC-1…AC-15, owned files, must-not-edit list, example pair |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-32 (wave 2; blocked by 10, 23; owns `repos_ops` body, `services/health.py`); §0 deviation 1 (AEA-10 writes every DDL); §0a J-10 (*proposed:* 32); §3 rows `web/container.py`, `repos_*.py`, `schema/*.sql`, `tests/journeys/`, context files | Own hunk only; never `schema/*.sql`; one journey file `tests/journeys/j10/test_aea_32.py` |
| Component contracts | `stage7/cases.md` §1.0 (unit of work, `format_wall`), §1.1 (`95_ops.sql`, wall-time storage MC-20, `turns.trace_export`), §1.2 (`cases.job_runs.latest()`), §1.3 (*Kept*), **§8 (this ticket — wins over DO-4)**, §9 (AEA-53 reads `latest_alert_states`, `AlertSettings`); `stage7/models.md` §6 (`LedgerService.spend_today()`), §4 / cross-topic 6 (`on_alert` → `AlertWriter.fire`); `stage7/data.md` §6 (`EvalRunRecord`, `EvalCaseResult`, `EvalReportFile`), §7 (start command); `stage7/web.md` §4 (`get_wall_clock()`), §7 (`/healthz` never waits), §9 table (`replied_at` stamped by `TurnService`); DO-4 §13, §16 | Exact shapes in §4 |
| Code design | DO-3 §2.1 (services may call `tx.<repo>`; never `sqlite3`, never `web/`), §2.3 rules 3 and 6, §3 (`repos_ops.py`, `services/health.py`), §4.4 row `services/health.py`, §8 (A10a) | Module homes and import direction |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` (report files feed CON-20) | n/a for scoring: health records answer "did it run?", never "was it right?"; the loader stores the harness's summary unchanged (AC-9) |
| Decisions | `docs/plans/7b-decisions/cases.md` CAS-22, CAS-25, CAS-26, CAS-27, CAS-30; `data.md` DAT-14; `merge-clashes.md` MC-10, MC-20, MC-22, MC-24; R-G-23 / R-W-19 | Alert rules, window, staleness, loader, no overdue alert |
| Observability contract | `docs/design/observability-contract.md` WF-13, WF-17; *Records* (`health_event`, `deploy_record`, `eval_run`, `eval_case_result`); *Content and redaction* (IDs only); *Missing instrumentation* ("no recent health events means not running"; "overdue job stopped ticking") | One event per check and per restart; IDs and numbers only |
| Key-metrics registry | DO-7 M-22 (4 h outside 22:00–06:00 Chicago), M-23 (p95 of `turn.server_ms`, 12.5 s), M-24 (`degraded_handoff` for model error, tool error or timeout ÷ turns, 2%), M-26 ($30, Chicago day), M-28 (restarts per day), M-29 (`trace_export`) | The exact alert computations in §5 step 4 |
| System design | §8.2 *Process hang* row (watchdog every 15 s, three failures → exit; Q-045 = A) | Watchdog behaviour |
| OpenAPI (read only) | `ui-contracts.openapi.yaml` `MonitorAlert.type` (six values), `state` (`firing`/`quiet`), `fired_at` | `AlertType` = six values + `scheduler_stale`; AC-5 test reads the enum |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`; workspace `code-design-solid-modularity.md`, `code-structure.md` (service ≤ 600 lines, adapter ≤ 600, test file ≤ 500), `async-safety.md` rule 2 (every thread / task names its closer) | Affected tests + fast gates; journey record at `mock-tested`; context rows in the same change |
| Sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 (all taken as recommended) | Nothing here conflicts; D-14's DAT-4 note: no code changes either way |
| Sibling code / plans (read only) | AEA-10 branch `135ad75`; AEA-19 branch `2d5b692` (`register_tracing` calls `container.get(Key[Any]("alert_writer")).fire("trace_export_failed", reason)`, `reason` ∈ `"wrong_project"`, `"project_check_failed"`); AEA-26 plan (`Key[LedgerService]("ledger")`, `spend_today() -> float`); AEA-23 plan (deps key table, D-P3, D-P4, `full_app`) | Key names and call shapes in §4 |

---

## 2. Boundary

### 2.1 Owned files (the only files you may create or edit)

| File | Create / modify | What |
|---|---|---|
| `src/meridian/adapters/sqlite/repos_ops.py` | modify (AEA-02 shell → body) | Row models, `HealthRepo`, `DeployRepo`, `EvalRepo`, `SignalsRepo`, `OpsRepos` (§4.5) |
| `src/meridian/services/health.py` | create | `AlertSettings`, `SpendReader`, `Heartbeat`, `run_beats`, `time_outside_quiet_hours`, `p95_nearest_rank`, `AlertWriter`, `AlertEvaluator`, `Watchdog`, `load_eval_reports` (§4.6) |
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_ops`** | §5 step 6 |
| `tests/adapters/__init__.py` | create (empty) | package marker for the AC's test path |
| `tests/adapters/test_repos_ops.py` | create | AC-1, AC-11, PA-1…PA-3 |
| `tests/unit/services/test_health.py` | create | AC-2, AC-3, AC-4 (restart day), PA-4…PA-6 |
| `tests/services/ops_support.py` | create | Test helpers for this ticket only (§6) — not collected by pytest |
| `tests/services/test_alerts.py` | create | AC-4…AC-8, AC-10 |
| `tests/services/test_load_eval_reports.py` | create | AC-9, PA-8 |
| `tests/services/test_health_capture.py` | create | AC-12, AC-14, example pair |
| `tests/unit/web/test_register_ops.py` | create | PA-7 |
| `tests/journeys/j10/test_aea_32.py` | create | AC-13 (mock level) |
| `docs/testing/journeys/<run-date>-AEA-32.md` | create | AC-13 record (§7.4) |
| `.claude/reference/area-map.md` | modify the A10a row only | AC-15 |
| `.claude/state/icm-progress.md` | add one row (format of the existing *Routes verified against code and tests* rows) | AC-15 |
| `docs/design/code-design.md` | modify §3 *Built* line and the §4.4 `services/health.py` row only | AC-15 |

(`tests/services/__init__.py`, `tests/unit/services/__init__.py`, `tests/unit/web/__init__.py` and `tests/journeys/j10/__init__.py`
already exist on `main`; do not recreate them.)

### 2.2 Shared surfaces you read (and may import) but never edit

`src/meridian/domain/*`, `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02); `src/meridian/adapters/sqlite/db.py`,
`rows.py`, `repos_core.py`, `repos_core_aux.py`, `repos_cases.py`, `repos_cases_state.py`, `migrate.py`, every `schema/*.sql`,
`tests/fixtures/sqlite.py`, `tests/unit/adapters/sqlite/helpers.py` (AEA-10); `src/meridian/web/app.py`, `deps.py`,
`middleware.py`, `logging.py`, `tests/api/*` (AEA-23); `src/meridian/policy/limits.py`, `tests/conftest.py`,
`tests/journeys/affected.py`, `pyproject.toml`, `uv.lock`, the rest of `web/container.py`, `tests/unit/web/test_container.py`,
`tests/unit/test_import_direction.py` (AEA-01); `tests/unit/adapters/test_repo_shells.py` (AEA-02, scoped by AEA-10);
`tests/fakes/` (AEA-11); `docs/ux/03-structure/ui-contracts.openapi.yaml` (read in one test, never written).

### 2.3 Owned by other tickets — do not create or edit

`services/ledger.py`, `repos_spend.py` (AEA-26); `adapters/tracing_langfuse.py` and the `register_tracing` hunk (AEA-19 —
it reads our `Key("alert_writer")`); `services/metrics_reader.py` (AEA-53); `web/routes/reads.py` (AEA-48);
`eval/**` (AEA-24, AEA-06); `Dockerfile`, `railway.json`, `scripts/` and the start-up deploy-record write (AEA-50);
`tests/journeys/support/` (AEA-57); `tests/fakes/` (AEA-11); `tests/capture/` (CAP files of 50–53); any other
`register_*` hunk; `apps/web/**`, `docs/ux/**`, `UI_CONTRACTS.md`, `docs/archive/`, `docs/parked/`, the briefing, issued data.

---

## 3. Requirements

### 3.1 Acceptance criteria → implementation → verification

| ID | Requirement (short; the issue text governs) | How | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `repos_ops` round-trips every row over `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`; wall times UTC `+00:00` via `db.format_wall`; `upsert_report` replaces by `run_id`, returns False when unchanged | §5 step 2 | `tests/adapters/test_repos_ops.py::test_round_trips`, `::test_upsert_report_by_run_id` — equal rows; one `eval_runs` row after two upserts |
| AC-2 [invariant] | `Heartbeat` in memory; fresh ≤ 30 s, stale after; beats only after a no-op ran through the pool; no `sqlite3` on its path | §5 step 3 | `tests/unit/services/test_health.py::test_heartbeat_fresh_and_stale`, `::test_beat_goes_through_pool` |
| AC-3 [failure/refusal] | `Watchdog.run_once` writes one check event per probe; three failures → one `restart` event + `exit(1)` once; a success resets | §5 step 5 | `tests/unit/services/test_health.py::test_watchdog_exits_after_three_failures`, `::test_success_resets_count` |
| AC-4 [invariant] | Each alert fires and clears from stored rows only, on change only (all seven rules incl. quiet hours, R-G-23 day rule) | §5 step 4 | `tests/services/test_alerts.py::test_each_alert_fires_and_clears` (parametrised per `AlertType`), `::test_no_duplicate_events_without_change`, `tests/unit/services/test_health.py::test_restart_alert_clears_next_chicago_day` |
| AC-5 [negative] | No overdue alert; `AlertType` = six OpenAPI values + `scheduler_stale` | `AlertType` literal; evaluator reads no case rows | `tests/services/test_alerts.py::test_overdue_is_not_a_health_alert` |
| AC-6 [negative] | `eval` / `load` / `seed` traffic never counts | `SignalsRepo` joins `conversations.run_tag = 'live'` and `turns.run_tag = 'live'`; AEA-10's `last_started_wall()` is live-only | `tests/services/test_alerts.py::test_test_traffic_excluded` |
| AC-7 [invariant] | `AlertWriter.fire` thread-safe, one row while firing; a call after a clear writes a new one | lock + read-then-write in one `BEGIN IMMEDIATE` unit | `tests/services/test_alerts.py::test_alert_writer_once_while_firing` |
| AC-8 [invariant] | Thresholds have one home; cap injected | literals only in `AlertSettings`; cap stored as `self._cap_usd` | `rg -n '12\.5\|0\.02\|daily_cap_usd\s*=' src/meridian/services/health.py src/meridian/adapters/sqlite/repos_ops.py`; `tests/services/test_alerts.py::test_evaluator_uses_injected_cap` |
| AC-9 [invariant] | `load_eval_reports` idempotent by `run_id`, returns number new, summary stored as given, invalid file skipped with one `health_event` and no partial rows | §5 step 4b | `tests/services/test_load_eval_reports.py::test_loads_idempotently`, `::test_invalid_file_skipped` |
| AC-10 [negative] | Ops rows hold IDs, kinds, statuses, timings, values, counts only; `src/meridian/` imports nothing from `eval/` | evaluator/writer/watchdog write codes and numbers only | `tests/services/test_alerts.py::test_ops_records_hold_no_pii`; `rg -n '^from eval\|^import eval' src/meridian` → no match |
| AC-11 [invariant] | `restarts_by_day("America/Chicago")`, `last_restart()`, `deploy.latest()` | §5 step 2 | `tests/adapters/test_repos_ops.py::test_restart_and_deploy_reads` (restarts 23:30 and 00:30 Chicago → two days) |
| AC-12 [capture] | WF-17 at its real trigger: `Watchdog` against `create_app`'s async `/healthz` bound to the real `Heartbeat`, beat stopped → events in order, exit(1) | §5 step 7 harness | `tests/services/test_health_capture.py::test_watchdog_against_app_healthz` |
| AC-13 [journey] | Extends J-10: alert states in the monitoring read equal the stored `health_event` rows; `scheduler_last_run` reflects the newest `job_runs` row. **Level `mock-tested`** until AEA-57 and AEA-53 land | §5 step 8 | `uv run pytest -m journey tests/journeys/j10/test_aea_32.py` + record `docs/testing/journeys/<date>-AEA-32.md` (Level `mock-tested`, Blocked by AEA-57, AEA-53) |
| AC-14 [capture] | WF-17 alerts raised by the running watchdog: zero traffic (14:00 → 19:00 fires; 21:00 → 07:00 quiet) and `health_check_restart` after a restart, as seen by `latest_alert_states()` | §5 step 7 | `tests/services/test_health_capture.py::test_watchdog_raises_zero_traffic_and_restart_alerts` |
| AC-15 [regression/context] | Area-map row, ICM row, DO-3 status and `services/health.py` row | §5 step 9 | `git diff --name-only main...HEAD` shows the three files with only this ticket's rows |

### 3.2 Plan-added criteria (engineering; report them in your final report so the orchestrator can comment them on the issue)

| ID | Criterion | Test |
|---|---|---|
| PA-1 | `ops.deploy.set_status(deploy_id, status) -> bool` updates one `deploy_records` row's `status` (DDL has the column; AEA-50 AC-19 needs `started` → `completed`/`failed`); False for an unknown id | `tests/adapters/test_repos_ops.py::test_deploy_set_status` |
| PA-2 | `ops.health.latest_alert_states()` always returns all seven `AlertType` keys (quiet, `fired_at` None when no row) and reflects the newest `alert_fired`/`alert_cleared` row per type | `tests/adapters/test_repos_ops.py::test_latest_alert_states_defaults_and_newest_row` |
| PA-3 | `ops.signals` reads only live turns of live conversations, by `replied_at` window; `latest_live_trace_export()` is the newest finished live turn by insertion order | `tests/adapters/test_repos_ops.py::test_signals_read_live_turns_only` |
| PA-4 | Quiet hours are subtracted in absolute (UTC) time, so a DST night counts correctly | `tests/unit/services/test_health.py::test_time_outside_quiet_hours` |
| PA-5 | The watchdog evaluates on its first run and then once per `evaluate_every_s` of wall time | `tests/unit/services/test_health.py::test_watchdog_evaluates_on_schedule` |
| PA-6 | A hung process always exits: if writing the `restart` row fails, `exit(1)` is still called once | `tests/unit/services/test_health.py::test_watchdog_exits_even_if_restart_write_fails` |
| PA-7 | `register_ops` provides `deps.HEARTBEAT`, `Key("alert_writer")`, `Key("alert_settings")`; its starter runs the beat task and the watchdog thread on the lifespan loop and the closer stops both; an app without a web shell gets nothing; a start outside an event loop raises | `tests/unit/web/test_register_ops.py` (three tests, §7.1) |
| PA-8 | A missing reports directory returns 0 and writes nothing | `tests/services/test_load_eval_reports.py::test_missing_dir_returns_zero` |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| One `health_event` per check and per restart, with `agent_version` | DO-6 WF-17, *Records* | AC-3 | in-ticket | step 5 |
| `health_check_id` and `deploy_id` on every `health_event` | DO-6 WF-17 *Correlation*; AEA-50 AC-24 | no | **other-ticket / request**: `95_ops.sql` (AEA-10, verified at `135ad75`) has neither column and cases.md §8 `HealthEvent` lists neither. Needs an AEA-10 DDL follow-up, then a small AEA-32 follow-up. Not built here (§8 R-4) | AEA-10 follow-up, then AEA-32 follow-up |
| `deploy_record.status` transitions | DO-6 *Status values*; AEA-50 AC-19 | no | **added** PA-1 | step 2 |
| `DeployRecord` = DO-6 *Records* fields | cases.md §8; AEA-10 DDL | AC-1 | in-ticket; field names = AEA-10 columns (`git_commit`, `image_digest`, `config_hash`, `trace_export_on`, `status`) | step 2 |
| Alerts computed from stored rows only; on change only | cases.md §8 | AC-4 | in-ticket | step 4 |
| Live turns in the last 60 min of **wall** time (CAS-25) | cases.md §8 | AC-4 | in-ticket, **with a gap**: `turns` has no wall-time receipt column (`received_at` is the demo clock). This plan windows by `turns.replied_at`; web.md §9 says `TurnService` stamps it but names no clock, and AEA-10's own test builder stamps it with demo time. Request to AEA-40 (§8 R-1) | step 2 (`SignalsRepo`), request to AEA-40 |
| Last live conversation start in wall time (M-22) | cases.md §8 | AC-4 | in-ticket via AEA-10's `conversations.last_started_wall()`; **request** AEA-40 sets `started_wall_at` (§8 R-2); fallback anchor when none is stored (§5 step 4) | step 4 |
| `trace_export_failed` fires on `failed` or `off`, clears on `sent` (MC-24) | cases.md §8 | AC-4 | in-ticket | step 4 |
| `/healthz` never touches SQLite or the pool | DO-3 §2.3 rule 3; web.md §7 | AC-2 | in-ticket (`Heartbeat` is pure) | step 3 |
| Alert timers on the wall clock (`get_wall_clock()`, MC-20) | web.md §4 | — | in-ticket: every wall reading comes from the injected callable; the container passes `deps.WALL_CLOCK` | steps 4–6 |
| Spend cap from `limits.spend.daily_cap_usd` (MC-22) | models.md §6 | AC-8 | in-ticket | step 6 |
| Reset keeps ops tables | cases.md §1.3 | — | n/a here: AEA-10's `migrate.KEPT_TABLES` / `clear_demo_tables` never clear them; this ticket adds no reset path | — |
| `load_eval_reports` called at start-up after the deploy record | cases.md §8; data.md §9 item 3 | — | **other-ticket**: AEA-50's start-up calls it; this ticket provides the function | AEA-50 |
| `AlertWriter` bound to the trace sink's `on_alert` | models.md cross-topic 6 | — | **other-ticket**: AEA-19 binds it (built on its branch: `container.get(Key[Any]("alert_writer")).fire("trace_export_failed", reason)`); this ticket provides the key | AEA-19 |
| Overdue lives on CON-17, not here (CAS-30) | cases.md §8 | AC-5 | in-ticket | step 1 |
| Retention / pruning of `health_events` | DO-6 *Storage* | — | n/a: nothing prunes; ~5,760 check rows a day; noted (§8 R-11) | — |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| Health-check probe and watchdog restart (started by `register_ops`) | WF-17 | DO-6 *Covered workflows* WF-17 | CAP-9 (AEA-50, deployed level); M-28 |
| Start-up eval-report loader (`load_eval_reports`, called by AEA-50) | WF-13 neighbourhood (CAS-27, DAT-14) | cases.md §8; data.md §9 item 3 | CON-20 reads (AEA-53) |

---

## 4. Shared code to use (exact shapes; copied, not paraphrased)

### 4.1 From AEA-02 (merged on `main`)

```python
# meridian.domain.common
class MeridianModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
CustomerId   # validated str, MHC-\d{5}
ThreadId     # validated str, UUID4
# meridian.domain.turn  (re-exported by meridian.ports.runtime)
ExportStatus = Literal["off", "sent", "failed"]
RunTag = Literal["live", "eval", "load"]
DegradeReason = Literal["model_error", "tool_error", "timeout", "brake", "spend_cap", "rate_limit"]
# meridian.ports.runtime
class UnitOfWork(Protocol):
    core: CoreRepos; spend: SpendRepo; identity: IdentityRepos; booking: BookingRepos
    cases: CaseRepos; staff: StaffRepos; ops: OpsRepos
    def commit(self) -> None: ...
class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
# meridian.config
class Settings(MeridianModel):  # required: anthropic_api_key, openrouter_api_key, demo_username, demo_password,
    ...                         #   session_secret (all SecretStr); data_dir: Path = Path("var"); agent_version: str = "dev";
                                #   issued_db_path: Path = Path("docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite")
```

The shell on `main` today (you replace the body; keep the class name, the constructor and the runtime `import sqlite3`):

```python
"""Repository shell for health events and alerts (AEA-02 shell; body: AEA-32, cases.md section 8)."""
from __future__ import annotations
import sqlite3
class OpsRepos:
    """health events and alerts. Body by AEA-32; AEA-02 creates the constructor only."""
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
```

`tests/unit/adapters/test_repo_shells.py::test_seven_shells_one_constructor` asserts, for `OpsRepos`:
`typing.get_type_hints(OpsRepos.__init__) == {"conn": sqlite3.Connection, "return": NoneType}` and, on `main` today,
`[n for n in vars(OpsRepos) if not n.startswith("_")] == []`. AEA-10's branch scopes that second assertion to classes whose
docstring still contains `"AEA-02 creates the constructor only"`. **Satisfy both versions:** `OpsRepos` gets only class-level
annotations (no values) and `__init__` (annotations are stored in `__annotations__`, not as public members); every method
lives on the sub-repository classes; replace the class docstring with the one in §4.5 (it no longer contains that phrase).
`import sqlite3` stays a runtime import (not under `TYPE_CHECKING`) so `get_type_hints` resolves it.

### 4.2 From AEA-10 (wave 1; verified against branch `aea-10-aea-10-storage` at `135ad75`)

```python
# meridian.adapters.sqlite.db
class StorageError(Exception):                     # __init__(self, table: str, constraint: str); str(exc) == f"{table}: {constraint}"
    table: str; constraint: str
@contextmanager
def integrity_errors(table: str) -> Iterator[None]: ...     # sqlite3.IntegrityError → StorageError(table, kind) from None
def connect(path: Path, *, read_only: bool = False, busy_timeout_ms: int = BUSY_TIMEOUT_MS) -> sqlite3.Connection: ...
    # isolation_level=None, check_same_thread=False, WAL, busy_timeout 5000 ms, foreign_keys=ON
def format_wall(dt: datetime) -> str: ...          # tz-aware → dt.astimezone(UTC).isoformat() ("+00:00"); naive → ValueError("naive datetime")
def parse_wall(text: str) -> datetime: ...         # → tz-aware UTC; naive text → ValueError("naive timestamp")
def last_row_id(cur: sqlite3.Cursor, table: str) -> int: ...   # cur.lastrowid as int; None → StorageError(table, "no row id")
class SqliteUnitOfWork:                            # .core .spend .identity .booking .cases .staff .ops; commit()
    @property
    def connection(self) -> sqlite3.Connection: ...     # tests may run raw SQL through it
class SqliteUnitOfWorkFactory:                     # __init__(db_path: Path, *, busy_timeout_ms=...); .db_path
    # __call__(*, write=False, exclusive=False) -> ContextManager[SqliteUnitOfWork]; a NEW connection per unit
    # write=True → BEGIN IMMEDIATE; exclusive=True → BEGIN EXCLUSIVE; read → PRAGMA query_only=ON + BEGIN DEFERRED (no writes!)
    # exit without commit() → ROLLBACK; exception → ROLLBACK + propagate; connection closed on exit
# meridian.adapters.sqlite.rows
class ConversationRow(MeridianModel): thread_id: ThreadId; demo_session: str; run_tag: Literal["live","eval","load","seed"]
    run_id: str | None = None; agent_version: str; started_at: datetime; started_wall_at: datetime | None = None; ...
class CustomerRow(MeridianModel): customer_id: CustomerId; name: str; phone: str; email: str | None; ...
class JobRunRow(MeridianModel): job_run_id: str; started_wall_at: datetime; finished_wall_at: datetime | None; demo_now: datetime; ...
class ResetEventRow(MeridianModel): reset_id: str; at_wall: datetime; ...
class CaseRow(MeridianModel): ...                  # tests only (AC-5), built with helpers.case_row
# repositories, reached through the unit of work
tx.core.conversations.insert(row: ConversationRow) -> None      # tests only (fixtures)
tx.core.conversations.last_started_wall() -> datetime | None    # SELECT MAX(started_wall_at) … WHERE run_tag = 'live'
tx.core.reads.customer(customer_id: CustomerId) -> CustomerRow | None   # tests only (AC-10)
tx.cases.job_runs.start(job_run_id: str, *, started_wall_at: datetime, demo_now: datetime) -> None
tx.cases.job_runs.latest() -> JobRunRow | None     # ORDER BY started_wall_at DESC, job_run_id DESC
tx.cases.records.latest_reset_event() -> ResetEventRow | None
tx.cases.cases.insert(row: CaseRow) -> None        # tests only (AC-5)
# meridian.adapters.sqlite.repos_cases re-exports DEMO_START (defined in repos_cases_state.py):
DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
# tests.fixtures.sqlite
@dataclass(frozen=True)
class TempStore:
    data_dir: Path; db_path: Path; issued_path: Path; uow: SqliteUnitOfWorkFactory
@contextmanager
def temp_sqlite(*, issued_path: Path = ISSUED_DB) -> Iterator[TempStore]: ...   # every schema/*.sql applied; dir removed after
# tests.unit.adapters.sqlite.helpers (AEA-10's test builders; import, never edit)
def new_thread() -> ThreadId: ...
def customer_id(text: str) -> CustomerId: ...
def conversation(thread: ThreadId, **kw: Any) -> ConversationRow: ...   # defaults: run_tag "live", agent_version "test", started_at DEMO_START
def case_row(thread: ThreadId, ref: int = 9, **kw: Any) -> CaseRow: ...  # defaults: reason "fee_bearing_change", P2, lifecycle "unassigned"
# container hunk (register_storage): provides Key[SqliteUnitOfWorkFactory]("uow_factory") (building it migrates settings.data_dir)
```

`95_ops.sql` (verified at `135ad75` — the DDL you write against; never edit it):

```sql
health_events(id INTEGER PRIMARY KEY AUTOINCREMENT, at_wall TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('check_ok','check_failed','restart','alert_fired','alert_cleared')),
  alert_type TEXT NULL, reason_code TEXT NULL, value REAL NULL, threshold REAL NULL, agent_version TEXT NOT NULL)
deploy_records(deploy_id TEXT PRIMARY KEY, at_wall TEXT NOT NULL, agent_version TEXT NOT NULL, git_commit TEXT,
  image_digest TEXT, config_hash TEXT, trace_export_on INTEGER CHECK (trace_export_on IN (0,1)),
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('started','completed','failed','incomplete')))
eval_runs(run_id TEXT PRIMARY KEY, suite TEXT NOT NULL CHECK (suite IN ('worked-pairs','retrieval','e2e','load')),
  split TEXT CHECK (split IN ('dev','held-out')), agent_version TEXT NOT NULL, harness_commit TEXT NOT NULL,
  harness_digest TEXT NOT NULL, experiment_id TEXT, repeats INTEGER NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('started','completed','failed','incomplete')), cases_expected INTEGER NOT NULL,
  cases_scored INTEGER NOT NULL, index_manifest_hash TEXT, judge_spend_usd REAL NOT NULL DEFAULT 0,
  summary_json TEXT NOT NULL DEFAULT '{}', loaded_at TEXT)
eval_case_results(run_id TEXT NOT NULL, case_id TEXT NOT NULL, repeat INTEGER NOT NULL, thread_id TEXT,
  passed_hard INTEGER NOT NULL CHECK (passed_hard IN (0,1)), items TEXT NOT NULL DEFAULT '[]',
  outcome TEXT NOT NULL CHECK (outcome IN ('resolved','handed_off','degraded','environment_error')),
  in_scope INTEGER, topic TEXT, top3 TEXT NOT NULL DEFAULT '[]', below_floor INTEGER, PRIMARY KEY (run_id, case_id, repeat))
-- read by SignalsRepo (00_core.sql): conversations(thread_id PK, demo_session NOT NULL, run_tag ∈ live|eval|load|seed,
--   run_id, agent_version NOT NULL, started_at NOT NULL, started_wall_at, …);
-- turns(turn_id PK, thread_id, request_id, run_tag ∈ live|eval|load, run_id, agent_version, sequence, received_at — all NOT NULL
--   except run_id; status ∈ running|completed|failed NOT NULL; outcome ∈ answered|acted|safety_reply|handed_off|to_staff|degraded_handoff;
--   degrade_reason ∈ model_error|tool_error|timeout|brake|spend_cap|rate_limit; replied_at; server_ms; trace_export ∈ off|sent|failed;
--   specialists_run NOT NULL DEFAULT '[]'; …); messages(id, thread_id, role ∈ customer|assistant|representative, text, at — NOT NULL)
-- cases has no foreign key to conversations.
```

**If a merged AEA-10 name differs:** use the merged one. If `conversations.last_started_wall()` or
`records.latest_reset_event()` is missing, add the same read to **your** `SignalsRepo` (`SELECT MAX(started_wall_at)
FROM conversations WHERE run_tag = 'live'`; `SELECT at_wall FROM reset_events ORDER BY at_wall DESC LIMIT 1`) instead of
blocking, and say so in your report.

### 4.3 From AEA-23 (wave 1; not yet built — names from its plan) — hunk and capture tests only

```python
# meridian.web.deps (container keys; Key names are binding)
UOW_FACTORY: Key[UnitOfWorkFactory]      = Key("uow_factory")   # bound by AEA-10's register_storage
WALL_CLOCK:  Key[Callable[[], datetime]] = Key("wall_clock")    # bound by AEA-23's register_web (create_app's choice)
HEARTBEAT:   Key[HeartbeatReader]        = Key("heartbeat")     # bound by THIS ticket (AEA-23 plan D-P4)
class HeartbeatReader(Protocol):
    def fresh(self, mono: float) -> bool: ...
def get_heartbeat(request: Request) -> HeartbeatReader: ...    # providers take a Request; hunks NEVER call providers (D-P3)
# meridian.web.middleware
HEALTHZ_PATH = "/healthz"
@dataclass(frozen=True)
class WebShellState:            # app.state.web_shell, set by create_app BEFORE the lifespan builds the container
    settings: Settings; wall_clock: Callable[[], datetime]; public_paths: PublicPaths
class PublicPaths: ...          # PublicPaths() constructs an empty set; register_web adds ("exact","GET","/healthz")
# meridian.web.app
@dataclass(frozen=True)
class ContainerOverrides:       # choice, structured, tools, trace, wall_clock: Callable[[], datetime] | None = None
def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> FastAPI: ...
    # lifespan: container = build_container(app, settings, overrides=overrides) — referenced as the module global
    # meridian.web.app.build_container, so tests may monkeypatch it; app.state.container = container
async def healthz(request: Request) -> JSONResponse: ...
    # provided(app, get_heartbeat).fresh(time.monotonic()) → 200 {"status": "ok"} | 503 {"status": "stale"}
```

`/healthz` is a public path: the gate middleware takes no session and no wall-clock reading for it and never waits on the
reset gate, but it does read the reset gate (`RESET_GATE`, provided by `register_web`). So a harness that runs
`register_web` + `register_ops` over a temp store serves `/healthz` without any other hunk. AEA-23's own `full_app`
helper runs the real `build_container` with `Container.on_start` patched to a no-op and overrides the heartbeat through
`app.dependency_overrides[get_heartbeat]`; that override wins over our provided key, so the two never collide.

### 4.4 From AEA-01 (on `main`) and sibling hunks

```python
# meridian.web.container
@dataclass(frozen=True)
class Key[T]:
    name: str                                  # two keys are equal when their names are
class ContainerError(RuntimeError): ...        # "not provided: <name>", "provide after build: <name>", ...
class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    settings: Any (property); limits: Limits (property); closed: bool (property)
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...   # before build only
    def get[T](self, key: Key[T]) -> T: ...                                              # lazy, memoised
    def on_start(self, starter: Callable[[], None]) -> None: ...   # run by build(), after every object is built
    def on_close(self, closer: Callable[[], None]) -> None: ...    # run by close(), newest first
    def build(self) -> None: ...   # builds EVERY provided factory, then runs the starters
    def close(self) -> None: ...
def register_ops(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-32 ops: health events, heartbeat, watchdog, alerts (cases.md §8).

    No-op until AEA-32 fills it.
    """
# call order in build_container: register_storage, register_web, register_ops, register_tracing, register_spend, …
# module-level imports of container.py: contextlib, Callable, dataclass, TYPE_CHECKING/Any/cast, Limits (+ FastAPI under TYPE_CHECKING)
# meridian.policy.limits
@dataclass(frozen=True)
class SpendLimits:
    daily_cap_usd: float = 30.0
class Limits: ...; spend: SpendLimits          # limits.spend.daily_cap_usd
```

- **`tests/unit/web/test_container.py::test_every_register_stub_present`** checks `"AEA-32"` is in the docstring. On `main`
  it also calls every hunk with a bare `FastAPI()` expecting nothing provided; AEA-10's branch skips hunks whose docstring
  no longer says `"No-op until"`. Your docstring keeps `AEA-32` and drops `No-op until AEA-32 fills it.`, and the web-shell
  guard (§5 step 6) returns early on a bare `FastAPI()`, so the test is green under both versions.
- **AEA-19 (`register_tracing`, built on its branch)** binds the trace sink's `on_alert` to
  `container.get(Key[Any]("alert_writer")).fire("trace_export_failed", reason)` with `reason` ∈ `"wrong_project"`,
  `"project_check_failed"`, and logs a fixed line when the key is absent. Keep the key name `"alert_writer"` and the
  method `fire(alert_type, reason_code)` exactly.
- **AEA-26 (`register_spend`, planned)** provides `Key[LedgerService]("ledger")`; `LedgerService.spend_today(self) -> float`
  is USD for the current America/Chicago day (models.md §6). Read it as `Key[SpendReader]("ledger")` (keys are equal by name).

### 4.5 What this ticket exports — `src/meridian/adapters/sqlite/repos_ops.py`

```python
"""Ops repositories: health events, deploy records, eval results, alert inputs (AEA-32; stage7/cases.md §8)."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import JsonValue

from meridian.adapters.sqlite.db import format_wall, integrity_errors, last_row_id, parse_wall
from meridian.domain.common import MeridianModel
from meridian.ports.runtime import ExportStatus
# Import only what the body uses (ruff F401).

AlertType = Literal["spend_cap_reached", "p95_latency_over_12_5s", "health_check_restart", "zero_traffic",
                    "failure_rate_over_2pct", "trace_export_failed",            # = OpenAPI MonitorAlert.type
                    "scheduler_stale"]                 # stored only; CON-19 health tile (CAS-30). No overdue type.
ALERT_TYPES: tuple[AlertType, ...] = ("spend_cap_reached", "p95_latency_over_12_5s", "health_check_restart",
                                      "zero_traffic", "failure_rate_over_2pct", "trace_export_failed",
                                      "scheduler_stale")      # evaluation and return order
HealthKind = Literal["check_ok", "check_failed", "restart", "alert_fired", "alert_cleared"]
RunStatus = Literal["started", "completed", "failed", "incomplete"]

class HealthEvent(MeridianModel):                     # cases.md §8, verbatim fields
    at_wall: datetime; kind: HealthKind
    alert_type: AlertType | None; reason_code: str | None; value: float | None; threshold: float | None
    agent_version: str

class AlertState(MeridianModel):                      # cases.md §8, verbatim fields
    type: AlertType; state: Literal["firing", "quiet"]; fired_at: datetime | None
    value: float | None; threshold: float | None

class DeployRecord(MeridianModel):                    # DO-6 Records; names = AEA-10's deploy_records columns
    deploy_id: str; at_wall: datetime; agent_version: str
    git_commit: str | None = None; image_digest: str | None = None; config_hash: str | None = None
    trace_export_on: bool | None = None; status: RunStatus = "completed"

class EvalRunRow(MeridianModel):                      # data.md §6 EvalRunRecord, field for field
    run_id: str; suite: Literal["worked-pairs", "retrieval", "e2e", "load"]
    split: Literal["dev", "held-out"] | None; agent_version: str
    harness_commit: str; harness_digest: str; experiment_id: str | None
    repeats: int; started_at: datetime; finished_at: datetime | None
    status: RunStatus; cases_expected: int; cases_scored: int
    index_manifest_hash: str | None; judge_spend_usd: float

class StoredEvalRun(EvalRunRow):                      # what the store gives back (an EvalRunRow, plus two stored columns)
    summary_json: str                                 # stored as given; AEA-53 reads it, never recomputes
    loaded_at: datetime | None

class EvalCaseResultRow(MeridianModel):               # data.md §6 EvalCaseResult, field for field
    run_id: str; case_id: str; repeat: int; thread_id: str | None
    passed_hard: bool; items: tuple[dict[str, JsonValue], ...]      # ItemResult objects, kept as JSON
    outcome: Literal["resolved", "handed_off", "degraded", "environment_error"]
    in_scope: bool | None; topic: str | None
    top3: tuple[dict[str, JsonValue], ...] = (); below_floor: bool | None = None

class TurnSignal(MeridianModel):                      # one live turn as the alert evaluator needs it (codes and numbers only)
    status: Literal["running", "completed", "failed"]; outcome: str | None; degrade_reason: str | None
    server_ms: int | None

class HealthRepo:                                     # tx.ops.health
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def append(self, event: HealthEvent) -> int: ...
    def latest_alert_states(self) -> dict[AlertType, AlertState]: ...   # all seven keys (PA-2)
    def last_restart(self) -> HealthEvent | None: ...
    def restarts_by_day(self, tz: str) -> list[tuple[date, int]]: ...

class DeployRepo:                                     # tx.ops.deploy
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def insert(self, record: DeployRecord) -> None: ...
    def latest(self) -> DeployRecord | None: ...
    def set_status(self, deploy_id: str, status: RunStatus) -> bool: ...   # PA-1

class EvalRepo:                                       # tx.ops.eval
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def upsert_report(self, run: EvalRunRow, results: Sequence[EvalCaseResultRow], summary_json: str, *,
                      loaded_at: datetime | None = None) -> bool: ...
    def latest_completed(self, suite: Literal["worked-pairs", "retrieval", "e2e", "load"],
                         split: Literal["dev", "held-out"] | None) -> StoredEvalRun | None: ...
    def case_results(self, run_id: str) -> list[EvalCaseResultRow]: ...

class SignalsRepo:                                    # tx.ops.signals — read-only alert inputs over core tables (PA-3)
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def live_turns_replied_since(self, since: datetime) -> tuple[TurnSignal, ...]: ...
    def latest_live_trace_export(self) -> ExportStatus | None: ...

class OpsRepos:
    """Ops repositories over one connection (body AEA-32, cases.md §8): health, deploy, eval, signals."""
    health: HealthRepo                                # annotations only, no values (§4.1)
    deploy: DeployRepo
    eval: EvalRepo
    signals: SignalsRepo
    def __init__(self, conn: sqlite3.Connection) -> None: ...   # self._conn = conn; self.health = HealthRepo(conn); …
```

### 4.6 What this ticket exports — `src/meridian/services/health.py`

```python
"""Health events, heartbeat, watchdog and alerts (AEA-32; stage7/cases.md §8; DO-3 §4.4)."""
from __future__ import annotations

import json
import logging
import math
import threading
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import time as dtime
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

import anyio

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.repos_ops import (ALERT_TYPES, AlertState, AlertType, EvalCaseResultRow, EvalRunRow,
                                                HealthEvent)
from meridian.ports.runtime import UnitOfWorkFactory
# Import only what the body uses (ruff F401); let `ruff check --fix` / `ruff format` order the block.
logger = logging.getLogger("meridian.ops")

__all__ = ["ALERT_TYPES", "AlertEvaluator", "AlertSettings", "AlertState", "AlertType", "AlertWriter", "HealthEvent",
           "Heartbeat", "SpendReader", "Watchdog", "load_eval_reports", "p95_nearest_rank", "run_beats",
           "time_outside_quiet_hours"]

@dataclass(frozen=True)
class AlertSettings:                                   # the ONE place alert lines live (cases.md §8, verbatim)
    latency_p95_s: float = 12.5                        # [T] M-23
    failure_rate: float = 0.02                         # [T] M-24
    zero_traffic_after: timedelta = timedelta(hours=4) # [Decided Innocent 2026-10-21] M-22
    quiet_start: dtime = dtime(22); quiet_end: dtime = dtime(6); tz: str = "America/Chicago"   # [A, configurable] M-22
    turn_window: timedelta = timedelta(minutes=60)     # [A] CAS-25
    min_turns: int = 20                                # [A] below it, latency and failure-rate alerts stay quiet
    evaluate_every_s: int = 60                         # [A] CAS-25
    scheduler_stale_after_s: int = 180                 # [A] CAS-22
    heartbeat_every_s: int = 5; heartbeat_stale_after_s: int = 30    # [A] CAS-26
    probe_every_s: int = 15; probe_timeout_s: int = 5; failures_to_exit: int = 3   # [A, system design §8.2]
    # spend cap: not here — limits.spend.daily_cap_usd (MC-22), passed to AlertEvaluator by the container.
    # (write one field per line in the real file; the `;` lines above are only compact here)

class SpendReader(Protocol):                           # the one LedgerService method the evaluator reads (models.md §6);
    def spend_today(self) -> float: ...                #   LedgerService satisfies it structurally (no import of AEA-26)

class Heartbeat:                                       # implements AEA-23's HeartbeatReader structurally
    def __init__(self, settings: AlertSettings, *, started_mono: float | None = None) -> None: ...
    def beat(self, mono: float) -> None: ...
    def fresh(self, mono: float) -> bool: ...          # last is not None and mono - last <= heartbeat_stale_after_s

async def run_beats(heartbeat: Heartbeat, settings: AlertSettings, *,
                    run_sync: Callable[[Callable[[], None]], Awaitable[None]] = _to_pool,
                    sleep: Callable[[float], Awaitable[None]] = anyio.sleep,
                    monotonic: Callable[[], float] = time.monotonic) -> None: ...

def time_outside_quiet_hours(start: datetime, end: datetime, settings: AlertSettings) -> timedelta: ...
def p95_nearest_rank(values: Sequence[float]) -> float: ...   # non-empty; sorted(values)[ceil(0.95 * n) - 1]

class AlertWriter:                                     # cases.md §8
    def __init__(self, uow: UnitOfWorkFactory, wall_clock: Callable[[], datetime], agent_version: str) -> None: ...
    def fire(self, alert_type: AlertType, reason_code: str) -> None: ...

class AlertEvaluator:                                  # cases.md §8 + keyword-only agent_version (§8 R-5)
    def __init__(self, uow: UnitOfWorkFactory, ledger: SpendReader, settings: AlertSettings,
                 wall_clock: Callable[[], datetime], daily_cap_usd: float, *, agent_version: str) -> None: ...
    def evaluate(self) -> tuple[AlertState, ...]: ...  # seven states, ALERT_TYPES order

class Watchdog:                                        # cases.md §8 + keyword-only agent_version (§8 R-5)
    def __init__(self, uow: UnitOfWorkFactory, probe: Callable[[], bool], exit: Callable[[int], None],
                 evaluator: AlertEvaluator, settings: AlertSettings, wall_clock: Callable[[], datetime], *,
                 agent_version: str) -> None: ...
    def run_once(self) -> None: ...
    def run_until(self, stop: threading.Event) -> None: ...   # the thread body register_ops starts

def load_eval_reports(reports_dir: Path, uow: UnitOfWorkFactory, *,
                      wall_clock: Callable[[], datetime] = _utc_now, agent_version: str = "unknown") -> int: ...
```

`_to_pool` and `_utc_now` are module-private functions defined **above** `run_beats` / `load_eval_reports` (§5 steps 3, 4b).
The parameter name `exit` shadows a builtin inside `Watchdog.__init__` only; it is the contract's name (cases.md §8) — keep it
and, if ruff flags `A002`, that rule is not selected in `pyproject.toml` (`E, W, F, I, B, UP, S, RUF`), so no ignore is needed.

Re-export rule: consumers (AEA-53, AEA-19, AEA-50) may import `AlertType`, `AlertState`, `HealthEvent`, `ALERT_TYPES`
from `meridian.services.health`; the definitions stay in `repos_ops.py` (services import adapters/sqlite; never the
reverse, DO-3 §2.1).

**Container keys this ticket provides** (put them in the hunk docstring): `deps.HEARTBEAT` (`"heartbeat"`),
`Key[AlertWriter]("alert_writer")`, `Key[AlertSettings]("alert_settings")`. It **reads** `deps.UOW_FACTORY`
(`"uow_factory"`, AEA-10), `deps.WALL_CLOCK` (`"wall_clock"`, AEA-23) and `Key[SpendReader]("ledger")` (AEA-26).

---

## 5. Steps (build order; each step ends with a check)

Module boundary (DO-3 §2.1, rule `code-design-solid-modularity`): `repos_ops.py` holds all SQL and the row models; it
imports `db.py`, `domain`, `ports` only. `services/health.py` holds the rules and threads; it reaches storage only through
`tx.ops.*`, `tx.core.conversations.last_started_wall()`, `tx.cases.job_runs.latest()`,
`tx.cases.records.latest_reset_event()`; it imports nothing from `web/`, `eval/`, `services/ledger.py`, `sqlite3`,
`httpx` or `fastapi`. The container hunk is the only place that touches `asyncio`, `httpx`, `os._exit` and the app.
**Interfaces:** implements `UnitOfWork.ops` (body of AEA-02's `OpsRepos`) and AEA-23's `HeartbeatReader` (structurally);
consumes `UnitOfWorkFactory`, `SpendReader` (satisfied by AEA-26's `LedgerService`), the wall-clock callable. No other
new seam.

### Step 0 — environment and preconditions

1. `cd` into your worktree; `export UV_LINK_MODE=hardlink` in every shell; `uv sync` (never copy a venv; no
   `node_modules`).
2. Check these exist on your base (`ls`): `src/meridian/adapters/sqlite/db.py`, `src/meridian/adapters/sqlite/schema/95_ops.sql`,
   `src/meridian/adapters/sqlite/repos_ops.py` (shell), `tests/fixtures/sqlite.py`, `tests/unit/adapters/sqlite/helpers.py`,
   `src/meridian/web/deps.py`, `src/meridian/web/app.py`, `src/meridian/web/middleware.py`.
   If any is missing, **stop and report `blocked-on AEA-10` / `blocked-on AEA-23`**; do not create it.
3. `grep -n "HEARTBEAT\|UOW_FACTORY\|WALL_CLOCK\|class HeartbeatReader" src/meridian/web/deps.py` — all four present.
   If `HEARTBEAT` is absent, stop and report `blocked-on AEA-23 follow-up` (its plan D-P4 declares it).
4. Import check: `uv run python -c "import meridian.adapters.sqlite.db, meridian.web.app, tests.fixtures.sqlite"`.
5. `grep -n "No-op until" src/meridian/web/container.py | grep -c AEA-` and `grep -n "No-op until" tests/unit/web/test_container.py`
   — tells you which version of the stub test is on your base (§4.4); both are fine.

### Step 1 — read the merged shapes (no code)

`grep -n "def last_started_wall\|def latest_reset_event\|def latest\b\|class JobRunRow\|class TempStore\|def format_wall\|def last_row_id\|def integrity_errors\|class StorageError\|def connection" -r src/meridian/adapters/sqlite tests/fixtures`
and `sed -n '/CREATE TABLE IF NOT EXISTS health_events/,$p' src/meridian/adapters/sqlite/schema/95_ops.sql` (and the
`turns` / `conversations` / `messages` blocks of `00_core.sql`). Note any name that differs from §4 and use the merged one.

### Step 2 — `src/meridian/adapters/sqlite/repos_ops.py` (AC-1, AC-11, PA-1…PA-3)

Write §4.5 exactly. SQL rules: static SQL strings with `?` parameters only (no f-string SQL: ruff `S608`); every write
inside `with integrity_errors("<table>"):`; times written with `format_wall`, read with `parse_wall`; booleans as `0/1`;
JSON columns with `json.dumps(..., ensure_ascii=False, separators=(",", ":"))`. **No method commits** (the caller's unit of
work does).

- `HealthRepo.append(event)`: `cur = self._conn.execute("INSERT INTO health_events (at_wall, kind, alert_type, reason_code,
  value, threshold, agent_version) VALUES (?,?,?,?,?,?,?)", …)` inside `integrity_errors("health_events")`; return
  `last_row_id(cur, "health_events")`.
- `HealthRepo.latest_alert_states()`:
  1. `SELECT h.alert_type, h.kind, h.at_wall, h.value, h.threshold FROM health_events h JOIN (SELECT alert_type,
     MAX(id) AS id FROM health_events WHERE kind IN ('alert_fired','alert_cleared') AND alert_type IS NOT NULL GROUP BY
     alert_type) m ON h.id = m.id`.
  2. Start from `{t: AlertState(type=t, state="quiet", fired_at=None, value=None, threshold=None) for t in ALERT_TYPES}`.
  3. For each row whose `alert_type` is in `ALERT_TYPES` (skip any other string): `alert_fired` → `state="firing",
     fired_at=parse_wall(at_wall)`; `alert_cleared` → `state="quiet", fired_at=None`; `value`, `threshold` from the row.
  *Invariant:* the newest row by `id` decides (ids are AUTOINCREMENT, never reused).
- `HealthRepo.last_restart()`: newest `kind = 'restart'` row by `id` → `HealthEvent` (or `None`).
- `HealthRepo.restarts_by_day(tz)`: `SELECT at_wall FROM health_events WHERE kind = 'restart'`; group in Python by
  `parse_wall(at_wall).astimezone(ZoneInfo(tz)).date()`; return `sorted((day, count) ...)` ascending; days with no restart
  are absent.
- `DeployRepo.insert(record)`: plain `INSERT` of the eight columns (`trace_export_on` → `None | 0 | 1`).
  `latest()`: `ORDER BY at_wall DESC, rowid DESC LIMIT 1`. `set_status(deploy_id, status)`: `UPDATE … SET status = ?
  WHERE deploy_id = ?` inside `integrity_errors("deploy_records")`; return `cursor.rowcount == 1`.
- `EvalRepo.upsert_report(run, results, summary_json, *, loaded_at=None)` (numbered; invariant per step):
  1. `existing = self._get(run.run_id)` (`StoredEvalRun | None`, private helper).
  2. If `existing is not None` and `EvalRunRow.model_validate(existing.model_dump(exclude={"summary_json",
     "loaded_at"})) == run` and `existing.summary_json == summary_json` and `self.case_results(run.run_id) ==
     sorted(results, key=lambda r: (r.case_id, r.repeat))`: return `False`. *Invariant:* an unchanged report writes
     nothing (AC-1, AC-9 second call returns 0).
  3. `DELETE FROM eval_case_results WHERE run_id = ?`; `INSERT OR REPLACE INTO eval_runs (<16 columns>) VALUES (…)`
     with `summary_json` as given and `loaded_at` (`format_wall` or `NULL`); `executemany` `INSERT INTO
     eval_case_results (<11 columns>)`. *Invariant:* all inside the caller's transaction, so a failure leaves no partial
     report (AC-9).
  4. Return `True`.
  Note: `started_at` / `finished_at` are compared after a `format_wall` → `parse_wall` round trip, so build test values
  in UTC (or compare after `astimezone(UTC)`); `parse_wall` returns UTC-aware datetimes and pydantic equality compares the
  `datetime` objects (equal instants in different zones compare equal in Python, so this is safe either way).
- `EvalRepo.latest_completed(suite, split)`: `WHERE suite = ? AND status = 'completed' AND split IS ? ORDER BY
  finished_at DESC, started_at DESC LIMIT 1` → `StoredEvalRun`. `case_results(run_id)`: `ORDER BY case_id, repeat`.
- `SignalsRepo.live_turns_replied_since(since)`: `SELECT t.status, t.outcome, t.degrade_reason, t.server_ms FROM turns t
  JOIN conversations c ON c.thread_id = t.thread_id WHERE t.run_tag = 'live' AND c.run_tag = 'live' AND t.replied_at IS
  NOT NULL AND t.replied_at >= ?` with `format_wall(since)`. *Invariant:* eval, load and seed traffic never counts (AC-6);
  string comparison is valid because every stored value is `format_wall` UTC output (AEA-10 uses the same rule in
  `promises.list_open_past`).
- `SignalsRepo.latest_live_trace_export()`: same join and live filters, `AND t.trace_export IS NOT NULL ORDER BY
  t.rowid DESC LIMIT 1` → the value or `None`. (Insertion order, not a clock, so it is right whichever clock
  `replied_at` uses.)
- `OpsRepos.__init__`: `self._conn = conn`; `self.health = HealthRepo(conn)`; `self.deploy = DeployRepo(conn)`;
  `self.eval = EvalRepo(conn)`; `self.signals = SignalsRepo(conn)`. Nothing else on the class.

Check: `uv run pytest tests/adapters/test_repos_ops.py tests/unit/adapters -q` (write §7.1's repo tests alongside).

### Step 3 — `services/health.py` part 1: `AlertSettings`, `Heartbeat`, `run_beats` (AC-2)

1. `AlertSettings` exactly as §4.6, one field per line (the only place 12.5, 0.02, 4 h and the quiet hours appear as
   literals — AC-8; do not write those numbers in any docstring or comment elsewhere in the two files).
2. `Heartbeat.__init__`: `self._stale_after_s = settings.heartbeat_stale_after_s`; `self._last: float | None =
   started_mono`. `beat(mono)`: `self._last = mono`. `fresh(mono)`: `return self._last is not None and mono - self._last
   <= self._stale_after_s`. No lock (one float assignment). *Invariant:* never touches storage or the pool (AC-2).
   `started_mono` is the start-up grace: a process that has just started counts as fresh until its first pool beat, for at
   most `heartbeat_stale_after_s` (the container passes `time.monotonic()`; tests construct without it).
3. `def _pool_noop() -> None: return None` and `async def _to_pool(fn: Callable[[], None]) -> None: await
   anyio.to_thread.run_sync(fn)` (module-private).
4. `run_beats`: `while True: await run_sync(_pool_noop); heartbeat.beat(monotonic()); await
   sleep(settings.heartbeat_every_s)`. *Invariant:* the beat is recorded only after the no-op returned from a worker thread,
   so a fresh beat proves the loop **and** the pool (CAS-26). Exceptions propagate (the task ends, the heartbeat goes
   stale, the watchdog restarts the process — honest).

Check: `uv run pytest tests/unit/services/test_health.py -k "heartbeat or beat" -q`.

### Step 4 — `services/health.py` part 2: quiet hours, p95, `AlertWriter`, `AlertEvaluator` (AC-4…AC-8, AC-10)

**`time_outside_quiet_hours(start, end, settings)`** (numbered; invariant per step):
1. If either is naive → `ValueError("naive datetime")`. If `end <= start` → `timedelta(0)`.
2. `s, e = start.astimezone(UTC), end.astimezone(UTC)`; `total = e - s`. *Invariant:* all arithmetic on UTC values
   (subtracting two datetimes that share one `ZoneInfo` ignores DST; UTC does not).
3. `tz = ZoneInfo(settings.tz)`; for each local date `d` from `start.astimezone(tz).date() - timedelta(days=1)` to
   `end.astimezone(tz).date()` inclusive: if `quiet_start > quiet_end` (wraps midnight) the window is
   `[combine(d, quiet_start, tz), combine(d + 1 day, quiet_end, tz))`; if `quiet_start < quiet_end` it is
   `[combine(d, quiet_start, tz), combine(d, quiet_end, tz))`; if equal there is no window. Convert both ends to UTC;
   `quiet += max(timedelta(0), min(e, q1) - max(s, q0))`. (`datetime.combine(d, t, tzinfo=tz)`.)
4. Return `total - quiet`. Examples: 21:00 → 07:00 next day = 2 h; Sat 2026-10-31 20:00 CDT → Sun 2026-11-01 08:00 CST
   = 13 h absolute − 9 h quiet = 4 h.

**`p95_nearest_rank(values)`**: `ordered = sorted(values)`; `k = math.ceil(0.95 * len(ordered))`; return
`ordered[k - 1]` (n = 20 → the 19th value). Raise `ValueError` on empty input.

**`AlertWriter`**: `__init__` stores the three arguments and `self._lock = threading.Lock()`. `fire(alert_type,
reason_code)`:
1. `with self._lock, self._uow(write=True) as tx:` *Invariant:* the lock serialises threads in this process; `BEGIN
   IMMEDIATE` serialises against the evaluator and any other writer, so read-then-write is atomic (AC-7).
2. `if tx.ops.health.latest_alert_states()[alert_type].state == "firing": return` (rollback, nothing written).
3. `tx.ops.health.append(HealthEvent(at_wall=self._wall_clock(), kind="alert_fired", alert_type=alert_type,
   reason_code=reason_code, value=None, threshold=None, agent_version=self._agent_version))`; `tx.commit()`.

**`AlertEvaluator.__init__`**: store `uow`, `ledger`, `settings`, `wall_clock`, `self._cap_usd = daily_cap_usd`,
`agent_version`. (Name the attribute `_cap_usd`: the AC-8 grep pattern `daily_cap_usd\s*=` must not match anything.)

**`AlertEvaluator.evaluate()`** (numbered; invariant per step):
1. `now = self._wall_clock()`; naive → `ValueError("naive datetime")`.
2. `spent = self._ledger.spend_today()` **before** opening the unit of work. *Invariant:* no nested unit of work inside
   the write transaction (the ledger opens its own read unit).
3. `with self._uow(write=True) as tx:` `current = tx.ops.health.latest_alert_states()`. Build one decision per type,
   `fire: bool | None` (None = no evidence → leave the stored state as it is), `value`, `threshold`, `reason_code`:
   - `spend_cap_reached`: `fire = spent >= self._cap_usd`; value `spent`; threshold `self._cap_usd`; reason
     `"spend_at_or_over_cap"`.
   - `turns = tx.ops.signals.live_turns_replied_since(now - settings.turn_window)` (one read, used by the next two).
   - `p95_latency_over_12_5s`: `secs = [t.server_ms / 1000 for t in turns if t.server_ms is not None]`; if
     `len(secs) < settings.min_turns` → `fire=False`, value `None`; else `p95 = p95_nearest_rank(secs)`,
     `fire = p95 > settings.latency_p95_s`, value `p95`; threshold `settings.latency_p95_s`; reason `"p95_over_line"`.
   - `failure_rate_over_2pct`: `n = len(turns)`; if `n < settings.min_turns` → `fire=False`, value `None`; else
     `failed = sum(1 for t in turns if t.outcome == "degraded_handoff" and t.degrade_reason in ("model_error",
     "tool_error", "timeout"))` (M-24), `rate = failed / n`, `fire = rate > settings.failure_rate`; threshold
     `settings.failure_rate`; reason `"failure_rate_over_line"`.
   - `zero_traffic`: `anchor = tx.core.conversations.last_started_wall()`; if `None`, `anchor = max` of the
     `at_wall` of `tx.ops.deploy.latest()` and `tx.cases.records.latest_reset_event()` (those that exist); if still
     `None` → `fire=None`. Else `counted = time_outside_quiet_hours(anchor, now, settings)`, `fire = counted >
     settings.zero_traffic_after`, value `counted / timedelta(hours=1)`, threshold `settings.zero_traffic_after /
     timedelta(hours=1)`, reason `"no_new_live_conversation"`. *Invariant:* a reset clears conversations, so the reset
     time (or, on a fresh store, the deploy time) is the last moment we know the service was in use; a store with none
     of the three never fires (no evidence).
   - `health_check_restart` (R-G-23): `last = tx.ops.health.last_restart()`; `tz = ZoneInfo(settings.tz)`; if `last` is
     `None` → `fire=False`; else `fire = last.at_wall.astimezone(tz).date() == now.astimezone(tz).date()`; when firing,
     value = that day's count from `tx.ops.health.restarts_by_day(settings.tz)`, reason = `last.reason_code or
     "health_check_restart"`; threshold `None`.
   - `trace_export_failed`: `status = tx.ops.signals.latest_live_trace_export()`; `None` → `fire=None`; `"sent"` →
     `False`; `"failed"` / `"off"` → `True`, reason `f"turn_export_{status}"`; value and threshold `None` (MC-24).
   - `scheduler_stale`: `job = tx.cases.job_runs.latest()`; `None` → `fire=None` (CAS-22 defines staleness against a
     recorded tick; AEA-53's tile shows "never ran"); else `age = (now - job.started_wall_at).total_seconds()`,
     `fire = age > settings.scheduler_stale_after_s`, value `age`, threshold `float(settings.scheduler_stale_after_s)`,
     reason `"scheduler_tick_missed"`.
4. For each `t` in `ALERT_TYPES`: `cur = current[t]`. If `fire is True and cur.state == "quiet"` → append
   `alert_fired` (`at_wall=now`, value, threshold, reason) and the new state is `firing` with `fired_at=now`. If
   `fire is False and cur.state == "firing"` → append `alert_cleared` (`reason_code="condition_cleared"`, value,
   threshold) and the new state is `quiet`. Otherwise keep `cur`. *Invariant:* an event is written only on a change
   (AC-4); a second `evaluate()` with the same rows writes nothing.
5. `tx.commit()`; return the seven states in `ALERT_TYPES` order.
- Never read a `cases` row (no overdue alert, CAS-30, AC-5). Never write message text, a name, a phone, an email, a
  code, a key value or an exception message into a row or a log (AC-10).

### Step 4b — `load_eval_reports` (AC-9, PA-8)

```python
def _utc_now() -> datetime: return datetime.now(UTC)      # module-level default (cases.md §6 SchedulerJob precedent)
```
1. If `not reports_dir.is_dir()` → return `0`.
2. `new = 0`; for `path in sorted(reports_dir.glob("*.json"))` (the `.client_side_turn_timings.jsonl` files do not
   match):
   1. Parse: `raw = json.loads(path.read_text(encoding="utf-8"))`; it must be a `dict` with keys exactly `{"run",
      "results", "summary"}` and `raw["summary"]` a `dict`, else `ValueError("report shape")`;
      `run = EvalRunRow.model_validate(raw["run"])`; `results = tuple(EvalCaseResultRow.model_validate(r) for r in
      raw["results"])` (`raw["results"]` must be a list); `summary_json = json.dumps(raw["summary"],
      ensure_ascii=False, separators=(",", ":"))`. *Invariant:* the summary is never recomputed or reordered — key order
      is the file's (`json.loads` keeps it); see §8 R-7 for "byte for byte".
   2. `with uow(write=True) as tx: changed = tx.ops.eval.upsert_report(run, results, summary_json,
      loaded_at=wall_clock()); tx.commit()`.
   3. `except (OSError, ValueError, StorageError)` (covers `UnicodeDecodeError`, `json.JSONDecodeError`,
      pydantic `ValidationError`, naive datetimes): the unit of work already rolled back; write **one** event in its own
      write unit — `HealthEvent(at_wall=wall_clock(), kind="check_failed", alert_type=None,
      reason_code="eval_report_invalid", value=None, threshold=None, agent_version=agent_version)` — log one line
      `logger.warning("eval_report_invalid")` (no file content, no exception text), `continue`. *Invariant:* never
      half-loaded; one event per bad file.
   4. `new += int(changed)`.
3. Return `new` ("new" = newly stored: a new `run_id` or a changed report).

Check: `uv run pytest tests/services/test_load_eval_reports.py tests/services/test_alerts.py -q`.

### Step 5 — `services/health.py` part 3: `Watchdog` (AC-3, PA-5, PA-6)

`__init__`: store the arguments; `self._failures = 0`; `self._last_eval: datetime | None = None`;
`self._stopping: threading.Event | None = None`. Reason codes as module constants: `PROBE_NOT_OK = "healthz_not_ok"`,
`PROBE_ERROR = "healthz_error"`.

**`run_once()`** (numbered; invariant per step):
1. If `self._stopping` is set → return.
2. `try: ok = bool(self._probe()); reason = None if ok else PROBE_NOT_OK` / `except Exception: ok = False; reason =
   PROBE_ERROR` (never store the exception text).
3. If `self._stopping` is set → return. *Invariant:* a probe that timed out because the process is shutting down never
   becomes a `check_failed` row.
4. `now = self._wall_clock()`; `self._failures = 0 if ok else self._failures + 1`. *Invariant:* the count changes before
   any write, so a storage error cannot stop the count.
5. `try:` write one event (`kind="check_ok"` or `"check_failed"`, `reason_code=reason`, value/threshold `None`,
   `agent_version`) in its own write unit and commit; `finally: if self._failures >= self._settings.failures_to_exit:
   self._restart(now)`.
6. If a restart happened in step 5 → return (no evaluation).
7. If `self._last_eval is None or (now - self._last_eval).total_seconds() >= self._settings.evaluate_every_s`:
   `self._evaluator.evaluate()`; `self._last_eval = now`. (First run evaluates at once: PA-5.)

**`_restart(now)`**: `n = self._failures`; `try:` write `HealthEvent(at_wall=now, kind="restart", alert_type=None,
reason_code=f"healthz_failed_{n}_in_a_row", value=float(n), threshold=float(self._settings.failures_to_exit),
agent_version=…)` and commit; `finally: self._failures = 0; self._exit(1)`. *Invariant:* a hung process always exits,
exactly once per run of failures, even if the row cannot be written (PA-6).

**`run_until(stop)`**: `self._stopping = stop`; `while not stop.wait(self._settings.probe_every_s): try:
self.run_once() except Exception: logger.warning("watchdog_run_failed")` (one line, no exception text). The first probe
runs one interval after start, which gives the beat task time to run.

Check: `uv run pytest tests/unit/services/test_health.py -q`.

### Step 6 — the `register_ops` hunk in `src/meridian/web/container.py` (PA-7)

Edit **only** this function: keep its name, parameters and the first docstring line; replace the
`No-op until AEA-32 fills it.` paragraph and the empty body. Module-level imports of `container.py` must not change
(`tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`): import inside the function.

```python
def register_ops(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-32 ops: health events, heartbeat, watchdog, alerts (cases.md §8).

    Provides deps.HEARTBEAT (the Heartbeat /healthz reads), Key[AlertWriter]("alert_writer") (AEA-19 binds the trace
    sink's on_alert to it) and Key[AlertSettings]("alert_settings") (AEA-53). Its starter runs the heartbeat task on the
    lifespan's event loop and the watchdog thread; it reads Key("uow_factory") (AEA-10), Key("wall_clock") (AEA-23) and
    Key("ledger") (AEA-26). An app that create_app did not build has no /healthz to probe, so this does nothing.
    """
    import asyncio
    import contextlib
    import os
    import threading
    import time

    import httpx

    from meridian.services.health import (AlertEvaluator, AlertSettings, AlertWriter, Heartbeat, SpendReader,
                                          Watchdog, run_beats)
    from meridian.web import deps
    from meridian.web.middleware import HEALTHZ_PATH, WebShellState

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    alert_settings = AlertSettings()
    agent_version = str(settings.agent_version)
    heartbeat = Heartbeat(alert_settings, started_mono=time.monotonic())
    running: dict[str, Any] = {}

    container.provide(Key[AlertSettings]("alert_settings"), lambda _c: alert_settings)
    container.provide(deps.HEARTBEAT, lambda _c: heartbeat)
    container.provide(
        Key[AlertWriter]("alert_writer"),
        lambda c: AlertWriter(c.get(deps.UOW_FACTORY), c.get(deps.WALL_CLOCK), agent_version),
    )

    def hard_exit(code: int) -> None:
        os._exit(code)            # sys.exit in a thread would end only the thread; Railway restarts on a non-zero exit

    def start() -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("register_ops: start needs the app lifespan's running event loop") from None
        uow = container.get(deps.UOW_FACTORY)
        wall_clock = container.get(deps.WALL_CLOCK)
        evaluator = AlertEvaluator(uow, container.get(Key[SpendReader]("ledger")), alert_settings, wall_clock,
                                   limits.spend.daily_cap_usd, agent_version=agent_version)

        async def healthz_ok() -> bool:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://watchdog.local") as client:
                response = await client.get(HEALTHZ_PATH)
            return response.status_code == 200

        def probe() -> bool:
            future = asyncio.run_coroutine_threadsafe(healthz_ok(), loop)
            try:
                return future.result(timeout=alert_settings.probe_timeout_s)
            except Exception:
                future.cancel()
                return False

        watchdog = Watchdog(uow, probe, hard_exit, evaluator, alert_settings, wall_clock, agent_version=agent_version)
        stop = threading.Event()
        thread = threading.Thread(target=watchdog.run_until, args=(stop,), name="meridian-watchdog", daemon=True)
        running.update(loop=loop, stop=stop, thread=thread,
                       task=loop.create_task(run_beats(heartbeat, alert_settings), name="meridian-heartbeat"))
        thread.start()

    def close() -> None:
        stop = running.get("stop")
        if stop is not None:
            stop.set()
            running["thread"].join(timeout=1.0)
        task, loop = running.get("task"), running.get("loop")
        if task is not None and loop is not None:
            with contextlib.suppress(RuntimeError):
                loop.call_soon_threadsafe(task.cancel)

    container.on_start(start)
    container.on_close(close)
```

Notes the implementer must keep:
- **Why the probe goes through `ASGITransport`:** it calls the real `/healthz` route (middleware included) on the real
  event loop without needing the listening port (`Settings` has no port field). A hung loop never runs the coroutine
  → `future.result` times out → `False`; a stale heartbeat → 503 → `False`. The socket path is Railway's own health check
  (AEA-50).
- **Who closes what (rule `async-safety` §2):** the beat task is cancelled and the watchdog thread is stopped and joined by
  `close()`, which `container.close()` runs from the lifespan's `finally`; the `httpx.AsyncClient` is closed by its own
  `async with` on every probe.
- The evaluator and watchdog are built **in the starter**, not as providers: `Container.build()` builds every provided
  factory, and AEA-23's `full_app` test helper runs the real `build_container` with `on_start` patched to a no-op, so
  nothing here may need `ledger` outside the starter.
- `container.py` already imports `contextlib` at module level; the `import contextlib` inside the hunk is harmless — keep the
  hunk self-contained, and keep `Any` / `Key` from the module (they are already in scope).
- `mypy`: if `Key[SpendReader]("ledger")` vs AEA-26's `Key[LedgerService]` raises a type complaint, keep
  `Key[SpendReader]` (keys are equal by name, §4.4). Do not add `# type: ignore` unless mypy reports a real error you
  cannot express otherwise; if you add one, give the error code (`# type: ignore[<code>]`) and say why in your report.

Check: `uv run pytest tests/unit/web -q` and `uv run pytest tests/unit/test_import_direction.py -q`.

### Step 7 — capture tests against `create_app` (AC-12, AC-14, example pair)

Write `tests/services/ops_support.py` (§6) and `tests/services/test_health_capture.py` (§7.1). The harness function
`build_ops_app` monkeypatches `Container.on_start` to a no-op (no real beat task, no real watchdog thread) and
`meridian.web.app.build_container` to a small builder that provides the temp store's factory and the ledger double, then
runs only `register_web` and `register_ops`, then `create_app(settings, overrides=ContainerOverrides(wall_clock=wall))`.
The test drives its **own** `Watchdog` whose probe is `lambda: client.get("/healthz").status_code == 200`, against the
app's real `Heartbeat` (`app.state.container.get(deps.HEARTBEAT)`).

Check: `uv run pytest tests/services/test_health_capture.py -q -rP`.

### Step 8 — journey step and record (AC-13)

1. Write `tests/journeys/j10/test_aea_32.py` (§7.1).
2. `uv run pytest -m journey tests/journeys/j10/test_aea_32.py -q` → 1 passed.
3. `uv run python -m tests.journeys.affected --base main` → any change under `tests/journeys/` selects every journey file
   present; all pass.
4. Write the record (§7.4) **after** the feat commit exists (it names the SHA).

### Step 9 — context (AC-15), in the docs commit

- `.claude/reference/area-map.md`, the A10a row (`| … | **A10a Ops** | … | AEA-19, 32 | … |`): change only its status cell to
  add `built: services/health.py, adapters/sqlite/repos_ops.py (AEA-32, <feat sha>)` (keep any annotation AEA-19 or another
  ticket already added; `95_ops.sql` stays on AEA-10's A0 row).
- `.claude/state/icm-progress.md`: add one row directly after the last *Routes verified against code and tests* row:
  `| Routes verified against code and tests | provisional | <date>: area map A10a → services/health.py, repos_ops.py checked against tests/adapters/test_repos_ops.py, tests/unit/services/test_health.py, tests/services/test_{alerts,load_eval_reports,health_capture}.py (AEA-32, <sha>; <N> pass) | Verified when every area-map row is actual |` (≤ 400 characters).
- `docs/design/code-design.md` §3: append `· services/health.py, adapters/sqlite/repos_ops.py (body) (AEA-32, <sha>)` to the
  **first** `**Built:**` line (or add a new `**Built:**` line in the same style if the merge order made that awkward);
  §4.4 row `services/health.py`: interface cell becomes
  `` `AlertSettings`, `Heartbeat`, `Watchdog`, `AlertWriter`, `AlertEvaluator`, `load_eval_reports` (stage7/cases.md §8; built AEA-32) `` — nothing else in the file.

### Step 10 — commits (explicit paths; never `git add -A`; never push; never force-push)

1. `git add src/meridian/adapters/sqlite/repos_ops.py src/meridian/services/health.py src/meridian/web/container.py tests/adapters/__init__.py tests/adapters/test_repos_ops.py tests/unit/services/test_health.py tests/services/ops_support.py tests/services/test_alerts.py tests/services/test_load_eval_reports.py tests/services/test_health_capture.py tests/unit/web/test_register_ops.py tests/journeys/j10/test_aea_32.py`
   then commit `feat(AEA-32): ops health events, heartbeat, watchdog, alerts`.
2. `git add docs/testing/journeys/<run-date>-AEA-32.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`
   then commit `docs(AEA-32): journey record and context for services/health.py`.
3. The **last line** of every commit message is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

## 6. Data and fixtures (synthetic only)

All in `tests/services/ops_support.py` unless noted. No literal phone number, code, card-like number or secret anywhere.
Rows are written through `store.uow(write=True)` units and `tx.commit()`; raw SQL goes through `tx.connection.execute(...)`
(the write unit's own connection), never a second connection.

| Fixture | Value | Source |
|---|---|---|
| `chi(y, mo, d, h, mi=0) -> datetime` | `datetime(y, mo, d, h, mi, tzinfo=ZoneInfo("America/Chicago"))`; baseline `chi(2026, 10, 21, 14, 0)` | synthetic |
| `FakeWall(now)` | callable object: `__call__` returns `self.now`; tests assign `wall.now = …` (not `tests.fakes.FixedClock`: that is a Chicago-only `Clock` with `.now()`, not a wall-clock callable) | synthetic |
| `LedgerDouble(spent: float = 0.0)` | `spend_today() -> float` returns `self.spent` (models.md §6: USD for the current Chicago day) | double honouring models.md §6 |
| `EvaluatorDouble` | `calls: int`; `evaluate()` increments and returns `()`; pass as `cast(AlertEvaluator, EvaluatorDouble())` | double |
| `ProbeDouble(answers)` | callable returning the next `bool` of a list (or raising when the item is an `Exception`) | double |
| `sentinel() -> str` | `"sentinel-" + uuid.uuid4().hex` | synthetic |
| `make_settings(data_dir: Path) -> Settings` | `Settings.model_validate({"anthropic_api_key": sentinel(), "openrouter_api_key": sentinel(), "demo_username": sentinel(), "demo_password": sentinel(), "session_secret": sentinel(), "data_dir": data_dir, "agent_version": "test-ops"})` | synthetic |
| `add_conversation(store, *, run_tag, started_wall_at) -> ThreadId` | `thread = new_thread()`; `tx.core.conversations.insert(conversation(thread, run_tag=run_tag, started_wall_at=started_wall_at))`; commit (builders from `tests.unit.adapters.sqlite.helpers`) | synthetic |
| `add_turn(store, thread_id, *, run_tag, replied_at, server_ms=4000, status="completed", outcome="answered", degrade_reason=None, trace_export="sent") -> str` | `tx.connection.execute("INSERT INTO turns (turn_id, thread_id, request_id, run_tag, agent_version, sequence, received_at, status, outcome, degrade_reason, replied_at, server_ms, trace_export) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", …)`; ids `str(uuid4())`; `agent_version "test-ops"`; `sequence` = a module counter; `received_at = format_wall(DEMO_START)`; `replied_at = format_wall(replied_at)` | synthetic |
| `add_message(store, thread_id, text)` | `tx.connection.execute("INSERT INTO messages (thread_id, role, text, at) VALUES (?, 'customer', ?, ?)", (thread_id, text, format_wall(DEMO_START)))` | synthetic text built from issued values at run time (AC-10 only) |
| `ops_rows(store) -> list[str]` | in a read unit, every row of `health_events`, `deploy_records`, `eval_runs`, `eval_case_results` as `json.dumps(list(row), default=str)` | read-back |
| `build_ops_app(monkeypatch, *, store, settings, wall, ledger) -> FastAPI` | §5 step 7; builder `def build(app, settings, *, overrides=None) -> Container`: `c = Container(settings=settings, limits=Limits())`; `c.provide(deps.UOW_FACTORY, lambda _c: store.uow)`; `c.provide(Key[object]("ledger"), lambda _c: ledger)`; `register_web(c, app, settings=settings, limits=c.limits)`; `register_ops(c, app, settings=settings, limits=c.limits)`; `c.build()`; `return c`. `monkeypatch.setattr(Container, "on_start", lambda self, starter: None)` and `monkeypatch.setattr("meridian.web.app.build_container", build)`; return `create_app(settings, overrides=ContainerOverrides(wall_clock=wall))` | harness |
| Issued customer (AC-10) | `tx.core.reads.customer(customer_id("MHC-10002"))` read at run time from the temp copy; its `name` (first word) and `phone` are used in memory only, **never printed or written in source** | issued data (read only) |
| Eval reports (AC-9) | built in `tmp_path` by the test: two valid files `<run_id>.json` written with `json.dumps(obj, separators=(",", ":"))` (run: `suite "worked-pairs"`, `split None`, `agent_version "test-ops"`, `harness_commit "abc123def456"`, `harness_digest "d1g3st"`, `experiment_id None`, `repeats 1`, UTC-aware ISO `started_at`/`finished_at`, `status "completed"`, `cases_expected 2`, `cases_scored 2`, `index_manifest_hash None`, `judge_spend_usd 0.0`; results: `WP-1` and `WP-3`, repeat 0, `passed_hard true`, `items [{"item": "must_do", "index": 0, "passed": true, "failing_quote": null}]`, `outcome "resolved"`, `in_scope true`, `topic "billing"`; summary `{"measures": {"passed": {"n": 2, "of": 2}}, "mix": {"billing": 1}}`), plus one truncated file (the first 40 bytes of a valid file) | synthetic |
| Overdue cases (AC-5) | three `case_row(new_thread(), ref, due_at=DEMO_START - timedelta(days=1), created_at=DEMO_START - timedelta(days=2), updated_at=DEMO_START - timedelta(days=2))` rows for `ref` 101, 102, 103 (`MHC-C-0101…0103`; helper defaults: `fee_bearing_change`, `P2`, `unassigned`), inserted with `tx.cases.cases.insert` | synthetic |

---

## 7. Checks

### 7.1 Tests you write with the code (names are binding)

**`tests/adapters/test_repos_ops.py`** (all use `temp_sqlite()`; `store.uow(write=True)` then `tx.commit()`)
- `test_round_trips` (AC-1): append one `HealthEvent` of each of the five kinds (alert ones with `alert_type`) at
  `chi(2026,10,21,14,0)`; insert a `DeployRecord` with every field set; upsert one report; read back: `last_restart()` equals
  the restart event; `deploy.latest()` equals the record; `latest_completed("worked-pairs", None)` equals the run plus
  `summary_json`; `case_results(run_id)` equals the results; the raw `at_wall` text ends with `+00:00` and equals
  `"2026-10-21T19:00:00+00:00"`.
- `test_upsert_report_by_run_id` (AC-1): first upsert → `True`; same again → `False`; `SELECT COUNT(*) FROM eval_runs` = 1;
  changed `cases_scored` → `True` and the stored row shows the new value; results replaced, not duplicated.
- `test_restart_and_deploy_reads` (AC-11): restarts at `chi(2026,10,21,23,30)` and `chi(2026,10,22,0,30)` →
  `restarts_by_day("America/Chicago") == [(date(2026,10,21), 1), (date(2026,10,22), 1)]`; `last_restart().at_wall` is the
  00:30 one; two deploy records → `latest()` is the newer.
- `test_deploy_set_status` (PA-1): insert `status="started"` → `set_status(id, "completed")` is `True` and `latest().status`
  is `"completed"`; unknown id → `False`.
- `test_latest_alert_states_defaults_and_newest_row` (PA-2): empty store → seven keys, all quiet, `fired_at None`; fired
  then cleared then fired for one type → `firing` with the last `fired_at`.
- `test_signals_read_live_turns_only` (PA-3): live/live turn in window counted; eval, load turns and a turn of a `seed`
  conversation excluded; a turn with `replied_at` before `since` excluded; `latest_live_trace_export()` returns the most
  recently inserted live turn's value even when an older row has a later `replied_at`.

**`tests/unit/services/test_health.py`**
- `test_heartbeat_fresh_and_stale` (AC-2): `hb = Heartbeat(AlertSettings())` → `fresh(100.0)` False (never beaten);
  `beat(100.0)` → `fresh(130.0)` True, `fresh(130.001)` False; `Heartbeat(AlertSettings(), started_mono=50.0).fresh(60.0)`
  True. Plus an AST check: parse `src/meridian/services/health.py`, find `ClassDef Heartbeat` and `AsyncFunctionDef
  run_beats`; no `Name`/`Attribute` in them is `sqlite3`, `uow`, `tx`, `UnitOfWork` or `UnitOfWorkFactory`.
- `test_beat_goes_through_pool` (AC-2): `asyncio.run(main())`. (a) `run_sync` double that records the function and calls
  it; `sleep` double that records and then awaits a never-set `asyncio.Event`; `monotonic=lambda: 100.0`; create the task,
  `await asyncio.sleep(0)` a few times, cancel it → `hb.fresh(100.0)` True and the recorded function is the module's pool
  no-op. (b) a "saturated pool" `run_sync` double that awaits a never-set event → after the same spins `hb.fresh(100.0)`
  is False and `sleep` was never called.
- `test_watchdog_exits_after_three_failures` (AC-3): temp store; `ProbeDouble([True, False, False, False])`;
  `exits: list[int] = []`; `Watchdog(store.uow, probe, exits.append, cast(AlertEvaluator, EvaluatorDouble()),
  AlertSettings(), wall, agent_version="test-ops")`; four `run_once()` → `health_events` kinds in id order:
  `check_ok, check_failed, check_failed, check_failed, restart`; `exits == [1]`; restart row has `at_wall` and
  `reason_code == "healthz_failed_3_in_a_row"`.
- `test_success_resets_count` (AC-3): probes `False, False, True, False` → `exits == []`; four check rows, no restart.
- `test_restart_alert_clears_next_chicago_day` (AC-4, R-G-23): restart row at `chi(2026,10,21,14,0)`; evaluator with
  `LedgerDouble(0.0)`; wall 14:01 → one `alert_fired` `health_check_restart`; 23:59 → no new row, still firing; a second
  restart row at 23:58 → evaluate at 23:59 → still exactly one `alert_fired`; `chi(2026,10,22,0,5)` → exactly one
  `alert_cleared`.
- `test_time_outside_quiet_hours` (PA-4): 21:00 → 07:00 next day = 2 h; 14:00 → 19:00 = 5 h; 2026-10-31 20:00 →
  2026-11-01 08:00 Chicago = 4 h; `AlertSettings(quiet_start=time(6), quiet_end=time(6))` → no quiet window; naive input →
  `ValueError`.
- `test_watchdog_evaluates_on_schedule` (PA-5): probes all `True`; wall 14:00:00, 14:00:15, 14:00:59, 14:01:00 →
  `EvaluatorDouble.calls == 2`.
- `test_watchdog_exits_even_if_restart_write_fails` (PA-6): a uow double wrapping `store.uow` whose 4th `write=True` entry
  (the restart write) raises `StorageError("health_events", "CHECK")`; three failing probes → `exits == [1]` and the
  exception propagates from `run_once`.

**`tests/services/test_alerts.py`** (temp store; `FakeWall`; `LedgerDouble`; cap `Limits().spend.daily_cap_usd` unless stated)
- `test_each_alert_fires_and_clears` (AC-4), `@pytest.mark.parametrize("alert_type", ALERT_TYPES)`; per type, set the
  firing condition → `evaluate()` → exactly one `alert_fired` row of that type; set the clearing condition → one
  `alert_cleared`. Assert only on the type under test.
  - `spend_cap_reached`: `spent = cap` → fires; `spent = cap - 1` → clears.
  - `p95_latency_over_12_5s`: 20 live turns replied 10 min ago with `server_ms = 13_000` → fires; wall + 2 h → clears.
  - `failure_rate_over_2pct`: 20 live turns, one `degraded_handoff` / `model_error` → fires; wall + 2 h → clears.
  - `zero_traffic`: live conversation started `chi(…,14,0)`, wall `chi(…,19,0)` → fires; a new live conversation started
    at 19:00 → clears; separately (fresh store) start 21:00, wall next day 07:00 → no row at all.
  - `health_check_restart`: restart row at 14:00, wall 14:05 → fires; wall next day 00:05 → clears.
  - `trace_export_failed`: one live turn `trace_export="failed"` → fires; a newer live turn `"sent"` → clears; then a newer
    `"off"` → fires again.
  - `scheduler_stale`: `job_runs.start("job-1", started_wall_at=wall() - timedelta(seconds=300), demo_now=DEMO_START)` →
    fires; `job_runs.start("job-2", started_wall_at=wall() - timedelta(seconds=10), …)` → clears.
- `test_no_duplicate_events_without_change` (AC-4): spend at cap → two `evaluate()` → one `alert_fired` total; then quiet
  everywhere → two more `evaluate()` → one `alert_cleared` total.
- `test_overdue_is_not_a_health_alert` (AC-5): three overdue cases (§6) → `evaluate()` writes no `health_events` row;
  `set(ALERT_TYPES) == set(typing.get_args(AlertType))`; the OpenAPI enum read with `yaml.load(text,
  Loader=yaml.BaseLoader)` at `components.schemas.MonitorAlert.properties.type.enum` plus `"scheduler_stale"` equals
  `set(ALERT_TYPES)`; no `AlertType` value contains `"overdue"`.
- `test_test_traffic_excluded` (AC-6): live conversation started 5 h before a 19:00 wall; `eval`, `load` and `seed`
  conversations started 10 min ago → `zero_traffic` fires. Fresh store: 25 `load` turns (load conversation) with
  `server_ms = 20_000` replied 10 min ago → no `p95_latency_over_12_5s` row; 25 `eval` turns `degraded_handoff` /
  `timeout` → no `failure_rate_over_2pct` row.
- `test_alert_writer_once_while_firing` (AC-7): two threads, a `threading.Barrier(2)`, each calls
  `writer.fire("trace_export_failed", "wrong_project")` → 1 `alert_fired` row; append an `alert_cleared` for that type
  → `fire` again → 2 rows.
- `test_evaluator_uses_injected_cap` (AC-8): `daily_cap_usd=5.0`, `LedgerDouble(5.0)` → `spend_cap_reached` fires with
  `threshold == 5.0`.
- `test_ops_records_hold_no_pii` (AC-10): temp store; read MHC-10002's name and phone (§6); a live conversation with two
  messages whose text contains them; settings from `make_settings` (sentinel `session_secret`); run `AlertWriter.fire`,
  `AlertEvaluator.evaluate`, a `Watchdog` through three failing probes (exit recorder), insert a deploy record, load one
  valid report; then for every string in `ops_rows(...)`: the first name, the phone, the phone's digits only, and the
  session-secret value are absent. Print counts only.

**`tests/services/test_load_eval_reports.py`**
- `test_loads_idempotently` (AC-9): two valid files → first call returns 2, second 0; stored `summary_json ==
  json.dumps(file["summary"], ensure_ascii=False, separators=(",", ":"))` and `json.loads(stored) == file["summary"]`.
- `test_invalid_file_skipped` (AC-9): two valid + one truncated → returns 2; zero `eval_runs` rows for the truncated
  file's `run_id`; exactly one `health_events` row with `reason_code == "eval_report_invalid"`.
- `test_missing_dir_returns_zero` (PA-8): `tmp_path / "absent"` → 0, no rows.

**`tests/services/test_health_capture.py`** (uses `build_ops_app` + `fastapi.testclient.TestClient`)
- `test_watchdog_against_app_healthz` (AC-12): `with TestClient(app) as client:`; `hb = app.state.container.get(deps.HEARTBEAT)`,
  `assert isinstance(hb, Heartbeat)`; probe = `client.get("/healthz").status_code == 200`; run 1 → `check_ok`; then
  `hb.beat(time.monotonic() - (AlertSettings().heartbeat_stale_after_s + 1))` (the last beat was 31 s ago: the beat has
  stopped); runs 2–4 → three `check_failed`, then `restart`; `exits == [1]`. Print the rows (kind, reason_code).
- `test_watchdog_raises_zero_traffic_and_restart_alerts` (AC-14): (a) live conversation started `chi(2026,10,21,14,0)`,
  wall 19:00 → one `run_once()` → one `alert_fired` `zero_traffic` and `latest_alert_states()["zero_traffic"].state ==
  "firing"`; fresh store: start 21:00, wall next day 07:00 → no `alert_fired` row. (b) stop the beat as above → restart;
  a **second** `Watchdog` on the same store with the beat fresh again (`hb.beat(time.monotonic())`) → its first
  `run_once()` writes one `alert_fired` `health_check_restart`; `latest_alert_states()["health_check_restart"].state ==
  "firing"`. Print the alert rows and the two `AlertState`s.
- `test_example_pair_wf17` (example pair): wall `chi(2026,10,21,14,0)`, +15 s per probe; probes: ok, then beat stopped ×3
  → kinds `check_ok, check_failed, check_failed, check_failed, restart`, `exits == [1]`; second `Watchdog` → `alert_fired`
  `health_check_restart`; `restarts_by_day("America/Chicago") == [(date(2026,10,21), 1)]`.

**`tests/unit/web/test_register_ops.py`** (PA-7)
- `test_register_ops_provides_and_starts`: temp store; `app = FastAPI()`; `app.state.web_shell =
  WebShellState(settings=make_settings(tmp_path), wall_clock=FakeWall(chi(2026,10,21,14,0)), public_paths=PublicPaths())`;
  `c = Container(settings=…, limits=Limits())`; provide `deps.UOW_FACTORY`, `deps.WALL_CLOCK`, `Key[object]("ledger")`;
  `register_ops(c, app, settings=c.settings, limits=c.limits)`; inside `asyncio.run(main())`: `c.build()`; the three keys
  return a `Heartbeat`, an `AlertWriter` and `AlertSettings()`; a thread named `meridian-watchdog` is alive; a task named
  `meridian-heartbeat` is in `asyncio.all_tasks()`; `await asyncio.sleep(0.05)`; `c.close()`; `await asyncio.sleep(0)`.
  After `asyncio.run`: no live thread named `meridian-watchdog`; zero `health_events` rows (the first probe is 15 s away).
- `test_register_ops_ignores_app_without_web_shell`: bare `FastAPI()` → after `c.build()` nothing provided
  (`c.get(deps.HEARTBEAT)` raises `ContainerError`).
- `test_register_ops_start_needs_running_loop`: same setup as the first test, `c.build()` outside any loop →
  `RuntimeError` whose message names the running event loop.

**`tests/journeys/j10/test_aea_32.py`** (AC-13; `pytestmark = pytest.mark.journey`)

Module docstring: "J-10 (proposed extension, slice plan §0a): the monitoring read's alert states equal the stored
health_event rows, and the scheduler_last_run tile's source is the newest job_runs row. Level today: mock-tested (real
AlertEvaluator and repositories on a temp SQLite copy; no server, no MetricsReader). The integrated steps (CON-19 through
the real app with a scripted model) are blocked by AEA-57 (harness) and AEA-53 (metrics reader)."
- `test_j10_alert_states_match_stored_events`: temp store; wall `chi(2026,10,21,14,0)`; `job_runs` rows `job-older`
  (−10 min) and `job-newest` (−5 min); a restart row at 13:00; `AlertEvaluator(store.uow, LedgerDouble(31.0),
  AlertSettings(), wall, Limits().spend.daily_cap_usd, agent_version="j10").evaluate()`; then in a read unit:
  `stored = tx.ops.health.latest_alert_states()`, the newest alert row per type by raw SQL, `tx.cases.job_runs.latest()`.
  Assert: the returned states' `state` per type equal `stored`; each `firing` iff its newest row is `alert_fired`;
  `spend_cap_reached` (31.0 >= 30.0), `health_check_restart` (restart today) and `scheduler_stale` (newest tick 300 s old,
  over 180 s) are firing; `job_runs.latest().job_run_id == "job-newest"`. Define helpers locally or import from
  `tests.services.ops_support`.

### 7.2 Existing tests that must stay green

`tests/unit/web/test_container.py` (all — §4.4), `tests/unit/test_import_direction.py`, `tests/unit/adapters/test_repo_shells.py`
(`OpsRepos` keeps no public class member — §4.1), AEA-10's `tests/unit/adapters/sqlite/` and `tests/unit/web/test_register_storage.py`
(they construct `SqliteUnitOfWork`, which builds `OpsRepos`), AEA-23's `tests/api/` (its `full_app` runs the real
`register_ops`: it must provide its three keys without touching `ledger`), AEA-19's `tests/unit/web/test_register_tracing.py`
if it is on your base.

### 7.3 Gates (cheapest first; stop at the first red)

Affected set: `grep -rl "repos_ops\|services.health\|services import health\|web.container\|web import container\|adapters.sqlite.db\|SqliteUnitOfWork\|temp_sqlite" tests/`
plus the folders of this ticket's new tests.

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/adapters/sqlite/repos_ops.py src/meridian/services/health.py src/meridian/web/container.py tests/adapters tests/unit/services/test_health.py tests/services/ops_support.py tests/services/test_alerts.py tests/services/test_load_eval_reports.py tests/services/test_health_capture.py tests/unit/web/test_register_ops.py tests/journeys/j10/test_aea_32.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check <same paths>` | all already formatted (run `uv run ruff format <paths>` first if not) |
| 3 | Type check | `uv run mypy` | `Success: no issues found` |
| 4 | Threshold literals (AC-8) | `rg -n '12\.5\|0\.02\|daily_cap_usd\s*=' src/meridian/services/health.py src/meridian/adapters/sqlite/repos_ops.py` | matches only on the two `AlertSettings` lines (the `AlertType` literal `"p95_latency_over_12_5s"` uses `12_5`, not `12\.5`, so it does not match) |
| 5 | No eval import (AC-10) | `rg -n '^from eval\|^import eval' src/meridian` | no output |
| 6 | Affected tests | `uv run pytest -q tests/adapters tests/unit/services tests/services/test_alerts.py tests/services/test_load_eval_reports.py tests/services/test_health_capture.py tests/unit/web tests/unit/test_import_direction.py tests/unit/adapters tests/api` plus any other file the grep above lists (add `uv run --with pytest-xdist pytest -n 2 …` only if slow; never more than `-n 2`) | all passed; 0 failed |
| 7 | Affected journeys | `uv run pytest -m journey tests/journeys/j10/test_aea_32.py -q` then `uv run python -m tests.journeys.affected --base main` | 1 passed; affected run all green |
| 8 | Diff scope | `git diff --name-only main...HEAD` | only §2.1 files |

Full suite: **not** required (no shared fixture, settings, dependency or lock change; `container.py` changes in one hunk).
Iterate with the single test file you are working on; run all gates once before the final commit and paste the results in
your report.

### 7.4 Journey record — `docs/testing/journeys/<run-date>-AEA-32.md`

```markdown
# Journey record: AEA-32 ops health events, heartbeat, watchdog, alerts

| Field | Value |
|---|---|
| Claim | AEA-32 `services/health.py`, `adapters/sqlite/repos_ops.py`: health events per probe, restart and exit after three failures, alerts fired and cleared on change from stored rows, eval reports loaded by run_id (AC-1…AC-12, AC-14); J-10 step at mock level: alert states read back equal the stored health_event rows; the newest job_runs row is the scheduler tile's source |
| Level | `mock-tested` (AC-12/AC-14 drive create_app's real /healthz in process; no model involved) |
| Tested revision | `<feat sha>` |
| Environment | VPS, Python 3.12, `uv`; temp SQLite copy from `tests/fixtures/sqlite.py`; FastAPI TestClient over create_app with only register_web and register_ops; no port bound; no model adapter |
| Command | `uv run pytest tests/adapters/test_repos_ops.py tests/unit/services/test_health.py tests/services/test_alerts.py tests/services/test_load_eval_reports.py tests/services/test_health_capture.py tests/unit/web/test_register_ops.py -q`; `uv run pytest -m journey tests/journeys/j10/test_aea_32.py -q`; `uv run python -m tests.journeys.affected --base main` |
| Result | <N> passed; journey 1 passed; affected: <output summary> |
| Evidence location | GitLab issue #32 comment; this file |
| Remaining limitations | Window uses `turns.replied_at` (assumed wall UTC; AEA-40 stamps it); zero traffic needs AEA-40 to write `conversations.started_wall_at`; no `health_check_id`/`deploy_id` on health events (AEA-10 follow-up); the deployed restart (CAP-9) is AEA-50's |
| Blocked by | AEA-57 (journey harness) and AEA-53 (metrics reader, CON-19) for the integrated J-10 step; AEA-50 for the deployed restart |
| Journeys that will exercise this code | J-10 (monitoring read, at `integrated with a scripted model`); every journey's server start runs the heartbeat and watchdog |
```

---

## 8. Risks and requests

| ID | Risk / request | What to do |
|---|---|---|
| R-1 | **Turns have no wall-time receipt column.** CAS-25 asks for "live turns received in the last 60 min (wall)", but `turns.received_at` is the demo clock (graph-core §2; web.md §9 sweep note), which a clock advance moves by hours. This plan windows by `turns.replied_at`; web.md §9 says `TurnService` stamps it but names no clock, and AEA-10's test builder (`helpers.turn_record`) stamps it with demo time. If AEA-40 stamps `replied_at` from the demo clock, no turn ever falls in the window and the latency and failure-rate alerts stay quiet forever. | **Request to the orchestrator → AEA-40 planner:** stamp `TurnRecord.replied_at` from the injected wall clock (`get_wall_clock()`, UTC, MC-20), on every finished turn including `rate_limited`. Tests here write rows directly, so this ticket does not wait. AEA-51/53 seam checks should assert it. (Alternative if refused: an AEA-10 follow-up adding `turns.received_wall_at`, then a one-line change in `SignalsRepo`.) |
| R-2 | `conversations.started_wall_at` has no writer yet (AEA-10 plan R-6; the column exists at `135ad75`). Without it, zero traffic falls back to the newest reset or deploy time and fires 4 h (outside quiet hours) after it even with traffic. | **Request → AEA-40 planner:** `SessionService.open` writes `started_wall_at` from the wall clock. |
| R-3 | **Merge order inside wave 2: AEA-26 before AEA-32.** The starter reads `Key("ledger")`; with no ledger bound, the real start raises `ContainerError("not provided: ledger")` (loud, by design). Unit tests and AEA-23's `full_app` are unaffected (starter patched / ledger provided). | Orchestrator: merge AEA-26 first. If AEA-32 is ready first, it waits at the merge step; no code change. |
| R-4 | AEA-50 AC-24 wants `health_check_id` and `deploy_id` on every `health_event` (DO-6 WF-17 *Correlation*); neither `95_ops.sql` nor cases.md §8 has them. | **Request:** an AEA-10 DDL follow-up (two nullable TEXT columns) and an AEA-32 follow-up (fields on `HealthEvent`, set by `Watchdog`), both merged before AEA-50. Not built here (outside this ticket's ACs and DDL ownership). |
| R-5 | Additive refinements of the cases.md §8 sketch, made here: keyword-only `agent_version` on `AlertEvaluator` and `Watchdog` (their rows need it; the sketch omits it); `Heartbeat(settings, *, started_mono=None)`; `run_beats`; `Watchdog.run_until`; `SpendReader` Protocol for the ledger parameter (LedgerService satisfies it; avoids importing a same-wave sibling); `upsert_report(..., *, loaded_at=None)`; `load_eval_reports(..., *, wall_clock=…, agent_version="unknown")`; `ops.deploy.set_status`; `ops.signals`; `StoredEvalRun` (a subclass of the sketch's `EvalRunRow`, so `latest_completed`'s declared return still holds). Positional signatures and every named type are unchanged; the addenda are drafts, not signed contracts. | **Request:** one pointer sentence in `stage7/cases.md` §8 at the next docs pass (not this ticket's file). |
| R-6 | An invalid eval report is recorded as `kind = "check_failed"` with `reason_code = "eval_report_invalid"` (the only fitting kind of the five the DDL allows). | **Note to AEA-53:** count probe failures only where `reason_code` is `healthz_not_ok` or `healthz_error`. |
| R-7 | "Summary stored byte for byte": the stored text is the file's `summary` object re-serialised compactly in the file's key order. It equals the file's bytes when AEA-24 writes compact JSON; otherwise only whitespace differs, never a value or order. | **Note to AEA-24:** write reports with `separators=(",", ":")`. |
| R-8 | Wall-clock access in hunks: AEA-23's plan reads `container.get(deps.WALL_CLOCK)` (D-P3); AEA-26's plan uses the literal `Key("wall_clock")`. Both resolve the same object (keys equal by name). | Use `deps.WALL_CLOCK` as written; if AEA-23 merged a different key name, use it and report. |
| R-9 | AEA-01's `test_every_register_stub_present`: on `main` it calls every hunk with a bare `FastAPI()`; AEA-10's branch skips filled hunks. | The web-shell guard keeps it green under both versions without touching AEA-01's file. |
| R-10 | Shared context lines: AEA-19 edits the same A10a area-map row; many tickets add ICM rows and extend DO-3's *Built* line. | Expect textual merge conflicts on those lines; the merge agent keeps every ticket's annotation. |
| R-11 | Growth: about 5,760 `check_*` rows a day; nothing prunes `health_events` (DO-6 keeps them). | Out of scope; a pruning job needs its own ticket. |
| R-12 | **AEA-57's harness may run the real starters**, so a real watchdog would run in the pytest process with `os._exit(1)`. A journey that stalls the event loop or the pool for more than ~30 s plus three probes would end the test process. | **Note to AEA-57:** keep journeys well under that, or patch `Container.on_start` for ops in the harness (AEA-23's `full_app` already patches it). |
| R-13 | AEA-23 drift: this plan copies its **plan** (AEA-10's names were verified against its built branch). | Merged code wins for names; if a shape differs (e.g. `WebShellState` fields, `HEALTHZ_PATH`, `deps.HEARTBEAT`), use the merged one and report it. If `OpsRepos`'s constructor differs from `(conn)`, stop and report. |
| R-14 | The fixtures import AEA-10's test builders from `tests/unit/adapters/sqlite/helpers.py` (another ticket's test module). | Read-only import, frozen after AEA-10's wave. If a builder's signature differs on your base, build the row with `ConversationRow.model_validate({...})` / `CaseRow.model_validate({...})` in `ops_support.py` instead, and report it. |

**What you must not do:** edit any file outside §2.1; touch `schema/*.sql`, `db.py`, `rows.py`, `repos_core*.py`,
`repos_cases*.py`, `migrate.py`, `ports/*`, `domain/*`, `config.py`, `policy/limits.py`, `web/app.py`, `web/deps.py`,
`web/middleware.py`, any other `register_*` hunk or `container.py`'s module-level imports, `test_container.py`,
`test_repo_shells.py`, `tests/conftest.py`, `tests/fixtures/`, `tests/unit/adapters/sqlite/`, `tests/journeys/support/`,
`tests/fakes/`, `eval/**`, `pyproject.toml`, `uv.lock`; add a method, property or valued attribute to the `OpsRepos` class
itself; add an overdue alert type or read `cases` in the evaluator; write 12.5, 0.02, 4 h or the quiet hours anywhere but
`AlertSettings`, or the $30 cap anywhere in these files; call `datetime.now` in `health.py` except the `_utc_now` default of
`load_eval_reports`; call `sys.exit` from the watchdog; store or log message text, names, phones, emails, codes, card-like
numbers, keys or exception messages; put a literal phone number or secret in a test; read or print `.env`; call a paid
model; bind a port (no uvicorn; TestClient only; never 4019 or 5184); run pytest with more than `-n 2`; `git add -A`; push;
force-push.

---

## 9. Readiness

**BLOCKED-ON AEA-10 and AEA-23** (both wave 1, both real imports; nothing needs a product decision):

- **AEA-10** — built on branch `aea-10-aea-10-storage` at `135ad75`, awaiting merge. Needed: `db.py` (`format_wall`,
  `parse_wall`, `last_row_id`, `integrity_errors`, `StorageError`, `SqliteUnitOfWorkFactory`), `95_ops.sql` and `00_core.sql`,
  `conversations.last_started_wall()`, `job_runs.latest()`, `records.latest_reset_event()`, `temp_sqlite()`, the test builders.
- **AEA-23** — not started (frozen tests first, `risk::security`). Needed: `web/deps.py` (`HEARTBEAT`, `UOW_FACTORY`,
  `WALL_CLOCK`, `HeartbeatReader`), `web/middleware.py` (`WebShellState`, `PublicPaths`, `HEALTHZ_PATH`), `web/app.py`
  (`create_app`, `ContainerOverrides`, async `/healthz`) for the hunk (PA-7) and the capture tests (AC-12, AC-14).
- **Already on `main`:** AEA-01 (`Container`, `Key`, `Limits`, the `register_ops` stub) and AEA-02 (domain, ports, `Settings`,
  the `OpsRepos(conn)` shell).
- **Merge order:** AEA-26 (the `ledger` key) merges before AEA-32 (§8 R-3). Not an import; tests use a double.

Once both blockers are on `main`, the plan is **READY** as written. No `NEEDS-DECISION`: nothing changes the signed OpenAPI or
`UI_CONTRACTS.md`, and nothing contradicts D-4…D-15. The cross-ticket requests (R-1, R-2, R-4) go to the orchestrator for
AEA-40 and AEA-10; none blocks this ticket's build.

## Gates

None (no human, external, paid or live gate). Merge gate: lint and format, type check, affected tests, affected journeys
(`j10/test_aea_32.py` and whatever `tests.journeys.affected` selects). The deployed restart (CAP-9) is AEA-50's.
