# AEA 7b decisions: web evidence sweep

Scope: the needs-decision items and gap/missing/disagree notes in docs/plans/tickets/AEA-01, 23, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49 (.md). Each item's text is copied verbatim from its ticket file (quoted block). Evidence is searched in docs/ux/03-structure/ (ui-contracts.openapi.yaml, UI_CONTRACTS.md, SCREEN_SPECS.md, IA.md), docs/design/*.md, docs/design/contracts/*.md, docs/prd/*.md, docs/analysis/*.md and docs/research/*.md. Paths are relative to inno-aea-callcenter.

Status key: **sourced** = a passage states the answer; **partial** = passages constrain or name the decision but do not decide it; **no source found** = nothing in the searched set bears on the decision. No decisions are made here.

Counts: 55 needs-decision items and 4 gap/disagree notes (59 entries). No source found: 12 (see the closing list).

## AEA-01 · item 1: per-session and per-IP rate-limit values (R-41)
**Ticket text (AEA-01.md:63):**
> - `needs-decision: per-session and per-IP rate-limit values (R-41).` No source gives a number: system design §8.2 says
>   only "rate limits per session and IP" and PRD §5 "set above 20". `policy/limits.py` declares the names with no value
>   invented; the planner asks the orchestrator before the build.

**Evidence** (partial, no numbers in any source)
- `docs/ux/03-structure/UI_CONTRACTS.md:596`: "Only numbers to tune at build: the timing budgets other than the 12.5 s p95 and the 60 s deadline, the 5 s reset-lock wait and the per-IP throttle."
- `docs/ux/03-structure/UI_CONTRACTS.md:602`: "REQUEST_RATE_LIMITED (429) is new: it exists so every read operation has a documented 4xx and so R-41's per-IP limit has a name distinct from the chat's RATE_LIMITED."
- `docs/design/system-design.md:402`: "**Rate limits per session and IP** (R-41) | `RATE_LIMITED` with the person key"
- Searched "set above 20" and "above 20": no hit in the PRD or elsewhere.

## AEA-01 · item 2: parked src/meridian/ tree before config.py (needs-decision, no source for the keep/delete call)
**Ticket text (AEA-01.md:66):**
> - `needs-decision: what happens to the parked src/meridian/ tree before this ticket writes src/meridian/config.py.` The
>   parked files are uncommitted (`.claude/state/resume.md`: "Innocent decides whether they are kept"); `config.py`
>   collides by name, and AEA-05, AEA-13 and AEA-16 copy-and-adapt from parked files (SP-1 build §4.5). Nothing parked is
>   deleted or overwritten until he answers.

