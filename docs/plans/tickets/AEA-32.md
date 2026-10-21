## [AEA-32] ops: health events, heartbeat, watchdog, alerts

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

> **US-27:** As a **reviewer** (and the business owner), I need a monitoring page (volume, containment, escalations,
> failures, latency, spend against the daily cap, alerts as decision lines, and when the health check last restarted the
> service) and the evaluation report (…), with no codes or card numbers in what's shown, so that I can check the claims
> myself.

"Would the business know if it broke?" — the records that answer it. Shapes are `docs/design/contracts/stage7/cases.md`
§8 (CAS-22, CAS-25, CAS-26, CAS-27, CAS-30); the tables are created by AEA-10's `95_ops.sql` (slice plan §0 deviation 1,
merge MC-10), columns per stage7/cases §1.1.

- **`adapters/sqlite/repos_ops.py`** (the body of AEA-02's shell, constructor `__init__(self, conn)`, CAS-35):
  `ops.health.append(event) -> int`, `ops.health.latest_alert_states() -> dict[AlertType, AlertState]`,
  `ops.health.last_restart()`, `ops.health.restarts_by_day(tz) -> list[tuple[date, int]]`, `ops.deploy.insert(record)`,
  `ops.deploy.latest()`, `ops.eval.upsert_report(run, results, summary_json) -> bool` (by `run_id`),
  `ops.eval.latest_completed(suite, split)`, `ops.eval.case_results(run_id)`, over `health_events`, `deploy_records`,
  `eval_runs`, `eval_case_results` (no experiments table: an experiment is `eval_runs.experiment_id`, CAS-27). The row
  models `HealthEvent` (`at_wall`, `kind` ∈ `check_ok`, `check_failed`, `restart`, `alert_fired`, `alert_cleared`,
  `alert_type`, `reason_code`, `value`, `threshold`, `agent_version`), `DeployRecord` (DO-6 *Records* fields),
  `EvalRunRow` / `EvalCaseResultRow` (data.md §6 field names; `src/` never imports `eval/`) and `AlertState` are this
  ticket's. A demo reset clears none of these tables (stage7/cases §1.3 *Kept*).
- **`services/health.py` — `AlertSettings`** (frozen dataclass, the **one** place alert lines live): `latency_p95_s =
  12.5` [T] M-23, `failure_rate = 0.02` [T] M-24, `zero_traffic_after = 4 h` (Innocent 2026-10-21) M-22, quiet hours
  22:00–06:00 America/Chicago [A, configurable], `turn_window = 60 min`, `min_turns = 20`, `evaluate_every_s = 60` [A]
  CAS-25, `scheduler_stale_after_s = 180` [A] CAS-22, `heartbeat_every_s = 5`, `heartbeat_stale_after_s = 30` [A]
  CAS-26, `probe_every_s = 15`, `probe_timeout_s = 5`, `failures_to_exit = 3` [A, system design §8.2]. The spend cap is
  **not** here: it is `limits.spend.daily_cap_usd` ($30/day, AEA-01 `policy/limits.py`; merge MC-22), passed in by the
  container.
- **`services/health.py` — `Heartbeat`, `Watchdog`, `AlertWriter`, `AlertEvaluator`, `load_eval_reports`**
  (stage7/cases §8):
  - `Heartbeat.beat(mono)` / `fresh(mono)`: advanced every 5 s by a task that runs a no-op through the worker pool
    (`anyio.to_thread.run_sync`), so a fresh beat proves the event loop **and** the pool work; fresh while the last
    beat is ≤ 30 s old; never touches SQLite. AEA-23's async `/healthz` reads it (DO-3 §2.3 rule 3).
  - `Watchdog(uow, probe, exit, evaluator, settings, wall_clock)`, a thread started by `register_ops()`: `run_once()`
    probes `/healthz` (injected `probe`, 5 s timeout) every 15 s and writes one `check_ok` / `check_failed`
    `health_event`; after three failures in a row it writes a `restart` `health_event` (`at_wall`, `reason_code`) and
    calls `exit(1)` so Railway's restart policy starts the service again (Q-045 = A); a success resets the count; every
    `evaluate_every_s` it calls `evaluator.evaluate()`.
  - `AlertWriter(uow, wall_clock, agent_version).fire(alert_type, reason_code)`: thread-safe, its own short write unit
    of work, callable from a non-request thread at start-up; writes `alert_fired` only when that type is not already
    firing. The container (AEA-51) binds the trace sink's `on_alert` to `fire("trace_export_failed", reason)` (models.md
    cross-topic 6).
  - `AlertEvaluator(uow, ledger, settings, wall_clock, daily_cap_usd)`: `evaluate() -> tuple[AlertState, ...]` from
    stored rows only, writing `alert_fired` / `alert_cleared` **only on a change**, for `AlertType` =
    `spend_cap_reached` (`ledger.spend_today() >= daily_cap_usd`), `p95_latency_over_12_5s`,
    `failure_rate_over_2pct` (both over live turns received in the last 60 min, quiet below 20 turns),
    `zero_traffic` (time since the last live conversation started, **not counting** any part inside 22:00–06:00 Chicago,
    exceeds 4 h: last start 21:00, now 07:00 → 2 h counted → quiet), `health_check_restart` (from the stored `restart`
    event; firing while the latest restart falls on the current America/Chicago day, cleared at the first evaluation on
    a later Chicago day; cases.md §8, R-G-23), `trace_export_failed` (fires when the latest live turn's `turn.trace_export` is `failed` or `off`, clears
    when it is `sent`; DO-6 "Export failed on any turn, or off"; MC-24) and `scheduler_stale` (stored only, shown as the
    CON-19 health tile: `cases.job_runs.latest().started_wall_at` older than 180 s; CAS-22, CAS-30). **No overdue
    alert:** overdue is the supervisor view's (CON-17, via the scheduler's `case_events`; DO-6 "Supervisor view alert
    (C3)"; CAS-30). Live means `run_tag = 'live'`: `eval`, `load` and `seed` traffic never counts.
  - `load_eval_reports(reports_dir, uow) -> int` (CAS-27, DAT-14): at start-up, parses every `eval/reports/*.json`
    (data.md §6 `EvalReportFile`: run, results, summary) and upserts by `run_id`; returns how many were new; idempotent;
    a file that fails to parse is skipped with one `health_event` (`reason_code` "eval_report_invalid") and never
    half-loaded; `summary_json` stored as given (AEA-53 reads it and never recomputes). AEA-50's start-up calls it after
    the deploy record.

