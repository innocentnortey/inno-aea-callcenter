## [AEA-47] staff API: advance the demo clock (CON-8)

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

> **US-22:** "As a **supervisor**, I need one view of P0/P1, unowned, due-soon, overdue and stuck-waiting cases … In the
> demo I also start or end the simulated shift and advance the simulated clock." Acceptance: "advancing time moves a
> seeded case into "overdue"".

One thin route, `advanceDemoClock` (CON-8, `POST /api/demo/clock`), in `web/routes/staff_clock.py`, with its wire models
in `web/schemas/staff_clock.py`. Per staff.md §8 (STF-15, STF-16, MC-13):

1. `require_staff(SUPERVISOR)` (web.md §3; the operation's `x-roles: [supervisor]`) returns the `StaffActor`.
2. The request schema accepts `step` ∈ `plus_1h`, `plus_4h`, `next_business_morning` (`ClockStep`, cases.md §6); any
   other value or a missing step → 400 `VALIDATION_ERROR` field `step` from AEA-23's handler, with no service call.
3. Exactly one call: `DemoService.advance_clock(step, actor=actor, request_id=ctx.request_id) -> ClockAdvanced`
   (cases.md §6, injected through `get_demo_service()`). The service stores `actor.role.value` in `demo_events.role`
   and the `request_id` in `demo_events.request_id` (cases.md §1.1), recomputes nothing on write, appends
   `clock_changed` to every open chat and counts `became_overdue`.
4. The route returns the service's `now`, `label` and `became_overdue` unchanged as `ClockAdvanceResponse`. The label
   is formatted by `format_clock` (cases.md §6, the one formatter); the route reads no clock and formats nothing.

The clock only moves forward; the only way back to Fri Oct 16 is a reset (CON-9, AEA-43). While a reset holds
`ResetGate`, AEA-23's middleware answers 503 `RESET_IN_PROGRESS` with `details.retry_after_ms: 5000` before the route
runs (web.md §7, staff.md §11, STF-7); the route adds no reset check.

**Example pair (OpenAPI examples `NEXT_MORNING`, `ROLE_NOT_ALLOWED`).** Demo time Fri Oct 16, 2026 · 2:20 pm, acting as
the supervisor: `POST /api/demo/clock` `{"step": "next_business_morning"}` → 200 `{"now": "2026-10-19T07:00:00-05:00",
"label": "Mon Oct 19, 2026 · 7:00 am", "became_overdue": 1}` (SCR-7 success line "Demo time is now Mon Oct 19 · 7:00 am.
1 case became overdue."). The same request acting as the representative → 403 `ROLE_NOT_ALLOWED` with
`details.needs: ["supervisor"]`, `details.reason: "wrong_role"`, and the service is never called. AEA-52's CAP-5 then
advances past WP-7's refund promise (due Tue Oct 20, 7:00 pm) to prove, with real services, that the promise turns
overdue.

**Produced for other issues:** CON-8 advance for AEA-52 (CAP-5) and AEA-55.

### Source

- PRD R-3, R-30, R-33, R-48; US-22, US-25; WP-7 (due time used by CAP-5).
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml`: `advanceDemoClock` (`x-roles: [supervisor]`, `x-demo-only`);
  schemas `ClockAdvanceRequest`, `ClockAdvanceResponse`, `ApiError`; responses `ValidationError`, `Unauthenticated`,
  `RoleNotAllowed`, `ResetInProgress`.
- `UI_CONTRACTS.md` CON-8 (guarantees: one clock, never the server clock, never backwards).
- `docs/design/contracts/stage7/staff.md` §1 (`StaffActor`), §8 (CON-8 advance), §11 (during a reset);
  `stage7/cases.md` §1.1 (`demo_events` columns), §6 (`DemoService.advance_clock`, `ClockStep`, `ClockAdvanced`,
  `format_clock`); `stage7/web.md` §3 (`require_staff`), §4 (`get_demo_service`, `RequestContext.request_id`), §7
  (`ResetGate`, the 503 set), §10 (`request` record), §13 (`openapi_check.py`). Decisions:
  `docs/plans/7b-decisions/staff.md` STF-7, STF-8, STF-15, STF-16, STF-26; merge MC-4, MC-13, MC-14; web WEB-13, WEB-25.
- `docs/design/contracts/api-con-mapping.md` §1 CON-8 (advance is supervisor-only, UX-3 wins over DO-4 rev 2).
- DO-4 §13 (`Clock`: never the server's wall clock, R-3); DO-3 §4.4 (`DemoService.advance_clock`), §6 S-8.
- DO-6 WF-5, WF-7, CAP-5; DO-7 M-13, M-27.
- SCREEN_SPECS SCR-7 (advance states) — states only.
- **Contract notes (OpenAPI wins; listed, not edited; AEA-08 reconciles, STF-26):** (1) api-con-mapping §1 and DO-3 §3
  put the advance in `web/routes/staff.py`; the slice plan gives it `web/routes/staff_clock.py`, on the same path as
  AEA-43's `GET /api/demo/clock`. (2) UI_CONTRACTS CON-8 *Access* says "read by any browser"; the read needs the login
  too (AEA-43). (3) Settled: staff.md §8 now lists the three OpenAPI fields only (R-W-17); the wire model carries
  exactly `now`, `label` and `became_overdue` (OpenAPI `ClockAdvanceResponse`), and AC-1 and AC-10 hold it.
- **Brief check:** serves "a reviewer should be able to type questions, probe edge cases, and watch the agent escalate."
  (Part B §6): moving the demo clock is how a reviewer sees a handoff promise come due. Touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `advanceDemoClock` 200 bodies validate against `ClockAdvanceResponse` for the `NEXT_MORNING` and `PLUS_1H` shapes, with `now`, `label` and `became_overdue` equal to the service double's `ClockAdvanced` values, and no other key (R-W-17) — verify: `tests/api/test_staff_clock_routes.py::test_advance_matches_openapi` (AEA-23's `assert_response_matches`, STF-8) — evidence: two bodies validate and equal the double's values.
- [ ] AC-2 [invariant] Each accepted request makes exactly one call `advance_clock(step, actor=…, request_id=…)` (MC-13): `plus_1h`, `plus_4h` and `next_business_morning` reach the service unchanged, `actor` is `StaffActor(role=supervisor, name="Demo supervisor", …)`, and `request_id` equals the response's `X-Request-ID` — verify: `…::test_one_call_with_step_actor_and_request_id` — evidence: the double records three calls, one per step, with those arguments.
- [ ] AC-3 [failure/refusal] Any other step (`"minus_1h"`, `"back"`) or a missing step → 400 `VALIDATION_ERROR` field `step` and no service call — verify: `…::test_invalid_step_400` — evidence: three 400 bodies validate against `ValidationError`; zero service calls.
- [ ] AC-4 [negative] A rejected step value never leaves the request: the distinctive string sent as `step` in AC-3 is absent from the 400 body and from every captured log record (the `request` record included) — verify: `…::test_rejected_step_never_echoed_or_logged` — evidence: string absent from body and caplog.
- [ ] AC-5 [failure/refusal] **WF-5:** Supervisor only: the customer, representative and owner roles get 403 `ROLE_NOT_ALLOWED` with `details.needs` `["supervisor"]` and `details.reason` `wrong_role`; a session whose role a reset sent back gets `details.reason` `role_reset` (STF-20); the service is never called — verify: `…::test_supervisor_only` (`get_staff_access` overridden with a double over real `RoleRefusal` values) — evidence: four bodies validate against `RoleNotAllowed`; zero service calls.
- [ ] AC-6 [failure/refusal] **WF-5:** Without `mhc_session` → 401 `UNAUTHENTICATED`; with a fake `ResetGate` held → 503 `RESET_IN_PROGRESS` with `details.retry_after_ms` 5000, at once and with no service call (AEA-23's real middleware; staff.md §11) — verify: `…::test_login_gate_and_reset_503` — evidence: bodies validate against `Unauthenticated` and `ResetInProgress`; zero service calls.
- [ ] AC-7 [invariant] The route never reads the server clock and never computes overdue counts or labels: `grep -nE "datetime\.now|time\.time|date\.today|format_clock|strftime" src/meridian/web/routes/staff_clock.py src/meridian/web/schemas/staff_clock.py` prints nothing — verify: the grep, run by `code-review-agent` — evidence: empty output.
- [ ] AC-8 [invariant] This router registers only `POST /api/demo/clock`, so AEA-43's `GET` on the same path is never shadowed — verify: `…::test_router_declares_post_only` (inspects the router's routes and methods) — evidence: one route, method `POST`. The combined app is checked at AEA-52.
- [ ] AC-9 [capture] Driving `POST /api/demo/clock` through the app the container builds leaves one `request` record (web.md §10: `request_id` = `X-Request-ID`, route `/api/demo/clock`, status, `caller_role` `supervisor`), and the service receives that same `request_id` and the supervisor actor it stores in its `demo_events` row (WF-5: "a `demo_event` row per change") — verify: `…::test_wf5_advance_emits_records` — evidence: the record printed; identifiers captured by the double equal the record's. The `demo_event`, `job_run` and overdue marking (CAP-5) are AEA-52's.
- [ ] AC-10 [negative] The response carries exactly the OpenAPI keys (AEA-47-1, staff audit A7; R-W-17): an `advanceDemoClock` 200 body has the keys `now`, `label` and `became_overdue` and no others (staff.md §8 once also listed `date_label`; R-W-17 corrected it to these three); the OpenAPI sets no `additionalProperties: false`, so this test, not the schema check, catches drift — verify: `tests/api/test_staff_clock_routes.py::test_advance_response_keys_exact` — evidence: the sorted key list printed equals `["became_overdue", "label", "now"]`.
- [ ] AC-11 [contract] `tests/contract/cases/staff_clock.py` holds the server case for `advanceDemoClock` (supervisor; `plus_1h`, `plus_4h`, `next_business_morning`) and each documented error status the route can produce (400 field `step`, 401, 403 for the representative, 503 `RESET_IN_PROGRESS`) (AEA-47-2; slice plan §0a, contract cases per route issue) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k advanceDemoClock -rs` once AEA-59's runner is merged — evidence: one pass per case.
- [ ] AC-12 [journey] Extends J-6 (slice plan §0a journey map; J-6 is a proposed addition to the map, from the join audits): the supervisor's `advanceDemoClock` `plus_4h` past WP-4's case due reports `became_overdue` 1, and the next `getQueue` shows that case `due_state: overdue`; asserting what the user sees and what is stored, in `tests/journeys/j6/test_aea_47.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6/test_aea_47.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-47.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-13 [regression/context] Same change updates `.claude/reference/area-map.md` (this issue's row, planned → actual with the commit), `.claude/state/icm-progress.md` (the A9 staff-console row's evidence link) and DO-3 §3's status for `web/routes/staff_clock.py` and `web/schemas/staff_clock.py` — verify: `git diff --stat` — evidence: only those rows change.

### Observability

- Responsibilities: WF-5 (DO-6 registry) — the middleware's `request` record with `caller_role`; the `request_id` and
  the acting role handed to `DemoService` so it writes one `demo_event` per change (`demo_events.request_id`, `role`;
  cases.md §1.1), making every clock move visible and correlated. No rejected value in any log (AC-4).
- Capture evidence: AC-9 (entry point), AC-4 and AC-10 (negative). CAP-5 end to end is AEA-52's; J-6's clock step
  (AC-12) runs on AEA-57's harness.

### Evaluation

N/A — WF-5's registry row says demo controls change the simulation, not an outcome, and their effect is measured through
WF-1 and WF-6; no DO-5 suite (E-1…E-8) drives the clock, and this route decides no answer.

### Metrics

- References: M-13 (promises kept on time), M-27 (unowned and overdue cases).
- Acceptance conditions: both stay computable because the clock move and the due-state change are recorded by
  `DemoService` and the scheduler from stored rows (cases.md §6), and this route passes `became_overdue` through without
  computing it (AC-1, AC-7). No target is set here.

### Blocked by

- AEA-23 (web app, middleware, `web/deps.py` with `require_staff`, `get_demo_service`, `ResetGate`, `openapi_check.py`).
- Evidence level only, not a build blocker: AC-11 runs once AEA-59's server-case runner (wave 2) is merged; AC-12 reaches
  `integrated with a scripted model` once AEA-57 (harness, wave 2) and AEA-52 (J-6 lands, wave 3) merge, and until then
  its record states `mock-tested` with those two in *Blocked by* (`integrated-journeys.md` §4).

### Agent handoff

- **Area / owner:** A9 Staff console (DO-3 §8); files `src/meridian/web/routes/staff_clock.py`,
  `src/meridian/web/schemas/staff_clock.py`, this issue's `register_…()` hunk in `web/container.py` (includes the router
  only; `DemoService` is bound by AEA-30's hunk), tests under `tests/api/`, `tests/contract/cases/staff_clock.py`
  (AC-11; AEA-59 owns the runner), `tests/journeys/j6/test_aea_47.py` and its record
  `docs/testing/journeys/YYYY-MM-DD-AEA-47.md` (AC-12; `tests/journeys/support/` is AEA-57's).
- **Contracts and shared surfaces:** consumes `DemoService.advance_clock` and `ClockStep` / `ClockAdvanced` (AEA-30,
  injected; `ClockAdvanced` is a cases.md A-2 view type homed in `domain/` by an AEA-02 follow-up, graph-core *cases
  A-2* row; if that has not merged when the planner starts, the plan records `blocked-on` it), `require_staff` and
  `StaffActor` (AEA-23 declares, AEA-44 implements, AEA-02 types); produces CON-8 advance for AEA-52 and AEA-55. Must
  not edit: `web/routes/demo.py` and `web/schemas/demo.py` (AEA-43 owns `GET /api/demo/clock`),
  `web/{app,middleware,deps,errors}.py`, `services/demo.py`, any other route or schema file, `domain/*`,
  `tests/api/openapi_check.py`, the OpenAPI.
- **Scope boundary / refusal:** no backwards step, no "set to a time" step, no due-state computation, no label
  formatting, no event writing and no reset check in the route.
- **Decisions applied:** STF-7 / MC-14 (503 from the middleware), STF-8 (shared validator), STF-15 / WEB-25 (the label
  comes from `format_clock`), STF-16 as changed by MC-13 (`advance_clock(step, actor=actor, request_id=ctx.request_id)`),
  MC-4 (`needs` in x-roles order), R-W-17 (exactly the three OpenAPI keys; AC-1, AC-10), join amendments AEA-47-1 and
  AEA-47-2 (`docs/plans/ux-join/backend-amendments.md` §2).
- **Wave and gates:** wave 2; no gate.
- **Lane:** `lane::build-loop` — route, schema and test code (ticket-lanes: changes code).
- **Risk:** None (slice plan). The supervisor check is a demo label behind the login (R-48).
- **Entry points added or changed:** WF-5 (`POST /api/demo/clock`).
