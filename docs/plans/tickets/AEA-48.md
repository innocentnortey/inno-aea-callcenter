## [AEA-48] reads API: owner metrics, monitoring, latest eval (CON-18…20)

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

> **US-27:** "As a **reviewer** (and the business owner), I need a monitoring page (volume, containment, escalations,
> failures, latency, spend against the daily cap, alerts as decision lines, and when the health check last restarted the
> service) and the evaluation report (test-set mix, retrieval hit rate, accuracy and escalation rates, each with its
> denominator, and which split each number comes from), with no codes or card numbers in what's shown, so that I can
> check the claims myself."
> **US-24:** "As a **business owner**, I need the in-scope correct-resolution rate, promises kept on time, outcomes with
> their denominators, and handoffs by reason, each opening the cases behind it, so that I can decide what to fix or
> widen next."

Three read routes in `web/routes/reads.py`, with response models in `web/schemas/reads.py` whose fields are copied from
the OpenAPI schemas. Each is a thin wrapper over the **`MetricsReads` Protocol** declared in web.md §4 (`web/deps.py`,
AEA-23; MC-6), reached through `get_metrics_reads()`. AEA-53's concrete `MetricsReader` (cases.md §9, wave 3)
satisfies it structurally and binds the provider; until then the routes are built and tested against a fake (DO-3 S-20).

| Operation | CON | Reader call | Role check |
|---|---|---|---|
| `getOwnerMetrics` `GET /api/staff/owner-metrics` | CON-18 | `owner_metrics() -> Mapping[str, object]` | `require_staff(OWNER, SUPERVISOR)` (x-roles order, MC-4) |
| `getMonitoring` `GET /api/monitoring` | CON-19 | `monitoring() -> Mapping[str, object]` | none: every signed-in role, the login gate is enough |
| `getLatestEval` `GET /api/eval/latest` | CON-20 | `latest_eval() -> Mapping[str, object]` | none: every signed-in role |

**What the route does with the mapping (staff.md §9, STF-17).** It validates it through `web/schemas/reads.py`.
Unknown keys are dropped (`extra="ignore"`) with **one warning that names the dropped keys, never their values**, so
nothing undocumented reaches a client. A missing required field is a server bug and answers 500. The route computes
nothing, stamps nothing and reads no clock: **the reader stamps every time field** (CON-19 `as_of` = wall clock, CON-19
`demo_now` and CON-18 `as_of` = demo clock; staff.md §10, STF-22, MC-5). `Measure.id` values are DO-7 `M-n` / DO-5
`E-n` ids set by the reader and passed through unchanged; the OpenAPI examples' ids are illustrative and are not asserted
(STF-18). Stored numbers only, never recomputed on read (DO-6 WF-6, R-35).

**Limits and reset (web.md §5, §7; staff.md §11).** AEA-23's middleware does both; the routes add nothing.
`getMonitoring` and `getLatestEval` document 429 `REQUEST_RATE_LIMITED` and 503 `RESET_IN_PROGRESS`.
`getOwnerMetrics` documents neither: it is never rate-limited, and while a reset holds the gate it waits up to
`limits.web.reset_wait_s` (5 s [A]) and then answers 200 (STF-7).

**Example pair (OpenAPI examples; their numbers are made-up values, not results).** Before any evaluation run:
`GET /api/eval/latest` → 200 `NO_RUN`: `splits` `{dev: null, held_out: null}`, `headline: null`, `dev_label` "Dev (we
read and fixed these, so it overstates)" (SCR-11: "No evaluation run yet. No number is shown before then."). With too few
turns for a percentile: `GET /api/monitoring` → 200 `TOO_FEW_TURNS`: the latency tiles have `value: null` and
`null_reason` "Not enough turns yet (fewer than 20)", while `spend` shows `today_cents`, `cap_cents: 3000`, `day`
"America/Chicago midnight to midnight" and `resets_at`. Acting as the representative,
`GET /api/staff/owner-metrics` → 403 `ROLE_NOT_ALLOWED` with `details.needs` `["owner", "supervisor"]`.

