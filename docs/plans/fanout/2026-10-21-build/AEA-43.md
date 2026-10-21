# Plan — [AEA-43] customer API: inbox, staffing, clock read, reset (CON-6…CON-9)

**Status:** re-planned, revision 4 (READY) · `lane::build-loop` · `risk::security` · wave 2
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/43 (spec copy:
`docs/plans/tickets/AEA-43.md`) · **Base revision checked:** `main` at `2ec19ad`; branch at `a8c8b5d`
**Planner:** claude-opus-5-5, 2026-10-21. Revision 1 first plan; revision 2 added Step 6a (frozen clock-test fix);
revision 3 re-checked against `main` at `b559c75`; **revision 4 (this one)** re-checked against `main` at `2ec19ad` and
the branch at `a8c8b5d`, kept everything that held, and moves the resume point to Step 9.

### What revision 4 changes, and why (read this first)

| # | Change | Why (what was found) |
|---|---|---|
| R4-1 | **Steps 1–8 are done.** The implementer resumes at **Step 9a** (a new short re-check), then Step 9 | The branch now holds commit A `db9ef50` (`feat(web): demo routes CON-6..CON-9 (AEA-43)`, Step 7, includes the Step 5b rule) and `a8c8b5d` (`Merge branch 'main'`, Step 8, merged `b559c75`). Working tree clean. Frozen files still hash to the manifest |
| R4-2 | **sha A = `db9ef50`** is written into Steps 14 and 15 (no placeholder left) | Commit A exists |
| R4-3 | No second merge of `main` is needed | `main` moved `b559c75` → `2ec19ad` by one docs-only commit (`docs/plans/fanout/2026-10-21-build/AEA-29.md`); `git log HEAD..main -- src tests pyproject.toml uv.lock` is empty. Step 9a says what to do if that changes before the implementer starts |
| R4-4 | Every name the remaining steps use was re-read on the branch and holds | `web_shell_support` (`full_app`, `make_client`, `reset_gate_of`, `records_of`, `captured_log`, `app_log_text`, `effective_routes`), `demo_support` exports, AEA-59 vocabulary (`reset_gate_held`, `rate_limited` in `LOCAL_DRIVER_ONLY`; no `reset_fails`), harness (`JourneyRun.login`, `.step(journey, name, *, needs, operations)`, `db.one`, `db.count`), need keys (`login_sessions`, `identity_service`, `demo_service`, `reset_service`, `handoff_service`, `session_service`, `turn_service`, `run_graph`), tables `reset_events`, `demo_state`, `demo_inbox`, limits `resets_per_ip = 10`, `reset_window_s = 600`, doc lines (area map A8 line 36, ICM A4 row line 45, DO-3 line 314) |
| R4-5 | §7.3 names the runner test that carries the non-success drives: `test_route_cases_match_contract` | `tests/contract/test_openapi_server.py` line 119 |
| R4-6 | R-12 (merge after AEA-30 and AEA-29) still stands | Neither is on `main` at `2ec19ad` (build ledger: AEA-29, AEA-30 not merged) |

### What revision 3 changes, and why (read this first)

| # | Change | Why (what was found on `main`) |
|---|---|---|
| R3-1 | The implementer **merges `main` into the ticket branch** (new Step 8) before writing the journey, contract and doc work | The branch was cut from `7603145`. Since then `main` gained AEA-57's journey harness (`tests/journeys/support/`), AEA-59's contract runner (`tests/contract/test_openapi_server.py`, `openapi_cases.py`, `openapi_driver.py`, `cases/README.md`), AEA-27's real `IdentityService`, AEA-31's `ResetService`, AEA-44's login store, AEA-02b's `domain/views.py`. None of them is on the branch. Precedent: `0c74722`, `af79286`, `2d16cd8` (main merged into a ticket branch) |
| R3-2 | `to_wire_message`: a message with `code=None` shows dots and `INBOX_CODE_GONE`; its status becomes `expired` **only when the service said `active`**; `used` and `expired` are kept | AEA-27 (merged) returns a consumed code as `status="used", code=None` (`services/identity.py` `inbox`, test `test_inbox_scoped_to_login_session`). The old rule ("every `code=None` → `expired`") would make `used` unreachable and break AC-16's J-3 "active, then used". The frozen AC-14 test (an `active` message with no code → `expired`) still passes. Decision recorded in §3.2 and §8 R-10 |
| R3-3 | `tests/contract/cases/demo.py` uses AEA-59's **closed vocabulary**: `reset_gate_held`, `rate_limited`; the `RESET_FAILED` drive moves to a separate `LOCAL_ONLY_DRIVES` constant | AEA-59's format check (`tests/contract/openapi_cases.py`) fails any unknown word by name; the old words `reads_exhausted`, `resets_exhausted`, `reset_fails` are unknown. Adding a word is "a follow-up on AEA-59, not an edit to your file" (`tests/contract/cases/README.md` §3) → request in §8 R-11 |
| R3-4 | The two journey files are written **on AEA-57's harness** (`journey` fixture, `journey.step(..., needs=..., operations=...)`), with no TestClient or doubles; the old mock-level flow bodies move to `tests/api/test_demo_flows.py` | `tests/journeys/support/README.md` *Rules for journey files*: "no `dependency_overrides`, no monkeypatch of `meridian`, no `TestClient`, no doubles above the model ports" |
| R3-5 | **Merge order:** AEA-43 merges into `main` **after AEA-30 and AEA-29** | On the real app, `resetDemo` runs the real `ResetService`, which calls AEA-30's `services/demo.format_clock` (`ModuleNotFoundError` today → `test_success_matches_contract[resetDemo/confirmed]` **fails**, not skips) and AEA-29's `services/handoff` seed (missing → `ResetFailed` → 500). See §8 R-12 |
| R3-6 | Doc row locations updated: area map row A8 is now line 36; the ICM row goes after line 45; DO-3 line is 314 | `main` moved |

