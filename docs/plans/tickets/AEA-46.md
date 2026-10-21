## [AEA-46] staff API: live takeover and case stream (CON-14, CON-21)

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

> **US-20:** "As a **representative** on a simulated shift, I need to claim a live-queued case, reply in the customer's
> chat while the assistant is paused, and hand back or close explicitly, so that the customer has one conversation, not
> two."
> **US-15:** "As a **homeowner** during staffed hours (simulated in the demo), I need to wait in the same chat and see
> clearly when a person has joined and the assistant has stopped, so that I know who I'm talking to."

**1. `services/live_chat.py`: `LiveChatService`** exactly as staff.md §5 signs it:
`LiveChatService(uow: UnitOfWorkFactory, demo_clock: Clock, redact_store: Callable[[str], str])` with `join`, `send`,
`hand_back` and `close`, each taking `(case_ref, …, actor: StaffActor)` and returning `LiveView | LiveRefused`.
`StoredChatLine`, `LiveView` and `LiveRefused` are defined in this file (staff.md §5). Each method is **one write
transaction**: it reads the case's `(thread_id, owner_role, owner_since, lifecycle)` through AEA-10's
`core.cases_ro.owner(case_ref)` and the conversation's `live_state` and `controller` inside the transaction, runs the
checks below in order, then writes the controller, `live_state` / `live_since`, any message (text through
`redact_store`, the STORE profile, via `core.messages.append`), the thread-stream and case-stream events
(`core.events.append`) and one `case_event` with the actor role (`cases.case_events.append`, cases.md §1.2). A refusal
writes nothing. SQLite serialises two staff joining at once, so the second reads the first's result.

**Checks, in order** (staff.md §5, STF-11; the route has already run `require_staff(REPRESENTATIVE)` and request
validation):

| # | Condition | Result |
|---|---|---|
| 1 | no such case | `CASE_NOT_FOUND` {reference} (404) |
| 2 | `join`, case has no owner | `NOT_CLAIMED_BY_YOU` {owner: null} (403) |
| 3 | `join`, owner role ≠ actor role | `CASE_ALREADY_CLAIMED` {claimed_by, claimed_at} (409) |
| 4 | `send` / `hand_back` / `close`, owner role ≠ actor role or no owner | `NOT_CLAIMED_BY_YOU` {owner: name or null} (403) |
| 5 | conversation ended by a demo reset | `NOT_LIVE` {reason: `demo_reset`} (409): defensive only, unreachable after cases.md §1.3; no test asserts it (MC-25) |
| 6 | `join` and live state already `joined` | 200, current view, nothing written |
| 7 | `join` and live state ≠ `queued` | `NOT_LIVE` {reason: `not_waiting`} (409) |
| 8 | `send` / `hand_back` / `close` and live state ≠ `joined` | the same action on its own end state (`hand_back` on `handed_back`, `close` on `closed`) → 200, nothing written; otherwise `NOT_LIVE` {reason: `not_joined` or `chat_closed`} |

**Writes per action** (staff.md §5): join → controller human ("Riley", case_ref), live `joined` since now;
`representative_joined` + `ai_paused` on the thread stream, `controller_changed` (human, "Riley") on `case:<ref>`.
send → a `representative` message in the **same thread** as the customer's; `staff_message` on the thread stream.
hand_back → controller ai, live `handed_back`; `ai_resumed`; `controller_changed` (ai, null). close → controller ai,
live `closed` and the rest of staff.md §5's close row; `chat_closed` on the thread stream, `chat_closed`
{reason `closed_by_staff`} on the case stream. Invariant: `controller = human` exactly when live state is `joined`.
Event `line` sentences come from `policy/texts.py`'s `live` group with placeholder `rep_name` (DAT-29). Names come from
`STAFF_PERSONAS` (staff.md §1); no table stores a display name.

**2. `web/routes/staff_live.py` + `web/schemas/staff_live.py`.**
- `liveChatAction` (CON-14, `POST /api/staff/cases/{reference}/live`, a `def` route): `require_staff(REPRESENTATIVE)`;
  `LiveActionRequest.text` rules (STF-12, staff.md §6): for `send` required, stripped, 1–2,000 characters (null or blank
  → 400 `VALIDATION_ERROR` field `text`, constraint "required for send"; longer → "at most 2000 characters"); a non-null
  `text` on any other action → 400 field `text`, constraint "only for send"; never echoed. One `LiveChatService` call
  through `get_live_chat()` (web.md §4); `LiveView` serialises to `LiveActionResponse`, `LiveRefused` to its status.
