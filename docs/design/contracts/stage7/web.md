# Signatures and types added at Stage 7 (2026-10-21), web

**Status:** DRAFT, nothing built. Written by the Stage 7b web resolver (prefix WEB) for tickets AEA-01 (rate-limit
numbers only), AEA-23, AEA-40, AEA-41, AEA-42, AEA-43 and AEA-49. AEA-44…AEA-48 are the staff topic's
([`stage7/staff.md`](staff.md), prefix STF). Decisions and their basis: [`docs/plans/7b-decisions/web.md`](../../../plans/7b-decisions/web.md).
**Signature-check pass (2026-10-21):** `Contract` given fields (§13) and `SessionService` signed (§14), WEB-38.
**Residual pass (2026-10-21):** the contract disagreements the regenerated tickets still carried are closed here and in
staff.md / data.md; one row each (R-W-n) in [`docs/plans/7b-decisions/residuals-web.md`](../../../plans/7b-decisions/residuals-web.md).
Changed sections: §2 (`session_info`), §4 (`owned_stream_thread`, resume note), §7 (AEA-31 blocker), §9 (conversation
outcome, restart sweep, `TurnPayload`), §11, §13 (YAML loading, UX-session inputs), §14 (one `SessionService`, history),
§15 (new: `create_app` and `ContainerOverrides`).
**Sketch style** as in [DO-4](../internal-components.md): field names, types and signatures are the agreement; bodies
are not. **Labels:** `[Decided §7, engineering]` (an interface, name, file or internal type the resolver settled),
`[A]` (a number a measurement replaces, named next to it), `[Source: …]` (a document already settles it),
`[Innocent: WEB-1]` (waits on his answer). The OpenAPI (`docs/ux/03-structure/ui-contracts.openapi.yaml`) wins on every
wire shape and code; nothing here changes it.

**What the reviewer sees, end to end (one example).** An unsigned browser opens `https://…/staff/queue`. The middleware
finds no `mhc_session`, sees a page path, and answers `303 See Other` to `/login?return_to=%2Fstaff%2Fqueue&reason=none`
(WEB-28). `/login` and, if Innocent picks WEB-1 option A, the hashed files under `/assets/` and `/fonts/` load without a
session. The reviewer posts the demo pair to `POST /api/login`; the route compares it, calls
`LoginSessions.start(now)` (§2; the staff topic's `StaffSessionStore` implements it), sets `mhc_session` (HttpOnly,
SameSite=Lax, Secure in deploy, Max-Age 12 h) to the returned `IssuedSession.token`, and the app returns to
`/staff/queue`. `GET /api/staff/queue` passes the gate as `customer`; `require_staff(REPRESENTATIVE, SUPERVISOR)`
refuses it with 403 `ROLE_NOT_ALLOWED` `{role: customer, needs: [representative, supervisor], reason: wrong_role}`
until the reviewer switches role (CON-10, staff topic).

---

## 1. Errors on the wire: one exception, one handler (`web/errors.py`, AEA-23)

```python
class ApiProblem(Exception):                          # web/errors.py (AEA-23) [Decided §7, engineering]
    """Raised by routes and dependencies for every HTTP 4xx/5xx; never for a composed outcome (those are HTTP 200
    blocks/notices, UXR-1). The one handler in web/app.py renders ApiError {error: {code, field, constraint, details},
    request_id} and sets X-Request-ID. `details` never holds a rejected value (DO-4 §0)."""
    def __init__(self, status: int, code: ApiErrorCode, *, field: str | None = None,
                 constraint: str | None = None, details: dict[str, object] | None = None,
                 headers: Mapping[str, str] | None = None) -> None: ...
# Consumers: AEA-23 (gate, limiter, login), AEA-40…AEA-49 (routes). The 422 → 400 VALIDATION_ERROR handler (AEA-23)
# builds an ApiProblem too, so there is exactly one renderer.
```

`ApiErrorCode`'s HTTP part is exactly the OpenAPI `ApiError.error.code` enum: it **adds** `UNAUTHENTICATED`,
`LOGIN_FAILED`, `LOGIN_RATE_LIMITED` and **drops** `STAFF_AUTH_REQUIRED` (DO-4 §11 still lists it) [Source: OpenAPI
`ApiError`, `RoleNotAllowed` "Replaces STAFF_AUTH_REQUIRED"; WEB-9]. The type itself is AEA-02's (`domain/common.py`).

---

## 2. The login session: what the web shell owns (`routes/auth.py`, `web/middleware.py`, AEA-23)

The method names and the session types are the staff topic's (staff.md §2 implements them in `StaffSessionStore`);
the pure types live in `domain/staff.py` (AEA-02, wave 0; staff.md §1): `DemoRole`, `LoginSession`, `IssuedSession`,
`SessionMissing`, `SessionExpired`, `RoleRefusal` (MC-1, MC-2). The web shell owns the cookie, the credential check and
the declaration AEA-23 builds against before AEA-44 exists (AEA-44 is blocked by AEA-23):

```python
class LoginSessions(Protocol):                        # web/deps.py (AEA-23) [Decided §7, engineering; WEB-8; MC-1]
    def start(self, now: datetime) -> IssuedSession: ...                          # login: role customer
    def resolve(self, token: SecretStr, now: datetime) -> LoginSession | SessionMissing | SessionExpired: ...
                                                                                  # middleware, once per request
    def end(self, token: SecretStr) -> None: ...                                  # logout; idempotent
    def session_info(self, session: LoginSession) -> SessionInfoData: ...         # login body + getSession [R-W-1]
# `now` is always get_wall_clock() (§4). staff.md §2's StaffSessionStore satisfies this Protocol structurally. switch_role
# is CON-10's and is called by AEA-44's route directly, so it is not in this Protocol (interface segregation).
# SessionInfoData is staff.md §1's (domain/staff.py, AEA-02, wave 0), so AEA-23 (wave 1) types against it without
# importing services/staff.py (wave 2). The login route answers
#   LoginResponse(session=SessionInfo(authenticated=true, **sessions.session_info(issued.session)), landing="/")
# and AEA-44's getSession route uses the same method, so both bodies come from one builder [R-W-1].
# Consumers: AEA-23 (gate, login, logout), AEA-44 (binds StaffSessionStore in its register hunk; getSession).
```

**Lifetime** [Decided §7, engineering; WEB-5]: `limits.web.login_session_lifetime_s = 43_200` (12 h, §5), **absolute**,
no idle timeout, no `sliding` argument. The container builds `StaffSessionStore(uow, session_secret, demo_clock,
lifetime_s=limits.web.login_session_lifetime_s)` (MC-1, MC-22). Expiry runs on the **wall clock**, never the demo
clock, so advancing the demo clock signs nobody out (staff STF-4 agrees). `SessionInfo.signed_in_at` is demo time
(STF-22); only expiry uses the wall clock (`LoginSession.signed_in_at` = demo clock at `start()`, `expires_at` = wall
clock UTC; MC-5).

**Cookie** [Source: OpenAPI `securitySchemes.mhcSession` "HttpOnly, SameSite=Lax, Secure in deploy"; Max-Age Decided §7,
engineering]: `Set-Cookie: mhc_session=<IssuedSession.token>; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200` plus
`Secure` when `Settings.cookie_secure` is on (deploy). The value is the token itself (`secrets.token_urlsafe(32)`;
only `HMAC-SHA256(session_secret, token)` is stored, STF-5); the web shell unwraps the `SecretStr` only to write the
header, treats it as opaque and never logs it (DO-6 *Content*: session cookies never). Logout and an expired lookup
answer with `Max-Age=0`. A login with a still-valid cookie ends that session first, then starts a new one.