**Produced for other issues:** the three operations for AEA-53 (binds the real reader and proves CAP-6 through them; its
tests validate the reader's output with this issue's `web/schemas/reads.py` models) and AEA-55.

### Source

- PRD R-12, R-32, R-35, R-36, R-38, R-39, R-41, R-48; US-24, US-27.
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml`: `getOwnerMetrics`, `getMonitoring`, `getLatestEval`; schemas
  `OwnerMetricsResponse`, `Measure`, `MonitoringResponse`, `Tile`, `MonitorAlert`, `EvalResponse`, `EvalRun`,
  `EvalMeasure`, `ApiError`; responses `Unauthenticated`, `RoleNotAllowed`, `TooManyRequests`, the 503
  `RESET_IN_PROGRESS` examples; each operation's `x-roles`.
- `UI_CONTRACTS.md` CON-18, CON-19, CON-20, *Data classes* (D5), *Access* (R-48 reverses open access).
- `docs/design/contracts/stage7/staff.md` §9 (metrics reads), §10 (time sources), §11 (during a reset);
  `stage7/web.md` §3 (`require_staff`), §4 (`MetricsReads`, `get_metrics_reads`), §5 (the 429 set), §7 (`ResetGate`,
  the 503 set), §10 (`request` record), §13 (`openapi_check.py`); `stage7/cases.md` §9 (`MetricsReader`, who stamps
  what). Decisions: `docs/plans/7b-decisions/staff.md` STF-7, STF-8, STF-17, STF-18, STF-22, STF-25; merge MC-4, MC-5,
  MC-6, MC-14.
- `docs/design/contracts/api-con-mapping.md` §1 CON-18…CON-20, UXR-23, §4 (`as_of` is real time).
- DO-3 §4.4 (`services/metrics_reader.py`), §7 rows R-35, R-38/R-39; DO-6 WF-6, CAP-6, *Two questions, kept apart*,
  alerts table; DO-7 registry (M-1…M-29) and *Where this registry and other documents differ*; DO-5 *Verification and
  evidence*, *Development and held-out separation*.
- SCREEN_SPECS SCR-9, SCR-10, SCR-11 (states only).
- **Contract notes (OpenAPI wins on fields; listed, not edited; settled by STF-18 and STF-25, documents fixed by
  AEA-08):** (1) The examples' `Measure.id` values disagree with DO-7 and DO-5 (CON-18 `SEEDED` labels promises kept
  M-9, DO-7 says M-13; CON-19 `TOO_FEW_TURNS` labels latency M-25/M-26, DO-7 says M-23; CON-20 `STALE_RUN` labels
  retrieval E-6, DO-5 says E-2); the field description "M-n from the metrics registry" makes DO-7 / DO-5 authoritative.
  (2) SCREEN_SPECS SCR-10 R1 reads "Updated [time] (demo time)"; CON-19 `as_of` is real time. (3) DO-7 M-26 still
  proposes a UTC spend day; the OpenAPI `spend.day` is "America/Chicago midnight to midnight". (4) DO-3 §8 and
  api-con-mapping put these routes in wave 3 with the reader; the slice plan builds them in wave 2 against the injected
  Protocol.
- **Brief check:** serves "Add observability so the business can see how the agent is performing after launch: volume,
  containment, escalations, failures, latency." (Part B §7) and "Report accuracy on the handled drivers and the escalation
  rate on the rest. Show the numbers, not just the claim." (Part B §5); touches nothing out of scope; weakens nothing →
  proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] With the `MetricsReads` fake returning each named example's content as a plain mapping, every 200 body validates against its response schema: `getOwnerMetrics` SEEDED, EMPTY; `getMonitoring` DEFAULT, FIRING, TOO_FEW_TURNS, EMPTY, ZERO_TRAFFIC_FIRING, FAILURE_AND_TRACE_FIRING; `getLatestEval` BOTH_SPLITS, DEV_ONLY, STALE_RUN, NO_RUN — verify: `tests/api/test_reads_routes.py::test_<operationId>_matches_openapi` (AEA-23's `assert_response_matches`, STF-8) — evidence: twelve bodies validate.
- [ ] AC-2 [invariant] The routes compute nothing: each request calls its reader method once and returns its values field for field (numerators, denominators, `null_reason`, `kind`, `case_refs`, alert states, `Measure.id`, split measures with `min`, `max`, `target`, and every time field as the reader stamped it); `routes/reads.py` and `schemas/reads.py` import no repository, unit of work or SQL and read no clock — verify: `…::test_reads_pass_through` plus `grep -nE "uow|repos_|sqlite|UnitOfWork|datetime\.now|time\.time" src/meridian/web/routes/reads.py src/meridian/web/schemas/reads.py` — evidence: equality asserts pass; grep prints nothing.
- [ ] AC-3 [invariant] Time fields keep their clocks (STF-22): with the fake's CON-19 `as_of` (wall) and `demo_now` (demo, 2026-10-19 07:00 −05:00) set to different instants, the body carries both unchanged and distinct; CON-18 `as_of` is the fake's demo-clock value — verify: `…::test_time_fields_passed_through` — evidence: three values asserted equal to the fake's.
- [ ] AC-4 [negative] Nothing outside the documented fields reaches a client (R-36; CON-19 `redacted: true`): a reader mapping carrying extra keys `trace_url`, `customer_name` and `code` with distinctive values produces bodies without those keys or values, and exactly one warning log record that names the three keys and contains none of the values — verify: `…::test_unknown_keys_dropped_and_named_only` — evidence: values absent from bodies and every captured log record; one warning listing the keys.
- [ ] AC-5 [failure/refusal] A reader mapping missing a required field (e.g. CON-19 without `as_of`) answers 500 and logs no field value — verify: `…::test_missing_required_field_is_500` — evidence: status 500; the fake's distinctive values absent from captured logs.
- [ ] AC-6 [invariant] The held-out rule survives the route: with the fake returning `DEV_ONLY` (dev split populated, `headline: null`), the body's `headline` is null and the dev split keeps `dev_label`; a measure's target appears only in its `target` field, never in `value` — verify: `…::test_headline_never_dev` — evidence: `headline` null; `target` and `value` equal the fake's separately.
- [ ] AC-7 [failure/refusal] **WF-6:** Access: `getOwnerMetrics` passes owner and supervisor; customer and representative get 403 `ROLE_NOT_ALLOWED` with `details.needs` `["owner", "supervisor"]` and `details.reason` `wrong_role`, and the reader is not called; `getMonitoring` and `getLatestEval` answer every signed-in role, customer included; all three answer 401 `UNAUTHENTICATED` without `mhc_session` (AEA-23's real middleware) — verify: `…::test_reads_access` — evidence: bodies validate against `RoleNotAllowed` / `Unauthenticated`; zero reader calls on refusals.
- [ ] AC-8 [failure/refusal] **WF-6:** Through AEA-23's real middleware: with the rate limiter overridden to refuse, `getMonitoring` and `getLatestEval` answer 429 `REQUEST_RATE_LIMITED` with `details.retry_after_ms`, and `getOwnerMetrics` still answers 200; with a fake `ResetGate` held, `getMonitoring` and `getLatestEval` answer 503 `RESET_IN_PROGRESS` with `details.retry_after_ms` 5000 at once, and `getOwnerMetrics` waits and answers 200 once the gate clears (STF-7) — verify: `…::test_reads_429_and_503` — evidence: bodies validate against `TooManyRequests` and the documented 503; one 200 for `getOwnerMetrics` in each case.
- [ ] AC-9 [capture] Driving the three entry points through the app the container builds leaves one `request` record per read (web.md §10: `request_id` = `X-Request-ID`, route template, status, `caller_role`) and no other record kind; page reads are counted, never recomputed into outcomes (DO-6 WF-6) — verify: `…::test_wf6_reads_emit_request_records` — evidence: one record per read; the fake records one call per read. CAP-6 (numbers equal the stored counts after CAP-1…CAP-3; no names, codes, card-like numbers or trace links on CON-19 and CON-20) is AEA-53's.
- [ ] AC-10 [failure/refusal] The read schemas refuse values the pages would misreport (AEA-48-1, shell audit A1): in `web/schemas/reads.py`, `unit` is `Literal["count", "ms", "share"]` on `Measure` and `Tile`; a `share` value must lie in [0, 1]; every `EvalMeasure.value` lies in [0, 1]; and (`id`, `label`) pairs are unique within one response. A `MetricsReads` mapping that breaks any of these is a server bug: 500 and one log line naming the field and rule, never the value (the OpenAPI types `unit` as a free string, so this is stricter than the contract and still valid against it) — verify: `tests/api/test_reads_routes.py::test_unit_vocabulary_enforced` — evidence: three valid mappings pass; `unit: "per 100 turns"`, a share of 75 and a duplicate (`id`, `label`) each answer 500 naming the field.
- [ ] AC-11 [contract] `tests/contract/cases/reads.py` holds the server cases for `getOwnerMetrics`, `getMonitoring` and `getLatestEval` (AEA-48-2; slice plan §0a, contract cases per route issue): preconditions (owner or supervisor for the first; any role for the others), and each documented error status the routes can produce (401, 403 on `getOwnerMetrics`, 429 and 503 on the other two) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "getOwnerMetrics or getMonitoring or getLatestEval" -rs` once AEA-59's runner is merged — evidence: one pass per case; skips only as `not bound: get_metrics_reads` until AEA-53.
- [ ] AC-12 [journey] Extends J-10 (slice plan §0a journey map): the three read routes return the reader's stored values field for field, with their labels, units from {count, ms, share} and denominators; asserting what the user sees and what is stored, in `tests/journeys/j10/test_aea_48.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j10/test_aea_48.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-53 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-48.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-53 (`integrated-journeys.md` §4).
- [ ] AC-13 [invariant] **WF-6:** status values (OBS-13, DO-6 *Status values*): through the app the container builds, each read's `request` record has `status` equal to the HTTP status of its 200, 401, 403 (`getOwnerMetrics` as representative), 429 and 503 answers, and AC-5's missing-field 500 records `error_kind`; no status value outside DO-6's list is stored — verify: `tests/api/test_reads_routes.py::test_wf6_request_status_values` — evidence: (`status`, `error_kind`) per response printed.
- [ ] AC-14 [regression/context] Same change updates `.claude/reference/area-map.md` (A10b row: routes planned → actual with the commit, reader still planned), `.claude/state/icm-progress.md` (the A10b reads row's evidence link) and DO-3 §3's status for `web/routes/reads.py` and `web/schemas/reads.py` — verify: `git diff --stat` — evidence: only those rows change.

### Observability

- Responsibilities: WF-6 (DO-6 registry) — the middleware's `request` record per page read with `caller_role`; no
  recomputation and no new record kind ("page reads are counted, never recomputed into outcomes"); one warning naming
  dropped keys, never their values (AC-4); no response content logged.
  A schema refusal (AC-10) logs one line naming the field and rule, never the value.
- Capture evidence: AC-9 (entry points), AC-13 (status values), AC-4, AC-5 and AC-10 (negative). CAP-6 end to end is AEA-53's; J-10's read
  step (AC-12) runs on AEA-57's harness.

### Evaluation

- Checks: CON-20 only displays scored runs. This issue keeps two of DO-5's rules visible on the page: the headline comes
  only from the sealed held-out split (AC-6), and a target is never shown as a result (AC-6). No suite is added.
- Expected-answer authority: the eval harness's run records (`eval_runs`, `eval_case_results`, loaded from
  `eval/reports/<run_id>.json`; cases.md A-8) written by AEA-24 and scored per DO-5; never this route.