Alert timers run on the wall clock, UTC (`get_wall_clock()`, web.md §4; merge MC-20); case due times stay on the demo
clock (api-con-mapping §4). Produces: `repos_ops` for AEA-24 (report files it writes are loaded here), AEA-50 (deploy
record, start-up loader, CAP-9), AEA-53 (CON-19 alert states and restarts, CON-20 latest eval, the `scheduler_last_run`
tile; it only reads these rows); `Heartbeat` for AEA-23's `/healthz`; `AlertWriter` for AEA-51's trace-sink wiring;
`AlertSettings` for AEA-53's `alert_config`.

**Example pair (WF-17):** input — `/healthz` answers OK, then the heartbeat stops advancing for three probes → output:
one `health_event` per probe (`check_ok`, `check_failed`, `check_failed`, `check_failed`), then a `restart`
`health_event` with `at_wall` and a `reason_code`, then `exit(1)` (in tests, the injected exit callable is called once
with 1). On the next start, `evaluate()` writes `alert_fired` for `health_check_restart`, and
`ops.health.restarts_by_day("America/Chicago")` returns one restart for the day (M-28).

### Source

- `docs/design/contracts/stage7/cases.md` §1.0 (`SqliteUnitOfWork`, the repository constructor), §1.1 (`95_ops.sql`
  tables; wall-time storage; `turns` row with `trace_export`), §1.2 (`cases.job_runs.latest()`), §1.3 (*Kept*), §8 (this
  ticket), §9 (AEA-53 reads `latest_alert_states`, `AlertSettings`); `stage7/models.md` §6 (`LedgerService.spend_today()`,
  `SpendLimits.daily_cap_usd`), §4 / cross-topic 6 (`on_alert`); `stage7/data.md` §6 (eval report file and row fields),
  §7 (deploy, start-up); `stage7/web.md` §4 (`get_wall_clock()`), §7 (`/healthz` never waits); DO-4 §13, §16.
