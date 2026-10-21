# Plan — [AEA-46] staff API: live takeover and case stream (CON-14, CON-21)

**Status:** planned (READY)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/46 (spec copy: `docs/plans/tickets/AEA-46.md`)
**Base revision:** `ef40f45` (main, after the AEA-32 merge). Planner: `fanout-planner` on claude-opus-5-5, 2026-10-21.
**Lane / risk:** `lane::build-loop`, no `risk::security` → plan → implement (code **and** the tests named here) →
affected tests → `code-review-agent`. No test-writer, no frozen manifest, no security agent (rule `build-loop-test-scope`).

---

## 1. Goal and sources

### Goal (quoted from the issue's *What to build*)

> **US-20:** "As a **representative** on a simulated shift, I need to claim a live-queued case, reply in the customer's
> chat while the assistant is paused, and hand back or close explicitly, so that the customer has one conversation, not
> two."
> **US-15:** "As a **homeowner** during staffed hours (simulated in the demo), I need to wait in the same chat and see
> clearly when a person has joined and the assistant has stopped, so that I know who I'm talking to."

The slice delivers three things:

1. **`services/live_chat.py`: `LiveChatService`.** Its `join`, `send`, `hand_back` and `close` each run as one write
   transaction with the eight ordered checks of stage7/staff.md §5.
2. **`web/routes/staff_live.py` + `web/schemas/staff_live.py`:**
   - CON-14 `liveChatAction`, a `def` route;
   - CON-21 `streamCaseEvents`, an `async def` SSE route with its own generator.
3. **The `register_staff_live()` hunk in `web/container.py`.** It binds `get_live_chat()` and includes the router.

**In practice (WP-2, Omar Patel, MHC-10002, INV-204411).** Riley has claimed MHC-C-0007, which is live-queued.
1. Riley posts `{"action":"join"}`. The answer is 200 with `controller {kind: human, display_name: "Riley"}` and
   `live.state "joined"`. Omar's thread stream gains `representative_joined` and `ai_paused`, and the case stream
   gains `controller_changed`.
2. Riley posts `{"action":"send","text":"Hi Omar, …"}`. The answer is 200 with the stored message (speaker
   `representative`, "Riley"). The message row sits in Omar's own thread.
3. Omar replies (AEA-40 writes that reply). The open `GET …/events` receives `event: customer_message`.
4. Riley closes. The stream receives `chat_closed {reason: closed_by_staff}` and stays open.
5. The case's `version` and `lifecycle` never change.

### Sources (all read for this plan)

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-46.md` (= GitLab #46) | AC-1…AC-24, owned files, must-not-edit list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-46 (wave 2, blockers 10, 23); §0a J-7; §3 collision map | One route + one schema file; own hunk only; `tests/journeys/j7/test_aea_46.py` only |
| Component contracts (Stage 7, win over DO-4) | `docs/design/contracts/stage7/staff.md` §1 (`StaffActor`, `STAFF_PERSONAS`), §5 (`LiveChatService`, checks, writes, R-W-16), §6 (`LiveActionRequest.text`), §7 (CON-21), §10 (clocks), §11 (reset) | Every signature and rule in §4–§5 below |
| | `stage7/web.md` §1 (`ApiProblem`), §3 (`require_staff`), §4 (providers), §7 (`ResetGate`), §10 (`stream_reconnect`), §11 (poll 1 s [A], heartbeat 15 s), §13 (`assert_response_matches`, `assert_sse_frames_match`) | Route plumbing |
| | `stage7/cases.md` §1.0 (unit of work), §1.1 (`live_state`, `live_since`, AUTOINCREMENT events), §1.2 (`cases_ro.owner`, `messages.append`, `events.latest_of`, `case_events.append`), §1.3 (reset), §1.5 (`temp_sqlite`), §5 (`CaseService.apply` version rule) | Storage calls; AC-21 double |
| | `stage7/data.md` §1 (STORE profile; `redact_store` binding, MC-23) | AC-7 |
| DO-4 | `docs/design/contracts/internal-components.md` §11 (`AI_PAUSED` row: AEA-40 reads `controller`), §13 (`UnitOfWork`, `core.events`, `CaseService.apply(case_ref, action, actor, expected_version, now)`) | Seams with AEA-40 and AEA-29 |
| DO-3 | `docs/design/code-design.md` §2.1 (services may call `tx.<repo>` and import `adapters/sqlite` row types; web never imports adapters at run time), §2.3 rules 1 and 4, §3 module map lines for `live_chat.py` and `routes/staff_live.py`, S-11 (polling, no shared SSE helper) | Dependency direction; AC-24 |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `liveChatAction` (≈5763–5924), `streamCaseEvents` (≈5925–5992), `LiveActionRequest` (11003), `LiveActionResponse` (11019), `LiveState` (10845), `ChatLine` (10722), `Speaker` (8203), `CaseEvent` + `Ce*` (11688–11830), thread `Ev*` (9982–10165), `ApiError` (9708), responses `ValidationError`, `RoleNotAllowed`, `CaseNotFound`, `Unauthenticated` (11873–12040) | Wire shapes; examples used as WP-2 fixtures |
| Decisions | `docs/plans/7b-decisions/staff.md` STF-1, 7, 8, 11, 12, 13, 14, 23, 26; merge MC-7, MC-8, MC-23, MC-25; `residuals-web.md` R-W-16; `docs/plans/ux-join/backend-amendments.md` AEA-46-1, AEA-46-2 | Already reflected in the ACs |
| Observability (DO-6) | `docs/design/observability-contract.md` row WF-4 (line 79), CAP-4 (line 266), *Registering a new workflow* (278) | AC-20, AC-24 |
| Metrics (DO-7) | M-13, M-27 (ticket *Metrics*) | No write to owner, promise, version or lifecycle (AC-1, AC-21) |
| Evaluation (DO-5) | n/a: no E-suite drives staff live chat (ticket *Evaluation*) | Nothing added |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`; workspace `code-structure.md` (test file cap 500, service cap 600, route cap 600), `async-safety.md` rules 2–3 | Checks, journey record, file sizes |
| Sibling plans (read only, for seam agreement) | `docs/plans/fanout/2026-10-21-build/AEA-41.md` (frame = `{event_id, type, at}` + stored payload; thread payload fixtures), `AEA-40.md` (reads `conv.controller.case_ref`; `customer_message` payload), `AEA-29.md` (`case_changed`, shift-end `chat_closed` payloads), `AEA-30.md` R-3 (`Key("demo_clock")`), `AEA-42.md` step 8 (lazy keys) | §4.6 payload table |

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Create / modify | Content (size target) |
|---|---|---|
| `src/meridian/services/live_chat.py` | create | `StoredChatLine`, `LiveView`, `LiveRefused`, `LiveChatService` (≤ 330 lines) |
| `src/meridian/web/schemas/staff_live.py` | create | `LiveActionRequest`, response models, `live_action_response`, case-frame encoder, `parse_last_event_id`, constants (≤ 200) |
| `src/meridian/web/routes/staff_live.py` | create | `parse_case_ref`, `case_stream_key`, `read_case_events`, `case_event_frames`, `known_case`, the two endpoints, `build_router` (≤ 330) |
| `src/meridian/web/container.py` | modify **`register_staff_live` only** (docstring + body) | Binds `deps.LIVE_CHAT`, includes the router once |
| `tests/services/live_chat_support.py` | create | Seed helpers, snapshot, AEA-40 stand-in (≤ 260) |
| `tests/services/test_live_chat.py` | create | AC-1…AC-8, AC-21 (≤ 500) |
| `tests/services/test_live_chat_events.py` | create | PA-2, PA-3 (payload seams) (≤ 200) |
| `tests/api/staff_live_support.py` | create | App builder, in-process ASGI stream harness, doubles (≤ 400) |
| `tests/api/test_staff_live_routes.py` | create | AC-9…AC-12, AC-18, PA-4 (≤ 450) |
| `tests/api/test_staff_live_stream.py` | create | AC-13…AC-16, PA-5 (≤ 450) |
| `tests/api/test_staff_live_capture.py` | create | AC-17, AC-20 (≤ 250) |
| `tests/api/test_contract_cases_staff_live.py` | create | Driver for AC-22 until AEA-59 lands (≤ 300) |
| `tests/contract/cases/staff_live.py` | create | AC-22 case data (≤ 150) |
| `tests/unit/web/test_register_staff_live.py` | create | PA-1 (≤ 200) |
| `tests/unit/web/test_staff_live_units.py` | create | Schema, frame, parser and loop unit tests, the WP-2 pair at unit level (≤ 400) |
| `tests/journeys/j7/test_aea_46.py` | create | AC-23 (≤ 250) |
| `docs/testing/journeys/<run date>-AEA-46.md` | create | AC-23 record, level `mock-tested` |
| `.claude/reference/area-map.md` | modify: row A9 status cell only | AC-24 |
| `.claude/state/icm-progress.md` | modify: add one row | AC-24 |
| `docs/design/code-design.md` | modify: §3 module-map lines 267 (`live_chat.py`) and 311 (`routes/staff_live.py · schemas/staff_live.py`) only | AC-24 |
| `docs/design/observability-contract.md` | modify: row WF-4 (line 79) only | AC-24 |

**Test file split vs the ticket's `…::` shorthand.** The ticket writes AC-9…AC-19 as `…::name` after
`tests/api/test_staff_live_routes.py`. Putting all of them in one file would break the 500-line test cap
(`code-structure.md`). So: AC-13…AC-16 go in `tests/api/test_staff_live_stream.py`, and AC-17 and AC-20 go in
`tests/api/test_staff_live_capture.py`. **Every test function keeps the name the ticket gives.** The PR description
and the journey record list the file for each AC.

### Shared surfaces: read only, never edit

`src/meridian/web/{app,deps,errors,middleware,logging}.py`; every other `register_*` hunk in `web/container.py`;
`src/meridian/adapters/sqlite/*` (incl. `rows.py`, `repos_core*.py`, `repos_cases.py`, `db.py`, `migrate.py`, `schema/`);
`src/meridian/domain/*`, `ports/*`, `policy/*`, `privacy/*`, `config.py`, `services/reset_gate.py`;
`tests/api/openapi_check.py`, `tests/api/web_shell_support.py`, `tests/fixtures/sqlite.py`, `tests/fakes/*`,
`tests/conftest.py`, `tests/journeys/{affected.py,README.md}`; the OpenAPI YAML, `UI_CONTRACTS.md`, `docs/ux/**`,
`apps/web/**`, the briefing, issued data, `docs/archive/`, `docs/parked/`; `pyproject.toml`, `uv.lock`.

### Owned by other slices: do not touch, do not import from unmerged branches

- `web/routes/events.py` and `web/schemas/events.py` (AEA-41, CON-3). **No import** from them, now or after they
  merge: DO-3 S-11 and AC-19.
- `tests/api/events_support.py` (AEA-41; not on main). Copy its harness pattern (given in §5 step 9). Do not import it.
- `services/cases.py` and `handoff.py` (AEA-29), `services/demo.py` (AEA-30), `services/turn.py` and `session.py`
  (AEA-40), `services/staff.py` (AEA-44).
- `web/routes/staff_{session,cases,clock}.py` (AEA-44, 45, 47) and their schemas.
- `tests/journeys/support/` (AEA-57) and `tests/contract/test_openapi_server.py` (AEA-59).

---

## 3. Requirements table

AC text is the ticket's (abridged where marked …). PA = plan-added; each closes a gap found in reconciliation (§3b).