**Credential check** [Source: SCREEN_SPECS N-28 "the same body and timing whatever the cause"; OpenAPI `LoginFailed`
"every cause (wrong username, wrong password, empty)"; WEB-10]: username and password are each compared with
`hmac.compare_digest` against `Settings.demo_username` / `demo_password` (both always compared, no short-circuit).
Empty strings pass schema validation (`LoginRequest` has no `minLength`) and fail the comparison → 401 `LOGIN_FAILED`.
A missing field, a non-string or a non-JSON body → 400 `VALIDATION_ERROR`.

---

## 3. Role gate: the `require_staff` declaration (`web/deps.py`, AEA-23)

```python
class StaffAccess(Protocol):                         # web/deps.py (AEA-23) [Decided §7, engineering; WEB-8; MC-1, MC-4]
    def actor_for(self, session: LoginSession, needs: tuple[StaffRole, ...]) -> StaffActor | RoleRefusal: ...
    # staff.md §2's StaffSessionStore implements it. LoginSession, StaffRole, StaffActor and RoleRefusal are the
    # domain/staff.py types (AEA-02; staff.md §1).
# Provider: get_staff_access() -> StaffAccess, declared once in §4; AEA-44's register hunk binds the StaffSessionStore.

def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]: ...     # [Decided §7, engineering; WEB-8]
    # A FastAPI dependency factory. The middleware has already answered 401 for no session, so this never sees one.
    # It takes RequestContext.session (a LoginSession), calls get_staff_access().actor_for(session, roles) with `roles`
    # as the tuple received, in the order of the operation's x-roles (MC-4), and on RoleRefusal raises
    # ApiProblem(403, ROLE_NOT_ALLOWED, details={"role", "needs", "reason"}) with `needs` = RoleRefusal.needs, that
    # tuple [Source: OpenAPI RoleNotAllowed]; otherwise it returns the StaffActor. Per-action checks pass a one-role
    # tuple, (StaffRole.SUPERVISOR,). Chat, demo and session routes never use it (they accept every role, R-48);
    # advanceDemoClock uses require_staff(SUPERVISOR).
# Consumers: AEA-44…AEA-48 (staff topic). Tests override get_staff_access with a double.
```

---

## 4. Request context and the providers in `web/deps.py` (AEA-23, sole owner)

```python
EVAL_KEY_HEADER = "X-Meridian-Eval-Key"               # web/middleware.py (AEA-23) [Decided §7, engineering; WEB-7]
RUN_ID_HEADER   = "X-Meridian-Run-Id"                 #   shared with AEA-24's harness (DAT-15); never logged or traced
RUN_TAG_HEADER  = "X-Meridian-Run-Tag"                #   "eval" | "load"; absent or other with a valid key → "eval"

@dataclass(frozen=True)
class RequestContext:                                  # built by the middleware, read through get_request_context
    request_id: RequestId
    client_ip: str                                    # last X-Forwarded-For entry when Settings.trust_proxy_headers
                                                      #   (Railway's edge appends the peer) else the socket peer
                                                      #   [A: confirm Railway's header at first deploy, AEA-56]
    session: LoginSession | None                      # None only on the public paths (§6); domain/staff.py (MC-1)
    run_tag: Literal["live", "eval", "load"]          # eval/load only when the eval key matches (hmac.compare_digest)
    run_id: str | None                                # None unless the key matches (DO-6 Correlation)
    turn_verdict: LimitVerdict | None                 # set on submitTurn only (§5)

# Providers (each resolves from the container on app.state; each is a plain function so tests override it):
def get_request_context(request: Request) -> RequestContext: ...
def get_login_session(ctx: RequestContext = Depends(get_request_context)) -> LoginSession: ...  # never None after gate
def get_login_sessions() -> LoginSessions: ...        # AEA-44 binds (§2)
def get_staff_access() -> StaffAccess: ...            # AEA-44 binds (§3); the same StaffSessionStore instance
def get_flag_service() -> FlagService: ...            # AEA-44 binds (staff.md §2)
def get_session_service() -> SessionService: ...      # AEA-40 (§14) def get_turn_service() -> TurnService: ...    # AEA-40
def get_person_requests() -> PersonRequestService: ...  # AEA-42 (§8)
def get_handoff_service() -> HandoffService: ...      # AEA-29      def get_case_service() -> CaseService: ...    # AEA-29
def get_reply_composer() -> ReplyComposer: ...        # AEA-21 (graph topic; WEB-20)
def get_identity_service() -> IdentityService: ...    # AEA-27      def get_demo_service() -> DemoService: ...    # AEA-30
def get_reset_service() -> ResetService: ...          # AEA-31      def get_reset_gate() -> ResetGate: ...        # AEA-23 (§7)
def get_live_chat() -> LiveChatService: ...           # AEA-46
def get_metrics_reads() -> MetricsReads: ...          # AEA-53 binds (cases.md §9 MetricsReader, structurally) [MC-6]
def get_uow_factory() -> UnitOfWorkFactory: ...       # AEA-10 (stream polling reads, ownership checks)
def get_stream_poll_limiter() -> anyio.CapacityLimiter: ...   # ONE CapacityLimiter(4) per process, shared by CON-3 and
                                                      #   CON-21 so all streams together hold ≤ 4 threads (DO-3 §2.3
                                                      #   rule 4; WEB-19, staff STF agrees)
def get_rate_limiter() -> RateLimiter: ...            # §5
def get_wall_clock() -> Callable[[], datetime]: ...   # returns `lambda: datetime.now(UTC)`: session expiry, limiter
    # windows, reset `now`. The container passes this ONE callable to LedgerService, SchedulerJob, AlertWriter, Watchdog,
    # AlertEvaluator, MetricsReader, PersonRequestService and every `now` argument of StaffSessionStore (MC-20).
    # Stored wall times are UTC ISO-8601 with +00:00 (cases.md §1.1); Chicago is for display only.
# require_staff(*roles): declared in §3 (same file, web/deps.py).
def owned_thread(thread_id: str, session: LoginSession = Depends(get_login_session),
                 uow: UnitOfWorkFactory = Depends(get_uow_factory)) -> ThreadId: ...
    # Reads core.conversations.lookup(thread_id). A ConversationRow of this session → the ThreadId. An EndedThread
    # whose demo_session == str(session.session_id) → ApiProblem(410, SESSION_ENDED, details={"reason":
    # <ended_threads.reason>}). Anything else (malformed id, unknown, another session's live or ended thread) → the
    # identical ApiProblem(404, SESSION_NOT_FOUND) (OpenAPI path parameter is a plain string; WEB-34; MC-16).
    # Consumers: AEA-40 (getChatThread, submitTurn), AEA-42 (requestPerson, saveFollowUp): each documents 410.
def owned_stream_thread(thread_id: str, session: LoginSession = Depends(get_login_session),
                        uow: UnitOfWorkFactory = Depends(get_uow_factory)) -> ThreadId: ...
    # [R-W-3] streamChatEvents documents only 200 / 401 / 404, and the OpenAPI wins on codes, so CON-3 uses this
    # variant: the same lookup as owned_thread, but an EndedThread of this session answers the IDENTICAL 404
    # SESSION_NOT_FOUND (body equal to the other 404s apart from request_id). Implemented as owned_thread with the 410
    # branch mapped, never a second lookup. Consumer: AEA-41 only. Adding 410 to streamChatEvents is an OpenAPI change
    # (Innocent / UX session); if made, AEA-41 switches to owned_thread and nothing else moves.
# Not decided here (Innocent / UX session, R-W-12): SCREEN_SPECS SCR-1 says the chat resumes after the reviewer signs in
# again. As specified, every login starts a new LoginSession (§2) and a thread belongs to the session that opened it, so
# the earlier session's thread answers 404 to the new one. Nothing in this file is changed until that is answered.

class MetricsReads(Protocol):                         # web/deps.py (AEA-23) [Decided §7, engineering; MC-6]
    def owner_metrics(self) -> Mapping[str, object]: ...   # CON-18, OpenAPI field names
    def monitoring(self) -> Mapping[str, object]: ...      # CON-19
    def latest_eval(self) -> Mapping[str, object]: ...     # CON-20
# cases.md §9's MetricsReader (AEA-53) satisfies it structurally (services never import web/, DO-3 §2.1). AEA-48's
# routes validate each mapping through web/schemas/reads.py (staff.md §9's rules).
```

