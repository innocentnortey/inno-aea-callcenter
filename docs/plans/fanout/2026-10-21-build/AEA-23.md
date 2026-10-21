# Plan — [AEA-23] web: app, middleware, demo login, dependency providers

**Status:** planned
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #23 (= `docs/plans/tickets/AEA-23.md`) · **Base revision:** `16ca639` (main, after AEA-01, 03, 04, 08, 25 merged)
**Refreshed:** 2026-10-21 against main `16ca639` (nothing under `src/`, `tests/`, the OpenAPI, web.md or the ticket changed
since the first draft at `c15a6b1`; only README, SUBMISSION and the ledger) and against AEA-02's frozen tests on branch
`aea-02-aea-02-domain-ports` at `de9bb42` (§4.2 note). Every step, name and test below still holds.
**Lane / risk:** `lane::build-loop`, `risk::security` → the test-writer freezes the tests in §7.1 first; the implementer never edits them.
**Blocked on (real imports):** AEA-02 (`config.Settings`, `domain/common.py` `ApiErrorCode` / `RequestId` / `ThreadId`, `domain/staff.py`, `ports/models.py`, `ports/runtime.py`). AEA-01 and AEA-04 are already on main.
**Planner model:** claude-opus-5-5. **Implementer:** Sonnet (`fanout-implementer`).

---

## 1. Goal and sources

### Goal (from the issue, *What to build*, quoted)

> **US-28 · Sign in once, then switch between customer and staff in one click.** "As a **reviewer**, I need to sign in
> once with the demo login given in the README and then switch between acting as the customer and acting as a
> representative, supervisor or business owner in one click from any screen [...]" Acceptance includes: "nothing except
> the login and `/healthz` answers without the login … a wrong login gets one message whatever the cause; an expired
> session returns to the login." Also US-26 ("a rate limit … shows a plain message and the person option; no account
> existence is revealed").
>
> The HTTP shell every route ticket (AEA-40…AEA-49) plugs into, and the one gate in front of all of them. Every shape
> below is defined in `docs/design/contracts/stage7/web.md` ("web §n"); where web.md and DO-4 disagree, web.md wins.

Items 1–8 of the issue (errors, app, middleware, logging, auth route + schema, deps, reset gate, `openapi_check.py`)
are the deliverables; §5 below builds each one.

### Context

Stage 7 closed on 2026-10-21 with 62 tickets; wave 0 (AEA-01, 03, 04 merged; AEA-02 in flight: frozen tests committed at
`de9bb42`, `domain/common.py` being written in its worktree) gives the package
skeleton, `Limits`, the container with 27 `register_<area>()` stubs, and the redaction function. Nothing serves HTTP yet.
Every wave-2 route ticket (AEA-40…49), the journey harness (AEA-57) and the contract runner (AEA-59) are blocked by this
ticket, because it owns the app factory, the one login gate, the provider declarations in `web/deps.py` and the one
OpenAPI response validator. It is `risk::security`: a bug here opens every route, leaks the demo pair, the cookie token
or the eval key, or lets public traffic tag itself `eval`.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Requirements | PRD `docs/prd/inno-aea-callcenter-prd.md` R-41 (rate limits per session and IP), R-48 (one demo login; role switch), R-40 (secrets in Railway variables); US-26, US-28; PRD §5 *Load* "rate limits … are set above 20" | One gate on every route but `login` and `/healthz`; per-session/IP limits that admit 20 conversations from one IP; secrets only from `Settings` |
| Component contracts | `docs/design/contracts/stage7/web.md` §1–§7, §10, §13, §15 (wins over DO-4 §11, §16); `stage7/staff.md` §1–§2; `stage7/cases.md` §1.2 (`lookup`, `EndedThread`), §8 (`Heartbeat`); `stage7/graph-nodes.md` §4 (`SignalRecord`); `stage7/graph-core.md` §12 (`Settings`); OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml` (wins on every wire shape); residuals R-W-1, R-W-3, R-W-8, R-W-9; UX-join AEA-23-1…3; merge MC-1, 2, 4, 5, 9, 14, 15, 16, 20, 22, 27 | Exact signatures in §4 below; every status and code from the OpenAPI; nothing new on the wire |
| Evaluation plan | `docs/design/evaluation-plan.md` E-8 (load from one IP and one login), CAP-7 (eval tag) | AC-13 (20 conversations never limited); AC-15 (eval/load tag only with the key). No DO-5 suite added |
| Observability contract | `docs/design/observability-contract.md` WF-17 (`/healthz`), WF-18 (login/logout, CAP-10), *Records*, *Status values* (`request.status` + `error_kind` on 5xx), *Correlation* (eval key), *Content* (session cookies never) | `request` and `auth_event` records through an allow-list formatter; CAP-10 driven at the real routes (AC-25); status/error_kind (AC-32, AC-33) |
| Key-metrics registry | `docs/design/key-metrics-registry.md` M-28 (health-check restarts), M-22, M-3, M-18 (exclude eval/load), M-24 (`degrade_reason` `rate_limit`) | `/healthz` answers truthfully from the heartbeat (M-28); run tags right (M-3, M-18, M-22); the turn verdict is exposed for AEA-40 (M-24). No target set here |

Also read: `CLAUDE.md`, `.claude/README.md`, `.claude/reference/area-map.md`, rules `build-loop-test-scope.md` (+ AEA
addition), `integrated-journeys.md`, `context-maintenance.md`, `safe-validation-errors.md`, workspace `async-safety.md`,
`code-structure.md`, `code-design-solid-modularity.md`; `docs/design/code-design.md` §2.1–§2.3, §3; slice plan §0, §0a,
§1 row AEA-23, §3; `docs/plans/stage7-signoff.md` D-4…D-15 (D-4 WEB-1 = A, D-7 separate throttle message (frontend
copy only), D-8 start a fresh chat after re-login, D-13 test-only wall-clock override — all consistent with this plan);
the merged code on main (`src/meridian/web/container.py`, `policy/limits.py`, `privacy/redact.py`,
`tests/unit/web/test_container.py`, `tests/journeys/affected.py`); the AEA-02 and AEA-10 plans in this folder (for the
exact shapes of `Settings`, `domain/staff.py`, `UnitOfWorkFactory`, `EndedThread` and the container key `uow_factory`);
`apps/web/src/api/client.ts` (read only: how the browser parses error bodies).

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| One `ApiProblem`, one renderer, 422 → 400 `VALIDATION_ERROR` without the value | web §1; DO-4 §0; safe-validation-errors | AC-9 | in-ticket | Step 2, 8 |
| `X-Request-ID` on every response, = `request_id` in error bodies | web §6 step 1; OpenAPI headers | AC-10 | in-ticket | Step 6 |
| Gate: 401 `UNAUTHENTICATED` (`none`/`expired`) on every route but `login`, `/healthz` | web §6; OpenAPI `Unauthenticated`; R-48 | AC-1, AC-3 | in-ticket | Step 6 |
| Page GET → 303 to `/login?return_to=…&reason=…`; no open redirect | web §6; WEB-28 | AC-2 | in-ticket | Step 4, 6 |
| Expired session clears the cookie (`Max-Age=0`); expiry on the wall clock only | web §2, §6; MC-5, MC-20 | AC-3 | in-ticket | Step 6 |
| Login: both comparisons always, `hmac.compare_digest`, one `LOGIN_FAILED` | web §2; SCREEN_SPECS N-28; OpenAPI `LoginFailed` | AC-5 | in-ticket | Step 7 |
| Login cookie attributes; old valid session ended first; body from `session_info` | web §2; R-W-1; OpenAPI `mhcSession` | AC-4 | in-ticket | Step 7 |
| Malformed login body → 400 naming field and rule, never the value | web §2; WEB-10; DO-6 WF-18 | AC-6 | in-ticket | Step 2, 7 |
| Login throttle per IP: 10 rejects / 600 s → 429 `LOGIN_RATE_LIMITED` + `Retry-After` | web §5; WEB-4 | AC-7 | in-ticket | Step 4, 7 |
| Credentials, token, session secret never in body, log, span or DB | DO-6 CAP-10 *Asserts absent*; *Content* | AC-8 | in-ticket | Step 3, 7 |
| Six read ops 429; `submitTurn` verdict into `RequestContext`; `requestPerson` never limited; set checked vs OpenAPI | web §5; WEB-3, WEB-12; DO-1 §8.2 | AC-12 | in-ticket | Step 4, 6 |
| Limits admit 20 conversations from one IP and one login | PRD §5 *Load*; WEB-2; E-8 | AC-13 | in-ticket | Step 4 |
| Client IP = last `X-Forwarded-For` entry when trusted, else the peer; keys never the cookie | web §4; [A] AEA-56 | AC-14 | in-ticket | Step 4 |
| Eval tag only with the eval key (`hmac.compare_digest`) | web §4; WEB-7; DO-6 *Correlation* | AC-15, AC-16 | in-ticket | Step 4, 6 |
| `request` / `auth_event` records, allow-list formatter through the LOG profile; `signal`, `stream_reconnect` pass-through | web §10; WEB-11; graph-nodes §4; DO-6 *Records* | AC-17, AC-25 | in-ticket | Step 3 |
| `web/deps.py` declares every provider, `require_staff`, `owned_thread`, `owned_stream_thread`; lazy `not bound` errors; one `CapacityLimiter(4)` | web §3, §4; R-W-3; WEB-19 | AC-18 | in-ticket | Step 5 |
| `require_staff` 403 with `role`, `needs` in order, `reason`; role resolved per request | web §3; MC-4; AEA-23-2 | AC-19, AC-28 | in-ticket | Step 5 |
| `owned_thread` 404/410 rules; `owned_stream_thread` maps ended → identical 404, one lookup | web §4; WEB-34; MC-16; R-W-3 | AC-20 | in-ticket | Step 5 |
| Reset gate: eight ops 503 at once; others wait ≤ 5 s; second hold raises | web §7; WEB-13, WEB-37; MC-14, MC-27 | AC-21 | in-ticket | Step 1, 6 |
| `resetDemo` must not wait (its route answers 409 itself) | web §7 table row `resetDemo` | AC-21 (implied) | added | Step 4 (`RESET_NO_WAIT_OPERATIONS`), Step 6 |
| Logout 204, `Max-Age=0`, `end` idempotent; old cookie then 401 | web §2; OpenAPI `logout` | AC-22 | in-ticket | Step 7 |
| Lifespan builds once, closes once; no module-level singletons in `web/` | DO-3 §2.1; async-safety rule 2 | AC-23 | in-ticket | Step 8 |
| `openapi_check.py` validator + `ContractLoader` YAML 1.2 strings | web §13; R-W-9; AEA-23-1 | AC-24, AC-27 | in-ticket | Step 10 |
| `ContractLoader` must also keep `22:00` a string (YAML 1.1 sexagesimal int → 1320 breaks 6 `getMonitoring` examples; measured in planning) | AC-24 "passes the OpenAPI's own examples"; AC-27 "YAML 1.2" | AC-24, AC-27 | added | Step 10 (int/float resolvers), test fact 4 in §7.1 |
| CAP-10 capture at the real login route; WF-17 `/healthz` record | DO-6 CAP-10, WF-17, WF-18 | AC-25, AC-26, AC-32, AC-33 | in-ticket | Step 3, 6, 8 |
| `/healthz` async, from the injected heartbeat, never pool/SQLite/reset | web §7; DO-3 §2.3 rule 3; cases §8 | AC-11 | in-ticket | Step 8 |
| Per-route contract cases for `login`, `logout` | slice plan §0a; AEA-23-3 | AC-29 | in-ticket | Step 11 |
| Container overrides test-only; wall clock override reaches `get_wall_clock` only | web §15; R-W-8; D-13 | AC-30, AC-34, AC-35 | in-ticket | Step 8, 9 |
| Unhandled exception → 500 with `X-Request-ID` and `error_kind`, **no invented error code** (the OpenAPI `ApiError.code` enum has no generic code) | OpenAPI `ApiError` enum (wins on codes); DO-6 *Status values* | AC-32, AC-33 (body wording) | added | Step 6 (decision D-P1, §8) |
| Every registered `/api` route is in the operation table (classification for limits and reset) | web §5, §7 (sets are constants checked against the OpenAPI) | AC-1 (route loop) | added | Step 4, test `test_every_api_route_but_login_requires_session` |
| Journey record `mock-tested`, blocked by AEA-57 / AEA-52; J-1, J-8 named | integrated-journeys §3–§4; slice plan §0a | AC-31 | in-ticket | Step 13 |
| Same-change context updates (area map A8, ICM row, DO-3 *Built* line) | context-maintenance; AC-36 | AC-36 | in-ticket | Step 13 |
| Heartbeat object (`Heartbeat`, `beat`, watchdog) | cases §8 | — | other-ticket | AEA-32 (binds `deps.HEARTBEAT`) |
| `StaffSessionStore` implementing `LoginSessions` + `StaffAccess` | staff §2 | — | other-ticket | AEA-44 (binds `deps.LOGIN_SESSIONS`, `deps.STAFF_ACCESS`, `deps.FLAG_SERVICE`) |
| `core.conversations.lookup`, `EndedThread`, `SqliteUnitOfWorkFactory` | cases §1.2 | — | other-ticket | AEA-10 (provides container key `uow_factory`) |
| `/login` page, asset public paths, SPA fallback | web §6, §12; D-4 | — | other-ticket | AEA-49 |
| `RATE_LIMITED` chat notice, `RESET_IP` 409 answer | web §5, §9 | — | other-ticket | AEA-40 (notice), AEA-43 (`resetDemo`) |
| Strict contract run of the `auth` cases | slice plan §0a | AC-29 (verify later) | other-ticket | AEA-59 (runner); evidence recorded later |
| uvicorn's access log prints raw paths and query strings (would defeat AC-17 in deploy) | DO-6 *Content*; web §10 | — | other-ticket | AEA-50 (start command `--no-access-log`), request in §8 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `POST /api/login`, `POST /api/logout` (CON-22) and the middleware session check | WF-18 | yes (DO-6 WF-18, CAP-10, 2026-10-21) | n/a — the login gates access and decides no outcome; rejected attempts feed the rate limit (R-41) |
| `GET /healthz` | WF-17 | yes (DO-6 WF-17, CAP-9) | M-28; the "last health-check restart" line on SCR-10 |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files the implementer creates or edits)

| File | Action | Who writes it |
|---|---|---|
| `src/meridian/web/errors.py` | create | implementer |
| `src/meridian/web/logging.py` | create | implementer |
| `src/meridian/web/middleware.py` | create | implementer |
| `src/meridian/web/deps.py` | create (sole owner, slice plan §3) | implementer |
| `src/meridian/web/app.py` | create | implementer |
| `src/meridian/web/routes/auth.py` | create | implementer |
| `src/meridian/web/schemas/auth.py` | create | implementer |
| `src/meridian/services/reset_gate.py` | create (MC-27) | implementer |
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_web`** | implementer |
| `tests/api/openapi_check.py` | create (shared validator; product code for tests) | implementer |
| `tests/contract/cases/auth.py` | create (AC-29 case data) | implementer |
| `docs/testing/journeys/<build date>-AEA-23.md` | create (AC-31) | implementer |
| `.claude/reference/area-map.md` (A8 row *Status* cell only), `.claude/state/icm-progress.md` (row *Routes verified against code and tests*, evidence cell only), `docs/design/code-design.md` (the `**Built:**` line above the §3 tree only) | modify | implementer |
| `tests/api/web_shell_support.py` and the ten test files in §7.1 | create | **test-writer** (frozen; implementer must not edit) |