| ID | Requirement | How it is implemented | Verified by (file::test, command) |
|---|---|---|---|
| AC-1 | [invariant] `join` with preconditions met writes in one transaction: controller human, `live_state` joined, `live_since` = demo clock, `representative_joined` then `ai_paused` on the thread stream, `controller_changed` (human, "Riley") on `case:<ref>`, one `case_event` (actor_role representative); owner and promise rows unchanged | §5 step 2, `_write` join branch | `tests/services/test_live_chat.py::test_join_writes_one_transaction`: rows and events read back, event ids ascending, owner and promise rows equal the pre-call snapshot; also asserts `controller.case_ref == ref` (PA-2) |
| AC-2 | [failure/refusal] Checks 1–4 and 7–8 give their result; a refusal writes nothing | `_check` rows 1–4, 7, 8 | `…/test_live_chat.py::test_checks_in_order_write_nothing` (parametrised: 7 cases listed in §5 step 7); snapshot equal per case |
| AC-3 | [invariant] Repeats idempotent: `join` on joined, `hand_back` on handed_back, `close` on closed → 200 current view, no write | `_check` rows 6 and 8 return `_view(conv)` before any write | `…::test_repeats_write_nothing` |
| AC-4 | [invariant] `send` writes into the customer's thread (`thread_id` of the case, role representative, demo-clock `at`) + `staff_message`; returns `StoredChatLine` with `speaker_name` "Riley" | `_write` send branch | `…::test_send_same_thread` |
| AC-5 | [invariant] `hand_back` → ai / handed_back, `ai_resumed`, `controller_changed (ai, null)`; `close` → ai / closed, thread `chat_closed`, case `chat_closed {closed_by_staff}`; after every action controller = human ⇔ live_state = joined | `_write` hand_back and close branches | `…::test_hand_back_close_and_controller_invariant`. Two cases, because the spec table makes join→send→hand_back→close impossible on one case (§8 R-7). Also asserts `live_since` = action time (PA-6) |
| AC-6 | [invariant] All or nothing: events append raising after the controller write leaves everything as it was | Unit of work rolls back on exception (`db.py` `__call__`); the service catches nothing | `…::test_live_action_rolls_back` (monkeypatch `EventsRepo.append` to raise) |
| AC-7 | [negative] Staff text stored, relayed and returned STORE-redacted | `redact_store(text)` before `messages.append`; same string in event payload and view | `…::test_staff_message_store_redacted` (`redact_store = lambda t: redact(t, RedactionProfile.STORE).text`; digits generated at run time, §6) |
| AC-8 | [invariant] Claims belong to the role (STF-1): a second representative session joins a case the role owns | Service compares roles only (`StaffActor.owns`) | `…::test_two_sessions_share_riley` (app level: two `FakeSessionStore` representative tokens; B joins → 200 `JOINED`, A sends → 200 `SENT`) |
| AC-9 | [invariant] 200 bodies validate for JOINED, SENT, HANDED_BACK, CLOSED | `live_action_response(view)` | `tests/api/test_staff_live_routes.py::test_live_action_matches_openapi` (`assert_matches`) |
| AC-10 | [failure/refusal] `LiveRefused` mapping 404/403/409/409; `action: "wave"` → 400 field `action` | `STATUS_BY_CODE`; pydantic Literal | `…/test_staff_live_routes.py::test_live_action_refusals` (double service returning each refusal; bodies validate) |
| AC-11 | [failure/refusal] `text` rules: null, "   ", 2,001 chars on `send`, any text on `join` → 400 field `text` with the four constraints; no service call; text never echoed | `LiveActionRequest._text_rules` raising `PydanticCustomError` | `…::test_text_rules` (zero calls on the double; submitted text absent from bodies and `caplog`) |
| AC-12 | [failure/refusal] Roles: live = representative only (`needs ["representative"]`); stream = representative, supervisor, owner (customer `needs [...3]`) | `require_staff(REPRESENTATIVE)` / `require_staff(REPRESENTATIVE, SUPERVISOR, OWNER)` declared first in each signature | `…::test_live_roles` (no service call, no poll read recorded for refusals) |
| AC-13 | [invariant] Stream: `text/event-stream`; frames validate; `Last-Event-ID: 30` → only ids > 30 in order + one `stream_reconnect` (case_ref, last_event_id 30); later append arrives; idle heartbeat (patched constant); unknown case 404 before any frame | `case_event_frames`, `known_case` | `tests/api/test_staff_live_stream.py::test_case_stream_replay_live_and_heartbeat` |
| AC-14 | [invariant] Start after reset: no header → no `demo_reset` frame, stays open; header below the reset id → receives it and closes; stays open after `chat_closed` | `read_case_events(last=None)` resolves `latest_of(stream, "demo_reset")`; loop closes only on `demo_reset` | `…/test_staff_live_stream.py::test_case_stream_start_after_reset_and_close_rules` |
| AC-15 | [invariant] One shared limiter; a fifth poll waits while 4 slots are held; a `def` route still answers with five streams open | Reads run through `anyio.to_thread.run_sync(…, limiter=get_stream_poll_limiter())` | `…::test_streams_share_limiter` |
| AC-16 | [invariant] Reset held: open stream skips reads, never 503; a new connection is accepted without waiting; `liveChatAction` waits then runs | Loop checks `gate.held()`; `known_case` skips its read while held; the middleware handles the waits (already on main) | `…::test_reset_gate_behaviour` |
| AC-17 | [negative] Staff text and relayed customer text in rows and response/frame, absent from every log record | No route or service logs text; only the `stream_reconnect` record (ids and counts) | `tests/api/test_staff_live_capture.py::test_message_text_never_logged` |
| AC-18 | [invariant] Both operations 401 `UNAUTHENTICATED` without `mhc_session` (real AEA-23 middleware) | Middleware (on main) | `…/test_staff_live_routes.py::test_login_gate` |
| AC-19 | [invariant] Route and schema files read no clock and import nothing from `routes/events` | Design: no clock read; own constants | `grep -nE "datetime\.now\|time\.time\|routes\.events\|routes/events" src/meridian/web/routes/staff_live.py src/meridian/web/schemas/staff_live.py` prints nothing (run by the implementer **and** by `code-review-agent`) |
| AC-20 | [capture] WF-4 records: one `request` per call (`request_id` = `X-Request-ID`, route template, `caller_role`); one `case_event` per live action with actor_role and action; thread-stream events keyed by `thread_id`, case-stream events by `case:<ref>` | Middleware `request`; `_write` `case_events.append(detail={"action": …})`; `thread_stream` / `case_stream` keys | `…/test_staff_live_capture.py::test_wf4_live_entry_points_emit_records` (prints records, case events, stream rows) |
| AC-21 | [invariant] Live actions leave `version` and `lifecycle` unchanged, no `case_changed`; a later CON-13 `resolve` with the pre-join version is accepted | `_write` never touches `cases` | `tests/services/test_live_chat.py::test_live_actions_keep_case_version` (with a `CaseService` double that honours cases.md §5's version rule, §5 step 7) |
| AC-22 | [contract] `tests/contract/cases/staff_live.py` holds the server cases | Data file, §5 step 12 | Now: `uv run pytest tests/api/test_contract_cases_staff_live.py -q`. After AEA-59 merges: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "liveChatAction or streamCaseEvents" -rs` |
| AC-23 | [journey] Extends J-7: join, send, hand back, close; customer thread shows each line; `version` unchanged; CON-21 delivers `controller_changed`, no `case_changed`; level `mock-tested` until AEA-57 and AEA-52 | `tests/journeys/j7/test_aea_46.py`, §5 step 13 | `uv run pytest -m journey tests/journeys/j7/test_aea_46.py -q`; record `docs/testing/journeys/<date>-AEA-46.md` |
| AC-24 | [regression/context] area map A9 row, ICM row, DO-3 §3 two lines, DO-6 WF-4 cell | §5 step 15 | `git diff --stat` on the docs commit shows only those four files plus the journey record |
| PA-1 | `register_staff_live` binds `deps.LIVE_CHAT` to a `LiveChatService` over `Key("uow_factory")`, the lazy `Key("demo_clock")` and the STORE redactor. It includes the router once. A bare app gets nothing. Before AEA-30 binds the clock, a write action raises `RuntimeError("not bound: demo_clock")`, and the route is reachable through the real container | §5 step 8 | `tests/unit/web/test_register_staff_live.py` (4 tests, §5 step 11) |
| PA-2 | `join` stores `controller.case_ref` (AEA-40 relays `customer_message` to `case_stream(conv.controller.case_ref)`; AEA-40 plan step 4f) | `Controller(kind="human", representative_name=name, case_ref=case_ref)` | asserted inside AC-1's test, plus `tests/services/test_live_chat_events.py::test_join_sets_case_ref_for_relay` |
| PA-3 | Thread-stream payloads render as valid OpenAPI `ChatEvent`s (AEA-41 sends `{event_id, type, at}` + payload unchanged); case-stream payloads as `CaseEvent`s | Payload table §4.6 | `tests/services/test_live_chat_events.py::test_thread_events_validate_as_chat_events`, `::test_case_events_validate_as_case_events` (`assert_sse_frames_match` with `streamChatEvents` / `streamCaseEvents`) |
| PA-4 | A malformed `{reference}` answers 404 `CASE_NOT_FOUND` (details null) on both operations, never 400/422 on the stream (it documents no 400) | `parse_case_ref` | `tests/api/test_staff_live_routes.py::test_malformed_reference_is_not_found` |
| PA-5 | A malformed `Last-Event-ID` is treated as absent: start at the newest `demo_reset` and no `stream_reconnect` | `parse_last_event_id` → None | `tests/unit/web/test_staff_live_units.py::test_parse_last_event_id` and `tests/api/test_staff_live_stream.py::test_malformed_last_event_id_is_ignored` |
| PA-6 | `LiveState.since` = the time the current live state began (join, hand_back and close each set it to the action's demo time; send keeps it) | `live_since=now` in the three state changes | asserted in AC-5's test |
| PA-7 | WP-2 worked pair at unit level: the four 200 bodies equal the OpenAPI examples JOINED, SENT, HANDED_BACK, CLOSED; the case frames equal the `FRAMES` example byte for byte | `live_action_response`, `encode_case_frame` | `tests/unit/web/test_staff_live_units.py::test_wp2_bodies_equal_openapi_examples`, `::test_case_frames_equal_openapi_example` |

### 3b. Source-contract reconciliation (obligations the ACs leave implicit)

| Obligation | Source | In ticket | Disposition | Step |
|---|---|---|---|---|
| `join` must set `controller.case_ref`; AEA-40 reads it to relay `customer_message` | DO-4 §11 `AI_PAUSED` row; AEA-40 plan step 4f | no | added (PA-2) | 2 |
| Thread payload keys the CON-3 renderer expects (`speaker`, `display_name`, `line`, `message_id`, `text`, `composer_disabled`) | OpenAPI `Ev*`; AEA-41 plan fixtures | partly ("event lines from texts") | added (PA-3) | 2 |
| `CeControllerChanged.line` is required but no addendum names the sentence | OpenAPI `CeControllerChanged` | no | added: join → `live.rep_joined`, hand_back → `live.ai_resumed` (existing DAT-29 texts) | 2 |
| `streamCaseEvents` documents no 400 | OpenAPI | no | added (PA-4): malformed ref → 404 | 4 |
| Stream "never waits on connect" during a reset (staff.md §11) vs the 404 lookup reading SQLite | staff.md §11, web.md §7 | implicit | added: `known_case` skips its read while `gate.held()`; the first poll resolves the start | 4 |
| `LiveState.since` meaning on hand_back and close | OpenAPI examples (illustrative) | no | added (PA-6) | 2 |
| Wire times in America/Chicago | staff.md §10; AEA-41 decision | implicit | added: `wire_time()` for `since`, message `at` and frame `at` | 3 |
| CON-13 `resolve` after live actions (AC-21) needs `CaseService` (AEA-29, unmerged) | cases.md §5 | yes | in-ticket (double) | 7 |
| Demo clock key comes from AEA-30 (unmerged) | AEA-30 plan R-3 | no | added (PA-1): lazy forwarder, as AEA-40 and AEA-42 do | 8 |
| AEA-59 runner not on main | slice plan §0a | yes | in-ticket; driver test until it lands (sibling precedent) | 12 |
| DO-6 WF-4 lacks CON-21 | AC-24 | yes | in-ticket | 15 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `POST /api/staff/cases/{reference}/live` (CON-14) | WF-4 | yes (row 79, "takeover and live chat (CON-14 …)") | CAP-4; EV: flags → R-37 only; M-13, M-27 |
| `GET /api/staff/cases/{reference}/events` (CON-21) | WF-4 | **added by AC-24** (step 15) | same |

---

## 4. Shared code to use (copied from main at `ef40f45`)

### 4.1 Storage (AEA-10, merged)

```python
# meridian.ports.runtime
class Clock(Protocol):
    def now(self) -> dt.datetime: ...
class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
# UnitOfWork: core: CoreRepos; cases: CaseRepos; …; def commit(self) -> None
# SqliteUnitOfWorkFactory: write=True → BEGIN IMMEDIATE; leaving the block without commit() → ROLLBACK;
#   an exception → ROLLBACK and re-raise.

# tx.core.cases_ro (repos_core_aux.CasesReadRepo)
def owner(self, case_ref: CaseRef) -> CaseOwnerRow | None
# rows.CaseOwnerRow: thread_id: ThreadId; owner_role: StaffRole | None; owner_since: datetime | None; lifecycle: str

# tx.core.conversations (repos_core.ConversationsRepo)
def lookup(self, thread_id: str) -> ConversationRow | EndedThread | None
def set_controller(self, thread_id: ThreadId, controller: Controller, *, live_state: str, live_since: datetime | None) -> None
#   one UPDATE of controller, controller_name, controller_case_ref, live_state, live_since; StorageError if no row
def insert(self, row: ConversationRow) -> None                 # tests only
def set_live_state(self, thread_id: ThreadId, live_state: str, live_since: datetime | None) -> None   # tests only

# tx.core.messages (repos_core.MessagesRepo)
def append(self, thread_id: ThreadId, role: str, text_redacted: str, at: datetime, *, turn_id=None, kind=None,
           card_id=None, choice_option=None) -> int
def all_for_thread(self, thread_id: ThreadId) -> tuple[MessageRow, ...]   # tests only

# tx.core.events (repos_core_aux.EventsRepo)
def append(self, stream: StreamKey, event: StreamEvent) -> EventId
def after(self, stream: StreamKey, last: EventId) -> list[EventRow]      # id > last ORDER BY id
def latest_of(self, stream: StreamKey, kind: str) -> EventId | None
#   payload JSON is stored with sort_keys=True: read-back payloads have SORTED keys.

# tx.cases.case_events (repos_cases.CaseEventsRepo)
def append(self, event: CaseEventRow) -> int
def list_for_case(self, case_ref: CaseRef) -> tuple[CaseEventRow, ...]   # tests only
# tx.cases.cases: get(case_ref) -> CaseRow | None; insert(row: CaseRow); update_versioned(case_ref, expected_version,
#   **changes) -> int | None (new version, None when stale/unknown; allowed keys include lifecycle, resolved_at, updated_at)
# tx.cases.promises: insert(case_ref, promise: Promise, at) -> int; history(case_ref) -> tuple[PromiseRow, ...]
# tx.core.reset.clear_demo_tables(reset_id: str, *, ended_at: datetime | None = None) -> Cleared   # tests only (AC-14)
```

```python
# meridian.adapters.sqlite.rows (import in services and tests; web imports it under TYPE_CHECKING only)
StreamKey = NewType("StreamKey", str)
def thread_stream(thread_id: ThreadId) -> StreamKey        # the bare thread id
def case_stream(case_ref: CaseRef) -> StreamKey            # "case:" + ref
class StreamEvent(MeridianModel): type: str (1–40); payload: dict[str, JsonValue] = {}; at: datetime   # demo clock
class EventRow(MeridianModel): id: EventId; stream: str; type: str; payload: dict[str, JsonValue]; at: datetime
class ConversationRow(MeridianModel): thread_id: ThreadId; demo_session: str; run_tag: Literal["live","eval","load","seed"];
    run_id: str | None = None; agent_version: str; started_at: datetime; started_wall_at: datetime | None = None;
    staffing_at_start: … = None; outcome: … = "open"; ended_wall_at=None; last_customer_wall_at=None;
    controller: Controller = Controller(kind="ai"); live_state: Literal["not_live","queued","joined","handed_back","closed"] = "not_live";
    live_since: datetime | None = None
class CaseRow(MeridianModel): case_ref: CaseRef; thread_id: ThreadId; turn_id=None; customer_id: CustomerId | None = None;
    reason: HandoffReason; priority: Priority; rule_id: str; trigger: str; lifecycle: Lifecycle; owner_role: StaffRole | None = None;
    owner_since: datetime | None = None; due_at=None; wake_up_at=None; version: int = 1 (ge=1); seed: bool = False; …;
    created_at: datetime; updated_at: datetime; resolved_at=None; queued_at=None
class CaseEventRow(MeridianModel): id: int | None = None; case_ref: CaseRef; kind: str (1–40); key: str = "";
    actor_role: Literal["representative","supervisor","owner","ai","system"]; job_run_id: str | None = None;
    detail: dict[str, JsonValue] = {}; at: datetime
```

### 4.2 Domain, policy, privacy

```python
# meridian.domain.common
class MeridianModel(BaseModel): extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
class CaseRef(_PatternId): PATTERN = r"^MHC-C-[0-9]{4}$"    # CaseRef("x") does NOT validate; use the pattern
class ThreadId(_PatternId): PATTERN = UUID4
EventId = Annotated[int, Field(ge=0)]
class ApiErrorCode(StrEnum): … VALIDATION_ERROR, UNAUTHENTICATED, ROLE_NOT_ALLOWED, CASE_NOT_FOUND, CASE_ALREADY_CLAIMED,
    NOT_LIVE, NOT_CLAIMED_BY_YOU …
class HandoffReason(StrEnum): … BILLING_DISPUTE = "billing_dispute" …      # tests
class Priority(StrEnum): P0 … P3                                           # tests
class Promise(MeridianModel): policy_row: str; text: str; due_at: datetime | None; due_label: str | None;
    extra_lines: tuple[str, ...] = (); live_queued: bool = False          # tests
# meridian.domain.state
class Controller(MeridianModel): kind: Literal["ai","human"]; representative_name: str | None = None; case_ref: CaseRef | None = None
# meridian.domain.staff
class StaffRole(StrEnum): REPRESENTATIVE, SUPERVISOR, OWNER
STAFF_PERSONAS: Mapping[StaffRole, StaffPersona]   # name: "Riley" | "Demo supervisor" | "Demo business owner"
class StaffActor(MeridianModel): role: StaffRole; name: str; signature: str; def owns(self, owner_role: StaffRole | None) -> bool
def actor_for(role: StaffRole) -> StaffActor
CUSTOMER_SPEAKER_NAME = "Customer"
class DemoRole(StrEnum): CUSTOMER, REPRESENTATIVE, SUPERVISOR, OWNER     # tests
# meridian.policy.texts
class TextId(StrEnum): REP_JOINED = "live.rep_joined"; AI_PAUSED = "live.ai_paused"; AI_RESUMED = "live.ai_resumed";
    CHAT_CLOSED = "live.chat_closed"; …
def render(text_id: TextId, /, **values: str) -> str
#   REP_JOINED "{rep_name} (demo representative) has joined." · AI_PAUSED "The assistant is paused while {rep_name} is here."
#   AI_RESUMED "{rep_name} handed the chat back to the automated assistant." · CHAT_CLOSED "{rep_name} closed this chat."
# meridian.policy.limits
class TurnLimits: max_message_chars: int = 2_000
# meridian.privacy.redact
class RedactionProfile(StrEnum): STORE = "store"; …
def redact(text: str, profile: RedactionProfile) -> Redacted      # .text; STORE: card → "[card number removed]", 6 digits → "[code]"
```

### 4.3 Web shell (AEA-23, merged)

```python
# meridian.web.errors
class ApiProblem(Exception):
    def __init__(self, status: int, code: ApiErrorCode, *, field: str | None = None, constraint: str | None = None,
                 details: dict[str, object] | None = None, headers: Mapping[str, str] | None = None) -> None
# 422 handler: field = loc without "body"; constraint = errors()[0]["msg"]; never the input.

# meridian.web.deps
LIVE_CHAT: Key[Any] = Key("live_chat"); UOW_FACTORY: Key[UnitOfWorkFactory] = Key("uow_factory")
def get_live_chat(request: Request) -> Any            # raises RuntimeError("not bound: get_live_chat") until bound
def get_uow_factory(request: Request) -> UnitOfWorkFactory
def get_stream_poll_limiter(request: Request) -> anyio.CapacityLimiter   # ONE CapacityLimiter(4) per process
def get_reset_gate(request: Request) -> ResetGate
def get_request_context(request: Request) -> RequestContext
def require_staff(*roles: StaffRole) -> Callable[..., StaffActor]   # 403 ROLE_NOT_ALLOWED {role, needs, reason}
def provided[T](app: Starlette, provider: Callable[..., T]) -> T    # tests: resolve outside a request

# meridian.web.middleware (already maps both operations)
OPERATIONS_BY_ROUTE[("POST", "/api/staff/cases/{reference}/live")] == "liveChatAction"
OPERATIONS_BY_ROUTE[("GET", "/api/staff/cases/{reference}/events")] == "streamCaseEvents"
RESET_NO_WAIT_OPERATIONS ⊇ {"streamCaseEvents"}   # liveChatAction is not in it and not in RESET_503_OPERATIONS:
#   while the gate is held the middleware awaits gate.wait_clear(limits.web.reset_wait_s) then runs the route (AC-16).
class RequestContext: request_id: RequestId; client_ip; session; run_tag; run_id; turn_verdict
class WebShellState: settings; wall_clock; public_paths
# The middleware writes the `request` record (record, request_id, route template, status, duration_ms, caller_role,
#   thread_id=None here) after the response ends; for a stream, after the stream ends.

# meridian.web.logging
STREAM_LOGGER = "meridian.web.stream"
def emit_record(logger_name: str, fields: Mapping[str, object]) -> None
ALLOWED_FIELDS["stream_reconnect"] == {"record", "request_id", "thread_id", "case_ref", "last_event_id", "replayed"}

# meridian.services.reset_gate
class ResetGate: def held(self) -> bool; def hold(self) -> ContextManager[None]; async def wait_clear(self, timeout_s: float) -> bool

# meridian.web.container
class Key[T]: name: str            class ContainerError(RuntimeError)
class Container: provide(key, factory); get(key); on_start; on_close; build(); close()
#   get on a key nobody provided → ContainerError("not provided: <name>")
```

### 4.4 Test surfaces (on main)

```python
# tests/fixtures/sqlite.py
ISSUED_DB: Path
@contextmanager
def temp_sqlite(*, issued_path: Path = ISSUED_DB) -> Iterator[TempStore]   # TempStore(data_dir, db_path, issued_path, uow)
# tests/fakes/clock.py
CHICAGO = ZoneInfo("America/Chicago")
class FixedClock: def __init__(self, at: datetime = WORKED_PAIRS_NOW); def now(self) -> datetime   # needs Chicago tz
# tests/api/openapi_check.py
@dataclass(frozen=True) class SseFrame: event: str | None; id: str | None; data: str
def assert_response_matches(response, operation_id: str) -> None      # NOT on a 200 stream (it calls .json())
def assert_sse_frames_match(frames: Sequence[SseFrame], operation_id: str) -> None
def load_document() -> Mapping[str, Any]
# tests/api/web_shell_support.py
def rand_word(length: int = 16, prefix: str = "zq") -> str          # letters only
def make_settings(tmp_path: Path, **changes: Any) -> Settings
class FakeSessionStore:  # implements LoginSessions + StaffAccess
    def issue(self, role: DemoRole = DemoRole.CUSTOMER, *, now: datetime | None = None) -> str   # a live token
class FakeHeartbeat
def full_app(monkeypatch, settings, *, store, heartbeat, overrides=None) -> FastAPI   # REAL build_container, starters off
def make_client(app: FastAPI, *, peer: str = "198.51.100.7") -> TestClient          # use as `with make_client(app) as c:`
def reset_gate_of(app: FastAPI) -> ResetGate
def cookie_header(token: str) -> dict[str, str]
def error_body(response, status: int, code: str) -> dict[str, Any]
def assert_matches(response, operation_id: str) -> None
@contextmanager def captured_log() -> Iterator[io.StringIO]        # "meridian" tree through the allow-list formatter
def records_of(stream: io.StringIO, kind: str) -> list[dict[str, Any]]
def app_log_text(caplog: pytest.LogCaptureFixture) -> str
def effective_routes(app: FastAPI) -> list[RouteInfo]               # RouteInfo(path, methods, operation_id, endpoint)
```

### 4.5 Sibling signatures used through doubles only (not on main)

- **`CaseService.apply(case_ref: CaseRef, action: CaseAction, actor: StaffActor, expected_version: int, now: datetime) -> CaseSummary | CaseActionRejected`**
  (DO-4 §13; AEA-29). AC-21's test double is §5 step 7.
- **`Key("demo_clock")`**: a `Clock` that AEA-30 provides (AEA-30 plan R-3). The hunk reads it lazily (§5 step 8).
- **AEA-40's `customer_message`** on `case:<ref>` while `controller = human`. The payload is `{"message":
  {"message_id": str(id), "speaker": {"kind": "customer", "display_name": CUSTOMER_SPEAKER_NAME}, "at": at.isoformat(),
  "text": text_store}}`. Tests stand it in with `append_customer_reply` (§6).
- **AEA-29** writes `case_changed {"version", "lifecycle"}` and `chat_closed {"reason": "shift_ended"}`.
- **AEA-31** writes `demo_reset {"speaker": EVENT_SPEAKER, "line": "The demo was reset, so this chat has ended. Nothing from it was kept."}`.

### 4.6 Stream payloads this service writes (decided; frame = `{event_id, type, at}` + payload)

`EVENT_SPEAKER = {"kind": "event", "display_name": None}`; `name = actor.name` ("Riley").

| Action | Stream | `type` | `payload` |
|---|---|---|---|
| join | thread `thread_stream(tid)` | `representative_joined` | `{"speaker": {"kind": "representative", "display_name": name}, "display_name": name, "line": render(TextId.REP_JOINED, rep_name=name)}` |
| join | thread | `ai_paused` | `{"speaker": EVENT_SPEAKER, "line": render(TextId.AI_PAUSED, rep_name=name)}` |
| join | case `case_stream(ref)` | `controller_changed` | `{"controller": {"kind": "human", "display_name": name}, "line": render(TextId.REP_JOINED, rep_name=name)}` |
| send | thread | `staff_message` | `{"speaker": {"kind": "representative", "display_name": name}, "message_id": str(mid), "text": stored}` |
| hand_back | thread | `ai_resumed` | `{"speaker": EVENT_SPEAKER, "line": render(TextId.AI_RESUMED, rep_name=name)}` |
| hand_back | case | `controller_changed` | `{"controller": {"kind": "ai", "display_name": None}, "line": render(TextId.AI_RESUMED, rep_name=name)}` |
| close | thread | `chat_closed` | `{"speaker": EVENT_SPEAKER, "line": render(TextId.CHAT_CLOSED, rep_name=name), "composer_disabled": True}` |
| close | case | `chat_closed` | `{"reason": "closed_by_staff"}` |

`case_events` row per action: `kind` ∈ `{"live_join", "live_send", "live_hand_back", "live_close"}`,
`actor_role = actor.role.value`, `detail = {"action": "<join|send|hand_back|close>"}`. For send the detail also holds
`"message_id": str(mid)`. **Never the text.**

---

## 5. Steps

The slice **implements** `LiveChatService` (staff.md §5) and the CON-14 and CON-21 operations. It **consumes**
`UnitOfWorkFactory` and the repositories in §4.1, `require_staff`, the providers in §4.3, `ResetGate`, `emit_record`,
`render` and `redact`. It adds no seam the design lacks. Dependency direction:
- `web/routes/staff_live.py` → `web/schemas/staff_live.py`, `web/deps.py`, `web/errors.py`, `web/logging.py`,
  `web/middleware.py` (the `RequestContext` type), `services/live_chat.py`, `services/reset_gate.py`,
  `ports/runtime.py` and `domain/`. It imports `adapters/sqlite/rows` **only under `TYPE_CHECKING`**.
- `services/live_chat.py` → `adapters/sqlite/rows` (row types, stream keys; DO-3 §2.1 allows it, and `services/ledger.py`
  is the precedent), `domain/`, `policy/texts`, `ports/runtime`.
- Only `web/container.py`'s own hunk imports `privacy.redact`.

### Step 0 — set up

`export UV_LINK_MODE=hardlink`. Work in the orchestrator's worktree on your own branch. Never copy a venv. Run the import
check only, with no baseline suite:
`uv run python -c "import meridian.web.app, meridian.web.deps, tests.api.web_shell_support, tests.fixtures.sqlite"`.
Re-read row A9 of `.claude/reference/area-map.md`.

### Step 1 — `src/meridian/services/live_chat.py`: types

Module docstring: `"""Live takeover (CON-14): a claiming representative joins, writes in, hands back or closes a live chat
(stage7/staff.md section 5; STF-11, STF-14, R-W-16). Each action is one write transaction and a refusal writes nothing.
Live actions never touch a case's lifecycle, version, owner or promise."""`

```python
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal
from zoneinfo import ZoneInfo

from pydantic import JsonValue

from meridian.adapters.sqlite.rows import CaseEventRow, ConversationRow, StreamEvent, case_stream, thread_stream
from meridian.domain.common import CaseRef, MeridianModel, ThreadId
from meridian.domain.staff import STAFF_PERSONAS, StaffActor
from meridian.domain.state import Controller
from meridian.policy.texts import TextId, render
from meridian.ports.runtime import Clock, UnitOfWork, UnitOfWorkFactory

LiveAction = Literal["join", "send", "hand_back", "close"]
LiveStateName = Literal["not_live", "queued", "joined", "handed_back", "closed"]
WIRE_ZONE: Final = ZoneInfo("America/Chicago")          # details times only (claimed_at)
EVENT_SPEAKER: Final[Mapping[str, JsonValue]] = {"kind": "event", "display_name": None}
_END_STATE: Final[Mapping[str, str]] = {"hand_back": "handed_back", "close": "closed"}
CASE_EVENT_KIND: Final[Mapping[str, str]] = {"join": "live_join", "send": "live_send",
                                              "hand_back": "live_hand_back", "close": "live_close"}

class StoredChatLine(MeridianModel):      # serialises to the OpenAPI ChatLine (speaker kind "representative")
    message_id: str                       # str() of core.messages.append's int id
    speaker_name: str                     # STAFF_PERSONAS[actor.role].name, "Riley"
    at: datetime                          # demo clock
    text: str                             # as stored (STORE-redacted)

class LiveView(MeridianModel):            # serialises to the OpenAPI LiveActionResponse
    controller_kind: Literal["ai", "human"]
    controller_name: str | None           # "Riley" or None
    state: LiveStateName
    since: datetime | None
    message: StoredChatLine | None = None # only for send

class LiveRefused(MeridianModel):
    code: Literal["CASE_NOT_FOUND", "NOT_CLAIMED_BY_YOU", "CASE_ALREADY_CLAIMED", "NOT_LIVE"]
    details: dict[str, str | None]        # {reference} | {owner} | {claimed_by, claimed_at} | {reason}

@dataclass(frozen=True)
class _Checked:                           # what a passing check hands to the write step
    case_ref: CaseRef
    thread_id: ThreadId
    conversation: ConversationRow
```

Private helpers, at module level:
- `def _wire(value: datetime | None) -> str | None`: returns `None` for `None`, else `value.astimezone(WIRE_ZONE).isoformat()`.
- `def _view(conv: ConversationRow) -> LiveView`: returns `LiveView(controller_kind=conv.controller.kind,
  controller_name=conv.controller.representative_name if conv.controller.kind == "human" else None,
  state=conv.live_state, since=conv.live_since)`.
- `def _refused(code, **details: str | None) -> LiveRefused`: returns `LiveRefused(code=code, details=dict(details))`.

### Step 2 — `LiveChatService`

```python
class LiveChatService:
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, redact_store: Callable[[str], str]) -> None
    def join(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused        # self._run("join", case_ref, actor, None)
    def send(self, case_ref: CaseRef, text: str, actor: StaffActor) -> LiveView | LiveRefused
    def hand_back(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused
    def close(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused
```

**`_run(action, case_ref, actor, text)`**, in order:
1. `with self._uow(write=True) as tx:`. BEGIN IMMEDIATE.
   *Protects:* two staff joining at once are serialised, so the second reads the first's result (staff.md §5).
2. `checked = self._check(tx, action, case_ref, actor)`.
3. If `checked` is a `LiveRefused` or a `LiveView`, `return checked` **without** `tx.commit()`. The block exit rolls back.
   *Protects:* a refusal or a repeat writes nothing and reads no clock (AC-2, AC-3).
4. `now = self._clock.now()`. This is the only clock read.
5. `view = self._write(tx, action, checked, actor, text, now)`, then `tx.commit()`, then `return view`.
   *Protects:* every write of one action commits together. If anything raises, the unit of work rolls everything back
   (AC-6). **Catch no exception in this method.**

**`_check(tx, action, case_ref, actor) -> LiveRefused | LiveView | _Checked`**. Run the staff.md §5 table in this exact order:
1. `owner = tx.core.cases_ro.owner(case_ref)`. If `owner is None` → `_refused("CASE_NOT_FOUND", reference=str(case_ref))`.
2. If `action == "join"`:
   - **row 2:** `owner.owner_role is None` → `_refused("NOT_CLAIMED_BY_YOU", owner=None)`;
   - **row 3:** `not actor.owns(owner.owner_role)` → `_refused("CASE_ALREADY_CLAIMED",
     claimed_by=STAFF_PERSONAS[owner.owner_role].name, claimed_at=_wire(owner.owner_since))`.
3. Else (send, hand_back, close), **row 4:** `not actor.owns(owner.owner_role)` (this includes no owner) →
   `_refused("NOT_CLAIMED_BY_YOU", owner=None if owner.owner_role is None else STAFF_PERSONAS[owner.owner_role].name)`.
4. `conv = tx.core.conversations.lookup(str(owner.thread_id))`. **Row 5 (defensive, MC-25):** if `not isinstance(conv,
   ConversationRow)` → `_refused("NOT_LIVE", reason="demo_reset")`. No test asserts this row.
5. `state = conv.live_state`. If `action == "join"`:
   - **row 6:** `state == "joined"` → `return _view(conv)`;
   - **row 7:** `state != "queued"` → `_refused("NOT_LIVE", reason="not_waiting")`.
6. Else, **row 8:** if `state != "joined"`:
   - `_END_STATE.get(action) == state` → `return _view(conv)`;
   - otherwise → `_refused("NOT_LIVE", reason="chat_closed" if state == "closed" else "not_joined")`.
7. `return _Checked(case_ref, owner.thread_id, conv)`.

**`_write(tx, action, c: _Checked, actor, text, now) -> LiveView`**. `name = actor.name`, `thread =
thread_stream(c.thread_id)`, `case = case_stream(c.case_ref)`, `detail: dict[str, JsonValue] = {"action": action}`.
Each event is `tx.core.events.append(<stream>, StreamEvent(type=…, payload=…, at=now))`, with the payloads from §4.6
**in the table's order**.

- **join**
  1. `tx.core.conversations.set_controller(c.thread_id, Controller(kind="human", representative_name=name,
     case_ref=c.case_ref), live_state="joined", live_since=now)`.
     *Protects:* PA-2; AEA-40 relays `customer_message` by `controller.case_ref`.
  2. Append `representative_joined` and `ai_paused` (thread), then `controller_changed` (case).
  3. `view = LiveView(controller_kind="human", controller_name=name, state="joined", since=now)`.
- **send**
  1. `if text is None: raise ValueError("send needs text")`. The route never passes `None`.
  2. `stored = self._redact_store(text)`.
  3. `mid = tx.core.messages.append(c.thread_id, "representative", stored, now)`.
  4. Append `staff_message` (thread). `detail["message_id"] = str(mid)`.
  5. `view = LiveView(controller_kind="human", controller_name=c.conversation.controller.representative_name or name,
     state="joined", since=c.conversation.live_since, message=StoredChatLine(message_id=str(mid), speaker_name=name,
     at=now, text=stored))`.
  *Protects:* the same `stored` string goes into the row, the event and the response (AC-7). The thread is the
  customer's own (AC-4).
- **hand_back**
  1. `set_controller(c.thread_id, Controller(kind="ai"), live_state="handed_back", live_since=now)`.
  2. Append `ai_resumed` (thread), then `controller_changed` ai (case).
  3. `view = LiveView(controller_kind="ai", controller_name=None, state="handed_back", since=now)`.
- **close**
  1. `set_controller(c.thread_id, Controller(kind="ai"), live_state="closed", live_since=now)`.
  2. Append `chat_closed` (thread), then `chat_closed {reason: closed_by_staff}` (case).
  3. `view = LiveView(controller_kind="ai", controller_name=None, state="closed", since=now)`.
- **Then, for every action:**
  1. `tx.cases.case_events.append(CaseEventRow.model_validate({"case_ref": c.case_ref, "kind":
     CASE_EVENT_KIND[action], "actor_role": actor.role.value, "detail": detail, "at": now}))`.
  2. `return view`.

`model_validate` keeps mypy happy with the `actor_role` Literal. Use `dict(EVENT_SPEAKER)` where a payload needs it, so
each payload holds its own dict.

**Invariants the code must keep:**
- `controller.kind == "human"` exactly when `live_state == "joined"`.
- No call touches `tx.cases.cases`, `tx.cases.promises` or `case_changed` (R-W-16, AC-21).
- No `CaseService` import.
- No logging anywhere in this module.

Check: `uv run ruff check src/meridian/services/live_chat.py && uv run mypy src/meridian/services/live_chat.py`.

### Step 3 — `src/meridian/web/schemas/staff_live.py`

Module docstring: `"""Wire shapes for CON-14 liveChatAction and CON-21 streamCaseEvents (OpenAPI LiveActionRequest,
LiveActionResponse, CaseEvent; stage7/staff.md sections 5 to 7). CON-21 keeps its own frame encoder (DO-3 S-11):
nothing here is shared with web/schemas/events.py."""`

```python
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Final, Literal, Protocol, get_args
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError

from meridian.policy.limits import TurnLimits
from meridian.services.live_chat import LiveView

MAX_LIVE_TEXT_CHARS: Final = TurnLimits().max_message_chars          # 2000: the customer's limit (STF-12)
MAX_EVENT_ID_DIGITS: Final = 18
WIRE_ZONE: Final = ZoneInfo("America/Chicago")
CaseEventType = Literal["customer_message", "controller_changed", "chat_closed", "demo_reset", "case_changed"]
CASE_EVENT_TYPES: Final[frozenset[str]] = frozenset(get_args(CaseEventType))
CLOSING_CASE_EVENT_TYPES: Final[frozenset[str]] = frozenset({"demo_reset"})   # NOT chat_closed (staff.md section 7, step 6)
RESERVED_KEYS: Final[tuple[str, ...]] = ("event_id", "type", "at")
HEARTBEAT_FRAME: Final[bytes] = b": heartbeat\n\n"
```

1. **`class LiveActionRequest(BaseModel)`**: `model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)`.
   This is a plain `BaseModel`, like AEA-23's `LoginRequest`: the OpenAPI schema has no `additionalProperties: false`,
   and the validator strips the text itself.
   - Fields, in this order: `action: Literal["join", "send", "hand_back", "close"]`, then
     `text: str | None = Field(default=None, validate_default=True)`.
   - `@field_validator("text", mode="after")` `@classmethod def _text_rules(cls, value: str | None, info: ValidationInfo)
     -> str | None`:
     1. `action = info.data.get("action")`. If `action is None`, `return value`: the action already failed and its
        error is reported first (AC-10).
     2. If `action != "send"`: when `value is not None`, raise `PydanticCustomError("live_text", "only for send")`;
        otherwise `return None`.
     3. `stripped = (value or "").strip()`. If it is empty, raise `PydanticCustomError("live_text", "required for send")`.
     4. If `len(stripped) > MAX_LIVE_TEXT_CHARS`, raise `PydanticCustomError("live_text",
        f"at most {MAX_LIVE_TEXT_CHARS} characters")`.
     5. `return stripped`.
   - *Protects:* the 422 handler turns this into 400 `VALIDATION_ERROR` with field `text` and constraint exactly
     "required for send", "at most 2000 characters" or "only for send". It reads only `loc`, `type` and `msg`, so the
     value is never echoed.
2. Response models (all `BaseModel`, `ConfigDict(extra="forbid")`):
   - `SpeakerOut`: `kind: Literal["representative"]; display_name: str`
   - `ChatLineOut`: `message_id: str; speaker: SpeakerOut; at: str; text: str`
   - `ControllerOut`: `kind: Literal["ai","human"]; display_name: str | None`
   - `LiveStateOut`: `state: Literal["not_live","queued","joined","handed_back","closed"]; since: str | None;
     controller: Literal["ai","human"]`
   - `LiveActionResponse`: `controller: ControllerOut; live: LiveStateOut; message: ChatLineOut | None`
3. `def wire_time(value: datetime) -> str`: `return value.astimezone(WIRE_ZONE).isoformat()`.
4. `def live_action_response(view: LiveView) -> LiveActionResponse`:
   - `controller = ControllerOut(kind=view.controller_kind, display_name=view.controller_name)`;
   - `live = LiveStateOut(state=view.state, since=None if view.since is None else wire_time(view.since),
     controller=view.controller_kind)`;
   - `message = None`, or `ChatLineOut(message_id=m.message_id, speaker=SpeakerOut(kind="representative",
     display_name=m.speaker_name), at=wire_time(m.at), text=m.text)`.
5. `class StoredCaseEvent(Protocol)`: read-only properties `id: int`, `type: str`, `payload: Mapping[str, JsonValue]`,
   `at: datetime`. AEA-10's `EventRow` satisfies it.
6. `def case_event_data(event: StoredCaseEvent) -> dict[str, JsonValue]`:
   - start from `{"event_id": event.id, "type": event.type, "at": wire_time(event.at)}`;
   - add each `(k, v)` of `event.payload` **in its stored order** where `k not in RESERVED_KEYS`;
   - never change a value.
7. `def encode_case_frame(event: StoredCaseEvent) -> bytes`:
   - `data = json.dumps(case_event_data(event), ensure_ascii=False, separators=(",", ":"))`;
   - `return f"id: {event.id}\nevent: {event.type}\ndata: {data}\n\n".encode("utf-8")`.
8. `def parse_last_event_id(raw: str | None) -> int | None`:
   - `None` → `None`;
   - otherwise `value = raw.strip()`; return `int(value)` only if `value.isascii() and value.isdigit() and 1 <=
     len(value) <= MAX_EVENT_ID_DIGITS`; anything else → **`None`** ("as if not sent", PA-5).

No clock read, no `datetime.now`. Check: `uv run ruff check src/meridian/web/schemas/staff_live.py && uv run mypy src/meridian/web/schemas/staff_live.py`.

### Step 4 — `src/meridian/web/routes/staff_live.py`

Module docstring: `"""CON-14 liveChatAction (a def route) and CON-21 streamCaseEvents (an async SSE route with its own
generator; DO-3 S-11). stage7/staff.md sections 5 to 7 and 11. The route files read no clock; poll and heartbeat are
this file's own copies of web.md section 11's values."""`

Runtime imports: `functools`, `re`, `time`, `collections.abc` (`AsyncIterator`, `Awaitable`, `Callable`, `Sequence`),
`typing` (`TYPE_CHECKING`, `Final`, `cast`), `anyio`, `fastapi` (`APIRouter`, `Depends`, `Request`),
`fastapi.responses.JSONResponse`, `starlette.responses.StreamingResponse`, `meridian.domain.common` (`ApiErrorCode`,
`CaseRef`), `meridian.domain.staff` (`StaffActor`, `StaffRole`), `meridian.ports.runtime.UnitOfWorkFactory`,
`meridian.services.live_chat` (`LiveChatService`, `LiveRefused`), `meridian.services.reset_gate.ResetGate`,
`meridian.web.deps` (`get_live_chat`, `get_request_context`, `get_reset_gate`, `get_stream_poll_limiter`,
`get_uow_factory`, `require_staff`), `meridian.web.errors.ApiProblem`, `meridian.web.logging` (`STREAM_LOGGER`,
`emit_record`), `meridian.web.middleware.RequestContext`, `meridian.web.schemas.staff_live` (Step 3 names).
Under `if TYPE_CHECKING:` only: `from meridian.adapters.sqlite.rows import EventRow, StreamKey`.

```python
STREAM_POLL_S = 1.0          # [A] web.md section 11 / DO-3 S-11; this file's own copy (AC-19). Tests patch it.
STREAM_HEARTBEAT_S = 15.0    # [Source: OpenAPI streamChatEvents "Heartbeat comment every 15 s"; web.md section 11]
LIVE_PATH: Final = "/api/staff/cases/{reference}/live"
EVENTS_PATH: Final = "/api/staff/cases/{reference}/events"
LAST_EVENT_ID_HEADER: Final = "last-event-id"
STATUS_BY_CODE: Final[Mapping[str, int]] = {"CASE_NOT_FOUND": 404, "NOT_CLAIMED_BY_YOU": 403,
                                            "CASE_ALREADY_CLAIMED": 409, "NOT_LIVE": 409}
_LIVE_ROLES = require_staff(StaffRole.REPRESENTATIVE)                                        # x-roles of liveChatAction
_STREAM_ROLES = require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR, StaffRole.OWNER)  # x-roles of streamCaseEvents, in order
```
Keep the poll and heartbeat as **plain module globals** (no `Final`), read inside the endpoint at request time, so
`monkeypatch.setattr(staff_live, "STREAM_HEARTBEAT_S", 0.05)` works.

1. `def parse_case_ref(reference: str) -> CaseRef | None`: `CaseRef(reference) if re.fullmatch(CaseRef.PATTERN,
   reference) else None`.
2. `def case_stream_key(case_ref: CaseRef) -> StreamKey`: `return cast("StreamKey", "case:" + str(case_ref))`.
   It must equal `rows.case_stream(case_ref)` (a unit test proves it). *This keeps adapters out of `web/` at run time,
   as AEA-41 does.*
3. `def read_case_events(uow: UnitOfWorkFactory, stream: StreamKey, last: int | None) -> tuple[int, list[EventRow]]`
   (sync; it runs on a worker thread):
   ```python
   with uow(write=False) as tx:
       if last is None:
           found = tx.core.events.latest_of(stream, "demo_reset")
           last = 0 if found is None else found
       return last, tx.core.events.after(stream, last)
   ```
   *Protects:* MC-8. With no header, the start is the newest `demo_reset`, resolved in the same read unit as the
   first `after`, so nothing is missed between the two reads.
4. **The poll loop:**
   ```python
   async def case_event_frames(*, start: int | None,
       read_after: Callable[[int | None], Awaitable[tuple[int, Sequence[StoredCaseEvent]]]],
       reset_held: Callable[[], bool], disconnected: Callable[[], Awaitable[bool]],
       poll_s: float, heartbeat_s: float, on_replayed: Callable[[int], None] | None,
       monotonic: Callable[[], float] = time.monotonic,
       sleep: Callable[[float], Awaitable[None]] = anyio.sleep) -> AsyncIterator[bytes]
   ```
   Write exactly this order:
   1. `last: int | None = start`; `reported = on_replayed is None`; `last_sent_at = monotonic()`.
   2. `try:` wraps steps 3–9; step 10 is the `finally`.
   3. `while True:`
   4. `if await disconnected(): return`.
   5. `if not reset_held():` do steps 6–8.
      *Protects:* while a reset holds the gate, no read touches SQLite, and the stream neither waits nor answers 503
      (AC-16).
   6. Read and encode:
      - `last, rows = await read_after(last)`; then `frames: list[bytes] = []` and `closing = False`.
      - For each `row` in order:
        - `last = row.id`. *Protects:* `last` moves past every row, skipped ones included.
        - `if row.type not in CASE_EVENT_TYPES: continue`.
        - `frames.append(encode_case_frame(row))`.
        - `if row.type in CLOSING_CASE_EVENT_TYPES: closing = True; break`.
   7. `if not reported:` set `reported = True`, then `if on_replayed is not None: on_replayed(len(frames))`.
   8. Send:
      - `for frame in frames: yield frame`.
      - `if frames: last_sent_at = monotonic()`.
      - `if closing: return`.
      *Protects:* the stream closes after `demo_reset` and only after it. `chat_closed` keeps it open (AC-14).
   9. Heartbeat and sleep:
      - `if monotonic() - last_sent_at >= heartbeat_s: yield HEARTBEAT_FRAME; last_sent_at = monotonic()`.
      - `await sleep(poll_s)`.
      *Protects:* the first read happens at t = 0.
   10. `finally:` `if not reported and on_replayed is not None: on_replayed(0)`. **No `await` in this `finally`.**

   Catch no exception in the loop. A failing read ends the stream and the browser reconnects with its last id.
   `CancelledError` must propagate.
5. **The existence check** (a sync dependency, so FastAPI runs it on a worker thread, not the loop):
   ```python
   def known_case(reference: str, uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
                  gate: ResetGate = Depends(get_reset_gate)) -> CaseRef:  # noqa: B008
   ```
   1. `ref = parse_case_ref(reference)`. If it is `None` → `raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND)`
      (details `None`: the malformed value is never echoed; PA-4).
   2. `if gate.held(): return ref`. *Protects:* staff.md §11 says the stream never waits on connect. During a reset,
      the existence read is skipped and the stream's first poll after the reset sees the post-reset state.
   3. `with uow(write=False) as tx: found = tx.core.cases_ro.owner(ref)`. If `found is None` → `raise ApiProblem(404,
      ApiErrorCode.CASE_NOT_FOUND, details={"reference": str(ref)})`.
   4. `return ref`.
6. **CON-14:**
   ```python
   def live_chat_action(reference: str, body: LiveActionRequest,
                        actor: StaffActor = Depends(_LIVE_ROLES),  # noqa: B008
                        live_chat: LiveChatService = Depends(get_live_chat)) -> JSONResponse:  # noqa: B008
   ```
   1. `ref = parse_case_ref(reference)`. `None` → `raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND)`.
   2. Dispatch on `body.action`:
      - `"join"` → `live_chat.join(ref, actor)`;
      - `"send"` → if `body.text is None`, `raise ApiProblem(400, ApiErrorCode.VALIDATION_ERROR, field="text",
        constraint="required for send")` (unreachable, defensive); otherwise `live_chat.send(ref, body.text, actor)`;
      - `"hand_back"` → `live_chat.hand_back(ref, actor)`;
      - `"close"` → `live_chat.close(ref, actor)`.
   3. A `LiveRefused` → `raise ApiProblem(STATUS_BY_CODE[result.code], ApiErrorCode(result.code),
      details=dict(result.details))`.
   4. Otherwise `return JSONResponse(live_action_response(result).model_dump(mode="json"))`.

   No logging. FastAPI resolves `actor` (403) before validating the body (400), so a wrong role never reaches validation.
7. **CON-21:**
   ```python
   async def stream_case_events(request: Request,
       actor: StaffActor = Depends(_STREAM_ROLES),  # noqa: B008     ← declared FIRST: 403 before any read (AC-12)
       case_ref: CaseRef = Depends(known_case),  # noqa: B008
       context: RequestContext = Depends(get_request_context),  # noqa: B008
       uow: UnitOfWorkFactory = Depends(get_uow_factory),  # noqa: B008
       limiter: anyio.CapacityLimiter = Depends(get_stream_poll_limiter),  # noqa: B008
       gate: ResetGate = Depends(get_reset_gate)) -> StreamingResponse:  # noqa: B008
   ```
   1. `start = parse_last_event_id(request.headers.get(LAST_EVENT_ID_HEADER))`.
   2. `stream = case_stream_key(case_ref)`.
   3. Define the reader:
      ```python
      async def read_after(last: int | None) -> tuple[int, Sequence[StoredCaseEvent]]:
          return await anyio.to_thread.run_sync(functools.partial(read_case_events, uow, stream, last), limiter=limiter)
      ```
      - `read_case_events` is looked up as a module global at call time, so tests can monkeypatch it.
      - Keep the default `abandon_on_cancel=False`, so a cancelled stream returns its limiter token.
      *Protects:* every poll read runs under the one process-wide `CapacityLimiter(4)` (AC-15).
   4. `on_replayed`: when `start is not None and start > 0`, a closure that calls `emit_record(STREAM_LOGGER,
      {"record": "stream_reconnect", "request_id": str(context.request_id), "case_ref": str(case_ref),
      "last_event_id": start, "replayed": replayed})`; otherwise `None`. IDs and counts only.
   5. `return StreamingResponse(case_event_frames(start=start, read_after=read_after, reset_held=gate.held,
      disconnected=request.is_disconnected, poll_s=STREAM_POLL_S, heartbeat_s=STREAM_HEARTBEAT_S,
      on_replayed=<closure or None>), media_type="text/event-stream", headers={"Cache-Control": "no-store"})`.
      The middleware adds `X-Request-ID`.
8. **The router:**
   ```python
   def build_router() -> APIRouter:
       router = APIRouter()
       router.add_api_route(LIVE_PATH, live_chat_action, methods=["POST"], operation_id="liveChatAction", response_model=None)
       router.add_api_route(EVENTS_PATH, stream_case_events, methods=["GET"], operation_id="streamCaseEvents", response_model=None)
       return router
   ```
   The path strings must equal the middleware's `OPERATIONS_BY_ROUTE` keys, including the parameter name `reference`.

Check: ruff, mypy on the file, and the AC-19 grep (§7).

### Step 5 — unit tests first: `tests/unit/web/test_staff_live_units.py`

These need no app. Every async case is a plain sync test that calls `anyio.run(scenario)`; add no new pytest plugin.

- `test_text_rules_table`: `LiveActionRequest.model_validate` over these cases:
  - `{"action": "send", "text": None}` → errors()[0] `loc == ("text",)`, `msg == "required for send"`;
  - `"   "` → the same;
  - `"a" * 2001` → `"at most 2000 characters"`;
  - `{"action": "join", "text": "zq…"}` → `"only for send"`;
  - `{"action": "send", "text": "  hi  "}` → `.text == "hi"`;
  - `{"action": "join"}` → `.text is None`;
  - `{"action": "wave"}` → `loc == ("action",)`;
  - also assert `MAX_LIVE_TEXT_CHARS == 2000`.
- `test_wp2_bodies_equal_openapi_examples` (PA-7, the WP-2 worked pair at unit level). Read `load_document()["paths"]
  ["/api/staff/cases/{reference}/live"]["post"]["responses"]["200"]["content"]["application/json"]["examples"]`.
  For each of JOINED, SENT, HANDED_BACK and CLOSED, build the matching `LiveView` and assert
  `live_action_response(view).model_dump(mode="json") == example["value"]`:
  - JOINED: since `2026-10-16 14:22` Chicago;
  - SENT: message `StoredChatLine(message_id="m-88", speaker_name="Riley", at=14:22:40, text=STAFF_TEXT)`;
  - HANDED_BACK: since 14:22;
  - CLOSED: since 14:23.
- `test_case_frames_equal_openapi_example` (PA-7):
  - read the `streamCaseEvents` 200 `FRAMES` example text;
  - build two simple objects satisfying `StoredCaseEvent` (a frozen dataclass in the test): id 5, `customer_message`,
    at 14:23:10 Chicago, payload = the example's `message` object in the example's key order; and id 6,
    `chat_closed`, at 14:24, payload `{"reason": "closed_by_staff"}`;
  - assert `(encode_case_frame(a) + encode_case_frame(b)).decode()` equals the example text (strip one trailing `\n`
    if YAML `|+` adds it; compare after `rstrip("\n")` on both).
- `test_parse_last_event_id`: `None`→`None`, `"30"`→30, `" 7 "`→7, `"0"`→0; each of `"abc"`, `"-3"`, `"12abc"`, `"+5"`,
  `""` and `"9" * 19` → `None`.
- `test_parse_case_ref`: `"MHC-C-0007"` → `"MHC-C-0007"`; each of `"mhc-c-0007"`, `"MHC-C-7"` and `"MHC-C-00071"` → `None`.
- `test_case_stream_key_matches_rows`: `case_stream_key(CaseRef("MHC-C-0007")) == rows.case_stream(CaseRef("MHC-C-0007"))
  == "case:MHC-C-0007"`.
- Loop tests. They drive `case_event_frames` with a fake `read_after`, `reset_held`, `disconnected` and a
  `FakeTime(monotonic, sleep)` whose `sleep` advances the clock and awaits `anyio.lowlevel.checkpoint()`:
  - `test_loop_skips_reads_while_held`: held for 3 polls → 0 reads, then released → 1 read. Never raises or emits
    anything but heartbeats.
  - `test_loop_closes_after_demo_reset_not_chat_closed`:
    - rows `[chat_closed id 1, case_changed id 2]` → both yielded and the loop continues (it reads again);
    - rows `[demo_reset id 3, case_changed id 4]` → only id 3, then the generator ends.
  - `test_loop_skips_foreign_types_and_advances`: a row of type `staff_message` id 7 is not yielded; the next
    `read_after` call receives `last == 7`.
  - `test_loop_heartbeat_after_idle`: with heartbeat 15 and poll 1, no rows → the first item after 15 fake seconds is
    `HEARTBEAT_FRAME`, and none earlier.
  - `test_start_none_resolved_by_first_read`: `read_after(None)` returns `(12, [])`; the next call receives `12`.
  - `test_on_replayed_called_once`: two reads → `on_replayed` called once, with the first read's frame count; a
    generator closed before any read (held) calls it once with 0.

Run: `uv run pytest tests/unit/web/test_staff_live_units.py -q`.

### Step 6 — test support: `tests/services/live_chat_support.py`

Docstring: `"""AEA-46 test support: synthetic seed rows for a live-queued case, a snapshot of everything a live action may
write, and a stand-in for AEA-40's relayed customer message. Not a conftest; other tickets may import it read-only."""`

```python
WP2_REF = CaseRef("MHC-C-0007")            # WP-2, Omar Patel's case in the worked pair
SECOND_REF = CaseRef("MHC-C-0011")         # a second synthetic case (two-case sequences, §8 R-7)
UNKNOWN_REF = CaseRef("MHC-C-0099")        # the OpenAPI CASE_NOT_FOUND example
WP2_CUSTOMER = CustomerId("MHC-10002")     # issued, fictional (worked-pairs.md WP-2)
QUEUED_AT = datetime(2026, 10, 16, 14, 20, tzinfo=CHICAGO)   # case claimed and queued
JOIN_AT = datetime(2026, 10, 16, 14, 22, tzinfo=CHICAGO)     # OpenAPI JOINED example time; the FixedClock for actions
STAFF_TEXT = "Hi Omar, I can look at the after-hours charge with you."
CUSTOMER_REPLY = "Thanks, that helps."
EVENT_SPEAKER = {"kind": "event", "display_name": None}
RILEY = actor_for(StaffRole.REPRESENTATIVE)
SUPERVISOR = actor_for(StaffRole.SUPERVISOR)

