## [AEA-42] customer API: person request and follow-up (CON-4, CON-5)

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

> **US-2:** "As a **homeowner**, I need a "Talk to a person" control that is always visible and works the first time
> (button or words), so that I never have to argue with a bot to reach someone."
> **US-14:** "As a **homeowner** whose request needs a person, I need a reference number, the exact promise (who gets
> back to me and by when), and a choice of email or phone and a time window, so that I know what happens next and never
> repeat my story."

**`requestPerson`** (CON-4, `POST /api/chat/sessions/{thread_id}/handoff`), built as a thin route over a new service
(stage7/web.md §8; WEB-21, WEB-22; MC-17, MC-18, MC-27):

- `web/routes/handoff.py` resolves the thread with `owned_thread` (stage7/web.md §4), builds
  `PersonRequest(thread_id, turn_id from the body, request_id, demo_session=str(session.session_id), run_tag, run_id)`
  from `RequestContext`, calls `PersonRequestService.request` through `get_person_requests()`, and serialises
  `PersonRequestOutcome` as `HandoffResponse` unchanged. `HandoffWriteFailed` → 503 `HANDOFF_FAILED`.
- `services/person_request.py` (owned here; MC-27), constructor `PersonRequestService(uow, handoff: HandoffService,
  composer: ReplyComposer, trace: TraceSink, demo_clock: Clock, wall_clock)` (MC-17), runs stage7/web.md §8's six steps:
  1. `core.turns.begin(ids, received_at)`: `completed` → the stored outcome (same body as the first call); `running` →
     wait ≤ 3 s [A] for it, else `HandoffWriteFailed`; `new` / `failed` → run.
  2. Inside `with trace.turn(ids) as span:` build the `HandoffRequest` with every required DO-4 §7 field: `thread_id`,
     `turn_id`, `reason=customer_requested_person`, `priority=priority_for(reason)` (P3, stage7/cases.md §3.3, AEA-14),
     `rule_id="CON4.person"`, `trigger="con4"`, `identity=core.reads.identity_state(thread_id)` (stage7/cases.md §1.2).
  3. `HandoffService.open(req, ctx)` with `TurnContext(ids, budget, now=<one demo-clock reading>,
     demo_session, span=span, intake=None)` (stage7/graph-core.md §2).
  4. Result: created → `case_created`, or `live_queued` when the promise is live-queued; not created and the case's
     `turn_id` equals this one → the first call's result; otherwise `already_open`.
  5. Block from `ReplyComposer.handoff_block(result)`; `settled` from `core.settled_for(thread_id, read_at=ctx.now)` made
     the wire view by `composer.settled_view(settled, core.reads.identity_state(thread_id), <conversation controller>)`
     (stage7/graph-core.md §6, §13; WEB-20).
  6. After the span closes, `core.turns.finish(turn_id, TurnRecord(status="completed", trace=TurnTrace(gate_result=
     "person_requested", path="handoff", outcome="handed_off"), trace_id=span.trace_id,
     trace_export=trace.export_status(span), response=<stored outcome>, …))`, and in the same transaction, when the result
     is `case_created` or `live_queued`, `conversations.outcome = 'handed_off'` (stage7/cases.md A-7; MC-18). The stored
     `response` is the `PersonRequestOutcome` body exactly as returned, with the card under the key `block`; AEA-40's
     `SessionService.thread()` reads it to show the request in the history (stage7/web.md §14; R-W-6; AEA-42-1).
  No admission, no `SpendGuard`, no rate limit, no model (OpenAPI `requestPerson`; stage7/web.md §5 table).

**`saveFollowUp`** (CON-5, `PUT /api/chat/sessions/{thread_id}/follow-up`), a direct route (stage7/web.md §8 last
paragraph): `owned_thread`; if `destination == "on_record"` and `core.reads.identity_state(thread_id)` is not verified
→ 409 `NOT_ALLOWED_IN_STATE` `details.state: "not_verified"` before any service call (WEB-23); if
`CaseService.open_case_for_thread(thread_id)` is `None` → 409 `NOT_ALLOWED_IN_STATE` `details.state: "no_open_case"`
(OpenAPI example); else `CaseService.set_followup(thread_id, choice, now=DemoService.clock_view().now)` (DO-4 §13;
stage7/cases.md §5, §6) and return its `FollowUp` (= OpenAPI `FollowUpView`, masked by AEA-29) unchanged with `settled`
built as in step 5.

