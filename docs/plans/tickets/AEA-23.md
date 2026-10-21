## [AEA-23] web: app, middleware, demo login, dependency providers

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

> **US-28 · Sign in once, then switch between customer and staff in one click.** "As a **reviewer**, I need to sign in
> once with the demo login given in the README and then switch between acting as the customer and acting as a
> representative, supervisor or business owner in one click from any screen, so that I can play both sides of a handoff
> without separate accounts or passcodes." Acceptance includes: "nothing except the login and `/healthz` answers without
> the login … a wrong login gets one message whatever the cause; an expired session returns to the login."
> Also US-26 ("a rate limit … shows a plain message and the person option; no account existence is revealed").

**Example pair** (no worked pair exercises the login, so the pair is web.md's own end-to-end example and the OpenAPI's
CON-22 examples): an unsigned browser opens `/staff/queue` → the middleware finds no `mhc_session`, sees a page path and
answers **303** to `/login?return_to=%2Fstaff%2Fqueue&reason=none`. `POST /api/login` with the pair that matches
`MERIDIAN_DEMO_USERNAME` / `MERIDIAN_DEMO_PASSWORD` → **200** `LoginResponse` (`session.role: "customer"`, `landing: "/"`)
plus `Set-Cookie: mhc_session=<token>; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200` (and `Secure` in deploy). A wrong
password, a wrong username or an empty field → **401** `{error: {code: "LOGIN_FAILED", field: null, constraint: null,
details: null}, request_id}`, byte-identical apart from `request_id`. `GET /api/staff/queue` as `customer` passes the gate
and `require_staff(REPRESENTATIVE, SUPERVISOR)` refuses it with **403** `ROLE_NOT_ALLOWED` `{role: "customer", needs:
["representative", "supervisor"], reason: "wrong_role"}` (web.md opening example).

The HTTP shell every route ticket (AEA-40…AEA-49) plugs into, and the one gate in front of all of them. Every shape
below is defined in [`docs/design/contracts/stage7/web.md`](../../design/contracts/stage7/web.md) ("web §n"); where
web.md and DO-4 disagree, web.md wins (DO-4 §16).

1. **`web/errors.py`** (web §1): `ApiProblem(status, code, *, field, constraint, details, headers)`, raised by routes and
   dependencies for every HTTP 4xx/5xx and never for a composed HTTP 200 outcome; **one** handler in `web/app.py`
   renders `ApiError {error: {code, field, constraint, details}, request_id}`. The 422 → **400 `VALIDATION_ERROR`**
   handler builds an `ApiProblem` too, so there is exactly one renderer; `details` never holds a rejected value
   (DO-4 §0; `safe-validation-errors.md`). `ApiErrorCode` is AEA-02's and equals the OpenAPI enum (WEB-9).