- `streamCaseEvents` (CON-21, `GET /api/staff/cases/{reference}/events`, an `async def` SSE endpoint, its own generator,
  no shared helper with CON-3, DO-3 S-11), per staff.md §7 (STF-23, MC-8):
  `require_staff(REPRESENTATIVE, SUPERVISOR, OWNER)`; unknown case → 404 before the stream starts. Start = the
  `Last-Event-ID` header if sent, otherwise the id of the newest `demo_reset` row in `case:<ref>` read with AEA-10's
  `core.events.latest_of` (0 if none), so a view opened after a reset replays only post-reset events. Every 1 s [A] it
  reads `core.events.after(case:<ref>, last)` under `get_stream_poll_limiter()` (the one `CapacityLimiter(4)` shared
  with CON-3, STF-13, WEB-19) and skips the read while `ResetGate.held()`. Frames are `id: <event_id>`,
  `event: <type>`, `data: <CaseEvent JSON>`, with a `: heartbeat` comment after 15 s idle. The poll (1 s [A]) and
  heartbeat (15 s) values are web.md §11's; they are this file's own constants, because importing them from
  `routes/events.py` (AEA-41, same wave) would create an edge the slice plan does not have. A reconnect
  (`Last-Event-ID` > 0) writes web.md §10's `stream_reconnect` record with `case_ref`. The stream closes after sending
  `demo_reset`, and stays open after `chat_closed`.

**Who appends what to `case:<ref>`** (staff.md §7): `controller_changed` and staff `chat_closed` come from this
issue's service. `customer_message` comes from `TurnService` (AEA-40) while `controller = human`. Shift-end
`chat_closed` and `case_changed` come from `CaseService` (AEA-29). `demo_reset` comes from the reset (AEA-31).

**Example pair (tied to WP-2: Omar Patel, MHC-10002, invoice INV-204411).** Simulated staff are on shift; Omar asked for a
person about the after-hours charge and is live-queued on MHC-C-0007, which Riley has claimed. Acting as the
representative: `POST /api/staff/cases/MHC-C-0007/live` `{"action": "join"}` → 200 (OpenAPI `JOINED`): `controller`
`{kind: "human", display_name: "Riley"}`, `live.state` "joined", `message: null`; Omar's chat stream receives
`representative_joined` and `ai_paused`. Then `{"action": "send", "text": "Hi Omar, I can look at the after-hours charge
with you."}` → 200 (`SENT`) with the stored `message` (speaker `representative`, "Riley"). Omar answers "Thanks, that
helps."; the open `GET /api/staff/cases/MHC-C-0007/events` receives `event: customer_message` with that text, and after
`{"action": "close"}`, `event: chat_closed` with `reason: "closed_by_staff"` (example `FRAMES`). Had the supervisor
claimed MHC-C-0007, the join answers 409 `CASE_ALREADY_CLAIMED` with `claimed_by: "Demo supervisor"`; had nobody
claimed it, 403 `NOT_CLAIMED_BY_YOU` with `owner: null` ("Claim the case first.").

**Produced for other issues:** CON-14, CON-21 and `LiveChatService` for AEA-51 (the relayed `to_staff` turn proof needs a
representative in control; cases.md §10, CAS-28), AEA-52 (CAP-4: claim, live reply, hand back) and AEA-55. AEA-40's turn
path reads `conversations.controller` to compose `AI_PAUSED`, relay customer messages and append `customer_message`.

### Source

