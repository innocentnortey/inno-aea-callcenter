# Signatures and types added at Stage 7 (2026-10-21), staff

**Status:** planned, nothing built. Same rules as [DO-4](../internal-components.md) §0: these are sketches; field names,
types and validators are the agreement, method bodies are not. The OpenAPI
([`ui-contracts.openapi.yaml`](../../../ux/03-structure/ui-contracts.openapi.yaml)) stays the authority for every wire
field and code; nothing here restates a wire schema. Decision IDs (STF-n) are in
[`docs/plans/7b-decisions/staff.md`](../../../plans/7b-decisions/staff.md).
**Labels:** [Source: …] a source settles it · [Decided §7, engineering] an interface, name or location chosen at Stage 7 ·
[A] a number a measurement or later decision replaces.

**Scope (topic "staff", split from "web"):** AEA-44 (login sessions, role switch, the `require_staff` implementation,
flags, CON-10, CON-16 store), AEA-45 (staff case routes, CON-11…13, 15…17), AEA-46 (live takeover CON-14, case stream
CON-21), AEA-47 (clock advance, CON-8), AEA-48 (reads CON-18…20). **Built on, never redefined:** the web topic's
[`stage7/web.md`](web.md) — the `LoginSessions` and `StaffAccess` Protocols and `require_staff`, declared by web.md §2–§3
under these names (MC-1); the providers in `web/deps.py` (`get_login_sessions`, `get_staff_access`, `get_metrics_reads`
and its `MetricsReads` Protocol, `get_stream_poll_limiter`, `get_wall_clock`; web.md §4); `ResetGate` and `limits.web.reset_wait_s`
(web.md §5, §7); `openapi_check.py` (web.md §13); the cases topic's [`stage7/cases.md`](cases.md) — `CaseService`,
`DemoService`, `format_clock`, `ResetService`, `Cleared`, `MetricsReader`, the reset table list; AEA-01's `Limits`
(`policy/limits.py`, MC-22); DO-4 §13's `StreamKey` and `core.events`. **Defined here, built by AEA-02:** `DemoRole`,
`LoginSessionId`, `LoginSession`, `IssuedSession`, `SessionMissing`, `SessionExpired`, `RoleRefusal`, `SessionInfoData`,
the staff role types and the constants `CUSTOMER_SPEAKER_NAME` and `ROLE_ACTIONS`, in the new `domain/staff.py` (§1,
MC-2; residual pass R-W-1, R-W-13, R-W-14 in [`residuals-web.md`](../../../plans/7b-decisions/residuals-web.md)).

## What this adds, in one example