def store_redactor(text: str) -> str: return redact(text, RedactionProfile.STORE).text   # = the container's binding (MC-23)
def new_service(uow: UnitOfWorkFactory, at: datetime = JOIN_AT) -> LiveChatService:
    return LiveChatService(uow, FixedClock(at), store_redactor)

@dataclass(frozen=True)
class SeededCase:
    case_ref: CaseRef; thread_id: ThreadId; version: int

def seed_live_case(uow, *, case_ref: CaseRef = WP2_REF, owner_role: StaffRole | None = StaffRole.REPRESENTATIVE,
                   live_state: str = "queued", lifecycle: str = "claimed", version: int = 1,
                   session_id: str = "seed-session") -> SeededCase
```
`seed_live_case` runs in one write unit:
- `tid = ThreadId(str(uuid.uuid4()))`;
- conversation: `ConversationRow(thread_id=tid, demo_session=session_id, run_tag="live", agent_version="test-agent-0",
  started_at=QUEUED_AT, live_state=live_state, live_since=None if live_state == "not_live" else QUEUED_AT,
  controller=Controller(kind="human", representative_name="Riley", case_ref=case_ref) if live_state == "joined" else
  Controller(kind="ai"))`;
- two messages: `("assistant", "Hi, I'm Meridian's automated assistant.")` and
  `("customer", "Can I talk to a person about the after-hours charge?")`, both at `QUEUED_AT`;
- `CaseRow(case_ref=case_ref, thread_id=tid, customer_id=WP2_CUSTOMER, reason=HandoffReason.BILLING_DISPUTE,
  priority=Priority.P2, rule_id="R-test", trigger="customer_requested", lifecycle=lifecycle, owner_role=owner_role,
  owner_since=QUEUED_AT if owner_role else None, version=version, created_at=QUEUED_AT, updated_at=QUEUED_AT)`;
- one promise: `Promise(policy_row="P-test", text="A representative will join this chat shortly.", due_at=None,
  due_label=None, live_queued=True)` at `QUEUED_AT`;
- `commit`, then return `SeededCase(case_ref, tid, version)`.

Other helpers:
- `def snapshot(uow, seeded: SeededCase) -> dict[str, object]`: in one read unit, model dumps of:
  - `lookup(str(tid))`;
  - `messages.all_for_thread(tid)`;
  - `events.after(thread_stream(tid), 0)` and `events.after(case_stream(ref), 0)`;
  - `case_events.list_for_case(ref)`;
  - `cases.get(ref)`;
  - `promises.history(ref)`.
- `def invariant_holds(uow, seeded) -> bool`: `conv.controller.kind == "human"` ⇔ `conv.live_state == "joined"`.
- `def append_customer_reply(uow, seeded, text: str, at: datetime) -> int`:
  - **a stand-in for AEA-40 `TurnService` step 4 (web.md §9) until it merges**;
  - in one write unit: `mid = messages.append(tid, "customer", text, at)`;
  - `events.append(case_stream(ref), StreamEvent(type="customer_message", payload={"message": {"message_id": str(mid),
    "speaker": {"kind": "customer", "display_name": CUSTOMER_SPEAKER_NAME}, "at": at.isoformat(), "text": text}},
    at=at))`;
  - commit and return `mid`.
- `def card_like_and_code(seed: int = 46) -> tuple[str, str]`: `rng = random.Random(seed)`; a 16-digit string grouped
  in fours by single spaces, and `str(rng.randint(100000, 999999))`. Built at run time. **No digit literal in any test
  file** (rule: no card-like numbers or codes in tests).

### Step 7 — `tests/services/test_live_chat.py` (AC-1…AC-8, AC-21)

Each test uses `with temp_sqlite() as db:` and `svc = new_service(db.uow)`.

- **`test_join_writes_one_transaction` (AC-1, PA-2).**
  - Seed queued and take a snapshot; `svc.join(WP2_REF, RILEY)` returns `LiveView(controller_kind="human",
    controller_name="Riley", state="joined", since=JOIN_AT, message=None)`.
  - Conversation: controller human, `representative_name == "Riley"`, `case_ref == WP2_REF`, `live_state == "joined"`,
    `live_since == JOIN_AT`.
  - Thread stream types `["representative_joined", "ai_paused"]`; case stream `["controller_changed"]`; the three ids
    strictly ascending.
  - `case_events` has one row: `kind "live_join"`, `actor_role "representative"`, `detail == {"action": "join"}`.
  - The case row and the promise history are unchanged against the snapshot. Print the rows.
- **`test_checks_in_order_write_nothing` (AC-2).** `@pytest.mark.parametrize` over seven cases. Each seeds, snapshots,
  calls, and asserts the result plus `snapshot == before`. Cases (seed → call → expected):
  1. no seed → `join(UNKNOWN_REF)` → `CASE_NOT_FOUND {"reference": "MHC-C-0099"}`;
  2. `owner_role=None` → `join` → `NOT_CLAIMED_BY_YOU {"owner": None}`;
  3. `owner_role=SUPERVISOR` → `join` → `CASE_ALREADY_CLAIMED {"claimed_by": "Demo supervisor", "claimed_at":
     "2026-10-16T14:20:00-05:00"}`;
  4. `owner_role=SUPERVISOR, live_state="joined"` → `send(…, "x", RILEY)` → `NOT_CLAIMED_BY_YOU {"owner": "Demo supervisor"}`;
  5. `live_state="not_live"` → `join` → `NOT_LIVE {"reason": "not_waiting"}`;
  6. queued → `send` → `NOT_LIVE {"reason": "not_joined"}`;
  7. `live_state="closed"` → `send` → `NOT_LIVE {"reason": "chat_closed"}`.

  Add a comment: row 5 is defensive and untested (MC-25).
- **`test_repeats_write_nothing` (AC-3).** Each case seeds, snapshots, calls, then asserts the view and that the
  snapshot is unchanged:
  - joined (controller human): `join` → view state `joined`, controller human "Riley";
  - `handed_back`: `hand_back` → view state `handed_back`, controller ai;
  - `closed`: `close` → state `closed`.
- **`test_send_same_thread` (AC-4).**
  1. Seed queued; `join`; `view = svc.send(WP2_REF, STAFF_TEXT, RILEY)`.
  2. The newest `messages` row has `thread_id == seeded.thread_id`, `role "representative"`, `text == STAFF_TEXT` and
     `at == JOIN_AT`.
  3. `view.message == StoredChatLine(message_id=str(row.id), speaker_name="Riley", at=JOIN_AT, text=STAFF_TEXT)`.
  4. A `staff_message` event exists on the thread stream; a `case_events` row has `kind "live_send"` and
     `detail["message_id"] == str(row.id)`.
- **`test_hand_back_close_and_controller_invariant` (AC-5, PA-6).**
  - Case A (`WP2_REF`): `join` → invariant; `send` → invariant; then `hand_back` with
    `new_service(db.uow, JOIN_AT + 1 min)` →
    - live `handed_back`, `live_since == JOIN_AT + 1 min`, controller ai;
    - thread gains `ai_resumed`;
    - case stream `["controller_changed", "controller_changed"]`, the second's payload controller
      `{"kind": "ai", "display_name": None}`;
    - invariant holds.
  - Case B (`SECOND_REF`): `join` → `close` (at +2 min) →
    - live `closed`, since +2 min, controller ai;
    - thread last event `chat_closed` with `composer_disabled is True`;
    - case stream last `chat_closed` with payload `{"reason": "closed_by_staff"}`;
    - invariant holds after each action.
- **`test_live_action_rolls_back` (AC-6).**
  1. Seed queued and snapshot.
  2. `monkeypatch.setattr(repos_core_aux.EventsRepo, "append", boom)` where `boom` raises `RuntimeError("injected")`.
  3. `pytest.raises(RuntimeError)` on `join`.
  4. `monkeypatch.undo()`, then `snapshot == before`.
- **`test_staff_message_store_redacted` (AC-7).**
  1. `card, code = card_like_and_code()`; `text = f"My card is {card} and the code {code}, please"`.
  2. Seed, `join`, `view = send(…, text, RILEY)`.
  3. The message row text, the `staff_message` payload text and `view.message.text` each contain
     `"[card number removed]"` and `"[code]"`.
  4. None of them contains `card`, `card.replace(" ", "")` or `code`.
- **`test_two_sessions_share_riley` (AC-8; app level).**
  1. `store = FakeSessionStore()`; `a = store.issue(DemoRole.REPRESENTATIVE)`; `b = store.issue(DemoRole.REPRESENTATIVE)`.
  2. `app = staff_live_app(monkeypatch, tmp_path, store=store)`; `with make_client(app) as c:` seed queued through
     `app_uow(app)` ("claimed through one login session" = `owner_role` representative).
  3. B posts join → 200, and `assert_matches(r, "liveChatAction")`; `r.json()["controller"]["display_name"] == "Riley"`.
  4. A posts `send` → 200 (the same Riley).
- **`test_live_actions_keep_case_version` (AC-21).**
  1. Seed case A with `version=3` and case B with `version=5`, both `lifecycle="claimed"`.
  2. A: `join`, `send`, `hand_back`. B: `join`, `close`.
  3. Afterwards: `cases.get(...).version` is 3 and 5; `lifecycle == "claimed"`; case-stream types A
     `["controller_changed", "controller_changed"]`, B `["controller_changed", "chat_closed"]`; no `case_changed`
     anywhere (print the types).
  4. Then `ResolveDouble(db.uow).apply(WP2_REF, "resolve", RILEY, expected_version=3, now=JOIN_AT)` returns 4
     (accepted).
  5. A second `apply` with `expected_version=3` returns `"VERSION_CONFLICT"`. This proves the double really checks.

  The double (defined in this test file) honours cases.md §5 / DO-4 §13 `apply`:
  ```python
  class ResolveDouble:
      """Stand-in for AEA-29 CaseService.apply (resolve only): one write unit; update_versioned(case_ref,
      expected_version, lifecycle="resolved", resolved_at=now, updated_at=now); None → "VERSION_CONFLICT"; else append
      case_changed {"version": v, "lifecycle": "resolved"} to the case stream, commit, return v."""
  ```
  Replace it with AEA-29's `CaseService` once that merges (§8 R-6).

Run: `uv run pytest tests/services/test_live_chat.py -q`.

**`tests/services/test_live_chat_events.py`** (PA-2, PA-3):
- `test_join_sets_case_ref_for_relay`: after `join`, `append_customer_reply(…)` written to
  `case_stream(conv.controller.case_ref)` lands on `case:MHC-C-0007` (the AEA-40 rule).
- `test_thread_events_validate_as_chat_events`:
  1. Run join, send, hand_back on case A and join, close on case B.
  2. For every thread-stream row, build `SseFrame(event=row.type, id=str(row.id), data=json.dumps({"event_id": row.id,
     "type": row.type, "at": row.at.isoformat(), **row.payload}))`.
  3. `assert_sse_frames_match(frames, "streamChatEvents")`. This is AEA-41's rendering rule.
- `test_case_events_validate_as_case_events`: the same over both case streams with
  `assert_sse_frames_match(frames, "streamCaseEvents")`.

### Step 8 — the hunk: `register_staff_live` in `src/meridian/web/container.py` (this function only)

New docstring. Keep "AEA-46"; it must **not** contain "No-op until":

> AEA-46 staff API: LiveChatService, CON-14 and CON-21 routes (staff.md §5, §7). Provides deps.LIVE_CHAT ("live_chat"):
> a LiveChatService over Key("uow_factory") (AEA-10), the demo clock Key("demo_clock") (AEA-30, read through a forwarder
> only when an action writes, so the app builds before AEA-30 binds it; until then a write raises RuntimeError("not
> bound: demo_clock")) and the STORE redactor (data.md §1, MC-23). Includes the staff_live router once per app. An app
> that create_app did not build has no web shell, so this does nothing.

Body. All imports go **inside** the function: `test_import_direction.py::test_container_imports_only_policy_limits`
checks the module-level block.

```python
    from datetime import datetime

    from meridian.privacy.redact import RedactionProfile, redact
    from meridian.services.live_chat import LiveChatService
    from meridian.web.deps import LIVE_CHAT, UOW_FACTORY
    from meridian.web.middleware import WebShellState
    from meridian.web.routes.staff_live import build_router

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    demo_clock_key: Key[Any] = Key("demo_clock")

    class _DemoClock:
        """Resolves AEA-30's clock at call time (AEA-40 and AEA-42 use the same forwarder)."""

        def now(self) -> datetime:
            try:
                clock = container.get(demo_clock_key)
            except ContainerError as exc:
                if str(exc) == f"not provided: {demo_clock_key.name}":
                    raise RuntimeError(f"not bound: {demo_clock_key.name}") from None
                raise
            moment: datetime = clock.now()
            return moment

    container.provide(
        LIVE_CHAT,
        lambda c: LiveChatService(c.get(UOW_FACTORY), _DemoClock(), lambda t: redact(t, RedactionProfile.STORE).text),
    )
    if not getattr(app.state, "staff_live_router_included", False):
        app.include_router(build_router())
        app.state.staff_live_router_included = True
