## [AEA-41] customer API: chat event stream (CON-3)

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

> **US-15:** "As a **homeowner** during staffed hours (simulated in the demo), I need to wait in the same chat and see
> clearly when a person has joined and the assistant has stopped, so that I know who I'm talking to."

**Example pair (the OpenAPI `FRAMES` example, WP-2 thread).** The `events` table holds, on Omar Patel's thread stream,
event 12 `representative_joined` ("Riley (demo representative) has joined."), 13 `ai_paused` ("The assistant is paused
while Riley is here.") and 14 `staff_message` ("Hi Omar, I can look at the after-hours charge with you."). The browser's
stream drops after event 12 and reconnects with `Last-Event-ID: 12`. Expected output: `GET
/api/chat/sessions/{thread_id}/events` (`streamChatEvents`) sends exactly events 13 and 14, in order, as SSE frames
(`id: 13` / `event: ai_paused` / `data: <ChatEvent JSON>`), writes one `stream_reconnect` log record (`last_event_id` 12,
`replayed` 2), then a `: heartbeat` comment every 15 s while nothing new arrives; nothing before 13 is repeated.

**The behaviour.** One `async def` route in `web/routes/events.py`, its frame/payload models in `web/schemas/events.py`
(stage7/web.md §11; DO-3 §2.1: the only async endpoints are the event streams and `/healthz`):

- **Gate and ownership.** The login gate is AEA-23's middleware (no session → 401 `UNAUTHENTICATED`). The thread is
  resolved with `owned_stream_thread` from `web/deps.py` (stage7/web.md §4, §11; R-W-3; WEB-34, MC-16): `owned_thread`
  with its 410 branch mapped, no second lookup, so a malformed, unknown or another session's thread **and this session's
  ended thread** answer the identical 404 `SESSION_NOT_FOUND` (the operation documents no 410). Response headers: `text/event-stream`,
  `Cache-Control: no-store`, `X-Request-ID`.
- **Start point.** `Last-Event-ID` header if present, else **0**, the whole thread stream (WEB-16; stage7/web.md §11).
  One path for live and replay.
- **One stream per thread.** Demo-wide events (`staffing_changed`, `clock_changed`, `demo_reset`) are written by their
  writers as one row per open thread, in the writer's own transaction (WEB-17; stage7/cases.md §6–§7); the route reads one
  `StreamKey` (the thread variant, DO-4 §13) and never merges.
- **Polling.** Every `STREAM_POLL_S = 1.0` s [A] (DO-3 S-11; replaced by the measured `first_event_ms` at Stage 9) it
  reads `core.events.after(thread_stream, last)` (DO-4 §13, AEA-10) in a read unit of work, off the event loop, under
  `get_stream_poll_limiter()`: the **one** `anyio.CapacityLimiter(4)` per process shared with CON-21 (WEB-19; DO-3 §2.3
  rule 4). While `ResetGate.held()` (stage7/web.md §7) it skips the poll read, never waits on connect and never answers 503.
- **Heartbeat.** A `: heartbeat` comment after `STREAM_HEARTBEAT_S = 15` s without a frame [Source: OpenAPI
  `streamChatEvents` "Heartbeat comment every 15 s (decided 2026-10-21)"].
- **Types.** Only `CHAT_EVENT_TYPES` (the nine OpenAPI `ChatEvent` members: `representative_joined`, `staff_message`,
  `ai_paused`, `ai_resumed`, `chat_closed`, `staffing_changed`, `shift_ended`, `clock_changed`, `demo_reset`) are ever
  sent; a stored row of any other type is skipped (stage7/web.md §11). No `case_created` (UXR-10), no progress events
  (SDQ-2 = A). After sending `chat_closed` or `demo_reset` the server closes the stream.
- **Records.** When `Last-Event-ID` > 0 it emits the `stream_reconnect` log record `{record, request_id, thread_id,
  last_event_id, replayed}` (stage7/web.md §10, WEB-18). The `request` record is AEA-23's middleware's.
- **Read only.** It writes no event and no row; frames carry the stored payload unchanged. Writers: AEA-46 (join, staff
  message, pause, resume, close), AEA-29/AEA-30 (`shift_ended`, `staffing_changed`, `clock_changed`), AEA-31 (`demo_reset`).

**Produced for other issues:** CON-3 for AEA-52 (staff and demo end to end, CAP-4 through the real writers) and AEA-55
(UI against the real backend).

### Source

- `docs/ux/03-structure/ui-contracts.openapi.yaml` (read-only): `streamChatEvents` (description, `FRAMES` example,
  `Last-Event-ID` header, responses 200 / 401 / 404, `x-timing.first_event_ms` 1000 [A]), `x-event-schema` `ChatEvent`
  and its nine `Ev*` members; responses `Unauthenticated`, `SessionNotFound`.
- `docs/design/contracts/stage7/web.md` §4 (`owned_thread`, `owned_stream_thread`, `get_stream_poll_limiter`,
  `get_uow_factory`), §7 (streams
  never wait; skip polls while held), §10 (`stream_reconnect`, `request`), §11 (CON-3 stream rules), §13
  (`assert_sse_frames_match`, `assert_response_matches`); decisions WEB-16, WEB-17, WEB-18, WEB-19, WEB-34
  (`docs/plans/7b-decisions/web.md`); merge MC-16 (`docs/plans/7b-decisions/merge-clashes.md`); residual R-W-3
  (`docs/plans/7b-decisions/residuals-web.md`).
- UX-join amendments `docs/plans/ux-join/backend-amendments.md` §2 AEA-41-1 (per-route contract cases) and §3 (the
  `[journey]` criterion, pattern A; J-9 and the proposed J-7); slice plan §0a journey map and rule
  `.claude/rules/integrated-journeys.md` §3–§4.
- `docs/design/contracts/stage7/cases.md` §1.1 (`events.id` AUTOINCREMENT, never reused after a reset; `ended_threads`),
  §1.2 (`core.conversations.lookup`), §6–§7 (demo-wide writers).
- DO-4 §0 (`EventId`), §13 (no event Protocols; `core.events.after`; reconnect replays from `Last-Event-ID`).
- DO-3 §2.1, §2.3 rule 4, §6 S-11. DO-2 `system-design.md` §8.2 (*Event stream (CON-3)* row; signal `stream_reconnect`),
  §9, SDQ-2, SDQ-5.
- DO-6 `observability-contract.md` WF-4 row (CON-3 stream registered under the takeover workflow), CAP-4, *Content and
  redaction*. DO-7 M-13, M-27.
- PRD R-30, R-31; US-15, US-20. `api-con-mapping.md` §1 row CON-3, §2.1 UXR-10.
- Slice plan row AEA-41; area-map row A8 Customer API; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "a reviewer should be able to type questions, probe edge cases, and watch the agent escalate"
  (briefing Part B §6); touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Replay: with events 12, 13 and 14 stored on a thread stream, a connection with `Last-Event-ID: 12` receives frames 13 then 14 and nothing earlier — verify: `tests/api/test_events.py::test_replay_after_last_event_id` (frames checked with `assert_sse_frames_match(frames, "streamChatEvents")`, stage7/web.md §13) — evidence: parsed frame ids `[13, 14]`; every `data:` validates against `ChatEvent` and its `event_id` equals the frame `id`.
- [ ] AC-2 [invariant] No `Last-Event-ID` → start at 0 (WEB-16): a first connection after two events were appended receives both — verify: `tests/api/test_events.py::test_first_connect_replays_from_zero` — evidence: both stored ids received in order.
- [ ] AC-3 [invariant] Live delivery: an event appended through `core.events.append` while the stream is open arrives as the next frame within two `STREAM_POLL_S` intervals — verify: `tests/api/test_events.py::test_live_event_delivered` — evidence: frame received; its `id` is the appended `EventId`.
- [ ] AC-4 [invariant] Heartbeat: with no new events, a `: heartbeat` comment follows every 15 s (time driven by a test clock, no real sleeps) — verify: `tests/api/test_events.py::test_heartbeat_every_15s` — evidence: comment frames at 15 s and 30 s.
- [ ] AC-5 [invariant] The stream closes after `chat_closed` and after `demo_reset`, each delivered first — verify: `tests/api/test_events.py::test_stream_closes_after_chat_closed_and_demo_reset` — evidence: last frame type as stated; the response ends.
- [ ] AC-6 [failure/refusal] No login session → 401 `UNAUTHENTICATED` from AEA-23's middleware; a malformed id (`thr_9d41`), an unknown UUID and another session's thread → the identical 404 `SESSION_NOT_FOUND` through `owned_stream_thread` (web.md §4, R-W-3; WEB-34); no stream starts — verify: `tests/api/test_events.py::test_auth_and_ownership` (`assert_response_matches(response, "streamChatEvents")`) — evidence: bodies validate; the three 404 bodies differ only in `request_id`.
- [ ] AC-7 [failure/refusal] A tombstoned thread of this session (after a reset, `core.conversations.lookup` returns `EndedThread`) never gets a status `streamChatEvents` does not document: it answers 404 `SESSION_NOT_FOUND` through `owned_stream_thread` (web.md §4, §11; settled R-W-3), and the 404 body equals an unknown thread's apart from `request_id` — verify: `tests/api/test_events.py::test_ended_thread_answers_documented_status` — evidence: status 404; `assert_response_matches(response, "streamChatEvents")` passes; the two bodies differ only in `request_id`.
- [ ] AC-8 [invariant] Poll reads never run on the event loop and never exceed 4 at once: with 6 streams open, each poll runs on a worker thread under the limiter `get_stream_poll_limiter()` returns (one instance per process, WEB-19) — verify: `tests/api/test_events.py::test_poll_reads_off_loop_limited_to_4` (recording repository double) — evidence: max concurrent reads 4; no read on the loop thread; the limiter object is the provider's.
- [ ] AC-9 [invariant] During a reset the stream neither waits nor refuses: with a fake `ResetGate` held, a connection opens at once (200), no poll read happens while held, and after release the appended `demo_reset` is delivered and the stream closes (stage7/web.md §7, §11) — verify: `tests/api/test_events.py::test_reset_gate_skips_polls` — evidence: zero reads recorded while held; then the `demo_reset` frame and end of response.
- [ ] AC-10 [invariant] A client disconnect ends that stream's poll loop within one poll interval and frees its limiter slot (no leaked task) — verify: `tests/api/test_events.py::test_disconnect_stops_polling` — evidence: no further reads for that stream; limiter borrowed count back to its prior value.
- [ ] AC-11 [negative] Only the nine `ChatEvent` types are sent: a stored row of another type on this thread's stream (for example `case_changed`) is never emitted, and the frames after it still arrive in order — verify: `tests/api/test_events.py::test_only_chat_event_types_sent` — evidence: the foreign row's id is absent from the frames; the following event arrives.
- [ ] AC-12 [negative] Frames carry exactly the stored payload, and the stream's log output holds IDs, status and timings only: the staff message text "Hi Omar, I can look at the after-hours charge with you." appears in the frame and in no captured log record (`request`, `stream_reconnect` or any other) — verify: `tests/api/test_events.py::test_frames_equal_stored_and_logs_hold_no_text` (caplog) — evidence: frame `data` equals the stored JSON; the sentence is absent from caplog.
- [ ] AC-13 [negative] The route writes nothing: it opens only read units of work (`uow(write=False)`), and after a replay, a live event and a reconnect every table's row count except the rows the test appended is unchanged — verify: `tests/api/test_events.py::test_stream_is_read_only` (temp SQLite from `tests/fixtures/sqlite.py`) — evidence: no `write=True` call recorded; row counts equal.
- [ ] AC-14 [capture] Driving the real route through the app the container builds (AEA-23 middleware) leaves one `request` record with route template `/api/chat/sessions/{thread_id}/events`, status 200, `thread_id` and `caller_role`, and `request_id` equal to the `X-Request-ID` header (WF-4); a reconnect with `Last-Event-ID: 12` also leaves one `stream_reconnect` record `{request_id, thread_id, last_event_id: 12, replayed: 2}`, and a first connect without the header leaves none — verify: `tests/api/test_events_capture.py::test_stream_request_and_reconnect_recorded` — evidence: records read back from the log capture. (CAP-4 end to end with the real writers: AEA-52.)
- [ ] AC-15 [contract] `tests/contract/cases/events.py` holds the server case for `streamChatEvents` (AEA-41-1): a started thread, a first connect with no `Last-Event-ID`, a resume with one, and each documented error status (401, 404), every frame checked with `assert_sse_frames_match` — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k streamChatEvents -rs` once AEA-59's runner is merged — evidence: the case passes with its frame count printed.
- [ ] AC-16 [journey] Extends J-9 and J-7 (slice plan §0a journey map; J-7 is a proposed addition to the map, from the join audits): J-9, a stream reconnect with `Last-Event-ID` gets each missed event once and writes a `stream_reconnect` record; J-7, during a takeover the customer's stream delivers `representative_joined`, `ai_paused`, `staff_message` and `ai_resumed` in order; asserting what the user sees and what is stored, in `tests/journeys/j9/test_aea_41.py` and `tests/journeys/j7/test_aea_41.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j9/test_aea_41.py tests/journeys/j7/test_aea_41.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57, AEA-51 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-41.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-17 [regression/context] Context-management rule 3 does not apply (no model prompt). In the same change: `.claude/reference/area-map.md` row A8 (`web/routes/events.py`, `web/schemas/events.py` planned → actual + commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link), DO-3 §3 line for `web/routes/events.py` marked built — verify: `git diff --name-only` — evidence: those three files in the diff, only this issue's rows changed.

### Observability

- Responsibilities: for WF-4 (DO-6 registers the CON-3 stream under the staff-takeover workflow; the chat page of WF-1 opens it), preserve the middleware's `request` record (`request_id`, route template, status, `caller_role`, `thread_id`) and emit the `stream_reconnect` record (stage7/web.md §10, WEB-18; the DO-2 §8.2 signal) with IDs and counts only; relayed staff lines keep the `thread_id` the writers stored. No event text, name or contact value reaches a log line (DO-6 *Content and redaction*, LOG allow-list).
- Capture evidence: AC-14 drives the real entry point and reads both records back; AC-12 is the negative check on log content; AC-13 proves the stream writes nothing.

### Evaluation

- Checks: no DO-5 suite drives CON-3; WF-4's evaluation rule (flags feed the review list, never the eval set unreviewed, R-37) stays true because this route reads `events` only and writes no flag or eval row (AC-13).
- Expected-answer authority: the OpenAPI `ChatEvent` schema and the rows the writers stored decide what a frame must contain; DO-5 *Expected-answer authority* ("A model is never its own authority") has no row for event relay because no model is involved, and this route only relays (AC-12).

### Metrics

- References: M-13 (promises kept on time) and M-27 (unowned and overdue cases), inherited from WF-4.
- Acceptance conditions: this route computes neither and writes nothing (AC-13), so M-13 and M-27 stay computable from the `promise`, `case` and `case_event` rows AEA-29 and AEA-30 write. No target is set here.

### Blocked by

AEA-10, AEA-11, AEA-23 (slice plan row AEA-41); `owned_stream_thread` is AEA-23's (web.md §4, R-W-3). Record-level
only, not merge blockers: AC-15 runs once AEA-59's runner (wave 2) merges; AC-16's journey level waits on AEA-57 (wave
2), AEA-51 and AEA-52 (wave 3).

### Agent handoff

- Area / owner: A8 Customer API; files `src/meridian/web/routes/events.py`, `src/meridian/web/schemas/events.py`, this
  issue's `register_<area>()` hunk in `web/container.py` (stub from AEA-01; the router is included from it), tests under
  `tests/api/`, `tests/contract/cases/events.py` (AC-15; AEA-59 owns the runner) and `tests/journeys/j9/test_aea_41.py`,
  `tests/journeys/j7/test_aea_41.py` (AC-16; `support/` is AEA-57's).
- Contracts and shared surfaces: consumes `core.events.after`, `core.conversations.lookup` (through `owned_stream_thread`)
  and `temp_sqlite()` (AEA-10); `StreamKey`, `EventId` (AEA-02); `owned_stream_thread`, `get_uow_factory`,
  `get_stream_poll_limiter`, `get_reset_gate`, `RequestContext`, the LOG formatter and `tests/api/openapi_check.py`
  (AEA-23); `tests/fakes/` (AEA-11). Tests seed rows with `core.events.append`. Produces CON-3 for AEA-52 and AEA-55.
  Must not edit `repos_core.py`, `web/{app,middleware,deps,logging}.py`, `routes/chat.py`, the CON-21 stream
  (`routes/staff_live.py`, AEA-46) or the OpenAPI.
- Scope boundary / refusal: no event writing; no shared SSE helper with CON-21 until a third stream exists (DO-3 S-11;
  stage7/staff.md §7 "its own generator"); no progress events (SDQ-2 = A); no merging of demo-wide streams (WEB-17).
- ND-1 — Settled (R-W-3): CON-3 uses `owned_stream_thread` (web.md §4, §11); an ended thread of this session gets the
  identical 404. Adding 410 to the OpenAPI is Innocent's (join Decision 4, `docs/plans/ux-join/decisions-for-innocent.md`);
  if he does, AC-7 expects 410 `{reason: demo_reset}` (the conditional amendment AEA-41-2, not applied), the route
  switches to `owned_thread`, and nothing else moves.
- Wave and gates: wave 2; no gate.
- Lane: build-loop — it changes source and tests (`ticket-lanes.md`).
- Risk: None (slice plan). Ownership comes from AEA-23's `owned_stream_thread`, and the stream carries only rows the writers
  stored; a reviewer who sees a cross-session leak path here should propose `risk::security`.
- Entry points added or changed: WF-4 (CON-3 `GET /api/chat/sessions/{thread_id}/events`, `streamChatEvents`)