2. **`web/app.py`**: `create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None)` and
   the frozen, test-only `ContainerOverrides(choice, structured, tools, trace, wall_clock)` (all optional; no env name,
   `Settings` field or CLI flag can build one; the deployed factory call passes nothing) (web §15, R-W-8);
   `wall_clock: Callable[[], datetime] | None` (Innocent D-13, 2026-10-21): when set, `create_app` binds
   `get_wall_clock` to it before the container is built, so session expiry, limiter windows, reset `now` and every
   MC-20 consumer read it and the demo clock is untouched; `None` keeps `lambda: datetime.now(UTC)`; no `Settings`
   field, env name, header, query parameter or route reads or shifts it (AEA-57's journey harness is its consumer, J-8's
   expired session); a lifespan that builds the container (`web/container.py`, AEA-01) once and closes
   it once (DO-3 §2.1); routers are included from each area's own `register_<area>()` hunk so this file never changes
   after this issue (slice plan §3); the lifespan hands `(settings, overrides)` to the container once, which passes
   `overrides` through untouched to `register_graph` (AEA-51), the only reader of the port maps and `trace` (this
   issue's `get_wall_clock` binding is the only reader of `wall_clock`); `GET /healthz` is `async def`, answers from the injected `Heartbeat.fresh(mono)`
   (AEA-32, cases.md §8; CAS-26: healthy while the last beat is ≤ 30 s old), never the worker pool or SQLite (DO-3
   §2.3 rule 3), and never waits on a reset (web §7).
3. **`web/middleware.py`**, in web §6's gate order, async and with no worker thread: (1) a `RequestId` (UUID4) returned
   as `X-Request-ID` on every response, errors included; (2) the reset gate (web §7: while `ResetGate.held()`, the eight
   operations that document 503 answer **503 `RESET_IN_PROGRESS`**, `details.retry_after_ms: 5000`, at once; every
   other operation except `/healthz`, `login` and the streams `await wait_clear(limits.web.reset_wait_s)` (5 s [A],
   WEB-37, MC-14) and then runs); (3) the session: public paths (`PublicPaths`: this issue registers only
   `("POST", "/api/login")` and `("GET", "/healthz")`; AEA-49 adds `/login` and, per WEB-1, the asset prefixes) continue
   with no session; otherwise `LoginSessions.resolve(SecretStr(cookie or ""), get_wall_clock()())` →
   `SessionMissing`: `/api/*` → **401 `UNAUTHENTICATED`** `details.reason: "none"`, any other GET → **303** to
   `/login?return_to=<path+query>&reason=none` (WEB-28); `SessionExpired`: the same with `"expired"` plus
   `Set-Cookie: mhc_session=; Max-Age=0`; `return_to` is accepted only as a same-origin path starting with `/` and not
   `//` (no open redirect); (4) rate limits (web §5; numbers are `Limits.web`, AEA-01, MC-22, each `[A]`): the six
   operations that document 429 (`startChatSession`, `listDemoInbox`, `getStaffing`, `getDemoClock`, `getMonitoring`,
   `getLatestEval`) answer **429 `REQUEST_RATE_LIMITED`** with `details.retry_after_ms` (SESSION then IP read buckets);
   `submitTurn` is **never** 429: the THREAD → SESSION → IP verdict goes into `RequestContext.turn_verdict` for AEA-40
   (WEB-12); `requestPerson` and every other operation are **never** limited (DO-1 §8.2); the six-operation set is a
   constant checked against the OpenAPI (WEB-3); (5) the eval tag: `X-Meridian-Eval-Key` compared with
   `hmac.compare_digest` against `Settings.eval_key`; only on a match is `run_tag` `X-Meridian-Run-Tag` (`eval` | `load`;
   absent or other → `eval`) and `run_id` `X-Meridian-Run-Id`; otherwise `run_tag = "live"`, `run_id = None`
   (WEB-7; DO-6 *Correlation*); (6) the route; (7) the `request` log record (web §10). Also in this file: the
   `RateLimiter` (in-process token buckets, `check`, `peek`, `record_login_reject`, `record_reset`; keys are thread id,
   session id or client IP, never the cookie value; idle buckets evicted after 2 × their window), `LimitScope`,
   `LimitVerdict`, `RequestContext` (client IP = the last `X-Forwarded-For` entry when `Settings.trust_proxy_headers`,
   else the socket peer [A: confirm Railway's header at AEA-56]), `PublicPaths` and the three header constants.
4. **`web/logging.py`**: structured log records through the AEA-04 LOG redaction profile and an **allow-list**
   formatter (web §10, WEB-11; no table, no DDL): `request` (`request_id`, `route` as the template, never the raw path
   or query, `status`, `duration_ms`, `caller_role` `anonymous` | a `DemoRole`, `thread_id` or null, `error_kind` on 5xx),
   `auth_event` (`request_id`, `outcome` `ok` | `rejected` | `rate_limited` | `logged_out`, `session_id` (the opaque
   UUID; null when rejected or rate limited), `at`), and pass-through for `stream_reconnect` (emitted by AEA-41/46) and
   `signal` (graph-nodes §4's `SignalRecord` fields, emitted by AEA-21). Never the username, password, cookie value,
   eval key or a request body.
5. **`web/routes/auth.py` + `web/schemas/auth.py`** (CON-22, operationIds `login`, `logout`; web §2): username and
   password each compared with `hmac.compare_digest` against `Settings.demo_username` / `demo_password` (both always
   compared, no short-circuit); empty strings fail the comparison → 401 `LOGIN_FAILED`; a missing field, non-string or
   non-JSON body → 400 `VALIDATION_ERROR` (WEB-10). Rejections call `RateLimiter.record_login_reject`; while
   `limits.web.login_rejects_per_ip` (10 [A]) rejects in `login_reject_window_s` (600 s [A]) are on record for the IP,
   every attempt, the right pair too, gets **429 `LOGIN_RATE_LIMITED`** with `Retry-After` and `details.retry_after_ms`
   (WEB-4). Success: a still-valid cookie's session is ended first, then `LoginSessions.start(now)` (staff.md §2's
   `StaffSessionStore`, injected double here) and the cookie is set to `IssuedSession.token` per web §2 (WEB-5, WEB-6).
   `login` builds `LoginResponse.session` from `get_login_sessions().session_info(issued.session)` plus
   `authenticated: true`, and `landing: "/"` (web §2, R-W-1; `SessionInfoData` is AEA-02's, in `domain/staff.py`,
   staff.md §1).
   `logout` answers 204, calls `LoginSessions.end` (idempotent) and sends `Max-Age=0`.
6. **`web/deps.py`** (sole owner, slice plan §0 rule 2; web §2–§4): the `LoginSessions` (with `session_info(session) ->
   SessionInfoData`, R-W-1), `StaffAccess` and `MetricsReads` Protocols; `require_staff(*roles: StaffRole)` (on `RoleRefusal` → `ApiProblem(403, ROLE_NOT_ALLOWED, details={role,
   needs, reason})`, `needs` in the order received, MC-4); `owned_thread` (a `ConversationRow` of this session → the
   `ThreadId`; an `EndedThread` of this session → **410 `SESSION_ENDED`** `{reason}`; malformed, unknown or another
   session's thread → the identical **404 `SESSION_NOT_FOUND`**; WEB-34, MC-16); `owned_stream_thread` (web §4, R-W-3:
   the same lookup as `owned_thread` with its 410 branch mapped to the identical 404, never a second lookup; CON-3's
   dependency, consumer AEA-41 only, because `streamChatEvents` documents no 410); and every provider web §4 lists
   (`get_request_context`, `get_login_session`, `get_login_sessions`, `get_staff_access`, `get_flag_service`,
   `get_session_service`, `get_turn_service`, `get_person_requests`, `get_handoff_service`, `get_case_service`,
   `get_reply_composer`, `get_identity_service`, `get_demo_service`, `get_reset_service`, `get_reset_gate`,
   `get_live_chat`, `get_metrics_reads`, `get_uow_factory`, `get_stream_poll_limiter` (ONE `CapacityLimiter(4)` per
   process, WEB-19), `get_rate_limiter`, `get_wall_clock` (returns `datetime.now(UTC)`, or `ContainerOverrides.wall_clock` when
   a test passed one (item 2, D-13); the one wall clock the container passes to every service, MC-20)). A provider whose ticket is later is declared by name and bound in its owner's
   `register_<area>()` hunk; until bound it raises `RuntimeError("not bound: <name>")` at call time, never at import.
7. **`services/reset_gate.py`** (web §7; WEB-13; slice-plan *Owns* addition MC-27): `ResetGate` (`held()`, `hold()`
   raising `ResetAlreadyRunning` when already held, `async wait_clear(timeout_s)`), one per process, built and bound in
   this issue's container hunk from the start; `ResetService` (AEA-31) takes it by constructor.
8. **`tests/api/openapi_check.py`** (web §13; WEB-24): `OperationSpec`, `Contract`, `ContractLoader(yaml.SafeLoader)`
   (no timestamp implicit resolver; booleans only `true`/`false` in their three spellings, so `yes`/`no`/`on`/`off`/`ON`/
   `OFF`/`y`/`n` stay strings; R-W-9), `load_contract()` (reads with `ContractLoader`, never plain `yaml.safe_load`;
   cached per test session; the OpenAPI is read, never written), `assert_response_matches(response, operation_id)`,
   `assert_sse_frames_match(frames, operation_id)` and `operations_documenting(status)`, using `jsonschema>=4.18`
   (Draft 2020-12, `referencing` registry) and PyYAML (dev dependencies in AEA-01's `pyproject.toml`). Every route ticket
   uses it.

### Source

- PRD R-48 (one demo login; role switch), R-41 (rate limits per session and IP), R-40 (secrets in Railway variables).
- **Final contract:** [`stage7/web.md`](../../design/contracts/stage7/web.md) §1 (errors), §2 (login session, lifetime,
  cookie, credential check), §3 (`require_staff`), §4 (request context, providers, `owned_thread`, `MetricsReads`), §5
  (rate limits), §6 (gate and public paths), §7 (reset gate), §10 (log records), §13 (`openapi_check.py`,
  `ContractLoader`), §15 (`create_app`, `ContainerOverrides`); residuals R-W-1, R-W-3, R-W-8, R-W-9
  ([`7b-decisions/residuals-web.md`](../7b-decisions/residuals-web.md)); UX-join amendments AEA-23-1…3
  ([`ux-join/backend-amendments.md`](../ux-join/backend-amendments.md) §2); ledger
  [`7b-decisions/web.md`](../7b-decisions/web.md) WEB-2…WEB-11, WEB-13, WEB-19, WEB-24, WEB-28, WEB-34, WEB-37; merge
  [`merge-clashes.md`](../7b-decisions/merge-clashes.md) MC-1, MC-2, MC-4, MC-5, MC-6, MC-9, MC-14, MC-15, MC-16, MC-20,
  MC-22, MC-27.
- `stage7/staff.md` §1 (`domain/staff.py`: `DemoRole`, `StaffRole`, `StaffActor`, `LoginSessionId`, `LoginSession`,
  `IssuedSession`, `SessionMissing`, `SessionExpired`, `RoleRefusal`), §2 (`StaffSessionStore`, the implementation this
  issue's doubles stand in for). `stage7/graph-core.md` §12 (`Settings`: `demo_username`, `demo_password`,
  `session_secret`, `eval_key`, `cookie_secure`, `trust_proxy_headers`; GRC-22). `stage7/cases.md` §8 (`Heartbeat`),
  CAS-26; §1.1–§1.2 (`core.conversations.lookup`, `EndedThread`). `stage7/graph-nodes.md` §4 (`signal` record fields).
- OpenAPI `ui-contracts.openapi.yaml` (wins on every wire shape): operationIds `login`, `logout` (CON-22);
  `components.responses` `Unauthenticated`, `LoginFailed`, `LoginRateLimited`, `TooManyRequests`, `ValidationError`,
  `RoleNotAllowed`; schemas `ApiError`, `LoginRequest`, `LoginResponse`, `SessionInfo`; security scheme `mhcSession`;
  the per-operation 429 and 503 responses. UI_CONTRACTS *Conventions*, *Access*, *Named errors*, CON-22.
- DO-3 §2.1, §2.3 rules 3–4, §3 `web/` rows, §6 S-17, S-18, §7 R-41 and R-48 rows. DO-1 §8.2 (*Rate limits*, *Handoff*,
  *Process hang*), §10 (*Demo login*, *Secrets*, *Errors*). DO-6 *Records*, *Correlation across boundaries*, *Content
  and redaction*, WF-17, WF-18, CAP-10. DO-7 M-3, M-18, M-22, M-24, M-28. PRD §5 *Load* ("rate limits … are set above 20").
- Slice plan row AEA-23; §0 rules 2–3; §3 rows `web/container.py`, `web/deps.py`, `web/routes/*.py`.
- **Brief check:** serves "Deployed URL — a live web app the reviewer can interact with directly. They will ask their own
  questions and try to break it" (Deliverables 1) by gating it behind one login (R-48) and failing cleanly under abuse;
  touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Every registered `/api/*` route except `POST /api/login` answers 401 `UNAUTHENTICATED` with `details.reason: "none"` when no `mhc_session` cookie (or a blank, unknown or tampered one) is sent, and `/healthz` answers without one — verify: `tests/api/test_gate.py::test_every_api_route_but_login_requires_session` (parametrised over `app.routes` at test time, so routes added later are covered; `PublicPaths` holds exactly the two entries this issue registers) — evidence: one passing case per route; the two public entries listed by name; each body passes `assert_response_matches`.
- [ ] AC-2 [invariant] An unsigned GET of a page path answers 303 to `/login?return_to=<path+query>&reason=none`; `return_to` values `//evil.example`, `https://evil.example/x` and `evil` are refused as targets (WEB-28) — verify: `tests/api/test_gate.py::test_page_get_redirects_to_login_without_open_redirect` — evidence: the `Location` header for `/staff/queue` equals `/login?return_to=%2Fstaff%2Fqueue&reason=none`; the three hostile values never appear in a `Location`.
- [ ] AC-3 [invariant] A session the `LoginSessions` double reports as `SessionExpired` answers 401 `UNAUTHENTICATED` with `details.reason: "expired"` on `/api/*` (303 with `reason=expired` on a page path) and sends `Set-Cookie: mhc_session=…; Max-Age=0`; `resolve` is called with the wall clock from `get_wall_clock()`, never the demo clock — verify: `tests/api/test_gate.py::test_expired_session_reason_expired_and_cookie_cleared` — evidence: pass; the double records a UTC `now`; the body carries no session id or token.
- [ ] AC-4 [invariant] Login with the configured pair returns 200 `LoginResponse` (`session.role: "customer"`, `landing: "/"`, no username or password anywhere in the body) and sets `mhc_session` to the double's `IssuedSession.token` with `Path=/`, `HttpOnly`, `SameSite=Lax`, `Max-Age=43200`, plus `Secure` exactly when `Settings.cookie_secure` is on; a login over a still-valid cookie calls `end` for the old session before `start` — verify: `tests/api/test_auth.py::test_login_success_sets_session_cookie` (`session` from the double's `session_info`, R-W-1) — evidence: `assert_response_matches(response, "login")` passes; each cookie attribute asserted for both `cookie_secure` values; the double's call order is `end`, `start`.
- [ ] AC-5 [failure/refusal] Wrong username, wrong password, both wrong, and each field an empty string return byte-identical 401 `LOGIN_FAILED` bodies apart from `request_id`, with `field`, `constraint` and `details` null, and both comparisons run on every attempt (WEB-10; SCREEN_SPECS N-28) — verify: `tests/api/test_auth.py::test_login_failed_identical_for_every_cause` (a spy on `hmac.compare_digest` counts two calls per attempt) — evidence: the five bodies compare equal; two comparisons per attempt.
- [ ] AC-6 [failure/refusal] **WF-18 (`login`):** A login body with a missing field, a non-string field or non-JSON text returns 400 `VALIDATION_ERROR` naming the field and rule, never the value — verify: `tests/api/test_auth.py::test_login_malformed_body_is_400` — evidence: three cases pass; a seeded distinctive value is absent from each body.
- [ ] AC-7 [failure/refusal] After `limits.web.login_rejects_per_ip` (10) rejected attempts from one IP inside `login_reject_window_s` (600 s), the next attempt, with the correct pair, returns 429 `LOGIN_RATE_LIMITED` with a `Retry-After` header and `details.retry_after_ms`, writes `auth_event` outcome `rate_limited`, and a different IP still logs in (WEB-4) — verify: `tests/api/test_auth.py::test_login_rate_limited_per_ip` (fake monotonic clock; limits read from the injected `WebLimits`) — evidence: the 11th response is 429 with both retry values; the other IP gets 200; after the window passes the pair works again.
- [ ] AC-8 [negative] The username and password, **right or wrong**, the cookie token and the session secret never appear in any response body, log line, span or DB text: after a correct login, a wrong-password login, a wrong-username login, a rate-limited login and a logout, distinctive values generated at test time are absent from every response body and header except the one `Set-Cookie` that carries the token, from the captured log output, from the in-memory trace sink, and from a text dump of every table in the temp SQLite file (DO-6 CAP-10 *Asserts absent*; DO-6 *Content* "session cookies … Never") — verify: `tests/api/test_auth.py::test_credentials_and_token_absent_from_body_log_span_db` — evidence: absence asserted per value per sink.
- [ ] AC-9 [failure/refusal] A malformed body on any route returns 400 `VALIDATION_ERROR` with `field` and `constraint` set and `details` holding no rejected value; exactly one exception handler renders `ApiError` (the 422 handler builds an `ApiProblem`) — verify: `tests/api/test_app.py::test_validation_error_is_400_without_value` — evidence: a seeded distinctive rejected value is absent from the body and the captured log; registered `ApiError` renderer count asserted equal to 1.
- [ ] AC-10 [invariant] Every response, success or error (200, 204, 303, 400, 401, 403, 404, 410, 429, 503, 5xx), carries `X-Request-ID` equal to the `request_id` in any error body — verify: `tests/api/test_app.py::test_request_id_on_every_response` — evidence: pass for each status the test app produces.
- [ ] AC-11 [invariant] `/healthz` is `async def` and answers 200 while the injected `Heartbeat.fresh(mono)` is true and a non-200 status once it is false; it still answers within the test timeout while every worker thread is blocked, while the unit-of-work double raises on use, and while `ResetGate` is held — verify: `tests/api/test_app.py::test_healthz_reads_heartbeat_not_pool_or_db` — evidence: 200 with a fresh double and non-200 with a stale one; UoW double records zero calls; no wait on the held gate.
- [ ] AC-12 [invariant] Over-limit answers follow web §5's table: each of the six read operations gets 429 `REQUEST_RATE_LIMITED` with `details.retry_after_ms`; `requestPerson` is never limited; `submitTurn` is never answered 429 by the middleware and its `RequestContext.turn_verdict` holds the first refusing scope (`thread`, `session` or `ip`) and `retry_after_ms`; the six-operation set equals `operations_documenting("429")` minus `login` (WEB-3) — verify: `tests/unit/web/test_middleware.py::test_rate_limits_by_operation`, `tests/api/test_openapi_sets.py::test_rate_limit_set_matches_openapi` — evidence: sub-cases pass (read limited, CON-4 unlimited after 10 × the limit, CON-2 verdict exposed with status 200 from a double route); set equality asserted.
- [ ] AC-13 [invariant] The limits admit the decided load shape: 20 conversations at once from one IP and one login, each opening a session and sending turns at SP-1's p50 pace (≈ 255 turns/min [C], WEB-2), are never limited (PRD §5 *Design consequences*: "rate limits … are set above 20") — verify: `tests/unit/web/test_middleware.py::test_limits_admit_twenty_conversations_from_one_ip_and_login` — evidence: 0 limited responses across the scripted burst.
- [ ] AC-14 [invariant] The client IP that keys the IP buckets is the last `X-Forwarded-For` entry when `Settings.trust_proxy_headers` is on and the socket peer when it is off; bucket keys never include the cookie value — verify: `tests/unit/web/test_middleware.py::test_client_ip_and_bucket_keys` — evidence: both settings asserted; the limiter's key set holds no token.
- [ ] AC-15 [invariant] `run_tag` is `eval` or `load` with the request's `X-Meridian-Run-Id` only when `X-Meridian-Eval-Key` matches `Settings.eval_key` (compared with `hmac.compare_digest`); a missing or wrong key, or `eval_key` unset, yields `run_tag = "live"` and `run_id = None`; a matching key with an absent or unknown run tag yields `eval` (WEB-7) — verify: `tests/unit/web/test_middleware.py::test_run_tag_requires_eval_key` — evidence: six sub-cases (no key, wrong key, key unset, eval, load, unknown tag) pass.
- [ ] AC-16 [negative] A seeded eval-key value and a seeded `run_id` sent without the key are absent from response bodies, the captured log and the trace sink — verify: `tests/unit/web/test_middleware.py::test_eval_key_absent_from_outputs` — evidence: absence asserted in all three.
- [ ] AC-17 [negative] The `request` record carries the route template, never the raw path or query string, and the formatter emits only the allow-listed fields of `request`, `auth_event`, `stream_reconnect` and `signal`: a distinctive value placed in a path parameter, a query string and a request body, and an unlisted extra field on a log call, are absent from the captured log — verify: `tests/unit/web/test_logging.py::test_allow_list_formatter_drops_raw_path_query_body_and_extras` — evidence: absence asserted; each record's key set equals web §10's list.
- [ ] AC-18 [invariant] `web/deps.py` declares every provider web §4 lists plus `require_staff`, `owned_thread` and `owned_stream_thread` (R-W-3); each is overridable; an unbound provider raises `RuntimeError("not bound: <name>")` when called and importing the module raises nothing; `get_stream_poll_limiter()` returns the same `CapacityLimiter(4)` object on every call — verify: `tests/unit/web/test_deps.py::test_every_provider_declared_overridable_and_lazy` — evidence: provider names asserted against web §4's list; import succeeds with nothing bound; identity of the limiter asserted.
- [ ] AC-19 [failure/refusal] `require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR)` returns the `StaffActor` the `StaffAccess` double gives for an allowed role, and on a `RoleRefusal` returns 403 `ROLE_NOT_ALLOWED` with `details.role`, `details.needs` in the order passed and `details.reason` `wrong_role` or `role_reset` (MC-4) — verify: `tests/unit/web/test_deps.py::test_require_staff_refusals` — evidence: refusal bodies pass `assert_response_matches` against an operation documenting `RoleNotAllowed`; `needs` equals `["representative", "supervisor"]`.
- [ ] AC-20 [failure/refusal] `owned_thread` returns the `ThreadId` for this session's conversation; answers 410 `SESSION_ENDED` with `details.reason` for an `EndedThread` whose `demo_session` is this session's; and answers byte-identical 404 `SESSION_NOT_FOUND` bodies (apart from `request_id`) for a malformed id, an unknown id, another session's live thread and another session's ended thread (WEB-34, MC-16); and `owned_stream_thread` answers the identical 404 `SESSION_NOT_FOUND` for this session's ended thread, through the same single lookup (web §4, R-W-3) — verify: `tests/unit/web/test_deps.py::test_owned_thread_404_410` and `::test_owned_stream_thread_maps_ended_to_404` (UoW double) — evidence: the four 404 bodies compare equal; the 410 carries `reason: "demo_reset"`; the `owned_stream_thread` 404 body equals an unknown thread's apart from `request_id`, with one lookup recorded.
- [ ] AC-21 [failure/refusal] While `ResetGate` is held, each of the eight operations web §7 lists answers 503 `RESET_IN_PROGRESS` with `details.retry_after_ms: 5000` at once; another operation waits for `wait_clear` and then answers from the post-reset state; a second `hold()` raises `ResetAlreadyRunning`; the eight-operation set equals `operations_documenting("503")` filtered to `RESET_IN_PROGRESS` — verify: `tests/unit/web/test_reset_gate.py::test_reset_gate_503_wait_and_double_hold`, `tests/api/test_openapi_sets.py::test_reset_503_set_matches_openapi` — evidence: eight 503s with no wait; a non-503 operation during a 1 s hold answers after the release; set equality asserted.
- [ ] AC-22 [invariant] `logout` returns 204 with `Set-Cookie: mhc_session=…; Max-Age=0` and calls `LoginSessions.end` for the token; a second logout is also 204; the next request with the old cookie gets 401 `UNAUTHENTICATED` — verify: `tests/api/test_auth.py::test_logout_clears_cookie_and_ends_session` — evidence: pass; the double records the ended token.
- [ ] AC-23 [invariant] The lifespan builds the container once and closes it once on shutdown; no module-level client, settings or limiter singleton exists in `src/meridian/web/` — verify: `tests/api/test_app.py::test_lifespan_builds_and_closes_container` plus `grep -rn "^[a-z_]* = .*(" src/meridian/web/` reviewed in the code review — evidence: build and close counters equal 1; the grep lists only constants (header names, operation sets).
- [ ] AC-24 [invariant] `openapi_check.py` fails a response whose status is undocumented for the operation, whose body breaks the schema, or whose `error.code` is outside the enum, and passes the OpenAPI's own examples; `Contract.error_codes` equals AEA-02's `ApiErrorCode` HTTP members (WEB-9); and loads the OpenAPI with `ContractLoader` (web §13, R-W-9): the `STARTED` example's `greeting.at` is a `str`, the `BurningCheckBlock` option `"yes"` stays `"yes"`, and `getStaffing`'s 200 example names are `"ON"` and `"OFF"` — verify: `tests/api/test_openapi_check.py::test_validator_rejects_and_accepts`, `tests/api/test_openapi_check.py::test_error_codes_match_openapi`, `tests/api/test_openapi_check.py::test_loader_keeps_yaml12_strings` — evidence: three rejections raise `AssertionError` naming the OpenAPI `info.version`; examples pass; set equality asserted; the three named values with type `str`.
- [ ] AC-25 [capture] CAP-10 (WF-18): driving the real `login` / `logout` routes and the middleware through `TestClient` in CAP-10's order (log in with the right pair, log in with a wrong password, log out, then call a protected route without the session) produces one `request` record per call with exactly web §10's fields, one `auth_event` per attempt with outcomes `ok`, `rejected`, `logged_out` in order and the opaque `session_id` on `ok` and `logged_out` (never the username, password or token), and the protected call refused with 401 `UNAUTHENTICATED` — verify: `tests/api/test_auth.py::test_cap10_login_records_captured` — evidence: four `request` records, three `auth_event`s in that order, the 401 body; field sets equal the allow-list.
- [ ] AC-26 [capture] `/healthz` (WF-17) is served from the heartbeat without a session and writes its `request` record (route `/healthz`, `caller_role: "anonymous"`) — verify: `tests/api/test_app.py::test_healthz_request_record` — evidence: one record, status 200.
- [ ] AC-27 [invariant] `load_contract()` reads the OpenAPI as YAML 1.2 with a loader that keeps timestamps and the YAML 1.1 words `yes`, `no`, `on`, `off`, `ON`, `OFF` as strings (a plain `yaml.safe_load` turns 371 example timestamps into `datetime` objects and those words into booleans), while `true` and `false` stay booleans: the `startChatSession` `STARTED` example's `greeting.at` loads as the string `2026-10-16T14:20:00-05:00`, and a walk over the whole loaded document finds no `datetime` or `date` value (AEA-23-1; web §13; complements AC-24's three named values) — verify: `tests/api/test_openapi_check.py::test_contract_keeps_yaml_strings` — evidence: 0 `datetime`/`date` instances; the named value printed with its type `str`.
- [ ] AC-28 [failure/refusal] A refusal tells the browser what to re-read: every `ROLE_NOT_ALLOWED` that `require_staff` raises carries `details.role` = the role the session holds **on this request** (resolved per request, never cached between requests), `details.needs` in x-roles order and `details.reason`; when the `StaffAccess` double changes the session's role between two requests, the second 403 names the new role (AEA-23-2; web §3; staff.md §2) — verify: `tests/unit/web/test_deps.py::test_role_refusal_names_current_role` — evidence: two 403 bodies with the two roles, both valid against `RoleNotAllowed`.
- [ ] AC-29 [contract] `tests/contract/cases/auth.py` holds the server cases for the operations this issue serves, `login` and `logout`: preconditions, every named request example, and each documented error status the route can produce (`login`: 400, 401 `LOGIN_FAILED`, 429 `LOGIN_RATE_LIMITED`; `logout`: 401) (AEA-23-3; slice plan §0a, per-route contract case files) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "login or logout" -rs` once AEA-59's runner is merged — evidence: one pass per case; no `route not registered` or `not bound` skip for these two operations.
- [ ] AC-30 [invariant] The container overrides are test-only (web §15, R-W-8): `create_app()` with no arguments builds no override; the lifespan passes `overrides` to the container exactly once; `grep -rn "ContainerOverrides(" src/` finds nothing — verify: `tests/api/test_app.py::test_overrides_test_only` — evidence: the container double receives `overrides=None` from `create_app()` and the given object from `create_app(settings, overrides=…)`, once each; the grep output is empty.
- [ ] AC-31 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-23.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1 (the login, the guard redirect, the 401s) and J-8 (role refusals) as the journeys that will exercise this code once AEA-57 and AEA-52 land (AEA-57 is blocked by this issue, so this issue cannot run them itself), so the seam audit knows where to look (pattern C, `docs/plans/ux-join/backend-amendments.md` §3) — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-32 [capture] **WF-18 (status values and no outbound call; OBS-13, OBS-29):** over AC-25's CAP-10 sequence plus a 400 malformed body (AC-6) and a 429 (AC-7), each `request` record's `status` equals the HTTP status the response carried; a `login` forced to fail inside the route (the `LoginSessions` double raising on `start`) answers 500 `ApiError` and its `request` record carries `status` 500 and a non-empty `error_kind`, while no record of a non-5xx call carries `error_kind`; and a socket guard that fails the test on any non-loopback `connect` sees none during login, the wrong-password login, logout and the 500 — verify: `tests/api/test_auth.py::test_wf18_status_values_and_no_outbound` — evidence: the (response status, record status, `error_kind`) triple per call printed; 0 outbound connects.
- [ ] AC-33 [capture] **WF-17 (`/healthz` status values; OBS-13):** the `/healthz` `request` record's `status` equals the response status with a fresh heartbeat (200) and with a stale one (AC-11's non-200); a `/healthz` call whose injected `Heartbeat` double raises answers 500 and its record carries `status` 500 and a non-empty `error_kind`; a record carries `error_kind` only when its status is 5xx (DO-6 *Status values*) — verify: `tests/api/test_app.py::test_healthz_status_values` — evidence: the three records printed with status and `error_kind`.
- [ ] AC-34 [invariant] The test-only wall-clock override reaches the one wall clock (Innocent D-13, 2026-10-21; web §15): `create_app(settings, overrides=ContainerOverrides(wall_clock=fake))`, where `fake` is a callable returning a fixed aware UTC time and then that time + 43,200 s, makes `get_wall_clock()` return `fake` itself, so `LoginSessions.resolve` (the double) receives exactly the fake's times and a session the double expires at the second time answers 401 `UNAUTHENTICATED` `details.reason: "expired"`; the demo clock (`getDemoClock`'s source) reads the same before and after; `create_app()` with no overrides, and `ContainerOverrides()` with `wall_clock=None`, give a `get_wall_clock()` whose value is within 2 s of `datetime.now(UTC)` — verify: `tests/api/test_app.py::test_wall_clock_override_reaches_get_wall_clock` — evidence: identity of the bound callable asserted; the two `now` values the double recorded printed; the 401 body; the default's delta printed.
- [ ] AC-35 [negative] The wall clock cannot be set from outside code: `Settings.model_fields` holds no clock, time or `now` field; with every env variable the test sets that names a clock (`MERIDIAN_WALL_CLOCK`, `MERIDIAN_NOW`, `MERIDIAN_FAKE_TIME`, set to a year-2000 time) `create_app()`'s `get_wall_clock()` still reads real time; and requests carrying a time in a header (`X-Meridian-Now`, `X-Meridian-Wall-Clock`), a query string (`?now=`, `?wall_clock=`) or a JSON body, with and without a valid eval key, leave `get_wall_clock()()` within 2 s of `datetime.now(UTC)` and the session unexpired; no registered route's path or operation names a wall clock (only CON-8's demo clock exists) — verify: `tests/api/test_app.py::test_wall_clock_not_settable_from_settings_env_or_http`, plus `grep -rn "wall_clock" src/meridian/` reviewed in the code review (only `web/app.py`, `web/deps.py` and the container's pass-through) — evidence: the field list, the env and per-request cases printed with the clock delta; the route list; the grep output.
- [ ] AC-36 [regression/context] Same change updates: `.claude/reference/area-map.md` (A8 web-shell rows for this issue's files, planned → actual + commit), `.claude/state/icm-progress.md` (the affected row's evidence link), DO-3 §3 `web/` rows and the `services/reset_gate.py` row (status only), and DO-6's WF-18 / CAP-10 rows only if the built record names differ from web §10 (status line, no redesign) — verify: `git diff --name-only` — evidence: those paths in the diff, nothing under `docs/ux/**`.

### Observability

- Responsibilities: **WF-18** (demo login and logout, CON-22, plus the middleware session check; registered in DO-6
  2026-10-21): a `request` record per call and an `auth_event` per attempt with outcome `ok` / `rejected` /
  `rate_limited` / `logged_out` and its time, correlated by `request_id` and the opaque demo session id minted at login;
  never the username, password or token (DO-6 WF-18; web §10; MC-9). **WF-17** (`/healthz`): served from the in-memory
  heartbeat, with its `request` record. For every HTTP call of WF-1…WF-6 and WF-19: the `request` record (route
  template, status, duration, caller role, `thread_id`) through the allow-list formatter and `X-Request-ID` on every
  response; `run_tag` / `run_id` derived only with the eval key so the `turn` and `conversation` records downstream are
  tagged `live`, `eval` or `load` correctly (DO-6 *Correlation*). No credential, cookie, eval key or request body in any
  log or trace (DO-6 *Content*).
- Capture evidence: AC-25 drives the real login route per CAP-10 (WF-18); AC-26 covers WF-17 (the restart records of
  CAP-9 are AEA-32's and AEA-50's); AC-32 (WF-18) and AC-33 (WF-17) hold `request.status` to DO-6's status values;
  AC-8, AC-16 and AC-17 are the negative halves. End-to-end CAP-1 and CAP-4 (AEA-51,
  AEA-52) rely on these records.

### Evaluation

- Checks: no DO-5 suite is added. This issue keeps three runs admissible: E-8's 20-at-once load from one IP and one
  login is never rate limited (AC-13); eval and load traffic is told apart from live traffic only with the eval key
  (AC-15), which CAP-7 asserts; and WF-17's health check answers from the heartbeat, so SCR-10's "last health-check
  restart" line counts real hangs only (AC-11).
- Expected-answer authority: DO-6 *Correlation across boundaries* (eval-key rule), PRD §5 *Load* ("rate limits … are
  set above 20"), DO-1 §8.2 *Process hang* and DO-3 §2.3 rule 3 (what a healthy `/healthz` means).

### Metrics

- References: M-28 (health-check restarts: WF-17 must answer truthfully, so a restart means a real hang); M-22, M-3,
  M-18 (exclude `eval` and `load` tags, so the tag must be right); M-24 (`degrade_reason` `rate_limit` comes from the
  verdict this issue exposes; `auth_event` `rate_limited` counts R-41 refusals).
- Acceptance conditions: each stays computable from records this issue emits or tags (AC-11, AC-12, AC-15, AC-25,
  AC-26); no target is set here.

### Blocked by

AEA-01 (`policy/limits.py` `Limits.web`, container stubs, dev dependencies; the container builder's pass-through
`overrides` keyword, R-W-8), AEA-02 (`config.py` `Settings`, `ApiErrorCode`, ID types, `domain/staff.py` incl.
`SessionInfoData`, R-W-1), AEA-04 (LOG profile for the formatter).

Not merge blockers (later-wave evidence only): AC-29's strict contract run needs AEA-59's runner (wave 2), and AC-31's
journey record names *Blocked by* AEA-57 (wave 2) and AEA-52 (wave 3); both AEA-57 and AEA-59 are blocked by this issue,
so neither becomes an edge into it.

### Agent handoff

- Area / owner: A8 web shell (DO-3 §3 `web/`); slice plan AEA-23 (plus `services/reset_gate.py`, MC-27); also
  `tests/contract/cases/auth.py`, the server contract cases for `login` and `logout` (AC-29; AEA-59 owns the runner).
- Contracts and shared surfaces: consumes `Settings` (AEA-02, graph-core §12), `Limits.web` (AEA-01, web §5),
  `ApiErrorCode`, `RequestId` and `domain/staff.py` types (AEA-02), the LOG redaction profile (AEA-04), `Heartbeat`
  (AEA-32, injected), `StaffSessionStore` as `LoginSessions` / `StaffAccess` (AEA-44, injected double). Produces
  `create_app` and `ContainerOverrides` (AEA-57's journey launcher, AEA-51's `register_graph`; web §15, R-W-8),
  `ApiProblem`, the gate, `PublicPaths` (AEA-49 registers into it), the limiter and its verdict (AEA-40,
  AEA-43), the run tag, `owned_thread` (AEA-40, 42), `owned_stream_thread` (AEA-41, R-W-3), `ResetGate` (AEA-31, AEA-43), `get_wall_clock` (every service
  wired by the container), `openapi_check.py` (AEA-40…AEA-49, AEA-52) and **every provider in `web/deps.py`** for
  AEA-40…AEA-49. Must not edit: `web/container.py` outside its own `register_` hunk, `domain/*`, `config.py`,
  `policy/limits.py`, any other route or schema file, the OpenAPI or `UI_CONTRACTS.md`.
- Scope boundary / refusal: no CON-1…CON-21 route, no role switch (`getSession`, `listDemoRoles`, `switchRole` are CON-10,
  AEA-44), no session storage (AEA-44's `repos_staff` over AEA-10's `90_staff.sql`), no static file serving or `/login`
  page (AEA-49), no chat `RATE_LIMITED` notice (AEA-40), no reset throttle answer (AEA-43 applies `RESET_IP`). A needed
  OpenAPI change stops the issue.
- Wave and gates: wave 1; no human gate. Credentials, session secret and eval key come from Railway variables at deploy
  (AEA-09); tests use placeholder settings generated at run time.
- Lane: build-loop — it adds source and tests the app runs.
- Risk: security (`risk::security`) — a bug here opens every route without the login, leaks the demo credentials, the
  session token or the eval key, allows an open redirect, or lets public traffic tag itself `eval` and drop out of the
  live numbers.
- Awaiting Innocent: WEB-1 — built on the recommended option (A: `/login` plus `/assets/` and `/fonts/` public, registered
  by AEA-49); if he picks C (whole app shell public), the page-path 303 of gate step 3 moves into the app and AC-2 is
  dropped; if B, nothing in this issue changes.
- Entry points added or changed: WF-18 (CON-22 `login`/`logout` and the middleware session check; capture CAP-10), WF-17 (`/healthz`).

- Resolved R-W-1 (web §2; `docs/plans/7b-decisions/residuals-web.md`): `LoginSessions` gains `session_info(session) ->
  SessionInfoData`, `SessionInfoData` lives in `domain/staff.py` (AEA-02, staff.md §1), and `login` builds
  `LoginResponse.session` from it (see *What to build* item 5 and AC-4).
- Open with Innocent, not applied here: R-W-12 (should a chat resume after the reviewer signs in again?). Built on the
  current contract: every login starts a new `LoginSession` and `owned_thread` answers 404 for an earlier session's
  thread (web §4 note). If he picks B or C, `owned_thread`'s ownership rule and AC-20 change.
