# Plan — [AEA-40] customer API: sessions and turns (CON-1, CON-2)

**Status:** planned — **READY** (both parts). Refreshed again 2026-10-21 against `main` at **`2ec19ad`**. The only
commit since the previous base `b559c75` is `2ec19ad` (docs: `docs/plans/fanout/2026-10-21-build/AEA-29.md`), so every
signature, import and line number below still holds. Part B's two old blockers are on `main`: AEA-02b
(`meridian.domain.views.ClockView` / `StaffingView`, merge `5305d57`) and AEA-03b (`TextId.HISTORY_CODE_ENTERED` /
`HISTORY_DETAILS_SENT`, merge `19e046b`). AEA-30 and AEA-51 are still **not** on `main` (ledger rows `ready`).
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #40 (= `docs/plans/tickets/AEA-40.md`) · **Base revision:**
`2ec19ad` (main).
**Branch already in flight (continue it, do not restart):** `aea-40-aea-40-sessions-turns` at **`6891c3c`**, worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-40`. It holds the frozen tests (`61d5bd8`, test-writer), Part A
code (`d7fb642`), Part A docs (`f8d3355`) and **Step 0's merge of `b559c75` (`6891c3c`, done)**. Its merge base with
`main` is `b559c75`.
**Uncommitted work in that worktree at refresh time (an implementer run in progress; keep it, never discard it):**
- `src/meridian/services/session.py` (new, 344 lines): a Part B draft with §4.6's names (`GREETING_TURN_ID`,
  `GREETING_BLOCK_ID`, `EVENT_LINE_TYPES`, `DemoReads`, `greeting_block`, `ChatLimits`, `ChatOpened`, `HistoryEntry`,
  `ThreadHistory`, `_option_labels`, `_customer_text`, `SessionService.open` / `.thread`). Treat it as Steps B1–B3 in
  progress: check it line by line against B1–B3 below and finish it; do not rewrite it from scratch.
- `.claude/reference/area-map.md`: removes a stray "AEA-40 Part A (d7fb642): …" clause that Step 0.3 put in the **A9
  Staff console** row by mistake. That fix is correct; keep it. The A8 row keeps its Part A clause until Step D.
**Step T has not run:** `tests/services/chat_storage.py` does not exist, `chat_doubles.py` is still 1,002 lines and the
two journey files still carry the old `@pytest.mark.skip` stubs naming AEA-57.
**Lane / risk:** `lane::build-loop` · **`risk::security`**. The frozen tests (§3.1) are the test-writer's. The
implementer never edits them. The `security-privacy-agent` reads this diff at the wave merge.
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21. Second refresh of the plan at this path: the header,
§0 facts 1–2, Step 0 (now done) and §9 changed; everything else is unchanged from the `b559c75` refresh.
**Implementer:** `fanout-implementer` on Sonnet, in the worktree above. All paths are repo-relative.
**Merging:** the implementer commits on the branch only. It never merges into `main`, never pushes and never
force-pushes. The orchestrator's merge step merges branches in dependency-tree order: AEA-40 is a parent of AEA-51,
AEA-52, AEA-58 and AEA-62.

## 0. Read this first (seven facts that shape every step)

1. **Part A is built. Part B is in progress.** On the branch, `services/turn.py`, `submitTurn`, `TurnRequest` and
   the `register_chat` hunk are committed, and the Part A tests passed at `d7fb642`. `services/session.py` exists only
   as an uncommitted draft (header); `startChatSession`, `getChatThread`, their wire models and the Step H hunk changes
   do not exist yet.
2. **Step 0 (take `main`) is done** at `6891c3c` (merge of `b559c75`). `main` has moved one docs-only commit since
   (`2ec19ad`, AEA-29's plan file). Do **not** merge it again: it touches no file this ticket reads or owns, and the
   orchestrator's merge step brings it in. Step 0 below now only verifies.
3. **Services never import `web/` or `agent/`** (DO-3 §2.1). So:
   - `LimitVerdict` (web) is read through the `TurnVerdict` Protocol;
   - `ReplyComposer.settled_view` (agent) arrives as an injected callable;
   - `DemoService` (AEA-30, not merged) arrives as the `DemoReads` Protocol.

   A service may import another service's types (DO-3 has no ban). This plan uses `PersonRequestOutcome` from
   `services/person_request.py` (AEA-42) to read stored CON-4 rows.
4. **Siblings are injected and doubled.** Four container keys are still unprovided on `main`:
   - `Key("demo_clock")` and `deps.DEMO_SERVICE`, bound by AEA-30;
   - `deps.REPLY_COMPOSER` and `Key("run_graph")`, bound by AEA-51.

   `register_chat` resolves each one lazily, at call time, so the app builds before they exist. A call made before then
   raises `RuntimeError("not bound: <key>")`. AEA-59's contract runner and AEA-57's journey steps report exactly that
   message as "blocked/skipped".
5. **The demo clock does not move between advances** (`DemoClock.now()` = `demo_state.demo_now`, cases.md §6). In a
   real demo, almost every stored `at` in a thread is the same instant. Step B3's merge rule handles that (§8 R-1).
6. **No literal code, card number or full phone number** appears in any file, tests included. Tests build them at run
   time from a seeded `random.Random`. The frozen helpers already do this (`synthetic()`).
7. **The frozen journey files predate AEA-57's harness.** Their `@pytest.mark.skip` stubs still name AEA-57 as a
   blocker, but AEA-57 has merged. Step T (a small test-writer amendment, dispatched before the implementer) replaces
   them with harness steps that report the real blockers (AEA-30, AEA-51). Step T also splits the 1,002-line
   `tests/services/chat_doubles.py` under the 500-line test cap.

---

## 1. Goal and sources

### 1.1 Goal (quoted from the issue, *What to build*)

> The customer chat's two entry points (DO-3 §4.4, DO-4 §14, web.md §9, §14):
> - **`web/routes/chat.py` + `web/schemas/chat.py`**: thin `def` routes (DO-3 §2.1) for `startChatSession` and
>   `getChatThread` (CON-1) and `submitTurn` (CON-2) … every response checked in tests with `tests/api/openapi_check.py`
>   `assert_response_matches` … Thread routes take the path id through `owned_thread` … `submitTurn` reads
>   `RequestContext.turn_verdict` and calls `TurnService.rate_limited` instead of `run_turn` when it is not allowed …
> - **`services/session.py` `SessionService`** (A8): `open` mints the `ThreadId` … in ONE write transaction writes the
>   `conversations` row … and the greeting as an `assistant` message … `thread` returns web.md §14's `ThreadHistory` …
> - **`services/turn.py` `TurnService.run_turn(RunTurn) -> TurnResponse`**, in DO-4 §14's order as web.md §9 completes
>   it: (1) admission … (2) `spend.allow_turn()` … (3) `core.turns.begin` … (4) `parse_intake` … (5) inside
>   `with trace.turn(ids) as span:` … call the injected `run_graph` … (6) `DEADLINE` → `TURN_TIMEOUT` … (7) persist …
>   (8) return `outcome.reply` as `TurnResponse`. `TurnService` never reads `ConversationState`.
> - **`TurnService.rate_limited(cmd, verdict)`** (web.md §9, WEB-12) …
> - **Start-up restart sweep** … this ticket's own `register_<area>()` hunk in `web/container.py` calls
>   `core.turns.fail_running()` once while the container is built … logs one `turn_sweep` count line …
> - No database transaction is open across `run_graph` (DO-3 §2.3 rule 1).

**What it does in practice:**

- **Opening the chat.** A reviewer signs in and opens the chat. `POST /api/chat/sessions` writes a conversation row and
  the fixed greeting ("Hi, I'm Meridian Home Comfort's automated assistant, not a person. …") in one transaction. It
  answers 201 with the demo clock, staffing, an empty *What's settled* panel and the CON-1 limits. No model runs.
- **Each message** goes to `POST …/turns`. The service:
  1. checks capacity (30 turns in flight) and the $30/day spend gate;
  2. records the turn as `running`;
  3. strips codes, card numbers and form values out of what it stores;
  4. runs the graph outside any database transaction, with a 60 s budget;
  5. stores the reply, the turn record (timings, tokens, cost, trace id) and the check events, and returns the reply.

  Sending the same `turn_id` again returns the stored reply and runs nothing.
- **A reload** calls `GET /api/chat/sessions/{id}` and gets the whole conversation back in order: the greeting,
  customer lines, replies, "Talk to a person" requests, Riley's lines and the event lines.

**Example pair (the ticket's).**

- *First call.* `POST /api/chat/sessions` → 201 `StartSessionResponse`: greeting, clock "Fri Oct 16, 2026 (demo date)",
  `staffing.mode = "nobody_online"`, empty `settled`, `events.last_event_id = 0`, and `limits`
  60000/10000/65000/2000.
- *A turn.* `POST …/turns` with `{"turn_id": "<uuid4>", "payload": {"kind": "text", "text": "I got an invoice … and I'm
  not sure what it's for."}}` → 200 `TurnResponse` (`blocks`, `settled`, `writes`, `controller`, `notice: null`).
- *A retry.* The same body again → the stored response, byte-identical, with `run_graph` called once in total.
- *Second pair (a code turn).* A code payload → the `messages` row holds `"[code entered]"`. The graph gets
  `TurnInput(kind="code", text_store="[code entered]", message_id=<row id>)`. The digits travel only in
  `TurnContext.intake.code_digits`, a `SecretStr`.

### 1.2 Context

Stage 8, wave 2, area A8 (DO-3 §8). The build ledger (`.claude/state/build-ledger.md` row AEA-40) says `ready`, with
blockers AEA-03, 10, 11, 12, 23, 02b, 03b, all merged. On `main` now:

- **Merged since the first plan:** AEA-21 (graph spine and `ReplyComposer` class, not bound), AEA-41, AEA-42, AEA-44,
  AEA-46, AEA-47, AEA-48, AEA-49, AEA-31, AEA-32, AEA-57 (journey harness), AEA-59 (contract runner), AEA-02b, AEA-03b,
  AEA-27, AEA-28.
- **Not on `main`:** AEA-30 (`demo_clock`, `demo_service`) and AEA-51 (`reply_composer`, `run_graph`).

The AEA-51 plan already reads this ticket's lazy keys (its plan line 375: `register_chat` reads `Key("run_graph")`,
`Key("reply_composer")`, `Key("trace")` and `Key("ledger")`).

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-40.md` (AC-1…AC-23) | The criteria, test names and evidence in §3 |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-40, §3 collision map | Owned files; one `register_chat` hunk; one route file and one schema file; journey files `j1/`, `j9/` |
| Requirements | PRD R-1, R-3, R-15, R-41, R-45, R-48; US-1, US-26 | Greeting says "automated, not a person" (R-1, fixed text, no model); clean degraded answers, never a 500 (US-26) |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §1, §2, §3, §9, §11, §13, §14, §16 | `RunTurn`, the `TurnService` order, `TraceSink`, `UnitOfWork`, the error-to-customer table; §16: the addenda win |
| Web addendum | `stage7/web.md` §1, §4, §5, §7, §8, §9, §10, §13, §14 | `ApiProblem`, `owned_thread`, `turn_verdict`, `rate_limited`, the outcome table, the sweep, `TurnPayload`, `SessionService` (the one signature), history entries 1–6 |
| Graph addendum | `stage7/graph-core.md` §2 (rules 1–4), §6, §11, §13 | `TurnInput` / `TurnContext` / `GraphOutcome` / `TurnRecord` / `RunGraph`; DEADLINE; `settled_for`; `settled_view` |
| Cases addendum | `stage7/cases.md` §1.1, §1.2, §5, §6, A-7, A-15 | Columns; repository methods; greeting anchor (CAS-38); `DemoService.staffing()` / `clock_view()` |
| Models addendum | `stage7/models.md` §4, §6 | `SpanHandle`, `export_status(turn)` after the span closes; `SpendGuard.allow_turn` |
| Staff addendum | `stage7/staff.md` §1, §5, §7, §12 | `CUSTOMER_SPEAKER_NAME`; the `customer_message` payload on `case:<ref>`; takeover event shapes (written by AEA-46, merged) |
| Data addendum | `stage7/data.md` §1, §2 (AEA-03b note line 11, line 116) | STORE profile; `render`, `TextId.PERSON_REQUEST_LABEL`, `HISTORY_CODE_ENTERED`, `HISTORY_DETAILS_SENT` |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` | `startChatSession` (201, 401, 429, 503), `getChatThread` (200, 401, 404, 410), `submitTurn` (200, 400, 401, 404, 409, 410, 503; request examples `TEXT`, `CHOICE_SLOT`, `CODE`, `FORM_LOCATE`, `FORM_WHERE`); schemas `StartSessionResponse`, `ChatThread`, `TurnRequest`, `TurnResponse`, `Notice`, `Limits`, `CeCustomerMessage` |
| Residual rulings | `docs/plans/7b-decisions/residuals-web.md` R-W-2, 4, 5, 6, 14, 15; `residuals-graph.md` R-G-20…22 | Settled: one `SessionService`; the sweep fails every running row; the outcome table; history rules |
| UX join | `docs/plans/ux-join/backend-amendments.md` §2 AEA-40-1…7 | AC-16…AC-22; AEA-40-3 excluded (ticket *Agent handoff*) |
| Sign-off | `docs/plans/stage7-signoff.md` D-8 | Signing in again starts a fresh chat: `owned_thread`'s 404 for an earlier session's thread stands |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | No check added. CON-1/CON-2 keep eval-key tagging and the idempotent retry the harness (AEA-24) relies on |
| Observability contract | DO-6 `docs/design/observability-contract.md` WF-1 row, *Records*, *Correlation*, *Missing instrumentation*; CAP-1, CAP-2, CAP-7 | `conversation`, `turn` and `check_event` records; one trace per turn; the start-up sweep; eval/live tag |
| Key-metrics registry | DO-7 M-3, M-8, M-14, M-16…M-26, M-29 | The rows they read must be written (AC-14); no target set |
| Rules | `build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`, `code-design-solid-modularity`, `code-structure.md` (500-line test cap), `context-management-multi-turn` rule 1, `safe-validation-errors.md` | Frozen tests; affected tests and journeys; context rows; no growing message list; errors never carry the value |

### 1.4 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| `TurnResponse` needs a Python type; DO-4 and web.md name it, but nobody defines it | DO-4 §14; OpenAPI `TurnResponse` | implied | **added**: `services/turn.py` defines it field for field (built) | Part A (built) |
| `RunTurn` has no home on `main` | DO-4 §14 | AC-1…AC-21 | **added**: `services/turn.py`, verbatim (built) | Part A (built) |
| `rate_limited(cmd, verdict: LimitVerdict)`: `LimitVerdict` lives in `web/middleware.py` | web.md §9; DO-3 §2.1 | AC-6 | **added**: the `TurnVerdict` Protocol (built) | Part A (built) |
| `DemoService` (AEA-30) not merged; `SessionService(..., demo: DemoService, ...)` | web.md §14 | AC-1 | **added**: the `DemoReads` Protocol (`staffing()`, `clock_view()`); the container passes a lazy forwarder | Steps B1, H |
| `ClockView`, `StaffingView` | web.md §14; cases.md §6 | AC-1, AC-16 | in-ticket: `meridian.domain.views` (AEA-02b, merged) | Step B1 |
| `TextId.HISTORY_CODE_ENTERED` / `HISTORY_DETAILS_SENT` | data.md §2 (AEA-03b) | AC-19 | in-ticket: on `main` (`policy/texts.py:107–108`) | Step B2 |
| `started_wall_at` and `staffing_at_start` on the conversations row | AEA-32 alert reads `MAX(started_wall_at)`; DO-6 M-22 | — | **added**: `SessionService` takes keyword-only `wall_clock`. The frozen `make_session_service` already passes it (PA-5) | Step B1; §8 R-3 |
| Restart sweep through `core.turns.fail_running()` | cases.md §1.2, R-G-22 | AC-12 | in-ticket (built; `repos_core.py:427`) | Step H |
| A second app lifespan must not include the chat router twice | precedent: every merged hunk since AEA-41 (`app.state.<x>_included`) | — | **added**: guard flag `app.state.chat_routes_included` | Step H |
| CON-4 stored body in history | web.md §8 `PersonRequestOutcome`; AEA-42 merged | AC-17 | in-ticket: parse with `PersonRequestOutcome.model_validate_json` | Step B3 |
| `turn_sweep` / `turn_error` records missing from `web/logging.py`'s allow-list | web.md §10; WEB-11 | AC-12 (count line) | in-ticket at record level (tests read the `LogRecord` attribute); **request** an AEA-23 follow-up (§8 R-5), not blocking | Step H |
| Cross-table order of history entries under a frozen demo clock | web.md §14 ("`at`, then the row's id within its table") | AC-16, AC-18 | **added**: the anchored merge in Step B3 | Step B3; §8 R-1 |
| A re-run of a failed turn must not duplicate the customer line | web.md §14 entry 2; AC-3 | AC-3, AC-16 | **added** (built): step 4 reuses that `turn_id`'s customer message | Part A (built) |
| A row stuck `running` after a step-7 storage error | DO-4 §14 step 3 | — | **added** (built): a fresh transaction finishes it `failed`, then re-raises | Part A (built) |
| `customer_message` speaker name | staff.md §1, §7, R-W-14 | AC-20 | in-ticket: `CUSTOMER_SPEAKER_NAME` ("Customer") | Part A (built) |
| Journey stubs name AEA-57, which has merged; integrated steps must report the real blockers | `integrated-journeys.md` §3 rule 6, §4 | AC-15 | **added**: Step T replaces the stubs with harness steps (`journey.step(needs=…)`) | Step T |
| TURN_TIMEOUT and BUSY through the real server need a held provider call, which the harness lacks | AC-15 | AC-15 | **request** an AEA-57 follow-up (§8 R-6); until then those two stay mock-tested, with the reason recorded | Step T; §8 R-6 |
| Card `answered` after reload (AEA-40-3) | web.md §14 says it is not rebuilt | excluded by the ticket | **other-ticket / open** (orchestrator); build web.md §14 | — |
| Rate-limit counting, 503 reset answers, startChatSession's 429 | web.md §5, §7 | out of scope | other-ticket (AEA-23 middleware, merged) | — |
| The CON-4 turn row itself | web.md §8 | out of scope | other-ticket (AEA-42, merged). This ticket only **reads** it | Step B3 |
| Full CAP-1/CAP-2 with the real graph | DO-6 | AC-14 note | other-ticket (AEA-51) | — |
| No growing message list | context-management rule 1 | AC-10 | in-ticket (built): `TurnInput` carries one message | Part A (built) |

### 1.5 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `POST /api/chat/sessions` (`startChatSession`, CON-1) | WF-1 | DO-6 WF-1 row | M-22 (conversations/day by tag), M-3, M-18 (outcome) |
| `GET /api/chat/sessions/{thread_id}` (`getChatThread`, CON-1) | WF-1 | DO-6 WF-1 row | request record only (AEA-23 middleware) |
| `POST /api/chat/sessions/{thread_id}/turns` (`submitTurn`, CON-2) | WF-1 | DO-6 WF-1 row | M-8, M-14, M-16, M-17, M-19…M-26, M-29 |
| Start-up sweep in `register_chat` | WF-1 (*Missing instrumentation*) | web.md §9, R-W-4 | M-24 (timeouts by reason) |

---

## 2. Boundary

### 2.1 Owned files (the only files anyone working this ticket creates or edits)

| File | State on the branch | Action | Who |
|---|---|---|---|
| `src/meridian/services/turn.py` | built (563 lines) | keep; fix only if a test goes red after the merge | implementer |
| `src/meridian/services/session.py` | absent | **create** (Part B) | implementer |
| `src/meridian/web/routes/chat.py` | `submitTurn` only | **add** `start_chat_session`, `get_chat_thread` | implementer |
| `src/meridian/web/schemas/chat.py` | `TurnRequest` only | **add** `EventsRef`, `StartSessionResponse`, `ChatThreadTurn`, `ChatThread` | implementer |
| `src/meridian/web/container.py` | `register_chat` body (Part A) | modify **only** `register_chat`'s body and docstring (Step H) | implementer |
| `tests/services/chat_doubles.py` | frozen, 1,002 lines | split in Step T (no assertion change) | **test-writer** |
| `tests/services/chat_storage.py` | absent | **create** in Step T (the second half of `chat_doubles.py`) | **test-writer** |
| `tests/services/test_turn.py`, `tests/services/test_session.py` | frozen | Step T may update import lines only | **test-writer** |
| `tests/api/chat_support.py`, `tests/api/test_chat.py`, `tests/api/test_chat_capture.py`, `tests/api/test_contract_cases_chat.py` | frozen | Step T may update import lines only | **test-writer** |
| `tests/unit/web/test_register_chat.py`, `tests/contract/cases/chat.py` | frozen | none | **test-writer** |
| `tests/journeys/j1/test_aea_40.py`, `tests/journeys/j9/test_aea_40.py` | frozen | Step T replaces the skip stubs | **test-writer** |
| `docs/testing/journeys/2026-10-21-AEA-40.md` | Part A version | rewritten by `--journey-record=AEA-40` (Step D.4), then the implementer adds the *Remaining limitations* lines | implementer |
| `.claude/reference/area-map.md` | conflict at merge | the A8 row's status cell only | implementer |
| `.claude/state/icm-progress.md` | conflict at merge | the one AEA-40 *Routes verified* row only | implementer |
| `docs/design/code-design.md` | conflict at merge | the one AEA-40 `**Built:**` line only | implementer |

### 2.2 Shared surfaces you read but never edit

- **Source:** `src/meridian/domain/*` (incl. `views.py`), `src/meridian/ports/*`, `src/meridian/config.py`,
  `src/meridian/policy/{texts,limits}.py`, `src/meridian/gates/gate.py`, `src/meridian/privacy/redact.py`,
  `src/meridian/adapters/sqlite/*`, `src/meridian/services/{ledger,reset_gate,person_request,live_chat,...}.py`,
  `src/meridian/web/{app,deps,errors,logging,middleware,frontend}.py`, every other `web/routes/*.py` and
  `web/schemas/*.py`, every other `register_*` hunk.
- **Tests:** `tests/api/openapi_check.py`, `tests/api/web_shell_support.py`, `tests/fakes/*`,
  `tests/fixtures/sqlite.py`, `tests/conftest.py`, `tests/journeys/support/*`, `tests/journeys/affected.py`,
  `tests/contract/*` (except `cases/chat.py`).
- **Contract:** the OpenAPI file.

### 2.3 Owned by other tickets — do not create or edit

- **Code:** `web/routes/{events,handoff,demo,reads,staff_*}.py` and their schemas; `services/{person_request,demo,
  live_chat,cases,handoff,staff,reset,scheduling,identity,health}.py`; `agent/**`.
- **Tests:** `tests/journeys/j1/test_aea_57.py` and every other journey file; `tests/journeys/support/` (AEA-57);
  `tests/contract/test_openapi_*.py`, `openapi_cases.py`, `openapi_driver.py` (AEA-59).
- **Never edit:** `apps/web/**`, `docs/ux/**`, `UI_CONTRACTS.md`, the briefing, issued data, `docs/archive/`,
  `docs/parked/`.
- **Do not add** `TextId` members, domain types, container keys in `deps.py`, or `NEED_OWNERS` entries yourself.

---

## 3. Requirements

### 3.1 Acceptance criteria → implementation → verification (frozen-test manifest)

The criteria text is the issue's (`docs/plans/tickets/AEA-40.md` lines 139–161). This table is the test-writer's
manifest, frozen at `61d5bd8` and amended in Step T. Abbreviations:

- **TT** = `tests/services/test_turn.py`
- **TS** = `tests/services/test_session.py`
- **TA** = `tests/api/test_chat.py`
- **TC** = `tests/api/test_chat_capture.py`

"State at `d7fb642`" is the state before the merge. **Every row must be green after Step B5.**

| AC | Kind | Implemented in | Frozen test(s) (names binding) | State at `d7fb642` |
|---|---|---|---|---|
| AC-1 | invariant | `SessionService.open`; route `start_chat_session` | TA `::test_start_session_fixed_greeting_no_model`; TS `::test_open_writes_one_transaction_with_wall_start`, `::test_open_is_one_transaction`, `::test_two_opens_make_two_threads` | red (Part B) |
| AC-2 | failure/refusal | `owned_thread` (AEA-23) on both thread routes; history keeps stored STORE text | TA `::test_get_thread_redacted`, `::test_thread_not_found_identical_for_malformed_unknown_and_foreign`, `::test_ended_thread_410` | red (Part B) |
| AC-3 | invariant | `run_turn` step 3 (`begin`) | TT `::test_same_turn_id_returns_stored`, `::test_running_turn_409`, `::test_failed_turn_reruns` | green |
| AC-4 | failure/refusal | step 1 admission (`BoundedSemaphore(30)`) → `_reject(BUSY)` | TT `::test_admission_31st_turn_busy` | green |
| AC-5 | failure/refusal | step 2 → `_reject(SPEND_CAP_REACHED)` | TT `::test_spend_cap_notice_no_model` | green |
| AC-6 | failure/refusal | route branch + `rate_limited` | TA `::test_rate_limited_notice_then_same_turn_runs` | green |
| AC-7 | failure/refusal | step 6 DEADLINE branch; graph-exception branch | TT `::test_deadline_turn_timeout_notice`, `::test_graph_exception_degraded_not_500`; TA `::test_timeout_and_exception_notices_via_submit_turn` | green |
| AC-8 | negative | `parse_intake`; step 4 stores `text_store`; step 5 `TurnInput` vs `TurnContext.intake` | TT `::test_intake_redacted_and_never_in_turn_input` | green |
| AC-9 | negative | `TurnRequest` → domain `TurnPayload`; AEA-23's 422→400 handler | TA `::test_validation_error_hides_value` | green |
| AC-10 | invariant | step 5: one `TurnContext` / `TurnInput` per turn | TT `::test_turn_context_and_inputs_turns_1_2_5` | green |
| AC-11 | invariant | step 4: `last_customer_wall_at`; the CON-21 event in the same commit | TT `::test_customer_message_event_same_commit_when_human`; TA `::test_customer_message_event_via_submit_turn` | green |
| AC-12 | invariant | `register_chat` on-start sweep | TT `::test_restart_sweep_fails_every_running_turn` | green |
| AC-13 | invariant | no `uow(...)` around step 5 | TT `::test_no_uow_open_during_run_graph` | green |
| AC-14 | capture | routes + both services write every DO-6 field | TC `::test_con1_con2_records_written` (+ `::test_trace_id_and_export_status_recorded`, `::test_eval_key_tags_runs_and_live_is_the_default`) | red (needs CON-1) |
| AC-15 | journey | J-1, J-9 | `tests/journeys/j1/test_aea_40.py`, `tests/journeys/j9/test_aea_40.py` (after Step T) | J-9 mock green; J-1 red |
| AC-16 | invariant | `SessionService.thread` (Step B3) | TS `::test_thread_holds_full_history`, `::test_failed_turn_contributes_only_its_customer_line`, `::test_thread_not_open_for_unknown_thread`; TA `::test_get_thread_full_history` | red (Part B) |
| AC-17 | invariant | Step B3, CON-4 entries | TS `::test_thread_shows_person_request_card[handoff]`, `[live_queued]` | red (Part B) |
| AC-18 | invariant | Step B3 merge | TA `::test_thread_history_includes_greeting_staff_and_event_lines` | red (Part B) |
| AC-19 | invariant | Step B2 display texts | TA `::test_history_display_texts` | red (Part B) |
| AC-20 | invariant | step 4 payload builder `_customer_message_event` | TT `::test_customer_message_payload_valid_and_unnamed` | green |
| AC-21 | invariant | `next_outcome` / `reopened_outcome`, applied in steps 4 and 7 | TT `::test_conversation_outcome_rules`; TC `::test_conversation_outcome_via_submit_turn` | TT green; TC red (needs CON-1) |
| AC-22 | contract | `tests/contract/cases/chat.py` | `tests/api/test_contract_cases_chat.py::test_chat_cases_cover_documented_statuses`; AEA-59 runner: `uv run pytest tests/contract/test_openapi_server.py -k "startChatSession or getChatThread or submitTurn" -rs` | red (needs CON-1) |
| AC-23 | regression/context | docs rows | `git diff --name-only main...HEAD` | Part A rows only |

Also frozen and binding (route and service extras): TA `::test_start_session_tags_eval_runs_and_leaves_others_live`,
`::test_submit_turn_other_threads_are_refused_and_run_nothing`, `::test_chat_routes_need_a_session`,
`::test_running_turn_409_via_submit_turn` and `::test_completed_turn_resent_is_byte_identical`; TT
`::test_timed_out_turn_reruns`, `::test_next_outcome_table`,
`::test_reopened_outcome_never_reopens_handed_off_or_safety` and `::test_unknown_thread_is_refused_not_created`.

### 3.2 Plan-added criteria (propose them on issue #40 at merge)

| Id | Criterion | Frozen test |
|---|---|---|
| PA-1 | `register_chat` behaves differently by app type. **On a bare `FastAPI()`** it provides nothing and adds no route. **On an app with a web shell** it: provides `deps.SESSION_SERVICE` (memoised) and `deps.TURN_SERVICE`; registers the three routes with their operation ids; and raises `RuntimeError("not bound: <key>")` for an unbound sibling only when that sibling is called, never at build | `tests/unit/web/test_register_chat.py::test_bare_app_gets_nothing`, `::test_wires_services_routes_and_lazy_siblings` |
| PA-2 | A re-run of a failed `turn_id` reuses its customer message | TT `::test_failed_turn_reruns` |
| PA-3 | A storage failure in step 7 leaves the turn row `failed`, never `running` | TT `::test_step7_failure_leaves_row_failed` |
| PA-4 | `services/turn.py`'s `LOG_RECORD_ATTR` equals `meridian.web.logging.RECORD_ATTR` | TT `::test_log_record_attr_matches_web_logging` |
| PA-5 | `open` writes `conversations.started_wall_at` (UTC) and `staffing_at_start` | TS `::test_open_writes_one_transaction_with_wall_start` |
| PA-6 | A second lifespan on the same app does not add the chat routes again | none frozen; verified by `tests/api/test_app.py` (full app, two lifespans) staying green |

---

## 4. Shared code to use (copied from `main` at `b559c75`, identical at `2ec19ad`; never paraphrase)

### 4.1 Domain (AEA-02, AEA-02b)

```python
from meridian.domain.common import ApiErrorCode, EventId, HaltReason, MeridianModel, RequestId, ThreadId, TurnId
#   MeridianModel: ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
#   ThreadId / TurnId / RequestId: str subclasses, UUID4 pattern, strict. ThreadId(str(uuid.uuid4())) is fine
#   (web/deps.py and AEA-42 do it); pydantic validates on model construction. EventId = Annotated[int, Field(ge=0)]
from meridian.domain.actions import Settled
from meridian.domain.blocks import (FailureOfferBlock, HandoffBlock, LiveQueuedBlock, Notice, NoticeBlock, ReplyBlock,
                                    SettledView, Speaker, TextBlock, Write)
#   Speaker(kind: Literal["assistant","customer","representative","event"], display_name: str | None)
#   TextBlock(block_id, speaker, at, text: str, sources: tuple[SourceChip, ...])          # type="text"
#   Card blocks carry card_id: str and options: tuple[Option(option, label, disabled, reason), ...]
from meridian.domain.identity import IdentityState
from meridian.domain.state import Controller           # kind: Literal["ai","human"]; representative_name; case_ref
from meridian.domain.staff import CUSTOMER_SPEAKER_NAME, LoginSession, STAFF_PERSONAS, StaffRole
#   CUSTOMER_SPEAKER_NAME = "Customer"; STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name == "Riley"
from meridian.domain.views import ClockView, StaffingView        # AEA-02b, merged
#   class StaffingView(MeridianModel): mode: Presence; label: str; banner: str | None          # = OpenAPI Staffing
#   class ClockView(MeridianModel):    now: dt.datetime; label: str; date_label: str           # = OpenAPI DemoClock
from meridian.domain.turn import (GraphOutcome, Intake, RunGraph, TurnBudget, TurnContext, TurnIds, TurnInput,
                                  TurnPayload, TurnRecord, TurnTrace)
```

The `domain/turn.py` signatures are unchanged since the first plan:
`TurnIds(thread_id, turn_id, request_id, run_tag, run_id, agent_version)`, `TurnBudget(started, deadline)`,
`Intake(kind, text_store, code_digits: SecretStr | None, form, card_number_seen, choice, card_id)`,
`TurnInput(turn_id, message_id, kind, text_store, card_id, choice, card_number_seen, received_at)`,
`TurnContext(ids, budget, now, demo_session, span, intake)`, `TurnRecord(status, trace, replied_at, server_ms,
model_calls, input_tokens, output_tokens, cost_usd, tool_calls, trace_id, trace_export, response)`,
`GraphOutcome(reply, turn_trace, check_events, halt, closed_every_open_task)`,
`RunGraph = Callable[[TurnInput, TurnContext], GraphOutcome]`.

### 4.2 Pure core, ports, policy

```python
from meridian.gates.gate import parse_intake          # def parse_intake(payload: TurnPayload) -> Intake (pure)
#   code → text_store "[code entered]"; form → "[details submitted]" (a "where" form stores the redacted place);
#   choice → kind "choice", choice=CardChoice(card_id, option), card_id set; text → STORE-redacted
from meridian.privacy.redact import RedactionProfile, redact
from meridian.policy.texts import TextId, render       # render(text_id: TextId, /, **values: str) -> str
#   TextId.GREETING, BUSY, RATE_LIMITED, SPEND_CAP_REACHED, TURN_TIMEOUT, FAILURE_OFFER, PERSON_REQUEST_LABEL,
#   HISTORY_CODE_ENTERED ("Code entered"), HISTORY_DETAILS_SENT ("Details sent")
from meridian.policy.limits import Limits
#   limits.admission.max_in_flight == 30; limits.turn.deadline_s == 60; limits.turn.turn_deadline_ms == 60000;
#   limits.turn.still_working_after_ms == 10000; limits.turn.browser_give_up_after_ms == 65000;
#   limits.turn.max_message_chars == 2000; limits.web.chat_turns_per_thread_per_min == 20
from meridian.ports.runtime import Clock, TraceSink, UnitOfWorkFactory
from meridian.services.ledger import SpendGuard        # Protocol: def allow_turn(self) -> bool
from meridian.services.person_request import PersonRequestOutcome   # AEA-42, merged
#   class PersonRequestOutcome(MeridianModel): result: Literal["case_created","live_queued","already_open"];
#       block: Annotated[HandoffBlock | LiveQueuedBlock, Field(discriminator="type")]; settled: SettledView
```

### 4.3 Storage (AEA-10). `with uow(write=True) as tx:`; nothing commits unless `tx.commit()` ran

```python
from meridian.adapters.sqlite.rows import (ConversationRow, EndedThread, EventRow, MessageRow, StreamEvent, TurnRow,
                                           case_stream, thread_stream)
tx.core.conversations.lookup(thread_id: str) -> ConversationRow | EndedThread | None
tx.core.conversations.insert(row: ConversationRow) -> None
tx.core.messages.append(thread_id, role, text_redacted, at, *, turn_id=None, kind=None, card_id=None,
                        choice_option=None) -> int
tx.core.messages.all_for_thread(thread_id) -> tuple[MessageRow, ...]          # ORDER BY id
tx.core.turns.for_thread(thread_id) -> tuple[TurnRow, ...]                    # ORDER BY sequence
tx.core.turns.fail_running() -> tuple[TurnId, ...]
tx.core.events.after(stream: StreamKey, last: EventId) -> list[EventRow]     # EventRow(id, stream, type, payload, at)
tx.core.events.latest_id(stream: StreamKey) -> EventId                       # 0 when none
tx.core.reads.identity_state(thread_id) -> IdentityState
tx.core.settled_for(thread_id: ThreadId, read_at: datetime) -> Settled
tx.cases.cases.list_for_thread(thread_id) -> tuple[CaseRow, ...]             # CaseRow.case_ref: CaseRef
```

The row fields used:

- `ConversationRow(thread_id, demo_session, run_tag, run_id=None, agent_version, started_at, started_wall_at=None,
  staffing_at_start=None, outcome="open", ended_wall_at=None, last_customer_wall_at=None,
  controller=Controller(kind="ai"), live_state="not_live", live_since=None)`.
- `MessageRow(id, thread_id, role, text, at, turn_id, kind, card_id, choice_option)`.
- `TurnRow(turn_id, …, sequence, received_at, status, gate_result, …, replied_at, …, response)`.

**Stored event payloads**, as written on `main`:

- **AEA-46** (`services/live_chat.py`):
  - `representative_joined` `{"speaker", "display_name", "line"}`;
  - `ai_paused` `{"speaker", "line"}`;
  - `staff_message` `{"speaker", "message_id": str, "text"}`;
  - `ai_resumed` `{"speaker", "line"}`;
  - `chat_closed` `{"speaker", "line", "composer_disabled"}`.
- **AEA-30** (planned, cases.md §6): `staffing_changed` `{"speaker", "staffing", "line"}`.
- **AEA-29/30** (planned): `shift_ended` `{"speaker", "line", "handoff", "settled"}`.
- **This ticket**, on `case:<ref>`: `customer_message` `{"message": {"message_id", "speaker", "at", "text"}}`.

### 4.4 Web shell (AEA-23) and the hunk pattern

```python
from meridian.web.errors import ApiProblem      # ApiProblem(status, code, *, field=None, constraint=None, details=None)
from meridian.web.deps import (get_login_session, get_request_context, get_session_service, get_turn_service,
                               owned_thread, DEMO_SERVICE, REPLY_COMPOSER, SESSION_SERVICE, TURN_SERVICE,
                               UOW_FACTORY, WALL_CLOCK)
#   owned_thread → this session's live thread; its ended thread → ApiProblem(410, SESSION_ENDED, details={"reason"});
#   malformed / unknown / foreign → the identical ApiProblem(404, SESSION_NOT_FOUND)
from meridian.web.middleware import RequestContext, WebShellState
#   RequestContext(request_id, client_ip, session, run_tag, run_id, turn_verdict: LimitVerdict | None)
from meridian.web.logging import emit_record    # emit_record(logger_name, fields)
from meridian.web.container import Container, ContainerError, Key
```

The router-guard pattern every merged hunk uses (copy it; `register_staff_session`, `register_reads`):

```python
if not getattr(app.state, "chat_routes_included", False):
    app.include_router(build_router())
    app.state.chat_routes_included = True
```

### 4.5 Test helpers on `main` (the test-writer uses them in Step T; the implementer only runs tests)

- `tests/api/openapi_check.py`: `assert_response_matches`, `assert_sse_frames_match`, `SseFrame`.
- `tests/journeys/support/run.py`:
  - `JourneyRun.login() -> LoginResult(client, response, session_id, cookie)`;
  - `JourneyRun.step(journey, name, *, needs=(), operations=())`, a context manager that records pass, fail or
    blocked and skips while a need is unbound;
  - `journey.db.one/rows/count/scalar`, `journey.logs.all_text()`, `journey.container.limits`.
- `tests/journeys/support/client.py`: `JourneyClient.call(method, path, *, operation_id, body=None, headers=None)`.
- `tests/journeys/support/steps.py`: `NEED_OWNERS` names `"session_service"`, `"turn_service"` (AEA-40),
  `"demo_service"`, `"demo_clock"` (AEA-30), `"reply_composer"`, `"run_graph"` (AEA-51).

### 4.6 What this ticket exports (exact; AEA-24, 42, 51, 52, 57, 58 build against it)

The `services/turn.py` block is **built** at `d7fb642`. The `session.py` and Part B schema blocks are **new**.

```python
# ---- src/meridian/services/turn.py (built) ---------------------------------------------------------------------
TURN_LOGGER: Final = "meridian.services.turn"
LOG_RECORD_ATTR: Final = "meridian_record"
TURN_IN_PROGRESS_RETRY_MS: Final = 2000
ASSISTANT_SPEAKER: Final = Speaker(kind="assistant", display_name="Meridian assistant")
SettledViewFn = Callable[[Settled, IdentityState, Controller], SettledView]
class RunTurn(MeridianModel): thread_id; turn_id; request_id; demo_session: str; payload: TurnPayload;
                              run_tag: Literal["live","eval","load"]; run_id: str | None
class ChatController(MeridianModel): kind: Literal["ai","human"]; display_name: str | None
class TurnResponse(MeridianModel): thread_id; turn_id; sequence: int; blocks: tuple[ReplyBlock, ...];
                                   settled: SettledView; writes: tuple[Write, ...]; controller: ChatController;
                                   notice: Notice | None; last_event_id: EventId
class TurnVerdict(Protocol): allowed (property) -> bool
class TurnInProgress(Exception): retry_after_ms
class ThreadNotOpen(Exception): ...
def next_outcome(stored, trace_outcome, closed_every_open_task) -> str | None
def reopened_outcome(stored) -> str | None
class TurnService:
    def __init__(self, uow, demo_clock: Clock, wall_clock: Callable[[], datetime], spend: SpendGuard,
                 trace: TraceSink, run_graph: RunGraph, settled_view: SettledViewFn, limits: Limits,
                 agent_version: str, *, monotonic: Callable[[], float] = time.monotonic) -> None
    def run_turn(self, cmd: RunTurn) -> TurnResponse
    def rate_limited(self, cmd: RunTurn, verdict: TurnVerdict) -> TurnResponse

# ---- src/meridian/services/session.py (NEW, Part B) ------------------------------------------------------------
GREETING_TURN_ID: Final = "greeting"
GREETING_BLOCK_ID: Final = "blk-greeting"
EVENT_LINE_TYPES: Final = frozenset({"representative_joined", "ai_paused", "ai_resumed", "chat_closed",
                                     "staffing_changed"})
class DemoReads(Protocol):                          # the two DemoService methods this service reads
    def staffing(self) -> StaffingView: ...
    def clock_view(self) -> ClockView: ...
def greeting_block(text: str, at: datetime) -> TextBlock:
    # TextBlock(block_id=GREETING_BLOCK_ID, speaker=ASSISTANT_SPEAKER, at=at, text=text, sources=())
class ChatLimits(MeridianModel):                    # web.md §14 verbatim
    turn_deadline_ms: int; still_working_after_ms: int; browser_give_up_after_ms: int; max_message_chars: int
class ChatOpened(MeridianModel):                    # web.md §14 verbatim
    thread_id: ThreadId; greeting_message_id: int; greeting_text: str; greeting_at: datetime
    clock: ClockView; staffing: StaffingView; controller: Controller; settled: SettledView
    limits: ChatLimits; last_event_id: EventId
class HistoryEntry(MeridianModel):                  # web.md §14 verbatim
    turn_id: str; speaker_kind: Literal["assistant", "customer", "representative", "event"]
    speaker_name: str | None; at: datetime; text: str | None; blocks: tuple[ReplyBlock, ...]
class ThreadHistory(MeridianModel):                 # web.md §14 verbatim
    thread_id: ThreadId; state: Literal["open", "closed"]; entries: tuple[HistoryEntry, ...]
    settled: SettledView; clock: ClockView; staffing: StaffingView; last_event_id: EventId
class SessionService:                               # web.md §14 + one additive keyword (PA-5, §8 R-3)
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, demo: DemoReads, limits: Limits,
                 settled_view: SettledViewFn, agent_version: str, *,
                 wall_clock: Callable[[], datetime] = _utc_now) -> None: ...
    def open(self, session: LoginSession, *, run_tag: Literal["live", "eval", "load"], run_id: str | None,
             request_id: RequestId) -> ChatOpened: ...
    def thread(self, thread_id: ThreadId) -> ThreadHistory: ...

# ---- src/meridian/web/routes/chat.py (built: CHAT_LOGGER, submit_turn, build_router; NEW: two CON-1 routes) -----
CHAT_LOGGER: Final = "meridian.web.chat"

# ---- src/meridian/web/schemas/chat.py (built: TurnRequest; NEW below) -------------------------------------------
class EventsRef(MeridianModel): url: str; last_event_id: EventId
class StartSessionResponse(MeridianModel):          # = OpenAPI StartSessionResponse
    thread_id: ThreadId; greeting: TextBlock; demo_clock: ClockView; staffing: StaffingView
    controller: ChatController; settled: SettledView; events: EventsRef; limits: ChatLimits
class ChatThreadTurn(MeridianModel):                # = ChatThread.turns[] item
    turn_id: str; speaker: Speaker; at: datetime; text: str | None; blocks: tuple[ReplyBlock, ...]
class ChatThread(MeridianModel):                    # = OpenAPI ChatThread
    thread_id: ThreadId; state: Literal["open", "closed", "ended_by_reset"]; turns: tuple[ChatThreadTurn, ...]
    settled: SettledView; demo_clock: ClockView; staffing: StaffingView; last_event_id: EventId
```

`web/schemas/chat.py` imports `ChatController` from `meridian.services.turn` and `ChatLimits` from
`meridian.services.session`. web/ may import services; services may not import web.

---

## 5. Steps (build order; each step ends with a check)

**Design boundary:** routes (web/) → services (A8) → pure core / ports / `adapters/sqlite` repositories. This ticket
adds no new seam beyond `TurnVerdict` (built), `DemoReads` and the `SettledViewFn` alias. Each one is the minimum a
service needs from a module it may not import.

### Step 0 — verify the branch (done at `6891c3c`; implementer; no product code)

The merge of `b559c75` is committed (`6891c3c`). Do only these checks:

1. `cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-40`, `export UV_LINK_MODE=hardlink`, `df -h /home`
   (below 3 GB free: stop and report).
2. `git status --short`. Expected: ` M .claude/reference/area-map.md` and `?? src/meridian/services/session.py` (the
   in-progress draft), plus whatever a later run of this plan added. **Never** `git checkout --`, `git stash`,
   `git clean` or `git reset` them. Anything else uncommitted: stop and report.
3. `git log --oneline -1` shows `6891c3c` (or a later commit of this ticket). Do not run `git merge main` again
   (§0 fact 2).
4. Import check: `uv run python -c "import meridian.web.app, meridian.services.turn"` succeeds.
5. **Part A still green on the merged branch** (run once if no earlier report shows it):
   `uv run pytest tests/services/test_turn.py tests/unit/web tests/unit/test_import_direction.py tests/api/test_app.py
   -q -p no:cacheprovider`.
   - Expected: all pass, except `test_register_chat.py::test_wires_services_routes_and_lazy_siblings` (it needs
     `SESSION_SERVICE`, Step H). `test_import_direction.py` may also flag the uncommitted `session.py` draft until B1
     is finished; fix the draft, never the test.
   - If another Part A test is red, fix **`services/turn.py` or the hunk** (never the test) and record the cause in
     the report.

The merge-conflict resolutions Step 0.3 used are kept for the record: A8 row = main's cell with the Part A clause
inserted before "; the rest planned"; ICM progress and code-design keep both sides' rows, the AEA-40 Part A line last.
The A9 row must **not** carry the Part A clause (the uncommitted fix above removes it).

### Step T — test-writer amendment (dispatched by the orchestrator **before** the implementer's Part B work)

**Who:** `test-writer-agent`, on the same branch (Step 0's merge `6891c3c` is already there). It touches only the
test files listed below, never the uncommitted `session.py` or `area-map.md`, and commits only its own paths. **Assertions do not change.** Then re-record the frozen-test manifest (hashes) and
commit `test(AEA-40): journey stubs onto the AEA-57 harness; split chat_doubles under the 500-line cap`.

**T1. `tests/journeys/j1/test_aea_40.py`.** Keep `test_j1_login_start_one_turn_reload_resumes_the_same_thread`
(mock level) unchanged. Replace the `@pytest.mark.skip` stub `test_j1_through_the_real_server_with_the_scripted_model`
with:

```python
TURN_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer", "turn_service",
              "run_graph")

def test_j1_code_turn_and_reload_through_the_real_server(journey: JourneyRun) -> None:
    """integrated (AC-15, AC-19, AC-8): a code turn reads "Code entered" after a reload; the digits are stored nowhere."""
    with journey.step("J-1", "AEA-40 code turn and reload", needs=TURN_NEEDS,
                      operations=("login", "startChatSession", "submitTurn", "getChatThread")):
        signed = journey.login()
        start = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        assert start.status_code == 201
        thread_id = start.json()["thread_id"]
        code = "".join(str(d) for d in random.Random(4041).choices(range(10), k=6))
        turn_id = str(uuid.uuid4())
        sent = signed.client.call("POST", f"/api/chat/sessions/{thread_id}/turns", operation_id="submitTurn",
                                  body={"turn_id": turn_id,
                                        "payload": {"kind": "code", "card_id": "code-card-1", "code": code}})
        assert sent.status_code == 200
        reloaded = signed.client.call("GET", f"/api/chat/sessions/{thread_id}", operation_id="getChatThread")
        turns = reloaded.json()["turns"]
        assert turns[0]["turn_id"] == "greeting"
        assert (turns[1]["speaker"]["kind"], turns[1]["turn_id"], turns[1]["text"]) == (
            "customer", turn_id, render(TextId.HISTORY_CODE_ENTERED))
        row = journey.db.one("SELECT text FROM messages WHERE turn_id = ? AND role = 'customer'", (turn_id,))
        assert row["text"] == "[code entered]"
        assert journey.db.count("conversations", "demo_session = ?", (signed.session_id,)) == 1
        for table in ("messages", "turns", "conversations", "check_events", "events"):
            assert code not in json.dumps(journey.db.rows(f"SELECT * FROM {table}"), default=str)  # noqa: S608
        assert code not in journey.logs.all_text()
```

Imports to add: `json`, `random`, `uuid`; `from tests.journeys.support.run import JourneyRun`. Keep
`pytestmark = pytest.mark.journey`. Update the module docstring:

> Level today: the mock test runs (`mock-tested`); the integrated test is blocked by AEA-30 (demo clock, DemoService)
> and AEA-51 (reply composer, graph) and is reported by the harness as blocked.

**T2. `tests/journeys/j9/test_aea_40.py`.** Keep the three mock tests unchanged. Replace the stub
`test_j9_notices_through_the_real_server_with_the_scripted_model` with **two** tests:

```python
def test_j9_rate_limited_through_the_real_server(journey: JourneyRun) -> None:
    """integrated (AC-15): the real limiter refuses the 21st turn on a thread with a RATE_LIMITED notice, never 429."""
    with journey.step("J-9", "AEA-40 RATE_LIMITED through the real limiter", needs=TURN_NEEDS,
                      operations=("login", "startChatSession", "submitTurn")):
        signed = journey.login()
        thread_id = signed.client.call("POST", "/api/chat/sessions",
                                       operation_id="startChatSession").json()["thread_id"]
        limit = journey.container.limits.web.chat_turns_per_thread_per_min
        codes: list[str | None] = []
        last_turn = ""
        for n in range(limit + 1):
            last_turn = str(uuid.uuid4())
            r = signed.client.call("POST", f"/api/chat/sessions/{thread_id}/turns", operation_id="submitTurn",
                                   body={"turn_id": last_turn, "payload": {"kind": "text", "text": f"message {n}"}})
            assert r.status_code == 200
            codes.append((r.json()["notice"] or {}).get("code"))
            if codes[-1] == "RATE_LIMITED":
                break
        assert codes[-1] == "RATE_LIMITED" and "RATE_LIMITED" not in codes[:-1]
        notice = r.json()["notice"]
        assert notice["actions"] == ["talk_to_person"] and notice["retry_turn_id"] is None
        row = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (last_turn,))
        assert (row["status"], row["outcome"], row["degrade_reason"]) == ("failed", "degraded_handoff", "rate_limit")
        assert journey.db.count("messages", "turn_id = ?", (last_turn,)) == 0


@pytest.mark.skip(reason="blocked-on AEA-51 and an AEA-57 follow-up (a scripted entry that holds a provider call): "
                         "TURN_TIMEOUT and BUSY through the real server; mock-tested above")
def test_j9_timeout_and_busy_through_the_real_server() -> None:
    """TURN_TIMEOUT and BUSY through the real server process and the scripted model adapter (integrated level)."""
```

`TURN_NEEDS` is as in T1, defined in this file too. Update the docstring as in T1.

**T3. Split `tests/services/chat_doubles.py` (1,002 lines) at its section boundary.**

- **Lines 1–518 stay** in `chat_doubles.py`: ids, payloads, `FakeSpendGuard`, the outcome builders, the `run_graph`
  doubles, `FakeComposer`, `resolve_domain_class`, `history_text_id`, `FakeDemo`, `human_controller`,
  `seed_thread`, `make_cmd`, `make_turn_service`, `make_session_service`.
- **Lines 520–1002 move** to a new `tests/services/chat_storage.py`: `conversation`, `messages_of`,
  `customer_messages`, `turn_row`, `count_rows`, `raw_value`, `text_dump`, `HookedUow` with its proxies,
  `fail_after`, `fail_first_call`, `handoff_block`, `live_queued_block`, `notice_codes`, `has_person_key`,
  `Collected`, `turn_ids_of`, `records_of_kind`, `log_blob`, `notice_of`, `dump_json`, `data_dir_text`, `RILEY`,
  `Takeover`, `seed_case`, `seed_person_request_turn`, `seed_takeover`, `newest_event_id`, `attr`.
- `chat_storage.py` imports what it needs from `chat_doubles.py` (e.g. `AGENT_VERSION`, `new_turn_id`,
  `new_request_id`, `empty_view`, `ASSISTANT_SPEAKER`).
- Update the `from tests.services.chat_doubles import (...)` lines in every test file to import each name from its new
  module. **No other line changes.**
- `test_turn.py` (684 lines) and `test_chat.py` (588 lines) stay as they are. Every test in them is named by an
  acceptance criterion or this plan, so moving one would break a node id the signed ticket cites. Say so in the commit
  message (precedent for an authorised split: `f247370`).

**T-check.** Run:

- `uv run pytest --collect-only -q tests/services tests/api tests/unit/web tests/journeys/j1/test_aea_40.py
  tests/journeys/j9/test_aea_40.py`. It collects with the same count as before, plus one test.
- `uv run ruff check` and `uv run ruff format --check` on the changed files.
- `uv run mypy tests/services tests/journeys/j1/test_aea_40.py tests/journeys/j9/test_aea_40.py`.

The two new harness tests report `blocked-on AEA-30, AEA-51` (skipped). They are red for the right reason.

### Part A — built; the reference for reviewers and for any fix after the merge

Part A is built at `d7fb642` exactly as the first plan's Steps A1–A6 said. Change it only when a test goes red after
Step 0. The invariants a fix must keep:

1. One demo-clock reading per turn (`now`). It is used for `received_at`, `TurnContext.now`, the stored message `at`
   and `settled_for`.
2. Admission: `threading.BoundedSemaphore(limits.admission.max_in_flight)`, acquired non-blocking before anything
   else. It is released in `finally`.
3. Rejections (BUSY, SPEND_CAP_REACHED, RATE_LIMITED) share one `_reject`:
   - one write transaction, `begin`, then `finish(TurnRecord(status="failed", trace=_degraded_trace(reason), …))`;
   - no customer message, no outcome change, no model;
   - the same `turn_id` re-runs later.
4. Transaction T1 holds `begin`, the customer message (or the reused one on a re-run), `last_customer_wall_at` (wall,
   UTC), the reopen to `open`, and, when the controller is `human`, the `customer_message` event on `case:<ref>`. It
   commits once.
5. `run_graph` runs inside `with self._trace.turn(ids) as span:` with **no** unit of work open. Any `Exception` →
   `failed` + `_degraded_trace("model_error")` + a `FailureOfferBlock` (person key), logged as a `turn_error` record
   with ids and the exception class name only.
6. A `DEADLINE` halt → `failed`, trace `degraded_handoff` / `timeout`, plus the TURN_TIMEOUT notice
   (`try_again`, `talk_to_person`, `retry_turn_id` = this turn). `settled` is re-read from the DB.
7. Transaction T2 holds:
   - the assistant message, for completed turns only;
   - the check events;
   - `finish(TurnRecord(…, trace_id=span.trace_id, trace_export=trace.export_status(span), response=<json>))`;
   - `next_outcome` → `set_outcome`.

   If T2 fails, a fresh transaction finishes the row `failed`, then re-raises.
8. A stored body that does not parse as `TurnResponse` (e.g. a CON-4 `turn_id` reused on CON-2) answers 409
   `TURN_IN_PROGRESS`.

**Must not:**

- read or import `ConversationState`;
- keep a list of past messages;
- pass `intake` anywhere but `TurnContext.intake`;
- log `str(exc)`, the payload or `cmd`;
- write SQL;
- import `sqlite3`, `meridian.web.*` or `meridian.agent.*`.

### Part B — sessions and history

#### Step B1 — `services/session.py`: types and `open`

Write the module docstring, one paragraph: CON-1 conversations; one write transaction for the row and the greeting; a
read-only history rebuild; never imports `agent/` or `web/`. Then define §4.6's `services/session.py` block exactly,
with the imports:

- `ASSISTANT_SPEAKER`, `SettledViewFn`, `ThreadNotOpen`, `TurnResponse` from `meridian.services.turn`;
- `PersonRequestOutcome` from `meridian.services.person_request`;
- `ClockView`, `StaffingView` from `meridian.domain.views`.

Module-level helpers:

- `_utc_now() -> datetime` returns `datetime.now(UTC)`.
- `_THREAD_ID: Final = TypeAdapter(ThreadId)`.

The constructor stores every argument. It builds `self._limits_view = ChatLimits(turn_deadline_ms=
limits.turn.turn_deadline_ms, still_working_after_ms=limits.turn.still_working_after_ms, browser_give_up_after_ms=
limits.turn.browser_give_up_after_ms, max_message_chars=limits.turn.max_message_chars)`, with no literals.

`open(session, *, run_tag, run_id, request_id)`, in this order. Each step names the invariant it protects:

1. `now = self._demo_clock.now()`, then `clock = self._demo.clock_view()`, then `staffing = self._demo.staffing()`.
   - *This order is binding:* `test_register_chat` expects "not bound: demo_service" when only the clock is bound.
   - All three are read before the write transaction.
2. `thread_id = _THREAD_ID.validate_python(str(uuid.uuid4()))`; `text = render(TextId.GREETING)`.
3. **One** write transaction, `with self._uow(write=True) as tx:`
   - `tx.core.conversations.insert(ConversationRow(thread_id=thread_id, demo_session=str(session.session_id),
     run_tag=run_tag, run_id=run_id, agent_version=self._agent_version, started_at=now,
     started_wall_at=self._wall_clock(), staffing_at_start=staffing.mode, outcome="open",
     controller=Controller(kind="ai"), live_state="not_live"))`
   - `greeting_id = tx.core.messages.append(thread_id, "assistant", text, now)` (no `turn_id`, no `kind`)
   - `settled = tx.core.settled_for(thread_id, now)`; `identity = tx.core.reads.identity_state(thread_id)`;
     `last = tx.core.events.latest_id(thread_stream(thread_id))`
   - `tx.commit()`

   *Invariant:* both rows commit together, or neither does (CAS-38; `test_open_is_one_transaction`). Write no turn row,
   no event, no lookup, and call no model.
4. Return `ChatOpened(thread_id=thread_id, greeting_message_id=greeting_id, greeting_text=text, greeting_at=now,
   clock=clock, staffing=staffing, controller=Controller(kind="ai"), settled=self._settled_view(settled, identity,
   Controller(kind="ai")), limits=self._limits_view, last_event_id=last)`. `request_id` is accepted for the
   signature only; do not log it.

**Check:** `uv run pytest tests/services/test_session.py -q -k open`.

#### Step B2 — display texts (AC-19)

`_option_labels(blocks: Iterable[ReplyBlock]) -> dict[str, dict[str, str]]`: for each block where
`getattr(block, "card_id", None)` is a `str` and `getattr(block, "options", None)` is a tuple, set
`labels[card_id] = {o.option: o.label for o in options}`.

`_customer_text(msg: MessageRow, labels: Mapping[str, Mapping[str, str]]) -> str`, by `msg.kind`:

| `msg.kind` | Text |
|---|---|
| `"code"` | `render(TextId.HISTORY_CODE_ENTERED)` |
| `"form"` | `render(TextId.HISTORY_DETAILS_SENT)` |
| `"choice"` | `labels.get(msg.card_id or "", {}).get(msg.choice_option or "")`; if that is `None`, then `msg.choice_option or msg.text` |
| anything else | `msg.text` |

*Invariant:* stored `messages` rows are never changed; only the history text differs (AC-8 still holds).

#### Step B3 — `thread(thread_id)`: one read-only unit of work, then a pure merge

**Read.** First `now = self._demo_clock.now()`. Then, inside `with self._uow() as tx:` (read-only):

- `conv = tx.core.conversations.lookup(str(thread_id))`. If it is not a `ConversationRow`, `raise ThreadNotOpen()`.
- `messages = tx.core.messages.all_for_thread(thread_id)` and `turns = tx.core.turns.for_thread(thread_id)`.
- `events = tx.core.events.after(thread_stream(thread_id), 0)` and
  `last_event_id = tx.core.events.latest_id(thread_stream(thread_id))`.
- `case_rows = [row for case in tx.cases.cases.list_for_thread(thread_id) for row in
  tx.core.events.after(case_stream(case.case_ref), 0) if row.type == "customer_message"]`.
- `settled = tx.core.settled_for(thread_id, now)` and `identity = tx.core.reads.identity_state(thread_id)`.

After the block: `clock = self._demo.clock_view()` and `staffing = self._demo.staffing()`.

**Parse stored replies once.**

- `replies: dict[str, tuple[ReplyBlock, ...]]`: for each `TurnRow` with `status == "completed"` and a non-empty
  `response`, try `TurnResponse.model_validate_json(row.response).blocks`. On a `ValueError` (pydantic's
  `ValidationError` subclasses it), try `PersonRequestOutcome.model_validate_json(row.response)` and store
  `(outcome.block,)` under `con4[str(row.turn_id)]`. On a second `ValueError`, store nothing.
- `labels = _option_labels(b for blocks in replies.values() for b in blocks)`.

**Turn spine**, in this order; each item is `(entry, at, anchor)`:

1. **Greeting.** The lowest-id message with `role == "assistant"` and `turn_id is None` gives
   `HistoryEntry(turn_id=GREETING_TURN_ID, speaker_kind="assistant", speaker_name=None, at=msg.at, text=None,
   blocks=(greeting_block(msg.text, msg.at),))`, anchor `None`. Other assistant rows without a `turn_id` are ignored.
2. **Each `TurnRow` in `sequence` order.** Let `cust` be the first customer message whose `turn_id` equals the row's.
   - **`cust` exists.** Emit a customer entry: `turn_id=str(row.turn_id)`, `speaker_kind="customer"`,
     `speaker_name=None`, `at=cust.at`, `text=_customer_text(cust, labels)`, `blocks=()`,
     `anchor=case_anchor.get(cust.id)`. Then, only when `str(row.turn_id) in replies`, emit an assistant entry:
     `blocks=replies[...]`, `at` = the `at` of the assistant message with this `turn_id` if one exists, else
     `row.replied_at or row.received_at`, `text=None`, `speaker_name=None`, anchor `None`.
   - **No `cust`, and `str(row.turn_id) in con4`** (a CON-4 row, AC-17). Emit a customer entry with
     `text=render(TextId.PERSON_REQUEST_LABEL)` and `at=row.received_at`. Then an assistant entry with
     `blocks=con4[...]` and `at=row.replied_at or row.received_at`. Both have `turn_id=str(row.turn_id)`.
   - **Anything else** (a rejected turn with no message) emits nothing.

**Case anchors.** For each `row` in `case_rows`, read `row.payload["message"]["message_id"]` defensively: skip the row
unless the payload is a dict holding a dict with a `str` `message_id` of digits. Then set
`case_anchor[int(message_id)] = row.id`. This puts customer lines typed during a takeover after "Riley has joined".

**Event spine** (items `(entry, at, key)`):

- For each thread event with `row.type in EVENT_LINE_TYPES` and a `str` `payload["line"]`: an entry with
  `turn_id=f"evt-{row.id}"`, `speaker_kind="event"`, `speaker_name=None`, `text=payload["line"]`, `blocks=()`,
  `at=row.at`, key `row.id`.
- `shift_ended`: an entry with `turn_id=f"evt-{row.id}"`, `speaker_kind="assistant"`, `speaker_name=None`, `text=None`,
  `blocks=(HandoffBlock.model_validate(row.payload["handoff"]),)`, `at=row.at`, key `row.id`.
- `staff_message` adds no entry. It records `staff_anchor[int(str(row.payload["message_id"]))] = row.id`.
- Every message with `role == "representative"`: an entry with `turn_id=f"msg-{msg.id}"`,
  `speaker_kind="representative"`, `speaker_name=STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name`, `text=msg.text`,
  `blocks=()`, `at=msg.at`, key `staff_anchor.get(msg.id, sys.maxsize)`, tie-broken by `msg.id`.
- Every other type (`clock_changed`, `demo_reset`, `controller_changed`, unknown) adds nothing.

**Merge.** It is deterministic. The invariant is "creation order wherever the rows can tell it".

1. Sort the event spine by `(key, tie)`, where `tie` is the event id or the message id.
2. Walk the turn spine. Before appending an item whose `anchor is not None`, append every remaining event item whose
   `key < anchor`. Then append the turn item.
3. Append the remaining event items.
4. Run `merged.sort(key=lambda item: item.at)`. Python's sort is stable, so equal `at` values keep the merge order.

**Return** `ThreadHistory(thread_id=thread_id, state="closed" if conv.live_state == "closed" else "open",
entries=tuple(...), settled=self._settled_view(settled, identity, conv.controller), clock=clock, staffing=staffing,
last_event_id=last_event_id)`.

*Worked check, AC-18.* Every `at` is the same instant.

- The turn spine is: greeting, customer, reply, "Talk to a person", handoff block.
- The event spine is: joined (key 1), paused (2), Riley (key 3, from its `staff_message`), resumed (4), staffing (5).
- There are no anchors, so the result is the turn spine, then the events in key order. That is AC-18's order.

*Worked check, AC-16.* Each row is 1 s apart, so the stable sort by `at` gives the asserted order.

**Must not:**

- read `ConversationState`;
- rebuild card `answered` (AEA-40-3 is out of scope);
- show a failed or running turn's reply;
- emit an entry for a `staff_message` event;
- write anything.

**Check:** `uv run pytest tests/services/test_session.py -q`.

#### Step B4 — routes and schemas (Part B)

Add §4.6's four models to `web/schemas/chat.py`, with docstrings naming the OpenAPI schema each one mirrors. Add to
`web/routes/chat.py`, as thin sync `def`s:

```python
def start_chat_session(
    ctx: RequestContext = Depends(get_request_context),          # noqa: B008
    session: LoginSession = Depends(get_login_session),          # noqa: B008
    sessions: SessionService = Depends(get_session_service),     # noqa: B008
) -> JSONResponse:
    opened = sessions.open(session, run_tag=ctx.run_tag, run_id=ctx.run_id, request_id=ctx.request_id)
    body = StartSessionResponse(
        thread_id=opened.thread_id,
        greeting=greeting_block(opened.greeting_text, opened.greeting_at),
        demo_clock=opened.clock, staffing=opened.staffing,
        controller=ChatController(kind=opened.controller.kind, display_name=opened.controller.representative_name),
        settled=opened.settled,
        events=EventsRef(url=f"/api/chat/sessions/{opened.thread_id}/events", last_event_id=opened.last_event_id),
        limits=opened.limits,
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=201)


def get_chat_thread(
    owned: ThreadId = Depends(owned_thread),                     # noqa: B008
    sessions: SessionService = Depends(get_session_service),     # noqa: B008
) -> JSONResponse:
    try:
        history = sessions.thread(owned)
    except ThreadNotOpen:
        raise ApiProblem(404, ApiErrorCode.SESSION_NOT_FOUND) from None
    turns = tuple(
        ChatThreadTurn(turn_id=e.turn_id, speaker=Speaker(kind=e.speaker_kind, display_name=e.speaker_name),
                       at=e.at, text=e.text, blocks=e.blocks)
        for e in history.entries
    )
    body = ChatThread(thread_id=history.thread_id, state=history.state, turns=turns, settled=history.settled,
                      demo_clock=history.clock, staffing=history.staffing, last_event_id=history.last_event_id)
    return JSONResponse(body.model_dump(mode="json"))
```

In `build_router()`, add these **before** the `submitTurn` line:

- `router.add_api_route("/api/chat/sessions", start_chat_session, methods=["POST"], operation_id="startChatSession",
  status_code=201, response_model=None)`
- `router.add_api_route("/api/chat/sessions/{thread_id}", get_chat_thread, methods=["GET"],
  operation_id="getChatThread", response_model=None)`

These path templates must equal `OPERATIONS_BY_ROUTE`'s keys in `web/middleware.py`. Update the module docstrings of
both files: drop "the CON-1 routes join when …".

**Check:** `uv run ruff check src/meridian/web/routes/chat.py src/meridian/web/schemas/chat.py
src/meridian/services/session.py`.

#### Step H — the `register_chat` hunk (own function only; module imports unchanged)

Replace the docstring with:

> AEA-40 customer API: SessionService, TurnService, CON-1 and CON-2 routes, the start-up turn sweep (web.md §9, §14).
>
> Provides deps.SESSION_SERVICE and deps.TURN_SERVICE and includes the chat router once per app. Reads
> Key("demo_clock") and deps.DEMO_SERVICE (AEA-30), deps.REPLY_COMPOSER and Key("run_graph") (AEA-51) only when a
> request needs them, so the app builds before those tickets bind them; until then a call raises
> RuntimeError("not bound: <key>"). On start it fails every turn still `running` and logs one turn_sweep count line
> (R-W-4). An app that create_app did not build has no web shell, so this does nothing.

Body changes to the built hunk (keep `lazy`, `_DemoClock`, `settled_view`, `run_graph`, the `TURN_SERVICE` provider
and `sweep`, exactly as built):

1. Add `from meridian.services.session import SessionService` and add `DEMO_SERVICE`, `SESSION_SERVICE` to the
   `meridian.web.deps` import inside the function. Both imports stay inside the function body.
2. After `_DemoClock`, add:

   ```python
   class _Demo:
       def staffing(self) -> Any:
           return lazy(DEMO_SERVICE).staffing()

       def clock_view(self) -> Any:
           return lazy(DEMO_SERVICE).clock_view()
   ```
3. After the `TURN_SERVICE` provider, add:

   ```python
   container.provide(
       SESSION_SERVICE,
       lambda c: SessionService(
           c.get(UOW_FACTORY), _DemoClock(), _Demo(), limits, settled_view, settings.agent_version,
           wall_clock=c.get(WALL_CLOCK),
       ),
   )
   ```
4. Replace the bare `app.include_router(build_router())` with §4.4's guard, using the flag name
   `chat_routes_included`.
5. Keep `container.on_start(sweep)`. *Invariant:* the sweep runs once per container build, before the first request,
   with no age test (R-W-4).

**Check:** `uv run pytest tests/unit/web tests/unit/test_import_direction.py tests/api/test_app.py -q`. All must pass,
including `test_container.py::test_every_register_stub_present` and both `test_register_chat.py` tests.

#### Step B5 — the rest of Part B's tests and the journeys

Run each of these and make it green, fixing source only:

- `tests/api/test_chat.py`, `tests/api/test_chat_capture.py`, `tests/api/test_contract_cases_chat.py`;
- `tests/journeys/j1/test_aea_40.py` and `tests/journeys/j9/test_aea_40.py`.

The two harness tests from Step T are expected to be **skipped** with `blocked-on AEA-30, AEA-51: …`. Then run AEA-59's
runner for the three operations (§7, gate 7). Expected: the format and completeness tests pass, and every chat drive
either passes or is skipped `not bound: demo_clock` (or `demo_service` / `reply_composer`). Nothing else may skip or
fail.

#### Step D — context and evidence (AC-23), in a separate docs commit

1. **`.claude/reference/area-map.md`, A8 row, last cell.** Replace the Part A text from Step 0.3 with `; AEA-40
   (<code sha>): services/{turn,session}.py, web/routes/chat.py, web/schemas/chat.py, register_chat hunk built`.
   Change nothing else.
2. **`.claude/state/icm-progress.md`.** Replace the AEA-40 Part A row with `| Routes verified against code and tests |
   provisional | 2026-10-21: area map A8 → services/{turn,session}.py, web/routes/chat.py checked against
   tests/services/test_{turn,session}.py, tests/api/test_chat*.py, tests/unit/web/test_register_chat.py (AEA-40,
   <code sha>; <n> pass) | Integrated level when AEA-30 and AEA-51 land |`. Keep it to 400 characters or fewer.
3. **`docs/design/code-design.md`.** Replace the AEA-40 Part A `**Built:**` line with `**Built:**
   \`services/{turn,session}.py\`, \`web/routes/chat.py\`, \`web/schemas/chat.py\`, the \`register_chat\` hunk
   (AEA-40, \`<code sha>\`).`
4. **Journey record.** Run `uv run pytest -m journey tests/journeys/j1/test_aea_40.py tests/journeys/j9/test_aea_40.py
   -rs --journey-record=AEA-40`. It rewrites `docs/testing/journeys/2026-10-21-AEA-40.md` (use today's Chicago date
   if it differs). Then append these lines to its *Remaining limitations* field if the generator leaves the field
   empty:
   - no real graph (AEA-51);
   - TURN_TIMEOUT and BUSY not yet through the real server (§8 R-6);
   - history order exact only where §5 B3's anchors reach (§8 R-1);
   - a retried failed turn sums spend rows of every attempt.

   The *Blocked by* field must read "AEA-30, AEA-51".
5. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL.

#### Step E — commits (explicit paths; never `git add -A`; never push; never merge into `main`)

- **Commit 1 (code).** `git add src/meridian/services/session.py src/meridian/web/routes/chat.py
  src/meridian/web/schemas/chat.py src/meridian/web/container.py`, plus `src/meridian/services/turn.py` only if Step 0.5
  changed it. Message: `feat(chat): CON-1 SessionService and routes; register_chat binds both services (AEA-40 Part B)`.
- **Commit 2 (docs).** `git add .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md
  docs/testing/journeys/2026-10-21-AEA-40.md`. Message: `docs(AEA-40): journey record and context rows for Part B`.

Every message ends with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Never touch a frozen test
file. Report the gate results (§7.3) with counts.

---

## 6. Data and fixtures (synthetic only; built at run time; all already in the frozen helpers)

| Need | Source | Built how |
|---|---|---|
| Working DB | issued scheduling DB copy | `temp_sqlite()` (`tests/fixtures/sqlite.py`). The issued file is never written |
| Login sessions | — | `FakeSessionStore().issue()`; two tokens for the foreign-thread 404 |
| Settings | — | `make_settings(tmp_path, eval_key=rand_word(18, "ek"))`: generated secrets, nothing from `.env` |
| Demo clock | worked-pairs instant | `FixedClock()` (`WORKED_PAIRS_NOW`, 2026-10-16 10:00 America/Chicago); `.advanced(timedelta)` |
| Wall clock | — | `WALL_NOW = 2026-10-21 15:30 UTC` (`chat_doubles.fixed_wall`) |
| `DemoReads` double | OpenAPI `STARTED` example values | `FakeDemo`: `ClockView(now=WORKED_PAIRS_NOW, label="Fri Oct 16, 2026 · 10:00 am", date_label="Fri Oct 16, 2026 (demo date)")`, `StaffingView(mode="nobody_online", label="Nobody online", banner=None)` |
| `settled_view` double | graph-core §13 | `simple_settled_view` / `FakeComposer` |
| `SpendGuard` double | — | `FakeSpendGuard(allow)` |
| `run_graph` doubles | graph-core §2 | `ScriptedRunGraph`, `BlockingRunGraph`, `RaisingRunGraph`, `DeadlineRunGraph` |
| Code, card, phone | redaction rules (AEA-04) | `synthetic(seed=4040)`. Journey T1 uses `random.Random(4041)`. Never a literal |
| CON-4 stored outcome | web.md §8 (`PersonRequestOutcome` JSON) | `seed_person_request_turn` (`chat_storage.py` after Step T) |
| Takeover rows | staff.md §5, §7 (AEA-46's real shapes) | `seed_takeover`, `seed_case` |
| Running turn rows (AC-12) | — | `begin()` at `now - 66 s` and `now - 10 s`, plus one completed |
| Journey harness | AEA-57 | the `journey` fixture: real app, disposable DB copy, scripted adapter, socket guard |

---

## 7. Checks

### 7.1 Tests

The frozen tests are §3.1 and §3.2 (manifest `61d5bd8`, amended in Step T). The implementer makes them pass and never
edits them. This is a `risk::security` slice: the test-writer owns every test file. The implementer writes no tests.

### 7.2 Existing tests that must stay green

- `tests/unit/web/test_container.py` (the stub list, and `register_chat`'s docstring keeps "AEA-40" without
  "No-op until");
- `tests/api/test_app.py` (the full app builds every hunk; its `submitTurn` probe route is registered first and still
  wins; two lifespans on one app);
- `tests/unit/test_import_direction.py`, `tests/unit/web/*`, `tests/api/test_openapi_sets.py`;
- `tests/api/test_handoff_*.py` (AEA-42 shares `owned_thread` and the turn rows);
- `tests/services/test_person_request.py`;
- `tests/journeys/j1/test_aea_57.py` (its CHAT steps stay *blocked* on AEA-30 and AEA-51, never *failed*);
- `tests/journeys/j7/*`;
- `tests/contract/test_openapi_server.py`.

### 7.3 Gates (cheapest first; stop at the first red)

The affected set is `tests/services tests/api tests/unit/web tests/unit/test_import_direction.py tests/contract`, plus
every file `grep -rl "services.turn\|services.session\|routes.chat\|schemas.chat\|register_chat\|chat_doubles\|chat_storage" tests/`
lists. `web/container.py` changes in one hunk only; there is no shared fixture, settings or lockfile change, so **no
full suite**.

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/services/turn.py src/meridian/services/session.py src/meridian/web/routes/chat.py src/meridian/web/schemas/chat.py src/meridian/web/container.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check <same paths>` | `… files already formatted` |
| 3 | Type check | `uv run mypy` | `Success: no issues found` (strict; `src`, `tests`, `eval`) |
| 4 | Forbidden reads | `grep -n "ConversationState\|meridian.agent\|meridian.web\|sqlite3" src/meridian/services/turn.py src/meridian/services/session.py` | no output |
| 5 | Affected tests | `uv run --with pytest-xdist pytest -n 2 tests/services tests/api tests/unit/web tests/unit/test_import_direction.py -q` (iterate on single files without `-n`) | all passed; the only skips are journey/harness skips naming AEA-30/AEA-51 |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main`, then `uv run pytest -m journey tests/journeys/j1/test_aea_40.py tests/journeys/j9/test_aea_40.py -rs --journey-record=AEA-40` | the mock tests pass; the harness tests are skipped `blocked-on AEA-30, AEA-51`; nothing fails |
| 7 | Contract cases (AC-22) | `uv run pytest tests/contract/test_openapi_server.py -k "startChatSession or getChatThread or submitTurn" -rs` | passes, or skips with `not bound: demo_clock` / `demo_service` / `reply_composer` only. The `CONTRACT_STRICT=1` form is the wave-merge gate and stays red until AEA-30/AEA-51 land; record that, do not chase it |
| 8 | Diff scope | `git diff --name-only main...HEAD` | only §2.1 files |
| 9 | Context | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL |

Paste the result of every gate into the report, with counts. Never call a paid model: nothing here is marked `live`, and
the journey harness blocks outbound sockets.

### 7.4 Journey record

`--journey-record=AEA-40` writes it (Step D.4). It must read as follows:

- **Level:** `mock-tested` for the mock tests. The harness tests are blocked.
- **Blocked by:** AEA-30, AEA-51 (and §8 R-6 for TURN_TIMEOUT/BUSY at integrated level).
- **Journeys that will exercise this code:** J-1 and J-9 at `integrated with a scripted model`, J-7 reload (AEA-52),
  and AEA-57's J-1 steps 4–7.

---

## 8. Risks and requests

| # | Risk / request | What to do |
|---|---|---|
| R-1 | **History order under the frozen demo clock.** Messages, events and turns share no ordering column. Step B3 is exact for AC-16…AC-18, for CON-4 followed by a takeover, and for customer lines typed during a takeover. It can misplace two cases: a demo-wide `staffing_changed` line written mid-conversation, and a customer line typed after a hand back (it shows before `ai_resumed`). | **Request to the orchestrator (non-blocking):** an AEA-10 follow-up that adds one insertion-order value (a UTC `wall_at` with sub-second precision, written by the repositories) to `messages`, `events` and `turns`. B3's sort key then becomes `(at, wall_at)`. AEA-52's J-7 reload is where it would show. |
| R-2 | **Step T is a test-writer dispatch.** The implementer cannot edit frozen files. | Orchestrator: dispatch `test-writer-agent` with Step T before (or in parallel with) the implementer's Steps B1–H. Step B5's journey check needs T1/T2. Everything else does not. |
| R-3 | `SessionService` takes a keyword-only `wall_clock` (default: UTC now) beyond web.md §14's signature, so `started_wall_at` is written. AEA-32's zero-traffic alert reads it. The change is additive. | Record it as a deviation on issue #40 and in the build ledger. No decision is needed. |
| R-4 | **AEA-57's J-1 step "4 start session"** reads `SELECT demo_now FROM demo_state WHERE id = 1`. No row exists until AEA-30 writes one (AEA-30 plan R-15). The step is blocked today on AEA-30/AEA-51. | Not this ticket's file or table. `SessionService.open` reads the clock through `DemoClock` and never writes `demo_state`. Orchestrator: route it to AEA-30 (seed the row at boot without overwriting) or to an AEA-57 follow-up. |
| R-5 | `web/logging.py`'s allow-list has no `turn_sweep` or `turn_error` record, so the formatter writes them as `{"record": "log", "length": N}`. That is safe, but the count is not readable in production logs. | **Request:** an AEA-23 follow-up that adds `"turn_sweep": {"record", "count"}` and `"turn_error": {"record", "request_id", "turn_id", "thread_id", "error_kind"}`. Tests read the `LogRecord` attribute, so nothing waits on it. |
| R-6 | **TURN_TIMEOUT and BUSY through the real server.** The scripted adapter cannot hold a provider call, so a DEADLINE halt or 30 in-flight turns cannot be produced through the real server. | **Request:** an AEA-57 follow-up: a `ScriptEntry` that blocks until the test releases it (or a monotonic-clock override in `ContainerOverrides`). Until then those two J-9 steps are mock-tested and the record says so (Step T2's skip reason). |
| R-7 | A CON-4 `turn_id` reused on CON-2 has a stored body that is not a `TurnResponse`. `begin` also reports another thread's `turn_id` as `running`. | Both answer 409 `TURN_IN_PROGRESS` (built). Never a 500, never another thread's reply. |
| R-8 | Reopening an `abandoned` conversation keeps its old `ended_wall_at` (`set_outcome` uses `COALESCE`). | A note for AEA-53 (M-18 reads `outcome`). No change here. |
| R-9 | A retried failed turn sums the spend rows of every attempt of that `turn_id`. | Intended (cost per `turn_id`); stated in the journey record. |
| R-10 | Collision: `web/container.py` is shared. | Edit only `register_chat`'s body and docstring; the module-level import block never changes. |
| R-11 | AEA-40-3 (card `answered` after a reload) contradicts web.md §14. | Not built here; it stays with the orchestrator. |
| R-12 | `test_turn.py` (684 lines) and `test_chat.py` (588 lines) exceed the 500-line test cap, and every test in them is named by an AC or by this plan. | Accepted for this ticket: moving a test would break a node id the signed ticket cites. Step T says so in its commit message. A reviewer finding on this cites this row. |
| R-13 | `services/turn.py` is 563 lines (service target 400, hard cap 600). | Do not grow it. Part B goes in `session.py`. If a post-merge fix would cross 600 lines, stop and report instead of splitting on your own. |
| R-14 | **An implementer run is already in progress in the AEA-40 worktree** (uncommitted `session.py` draft, area-map A9 fix, 16:46 UTC). A second implementer started on the same worktree would overwrite it. | Orchestrator: resume or wait for that run rather than dispatching a parallel one; the next implementer continues from the draft (Step 0.2). The test-writer's Step T touches only test paths, so it may run alongside. |

---

## 9. Readiness

- **READY.** Every import Part A and Part B need is on `main` at `2ec19ad` (unchanged from `b559c75` for this
  ticket's surfaces). Sibling services that are not merged
  (AEA-30's demo clock and DemoService, AEA-51's reply composer and graph) are called through injection and doubled in
  tests, so they are **not** blockers.
- **Order:**
  1. Step 0 is done (`6891c3c`); the implementer only runs its checks;
  2. Step T (test-writer, not yet run) alongside B1–H (implementer, B1–B3 in progress as an uncommitted draft);
  3. B5, D, E.
- **Record-level only, not merge blockers:**
  - AC-15's integrated level waits on AEA-30 and AEA-51, plus §8 R-6 for TURN_TIMEOUT/BUSY.
  - AC-22's `CONTRACT_STRICT=1` run waits on AEA-30 and AEA-51.
- **No NEEDS-DECISION.** No signed contract (OpenAPI, `UI_CONTRACTS.md`) changes. D-8 (start fresh after signing in
  again) is honoured by `owned_thread`'s 404. Every other choice above is engineering and is recorded.

## Gates

None human, paid or live. Because of `risk::security`, the frozen tests come first (amended in Step T), and the
`security-privacy-agent` reads this diff at the wave merge. Its focus:

- code-payload handling;
- STORE redaction before storage;
- the history display texts, which never echo stored values;
- thread ownership;
- untrusted input;
- logs.