**Example pair 1 (CON-4, OpenAPI example `CASE_CREATED`).** Nobody online. Request `POST …/handoff` with
`{"turn_id": "9a316052-be7f-4e96-8c43-3e5f60718293"}` and the `mhc_session` cookie. Response 200: `result:
"case_created"`; block `type: "handoff"`, a reference from `refs.next_case_ref()` (live cases number from MHC-C-0009,
stage7/cases.md §7; the example shows MHC-C-0007), `variant: "nobody_online"`, promise text, `due_at` and `due_label`
exactly as `promise_for` produced them (R-26 row `R26.unstaffed`, one business day), `produced_by_code: true`;
`settled.request.reference` equals the block's. A second tap with a new `turn_id` returns `result: "already_open"` with
the same reference and no second case (example `ALREADY_OPEN`); the same `turn_id` again returns the first body.

**Example pair 2 (CON-5, tied to WP-7 and WP-2).** After WP-7's refund handoff (promise "A representative will get to
your refund request within 2 business days"), the verified customer MHC-10002 picks phone, mornings: `PUT …/follow-up`
`{"channel": "phone", "destination": "on_record", "window": "morning"}` → 200 (example `PHONE_MORNINGS`):
`followup.destination_label` "the number ending in 02", `on_record: true`, `saved_line` "Follow-up saved: phone call, the
number ending in 02, mornings."; nothing says a message was sent. The same body from an unverified thread → 409
`NOT_ALLOWED_IN_STATE` `{state: "not_verified"}` and no follow-up row.

**Produced for other issues:** the two operations and `PersonRequestService` for AEA-51 (binds the real
`HandoffService`, `CaseService`, `ReplyComposer` and trace sink; proves CAP-3) and AEA-55 (UI against the real backend).

### Source