**Where the build stands (worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-43`, branch
`aea-43-aea-43-demo-routes`, HEAD `a8c8b5d`, working tree clean):** frozen commits `54b74b4` (tests) and `7d29c51`
(Step 6a amendment). Frozen manifest (sha256, from `7d29c51`, re-checked at `a8c8b5d`):
`574d907f5ec70c1ebc71076c4cf2b9d6cb99735900b2c2d5fc99dfb0161443e0  tests/api/demo_support.py`,
`9fa80a07cf015c9e550ae827a65ac66c2303173089767a8b494b6684b54811d9  tests/api/test_demo_routes.py`. **Committed:**
commit A `db9ef50` (`src/meridian/web/schemas/demo.py`, `src/meridian/web/routes/demo.py` with the Step 5b
`to_wire_message` rule, the `register_demo_routes` hunk in `src/meridian/web/container.py`), then `a8c8b5d` (merge of
`main` at `b559c75`). **Next:** the implementer starts at **Step 9a**, then Step 9.

**Builder:** `fanout-implementer` (Sonnet). The test-writer's work is done. Nobody needs to re-read the design: every
name below is copied from the code on `main` (`b559c75`), the worktree, or the signed contracts.

---

## 1. Goal and sources

### Goal (quoted from the issue, *What to build*)

> The demo-control routes in `web/routes/demo.py` with their wire models in `web/schemas/demo.py`, proven against the
> OpenAPI with services replaced by doubles through `web/deps.py` overrides. Every operation accepts every signed-in role
> (x-roles: all four; R-48) and takes the session from AEA-23's middleware, never from a query, header or body value.

Five operations, one route file, one schema file, one container hunk:

| operationId | Method, path | Calls (injected; a double in every `tests/api` test) | Answers |
|---|---|---|---|
| `listDemoInbox` (CON-6) | `GET /api/demo/inbox` | `DemoService.clock_view().now`, then `IdentityService.inbox(str(session.session_id), now=…)` | 200 `InboxResponse`; 401/429/503 come from AEA-23's middleware |
| `getStaffing` (CON-7) | `GET /api/demo/staffing` | `DemoService.staffing()` | 200 `Staffing`; 401/429 from the middleware |
| `setStaffing` (CON-7) | `PUT /api/demo/staffing` | `DemoService.set_staffing(mode, request_id=ctx.request_id, role=session.role)` | 200 `StaffingResponse`; 400 from the validation handler; 401/503 from the middleware |
| `getDemoClock` (CON-8 read) | `GET /api/demo/clock` (**GET only**; POST is AEA-47's) | `DemoService.clock_view()` | 200 `DemoClock`; 401/429 from the middleware |
| `resetDemo` (CON-9) | `POST /api/demo/reset` | per-IP throttle on `RESET_IP`, then `ResetService.reset(wall_now, request_id=…, session_id=…, role=…)` | 200 `ResetResponse`; 400; 401; 409 (`ResetAlreadyRunning` or throttle); 500 `RESET_FAILED` |

**What a reviewer sees (WP-2, the ticket's worked pair).** MHC-10002 has been located and the chat shows "the phone
ending in 02". The reviewer opens the inbox tab: `GET /api/demo/inbox` with that login's `mhc_session` → 200, one message,
`to_masked` "···02", `body` "Your Meridian Home Comfort verification code is <digits>. It expires in 10 minutes.", `code`
the six digits, `status` "active", `expires_at` ten minutes after `at`. A second reviewer, logged in separately, gets
`{"messages": []}`. After the code is entered, the same message reads `status` "used" with code "······" and the
"no longer shown" text. Later the reviewer posts `{"confirm": true}` to `/api/demo/reset` → 200 with `ok: true`,
`open_chats_ended`, `roles_reset`, and `clock` back at `DEMO_START` (Fri 2026-10-16 10:00 Chicago, `label`
"Fri Oct 16, 2026 · 10:00 am", `date_label` "Fri Oct 16, 2026 (demo date)").

### Context

AEA-23 (merged) built the gate, providers and reset gate; its `register_demo_routes` stub in `web/container.py` waits for
this ticket. Behind the routes: AEA-27 `IdentityService` (merged), AEA-31 `ResetService` (merged), AEA-30 `DemoService`
(wave 2, not merged; worktree `aea-30-aea-30-demo-clock-sched`). The route imports none of them: it types them with
local `Protocol`s and every `tests/api` test uses doubles. CON-6 is the only response in the contract set that carries a
verification code, hence `risk::security`.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-43.md` (= GitLab #43): AC-1…AC-20, *Agent handoff*, *Observability*, *Blocked by* | Everything below; frozen-first AC-2, AC-3, AC-6, AC-8 |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-43 (line 178: B, **Sec**, blocked by 23; calls 27, 30, 31), §0a J-3/J-8, §3 collision map | Owned files; one `register_<area>()` hunk |
| Web contract (wins over DO-4) | `docs/design/contracts/stage7/web.md` §1, §4 ("routes pass `str(session.session_id)`"), §5 (`record_reset` "called by routes/demo.py"), §7, §10, §13 | Call shapes in §4 |
| Cases contract | `stage7/cases.md` §1.1 (`DEMO_START`), §6 (`DemoService`, `format_clock`), §7 (`ResetService.reset`, `ResetDone`, `ResetFailed`) | Route copies service values, formats nothing (WEB-25) |
| Graph-tools contract | `stage7/graph-tools.md` §5 (`InboxMessage`, "unwraps `code` only while serialising", "`INBOX_CODE_GONE` and code `"······"` when `code` is None", GRT-2: a restart reads `expired` with `code=None`), C-5, C-10 | Body rendering, `SecretStr` handling |
| Data contract | `stage7/data.md` §2 → `src/meridian/policy/texts.py` `TextId.INBOX_CODE_BODY`, `TextId.INBOX_CODE_GONE` | `render(...)` |
| DO-4 | `docs/design/contracts/internal-components.md` §14 `IdentityService.inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]` | Inbox signature (DO-4's `ResetService.reset(now)` is superseded by cases.md §7) |
| Decisions | `docs/plans/7b-decisions/web.md` WEB-3, WEB-13, WEB-25, WEB-26 (MC-19, MC-20), WEB-27, WEB-33, WEB-36 | Throttle numbers; who formats; reset arguments |
| UX-join amendments | `docs/plans/ux-join/backend-amendments.md` AEA-43-1 (AC-14), AEA-43-2 (AC-15), AEA-27-1 (restart → `expired`, `code=None`), §3 journey pattern A | Code-gone handling; case file |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `/api/demo/inbox` (examples `ONE_ACTIVE`, `EMPTY`, `USED_AND_EXPIRED`), `/api/demo/staffing` (`OFF`, `ON`; `TURNED_ON`, `TURNED_OFF_WITH_WAITING`; request `ON`, `OFF`), `/api/demo/clock` GET, `/api/demo/reset` (request `CONFIRM`; `RESET`; 409 `RESET_IN_PROGRESS` with `retry_after_ms: 5000`; 500 `RESET_FAILED` with `details: null`) | Wire shapes and statuses |
| AEA-59 runner (merged) | `tests/contract/cases/README.md`, `tests/contract/openapi_cases.py` (`PRECONDITIONS`, `SETUPS`, `LOCAL_DRIVER_ONLY`, `check_cases_mapping`, `ROUTE_FILE_BY_CON` maps CON-6…CON-9 → `demo`; only `("CON-8","post")` → `staff_clock`), `tests/contract/openapi_driver.py` (`real_app`, `run_drive`, `send`: a 500 whose exception is not `RuntimeError("not bound: …")` is a **failure**) | Case-file vocabulary (§5 Step 11) |
| AEA-57 harness (merged) | `tests/journeys/support/README.md`, `steps.py` (`NEED_OWNERS`, `OPERATION_OWNERS`: the five demo operations are owned by AEA-43), `run.py` (`JourneyRun.login`, `.step`, `.db`), `client.py` (`JourneyClient.call` validates every response) | Journey files (§5 Step 12) |
| Sibling journey files | `tests/journeys/j3/test_aea_27.py` (step declared with needs; body `pytest.skip` until AEA-51), `tests/journeys/j8/test_aea_31.py`, `j8/test_aea_44.py`, `j6/test_aea_47.py` | Precedent for blocked steps |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` | n/a (ticket *Evaluation*) |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-3, WF-5, WF-15; *Content and redaction* "Verification codes … Never raw" | One `request` record per call; identifiers reach the services; code never logged or traced |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-22, M-27 (indirect) | Nothing computed here |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`; workspace `code-design-solid-modularity`, `code-structure` | Frozen tests; affected tests and journeys; journey record; doc rows in the same change |
| Code read on `main` `b559c75` | `src/meridian/web/{app,container,deps,errors,middleware}.py`, `services/{identity,reset,reset_gate}.py`, `domain/{identity,staff,views}.py`, `policy/texts.py`, `adapters/sqlite/schema/{40_identity,60_cases}.sql`, `adapters/sqlite/repos_cases_state.py`; `tests/api/{web_shell_support,openapi_check,test_app,test_contract_cases_reads}.py`, `tests/contract/*`, `tests/journeys/support/*`, `tests/journeys/affected.py` | §4 copies the signatures |
| Branch (read at `a8c8b5d`) | `tests/api/demo_support.py`, `tests/api/test_demo_routes.py` (frozen), the three production files in commit A `db9ef50` | Unchanged |

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Change | State today |
|---|---|---|
| `src/meridian/web/routes/demo.py` | create | **done**, commit A `db9ef50` (Step 5b rule included); no change planned |
| `src/meridian/web/schemas/demo.py` | create | **done**, `db9ef50`; no change planned |
| `src/meridian/web/container.py` | modify **only** the body and docstring of `register_demo_routes` | **done**, `db9ef50`; no change planned |
| `tests/api/demo_support.py` | — | **frozen** (`7d29c51`); never edit |
| `tests/api/test_demo_routes.py` | — | **frozen** (`7d29c51`); never edit |
| `tests/api/test_demo_capture.py` | create (AC-13, AC-17, AC-18, AC-19) | not started |
| `tests/api/test_demo_register.py` | create (plan-added hunk test) | not started |
| `tests/api/test_demo_flows.py` | create (AC-16 at `mock-tested`; R3-2 decision test) | not started |
| `tests/api/test_contract_cases_demo.py` | create (AC-15 local driver) | not started |
| `tests/contract/cases/demo.py` | create (AC-15) | not started |
| `tests/journeys/j3/test_aea_43.py` | create (AC-16, J-3, on the harness) | not started |
| `tests/journeys/j8/test_aea_43.py` | create (AC-16, J-8, on the harness) | not started |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-43.md` | create (AC-16 record; the date is the day of the final commit) | not started |
| `.claude/reference/area-map.md` | modify the *Status* cell of row A8 only (line 36 on `main`) | — |
| `.claude/state/icm-progress.md` | add **one new** *Routes verified against code and tests* row directly after line 45 | — |
| `docs/design/code-design.md` | modify line 314 only (`routes/demo.py · schemas/demo.py …`) | — |

### Shared surfaces: read only, never edit

`src/meridian/web/{app,middleware,deps,errors,logging,frontend}.py`, every other route and schema file,
`services/*` (incl. `reset_gate.py`, `identity.py`, `reset.py`), `domain/*`, `ports/*`, `policy/*`, `config.py`,
`adapters/*`; `tests/api/{web_shell_support,openapi_check}.py` and every existing test file; `tests/fakes/*`,
`tests/conftest.py`, `tests/fixtures/*`; `tests/contract/{openapi_cases,openapi_driver,openapi_variants,test_openapi_server}.py`
and `tests/contract/cases/README.md` (AEA-59); `tests/journeys/support/**`, `tests/journeys/{affected.py,README.md}`
(AEA-57); `pyproject.toml`, `uv.lock`.

### Owned by other tickets — do not touch

`web/routes/staff_clock.py` + `schemas/staff_clock.py` (AEA-47, the `POST /api/demo/clock`); every other
`register_<area>()` hunk (in particular `register_identity` AEA-27, `register_demo` AEA-30, `register_reset` AEA-31,
`register_cases` AEA-29); `services/demo.py`, `services/scheduler.py` (AEA-30), `services/handoff.py`,
`services/cases.py` (AEA-29); every other `tests/contract/cases/*.py`; `tests/capture/` (AEA-50, 51, 52); every other
`tests/journeys/j<N>/test_aea_<NN>.py`; `apps/web/**`, `docs/ux/**` (the OpenAPI and `UI_CONTRACTS.md` included), the
briefing, issued data, `docs/archive/`, `docs/parked/`; this plan file.

### Must not do

- Do not import `meridian.services.identity`, `meridian.services.demo`, `meridian.services.reset` or
  `meridian.domain.views` in `routes/demo.py` or `schemas/demo.py`: the route types its collaborators with local
  `Protocol`s (§4.3) and reads results by attribute (`from_attributes=True`).
- Do not register `POST /api/demo/clock`, add a route under any other path, or add a public path.
- Do not read the wall clock anywhere except `reset_demo` (one reading); never call `strftime`, `datetime.now` or
  `format_clock` in `routes/demo.py` or `schemas/demo.py` (AC-5 greps for the first two).
- Do not log, print, trace or put into an exception message any inbox `code` or `body`, any request body, or any rejected
  value. The routes emit **no** log record of their own (the middleware's `request` record is the only one).
- Do not add a reset-gate check or read rate-limiting to the routes (the middleware does both).
- No six-digit literal, card-like number or full phone number in any test, fixture, case file or record: codes come from
  `new_digits()` (§6).
- No `.env` reads, no paid model call, no port bind other than the harness's own OS-assigned loopback port (never 4019
  or 5184).
- In journey files: no `TestClient`, no `dependency_overrides`, no monkeypatch of `meridian`, no doubles.
- Never edit the two frozen files. If a frozen test is wrong, stop and report (the plan goes back to the planner).
- `git add <explicit paths>` only, never `git add -A`; no push; no force push; no rebase of the branch.

---

## 3. Requirements table

### 3.1 Acceptance criteria → implementation → test

**F** = frozen test (already written, in `tests/api/test_demo_routes.py`). Every `tests/api` test drives the real
AEA-23 app (`create_app` + gate middleware) in process with `TestClient`, services replaced through
`app.dependency_overrides` (`tests/api/demo_support.demo_app`).

| AC | Criterion (abridged; full text in the ticket) | How it is implemented | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `listDemoInbox` 200 bodies validate for `ONE_ACTIVE`, `USED_AND_EXPIRED`, `EMPTY`; active `body` = `INBOX_CODE_BODY` with its digits; `code is None` → `INBOX_CODE_GONE` and code `"······"` | `list_demo_inbox` + `to_wire_message` | F `tests/api/test_demo_routes.py::test_inbox_matches_openapi` |
| AC-2 [invariant] **F-first** | Inbox scoped to the login session; `?demo_session=` and an extra header change nothing | session only from `get_login_session` | F `::test_inbox_scoped_to_login_session` |
| AC-3 [negative] **F-first** | Digits only in the response body: absent from every log record, trace span, `repr` | `InboxMessageOut` keeps `body`/`code` as `SecretStr`, revealed only by `model_dump(mode="json")` | F `::test_inbox_code_never_logged` |
| AC-4 [invariant] | `getStaffing` both modes; `setStaffing` call args and `converted_cases` passthrough | `get_staffing`, `set_staffing` | F `::test_staffing_matches_openapi` |
| AC-5 [invariant] | `getDemoClock` = `clock_view()` whatever the wall clock; GET only | `get_demo_clock`; `build_router` | F `::test_clock_is_demo_clock_and_get_only` + grep (§7) |
| AC-6 [invariant] **F-first** | `resetDemo` calls `reset(<wall now>, request_id, session_id, role)`; 200 from `ResetDone` | `reset_demo` | F `::test_reset_matches_openapi` |
| AC-7 [failure/refusal] WF-15 | `confirm` false/missing (and `1`) → 400 field `confirm`; `ResetAlreadyRunning` → 409 + `retry_after_ms`; `ResetFailed` → 500 | `ResetRequest`; `reset_demo` | F `::test_reset_refusals` |
| AC-8 [failure/refusal] **F-first** | 11th reset from one IP in 600 s → 409, no service call; other IP unaffected | `limiter.peek(RESET_IP)` then `record_reset` | F `::test_reset_throttle_per_ip` |
| AC-9 [failure/refusal] | Gate held: inbox and setStaffing → 503; staffing and clock reads wait and answer | middleware; routes reachable | F `::test_reset_gate_answers` |
| AC-10 [failure/refusal] WF-5 | `{"mode": "maybe"}` → 400 field `mode`; "maybe" nowhere | `StaffingMode` Literal, `hide_input_in_errors=True` | F `::test_staffing_validation_error` |
| AC-11 [failure/refusal] WF-3 | read buckets exhausted → inbox 429 | middleware | F `::test_inbox_request_rate_limited` |
| AC-12 [invariant] | 401 without cookie for reset, staffing ×2, clock; 2xx for each role | no role dependency | F `::test_login_gate_and_any_role` |
| AC-13 [capture] | Through the real container: one `request` record per call; identifiers reach the services | hunk + middleware | `tests/api/test_demo_capture.py::test_demo_entry_points_emit_records` |
| AC-14 [invariant] | `code=None` from the service as `active` → `expired`, dots, `INBOX_CODE_GONE`; held code keeps `active` | `to_wire_message` (Step 5b rule) | F `::test_inbox_code_gone_is_expired`; plus `tests/api/test_demo_flows.py::test_inbox_code_gone_keeps_used_and_expired` (R3-2) |
| AC-15 [contract] | `tests/contract/cases/demo.py` holds the five operations' cases | case file (Step 11) | `tests/api/test_contract_cases_demo.py::test_demo_cases_drive_documented_statuses` (local driver, every drive incl. local-only) and `uv run pytest tests/contract/test_openapi_server.py -k "listDemoInbox or Staffing or getDemoClock or resetDemo" -rs` (AEA-59 runner, real app); strict form at the wave merge |
| AC-16 [journey] | J-3 inbox `active` then `used`; J-8 reset valid and reads back at defaults | harness journey files (Step 12) + mock-level flows (Step 10) + record | `uv run pytest -m journey tests/journeys/j3/test_aea_43.py tests/journeys/j8/test_aea_43.py -rs` (steps skip `blocked-on …` today) and `tests/api/test_demo_flows.py` (pass, `mock-tested`); record says level `mock-tested`, *Blocked by* AEA-29, AEA-30, AEA-40, AEA-51, AEA-52 |
| AC-17 [failure/refusal] WF-3 | inbox: 401 (no call), 200 per role, record status = response status (200, 401, 429, 503), forced 500 with `error_kind`; no digits in records | middleware + route | `tests/api/test_demo_capture.py::test_wf3_inbox_login_gate_and_request_status` |
| AC-18 [failure/refusal] WF-5 | staffing/clock 429, setStaffing never limited; statuses recorded; forced 500 with `error_kind` | middleware + route | `tests/api/test_demo_capture.py::test_wf5_read_limits_and_request_status` |
| AC-19 [capture] WF-15 | reset record statuses 200, 400, 409 busy, 409 throttled, 500; `error_kind` on 500 only | `ApiProblem` handler | `tests/api/test_demo_capture.py::test_wf15_reset_request_status` |
| AC-20 [regression/context] | area map A8, ICM row, DO-3 line updated; only this ticket's rows | Step 14 | `git diff --name-only` |
| plan-added | `register_demo_routes` includes the router once; nothing on a bare app; GET only on the clock path | hunk | `tests/api/test_demo_register.py::test_register_demo_routes_includes_router_once` |

**Worked pair (WP-2):** AC-1 `ONE_ACTIVE` + `EMPTY` and AC-6 `RESET` (frozen file), repeated end to end at mock level by
`tests/api/test_demo_flows.py::test_wp2_inbox_active_then_used_and_second_reviewer_empty`.
**Journey criterion:** AC-16, level today `mock-tested` (all harness steps blocked; see §8 R-6).

### 3.2 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Step |
|---|---|---|---|---|
| Four roles; no `require_staff` | OpenAPI `x-roles`; R-48 | AC-12, AC-17 | in-ticket | 4 |
| Session only from the gate | web.md §4; graph-tools §5 | AC-2 | in-ticket | 3 |
| `inbox(str(session.session_id), now=<demo clock>)` | ticket; DO-4 §14 | AC-2 | in-ticket; `now` asserted in AC-1's test | 3 |
| Unwrap `code` only while serialising; `body` from texts | graph-tools §5, C-10; data.md §2 | AC-1, AC-3 | in-ticket | 2–3 |
| **No code → dots and `INBOX_CODE_GONE`; status `expired` only when the service said `active`; `used`/`expired` kept** | AEA-43-1 ("never sends dots as an active code"); graph-tools §5 (status is the service's); AEA-27 merged (`used` ⇒ `code=None`); OpenAPI enum and `USED_AND_EXPIRED`; AC-16 ("active, then used") | AC-14 (its sentence reads "with `status: "expired"`"; its test and title concern `active`) | **decided here (engineering, R3-2):** the literal sentence would make `used` unreachable on the wire and contradict AC-16; the rule keeps AC-14's guarantee (dots are never `active`) and its frozen test | 5b |
| Newest-first order kept | graph-tools §5; OpenAPI "Newest first" | no | added (AC-1's test asserts `msg-2`, `msg-1`) | 3 |
| Copy `clock_view()` / `staffing()` / `set_staffing()` unchanged | cases.md §6; WEB-25 | AC-4, AC-5 | in-ticket | 4 |
| `reset(now, *, request_id, session_id, role)`; `now = get_wall_clock()()` | cases.md §7; MC-19, MC-20; WEB-26 | AC-6 | in-ticket | 4 |
| `ResetAlreadyRunning` → 409; `ResetFailed` → 500; `ResetDone` → 200 | web.md §7; cases.md §7 | AC-7 | in-ticket (`getattr(result, "code", None) == "RESET_FAILED"`, no import of AEA-31) | 4 |
| `RESET_IP` throttle; `record_reset` called by `routes/demo.py` | web.md §5; WEB-27 | AC-8 | in-ticket | 4 |
| What counts as one reset run | web.md §5 (silent) | no | decided (rev 1): every call that reaches `ResetService.reset` counts, recorded just before the call; a 400 does not | 4 |
| 409 `retry_after_ms` when another reset runs | OpenAPI 409 example (5000) | AC-7 | `RESET_RETRY_AFTER_MS` (5000, `web/middleware.py`) | 4 |
| `confirm` must be JSON `true` | OpenAPI `const: true` | AC-7 | `StrictBool` + true-only validator (`1`, `"true"` → 400) | 2 |
| 400 never echoes the value | DO-4 §0; web.md §1 | AC-10 | `hide_input_in_errors=True` | 2 |
| Request bodies allow extra properties | OpenAPI (no `additionalProperties: false`) | no | `extra="ignore"` on the two request models | 2 |
| 503 during reset; reads wait | web.md §7; WEB-13; `RESET_503_OPERATIONS`, `RESET_NO_WAIT_OPERATIONS` in `middleware.py` | AC-9 | middleware (AEA-23) | — |
| 429 on reads; `setStaffing` never limited | web.md §5; WEB-3; `RATE_LIMITED_READ_OPERATIONS` | AC-11, AC-18 | middleware (AEA-23) | — |
| 401 for every op without a session | web.md §6 | AC-12, AC-17 | middleware + router-level `Depends(get_login_session)` | 4 |
| One `request` record per call; `error_kind` only on 5xx | web.md §10; DO-6 | AC-13, AC-17–19 | middleware | — |
| Router from this ticket's own hunk; `web/app.py` untouched | slice plan §3 | no | plan test `test_register_demo_routes_includes_router_once` | 5 |
| Case file in AEA-59's vocabulary; a 500 the real app cannot produce on demand | AEA-59 `cases/README.md` §3, §6 | AC-15 ("500 on `resetDemo`") | `RESET_FAILED` drive kept in `tests/contract/cases/demo.py` as `LOCAL_ONLY_DRIVES` (proved by the local driver) until AEA-59 adds a `reset_fails` local-driver word (§8 R-11) | 11 |
| `demo_event` (CAP-5), code-sent event (CAP-1), `reset_event` (CAP-9) rows | DO-6 | AC-13 note | other-ticket: AEA-52, AEA-51, AEA-50 (services AEA-30, 27, 31 write them); J-8 harness step reads `reset_events` | 12 |
| `x-timing` p95 | OpenAPI | no | n/a (E-8 load run) | — |
| uvicorn access log off | AEA-23 record | no | other-ticket: AEA-50 | — |

### 3.3 Entry-point registration

| Entry point | Workflow | Registered in DO-6 | Inherits |
|---|---|---|---|
| `GET /api/demo/inbox` | WF-3 | yes | `request` record; CAP-1 (AEA-51); evaluation n/a |
| `GET`/`PUT /api/demo/staffing`, `GET /api/demo/clock` | WF-5 | yes | `request`, `demo_event` (AEA-30); CAP-5 (AEA-52); evaluation n/a |
| `POST /api/demo/reset` | WF-15 | yes | `reset_event` (AEA-31); CAP-9 (AEA-50); evaluation n/a |

---

## 4. Shared code to use (copied from `main` at `b559c75` and the worktree)

### 4.1 Imports the route file uses (unchanged; all exist on the branch and on `main`)

```python
from meridian.domain.common import ApiErrorCode, RequestId
from meridian.domain.identity import InboxMessage
from meridian.domain.staff import DemoRole, LoginSession, LoginSessionId
from meridian.policy.texts import TextId, render
from meridian.services.reset_gate import ResetAlreadyRunning
from meridian.web.deps import (get_demo_service, get_identity_service, get_login_session, get_rate_limiter,
                               get_request_context, get_reset_service, get_wall_clock)
from meridian.web.errors import ApiProblem
from meridian.web.middleware import RESET_RETRY_AFTER_MS, LimitScope, RateLimiter, RequestContext
from meridian.web.schemas.demo import (DemoClock, InboxMessageOut, InboxResponse, ResetRequest, ResetResponse,
                                       Staffing, StaffingMode, StaffingRequest, StaffingResponse)
```

### 4.2 Signatures copied verbatim

```python
# domain/identity.py
class InboxMessage(MeridianModel):
    id: str; at: dt.datetime; to_masked: str; code: SecretStr | None
    status: Literal["active", "used", "expired"]; expires_at: dt.datetime
# domain/staff.py
class DemoRole(StrEnum): CUSTOMER = "customer"; REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
LoginSessionId = NewType("LoginSessionId", str)
class LoginSession(MeridianModel): session_id: LoginSessionId; role: DemoRole; role_reset: bool; signed_in_at; expires_at
# policy/texts.py
TextId.INBOX_CODE_BODY  # "Your Meridian Home Comfort verification code is {digits}. It expires in 10 minutes."
TextId.INBOX_CODE_GONE  # "This code is no longer shown. Ask the chat for a new code if you need one."
def render(text_id: TextId, /, **values: str) -> str: ...
# web/middleware.py
RESET_RETRY_AFTER_MS = 5000
class LimitScope(StrEnum): THREAD; SESSION; IP; LOGIN_IP; RESET_IP = "reset_ip"
class RateLimiter:
    def peek(self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read") -> LimitVerdict
    def record_reset(self, ip: str, now: float) -> None
@dataclass(frozen=True)
class RequestContext: request_id: RequestId; client_ip: str; session: LoginSession | None; run_tag; run_id; turn_verdict
RATE_LIMITED_READ_OPERATIONS ⊇ {"listDemoInbox", "getStaffing", "getDemoClock"}
RESET_503_OPERATIONS ⊇ {"listDemoInbox", "setStaffing"};  RESET_NO_WAIT_OPERATIONS ⊇ {"resetDemo"}
# web/errors.py
class ApiProblem(Exception):
    def __init__(self, status: int, code: ApiErrorCode, *, field=None, constraint=None, details=None, headers=None)
# web/deps.py — providers; unbound ones raise RuntimeError(f"not bound: {provider.__name__}")
get_identity_service, get_demo_service, get_reset_service, get_rate_limiter, get_wall_clock,
get_request_context, get_login_session (401 if no session)
IDENTITY_SERVICE = Key("identity_service"); DEMO_SERVICE = Key("demo_service"); RESET_SERVICE = Key("reset_service")
HANDOFF_SERVICE = Key("handoff_service"); LOGIN_SESSIONS = Key("login_sessions"); RESET_GATE = Key("reset_gate")
```

### 4.3 The services behind the routes (the route declares local Protocols; it imports none of these)

```python
# AEA-27, merged (services/identity.py line 308)
def inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]:
    # newest first; status "used" if the code was used (code=None), "expired" if expired / not held by this
    # process / past expiry (code=None), else "active" with the held SecretStr
# AEA-30, not merged (worktree services/demo.py: returns domain/views.py models)
def staffing(self) -> StaffingView             # {mode, label, banner}
def set_staffing(self, mode: Presence, *, request_id: RequestId, role: DemoRole) -> StaffingChange  # {mode, label, converted_cases}
def clock_view(self) -> ClockView              # {now, label, date_label}
def format_clock(dt: datetime) -> tuple[str, str]   # module function; ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)") at DEMO_START
# AEA-31, merged (services/reset.py)
def reset(self, now: datetime, *, request_id: RequestId, session_id: LoginSessionId | None,
          role: DemoRole | None) -> ResetDone | ResetFailed
#   ResetDone(ok=True, open_chats_ended, roles_reset, clock: ResetClock(now, label, date_label)); ResetFailed(code="RESET_FAILED")
#   raises ResetAlreadyRunning from gate.hold(); calls format_clock(DEMO_START) before its try-block
```

Local Protocols in `routes/demo.py` (already written): `_ClockLike` (`now` property), `InboxReader.inbox`,
`DemoControls.staffing / set_staffing / clock_view`, `DemoReset.reset`, exactly as in the worktree file.

### 4.4 Test helpers (read only)

`tests/api/web_shell_support.py`: `make_settings(tmp_path, **changes)`, `make_client(app, *, peer="198.51.100.7")`
(context manager), `FakeSessionStore` (`.issue(role, *, now)`, `.session_of(token)`, `.set_role(token, role)`),
`FakeHeartbeat`, `MutableClock(start)` (`.advance(s)`), `cookie_header(token)`, `login(client, settings)`,
`session_cookie_value(response)`, `error_body(response, status, code)`, `assert_matches(response, operation_id)`,
`captured_log()`, `records_of(stream, "request")`, `app_log_text(caplog)`, `reset_gate_of(app)`, `effective_routes(app)`,
`full_app(monkeypatch, settings, *, store, heartbeat, overrides=None)`.
`tests/api/demo_support.py` (frozen): see §6. `tests/contract/openapi_variants.request_examples(op) -> dict[str, value]`;
`tests/contract/openapi_cases.check_cases_mapping(cases, where) -> list[str]`, `expected_route_file(op) -> str`;
`tests/api/openapi_check.load_contract().operations[op]` (`.method`, `.path_template`, `.responses`).
Harness (`tests/journeys/support/`): fixture `journey: JourneyRun`; `journey.login() -> LoginResult(client, response,
session_id, cookie)`; `journey.step(journey_id, name, needs=(...), operations=(...))` (context manager; skips with
`blocked-on AEA-NN` when a need is unbound or an operation unrouted); `JourneyClient.call(method, path, *,
operation_id, body=None, headers=None) -> httpx.Response` (validates against the OpenAPI);
`journey.db.one(sql, params) -> dict`, `.count(table, where="", params=())`. Import `JourneyRun` from
`tests.journeys.support.run`. `tests.fakes.clock.WORKED_PAIRS_NOW` = `DEMO_START` (2026-10-16 10:00 America/Chicago).

---

## 5. Steps (build order; each step is checkable on its own)

The slice sits in area A8 (DO-3 §3): `web/routes/demo.py` depends on `web/deps.py` providers and on local
abstractions only; nothing in `services/` or `domain/` depends on it. No new seam.

Every shell command runs in `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-43` after
`export UV_LINK_MODE=hardlink`.

### Steps 0–5, 6a — done (keep as is)

Frozen tests (`54b74b4`, amended `7d29c51`); `schemas/demo.py`, `routes/demo.py`, the `register_demo_routes` hunk
(committed in `db9ef50`). Their contents are the committed files; do not rewrite them. For reference the hunk is:

```python
    """AEA-43 customer API: CON-6 to CON-9 demo routes (web.md §4, §5, §7).

    Includes routes/demo.py's router (...) once per app. ... An app that create_app did not build has no web shell,
    so this does nothing.
    """
    from meridian.web.middleware import WebShellState
    from meridian.web.routes.demo import build_router

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    if getattr(app.state, "demo_routes_included", False):
        return  # a second lifespan on the same app must not add the routes again (FastAPI includes lazily)
    app.include_router(build_router())
    app.state.demo_routes_included = True
```

### Step 1 — check the base (done in an earlier session; kept for the record)

### Step 5b — done (in commit A `db9ef50`; kept for the record) — `to_wire_message` status rule (edit `src/meridian/web/routes/demo.py`)

Replace the first branch of `to_wire_message` so the function reads (docstring included):

```python
def to_wire_message(message: InboxMessage) -> InboxMessageOut:
    """Wire form of one inbox message. Without digits it shows dots and INBOX_CODE_GONE, and a message the service
    called `active` is sent as `expired` (AEA-43-1: dots are never an active code); `used` and `expired` keep their
    status (AEA-27 returns a used code with code=None)."""
    if message.code is None:
        return InboxMessageOut(
            id=message.id,
            at=message.at,
            to_masked=message.to_masked,
            body=SecretStr(render(TextId.INBOX_CODE_GONE)),
            code=SecretStr(CODE_GONE),
            status="expired" if message.status == "active" else message.status,
            expires_at=message.expires_at,
        )
    ...  # the held-code branch is unchanged
```

Invariants: (1) a message without digits is never sent `active` (AC-14); (2) the digits branch is untouched, so AC-1
and AC-3 keep passing; (3) `status` is still one of the three Literal values. Check: `uv run ruff check
src/meridian/web/routes/demo.py`.

### Step 6 — frozen tests and the hunk's neighbours green — done (re-proved by Step 9a item 4)

```bash
uv run pytest -q tests/api/test_demo_routes.py                       # 13 passed
uv run pytest -q tests/unit/web/test_container.py tests/unit/test_import_direction.py tests/api/test_gate.py
```
If a frozen test fails, fix production code only. If it cannot pass without breaking §2, stop and report.

### Step 7 — commit A (production code) — **done: `db9ef50`**

```bash
git add src/meridian/web/routes/demo.py src/meridian/web/schemas/demo.py src/meridian/web/container.py
git commit
```
Message: `feat(web): demo routes CON-6..CON-9 (AEA-43)`; body: one line per file (routes: five operations, GET only on
the clock path, inbox code unwrapped only while serialising; schemas: `SecretStr` wire model, strict `confirm`;
container: `register_demo_routes` includes the router once); last line
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Record its short SHA as **sha A** (= `db9ef50`).

### Step 8 — merge `main` into the branch (R3-1) — **done: `a8c8b5d`** (merged `main` at `b559c75`)

```bash
git merge --no-edit main
```
- Expected: a clean merge (`main` touched other hunks of `container.py`, not `register_demo_routes`, which is still the
  AEA-23 stub on `main` at line 691). If `container.py` conflicts, keep **every** hunk from `main` and this branch's
  `register_demo_routes` body and docstring; nothing else. Any conflict in another file: stop and report.
- `pyproject.toml` and `uv.lock` did not change between `7603145` and `b559c75`: no `uv sync` needed. If `git diff
  --stat HEAD~1 -- pyproject.toml uv.lock` shows a change, run `uv sync` (hardlink mode, no venv copy).
- Then re-prove: `sha256sum` of the two frozen files unchanged; `uv run pytest -q tests/api/test_demo_routes.py
  tests/unit/web/test_container.py tests/unit/test_import_direction.py tests/api/test_gate.py tests/api/test_app.py`
  all green. (`tests/api/test_app.py` adds probe routes for `/api/demo/inbox` before the lifespan includes the demo
  router, so its probes still answer first; if it fails because the real inbox route answered instead, stop and report:
  that file is AEA-23's.)

### Step 9a — re-check the base (start here)

Run in the worktree, after `export UV_LINK_MODE=hardlink`:

1. `git log --oneline -3` shows `a8c8b5d`, `db9ef50`, `b559c75`; `git status --short` prints nothing.
2. `sha256sum tests/api/demo_support.py tests/api/test_demo_routes.py` equals the manifest above, and
   `git diff 7d29c51 -- tests/api/test_demo_routes.py tests/api/demo_support.py` prints nothing.
3. `git log --oneline HEAD..main -- src tests pyproject.toml uv.lock` prints nothing (true at `main` `2ec19ad`).
   If it prints commits, run Step 8's procedure again (`git merge --no-edit main`, the same conflict rule, the same
   re-proof); if one of those commits is AEA-29's or AEA-30's merge, the §7.3 runner's expected failure may turn into a
   pass (R-12), which is fine.
4. `uv run pytest -q tests/api/test_demo_routes.py` → 13 passed.

Any other state: stop and report.

### Step 9 — `tests/api/test_demo_capture.py` (≤ 300 lines) and `tests/api/test_demo_register.py` (≤ 100 lines)

Write exactly as §7.2 describes.

### Step 10 — `tests/api/test_demo_flows.py` (≤ 250 lines)

Write exactly as §7.2 describes (mock-level J-3/J-8 flows and the R3-2 decision test).

### Step 11 — `tests/contract/cases/demo.py` + `tests/api/test_contract_cases_demo.py`

`tests/contract/cases/demo.py` (module docstring: owner AEA-43, AC-15, AEA-43-2; read by AEA-59's runner
`tests/contract/test_openapi_server.py` and by `tests/api/test_contract_cases_demo.py`; the vocabulary it uses:
precondition `login`; setups `reset_gate_held` (hold the app's ResetGate for the request: the middleware answers 503
for `listDemoInbox`/`setStaffing`, a real ResetService raises ResetAlreadyRunning for `resetDemo`) and `rate_limited`
(local-driver only in AEA-59: the limiter refuses the request; reads → 429, `resetDemo` → 409 throttle); and that
`LOCAL_ONLY_DRIVES` holds the `RESET_FAILED` drive, whose setup word `reset_fails` AEA-59 does not know yet — when AEA-59
adds it to `LOCAL_DRIVER_ONLY`, the drive moves into `CASES`):

```python
from __future__ import annotations

from typing import Final

ROUTE_FILE: Final = "demo"
CASES: Final[dict[str, dict[str, object]]] = {
    "listDemoInbox": {
        "public": False,
        "drives": (
            {"name": "messages", "status": 200, "preconditions": ("login",), "body": None},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (), "body": None},
            {"name": "rate_limited", "status": 429, "code": "REQUEST_RATE_LIMITED", "preconditions": ("login",),
             "setup": "rate_limited", "body": None},
            {"name": "reset_running", "status": 503, "code": "RESET_IN_PROGRESS", "preconditions": ("login",),
             "setup": "reset_gate_held", "body": None},
        ),
    },
    "getStaffing": {
        "public": False,
        "drives": (
            {"name": "current", "status": 200, "preconditions": ("login",), "body": None},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (), "body": None},
            {"name": "rate_limited", "status": 429, "code": "REQUEST_RATE_LIMITED", "preconditions": ("login",),
             "setup": "rate_limited", "body": None},
        ),
    },
    "setStaffing": {
        "public": False,
        "drives": (
            {"name": "on", "status": 200, "preconditions": ("login",), "body": {"example": "ON"}},
            {"name": "off", "status": 200, "preconditions": ("login",), "body": {"example": "OFF"}},
            {"name": "bad_mode", "status": 400, "code": "VALIDATION_ERROR", "preconditions": ("login",),
             "body": {"raw": {"mode": "maybe"}}},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (),
             "body": {"example": "ON"}},
            {"name": "reset_running", "status": 503, "code": "RESET_IN_PROGRESS", "preconditions": ("login",),
             "setup": "reset_gate_held", "body": {"example": "ON"}},
        ),
    },
    "getDemoClock": {
        "public": False,
        "drives": (
            {"name": "demo_clock", "status": 200, "preconditions": ("login",), "body": None},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (), "body": None},
            {"name": "rate_limited", "status": 429, "code": "REQUEST_RATE_LIMITED", "preconditions": ("login",),
             "setup": "rate_limited", "body": None},
        ),
    },
    "resetDemo": {
        "public": False,
        "drives": (
            {"name": "confirmed", "status": 200, "preconditions": ("login",), "body": {"example": "CONFIRM"}},
            {"name": "not_confirmed", "status": 400, "code": "VALIDATION_ERROR", "preconditions": ("login",),
             "body": {"raw": {"confirm": False}}},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (),
             "body": {"example": "CONFIRM"}},
            {"name": "already_running", "status": 409, "code": "RESET_IN_PROGRESS", "preconditions": ("login",),
             "setup": "reset_gate_held", "body": {"example": "CONFIRM"}},
            {"name": "throttled", "status": 409, "code": "RESET_IN_PROGRESS", "preconditions": ("login",),
             "setup": "rate_limited", "body": {"example": "CONFIRM"}},
        ),
    },
}
LOCAL_ONLY_DRIVES: Final[dict[str, tuple[dict[str, object], ...]]] = {
    "resetDemo": (
        {"name": "failed", "status": 500, "code": "RESET_FAILED", "preconditions": ("login",),
         "setup": "reset_fails", "body": {"example": "CONFIRM"}},
    ),
}
```
(Run `ruff format`; it will expand the dicts one key per line like `cases/staff_clock.py`.)

`tests/api/test_contract_cases_demo.py::test_demo_cases_drive_documented_statuses(monkeypatch, tmp_path)` — the local
driver (pattern of `tests/api/test_contract_cases_reads.py`), docstring `invariant (AC-15): each case yields its status
and code on AEA-23's app with doubles; every documented error status is covered; the file passes AEA-59's format check.`

1. `assert ROUTE_FILE == "demo"`; `assert set(CASES) == {"listDemoInbox", "getStaffing", "setStaffing",
   "getDemoClock", "resetDemo"}`; `assert check_cases_mapping(CASES, "cases/demo.py") == []`;
   `assert all(expected_route_file(op) == "demo" for op in CASES)`.
2. For each `op` and each drive in `(*CASES[op]["drives"], *LOCAL_ONLY_DRIVES.get(op, ()))`:
   - `spec = load_contract().operations[op]`; `settings = make_settings(tmp_path / op / case["name"])`;
   - `limiter = RateLimiter(WebLimits(reads_per_session_per_min=1, reads_per_ip_per_min=100))` when
     `case.get("setup") == "rate_limited" and op != "resetDemo"`, else `None`; `h = demo_app(monkeypatch, settings,
     limiter=limiter)`;
   - inside `with make_client(h.app) as client:` — preconditions: `"login"` → `token =
     session_cookie_value(login(client, settings))`, `assert token`, `headers = cookie_header(token)`; any other word →
     `raise AssertionError(f"unknown precondition {word!r}")`; no preconditions → `headers = {}`;
   - body: `None` → no JSON; `{"example": name}` → `request_examples(op)[name]`; `{"raw": value}` → `value`;
   - `send = lambda: client.request(spec.method.upper(), spec.path_template, headers=headers, json=payload)` (pass
     `json=` only when the body is not `None`);
   - setup: `None` → `response = send()`; `"reset_gate_held"` → if `op == "resetDemo"`:
     `h.resets.outcomes.append(ResetAlreadyRunning())`; then `with reset_gate_of(h.app).hold(): response = send()`;
     `"rate_limited"` → if `op == "resetDemo"`: send `Limits().web.resets_per_ip` times first, each `== 200`; else send
     once first, `== 200`; then `response = send()`; `"reset_fails"` → `h.resets.outcomes.append(ResetFailedStub())`,
     `response = send()`; anything else → `AssertionError`.
   - `assert response.status_code == case["status"], (op, case["name"])`; when `"code" in case`:
     `assert response.json()["error"]["code"] == case["code"]`; `assert_matches(response, op)`;
     `covered[op].add(str(case["status"]))`; `print(f"{op}/{case['name']}: {response.status_code}")`.
3. After the loop, for each op: every status key `>= "400"` in `spec.responses` is in `covered[op]`
   (compare as `int(k) >= 400`).
Imports: `ResetAlreadyRunning` (`meridian.services.reset_gate`), `Limits`, `WebLimits` (`meridian.policy.limits`),
`RateLimiter` (`meridian.web.middleware`), `demo_app`, `ResetFailedStub` (`tests.api.demo_support`), the helpers of §4.4.
Expected: 22 drive lines printed (21 in `CASES`, 1 local-only).

Then run the AEA-59 runner on the real app (non-strict) and record its output (expected result in §7.3).

### Step 12 — journeys on AEA-57's harness (AC-16): `tests/journeys/j3/test_aea_43.py`, `tests/journeys/j8/test_aea_43.py`

Both files: `pytestmark = pytest.mark.journey`; `from tests.journeys.support.run import JourneyRun`; no TestClient, no
doubles, no monkeypatch. Every `/api` call names its `operation_id` (the harness validates each response).

**`tests/journeys/j3/test_aea_43.py`** — docstring: "J-3 inbox legs (AEA-43, AC-16; pattern A). API level on AEA-57's
harness: real app, container and DB copy, scripted model. Step 0 needs AEA-30's DemoService (the inbox reads the demo
clock). Step 1 (a code sent through the chat shows `active`, is entered, then shows `used` with dots; a second login sees
none) also needs AEA-40 and AEA-51; its body is written with AEA-51's scripted outputs (AEA-27 plan R-1). The same flow
at mock level: tests/api/test_demo_flows.py."

```python
J3 = "J-3"

def test_j3_inbox_empty_for_new_login(journey: JourneyRun) -> None:
    with journey.step(J3, "inbox 0 a new login's inbox is empty",
                      needs=("login_sessions", "identity_service", "demo_service"),
                      operations=("login", "listDemoInbox")):
        signed = journey.login()
        r = signed.client.call("GET", "/api/demo/inbox", operation_id="listDemoInbox")
        assert r.status_code == 200
        assert r.json() == {"messages": []}
        assert journey.db.count("demo_inbox", "demo_session = ?", (signed.session_id,)) == 0

def test_j3_inbox_code_active_then_used(journey: JourneyRun) -> None:
    with journey.step(J3, "inbox 1 code active then used; a second login sees none",
                      needs=("login_sessions", "session_service", "turn_service", "run_graph",
                             "identity_service", "demo_service"),
                      operations=("login", "startChatSession", "submitTurn", "listDemoInbox")):
        pytest.skip("J-3 inbox body not written yet: needs AEA-51's scripted graph outputs (AEA-27 plan R-1)")
```

**`tests/journeys/j8/test_aea_43.py`** — docstring: "J-8 reset leg (AEA-43, AC-16; proposed J-8 extension). API level
on AEA-57's harness. Needs AEA-30 (DemoService and format_clock, which the real ResetService calls) and AEA-29 (the
demo seed the reset reloads); until both land the step is skipped `blocked-on`."

```python
DEMO_START = WORKED_PAIRS_NOW                         # from tests.fakes.clock
START_LABEL = "Fri Oct 16, 2026 · 10:00 am"
START_DATE_LABEL = "Fri Oct 16, 2026 (demo date)"

def test_j8_reset_returns_staffing_and_clock_to_start(journey: JourneyRun) -> None:
    with journey.step("J-8", "reset 1 resetDemo answers the start clock; reads back at defaults; who asked stored",
                      needs=("login_sessions", "reset_service", "demo_service", "handoff_service"),
                      operations=("login", "setStaffing", "resetDemo", "getStaffing", "getDemoClock")):
        signed = journey.login()
        c = signed.client
        on = c.call("PUT", "/api/demo/staffing", operation_id="setStaffing", body={"mode": "simulated_on_shift"})
        assert on.status_code == 200 and on.json()["mode"] == "simulated_on_shift"
        r = c.call("POST", "/api/demo/reset", operation_id="resetDemo", body={"confirm": True})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert datetime.fromisoformat(body["clock"]["now"]) == DEMO_START
        assert (body["clock"]["label"], body["clock"]["date_label"]) == (START_LABEL, START_DATE_LABEL)
        row = journey.db.one(
            "SELECT asked_by_role, asked_by_session, open_chats_ended, roles_reset FROM reset_events "
            "WHERE request_id = ?", (r.headers["X-Request-ID"],))
        assert row["asked_by_session"] == signed.session_id
        assert row["asked_by_role"] == "customer"
        assert (row["open_chats_ended"], row["roles_reset"]) == (body["open_chats_ended"], body["roles_reset"])
        state = journey.db.one("SELECT demo_now, staffing FROM demo_state WHERE id = 1")
        assert state["staffing"] == "nobody_online"
        assert datetime.fromisoformat(state["demo_now"]) == DEMO_START
        staffing = c.call("GET", "/api/demo/staffing", operation_id="getStaffing").json()
        assert staffing["mode"] == "nobody_online" and staffing["banner"] is None
        clock = c.call("GET", "/api/demo/clock", operation_id="getDemoClock").json()
        assert (clock["label"], clock["date_label"]) == (START_LABEL, START_DATE_LABEL)
        assert datetime.fromisoformat(clock["now"]) == DEMO_START
```
(The login starts as `customer` — AEA-44's store; the reset sends roles back to customer, the login stays — OpenAPI
`resetDemo` description. Do not print the cookie.)

### Step 13 — fast gates, affected tests, affected journeys (§7.3); fix until green (except §7.3's one allowed red)

### Step 14 — context rows (AC-20) and the journey record

1. `.claude/reference/area-map.md` line 36 (row A8), *Status* cell: insert immediately before `; the rest planned`
   the text `; AEA-43 (db9ef50): web/routes/demo.py, web/schemas/demo.py and the register_demo_routes hunk built`.
   Change nothing else.
2. `.claude/state/icm-progress.md`: insert one row directly after the row that starts `| Routes verified against
   code and tests | provisional | 2026-10-21: area map A4 → services/identity.py` (line 45 at `a8c8b5d`), ≤ 400 characters:
   `| Routes verified against code and tests | provisional | 2026-10-21: A8 → web/routes/demo.py, web/schemas/demo.py
   (AEA-43, db9ef50) vs tests/api/test_demo_*.py, test_contract_cases_demo.py (<N> passed); J-3/J-8 harness steps
   blocked-on AEA-29, 30, 40, 51; record docs/testing/journeys/<date>-AEA-43.md | Each slice adds its route; verified
   when every area-map row is actual |` (one line; use the real date and counts). Do not edit the *Last reconciled* line.
3. `docs/design/code-design.md` line 314 (`routes/demo.py · schemas/demo.py …`): append `   built AEA-43 db9ef50`
   after `A8    2` (same layout as line 313, `built AEA-42 55b5e7c`).
4. `docs/testing/journeys/<YYYY-MM-DD>-AEA-43.md` in the format of `docs/testing/journeys/2026-10-21-AEA-27.md`
   (heading `# Journey record — AEA-43 (web/routes/demo.py, web/schemas/demo.py, register_demo_routes)`, then the
   nine-field table): **Claim** CON-6…CON-9 routes (AC-1…AC-20), J-3 inbox legs and J-8 reset leg; **Level**
   `mock-tested` (the `tests/api` doubles and `test_demo_flows.py`; every harness step is blocked today);
   **Tested revision** the final commit SHA (or "uncommitted"); **Environment** VPS worktree, Python, in-process
   AEA-23 app with doubles, the harness's own loopback server and DB copy for the journey files, no model or paid call;
   **Command** the exact commands of §7.3; **Result** the pass/skip counts, the journey skip reasons quoted, the AEA-59
   runner counts and the one expected failure (§7.3) quoted; **Evidence location** GitLab issue #43 comment; this
   file; **Remaining limitations** J-3 step 1 body waits for AEA-51; `RESET_FAILED` drive is local-driver only (R-11);
   the runner's `resetDemo/confirmed` needs AEA-29 and AEA-30 on `main`; **Blocked by** AEA-30 (`demo_service`,
   `format_clock`), AEA-29 (`handoff_service`, demo seed), AEA-40 (`startChatSession`, `submitTurn`), AEA-51
   (`run_graph`; J-3 body), AEA-52 (WEB-33 wiring), AEA-59 (`reset_fails` word; strict run at the wave merge). Below the
   table, the two steps to run once unblocked. No digits, cookie, password or personal data in the file.
5. `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL in the files you own.

### Step 15 — commit B

`git add` exactly: `tests/api/test_demo_capture.py tests/api/test_demo_register.py tests/api/test_demo_flows.py
tests/api/test_contract_cases_demo.py tests/contract/cases/demo.py tests/journeys/j3/test_aea_43.py
tests/journeys/j8/test_aea_43.py docs/testing/journeys/<date>-AEA-43.md .claude/reference/area-map.md
.claude/state/icm-progress.md docs/design/code-design.md`. Message `test+docs(AEA-43): capture, flows, contract cases,
journeys, record and context rows`; body names sha A (`db9ef50`) and the §7.3 results; last line
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No push.

---

## 6. Data and fixtures (all synthetic; the frozen `tests/api/demo_support.py`, unchanged)

Sources: OpenAPI examples (labels, banner, `to_masked` "···02", ten-minute expiry), cases.md §1.1 `DEMO_START`,
`tests.fakes.clock.WORKED_PAIRS_NOW`. Codes are generated at run time; no file holds a six-digit literal. IP addresses
come from the documentation ranges (`198.51.100.0/24`, `203.0.113.0/24`).

Names exported by `tests/api/demo_support.py` (frozen; use as is):
`DEMO_START`, `START_LABEL` ("Fri Oct 16, 2026 · 10:00 am"), `START_DATE_LABEL`, `WALL_START` (2026-10-21 15:00 UTC),
`CODE_GONE` (`"·" * 6`), `OFF_LABEL`, `ON_LABEL`, `ON_BANNER`; `new_digits() -> str`; frozen dataclasses
`ClockViewStub(now, label, date_label)`, `START_CLOCK`, `StaffingViewStub(mode, label, banner)`, `OFF`, `ON`,
`StaffingChangeStub(mode, label, converted_cases)`, `ResetDoneStub(open_chats_ended, roles_reset, clock, ok=True)`,
`ResetFailedStub(code="RESET_FAILED")`; `inbox_message(*, digits, status="active", msg_id="msg-1", at=DEMO_START,
to_masked="···02") -> InboxMessage`; doubles `FakeIdentityService(by_session=None, *, raises=None)` (`.by_session`,
`.raises`, `.calls: list[(demo_session, now)]`), `FakeDemoService(*, staffing=OFF, clock=START_CLOCK,
converted_on_change=0, staffing_raises=None)` (`.current_mode`, `.clock`, `.calls: list[DemoCall(method, at_mono,
kwargs)]`), `FakeResetService(*, outcomes=(), default=ResetDoneStub(2, 1, START_CLOCK))` (`.outcomes: list`,
`.default`, `.calls: list[(now, {"request_id", "session_id", "role"})]`); `DemoHarness(app, settings, store, identity,
demo, resets, wall, trace)`; `demo_app(monkeypatch, settings, *, identity=None, demo=None, resets=None, store=None,
limiter=None, wall=None) -> DemoHarness`; `signed_in(h, role=DemoRole.CUSTOMER) -> (cookie headers, LoginSession)`;
`hold_gate_for(gate, seconds) -> GateHold(thread, released_at)`.

---

## 7. Checks

### 7.1 Frozen tests (done; `tests/api/test_demo_routes.py`, 13 tests)

`test_inbox_matches_openapi` (AC-1), `test_inbox_scoped_to_login_session` (AC-2), `test_inbox_code_never_logged` (AC-3),
`test_staffing_matches_openapi` (AC-4), `test_clock_is_demo_clock_and_get_only` (AC-5, amended `7d29c51`),
`test_reset_matches_openapi` (AC-6), `test_reset_refusals` (AC-7), `test_reset_throttle_per_ip` (AC-8),
`test_reset_gate_answers` (AC-9), `test_staffing_validation_error` (AC-10), `test_inbox_request_rate_limited` (AC-11),
`test_login_gate_and_any_role` (AC-12), `test_inbox_code_gone_is_expired` (AC-14). Tamper check: `git diff 7d29c51 --
tests/api/test_demo_routes.py tests/api/demo_support.py` is empty at every commit.

### 7.2 Tests the implementer writes with the code

`tests/api/test_demo_capture.py` (use `captured_log()` + `records_of(stream, "request")`; print each recorded status
beside the response status):

- `test_demo_entry_points_emit_records` (AC-13): `store = FakeSessionStore()`; `app = full_app(monkeypatch, settings,
  store=store, heartbeat=FakeHeartbeat(), overrides=ContainerOverrides(wall_clock=MutableClock(WALL_START)))` — the
  **real** `build_container` with every hunk — then `app.dependency_overrides[get_identity_service] = lambda: identity`,
  same for `get_demo_service` and `get_reset_service` with `FakeIdentityService()`, `FakeDemoService()`,
  `FakeResetService()`; token `store.issue(DemoRole.SUPERVISOR, now=WALL_START)`; call the five operations once each
  (reset with `{"confirm": True}`, set staffing with `{"mode": "simulated_on_shift"}`); exactly five `request` records
  whose `route` values are `/api/demo/inbox`, `/api/demo/staffing` (×2), `/api/demo/clock`, `/api/demo/reset`, each
  `status` 200, `caller_role == "supervisor"`, `request_id` equal to that response's `X-Request-ID`; the
  `set_staffing` call's kwargs carry that request's id and `DemoRole.SUPERVISOR`; the reset call carries its request
  id, `store.session_of(token).session_id`, `DemoRole.SUPERVISOR`.
- `test_wf3_inbox_login_gate_and_request_status` (AC-17): one `demo_app(..., limiter=RateLimiter(WebLimits(
  reads_per_session_per_min=1, reads_per_ip_per_min=100)))`; no cookie → 401 (validates), `h.identity.calls == []`;
  four sessions, one per `DemoRole` → 200 each (one held active message each, digits from `new_digits()`); the customer
  session again → 429; a fifth session while `reset_gate_of(h.app).hold()` is held → 503; `h.identity.raises =
  RuntimeError("inbox down")`, a sixth session → 500 (no `assert_matches`: undocumented); recorded statuses equal the
  responses' in order; only the 500 record has `error_kind == "RuntimeError"`; no served digits in `stream.getvalue()`
  or `app_log_text(caplog)`.
- `test_wf5_read_limits_and_request_status` (AC-18): same limiter; session A: `GET staffing` 200, `GET staffing` 429,
  `GET clock` 429, `PUT staffing {"mode": "simulated_on_shift"}` 200, `PUT staffing {"mode": "maybe"}` 400; then
  `h.demo.staffing_raises = RuntimeError("staffing down")` and a fresh session B `GET staffing` → 500 with `error_kind`;
  the two 429s validate against `getStaffing` / `getDemoClock`; recorded statuses equal response statuses.
- `test_wf15_reset_request_status` (AC-19): `make_settings(tmp_path, trust_proxy_headers=True)`, every post with
  `X-Forwarded-For: 198.51.100.40`, `FakeResetService(outcomes=[ResetDoneStub(open_chats_ended=0, roles_reset=0,
  clock=START_CLOCK), ResetAlreadyRunning(), ResetFailedStub()])`: post 1 → 200; `{"confirm": False}` → 400 (not
  counted); post 2 → 409 busy; post 3 → 500; posts 4–10 → 200; post 11 → 409 throttled; recorded statuses equal
  response statuses; only the 500 record has `error_kind == "RESET_FAILED"`; `len(h.resets.calls) == 10`.

`tests/api/test_demo_register.py::test_register_demo_routes_includes_router_once`: `register_demo_routes(Container(
settings=s, limits=Limits()), FastAPI(), settings=s, limits=Limits())` on a bare app adds no `/api/demo/` route; on
`app = create_app(make_settings(tmp_path))` (not started; its `app.state.web_shell` is set by `create_app`) it adds
exactly `{("GET", "/api/demo/inbox"), ("GET", "/api/demo/staffing"), ("PUT", "/api/demo/staffing"), ("GET",
"/api/demo/clock"), ("POST", "/api/demo/reset")}` with operation ids `listDemoInbox`, `getStaffing`, `setStaffing`,
`getDemoClock`, `resetDemo` (via `effective_routes`); a second call adds nothing (same set, same count).
`create_app` sets `app.state.web_shell` eagerly (`web/app.py` line 88), so no lifespan is needed for this test.

`tests/api/test_demo_flows.py` (module docstring: mock-level flows for AC-16 and the R3-2 rule; not journey files,
because the harness forbids TestClient and doubles under `tests/journeys/`):

- `test_wp2_inbox_active_then_used_and_second_reviewer_empty(monkeypatch, tmp_path)`: `h = demo_app(...)`;
  `a_cookie, a = signed_in(h)`; `b_cookie, _ = signed_in(h)`; `d = new_digits()`;
  `h.identity.by_session[str(a.session_id)] = (inbox_message(digits=d, status="active"),)`. In one client block:
  A's inbox → 200, `assert_matches(r, "listDemoInbox")`, one message: `status == "active"`, `code == d`,
  `body == render(TextId.INBOX_CODE_BODY, digits=d)`, `to_masked == "···02"`, `expires_at − at == 10 min` (parse with
  `datetime.fromisoformat`); B's inbox → `{"messages": []}`, validates; then
  `h.identity.by_session[str(a.session_id)] = (inbox_message(digits=None, status="used"),)` (AEA-27's shape after a
  `Verified`) → A's inbox: `status == "used"`, `code == CODE_GONE`, `body == render(TextId.INBOX_CODE_GONE)`,
  `d not in r.text`, validates; then `POST /api/demo/reset {"confirm": True}` with A's cookie → 200,
  `assert_matches(r, "resetDemo")`, `clock.date_label == START_DATE_LABEL`.
- `test_inbox_code_gone_keeps_used_and_expired(monkeypatch, tmp_path)`: the double returns `(inbox_message(digits=None,
  status="used", msg_id="msg-3"), inbox_message(digits=None, status="expired", msg_id="msg-2"),
  inbox_message(digits=None, status="active", msg_id="msg-1"))` → statuses `["used", "expired", "expired"]`, every
  `code == CODE_GONE`, every `body == render(TextId.INBOX_CODE_GONE)`, validates; and directly
  `to_wire_message(inbox_message(digits=None, status="used")).status == "used"` (import `to_wire_message` from
  `meridian.web.routes.demo`). Docstring: `invariant (AC-14, R3-2): dots are never active; used and expired keep their
  status.`
- `test_j8_reset_returns_staffing_and_clock_to_defaults(monkeypatch, tmp_path)`: a local class

  ```python
  class LinkedResetService(FakeResetService):
      """Stands in for the real reset's effect on the demo double: staffing off, clock at DEMO_START."""
      def __init__(self, demo: FakeDemoService) -> None:
          super().__init__()
          self._demo = demo
      def reset(self, now: datetime, *, request_id: object, session_id: object, role: object) -> object:
          result = super().reset(now, request_id=request_id, session_id=session_id, role=role)
          self._demo.current_mode = OFF.mode
          self._demo.clock = START_CLOCK
          return result
  ```
  `demo = FakeDemoService(staffing=OFF)`; `h = demo_app(..., demo=demo, resets=LinkedResetService(demo))`; sign in;
  `PUT staffing {"mode": "simulated_on_shift"}` → 200; `demo.clock = ClockViewStub(DEMO_START + timedelta(days=3),
  "Mon Oct 19, 2026 · 10:00 am", "Mon Oct 19, 2026 (demo date)")` (the advance is AEA-47's; the double stands in);
  `GET clock` → that label; `POST reset {"confirm": True}` → 200; `GET staffing` → `mode == "nobody_online"`,
  `banner is None`; `GET clock` → `label == START_LABEL`, `date_label == START_DATE_LABEL`,
  `datetime.fromisoformat(now) == DEMO_START`; every response through `assert_matches`.

Plus `tests/api/test_contract_cases_demo.py::test_demo_cases_drive_documented_statuses` (Step 11) and the three journey
tests (Step 12).

### 7.3 Commands (cheapest first; stop at the first unexpected red)

```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-43 && export UV_LINK_MODE=hardlink
# while iterating
uv run pytest -q tests/api/test_demo_routes.py tests/api/test_demo_capture.py tests/api/test_demo_register.py \
  tests/api/test_demo_flows.py tests/api/test_contract_cases_demo.py
# once before commit B
uv run ruff check src/meridian/web tests/api tests/contract/cases tests/journeys/j3 tests/journeys/j8
uv run ruff format --check src/meridian/web tests/api tests/contract/cases tests/journeys/j3 tests/journeys/j8
uv run mypy
uv run pytest -q tests/api tests/unit/web tests/unit/test_import_direction.py tests/unit/test_skeleton.py
uv run pytest -q tests/contract/test_openapi_server.py -k "case_files or every_operation or listDemoInbox or Staffing or getDemoClock or resetDemo" -rs
uv run pytest -q tests/journeys/support -rs
uv run pytest -m journey tests/journeys/j3/test_aea_43.py tests/journeys/j8/test_aea_43.py -rs
uv run python -m tests.journeys.affected --base main -- -q -rs
grep -n "strftime\|datetime.now" src/meridian/web/routes/demo.py src/meridian/web/schemas/demo.py   # prints nothing
git diff 7d29c51 -- tests/api/test_demo_routes.py tests/api/demo_support.py                          # empty
python3 ~/.claude/skills/icm-project/scripts/check_context.py .
```

If you add xdist, `-n 2` at most. "Affected" = `tests/api/` (mirrors `web/`), `tests/unit/web/` (`test_container.py`
reads the hunk docstring), `tests/unit/test_import_direction.py`, `tests/unit/test_skeleton.py`, the AEA-59 runner (it
loads `tests/contract/cases/demo.py`), the harness self-tests (one step calls `getDemoClock`), and every journey (a new
file under `tests/journeys/` selects them all in `tests/journeys/affected.py`). No full suite: nothing here reaches a
shared fixture, settings, a dependency or a cross-codebase module.

**What passing looks like:**
- ruff and format clean; mypy "Success: no issues found"; the grep and the frozen-file diff print nothing; the context
  check shows no FAIL.
- `tests/api …` run: 0 failed.
- AEA-59 runner subset: `test_case_files_are_well_formed` and `test_every_operation_has_a_case` pass; the non-success
  drives run under `test_route_cases_match_contract[<op>/<drive>]`; the five
  `test_unauthenticated_matches_contract[...]` for the demo ops pass; `test_validation_error_matches_contract[resetDemo]`
  and `[setStaffing]` pass; `listDemoInbox/reset_running`, `setStaffing/reset_running`, `resetDemo/not_confirmed`,
  `resetDemo/already_running` and the five `no_session` drives pass; the `rate_limited` drives are not run (local-driver
  only); drives that reach `DemoService` skip with `not bound: get_demo_service`. **One failure is expected until AEA-30
  and AEA-29 are on `main`:** `test_success_matches_contract[resetDemo/confirmed]` with `resetDemo: unhandled
  ModuleNotFoundError (500)` (the real `ResetService` imports AEA-30's `format_clock`). Any other red: fix it or stop and
  report. Quote the run's summary line and this failure in the record and the report.
- Journeys: the three AEA-43 journey tests skip with `blocked-on AEA-30, …` / `blocked-on AEA-40, AEA-51, AEA-30`
  reasons (no failure); the affected-journeys command shows no failure.

| Check | Command | Evidence |
|---|---|---|
| Capture verification WF-3, WF-5, WF-15 | `uv run pytest -q -s tests/api/test_demo_capture.py` | printed record statuses beside response statuses; `error_kind` on the 500s only |
| Evaluation check | n/a (ticket *Evaluation*: N/A) | — |
| Frozen tests green, untouched | `uv run pytest -q tests/api/test_demo_routes.py`; the `git diff 7d29c51` above | 13 passed; empty diff |
| Contract cases | `uv run pytest -q -s tests/api/test_contract_cases_demo.py` and the runner subset | 22 drive lines; runner summary as above |
| Journeys | the two journey commands | skips with `blocked-on` reasons; record file |

---

## 8. Risks and requests

- **R-1 Sibling result types.** AEA-30 returns `domain/views.py` models (`StaffingView`, `StaffingChange`, `ClockView`),
  AEA-31 returns `ResetDone(clock=ResetClock)` / `ResetFailed`. The route reads them by attribute
  (`from_attributes=True`) and tells `ResetFailed` apart by `code == "RESET_FAILED"`; it imports none of them. No blocker.
- **R-2 Shared context rows.** Area map row A8 is one cell edited by AEA-40, 41, 42, 43, 49: expect a textual conflict
  at the merge; keep every ticket's text. The ICM edit is a new row; the DO-3 edit is this ticket's own line.
- **R-3 `web/container.py`.** Only `register_demo_routes` changes; `app.state.demo_routes_included` is read by no other
  code.
- **R-4 Throttle counting** (§3.2): a busy or failed reset still counts toward 10 per 600 s; visible to the security
  reviewer.
- **R-5 Router-level `Depends(get_login_session)`** duplicates the gate on purpose; FastAPI caches it per request.
- **R-6 Journey level.** Every harness step is blocked today: J-3 step 0 on AEA-30; J-3 step 1 on AEA-40, AEA-51, AEA-30;
  J-8 on AEA-30, AEA-29. AC-16's evidence is `mock-tested` (`tests/api/test_demo_flows.py`). The steps run, unchanged,
  as soon as those land; J-3 step 1's body is AEA-51's to write (AEA-27 plan R-1 precedent).
- **R-7 AC-15's strict run** (`CONTRACT_STRICT=1`) fails until AEA-30 binds `demo_service` (skips become failures) and
  until AEA-59 has a `reset_fails` word (completeness is per operation, so `resetDemo` is covered; only the 500 drive is
  missing from the runner). It belongs to the wave merge, not this ticket's commit.
- **R-8 (closed)** Frozen clock-test bug, fixed by Step 6a at `7d29c51`.
- **R-9 (closed)** `main` moved since the branch was cut: handled by Step 8 (merge `main` into the branch).
- **R-10 `used` with no code (R3-2, decided here).** AC-14's sentence says every `code=None` message is serialised
  `expired`; AEA-27 (merged) returns a used code as `status="used", code=None`, and AC-16 and the OpenAPI's
  `USED_AND_EXPIRED` both expect `used` on the wire. The route keeps `used`/`expired`, and turns only `active` without
  digits into `expired`. Security effect: none (no digits are ever shown without being held; the dots and the "no longer
  shown" text appear in all three cases). The frozen AC-14 test passes unchanged; its docstring ("always shown expired")
  is now looser than the rule; the implementer must not edit it. The security reviewer should read this row.
- **R-11 Request to AEA-59 (integrator follow-up, not an edit here):** add `"reset_fails"` to `LOCAL_DRIVER_ONLY` in
  `tests/contract/openapi_cases.py` (reason: "needs a ResetService double that returns ResetFailed; proved by the
  route's local driver (mock-tested)"). Then move the `failed` drive from `LOCAL_ONLY_DRIVES` into
  `CASES["resetDemo"]["drives"]` in `tests/contract/cases/demo.py` (a one-line follow-up on AEA-43). Until then the 500
  is proved by the local driver and by the frozen `test_reset_refusals`.
- **R-12 Merge order (for the orchestrator's merge tree).** AEA-43 must merge into `main` **after AEA-30 and AEA-29**:
  once this ticket registers `POST /api/demo/reset`, AEA-59's runner drives `resetDemo/confirmed` through the real
  `ResetService`, which needs AEA-30's `services/demo.format_clock` (else `ModuleNotFoundError` → hard failure) and
  AEA-29's `services/handoff` seed (else `ResetFailed` → 500, a failure). Neither is an import of AEA-43's code, so the
  build is not blocked; only the merge is. After both land, re-run the runner subset on the merged branch:
  `resetDemo/confirmed` must pass.
- **R-13 `tests/api/test_app.py` (AEA-23's)** adds probe routes on `/api/demo/inbox` to apps built with `web_app` (only
  `register_web`, so no demo router) and `full_app` (probes added before the lifespan includes the demo router, so the
  probe matches first). Expected green; if not, stop and report (do not edit it).
- **No shared primitive requested** beyond R-11. No signed contract change; nothing in the OpenAPI disagrees with this
  plan.

---

## 9. Readiness

**READY** (revision 4). The implementer starts at **Step 9a** in the existing worktree (Steps 1–8 done: commit A
`db9ef50`, merge `a8c8b5d`). Blocked by AEA-23 only (merged).
No `NEEDS-DECISION`: the open choices (throttle counting, 409 `retry_after_ms`, strict `confirm`, extra properties,
double-include guard, the R3-2 status rule, `LOCAL_ONLY_DRIVES`) are engineering decisions inside decisions already
taken (WEB-25, WEB-26, WEB-27, MC-19, MC-20) and change no signed contract. No `BLOCKED-ON` for the build: AEA-27, 30,
31 are reached through `web/deps.py` overrides and doubles. **Merge-order constraint:** merge after AEA-30 and AEA-29
(R-12). Request to the integrator: R-11 (AEA-59 vocabulary word).

**Gates:** none human, external, paid or live. `security-privacy-agent` reads this diff at the wave-2 merge
(`risk::security`), including R-4 and R-10.

## Deviations

- Contract-case drive count is 21 (20 in `CASES` plus the local-only `RESET_FAILED`), not 22: the plan's arithmetic was
  off by one. The local-driver test asserts 21.
- `src/meridian/web/routes/demo.py` was reformatted with `ruff format` (commit A was unformatted and the fast gate
  `ruff format --check` failed); formatting only.
- `test_wf3`: the 503 record also carries `error_kind` (`RESET_IN_PROGRESS`), so the test asserts that, not "only the 500".
- `uv run mypy` reports one error in the frozen `tests/api/test_demo_routes.py:222` (`"BaseRoute" has no attribute
  "methods"`). The file is frozen and cannot be edited here; planner/test-writer should fix it (e.g. `getattr(route,
  "methods", ())`).
- The runner's `resetDemo/confirmed` skips (`not bound: demo_clock`) instead of failing with ModuleNotFoundError.