- PRD R-30, R-31, R-33, R-36, R-48; US-15, US-20; WP-2.
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml`: `liveChatAction`, `streamCaseEvents`; schemas
  `LiveActionRequest`, `LiveActionResponse`, `LiveState`, `ChatLine`, `CaseEvent` (`CeCustomerMessage`,
  `CeControllerChanged`, `CeChatClosed`, `CeDemoReset`, `CeCaseChanged`), `ApiError`; responses `Unauthenticated`,
  `RoleNotAllowed`, `CaseNotFound`, `ValidationError`; `x-roles` of both operations.
- `UI_CONTRACTS.md` CON-14, CON-21, CON-3 (frame format, replay, 15 s heartbeat), *Access*, *Why CON-21 exists*.
- `docs/design/contracts/stage7/staff.md` §1 (`StaffActor`, `STAFF_PERSONAS`), §5 (`LiveChatService`, checks, writes),
  §6 (`LiveActionRequest.text`), §7 (CON-21 stream contract), §10 (demo-clock times), §11 (during a reset);
  `stage7/web.md` §3 (`require_staff`), §4 (`get_live_chat`, `get_stream_poll_limiter`, `get_uow_factory`), §7
  (`ResetGate`), §10 (`request`, `stream_reconnect`), §11 (poll and heartbeat values), §13
  (`assert_response_matches`, `assert_sse_frames_match`); `stage7/cases.md` §1.1 (`conversations.live_state`,
  `live_since`; `events` AUTOINCREMENT), §1.2 (`core.cases_ro.owner`, `core.messages.append`, `core.events.latest_of`,
  `cases.case_events.append`), §1.3 (what a reset clears), §1.5 (`temp_sqlite()`); `stage7/data.md` §1 (STORE profile,
  `redact_store` binding). Decisions: `docs/plans/7b-decisions/staff.md` STF-1, STF-7, STF-8, STF-11, STF-12, STF-13,
  STF-14, STF-23, STF-26; merge MC-7, MC-8, MC-23, MC-25; cases CAS-28; data DAT-29.
- DO-4 §11 (`AI_PAUSED` row), §13 (events polling note; `UnitOfWork`); DO-3 §2.1 (sync routes except streams), §2.3
  rules 1 and 4, §6 S-11, §10 C-7; system design §8.2 *Event stream*, §10 *Staff console*.
- DO-6 WF-4, CAP-4, *Content and redaction*, *Correlation*; DO-7 M-13, M-27.
- SCREEN_SPECS SCR-6 flow states (joined, handed back, chat closed) — states only.
- Slice plan §0a (journey map, J-7) and rule `.claude/rules/integrated-journeys.md` §3–§4; UX-join amendments
  `docs/plans/ux-join/backend-amendments.md` AEA-46-1, AEA-46-2 and §3; residual R-W-16
  (`docs/plans/7b-decisions/residuals-web.md`; staff.md §5 live-action version rule).
- **Contract notes (OpenAPI wins; listed, not edited; AEA-08 reconciles, STF-26):** (1) api-con-mapping §1 serves CON-14
  and CON-21 from `web/routes/staff.py`; the slice plan moves them to `web/routes/staff_live.py`. (2) `liveChatAction`
  documents a 403 example `NOT_CLAIMED_BY_YOU` only; a role outside `x-roles` gets 403 `ROLE_NOT_ALLOWED` (UI_CONTRACTS
  *Access*; the 403 `ApiError` schema admits both). (3) UI_CONTRACTS CON-21's error list omits `ROLE_NOT_ALLOWED`; the
  OpenAPI documents 403 `RoleNotAllowed`. (4) DO-6 WF-4 names "takeover and live chat (CON-14, CON-3 stream)"; CON-21
  postdates DO-6 and is registered by AC-24. (5) The OpenAPI `NOT_LIVE` `demo_reset` example is illustrative only
  (MC-25). (6) The slice plan's *Calls (injected)* names cases (29); staff.md §5 resolves ownership with AEA-10's
  in-transaction `core.cases_ro.owner`, so no `CaseService` method is called.
- **Brief check:** serves "Escalation must be graceful: … hands off with enough context that a human can pick up without
  starting over." (Part B §4) and "a reviewer should be able to … watch the agent escalate" (Part B §6); touches nothing
  out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `join` with its preconditions met (case owned by the actor's role, `live_state` `queued`) writes in one transaction: `controller` human, `live_state` `joined` with `live_since` = the demo clock, `representative_joined` then `ai_paused` on the thread stream, `controller_changed` (human, "Riley") on `case:<ref>`, and one `case_event` with `actor_role` representative; the `cases` owner and `promises` rows are unchanged — verify: `tests/services/test_live_chat.py::test_join_writes_one_transaction` (`temp_sqlite()`, `FixedClock`) — evidence: rows and events read back; event ids ascending; owner and promise rows equal the pre-call snapshot.
- [ ] AC-2 [failure/refusal] Checks 1–4 and 7–8 of staff.md §5 each give their result and a refusal writes nothing: unknown case → `CASE_NOT_FOUND`; `join` unowned → `NOT_CLAIMED_BY_YOU` {owner: null}; `join` owned by supervisor → `CASE_ALREADY_CLAIMED` {claimed_by "Demo supervisor", claimed_at}; `send` by a non-owner → `NOT_CLAIMED_BY_YOU` {owner "Demo supervisor"}; `join` while `not_live` → `NOT_LIVE` {reason `not_waiting`}; `send` while `queued` → `NOT_LIVE` {reason `not_joined`}; `send` while `closed` → `NOT_LIVE` {reason `chat_closed`} (row 5 is defensive and untested, MC-25) — verify: `…::test_checks_in_order_write_nothing` (one parametrised case per row) — evidence: each `LiveRefused` code and details; row and event counts unchanged per case.
- [ ] AC-3 [invariant] Repeats are idempotent (checks 6 and 8): `join` while already `joined`, `hand_back` on `handed_back` and `close` on `closed` return 200 with the current view and write no row or event — verify: `…::test_repeats_write_nothing` — evidence: views returned; counts unchanged.
- [ ] AC-4 [invariant] `send` writes the representative's message into the customer's own thread (`core.messages.append` with the case's `thread_id`, role `representative`, demo-clock `at`) and `staff_message` on that thread's stream in one transaction, and returns it as `StoredChatLine` with `speaker_name` "Riley" — verify: `…::test_send_same_thread` — evidence: the message row's `thread_id` equals the customer's; response `message` matches the row.
- [ ] AC-5 [invariant] `hand_back` sets controller ai and `live_state` `handed_back` with `ai_resumed` (thread) and `controller_changed` (ai, null) (case); `close` sets controller ai and `live_state` `closed` with `chat_closed` on the thread stream and `chat_closed` {reason `closed_by_staff`} on the case stream; after every action `controller = human` holds exactly when `live_state = joined` — verify: `…::test_hand_back_close_and_controller_invariant` — evidence: states and events as listed; invariant asserted after each of the four actions.
- [ ] AC-6 [invariant] All or nothing: a failure injected after the controller write (the events append raising) leaves controller, live state, messages, events and case events as they were — verify: `…::test_live_action_rolls_back` — evidence: values equal the pre-call snapshot.
- [ ] AC-7 [negative] A staff message is stored and relayed through the STORE profile (DO-6 *Content and redaction*; data.md §1): a `send` containing a synthetic 16-digit card-like number and a standalone 6-digit number stores, relays and returns `[card number removed]` and `[code]` in their place — verify: `…::test_staff_message_store_redacted` (`redact_store` bound as `lambda t: redact(t, RedactionProfile.STORE).text`, MC-23) — evidence: neither digit run in the `messages` row, the `staff_message` event or the response.
- [ ] AC-8 [invariant] Claims belong to the role (STF-1): with MHC-C-0007 claimed by representative through one login session, a second session acting as representative joins it successfully — verify: `…::test_two_sessions_share_riley` — evidence: 200 `JOINED` for the second session.
- [ ] AC-9 [invariant] `liveChatAction` 200 bodies validate against `LiveActionResponse` for `JOINED`, `SENT`, `HANDED_BACK` and `CLOSED` — verify: `tests/api/test_staff_live_routes.py::test_live_action_matches_openapi` (AEA-23's `assert_response_matches`, STF-8) — evidence: four bodies validate.
- [ ] AC-10 [failure/refusal] Route mapping of `LiveRefused`: 404 `CASE_NOT_FOUND`, 403 `NOT_CLAIMED_BY_YOU` with `details.owner`, 409 `CASE_ALREADY_CLAIMED` with `details.claimed_by` and `claimed_at`, 409 `NOT_LIVE` with `details.reason`; `action: "wave"` → 400 `VALIDATION_ERROR` field `action` — verify: `…::test_live_action_refusals` — evidence: each body validates against its documented response.
- [ ] AC-11 [failure/refusal] `text` rules (STF-12): `send` with `text` null, "   " or 2,001 characters, and `join` with any `text`, each answer 400 `VALIDATION_ERROR` field `text` with constraint "required for send", "required for send", "at most 2000 characters" and "only for send", and no service call — verify: `…::test_text_rules` — evidence: four 400 bodies validate; zero service calls; the submitted text absent from bodies and captured logs.
- [ ] AC-12 [failure/refusal] Roles: `liveChatAction` passes only the representative; customer, supervisor and owner get 403 `ROLE_NOT_ALLOWED` with `details.needs` `["representative"]`; `streamCaseEvents` passes representative, supervisor and owner and the customer gets 403 with `needs` `["representative", "supervisor", "owner"]` — verify: `…::test_live_roles` — evidence: bodies validate against `RoleNotAllowed`; no service or poll call recorded for refusals.
- [ ] AC-13 [invariant] `streamCaseEvents` answers `text/event-stream`; frames carry `id`, `event` and `data`, and `assert_sse_frames_match(frames, "streamCaseEvents")` passes; with `Last-Event-ID: 30` only events with id > 30 arrive, in order, and one `stream_reconnect` record with `case_ref` and `last_event_id` 30 is written; an event appended after connecting arrives on a later poll; an idle stream sends a `: heartbeat` comment (interval shortened by patching the module constant); an unknown case answers 404 `CASE_NOT_FOUND` before any frame — verify: `…::test_case_stream_replay_live_and_heartbeat` (async client) — evidence: frames parsed and validated; order asserted; one `stream_reconnect` record.
- [ ] AC-14 [invariant] Start point and close rules (staff.md §7, MC-8): after a reset appends `demo_reset` to `case:MHC-C-0005` and the seed re-creates the case, a connection with no `Last-Event-ID` receives no `demo_reset` frame and stays open; a connection whose `Last-Event-ID` is below that `demo_reset` id receives it and the stream closes; a stream that sends `chat_closed` stays open — verify: `…::test_case_stream_start_after_reset_and_close_rules` — evidence: the three outcomes asserted.
- [ ] AC-15 [invariant] Streams share the one limiter and never block the loop (STF-13, DO-3 §2.3 rule 4): with all 4 slots of `get_stream_poll_limiter()` held, a fifth poll read waits, and a `def` route (`liveChatAction`) still answers while five streams are open — verify: `…::test_streams_share_limiter` — evidence: the fifth poll completes only after a slot is released; the route answers within the test's timeout.
- [ ] AC-16 [invariant] During a reset (staff.md §11): with a fake `ResetGate` held, an open stream skips its poll read and never answers 503; a new connection is accepted without waiting; `liveChatAction` waits up to `reset_wait_s` and then runs (never 503) — verify: `…::test_reset_gate_behaviour` — evidence: zero poll reads while held; no 503 body; the action's documented answer after the gate clears.
- [ ] AC-17 [negative] A distinctive staff message string and the customer's relayed text are present in the `messages` rows and the response or frame, and absent from every captured log record (all loggers, `request` and `stream_reconnect` included) — verify: `…::test_message_text_never_logged` — evidence: both strings absent from captured logs.
- [ ] AC-18 [invariant] Login gate: both operations answer 401 `UNAUTHENTICATED` without `mhc_session` (AEA-23's real middleware) — verify: `…::test_login_gate` — evidence: two 401 bodies validate.
- [ ] AC-19 [invariant] The route files read no clock and import no `routes/events.py` symbol: `grep -nE "datetime\.now|time\.time|routes\.events|routes/events" src/meridian/web/routes/staff_live.py src/meridian/web/schemas/staff_live.py` prints nothing — verify: the grep, run by `code-review-agent` — evidence: empty output.
- [ ] AC-20 [capture] Driving `liveChatAction` (join, send, hand_back, close) and `streamCaseEvents` through the app the container builds (real `LiveChatService` over `temp_sqlite()`, `require_staff` doubled) leaves one `request` record per call (`request_id` = `X-Request-ID`, route template, `caller_role`), one `case_event` per live action with `actor_role` and action in the action's transaction (DO-6 CAP-4 "case_event per action with actor role"), and stream events that carry the case's `thread_id` (thread stream) and `case_ref` (case stream) (DO-6 *Correlation*) — verify: `…::test_wf4_live_entry_points_emit_records` — evidence: records, case events and event streams printed. The full CAP-4 is AEA-52's; the relayed `to_staff` turn is AEA-51's.
- [ ] AC-21 [invariant] Live actions leave the case alone: after `join`, `send`, `hand_back` and `close` on a claimed case at version n, the case's `version` is still n and its `lifecycle` unchanged, `case:<ref>` receives only `controller_changed` (join, hand back) and `chat_closed` (close) and no `case_changed`, and a CON-13 `resolve` sent afterwards with `expected_version` n (the version read before the join) is accepted (AEA-46-1; staff audit A4; R-W-16; staff.md §5 live-action version rule; moving to `in_progress` stays the explicit `start` action, and the OpenAPI `LIVE_JOINED` example's `in_progress` is illustrative) — verify: `tests/services/test_live_chat.py::test_live_actions_keep_case_version` (temp SQLite; `CaseService` double honouring cases.md §5, or AEA-29's when merged) — evidence: version n before and after; the case-stream event types printed; the resolve accepted.
- [ ] AC-22 [contract] `tests/contract/cases/staff_live.py` holds the server cases for `liveChatAction` (join, send, hand_back, close on a claimed live-queued case) and `streamCaseEvents` (first connect and resume), with each documented error status the routes can produce (401, 403, 404, 409 `NOT_LIVE` / `CASE_ALREADY_CLAIMED`, 400 field `text`), frames checked with `assert_sse_frames_match` (AEA-46-2) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "liveChatAction or streamCaseEvents" -rs` once AEA-59's runner is merged — evidence: one pass per case.
- [ ] AC-23 [journey] Extends J-7 (slice plan §0a journey map): join, send, hand back and close through `liveChatAction`: the customer's thread shows each line, the case `version` is unchanged by all four (staff audit A4), and `streamCaseEvents` delivers `controller_changed` and no `case_changed`; asserting what the user sees and what is stored, in `tests/journeys/j7/test_aea_46.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j7/test_aea_46.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-46.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-24 [regression/context] Same change updates `.claude/reference/area-map.md` (this issue's row, planned → actual with the commit), `.claude/state/icm-progress.md` (the A9 staff-console row's evidence link), DO-3 §3's status for `services/live_chat.py`, `web/routes/staff_live.py`, `web/schemas/staff_live.py`, and registers CON-21 `streamCaseEvents` in WF-4's entry-point cell of `docs/design/observability-contract.md` (DO-6 *Registering a new workflow*, steps 1 and 4) — verify: `git diff --stat` — evidence: only those rows change.

### Observability

- Responsibilities: WF-4 (DO-6 registry) — the `request` record per call with `caller_role`; one `case_event` per live
  action with actor role and action; thread-stream events carrying `thread_id` and case-stream events carrying
  `case_ref`; a `stream_reconnect` record with `case_ref` on every CON-21 reconnect (web.md §10);
  `conversations.controller` as the one authority AEA-40's turn path reads to record relayed customer turns as
  `outcome = to_staff`. Staff and customer message text never in logs (AC-17); stored text STORE-redacted (AC-7).
- Capture evidence: AC-20 (both entry points through the app), AC-13 (`stream_reconnect`), AC-7 and AC-17 (negative).
  CAP-4 end to end is AEA-52's.

### Evaluation

- Checks: none added. WF-4's evaluation duty (DO-6: "flags feed the review list (R-37), never the eval set unreviewed")
  is untouched: this issue writes no flag and no eval row (AC-1 and AC-20 list every row it writes). No DO-5 suite
  (E-1…E-8) drives the staff live chat; the customer-side effect (`AI_PAUSED`, relayed `to_staff` turns) is scored
  through the customer path at AEA-40 and AEA-51.
- Expected-answer authority: DO-5 *Expected-answer authority*; a representative's reply is a person's answer, judged by
  people, and this issue decides no correct answer.

### Metrics

- References: M-13 (promises kept on time), M-27 (unowned and overdue cases).
- Acceptance conditions: both stay computable from `CaseService`'s records because live actions never change case
  ownership or promise rows (AC-1), nor the case's `version` or `lifecycle` (AC-21): a live message is not a kept-promise event (cases.md §5 *Promise kept*: a resolve
  or a CON-15 contact), so M-13 and M-27 read exactly what AEA-29 and CON-15 record. Every live action leaves a
  demo-clock `case_event` with the actor role (AC-20) for the case history. No target is set here.

