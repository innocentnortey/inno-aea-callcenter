# Plan — [AEA-47] staff API: advance the demo clock (CON-8)

**Status:** planned (READY) · `lane::build-loop` · no `risk::security` (slice plan row: not **Sec**) · wave 2
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/47 (spec copy:
`docs/plans/tickets/AEA-47.md`) · **Base revision:** `main` at `ef40f45` (AEA-23 web shell merged at `1e6889a`; AEA-32
ops merged at `edf53a5`)
**Planner:** claude-opus-5-5, 2026-10-21. First plan for this ticket (no earlier plan file existed).
**Builder:** `fanout-implementer` (Sonnet). Normal loop: the implementer writes the code **and** the tests named in §7
together. No test-writer, no frozen tests, no security agent. Every name below is copied from the code on `main` or the
signed contracts; you do not need to re-read the design.
**Worktree / branch:** whatever the orchestrator gives you (convention: `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-47`,
branch `aea-47-staff-clock`). All paths below are relative to the repository root.

---

## 1. Goal and sources

### Goal (quoted from the issue, *What to build*)

> One thin route, `advanceDemoClock` (CON-8, `POST /api/demo/clock`), in `web/routes/staff_clock.py`, with its wire models
> in `web/schemas/staff_clock.py`. Per staff.md §8 (STF-15, STF-16, MC-13):
> 1. `require_staff(SUPERVISOR)` returns the `StaffActor`.
> 2. The request schema accepts `step` ∈ `plus_1h`, `plus_4h`, `next_business_morning`; any other value or a missing step
>    → 400 `VALIDATION_ERROR` field `step` from AEA-23's handler, with no service call.
> 3. Exactly one call: `DemoService.advance_clock(step, actor=actor, request_id=ctx.request_id) -> ClockAdvanced`.
> 4. The route returns the service's `now`, `label` and `became_overdue` unchanged as `ClockAdvanceResponse`. The route
>    reads no clock and formats nothing.

