## [AEA-43] customer API: inbox, staffing, clock read, reset (CON-6…CON-9)

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

> **US-25:** "As a **reviewer**, I need a demo (reached with the demo login) where the date, the empty staffing, the code
> inbox and the "recorded, not sent" follow-ups are all labelled as demo simulations, and a one-click role switch that
> lets me play the representative without separate accounts, so that I can "watch the agent escalate" and judge it
> honestly."
> **US-8:** "As a **homeowner** asking about my bill, I need to receive a one-time code at the phone or email on my
> account and type it in the chat, so that nobody else can read my account by guessing my name."

The demo-control routes in `web/routes/demo.py` with their wire models in `web/schemas/demo.py`, proven against the
OpenAPI with services replaced by doubles through `web/deps.py` overrides. Every operation accepts every signed-in role
(x-roles: all four; R-48) and takes the session from AEA-23's middleware, never from a query, header or body value.

- **`listDemoInbox`** (CON-6, `GET /api/demo/inbox`): `IdentityService.inbox(str(session.session_id),
  now=DemoService.clock_view().now)` (DO-4 §14; stage7/graph-tools.md §5; stage7/web.md §4 "routes pass
  `str(session.session_id)`"). Each `InboxMessage.code` is a `SecretStr`, unwrapped **only while serialising** the
  response; `body` is rendered from `policy/texts.py`: `INBOX_CODE_BODY` with the digits, or `INBOX_CODE_GONE` and code
  `"······"` when `code` is `None` (stage7/data.md §2; graph-tools C-10). The only response in the contract set that
  carries a code; its body is never logged.
- **`getStaffing` / `setStaffing`** (CON-7, `GET` / `PUT /api/demo/staffing`): `DemoService.staffing()` and
  `DemoService.set_staffing(mode, request_id=ctx.request_id, role=session.role)` (stage7/cases.md §6), returned unchanged
  as `Staffing` / `StaffingResponse` (`converted_cases` from the service; same mode → no write, 0).
- **`getDemoClock`** (CON-8 read, `GET /api/demo/clock`): `DemoService.clock_view()` copied unchanged: `label` and
  `date_label` come from the one formatter `format_clock` (stage7/cases.md §6; WEB-25); the route reads no clock and
  formats nothing. This router registers **GET only** on that path; `POST` is AEA-47's `routes/staff_clock.py`.
- **`resetDemo`** (CON-9, `POST /api/demo/reset`): `{confirm: true}` → `ResetService.reset(get_wall_clock()(),
  request_id=ctx.request_id, session_id=session.session_id, role=session.role)` (stage7/cases.md §7; stage7/web.md §7;
  WEB-26, MC-19, MC-20). `ResetDone` → 200 `ResetResponse` (`ok`, `open_chats_ended`, `roles_reset`, `clock`);
  `ResetAlreadyRunning` (raised by `ResetGate.hold()`, `services/reset_gate.py`) → 409 `RESET_IN_PROGRESS` with
  `details.retry_after_ms`; `ResetFailed` → 500 `RESET_FAILED`. Per-IP throttle (WEB-27): the `RESET_IP` bucket
  (`limits.web.resets_per_ip` = 10 per `limits.web.reset_window_s` = 600 s [A], stage7/web.md §5) is checked through
  `get_rate_limiter()` before the service is called, and each reset run is counted with `RateLimiter.record_reset(ip,
  now)`; over the limit → 409 `RESET_IN_PROGRESS` with `details.retry_after_ms`, the operation's only documented refusal.
- **During a reset** (stage7/web.md §7, WEB-13): AEA-23's middleware answers 503 `RESET_IN_PROGRESS`
  (`retry_after_ms: 5000`) for `listDemoInbox` and `setStaffing` (the two here that document 503); `getStaffing` and
  `getDemoClock` wait up to `limits.web.reset_wait_s` (5 s [A]) and then answer from the post-reset state. This route
  file adds no reset check of its own.
- **Rate limits** (stage7/web.md §5, WEB-3): `listDemoInbox`, `getStaffing`, `getDemoClock` answer 429
  `REQUEST_RATE_LIMITED` from the middleware's read buckets; `setStaffing` is never limited.

**Example pair (tied to WP-2).** WP-2's customer MHC-10002 has been located; the chat shows the code card with the hint
"the phone ending in 02". The reviewer opens the inbox tab in the same browser: `GET /api/demo/inbox` with that login
session's `mhc_session` → 200 (OpenAPI example `ONE_ACTIVE`): one message, `to_masked` "···02", `body` "Your Meridian
Home Comfort verification code is <digits>. It expires in 10 minutes.", `code` the six digits, `status` "active",
`expires_at` ten minutes after `at`. A second reviewer logged in separately gets `{"messages": []}` (example `EMPTY`).
Later the reviewer resets: `POST /api/demo/reset` `{"confirm": true}` → 200 (example `RESET`): `ok: true`,
`open_chats_ended`, `roles_reset`, and `clock` back to the demo start, `DEMO_START` = Fri 2026-10-16 10:00 Chicago
(stage7/cases.md §1.1), `date_label` "Fri Oct 16, 2026 (demo date)".

**Produced for other issues:** CON-6, CON-7, CON-8 read and CON-9 for AEA-51 (code read from the inbox in CAP-1),
AEA-52 (real services behind CON-7 and CON-9; WEB-33) and AEA-55; AEA-24's harness reads codes from CON-6.

### Source

- PRD R-3, R-15, R-16, R-19, R-30, R-33, R-34, R-40, R-48; US-8, US-25; WP-2.
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml` (read-only): `listDemoInbox` (200 / 401 / 429 / 503),
  `getStaffing` (200 / 401 / 429), `setStaffing` (200 / 400 / 401 / 503), `getDemoClock` (200 / 401 / 429), `resetDemo`
  (200 / 400 / 401 / 409 / 500); schemas `InboxResponse`, `InboxMessage` ("DATA CLASS: secret. This is the ONLY response
  that carries a code."), `Staffing`, `StaffingRequest`, `StaffingResponse`, `DemoClock`, `ResetRequest` (`confirm`
  const true), `ResetResponse`, `ApiError`.
- `docs/design/contracts/stage7/web.md` §1 (`ApiProblem`), §4 (`RequestContext`, providers, `get_wall_clock`), §5 (rate
  limits, `RESET_IP`, `record_reset`), §7 (`ResetGate`, the 503 set, the wait), §10 (`request` record), §13
  (`openapi_check.py`). Decisions WEB-3, WEB-13, WEB-24, WEB-25, WEB-26, WEB-27, WEB-33, WEB-36
  (`docs/plans/7b-decisions/web.md`); merge MC-19, MC-20.
- `docs/design/contracts/stage7/cases.md` §1.1 (`DEMO_START`, `demo_events`, `reset_events`), §1.3 (what a reset
  clears), §6 (`DemoService`, `format_clock`), §7 (`ResetService.reset`, `ResetDone`, `ResetFailed`).
- `docs/design/contracts/stage7/graph-tools.md` §5 (`InboxMessage`, `IdentityService.inbox`, where the digits live, GRT-2);
  `stage7/data.md` §2 (`INBOX_CODE_BODY`, `INBOX_CODE_GONE`); `stage7/staff.md` §1 (`LoginSessionId`, `DemoRole`).
- DO-4 §11, §14 (`IdentityService.inbox`). DO-2 §8.2 *Demo reset (CON-9)*, §10 *Identity code*.
- DO-6 WF-3, WF-5, WF-15, *Content and redaction* (codes row), CAP-1, CAP-5, CAP-9. DO-7 M-22, M-27.
- `UI_CONTRACTS.md` CON-6…CON-9, *Data classes* (D3), *Access* (R-48).
- Slice plan §0a (journey map, J-3 and J-8) and rule `.claude/rules/integrated-journeys.md` §3–§4; UX-join amendments
  `docs/plans/ux-join/backend-amendments.md` AEA-43-1, AEA-43-2 and §3.
- Slice plan row AEA-43; area-map row A8 Customer API; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "The interface must be interactive: a reviewer should be able to type questions, probe edge
  cases, and watch the agent escalate." (briefing Part B §6); touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `listDemoInbox` 200 bodies validate for the `ONE_ACTIVE`, `USED_AND_EXPIRED` and `EMPTY` shapes; an active message's `body` is `INBOX_CODE_BODY` with its digits, a message whose `code` is `None` shows `INBOX_CODE_GONE` and code `"······"`; an empty list is a 200 — verify: `tests/api/test_demo_routes.py::test_inbox_matches_openapi` (`assert_response_matches(response, "listDemoInbox")`; digits generated at test time) — evidence: three bodies validate; body texts equal the two `policy/texts.py` entries.
- [ ] AC-2 [invariant] (frozen first) The inbox is scoped to the login session: the route passes `str(session.session_id)` from the middleware's `LoginSession` to `IdentityService.inbox` and nothing taken from a query parameter, header or body; with two login sessions each sees only its own messages — verify: `tests/api/test_demo_routes.py::test_inbox_scoped_to_login_session` (double keyed by session; a `?demo_session=` query and an extra header tried) — evidence: session A's digits absent from session B's body and vice versa; the double received only the cookie's session id.
- [ ] AC-3 [negative] (frozen first) The code never reaches a log or trace (D3; DO-6 *Content and redaction*): a request returning a code generated at test time leaves it in the response body only — no captured log record (including the `request` record), no trace-double span, and no `repr` of the `InboxMessage` holds it — verify: `tests/api/test_demo_routes.py::test_inbox_code_never_logged` (caplog + trace double) — evidence: digits present in the body, absent from every record; `to_masked` is the only recipient form.
- [ ] AC-4 [invariant] `getStaffing` validates against `Staffing` in both modes; `setStaffing` validates against `StaffingResponse`, calls `DemoService.set_staffing(mode, request_id=<the request's id>, role=<the session's role>)`, and passes `converted_cases` through unchanged, including 0 when the mode is unchanged — verify: `tests/api/test_demo_routes.py::test_staffing_matches_openapi` — evidence: `TURNED_ON`, `TURNED_OFF_WITH_WAITING` and unchanged shapes validate; call arguments asserted.
- [ ] AC-5 [invariant] `getDemoClock` returns `DemoService.clock_view()` unchanged and formats nothing: with the double holding `DEMO_START` (2026-10-16 10:00 −05:00) and labels "Fri Oct 16, 2026 · 10:00 am" / "Fri Oct 16, 2026 (demo date)", the body equals them whatever the wall clock reads; the route registers GET only on `/api/demo/clock` — verify: `tests/api/test_demo_routes.py::test_clock_is_demo_clock_and_get_only` plus `grep -n "strftime\|datetime.now" src/meridian/web/routes/demo.py src/meridian/web/schemas/demo.py` — evidence: body equals the double's values; the router lists only `GET` for that path; grep prints nothing.
- [ ] AC-6 [invariant] (frozen first) `resetDemo` with `{"confirm": true}` calls `ResetService.reset(<wall now>, request_id=<the request's id>, session_id=<session.session_id>, role=<session.role>)` and returns 200 `ResetResponse` with `ok`, `open_chats_ended`, `roles_reset` and `clock` from `ResetDone` — verify: `tests/api/test_demo_routes.py::test_reset_matches_openapi` (recording double; fake wall clock) — evidence: body validates; the double received the request id, the caller's session id and role, and the fake wall time.
- [ ] AC-7 [failure/refusal] **WF-15** (CON-9 `resetDemo`): `resetDemo` refusals: `confirm` false or missing → 400 `VALIDATION_ERROR` field `confirm`, no service call; `ResetAlreadyRunning` → 409 `RESET_IN_PROGRESS` with `details.retry_after_ms`; `ResetFailed` → 500 `RESET_FAILED` — verify: `tests/api/test_demo_routes.py::test_reset_refusals` — evidence: three bodies validate against their documented responses.
- [ ] AC-8 [failure/refusal] (frozen first) **WF-15** (CON-9 `resetDemo`; R-41): Reset throttle (WEB-27): ten resets from one client IP within 600 s succeed; the eleventh answers 409 `RESET_IN_PROGRESS` with a positive `details.retry_after_ms` and does not call `ResetService.reset`; another IP is unaffected — verify: `tests/api/test_demo_routes.py::test_reset_throttle_per_ip` (real `RateLimiter`, fake time) — evidence: eleventh body validates; double call count 10.
- [ ] AC-9 [failure/refusal] While a fake `ResetGate` is held, `listDemoInbox` and `setStaffing` answer 503 `RESET_IN_PROGRESS` with `details.retry_after_ms: 5000` from the real AEA-23 middleware and their services are not called; `getStaffing` and `getDemoClock` wait and answer 200 once the gate clears within 1 s — verify: `tests/api/test_demo_routes.py::test_reset_gate_answers` — evidence: two 503 bodies validate against `ResetInProgress`; two 200 bodies after release.
- [ ] AC-10 [failure/refusal] **WF-5** (CON-7 `setStaffing`): `setStaffing` with `{"mode": "maybe"}` → 400 `VALIDATION_ERROR`, field `mode`; the value "maybe" appears in neither the body nor any captured log record — verify: `tests/api/test_demo_routes.py::test_staffing_validation_error` (caplog) — evidence: body validates; "maybe" absent.
- [ ] AC-11 [failure/refusal] **WF-3** (CON-6 `listDemoInbox`): with the middleware's read buckets exhausted, `listDemoInbox` answers 429 `REQUEST_RATE_LIMITED` with `details.retry_after_ms` (WEB-3); the same check for the staffing and clock reads, and `setStaffing` never limited, is AC-18 (WF-5) — verify: `tests/api/test_demo_routes.py::test_inbox_request_rate_limited` — evidence: the 429 body validates against `TooManyRequests`.
- [ ] AC-12 [invariant] **WF-15** (CON-9 `resetDemo`) and **WF-5** (CON-7 `getStaffing`, `setStaffing`; CON-8 `getDemoClock`): Login gate and roles: each of these four operations answers 401 `UNAUTHENTICATED` without `mhc_session` (real AEA-23 middleware) and succeeds for each of the four roles, customer included (no `require_staff`, no `ROLE_NOT_ALLOWED`; R-48); the same check on `listDemoInbox` is AC-17 (WF-3) — verify: `tests/api/test_demo_routes.py::test_login_gate_and_any_role` — evidence: one 401 body per operation (four); 2xx under each role.
- [ ] AC-13 [capture] Driving each entry point through the app the container builds leaves one `request` record per call (route template, status, `caller_role`, `request_id` equal to `X-Request-ID`) for WF-3 (`listDemoInbox`), WF-5 (`getStaffing`, `setStaffing`, `getDemoClock`) and WF-15 (`resetDemo`); the identifiers the services need for their own records reach them (`set_staffing` gets `request_id` and `role` for its `demo_event`; `reset` gets `request_id`, `session_id`, `role` for its `reset_event`) — verify: `tests/api/test_demo_capture.py::test_demo_entry_points_emit_records` — evidence: five records printed; the doubles' recorded arguments. The `demo_event` row (CAP-5, AEA-52), the code-sent event (CAP-1, AEA-51) and the `reset_event` row (CAP-9, AEA-50) are proven at those issues.
- [ ] AC-14 [invariant] The route never sends dots as an active code: a message the service returns with `code=None` is serialised with `status: "expired"`, code `"······"` and `INBOX_CODE_GONE`, even if a double returns it as `active`; a held code keeps `active` (AEA-43-1; customer audit A-6, with AEA-27-1) — verify: `tests/api/test_demo_routes.py::test_inbox_code_gone_is_expired` — evidence: the two bodies validate against `listDemoInbox`; statuses `expired` and `active`.
- [ ] AC-15 [contract] `tests/contract/cases/demo.py` holds the server cases for `listDemoInbox`, `getStaffing`, `setStaffing`, `getDemoClock` and `resetDemo`: preconditions, every named request example, and each documented error status the routes can produce (429 on the three reads that document it, 400 on `setStaffing` and `resetDemo`, 503 `RESET_IN_PROGRESS`, 409 and 500 on `resetDemo`) (AEA-43-2) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "listDemoInbox or Staffing or getDemoClock or resetDemo" -rs` once AEA-59's runner is merged — evidence: one pass per case.
- [ ] AC-16 [journey] Extends J-3 and J-8 (slice plan §0a journey map; both are proposed additions to the map, from the join audits): J-3, SCR-2's inbox lists the sent code as `active`, then `used`; J-8, `resetDemo` answers a valid `ResetResponse` and the staffing and clock reads return to their defaults; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_43.py` and `tests/journeys/j8/test_aea_43.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_43.py tests/journeys/j8/test_aea_43.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57, AEA-51 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-43.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-17 [failure/refusal] **WF-3** (CON-6 `listDemoInbox`; R-48, OBS-13): without `mhc_session`, `listDemoInbox` answers 401 `UNAUTHENTICATED` from the real AEA-23 middleware and the `IdentityService.inbox` double records no call; signed in under each of the four roles it answers 200; every call's `request` record has `status` equal to the HTTP status it answered (200, 401, a 429 with the read bucket exhausted, a 503 with the `ResetGate` held), and a forced 5xx (the inbox double raising) answers 500 and its `request` record carries `error_kind`, with no code digits in any record (AC-3) — verify: `tests/api/test_demo_capture.py::test_wf3_inbox_login_gate_and_request_status` — evidence: the 401 body validates against `Unauthenticated`; 200 under each role; each recorded `status` printed beside the response status; `error_kind` on the 500 record.
- [ ] AC-18 [failure/refusal] **WF-5** (CON-7 `getStaffing`, `setStaffing`; CON-8 `getDemoClock`; R-41, OBS-13): with the middleware's read buckets exhausted, `getStaffing` and `getDemoClock` answer 429 `REQUEST_RATE_LIMITED` with `details.retry_after_ms`, while `setStaffing` is never limited and answers 200 (WEB-3); every call's `request` record has `status` equal to the HTTP status it answered (the two 429s, the 200, and the 400 of a `{"mode": "maybe"}` body), and a forced 5xx (the `DemoService.staffing` double raising on `getStaffing`) answers 500 and its `request` record carries `error_kind` — verify: `tests/api/test_demo_capture.py::test_wf5_read_limits_and_request_status` — evidence: two 429 bodies validate against `TooManyRequests`; `setStaffing` 200; each recorded `status` printed beside the response status; `error_kind` on the 500 record.
- [ ] AC-19 [capture] **WF-15** (CON-9 `resetDemo`; OBS-13): each `resetDemo` call's `request` record has `status` equal to the HTTP status it answered: 200 (`ResetDone`), 400 (`confirm` false), 409 (`ResetAlreadyRunning`, and the throttled eleventh reset of AC-8) and 500 (`ResetFailed`); only the 500 record carries `error_kind` — verify: `tests/api/test_demo_capture.py::test_wf15_reset_request_status` — evidence: the recorded statuses printed beside the response statuses; `error_kind` on the 500 record only.
- [ ] AC-20 [regression/context] Same change updates `.claude/reference/area-map.md` row A8 (`web/routes/demo.py`, `web/schemas/demo.py` planned → actual + commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link), DO-3 §3 lines for those two files marked built — verify: `git diff --name-only` — evidence: the three docs in the diff, only this issue's rows changed.

### Observability

- Responsibilities: for WF-3, WF-5 and WF-15 (DO-6 registry), preserve the middleware's `request` record on every entry point; pass the request id and the caller's session id and role into `DemoService.set_staffing` (its `demo_event`, WF-5) and `ResetService.reset` (its `reset_event` "who asked", WF-15; MC-9, MC-19); never log, trace or `repr` the inbox code or body (D3; WF-3's code-sent event keeps hash and expiry only, AEA-27).
- Capture evidence: AC-13 drives the five real entry points; AC-17 (WF-3), AC-18 (WF-5) and AC-19 (WF-15) check each call's `request.status` and `error_kind` on a 5xx (OBS-13); AC-3 (the code) and AC-10 (a rejected value) are the negative checks; AC-14 keeps a code the process no longer holds from being shown as `active`.

### Evaluation

N/A — reading the inbox decides nothing, demo controls change the simulation rather than an outcome, and a reset
restores state; DO-6 marks WF-3, WF-5 and WF-15 evaluation `n/a` for exactly these reasons, and no DO-5 suite scores
these operations (AEA-24's harness only reads codes through CON-6).

### Metrics

- References: M-22 (volume, segmented staffed vs unstaffed) and M-27 (unowned and overdue cases), indirectly; WF-3, WF-5 and WF-15 inherit no metric (DO-6 `n/a`).
- Acceptance conditions: this route computes no metric. Staffing changes reach `demo_event` with request id and role (AC-4, AC-13), so M-22 can be segmented staffed vs unstaffed; a reset reaches `reset_event` with who asked (AC-6, AC-13), so a drop to zero on SCR-10 is explained (DO-6 WF-15). No target is set here.

### Blocked by

AEA-23 (slice plan row AEA-43).

Evidence only, not a merge edge (wave unchanged): AC-15's strict run waits for AEA-59's runner, and AC-16's journey
record stays `mock-tested` with *Blocked by* AEA-57, AEA-51 and AEA-52 until they land (`integrated-journeys.md` §4).

### Agent handoff

- **Area / owner:** A8 Customer API; files `src/meridian/web/routes/demo.py`, `src/meridian/web/schemas/demo.py`, this
  issue's `register_<area>()` hunk in `web/container.py` (stub from AEA-01), tests under `tests/api/`,
  `tests/contract/cases/demo.py` (AC-15), `tests/journeys/j3/test_aea_43.py` and `tests/journeys/j8/test_aea_43.py`
  (AC-16; `tests/journeys/support/` is AEA-57's, never edited here).
- **Contracts and shared surfaces:** consumes `IdentityService.inbox` (AEA-27), `DemoService.staffing` / `set_staffing` /
  `clock_view` (AEA-30), `ResetService.reset` and its `ResetDone` / `ResetFailed` results (AEA-31), all injected through
  `web/deps.py` and tested with doubles honouring stage7/cases.md §6–§7 and stage7/graph-tools.md §5; `ResetGate`,
  `ResetAlreadyRunning`, `RateLimiter`, `RequestContext`, `get_wall_clock`, `ApiProblem` and `openapi_check.py` (AEA-23);
  `INBOX_CODE_BODY` / `INBOX_CODE_GONE` (AEA-03); `LoginSession`, `DemoRole` (AEA-02). Produces CON-6…CON-9 (CON-8 read)
  for AEA-51, AEA-52, AEA-55 and AEA-24. If the planner needs to import `ResetDone` / `ResetFailed` from
  `services/reset.py` rather than distinguish them by their fields (`ok` vs `code`), record `blocked-on AEA-31`. Must not
  edit `web/{app,middleware,deps,errors}.py`, `services/reset_gate.py`, `routes/auth.py`, `routes/staff_clock.py`
  (AEA-47), any other route or schema file, `services/*`, `domain/*`, `policy/*` or the OpenAPI.
- **Scope boundary / refusal:** no clock advance (AEA-47); no case conversion, event writing or reset logic in the route
  (AEA-30, AEA-31); no clock formatting (WEB-25); no inbox screen or "Simulated messages" copy (UX-4).
- **Wave and gates:** wave 2; no gate. The wave merge runs `security-privacy-agent` on this diff.
- **Lane:** build-loop — route, schema and test code (`ticket-lanes.md`).
- **Risk:** security (`risk::security`, slice plan **Sec**; WEB-36): CON-6 is the only response carrying a D3 secret, so
  a bug in session scoping (AC-2) or log exclusion (AC-3) leaks a verification code to another reviewer or into Railway
  logs; a bug in the reset caller fields or throttle (AC-6, AC-8) loses "who asked" or lets one IP wipe the demo
  repeatedly. Frozen tests first: AC-2, AC-3, AC-6, AC-8.
- **Entry points added or changed:** WF-3 (`GET /api/demo/inbox`), WF-5 (`GET` / `PUT /api/demo/staffing`, `GET /api/demo/clock`), WF-15 (`POST /api/demo/reset`)
