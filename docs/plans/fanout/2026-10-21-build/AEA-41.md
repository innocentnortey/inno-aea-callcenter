# Plan — [AEA-41] customer API: chat event stream (CON-3)

**Status:** planned (READY) · **Lane:** `lane::build-loop` · **Risk:** none (no `risk::security`: no frozen tests, no
security agent) · **Wave:** 2
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/41 (spec copy:
`docs/plans/tickets/AEA-41.md`) · **Base revision:** `main` at `c7ce976` (AEA-23 web shell merged in `1e6889a`;
AEA-10 storage and AEA-11 fakes merged earlier)
**Planner:** fanout-planner (claude-opus-5-5), 2026-10-21. **Implementer:** fanout-implementer (Sonnet). Every decision
below is made; if something here turns out wrong against the code, stop and send the slice back to the planner.

---

## 1. Goal and sources

### Goal

Quoted from the issue (*What to build*): "One `async def` route in `web/routes/events.py`, its frame/payload models in
`web/schemas/events.py` (stage7/web.md §11; DO-3 §2.1: the only async endpoints are the event streams and `/healthz`)."
`GET /api/chat/sessions/{thread_id}/events` (`streamChatEvents`, CON-3) streams one chat thread's rows from the `events`
table as Server-Sent Events. It replays from `Last-Event-ID` (or from 0), polls every 1 s off the event loop under the
one shared `CapacityLimiter(4)`, sends `: heartbeat` after 15 s of silence, and sends only the nine `ChatEvent` types.
It closes after `chat_closed` or `demo_reset`, writes one `stream_reconnect` log record on a reconnect, and writes
nothing to the database.

**The worked pair (WP-2 thread, OpenAPI `FRAMES` example).** Omar Patel's thread stream holds event 12
`representative_joined`, 13 `ai_paused` and 14 `staff_message`. The browser reconnects with `Last-Event-ID: 12`. The
route sends exactly frames 13 and 14, in order (`id: 13` / `event: ai_paused` / `data: <ChatEvent JSON>`). It writes
one `stream_reconnect` record (`last_event_id` 12, `replayed` 2), then a `: heartbeat` comment every 15 s while nothing
new arrives. Nothing before 13 is repeated.

### Context