A service whose ticket is later than AEA-23 is declared by name and bound in its own `register_<area>()` hunk; until
bound, the provider raises `RuntimeError("not bound: <name>")` at call time, never at import. `ResetGate` is AEA-23's
own and is bound from the start, so the middleware never meets an unbound gate. [Decided §7, engineering]

Routes pass `str(session.session_id)` wherever DO-4 takes `demo_session: str` (`RunTurn`, `IdentityService.inbox`,
`send_code`). `LoginSession.session_id` is a `LoginSessionId`, defined once in staff.md §1 (`domain/staff.py`, AEA-02;
the UUID4 string minted at login); typed callers such as `ResetService.reset` take it unconverted.

---

## 5. Rate limits (`web/middleware.py` + `policy/limits.py`)

```python
# policy/limits.py (AEA-01 owns the file; MC-22): ONE frozen `Limits`, as DO-4 passes it (GraphDeps.limits). Its
# `web` field is this topic's; `spend`, `brakes`, `identity` and the rest are their topics' (models.md §6; graph-tools
# C-9: brakes.tool_rounds, IdentityLimits). The container hands each consumer its field; no second literal anywhere.
# Each [A] is "set above 20" (PRD §5 line 276) for the 20-at-once load, and is replaced by the E-8 load re-measure at
# Stage 9 (0 limited responses at 20 conversations from one IP and one login) and by abuse seen in the deploy logs.
# [WEB-2, WEB-4]
@dataclass(frozen=True)
class WebLimits:                                      # Limits.web
    chat_turns_per_thread_per_min: int = 20     # [A] a person types far fewer; one scripted case has ≤ ~10 turns
    chat_turns_per_session_per_min: int = 600   # [A] 20 closed-loop conversations at SP-1's p50 4.7 s ≈ 255/min [C], ×2
    chat_turns_per_ip_per_min: int = 600        # [A] same arithmetic: the harness and a reviewer's office share one IP
    reads_per_session_per_min: int = 120        # [A] apps/web polls the demo status every 10 s per open tab (POLL_MS)
    reads_per_ip_per_min: int = 240             # [A]
    login_rejects_per_ip: int = 10              # [A] rejected attempts per window; while over, every attempt (even the
    login_reject_window_s: int = 600            #   right pair) answers 429 LOGIN_RATE_LIMITED + Retry-After (AEA-23 AC-5)
    resets_per_ip: int = 10                     # [A] per window; never reached by a reviewer, so not a cool-down (R-48)
    reset_window_s: int = 600
    login_session_lifetime_s: int = 43_200      # 12 h absolute, no idle timeout [Decided §7, engineering; WEB-5]
    reset_wait_s: int = 5                       # [A] [Source: UI_CONTRACTS *Still open* "the 5 s reset-lock wait"] (§7)
# Limits gains `web: WebLimits` (this class) beside `spend: SpendLimits` (defined in models.md §6; MC-22).

class LimitScope(StrEnum): THREAD = "thread"; SESSION = "session"; IP = "ip"; LOGIN_IP = "login_ip"; RESET_IP = "reset_ip"

@dataclass(frozen=True)
class LimitVerdict:
    allowed: bool
    scope: LimitScope | None                          # the first scope that refused
    retry_after_ms: int | None                        # ceil to whole seconds × 1000

class RateLimiter:                                    # web/middleware.py (AEA-23); in-process token buckets (DO-3 S-17)
    def __init__(self, limits: WebLimits) -> None: ...  # the container passes limits.web
    def check(self, scope: LimitScope, key: str, now: float) -> LimitVerdict: ...   # consumes a token when allowed
    def peek(self, scope: LimitScope, key: str, now: float) -> LimitVerdict: ...    # no token consumed
    def record_login_reject(self, ip: str, now: float) -> None: ...                 # called by routes/auth.py
    def record_reset(self, ip: str, now: float) -> None: ...                        # called by routes/demo.py
# Idle buckets are evicted after 2 × their window, so memory is bounded by recent callers. Keys: thread_id, the session
# id, the client IP; never the cookie value.
```

**Which operation gets which answer** [Source: OpenAPI responses per operation; WEB-3]:

| Operations | Over the limit |
|---|---|
| `startChatSession`, `listDemoInbox`, `getStaffing`, `getDemoClock`, `getMonitoring`, `getLatestEval` (the six that document 429) | `429 REQUEST_RATE_LIMITED`, `details.retry_after_ms` (SESSION then IP read buckets) |
| `login` | `429 LOGIN_RATE_LIMITED`, `Retry-After` seconds and `details.retry_after_ms` (LOGIN_IP) |
| `submitTurn` | never 429: the middleware puts the THREAD → SESSION → IP verdict in `RequestContext.turn_verdict`; AEA-40 answers HTTP 200 with the `RATE_LIMITED` notice (§9; WEB-12) |
| `resetDemo` | RESET_IP over → `409 RESET_IN_PROGRESS` with `details.retry_after_ms` (its only documented refusal; WEB-27) |
| `requestPerson` and every other operation | never limited (CON-4: DO-1 §8.2; the rest document no 429) |

The six-operation set is a constant in `web/middleware.py`; `tests/api/openapi_check.py` asserts it equals the set of
operations whose OpenAPI responses contain `429` (minus `login`), so a contract change breaks the build, not production.

---

## 6. The gate and public paths (`web/middleware.py`, AEA-23; registry filled by AEA-49)

```python
class PublicPaths:                                    # on app.state; filled only by register_<area>() hunks
    def add_exact(self, method: str, path: str) -> None: ...
    def add_prefix(self, method: str, prefix: str) -> None: ...
    def is_public(self, method: str, path: str) -> bool: ...
# AEA-23 registers ("POST", "/api/login") and ("GET", "/healthz"). AEA-49 registers ("GET", "/login") and, only if
# Innocent answers WEB-1 with A, the build's static prefixes ("GET", "/assets/") and ("GET", "/fonts/").

# Gate order per request (middleware, async, no worker thread):
#   1 RequestId (UUID4) → X-Request-ID on every response, errors included
#   2 reset gate (§7)
#   3 session: is_public → continue with session None; else LoginSessions.resolve(SecretStr(cookie or ""),
#     get_wall_clock()()) (MC-1):
#       SessionMissing → /api/* and other JSON paths: ApiProblem(401, UNAUTHENTICATED, details={"reason": "none"})
#                        any other GET path (a page): 303 to /login?return_to=<path+query>&reason=none   (WEB-28)
#       SessionExpired → the same two answers with reason "expired", plus Set-Cookie mhc_session Max-Age=0
#       LoginSession   → RequestContext.session
#   4 rate limits (§5)   5 eval tag (§4)   6 route   7 the `request` log record (§10)
# return_to is accepted by /login only when it is a same-origin path starting with "/" and not "//" (no open redirect).
```

---

## 7. Reset in progress (`services/reset_gate.py`, AEA-23)

Lives under `services/` and is owned by AEA-23 (wave 1), so `ResetService` (AEA-31) can take it by constructor without
importing `web/` (cases.md §7 does). [Decided §7, engineering; WEB-13]
**AEA-31 is blocked by AEA-23** (`ResetGate`, `ResetAlreadyRunning`, and `owned_thread` for its AC-6), recorded here and
in merge MC-27; slice-plan row AEA-31's *Blocked by* reads "10, 23" once the orchestrator applies MC-27 (no wave moves:
23 is wave 1, 31 wave 2) [R-W-11].