**What a reviewer sees (the ticket's worked pair, OpenAPI examples `NEXT_MORNING` and `ROLE_NOT_ALLOWED`).** Demo time Fri
Oct 16, 2026 · 2:20 pm, acting as the supervisor: `POST /api/demo/clock {"step": "next_business_morning"}` → 200
`{"now": "2026-10-19T07:00:00-05:00", "label": "Mon Oct 19, 2026 · 7:00 am", "became_overdue": 1}`. The same request
acting as the representative → 403 `ROLE_NOT_ALLOWED`, `details.needs == ["supervisor"]`, `details.reason == "wrong_role"`,
and the service is never called.

### Context

AEA-23 (merged) built the gate middleware, `web/deps.py` (with `require_staff` and `get_demo_service`), the reset gate and
`tests/api/openapi_check.py`; its `register_staff_clock` stub in `web/container.py` waits for this ticket. The service
behind the route, `DemoService` (AEA-30), is a wave-2 sibling being built now, so the route calls it through
`get_demo_service()` and every test overrides that provider with a double. AEA-52 wires the real service and proves CAP-5.
AEA-43 (same wave) owns `GET /api/demo/clock` on the same path; this router declares `POST` only.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-47.md` (= GitLab #47): AC-1…AC-13, *Agent handoff*, *Observability* | Everything below |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-47 (B, not Sec, blocked by 23, calls demo 30), §0a journey map J-6, §3 collision map rows `web/container.py` and `web/routes/*.py` | Owned files; one `register_<area>()` hunk; one journey file `tests/journeys/j6/test_aea_47.py` |
| Requirements | PRD R-3 (one demo clock, never the server clock), R-30, R-33, R-48; US-22 ("advancing time moves a seeded case into overdue"), US-25; WP-4 (case due Fri 12:00), WP-7 (promise due Tue Oct 20 7:00 pm, AEA-52's) | Route reads no clock; J-6 step uses WP-4's due |
| Staff contract (wins over DO-4) | `docs/design/contracts/stage7/staff.md` §1 (`StaffRole`, `StaffActor`, `actor_for`, `RoleRefusal`), §8 (CON-8 advance), §11 (503 from the middleware) | Exact call; three keys only (R-W-17); no reset check in the route |
| Cases contract | `stage7/cases.md` §1.1 (`demo_events.role`, `request_id`), §6 (`DemoService.advance_clock`, `ClockStep`, `ClockAdvanced`, the one label formatter), cross-topic A-2 | The service, not the route, writes the event and builds the label |
| Web contract | `stage7/web.md` §1 (`ApiProblem`, the 422→400 handler), §3 (`require_staff`), §4 (`get_demo_service`, `RequestContext.request_id`), §7 (`ResetGate`, the 503 set), §10 (`request` record), §13 (`openapi_check.py`) | §4 of this plan copies the code |
| DO-4 | `docs/design/contracts/internal-components.md` §13 (`Clock`: never the server's wall clock, R-3) | AC-7 grep |
| DO-3 | `docs/design/code-design.md` §3 line 312 (`routes/staff_clock.py · schemas/staff_clock.py`), §4.4, §6 S-8 | Location; status line updated (AC-13) |
| Decisions | `docs/plans/7b-decisions/staff.md` STF-7, STF-8, STF-15, STF-16 (as changed by MC-13), STF-26; `merge-clashes.md` MC-4, MC-13, MC-14; web WEB-13, WEB-25; residual R-W-17; UX-join amendments AEA-47-1, AEA-47-2 | Applied as written |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` path `/api/demo/clock` `post` (operationId `advanceDemoClock`, `x-roles: [supervisor]`, responses 200/400/401/403/503, request examples `NEXT_MORNING`, `PLUS_4H`, response examples `NEXT_MORNING`, `PLUS_1H`); schemas `ClockAdvanceRequest`, `ClockAdvanceResponse`, `ApiError`; responses `ValidationError`, `Unauthenticated`, `RoleNotAllowed`, `ResetInProgress` | Wire shapes and statuses; no 429 (not rate-limited) |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` | n/a: no E-1…E-8 suite drives the clock; ticket *Evaluation* N/A |
| Observability (DO-6) | `docs/design/observability-contract.md` row WF-5 ("`request_id`; a `demo_event` row per change"; records `request`, `demo_event`; CAP-5) | Middleware writes `request`; the route hands `request_id` and the actor to the service (AC-9); CAP-5 is AEA-52's |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-13, M-27 | Nothing computed here; `became_overdue` passed through unchanged |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`; workspace `code-design-solid-modularity`, `code-structure` | Affected tests and journeys; journey record; doc rows in the same change |
| Merged code (read) | `src/meridian/web/{app,container,deps,errors,logging,middleware}.py`, `web/routes/auth.py`, `web/schemas/auth.py`, `services/reset_gate.py`, `domain/{common,staff}.py`; `tests/api/{web_shell_support,openapi_check,test_contract_cases_auth,test_gate,test_app}.py`, `tests/contract/cases/auth.py`, `tests/fakes/clock.py`, `tests/unit/web/test_container.py`, `tests/unit/test_import_direction.py`, `tests/journeys/{README.md,affected.py}` | §4 copies the signatures |
| Sibling plans (read) | `docs/plans/fanout/2026-10-21-build/AEA-43.md` (same path, GET; same test pattern), `AEA-30.md` §4.3 (`ClockAdvanced` = `now`, `label`, `became_overdue`, a `MeridianModel`) | Consistent patterns; no shared file |

Prototyped by the planner with the project venv (scratch only, nothing in the repo): `MeridianModel.model_validate(obj,
from_attributes=True)` with fields `now`, `label`, `became_overdue` (1) accepts a frozen dataclass that also carries an
extra `date_label` attribute and serialises only the three fields; (2) accepts a plain dict with exactly the three keys;
(3) rejects a dict with an extra key (`ValidationError`); (4) serialises a `ZoneInfo("America/Chicago")` time as
`"2026-10-19T07:00:00-05:00"`. FastAPI 0.156.8, pydantic 2.14.1. AEA-43's planner also confirmed that
`app.include_router(...)` inside the lifespan serves the routes, and that a second lifespan on the same app includes them
twice unless the hunk guards with a flag (§5 step 3).

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Change |
|---|---|
| `src/meridian/web/routes/staff_clock.py` | create |
| `src/meridian/web/schemas/staff_clock.py` | create |
| `src/meridian/web/container.py` | modify **only** the body and docstring of `register_staff_clock` (lines 493–497 on `main`) |
| `tests/api/staff_clock_support.py` | create (doubles, app builder, helpers; §6) |
| `tests/api/test_staff_clock_routes.py` | create (AC-1…AC-6, AC-8…AC-10, worked pair, plan-added tests) |
| `tests/api/test_contract_cases_staff_clock.py` | create (AC-11 local driver, plan-added; AEA-23 precedent) |
| `tests/contract/cases/staff_clock.py` | create (AC-11) |
| `tests/journeys/j6/test_aea_47.py` | create (AC-12, J-6) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-47.md` | create (AC-12 record; date = the day you commit) |
| `.claude/reference/area-map.md` | modify the *Status* cell of row A9 only (line 36) |
| `.claude/state/icm-progress.md` | add **one new** *Routes verified against code and tests* row directly after line 28 (do not edit other rows) |
| `docs/design/code-design.md` | modify line 312 only (`routes/staff_clock.py · schemas/staff_clock.py …`) |

### Shared surfaces: read only, never edit

`src/meridian/web/{app,middleware,deps,errors,logging}.py`, `web/routes/auth.py`, `web/schemas/auth.py`,
`services/reset_gate.py`, every `services/*`, `domain/*`, `ports/*`, `policy/*`, `config.py`, `adapters/*`;
`tests/api/{web_shell_support,openapi_check}.py` and every existing test; `tests/fakes/*`, `tests/conftest.py`,
`tests/fixtures/*`, `tests/journeys/{affected.py,README.md}`; `pyproject.toml`, `uv.lock`.

### Owned by other tickets — do not touch

`web/routes/demo.py` + `web/schemas/demo.py` and `register_demo_routes` (AEA-43, `GET /api/demo/clock`), every other route
or schema file (AEA-40…46, 48), every other `register_<area>()` hunk (in particular `register_demo`, AEA-30, which binds
`DemoService`), `services/demo.py` (AEA-30), `tests/api/demo_support.py` (AEA-43), `tests/journeys/j6/test_aea_30.py`
(AEA-30), `tests/journeys/support/` (AEA-57), `tests/contract/test_openapi_server.py` (AEA-59), `tests/capture/`,
`apps/web/**`, `docs/ux/**` (the OpenAPI and `UI_CONTRACTS.md` included), the briefing, issued data, `docs/archive/`,
`docs/parked/`.

### Must not do

- Do not import anything from `meridian.services.demo` (it does not exist on `main`) or any other `meridian.services.*`
  module in the route or schema file. The route types the service with a local `Protocol` (§4.3) and reads the result by
  attribute (`from_attributes=True`).
- Do not register any route other than `POST /api/demo/clock`. No `GET`, no other path, no public path.
- Do not read any clock and do not build a label in `routes/staff_clock.py` or `schemas/staff_clock.py`. The AC-7 grep
  (`datetime\.now|time\.time|date\.today|format_clock|strftime`) must print nothing, **so do not write those strings
  anywhere in the two files, comments and docstrings included**. Note that `time\.time` also matches inside
  `datetime.timezone` and `datetime.timedelta`: in these two files import only `import datetime as dt` and use only
  `dt.datetime`.
- Do not add a reset-gate check, a rate limit, a role check other than `require_staff(StaffRole.SUPERVISOR)`, an event
  write, a due-state computation, a "set to a time" step or a backwards step.
- Do not log, print or put into an exception message the request body or a rejected `step` value. The route emits **no**
  log record of its own (the middleware's `request` record is the only one).
- No `.env` reads, no paid model call, no port bind (TestClient only; never 4019 or 5184). No digits that look like a
  verification code, card or phone number in any test, fixture or record.
- `git add` explicit paths only; never `git add -A`. No push, no force-push.

---

## 3. Requirements table

### 3.1 Acceptance criteria (issue verbatim in substance) and plan-added rows

| # | Requirement | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 [invariant] | 200 bodies validate against `ClockAdvanceResponse` for the `NEXT_MORNING` and `PLUS_1H` shapes; `now`, `label`, `became_overdue` equal the double's `ClockAdvanced` values; no other key (R-W-17) | `ClockAdvanceResponse.model_validate(result, from_attributes=True).model_dump(mode="json")` | `tests/api/test_staff_clock_routes.py::test_advance_matches_openapi` |
| AC-2 [invariant] | Exactly one call per accepted request: each of the three steps reaches the service unchanged; `actor` is `StaffActor(role=supervisor, name="Demo supervisor", signature="Demo supervisor")`; `request_id` equals the response's `X-Request-ID` (MC-13) | `demo.advance_clock(body.step, actor=actor, request_id=ctx.request_id)` | `…::test_one_call_with_step_actor_and_request_id` |
| AC-3 [failure/refusal] | `"minus_1h"`, `"back"` or a missing step → 400 `VALIDATION_ERROR` field `step`, no service call | `ClockAdvanceRequest.step: ClockStepName` (Literal); AEA-23's handler | `…::test_invalid_step_400` |
| AC-4 [negative] | A distinctive rejected `step` string is absent from the 400 body and from every captured log record (the `request` record included) | `hide_input_in_errors=True`; the handler reads only `loc`/`type`/`msg`; route logs nothing | `…::test_rejected_step_never_echoed_or_logged` |
| AC-5 [failure/refusal] **WF-5** | customer, representative, owner → 403 `ROLE_NOT_ALLOWED`, `details.needs == ["supervisor"]`, `details.reason == "wrong_role"`; a role-reset session → `details.reason == "role_reset"`; service never called | `require_staff(StaffRole.SUPERVISOR)`; `get_staff_access` overridden by `FakeSessionStore` (real `RoleRefusal` values) | `…::test_supervisor_only` |
| AC-6 [failure/refusal] **WF-5** | No `mhc_session` → 401 `UNAUTHENTICATED`; with the reset gate held → 503 `RESET_IN_PROGRESS`, `details.retry_after_ms` 5000, at once, no service call | Nothing in the route: AEA-23's middleware (`advanceDemoClock` is already in `RESET_503_OPERATIONS`) | `…::test_login_gate_and_reset_503` |
| AC-7 [invariant] | The route never reads the server clock nor computes labels or counts | §2 *Must not do* | `grep -nE "datetime\.now\|time\.time\|date\.today\|format_clock\|strftime" src/meridian/web/routes/staff_clock.py src/meridian/web/schemas/staff_clock.py` prints nothing |
| AC-8 [invariant] | The router registers only `POST /api/demo/clock` | `build_router()` adds one route | `…::test_router_declares_post_only` |
| AC-9 [capture] | Through the app the **real container** builds: one `request` record (`request_id` = `X-Request-ID`, `route` `/api/demo/clock`, `status`, `caller_role` `supervisor`); the service receives that `request_id` and the supervisor actor | Middleware record; route passes `ctx.request_id` and `actor` | `…::test_wf5_advance_emits_records` |
| AC-10 [negative] | A 200 body has exactly the keys `now`, `label`, `became_overdue`, even when the service result carries an extra `date_label` | Response model declares three fields; `from_attributes` reads only those | `tests/api/test_staff_clock_routes.py::test_advance_response_keys_exact` (prints the sorted key list) |
| AC-11 [contract] | `tests/contract/cases/staff_clock.py` holds the server case for `advanceDemoClock` (supervisor; three steps) and each documented error status (400 `step`, 401, 403 representative, 503) | Case file (§5 step 6) | AEA-59's `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k advanceDemoClock -rs` once merged; **until then** `tests/api/test_contract_cases_staff_clock.py::test_staff_clock_cases_drive_documented_statuses` |
| AC-12 [journey] | Extends J-6: supervisor `plus_4h` past WP-4's case due (Fri 12:00) reports `became_overdue` 1; the next `getQueue` shows `due_state: overdue`. Level today `mock-tested`; *Blocked by* AEA-57 and AEA-52 (and AEA-45 for `getQueue`) | `tests/journeys/j6/test_aea_47.py` (§5 step 7) + record | `uv run pytest -m journey tests/journeys/j6/test_aea_47.py -rs`; record `docs/testing/journeys/<date>-AEA-47.md` |
| AC-13 [regression/context] | Area-map row A9, ICM progress, DO-3 §3 status line for the two files | §5 step 9 | `git diff --stat` shows only those rows in the three docs |
| plan-added (worked pair) | The ticket's example pair: `NEXT_MORNING` as supervisor → the OpenAPI example body; same request as representative → 403, needs `["supervisor"]`, reason `wrong_role`, zero calls | as above | `…::test_example_pair_next_morning_and_role_not_allowed` |
| plan-added | The schema's step names equal the OpenAPI `ClockAdvanceRequest.step` enum, in order (drift guard; the route does not import AEA-30's `ClockStep`) | `CLOCK_STEP_NAMES = get_args(ClockStepName)` | `…::test_step_names_equal_openapi_enum` |
| plan-added | `register_staff_clock` includes the router once per web-shell app; does nothing on a bare app; second call adds nothing | Hunk (§5 step 3) | `…::test_register_staff_clock_includes_router_once` |

### 3.2 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| `require_staff(SUPERVISOR)`, `needs` in x-roles order | web.md §3; MC-4 | AC-5 | in-ticket | step 2 |
| One call `advance_clock(step, actor=actor, request_id=ctx.request_id)` | staff.md §8; cases.md §6; MC-13 | AC-2 | in-ticket | step 2 |
| Exactly three response keys, no `date_label` | staff.md §8; R-W-17; AEA-47-1 | AC-1, AC-10 | in-ticket | steps 1–2 |
| Label from the service, route formats nothing; never the server clock | STF-15, WEB-25; DO-4 §13; R-3 | AC-7 | in-ticket | §2 |
| 400 field `step` via the shared handler, no input echoed | web.md §1; STF-8 | AC-3, AC-4 | in-ticket | step 1 |
| 503 during a reset from the middleware only | web.md §7; staff.md §11; STF-7, MC-14 | AC-6 | in-ticket (nothing to build) | — |
| `request` record with `caller_role` | web.md §10; DO-6 WF-5 | AC-9 | in-ticket (middleware) | step 5 tests |
| `demo_event` row with `role` and `request_id` | cases.md §1.1, §6; WF-5 | AC-9 (identifiers only) | other-ticket: AEA-30 writes it, AEA-52 proves it (CAP-5) | AEA-30, AEA-52 |
| Clock moves only forward; no "set" step | UI_CONTRACTS CON-8; OpenAPI description | Scope boundary | in-ticket: enum has three forward steps | step 1 |
| POST only on the shared path | slice plan §3; AEA-43 owns GET | AC-8 | in-ticket | step 2 |
| Contract server cases in the route's own file | AEA-59 AC-18; AEA-47-2 | AC-11 | in-ticket; local driver plan-added | step 6 |
| `[journey]` J-6 at the right level with record | integrated-journeys §3–§4 | AC-12 | in-ticket | step 7 |
| Step names equal the OpenAPI enum | OpenAPI `ClockAdvanceRequest` | — | added (drift guard) | step 5 |
| Router included once, from the ticket's own hunk | slice plan §3 `web/container.py` row | — | added | step 3 |
| `ClockAdvanced` homed in `domain/` (cases A-2, an AEA-02 follow-up not yet cut) | cases.md cross-topic A-2; graph-core GRC-19 | Agent handoff | n/a for this ticket: the route never imports it (local `Protocol` + `from_attributes`), so it is **not** a blocker (§8 R-1) | — |
| Contract notes (1) DO-3/api-con-mapping put the advance in `routes/staff.py`; (2) CON-8 *Access* "read by any browser" | ticket *Contract notes*; STF-26 | — | other-ticket: AEA-08 reconciles; listed, not edited | AEA-08 |

### 3.3 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `POST /api/demo/clock` (`advanceDemoClock`) | WF-5 Demo controls (CON-7, CON-8) | yes, DO-6 row WF-5 | Evaluation n/a (demo controls change the simulation; measured through WF-1, WF-6); metrics M-13, M-27 indirectly; capture CAP-5 (AEA-52) |

---

## 4. Shared code to use (copied from `main` at `ef40f45`)

### 4.1 `meridian.web.deps` (AEA-23)

```python
def get_request_context(request: Request) -> RequestContext: ...
def get_demo_service(request: Request) -> Any:        # DemoService (cases.md §6), bound by AEA-30; until bound it raises
                                                      # RuntimeError("not bound: get_demo_service") when called
def get_staff_access(request: Request) -> StaffAccess: ...
def get_login_sessions(request: Request) -> LoginSessions: ...
def get_heartbeat(request: Request) -> HeartbeatReader: ...
RESET_GATE: Key[ResetGate] = Key("reset_gate")

def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]:
    # Depends(get_login_session) + Depends(get_staff_access); access.actor_for(session, roles);
    # RoleRefusal -> ApiProblem(403, ApiErrorCode.ROLE_NOT_ALLOWED,
    #                details={"role": result.role.value, "needs": [r.value for r in result.needs], "reason": result.reason})
    # else returns the StaffActor
```

### 4.2 Middleware, errors, domain types

```python
# meridian.web.middleware
@dataclass(frozen=True)
class RequestContext:
    request_id: RequestId; client_ip: str; session: LoginSession | None
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; turn_verdict: LimitVerdict | None
class WebShellState: ...           # app.state.web_shell; present only on apps create_app built
OPERATIONS_BY_ROUTE[("POST", "/api/demo/clock")] == "advanceDemoClock"
RESET_503_OPERATIONS contains "advanceDemoClock"          # the middleware answers 503, details {"retry_after_ms": 5000}
RATE_LIMITED_READ_OPERATIONS does NOT contain it          # no 429 for this operation (the OpenAPI documents none)
# The middleware's request record: {"record": "request", "request_id", "route" (template), "status", "duration_ms",
#   "caller_role" ("anonymous" | DemoRole value), "thread_id": None, "error_kind" on 5xx}

# meridian.web.errors: the RequestValidationError handler builds ApiProblem(400, VALIDATION_ERROR, field=<loc after
#   "body">, constraint=<msg>, details=None); for {"step": "x"} and for {} the field is "step". It never reads `input`.

# meridian.domain.common
class MeridianModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
class RequestId(_PatternId): ...   # UUID4 str subclass, minted by the middleware

# meridian.domain.staff
class DemoRole(StrEnum): CUSTOMER = "customer"; REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
class StaffRole(StrEnum): REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
class StaffActor(MeridianModel): role: StaffRole; name: str; signature: str
def actor_for(role: StaffRole) -> StaffActor: ...     # SUPERVISOR -> name "Demo supervisor", signature "Demo supervisor"
class RoleRefusal(MeridianModel): role: DemoRole; needs: tuple[StaffRole, ...]; reason: Literal["wrong_role", "role_reset"]
```

### 4.3 The sibling signature this route calls (AEA-30, injected; cases.md §6 as changed by MC-13)

```python
ClockStep = Literal["plus_1h", "plus_4h", "next_business_morning"]          # services/demo.py (AEA-30)
class DemoService:
    def advance_clock(self, step: ClockStep, *, actor: StaffActor, request_id: RequestId) -> ClockAdvanced: ...
# ClockAdvanced (AEA-30 plan §4.3 / cases A-2): MeridianModel with now: datetime; label: str; became_overdue: int
```

The route declares the **one method it uses** as a local `Protocol` in `routes/staff_clock.py` (interface segregation;
it imports no sibling module) and validates the result by attribute, so a pydantic model, a frozen dataclass or a dict
with exactly the three keys all work:

```python
class ClockAdvancer(Protocol):
    def advance_clock(self, step: ClockStepName, *, actor: StaffActor, request_id: RequestId) -> object: ...
```

### 4.4 Container (`meridian.web.container`)

```python
class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...
    def get[T](self, key: Key[T]) -> T: ...
    def build(self) -> None: ...
def register_web(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None: ...   # AEA-23
def register_staff_clock(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:  # lines 493-497
    """AEA-47 staff API: the CON-8 clock-advance route (staff.md §8).

    No-op until AEA-47 fills it.
    """
```
Rules from existing tests: the docstring must keep the text `AEA-47` and must **not** contain `No-op until`
(`tests/unit/web/test_container.py::test_every_register_stub_present`); imports stay **inside** the function
(`tests/unit/test_import_direction.py::test_container_imports_only_policy_limits` fails on any new module-level import).

### 4.5 Test helpers to reuse (read only)

From `tests/api/web_shell_support.py`: `make_settings(tmp_path, **changes) -> Settings` · `make_client(app, *,
peer="198.51.100.7") -> TestClient` (use as a context manager so the lifespan runs) · `FakeSessionStore` (`.issue(role,
*, now=None) -> token`, `.session_of(token) -> LoginSession`, `.set_role(token, role, *, role_reset=False)`, implements
`actor_for` with real `RoleRefusal` values) · `FakeHeartbeat()` · `cookie_header(token) -> {"Cookie": "mhc_session=…"}` ·
`login(client, settings)` · `session_cookie_value(response)` · `error_body(response, status, code) -> dict` (asserts
status, code and `request_id == X-Request-ID`) · `assert_matches(response, operation_id)` · `captured_log()` (context
manager → `io.StringIO` of allow-list JSON lines) · `records_of(stream, "request") -> list[dict]` ·
`app_log_text(caplog) -> str` · `all_output_text(responses) -> str` · `rand_word(length=16, prefix="zq") -> str`
(letters only) · `reset_gate_of(app) -> ResetGate` · `effective_routes(app) -> list[RouteInfo(path, methods,
operation_id, endpoint)]` · `full_app(monkeypatch, settings, *, store, heartbeat, overrides=None) -> FastAPI` (the real
`build_container`, every hunk, starters suppressed).
From `tests/api/openapi_check.py`: `load_contract()` (`.operations["advanceDemoClock"].responses`), `load_document()`
(the parsed YAML; timestamps stay strings).
From `tests/fakes/clock.py`: `CHICAGO = ZoneInfo("America/Chicago")`, `WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0,
tzinfo=CHICAGO)` (= `DEMO_START`).
`meridian.web.app`: `create_app(settings, *, overrides=None)`; `import meridian.web.app as app_module` to monkeypatch
`app_module.build_container`.
`meridian.services.reset_gate.ResetGate.hold()` is a context manager; `held()` is a lock-free read.

---

## 5. Steps (build order; each step is checkable on its own)

The slice sits in area A9 (staff console), DO-3 §3. `web/routes/staff_clock.py` depends on `web/deps.py` providers, the
`web/schemas` module and `domain/` types only, and on the sibling service through the local `ClockAdvancer` Protocol;
nothing depends on it except the container hunk. No new seam is introduced.

### Step 0 — check the base

`export UV_LINK_MODE=hardlink`; `git log --oneline -1` (your branch starts from `main`);
`grep -n "def register_staff_clock" -A5 src/meridian/web/container.py` shows the "No-op until AEA-47 fills it." stub;
`uv run python -c "import meridian.web.app"` succeeds. No baseline suite.

### Step 1 — `src/meridian/web/schemas/staff_clock.py` (create; ≤ 50 lines)

Exact contents (names are load-bearing; tests import them):

```python
"""Wire shapes for CON-8 `advanceDemoClock` (OpenAPI ClockAdvanceRequest, ClockAdvanceResponse). AEA-47.

The response carries exactly the three OpenAPI fields (R-W-17). Its values come from the demo service unchanged.
"""

from __future__ import annotations

import datetime as dt
from typing import Final, Literal, get_args

from pydantic import BaseModel, ConfigDict

from meridian.domain.common import MeridianModel

ClockStepName = Literal["plus_1h", "plus_4h", "next_business_morning"]  # = OpenAPI ClockAdvanceRequest.step
CLOCK_STEP_NAMES: Final[tuple[str, ...]] = get_args(ClockStepName)


class ClockAdvanceRequest(BaseModel):
    """Plain BaseModel: the OpenAPI allows extra properties, so they are ignored, never refused."""

    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    step: ClockStepName


class ClockAdvanceResponse(MeridianModel):
    now: dt.datetime
    label: str
    became_overdue: int
```

Check: `uv run python -c "from meridian.web.schemas.staff_clock import CLOCK_STEP_NAMES; print(CLOCK_STEP_NAMES)"` prints
`('plus_1h', 'plus_4h', 'next_business_morning')`.

### Step 2 — `src/meridian/web/routes/staff_clock.py` (create; ≤ 70 lines)

```python
"""CON-8 advance: `advanceDemoClock`, POST /api/demo/clock, supervisor only (stage7/staff.md §8). AEA-47.

One call DemoService.advance_clock(step, actor=actor, request_id=ctx.request_id) (cases.md §6, MC-13). The body is the
service's now, label and became_overdue, unchanged (R-W-17): the route reads no clock and builds no label. While a reset
holds the ResetGate the middleware answers 503 before this runs (staff.md §11). The GET on this path is AEA-43's.
"""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from meridian.domain.common import RequestId
from meridian.domain.staff import StaffActor, StaffRole
from meridian.web.deps import get_demo_service, get_request_context, require_staff
from meridian.web.middleware import RequestContext
from meridian.web.schemas.staff_clock import ClockAdvanceRequest, ClockAdvanceResponse, ClockStepName

ADVANCE_PATH = "/api/demo/clock"
ADVANCE_OPERATION = "advanceDemoClock"
_SUPERVISOR_ONLY = require_staff(StaffRole.SUPERVISOR)  # the operation's x-roles: [supervisor] (MC-4)


class ClockAdvancer(Protocol):
    """The one DemoService method this route calls (cases.md §6, MC-13); AEA-30's DemoService satisfies it."""

    def advance_clock(self, step: ClockStepName, *, actor: StaffActor, request_id: RequestId) -> object: ...


def advance_demo_clock(
    body: ClockAdvanceRequest,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    actor: StaffActor = Depends(_SUPERVISOR_ONLY),  # noqa: B008
    demo: ClockAdvancer = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    result = demo.advance_clock(body.step, actor=actor, request_id=ctx.request_id)
    payload = ClockAdvanceResponse.model_validate(result, from_attributes=True)
    return JSONResponse(payload.model_dump(mode="json"))


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        ADVANCE_PATH,
        advance_demo_clock,
        methods=["POST"],
        operation_id=ADVANCE_OPERATION,
        response_model=None,
    )
    return router
```

Load-bearing details (do not change):
1. **Parameter order** `body, ctx, actor, demo`. FastAPI resolves dependencies in signature order, so the role check runs
   before `get_demo_service`: a wrong role answers 403 even while `DemoService` is unbound (before AEA-30 merges, the real
   provider raises `RuntimeError("not bound: get_demo_service")`). Body validation runs after the dependencies, so a
   supervisor with a bad step gets 400 and the endpoint (and the service) never runs.
2. The endpoint is a plain `def` (sync, like `routes/auth.py`): the real service writes SQLite.
3. `JSONResponse(payload.model_dump(mode="json"))`: the body is exactly the model's three fields; `now` keeps its offset
   (`"2026-10-19T07:00:00-05:00"`).
4. No try/except around the service call: an unexpected error becomes the middleware's 500 with `X-Request-ID` and
   `error_kind` on the `request` record. The operation documents no 500; no test asserts one.

Check: `uv run python -c "from meridian.web.routes.staff_clock import build_router; print([(r.path, sorted(r.methods)) for r in build_router().routes])"`
prints `[('/api/demo/clock', ['POST'])]`.

### Step 3 — the hunk in `src/meridian/web/container.py` (modify `register_staff_clock` only, lines 493–497)

Keep the signature `def register_staff_clock(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:`
and replace the docstring and body with:

```python
    """AEA-47 staff API: the CON-8 clock-advance route (staff.md §8).

    Includes routes/staff_clock.py's router (advanceDemoClock: POST /api/demo/clock only; the GET on the same path is
    AEA-43's) once per app. Provides nothing: DemoService is bound by AEA-30's register_demo hunk. An app that
    create_app did not build has no web shell, so this does nothing.
    """
    from meridian.web.middleware import WebShellState
    from meridian.web.routes.staff_clock import build_router

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    if getattr(app.state, "staff_clock_routes_included", False):
        return  # a second lifespan on the same app must not add the route again (FastAPI includes lazily)
    app.include_router(build_router())
    app.state.staff_clock_routes_included = True
```
Touch nothing else in the file (siblings edit their own hunks in the same wave).

Check: `uv run pytest -q tests/unit/web/test_container.py tests/unit/test_import_direction.py tests/api/test_gate.py`
→ all pass.

### Step 4 — `tests/api/staff_clock_support.py` (create; ≤ 200 lines; spec in §6)

### Step 5 — `tests/api/test_staff_clock_routes.py` (create; ≤ 450 lines; tests in §7.1)

Run `uv run pytest -q tests/api/test_staff_clock_routes.py` until 12 passed.

### Step 6 — contract cases: `tests/contract/cases/staff_clock.py` + `tests/api/test_contract_cases_staff_clock.py`

`tests/contract/cases/staff_clock.py` follows `tests/contract/cases/auth.py`'s shape exactly (module docstring, `from
__future__ import annotations`, `from typing import Final`, `ROUTE_FILE`, `CASES`):

```python
"""Server contract cases for CON-8 `advanceDemoClock`, owned by AEA-47 (AC-11, AEA-47-2).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, AEA-47's
tests/api/test_contract_cases_staff_clock.py drives them. Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie;
                 "role:supervisor" / "role:representative" = then act as that role (switchRole, CON-10, on the real
                 app; the local driver sets the role on its session-store double).
  setup: "reset_gate_held" = hold the app's ResetGate during the request (the middleware answers 503).
  body: {"example": <named request example>} sends that example's value read from the OpenAPI;
        {"raw": <JSON value>} sends JSON as given.
"""

from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "staff_clock"
CASES: Final[dict[str, dict[str, object]]] = {
    "advanceDemoClock": {
        "public": False,
        "drives": (
            {"name": "next_morning", "status": 200, "preconditions": ("login", "role:supervisor"),
             "body": {"example": "NEXT_MORNING"}},
            {"name": "plus_4h", "status": 200, "preconditions": ("login", "role:supervisor"),
             "body": {"example": "PLUS_4H"}},
            {"name": "plus_1h", "status": 200, "preconditions": ("login", "role:supervisor"),
             "body": {"raw": {"step": "plus_1h"}}},
            {"name": "bad_step", "status": 400, "code": "VALIDATION_ERROR", "preconditions": ("login", "role:supervisor"),
             "body": {"raw": {"step": "minus_1h"}}},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (),
             "body": {"example": "NEXT_MORNING"}},
            {"name": "representative", "status": 403, "code": "ROLE_NOT_ALLOWED",
             "preconditions": ("login", "role:representative"), "body": {"example": "NEXT_MORNING"}},
            {"name": "reset_running", "status": 503, "code": "RESET_IN_PROGRESS",
             "preconditions": ("login", "role:supervisor"), "setup": "reset_gate_held",
             "body": {"example": "NEXT_MORNING"}},
        ),
    },
}
```
(Let `ruff format` lay it out.)

`tests/api/test_contract_cases_staff_clock.py::test_staff_clock_cases_drive_documented_statuses` mirrors
`tests/api/test_contract_cases_auth.py`:
1. `assert ROUTE_FILE == "staff_clock"` and `set(CASES) == {"advanceDemoClock"}`; `examples =
   load_document()["paths"]["/api/demo/clock"]["post"]["requestBody"]["content"]["application/json"]["examples"]`.
2. For each case: `settings = make_settings(tmp_path / case["name"])`, `h = clock_app(monkeypatch, settings)` (§6),
   `with make_client(h.app) as client:`
   - `"login"` → `token = session_cookie_value(login(client, settings))`, `assert token`, `headers = cookie_header(token)`;
   - `"role:<r>"` → `h.store.set_role(token, DemoRole(r))`; any other precondition → `AssertionError` naming it;
   - body: `{"example": n}` → `assert n in examples`, record `n` as sent, send `examples[n]["value"]`; `{"raw": v}` → send `v`;
   - `setup == "reset_gate_held"` → send inside `with reset_gate_of(h.app).hold():`;
   - `response = client.post("/api/demo/clock", headers=headers, json=payload)`.
   Then assert the status, the `error.code` when the case names one, and `assert_matches(response, "advanceDemoClock")`
   for every case (the 200s too); print `advanceDemoClock/<name>: <status>`.
3. After the loop: every documented status ≥ 400 in `load_contract().operations["advanceDemoClock"].responses` (400,
   401, 403, 503) has a case; `"200"` is covered; every named request example (`NEXT_MORNING`, `PLUS_4H`) was sent; the
   three 200 cases' recorded double calls used steps `next_business_morning`, `plus_4h`, `plus_1h`; `ran == 7`.

### Step 7 — journey (AC-12): `tests/journeys/j6/test_aea_47.py`

`pytestmark = pytest.mark.journey`. Module docstring: "J-6 clock leg (AEA-47). **Level today: mock-tested** — the real
AEA-23 app and middleware in process with AEA-47's router, a session-store double and a demo-service double over one
open WP-4 case; no server, no browser, no DB copy. Blocked steps: the `getQueue` read showing `due_state: overdue` (AEA-45
route; AEA-30 + AEA-52 real DemoService and CaseService on the DB copy) and the integrated run (AEA-57 harness). Stored
side at this level: the double's demo-event list only."

Contents:

```python
WP4_CASE_DUE = datetime(2026, 10, 16, 12, 0, tzinfo=CHICAGO)   # WP-4 step 5: P2 change request, due 12:00 today (Fri)
AFTER_PLUS_4H_LABEL = "Fri Oct 16, 2026 · 2:00 pm"

@dataclass
class OneCaseDemo:
    """Stands in for AEA-30's DemoService over one open WP-4 case. became_overdue follows cases.md §6:
    open cases whose case due d satisfies old_now <= d < new_now."""
    now: datetime = WORKED_PAIRS_NOW                  # Fri Oct 16 10:00 (DEMO_START)
    case_due: datetime = WP4_CASE_DUE
    demo_events: list[dict[str, object]] = field(default_factory=list)

    def advance_clock(self, step: str, *, actor: StaffActor, request_id: str) -> ClockAdvancedStub:
        assert step == "plus_4h", step                 # the only step this journey sends
        new = self.now + timedelta(hours=4)
        became = 1 if self.now <= self.case_due < new else 0
        self.demo_events.append({"kind": "clock_advanced", "step": step, "role": actor.role.value,
                                 "request_id": str(request_id), "became_overdue": became})
        self.now = new
        return ClockAdvancedStub(now=new, label=AFTER_PLUS_4H_LABEL, became_overdue=became)
```
(`timedelta` and `datetime` are fine here: the AC-7 grep covers only the two production files.)

- `test_j6_supervisor_advance_turns_wp4_case_overdue(monkeypatch, tmp_path)`: `demo = OneCaseDemo()`;
  `h = clock_app(monkeypatch, make_settings(tmp_path), demo=demo)`; `with make_client(h.app) as client:` sign in through
  the real login route (`login(client, settings)` → cookie) and `h.store.set_role(token, DemoRole.SUPERVISOR)`;
  `POST /api/demo/clock {"step": "plus_4h"}` → 200, `assert_matches(r, "advanceDemoClock")`, `r.json() == {"now":
  "2026-10-16T14:00:00-05:00", "label": "Fri Oct 16, 2026 · 2:00 pm", "became_overdue": 1}`; stored side:
  `demo.demo_events == [{"kind": "clock_advanced", "step": "plus_4h", "role": "supervisor", "request_id":
  r.headers["X-Request-ID"], "became_overdue": 1}]`. Print the body and the event.
- `test_j6_queue_shows_wp4_case_overdue_after_advance()`: body is a single
  `pytest.skip("blocked: getQueue route (AEA-45); real DemoService and CaseService on the DB copy (AEA-30, AEA-52); journey harness (AEA-57)")`.
  It is never reported as passed.

Then write `docs/testing/journeys/<YYYY-MM-DD>-AEA-47.md` in the format of `docs/testing/journeys/2026-10-21-AEA-23.md`
(a heading `# Journey record: AEA-47 staff API: advance the demo clock (CON-8)` and the field table): **Claim** CON-8
advance (AC-1…AC-12) at TestClient level with doubles; the J-6 clock leg (plus_4h past WP-4's due → `became_overdue` 1);
**Level** `mock-tested`; **Tested revision** "the commit that adds this record, on branch <branch>"; **Environment** VPS,
Python 3.12, FastAPI TestClient in process, no port, no browser; `FakeSessionStore`, `FakeClockAdvancer`, `OneCaseDemo`
doubles; no model call; **Command** the §7.3 test, journey and contract-case commands; **Result** the pass/skip counts
you saw; **Evidence location** GitLab issue #47 comment, this file; **Remaining limitations** no real `DemoService`,
`demo_events` row, `clock_changed` events or due-state recompute (AEA-30, CAP-5 at AEA-52); the `getQueue` step is
skipped; the strict contract run waits for AEA-59; **Blocked by** AEA-57 (harness), AEA-52 (real services, J-6 lands),
AEA-45 (`getQueue`), AEA-59 (strict contract run); **Journeys that will exercise this code** J-6 (and J-8's reset
returning the clock, AEA-43/52). No code digits, password or personal data.

### Step 8 — fast gates, affected tests, affected journeys (§7.3); fix until green

### Step 9 — context rows (AC-13), in the same change as the code

1. `.claude/reference/area-map.md` line 36, row **A9 Staff console**, *Status* cell (currently `planned`): replace with
   `partly built: AEA-47 (<short sha>): web/routes/staff_clock.py, web/schemas/staff_clock.py, register_staff_clock
   hunk; the rest planned`. If a sibling (AEA-44, 45, 46) changed the same cell first, keep both texts.
2. `.claude/state/icm-progress.md`: add one row directly after line 28 (the AEA-32 row), ≤ 400 characters:
   `| Routes verified against code and tests | provisional | <date>: area map A9 → web/routes/staff_clock.py,
   web/schemas/staff_clock.py (AEA-47, <short sha>) checked against tests/api/test_staff_clock_routes.py,
   test_contract_cases_staff_clock.py (<N> passed); record docs/testing/journeys/<date>-AEA-47.md | Each slice adds its
   route; verified when every area-map row is actual |`
   (There is no existing A9 row; this new row is the "A9 staff-console row" AC-13 refers to.)
3. `docs/design/code-design.md` line 312: append `   built AEA-47 <short sha>` at the end of the line (the format of the
   existing `built AEA-04 9145044` lines).
4. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in files you own.

`<short sha>` is the implementation commit. If it is not known before committing, commit the code first, then the three
doc edits and the journey record as a second commit naming the first sha. Amend nothing.

### Step 10 — commit

`git add` exactly the owned paths of §2 that changed (never `-A`), for example:
`git add src/meridian/web/routes/staff_clock.py src/meridian/web/schemas/staff_clock.py src/meridian/web/container.py
tests/api/staff_clock_support.py tests/api/test_staff_clock_routes.py tests/api/test_contract_cases_staff_clock.py
tests/contract/cases/staff_clock.py tests/journeys/j6/test_aea_47.py`, then the docs commit with
`docs/testing/journeys/<date>-AEA-47.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`.
Messages such as `feat(web): advanceDemoClock route CON-8 (AEA-47)` and `docs(AEA-47): journey record and context rows`,
each ending with the last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Commit on your branch only;
no push (only the merge step pushes `main`), no force-push.

---

## 6. Data and fixtures (all synthetic; spec of `tests/api/staff_clock_support.py`)

Sources: the OpenAPI `advanceDemoClock` response examples (`NEXT_MORNING`, `PLUS_1H`), the ticket's example pair (demo
time Fri Oct 16 · 2:20 pm), `tests/fakes/clock.CHICAGO`. No digits that resemble a code, card or phone number; the
distinctive strings are `rand_word(...)` (letters only); IP addresses are the default documentation peer.

```python
"""AEA-47 test support: a DemoService.advance_clock double (cases.md §6, MC-13) and an app builder that runs AEA-23's
register_web plus AEA-47's register_staff_clock. Not a conftest. Synthetic values only (OpenAPI examples)."""

from __future__ import annotations
# imports: dataclasses (dataclass, field), datetime (datetime), typing (Any), collections.abc (Mapping),
# pytest, fastapi (FastAPI), import meridian.web.app as app_module, meridian.config.Settings,
# meridian.domain.staff (DemoRole, LoginSession, StaffActor), meridian.policy.limits.Limits,
# meridian.web.app.create_app, meridian.web.container (Container, register_staff_clock, register_web),
# meridian.web.deps (get_demo_service, get_heartbeat, get_login_sessions, get_staff_access),
# tests.api.web_shell_support (FakeHeartbeat, FakeSessionStore, cookie_header), tests.fakes.clock.CHICAGO

ADVANCE_PATH = "/api/demo/clock"


@dataclass(frozen=True)
class ClockAdvancedStub:                     # = ClockAdvanced's three fields (AEA-30 plan §4.3)
    now: datetime
    label: str
    became_overdue: int


@dataclass(frozen=True)
class ClockAdvancedWithDateLabel:            # the pre-R-W-17 shape, to prove the route drops extra attributes
    now: datetime
    label: str
    became_overdue: int
    date_label: str


EXAMPLE_START = datetime(2026, 10, 16, 14, 20, tzinfo=CHICAGO)          # "Fri Oct 16, 2026 · 2:20 pm"
NEXT_MORNING = ClockAdvancedStub(datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO), "Mon Oct 19, 2026 · 7:00 am", 1)
PLUS_1H = ClockAdvancedStub(datetime(2026, 10, 16, 15, 20, tzinfo=CHICAGO), "Fri Oct 16, 2026 · 3:20 pm", 0)
PLUS_4H = ClockAdvancedStub(datetime(2026, 10, 16, 18, 20, tzinfo=CHICAGO), "Fri Oct 16, 2026 · 6:20 pm", 0)


def default_results() -> dict[str, object]:
    return {"plus_1h": PLUS_1H, "plus_4h": PLUS_4H, "next_business_morning": NEXT_MORNING}


@dataclass(frozen=True)
class AdvanceCall:
    step: str
    actor: StaffActor
    request_id: str


class FakeClockAdvancer:
    """advance_clock(step, *, actor, request_id) double. Records every call; returns results[step] or raises `raises`."""

    def __init__(self, results: Mapping[str, object] | None = None, *, raises: Exception | None = None) -> None:
        self.results: dict[str, object] = dict(results) if results is not None else default_results()
        self.raises = raises
        self.calls: list[AdvanceCall] = []

    def advance_clock(self, step: str, *, actor: StaffActor, request_id: str) -> object:
        self.calls.append(AdvanceCall(step=step, actor=actor, request_id=request_id))
        if self.raises is not None:
            raise self.raises
        return self.results[step]


@dataclass
class ClockHarness:
    app: FastAPI
    settings: Settings
    store: FakeSessionStore
    demo: Any                                  # FakeClockAdvancer or any object with advance_clock (the J-6 double)


def clock_app(monkeypatch: pytest.MonkeyPatch, settings: Settings, *, demo: Any = None,
              store: FakeSessionStore | None = None) -> ClockHarness:
    # 1. def build(app, settings, *, overrides=None) -> Container: limits = Limits();
    #    container = Container(settings=settings, limits=limits); register_web(container, app, settings=settings,
    #    limits=limits); register_staff_clock(container, app, settings=settings, limits=limits); container.build();
    #    return container.   monkeypatch.setattr(app_module, "build_container", build)
    # 2. app = create_app(settings)
    # 3. store = store or FakeSessionStore(); demo = demo if demo is not None else FakeClockAdvancer()
    #    app.dependency_overrides[get_login_sessions] = lambda: store
    #    app.dependency_overrides[get_staff_access] = lambda: store
    #    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    #    app.dependency_overrides[get_demo_service] = lambda: demo
    # 4. return ClockHarness(app=app, settings=settings, store=store, demo=demo)


def signed_in(h: ClockHarness, role: DemoRole) -> tuple[dict[str, str], LoginSession]:
    token = h.store.issue(role)
    return cookie_header(token), h.store.session_of(token)
```

Every attribute of `FakeClockAdvancer` is public and mutable (`results`, `raises`, `calls`), so a test may change it
between requests. The stubs are frozen dataclasses (not AEA-30 classes) on purpose: the route must read the result by
attribute.

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (`tests/api/test_staff_clock_routes.py`)

Each test's docstring names its failure mode (invariant / negative / failure-refusal / capture) and its AC, like AEA-23's
tests. Every test that sends requests builds `h = clock_app(monkeypatch, make_settings(tmp_path))` (with a different
`tmp_path` subfolder per harness when a test builds several) and runs inside `with make_client(h.app) as client:`.

1. `test_example_pair_next_morning_and_role_not_allowed` (**the ticket's worked pair**): supervisor
   `POST {"step": "next_business_morning"}` → 200, `assert_matches(r, "advanceDemoClock")`, `r.json() ==
   load_document()["paths"]["/api/demo/clock"]["post"]["responses"]["200"]["content"]["application/json"]["examples"]["NEXT_MORNING"]["value"]`;
   then a representative session, same request → `body = error_body(r, 403, "ROLE_NOT_ALLOWED")`,
   `body["error"]["details"] == {"role": "representative", "needs": ["supervisor"], "reason": "wrong_role"}`,
   `assert_matches`; `len(h.demo.calls) == 1` (only the supervisor's).
2. `test_advance_matches_openapi` (AC-1): supervisor; `next_business_morning` and `plus_1h` → each 200, `assert_matches`,
   body equals the matching OpenAPI response example value (`NEXT_MORNING`, `PLUS_1H`) **and** equals
   `{"now": stub.now.isoformat(), "label": stub.label, "became_overdue": stub.became_overdue}` for the double's stub;
   `sorted(body) == ["became_overdue", "label", "now"]`.
3. `test_one_call_with_step_actor_and_request_id` (AC-2): supervisor; post the three steps in the order `plus_1h`,
   `plus_4h`, `next_business_morning` → three 200s; `[c.step for c in h.demo.calls]` equals that order;
   every `c.actor == actor_for(StaffRole.SUPERVISOR)` and `c.actor.name == "Demo supervisor"`; `c.request_id ==
   r.headers["X-Request-ID"]` for the matching response, and `isinstance(c.request_id, RequestId)`. Print the three calls.
4. `test_invalid_step_400` (AC-3): supervisor; bodies `{"step": "minus_1h"}`, `{"step": "back"}`, `{}` → each
   `error_body(r, 400, "VALIDATION_ERROR")`, `body["error"]["field"] == "step"`, `assert_matches`; `h.demo.calls == []`.
5. `test_rejected_step_never_echoed_or_logged` (AC-4): `caplog.set_level(logging.DEBUG)`; `bad = rand_word(12, "zqstep")`;
   `with captured_log() as stream:` supervisor `POST {"step": bad}` → 400; `bad not in all_output_text([r])`,
   `bad not in stream.getvalue()`, `bad not in app_log_text(caplog)`, and for every `rec in caplog.records`:
   `bad not in repr(rec.__dict__)`; `records_of(stream, "request")` has exactly one record, with `route ==
   "/api/demo/clock"` and `status == 400`; `h.demo.calls == []`.
6. `test_supervisor_only` (AC-5): for `DemoRole.CUSTOMER`, `REPRESENTATIVE`, `OWNER`: `signed_in(h, role)` → POST
   `{"step": "plus_1h"}` → `error_body(r, 403, "ROLE_NOT_ALLOWED")`, details `{"role": role.value, "needs":
   ["supervisor"], "reason": "wrong_role"}`, `assert_matches`. Then a fourth session: `token = h.store.issue(
   DemoRole.SUPERVISOR)`, `h.store.set_role(token, DemoRole.CUSTOMER, role_reset=True)` → 403 with details `{"role":
   "customer", "needs": ["supervisor"], "reason": "role_reset"}`, `assert_matches`. `h.demo.calls == []`. Print the four
   `details`.
7. `test_login_gate_and_reset_503` (AC-6): no cookie, `POST {"step": "plus_1h"}` → `error_body(r, 401,
   "UNAUTHENTICATED")`, `details == {"reason": "none"}`, `assert_matches`. Then with a supervisor cookie:
   `with reset_gate_of(h.app).hold():` `t0 = time.monotonic()`; POST → `error_body(r, 503, "RESET_IN_PROGRESS")`,
   `details == {"retry_after_ms": 5000}`, `assert_matches`, `time.monotonic() - t0 < 1.0` (the waiting path would take
   5 s). `h.demo.calls == []`. After the `with` block the same request → 200 and one call.
8. `test_router_declares_post_only` (AC-8): `routes = build_router().routes`; `len(routes) == 1`; the route is an
   `APIRoute` (assert `isinstance`) with `path == "/api/demo/clock"`, `methods == {"POST"}`, `operation_id ==
   "advanceDemoClock"`. Inside a started `clock_app` client: the `effective_routes(h.app)` entries whose `path ==
   "/api/demo/clock"` are exactly one, with `methods == frozenset({"POST"})`. Print it.
9. `test_wf5_advance_emits_records` (AC-9): `store = FakeSessionStore()`; `app = full_app(monkeypatch,
   make_settings(tmp_path), store=store, heartbeat=FakeHeartbeat())` (the **real** `build_container`, every hunk);
   `demo = FakeClockAdvancer()`; `app.dependency_overrides[get_demo_service] = lambda: demo`;
   `headers = cookie_header(store.issue(DemoRole.SUPERVISOR))`; `with captured_log() as stream, make_client(app) as
   client:` POST `{"step": "next_business_morning"}` → 200. `recs = [x for x in records_of(stream, "request") if x["route"]
   == "/api/demo/clock"]`; exactly one; `rec["request_id"] == r.headers["X-Request-ID"]`, `rec["status"] == 200`,
   `rec["caller_role"] == "supervisor"`, `rec.get("thread_id") is None`; `len(demo.calls) == 1`,
   `demo.calls[0].request_id == rec["request_id"]`, `demo.calls[0].actor.role.value == rec["caller_role"]`. Print `rec`.
10. `test_advance_response_keys_exact` (AC-10): `h.demo.results["next_business_morning"] = ClockAdvancedWithDateLabel(
    NEXT_MORNING.now, NEXT_MORNING.label, 1, "Mon Oct 19, 2026 (demo date)")`; supervisor POST → 200;
    `keys = sorted(r.json())`; `print(keys)`; `keys == ["became_overdue", "label", "now"]`; `"date_label" not in r.text`;
    `assert_matches`.
11. `test_step_names_equal_openapi_enum` (plan-added): `load_document()["components"]["schemas"]["ClockAdvanceRequest"]
    ["properties"]["step"]["enum"] == list(CLOCK_STEP_NAMES)`.
12. `test_register_staff_clock_includes_router_once` (plan-added): `s = make_settings(tmp_path)`; on a bare `FastAPI()`
    `register_staff_clock(Container(settings=s, limits=Limits()), bare, settings=s, limits=Limits())` adds no route with
    path `/api/demo/clock` (`effective_routes(bare)`); on `app = create_app(s)` (not started) two calls leave exactly one
    `("POST", "/api/demo/clock")` route with `operation_id == "advanceDemoClock"`, and `app.state.staff_clock_routes_included is True`.

Plus `tests/api/test_contract_cases_staff_clock.py::test_staff_clock_cases_drive_documented_statuses` (step 6, 7 cases)
and the two journey tests (step 7: one pass, one skip).

### 7.2 What stays green

Every existing test under `tests/api/` (notably `test_gate.py` and `test_app.py`, which build the real container and so
now include this router; `test_gate.py` adds a probe for `advanceDemoClock` before the lifespan, which is harmless because
the middleware answers 401 first), `tests/unit/web/` (`test_container.py` reads the hunk docstring),
`tests/unit/test_import_direction.py`, `tests/unit/test_skeleton.py`, and every journey the affected command selects.

### 7.3 Commands (cheapest first; stop at the first red)

```bash
export UV_LINK_MODE=hardlink
# while iterating
uv run pytest -q tests/api/test_staff_clock_routes.py tests/api/test_contract_cases_staff_clock.py
# once before the final commit
uv run ruff check src/meridian/web tests/api tests/contract/cases tests/journeys/j6
uv run ruff format --check src/meridian/web tests/api tests/contract/cases tests/journeys/j6
uv run mypy
uv run pytest -q tests/api tests/unit/web tests/unit/test_import_direction.py tests/unit/test_skeleton.py
uv run pytest -m journey tests/journeys/j6/test_aea_47.py -rs
uv run python -m tests.journeys.affected --base main
grep -nE "datetime\.now|time\.time|date\.today|format_clock|strftime" src/meridian/web/routes/staff_clock.py src/meridian/web/schemas/staff_clock.py   # prints nothing
python3 ~/.claude/skills/icm-project/scripts/check_context.py .
```

"Affected" here = `tests/api/` (mirrors `web/`; confirm with `grep -rl "meridian.web" tests/`), `tests/unit/web/`,
`tests/unit/test_import_direction.py` and `tests/unit/test_skeleton.py`. A new file under `tests/journeys/` selects every
journey in the affected command (`ALWAYS_PREFIXES`), so it runs every journey on `main` plus this one. No full suite: the
change reaches no shared fixture, setting, dependency or cross-codebase module (rule `build-loop-test-scope`). If you use
xdist, `-n 2` at most. Passing looks like: ruff and format clean, `mypy` "Success: no issues found", every pytest run green
with 0 failures, the journey file "1 passed, 1 skipped" with the skip reason printed, the affected-journeys command green,
the grep empty, the context check without FAIL.

| Check | Command | Evidence |
|---|---|---|
| Capture verification WF-5 | `uv run pytest -q -s tests/api/test_staff_clock_routes.py -k "wf5 or rejected_step"` | the printed `request` record; the double's `request_id` and role equal it; the rejected string absent |
| Evaluation check | n/a (ticket *Evaluation*: N/A) | — |
| Worked pair | `uv run pytest -q -s tests/api/test_staff_clock_routes.py -k example_pair` | 200 body equal to the OpenAPI example; 403 details printed; one service call |
| Contract cases | `uv run pytest -q -s tests/api/test_contract_cases_staff_clock.py` | one line per case, 7 cases |
| Journey | `uv run pytest -m journey tests/journeys/j6/test_aea_47.py -rs` | 1 passed (mock-tested), 1 skipped with its blockers; record file |
| AC-7 | the grep above | empty output |

---

## 8. Risks and requests

- **R-1 `ClockAdvanced` is not on `main` (cases A-2 follow-up, "AEA-02b", not cut).** The ticket says to record
  `blocked-on` it if missing, but this route does not need the import: it types the service with the local
  `ClockAdvancer` Protocol and validates the result by attribute (`from_attributes=True`), which accepts AEA-30's planned
  `MeridianModel` and the test stubs alike. So it is **not** a blocker here (AEA-30 itself waits on it; see its plan
  §8 R-1). If AEA-30 instead returned a plain dict (the A-2 "graph declines" fallback), a dict with exactly the three keys
  still validates; a dict with an extra key would fail loudly (500), which AEA-52's integration run would catch.
- **R-2 Same path as AEA-43.** AEA-43 registers `GET /api/demo/clock`, this ticket `POST`. Starlette tries every route and
  returns the method-matching one, and the middleware's `_match` prefers a full match, so order does not matter. AC-8
  proves this router is POST-only; the combined app is AEA-52's check.
- **R-3 Shared context rows.** Area-map row A9's *Status* cell is also edited by AEA-44, 45, 46 in this wave: expect a
  textual merge conflict; resolve by keeping every ticket's text. The ICM row is new (no conflict); DO-3 line 312 is this
  ticket's own.
- **R-4 `web/container.py`.** Only `register_staff_clock` changes; siblings edit their own hunks. The
  `app.state.staff_clock_routes_included` flag is this hunk's own attribute.
- **R-5 Contract-case vocabulary.** AEA-59 (wave 2) has no plan yet, so its runner's vocabulary is not fixed. This file
  uses AEA-23's shape plus `"role:<r>"` (switchRole to an x-roles role, which AEA-59 AC text requires) and AEA-43's
  `"reset_gate_held"`. If AEA-59 names them differently, AEA-59 maps them (its ticket: "each written by its route issue"),
  or a one-line follow-up here.
- **R-6 Journey level.** AC-12 reaches `mock-tested` only; `integrated with a scripted model` needs AEA-57 (harness),
  AEA-52 (real DemoService + CaseService, J-6 lands) and AEA-45 (`getQueue`). The record says so; this is evidence timing,
  not a merge edge (ticket *Blocked by*).
- **R-7 Ticket wording vs code.** AC-13 names "the A9 staff-console row" in `icm-progress.md`; no such row exists, so the
  plan adds one (step 9), following AEA-43's plan. AC-6 says "a fake `ResetGate` held"; the tests hold the container's
  real `ResetGate` (`reset_gate_of(app).hold()`), which is the same condition with less code.
- **No shared primitive requested; no signed contract changes.** Everything used exists on `main`; nothing in the OpenAPI
  disagrees with this plan. The two *Contract notes* in the ticket stay with AEA-08.

---

## 9. Readiness

**READY.** Blocked by AEA-23 only, which is merged (`1e6889a`). No `BLOCKED-ON`: AEA-30's `DemoService` is reached through
`get_demo_service()` and tested with a double; `ClockAdvanced` is not imported (R-1). No `NEEDS-DECISION`: every choice
(the local Protocol, attribute validation, the include-once flag, the case vocabulary, the new ICM row) is an
engineering decision inside decisions already taken (STF-7, STF-8, STF-15, STF-16/MC-13, MC-4, MC-14, R-W-17, WEB-25) and
changes no signed contract.

**Gates:** none human, external, paid or live. Not `risk::security`: no test-writer, no security review at the wave merge.