Wave 2 route ticket in A8 Customer API. The web shell (AEA-23) is on main. It provides the gate middleware, the
`request` record, `owned_stream_thread`, the stream limiter, the reset gate and the OpenAPI check. AEA-10's `events`
table and `EventsRepo.after` are on main. The writers of chat events (AEA-29/30/31/46) are siblings in the same wave or
later. This route only reads their rows, and the tests seed rows themselves. The plan stays relevant as long as
`stage7/web.md` §4, §7, §10, §11 and the OpenAPI `streamChatEvents` are unchanged.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-41.md` (= GitLab #41) | AC-1…AC-17, owned files, must-nots, ND-1 settled (404 for ended thread) |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-41 (blocked by 10, 11, 23; owns `routes/events.py`, `schemas/events.py`), §0a journey map (J-7 *proposed*, J-9), §3 collision map | Own hunk only in `web/container.py`; router included from the hunk; one journey file per journey |
| Requirements | PRD R-30, R-31; US-15, US-20 | Customer sees staff join/pause/message/resume in the same chat |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §0 (`EventId`), §13 ("No event Protocols … SSE routes poll `events WHERE stream = ? AND id > ?` … reconnect replays from Last-Event-ID") and the listed method `core.events.after(stream, last: EventId) -> list` | Read through `tx.core.events.after`; no event Protocol, no bus |
| Stage 7 addenda (win over DO-4) | `docs/design/contracts/stage7/web.md` §4 (`owned_stream_thread`, `get_stream_poll_limiter`, `get_uow_factory`, `get_reset_gate`), §7 (streams never wait; skip polls while held), §10 (`stream_reconnect` record), §11 (CON-3 rules and constants), §13 (`assert_sse_frames_match`, `assert_response_matches`) | Exact constants and rules copied in §4 below |
| Stage 7 cases | `stage7/cases.md` §1.1 (`events.id` AUTOINCREMENT, never reused; wall times stored UTC), §1.2 (`core.conversations.lookup`), §6–§7 (demo-wide writers append one row per open thread) | One stream per thread; replay from 0 is safe |
| Decisions | `docs/plans/7b-decisions/web.md` WEB-16 (start at 0), WEB-17 (one stream per thread), WEB-18 (`stream_reconnect`), WEB-19 (one limiter), WEB-34 (string path param, identical 404); MC-16; residual R-W-3; sign-off D-6 (no 410 on the chat stream) | All settled; nothing for Innocent |
| Code design | DO-3 `docs/design/code-design.md` §2.1 (async only for streams; web never touches SQLite on the loop), §2.3 rule 4 (`CapacityLimiter(4)`), §6 S-11 (polling, ~1 s [A]; no shared helper with CON-21) | Off-loop reads, one limiter |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `streamChatEvents` (lines ≈2479–2545): 200 `text/event-stream` with `FRAMES` example, 401 `Unauthenticated`, 404 `SessionNotFound`, `Last-Event-ID` header (integer), `Cache-Control: no-store`, `x-timing.first_event_ms` 1000 [A]; `ChatEvent` `oneOf` the nine `Ev*` schemas (lines ≈9982–10215); `Speaker` (≈8203) | Wire shape of frames and errors |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | n/a: no DO-5 suite drives CON-3; WF-4's rule stays true because the route writes no flag or eval row (AC-13) |
| Observability contract | DO-6 `docs/design/observability-contract.md` WF-4 row (line ≈79: "takeover and live chat (CON-14, CON-3 stream)"), §*Event stream (CON-3)* (line ≈145), records list (≈170: `request`, `auth_event`, `stream_reconnect`, `signal` are log records only), CAP-4 (≈266, owned by AEA-52) | Preserve `request` record; emit `stream_reconnect`; IDs and counts only |
| System design | DO-2 `docs/design/system-design.md` §8.2 (*Event stream (CON-3)* row: reconnect with last id, replay; signal `stream_reconnect`), SDQ-2 = A (no progress events), SDQ-5 (async SSE) | No progress events |
| Key-metrics registry | DO-7 M-13, M-27 (inherited from WF-4) | This route computes neither and writes nothing |
| Writer payload shape (sibling plans, read only) | `docs/plans/fanout/2026-10-21-build/AEA-30.md` §4.6 ("AEA-41 sends them unchanged after adding `event_id`, `type` and `at` from the row"), `AEA-31.md` step 1.8 (`demo_reset` payload `{"speaker": …, "line": …}`) | Frame data = `{event_id, type, at}` + stored payload |
| Journey rule | `.claude/rules/integrated-journeys.md` §3–§4; `docs/plans/ux-join/backend-amendments.md` §2 AEA-41-1, §3 (pattern A) | AC-15 case file; AC-16 at level `mock-tested` until AEA-57/51/52 |
| Build loop | `.claude/rules/build-loop-test-scope.md` + *AEA addition* | Affected tests and affected journeys only; no full suite (see §7) |

---

## 2. Boundary

### Owned files (the implementer creates or edits only these)

| File | Create / modify | Change |
|---|---|---|
| `src/meridian/web/routes/events.py` | create | The route, its timing dependency, the poll loop (≤ 200 lines) |
| `src/meridian/web/schemas/events.py` | create | Event types, frame encoding, heartbeat bytes (≤ 120 lines) |
| `src/meridian/web/container.py` | modify **only** the body and docstring of `register_events` | Include the router once |
| `tests/api/events_support.py` | create | Test doubles, the in-process ASGI stream harness, seed helpers, payload fixtures (≤ 500 lines) |
| `tests/api/test_events.py` | create | AC-1…AC-13 + PA-1, PA-2 (≤ 500 lines) |
| `tests/api/test_events_capture.py` | create | AC-14 |
| `tests/api/test_contract_cases_events.py` | create | AC-15 local driver (until AEA-59's runner) |
| `tests/contract/cases/events.py` | create | AC-15 server cases for `streamChatEvents` |
| `tests/unit/web/test_events_frames.py` | create | PA-3, PA-4, PA-5 (frame encoding, header parsing, stream key) |
| `tests/unit/web/test_register_events.py` | create | PA-6 (hunk) |
| `tests/journeys/j9/test_aea_41.py` | create | AC-16 J-9 |
| `tests/journeys/j7/test_aea_41.py` | create | AC-16 J-7 |
| `docs/testing/journeys/<build date>-AEA-41.md` | create | AC-16 evidence record (e.g. `2026-10-21-AEA-41.md`) |
| `.claude/reference/area-map.md` | modify **only the A8 row's last cell** | AC-17 |
| `.claude/state/icm-progress.md` | add **one** row | AC-17 |
| `docs/design/code-design.md` | add **one** `**Built:**` line in §3 | AC-17 |

### Shared surfaces: read only

`src/meridian/web/{app,deps,middleware,logging,errors}.py`, `src/meridian/web/routes/auth.py`,
`src/meridian/services/reset_gate.py`, `src/meridian/ports/runtime.py`, `src/meridian/domain/*`,
`src/meridian/adapters/sqlite/*` (incl. `rows.py`, `repos_core.py`, `repos_core_aux.py`, `db.py`), every other
`register_*` hunk in `web/container.py`, `tests/api/openapi_check.py`, `tests/api/web_shell_support.py`,
`tests/fixtures/sqlite.py`, `tests/fakes/*`, `tests/conftest.py`, `tests/journeys/{affected.py,README.md}`,
`pyproject.toml`, `uv.lock`, the OpenAPI, `docs/ux/**`, `apps/web/**`.

### Owned by other slices: never touch

`routes/chat.py` and `services/{turn,session}.py` (AEA-40), `routes/handoff.py` (AEA-42), `routes/demo.py` (AEA-43),
`routes/staff_live.py` and `services/live_chat.py` (AEA-46, CON-21), `services/{cases,handoff,demo,scheduler,reset}.py`
(AEA-29/30/31), `tests/journeys/support/` (AEA-57), `tests/journeys/browser/` (AEA-58), `tests/contract/test_openapi_*`
(AEA-59), other tickets' `tests/contract/cases/*.py`, other `j<N>/test_aea_<NN>.py` files.

---

## 3. Requirements table

Each ticket criterion appears with its implementation and its check. Plan-added rows are marked **PA** and are delivered
by this plan (the orchestrator may propose them on the issue).

| # | Requirement (ticket AC or source obligation) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 | [invariant] Replay: events 12, 13, 14 stored; `Last-Event-ID: 12` receives 13 then 14, nothing earlier; every `data:` validates against `ChatEvent`, `event_id` = frame `id` | `parse_last_event_id` → start 12; first poll `after(stream, 12)`; frames encoded by `encode_event_frame` | `tests/api/test_events.py::test_replay_after_last_event_id`: parsed ids `[13, 14]`; `assert_sse_frames_match(frames, "streamChatEvents")`; data lines equal the OpenAPI `FRAMES` example's lines for 13 and 14; one `stream_reconnect` record `{last_event_id: 12, replayed: 2}` |
| AC-2 | [invariant] No `Last-Event-ID` → start at 0 (WEB-16) | `parse_last_event_id(None) == 0` | `test_first_connect_replays_from_zero`: both stored ids in order; no `stream_reconnect` record; headers `text/event-stream`, `Cache-Control: no-store`, `X-Request-ID` |
| AC-3 | [invariant] A live `core.events.append` while open arrives as the next frame within two `STREAM_POLL_S` intervals | Poll loop reads every `poll_s` | `test_live_event_delivered` (real temp SQLite): frame id = appended `EventId`; at most 2 `EventsRepo.after` calls between the append and the frame |
| AC-4 | [invariant] `: heartbeat` every 15 s with no new events (test clock, no real sleeps) | Heartbeat check after each poll using `StreamTiming.monotonic` | `test_heartbeat_every_15s`: generator driven with a fake clock yields heartbeats at t = 15.0 and 30.0, with 31 reads |
| AC-5 | [invariant] Closes after `chat_closed` and after `demo_reset`, each delivered first | `CLOSING_EVENT_TYPES` stops the generator after that frame | `test_stream_closes_after_chat_closed_and_demo_reset`: last frame type as stated; body ends; a later stored event is not sent |
| AC-6 | [failure/refusal] No session → 401 `UNAUTHENTICATED` (middleware); `thr_9d41`, unknown UUID, another session's thread → identical 404 `SESSION_NOT_FOUND`; no stream starts | `Depends(owned_stream_thread)` before the response object exists | `test_auth_and_ownership`: `assert_matches(response, "streamChatEvents")`; the three 404 bodies equal after `without_request_id`; zero poll reads |
| AC-7 | [failure/refusal] This session's ended thread → 404, equal to an unknown thread's apart from `request_id` | `owned_stream_thread` maps the 410 branch (R-W-3, D-6) | `test_ended_thread_answers_documented_status` |
| AC-8 | [invariant] Polls off the loop, ≤ 4 at once with 6 streams, under the provider's limiter (WEB-19) | `anyio.to_thread.run_sync(…, limiter=<get_stream_poll_limiter()>)` | `test_poll_reads_off_loop_limited_to_4`: max concurrent reads 4; no read on the loop thread; container limiter `borrowed_tokens == 4` while blocked, then 0 |
| AC-9 | [invariant] While `ResetGate.held()`: 200 at once, no poll read; after release, `demo_reset` delivered and the stream closes | `reset_held()` checked before each read; middleware never waits for this operation | `test_reset_gate_skips_polls` |
| AC-10 | [invariant] Disconnect ends the poll loop within one interval and frees the limiter slot | Generator checks `request.is_disconnected()` each iteration and is cancellable; `try/finally` | `test_disconnect_stops_polling[2.3]` and `[2.4]` (both Starlette disconnect paths) |
| AC-11 | [negative] A stored non-`ChatEvent` row (e.g. `case_changed`) is never sent; later frames still arrive | Skip rows whose type ∉ `CHAT_EVENT_TYPES`, but advance `last` past them | `test_only_chat_event_types_sent`: foreign id absent; next event arrives; no later read uses a `last` below the foreign id |
| AC-12 | [negative] Frame carries the stored payload unchanged; logs hold IDs, status and timings only | `chat_event_data` copies the payload; only `stream_reconnect` is logged by the route | `test_frames_equal_stored_and_logs_hold_no_text` (caplog + `captured_log`) |
| AC-13 | [negative] Only read units of work; table row counts unchanged apart from test appends | `uow(write=False)` for every poll; ownership read uses `uow()` (default read) | `test_stream_is_read_only` (temp SQLite, `RecordingUowFactory`) |
| AC-14 | [capture] One `request` record (template, 200, `thread_id`, `caller_role`, `request_id` = `X-Request-ID`); reconnect with 12 → one `stream_reconnect` `{request_id, thread_id, last_event_id: 12, replayed: 2}`; first connect → none | Middleware's record (AEA-23) + route's `emit_record(STREAM_LOGGER, …)` | `tests/api/test_events_capture.py::test_stream_request_and_reconnect_recorded` (real `build_container` via `full_app`) |
| AC-15 | [contract] `tests/contract/cases/events.py` holds the `streamChatEvents` server cases (first connect, resume, 401, 404), frames checked with `assert_sse_frames_match` | Case data file mirroring AEA-23's `auth.py` format | `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k streamChatEvents -rs` **once AEA-59 merges**; until then `tests/api/test_contract_cases_events.py::test_events_cases_drive_documented_statuses` (prints frame counts) |
| AC-16 | [journey] J-9 reconnect replays each missed event once + `stream_reconnect`; J-7 takeover events in order; level stated | `tests/journeys/j9/test_aea_41.py`, `tests/journeys/j7/test_aea_41.py` on `full_app` + harness | `uv run pytest -m journey tests/journeys/j9/test_aea_41.py tests/journeys/j7/test_aea_41.py`; record states **`mock-tested`**, *Blocked by* AEA-57, AEA-51, AEA-52 |
| AC-17 | [regression/context] area map A8, ICM *Routes verified* row, DO-3 §3 Built line | Step 10 | `git diff --name-only main...HEAD` shows the three files, only this ticket's lines |
| PA-1 | A malformed `Last-Event-ID` (`abc`, `-3`, `12abc`, `+5`) never produces an undocumented status; it starts at 0 and writes no `stream_reconnect` | `parse_last_event_id` returns 0 for anything but 1–18 ASCII digits | `test_events.py::test_malformed_last_event_id_starts_at_zero` |
| PA-2 | The heartbeat timer restarts after a frame (OpenAPI "after 15 s without a frame") | `last_sent_at` updated when frames are sent | `test_events.py::test_heartbeat_restarts_after_a_frame` |
| PA-3 | Encoding reproduces the OpenAPI `FRAMES` example byte-for-byte for in-order payloads (the WP pair at unit level) | `encode_event_frame`, `HEARTBEAT_FRAME` | `tests/unit/web/test_events_frames.py::test_frames_match_openapi_example` |
| PA-4 | `parse_last_event_id` table | — | `test_events_frames.py::test_parse_last_event_id` |
| PA-5 | The route's stream key equals AEA-10's `thread_stream(thread_id)` | `thread_stream_key` | `test_events_frames.py::test_thread_stream_key_matches_rows` |
| PA-6 | `register_events` includes the route once (idempotent), provides nothing, docstring keeps "AEA-41", drops "No-op until" | Step 6 | `tests/unit/web/test_register_events.py::test_register_events_includes_the_route_once` |
| S-1 | Only `async def` endpoint; no SQLite on the loop (DO-3 §2.1) | Ownership dep is sync (thread pool); polls via `to_thread` | AC-8 |
| S-2 | Demo-wide events: one stream, never merged (WEB-17) | Reads only `thread_stream_key(thread_id)` | AC-1 (store double asserts the stream string read) |
| S-3 | No `case_created`, no progress events (UXR-10, SDQ-2 = A) | Type allow-list | AC-11 |
| S-4 | No shared SSE helper with CON-21 (DO-3 S-11) | Helpers live in `routes/events.py` / `schemas/events.py` and are documented as CON-3-only | Review |
| S-5 | `x-timing.first_event_ms` 1000 [A] | First poll at t = 0 (no initial sleep) | AC-2 (frames before any sleep); measured at Stage 9 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `GET /api/chat/sessions/{thread_id}/events` (`streamChatEvents`, CON-3) | WF-4 (staff takeover; the chat page of WF-1 opens it) | Yes: DO-6 WF-4 row ("takeover and live chat (CON-14, CON-3 stream)") | Records `request` (middleware), `stream_reconnect` (this route); CAP-4 (AEA-52); EV: none (flags never enter evals unreviewed; this route writes none); M-13, M-27 |

---

## 4. Shared code to use (copied from main `c7ce976`)

**`meridian.web.deps`** (AEA-23):
```python
def owned_stream_thread(thread_id: str, session: LoginSession = Depends(get_login_session),
                        uow: UnitOfWorkFactory = Depends(get_uow_factory)) -> ThreadId
    # malformed (not UUID4) → 404 without lookup; unknown / other session / THIS session's EndedThread → ApiProblem(404, SESSION_NOT_FOUND)
def get_request_context(request: Request) -> RequestContext
def get_uow_factory(request: Request) -> UnitOfWorkFactory
def get_stream_poll_limiter(request: Request) -> anyio.CapacityLimiter      # ONE CapacityLimiter(4) per process
def get_reset_gate(request: Request) -> ResetGate
def get_login_sessions(request: Request) -> LoginSessions                      # tests override
STREAM_POLL_LIMITER: Key[anyio.CapacityLimiter] = Key("stream_poll_limiter")
UOW_FACTORY: Key[UnitOfWorkFactory] = Key("uow_factory")
RESET_GATE: Key[ResetGate] = Key("reset_gate")
STREAM_POLL_THREADS = 4
```
**`meridian.web.middleware`**: `RequestContext(request_id: RequestId, client_ip: str, session: LoginSession | None,
run_tag, run_id, turn_verdict)`; `OPERATIONS_BY_ROUTE[("GET", "/api/chat/sessions/{thread_id}/events")] ==
"streamChatEvents"`; `"streamChatEvents" in RESET_NO_WAIT_OPERATIONS` (middleware never waits or 503s this op); not
rate-limited. The middleware emits the `request` record in its `finally`, i.e. **when the stream ends**, with
`route` = the template, `status` = 200, `thread_id` from the path (only if UUID4), `caller_role` = session role.
**`meridian.web.logging`**: `STREAM_LOGGER = "meridian.web.stream"`; `emit_record(logger_name: str, fields:
Mapping[str, object]) -> None`; allow-list `ALLOWED_FIELDS["stream_reconnect"] == {"record", "request_id",
"thread_id", "case_ref", "last_event_id", "replayed"}`.
**`meridian.services.reset_gate`**: `class ResetGate: def held(self) -> bool` (lock-free; safe on the loop).
**`meridian.web.container`**: `Container`, `Key`, `register_web(container, app, *, settings, limits)`, stub
`register_events(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None`.
**`meridian.web.app`**: `create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None)
-> FastAPI` (lifespan calls `meridian.web.app.build_container(app, settings, overrides=…)`).
**`meridian.ports.runtime`**: `class UnitOfWorkFactory(Protocol): def __call__(self, *, write: bool = False,
exclusive: bool = False) -> AbstractContextManager[UnitOfWork]`; `UnitOfWork.core: CoreRepos` (TYPE_CHECKING
import). A read unit sets `PRAGMA query_only=ON` (`adapters/sqlite/db.py`), so it cannot write.
**`meridian.adapters.sqlite.rows`** (AEA-10; import in **tests** freely, in `src/meridian/web/**` only under
`TYPE_CHECKING`):
```python
StreamKey = NewType("StreamKey", str)
def thread_stream(thread_id: ThreadId) -> StreamKey      # the bare thread id
class StreamEvent(MeridianModel): type: str (1–40); payload: dict[str, JsonValue] = {}; at: datetime   # demo clock
class EventRow(MeridianModel): id: EventId; stream: str; type: str; payload: dict[str, JsonValue]; at: datetime
class ConversationRow(MeridianModel): thread_id: ThreadId; demo_session: str; run_tag: Literal["live","eval","load","seed"];
    agent_version: str; started_at: datetime; …(the rest defaulted)
class EndedThread(MeridianModel): thread_id; demo_session: str; ended_wall_at: datetime; reason: str; reset_id: str | None
```
**Repositories** (`adapters/sqlite/repos_core_aux.py`, `repos_core.py`): `tx.core.events.append(stream: StreamKey,
event: StreamEvent) -> EventId`; `tx.core.events.after(stream: StreamKey, last: EventId) -> list[EventRow]` (`id > last
ORDER BY id`); `tx.core.conversations.insert(row: ConversationRow) -> None`; `tx.commit()`. Payload JSON is stored
with `sort_keys=True`, so a payload read back from SQLite has **sorted** keys.
**`meridian.domain.common`**: `ThreadId` (UUID4 pattern `ThreadId.PATTERN`), `EventId = Annotated[int, Field(ge=0)]`,
`ApiErrorCode.SESSION_NOT_FOUND`, `ApiErrorCode.UNAUTHENTICATED`.
**Tests, `tests/api/openapi_check.py`** (AEA-23): `@dataclass(frozen=True) class SseFrame: event: str | None; id: str
| None; data: str`; `assert_sse_frames_match(frames: Sequence[SseFrame], operation_id: str) -> None`;
`assert_response_matches(response, operation_id: str) -> None` (**do not** call it on a 200 stream: it calls
`.json()`); `load_contract()`, `load_document()`.
**Tests, `tests/api/web_shell_support.py`** (AEA-23, import read-only): `make_settings(tmp_path, **changes) ->
Settings`, `FakeSessionStore` (`.issue(role=DemoRole.CUSTOMER) -> token`, `.session_of(token) -> LoginSession`),
`FakeHeartbeat`, `ConversationRowStub(thread_id, demo_session, live_state="not_live")`, `EndedThreadStub(thread_id,
demo_session, ended_wall_at, reason, reset_id=None)`, `full_app(monkeypatch, settings, *, store, heartbeat,
overrides=None) -> FastAPI` (real `build_container`, starters suppressed), `make_client(app) -> TestClient`,
`cookie_header(token) -> dict`, `error_body(response, status, code) -> dict`, `without_request_id(response) -> dict`,
`assert_matches(response, operation_id)`, `captured_log()` (context manager → `io.StringIO`),
`records_of(stream, kind) -> list[dict]`, `app_log_text(caplog) -> str`, `effective_routes(app) -> list[RouteInfo]`,
`new_thread_id() -> str`.
**Tests, other**: `tests.fixtures.sqlite.temp_sqlite() -> ContextManager[TempStore(data_dir, db_path, issued_path,
uow)]`, `tests.fixtures.sqlite.ISSUED_DB`; `tests.fakes.clock.CHICAGO` (`ZoneInfo("America/Chicago")`).

**Constants to define, verbatim from stage7/web.md §11:**
```python
STREAM_POLL_S = 1.0          # [A] DO-3 S-11; replaced by the measured first_event_ms at Stage 9
STREAM_HEARTBEAT_S = 15      # [Source: OpenAPI streamChatEvents "Heartbeat comment every 15 s (decided 2026-10-21)"]
CHAT_EVENT_TYPES = frozenset({"representative_joined", "staff_message", "ai_paused", "ai_resumed", "chat_closed",
                              "staffing_changed", "shift_ended", "clock_changed", "demo_reset"})   # OpenAPI ChatEvent
```

**Library facts the design relies on (checked in `.venv`):** Starlette 1.9 `StreamingResponse`: with ASGI
`spec_version` < 2.4 (uvicorn 0.54 sends `"2.3"`) it listens for `http.disconnect` and **cancels** the body iterator;
with ≥ 2.4 it does not, so the generator must poll `request.is_disconnected()` itself. `StreamingResponse` with
`media_type="text/event-stream"` sends `content-type: text/event-stream; charset=utf-8`. FastAPI 0.156's own SSE mode
(`fastapi.sse.EventSourceResponse` with a generator endpoint) inserts `: ping` keep-alives on its own wall-clock timer
and orders fields `event/data/id`, so **it is not used**. Starlette 1.9's `TestClient` streams for real and cancels
the app when a `client.stream(...)` block exits.

---

## 5. Steps

Interfaces: this slice **consumes** `owned_stream_thread`, `get_uow_factory`, `get_stream_poll_limiter`,
`get_reset_gate`, `get_request_context` (AEA-23), `UnitOfWorkFactory` / `tx.core.events.after` (DO-4 §13, AEA-10),
`emit_record` + `STREAM_LOGGER` (AEA-23). It **implements** the CON-3 operation. It adds no seam to the design; its one
local dependency, `get_stream_timing`, is private to the route (Risk R-3). Dependency direction: `web/routes/events.py`
→ `web/schemas/events.py`, `web/deps.py`, `web/logging.py`, `ports/runtime.py`, `domain/`; adapters only under
`TYPE_CHECKING`.

### Step 0 — set up

`export UV_LINK_MODE=hardlink`. Work in the orchestrator's worktree on your branch. Run the import check:
`uv run python -c "import meridian.web.app, meridian.web.deps, tests.api.web_shell_support"`. Re-read the A8 row of
`.claude/reference/area-map.md` (it changed today). Run no baseline suite.

### Step 1 — `src/meridian/web/schemas/events.py` (pure, no I/O)

Module docstring: `"""Wire shapes for CON-3 streamChatEvents (OpenAPI ChatEvent; stage7/web.md section 11): which event
types are sent and how one stored events row becomes one SSE frame. CON-3 only: CON-21 keeps its own (DO-3 S-11)."""`

```python
from __future__ import annotations
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Final, Literal, Protocol, get_args
from zoneinfo import ZoneInfo
from pydantic import JsonValue

ChatEventType = Literal["representative_joined", "staff_message", "ai_paused", "ai_resumed", "chat_closed",
                        "staffing_changed", "shift_ended", "clock_changed", "demo_reset"]
CHAT_EVENT_TYPES: Final[frozenset[str]] = frozenset(get_args(ChatEventType))   # == web.md §11 set
CLOSING_EVENT_TYPES: Final[frozenset[str]] = frozenset({"chat_closed", "demo_reset"})
RESERVED_KEYS: Final[tuple[str, ...]] = ("event_id", "type", "at")
HEARTBEAT_FRAME: Final[bytes] = b": heartbeat\n\n"
WIRE_ZONE: Final = ZoneInfo("America/Chicago")

class StoredEvent(Protocol):                 # AEA-10's EventRow satisfies it structurally
    @property
    def id(self) -> int: ...
    @property
    def type(self) -> str: ...
    @property
    def payload(self) -> Mapping[str, JsonValue]: ...
    @property
    def at(self) -> datetime: ...

def chat_event_data(event: StoredEvent) -> dict[str, JsonValue]: ...
def encode_event_frame(event: StoredEvent) -> bytes: ...
```
1. `chat_event_data`: build `{"event_id": event.id, "type": event.type, "at": event.at.astimezone(WIRE_ZONE).isoformat()}`,
   then add every `(key, value)` of `event.payload` **in its stored order** whose key is not in `RESERVED_KEYS`. Never
   change a payload value. *Invariant: the frame carries the stored payload unchanged; the row's id, type and time
   always win over a stray payload key.*
   - **Decision (`at` on the wire):** `at` is the demo clock (DO-4 `Clock`: America/Chicago). It is stored UTC
     (cases.md §1.1, MC-20) and sent with the Chicago offset, as the OpenAPI example (`-05:00`) and AEA-30's
     `clock_changed.demo_clock.now` do. It is the same instant either way and valid `date-time`.
2. `encode_event_frame`: `data = json.dumps(chat_event_data(event), ensure_ascii=False, separators=(",", ":"))`;
   return `f"id: {event.id}\nevent: {event.type}\ndata: {data}\n\n".encode("utf-8")`. *Invariant: `json.dumps` escapes
   newlines, so `data:` is one line; field order id/event/data matches the OpenAPI example.*

### Step 2 — `src/meridian/web/routes/events.py`: constants, timing, helpers

Module docstring: `"""CON-3 streamChatEvents (stage7/web.md section 11): one async SSE route that polls this thread's
events stream off the event loop, replays from Last-Event-ID, sends a heartbeat comment and closes after chat_closed or
demo_reset. Reads only; writes no row and no event."""`

```python
STREAM_POLL_S: Final = 1.0          # [A] DO-3 S-11; replaced by the measured first_event_ms at Stage 9
STREAM_HEARTBEAT_S: Final = 15      # [Source: OpenAPI streamChatEvents "Heartbeat comment every 15 s (decided 2026-10-21)"]
EVENTS_PATH: Final = "/api/chat/sessions/{thread_id}/events"
OPERATION_ID: Final = "streamChatEvents"
LAST_EVENT_ID_HEADER: Final = "last-event-id"
MAX_EVENT_ID_DIGITS: Final = 18

@dataclass(frozen=True)
class StreamTiming:
    """How long the loop sleeps and how it reads time; tests override get_stream_timing."""
    poll_s: float = STREAM_POLL_S
    heartbeat_s: float = STREAM_HEARTBEAT_S
    sleep: Callable[[float], Awaitable[None]] = anyio.sleep
    monotonic: Callable[[], float] = time.monotonic

def get_stream_timing() -> StreamTiming: return StreamTiming()
def parse_last_event_id(raw: str | None) -> int: ...
def thread_stream_key(thread_id: ThreadId) -> StreamKey: ...
def read_events_after(uow: UnitOfWorkFactory, stream: StreamKey, last: int) -> list[EventRow]: ...
```
Imports at runtime: `anyio`, `functools`, `time`, `dataclasses.dataclass`, `collections.abc` (`AsyncIterator`,
`Awaitable`, `Callable`, `Sequence`), `typing` (`TYPE_CHECKING`, `Final`, `cast`), `fastapi` (`APIRouter`, `Depends`,
`Request`), `starlette.responses.StreamingResponse`, `meridian.domain.common.ThreadId`,
`meridian.ports.runtime.UnitOfWorkFactory`, `meridian.services.reset_gate.ResetGate`,
`meridian.web.deps` (`get_request_context`, `get_reset_gate`, `get_stream_poll_limiter`, `get_uow_factory`,
`owned_stream_thread`), `meridian.web.logging` (`STREAM_LOGGER`, `emit_record`),
`meridian.web.middleware.RequestContext`, `meridian.web.schemas.events` (the Step 1 names). Under `if TYPE_CHECKING:`
only: `from meridian.adapters.sqlite.rows import EventRow, StreamKey`.

1. `parse_last_event_id(raw)`: `None` → 0. Otherwise `value = raw.strip()`; if `value.isascii() and value.isdigit()
   and 1 <= len(value) <= MAX_EVENT_ID_DIGITS` → `int(value)`, else **0**. *Invariant: a bad header never yields a
   status the operation does not document (only 200/401/404). Replay from 0 is safe because the screen de-duplicates
   by event id (web.md §11).*
2. `thread_stream_key(thread_id)`: `return cast("StreamKey", str(thread_id))`. It must equal
   `meridian.adapters.sqlite.rows.thread_stream(thread_id)` (PA-5 proves it). *Keeps adapters out of `web/` at run
   time, like `web/deps.py`.*
3. `read_events_after(uow, stream, last)`: `with uow(write=False) as tx: return tx.core.events.after(stream, last)`.
   This is a sync function that runs on a worker thread. It opens a read unit only (AC-13).

### Step 3 — the poll loop (`chat_event_frames`)

```python
async def chat_event_frames(
    *,
    start: int,
    read_after: Callable[[int], Awaitable[Sequence[StoredEvent]]],
    reset_held: Callable[[], bool],
    disconnected: Callable[[], Awaitable[bool]],
    timing: StreamTiming,
    on_replayed: Callable[[int], None] | None,
) -> AsyncIterator[bytes]:
```
Numbered algorithm. Write it exactly in this order:

1. `last = start`; `reported = on_replayed is None`; `last_sent_at = timing.monotonic()`.
2. Wrap steps 3–9 in `try:` … `finally:` (step 10).
3. Loop `while True:`.
4. `if await disconnected(): return`. *Invariant: on ASGI ≥ 2.4 servers nothing else stops the loop; ends polling
   within one interval (AC-10).*
5. `if not reset_held():` do steps 6–8. Otherwise skip to step 9. *Invariant: while a reset holds the gate, no read
   touches SQLite and the stream neither waits nor refuses (web.md §7; AC-9).*
6. `rows = await read_after(last)`. Then build `frames: list[bytes] = []` and `closing = False`. For each `row` in
   `rows`, in order:
   1. `last = row.id`. *Invariant: `last` moves past every row read, including skipped ones, so no row is read twice.*
   2. `if row.type not in CHAT_EVENT_TYPES: continue`. *Only the nine types are sent (AC-11).*
   3. `frames.append(encode_event_frame(row))`.
   4. `if row.type in CLOSING_EVENT_TYPES: closing = True; break`.
7. `if not reported: reported = True; on_replayed(len(frames))`. The type checker needs `assert on_replayed is not
   None` or an `if on_replayed is not None` guard; use the guard. *`replayed` = frames produced by the first completed
   read; exactly one record per reconnect (WEB-18).*
8. `for frame in frames: yield frame`. `if frames: last_sent_at = timing.monotonic()`. `if closing: return`.
   *Invariant: `chat_closed` / `demo_reset` is delivered, then the stream ends (AC-5).*
9. `if timing.monotonic() - last_sent_at >= timing.heartbeat_s: yield HEARTBEAT_FRAME; last_sent_at =
   timing.monotonic()`. Then `await timing.sleep(timing.poll_s)`. *Heartbeat after 15 s without a frame (AC-4, PA-2).
   The first read happens at t = 0 with no initial sleep (`first_event_ms`).*
10. `finally:` `if not reported and on_replayed is not None: on_replayed(0)`. *A reconnect that ends before its first
    read (cancelled or held) still leaves exactly one record.* Put no `await` in this `finally`.

Do not catch exceptions in the loop. A failing read ends the stream, and the browser reconnects with its last id
(R-7). `CancelledError` (Starlette < 2.4 disconnect) must propagate.

### Step 4 — the endpoint and router

```python
async def stream_chat_events(
    request: Request,
    owned: ThreadId = Depends(owned_stream_thread),  # noqa: B008
    context: RequestContext = Depends(get_request_context),  # noqa: B008
    uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
    limiter: anyio.CapacityLimiter = Depends(get_stream_poll_limiter),  # noqa: B008
    gate: ResetGate = Depends(get_reset_gate),  # noqa: B008
    timing: StreamTiming = Depends(get_stream_timing),  # noqa: B008
) -> StreamingResponse:

def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(EVENTS_PATH, stream_chat_events, methods=["GET"], operation_id=OPERATION_ID,
                         response_model=None)
    return router
```
1. Ownership runs first as a dependency. A refusal raises `ApiProblem` (404) before any response object exists, so no
   stream starts (AC-6, AC-7). The parameter is named `owned`, **not** `thread_id`, so the path parameter stays the
   dependency's.
2. `start = parse_last_event_id(request.headers.get(LAST_EVENT_ID_HEADER))`.
3. `stream = thread_stream_key(owned)`.
4. Inner `async def read_after(last: int) -> Sequence[StoredEvent]: return await anyio.to_thread.run_sync(
   functools.partial(read_events_after, uow, stream, last), limiter=limiter)`. Use the default
   `abandon_on_cancel=False`, so a cancelled stream waits for its read to finish and **returns its limiter token**
   (AC-10). *Invariant: every poll read runs on a worker thread under the one process-wide limiter (AC-8, WEB-19).*
5. `on_replayed`: if `start > 0`, a closure `def record(replayed: int) -> None: emit_record(STREAM_LOGGER,
   {"record": "stream_reconnect", "request_id": str(context.request_id), "thread_id": str(owned), "last_event_id":
   start, "replayed": replayed})`; else `None`. *IDs and counts only (DO-6 Content and redaction).*
6. `return StreamingResponse(chat_event_frames(start=start, read_after=read_after, reset_held=gate.held,
   disconnected=request.is_disconnected, timing=timing, on_replayed=record_or_none), media_type="text/event-stream",
   headers={"Cache-Control": "no-store"})`. `X-Request-ID` is added by the middleware.

### Step 5 — run the unit-level checks while iterating

Write `tests/unit/web/test_events_frames.py` (Step 8) first and run it. It needs no app.

### Step 6 — `register_events` hunk in `src/meridian/web/container.py` (only this function)

```python
def register_events(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-41 customer API: the CON-3 event stream route (web.md §11).

    Includes routes/events.py's router once per app. Provides nothing: the route reads AEA-10's unit of work and
    AEA-23's stream limiter and reset gate through web/deps.py.
    """
    from meridian.web.routes.events import build_router

    if getattr(app.state, "events_router_included", False):
        return
    app.include_router(build_router())
    app.state.events_router_included = True
```
Rules: the import stays **inside** the function (`tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`
checks module-level imports). The docstring keeps "AEA-41" and must not contain "No-op until"
(`tests/unit/web/test_container.py::test_every_register_stub_present`). Change no other line of the file.

### Step 7 — `tests/api/events_support.py` (test support; not a conftest)

Docstring: AEA-41 test support (doubles, an in-process ASGI stream harness, seed helpers, payload fixtures). It is
synthetic and needs no socket, `.env` or paid call. Other tickets may import it read-only. Contents, with exact
names:

**Payload fixtures** (copied from the OpenAPI `FRAMES` example and `Ev*` descriptions; key order as written):
```python
WP2_JOINED_AT = datetime(2026, 10, 16, 14, 22, tzinfo=CHICAGO)
WP2_MESSAGE_AT = datetime(2026, 10, 16, 14, 22, 40, tzinfo=CHICAGO)
STAFF_TEXT = "Hi Omar, I can look at the after-hours charge with you."
EVENT_SPEAKER = {"kind": "event", "display_name": None}
RILEY = {"kind": "representative", "display_name": "Riley"}
PAYLOADS: dict[str, dict[str, JsonValue]] = {
  "representative_joined": {"speaker": RILEY, "display_name": "Riley", "line": "Riley (demo representative) has joined."},
  "ai_paused": {"speaker": EVENT_SPEAKER, "line": "The assistant is paused while Riley is here."},
  "staff_message": {"speaker": RILEY, "message_id": "m-88", "text": STAFF_TEXT},
  "ai_resumed": {"speaker": EVENT_SPEAKER, "line": "Riley handed the chat back to the automated assistant."},
  "chat_closed": {"speaker": EVENT_SPEAKER, "line": "Riley closed this chat.", "composer_disabled": True},
  "demo_reset": {"speaker": EVENT_SPEAKER, "line": "The demo was reset, so this chat has ended. Nothing from it was kept."},
  "case_changed": {},          # a CaseEvent type: never sent on CON-3 (AC-11)
}
def payload(event_type: str) -> dict[str, JsonValue]   # a deep copy (copy.deepcopy) of PAYLOADS[event_type]
```
**Timing doubles:**
```python
FAST_TIMING = StreamTiming(poll_s=0.01, heartbeat_s=3600.0)
class FakeMonotonic:                    # a test clock: sleep() advances it, never sleeps for real
    now: float = 0.0
    def monotonic(self) -> float
    async def sleep(self, seconds: float) -> None   # self.now += seconds; await anyio.lowlevel.checkpoint()
    def timing(self) -> StreamTiming                # StreamTiming(sleep=self.sleep, monotonic=self.monotonic) with the module defaults
```
**Store doubles:**
```python
@dataclass(frozen=True)
class ReadCall: stream: str; last: int; thread: int          # thread = threading.get_ident() of the reading thread

class FakeStreamStore:
    """UnitOfWorkFactory double: tx.core.conversations.lookup from `rows`; tx.core.events.after over an in-memory list."""
    def __init__(self, rows: Mapping[str, object] | None = None) -> None
    rows: dict[str, object]; events: list[EventRow]; write_flags: list[bool]; reads: list[ReadCall]
    active_reads: int; max_active_reads: int
    hold_reads: threading.Event | None        # when set to an Event, after() waits on it (timeout 5 s) while counted active
    def append(self, stream: str, event_type: str, data: dict[str, JsonValue], *, at: datetime = WP2_JOINED_AT,
               event_id: int | None = None) -> int     # id = event_id or (max id + 1, starting at 1); returns it
    def after(self, stream: str, last: int) -> list[EventRow]   # under a threading.Lock: record ReadCall, bump active/max;
                                                               # wait on hold_reads if set; return rows with stream == stream
                                                               # and id > last, sorted by id; finally decrement active
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[Any]
        # appends (write or exclusive) to write_flags; yields an object `tx` with tx.core.conversations.lookup(thread_id)
        # → rows.get(thread_id) and tx.core.events.after(stream, last) → self.after(str(stream), last)

class RecordingUowFactory:              # wraps a real SqliteUnitOfWorkFactory
    def __init__(self, inner: UnitOfWorkFactory) -> None
    write_flags: list[bool]
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[Any]
        # write_flags.append(write or exclusive); return self.inner(write=write, exclusive=exclusive)

class FlagGate:                         # ResetGate double for AC-9
    flag: bool = False
    def held(self) -> bool
```
**Real-SQLite helpers:**
```python
def seed_conversation(uow: UnitOfWorkFactory, session_id: str, *, thread_id: str | None = None) -> str
    # one write unit: tx.core.conversations.insert(ConversationRow(thread_id=ThreadId(tid), demo_session=session_id,
    #   run_tag="live", agent_version="test-agent-0", started_at=WP2_JOINED_AT)); tx.commit(); returns tid
def append_stored(uow: UnitOfWorkFactory, stream: str, items: Sequence[tuple[str, dict[str, JsonValue]]],
                  *, at: datetime = WP2_JOINED_AT) -> list[int]
    # one write unit: tx.core.events.append(StreamKey(stream), StreamEvent(type=t, payload=p, at=at)) per item; commit; ids
def table_counts(db_path: Path) -> dict[str, int]
    # sqlite3 connect (read only, `file:{db_path}?mode=ro`, uri=True); COUNT(*) for every name in
    # SELECT name FROM sqlite_master WHERE type='table'; close in finally
def count_event_reads(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]
    # wraps meridian.adapters.sqlite.repos_core_aux.EventsRepo.after with monkeypatch.setattr so each call
    # appends (str(stream), last) and then calls the original
```
**App builders:**
```python
def install_events_builder(monkeypatch: pytest.MonkeyPatch) -> None
    # monkeypatch meridian.web.app.build_container with a builder that makes Container(settings, Limits()), runs
    # register_web then register_events, calls container.build(), returns it (no other hunk)
def events_app(monkeypatch, settings, *, uow: object, store: FakeSessionStore, gate: object | None = None,
               timing: StreamTiming = FAST_TIMING) -> FastAPI
    # install_events_builder; app = create_app(settings); dependency_overrides: get_login_sessions → store,
    # get_uow_factory → uow, get_stream_timing → timing, and get_reset_gate → gate when given (zero-argument lambdas,
    # the middleware's `provided` honours them); app.state.test_store = store; return app
def full_stream_app(monkeypatch, tmp_path: Path, *, store: FakeSessionStore, timing: StreamTiming = FAST_TIMING) -> FastAPI
    # settings = make_settings(tmp_path, issued_db_path=ISSUED_DB); app = full_app(monkeypatch, settings, store=store,
    # heartbeat=FakeHeartbeat()); app.dependency_overrides[get_stream_timing] = lambda: timing; return app
```
**In-process ASGI stream harness.** All waits are bounded by `anyio.fail_after`. It binds no port.
```python
@dataclass
class StreamHandle:
    status: int | None; headers: dict[str, str]            # header names lower-cased
    started: anyio.Event; disconnect: anyio.Event; done: anyio.Event
    chunks: MemoryObjectReceiveStream[bytes]; buffer: str = ""; request_sent: bool = False

@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[TaskGroup]
    # async with app.router.lifespan_context(app): async with anyio.create_task_group() as tg: yield tg;
    # then tg.cancel_scope.cancel(). (Fallback if lifespan_context is unusable: drive the ASGI lifespan protocol in a
    # task: send {"type": "lifespan.startup"}, wait for "lifespan.startup.complete", and at exit "lifespan.shutdown".)

async def open_stream(tg: TaskGroup, app: FastAPI, thread_id: str, *, token: str | None,
                      last_event_id: str | None = None, spec_version: str = "2.3", timeout: float = 2.0) -> StreamHandle
    # scope: {"type": "http", "asgi": {"version": "3.0", "spec_version": spec_version}, "http_version": "1.1",
    #   "method": "GET", "scheme": "http", "path": f"/api/chat/sessions/{thread_id}/events", "raw_path": <bytes>,
    #   "root_path": "", "query_string": b"", "headers": [(b"host", b"testserver"), cookie if token,
    #   (b"last-event-id", value) if given], "client": ("198.51.100.7", 50000), "server": ("testserver", 80), "state": {}}
    # receive(): first call → {"type": "http.request", "body": b"", "more_body": False}; later: if disconnect.is_set()
    #   return {"type": "http.disconnect"} AT ONCE (no checkpoint, like uvicorn), else await disconnect.wait() and
    #   return it.
    # send(): http.response.start → status, headers, started.set(); http.response.body → push body bytes (if any) into
    #   an unbounded memory stream; more_body False → close the send side.
    # tg.start_soon(run) where run awaits app(scope, receive, send), then closes the send side and sets done.
    # Wait for `started` under fail_after(timeout); return the handle.

async def next_item(handle: StreamHandle, *, timeout: float = 2.0) -> SseFrame | str | None
    # Parse blocks separated by "\n\n" from handle.buffer, receiving more chunks under fail_after(timeout).
    # A block whose lines all start with ":" → return the comment text (": heartbeat" → "heartbeat").
    # Otherwise → SseFrame(event=<event: value or None>, id=<id: value or None>, data=<data: lines joined by "\n">).
    # End of body with an empty buffer → None.
async def read_frames(handle: StreamHandle, count: int, *, timeout: float = 2.0) -> list[SseFrame]
    # next_item until `count` SseFrames (comments skipped); fails if the body ends first
async def close_stream(handle: StreamHandle, *, timeout: float = 2.0) -> None
    # handle.disconnect.set(); wait for handle.done under fail_after(timeout)
def parse_sse_text(text: str) -> list[SseFrame | str]     # the same parser over a whole body (TestClient bodies)
def frame_ids(frames: Sequence[SseFrame]) -> list[int]
def session_of(store: FakeSessionStore, token: str) -> str   # str(store.session_of(token).session_id)
```
Every async test is a plain sync `def test_…()` that calls `anyio.run(scenario)`. No pytest anyio plugin, no new
marker.

### Step 8 — tests (write with the code; each test has a one-line docstring `"<kind> (AC-n): …"`)

**`tests/unit/web/test_events_frames.py`**
- `test_frames_match_openapi_example` (PA-3): build three `EventRow`s directly (ids 12, 13, 14; types
  `representative_joined`, `ai_paused`, `staff_message`; payloads `payload(...)`; `at` `WP2_JOINED_AT`,
  `WP2_JOINED_AT`, `WP2_MESSAGE_AT`; `stream` = any UUID). Then
  `(b"".join(encode_event_frame(r) for r in rows) + HEARTBEAT_FRAME).decode().rstrip("\n")` must equal
  `load_document()["paths"]["/api/chat/sessions/{thread_id}/events"]["get"]["responses"]["200"]["content"]["text/event-stream"]["examples"]["FRAMES"]["value"].rstrip("\n")`.
- `test_chat_event_data_adds_id_type_at_and_keeps_payload`: payload with a stray `"type": "x"` key → the row's type
  wins; other payload values identical; `at` with offset `-05:00`; a `datetime` stored in UTC converts to the same
  instant.
- `test_parse_last_event_id` (PA-4): `None→0`, `"12"→12`, `" 12 "→12`, `"0"→0`, `"abc"→0`, `"-3"→0`, `"+5"→0`,
  `"12abc"→0`, `"1"*19→0`, `"１２"` (full-width) `→0`.
- `test_thread_stream_key_matches_rows` (PA-5): `thread_stream_key(ThreadId(t)) == thread_stream(ThreadId(t))`.

**`tests/unit/web/test_register_events.py`**
- `test_register_events_includes_the_route_once` (PA-6): `app = FastAPI()`, `c = Container(settings=SimpleNamespace(),
  limits=Limits())`, call `register_events` twice, `c.build()`. Assert exactly one `effective_routes(app)` entry with path
  `EVENTS_PATH`, methods `{"GET"}` and `operation_id == "streamChatEvents"`; `not c._factories`; the docstring contains
  "AEA-41" and not "No-op until".

**`tests/api/test_events.py`** (settings: `make_settings(tmp_path)`; customer token `store.issue()`; thread owned via
`ConversationRowStub(thread_id, session_of(store, token))` in `FakeStreamStore(rows=…)`, unless real SQLite is named)
- `test_replay_after_last_event_id` (AC-1): store events 12, 13, 14 (the WP-2 trio, explicit `event_id`s, stream =
  thread id). Run `captured_log()` around `anyio.run`. Open with `last_event_id="12"`, `read_frames(h, 2)`,
  `close_stream`. Assert: `frame_ids == [13, 14]`; `assert_sse_frames_match(frames, "streamChatEvents")`; each
  `frame.data` equals the example's `data:` line for that id; `store.reads[0] == ReadCall(stream=thread_id, last=12,
  …)`; `records_of(log, "stream_reconnect") == [{"record": "stream_reconnect", "request_id": h.headers["x-request-id"],
  "thread_id": thread_id, "last_event_id": 12, "replayed": 2}]` (the formatter sorts keys and drops `case_ref`, so
  compare dicts).
- `test_first_connect_replays_from_zero` (AC-2): two events (`representative_joined`, `ai_paused`), no header →
  `frame_ids == [1, 2]`; `h.status == 200`; `h.headers["content-type"].split(";")[0] == "text/event-stream"`;
  `h.headers["cache-control"] == "no-store"`; `x-request-id` matches `ThreadId.PATTERN` (UUID4); no `stream_reconnect`
  record.
- `test_live_event_delivered` (AC-3): `temp_sqlite()` store. `seed_conversation(store.uow, session_id)`, then
  `reads = count_event_reads(monkeypatch)` and `events_app(…, uow=store.uow)`. Open (no header) and read nothing yet.
  Wait until `len(reads) >= 1`. Note `n0 = len(reads)`. `[eid] = append_stored(store.uow, tid,
  [("staff_message", payload("staff_message"))])`. `[frame] = await read_frames(h, 1)`. Assert `frame.id ==
  str(eid)` and `len(reads) - n0 <= 2`.
- `test_heartbeat_every_15s` (AC-4): no app. `clock = FakeMonotonic()`, `reads: list[int] = []`, `read_after` returns
  `[]` and appends `last`, `disconnected` returns False, `reset_held` returns False. Drive
  `chat_event_frames(start=0, …, timing=clock.timing(), on_replayed=None)`; collect `(clock.now, chunk)` until two
  chunks; `await gen.aclose()`. Assert `== [(15.0, HEARTBEAT_FRAME), (30.0, HEARTBEAT_FRAME)]` and `len(reads) ==
  31`. No real sleep is allowed anywhere in this test.
- `test_heartbeat_restarts_after_a_frame` (PA-2): as above, but `read_after` returns one `EventRow` (`ai_paused`, id
  1) when `clock.now == 10.0` and `[]` otherwise. Expected chunks: the frame at 10.0, then a heartbeat at 25.0.
- `test_stream_closes_after_chat_closed_and_demo_reset` (AC-5): for `closer` in `("chat_closed", "demo_reset")` use a
  fresh store and app: `representative_joined` (1), `closer` (2), `staff_message` (3). Read items until `next_item`
  returns `None`. Assert frame types `["representative_joined", closer]`, `3` is absent, and `h.done` is set within 2 s
  without `close_stream`.
- `test_auth_and_ownership` (AC-6): `FakeStreamStore` with one event on every thread used. TestClient
  (`with make_client(app) as client`): no cookie → `error_body(r, 401, "UNAUTHENTICATED")`, `assert_matches(r,
  "streamChatEvents")`. With the cookie: `thr_9d41`, a fresh `new_thread_id()`, and a thread owned by another session
  (`ConversationRowStub(other, "another-session-id")`) → each `error_body(r, 404, "SESSION_NOT_FOUND")` +
  `assert_matches`. The three `without_request_id(r)` are equal. `store.reads == []`.
- `test_ended_thread_answers_documented_status` (AC-7): `EndedThreadStub(tid, session_id,
  "2026-10-16T15:00:00+00:00", "demo_reset")` → 404 `SESSION_NOT_FOUND`, `assert_matches`; equal to an unknown thread's
  body apart from `request_id`; `store.reads == []`.
- `test_poll_reads_off_loop_limited_to_4` (AC-8): six owned threads, each with one event. Set
  `store.hold_reads = threading.Event()`. In the scenario: `loop_thread = threading.get_ident()`; `lim =
  app.state.container.get(STREAM_POLL_LIMITER)` (the provider's one instance, **not** overridden). Open six streams.
  Wait (≤ 3 s) until `store.active_reads == 4`, `await anyio.sleep(0.1)`, then assert `store.active_reads == 4` and
  `lim.borrowed_tokens == 4`. `store.hold_reads.set()`, read one frame from each stream, close all. Assert
  `store.max_active_reads == 4`, `all(r.thread != loop_thread for r in store.reads)`, `lim.borrowed_tokens == 0`,
  `lim.total_tokens == 4`.
- `test_reset_gate_skips_polls` (AC-9): `gate = FlagGate(); gate.flag = True` passed to `events_app(gate=gate)`. Open
  the stream; assert `h.status == 200` right away. `await anyio.sleep(0.1)` (≈ 10 poll intervals), then `store.reads ==
  []`. `store.append(tid, "demo_reset", payload("demo_reset"))`, `gate.flag = False`. Assert the next frame is type
  `demo_reset`, `next_item` returns `None`, and `h.done` is set.
- `test_disconnect_stops_polling` (AC-10), `@pytest.mark.parametrize("spec_version", ["2.3", "2.4"])`: `lim` from the
  container, `before = lim.borrowed_tokens`. Open, wait until `len(store.reads) >= 2`, `n = len(store.reads)`,
  `close_stream(h, timeout=1.0)`, then `await anyio.sleep(0.05)`. Assert `len(store.reads) - n <= 1`,
  `lim.borrowed_tokens == before`, `h.done.is_set()`.
- `test_only_chat_event_types_sent` (AC-11): events `representative_joined` (1), `case_changed` (2), `ai_paused` (3).
  `frame_ids == [1, 3]`. Every `ReadCall` after the first has `last >= 3`.
- `test_frames_equal_stored_and_logs_hold_no_text` (AC-12, `caplog` at INFO): real `temp_sqlite()`. Seed the WP-2 trio
  through `append_stored` and reconnect with the first id. For each frame: `data = json.loads(frame.data)`;
  `{k: v for k, v in data.items() if k not in RESERVED_KEYS}` equals the stored payload read back with
  `tx.core.events.after(…)`; `datetime.fromisoformat(data["at"]) == row.at`. `STAFF_TEXT` is in a frame. It is not in
  `app_log_text(caplog)`, not in any `repr(r.__dict__)` of `caplog.records` whose name starts with `meridian`, and not in
  the `captured_log()` text.
- `test_stream_is_read_only` (AC-13): `temp_sqlite()`. Seed a conversation and two events first. Take `before =
  table_counts(store.db_path)`. With `uow = RecordingUowFactory(store.uow)`: replay from 0 (read 2, close); open again
  from 0, `append_stored(store.uow, tid, [("ai_resumed", …)])` (the test's own write, not through `uow`), read 3 frames,
  close; reconnect with header `"2"`, read 1, close. Assert `uow.write_flags` is non-empty and all `False`, and
  `table_counts(store.db_path) == {**before, "events": before["events"] + 1}`.
- `test_malformed_last_event_id_starts_at_zero` (PA-1): for each of `"abc"`, `"-3"`, `"12abc"`: two events → frames
  `[1, 2]`; no `stream_reconnect` record.

**`tests/api/test_events_capture.py`**
- `test_stream_request_and_reconnect_recorded` (AC-14): `full_stream_app(monkeypatch, tmp_path, store=store)` (real
  `build_container`, real storage, `register_events` from the real hunk). Inside `running(app)`: `uow =
  app.state.container.get(UOW_FACTORY)`. `seed_conversation(uow, session_id)`. `append_stored` 11 `case_changed` rows
  on another thread's stream (ids 1–11), then the WP-2 trio on Omar's thread → ids 12, 13, 14 (assert this). Inside
  `captured_log()`: open with `"12"`, read 2 frames, close; then open with no header, read 3 frames, close. Then
  `requests = records_of(log, "request")` has 2 entries. Each has `route == EVENTS_PATH`, `status == 200`, `thread_id
  == tid`, `caller_role == "customer"`, and `request_id ==` that stream's `x-request-id` header.
  `records_of(log, "stream_reconnect") == [{"record": "stream_reconnect", "request_id": <first stream's id>,
  "thread_id": tid, "last_event_id": 12, "replayed": 2}]`.

**`tests/contract/cases/events.py`** (AC-15), same shape as AEA-23's `tests/contract/cases/auth.py`:
```python
"""Server contract cases for CON-3 (`streamChatEvents`), owned by AEA-41 (AC-15, AEA-41-1).

Read by AEA-59's runner (tests/contract/test_openapi_server.py); until it lands, tests/api/test_contract_cases_events.py
drives them. Vocabulary (closed):
  preconditions: "login" = sign in and keep the cookie; "started_thread" = a conversations row owned by this login session.
  thread: "started" (the precondition's thread), "unknown" (a fresh UUID4) or a literal path segment ("thr_9d41").
  events: ChatEvent types appended in order to the started thread's stream, payloads from the OpenAPI Ev* examples.
  last_event_id: None sends no header; {"after_event": n} sends the id of the n-th appended event (1-based).
  frames: the number of SSE frames expected; every 200 case ends on chat_closed, so a runner can read to the end.
"""
ROUTE_FILE: Final = "events"
_TAKEOVER: Final = ("representative_joined", "ai_paused", "staff_message", "chat_closed")
CASES: Final[dict[str, dict[str, object]]] = {"streamChatEvents": {"public": False, "drives": (
    {"name": "first_connect", "status": 200, "preconditions": ("login", "started_thread"), "thread": "started",
     "events": _TAKEOVER, "last_event_id": None, "frames": 4},
    {"name": "resume", "status": 200, "preconditions": ("login", "started_thread"), "thread": "started",
     "events": _TAKEOVER, "last_event_id": {"after_event": 2}, "frames": 2},
    {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (), "thread": "unknown"},
    {"name": "unknown_thread", "status": 404, "code": "SESSION_NOT_FOUND", "preconditions": ("login",), "thread": "unknown"},
    {"name": "malformed_thread", "status": 404, "code": "SESSION_NOT_FOUND", "preconditions": ("login",), "thread": "thr_9d41"},
)}}
```
**`tests/api/test_contract_cases_events.py`**
- `test_events_cases_drive_documented_statuses` (AC-15 local driver): for each case build a fresh `events_app` on
  `FakeStreamStore` and use TestClient `client.get(...)`, which works because every 200 case closes. Apply the
  preconditions, seed the events, and send the header. For 200: `parse_sse_text(r.text)` frames count ==
  `case["frames"]`, `assert_sse_frames_match`, `cache-control == "no-store"`. For errors: `error_body(r, status, code)`
  + `assert_matches`. Also assert that the set of statuses covered == `set(load_contract().operations["streamChatEvents"].responses)`
  (`{"200", "401", "404"}`) and `ROUTE_FILE == "events"`, and print `"<name>: <status>, frames=<n>"` per case.

**`tests/journeys/j9/test_aea_41.py`** (`pytestmark = pytest.mark.journey`; module docstring states level
`mock-tested` and *Blocked by* AEA-57, AEA-51, AEA-52, as in `j9/test_aea_26.py`)
- `test_j9_reconnect_replays_each_missed_event_once`: `full_stream_app` with real storage. Seed `representative_joined`,
  `ai_paused`, `staff_message`. Connection 1 (no header) reads **one** frame, then the browser drops (close). Connection
  2 sends that frame's id and reads 2 frames. The test then appends `ai_resumed` live and reads 1 more frame. User sees:
  the ids across both connections are each stored id exactly once, in increasing order, and the `line`/`text` values
  equal the stored payloads. Stored: `events` rows on the thread stream are exactly the 4 the test wrote (via
  `tx.core.events.after(stream, 0)`), and one `stream_reconnect` record with `replayed == 2`.

**`tests/journeys/j7/test_aea_41.py`** (same marker and docstring pattern)
- `test_j7_takeover_events_reach_customer_stream_in_order`: seed the takeover sequence `representative_joined`,
  `ai_paused`, `staff_message`, `ai_resumed` (standing in for AEA-46's writers). The customer stream (no header) shows
  those four types in that order, with Riley's speaker on joined and message and `STAFF_TEXT` as the message text.
  Stored rows are unchanged after the read (`table_counts` before/after equal).

### Step 9 — evidence record `docs/testing/journeys/<build date>-AEA-41.md`

Use the AEA-26 record's table. **Claim:** CON-3 stream (AC-1…AC-15); J-9 reconnect replay + `stream_reconnect`; J-7
takeover order. **Level:** `mock-tested` (real app factory, middleware and SQLite copy; session store double; no
journey harness; events seeded by the test, not by the real writers). **Tested revision:** your commit SHA, or
"uncommitted" if you write it before committing. **Environment:** VPS, Python 3.12, `uv`; in-process ASGI (no socket);
temp SQLite from `tests/fixtures/sqlite.py`; no model adapter. **Command:** the Step 7 commands of §7. **Result:** pass
counts from your run. **Remaining limitations:** no real writer (AEA-29/30/31/46), no browser, no server in a thread.
**Blocked by:** AEA-57 (harness), AEA-51 (integrated turn), AEA-52 (real takeover writers, CAP-4). **Journeys that will
exercise this code:** J-7, J-9; J-1 (the page opens the stream on every chat).

### Step 10 — context rows (AC-17; only this ticket's lines)

1. `.claude/reference/area-map.md`, A8 row, last cell: append `; AEA-41 (branch <your branch>): web/routes/events.py,
   web/schemas/events.py` inside the existing "partly built: …" text. Change nothing else in the file. If the cell has
   changed since you read it, append to whatever is there.
2. `.claude/state/icm-progress.md`: add one row under the existing *Routes verified against code and tests* rows:
   `| Routes verified against code and tests | provisional | <date>: area map A8 → web/routes/events.py, web/schemas/events.py checked against tests/api/test_events.py, test_events_capture.py, tests/unit/web/test_events_frames.py (AEA-41, branch <your branch>; <N> pass) | Each slice adds its route; verified when every area-map row is actual |`
   (≤ 400 characters).
3. `docs/design/code-design.md` §3: add one line after the AEA-23 `**Built:**` line:
   `**Built:** web/routes/events.py, web/schemas/events.py (AEA-41, branch <your branch>).` with the paths in
   backticks. The merge step replaces the branch with the SHA, as for AEA-23.

### Step 11 — gates, commit

Run §7 (cheapest first). Then `git add` **each owned path explicitly** (never `-A`), and commit on your branch with a
message such as `feat(web): CON-3 chat event stream with replay, heartbeat and shared poll limiter (AEA-41)`. The last
line must be `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push and do not merge.

### What the implementer must NOT do

- Edit `web/{app,deps,middleware,logging,errors}.py`, `routes/auth.py`, `tests/api/{openapi_check,web_shell_support}.py`,
  any `adapters/sqlite/*`, `tests/fixtures/sqlite.py`, `tests/fakes/*`, `tests/conftest.py`, `pyproject.toml`, `uv.lock`,
  the OpenAPI, `UI_CONTRACTS.md`, `docs/ux/**`, `apps/web/**`, the briefing, issued data, `docs/archive/`, `docs/parked/`.
- Add a provider to `web/deps.py` (the timing dependency lives in `routes/events.py`), or add any dependency
  (no `sse-starlette`).
- Use `fastapi.sse.EventSourceResponse` / a generator endpoint, or Starlette's `EventSourceResponse` (§4 library facts).
- Open a write unit of work, call `events.append`, or write any row from `src/`. Do not merge streams, read a case
  stream, send `case_created` or any progress event, or share helpers with CON-21 (`routes/staff_live.py`).
- Import `meridian.adapters.*` at run time in `src/meridian/web/routes/events.py` or `web/schemas/events.py` (only
  under `TYPE_CHECKING`).
- Log any payload, text, name or header value. The route logs only the `stream_reconnect` record.
- Catch `Exception` / `BaseException` in the poll loop, or put an `await` in its `finally`.
- Use real sleeps in AC-4/PA-2. Make a paid model call, bind any port (4019/5184 or other), or start a server.
- Read, print or commit `.env` values. Put a secret, code, card-like number or full phone number in tests.
- Run the full suite (§7 says why it is not needed), use `-n` above 2, or `git add -A`.

---

## 6. Data and fixtures

All synthetic, built at run time:
- **Event payloads:** `PAYLOADS` in `tests/api/events_support.py` (Step 7). The text comes from the OpenAPI `FRAMES`
  example (`representative_joined`, `ai_paused`, `staff_message`) and the `Ev*` field descriptions (`ai_resumed`,
  `chat_closed`, `demo_reset`). The `staff_message` text "Hi Omar, I can look at the after-hours charge with you." is
  the WP-2 worked-pair sentence. `message_id` is `"m-88"`. Times are `2026-10-16 14:22:00` and `14:22:40` America/Chicago.
- **Threads and sessions:** fresh UUID4s from `new_thread_id()`. Tokens come from `FakeSessionStore.issue()` (letters
  only).
- **Database:** `temp_sqlite()` (a migrated copy of the issued scheduling DB; the issued file is never written), or the
  container's working copy under `tmp_path` via `full_app` with `issued_db_path=ISSUED_DB`.
- **Ids 12–14 in AC-14:** produced by appending 11 `case_changed` filler rows on a second thread's stream first (fresh
  DB ids start at 1).

---

## 7. Checks

Run from the worktree root with `export UV_LINK_MODE=hardlink`. Cheapest first; stop at the first red.

| # | When | Command | Passing looks like |
|---|---|---|---|
| 1 | While iterating | `uv run pytest tests/unit/web/test_events_frames.py tests/unit/web/test_register_events.py tests/api/test_events.py -q` | All pass |
| 2 | Before commit: lint + format | `uv run ruff check src/meridian/web tests/api tests/unit/web tests/contract/cases tests/journeys/j7 tests/journeys/j9` and `uv run ruff format --check src/meridian/web tests/api tests/unit/web tests/contract/cases tests/journeys/j7 tests/journeys/j9` | No findings |
| 3 | Before commit: type check | `uv run mypy` (project config: `src/meridian`, `tests`, `eval`, strict) | `Success: no issues found` |
| 4 | Before commit: affected tests | `uv run --with pytest-xdist pytest -n 2 tests/api tests/unit/web tests/unit/test_import_direction.py -q` | All pass. Includes AEA-23's `test_gate.py` sweep: `streamChatEvents` gains a real route but still answers 401 without a session |
| 5 | Before commit: AC-15 local | `uv run pytest tests/api/test_contract_cases_events.py -rs -s` | Pass, frame counts printed (`first_connect: 200, frames=4`, `resume: 200, frames=2`) |
| 6 | Before commit: affected journeys | `uv run pytest -m journey tests/journeys/j9/test_aea_41.py tests/journeys/j7/test_aea_41.py -q`, then `uv run python -m tests.journeys.affected --base main` | Pass. The second command selects every journey because `tests/journeys/` changed; today that is these two and `j9/test_aea_26.py` |
| 7 | Before commit: context | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and `git diff --name-only main...HEAD` | No FAIL; diff lists only §2's owned files |
| 8 | After AEA-59 merges (not this ticket's gate) | `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k streamChatEvents -rs` | The case passes with its frame count printed |

**Why not the full suite** (`build-loop-test-scope.md`): the change adds two new modules and fills one hunk of
`web/container.py`. No shared fixture, setting, dependency, lockfile or widely imported module changes. Affected =
`tests/api/`, `tests/unit/web/` (they import `meridian.web.container` / `meridian.web.app`) and
`tests/unit/test_import_direction.py` (it reads `container.py`). Evidence in the report: each command and its pass
count. The ticket's capture evidence is AC-14. Its evaluation check is n/a (no DO-5 suite drives CON-3; AC-13 proves
nothing is written).

**Gates:** none (no human, external, paid or live gate).

---

## 8. Risks and requests

- **R-1 — `at` timezone on the wire (engineering decision, made here).** Frames send `at` with the America/Chicago
  offset, as the OpenAPI example does. AEA-40's history and AEA-46's CON-21 should agree. If the reviewer or the UX
  session wants UTC, it is a one-line change in `chat_event_data` plus PA-3. Either form validates.
- **R-2 — Malformed `Last-Event-ID` → start at 0 (engineering decision).** The operation documents no 400. The browser
  only echoes ids the server sent. Covered by PA-1.
- **R-3 — `get_stream_timing` / `StreamTiming` is a route-local seam, not a DO-4 provider.** It exists so tests drive
  time without real sleeps. It is not a shared primitive, and AEA-46 must not import it (DO-3 S-11). If the integrator
  prefers a shared provider, that is a follow-up on AEA-23 (`web/deps.py`). It is **not** requested now.
- **R-4 — Writer payload shape (sibling assumption).** Frames are `{event_id, type, at}` + the stored payload.
  AEA-30's plan §4.6 and AEA-31's step 1.8 store exactly the `Ev*` fields minus those three. **AEA-46 has no plan yet**
  (it writes `representative_joined`, `ai_paused`, `staff_message`, `ai_resumed`, `chat_closed`). If it stores
  differently shaped payloads, AEA-52's end-to-end check fails. Ask the AEA-46 planner to follow the same rule.
- **R-5 — Shared context files.** The area map, the ICM checklist and DO-3 §3 receive one-line edits from many wave-2
  tickets, so expect textual merge conflicts at adjacent lines. The merge step resolves them by keeping every ticket's
  line. The area map showed conflict markers in the working tree earlier today (`aea-33` merge), so re-read it before
  editing.
- **R-6 — The `request` record is written when the stream ends** (middleware `finally`). Its `duration_ms` is the
  stream's lifetime. This is no change to AEA-23; it is noted for DO-6 readers and AEA-53.
- **R-7 — A failing poll read ends the stream without a JSON error** (headers are already sent). The browser
  reconnects and replays (SDQ-5, N-2). The read is not retried in the loop.
- **R-8 — Routers appear at lifespan start**, because `register_events` runs inside `build_container`. AEA-23's
  `test_gate.py` adds probe routes before the lifespan, which gives a harmless duplicate GET for this path (both answer
  401 unsigned). The idempotence flag `app.state.events_router_included` prevents duplicates across lifespans.
- **R-9 — AEA-59's case format is not fixed yet.** `tests/contract/cases/events.py` mirrors AEA-23's `auth.py` shape
  and documents its vocabulary. If AEA-59's runner needs another shape, that is its follow-up on this file, merged
  after.
- **R-10 — J-7 is a *proposed* map entry** (slice plan §0a). This ticket writes `j7/test_aea_41.py` as the ticket
  requires. It does not edit the slice plan.
- **R-11 — Spec wording.** The ticket says `StreamKey` is AEA-02's. It is AEA-10's (`adapters/sqlite/rows.py`). This
  has no effect on the work.
- No contract problem was found, and no signed contract needs changing. Sign-off D-6 (no 410) is followed as
  recommended.

---

## 9. Readiness

**READY.** AEA-10, AEA-11 and AEA-23 are merged on `main` (`c7ce976`), and every import this slice needs exists there.
Same-wave siblings (AEA-29/30/31/46 writers, AEA-57 harness, AEA-59 runner) are not imported. Their effects are
seeded by the tests, and the record states `mock-tested` with *Blocked by* AEA-57, AEA-51, AEA-52. No product
decision is needed.

## Deviations

- `chat_event_frames` is annotated `AsyncGenerator[bytes]` (not `AsyncIterator[bytes]`) so mypy accepts the test's `aclose()`; behaviour is as planned.
- `tests/api/events_support.py` adds one `# type: ignore[arg-type]` on the ASGI `app(scope, receive, send)` call (FastAPI's callable typing).
- The AC-12 test reconnects with the first event's id (2 frames) so the staff sentence (third event) is in a frame.