**Evidence** (partial: describes the parked code's role, not whether it is kept)
- `docs/design/code-design.md:157`: "### 2.4 What changes from the parked code (`src/meridian/`, read for shapes only)"
- `docs/design/code-design.md:161`: "| `config.py` | Module-level `SETTINGS`; `now()` reads a DB setting inside config | A typed `Settings` built once by the container."
- Searched "parked", "src/meridian", "config.py": nothing on keeping or deleting the parked files.

## AEA-23 · item 1: per-session, per-IP and login-attempt rate-limit numbers
**Ticket text (AEA-23.md:161):**
> 1. The per-session and per-IP rate-limit numbers and the login-attempt limit per IP. Sources give only "set above 20"
>    (PRD §5) and "per-IP throttle [A]" (UI_CONTRACTS *Still open*).

**Evidence** (partial: no numbers)
- `docs/ux/03-structure/UI_CONTRACTS.md:484`: "Attempts are rate limited per IP."
- `docs/ux/03-structure/UI_CONTRACTS.md:101`: "| LOGIN_RATE_LIMITED | 429 | CON-22 `login` | "Too many attempts. Wait a moment and try again." (`Retry-After`) |"
- `docs/ux/03-structure/UI_CONTRACTS.md:596`: "Only numbers to tune at build: ... the per-IP throttle."

## AEA-23 · item 2: login session lifetime (reason "expired")
**Ticket text (AEA-23.md:163):**
> 2. The login session's lifetime that produces `details.reason: "expired"`.

**Evidence**: no source found for a lifetime value (searched: lifetime, idle, absolute, hours, "session expired"). Passages that use the reason only:
- `docs/ux/03-structure/UI_CONTRACTS.md:99`: "| UNAUTHENTICATED | 401 | **every operation except `login` and `/healthz`** | The page shows the login screen (SCR-12). `details.reason` is `none` or `expired` |"
- `docs/ux/03-structure/SCREEN_SPECS.md:576`: "session expired on any screen (every flow) → stale"
- Not a session value: `docs/ux/03-structure/SCREEN_SPECS.md:105`: "Codes last 10 minutes." (verification codes).

## AEA-23 · item 3: header names for eval key, run_id and eval/load choice
**Ticket text (AEA-23.md:164):**
> 3. The header names carrying the eval key, `run_id` and the eval/load choice (shared with AEA-24; not in the OpenAPI or
>    DO-4).

**Evidence**: no source found (searched: eval key, eval-key, run_id, run-id, X-, header). Nearest passages, neither naming those headers:
- `docs/ux/03-structure/UI_CONTRACTS.md:20`: "`X-Request-ID` on every response."
- `docs/ux/03-structure/UI_CONTRACTS.md:21`: "**one session cookie, `mhc_session`**, set by login (CON-22)."

## AEA-23 · item 4: session-service and require_staff(roles) signatures
**Ticket text (AEA-23.md:166):**
> 4. The session-service and `require_staff(roles)` signatures this issue declares and AEA-44 implements: DO-4 §13–§14 has
>    none. Proposal: this issue's plan writes them into `web/deps.py` and a one-line addition to DO-4 §14.

**Evidence** (partial: placement only, no signatures)
- `docs/design/code-design.md:243`: "staff sessions + require_staff(roles) (CON-10); flags"
- `docs/design/code-design.md:219`: "staff_sessions, flags"
- Searched "require_staff", "SessionService", "session service": no signature in the searched set.

## AEA-23 · item 5: ApiErrorCode (DO-4 §11) lacks UNAUTHENTICATED, LOGIN_FAILED, LOGIN_RATE_LIMITED; still lists STAFF_AUTH_REQUIRED
**Ticket text (AEA-23.md:168):**
> 5. DO-4 §11 `ApiErrorCode` lacks `UNAUTHENTICATED`, `LOGIN_FAILED`, `LOGIN_RATE_LIMITED` and still lists
>    `STAFF_AUTH_REQUIRED`, which the OpenAPI retired; AEA-02 must carry the OpenAPI list.

**Evidence** (sourced)
- `docs/design/contracts/internal-components.md:730`: "    STAFF_AUTH_REQUIRED = "STAFF_AUTH_REQUIRED"       # 401, details.reason: none | session_reset | expired"
- `docs/ux/03-structure/UI_CONTRACTS.md:111`: "Names from the screen specs and DO-4 that were **renamed to the decided list**"
- Grep of internal-components.md found no line for UNAUTHENTICATED, LOGIN_FAILED or LOGIN_RATE_LIMITED.

## AEA-23 · item 6: empty username or password (400 VALIDATION_ERROR vs LOGIN_FAILED)
**Ticket text (AEA-23.md:170):**
> 6. An empty username or password: UI_CONTRACTS CON-22 says 400 `VALIDATION_ERROR`; the OpenAPI `LoginFailed` description
>    says `LOGIN_FAILED` covers "empty".

**Evidence** (sourced for CON-22; the OpenAPI wording was not found)
- `docs/ux/03-structure/UI_CONTRACTS.md:483`: "VALIDATION_ERROR (400) for an empty field."
- `docs/ux/03-structure/UI_CONTRACTS.md:100`: "| LOGIN_FAILED | 401 | CON-22 `login` | One message for every cause: "That username or password didn't work." (never says which) |"
- Searched "empty" in ui-contracts.openapi.yaml: no LoginFailed description with "empty" (hits are unrelated example text).

## AEA-23 · item 7: where request and auth_event records live
**Ticket text (AEA-23.md:172):**
> 7. Where `request` and `auth_event` records live: DO-6 *Storage* lists no table for either, and no DDL owner in the
>    slice plan holds one (log line only, or a table, and whose `.sql`).

**Evidence** (partial: names the records, no table or DDL owner)
- `docs/design/observability-contract.md:256`: "`request` per call; `auth_event` per attempt"
- `docs/design/observability-contract.md:93`: "Demo login and logout (R-48, CON-22)"
- Searched "auth_event", "request record", "Storage": no table or DDL owner in the searched set.

## AEA-40 · item 1: who composes the chat RATE_LIMITED notice
**Ticket text (AEA-40.md:144):**
>   1. Who composes the chat's `RATE_LIMITED` notice (HTTP 200 + a `degraded_handoff` / `rate_limit` turn row, DO-4 §11):
>      AEA-23's middleware, or `TurnService` reading a limiter verdict from `web/deps.py`?

**Evidence** (partial)
- `docs/design/code-design.md:255`: "ReplyComposer: blocks, notices (incl. AI_PAUSED), settled"
- `docs/ux/03-structure/UI_CONTRACTS.md:80`: "| RATE_LIMITED | `notice` | "I can't take more messages in this chat right now." Field disabled; person key stays |"
- `docs/design/observability-contract.md:54`: "`model_error`, `tool_error`, `timeout`, `brake`, `spend_cap`, `rate_limit`"

## AEA-40 · item 2: where the 503 RESET_IN_PROGRESS signal comes from
**Ticket text (AEA-40.md:146):**
>   2. Where the 503 `RESET_IN_PROGRESS` signal comes from: `ResetService` (DO-4 §14) exposes only `reset(now)`.

**Evidence** (partial: the signature shown, not the signal)
- `docs/design/contracts/internal-components.md:984`: "    def reset(self, now: datetime) -> ResetDone: ..."
- `docs/design/code-design.md:355`: "`ResetService(uow, restore_working_copy, clear_checkpoints, seed_demo)`"
- `docs/ux/03-structure/UI_CONTRACTS.md:282`: "**all-or-nothing** under an exclusive lock (turns in flight wait up to 5 s [A])"

## AEA-40 · item 3: how Intake (SecretStr code, form values) reaches the graph; TurnInput has no message_id
**Ticket text (AEA-40.md:147):**
>   3. How `Intake` (with its `SecretStr` code and form values) reaches the graph without entering state (same item as
>      AEA-36's needs-decision 1); and `TurnInput` has no `message_id`, which `ToolCallScope` needs.

**Evidence** (partial)
- `docs/design/contracts/internal-components.md:194`: "# only for kind="code"; never logged, never in state"
- `docs/design/contracts/internal-components.md:315`: "# the customer message that led to this call (lookup log)"
- `docs/design/contracts/internal-components.md:552`: "# must be a customer message of this thread" (class not identified in this sweep)

## AEA-40 · item 4: who appends the CON-21 customer_message event on an AI_PAUSED turn
**Ticket text (AEA-40.md:149):**
>   4. Who appends the CON-21 `customer_message` event on an `AI_PAUSED` turn (DO-4 §11): `TurnService`, in the same
>      transaction as the message row, or AEA-46?

**Evidence** (partial)
- `docs/ux/03-structure/UI_CONTRACTS.md:465`: "Events: `customer_message` (so the representative sees replies arrive)"
- `docs/design/contracts/internal-components.md:752`: "| A representative owns the chat (`controller = human`) | `to_staff` (not a failure) |"
- `docs/design/contracts/api-con-mapping.md:58`: "Writes `conversations.controller` and the message in one transaction; appends the CON-…" (CON-14 staff write, not the AI_PAUSED turn)

## AEA-41 · item 1: first connection without Last-Event-ID (replay from 0 or current last event)
**Ticket text (AEA-41.md:116):**
>   1. First connection without `Last-Event-ID` (a browser `EventSource` sends it only on reconnect): replay from 0, or start
>      at the thread's current last event (CON-1 and `getChatThread` return `last_event_id`)?

**Evidence** (partial: only reconnect is specified)
- `docs/ux/03-structure/UI_CONTRACTS.md:189`: "- Writes: none. Reconnect with the `Last-Event-ID` header: missed events replay in order (N-2)."
- `docs/ux/03-structure/UI_CONTRACTS.md:163`: "Plus `settled`, `writes[]`, `controller`, `notice`, `last_event_id`, `sequence`."
- `docs/design/system-design.md:85`: "Reconnect with the last event ID, replay (N-2)"

## AEA-41 · item 2: demo-wide events (staffing_changed, clock_changed, demo_reset) per thread or merged stream
**Ticket text (AEA-41.md:118):**
>   2. `staffing_changed`, `clock_changed` and `demo_reset` are demo-wide: are they appended to every open thread's stream,
>      or does the route merge a demo-wide stream? `EventId` is per stream (DO-4 §0), so one `Last-Event-ID` cannot address
>      two streams.

**Evidence** (partial)
- `docs/ux/03-structure/UI_CONTRACTS.md:188`: "Open on every chat session, not only a live handoff, so the demo bar and banner update when the reviewer changes staffing or the clock in another tab."
- `docs/ux/03-structure/UI_CONTRACTS.md:191`: "After `chat_closed` or `demo_reset` the server closes the stream."
- `docs/design/system-design.md:707`: "events include `clock_changed`, `staffing_changed`, `case_created`"
- Searched "EventId": no hit in the searched set.

## AEA-41 · item 3: DO-6 names no record for stream_reconnect
**Ticket text (AEA-41.md:88-89, tail of a longer bullet):**
> `needs-decision`:
> DO-6 names no record for `stream_reconnect`.

**Evidence** (partial: the signal is named; no record is named)
- `docs/design/system-design.md:407`: "missed events replayed from the `events` table (N-2) | client-driven | `stream_reconnect`"
- Searched "stream_reconnect" in docs/design/observability-contract.md: no hit.

## AEA-42 · item 1: which component builds the CON-4/CON-5 handoff / live_queued block and settled
**Ticket text (AEA-42.md:145):**
>   - ND-1 — needs-decision: which component builds the CON-4/CON-5 `handoff` / `live_queued` block (with the masked
>     `followup_chooser`) and `settled` outside a graph turn: AEA-21's `ReplyComposer` reached through a `web/deps.py`
>     provider, or `schemas/handoff.py` serialising `HandoffResult` itself? DO-4 is silent; two builders risk the card and
>     the panel disagreeing. Recommended: reuse the composer.

**Evidence** (partial; "DO-4 is silent" not checked against DO-4 itself)
- `docs/ux/03-structure/UI_CONTRACTS.md:203`: "- Reads: `result` (`case_created`, `live_queued`, `already_open`), a `handoff` or `live_queued` block, `settled`."
- `docs/design/contracts/internal-components.md:512`: "    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ..."
- `docs/design/code-design.md:255`: "ReplyComposer: blocks, notices (incl. AI_PAUSED), settled"

## AEA-42 · item 2: who writes the CON-4 turn row (gate_result person_requested, outcome handed_off)
**Ticket text (AEA-42.md:149):**
>   - ND-2 — needs-decision: who writes the CON-4 `turn` row (`gate_result = person_requested`, `outcome = handed_off`)
>     that WF-2 and CAP-3 require and that makes "the same `turn_id` returns the same result" true: this route through
>     `core.turns.begin/finish`, or `HandoffService.open` (AEA-29)? DO-4 §7 and §14 are silent.

**Evidence** (partial: the row is required, its writer is not named)
- `docs/design/observability-contract.md:221`: "A check counts turns with `outcome = handed_off` and no `case` row for that `turn_id`."
- `docs/design/observability-contract.md:249`: "`turn.outcome = handed_off`"
- `docs/ux/03-structure/UI_CONTRACTS.md:207`: "**Idempotent**: a second tap returns `already_open` with the same reference"

## AEA-42 · item 3: unverified customer with destination on_record on CON-5 (400 or 409)
**Ticket text (AEA-42.md:152):**
>   - ND-3 — needs-decision: what does an unverified customer get for `destination: "on_record"` on CON-5 — 400
>     `VALIDATION_ERROR` (field `destination`) or 409 `NOT_ALLOWED_IN_STATE`? The OpenAPI says "general only" but names no
>     code.

**Evidence** (partial; "general only" not found)
- `docs/ux/03-structure/UI_CONTRACTS.md:219`: "- Writes: `channel` (email, phone), `destination` (`on_record` or `general`), `window` (`morning`, `afternoon`, `any`)."
- `docs/ux/03-structure/UI_CONTRACTS.md:221`: "NOT_ALLOWED_IN_STATE (409, no open case)"
- Searched "general only": no hit.

## AEA-42 · item 4: who assembles HandoffRequest for CON-4 (route or AEA-29 service entry)
**Ticket text (AEA-42.md:155):**
>   - ND-4 — needs-decision: CON-4 needs a `HandoffRequest` (priority from `policy/handoff.py` `priority_for`, AEA-14;
>     identity from the thread's `actions(verified)` rows). Does the route assemble it, or does AEA-29 expose a
>     "person requested for (thread_id, turn_id)" entry? Recommended: the service entry, so the route stays thin.

**Evidence** (partial)
- `docs/design/contracts/internal-components.md:488`: "class HandoffRequest(MeridianModel):"
- `docs/design/contracts/internal-components.md:923`: "def open_case(self, tx: UnitOfWork, req: HandoffRequest, promise: Promise, now: datetime) -> HandoffResult: ..."
- `docs/design/code-design.md:310`: "`promise_for(...) -> Promise`, `priority_for(...) -> Priority`"
- Searched "person requested for": no hit.

## AEA-42 · item 5: OpenAPI response validator library and owner of shared test helper
**Ticket text (AEA-42.md:158):**
>   - ND-5 — needs-decision (shared by every route issue): which library validates responses against the OpenAPI in
>     tests, and who owns the shared test helper (`pyproject.toml` is AEA-01's; no `tests/` helper is in the collision map).

**Evidence**: no source found (searched: OpenAPI validator, schemathesis, openapi-core, jsonschema, "contract test", "response validat", "test helper"). Only near hit, not about OpenAPI:
- `docs/design/code-design.md:525`: "the shared promise is the contract test"

## AEA-42 · gap note: promise text and due-label disagreement with PRD R-26 and DO-4 §7 (contract notes)
**Ticket text (AEA-42.md:71-78, match at line 76):**
> - **Contract notes (OpenAPI wins; listed, not edited):** (1) api-con-mapping §1 names `web/routes/chat.py` as CON-4/CON-5's
>   file; the slice plan and DO-3 §8 collision row move them to `web/routes/handoff.py` (this issue). (2) api-con-mapping §0
>   still says cookies `mhc_demo` / `mhc_staff`; the OpenAPI's only cookie is `mhc_session`. (3) The OpenAPI example
>   `promise_text` begins "No representative is online right now." while PRD R-26's table string begins "A representative
>   will get back to you…", and the example `due_label` reads "by Monday, October 19, 7:00 pm" where DO-4 §7 comments
>   "Monday, October 19, 7:00 pm": this route copies whatever `policy/handoff.py` (AEA-14) produces, so the disagreement
>   belongs to AEA-14's owner. (4) DO-4 §0 types `ThreadId` as UUID4, but the OpenAPI path parameter is a plain string
>   (example `thr_9d41`) and documents no 400 for a malformed id on these operations except via the body: an unknown or
>   malformed `thread_id` answers 404 `SESSION_NOT_FOUND`.

**Evidence** (sourced for the promise wording in the design docs)
- `docs/prd/inno-aea-callcenter-prd.md:232`: "Nobody online: "A representative will get back to you within 1 business day"."
- `docs/ux/03-structure/SCREEN_SPECS.md:152`: "No representative is online right now. A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm."
- `docs/design/DESIGN-DIRECTIONS.md:101`: "Line 1 is the exact promise ("A representative will get back to you within 1 business day")."

## AEA-43 · item 1: how a route learns CON-9 holds its exclusive lock (503)
**Ticket text (AEA-43.md:130):**
>   - ND-1 — needs-decision: how does a route learn that CON-9 holds its exclusive lock, so it can answer 503
>     `RESET_IN_PROGRESS` ("most operations during CON-9's lock")? DO-4 names no signal (a `ResetService` flag through
>     `web/deps.py`, the middleware answering for every route, or SQLite's `busy_timeout`). Shared with AEA-44 and AEA-48.

**Evidence** (partial)
- `docs/ux/03-structure/UI_CONTRACTS.md:282`: "**all-or-nothing** under an exclusive lock (turns in flight wait up to 5 s [A]); nothing is half-reset."
- `docs/design/system-design.md:412`: "| **Demo reset (CON-9)** | Takes an exclusive lock; turns in flight wait up to 5 s [A] |"
- `docs/design/code-design.md:334`: "WAL, `busy_timeout` 5 s [A]"

## AEA-43 · item 2: who formats the demo-clock label and date_label
**Ticket text (AEA-43.md:133):**
>   - ND-2 — needs-decision: who formats the demo-clock `label` ("Fri Oct 16, 2026 · 2:20 pm") and `date_label`
>     ("… (demo date)") that CON-1 (AEA-40), CON-8 read (here), CON-8 advance (AEA-47) and CON-3 `clock_changed` all send?
>     Recommended: `DemoService` (AEA-30) returns them, so one formatter exists.

**Evidence** (partial)
- `docs/ux/03-structure/UI_CONTRACTS.md:119`: "demo clock (`now`, `label`, `date_label`)"
- `docs/ux/03-structure/UI_CONTRACTS.md:263`: "- Reads: `now`, `label`, `date_label`. `advanceDemoClock` adds `became_overdue` (how many cases turned overdue)."
- `docs/ux/03-structure/UI_CONTRACTS.md:265`: "Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue."

## AEA-43 · item 3: ResetDone shape and who asked
**Ticket text (AEA-43.md:136):**
>   - ND-3 — needs-decision: DO-4 §14 gives `ResetService.reset(now) -> ResetDone` with no fields and no caller, but the
>     response needs `open_chats_ended`, `roles_reset` and `clock`, and DO-6's `reset_event` records "who asked". What is
>     `ResetDone`'s shape, and how does the route pass who asked? (Roles live in AEA-44's `staff_sessions`.)

**Evidence** (partial)
- `docs/design/contracts/internal-components.md:984`: "    def reset(self, now: datetime) -> ResetDone: ..."
- `docs/ux/03-structure/UI_CONTRACTS.md:278`: "- Reads: `ok`, `open_chats_ended`, `staff_sessions_invalidated`, `clock` (back to Fri 2026-10-16)."
- `docs/design/observability-contract.md:90`: "reset_event (what was restored, who asked, open chats ended)"

## AEA-43 · item 4: per-IP reset throttle and its documented response
**Ticket text (AEA-43.md:139):**
>   - ND-4 — needs-decision: does a per-IP reset throttle exist ([A] in UI_CONTRACTS CON-9), and if so which documented
>     response does it use? `resetDemo` documents no 429.

**Evidence** (partial: throttle named as [A]; no response code)
- `docs/ux/03-structure/UI_CONTRACTS.md:285`: "A per-IP throttle stays as a safety net [A]."
- `docs/ux/03-structure/UI_CONTRACTS.md:592`: "A per-IP throttle stays as a safety net [A]."
- `docs/ux/03-structure/UI_CONTRACTS.md:92`: "read operations without a 4xx of their own" (REQUEST_RATE_LIMITED is listed for reads, not for reset)

## AEA-43 · item 5: OpenAPI response validator and shared test helper owner
**Ticket text (AEA-43.md:141):**
>   - ND-5 — needs-decision (shared by every route issue): the OpenAPI response validator and the owner of a shared test
>     helper.

**Evidence**: no source found (same search as AEA-42 item 5).

## AEA-43 · gap note: AEA-52 blockers omit AEA-43 (slice-plan edge)
**Ticket text (AEA-43.md:143-144):**
> - **Slice-plan note:** AEA-52 "proves real services behind CON-7…17, 21", which includes this issue's CON-7 and CON-9, but
>   AEA-52's blockers omit AEA-43 (only AEA-51 lists it). Waves are unaffected; the edge is missing.

**Evidence**: no source found (the slice plan is outside the searched set; searched "AEA-52", "AEA-43").

## AEA-44 · item 1: demo reset keeps login sessions and sets roles to customer (role_reset); flags and review list
**Ticket text (AEA-44.md:140):**
>   - ND-1 — needs-decision: the demo reset must keep login sessions but set every role back to customer with a
>     `role_reset` marker (CON-9), and SCR-8 says a reset empties the review list; yet DO-4 §14's
>     `ResetService(uow, restore_working_copy, clear_checkpoints, seed_demo)` has no staff step. Does AEA-31 call a
>     `repos_staff` method this issue provides (inside its exclusive transaction), and is `flags` cleared by it?

**Evidence** (partial: reset behaviour is specified; no staff step in ResetService is named)
- `docs/ux/03-structure/UI_CONTRACTS.md:547`: "reset keeps the login and sets the role to customer"
- `docs/ux/03-structure/UI_CONTRACTS.md:502`: "stale: ROLE_NOT_ALLOWED `role_reset`, getSession."
- `docs/ux/03-structure/SCREEN_SPECS.md:265`: "a reset ends open chats, keeps the login and sets the role back to c…"
- Searched "review list" and "flags" against reset: no line ties them.

## AEA-44 · item 2: login-session lifetime
**Ticket text (AEA-44.md:144):**
>   - ND-2 — needs-decision: the login-session lifetime. `UNAUTHENTICATED` has `details.reason: "expired"`, but no source
>     gives a duration or says whether it is idle or absolute.

**Evidence**: no source found for a duration or idle/absolute rule. Same passages as AEA-23 item 2 (`docs/ux/03-structure/UI_CONTRACTS.md:99`).

## AEA-44 · item 3: how a route learns CON-9 holds its lock (switchRole 503)
**Ticket text (AEA-44.md:146):**
>   - ND-3 — needs-decision (shared with AEA-43 ND-1): how a route learns CON-9 holds its lock, for `switchRole`'s 503.

**Evidence** (partial)
- `docs/ux/03-structure/UI_CONTRACTS.md:296`: "RESET_IN_PROGRESS (503)."
- `docs/ux/03-structure/UI_CONTRACTS.md:282`: "**all-or-nothing** under an exclusive lock (turns in flight wait up to 5 s [A])"

## AEA-44 · item 4: what identifies "you" in StaffActor (role or login session)
**Ticket text (AEA-44.md:147):**
>   - ND-4 — needs-decision (shared with AEA-45, AEA-46): what identifies "you" in `StaffActor` for claims and
>     `NOT_CLAIMED_BY_YOU`: the role (owners shown as "Riley", "Demo supervisor"; `assignee` enum `riley | supervisor`) or
>     the login session acting as that role? Two reviewers both acting as Riley share claims under the first.
>     Recommended: the role, matching every example.

**Evidence** (partial)
- `docs/ux/03-structure/UI_CONTRACTS.md:21`: "It identifies the login session (which owns that session's chat threads and scopes the demo inbox)"
- `docs/ux/03-structure/IA.md:109`: "**Current-role line** on staff screens: "Riley · demo representative", "Demo supervisor", "Demo business owner" (CON-10)"
- `docs/ux/03-structure/UI_CONTRACTS.md:340`: "Claimed · Riley (demo)"

## AEA-44 · item 5: OpenAPI response validator and shared test helper owner
**Ticket text (AEA-44.md:151):**
>   - ND-5 — needs-decision (shared): the OpenAPI response validator and the owner of a shared test helper.

**Evidence**: no source found (same search as AEA-42 item 5).

## AEA-45 · item 1: StaffActor identity (role or login session)
**Ticket text (AEA-45.md:142):**
>   - ND-1 — needs-decision (shared with AEA-44 ND-4, AEA-46): what identifies "you" in `StaffActor`: the role or the login
>     session acting as it.

**Evidence** (partial; same passages as AEA-44 item 4)
- `docs/ux/03-structure/UI_CONTRACTS.md:21`: "It identifies the login session"
- `docs/ux/03-structure/IA.md:109`: "**Current-role line** on staff screens"

## AEA-45 · item 2: CaseService signature types (StaffRole, StaffActor, CaseAction, QueueView, etc.) defined where
**Ticket text (AEA-45.md:144):**
>   - ND-2 — needs-decision: DO-4 §13's `CaseService` signatures use `StaffRole`, `StaffActor`, `CaseAction`, `ActivityIn`,
>     `QueueView`, `CaseDetail`, `OversightView` and `CaseActionRejected`, none of which DO-4 defines. Which issue defines
>     them (AEA-02's frozen `domain/`, or AEA-29)? Until one does, the planner records `blocked-on` that issue.

**Evidence** (partial: types are used, none defined in the searched set)
- `docs/design/contracts/internal-components.md:930`: "def apply(self, case_ref: CaseRef, action: CaseAction, actor: StaffActor,"
- `docs/design/code-design.md:351`: "concrete `CaseService` (§13)"
- Searched "class StaffActor", "StaffRole", "QueueView", "CaseActionRejected": no definition found.

## AEA-45 · item 3: result_line wording for each action and its owner
**Ticket text (AEA-45.md:147):**
>   - ND-3 — needs-decision: `result_line` wording. Only "Claimed · Riley (demo)" is given (OpenAPI `CLAIMED`, SCR-5/SCR-6
>     success). Where do the lines for wait, resolve, release, start, close_unresolved, assign and change_priority come
>     from, and who owns them (`policy/texts.py`, AEA-29, or this schema)?

**Evidence** (partial: two lines given, others not)
- `docs/ux/03-structure/ui-contracts.openapi.yaml:5519`: "result_line: Claimed · Riley (demo)"
- `docs/ux/03-structure/ui-contracts.openapi.yaml:5543`: "result_line: Waiting until Mon Oct 19 · 9:00 am"
- `docs/ux/03-structure/UI_CONTRACTS.md:340`: "States the UI must be able to show: "Claimed · Riley (demo)" · waiting with a wake-up time"

## AEA-45 · item 4: flag service signatures
**Ticket text (AEA-45.md:150):**
>   - ND-4 — needs-decision: the flag service's signatures (DO-3 §4.4 names `flag`, `review`, `list_flags` only); this issue
>     builds against AEA-44's AC-10 behaviour.

**Evidence** (partial: names only)
- `docs/design/code-design.md:358`: "`sign_in`, `current`, `sign_out`, `flag`, `review`, `list_f…"
- `docs/ux/03-structure/UI_CONTRACTS.md:384`: "- Writes: `createFlag` `{case_ref, target, message_id?, reason?, note?}`"

## AEA-45 · item 5: OpenAPI response validator and shared test helper owner
**Ticket text (AEA-45.md:152):**
>   - ND-5 — needs-decision (shared): the OpenAPI response validator and the owner of a shared test helper.

**Evidence**: no source found (same search as AEA-42 item 5).

## AEA-46 · item 1: StaffActor identity for "claimed by you" (role or login session)
**Ticket text (AEA-46.md:132):**
>   - ND-1 — needs-decision (shared with AEA-44 ND-4, AEA-45 ND-1): what identifies "you" in `StaffActor` for "claimed by
>     you": the role or the login session.

**Evidence** (partial; same as AEA-44 item 4)
- `docs/ux/03-structure/IA.md:109`: "**Current-role line** on staff screens"
- `docs/ux/03-structure/UI_CONTRACTS.md:21`: "It identifies the login session"

## AEA-46 · item 2: NOT_CLAIMED_BY_YOU (403) vs CASE_ALREADY_CLAIMED (409) for CON-14
**Ticket text (AEA-46.md:134):**
>   - ND-2 — needs-decision: CON-14 has two codes for a case someone else claimed: 403 `NOT_CLAIMED_BY_YOU` (example
>     `details.owner` "Demo supervisor") and 409 `CASE_ALREADY_CLAIMED` (example `details.claimed_by` "Demo supervisor").
>     Which applies to which action, and which does an unclaimed case get? Recommended: `join` on a case another actor
>     claimed → `CASE_ALREADY_CLAIMED`; `send` / `hand_back` / `close` by a non-owner, or `join` on an unclaimed case →
>     `NOT_CLAIMED_BY_YOU`.

**Evidence** (partial: both codes listed, no which-applies rule)
- `docs/ux/03-structure/UI_CONTRACTS.md:356`: "NOT_LIVE (409); NOT_CLAIMED_BY_YOU (403); CASE_ALREADY_CLAIMED (409)"
- `docs/ux/03-structure/UI_CONTRACTS.md:361`: "errors NOT_LIVE, CASE_ALREADY_CLAIMED, NOT_CLAIMED_BY_YOU, CASE_NOT_FOUND, UNAUTHENTICATED, VALIDATION_ERROR"

## AEA-46 · item 3: send with null or empty text (400 VALIDATION_ERROR) and staff text length cap
**Ticket text (AEA-46.md:139):**
>   - ND-3 — needs-decision: `send` with `text` null or empty — 400 `VALIDATION_ERROR` field `text`? And is there a length
>     cap for staff text (the customer's is 2,000 characters)? `LiveActionRequest.text` is nullable with no limit.

**Evidence** (partial: customer limit only)
- `docs/ux/03-structure/UI_CONTRACTS.md:167`: "`text` (1–2,000 characters)" (customer CON-2 payload)
- Searched "2,000", "maxLength", "staff text": no staff-side limit found.

## AEA-46 · item 4: whether CON-21 shares CON-3's CapacityLimiter(4)
**Ticket text (AEA-46.md:141):**
>   - ND-4 — needs-decision: does CON-21 share CON-3's `CapacityLimiter(4)` (AEA-41) so all streams together hold at most
>     four threads, as DO-3 §2.3 rule 4 intends, or have its own? If shared, who owns the limiter (a `web/deps.py`
>     provider, AEA-23)?

**Evidence** (partial)
- `docs/design/code-design.md:149`: "**Event-stream polling reads run on their own `anyio` `CapacityLimiter(4)`** [A], so many open streams cannot take"
- `docs/design/contracts/internal-components.md:885`: "on a CapacityLimiter(4), and a reconnect replays from Last-Event-ID."
- Searched "CON-21" against limiter terms: no sharing rule found.

## AEA-46 · item 5: where live state (not_live, queued, joined, handed_back, closed, since) is stored
**Ticket text (AEA-46.md:144):**
>   - ND-5 — needs-decision: where the live state (`not_live`, `queued`, `joined`, `handed_back`, `closed`, with `since`)
>     is stored; DO-4 names only `conversations.controller`. If no column exists in AEA-10's tables, `blocked-on AEA-10`.

**Evidence** (partial: controller column is named; live-state column is not)
- `docs/ux/03-structure/UI_CONTRACTS.md:353`: "the new controller, live state (not_live, queued, joined, handed_back, closed)"
- `docs/design/code-design.md:357`: "UoW (`conversations.controller`, `messages`, `events`)"
- `docs/design/contracts/api-con-mapping.md:58`: "Writes `conversations.controller` and the message in one transaction"

## AEA-46 · item 6: OpenAPI response validator and shared test helper owner
**Ticket text (AEA-46.md:146):**
>   - ND-6 — needs-decision (shared): the OpenAPI response validator and the owner of a shared test helper.

**Evidence**: no source found (same search as AEA-42 item 5).

## AEA-47 · item 1: how a route learns CON-9 holds its lock (503)
**Ticket text (AEA-47.md:107):**
>   - ND-1 — needs-decision (shared with AEA-43 ND-1): how a route learns CON-9 holds its lock, for the 503.

**Evidence** (partial; same as AEA-43 item 1)
- `docs/ux/03-structure/UI_CONTRACTS.md:282`: "**all-or-nothing** under an exclusive lock (turns in flight wait up to 5 s [A]); nothing is half-reset."

## AEA-47 · item 2: who formats the demo-clock label
**Ticket text (AEA-47.md:108):**
>   - ND-2 — needs-decision (shared with AEA-43 ND-2): who formats the demo-clock `label` ("Mon Oct 19, 2026 · 7:00 am")
>     that CON-1, CON-8 read, CON-8 advance and `clock_changed` all send. Recommended: `DemoService`.

**Evidence** (partial; same as AEA-43 item 2)
- `docs/ux/03-structure/UI_CONTRACTS.md:265`: "Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue."
- `docs/ux/03-structure/UI_CONTRACTS.md:263`: "`advanceDemoClock` adds `became_overdue` (how many cases turned overdue)."

## AEA-47 · item 3: DemoService.advance_clock signature and result
**Ticket text (AEA-47.md:110):**
>   - ND-3 — needs-decision: the `DemoService.advance_clock` signature and result (DO-4 has none); this issue builds against
>     "step in; new demo time and the count of cases that became overdue out", the minimum `ClockAdvanceResponse` needs.

**Evidence** (partial: method named, no signature)
- `docs/design/code-design.md:353`: "`DemoService.staffing/set_staffing/advance_clock`"
- `docs/ux/03-structure/UI_CONTRACTS.md:263`: "`advanceDemoClock` adds `became_overdue` (how many cases turned overdue)."

## AEA-47 · item 4: OpenAPI response validator and shared test helper owner
**Ticket text (AEA-47.md:112):**
>   - ND-4 — needs-decision (shared): the OpenAPI response validator and the owner of a shared test helper.

**Evidence**: no source found (same search as AEA-42 item 5).

## AEA-48 · gap note: example measure ids disagree with registries (contract notes)
**Ticket text (AEA-48.md:66-68, match at line 66):**
> - **Contract notes (OpenAPI wins on fields; listed, not edited):** (1) The examples' `id` values disagree with the
>   registries: CON-18 `SEEDED` labels "Promises kept on time" M-9 and "Handoffs" M-5 (DO-7: M-13 is promises kept on time,
>   M-9 booking validity, M-5 containment); CON-19 `TOO_FEW_TURNS` labels latency M-25/M-26 and turns M-23 (DO-7: M-23 is
>   latency, M-25 cost per conversation, M-26 daily spend); CON-20 `STALE_RUN` labels "Retrieval hit rate (top 3)" E-6
>   (DO-5: E-2 is retrieval, E-6 the handoff slice). The `Measure.id` description says "M-n from the metrics registry", so
>   DO-7 decides which id names what; the values are AEA-53's. (2) SCREEN_SPECS SCR-10 R1 reads "Updated [time] (demo
>   time)"; the OpenAPI `as_of` and api-con-mapping §4 settle it as real time. (3) DO-7 M-26 still proposes a UTC spend day;
>   the OpenAPI `spend.day` is "America/Chicago midnight to midnight" (DO-3 §10 C-12). (4) DO-3 §8 and api-con-mapping put
>   these routes in wave 3 with the reader; the slice plan builds the routes in wave 2 against the injected reader.

**Evidence** (sourced for the registry; the example ids were checked only partly)
- `docs/design/key-metrics-registry.md:65`: "| M-13 | Promises kept on time (V3, lagging) | outcome |"
- `docs/design/key-metrics-registry.md:47`: "M-25 cost per conversation"
- `docs/ux/03-structure/ui-contracts.openapi.yaml:6773`: "id: M-9" (CON-18 SEEDED region, line 6753 onward)
- `docs/ux/03-structure/ui-contracts.openapi.yaml:6978`: "- id: M-25" (CON-19 example; which example it sits in was not resolved)

## AEA-48 · item 1: metrics reader signature, return types, and who stamps as_of
**Ticket text (AEA-48.md:127):**
>   - ND-1 — needs-decision: the metrics reader's signature and return types. DO-4 has none; DO-3 names `owner_metrics`,
>     `monitoring`, `latest_eval`; a service may not import `web/schemas` (DO-3 §2.1). Do the return types live in
>     `domain/` (AEA-02 is frozen, so a small follow-up), or does the reader return plain data that `schemas/reads.py`
>     validates? And who stamps CON-19's real-time `as_of`, the reader or the route?

**Evidence** (partial: reads named, no signature)
- `docs/ux/03-structure/UI_CONTRACTS.md:413`: "Reads: per measure `id` (M-n), label, numerator, denominator, unit, value, `null_reason`, `kind` (measured or estimate), `case_refs`; `as_of`"
- `docs/ux/03-structure/UI_CONTRACTS.md:428`: "`as_of` (wall-clock time; the "Updated" line shows it) and `demo_now` (business date only)"
- `docs/design/code-design.md:601`: "`services/metrics_reader.py`, `web/routes/reads.py` (CON-18…CON-20)"
- Searched "owner_metrics", "latest_eval", "monitoring": no signature.

## AEA-48 · item 2: how a route learns CON-9 holds its lock (503)
**Ticket text (AEA-48.md:131):**
>   - ND-2 — needs-decision (shared with AEA-43 ND-1): how a route learns CON-9 holds its lock, for the 503.

**Evidence** (partial; same as AEA-43 item 1)
- `docs/ux/03-structure/UI_CONTRACTS.md:282`: "**all-or-nothing** under an exclusive lock (turns in flight wait up to 5 s [A])"

## AEA-48 · item 3: Measure.id values follow DO-7 (AEA-53 and UI agree)
**Ticket text (AEA-48.md:132):**
>   - ND-3 — needs-decision: confirm that the `Measure.id` values follow DO-7 (contract note 1), so AEA-53 and the UI agree
>     on which id names which measure.

**Evidence** (partial: registry rows; not checked against the example ids)
- `docs/design/key-metrics-registry.md:43`: "M-13 promises kept on time"
- `docs/design/key-metrics-registry.md:57`: "| M-5 | Containment (the brief's metric) | outcome |"
- `docs/ux/03-structure/UI_CONTRACTS.md:413`: "per measure `id` (M-n)"

## AEA-48 · item 4: OpenAPI response validator and shared test helper owner
**Ticket text (AEA-48.md:134):**
>   - ND-4 — needs-decision (shared): the OpenAPI response validator and the owner of a shared test helper.

**Evidence**: no source found (same search as AEA-42 item 5).

## AEA-49 · item 1: which static paths answer without a session (/login and built assets)
**Ticket text (AEA-49.md:111):**
>   - ND-1 — needs-decision: which static paths answer without a session? SCR-12 makes `/login` public, but the page needs
>     its built script and style files; R-48 read literally gates them. Recommended: `/login` plus the hashed asset files
>     under the build's asset folder are public (they hold no data; every datum comes from gated `/api`), everything else
>     gated. This touches R-48's wording, so it is Innocent's call.

**Evidence** (partial: /login public and R-48 gate; no asset rule)
- `docs/ux/03-structure/SCREEN_SPECS.md:552`: "The only route, with `/healthz`, that answers without a session."
- `docs/ux/03-structure/UI_CONTRACTS.md:39`: "Every route except `login` (CON-22) and `/healthz`"
- `docs/design/code-design.md:277`: "NOT PLANNED: screens are the React app apps/web/ (built 2026-10-21, UX-4 gate unsigned);"

## AEA-49 · item 2: unsigned browser navigation to a gated page (JSON 401 or redirect to /login)
**Ticket text (AEA-49.md:115):**
>   - ND-2 — needs-decision: what does an unsigned browser navigation to a gated page (e.g. `/staff/queue`) get: the JSON
>     401 `UNAUTHENTICATED` that every API route returns, or a redirect to `/login`? SCREEN_SPECS SCR-12 says such routes
>     answer `UNAUTHENTICATED` "and send the visitor here", which a JSON 401 cannot do for a page load.

**Evidence** (partial: SCR-12 says both things)
- `docs/ux/03-structure/SCREEN_SPECS.md:552`: "Every other route answers `UNAUTHENTICATED` and sends the visitor here."
- `docs/ux/03-structure/UI_CONTRACTS.md:503`: "UNAUTHENTICATED sends any page here"
- `docs/ux/03-structure/SCREEN_SPECS.md:619`: "redirect to the page asked for, else the chat" (SCR-12 after sign-in)

## AEA-49 · item 3: file owning the mount and fallback (web/routes/pages.py or other)
**Ticket text (AEA-49.md:118):**
>   - ND-3 — needs-decision: which file owns the mount and fallback. The slice plan names none, AEA-01's `register_…()` stub
>     list in the collision map omits AEA-49, and `web/app.py` "never changes after 23". Recommended: a new
>     `web/routes/pages.py` with its own container hunk, added to the collision map.

**Evidence** (partial)
- `docs/design/code-design.md:278`: "AEA-49 serves its dist/ with fallback to index.html (planned)"
- `docs/design/code-design.md:267`: "composition root; one register_<area>() stub per area"
- `docs/design/code-design.md:170`: "`web/app.py` | `async def api_chat`; password staff login"
- Searched "pages.py" and "web/app.py never changes": no hit.

## AEA-49 · item 4: page-path behaviour when no build is present (404, notice, or refuse in deploy)
**Ticket text (AEA-49.md:121):**
>   - ND-4 — needs-decision: page-path behaviour when no build is present (local backend runs, CI): 404, a plain notice, or
>     refuse to start in deploy only?

**Evidence**: no source found for no-build behaviour (searched: dist, 404, "no build"). Only the dist fallback at `docs/design/code-design.md:278` (see item 3).

## AEA-49 · item 5: register page serving as a DO-6 workflow or record it as outside the registry
**Ticket text (AEA-49.md:123):**
>   - ND-5 — needs-decision: register page serving as a DO-6 workflow, or record it as outside the registry with a reason
>     (as WF-3 does for a read that decides nothing)? DO-6 *Registering a new workflow* expects one or the other.

**Evidence** (partial: the registry section exists; the rule is not quoted)
- `docs/design/observability-contract.md:261`: "## Registering a new workflow"
- Searched "outside the registry", "page serving": no hit.

## AEA-49 · gap note: deployed image may carry no UI (AEA-50 Dockerfile does not copy dist; slice-plan note)
**Ticket text (AEA-49.md:125-127):**
> - **Slice-plan note:** AEA-50 (Dockerfile, wave 3) is not blocked by this issue and its row does not mention building or
>   copying `apps/web/dist` into the image, so the deployed image may carry no UI. AEA-56's deploy depends on AEA-50 and
>   AEA-55, so the gap shows only at deploy.

**Evidence** (partial)
- `docs/design/code-design.md:566`: "| R-40 | Railway | `Dockerfile`, `railway.json`, `config.py` |"
- `docs/design/code-design.md:277`: "screens are the React app apps/web/ (built 2026-10-21, UX-4 gate unsigned)"
- Searched "dist": only `docs/design/code-design.md:278`. No Dockerfile copy rule found.

## Closing list: items with no source found
- AEA-23 item 2 (login session lifetime); AEA-44 item 2 (same)
- AEA-23 item 3 (eval-key header names)
- AEA-42 item 5, AEA-43 item 5, AEA-44 item 5, AEA-45 item 5, AEA-46 item 6, AEA-47 item 4, AEA-48 item 4 (OpenAPI validator and test-helper owner, 7 items)
- AEA-43 gap note (AEA-52 blocker edge)
- AEA-49 item 4 (no-build behaviour: no source found)
