## [AEA-44] staff: sessions, role switch, flags (CON-10)

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

> **US-28:** "As a **reviewer**, I need to sign in once with the demo login given in the README and then switch between
> acting as the customer and acting as a representative, supervisor or business owner in one click from any screen, so
> that I can play both sides of a handoff without separate accounts or passcodes."

The store behind the one demo login (R-48), the role switch, the implementation of the role check every staff route
uses, and the flag store behind the review list:

- **`services/staff.py` `StaffSessionStore(uow, session_secret, demo_clock, lifetime_s)`** (stage7/staff.md §2; STF-3,
  STF-4, STF-5; MC-1). It implements web.md's two Protocols unchanged:
  - `LoginSessions` (stage7/web.md §2): `start(now) -> IssuedSession` (token `secrets.token_urlsafe(32)`; the row is keyed
    by hex HMAC-SHA256(session_secret, token); new UUID4 `session_id`; role customer; `signed_in_demo` = one demo-clock
    reading; `expires_real` = now + `lifetime_s`), `resolve(token, now) -> LoginSession | SessionMissing |
    SessionExpired` (blank, unknown or altered → `SessionMissing`; `expires_real <= now` → delete the row,
    `SessionExpired`; read-only otherwise), `end(token)` (delete; idempotent). `now` is always the **wall** clock from
    `get_wall_clock()`; `lifetime_s` has no default and the container passes `limits.web.login_session_lifetime_s` =
    43,200 s, absolute, no idle timeout (WEB-5, STF-4, MC-22), so a demo-clock advance signs nobody out.
  - `StaffAccess.actor_for(session, needs) -> StaffActor | RoleRefusal` (stage7/web.md §3): pure over `session`;
    `session.role in needs` → `domain` `actor_for(StaffRole(session.role))`; otherwise `RoleRefusal(role, needs in the
    order given (the operation's x-roles, MC-4), reason="role_reset" if session.role_reset else "wrong_role")`, reason
    always sent (STF-20). It never clears `role_reset`. AEA-23's `require_staff(*roles)` turns a refusal into 403
    `ROLE_NOT_ALLOWED`.
  - Added for CON-10: `switch_role(session_id, role) -> LoginSession` (role only, clears `role_reset_pending`; session
    id, times, threads and inbox scope unchanged; no new cookie; switching to the current role is a no-op that still
    clears the marker) and `session_info(session) -> SessionInfoData` (role, `ROLE_CARDS` display name and `sees`,
    `signed_in_at` = the demo time stored at login, STF-22, MC-5). `StaffSessionStore.session_info` is a `LoginSessions`
    method (web.md §2); `SessionInfoData` is imported from `domain/staff.py` (staff.md §1, AEA-02), not defined in
    `services/staff.py`. AEA-23's `login` and this issue's `getSession` both build `SessionInfo` from it (R-W-1).
  - `RoleCard` and `ROLE_CARDS` (four entries in the order customer, representative, supervisor, owner, copied word for
    word from the OpenAPI examples) live here; the acting identity is the **role**, not the session (STF-1).
- **`services/staff.py` `FlagService(uow, demo_clock)`** (stage7/staff.md §2 *Flags*; STF-10): `flag(FlagIn, actor) ->
  FlagRecord | FlagRejected`, `review(flag_id, note, actor)`, `list_flags()` (newest first: `at` desc, then id desc).
  Touches no table but `flags` (R-37). CON-16's routes are AEA-45's.
- **`adapters/sqlite/repos_staff.py` bodies** (stage7/staff.md §3; STF-21, STF-27): `StaffRepos(conn)` holding
  `StaffSessionsRepo` (`insert`, `by_token_hash`, `by_session_id`, `set_role -> bool`, `delete`) and `FlagsRepo`
  (`insert -> int`, `get`, `review -> bool`, `list_ordered`) over typed rows `StaffSessionRow`, `FlagRow`, on the tables
  **AEA-10's** `90_staff.sql` creates (slice plan §0: AEA-10 writes every DDL file). The reset's `staff_sessions` UPDATE
  and `flags` DELETE are AEA-10's `clear_demo_tables` (stage7/staff.md §4, STF-6), not methods here.