### 2.2 Shared surfaces read only

`src/meridian/web/container.py` outside `register_web` (AEA-01's `Container`, `Key`, `ContainerError`,
`build_container`); `src/meridian/policy/limits.py` (`Limits`, `WebLimits`); `src/meridian/privacy/redact.py`
(`redact`, `RedactionProfile`); AEA-02's `src/meridian/config.py`, `domain/common.py`, `domain/staff.py`,
`ports/models.py`, `ports/runtime.py`; `docs/ux/03-structure/ui-contracts.openapi.yaml` (read, never written);
`pyproject.toml` / `uv.lock` (no change: every library needed is already pinned — fastapi 0.156, starlette 1.9,
pydantic 2.14, anyio 4.x, httpx, jsonschema ≥ 4.18 + referencing, pyyaml).

### 2.3 Owned by other tickets — do not touch

Every other `register_<area>()` hunk; `domain/*`, `config.py`, `ports/*` (AEA-02); `policy/*` (AEA-01, 03);
`adapters/**`; every other `web/routes/*.py` and `web/schemas/*.py`; `web/frontend.py` (AEA-49); `tests/conftest.py`,
`tests/journeys/**` (AEA-01, AEA-57); `tests/unit/web/test_container.py` (AEA-01); `tests/contract/test_openapi_*.py`
(AEA-59); `apps/web/**`, `docs/ux/**`, the OpenAPI, `UI_CONTRACTS.md`, the briefing, issued data, `docs/archive/`,
`docs/parked/`.

---

## 3. Requirements table (acceptance criteria → implementation → verification)

**Verbatim criteria:** `docs/plans/tickets/AEA-23.md` *Acceptance criteria* (AC-1…AC-36, lines 158–195). The test-writer
and the implementer read them there; each row below summarises one and names the test that proves it. Where a row
and the issue differ, the issue wins, except AC-32's body shape (D-P1, §8). Test files are the test-writer's (§7.1).
Commands: §7.