```python
class ResetAlreadyRunning(Exception): ...

class ResetGate:                                      # one per process, built by the container in AEA-23's hunk
    def held(self) -> bool: ...                       # lock-free read; the middleware calls it on every request
    def hold(self) -> ContextManager[None]: ...       # ResetService.reset (AEA-31) holds it for the whole reset;
                                                      #   raises ResetAlreadyRunning if already held (→ 409 at CON-9)
    async def wait_clear(self, timeout_s: float) -> bool: ...   # anyio.sleep(0.1) loop on the event loop, no thread
```

| While `held()` | Answer |
|---|---|
| Operations whose OpenAPI documents 503 `RESET_IN_PROGRESS`: `startChatSession`, `submitTurn`, `listDemoInbox`, `setStaffing`, `advanceDemoClock`, `switchRole`, `getMonitoring`, `getLatestEval` | the middleware answers `503 RESET_IN_PROGRESS`, `details.retry_after_ms: 5000`, at once |
| `resetDemo` | the route calls `ResetService.reset(get_wall_clock()(), request_id=ctx.request_id, session_id=session.session_id, role=session.role)` (cases.md §7; `now` is the wall clock, MC-19, MC-20): `ResetAlreadyRunning` → `409 RESET_IN_PROGRESS`; `ResetFailed` → `500 RESET_FAILED`. The operator script passes `session_id=None, role=None` with its own gate and is for a stopped service only (data.md §7, MC-19) |
| `/healthz`, `login`, the SSE streams | never wait: `/healthz` reads the heartbeat; CON-3/CON-21 skip their poll read while held |
| Every other operation (incl. `requestPerson`, whose 503 is `HANDOFF_FAILED`, not a reset) | `await wait_clear(limits.web.reset_wait_s)` (5 s [A], §5; MC-14), then run against the post-reset state, so its own documented answer applies (410 `SESSION_ENDED`, 404 `CASE_NOT_FOUND`, 403 `ROLE_NOT_ALLOWED` `role_reset`, …). If the reset still holds after 5 s, the request proceeds and SQLite's `busy_timeout` (5 s [A], DO-3) is the second wait (staff.md §11 describes the same outcome) |

The set of 503 operations is a constant checked against the OpenAPI by `openapi_check.py`, like the 429 set.

---

## 8. CON-4 person request (`services/person_request.py`, AEA-42)

```python
class PersonRequest(MeridianModel):                   # [Decided §7, engineering; WEB-21, WEB-22]
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId; demo_session: str
    run_tag: Literal["live", "eval", "load"]; run_id: str | None

class PersonRequestOutcome(MeridianModel):
    result: Literal["case_created", "live_queued", "already_open"]
    block: HandoffBlock | LiveQueuedBlock             # domain/blocks.py ReplyBlock members (AEA-02; named as the OpenAPI
                                                      #   schemas, like QuickChecksBlock), built by ReplyComposer
    settled: SettledView                              # from core.settled_for(thread_id, read_at) (AEA-10; graph-core §6)

class HandoffWriteFailed(Exception): ...              # HandoffService failed after its one retry → 503 HANDOFF_FAILED

class PersonRequestService:                           # services/person_request.py (A8, owned by AEA-42)
    def __init__(self, uow: UnitOfWorkFactory, handoff: HandoffService, composer: ReplyComposer,
                 trace: TraceSink, demo_clock: Clock, wall_clock: Callable[[], datetime]) -> None: ...   # MC-17
    def request(self, cmd: PersonRequest) -> PersonRequestOutcome: ...
    # 1 core.turns.begin(ids, received_at): completed → return the stored outcome (same body as the first call);
    #   running → wait ≤ 3 s [A] for it, then the stored outcome, else HandoffWriteFailed (503, "tap again");
    #   new / failed → run
    # Steps 2–5 run inside `with trace.turn(ids) as span:` (models.md §4; MC-17).
    # 2 HandoffRequest(thread_id=cmd.thread_id, turn_id=cmd.turn_id, reason=customer_requested_person,
    #   priority=priority_for(reason) from policy/handoff.py (AEA-14; P3, cases.md §3.3), rule_id="CON4.person",
    #   trigger="con4", identity=core.reads.identity_state(thread_id) (cases.md §1.2)) — every required DO-4 §7 field
    # 3 HandoffService.open(req, ctx) with TurnContext(ids, budget, now=<one demo-clock reading>,
    #   demo_session=cmd.demo_session, span=span, intake=None) (graph-core §2)
    # 4 result: created → "case_created" (or "live_queued" when case.promise.live_queued); not created and
    #   case's turn_id == cmd.turn_id → the same result as the first call; otherwise "already_open"
    # 5 block via ReplyComposer.handoff_block(result) (graph topic, WEB-20); settled via
    #   core.settled_for(cmd.thread_id, read_at=ctx.now) (graph-core §6), made the wire view by
    #   composer.settled_view(settled, core.reads.identity_state(thread_id), the conversation's controller) (graph-core §13)
    # 6 after the span closes: core.turns.finish(turn_id, TurnRecord(status="completed",
    #   trace=TurnTrace(gate_result="person_requested", path="handoff", outcome="handed_off"),
    #   trace_id=span.trace_id, trace_export=trace.export_status(span), response=<stored outcome>, …))
    #   (graph-core §2, GRC-21), as AEA-40 does (MC-17). In the same transaction, when `result` is "case_created" or "live_queued", set
    #   conversations.outcome = 'handed_off' (cases.md A-7; MC-18), so the abandonment sweep never claims it.
    # No admission, no SpendGuard, no rate limit, no model (OpenAPI requestPerson).
    # Tests (AEA-42): the turn row carries trace_id and trace_export (off with NullTraceSink); CON-4, then a sweep
    #   31 min later leaves outcome = 'handed_off' (MC-18).
```

`saveFollowUp` stays a direct `CaseService.set_followup` call from the route; an unverified thread asking for
`destination: "on_record"` gets `409 NOT_ALLOWED_IN_STATE`, `details.state: "not_verified"`, before the service is
called (WEB-23).

---

## 9. CON-2 additions (`services/turn.py`, AEA-40)

```python
class TurnService:
    def run_turn(self, cmd: RunTurn) -> TurnResponse: ...              # DO-4 §14, unchanged
    def rate_limited(self, cmd: RunTurn, verdict: LimitVerdict) -> TurnResponse: ...   # [Decided §7, engineering; WEB-12]
    # Called by routes/chat.py instead of run_turn when RequestContext.turn_verdict.allowed is False.
    # HTTP 200, notice RATE_LIMITED (actions ["talk_to_person"], retry_turn_id null), `settled` from
    # core.settled_for(thread_id, read_at=<one demo-clock reading>) (graph-core §6),
    # no model, turn row TurnRecord(status="failed", trace=TurnTrace(gate_result="clear", path="degraded",
    # outcome="degraded_handoff", degrade_reason="rate_limit"), …) (graph-core §2), so the same turn_id re-runs once the
    # bucket refills. Same notice builder as BUSY and SPEND_CAP_REACHED; text from policy/texts.py.
```

Step 4 of `run_turn` (customer message row), when `conversations.controller == "human"` in that same transaction, also
appends the CON-21 `customer_message` event to the case stream (payload and stream key: staff.md §7). [Source: DO-4 §13
"writers append … inside their own transaction" + §14 step 4; WEB-15]

