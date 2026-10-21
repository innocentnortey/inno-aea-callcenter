## [AEA-40] customer API: sessions and turns (CON-1, CON-2)

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

> **US-1:** "As a **homeowner**, I need the chat to say plainly that it is Meridian's automated assistant and to show the
> date it is working from, so that I never think I'm talking to a person and every "tomorrow" or "Friday" means what I
> think it means." **US-26:** "As a **reviewer**, I need prompt injection, account fishing and spam to meet limits that end
> in a polite handoff, so that I see "clean failure", not a crash or a leak."

**Example pair (CON-1, then CON-2 with WP-2 and a retry).** `POST /api/chat/sessions` (`startChatSession`) → 201 with
the fixed greeting "Hi, I'm Meridian Home Comfort's automated assistant, not a person. …" (`policy/texts.py`, no model),
the demo clock "Fri Oct 16, 2026 (demo date)", `staffing.mode = "nobody_online"`, an empty `settled`,
`events.last_event_id = 0` and `limits` {`turn_deadline_ms` 60000, `still_working_after_ms` 10000,
`browser_give_up_after_ms` 65000, `max_message_chars` 2000}. Then `POST …/turns` (`submitTurn`) with `{"turn_id":
"<uuid>", "payload": {"kind": "text", "text": "I got an invoice … and I'm not sure what it's for."}}` → HTTP 200
`TurnResponse` with `blocks`, `settled`, `writes`, `controller`, `notice: null`. Sending the **same `turn_id`** again
returns the stored response and runs nothing (idempotent retry).

**Second pair (a code turn, graph-core §2).** `{"kind": "code", "card_id": "code-…", "code": "<6 digits>"}` → step 4 runs
`parse_intake` once, stores the message as "[code entered]" and gets its id (say 412); the graph receives
`TurnInput(kind="code", text_store="[code entered]", message_id=412, …)` while the digits travel only in
`TurnContext.intake` as a `SecretStr`, never in state, a prompt, a log or a trace.

**The behaviour.** The customer chat's two entry points (DO-3 §4.4, DO-4 §14, web.md §9, §14):

- **`web/routes/chat.py` + `web/schemas/chat.py`**: thin `def` routes (DO-3 §2.1) for `startChatSession` and
  `getChatThread` (CON-1) and `submitTurn` (CON-2). The OpenAPI file is the field authority (api-con-mapping §1); this
  ticket serves exactly its request and response shapes, named errors and cookie, every response checked in tests with
  `tests/api/openapi_check.py` `assert_response_matches` (web.md §13). Thread routes take the path id through
  `owned_thread` (web.md §4): malformed, unknown and another session's thread → the identical 404 `SESSION_NOT_FOUND`; an
  ended thread of this session → 410 `SESSION_ENDED` `{reason}` (WEB-34, MC-16). Errors are raised as `ApiProblem`
  (web.md §1). `submitTurn` reads `RequestContext.turn_verdict` and calls `TurnService.rate_limited` instead of
  `run_turn` when it is not allowed (WEB-12). `web/schemas/chat.py` validates into graph-core's `domain` `TurnPayload`
  (`domain/turn.py`, AEA-02; web.md §9, R-W-15, R-G-20) and defines no Python payload union. CON-4 and CON-5 are
  AEA-42's `routes/handoff.py`, not here.
- **`services/session.py` `SessionService`** (A8): `open` mints the `ThreadId`, owned by the signed-in login session, and in
  ONE write transaction writes the `conversations` row (`run_tag` / `run_id` from `RequestContext`, `agent_version`,
  outcome `open`, controller `ai`) and the greeting as an `assistant` message (the anchor cases.md §5 relies on, CAS-38);
  clock and staffing from the injected `DemoService` (AEA-30); `settled` through an injected `settled_view` callable
  (`ReplyComposer.settled_view`, graph-core §13) so the service never imports `agent/`. `thread` returns web.md §14's
  `ThreadHistory` (R-W-6): greeting, customer lines, turn replies, CON-4 rows, representative lines and event lines in
  time order, from stored rows, never a code (AEA-40-1, AEA-40-2). Signature: web.md §14 (R-W-2).