### Blocked by

- AEA-10 (storage: `conversations.live_state` / `live_since`, `core.cases_ro.owner`, `core.messages.append`,
  `core.events.append/after/latest_of`, `cases.case_events.append`, `temp_sqlite()`).
- AEA-23 (web app, middleware, `web/deps.py` with `require_staff`, `get_live_chat`, `get_stream_poll_limiter`,
  `ResetGate`, `openapi_check.py`).
- Evidence only, not a merge edge (wave unchanged): AC-21 uses a `CaseService` double until AEA-29 (same wave) merges;
  AC-22's strict run waits for AEA-59's runner, and AC-23's journey record stays `mock-tested` with *Blocked by* AEA-57
  and AEA-52 until they land (`integrated-journeys.md` §4).

### Agent handoff

- **Area / owner:** A9 Staff console (DO-3 §8); files `src/meridian/services/live_chat.py`,
  `src/meridian/web/routes/staff_live.py`, `src/meridian/web/schemas/staff_live.py`, this issue's `register_…()` hunk in
  `web/container.py` (binds `get_live_chat()` to `LiveChatService(uow, demo_clock, redact_store)` with the container's
  demo clock and `lambda t: redact(t, RedactionProfile.STORE).text`; includes the router), tests under
  `tests/services/` and `tests/api/`, `tests/contract/cases/staff_live.py` (AC-22) and `tests/journeys/j7/test_aea_46.py`
  (AC-23; `tests/journeys/support/` is AEA-57's, never edited here).
- **Contracts and shared surfaces:** consumes `UnitOfWorkFactory` and the `repos_core` / `repos_cases` methods above
  (AEA-10), `require_staff` / `StaffActor` / `STAFF_PERSONAS` (AEA-23 declares, AEA-44 implements, AEA-02 types),
  `redact` STORE (AEA-04), `policy/texts.py` `live` group (AEA-03), the `Clock` port (`DemoClock`, AEA-30, injected),
  and, in AC-21's test only, `CaseService.apply` (AEA-29) as a double honouring cases.md §5 (the service calls no
  `CaseService` method, contract note 6);
  produces CON-14, CON-21 and the `conversations.controller` / `live_state` writes for AEA-40 (`AI_PAUSED`, relay),
  AEA-51, AEA-52 and AEA-55. Must not edit: `routes/events.py` (AEA-41, CON-3), `web/{app,middleware,deps,errors}.py`,
  `repos_core.py`, `repos_cases.py`, `db.py`, `services/cases.py`, any other route or schema file, `domain/*`,
  `tests/api/openapi_check.py`, the OpenAPI.
- **Scope boundary / refusal:** no claim (CON-13, AEA-45); no change to the customer turn path or to who appends
  `customer_message`; no shared SSE helper with CON-3 until a third stream exists (DO-3 S-11); no progress events; no
  owner or promise write.
- **Decisions applied:** STF-1 (identity is the role), STF-7 (no 503; streams never wait), STF-8 (shared validator),
  STF-11 (refusal order), STF-12 (`text` rules), STF-13 (shared limiter), STF-14 (`live_state` / `live_since`), STF-23
  with MC-7 and MC-8 (stream contract, start after the newest `demo_reset`), MC-23 (`redact_store` binding), MC-25
  (row 5 defensive only), R-W-16 (live actions never change case `version` or `lifecycle`; staff.md §5).
- **Wave and gates:** wave 2; no gate.
- **Lane:** `lane::build-loop` — service, routes and tests (ticket-lanes: changes code).
- **Risk:** None (slice plan). Roles are demo labels behind the login (R-48); stored text goes through AEA-04's STORE
  profile (AC-7).
- **Entry points added or changed:** WF-4 (`POST /api/staff/cases/{reference}/live`;
  `GET /api/staff/cases/{reference}/events`, registered in WF-4 by AC-24).