Settled elsewhere and carried by `run_turn` (not new signatures): admission checks `ledger.allow_turn()` only; the turn
span is opened with `with trace.turn(ids) as span`, put on `TurnContext.span`, and after it closes
`trace.export_status(span)` and `span.trace_id` go on the `turn` row (models.md MOD-9, MOD-10, MOD-11); every customer
message writes `conversations.last_customer_wall_at` (UTC, MC-20), and the ending turn sets `conversations.outcome`
(cases.md A-7). Step 4 runs `parse_intake` once, writes the message row and gets its id; `run_turn` then builds
`TurnInput` (non-secret fields plus `message_id`) and `TurnContext(…, span=span, intake=intake)` exactly as graph-core
§2 rules 1–2 (graph-core X-6). Step 5 receives a `GraphOutcome` (graph-core §2, GRC-20, GRC-21); `TurnService` never
reads `ConversationState`. Step 7 persists `outcome.check_events` as given, one `core.check_events.append(event,
thread_id)` row each (graph-core §11 builds them; graph-nodes §1), and the turn row as
`core.turns.finish(turn_id, TurnRecord(trace=outcome.turn_trace, …))`.

**Where each DO-6 `turn` field comes from** (DO-6 *Records*; `TurnRecord` fields are graph-core §2's):

| DO-6 field | Source |
|---|---|
| `turn_id`, `thread_id`, `request_id`, sequence, received time | `core.turns.begin(ids, received_at)` at step 3 |
| `gate_result`, planner decision, specialists run, `outcome`, `degrade_reason` (+ `path`, `danger_raised`) | `outcome.turn_trace` (`TurnTrace`); step 6 sets `degraded_handoff` / `timeout` on a `DEADLINE` halt |
| replied time, `server_ms` | `TurnRecord.replied_at`, `server_ms`, stamped by `TurnService` when the reply body is written |
| counts of model calls, tokens, cost | summed from this `turn_id`'s `spend_ledger` rows (models.md §6) |
| count of tool calls | this `turn_id`'s `lookup_log` rows (one per dispatched call, graph-tools §1) |
| `trace_id`, `trace_export` | `span.trace_id`, `trace.export_status(span)` after the span closes (models.md §4) |

**Who writes `conversations.outcome`, and when** [Decided §7, engineering; R-W-5; DO-7 M-18 end rule; cases.md A-7].
`TurnService` reads only `GraphOutcome` (never `ConversationState`), so the graph tells it whether the turn closed every
open task: `GraphOutcome.closed_every_open_task: bool` (graph-core §2 adds it; wording in the residual log). Rules, applied
in the step-7 transaction that finishes the turn row:

| This turn | `conversations.outcome` becomes |
|---|---|
| `turn_trace.outcome == "handed_off"` | `handed_off` (replaces any value) |
| `turn_trace.outcome == "safety_reply"` and the stored value is `open` | `safety_reply` |
| `turn_trace.outcome in ("answered", "acted")` and `outcome.closed_every_open_task` and the stored value is `open` | `ai_resolved` |
| anything else (`to_staff`, `degraded_handoff`, a timeout, a rate-limited or BUSY turn) | unchanged |

Step 4 (the customer message row) sets an `ai_resolved` or `abandoned` value back to `open` in the same transaction: the
customer came back, so the conversation had not ended. `handed_off` and `safety_reply` are never reopened. CON-4 keeps
its own rule (§8: `handed_off`); AEA-30's sweep writes only `abandoned` (cases.md §6). Example: turn 3 books slot 56 and
the booking task is `done` with nothing else open → `ai_resolved`; ten minutes later "actually, can you move it?" → step 4
reopens to `open`, and the move turn sets `ai_resolved` again.

**Start-up restart sweep** (DO-3 §2.3 rule 6; DO-6 *Missing instrumentation*) [Decided §7, engineering; R-W-4]. AEA-40's
`register_` hunk calls `core.turns.fail_running()` once, while the container is built and before the app serves its first
request. It marks **every** `turns` row still `running`: status `failed`, `path` `degraded`, `outcome`
`degraded_handoff`, `degrade_reason` `timeout`, other columns as `begin` left them; it returns the swept ids, and the hunk
logs one `turn_sweep` count line (ids and a count only). Why every row and not "older than 65 s": the service is one
process on one Railway volume (DO-2 "One service, one process, one volume": Railway volumes forbid replicas), so no turn can be in flight before the first request,
and `received_at` is a demo-clock reading that a clock advance moves by hours, so it cannot measure 65 s. A swept turn is
`failed`, so a browser retry of the same `turn_id` re-runs it (AC-3). The repository method is cases.md §1.2's (AEA-10
follow-up merged first, slice plan §3); its wording is in the residual log.

**`TurnPayload`** [R-W-15]: `web/schemas/chat.py`'s request model validates the OpenAPI `TurnPayload` into the one
Python `TurnPayload` union graph-core places in `domain/` (AEA-02); the route builds `RunTurn(payload=…)` from it and
defines no second union.

---

## 10. Records written by the web shell

```python
# Structured log records through web/logging.py's LOG-profile allow-list formatter (AEA-23). No table. [WEB-11]
# request:          {"record": "request", "request_id", "route" (template, never the raw path), "status",
#                    "duration_ms", "caller_role" ("anonymous" | DemoRole), "thread_id" | null, "error_kind" on 5xx}
# auth_event:       {"record": "auth_event", "request_id", "outcome": "ok" | "rejected" | "rate_limited" | "logged_out",
#                    "session_id" (the opaque UUID; null when rejected or rate_limited), "at"}
#                    DO-6 WF-18 names the opaque demo session id as this workflow's correlation id (MC-9: the
#                    session_id is a correlation id, the token never appears); `rate_limited` is added so R-41
#                    refusals are countable. Never the username, password or cookie value.
# stream_reconnect: {"record": "stream_reconnect", "request_id", "thread_id" | "case_ref", "last_event_id",
#                    "replayed": int}   — emitted by routes/events.py (AEA-41) when Last-Event-ID > 0   [WEB-18]
# signal:           graph-nodes.md §4's SignalRecord fields, emitted by agent/signals.py (AEA-21) on the logger
#                    "meridian.signal"; the LOG allow-list passes exactly those fields (IDs and codes only;
#                    graph-nodes cross-topic 6)
```

---

## 11. CON-3 stream rules (`web/routes/events.py`, AEA-41)

```python
STREAM_POLL_S = 1.0          # [A] DO-3 S-11; replaced by the measured first_event_ms at Stage 9
STREAM_HEARTBEAT_S = 15      # [Source: OpenAPI streamChatEvents "Heartbeat comment every 15 s (decided 2026-10-21)"]
CHAT_EVENT_TYPES = frozenset({"representative_joined", "staff_message", "ai_paused", "ai_resumed", "chat_closed",
                              "staffing_changed", "shift_ended", "clock_changed", "demo_reset"})   # OpenAPI ChatEvent
# Ownership: owned_stream_thread (§4): malformed, unknown, another session's and THIS session's ended thread all answer
#   the identical 404 SESSION_NOT_FOUND before the stream starts (the operation documents no 410) [R-W-3].
# Start point: Last-Event-ID header if present, else 0 (the whole thread's stream) [WEB-16]. apps/web's transport
#   (src/api/transport.ts) sends the header whenever it holds an id: from CON-1 / getChatThread's last_event_id, then
#   from the last frame; the screen de-duplicates by event id.
# One stream per thread: demo-wide events (staffing_changed, clock_changed, demo_reset) are written by their writers
#   as one row per OPEN thread, in the writer's own transaction [WEB-17; cases.md §6–§7 do this]; the route reads one
#   stream and never merges.
# Reads: core.events.after(thread_stream, last) under get_stream_poll_limiter(), skipped while ResetGate.held().
# A stored row whose type is not in CHAT_EVENT_TYPES is never sent. After sending chat_closed or demo_reset, close.
# Replay from 0 is safe for thread streams after a reset: reset threads are tombstoned and thread ids are never reused.
#   Case streams (CON-21) are different: their refs are re-seeded, so staff.md §7 starts a header-less connection at
#   the newest demo_reset row (MC-8).
```