- PRD R-2, R-24, R-25, R-26, R-27, R-34, R-41; US-2, US-14; WP-7, WP-2 (`docs/data/worked-pairs.md`).
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml` (read-only): `requestPerson` (200 / 400 / 401 / 404 / 410 /
  503 `HANDOFF_FAILED` `details.retry_after_ms`), `saveFollowUp` (200 / 400 / 401 / 404 / 409 / 410); schemas
  `HandoffRequest`, `HandoffResponse`, `HandoffBlock`, `LiveQueuedBlock`, `FollowUpRequest`, `FollowUpResponse`,
  `FollowUpView`, `Settled`, `ApiError`.
- `docs/design/contracts/stage7/web.md` §1 (`ApiProblem`), §4 (`owned_thread`, `get_person_requests`,
  `get_case_service`, `get_reply_composer`, `get_demo_service`, `get_uow_factory`), §5 (CON-4 never limited), §7
  (`requestPerson` waits for a reset, its 503 is `HANDOFF_FAILED`), §8 (`PersonRequestService`), §10 (`request` record),
  §13 (`openapi_check.py`). Decisions WEB-20, WEB-21, WEB-22, WEB-23, WEB-24, WEB-34, WEB-35
  (`docs/plans/7b-decisions/web.md`); merge MC-16, MC-17, MC-18, MC-27.
- `docs/design/contracts/stage7/cases.md` §1.2 (`core.turns.begin/finish`, `core.reads.identity_state`,
  `core.conversations.lookup`, `core.messages.handoff_anchor`), §3.2–§3.3 (`promise_for`, `priority_for`), §5
  (`HandoffService.open` writes no turn row; `CaseService`), §6 (`DemoService.clock_view`), A-7.
- `docs/design/contracts/stage7/graph-core.md` §2 (`TurnContext`, `TurnRecord`, `TurnTrace`), §6 (`settled_for`), §13
  (`ReplyComposer.handoff_block`, `settled_view`); `stage7/models.md` §4 (`SpanHandle`, `export_status(span)`).
- DO-4 §7 (`HandoffRequest`, `HandoffResult`), §13 (`CaseService.set_followup`, `open_case_for_thread`).
- DO-2 §8.2 *Handoff (CON-4 and the handoff node)*, §8.3 *Promise*. DO-6 WF-2, CAP-3; DO-7 M-10…M-13, M-15; DO-5 E-6 and
  *Expected-answer authority* ("Handoff promise, priority and reference").
- Slice plan §0a (journey map, J-7) and rule `.claude/rules/integrated-journeys.md` §3–§4; UX-join amendments
  `docs/plans/ux-join/backend-amendments.md` AEA-42-1, AEA-42-2 and §3; residual R-W-6
  (`docs/plans/7b-decisions/residuals-web.md`).
- Slice plan row AEA-42 and §0; area-map row A8 Customer API; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Escalation must be graceful: the agent recognizes it is out of scope, tells the caller what is
  happening, and hands off with enough context that a human can pick up without starting over." (briefing Part B §4);
  touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Every `requestPerson` 200 body validates for each result: `created=True` with a non-live promise → `case_created` + `HandoffBlock`; `created=True` with a live-queued promise → `live_queued` + `LiveQueuedBlock`; `created=False` → `already_open` with the existing case's block — verify: `tests/api/test_handoff_routes.py::test_request_person_matches_openapi` (`assert_response_matches(response, "requestPerson")`, stage7/web.md §13) — evidence: three bodies validate, one per `result` value.
- [ ] AC-2 [invariant] The block is exactly what `ReplyComposer.handoff_block(result)` returned (recording double called once with the `HandoffResult`), and no file of this issue holds a promise sentence — verify: `tests/services/test_person_request.py::test_block_from_composer` plus `grep -rn "business day\|representative will" src/meridian/web/routes/handoff.py src/meridian/web/schemas/handoff.py src/meridian/services/person_request.py` — evidence: equality assert passes; grep prints nothing.
- [ ] AC-3 [invariant] **WF-2** (CON-4 `requestPerson`): The `HandoffRequest` passed to `HandoffService.open` carries `thread_id`, the body's `turn_id`, `reason=customer_requested_person`, `priority` P3 from `priority_for`, `rule_id="CON4.person"`, `trigger="con4"` and the identity from `core.reads.identity_state`; its `TurnContext` has `intake=None`, the span yielded by `trace.turn(ids)` and one demo-clock reading as `now` (stage7/web.md §8 steps 2–3) — verify: `tests/services/test_person_request.py::test_handoff_request_fields` (temp SQLite, recording `HandoffService` double), and `tests/api/test_handoff_routes.py::test_request_person_passes_handoff_request` (TestClient through the real AEA-23 middleware, same recording double) — evidence: every field asserted, in both tests.
- [ ] AC-4 [invariant] Idempotent per `turn_id` and per thread: the same body twice returns the identical body (apart from `request_id`) and leaves one `turn` row; a new `turn_id` after a case exists returns `already_open` with the same reference — verify: `tests/services/test_person_request.py::test_idempotent_turn_id` and `tests/api/test_handoff_routes.py::test_request_person_idempotent` — evidence: bodies equal; `turns` count for the thread is 2 after three presses; third `result` is `already_open`.
- [ ] AC-5 [failure/refusal] A `turn_id` whose row is `running` waits up to 3 s [A] for the stored outcome and returns it; if none arrives, the press answers 503 `HANDOFF_FAILED` — verify: `tests/services/test_person_request.py::test_running_turn_waits_then_fails` (fake clock) — evidence: first case returns the stored body; second raises `HandoffWriteFailed` → 503.
- [ ] AC-6 [failure/refusal] **WF-2** (CON-4 `requestPerson`): "Talk to a person" is never limited (R-41; DO-2 §8.2): with the middleware's session and IP buckets exhausted and `ledger.allow_turn()` false, `requestPerson` still answers 200; `PersonRequestService` takes no ledger, admission or limiter argument (stage7/web.md §8) — verify: `tests/api/test_handoff_routes.py::test_person_key_never_limited` (real AEA-23 middleware) — evidence: 200 `case_created`; no 429; constructor signature asserted with `inspect.signature`.
- [ ] AC-7 [failure/refusal] `HandoffService.open` raising after its one retry → 503 `HANDOFF_FAILED` with `details.retry_after_ms` and no reference; the turn row is not `completed` — verify: `tests/api/test_handoff_routes.py::test_handoff_failed_503` — evidence: body validates against the 503 response; turn status read back is not `completed`.
- [ ] AC-8 [failure/refusal] On both operations a malformed id (`thr_9d41`), an unknown UUID and another session's thread answer the identical 404 `SESSION_NOT_FOUND` through `owned_thread` (WEB-34); nothing is written — verify: `tests/api/test_handoff_routes.py::test_session_not_found_identical` — evidence: the 404 bodies differ only in `request_id`; no case, turn or follow-up row.
- [ ] AC-9 [failure/refusal] On both operations a thread of this session that a demo reset ended (`EndedThread`) answers 410 `SESSION_ENDED` `details.reason: "demo_reset"` (MC-16) — verify: `tests/api/test_handoff_routes.py::test_session_ended_410` — evidence: 410 bodies validate against `SessionEnded`.
- [ ] AC-10 [failure/refusal] `saveFollowUp` on a thread with no open case answers 409 `NOT_ALLOWED_IN_STATE` `details.state: "no_open_case"` — verify: `tests/api/test_handoff_routes.py::test_follow_up_without_case_409` — evidence: body matches the OpenAPI example's code and details; `set_followup` never called.
- [ ] AC-11 [failure/refusal] An unverified thread asking for `destination: "on_record"` answers 409 `NOT_ALLOWED_IN_STATE` `details.state: "not_verified"` before any service call; `destination: "general"` from the same thread saves (WEB-23) — verify: `tests/api/test_handoff_routes.py::test_unverified_on_record_refused` — evidence: `set_followup` double records zero calls for `on_record`, one for `general`; no follow-up row for the refused request.
- [ ] AC-12 [invariant] `saveFollowUp` 200 validates against `FollowUpResponse`; `followup` is `CaseService.set_followup`'s return unchanged ("the number ending in 02", the `PHONE_MORNINGS` `saved_line`), called with `now = DemoService.clock_view().now` — verify: `tests/api/test_handoff_routes.py::test_save_follow_up_matches_openapi` — evidence: schema validation passes; equality and call-argument asserts pass.
- [ ] AC-13 [invariant] **WF-2** (both operations, `requestPerson` and `saveFollowUp`): Both responses carry `settled` built by `core.settled_for(thread_id, read_at=<demo now>)` and `ReplyComposer.settled_view(...)`; a thread with a prior `verified` action shows it, and `settled.request.reference` equals the block's reference (WEB-20) — verify: `tests/services/test_person_request.py::test_settled_from_conversation_state`, and `tests/api/test_handoff_routes.py::test_both_responses_carry_settled` (TestClient: one `requestPerson` and one `saveFollowUp` on a thread with a prior `verified` action) — evidence: the verified action and the reference read back in `settled` of both responses.
- [ ] AC-14 [failure/refusal] **WF-2** (`requestPerson`, `saveFollowUp`): `VALIDATION_ERROR` (400): `turn_id` "not-a-uuid" on `requestPerson`; `window: "evening"` and a missing `channel` on `saveFollowUp` each name `error.field` and a `constraint`, never the value — verify: `tests/api/test_handoff_routes.py::test_validation_error_names_field_not_value` (caplog) — evidence: `field` is `turn_id` / `window` / `channel`; "not-a-uuid" and "evening" appear in neither the body nor any captured log record.
- [ ] AC-15 [negative] **WF-2** (both operations): No response says a message was sent (R-34): no string in any CON-4 or CON-5 body contains "was sent", "we sent", "emailed you" or "called you" — verify: `tests/api/test_handoff_routes.py::test_nothing_claims_a_send` over every example-shaped response — evidence: assertion passes for all bodies.
- [ ] AC-16 [negative] **WF-2** (both operations): The full contact value never leaves the record: the seeded customer's full phone number and email, read from the issued DB at test time (never written into the test file), appear in no response body, captured log record or trace-double span of either operation; only "ending in 02" appears — verify: `tests/api/test_handoff_routes.py::test_destination_masked_everywhere` (caplog + trace double) — evidence: absent everywhere; the masked label present.
- [ ] AC-17 [invariant] **WF-2** (both operations): Login gate and roles: without `mhc_session` both operations answer 401 `UNAUTHENTICATED` (`details.reason: "none"`) from the real AEA-23 middleware; with the session's role switched to `representative` both still answer 200 (x-roles: every role; R-48) — verify: `tests/api/test_handoff_routes.py::test_login_gate_and_role_ignored` — evidence: 401 bodies validate against `Unauthenticated`; 200 under a staff role.
- [ ] AC-18 [invariant] A CON-4 that creates or live-queues a case sets `conversations.outcome = 'handed_off'` in the transaction that finishes the turn row (MC-18), so the abandonment sweep's selection (run_tag `live`, outcome `open`, last customer message ≥ 30 wall-minutes old; stage7/cases.md §6) cannot pick it 31 minutes later — verify: `tests/services/test_person_request.py::test_con4_marks_conversation_handed_off` (temp SQLite; the sweep's selection evaluated as stage7/cases.md §6 states it, or AEA-30's `SchedulerJob.tick` with the wall clock +31 min if AEA-30 has merged) — evidence: outcome `handed_off` read back; the sweep selects 0 rows.
- [ ] AC-19 [capture] Driving both entry points through the app the container builds (real AEA-23 middleware, service doubles where siblings are unmerged) leaves one `request` record per call with route template, status, `caller_role`, `thread_id` and `request_id` equal to `X-Request-ID` (WF-2); the CON-4 call also leaves one `turn` row with `gate_result = person_requested`, `path = handoff`, `outcome = handed_off`, `trace_id` from the span and `trace_export` from `trace.export_status(span)` (`off` with a `NullTraceSink`-shaped double, stage7/models.md §4) — verify: `tests/api/test_handoff_capture.py::test_wf2_entry_points_emit_records` — evidence: records and the turn row printed in the test output. (CAP-3 end to end, with the real case, case_event and promise rows: AEA-51.)
- [ ] AC-20 [invariant] The CON-4 turn row is history-ready and a second press can draw the card: the row's stored response is the `PersonRequestOutcome` body exactly as returned (`result`, `block`, `settled`), with the card under the key `block`, and its trace `gate_result` is `person_requested`, so AEA-40's `thread()` can show it (stage7/web.md §14; R-W-6); a second press with a **new** `turn_id` on a thread with an open case answers `already_open` whose `block` is the open case's card (the same reference and promise text as the first answer) (AEA-42-1; customer audit A-2, B-1) — verify: `tests/services/test_person_request.py::test_stored_outcome_is_history_ready` and `::test_already_open_block_names_existing_case` — evidence: the stored JSON equals the first response; the second response's `block.reference` and promise equal the first's.
- [ ] AC-21 [contract] `tests/contract/cases/handoff.py` holds the server cases for `requestPerson` and `saveFollowUp`: preconditions (a thread; a thread with an open case; an unverified thread), every named request example, and each documented error status the route can produce (`requestPerson`: 400, 401, 404, 410, 503 `HANDOFF_FAILED`; `saveFollowUp`: 400, 401, 404, 409 `NOT_ALLOWED_IN_STATE` with `state` `no_open_case` and `not_verified`, 410) (AEA-42-2) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "requestPerson or saveFollowUp" -rs` once AEA-59's runner is merged — evidence: one pass per case; skips only as `not bound: <name>` for a later issue's provider.
- [ ] AC-22 [journey] Extends J-7 (slice plan §0a journey map): "Talk to a person" creates one case (live-queued while staffed), a second press with a new `turn_id` answers `already_open` with the same card, and after a reload the card is in `getChatThread` (customer audit A-2, B-1); asserting what the user sees and what is stored, in `tests/journeys/j7/test_aea_42.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j7/test_aea_42.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-42.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-23 [regression/context] Same change updates: `.claude/reference/area-map.md` row A8 (`web/routes/handoff.py`, `web/schemas/handoff.py`, `services/person_request.py` planned → actual + commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link), DO-3 §3 lines for those three files marked built — verify: `git diff --name-only` — evidence: the three docs in the diff, only this issue's rows changed.

### Observability

- Responsibilities: for WF-2 (DO-6 registry: request, turn `person_requested`, case, case_event, promise), preserve the middleware's `request` record on both operations; write the CON-4 `turn` row with `gate_result`, `path`, `outcome`, `trace_id` and `trace_export` (stage7/web.md §8 step 6, MC-17), so DO-6's "`turn.trace_export` on every turn" holds for CON-4; pass `thread_id` and `turn_id` into `HandoffService.open` so AEA-29's `case`, `case_event` and `promise` rows carry them. No free text, contact value or code reaches a log line or span (DO-6 *Content and redaction*, LOG allow-list).
- Capture evidence: AC-19 drives both real entry points and reads the records back; AC-20 proves the stored CON-4 outcome is the body AEA-40's history reads; AC-14 and AC-16 are the negative checks; CAP-3 end to end is AEA-51's.

### Evaluation

- Checks: E-6 (handoff and brief slice) stays scorable on WF-2: the promise and reference this route returns are the ones code stored, built by the one `ReplyComposer` (AC-2), so "promise and reference appended by code equal the policy table" can be judged from the records.
- Expected-answer authority: the R-26 policy table (exact strings, `PROMISE_TABLE`, stage7/cases.md §3.2) and the D4 priority table, never the model (DO-5 *Expected-answer authority*, row "Handoff promise, priority and reference").

### Metrics

- References: M-10 (promise text consistency), M-11 (brief required-item recall), M-12 (invented facts in briefs), M-13 (promises kept on time), M-15 (person on the first request), all inherited from WF-2.
- Acceptance conditions: M-10 stays computable because `promise.text` reaches the customer only through `handoff_block` (AC-2); M-15 because the first press writes a `person_requested` turn with `outcome = handed_off` (AC-4, AC-19); M-13 because `due_at` passes through unchanged and the conversation is not later miscounted as abandoned (AC-18); M-11 and M-12 because CON-4 calls no model and writes no brief text, so it adds no brief item or invented fact, while `HandoffService` anchors its staff-guidance lookup rows on the newest customer message (stage7/cases.md §5, CAS-38). No target is set here.

### Blocked by

AEA-23 (slice plan row AEA-42).

Evidence only, not a merge edge (wave unchanged): AC-21's strict run waits for AEA-59's runner, and AC-22's journey
record stays `mock-tested` with *Blocked by* AEA-57 and AEA-52 until they land (`integrated-journeys.md` §4).

### Agent handoff

- **Area / owner:** A8 Customer API; files `src/meridian/web/routes/handoff.py`, `src/meridian/web/schemas/handoff.py`,
  `src/meridian/services/person_request.py` (MC-27, WEB-22), this issue's `register_<area>()` hunk in
  `web/container.py` (stub from AEA-01; binds `get_person_requests()`), tests under `tests/api/` and `tests/services/`,
  `tests/contract/cases/handoff.py` (AC-21) and `tests/journeys/j7/test_aea_42.py` (AC-22; `tests/journeys/support/` is
  AEA-57's, never edited here).
- **Contracts and shared surfaces:** consumes `HandoffService.open`, `CaseService.set_followup` /
  `open_case_for_thread` (AEA-29, injected), `ReplyComposer` (AEA-21, injected), `DemoService.clock_view` (AEA-30,
  injected), `priority_for` (AEA-14), `core.turns`, `core.reads.identity_state`, `core.settled_for`,
  `core.conversations.lookup` and `temp_sqlite()` (AEA-10), `TraceSink` / `SpanHandle` / `TurnContext` / `TurnRecord`
  (AEA-02), `owned_thread`, the providers, `ApiProblem` and `tests/api/openapi_check.py` (AEA-23). Produces CON-4, CON-5
  and `PersonRequestService` for AEA-51 and AEA-55. Must not edit `web/{app,middleware,deps,errors}.py`,
  `routes/auth.py`, any other route or schema file, `services/{cases,handoff,demo}.py`, `domain/*`, `policy/*`,
  `repos_core.py` or the OpenAPI.
- **Scope boundary / refusal:** no model call, no spend-guard, admission or rate-limit call, no promise or due-time text
  composed here, no masking here (AEA-29 masks); the graph's own handoffs (WP-7 through CON-2) are AEA-39/AEA-40's; no
  SSE (AEA-41).
- **Slice-plan note (informational; nothing open):** `PersonRequestService` imports `priority_for` (AEA-14) and its tests use
  AEA-10's repositories and `temp_sqlite()`; both are wave 1, merged before wave 2 starts, so the wave is unchanged. If a
  planner finds either unmerged, record `blocked-on AEA-14` / `blocked-on AEA-10`.
- **Wave and gates:** wave 2; no gate.
- **Lane:** build-loop — adds route, schema, service code and tests (`ticket-lanes.md`).
- **Risk:** None (slice plan). Contact values are masked by AEA-29's `CaseService`; this issue only copies them (AC-16
  proves nothing unmasked leaks).
- **Entry points added or changed:** WF-2 (`POST /api/chat/sessions/{thread_id}/handoff`, `PUT /api/chat/sessions/{thread_id}/follow-up`)