| AC | Requirement (short) | Implemented by (step) | Verified by |
|---|---|---|---|
| AC-1 | Every `/api/*` route except `POST /api/login` → 401 `UNAUTHENTICATED` `reason: none` with no / blank / unknown / tampered cookie; `/healthz` answers; public set holds the two entries | Step 6 gate, Step 9 public paths | `tests/api/test_gate.py::test_every_api_route_but_login_requires_session` |
| AC-2 | Unsigned page GET → 303 `/login?return_to=<path+query>&reason=none`; hostile `return_to` never in a `Location` | Step 4 `safe_return_to`, Step 6 | `tests/api/test_gate.py::test_page_get_redirects_to_login_without_open_redirect` |
| AC-3 | `SessionExpired` → 401 `reason: expired` / 303 `reason=expired`, `Set-Cookie … Max-Age=0`; `resolve` gets the wall clock | Step 6 | `tests/api/test_gate.py::test_expired_session_reason_expired_and_cookie_cleared` |
| AC-4 | Login success: 200 `LoginResponse`, cookie attributes (both `cookie_secure` values), `end` before `start` | Step 7 | `tests/api/test_auth.py::test_login_success_sets_session_cookie` |
| AC-5 | Five failure causes → byte-identical 401 `LOGIN_FAILED`; two `compare_digest` calls per attempt | Step 7 | `tests/api/test_auth.py::test_login_failed_identical_for_every_cause` |
| AC-6 | Missing field / non-string / non-JSON → 400 naming field and rule, never the value | Step 2, 7 | `tests/api/test_auth.py::test_login_malformed_body_is_400` |
| AC-7 | 10 rejects in 600 s from one IP → 11th (right pair) 429 + `Retry-After` + `details.retry_after_ms`; `auth_event rate_limited`; other IP fine; after the window, works | Step 4 limiter, Step 7 | `tests/api/test_auth.py::test_login_rate_limited_per_ip` |
| AC-8 | Username, password (right or wrong), token, session secret absent from bodies, headers (except the one `Set-Cookie`), log, trace sink, DB text | Step 3, 7 | `tests/api/test_auth.py::test_credentials_and_token_absent_from_body_log_span_db` |
| AC-9 | Malformed body on any route → 400 with `field`, `constraint`, no value; exactly one `ApiError` renderer | Step 2 | `tests/api/test_app.py::test_validation_error_is_400_without_value` |
| AC-10 | `X-Request-ID` on 200, 204, 303, 400, 401, 403, 404, 410, 429, 503, 5xx; equals body `request_id` | Step 6 | `tests/api/test_app.py::test_request_id_on_every_response` |
| AC-11 | `/healthz` async; 200 fresh / non-200 stale; answers while workers blocked, UoW raises, gate held | Step 8 | `tests/api/test_app.py::test_healthz_reads_heartbeat_not_pool_or_db` |
| AC-12 | Six read ops 429; `requestPerson` never; `submitTurn` verdict in context; set = OpenAPI 429 set − `login` | Step 4, 6 | `tests/unit/web/test_middleware.py::test_rate_limits_by_operation`, `tests/api/test_openapi_sets.py::test_rate_limit_set_matches_openapi` |
| AC-13 | 20 conversations from one IP and one login at ≈ 255 turns/min never limited | Step 4 | `tests/unit/web/test_middleware.py::test_limits_admit_twenty_conversations_from_one_ip_and_login` |
| AC-14 | Client IP rule both settings; bucket keys hold no token | Step 4 | `tests/unit/web/test_middleware.py::test_client_ip_and_bucket_keys` |
| AC-15 | Run tag six sub-cases | Step 4, 6 | `tests/unit/web/test_middleware.py::test_run_tag_requires_eval_key` |
| AC-16 | Seeded eval key and keyless `run_id` absent from bodies, log, trace | Step 3, 6 | `tests/unit/web/test_middleware.py::test_eval_key_absent_from_outputs` |
| AC-17 | `request.route` is the template; formatter emits only allow-listed fields; path/query/body/extra values absent | Step 3, 6 | `tests/unit/web/test_logging.py::test_allow_list_formatter_drops_raw_path_query_body_and_extras` |
| AC-18 | Every web §4 provider + `require_staff`, `owned_thread`, `owned_stream_thread`; overridable; lazy `RuntimeError("not bound: <name>")`; one `CapacityLimiter(4)` | Step 5, 9 | `tests/unit/web/test_deps.py::test_every_provider_declared_overridable_and_lazy` |
| AC-19 | `require_staff` returns the actor; 403 body with `role`, `needs` in order, `reason` | Step 5 | `tests/unit/web/test_deps.py::test_require_staff_refusals` |
| AC-20 | `owned_thread` 404 ×4 identical, 410 `demo_reset`; `owned_stream_thread` ended → identical 404, one lookup | Step 5 | `tests/unit/web/test_deps.py::test_owned_thread_404_410`, `::test_owned_stream_thread_maps_ended_to_404` |
| AC-21 | Eight ops 503 at once while held; others wait then answer post-reset; second hold raises; set = OpenAPI 503 `RESET_IN_PROGRESS` set | Step 1, 6 | `tests/unit/web/test_reset_gate.py::test_reset_gate_503_wait_and_double_hold`, `tests/api/test_openapi_sets.py::test_reset_503_set_matches_openapi` |
| AC-22 | Logout 204 + `Max-Age=0` + `end(token)`; second logout 204; old cookie then 401 | Step 7 | `tests/api/test_auth.py::test_logout_clears_cookie_and_ends_session` |
| AC-23 | Lifespan builds once, closes once; no module-level singletons in `web/` | Step 8 | `tests/api/test_app.py::test_lifespan_builds_and_closes_container` + grep (§7.4) |
| AC-24 | Validator rejects undocumented status, schema break, unknown code (message names `info.version`); examples pass; `error_codes` = HTTP members of `ApiErrorCode`; three YAML facts | Step 10 | `tests/api/test_openapi_check.py::test_validator_rejects_and_accepts`, `::test_error_codes_match_openapi`, `::test_loader_keeps_yaml12_strings` |
| AC-25 | CAP-10 sequence: four `request` records, three `auth_event`s in order, 401 body | Step 3, 7 | `tests/api/test_auth.py::test_cap10_login_records_captured` |
| AC-26 | `/healthz` record: route `/healthz`, `caller_role: anonymous`, 200 | Step 6, 8 | `tests/api/test_app.py::test_healthz_request_record` |
| AC-27 | No `datetime`/`date` anywhere in the loaded OpenAPI; `greeting.at` a `str` | Step 10 | `tests/api/test_openapi_check.py::test_contract_keeps_yaml_strings` |
| AC-28 | 403 names the role the session holds on this request; changes between requests | Step 5 | `tests/unit/web/test_deps.py::test_role_refusal_names_current_role` |
| AC-29 | `tests/contract/cases/auth.py` holds `login`/`logout` cases | Step 11 | Now: `tests/api/test_contract_cases_auth.py::test_auth_cases_drive_documented_statuses` (plan-added, local driver). Later (AEA-59 merged): `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "login or logout" -rs` |
| AC-30 | Overrides test-only; `create_app()` passes `None`; given object passed once; no `ContainerOverrides(` in `src/` | Step 8 | `tests/api/test_app.py::test_overrides_test_only` + grep (§7.4) |
| AC-31 [journey] | Level `mock-tested`; record names J-1 and J-8 and *Blocked by* AEA-57 (J-1) and AEA-52 (J-8); affected-journeys command prints "0 journeys affected" | Step 13 | `docs/testing/journeys/<date>-AEA-23.md` + `uv run python -m tests.journeys.affected --base main` |
| AC-32 | WF-18 status values; forced 500 has `error_kind`; non-5xx records have none; no outbound connect | Step 6, 7 | `tests/api/test_auth.py::test_wf18_status_values_and_no_outbound` |
| AC-33 | WF-17 status values: 200 / 503 stale / 500 raising | Step 6, 8 | `tests/api/test_app.py::test_healthz_status_values` |
| AC-34 | `ContainerOverrides(wall_clock=fake)` → `get_wall_clock()` is `fake`; resolve gets exactly the fake's times; expiry → 401 `expired`; demo clock unchanged; default within 2 s of now | Step 8, 9 | `tests/api/test_app.py::test_wall_clock_override_reaches_get_wall_clock` |
| AC-35 | Wall clock not settable from Settings, env, header, query or body; no route names a wall clock | Step 8 | `tests/api/test_app.py::test_wall_clock_not_settable_from_settings_env_or_http` + grep (§7.4) |
| AC-36 | Context files updated in the same change | Step 13 | `git diff --name-only main...HEAD` |
| WP (example pair) | The issue's example pair, end to end (no WP-N exercises the login; the pair is web.md's opening example plus the OpenAPI CON-22 examples) | Steps 5–9 | `tests/api/test_gate.py::test_example_pair_unsigned_page_login_and_role_refusal` (plan-added) |
| PA-1 (plan-added) | Unhandled exception → 500, body `{"request_id": …}` only, `X-Request-ID`, `error_kind` = exception class name; no `error.code` invented | Step 6 | `tests/api/test_app.py::test_unhandled_error_is_500_with_request_id_only` |
| PA-2 (plan-added) | `OPERATIONS_BY_ROUTE` equals the OpenAPI's (method, path) → operationId map | Step 4 | `tests/api/test_openapi_sets.py::test_operation_table_matches_openapi` |
| PA-3 (plan-added) | `register_web` binds the four shell objects and the two public paths, and does nothing on an app `create_app` did not build (keeps AEA-01's stub test green) | Step 9 | `tests/unit/web/test_deps.py::test_register_web_binds_shell_objects_and_skips_bare_app` |

---

## 4. Shared code to use (exact shapes)

### 4.1 Already on main (copy these names exactly)

```python
# src/meridian/web/container.py (AEA-01)
class ContainerError(RuntimeError): ...          # messages: "not provided: <name>", "already provided: <name>", ...
@dataclass(frozen=True)
class Key[T]:
    name: str                                     # two keys are equal when their names are
class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    settings: Any  (property); limits: Limits (property); closed: bool (property)
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...   # before build only
    def get[T](self, key: Key[T]) -> T: ...                                              # lazy, memoised
    def on_start(self, starter: Callable[[], None]) -> None: ...
    def on_close(self, closer: Callable[[], None]) -> None: ...
    def build(self) -> None: ...
    def close(self) -> None: ...                  # idempotent
def register_web(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None: ...  # AEA-23's hunk
def build_container(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container: ...
# register_web is called 2nd (after register_storage), inside the app lifespan. Hunks import their modules INSIDE the
# function body (tests/unit/test_import_direction.py::test_container_imports_only_policy_limits).

# src/meridian/policy/limits.py (AEA-01)
@dataclass(frozen=True)
class WebLimits:
    chat_turns_per_thread_per_min: int = 20; chat_turns_per_session_per_min: int = 600; chat_turns_per_ip_per_min: int = 600
    reads_per_session_per_min: int = 120; reads_per_ip_per_min: int = 240
    login_rejects_per_ip: int = 10; login_reject_window_s: int = 600
    resets_per_ip: int = 10; reset_window_s: int = 600
    login_session_lifetime_s: int = 43_200; reset_wait_s: int = 5
@dataclass(frozen=True)
class Limits: ...; web: WebLimits

# src/meridian/privacy/redact.py (AEA-04)
class RedactionProfile(StrEnum): STORE, SONNET, JEV, TRACE, LOG
@dataclass(frozen=True)
class Redacted: text: str; replaced: Mapping[RedactionKind, int]; length: int     # LOG: text "" and length only
def redact(text: str, profile: RedactionProfile) -> Redacted: ...
```

### 4.2 From AEA-02 (blocked-on; shapes from `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.1, §4.11–§4.14)

```python
# meridian.domain.common
class ThreadId(_PatternId): PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
class RequestId(_PatternId): PATTERN = <same UUID4 pattern>     # RequestId(str(uuid.uuid4())) constructs without validation
class ApiErrorCode(StrEnum): ...  # 35 members; HTTP ones: VALIDATION_ERROR, UNAUTHENTICATED, LOGIN_FAILED,
    # LOGIN_RATE_LIMITED, REQUEST_RATE_LIMITED, SESSION_NOT_FOUND, SESSION_ENDED, TURN_IN_PROGRESS, RESET_IN_PROGRESS,
    # RESET_FAILED, HANDOFF_FAILED, ROLE_NOT_ALLOWED, CASE_NOT_FOUND, ... (no STAFF_AUTH_REQUIRED, no generic code)
class MeridianModel(BaseModel): model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True,
                                                          str_strip_whitespace=True)
# meridian.domain.staff
class DemoRole(StrEnum): CUSTOMER="customer"; REPRESENTATIVE="representative"; SUPERVISOR="supervisor"; OWNER="owner"
class StaffRole(StrEnum): REPRESENTATIVE; SUPERVISOR; OWNER
class StaffActor(MeridianModel): role: StaffRole; name: str; signature: str
def actor_for(role: StaffRole) -> StaffActor: ...
LoginSessionId = NewType("LoginSessionId", str)
class LoginSession(MeridianModel): session_id: LoginSessionId; role: DemoRole; role_reset: bool
                                   signed_in_at: dt.datetime  # demo clock;  expires_at: dt.datetime  # wall UTC
class IssuedSession(MeridianModel): session: LoginSession; token: SecretStr
class SessionMissing(MeridianModel): """No fields."""
class SessionExpired(MeridianModel): """No fields."""
class RoleRefusal(MeridianModel): role: DemoRole; needs: tuple[StaffRole, ...]; reason: Literal["wrong_role", "role_reset"]
class SessionInfoData(MeridianModel): role: DemoRole; display_name: str; sees: tuple[str, ...]; signed_in_at: dt.datetime
# meridian.ports.models
ChoiceRole, StructuredRole, ToolRole (Literal aliases); class ChoiceModel(Protocol); class StructuredModel(Protocol);
class ToolCallingModel(Protocol)
# meridian.ports.runtime
class TraceSink(Protocol): ...
class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
# meridian.config
class Settings(MeridianModel):  # fields used here: demo_username: SecretStr; demo_password: SecretStr;
    # session_secret: SecretStr; eval_key: SecretStr | None = None; cookie_secure: bool = False;
    # trust_proxy_headers: bool = False; data_dir: Path; index_dir: Path; web_dist_dir: Path; require_frontend: bool
    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Settings: ...   # never reads os.environ itself
```

**Checked 2026-10-21 against AEA-02's frozen tests (`de9bb42`):** `tests/unit/test_config.py` imports `ENV_NAMES`,
`Settings`, `SettingsError`, `ModelSettings`, `default_model_settings`, `JEV_MODEL`, `SONNET_MODEL` from `meridian.config`
and `Role` from `meridian.ports.models`; `ENV_NAMES` holds 17 names including `MERIDIAN_EVAL_KEY`,
`MERIDIAN_COOKIE_SECURE`, `MERIDIAN_TRUST_PROXY_HEADERS`, `MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`,
`MERIDIAN_SESSION_SECRET` (and none naming a clock, which AC-35 relies on). `tests/unit/domain/test_conventions.py`
imports `DemoRole`, `IssuedSession`, `LoginSession`, `LoginSessionId` from `meridian.domain.staff` and `MeridianModel` from
`meridian.domain.common`. The branch's `domain/common.py` already defines `ThreadId`, `RequestId` (UUID4 pattern) and
`ApiErrorCode`. `Settings` also has `models`, four `langfuse_*` fields, `issued_db_path` and `agent_version`, all
defaulted; `make_settings` need not set them. `ChoiceRole`, `StructuredRole`, `ToolRole` live in `meridian.ports.models`
(AEA-02 plan §4.12).

If AEA-02 lands any of these under a different name or module, **stop and report** (do not alias or redefine).

### 4.3 Signatures this ticket creates (copied from web.md; additions marked **[plan]**)

```python
# web/errors.py (web §1)
class ApiProblem(Exception):
    def __init__(self, status: int, code: ApiErrorCode, *, field: str | None = None,
                 constraint: str | None = None, details: dict[str, object] | None = None,
                 headers: Mapping[str, str] | None = None) -> None: ...
    # attributes: status, code, field, constraint, details, headers (dict, {} when None); str(self) == f"{status} {code}"
def render_api_problem(problem: ApiProblem, request_id: str) -> JSONResponse: ...          # [plan] THE renderer
async def handle_api_problem(request: Request, exc: Exception) -> Response: ...             # [plan]
async def handle_validation_error(request: Request, exc: Exception) -> Response: ...        # [plan] 422 → 400
def render_unhandled_error(request_id: str) -> JSONResponse: ...                            # [plan] 500, {"request_id"}

# services/reset_gate.py (web §7)
class ResetAlreadyRunning(Exception): ...
class ResetGate:
    def held(self) -> bool: ...
    def hold(self) -> ContextManager[None]: ...            # raises ResetAlreadyRunning on enter when already held
    async def wait_clear(self, timeout_s: float) -> bool: ...

# web/middleware.py (web §4–§6)
EVAL_KEY_HEADER = "X-Meridian-Eval-Key"; RUN_ID_HEADER = "X-Meridian-Run-Id"; RUN_TAG_HEADER = "X-Meridian-Run-Tag"
class LimitScope(StrEnum): THREAD = "thread"; SESSION = "session"; IP = "ip"; LOGIN_IP = "login_ip"; RESET_IP = "reset_ip"
@dataclass(frozen=True)
class LimitVerdict: allowed: bool; scope: LimitScope | None; retry_after_ms: int | None
class RateLimiter:
    def __init__(self, limits: WebLimits) -> None: ...
    def check(self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read") -> LimitVerdict: ...
    def peek(self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read") -> LimitVerdict: ...
    def record_login_reject(self, ip: str, now: float) -> None: ...
    def record_reset(self, ip: str, now: float) -> None: ...
    def bucket_keys(self) -> frozenset[tuple[str, str, str]]: ...      # [plan] (family, scope, key), for AC-14
    # `family` is [plan]: SESSION and IP each have a turn limit and a read limit (web §5 table); default "read".
@dataclass(frozen=True)
class RequestContext:
    request_id: RequestId; client_ip: str; session: LoginSession | None
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; turn_verdict: LimitVerdict | None
class PublicPaths:
    def add_exact(self, method: str, path: str) -> None: ...
    def add_prefix(self, method: str, prefix: str) -> None: ...
    def is_public(self, method: str, path: str) -> bool: ...
    def entries(self) -> frozenset[tuple[str, str, str]]: ...         # [plan] ("exact"|"prefix", METHOD, path)
@dataclass(frozen=True)
class WebShellState:                                                   # [plan] app.state.web_shell, set by create_app
    settings: Settings; wall_clock: Callable[[], datetime]; public_paths: PublicPaths
@dataclass(frozen=True)
class GateBindings:                                                    # [plan] how the middleware reaches deps
    login_sessions: Callable[[Starlette], LoginSessions]; rate_limiter: Callable[[Starlette], RateLimiter]
    reset_gate: Callable[[Starlette], ResetGate]; wall_clock: Callable[[Starlette], Callable[[], datetime]]
class GateMiddleware:                                                  # pure ASGI; added in create_app
    def __init__(self, app: ASGIApp, *, bindings: GateBindings) -> None: ...
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None: ...
SESSION_COOKIE = "mhc_session"
def session_cookie(token: str, *, max_age: int, secure: bool) -> str: ...        # [plan] Set-Cookie value
def cleared_session_cookie(*, secure: bool) -> str: ...                          # [plan] Max-Age=0
def safe_return_to(target: str) -> str | None: ...                               # [plan] WEB-28
def client_ip_of(scope: Scope, *, trust_proxy_headers: bool) -> str: ...         # [plan]
def run_tag_of(headers: Headers, eval_key: SecretStr | None) -> tuple[Literal["live", "eval", "load"], str | None]: ...  # [plan]
OPERATIONS_BY_ROUTE: Mapping[tuple[str, str], str]                   # [plan] (METHOD, OpenAPI path) → operationId, 30 rows
RATE_LIMITED_READ_OPERATIONS: frozenset[str]; RESET_503_OPERATIONS: frozenset[str]
RESET_NO_WAIT_OPERATIONS: frozenset[str]; SUBMIT_TURN_OPERATION = "submitTurn"; HEALTHZ_PATH = "/healthz"

# web/deps.py (web §2–§4)
class LoginSessions(Protocol):
    def start(self, now: datetime) -> IssuedSession: ...
    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired: ...
    def end(self, token: SecretStr) -> None: ...
    def session_info(self, session: LoginSession) -> SessionInfoData: ...
class StaffAccess(Protocol):
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal: ...
class MetricsReads(Protocol):
    def owner_metrics(self) -> Mapping[str, object]: ...
    def monitoring(self) -> Mapping[str, object]: ...
    def latest_eval(self) -> Mapping[str, object]: ...
class HeartbeatReader(Protocol):                                      # [plan] cases §8 Heartbeat satisfies it
    def fresh(self, mono: float) -> bool: ...
def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]: ...
def owned_thread(thread_id: str, session: LoginSession = Depends(get_login_session),
                 uow: UnitOfWorkFactory = Depends(get_uow_factory)) -> ThreadId: ...
def owned_stream_thread(thread_id: str, session: LoginSession = Depends(get_login_session),
                        uow: UnitOfWorkFactory = Depends(get_uow_factory)) -> ThreadId: ...
def provided[T](app: Starlette, provider: Callable[..., T]) -> T: ...   # [plan] honours app.dependency_overrides
def wall_now(app: Starlette) -> datetime: ...                           # [plan] provided(app, get_wall_clock)()
# providers: every one takes (request: Request) — see §5 step 5 for the full list and container keys

# web/app.py (web §15)
@dataclass(frozen=True)
class ContainerOverrides:
    choice: Mapping[ChoiceRole, ChoiceModel] | None = None
    structured: Mapping[StructuredRole, StructuredModel] | None = None
    tools: Mapping[ToolRole, ToolCallingModel] | None = None
    trace: TraceSink | None = None
    wall_clock: Callable[[], datetime] | None = None
def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> FastAPI: ...

# tests/api/openapi_check.py (web §13)
@dataclass(frozen=True)
class OperationSpec:
    operation_id: str; method: Literal["get", "post", "put", "patch", "delete"]; path_template: str
    responses: Mapping[str, Mapping[str, JsonValue]]     # status → {content type → schema object}; {} when no content
    event_schema: str | None                             # "ChatEvent" / "CaseEvent" for the two SSE operations
@dataclass(frozen=True)
class Contract:
    source: Path; version: str; operations: Mapping[str, OperationSpec]; error_codes: frozenset[str]
    registry: referencing.Registry
@dataclass(frozen=True)
class SseFrame: event: str | None; id: str | None; data: str                     # [plan]
class ContractLoader(yaml.SafeLoader): ...
def load_document() -> Mapping[str, Any]: ...                                     # [plan] the raw OpenAPI, cached
def load_contract() -> Contract: ...                                              # cached per test session
def assert_response_matches(response: httpx.Response, operation_id: str) -> None: ...
def assert_sse_frames_match(frames: Sequence[SseFrame], operation_id: str) -> None: ...
def operations_documenting(status: str) -> frozenset[str]: ...
def operations_documenting_code(status: str, code: str) -> frozenset[str]: ...    # [plan] for the 503 set
```

### 4.4 Wire shapes (OpenAPI, read verbatim)

- `ApiError`: `{"error": {"code": <enum>, "field": str|null, "constraint": str|null, "details": object|null}, "request_id": str}`; all four `error` keys required.
- `LoginRequest`: `{username: string, password: string}`, both required, no `minLength`, extra keys not forbidden.
- `LoginResponse`: `{session: SessionInfo, landing: string}`; `SessionInfo`: `{authenticated: const true, role, display_name, sees: string[], signed_in_at: date-time}`.
- `login` responses: 200 (`Set-Cookie`, `X-Request-ID`), 400 `ValidationError`, 401 `LoginFailed`, 429 `LoginRateLimited` (header `Retry-After: integer`). `security: []`.
- `logout` responses: 204 (`X-Request-ID`, no body), 401 `Unauthenticated`.
- `Unauthenticated.details`: `{reason: "none" | "expired"}`; `RoleNotAllowed.details`: `{role, needs, reason}`; `TooManyRequests` / `ResetInProgress` / `LoginRateLimited` details: `{retry_after_ms}`; `SessionEnded.details`: `{reason}`; `SessionNotFound.details`: null.
- No operation documents a generic 500; `/healthz` is not in the OpenAPI.

---

## 5. Steps (build order; each ends with a check)

**Before step 1:** confirm AEA-02 is on main (`ls src/meridian/domain/staff.py src/meridian/config.py`). The test-writer's
frozen tests are already committed on the branch; run `uv run pytest --collect-only -q tests/api tests/unit/web` and
expect import errors only for the modules this ticket creates. `export UV_LINK_MODE=hardlink` in every shell.

**Module rules for every file:** first line after the docstring `from __future__ import annotations`; absolute imports;
**no module-level lower-case assignment that calls something** (AC-23 grep `^[a-z_]* = .*(`): constants are
UPPER_CASE (`MappingProxyType`, `frozenset`, `Key[...]`, strings); loggers are fetched with
`logging.getLogger(<CONSTANT>)` inside functions; routers are built inside `build_router()`. Use `import hmac` and call
`hmac.compare_digest(...)` (never `from hmac import compare_digest`; the AC-5 spy patches the module attribute). Never
put a secret, cookie value, eval key, request body, username or password in an exception message or log call.
Interfaces implemented here: `LoginSessions`, `StaffAccess`, `MetricsReads`, `HeartbeatReader` are **consumed**
(declared here, implemented by AEA-44, AEA-53, AEA-32); `UnitOfWorkFactory` is consumed (AEA-02 port, AEA-10
implementation). Dependency direction: `web/app.py` → `web/middleware.py`, `web/deps.py`, `web/errors.py`,
`web/logging.py`, `web/routes/auth.py`; `web/deps.py` → `web/middleware.py` (types), `services/reset_gate.py`,
`web/errors.py`; `web/middleware.py` → `web/errors.py`, `web/logging.py`, `services/reset_gate.py` and `web/deps.py`
**only under `TYPE_CHECKING`** (no import cycle); `services/reset_gate.py` imports only stdlib and `anyio` (never `web/`).

### Step 1 — `src/meridian/services/reset_gate.py`

```python
WAIT_POLL_S = 0.1          # [A] web §7 "anyio.sleep(0.1) loop"
class ResetAlreadyRunning(Exception): ...
class ResetGate:
    def __init__(self) -> None: self._lock = threading.Lock()
    def held(self) -> bool: return self._lock.locked()
    @contextmanager
    def hold(self) -> Iterator[None]:
        if not self._lock.acquire(blocking=False): raise ResetAlreadyRunning("a reset is already running")
        try: yield
        finally: self._lock.release()
    async def wait_clear(self, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        while self.held():
            if time.monotonic() >= deadline: return False
            await anyio.sleep(WAIT_POLL_S)
        return True
```
Invariants: `held()` never blocks (the middleware calls it on the event loop on every request); a second concurrent
`hold()` raises at `with` entry, so CON-9 answers 409 instead of running twice; `wait_clear` never uses a worker thread.
Check: `uv run pytest -q tests/unit/web/test_reset_gate.py -k double_hold`.

### Step 2 — `src/meridian/web/errors.py`

1. `ApiProblem` exactly as §4.3; store `self.headers = dict(headers or {})`; `super().__init__(f"{status} {code}")`.
2. `render_api_problem(problem, request_id)` — **the only place in `src/meridian/web/` that builds an `ApiError` body**
   (AC-9 counts string constants `"constraint"`: exactly one, here):
   `JSONResponse({"error": {"code": problem.code.value, "field": problem.field, "constraint": problem.constraint,
   "details": dict(problem.details) if problem.details is not None else None}, "request_id": request_id},
   status_code=problem.status, headers={**problem.headers, "X-Request-ID": request_id})`.
3. `async def handle_api_problem(request, exc)`: `assert isinstance(exc, ApiProblem)`; `request_id =
   getattr(request.state, "request_id", None) or str(uuid.uuid4())`; if `exc.status >= 500`:
   `request.state.error_kind = exc.code.value`; return `render_api_problem(exc, request_id)`.
4. `async def handle_validation_error(request, exc)`: `assert isinstance(exc, RequestValidationError)`; take
   `first = exc.errors()[0]` and read **only** `first["loc"]`, `first["type"]`, `first["msg"]` (never `input`, never
   `ctx`). Field rule: `loc = tuple(first["loc"])`; `rest = loc[1:] if loc and loc[0] in ("body", "query", "path",
   "header", "cookie") else loc`; if `first["type"] == "json_invalid"` or `rest` is empty or `rest[0]` is an `int`:
   `field = loc[0] if loc else "body"` (so a non-JSON or non-object body names `"body"`); else
   `field = ".".join(str(part) for part in rest)`. `constraint = str(first["msg"])`. Build
   `ApiProblem(400, ApiErrorCode.VALIDATION_ERROR, field=field, constraint=constraint, details=None)` and return
   `await handle_api_problem(request, problem)`. Never log `exc`.
5. `render_unhandled_error(request_id) -> JSONResponse({"request_id": request_id}, status_code=500,
   headers={"X-Request-ID": request_id})` (decision D-P1, §8: no generic code exists in the signed enum, so none is
   invented; `apps/web/src/api/client.ts` maps a body without `error` to `HTTP_500` and reads `request_id`).

Invariants: one renderer; `details` never carries a rejected value; handlers are `async def` (no worker thread).
Check: `uv run mypy src/meridian/web/errors.py`.

### Step 3 — `src/meridian/web/logging.py` (web §10; WEB-11)

```python
REQUEST_LOGGER = "meridian.web.request"; AUTH_LOGGER = "meridian.web.auth"
STREAM_LOGGER = "meridian.web.stream"      # AEA-41 emits stream_reconnect through emit_record(STREAM_LOGGER, …)
SIGNAL_LOGGER = "meridian.signal"          # AEA-21 emits with extra={"signal": record.model_dump(mode="json")}
RECORD_ATTR = "meridian_record"; ROOT_LOGGER = "meridian"; HANDLER_NAME = "meridian-allow-list"
ALLOWED_FIELDS: Mapping[str, frozenset[str]] = MappingProxyType({
    "request": frozenset({"record", "request_id", "route", "status", "duration_ms", "caller_role", "thread_id",
                          "error_kind"}),
    "auth_event": frozenset({"record", "request_id", "outcome", "session_id", "at"}),
    "stream_reconnect": frozenset({"record", "request_id", "thread_id", "case_ref", "last_event_id", "replayed"}),
    "signal": frozenset({"record", "name", "turn_id", "thread_id", "request_id", "run_tag", "node", "cause", "role",
                         "specialist", "attempt", "recovered"}),
})
def emit_record(logger_name: str, fields: Mapping[str, object]) -> None:
    # logging.getLogger(logger_name).info(str(fields["record"]), extra={RECORD_ATTR: dict(fields)})
def request_record(*, request_id: str, route: str, status: int, duration_ms: int, caller_role: str,
                   thread_id: str | None, error_kind: str | None) -> dict[str, object]:
    # {"record": "request", ...}; include "error_kind" ONLY when status >= 500 (DO-6 Status values)
def auth_event(*, request_id: str, outcome: Literal["ok", "rejected", "rate_limited", "logged_out"],
               session_id: str | None, at: datetime) -> dict[str, object]:
    # {"record": "auth_event", "request_id", "outcome", "session_id", "at": at.astimezone(UTC).isoformat()}
class AllowListFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str: ...
def install_log_formatter() -> None: ...
```
`AllowListFormatter.format`:
1. `payload = record.__dict__.get(RECORD_ATTR)`; if not a `Mapping`, `payload = record.__dict__.get("signal")`.
2. If `payload` is a `Mapping` and `payload.get("record") in ALLOWED_FIELDS` (for the `signal` attribute, kind is
   `payload.get("record", "signal")`): `out = {k: payload[k] for k in sorted(ALLOWED_FIELDS[kind]) if k in payload and
   isinstance(payload[k], (str, int, float, bool, type(None)))}`.
3. Otherwise (unstructured line or unknown kind) apply the LOG profile: `out = {"record": "log", "logger": record.name,
   "level": record.levelname, "length": redact(record.getMessage(), RedactionProfile.LOG).length}`; if
   `record.exc_info` and `record.exc_info[0]`: `out["exc_type"] = record.exc_info[0].__name__` (never the traceback).
4. `return json.dumps(out, sort_keys=True, separators=(",", ":"))`.
Invariant: only allow-listed keys with scalar values leave the process; free text is reduced to its length.

`install_log_formatter()`: `logger = logging.getLogger(ROOT_LOGGER)`; if any handler has `name == HANDLER_NAME`,
return; else add `logging.StreamHandler()` named `HANDLER_NAME` with `AllowListFormatter()`; `logger.setLevel(logging.INFO)`.
Keep `propagate` True (pytest's `caplog` then sees the message, which is only the record kind).
Check: `uv run pytest -q tests/unit/web/test_logging.py`.

### Step 4 — `src/meridian/web/middleware.py`, part A (constants, limiter, context types, helpers)

1. Header constants (§4.3), `SESSION_COOKIE = "mhc_session"`, `HEALTHZ_PATH = "/healthz"`,
   `SUBMIT_TURN_OPERATION = "submitTurn"`, `UNMATCHED_ROUTE = "<unmatched>"`.
2. `OPERATIONS_BY_ROUTE = MappingProxyType({...})` — exactly these 30 rows, `(METHOD, path) → operationId`:
   `("POST","/api/chat/sessions")→startChatSession`, `("GET","/api/chat/sessions/{thread_id}")→getChatThread`,
   `("POST","/api/chat/sessions/{thread_id}/turns")→submitTurn`, `("GET","/api/chat/sessions/{thread_id}/events")→streamChatEvents`,
   `("POST","/api/chat/sessions/{thread_id}/handoff")→requestPerson`, `("PUT","/api/chat/sessions/{thread_id}/follow-up")→saveFollowUp`,
   `("GET","/api/demo/inbox")→listDemoInbox`, `("GET","/api/demo/staffing")→getStaffing`, `("PUT","/api/demo/staffing")→setStaffing`,
   `("GET","/api/demo/clock")→getDemoClock`, `("POST","/api/demo/clock")→advanceDemoClock`, `("POST","/api/demo/reset")→resetDemo`,
   `("GET","/api/staff/queue")→getQueue`, `("GET","/api/staff/cases/{reference}")→getCase`,
   `("POST","/api/staff/cases/{reference}/actions")→applyCaseAction`, `("POST","/api/staff/cases/{reference}/live")→liveChatAction`,
   `("GET","/api/staff/cases/{reference}/events")→streamCaseEvents`, `("POST","/api/staff/cases/{reference}/activities")→recordContactActivity`,
   `("POST","/api/staff/flags")→createFlag`, `("GET","/api/staff/flags")→listFlags`, `("PATCH","/api/staff/flags/{flag_id}")→reviewFlag`,
   `("GET","/api/staff/oversight")→getOversight`, `("GET","/api/staff/owner-metrics")→getOwnerMetrics`,
   `("GET","/api/monitoring")→getMonitoring`, `("GET","/api/eval/latest")→getLatestEval`, `("POST","/api/login")→login`,
   `("POST","/api/logout")→logout`, `("GET","/api/session")→getSession`, `("GET","/api/session/roles")→listDemoRoles`,
   `("PUT","/api/session/role")→switchRole`.
3. Sets (frozensets):
   `RATE_LIMITED_READ_OPERATIONS = {startChatSession, listDemoInbox, getStaffing, getDemoClock, getMonitoring, getLatestEval}`;
   `RESET_503_OPERATIONS = {startChatSession, submitTurn, listDemoInbox, setStaffing, advanceDemoClock, switchRole, getMonitoring, getLatestEval}`;
   `RESET_NO_WAIT_OPERATIONS = {login, resetDemo, streamChatEvents, streamCaseEvents}` (`resetDemo` answers its own
   409 `RESET_IN_PROGRESS` through `ResetAlreadyRunning`; making it wait would run a second reset instead).
4. `LimitScope`, `LimitVerdict` as §4.3. `ALLOWED = LimitVerdict(allowed=True, scope=None, retry_after_ms=None)` (a
   frozen constant is fine).
5. `RateLimiter(limits)` — numbered algorithm:
   1. State: `self._lock = threading.Lock()` (the middleware runs on the loop, the login route in a worker thread);
      `self._buckets: dict[tuple[str, str, str], list[float]]` holding `[tokens, last_ts]` for token buckets;
      `self._logs: dict[tuple[str, str], collections.deque[float]]` for the LOGIN_IP and RESET_IP windows;
      `self._last_sweep = 0.0`.
   2. Capacity per minute: `(turn, THREAD) → chat_turns_per_thread_per_min` (THREAD always uses the turn limit,
      whatever `family`), `(turn, SESSION) → chat_turns_per_session_per_min`, `(turn, IP) → chat_turns_per_ip_per_min`,
      `(read, SESSION) → reads_per_session_per_min`, `(read, IP) → reads_per_ip_per_min`. Refill rate = capacity / 60
      tokens per second; a new bucket starts full.
   3. `peek(scope, key, now, *, family)`: for THREAD/SESSION/IP refill (`tokens = min(cap, tokens + (now - last) *
      rate)`, without storing for peek); allowed when `tokens >= 1`; else `retry_after_ms = max(1, ceil((1 - tokens) /
      rate)) * 1000`. For LOGIN_IP: drop log entries `<= now - login_reject_window_s`; allowed when `len(log) <
      login_rejects_per_ip`; else `retry_after_ms = max(1, ceil(log[0] + window - now)) * 1000`. RESET_IP: the same with
      `resets_per_ip` / `reset_window_s`. Returns `LimitVerdict(False, scope, retry_after_ms)` when refused.
   4. `check(...)`: `peek`; when allowed, consume (`tokens -= 1` and store `[tokens, now]`; for a window scope append
      `now`). Returns the verdict.
   5. `record_login_reject(ip, now)`: append `now` to the LOGIN_IP log of `ip` (deque `maxlen=login_rejects_per_ip`).
      `record_reset(ip, now)`: same for RESET_IP with `maxlen=resets_per_ip`.
   6. Eviction: at the start of every public method, when `now - self._last_sweep >= 60`, drop token buckets idle for
      more than 120 s (2 × 60 s window) and window logs whose newest entry is older than 2 × their window; set
      `_last_sweep = now`.
   7. `bucket_keys()`: `frozenset(self._buckets) | frozenset(("window", s, k) for (s, k) in self._logs)`.
   Invariants: keys are a thread id, a session id or a client IP, never a cookie value; memory is bounded by recent
   callers; a refused peek consumes nothing.
6. `PublicPaths`: a `set[tuple[str, str, str]]` of `("exact"|"prefix", METHOD.upper(), path)`; `is_public(method,
   path)` = exact match, or a prefix entry whose method matches and `path.startswith(prefix)`. Adding the same entry
   twice is harmless (set).
7. `RequestContext`, `WebShellState`, `GateBindings` as §4.3 (frozen dataclasses). `LoginSessions` is typed via
   `if TYPE_CHECKING: from meridian.web.deps import LoginSessions`.
8. Cookie helpers (exact strings; Starlette's `set_cookie` would write `SameSite=lax`, so build the header by hand):
   `session_cookie(token, *, max_age, secure)` → `f"mhc_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"`
   plus `"; Secure"` when `secure`; `cleared_session_cookie(*, secure)` → the same with an empty value and `Max-Age=0`.
9. `safe_return_to(target)`: return `target` only when it starts with `/`, does not start with `//` or `/\`, and
   contains no `\`, no control character (`ord < 0x20` or `0x7f`) and no `://`; else `None`.
   `//evil.example`, `https://evil.example/x`, `evil` → `None`; `/staff/queue` → `/staff/queue`.
10. `client_ip_of(scope, *, trust_proxy_headers)`: when trusted and an `x-forwarded-for` header is present, the last
    comma-separated entry, stripped, if non-empty; else `scope["client"][0]` if `scope.get("client")` else `"unknown"`.
    [A: confirm Railway's header at AEA-56]
11. `run_tag_of(headers, eval_key)`: `supplied = headers.get(EVAL_KEY_HEADER)`; if `supplied is None or eval_key is
    None` → `("live", None)` **without calling `compare_digest`**; `match = hmac.compare_digest(supplied.encode("utf-8"),
    eval_key.get_secret_value().encode("utf-8"))`; not matched → `("live", None)`; matched → tag =
    `headers.get(RUN_TAG_HEADER)` if it is `"eval"` or `"load"` else `"eval"`; `run_id = headers.get(RUN_ID_HEADER)`.
12. `limit_verdict(limiter, operation_id, *, thread_id, session_id, ip, now) -> LimitVerdict | None` **[plan, pure,
    unit-tested]**: for an op in `RATE_LIMITED_READ_OPERATIONS`: peek `(SESSION, session_id, read)` then `(IP, ip,
    read)`; first refusal is returned; if none, `check` both and return `ALLOWED`. For `submitTurn`: peek `(THREAD,
    thread_id, turn)`, `(SESSION, session_id, turn)`, `(IP, ip, turn)` in that order; first refusal returned; else check
    all three, return `ALLOWED`. Any other op → `None` (never limited).
Check: `uv run pytest -q tests/unit/web/test_middleware.py -k "limits_admit or client_ip"` (after step 6 for the HTTP
sub-cases).

### Step 5 — `src/meridian/web/deps.py`

1. Protocols `LoginSessions`, `StaffAccess`, `MetricsReads`, `HeartbeatReader` exactly as §4.3.
2. Container keys (names are binding; other tickets `container.provide(<KEY>, …)` with them; AEA-10 already plans
   `uow_factory`):

   | Key constant | `Key[...]` name | Provider | Bound by |
   |---|---|---|---|
   | `LOGIN_SESSIONS` | `login_sessions` | `get_login_sessions` | AEA-44 |
   | `STAFF_ACCESS` | `staff_access` | `get_staff_access` | AEA-44 (same instance) |
   | `FLAG_SERVICE` | `flag_service` | `get_flag_service` | AEA-44 |
   | `SESSION_SERVICE` | `session_service` | `get_session_service` | AEA-40 |
   | `TURN_SERVICE` | `turn_service` | `get_turn_service` | AEA-40 |
   | `PERSON_REQUESTS` | `person_requests` | `get_person_requests` | AEA-42 |
   | `HANDOFF_SERVICE` | `handoff_service` | `get_handoff_service` | AEA-29 |
   | `CASE_SERVICE` | `case_service` | `get_case_service` | AEA-29 |
   | `REPLY_COMPOSER` | `reply_composer` | `get_reply_composer` | AEA-21 / AEA-51 |
   | `IDENTITY_SERVICE` | `identity_service` | `get_identity_service` | AEA-27 |
   | `DEMO_SERVICE` | `demo_service` | `get_demo_service` | AEA-30 |
   | `RESET_SERVICE` | `reset_service` | `get_reset_service` | AEA-31 |
   | `RESET_GATE` | `reset_gate` | `get_reset_gate` | **AEA-23** (register_web) |
   | `LIVE_CHAT` | `live_chat` | `get_live_chat` | AEA-46 |
   | `METRICS_READS` | `metrics_reads` | `get_metrics_reads` | AEA-53 |
   | `UOW_FACTORY` | `uow_factory` | `get_uow_factory` | AEA-10 |
   | `STREAM_POLL_LIMITER` | `stream_poll_limiter` | `get_stream_poll_limiter` | **AEA-23** |
   | `RATE_LIMITER` | `rate_limiter` | `get_rate_limiter` | **AEA-23** |
   | `WALL_CLOCK` | `wall_clock` | `get_wall_clock` | **AEA-23** |
   | `HEARTBEAT` | `heartbeat` | `get_heartbeat` **[plan]** | AEA-32 |

   Typing: keys and providers whose type exists now are precise (`Key[LoginSessions]`, `Key[StaffAccess]`,
   `Key[MetricsReads]`, `Key[HeartbeatReader]`, `Key[ResetGate]`, `Key[UnitOfWorkFactory]`,
   `Key[anyio.CapacityLimiter]`, `Key[RateLimiter]`, `Key[Callable[[], datetime]]`); the services of later tickets are
   `Key[Any]` and their providers return `Any`, each with a docstring naming the DO-4 / addendum type and owner
   (`SessionService` web §14, `TurnService` web §9, `PersonRequestService` web §8, `HandoffService` / `CaseService`
   cases §5, `ReplyComposer` graph-core §13, `IdentityService` graph-tools §5, `DemoService` cases §6, `ResetService`
   cases §7, `LiveChatService` staff §5, `FlagService` staff §2). Do not import those modules (they do not exist).
3. `PROVIDER_KEYS = MappingProxyType({get_login_sessions: LOGIN_SESSIONS, …})` — one entry per row above.
4. `_bound(app, provider)`: `container = getattr(app.state, "container", None)`; if `None` → `raise
   RuntimeError(f"not bound: {provider.__name__}")`; `key = PROVIDER_KEYS[provider]`; `try: return container.get(key)`
   `except ContainerError as exc:` if `str(exc) == f"not provided: {key.name}"` → `raise RuntimeError(f"not bound:
   {provider.__name__}") from None`; else re-raise. Invariant: an unbound provider fails at call time, never at import.
5. `provided(app, provider)`: `override = app.dependency_overrides.get(provider)` (use `getattr(app,
   "dependency_overrides", {})`); if `override is not None` → `return cast(T, override())` (overrides used by the
   middleware are zero-argument callables; document this in the docstring); else `return provider_value` via
   `_bound(app, provider)`. `wall_now(app) = provided(app, get_wall_clock)()`.
6. Providers — each `def get_x(request: Request) -> X: return _bound(request.app, get_x)` (FastAPI injects `request`;
   overrides by `app.dependency_overrides[get_x] = lambda: double` work for routes): `get_login_sessions`,
   `get_staff_access`, `get_flag_service`, `get_session_service`, `get_turn_service`, `get_person_requests`,
   `get_handoff_service`, `get_case_service`, `get_reply_composer`, `get_identity_service`, `get_demo_service`,
   `get_reset_service`, `get_reset_gate`, `get_live_chat`, `get_metrics_reads`, `get_uow_factory`,
   `get_stream_poll_limiter`, `get_rate_limiter`, `get_wall_clock`, `get_heartbeat`. Plus:
   - `get_request_context(request) -> RequestContext`: `ctx = getattr(request.state, "request_context", None)`; if not a
     `RequestContext` → `RuntimeError("request context missing: GateMiddleware not installed")`.
   - `get_login_session(ctx = Depends(get_request_context)) -> LoginSession`: `ctx.session`; if `None` → `raise
     ApiProblem(401, ApiErrorCode.UNAUTHENTICATED, details={"reason": "none"})` (defence: a public route asking for it).
   - `get_settings(request) -> Settings` **[plan]**: `request.app.state.web_shell.settings`.
7. `require_staff(*roles)`: `needs = tuple(roles)`; inner `def dependency(session: LoginSession =
   Depends(get_login_session), access: StaffAccess = Depends(get_staff_access)) -> StaffActor`: `result =
   access.actor_for(session, needs)`; if `isinstance(result, RoleRefusal)`: `raise ApiProblem(403,
   ApiErrorCode.ROLE_NOT_ALLOWED, details={"role": result.role.value, "needs": [r.value for r in result.needs],
   "reason": result.reason})`; else return `result`. Set `dependency.__name__ = "require_staff_" + "_".join(r.value for
   r in needs)`. Invariant: the role comes from this request's resolved session (no caching across requests; FastAPI's
   per-request cache only).
8. `owned_thread` / `owned_stream_thread` both call `_owned(thread_id, session, uow, ended_as_404: bool)`:
   1. If `re.fullmatch(ThreadId.PATTERN, thread_id)` is `None` → `_not_found()` (no lookup).
   2. `with uow() as tx: found = cast(_CoreWithConversations, tx.core).conversations.lookup(thread_id)` — one
      read-only unit of work, **one** lookup. Local Protocols (so this file type-checks before AEA-10 lands):
      `class _ConversationsLookup(Protocol): def lookup(self, thread_id: str) -> object: ...`;
      `class _CoreWithConversations(Protocol): conversations: _ConversationsLookup`;
      `@runtime_checkable class _EndedThreadLike(Protocol): demo_session: str; reason: str`;
      `@runtime_checkable class _ConversationLike(Protocol): demo_session: str`.
   3. `mine = str(session.session_id)`. If `isinstance(found, _EndedThreadLike)` (check this **first**; a
      `ConversationRow` has no `reason`): when `found.demo_session == mine` and not `ended_as_404` → `raise
      ApiProblem(410, ApiErrorCode.SESSION_ENDED, details={"reason": found.reason})`; otherwise `_not_found()`.
   4. Elif `isinstance(found, _ConversationLike)` and `found.demo_session == mine` → `return ThreadId(thread_id)`.
   5. Else `_not_found()` = `raise ApiProblem(404, ApiErrorCode.SESSION_NOT_FOUND)` (field, constraint, details all
      `None`, so all 404 bodies are byte-identical apart from `request_id`).
   Do **not** import `EndedThread` or `ConversationRow` from `adapters/` (DO-3: web does not import adapters; AEA-10 is a
   same-wave sibling).
Check: `uv run mypy src/meridian/web/deps.py && uv run pytest -q tests/unit/web/test_deps.py` (after steps 6–9).

### Step 6 — `src/meridian/web/middleware.py`, part B: `GateMiddleware`

`__call__(scope, receive, send)` — numbered; each step's invariant in italics:

0. If `scope["type"] != "http"` → `await self.app(scope, receive, send)`; return. `app = scope["app"]`;
   `shell: WebShellState = app.state.web_shell`; `state = scope.setdefault("state", {})`; `start = time.perf_counter()`.
1. `request_id = str(uuid.uuid4())`; `state["request_id"] = request_id`. Wrap `send` as `send_wrapper`: on
   `http.response.start` record `status`, set `MutableHeaders(scope=message)["X-Request-ID"] = request_id`, append any
   pending `set-cookie` value (the expired-session clear), mark `started = True`. *Every response, errors included,
   carries exactly one `X-Request-ID`.*
2. Pre-match the route (no side effects): iterate `app.router.routes`; `match, child = route.matches(scope)`; first
   `Match.FULL` wins (else the first `Match.PARTIAL`): `template = getattr(route, "path", UNMATCHED_ROUTE)`,
   `path_params = child.get("path_params", {})`. `operation_id = OPERATIONS_BY_ROUTE.get((scope["method"], template))`.
   `thread_id = path_params.get("thread_id")` kept only if `re.fullmatch(ThreadId.PATTERN, …)`. *The log never sees the
   raw path; an unknown route is never classified.*
3. Reset gate: `gate = self._b.reset_gate(app)`; if `gate.held()`:
   if `operation_id in RESET_503_OPERATIONS` → respond `ApiProblem(503, RESET_IN_PROGRESS, details={"retry_after_ms":
   5000})` at once (set `error_kind = "RESET_IN_PROGRESS"`); elif `operation_id in RESET_NO_WAIT_OPERATIONS` or
   `scope["path"] == HEALTHZ_PATH` → continue; else `await gate.wait_clear(app.state.container.limits.web.reset_wait_s)`
   and continue whatever it returns (SQLite's `busy_timeout` is the second wait, web §7). *`/healthz`, `login`,
   `resetDemo` and the streams never wait.*
4. Session: `method = scope["method"]`, `path = scope["path"]`. If `shell.public_paths.is_public(method, path)` →
   `session = None` and take **no** wall-clock reading. Else: `now = self._b.wall_clock(app)()` (**the only wall-clock
   reading in the middleware for this request; reused in step 5**); `token = Request(scope).cookies.get(SESSION_COOKIE,
   "")`; `result = self._b.login_sessions(app).resolve(SecretStr(token), now)`:
   - `SessionMissing` → reason `"none"`; `SessionExpired` → reason `"expired"` and a pending
     `cleared_session_cookie(secure=shell.settings.cookie_secure)` header;
   - for either: if `path == "/api" or path.startswith("/api/")` or `method != "GET"` → respond `ApiProblem(401,
     UNAUTHENTICATED, details={"reason": reason})`; else (a page GET) → respond `RedirectResponse(location,
     status_code=303)` where `target = path + ("?" + scope["query_string"].decode("latin-1") if
     scope["query_string"] else "")`, `safe = safe_return_to(target)`, `location = "/login?" + urlencode({"return_to":
     safe, "reason": reason} if safe else {"reason": reason}, quote_via=quote)`;
   - `LoginSession` → `session = result`.
   *Nothing but the public paths runs without a session; the cookie value is only passed to `resolve` inside a
   `SecretStr`.*
5. Rate limits (only when `session` is not None and `operation_id` is not None): `ip = client_ip_of(scope,
   trust_proxy_headers=shell.settings.trust_proxy_headers)`; `verdict = limit_verdict(self._b.rate_limiter(app),
   operation_id, thread_id=path_params.get("thread_id", ""), session_id=str(session.session_id), ip=ip,
   now=now.timestamp())`. If `operation_id in RATE_LIMITED_READ_OPERATIONS` and the verdict is refused → respond
   `ApiProblem(429, REQUEST_RATE_LIMITED, details={"retry_after_ms": verdict.retry_after_ms})`. For `submitTurn` keep
   the verdict (allowed or not) as `turn_verdict`; **never** answer 429 for it. *`requestPerson` and every other op are
   never limited.* (For public paths compute `ip` the same way for the context.)
6. Eval tag: `run_tag, run_id = run_tag_of(Headers(scope=scope), shell.settings.eval_key)`.
7. `state["request_context"] = RequestContext(request_id=RequestId(request_id), client_ip=ip, session=session,
   run_tag=run_tag, run_id=run_id, turn_verdict=turn_verdict if operation_id == SUBMIT_TURN_OPERATION else None)`.
8. Route: `try: await self.app(scope, receive, send_wrapper)` `except Exception as exc:` `error_kind =
   type(exc).__name__`; if `started` → re-raise (cannot send a second response); else send
   `render_unhandled_error(request_id)` through `send_wrapper` and do not re-raise. *An unhandled error still answers
   with `X-Request-ID` and is counted as a 5xx.*
9. `finally:` emit `request_record(request_id=request_id, route=template, status=status, duration_ms=int((perf_counter()
   - start) * 1000), caller_role=session.role.value if session else "anonymous", thread_id=thread_id,
   error_kind=error_kind or state.get("error_kind") or (f"http_{status}" if status >= 500 else None))` via
   `emit_record(REQUEST_LOGGER, …)`. *One `request` record per call; `error_kind` only on 5xx.*

"Respond" in steps 3–5 means: build the response (`render_api_problem(problem, request_id)` for problems), `await
response(scope, receive, send_wrapper)`, then go to step 9. The middleware calls nothing that needs a worker thread.
Keep `middleware.py` under 600 lines (target ≤ 550; `code-structure.md`).
Check: `uv run pytest -q tests/api/test_gate.py tests/unit/web/test_middleware.py`.

### Step 7 — `src/meridian/web/schemas/auth.py` and `src/meridian/web/routes/auth.py` (CON-22)

`schemas/auth.py`:
```python
class LoginRequest(BaseModel):            # plain BaseModel: MeridianModel strips whitespace, which would change a password
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)
    username: StrictStr
    password: StrictStr
class SessionInfo(MeridianModel):
    authenticated: Literal[True]; role: DemoRole; display_name: str; sees: tuple[str, ...]; signed_in_at: datetime
class LoginResponse(MeridianModel):
    session: SessionInfo; landing: str
```
`routes/auth.py`: `def build_router() -> APIRouter` adds `POST /api/login` (`operation_id="login"`,
`response_model=None`) and `POST /api/logout` (`operation_id="logout"`, `status_code=204`, `response_model=None`). Both
endpoints are sync `def` (AEA-44's real store touches SQLite).

`login(body: LoginRequest, request: Request, ctx: RequestContext = Depends(get_request_context), sessions:
LoginSessions = Depends(get_login_sessions), limiter: RateLimiter = Depends(get_rate_limiter), wall_clock:
Callable[[], datetime] = Depends(get_wall_clock), settings: Settings = Depends(get_settings)) -> Response`:
1. `now = wall_clock()` — **exactly one reading** (AC-34 depends on it); `mono = now.timestamp()`.
2. `verdict = limiter.peek(LimitScope.LOGIN_IP, ctx.client_ip, mono)`; refused → `emit_record(AUTH_LOGGER,
   auth_event(request_id=ctx.request_id, outcome="rate_limited", session_id=None, at=now))`; `raise ApiProblem(429,
   ApiErrorCode.LOGIN_RATE_LIMITED, details={"retry_after_ms": verdict.retry_after_ms}, headers={"Retry-After":
   str(verdict.retry_after_ms // 1000)})`. *While 10 rejects are on record, even the right pair gets 429; a 429 is not
   itself recorded as a reject.*
3. `user_ok = hmac.compare_digest(body.username.encode("utf-8"), settings.demo_username.get_secret_value().encode("utf-8"))`;
   `pass_ok = hmac.compare_digest(body.password.encode("utf-8"), settings.demo_password.get_secret_value().encode("utf-8"))`;
   `ok = user_ok & pass_ok & (body.username != "") & (body.password != "")` (bitwise: **both comparisons always run**).
4. Not ok → `limiter.record_login_reject(ctx.client_ip, mono)`; emit `auth_event(outcome="rejected", session_id=None)`;
   `raise ApiProblem(401, ApiErrorCode.LOGIN_FAILED)`. *One body for every cause.*
5. `old = request.cookies.get(SESSION_COOKIE)`; if `old`: `prior = sessions.resolve(SecretStr(old), now)`; if
   `isinstance(prior, LoginSession)`: `sessions.end(SecretStr(old))`. *A still-valid session is ended before the new
   one starts.*
6. `issued = sessions.start(now)`; `info = sessions.session_info(issued.session)`.
7. `payload = LoginResponse(session=SessionInfo(authenticated=True, role=info.role, display_name=info.display_name,
   sees=info.sees, signed_in_at=info.signed_in_at), landing="/")`; `response = JSONResponse(payload.model_dump(mode="json"))`;
   `response.headers.append("set-cookie", session_cookie(issued.token.get_secret_value(),
   max_age=request.app.state.container.limits.web.login_session_lifetime_s, secure=settings.cookie_secure))` — the only
   place the token is unwrapped.
8. Emit `auth_event(outcome="ok", session_id=str(issued.session.session_id), at=now)`; return `response`.

`logout(request: Request, ctx = Depends(get_request_context), sessions = Depends(get_login_sessions), settings =
Depends(get_settings)) -> Response`: `sessions.end(SecretStr(request.cookies.get(SESSION_COOKIE, "")))`; emit
`auth_event(outcome="logged_out", session_id=str(ctx.session.session_id) if ctx.session else None,
at=wall_now(request.app))`; return `Response(status_code=204)` with `headers.append("set-cookie",
cleared_session_cookie(secure=settings.cookie_secure))`. (Logout passes the gate, so its session exists.)
Check: `uv run pytest -q tests/api/test_auth.py`.

### Step 8 — `src/meridian/web/app.py`

1. `ContainerOverrides` exactly as §4.3 (frozen dataclass, every field `None` by default). Never write the text
   `ContainerOverrides(` anywhere under `src/` — not even in a docstring (AC-30 grep).
2. `def _utc_now() -> datetime: return datetime.now(UTC)` (module-level function, not a lambda).
3. `create_app(settings=None, *, overrides=None)`:
   1. `settings = settings if settings is not None else Settings.from_env(os.environ)`.
   2. `wall_clock = overrides.wall_clock if overrides is not None and overrides.wall_clock is not None else _utc_now`
      (never call it here: a test's fake must see only the reads the app makes).
   3. Inner `@asynccontextmanager async def lifespan(app: FastAPI) -> AsyncIterator[None]`: `container =
      build_container(app, settings, overrides=overrides)`; `app.state.container = container`; `try: yield` `finally:`
      `app.state.container = None` then `container.close()`. `build_container` must be referenced as the module
      global imported at the top (`from meridian.web.container import build_container`) so tests can monkeypatch
      `meridian.web.app.build_container`.
   4. `app = FastAPI(lifespan=lifespan, openapi_url=None, docs_url=None, redoc_url=None)` (no generated schema routes:
      the signed OpenAPI is the contract).
   5. `app.state.web_shell = WebShellState(settings=settings, wall_clock=wall_clock, public_paths=PublicPaths())`.
   6. `app.add_exception_handler(ApiProblem, handle_api_problem)`;
      `app.add_exception_handler(RequestValidationError, handle_validation_error)`.
   7. `app.add_middleware(GateMiddleware, bindings=GateBindings(login_sessions=lambda a: provided(a,
      get_login_sessions), rate_limiter=lambda a: provided(a, get_rate_limiter), reset_gate=lambda a: provided(a,
      get_reset_gate), wall_clock=lambda a: provided(a, get_wall_clock)))`.
   8. `app.include_router(build_router())`; `app.add_api_route(HEALTHZ_PATH, healthz, methods=["GET"],
      include_in_schema=False)`.
   9. `install_log_formatter()`; return `app`.
4. `async def healthz(request: Request) -> JSONResponse`: `heartbeat = provided(request.app, get_heartbeat)` (direct
   call, **no `Depends`**: a sync dependency would take a worker thread); `if heartbeat.fresh(time.monotonic()):` return
   `JSONResponse({"status": "ok"})`; else `request.state.error_kind = "heartbeat_stale"` and return
   `JSONResponse({"status": "stale"}, status_code=503)`. No session, no SQLite, no pool, no reset wait (step 6.3).
Check: `uv run pytest -q tests/api/test_app.py`.

### Step 9 — `register_web` hunk in `src/meridian/web/container.py` (body and docstring only)

```python
def register_web(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-23 web shell: login routes, reset gate, rate limiter, public paths, web/deps.py bindings (web.md §1–§7).

    Binds the reset gate, the rate limiter, the one stream CapacityLimiter(4) and the wall clock create_app chose,
    and registers the two public paths. An app that create_app did not build has no web shell, so this does nothing.
    """
    import anyio
    from meridian.services.reset_gate import ResetGate
    from meridian.web.deps import RATE_LIMITER, RESET_GATE, STREAM_POLL_LIMITER, STREAM_POLL_THREADS, WALL_CLOCK
    from meridian.web.middleware import RateLimiter, WebShellState

    shell = getattr(app.state, "web_shell", None)
    if not isinstance(shell, WebShellState):
        return
    container.provide(RESET_GATE, lambda _c: ResetGate())
    container.provide(RATE_LIMITER, lambda _c: RateLimiter(limits.web))
    container.provide(STREAM_POLL_LIMITER, lambda _c: anyio.CapacityLimiter(STREAM_POLL_THREADS))
    container.provide(WALL_CLOCK, lambda _c: shell.wall_clock)
    shell.public_paths.add_exact("POST", "/api/login")
    shell.public_paths.add_exact("GET", "/healthz")
```
`STREAM_POLL_THREADS = 4` lives in `deps.py` ([A] DO-3 §2.3 rule 4; WEB-19). Keep the first docstring line and the
token `AEA-23` (AEA-01's `test_every_register_stub_present` checks it and calls the hunk with a bare `FastAPI()`,
expecting nothing provided — the guard keeps it green). Change nothing else in the file.
Check: `uv run pytest -q tests/unit/web/test_container.py tests/unit/test_import_direction.py tests/unit/web/test_deps.py -k "register_web or stub or container_imports"`.

### Step 10 — `tests/api/openapi_check.py` (web §13; R-W-9; AEA-23-1)

1. `CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "ux" / "03-structure" / "ui-contracts.openapi.yaml"`;
   `CONTRACT_URI = "urn:meridian:ui-contracts"`.
2. `ContractLoader(yaml.SafeLoader)`; after the class, set `ContractLoader.yaml_implicit_resolvers = {first: [(tag,
   rx) for tag, rx in resolvers if tag not in (TIMESTAMP, BOOL, INT, FLOAT)] for first, resolvers in
   yaml.SafeLoader.yaml_implicit_resolvers.items()}` (new lists: never mutate `SafeLoader`'s), then
   `add_implicit_resolver` (in this order) for: BOOL `^(?:true|True|TRUE|false|False|FALSE)$` first chars `tTfF`;
   INT (YAML 1.2 JSON schema) `^(?:[-+]?(?:0|[1-9][0-9]*)|0o[0-7]+|0x[0-9a-fA-F]+)$` first chars `-+0123456789`;
   FLOAT `^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$`
   first chars `-+.0123456789`. Null resolution is unchanged. Why INT/FLOAT too: YAML 1.1's sexagesimal ints turn
   `quiet_hours.start: 22:00` in six `getMonitoring` examples into `1320` and those examples then fail their schema
   (measured in planning: 248 examples, 6 invalid with web §13's two changes only, 0 invalid with all four).
3. `load_document()` (`functools.cache`): `yaml.load(CONTRACT_PATH.read_text("utf-8"), Loader=ContractLoader)` — never
   `yaml.safe_load`. Never writes the file.
4. `load_contract()` (`functools.cache`): for every path and method with an `operationId`: for each response status,
   follow a response-level `$ref` (`#/components/responses/<Name>`) to its pointer base; for each content type store
   the schema object `{"$ref": CONTRACT_URI + "#" + quote(pointer, safe="/~")}` where `pointer = base +
   "/content/" + esc(content_type) + "/schema"` and `esc` = `"~"→"~0"`, `"/"→"~1"`; statuses with no content map to
   `{}`. `event_schema` = the last segment of `responses["200"].content["text/event-stream"].schema.contentSchema.$ref`
   when present (the OpenAPI has no `x-event-schema` key; `contentSchema` carries it). `error_codes =
   frozenset(document["components"]["schemas"]["ApiError"]["properties"]["error"]["properties"]["code"]["enum"])`.
   `registry = Registry().with_resource(CONTRACT_URI, Resource.from_contents(document,
   default_specification=DRAFT202012))`. `version = document["info"]["version"]`.
5. `_FORMATS`: a `jsonschema.FormatChecker()` with `"date-time"` replaced by a checker that requires `"T"` and a UTC
   offset or `Z` and parses with `datetime.fromisoformat` (no `rfc3339-validator` dependency is installed); `uuid` is
   built in.
6. `assert_response_matches(response, operation_id)`: every failure is an `AssertionError` whose message starts with
   `f"[OpenAPI {contract.version}] {operation_id}: "`. Checks in order: operation exists; `str(response.status_code)`
   is documented; content: if the status documents no content, the body is empty; else the response content type (before
   `;`) is documented and `Draft202012Validator(schema, registry=contract.registry,
   format_checker=_FORMATS).iter_errors(response.json())` yields nothing (report the first error's path and message);
   `X-Request-ID` header present; if the body is a dict with `"error"`: `body["error"]["code"] in contract.error_codes`
   and `body["request_id"] == response.headers["X-Request-ID"]`.
7. `assert_sse_frames_match(frames, operation_id)`: the op has `event_schema`; each frame's `json.loads(frame.data)`
   validates against `{"$ref": CONTRACT_URI + "#/components/schemas/" + event_schema}`; when `frame.id` is not `None`,
   `str(payload["event_id"]) == frame.id`.
8. `operations_documenting(status)` = ops whose responses contain `status`.
   `operations_documenting_code(status, code)` = ops documenting `status` whose response (after following `$ref` to
   `components/responses`) has an `application/json` example with `value.error.code == code`.
Check: `uv run pytest -q tests/api/test_openapi_check.py tests/api/test_openapi_sets.py`.

### Step 11 — `tests/contract/cases/auth.py` (AC-29; case data for AEA-59's runner)

Plain data, no `meridian` import, no I/O. Docstring states the closed vocabulary the runner implements.
```python
"""Server contract cases for CON-22 (`login`, `logout`), owned by AEA-23 (AC-29, AEA-23-3).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, AEA-23's
tests/api/test_contract_cases_auth.py drives them. Vocabulary (closed):
  preconditions: "login" = sign in with the configured demo pair and keep the cookie.
  setup: "login_rejects_exhausted" = first send limits.web.login_rejects_per_ip wrong-pair logins from the same client.
  body: {"example": <named request example>, "credentials": "configured" | "wrong_password"} fills username and
        password from the test settings ("wrong_password" keeps the configured username and sends another password);
        {"raw": <JSON value>} sends JSON as given; {"text": <str>} sends non-JSON text; None sends no body.
"""
from __future__ import annotations
from typing import Final
ROUTE_FILE: Final = "auth"
CASES: Final[dict[str, dict[str, object]]] = {
    "login": {"public": True, "drives": (
        {"name": "signed_in", "status": 200, "preconditions": (), "body": {"example": "PLACEHOLDERS", "credentials": "configured"}},
        {"name": "missing_password", "status": 400, "code": "VALIDATION_ERROR", "preconditions": (), "body": {"raw": {"username": "placeholder-user"}}},
        {"name": "not_json", "status": 400, "code": "VALIDATION_ERROR", "preconditions": (), "body": {"text": "not json"}},
        {"name": "wrong_pair", "status": 401, "code": "LOGIN_FAILED", "preconditions": (), "body": {"example": "PLACEHOLDERS", "credentials": "wrong_password"}},
        {"name": "throttled", "status": 429, "code": "LOGIN_RATE_LIMITED", "preconditions": (), "setup": "login_rejects_exhausted", "body": {"example": "PLACEHOLDERS", "credentials": "configured"}},
    )},
    "logout": {"public": False, "drives": (
        {"name": "logged_out", "status": 204, "preconditions": ("login",), "body": None},
        {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (), "body": None},
    )},
}
```
Check: `uv run pytest -q tests/api/test_contract_cases_auth.py`.

### Step 12 — make the frozen suite green

Run the affected tests (§7.2) until green. If a frozen test looks wrong, **do not edit it**: stop and report the test,
the line and why (it goes back to the test-writer through the orchestrator).

### Step 13 — journey record and context files (AC-31, AC-36)

1. `docs/testing/journeys/<YYYY-MM-DD of the build>-AEA-23.md` in the AEA-01 record's table format (fields: Claim,
   Level, Tested revision, Environment, Command, Result, Evidence location, Remaining limitations, Blocked by). Claim:
   "AEA-23 web shell: gate, login/logout, providers, reset gate, rate limits, `openapi_check` (AC-1…AC-35) at unit and
   TestClient level with doubles; journeys J-1 (login, guard redirect, 401s) and J-8 (role refusals, expired session)
   will exercise this code". Level: `mock-tested`. Command: the affected-test command of §7.2 and `uv run python -m
   tests.journeys.affected --base main`. Result: the pass count and `0 journeys affected`. Limitations: no real
   `StaffSessionStore`, SQLite, heartbeat or browser; the DB and trace sinks in AC-8 are empty at this level; the strict
   contract run (AC-29) waits for AEA-59. Blocked by: "AEA-57 (harness, J-1); AEA-52 (J-8); AEA-59 (strict contract run)".
   No secrets, no demo pair values.
2. `.claude/reference/area-map.md`: A8 row *Status* cell → `partly built: AEA-23 <sha>` (`web/{app,middleware,deps,
   errors,logging}.py`, `web/routes/auth.py`, `web/schemas/auth.py`, `services/reset_gate.py`,
   `tests/api/openapi_check.py`); the rest planned. Change only that cell.
3. `.claude/state/icm-progress.md`: row *Routes verified against code and tests* — replace its evidence cell, adding
   "A8 → `web/` shell checked against `tests/api/` and `tests/unit/web/` (AEA-23, `<sha>`; N pass)"; ≤ 400 characters.
4. `docs/design/code-design.md`: append to the existing `**Built:**` line above the §3 tree:
   "`web/{app,middleware,deps,errors,logging}.py`, `web/routes/auth.py`, `web/schemas/auth.py`,
   `services/reset_gate.py` (AEA-23, `<sha>`)". Status only; no redesign. DO-6 is not edited (record names equal web §10).
5. `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL.

### Step 14 — gates and commit

Run §7.3 (cheapest first). Commit on the ticket branch with explicit paths (never `git add -A`):
`git add src/meridian/web/errors.py src/meridian/web/logging.py src/meridian/web/middleware.py src/meridian/web/deps.py
src/meridian/web/app.py src/meridian/web/routes/auth.py src/meridian/web/schemas/auth.py
src/meridian/services/reset_gate.py src/meridian/web/container.py tests/api/openapi_check.py
tests/contract/cases/auth.py docs/testing/journeys/<file> .claude/reference/area-map.md .claude/state/icm-progress.md
docs/design/code-design.md`. Message: `feat(web): app, gate middleware, demo login, providers (AEA-23)` with a body
listing ACs and the evidence, last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push
(only the merge step pushes main); never force-push.

### What the implementer must not do

- Edit any frozen test, `tests/api/web_shell_support.py`, `tests/conftest.py`, `tests/unit/web/test_container.py`, the
  OpenAPI, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, any other hunk of `container.py`, `domain/*`, `config.py`,
  `ports/*`, `policy/*`, `pyproject.toml`, `uv.lock`.
- Add an error code, a wire field, an env variable, a `Settings` field, a header, a query parameter or a route that sets
  or shifts the wall clock; construct `ContainerOverrides` anywhere in `src/`.
- Log, trace or return a username, password, cookie token, session secret, eval key, `run_id` sent without the key,
  request body, raw path or query string; call `str()` / `repr()` of a request body in a message.
- Short-circuit the credential check (`and`, early return) or compare with `==`.
- Read `.env`; put a 6-digit number, card-like number or full phone number in code or data; call a paid model; bind
  port 4019 or 5184; start a server.
- Import `EndedThread` / `ConversationRow` / anything from `adapters/`, or a later ticket's service module.
- Run the full suite (§7.2 says what runs) or `pytest -n` above 2.

---

## 6. Data and fixtures

All synthetic, generated at test run time; nothing issued is written.

| Data | Source | Rule |
|---|---|---|
| Demo pair, session secret, model keys, eval key | `secrets.token_hex` / `token_urlsafe` in `tests/api/web_shell_support.py::make_settings` | Distinct per test run; no real secret, no `.env` |
| Distinctive "must be absent" values | `"zq" + secrets.token_hex(10)` | Letters and hex only: never a 6-digit run, card-like or phone-like number |
| Login session tokens | the `FakeSessionStore` double (`secrets.token_urlsafe(32)`) | Test memory only |
| Thread ids | `str(uuid.uuid4())` | — |
| Case reference in probes | `"MHC-C-0001"` | synthetic format value |
| The OpenAPI | `docs/ux/03-structure/ui-contracts.openapi.yaml` | Read only (`load_document`) |
| Data dir for `full_app` | `tmp_path / "data"` (AEA-10's hunk, once merged, copies the issued DB there read-only) | Never the issued file |

### 6.1 `tests/api/web_shell_support.py` (test-writer; frozen)

Helpers every AEA-23 test imports (not a conftest; other route tickets may import it read-only):
- `make_settings(tmp_path, **changes) -> Settings` — `Settings.model_validate({...})` with generated
  `anthropic_api_key`, `openrouter_api_key`, `demo_username` (`"user-" + token_hex(6)`), `demo_password`
  (`"pw-" + token_hex(8)`), `session_secret`, `data_dir=tmp_path/"data"`, `index_dir=tmp_path/"index"`,
  `web_dist_dir=tmp_path/"no-dist"`, `require_frontend=False`, plus `changes`.
- `FakeSessionStore` implementing **both** `LoginSessions` and `StaffAccess` (like AEA-44's real store): `start(now)` →
  `LoginSession(session_id=LoginSessionId(str(uuid4())), role=DemoRole.CUSTOMER, role_reset=False,
  signed_in_at=<fixed demo time 2026-10-16T14:00:00-05:00>, expires_at=now + timedelta(seconds=lifetime_s))` and a
  `secrets.token_urlsafe(32)` token; `resolve(token, now)`: blank or unknown → `SessionMissing()`; `now >= expires_at`
  or token marked expired → `SessionExpired()`; else the stored session (with its **current** role); `end(token)`:
  idempotent removal unless `end_invalidates=False`; `session_info(session)` → `SessionInfoData(role, display_name
  "Customer (demo)", sees ("Chat", "Demo guide", "Demo inbox", "Monitoring", "Evaluation"), signed_in_at)`;
  `actor_for(session, needs)` → `actor_for(StaffRole(session.role))` when `session.role.value in {r.value for r in
  needs}` else `RoleRefusal(role=session.role, needs=needs, reason="role_reset" if session.role_reset else
  "wrong_role")`. Helpers: `issue(role=…) -> str` (a live token without a login), `set_role(token, role)`,
  `expire(token)`, `fail_on_start: bool`. Records every call as `(method, now-or-None)` in `calls`.
- `FakeHeartbeat(fresh: bool = True, raises: Exception | None = None)` recording calls.
- `FakeUow` (`__call__(*, write=False, exclusive=False)` → context manager whose object has
  `core.conversations.lookup(thread_id)` from a dict; records lookups; `raise_on_use=True` raises on `__call__`),
  `ConversationRowStub(thread_id, demo_session, live_state="not_live")`, `EndedThreadStub(thread_id, demo_session,
  ended_wall_at, reason, reset_id)` (frozen dataclasses).
- `RecordingTraceSink` (implements `TraceSink`'s four methods, appends `repr` of every argument to `seen`).
- `captured_log()` context manager: a `logging.Handler` with `AllowListFormatter` on the `"meridian"` logger writing to a
  `StringIO`, level INFO; yields the `StringIO`.
- `web_app(monkeypatch, settings, *, overrides=None, store=None, heartbeat=None, uow=None, limiter=None) -> FastAPI` —
  monkeypatches `meridian.web.app.build_container` with a builder that makes `Container(settings=…, limits=Limits())`,
  calls only `register_web`, then `build()`; then `create_app(settings, overrides=overrides)` and sets
  `app.dependency_overrides` (zero-argument lambdas) for `get_login_sessions` and `get_staff_access` (the store),
  `get_heartbeat`, `get_uow_factory`, `get_rate_limiter` when given.
- `full_app(monkeypatch, settings, *, store, heartbeat) -> FastAPI` — the **real** `build_container` (every hunk) with
  `Container.on_start` monkeypatched to a no-op (no background thread or watchdog starts in tests), the store and
  heartbeat overridden. Used by AC-1, AC-34, AC-35.
- `add_probe_route(app, operation_id, *, dependencies=(), endpoint=None)` — registers the operation's real method and
  path from `load_contract().operations[operation_id]`; the default sync endpoint returns
  `{"run_tag", "run_id", "client_ip", "turn_verdict"}` from `get_request_context` (never a 200 checked against the
  OpenAPI). `add_test_route(app, method, path, endpoint)` for non-OpenAPI probes under `/api/test/…`.
- `login(client, settings) -> httpx.Response`.

---

## 7. Checks

### 7.1 Frozen tests (test-writer writes these first, red for the right reason; implementer must not edit)

| File | Tests (names binding) | ACs |
|---|---|---|
| `tests/api/test_gate.py` | `test_every_api_route_but_login_requires_session` (uses `full_app`; loops over `app.routes` inside the lifespan: every `APIRoute` under `/api/` and each of its methods except `POST /api/login`, with no cookie, `mhc_session=` blank, an unknown token, and a valid token with one character changed; path params `{thread_id}`→UUID4, `{reference}`→`MHC-C-0001`, `{flag_id}`→`1`; JSON body `{}` for POST/PUT/PATCH; asserts 401 `UNAUTHENTICATED` `reason: none`, `assert_response_matches(resp, OPERATIONS_BY_ROUTE[(method, path)])`, fails naming any `/api` route missing from `OPERATIONS_BY_ROUTE`; `/healthz` not 401; public entries contain `("exact","POST","/api/login")` and `("exact","GET","/healthz")` and no other entry under `/api/`; prints the entries); `test_page_get_redirects_to_login_without_open_redirect` (`Location` for `/staff/queue` equals `/login?return_to=%2Fstaff%2Fqueue&reason=none`; `safe_return_to` returns `None` for the three hostile values; a GET of path `//evil.example` (built as `http://testserver//evil.example`) gets a `Location` without `evil`); `test_expired_session_reason_expired_and_cookie_cleared`; `test_example_pair_unsigned_page_login_and_role_refusal` (the issue's example pair: 303 for `/staff/queue`; login 200 + cookie; wrong password 401; `getQueue` probe with `require_staff(REPRESENTATIVE, SUPERVISOR)` as customer → 403 `{role: customer, needs: [representative, supervisor], reason: wrong_role}` validated against `getQueue`) | AC-1, AC-2, AC-3, WP |
| `tests/api/test_auth.py` | `test_login_success_sets_session_cookie`, `test_login_failed_identical_for_every_cause` (spy via `monkeypatch.setattr(hmac, "compare_digest", spy)`; no eval header), `test_login_malformed_body_is_400`, `test_login_rate_limited_per_ip` (fake wall clock via `ContainerOverrides(wall_clock=…)`; a different IP via `X-Forwarded-For` with `trust_proxy_headers=True`; limiter from `RateLimiter(WebLimits())`), `test_credentials_and_token_absent_from_body_log_span_db` (correct, wrong-password, wrong-username, rate-limited login and logout; sinks: every body and header except the one login `Set-Cookie`, `captured_log()` and `caplog.text`, `RecordingTraceSink` via `ContainerOverrides(trace=…)`, a text dump of every `*.sqlite`/`*.db` under `settings.data_dir` (prints the file count, 0 at this ticket)), `test_logout_clears_cookie_and_ends_session` (sub-case A: logout → 204 + `Max-Age=0` + `end` got the cookie token; old cookie then → 401; sub-case B, two tabs logging out at once: store with `end_invalidates=False`, two logouts with the same cookie → 204 both, `end` called twice), `test_cap10_login_records_captured`, `test_wf18_status_values_and_no_outbound` (socket guard on `socket.socket.connect` and `socket.create_connection` failing on any non-loopback address; the forced 500 (`FakeSessionStore(fail_on_start=True)`) asserts status 500, an `X-Request-ID` header, body `== {"request_id": <that header>}` with **no** `error` key (D-P1), and the `request` record's `status` 500 with a non-empty `error_kind`) | AC-4–AC-8, AC-22, AC-25, AC-32 |
| `tests/api/test_app.py` | `test_validation_error_is_400_without_value` (AST scan: exactly one `ast.Constant` equal to `"constraint"` in `src/meridian/web/**/*.py`, inside `errors.render_api_problem`; handlers registered for `ApiProblem` and `RequestValidationError`), `test_request_id_on_every_response`, `test_healthz_reads_heartbeat_not_pool_or_db` (inside the TestClient: `client.portal.call` sets `anyio.to_thread.current_default_thread_limiter().total_tokens = 1`; a background thread holds the one worker in a sync `/api/test/block` route waiting on a `threading.Event`; `/healthz` called from another thread and joined with a 3 s timeout returns 200; `FakeUow(raise_on_use=True)` records 0 calls; with `ResetGate` held, `/healthz` answers in < 1 s; restore the limiter), `test_lifespan_builds_and_closes_container`, `test_healthz_request_record`, `test_overrides_test_only`, `test_healthz_status_values` (the raising-heartbeat 500 is asserted the same way as AC-32's forced 500: `X-Request-ID`, body `{"request_id": …}` only, record `status` 500 with `error_kind`), `test_wall_clock_override_reaches_get_wall_clock` (fake returns T0 on the first call, T0 + 43 200 s after; `provided(app, get_wall_clock) is fake`; store calls are `start(T0)` then `resolve(T0+43200)`; 401 `expired`; `GET /api/demo/clock` read before and after when the route exists, else prints "getDemoClock not registered yet (AEA-43)"; default and `ContainerOverrides()` within 2 s of `datetime.now(UTC)`), `test_wall_clock_not_settable_from_settings_env_or_http` (env via `monkeypatch.setenv` for the required `ENV_NAMES` plus `MERIDIAN_WALL_CLOCK`, `MERIDIAN_NOW`, `MERIDIAN_FAKE_TIME` = a year-2000 ISO time; `create_app()` with no arguments over `full_app`'s builder), `test_unhandled_error_is_500_with_request_id_only` (PA-1) | AC-9–AC-11, AC-23, AC-26, AC-30, AC-33–AC-35, PA-1 |
| `tests/api/test_openapi_check.py` | `test_validator_rejects_and_accepts` (three rejections each `AssertionError` containing `0.1.0-ux3`; every `application/json` response example of every operation passes via `httpx.Response(status, json=value, headers={"X-Request-ID": <value's request_id or "x">})`), `test_error_codes_match_openapi` (`contract.error_codes == {m.value for m in ApiErrorCode} - Notice.code enum - ErrorBlock.code enum`, both enums read from the document), `test_loader_keeps_yaml12_strings` (STARTED `greeting.at` is `str` `2026-10-16T14:20:00-05:00`; BURNING_CHECK `blocks[0].options[0].option == "yes"` (str); `getStaffing` 200 example keys `{"ON", "OFF"}`; plan-added fact: `getMonitoring` DEFAULT `alert_config.quiet_hours.start == "22:00"` (str)), `test_contract_keeps_yaml_strings` (walk: 0 `datetime`/`date`; `true`/`false` stay `bool`) | AC-24, AC-27 |
| `tests/api/test_openapi_sets.py` | `test_rate_limit_set_matches_openapi`, `test_reset_503_set_matches_openapi` (`operations_documenting_code("503", "RESET_IN_PROGRESS")`), `test_operation_table_matches_openapi` (PA-2) | AC-12, AC-21, PA-2 |
| `tests/api/test_contract_cases_auth.py` | `test_auth_cases_drive_documented_statuses` (drives every `CASES` entry through `web_app` with `FakeSessionStore`, implements the docstring vocabulary, `assert_response_matches` on each; every documented error status of `login` (400, 401, 429) and `logout` (401) has a case) | AC-29 (local) |
| `tests/unit/web/test_middleware.py` | `test_rate_limits_by_operation` (small `WebLimits` via `get_rate_limiter` override; read op → 429 `REQUEST_RATE_LIMITED` + `retry_after_ms`, body valid for that op; `requestPerson` 200 after 10 × the smallest limit; `submitTurn` probe echoes `turn_verdict` `{allowed: false, scope: "thread"}` with status 200; session-then-IP order), `test_limits_admit_twenty_conversations_from_one_ip_and_login` (pure `limit_verdict` with default `WebLimits`: 20 `startChatSession` at t=0, then 255 `submitTurn` per minute round-robin over 20 threads for 5 fake minutes; 0 refusals), `test_client_ip_and_bucket_keys`, `test_run_tag_requires_eval_key` (six sub-cases), `test_eval_key_absent_from_outputs` | AC-12–AC-16 |
| `tests/unit/web/test_logging.py` | `test_allow_list_formatter_drops_raw_path_query_body_and_extras` (unit on `AllowListFormatter` + an app request to `POST /api/test/echo/{item}?q=<distinct>` with a distinct body; each record's key set ⊆ `ALLOWED_FIELDS[kind]`, request records have all but `error_kind`; a `logger.info("x", extra={"meridian_record": {..., "extra_field": distinct}})` drops it) | AC-17 |
| `tests/unit/web/test_deps.py` | `test_every_provider_declared_overridable_and_lazy`, `test_require_staff_refusals`, `test_owned_thread_404_410`, `test_owned_stream_thread_maps_ended_to_404`, `test_role_refusal_names_current_role`, `test_register_web_binds_shell_objects_and_skips_bare_app` (PA-3) | AC-18–AC-20, AC-28, PA-3 |
| `tests/unit/web/test_reset_gate.py` | `test_reset_gate_503_wait_and_double_hold` (eight 503s each < 1 s; `getChatThread` probe during a 1 s hold answers ≥ 0.9 s later with the post-reset value; nested `hold()` raises `ResetAlreadyRunning`) | AC-21 |

Test-writer commands: `uv run pytest -q <its files>` (red, each for a missing module/symbol or wrong behaviour) and
`uv run pytest --collect-only -q` (the whole suite still collects).

### 7.2 Implementer: while iterating, and the affected set

```bash
export UV_LINK_MODE=hardlink
uv run pytest -q tests/api tests/unit/web tests/unit/test_import_direction.py tests/unit/test_skeleton.py
```
"Affected" = `tests/api/`, `tests/unit/web/` (includes AEA-01's `test_container.py`, since `container.py` changes),
`tests/unit/test_import_direction.py`, `tests/unit/test_skeleton.py`, plus any file `grep -rl "meridian.web\|reset_gate\|openapi_check" tests/`
lists. Use `uv run --with pytest-xdist pytest -n 2 …` only if the serial run is slow; never above `-n 2`. The full
suite is **not** run: no `conftest.py`, settings, dependency or lockfile change, and `container.py` is imported only by
`web/app.py` and tests.

### 7.3 Implementer: once before the final commit (cheapest first; stop at the first red)

```bash
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy
uv run pytest -q tests/api tests/unit/web tests/unit/test_import_direction.py tests/unit/test_skeleton.py
uv run pytest --collect-only -q
uv run python -m tests.journeys.affected --base main          # expected: "0 journeys affected"
python3 ~/.claude/skills/icm-project/scripts/check_context.py .
```
Passing looks like: ruff and format clean; mypy "Success"; every listed test passes (report the count); collect-only
exit 0; the journey command prints `0 journeys affected`; `check_context.py` no FAIL. Paste the results into the
report and the journey record.

### 7.4 Grep evidence (in the report; the reviewer re-reads it)

```bash
grep -rn "^[a-z_]* = .*(" src/meridian/web/        # expected: no output (constants are UPPER_CASE)
grep -rn "ContainerOverrides(" src/                # expected: no output
grep -rn "wall_clock" src/meridian/                # expected: web/app.py (override binding), web/deps.py (provider,
                                                   #   key, wall_now), web/container.py register_web (pass-through),
                                                   #   web/middleware.py and web/routes/auth.py as READERS only
```

### 7.5 Later evidence (not a merge gate for this ticket)

`CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "login or logout" -rs` once AEA-59 merges;
J-1 at AEA-57, J-8 at AEA-52 (`integrated with a scripted model`). The wave-1 merge runs the security agent on this
diff (`risk::security`).

### Checks and evidence (template form)

| Check | Command | Evidence |
|---|---|---|
| Capture verification WF-18 (CAP-10) | `uv run pytest -q tests/api/test_auth.py -k "cap10 or wf18"` | 4 `request` records, 3 `auth_event`s (`ok`, `rejected`, `logged_out`), the 401 body; status/error_kind triples; 0 outbound connects |
| Capture verification WF-17 | `uv run pytest -q tests/api/test_app.py -k healthz` | 200 / 503 / 500 records with `error_kind` only on 5xx |
| Evaluation check (E-8 shape, CAP-7 tag) | `uv run pytest -q tests/unit/web/test_middleware.py -k "twenty or run_tag"` | 0 limited across the burst; six run-tag sub-cases |
| Fast gates | §7.3 | clean |
| Journey record | `uv run python -m tests.journeys.affected --base main` | `0 journeys affected`; record level `mock-tested` |

---

## 8. Risks and requests

**Decisions made here (engineering, within the signed contracts):**
- **D-P1 · Unhandled exception body.** No generic code exists in the signed `ApiError.code` enum, and inventing one
  would change the OpenAPI. So an unhandled exception answers **500 `{"request_id": …}` + `X-Request-ID`**, the
  `request` record carries `status: 500` and `error_kind` = the exception class name. `apps/web`'s client already maps
  a body without `error` to `HTTP_500` and reads `request_id`. AC-32's phrase "answers 500 `ApiError`" is met in
  status and correlation, not in shape. **Request to the orchestrator:** comment on issue #23 proposing AC-32's wording
  "answers 500 with `X-Request-ID` and a body holding `request_id`"; if Innocent wants a generic code, that is an
  OpenAPI change for the UX session (`INTERNAL_ERROR`, 500) plus one `ApiErrorCode` member in AEA-02, and only
  `render_unhandled_error` changes here.
- **D-P2 · `ContractLoader` also uses YAML 1.2 int/float resolution.** web §13 says "ints, floats and null resolve as
  before", but YAML 1.1 sexagesimal parsing turns `22:00` into `1320` in six `getMonitoring` examples, which then fail
  AC-24 (measured in planning). AC-27 asks for YAML 1.2, which this satisfies. **Request:** the web.md owner adds one
  line to §13 (doc only); AEA-59's planner should expect the same loader.
- **D-P3 · Provider signature.** Providers take `request: Request` (they resolve from `app.state.container`). Usage
  `Depends(get_x)` and overrides are unchanged. **Hunks never call providers**: they use the container keys in §5
  step 5 (e.g. `container.get(deps.WALL_CLOCK)` inside a factory; models.md's illustrative `get_wall_clock()` in the
  container becomes that). **Request to the orchestrator:** hand the key table (§5 step 5) to every wave-2 planner
  (AEA-29, 30, 31, 32, 40–48, 51, 53, 57).
- **D-P4 · Two extra providers.** `get_heartbeat` (+ `HeartbeatReader`, the ticket's "injected `Heartbeat`") and
  `get_settings`. **Request to AEA-32:** provide `deps.HEARTBEAT` in `register_ops`. AC-18's list check is a superset
  check, so these do not conflict with web §4.
- **D-P5 · `RateLimiter.check/peek` gain `family: Literal["turn", "read"] = "read"`** (keyword, defaulted) because web
  §5 has two limits each for SESSION and IP. AEA-43 calls only `record_reset` and `peek(RESET_IP, …)`, unaffected.
- **D-P6 · Login and reset windows are sliding logs, the per-minute limits are token buckets** (web §5 "while 10 rejects
  are on record" is a count in a window).
- **D-P7 · Operation classification by `(method, OpenAPI path)`.** **Request to every route ticket (AEA-40…48):**
  register paths and parameter names exactly as the OpenAPI writes them (`{thread_id}`, `{reference}`, `{flag_id}`)
  and set `operation_id=<operationId>`; AC-1's route loop fails on any `/api` route not in the table.
- **D-P8 · `resetDemo` never waits on the gate** (else a second reset would run after the first instead of answering
  409).

**Collisions and requests:**
- **AEA-01's `tests/unit/web/test_container.py::test_every_register_stub_present`** calls every hunk on a bare
  `FastAPI()` and asserts it provides nothing. `register_web` returns early on an app without `web_shell`, so it stays
  green. **AEA-10's hunk (and every later one) will turn that test red.** Request: a small follow-up on AEA-01 scoping
  that assertion to hunks whose docstring still says "No-op until".
- **`tests/contract/cases/auth.py` sets the first case format** before AEA-59 defines it. Request: AEA-59's planner
  adopts this vocabulary or files a one-file follow-up on AEA-23; AEA-23's local driver test stays the evidence until then.
- **AEA-44:** `LoginSessions.resolve` runs on the event loop (web §6: middleware async, no worker thread), so it must
  stay one indexed read with no write. During a reset's exclusive transaction a stream request's `resolve` could block
  the loop up to `busy_timeout`; AEA-41/46 should know.
- **AEA-50:** run uvicorn with `--no-access-log` (its access log prints raw paths and query strings, defeating AC-17 in
  deploy) and with the factory `meridian.web.app:create_app --factory`.
- **AEA-49:** register public paths through `app.state.web_shell.public_paths` (a `WebShellState`), guard a bare app
  the same way, and set `scope`-level route templates if it wants `spa_fallback` in the `request` record (the
  middleware logs the matched route's `path`, else `<unmatched>`).
- **AC-1, AC-34, AC-35 boot the real container** (starters suppressed). Each later hunk must build on a tmp data dir
  with test settings — AEA-57 needs the same; if a hunk cannot, these tests go red at that merge, which is the intended
  seam signal.
- **Honest limits at this level:** AC-8's DB and trace sinks are empty (doubles, no SQLite writes, no spans); AC-34's
  demo-clock check is live only once `getDemoClock` exists (AEA-43/30). Recorded in the journey record.
- **Shared context lines.** The A8 *Status* cell, the ICM row and the DO-3 `**Built:**` line are also edited by AEA-02,
  10, 44 and other wave-1 tickets. Expect a text conflict at merge; resolve by keeping every ticket's entry (the merge
  agent's job, not a reason to skip Step 13).
- **Size:** `middleware.py` is the largest file (~450–550 lines; cap 600). If it passes 600, stop and report rather than
  adding a module (a new module is a design change).

No signed contract changes. Decisions D-4…D-15 are unaffected (D-4 WEB-1 = A keeps the page-path 303; D-8 keeps
`owned_thread` per session; D-13's override is built as specified).

---

## 9. Readiness

**READY** (refreshed 2026-10-21 against `16ca639`), blocked on **AEA-02** only (still unmerged: frozen tests at `de9bb42`) (real imports: `Settings`, `ApiErrorCode`, `RequestId`, `ThreadId`,
`domain/staff.py`, `ports/*`). AEA-01 and AEA-04 are merged. Same-wave siblings (AEA-10 `uow_factory`, AEA-44 sessions,
AEA-32 heartbeat) are injected and tested with doubles; no edge to them.

**Gates:** none (no human, paid, live or UX gate). `risk::security`: frozen tests first (§7.1); `security-privacy-agent`
reads this diff at the wave-1 merge.
