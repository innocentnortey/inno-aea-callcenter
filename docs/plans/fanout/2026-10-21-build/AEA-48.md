# Plan — [AEA-48] reads API: owner metrics, monitoring, latest eval (CON-18…20)

**Status:** planned (READY) · `lane::build-loop` · no `risk::security` (slice plan row: not **Sec**) · wave 2
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/48 (spec copy:
`docs/plans/tickets/AEA-48.md`) · **Base revision:** `main` at `4a76850` (AEA-23 web shell merged; AEA-47 merged at
`23dd4ac`, whose route/test pattern this plan copies)
**Planner:** claude-opus-5-5, 2026-10-21. First plan for this ticket (no earlier plan file existed).
**Builder:** `fanout-implementer` (Sonnet). Normal loop: write the code **and** the tests named in §7 together. No
test-writer, no frozen tests, no security agent. Every name below is copied from the code on `main` or the signed
contracts; the two production files in §5 were prototyped by the planner in a scratch copy (outside the repo) and pass
`mypy --strict` (project config), `ruff check`, `ruff format`, the AC-2 grep, and a round-trip of all twelve OpenAPI
200 examples (each body equals its example). You do not need to re-read the design.
**Worktree / branch:** whatever the orchestrator gives you (convention:
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-48`, branch `aea-48-reads-api`). Paths below are relative to the
repository root.

---

## 1. Goal and sources

### Goal (from the issue, *What to build*)

> Three read routes in `web/routes/reads.py`, with response models in `web/schemas/reads.py` whose fields are copied
> from the OpenAPI schemas. Each is a thin wrapper over the **`MetricsReads` Protocol** declared in web.md §4
> (`web/deps.py`, AEA-23; MC-6), reached through `get_metrics_reads()`. AEA-53's concrete `MetricsReader` (wave 3)
> satisfies it structurally and binds the provider; until then the routes are built and tested against a fake.

| Operation | CON | Reader call | Role check |
|---|---|---|---|
| `getOwnerMetrics` `GET /api/staff/owner-metrics` | CON-18 | `owner_metrics() -> Mapping[str, object]` | `require_staff(OWNER, SUPERVISOR)` (x-roles order, MC-4) |
| `getMonitoring` `GET /api/monitoring` | CON-19 | `monitoring() -> Mapping[str, object]` | none: every signed-in role |
| `getLatestEval` `GET /api/eval/latest` | CON-20 | `latest_eval() -> Mapping[str, object]` | none: every signed-in role |

The route validates the mapping through `web/schemas/reads.py`; unknown keys are dropped with **one warning naming the
dropped keys, never their values**; a missing required field answers 500. The route computes nothing, stamps nothing and
reads no clock (the reader stamps every time field). The middleware (AEA-23, already on `main`) answers 429 and 503 for
`getMonitoring`/`getLatestEval` and makes `getOwnerMetrics` wait out a reset (≤ 5 s) and answer 200.

**What a reviewer sees (the ticket's worked pair, OpenAPI examples).** Before any evaluation run, `GET /api/eval/latest`
→ 200 `NO_RUN`: `splits {dev: null, held_out: null}`, `headline: null`, `dev_label` "Dev (we read and fixed these, so it
overstates)". With too few turns, `GET /api/monitoring` → 200 `TOO_FEW_TURNS`: the latency tiles have `value: null`,
`null_reason` "Not enough turns yet (fewer than 20)", and `spend` shows `today_cents`, `cap_cents: 3000`, `day`
"America/Chicago midnight to midnight", `resets_at`. Acting as the representative, `GET /api/staff/owner-metrics` → 403
`ROLE_NOT_ALLOWED`, `details.needs == ["owner", "supervisor"]`, and the reader is never called.

### Context

AEA-23 (merged) built the gate middleware, `web/deps.py` (with `MetricsReads`, `get_metrics_reads`, `require_staff`),
the reset gate, the rate limiter and `tests/api/openapi_check.py`; its `register_reads` stub in `web/container.py` waits
for this ticket. The reader (`services/metrics_reader.py`) is AEA-53, wave 3, and **blocks on this ticket** (its tests
validate its output with this ticket's models), so here every test overrides `get_metrics_reads` with a fake.
AEA-44's real staff store is not merged either; tests use AEA-23's `FakeSessionStore` (same pattern as AEA-47).

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-48.md` (= GitLab #48): AC-1…AC-14, *Observability*, *Evaluation*, *Metrics*, *Agent handoff* | Everything below |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-48 (B, not Sec, blocked by 23, calls metrics reader 53), §0a journey map row J-10 (landed by AEA-53, extended by 48), §3 collision map (`web/container.py`, `web/routes/*.py`, context docs) | Owned files; one hunk; `tests/journeys/j10/test_aea_48.py` |
| Requirements | PRD R-12, R-32, R-35, R-36, R-38, R-39, R-41, R-48; US-24, US-27 | Pages show stored numbers with denominators; no codes/cards/trace links (R-36); login required (R-48) |
| Staff contract (wins over DO-4) | `docs/design/contracts/stage7/staff.md` §9 (metrics reads), §10 (time sources), §11 (during a reset) | Validation rules, who stamps time, 503 vs wait |
| Web contract | `stage7/web.md` §3 (`require_staff`), §4 (`MetricsReads`, `get_metrics_reads`, `RequestContext`), §5 (the six 429 operations), §7 (`ResetGate`, the 503 set), §10 (`request` record), §13 (`openapi_check.py`) | §4 of this plan copies the code |
| Cases contract | `stage7/cases.md` §9 (`MetricsReader`: reader stamps `as_of`/`demo_now`; mapping with OpenAPI field names) | Fake returns plain mappings with OpenAPI names |
| Decisions | `docs/plans/7b-decisions/staff.md` STF-7, STF-8, STF-17 (as changed by MC-6), STF-18, STF-22, STF-25; merge MC-4, MC-5, MC-6, MC-14; UX-join `docs/plans/ux-join/backend-amendments.md` §2 AEA-48-1 (unit vocabulary, AC-10) and AEA-48-2 (contract cases, AC-11) | Applied as written |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml`: paths `/api/staff/owner-metrics` (200 examples `SEEDED`, `EMPTY`; 401; 403; `x-roles [owner, supervisor]`), `/api/monitoring` (200 examples `DEFAULT`, `FIRING`, `TOO_FEW_TURNS`, `EMPTY`, `ZERO_TRAFFIC_FIRING`, `FAILURE_AND_TRACE_FIRING`; 401; 429; 503), `/api/eval/latest` (200 examples `BOTH_SPLITS`, `DEV_ONLY`, `STALE_RUN`, `NO_RUN`; 401; 429; 503); schemas `Measure` (l. 11273), `OwnerMetricsResponse`, `Tile`, `MonitorAlert`, `MonitoringResponse`, `EvalMeasure`, `EvalRun`, `EvalResponse` (l. 11656) | Field names and shapes of §5 step 1; no 500 is documented, so the 500 body is AEA-23's `{"request_id"}` and is never passed to `assert_matches` |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` *Verification and evidence*, *Development and held-out separation* | The headline is held-out only and a target is never a result: the route passes both through unchanged (AC-6); enforcing them in the data is AEA-53 (its AC-5) |
| Observability (DO-6) | `docs/design/observability-contract.md` row WF-6 ("`request_id`; request (page reads are counted, never recomputed into outcomes)"; CAP-6); *Status values* (`request.status` = HTTP status, plus `error_kind` on 5xx) | AC-9, AC-13; CAP-6 is AEA-53's |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-1…M-29 | Displayed, never computed here; ids passed through (STF-18) |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`; workspace `code-design-solid-modularity`, `code-structure`, `async-safety` §6 | Affected tests and journeys; journey record; doc rows in the same change; consumers validate response shapes |
| Merged code (read) | `src/meridian/web/{app,container,deps,errors,logging,middleware}.py`, `web/routes/staff_clock.py`, `web/schemas/staff_clock.py`, `services/reset_gate.py`, `domain/{common,staff}.py`, `policy/limits.py`; `tests/api/{web_shell_support,openapi_check,staff_clock_support,test_staff_clock_routes,test_contract_cases_staff_clock,test_gate,test_app}.py`, `tests/contract/cases/{staff_clock,auth}.py`, `tests/journeys/{README.md,affected.py,j6/test_aea_47.py,j10/test_aea_32.py}`, `tests/unit/web/test_container.py`, `tests/unit/test_import_direction.py` | §4 copies the signatures |

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Change |
|---|---|
| `src/meridian/web/schemas/reads.py` | create (§5 step 1, exact text) |
| `src/meridian/web/routes/reads.py` | create (§5 step 2, exact text) |
| `src/meridian/web/container.py` | modify **only** the body and docstring of `register_reads` (the stub reading "AEA-48 reads API: CON-18 to CON-20 routes (staff.md §9). No-op until AEA-48 fills it.") |
| `tests/api/reads_support.py` | create (doubles, app builder, helpers; §6) |
| `tests/api/test_reads_routes.py` | create (AC-1…AC-10, AC-13, worked pair; §7.1) |
| `tests/api/test_reads_router.py` | create (plan-added router/hunk/source checks; §7.1) |
| `tests/api/test_contract_cases_reads.py` | create (AC-11 local driver, AEA-47 precedent) |
| `tests/contract/cases/reads.py` | create (AC-11) |
| `tests/journeys/j10/test_aea_48.py` | create (AC-12, J-10) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-48.md` | create (AC-12 record; date = the day you commit) |
| `.claude/reference/area-map.md` | modify the *Status* cell of row **A10b Reads** only |
| `.claude/state/icm-progress.md` | add **one new** *Routes verified against code and tests* row directly after the AEA-47 row (do not edit other rows) |
| `docs/design/code-design.md` | modify the one line `│   └── routes/reads.py · schemas/reads.py       CON-18…CON-20 (AEA-48; reader: AEA-53)  …` only |

### Shared surfaces: read only, never edit

`src/meridian/web/{app,middleware,deps,errors,logging}.py`, every other `web/routes/*` and `web/schemas/*`,
`services/*` (incl. `reset_gate.py`), `domain/*`, `ports/*`, `policy/*`, `config.py`, `adapters/*`;
`tests/api/{web_shell_support,openapi_check}.py` and every existing test; `tests/fakes/*`, `tests/conftest.py`,
`tests/fixtures/*`, `tests/journeys/{affected.py,README.md}`; `pyproject.toml`, `uv.lock`.

### Owned by other tickets — do not touch

`services/metrics_reader.py` and the `register_metrics_reader` hunk (AEA-53, which binds `get_metrics_reads`),
`services/health.py`, `repos_ops.py` (AEA-32), every other `register_<area>()` hunk, every other route or schema file
(AEA-40…47), `tests/journeys/j10/test_aea_32.py` (AEA-32), `tests/journeys/j10/test_aea_53.py` (AEA-53, later),
`tests/journeys/support/` (AEA-57), `tests/contract/test_openapi_server.py` (AEA-59), `tests/capture/` (CAP-6 is
AEA-53's), `tests/api/openapi_check.py`, `apps/web/**`, `docs/ux/**` (the OpenAPI and `UI_CONTRACTS.md` included), the
briefing, issued data, `docs/archive/`, `docs/parked/`.

### Must not do

- No metric arithmetic, no SQL, no storage import, no clock read, no time stamping, no trace links, no push alerts, no
  role check other than `require_staff(StaffRole.OWNER, StaffRole.SUPERVISOR)` on `getOwnerMetrics`, no rate-limit or
  reset-gate code (the middleware already does both: `getMonitoring`/`getLatestEval` are in
  `RATE_LIMITED_READ_OPERATIONS` and `RESET_503_OPERATIONS`; `getOwnerMetrics` is in neither).
- **AC-2 grep must print nothing:** do not write the strings `uow`, `repos_`, `sqlite`, `UnitOfWork`, `datetime.now`,
  `time.time` anywhere in `routes/reads.py` or `schemas/reads.py`, comments and docstrings included. `time.time` also
  matches inside `datetime.timezone` and `datetime.timedelta`: in these two files import only `import datetime as dt` and
  use only `dt.date`. (The field *name* `timezone` in `QuietHours` is fine: no dot before it.)
- Do not base the models on `MeridianModel` (it strips whitespace and forbids extras, which would change values or
  refuse extras). Use the `ReadModel` base of §5 step 1.
- Do not log, print or put into an exception message any value from a reader mapping. The route's only log lines are
  the two in §5 step 2 (one WARNING naming dropped keys; one ERROR naming field + rule). Never log `str(exc)` or
  `exc.errors()` with input.
- Do not import anything from `meridian.services.*` or `meridian.adapters.*` in the route or schema file.
- Do not assert `Measure.id` values against the OpenAPI example ids as a rule (STF-18). Comparing a body to the fake's own
  mapping (which may be an example) is fine.
- No `.env` reads, no paid model call, no port bind (TestClient only; never 4019 or 5184). No digits that look like a
  verification code, card or phone number in any test, fixture or record (distinctive values come from `rand_word`,
  letters only).
- `git add` explicit paths only; never `git add -A`. No push, no force-push.

---

## 3. Requirements table

### 3.1 Acceptance criteria (issue, in substance) and plan-added rows

| # | Requirement | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 [invariant] | With the fake returning each named example as a plain mapping, every 200 body validates: `getOwnerMetrics` SEEDED, EMPTY; `getMonitoring` DEFAULT, FIRING, TOO_FEW_TURNS, EMPTY, ZERO_TRAFFIC_FIRING, FAILURE_AND_TRACE_FIRING; `getLatestEval` BOTH_SPLITS, DEV_ONLY, STALE_RUN, NO_RUN (twelve bodies) | §5 steps 1–2 | `tests/api/test_reads_routes.py::test_getOwnerMetrics_matches_openapi`, `::test_getMonitoring_matches_openapi`, `::test_getLatestEval_matches_openapi` (each prints the count; 2 + 6 + 4 = 12) |
| AC-2 [invariant] | One reader call per request; body equals the mapping field for field (numerators, denominators, `null_reason`, `kind`, `case_refs`, alert states, `Measure.id`, split measures with `min`, `max`, `target`, every time field); the two files import no storage and read no clock | `_answer` validates and dumps; nothing else | `…::test_reads_pass_through`; `tests/api/test_reads_router.py::test_reads_sources_touch_no_storage_or_clock`; plus the grep in §7.3 prints nothing |
| AC-3 [invariant] | CON-19 `as_of` (wall) and `demo_now` (demo, 2026-10-19 07:00 −05:00) set to different instants come back unchanged and distinct; CON-18 `as_of` is the fake's demo value | `AwareDatetime` fields, no stamping | `…::test_time_fields_passed_through` |
| AC-4 [negative] | Extra keys `trace_url`, `customer_name`, `code` with distinctive values: absent from bodies (keys and values); exactly one WARNING per request naming the keys, containing none of the values | `ReadModel extra="ignore"`; `dropped_keys`; one `_log.warning` | `…::test_unknown_keys_dropped_and_named_only` |
| AC-5 [failure/refusal] | A mapping missing a required field (CON-19 without `as_of`) → 500; no field value logged | `ValidationError` → `render_unhandled_error`; one ERROR line from `describe_errors` | `…::test_missing_required_field_is_500` |
| AC-6 [invariant] | `DEV_ONLY` (dev populated, `headline: null`): body `headline` null, `dev_label` kept; a measure's `target` only in `target`, never in `value` | pass-through | `…::test_headline_never_dev` |
| AC-7 [failure/refusal] **WF-6** | `getOwnerMetrics`: owner and supervisor pass; customer and representative 403 `ROLE_NOT_ALLOWED`, `details.needs ["owner","supervisor"]`, `reason wrong_role`, reader not called. `getMonitoring`, `getLatestEval`: every role (customer included) 200. All three 401 `UNAUTHENTICATED` without `mhc_session` | `require_staff(StaffRole.OWNER, StaffRole.SUPERVISOR)` as a route-level dependency; AEA-23 middleware | `…::test_reads_access` |
| AC-8 [failure/refusal] **WF-6** | Limiter refusing: `getMonitoring`, `getLatestEval` 429 `REQUEST_RATE_LIMITED` with `details.retry_after_ms`; `getOwnerMetrics` 200. Gate held: the two 503 `RESET_IN_PROGRESS`, `retry_after_ms` 5000, at once; `getOwnerMetrics` waits and answers 200 once the gate clears | middleware only | `…::test_reads_429_and_503` |
| AC-9 [capture] | Through the app the **real container** builds: one `request` record per read (`request_id` = `X-Request-ID`, route template, status, `caller_role`), no other record kind; the fake records one call per read | middleware record | `…::test_wf6_reads_emit_request_records` |
| AC-10 [failure/refusal] | `unit` ∈ {count, ms, share} on `Measure` and `Tile`; a `share` in [0, 1]; every `EvalMeasure.value` in [0, 1]; (`id`, `label`) unique within one response (per `EvalRun` on CON-20, see §8 R-4). Breaking any → 500 + one log line naming field and rule, never the value | validators in §5 step 1 | `…::test_unit_vocabulary_enforced` (three valid mappings pass; `unit: "per 100 turns"`, a share of 75, a duplicate pair each 500 naming the field) |
| AC-11 [contract] | `tests/contract/cases/reads.py` holds server cases for the three operations: preconditions and each documented error status (401; 403 on `getOwnerMetrics`; 429 and 503 on the other two) | case file (§5 step 6) | AEA-59's `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "getOwnerMetrics or getMonitoring or getLatestEval" -rs` once merged; **until then** `tests/api/test_contract_cases_reads.py::test_reads_cases_drive_documented_statuses` (13 cases) |
| AC-12 [journey] | Extends J-10: the three reads return the reader's stored values field for field with labels, units ⊆ {count, ms, share}, denominators. Level today `mock-tested`; *Blocked by* AEA-57 and AEA-53 | `tests/journeys/j10/test_aea_48.py` + record | `uv run pytest -m journey tests/journeys/j10/test_aea_48.py -rs`; `docs/testing/journeys/<date>-AEA-48.md` |
| AC-13 [invariant] **WF-6** | Through the real container: each read's `request` record `status` equals the HTTP status of its 200, 401, 403, 429, 503 answers; the missing-field 500 records `error_kind` | middleware + `request.state.error_kind = "reads_schema_violation"` | `…::test_wf6_request_status_values` (prints `(status, error_kind)` per response) |
| AC-14 [regression/context] | area-map A10b row (routes actual + commit, reader still planned), ICM progress row, DO-3 §3 status line | §5 step 9 | `git diff --stat` shows only those rows in the three docs |
| plan-added (worked pair) | The ticket's example pair: NO_RUN, TOO_FEW_TURNS, representative 403 | as above | `…::test_example_pair_no_run_too_few_turns_and_role_not_allowed` |
| plan-added | Router declares exactly the three GETs with their operation ids; only `getOwnerMetrics` has the role dependency | `build_router()` | `tests/api/test_reads_router.py::test_router_declares_three_gets` |
| plan-added | `register_reads` includes the router once per web-shell app; nothing on a bare app | hunk (§5 step 3) | `tests/api/test_reads_router.py::test_register_reads_includes_router_once` |

### 3.2 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Routes depend on `MetricsReads` via `get_metrics_reads()` | web.md §4; STF-17 / MC-6 | Goal | in-ticket | step 2 |
| Validate through `schemas/reads.py`; extras dropped with one warning naming keys only | staff.md §9; STF-17 | AC-4 | in-ticket | steps 1–2 |
| Missing required field → 500 | staff.md §9; STF-17 | AC-5 | in-ticket | step 2 |
| Reader stamps every time field; route stamps nothing | staff.md §9–§10; STF-22; MC-5 | AC-2, AC-3 | in-ticket | step 2 |
| `Measure.id` passed through; examples' ids not asserted | STF-18 | AC-2 | in-ticket | §7.1 |
| `needs` in x-roles order `[owner, supervisor]` | web.md §3; MC-4 | AC-7 | in-ticket | step 2 |
| 429 set and 503 set from the middleware; `getOwnerMetrics` waits | web.md §5, §7; staff.md §11; STF-7; MC-14 | AC-8 | in-ticket (nothing to build; constants already on `main`, checked by `tests/api/test_openapi_sets.py`) | — |
| `request` record per read with `caller_role`; `error_kind` on 5xx | web.md §10; DO-6 WF-6, *Status values* | AC-9, AC-13 | in-ticket | step 2 (`request.state.error_kind`) |
| Shared response validator | STF-8 | AC-1 | in-ticket | tests use `assert_matches` |
| Unit vocabulary, share and ratio ranges, unique pairs | AEA-48-1 | AC-10 | in-ticket | step 1 |
| Contract cases in the route's own file | AEA-48-2 | AC-11 | in-ticket; local driver plan-added | step 6 |
| `[journey]` J-10 with level and record | integrated-journeys §3–§4 | AC-12 | in-ticket | step 7 |
| Headline only from the held-out split; target never a result (in the data) | DO-5; OpenAPI `EvalResponse` description | AC-6 (pass-through only) | other-ticket: AEA-53 AC-5 builds the data that way | AEA-53 |
| No names, codes, cards, trace links on CON-19/20 (in the data) | R-36; DO-6 CAP-6 | AC-4 (route guard only) | other-ticket: AEA-53 AC-6 (CAP-6) | AEA-53 |
| Consumers validate HTTP response shapes | workspace `async-safety` §6 | AEA-53 uses these models | in-ticket: models are public and importable | step 1 |
| Contract notes (1)–(4): example ids, SCR-10 "demo time", DO-7 UTC day, DO-3 wave 3 | ticket *Contract notes*; STF-18, STF-25 | — | other-ticket: AEA-08 reconciles; listed, not edited | AEA-08 |
| Dropped key names readable in deployed logs | STF-17 "one warning naming the dropped keys" vs AEA-23's allow-list formatter (WEB-11) | — | the LogRecord names them (tests read it); deployed stdout shows only the record's length. Not a blocker; noted as request §8 R-1 | AEA-23 follow-up if wanted |

### 3.3 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `GET /api/staff/owner-metrics` (`getOwnerMetrics`) | WF-6 read-only measure pages | yes, DO-6 row WF-6 | Evaluation: displays scored runs only (CON-20); metrics M-1…M-29 displayed, none computed; capture CAP-6 (AEA-53) |
| `GET /api/monitoring` (`getMonitoring`) | WF-6 | yes | same |
| `GET /api/eval/latest` (`getLatestEval`) | WF-6 | yes | same |

---

## 4. Shared code to use (copied from `main` at `4a76850`)

### 4.1 `meridian.web.deps` (AEA-23)

```python
class MetricsReads(Protocol):
    def owner_metrics(self) -> Mapping[str, object]: ...
    def monitoring(self) -> Mapping[str, object]: ...
    def latest_eval(self) -> Mapping[str, object]: ...

METRICS_READS: Key[MetricsReads] = Key("metrics_reads")   # AEA-53 provides it
def get_metrics_reads(request: Request) -> MetricsReads: ...   # until bound: RuntimeError("not bound: get_metrics_reads")
def get_request_context(request: Request) -> RequestContext: ...
def get_login_sessions(request: Request) -> LoginSessions: ...
def get_staff_access(request: Request) -> StaffAccess: ...
def get_heartbeat(request: Request) -> HeartbeatReader: ...
def get_rate_limiter(request: Request) -> RateLimiter: ...
RESET_GATE: Key[ResetGate] = Key("reset_gate")

def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]:
    # Depends(get_login_session) + Depends(get_staff_access); access.actor_for(session, roles);
    # RoleRefusal -> ApiProblem(403, ApiErrorCode.ROLE_NOT_ALLOWED,
    #     details={"role": result.role.value, "needs": [r.value for r in result.needs], "reason": result.reason})
```

### 4.2 Middleware, errors, logging, domain

```python
# meridian.web.middleware
@dataclass(frozen=True)
class RequestContext:
    request_id: RequestId; client_ip: str; session: LoginSession | None
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; turn_verdict: LimitVerdict | None
class WebShellState: ...                    # app.state.web_shell; present only on apps create_app built
class LimitScope(StrEnum): THREAD="thread"; SESSION="session"; IP="ip"; LOGIN_IP="login_ip"; RESET_IP="reset_ip"
@dataclass(frozen=True)
class LimitVerdict: allowed: bool; scope: LimitScope | None; retry_after_ms: int | None
ALLOWED = LimitVerdict(allowed=True, scope=None, retry_after_ms=None)
class RateLimiter:
    def __init__(self, limits: WebLimits) -> None: ...
    def peek(self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read") -> LimitVerdict: ...
    def check(self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read") -> LimitVerdict: ...
OPERATIONS_BY_ROUTE[("GET", "/api/staff/owner-metrics")] == "getOwnerMetrics"   # also getMonitoring, getLatestEval
RATE_LIMITED_READ_OPERATIONS ⊇ {"getMonitoring", "getLatestEval"}   # SESSION then IP read buckets; 429 details {"retry_after_ms": n}
RESET_503_OPERATIONS ⊇ {"getMonitoring", "getLatestEval"}           # 503 details {"retry_after_ms": 5000}, at once
# getOwnerMetrics is in neither: never limited; during a reset the gate waits limits.web.reset_wait_s (5) then the route runs.
# The login route calls limiter.peek(LimitScope.LOGIN_IP, ...) — a refusing double must allow LOGIN_IP.
# The request record: {"record": "request", "request_id", "route" (template), "status", "duration_ms",
#   "caller_role" ("anonymous" | DemoRole value), "thread_id": None, "error_kind" only when status >= 500}
#   error_kind = the middleware's own kind (e.g. "RESET_IN_PROGRESS" for its 503), else request.state.error_kind,
#   else f"http_{status}".

# meridian.web.errors
def render_unhandled_error(request_id: str) -> JSONResponse:
    # 500 with body {"request_id": request_id} and header X-Request-ID (no ApiError code exists for a generic 500)

# meridian.web.logging: AllowListFormatter reduces any plain log message to {"record": "log", "logger", "level",
#   "length"}; only "request", "auth_event", "stream_reconnect", "signal" records keep their fields.

# meridian.domain.staff
class DemoRole(StrEnum): CUSTOMER="customer"; REPRESENTATIVE="representative"; SUPERVISOR="supervisor"; OWNER="owner"
class StaffRole(StrEnum): REPRESENTATIVE="representative"; SUPERVISOR="supervisor"; OWNER="owner"
```

### 4.3 Container (`meridian.web.container`)

```python
class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    def build(self) -> None: ...
def register_web(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None: ...   # AEA-23
def register_reads(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-48 reads API: CON-18 to CON-20 routes (staff.md §9).

    No-op until AEA-48 fills it.
    """
```
Rules from existing tests: the docstring must keep the text `AEA-48` and must **not** contain `No-op until`
(`tests/unit/web/test_container.py::test_every_register_stub_present`); imports stay **inside** the function
(`tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`).

### 4.4 Test helpers to reuse (read only)

From `tests/api/web_shell_support.py`: `make_settings(tmp_path, **changes)` · `make_client(app, *, peer="198.51.100.7")`
(context manager; runs the lifespan; `raise_server_exceptions=False`) · `FakeSessionStore` (`.issue(role) -> token`,
`.session_of(token)`, `.set_role(token, role, *, role_reset=False)`; `start()` mints a CUSTOMER session; implements
`actor_for` with real `RoleRefusal` values) · `FakeHeartbeat()` · `cookie_header(token)` · `login(client, settings)` ·
`session_cookie_value(response)` · `error_body(response, status, code) -> dict` · `assert_matches(response, operation_id)` ·
`captured_log()` (allow-list JSON lines) · `log_records(stream)` · `records_of(stream, kind)` · `app_log_text(caplog)` ·
`all_output_text(responses)` · `rand_word(length=16, prefix="zq")` (letters only) · `reset_gate_of(app)` ·
`effective_routes(app)` · `full_app(monkeypatch, settings, *, store, heartbeat)` (the **real** `build_container`, every
hunk, starters suppressed).
From `tests/api/openapi_check.py`: `load_document()` (timestamps stay strings), `load_contract()`.
From `tests/fakes/clock.py`: `CHICAGO = ZoneInfo("America/Chicago")`.
`meridian.web.app`: `create_app(settings)`; `import meridian.web.app as app_module` to monkeypatch `build_container`.
`meridian.policy.limits.WebLimits`, `meridian.policy.limits.Limits`.

---

## 5. Steps (build order; each step is checkable on its own)

The slice sits in area **A10b Reads** (DO-3 §3, §8). `web/routes/reads.py` depends on `web/deps.py` (the `MetricsReads`
Protocol and providers), `web/errors.py`, `web/middleware.RequestContext`, `web/schemas/reads.py` and `domain/staff`;
it never imports a service or adapter. The interface it consumes is web.md §4 `MetricsReads`; the interface it
produces is the three operations plus the public models and helpers of `schemas/reads.py`, which AEA-53's tests import.
No new seam.

### Step 0 — check the base

`export UV_LINK_MODE=hardlink`; `git log --oneline -1`; `grep -n "def register_reads" -A5 src/meridian/web/container.py`
shows the "No-op until AEA-48 fills it." stub; `ls src/meridian/web/routes/reads.py` fails (not yet there);
`uv run python -c "import meridian.web.app"` succeeds. No baseline suite.

### Step 1 — `src/meridian/web/schemas/reads.py` (create; exact text, 308 lines after `ruff format`)

Names are load-bearing (tests and AEA-53 import them): `ReadModel`, `Measure`, `Tile`, `EvalMeasure`, `NorthStarLink`,
`MissedPromise`, `CaseLine`, `OwnerMetricsResponse`, `Spend`, `Correctness`, `MonitorAlert`, `QuietHours`,
`AlertConfig`, `LastRestart`, `MonitoringResponse`, `MixRow`, `DevFailure`, `EvalRun`, `EvalSplits`, `EvalResponse`,
`MeasureUnit`, `MEASURE_UNITS`, `SHARE_OUT_OF_RANGE`, `RATIO_OUT_OF_RANGE`, `DUPLICATE_MEASURE`, `OWN_RULES`,
`describe_errors`, `dropped_keys`.

Why each rule (the invariant it protects):
1. `extra="ignore"` drops undocumented keys so nothing outside the OpenAPI reaches a client (R-36, AC-4).
2. `hide_input_in_errors=True` and `describe_errors(... include_input=False ...)` keep values out of every message (AC-5).
3. Time fields are `AwareDatetime`: a reader string like `2026-10-16T14:20:00-05:00` round-trips unchanged; a
   `datetime` object serialises in ISO form (UTC as `Z`); a naive time (no offset) is refused (it would break the
   OpenAPI `date-time` check). No field is stamped here.
4. Numbers are `int | float` (smart union): `18` stays `18`, `0.75` stays `0.75` (prototyped), so bodies equal mappings.
5. Share/ratio checks and the duplicate check raise `PydanticCustomError` with a `{"field": ...}` context naming the
   path, which `describe_errors` appends; the message never contains the value.
6. Uniqueness is per response on CON-18 and CON-19, and per `EvalRun.measures` on CON-20 (the OpenAPI's own BOTH_SPLITS
   example repeats `E-1 / Correct resolution` in dev, held_out and headline, so a response-wide rule would refuse the
   contract's own example; §8 R-4).

```python
"""Wire shapes for CON-18 to CON-20 (OpenAPI OwnerMetricsResponse, MonitoringResponse, EvalResponse). AEA-48.

The routes validate each MetricsReads mapping through these models (stage7/staff.md section 9, STF-17). Field names and
shapes are copied from the OpenAPI. Unknown keys are ignored here and named by the route (dropped_keys); a missing
required field or a broken rule raises ValidationError, which the route answers with 500. Three rules are stricter than
the OpenAPI (AEA-48-1): `unit` is count, ms or share; a share and every evaluation value lie in [0, 1]; and (id, label)
pairs are unique within one response (per run on CON-20, where the two splits and the headline repeat ids by design).
The reader stamps every time field; these models only check that each carries a UTC offset.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Mapping, Sequence
from typing import Final, Literal, Self, get_args

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError, model_validator
from pydantic_core import PydanticCustomError

MeasureUnit = Literal["count", "ms", "share"]
MEASURE_UNITS: Final[tuple[str, ...]] = get_args(MeasureUnit)
SHARE_OUT_OF_RANGE: Final = "share_out_of_range"
RATIO_OUT_OF_RANGE: Final = "ratio_out_of_range"
DUPLICATE_MEASURE: Final = "duplicate_measure"
OWN_RULES: Final[frozenset[str]] = frozenset({SHARE_OUT_OF_RANGE, RATIO_OUT_OF_RANGE, DUPLICATE_MEASURE})
_FIELD: Final = "field"  # the context key our own rules use to name the field they refuse
_MAX_ERRORS: Final = 10


class ReadModel(BaseModel):
    """Plain BaseModel, not MeridianModel: values pass through unchanged (no whitespace stripping) and extras drop."""

    model_config = ConfigDict(extra="ignore", frozen=True, hide_input_in_errors=True)


def _in_unit_range(value: int | float | None) -> bool:
    return value is None or 0 <= value <= 1


class Measure(ReadModel):
    id: str
    label: str
    numerator: int | None
    denominator: int | None
    unit: MeasureUnit
    value: int | float | None
    null_reason: str | None
    kind: Literal["measured", "estimate"]
    case_refs: list[str]

    @model_validator(mode="after")
    def _share_in_range(self) -> Self:
        if self.unit == "share" and not _in_unit_range(self.value):
            raise PydanticCustomError(
                SHARE_OUT_OF_RANGE, "a share value must lie in [0, 1]", {_FIELD: "value"}
            )
        return self


class Tile(ReadModel):
    id: str
    label: str
    value: int | float | None
    unit: MeasureUnit
    numerator: int | None
    denominator: int | None
    null_reason: str | None

    @model_validator(mode="after")
    def _share_in_range(self) -> Self:
        if self.unit == "share" and not _in_unit_range(self.value):
            raise PydanticCustomError(
                SHARE_OUT_OF_RANGE, "a share value must lie in [0, 1]", {_FIELD: "value"}
            )
        return self


class EvalMeasure(ReadModel):
    id: str
    label: str
    numerator: int
    denominator: int
    value: int | float
    min: int | float | None
    max: int | float | None
    target: str | None

    @model_validator(mode="after")
    def _ratio_in_range(self) -> Self:
        if not _in_unit_range(self.value):
            raise PydanticCustomError(
                RATIO_OUT_OF_RANGE, "an evaluation value must lie in [0, 1]", {_FIELD: "value"}
            )
        return self


def _indexed(
    name: str, items: Sequence[Measure | Tile | EvalMeasure]
) -> list[tuple[str, Measure | Tile | EvalMeasure]]:
    return [(f"{name}[{index}]", item) for index, item in enumerate(items)]


def _refuse_duplicates(items: Iterable[tuple[str, Measure | Tile | EvalMeasure]]) -> None:
    """Raise on the second occurrence of an (id, label) pair, naming its path, never its values."""
    seen: set[tuple[str, str]] = set()
    for path, item in items:
        pair = (item.id, item.label)
        if pair in seen:
            raise PydanticCustomError(
                DUPLICATE_MEASURE, "(id, label) pairs must be unique within one response", {_FIELD: path}
            )
        seen.add(pair)


# -- CON-18 getOwnerMetrics ------------------------------------------------------------------------------------
class NorthStarLink(ReadModel):
    label: str
    path: Literal["/eval"]


class MissedPromise(ReadModel):
    reference: str
    due_at: AwareDatetime
    outcome: str


class CaseLine(ReadModel):
    reference: str
    reason: str
    status: str


class OwnerMetricsResponse(ReadModel):
    as_of: AwareDatetime  # demo clock, stamped by the reader (STF-22)
    seeds_included: bool
    seed_count: int
    in_scope_correct_resolution: Measure
    measured_north_star_link: NorthStarLink
    promises_kept_on_time: Measure
    handoffs: Measure
    outcomes: list[Measure]
    handoffs_by_reason: list[Measure]
    missed_promises: list[MissedPromise]
    cases: list[CaseLine]

    @model_validator(mode="after")
    def _unique_measures(self) -> Self:
        _refuse_duplicates(
            [
                ("in_scope_correct_resolution", self.in_scope_correct_resolution),
                ("promises_kept_on_time", self.promises_kept_on_time),
                ("handoffs", self.handoffs),
                *_indexed("outcomes", self.outcomes),
                *_indexed("handoffs_by_reason", self.handoffs_by_reason),
            ]
        )
        return self


# -- CON-19 getMonitoring --------------------------------------------------------------------------------------
class Spend(ReadModel):
    today_cents: int
    cap_cents: int
    day: Literal["America/Chicago midnight to midnight"]
    resets_at: AwareDatetime


class Correctness(ReadModel):
    containment_estimate: Tile
    escalations_by_reason: list[Tile]


class MonitorAlert(ReadModel):
    type: Literal[
        "spend_cap_reached",
        "p95_latency_over_12_5s",
        "health_check_restart",
        "zero_traffic",
        "failure_rate_over_2pct",
        "trace_export_failed",
    ]
    state: Literal["firing", "quiet"]
    fired_at: AwareDatetime | None
    decision_line: str


class QuietHours(ReadModel):
    start: str
    end: str
    timezone: str
    configurable: Literal[True]


class AlertConfig(ReadModel):
    zero_traffic_after_hours: int
    quiet_hours: QuietHours


class LastRestart(ReadModel):
    at: AwareDatetime
    kind: Literal["health_check"]


class MonitoringResponse(ReadModel):
    as_of: AwareDatetime  # wall clock, stamped by the reader (the OpenAPI's one documented exception)
    demo_now: AwareDatetime  # demo clock, stamped by the reader
    health: list[Tile]
    spend: Spend
    correctness: Correctness
    alerts: list[MonitorAlert]
    alert_config: AlertConfig
    last_restart: LastRestart | None
    trace_export: str
    redacted: Literal[True]

    @model_validator(mode="after")
    def _unique_tiles(self) -> Self:
        _refuse_duplicates(
            [
                *_indexed("health", self.health),
                ("correctness.containment_estimate", self.correctness.containment_estimate),
                *_indexed("correctness.escalations_by_reason", self.correctness.escalations_by_reason),
            ]
        )
        return self


# -- CON-20 getLatestEval --------------------------------------------------------------------------------------
class MixRow(ReadModel):
    category: str
    count: int
    origin: Literal["transcript", "synthetic"]
    tests: str | None


class DevFailure(ReadModel):
    case_id: str
    redacted_summary: str


class EvalRun(ReadModel):
    run_id: str
    date: dt.date
    agent_version: str
    size: int
    mix: list[MixRow]
    measures: list[EvalMeasure]
    dev_failures: list[DevFailure]

    @model_validator(mode="after")
    def _unique_measures(self) -> Self:
        _refuse_duplicates(_indexed("measures", self.measures))
        return self


class EvalSplits(ReadModel):
    dev: EvalRun | None
    held_out: EvalRun | None


class EvalResponse(ReadModel):
    splits: EvalSplits
    headline: EvalMeasure | None
    current_agent_version: str
    dev_label: str


# -- helpers the route (and AEA-53's tests) use ---------------------------------------------------------------
def _path(loc: Sequence[int | str]) -> str:
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}" if out else part
    return out


def describe_errors(exc: ValidationError) -> tuple[tuple[str, str], ...]:
    """(field, rule) per error, at most ten: the dotted location and the pydantic error type. Never an input value."""
    found: list[tuple[str, str]] = []
    for error in exc.errors(include_url=False, include_input=False, include_context=True)[:_MAX_ERRORS]:
        field = _path(error["loc"])
        named = (error.get("ctx") or {}).get(_FIELD) if error["type"] in OWN_RULES else None
        if isinstance(named, str):
            field = f"{field}.{named}" if field else named
        found.append((field or "(response)", error["type"]))
    return tuple(found)


def dropped_keys(raw: object, kept: object) -> tuple[str, ...]:
    """Dotted paths of keys in `raw` that are absent from `kept` (list positions written `[]`), sorted, unique."""
    found: set[str] = set()
    _walk(raw, kept, "", found)
    return tuple(sorted(found))


def _walk(raw: object, kept: object, at: str, found: set[str]) -> None:
    if isinstance(raw, Mapping) and isinstance(kept, Mapping):
        for key, value in raw.items():
            name = f"{at}.{key}" if at else str(key)
            if key in kept:
                _walk(value, kept[key], name, found)
            else:
                found.add(name)
    elif isinstance(raw, list | tuple) and isinstance(kept, list):
        for raw_item, kept_item in zip(raw, kept, strict=False):
            _walk(raw_item, kept_item, f"{at}[]", found)
```

Check: `uv run python -c "from meridian.web.schemas.reads import EvalResponse, describe_errors, dropped_keys"`.

### Step 2 — `src/meridian/web/routes/reads.py` (create; exact text, 116 lines)

The algorithm of `_answer` (each step's invariant):
1. `model.model_validate(raw)` — exactly one reader call happened before this (the caller passes the result in), so a
   request calls its reader method once (AC-2).
2. On `ValidationError`: build `"<field> <rule>"` pairs from `describe_errors(exc)` (paths and error types only), log
   **one** ERROR line, set `request.state.error_kind = "reads_schema_violation"` (the middleware copies it into the
   request record, AC-13), return `render_unhandled_error(ctx.request_id)` (500, body `{"request_id"}`). Nothing is
   raised, so no traceback with values is logged anywhere (AC-5, AC-10).
3. On success: `body = payload.model_dump(mode="json")`; `dropped_keys(raw, body)`; if any, **one** WARNING naming them
   (keys only, AC-4); return `JSONResponse(body)`.
4. The role check is a **route-level** dependency on `getOwnerMetrics` (`dependencies=[Depends(...)]`): FastAPI solves
   route dependencies before the endpoint's parameters, so a refused role gets 403 even while `get_metrics_reads` is
   unbound, and the reader is never called (prototyped: representative → 403, owner with unbound reader → 500
   `RuntimeError`).

```python
"""CON-18 to CON-20 reads: getOwnerMetrics, getMonitoring, getLatestEval (stage7/staff.md section 9). AEA-48.

Each route makes exactly one MetricsReads call (web.md section 4, MC-6), validates the mapping through
web/schemas/reads.py and returns it field for field. It computes nothing, stamps nothing and reads no clock: the reader
stamps every time field (STF-22, MC-5). Unknown keys are dropped with one warning naming them, never their values; a
mapping that breaks the schema answers 500 with one log line naming the field and rule (STF-17, AEA-48-1). Limits and
the reset gate are the middleware's (web.md sections 5 and 7); getOwnerMetrics alone needs owner or supervisor (MC-4).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Final

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from meridian.domain.staff import StaffRole
from meridian.web.deps import MetricsReads, get_metrics_reads, get_request_context, require_staff
from meridian.web.errors import render_unhandled_error
from meridian.web.middleware import RequestContext
from meridian.web.schemas.reads import (
    EvalResponse,
    MonitoringResponse,
    OwnerMetricsResponse,
    ReadModel,
    describe_errors,
    dropped_keys,
)

OWNER_METRICS_PATH: Final = "/api/staff/owner-metrics"
MONITORING_PATH: Final = "/api/monitoring"
LATEST_EVAL_PATH: Final = "/api/eval/latest"
OWNER_METRICS_OPERATION: Final = "getOwnerMetrics"
MONITORING_OPERATION: Final = "getMonitoring"
LATEST_EVAL_OPERATION: Final = "getLatestEval"
READS_LOGGER: Final = "meridian.web.reads"
SCHEMA_VIOLATION: Final = "reads_schema_violation"  # the request record's error_kind on the 500
_OWNER_OR_SUPERVISOR = require_staff(
    StaffRole.OWNER, StaffRole.SUPERVISOR
)  # x-roles order: [owner, supervisor]
_log = logging.getLogger(READS_LOGGER)


def _answer(
    request: Request,
    ctx: RequestContext,
    operation_id: str,
    model: type[ReadModel],
    raw: Mapping[str, object],
) -> Response:
    try:
        payload = model.model_validate(raw)
    except ValidationError as exc:
        refused = "; ".join(f"{field} {rule}" for field, rule in describe_errors(exc))
        _log.error("%s: reader mapping refused: %s", operation_id, refused)
        request.state.error_kind = SCHEMA_VIOLATION
        return render_unhandled_error(ctx.request_id)
    body = payload.model_dump(mode="json")
    dropped = dropped_keys(raw, body)
    if dropped:
        _log.warning("%s: dropped keys not in the OpenAPI: %s", operation_id, ", ".join(dropped))
    return JSONResponse(body)


def get_owner_metrics(
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    reads: MetricsReads = Depends(get_metrics_reads),  # noqa: B008
) -> Response:
    return _answer(request, ctx, OWNER_METRICS_OPERATION, OwnerMetricsResponse, reads.owner_metrics())


def get_monitoring(
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    reads: MetricsReads = Depends(get_metrics_reads),  # noqa: B008
) -> Response:
    return _answer(request, ctx, MONITORING_OPERATION, MonitoringResponse, reads.monitoring())


def get_latest_eval(
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    reads: MetricsReads = Depends(get_metrics_reads),  # noqa: B008
) -> Response:
    return _answer(request, ctx, LATEST_EVAL_OPERATION, EvalResponse, reads.latest_eval())


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        OWNER_METRICS_PATH,
        get_owner_metrics,
        methods=["GET"],
        operation_id=OWNER_METRICS_OPERATION,
        response_model=None,
        dependencies=[Depends(_OWNER_OR_SUPERVISOR)],  # route dependencies run before the endpoint's own
    )
    router.add_api_route(
        MONITORING_PATH,
        get_monitoring,
        methods=["GET"],
        operation_id=MONITORING_OPERATION,
        response_model=None,
    )
    router.add_api_route(
        LATEST_EVAL_PATH,
        get_latest_eval,
        methods=["GET"],
        operation_id=LATEST_EVAL_OPERATION,
        response_model=None,
    )
    return router
```

(You may move the `# x-roles order` comment onto its own line above `_OWNER_OR_SUPERVISOR`; `ruff format` decides the
rest.)

### Step 3 — the hunk in `src/meridian/web/container.py` (modify `register_reads` only)

Replace the stub's docstring and body with exactly:

```python
def register_reads(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-48 reads API: the CON-18 to CON-20 routes (staff.md §9).

    Includes routes/reads.py's router (getOwnerMetrics, getMonitoring, getLatestEval) once per app. Provides nothing:
    the routes reach the reader through web/deps.py's get_metrics_reads(), which AEA-53's register_metrics_reader hunk
    binds; until then an allowed read answers 500 ("not bound: get_metrics_reads") after the role check. An app that
    create_app did not build has no web shell, so this does nothing.
    """
    from meridian.web.middleware import WebShellState
    from meridian.web.routes.reads import build_router

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    if getattr(app.state, "reads_routes_included", False):
        return  # a second lifespan on the same app must not add the routes again (FastAPI includes lazily)
    app.include_router(build_router())
    app.state.reads_routes_included = True
```

Check: `uv run pytest -q tests/unit/web/test_container.py tests/unit/test_import_direction.py`.

### Step 4 — `tests/api/reads_support.py` (create; ≤ 230 lines; spec in §6)

### Step 5 — `tests/api/test_reads_routes.py` and `tests/api/test_reads_router.py` (create; tests in §7.1)

`test_reads_routes.py` ≤ 500 lines (hard cap): keep setup in `reads_support.py`.

### Step 6 — contract cases: `tests/contract/cases/reads.py` + `tests/api/test_contract_cases_reads.py`

`tests/contract/cases/reads.py`, exact content:

```python
"""Server contract cases for CON-18 `getOwnerMetrics`, CON-19 `getMonitoring`, CON-20 `getLatestEval`, owned by AEA-48
(AC-11, AEA-48-2).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, AEA-48's
tests/api/test_contract_cases_reads.py drives them. Until AEA-53 binds the reader, a runner on the real app skips the
200 cases as `not bound: get_metrics_reads`. Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie (the session starts as customer);
                 "role:<owner|supervisor|representative|customer>" = then act as that role (switchRole, CON-10, on the
                 real app; the local driver sets the role on its session-store double).
  setup: "reset_gate_held" = hold the app's ResetGate during the request (the middleware answers 503);
         "rate_limited" = the rate limiter refuses the SESSION and IP read buckets for the request (429).
  reader_example: the OpenAPI 200 example the local driver's MetricsReads double returns; a runner with the real reader
                  ignores it.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "reads"
CASES: Final[dict[str, dict[str, object]]] = {
    "getOwnerMetrics": {
        "public": False,
        "drives": (
            {"name": "owner_seeded", "status": 200, "preconditions": ("login", "role:owner"), "reader_example": "SEEDED"},
            {"name": "supervisor_empty", "status": 200, "preconditions": ("login", "role:supervisor"), "reader_example": "EMPTY"},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": ()},
            {"name": "representative", "status": 403, "code": "ROLE_NOT_ALLOWED", "preconditions": ("login", "role:representative")},
        ),
    },
    "getMonitoring": {
        "public": False,
        "drives": (
            {"name": "customer_default", "status": 200, "preconditions": ("login",), "reader_example": "DEFAULT"},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": ()},
            {"name": "rate_limited", "status": 429, "code": "REQUEST_RATE_LIMITED", "preconditions": ("login",), "setup": "rate_limited"},
            {"name": "reset_running", "status": 503, "code": "RESET_IN_PROGRESS", "preconditions": ("login",), "setup": "reset_gate_held"},
        ),
    },
    "getLatestEval": {
        "public": False,
        "drives": (
            {"name": "owner_both_splits", "status": 200, "preconditions": ("login", "role:owner"), "reader_example": "BOTH_SPLITS"},
            {"name": "customer_no_run", "status": 200, "preconditions": ("login",), "reader_example": "NO_RUN"},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": ()},
            {"name": "rate_limited", "status": 429, "code": "REQUEST_RATE_LIMITED", "preconditions": ("login",), "setup": "rate_limited"},
            {"name": "reset_running", "status": 503, "code": "RESET_IN_PROGRESS", "preconditions": ("login",), "setup": "reset_gate_held"},
        ),
    },
}
```
(`ruff format` will split the long dict lines; keep the content.)

`tests/api/test_contract_cases_reads.py`, one test, `test_reads_cases_drive_documented_statuses(monkeypatch, tmp_path)`
(docstring: "invariant (AC-11): each case yields its status and code; every documented error status is covered"):
1. `assert ROUTE_FILE == "reads"`; `assert set(CASES) == {"getOwnerMetrics", "getMonitoring", "getLatestEval"}`.
2. For each operation id and each case in `CASES[op]["drives"]`: `settings = make_settings(tmp_path / op / case["name"])`;
   `reads = FakeMetricsReads()`; if `"reader_example" in case`: `reads.returns[op] = example(op, case["reader_example"])`
   (and assert the name is in `EXAMPLE_NAMES[op]`); `h = reads_app(monkeypatch, settings, reads=reads)`;
   `with make_client(h.app) as client:` run the preconditions in order — `"login"`: `token = session_cookie_value(login(client, settings))`,
   assert truthy, `headers = cookie_header(token)`; `"role:<r>"`: `h.store.set_role(token, DemoRole(r))`; anything else:
   `raise AssertionError(f"unknown precondition {step!r}")`. Then by `case.get("setup")`: `"reset_gate_held"` → inside
   `with reset_gate_of(h.app).hold():` send; `"rate_limited"` → `h.app.dependency_overrides[get_rate_limiter] = lambda: RefusingLimiter()`
   then send; `None` → send; any other → `AssertionError`. Send = `get_read(client, op, headers)` (headers `{}` when no
   login).
3. Assert `response.status_code == case["status"]`; if `"code" in case`: `response.json()["error"]["code"] == case["code"]`;
   `assert_matches(response, op)`; 200 cases: `reads.calls == [op]` and `response.json() == reads.returns[op]`; other cases:
   `reads.calls == []`. Add the status string to `covered[op]`; print `f"{op}/{case['name']}: {response.status_code}"`.
4. After the loop, for each op: `{s for s in load_contract().operations[op].responses if int(s) >= 400} <= covered[op]`
   and `"200" in covered[op]`; total cases run `== 13`.

### Step 7 — journey (AC-12): `tests/journeys/j10/test_aea_48.py`

```python
"""J-10 read leg (AEA-48). **Level today: mock-tested** - the real AEA-23 app and middleware in process with AEA-48's
router, the real login route over a session-store double, and a MetricsReads double whose mappings stand in for the
stored aggregates; no server, no browser, no DB copy. Blocked steps: the same three reads over MetricsReader on stored
rows (AEA-53, which lands J-10) and the integrated run (AEA-57 harness). Stored side at this level: the double's
mappings only.
"""
```
- `pytestmark = pytest.mark.journey`.
- `test_j10_read_pages_show_stored_values(monkeypatch, tmp_path)`:
  1. `reads = FakeMetricsReads()` (SEEDED, DEFAULT, BOTH_SPLITS); `stored = copy.deepcopy(reads.returns)`.
  2. `settings = make_settings(tmp_path)`; `h = reads_app(monkeypatch, settings, reads=reads)`; `with make_client(h.app) as client:`
     `token = session_cookie_value(login(client, settings))`; assert token; `h.store.set_role(token, DemoRole.OWNER)`;
     `bodies = {op: get_read(client, op, cookie_header(token)) for op in OPERATIONS}`.
  3. For each op: status 200, `assert_matches(r, op)`, `r.json() == stored[op]` (what the user sees equals what is stored).
  4. `measures = all_measures({op: r.json() for op, r in bodies.items()})` (helper in §6). For each: `m["label"]` is a
     non-empty `str`; if `"unit" in m`: `m["unit"] in MEASURE_UNITS`; if `m.get("unit") == "share"` and `m["value"] is not
     None`: `m["denominator"]` is an `int` > 0 and `0 <= m["value"] <= 1`; for `EvalMeasure`s (no `"unit"` key):
     `m["denominator"] > 0` and `0 <= m["value"] <= 1`. Print the unit set and the number of measures checked.
  5. `reads.calls == list(OPERATIONS)` (one stored read per page, nothing recomputed).
- `test_j10_read_pages_from_metrics_reader_on_db_copy() -> None:` `pytest.skip("blocked: MetricsReader over stored rows on
  the DB copy (AEA-53, lands J-10); journey harness (AEA-57)")`.

Record `docs/testing/journeys/<YYYY-MM-DD>-AEA-48.md` (copy the AEA-47 record's table shape:
`docs/testing/journeys/2026-10-21-AEA-47.md`): **Claim** CON-18…CON-20 reads (AC-1…AC-13) at TestClient level with
doubles; the J-10 read leg (the three pages show the double's stored mappings field for field, units ⊆ {count, ms,
share}, shares with denominators); **Level** `mock-tested`; **Tested revision** "the commit that adds this record, on
branch <branch> (code commit <sha>)"; **Environment** VPS, Python 3.12, FastAPI TestClient in process, no port, no
browser; `FakeSessionStore`, `FakeMetricsReads`, `RefusingLimiter` doubles; no model call; **Command** the §7.3 test,
journey and contract-case commands; **Result** the pass/skip counts you saw; **Evidence location** GitLab issue #48
comment, this file; **Remaining limitations** no real `MetricsReader` or stored rows (AEA-53, CAP-6); dropped-key names
are visible in log capture, not in deployed stdout (allow-list formatter); the strict contract run waits for AEA-59;
**Blocked by** AEA-57 (harness), AEA-53 (reader, J-10 lands), AEA-59 (strict contract run); **Journeys that will exercise
this code** J-10 (and AEA-55's UI integration). No code digits, password or personal data.

### Step 8 — fast gates, affected tests, affected journeys (§7.3); fix until green

### Step 9 — context rows (AC-14), in the same change as the code

1. `.claude/reference/area-map.md`, row **A10b Reads** (`grep -n "A10b Reads" .claude/reference/area-map.md`; line 41 on
   `main`), *Status* cell, currently `planned`: replace with `partly built: AEA-48 (<short sha>): web/routes/reads.py,
   web/schemas/reads.py, register_reads hunk; services/metrics_reader.py planned (AEA-53)`.
2. `.claude/state/icm-progress.md`: add one row directly after the AEA-47 row (the one containing
   `web/routes/staff_clock.py`), ≤ 400 characters:
   `| Routes verified against code and tests | provisional | <date>: area map A10b → web/routes/reads.py,
   web/schemas/reads.py (AEA-48, <short sha>) checked against tests/api/test_reads_routes.py, test_reads_router.py,
   test_contract_cases_reads.py (<N> passed); record docs/testing/journeys/<date>-AEA-48.md | Reader (AEA-53) still
   planned; verified when every area-map row is actual |`
3. `docs/design/code-design.md`, the line `│   └── routes/reads.py · schemas/reads.py       CON-18…CON-20 (AEA-48; reader: AEA-53)                      A10b  2–3`
   (line 314 on `main`): append `   built AEA-48 <short sha>` at the end (format of `built AEA-47 0d75351`).
4. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in files you own.

`<short sha>` is the implementation commit: commit the code first, then the three doc edits and the journey record as a
second commit naming that sha. Amend nothing.

### Step 10 — commit

`git add` exactly the owned paths that changed (never `-A`):
`git add src/meridian/web/routes/reads.py src/meridian/web/schemas/reads.py src/meridian/web/container.py
tests/api/reads_support.py tests/api/test_reads_routes.py tests/api/test_reads_router.py
tests/api/test_contract_cases_reads.py tests/contract/cases/reads.py tests/journeys/j10/test_aea_48.py`, commit
`feat(web): CON-18…CON-20 read routes and schemas (AEA-48)`; then
`git add docs/testing/journeys/<date>-AEA-48.md .claude/reference/area-map.md .claude/state/icm-progress.md
docs/design/code-design.md`, commit `docs(AEA-48): journey record and context rows`. Each message ends with the last line
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Commit on your branch only; no push (only the merge step
pushes `main`), no force-push.

---

## 6. Data and fixtures (all synthetic; spec of `tests/api/reads_support.py`)

Sources: the twelve OpenAPI 200 examples, read at test time with `load_document()` (synthetic values the contract labels
"made-up"); `tests/fakes/clock.CHICAGO`. Distinctive strings come from `rand_word(...)` (letters only). No digits that
resemble a code, card or phone number; IPs are the default documentation peer.

```python
"""AEA-48 test support: a MetricsReads double (web.md section 4), a refusing rate limiter, and an app builder that runs
AEA-23's register_web plus AEA-48's register_reads. Not a conftest. Synthetic values only (the OpenAPI examples)."""

from __future__ import annotations
# imports: copy, logging, threading, time; collections.abc (Callable, Iterator, Mapping); contextlib (contextmanager);
# dataclasses (dataclass); typing (Any, Literal, cast); pytest; fastapi (FastAPI); import meridian.web.app as app_module;
# meridian.config.Settings; meridian.domain.staff.DemoRole; meridian.policy.limits (Limits, WebLimits);
# meridian.web.app.create_app; meridian.web.container (Container, register_reads, register_web);
# meridian.web.deps (get_heartbeat, get_login_sessions, get_metrics_reads, get_rate_limiter, get_staff_access);
# meridian.web.middleware (ALLOWED, LimitScope, LimitVerdict, RateLimiter);
# meridian.web.routes.reads (LATEST_EVAL_PATH, MONITORING_PATH, OWNER_METRICS_PATH, READS_LOGGER);
# tests.api.openapi_check.load_document; tests.api.web_shell_support (FakeHeartbeat, FakeSessionStore, cookie_header,
# reset_gate_of)

OPERATIONS: dict[str, str] = {            # operation id -> path, in this order everywhere
    "getOwnerMetrics": OWNER_METRICS_PATH,
    "getMonitoring": MONITORING_PATH,
    "getLatestEval": LATEST_EVAL_PATH,
}
EXAMPLE_NAMES: dict[str, tuple[str, ...]] = {
    "getOwnerMetrics": ("SEEDED", "EMPTY"),
    "getMonitoring": ("DEFAULT", "FIRING", "TOO_FEW_TURNS", "EMPTY", "ZERO_TRAFFIC_FIRING", "FAILURE_AND_TRACE_FIRING"),
    "getLatestEval": ("BOTH_SPLITS", "DEV_ONLY", "STALE_RUN", "NO_RUN"),
}
DEFAULT_EXAMPLE: dict[str, str] = {"getOwnerMetrics": "SEEDED", "getMonitoring": "DEFAULT", "getLatestEval": "BOTH_SPLITS"}
RETRY_AFTER_MS = 7000                     # the refusing limiter's verdict


def example_names(operation_id: str) -> tuple[str, ...]:
    """The 200 example names in the OpenAPI, in file order (drift guard for EXAMPLE_NAMES)."""
    # load_document()["paths"][OPERATIONS[op]]["get"]["responses"]["200"]["content"]["application/json"]["examples"]


def example(operation_id: str, name: str) -> dict[str, Any]:
    """A deep copy of the named 200 example's value (so a test may mutate it)."""


class FakeMetricsReads:
    """MetricsReads double. `returns[op]` is what the matching method returns (default: DEFAULT_EXAMPLE per op, deep
    copies); `calls` lists operation ids in call order; when `probe` is set, `held_at_call` records probe() per call."""

    def __init__(self, returns: Mapping[str, object] | None = None) -> None:
        self.returns: dict[str, object] = (
            dict(returns) if returns is not None else {op: example(op, DEFAULT_EXAMPLE[op]) for op in OPERATIONS}
        )
        self.calls: list[str] = []
        self.probe: Callable[[], bool] | None = None
        self.held_at_call: list[bool] = []

    def _read(self, operation_id: str) -> Mapping[str, object]:
        self.calls.append(operation_id)
        if self.probe is not None:
            self.held_at_call.append(self.probe())
        return cast(Mapping[str, object], self.returns[operation_id])

    def owner_metrics(self) -> Mapping[str, object]: return self._read("getOwnerMetrics")
    def monitoring(self) -> Mapping[str, object]: return self._read("getMonitoring")
    def latest_eval(self) -> Mapping[str, object]: return self._read("getLatestEval")


class RefusingLimiter(RateLimiter):
    """Refuses the SESSION and IP read buckets (the 429 path); allows LOGIN_IP, THREAD and RESET_IP, so login works."""

    def __init__(self) -> None:
        super().__init__(WebLimits())

    def _verdict(self, scope: LimitScope) -> LimitVerdict:
        if scope in (LimitScope.SESSION, LimitScope.IP):
            return LimitVerdict(allowed=False, scope=scope, retry_after_ms=RETRY_AFTER_MS)
        return ALLOWED

    def peek(self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read") -> LimitVerdict:
        return self._verdict(scope)

    def check(self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read") -> LimitVerdict:
        return self._verdict(scope)


@dataclass
class ReadsHarness:
    app: FastAPI
    settings: Settings
    store: FakeSessionStore
    reads: FakeMetricsReads


def reads_app(monkeypatch: pytest.MonkeyPatch, settings: Settings, *, reads: FakeMetricsReads | None = None,
              store: FakeSessionStore | None = None, limiter: RateLimiter | None = None) -> ReadsHarness:
    # 1. def build(app, settings, *, overrides=None) -> Container: limits = Limits();
    #    container = Container(settings=settings, limits=limits); register_web(container, app, settings=settings,
    #    limits=limits); register_reads(container, app, settings=settings, limits=limits); container.build();
    #    return container.    monkeypatch.setattr(app_module, "build_container", build)
    # 2. app = create_app(settings)
    # 3. the_store = store or FakeSessionStore(); the_reads = reads if reads is not None else FakeMetricsReads()
    #    app.dependency_overrides[get_login_sessions] = lambda: the_store
    #    app.dependency_overrides[get_staff_access] = lambda: the_store
    #    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    #    app.dependency_overrides[get_metrics_reads] = lambda: the_reads
    #    if limiter is not None: app.dependency_overrides[get_rate_limiter] = lambda: limiter
    # 4. return ReadsHarness(app=app, settings=settings, store=the_store, reads=the_reads)


def signed_in(h: ReadsHarness, role: DemoRole) -> dict[str, str]:
    return cookie_header(h.store.issue(role))


def get_read(client: Any, operation_id: str, headers: Mapping[str, str] | None = None) -> Any:
    return client.get(OPERATIONS[operation_id], headers=dict(headers or {}))


@contextmanager
def gate_held_for(app: FastAPI, seconds: float) -> Iterator[None]:
    """Hold the app's real ResetGate from a background thread for `seconds`; yields once it is held."""
    # gate = reset_gate_of(app); held = threading.Event()
    # def hold() -> None:  with gate.hold(): held.set(); time.sleep(seconds)
    # thread = threading.Thread(target=hold, daemon=True); thread.start(); assert held.wait(5)
    # try: yield  finally: thread.join(5)


def reads_log(caplog: pytest.LogCaptureFixture, level: int) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == READS_LOGGER and r.levelno == level]


def all_measures(bodies: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every Measure, Tile and EvalMeasure dict in the given bodies (keys: operation ids present)."""
    # getOwnerMetrics: [in_scope_correct_resolution, promises_kept_on_time, handoffs, *outcomes, *handoffs_by_reason]
    # getMonitoring: [*health, correctness.containment_estimate, *correctness.escalations_by_reason]
    # getLatestEval: [*run["measures"] for run in (splits.dev, splits.held_out) if run] + ([headline] if headline)
```

Every attribute of `FakeMetricsReads` is public and mutable, so a test may swap `returns[op]` between requests and clear
`calls` with `h.reads.calls.clear()`.

---

## 7. Checks

### 7.1 Tests the implementer writes with the code

Each test's docstring names its failure mode (invariant / negative / failure-refusal / capture) and its AC. A test that
sends requests builds `h = reads_app(monkeypatch, make_settings(tmp_path))` (a different `tmp_path` subfolder per extra
harness) and runs inside `with make_client(h.app) as client:`. "Owner headers" = `signed_in(h, DemoRole.OWNER)`.

**`tests/api/test_reads_routes.py`**

1. `test_example_pair_no_run_too_few_turns_and_role_not_allowed` (**worked pair**): `h.reads.returns["getLatestEval"] =
   example("getLatestEval", "NO_RUN")`, `h.reads.returns["getMonitoring"] = example("getMonitoring", "TOO_FEW_TURNS")`;
   representative headers. Eval → 200, `assert_matches`, body `== example(..., "NO_RUN")`, `body["splits"] == {"dev": None,
   "held_out": None}`, `body["headline"] is None`, `body["dev_label"] == "Dev (we read and fixed these, so it overstates)"`.
   Monitoring → 200, `assert_matches`; the tiles whose `label` is `"Latency p50"` and `"Latency p95"` have `value is None`
   and `null_reason == "Not enough turns yet (fewer than 20)"`; `body["spend"] == {"today_cents": 612, "cap_cents": 3000,
   "day": "America/Chicago midnight to midnight", "resets_at": "2026-10-17T00:00:00-05:00"}`. Owner metrics →
   `error_body(r, 403, "ROLE_NOT_ALLOWED")`, `details == {"role": "representative", "needs": ["owner", "supervisor"],
   "reason": "wrong_role"}`, `assert_matches`. `h.reads.calls == ["getLatestEval", "getMonitoring"]`. Print the details.
2. `test_getOwnerMetrics_matches_openapi` (AC-1): `example_names("getOwnerMetrics") == EXAMPLE_NAMES["getOwnerMetrics"]`;
   owner headers; for each name: `h.reads.returns[op] = example(op, name)`; GET → 200, `assert_matches(r, op)`, `r.json() ==
   example(op, name)`. Print `f"{op}: {n} bodies validated"`.
3. `test_getMonitoring_matches_openapi` (AC-1): the same for its six examples (customer headers: proves any role).
4. `test_getLatestEval_matches_openapi` (AC-1): the same for its four examples (customer headers).
5. `test_reads_pass_through` (AC-2): owner headers. Build three mappings with changed values and assert `r.json() ==
   mapping` and `h.reads.calls == [op]` after each request (clear between):
   owner = SEEDED with `in_scope_correct_resolution.label = rand_word(12, "zqlabel")`, `promises_kept_on_time.id = "M-13"`,
   `promises_kept_on_time.case_refs = ["MHC-C-0005", rand_word(8, "zqref")]`, `handoffs.null_reason = rand_word(10, "zqwhy")`
   (value stays), `outcomes[0].kind = "estimate"`; monitoring = FIRING with `health[3].id = "M-23"`, `health[4].id = "M-23"`
   (labels differ, so still unique), `alerts[2].state = "firing"`, `alerts[2].fired_at = "2026-10-16T14:10:00-05:00"`,
   `trace_export = rand_word(10, "zqsent")` (FIRING's `health` is M-22, M-23, M-24, M-25, M-26 at indices 0–4, so the
   two re-labelled latency tiles stay unique by label); eval = STALE_RUN with `splits.held_out.measures[0].min = 0.55`,
   `max = 0.7`, `target = "Target " + rand_word(6)`, and `splits.dev.measures[1].label = rand_word(10, "zqeval")` (keep
   every (`id`, `label`) pair unique within each run). Print the three call lists.
6. `test_time_fields_passed_through` (AC-3): `wall = datetime(2026, 10, 21, 20, 4, tzinfo=UTC)` (`from datetime import UTC,
   datetime`), `demo = datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO)`; monitoring = DEFAULT with `as_of = wall`, `demo_now =
   demo` (datetime objects, as a reader may stamp them); owner = SEEDED with `as_of = demo`. Owner headers. Monitoring
   body: `datetime.fromisoformat(b["as_of"]) == wall`, `datetime.fromisoformat(b["demo_now"]) == demo`, `b["as_of"] !=
   b["demo_now"]`, `b["demo_now"] == "2026-10-19T07:00:00-05:00"`; owner body `b["as_of"] == "2026-10-19T07:00:00-05:00"`.
   `assert_matches` both. Print the three values.
7. `test_unknown_keys_dropped_and_named_only` (AC-4): `caplog.set_level(logging.DEBUG)`; `values = {"trace_url":
   "https://langfuse.invalid/" + rand_word(10, "zqtrace"), "customer_name": rand_word(10, "zqname"), "code": rand_word(10,
   "zqcode")}`; each of the three mappings (owner SEEDED, monitoring DEFAULT, eval BOTH_SPLITS) gets `mapping.update(values)`;
   the monitoring one also gets `health[0]["customer_name"] = values["customer_name"]`. Owner headers; `with captured_log() as
   stream:` for each op: `caplog.clear()`; GET → 200, `assert_matches`; `set(values) & set(r.json()) == set()`; each value
   `not in r.text`; `warnings = reads_log(caplog, logging.WARNING)`, `len(warnings) == 1`, message contains `"code"`,
   `"customer_name"`, `"trace_url"` (and for monitoring also `"health[].customer_name"`), contains none of the values.
   After the loop: no value in `stream.getvalue()`, `app_log_text(caplog)`, or `repr(rec.__dict__)` for any `rec in
   caplog.records`.
8. `test_missing_required_field_is_500` (AC-5): `caplog.set_level(logging.DEBUG)`; distinctive `secret_label =
   rand_word(12, "zqlabel")`, `secret_export = rand_word(12, "zqexport")`; monitoring = DEFAULT with `health[0].label =
   secret_label`, `trace_export = secret_export`, and `del mapping["as_of"]`. Owner headers; `with captured_log() as
   stream:` GET → `status_code == 500`, `r.json() == {"request_id": r.headers["X-Request-ID"]}`; `errors =
   reads_log(caplog, logging.ERROR)`, `len(errors) == 1`, `"as_of missing" in errors[0].getMessage()`; neither secret in
   `stream.getvalue()`, `app_log_text(caplog)`, `r.text`, or any `repr(rec.__dict__)`; `h.reads.calls == ["getMonitoring"]`.
   Then the same for owner SEEDED without `"cases"` (`"cases missing"`) and eval BOTH_SPLITS without `"dev_label"`
   (`"dev_label missing"`), one ERROR each (clear caplog between). Do **not** call `assert_matches` on a 500 (undocumented).
9. `test_headline_never_dev` (AC-6): eval = DEV_ONLY with `splits.dev.measures[0].target = "Target 60 to 75 percent
   (ours)"`. Customer headers. Body: `headline is None`; `dev_label == mapping["dev_label"]`; `splits["dev"] ==
   mapping["splits"]["dev"]`; `splits["dev"]["measures"][0]["target"] == "Target 60 to 75 percent (ours)"` and
   `["value"] == 0.8`; `splits["held_out"] is None`; `assert_matches`.
10. `test_reads_access` (AC-7): for `DemoRole.OWNER`, `SUPERVISOR` → owner metrics 200 + `assert_matches`. For `CUSTOMER`,
    `REPRESENTATIVE` → `error_body(r, 403, "ROLE_NOT_ALLOWED")`, details `{"role": role.value, "needs": ["owner",
    "supervisor"], "reason": "wrong_role"}`, `assert_matches`. Count: `h.reads.calls.count("getOwnerMetrics") == 2`. For all
    four roles: monitoring and eval → 200 + `assert_matches`. With no cookie, each of the three → `error_body(r, 401,
    "UNAUTHENTICATED")`, `details == {"reason": "none"}`, `assert_matches`. Final `h.reads.calls` has 2 owner reads, 4
    monitoring, 4 eval. Print the refusal details.
11. `test_reads_429_and_503` (AC-8): (a) `h = reads_app(monkeypatch, make_settings(tmp_path / "limited"),
    limiter=RefusingLimiter())`; owner headers; monitoring and eval → `error_body(r, 429, "REQUEST_RATE_LIMITED")`,
    `details == {"retry_after_ms": RETRY_AFTER_MS}`, `assert_matches`; owner metrics → 200; `h.reads.calls ==
    ["getOwnerMetrics"]`. (b) `h2 = reads_app(monkeypatch, make_settings(tmp_path / "reset"))`; owner headers; `with
    reset_gate_of(h2.app).hold():` for monitoring and eval: `t0 = time.monotonic()`; GET → `error_body(r, 503,
    "RESET_IN_PROGRESS")`, `details == {"retry_after_ms": 5000}`, `assert_matches`, elapsed `< 1.0`; `h2.reads.calls == []`.
    (c) `h2.reads.probe = reset_gate_of(h2.app).held`; `with gate_held_for(h2.app, 0.5):` `t0`; owner metrics → 200,
    `assert_matches`, `elapsed = time.monotonic() - t0`, `0.3 <= elapsed < 5.0`; `h2.reads.held_at_call == [False]`
    (the reader ran after the gate cleared). Print the elapsed times.
12. `test_wf6_reads_emit_request_records` (AC-9): `store = FakeSessionStore()`; `app = full_app(monkeypatch,
    make_settings(tmp_path), store=store, heartbeat=FakeHeartbeat())`; `reads = FakeMetricsReads()`;
    `app.dependency_overrides[get_metrics_reads] = lambda: reads`; `headers = cookie_header(store.issue(DemoRole.OWNER))`;
    `with make_client(app) as client:` then (inside, so lifespan logs stay out) `with captured_log() as stream:` GET the
    three. Each 200. `records = log_records(stream)`; `{x["record"] for x in records} == {"request"}`; for each response
    exactly one record with `request_id == r.headers["X-Request-ID"]`, and it has `route == OPERATIONS[op]`, `status ==
    200`, `caller_role == "owner"`, `thread_id is None`, no `error_kind`; `reads.calls == list(OPERATIONS)`. Print the
    records.
13. `test_unit_vocabulary_enforced` (AC-10): `MEASURE_UNITS == ("count", "ms", "share")`. Valid: owner SEEDED,
    monitoring DEFAULT, eval BOTH_SPLITS → 200 each. Refusals (owner headers; `caplog.clear()` before each; each → 500 and
    exactly one ERROR record from `READS_LOGGER`):
    - monitoring DEFAULT with `health[1]["unit"] = "per 100 turns"` → message contains `"health[1].unit literal_error"`,
      not `"per 100 turns"`;
    - monitoring DEFAULT with `correctness.containment_estimate.value = 75` → `"correctness.containment_estimate.value
      share_out_of_range"`;
    - monitoring DEFAULT with `health[1] = copy.deepcopy(health[0])` → `"health[1] duplicate_measure"`;
    - owner SEEDED with `outcomes[0].value = 75` → `"outcomes[0].value share_out_of_range"`;
    - eval BOTH_SPLITS with `headline.value = 65` → `"headline.value ratio_out_of_range"`;
    - eval BOTH_SPLITS with `splits.held_out.measures[1] = copy.deepcopy(splits.held_out.measures[0])` →
      `"splits.held_out.measures[1] duplicate_measure"`.
    Also prove the per-run scope: BOTH_SPLITS unchanged (E-1 in dev, held_out and headline) → 200. Print each message.
14. `test_wf6_request_status_values` (AC-13): `full_app` as in test 12 with `reads` overridden; tokens for owner,
    representative and customer from `store.issue`. Inside `make_client`, `with captured_log() as stream:` send, in order:
    owner → owner metrics (200); no cookie → monitoring (401); representative → owner metrics (403);
    `app.dependency_overrides[get_rate_limiter] = lambda: RefusingLimiter()`, customer → monitoring (429), then
    `app.dependency_overrides.pop(get_rate_limiter)`; `with reset_gate_of(app).hold():` customer → eval (503);
    `reads.returns["getMonitoring"]` = DEFAULT without `"as_of"`, customer → monitoring (500). For each response find its
    record by `request_id`; `rec["status"] == r.status_code`; for 200/401/403/429 `"error_kind" not in rec`; for 503
    `rec["error_kind"] == "RESET_IN_PROGRESS"`; for 500 `rec["error_kind"] == "reads_schema_violation"`; every `status` in
    `{200, 401, 403, 429, 500, 503}`. Print `(status, error_kind)` per response.

**`tests/api/test_reads_router.py`** (plan-added)

15. `test_router_declares_three_gets`: `routes = build_router().routes`; three `APIRoute`s (assert `isinstance`);
    `{(r.path, frozenset(r.methods), r.operation_id) for r in routes} == {(OWNER_METRICS_PATH, frozenset({"GET"}),
    "getOwnerMetrics"), (MONITORING_PATH, frozenset({"GET"}), "getMonitoring"), (LATEST_EVAL_PATH, frozenset({"GET"}),
    "getLatestEval")}`; the owner-metrics route has `len(route.dependencies) == 1`, the other two `== 0`. In a started
    `reads_app`, `effective_routes(h.app)` lists each path exactly once.
16. `test_register_reads_includes_router_once`: `s = make_settings(tmp_path)`; on a bare `FastAPI()`, `register_reads(Container(
    settings=s, limits=Limits()), bare, settings=s, limits=Limits())` adds none of the three paths; on `app = create_app(s)`
    (not started) two calls leave exactly one route per path and `app.state.reads_routes_included is True`.
17. `test_reads_sources_touch_no_storage_or_clock` (AC-2, second half): for `meridian/web/routes/reads.py` and
    `meridian/web/schemas/reads.py` (locate via `Path(meridian.web.routes.reads.__file__)` and the schemas module):
    `re.search(r"uow|repos_|sqlite|UnitOfWork|datetime\.now|time\.time", text) is None`; and every imported module name
    (`ast` walk of `Import`/`ImportFrom`) is in `{"__future__", "datetime", "logging", "collections.abc", "typing",
    "fastapi", "fastapi.responses", "pydantic", "pydantic_core", "meridian.domain.staff", "meridian.web.deps",
    "meridian.web.errors", "meridian.web.middleware", "meridian.web.schemas.reads"}`.

Plus `tests/api/test_contract_cases_reads.py::test_reads_cases_drive_documented_statuses` (step 6, 13 cases) and the two
journey tests (step 7: one pass, one skip).

### 7.2 What stays green

Every existing test under `tests/api/` (notably `test_gate.py`, which adds probe routes for every operation before the
lifespan, so the probes for the three reads shadow this router there — harmless, the middleware answers 401 first; and
`test_app.py`, `test_openapi_sets.py`), `tests/unit/web/` (`test_container.py` reads the hunk docstring),
`tests/unit/test_import_direction.py`, `tests/unit/test_skeleton.py`, `tests/services/test_health_capture.py` (builds
the app), and every journey the affected command selects.

### 7.3 Commands (cheapest first; stop at the first red)

```bash
export UV_LINK_MODE=hardlink
# while iterating
uv run pytest -q tests/api/test_reads_routes.py tests/api/test_reads_router.py tests/api/test_contract_cases_reads.py
# once before the final commit
uv run ruff check src/meridian/web tests/api tests/contract/cases tests/journeys/j10
uv run ruff format --check src/meridian/web tests/api tests/contract/cases tests/journeys/j10
uv run mypy
uv run pytest -q tests/api tests/unit/web tests/unit/test_import_direction.py tests/unit/test_skeleton.py tests/services/test_health_capture.py
uv run pytest -m journey tests/journeys/j10/test_aea_48.py -rs
uv run python -m tests.journeys.affected --base main
grep -nE "uow|repos_|sqlite|UnitOfWork|datetime\.now|time\.time" src/meridian/web/routes/reads.py src/meridian/web/schemas/reads.py   # prints nothing
python3 ~/.claude/skills/icm-project/scripts/check_context.py .
```

"Affected" = `tests/api/` (mirrors `web/`), `tests/unit/web/`, the import-direction and skeleton tests, and
`tests/services/test_health_capture.py` (from `grep -rlE "meridian\.web\.(container|app)|web_shell_support|full_app"
tests/`). A new file under `tests/journeys/` selects every journey in the affected command (`ALWAYS_PREFIXES`). No full
suite: the change reaches no shared fixture, setting, dependency or cross-codebase module (rule `build-loop-test-scope`).
If you use xdist, `-n 2` at most. Passing looks like: ruff and format clean, `mypy` "Success: no issues found", every
pytest run with 0 failures, the journey file "1 passed, 1 skipped" with the reason printed, the affected command green,
the grep empty, the context check with no FAIL.

| Check | Command | Evidence |
|---|---|---|
| Capture verification WF-6 | `uv run pytest -q -s tests/api/test_reads_routes.py -k "wf6 or unknown_keys or missing_required"` | printed `request` records and `(status, error_kind)` pairs; one warning naming keys; one error naming `as_of missing`; no values in logs |
| Evaluation check | n/a (ticket *Evaluation*: no suite added; the route displays scored runs only) | — |
| Worked pair | `uv run pytest -q -s tests/api/test_reads_routes.py -k example_pair` | NO_RUN and TOO_FEW_TURNS bodies; 403 details printed |
| Twelve bodies | `uv run pytest -q -s tests/api/test_reads_routes.py -k matches_openapi` | "2 / 6 / 4 bodies validated" |
| Contract cases | `uv run pytest -q -s tests/api/test_contract_cases_reads.py` | one line per case, 13 cases |
| Journey | `uv run pytest -m journey tests/journeys/j10/test_aea_48.py -rs` | 1 passed (mock-tested), 1 skipped with its blockers; record file |
| AC-2 grep | the grep above | empty output |

---

## 8. Risks and requests

- **R-1 Dropped-key names in deployed logs (request, not a blocker).** AEA-23's allow-list formatter reduces every plain
  log message to `{"record": "log", "logger", "level", "length"}`, so on Railway stdout the warning shows as a
  `meridian.web.reads` WARNING with a length, not the key names. The `LogRecord` does name them (tests read it via
  `caplog`), which meets STF-17 and AC-4 as written. If Innocent wants the names in deployed logs, that is a small AEA-23
  follow-up (a `reads_drop` record kind in `ALLOWED_FIELDS`); this ticket must not edit `web/logging.py`.
- **R-2 500 body.** The OpenAPI documents no 500 for these operations and the `ApiError` enum has no generic code, so the
  500 is AEA-23's `render_unhandled_error` body `{"request_id"}` (plan decision D-P1 in `web/errors.py`). Tests never call
  `assert_matches` on it. A reader bug is a server bug; AEA-53's tests validate its output with these models first.
- **R-3 `AwareDatetime` is stricter than "pass through".** A naive time from the reader answers 500 (it would also fail the
  OpenAPI `date-time` format). A UTC time renders as `…Z` (same instant). AEA-53's reader stamps aware times (cases.md
  §9; stored wall times are UTC ISO-8601 with `+00:00`).
- **R-4 Uniqueness scope on CON-20.** AC-10 says pairs are unique "within one response". On CON-20 the OpenAPI's own
  BOTH_SPLITS and STALE_RUN examples repeat `E-1 / Correct resolution` in dev, held_out and the headline, so the rule
  applies per `EvalRun.measures` (and response-wide on CON-18 and CON-19). This is the only reading compatible with AC-1;
  it keeps the AC-10 purpose ("a split M-n stays distinguishable") because splits are separate objects. AEA-53 inherits it
  through the models.
- **R-5 Unbound reader until AEA-53.** On the real container, owner/supervisor reads answer 500 (`RuntimeError: not bound:
  get_metrics_reads`, `error_kind` `RuntimeError`) until AEA-53's hunk binds the provider. Expected; AEA-59's runner skips
  as `not bound: get_metrics_reads` (AC-11 text). Refused roles still get 403 because the role check runs first.
- **R-6 Shared context rows.** Area-map row A10b is edited again by AEA-53 (reader); the ICM row is new; DO-3's line is
  this ticket's own. Expect textual merge conflicts only if a sibling edits the same cell; keep both texts.
- **R-7 Contract-case vocabulary.** AEA-59 (wave 2) fixes the runner's vocabulary. This file reuses AEA-47's `"login"`,
  `"role:<r>"`, `"reset_gate_held"` and adds `"rate_limited"` and `"reader_example"`, documented in the file's docstring.
  If AEA-59 names them differently, AEA-59 maps them or a one-line follow-up here.
- **R-8 Journey level.** AC-12 reaches `mock-tested` only; `integrated with a scripted model` needs AEA-57 (harness) and
  AEA-53 (reader; J-10 lands). The record says so; this is evidence timing, not a merge edge.
- **R-9 Ticket wording vs code.** AC-8 says "a fake `ResetGate` held"; tests hold the container's real `ResetGate`
  (`reset_gate_of(app).hold()` / `gate_held_for`), the same condition with less code. AC-14 names "the A10b reads row" in
  `icm-progress.md`; none exists, so the plan adds one (AEA-47 precedent).
- **No shared primitive requested; no signed contract changes.** Everything used exists on `main`; nothing in the OpenAPI
  disagrees with this plan. The ticket's four *Contract notes* stay with AEA-08 (STF-18, STF-25).

---

## 9. Readiness

**READY.** Blocked by AEA-23 only, which is merged. No `BLOCKED-ON`: AEA-53's reader is reached through
`get_metrics_reads()` and tested with a double; AEA-44's store through `FakeSessionStore`; AEA-57 and AEA-59 affect
evidence level only (ticket *Blocked by*). No `NEEDS-DECISION`: every choice (local `ReadModel` base, `AwareDatetime`,
per-run uniqueness on CON-20, the `reads_schema_violation` error kind, the route-level role dependency, the case
vocabulary, the new ICM row) is an engineering decision inside decisions already taken (STF-7, STF-8, STF-17/MC-6,
STF-18, STF-22/MC-5, STF-25, MC-4, MC-14, AEA-48-1, AEA-48-2) and changes no signed contract.

## Deviations

- `src/meridian/web/routes/reads.py`: the module logger is named `_LOG`, not `_log`. `tests/api/test_app.py::test_lifespan_builds_and_closes_container`
  refuses lowercase module-level assignments that call something (regex `^[a-z_]* = .*\(`), and `_log = logging.getLogger(...)` matched.
- `tests/api/reads_support.py` and the tests: small typing and formatting adjustments so `mypy` (which covers `tests/`) passes; behaviour as planned.
- Noted, not caused here: `.claude/state/icm-progress.md` was already over the checker's 8192 B budget on main (9399 B); `check_context.py` reports that FAIL before and after this change.
