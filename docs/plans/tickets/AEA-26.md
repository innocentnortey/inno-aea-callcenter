## [AEA-26] spend: ledger and spend guard

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

> **US-26 · Try to break it and see it fail cleanly.** "As a **reviewer**, I need prompt injection, account fishing and
> spam to meet limits that end in a polite handoff, so that I see 'clean failure', not a crash or a leak."
> Acceptance: "a rate limit or booking cap shows a plain message and the person option".

**Example pair** (no worked pair spends money; the pair follows DO-4 §11's spend-cap rows, SP-1's measured maximum and
stage7/models §6): **input** the ledger holds $29.98 of model calls since midnight America/Chicago today (illustrative)
and a turn starts; its calls add $0.039 (SP-1's maximum per conversation [M]). **Output:** `allow_turn()` was `True` when
the turn started, so the turn finishes and every attempt is recorded (DO-1 §8.2: a running turn may overrun; with 30
turns in flight the day can overrun by up to about $1.17 [C], models ledger note); the next `allow_turn()` is `False`,
and the turn service (AEA-40) answers with the `SPEND_CAP_REACHED` notice. Safety and "Talk to a person" still work. At
the next Chicago midnight `allow_turn()` is `True` again. Separately, an Anthropic 429 with no `retry-after`
(`PROVIDER_SPEND_CAP`) at 14:00 opens Anthropic's circuit: `admit_call("anthropic")` is `REFUSE` until 14:10, then
`PROBE` once; the probe's attempt succeeds, the gateway calls `close_provider_cap("anthropic")`, and calls flow again.

The one place that records what every model call cost and stops model use at a cap (DO-3 §4.4 `services/ledger.py`;
DO-4 §14 `LedgerService` as revised by [`stage7/models.md`](../../design/contracts/stage7/models.md) §6, which wins):

1. **`adapters/sqlite/repos_spend.py`** (body of AEA-02's shell, over the `20_spend.sql` that **AEA-10 writes** with
   models §6's columns; slice plan §0 deviation 1, MOD-15, MC-10): `SpendRow(CallRecord)` plus `id`, `recorded_at` and
   the `TurnIds` fields; `SpendRepo(conn)` with `append(row) -> int` (the only write), `total_between(start_utc,
   end_utc) -> float` (`SUM(cost_usd)` over `recorded_at >= start AND < end`, 0.0 when no row) and `for_turn(turn_id)
   -> tuple[SpendRow, ...]` (id ascending) (MOD-19). `failure` is stored as `failure_kind` and `http_status` (null on
   success) and rebuilt on read. Append-only: no update, delete or clear; the demo reset keeps `spend_ledger`
   (cases.md §1.3 *Kept*; DO-6 *Storage*).
2. **`services/ledger.py`** (models §6; MOD-11, MOD-13, MOD-18):
   - `CallAdmission` (`ALLOW`, `PROBE`, `REFUSE`) and the one-method `SpendGuard` Protocol (`allow_turn() -> bool`),
     which `LedgerService` implements; `TurnService` (AEA-40) receives the ledger typed as `SpendGuard`.
   - `LedgerService(uow, *, wall_clock, daily_cap_usd, probe_after_s=600.0)`: `wall_clock` is the container's one
     wall clock (web.md §4 `get_wall_clock()`, `datetime.now(UTC)`, MC-20), **never** the demo `Clock`;
     `daily_cap_usd` has no default (the container passes `limits.spend.daily_cap_usd`, 30.0 [T], AEA-01 `SpendLimits`,
     MC-22); `probe_after_s` 10 min [A].
   - `record(call, ids)`: one row per `CallRecord` (one per HTTP attempt, failed ones included), in its own short write
     unit of work, `recorded_at` stamped from `wall_clock` as UTC ISO-8601 with `+00:00` by `adapters/sqlite/db.py`
     `format_wall` (cases.md §1.0).
   - `spend_today()`: the America/Chicago calendar day turned into UTC bounds with `zoneinfo`, then `total_between`;
     live, eval and load rows together (they share the cap, DO-7 M-26), so the 25-hour day on 2026-11-01 needs no
     special case.
   - `allow_turn()`: `spend_today() < daily_cap_usd`; **our cap only**, never the circuit; checked before a turn,
     never mid-turn (DO-1 §8.2, MOD-11).
   - **The per-provider circuit, in memory** (models §6 table): closed → `ALLOW`; open and under `probe_after_s` since
     the trip → `REFUSE`; open and at or past it with no probe in flight → `PROBE` once (marked in flight; a probe in
     flight for more than 60 s is treated as lost); open with a probe in flight → `REFUSE`.
     `trip_provider_cap(failure)` opens `failure.provider`'s circuit for kinds `PROVIDER_SPEND_CAP` and
     `OUR_SPEND_LIMIT` (re-opening with a new trip time when a probe meets the cap again) and ignores every other kind;
     `close_provider_cap(provider)` closes it; `admit_call(provider)`; `open_circuits()`. Release is **only** by a
     successful probe: not by the demo reset, not by Chicago midnight; not persisted, so a restarted process starts
     closed and re-trips on its first capped call (MOD-13).
   - `models_disabled()`: `True` when `not allow_turn()` or any circuit is open ("handoff-only mode" on CON-19).
3. A `register_spend()` hunk in `web/container.py` (own hunk only) that builds the one `LedgerService` and binds it for
   the gateway (AEA-20: `record`, `admit_call`, `trip_provider_cap`, `close_provider_cap`), the turn service (AEA-40, as
   `SpendGuard`), the alert evaluator (AEA-32: `spend_today`, `open_circuits`) and the metrics reader (AEA-53).

### Source

- PRD R-41 ("a daily model-spend cap that falls back to handoff"); PRD §5 *Spend* ($30/day, Q-061).
- **Final contract:** [`stage7/models.md`](../../design/contracts/stage7/models.md) §1 (`ProviderCall`, `CallRecord`), §5
  rules 1, 6, 7 (how the gateway calls the ledger), §6 (`SpendLimits`, `CallAdmission`, `SpendGuard`, `LedgerService`,
  the circuit table, `spend_ledger` columns, `SpendRow`, `SpendRepo`), §7 (container wiring); ledger
  [`7b-decisions/models.md`](../7b-decisions/models.md) MOD-5 (`cost_source`), MOD-11, MOD-13, MOD-15, MOD-18, MOD-19;
  merge MC-10, MC-20, MC-22. `stage7/cases.md` §1.0 (unit of work, `format_wall`), §1.1 (`20_spend.sql` = models §6),
  §1.3 (*Kept*), §8 (`AlertEvaluator` reads `spend_today`, `open_circuits`).
- DO-4 §11 (failure-to-customer rows *Our $30/day cap reached*, *Provider spend cap*), §12, §14 `LedgerService`.
- DO-3 §3 (`services/ledger.py`, `repos_spend.py`), §4.4, §8 A2 row, §10 C-3 and C-12.
- DO-1 §8.2 rows *Spend cap: ours* and *Spend cap: Anthropic's*.
- DO-6 *Records* (`spend_ledger`), *Storage and access*, *Missing instrumentation* ("Spend-ledger rows per turn are
  checked against the turn's model-call count"), alert *Spend*.
- DO-7 M-24, M-25, M-26. UI_CONTRACTS CON-19 (spend day; `today_cents`, `cap_cents`, `resets_at` read by AEA-53).
- Slice plan row AEA-26; §0 deviation 1; §3 rows `adapters/sqlite/repos_*.py`, `web/container.py`.
- **Brief check:** serves "Could this run for a month without you? Would the business know if it broke?" (*What we are
  looking for*, production thinking) by bounding model spend and recording every call; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `record` writes exactly one `spend_ledger` row per `CallRecord`, for `status` `ok` and `error` alike, holding every column models §6 lists (`recorded_at`, the `TurnIds` fields `thread_id`, `turn_id`, `request_id`, `run_tag`, `run_id`, `agent_version`, and `role`, `provider`, `model`, `attempt`, `latency_ms`, the five token counts, `cost_usd`, `cost_source`, `status`, `failure_kind`, `http_status`, `provider_request_id`, `stop_reason`); `recorded_at` is UTC with `+00:00` from the injected wall clock — verify: `tests/services/test_ledger.py::test_record_one_row_per_attempt_including_failures` (temp SQLite from `tests/fixtures/sqlite.py`) — evidence: row count equals record count; the column set equals models §6's list; a failed row reads back with its `ProviderFailure` kind and HTTP status.
- [ ] AC-2 [invariant] `spend_today()` sums rows from 00:00 to 24:00 America/Chicago on the injected wall clock, live, eval and load rows together; a row at 23:59:59 Chicago counts for that day and one at 00:00:00 for the next; UTC midnight is not a boundary — verify: `tests/services/test_ledger.py::test_spend_today_is_the_chicago_day` — evidence: sums equal the hand-computed fixture totals.
- [ ] AC-3 [invariant] The Chicago day holds across the daylight-saving change on Sun 2026-11-01 (a 25-hour day) — verify: `tests/services/test_ledger.py::test_spend_day_across_dst_end` — evidence: every fixture row of that local date is summed once and none of the next.
- [ ] AC-4 [invariant] `allow_turn()` is `True` below the injected `daily_cap_usd` (30.0) and `False` at or above it; records arriving after the cap (the running turn's overrun) are still written and counted; changing the constructor's cap to 5.0 moves the boundary, and `services/ledger.py` holds no `30` literal — verify: `tests/services/test_ledger.py::test_allow_turn_at_cap_and_overrun_recorded` plus `grep -n "30" src/meridian/services/ledger.py` in review — evidence: `True` at $29.98, the $0.039 overrun row present, `False` at $30.019; the 5.0 case flips at $5.00; the grep shows no cap literal.
- [ ] AC-5 [invariant] Our cap releases at the next Chicago midnight with no action — verify: `tests/services/test_ledger.py::test_allow_turn_releases_at_chicago_midnight` — evidence: `False` at 23:59 Chicago, `True` at 00:00 with the same rows.
- [ ] AC-6 [failure/refusal] The provider circuit follows models §6 (MOD-13): tripped at T by `PROVIDER_SPEND_CAP` → `admit_call` is `REFUSE` at T+9 min, `PROBE` once at T+10 min while a second caller gets `REFUSE`, `ALLOW` after `close_provider_cap`; a probe that meets the cap again (`trip_provider_cap`) re-opens with a new trip time; a probe in flight for more than 60 s is treated as lost and lets one more `PROBE` through — verify: `tests/services/test_ledger.py::test_provider_circuit_probe_cycle` (fake monotonic and wall clocks) — evidence: the admission sequence asserted step by step.
- [ ] AC-7 [failure/refusal] `trip_provider_cap` opens only `failure.provider`'s circuit and only for kinds `PROVIDER_SPEND_CAP` and `OUR_SPEND_LIMIT`; every other kind (`RATE_LIMITED`, `OVERLOADED`, `SERVER`, `TIMEOUT`, …) leaves it closed; with Anthropic open, `admit_call("openrouter_jev")` is `ALLOW` and `open_circuits()` is `("anthropic",)` — verify: `tests/services/test_ledger.py::test_trip_by_kind_and_per_provider` (parametrised over every `ProviderFailure` kind) — evidence: one case per kind; the per-provider case passes.
- [ ] AC-8 [invariant] A circuit is not released by Chicago midnight or by anything but a probe, and is not persisted: crossing midnight with the circuit open keeps `REFUSE` until the probe interval; a fresh `LedgerService` over the same database starts with every circuit closed while the earlier trip's row (its `failure_kind`) is still in `spend_ledger` — verify: `tests/services/test_ledger.py::test_circuit_not_released_by_midnight_and_not_persisted` — evidence: `REFUSE` at 00:00:01 Chicago; the new instance's `open_circuits()` is empty and `for_turn` returns the trip row.
- [ ] AC-9 [invariant] `allow_turn()` reads our cap only, and `models_disabled()` is `True` for either cause and `False` with neither (MOD-11) — verify: `tests/services/test_ledger.py::test_models_disabled_either_cause` — evidence: four-case table passes; `allow_turn()` stays `True` with a circuit open below the cap.
- [ ] AC-10 [invariant] 20 threads calling `record` at once all land and the day's sum is exact — verify: `tests/services/test_ledger.py::test_concurrent_records_all_written` (the real `busy_timeout`, write units of work) — evidence: 20 rows; the sum equals the inputs'.
- [ ] AC-11 [invariant] `SpendRepo` is append-only: its public methods are exactly `append`, `total_between` and `for_turn`, so the demo reset (AEA-31) and no other caller can remove spend; `LedgerService` satisfies `SpendGuard` structurally — verify: `tests/services/test_ledger.py::test_spend_repo_append_only_and_spend_guard` — evidence: the public method set asserted; `isinstance(ledger, SpendGuard)` with a `runtime_checkable` Protocol passes.
- [ ] AC-12 [negative] Ledger rows and the ledger's log lines hold IDs, model and role names, counts, costs, statuses and failure kinds only: a seeded distinctive API-key-shaped string and a seeded customer sentence placed in the surrounding test context (a failure's message, the test turn's text) never reach the table, the captured log or the in-memory trace sink — verify: `tests/services/test_ledger.py::test_rows_and_logs_hold_allow_listed_fields_only` — evidence: absence asserted in table text, log and sink.
- [ ] AC-13 [capture] Rows are readable per `turn_id` (`for_turn`) and summable per `thread_id` with `run_tag`, so DO-6's check "spend-ledger rows per turn against the turn's model-call count", web.md §9's turn-row cost and call counts, CAP-1's "spend rows" (AEA-51, at the real CON-2 entry point) and AEA-51's wiring assertion (every row's `model` equals its role's `RoleSpec.model`, models §7) can run — verify: `tests/services/test_ledger.py::test_rows_queryable_by_turn_and_thread` — evidence: per-turn count and per-conversation cost returned for a two-turn, two-tag fixture.
- [ ] AC-14 [journey] Extends J-9 (slice plan §0a journey map; J-9 is a proposed addition to the map, from the join audits; `backend-amendments.md` §3): a turn while the `SpendGuard` reports the day's cap reached shows the `SPEND_CAP_REACHED` notice with the person action, and the stored `turn` row is `degraded_handoff` / `spend_cap` with no `spend_ledger` row of its own; asserting what the user sees and what is stored, in `tests/journeys/j9/test_aea_26.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j9/test_aea_26.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-26.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-15 [regression/context] Same change updates: `.claude/reference/area-map.md` A2 ledger rows (`services/ledger.py`, `repos_spend.py`: planned → actual + commit), `.claude/state/icm-progress.md` (the affected row's evidence link), and DO-3 §3 rows for those two files (status only) — verify: `git diff --name-only` — evidence: those paths besides the owned files; no `schema/*.sql` in the diff.

### Observability

- Responsibilities: one `spend_ledger` row per model-call attempt for every workflow that calls a model (the WF-1 chat
  turn and the eval and load runs WF-9, WF-10 through the same app), each carrying `turn_id`, `thread_id` and `run_tag`
  (DO-6 *Records*); the cap and circuit state behind the `spend_cap_reached` and `provider_spend_cap` signals (DO-1
  §8.2) that AEA-32's alert evaluator and CON-19 read (`spend_today`, `open_circuits`, `models_disabled`). No prompt,
  output, customer text or key value.
- Capture evidence: AC-13 here; AC-12 is the negative half. End-to-end capture at the real CON-2 entry point is CAP-1
  in AEA-51. This issue adds no entry point.

### Evaluation

N/A — no DO-5 suite judges the ledger itself; its rules are proven by the service tests above, and DO-5 only reads
spend totals from these rows for its *Baselines* cost line and E-8's spend line.

### Metrics

- References: M-25 (cost per conversation: sum of `cost_usd` per `thread_id`, segments live / eval / load and role),
  M-26 (spend per Chicago day against the $30 cap, approved Q-061), M-24 (retried HTTP 429s counted apart: read from
  `attempt`, `failure_kind` and `http_status`).
- Acceptance conditions: M-25 and M-26 stay computable from the rows alone (AC-1, AC-2, AC-13); M-24's retry count stays
  computable from AC-1's columns; the $30 cap is the approved target, used as the guard, never reported as a result.

### Blocked by

AEA-10 (`20_spend.sql` with models §6's columns, `SqliteUnitOfWorkFactory`, `format_wall`, `temp_sqlite()`). The
`repos_spend.py` shell and `CallRecord` / `ProviderFailure` / `TurnIds` come from AEA-02 and `Limits.spend` from AEA-01,
both wave 0 and already merged before AEA-10.

AC-14's journey record names AEA-57 (harness, wave 2) and AEA-51 (the integrated turn) as *Blocked by* for its
integrated level only (`integrated-journeys.md` §4); they are evidence-level dependencies, not merge blockers, so no wave
moves.

### Agent handoff

- Area / owner: A2 Models, ledger part (DO-3 §8); slice plan AEA-26.
- Contracts and shared surfaces: consumes `CallRecord`, `ProviderCall`, `ProviderFailure`, `ProviderName`, `TurnIds`
  (AEA-02, models §1), the unit-of-work factory, `format_wall` and `20_spend.sql` (AEA-10), `Limits.spend.daily_cap_usd`
  (AEA-01, passed by the container). Produces `LedgerService` and `SpendGuard` for AEA-20 (gateway rules 1, 6, 7),
  AEA-40 (admission step 2), AEA-32 (`AlertEvaluator`), AEA-53 (`spend_today`, `open_circuits`, rows for M-25/M-26) and
  AEA-51 (wiring, `for_turn`); the same `LedgerService` satisfies `ModelsStatus` (`models_disabled() -> bool`,
  AEA-21's `agent/context.py`) structurally for `GraphDeps.ledger` (graph-core §4, R-G-13; AEA-51 wires it). Journey:
  extends J-9 in `tests/journeys/j9/test_aea_26.py` on AEA-57's harness (AC-14). Must not edit: `schema/*.sql`, `db.py`, `repos_core.py`, `ports/*`, `domain/*`,
  `policy/limits.py`, any other `register_` hunk.
- Scope boundary / refusal: no gateway logic (AEA-20 decides when to admit, record, trip and close), no notice
  composition (AEA-40), no alert writing (AEA-32), no monitoring read (AEA-53), no 80% early warning (none approved,
  DO-7 *Where … differ* 2), no persistence of circuit state (MOD-13).
- Wave and gates: wave 2; no human gate.
- Lane: build-loop — repository and service code the app runs.
- Risk: None — it caps spending but moves no money, holds no secret and opens no access (slice plan: not **Sec**).
- Entry points added or changed: None.