```

The guard flag stops duplicate routes when one app's lifespan builds twice. Change no other line of the file.

Run: `uv run pytest tests/unit/web/test_container.py tests/unit/test_import_direction.py -q`.

### Step 9 — `tests/api/staff_live_support.py`

Docstring: `"""AEA-46 test support: the app builder, an in-process ASGI stream harness (pattern from AEA-41's branch, copied:
no import from an unmerged file), and a recording LiveChatService double. Synthetic, socket-free, no .env, no paid
call."""`

**App builders:**
- `def staff_live_app(monkeypatch, tmp_path, *, store: FakeSessionStore, live_chat: object | None = None,
  at: datetime = JOIN_AT) -> FastAPI`:
  1. `settings = make_settings(tmp_path, issued_db_path=ISSUED_DB)`.
  2. `app = full_app(monkeypatch, settings, store=store, heartbeat=FakeHeartbeat())`. This is the **real**
     `build_container`, so the hunk includes the router.
  3. `app.dependency_overrides[get_live_chat]` is either `lambda: live_chat` (a double), or
     `lambda: LiveChatService(provided(app, get_uow_factory), FixedClock(at), store_redactor)`. The real service
     replaces only AEA-30's still-unbound clock.
  4. `return app`.
- `def app_uow(app: FastAPI) -> UnitOfWorkFactory`: `return provided(app, get_uow_factory)`. Call it only while the
  lifespan runs.
- `def fast_stream(monkeypatch, *, poll_s: float = 0.01, heartbeat_s: float = 0.05) -> None`: monkeypatches
  `meridian.web.routes.staff_live.STREAM_POLL_S` and `STREAM_HEARTBEAT_S`.
- `def live_url(ref: str) -> str` and `def events_url(ref: str) -> str`.

**`class RecordingLiveChat`.** It records `calls: list[tuple[str, str]]` as (method, case_ref) and returns the
configured `result: LiveView | LiveRefused` for every method. It never stores text: `send` records only `("send", ref)`.

**In-process ASGI stream harness.** Copy this, adapted from AEA-41's branch (`tests/api/events_support.py` at `fc5314b`;
it is proven there on this Starlette/FastAPI). Keep the names:
```python
@dataclass
class StreamHandle:
    status: int | None; headers: dict[str, str]; started: anyio.Event; disconnect: anyio.Event; done: anyio.Event
    chunks: MemoryObjectReceiveStream[bytes]; buffer: str = ""; request_sent: bool = False; ended: bool = False