- **`web/routes/staff_session.py` + `web/schemas/staff_session.py`**: CON-10's `getSession` (`GET /api/session`),
  `listDemoRoles` (`GET /api/session/roles`) and `switchRole` (`PUT /api/session/role`), every role allowed (x-roles: all
  four). `switchRole` is answered 503 `RESET_IN_PROGRESS` by AEA-23's middleware while a reset holds the gate;
  `getSession` and `listDemoRoles` wait for it (stage7/staff.md §11, STF-7).
- **Register hunk:** binds `get_login_sessions()` and `get_staff_access()` to **one** `StaffSessionStore` instance and
  `get_flag_service()` to `FlagService` (stage7/web.md §4; stage7/staff.md §2).

**Example pair (OpenAPI examples `CUSTOMER`, `TO_REPRESENTATIVE`, `RoleNotAllowed`).** The reviewer has just signed in
(role customer; AEA-23's `login` called `start`). `PUT /api/session/role` `{"role": "representative"}` with the same
`mhc_session` → 200 `{authenticated: true, role: "representative", display_name: "Riley, demo representative", sees:
["Queue", "Cases", "Live chat", "Review list"], signed_in_at: <unchanged demo time>}`, no `Set-Cookie`. The customer chat
in the other tab keeps working (chat routes ignore the role) and the inbox scope is unchanged. `GET /api/staff/queue`
(guarded `require_staff(REPRESENTATIVE, SUPERVISOR)`) now gets `StaffActor(role=representative, name="Riley",
signature="Riley (demo)")`; before the switch it answered 403 `ROLE_NOT_ALLOWED` `{role: customer, needs:
[representative, supervisor], reason: wrong_role}`. After a demo reset the same session's next staff call answers 403
with `reason: "role_reset"`, and `GET /api/session` shows role customer without a new login.

**Produced for other issues:** `StaffSessionStore` behind AEA-23's login, logout and gate (slice plan "Calls (injected):
staff sessions (44)"); the `require_staff` implementation and `StaffActor` for AEA-45, AEA-46, AEA-47, AEA-48;
`FlagService` for AEA-45's CON-16 routes; all proven with real services at AEA-52 (CAP-4) and AEA-51 (relayed turn).

### Source

- PRD R-31, R-32, R-37, R-48; US-28, US-23, US-25.
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml` (read-only): `getSession` (200 / 401), `listDemoRoles` (200 /
  401), `switchRole` (200 / 400 / 401 / 503; no `Set-Cookie`), examples `CUSTOMER`, `REPRESENTATIVE`, `ROLES`,
  `TO_REPRESENTATIVE`, `TO_SUPERVISOR`, `TO_OWNER`, `TO_CUSTOMER`; schemas `SessionInfo` ("No username or password is
  ever returned"), `RolesResponse`, `SwitchRoleRequest`, `Flag`, `FlagRequest`, `FlagReviewRequest`, `ApiError`;
  responses `Unauthenticated`, `RoleNotAllowed`, `ValidationError`, `ResetInProgress`; security scheme `mhcSession`.
- `docs/design/contracts/stage7/staff.md` §1 (`domain/staff.py` types, AEA-02), §2 (`StaffSessionStore`, `RoleCard`,
  `ROLE_CARDS`, `FlagService`), §3 (columns, `repos_staff.py`), §4 (reset effects), §10 (clocks), §11 (during a reset).
  Decisions STF-1, STF-3…STF-8, STF-10, STF-19…STF-22, STF-24, STF-26, STF-27 (`docs/plans/7b-decisions/staff.md`).
- `docs/design/contracts/stage7/web.md` §2 (`LoginSessions`, lifetime, cookie), §3 (`StaffAccess`, `require_staff`), §4
  (providers, `get_wall_clock`), §6 (gate step 3), §7 (reset gate), §10 (`request` record), §13 (`openapi_check.py`);
  WEB-5, WEB-6, WEB-8; merge MC-1, MC-2, MC-4, MC-5, MC-9, MC-11, MC-22.
- `docs/design/contracts/stage7/cases.md` §1.0 (repository constructor, wall-time formatter), §1.1, §1.3
  (`clear_demo_tables` updates `staff_sessions`, clears `flags`), §1.2 (`core.cases_ro.owner`,
  `core.messages.belongs_to_case`).
- DO-4 §13 (`UnitOfWork.staff`); DO-3 §3, §4.4, §6 S-18, §7 rows R-37, R-48; DO-2 §10 *Demo login*, *Staff console*,
  *Secrets*.
- DO-6 WF-4, CAP-4, *Content and redaction* (key values, session cookies); DO-7 M-3, M-13, M-27.
- Slice plan §0a (journey map, J-8) and rule `.claude/rules/integrated-journeys.md` §3–§4; UX-join amendments
  `docs/plans/ux-join/backend-amendments.md` AEA-44-1, AEA-44-2 and §3; residual R-W-1
  (`docs/plans/7b-decisions/residuals-web.md`; R-W-18 confirms the server needs nothing more for the role re-read).
- Slice plan row AEA-44 and §0; area-map row A9 Staff console; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "The interface must be interactive: a reviewer should be able to type questions, probe edge
  cases, and watch the agent escalate." (briefing Part B §6): the role switch is how the reviewer watches the escalation
  from the staff side; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `getSession` 200 validates against `SessionInfo` for each role, with `display_name` and `sees` exactly as `ROLE_CARDS` copies them from the OpenAPI examples (customer "Customer (demo)"; representative "Riley, demo representative", `["Queue", "Cases", "Live chat", "Review list"]`; supervisor "Demo supervisor"; owner "Demo business owner"), and `signed_in_at` is the demo-clock reading taken at login, not the wall time (STF-22) — verify: `tests/api/test_staff_session_routes.py::test_get_session_matches_openapi` (`assert_response_matches(response, "getSession")`; `FixedClock` demo time ≠ wall time) — evidence: four bodies validate and equal the examples apart from `signed_in_at`, which equals the demo reading.
- [ ] AC-2 [invariant] `listDemoRoles` returns the four roles in the order customer, representative, supervisor, owner with the `ROLES` example's `display_name` and `sees` lines — verify: `tests/api/test_staff_session_routes.py::test_list_demo_roles` — evidence: body validates against `RolesResponse` and equals the example.
- [ ] AC-3 [invariant] `switchRole` to each role returns the `TO_*` example shape; the next `getSession` on the same cookie shows the new role, and a second client carrying the same `mhc_session` (a second tab) sees the same role (STF-19) — verify: `tests/api/test_staff_session_routes.py::test_switch_role_persists_on_session` — evidence: four switches validate; role read back from both clients.
- [ ] AC-4 [invariant] A switch changes only the role and clears `role_reset_pending`: `session_id`, `signed_in_demo`, `expires_real` and the token hash are unchanged, no `Set-Cookie` is sent, and switching to the current role writes nothing else — verify: `tests/services/test_staff_service.py::test_switch_changes_only_role` (temp SQLite) plus `tests/api/test_staff_session_routes.py::test_switch_sets_no_cookie` — evidence: row columns equal before and after except `role` / `role_reset_pending`; no `Set-Cookie` header.
- [ ] AC-5 [failure/refusal] `switchRole` with `{"role": "admin"}` → 400 `VALIDATION_ERROR`, field `role`, the value absent from body and logs; without a session → 401 `UNAUTHENTICATED`; with a fake `ResetGate` held → 503 `RESET_IN_PROGRESS` `details.retry_after_ms: 5000` from AEA-23's middleware, the store not called (STF-7) — verify: `tests/api/test_staff_session_routes.py::test_switch_role_refusals` (caplog) — evidence: three bodies validate against their documented responses; "admin" absent from caplog.
- [ ] AC-6 [failure/refusal] (frozen first) Session lookup: `start` returns a token of `secrets.token_urlsafe(32)` shape and stores only `token_hash` = hex HMAC-SHA256(session_secret, token); `resolve` with a blank, unknown or one-character-altered token → `SessionMissing`; with `expires_real <= now` → `SessionExpired` and the row is deleted; through the real AEA-23 middleware these answer 401 `UNAUTHENTICATED` `details.reason` `"none"` / `"expired"`; `end` twice is a no-op the second time — verify: `tests/services/test_staff_service.py::test_session_lookup` and `tests/api/test_staff_session_routes.py::test_tampered_and_expired_cookie_401` — evidence: each case the stated result; the token string appears in no `staff_sessions` column.
- [ ] AC-7 [invariant] (frozen first) Lifetime is 43,200 s absolute on the wall clock (WEB-5): a session resolves at start + 43,199 s and is expired at start + 43,200 s; requests in between write nothing (no sliding touch); advancing the demo clock by three days does not expire it — verify: `tests/services/test_staff_service.py::test_lifetime_absolute_wall_clock` (fake wall clock, `FixedClock` demo clock) — evidence: valid / expired at the two instants; row unchanged between; still valid after the demo advance.
- [ ] AC-8 [failure/refusal] (frozen first) `actor_for` through `require_staff` on test routes: no session → 401 (never 403); customer on a `(REPRESENTATIVE, SUPERVISOR)` guard → 403 `ROLE_NOT_ALLOWED` `{role: "customer", needs: ["representative", "supervisor"], reason: "wrong_role"}`; on an `(OWNER, SUPERVISOR)` guard `needs` is `["owner", "supervisor"]` (MC-4); supervisor → `StaffActor(role=supervisor, name="Demo supervisor", signature="Demo supervisor")`; representative → name "Riley", signature "Riley (demo)"; `actor_for` makes no unit-of-work call — verify: `tests/api/test_staff_session_routes.py::test_require_staff_matrix` — evidence: outcomes as stated; 403 bodies validate against `RoleNotAllowed`; the uow double records zero calls from `actor_for`.
- [ ] AC-9 [failure/refusal] (frozen first) After AEA-10's `tx.core.reset.clear_demo_tables(reset_id)` runs on temp SQLite, a session that was `representative` resolves with role customer and `role_reset` true; its next staff call gets 403 `ROLE_NOT_ALLOWED` `reason: "role_reset"` from both of two clients (tabs); `getSession` answers 200 with role customer (the login stays); after `switchRole` to representative the next staff call passes and the marker is gone (STF-6) — verify: `tests/services/test_staff_service.py::test_reset_sends_roles_to_customer` — evidence: the sequence of outcomes as stated.
- [ ] AC-10 [negative] (frozen first) The session token, the demo username and the demo password (test values generated at test time in the test `Settings`) appear in no response body, captured log record, `request` record, trace-double span or `staff_sessions` column across a login → getSession → switchRole → staff call sequence; `SessionInfo` carries no username or password field — verify: `tests/api/test_staff_session_routes.py::test_no_secret_in_any_output` (caplog + trace double + table dump) — evidence: all three values absent everywhere.
- [ ] AC-11 [invariant] Flag lifecycle over temp SQLite: `flag` stores `case_ref`, `target`, `message_id`, `note`, `reason`, `flagged_by_role` = the actor's role, `flagged_at` = demo now, status `new`, and returns `FlagRecord` with `flag_id` "flg-<id>" and `flagged_by` "Riley (demo)"; `review` sets `reviewed`, the reviewer role and note, and a second review overwrites both; `list_flags` orders by `at` desc then id desc — verify: `tests/services/test_staff_service.py::test_flag_lifecycle` — evidence: rows and records read back match; order assert passes.
- [ ] AC-12 [failure/refusal] Flag refusals (`FlagRejected`): unknown `case_ref` → `CASE_NOT_FOUND` `{reference}`; unknown flag id → `FLAG_NOT_FOUND` `{flag_id}`; a `message_id` that is not a message of the case (`core.messages.belongs_to_case`) → `VALIDATION_ERROR` field `message_id`, constraint "not a message of this case"; `note` or `reason` over 2,000 characters → `VALIDATION_ERROR` naming the field; blank `note` / `reason` are stored as null (UXR-22); a rejected value never appears in the `FlagRejected` or a log record; a refusal writes no row — verify: `tests/services/test_staff_service.py::test_flag_refusals` (caplog) — evidence: each result as stated; `flags` row count unchanged by refusals.
- [ ] AC-13 [negative] Flags change nothing automatically (R-37): creating and reviewing flags changes only the `flags` table; the hashes of `docs/data/issued/meridian_dataset/knowledge_base/`, `eval/cases/` and `src/meridian/agent/prompts/` and every other table's row count are unchanged — verify: `tests/services/test_staff_service.py::test_flags_touch_only_flags_table` — evidence: hashes and counts equal before and after.
- [ ] AC-14 [invariant] `repos_staff.py` bodies work on the tables AEA-10's `90_staff.sql` creates, reached as `SqliteUnitOfWork(...).staff`: `set_role` returns False for an unknown session id; `list_ordered` orders `flagged_at` desc then id desc; after `clear_demo_tables` an old `flg-3` link answers `FLAG_NOT_FOUND`, never another flag (AUTOINCREMENT kept) — verify: `tests/services/test_staff_repos.py::test_repos_staff_bodies` — evidence: assertions pass on temp SQLite.
- [ ] AC-15 [invariant] The register hunk binds `get_login_sessions()` and `get_staff_access()` to the same `StaffSessionStore` instance, built with `lifetime_s = limits.web.login_session_lifetime_s`, and `get_flag_service()` to `FlagService` — verify: `tests/api/test_staff_session_routes.py::test_register_staff_binds_providers` — evidence: identity check `is` passes; `lifetime_s` read back as 43,200.
- [ ] AC-16 [capture] Driving `getSession`, `listDemoRoles` and `switchRole` through the app the container builds (real AEA-23 middleware, this issue's real store over temp SQLite) leaves one `request` record per call with route template, status, `caller_role` and `request_id` equal to `X-Request-ID`, and the `request` record of a staff call made after a switch carries the new role (WF-4: "staff role on every action") — verify: `tests/api/test_staff_session_capture.py::test_wf4_session_entry_points_emit_records` — evidence: records printed; `caller_role` before and after the switch. (The full CAP-4: claim, live reply, hand back, flag: AEA-52.)
- [ ] AC-17 [failure/refusal] A tab can always find out its current role: `getSession` and `listDemoRoles` never answer 403 for any role, `role_reset` included; after a switch made by a second client on the same cookie, the first client's next `getSession` returns the new role; after a reset, **every** staff call from either client (three in a row, through a `require_staff`-guarded route) answers 403 `ROLE_NOT_ALLOWED` `reason: "role_reset"` until `switchRole`, while `getSession` answers 200 role `customer` throughout (AEA-44-1; staff audit B1, B2; shell audit B1, B5; staff.md §2) — verify: `tests/api/test_staff_session_routes.py::test_role_reread_after_switch_and_reset` — evidence: the call sequence with statuses and `details.reason` printed.
- [ ] AC-18 [contract] `tests/contract/cases/staff_session.py` holds the server cases for `getSession`, `listDemoRoles` and `switchRole`: preconditions (a login; each role), every named request example (`TO_*`), and each documented error status the routes can produce (401; 400 and 503 `RESET_IN_PROGRESS` on `switchRole`) (AEA-44-2) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "getSession or listDemoRoles or switchRole" -rs` once AEA-59's runner is merged — evidence: one pass per case.
- [ ] AC-19 [journey] Extends J-8 (slice plan §0a journey map): a role switch through one client is seen by a second client on the same cookie at its next `getSession`, and a refused staff call names the current role and its reason (staff audit B1); asserting what the user sees and what is stored, in `tests/journeys/j8/test_aea_44.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j8/test_aea_44.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-44.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-20 [regression/context] Same change updates `.claude/reference/area-map.md` row A9 (`services/staff.py`, `adapters/sqlite/repos_staff.py`, `web/routes/staff_session.py`, `web/schemas/staff_session.py` planned → actual + commit; `schema/90_staff.sql` shown under AEA-10), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link), DO-3 §3 and §4.4 lines for `services/staff.py` (start / resolve / end / actor_for / switch_role / session_info / FlagService, replacing `sign_in` / `current` / `sign_out`, STF-26) — verify: `git diff --name-only` — evidence: the three docs in the diff, only this issue's rows changed.

### Observability

- Responsibilities: for WF-4 (DO-6 registry: "staff role on every action"), the middleware's `request` record takes `caller_role` from the `LoginSession` this store resolves on every request; `StaffActor` gives every staff action its role, name and signature so AEA-29 and AEA-46 write `case_event.actor_role` (CAP-4); flag rows keep `case_ref`, `message_id` and the flagging role. The session token, the demo username and the password never reach a log, record, span or table (DO-6 *Content and redaction*); the opaque `session_id` may appear as a correlation id (MC-9).
- Capture evidence: AC-16 drives the three real entry points; AC-17 proves a tab can always re-read its role; AC-10 (secrets) and AC-5 (a rejected value) are the negative checks.

### Evaluation

- Checks: WF-4's rule that flags feed the review list and never the eval set unreviewed (R-37) holds: flags change only the `flags` table and touch no eval case, prompt or knowledge file (AC-13). No DO-5 suite scores the role switch.
- Expected-answer authority: flag review outcomes are decided by people (R-37; DO-5 *Expected-answer authority* "A model is never its own authority"), never by this code; role cards are fixed copy from the OpenAPI examples (AC-1, AC-2).

### Metrics

- References: M-3 (live AI-resolved rate: "not flagged wrong by staff"), M-13 (promises kept on time) and M-27 (unowned and overdue cases), the last two inherited from WF-4.
- Acceptance conditions: M-3 stays computable because each flag row keeps `target`, `case_ref` and `message_id` (AC-11); M-13 and M-27 stay computable because `StaffActor.role` is a `StaffRole` value that AEA-29 stores as `cases.owner_role` and `case_event.actor_role` (stage7/staff.md §1, MC-12), so "no owner" and per-actor contact records are countable; this issue writes no case or promise row. No target is set here.

### Blocked by

AEA-10, AEA-23 (slice plan row AEA-44). `SessionInfoData` comes from AEA-02 (wave 0, R-W-1), already upstream.

Evidence only, not a merge edge (wave unchanged): AC-18's strict run waits for AEA-59's runner, and AC-19's journey
record stays `mock-tested` with *Blocked by* AEA-57 and AEA-52 until they land (`integrated-journeys.md` §4).

### Agent handoff

- **Area / owner:** A9 Staff console; files `src/meridian/services/staff.py`, `src/meridian/adapters/sqlite/repos_staff.py`
  (bodies; the shell is AEA-02's), `src/meridian/web/routes/staff_session.py`, `src/meridian/web/schemas/staff_session.py`,
  this issue's `register_<area>()` hunk in `web/container.py` (stub from AEA-01), tests under `tests/api/` and
  `tests/services/`, `tests/contract/cases/staff_session.py` (AC-18) and `tests/journeys/j8/test_aea_44.py` (AC-19;
  `tests/journeys/support/` is AEA-57's, never edited here).
- **Contracts and shared surfaces:** consumes `domain/staff.py` (`DemoRole`, `StaffRole`, `StaffPersona`,
  `STAFF_PERSONAS`, `StaffActor`, `actor_for`, `LoginSessionId`, `LoginSession`, `IssuedSession`, `SessionMissing`,
  `SessionExpired`, `RoleRefusal`, `SessionInfoData` (R-W-1); AEA-02), `Settings.session_secret` (AEA-02), `Limits.web` (AEA-01), `UnitOfWorkFactory`,
  `SqliteUnitOfWork`, `90_staff.sql`, `clear_demo_tables`, `core.cases_ro.owner`, `core.messages.belongs_to_case` and
  `temp_sqlite()` (AEA-10), `LoginSessions`, `StaffAccess`, `require_staff`, the providers, `get_wall_clock`,
  `ApiProblem` and `openapi_check.py` (AEA-23), `FixedClock` (AEA-11). Produces the session store for AEA-23, the
  `require_staff` implementation and `StaffActor` for AEA-45…AEA-48, `FlagService` for AEA-45, all for AEA-51 and
  AEA-52. Must not edit `web/{app,middleware,deps,errors}.py` or `routes/auth.py` (AEA-23 sets the cookie and its
  attributes), `schema/*.sql`, `db.py`, `migrate.py`, `repos_core.py`, `repos_cases.py` (AEA-10), `services/reset.py`
  (AEA-31), any other route or schema file, `domain/*`, or the OpenAPI.
- **Scope boundary / refusal:** no passcode and no per-role password (R-48: the login is the gate; roles are labels); no
  login or logout route and no cookie writing (AEA-23); no DDL (AEA-10, STF-21); no reset method (STF-6); no flag routes
  (AEA-45); no change to case data.
- **Wave and gates:** wave 2; no gate. The wave merge runs `security-privacy-agent` on this diff.
- **Lane:** build-loop — service, repository bodies, routes and tests (`ticket-lanes.md`).
- **Risk:** security (`risk::security`, slice plan **Sec**): a bug here lets an unsigned, forged or expired session past
  the one login that gates the whole deployment (R-48), leaks the session token or the demo credentials into logs or the
  database, or lets the customer role act on staff data (D4 briefs, D2 names). Frozen tests first: AC-6, AC-7, AC-8,
  AC-9, AC-10.
- **Entry points added or changed:** WF-4 (`GET /api/session`, `GET /api/session/roles`, `PUT /api/session/role`)