---

## 12. Frontend serving (`web/frontend.py` + `register_frontend()`, AEA-49)

```python
def register_frontend(container: Container, app: FastAPI) -> None: ...   # web/frontend.py [Source: slice plan row AEA-49]
    # Settings.web_dist_dir (default apps/web/dist; /app/apps/web/dist in the image, data.md §7) present → mount it
    #   read-only: files under /assets/ and /fonts/ with their content types; every other GET path not under /api/ and
    #   not /healthz answers dist/index.html (SPA fallback); path traversal and dotfiles 404. Registers its public
    #   paths (§6).
    # Missing dist: Settings.require_frontend True (deploy) → start-up fails naming the setting and the path;
    #   False (local, CI) → one warning log `frontend_dist_missing`, nothing mounted, page paths fall through to
    #   FastAPI's JSON 404 (after the gate). [Decided §7, engineering; WEB-30]
```

`web/container.py` (AEA-01) needs a `register_frontend` stub; AEA-01's stub list and slice plan §3's container row omit
AEA-49 (WEB-29). Page serving is registered in DO-6 as **WF-19** (WEB-31): class user-operation; emitter the middleware;
correlation `request_id`; records `request` only (route template `spa_fallback` or `/assets/{file}`, never the raw path
or query string); capture check in AEA-49's tests; evaluation and metrics `n/a — serving files decides nothing`.

---

## 13. The shared OpenAPI response check (`tests/api/openapi_check.py`, AEA-23)

```python
# [Source: slice plan row AEA-23 owns the file; library Decided §7, engineering — WEB-24]
# Dev dependencies (AEA-01's pyproject): jsonschema>=4.18 (Draft 2020-12, the dialect of OpenAPI 3.1) with its
# `referencing` registry for "#/components/..." refs, and PyYAML to load the file. The OpenAPI is read, never written.
@dataclass(frozen=True)
class OperationSpec:                                  # one operation of the OpenAPI, indexed by operationId [WEB-38]
    operation_id: str; method: Literal["get", "post", "put", "patch", "delete"]; path_template: str
    responses: Mapping[str, Mapping[str, JsonValue]]  # status ("200", "429", …) → {content type → schema object}
    event_schema: str | None                          # x-event-schema for an SSE operation (ChatEvent / CaseEvent)
@dataclass(frozen=True)
class Contract:                                       # the parsed OpenAPI, read once; nothing writes it [WEB-38]
    source: Path                                      # docs/ux/03-structure/ui-contracts.openapi.yaml
    version: str                                      # info.version, printed in a failing assertion's message
    operations: Mapping[str, OperationSpec]           # operationId → spec
    error_codes: frozenset[str]                       # ApiError's `code` enum
    registry: referencing.Registry                    # "#/components/..." refs resolved for jsonschema
def load_contract() -> Contract: ...                  # cached per test session
def assert_response_matches(response: httpx.Response, operation_id: str) -> None: ...
    # status is documented for the operation; content type matches; the body validates against that status's
    # schema with FormatChecker (uuid, date-time); X-Request-ID present; for ApiError bodies error.code is in the enum
def assert_sse_frames_match(frames: Sequence[SseFrame], operation_id: str) -> None: ...
    # each data: line validates against the operation's x-event-schema (ChatEvent / CaseEvent); id equals event_id
def operations_documenting(status: str) -> frozenset[str]: ...   # feeds the 429 and 503 set checks (§5, §7)
# Note: jsonschema ignores OpenAPI's `discriminator`; oneOf still validates, so a body matching two members fails loudly.
# Consumers: every route ticket (AEA-40…AEA-49, AEA-52, staff STF tickets), AEA-57's journey client, AEA-59.

class ContractLoader(yaml.SafeLoader):               # tests/api/openapi_check.py (AEA-23) [Decided §7, engineering; R-W-9]
    """load_contract reads the OpenAPI with this loader, never plain yaml.safe_load. PyYAML resolves YAML 1.1 implicit
    types; the OpenAPI is written to YAML 1.2 / JSON meaning. The class removes the `tag:yaml.org,2002:timestamp`
    implicit resolver (so `2026-10-16T14:20:00-05:00` stays a string, as a JSON body carries it) and replaces the bool
    resolver with one that matches only true|True|TRUE|false|False|FALSE (so `yes`, `no`, `on`, `off`, `ON`, `OFF`, `y`,
    `n` stay strings). Ints, floats and null resolve as before. Measured 2026-10-21 (AEA-59): safe_load turns 371
    example timestamps into datetime and the getStaffing example names ON / OFF into booleans."""
# AEA-23 AC-24 adds: the STARTED example's greeting.at loads as a str, the BurningCheckBlock option "yes" as "yes", and
#   getStaffing's 200 example names are "ON" and "OFF" (the same three facts AEA-59 AC-5 asserts).
```

**Inputs AEA-59 takes from the UX session, not design gaps** [R-W-10]: (1) a JSON export of every dev scenario's resolved
response bodies, path and format named by the UX session in `docs/plans/ux-join/` (the scenarios are TypeScript
transforms a Python test cannot read); (2) the drift-check pins: `apps/web/src/api/types.gen.ts` stays the committed
path, `gen:types` keeps its spec path and `-o` arguments, and `openapi-typescript` stays exactly pinned in
`apps/web/package.json`. Until the UX session publishes them, AEA-59 checks what exists today and its evidence record says
so; nothing in this file waits on them.

---

## 14. CON-1 conversations: `SessionService` (`services/session.py`, AEA-40) [WEB-38; one definition, R-W-2]