@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[TaskGroup]:
    """Run the app's lifespan and a task group for the streams; both end when the block exits."""
    async with app.router.lifespan_context(app):
        async with anyio.create_task_group() as tg:
            yield tg
            tg.cancel_scope.cancel()

async def asgi_call(app, method: str, path: str, *, token: str | None, json_body: object | None = None,
                    headers: Mapping[str, str] | None = None, timeout: float = 3.0) -> tuple[int, dict[str, str], bytes]:
    # one finite request: build the same scope as open_stream with method/path, body = json.dumps(json_body).encode()
    # (content-type application/json), run `await app(scope, receive, send)` under anyio.fail_after(timeout), collect
    # status, lower-cased headers and the full body.

async def open_stream(tg, app, path: str, *, token: str | None, last_event_id: str | None = None,
                      spec_version: str = "2.3", timeout: float = 2.0) -> StreamHandle: ...
    # exactly AEA-41's body (scope with "asgi": {"version": "3.0", "spec_version": spec_version}, cookie header
    # f"mhc_session={token}", optional last-event-id header, client ("198.51.100.7", 50000), "state": {};
    # memory object stream max_buffer_size=10_000; receive() returns the empty request once, then waits for
    # handle.disconnect; send() records status/headers on http.response.start and forwards body chunks; run() always
    # closes the send side and sets started/done in finally; tg.start_soon(run); wait for `started` under fail_after)
