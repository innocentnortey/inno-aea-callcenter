# Plan — [AEA-44] staff: sessions, role switch, flags (CON-10)

**Status:** planned (READY) · `risk::security` · `lane::build-loop` · wave 2
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #44 (spec copy `docs/plans/tickets/AEA-44.md`) ·
**Base revision:** `main` at `7603145` (AEA-33 ledger row; AEA-02, AEA-10, AEA-11, AEA-23 merged)
**Planner model:** claude-opus-5-5 · **Implementer:** Sonnet (`fanout-implementer`) · **Test-writer first** (security ticket)

No earlier plan existed at this path; this is the first version.

---

## 1. Goal and sources

### Goal (issue *What to build*, quoted)

> **US-28:** "As a **reviewer**, I need to sign in once with the demo login given in the README and then switch between
> acting as the customer and acting as a representative, supervisor or business owner in one click from any screen, so
> that I can play both sides of a handoff without separate accounts or passcodes."
>
> The store behind the one demo login (R-48), the role switch, the implementation of the role check every staff route
> uses, and the flag store behind the review list.

Concretely, this ticket delivers:

1. `services/staff.py`: `StaffSessionStore` (implements AEA-23's `LoginSessions` and `StaffAccess` Protocols, plus
   `switch_role`), `RoleCard` / `ROLE_CARDS`, and `FlagService` with `FlagIn`, `FlagRecord`, `FlagRejected`.
2. `adapters/sqlite/repos_staff.py`: the repository bodies over AEA-10's `90_staff.sql`.
3. `web/routes/staff_session.py` + `web/schemas/staff_session.py`: CON-10 `getSession`, `listDemoRoles`, `switchRole`.
4. The `register_staff_session` hunk in `web/container.py`: binds `get_login_sessions()` and `get_staff_access()` to **one**
   `StaffSessionStore`, `get_flag_service()` to `FlagService`, and includes the CON-10 router.

### Context