### Metrics

- References: displays M-1 to M-29 (DO-6 WF-6: "Displays M-1 to M-29; computes none of them on read"): M-1, M-2, M-3,
  M-4, M-5, M-6, M-7, M-8, M-9, M-10, M-11, M-12, M-13, M-14, M-15, M-16, M-17, M-18, M-19, M-20, M-21, M-22, M-23,
  M-24, M-25, M-26, M-27, M-28, M-29.
- Acceptance conditions: every measure reaches the client with its id, numerator, denominator, unit and `null_reason`
  unchanged (AC-2), so each M-n stays exactly what AEA-53 reads from the stored records; units are only `count`, `ms`
  or `share`, shares and `EvalMeasure.value` lie in [0, 1], and (`id`, `label`) pairs are unique (AC-10, so a split M-n
  stays distinguishable); no target is set here or shown as a result.

### Blocked by

- AEA-23 (web app, middleware, `web/deps.py` with `require_staff`, `MetricsReads` / `get_metrics_reads`, the rate
  limiter, `ResetGate`, `openapi_check.py`).
- Evidence level only, not a build blocker: AC-11 runs once AEA-59's server-case runner (wave 2) is merged and binds the
  reader once AEA-53 (wave 3) is; AC-12 reaches `integrated with a scripted model` once AEA-57 (harness, wave 2) and
  AEA-53 (J-10 lands, wave 3) merge, and until then its record states `mock-tested` with those two in *Blocked by*
  (`integrated-journeys.md` §4).

