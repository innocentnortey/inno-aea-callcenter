# Plan — [AEA-45] staff API: queue, case, actions, contact log, flags, oversight (CON-11…13, 15…17)

**Status:** planned — **READY (resume run).** Refreshed 2026-10-21 against `main` `c9b17ea`.

**What this run is.** The routes, wire models, `result_line`, the `register_staff_cases` hunk, four API test files, the
J-6 journey file, the journey record and the context rows are **already built and committed** on branch
`aea-45-staff-cases-api` (`c6cdab6` code, `ea00827` record and rows), in the worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-45` (clean). The ledger shows the ticket `blocked` because the
last run could not build AC-19: R-1 (below) was never granted. This run resumes on that branch:

1. merge `main` and resolve two documentation conflicts;
2. add one seam test that puts the now-merged real `CaseService` behind the routes (plan-added AC-23);
3. build AC-19 if R-1 has landed or been granted;
4. refresh the journey record and the context rows;
5. re-run the checks.

Steps **R0–R7** in §5 are the work. Steps 0–6 and 8 are the built reference; step 7 is still to build; steps 9–10 are
replaced by R5–R7.

**What changed on `main` since the last plan (`2ec19ad` → `c9b17ea`):**

- AEA-29 merged (`ef561fc`): `services/cases.py` (`CaseService`, `CaseNotFound(LookupError)` with `.case_ref`) and the
  `register_cases` hunk, which binds `case_service`. Its signatures equal §4.4 exactly; its check order equals R-2's.
- AEA-30 is **still not merged** (ledger `blocked`). `register_demo` is a no-op, so `demo_clock` and `demo_service` are
  unbound, a real login still answers 500, and the J-6 file still skips at step 0.
- R-1's `case_state` word is **still absent** from `tests/contract/openapi_cases.py` `LOCAL_DRIVER_ONLY`.
- The OpenAPI `CaseDetail` still has 11 properties (no `events`), so AC-21 stays skipped.
- Nothing the branch imports changed. The diff from the branch base `895f271` to `main` is empty for
  `domain/{views,staff,common}.py`, `services/staff.py`, `web/{deps,errors,middleware,app}.py`,
  `tests/api/{openapi_check,web_shell_support}.py`, `tests/contract/openapi_*`, `tests/contract/test_openapi_server.py`,
  `tests/journeys/support/`, `tests/fixtures/sqlite.py`, `tests/fakes/clock.py`, `pyproject.toml` and `uv.lock`.
- A dry-run merge (`git merge-tree`) shows exactly **two** conflicts, both documentation:
  `.claude/reference/area-map.md` (the block holding the A9 row) and `docs/design/code-design.md` (the `**Built:**`
  lines). `container.py` and `icm-progress.md` merge cleanly.
- `uv run mypy … tests/journeys/j6` is red on `main` (5 errors in `tests/services/_case_fixtures.py`, AEA-29's, pulled in
  by `tests/journeys/j6/test_aea_29.py`). Check B therefore names this ticket's journey file, not the folder (§7, §8 R-10).

**Pre-dispatch request (§8 R-1): land the `case_state` word on `main`, or write "R-1 granted to AEA-45" in the dispatch
message.** Without one of them, AC-19 stays unbuilt and the ticket cannot close.

**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/45 (identical to
`docs/plans/tickets/AEA-45.md`) · **Base revision:** `main` `c9b17ea` (branch base `895f271`, branch head `ea00827`).
**Wave:** 2 · **Lane:** `lane::build-loop` · **Risk:** none (no `risk::security`), so the loop is plan → implement (code + the
tests named here) → test → `code-review-agent`. No test-writer, no frozen tests, no security agent.
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21. Third pass: first against `4754991`, then `2ec19ad`, now
`c9b17ea`.
**Implementer:** fanout-implementer (Sonnet).
**Branch / worktree:** **reuse** `aea-45-staff-cases-api` in `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-45`.
Do not create a branch or worktree, do not rebase; merge `main` in (R1).

---

## 1. Goal and sources

### Goal (quoted from the issue, *What to build*)

> The staff console's case routes in `web/routes/staff_cases.py`, with wire models in `web/schemas/staff_cases.py` whose
> fields are copied from the OpenAPI schemas. Each route is thin: it checks the role, validates the request, takes **one
> demo-clock reading** for `now`, makes **one** service call, maps a rejection to its documented status and serialises the
> result. Lifecycle rules, ordering, due states, lanes, `allowed_actions`, promise marking and the "Demo: recorded, not
> sent" label are all `CaseService`'s (AEA-29, cases.md §5) or `FlagService`'s (AEA-44, staff.md §2); the route decides
> none of them.

In plain words, this ticket adds eight HTTP endpoints for the staff console. Each one does six things in order:

1. refuses the wrong role;
2. validates the request;
3. reads the demo clock once;
4. calls exactly one service method;
5. turns a service refusal into the status the OpenAPI documents;
6. copies the service's view onto the wire unchanged. Times are rendered in America/Chicago. Case actions also get one
   composed sentence, `result_line`.

**Worked example (WP-2 pair).** Acting as the representative, the user sends `POST /api/staff/cases/MHC-C-0007/actions`
with `{"action": "claim", "expected_version": 3}`. The route:

- checks the role (representative is allowed);
- validates the body;
- reads `DemoService.clock_view().now` once;
- calls `CaseService.apply(CaseRef("MHC-C-0007"), CaseAction(action="claim", expected_version=3), actor=Riley, expected_version=3, now)`;
- gets back a `CaseSummaryView` with `lifecycle` "claimed", `owner` "Riley" and `version` 4;
- answers 200 `{"case": {...}, "result_line": "Claimed · Riley (demo)"}`.

### Context

Wave 2 route ticket. On `main` now:

- AEA-23's web shell: middleware, `require_staff`, providers, `openapi_check.py`;
- AEA-02b's view types (`domain/views.py`);
- AEA-44's `FlagService`;
- AEA-57's journey harness;
- AEA-59's contract runner;
- since `ef561fc`, AEA-29's real `CaseService`, bound as `case_service`.

Not on `main`: `DemoService` (AEA-30). The routes reach it by injection (`get_demo_service`), and the API tests use a
clock double. Every 2xx example in the OpenAPI round-trips through the real `domain/views.py` types unchanged (26 of 26,
checked in the first pass). Now that AEA-29 is merged, this run adds one seam test that puts the **real** `CaseService`,
over a seeded temporary DB, behind the routes (§5 R3). That proves the wire models against real views before AEA-30
unblocks the journey.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-45.md` | AC-1…AC-22, WP-2 pair, owned files, must-not list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-45 (line 180), §0a J-6 (line 84), §3 collision map | owned `routes/staff_cases.py`, `schemas/staff_cases.py`; calls cases (29), flags (44) by injection; extends J-6 |
| Requirements | PRD R-25, R-28, R-29, R-30, R-32, R-33, R-34, R-37, R-48; US-18…US-23 (via ticket *Source*) | pass the brief, promise and sources through; "Demo: recorded, not sent" unchanged (R-34); roles are demo labels (R-48) |
| UI conventions | `docs/ux/03-structure/UI_CONTRACTS.md` line 20 | "Times are ISO 8601 with offset (America/Chicago, the demo clock)" → wire datetimes are rendered in America/Chicago |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §0 (errors never carry values), §13 (`CaseService` signatures; "Staff routes never call `open_case`") | signatures in §4 |
| Stage 7 addenda (win over DO-4) | `stage7/staff.md` §1, §2, §6 (request rules, `result_line` table), §10, §11; `stage7/web.md` §1, §3, §4, §7, §10, §13; `stage7/cases.md` §5, §6 | `require_staff`, providers, `FlagService`, result lines, request rules, reset behaviour, `request` record |
| Code on `main` | `src/meridian/domain/views.py` (AEA-02b), `src/meridian/services/staff.py` (AEA-44), `src/meridian/services/cases.py` (AEA-29), `src/meridian/web/{deps,errors,container}.py` (AEA-23), sibling routes `web/routes/staff_{clock,live}.py` (pattern) | exact types in §4 |
| AEA-29 code (merged `ef561fc`; read for fidelity, the routes never import it) | `src/meridian/services/{cases,_case_actions,_case_rules,_case_views}.py`; seed `src/meridian/services/reset.py` | `apply` returns `CaseSummaryView \| CaseActionRejected`; `record_activity` returns `ActivityResult \| CaseActionRejected`; `detail` raises `CaseNotFound(LookupError)` with `.case_ref == str(case_ref)`. `apply_in` checks: not found → role (only when the action is outside `ROLE_ACTIONS[actor.role]`) → missing field (the 422s) → version → state. A claim on a claimed case answers `CASE_ALREADY_CLAIMED` with `details.claimed_by` = the owner's persona name ("Riley"). `ROLE_ACTIONS[OWNER]` is empty, so the owner's `allowed_actions` is `[]`. `brief_view` already emits `source_ids`. The seed: MHC-C-0005…0008, `unassigned`, `owner_role` NULL, version 1; MHC-C-0007's customer is MHC-10002 |
| AEA-30 code (not merged; ledger `blocked`) | branch `aea-30-aea-30-demo-clock-sched` | `clock_view()` returns `ClockView(now=Chicago)`; never imported here |
| Signed wire contract (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` (§4.5) | every wire field, status, error code, x-roles order |
| Contract runner (read only) | `tests/contract/openapi_cases.py`, `openapi_driver.py`, `test_openapi_server.py`, `cases/README.md` | case-file format: allowed drive keys, closed precondition vocabulary, one 2xx drive per request example; skip only `not bound:` / `route not registered:` |
| Journey harness (read only) | `tests/journeys/support/README.md`, `steps.py` (`NEED_OWNERS`, `OPERATION_OWNERS`), `run.py` | journey file rules: `journey` fixture, named steps with `needs`/`operations`, no doubles, no `TestClient`, every `/api` call names its operationId |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | n/a: no check is added, and the route writes no eval file or row (ticket *Evaluation*) |
| Observability contract | DO-6 `docs/design/observability-contract.md` WF-4, CAP-4 | one `request` record per call (middleware); actor + reason handed to every write; no D2 contact / D4 free text in logs |
| Key-metrics registry | DO-7 M-3, M-13, M-27 | must stay computable: `now` and the actor reach the services; flags keep case and message refs |
| Decisions | `docs/plans/7b-decisions/staff.md` STF-1, 2, 3, 7, 8, 9, 10, 26; merge MC-2, 4, 12, 14; R-W-13; UX-join AEA-45-1/2/3; `stage7-signoff.md` D-5 | applied as listed in the reconciliation table |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`; workspace `code-design-solid-modularity.md`, `code-structure.md`, `async-safety.md` | affected tests only; journey record; context rows in the same change; file-size caps |

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Role per operation from x-roles, `needs` in x-roles order | OpenAPI x-roles; MC-4; web.md §3 | AC-3 | in-ticket | step 2 (`require_staff` as the **first** parameter) |
| assign / change_priority supervisor only, via a second role check | STF-3, MC-4 | AC-4 | in-ticket | step 2 H4 |
| Identity is the role | STF-1 | AC-5 | in-ticket | step 2 (actor only from `require_staff`) |
| `now` = one demo-clock reading; never the server clock | R-3; cases.md §6; web.md §4 | AC-12 | in-ticket | step 2 (every case handler) |
| Wire times in America/Chicago | UI_CONTRACTS *Conventions* line 20; precedent `schemas/staff_live.py::wire_time`, `schemas/events.py` | no | **added**: every output date-time is serialised with `.astimezone(America/Chicago).isoformat()`. The instant is unchanged; only its offset form changes. Every OpenAPI example is already `-05:00`, so AC-1/6/18 equality still holds | step 1 (`WireTime`) |
| `listFlags` `as_of` is demo time, but `FlagService.list_flags()` returns no time | staff.md §2, §10 | no | **added**: the route stamps `as_of` from its single `clock_view().now` reading | step 2 H7 |
| `detail` of an unknown case → 404 | OpenAPI getCase 404; AEA-29 `CaseNotFound(LookupError)` with `.case_ref` | AC-7 | in-ticket. Mechanism **added**: a structural match on a `LookupError` whose `case_ref` equals the requested reference; any other `LookupError` stays a 500 | step 2 H3 |
| Service rejection codes beyond the ticket's list: `VALIDATION_ERROR` (assign without assignee, wait in the past) → 400; `ROLE_NOT_ALLOWED` (AEA-29's defence) → 403 | AEA-29 `_case_rules.py`; OpenAPI applyCaseAction 400/403 | no | **added** to `REJECTION_STATUS` | step 2 |
| Malformed `case_ref` in the `createFlag` body | OpenAPI createFlag documents 400 | no | **added**: 400 `VALIDATION_ERROR` field `case_ref` (same constraint as `reference`) | step 2 H6 |
| Malformed reference on getCase → 404 with **no** echoed value | contract note 3; DO-4 §0 | AC-7 | in-ticket. `details` is `null` for a malformed reference; a well-formed unknown one carries `{"reference": …}` like the OpenAPI example | step 2 H3 |
| Free-text rules for flags and reviews (strip, blank → null, ≤ 2,000, never echoed) | staff.md §6; STF-10 | AC-11 | in-ticket | step 1 |
| Case-action `reason`/`outcome` and activity `note`: strip, blank → null (no length rule specified) | staff.md §6 (flags' rule, applied by analogy) | no | **added**, so whitespace-only text reaches the service as missing and `REASON_REQUIRED`/`OUTCOME_REQUIRED` fire | step 1 |
| `result_line` table | staff.md §6; STF-9 | AC-2 | in-ticket | step 1 |
| No 503 from these routes; the middleware waits | staff.md §11; STF-7; MC-14 | AC-15 | in-ticket (the route adds nothing) | — |
| `allowed_actions` and every display field passed through | R-W-13; AEA-45-1 | AC-18 | in-ticket | steps 1–2 |
| `CaseDetail.events.last_event_id` | D-5; AEA-45-2 | AC-21 | **blocked-on UX session: OpenAPI amendment** (evidence only; `CaseDetail` in the OpenAPI still has 11 properties, re-checked at `c9b17ea`) | step 5 (conditional skip, built) |
| Server contract cases | AEA-45-3; AEA-59 format | AC-19 | in-ticket. Needs one new local-driver word (§8 R-1), still absent at `c9b17ea` | R4 → step 7 |
| J-6 extension and record | integrated-journeys §3–§4 | AC-20 | in-ticket. Built on AEA-57's harness. Every step stays `blocked-on AEA-30`, because the real login reads `demo_clock` | step 8 (built); R6 refreshes the record |
| Staff routes never call `open_case` | DO-4 §13; DO-3 §6 S-7 | AC-16 | in-ticket | §7 G-2 |
| REASON_REQUIRED constraint text: the OpenAPI example says "required for release, assign and change_priority"; AEA-29 (merged) builds `f"required for {name}"` (`_case_rules.py` line 266) | OpenAPI applyCaseAction 422; AEA-29 | no | **other-ticket** (AEA-52 integration). The route passes `constraint` through unchanged; the seam test asserts only the prefix `required for` | §8 R-5 |
| The wire models accept the **real** `CaseService` views, and real stored times render in America/Chicago | DO-4 §13; UI_CONTRACTS *Conventions*; R-4 | no | **added** as AC-23 (plan-added): the real `CaseService` over a seeded temp DB behind the routes; demo clock and session store doubled. The orchestrator posts the added criterion on issue #45 | R3 |
| Context rows | context-maintenance | AC-22 | in-ticket | step 9 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `getQueue`, `getCase`, `applyCaseAction`, `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag`, `getOversight` | WF-4 (staff console) | yes — `observability-contract.md` WF-4 row; middleware `OPERATIONS_BY_ROUTE` already lists all eight `(method, template)` pairs | CAP-4 (end to end is AEA-52's); EV "flags feed the review list (R-37), never the eval set unreviewed"; M-13, M-27 |

---

## 2. Boundary

### Owned files: the only files the implementer may create or edit

| File | Current (branch head `ea00827`) | Action this run |
|---|---|---|
| `src/meridian/web/routes/staff_cases.py` | built (`c6cdab6`, 292 lines) | **keep**. Edit only to fix a failure that R2 or R3 exposes, and record it in *Deviations* |
| `src/meridian/web/schemas/staff_cases.py` | built (`c6cdab6`, 399 lines) | **keep**; same rule |
| `src/meridian/web/container.py` | `register_staff_cases` body built (`c6cdab6`) | **keep**; it merges cleanly. Touch nothing else in the file |
| `tests/api/staff_cases_support.py` | built (355 lines) | keep. Step 7's driver may add helpers here (stay under 500 lines); never change `staff_app`'s signature |
| `tests/api/test_staff_cases_routes.py` | built (408 lines) | keep |
| `tests/api/test_staff_cases_access.py` | built | keep |
| `tests/api/test_staff_cases_refusals.py` | built | keep. `test_real_case_not_found_maps_to_404` now runs, because `CaseNotFound` exists on `main` |
| `tests/api/test_staff_cases_capture.py` | built | keep |
| `tests/api/test_staff_cases_seam.py` | absent | **create** (R3): plan-added AC-23 |
| `tests/api/test_contract_cases_staff_cases.py` | absent | **create** (R4 → step 7), only when `case_state` is available |
| `tests/contract/cases/staff_cases.py` | absent | **create** (R4 → step 7), only when `case_state` is available |
| `tests/journeys/j6/test_aea_45.py` | built | keep |
| `docs/testing/journeys/2026-10-21-AEA-45.md` | built | **rewrite** (R6) if `date +%F` prints `2026-10-21`; otherwise create `docs/testing/journeys/<date>-AEA-45.md` and leave this one as history |
| `.claude/reference/area-map.md` | A9 row edited on the branch; conflicts with `main` | **resolve** (R1): take `main`'s file, re-apply only the A9 *Status* cell |
| `.claude/state/icm-progress.md` | AEA-45 row added; merges cleanly | **edit** (R6): the AEA-45 row only |
| `docs/design/code-design.md` | AEA-45 `**Built:**` line; conflicts with `main` | **resolve** (R1): take `main`'s file, then add the AEA-45 line after the last `**Built:**` line |
| `tests/contract/openapi_cases.py`, `tests/contract/cases/README.md` | AEA-59's | **only when R1 = `granted`** (R0): the exact lines in §8 R-1, in their own commit. Otherwise never edit |

**One deviation from the ticket's paths.** The ticket names `tests/api/test_staff_cases_routes.py::…` for every test. A
single file would be about 700 lines, over the 500-line test hard cap in `code-structure.md`. So the tests are split across
four files with **unchanged test names**; §3 gives each test's file.

### Shared surfaces: read only, never edit

- `src/meridian/web/{app,middleware,deps,errors,logging,frontend}.py`, `web/routes/*.py` and `web/schemas/*.py` other than this
  ticket's two
- `src/meridian/domain/*` (incl. `views.py`), `src/meridian/services/*` (incl. `staff.py`, `reset.py`), `src/meridian/policy/*`
- `tests/api/openapi_check.py`, `tests/api/web_shell_support.py`, every other `tests/api/*_support.py`
- `tests/contract/openapi_{cases,driver,variants}.py`, `tests/contract/test_openapi_server.py`, `tests/contract/cases/README.md`
  (except as R-1 grants)
- `tests/journeys/support/`, `tests/journeys/affected.py`, `tests/fixtures/sqlite.py`, `tests/fakes/*`, `tests/conftest.py`
- `docs/ux/**` (the OpenAPI and `UI_CONTRACTS.md`), `apps/web/**`, the briefing, issued data, `docs/archive/`, `docs/parked/`

### Owned by other tickets: must not touch

- AEA-29: `services/cases.py`, `services/_case_*.py`, `services/handoff.py`, the `register_cases` hunk, `tests/journeys/j6/test_aea_29.py`
- AEA-30: `services/demo.py` and the `register_demo` hunk
- AEA-44, 46, 47, 48: their route/schema files and hunks
- AEA-47: `tests/journeys/j6/test_aea_47.py`. Its skipped `test_j6_queue_shows_wp4_case_overdue_after_advance` mentions
  AEA-45; leave it for AEA-47/52.
- AEA-59: the contract runner files, except the R-1 grant
- AEA-57: `tests/journeys/support/`
- the orchestrator: `.claude/state/build-ledger.md`

---

## 3. Requirements table

Level of every `tests/api` test: `mock-tested`. The middleware, the login route, `require_staff` and the error renderer
are real; the services are doubles. The exception is `test_staff_cases_seam.py`: its `CaseService` and SQLite DB are
real, while its demo clock and session store are doubles. Under integrated-journeys §4 it is still `mock-tested`
(in-process `TestClient`, no harness server).

| # | Requirement (ticket AC, abridged; full text in the issue) | How it is implemented | Verified by (file :: test) | Status at `ea00827` → this run |
|---|---|---|---|---|
| AC-1 | Every 2xx body validates against its OpenAPI response for each named example shape | Output wire models copied from the OpenAPI; doubles return each named example as the real `domain/views.py` type | `tests/api/test_staff_cases_routes.py` :: `test_getQueue_matches_openapi`, `test_getCase_matches_openapi`, `test_applyCaseAction_matches_openapi`, `test_recordContactActivity_matches_openapi`, `test_createFlag_matches_openapi`, `test_listFlags_matches_openapi`, `test_reviewFlag_matches_openapi`, `test_getOversight_matches_openapi` (each `assert_matches` + `response.json() == example`) | built → re-run in R2 |
| AC-2 | `result_line` per staff.md §6, eight actions | `result_line()` in `schemas/staff_cases.py` | `test_staff_cases_routes.py` :: `test_result_lines` (parametrised, 8) | built → R2 |
| AC-3 | Role matrix from x-roles before any service call; 403 carries `details.role`, `details.needs` (x-roles order), `details.reason` `wrong_role` | `actor: StaffActor = Depends(require_staff(...))` as the **first** parameter of each handler | `test_staff_cases_access.py` :: `test_role_matrix` | built → R2 |
| AC-4 | Representative assign / change_priority → 403 `needs ["supervisor"]`; `apply` never called | Second check: `_SUPERVISOR_ONLY(session=session, access=access)` | `test_staff_cases_access.py` :: `test_assign_and_priority_supervisor_only` | built → R2 |
| AC-5 | Two sessions acting as representative hand `apply` equal `StaffActor`s | The actor comes only from `require_staff` | `test_staff_cases_access.py` :: `test_actor_is_the_role` | built → R2 |
| AC-6 | `getCase` passes `CaseDetail` through unchanged; never 403 to a staff role | `CaseDetailOut.model_validate(view)` → `model_dump(mode="json")` | `test_staff_cases_routes.py` :: `test_case_detail_passthrough` | built → R2 |
| AC-7 | 404 for unknown; malformed → 404 on getCase, 400 field `reference` on actions / activities | Regex check in the route; structural `LookupError` match; rejection table | `test_staff_cases_refusals.py` :: `test_case_not_found_and_malformed_reference`, `test_real_case_not_found_maps_to_404`; real-service twin in `test_staff_cases_seam.py` | built → R2: `test_real_case_not_found_maps_to_404` must now **pass**, not skip |
| AC-8 | 409 VERSION_CONFLICT / CASE_ALREADY_CLAIMED / NOT_ALLOWED_IN_STATE with their details | `REJECTION_STATUS`; details copied | `test_staff_cases_refusals.py` :: `test_case_action_409s` | built → R2 |
| AC-9 | Named 422s stay 422; a missing `expected_version` → 400 from AEA-23's handler | Rejection table; `StrictInt` required field | `test_staff_cases_refusals.py` :: `test_named_422_vs_400` | built → R2 |
| AC-10 | Activity 201 with the label unchanged; 409s mapped | Pass-through + table | `test_staff_cases_refusals.py` :: `test_contact_activity` | built → R2 |
| AC-11 | Flag rules: reason null when blank; 2,001 chars → 400; `message_id` rejection; bad status; unknown flag; list order | Field validators; `Literal["reviewed"]`; table; pass-through | `test_staff_cases_refusals.py` :: `test_flags` | built → R2 |
| AC-12 | One demo-clock reading as `now`; no server-clock call in the route or schema file | `now = demo.clock_view().now` once per case handler | `test_staff_cases_capture.py` :: `test_now_is_demo_clock` + grep G-1 (§7) | built → R2 |
| AC-13 | Queue / oversight bodies carry no contact value | Output models `extra="ignore"`, `from_attributes=True`, documented fields only | `test_staff_cases_capture.py` :: `test_queue_and_oversight_carry_no_contact` | built → R2 |
| AC-14 | Staff free text never logged; no 400 echoes a value | Route logs nothing; the handler reads only loc/type/msg | `test_staff_cases_capture.py` :: `test_staff_text_never_logged` | built → R2 |
| AC-15 | 401 without session on all eight; 403 `role_reset`; reset wait → 200, never 503 | AEA-23 middleware (unchanged) | `test_staff_cases_access.py` :: `test_login_gate_role_reset_and_reset_wait` | built → R2 |
| AC-16 | No `open_case` in the route or schema file | — | grep G-2 (§7), re-run by `code-review-agent` | built → G-2 |
| AC-17 | One `request` record per call through the real container; actor + reason / outcome / note reach writes | `staff_full_app` (real `build_container`) + doubles | `test_staff_cases_capture.py` :: `test_wf4_case_entry_points_emit_records` | built → R2 |
| AC-18 | Views pass through unchanged per role | Output models never strip, default or rewrite | `test_staff_cases_routes.py` :: `test_views_pass_through_unchanged` | built → R2 |
| AC-19 | `tests/contract/cases/staff_cases.py` holds the server cases | Case file + local driver (step 7) | `tests/api/test_contract_cases_staff_cases.py` :: `test_staff_cases_contract_cases_drive_and_cover`; runner `uv run pytest tests/contract/test_openapi_server.py -k "Queue or Case or Contact or Flag or Oversight" -rs`. The strict form `CONTRACT_STRICT=1 …` is the wave-merge check once AEA-30 is merged | **not built** (R-1 absent) → R4 builds it when R1 = `landed` or `granted` |
| AC-20 [journey] | Extends J-6: claim → result line; queue and case carry display fields and `allowed_actions`; stale version → VERSION_CONFLICT; user-visible and stored state | `tests/journeys/j6/test_aea_45.py` on AEA-57's `journey` fixture | `uv run pytest -m journey tests/journeys/j6/test_aea_45.py -rs`. Today the whole file skips `blocked-on AEA-30` at step 0 (the login reads `demo_clock`); the record says `mock-tested`, *Blocked by* AEA-30 and AEA-52 | built, skips → if AEA30 = `yes` (R0) all seven steps must pass at `integrated with a scripted model` |
| AC-21 | `events.last_event_id` passed through | Not built until the OpenAPI amendment lands | `test_staff_cases_routes.py` :: `test_case_detail_carries_last_event_id` (skips `blocked-on UX session: OpenAPI amendment …` while the OpenAPI `CaseDetail` has no `events`) | built, skips → unchanged |
| AC-22 | Area map, ICM row, DO-3 §3 updated | R1 (re-applied after the merge), R6 | `git diff --stat` | built → R1, R6 |
| AC-23 (plan-added) [invariant] | With the **real** `CaseService` (AEA-29) over a seeded temporary DB behind the routes: the WP-2 claim on MHC-C-0007 answers 200 "Claimed · Riley (demo)" and stores `claimed` / `representative` / version + 1; a repeat answers 409 `VERSION_CONFLICT` with `current_version` and stores nothing; the supervisor's claim answers 409 `CASE_ALREADY_CLAIMED` with `claimed_by` "Riley"; a release without a reason answers 422 `REASON_REQUIRED` field `reason`; a CALL answers 201 with the label "Demo: recorded, not sent"; an unknown reference answers 404 with `details.reference`; the owner sees `allowed_actions: []`; queue, case and oversight bodies validate, and real times render with `-05:00` | Override `get_case_service` with a real `CaseService` over `temp_sqlite()` + `seed_demo` (§4.7) | `tests/api/test_staff_cases_seam.py` :: `test_real_case_service_wp2_claim`, `test_real_case_service_views_per_role` | **new** → R3 |
| WP-2 | The ticket's example pair on MHC-C-0007 | — | `test_staff_cases_routes.py` :: `test_wp2_example_pair_mhc_c_0007` (doubles); real-service twin `test_staff_cases_seam.py` :: `test_real_case_service_wp2_claim` | built → R2; twin new in R3 |
| (plan) | The hunk includes the router once; nothing without a web shell | Step 3 | `test_staff_cases_access.py` :: `test_register_hunk_includes_router_once` | built → R2 |

---

## 4. Shared code to use (copied from `main` `2ec19ad`; re-checked unchanged at `c9b17ea`)

### 4.1 Web shell (AEA-23): import exactly these

```python
from meridian.web.deps import (
    StaffAccess,          # Protocol: actor_for(session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal
    get_case_service,     # (request: Request) -> Any ; bound since AEA-29 (ef561fc) by register_cases (the real CaseService)
    get_demo_service,     # (request: Request) -> Any ; RuntimeError("not bound: get_demo_service") until AEA-30 binds Key("demo_service")
    get_flag_service,     # (request: Request) -> Any ; bound by AEA-44 (real FlagService)
    get_login_session,    # (context: RequestContext = Depends(get_request_context)) -> LoginSession
    get_staff_access,     # (request: Request) -> StaffAccess
    require_staff,        # (*roles: StaffRole) -> Callable[..., StaffActor]
)
from meridian.web.errors import ApiProblem
# class ApiProblem(Exception):
#     def __init__(self, status: int, code: ApiErrorCode, *, field: str | None = None, constraint: str | None = None,
#                  details: dict[str, object] | None = None, headers: Mapping[str, str] | None = None) -> None
```

`require_staff(*roles)` returns a function `dependency(session: LoginSession = Depends(get_login_session), access:
StaffAccess = Depends(get_staff_access)) -> StaffActor`. It raises `ApiProblem(403, ROLE_NOT_ALLOWED, details={"role":
result.role.value, "needs": [r.value for r in result.needs], "reason": result.reason})`. **Calling that returned
function directly** with `session=` and `access=` is the second check AC-4 needs.

`web/errors.py::handle_validation_error` turns any request-model failure into `400 VALIDATION_ERROR`, with `field` = the
dotted location after `body`/`path`/`query` and `constraint` = pydantic's `msg`. It reads only `loc`, `type` and `msg`.
So a `PydanticCustomError("text_too_long", "at most 2000 characters")` raised in a field validator becomes exactly
`field="note"`, `constraint="at most 2000 characters"`, with no value in the body.

The middleware already does four things, and **the routes add nothing to any of them**:

- resolves the session (401 `UNAUTHENTICATED` before any route);
- waits up to `limits.web.reset_wait_s` (5 s) on a held `ResetGate` for these eight operations (none is in
  `RESET_503_OPERATIONS`);
- stamps `X-Request-ID`;
- emits one `request` record per call with `route` = the matched template and `caller_role` (from
  `OPERATIONS_BY_ROUTE`, which already lists all eight pairs).

### 4.2 Domain (AEA-02 / AEA-02b)

```python
from meridian.domain.common import ApiErrorCode, CaseRef        # CaseRef.PATTERN == r"^MHC-C-[0-9]{4}$"
from meridian.domain.staff import STAFF_PERSONAS, LoginSession, StaffActor, StaffRole
# STAFF_PERSONAS: REPRESENTATIVE → StaffPersona(name="Riley", signature="Riley (demo)");
#   SUPERVISOR → ("Demo supervisor", "Demo supervisor"); OWNER → ("Demo business owner", "Demo business owner")
# tests also use: from meridian.domain.staff import DemoRole, actor_for   # actor_for(role: StaffRole) -> StaffActor
from meridian.domain.views import ActivityIn, CaseAction, CaseActionName, CaseActionRejected
# tests also use: ActivityResult, CaseDetail, CaseSummaryView, OversightView, QueueView
```

From `src/meridian/domain/views.py` (all `MeridianModel`: `extra="forbid", frozen=True, hide_input_in_errors=True,
str_strip_whitespace=True`):

```python
CaseActionName = Literal["claim", "release", "start", "wait", "resolve", "close_unresolved", "assign", "change_priority"]

class CaseAction(MeridianModel):          # = OpenAPI CaseActionRequest
    action: CaseActionName
    expected_version: int
    reason: str | None = None
    wake_up_at: dt.datetime | None = None
    outcome: str | None = None
    assignee: Literal["riley", "supervisor"] | None = None
    priority: Priority | None = None      # domain.common.Priority enum (P0…P4)

class CaseActionRejected(MeridianModel):  # = OpenAPI ApiError.error
    code: ApiErrorCode
    field: str | None = None
    constraint: str | None = None
    details: dict[str, JsonValue] | None = None

class ActivityIn(MeridianModel):          # = OpenAPI ActivityRequest
    kind: Literal["call", "email"]
    outcome: Literal["reached", "no_answer", "left_message"]
    note: str | None = None
    expected_version: int

# Views returned by CaseService (field names = the OpenAPI schemas):
# QueueView(as_of, staffing: StaffingView, live: tuple[QueueRow, ...], needs_my_action: tuple[QueueRow, ...])
# CaseDetail(case: CaseSummaryView, promise, brief: BriefView, identity, sources, conversation, activities, live,
#            other_cases, agent_version, as_of)
# CaseSummaryView(reference, reason, priority: PriorityView, lifecycle, owner, created_at, due_at, due_label, due_state,
#                 wake_up_at, promise_status, seed, version, allowed_actions: tuple[AllowedAction, ...])
# ActivityResult(activity: Activity, case: CaseSummaryView)
# OversightView(as_of, demo_now, staffing, alerts, lanes: OversightLanes, live_queue_length, new_flags_count)
# ClockView(now: dt.datetime, label: str, date_label: str)
```

### 4.3 Flags (AEA-44, `src/meridian/services/staff.py`)

```python
from meridian.services.staff import FlagIn, FlagRejected
# tests also use: FlagRecord

class FlagIn(MeridianModel):
    case_ref: CaseRef
    target: Literal["answer", "brief", "escalation"]
    message_id: str | None                                  # REQUIRED key (no default): always pass it
    note: str | None = Field(default=None, max_length=2000)
    reason: str | None = Field(default=None, max_length=2000)

class FlagRecord(MeridianModel):
    flag_id: str; target: str; reason: str | None; case_ref: CaseRef; message_id: str | None; note: str | None
    flagged_by: str; at: datetime; status: Literal["new", "reviewed"]; reviewed_by: str | None; reviewed_note: str | None

class FlagRejected(MeridianModel):
    code: Literal["CASE_NOT_FOUND", "FLAG_NOT_FOUND", "VALIDATION_ERROR"]
    field: str | None; constraint: str | None; details: dict[str, str] | None

class FlagService:
    def flag(self, flag: FlagIn, actor: StaffActor) -> FlagRecord | FlagRejected: ...    # stamps the demo clock itself
    def review(self, flag_id: str, note: str | None, actor: StaffActor) -> FlagRecord | FlagRejected: ...
    def list_flags(self) -> tuple[FlagRecord, ...]: ...                                  # newest first; no time
```

### 4.4 Service methods the routes call (cases.md §5–§6; AEA-29's merged code matches; AEA-30's branch confirms `clock_view`)

```python
CaseService.queue(role: StaffRole, now: datetime) -> QueueView                                          # CON-11
CaseService.detail(case_ref: CaseRef, role: StaffRole, now: datetime) -> CaseDetail                     # CON-12; raises CaseNotFound
CaseService.oversight(now: datetime) -> OversightView                                                   # CON-17
CaseService.apply(case_ref: CaseRef, action: CaseAction, actor: StaffActor, expected_version: int,
                  now: datetime) -> CaseSummaryView | CaseActionRejected                                # CON-13
CaseService.record_activity(case_ref: CaseRef, activity: ActivityIn, actor: StaffActor,
                            now: datetime) -> ActivityResult | CaseActionRejected                       # CON-15
DemoService.clock_view() -> ClockView                                                                   # .now is the demo clock (Chicago)
# AEA-29: class CaseNotFound(LookupError): __init__(self, case_ref: str); self.case_ref = case_ref
# Staff routes never call open_case (DO-4 §13).
```

### 4.5 OpenAPI facts the wire models copy (`ui-contracts.openapi.yaml`)

| operationId | Method + path | x-roles (order; first word) | 2xx | Errors documented | Named 2xx examples | Request examples |
|---|---|---|---|---|---|---|
| getQueue | GET `/api/staff/queue` | representative, supervisor | 200 `QueueResponse` | 401, 403 | SEEDED, STAFFED_WITH_WAITING, ALL_CAUGHT_UP, BRIEF_BEING_WRITTEN | — |
| getCase | GET `/api/staff/cases/{reference}` | representative, supervisor, owner | 200 `CaseDetail` | 401, 403, 404 | DEFAULT, BRIEF_BEING_WRITTEN, TRIMMED_STOP, SAFETY_CASE, LIVE_JOINED, WAITING, FEE_BEARING_CHANGE | — |
| applyCaseAction | POST `/api/staff/cases/{reference}/actions` | representative, supervisor | 200 `CaseActionResponse` | 400, 401, 403, 404, 409 (VERSION_CONFLICT, CASE_ALREADY_CLAIMED, NOT_ALLOWED_IN_STATE), 422 (REASON_REQUIRED, WAKE_UP_REQUIRED, OUTCOME_REQUIRED) | CLAIMED, WAITING, RESOLVED, ASSIGNED, PRIORITY_CHANGED | CLAIM (v3), WAIT (v5), RESOLVE (v8), RELEASE (v4), ASSIGN (v3), CHANGE_PRIORITY (v3) |
| recordContactActivity | POST `/api/staff/cases/{reference}/activities` | representative | 201 `ActivityResponse` | 400, 401, 403, 404, 409 (NOT_ALLOWED_IN_STATE, VERSION_CONFLICT) | CALL_REACHED, EMAIL_LEFT_MESSAGE | CALL (v4) |
| createFlag | POST `/api/staff/flags` | representative, supervisor | 201 `Flag` | 400, 401, 403, 404 | ANSWER | ANSWER (`case_ref` MHC-C-0007, `message_id` m-2) |
| listFlags | GET `/api/staff/flags` | representative, supervisor, owner | 200 `FlagsResponse` | 401, 403 | THREE, EMPTY | — |
| reviewFlag | PATCH `/api/staff/flags/{flag_id}` | supervisor | 200 `Flag` | 400, 401, 403, 404 (FLAG_NOT_FOUND) | REVIEWED | REVIEW |
| getOversight | GET `/api/staff/oversight` | supervisor | 200 `OversightResponse` | 401, 403 | SEEDED, AFTER_ADVANCE, SHIFT_ENDED_WITH_WAITING, NOTHING_URGENT | — |

The x-roles strings for applyCaseAction are `"representative (claim, …)"` and `"supervisor (all, …)"`; the role is the
first word. No schema sets `additionalProperties: false`. Every example date-time is `YYYY-MM-DDTHH:MM:SS-05:00`.
`load_document()` keeps them as strings. The 409/422 error examples are quoted in step 6.

Schema fields (all required unless marked optional; `X | None` means nullable):

- `Staffing`: `mode` ∈ {nobody_online, simulated_on_shift}, `label: str`, `banner: str | None`.
- `Priority`: `level` ∈ {P0…P4}, `word` ∈ {Safety, Danger, Time-sensitive, Standard, Routine}.
- `QueueRow` (16 fields):
  - `reference: str`, `priority: Priority`, `reason: str`, `customer_display_name: str`, `owner: str | None`
  - `created_at: date-time`, `due_at: date-time | None`, `due_label: str | None`
  - `due_state` ∈ {on_time, due_soon, overdue, no_due_time}, `wake_up_at: date-time | None`
  - `lifecycle` ∈ {live_queued, unassigned, claimed, in_progress, waiting, resolved, closed_unresolved}
  - `follow_up_short: str | None`, `seed: bool`, `brief_status` ∈ {ready, being_written, failed}
  - `queued_at: date-time | None`, `age_label: str | None`
- `QueueResponse`: `as_of: date-time`, `staffing: Staffing`, `live: list[QueueRow]`, `needs_my_action: list[QueueRow]`.
- `CaseSummary` (14 fields):
  - `reference`, `reason`, `priority: Priority`, `lifecycle` (as above), `owner: str | None`
  - `created_at`, `due_at | None`, `due_label | None`, `due_state` (as above), `wake_up_at | None`
  - `promise_status` ∈ {open, kept, missed, changed}, `seed: bool`, `version: int`
  - `allowed_actions: list[` {claim, claim_and_join, release, start, wait, resolve, close_unresolved, assign,
    change_priority, join_chat, send_live_message, hand_back, close_chat, log_call, log_email, flag} `]`
- `PromiseRecord`:
  - `text: str`, `due_at | None`, `due_label | None`, `policy_row: str`, `status` (as promise_status)
  - `follow_up: {channel ∈ {email, phone}, destination_label: str, on_record: bool, window: str | None} | None`
  - `history: list[{at: date-time, text: str, reason: str}]`
- `Brief`: `status` ∈ {ready, being_written, failed}, `headings: list[BriefHeading]` (exactly 8).
  - `BriefHeading`: `number: int (1–8)`, `key` ∈ {why, needs, know, says, ai_did, told, decide, who}, `title: str`,
    `checked: bool`, `items: list[BriefItem]`, `trimmed: bool`, `trim_note: str | None`, `not_generated: bool`.
  - `BriefItem`: `text: str`, `kind` ∈ {fact, claim, ai_action, told_customer, decision, contact},
    `source_ids: list[str]`, `changed: bool`.
- `CaseDetail.identity`: `status` ∈ {not_checked, code_sent, verified, not_verified, locked}, `line: str`, `demo_note: str`.
- `CaseSource` (12 fields):
  - `source_id`, `lookup_log_id`, `audience` ∈ {customer, staff_only}, `title`, `ref`, `version_date: date | None`
  - `snapshot: object`, `current: object | None`, `changed_since: bool`, `changed_note: str | None`
  - `current_unavailable: bool`, `version_label: str`
- `ChatLine`: `message_id: str`, `speaker: {kind ∈ {assistant, customer, representative, event}, display_name: str | None}`,
  `at: date-time`, `text: str`.
- `Activity`: `activity_id: str`, `kind` ∈ {call, email}, `outcome` ∈ {reached, no_answer, left_message},
  `note: str | None`, `at: date-time`, `by: str`, `label` const "Demo: recorded, not sent".
- `LiveState`: `state` ∈ {not_live, queued, joined, handed_back, closed}, `since: date-time | None`,
  `controller` ∈ {ai, human}.
- `CaseDetail` (11 fields): `case: CaseSummary`, `promise: PromiseRecord`, `brief: Brief`, `identity`,
  `sources: list[CaseSource]`, `conversation: list[ChatLine]`, `activities: list[Activity]`, `live: LiveState`,
  `other_cases: list[{reference: str, status: str}]`, `agent_version: str`, `as_of: date-time`. **No `events` today.**
- `CaseActionRequest`: required `action` (8 values), `expected_version: integer`. Optional nullable: `reason`,
  `wake_up_at: date-time`, `outcome`, `assignee` ∈ {riley, supervisor}, `priority` ∈ {P0…P4}.
- `CaseActionResponse`: `case: CaseSummary`, `result_line: str`.
- `ActivityRequest`: required `kind`, `outcome`, `expected_version: integer`; optional nullable `note`.
- `ActivityResponse`: `activity: Activity`, `case: CaseSummary`.
- `FlagRequest`: required `case_ref: str`, `target` ∈ {answer, brief, escalation}; optional nullable `message_id`,
  `note`, `reason`.
- `Flag` (11 fields): `flag_id`, `target`, `reason | None`, `case_ref`, `message_id | None`, `note | None`,
  `flagged_by: str`, `at: date-time`, `status` ∈ {new, reviewed}, `reviewed_by | None`, `reviewed_note | None`.
- `FlagsResponse`: `as_of: date-time`, `flags: list[Flag]`.
- `FlagReviewRequest`: required `status` const "reviewed"; optional nullable `note`.
- `OversightResponse`: `as_of` and `demo_now` (date-times), `staffing: Staffing`, `alerts: list[Alert]`,
  `lanes: {p0_p1, overdue, due_soon, unowned, stuck_waiting: Lane}`, `live_queue_length: int`, `new_flags_count: int`.
  - `Alert`: `type` ∈ {p0_p1_created, unowned, due_soon, overdue, stuck_waiting, shift_ended_with_queued},
    `case_ref: str | None`, `line: str`, `at: date-time`.
  - `Lane`: `count: int`, `rows: list[QueueRow]`.

### 4.6 Test support already on `main` (import read-only)

```python
from tests.api.openapi_check import assert_response_matches, load_contract, load_document
from tests.api.web_shell_support import (
    FakeHeartbeat, FakeSessionStore,  # .issue(role: DemoRole = CUSTOMER) -> token; .set_role(token, role, *, role_reset=False);
                                      # .session_of(token) -> LoginSession; implements LoginSessions + StaffAccess (real RoleRefusal)
    assert_matches, captured_log, cookie_header, error_body, full_app, login, make_client, make_settings,
    rand_word, records_of, reset_gate_of, effective_routes, session_cookie_value,
)
from tests.contract.openapi_variants import iter_response_examples, request_examples  # deep copies; NamedExample(.operation_id, .status, .name, .value)
from tests.fakes.clock import CHICAGO                     # ZoneInfo("America/Chicago")
from tests.fixtures.sqlite import ISSUED_DB               # issued scheduling DB path: open read-only only
from tests.journeys.support.run import JourneyRun          # journey file only (fixture `journey`)
```

- `full_app(monkeypatch, settings, *, store, heartbeat)` builds the app over the **real** `build_container` (every hunk,
  starters suppressed) and overrides the session store and heartbeat.
- Use `make_client(app)` as a context manager, so the lifespan runs and the hunk includes the router.
- Precedent for the builder pattern: `tests/api/staff_clock_support.py::clock_app`.

### 4.7 Real `CaseService` recipe for the seam test (R3)

This is AEA-29's own recipe (`tests/services/test_cases_contract.py::_seeded`). Import it read-only:

```python
from meridian.services.cases import CaseService
from meridian.services.handoff import BriefAssembler
from meridian.services.reset import seed_demo
from tests.fakes.clock import WORKED_PAIRS_NOW, FixedClock   # 2026-10-16 10:00 America/Chicago (-05:00)
from tests.fixtures.sqlite import TempStore, temp_sqlite      # temp copy of the issued DB, deleted on exit

with temp_sqlite() as db:                                     # db: TempStore (.uow, .db_path, .data_dir)
    with db.uow(write=True) as tx:
        assert seed_demo(tx, assembler=BriefAssembler()) == 4
        tx.commit()
    cases = CaseService(db.uow, FixedClock(WORKED_PAIRS_NOW))
    # stored state, read-only:
    # with db.uow() as tx:
    #     tx.connection.execute("SELECT lifecycle, owner_role, version FROM cases WHERE case_ref = ?", (REF,)).fetchone()
```

- `staff_app(...)` types `cases` as `FakeCaseService`. Do **not** change that signature. After
  `h = staff_app(monkeypatch, settings, demo=FakeDemoService(WORKED_PAIRS_NOW))`, set
  `h.app.dependency_overrides[get_case_service] = lambda: cases` (`get_case_service` from `meridian.web.deps`).
- **Never import `tests.services._case_fixtures`**: it is red under mypy on `main` (§8 R-10).
- After seeding, the `cases` rows are MHC-C-0005…0008 with `lifecycle 'unassigned'`, `owner_role NULL` and `version 1`.
  At `WORKED_PAIRS_NOW`, AEA-29's own test shows the oversight `unowned` lane holds MHC-C-0006 and MHC-C-0007.

---

## 5. Steps

**Module boundary (DO-3 §2.1).**

- `web/routes/staff_cases.py` depends on `web/deps.py` providers, `web/errors.py`, `web/schemas/staff_cases.py`,
  `domain/{common,staff,views}.py` and the types in `services/staff.py` (`FlagIn`, `FlagRejected`). The same direction is
  already used by `routes/staff_live.py`, which imports `services.live_chat`.
- It reaches `CaseService`, `FlagService` and `DemoService` only through small **private** typing Protocols declared in the
  route file (consumer-side interface segregation, as `routes/staff_clock.py::ClockAdvancer` does).
- It imports no service class and no adapter, and adds no new public seam.

### This run: steps R0–R7 (resume on the existing branch)

Steps 0–6 and 8 below are **built** on the branch (`c6cdab6`). They stay in this plan as the reference the reviewer
checks the code against. **Do not rewrite them.** Step 0 is replaced by R0. Step 7 is still to build (R4). Steps 9 and 10
are replaced by R1, R6 and R7.

**R0. Preflight (no edits).**

1. `cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-45`; `export UV_LINK_MODE=hardlink`.
   - `git status --short` prints nothing.
   - `git rev-parse --abbrev-ref HEAD` prints `aea-45-staff-cases-api`.
   - `git log -1 --format=%h` prints `ea00827`.
   - If any of these differ, stop and report.
2. `git log -1 --format=%h main`: note the SHA (`c9b17ea` or later).
3. Set three switches from `main` and the dispatch message. Write all three in the report.
   - **AEA30** = `yes` if `git show main:src/meridian/web/container.py | grep -c "No-op until AEA-30"` prints `0`;
     otherwise `no` (expected: `no`).
   - **R1** = `landed` if `git show main:tests/contract/openapi_cases.py | grep -c '"case_state"'` prints `1`.
     Otherwise `granted` if the dispatch message contains "R-1 granted to AEA-45". Otherwise `absent`.
   - **EVENTS** is set in R1 step 7, after the merge.

**R1. Merge `main` into the branch.**

1. `git merge --no-ff --no-commit main`. Expect conflicts in exactly two files: `.claude/reference/area-map.md` and
   `docs/design/code-design.md` (`git diff --name-only --diff-filter=U`). If any other file conflicts, run
   `git merge --abort` and stop.
2. **Area map.** `git checkout --theirs .claude/reference/area-map.md`. In `git merge main`, *theirs* is `main`.
   - Then edit the single row that begins `| 2 | **A9 Staff console** |` (there is exactly one on `main`). In its last
     cell:
     - replace the leading `partly built:` with `built:`;
     - replace the trailing `; the rest planned` with
       `; AEA-45 (c6cdab6): web/routes/staff_cases.py, web/schemas/staff_cases.py, register_staff_cases hunk`.
   - Change nothing else. The file's duplicated rows (A6, A11, A7a, A8 and A12 each appear twice on `main`) are not this
     ticket's (§8 R-13).
   - *Protects:* the other tickets' edits on `main` survive, and the A9 cell says what the branch built.
3. **Code design.** `git checkout --theirs docs/design/code-design.md`. Then insert one line directly after the **last**
   line that starts with `**Built:**` (on `c9b17ea` that is the AEA-24 line, line 196):
   `` **Built:** `web/routes/staff_cases.py`, `web/schemas/staff_cases.py`, the `register_staff_cases` hunk (AEA-45, `c6cdab6`). ``
4. `grep -c "^<<<<<<<\|^>>>>>>>" .claude/reference/area-map.md docs/design/code-design.md` prints `0` for both files.
5. `git add .claude/reference/area-map.md docs/design/code-design.md`, then commit the merge:
   ```
   git commit -m "Merge main into aea-45-staff-cases-api (AEA-29 merged)" \
     -m "Conflicts: .claude/reference/area-map.md, docs/design/code-design.md. Kept main's files; re-applied AEA-45's A9 status cell and Built line." \
     -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
   ```
6. `uv sync`, then `uv run python -c "import meridian.web.routes.staff_cases, meridian.services.cases"` exits 0.
7. **EVENTS** = the output of
   `uv run python -c "from tests.api.openapi_check import load_document; print('events' in load_document()['components']['schemas']['CaseDetail']['properties'])"`.
   - `False` is expected; go on.
   - `True` means the UX amendment landed. AC-21's test will stop skipping and fail, as R-6 intends. Stop after R2 and
     report `NEEDS R-6 follow-up` (the domain `CaseDetail` in `domain/views.py` is not this ticket's file).
8. `git diff --name-only main...HEAD` lists only the branch's files (the "built" rows of §2's table). If anything else
   appears, stop.

**R2. Re-run the built tests on the merged tree.**

`uv run --with pytest-xdist pytest -n 2 tests/api/test_staff_cases_routes.py tests/api/test_staff_cases_access.py tests/api/test_staff_cases_refusals.py tests/api/test_staff_cases_capture.py -q -rs`

- Expected: all pass. The only skip is `test_case_detail_carries_last_event_id` (blocked-on UX session).
- `test_real_case_not_found_maps_to_404` must now **pass**, not skip.
- A failure here is a merge regression. Fix it inside the owned files only, and record it in *Deviations*.

**R3. Create `tests/api/test_staff_cases_seam.py` (plan-added AC-23, about 170 lines).**

- **Module docstring:** "AEA-45 AC-23 (plan-added): the real CaseService (AEA-29) over a seeded temporary copy of the
  issued DB, behind the real routes, middleware and role check. The demo clock (AEA-30, not merged) and the session store
  are doubles. Level: mock-tested (in-process TestClient, no harness server). Issued and synthetic data only."
- **Imports:**
  - the §4.7 block;
  - `from collections.abc import Iterator`, `from contextlib import contextmanager`, `from pathlib import Path`,
    `from typing import Final`, `import pytest`;
  - `from meridian.domain.staff import DemoRole`;
  - `from meridian.web.deps import get_case_service`;
  - `from tests.api.staff_cases_support import FakeDemoService, StaffCasesHarness, as_role, staff_app`;
  - `from tests.api.web_shell_support import assert_matches, make_client, make_settings`.
- **Constants:** `REF: Final = "MHC-C-0007"`; `UNKNOWN: Final = "MHC-C-0099"`;
  `AS_OF: Final = "2026-10-16T10:00:00-05:00"`; `CASE: Final = f"/api/staff/cases/{REF}"`.
- **Helper `_real_app`.** `@contextmanager def _real_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) ->
  Iterator[tuple[StaffCasesHarness, TempStore]]`:
  1. `with temp_sqlite() as db:`;
  2. seed as in §4.7 and build `cases`;
  3. `h = staff_app(monkeypatch, make_settings(tmp_path), demo=FakeDemoService(WORKED_PAIRS_NOW))`;
  4. `h.app.dependency_overrides[get_case_service] = lambda: cases`;
  5. `yield h, db`.
- **Helper `_stored`.** `def _stored(db: TempStore) -> tuple[str, str | None, int]`: run the read-only `SELECT lifecycle,
  owner_role, version FROM cases WHERE case_ref = ?` from §4.7 and return the row as a tuple.

**`test_real_case_service_wp2_claim(monkeypatch, tmp_path)`.** Use `with _real_app(...) as (h, db), make_client(h.app) as
client:`, with `rep = as_role(h, DemoRole.REPRESENTATIVE)` and `sup = as_role(h, DemoRole.SUPERVISOR)`. Every response
also passes `assert_matches(response, "<operationId>")`.

| Step | Request | Expect |
|---|---|---|
| a | rep GET `/api/staff/queue` | 200; `body["as_of"] == AS_OF`; exactly one `needs_my_action` row with `reference == REF`, and it has `lifecycle "unassigned"` and `owner None` |
| b | rep GET `CASE` | 200; 8 brief headings; `"claim" in body["case"]["allowed_actions"]`; `v0 = body["case"]["version"]`, and `v0 == _stored(db)[2]` |
| c | rep POST `CASE + "/actions"` `{"action": "claim", "expected_version": v0}` | 200; `result_line == "Claimed · Riley (demo)"`; `case.owner == "Riley"`; `case.lifecycle == "claimed"`; `case.version == v0 + 1`; `_stored(db) == ("claimed", "representative", v0 + 1)` |
| d | the same body again | 409; `error.code == "VERSION_CONFLICT"`; `error.details["current_version"] == v0 + 1`; `_stored(db)` unchanged |
| e | sup POST `{"action": "claim", "expected_version": v0 + 1}` | 409; `error.code == "CASE_ALREADY_CLAIMED"`; `error.details["claimed_by"] == "Riley"`; `_stored(db)` unchanged |
| f | rep POST `{"action": "release", "expected_version": v0 + 1}` | 422; `error.code == "REASON_REQUIRED"`; `error.field == "reason"`; `error.constraint.startswith("required for")`; `_stored(db)` unchanged |
| g | rep POST `CASE + "/activities"` `{"kind": "call", "outcome": "reached", "expected_version": v0 + 1}` | 201; `body["activity"]["label"] == "Demo: recorded, not sent"` |
| h | rep GET `/api/staff/cases/MHC-C-0099` | 404; `error.code == "CASE_NOT_FOUND"`; `error.details == {"reference": UNKNOWN}` |

**`test_real_case_service_views_per_role(monkeypatch, tmp_path)`.** Use the same harness; every response passes
`assert_matches`.

- For each of `DemoRole.REPRESENTATIVE` and `DemoRole.SUPERVISOR`: GET queue → 200; `body["as_of"] == AS_OF`; every
  `needs_my_action` row's `created_at` ends with `"-05:00"`. This is R-4 on real stored times.
- `DemoRole.OWNER`: GET `CASE` → 200 and `body["case"]["allowed_actions"] == []` (computed by the real service).
- `DemoRole.SUPERVISOR`: GET `/api/staff/oversight` → 200;
  `sorted(r["reference"] for r in body["lanes"]["unowned"]["rows"]) == ["MHC-C-0006", "MHC-C-0007"]`.
- Never print a body. Bodies carry the seeded customer's display name only, but keep the output clean.

Iterate with `uv run pytest tests/api/test_staff_cases_seam.py -q -rs`. A failure that shows a wire model rejecting a
real view is a real seam bug:

- fix it in `schemas/staff_cases.py` without stripping, defaulting or rewriting any value;
- if the real view breaks the **OpenAPI** (not just our model), stop and report it as an AEA-29 seam finding. Never edit
  `services/*` or `domain/*`.

**R4. AC-19 (step 7), by the R1 switch.**

- **`landed`:** build step 7 exactly as written below (the case file plus the local driver).
- **`granted`:** first make the R-1 edit (§8 R-1, the exact lines). Run
  `uv run pytest tests/contract/test_openapi_server.py -k "well_formed or format_example" -q`; it passes. Commit it on its
  own:
  - `git add tests/contract/openapi_cases.py tests/contract/cases/README.md`;
  - message `AEA-59 follow-up (R-1, granted to AEA-45): case_state local-driver word`, last line
    `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

  Then build step 7.
- **`absent`:** write neither step-7 file. Report AC-19 as `blocked-on R-1 (case_state word)`. Everything else in this
  run still goes ahead.

**One change to step 7 since the last plan.** Its paragraph *Why none of these is red on today's `main`* is out of date:
`case_service` is now bound. Drives that reach a case route now skip with `not bound: get_demo_service`, because the demo
provider resolves after the case provider and raises. The flag drives that reach the real `FlagService` still skip with
`not bound: demo_clock`. If AEA30 = `yes`, all of these run for real and must give the statuses in step 7's tables. Those
statuses follow AEA-29's merged check order (R-2).

**R5. Gates.** Run §7's checks A → H, cheapest first; stop at the first red.

**R6. Record and context rows** (after the R7 code commit, so its SHA is known).

1. **Record.** Rewrite `docs/testing/journeys/2026-10-21-AEA-45.md` (or create `<date>-AEA-45.md`, §2). Keep step 8's
   table shape and fill it from this run:
   - *Claim:* add AC-23 and, if built, AC-19.
   - *Level:* `mock-tested` for the API tests (service doubles) and for the seam test (real `CaseService` and SQLite,
     doubled clock and session store). The J-6 file did not run integrated, because it is blocked at step 0 by AEA-30,
     unless AEA30 = `yes`; then `integrated with a scripted model` for its seven steps.
   - *Tested revision:* the R7 code commit SHA.
   - *Result:* the counts printed by checks C, D and E, plus every skip reason quoted.
   - *Remaining limitations:* no real `DemoService`; AC-21 waits on the OpenAPI amendment; the AC-19 strict run waits on
     AEA-30; no browser leg (AEA-62).
   - *Blocked by:* AEA-30 (login and `demo_service`) for J-6 at `integrated with a scripted model`; R-1 for AC-19 when
     R1 = `absent`; AEA-52 for CAP-4 end to end.
2. **ICM row.** Replace the row that starts
   `| Routes verified against code and tests | provisional | 2026-10-21: area map A9 → web/routes/staff_cases.py` with
   one row of at most 400 characters:
   `| Routes verified against code and tests | provisional | 2026-10-21: area map A9 → web/routes/staff_cases.py, web/schemas/staff_cases.py (AEA-45, <code sha>) checked against tests/api/test_staff_cases_*.py incl. a real-CaseService seam test (<N> passed, <S> skipped); record docs/testing/journeys/<date>-AEA-45.md | <tail> |`
   - `<tail>` is `Each slice adds its route; verified when every area-map row is actual` when AC-19 is built.
   - Otherwise it is `Server contract cases (AC-19) wait on the case_state word; verified when every area-map row is actual`.
3. **SHA in the area map and DO-3.** If R2–R4 changed any file under `src/`, replace `c6cdab6` in the A9 cell and in the
   AEA-45 `**Built:**` line with the R7 code commit SHA. Otherwise leave `c6cdab6`.
4. `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` shows no **new** FAIL. The
   `FAIL icm … (budget 8192 B)` is pre-existing (the file is 15,697 B on `main`): report it, and do not trim other
   tickets' rows.

**R7. Commits.** Use explicit paths only. Never `git add -A`, never push, never force-push.

1. **Code and tests** (after R5 is green):
   - `git add tests/api/test_staff_cases_seam.py`;
   - plus, when built, `tests/api/test_contract_cases_staff_cases.py tests/contract/cases/staff_cases.py`;
   - plus any owned file changed in R2–R4 (`git status --short` lists them; every one must be in §2's table).
   - Message: `AEA-45: real-CaseService seam test and server contract cases (AC-23, AC-19)`. Drop "and server contract
     cases" and "AC-19" when R1 = `absent`.
   - Body: the ACs met and the waits (AC-20 integrated, AC-21, AC-19 strict). Last line
     `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
2. **Record and rows:**
   - `git add docs/testing/journeys/<date>-AEA-45.md .claude/state/icm-progress.md`;
   - plus `.claude/reference/area-map.md docs/design/code-design.md` if R6.3 changed them.
   - Message: `AEA-45: refresh journey record and context rows`, with the same last line.
3. **The plan file:** append to *Deviations* below, but do **not** commit it; the orchestrator commits plan files.
4. **Report:**
   - the R0 switches;
   - the merge SHA and every commit SHA;
   - each gate's output line;
   - the record path with its Level and *Blocked by*;
   - the AC table marked verified / waiting;
   - the pre-existing reds you saw (§7, §8 R-10).

### Step 0: preflight — SUPERSEDED by R0 (kept as the first run's record)

1. `cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-45`; `export UV_LINK_MODE=hardlink`; `uv sync`. Never copy a
   venv; no `node_modules`.
2. `grep -n "^class CaseAction\b\|^class ActivityIn\|^class CaseActionRejected" src/meridian/domain/views.py` → 3 hits.
   `grep -n "^class FlagIn\|^class FlagRejected" src/meridian/services/staff.py` → 2 hits.
3. `grep -n "def register_staff_cases" -A5 src/meridian/web/container.py` → still the "No-op until AEA-45" stub.
4. `grep -n '"case_state"' tests/contract/openapi_cases.py` → 1 hit (§8 R-1).
   - If it is missing and the orchestrator granted the two lines to this ticket, add them first (R-1 gives the exact
     text).
   - If it is missing and not granted: stop at step 7, finish everything else, and report
     `blocked-on R-1 (case_state word)`.

### Step 1: `src/meridian/web/schemas/staff_cases.py` — BUILT (`c6cdab6`; reference only)

Module docstring: `"""Wire shapes for CON-11…13 and CON-15…17 (OpenAPI field names; times in America/Chicago) and the
CON-13 result line (stage7/staff.md section 6). AEA-45."""`

1. Imports:
   ```python
   from __future__ import annotations

   from collections.abc import Mapping
   from datetime import date, datetime
   from types import MappingProxyType
   from typing import Annotated, Any, Final, Literal
   from zoneinfo import ZoneInfo

   from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PlainSerializer, StrictInt, field_validator
   from pydantic_core import PydanticCustomError

   from meridian.domain.staff import STAFF_PERSONAS, StaffActor, StaffRole
   from meridian.domain.views import CaseActionName
   ```
2. Constants and the time type:
   ```python
   WIRE_ZONE: Final = ZoneInfo("America/Chicago")           # UI_CONTRACTS Conventions: times in America/Chicago
   FLAG_TEXT_MAX_CHARS: Final = 2000                        # staff.md section 6 (STF-10)
   TEXT_TOO_LONG: Final = "at most 2000 characters"
   REFERENCE_CONSTRAINT: Final = "must match ^MHC-C-[0-9]{4}$"
   RESULT_RELEASED: Final = "Released back to Unassigned."  # staff.md section 6 proposal
   _WEEKDAYS: Final = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
   _MONTHS: Final = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

   def wire_time(value: datetime) -> str:
       """The same instant, written with its America/Chicago offset."""
       return value.astimezone(WIRE_ZONE).isoformat()

   WireTime = Annotated[AwareDatetime, PlainSerializer(wire_time, return_type=str, when_used="json")]
   ```
   *Protects:* a UTC instant from the store is shown as `…-05:00` (prototyped 2026-10-21: `14:14:00+00:00` UTC-converted
   CLAIMED `created_at` → `"2026-10-16T14:14:00-05:00"`). A naive datetime is a server bug: `AwareDatetime` → ValidationError → 500.
3. Request base and models. Inputs strip whitespace, ignore unknown keys (the OpenAPI schemas are open) and never echo
   input:
   ```python
   class _WireIn(BaseModel):
       model_config = ConfigDict(extra="ignore", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)

   def _blank_is_none(value: str | None) -> str | None:   # runs after stripping
       return None if value is None or value == "" else value

   def _capped_text(value: str | None) -> str | None:
       value = _blank_is_none(value)
       if value is not None and len(value) > FLAG_TEXT_MAX_CHARS:
           raise PydanticCustomError("text_too_long", TEXT_TOO_LONG)
       return value

   class CaseActionRequest(_WireIn):
       action: CaseActionName
       expected_version: StrictInt
       reason: str | None = None
       wake_up_at: AwareDatetime | None = None
       outcome: str | None = None
       assignee: Literal["riley", "supervisor"] | None = None
       priority: Literal["P0", "P1", "P2", "P3", "P4"] | None = None

       @field_validator("reason", "outcome", mode="after")
       @classmethod
       def _texts(cls, value: str | None) -> str | None:
           return _blank_is_none(value)

   class ActivityRequest(_WireIn):
       kind: Literal["call", "email"]
       outcome: Literal["reached", "no_answer", "left_message"]
       note: str | None = None
       expected_version: StrictInt

       @field_validator("note", mode="after")
       @classmethod
       def _note(cls, value: str | None) -> str | None:
           return _blank_is_none(value)

   class FlagRequest(_WireIn):
       case_ref: str
       target: Literal["answer", "brief", "escalation"]
       message_id: str | None = None
       note: str | None = None
       reason: str | None = None

       @field_validator("note", "reason", mode="after")
       @classmethod
       def _texts(cls, value: str | None) -> str | None:
           return _capped_text(value)

   class FlagReviewRequest(_WireIn):
       status: Literal["reviewed"]
       note: str | None = None

       @field_validator("note", mode="after")
       @classmethod
       def _note(cls, value: str | None) -> str | None:
           return _capped_text(value)
   ```
   *Protects:*
   - blank → `None`;
   - 2,001 characters → `400 VALIDATION_ERROR`, with `field` the field name and `constraint` "at most 2000 characters";
   - no value is ever echoed;
   - a missing `expected_version` → 400 field `expected_version`;
   - `"3"` or `true` for `expected_version` → 400.
4. Response base. It has **no** `str_strip_whitespace`, no defaults and no validator that changes a value:
   ```python
   class _WireOut(BaseModel):
       model_config = ConfigDict(extra="ignore", from_attributes=True, frozen=True)
   ```
   *Protects:* AC-13 (an undocumented attribute, such as a contact value, is never read) and AC-18 (a display string is
   never stripped or rewritten). A value outside a `Literal` is a server bug: ValidationError → 500.
5. One `_WireOut` subclass per OpenAPI schema in §4.5, with the same field names in the same order.
   - **Class names (suffix `Out`, to avoid clashing with the domain types):** `StaffingOut`, `PriorityOut`,
     `QueueRowOut`, `QueueResponse`, `CaseSummaryOut`, `PromiseFollowUpOut`, `PromiseHistoryItemOut`,
     `PromiseRecordOut`, `BriefItemOut`, `BriefHeadingOut`, `BriefOut`, `CaseIdentityOut`, `CaseSourceOut`,
     `SpeakerOut`, `ChatLineOut`, `ActivityOut`, `LiveStateOut`, `OtherCaseOut`, `CaseDetailOut`,
     `CaseActionResponse`, `ActivityResponse`, `FlagOut`, `FlagsResponse`, `AlertOut`, `LaneOut`, `OversightLanesOut`,
     `OversightResponse`.
   - **Types:**
     - date-time → `WireTime`; date → `date`; nullable → `X | None` (required, no default); enums → `Literal[...]`
     - `snapshot: dict[str, Any]`, `current: dict[str, Any] | None`
     - lists → `list[...]`, with these exceptions:
       - `BriefOut.headings: list[BriefHeadingOut] = Field(min_length=8, max_length=8)`
       - `BriefHeadingOut.number: int = Field(ge=1, le=8)`
       - `ActivityOut.label: Literal["Demo: recorded, not sent"]`
       - `CaseSummaryOut.allowed_actions: list[AllowedActionName]`, where `AllowedActionName` is a local `Literal` of the
         16 values
   - **Do not** add `events` to `CaseDetailOut` (AC-21 waits on the amendment).
6. Result line:
   ```python
   _ROLE_BY_NAME: Final[Mapping[str, StaffRole]] = MappingProxyType({p.name: r for r, p in STAFF_PERSONAS.items()})

   def chicago_label(moment: datetime) -> str:
       """'Mon Oct 19 · 9:00 am' in America/Chicago (staff.md section 6)."""
       local = moment.astimezone(WIRE_ZONE)
       hour12 = local.hour % 12 or 12
       return (f"{_WEEKDAYS[local.weekday()]} {_MONTHS[local.month - 1]} {local.day} · "
               f"{hour12}:{local.minute:02d} {'am' if local.hour < 12 else 'pm'}")

   def result_line(action: CaseActionName, case: CaseSummaryOut, actor: StaffActor) -> str:
       ...
   ```
   Body, one branch per action. The five sourced lines must equal the OpenAPI examples word for word.

   | Action | Returns | Raises when |
   |---|---|---|
   | `claim` | `f"Claimed · {actor.signature}"` | — |
   | `wait` | `f"Waiting until {chicago_label(case.wake_up_at)}"` | `case.wake_up_at is None` → `RuntimeError("wait result has no wake_up_at")` |
   | `resolve` | `f"{case.reference} resolved."` | — |
   | `assign` | `f"Assigned to {STAFF_PERSONAS[_ROLE_BY_NAME[case.owner]].signature}."` | `case.owner` is `None` or not a persona name → `RuntimeError("assign result has no known owner")` |
   | `change_priority` | `f"Priority is now {case.priority.level} · {case.priority.word}."` | — |
   | `release` | `RESULT_RELEASED` | — |
   | `start` | `f"In progress · {actor.signature}"` | — |
   | `close_unresolved` | `f"{case.reference} closed unresolved."` | — |

   The `·` is U+00B7, the character the OpenAPI examples use; ruff's RUF001 is already ignored.

### Step 2: `src/meridian/web/routes/staff_cases.py` — BUILT (`c6cdab6`; reference only)

Module docstring: `"""CON-11…13, CON-15…17: the staff case routes (stage7/staff.md section 6). AEA-45. Thin: role,
request, one demo-clock reading, one service call, rejection → documented status, serialise. Reads no server clock,
logs nothing, never opens a case, adds no reset check."""`

1. Imports:
   - stdlib: `import re`; `from collections.abc import Mapping, Sequence`; `from datetime import datetime`;
     `from types import MappingProxyType`; `from typing import Final, Literal, Protocol`
   - FastAPI: `from fastapi import APIRouter, Depends`; `from fastapi.responses import JSONResponse`;
     `from pydantic import BaseModel`
   - meridian: §4.1, §4.2, §4.3, and the schema names
   - **Never:** `datetime.now`, `time.time`, `date.today`, a logger, `open_case`.
2. Private Protocols (typing only):
   ```python
   class _ClockReading(Protocol):
       @property
       def now(self) -> datetime: ...

   class _DemoClock(Protocol):
       def clock_view(self) -> _ClockReading: ...

   class _Cases(Protocol):
       def queue(self, role: StaffRole, now: datetime) -> object: ...
       def detail(self, case_ref: CaseRef, role: StaffRole, now: datetime) -> object: ...
       def oversight(self, now: datetime) -> object: ...
       def apply(self, case_ref: CaseRef, action: CaseAction, actor: StaffActor, expected_version: int,
                 now: datetime) -> object: ...
       def record_activity(self, case_ref: CaseRef, activity: ActivityIn, actor: StaffActor, now: datetime) -> object: ...

   class _Flags(Protocol):
       def flag(self, flag: FlagIn, actor: StaffActor) -> object: ...
       def review(self, flag_id: str, note: str | None, actor: StaffActor) -> object: ...
       def list_flags(self) -> Sequence[object]: ...
   ```
3. Role dependencies (x-roles order; MC-4), the supervisor-only set and the refusal table:
   ```python
   _R, _S, _O = StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR, StaffRole.OWNER
   _QUEUE_ROLES = require_staff(_R, _S)
   _CASE_ROLES = require_staff(_R, _S, _O)
   _ACTION_ROLES = require_staff(_R, _S)
   _ACTIVITY_ROLES = require_staff(_R)
   _CREATE_FLAG_ROLES = require_staff(_R, _S)
   _LIST_FLAG_ROLES = require_staff(_R, _S, _O)
   _REVIEW_FLAG_ROLES = require_staff(_S)
   _OVERSIGHT_ROLES = require_staff(_S)
   _SUPERVISOR_ONLY = require_staff(_S)                                   # STF-3 second check
   SUPERVISOR_ONLY_ACTIONS: Final = frozenset({"assign", "change_priority"})
   REJECTION_STATUS: Final[Mapping[ApiErrorCode, int]] = MappingProxyType({
       ApiErrorCode.CASE_NOT_FOUND: 404, ApiErrorCode.FLAG_NOT_FOUND: 404,
       ApiErrorCode.VERSION_CONFLICT: 409, ApiErrorCode.CASE_ALREADY_CLAIMED: 409,
       ApiErrorCode.NOT_ALLOWED_IN_STATE: 409,
       ApiErrorCode.REASON_REQUIRED: 422, ApiErrorCode.WAKE_UP_REQUIRED: 422, ApiErrorCode.OUTCOME_REQUIRED: 422,
       ApiErrorCode.VALIDATION_ERROR: 400, ApiErrorCode.ROLE_NOT_ALLOWED: 403,
   })
   ```
4. Helpers:
   - `_problem(rejection: CaseActionRejected | FlagRejected) -> ApiProblem`:
     - `code = ApiErrorCode(str(rejection.code))`;
     - `status = REJECTION_STATUS.get(code)`; if `None` → `raise RuntimeError(f"unmapped rejection code {code.value}")`
       (a 500);
     - return `ApiProblem(status, code, field=rejection.field, constraint=rejection.constraint, details=None if
       rejection.details is None else dict(rejection.details))`.
     - *Protects:* the route never invents a field, constraint or details; it copies them, and they never carry a value
       (DO-4 §0).
   - `_case_ref(reference: str, *, malformed_status: Literal[400, 404]) -> CaseRef`:
     - `re.fullmatch(CaseRef.PATTERN, reference)` is `None` and 404 → `raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND)`
       (details `None`);
     - `None` and 400 → `raise ApiProblem(400, ApiErrorCode.VALIDATION_ERROR, field="reference",
       constraint=REFERENCE_CONSTRAINT)`;
     - else `return CaseRef(reference)`.
     - *Protects:* contract note 3; the malformed value is never echoed.
   - `_json(model: BaseModel, status: int = 200) -> JSONResponse`: `return JSONResponse(model.model_dump(mode="json"),
     status_code=status)`.
5. Handlers: all **sync** `def` (the real services use SQLite).
   - **Parameter order is load-bearing.** `actor: StaffActor = Depends(<role dep>)` comes **first**; then path params
     and the body; then `session`/`access` (applyCaseAction only); then the service providers, each with
     `# noqa: B008`.
   - **Why:** FastAPI solves `Depends` in parameter order and raises the first `ApiProblem` at once. So a refused role
     answers 403 before any provider resolves. An unbound provider therefore can never turn a 403 into a 500 (the
     contract runner relies on this, step 7), and no service method runs (AC-3).
   - Every case handler reads the demo clock **once**, after the route's own checks.

   **H1** `get_queue(actor = Depends(_QUEUE_ROLES), cases: _Cases = Depends(get_case_service), demo: _DemoClock = Depends(get_demo_service)) -> JSONResponse`:
   `now = demo.clock_view().now`; `return _json(QueueResponse.model_validate(cases.queue(actor.role, now)))`.

   **H2** `get_oversight(actor = Depends(_OVERSIGHT_ROLES), cases, demo)`: `now = demo.clock_view().now`;
   `return _json(OversightResponse.model_validate(cases.oversight(now)))`.

   **H3** `get_case(reference: str, actor = Depends(_CASE_ROLES), cases, demo)`:
   1. `case_ref = _case_ref(reference, malformed_status=404)`.
   2. `now = demo.clock_view().now`.
   3. Call the service:
      ```python
      try:
          detail = cases.detail(case_ref, actor.role, now)
      except LookupError as exc:
          if getattr(exc, "case_ref", None) != str(case_ref):
              raise                         # any other LookupError (a KeyError bug) stays a 500
          raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND, details={"reference": str(case_ref)}) from None
      ```
   4. `return _json(CaseDetailOut.model_validate(detail))`.

   **H4** `apply_case_action(reference: str, body: CaseActionRequest, actor = Depends(_ACTION_ROLES), session: LoginSession = Depends(get_login_session), access: StaffAccess = Depends(get_staff_access), cases, demo)`:
   1. `case_ref = _case_ref(reference, malformed_status=400)`.
   2. `if body.action in SUPERVISOR_ONLY_ACTIONS: _SUPERVISOR_ONLY(session=session, access=access)`. This is the function
      `require_staff` returned, called directly, so the 403 body comes from AEA-23's one mapping (`details.needs ==
      ["supervisor"]`, `reason` from the session). *Protects:* AC-4; `apply` is never called.
   3. `now = demo.clock_view().now`.
   4. `action = CaseAction.model_validate(body.model_dump())`. The field names are identical; `priority` "P2" becomes
      the `Priority` enum.
   5. `result = cases.apply(case_ref, action, actor, body.expected_version, now)`.
   6. `if isinstance(result, CaseActionRejected): raise _problem(result)`.
   7. `summary = CaseSummaryOut.model_validate(result)`;
      `return _json(CaseActionResponse(case=summary, result_line=result_line(body.action, summary, actor)))`.

   **H5** `record_contact_activity(reference: str, body: ActivityRequest, actor = Depends(_ACTIVITY_ROLES), cases, demo)`:
   1. `case_ref = _case_ref(reference, malformed_status=400)`.
   2. `now = demo.clock_view().now`.
   3. `activity = ActivityIn.model_validate(body.model_dump())`.
   4. `result = cases.record_activity(case_ref, activity, actor, now)`.
   5. If `result` is a `CaseActionRejected` → `raise _problem(result)`.
   6. `return _json(ActivityResponse.model_validate(result), status=201)`.

   **H6** `create_flag(body: FlagRequest, actor = Depends(_CREATE_FLAG_ROLES), flags: _Flags = Depends(get_flag_service))`
   (body after actor is fine: a body-validation error is raised only after the dependencies are solved):
   1. `if re.fullmatch(CaseRef.PATTERN, body.case_ref) is None: raise ApiProblem(400, ApiErrorCode.VALIDATION_ERROR,
      field="case_ref", constraint=REFERENCE_CONSTRAINT)`.
   2. `flag_in = FlagIn.model_validate({"case_ref": body.case_ref, "target": body.target, "message_id":
      body.message_id, "note": body.note, "reason": body.reason})`.
   3. `result = flags.flag(flag_in, actor)`; if it is a `FlagRejected` → `raise _problem(result)`.
   4. `return _json(FlagOut.model_validate(result), status=201)`.
   - **No clock read**: `FlagService` stamps `at` itself (staff.md §2).

   **H7** `list_flags(actor = Depends(_LIST_FLAG_ROLES), flags, demo)`:
   - `now = demo.clock_view().now`. This is the single reading: staff.md §10 makes `FlagsResponse.as_of` demo time, and
     `list_flags()` returns none.
   - `records = flags.list_flags()`.
   - `return _json(FlagsResponse(as_of=now, flags=[FlagOut.model_validate(r) for r in records]))`. The order is
     unchanged.

   **H8** `review_flag(flag_id: str, body: FlagReviewRequest, actor = Depends(_REVIEW_FLAG_ROLES), flags)`:
   1. `result = flags.review(flag_id, body.note, actor)`.
   2. If it is a `FlagRejected` → `raise _problem(result)`.
   3. `return _json(FlagOut.model_validate(result))`.
   - No clock read.
6. `build_router() -> APIRouter`: one `router.add_api_route(path, endpoint, methods=[...], operation_id=...,
   response_model=None)` per row of §4.5, with paths and operationIds exactly as there. Add `status_code=201` on
   `recordContactActivity` and `createFlag`. Module constants: `QUEUE_PATH = "/api/staff/queue"`,
   `CASE_PATH = "/api/staff/cases/{reference}"`, `ACTIONS_PATH = CASE_PATH + "/actions"`,
   `ACTIVITIES_PATH = CASE_PATH + "/activities"`, `FLAGS_PATH = "/api/staff/flags"`, `FLAG_PATH = FLAGS_PATH + "/{flag_id}"`,
   `OVERSIGHT_PATH = "/api/staff/oversight"`.

### Step 3: the `register_staff_cases` hunk in `src/meridian/web/container.py` — BUILT (`c6cdab6`; reference only)

Replace only the stub's body and docstring (same shape as `register_staff_clock` and `register_reads`):

```python
def register_staff_cases(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-45 staff API: queue, case, actions, contact log, flags, oversight routes (staff.md §6).

    Includes routes/staff_cases.py's router (CON-11…13, CON-15…17) once per app. Provides nothing: CaseService (AEA-29),
    FlagService (AEA-44) and DemoService (AEA-30) are bound by their own hunks; until a service is bound an allowed
    request answers 500 ("not bound: <provider>") after the role check. An app that create_app did not build has no
    web shell, so this does nothing.
    """
    from meridian.web.middleware import WebShellState
    from meridian.web.routes.staff_cases import build_router

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    if getattr(app.state, "staff_cases_routes_included", False):
        return  # a second lifespan on the same app must not add the routes again (FastAPI includes lazily)
    app.include_router(build_router())
    app.state.staff_cases_routes_included = True
```

*Protects:*

- `tests/unit/web/test_container.py::test_every_register_stub_present`: the docstring still names AEA-45 and no longer
  says "No-op until".
- `test_container_imports_only_policy_limits`: the imports stay inside the function.
- Existing tests that add a **probe** route for `getQueue` before the lifespan (`staff_session_support.container_app`,
  `test_gate.py`) keep their probe. The probe is registered first and FastAPI matches the first route, so those tests
  are unchanged.

### Step 4: `tests/api/staff_cases_support.py` — BUILT (`c6cdab6`; reference only)

Docstring: AEA-45 test support. Doubles of CaseService, FlagService and DemoService return the real `domain/views.py` /
`services/staff.py` types built from the OpenAPI examples. Not a conftest. Synthetic values only.

1. Constants:
   - `FIXED_NOW = datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO)` (−05:00; the AC-12 instant);
   - `SEEDED_REF = "MHC-C-0007"`;
   - `PATHS: Final[dict[str, str]]` = operationId → a concrete path: getCase/applyCaseAction/recordContactActivity on
     `MHC-C-0007`; reviewFlag on `/api/staff/flags/flg-3`; the GETs and createFlag on their own paths;
   - `METHODS` = operationId → HTTP method.
2. Example loaders:
   - `response_example(operation_id: str, name: str, status: str = "200") -> dict[str, Any]`: a deepcopy of the
     `.value` of the matching `iter_response_examples()` entry (`KeyError` if absent). Use the status "201" for
     recordContactActivity and createFlag.
   - `request_example(operation_id: str, name: str) -> dict[str, Any]` → `request_examples(operation_id)[name]`.
   - `error_example(operation_id: str, status: str, name: str) -> dict[str, Any]` → `response_example(...)["error"]`.
   - `x_roles(operation_id: str) -> list[str]`: the first word of each `x-roles` entry, via
     `load_document()["paths"][path][method]["x-roles"]` (path and method from `load_contract().operations`).
3. View builders, using the real types:
   - `queue_view(name="SEEDED") -> QueueView`, `case_detail(name="DEFAULT") -> CaseDetail`,
     `oversight_view(name="SEEDED") -> OversightView`: `X.model_validate(response_example(op, name))`;
   - `summary(name="CLAIMED", **changes) -> CaseSummaryView`:
     `CaseSummaryView.model_validate({**response_example("applyCaseAction", name)["case"], **changes})`;
   - `activity_result(name="CALL_REACHED") -> ActivityResult`;
   - `flag_record(op="createFlag", name="ANSWER", status="201") -> FlagRecord`;
   - `flag_records(name="THREE") -> tuple[FlagRecord, ...]`;
   - `case_rejected(operation_id, status, name) -> CaseActionRejected` = `CaseActionRejected.model_validate(error_example(...))`.
4. `as_attrs(value: Any) -> Any`: recursively turns dicts into `types.SimpleNamespace` (lists element-wise), **except**
   the values under the keys `snapshot`, `current` and `details`, which stay dicts. Used only where a test needs extra,
   undocumented attributes (AC-13).
5. `class CaseNotFoundStandIn(LookupError)`: `__init__(self, case_ref: str)` calls
   `super().__init__(f"no case {case_ref}")` and sets `self.case_ref = case_ref` (AEA-29's shape).
6. `@dataclass class ServiceCall: method: str; args: dict[str, Any]`.
7. `class FakeDemoService`:
   - `__init__(self, now: datetime = FIXED_NOW)`; `self.now = now`; `self.reads = 0`;
   - `clock_view()` does `self.reads += 1` and returns `ClockView(now=self.now, label="demo label", date_label="demo date label")`.
8. `class FakeCaseService` with settable attributes:
   - results: `queue_result = queue_view()`, `detail_result = case_detail()`,
     `detail_raises: BaseException | None = None`, `oversight_result = oversight_view()`, `apply_result = summary()`,
     `activity_result = activity_result()`;
   - `calls: list[ServiceCall]`.
   - Each method records one `ServiceCall` with every argument by name (`role`, `case_ref`, `now`, `action`, `actor`,
     `expected_version`, `activity`), then returns its result (or raises `detail_raises` in `detail`).
   - **No `open_case` method.**
9. `class FakeFlagService`:
   - `flag_result: object | None = None`, `review_result: object = flag_record("reviewFlag", "REVIEWED", "200")`,
     `list_result = flag_records()`, `calls: list[ServiceCall]`.
   - `flag(flag, actor)` records the call and returns `flag_result` if set. Otherwise it returns
     `flag_record().model_copy(update={"note": flag.note, "reason": flag.reason, "case_ref": flag.case_ref, "target":
     flag.target, "message_id": flag.message_id})`.
   - `review(flag_id, note, actor)` and `list_flags()` record and return their results.
10. `@dataclass class StaffCasesHarness: app: FastAPI; settings: Settings; store: FakeSessionStore; cases:
    FakeCaseService; flags: FakeFlagService; demo: FakeDemoService`.
11. `staff_app(monkeypatch, settings, *, store=None, cases=None, flags=None, demo=None) -> StaffCasesHarness`:
    - copy `tests/api/staff_clock_support.py::clock_app`;
    - the builder runs `register_web` and then `register_staff_cases` (both from `meridian.web.container`), then
      `container.build()`;
    - `monkeypatch.setattr(app_module, "build_container", build)`; `create_app(settings)`;
    - dependency overrides (zero-argument lambdas) for `get_login_sessions` and `get_staff_access` (both the store),
      `get_heartbeat` (`FakeHeartbeat()`), `get_case_service`, `get_flag_service` and `get_demo_service`.
12. `staff_full_app(monkeypatch, settings, *, store, cases, flags, demo) -> FastAPI`:
    `full_app(monkeypatch, settings, store=store, heartbeat=FakeHeartbeat())` plus the three service overrides (the real
    `build_container`, every hunk; AC-17).
13. `as_role(h: StaffCasesHarness, role: DemoRole) -> dict[str, str]` → `cookie_header(h.store.issue(role))`.
14. `call(client: TestClient, op: str, headers: dict[str, str], *, path: str | None = None, body: Any = None) -> Any`:
    sends `METHODS[op]` to `path or PATHS[op]` with `json=body` when not `None`.
15. `seeded_contact(customer_id: str = "MHC-10002") -> tuple[str, str]`:
    - opens `sqlite3.connect(f"file:{ISSUED_DB}?mode=ro", uri=True)`;
    - `SELECT email, service_address FROM customers WHERE customer_id = ?`;
    - closes in `finally`.
    - **Never print or log the values.** No phone column is read.

### Step 5: `tests/api/test_staff_cases_routes.py` — BUILT (`c6cdab6`; reference only)

Every test: `settings = make_settings(tmp_path)`; `h = staff_app(monkeypatch, settings)`; `with make_client(h.app) as
client:`.

- **`test_<operationId>_matches_openapi` (eight functions).** For each named 2xx example in §4.5, set the matching double
  result to the example's view and call the operation as an allowed role. Then `assert_matches(response,
  "<operationId>")` and `response.json() == example`. Specifics:
  - **applyCaseAction** pairs each response with a request: CLAIMED←CLAIM (representative), WAITING←WAIT
    (representative), RESOLVED←RESOLVE (representative), ASSIGNED←ASSIGN (supervisor), PRIORITY_CHANGED←CHANGE_PRIORITY
    (supervisor), with `apply_result = summary(name)`. Full-body equality also proves AC-2's five sourced lines.
  - **recordContactActivity:** CALL_REACHED and EMAIL_LEFT_MESSAGE, both sent with CALL.
  - **createFlag:** ANSWER ← ANSWER, with `flag_result = flag_record()`.
  - **listFlags:** THREE and EMPTY, with `demo.now = datetime.fromisoformat(example["as_of"])` and `list_result =
    tuple(FlagRecord.model_validate(f) for f in example["flags"])`.
  - **reviewFlag:** REVIEWED ← REVIEW on `/api/staff/flags/flg-3` as supervisor.
- **`test_result_lines`.** `@pytest.mark.parametrize` over `(action, role, case_changes, body_extra, expected)`:

  | action | role | case changes | body extra | expected |
  |---|---|---|---|---|
  | claim | rep | `{}` | `{}` | "Claimed · Riley (demo)" |
  | wait | rep | `{"lifecycle": "waiting", "wake_up_at": "2026-10-19T09:00:00-05:00"}` | `{"wake_up_at": "2026-10-19T09:00:00-05:00", "reason": "zqwait"}` | "Waiting until Mon Oct 19 · 9:00 am" |
  | resolve | rep | `{"lifecycle": "resolved"}` | `{"outcome": "zqdone"}` | "MHC-C-0007 resolved." |
  | assign | sup | `{"owner": "Riley"}` | `{"assignee": "riley", "reason": "zqassign"}` | "Assigned to Riley (demo)." |
  | change_priority | sup | `{"priority": {"level": "P2", "word": "Time-sensitive"}}` | `{"priority": "P2", "reason": "zqprio"}` | "Priority is now P2 · Time-sensitive." |
  | release | rep | `{"lifecycle": "unassigned", "owner": None}` | `{"reason": "zqrelease"}` | "Released back to Unassigned." |
  | start | rep | `{"lifecycle": "in_progress"}` | `{}` | "In progress · Riley (demo)" |
  | close_unresolved | rep | `{"lifecycle": "closed_unresolved"}` | `{"reason": "zqclose"}` | "MHC-C-0007 closed unresolved." |

  `apply_result = summary("CLAIMED", **case_changes)`; the body is `{"action": action, "expected_version": 4, **body_extra}`.
  Assert 200 and `response.json()["result_line"] == expected`.
- **`test_case_detail_passthrough` (AC-6).**
  - For each getCase example × each of representative, supervisor and owner: `detail_result = case_detail(name)`; for
    the owner, use `case_detail(name)` rebuilt with `case.allowed_actions = []`. Assert 200 and body == the double's
    dict.
  - Also assert:
    - the heading titles in order equal the example's;
    - `[h["number"] for h in body["brief"]["headings"]] == [1, …, 8]`;
    - `"staff_only" in {s["audience"] for s in body["sources"]}` where the example has one;
    - the owner's `body["case"]["allowed_actions"] == []`.
  - No 403 for any staff role.
- **`test_views_pass_through_unchanged` (AC-18).** For each role (rep and sup for getQueue and applyCaseAction claim;
  rep, sup and owner for getCase):
  - Start from the example dict and set distinctive values with `rand_word()`: every row's `reason`, `due_label`,
    `age_label` and `follow_up_short`; `identity.line`; every `BriefItem.source_ids` entry and the matching
    `CaseSource.source_id`; every `version_label`.
  - Set `priority.word` to a different valid word per role.
  - Set `allowed_actions`: rep `["claim", "flag"]`; sup `["claim", "assign", "change_priority", "flag"]`; owner `[]`.
  - Set `queued_at` to `"2026-10-16T09:31:00-05:00"`.
  - Validate the dict into the domain type for the double. Assert the response JSON equals the mutated dict (for
    applyCaseAction, `body["case"]`).
- **`test_case_detail_carries_last_event_id` (AC-21).** First lines:
  ```python
  props = load_document()["components"]["schemas"]["CaseDetail"]["properties"]
  if "events" not in props:
      pytest.skip("blocked-on UX session: OpenAPI amendment CaseDetail.events.last_event_id (Decision 2 option A, D-5)")
  ```
  Body (runs only after the amendment): the double returns `as_attrs({**DEFAULT, "events": {"last_event_id": 41}})`;
  expect 200, `assert_response_matches(response, "getCase")` and `response.json()["events"]["last_event_id"] == 41`.
  It **fails** until `CaseDetailOut` gains `events` (R-6). That is intended.
- **`test_wp2_example_pair_mhc_c_0007` (WP-2).** One test, five steps on one app:
  - (a) rep CLAIM → 200, `case.lifecycle` "claimed", `owner` "Riley", `version` 4, `result_line` "Claimed · Riley (demo)";
  - (b) `apply_result = case_rejected("applyCaseAction", "409", "CASE_ALREADY_CLAIMED")` → 409, `details.claimed_by`
    "Demo supervisor";
  - (c) `case_rejected(..., "VERSION_CONFLICT")` → 409 with `changed_by`, `changed_at`, `current_version` 4;
  - (d) `case_rejected("applyCaseAction", "422", "REASON_REQUIRED")` on a RELEASE without reason → 422, `field`
    "reason", `constraint` "required for release, assign and change_priority";
  - (e) rep `{"action": "assign", "assignee": "riley", "reason": rand_word(), "expected_version": 4}` → 403,
    `details.needs == ["supervisor"]`, and the count of `apply` calls did not grow.
  - Every response passes `assert_matches`.

### Step 6: the other three test files — BUILT (`c6cdab6`; reference only)

**`tests/api/test_staff_cases_access.py`** (≈ 230 lines):
- **`test_role_matrix` (AC-3).** Parametrise over 8 operations × 4 roles (customer, representative, supervisor, owner).
  - The allowed set per operation is `x_roles(operation_id)`.
  - Each call uses the operation's default request: CLAIM for applyCaseAction, CALL for recordContactActivity, ANSWER for
    createFlag, REVIEW on `flg-3` for reviewFlag. So every refused request carries a valid body.
  - **Refused cell:** 403; `assert_matches`; `details.role` = the role; `details.needs` = `x_roles(operation_id)` (e.g.
    `["representative", "supervisor"]` on getQueue); `details.reason == "wrong_role"`; `h.cases.calls == []`,
    `h.flags.calls == []`, `h.demo.reads == 0`.
  - **Allowed cell:** 2xx.
  - Expected refusals: customer on all 8; owner on everything except getCase and listFlags; representative on reviewFlag
    and getOversight; supervisor only on recordContactActivity.
- **`test_assign_and_priority_supervisor_only` (AC-4).** The representative sends ASSIGN and CHANGE_PRIORITY → two 403s
  with `needs ["supervisor"]`, both validated; zero `apply` calls. The supervisor sends both → two 200s.
- **`test_actor_is_the_role` (AC-5).** Issue two tokens with `store.issue(DemoRole.REPRESENTATIVE)`; each sends CLAIM.
  The two recorded `actor` arguments compare equal, and equal `actor_for(StaffRole.REPRESENTATIVE)`
  (`StaffActor(role=representative, name="Riley", signature="Riley (demo)")`).
- **`test_login_gate_role_reset_and_reset_wait` (AC-15).**
  - (a) With no cookie, each of the 8 operations answers 401 `UNAUTHENTICATED`; `assert_matches` on each.
  - (b) `store.set_role(token, DemoRole.CUSTOMER, role_reset=True)` → getQueue 403 with `details.reason == "role_reset"`.
  - (c) A thread takes `reset_gate_of(h.app).hold()`, sets a `threading.Event`, sleeps 0.5 s and releases. After the
    event, `client.get("/api/staff/queue", …)` as representative → 200 (never 503), with elapsed ≥ 0.3 s. Join the
    thread in `finally`.
- **`test_register_hunk_includes_router_once` (plan).**
  - A bare `FastAPI()` passed through `register_staff_cases(Container(settings=…, limits=Limits()), app, …)` gets no
    `/api/staff/queue` in `effective_routes(app)`.
  - `staff_app` entered twice (`with make_client(h.app)` two times in a row) lists `("/api/staff/queue", "getQueue")`
    exactly once, and each of the 8 operationIds exactly once.

**`tests/api/test_staff_cases_refusals.py`** (≈ 290 lines):
- **`test_case_not_found_and_malformed_reference` (AC-7).** Each response validated with `assert_matches`
  (CaseNotFound / ValidationError):
  - getCase `MHC-C-0099` with `detail_raises = CaseNotFoundStandIn("MHC-C-0099")` → 404 `details == {"reference": "MHC-C-0099"}`;
  - applyCaseAction / recordContactActivity with `CaseActionRejected(code=ApiErrorCode.CASE_NOT_FOUND, details={"reference": "MHC-C-0099"})` → 404;
  - createFlag with `FlagRejected(code="CASE_NOT_FOUND", field=None, constraint=None, details={"reference": "MHC-C-0099"})` → 404;
  - getCase `MHC-C-7` → 404 with `details` null, and `detail` never called;
  - actions / activities on `MHC-C-7` → 400 field `reference`, no service call;
  - createFlag `case_ref` "MHC-C-7" → 400 field `case_ref`, no flag call;
  - `detail_raises = KeyError("x")` → 500 (any other `LookupError` is not a 404).
- **`test_real_case_not_found_maps_to_404`.** `mod = pytest.importorskip("meridian.services.cases")`;
  `exc = getattr(mod, "CaseNotFound", None)`; if `None` → `pytest.skip("AEA-29 CaseNotFound not merged")`. Otherwise
  `detail_raises = exc("MHC-C-0099")` → 404. This seam check turns on by itself when AEA-29 lands.
- **`test_case_action_409s` (AC-8).** The three applyCaseAction 409 examples as `case_rejected(...)` → 409;
  `body["error"] == example["error"]`; each validated.
- **`test_named_422_vs_400` (AC-9).** The three 422 examples → 422 with the example's field and constraint. A body
  `{"action": "claim"}` → 400 `field == "expected_version"` with zero `apply` calls. All validated.
- **`test_contact_activity` (AC-10).** CALL → 201; `activity.label == "Demo: recorded, not sent"`, equal to the double's.
  The two recordContactActivity 409 examples → 409, validated.
- **`test_flags` (AC-11).**
  - ANSWER without `reason`, and with `reason: "   "` → 201 with `reason` null; the recorded `FlagIn.reason is None`.
  - `note`, `reason` and review `note` of 2,001 letters (`"zq" * 1000 + "z"`) → 400 with the field named and
    `constraint == "at most 2000 characters"`; the body does not contain the text.
  - A `FlagRejected(code="VALIDATION_ERROR", field="message_id", constraint="not a message of this case", details=None)`
    → 400 with both.
  - Review `{"status": "new"}` → 400 `field == "status"`.
  - `FlagRejected(code="FLAG_NOT_FOUND", field=None, constraint=None, details={"flag_id": "flg-99"})` → 404.
  - `listFlags` returns the THREE flags in the double's order: `[f["flag_id"] for f in body["flags"]]` equals the
    double's.

**`tests/api/test_staff_cases_capture.py`** (≈ 250 lines):
- **`test_now_is_demo_clock` (AC-12).**
  - `FakeDemoService(FIXED_NOW)`; call getQueue, getCase, applyCaseAction (CLAIM), recordContactActivity (CALL) and
    getOversight.
  - Each recorded `now == FIXED_NOW`, and `demo.reads` grows by exactly 1 per request.
  - listFlags: `reads` +1 and `body["as_of"] == "2026-10-19T07:00:00-05:00"`. createFlag and reviewFlag: `reads` +0.
  - The grep half of AC-12 is G-1 in §7.
- **`test_queue_and_oversight_carry_no_contact` (AC-13).**
  - `email, address = seeded_contact()`.
  - Queue double: `as_attrs(response_example("getQueue", "SEEDED"))` with `contact_email=email` and
    `service_address=address` set on every row namespace in `live` and `needs_my_action`. Do the same for every row of
    every oversight lane.
  - Assert the double rows really have the attributes. Then assert both strings are absent from the getQueue and
    getOversight response texts (`response.text`).
  - Never print the values.
- **`test_staff_text_never_logged` (AC-14).** Use `caplog.set_level(logging.DEBUG)` and `with captured_log() as stream`.
  - Send distinctive `rand_word()` values through the routes: a release reason and a resolve outcome (as representative,
    `apply_result = summary()`), an activity note, a flag note and a flag reason.
  - Assert each value appears in the recorded call arguments (`action.reason`, `action.outcome`, `activity.note`,
    `FlagIn.note`, `FlagIn.reason`), and is absent from `stream.getvalue()` and from `caplog.text`, the `request`
    records included.
  - One 400 (a flag note of 2,001 letters) body does not contain the note.
- **`test_wf4_case_entry_points_emit_records` (AC-17).** Use `staff_full_app` (the real `build_container`).
  - Drive each of the 8 operations once, as an allowed role, inside `captured_log()`.
  - `records_of(stream, "request")` holds 8 records. For each: `request_id == response.headers["X-Request-ID"]`,
    `route == load_contract().operations[op].path_template`, `status == response.status_code`, `caller_role` = the
    role. No `route` contains `"MHC-C-"`.
  - The recorded writes carry `actor.role` / `actor.name` plus the reason (apply RELEASE), the note (activity),
    note / reason (flag) and note (review).
  - Print the 8 `(route, status, caller_role)` tuples and the 4 actors.

### Step 7: `tests/contract/cases/staff_cases.py` and its local driver (AC-19) — TO BUILD in R4 (see R4 for the one change)

**Format** is AEA-59's (`tests/contract/cases/README.md`; checked by `tests/contract/openapi_cases.py`):

- `ROUTE_FILE: Final = "staff_cases"` and `CASES: Final[dict[str, dict[str, object]]]`, keyed by operationId, each
  `{"public": False, "drives": (...)}`.
- **Drive keys allowed:** `name, status, code, preconditions, setup, body, path, thread, reference, events,
  last_event_id, frames, response_example, reader_example`. **No `by`, no `with`.**
- **Preconditions only from the closed vocabulary:** `login`, `role:<customer|representative|supervisor|owner>`, the
  local-only word `case_claimed_by_supervisor`, and the new local-only word **`case_state`** (R-1).
- **Body:** `{"example": NAME}` or `{"raw": JSON}`.
- **Path:** `{"reference": "<literal>"}` or `{"flag_id": "<literal>"}`. Literals are sent as given.
- Each named request example must appear in a 2xx drive.

**Module docstring** must state:

- the vocabulary;
- that `"MHC-C-0007"` is AEA-31's first-boot seed case (unassigned, version 1, `services/reset.py`);
- that the raw-body drives with `expected_version: 1` rely on that seed;
- that `case_state` marks drives whose case or flag state the runner cannot build on a fresh first-boot copy, so they
  are proved by `tests/api/test_contract_cases_staff_cases.py` at `mock-tested`.

Module constants: `_REP = ("login", "role:representative")`, `_SUP = ("login", "role:supervisor")`,
`_OWN = ("login", "role:owner")`, `_CUST = ("login",)`, `_SEEDED = {"reference": "MHC-C-0007"}`,
`_UNKNOWN = {"reference": "MHC-C-9999"}`, `_MALFORMED = {"reference": "MHC-C-7"}`, `_FLAG = {"flag_id": "flg-1"}`,
`_LONG: Final = "z" * 2001`.

**Drives.** Columns: name, status, code, preconditions, path, body.

- **getQueue** (no path, body `None`):

  | name | status | code | preconditions |
  |---|---|---|---|
  | `representative_reads` | 200 | — | `_REP` |
  | `supervisor_reads` | 200 | — | `_SUP` |
  | `no_session` | 401 | UNAUTHENTICATED | `()` |
  | `customer_refused` | 403 | ROLE_NOT_ALLOWED | `_CUST` |
  | `owner_refused` | 403 | ROLE_NOT_ALLOWED | `_OWN` |

- **getCase** (body `None`):

  | name | status | code | preconditions | path |
  |---|---|---|---|---|
  | `representative_reads` | 200 | — | `_REP` | `_SEEDED` |
  | `owner_reads` | 200 | — | `_OWN` | `_SEEDED` |
  | `no_session` | 401 | UNAUTHENTICATED | `()` | `_SEEDED` |
  | `customer_refused` | 403 | ROLE_NOT_ALLOWED | `_CUST` | `_SEEDED` |
  | `unknown_case` | 404 | CASE_NOT_FOUND | `_REP` | `_UNKNOWN` |
  | `malformed_reference` | 404 | CASE_NOT_FOUND | `_REP` | `_MALFORMED` |

- **applyCaseAction** (path `_SEEDED` unless stated):

  | name | status | code | preconditions | path | body |
  |---|---|---|---|---|---|
  | `claim` | 200 | — | `(*_REP, "case_state")` | | CLAIM |
  | `wait` | 200 | — | `(*_REP, "case_state")` | | WAIT |
  | `resolve` | 200 | — | `(*_REP, "case_state")` | | RESOLVE |
  | `release` | 200 | — | `(*_REP, "case_state")` | | RELEASE |
  | `assign` | 200 | — | `(*_SUP, "case_state")` | | ASSIGN |
  | `change_priority` | 200 | — | `(*_SUP, "case_state")` | | CHANGE_PRIORITY |
  | `claim_seeded` | 200 | — | `_REP` | | raw `{"action": "claim", "expected_version": 1}` |
  | `no_session` | 401 | UNAUTHENTICATED | `()` | | CLAIM |
  | `owner_refused` | 403 | ROLE_NOT_ALLOWED | `_OWN` | | CLAIM |
  | `assign_as_representative` | 403 | ROLE_NOT_ALLOWED | `_REP` | | ASSIGN |
  | `unknown_case` | 404 | CASE_NOT_FOUND | `_REP` | `_UNKNOWN` | CLAIM |
  | `malformed_reference` | 400 | VALIDATION_ERROR | `_REP` | `_MALFORMED` | CLAIM |
  | `missing_expected_version` | 400 | VALIDATION_ERROR | `_REP` | | raw `{"action": "claim"}` |
  | `stale_version` | 409 | VERSION_CONFLICT | `_REP` | | CLAIM (v3 ≠ seed v1) |
  | `claimed_by_supervisor` | 409 | CASE_ALREADY_CLAIMED | `(*_REP, "case_claimed_by_supervisor")` | | CLAIM |
  | `resolve_before_claim` | 409 | NOT_ALLOWED_IN_STATE | `_REP` | | raw `{"action": "resolve", "expected_version": 1, "outcome": "Credit decision recorded"}` |
  | `release_without_reason` | 422 | REASON_REQUIRED | `_REP` | | raw `{"action": "release", "expected_version": 1}` |
  | `wait_without_wake_up` | 422 | WAKE_UP_REQUIRED | `_REP` | | raw `{"action": "wait", "expected_version": 1}` |
  | `resolve_without_outcome` | 422 | OUTCOME_REQUIRED | `_REP` | | raw `{"action": "resolve", "expected_version": 1}` |

- **recordContactActivity** (path `_SEEDED` unless stated):

  | name | status | code | preconditions | path | body |
  |---|---|---|---|---|---|
  | `call_logged` | 201 | — | `(*_REP, "case_state")` | | CALL |
  | `not_claimed` | 409 | NOT_ALLOWED_IN_STATE | `_REP` | | raw `{"kind": "call", "outcome": "reached", "expected_version": 1}` |
  | `stale_version` | 409 | VERSION_CONFLICT | `_REP` | | CALL (v4 ≠ 1) |
  | `no_session` | 401 | UNAUTHENTICATED | `()` | | CALL |
  | `supervisor_refused` | 403 | ROLE_NOT_ALLOWED | `_SUP` | | CALL |
  | `unknown_case` | 404 | CASE_NOT_FOUND | `_REP` | `_UNKNOWN` | CALL |
  | `malformed_reference` | 400 | VALIDATION_ERROR | `_REP` | `_MALFORMED` | CALL |
  | `missing_expected_version` | 400 | VALIDATION_ERROR | `_REP` | | raw `{"kind": "call", "outcome": "reached"}` |

- **createFlag** (no path):

  | name | status | code | preconditions | body |
  |---|---|---|---|---|
  | `flag_answer` | 201 | — | `(*_REP, "case_state")` | ANSWER |
  | `no_session` | 401 | UNAUTHENTICATED | `()` | ANSWER |
  | `owner_refused` | 403 | ROLE_NOT_ALLOWED | `_OWN` | ANSWER |
  | `unknown_case` | 404 | CASE_NOT_FOUND | `_REP` | raw `{"case_ref": "MHC-C-9999", "target": "answer"}` |
  | `malformed_case_ref` | 400 | VALIDATION_ERROR | `_REP` | raw `{"case_ref": "MHC-C-7", "target": "answer"}` |
  | `note_too_long` | 400 | VALIDATION_ERROR | `_REP` | raw `{"case_ref": "MHC-C-0007", "target": "answer", "note": _LONG}` |
  | `message_outside_case` | 400 | VALIDATION_ERROR | `(*_REP, "case_state")` | raw `{"case_ref": "MHC-C-0007", "target": "answer", "message_id": "m-999999"}` |

- **listFlags** (body `None`):

  | name | status | code | preconditions |
  |---|---|---|---|
  | `representative_lists` | 200 | — | `_REP` |
  | `owner_lists` | 200 | — | `_OWN` |
  | `no_session` | 401 | UNAUTHENTICATED | `()` |
  | `customer_refused` | 403 | ROLE_NOT_ALLOWED | `_CUST` |

- **reviewFlag** (path `_FLAG` unless stated):

  | name | status | code | preconditions | path | body |
  |---|---|---|---|---|---|
  | `review` | 200 | — | `(*_SUP, "case_state")` | | REVIEW |
  | `no_session` | 401 | UNAUTHENTICATED | `()` | | REVIEW |
  | `representative_refused` | 403 | ROLE_NOT_ALLOWED | `_REP` | | REVIEW |
  | `unknown_flag` | 404 | FLAG_NOT_FOUND | `_SUP` | `{"flag_id": "flg-999999"}` | REVIEW |
  | `bad_status` | 400 | VALIDATION_ERROR | `_SUP` | | raw `{"status": "new"}` |
  | `note_too_long` | 400 | VALIDATION_ERROR | `_SUP` | | raw `{"status": "reviewed", "note": _LONG}` |

- **getOversight** (body `None`):

  | name | status | code | preconditions |
  |---|---|---|---|
  | `supervisor_reads` | 200 | — | `_SUP` |
  | `no_session` | 401 | UNAUTHENTICATED | `()` |
  | `representative_refused` | 403 | ROLE_NOT_ALLOWED | `_REP` |
  | `owner_refused` | 403 | ROLE_NOT_ALLOWED | `_OWN` |

**Why none of these is red on today's `main`** (the AEA-59 runner, non-strict):

- Role refusals run, because `require_staff` is the first parameter.
- Drives that reach `CaseService`/`DemoService` skip with `not bound: get_case_service` / `get_demo_service`.
- createFlag `unknown_case` and reviewFlag `unknown_flag` reach the real `FlagService`, whose first demo-clock read
  raises `not bound: demo_clock`, so they skip.
- The 400 drives are answered by the route or the request model before any service call.
- `case_state` and `case_claimed_by_supervisor` drives are listed, not run.

After AEA-29 + AEA-30 merge, the raw-body drives follow AEA-29's check order: not found → role → missing field → version
→ state (`_case_actions.py::apply_in` lines 75–102, `record_activity_in` lines 226–252). On the seed they produce exactly
the statuses above.

**Local driver `tests/api/test_contract_cases_staff_cases.py`** (≈ 220 lines), test
`test_staff_cases_contract_cases_drive_and_cover(monkeypatch, tmp_path)`:

1. **Static.**
   - `from tests.contract.openapi_cases import check_cases_mapping`; `assert check_cases_mapping(CASES,
     "cases/staff_cases.py") == []`; `assert ROUTE_FILE == "staff_cases"`;
     `set(CASES) == {the 8 operationIds}`.
   - Every documented status of each operation (`load_contract().operations[op].responses`) appears in some drive.
   - applyCaseAction's three 409 codes and three 422 codes, and recordContactActivity's two 409 codes, each appear.
   - Print the case count per operation.
2. **Drive every case** through `staff_app` with doubles, one fresh `tmp_path / name` app per drive.
   - Preconditions:
     - `login` → `token = session_cookie_value(login(client, settings))`;
     - `role:<r>` → `h.store.set_role(token, DemoRole(r))`;
     - `case_state` / `case_claimed_by_supervisor` → no-op. The double's programmed answer below *is* that state.
   - Bodies: `{"example": N}` → `request_examples(op)[N]`; `{"raw": J}` → `J`.
   - Path: fill `{reference}` / `{flag_id}` from `drive["path"]`.
3. **Programmed answers.** A module dict `SERVICE_ANSWERS: dict[tuple[str, str], Callable[[StaffCasesHarness], None]]`
   sets the double before the request:
   - **2xx:**
     - getQueue → `queue_view()`; getCase → `case_detail()`; getOversight → `oversight_view()`;
     - applyCaseAction `claim`/`claim_seeded` → `summary("CLAIMED")`, `wait` → `summary("WAITING")`, `resolve` →
       `summary("RESOLVED")`, `release` → `summary("CLAIMED", lifecycle="unassigned", owner=None, version=5)`,
       `assign` → `summary("ASSIGNED")`, `change_priority` → `summary("PRIORITY_CHANGED")`;
     - recordContactActivity → `activity_result()`; createFlag → `flag_record()`;
       reviewFlag → `flag_record("reviewFlag", "REVIEWED", "200")`; listFlags → `flag_records()`.
   - **Service errors:**
     - getCase `unknown_case` → `detail_raises = CaseNotFoundStandIn("MHC-C-9999")`;
     - applyCaseAction `unknown_case` and recordContactActivity `unknown_case` →
       `CaseActionRejected(code=ApiErrorCode.CASE_NOT_FOUND, details={"reference": "MHC-C-9999"})`;
     - applyCaseAction: `stale_version` → `case_rejected("applyCaseAction", "409", "VERSION_CONFLICT")`,
       `claimed_by_supervisor` → `…CASE_ALREADY_CLAIMED`, `resolve_before_claim` → `…NOT_ALLOWED_IN_STATE`,
       `release_without_reason` → `case_rejected("applyCaseAction", "422", "REASON_REQUIRED")`,
       `wait_without_wake_up` → `…WAKE_UP_REQUIRED`, `resolve_without_outcome` → `…OUTCOME_REQUIRED`;
     - recordContactActivity: `not_claimed` → `case_rejected("recordContactActivity", "409", "NOT_ALLOWED_IN_STATE")`,
       `stale_version` → `…VERSION_CONFLICT`;
     - createFlag: `unknown_case` → `FlagRejected(code="CASE_NOT_FOUND", field=None, constraint=None,
       details={"reference": "MHC-C-9999"})`; `message_outside_case` → `FlagRejected(code="VALIDATION_ERROR",
       field="message_id", constraint="not a message of this case", details=None)`;
     - reviewFlag `unknown_flag` → `FlagRejected(code="FLAG_NOT_FOUND", field=None, constraint=None,
       details={"flag_id": "flg-999999"})`.
   - **Every other non-2xx drive is answered by the gate or the route:** assert `h.cases.calls == []` and
     `h.flags.calls == []` after it.
4. **Every response:** the status and (when given) `error.code` match the drive, and `assert_matches(response, op)`
   passes. Print `op/name: status`. At the end assert the number of drives run equals the total in `CASES`.

**Runner run (AC-19 evidence):** `uv run pytest tests/contract/test_openapi_server.py -k "Queue or Case or Contact or
Flag or Oversight" -rs`. Passing looks like: no failure; every skip reason starts with `not bound:`. Record the counts.
Strict mode is a wave-merge check after AEA-29 + AEA-30; do not run it as a gate here.

### Step 8: journey `tests/journeys/j6/test_aea_45.py` (AC-20) and its record — BUILT (`c6cdab6`, record `ea00827`); R6 refreshes the record

Rules (`tests/journeys/support/README.md`): use the `journey` fixture, `pytestmark = pytest.mark.journey`; no
`TestClient`, no `dependency_overrides`, no doubles, no monkeypatch of `meridian`; every `/api` call names its
operationId (the client validates every response against the OpenAPI).

Docstring: "J-6 extension (slice plan §0a): the representative claims the escalated case MHC-C-0007 on AEA-57's harness
(real app on a first-boot DB copy, scripted model; no model call is reached). Steps that need `case_service` (AEA-29)
or `demo_service` (AEA-30) are reported blocked until those merge. CAP-4 end to end is AEA-52's."

One test, `test_j6_representative_claims_escalated_case(journey: JourneyRun) -> None`, with `REF = "MHC-C-0007"`:

0. `signed = journey.login()`; `c = signed.client`.
   `with journey.step("J-6", "0 the customer role is refused the queue", operations=("getQueue",)):`
   `r = c.call("GET", "/api/staff/queue", operation_id="getQueue")`; assert 403 and `r.json()["error"]["details"] ==
   {"role": "customer", "needs": ["representative", "supervisor"], "reason": "wrong_role"}`.
1. `with journey.step("J-6", "1 act as the representative", needs=("login_sessions",), operations=("switchRole",)):`
   `PUT /api/session/role` body `{"role": "representative"}` with operation_id `switchRole` → 200. Stored:
   `journey.db.scalar("SELECT role FROM staff_sessions WHERE session_id = ?", (signed.session_id,)) == "representative"`.
2. `with journey.step("J-6", "2 the queue lists the escalated case", needs=("case_service", "demo_service"), operations=("getQueue",)):`
   - `stored = journey.db.one("SELECT lifecycle, owner_role, version, priority FROM cases WHERE case_ref = ?", (REF,))`.
   - GET queue → 200. Exactly one row in `needs_my_action` has `reference == REF`.
   - That row's `lifecycle == stored["lifecycle"] == "unassigned"`, `owner is None`, and
     `priority["level"] == stored["priority"]`.
3. `with journey.step("J-6", "3 the case opens with its brief and allowed actions", needs=("case_service", "demo_service"), operations=("getCase",)):`
   - GET `/api/staff/cases/MHC-C-0007` → 200.
   - `body["case"]["version"] == stored["version"]`; `"claim" in body["case"]["allowed_actions"]`;
     `len(body["brief"]["headings"]) == 8`.
   - **Unchanged check:** `demo_now = journey.container.get(DEMO_SERVICE).clock_view().now`, then
     `CaseDetailOut.model_validate(journey.container.get(CASE_SERVICE).detail(CaseRef(REF), StaffRole.REPRESENTATIVE,
     demo_now)).model_dump(mode="json") == body`. `DEMO_SERVICE` and `CASE_SERVICE` come from `meridian.web.deps`. This
     is the real service on the same DB copy, not a double, and the demo clock does not move by itself.
   - `v0 = body["case"]["version"]`.
4. `with journey.step("J-6", "4 the representative claims it", needs=("case_service", "demo_service"), operations=("applyCaseAction",)):`
   - `events_before = journey.db.count("case_events", "case_ref = ? AND actor_role = 'representative'", (REF,))`.
   - POST actions `{"action": "claim", "expected_version": v0}` → 200; `result_line == "Claimed · Riley (demo)"`;
     `case.owner == "Riley"`, `case.lifecycle == "claimed"`, `case.version == v0 + 1`.
   - Stored: the `cases` row has `lifecycle 'claimed'`, `owner_role 'representative'`, `version v0 + 1`; the
     representative `case_events` count is `events_before + 1`.
5. `with journey.step("J-6", "5 a stale version is refused and changes nothing", needs=("case_service", "demo_service"), operations=("applyCaseAction",)):`
   - POST the same body again (`expected_version: v0`) → 409, `error.code == "VERSION_CONFLICT"`,
     `details.current_version == v0 + 1`.
   - Stored: version still `v0 + 1`; the `case_events` count unchanged.
6. `with journey.step("J-6", "6 reopening shows it claimed", needs=("case_service", "demo_service"), operations=("getCase",)):`
   GET case → `owner == "Riley"`, `version == v0 + 1`, `"claim" not in allowed_actions`.

**Today:** steps 0–1 pass. Step 2 is recorded `blocked-on AEA-29, AEA-30` and the test is skipped. That is the harness's
`stop_blocked`; with `--journeys-strict` it fails instead.

**Record:** `docs/testing/journeys/<YYYY-MM-DD>-AEA-45.md`. Hand-written, the same table as `2026-10-21-AEA-27.md`:

| Field | Value |
|---|---|
| Claim | AEA-45 routes CON-11…13, 15…17 (AC-1…AC-22); J-6 step "claim the escalated case" |
| Level | `mock-tested` for the claim, refusals and pass-through (`tests/api/test_staff_cases_*.py`, service doubles). J-6 steps 0–1 ran `integrated with a scripted model` on AEA-57's harness (route registered, role gate, switchRole stored) |
| Tested revision | the code commit SHA |
| Environment | VPS worktree, Python 3.12, uv; in-process FastAPI for `tests/api`; the harness's uvicorn on an OS-assigned loopback port with a first-boot DB copy for the journey; no model call, no paid call |
| Command | the §7 commands |
| Result | counts from the runs, plus the skip reason quoted |
| Evidence location | this file; GitLab issue #45 comment (the orchestrator posts it at merge) |
| Remaining limitations | no real `CaseService`/`DemoService`; AC-21 skipped pending the OpenAPI amendment; AC-19 strict run waits on AEA-29 + AEA-30; no browser leg (AEA-62) |
| Blocked by | AEA-29 (`case_service`), AEA-30 (`demo_service`) for J-6 steps 2–6 at `integrated with a scripted model`; AEA-52 for CAP-4 end to end |

### Step 9: context rows (AC-22) — SUPERSEDED by R1 and R6

1. **`.claude/reference/area-map.md`, line 35 (A9 row), *Status* cell.**
   - Replace the leading `partly built:` with `built:`.
   - Replace the trailing `; the rest planned` with
     `; AEA-45 (<sha>): web/routes/staff_cases.py, web/schemas/staff_cases.py, register_staff_cases hunk`.
   - Change nothing else in the row.
2. **`docs/design/code-design.md`:** after line 192 add
   `` **Built:** `web/routes/staff_cases.py`, `web/schemas/staff_cases.py`, the `register_staff_cases` hunk (AEA-45, `<sha>`). ``
3. **`.claude/state/icm-progress.md`:** add one row after line 37, at most 400 characters:
   `| Routes verified against code and tests | provisional | 2026-10-21: area map A9 → web/routes/staff_cases.py, web/schemas/staff_cases.py (AEA-45, <sha>) checked against tests/api/test_staff_cases_*.py, test_contract_cases_staff_cases.py (<N> passed); record docs/testing/journeys/<date>-AEA-45.md | Each slice adds its route; verified when every area-map row is actual |`
4. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL.

### Step 10: gates, commits, report — SUPERSEDED by R5 and R7

Run §7's gates cheapest first; stop at the first red.

**Commit 1 (code + tests):**

```
git add src/meridian/web/routes/staff_cases.py src/meridian/web/schemas/staff_cases.py src/meridian/web/container.py tests/api/staff_cases_support.py tests/api/test_staff_cases_routes.py tests/api/test_staff_cases_access.py tests/api/test_staff_cases_refusals.py tests/api/test_staff_cases_capture.py tests/api/test_contract_cases_staff_cases.py tests/contract/cases/staff_cases.py tests/journeys/j6/test_aea_45.py
```

Message `AEA-45: staff case routes (CON-11…13, 15…17)`. The body lists the ACs met and marks AC-21, AC-19-strict and
AC-20's integrated steps as waiting. If R-1 was granted to this ticket, also `git add` its two files and say so. The last
line is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

**Commit 2 (record and context):**

```
git add docs/testing/journeys/<date>-AEA-45.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md
```

Message `AEA-45: journey record and context rows`, with the same last line.

Never `git add -A`; never push (the merge step does); never force-push.

**Report:** each gate's output line, both SHAs, the record path with its Level and Blocked-by, and the AC table marked
verified / waiting.

---

## 6. Data and fixtures

All synthetic or issued. Nothing from `.env`; no paid call; no port bound by the API tests (in-process `TestClient`); the
journey harness binds an OS-assigned loopback port (never 4019 / 5184).

| Data | Source | Notes |
|---|---|---|
| Every 2xx / 4xx body and request body | The signed OpenAPI's named examples, read at run time (`iter_response_examples`, `request_examples`, `load_document`) | Deep copies; never edited. Doubles validate them into the real `domain/views.py` / `FlagRecord` types (all 26 round-trip unchanged) |
| `FIXED_NOW` | 2026-10-19 07:00 America/Chicago (−05:00), the ticket's AC-12 instant | Demo-clock double |
| Distinctive free text | `rand_word()` (letters only, so never code-, card- or phone-like) | AC-14, AC-18 |
| MHC-10002's email and service address | Issued scheduling DB (`tests/fixtures/sqlite.ISSUED_DB`), opened `mode=ro` at run time | AC-13 only; never written into source, never printed; no phone column read |
| Seeded case MHC-C-0007 (journey, runner) | AEA-31's first-boot seed (`services/reset.py`: unassigned, version 1) on the harness's / runner's DB copy | Present on `main` (AEA-29 merged). The routes reach it only once AEA-30 binds the demo clock |
| Seam-test DB (R3) | `tests/fixtures/sqlite.temp_sqlite()`: a temporary copy of the issued DB, deleted on exit, seeded with `seed_demo(tx, assembler=BriefAssembler())` | Never writes the issued file; asserts no contact value; prints no body |
| Settings and secrets | `make_settings(tmp_path)`; the harness's own generated env | As AEA-23's tests |
| Case references | `MHC-C-0007` (seeded), `MHC-C-0099` / `MHC-C-9999` (unknown), `MHC-C-7` (malformed); flag ids `flg-1`, `flg-3`, `flg-99`, `flg-999999` | None is phone- or card-like |

---

## 7. Checks

Run inside the worktree with `export UV_LINK_MODE=hardlink`, cheapest first, and stop at the first red. The planner ran
none of these (one exception: a mypy probe on `main` that found R-10's pre-existing red).

| # | Check | Command | Passing looks like |
|---|---|---|---|
| A | Lint + format | `uv run ruff check src/meridian/web tests/api tests/contract tests/journeys/j6 && uv run ruff format --check src/meridian/web tests/api tests/contract tests/journeys/j6` | `All checks passed!`; `N files already formatted` |
| B | Type check | `uv run mypy src/meridian/web tests/api tests/contract tests/journeys/j6/test_aea_45.py` | `Success: no issues found`. Not the whole `tests/journeys/j6` folder: `test_aea_29.py` pulls in AEA-29's `tests/services/_case_fixtures.py`, which has 5 mypy errors on `main` (R-10) |
| C1 | New files, while iterating | `uv run pytest tests/api/test_staff_cases_seam.py tests/api/test_contract_cases_staff_cases.py -q -rs` (leave out the second file when R1 = `absent`) | all pass |
| C | Affected tests, once at the end | `uv run --with pytest-xdist pytest -n 2 tests/api tests/unit/web tests/unit/test_import_direction.py tests/contract/test_openapi_server.py tests/services/test_health_capture.py -q -rs` | 0 failed. Allowed skips: `test_case_detail_carries_last_event_id` (blocked-on UX session) and runner drives skipped as `not bound: …` / `route not registered: …`. `test_real_case_not_found_maps_to_404` passes |
| D | AC-19 runner subset | `uv run pytest tests/contract/test_openapi_server.py -k "Queue or Case or Contact or Flag or Oversight" -rs` | 0 failed. AEA30 = `no`: every skip reason starts with `not bound:`. AEA30 = `yes`: no skip for the eight operations |
| E | Journeys | `uv run pytest -m journey tests/journeys/j6/test_aea_45.py -rs`, then `uv run python -m tests.journeys.affected --base main -- -q -rs` | AEA30 = `no`: the J-6 file shows 1 skipped, reason `blocked-on AEA-30: …`; the affected journeys show 0 failed. AEA30 = `yes`: the J-6 file passes all seven steps |
| F | Collect | `uv run pytest --collect-only -q > /dev/null` | exit 0 |
| G-1 | No server clock (AC-12) | `grep -nE "datetime\.now\|time\.time\|date\.today" src/meridian/web/routes/staff_cases.py src/meridian/web/schemas/staff_cases.py` | prints nothing |
| G-2 | Never `open_case` (AC-16) | `grep -n "open_case" src/meridian/web/routes/staff_cases.py src/meridian/web/schemas/staff_cases.py` | prints nothing |
| G-3 | No logging in the routes | `grep -nE "logging\|logger\|emit_record\|print\(" src/meridian/web/routes/staff_cases.py src/meridian/web/schemas/staff_cases.py` | prints nothing |
| G-4 | No contact-like literals in tests | `grep -rnE "[0-9]{3}-[0-9]{3}-[0-9]{4}\|@example\.com\|[0-9]{13,19}" tests/api/*staff_cases* tests/contract/cases/staff_cases.py tests/journeys/j6/test_aea_45.py` (a missing file is fine) | prints nothing |
| G-5 | Owned files only | `git diff --name-only main...HEAD` | only §2's files (plus R-1's two when R1 = `granted`) |
| H | Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no new FAIL; the pre-existing `FAIL icm` budget line is reported, not fixed |

**Why these are the affected tests:**

- This ticket's diff against `main` reaches the same places as before: `register_staff_cases` adds eight routes to every
  app built by `create_app` + the real `build_container`. The test folders that build such an app are `tests/api`,
  `tests/contract/test_openapi_server.py` (the AEA-59 runner and its case-file checks, which load the new case file),
  `tests/unit/web` (container stubs, deps, and now AEA-29's `test_register_cases.py`),
  `tests/services/test_health_capture.py` and `tests/journeys` (via the affected command).
- `test_import_direction.py` checks `container.py`'s imports.
- The merge brings in `main`'s own changes. `main`'s merge gates already proved those, so they are not re-run here.

**Full suite: not required.** No shared fixture, settings, dependency, lockfile or cross-package module changes (rule
`build-loop-test-scope`).

**Existing tests that must stay green:**

- all of `tests/api/`, especially:
  - `test_gate.py::test_every_api_route_but_login_requires_session` (it now meets the real staff routes behind its
    probes);
  - `test_web_frontend.py::test_example_pair` (`/api/staff/cases/MHC-C-0007` as a customer now answers a JSON 403
    instead of a JSON 404; the test checks only JSON-ness);
  - `test_staff_session_*` (its `getQueue` probe is registered before the lifespan and still wins);
- `tests/unit/web/test_container.py`, `tests/unit/web/test_deps.py`, `tests/unit/web/test_register_cases.py`;
- `tests/contract/test_openapi_server.py`. Its `test_unauthenticated_matches_contract[<op>]` cases for the eight
  operations run and must answer 401. Its `test_validation_error_matches_contract[createFlag|reviewFlag]` cases run and
  must answer 400.

**Known reds on `main` that are not this ticket's:**

- `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero…` (ledger rows AEA-44/47/57). Do not include that
  file; report it if seen.
- mypy on `tests/services/_case_fixtures.py` (R-10). Check B avoids it; report it.

---

## 8. Risks and requests

- **R-1: request to the orchestrator (pre-dispatch): one local-driver word for the contract cases.** Still open at
  `c9b17ea`. This is the only reason the ledger shows AEA-45 `blocked`.
  - **Why it is needed.**
    - AEA-59's format check (`check_cases_mapping`) requires a 2xx drive for every named request example: CLAIM v3,
      WAIT v5, RESOLVE v8, RELEASE v4, ASSIGN v3, CHANGE_PRIORITY v3, CALL v4, ANSWER with `message_id` m-2, and REVIEW of
      an existing flag.
    - The runner cannot build those states on a fresh first-boot copy: the seed is at version 1, has no message it can
      name, and has no flags. Run as-is, those drives would turn red once AEA-30 merges. Two of them (`flag_answer`,
      `review`) reach the real `FlagService`.
    - A drive that carries a `LOCAL_DRIVER_ONLY` word is listed, not run (`RUNNABLE` in `test_openapi_server.py`
      excludes it), and the route's local driver proves it. None of the existing words describes these states honestly.
    - The README says a new word "is a follow-up on AEA-59, not an edit to your file".
  - **The exact change (two files, two lines):**
    - In `tests/contract/openapi_cases.py`, inside `LOCAL_DRIVER_ONLY`, directly after the `"case_events": …` line,
      add (102 characters; ruff's limit is 110):
      `        "case_state": "seeds the case or flag state a drive assumes; local driver only (mock-tested)",`
    - In `tests/contract/cases/README.md` §3, replace `` `case_claimed_by_supervisor`, `case_events`. `` with
      `` `case_claimed_by_supervisor`, `case_events`, `case_state`. ``
    - Check: `uv run pytest tests/contract/test_openapi_server.py -k "well_formed or format_example" -q` passes.
  - **Options.**
    - (a) **Recommended:** the orchestrator lands it on `main` before dispatching AEA-45. It is a one-file-pair change
      under 30 lines, so it can go straight to a `fanout-implementer` with this bullet as its whole plan. R0 then reads
      `landed`.
    - (b) Write "R-1 granted to AEA-45" in the dispatch message. R4 then commits it on its own, first.
    - With neither, R4 skips step 7 and the ticket comes back `blocked-on R-1` again.
- **R-2: AEA-29 check order (confirmed on `main`).** `_case_actions.py::apply_in` (lines 75–102) runs not found → role →
  missing field → version → state, and `record_activity_in` (lines 226–252) runs not found → role → version → state.
  Step 7's raw-body drives follow exactly that. If AEA-29 ever changes it, the AEA-59 runner flags the drive, and the
  fix is a one-line status/code edit in this case file, not a route change.
- **R-3: AEA-29 shapes (satisfied).** `CaseNotFound(LookupError)` sets `case_ref = str(case_ref)` and is raised by
  `detail()`; `apply` and `record_activity` return the documented unions. `test_real_case_not_found_maps_to_404` now
  runs.
- **R-4: wire times in America/Chicago (a plan decision).** UI_CONTRACTS *Conventions* line 20 says times are ISO 8601
  "with offset (America/Chicago, the demo clock)". The sibling route files `staff_live.py` and `events.py` already
  render `astimezone(America/Chicago)`. The instant is unchanged, so AC-18's "rewrite nothing" holds for every value;
  only its offset form changes. AC-23 now checks it on real stored times.
- **R-5: REASON_REQUIRED wording (for AEA-52).** The OpenAPI example's constraint is "required for release, assign and
  change_priority"; AEA-29, now merged, builds `f"required for {name}"`. The route copies whatever the service returns,
  so this ticket is unaffected. AEA-52 should align them when it integrates.
- **R-6: AC-21 follow-up when the UX amendment lands.**
  - `test_case_detail_carries_last_event_id` stops skipping the moment `CaseDetail` gains `events` in the OpenAPI.
  - It then fails until `CaseDetailOut` gets `events: CaseEventsOut` (`last_event_id: int`, as the amended schema says).
    That failure is intended: the output models ignore unknown keys, so without it the new field would be dropped
    silently.
  - **Ask:** pair the UX amendment with a one-file follow-up on `schemas/staff_cases.py`, plus AEA-02b's `CaseDetail`
    (`domain/views.py`). R1 step 7 stops the run if the amendment has already landed.
- **R-7: the test paths differ from the ticket's.** `test_staff_cases_routes.py` holds AC-1, 2, 6, 18, 21 and WP-2. The
  rest sit in sibling files with unchanged names (`_access`, `_refusals`, `_capture`, and now `_seam`), to respect the
  500-line test cap.
- **R-8: shared lines (expected textual conflicts; resolve as the union).**
  - The area-map A9 row block and DO-3's `**Built:**` lines: resolved in R1.
  - `container.py`: AEA-30's `register_demo` hunk is still in flight. It edits only its own function, so expect at most
    a textual neighbour conflict at that merge.
  - The ICM *Routes verified* rows.
- **R-9: dependency order inside the routes is load-bearing** (step 2, item 5). A reviewer who reorders the parameters
  would let an unbound provider turn a 403 into a 500, which would also turn the AEA-59 runner's role drives from pass
  into skip. `test_role_matrix`'s zero-call assertions and the runner's 403 drives guard it.
- **R-10: pre-existing mypy red on `main` (AEA-29's, for the orchestrator).** `uv run mypy tests/journeys/j6` reports 5
  `no-untyped-call` errors in `tests/services/_case_fixtures.py` (lines 540–569), reached through
  `tests/journeys/j6/test_aea_29.py`. Check B names this ticket's files so the red is not this ticket's. The seam test
  must not import `_case_fixtures`. A fix belongs to an AEA-29 follow-up.
- **R-11: AEA-30 may land before this run.** R0's AEA30 switch covers it. The journey and the runner drives then run for
  real, and any failure is a real seam to report. Fix it in owned files only when the route or schema is at fault.
- **R-12: stale comment (for AEA-29 / AEA-08).** `domain/handoff.py` line 73 says the route (AEA-45) serialises
  `sources` as `source_ids`. In fact `CaseService`'s `brief_view` does it (`_case_views.py` line 330), and the route
  must not add a mapping. Not this ticket's file.
- **R-13: duplicated area-map rows on `main` (for a `lane::direct` cleanup).** A6, A11, A7a, A8 and A12 each appear
  twice in `.claude/reference/area-map.md`. R1 keeps them as they are; only the A9 cell is this ticket's.
- **R-14: disk and CPU.** The tests copy nothing large. `full_app`, the runner and `temp_sqlite()` each make a small DB
  copy in a temp dir and delete it. Use `-n 2` at most.
- **No signed-contract change and no D-4…D-15 reversal.** Nothing edits the OpenAPI, `UI_CONTRACTS.md` or `docs/ux/**`.
  D-5 (Decision 2 option A) is followed by waiting for the UX session's amendment.

### What the implementer must not do

- Re-create the branch, rebase, or rewrite the built files from steps 1–6 and 8. Edit them only to fix a failure that
  R2 or R3 shows, and log it in *Deviations*.
- Define `CaseAction`, `ActivityIn`, `CaseActionRejected`, `FlagIn`, `FlagRejected`, `CaseNotFound` (except the
  test-only stand-in) or any service class. Import them.
- Decide anything a service owns: no lifecycle check, no ordering, no due state, no `allowed_actions` computation or
  filtering, no "claimed by you", no promise marking, and no label text other than `result_line`.
- Read the server clock, add a logger or log line, add a reset check, return 503, call `open_case`, or touch the
  database from a route.
- Strip, default or rewrite any output value; add `events` to `CaseDetailOut` before the OpenAPI has it.
- Use a precondition word outside AEA-59's vocabulary (plus `case_state` once R-1 is in), or a `by` / `with` drive key.
- Put a double, `TestClient`, `dependency_overrides` or monkeypatch in the journey file.
- Change `staff_app`'s signature; import `tests.services._case_fixtures`.
- Edit any file outside §2's list. That includes `web/deps.py`, `web/errors.py`, `web/middleware.py`, `services/*`,
  `domain/*`, `tests/api/openapi_check.py`, `tests/api/web_shell_support.py`, `tests/journeys/support/`,
  `tests/services/*`, other hunks and the OpenAPI. R-1's two files are allowed only when R1 = `granted`.
- Put a phone number, card-like number, verification code, secret or the MHC-10002 contact values in source, test
  names, fixtures or output; print a response body or the contact values.
- Run the full suite, bind ports 4019 / 5184, `git add -A`, push, force-push, or commit the plan file.

---

## 9. Readiness

**READY (resume run).** No product decision is needed, and no signed contract changes.

| Prerequisite | Why | Status on `main` `c9b17ea` |
|---|---|---|
| AEA-23 web shell | `require_staff`, providers, renderer, `openapi_check` | merged |
| AEA-02b case view types | `CaseAction`, `ActivityIn`, `CaseActionRejected` (imported) | merged `5305d57` |
| AEA-44 flags | `FlagIn`, `FlagRejected` (imported) | merged `ec86bf8` |
| AEA-29 `CaseService` | not imported by the routes; enables the R3 seam test and `test_real_case_not_found_maps_to_404` | merged `ef561fc` |
| **R-1 `case_state` word** (AEA-59 follow-up) | AC-19's case file must pass AEA-59's format check without planting reds | **open: land on `main` (recommended) or grant to this ticket before dispatch** |

**Not blockers** (injection and doubles, or evidence only):

- AEA-30 `DemoService` (`clock_view().now` only; the J-6 steps and the runner's real drives wait on it);
- AEA-52 (CAP-4 end to end);
- the UX session's OpenAPI amendment (AC-21).

**Gates:** none (no human, paid or live gate).

## Deviations

Appended by the implementer, 2026-10-21 (branch `aea-45-staff-cases-api`, code commit `c6cdab6`).

- **AC-19 not built (R-1 not granted, `case_state` absent on `main`).** Step 0.4's grep found no `case_state` in
  `tests/contract/openapi_cases.py` and the dispatch did not grant the two R-1 edits. Per step 0.4, step 7
  (`tests/contract/cases/staff_cases.py` and `tests/api/test_contract_cases_staff_cases.py`) was not written. Nothing
  else depends on it; the runner subset (check D) passes without the file in non-strict mode. Needs the R-1
  follow-up on AEA-59, then a re-dispatch for step 7 only.
- **J-6 file is blocked from step 0, not from step 2.** The plan expected steps 0-1 to pass today. The real login
  reads `demo_clock` (AEA-30), so `journey.login()` answers 500 on `main`. Steps 0 and 1 now declare
  `needs=("login_sessions", "demo_clock")`, login happens inside step 0, and the whole file skips with
  `blocked-on AEA-30: demo_clock not bound`. The body of steps 2-6 has therefore never executed.
- **Context rows.** The area-map A9 row, the DO-3 `**Built:**` line (placed after the last existing line, 194) and
  the ICM row (after the AEA-47 row, 37) were edited in commit 2. `check_context.py` reports `FAIL icm 14537 B (budget
  8192 B)`; the file was already over budget from other tickets' rows, and is not this ticket's to trim.
- Test files hold a few more parametrised cases than the plan lists (per-example parametrisation); names match.