- **`services/turn.py` `TurnService.run_turn(RunTurn) -> TurnResponse`**, in DO-4 §14's order as web.md §9 completes it:
  (1) admission, at most **30 turns in flight** [Decided SDQ-9] → `BUSY` notice with the person key, no model; (2)
  `spend.allow_turn()` on the injected `SpendGuard` (models.md §6, MOD-18) → `SPEND_CAP_REACHED`; (3)
  `core.turns.begin(ids, received_at)`: `completed` → the stored response, `running` → 409 `TURN_IN_PROGRESS` with
  `details.retry_after_ms` 2000 [A] (api-con-mapping CON-2 row; OpenAPI example), `new` / `failed` → run; (4)
  `parse_intake` (AEA-12, STORE profile) once, `core.messages.append` → `message_id`, `conversations.last_customer_wall_at`
  (UTC wall clock, MC-20; cases.md A-7), and, when `conversations.controller == "human"`, the CON-21 `customer_message`
  event in the same transaction (staff.md §7, WEB-15); (5) inside `with trace.turn(ids) as span:` build `TurnInput` (the
  Intake's non-secret fields plus `message_id`) and `TurnContext(ids, budget, now=<one demo-clock reading>,
  demo_session, span=span, intake=intake)` exactly as graph-core §2 rules 1–2 say, with a `TurnBudget` of **60 s** from
  server receipt [Decided SDQ-1], and call the injected `run_graph: RunGraph` (returns `GraphOutcome`, graph-core §2;
  AEA-51 binds the compiled graph); (6) `outcome.halt.reason == DEADLINE` → `TURN_TIMEOUT` with *Try again* (same
  `turn_id`) and *Talk to a person*, plus whatever `settled` holds, and the trace becomes `degraded_handoff` / `timeout`;
  (7) persist the reply message, `core.turns.finish(turn_id, TurnRecord(status, trace=outcome.turn_trace, replied_at,
  server_ms, model_calls, input_tokens, output_tokens, cost_usd (this `turn_id`'s `spend_ledger` rows), tool_calls (its
  `lookup_log` rows), trace_id=span.trace_id, trace_export=trace.export_status(span) after the span closes, response))`,
  and one `core.check_events.append(event, thread_id)` per item of `outcome.check_events`; set `conversations.outcome`
  by web.md §9's table in this same transaction (R-W-5): `handed_off` replaces anything; `safety_reply` from `open`;
  `ai_resolved` from `open` when `turn_trace.outcome in (answered, acted)` and `GraphOutcome.closed_every_open_task`
  (graph-core §2, R-G-21); otherwise unchanged, while step 4 reopens `ai_resolved` / `abandoned` to `open` and never
  reopens `handed_off` or `safety_reply` (cases.md A-7); (8) return `outcome.reply` as `TurnResponse`. `TurnService` never
  reads `ConversationState` (web.md §9). There is no growing message list (context-management rule 1).
- **`TurnService.rate_limited(cmd, verdict)`** (web.md §9, WEB-12): HTTP 200, notice `RATE_LIMITED` (actions
  `["talk_to_person"]`, `retry_turn_id` null), `settled` from `core.settled_for(thread_id, read_at)`, no model, turn row
  `TurnRecord(status="failed", trace=TurnTrace(gate_result="clear", path="degraded", outcome="degraded_handoff",
  degrade_reason="rate_limit"), …)` so the same `turn_id` re-runs once the bucket refills; same notice builder as `BUSY`
  and `SPEND_CAP_REACHED`, text from `policy/texts.py`.
- **Start-up restart sweep** (DO-3 §2.3 rule 6; DO-6 *Missing instrumentation*; web.md §9, R-W-4): this ticket's own
  `register_<area>()` hunk in `web/container.py` calls `core.turns.fail_running()` (cases.md §1.2, R-G-22; an AEA-10
  follow-up merged first) once while the container is built, before the first request; it fails **every** `running` row
  (status `failed`, `path` `degraded`, `outcome` `degraded_handoff`, `degrade_reason` `timeout`) and logs one
  `turn_sweep` count line (ids and a count only). No age test: one process on one volume, and `received_at` is demo time
  (this supersedes DO-3 §2.3 rule 6's "older than 65 s"). `web/app.py` is AEA-23's and does not change.
- No database transaction is open across `run_graph` (DO-3 §2.3 rule 1).

### Source

- DO-4 §1 (`TurnInput`), §2 (`TurnBudget`, `TurnIds`, `TurnContext`), §3 (`Intake`, STORE texts), §9 (`ComposedReply`),
  §11 (`ApiErrorCode`; rows *Deadline*, *Admission limit*, *Our $30/day cap*, *Per-session or per-IP rate limit*, *A
  representative owns the chat*), §13 (`core.turns.begin/finish`, `TraceSink.turn`), §14 (`TurnService`, `RunTurn`), §16
  (addenda win).
- `docs/design/contracts/stage7/web.md` §1 (`ApiProblem`), §4 (`RequestContext`, `owned_thread`, providers
  `get_session_service`, `get_turn_service`, `get_wall_clock`), §5 (`LimitVerdict`; `submitTurn` never 429), §7 (503
  `RESET_IN_PROGRESS` from the middleware for `startChatSession` and `submitTurn`), §9 (CON-2 additions, `rate_limited`,
  the DO-6 `turn` field sources, the conversation-outcome table, the restart sweep, `TurnPayload`), §10 (`signal`
  record), §13 (`openapi_check`), §14 (`SessionService`, `ChatOpened`, `HistoryEntry`, `ThreadHistory`: the one
  signature, R-W-2).
- Residual rulings `docs/plans/7b-decisions/residuals-web.md` R-W-2, R-W-4, R-W-5, R-W-6, R-W-14, R-W-15 and
  `residuals-graph.md` R-G-20, R-G-21, R-G-22; UX-join amendments `docs/plans/ux-join/backend-amendments.md` §2 AEA-40-1,
  -2, -4, -5, -6, -7 (customer audit A-1, A-2, A-7; staff audit E1, A3).
- `docs/design/contracts/stage7/graph-core.md` §2 (`TurnInput`, `TurnContext.span` / `.intake`, `TurnTrace`, `TurnRecord`,
  `GraphOutcome`, `RunGraph`; rules 1–4), §6 (`core.settled_for`), §11 (what `GraphOutcome.check_events` holds), §13
  (`ReplyComposer.settled_view`).
- `docs/design/contracts/stage7/cases.md` §1.1 (`conversations`, `turns`, `check_events` columns), §1.2
  (`core.conversations.lookup`, `core.messages.append`, `core.check_events.append`, `core.turns.begin/finish`), §5
  (greeting anchor), closing rows A-7, A-15; `docs/design/contracts/stage7/models.md` §4 (`SpanHandle`,
  `export_status(turn)`, MOD-9, MOD-10), §6 (`SpendGuard`, MOD-18), cross-topic 5; `docs/design/contracts/stage7/staff.md`
  §1 (`CUSTOMER_SPEAKER_NAME`), §7 (`customer_message` payload), §12 (now a pointer to web.md §14);
  `docs/design/contracts/stage7/data.md` §1 (STORE profile), §2 (`render`, `TextId`, `TextId.PERSON_REQUEST_LABEL`).
- Decision ledgers: `docs/plans/7b-decisions/web.md` WEB-3, WEB-12, WEB-13, WEB-14, WEB-15, WEB-34, WEB-36, WEB-38;
  `docs/plans/7b-decisions/graph-core.md` GRC-10, GRC-20, GRC-21; `docs/plans/7b-decisions/models.md` MOD-9, MOD-10,
  MOD-11, MOD-18; `docs/plans/7b-decisions/staff.md` STF-28; `docs/plans/7b-decisions/merge-clashes.md` MC-16, MC-20.
- `docs/design/contracts/api-con-mapping.md` §0 (two kinds of failure, error body, timing constants), §1 rows CON-1, CON-2.
  `docs/ux/03-structure/ui-contracts.openapi.yaml` (read-only): `startChatSession`, `getChatThread`, `submitTurn`; schemas
  `StartSessionResponse`, `ChatThread`, `TurnRequest`, `TurnPayload` (`TextPayload` maxLength 2000, `CodePayload` pattern
  `^[0-9]{6}$`, `FormPayload`), `TurnResponse`, `Notice`; responses `ValidationError`, `Unauthenticated`,
  `SessionNotFound`, `SessionEnded`, `TurnInProgress`, `ResetInProgress`, `TooManyRequests`.
- DO-3 §2.1, §2.3 (rules 1, 5, 6), §4.4, §5.2, §7 rows R-1, R-3, R-41. DO-2 `system-design.md` §8.1, §8.2, §9, SDQ-1,
  SDQ-9. DO-6 `observability-contract.md` WF-1 row, *Records*, *Correlation*, *Missing instrumentation*, CAP-1, CAP-2,
  CAP-7; DO-7 M-18 end rule.
- PRD R-1, R-3, R-15, R-41, R-45, R-48; US-1, US-26. Slice plan §0a (Amendment 1, journeys J-1, J-9) and rule
  `.claude/rules/integrated-journeys.md` §3–§4.
- Slice plan row AEA-40; area-map row A8 (Customer API); ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "The interface must be interactive: a reviewer should be able to type questions, probe edge
  cases, and watch the agent escalate" and "failures should be observable, and failure handling must be clean"; touches
  nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] **WF-1** (CON-1 `startChatSession`): `startChatSession` returns 201 matching `StartSessionResponse`: the greeting equals `render` of the `policy/texts.py` greeting, `limits` equal `Limits` (60000, 10000, 65000, 2000), clock and staffing come from the `DemoService` double, the `run_graph` double is never called, and one transaction wrote the `conversations` row (outcome `open`, controller `ai`, the request's `run_tag`) and the greeting `assistant` message; `open` receives the `LoginSession` and `RequestContext.run_tag` / `run_id`, and the conversations row carries `agent_version` from the constructor (web.md §14, R-W-2) — verify: `tests/api/test_chat.py::test_start_session_fixed_greeting_no_model` with `assert_response_matches(response, "startChatSession")` — evidence: response validates; 0 `run_graph` calls; both rows present.
- [ ] AC-2 [failure/refusal] `getChatThread` returns card-like numbers as "[card number removed]" (the code, form and choice display texts are AC-19's, which replaces this criterion's former "codes shown as '[code entered]'" clause, AEA-40-4); a malformed id, an unknown thread and another login session's thread give the identical 404 `SESSION_NOT_FOUND`; this session's ended thread gives 410 `SESSION_ENDED` with `details.reason` — verify: `test_chat.py::test_get_thread_redacted`, `::test_thread_not_found_identical_for_malformed_unknown_and_foreign`, `::test_ended_thread_410` — evidence: bodies as stated; the three 404 bodies differ only in `request_id`.
- [ ] AC-3 [invariant] Idempotent `turn_id`: a completed turn resent returns the stored response byte-identical with `run_graph` called once in total; a resend while it runs returns 409 `TURN_IN_PROGRESS` with `details.retry_after_ms = 2000`; a failed or timed-out turn re-runs — verify: `tests/services/test_turn.py::test_same_turn_id_returns_stored`, `::test_running_turn_409`, `::test_failed_turn_reruns` — evidence: call counts and bodies as stated.
- [ ] AC-4 [failure/refusal] Admission: with 30 turns held in flight by a blocking `run_graph` double, a 31st turn returns HTTP 200 with notice `BUSY` and the `talk_to_person` action, no `run_graph` call, and a `turn` row with trace `degraded_handoff` / `rate_limit` (DO-4 §11) — verify: `test_turn.py::test_admission_31st_turn_busy` — evidence: notice and row as stated.
- [ ] AC-5 [failure/refusal] Spend cap: when the `SpendGuard` double's `allow_turn()` is false, the turn returns notice `SPEND_CAP_REACHED` with the person key, no `run_graph` call, and a `turn` row `degraded_handoff` / `spend_cap` — verify: `test_turn.py::test_spend_cap_notice_no_model` — evidence: as stated.
- [ ] AC-6 [failure/refusal] Rate limit (WEB-12): with `RequestContext.turn_verdict.allowed = False` (provider overridden), `submitTurn` returns HTTP 200 with notice `RATE_LIMITED`, actions `["talk_to_person"]`, `retry_turn_id` null, no `run_graph` call, and a `turn` row `failed` with trace (`clear`, `degraded`, `degraded_handoff`, `rate_limit`); the same `turn_id` sent again with an allowed verdict runs the graph — verify: `test_chat.py::test_rate_limited_notice_then_same_turn_runs` — evidence: body validates against `submitTurn`; row and second-call count as stated.
- [ ] AC-7 [failure/refusal] **WF-1** (CON-2 `submitTurn`; composed outcomes are HTTP 200 with `settled`): Deadline: a `run_graph` double returning a `GraphOutcome` with `halt.reason = DEADLINE` (budget built as 60 s from receipt on a stubbed monotonic clock) gives notice `TURN_TIMEOUT` with actions `try_again` and `talk_to_person`, `retry_turn_id` equal to the same `turn_id`, `settled` still showing a write committed earlier in the turn, and a `turn` row `degraded_handoff` / `timeout`; a `run_graph` that raises gives HTTP 200 with a person offer and a `degraded_handoff` row, never a 500 (PRD §5 *Reliability*) — verify: `test_turn.py::test_deadline_turn_timeout_notice`, `::test_graph_exception_degraded_not_500`, and the same two doubles driven through `submitTurn` (TestClient) in `tests/api/test_chat.py::test_timeout_and_exception_notices_via_submit_turn` with `assert_response_matches(response, "submitTurn")` — evidence: bodies and rows as stated; both route bodies are HTTP 200, carry `settled` and validate.
- [ ] AC-8 [negative] Intake redaction and the intake carrier (graph-core §2 rules 1–4): a code turn stores "[code entered]", a text with a synthetic card-like number stores "[card number removed]", a locate form stores "[details submitted]"; the recorded `TurnInput` holds `message_id` and no code digits or form values, while `TurnContext.intake` holds them as `SecretStr`; the code digits, the card number and the form's phone appear in no `messages`, `turns`, `conversations` or `check_events` text and in no captured log record — verify: `test_turn.py::test_intake_redacted_and_never_in_turn_input` — evidence: values built in the test from parts are absent from a dump of the temp working copy, the recorded `TurnInput` and the log capture.
- [ ] AC-9 [negative] **WF-1** (CON-2 `submitTurn`): Validation errors name the field and rule, never the value: a code payload "12ab56" and a 2,001-char text return 400 `VALIDATION_ERROR` with `field` and `constraint` and without the submitted value anywhere in the body — verify: `test_chat.py::test_validation_error_hides_value` — evidence: bodies validate against `ValidationError`; the value absent.
- [ ] AC-10 [invariant] One turn context per turn and no growing context: `TurnContext` carries one demo-clock reading, the span from `trace.turn(ids)` and a 60 s budget; the graph input for turns 1, 2 and 5 holds the same key set and no message-list key; `TurnService` reads only `GraphOutcome`, never `ConversationState` — verify: `test_turn.py::test_turn_context_and_inputs_turns_1_2_5` — evidence: recorded inputs and contexts as stated; a grep of `services/turn.py` for `ConversationState` finds nothing.
- [ ] AC-11 [invariant] **WF-1** (CON-2 `submitTurn`): Customer message side effects (WEB-15, cases.md A-7): every customer message writes `conversations.last_customer_wall_at` in UTC; when `controller == "human"`, the CON-21 `customer_message` event (staff.md §7 payload, stream `case:<ref>`) is in the same commit as the message row, and the `customer_message` payload's `speaker.display_name` is `CUSTOMER_SPEAKER_NAME` (staff.md §1, §7, R-W-14) — verify: `test_turn.py::test_customer_message_event_same_commit_when_human`, and `tests/api/test_chat.py::test_customer_message_event_via_submit_turn` (a `submitTurn` on a thread whose `controller` is `human`) — evidence: the route call leaves the message row and one `customer_message` event row; a fault injected after the event write rolls back both rows; the timestamp ends `+00:00`.
- [ ] AC-12 [invariant] Restart sweep (web.md §9, R-W-4): at container start, every `turns` row still `running` (one received 66 s and one 10 s earlier on the demo clock) becomes `failed` with `degraded_handoff` / `timeout`; a `completed` row is untouched; resending a swept `turn_id` runs the graph — verify: `test_turn.py::test_restart_sweep_fails_every_running_turn` — evidence: rows and the rerun as stated.
- [ ] AC-13 [invariant] No transaction is open while `run_graph` runs (DO-3 §2.3 rule 1) — verify: `test_turn.py::test_no_uow_open_during_run_graph` (a UoW double that fails if entered during the `run_graph` call) — evidence: passes.
- [ ] AC-14 [capture] **WF-1** (CON-1 `startChatSession` → CON-2 `submitTurn`; OBS-32 receipt row): Driving the real entry points (TestClient → CON-1 → CON-2, `run_graph` double returning a `GraphOutcome` whose `turn_trace` has a gate result, planner decision and specialists run, plus two check events) writes a `conversations` row (`run_tag`, `agent_version`), a `turn` row on receipt with `outcome` empty, then finished with `request_id`, sequence, received and replied times, `server_ms`, every `TurnTrace` field, model-call and token counts and cost summed from seeded `spend_ledger` rows of this `turn_id`, `tool_calls` from its `lookup_log` rows, `trace_id` and `trace_export` (`off` with `NullTraceSink`), and two `check_events` rows; a handed-off turn sets `conversations.outcome = 'handed_off'`; a run with the eval key is tagged `eval`, one without it `live` (CAP-7) — verify: `tests/api/test_chat_capture.py::test_con1_con2_records_written` — evidence: rows read back with every DO-6 field populated. (Full CAP-1/CAP-2 with the real graph: AEA-51.)
- [ ] AC-15 [journey] (replaced by AEA-40-7) Extends J-1 and J-9 (slice plan §0a journey map): J-1, login → `startChatSession` → one turn → reload resumes the same thread through `getChatThread`, whose `turns` start with the greeting and hold the customer turn and its reply in order (AC-16, AEA-40-1), with no second `startChatSession`; J-9, the `TURN_TIMEOUT`, `BUSY` and `RATE_LIMITED` notices reached through the real server; asserting what the user sees and the stored `conversations`, `messages` and `turns` rows, in `tests/journeys/j1/test_aea_40.py` and `tests/journeys/j9/test_aea_40.py` with the scripted model adapter — verify: `uv run pytest -m journey tests/journeys/j1/test_aea_40.py tests/journeys/j9/test_aea_40.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57's harness (J-1) and AEA-51 (the turn steps and J-9) land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-40.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-16 [invariant] `getChatThread` returns the whole conversation in time order (web.md §14 entries 1–6, R-W-6; AEA-40-1, customer audit A-1): the greeting as an assistant turn with `blocks: [TextBlock]` and turn_id `greeting`; each customer message (`speaker.kind: customer`, `text` as stored, except the code, form and choice texts of AC-19); each completed turn's stored blocks; each representative message (`speaker: {kind: representative, display_name: "Riley"}`, `text`); each stored chat-event line of the thread's stream (`speaker: {kind: event, display_name: null}`, `text` = its `line`); a `shift_ended` handoff as an assistant turn with `blocks: [HandoffBlock]`. Entries that are not turns get web.md §14's stable ids, unique in the thread (`msg-<message_id>`, `evt-<event_id>`), and `last_event_id` is the newest event id read in the same unit of work, so a stream opened from it replays nothing already in `turns`; a failed or running turn contributes only its customer message — verify: `tests/services/test_session.py::test_thread_holds_full_history` (temp SQLite: greeting, one turn, a representative join, a staff message, hand back, a shift end) and `tests/api/test_chat.py::test_get_thread_full_history` with `assert_response_matches(response, "getChatThread")` — evidence: the entries in the stated order with the stated speakers; the body validates; ids unique.
- [ ] AC-17 [invariant] A CON-4 person request appears in the history (web.md §14 entry 4, R-W-6; AEA-40-2, customer audit A-2): a `turns` row whose trace `gate_result` is `person_requested` (AEA-42's stored outcome, web.md §8, AEA-42-1) becomes a customer turn with `text` = `render(TextId.PERSON_REQUEST_LABEL)` ("Talk to a person", data.md §2, AEA-03) followed by an assistant turn with `blocks: [<stored block>]` (`HandoffBlock` or `LiveQueuedBlock`), both carrying the CON-4 turn_id — verify: `tests/services/test_session.py::test_thread_shows_person_request_card` (the CON-4 row seeded in web.md §8's stored shape) — evidence: the two entries in order; the card's reference equals the case's.
- [ ] AC-18 [invariant] Reload after a live takeover (R-W-6): a thread with the greeting, one CON-2 turn, a CON-4 request, Riley's join / message / hand back and a staffing change returns, in order, greeting, customer line, reply blocks, "Talk to a person", the handoff block, "Riley (demo representative) has joined.", the pause line, Riley's text (speaker representative "Riley"), the resume line and the staffing line; `last_event_id` equals the newest event id; the body validates against `getChatThread` — verify: `tests/api/test_chat.py::test_thread_history_includes_greeting_staff_and_event_lines` — evidence: entries in that order; `last_event_id` as stated; the body validates.
- [ ] AC-19 [invariant] History rows read like the live rows (AEA-40-4, customer audit A-7; replaces AC-2's former "codes shown as '[code entered]'" clause): in `getChatThread` a code turn's `text` is "Code entered", a form turn's "Details sent", a choice turn's the option's label from the card it answered (the stored option string when that card is not in the thread), never "[code entered]", "[details submitted]" or null; the texts come from `policy/texts.py`, and the stored `messages` rows stay redacted as AC-8 requires — verify: `tests/api/test_chat.py::test_history_display_texts` — evidence: three rows with the three texts; the `messages` rows still hold "[code entered]" and "[details submitted]".
- [ ] AC-20 [invariant] The relayed customer message is a valid case event that names nobody (AEA-40-5, staff audit E1, A3; AC-11 proves the append and its single commit): the `customer_message` payload AC-11 writes validates against the OpenAPI `CaseEvent` member for that type (through `assert_sse_frames_match` on a frame built from it), carries the STORE-redacted text and the message's `message_id` and `at`, and its customer speaker is `{kind: "customer", display_name: CUSTOMER_SPEAKER_NAME}` ("Customer", staff.md §1, §7, R-W-14), never "You", a name or a contact value — verify: `tests/services/test_turn.py::test_customer_message_payload_valid_and_unnamed` — evidence: the frame validates; `display_name` equals `CUSTOMER_SPEAKER_NAME`; a synthetic card number built in the test from parts is stored and relayed as "[card number removed]".
- [ ] AC-21 [invariant] **WF-1** (CON-2 `submitTurn`): Conversation outcome (web.md §9 table, R-W-5): a scripted `answered` turn with `closed_every_open_task` → `ai_resolved`; the next customer message reopens it to `open`; a `handed_off` turn sets `handed_off` and a later `answered` turn leaves it; a `degraded_handoff` turn leaves `open` — verify: `tests/services/test_turn.py::test_conversation_outcome_rules`, and the same sequence sent through `submitTurn` (TestClient, scripted `run_graph` double) in `tests/api/test_chat_capture.py::test_conversation_outcome_via_submit_turn` — evidence: the stored `conversations.outcome` after each step as stated.
- [ ] AC-22 [contract] `tests/contract/cases/chat.py` holds the server cases for `startChatSession`, `getChatThread` and `submitTurn` (AEA-40-6): preconditions (login, a started thread), every named request example, and each documented error status the route can produce (401, 404 `SESSION_NOT_FOUND`, 410 `SESSION_ENDED`, 409 `TURN_IN_PROGRESS`, 400, 503) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "startChatSession or getChatThread or submitTurn" -rs` once AEA-59's runner is merged — evidence: one pass per case; a skip only as `not bound: <name>` naming a provider of a later issue (`run_graph`, AEA-51).
- [ ] AC-23 [regression/context] Context-management rule 3 does not apply here: this ticket renders no model prompt. In the same change: the area-map row A8 for sessions and turns (planned → actual + commit), the ICM progress row *Routes verified against code and tests*, DO-3 §3's rows for `services/{turn,session}.py` and `web/routes/chat.py` / `web/schemas/chat.py` marked built — verify: `git diff --name-only` — evidence: those docs in the diff, only this ticket's rows changed.

### Observability

- Responsibilities: WF-1 entry point (CON-1 `startChatSession`, `getChatThread`; CON-2 `submitTurn`). This ticket writes
  the `conversation` record (`thread_id` minted at CON-1, `run_tag`, `run_id`, `agent_version`, outcome) and the `turn`
  record (begun on receipt; finished with every DO-6 field from `TurnRecord`, incl. `trace_id` and `trace_export`,
  web.md §9's source table), persists the `check_event` rows from `GraphOutcome.check_events`, and carries the
  correlation IDs: `request_id` from AEA-23's middleware, `thread_id`, `turn_id`, and `run_id` only with the eval key. The
  `request` record is AEA-23's middleware. One trace per turn: `trace.turn(ids)` around `run_graph`, its handle on
  `TurnContext.span` (models.md §4, MOD-10). Signals `turn_timeout`, `turn_rejected_busy`, `spend_cap_reached`,
  `rate_limited` (DO-4 §11) are recorded as the turn's `degrade_reason`. Silence check: every turn still `running` at
  start-up is swept to `failed` / `degraded_handoff` / `timeout`, with one `turn_sweep` count line (AC-12, web.md §9,
  R-W-4). `conversations.outcome` follows web.md §9's table (AC-21, R-W-5).
- Capture evidence: AC-14 drives the real CON-1/CON-2 entry points and finds the records; AC-8, AC-9 and AC-20 assert the
  forbidden values are absent. CAP-1 and CAP-2 with the real graph are AEA-51's.

### Evaluation

- Checks: none added; E-1…E-5 and E-7 reach the agent only through CON-1 and CON-2 (the harness is HTTP only, AEA-24), so
  these routes must keep the eval-key tagging (CAP-7: a run without the eval key is tagged `live`) and the idempotent retry
  the harness relies on.
- Expected-answer authority: DO-5 *Expected-answer authority* (unchanged by this ticket).

### Metrics

- References: WF-1 inherits M-1, M-3, M-4, M-6, M-7, M-8, M-9, M-14, M-16, M-17, M-18, M-19, M-20, M-21, M-22, M-23, M-24,
  M-25, M-26, M-29. **Affected here (this ticket writes the rows they read):** M-22 (volume: conversations and turns per
  day by tag), M-23 (`turn.server_ms` p50/p95), M-24 (turns ending `degraded_handoff` by reason), M-25 and M-26 (spend
  gate before the graph; cost summed per turn), M-29 (`turn.trace_export`), M-3 and M-18 (`conversations.outcome`, and
  `last_customer_wall_at` for the abandonment sweep), M-14, M-16, M-17, M-19, M-20 (`turn.gate_result` and `outcome` copied
  from `TurnTrace`), M-21 and M-8 (the persisted `check_event` rows). **Kept computable, not changed by this ticket:** M-1,
  M-4, M-6, M-7, M-9 (eval-side or retrieval and write records written by other tickets; this ticket keeps live, eval and
  load separable by tag).
- Acceptance conditions: every metric above stays computable from the `conversation`, `turn` and `check_event` rows this
  ticket writes (AC-14); live, eval and load traffic stay separable by tag. No target set or changed.

### Blocked by

AEA-03, AEA-10, AEA-11, AEA-12, AEA-23 (slice plan). Within them: `TextId.PERSON_REQUEST_LABEL` (AEA-03, data.md §2,
R-W-6) and `core.turns.fail_running()` (the AEA-10 follow-up, cases.md §1.2, R-G-22); if either is not on `main` when
the plan is written, the plan records `blocked-on AEA-03` / `blocked-on AEA-10` for that piece (web.md cross-topic row
"data (DAT), AEA-03"; web.md §9 "AEA-10 follow-up merged first"). Types from AEA-02 (wave 0): `TurnPayload` (R-G-20), `GraphOutcome.closed_every_open_task`
(R-G-21), `CUSTOMER_SPEAKER_NAME` (staff.md §1). Calls (injected): `run_graph: RunGraph` (bound by AEA-51),
`SpendGuard` (AEA-26), `DemoService` and the demo `Clock` (AEA-30), `ReplyComposer.settled_view` (AEA-21), each tested
with a double honouring graph-core §2, §13, models.md §6 and cases.md §6. Same-wave rows read by `thread()` (AC-16–AC-18)
are seeded in tests in their contract shapes: the CON-4 stored outcome (AEA-42, web.md §8), representative messages and
chat-event rows (AEA-46, staff.md §5, §7). Record-level only, not merge blockers: AC-15's journey level waits on AEA-57
(wave 2) and AEA-51 (wave 3); AC-22 runs once AEA-59's runner (wave 2) merges.

### Agent handoff

- Area / owner: A8 Customer API (`web/routes/chat.py`, `web/schemas/chat.py`, `services/session.py`, `services/turn.py`,
  and this area's `register_<area>()` hunk in `web/container.py`), plus `tests/contract/cases/chat.py` (AC-22; AEA-59
  owns the runner) and `tests/journeys/j1/test_aea_40.py`, `tests/journeys/j9/test_aea_40.py` (AC-15; `support/` is
  AEA-57's).
- Contracts and shared surfaces: consumes `web/deps.py` providers (`get_request_context`, `get_login_session`,
  `owned_thread`, `get_uow_factory`, `get_wall_clock`), `ApiProblem` and `openapi_check` (AEA-23), `repos_core` incl.
  `core.settled_for`, `core.turns.begin/finish`, `core.turns.fail_running` (R-G-22), `core.messages.append`,
  `core.check_events.append`, `core.conversations.lookup` (AEA-10), `parse_intake` (AEA-12), `privacy/redact.py`
  (AEA-04), texts incl. `TextId.PERSON_REQUEST_LABEL` (AEA-03), `Limits` (AEA-01), `TurnInput`, `TurnContext`,
  `TurnRecord`, `TurnTrace`, `GraphOutcome` (with `closed_every_open_task`), `TurnPayload` and `CUSTOMER_SPEAKER_NAME`
  (AEA-02), and, injected with doubles,
  `run_graph`, `SpendGuard`, `DemoService`, `TraceSink`, `settled_view`. Produces `TurnService` and `SessionService` (via
  `get_turn_service`, `get_session_service`) for AEA-51 (wires the real graph) and AEA-24's harness (HTTP), and the
  `conversation`, `turn` and `check_event` rows AEA-32 and AEA-53 read. Must not edit `web/app.py`, `web/middleware.py`,
  `web/deps.py`, `routes/handoff.py`, `routes/events.py`, `domain/*`, `repos_*.py`, another hunk of `container.py`.
- Scope boundary / refusal: no graph or node logic, no reply wording, no CON-3…CON-9 routes, no rate-limit counting or 503
  reset answers (AEA-23's middleware), no CON-4 turn row (AEA-42).
- Settled (formerly needs-decision 1–3; `docs/plans/7b-decisions/residuals-web.md`): one `SessionService` signature,
  web.md §14 (R-W-2, AC-1); the restart sweep calls `core.turns.fail_running()` and fails every running row (R-W-4,
  R-G-22, AC-12); `conversations.outcome` follows web.md §9's table using `GraphOutcome.closed_every_open_task` (R-W-5,
  R-G-21, AC-21).
- UX-join items left for the orchestrator (not applied; `docs/plans/ux-join/backend-amendments.md` §2):
  - **AEA-40-3** (card `answered` survives a reload) is not in this ticket: it contradicts web.md §14 (R-W-6), which says
    `thread()` does not rebuild `answered` (the stored choice keeps no `card_id`) and the UX session treats every history
    card as spent; `decisions-for-innocent.md` lists the opposite owner (AEA-40). Until one ruling wins, build web.md §14.
  - **AEA-40-5**'s `display_name: null` was replaced by `CUSTOMER_SPEAKER_NAME` ("Customer") in AC-20, because staff.md
    §1 and §7 (R-W-14) fix that value; the join's "null" choice (README ST A3, `decisions-for-innocent.md`) disagrees.
  - **AEA-40-4** (AC-19) asks that the three texts ("Code entered", "Details sent", the option label) be agreed with the
    UX session first; data.md §2 has no `TextId` for the first two yet, so their `policy/texts.py` entries are an AEA-03
    follow-up and the plan records `blocked-on AEA-03` for them until it lands.
- Wave and gates: wave 2; no gate.
- Lane: build-loop — it changes source and tests (`ticket-lanes.md`).
- Risk: security (`risk::security`, slice plan; WEB-36): it receives the verification-code payload, redacts PII before
  storage, enforces thread ownership and admits untrusted input; a bug could leak a code or another session's chat.
  Frozen failing tests first (AC-2, AC-8, AC-9 at least); `security-privacy-agent` reviews the diff at the wave merge.
- Entry points added or changed: WF-1 (CON-1 `startChatSession`, `getChatThread`; CON-2 `submitTurn`).