async def next_item(handle, *, timeout: float = 2.0) -> SseFrame | str | None: ...   # frame, comment text, or None at end
def _parse_block(block: str) -> SseFrame | str: ...
async def read_frames(handle, count: int, *, timeout: float = 2.0) -> list[SseFrame]: ...   # skips comments
async def read_until_heartbeat(handle, *, timeout: float = 2.0) -> list[SseFrame]: ...
    # frames received before the next ": heartbeat" comment (used to prove "nothing else arrived")
async def close_stream(handle, *, timeout: float = 2.0) -> None: ...   # set disconnect, wait for done
def frame_ids(frames: Sequence[SseFrame]) -> list[int]: ...
```

### Step 10 — route, stream and capture tests

Sync tests use `with make_client(app) as c:`. Stream tests are sync tests that call `anyio.run(scenario)` and use
`async with running(app) as tg:`. Every stream test calls `fast_stream(monkeypatch)` first, so reads are bounded.

**`tests/api/test_staff_live_routes.py`:**
- **`test_live_action_matches_openapi` (AC-9).** Real service. Seed case A and case B (queued, rep-owned).
  1. A: join, send `STAFF_TEXT`, hand_back. B: join, close.
  2. `assert_matches(r, "liveChatAction")` on each of the four 200 kinds.
  3. Print the `live.state` values.
- **`test_live_action_refusals` (AC-10).** With a `RecordingLiveChat` returning each of these in turn:
  - `LiveRefused("CASE_NOT_FOUND", {"reference": "MHC-C-0099"})` → 404;
  - `("NOT_CLAIMED_BY_YOU", {"owner": None})` → 403, `details.owner is None`;
  - `("CASE_ALREADY_CLAIMED", {"claimed_by": "Demo supervisor", "claimed_at": "2026-10-16T14:20:00-05:00"})` → 409;
  - `("NOT_LIVE", {"reason": "not_joined"})` → 409.
  - Each body passes `error_body(...)` and `assert_matches`.
  - Then `{"action": "wave"}` → 400 `VALIDATION_ERROR`, `field == "action"`, with no recorded call.
  - Finally the reachability check (PA-1 at route level): with the real service, `UNKNOWN_REF` answers an `ApiError`
    404 `CASE_NOT_FOUND`, not FastAPI's `{"detail": "Not Found"}`.
- **`test_text_rules` (AC-11).** With `RecordingLiveChat`:
  - send `text=None`, `"   "`, `"q" * 2001` and join with `text=rand_word()` → four 400 bodies with field `text` and
    constraints "required for send", "required for send", "at most 2000 characters", "only for send";
  - `assert_matches` on each; `calls == []`;
  - each submitted non-blank text is absent from every body and from `app_log_text(caplog)` (use
    `caplog.set_level(logging.DEBUG)`).
- **`test_live_roles` (AC-12).**
  - Tokens for customer, supervisor and owner each POST join → 403 `ROLE_NOT_ALLOWED` with `details.needs ==
    ["representative"]` (the customer's `role` is "customer").
  - The stream: customer → 403 with `needs == ["representative", "supervisor", "owner"]`; `assert_matches` with
    `"streamCaseEvents"` (a JSON 403).
  - representative, supervisor and owner each open the stream (harness) → status 200.
  - The `RecordingLiveChat` has no calls, and a monkeypatched counting `staff_live.read_case_events` recorded 0 reads
    for refusals.
- **`test_login_gate` (AC-18).** No cookie: POST live and GET events both → 401 `UNAUTHENTICATED`; `assert_matches`
  each.
- **`test_malformed_reference_is_not_found` (PA-4).** `/api/staff/cases/mhc-c-7/live` (rep) and `/…/events` → both 404
  `CASE_NOT_FOUND`, `details is None`, never 400 or 422; `assert_matches` each.

**`tests/api/test_staff_live_stream.py`:**
- **`test_case_stream_replay_live_and_heartbeat` (AC-13).**
  1. Seed `WP2_REF`. Append 32 `case_changed` rows `{"version": i, "lifecycle": "claimed"}` to `case:MHC-C-0007`.
     A fresh temp DB starts events at id 1, so ids are 1–32.
  2. Inside `captured_log()`: open with `last_event_id="30"` → `handle.headers["content-type"]` starts with
     `text/event-stream`; `read_frames(h, 2)` ids `[31, 32]`; `assert_sse_frames_match(frames, "streamCaseEvents")`.
  3. Append `controller_changed` through `app_uow(app)` → `read_frames(h, 1)` id 33.
  4. `next_item` eventually returns the comment `"heartbeat"`.
  5. `close_stream`; `records_of(log, "stream_reconnect") == [{"record": "stream_reconnect", "request_id": <the
     X-Request-ID header>, "case_ref": "MHC-C-0007", "last_event_id": 30, "replayed": 2}]`.
  6. Then `GET` events for `UNKNOWN_REF` via `make_client` → 404 `CASE_NOT_FOUND`, `assert_matches`, and the body is
     not an event stream.
- **`test_case_stream_start_after_reset_and_close_rules` (AC-14).**
  1. Seed `MHC-C-0005` and append one `controller_changed`.
  2. In one write unit: `tx.core.reset.clear_demo_tables("reset-test", ended_at=<UTC now>)`; append `demo_reset`
     `{"speaker": EVENT_SPEAKER, "line": "The demo was reset, so this chat has ended. Nothing from it was kept."}`
     (keep its id `R`); commit.
  3. Re-seed `MHC-C-0005` with `seed_live_case(case_ref=CaseRef("MHC-C-0005"))`.
  4. (a) Open with no header → `read_until_heartbeat` returns `[]` (no `demo_reset`). Append `case_changed` → it
     arrives (the stream is open).
  5. (b) Open with `last_event_id=str(R - 1)` → the frames are `[demo_reset id R]`, then `next_item` returns `None`
     (the body ended).
  6. (c) Append `chat_closed {"reason": "closed_by_staff"}` then `case_changed` → a header-less stream receives both,
     in order (it stays open after `chat_closed`).
- **`test_streams_share_limiter` (AC-15).**
  1. Monkeypatch `staff_live.read_case_events` with `BlockingReads`. It is a callable that, under a `threading.Lock`,
     records `starts.append(time.monotonic())`, bumps `active` and `max_active`, then waits `release.wait(5)`, then
     returns `(last or 0, [])`, then drops `active` and bumps `done`.
  2. `async with running(app)`: open 5 streams to `WP2_REF` (seeded).
  3. Wait (≤ 2 s, 10 ms steps) until `active == 4`; `await anyio.sleep(0.2)`.
  4. Assert `active == 4`, `max_active == 4`, `done == 0`, and
     `provided(app, get_stream_poll_limiter).borrowed_tokens == 4`.
  5. Under `anyio.fail_after(3)`: `asgi_call(app, "POST", live_url(...), token=rep, json_body={"action": "join"})` →
     status 200 (a `RecordingLiveChat` returning the JOINED view).
  6. `release_at = time.monotonic(); release.set()`; wait until `done >= 5`; assert `sorted(starts)[4] >= release_at`.
  7. Close the streams.
  8. In a `finally`, always call `release.set()`, so cancelled worker threads finish.
- **`test_reset_gate_behaviour` (AC-16).**
  1. Count reads with a counting wrapper on `staff_live.read_case_events`.
  2. `gate = provided(app, get_reset_gate)`.
  3. `with gate.hold():`
     - `open_stream(...)` returns within 0.5 s with `status == 200`, not 503;
     - `read_until_heartbeat` → `[]` and `reads == 0`.
  4. After the block, the next poll reads: the count rises within 1 s, and an appended `case_changed` arrives.
  5. Then the wait: a task does `with gate.hold(): await anyio.sleep(0.3)`; once `gate.held()`, time
     `asgi_call(POST join)` → status 200 (never 503), elapsed ≥ 0.25 s.
- **`test_malformed_last_event_id_is_ignored` (PA-5).**
  1. Seed, append `demo_reset` (id R), then `case_changed`.
  2. Open with `last_event_id="abc"` → frames are only the `case_changed`, so the start was R.
  3. Inside `captured_log()`, there is no `stream_reconnect` record.

**`tests/api/test_staff_live_capture.py`:**
- **`test_message_text_never_logged` (AC-17).**
  1. `staff = rand_word(18, "zqstaff")`; `reply = rand_word(18, "zqreply")`. Letters only.
  2. `caplog.set_level(logging.DEBUG)` and `captured_log()`.
  3. Seed, join and send `staff` (the response `message.text == staff`); `append_customer_reply(…, reply, JOIN_AT)`;
     a header-less stream frame `customer_message` carries `reply`.
  4. Both strings are in the `messages` rows; neither is in `caplog.text`, `app_log_text(caplog)` or the
     `captured_log` text. That covers all loggers, including `request` and `stream_reconnect` (reconnect once with
     `last_event_id` to emit one).
- **`test_wf4_live_entry_points_emit_records` (AC-20).** One `anyio.run` scenario.
  1. Case A: join, send, hand_back. Case B: join, close. All via `asgi_call`.
  2. Then a stream connect with `last_event_id="1"` on A; read 1 frame; close.
  3. Assertions:
     - `records_of(log, "request")` has 6 records, each with `request_id` equal to that response's `x-request-id`;
       `route` is `"/api/staff/cases/{reference}/live"` for 5 and `"…/events"` for 1; `caller_role ==
       "representative"`;
     - `case_events` gives A `[live_join, live_send, live_hand_back]` and B `[live_join, live_close]`, all with
       `actor_role "representative"` and `detail["action"]`;
     - `events.after(thread_stream(A.thread_id), 0)` is non-empty and `events.after(case_stream(A.case_ref), 0)` is
       non-empty: the correlation keys.
  4. Print the records, case events and stream rows.

### Step 11 — `tests/unit/web/test_register_staff_live.py` (PA-1)

- `test_register_staff_live_binds_service_and_router`:
  1. `with temp_sqlite() as db`: `c = Container(settings=make_settings(tmp_path), limits=Limits())`.
  2. `c.provide(Key[Any]("uow_factory"), lambda _c: db.uow)` and `c.provide(Key[Any]("demo_clock"), lambda _c:
     FixedClock(JOIN_AT))`.
  3. `app = FastAPI()`; `app.state.web_shell = WebShellState(settings=c.settings, wall_clock=lambda:
     datetime.now(UTC), public_paths=PublicPaths())`.
  4. `register_staff_live(c, app, settings=c.settings, limits=c.limits)`; `c.build()`.
  5. Assertions:
     - `isinstance(c.get(LIVE_CHAT), LiveChatService)` and the same object twice;
     - `{(r.path, r.operation_id) for r in effective_routes(app)}` ⊇ the two paths with `liveChatAction` and
       `streamCaseEvents`;
     - a second container built over the same app → still one route each (the guard flag).
- `test_redactor_binding_is_store`: through `c.get(LIVE_CHAT)`, seed, `join`, send a run-time card-like text → the
  stored text has `"[card number removed]"`. This is MC-23 at the hunk.
- `test_demo_clock_unbound_raises_not_bound`: no `demo_clock` key provided → `build()` succeeds; `join` on a seeded
  queued case → `RuntimeError("not bound: demo_clock")`; the snapshot is unchanged.
- `test_bare_app_gets_nothing`: `FastAPI()` without `web_shell` → after `build()`, `c.get(LIVE_CHAT)` raises
  `ContainerError("not provided: live_chat")`.

### Step 12 — contract cases (AC-22)

**`tests/contract/cases/staff_live.py`.** Same shape as `tests/contract/cases/auth.py`: `ROUTE_FILE: Final =
"staff_live"`, `CASES: Final[dict[str, dict[str, object]]]`. Each operation is `{"public": False, "drives": (…)}`, and
each drive is `{"name", "status", "code" (errors only), "preconditions": tuple[str, ...], "reference": str, "body"
(live) | "last_event_id" (stream), "frames" (stream 200 only)}`.

The module docstring states the owner (AEA-46, AC-22, AEA-46-2), that AEA-59's runner reads the file, and this
**closed vocabulary**:
- `"login"`: sign in with the configured demo pair and keep the cookie.
- `"as_representative"`: `switchRole` to representative (CON-10, AEA-44). The local driver issues a representative token.
- `"live_case_claimed"`: the working copy holds MHC-C-0007, lifecycle claimed, owner representative, its
  conversation `live_state` queued.
- `"live_case_joined"`: as above, then a successful `join`.
- `"live_case_unclaimed"`: MHC-C-0007 queued with no owner.
- `"case_claimed_by_supervisor"`: MHC-C-0007 queued, owner supervisor.
- `"case_events"`: three events on `case:MHC-C-0007` (`controller_changed`, `case_changed`, `chat_closed` closed_by_staff).
- `body`: `{"example": "<JOIN|SEND|HAND_BACK|CLOSE>"}` sends the named OpenAPI request example; `{"raw": <JSON>}`
  sends JSON as given.

Drives:

| op | name | status/code | preconditions | reference / body / header |
|---|---|---|---|---|
| liveChatAction | joined | 200 | login, as_representative, live_case_claimed | MHC-C-0007, example JOIN |
| | sent | 200 | login, as_representative, live_case_joined | example SEND |
| | handed_back | 200 | … live_case_joined | example HAND_BACK |
| | closed | 200 | … live_case_joined | example CLOSE |
| | text_on_join | 400 VALIDATION_ERROR | … live_case_claimed | raw `{"action": "join", "text": "placeholder"}` |
| | no_session | 401 UNAUTHENTICATED | — | example JOIN |
| | wrong_role | 403 ROLE_NOT_ALLOWED | login | example JOIN |
| | not_claimed_by_you | 403 NOT_CLAIMED_BY_YOU | login, as_representative, live_case_unclaimed | example JOIN |
| | unknown_case | 404 CASE_NOT_FOUND | login, as_representative | MHC-C-0099, example JOIN |
| | not_live | 409 NOT_LIVE | … live_case_claimed | example SEND |
| | already_claimed | 409 CASE_ALREADY_CLAIMED | … case_claimed_by_supervisor | example JOIN |
| streamCaseEvents | first_connect | 200, frames 3 | login, as_representative, live_case_claimed, case_events | MHC-C-0007, no header |
| | resume | 200, frames 2 | same | `last_event_id: 1` |
| | no_session | 401 | — | MHC-C-0007 |
| | wrong_role | 403 ROLE_NOT_ALLOWED | login | MHC-C-0007 |
| | unknown_case | 404 CASE_NOT_FOUND | login, as_representative | MHC-C-0099 |

**`tests/api/test_contract_cases_staff_live.py::test_staff_live_cases_drive_documented_statuses`.** Plan-added,
following the AEA-23, 41, 42 and 43 precedent. For each drive:
1. Build a fresh `staff_live_app` (real service).
2. Apply the preconditions with the helpers from §6 and §9 (`as_representative` = `store.issue(DemoRole.REPRESENTATIVE)`;
   `login` alone = a customer token).
3. Send the request. Non-stream answers pass `assert_matches`; stream 200s go through the harness, `read_frames(h,
   frames)` and `assert_sse_frames_match`.
4. Assert the per-operation status sets equal `{"200","400","401","403","404","409"}` for liveChatAction and
   `{"200","401","403","404"}` for streamCaseEvents, and that `ROUTE_FILE == "staff_live"`.
5. Print `"<op> <name>: <status>"`.

### Step 13 — the journey (AC-23): `tests/journeys/j7/test_aea_46.py`

`pytestmark = pytest.mark.journey`. Module docstring: J-7 (slice plan §0a) at level **mock-tested**. Name what is real:
the app, the middleware, the routes, `LiveChatService` and the SQLite working copy. Name what is doubled:
`FakeSessionStore` (AEA-44), the demo clock (AEA-30), and the customer reply written as AEA-40 would write it.

1. **`test_j7_live_takeover_mock_level`**, one `anyio.run` scenario on `staff_live_app`:
   1. Seed `WP2_REF` (version 2) and `SECOND_REF` (version 2), both queued and rep-owned. Record the versions.
   2. A: POST join → 200 JOINED. Then send `STAFF_TEXT` → 200 SENT. Then `append_customer_reply(CUSTOMER_REPLY)`.
      Then hand_back → 200 HANDED_BACK.
   3. B: join → close → 200 CLOSED.
   4. **What the customer sees** (the thread rows and the thread-stream events CON-3 will send):
      - A's thread messages in order end with `STAFF_TEXT` (representative) and then `CUSTOMER_REPLY` (customer);
      - A's thread events are `[representative_joined, ai_paused, staff_message, ai_resumed]` with the `live` lines;
      - B's thread events end with `chat_closed` (`composer_disabled` true).
   5. **What is stored:** both versions are unchanged and the lifecycles are still `claimed`.
   6. **What staff see:** a header-less `streamCaseEvents` on A → `read_until_heartbeat` types are `[controller_changed,
      customer_message, controller_changed]`, with no `case_changed`; `assert_sse_frames_match`.
   7. Every JSON 200 passes `assert_response_matches` (adapt `asgi_call`'s result with a small `_Resp` object having
      `status_code`, `headers`, `content` and `json()`, which is what `_ResponseLike` needs).
2. **`test_j7_live_takeover_integrated`**: `@pytest.mark.skip(reason="blocked: integrated J-7 needs AEA-57's harness
   (scripted model) and AEA-52's wiring; record level mock-tested")`. Its docstring lists the integrated steps:
   1. real login → `switchRole` representative → `claim` (CON-13);
   2. the customer opens the chat and asks for a person (CON-4);
   3. join, send, the customer's turn relayed with `AI_PAUSED`, hand back, close;
   4. the browser sees each line.

   It is reported as skipped, never as passed.

Run: `uv run pytest -m journey tests/journeys/j7/test_aea_46.py -q`.

### Step 14 — gates, then the code commit

Run §7 rows 1–6 in order and stop at the first red. Then:

```
git add src/meridian/services/live_chat.py src/meridian/web/routes/staff_live.py src/meridian/web/schemas/staff_live.py \
  src/meridian/web/container.py tests/services/live_chat_support.py tests/services/test_live_chat.py \
  tests/services/test_live_chat_events.py tests/api/staff_live_support.py tests/api/test_staff_live_routes.py \
  tests/api/test_staff_live_stream.py tests/api/test_staff_live_capture.py tests/api/test_contract_cases_staff_live.py \
  tests/contract/cases/staff_live.py tests/unit/web/test_register_staff_live.py tests/unit/web/test_staff_live_units.py \
  tests/journeys/j7/test_aea_46.py
git commit   # "feat(AEA-46): LiveChatService, CON-14 liveChatAction and CON-21 streamCaseEvents"
             # body: one line per AC group; last line exactly:
             # Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

### Step 15 — context (AC-24) and the journey record, then the docs commit

Use the code commit's short SHA as `<sha>`.

- **`.claude/reference/area-map.md`, row A9 (line 36), status cell `planned`.** Change it to: `` `services/live_chat.py`,
  `web/routes/staff_live.py`, `web/schemas/staff_live.py` actual (AEA-46, `<sha>`); the rest planned ``. Change
  nothing else in the row.
- **`docs/design/code-design.md` §3.** On line 267 (`live_chat.py …  A9    2`), append `   built AEA-46 <sha>`. On
  line 311 (`routes/staff_live.py · schemas/staff_live.py …  A9    2`), append the same. Use the style of `built
  AEA-19 2d5b692`.
- **`.claude/state/icm-progress.md`.** Add one row after the last *Routes verified against code and tests* row (≤ 400
  characters): `| Routes verified against code and tests | provisional | <date>: area map A9 → services/live_chat.py,
  web/routes/staff_live.py, web/schemas/staff_live.py checked by tests/services/test_live_chat*.py,
  tests/api/test_staff_live_*.py (AEA-46, <sha>; <N> passed) | Each slice adds its route; verified when every area-map
  row is actual |`.
- **`docs/design/observability-contract.md`, row WF-4 (line 79).**
  - Entry-point cell: change "takeover and live chat (CON-14, CON-3 stream)" to "takeover and live chat (CON-14, CON-3
    stream), staff case stream (CON-21 `GET …/cases/{reference}/events`)".
  - Records cell: append ", `stream_reconnect` (`case_ref`) on a CON-21 reconnect".
  - This is DO-6 *Registering a new workflow* step 1. Step 4 is already the ticket's *Entry points* line.
- **`docs/testing/journeys/<run date>-AEA-46.md`.** The §4 record format of `integrated-journeys.md`:
  - Claim: J-7 join, send, hand back, close; version unchanged; CON-21 `controller_changed`, no `case_changed`;
  - Level: `mock-tested`;
  - Tested revision: `<sha>`;
  - Environment: VPS, uv, temp SQLite copy via `full_app`, FakeSessionStore, FixedClock demo clock, no model;
  - Command: the §7 rows 4–6;
  - Result: counts;
  - Evidence location: GitLab #46 comment and this file;
  - Remaining limitations: AEA-40 relay simulated; AEA-30 clock doubled; login and roles doubled;
  - Blocked by: **AEA-57 (harness, scripted model) and AEA-52 (integration)**; AEA-59 for the strict contract run;
  - Journeys that will exercise this code: J-7, J-6 (staff view of a case).

Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in this slice's rows. Then:
`git add .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md
docs/design/observability-contract.md docs/testing/journeys/<date>-AEA-46.md`, and commit "docs(AEA-46): journey
record and context for live takeover" with the same Co-Authored-By last line. `git diff --stat HEAD~1` must list
exactly those five files.

### Must not

- Edit any file outside §2's owned list; in `container.py`, change anything but `register_staff_live`.
- Import from `routes/events.py`, `schemas/events.py` or `tests/api/events_support.py`, or add a shared SSE helper
  (DO-3 S-11, AC-19).
- Write to `cases`, `promises`, `case_changed` or `conversations.outcome`; call or import `CaseService`; claim a case
  (CON-13 is AEA-45's).
- Read a clock in the route or schema files (`datetime.now`, `time.time`). The service reads only its injected
  `demo_clock`, once per writing action.
- Log, trace or put in a record any message text, the `Last-Event-ID` value beyond `last_event_id`, or any cookie.
- Put a digit-literal card-like number, a 6-digit code or a full phone number in any file. Generate them at run time
  (§6).
- Add dependencies (no `pytest-asyncio`, no `pytest-timeout`); edit `pyproject.toml` or `uv.lock`.
- Bind a port (in particular 4019 and 5184), call a paid model, read `.env`, `git add -A`, push, or force-push.
- Catch exceptions inside `_run` or the stream loop; put `await` in the loop's `finally`.

---

## 6. Data and fixtures (all synthetic or issued-fictional)

| Data | Source | Where |
|---|---|---|
| MHC-C-0007, Omar Patel's case; customer MHC-10002 | WP-2 (`docs/data/worked-pairs.md`, issued fictional ids; ticket example pair) | `WP2_REF`, `WP2_CUSTOMER` |
| MHC-C-0011, MHC-C-0005, MHC-C-0099 | synthetic refs (0005 = a seed ref named by staff.md §7's MC-8 test; 0099 = the OpenAPI CASE_NOT_FOUND example) | support constants |
| Times 2026-10-16 14:20 / 14:22 / 14:22:40 / 14:23 Chicago | OpenAPI liveChatAction examples | `QUEUED_AT`, `JOIN_AT` |
| "Hi Omar, I can look at the after-hours charge with you." / "Thanks, that helps." | OpenAPI SEND example / FRAMES example | `STAFF_TEXT`, `CUSTOMER_REPLY` |
| `demo_reset` line | AEA-41 plan fixture (SCREEN_SPECS SCR-1 wording) | AC-14 test |
| Card-like 16 digits and a 6-digit code | generated at run time by `random.Random(46)` | `card_like_and_code()` |
| Distinctive "must be absent" strings | `rand_word()` (letters only) | AC-11, AC-17 |
| Working database | `temp_sqlite()` or `full_app`'s tmp `data_dir`, copied from the issued file, never written | every test |

---

## 7. Checks

### While iterating (affected tests only)

| Check | Command | Passing looks like |
|---|---|---|
| Units | `uv run pytest tests/unit/web/test_staff_live_units.py tests/unit/web/test_register_staff_live.py -q` | all pass |
| Service | `uv run pytest tests/services/test_live_chat.py tests/services/test_live_chat_events.py -q` | all pass |
| Routes and streams | `uv run pytest tests/api/test_staff_live_routes.py tests/api/test_staff_live_stream.py tests/api/test_staff_live_capture.py tests/api/test_contract_cases_staff_live.py -q` | all pass; no test over ~5 s |

### Once, before the code commit (cheapest first; stop at the first red)

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/services/live_chat.py src/meridian/web/routes/staff_live.py src/meridian/web/schemas/staff_live.py src/meridian/web/container.py tests/services tests/api tests/unit/web tests/contract/cases/staff_live.py tests/journeys/j7/test_aea_46.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check` with the same paths | no file would be reformatted |
| 3 | Types | `uv run mypy src/meridian/services/live_chat.py src/meridian/web/routes/staff_live.py src/meridian/web/schemas/staff_live.py src/meridian/web/container.py tests/services/live_chat_support.py tests/services/test_live_chat.py tests/services/test_live_chat_events.py tests/api/staff_live_support.py tests/api/test_staff_live_routes.py tests/api/test_staff_live_stream.py tests/api/test_staff_live_capture.py tests/api/test_contract_cases_staff_live.py tests/contract/cases/staff_live.py tests/unit/web/test_register_staff_live.py tests/unit/web/test_staff_live_units.py tests/journeys/j7/test_aea_46.py` | `Success: no issues found` |
| 4 | AC-19 grep | `grep -nE "datetime\.now\|time\.time\|routes\.events\|routes/events" src/meridian/web/routes/staff_live.py src/meridian/web/schemas/staff_live.py` | prints nothing (exit 1) |
| 5 | Affected tests | `uv run pytest tests/unit/web tests/unit/test_import_direction.py tests/services tests/api -q`. "Affected" here means the mirror folders of `services/` and `web/`, plus every test that builds the real container through `create_app` / `full_app` (`grep -rl "full_app\|build_container\|create_app(" tests`), because the hunk now runs in all of them. Optionally `uv run --with pytest-xdist pytest -n 2 …`; never more than 2 workers | all pass; report the counts (the AEA-32 record notes one pre-existing failure on main; name it if it recurs, do not fix it here) |
| 6 | Affected journeys | `uv run pytest -m journey tests/journeys/j7/test_aea_46.py -q`, then `uv run python -m tests.journeys.affected --base main` (a change under `tests/journeys/` selects every journey) | 1 passed, 1 skipped (blocked); every selected journey passes |
| 7 | Context | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` (after step 15) | no FAIL |

**Full suite:** not required. The change reaches no shared fixture, settings, dependency or lockfile. The container
hunk runs in every `create_app` test, and row 5 covers all of them.
**Contract strict run:** `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "liveChatAction or
streamCaseEvents" -rs`. It runs only after AEA-59 merges; until then the file does not exist, and the report says so.
**Report:** for each AC, the test, its file and the result, using the §3 table. State the journey level
(`mock-tested`) and its *Blocked by*.

---

## 8. Risks and requests

| # | Risk / request | Handling |
|---|---|---|
| R-1 | This is the first hunk on main to `include_router` during the lifespan (AEA-40/41/42 plan the same). FastAPI 0.156 keeps `include_router` lazy, and the middleware matches through `iter_route_contexts` | PA-1 asserts the routes through `effective_routes`, and AC-10's last call proves the route answers through the real `full_app` |
| R-2 | `CeControllerChanged.line` has no specified sentence | Engineering decision: reuse the DAT-29 `live` texts (join → `REP_JOINED`, hand_back → `AI_RESUMED`). A different sentence later is a one-line change here plus an AEA-03 text, not a contract change |
| R-3 | `LiveState.since` semantics: the OpenAPI HANDED_BACK example keeps the join time | Examples are illustrative (staff.md §5 says so for `LIVE_JOINED`). PA-6 decides "since the current state began". PA-7 builds the examples from matching views, so they still validate |
| R-4 | Malformed `{reference}` → 404 on both operations (the stream documents no 400) | PA-4 |
| R-5 | During a reset, a CON-21 connect skips its 404 lookup (staff.md §11 "never waits on connect") | An unknown-case stream opened mid-reset only heartbeats until the client closes. Harmless; written in the route docstring |
| R-6 | AEA-29 (`CaseService`) and AEA-30 (`demo_clock`) are same-wave and unmerged | Doubles (`ResolveDouble`, `FixedClock` via `get_live_chat` override). **Until AEA-30 merges, a real deployed write action answers 500 ("not bound: demo_clock").** AEA-52 proves the wired path. **Request to AEA-29's and AEA-52's implementers:** once `CaseService` lands, swap `ResolveDouble` for it in AC-21 (follow-up on this test file) |
| R-7 | AC-5, AC-21 and AC-23 say "join, send, hand back and close". The spec table makes close-after-hand-back `NOT_LIVE not_joined` | Every test uses two cases (A: join/send/hand_back; B: join/close). No behaviour is invented |
| R-8 | AEA-41 (same wave) renders thread events from these payloads | PA-3 validates them with AEA-41's rule against the OpenAPI `ChatEvent`; both plans use the same payload table (§4.6) |
| R-9 | AEA-40 relays by `controller.case_ref` | PA-2. **Tell AEA-40/52:** `join` stores `Controller(kind="human", representative_name="Riley", case_ref=<ref>)`; hand_back and close store `Controller(kind="ai")` |
| R-10 | AEA-59's case format is not fixed | `tests/contract/cases/staff_live.py` mirrors `auth.py` and documents its vocabulary. A different shape is AEA-59's follow-up on this file |
| R-11 | Collisions | `container.py`: own hunk only. Context docs: own row and lines only (AEA-41/42/45 edit neighbouring lines of the same files, so the merge resolves by keeping both). `tests/journeys/j7/`: own file only (AEA-42 owns `test_aea_42.py`). No overlap with AEA-45's `staff_cases` files |
| R-12 | `CASE_ALREADY_CLAIMED.details` carries `claimed_at` beyond the OpenAPI example | `ApiError.details` is a free object; staff.md §5 decides. AC-10 validates the body |
| R-13 | Test-file count is high (11 test files) | Forced by the 500-line cap; each file has one responsibility |

No shared primitive is requested from the integrator. No contract change is needed.

---

## 9. Readiness

**READY.** Blockers AEA-10 and AEA-23 are merged on main (`ef40f45`). Every sibling this slice calls (AEA-29, 30, 40, 41,
44, 52, 57, 59) is reached through its signed signature and tested with a double; none is a merge edge. No decision in
`docs/plans/stage7-signoff.md` D-4…D-15 is touched, and no signed contract needs a change. The engineering decisions
taken here are listed under §8 R-2…R-5 and in §3b.

## Deviations

- Base moved: the worktree was cut from main `24a5e9a`, not `ef40f45`. AEA-41 had merged, so `tests/api/events_support.py` exists on main; the harness was still copied, not imported (AC-19 spirit, DO-3 S-11).
- `docs/design/code-design.md` module-map lines were 268 (`live_chat.py`) and 312 (`routes/staff_live.py`), not 267 and 311; same lines edited.
- ICM row inserted after the last "Routes verified" row (line 31 on this base). `check_context.py` reports `FAIL icm 8665 B (budget 8192 B)`; the file was already over budget before this row (about 8.3 KB without it), so the failure is cumulative from earlier slices, not from AEA-46.
- Extra test `test_supervisor_does_not_own_representative_case` and `test_unknown_case_through_real_service` added (cheap companions to AC-2 and PA-1).
- `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0` fails on main as well (journeys now exist); untouched.