### Agent handoff

- **Area / owner:** A10b Reads (DO-3 §8); files `src/meridian/web/routes/reads.py`, `src/meridian/web/schemas/reads.py`,
  this issue's `register_…()` hunk in `web/container.py` (includes the router only; AEA-53's hunk binds
  `get_metrics_reads()`), tests under `tests/api/`, `tests/contract/cases/reads.py` (AC-11; AEA-59 owns the runner),
  `tests/journeys/j10/test_aea_48.py` and its record `docs/testing/journeys/YYYY-MM-DD-AEA-48.md` (AC-12;
  `tests/journeys/support/` is AEA-57's).
- **Contracts and shared surfaces:** consumes `MetricsReads` through `get_metrics_reads()` (declared by AEA-23,
  implemented by AEA-53 in a later wave, injected) and `require_staff` (AEA-23 declares, AEA-44 implements); produces
  CON-18…CON-20 and the `web/schemas/reads.py` models for AEA-53 (which blocks on this issue and validates its output
  with them) and AEA-55. Must not edit: `services/metrics_reader.py` (AEA-53), `services/health.py` and `repos_ops.py`
  (AEA-32), `web/{app,middleware,deps,errors}.py`, any other route or schema file, `domain/*`,
  `tests/api/openapi_check.py`, the OpenAPI.
- **Scope boundary / refusal:** no metric arithmetic, no SQL, no clock read, no time stamping, no trace links, no push
  alerts (R-35: alerts live on the page only); a target never appears as a result.
- **Decisions applied:** STF-7 / MC-14 (429 and 503 from the middleware; `getOwnerMetrics` waits), STF-8 (shared
  validator), STF-17 as changed by MC-6 (`MetricsReads` in `web/deps.py`, mappings validated by `schemas/reads.py`,
  unknown keys dropped and named, missing field → 500), STF-18 (ids per DO-7 / DO-5, not asserted against examples),
  STF-22 / MC-5 (the reader stamps every time), STF-25 (contract notes 2–4 confirmed), MC-4 (`needs` in x-roles order),
  join amendments AEA-48-1 (unit vocabulary and scales in `schemas/reads.py`, which AEA-53-1 validates against) and
  AEA-48-2 (`docs/plans/ux-join/backend-amendments.md` §2).
- **Wave and gates:** wave 2; no gate.
- **Lane:** `lane::build-loop` — route, schema and test code (ticket-lanes: changes code).
- **Risk:** None (slice plan). Redaction is by construction in the stored aggregates (AEA-53, CAP-6); this route adds the
  unknown-key guard (AC-4).
- **Entry points added or changed:** WF-6 (`GET /api/staff/owner-metrics`, `GET /api/monitoring`, `GET /api/eval/latest`).