**This is the one signature.** web.md §14 and staff.md §12 signed it twice; this section now holds both halves (staff's
`LoginSession` argument, `run_tag` / `run_id` and the `ChatOpened` result; web's `settled_view`, `limits` and `thread()`),
and staff.md §12 points here.

**In practice.** The reviewer opens the chat. `POST /api/chat/sessions` calls `SessionService.open(session, run_tag=…,
run_id=…, request_id=…)`: one write transaction creates the `conversations` row owned by this login session and the
greeting message (say id 401), and the route renders `ChatOpened` as 201 `StartSessionResponse`, adding only the CON-3
URL. After a reload, `GET /api/chat/sessions/{thread_id}` passes `owned_thread` (§4) and calls `SessionService.thread`,
which rebuilds everything the reviewer saw, the greeting and Riley's lines included, so the stream can resume after it.

```python
class ChatLimits(MeridianModel):                      # services/session.py; = OpenAPI Limits (CON-1 `limits`)
    turn_deadline_ms: int; still_working_after_ms: int; browser_give_up_after_ms: int; max_message_chars: int
    # 60000 / 10000 / 65000 / 2000, copied from AEA-01's Limits (api-con-mapping §0 timing constants; SDQ-1)

class ChatOpened(MeridianModel):                      # what open() returns; the route renders OpenAPI StartSessionResponse
    thread_id: ThreadId                               # new UUID4 (DO-4 §0 ThreadId)
    greeting_message_id: int                          # the messages row holding the greeting (core.messages.append's id)
    greeting_text: str                                # render(TextId greeting) word for word (R-1: says it is automated)
    greeting_at: datetime                             # demo clock
    clock: ClockView                                  # = OpenAPI DemoClock (cases.md §6 format_clock)
    staffing: StaffingView                            # = OpenAPI Staffing (DemoService.staffing(), cases.md §6)
    controller: Controller                            # kind "ai", no name (DO-4 §1)
    settled: SettledView                              # empty: settled_view(core.settled_for(thread_id, read_at=greeting_at), …)
    limits: ChatLimits
    last_event_id: EventId                            # 0 for a new thread (OpenAPI events.last_event_id)

class HistoryEntry(MeridianModel):                    # one OpenAPI ChatThread.turns[] item
    turn_id: str                                      # see the id rule below
    speaker_kind: Literal["assistant", "customer", "representative", "event"]
    speaker_name: str | None                          # Speaker.display_name: STAFF_PERSONAS[REPRESENTATIVE].name for a
                                                      #   representative line; None for every other kind
    at: datetime                                      # demo clock, as stored
    text: str | None                                  # customer, representative and event lines; None for assistant turns
    blocks: tuple[ReplyBlock, ...]                    # assistant turns only (domain/blocks.py, AEA-02); () otherwise

class ThreadHistory(MeridianModel):                   # what thread() returns; the route renders OpenAPI ChatThread
    thread_id: ThreadId
    state: Literal["open", "closed"]                  # "closed" when conversations.live_state == 'closed' (staff closed
                                                      #   it); "ended_by_reset" never reaches here (owned_thread → 410)
    entries: tuple[HistoryEntry, ...]
    settled: SettledView
    clock: ClockView
    staffing: StaffingView
    last_event_id: EventId                            # the thread stream's newest event id (0 when none)

class SessionService:                                 # services/session.py (A8, AEA-40); DO-3 :348 "SessionService.open"
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, demo: DemoService, limits: Limits,
                 settled_view: Callable[[Settled, IdentityState, Controller], SettledView],
                 agent_version: str) -> None: ...
        # settled_view: the container passes ReplyComposer.settled_view (graph-core §13), so this service never
        #   imports agent/ (DO-3 §2.1) and the panel is built by the same code as a turn's. agent_version:
        #   Settings.agent_version (data.md §9 item 1b), stamped on the conversations row.
    def open(self, session: LoginSession, *, run_tag: Literal["live", "eval", "load"], run_id: str | None,
             request_id: RequestId) -> ChatOpened: ...                                    # CON-1 startChatSession
        # ONE write transaction: the conversations row (thread_id, demo_session = str(session.session_id) (§4), run_tag /
        # run_id from RequestContext (eval and load only with the eval key, DO-6), agent_version, outcome 'open',
        # controller 'ai', live_state 'not_live', last_customer_wall_at NULL) and the greeting row
        # core.messages.append(thread_id, "assistant", greeting_text, at=demo now) (cases.md §1.2). Writes no turn row,
        # no event, no lookup, calls no model. Both rows commit together, so every conversation has at least one message,
        # which cases.md §1.2 core.messages.handoff_anchor relies on (CAS-38). Any role may open a chat (x-roles *a1); a
        # reset in progress answers 503 from the middleware before this runs (§7).
    def thread(self, thread_id: ThreadId) -> ThreadHistory: ...                           # CON-1 getChatThread
        # thread_id already passed owned_thread (§4). One read-only unit of work; never a code (stored text is
        # STORE-redacted). entries, merged in time order (`at`, then the row's id within its table; a customer message
        # sorts before its own turn's reply) [R-W-6; audit-customer A-1, A-2]:
        #   1 the greeting: assistant, blocks (TextBlock(greeting_text),), turn_id "greeting"
        #   2 each customer message row: customer, text as stored, turn_id = the row's turn_id
        #   3 each completed CON-2 turn: assistant, blocks = the stored response's `blocks`, at = its reply message row's at
        #   4 each completed CON-4 turn (gate_result person_requested): a customer entry, text
        #     render(TextId.PERSON_REQUEST_LABEL) ("Talk to a person", data.md §2), then an assistant entry, blocks
        #     (stored outcome's `block`,); both carry the CON-4 turn_id
        #   5 each representative message row: representative, speaker_name "Riley", text, turn_id f"msg-{message_id}"
        #   6 each thread-stream event row that carries a line (representative_joined, ai_paused, ai_resumed,
        #     chat_closed, staffing_changed): event, text = the stored `line`, turn_id f"evt-{event_id}"; a shift_ended
        #     row adds an assistant entry, blocks (its stored `handoff` HandoffBlock,). clock_changed (no line) and
        #     staff_message (already entry 5) add nothing.
        # A failed or running turn contributes only its customer message. settled as in open, with
        # core.reads.identity_state and the conversation's controller; last_event_id is read in the same unit of work as
        # the entries, so the stream resumes exactly after the newest line shown (WEB-16).
        # Card `answered` is not rebuilt (the stored choice keeps no card_id): the UX session treats a history card as
        # spent (audit-customer A-3, R-W-6).
```

The route copies `ChatOpened` into `StartSessionResponse` (adding `events.url = /api/chat/sessions/{thread_id}/events`)
and `ThreadHistory` into `ChatThread` (`speaker = {kind, display_name}`); `assert_response_matches` (§13) checks both.
`ChatLimits`, `ClockView`, `StaffingView` and `SettledView` serialise field for field. Consumers: AEA-40 (writes it;
`get_session_service`, §4), AEA-51 (wires `settled_view`), AEA-24 (the harness starts every scripted conversation here),
AEA-57 / AEA-58 (J-1 refresh and resume read `thread()`).

---

## 15. App factory and the test-only container overrides (`web/app.py`, AEA-23) [Decided §7, engineering; R-W-8]

**In practice.** The deployed start command runs uvicorn's factory with no arguments, so nothing is overridden. AEA-57's
journey launcher calls `create_app(settings, overrides=ContainerOverrides(choice=…, structured=…, tools=…))` with its
scripted adapter in all three maps; the real gateway, ledger, graph, services and SQLite then run on that adapter.

```python
@dataclass(frozen=True)
class ContainerOverrides:                             # web/app.py (AEA-23). TEST-ONLY: no env name, no Settings field and
                                                      #   no CLI flag can build one; production never passes it
    choice: Mapping[ChoiceRole, ChoiceModel] | None = None          # replaces the adapter for each listed role
    structured: Mapping[StructuredRole, StructuredModel] | None = None
    tools: Mapping[ToolRole, ToolCallingModel] | None = None
    trace: TraceSink | None = None                    # an in-memory sink or exporter the test built (AEA-51 capture);
                                                      #   None → the container's own choice (models.md §7)
    # Each port object keeps the read-only `provider` attribute (models.md §5). The RoleSpec (model, caps, redaction)
    # still comes from Settings, so ledger rows name the configured model (models.md §7 AEA-51 assertion).

def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> fastapi.FastAPI: ...
    # settings None → Settings() from the environment (AEA-02 config.py). The lifespan builds AEA-01's container once with
    # (settings, overrides) and closes it once (AEA-23 AC-23). The container passes `overrides` through untouched, as it
    # does Settings, and only register_graph (AEA-51) reads it: for a role present in a map it pairs that object with the
    # role's RoleSpec instead of calling adapter_for (models.md §7); every other role, and every role when overrides is
    # None, gets the real adapter.
```

**Guards** (AEA-23 tests): `create_app()` with no arguments builds no override; a grep over `src/meridian/` finds
`ContainerOverrides(` constructed nowhere; `register_graph` is the only reader (AEA-51 AC-1: "no double is reachable
except the scripted provider adapter and the in-memory trace exporter"). Consumers: AEA-57 (journey launcher), AEA-51
(integration harness, `register_graph`), AEA-59 and AEA-58 (through AEA-57's launcher). AEA-01's container builder gains
the one pass-through keyword `overrides` (residual log R-W-8).

---

## Cross-topic assumptions

| Assumed from | What this file relies on | If it turns out otherwise |
|---|---|---|
| **staff (STF)**, AEA-02/AEA-44 | `DemoRole`, `StaffRole`, `StaffActor`, `RoleRefusal`, `LoginSession`, `IssuedSession`, `SessionMissing`, `SessionExpired` and `LoginSessionId` live in the new `domain/staff.py` (AEA-02, wave 0; MC-2; staff.md §1). **Settled at merge.** | AEA-23 records `blocked-on AEA-02` for the missing file |
| **staff (STF)**, AEA-44 | `StaffSessionStore(uow, session_secret, demo_clock, lifetime_s)` implements `LoginSessions` and `StaffAccess` (§2–§3) with staff.md §2's method names; `lifetime_s` has no default, the container passes `limits.web.login_session_lifetime_s`; `resolve()` reports expiry by the wall clock (MC-1, MC-22) | — |
| **staff (STF)**, AEA-46/48 | CON-21 uses `get_stream_poll_limiter()`, skips polls while `ResetGate.held()`, emits `stream_reconnect` (§10); the metrics reads go through §4's `MetricsReads` / `get_metrics_reads()` (MC-6) | — |
| **cases (CAS)**, AEA-31 | `ResetService` takes `ResetGate` by constructor and holds `gate.hold()` for the whole reset (so a second reset raises `ResetAlreadyRunning`); `reset(now: datetime, *, request_id: RequestId, session_id: LoginSessionId \| None, role: DemoRole \| None) -> ResetDone \| ResetFailed` (MC-19); `ResetDone` = `{ok, open_chats_ended, roles_reset, clock}` (cases.md §7) | AEA-43 maps whatever CAS names to the same wire answers |
| **cases (CAS)**, AEA-10/AEA-53 | `core.conversations.lookup` returns `ConversationRow \| EndedThread \| None` and `EndedThread` carries `demo_session` and `reason` (`ended_threads`, cases.md §1.1), for `owned_thread`'s 410 (MC-16); `MetricsReader` satisfies `MetricsReads` structurally (MC-6); wall times stored UTC (MC-20) | — |
| **cases (CAS)**, AEA-10/30/31 | `staffing_changed`, `clock_changed` and `demo_reset` are appended once per open thread's stream in the writer's transaction; `events.id` is `AUTOINCREMENT`, never reused after a reset (cases.md §1, §6, §7) | — |
| **cases (CAS)**, AEA-30 | `format_clock` in `services/demo.py` is the one formatter; `DemoService.clock_view()` / `advance_clock()` return `label` and `date_label` ready to copy; routes never format (WEB-25) | — |
| **cases (CAS)**, AEA-10 | `core.turns.begin/finish` store and return an opaque serialised response, so a CON-4 outcome uses the same idempotency path as CON-2; `core.settled_for(thread_id, read_at)` is the one `Settled` builder (graph-core §6, X-2); `core.conversations.lookup` tells ended from unknown | — |
| **cases (CAS)**, AEA-29 | `HandoffService.open` stays idempotent per thread, keeps the originating `turn_id` on the case, and does **not** write a `turn` row (the CON-4 row is AEA-42's, §8) | Two writers of the CON-4 turn row; raise with the parent |
| **graph (GRA)**, AEA-21 | `ReplyComposer` exposes a pure `handoff_block(result: HandoffResult) -> HandoffBlock \| LiveQueuedBlock` usable outside a graph turn (WEB-20). **Accepted** (graph-core X-9); the class, incl. `settled_view` used by §8 and §14, is signed in graph-core §13 (GRC-24) | AEA-42 records `blocked-on AEA-21` |
| **graph (GRA)** | `TurnContext`, `TurnInput` (and how `Intake`, the code digits and `message_id` reach the graph) are graph-core §2's; AEA-40 builds both as its rules 1–2 say, AEA-42 builds `TurnContext` with `intake=None` (WEB-14; graph-core X-6). **Settled at merge** | — |
| **graph (GRA)**, AEA-21/AEA-40 | `run_graph` returns `GraphOutcome(reply, turn_trace, check_events, halt)` (graph-core §2, GRC-20, GRC-21); `TurnService` step 7 persists `outcome.check_events` and `TurnRecord(trace=outcome.turn_trace, …)`; the LOG allow-list passes the `signal` record (§10) (graph-nodes §1, §4, cross-topic 6). **Accepted at merge** | — |
| **graph (GRA)**, AEA-01 | `Limits` also carries `brakes.tool_rounds` (2) and `IdentityLimits(code_ttl_s=600, tries=3, max_sends=3)` beside `web` (graph-tools C-9); this file declares only `WebLimits` (§5) | — |
| **graph (GRA)**, AEA-43 | The CON-6 route unwraps `InboxMessage.code` only while serialising the response and renders `body` from `policy/texts` (`INBOX_CODE_BODY` / `INBOX_CODE_GONE`, code `"······"` when None) (graph-tools §5, C-10). **Accepted at merge** | AEA-43 uses whatever text ids AEA-03 defines |
| **graph (GRA)**, AEA-02 | `ApiErrorCode` carries the OpenAPI enum (WEB-9); `Settings` (AEA-02 `config.py`, MC-21; the full field list is graph-core §12, GRC-22) adds `cookie_secure: bool`, `trust_proxy_headers: bool`, `web_dist_dir: Path` (default `apps/web/dist`), `require_frontend: bool` (default False) beside `demo_username`, `demo_password`, `eval_key`, `session_secret` (env names: data.md §9 item 1, which includes `LANGFUSE_PROJECT_ID` after `LANGFUSE_BASE_URL` (MC-21), plus `MERIDIAN_COOKIE_SECURE`, `MERIDIAN_TRUST_PROXY_HEADERS`, `MERIDIAN_WEB_DIST_DIR`, `MERIDIAN_REQUIRE_FRONTEND`) | AEA-23/AEA-49 record `blocked-on AEA-02` for the missing field |
| **data (DAT)**, AEA-24 | the harness sends the three `X-Meridian-*` headers (§4) and logs in once (DAT-15) | — |
| **data (DAT)**, AEA-50/54/56 | the image builds `apps/web` (DAT-21) into `/app/apps/web/dist`; the Railway variables set `MERIDIAN_COOKIE_SECURE=true`, `MERIDIAN_TRUST_PROXY_HEADERS=true`, `MERIDIAN_REQUIRE_FRONTEND=true`, `MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist`, listed in AEA-54's guide | A deployed image without `dist/` fails start-up loudly instead of serving no UI |
| **data (DAT)**, AEA-25 | Whether the README holds the login values is DAT-3 (Innocent); nothing here depends on it | — |
| **staff (STF)**, AEA-02/AEA-44 (residual R-W-1) | `SessionInfoData` lives in `domain/staff.py` (staff.md §1); `StaffSessionStore.session_info` implements §2's Protocol method | AEA-23 builds `session` from a double and records `blocked-on AEA-02` |
| **cases (CAS)**, AEA-10 (residual R-W-4) | cases.md §1.2 adds `core.turns.fail_running() -> tuple[TurnId, ...]` with §9's column values; an AEA-10 follow-up merged before AEA-40 | AEA-40 records `blocked-on AEA-10` for the sweep only |
| **graph (GRA)**, AEA-02/AEA-21 (residual R-W-5, R-W-15) | graph-core §2 `GraphOutcome` gains `closed_every_open_task: bool = False`; graph-core places the Python `TurnPayload` union in `domain/` | AEA-40 never writes `ai_resolved` and records `blocked-on AEA-21` for that row of §9's table only |
| **data (DAT)**, AEA-03 (residual R-W-6) | `TextId.PERSON_REQUEST_LABEL` ("Talk to a person") exists (data.md §2) | AEA-40 records `blocked-on AEA-03` for history entry 4's text |
| **AEA-01** `web/container.py` (residual R-W-8) | the container builder takes `overrides` from its caller and passes it to `register_graph` untouched, as it does `Settings` | AEA-23's lifespan passes it as a keyword; AEA-51 reads it |
