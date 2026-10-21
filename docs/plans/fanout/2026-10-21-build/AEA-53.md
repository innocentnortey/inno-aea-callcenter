# Plan — [AEA-53] reads: metrics reader

**Status:** planned (READY). Nothing blocks it: AEA-29 and AEA-30 are merged, and the R-1 grant is recorded
(*Deviations*, DV-1). Gates: none.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/53 (spec copy:
`docs/plans/tickets/AEA-53.md`) · **Base revision:** `main` at `3725c90` (2026-10-21; refreshed from the `895f271` plan)
· **Lane:** `lane::build-loop`, risk none (not `risk::security`: plan → implement with tests → review; no frozen tests,
no security agent).
**Planner:** Opus (`claude-opus-5-5`). **Implementer:** Sonnet. Every decision is made below. If a precondition in
Step 0 fails, stop and report. Do not improvise.

**What changed in this refresh (checked against `main` at `3725c90`):**
1. **The R-1 grant is given.** The orchestrator recorded on 2026-10-21 that Innocent chose option A ("just do whatever
   you recommend"). It is DV-1 below, and Step 0 no longer asks for it.
2. **AEA-29 is merged** (`ef561fc`). `services/_case_rules.py` (`REASON_LABEL`, `LIFECYCLE_WORD`, `reason_label`) and
   `services/handoff.py` (`BriefAssembler`) are on main with the names this plan copied. R-2 is closed.
   `handoff.py`, `_case_views.py` and `_case_actions.py` already import `_case_rules`, so the reader's import has
   precedent.
3. **AEA-30 is merged** (`cf8fd78`). `register_demo` now provides `Key("demo_clock")`: a `DemoClock` that reads the
   stored `demo_state` row. That has four consequences:
   - `container_app` (tests) no longer swaps in a `FixedClock` stand-in. The capture and integration tests run on the
     real `DemoClock`, which reads `DEMO_START` until someone advances it.
   - The J-10 page-read step is no longer blocked. The harness has every need, so the step runs at level
     `integrated with a scripted model`.
   - The journey server now runs AEA-30's `SchedulerThread`. Every 60 s a tick writes a `job_runs` row, marks
     past-due promises `missed` and abandons idle live conversations. New decision **D-11** keeps the journey's
     page-vs-SQL comparison stable across a tick (Step 7).
   - AEA-59's contract runner will run the three reads' 200 cases on the real reader in this ticket (R-8).
4. **AEA-24 is merged** (`7fddbf5`). `eval/harness/report.py` on main matches §4.2 unchanged: the `base_summary` keys,
   `headline` (the held-out `M-1` dict), and the ids `M-1:<topic>` and `E-1:hard`.
5. **AEA-40 is merged** (`f466ff7`), but AEA-51 (`register_graph`, `run_graph`) is not. The J-10 chat leg is now
   blocked on **AEA-51 only**. Before, it was blocked on AEA-40, 51, 29, 27 and 30.
6. **AEA-50 added `tests/capture/conftest.py`** (deploy-marker hooks). This ticket neither edits nor replaces it. The
   new capture test is collected under it unchanged.
7. **Line numbers moved.** `register_metrics_reader` is now lines 993–997 of `web/container.py`, and the area-map A10b
   row is line 46. The ICM A10b row is still line 38. `repos_ops.py` has not changed since `895f271` (`OpsRepos` is
   at lines 433–446).
8. **Re-checked from the `895f271` refresh, all still true:**
   - D-7 reads the stored `headline`, and D-10 projects each split onto `EvalRun`'s seven keys.
   - AEA-30's missed-promise reason is `"past_due"`.
   - AC-6 does not test for the word "langfuse".
   - AC-14 patches `tests.api.staff_session_support.make_settings`. `container_app` still resolves `make_settings`
     in that module.
   - `repos_metrics.py` parses times with `db.parse_wall`.
   - `test_repo_shells.py` accepts a new `OpsRepos` attribute: it checks only the constructor signature.

## Deviations (recorded grants and departures from the issue text)

| # | Deviation | Basis | Where |
|---|---|---|---|
| DV-1 | This ticket creates `src/meridian/adapters/sqlite/repos_metrics.py`. The grant writes the path as `src/adapters/sqlite/repos_metrics.py`, but the package root is `src/meridian/`. It also adds exactly one import and the 3-line `OpsRepos.metrics` hook to `src/meridian/adapters/sqlite/repos_ops.py` (AEA-32's merged file). It touches nothing else outside the issue's owned files | Orchestrator note, 2026-10-21: Innocent decided R-1 option A ("just do whatever you recommend"). The orchestrator checked that no in-flight branch touches `repos_ops.py`, and `git diff 895f271..main` shows the file unchanged | Step 1; section 2 |
| DV-2 | AC-15's DO-7 edit is not made | DO-7 line 78 already says the M-26 day runs "midnight to midnight Austin time (America/Chicago)" | Step 8 |
| DV-3 | AC-9's "drives WP-2, WP-5 and WP-7 through the real server" is met only for the read leg. The pairs' rows are written through the real writers' repositories into the running server's DB copy, and the chat-driven leg is a declared skip | AEA-51 (the graph and `run_graph`) is not merged. Integrated-journeys §3 rule 6: a blocked step is recorded, never silently dropped | Step 7; R-3 |
| DV-4 | AC-5's CON-20 `Measure.id` clause ("a DO-5 `E-n`") is tested as pass-through of the stored ids | STF-18's own consequence for AEA-53 (the route passes ids through unchanged). DO-5's E-n names eval runs, not measures. See R-4 | Step 2 D-10; §7.2 |

---

## 1. Goal and sources

### Goal (from the issue, *What to build*)

Build `services/metrics_reader.py` (DO-3 §4.4: "Serve stored measures without recomputing outcomes"), exactly as
`stage7/cases.md` §9 signs it:
`MetricsReader(uow, demo_clock, wall_clock, ledger, settings: AlertSettings, current_agent_version: str, daily_cap_usd: float)`
with `owner_metrics()`, `monitoring()` and `latest_eval()`. Each returns `Mapping[str, object]` with the OpenAPI field
names. The class satisfies web.md §4's `MetricsReads` Protocol structurally (services never import `web/`). This
issue's `register_metrics_reader()` hunk binds it to `get_metrics_reads()` (MC-6), so AEA-48's `routes/reads.py`
serves CON-18 `GET /api/staff/owner-metrics`, CON-19 `GET /api/monitoring` and CON-20 `GET /api/eval/latest` from
stored rows.

**What "never recomputed" means here.** Say the store holds 12 live `turns` rows, 3 of them with
`outcome = degraded_handoff` and `degrade_reason = model_error`. The reader counts those stored fields, and CON-19 shows
"Failures" with value 3, numerator 3 and denominator 12. It never re-runs a gate, a check or a model. It never
re-judges an outcome, never applies an alert line and never applies the 30-minute end rule. For CON-20 it copies the
fields the harness stored. It never re-scores a run.

### Context

AEA-48 (wave 2, merged `cb7df88`) built the three routes and their schemas (`web/schemas/reads.py`), typed against the
`MetricsReads` Protocol in `web/deps.py`. Today an allowed read answers 500 `not bound: get_metrics_reads`. This ticket
supplies the reader behind those routes. The rows it reads come from these writers:
- AEA-10: conversations, turns, job_runs;
- AEA-26: spend;
- AEA-29: cases and promises;
- AEA-30: `abandoned` (sweep) and `missed` (tick);
- AEA-32: health events and the eval tables;
- AEA-44: flags;
- AEA-24: the eval report files.

All of them are merged on `main` at `3725c90`.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-53.md` (= issue #53) | AC-1…AC-15, the seams table, the owned files |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-53 (wave 3; blockers 26, 29, 32, 48, 44); §0a Amendment 1 (J-10 landed here); §3 collision map (`web/container.py` own hunk only; `tests/capture/` CAP-6 is ours) | Owned files, blockers, journey |
| Requirements | PRD R-32, R-35, R-38, R-39; US-24, US-27 | Owner view read-only; monitoring reads stored data, health apart from correctness, no push alerts; eval report with denominators |
| Component contracts | `docs/design/contracts/stage7/cases.md` §9 (MetricsReader, the decision of record), §8 (`AlertSettings`, `AlertType`, `ops.health.latest_alert_states`, `ops.eval.latest_completed`, `load_eval_reports`), §1.2 (`cases.job_runs.latest`), §1.3 (reset clears conversations and turns); `stage7/web.md` §4 (`MetricsReads`, `get_metrics_reads`, `get_wall_clock`); `stage7/staff.md` §9 (route validation, `Measure.id`), §10 (time sources); `stage7/models.md` §6 (`LedgerService.spend_today`, `models_disabled`, `open_circuits`; `SpendLimits.daily_cap_usd`); `stage7/data.md` §6 (eval report and summary shapes). These addenda win over DO-4 | Signatures, clocks, which repository calls exist |
| Code design | `docs/design/code-design.md` (DO-3) §4.4 (`services/metrics_reader.py`, depends on UoW), §8 (A10b, wave 3) | Module boundary and dependency direction: `web/` → `services/` → ports and repositories |
| Evaluation plan | `docs/design/evaluation-plan.md` (DO-5) *What the R-39 report contains*; *Development and held-out separation*; E-1…E-8 are eval **runs** (line 170 onwards) | CON-20 shows stored summaries; the headline comes from held-out only |
| Observability contract | `docs/design/observability-contract.md` (DO-6) row **WF-6**; **CAP-6**; *Missing instrumentation*; *Alerts on the monitoring page* | Stored counts only; no names, codes, card-like numbers or trace links; an incomplete eval run is not a result |
| Key-metrics registry | `docs/design/key-metrics-registry.md` (DO-7) M-1…M-29; *Where this registry and other documents differ* 1–4; M-26 row (line 78) | Ids, numerators, denominators; 12.5 s; no 80% spend line; M-3 is an estimate. The M-26 day is already "America/Chicago" in DO-7, so AC-15's DO-7 edit is not needed |
| UI contracts (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `OwnerMetricsResponse`, `MonitoringResponse`, `EvalResponse`, `Measure`, `Tile`, `MonitorAlert`, `EvalMeasure`, `EvalRun` (examples: `trace_export: sent 70 of 74`; null reason `Not enough turns yet (fewer than 20)`) | Field names and shapes. Example ids are illustrative and wrong (STF-18) |
| Sibling code on `main` (read only) | AEA-24 `eval/harness/report.py` (`base_summary`, `build_scored_report`, `_case_measures`); AEA-30 `services/scheduler.py` (`PROMISE_MISSED_REASON = "past_due"`, `TICK_INTERVAL_S`, the abandon sweep), `services/demo.py` (`DemoClock`); AEA-29 `services/_case_rules.py` (`REASON_LABEL`, `reason_label`, `LIFECYCLE_WORD`); AEA-31 `services/reset.py` (`seed_demo`, `seed_first_boot`, `SEED_COUNT = 4`) | What the stored rows really look like |
| UX ↔ backend join | `docs/plans/ux-join/backend-amendments.md` AEA-53-1…4 | Unit vocabulary, unique (id, label), fixed tile list plus a note, J-10 share check |
| Rules | `.claude/rules/build-loop-test-scope.md` (with its AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`, `source-authority.md`; workspace `ticket-lanes.md`, `code-design-solid-modularity.md` | Affected tests and journeys only; journey record with level; context rows in the same change |
| Decisions | `docs/plans/7b-decisions/` CAS-22, 25, 27, 29, 30; STF-17, 18, 22; DAT-14; merge MC-5, 6, 20, 22, 24; `docs/plans/stage7-signoff.md` D-4…D-15 (none bears on this ticket) | As cited in the requirements table |

---

## 2. Boundary

### Owned files (the implementer may create or edit only these)

| File | Create / modify | Note |
|---|---|---|
| `src/meridian/services/metrics_reader.py` | create | The reader (Step 2) |
| `src/meridian/adapters/sqlite/repos_metrics.py` | create | **Granted (DV-1).** The read-only `MetricsRepo` (Step 1) |
| `src/meridian/adapters/sqlite/repos_ops.py` | modify: **3 lines only** in `OpsRepos` plus one import | **Granted (DV-1).** Wires `OpsRepos.metrics` |
| `src/meridian/web/container.py` | modify: the **body and docstring of `register_metrics_reader` only** (lines 993–997 today) | Collision map §3 |
| `tests/unit/services/test_metrics_reader_rows.py` | create | Shared builders, no `test_` functions (pytest collects 0 tests from it) |
| `tests/unit/services/test_metrics_reader_repo.py` | create | `MetricsRepo` tests |
| `tests/unit/services/test_metrics_reader.py` | create | AC-10, AC-11, AC-12, the worked pairs, the 3-of-12 example, the CON-20 projection |
| `tests/unit/services/test_metrics_reader_alerts.py` | create | AC-4 |
| `tests/unit/services/test_metrics_reader_stamps.py` | create | AC-8 |
| `tests/integration/test_reads_composition.py` | create | AC-1, AC-7 |
| `tests/capture/test_cap6_reads.py` | create | AC-2, AC-3, AC-5, AC-6, AC-13, AC-14 (CAP-6) |
| `tests/journeys/j10/test_aea_53.py` | create | AC-9 (J-10) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-53.md` | create (written by the harness, then one notes paragraph appended) | AC-9 evidence record |
| `docs/plans/ux-join/AEA-53-con19-health-tiles.md` | create | AC-12 note (the only file in that folder this ticket touches) |
| `.claude/reference/area-map.md` | modify: the **A10b row only** (line 46 today) | AC-15 |
| `.claude/state/icm-progress.md` | modify: the **A10b "Routes verified against code and tests" row only** (line 38 today, the one citing AEA-48) | AC-15 |

`tests/unit/services/__init__.py`, `tests/integration/__init__.py` and `tests/capture/__init__.py` already exist on
`main`. Do not create or edit them.

### Shared surfaces: read and import, never edit

- `src/meridian/web/routes/reads.py`, `web/schemas/reads.py` (AEA-48).
- `web/deps.py`, `web/app.py`, `web/middleware.py` (AEA-23).
- `services/health.py` and the rest of `repos_ops.py` (AEA-32).
- `services/ledger.py`, `repos_spend.py` (AEA-26).
- `adapters/sqlite/{db,rows,repos_core,repos_core_aux,repos_cases,repos_cases_state,migrate}.py` and every
  `schema/*.sql` (AEA-10).
- `services/_case_rules.py`, `services/cases.py`, `services/handoff.py` (AEA-29).
- `services/reset.py` (AEA-31); `services/staff.py`, `repos_staff.py` (AEA-44).
- `policy/*`, `ports/*`, `domain/*`.
- `tests/journeys/support/` (AEA-57).
- `tests/api/*_support.py`, `tests/fixtures/sqlite.py`, `tests/unit/adapters/sqlite/helpers.py`, `tests/fakes/`.
- `tests/contract/cases/reads.py` (AEA-48), `tests/contract/*` (AEA-59).
- The OpenAPI, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, the briefing, issued data, `docs/archive/`,
  `docs/parked/`.

### Other slices' files: never touch

- Every other `register_<area>()` hunk in `web/container.py`. They are merged (AEA-29, 30, 40, 43 and others) or
  belong to open tickets (`register_staff_cases` AEA-45, `register_graph` AEA-51).
- `tests/capture/conftest.py` (AEA-50, on main): do not edit or replace it. It appends no fixture this ticket uses.
- Every other journey file, including AEA-48's `tests/journeys/j10/test_aea_48.py` (its skipped
  `test_j10_read_pages_from_metrics_reader_on_db_copy` stays AEA-48's; the seam audit retires it) and
  `tests/journeys/j10/test_aea_32.py`.
- `key-metrics-registry.md`.
- AEA-24's `eval/**`.

---

## 3. Requirements table

### 3a. Acceptance criteria → how built → how verified

| AC | Requirement (issue, abridged; full text in the issue) | How it is built | How it is verified |
|---|---|---|---|
| AC-1 [invariant] | Real `MetricsReader` bound to `get_metrics_reads()` at `create_app()`. CON-18: owner and supervisor 200; representative or customer 403 `ROLE_NOT_ALLOWED`; no session 401 `UNAUTHENTICATED`. CON-19 and CON-20 answer any signed-in role. Every response passes `assert_response_matches` | The Step 5 hunk provides `METRICS_READS`. The role checks are AEA-48's routes plus AEA-44's `StaffSessionStore.actor_for` (not rebuilt here) | `tests/integration/test_reads_composition.py::test_reader_bound_and_access`. Prints the bound class name and a role → status table |
| AC-2 [capture] | CAP-6, WF-6, CON-18, over rows written through the real writers' repositories: every owner measure's numerator and denominator equal a direct SQL count, and `case_refs` list exactly the cases behind it. Ids are DO-7 `M-n`. The live estimate has `kind: estimate` and the north-star link. Seeds are counted and named (`seed_count` 4). A zero denominator gives `null_reason`, never 0% | Step 2 `owner_metrics` (§4.4 CON-18 table) | `tests/capture/test_cap6_reads.py::test_owner_metrics_equal_stored_counts`: per-measure equality with the SQL in §6.4 |
| AC-3 [capture] | CAP-6, CON-19. These all equal direct counts over the stored rows: volume (M-22), failures (M-24), latency p50 and p95 from `turns.server_ms` (null reason "Not enough turns yet (fewer than 20)" below 20 turns), spend today (M-26, Chicago day), the last restart (M-28), "n of N turns" (M-29) and the `scheduler_last_run` tile. `eval`, `load` and `seed` rows are excluded. Health and correctness are separate groups | Step 2 `monitoring` (§4.4 CON-19) | `tests/capture/test_cap6_reads.py::test_monitoring_equals_stored_counts` |
| AC-4 [invariant] | Alerts are shown, never applied. Each `MonitorAlert` state equals `latest_alert_states()`, so a stored `firing` row whose value is under its threshold still shows `firing`. `alert_config` comes from `AlertSettings`, and the spend line shows `daily_cap_usd` (no 80% line). `scheduler_stale` appears only as a tile. With `AlertEvaluator` patched to raise, all three pages still answer | Step 2: `alerts` are copied from `tx.ops.health.latest_alert_states()`. The reader never imports or calls `AlertEvaluator` | `tests/unit/services/test_metrics_reader_alerts.py` (3 tests, §7.2) |
| AC-5 [capture] | CON-20. Each split shows its latest **completed** run as stored. The headline comes from held-out only and is absent without a held-out run. A stale run carries the stale label. An `incomplete` run is never a result. No target appears as a result field | Step 2 `latest_eval`: D-7 (the stored `headline`) and D-10 (project onto `EvalRun`'s keys) | `tests/capture/test_cap6_reads.py::test_latest_eval_per_split`, 6 scenarios (§6.3). **The `E-n` id clause:** the test asserts ids equal the stored ids unchanged. The writer's naming is R-4 |
| AC-6 [negative] | Sentinel names, phones, code-like digits and card-like numbers are seeded in conversations, messages and eval failure examples. CON-19 and CON-20 contain none of them and no trace link or trace id. CON-18 carries case references and no PII | The reader reads no message, quote or trace-id column (`MetricsRepo` selects none), and D-10 drops every summary key outside `EvalRun` | `tests/capture/test_cap6_reads.py::test_no_pii_codes_cards_or_trace_links` |
| AC-7 [invariant] | Never recomputes: read-only units of work only. With the gates, `checks.py`, the policy modules and the model ports patched to raise, the pages still answer. M-18 reads `outcome` as stored. A conversation a staff flag marks wrong is dropped from M-3's numerator | Step 2: every `with self._uow() as tx` uses the default `write=False` | `tests/integration/test_reads_composition.py::test_reader_never_recomputes` |
| AC-8 [invariant] | Stamps. CON-19 `as_of` = wall clock and `demo_now` = demo clock. CON-18 `as_of` = demo clock. `cap_cents` is 3000 from 30. `today_cents` = `spend_today()` × 100. `resets_at` = the next Chicago midnight. An open circuit shows handoff-only mode | Step 2 (`_chicago`, `_next_chicago_midnight`, the `handoff_only` tile, D-5) | `tests/unit/services/test_metrics_reader_stamps.py` (4 tests, §7.2) |
| AC-9 [journey] | **J-10**, level `integrated with a scripted model`. Drive WP-2, WP-5 and WP-7 through the real server, read CON-18…20, and assert the stored values with their labels and denominators, each equal to a direct count. Every unit is `count`/`ms`/`share`; every share is in [0, 1] and equals n/d (AEA-53-4) | Step 7: the stored-rows leg on AEA-57's harness, compared with D-11's stable read. The chat-driven leg is a declared skip, blocked on AEA-51 (section 8 R-3; DV-3) | `uv run pytest -m journey tests/journeys/j10/test_aea_53.py -rs --journey-record AEA-53`, plus the record `docs/testing/journeys/<date>-AEA-53.md` |
| AC-10 [invariant] | One unit vocabulary (AEA-53-1): `count`, `ms`, `share`. Shares are 0–1 fractions. `EvalMeasure.value` is 0–1. M-24 is a count with numerator and denominator. Every mapping passes AEA-48's models | Step 2 constants. Shares are `numerator / denominator`, unrounded | `tests/unit/services/test_metrics_reader.py::test_units_and_scales` over the J-10 rows |
| AC-11 [invariant] | (`id`, `label`) unique within each response. A DO-7 split is named in `label`, and the `id` stays M-n | CON-18 and CON-19: Step 2 labels (§4.4 tables). CON-20: pass-through (R-4) | `tests/unit/services/test_metrics_reader.py::test_measure_keys_unique` |
| AC-12 [invariant] | The CON-19 health tiles are a fixed, listed set, in order, on an empty DB and after the J-10 run, with a note in `docs/plans/ux-join/` | `HEALTH_TILES` constant (§4.4) | `tests/unit/services/test_metrics_reader.py::test_health_tiles_fixed_list`. The note is Step 8 |
| AC-13 [capture] | With no Langfuse keys and every live turn's `trace_export` `off`, `trace_export` reads 0 of N turns and the `trace_export_failed` alert shows its stored state. All three pages answer 200 under a socket guard with 0 outbound attempts | Step 2 | `tests/capture/test_cap6_reads.py::test_monitoring_says_export_off_and_no_outbound` |
| AC-14 [negative] | Sentinel provider, Langfuse and eval keys and a sentinel demo password in the settings; a sentinel phrase in messages and replies. Neither the three bodies nor the logs of the three reads contain any of them. CON-20 dev failures equal the stored redacted ones field for field | The reader copies `summary["dev_failures"]` as stored and reads no settings secret | `tests/capture/test_cap6_reads.py::test_no_key_values_or_message_text` |
| AC-15 [regression/context] | Area-map A10b row (planned → actual with the commit), the ICM routes row, the ux-join note. DO-7 M-26 is already Chicago, so no DO-7 edit | Step 8 | `git diff --name-only main...HEAD` lists only the owned files |

### 3b. Source-contract reconciliation (obligations the ACs do not spell out)

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| A `request` record per page read with `request_id` | DO-6 WF-6 | Observability | other-ticket: AEA-23's middleware writes one for every request. The reader logs nothing on success | AEA-23 (merged) |
| Reads go through `UnitOfWork` repository methods | cases.md §9 ("Opens read-only units of work only"); DO-3 §2; `ports/runtime.py` `UnitOfWork` has no `connection` member | yes | **added**: no repository method lists conversations, turns, cases or promises across threads, so a read-only `MetricsRepo` is added. Granted (DV-1) | Step 1; DV-1 |
| Reason and lifecycle **display words** have one owner | source-authority rule 9; AEA-29 plan §4.2 (`services/_case_rules.py`: `REASON_LABEL`, `reason_label`, `LIFECYCLE_WORD`) | no | added: imported from AEA-29, never copied. On main, `handoff.py`, `_case_views.py` and `_case_actions.py` already import `_case_rules`, and no test forbids it (R-2 note) | Step 0 check; Step 2 |
| M-23 live latency is "segmented by gate_result" | DO-7 M-23 | no | n/a: the `Tile` schema has one value per tile. The page uses every live turn with `server_ms`, the same population `AlertEvaluator` uses. Recorded as a limit in the journey record | Step 7 record |
| Seeds reported "with and without them" (M-3, M-13, M-27) | DO-6 WF-16 | partly (`seeds_included`, `seed_count`) | n/a: the schema carries one value per measure. CON-18 includes seed rows and says so through `seeds_included` / `seed_count`. M-3 is live-only, and seed threads have no turns | D-2 |
| M-22 "per day" | DO-7 M-22 | no | Decision D-3: the counts cover every stored live row. The store holds the demo since its last reset (reset clears conversations and turns, cases.md §1.3), which is what the OpenAPI EMPTY example "Nothing since the reset" shows | D-3 |
| Handoff-only mode has no field in `MonitoringResponse` | OpenAPI; ticket AC-8 | yes (AC-8) | Decision D-5: health tile 7 `handoff_only` (value 1 or 0), listed in the AC-12 note | Step 2, Step 8 |
| The headline is the held-out north star, as stored | DO-5; AEA-24 `build_scored_report` stores `summary["headline"]` (the `M-1` measure on held-out, `None` on dev) | yes (AC-5) | Decision D-7 (revised): read the held-out summary's stored `headline` | Step 2 |
| CON-20 returns only `EvalRun`'s keys | AEA-48 route: extra keys are dropped **and logged by name**; AEA-24's summary carries `suite`, `split`, `headline`, `gates`, `failure_rows`, `withheld`, … | no | added: Decision D-10, a projection onto the seven `EvalRun` keys (a selection of stored fields, nothing computed) | Step 2 |
| CON-20 measure ids: STF-18 says DO-5 `E-n`; DO-7, the ticket's *Evaluation* section and AEA-24 use `M-n` (with `M-1:<topic>` and `E-1:hard`) | STF-18; DO-7 M-1…M-21; AEA-24 `_case_measures` | yes (AC-5, AC-11) | other-ticket: the reader passes ids through unchanged (STF-18's consequence for AEA-53). The naming belongs to the writer, AEA-24 | section 8 R-4 |

### 3c. Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `GET /api/staff/owner-metrics`, `GET /api/monitoring`, `GET /api/eval/latest` (routes AEA-48; the reader is bound here) | WF-6 | yes, DO-6 row WF-6 | CAP-6; displays M-1…M-29, computes none |

---

## 4. Shared code to use (copied from `main` at `3725c90` and the addenda)

### 4.1 Imports the reader uses (exact)

```python
from meridian.adapters.sqlite.repos_metrics import CaseFact, ConversationFact, PromiseFact, TurnFact   # Step 1 (new)
from meridian.adapters.sqlite.repos_ops import ALERT_TYPES, AlertType         # AEA-32; precedent: services/health.py
from meridian.domain.common import HandoffReason                              # StrEnum, 16 members
from meridian.policy.texts import TextId, format_usd, render                  # AEA-03
from meridian.ports.runtime import Clock, UnitOfWorkFactory                   # Clock.now() -> datetime
from meridian.services._case_rules import LIFECYCLE_WORD, reason_label       # AEA-29 (Step 0 verifies)
from meridian.services.health import AlertSettings                            # AEA-32
```
Services may import `adapters.sqlite` row and type modules (precedents: `services/health.py`, `services/ledger.py`,
`services/reset.py`). **Never import `meridian.web`** from `services/`.

### 4.2 Signatures this ticket consumes (verbatim from code)

```python
# web/deps.py (AEA-23)
class MetricsReads(Protocol):
    def owner_metrics(self) -> Mapping[str, object]: ...
    def monitoring(self) -> Mapping[str, object]: ...
    def latest_eval(self) -> Mapping[str, object]: ...
METRICS_READS: Key[MetricsReads] = Key("metrics_reads")  # AEA-53
UOW_FACTORY: Key[UnitOfWorkFactory] = Key("uow_factory")  # AEA-10
WALL_CLOCK: Key[Callable[[], datetime]] = Key("wall_clock")  # AEA-23
# Container keys provided by earlier hunks: Key("ledger") -> LedgerService (register_spend, always);
#   Key("alert_settings") -> AlertSettings (register_ops, only when the app has a web shell);
#   Key("demo_clock") -> DemoClock (AEA-30's register_demo, only when the app has a web shell)

# services/demo.py (AEA-30)
class DemoClock:
    def __init__(self, uow: UnitOfWorkFactory) -> None: ...
    def now(self) -> datetime: ...          # the stored demo_state.demo_now, as America/Chicago

# ports/runtime.py
class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
# UnitOfWork exposes core, spend, identity, booking, cases, staff, ops (ops: OpsRepos from repos_ops) and commit().

# services/ledger.py (AEA-26)
class LedgerService:
    def __init__(self, uow, *, wall_clock, daily_cap_usd, probe_after_s=..., probe_lost_after_s=...) -> None: ...
    def record(self, call: CallRecord, ids: TurnIds) -> None: ...          # recorded_at = wall_clock()
    def spend_today(self) -> float: ...                                    # USD, America/Chicago day, wall clock
    def open_circuits(self) -> tuple[ProviderName, ...]: ...
    def models_disabled(self) -> bool: ...                                 # any open circuit, or spend_today() >= cap

# services/health.py (AEA-32)
@dataclass(frozen=True)
class AlertSettings:
    latency_p95_s: float = 12.5; failure_rate: float = 0.02; zero_traffic_after: timedelta = timedelta(hours=4)
    quiet_start: dtime = dtime(22); quiet_end: dtime = dtime(6); tz: str = "America/Chicago"
    turn_window: timedelta = timedelta(minutes=60); min_turns: int = 20; evaluate_every_s: int = 60
    scheduler_stale_after_s: int = 180; heartbeat_every_s: int = 5; heartbeat_stale_after_s: int = 30
    probe_every_s: int = 15; probe_timeout_s: int = 5; failures_to_exit: int = 3
def p95_nearest_rank(values: Sequence[float]) -> float: ...   # ordered[ceil(0.95*n) - 1]; raises ValueError on empty
def load_eval_reports(reports_dir: Path, uow: UnitOfWorkFactory, *, wall_clock=..., agent_version: str = "unknown") -> int: ...
    # each *.json must be exactly {"run", "results", "summary"}; run -> EvalRunRow, results -> EvalCaseResultRow,
    # summary stored as json.dumps(summary) in eval_runs.summary_json
class AlertEvaluator:  def evaluate(self) -> tuple[AlertState, ...]: ...   # the reader never calls it

# adapters/sqlite/repos_ops.py (AEA-32)
ALERT_TYPES: tuple[AlertType, ...] = ("spend_cap_reached", "p95_latency_over_12_5s", "health_check_restart",
    "zero_traffic", "failure_rate_over_2pct", "trace_export_failed", "scheduler_stale")
class AlertState(MeridianModel): type: AlertType; state: Literal["firing", "quiet"]; fired_at: datetime | None
                                 value: float | None; threshold: float | None
class HealthEvent(MeridianModel): at_wall: datetime; kind: Literal["check_ok", "check_failed", "restart",
    "alert_fired", "alert_cleared"]; alert_type: AlertType | None; reason_code: str | None; value: float | None
    threshold: float | None; agent_version: str
class EvalRunRow(MeridianModel): run_id: str; suite: Literal["worked-pairs", "retrieval", "e2e", "load"]
    split: Literal["dev", "held-out"] | None; agent_version: str; harness_commit: str; harness_digest: str
    experiment_id: str | None; repeats: int; started_at: datetime; finished_at: datetime | None
    status: Literal["started", "completed", "failed", "incomplete"]; cases_expected: int; cases_scored: int
    index_manifest_hash: str | None; judge_spend_usd: float
class EvalCaseResultRow(MeridianModel): run_id: str; case_id: str; repeat: int; thread_id: str | None
    passed_hard: bool; items: tuple[dict[str, JsonValue], ...]
    outcome: Literal["resolved", "handed_off", "degraded", "environment_error"]; in_scope: bool | None
    topic: str | None; top3: tuple[dict[str, JsonValue], ...] = (); below_floor: bool | None = None
class StoredEvalRun(EvalRunRow): summary_json: str; loaded_at: datetime | None
tx.ops.health.append(event: HealthEvent) -> int
tx.ops.health.latest_alert_states() -> dict[AlertType, AlertState]   # every type present; default quiet
tx.ops.health.last_restart() -> HealthEvent | None
tx.ops.eval.latest_completed(suite, split) -> StoredEvalRun | None     # status = 'completed' only;
                                                                       # ORDER BY finished_at DESC, started_at DESC
class OpsRepos:   # lines 433-446 today
    health: HealthRepo; deploy: DeployRepo; eval: EvalRepo; signals: SignalsRepo
    def __init__(self, conn): self._conn = conn; self.health = …; self.deploy = …; self.eval = …; self.signals = SignalsRepo(conn)

# adapters/sqlite/db.py (AEA-10)
def parse_wall(text: str) -> datetime: ...           # the one stored-time parser (aware UTC)
# adapters/sqlite/repos_cases_state.py (AEA-10)
tx.cases.job_runs.latest() -> JobRunRow | None       # JobRunRow.started_wall_at: datetime (UTC)
tx.cases.job_runs.start(job_run_id, …)               # the test builder calls it as AEA-30 does

# policy/texts.py (AEA-03): CON-19 decision lines
TextId.MONITOR_SPEND_CAP    "Spend reached the {amount} daily cap: new chats hand off and no model calls run until tomorrow."
TextId.MONITOR_LATENCY      "p95 latency is over 12.5 s per turn: check the model route."
TextId.MONITOR_RESTART      "The health check restarted the service: check the logs."
TextId.MONITOR_ZERO_TRAFFIC "No new live chat for 4 hours: check the public URL and the health check."
TextId.MONITOR_FAILURE_RATE "More than 2% of turns failed: check the model route and the logs."
TextId.MONITOR_TRACE_EXPORT "Trace export is failing and traces are being dropped: check the Langfuse server on the VPS."
def render(text_id: TextId, /, **values: str) -> str: ...      # MONITOR_SPEND_CAP needs amount=; the others take none
def format_usd(cents: int) -> str: ...                         # 3000 -> "$30"

# services/_case_rules.py (AEA-29, on main: lines 105, 135, 342)
REASON_LABEL: Final[Mapping[HandoffReason, str]]   # e.g. refund "Refund request", safety "Safety report in chat"
LIFECYCLE_WORD: Final[Mapping[str, str]]           # "unassigned" -> "Unassigned", "resolved" -> "Resolved", …
def reason_label(reason: HandoffReason, safety_kind: str | None = None) -> str: ...   # never the enum value

# services/scheduler.py (AEA-30, on main, lines 27-31)
TICK_INTERVAL_S: Final = 60.0               # SchedulerThread ticks this often in a running server (not in container_app)
ABANDON_AFTER: Final = timedelta(minutes=30)  # the sweep's wall-clock idle limit (CAS-29)
PROMISE_MISSED_REASON: Final = "past_due"   # promises.status_reason when the tick marks a promise missed
# SchedulerJob.tick(): job_runs.start(...) -> marks open promises with due_at < demo now 'missed' -> sets 'abandoned'
#   on live open conversations whose last_customer_wall_at <= wall now - 30 min -> job_runs.finish(...)

# services/reset.py (AEA-31): the first-boot seed (an on_start hook, so container_app, which suppresses
#   starters, never runs it; the journey server does)
SEED_COUNT = 4
def seed_demo(tx: UnitOfWork, *, assembler: _BriefAssembler) -> int: ...   # 4 'seed' threads, refs MHC-C-0005..0008
def seed_first_boot(uow: UnitOfWorkFactory, seed: Callable[[UnitOfWork], int], now: datetime, *,
                    deploy_id: str | None = None) -> int: ...             # 4 on a store without seed rows, else 0
# tx.cases.refs.next_case_ref() returns max(highest ref, SEED_REF_MAX) + 1, so builder refs never collide with seeds

# policy/handoff.py (AEA-14), used by the test builders only
def promise_for(reason: HandoffReason, presence: Presence, now: datetime, window_start: datetime | None = None) -> Promise
def case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None
def priority_for(reason: HandoffReason, *, promise_due: datetime | None = None, renewal_date: date | None = None) -> Priority
```

**AEA-24's stored summary** (`eval/harness/report.py` on main, `base_summary`, lines 293–337): `run_id`, `date` (ISO Chicago
date), `agent_version`, `size`, `mix` (rows `{category, count, origin, tests}`), `measures` (each `{id, label,
numerator, denominator, value, min, max, target}`, values rounded to 4 places), `dev_failures` (`{case_id,
redacted_summary}`; `[]` on held-out), plus `suite`, `split`, `split_label`, `status`, `repeats`, `experiment_id`,
`headline` (held-out: the `M-1` measure dict; dev: `None`), `gates`, `failure_rows`, `topic_readiness`, `db_check`,
`unscored_cases`, `judge`, `cost_per_conversation_usd`, `withheld`, `empty_measures`, `not_measured`.
Measure ids AEA-24 writes: `M-1` / `M-2`, `M-1:<topic>` / `M-2:<topic>`, `M-4`, `M-5`, `M-7`, `M-8`, `M-9`, `M-10`,
`M-14`…`M-17`, `M-19`, `M-20`, `M-21`, `E-1:hard`.

### 4.3 Wire shapes the route validates (AEA-48 `web/schemas/reads.py`; extra keys are dropped **and logged**)

- `Measure{id, label, numerator: int|None, denominator: int|None, unit: count|ms|share, value: int|float|None,
  null_reason: str|None, kind: measured|estimate, case_refs: list[str]}`. A `share` value must be in [0, 1].
- `Tile{id, label, value, unit, numerator, denominator, null_reason}`.
- `OwnerMetricsResponse{as_of, seeds_included, seed_count, in_scope_correct_resolution, measured_north_star_link{label,
  path:"/eval"}, promises_kept_on_time, handoffs, outcomes[], handoffs_by_reason[], missed_promises[{reference, due_at,
  outcome}], cases[{reference, reason, status}]}`, with (id, label) unique across the measures.
- `MonitoringResponse{as_of, demo_now, health[Tile], spend{today_cents, cap_cents, day:"America/Chicago midnight to
  midnight", resets_at}, correctness{containment_estimate: Tile, escalations_by_reason[Tile]}, alerts[{type (6 values,
  no scheduler_stale), state, fired_at, decision_line}], alert_config{zero_traffic_after_hours: int, quiet_hours{start,
  end, timezone, configurable: true}}, last_restart{at, kind:"health_check"}|null, trace_export: str, redacted: true}`,
  with (id, label) unique across `health` and `correctness`.
- `EvalResponse{splits{dev: EvalRun|null, held_out: EvalRun|null}, headline: EvalMeasure|null, current_agent_version,
  dev_label}`.
- `EvalRun{run_id, date, agent_version, size, mix[{category, count, origin, tests}], measures[EvalMeasure],
  dev_failures[{case_id, redacted_summary}]}`, with (id, label) unique per run.
- `EvalMeasure{id, label, numerator: int, denominator: int, value (in [0, 1]), min, max, target: str|None}`.

Every time field must be an aware datetime. The route answers with `payload.model_dump(mode="json")`, so HTTP bodies
carry ISO strings. **Return only these keys.**

### 4.4 The decided content of each page (decisions D-1…D-10 live here)

**Populations.** `HANDLED_TOPICS = frozenset({"booking", "membership", "billing", "warranty"})` (domain `Topic` minus
"other"; DO-7 M-1 topics). "Ended" means `outcome != "open"`. `FAILURE_REASONS = frozenset({"model_error", "tool_error",
"timeout"})`, the same set `AlertEvaluator` uses.

- **D-1 M-3 (both pages, live only).**
  - Population: live conversations (`run_tag == "live"`) that have ended and have at least one turn whose `plan_topic`
    is in `HANDLED_TOPICS`.
  - Numerator: those with `outcome == "ai_resolved"` and `flag_count == 0`.
  - A conversation counts as flagged when any `flags` row's `case_ref` names a case on that thread (`flags.case_ref`
    is required, staff.md §3).
- **D-2 CON-18 population** = conversations and cases whose thread `run_tag` is `live` or `seed`. Seeds are counted and
  named: `seed_count` = the number of those cases with `seed = 1`; `seeds_included = seed_count > 0`.
- **D-3 CON-19 population** = `run_tag == "live"` only (turns also need `turns.run_tag == "live"`). There is no time
  window: the counts cover every stored live row.
- **D-4 Promises (M-13).** Denominator: promise rows with `due_at IS NOT NULL` and `status IN ('kept','missed')`, the
  verdicts already stored. Numerator: `status == 'kept'`. The reader never compares a due time with a clock.
- **D-5 Handoff-only mode** = health tile `handoff_only`: value `1` when `ledger.models_disabled()` is true or
  `ledger.open_circuits()` is non-empty, else `0`.
- **D-6 Latency** = nearest rank over the `server_ms` of live turns where `server_ms IS NOT NULL`:
  p50 = `sorted[ceil(0.5·n) − 1]`, p95 = `sorted[ceil(0.95·n) − 1]` (equal to `services.health.p95_nearest_rank`).
- **D-7 Headline (revised)** = the held-out run's stored `summary["headline"]` when it is a `dict`, else `None`. It is
  never taken from the dev split and never picked out of `measures`.
- **D-8 Wire times** go out as aware datetimes converted to `ZoneInfo("America/Chicago")`. The instant is unchanged,
  and Python compares instants, so equality tests hold.
- **D-9 `case_refs`** = the sorted distinct refs of the cases behind the **numerator**. For thread-based measures these
  are the cases on the numerator threads; for M-13, the cases of the kept promises; for a reason row, that reason's
  cases. A zero-denominator measure has `case_refs: []`.
- **D-10 CON-20 projection (new).** `EVAL_RUN_KEYS = ("run_id", "date", "agent_version", "size", "mix", "measures",
  "dev_failures")`. A split's value is `{k: summary[k] for k in EVAL_RUN_KEYS}`, copied as stored, in that key order.
  - If the summary JSON does not parse to a `dict`, or any of the seven keys is missing: the split is `None`, logged
    once with `_LOG.warning("eval_summary_unreadable run_id=%s", run.run_id)` (the run id only).
  - Nothing inside the seven values is changed: ids, labels, values, `min`, `max`, `target`, mix rows and failure
    rows all pass through.

**CON-18 measures** (all `unit: "share"`, value = `numerator / denominator` unrounded):

| Field | id | label | kind | numerator / denominator | null_reason when the denominator is 0 |
|---|---|---|---|---|---|
| `in_scope_correct_resolution` | `M-3` | `Estimate from live chats (no verified answers)` | `estimate` | D-1 | `No conversations since the reset.` if no live conversation has ended; else `No ended conversations on a handled topic yet.` |
| `promises_kept_on_time` | `M-13` | `Promises kept on time` | measured | D-4 | `No promises are due yet.` |
| `handoffs` | `M-18` | `Handoffs (all reasons)` | measured | ended D-2 conversations with `handed_off` / ended D-2 conversations | `No conversations since the reset.` |
| `outcomes[0..3]` (`[]` when no D-2 conversation has ended) | `M-18` each | `Resolved by the AI` (`ai_resolved`), `Handed off to a person` (`handed_off`), `Safety reply given` (`safety_reply`), `Abandoned` (`abandoned`), in this order | measured | that outcome / ended D-2 conversations | (n/a: the list is empty instead) |
| `handoffs_by_reason[]` (one row per reason with ≥ 1 case; `[]` when there is no case) | `M-22` | `reason_label(HandoffReason(reason))` | measured | that reason's D-2 cases / all D-2 cases | (n/a) |

- A zero-denominator measure is `numerator 0, denominator 0, value None, null_reason <text>, case_refs []`.
- Order `handoffs_by_reason` by numerator descending, then label ascending.
- `missed_promises`: one entry per D-2 promise row with `status == 'missed'` and `due_at` not null, in the
  repository's order (due ascending). Each entry is `{"reference": case_ref, "due_at": _chicago(due_at), "outcome":
  LIFECYCLE_WORD[case.lifecycle]}`.
- `cases`: one entry per distinct ref in every measure's `case_refs` plus every `missed_promises.reference`, sorted by
  reference. Each entry is `{"reference": ref, "reason": reason_label(HandoffReason(case.reason), case.safety_kind),
  "status": LIFECYCLE_WORD[case.lifecycle]}`.
- `measured_north_star_link = {"label": "The measured number is on the Evaluation page (latest held-out run).",
  "path": "/eval"}`.
- `as_of = _chicago(demo_clock.now())`.

**CON-19 health tiles** (AC-12; position, id, label, unit; the `HEALTH_TILES` constant):

| # | id | label | unit | value | null rule |
|---|---|---|---|---|---|
| 1 | `M-22` | `Conversations` | count | live conversations, any outcome | never null (0 on empty) |
| 2 | `M-22` | `Turns` | count | live turns | never null |
| 3 | `M-24` | `Failures` | count | value = numerator = turns with `outcome == "degraded_handoff"` and `degrade_reason ∈ FAILURE_REASONS`; denominator = live turns | 0 turns → value, numerator and denominator `None`, null reason `No turns yet` |
| 4 | `M-23` | `Latency p50` | ms | D-6 p50 (int ms) | 0 values → `No turns yet`; fewer than `settings.min_turns` → `Not enough turns yet (fewer than 20)` (built as `f"Not enough turns yet (fewer than {settings.min_turns})"`) |
| 5 | `M-23` | `Latency p95` | ms | D-6 p95 (int ms) | same as 4 |
| 6 | `scheduler_last_run` | `Overdue job last ran` | ms | `max(0, int((wall_now − job.started_wall_at).total_seconds() * 1000))` from `tx.cases.job_runs.latest()` | no job row → `The overdue job has not run yet` |
| 7 | `handoff_only` | `Handoff-only mode (1 = on)` | count | D-5 | never null |

- The count tiles and the latency and job tiles have `numerator: None, denominator: None`. Tile 3 is the only tile
  with both.
- `correctness.containment_estimate`: id `M-3`, label `Estimate of correct resolution from live chats (the measured
  number is on the Evaluation page)`, unit share, D-1 numbers. With a zero denominator: value, numerator and
  denominator are `None`, with the D-1 null reason.
- `correctness.escalations_by_reason`: one tile per reason over live cases (D-3). Id `M-22`, label
  `reason_label(HandoffReason(reason))`, unit count, value = the count, numerator and denominator `None`, null_reason
  `None`. Order: count descending, then label.
- `alerts`: for each `t` in `MONITOR_ALERT_TYPES = tuple(a for a in ALERT_TYPES if a != "scheduler_stale")`, in that
  order, one entry `{"type": t, "state": states[t].state, "fired_at": _chicago(states[t].fired_at) if
  states[t].state == "firing" and states[t].fired_at is not None else None, "decision_line": DECISION_LINE[t]}`.
  The spend line is `render(TextId.MONITOR_SPEND_CAP, amount=format_usd(cap_cents))`; the others are `render(<id>)`.
- `alert_config = {"zero_traffic_after_hours": int(settings.zero_traffic_after.total_seconds() // 3600),
  "quiet_hours": {"start": settings.quiet_start.strftime("%H:%M"), "end": settings.quiet_end.strftime("%H:%M"),
  "timezone": settings.tz, "configurable": True}}`.
- `spend = {"today_cents": round(spent * 100), "cap_cents": round(daily_cap_usd * 100), "day": "America/Chicago
  midnight to midnight", "resets_at": _next_chicago_midnight(wall_now)}`. The `day` value is the single-line string
  `"America/Chicago midnight to midnight"`.
- `last_restart = {"at": _chicago(r.at_wall), "kind": "health_check"}`, or `None`.
- `trace_export = f"sent {sent} of {n} turns"`, where `sent` = live turns with `trace_export == "sent"` and `n` = live
  turns (OpenAPI example "sent 70 of 74"; the ticket says "n of N turns").
- `redacted = True`. `as_of = _chicago(wall_now)`. `demo_now = _chicago(demo_clock.now())`.

**CON-20.**
- `dev_run = tx.ops.eval.latest_completed("e2e", "dev")` and `held = tx.ops.eval.latest_completed("e2e", "held-out")`.
- Each split is projected by D-10, and `headline` is D-7.
- `current_agent_version` is the constructor argument.
- `dev_label = "Dev (we read and fixed these, so it overstates)"`.
- The UI draws the stale line from `run.agent_version != current_agent_version` (OpenAPI `getLatestEval`
  description). The reader adds no field for it.

---

## 5. Steps

Area **A10b**. Dependency direction: `web/container.py` (composition root) → `services/metrics_reader.py` → `ports/`
(`Clock`, `UnitOfWorkFactory`) and the repository types. The reader implements `MetricsReads` (web.md §4)
structurally. It consumes `UnitOfWork` reads, a ledger Protocol (`MetricsLedger`, below) and `AlertSettings`. The one
new seam, `MetricsRepo`, was requested in section 8 (R-1) and granted (DV-1). It is not invented here.

### Step 0 — preconditions (stop and report if any fails)

```bash
export UV_LINK_MODE=hardlink
cd <your worktree>                    # branch aea-53-aea-53-metrics-reader from main; never copy a venv; no node_modules
git log --oneline -1 main
test -f src/meridian/services/_case_rules.py && test -f src/meridian/services/handoff.py && echo "AEA-29 merged"
uv run python -c "from meridian.services._case_rules import REASON_LABEL, LIFECYCLE_WORD, reason_label; from meridian.domain.common import HandoffReason as H; assert all(H(r) in REASON_LABEL for r in H); print(reason_label(H.REFUND), LIFECYCLE_WORD['unassigned'])"
uv run python -c "from meridian.services.handoff import BriefAssembler; print('ok')"
uv run python -c "from meridian.web.deps import METRICS_READS; from meridian.services.health import AlertSettings; print(AlertSettings().min_turns)"
uv run python -c "import meridian.web.container as c; assert 'No-op until' not in (c.register_demo.__doc__ or ''); assert 'No-op until' in (c.register_metrics_reader.__doc__ or ''); print('AEA-30 merged, hunk empty')"
test ! -e src/meridian/adapters/sqlite/repos_metrics.py && test ! -e src/meridian/services/metrics_reader.py && echo "files free"
git diff --quiet 3725c90 HEAD -- src/meridian/adapters/sqlite/repos_ops.py src/meridian/web/container.py && echo "anchors unchanged"
```
- Expected output: `AEA-29 merged`, `Refund request Unassigned`, `ok`, `20`, `AEA-30 merged, hunk empty`, `files free`,
  `anchors unchanged`.
- If `anchors unchanged` is missing, `repos_ops.py` or `container.py` moved after this plan. Re-read `OpsRepos` and
  `register_metrics_reader` and apply Steps 1 and 5 to the same functions. If another ticket now owns either spot,
  stop and report.
- The R-1 grant is recorded (DV-1). It needs no confirmation.
- If AEA-29's names differ (for example, the labels live elsewhere), stop and report `BLOCKED-ON AEA-29 names`. Do not
  copy the label tables.

### Step 1 — `src/meridian/adapters/sqlite/repos_metrics.py` and the hook (granted, DV-1)

Create the file with exactly this content, then run `ruff format` on it:

```python
"""Read-only facts for the CON-18…CON-20 reads (AEA-53; stage7/cases.md section 9). Plain queries over stored rows.

MetricsReader counts and divides these facts. Nothing here decides an outcome, applies a rule or writes a row.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from meridian.adapters.sqlite.db import parse_wall
from meridian.domain.common import MeridianModel

ConversationTag = Literal["live", "eval", "load", "seed"]
_TAGS: frozenset[str] = frozenset({"live", "eval", "load", "seed"})


class ConversationFact(MeridianModel):
    thread_id: str
    run_tag: ConversationTag
    outcome: Literal["ai_resolved", "handed_off", "safety_reply", "abandoned", "open"]
    topics: tuple[str, ...]  # distinct non-null turns.plan_topic of this thread, sorted
    flag_count: int  # flags rows whose case_ref names a case on this thread


class TurnFact(MeridianModel):
    status: Literal["running", "completed", "failed"]
    outcome: str | None
    degrade_reason: str | None
    server_ms: int | None
    trace_export: Literal["off", "sent", "failed"] | None


class CaseFact(MeridianModel):
    case_ref: str
    thread_id: str
    thread_run_tag: ConversationTag
    reason: str
    safety_kind: str | None
    lifecycle: str
    seed: bool


class PromiseFact(MeridianModel):
    promise_id: int
    case_ref: str
    status: Literal["open", "kept", "missed", "changed"]
    due_at: datetime | None


def _marks(run_tags: Sequence[str]) -> str:
    if not run_tags or any(tag not in _TAGS for tag in run_tags):
        raise ValueError("run_tags must be a non-empty subset of live, eval, load, seed")
    return ",".join("?" for _ in run_tags)


class MetricsRepo:
    """= tx.ops.metrics. Every query is a SELECT; the connection is the unit of work's."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def conversations(self, run_tags: Sequence[ConversationTag]) -> tuple[ConversationFact, ...]:
        marks = _marks(run_tags)
        rows = self._conn.execute(
            f"SELECT thread_id, run_tag, outcome FROM conversations WHERE run_tag IN ({marks}) "  # noqa: S608 - placeholders only
            "ORDER BY started_at, thread_id",
            tuple(run_tags),
        ).fetchall()
        topics: dict[str, list[str]] = {}
        for thread_id, topic in self._conn.execute(
            "SELECT DISTINCT thread_id, plan_topic FROM turns WHERE plan_topic IS NOT NULL "
            "ORDER BY thread_id, plan_topic"
        ):
            topics.setdefault(str(thread_id), []).append(str(topic))
        flags = {
            str(thread_id): int(n)
            for thread_id, n in self._conn.execute(
                "SELECT k.thread_id, COUNT(f.id) FROM flags f JOIN cases k ON k.case_ref = f.case_ref "
                "GROUP BY k.thread_id"
            )
        }
        return tuple(
            ConversationFact.model_validate(
                {
                    "thread_id": r[0],
                    "run_tag": r[1],
                    "outcome": r[2],
                    "topics": tuple(topics.get(str(r[0]), ())),
                    "flag_count": flags.get(str(r[0]), 0),
                }
            )
            for r in rows
        )

    def live_turns(self) -> tuple[TurnFact, ...]:
        rows = self._conn.execute(
            "SELECT t.status, t.outcome, t.degrade_reason, t.server_ms, t.trace_export FROM turns t "
            "JOIN conversations c ON c.thread_id = t.thread_id "
            "WHERE t.run_tag = 'live' AND c.run_tag = 'live' ORDER BY t.rowid"
        ).fetchall()
        return tuple(
            TurnFact.model_validate(
                {"status": r[0], "outcome": r[1], "degrade_reason": r[2], "server_ms": r[3], "trace_export": r[4]}
            )
            for r in rows
        )

    def cases(self, run_tags: Sequence[ConversationTag]) -> tuple[CaseFact, ...]:
        marks = _marks(run_tags)
        rows = self._conn.execute(
            "SELECT k.case_ref, k.thread_id, c.run_tag, k.reason, k.safety_kind, k.lifecycle, k.seed FROM cases k "
            f"JOIN conversations c ON c.thread_id = k.thread_id WHERE c.run_tag IN ({marks}) "  # noqa: S608 - placeholders only
            "ORDER BY k.case_ref",
            tuple(run_tags),
        ).fetchall()
        return tuple(
            CaseFact.model_validate(
                {
                    "case_ref": r[0],
                    "thread_id": r[1],
                    "thread_run_tag": r[2],
                    "reason": r[3],
                    "safety_kind": r[4],
                    "lifecycle": r[5],
                    "seed": bool(r[6]),
                }
            )
            for r in rows
        )

    def promises(self, run_tags: Sequence[ConversationTag]) -> tuple[PromiseFact, ...]:
        marks = _marks(run_tags)
        rows = self._conn.execute(
            "SELECT p.id, p.case_ref, p.status, p.due_at FROM promises p "
            "JOIN cases k ON k.case_ref = p.case_ref JOIN conversations c ON c.thread_id = k.thread_id "
            f"WHERE c.run_tag IN ({marks}) "  # noqa: S608 - placeholders only
            "ORDER BY p.due_at IS NULL, p.due_at, p.case_ref, p.id",
            tuple(run_tags),
        ).fetchall()
        return tuple(
            PromiseFact.model_validate(
                {
                    "promise_id": r[0],
                    "case_ref": r[1],
                    "status": r[2],
                    "due_at": parse_wall(r[3]) if r[3] is not None else None,
                }
            )
            for r in rows
        )
```

Make the hook in `src/meridian/adapters/sqlite/repos_ops.py`. These three edits are the only ones allowed in that
file:
1. Add `from meridian.adapters.sqlite.repos_metrics import MetricsRepo` to the import block, right after
   `from meridian.adapters.sqlite.db import format_wall, integrity_errors, last_row_id, parse_wall` (isort order).
2. In `class OpsRepos`, add the annotation `metrics: MetricsRepo` after `signals: SignalsRepo`.
3. In `OpsRepos.__init__`, add `self.metrics = MetricsRepo(conn)` after `self.signals = SignalsRepo(conn)`. Change the
   class docstring's list from `health, deploy, eval, signals` to `health, deploy, eval, signals, metrics (AEA-53)`.

*Invariants:* `MetricsRepo` holds the unit of work's connection (AEA-10's `test_uow` checks `vars(repo)["_conn"] is
tx.connection` on top-level repos only), and it runs SELECTs only. `repos_metrics.py` imports only `db` and
`domain.common`, so there is no import cycle with `repos_ops.py`.
Then write `tests/unit/services/test_metrics_reader_repo.py` (§7.2) and run it.

### Step 2 — `src/meridian/services/metrics_reader.py`

Module docstring: "Serve stored measures without recomputing outcomes (A10b, AEA-53; stage7/cases.md section 9; DO-3
section 4.4). Each method opens one read-only unit of work, counts and divides stored fields, and returns a mapping with
the OpenAPI field names (web.md section 4 MetricsReads, structurally). It never runs a gate, a check, a policy rule or a
model, never applies an alert line (AlertEvaluator does) and never re-judges an outcome or re-scores an eval run (the
writers store them)."

Write it in this order. Keep each helper module-private (`_name`). Target under 450 lines (service cap 600).

1. **Imports**: §4.1, plus `import json, logging, math`, `from collections import Counter`, `from collections.abc import
   Callable, Mapping, Sequence`, `from datetime import datetime, time, timedelta`, `from typing import Final, Protocol`,
   `from zoneinfo import ZoneInfo`.
2. **Constants** (each `Final`):
   - `CHICAGO = ZoneInfo("America/Chicago")`, `HANDLED_TOPICS`, `FAILURE_REASONS`, `OWNER_TAGS = ("live", "seed")`,
     `LIVE_TAGS = ("live",)`.
   - The labels and null reasons exactly as written in §4.4: `NO_CONVERSATIONS = "No conversations since the reset."`,
     `NO_HANDLED_TOPIC = "No ended conversations on a handled topic yet."`, `NO_PROMISES_DUE = "No promises are due
     yet."`, `NO_TURNS = "No turns yet"`, `NO_JOB_RUN = "The overdue job has not run yet"`, `SPEND_DAY = "America/Chicago
     midnight to midnight"`, `DEV_LABEL`, `NORTH_STAR_LINK_LABEL`, `M3_OWNER_LABEL`, `M3_MONITOR_LABEL`.
   - `OUTCOME_ROWS: tuple[tuple[str, str], ...] = (("ai_resolved", "Resolved by the AI"), ("handed_off", "Handed off to
     a person"), ("safety_reply", "Safety reply given"), ("abandoned", "Abandoned"))`.
   - `HEALTH_TILES: tuple[tuple[str, str, str], ...]` = the seven (id, label, unit) triples of §4.4, in order.
   - `MONITOR_ALERT_TYPES`; `DECISION_LINE: Mapping[str, TextId]` (six entries: `spend_cap_reached` →
     `MONITOR_SPEND_CAP`, `p95_latency_over_12_5s` → `MONITOR_LATENCY`, `health_check_restart` → `MONITOR_RESTART`,
     `zero_traffic` → `MONITOR_ZERO_TRAFFIC`, `failure_rate_over_2pct` → `MONITOR_FAILURE_RATE`,
     `trace_export_failed` → `MONITOR_TRACE_EXPORT`).
   - `EVAL_RUN_KEYS` (D-10). `_LOG = logging.getLogger("meridian.reads")`.
3. **Ledger Protocol** (the precedent is `services.health.SpendReader`; the real `LedgerService` satisfies it because
   `tuple[ProviderName, ...]` is a `tuple[str, ...]`):
   ```python
   class MetricsLedger(Protocol):
       def spend_today(self) -> float: ...
       def models_disabled(self) -> bool: ...
       def open_circuits(self) -> tuple[str, ...]: ...
   ```
4. **Pure helpers**:
   - `_chicago(at: datetime) -> datetime`: raise `ValueError("naive datetime")` if `at.tzinfo is None or
     at.utcoffset() is None`; return `at.astimezone(CHICAGO)`.
   - `_next_chicago_midnight(now: datetime) -> datetime`: `local = _chicago(now)`; return
     `datetime.combine(local.date() + timedelta(days=1), time(0), tzinfo=CHICAGO)`.
   - `_nearest_rank(values: Sequence[int], q: float) -> int`: `ordered = sorted(values)`; return
     `ordered[math.ceil(q * len(ordered)) - 1]`. The caller guarantees `values` is not empty.
   - `_share(mid, label, numerator, denominator, null_reason, case_refs, *, kind="measured") -> dict[str, object]`:
     with `denominator == 0` it returns the §4.4 zero form; otherwise `value = numerator / denominator`,
     `null_reason None`, `case_refs = sorted(set(case_refs))`, `unit "share"`.
   - `_tile(tid, label, unit, value, *, numerator=None, denominator=None, null_reason=None) -> dict[str, object]`.
   - `_m3(conversations) -> tuple[int, int, list[str], str | None]`: implements D-1 and returns (numerator,
     denominator, numerator thread ids, null reason or None).
   - `_eval_split(run: StoredEvalRun | None) -> tuple[dict[str, object] | None, object]`: implements D-10 and returns
     (the projected split, or None; the raw stored `headline` value, or None). The steps:
     1. `run is None` → `(None, None)`.
     2. `summary = json.loads(run.summary_json)`; on `ValueError`, warn (D-10 line) and return `(None, None)`.
     3. If `summary` is not a `dict` or `any(k not in summary for k in EVAL_RUN_KEYS)`, warn and return `(None, None)`.
     4. Return `({k: summary[k] for k in EVAL_RUN_KEYS}, summary.get("headline"))`.
     *Invariant:* the reader copies stored values and computes none, so an unreadable report becomes "no run", never a
     500 and never a guessed number.
5. **Class**:
   ```python
   class MetricsReader:
       def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, wall_clock: Callable[[], datetime],
                    ledger: MetricsLedger, settings: AlertSettings, current_agent_version: str,
                    daily_cap_usd: float) -> None: ...
       def owner_metrics(self) -> Mapping[str, object]: ...
       def monitoring(self) -> Mapping[str, object]: ...
       def latest_eval(self) -> Mapping[str, object]: ...
   ```
   - `owner_metrics`: one `with self._uow() as tx:` block reads `tx.ops.metrics.conversations(OWNER_TAGS)`,
     `.cases(OWNER_TAGS)` and `.promises(OWNER_TAGS)`. Outside the block, build §4.4's CON-18 mapping. Use
     `as_of = _chicago(self._demo_clock.now())`.
   - `monitoring`, in this order:
     1. `wall_now = self._wall_clock()` (`_chicago` rejects a naive value).
     2. `spent = self._ledger.spend_today()`; `handoff_only = self._ledger.models_disabled() or
        bool(self._ledger.open_circuits())`. These come **before** the unit of work, because the ledger opens its own
        read unit.
     3. One `with self._uow() as tx:` block reads `conversations(LIVE_TAGS)`, `live_turns()`, `cases(LIVE_TAGS)`,
        `tx.ops.health.latest_alert_states()`, `tx.ops.health.last_restart()` and `tx.cases.job_runs.latest()`.
     4. `demo_now = self._demo_clock.now()`. Build §4.4's CON-19 mapping, with the tiles in `HEALTH_TILES` order.
   - `latest_eval`:
     1. One `with self._uow() as tx:` block reads `dev = tx.ops.eval.latest_completed("e2e", "dev")` and
        `held = tx.ops.eval.latest_completed("e2e", "held-out")`.
     2. `dev_split, _ = _eval_split(dev)` (the dev headline is ignored); `held_split, stored_headline =
        _eval_split(held)`.
     3. `headline = stored_headline if held_split is not None and isinstance(stored_headline, dict) else None` (D-7).
     4. Return `{"splits": {"dev": dev_split, "held_out": held_split}, "headline": headline,
        "current_agent_version": self._agent_version, "dev_label": DEV_LABEL}`.

   *Invariants:*
   - no `write=True` anywhere;
   - no import of `meridian.web`, `meridian.gates`, `meridian.checks`, `meridian.agent`,
     `meridian.policy.{handoff,escalation,booking}` or `meridian.services.health.AlertEvaluator`;
   - no logging on success;
   - no key outside §4.3.

### Step 3 — `tests/unit/services/test_metrics_reader_rows.py` (builders; section 6)

### Step 4 — unit tests: `test_metrics_reader.py`, `test_metrics_reader_alerts.py`, `test_metrics_reader_stamps.py` (§7.2)

### Step 5 — `register_metrics_reader` in `src/meridian/web/container.py` (replace the body and the docstring; nothing else in the file)

```python
def register_metrics_reader(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-53 reads: MetricsReader bound to get_metrics_reads() (cases.md §9).

    Provides deps.METRICS_READS ("metrics_reads"): one MetricsReader over Key("uow_factory") (AEA-10), the demo clock
    Key("demo_clock") (AEA-30, read through a forwarder each time a page stamps a demo time, as register_staff_live
    does, so a container without register_demo still builds; there a demo stamp raises RuntimeError("not bound:
    demo_clock")), Key("wall_clock") (AEA-23), Key("ledger") (AEA-26), Key("alert_settings") (AEA-32),
    settings.agent_version and limits.spend.daily_cap_usd (MC-22). An app that create_app did not build has no web
    shell, so this does nothing.
    """
    from datetime import datetime

    from meridian.services.metrics_reader import MetricsReader
    from meridian.web.deps import METRICS_READS, UOW_FACTORY, WALL_CLOCK
    from meridian.web.middleware import WebShellState

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    demo_clock_key: Key[Any] = Key("demo_clock")

    class _DemoClock:
        """Resolves AEA-30's clock at call time (the register_staff_live forwarder)."""

        def now(self) -> datetime:
            try:
                clock = container.get(demo_clock_key)
            except ContainerError as exc:
                if str(exc) == f"not provided: {demo_clock_key.name}":
                    raise RuntimeError(f"not bound: {demo_clock_key.name}") from None
                raise
            moment: datetime = clock.now()
            return moment

    container.provide(
        METRICS_READS,
        lambda c: MetricsReader(
            c.get(UOW_FACTORY),
            _DemoClock(),
            c.get(WALL_CLOCK),
            c.get(Key[Any]("ledger")),
            c.get(Key[Any]("alert_settings")),
            str(settings.agent_version),
            limits.spend.daily_cap_usd,
        ),
    )
```
*Invariants:*
- The docstring keeps "AEA-53" and must not contain "No-op until" (AEA-01's `test_every_register_stub_present` keys on
  it).
- The module-level imports of `container.py` are unchanged (`test_container_imports_only_policy_limits`).
- `provide(METRICS_READS, …)` type-checks only if `MetricsReader` structurally satisfies `MetricsReads`, so mypy is the
  static proof.
- **Why the forwarder stays now that AEA-30 is merged.** `register_cases`, `register_chat` and `register_staff_live`
  all reach the demo clock lazily. A direct `c.get(Key("demo_clock"))` inside this factory would make
  `container.build()` fail in any test container that runs this hunk without `register_demo`. With the real app,
  the forwarder resolves AEA-30's `DemoClock` on every call.

Then write `tests/integration/test_reads_composition.py` (§7.2).

### Step 6 — `tests/capture/test_cap6_reads.py` (§7.2)

### Step 7 — `tests/journeys/j10/test_aea_53.py` and the record (§7.2, section 8 R-3)

**D-11, a stable read on a live server.** The journey server runs AEA-30's scheduler thread, which ticks every 60 s
(`TICK_INTERVAL_S`). A tick does three things:
- it writes a `job_runs` row;
- it marks `missed` every open promise whose `due_at` is before the demo time;
- it sets `abandoned` on every live open conversation idle for 30 minutes of wall time (STALE_OPEN qualifies).

So the test compares the pages with SQL like this, in a helper `_stable_read(journey, client)`:
1. `before = _counts(journey.db)`. This is a `dict[str, object]` of every §6.4 scalar:
   - CON-18: the ended count and each per-outcome count, the M-3 numerator and denominator, the cases-by-reason
     rows, the seed count, and the kept and missed promise counts;
   - CON-19: the conversation, turn, failure and trace-sent counts.
2. GET CON-18, CON-19 and CON-20 as owner.
3. `after = _counts(journey.db)`.
4. If `before == after`, return the three bodies and `after`. Otherwise repeat from 1, at most 3 attempts in all.
   Then fail with `"store changed during every read attempt"`.

*Invariant:* a page is compared only with SQL that bracketed it unchanged. A tick therefore cannot make the test flaky,
and a reader bug cannot hide behind a retry: the values must still be equal.

Some fields move with wall time alone, so they are not compared for equality:
- the `scheduler_last_run` tile: assert an `int` ≥ 0 when `journey.db.count("job_runs") > 0`, else its null reason;
- `as_of` and `demo_now`;
- alert states: the watchdog and the tick may write alert rows.

`last_restart.at` is compared with `tx.ops.health.last_restart().at_wall`, read through
`journey.container.get(UOW_FACTORY)` right after the GETs.

Run `uv run pytest -m journey tests/journeys/j10/test_aea_53.py -rs --journey-record AEA-53`. The harness writes
`docs/testing/journeys/<Chicago date>-AEA-53.md`. Then append one **Notes** paragraph under its table that says:
- the other evidence and its level: the unit, capture and integration tests are `mock-tested` (in process, the real
  container and the real `DemoClock`, no server process);
- this journey's level: `integrated with a scripted model` for the read leg (real server, DB copy, guards on). The WP
  rows are written through the writers' repositories, not driven through chat (DV-3);
- what is blocked: the chat-driven leg, on AEA-51 (the graph and `run_graph`);
- the limits: no time window (D-3); latency is not segmented by `gate_result`; CON-20 measure ids are passed through as
  the harness stores them (R-4);
- "Journeys that will exercise this code: J-10; AEA-55's UI integration".

### Step 8 — context (AC-15, AC-12 note)

- **`docs/plans/ux-join/AEA-53-con19-health-tiles.md`** (new). Title: "CON-19 health tiles (AEA-53, AC-12)". Content:
  - one sentence: the list is fixed and always in this order, on an empty store too;
  - the seven-row table of §4.4 (position, id, label, unit, null reasons);
  - the line "SCR-10's empty state keys on tile 1 (`M-22` Conversations) having value 0";
  - the two non-registry ids (`scheduler_last_run`, `handoff_only`, D-5);
  - one sentence that `trace_export` reads "sent n of N turns".
  Make no other edit in that folder.
- **`.claude/reference/area-map.md`**, row A10b (line 46):
  - Status cell → "built: AEA-48 (cb7df88): web/routes/reads.py, web/schemas/reads.py, register_reads hunk; AEA-53
    (`<code commit>`): services/metrics_reader.py, adapters/sqlite/repos_metrics.py (read-only MetricsRepo, wired as
    OpsRepos.metrics), register_metrics_reader hunk".
  - Add `adapters/sqlite/repos_metrics.py` to that row's *Owns* cell.
- **`.claude/state/icm-progress.md`**, the A10b "Routes verified against code and tests" row (line 38, the one citing
  AEA-48):
  - Replace its evidence cell with "2026-10-21: area map A10b → services/metrics_reader.py, repos_metrics.py behind
    web/routes/reads.py (AEA-53, `<sha>`) checked by tests/unit/services/test_metrics_reader*.py,
    tests/integration/test_reads_composition.py, tests/capture/test_cap6_reads.py (`<n>` passed); record
    docs/testing/journeys/`<date>`-AEA-53.md". Keep it ≤ 400 characters.
  - The last cell becomes "Verified when every area-map row is actual".

### Step 9 — gates and commits (section 7)

Commit the code and tests first, then the context in a second commit. Use explicit `git add <paths>`.

---

## 6. Data and fixtures (synthetic only)

All rows are built at test time through the **real writers' repositories**:
- `tx.core.conversations.insert` / `set_outcome`;
- `tx.core.turns.begin` / `finish`;
- `tx.core.messages.append`;
- `tx.cases.refs.next_case_ref`, `tx.cases.cases.insert`, `tx.cases.promises.insert` / `set_status`;
- `tx.staff.flags.insert`;
- `tx.ops.health.append`;
- `tx.cases.job_runs.start`;
- `LedgerService.record`;
- `load_eval_reports`;
- `seed_first_boot` with AEA-29's `BriefAssembler`.

Raw SQL goes through `tx.connection` and is used **only** for the independent counts in assertions.

Sources of shape: AEA-10's `tests/unit/adapters/sqlite/helpers.py` (`new_thread`, `new_turn`, `conversation`,
`turn_ids`, `turn_record`; import them, do not copy), AEA-26's `tests/services/test_ledger.py` `make_call` (copy its
dict, below), AEA-24's `report.py` (summary shape) and AEA-30's scheduler (the `"past_due"` reason).

**No literal phone, card, code or secret** appears in any file. Sentinels are generated per run with `secrets`/`uuid`,
and are never printed.

### 6.1 `tests/unit/services/test_metrics_reader_rows.py` (builders; no `test_` functions)

**Clocks and the ledger double**
- `CHI = ZoneInfo("America/Chicago")`; `WALL_NOW = datetime(2026, 10, 21, 20, 15, tzinfo=UTC)` (15:15 Chicago);
  `DEMO_NOW = DEMO_START` (from `meridian.adapters.sqlite.repos_cases`).
- `class WallClock`: a callable with a mutable `.now` attribute; `__call__` returns it.
- `class LedgerDouble(spent: float = 0.0, circuits: tuple[str, ...] = (), capped: bool = False)` with
  `spend_today() -> self.spent`, `open_circuits() -> self.circuits` and `models_disabled() -> bool(self.circuits) or
  self.capped`.

**Turns**
- `turn_record_for(*, gate_result="clear", path="talk", outcome="answered", degrade_reason=None, topic: str | None =
  "billing", server_ms=1200, trace_export="off", trace_id=None, response=None) -> TurnRecord`:
  - start from `helpers.turn_record()`'s dict shape (`status "completed"`, `trace{gate_result, path, outcome,
    degrade_reason, planner{…, topic}, danger_raised False, specialists_run []}`, `replied_at`, `server_ms`,
    `model_calls 2`, `input_tokens 100`, `output_tokens 40`, `cost_usd 0.0125`, `tool_calls 1`, `trace_id`,
    `trace_export`, `response`);
  - set `planner` to `None` when `topic is None`;
  - use `replied_at=WALL_NOW`;
  - `response` defaults to `"synthetic reply " + uuid4().hex[:6]`;
  - call `TurnRecord.model_validate`.
- `add_turn(uow, thread, *, run_tag="live", **record_kw) -> TurnIds`: `ids = helpers.turn_ids(thread, new_turn(),
  run_tag=run_tag)`, then `tx.core.turns.begin(ids, DEMO_START)`, then `tx.core.turns.finish(ids.turn_id,
  turn_record_for(**record_kw))`; commit; return `ids`.

**Conversations, cases and flags**
- `add_conversation(uow, *, run_tag="live", outcome="open", last_customer_wall_at=None) -> ThreadId`:
  1. insert with `helpers.conversation(thread, run_tag=…, started_wall_at=WALL_NOW,
     last_customer_wall_at=…)`;
  2. when the outcome is not `open`, call `set_outcome(thread, outcome, ended_wall_at=WALL_NOW)`;
  3. commit.
- `add_case(uow, thread, *, reason: HandoffReason, lifecycle="unassigned", safety_kind: str | None = None,
  missed=False) -> CaseRef`, in one write unit of work:
  1. `ref = tx.cases.refs.next_case_ref()`;
  2. `promise = promise_for(reason, "nobody_online", DEMO_NOW)` (from `meridian.policy.handoff`);
  3. `tx.cases.cases.insert(CaseRow.model_validate({"case_ref": ref, "thread_id": thread, "reason": reason,
     "priority": priority_for(reason, promise_due=promise.due_at), "rule_id": "test.rule", "trigger": "escalation",
     "lifecycle": lifecycle, "due_at": case_due_at(reason, promise, None), "safety_kind": safety_kind, "created_at":
     DEMO_NOW, "updated_at": DEMO_NOW}))`;
  4. `tx.cases.promises.insert(ref, promise, DEMO_NOW)`;
  5. if `missed` and `promise.due_at is not None`: `tx.cases.promises.set_status(ref, "missed", DEMO_NOW,
     "past_due")` (exactly as AEA-30's tick stores it);
  6. commit.
- `add_flag(uow, case_ref)`: `tx.staff.flags.insert(FlagRow.model_validate({"case_ref": ref, "target": "answer",
  "message_id": None, "note": None, "reason": None, "flagged_by_role": "supervisor", "flagged_at": DEMO_NOW, "status":
  "new", "reviewed_by_role": None, "reviewed_note": None, "reviewed_at": None}))`; commit.

**Spend**
- `call_record(cost: float) -> CallRecord`: `CallRecord.model_validate({"provider": "anthropic", "model":
  "claude-sonnet-test", "latency_ms": 1200, "input_tokens": 9000, "output_tokens": 700, "cache_read_tokens": 0,
  "cache_write_tokens": 0, "thinking_tokens": 0, "cost_usd": cost, "cost_source": "price_table", "status": "ok",
  "failure": None, "provider_request_id": "req_test_0001", "stop_reason": "end_turn", "role": Role.RESPONDER,
  "attempt": 1})` (`Role` and `CallRecord` from `meridian.ports.models`).

**Eval reports**
- `write_eval_reports(dir: Path, *, agent_version: str, dev=True, held_out=True, held_out_incomplete=False,
  dev_failure_text="Quoted the stale fee for [name].", quote: str | None = None) -> dict[str, str]` writes one
  `<run_id>.json` per run, shaped `{"run": …, "results": […], "summary": …}`, and returns `{split: run_id}`. Load the
  files with `load_eval_reports(dir, uow)`.
  - `run` (an `EvalRunRow` dict): `{"run_id": f"e2e-{split}-{uuid4().hex[:6]}", "suite": "e2e", "split": split,
    "agent_version": agent_version, "harness_commit": "testcommit", "harness_digest": "testdigest", "experiment_id":
    None, "repeats": 3, "started_at": "2026-10-21T18:00:00+00:00", "finished_at": "2026-10-21T18:30:00+00:00",
    "status": "completed", "cases_expected": 4, "cases_scored": 4, "index_manifest_hash": None, "judge_spend_usd":
    0.0}`.
  - The incomplete variant has `"status": "incomplete"`, `"cases_scored": 3` and `"finished_at": None`.
  - `results` (`EvalCaseResultRow` dicts): four rows `{"run_id": rid, "case_id": f"{split}-00{i}", "repeat": 1,
    "thread_id": None, "passed_hard": True, "items": [{"item": "must_do", "index": 0, "passed": True}], "outcome":
    "resolved", "in_scope": True, "topic": "billing"}`. When `quote` is given, the dev rows' first item also carries
    `"failing_quote": quote`.
  - `summary`: every AEA-24 `base_summary` key (§4.2), so the projection is exercised:
    - `"run_id": rid`, `"date": "2026-10-21"`, `"agent_version": agent_version`, `"size": 4`;
    - `"mix": [{"category": "billing", "count": 4, "origin": "transcript", "tests": None}]`;
    - `"suite": "e2e"`, `"split": split`, `"split_label": split`, `"status": <run status>`, `"repeats": 3`,
      `"experiment_id": None`;
    - `"gates": {}`, `"failure_rows": []`, `"topic_readiness": {}`, `"db_check": {"status": "not_run"}`,
      `"unscored_cases": []`, `"judge": {"enabled": False}`, `"cost_per_conversation_usd": None`, `"withheld": None`,
      `"empty_measures": []`, `"not_measured": []`.
  - Held-out `measures`, in this order:
    1. `{"id": "M-1", "label": "In-scope correct resolution (held-out)", "numerator": 3, "denominator": 4, "value":
       0.75, "min": 0.5, "max": 0.75, "target": "≥ 90% per handled topic"}`;
    2. `{"id": "M-1:billing", "label": "In-scope correct resolution: billing (held-out)", "numerator": 3,
       "denominator": 4, "value": 0.75, "min": 0.5, "max": 0.75, "target": "≥ 90% for this topic"}`;
    3. `{"id": "M-19", "label": "Escalation recall on out-of-scope cases", "numerator": 1, "denominator": 1, "value":
       1.0, "min": 1.0, "max": 1.0, "target": "≥ 95%"}`.
    Held-out `"headline"` = a copy of measure 1; held-out `"dev_failures": []`.
  - Dev `measures`:
    1. `{"id": "M-2", "label": "In-scope correct resolution (dev)", "numerator": 2, "denominator": 4, "value": 0.5,
       "min": 0.25, "max": 0.5, "target": None}`;
    2. `{"id": "M-4", "label": "Scope coverage: in-scope cases", "numerator": 4, "denominator": 4, "value": 1.0,
       "min": 1.0, "max": 1.0, "target": None}`.
    Dev `"headline": None`; dev `"dev_failures": [{"case_id": "dev-001", "redacted_summary": dev_failure_text}]`.

**Sentinels**
- `sentinels() -> dict[str, str]`:
  - name: `"Zq"` plus 10 letters drawn with `secrets.choice(string.ascii_letters)`;
  - phone: three random digit groups of 3, 3 and 4 digits joined with `-`;
  - code: 6 random digits;
  - card: `"4"` plus 15 random digits;
  - trace_id: `"trace-" + uuid4().hex`.
  Never print them.

**The J-10 seed**
- `seed_j10_rows(uow, ledger, *, with_seed: bool) -> J10Rows`:
  - When `with_seed` is true, it first runs `seed_first_boot(uow, functools.partial(seed_demo,
    assembler=BriefAssembler()), WALL_NOW)` (4 seed cases; AEA-31 and AEA-29).
  - Then it writes the §6.2 table.
  - **Which seed each level gets.** `container_app` suppresses starters, so its first-boot seed never runs: the
    HTTP-level capture tests that need seeds call `seed_j10_rows(h.uow, ledger, with_seed=True)` after entering the
    client. The journey server already ran the first-boot seed, so the journey passes `with_seed=False`.
  - `J10Rows` is a frozen dataclass with fields `wp2, wp5, wp7, failed, flagged, abandoned, stale_open, eval_thread,
    load_thread` (ThreadId), `wp5_case, wp7_case, flagged_case` (CaseRef) and `wp2_turn: TurnIds`.

### 6.2 The J-10 rows (shared by the unit, capture, integration and journey tests)

| Row | Writer calls | Represents |
|---|---|---|
| WP-2 | live conversation, `ai_resolved`; turns (`path "act"`, `outcome "acted"`, topic `billing`, 2300 ms) and (`talk`, `answered`, `billing`, 1500 ms); `ledger.record(call_record(0.0123), ids)` and `ledger.record(call_record(0.0456), ids)` with the first turn's `TurnIds` | a verified account read with model calls and spend rows |
| WP-5 | live conversation, `safety_reply`; turn (`gate_result "safety"`, path `safety`, outcome `safety_reply`, topic `None`, 40 ms); case `HandoffReason.SAFETY`, `safety_kind "co"`, unassigned | a safety turn and its P0 case |
| WP-7 | live conversation, `handed_off`; turn (path `handoff`, outcome `handed_off`, `billing`, 3100 ms); case `HandoffReason.REFUND`, unassigned, `missed=True` | a refund handoff with a missed P3 promise |
| FAILED | live conversation, `open`; turn (path `degraded`, outcome `degraded_handoff`, `degrade_reason "model_error"`, topic `None`, 60000 ms) | a failure turn |
| FLAGGED | live conversation, `ai_resolved`; turn (`talk`, `answered`, `booking`, 900 ms); case `HandoffReason.UNSUPPORTED_ACTION`, lifecycle `resolved`; one flag on that case | M-3 drops it |
| ABANDONED | live conversation, `abandoned` (as AEA-30's sweep stores it), `last_customer_wall_at = WALL_NOW − 2 h`; no turns | M-18 abandoned |
| STALE_OPEN | live conversation, `open`, `last_customer_wall_at = WALL_NOW − 2 h`; no turns | not abandoned on read (AC-7) |
| EVAL / LOAD | one `eval` and one `load` conversation, `ai_resolved`, each with one turn of the same `run_tag` (`billing`, 500 ms) | excluded from live counts |
| OPS | `tx.ops.health.append(HealthEvent(kind="restart", at_wall=WALL_NOW − 3 h, reason_code="healthz_failed_3_in_a_row", value=3.0, threshold=3.0, alert_type=None, agent_version="test"))`; `tx.cases.job_runs.start("job-j10", started_wall_at=WALL_NOW − 2 min, demo_now=DEMO_NOW)`; commit | M-28 and `scheduler_last_run` |

Expected values over these rows, without seeds. With seeds, add the 4 seed cases and the 4 ended seed conversations;
the tests take the seed side from SQL, not from literals.
- **CON-19:**
  - Conversations 7; Turns 6; Failures 1 of 6.
  - Latency null with "Not enough turns yet (fewer than 20)".
  - `scheduler_last_run` 120000 ms; `trace_export` "sent 0 of 6 turns".
  - Escalations: `reason_label(SAFETY, "co")` is not used here: escalation tiles use `reason_label(HandoffReason(r))`.
    The three tiles are SAFETY 1, REFUND 1 and UNSUPPORTED_ACTION 1.
  - `last_restart.at` = WALL_NOW − 3 h.
  - `spend.today_cents` 6 (0.0579 USD) with a real `LedgerService` on `WallClock(WALL_NOW)`.
- **M-3:** 1 of 3 (WP-2 counts; WP-7 does not, because it was handed off; FLAGGED does not). The same on both pages.
- **CON-18 without seeds:**
  - ended 5 (WP-2, WP-5, WP-7, FLAGGED, ABANDONED); outcomes 2/5, 1/5, 1/5, 1/5;
  - M-13 0 of 1 (WP-7 missed; WP-5's safety promise has no due; FLAGGED's promise is still open);
  - `missed_promises` = [WP-7's case].

The tests assert these literals **and** the independent SQL below.

### 6.3 Eval scenarios (AC-5; each on a fresh store)

1. Both splits completed (`agent_version "agent-new"`).
2. Dev only: `held_out None`, `headline None`.
3. Stale: runs at `"agent-old"`, reader `current_agent_version "agent-new"`. The response carries both versions.
4. No run: both splits `None`, `headline None`.
5. Held-out incomplete only (`held_out_incomplete=True`, no completed held-out): `held_out None`, `headline None`.
6. A completed held-out (finished 18:30) plus a newer incomplete held-out (`"started_at": "2026-10-21T19:00:00+00:00"`,
   `"finished_at": None`): the completed run is shown.

### 6.4 Independent SQL (assertions only, through `tx.connection` or the journey's `journey.db.scalar`)

```sql
-- CON-18 ended / outcome (O = 'ai_resolved' | 'handed_off' | 'safety_reply' | 'abandoned')
SELECT COUNT(*) FROM conversations WHERE run_tag IN ('live','seed') AND outcome <> 'open';
SELECT COUNT(*) FROM conversations WHERE run_tag IN ('live','seed') AND outcome = ?;
-- M-3 denominator / numerator
SELECT COUNT(*) FROM conversations c WHERE c.run_tag = 'live' AND c.outcome <> 'open' AND EXISTS (SELECT 1 FROM turns t
  WHERE t.thread_id = c.thread_id AND t.plan_topic IN ('booking','membership','billing','warranty'));
-- numerator: the same plus  AND c.outcome = 'ai_resolved' AND NOT EXISTS (SELECT 1 FROM flags f JOIN cases k
--   ON k.case_ref = f.case_ref WHERE k.thread_id = c.thread_id)
-- cases by reason, seeds, promises
SELECT k.reason, COUNT(*) FROM cases k JOIN conversations c ON c.thread_id = k.thread_id
  WHERE c.run_tag IN ('live','seed') GROUP BY k.reason;
SELECT COUNT(*) FROM cases WHERE seed = 1;
SELECT status, COUNT(*) FROM promises WHERE due_at IS NOT NULL AND status IN ('kept','missed') GROUP BY status;
-- CON-19
SELECT COUNT(*) FROM conversations WHERE run_tag = 'live';
SELECT COUNT(*) FROM turns t JOIN conversations c ON c.thread_id = t.thread_id WHERE t.run_tag = 'live' AND c.run_tag = 'live';
-- failures: the same plus  AND t.outcome = 'degraded_handoff' AND t.degrade_reason IN ('model_error','tool_error','timeout')
-- trace sent: the same plus  AND t.trace_export = 'sent'
SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger WHERE recorded_at >= ? AND recorded_at < ?;   -- Chicago-day UTC bounds via db.format_wall
-- CON-20
SELECT summary_json FROM eval_runs WHERE suite = 'e2e' AND split = ? AND status = 'completed'
  ORDER BY finished_at DESC, started_at DESC LIMIT 1;
```

---

## 7. Checks

### 7.1 Commands (cheapest first; stop at the first red; `pytest -n 2` at most, via `uv run --with pytest-xdist`)

```bash
export UV_LINK_MODE=hardlink
P="src/meridian/services/metrics_reader.py src/meridian/adapters/sqlite/repos_metrics.py src/meridian/adapters/sqlite/repos_ops.py src/meridian/web/container.py tests/unit/services tests/integration tests/capture/test_cap6_reads.py tests/journeys/j10/test_aea_53.py"
uv run ruff check $P && uv run ruff format --check $P
uv run mypy                                                    # project config: strict over src, tests, eval
# while iterating: this ticket's tests
uv run pytest -q tests/unit/services/test_metrics_reader_repo.py tests/unit/services/test_metrics_reader.py \
  tests/unit/services/test_metrics_reader_alerts.py tests/unit/services/test_metrics_reader_stamps.py \
  tests/integration/test_reads_composition.py tests/capture/test_cap6_reads.py -rs
# once before the final commit: affected = ours + the importers of repos_ops, container, the reads routes and create_app
grep -rl "repos_ops\|meridian.web.container\|create_app\|metrics_reader\|repos_metrics\|get_metrics_reads" tests/ | sort   # review the list; add any file not covered below
uv run --with pytest-xdist pytest -n 2 -q tests/unit/services tests/integration tests/capture/test_cap6_reads.py \
  tests/adapters tests/unit/adapters tests/unit/ports tests/services tests/api tests/unit/web \
  tests/unit/test_import_direction.py tests/unit/test_skeleton.py -rs
uv run pytest -q tests/contract/test_openapi_server.py -k "getOwnerMetrics or getMonitoring or getLatestEval" -rs
# journeys (AEA addition): the affected journeys, then this ticket's journey with its record
uv run python -m tests.journeys.affected --base main
uv run pytest -m journey tests/journeys/j10/test_aea_53.py -rs --journey-record AEA-53
```

**Passing looks like:**
- ruff and format clean; mypy prints "Success: no issues found"; every listed test passes.
- The only allowed skips are those the existing suites already print, plus the J-10 chat-leg skip (`blocked-on
  AEA-51`).
- The contract runner's reads cases (`getOwnerMetrics`, `getMonitoring`, `getLatestEval`) **pass** on the real reader.
  A skip that reads `not bound: get_metrics_reads` or `not bound: demo_clock` means the hunk is not wired: fix it.
- `test_j10_read_pages_show_stored_rows` passes, and the record's level reads `integrated with a scripted model`.
- `tests/journeys/j10/test_aea_48.py::test_j10_read_pages_from_metrics_reader_on_db_copy` still skips. It is AEA-48's
  file; the seam audit retires it.
- No paid call (no `live` marker is selected).
- The full suite is **not** run: the container change touches only this ticket's hunk, and no shared fixture,
  settings field or dependency changes.

### 7.2 Tests the implementer writes with the code (the names are fixed)

**`tests/unit/services/test_metrics_reader_repo.py`** (store: `with temp_sqlite() as store`)
- `test_conversation_facts_filter_tags_topics_flags`: rows of every tag. Assert:
  - `conversations(("live",))` excludes eval, load and seed;
  - `topics` is distinct and sorted;
  - `flag_count` counts flags through the case join;
  - `conversations(())` and `conversations(("bogus",))` raise `ValueError`.
- `test_live_turns_need_live_turn_and_conversation`: a `live` turn on an `eval` conversation and an `eval` turn are
  both excluded.
- `test_cases_and_promises_join_and_order`: promises come back due ascending with nulls last; `due_at` is aware UTC;
  a `changed` row is returned too.
- `test_ops_repos_exposes_metrics`: in one unit of work, `tx.ops.metrics` is a `MetricsRepo` and
  `vars(tx.ops.metrics)["_conn"] is tx.connection`.

**`tests/unit/services/test_metrics_reader.py`.** Each test builds
`MetricsReader(store.uow, FixedClock(), WallClock(WALL_NOW), LedgerDouble(), AlertSettings(), "agent-test", 30.0)` and
validates every output with `OwnerMetricsResponse` / `MonitoringResponse` / `EvalResponse` from
`meridian.web.schemas.reads` (tests may import `web`).
- `test_units_and_scales` (AC-10), over `seed_j10_rows` plus both eval splits. Assert:
  - the units are a subset of `{"count", "ms", "share"}`;
  - every share is in [0, 1] and `== numerator / denominator` when its value is not None;
  - every `EvalMeasure.value` is in [0, 1];
  - M-24 has unit `count` with both a numerator and a denominator.
  Print the unit set and the min and max of the shares.
- `test_measure_keys_unique` (AC-11):
  - (id, label) pairs are unique across CON-18's five measure groups, across CON-19's health and correctness, and
    per run on CON-20;
  - CON-18 and CON-19 ids match `^M-\d+$`, except `scheduler_last_run` and `handoff_only`;
  - CON-20 ids equal the stored ids in order (pass-through, R-4).
  Print the duplicate count, which must be 0.
- `test_health_tiles_fixed_list` (AC-12): `[(t["id"], t["label"], t["unit"]) for t in health]` equals the literal
  seven-row list of §4.4, on an empty store and again after `seed_j10_rows`. Print it both times.
- `test_worked_pairs_wp2_wp5_wp7_counted` (the issue's example pairs):
  - WP-5's turn is in Turns, and its case is in `escalations_by_reason` as `reason_label(HandoffReason.SAFETY)` with
    value 1;
  - WP-7's case is in CON-18 `handoffs_by_reason` (`Refund request`) and in `missed_promises` (its reference);
  - WP-2's two turns are counted, and with a real `LedgerService(store.uow, wall_clock=WallClock(WALL_NOW),
    daily_cap_usd=30.0)` as the ledger, `today_cents == round(ledger.spend_today() * 100) == 6`.
- `test_never_recomputed_example_3_of_12` (the issue's input → output example): 12 live turns, 3 of them
  `degraded_handoff` / `model_error`. Assert Failures has `value 3, numerator 3, denominator 12`.
- `test_latency_null_reasons_and_nearest_rank`:
  - 0 turns give `No turns yet`;
  - 5 turns give `Not enough turns yet (fewer than 20)`;
  - 20 turns with known `server_ms` give p50 and p95 equal to the hand-computed nearest rank, and p95 equals
    `int(p95_nearest_rank([...]))` from `services.health`.
- `test_eval_projection_and_unreadable_summary` (D-10). Load scenario 1, then assert:
  - each split's keys are exactly `EVAL_RUN_KEYS`, and `suite`, `gates`, `headline` and `withheld` are absent;
  - each value equals the stored summary's value;
  - then overwrite one held-out row's `summary_json` through `tx.connection` (a test-only write) with `"[]"`, and
    then with a summary missing `"measures"`. Each time `held_out is None`, `headline is None`, and
    `caplog` holds exactly one `eval_summary_unreadable run_id=<id>` warning.

**`tests/unit/services/test_metrics_reader_alerts.py`** (AC-4)
- `test_alert_states_equal_stored_rows`. Append these rows:
  - `alert_fired` for `p95_latency_over_12_5s` with `value=3.0, threshold=12.5`;
  - `alert_fired` then `alert_cleared` for `spend_cap_reached`;
  - `alert_fired` for `scheduler_stale`.
  Then assert:
  - the alert types equal the six OpenAPI types in `ALERT_TYPES` order;
  - each state equals `latest_alert_states()[t].state`;
  - p95 is `firing`;
  - `scheduler_stale` is absent from `alerts`, while the `scheduler_last_run` tile is present.
- `test_alert_config_and_decision_lines`:
  - `alert_config == {"zero_traffic_after_hours": 4, "quiet_hours": {"start": "22:00", "end": "06:00", "timezone":
    "America/Chicago", "configurable": True}}`;
  - the spend line equals `render(TextId.MONITOR_SPEND_CAP, amount="$30")`;
  - no decision line contains "80%";
  - the latency line contains "12.5 s", and the failure line contains "2%".
- `test_pages_answer_with_evaluator_patched`: `monkeypatch.setattr(AlertEvaluator, "evaluate", raiser)`. All three
  methods return and validate.

**`tests/unit/services/test_metrics_reader_stamps.py`** (AC-8)
- `test_time_stamps_from_injected_clocks`: CON-19 `as_of == WALL_NOW` and `demo_now == FixedClock(DEMO_START +
  timedelta(hours=3)).now()` (build that clock as `FixedClock().advanced(timedelta(hours=3))`); CON-18 `as_of` equals
  the demo time; all values are aware.
- `test_spend_cents_and_reset_time`:
  - `LedgerDouble(spent=6.12)` gives `today_cents 612`, `cap_cents 3000` and
    `resets_at == datetime(2026, 10, 22, 0, 0, tzinfo=CHI)`;
  - a second wall time, `datetime(2026, 11, 1, 12, 0, tzinfo=UTC)` (the DST day), gives
    `datetime(2026, 11, 2, 0, 0, tzinfo=CHI)`.
- `test_handoff_only_from_open_circuit_or_cap`: `circuits=("anthropic",)` gives 1; `capped=True` gives 1; neither
  gives 0.
- `test_real_ledger_spend_today`: a real `LedgerService` over the store. Record two calls "today" and one at Chicago
  yesterday 23:30 (move the `WallClock` between records). `today_cents` equals
  `round(100 × the SQL sum over today's UTC bounds)`.

**`tests/integration/test_reads_composition.py`.** It uses `container_app`, `login_token` and `switch` from
`tests.api.staff_session_support`; `make_client`, `error_body`, `assert_matches` and `cookie_header` from
`tests.api.web_shell_support`; and `OPERATIONS`, `get_read` from `tests.api.reads_support`.
- `test_reader_bound_and_access` (AC-1), inside `with make_client(h.app) as client`:
  - `isinstance(h.app.state.container.get(METRICS_READS), MetricsReader)`;
  - with no cookie, all three paths give 401 `UNAUTHENTICATED`;
  - customer: CON-18 403 `ROLE_NOT_ALLOWED`; CON-19 and CON-20 200;
  - representative: the same as customer;
  - supervisor and owner: all 200;
  - `assert_matches(response, op)` on every response; print the role → status table.
- `test_reader_never_recomputes` (AC-7), in two parts.
  - *(a) Store level:*
    1. `seed_j10_rows`.
    2. A `RecordingUow` wraps `store.uow` and records `(write, exclusive)` for every call. Both the reader and a real
       `LedgerService` use it.
    3. Monkeypatch to a raiser every public function (only `inspect.isfunction` objects whose `__module__` equals the
       module) of `meridian.gates.gate`, `meridian.gates.rules`, `meridian.checks`, `meridian.policy.handoff`,
       `meridian.policy.escalation` and `meridian.policy.booking`, and every public method of
       `meridian.agent.gateway.ModelGateway`.
    4. Call the three methods.
    5. Assert every recorded call is `(False, False)`; the M-18 `Abandoned` numerator == 1 == the SQL count of
       `outcome = 'abandoned'` (STALE_OPEN is not counted); the M-3 numerator is 1 (FLAGGED is dropped).
  - *(b) App level:* `container_app`; log in; switch to owner; apply the same patches **after** the lifespan has
    started; the three GETs answer 200.

**`tests/capture/test_cap6_reads.py`.** AC-2, AC-3 and AC-5 run at store level. AC-6, AC-13 and AC-14 run on
`container_app` over HTTP: seed through `h.uow` after entering the client, and get the ledger with
`h.app.state.container.get(Key[Any]("ledger"))`.
- `test_owner_metrics_equal_stored_counts` (AC-2): `seed_j10_rows(with_seed=True)`. Assert:
  - each measure's numerator and denominator equal §6.4; `case_refs` equal the refs from SQL;
  - `kind == "estimate"` only on M-3; the north-star link path is `/eval`;
  - `seeds_included is True` and `seed_count == 4 ==` the SQL count;
  - then, with an empty-store reader: M-3, M-13 and handoffs have `value None` and the §4.4 null reasons, and
    `outcomes == []`.
- `test_monitoring_equals_stored_counts` (AC-3): every tile and field against §6.4 and §6.2; eval, load and seed rows
  are excluded; `last_restart.at` equals the stored `at_wall`; `health` and `correctness` share no (id, label) pair.
- `test_latest_eval_per_split` (AC-5): the six scenarios of §6.3, each with a fresh store. Assert:
  - each shown split equals `{k: stored[k] for k in EVAL_RUN_KEYS}` from §6.4's `summary_json`;
  - the headline equals the held-out summary's stored `headline`, or None;
  - the stale scenario carries both versions; the incomplete scenarios never show the incomplete run;
  - every measure id equals the stored id and matches `^[ME]-\d+(:[a-z_]+)?$`;
  - every `target` is None or a string, and no target text appears in a `value`, `numerator` or `denominator`.
  Print the response per scenario.
- `test_no_pii_codes_cards_or_trace_links` (AC-6):
  1. Seed the J-10 rows.
  2. Put the sentinels into: WP-2 messages (`tx.core.messages.append(thread, "customer", f"… {name} {phone} {code}
     {card}", DEMO_NOW)`); a turn's `response` and `trace_id` (through `add_turn(..., response=…, trace_id=…)`); and a
     dev result's `failing_quote` (`write_eval_reports(..., quote=…)`), keeping the summary's `redacted_summary` clean.
  3. As owner, GET the three pages.
  4. Assert: CON-19 and CON-20 contain no sentinel; no body contains the `trace_id` sentinel, `"http"` or `"/trace"`;
     no JSON key anywhere in the three bodies contains `"trace_id"` or `"trace_url"` (walk the dict). CON-18 holds no
     sentinel.
  5. Print the hit count, which must be 0.
  *Do not* assert on the word "langfuse": the stored `MONITOR_TRACE_EXPORT` decision line names the Langfuse server.
- `test_monitoring_says_export_off_and_no_outbound` (AC-13). Use the default settings (no Langfuse keys). Assert the
  container's `Key("trace")` object is a `NullTraceSink`. Every live turn is `off`. Store `alert_fired` for
  `trace_export_failed`. Then, under `with socket_guard() as guard` (from `tests.journeys.support.server`):
  - the three pages answer 200;
  - `trace_export == f"sent 0 of {N} turns"`, with N from SQL;
  - the alert is `firing`, as stored;
  - `guard.blocked == []`.
- `test_no_key_values_or_message_text` (AC-14):
  1. Generate sentinels `s1…s6` with `rand_word`.
  2. Patch the settings: `real = staff_session_support.make_settings`, then `monkeypatch.setattr(staff_session_support,
     "make_settings", lambda tmp_path, **kw: real(tmp_path, anthropic_api_key=s1, openrouter_api_key=s2,
     demo_password=s3, eval_key=s4, langfuse_public_key=s5, langfuse_secret_key=s6, **kw))`, **before** calling
     `container_app`. Leave `langfuse_base_url` unset, so no sink builds.
  3. Store a sentinel phrase in customer messages and turn responses.
  4. `caplog.set_level(logging.DEBUG)`, then `caplog.clear()` right before the three GETs.
  5. Assert neither the bodies nor `app_log_text(caplog)` contain any sentinel, and CON-20's `dev_failures` equal the
     stored summary's, field for field.

**`tests/journeys/j10/test_aea_53.py`** (`pytestmark = pytest.mark.journey`; the module docstring states the level and
the blocked steps; `J10 = "J-10"`)
- `test_j10_read_pages_show_stored_rows(journey)`:
  - Step `"seed stored rows"`, with `journey.step(J10, "seed stored rows", needs=("uow_factory", "ledger"))`:
    - `seed_j10_rows(journey.container.get(UOW_FACTORY), journey.container.get(Key[Any]("ledger")),
      with_seed=False)`. The harness's own first-boot seed already loaded the 4 seeds once AEA-29 merged.
    - Also write the eval reports into a temp dir and load them with
      `load_eval_reports(dir, journey.container.get(UOW_FACTORY))`.
  - Step `"owner reads the three pages"`, with `needs=("login_sessions", "staff_access", "demo_clock",
    "metrics_reads")` and `operations=("login", "switchRole", "getOwnerMetrics", "getMonitoring", "getLatestEval")`:
    - `signed = journey.login()`;
    - `signed.client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "owner"})`;
    - then the three GETs through `signed.client.call(...)`, each validated against the OpenAPI.
    - Assert what the user sees: labels, denominators, units in {count, ms, share}, each share in [0, 1] and equal to
      n/d.
    - Assert what is stored with D-11 (Step 7): get the bodies and `after` from `_stable_read`, then check that each
      page count equals its `after` entry.
    - Do not compare alert states, `as_of`, `demo_now` or the `scheduler_last_run` value (D-11).
- `test_j10_worked_pairs_driven_through_chat`: mark it `@pytest.mark.skip(reason="blocked-on AEA-51: WP-2, WP-5 and
  WP-7 through the chat API need the graph (run_graph) and AEA-51's scripts; see the AEA-53 journey record")`. Its docstring lists the steps: drive the three pairs, then re-run the page
  reads and the stored-count equalities.

**Existing tests that must stay green:**
- `tests/unit/web/test_container.py` (hunk docstring and order);
- `tests/unit/test_import_direction.py`, `tests/unit/adapters/sqlite/test_uow.py`, `tests/adapters/test_repos_ops.py`;
- `tests/unit/adapters/test_repo_shells.py` (the `OpsRepos` constructor signature), `tests/unit/ports/test_protocol_shapes.py`;
- `tests/services/test_alerts.py`, `tests/services/test_health_capture.py`, `tests/services/test_load_eval_reports.py`;
- `tests/api/test_reads_routes.py`, `tests/api/test_reads_router.py`, `tests/api/test_contract_cases_reads.py`;
- `tests/contract/test_openapi_server.py` (the three reads' cases now run, and must pass);
- `tests/journeys/j10/test_aea_48.py`, `tests/journeys/j10/test_aea_32.py`;
- every `tests/api` test built on `container_app`.

### 7.3 Commits (factory mode: your own branch only; never push; never `git add -A`)

```bash
git add src/meridian/services/metrics_reader.py src/meridian/adapters/sqlite/repos_metrics.py \
  src/meridian/adapters/sqlite/repos_ops.py src/meridian/web/container.py \
  tests/unit/services/test_metrics_reader_rows.py tests/unit/services/test_metrics_reader_repo.py \
  tests/unit/services/test_metrics_reader.py tests/unit/services/test_metrics_reader_alerts.py \
  tests/unit/services/test_metrics_reader_stamps.py tests/integration/test_reads_composition.py \
  tests/capture/test_cap6_reads.py tests/journeys/j10/test_aea_53.py
git commit -m "AEA-53: metrics reader behind CON-18…CON-20 (stored counts, never recomputed)

<what and the test result line>

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
git add docs/testing/journeys/<date>-AEA-53.md docs/plans/ux-join/AEA-53-con19-health-tiles.md \
  .claude/reference/area-map.md .claude/state/icm-progress.md
git commit -m "AEA-53: journey record, CON-19 tile note, area-map and ICM rows

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
git diff --name-only main...HEAD      # must list exactly the files above (AC-15)
```

### 7.4 Must not

- Do not edit any file outside section 2. That includes `routes/reads.py`, `schemas/reads.py`, `web/deps.py`,
  `services/health.py`, the rest of `repos_ops.py`, any writer, `tests/journeys/support/`, `tests/capture/conftest.py`
  (do not create it), other journey files, `eval/**`, the OpenAPI, `apps/web/**`, `docs/ux/**` and DO-7.
- Do not run SQL in `src/` outside `repos_metrics.py`, and do not use `tx.connection` in production code.
- Do not import `meridian.web` from `services/`. Do not call `AlertEvaluator`, a gate, `checks`, a policy rule or a
  model.
- Do not open a write unit of work.
- Do not re-apply the 30-minute rule, compare a promise due with a clock, or re-score an eval run.
- Do not rename, rewrite or strip CON-20 measure ids, and do not pick the headline out of `measures`.
- Do not round shares. Do not add keys that are not in the OpenAPI. Do not add a stale-label field.
- Do not copy `REASON_LABEL` or `LIFECYCLE_WORD`.
- No literal phone, card, code or secret in any file. Do not print sentinel values. Do not read `.env`.
- No new dependency. No paid model call. Do not bind 4019 or 5184. No full suite (section 7.1). No push.

---

## 8. Risks and requests

- **R-1, a read-only repository seam: closed, granted as option A (DV-1).**
  - The reader must count conversations, turns, cases, promises and flags across every thread. No existing repository
    method does that. Production code may not use `tx.connection` (the `UnitOfWork` Protocol has no such member, and
    DO-3 §2 forbids it).
  - Step 1 adds `MetricsRepo` and the 3-line hook. The hook is the only edit to `repos_ops.py`.
- **R-2, AEA-29: closed (merged, `ef561fc`).** The reader imports `reason_label` and `LIFECYCLE_WORD` from
  `services/_case_rules.py`, the one owner of display words. Three modules besides `cases.py` already import it. If a
  reviewer still objects to the underscore module, the fix is an AEA-29 re-export from `services/cases.py`, never a
  copy here.
- **R-3, J-10 reaches `integrated with a scripted model` for the read leg only.**
  - AEA-30 is merged, so login on the harness works, and the page reads run on the real server and DB copy.
  - Driving WP-2, WP-5 and WP-7 through the chat needs AEA-51 (the graph and `run_graph`). That leg is a declared skip,
    never a pass. Its scripts belong to AEA-51 (integrated-journeys §6).
  - The record names AEA-51 under *Blocked by* (rule 6). The wave-3 seam audit should re-run J-10 once AEA-51 lands.
  - The scheduler tick in the live server is handled by D-11. It is not a reason to skip.
- **R-4, CON-20 measure ids: a cross-ticket conflict the orchestrator should settle with AEA-24 (not blocking this
  plan).**
  - STF-18 and AC-5 say CON-20 ids are DO-5 `E-n`, but DO-5's E-1…E-8 name eval *runs*, not measures. DO-7, this
    ticket's own *Evaluation* section ("M-1 (held-out headline), M-2 (dev, labelled), M-4 …") and AEA-24's built
    `report.py` all use `M-n`.
  - AEA-24 also writes the topic split into the id (`M-1:booking`) and one `E-1:hard` row, while AC-11 says "the split
    is named in the label and the id stays the registry's M-n".
  - The reader passes ids through unchanged, which is STF-18's own consequence for AEA-53 ("ids per DO-7/DO-5"; the
    route "passes ids through unchanged").
  - **Recommendation:** record an STF-18 erratum ("CON-20 ids are DO-7 `M-n`") and ask AEA-24 to keep the id `M-1`
    with the topic in the label only. That would make AC-5 and AC-11 literally true on stored data. Either way, this
    ticket's code is unchanged.
- **R-5, collisions.**
  - `web/container.py`: only `register_metrics_reader`'s body and docstring change. Open tickets (AEA-45, AEA-51)
    edit other functions, so a textual merge is likely clean.
  - `repos_ops.py`: three lines plus one import (DV-1). The orchestrator found no in-flight branch touching it.
  - `area-map.md` and `icm-progress.md`: every branch adds or edits its own row. Resolve any conflict by keeping
    every row.
  - `tests/capture/conftest.py` exists on main (AEA-50). Do not edit it. If a later CAP ticket appends a hook first,
    re-run `tests/capture/test_cap6_reads.py` after rebasing.
- **R-6, the monitoring window (D-3) and latency segmentation** are recorded as limits, not decided against a source.
  DO-7 leaves M-22 and M-23's live windows open, and the page shows all stored live rows since the reset.
- **R-7, handoff-only mode as tile 7 (D-5).** The OpenAPI has no field for it, and a tile is the only place inside the
  signed contract. No contract change is needed.
- **R-8, AEA-59's contract runner now runs the three reads' 200 cases on the real reader.** AEA-30 is merged, so
  login works in the runner, and this ticket's hunk removes the last `not bound` skip. The reader's empty-store
  output must validate. `test_health_tiles_fixed_list` and the empty-store part of AC-2 prove that it does, and
  §7.1 runs `tests/contract/test_openapi_server.py -k` on the three operations.

---

## 9. Readiness

**READY.** Nothing blocks the build:
1. AEA-29, AEA-30, AEA-24, AEA-26, AEA-32, AEA-44 and AEA-48 are merged on `main` at `3725c90`. Every import the
   reader and its tests need exists, with the names this plan copies.
2. The R-1 grant is recorded (DV-1).

Siblings outside `main` are reached by doubles or declared skips only. The J-10 chat leg (AEA-51) is a declared skip
with its blocker named (DV-3, R-3). It is not a build blocker.

No product decision, no signed-contract change and no answer different from D-4…D-15 is needed. R-4 is a naming
conflict between two of our own records, for the orchestrator to settle with AEA-24. This plan's code does not depend
on its outcome. Gates: none (no human, paid or live gate).