Stage 7 closed 2026-10-21 with 62 tickets. AEA-23 (web shell, `web/deps.py` with the `LoginSessions` / `StaffAccess`
Protocols and `require_staff`) and AEA-10 (storage, `90_staff.sql`, `clear_demo_tables`) are merged on `main`. Until
this ticket lands, every login in tests runs against AEA-23's `FakeSessionStore`; nothing real stores a session. AEA-30
(the real demo clock) is a same-wave sibling and is **not** merged: this ticket reads `Key("demo_clock")` lazily.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-44.md` | AC-1…AC-20; owned files; frozen-first AC-6…AC-10 |
| Staff addendum (wins over DO-4) | `docs/design/contracts/stage7/staff.md` §1 (types, AEA-02, merged), §2 (`StaffSessionStore`, `RoleCard`, `ROLE_CARDS`, Flags), §3 (columns, `repos_staff.py`), §4 (reset effects), §10 (clocks), §11 (during a reset) | every signature in §4 below |
| Web addendum | `stage7/web.md` §2 (`LoginSessions`, lifetime, cookie), §3 (`StaffAccess`, `require_staff`), §4 (providers, `get_wall_clock`), §6 gate step 3, §7 reset gate | the Protocols this store satisfies; `now` is the wall clock |
| Cases addendum | `stage7/cases.md` §1.0 (repo constructor, `format_wall`), §1.2 (`core.cases_ro.owner`, `core.messages.belongs_to_case`), §1.3 (`clear_demo_tables`), §6 (`DemoClock`) | flag checks run inside one write transaction; reset is AEA-10's |
| Decisions | `docs/plans/7b-decisions/staff.md` STF-1, 3–8, 10, 19–22, 24, 26, 27; `residuals-web.md` R-W-1, R-W-18; merge MC-1, 2, 4, 5, 9, 11, 22 | role on the session (STF-19); HMAC key (STF-5); `needs` in x-roles order (MC-4); reason always sent (STF-20); demo-time `signed_in_at` (STF-22) |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `/api/session`, `/api/session/roles`, `/api/session/role`; schemas `SessionInfo`, `RolesResponse`, `SwitchRoleRequest`, `Flag`, `FlagRequest`; responses `Unauthenticated`, `RoleNotAllowed`, `ValidationError`, `ResetInProgress`, `CaseNotFound`, `FLAG_NOT_FOUND` | wire shapes; `getSession` documents 200/401; `listDemoRoles` 200/401; `switchRole` 200/400/401/503, no `Set-Cookie` |
| Code design | `docs/design/code-design.md` §3 tree lines 237, 303, 308; §4.4 row `services/staff.py` (line 401) | AC-20 flips these to built |
| Requirements | PRD R-31, R-32, R-37, R-48; US-23, US-25, US-28 | one login, roles are labels, no passcode; flags change nothing automatically |
| Evaluation plan | DO-5 | n/a: no suite scores the role switch (ticket *Evaluation*); R-37 check is AC-13 |
| Observability | DO-6 WF-4 "staff role on every action"; *Content and redaction* | the middleware's `request.caller_role` comes from this store (AC-16); token / username / password never logged (AC-10) |
| Metrics | DO-7 M-3, M-13, M-27 | flag rows keep `target`, `case_ref`, `message_id` (AC-11); `StaffActor.role` is a `StaffRole` |
| UX-join | `docs/plans/ux-join/backend-amendments.md` AEA-44-1 (→ AC-17), AEA-44-2 (→ AC-18) | in ticket |
| Journeys | `.claude/rules/integrated-journeys.md` §3–§4; slice plan §0a J-8 | AC-19 at level `mock-tested` now |
| Stage 7 sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | none touches this ticket's choices; D-13 (wall-clock override in `ContainerOverrides`) is what the tests use |

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Store only HMAC-SHA256(secret, token) hex; token = `secrets.token_urlsafe(32)` | STF-5 / WEB-6 | AC-6 | in-ticket | Step 3 |
| Absolute 43,200 s lifetime on the wall clock; no touch write | WEB-5, STF-4, MC-22 | AC-7 | in-ticket | Step 3 |
| `actor_for` pure; `needs` in the order given; reason always sent | staff §2, MC-4, STF-20 | AC-8 | in-ticket | Step 3 |
| `role_reset` cleared only by `switch_role` | staff §2 | AC-9, AC-17 | in-ticket | Step 3 |
| `session_info` builds `SessionInfoData` from `ROLE_CARDS` | R-W-1 | AC-1 | in-ticket | Step 3 |
| What `switch_role` does when the session row is gone (logged out in another tab between the gate and the route) | not specified | no | added — `SessionGone` exception → 401 `UNAUTHENTICATED` `reason: none` (documented status) | Step 3, Step 5; test inside `test_switch_changes_only_role` |
| `FlagIn` length / blank rules; service re-checks so a bypassed model still refuses | staff §2, §6 | AC-12 | in-ticket (service re-check is a plan decision) | Step 4 |
| `FLAG_NOT_FOUND` details never echo arbitrary text | DO-4 §0 "never a rejected value" | partly | added — malformed id → `details: None`; well-formed unknown → `{flag_id}` | Step 4 |
| Flag routes (CON-16) | staff §2 | no | other-ticket — AEA-45 | — |
| Reset UPDATE / DELETE | staff §4, STF-6 | — | other-ticket — AEA-10 `clear_demo_tables` (merged) | — |
| The real demo clock | cases §6 | — | other-ticket — AEA-30 provides `Key("demo_clock")`; read lazily here | Step 6 |
| `SessionInfo` carries no username / password | OpenAPI `SessionInfo` | AC-10 | in-ticket | Step 5 |
| The ticket's example pair (CUSTOMER → TO_REPRESENTATIVE → RoleNotAllowed → reset) as one test | ticket *Example pair* | no single AC | added — `test_example_pair_switch_to_representative` | §7 |
| Local driver for the contract cases until AEA-59's runner exists | AEA-23 precedent (`test_contract_cases_auth.py`) | AC-18 waits on AEA-59 | added — `tests/api/test_contract_cases_staff_session.py` | Step 9 |
| Journey record | integrated-journeys §4 | AC-19 | in-ticket | Step 11 |
| Context docs | context-maintenance | AC-20 | in-ticket | Step 12 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `GET /api/session` (`getSession`) | WF-4 | DO-6 WF-4, ticket *Entry points* | caller_role on every `request` record; M-13, M-27 |
| `GET /api/session/roles` (`listDemoRoles`) | WF-4 | same | same |
| `PUT /api/session/role` (`switchRole`) | WF-4 | same | same |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files created or edited)

| File | Action | Who writes it |
|---|---|---|
| `src/meridian/services/staff.py` | create | implementer |
| `src/meridian/adapters/sqlite/repos_staff.py` | modify (replace the AEA-02 shell; keep the module path and `StaffRepos(conn)` constructor) | implementer |
| `src/meridian/web/routes/staff_session.py` | create | implementer |
| `src/meridian/web/schemas/staff_session.py` | create | implementer |
| `src/meridian/web/container.py` | modify **only** the body and docstring of `register_staff_session` | implementer |
| `tests/api/staff_session_support.py` | create | **test-writer** (frozen) |
| `tests/services/test_staff_service.py` | create | **test-writer** (frozen) |
| `tests/api/test_staff_session_routes.py` | create | **test-writer** (frozen) |
| `tests/services/test_staff_repos.py` | create | implementer |
| `tests/api/test_staff_session_capture.py` | create | implementer |
| `tests/contract/cases/staff_session.py` | create | implementer |
| `tests/api/test_contract_cases_staff_session.py` | create | implementer |
| `tests/journeys/j8/test_aea_44.py` | create | implementer |
| `docs/testing/journeys/<run date>-AEA-44.md` | create | implementer |
| `.claude/reference/area-map.md` | modify row A9 only | implementer |
| `.claude/state/icm-progress.md` | add one row | implementer |
| `docs/design/code-design.md` | modify §3 (one **Built:** line; tree lines 303 and 308) and §4.4 row `services/staff.py` only | implementer |

### 2.2 Shared surfaces, read only (import, never edit)

`src/meridian/domain/staff.py`, `domain/common.py` (AEA-02); `config.py` (`Settings.session_secret`, `demo_username`,
`demo_password`); `policy/limits.py` (`Limits.web.login_session_lifetime_s`, AEA-01); `ports/runtime.py` (`Clock`,
`UnitOfWork`, `UnitOfWorkFactory`); `adapters/sqlite/{db,migrate,rows,repos_core,repos_core_aux,repos_cases}.py`,
`schema/90_staff.sql` (AEA-10); `web/{app,middleware,deps,errors,logging}.py`, `web/routes/auth.py`,
`web/schemas/auth.py` (AEA-23); `tests/api/web_shell_support.py`, `tests/api/openapi_check.py` (AEA-23);
`tests/fakes/clock.py` (AEA-11); `tests/fixtures/sqlite.py` (AEA-10); `tests/unit/adapters/sqlite/helpers.py`
(AEA-10's test builders, imported read-only); the OpenAPI YAML.

### 2.3 Owned by other tickets — do not touch

`web/{app,middleware,deps,errors,logging}.py`, `routes/auth.py`, `schemas/auth.py` (AEA-23); every other
`register_<area>()` function in `container.py`; `schema/*.sql`, `db.py`, `migrate.py`, `rows.py`, `repos_core*.py`,
`repos_cases*.py`, `tests/fixtures/sqlite.py` (AEA-10); `services/reset.py` (AEA-31); `services/demo.py` (AEA-30);
`domain/*`, `ports/*`, `config.py`, `policy/*`; any other route or schema file (AEA-40…48); `tests/journeys/support/`
(AEA-57); `tests/contract/test_openapi_server.py` (AEA-59); `apps/web/**`, `docs/ux/**`, the briefing, issued data,
`docs/archive/`, `docs/parked/`.

---

## 3. Requirements table

`F` = frozen (written by the test-writer before the implementer starts). Frozen-first ACs named by the ticket: AC-6,
AC-7, AC-8, AC-9, AC-10. The other ACs that live in the same two frozen files are frozen with them (file-level tamper
check; AEA-23 precedent).

| AC | Requirement (short) | How it is implemented | Verified by |
|---|---|---|---|
| AC-1 | `getSession` 200 per role validates; `display_name`/`sees` exactly `ROLE_CARDS`; `signed_in_at` = demo reading at login, not wall | `ROLE_CARDS` (Step 3); `session_info`; route (Step 5) | F `tests/api/test_staff_session_routes.py::test_get_session_matches_openapi` |
| AC-2 | `listDemoRoles` four roles in order with `ROLES` example lines | `ROLE_CARDS[*].sees_line`; route | F `tests/api/test_staff_session_routes.py::test_list_demo_roles` |
| AC-3 | `switchRole` → `TO_*` shape; next `getSession` and a second client on the same cookie see it | `switch_role`; route | F `tests/api/test_staff_session_routes.py::test_switch_role_persists_on_session` |
| AC-4 | switch changes only role and clears `role_reset_pending`; no `Set-Cookie`; same-role switch writes nothing else | `set_role` one UPDATE; route returns plain JSON | F `tests/services/test_staff_service.py::test_switch_changes_only_role`; F `tests/api/test_staff_session_routes.py::test_switch_sets_no_cookie` |
| AC-5 | `{"role":"admin"}` → 400 field `role`, value absent from body and logs; no session → 401; gate held → 503, store not called | `SwitchRoleRequest` (`hide_input_in_errors`); AEA-23's handler and middleware | F `tests/api/test_staff_session_routes.py::test_switch_role_refusals` |
| AC-6 | token shape; only `token_hash` stored; blank/unknown/altered → `SessionMissing`; expired → `SessionExpired` + row deleted; 401 `none`/`expired` via middleware; `end` idempotent | `start`, `resolve`, `end` (Step 3) | F `tests/services/test_staff_service.py::test_session_lookup`; F `tests/api/test_staff_session_routes.py::test_tampered_and_expired_cookie_401` |
| AC-7 | 43,200 s absolute wall clock; valid at +43,199, expired at +43,200; no write between; demo advance doesn't expire | `resolve` read-only; expiry compares `expires_real <= now` | F `tests/services/test_staff_service.py::test_lifetime_absolute_wall_clock` |
| AC-8 | `require_staff` matrix: 401 never 403 without session; 403 bodies with `needs` in x-roles order; actor personas; `actor_for` makes no UoW call | `actor_for` pure | F `tests/api/test_staff_session_routes.py::test_require_staff_matrix` |
| AC-9 | after `clear_demo_tables`: role customer + `role_reset`; refusals `role_reset` for both tabs; login stays; `switchRole` clears it | `resolve` maps `role_reset_pending`; `switch_role` clears | F `tests/services/test_staff_service.py::test_reset_sends_roles_to_customer` (service level: `actor_for` is the `require_staff` implementation; the HTTP form is AC-17) |
| AC-10 | token, username, password absent from bodies, logs, `request` records, trace double, `staff_sessions` dump; `SessionInfo` has no username/password field | no logging in `services/staff.py`; only the hash stored | F `tests/api/test_staff_session_routes.py::test_no_secret_in_any_output` |
| AC-11 | flag lifecycle and ordering | `FlagService.flag/review/list_flags`; `FlagsRepo` | F `tests/services/test_staff_service.py::test_flag_lifecycle` |
| AC-12 | flag refusals; blank → null; rejected value never in `FlagRejected` or logs; refusal writes no row | Step 4 order of checks | F `tests/services/test_staff_service.py::test_flag_refusals` |
| AC-13 | flags touch only `flags` (hashes of KB, `eval/cases/`, `agent/prompts/`; every other table count) | `FlagService` touches `tx.staff.flags` + two read helpers only | F `tests/services/test_staff_service.py::test_flags_touch_only_flags_table` |
| AC-14 | `repos_staff.py` bodies on AEA-10's tables; `set_role` False unknown; order; stale `flg-3` after reset | Step 2 | `tests/services/test_staff_repos.py::test_repos_staff_bodies` |
| AC-15 | hunk binds both providers to the same instance (`lifetime_s` 43,200) and `FlagService` | Step 6 | F `tests/api/test_staff_session_routes.py::test_register_staff_binds_providers` |
| AC-16 | one `request` record per call through the container-built app; `caller_role` before and after the switch | real middleware + real store | `tests/api/test_staff_session_capture.py::test_wf4_session_entry_points_emit_records` |
| AC-17 | `getSession`/`listDemoRoles` never 403; second-client switch seen; three staff calls after reset all 403 `role_reset` until `switchRole` | as AC-9 over HTTP | F `tests/api/test_staff_session_routes.py::test_role_reread_after_switch_and_reset` |
| AC-18 | `tests/contract/cases/staff_session.py` cases | Step 9 | now: `tests/api/test_contract_cases_staff_session.py::test_staff_session_cases_drive_documented_statuses` (plan-added local driver); later `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "getSession or listDemoRoles or switchRole" -rs` once AEA-59 merges |
| AC-19 | **[journey] J-8**, level **`mock-tested`** now (target `integrated with a scripted model` once AEA-57 and AEA-52 land) | Step 10 | `uv run pytest -m journey tests/journeys/j8/test_aea_44.py -rs`; record `docs/testing/journeys/<date>-AEA-44.md` |
| AC-20 | area map A9, ICM row, DO-3 §3/§4.4 | Step 12 | `git diff --name-only` shows the three docs; only this ticket's rows changed |
| Example pair (plan-added) | CUSTOMER → `PUT role representative` = `TO_REPRESENTATIVE`, no `Set-Cookie`; queue probe 403 before / Riley after; reset → 403 `role_reset`, `getSession` customer | all of the above | F `tests/api/test_staff_session_routes.py::test_example_pair_switch_to_representative` |

---

## 4. Shared code to use (exact shapes)

### 4.1 Already on main — copy these names exactly

```python
# src/meridian/domain/staff.py (AEA-02)
class DemoRole(StrEnum): CUSTOMER="customer"; REPRESENTATIVE="representative"; SUPERVISOR="supervisor"; OWNER="owner"
class StaffRole(StrEnum): REPRESENTATIVE="representative"; SUPERVISOR="supervisor"; OWNER="owner"
class StaffPersona(MeridianModel): name: str; signature: str
STAFF_PERSONAS: Mapping[StaffRole, StaffPersona]   # Riley / "Riley (demo)"; "Demo supervisor" x2; "Demo business owner" x2
class StaffActor(MeridianModel): role: StaffRole; name: str; signature: str; def owns(self, owner_role) -> bool
def actor_for(role: StaffRole) -> StaffActor        # import as `actor_for as persona_actor` (name clash with the method)
LoginSessionId = NewType("LoginSessionId", str)
class LoginSession(MeridianModel): session_id: LoginSessionId; role: DemoRole; role_reset: bool
                                   signed_in_at: dt.datetime  # demo clock;  expires_at: dt.datetime  # wall clock UTC
class IssuedSession(MeridianModel): session: LoginSession; token: SecretStr
class SessionMissing(MeridianModel): ...            # no fields
class SessionExpired(MeridianModel): ...            # no fields
class RoleRefusal(MeridianModel): role: DemoRole; needs: tuple[StaffRole, ...]; reason: Literal["wrong_role", "role_reset"]
class SessionInfoData(MeridianModel): role: DemoRole; display_name: str; sees: tuple[str, ...]; signed_in_at: dt.datetime

# src/meridian/domain/common.py
class MeridianModel(BaseModel): model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True,
                                                          str_strip_whitespace=True)
class CaseRef(_PatternId): PATTERN = r"^MHC-C-[0-9]{4}$"
class ApiErrorCode(StrEnum): ... UNAUTHENTICATED, VALIDATION_ERROR, CASE_NOT_FOUND, FLAG_NOT_FOUND, ROLE_NOT_ALLOWED ...

# src/meridian/ports/runtime.py
class Clock(Protocol):
    def now(self) -> dt.datetime: ...
class UnitOfWork(Protocol): core: CoreRepos; ...; cases: CaseRepos; staff: StaffRepos; ops: OpsRepos; def commit(self) -> None
class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
# A unit of work commits only if tx.commit() ran; leaving the `with` without commit rolls back (db.py).
# write=False opens `PRAGMA query_only=ON` + BEGIN DEFERRED (reads only).

# src/meridian/adapters/sqlite/db.py
def format_wall(dt: datetime) -> str      # UTC ISO-8601 "+00:00"; raises ValueError on a naive datetime
def parse_wall(text: str) -> datetime     # tz-aware, UTC
def integrity_errors(table: str)          # context manager: sqlite3.IntegrityError -> StorageError(table, kind)
def last_row_id(cur: sqlite3.Cursor, table: str) -> int
class SqliteUnitOfWork: core, spend, identity, booking, cases, staff: StaffRepos, ops; connection (property); commit()

# AEA-10 helpers used by FlagService (inside the caller's transaction)
tx.core.cases_ro.owner(case_ref: CaseRef) -> CaseOwnerRow | None     # None = no such case
tx.core.messages.belongs_to_case(message_id: int | str, case_ref: CaseRef) -> bool   # False on a non-integer id
tx.core.reset.clear_demo_tables(reset_id: str, *, ended_at: datetime | None = None) -> Cleared   # Cleared.roles_reset: int
# clear_demo_tables: UPDATE staff_sessions SET role='customer', role_reset_pending=1 WHERE role<>'customer'; DELETE FROM flags
#   (CLEARED_TABLES includes "flags"; sqlite_sequence is not restored, so ids are never reused)

# src/meridian/adapters/sqlite/schema/90_staff.sql (AEA-10) — columns
# staff_sessions(token_hash TEXT PK, session_id TEXT UNIQUE NOT NULL, role TEXT NOT NULL CHECK(...4 roles),
#                role_reset_pending INTEGER NOT NULL DEFAULT 0, signed_in_demo TEXT, created_real TEXT, expires_real TEXT)
# flags(id INTEGER PK AUTOINCREMENT, case_ref TEXT, target TEXT CHECK(answer|brief|escalation), message_id TEXT NULL,
#       note TEXT NULL, reason TEXT NULL, flagged_by_role TEXT, flagged_at TEXT, status TEXT CHECK(new|reviewed),
#       reviewed_by_role TEXT NULL, reviewed_note TEXT NULL, reviewed_at TEXT NULL)

# src/meridian/web/deps.py (AEA-23) — Protocols this store satisfies structurally, keys, providers
class LoginSessions(Protocol):
    def start(self, now: datetime) -> IssuedSession: ...
    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired: ...
    def end(self, token: SecretStr) -> None: ...
    def session_info(self, session: LoginSession) -> SessionInfoData: ...
class StaffAccess(Protocol):
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal: ...
LOGIN_SESSIONS = Key("login_sessions"); STAFF_ACCESS = Key("staff_access"); FLAG_SERVICE = Key("flag_service")
UOW_FACTORY = Key("uow_factory"); WALL_CLOCK = Key("wall_clock"); RESET_GATE = Key("reset_gate")
def get_login_sessions(request) -> LoginSessions; def get_staff_access(request) -> StaffAccess
def get_flag_service(request) -> Any; def get_login_session(context=Depends(get_request_context)) -> LoginSession
def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]   # 403 ROLE_NOT_ALLOWED {role, needs, reason}

# src/meridian/web/schemas/auth.py (AEA-23) — reuse, do not redefine
class SessionInfo(MeridianModel): authenticated: Literal[True]; role: DemoRole; display_name: str
                                  sees: tuple[str, ...]; signed_in_at: datetime

# src/meridian/web/errors.py
class ApiProblem(Exception): def __init__(self, status, code: ApiErrorCode, *, field=None, constraint=None,
                                          details: dict[str, object] | None = None, headers=None)

# src/meridian/web/container.py
class ContainerError(RuntimeError); @dataclass(frozen=True) class Key[T]: name: str
class Container: provide(key, factory), get(key), on_start, on_close, settings, limits
# get() of an unprovided key raises ContainerError(f"not provided: {name}")

# src/meridian/web/middleware.py
class WebShellState: settings; wall_clock; public_paths   # app.state.web_shell; absent on a bare FastAPI()
# Middleware already: switchRole in RESET_503_OPERATIONS (503 RESET_IN_PROGRESS, retry_after_ms 5000);
# getSession / listDemoRoles wait for the gate; caller_role = session.role.value resolved BEFORE the route runs.

# tests (read only)
tests/fakes/clock.py: FixedClock(at=WORKED_PAIRS_NOW)  # 2026-10-16 10:00 America/Chicago; now(); advanced(by) -> new clock
tests/fixtures/sqlite.py: temp_sqlite() -> TempStore(data_dir, db_path, issued_path, uow)
tests/api/web_shell_support.py: make_settings, MutableClock, make_client, cookie_header, session_cookie_value,
    set_cookie_lines, login, error_body, assert_matches, captured_log, records_of, app_log_text, add_probe_route,
    add_test_route, RecordingTraceSink, FakeHeartbeat, reset_gate_of, request_for, suppress_container_starters, rand_word
tests/api/openapi_check.py: load_contract(), load_document(), assert_response_matches(response, operation_id)
tests/unit/adapters/sqlite/helpers.py: new_thread(), case_ref(n), conversation(thread), case_row(thread, ref), NOW
```

### 4.2 Signatures this ticket creates (stage7/staff.md §2–§3; `[plan]` = added by this plan)

```python
# ---------------- src/meridian/adapters/sqlite/repos_staff.py ----------------
class StaffSessionRow(MeridianModel):
    token_hash: str; session_id: LoginSessionId; role: DemoRole; role_reset_pending: bool
    signed_in_demo: datetime; created_real: datetime; expires_real: datetime

class FlagRow(MeridianModel):
    id: int | None = None
    case_ref: CaseRef; target: Literal["answer", "brief", "escalation"]
    message_id: str | None; note: str | None; reason: str | None
    flagged_by_role: StaffRole; flagged_at: datetime
    status: Literal["new", "reviewed"]
    reviewed_by_role: StaffRole | None; reviewed_note: str | None; reviewed_at: datetime | None

class StaffSessionsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def insert(self, row: StaffSessionRow) -> None: ...
    def by_token_hash(self, token_hash: str) -> StaffSessionRow | None: ...
    def by_session_id(self, session_id: LoginSessionId) -> StaffSessionRow | None: ...
    def set_role(self, session_id: LoginSessionId, role: DemoRole) -> bool: ...   # role + role_reset_pending=0, one UPDATE
    def delete(self, token_hash: str) -> None: ...

class FlagsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def insert(self, row: FlagRow) -> int: ...
    def get(self, flag_id: int) -> FlagRow | None: ...
    def review(self, flag_id: int, by_role: StaffRole, note: str | None, at: datetime) -> bool: ...
    def list_ordered(self) -> tuple[FlagRow, ...]: ...   # flagged_at desc, then id desc

class StaffRepos:                                      # = UnitOfWork.staff
    sessions: StaffSessionsRepo; flags: FlagsRepo
    def __init__(self, conn: sqlite3.Connection) -> None: ...

# ---------------- src/meridian/services/staff.py ----------------
class RoleCard(MeridianModel):
    role: DemoRole; display_name: str; sees: tuple[str, ...]; sees_line: str
ROLE_CARDS: Mapping[DemoRole, RoleCard]               # MappingProxyType, insertion order customer, representative, supervisor, owner

class SessionGone(LookupError):                       # [plan] switch_role found no row for the session id
    """The login session row no longer exists (logged out or expired after the gate resolved it)."""

class StaffSessionStore:                              # implements LoginSessions and StaffAccess
    def __init__(self, uow: UnitOfWorkFactory, session_secret: SecretStr, demo_clock: Clock,
                 lifetime_s: int) -> None: ...        # lifetime_s has NO default; ValueError if <= 0
    @property
    def lifetime_s(self) -> int: ...                  # [plan] read back by AC-15
    def start(self, now: datetime) -> IssuedSession: ...
    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired: ...
    def end(self, token: SecretStr) -> None: ...
    def session_info(self, session: LoginSession) -> SessionInfoData: ...
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal: ...
    def switch_role(self, session_id: LoginSessionId, role: DemoRole) -> LoginSession: ...   # raises SessionGone

FLAG_TEXT_MAX = 2000                                  # [plan] constant name
class FlagIn(MeridianModel):
    case_ref: CaseRef
    target: Literal["answer", "brief", "escalation"]
    message_id: str | None
    note: str | None = Field(default=None, max_length=2000)
    reason: str | None = Field(default=None, max_length=2000)
    # + @field_validator("note", "reason") (mode="after"): "" -> None  (MeridianModel already strips)

class FlagRecord(MeridianModel):
    flag_id: str; target: str; reason: str | None; case_ref: CaseRef; message_id: str | None; note: str | None
    flagged_by: str; at: datetime; status: Literal["new", "reviewed"]
    reviewed_by: str | None; reviewed_note: str | None

class FlagRejected(MeridianModel):
    code: Literal["CASE_NOT_FOUND", "FLAG_NOT_FOUND", "VALIDATION_ERROR"]
    field: str | None; constraint: str | None; details: dict[str, str] | None   # no defaults: always pass all four

class FlagService:
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock) -> None: ...
    def flag(self, flag: FlagIn, actor: StaffActor) -> FlagRecord | FlagRejected: ...
    def review(self, flag_id: str, note: str | None, actor: StaffActor) -> FlagRecord | FlagRejected: ...
    def list_flags(self) -> tuple[FlagRecord, ...]: ...

# ---------------- src/meridian/web/schemas/staff_session.py ----------------
class SwitchRoleRequest(BaseModel):                   # plain BaseModel: the OpenAPI allows extra keys
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)
    role: DemoRole
class RoleLine(MeridianModel): role: DemoRole; display_name: str; sees: str
class RolesResponse(MeridianModel): roles: tuple[RoleLine, ...]

# ---------------- src/meridian/web/routes/staff_session.py ----------------
class RoleSwitcher(LoginSessions, Protocol):          # [plan] web.md §2: switch_role is not in LoginSessions
    def switch_role(self, session_id: LoginSessionId, role: DemoRole) -> LoginSession: ...
def get_role_switcher(sessions: LoginSessions = Depends(get_login_sessions)) -> RoleSwitcher   # cast only
def get_session(...) -> Response; def list_demo_roles(...) -> Response; def switch_role(...) -> Response   # sync def
def build_router() -> APIRouter
```

### 4.3 `ROLE_CARDS` — copy word for word (OpenAPI examples `TO_CUSTOMER`/`CUSTOMER`, `REPRESENTATIVE`, `TO_SUPERVISOR`, `TO_OWNER`, `ROLES`)

| role | `display_name` | `sees` (tuple) | `sees_line` |
|---|---|---|---|
| customer | `Customer (demo)` | `("Chat", "Demo guide", "Demo inbox", "Monitoring", "Evaluation")` | `The chat, the demo guide, the demo inbox, monitoring and evaluation` |
| representative | `Riley, demo representative` | `("Queue", "Cases", "Live chat", "Review list")` | `The queue and cases; can claim, join, reply, log, flag` |
| supervisor | `Demo supervisor` | `("Oversight", "Review list", "Queue", "Demo controls")` | `Urgent, unowned, due-soon, overdue and stuck cases; assigns; runs the demo shift and clock` |
| owner | `Demo business owner` | `("Outcomes", "Cases (read only)")` | `Outcomes, and opens the cases behind them (read only)` |

### 4.4 Wire shapes (OpenAPI, verbatim facts)

- `SessionInfo` required: `authenticated` (const true), `role`, `display_name`, `sees` (array of string), `signed_in_at`
  (date-time). "No username or password is ever returned."
- `RolesResponse`: `{roles: [{role, display_name, sees: string}]}`.
- `SwitchRoleRequest`: `{role}` required, enum of the four roles; no `additionalProperties: false`.
- `switchRole` documents 200, 400, 401, 503 and **no** `Set-Cookie`. `getSession`, `listDemoRoles`: 200, 401.
- `RoleNotAllowed` details: `{role, needs, reason}`; `Unauthenticated` details `{reason: none | expired}`.
- `FLAG_NOT_FOUND` details `{flag_id: "flg-99"}`; `CASE_NOT_FOUND` details `{reference: "MHC-C-0099"}`.
- Probe operations used in tests: `getQueue` and `getOwnerMetrics` both document 200, 401, 403.

---

## 5. Steps

Module boundaries (DO-3 §2.1, rule `code-design-solid-modularity`): `services/staff.py` depends on the `UnitOfWorkFactory`
and `Clock` ports and on its own repository's row models (precedent: `services/ledger.py` imports `SpendRow`); it
imports nothing from `web/`. The routes depend on `web/deps.py` providers and the service module's `SessionGone`; they
never construct the store. The hunk is the only place the store is built. No new seam is invented beyond `SessionGone`,
`RoleSwitcher` and the `lifetime_s` property (all local, listed in §8).

### Step 0 — test-writer (before the implementer)

Writes the three frozen files exactly as §6.1 and §7.1 specify, commits them on the ticket branch, records the
frozen-test manifest (the three paths and their hashes). Rules for red-for-the-right-reason:

- **Import every new module or new name inside test functions or inside the support helpers**, never at module level
  (`meridian.services.staff`, `meridian.web.routes.staff_session`, `meridian.web.schemas.staff_session`, and
  `StaffSessionRow`, `FlagRow`, `StaffSessionsRepo`, `FlagsRepo` from `repos_staff`). So
  `uv run pytest --collect-only -q` still collects the whole suite, and each frozen test fails with `ImportError` /
  `AttributeError` / a 404 / `RuntimeError("not bound: get_login_sessions")`.
- `register_staff_session` already exists on main (the AEA-01 stub), so the support module may import it at module level.

Commands: `uv run pytest -q tests/services/test_staff_service.py tests/api/test_staff_session_routes.py` (every test
red for a missing module/name or missing route) and `uv run pytest --collect-only -q` (exit 0).

### Step 1 — environment (implementer, no code)

```bash
cd <worktree>; export UV_LINK_MODE=hardlink
uv run python -c "import meridian.web.app, meridian.adapters.sqlite.db"   # import check, no baseline suite
git log --oneline -3                                                       # the test-writer's frozen commit is on top
```

### Step 2 — `adapters/sqlite/repos_staff.py`

Replace the shell. Module docstring: `"""Staff sessions and flags repositories (AEA-02 shell; body: AEA-44, stage7/staff.md section 3, STF-27)."""`
— the `StaffRepos` class docstring must **not** contain the phrase "AEA-02 creates the constructor only" (that phrase
switches `tests/unit/adapters/test_repo_shells.py` into "no public attributes" mode). Keep `from __future__ import
annotations` and a module-level `import sqlite3` so `get_type_hints(StaffRepos.__init__) == {"conn":
sqlite3.Connection, "return": NoneType}` still holds, and the constructor runs **no SQL** (the shell test builds it on
an empty `:memory:` connection).

1. Rows `StaffSessionRow`, `FlagRow` exactly as §4.2 (subclass `MeridianModel`).
2. Every datetime written with `format_wall(...)`, read with `parse_wall(...)` (both wall and demo times; cases.md §1.0).
   *Invariant: one time format in the database, UTC `+00:00`.*
3. `StaffSessionsRepo`:
   - `insert`: `INSERT INTO staff_sessions (token_hash, session_id, role, role_reset_pending, signed_in_demo,
     created_real, expires_real) VALUES (?,?,?,?,?,?,?)` inside `with integrity_errors("staff_sessions"):`;
     `role_reset_pending` as `1 if row.role_reset_pending else 0`; `role` as `row.role.value`.
   - `by_token_hash` / `by_session_id`: `SELECT token_hash, session_id, role, role_reset_pending, signed_in_demo,
     created_real, expires_real FROM staff_sessions WHERE token_hash = ?` (resp. `session_id = ?`); `None` if no row;
     `role_reset_pending=bool(r[3])`.
   - `set_role`: `UPDATE staff_sessions SET role = ?, role_reset_pending = 0 WHERE session_id = ?`; return
     `cur.rowcount == 1`. *Invariant: role and marker change together in one statement.*
   - `delete`: `DELETE FROM staff_sessions WHERE token_hash = ?`; no row is a no-op.
4. `FlagsRepo`:
   - `insert`: `INSERT INTO flags (case_ref, target, message_id, note, reason, flagged_by_role, flagged_at, status,
     reviewed_by_role, reviewed_note, reviewed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)` in `integrity_errors("flags")`;
     return `last_row_id(cur, "flags")`.
   - `get(flag_id)`: one row by `id`, `None` if absent.
   - `review`: `UPDATE flags SET status = 'reviewed', reviewed_by_role = ?, reviewed_note = ?, reviewed_at = ? WHERE id
     = ?`; return `rowcount == 1` (a second review overwrites).
   - `list_ordered`: `... ORDER BY flagged_at DESC, id DESC`.
5. `StaffRepos.__init__(self, conn)`: `self._conn = conn; self.sessions = StaffSessionsRepo(conn); self.flags =
   FlagsRepo(conn)`; class-level annotations `sessions: StaffSessionsRepo`, `flags: FlagsRepo`.
6. `__all__ = ["FlagRow", "FlagsRepo", "StaffRepos", "StaffSessionRow", "StaffSessionsRepo"]`.

Check: `uv run pytest -q tests/unit/adapters/test_repo_shells.py tests/unit/adapters/sqlite/test_uow.py` green.

### Step 3 — `services/staff.py`, part A: `ROLE_CARDS` and `StaffSessionStore`

Module docstring names AEA-44, stage7/staff.md §2, STF-3…STF-5, STF-20, STF-22. **No `logging` import, no `print`.**

1. `RoleCard`, `ROLE_CARDS` per §4.3 (`MappingProxyType({DemoRole.CUSTOMER: RoleCard(...), ...})` in that order).
2. `SessionGone(LookupError)` per §4.2.
3. `__init__`: store `uow`, `session_secret`, `demo_clock`, `lifetime_s`; `if lifetime_s <= 0: raise
   ValueError("lifetime_s must be positive")`. Property `lifetime_s`.
4. `_hash(self, token: str) -> str`: `hmac.new(self._secret.get_secret_value().encode("utf-8"),
   token.encode("utf-8"), hashlib.sha256).hexdigest()`. *Invariant: the token itself is never stored; a row copied to
   another deployment (other secret) cannot be replayed (STF-5).*
5. `_session_of(row: StaffSessionRow) -> LoginSession`: `LoginSession(session_id=row.session_id, role=row.role,
   role_reset=row.role_reset_pending, signed_in_at=row.signed_in_demo, expires_at=row.expires_real)`.
6. `start(now)`:
   1. `wall = now.astimezone(UTC)` (a naive `now` makes `format_wall` raise `ValueError`; let it).
   2. `token = secrets.token_urlsafe(32)`; `session_id = LoginSessionId(str(uuid.uuid4()))`.
   3. `demo = self._demo_clock.now().astimezone(UTC)` — **exactly one demo-clock reading** (STF-22).
   4. `row = StaffSessionRow(token_hash=self._hash(token), session_id=session_id, role=DemoRole.CUSTOMER,
      role_reset_pending=False, signed_in_demo=demo, created_real=wall, expires_real=wall +
      timedelta(seconds=self._lifetime_s))`.
   5. `with self._uow(write=True) as tx: tx.staff.sessions.insert(row); tx.commit()`.
   6. `return IssuedSession(session=self._session_of(row), token=SecretStr(token))`.
   *Invariant: both datetimes are UTC, so the login body and a later `getSession` body carry the identical string.*
7. `resolve(token, now)`:
   1. `raw = token.get_secret_value()`; `if not raw: return SessionMissing()` (no DB read).
   2. `token_hash = self._hash(raw)`; `with self._uow() as tx: row = tx.staff.sessions.by_token_hash(token_hash)`.
   3. `row is None` → `SessionMissing()` (unknown and one-character-altered tokens land here).
   4. `row.expires_real <= now` → `with self._uow(write=True) as tx: tx.staff.sessions.delete(token_hash);
      tx.commit()`; return `SessionExpired()`.
   5. otherwise `return self._session_of(row)`. **No write** on this path (absolute lifetime, WEB-5). *Invariant:
      the middleware calls this on the event loop once per request: one indexed read only.*
8. `end(token)`: `raw` empty → return; else one write unit of work deleting by `self._hash(raw)`; commit. Idempotent.
9. `session_info(session)`: `card = ROLE_CARDS[session.role]`; `return SessionInfoData(role=session.role,
   display_name=card.display_name, sees=card.sees, signed_in_at=session.signed_in_at)`. Pure.
10. `actor_for(session, needs)`: **pure, no unit of work, no clock**.
    - `if session.role.value in {r.value for r in needs}: return persona_actor(StaffRole(session.role.value))`.
    - else `return RoleRefusal(role=session.role, needs=tuple(needs), reason="role_reset" if session.role_reset else
      "wrong_role")`. *Invariants: `needs` keeps the caller's order (MC-4); reason always set (STF-20); never clears
      `role_reset` (only `switch_role` does, so two tabs both see `role_reset`).*
11. `switch_role(session_id, role)`:
    1. `with self._uow(write=True) as tx:` `if not tx.staff.sessions.set_role(session_id, role): raise
       SessionGone("login session not found")` (no commit → rollback; message holds no value);
       `row = tx.staff.sessions.by_session_id(session_id)`; `tx.commit()`.
    2. `if row is None: raise SessionGone(...)` (defensive); `return self._session_of(row)`.
    *Invariant: only `role` and `role_reset_pending` change; token hash, session id, times untouched; no new token.*

Check: `uv run python -c "from meridian.services.staff import StaffSessionStore, ROLE_CARDS"`; then the frozen
`test_session_lookup`, `test_lifetime_absolute_wall_clock`, `test_reset_sends_roles_to_customer`,
`test_switch_changes_only_role`.

### Step 4 — `services/staff.py`, part B: flags

1. `FLAG_TEXT_MAX = 2000`; `_FLAG_ID = re.compile(r"^flg-([1-9][0-9]{0,17})$")`; `_TOO_LONG = "at most 2000
   characters"`; `_NOT_IN_CASE = "not a message of this case"`.
2. `FlagIn`, `FlagRecord`, `FlagRejected` per §4.2. `FlagIn` validator:
   `@field_validator("note", "reason") @classmethod def _blank_is_none(cls, v: str | None) -> str | None: return None if
   v is not None and v == "" else v` (runs after strip and `max_length`).
3. Helpers: `_clean(v: str | None) -> str | None` (strip; `""` → `None`); `_reject(code, *, field=None,
   constraint=None, details=None) -> FlagRejected`; `_record(row: FlagRow) -> FlagRecord` with `flag_id=f"flg-{row.id}"`,
   `flagged_by=STAFF_PERSONAS[row.flagged_by_role].signature`, `reviewed_by=None if row.reviewed_by_role is None else
   STAFF_PERSONAS[row.reviewed_by_role].signature`, `at=row.flagged_at`.
4. `flag(flag, actor)` — checks in this order; **a refusal writes nothing**:
   1. `note, reason = _clean(flag.note), _clean(flag.reason)` (the service re-cleans, so a `FlagIn.model_construct`
      that bypassed validation is still refused).
   2. For `("note", note), ("reason", reason)`: `len(value) > FLAG_TEXT_MAX` → `_reject("VALIDATION_ERROR",
      field=name, constraint=_TOO_LONG)`. *The value never enters the result.*
   3. `at = self._demo_clock.now().astimezone(UTC)` (one reading).
   4. `with self._uow(write=True) as tx:`
      - `tx.core.cases_ro.owner(flag.case_ref) is None` → `return _reject("CASE_NOT_FOUND", details={"reference":
        str(flag.case_ref)})` (leaving without commit rolls back).
      - `flag.message_id is not None and not tx.core.messages.belongs_to_case(flag.message_id, flag.case_ref)` →
        `return _reject("VALIDATION_ERROR", field="message_id", constraint=_NOT_IN_CASE)`.
      - `row = FlagRow(case_ref=flag.case_ref, target=flag.target, message_id=flag.message_id, note=note,
        reason=reason, flagged_by_role=actor.role, flagged_at=at, status="new", reviewed_by_role=None,
        reviewed_note=None, reviewed_at=None)`; `new_id = tx.staff.flags.insert(row)`; `tx.commit()`.
   5. `return _record(row.model_copy(update={"id": new_id}))`.
5. `review(flag_id, note, actor)`:
   1. `m = _FLAG_ID.fullmatch(flag_id)`; `None` → `_reject("FLAG_NOT_FOUND")` with `details=None` (never echo
      arbitrary text).
   2. `note_c = _clean(note)`; too long → `_reject("VALIDATION_ERROR", field="note", constraint=_TOO_LONG)`.
   3. `at = demo now (UTC)`; `with self._uow(write=True) as tx:` `ok = tx.staff.flags.review(int(m.group(1)),
      actor.role, note_c, at)`; `not ok` → `return _reject("FLAG_NOT_FOUND", details={"flag_id": flag_id})`;
      `row = tx.staff.flags.get(int(m.group(1)))`; `tx.commit()`; `return _record(row)` (assert/raise if `None`).
6. `list_flags()`: `with self._uow() as tx: rows = tx.staff.flags.list_ordered()`; `return tuple(_record(r) for r in
   rows)`.
*Invariant (R-37, AC-13): the only tables read are `cases` and `messages` (through the two AEA-10 helpers) and the only
table written is `flags`.*

Check: frozen `test_flag_lifecycle`, `test_flag_refusals`, `test_flags_touch_only_flags_table`.

### Step 5 — `web/schemas/staff_session.py` and `web/routes/staff_session.py`

Schemas exactly as §4.2. Routes module docstring: `"""CON-10: getSession, listDemoRoles, switchRole (stage7/staff.md
section 2, section 11). Sync routes: the real store touches SQLite."""`

```python
def _info_body(info: SessionInfoData) -> JSONResponse:
    body = SessionInfo(authenticated=True, role=info.role, display_name=info.display_name, sees=info.sees,
                       signed_in_at=info.signed_in_at)
    return JSONResponse(body.model_dump(mode="json"))

def get_session(session: LoginSession = Depends(get_login_session),           # noqa: B008
                sessions: LoginSessions = Depends(get_login_sessions)) -> Response:   # noqa: B008
    return _info_body(sessions.session_info(session))

def list_demo_roles(_session: LoginSession = Depends(get_login_session)) -> Response:   # noqa: B008
    roles = RolesResponse(roles=tuple(RoleLine(role=c.role, display_name=c.display_name, sees=c.sees_line)
                                      for c in ROLE_CARDS.values()))
    return JSONResponse(roles.model_dump(mode="json"))

def switch_role(body: SwitchRoleRequest,
                session: LoginSession = Depends(get_login_session),           # noqa: B008
                switcher: RoleSwitcher = Depends(get_role_switcher)) -> Response:   # noqa: B008
    try:
        changed = switcher.switch_role(session.session_id, body.role)
    except SessionGone:
        raise ApiProblem(401, ApiErrorCode.UNAUTHENTICATED, details={"reason": "none"}) from None
    return _info_body(switcher.session_info(changed))
```

- `get_role_switcher(sessions = Depends(get_login_sessions)) -> RoleSwitcher: return cast(RoleSwitcher, sessions)`.
  *The container binds one object for both Protocols; overriding `get_login_sessions` in a test flows through.*
- `build_router()`: `add_api_route("/api/session", get_session, methods=["GET"], operation_id="getSession",
  response_model=None)`; `("/api/session/roles", list_demo_roles, ["GET"], "listDemoRoles")`;
  `("/api/session/role", switch_role, ["PUT"], "switchRole")`, each `response_model=None`.
- No cookie is written anywhere in this file; no logging; the routes add nothing for the reset gate (the middleware
  already 503s `switchRole` and makes the two reads wait, staff §11).
- A bad role value (`{"role": "admin"}`) is rejected by FastAPI → AEA-23's handler → 400 `VALIDATION_ERROR`, `field:
  "role"`, constraint = pydantic's message (lists the allowed values, never the input).

### Step 6 — `register_staff_session` in `web/container.py` (own function only)

Replace the docstring (keep "AEA-44"; drop "No-op until"):

> AEA-44 staff: StaffSessionStore, FlagService, CON-10 routes (staff.md §2). Provides deps.LOGIN_SESSIONS and
> deps.STAFF_ACCESS (one StaffSessionStore built from deps.UOW_FACTORY, settings.session_secret, Key("demo_clock") and
> limits.web.login_session_lifetime_s) and deps.FLAG_SERVICE (FlagService), and includes the CON-10 router once.
> Key("demo_clock") is AEA-30's and is read only when a clock reading is needed; until it is provided that reading
> raises RuntimeError("not bound: demo_clock"), so the app still builds. An app that create_app did not build has no
> web shell, so this does nothing.

Body (all imports inside the function; the module-level import block never changes —
`test_container_imports_only_policy_limits`):

1. Imports: `import datetime as dt`; `from meridian.config import Settings`; `from meridian.ports.runtime import
   Clock`; `from meridian.services.staff import FlagService, StaffSessionStore`; `from meridian.web.deps import
   FLAG_SERVICE, LOGIN_SESSIONS, STAFF_ACCESS, UOW_FACTORY`; `from meridian.web.middleware import WebShellState`;
   `from meridian.web.routes.staff_session import build_router`.
2. `shell = getattr(app.state, "web_shell", None)`; `if not isinstance(shell, WebShellState): return`.
3. `typed = cast(Settings, settings)`; `demo_key: Key[Clock] = Key("demo_clock")`;
   `store_key: Key[StaffSessionStore] = Key("staff_session_store")`.
4. Local forwarder:
   ```python
   class _DemoClock:
       def now(self) -> dt.datetime:
           try:
               clock = container.get(demo_key)
           except ContainerError as exc:
               if str(exc) == f"not provided: {demo_key.name}":
                   raise RuntimeError(f"not bound: {demo_key.name}") from None
               raise
           return clock.now()
   demo_clock = _DemoClock()
   ```
5. `container.provide(store_key, lambda c: StaffSessionStore(c.get(UOW_FACTORY), typed.session_secret, demo_clock,
   lifetime_s=limits.web.login_session_lifetime_s))`.
6. `container.provide(LOGIN_SESSIONS, lambda c: c.get(store_key))`;
   `container.provide(STAFF_ACCESS, lambda c: c.get(store_key))`. *Invariant: one instance for both (AC-15).*
7. `container.provide(FLAG_SERVICE, lambda c: FlagService(c.get(UOW_FACTORY), demo_clock))`.
8. `if not getattr(app.state, "staff_session_routes_included", False): app.include_router(build_router());
   app.state.staff_session_routes_included = True` (a lifespan that runs twice must not add duplicate routes).

Check: `uv run pytest -q tests/unit/web tests/unit/test_import_direction.py` (incl. `test_every_register_stub_present`,
which now skips this filled hunk but still requires "AEA-44" in its docstring).

### Step 7 — make the frozen suites green

`uv run --with pytest-xdist pytest -n 2 -q tests/services/test_staff_service.py tests/api/test_staff_session_routes.py`.
If a frozen test is wrong, **stop and report** (it goes back to the test-writer / planner); never edit it.

### Step 8 — `tests/services/test_staff_repos.py` (AC-14) and `tests/api/test_staff_session_capture.py` (AC-16)

As §7.2.

### Step 9 — `tests/contract/cases/staff_session.py` and its local driver (AC-18)

Case module (data only, ≤ 120 lines). Docstring states the closed vocabulary:

```
preconditions: "login" = sign in with the configured demo pair and keep the cookie;
               "as_representative" / "as_supervisor" / "as_owner" = after "login", PUT /api/session/role to that role.
setup: "reset_gate_held" = hold the app's ResetGate for the duration of the request.
body: {"example": <named request example>} sends that example's value; {"raw": <JSON value>} sends it as given; None = no body.
response_example: the named 200 response example the body must equal, apart from signed_in_at.
```

`ROUTE_FILE: Final = "staff_session"`; `CASES: Final[dict[str, dict[str, object]]]`:

- `getSession` (`"public": False`): `customer` 200 `("login",)` `response_example "CUSTOMER"`; `representative` 200
  `("login","as_representative")` `"REPRESENTATIVE"`; `supervisor` 200 `("login","as_supervisor")`; `owner` 200
  `("login","as_owner")`; `no_session` 401 `UNAUTHENTICATED` `()`.
- `listDemoRoles`: `roles` 200 `("login",)` `response_example "ROLES"`; `no_session` 401.
- `switchRole`: `to_representative` 200 `("login",)` body `{"example":"REPRESENTATIVE"}` `"TO_REPRESENTATIVE"`;
  `to_supervisor` (`SUPERVISOR` / `TO_SUPERVISOR`); `to_owner` (`OWNER` / `TO_OWNER`); `to_customer`
  `("login","as_representative")` (`CUSTOMER` / `TO_CUSTOMER`); `bad_role` 400 `VALIDATION_ERROR` `("login",)` body
  `{"raw": {"role": "admin"}}`; `missing_role` 400 `("login",)` `{"raw": {}}`; `no_session` 401 `()` body
  `{"example":"REPRESENTATIVE"}`; `reset_in_progress` 503 `RESET_IN_PROGRESS` `("login",)` setup `"reset_gate_held"`
  body `{"example":"REPRESENTATIVE"}`.

Local driver `tests/api/test_contract_cases_staff_session.py::test_staff_session_cases_drive_documented_statuses`:
for each case, a fresh `temp_sqlite()` and `staff_app(...)` (§6.1); apply preconditions, setup and body; assert status,
error code (when given), `assert_matches(response, operation_id)`, and the `response_example` equality (minus
`signed_in_at`). Coverage asserts: every `switchRole` request example name is used; every documented status of each
operation (`getSession` 200/401, `listDemoRoles` 200/401, `switchRole` 200/400/401/503) has a case; every 200 example
of `switchRole` (`TO_*`) is referenced. Print the case count.

### Step 10 — journey `tests/journeys/j8/test_aea_44.py` (AC-19)

`pytestmark = pytest.mark.journey`. Docstring: "J-8 (slice plan §0a): role switch and session. Level today:
mock-tested (in-process app with AEA-23's real middleware, this ticket's real store over a temp SQLite copy; not AEA-57's
harness). Integrated level blocked by AEA-57 and AEA-52."

1. `test_j8_role_switch_seen_by_second_tab_and_refusal_names_role(monkeypatch, tmp_path)`: with `temp_sqlite()` and
   `staff_app`: login → token; **tab B** `PUT /api/session/role {"role":"representative"}` → 200; **tab A** `GET
   /api/session` → `role == "representative"`, `display_name == "Riley, demo representative"` (what the user sees);
   stored: `staff_rows(db.uow)[0]["role"] == "representative"`; tab A `GET /api/staff/queue` → 200 Riley; `run_reset(db.uow)`;
   tab A `GET /api/staff/queue` → 403 `details == {"role": "customer", "needs": ["representative", "supervisor"],
   "reason": "role_reset"}`; stored: row `role == "customer"`, `role_reset_pending == 1`, same `session_id`; tab A
   `GET /api/session` → 200 `role == "customer"`. Print each step as `"<tab> <method> <path> <status> <role/reason>"`.
2. `test_j8_on_harness` with `@pytest.mark.skip(reason="blocked: integrated level needs AEA-57 (journey harness) and
   AEA-52 (staff routes wired); see docs/testing/journeys/<date>-AEA-44.md")`, body `pass`, docstring listing the same
   steps on AEA-57's harness with the production build.

### Step 11 — journey record `docs/testing/journeys/<run date>-AEA-44.md`

Same table as `docs/testing/journeys/2026-10-21-AEA-10.md`: Claim (J-8: role switch seen by a second tab; refusal names
role and reason; CON-10 routes); Level `mock-tested`; Tested revision = the code commit SHA; Environment (VPS, `uv run`,
Python 3.12, `temp_sqlite()` copy, in-process TestClient, no model); Command (the two journey commands in §7.3);
Result (pass/fail per test, skipped count); Evidence location; Remaining limitations (no browser, no AEA-57 harness,
no staff route other than probes); Blocked by `AEA-57, AEA-52`; Journeys that will exercise this code: J-1, J-6, J-7, J-8.
No secrets, no token, no demo credentials in the record.

### Step 12 — context files (AC-20), in a second commit after the code commit (it cites the code SHA)

- `.claude/reference/area-map.md` row A9, *Owns* column: remove "(all planned)" wording only if it is in this row
  (it is in the header; leave the header); *Status* column → `partly built: services/staff.py,
  adapters/sqlite/repos_staff.py (body), web/routes/staff_session.py, web/schemas/staff_session.py actual (AEA-44,
  <sha>); schema/90_staff.sql is AEA-10's (ff4b9bd); the rest planned`.
- `.claude/state/icm-progress.md`: add one row (≤ 400 characters) under the existing *Routes verified against code and
  tests* rows: `| Routes verified against code and tests | provisional | <date>: area map A9 → services/staff.py,
  repos_staff.py, web/routes/staff_session.py checked against tests/services/test_staff_{service,repos}.py and
  tests/api/test_staff_session_*.py (AEA-44, <sha>; <N> passed) | Each slice adds its route; verified when every
  area-map row is actual |`.
- `docs/design/code-design.md`:
  - §3, after the AEA-23 **Built:** line (line 185) add: `**Built:** services/staff.py, adapters/sqlite/repos_staff.py
    body, web/routes/staff_session.py, web/schemas/staff_session.py (AEA-44, <sha>).` (backticks as in the neighbouring lines).
  - tree line 303: `CON-22 login, logout, getSession (AEA-23)` → `CON-22 login, logout (AEA-23)` (getSession is CON-10,
    this ticket's).
  - tree line 308: `CON-10 role switch (AEA-44)` → `CON-10 getSession, listDemoRoles, switchRole (AEA-44)`.
  - §4.4 row `services/staff.py`: replace `AEA-44 flips the row to built; it does not rename` with `Built (AEA-44, <sha>)`.
- Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL it reports in these rows only.

### Step 13 — gates and commits

§7.3 in order (cheapest first, stop at first red). Commits with explicit paths (`git add <path> ...`, never `-A`):

1. code commit: the four `src/` files, `container.py`, the five implementer test files, the contract case file;
   message `feat(staff): login session store, role switch, flags, CON-10 routes (AEA-44)`;
2. context commit: the journey record, `area-map.md`, `icm-progress.md`, `code-design.md`; message
   `docs(AEA-44): journey record and context for services/staff.py`.

Every commit message ends with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No push (the
merge step pushes `main`); no force push.

### What the implementer must not do

- Edit any frozen file (`tests/api/staff_session_support.py`, `tests/services/test_staff_service.py`,
  `tests/api/test_staff_session_routes.py`) — report instead.
- Edit any file in §2.3, any other `register_*` hunk, `web/deps.py`, `web/app.py`, `middleware.py`, the OpenAPI,
  `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, `schema/*.sql`.
- Store, log, trace or return the token, the demo username, the password or the session secret; add any `logging`
  call to `services/staff.py` or the routes.
- Add a passcode, a per-role password, a sliding expiry, an idle timeout, a `sliding` argument, or a default for
  `lifetime_s`.
- Read the demo clock anywhere but `start` (once) and the flag methods (once each); read the wall clock at all inside
  the store (`now` is passed in).
- Clear `role_reset` anywhere but `switch_role`; touch any table but `staff_sessions` (store) and `flags` (writes) /
  `cases`, `messages` (reads via AEA-10 helpers).
- Set a cookie in `staff_session.py`; add a login/logout route; add flag routes (AEA-45).
- Construct `StaffSessionStore` outside the hunk; import `services/staff.py` at `container.py` module level.
- Read `.env`; use real secrets; call any paid model; bind any port (4019, 5184 especially); `git add -A`; push.
- Use digits-only strings that could look like a code, card or phone number in tests (use `rand_word`).

---

## 6. Data and fixtures

All synthetic. Databases are `temp_sqlite()` copies of the issued scheduling DB (read only, copied per test, deleted
after). Secrets, demo username and password come from `make_settings()` (`rand_word`, letters only, generated per test).
Wall times: `WALL_T0 = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)` (a date different from the demo date). Demo time:
`FixedClock()` = `WORKED_PAIRS_NOW` (2026-10-16 10:00 America/Chicago). Cases `MHC-C-0009`, `MHC-C-0010` built with
AEA-10's `helpers.conversation` / `case_row`; unknown case `MHC-C-0999`; message text `"synthetic flagged answer"`.

### 6.1 `tests/api/staff_session_support.py` (test-writer; frozen; ≤ 300 lines; not a conftest)

Docstring: "AEA-44 shared test support (frozen with the AEA-44 tests). Synthetic only; no `.env`, no paid call, no
socket. Imports of AEA-44's own modules happen inside helpers so the suite collects before they exist."

```python
WALL_T0: datetime            # datetime(2026, 10, 21, 19, 0, tzinfo=UTC)
LIFETIME_S = 43_200

@dataclass
class StaffHarness:
    app: FastAPI; db: TempStore; settings: Settings; wall: MutableClock; demo: FixedClock; trace: RecordingTraceSink

def queue_probe(actor: StaffActor = Depends(require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR))) -> dict[str, str]
def owner_probe(actor: StaffActor = Depends(require_staff(StaffRole.OWNER, StaffRole.SUPERVISOR))) -> dict[str, str]
    # both return {"role": actor.role.value, "name": actor.name, "signature": actor.signature}

def staff_app(monkeypatch, tmp_path, db: TempStore, *, demo: FixedClock | None = None,
              wall: MutableClock | None = None) -> StaffHarness:
    # suppress_container_starters(monkeypatch); trace = RecordingTraceSink(); demo = demo or FixedClock();
    # wall = wall or MutableClock(WALL_T0); settings = make_settings(tmp_path)
    # monkeypatch meridian.web.app.build_container with a builder that: Container(settings=settings, limits=Limits());
    #   register_web(...); container.provide(UOW_FACTORY, lambda _c: db.uow);
    #   container.provide(Key("demo_clock"), lambda _c: demo); container.provide(Key("trace"), lambda _c: trace);
    #   register_staff_session(container, app, settings=settings, limits=limits)   # the REAL hunk
    #   container.build(); return container
    # app = create_app(settings, overrides=ContainerOverrides(wall_clock=wall))
    # app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    # add_probe_route(app, "getQueue", endpoint=queue_probe); add_probe_route(app, "getOwnerMetrics", endpoint=owner_probe)

@dataclass
class ContainerHarness:
    app: FastAPI; settings: Settings; wall: MutableClock; uow: SqliteUnitOfWorkFactory   # over data_dir / WORKING_DB_NAME

def container_app(monkeypatch, tmp_path, *, wall: MutableClock | None = None) -> ContainerHarness:
    # the REAL build_container (every hunk); suppress_container_starters(monkeypatch);
    # if "No-op until" in (container_mod.register_demo.__doc__ or ""): monkeypatch container_mod.register_demo with a
    #   stand-in that, on an app with a WebShellState, provides Key("demo_clock") -> FixedClock()   (AEA-30 not merged)
    # app = create_app(settings, overrides=ContainerOverrides(wall_clock=wall)); heartbeat override as above;
    # add_probe_route(app, "getQueue", endpoint=queue_probe)

def login_token(client: TestClient, settings: Settings) -> str
    # POST /api/login with demo_pair(settings); assert 200; token = session_cookie_value(resp); client.cookies.clear()
def tab(token: str) -> dict[str, str]                       # = cookie_header(token); "tabs" are request streams sharing a cookie
def switch(client, token: str, role: str) -> Any           # PUT /api/session/role {"role": role} with tab(token)
def staff_rows(uow) -> list[dict[str, object]]             # SELECT the 7 columns FROM staff_sessions ORDER BY session_id
def flag_rows(uow) -> list[dict[str, object]]              # SELECT * FROM flags ORDER BY id
def table_counts(uow, *, skip: frozenset[str]) -> dict[str, int]   # every table in sqlite_master except `skip`
def dir_digest(path: Path) -> str                          # sha256 over sorted (relative path, bytes); "absent" if missing
def run_reset(uow) -> int                                   # exclusive uow: tx.core.reset.clear_demo_tables("reset-"+uuid4().hex[:8]); commit; return roles_reset
def seed_case(uow, ref: int) -> tuple[CaseRef, int]        # conversation + case_row + one customer message; returns (case_ref, message_id)
def example(operation_id: str, name: str, *, request: bool = False) -> dict[str, Any]   # a named example value from load_document()
def without_signed_in_at(body: Mapping[str, Any]) -> dict[str, Any]

class CountingUow:                                          # a UnitOfWorkFactory double that counts calls and raises if used
    calls: int
def make_store(uow, *, secret: SecretStr, demo: Clock | None = None, lifetime_s: int = LIFETIME_S) -> Any  # lazy import
def make_flags(uow, demo: Clock) -> Any                     # lazy import FlagService
```

`example()` paths: `getSession` 200 examples `CUSTOMER`, `REPRESENTATIVE`; `switchRole` 200 `TO_CUSTOMER`,
`TO_REPRESENTATIVE`, `TO_SUPERVISOR`, `TO_OWNER`; `switchRole` request examples (`request=True`) `REPRESENTATIVE`,
`SUPERVISOR`, `OWNER`, `CUSTOMER`; `listDemoRoles` 200 `ROLES`.

---

## 7. Checks

### 7.1 Frozen tests (test-writer writes these first; implementer must not edit)

| File | Tests (names binding) — key assertions | ACs |
|---|---|---|
| `tests/services/test_staff_service.py` | **`test_session_lookup`**: `start(WALL_T0)`; token matches `^[A-Za-z0-9_-]{43}$`; one row; `token_hash == hmac.new(secret, token, sha256).hexdigest()`; no column value contains the token; role `customer`, pending 0, `session_id` is a UUID4; `resolve` of `""`, a fresh `rand_word(43)`, and the token with its last character flipped → `SessionMissing`; the real token → `LoginSession` with that `session_id`; a store over the same DB with **another** secret → `SessionMissing`; `resolve(token, expires_at)` → `SessionExpired` and `staff_rows == []`; `end` twice and `end(SecretStr(""))` raise nothing. **`test_lifetime_absolute_wall_clock`**: `expires_at == WALL_T0 + 43,200 s`; `lifetime_s` parameter has no default (`inspect`); `resolve` at +1, +60, +3,600, +43,199 s → `LoginSession` and `staff_rows` unchanged after each; a second store with `FixedClock().advanced(timedelta(days=3))` resolves the token at +100 s → `LoginSession` with the original `signed_in_at`; at +43,200 s → `SessionExpired`, rows gone. **`test_reset_sends_roles_to_customer`**: A switched to representative, B another customer login; `run_reset` returns 1; two resolves of A (tabs) → role customer, `role_reset` True, each `actor_for(s, (REP, SUP)) == RoleRefusal(role=customer, needs=(REP, SUP), reason="role_reset")`; `session_info` customer card; B → `role_reset` False (reason `wrong_role`); `switch_role(A, REP)` → `actor_for` → `StaffActor(role=REP, name="Riley", signature="Riley (demo)")`, row pending 0; the same token resolved at every step. **`test_switch_changes_only_role`**: before/after column diff `{"role"}`; returned session keeps `session_id`, `signed_in_at`, `expires_at`; after `run_reset`, switching to the current role (customer) changes only `role_reset_pending` 1→0; again → row identical; unknown session id → `SessionGone`, no row changed. **`test_flag_lifecycle`**, **`test_flag_refusals`** (caplog; distinctive `rand_word(2001)` values; `FlagIn(note=too_long)` raises `ValidationError` whose `str` lacks the value; `FlagIn.model_construct(...)` path → `FlagRejected` naming `note` / `reason`; review note too long → field `note`; malformed `"not-a-flag"` → `FLAG_NOT_FOUND` `details is None`; `"flg-999999"` → `{"flag_id": "flg-999999"}`; message of case B on case A and `"abc"` → `message_id` / "not a message of this case"; unknown case → `{"reference": "MHC-C-0999"}`; flag count unchanged by refusals; a blank `"   "` note and reason store NULL), **`test_flags_touch_only_flags_table`** (digests of `docs/data/issued/meridian_dataset/knowledge_base/`, `eval/cases/`, `src/meridian/agent/prompts/`; `table_counts(skip={"flags","sqlite_sequence"})` equal before/after two flags and one review; flags +2) | AC-4, AC-6, AC-7, AC-9, AC-11, AC-12, AC-13 |
| `tests/api/test_staff_session_routes.py` | **`test_get_session_matches_openapi`** (four roles; `assert_matches(r, "getSession")`; body minus `signed_in_at` equals `TO_*`; `datetime.fromisoformat(signed_in_at) == h.demo.now()` and `!= WALL_T0`). **`test_list_demo_roles`** (body == `ROLES` example; also 200 as representative). **`test_switch_role_persists_on_session`** (four switches each `== TO_*` minus `signed_in_at`, validated; tab A and tab B `getSession` show the new role). **`test_switch_sets_no_cookie`** (`set_cookie_lines(r) == []`; token still works). **`test_switch_role_refusals`** (caplog + `captured_log`; `{"role":"admin"}` → 400 `field == "role"`, `"admin"` absent from `r.text`, `app_log_text(caplog)` and the stream; no cookie → 401 `{"reason":"none"}`; `with reset_gate_of(app).hold():` → 503 `{"retry_after_ms": 5000}`; `monkeypatch.setattr(StaffSessionStore, "switch_role", counting_spy)` records 0 calls; row role unchanged; every body `assert_matches(r, "switchRole")`). **`test_tampered_and_expired_cookie_401`** (control 200; flipped last character, blank `mhc_session=`, no cookie → 401 `{"reason":"none"}`; `h.wall.advance(43_200)` → 401 `{"reason":"expired"}` with a `mhc_session=` `Max-Age=0` line and `staff_rows == []`; same token again → `none`; bodies validated against `getSession`). **`test_require_staff_matrix`** (as §3 AC-8: no cookie on `/api/staff/queue` → 401; customer → 403 `{"role":"customer","needs":["representative","supervisor"],"reason":"wrong_role"}`; customer on `/api/staff/owner-metrics` → `needs == ["owner","supervisor"]`; supervisor → both 200, persona `Demo supervisor`; representative → queue `{"role":"representative","name":"Riley","signature":"Riley (demo)"}`, owner-metrics 403; owner → queue 403, owner-metrics 200; 403 bodies `assert_matches` `getQueue` / `getOwnerMetrics`; `CountingUow` store: `actor_for` for a representative on `(SUPERVISOR,)` → `wrong_role`, for a customer with `role_reset=True` → `role_reset`; `calls == 0`). **`test_no_secret_in_any_output`** (login → getSession → switchRole representative → queue probe → listDemoRoles; token, username, password and the session secret absent from every response body, `captured_log` text, `records_of(stream, "request")`, `app_log_text(caplog)`, `"".join(h.trace.seen)`, and every `staff_sessions` value; `set(body) == {"authenticated","role","display_name","sees","signed_in_at"}` for getSession and switchRole; `set(SessionInfo.model_fields)` equals the same set). **`test_register_staff_binds_providers`** (`container_app`; inside the client: `c.get(LOGIN_SESSIONS) is c.get(STAFF_ACCESS)`, `isinstance(..., StaffSessionStore)`, `.lifetime_s == 43_200`, `isinstance(c.get(FLAG_SERVICE), FlagService)`, `get_login_sessions(request_for(app)) is get_staff_access(request_for(app))`; a bare `FastAPI()` + fresh `Container` → nothing provided after `build()`; docstring has "AEA-44", no "No-op until"). **`test_role_reread_after_switch_and_reset`** (AC-17 sequence; prints each line). **`test_example_pair_switch_to_representative`** (ticket example pair). | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-8, AC-10, AC-15, AC-17, example pair |
| `tests/api/staff_session_support.py` | support (§6.1) | — |

Test-writer commands: `uv run pytest -q tests/services/test_staff_service.py tests/api/test_staff_session_routes.py`
(all red for a missing module/name/route) and `uv run pytest --collect-only -q` (exit 0).

### 7.2 Tests the implementer writes with the code

| File::test | Asserts |
|---|---|
| `tests/services/test_staff_repos.py::test_repos_staff_bodies` (AC-14) | over `temp_sqlite()` and `with db.uow(write=True) as tx:` — `isinstance(tx.staff, StaffRepos)`; session row round trip equal (UTC datetimes); `by_session_id`; `set_role(unknown)` False; `set_role(known, SUPERVISOR)` True and pending False; `delete` twice OK; three flags → ids ascending; `get`; `review` True then overwrite, `review(unknown)` False; `list_ordered` is `flagged_at` desc then id desc (two rows share a time); commit; `run_reset`; `get(3)` (the third id) is `None`; next insert id > the old max (AUTOINCREMENT kept); `FlagService.review("flg-<old id>")` → `FLAG_NOT_FOUND` |
| `tests/api/test_staff_session_capture.py::test_wf4_session_entry_points_emit_records` (AC-16) | `container_app`; `captured_log()`; login; `GET /api/session`, `GET /api/session/roles`, `PUT /api/session/role` representative, `GET /api/staff/queue`; for each call exactly one `request` record with `route` = template (`/api/session`, `/api/session/roles`, `/api/session/role`, `/api/staff/queue`), `status`, `request_id == response.headers["X-Request-ID"]`; `caller_role` `customer` for the first three (resolved before the switch runs) and `representative` for the staff call; print the records |
| `tests/api/test_contract_cases_staff_session.py::test_staff_session_cases_drive_documented_statuses` (AC-18 local) | Step 9 |
| `tests/journeys/j8/test_aea_44.py` (AC-19) | Step 10 |

### 7.3 Commands

While iterating (affected tests only):

```bash
export UV_LINK_MODE=hardlink
uv run --with pytest-xdist pytest -n 2 -q tests/services/test_staff_service.py tests/services/test_staff_repos.py \
  tests/api/test_staff_session_routes.py tests/api/test_staff_session_capture.py tests/api/test_contract_cases_staff_session.py
```

Once before the final commit — cheapest first, stop at the first red:

```bash
F="src/meridian/services/staff.py src/meridian/adapters/sqlite/repos_staff.py src/meridian/web/routes/staff_session.py \
   src/meridian/web/schemas/staff_session.py src/meridian/web/container.py tests/services tests/api \
   tests/contract/cases/staff_session.py tests/journeys/j8"
uv run ruff check $F && uv run ruff format --check $F            # pass = no findings
uv run mypy                                                       # pass = "Success: no issues found"
grep -rl "repos_staff\|services.staff\|services import staff\|staff_session\|register_staff_session\|web.container" tests/ eval/
                                                                  # every file listed must be in the next command's set
uv run --with pytest-xdist pytest -n 2 -q tests/services tests/api tests/unit/web tests/unit/adapters \
  tests/unit/test_import_direction.py tests/journeys/j8           # pass = 0 failed, 0 errors; skips only the j8 harness test
uv run python -m tests.journeys.affected --base main              # affected journeys (j8 + any that import the changed modules)
uv run pytest -m journey tests/journeys/j8/test_aea_44.py -rs     # 1 passed, 1 skipped with the "blocked:" reason
python3 ~/.claude/skills/icm-project/scripts/check_context.py .   # no FAIL
```

Why this set: `tests/api` and `tests/unit/web` include AEA-23's `full_app` tests, which now run this ticket's real hunk
(changed module `web/container.py`); `tests/unit/adapters` holds the repo-shell and unit-of-work tests that import
`repos_staff`. **No full suite:** the change touches no `conftest.py`, settings, dependency or lock file, and no module
imported across the codebase (`build-loop-test-scope.md`).

Grep evidence for the report:

```bash
grep -n "token_urlsafe(32)\|hashlib.sha256\|hmac.new" src/meridian/services/staff.py      # present
grep -n "logging\|print(" src/meridian/services/staff.py src/meridian/web/routes/staff_session.py   # none
grep -n "set-cookie\|set_cookie" src/meridian/web/routes/staff_session.py                          # none
git diff --name-only main...HEAD                                  # only §2.1 files
```

### 7.4 Later evidence (not a merge gate here)

AC-18 strict run after AEA-59; AC-19 at `integrated with a scripted model` after AEA-57 and AEA-52; CAP-4 at AEA-52.

### Checks and evidence (template form)

| Check | Command | Evidence |
|---|---|---|
| Capture verification (WF-4) | `uv run pytest -q tests/api/test_staff_session_capture.py -s` | printed `request` records, `caller_role` before/after |
| Secrets negative | `uv run pytest -q tests/api/test_staff_session_routes.py::test_no_secret_in_any_output` | pass |
| Evaluation check | n/a (no DO-5 suite scores this; R-37 via AC-13) | `test_flags_touch_only_flags_table` pass |
| Journey | `uv run pytest -m journey tests/journeys/j8/test_aea_44.py -rs` | 1 passed, 1 skipped (blocked) at `mock-tested` |

---

## 8. Risks and requests

- **R-1 Demo clock not bound until AEA-30 merges.** On an app built by the real container, a real login reads the demo
  clock in `start()`; before AEA-30 provides `Key("demo_clock")` that raises `RuntimeError("not bound: demo_clock")`
  and the login answers 500. This ticket's tests supply the clock (`staff_app`, and `container_app`'s stand-in), and
  AEA-23's `full_app` tests override the store, so nothing on `main` goes red. **Request to the orchestrator:** merge
  AEA-30 before or right after AEA-44 in wave 2, and tell the AEA-57 planner that its harness's login needs AEA-30 (or
  the same stand-in). The pattern matches AEA-40/AEA-42's lazy keys.
- **R-2 Expired-session delete runs on the event loop.** `resolve` is called by the async middleware; the expired path
  is a write (one DELETE). During a reset's exclusive transaction it could wait up to `busy_timeout` (5 s). Contract
  behaviour (staff §2 "delete the row"); AEA-23's plan already flagged it.
- **R-3 Router included at lifespan.** AEA-23's `test_every_api_route_but_login_requires_session` now also meets the
  three CON-10 routes in `full_app`; they 401 at the middleware before any store call, so it stays green. The
  `staff_session_routes_included` flag prevents duplicate routes when a lifespan runs twice.
- **R-4 Probe routes on real paths.** `staff_app`/`container_app` register a `getQueue` probe before the lifespan; when
  AEA-45 lands its real route, the probe is earlier in the route list and still wins in these tests. No edit needed.
- **R-5 Contract-case vocabulary.** `as_representative` / `as_supervisor` / `as_owner` and `reset_gate_held` extend the
  AEA-23 / AEA-43 vocabulary. **Request:** the AEA-59 planner adopts them (or files a one-file follow-up here).
- **R-6 `signed_in_at` is serialised in UTC (`...Z`)** while the examples show `-05:00`. Same instant; the OpenAPI only
  requires `date-time`; the frontend formats in America/Chicago. Tests compare instants.
- **R-7 Plan-local additions** (not in the signed sketches, all inside owned files): `SessionGone`, the `lifetime_s`
  property, `RoleSwitcher` + `get_role_switcher`, `FLAG_TEXT_MAX`, the `staff_session_store` container key. None changes
  a Protocol, a wire shape or another ticket's file.
- **R-8 AEA-45 must map `FlagRejected`** `VALIDATION_ERROR` → 400 (field and constraint as given), `CASE_NOT_FOUND` /
  `FLAG_NOT_FOUND` → 404 with `details`. The service re-checks lengths even though `FlagIn` also enforces them.
- **R-9 Frozen files hold non-frozen ACs too** (AC-1…5, 11–13, 15, 17 sit in the same two files as AC-6…10), so the
  file-level tamper check holds; AEA-23 did the same. The implementer writes only the §7.2 files.
- **R-10 AC-9 is checked at service level** (`actor_for` is the `require_staff` implementation); the HTTP form of the same
  sequence is AC-17.
- **R-11 DO-3 tree line 303** lists `getSession` under AEA-23; Step 12 moves it to line 308 (this ticket's operation).

No shared primitive is requested; no signed contract changes; no D-4…D-15 decision is answered differently.

---

## 9. Readiness

**READY.** Blocked by nothing on `main`: AEA-02, AEA-10, AEA-11 and AEA-23 are merged. AEA-30 (demo clock) is reached
lazily through `Key("demo_clock")` and doubled in tests (R-1). AEA-57, AEA-52 (journey level) and AEA-59 (strict
contract runner) are evidence-only dependencies, recorded in the journey record and §7.4.

## Gates

None (no human, paid or live gate). Security: `security-privacy-agent` reviews this diff at the wave-2 merge.