The reviewer signs in (WEB's `login` calls `LoginSessions.start`), switches to Representative
(`PUT /api/session/role` → `StaffSessionStore.switch_role`), and opens `GET /api/staff/queue`. WEB's middleware has
already resolved the cookie to a `LoginSession`; WEB's `require_staff(REPRESENTATIVE, SUPERVISOR)` calls this topic's
`StaffSessionStore.actor_for`, which returns `StaffActor(role=representative, name="Riley", signature="Riley (demo)")`.
The route hands that actor to `CaseService`. If the supervisor (a second browser) had claimed MHC-C-0007, the case's
owner role is `supervisor`, so "claimed by you" is false for every session acting as Riley, and `join` answers 409
`CASE_ALREADY_CLAIMED` with `claimed_by: "Demo supervisor"`. After a demo reset the same session's next staff call gets
403 `ROLE_NOT_ALLOWED` with `reason: "role_reset"`, and its login survives.

---

## 1. `domain/staff.py` (new, AEA-02): staff roles, the acting identity and the login-session types (consumers: AEA-23, 29, 30, 31, 44, 45, 46, 47, 48) [Decided §7, engineering; STF-1, STF-2; MC-2]

Built by **AEA-02** (wave 0) from this section, as a new file `domain/staff.py` (slice plan row AEA-02: 10 files). Pure
types and constants, no I/O. Here because AEA-23 (wave 1) declares its Protocols over these types, `CaseService` (AEA-29)
and the staff routes need the same types, and `domain/` cannot import `services/` (DO-3 §2.1). `LoginSessionId` is
defined here too, beside `LoginSession`, so every session type is in one wave-0 file (final cross-reference pass; this
supersedes MC-3's `domain/common.py` home). `StaffSessionStore`, `FlagService`, `RoleCard` and `ROLE_CARDS` stay in
`services/staff.py` (AEA-44, §2).

```python
class DemoRole(StrEnum):                              # every login role; the values of OpenAPI x-roles and of
    CUSTOMER = "customer"; REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
                                                      #   staff_sessions.role [Source: OpenAPI x-roles; MC-2]

class StaffRole(StrEnum):                             # the roles that may act on staff routes; a subset of DemoRole
    REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
    # Lists of roles keep the order they are given in (RoleRefusal.needs follows the operation's x-roles; MC-4).

class StaffPersona(MeridianModel):                    # fixed strings, copied word for word from OpenAPI examples [Source]
    name: str          # owner / claimed_by / changed_by / controller.display_name / NOT_CLAIMED_BY_YOU.owner:
                       #   "Riley" · "Demo supervisor" · "Demo business owner"
    signature: str     # flagged_by / reviewed_by / result lines: "Riley (demo)" · "Demo supervisor" · "Demo business owner"

STAFF_PERSONAS: Mapping[StaffRole, StaffPersona]      # three entries

class StaffActor(MeridianModel):
    """Who is acting on a staff route. Identity is the ROLE, not the login session (STF-1) [Source: OpenAPI
    CaseActionRequest.assignee enum riley | supervisor names roles; every owner / claimed_by / changed_by example is a
    role persona; R-48 one login, roles are labels]. Two sessions acting as Riley are the same actor and share Riley's
    claims."""
    role: StaffRole
    name: str                                         # STAFF_PERSONAS[role].name
    signature: str                                    # STAFF_PERSONAS[role].signature
    def owns(self, owner_role: StaffRole | None) -> bool: ...   # owner_role == self.role

def actor_for(role: StaffRole) -> StaffActor: ...     # the only constructor callers use

ASSIGNEE_ROLES: Mapping[str, StaffRole] = {"riley": StaffRole.REPRESENTATIVE, "supervisor": StaffRole.SUPERVISOR}
                                                      # CON-13 assign target → owner role (AEA-29 maps; AEA-45 validates)

# --- Login-session types (MC-1, MC-2, MC-5). web.md §2–§3's Protocols return them; §2's StaffSessionStore builds them.
LoginSessionId = NewType("LoginSessionId", str)       # the ONE definition: str(uuid4()) minted at login; opaque, not a
                                                      #   credential; stored as staff_sessions.session_id and
                                                      #   reset_events.asked_by_session (cases.md §1.1, §7); a correlation id (MC-9)

class LoginSession(MeridianModel):
    session_id: LoginSessionId                        # above; minted by StaffSessionStore.start (§2)
    role: DemoRole
    role_reset: bool                                  # stored as staff_sessions.role_reset_pending (§3, MC-11)
    signed_in_at: datetime                            # DEMO clock reading at start() (stored signed_in_demo); sent as
                                                      #   SessionInfo.signed_in_at (STF-22, MC-5)
    expires_at: datetime                              # WALL clock, UTC (stored expires_real); used only for expiry (WEB-5)

class IssuedSession(MeridianModel):
    session: LoginSession
    token: SecretStr                                  # the cookie value: secrets.token_urlsafe(32); only
                                                      #   HMAC-SHA256(session_secret, token) is stored (STF-5)

class SessionMissing(MeridianModel): ...              # no fields: no cookie, blank, unknown or tampered token
                                                      #   (web.md §6 gate step 3 → details.reason "none")
class SessionExpired(MeridianModel): ...              # no fields: expires_at <= now (gate step 3 → details.reason "expired")

class RoleRefusal(MeridianModel):
    role: DemoRole
    needs: tuple[StaffRole, ...]                      # in the order given to actor_for (the operation's x-roles; MC-4)
    reason: Literal["wrong_role", "role_reset"]       # always sent (STF-20)

class SessionInfoData(MeridianModel):                 # = OpenAPI SessionInfo minus the constant `authenticated` (the route
                                                      #   adds `authenticated: true`). Moved here from services/staff.py so
                                                      #   AEA-23's login route (wave 1) can type against it [R-W-1]
    role: DemoRole
    display_name: str                                 # ROLE_CARDS[role].display_name, "Customer (demo)"
    sees: tuple[str, ...]                             # ROLE_CARDS[role].sees
    signed_in_at: datetime                            # LoginSession.signed_in_at, demo clock (STF-22, MC-5)

# --- Staff-surface constants [Decided §7, engineering; residual pass R-W-13, R-W-14] ---
CUSTOMER_SPEAKER_NAME = "Customer"                    # Speaker.display_name for a customer line on STAFF surfaces (CON-12
                                                      #   conversation, CON-21 customer_message). The OpenAPI examples' "You"
                                                      #   is the customer's own view (SCR-1) and is never sent to staff.

ROLE_ACTIONS: Mapping[StaffRole, frozenset[str]] = {  # the OpenAPI CaseSummary.allowed_actions keys each role may EVER be
    StaffRole.REPRESENTATIVE: frozenset({             #   offered, read off each operation's x-roles [Source: OpenAPI x-roles]
        "claim", "claim_and_join", "release", "start", "wait", "resolve", "close_unresolved",
        "join_chat", "send_live_message", "hand_back", "close_chat",    # liveChatAction: representative only
        "log_call", "log_email",                                        # recordContactActivity: representative only
        "flag"}),                                                       # createFlag: representative, supervisor
    StaffRole.SUPERVISOR: frozenset({
        "claim", "release", "start", "wait", "resolve", "close_unresolved",
        "assign", "change_priority",                                    # applyCaseAction: supervisor only
        "flag"}),
    StaffRole.OWNER: frozenset(),                                       # getCase is read-only for the owner
}
# CaseService (AEA-29) computes allowed_actions as its lifecycle × live-state table INTERSECTED with
# ROLE_ACTIONS[actor.role] (cases.md owns the table; wording in the residual log, R-W-13). So the supervisor is never
# offered "Claim and join", "Join chat", the live reply box or Log a call / email (audit-staff A1, C1, C2), and a request
# that bypasses the UI still gets 403 ROLE_NOT_ALLOWED from require_staff (web.md §3) on liveChatAction and
# recordContactActivity, and from the per-action (SUPERVISOR,) check on assign / change_priority (§2).
```

Case ownership is stored as a `StaffRole` value (`cases.owner_role`) and rendered through `STAFF_PERSONAS`: every owner /
claimed_by / changed_by string is `STAFF_PERSONAS[role].name` (MC-12). No table stores a display name (cross-topic, CAS).

## 2. `services/staff.py`: the login-session store and the role check (AEA-44) [Decided §7, engineering; STF-3…STF-5, STF-20, STF-22, STF-24]

One class implements both Protocols that web.md §2–§3 declare (`LoginSessions`, `StaffAccess`; MC-1) and adds the role
switch. The container binds `get_login_sessions()` and `get_staff_access()` to the same instance (AEA-44's register hunk),
and `get_flag_service()` to §2's `FlagService`; AEA-46's hunk binds `get_live_chat()` to §5's `LiveChatService` (all four
providers declared in web.md §4).

```python
class StaffSessionStore:                              # implements LoginSessions and StaffAccess (web.md §2, §3)
    def __init__(self, uow: UnitOfWorkFactory, session_secret: SecretStr, demo_clock: Clock,
                 lifetime_s: int) -> None: ...
        # lifetime_s: no default; the container passes limits.web.login_session_lifetime_s (43,200 s, absolute, no idle
        # timeout; WEB-5, MC-22). No `sliding` argument (MC-1). `now` arguments are the WALL clock, from web.md §4's
        # get_wall_clock() (datetime.now(UTC), MC-20); demo_clock is read once, at start, for LoginSession.signed_in_at
        # (STF-22, MC-5).

    # --- LoginSessions (web.md §2's declaration, MC-1) ---
    def start(self, now: datetime) -> IssuedSession: ...
        # token = secrets.token_urlsafe(32); row keyed by HMAC-SHA256(session_secret, token) hex (WEB-6);
        # session_id = new UUID4; role customer, role_reset_pending 0, created_real = now, expires_real = now + lifetime_s,
        # signed_in_demo = demo_clock.now(). Returns IssuedSession(session=LoginSession(…, signed_in_at=signed_in_demo,
        # expires_at=expires_real), token=token). The token leaves only inside IssuedSession; never stored, logged or traced.
    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired: ...
        # blank or unknown keyed hash → SessionMissing; expires_real <= now → delete the row, SessionExpired.
        # Read-only otherwise (absolute lifetime: no touch write per request).
    def end(self, token: SecretStr) -> None: ...      # deletes the row; idempotent; ends nothing else (threads keep
                                                      #   their session_id; a deleted session's threads are unreachable)
    def session_info(self, session: LoginSession) -> SessionInfoData: ...
        # Part of the LoginSessions Protocol (web.md §2, R-W-1): the login body and getSession / switchRole bodies.
        # Pure over `session` and ROLE_CARDS: role, ROLE_CARDS[role].display_name and .sees, signed_in_at =
        # session.signed_in_at (demo time; STF-22, MC-5). SessionInfoData is §1's (domain/staff.py).

    # --- StaffAccess (web.md §3's declaration, MC-1); this is the require_staff implementation ---
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal: ...
        # Pure over `session` (no read, no write). session.role in needs → domain actor_for(StaffRole(session.role)).
        # Otherwise RoleRefusal(role=session.role, needs=needs,     # `needs` in the order given (MC-4)
        #   reason="role_reset" if session.role_reset else "wrong_role")  — reason ALWAYS sent (STF-20).
        # A request with no valid session never reaches it (WEB's gate answers 401 first, never 403).
        # Routes with per-action rules (CON-13 assign / change_priority: supervisor only) call it a second time with
        # (StaffRole.SUPERVISOR,). It never clears role_reset: only switch_role does, so two tabs both see role_reset.

    # --- added by this topic (CON-10) ---
    def switch_role(self, session_id: LoginSessionId, role: DemoRole) -> LoginSession: ...
        # changes role only and clears role_reset_pending; session_id, signed_in times, expiry, threads and inbox
        # scope unchanged; no new cookie (OpenAPI switchRole documents no Set-Cookie). Switching to the current role
        # is a no-op that still clears role_reset_pending.
    # session_info: listed above with the LoginSessions methods (R-W-1).

class RoleCard(MeridianModel):                        # services/staff.py (AEA-44): console copy only staff routes use (MC-2)
    role: DemoRole
    display_name: str          # SessionInfo / RolesResponse: "Customer (demo)", "Riley, demo representative",
                               #   "Demo supervisor", "Demo business owner"
    sees: tuple[str, ...]      # SessionInfo.sees, e.g. ("Queue", "Cases", "Live chat", "Review list")
    sees_line: str             # RolesResponse.roles[].sees, e.g. "The queue and cases; can claim, join, reply, log, flag"

ROLE_CARDS: Mapping[DemoRole, RoleCard]               # four entries, order customer, representative, supervisor, owner
                                                      #   (listDemoRoles returns them in this order) [Source: OpenAPI examples]
```

**Session times (STF-22, MC-5):** `LoginSession` (§1) carries exactly two times. `signed_in_at` is the demo-clock reading
at login (stored `signed_in_demo`), which `getSession` / `switchRole` send as `SessionInfo.signed_in_at`. `expires_at` is
wall time, UTC (stored `expires_real`), used only for expiry, so a demo-clock advance signs nobody out.

**Session id in records (MC-9):** `session_id` is an opaque correlation id and may appear in `auth_event`, `reset_events`
and thread rows; the token never does.

### Flags (CON-16) [Decided §7, engineering; STF-10]

```python
class FlagIn(MeridianModel):
    case_ref: CaseRef
    target: Literal["answer", "brief", "escalation"]
    message_id: str | None                            # must be a message of the case's thread (checked in the tx)
    note: str | None = Field(default=None, max_length=2000)    # stripped; blank → None (UXR-22)
    reason: str | None = Field(default=None, max_length=2000)  # free text, D4; stripped; blank → None

class FlagRecord(MeridianModel):                      # the OpenAPI Flag fields; names rendered from stored roles
    flag_id: str                                      # "flg-<n>", n from an AUTOINCREMENT key (never reused after reset)
    target: str; reason: str | None; case_ref: CaseRef; message_id: str | None; note: str | None
    flagged_by: str                                   # STAFF_PERSONAS[flagged_by_role].signature, "Riley (demo)"
    at: datetime                                      # demo clock
    status: Literal["new", "reviewed"]
    reviewed_by: str | None; reviewed_note: str | None

class FlagRejected(MeridianModel):
    code: Literal["CASE_NOT_FOUND", "FLAG_NOT_FOUND", "VALIDATION_ERROR"]
    field: str | None                                 # "message_id" for a message outside the case's thread
    constraint: str | None                            # "not a message of this case"
    details: dict[str, str] | None                    # {reference} or {flag_id}; never a rejected value

class FlagService:                                    # services/staff.py, second class (flags change for other reasons)
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock) -> None: ...
    def flag(self, flag: FlagIn, actor: StaffActor) -> FlagRecord | FlagRejected: ...      # status new, at = demo now
    def review(self, flag_id: str, note: str | None, actor: StaffActor) -> FlagRecord | FlagRejected: ...
        # status reviewed, reviewed_by_role = actor.role; reviewing twice overwrites note and reviewer (same shape)
    def list_flags(self) -> tuple[FlagRecord, ...]: ...   # newest first: at desc, then id desc [Source: SCR-8 R3]
    # Nothing here touches any table but `flags` (R-37; AEA-44 AC-11). CON-17's new_flags_count is CAS's
    # core.reads.new_flags_count().
```

## 3. Storage the staff services need (DDL: AEA-10; repository bodies: AEA-44) [Source: slice plan row AEA-10 "every `schema/*.sql`", §0; STF-21]

`90_staff.sql` is written by **AEA-10** from this field list; AEA-44 writes only the `repos_staff.py` bodies. Column
`role_reset_pending` is this section's name; cases.md §1.1, §1.3 and A-9 adopt it (MC-11). The model field stays
`LoginSession.role_reset: bool`. There is no `ended_real` column: logout and expiry delete the row. Real (wall) times are
UTC ISO-8601 with `+00:00`, written by the one formatter in `adapters/sqlite/db.py` (cases.md §1.1, MC-20).

| Table | Columns |
|---|---|
| `staff_sessions` | `token_hash TEXT PK` (hex HMAC-SHA256 keyed by the session secret), `session_id TEXT UNIQUE` (UUID4), `role TEXT CHECK IN (customer, representative, supervisor, owner)`, `role_reset_pending INTEGER NOT NULL DEFAULT 0`, `signed_in_demo TEXT` (demo, ISO), `created_real TEXT`, `expires_real TEXT` (real times UTC ISO, `+00:00`) |
| `flags` | `id INTEGER PK AUTOINCREMENT`, `case_ref TEXT`, `target TEXT CHECK IN (answer, brief, escalation)`, `message_id TEXT NULL`, `note TEXT NULL`, `reason TEXT NULL`, `flagged_by_role TEXT`, `flagged_at TEXT` (demo), `status TEXT CHECK IN (new, reviewed)`, `reviewed_by_role TEXT NULL`, `reviewed_note TEXT NULL`, `reviewed_at TEXT NULL` |

**Module: adapters/sqlite/repos_staff.py** (AEA-02 shell; AEA-44 bodies) [Decided §7, engineering; STF-27]. Rows are
typed one-for-one with the columns above; wall and demo times are read and written through `adapters/sqlite/db.py`'s
formatter (cases.md §1.0). Every repository takes the unit of work's one connection (cases.md §1.0).

```python
# adapters/sqlite/repos_staff.py (A9 / AEA-44)
class StaffSessionRow(MeridianModel):                 # one staff_sessions row
    token_hash: str                                   # hex HMAC-SHA256(session_secret, token); the token is never stored
    session_id: LoginSessionId; role: DemoRole; role_reset_pending: bool
    signed_in_demo: datetime                          # demo clock
    created_real: datetime; expires_real: datetime    # wall clock, UTC

class FlagRow(MeridianModel):                         # one flags row
    id: int | None = None                             # None before insert; AUTOINCREMENT after (FlagRecord.flag_id = f"flg-{id}")
    case_ref: CaseRef; target: Literal["answer", "brief", "escalation"]
    message_id: str | None; note: str | None; reason: str | None
    flagged_by_role: StaffRole; flagged_at: datetime  # demo clock
    status: Literal["new", "reviewed"]
    reviewed_by_role: StaffRole | None; reviewed_note: str | None; reviewed_at: datetime | None

class StaffSessionsRepo:                              # adapters/sqlite/repos_staff.py; = tx.staff.sessions
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def insert(self, row: StaffSessionRow) -> None: ...
    def by_token_hash(self, token_hash: str) -> StaffSessionRow | None: ...          # StaffSessionStore.resolve
    def by_session_id(self, session_id: LoginSessionId) -> StaffSessionRow | None: ...   # switch_role's read-back
    def set_role(self, session_id: LoginSessionId, role: DemoRole) -> bool: ...
        # sets role and role_reset_pending = 0 in one UPDATE; False when no row has that session_id
    def delete(self, token_hash: str) -> None: ...    # logout and expiry; no row → no-op

class FlagsRepo:                                      # adapters/sqlite/repos_staff.py; = tx.staff.flags
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def insert(self, row: FlagRow) -> int: ...        # returns the new id
    def get(self, flag_id: int) -> FlagRow | None: ...
    def review(self, flag_id: int, by_role: StaffRole, note: str | None, at: datetime) -> bool: ...
        # status 'reviewed', reviewed_by_role, reviewed_note, reviewed_at; overwrites a previous review; False when no row
    def list_ordered(self) -> tuple[FlagRow, ...]: ...   # flagged_at desc, then id desc [Source: SCR-8 R3]

class StaffRepos:                                     # adapters/sqlite/repos_staff.py; = UnitOfWork.staff (DO-4 §13)
    sessions: StaffSessionsRepo; flags: FlagsRepo
    def __init__(self, conn: sqlite3.Connection) -> None: ...   # builds both over the one connection
# The reset's staff_sessions UPDATE and flags DELETE are AEA-10's clear_demo_tables (§4), not methods here.
```

## 4. What a demo reset does to staff state (STF-6) [Source: UI_CONTRACTS CON-9, OpenAPI `ResetResponse.roles_reset`, SCREEN_SPECS SCR-8 "reset (FLOW-12) → empty", OpenAPI FLAG_NOT_FOUND "Cleared by reset"; slice plan §0; cases.md §1.3]

Executed by AEA-10's `core.reset.clear_demo_tables(reset_id) -> Cleared` inside AEA-31's exclusive transaction (cases.md
§1.2–§1.3); AEA-44 provides no reset method. In that transaction:

1. `staff_sessions`: no row is deleted (the login stays). Every row with `role != 'customer'` gets `role = 'customer',
   role_reset_pending = 1`. The number of such rows is `Cleared.roles_reset` → `ResetResponse.roles_reset`. A login that
   expired but was never looked up again may be counted; it can never be used, so the count is harmless.
2. `flags`: every row deleted. The AUTOINCREMENT sequence is kept (cases.md restores `sqlite_sequence` only for issued
   tables), so a stale `flg-3` link answers 404 `FLAG_NOT_FOUND`, never another flag.

## 5. `services/live_chat.py` (AEA-46) [Decided §7, engineering; STF-11, STF-12, STF-14]

```python
class StoredChatLine(MeridianModel):                  # services/live_chat.py; serialises to the OpenAPI ChatLine
    message_id: str                                   # str() of core.messages.append's int id (cases.md §1.2)
    speaker_name: str                                 # wire speaker = {kind: "representative", display_name: speaker_name},
                                                      #   STAFF_PERSONAS[actor.role].name ("Riley")
    at: datetime                                      # demo clock
    text: str                                         # as stored (STORE-redacted)

class LiveView(MeridianModel):                        # serialises to the OpenAPI LiveActionResponse
    controller_kind: Literal["ai", "human"]; controller_name: str | None     # "Riley" or None
    state: Literal["not_live", "queued", "joined", "handed_back", "closed"]; since: datetime | None
    message: StoredChatLine | None                    # only for send; None for every other action

class LiveRefused(MeridianModel):
    code: Literal["CASE_NOT_FOUND", "NOT_CLAIMED_BY_YOU", "CASE_ALREADY_CLAIMED", "NOT_LIVE"]
    details: dict[str, str | None]                    # {reference} | {owner} | {claimed_by, claimed_at} | {reason}

class LiveChatService:
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, redact_store: Callable[[str], str]) -> None: ...
        # redact_store: the container binds `lambda t: redact(t, RedactionProfile.STORE).text` (data.md §1, MC-23)
    def join(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused: ...
    def send(self, case_ref: CaseRef, text: str, actor: StaffActor) -> LiveView | LiveRefused: ...
    def hand_back(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused: ...
    def close(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused: ...
    # Each method is ONE write transaction: read the case's (thread_id, owner_role, owner_since, lifecycle) and the
    # conversation's (live_state, controller) inside it, check, then write controller, live state, any message
    # (text through redact_store, STORE profile), the thread-stream and case-stream events and one case_event with
    # the actor role (DO-6 CAP-4). A refusal writes nothing. Two staff joining at once: SQLite serialises the write
    # transactions, so the second reads the first's result.
```

**Checks, in order** (the route has already run `require_staff(REPRESENTATIVE)` and request validation):

| # | Condition | Result |
|---|---|---|
| 1 | no such case | `CASE_NOT_FOUND` {reference} (404) |
| 2 | `join`, case has no owner | `NOT_CLAIMED_BY_YOU` {owner: null} (403): screen "Claim the case first." (SCR-6 disabled state; "Claim and join" is two calls) |
| 3 | `join`, owner role ≠ actor role | `CASE_ALREADY_CLAIMED` {claimed_by: owner name, claimed_at} (409): "Already claimed by [name] at [time]. Reload." |
| 4 | `send` / `hand_back` / `close`, owner role ≠ actor role (or no owner) | `NOT_CLAIMED_BY_YOU` {owner: name or null} (403) |
| 5 | conversation ended by a demo reset | `NOT_LIVE` {reason: `demo_reset`} (409). Unreachable after cases.md §1.3 (cases and conversations cleared): a stale action meets row 1, whose OpenAPI description reads 'possibly cleared by a demo reset'. Kept as a defensive check; no test asserts it (MC-25). |
| 6 | `join` and live state already `joined` | 200, current view, nothing written (a double click) |
| 7 | `join` and live state ≠ `queued` | `NOT_LIVE` {reason: `not_waiting`} |
| 8 | `send` / `hand_back` / `close` and live state ≠ `joined` | the same action repeated on its own end state (`hand_back` on `handed_back`, `close` on `closed`) → 200 current view, nothing written; otherwise `NOT_LIVE` {reason: `not_joined` or `chat_closed`} |

`queued` exists only while simulated staff are on shift: CAS's shift end (`convert_live_queued`) sets it back to
`not_live` in its own transaction, so check 7 needs no separate staffing read and cannot race the shift end.

| Action | Conversation writes | Thread stream (CON-3) | Case stream (CON-21) |
|---|---|---|---|
| join | controller human (name, case_ref); live `joined`, since now | `representative_joined`, `ai_paused` | `controller_changed` (human, "Riley") |
| send | representative message in the same thread | `staff_message` | — |
| hand_back | controller ai; live `handed_back` | `ai_resumed` | `controller_changed` (ai, null) |
| close | controller ai; live `closed`; conversation state `closed` | `chat_closed` | `chat_closed` {reason `closed_by_staff`} |

Invariant: `controller = human` exactly when live state is `joined`. Event `line` sentences come from `policy/texts.py`.

**Live actions never touch the case's lifecycle or version** [Decided §7, engineering; R-W-16; audit-staff A4]. `join`,
`send`, `hand_back` and `close` write only the conversation columns, the message, the stream events in the table above
and the one `case_event` row (CAP-4); they never change `cases.lifecycle` or `cases.version` and append no
`case_changed`. So the representative's next `applyCaseAction` (start, resolve) uses the `version` it already holds and
never meets `VERSION_CONFLICT` "changed by Riley" from its own live action. Moving a case to `in_progress` stays the
explicit `start` action. The OpenAPI `LIVE_JOINED` example's `lifecycle: in_progress` is illustrative (examples are
checked for schema validity, not for this rule); AEA-52's AC-4 changes from "`case_changed` after a join" to
"`controller_changed` after a join, and no `case_changed`" (wording in the residual log).

## 6. Staff routes: request rules this topic sets (AEA-45, AEA-46) [Decided §7, engineering; STF-9, STF-12]

- **`LiveActionRequest.text`** (`web/schemas/staff_live.py`): for `send`, required, stripped, 1–2,000 characters
  (the customer's limit, `max_message_chars`); null or blank → 400 `VALIDATION_ERROR` field `text`, constraint
  "required for send"; longer → constraint "at most 2000 characters". For any other action a non-null `text` → 400
  field `text`, constraint "only for send". The value is never echoed.
- **Flag and review free text** (`note`, `reason`, review `note`): stripped, blank → null, at most 2,000 characters →
  400 field named, constraint "at most 2000 characters". `message_id` outside the case's thread → 400 field
  `message_id`, constraint "not a message of this case".
- **`result_line`** (`web/schemas/staff_cases.py`, composed by the route from the action, the returned case summary and
  the actor; times formatted in America/Chicago as "Mon Oct 19 · 9:00 am"):

  | Action | Line | Basis |
  |---|---|---|
  | claim | `Claimed · {actor.signature}` → "Claimed · Riley (demo)" | [Source: OpenAPI example CLAIMED] |
  | wait | `Waiting until {wake_up_at}` | [Source: OpenAPI WAITING] |
  | resolve | `{reference} resolved.` | [Source: OpenAPI RESOLVED; SCR-5 success] |
  | assign | `Assigned to {STAFF_PERSONAS[owner].signature}.` | [Source: OpenAPI ASSIGNED] |
  | change_priority | `Priority is now {level} · {word}.` | [Source: OpenAPI PRIORITY_CHANGED] |
  | release | `Released back to Unassigned.` | proposal (UI_CONTRACTS CON-13 "released back to Unassigned"; SCR-6 "Back to Unassigned") |
  | start | `In progress · {actor.signature}` | proposal (SCR-6 R4 lifecycle word "In progress") |
  | close_unresolved | `{reference} closed unresolved.` | proposal (mirrors RESOLVED) |

## 7. CON-21 stream contract (`streamCaseEvents`, AEA-46) [Decided §7, engineering; STF-13, STF-23]

```python
# web/routes/staff_live.py, async def; its own generator (no shared helper with CON-3, DO-3 S-11)
# 1 require_staff(REPRESENTATIVE, SUPERVISOR, OWNER); unknown case → 404 before the stream starts
# 2 start = Last-Event-ID if sent; otherwise the id of the newest `demo_reset` row in this case stream (0 if none), read
#   with core.events.latest_of(StreamKey case:<ref>, "demo_reset") (AEA-10), so a view opened after a reset replays only
#   post-reset events (MC-8). A connection whose start is below a `demo_reset` id receives it and closes (step 6).
#   Otherwise a first connection replays from that start (the same no-loss rule as CON-3, WEB-16; case streams are
#   short; the screen de-duplicates by event_id and message_id)
# 3 every STREAM_POLL_S (1 s [A], web.md §11) read core.events.after(StreamKey case:<ref>, last) under WEB's
#   get_stream_poll_limiter() — the ONE CapacityLimiter(4) shared with CON-3 (WEB-19) — skipped while ResetGate.held()
# 4 frames: id: <event_id> / event: <type> / data: <CaseEvent JSON>; a ": heartbeat" comment after STREAM_HEARTBEAT_S (15 s)
# 5 a reconnect (Last-Event-ID > 0) writes WEB's stream_reconnect record with case_ref (web.md §10)
# 6 close after sending `demo_reset`. NOT after `chat_closed`: the case view stays open and still gets case_changed.
```

AEA-46 test (MC-8): reset, then connect to MHC-C-0005 with no `Last-Event-ID` → no `demo_reset` frame, the stream stays
open.

Who appends what to the case stream: `customer_message` → `TurnService` (AEA-40) on a turn while `controller = human`,
in the transaction that writes the message row (web.md §9); `controller_changed`, `chat_closed` (closed_by_staff) →
`LiveChatService`; `chat_closed` (shift_ended), `case_changed` → `CaseService` (AEA-29); `demo_reset` → the reset
(AEA-31, cases.md §7), to every case stream that had events before the reset (`Cleared.case_streams`, MC-7).

**CaseEvent payloads this topic defines** (fields = the OpenAPI `Ce*` schemas; stream key `case:<CaseRef>`):
`customer_message` carries the stored (STORE-redacted) message exactly as CON-12's thread shows it, with
`speaker = {kind: "customer", display_name: CUSTOMER_SPEAKER_NAME}` ("Customer", §1; never the examples' "You") [R-W-14];
`controller_changed` carries `{kind, display_name}` from `STAFF_PERSONAS`.

## 8. CON-8 advance (AEA-47) [Source: cases.md §6; STF-15, STF-16]

```python
# web/routes/staff_clock.py: require_staff(SUPERVISOR) (x-roles), then exactly one call:
#   DemoService.advance_clock(step, actor=actor, request_id=ctx.request_id) -> ClockAdvanced     (cases.md §6, MC-13;
#   the service stores actor.role.value in demo_events.role)
# The route serialises exactly the OpenAPI ClockAdvanceResponse fields: now, label, became_overdue (cases.md §6 copies
#   the same three). No date_label: the OpenAPI has none, and with no additionalProperties: false an extra key would
#   pass the response check as silent drift [R-W-17; audit-staff A7].
# The label comes from CAS's format_clock; the route reads no clock and formats nothing.
# Step outside plus_1h | plus_4h | next_business_morning → 400 VALIDATION_ERROR field step (schema), no service call.
```

## 9. Metrics reads (AEA-48 consumes, AEA-53 implements) [Decided §7, engineering; STF-17, STF-18]

AEA-48 is wave 2 and AEA-53's concrete `MetricsReader` (cases.md §9) is wave 3, so the routes type against the
`MetricsReads` Protocol defined in stage7/web.md §4 (AEA-23, `web/deps.py`; MC-6) and reach it through web.md §4's provider
`get_metrics_reads()`. The concrete class satisfies it structurally (DO-3 S-20, injected dependency).

```python
# MetricsReads: defined in stage7/web.md §4 — owner_metrics() / monitoring() / latest_eval(), each returning
#   Mapping[str, object] with OpenAPI field names (CON-18 OwnerMetricsResponse, CON-19 MonitoringResponse,
#   CON-20 EvalResponse). The route validates the mapping through web/schemas/reads.py (field shapes from the OpenAPI).
# Unknown keys are dropped (extra="ignore") with one warning naming the dropped keys, never their values, so nothing
#   undocumented reaches a client (AEA-48 AC-3). A missing required field is a server bug (500).
# The READER stamps every time field (cases.md §9): CON-19 `as_of` = wall clock [Source: OpenAPI MonitoringResponse.as_of];
#   CON-19 `demo_now` = demo clock; CON-18 `as_of` = demo clock (STF-22). The route passes nothing and stamps nothing.
# Measure.id values are DO-7 M-n / DO-5 E-n ids [Source: OpenAPI Measure.id "M-n from the metrics registry"]; the
#   OpenAPI examples' ids are illustrative and wrong in places (STF-18). AEA-53's tests validate its output with the
#   same web/schemas/reads.py models.
# Routes depend on web.md §4's get_metrics_reads() -> MetricsReads (AEA-53 binds it).
```

Roles: `getOwnerMetrics` → `require_staff(OWNER, SUPERVISOR)`; `getMonitoring`, `getLatestEval` → every role (x-roles
`*a1`, so no `require_staff`; the login gate is enough).

## 10. Time sources on this topic's wire fields [STF-22]

| Field | Clock | Basis |
|---|---|---|
| `SessionInfo.signed_in_at`, `Flag.at`, `FlagsResponse.as_of`, `LiveState.since`, message `at`, CON-18 `as_of` | demo clock | UI_CONTRACTS *Conventions*: "Times are … America/Chicago, the demo clock"; OpenAPI `signed_in_at` examples fall on the demo date (2026-10-16); SCR-9 "as of 2:20 pm; the demo time is now Mon 7:00 am" |
| Session expiry | wall clock | WEB-5, web.md §2; a clock advance must not sign anyone out |
| CON-19 `as_of` | wall clock | OpenAPI field description (the one documented exception) |

## 11. During the reset (STF-7) [Source: web.md §7; OpenAPI documents 503 per operation]

| This topic's operations | While WEB's `ResetGate.held()` |
|---|---|
| `switchRole`, `advanceDemoClock`, `getMonitoring`, `getLatestEval` | 503 `RESET_IN_PROGRESS`, `details.retry_after_ms: 5000`, from the middleware; the routes add nothing |
| `streamCaseEvents` | never 503 and never waits, on connect or while connected (web.md §7: the SSE streams never wait); a stream skips its poll read while held, then delivers `demo_reset` (if appended for the case) and closes |
| `getSession`, `listDemoRoles`, `getQueue`, `getCase`, `applyCaseAction`, `liveChatAction`, `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag`, `getOversight`, `getOwnerMetrics` | never 503 (not documented): the middleware waits `limits.web.reset_wait_s` (5 s [A], web.md §5; MC-14, MC-22) for the gate to clear, then the route runs against the post-reset state — typically 403 `ROLE_NOT_ALLOWED` `role_reset`, or 404 for a cleared case or flag. If the reset still holds after 5 s, the request proceeds and SQLite's `busy_timeout` is the second wait (web.md §7) |

## 12. `SessionService` (CON-1): defined once, in web.md §14 [STF-28, superseded by residual R-W-2]

`SessionService`, `ChatOpened`, `ThreadHistory` and their rules are defined in
[`web.md` §14](web.md) (AEA-40 is the web topic's ticket). This topic keeps only what that definition takes from it:
`open(session: LoginSession, *, run_tag, run_id, request_id)` takes §1's `LoginSession`, and the greeting row it writes
in the same transaction as the `conversations` row is the anchor cases.md §5 uses for a staff-guidance lookup when a
customer asks for a person before typing anything (CAS-38). The earlier sketch here (`SessionService(uow, demo_clock,
demo)`) is withdrawn; web.md §14's constructor adds `limits`, `settled_view` and `agent_version`.

---

## Cross-topic assumptions

**WEB (web topic, [`stage7/web.md`](web.md))**
- Settled (MC-1): `LoginSessions`, `StaffAccess`, `require_staff` and the providers `get_login_sessions()`,
  `get_staff_access()`, `get_login_session()` are declared by web.md §2–§4 under these names; `StaffSessionStore`
  implements both Protocols unchanged. Their types (`DemoRole`, `LoginSession`, `IssuedSession`, `SessionMissing`,
  `SessionExpired`, `RoleRefusal`) are §1's, in `domain/staff.py` (MC-2). The container builds
  `StaffSessionStore(uow, session_secret, demo_clock, lifetime_s=limits.web.login_session_lifetime_s)`; no `sliding`.
- Settled (MC-5): `LoginSession.signed_in_at` is demo time and `expires_at` wall time (§1, §2); web.md §2 says so.
- Settled (MC-4): `require_staff(*roles)` passes a tuple in the operation's x-roles order and `RoleRefusal.needs` is that
  tuple, so `getOwnerMetrics` refuses with `needs: ["owner", "supervisor"]`.
- Settled (MC-6): web.md §4 declares `MetricsReads` and `get_metrics_reads()`; AEA-48 builds in wave 2 without AEA-53's
  class (§9).
- `limits.web.login_session_lifetime_s` (12 h absolute, WEB-5; AEA-01 `Limits`, MC-22), `get_stream_poll_limiter()`
  (WEB-19), `get_wall_clock()` (MC-20), `ResetGate` and `limits.web.reset_wait_s` (5 s, §5, §7; MC-14, MC-22), `STREAM_POLL_S` /
  `STREAM_HEARTBEAT_S` (§11), the `stream_reconnect` record (§10) and `tests/api/openapi_check.py` (§13, WEB-24) are used
  as declared.
- `TurnService` (AEA-40) appends `customer_message` to the case stream (`case:<ref>`) with §7's payload.
- Settled (R-W-1): `session_info(session) -> SessionInfoData` is a `LoginSessions` method (web.md §2) and
  `SessionInfoData` is §1's; the login route and `getSession` share it. Settled (R-W-2): `SessionService` is web.md §14's.

**CAS (cases topic, [`stage7/cases.md`](cases.md))**
- `CaseService` signatures use `StaffRole`, `StaffActor`, `DemoRole`, `STAFF_PERSONAS` and `ASSIGNEE_ROLES` from §1
  (`domain/staff.py`, MC-2; cases.md §5 cites staff.md §1). Settled (MC-12): case ownership is stored as a `StaffRole`
  value (`owner_role`); every owner / claimed_by / changed_by string is `STAFF_PERSONAS[role].name`; assign maps through
  `ASSIGNEE_ROLES`; `CaseService` never imports `ROLE_CARDS`.
- AEA-10 writes `90_staff.sql` from §3 (column `role_reset_pending`, MC-11) and implements §4 in `clear_demo_tables`,
  returning `Cleared.roles_reset`.
- Settled (cases.md §1.1): `conversations.live_state` (`not_live` default, `queued`, `joined`, `handed_back`, `closed`)
  and `live_since` beside `controller`; `HandoffService` sets `queued` when it opens a live-queued case, and
  `convert_live_queued` (shift end) sets it back to `not_live`.
- Settled (cases.md §1.2): the in-transaction helpers `core.cases_ro.owner(case_ref)` (thread_id, owner_role,
  owner_since, lifecycle), `core.messages.append(thread_id, role, text_redacted, at) -> int`,
  `core.messages.belongs_to_case(message_id, case_ref)` and `cases.case_events.append(event)` with `actor_role`.
- AEA-10 adds `core.events.latest_of(stream, kind) -> EventId | None` for §7 step 2 (MC-8).
- `DemoService.advance_clock(step: ClockStep, *, actor: StaffActor, request_id: RequestId) -> ClockAdvanced` and
  `format_clock` as cases.md §6 gives them (MC-13).
- Settled (MC-7): cases.md §7 appends `demo_reset` to every case stream that had events before the reset
  (`Cleared.case_streams`).
- Settled (MC-5): cases.md §9 stamps CON-19 `as_of` from `wall_clock`; CON-19 `demo_now` and CON-18 `as_of` from
  `demo_clock` (§10).
- Event ids never reused after a reset (cases.md §1.1 `AUTOINCREMENT`), so `Last-Event-ID` stays meaningful.

**GRA (graph topic)**
- AEA-02 creates `domain/staff.py` from §1, `LoginSessionId` included (MC-2; slice plan row AEA-02 "9 files" → 10, AEA-08
  adds the DO-3 §4.1 row).
- `StreamKey` (DO-4 §13) has a case variant (`case:<CaseRef>`) beside the thread variant.
- DO-4's `Controller.representative_name` comment ("Riley (demo representative)") is internal; the wire's
  `controller.display_name` is `STAFF_PERSONAS[REPRESENTATIVE].name` ("Riley").

**DAT (data topic)**
- `policy/texts.py` carries the event lines "{name} (demo representative) has joined.", "The assistant is paused while
  {name} is here.", "{name} handed the chat back to the automated assistant.", "{name} closed this chat." (OpenAPI
  `EvRepresentativeJoined`, `EvAiPaused`, `EvAiResumed`, `EvChatClosed`). Settled (DAT-29): the `live` group, with the
  OpenAPI `{name}` as placeholder `rep_name`.
- `privacy/redact.py` STORE profile is what `redact_store` binds to: the container binds it as
  `lambda t: redact(t, RedactionProfile.STORE).text` (data.md §1, MC-23).
- apps/web (UX session; audit-staff B1, B2, B3, E3; audit-shell B1) [R-W-18]: because the role lives on the session
  (STF-19) and `role_reset` stays set until `switchRole` (§2), a tab must (1) re-read `getSession` on window focus and
  `visibilitychange`, and after **every** 403 `ROLE_NOT_ALLOWED` from any call, `wrong_role` or `role_reset`, including
  a CON-21 stream answering 403; (2) then re-run the screen's reads; (3) never keep staff data on screen after a 403, but
  show the role panel with `reset = details.reason === "role_reset"`. The server needs nothing new for this: every
  request resolves the role from the session row (§2 `resolve`, read-only) and `require_staff` answers from it. The dev
  mock must match: the role shared across tabs, `role_reset` kept until a switch, per-action roles refused.

**CAS (cases topic), residual additions**
- `CaseSummary.allowed_actions` (AEA-29) = cases.md's lifecycle × live-state table ∩ `ROLE_ACTIONS[actor.role]` (§1,
  R-W-13). The owner always gets `[]`. Exact wording for cases.md is in the residual log.
- CON-12 `conversation` lines for the customer carry `display_name = CUSTOMER_SPEAKER_NAME` (§1, R-W-14), as §7's
  `customer_message` does.
