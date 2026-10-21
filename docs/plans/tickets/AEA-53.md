## [AEA-53] reads: metrics reader

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

`services/metrics_reader.py` (DO-3 §4.4: "Serve stored measures without recomputing outcomes"), exactly as cases.md §9
signs it: `MetricsReader(uow, demo_clock, wall_clock, ledger, settings: AlertSettings, current_agent_version: str,
daily_cap_usd: float)` with `owner_metrics()`, `monitoring()` and `latest_eval()`, each returning `Mapping[str, object]`
with the OpenAPI field names. It satisfies web.md §4's `MetricsReads` Protocol structurally (services never import
`web/`), and this issue's own `register_<area>()` hunk binds it to `get_metrics_reads()` (MC-6), so AEA-48's
`routes/reads.py` serves the three read pages at the real API. Its own tests validate its output with AEA-48's
`web/schemas/reads.py` models (staff.md §9).

- **CON-18** `GET /api/staff/owner-metrics` (SCR-9, owner and supervisor): per measure `id` (the DO-7 `M-n`, STF-18),
  label, numerator, denominator, unit, value, `null_reason`, `kind` (`measured` or `estimate`), `case_refs`; `as_of` from
  the **demo** clock (STF-22); `seeds_included` and `seed_count` (4 after first boot, cases.md §7); handoffs by reason;
  missed promises. `in_scope_correct_resolution` is the **M-3 estimate** from live chats; `measured_north_star_link` points
  to `/eval` (M-1 comes only from the held-out run).
- **CON-19** `GET /api/monitoring` (SCR-10, any signed-in role): `as_of` from the **wall** clock and `demo_now` from the
  demo clock; health tiles (volume, failures with share, latency p50 and p95, the `scheduler_last_run` tile "Overdue job
  last ran n min ago" from `cases.job_runs.latest()`, CAS-30); spend against the cap (`cap_cents` = `daily_cap_usd` × 100,
  `today_cents` = `ledger.spend_today()` × 100) with `resets_at` at the next America/Chicago midnight; handoff-only mode
  from `ledger.models_disabled()` and `ledger.open_circuits()`; a **separate** correctness group (the M-3 estimate,
  escalations by reason); alerts as decision lines, each `firing` or `quiet`, read from `ops.health.latest_alert_states()`;
  the alert settings from `AlertSettings`; the last health-check restart; traces exported "n of N turns".
- **CON-20** `GET /api/eval/latest` (SCR-11, any signed-in role): per split (dev, sealed held-out) the latest **completed**
  run from `ops.eval.latest_completed(suite, split)` and its stored `summary_json` (run ID, date, agent version, size, mix,
  measures as "n of N" with min and max over repeats; `Measure.id` the DO-5 `E-n`); `headline` from the held-out split only;
  `current_agent_version`; the dev label; redacted dev failures.