- Decision ledger `docs/plans/7b-decisions/cases.md`: CAS-22, CAS-25, CAS-26, CAS-27, CAS-30; `data.md` DAT-14; merge
  `merge-clashes.md` MC-10, MC-20, MC-22, MC-24; residuals R-G-23 (`residuals-graph.md`) and R-W-19
  (`residuals-web.md`): when `health_check_restart` clears.
- DO-3 §3 (`repos_ops.py`, `services/health.py`), §4.4, §2.3 rules 3 and 6, §8 (A10a); system design §8.2 (*Process
  hang* row: watchdog 15 s [A], three failures → exit), §A.8.
- DO-6 *Covered workflows* WF-13, WF-17; *Records* (`health_event`, `deploy_record`, `eval_run`, `eval_case_result`);
  *Storage and access*; *Content and redaction* (logs: IDs only); *Missing instrumentation* (alert table; "The overdue
  job stopped ticking"; "Traces are not exported"); CAP-9.
- DO-7 M-22 (zero-traffic line, decided 2026-10-21), M-23 (12.5 s), M-24 (2%), M-26 ($30, Chicago day), M-27, M-28,
  M-29; PRD R-35 (alerts stay on the page; health check restarts the service; no push channel); OpenAPI
  `MonitorAlert.type` (six values) and `getMonitoring`, `getLatestEval` (wire shapes win; read by AEA-53).
- **Brief check:** serves "Add observability so the business can see how the agent is performing after launch: volume,
  containment, escalations, failures, latency." and "Would the business know if it broke?"; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `repos_ops` round-trips every row over the tables AEA-10's `95_ops.sql` creates (`health_events`, `deploy_records`, `eval_runs`, `eval_case_results`): append/insert then read returns the same values, wall times as UTC ISO `+00:00` through `db.format_wall`; `ops.eval.upsert_report` replaces a run by `run_id` and returns False for an unchanged one — verify: `tests/adapters/test_repos_ops.py::test_round_trips` and `::test_upsert_report_by_run_id` (`temp_sqlite()` from `tests/fixtures/sqlite.py`) — evidence: equal rows; one `eval_runs` row after two upserts of the same run.
- [ ] AC-2 [invariant] `Heartbeat` is in memory and readable without the thread pool or SQLite; fresh while the last beat is ≤ 30 s old, stale after; the beat task advances it only when a no-op has run through the worker pool — verify: `tests/unit/services/test_health.py::test_heartbeat_fresh_and_stale` and `::test_beat_goes_through_pool` (fixed monotonic clock; a saturated pool double) — evidence: fresh → True; past 30 s → False; a blocked pool stops the beats; no `sqlite3` import on `Heartbeat`'s path.
- [ ] AC-3 [failure/refusal] `Watchdog.run_once` writes one `check_ok` / `check_failed` `health_event` per probe; after three consecutive failures it writes one `restart` `health_event` and calls the injected exit once with 1; a success between failures resets the count — verify: `tests/unit/services/test_health.py::test_watchdog_exits_after_three_failures` and `::test_success_resets_count` (probe and exit doubles) — evidence: exit called once after the third failure; never after fail, fail, ok, fail.
- [ ] AC-4 [invariant] Each alert fires and clears from stored rows only, writing an event only on a change: `zero_traffic` after 4 h without a new live conversation counted outside 22:00–06:00 Chicago (last start 21:00, now 07:00 → quiet); `p95_latency_over_12_5s` and `failure_rate_over_2pct` over live turns in the last 60 min, quiet below 20 turns; `spend_cap_reached` at `ledger.spend_today() >= daily_cap_usd`; `health_check_restart` from a stored `restart` event; `trace_export_failed` when the latest live turn's `trace_export` is `failed` or `off`, cleared when `sent`; `scheduler_stale` when `job_runs.latest().started_wall_at` is older than 180 s, cleared by a fresh tick; `health_check_restart` firing while `ops.health.last_restart().at_wall` falls on the current America/Chicago day and cleared (one `alert_cleared`) at the first evaluation on a later Chicago day, a second restart the same day writing no second `alert_fired` (cases.md §8, R-G-23, R-W-19) — verify: `tests/services/test_alerts.py::test_each_alert_fires_and_clears` (one parametrised case per `AlertType`, temp SQLite rows, ledger double honouring models.md §6, fixed UTC wall clock), `::test_no_duplicate_events_without_change` and `tests/unit/services/test_health.py::test_restart_alert_clears_next_chicago_day` (fake wall clock) — evidence: one `alert_fired` when the condition starts, one `alert_cleared` when it stops, nothing on an unchanged second `evaluate()`; the late-night case writes none; the alert written at a 14:00 Chicago restart is still firing at 23:59 and the evaluation at 00:05 the next Chicago day writes one `alert_cleared`.
- [ ] AC-5 [negative] Overdue is not a health alert (CAS-30): no `AlertType` value or `health_event` names an overdue case, however many cases are overdue — verify: `tests/services/test_alerts.py::test_overdue_is_not_a_health_alert` — evidence: with three overdue cases in the store, `evaluate()` writes no event and `AlertType` holds exactly the six OpenAPI `MonitorAlert` values plus `scheduler_stale`.
- [ ] AC-6 [negative] `eval`-, `load`- and `seed`-tagged conversations and turns never count toward the zero-traffic, latency or failure-rate alerts (DO-6 *Correlation*: test traffic must not hide or fake live numbers) — verify: `tests/services/test_alerts.py::test_test_traffic_excluded` — evidence: a window holding only eval turns still fires `zero_traffic`; 25 slow `load` turns do not fire latency.
- [ ] AC-7 [invariant] `AlertWriter.fire` is thread-safe and idempotent while firing: two threads firing `trace_export_failed` at once leave one `alert_fired` row; a call after `alert_cleared` writes a new one — verify: `tests/services/test_alerts.py::test_alert_writer_once_while_firing` (two threads, temp SQLite) — evidence: row counts 1, then 2 after a clear.
- [ ] AC-8 [invariant] The thresholds have one home: 12.5, 0.02, 4 h and the quiet hours appear as literals only in `AlertSettings`, and the $30 cap only in AEA-01's `policy/limits.py` (passed to `AlertEvaluator` as `daily_cap_usd`) — verify: `rg -n '12\.5|0\.02|daily_cap_usd\s*=' src/meridian/services/health.py src/meridian/adapters/sqlite/repos_ops.py` and `tests/services/test_alerts.py::test_evaluator_uses_injected_cap` (cap $5 injected) — evidence: matches only inside `AlertSettings` (none for the cap); the injected cap fires at $5.
- [ ] AC-9 [invariant] `load_eval_reports` loads every valid `eval/reports/*.json` once, keyed by `run_id`, returns the number new, stores `summary_json` byte for byte, and skips an invalid file with one `health_event` (`reason_code` "eval_report_invalid") and no partial rows — verify: `tests/services/test_load_eval_reports.py::test_loads_idempotently` and `::test_invalid_file_skipped` (a temp reports dir with two valid files and one truncated) — evidence: first call returns 2, second 0; stored summary equals the file's; zero rows for the invalid file's `run_id`; one event.
- [ ] AC-10 [negative] `health_events`, `deploy_records` and alert rows hold IDs, kinds, statuses, timings, values and counts only — no message text, customer name, phone, email, code or key value; `src/meridian/` imports nothing from `eval/` — verify: `tests/services/test_alerts.py::test_ops_records_hold_no_pii` (seeded MHC-10002 conversation with phone 512-555-0102 in its messages; a session secret test value in settings) and `rg -n '^from eval|^import eval' src/meridian` — evidence: "Omar", "512-555-0102" and the secret's test value absent from every ops row; no import match.
- [ ] AC-11 [invariant] `ops.health.restarts_by_day("America/Chicago")` and `last_restart()` give M-28's count per Chicago day with time and reason, and `ops.deploy.latest()` the newest deploy record — verify: `tests/adapters/test_repos_ops.py::test_restart_and_deploy_reads` (restarts at 23:30 and 00:30 Chicago) — evidence: two different days; latest deploy row returned.
- [ ] AC-12 [capture] WF-17 records at its real trigger: driving `Watchdog` against `create_app`'s async `/healthz` bound to the real `Heartbeat`, with the beat stopped, writes the per-check `health_event`s and the `restart` event and calls exit — verify: `tests/services/test_health_capture.py::test_watchdog_against_app_healthz` (FastAPI TestClient over AEA-23's app, which merges in wave 1) — evidence: rows present in order; exit called with 1. (CAP-9's forced health-check failure on the deployed image is AEA-50's.)
- [ ] AC-13 [journey] Extends J-10 (slice plan §0a journey map; J-10 is a proposed addition to the map, from the join audits; backend-amendments §3): after the journey's turns, the monitoring read's alert states equal the stored `health_event` rows and the `scheduler_last_run` tile reflects the newest `job_runs` row; asserting what the user sees and what is stored, in `tests/journeys/j10/test_aea_32.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j10/test_aea_32.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-53 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-32.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-53 (`integrated-journeys.md` §4).
- [ ] AC-14 [capture] **WF-17 (alerts raised by the running watchdog; OBS-31, OBS-40):** driving `Watchdog.run_once` against `create_app`'s `/healthz` as in AC-12, with `evaluate_every_s` elapsed on a fake wall clock: (a) with the last live conversation started 5 h earlier at 14:00 Chicago, the watchdog's evaluation writes one `alert_fired` `zero_traffic`; with it started at 21:00 and now 07:00 Chicago it writes none (quiet hours read from `AlertSettings`); (b) after the beat stops and the `restart` event is written, a second `Watchdog` on the same store (the restarted process) evaluates and writes one `alert_fired` `health_check_restart`; in each firing case `ops.health.latest_alert_states()`, the read CON-19 shows (AEA-53), reports that alert `firing` — verify: `tests/services/test_health_capture.py::test_watchdog_raises_zero_traffic_and_restart_alerts` — evidence: the alert rows and the `latest_alert_states()` entries printed.
- [ ] AC-15 [regression/context] Same change updates: the area-map row for `services/health.py` and `repos_ops.py` (planned → built, commit; `95_ops.sql` stays AEA-10's row); the `.claude/state/icm-progress.md` row whose evidence these modules change; DO-3 code-design status for both modules (planned → built) and its `services/health.py` row naming `AlertSettings`, `AlertWriter`, `AlertEvaluator` and `load_eval_reports` beside `Heartbeat` and `Watchdog` — verify: `git diff --name-only` — evidence: those files in the diff, only this ticket's rows.

Resolved R-G-23 (cases.md §8; same ruling as R-W-19): `health_check_restart` fires while the latest stored restart's
`at_wall` is on the current America/Chicago day and clears at the first evaluation on a later Chicago day, so the alert
and M-28's per-day tile agree. AC-4 tests both halves.

### Observability

- Responsibilities: WF-17 — one `health_event` per check (`check_ok` / `check_failed`) and per restart (`at_wall`,
  `reason_code`), and `alert_fired` / `alert_cleared` events on change, each with `agent_version`; the missed-tick record
  for WF-7 is the `scheduler_stale` event (CAS-22). Storage and reads for WF-13's `deploy_record` (the start-up write is
  AEA-50's) and for eval-run rows loaded from report files (written by AEA-24's harness). Silence must never look like
  "no traffic" (DO-6): no recent `health_event` means "not running". IDs and numbers only (AC-10).
- Capture evidence: AC-12 drives the watchdog against the real `/healthz`; AC-14 the alerts it raises there (zero
  traffic, restart); CAP-9 at deploy is AEA-50's.

### Evaluation

- Checks: no scoring — health records answer "did it run?", never "was it right?" (DO-6 *Two questions, kept apart*).
  Kept passing: CON-20 shows the harness's own numbers, because `load_eval_reports` stores each report's summary byte for
  byte and never recomputes it (AC-9); the "last health-check restart" line on SCR-10 (DO-6 WF-17) reads
  `last_restart()` (AC-11).
- Expected-answer authority: the eval report files AEA-24 writes (`eval/reports/<run_id>.json`, data.md §6) for every
  stored eval row; the DO-6 alert table and DO-7 decision lines for when an alert must fire.

### Metrics

- References: M-28 health-check restarts; the alert lines of M-22 (zero traffic), M-23 (latency), M-24 (failure rate),
  M-26 (spend cap), M-29 (trace export); M-27 (the `scheduler_stale` check tells the reader whether the overdue counts
  are current).
- Acceptance conditions: each stays computable from stored rows (`health_events`, `turns`, `conversations`,
  `spend_ledger`, `job_runs`); the alert lines are the approved ones (12.5 s, 2%, $30, 4 h outside 22:00–06:00) and live
  in one place each (AC-8); M-28 per Chicago day from `restarts_by_day` (AC-11).

### Blocked by

AEA-10 (the `repos_ops` shell inside `SqliteUnitOfWork`, `95_ops.sql`, `migrate.py`, `repos_core` turns and
conversations, `repos_cases` `job_runs.latest()`). Also imports, from waves 0–1 that land before wave 2:
`policy/limits.py` (AEA-01), and AC-12 drives AEA-23's app (wave 1) — no wave moves. The `[journey]` AC-13's
integrated level only (not this ticket's merge): AEA-57 (harness) and AEA-53 (lands J-10, wave 3).

### Agent handoff

- Area / owner: A10a Ops; owns `src/meridian/adapters/sqlite/repos_ops.py` (body), `src/meridian/services/health.py`,
  their tests, and its own `register_ops()` hunk in `web/container.py` (builds `Heartbeat`, `AlertWriter`,
  `AlertEvaluator`, `Watchdog` with `get_wall_clock()` and `limits.spend.daily_cap_usd`; starts the beat task and the
  watchdog thread — if AEA-23's lifespan offers no start hook for a registered area, the plan records `blocked-on
  AEA-23`).
- Contracts and shared surfaces: consumes `UnitOfWorkFactory` and stage7/cases §1.0–§1.2 (AEA-10), `LedgerService`
  (AEA-26, same wave: injected double honouring models.md §6), `SpendLimits` / `limits.spend.daily_cap_usd` (AEA-01),
  data.md §6 report shape (AEA-24). Produces `repos_ops` for AEA-24 (via report files), AEA-50, AEA-53; `Heartbeat` for
  AEA-23; `AlertWriter` for AEA-51; `AlertSettings` for AEA-53. Must not edit `web/app.py` (`/healthz` is AEA-23's), any
  `.sql`, `db.py`, `repos_core.py`, `repos_cases.py`, `services/ledger.py`, `eval/**`.
- Scope boundary / refusal: no push channel (R-35, Q-045 = A); no route; no overdue alert (CAS-30); computes no outcome
  metric (never on read, DO-6 WF-6); traces are AEA-19's.
- Evidence level (`.claude/rules/integrated-journeys.md` §4): the unit tests are `mock-tested`; AC-12 drives the real app's
  `/healthz` in process (no model involved); the deployed restart is AEA-50's CAP-9, so record `Blocked by: AEA-50` for
  the deployed level. The J-10 journey step (AC-13) records `mock-tested` and `Blocked by: AEA-57, AEA-53` until both
  merge.
- Wave and gates: wave 2; no human or external gate.
- Lane: build-loop — changes source and tests (ticket-lanes).
- Risk: None (slice plan row; the rows hold IDs and numbers only, AC-10).
- Awaiting Innocent: DAT-4 — built on the recommended option A (the ingestion-only Langfuse route opens, so deployed turns
  record `sent` and `trace_export_failed` stays quiet); under B no route opens, every deployed turn records `off`, and
  the `trace_export_failed` alert fires for as long as the app runs (MC-24) — no code here changes either way.
- Entry points added or changed: WF-17 (the health check probe and watchdog restart).
