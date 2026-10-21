# Plan — [AEA-42] customer API: person request and follow-up (CON-4, CON-5)

**Status:** planned — READY (no open blocker: AEA-02, 10, 11, 14, 19 and **AEA-23 merged**; siblings 21, 29, 30 are called
through their signed signatures and tested with doubles)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/42 (identical to
`docs/plans/tickets/AEA-42.md`) · **Base revision:** `main` `c7ce976` (AEA-23 merged at `1e6889a`) · **Wave:** 2 ·
**Lane:** build-loop · **Risk:** none (no `risk::security`: plan → implement with tests → review; no frozen tests)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-42-person-request` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-42`), cut from `main` at or after `c7ce976`.

No earlier version of this plan existed at this path; this is the first write.

---

## 1. Goal and sources

**Goal** (issue *What to build*): build `requestPerson` (CON-4, `POST /api/chat/sessions/{thread_id}/handoff`) as a thin
route over a new `PersonRequestService`, and `saveFollowUp` (CON-5, `PUT /api/chat/sessions/{thread_id}/follow-up`) as a
direct route over `CaseService.set_followup`. Serves US-2 ("Talk to a person" works the first time) and US-14 (reference,
exact promise, follow-up choice).

**What it does, concretely.** A signed-in customer taps "Talk to a person". The browser posts
`{"turn_id": "9a316052-be7f-4e96-8c43-3e5f60718293"}`. The route checks the thread belongs to this login session, then
the service: (1) claims the `turn_id` in the `turns` table; (2) builds a `HandoffRequest` (reason
`customer_requested_person`, P3, rule `CON4.person`, trigger `con4`, the thread's identity); (3) calls
`HandoffService.open`, which writes the case and promise; (4) asks `ReplyComposer` for the card; (5) reads the
"What's settled" panel from the stored rows; (6) stores the whole answer on the turn row and marks the conversation
`handed_off`. A second tap with the same `turn_id` gets the stored answer back; a tap with a new `turn_id` gets
`already_open` with the same card. No model, no spend guard, no rate limit.

**Sources (read; nothing here edits them):**

| Source | Section | Obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-42.md` (AC-1…AC-23, example pairs 1–2) | Everything below |
| Web addendum (wins over DO-4) | `docs/design/contracts/stage7/web.md` §1 `ApiProblem`, §4 `owned_thread` + providers, §5 table (CON-4 never limited), §7 (CON-4 waits for a reset; its 503 is `HANDOFF_FAILED`), **§8** (`PersonRequest`, `PersonRequestOutcome`, `HandoffWriteFailed`, `PersonRequestService`), §10 `request` record, §13 `openapi_check`, §14 (stored `block` read by `thread()`) | Signatures copied in §4 below |
| Cases addendum | `stage7/cases.md` §1.1 (`conversations.outcome`, wall times UTC), §1.2 (`core.turns.begin/finish`, `core.reads.identity_state`, `core.conversations.lookup`, `core.settled_for`), §3.2–§3.3 (`promise_for`, `priority_for` P3), §5 (`HandoffService.open` writes no turn row; `CaseService`), §6 (`DemoService.clock_view`; the abandonment sweep), A-7 | Steps 2–4 |
| Graph addendum | `stage7/graph-core.md` §2 (`TurnContext`, `TurnTrace`, `TurnRecord`), §6 (`settled_for`), §13 (`ReplyComposer.handoff_block`, `settled_view`) | Steps 2, 3 |
| Models addendum | `stage7/models.md` §4 (`SpanHandle`, `TraceSink.turn`, `export_status(span)`) | Step 2 |
| DO-4 | `internal-components.md` §7 (`HandoffRequest`, `HandoffResult`), §13 (`CaseService.set_followup`, `open_case_for_thread`, `UnitOfWorkFactory`) | §4 below |
| Merge clashes | `docs/plans/7b-decisions/merge-clashes.md` MC-16 (410), MC-17 (span + `trace_export`), MC-18 (`handed_off`), MC-20 (UTC wall clock), MC-27 (owns `services/person_request.py`) | Steps 2, 4 |
| UX-join | `docs/plans/ux-join/backend-amendments.md` AEA-42-1 (= AC-20), AEA-42-2 (= AC-21), J-7 row (= AC-22); residual R-W-6 (`residuals-web.md`) | Steps 6–8 |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `requestPerson` (200/400/401/404/410/503), `saveFollowUp` (200/400/401/404/409/410); schemas `HandoffRequest`, `HandoffResponse`, `HandoffBlock`, `LiveQueuedBlock`, `FollowUpRequest`, `FollowUpResponse`, `FollowUpView`, `Settled`, `ApiError`; request examples `BUTTON`, `PHONE_MORNINGS`, `EMAIL_GENERAL` | Wire shapes |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`; workspace `code-design-solid-modularity.md`, `async-safety.md` | §7, §5 step 9 |
| Sign-off | `docs/plans/stage7-signoff.md` D-9 (CON-4 builds no brief) — consistent with this plan | — |

## 2. Boundary

**Create (owned):**

| File | Purpose |
|---|---|
| `src/meridian/services/person_request.py` | `PersonRequest`, `PersonRequestOutcome`, `HandoffWriteFailed`, the two typing Protocols, `PersonRequestService`, helpers `read_identity`, `settled_view_for` |
| `src/meridian/web/schemas/handoff.py` | `HandoffRequestBody`, `FollowUpRequestBody`, `FollowUpResponse` |
| `src/meridian/web/routes/handoff.py` | `build_router()` with `request_person` and `save_follow_up` |
| `tests/services/person_request_support.py` | Doubles and DB seeding helpers (synthetic) |
| `tests/services/test_person_request.py` | Service tests (AC-2…AC-5, AC-13, AC-18, AC-20) |
| `tests/api/handoff_support.py` | The app harness (real `create_app`, real AEA-23 middleware, this ticket's hunk, doubles) |
| `tests/api/test_handoff_routes.py` | Route tests (AC-1, 3, 4, 6–17, example pairs 1–2) |
| `tests/api/test_handoff_capture.py` | AC-19 |
| `tests/api/test_contract_cases_handoff.py` | Local driver for AC-21's cases until AEA-59's runner lands |
| `tests/contract/cases/handoff.py` | AC-21 server cases (data only) |
| `tests/unit/web/test_register_person_request.py` | The hunk's own test |
| `tests/journeys/j7/test_aea_42.py` | AC-22 journey (mock level today) |
| `docs/testing/journeys/<run date>-AEA-42.md` | AC-22 evidence record |

**Modify (owned):** `src/meridian/web/container.py` — **only** the body and docstring of `register_person_request`.
**Context docs (AC-23, this ticket's lines only):** `.claude/reference/area-map.md` row A8 (status cell),
`.claude/state/icm-progress.md` (one new row), `docs/design/code-design.md` §3 lines for `person_request.py` and
`routes/handoff.py · schemas/handoff.py`.

**Read only (shared surfaces; never edit):** `web/{app,middleware,deps,errors,logging}.py`, `routes/auth.py`,
`schemas/auth.py`, every other `register_*` hunk, `domain/*`, `ports/*`, `policy/*`, `adapters/sqlite/*`,
`services/{ledger,reset_gate}.py`, `tests/api/{openapi_check,web_shell_support}.py`, `tests/fakes/*`,
`tests/fixtures/sqlite.py`, `tests/conftest.py`, `tests/journeys/{affected.py,support/}`, the OpenAPI,
`UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, the briefing, issued data, `docs/archive/`, `docs/parked/`.

**Owned by siblings (do not create):** `services/{cases,handoff}.py` (AEA-29), `services/demo.py` (AEA-30),
`agent/nodes/compose.py` (AEA-21), `services/session.py` / `routes/chat.py` (AEA-40), `domain/views.py` (the uncut
AEA-02b follow-up; see §8 R-2), `tests/journeys/support/` (AEA-57), `tests/contract/test_openapi_server.py` (AEA-59).

## 3. Requirements table

Every AC is the ticket's, verbatim in intent; "plan-added" rows close gaps found in reconciliation. Test files are in
§2; S = `tests/services/test_person_request.py`, R = `tests/api/test_handoff_routes.py`.

| ID | Requirement | How it is built | Verified by |
|---|---|---|---|
| AC-1 [invariant] | Every 200 validates per result: created non-live → `case_created` + `HandoffBlock`; created live → `live_queued` + `LiveQueuedBlock`; not created → `already_open` + the existing case's block | Step 3.6 result rule; route returns `outcome.model_dump(mode="json")` | R `test_request_person_matches_openapi` (`assert_matches(resp, "requestPerson")` on three bodies) |
| AC-2 [invariant] | Block is exactly `ReplyComposer.handoff_block(result)` (called once with the `HandoffResult`); no promise sentence in this ticket's files | Step 3.7: the service never builds a block itself | S `test_block_from_composer`; `grep -rn "business day\|representative will" src/meridian/web/routes/handoff.py src/meridian/web/schemas/handoff.py src/meridian/services/person_request.py` prints nothing |
| AC-3 [invariant] **WF-2** | `HandoffRequest` fields and `TurnContext(intake=None, span=<the trace.turn span>, now=<one demo reading>)` | Steps 3.4–3.5 | S `test_handoff_request_fields`; R `test_request_person_passes_handoff_request` |
| AC-4 [invariant] | Same body twice → identical body, one turn row; a new `turn_id` after a case exists → `already_open`, same reference | Steps 3.2–3.3 (`core.turns.begin`) + 3.6 | S `test_idempotent_turn_id`; R `test_request_person_idempotent` (3 presses → 2 turn rows; 3rd `already_open`) |
| AC-5 [failure] | A `running` turn waits ≤ 3 s [A] for its stored outcome, else `HandoffWriteFailed` → 503 | Step 3.3 `_await_stored` | S `test_running_turn_waits_then_fails` (fake wall clock, patched `time.sleep`) |
| AC-6 [failure] **WF-2** | Never limited: session and IP buckets exhausted → still 200; constructor takes no ledger/admission/limiter | Middleware already returns `None` for `requestPerson`; constructor in §4 | R `test_person_key_never_limited` (exhausted `RateLimiter`, `inspect.signature`) |
| AC-7 [failure] | `HandoffService.open` raising → 503 `HANDOFF_FAILED` + `details.retry_after_ms`, no reference, turn not `completed` | Steps 3.8, 4.2 | R `test_handoff_failed_503` |
| AC-8 [failure] | Malformed id `thr_9d41`, unknown UUID, another session's thread → identical 404 `SESSION_NOT_FOUND` on both ops; nothing written | `owned_thread` (AEA-23) as a dependency on both routes | R `test_session_not_found_identical` |
| AC-9 [failure] | This session's ended thread → 410 `SESSION_ENDED`, `details.reason: "demo_reset"`, both ops | `owned_thread` | R `test_session_ended_410` |
| AC-10 [failure] | `saveFollowUp` with no open case → 409 `NOT_ALLOWED_IN_STATE` `{state: "no_open_case"}`; `set_followup` never called | Step 4.3 | R `test_follow_up_without_case_409` |
| AC-11 [failure] | Unverified + `on_record` → 409 `{state: "not_verified"}` before any service call; `general` from the same thread saves | Step 4.3 | R `test_unverified_on_record_refused` |
| AC-12 [invariant] | 200 validates against `FollowUpResponse`; `followup` = `set_followup`'s return unchanged; called with `now = DemoService.clock_view().now` | Step 4.3 | R `test_save_follow_up_matches_openapi` |
| AC-13 [invariant] **WF-2** | Both responses carry `settled` from `core.settled_for(thread_id, read_at=<demo now>)` + `settled_view(...)`; a prior `verified` action shows; `settled.request.reference` = block reference | Steps 3.7, 4.3 via `settled_view_for` | S `test_settled_from_conversation_state`; R `test_both_responses_carry_settled` |
| AC-14 [failure] **WF-2** | 400 `VALIDATION_ERROR` names `field` + `constraint`, never the value (`turn_id` "not-a-uuid"; `window` "evening"; missing `channel`) | Body models in `schemas/handoff.py`; AEA-23's 422→400 handler | R `test_validation_error_names_field_not_value` (caplog) |
| AC-15 [negative] **WF-2** | No body says "was sent", "we sent", "emailed you", "called you" | Nothing composed here | R `test_nothing_claims_a_send` |
| AC-16 [negative] **WF-2** | The seeded customer's full phone and email (read from the DB copy at test time) appear in no body, log record or trace span; only "ending in 02" | Route copies `FollowUp` unchanged; no logging of values | R `test_destination_masked_everywhere` |
| AC-17 [invariant] **WF-2** | No cookie → 401 `UNAUTHENTICATED` `{reason: "none"}` (validates `Unauthenticated`); role `representative` → 200 | AEA-23 middleware; routes take no role check | R `test_login_gate_and_role_ignored` |
| AC-18 [invariant] | Created/live-queued CON-4 sets `conversations.outcome = 'handed_off'` in the finish transaction; the sweep selection 31 min later picks 0 rows | Step 3.9 | S `test_con4_marks_conversation_handed_off` (via `core.conversations.idle_live`, the sweep's selection; AEA-30 not merged) |
| AC-19 [capture] | One `request` record per call (template, status, `caller_role`, `thread_id`, `request_id` = `X-Request-ID`); CON-4 turn row `person_requested` / `handoff` / `handed_off`, `trace_id`, `trace_export` (`off` with `NullTraceSink`) | AEA-23 middleware + step 3.9 | `tests/api/test_handoff_capture.py::test_wf2_entry_points_emit_records` |
| AC-20 [invariant] | Stored `response` = the body exactly as returned, card under `block`; trace `gate_result` `person_requested`; a new `turn_id` → `already_open` whose block is the open case's card | Steps 3.6, 3.9 | S `test_stored_outcome_is_history_ready`, `test_already_open_block_names_existing_case` |
| AC-21 [contract] | `tests/contract/cases/handoff.py` holds every precondition, named request example and documented error status for both ops | Step 6 | Today: `tests/api/test_contract_cases_handoff.py::test_handoff_cases_drive_documented_statuses`. After AEA-59: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "requestPerson or saveFollowUp" -rs` |
| AC-22 [journey] | J-7: one case (live-queued while staffed), second press `already_open` with the same card, card in `getChatThread` after reload | Step 7 | `uv run pytest -m journey tests/journeys/j7/test_aea_42.py`; record at level `mock-tested`, *Blocked by* AEA-57, AEA-52 (and AEA-40 for the reload step) |
| AC-23 [context] | Area map A8, ICM row, DO-3 §3 lines updated, only this ticket's lines | Step 9 | `git diff --name-only main...HEAD` |
| WP pair 1 (example pair 1) | Nobody online → `case_created`, `MHC-C-0009` on a fresh store, `variant: nobody_online`, `due_at`/`due_label` as `promise_for` made them (`R26.unstaffed`), `settled.request.reference` = block's; new `turn_id` → `already_open` same ref, no 2nd case; same `turn_id` → first body | Steps 3–5 | R `test_example_pair_1_case_created_then_already_open` |
| WP pair 2 (example pair 2, WP-7 + WP-2) | After a refund case, verified MHC-10002 picks phone/on_record/morning → 200 with "the number ending in 02", `on_record: true`, the `PHONE_MORNINGS` `saved_line`; unverified thread, same body → 409 `not_verified`, no follow-up row | Step 5 | R `test_example_pair_2_phone_mornings` |
| PA-1 (plan-added) | A `CaseService` refusal object (AEA-29's `CaseActionRejected`, code `NOT_ALLOWED_IN_STATE`) maps to 409 with its `details`; anything else that is not a `FollowUp` is a 500, never an undocumented status | Step 5.3 | R `test_case_service_refusal_maps_to_409` |
| PA-2 (plan-added) | The hunk binds `get_person_requests()` to a real `PersonRequestService` when every dependency key is provided; otherwise build still succeeds and calling `request()` raises `RuntimeError("not bound: …")`; routes are included once; no web shell → nothing | Step 8 | `tests/unit/web/test_register_person_request.py::test_register_binds_service_and_routes`, `::test_register_unbound_raises_at_call`, `::test_register_ignores_app_without_web_shell` |
| PA-3 (plan-added) | A failed CON-4 leaves the turn row `failed` (not `running`), so the next tap re-runs instead of waiting 3 s and failing again | Step 3.8 | S `test_failed_open_marks_turn_failed_and_retry_reruns` |

**Source-contract reconciliation (beyond the ACs):**

| Obligation | Source | Disposition |
|---|---|---|
| `TurnIds.agent_version` is required but `PersonRequest` / the MC-17 constructor carry none | `domain/turn.py` `TurnIds`; web.md §8 | **added (engineering):** take `agent_version` from the thread's `ConversationRow.agent_version` (stamped by `SessionService.open` from `Settings.agent_version`, web.md §14). No signature change. Step 3.2 |
| `TurnRecord` needs `replied_at`, `server_ms`, counts | graph-core §2 | **added:** `replied_at = now` (the one demo reading), `server_ms` from `time.monotonic()`, every count 0, `cost_usd = 0.0` (no model, no tool). Step 3.9 |
| `TurnContext.budget` is required | graph-core §2 | **added:** `TurnBudget(started=mono, deadline=mono + TurnLimits().deadline_s)` (the one 60 s literal in `policy/limits.py`) |
| M-18 "conversation.outcome and end time" | DO-7 M-18; cases.md A-7 | **added:** `set_outcome(thread_id, "handed_off", ended_wall_at=self._wall_clock())` — this is what the MC-20 `wall_clock` parameter is for |
| CON-4 builds no brief | sign-off D-9 | n/a: `PersonRequestService` never calls `BriefAssembler` |
| `HandoffService.open`'s failure type is AEA-29's `CaseWriteFailed` (unmerged) | AEA-29 plan step 4 | **added:** catch `Exception` from `open` (documented `noqa: BLE001`), finish the turn `failed`, raise `HandoffWriteFailed` chained `from exc`. AEA-51 may narrow it (§8 R-3) |
| `FollowUpChoice` (AEA-29's parameter type) lives in the uncut `domain/views.py` | AEA-29 plan R-1, frozen test `_case_fixtures.py` | **added:** pass `FollowUpRequestBody` (same three fields, OpenAPI `FollowUpRequest`); structural match, `get_case_service()` returns `Any`. §8 R-2 |
| `set_followup` returns `FollowUp \| CaseActionRejected` and email/general raise `NotImplementedError` until AEA-03b | AEA-29 plan R-2, R-5 | **added:** PA-1; the `NotImplementedError` path stays a 500 (other-ticket: AEA-29 / AEA-03b). §8 R-4 |
| CON-4 during a reset waits ≤ 5 s | web.md §7 | in-ticket via AEA-23's middleware (`requestPerson` not in `RESET_503_OPERATIONS`); nothing to build |
| CAP-3 end to end (case, case_event, promise rows) | DO-6 | other-ticket: AEA-51 |
| Reload shows the card (`getChatThread`) | R-W-6 | other-ticket: AEA-40 reads the stored `block`; this ticket proves the stored shape (AC-20) |

**Entry-point registration:**

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `POST /api/chat/sessions/{thread_id}/handoff` (`requestPerson`) | WF-2 | yes (DO-6 WF-2; `OPERATIONS_BY_ROUTE` in `web/middleware.py`) | E-6; M-10…M-13, M-15; CAP-3 (AEA-51) |
| `PUT /api/chat/sessions/{thread_id}/follow-up` (`saveFollowUp`) | WF-2 | yes (same) | same |

## 4. Shared code to use (copied from `main` `c7ce976` and the addenda)

**From AEA-23 (merged), `src/meridian/web/deps.py`:**

```python
def get_request_context(request: Request) -> RequestContext: ...
def get_login_session(context: RequestContext = Depends(get_request_context)) -> LoginSession: ...
def get_person_requests(request: Request) -> Any: ...        # key PERSON_REQUESTS = Key("person_requests")
def get_case_service(request: Request) -> Any: ...           # key CASE_SERVICE = Key("case_service")      (AEA-29 / AEA-51 bind)
def get_demo_service(request: Request) -> Any: ...           # key DEMO_SERVICE = Key("demo_service")      (AEA-30 binds)
def get_reply_composer(request: Request) -> Any: ...         # key REPLY_COMPOSER = Key("reply_composer")  (AEA-21 / AEA-51 bind)
def get_uow_factory(request: Request) -> UnitOfWorkFactory: ...   # key UOW_FACTORY = Key("uow_factory") (AEA-10)
def owned_thread(thread_id: str, session: LoginSession = Depends(get_login_session),
                 uow: UnitOfWorkFactory = Depends(get_uow_factory)) -> ThreadId: ...
# other keys: HANDOFF_SERVICE = Key("handoff_service"), WALL_CLOCK = Key("wall_clock")
```

`src/meridian/web/middleware.py`: `RequestContext(request_id: RequestId, client_ip: str, session: LoginSession | None,
run_tag: Literal["live","eval","load"], run_id: str | None, turn_verdict: LimitVerdict | None)`; `RateLimiter(limits:
WebLimits)` with `check(scope, key, now: float, *, family: Literal["turn","read"] = "read")` and `peek(...)` (same
args); `LimitScope.SESSION`, `LimitScope.IP`; `WebShellState` (on `app.state.web_shell`).

`src/meridian/web/errors.py`: `ApiProblem(status: int, code: ApiErrorCode, *, field=None, constraint=None,
details: dict[str, object] | None = None, headers=None)`. The 422 handler already turns body errors into 400
`VALIDATION_ERROR` with `field` (e.g. `"turn_id"`, `"window"`, `"channel"`) and `constraint` = pydantic's `msg`.

`src/meridian/web/app.py`: `create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None)`;
`ContainerOverrides(choice=None, structured=None, tools=None, trace=None, wall_clock=None)`; module attribute
`build_container` (patched by test harnesses).

`src/meridian/web/container.py`: `Container.provide(key, factory)`, `.get(key)` (raises
`ContainerError("not provided: <name>")`), `Key[T](name)`; `register_web` provides `WALL_CLOCK` from
`app.state.web_shell.wall_clock` and returns early when the app has no `web_shell`. Hunk signature (keep it):
`def register_person_request(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:`.

Test support `tests/api/web_shell_support.py` (import, never edit): `make_settings(tmp_path, **changes)`,
`FakeSessionStore` (`.issue(role=DemoRole.CUSTOMER, *, now=None) -> str`, `.session_of(token) -> LoginSession`,
`.set_role(token, role)`), `FakeHeartbeat`, `MutableClock(start)` (`__call__`, `.advance(seconds)`), `make_client(app,
*, peer="198.51.100.7")`, `cookie_header(token)`, `error_body(resp, status, code)`, `without_request_id(resp)`,
`assert_matches(resp, operation_id)`, `captured_log()`, `records_of(stream, "request")`, `app_log_text(caplog)`,
`suppress_container_starters(monkeypatch)`. `tests/api/openapi_check.py`: `load_document()`, `load_contract()`.

**Storage (AEA-10, merged), reached as `tx.core.…` inside `with uow(write=…) as tx:`:**

```python
tx.core.conversations.lookup(thread_id: str) -> ConversationRow | EndedThread | None
tx.core.conversations.set_outcome(thread_id: ThreadId, outcome: str, *, ended_wall_at: datetime | None = None) -> None
tx.core.conversations.idle_live(cutoff_wall: datetime) -> tuple[tuple[ThreadId, datetime], ...]   # the sweep's selection
tx.core.turns.begin(ids: TurnIds, received_at: datetime) -> TurnBegin   # TurnBegin(status: "new"|"completed"|"running"|"failed", response: str | None)
tx.core.turns.finish(turn_id: TurnId, record: TurnRecord) -> None
tx.core.turns.get(turn_id: TurnId) -> TurnRow | None               # TurnRow.status, .thread_id, .response, .gate_result, …
tx.core.turns.for_thread(thread_id) -> tuple[TurnRow, ...]
tx.core.reads.identity_state(thread_id: ThreadId) -> IdentityState
tx.core.settled_for(thread_id: ThreadId, read_at: datetime) -> Settled
tx.commit()
# rows: from meridian.adapters.sqlite.rows import ConversationRow (fields: agent_version: str, controller: Controller, …)
```

`begin` semantics (as built): unknown id → inserts `running`, returns `new`; same id on another thread → `running`;
`completed` → returns the stored `response`; `failed` → re-arms to `running`, returns `failed`. **The write unit of
work must `commit()` after `begin`.**

**Domain and policy (merged):**

```python
from meridian.domain.common import ApiErrorCode, FollowUp, MeridianModel, RequestId, ThreadId, TurnId
from meridian.domain.handoff import HandoffReason, HandoffRequest, HandoffResult   # Priority via priority_for
from meridian.domain.blocks import HandoffBlock, LiveQueuedBlock, SettledView
from meridian.domain.actions import Settled
from meridian.domain.identity import IdentityState
from meridian.domain.state import Controller
from meridian.domain.turn import TurnBudget, TurnContext, TurnIds, TurnRecord, TurnTrace
from meridian.policy.handoff import priority_for      # priority_for(HandoffReason.CUSTOMER_REQUESTED_PERSON) -> Priority.P3
from meridian.policy.limits import TurnLimits          # TurnLimits().deadline_s == 60
from meridian.ports.runtime import Clock, TraceSink, UnitOfWorkFactory
```

`HandoffRequest(thread_id, turn_id, reason, priority, rule_id: str, trigger: Literal["gate","escalation","con4","safety"],
identity: IdentityState, change_request=None, safety_kind=None)`. `HandoffResult(case: CaseSummary, created: bool,
action: CompletedAction, alert)`; `CaseSummary.promise: Promise` (`live_queued: bool`); `action.key.turn_id` is the
turn that **opened** the case (AEA-29 returns the existing `case_opened` action on the already-open path).
`TurnContext(ids, budget, now, demo_session, span, intake=None)` (frozen dataclass).
`TurnTrace(gate_result, path, outcome, degrade_reason=None, …)`; `TurnRecord(status, trace, replied_at, server_ms,
model_calls, input_tokens, output_tokens, cost_usd, tool_calls, trace_id, trace_export, response)`.
`TraceSink.turn(ids) -> AbstractContextManager[SpanHandle]`; `TraceSink.export_status(turn: SpanHandle) -> ExportStatus`;
`SpanHandle.trace_id: str | None`.

**Siblings, by signature only (doubles in tests):**

```python
# AEA-29 HandoffService (cases.md §5):  open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult
#   idempotent per thread; writes no turn row; raises (CaseWriteFailed) after one retry
# AEA-29 CaseService (DO-4 §13 + AEA-29 plan R-2):
#   open_case_for_thread(self, thread_id: ThreadId) -> CaseSummary | None
#   set_followup(self, thread_id: ThreadId, choice: FollowUpChoice, now: datetime) -> FollowUp | CaseActionRejected
# AEA-21 ReplyComposer (graph-core §13):
#   handoff_block(self, result: HandoffResult) -> HandoffBlock | LiveQueuedBlock
#   settled_view(self, settled: Settled, identity: IdentityState, controller: Controller) -> SettledView
# AEA-30 DemoService (cases.md §6):  clock_view(self) -> ClockView   # read only `.now`
# Container keys these siblings provide: "handoff_service", "case_service", "reply_composer" (AEA-29 / 21 / 51),
#   "demo_clock" (AEA-30, a Clock), "demo_service" (AEA-30), "trace" (AEA-19, merged), "uow_factory" (AEA-10, merged),
#   "wall_clock" (AEA-23, merged)
```

**What this ticket defines** (web.md §8, copied; the two Protocols are typing only, because `services/` may not import
`agent/`, DO-3 §2.1, and `services/handoff.py` is unmerged; the real classes satisfy them structurally — the same pattern
AEA-29 uses for `_PresenceSource`):

```python
# src/meridian/services/person_request.py
RUNNING_WAIT_S: Final = 3.0     # [A] web.md §8 step 1; replaced by a measured CON-4 p99 at Stage 9
RUNNING_POLL_S: Final = 0.1     # poll interval while a duplicate press is running
CON4_RULE_ID: Final = "CON4.person"

class HandoffOpener(Protocol):
    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ...

class HandoffComposer(Protocol):
    def handoff_block(self, result: HandoffResult) -> HandoffBlock | LiveQueuedBlock: ...
    def settled_view(self, settled: Settled, identity: IdentityState, controller: Controller) -> SettledView: ...

class PersonRequest(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId; demo_session: str
    run_tag: Literal["live", "eval", "load"]; run_id: str | None

class PersonRequestOutcome(MeridianModel):
    result: Literal["case_created", "live_queued", "already_open"]
    block: Annotated[HandoffBlock | LiveQueuedBlock, Field(discriminator="type")]
    settled: SettledView

class HandoffWriteFailed(Exception): ...      # message carries no value

class PersonRequestService:
    def __init__(self, uow: UnitOfWorkFactory, handoff: HandoffOpener, composer: HandoffComposer,
                 trace: TraceSink, demo_clock: Clock, wall_clock: Callable[[], datetime]) -> None: ...
    def request(self, cmd: PersonRequest) -> PersonRequestOutcome: ...

def read_identity(uow: UnitOfWorkFactory, thread_id: ThreadId) -> IdentityState: ...
def settled_view_for(uow: UnitOfWorkFactory, composer: HandoffComposer, thread_id: ThreadId,
                     read_at: datetime) -> SettledView: ...
```

```python
# src/meridian/web/schemas/handoff.py   (field names = OpenAPI; MeridianModel forbids extra keys)
class HandoffRequestBody(MeridianModel):          # OpenAPI HandoffRequest
    turn_id: TurnId
class FollowUpRequestBody(MeridianModel):         # OpenAPI FollowUpRequest (= AEA-29's FollowUpChoice fields)
    channel: Literal["email", "phone"]
    destination: Literal["on_record", "general"]
    window: Literal["morning", "afternoon", "any"]
class FollowUpResponse(MeridianModel):            # OpenAPI FollowUpResponse
    followup: FollowUp
    settled: SettledView
HANDOFF_RETRY_AFTER_MS: Final = 3000              # [A] the OpenAPI requestPerson 503 example's details.retry_after_ms
```

## 5. Steps (build order; each is checkable on its own)

Dependency direction: `web/routes/handoff.py` → `web/schemas/handoff.py`, `services/person_request.py`, `web/deps.py`;
`services/person_request.py` → `domain`, `policy`, `ports`, `adapters/sqlite/rows` (row type only, as
`services/ledger.py` already does). Nothing under `services/` imports `web/` or `agent/`.

**Step 1 — schemas** (`web/schemas/handoff.py`). Write the three models and the constant from §4. Module docstring:
"Request and response bodies for CON-4 and CON-5 (AEA-42; OpenAPI HandoffRequest, FollowUpRequest, FollowUpResponse)."
`HandoffResponse` is not a second class: the route serialises `PersonRequestOutcome` unchanged.

**Step 2 — service types** (`services/person_request.py`, top half). The constants, Protocols, `PersonRequest`,
`PersonRequestOutcome`, `HandoffWriteFailed` from §4. Then the two helpers:

- `read_identity(uow, thread_id)`: `with uow() as tx: return tx.core.reads.identity_state(thread_id)`.
- `settled_view_for(uow, composer, thread_id, read_at)`: one read-only unit of work:
  `settled = tx.core.settled_for(thread_id, read_at)`; `identity = tx.core.reads.identity_state(thread_id)`;
  `row = tx.core.conversations.lookup(str(thread_id))`; after the `with`:
  `controller = row.controller if isinstance(row, ConversationRow) else Controller(kind="ai")`;
  return `composer.settled_view(settled, identity, controller)`. *Protects:* one builder of the panel for both ops
  (WEB-20); the panel always comes from stored rows.

**Step 3 — `PersonRequestService.request(cmd)`**, numbered as web.md §8:

1. `now = self._demo_clock.now()` (the **one** demo reading for `received_at`, `ctx.now`, `settled` and `replied_at`);
   `mono = time.monotonic()`.
2. Write unit of work: `row = tx.core.conversations.lookup(str(cmd.thread_id))`; if not a `ConversationRow` →
   `raise HandoffWriteFailed("thread is not open")` (a reset ended it after `owned_thread`; the next tap gets 410).
   `ids = TurnIds(thread_id=cmd.thread_id, turn_id=cmd.turn_id, request_id=cmd.request_id, run_tag=cmd.run_tag,
   run_id=cmd.run_id, agent_version=row.agent_version)`; `begin = tx.core.turns.begin(ids, now)`;
   `identity = tx.core.reads.identity_state(cmd.thread_id)`; `tx.commit()`.
3. Branch on `begin.status`: `"completed"` → `return PersonRequestOutcome.model_validate_json(begin.response)` (if
   `response` is `None` → `HandoffWriteFailed`); `"running"` → `return self._await_stored(cmd)`; `"new"` / `"failed"` →
   continue. `_await_stored(cmd)`:
   ```python
   deadline = self._wall_clock() + timedelta(seconds=RUNNING_WAIT_S)
   for _ in range(int(RUNNING_WAIT_S / RUNNING_POLL_S)):       # bounded even if a test freezes the wall clock
       with self._uow() as tx:
           row = tx.core.turns.get(cmd.turn_id)
       if row is None or str(row.thread_id) != str(cmd.thread_id) or row.status == "failed":
           raise HandoffWriteFailed("person request did not finish")
       if row.status == "completed" and row.response:
           return PersonRequestOutcome.model_validate_json(row.response)
       if self._wall_clock() >= deadline:
           break
       time.sleep(RUNNING_POLL_S)
   raise HandoffWriteFailed("person request still running")
   ```
   *Protects:* a double tap never creates a second case and never hangs past ~3 s (AC-5); another thread's `turn_id`
   is never answered from its row (PA-7 in `begin`).
4. `with self._trace.turn(ids) as span:` — steps 5–7 run inside; build
   `ctx = TurnContext(ids=ids, budget=TurnBudget(started=mono, deadline=mono + TurnLimits().deadline_s), now=now,
   demo_session=cmd.demo_session, span=span, intake=None)`.
5. `reason = HandoffReason.CUSTOMER_REQUESTED_PERSON`; `req = HandoffRequest(thread_id=cmd.thread_id,
   turn_id=cmd.turn_id, reason=reason, priority=priority_for(reason), rule_id=CON4_RULE_ID, trigger="con4",
   identity=identity)`; `try: result = self._handoff.open(req, ctx)` `except Exception as exc:  # noqa: BLE001` →
   remember `failure = exc`, `result = None`. (Reason for the broad catch, in a comment: AEA-29's `CaseWriteFailed` is
   the documented failure after its one retry and is not importable here; any failure must still leave the turn
   `failed`.)
6. Result rule (only when `result` is not `None`): `first = result.created or result.action.key.turn_id ==
   cmd.turn_id`; `kind = ("live_queued" if result.case.promise.live_queued else "case_created") if first else
   "already_open"`. *Protects:* a re-run of a failed turn whose case was written earlier answers as the first call did.
7. `block = self._composer.handoff_block(result)` (once); `view = settled_view_for(self._uow, self._composer,
   cmd.thread_id, now)` (runs **after** `open` committed, so the new case is in the panel);
   `outcome = PersonRequestOutcome(result=kind, block=block, settled=view)`.
8. After the `with` closes: `trace_id = span.trace_id`; `export = self._trace.export_status(span)`;
   `server_ms = int((time.monotonic() - mono) * 1000)`. If `result` is `None`: write unit of work →
   `tx.core.turns.finish(cmd.turn_id, TurnRecord(status="failed", trace=TurnTrace(gate_result="person_requested",
   path="handoff", outcome="degraded_handoff", degrade_reason="tool_error"), replied_at=now, server_ms=server_ms,
   model_calls=0, input_tokens=0, output_tokens=0, cost_usd=0.0, tool_calls=0, trace_id=trace_id,
   trace_export=export, response=""))`; `tx.commit()`; then `raise HandoffWriteFailed("case write failed") from failure`.
   *Protects:* the next tap re-runs (PA-3) instead of waiting on a stuck `running` row.
9. Success: `stored = outcome.model_dump_json()`; one write unit of work:
   `tx.core.turns.finish(cmd.turn_id, TurnRecord(status="completed", trace=TurnTrace(gate_result="person_requested",
   path="handoff", outcome="handed_off"), replied_at=now, server_ms=server_ms, model_calls=0, input_tokens=0,
   output_tokens=0, cost_usd=0.0, tool_calls=0, trace_id=trace_id, trace_export=export, response=stored))`; if
   `kind in ("case_created", "live_queued")`: `tx.core.conversations.set_outcome(cmd.thread_id, "handed_off",
   ended_wall_at=self._wall_clock())`; `tx.commit()`; `return outcome`. *Protects:* the stored body is byte-for-byte
   what the route returns (AC-20, R-W-6); the sweep never claims a handed-off chat (MC-18).

No logging in this module (nothing to log that the middleware's `request` record does not already carry). No string
containing "business day" or "representative will" anywhere in the three owned source files, comments and docstrings
included (AC-2's grep).

**Step 4 — `requestPerson` route** (`web/routes/handoff.py`):

```python
def build_router() -> APIRouter: ...   # returns a NEW APIRouter holding both routes

@router.post("/api/chat/sessions/{thread_id}/handoff", operation_id="requestPerson", response_model=None)
def request_person(body: HandoffRequestBody,
                   thread: ThreadId = Depends(owned_thread),
                   ctx: RequestContext = Depends(get_request_context),
                   session: LoginSession = Depends(get_login_session),
                   service: PersonRequestService = Depends(get_person_requests)) -> JSONResponse:
```

1. `cmd = PersonRequest(thread_id=thread, turn_id=body.turn_id, request_id=ctx.request_id,
   demo_session=str(session.session_id), run_tag=ctx.run_tag, run_id=ctx.run_id)`.
2. `try: outcome = service.request(cmd)` `except HandoffWriteFailed: raise ApiProblem(503,
   ApiErrorCode.HANDOFF_FAILED, details={"retry_after_ms": HANDOFF_RETRY_AFTER_MS}) from None`.
3. `return JSONResponse(outcome.model_dump(mode="json"))` (status 200).

Sync `def` (FastAPI runs it on the worker pool; the service does blocking SQLite). The path parameter must be named
`thread_id` (the middleware maps the template to the operation, and `owned_thread` reads it). `# noqa: B008` on each
`Depends(...)` default, as `web/deps.py` does.

**Step 5 — `saveFollowUp` route** (same file):

```python
@router.put("/api/chat/sessions/{thread_id}/follow-up", operation_id="saveFollowUp", response_model=None)
def save_follow_up(body: FollowUpRequestBody,
                   thread: ThreadId = Depends(owned_thread),
                   uow: UnitOfWorkFactory = Depends(get_uow_factory),
                   cases: Any = Depends(get_case_service),
                   demo: Any = Depends(get_demo_service),
                   composer: Any = Depends(get_reply_composer)) -> JSONResponse:
```

1. If `body.destination == "on_record"` and `read_identity(uow, thread).status != "verified"` →
   `raise ApiProblem(409, ApiErrorCode.NOT_ALLOWED_IN_STATE, details={"state": "not_verified"})` (before any service).
2. If `cases.open_case_for_thread(thread) is None` → `ApiProblem(409, NOT_ALLOWED_IN_STATE, details={"state":
   "no_open_case"})`.
3. `now = demo.clock_view().now`; `saved = cases.set_followup(thread, body, now)` (pass the body object itself; §8 R-2).
   If `not isinstance(saved, FollowUp)`: `code = getattr(saved, "code", None)`; `details = getattr(saved, "details",
   None)`; if `str(code) == ApiErrorCode.NOT_ALLOWED_IN_STATE.value and isinstance(details, Mapping)` →
   `raise ApiProblem(409, ApiErrorCode.NOT_ALLOWED_IN_STATE, details=dict(details))`; else
   `raise RuntimeError("saveFollowUp: unexpected result from set_followup")` (a 500, never an undocumented status).
4. `view = settled_view_for(uow, composer, thread, now)`;
   `return JSONResponse(FollowUpResponse(followup=saved, settled=view).model_dump(mode="json"))`.

**Step 6 — contract cases** (`tests/contract/cases/handoff.py`), same shape as `tests/contract/cases/auth.py`:
`ROUTE_FILE: Final = "handoff"`, `CASES: Final[dict[str, dict[str, object]]]`, each operation `{"public": False,
"drives": (…)}`, each drive `{"name", "status", "code" (errors only), "preconditions": tuple[str, ...], "setup"
(optional), "body"}`. Closed vocabulary, written in the module docstring:
preconditions `"login"` (customer cookie), `"thread"` (a live conversation of this session), `"open_case"` (a case on it,
created by a first `BUTTON` press), `"verified"` (identity verified as MHC-10002 + a `verified` action), `"ended"` (the
path id is this session's tombstone, reason `demo_reset`), `"unknown"` (a fresh UUID path id); setup `"handoff_fails"`;
body `{"example": "<name>"}`, `{"example": "BUTTON", "turn_id": "new"}` (the example with a fresh UUID),
`{"raw": <JSON>}`, or `None`. Drives:

| Operation | name | status / code | preconditions | setup / body |
|---|---|---|---|---|
| requestPerson | `case_created` | 200 | login, thread | `{"example": "BUTTON"}` |
| requestPerson | `already_open` | 200 | login, thread, open_case | `{"example": "BUTTON", "turn_id": "new"}` |
| requestPerson | `bad_turn_id` | 400 `VALIDATION_ERROR` | login, thread | `{"raw": {"turn_id": "not-a-uuid"}}` |
| requestPerson | `no_session` | 401 `UNAUTHENTICATED` | thread | `{"example": "BUTTON"}` |
| requestPerson | `not_found` | 404 `SESSION_NOT_FOUND` | login, unknown | `{"example": "BUTTON"}` |
| requestPerson | `ended` | 410 `SESSION_ENDED` | login, ended | `{"example": "BUTTON"}` |
| requestPerson | `handoff_failed` | 503 `HANDOFF_FAILED` | login, thread | setup `handoff_fails`; `{"example": "BUTTON"}` |
| saveFollowUp | `phone_mornings` | 200 | login, thread, verified, open_case | `{"example": "PHONE_MORNINGS"}` |
| saveFollowUp | `email_general` | 200 | login, thread, open_case | `{"example": "EMAIL_GENERAL"}` |
| saveFollowUp | `bad_window` | 400 `VALIDATION_ERROR` | login, thread, open_case | `{"raw": {"channel": "phone", "destination": "general", "window": "evening"}}` |
| saveFollowUp | `missing_channel` | 400 `VALIDATION_ERROR` | login, thread, open_case | `{"raw": {"destination": "general", "window": "any"}}` |
| saveFollowUp | `no_session` | 401 `UNAUTHENTICATED` | thread | `{"example": "EMAIL_GENERAL"}` |
| saveFollowUp | `not_found` | 404 `SESSION_NOT_FOUND` | login, unknown | `{"example": "EMAIL_GENERAL"}` |
| saveFollowUp | `no_open_case` | 409 `NOT_ALLOWED_IN_STATE` | login, thread | `{"example": "EMAIL_GENERAL"}` |
| saveFollowUp | `not_verified` | 409 `NOT_ALLOWED_IN_STATE` | login, thread, open_case | `{"example": "PHONE_MORNINGS"}` |
| saveFollowUp | `ended` | 410 `SESSION_ENDED` | login, ended | `{"example": "EMAIL_GENERAL"}` |

Local driver `tests/api/test_contract_cases_handoff.py::test_handoff_cases_drive_documented_statuses` (modelled on
`tests/api/test_contract_cases_auth.py`): builds a fresh harness per drive (§6), applies the preconditions, sends the
body, asserts status and code, calls `assert_matches(resp, op)`; then asserts every request example name in the
OpenAPI for both operations appears in some drive, and every documented non-200 status of each operation is covered.

**Step 7 — journey** (`tests/journeys/j7/test_aea_42.py`, `pytestmark = pytest.mark.journey`). Module docstring states
level `mock-tested` and *Blocked by* AEA-57 (harness), AEA-52 (integrated J-7) and AEA-40 (reload / `getChatThread`).
`test_j7_person_request_once_then_already_open`: harness (§6) with staffing `simulated_on_shift` (the
`RecordingHandoffService(presence="simulated_on_shift")` double); press 1 → 200 `live_queued`, `LiveQueuedBlock`;
press 2 with a new `turn_id` → `already_open`, `block` equal to press 1's block; stored: exactly one `cases` row for the
thread, `conversations.outcome == "handed_off"`, the press-1 turn row's `json.loads(response)["block"]` equals press 1's
`block`. `test_j7_reload_shows_card`: `@pytest.mark.skip(reason="blocked: getChatThread is AEA-40; integrated harness
AEA-57")` with the intended steps in its docstring (reported as skipped, never as passed).

**Step 8 — the hunk** (`web/container.py`, `register_person_request` only). New docstring (no "No-op until"; keep
"AEA-42"): "AEA-42 customer API: PersonRequestService, CON-4 and CON-5 routes (web.md §8). Provides deps.PERSON_REQUESTS
("person_requests") built from "uow_factory", "handoff_service", "reply_composer", "trace", "demo_clock" and
"wall_clock"; while any of those is not provided, the object it provides raises RuntimeError("not bound: …") when
called, so the app still starts. Includes the CON-4/CON-5 router once. An app without a web shell gets nothing."
Body (imports inside the function, as every hunk does):

1. `shell = getattr(app.state, "web_shell", None)`; if not a `WebShellState` → `return`.
2. Define `needed = (("uow", UOW_FACTORY), ("handoff", HANDOFF_SERVICE), ("composer", REPLY_COMPOSER),
   ("trace", Key[Any]("trace")), ("demo_clock", Key[Any]("demo_clock")), ("wall_clock", WALL_CLOCK))`.
3. Local class `_NotBound` with `__init__(self, missing: tuple[str, ...])` and `request(self, cmd: object) -> NoReturn`
   raising `RuntimeError("not bound: " + ", ".join(self.missing))`.
4. Factory `make(c)`: for each `(arg, key)`: `try: found[arg] = c.get(key)` `except ContainerError as exc:` if
   `str(exc) != f"not provided: {key.name}"` → `raise`; else append `key.name` to `missing`. Missing → return
   `_NotBound(tuple(missing))`; else `return PersonRequestService(**found)`.
5. `container.provide(PERSON_REQUESTS, make)`.
6. `if not getattr(app.state, "handoff_routes_included", False): app.include_router(build_router());
   app.state.handoff_routes_included = True`.
*Protects:* AEA-23's `full_app` tests and AEA-57's harness still start while AEA-29/30/21 are unmerged (AEA-29 plan R-3
names the same hazard); no duplicate routes when one app's lifespan runs twice.

**Step 9 — context (AC-23)**, after the code commit so the SHA exists:
- `.claude/reference/area-map.md` row A8, status cell: append one sentence "AEA-42 (`<sha>`): `web/routes/handoff.py`,
  `web/schemas/handoff.py`, `services/person_request.py` built." Change nothing else in the row.
- `docs/design/code-design.md` §3 module map: on the `person_request.py` line and the `routes/handoff.py ·
  schemas/handoff.py` line append `built AEA-42 <sha>` in the same style as `built AEA-19 2d5b692`.
- `.claude/state/icm-progress.md`: add one row after the last *Routes verified against code and tests* row:
  `| Routes verified against code and tests | provisional | <date>: area map A8 → web/routes/handoff.py, web/schemas/handoff.py, services/person_request.py checked by tests/services/test_person_request.py, tests/api/test_handoff_*.py (AEA-42, <sha>; <N> pass) | Each slice adds its route; verified when every area-map row is actual |` (≤ 400 characters).

## 6. Data and fixtures (all synthetic or read from the temp copy at run time)

**`tests/services/person_request_support.py`** (≤ 500 lines):

- `NOW = WORKED_PAIRS_NOW` (from `tests.fakes.clock`; Fri 2026-10-16 10:00 Chicago, a business day, nobody online);
  `WALL_T0 = datetime(2026, 10, 21, 15, 0, tzinfo=UTC)`; `AGENT = "test-agent-0"`; `CUSTOMER = "MHC-10002"`;
  `HINT = "the phone ending in 02"`.
- `open_thread(store, *, demo_session: str, now=NOW, last_customer_wall_at: datetime | None = None) -> ThreadId`:
  `ThreadId(str(uuid.uuid4()))`; one write unit of work: `tx.core.conversations.insert(ConversationRow(thread_id=…,
  demo_session=demo_session, run_tag="live", agent_version=AGENT, started_at=now, started_wall_at=WALL_T0,
  staffing_at_start="nobody_online", last_customer_wall_at=last_customer_wall_at))`;
  `tx.core.messages.append(thread_id, "assistant", "Hello, I am the automated assistant.", now)`; commit.
- `verify_thread(store, thread_id, *, now=NOW)`: `sqlite3.connect(store.db_path)`; `INSERT INTO identity_threads
  (thread_id, status, customer_id, masked_hint, channel, verified_at, updated_at) VALUES (?, 'verified', ?, ?, 'phone', ?, ?)`
  with `format_wall(now)` (from `meridian.adapters.sqlite.db`); commit; close; then a write unit of work recording
  `CompletedAction(key=ActionKey(thread_id=…, turn_id=TurnId(str(uuid.uuid4())), kind=ActionKind.VERIFIED,
  record_id=CUSTOMER), kind=ActionKind.VERIFIED, records={"customer": CUSTOMER}, at=now)`.
- `end_thread(store, *, demo_session: str) -> str`: a fresh UUID with **no** conversations row; `INSERT INTO
  ended_threads (thread_id, demo_session, ended_wall_at, reason, reset_id) VALUES (?, ?, ?, 'demo_reset', 'reset-test')`.
- `customer_contact(store) -> tuple[str, str]`: `tx.core.reads.customer(CustomerId(CUSTOMER))` → `(row.phone,
  row.email)`; used only for absence checks, never printed or written into a test file.
- `RecordingHandoffService(uow, *, presence: Presence = "nobody_online", fail: bool = False)`: `calls: list[tuple[
  HandoffRequest, TurnContext]]`. `open(req, ctx)`: record; if `fail` → `raise RuntimeError("case write failed")`; one
  write unit of work: `existing = tx.cases.cases.get_for_thread_open(req.thread_id)`; none → `ref =
  tx.cases.refs.next_case_ref()`, `promise = promise_for(req.reason, self.presence, ctx.now)`, insert `CaseRow(case_ref=
  ref, thread_id=req.thread_id, turn_id=req.turn_id, reason=req.reason, priority=req.priority, rule_id=req.rule_id,
  trigger=req.trigger, lifecycle="live_queued" if promise.live_queued else "unassigned", due_at=promise.due_at,
  created_at=ctx.now, updated_at=ctx.now)`, `tx.cases.promises.insert(ref, promise, ctx.now)`, `action =
  tx.core.actions.record(CompletedAction(key=ActionKey(thread_id=req.thread_id, turn_id=req.turn_id,
  kind=ActionKind.CASE_OPENED, record_id=str(ref)), kind=ActionKind.CASE_OPENED, records={"case": str(ref)},
  at=ctx.now))`, `created = True`; existing → `ref = existing.case_ref`, `action` = the `CASE_OPENED` row of
  `tx.core.actions.for_thread(req.thread_id)` with `key.record_id == str(ref)`, `created = False`. Build `CaseSummary`
  from `tx.cases.cases.get(ref)` and `tx.cases.promises.current(ref).promise` (`followup=None`, `version=row.version`,
  `due_at=row.due_at`); commit; return `HandoffResult(case=…, created=…, action=action, alert=None)`. Docstring: honours
  DO-4 §7 (one open case per thread, idempotent, no turn row); AEA-29's real rows are its own tests'.
- `RecordingComposer`: `block_calls: list[HandoffResult]`, `view_calls: list[tuple[Settled, IdentityState,
  Controller]]`. `handoff_block(result)`: record; speaker `Speaker(kind="assistant", display_name="Meridian assistant")`,
  `block_id=f"blk-{result.action.key.turn_id}-handoff"`, `at=result.action.at`; live-queued promise →
  `LiveQueuedBlock(reference=str(ref), promise_text=p.text, …)`; else `HandoffBlock(card_id=f"handoff-{ref}", options=(),
  answered=None, reference=str(ref), variant={"R26.refund": "refund", "R26.staffed": "staffed"}.get(p.policy_row,
  "nobody_online"), promise_text=p.text, due_at=p.due_at, due_label=p.due_label, extra_lines=p.extra_lines,
  followup_chooser=FollowUpOptions(legend=TEXTS[TextId.FOLLOWUP_LEGEND], channels=(), windows=(), general_only=True))`.
  `settled_view(settled, identity, controller)`: record; `request` from `settled.open_case` (`SettledRequest(reference=
  str(oc.case_ref), promise_text=oc.promise.text, due_at=oc.promise.due_at, due_label=oc.promise.due_label,
  extra_lines=oc.promise.extra_lines, live_queued=oc.live_queued, followup=oc.followup)`), `visit=None`, identity status
  `"not_checked"` when `identity.status == "located"` else the status, hint `identity.masked_hint` for `code_sent` /
  `verified` else `None`, `replying=SettledReplying(kind=controller.kind, display_name=controller.representative_name if
  controller.kind == "human" else None)`, `actions` = one `Write(kind=a.kind.value, summary=a.kind.value,
  turn_id=str(a.key.turn_id), at=a.at)` per action.
- `RecordingCaseService(uow)`: `calls: list[tuple[str, tuple[object, ...]]]`; `open_case_for_thread(thread_id)` reads
  `tx.cases.cases.get_for_thread_open` and returns the row or `None` (the route only tests `is None`);
  `set_followup(thread_id, choice, now) -> FollowUp`: record `(thread_id, choice, now)`; phone + on_record → read the
  identity's customer phone from the DB, `digits = <last two digits>`, `destination_label = f"the number ending in
  {digits}"`, `saved_line = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window={"morning": "mornings",
  "afternoon": "afternoons", "any": "any time"}[choice.window])`; any other choice → `destination_label = "a general
  contact"`, `saved_line = "Follow-up saved: " + choice.channel + ", " + window word + "."`; upsert a `FollowupRow`
  (`destination=choice.destination`, never the phone or email) on the open case; return the `FollowUp`. A `refuse:
  object | None` attribute, when set, is returned instead (PA-1).
- `FakeDemoService(clock)`: `clock_view()` returns `ClockViewStub(now=clock.now(), label="Fri Oct 16, 2026 · 10:00 am",
  date_label="Fri Oct 16, 2026 (demo date)")` (a frozen dataclass defined here); records calls.
- `make_service(store, *, handoff, composer, trace=None, clock=None, wall=None) -> PersonRequestService` with defaults
  `InMemoryTraceSink()`, `FixedClock()`, `MutableClock(WALL_T0)`.
- `person_request(thread_id, *, demo_session, turn_id=None) -> PersonRequest` (fresh UUIDs for `turn_id` /
  `request_id`, `run_tag="live"`, `run_id=None`).

**`tests/api/handoff_support.py`** (≤ 300 lines): `HandoffHarness` dataclass (`app, store, db, handoff, composer,
cases, demo, trace, wall, limiter`) and `handoff_app(monkeypatch, tmp_path, db, *, presence="nobody_online",
handoff_fails=False, trace=None, limiter=None) -> HandoffHarness`. It: calls `suppress_container_starters(monkeypatch)`;
monkeypatches `meridian.web.app.build_container` with a builder that creates `Container(settings=settings,
limits=Limits())`, runs `register_web(...)`, provides `UOW_FACTORY → db.uow`, `Key("trace") → trace or
InMemoryTraceSink()`, `Key("demo_clock") → FixedClock()`, `HANDOFF_SERVICE → RecordingHandoffService(db.uow, …)`,
`REPLY_COMPOSER → RecordingComposer()`, `CASE_SERVICE → RecordingCaseService(db.uow)`, `DEMO_SERVICE →
FakeDemoService(FixedClock())`, then runs **`register_person_request(...)`** (the real hunk) and `container.build()`;
then `app = create_app(make_settings(tmp_path), overrides=ContainerOverrides(wall_clock=wall))` with
`wall = MutableClock(WALL_T0)`; sets `app.dependency_overrides[get_login_sessions]`, `[get_staff_access]` to a
`FakeSessionStore()`, `[get_heartbeat]` to `FakeHeartbeat()`, and `[get_rate_limiter]` to `limiter` when given. Also
`customer_token(h) -> str` (`h.store.issue(now=WALL_T0)`) and `session_id_of(h, token) -> str`.

Every test that needs a DB uses `with temp_sqlite() as db:` (fresh copy, removed afterwards). No `.env`, no real
secret, no paid call, no socket; distinctive strings are letters only.

## 7. Checks

Run from the worktree with `export UV_LINK_MODE=hardlink`. pytest with **`-n 2` at most**. Never bind ports 4019 or
5184 (nothing here starts a server).

**While iterating:**
`uv run pytest tests/services/test_person_request.py tests/api/test_handoff_routes.py tests/api/test_handoff_capture.py tests/api/test_contract_cases_handoff.py tests/unit/web/test_register_person_request.py -q`

**Tests the implementer writes** (all must pass; names are binding):

- `tests/services/test_person_request.py`: `test_block_from_composer`, `test_handoff_request_fields`,
  `test_idempotent_turn_id`, `test_running_turn_waits_then_fails`, `test_settled_from_conversation_state`,
  `test_con4_marks_conversation_handed_off` (create a thread with `last_customer_wall_at=WALL_T0`, plus a control thread
  with the same value and no CON-4; run CON-4 with the wall clock at `WALL_T0`; read back `outcome == "handed_off"`;
  `tx.core.conversations.idle_live(WALL_T0 + timedelta(minutes=31) - timedelta(minutes=30))` contains the control
  thread and not the CON-4 thread), `test_stored_outcome_is_history_ready`, `test_already_open_block_names_existing_case`,
  `test_failed_open_marks_turn_failed_and_retry_reruns`.
  For `test_running_turn_waits_then_fails`: (a) begin a turn row as `running` directly (`tx.core.turns.begin(ids, NOW)`,
  commit); monkeypatch `meridian.services.person_request.time.sleep` with a function that, on its first call, finishes
  that row `completed` with a stored outcome JSON; assert `request()` returns it and the handoff double has 0 calls;
  (b) another `running` row, `sleep` patched to advance the `MutableClock` wall by 1 s per call; assert
  `HandoffWriteFailed` within ≤ 4 sleeps.
- `tests/api/test_handoff_routes.py`: `test_request_person_matches_openapi`, `test_request_person_passes_handoff_request`,
  `test_request_person_idempotent`, `test_person_key_never_limited` (limiter `RateLimiter(WebLimits(
  chat_turns_per_session_per_min=1, chat_turns_per_ip_per_min=1, reads_per_session_per_min=1, reads_per_ip_per_min=1))`;
  drain SESSION and IP in both families with `check(..., now=WALL_T0.timestamp(), family=…)` until `peek` says not
  allowed; POST → 200 `case_created`; assert `list(inspect.signature(PersonRequestService.__init__).parameters) ==
  ["self", "uow", "handoff", "composer", "trace", "demo_clock", "wall_clock"]`), `test_handoff_failed_503`,
  `test_session_not_found_identical`, `test_session_ended_410`, `test_follow_up_without_case_409`,
  `test_unverified_on_record_refused`, `test_save_follow_up_matches_openapi`, `test_both_responses_carry_settled`,
  `test_validation_error_names_field_not_value`, `test_nothing_claims_a_send`, `test_destination_masked_everywhere`,
  `test_login_gate_and_role_ignored`, `test_case_service_refusal_maps_to_409`,
  **`test_example_pair_1_case_created_then_already_open`** (WP pair 1: reference `MHC-C-0009` on a fresh store,
  `variant == "nobody_online"`, `due_at`/`due_label` equal `promise_for(CUSTOMER_REQUESTED_PERSON, "nobody_online",
  NOW)`'s, `settled.request.reference == block.reference`; new `turn_id` → `already_open` same reference, one `cases`
  row; same `turn_id` → the first body), **`test_example_pair_2_phone_mornings`** (WP-7 + WP-2: verified MHC-10002;
  a refund case seeded through `RecordingHandoffService.open` with a `HandoffRequest(reason=REFUND,
  priority=priority_for(REFUND), rule_id="test.refund", trigger="escalation", …)`; `PUT` `PHONE_MORNINGS` → 200,
  `destination_label == "the number ending in 02"`, `on_record is True`, `saved_line == "Follow-up saved: phone call,
  the number ending in 02, mornings."`; an unverified thread with an open case, same body → 409 `not_verified`, no
  `followups` row for it).
- `tests/api/test_handoff_capture.py::test_wf2_entry_points_emit_records` (harness with `trace=NullTraceSink()`;
  `with captured_log() as stream:` drive both ops; `records_of(stream, "request")` has one record per call with `route`
  = the template, `status`, `caller_role == "customer"`, `thread_id`, `request_id == resp.headers["X-Request-ID"]`; turn
  row `gate_result == "person_requested"`, `path == "handoff"`, `outcome == "handed_off"`, `trace_id is None`,
  `trace_export == "off"`; print the records and the row).
- `tests/api/test_contract_cases_handoff.py::test_handoff_cases_drive_documented_statuses`.
- `tests/unit/web/test_register_person_request.py`: `test_register_binds_service_and_routes`,
  `test_register_unbound_raises_at_call`, `test_register_ignores_app_without_web_shell`.
- `tests/journeys/j7/test_aea_42.py`: `test_j7_person_request_once_then_already_open` (+ the skipped reload step).

**Existing tests that must stay green** (the affected set: everything importing `meridian.web.container`, the web shell
or the touched packages): `tests/unit/web/` (incl. `test_container.py::test_every_register_stub_present`),
`tests/api/` (incl. `test_gate.py` and `test_app.py`, which build every hunk through `full_app`),
`tests/unit/test_import_direction.py`, `tests/unit/test_skeleton.py`, `tests/services/`, `tests/contract/`.

**Once before the final commit** (cheapest first; stop at the first red):

1. `uv run ruff check src tests && uv run ruff format --check src tests`
2. `uv run mypy` (configured paths: `src/meridian`, `tests`, `eval`; strict)
3. `uv run --with pytest-xdist pytest -n 2 tests/unit/web tests/api tests/services tests/contract tests/unit/test_import_direction.py tests/unit/test_skeleton.py -q`
4. `uv run python -m tests.journeys.affected --base main` and `uv run pytest -m journey tests/journeys/j7/test_aea_42.py -q`
5. `grep -rn "business day\|representative will" src/meridian/web/routes/handoff.py src/meridian/web/schemas/handoff.py src/meridian/services/person_request.py` → no output (AC-2)
6. After step 9's doc commit: `git diff --name-only main...HEAD` shows only §2's files (AC-23).

Passing looks like: all of the above green, the counts written into the journey record and the ICM row. The full suite
is **not** required: no shared fixture, settings, dependency or lockfile changes (`build-loop-test-scope.md`).
AC-21's strict command waits for AEA-59; record that in the journey record.

**Evidence record** `docs/testing/journeys/<run date>-AEA-42.md` in the AEA-26 record's table shape: Claim (CON-4,
CON-5, J-7 steps at mock level), Level `mock-tested`, Tested revision, Environment (VPS, `uv`, temp SQLite copy,
doubles for HandoffService / CaseService / ReplyComposer / DemoService, no server, no model), Command, Result, Evidence
location, Remaining limitations (real AEA-29/21/30 objects are AEA-51's; reload is AEA-40's; AC-21 strict waits for
AEA-59), Blocked by (AEA-57, AEA-52, AEA-40, AEA-59), Journeys that will exercise this code (J-7, J-6).

**Commits:** explicit `git add <paths>` only (never `-A`), two commits — code + tests, then context docs + record.
Message ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push.

**Must not:** edit any file outside §2; edit another hunk in `container.py`; change `web/deps.py` / `middleware.py` /
`app.py` / `errors.py` (a missing provider is a follow-up on AEA-23); compose or store any promise, due or follow-up
sentence; mask anything (AEA-29 masks); call a ledger, admission, limiter or model; build a brief; log any body, phone,
email or code; put a full phone number, email, code or card-like number in a test file or name; read `.env`; edit the
OpenAPI, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, issued data, the briefing, `docs/archive/`, `docs/parked/`.

## 8. Risks and requests

- **R-1 Shared A8 status cell (collision, low).** AEA-40, 41, 43, 49 append to the same area-map A8 cell in wave 2;
  append one sentence only, so the merge agent resolves a one-line conflict.
- **R-2 `FollowUpChoice` not on `main` (request to orchestrator, already raised by AEA-29 R-1 / AEA-30 R-1).** The
  route passes `FollowUpRequestBody`, which has exactly `FollowUpChoice`'s three fields; AEA-29's `set_followup` reads
  only `choice.channel`, `.destination`, `.window`. When the AEA-02b view-types follow-up lands, a one-line follow-up may
  convert with `FollowUpChoice.model_validate(body.model_dump())`. No blocker.
- **R-3 Broad catch around `HandoffService.open`.** Catches any exception because `CaseWriteFailed` (AEA-29) is not
  importable here; the original is chained (`from exc`) and the turn is finished `failed`. AEA-51 may narrow it to
  `CaseWriteFailed` once both are on `main`.
- **R-4 `email` / `general` follow-ups 500 with the real `CaseService` until AEA-03b** (AEA-29 plan R-5). This ticket's
  tests use a double, so `EMAIL_GENERAL` passes here; AEA-59's strict run against real services (AEA-51) will fail that
  case until AEA-03b. Owner: AEA-29 / AEA-03b, not this ticket.
- **R-5 `agent_version` on the CON-4 turn row** comes from the conversation row (the version that opened the chat), not
  from `Settings` (the MC-17 constructor has no such argument). Same value except across a deploy mid-conversation.
- **R-6 Unbound providers.** Until AEA-51 binds `handoff_service` / `reply_composer` and AEA-30 binds `demo_clock`, a
  real deployed CON-4 answers 500 (`not bound: …`), as web.md §4 specifies for unbound providers. AC-19 and every route
  test bind doubles.
- **R-7 The 3-s wait reads the injected wall clock** and is also capped at 30 polls, so a frozen test wall clock
  (D-13 overrides) cannot hang it.

## 9. Readiness

**READY.** Every import this plan needs is on `main` `c7ce976` (AEA-02, 10, 11, 14, 19, 23 merged). AEA-21, 29, 30 are
reached through their signed signatures by container key / FastAPI provider and tested with doubles; no product
decision or signed-contract change is needed. Gates: none.