**"Never recomputed" in practice.** Input: 12 stored `turns` rows with `run_tag = 'live'`, 3 with
`outcome = degraded_handoff` and `degrade_reason = model_error`. Process: the reader counts those stored fields. Output:
failures "3 of 12 turns". It never re-runs a gate, a check or a model, never re-judges whether a conversation was
resolved, never applies an alert line (AEA-32's `AlertEvaluator` does, cases.md §8) and never applies the 30-minute end
rule (AEA-30's sweep writes `abandoned`, CAS-29); it only counts and divides what the writers stored (DO-6 WF-6: "computes
none of them on read").

**Example pairs behind the seeded rows:** WP-5 (a safety turn and its P0 case: counted in volume and escalations by
reason), WP-7 (a refund handoff with its P3 promise: handoffs by reason; a missed promise once its due passes), WP-2 (a
verified account read: a turn with model calls and spend rows).

**Seams this issue proves (double in the consumer's own tests → real object wired here):**

| # | Consumer (ticket) | Double it was built against | Real object (ticket) | Proven by |
|---|---|---|---|---|
| 1 | `routes/reads.py` CON-18…CON-20 (48) | `get_metrics_reads` override | `MetricsReader` (this issue) via `web/deps.py` (23) | AC-1 |
| 2 | CON-18 access check (48) | `get_staff_access` override | `StaffSessionStore.actor_for` (44) | AC-1 |
| 3 | `MetricsReader` | — | rows written by the real writers' repositories: `spend_ledger` through `LedgerService` (26); cases and promises (29, `repos_cases`); `health_events`, `deploy_records`, `eval_runs` (32, `repos_ops`); `conversations`, `turns`, `job_runs` (10) | AC-2…AC-8 |

User stories closed: **US-24** (the owner knows whether the AI cuts load without hurting customers), **US-27** (the
reviewer sees health and the evaluation behind the containment number). PRD **R-35** (monitoring reads stored data;
health apart from correctness), **R-38**, **R-39** (eval report with denominators), **R-32** (owner view read-only).

### Source

- PRD R-32, R-35, R-38, R-39; framing §2 (north star, health list, decision lines).
- stage7/cases.md §8 (`AlertSettings`, `AlertType`, `ops.health.latest_alert_states`, `ops.eval.latest_completed`,
  `load_eval_reports`), §9 (`MetricsReader`, the decision of record); stage7/web.md §4 (`MetricsReads`,
  `get_metrics_reads`, `get_wall_clock`); stage7/staff.md §9 (route validation, `Measure.id`), §10 (time sources);
  stage7/models.md §6 (`LedgerService.spend_today`, `models_disabled`, `open_circuits`; `SpendLimits.daily_cap_usd`);
  stage7/data.md §6 (eval report fields).
- Decision ledgers (`docs/plans/7b-decisions/`): CAS-22, CAS-25, CAS-27, CAS-29, CAS-30; STF-17, STF-18, STF-22; DAT-14;
  merge MC-5, MC-6, MC-20, MC-22, MC-24.
- UI contracts (read only): `UI_CONTRACTS.md` CON-18, CON-19, CON-20; `ui-contracts.openapi.yaml`
  `/api/staff/owner-metrics`, `/api/monitoring`, `/api/eval/latest` (incl. the `failure_rate_over_2pct` and
  `trace_export_failed` alert types, UXR-23); `api-con-mapping.md` CON-18…CON-20 rows.
- DO-7 `key-metrics-registry.md`: every row M-1…M-29, *Numerators, readers, labels*, *Where this registry and other
  documents differ* (no 80% spend alert; 12.5 s; M-3 is an estimate; the decided definitions).
- DO-6: WF-6 row; *Two questions, kept apart*; *Missing instrumentation*; *Alerts on the monitoring page*; **CAP-6**.
- DO-5 *What the R-39 report contains*; *Development and held-out separation* (the headline is held-out only).
- DO-3 §4.4 (`services/metrics_reader.py`), §8 (A10b, wave 3 because CON-18 needs `require_staff`).
- UX ↔ backend join: `docs/plans/ux-join/backend-amendments.md` AEA-53-1…4 (shell audit A1, A3, A4).
- Project rule `.claude/rules/integrated-journeys.md`; slice plan row AEA-53 and Amendment 1 (J-10); collision map
  `web/container.py` (this issue fills only its own function), `tests/capture/` (CAP-6 is this issue's).
- **Brief check:** serves "Add observability so the business can see how the agent is performing after launch: volume,
  containment, escalations, failures, latency" and "Show the numbers, not just the claim"; touches nothing out of scope (no
  push alerts, R-35); weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] The real `MetricsReader` is bound to `get_metrics_reads()` at `create_app()`, and CON-18 uses the real role check: demo owner and supervisor read it; a representative or customer role gets 403 `ROLE_NOT_ALLOWED`; no session gets 401 `UNAUTHENTICATED`; CON-19 and CON-20 answer any signed-in role; every response passes `assert_response_matches` — verify: `tests/integration/test_reads_composition.py::test_reader_bound_and_access` — evidence: the bound class; status codes per role.
- [ ] AC-2 [capture] **CAP-6, WF-6, CON-18:** over rows written through the real writers' repositories (seam row 3), every owner measure's numerator and denominator equal a direct SQL count over the stored records, with `case_refs` listing exactly the cases behind it; each `id` is a DO-7 `M-n`; the live estimate has `kind: estimate` and the measured-north-star link; seed cases are counted and named (`seeds_included`, `seed_count` 4); a zero denominator gives `null_reason`, never 0% — verify: `tests/capture/test_cap6_reads.py::test_owner_metrics_equal_stored_counts` — evidence: per-measure equality with the independent SQL count.
- [ ] AC-3 [capture] **CAP-6, WF-6, CON-19:** volume (M-22: live conversations, turns, handoffs by reason), failures (M-24: `degraded_handoff` with `model_error`, `tool_error` or `timeout`), latency p50 and p95 (M-23) from stored `turns.server_ms` with "Not enough turns yet (fewer than 20)" as the null reason below `min_turns` 20, spend today (M-26) on the America/Chicago day, last health-check restart (M-28), traces exported "n of N turns" (M-29), the `scheduler_last_run` tile — all equal direct counts over the stored rows; conversations tagged `eval`, `load` or `seed` are excluded from live counts; health and correctness are separate groups — verify: `tests/capture/test_cap6_reads.py::test_monitoring_equals_stored_counts` — evidence: per-tile equality; tag exclusion.
- [ ] AC-4 [invariant] **OBS-40, OBS-31, WF-6 (CON-19 alerts):** Alerts are shown, never applied: each `MonitorAlert` state equals `ops.health.latest_alert_states()` for its type, so a stored `firing` row whose value is under its threshold still shows `firing`; `alert_config` equals `AlertSettings` (12.5 s, 2%, 4 h zero traffic outside 22:00–06:00 Chicago) and the spend line shows `daily_cap_usd` (no 80% alert, DO-7 difference 2); `scheduler_stale` appears only as the health tile, never as a `MonitorAlert` (CAS-30); with the `AlertEvaluator` patched to raise, all three pages still answer — verify: `tests/unit/services/test_metrics_reader_alerts.py` — evidence: state per type equal to the stored row; config fields; pages answer with the patch.
- [ ] AC-5 [capture] **CAP-6, WF-6, CON-20:** with eval-result rows as `load_eval_reports` stores them, each split shows its latest **completed** run (run ID, date, agent version, size, mix, measures as "n of N" with min and max, `Measure.id` a DO-5 `E-n`); the `headline` comes from the held-out split only and is absent when there is no held-out run ("No held-out run yet", dev labelled); a run whose agent version differs from `current_agent_version` carries the stale label; an `eval_run` marked `incomplete` is never reported as a result; no target value appears as a result field — verify: `tests/capture/test_cap6_reads.py::test_latest_eval_per_split` — evidence: response per scenario (both splits, dev only, stale, no run, incomplete).
- [ ] AC-6 [negative] **CAP-6 forbidden, WF-6:** after seeding conversations, messages and eval failure examples that hold sentinel names, phone numbers, code-like digits and card-like numbers (generated at test time), the CON-19 and CON-20 bodies contain none of them and no trace link or trace id; CON-18 carries case references and no PII — verify: `tests/capture/test_cap6_reads.py::test_no_pii_codes_cards_or_trace_links` — evidence: 0 sentinel hits; no `trace` URL or id field.
- [ ] AC-7 [invariant] The reader never recomputes an outcome: it opens read-only units of work only, and with the gates, `checks.py`, the policy modules and every model port patched to raise, all three pages still answer; it reads `conversations.outcome` as stored (an `abandoned` conversation counts for M-18 only because AEA-30's sweep stored it, CAS-29) and drops conversations a staff flag marks wrong from M-3's numerator — verify: `tests/integration/test_reads_composition.py::test_reader_never_recomputes` — evidence: pages answer with the patches; no write transaction opened; M-18 and M-3 equal the stored-field counts.
- [ ] AC-8 [invariant] Time and spend stamps (STF-22, MC-5, MC-20, MC-22): CON-19 `as_of` equals the injected wall clock and `demo_now` the demo clock; CON-18 `as_of` equals the demo clock; `spend.cap_cents` is 3000 from `daily_cap_usd` 30, `today_cents` equals `ledger.spend_today()` × 100, `resets_at` is the next Chicago midnight; with an open provider circuit the page shows handoff-only mode — verify: `tests/unit/services/test_metrics_reader_stamps.py` (injected clocks and ledger double) — evidence: each field equal to its source.
- [ ] AC-9 [journey] **J-10** (slice plan Amendment 1, landed here): `tests/journeys/j10/test_aea_53.py` drives WP-2, WP-5 and WP-7 through the real server on AEA-57's harness, then reads CON-18, CON-19 and CON-20 and asserts the pages show the stored values with their labels and denominators (what the user sees) and that each equals a direct count over the run's stored rows (what was stored), and that every unit on the three pages is `count`, `ms` or `share`, with each share's value between 0 and 1 and equal to its numerator over its denominator (AEA-53-4) — verify: `uv run pytest -m journey tests/journeys/j10/test_aea_53.py` plus `docs/testing/journeys/<date>-AEA-53.md` (integrated-journeys §4) — evidence: pass at level `integrated with a scripted model`, or the record's Blocked-by field naming AEA-57 if its harness has not merged.
- [ ] AC-10 [invariant] One unit vocabulary on all three reads (AEA-53-1): every `Measure.unit` and `Tile.unit` is `count`, `ms` or `share`; a `share` value is a 0–1 fraction, never 0–100; every `EvalMeasure.value` is a 0–1 ratio; M-24 failures go out as a count with numerator and denominator (as the OpenAPI example does), never as "per 100 turns"; and every mapping passes AEA-48's `web/schemas/reads.py` models — verify: `tests/unit/services/test_metrics_reader.py::test_units_and_scales` over the J-10 run's rows — evidence: the set of units printed is a subset of {count, ms, share}; the minimum and maximum of every share value lie in [0, 1].
- [ ] AC-11 [invariant] Measures can be told apart (AEA-53-2): (`id`, `label`) pairs are unique within each of CON-18, CON-19 and CON-20; where DO-7 splits one M-n (M-27 per reason, M-1 per topic) the split is named in the `label` and the `id` stays the registry's M-n (STF-18) — verify: `tests/unit/services/test_metrics_reader.py::test_measure_keys_unique` — evidence: 0 duplicate pairs across the three responses.
- [ ] AC-12 [invariant] The CON-19 health tiles are a fixed, listed set (AEA-53-3): the plan lists each tile's position, label and unit (volume, failures, latency p50, latency p95, `scheduler_last_run`, and any other), the test asserts exactly that list in that order on an empty database and after the J-10 run, and the list is copied as one note into `docs/plans/ux-join/` so the UX session keys SCR-10's empty state on the volume tile — verify: `tests/unit/services/test_metrics_reader.py::test_health_tiles_fixed_list` — evidence: the list printed twice, equal.
- [ ] AC-13 [capture] **CAP-6, WF-6:** the pages work with trace export off and nothing leaves (OBS-18, OBS-29): with no Langfuse keys in the settings and every stored live turn's `trace_export` `off`, CON-19's `trace_export` reports 0 exported of N turns (N the stored live-turn count) and the `trace_export_failed` alert shows its stored state; all three pages answer 200 under a socket guard that records 0 outbound connection attempts — verify: `tests/capture/test_cap6_reads.py::test_monitoring_says_export_off_and_no_outbound` — evidence: the `trace_export` value and N; the alert state; 0 connection attempts.
- [ ] AC-14 [negative] **WF-6:** keys and message text stay off the pages (OBS-24, OBS-26): with sentinel provider, Langfuse and eval keys and a sentinel demo password in the test settings, and a sentinel phrase stored in customer messages and agent replies, the CON-18, CON-19 and CON-20 bodies and every log record of the three reads contain none of them; CON-20's dev failure examples equal the stored redacted examples field for field — verify: `tests/capture/test_cap6_reads.py::test_no_key_values_or_message_text` — evidence: 0 sentinel hits per body and in the logs; the examples equal the stored ones.
- [ ] AC-15 [regression/context] Context updated in the same change: area-map A10b row (planned → actual with the commit); `.claude/state/icm-progress.md` routes-verified row; DO-7's M-26 day noted as America/Chicago if DO-7's owner has not already (code-design C-12); the CON-19 tile-list note in `docs/plans/ux-join/` (AC-12) — verify: `git diff --name-only` — evidence: those files only, beside this issue's owned files.

### Observability

- Responsibilities: **WF-6** (read-only measure pages CON-18…CON-20): a `request` record per page read with `request_id`;
  page reads are counted, never recomputed into outcomes. Surfaces DO-6's missing-instrumentation signals that CON-19
  carries: trace export "n of N turns", the last health-check restart, "overdue job last ran", the zero-traffic and failure
  alerts as stored; reports an `incomplete` eval run as not a result. Redacted by construction: aggregates only, no trace
  links.
- Capture evidence: AC-2 (CON-18), AC-3 (CON-19), AC-5 (CON-20), AC-13 (export off, no outbound call), AC-6 and AC-14
  (forbidden values), all on WF-6.

### Evaluation

- Checks: CON-20 shows the R-39 report as the harness stored it: M-1 (held-out headline), M-2 (dev, labelled), M-4, M-5,
  M-6, M-7, M-8, M-10, M-11, M-12, M-14…M-17, M-19…M-21, each "n of N" per split with repeats' spread (AC-5). The
  held-out/dev separation (DO-5) is enforced on read: the headline is never a dev number.
- Expected-answer authority: the eval-result records written by the frozen harness (AEA-24) and loaded by
  `load_eval_reports` (AEA-32) are the only source of correctness numbers (DO-5 *Scoring*); the reader adds no judgement.
  Live outcome numbers are labelled estimates (DO-7 difference 3).

### Metrics

- References: **M-1…M-29** as their registry rows assign them to a page: CON-18 (owner) M-3, M-13, M-18 and handoffs by
  reason; CON-19 (monitoring) M-22, M-23, M-24, M-26, M-28, M-29 and the M-3 estimate; CON-20 (evaluation) the R-39 list
  above. **M-9, M-25 and M-27** are served by no page here (M-27 is the supervisor view, CON-17, AEA-52; M-9 and M-25 are
  builders' and operators' numbers) and stay computable from the stored records.
- Acceptance conditions: every number on the three pages equals a direct count over the stored records (AC-2, AC-3, AC-5)
  with its denominator and segment; thresholds appear only as labelled alert settings (12.5 s, 2%, $30, 4 h), never as
  results.

### Blocked by

- Slice plan row AEA-53: AEA-26 (spend ledger), AEA-29 (cases and promises), AEA-32 (`repos_ops`: health events, alert
  states, deploy records, eval tables), AEA-44 (`require_staff` for CON-18), AEA-48 (the reads routes and schemas).

### Agent handoff

- Area / owner: A10b Reads (DO-3 §8). Owns `services/metrics_reader.py`, its `register_<area>()` hunk in
  `web/container.py`, `tests/unit/services/test_metrics_reader*.py`, `tests/integration/test_reads_composition.py`,
  `tests/capture/test_cap6_reads.py`, `tests/journeys/j10/test_aea_53.py` and its journey evidence record, and the one
  CON-19 tile-list note it adds to `docs/plans/ux-join/` (AC-12; it edits no other file there).
- Contracts and shared surfaces: consumes the stored records through `UnitOfWork` read methods (cases.md §1.2, §8),
  `LedgerService` (models.md §6), `AlertSettings` and `limits.spend.daily_cap_usd` from the container; produces the reader
  behind AEA-48's routes and the numbers AEA-55 renders. **Must not edit** `routes/reads.py`, `schemas/reads.py` (AEA-48),
  `web/deps.py` (AEA-23), `services/health.py` (AEA-32), any writer or `tests/journeys/support/` (AEA-57). A record a page
  needs that no writer stores is a gap to report, never a value to derive on read.
- Scope boundary / refusal: no recomputation of outcomes; no alert line applied on read; no push alerts (R-35, Q-045 = A);
  no new alert line or threshold (no 80% spend warning: DO-7 difference 2). The end-to-end check that pages equal the counts
  left by real WF-1/WF-2 flows through the browser (DO-6 CAP-6 "after CAP-1 to CAP-3") is AEA-55's AC-8; AC-9 here proves it
  over HTTP.
- Wave and gates: wave 3; no human gate. The wave-3 merge runs `seam-audit-agent` across 50–53, executing all journeys.
- Lane: `lane::build-loop` — service code and tests.
- Risk: None (slice plan; read-only aggregates; the negative check AC-6 guards the one leak path).
- Entry points added or changed: WF-6 (binds the real reader behind CON-18, CON-19, CON-20).
