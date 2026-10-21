## [AEA-57] journey harness: real server + disposable DB + scripted model

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

> **US-28:** "As a **reviewer**, I need to sign in once with the demo login given in the README and then switch between
> acting as the customer and acting as a representative, supervisor or business owner in one click from any screen …"
> Acceptance: "nothing except the login and `/healthz` answers without the login … an expired session returns to the
> login." **US-1:** "the chat [says] plainly that it is Meridian's automated assistant and … the date it is working from."

**Why this ticket exists** (rule `.claude/rules/integrated-journeys.md`, the Riverside lesson): every component test can
be green while a reviewer still cannot sign in, open a chat and see the conversation remembered. This ticket lands the
**journey harness** and the **first journey, J-1**, at the API level: the real FastAPI app, the real container, the real
middleware and guards, a disposable copy of the issued database, and a scripted model at the provider boundary. Every
later build ticket extends a journey with it, and the merge gate runs it (`build-loop-test-scope.md`, *AEA addition*).

**1. The harness, `tests/journeys/support/`** (this ticket's alone; later tickets never edit it, slice plan §3 row
`tests/journeys/`; a missing helper is a follow-up on this ticket, merged first). Six parts, exposed as pytest fixtures:

- **Environment and disposable DB.** Per run: a fresh temporary `MERIDIAN_DATA_DIR`, following `temp_sqlite()`'s pattern
  (temporary location, removed afterwards; AEA-10, cases.md §1.5) but filled by the app's **own** first boot, which copies
  the issued `docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite` into `meridian.sqlite` when it
  is missing (cases.md §1.4; DO-1 §9), so the issued rows and every `schema/*.sql` come from production code. The issued
  file is opened read-only and its SHA-256 is checked before and after (rule §2 *Output*). Settings come from the
  environment the same way the deployed app gets them (graph-core.md §12 env names): a per-run synthetic demo pair for
  `MERIDIAN_DEMO_USERNAME` / `MERIDIAN_DEMO_PASSWORD` and a per-run random `MERIDIAN_SESSION_SECRET` (generated, never
  written to a file or the record), `MERIDIAN_EVAL_KEY` unset (so every request is `run_tag = "live"`, web.md §4), the four
  `LANGFUSE_*` unset (so the container picks `NullTraceSink`, models.md §7), `MERIDIAN_COOKIE_SECURE=false`,
  `MERIDIAN_REQUIRE_FRONTEND=false` and `MERIDIAN_WEB_DIST_DIR` pointed at an empty temp path, so J-1 stays at the API level
  even when a local `apps/web/dist` exists (the browser level is AEA-58's). Provider key fields get a fixed non-secret
  placeholder; no request leaves loopback (a socket guard fails any non-loopback connection).
- **Scripted model adapter** (rule §3.1: "a deterministic scripted model adapter … sits at the provider boundary, so
  parsers run, and a deployed configuration can't select it"). One test-only class implementing `ChoiceModel`,
  `StructuredModel` and `ToolCallingModel` (DO-4 §12, signatures unchanged) with the read-only `provider` attribute
  (models.md §1, cross-topic 2) and `model` equal to the configured `RoleSpec.model`. A journey script gives it the **raw**
  output per role and call, in order. It applies the checks the real adapters apply (models.md §3): a structured answer is
  validated against `StructuredRequest.output_model`, a choice against each `ChoiceField.options`, a tool step's arguments
  parsed with `ToolCall.args = None` when unparseable; a mismatch comes back as `INVALID_OUTPUT`, never an exception, so a
  script that disagrees with the production schema fails the journey exactly as production would. Every `Attempt` carries
  a `ProviderCall` (no `role`, no `attempt`; `cost_usd = 0.0`, `cost_source = "price_table"`; models.md §1, MOD-1,
  MC-28), so the real gateway, ledger and trace sink run on it. It records every request so a journey can assert what the
  model saw. It may reuse AEA-11's `tests/fakes/` doubles internally; it never stands in above the three ports (the
  gateway, services, graph and DB are real).
- **Server launcher.** `create_app(settings, overrides=ContainerOverrides(choice=…, structured=…, tools=…))` with the
  scripted adapter in all three role maps (AEA-23, `web/app.py`, web.md §15, R-W-8; its lifespan builds the
  `web/container.py` container once with `(settings, overrides)`, AEA-01, and only `register_graph` reads `overrides`).
  The `overrides` argument is the launcher's own option: AEA-61 launches with none, so the real adapters run
  (web.md §15). Served by uvicorn in a background thread on `127.0.0.1` with an OS-assigned ephemeral port (port 0). Ready when
  uvicorn reports started and the lifespan has run, not on `/healthz` (that answers from AEA-32's heartbeat). Teardown stops
  the server, joins the thread and lets the lifespan close the container once.
- **Journey client and login helper.** An `httpx` client on the launcher's base URL with cookies on. **Every** response a
  journey step receives goes through AEA-23's `assert_response_matches(response, operation_id)` (web.md §13; rule §3.3:
  "every actual server response a journey receives is validated … using the one check AEA-23 owns"); each step names its
  operationId. `login()` posts the run's demo pair to `login` (CON-22) and returns the signed-in client.
- **DB-state reader.** A read-only connection (`mode=ro`) to the working copy for persisted-effect assertions (rule §3.2:
  "a 2xx response alone proves nothing"), opened per assertion, never holding a transaction across a request.
- **Evidence-record writer.** With a record option, the run writes `docs/testing/journeys/YYYY-MM-DD-<scope>.md` with the
  nine fields of rule §4 (Claim, Level, Tested revision, Environment, Command, Result, Evidence location, Remaining
  limitations, Blocked by). Without the option it writes nothing, so ordinary runs leave the tree clean. Never the demo
  pair, the session secret, a cookie value or real personal data (rule §4).
- **Blocked steps are named, never hidden** (rule §3.6). A provider not yet bound raises `RuntimeError("not bound:
  <name>")` at call time (web.md §4). The harness reports such a step as **blocked** with the owning ticket (from web.md
  §4's provider list) and the record's *Blocked by* names it. A blocked step never counts as a pass. A strict option turns
  every blocked step into a failure; the wave-merge and pre-deploy runs use it.

**2. Journey J-1** (slice plan §0a map: "Login → start session → one turn → refresh/resume the same thread; guards
redirect when signed out"), `tests/journeys/j1/test_aea_57.py`, asserting what the client sees **and** what was stored:

| Step | Request (operationId) | The client sees | Stored (DB reader) |
|---|---|---|---|
| 1 signed out | `GET /api/chat/sessions/<new uuid>` (`getChatThread`); `GET /staff/queue` (a page) | 401 `UNAUTHENTICATED`, `details.reason: "none"`; 303 to `/login?return_to=%2Fstaff%2Fqueue&reason=none` (web.md §6, WEB-28) | no `staff_sessions` row |
| 2 wrong login | `login` with the right username and a wrong password | 401 `LOGIN_FAILED` (web.md §2, WEB-10) | no `staff_sessions` row |
| 3 login | `login` with the run's pair | 200 `LoginResponse`, `session.role: "customer"`; `Set-Cookie: mhc_session=…; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200`, no `Secure` (web.md §2) | one `staff_sessions` row, role `customer`, whose `token_hash` is not the cookie value (staff.md §3, STF-5) |
| 4 start session | `startChatSession` | 201 `StartSessionResponse`: the `policy/texts.py` greeting, the demo clock, controller `ai`, empty `settled`, `events.last_event_id: 0` (web.md §14) | one `conversations` row for this login's `session_id`, `run_tag = 'live'`, `outcome = 'open'`, the container's `agent_version`; one greeting `messages` row; `demo_state.demo_now` equals the response's clock (cases.md §1.1) |
| 5 one turn | `submitTurn` with a fresh `turn_id` and text "Hi, what can you help me with?" | 200 `TurnResponse` whose text block is the scripted responder text | the customer `messages` row (STORE-redacted text); one `turns` row, status `completed`, `gate_result` `clear`, plan mode `talk`, `outcome` `answered`, `specialists_run` empty, `server_ms`, `replied_at`, `trace_export`, `agent_version` (graph-core §2 `TurnRecord`, `TurnTrace`); one `spend_ledger` row per scripted call with the configured model and cost 0; `conversations.last_customer_wall_at` set (web.md §9) |
| 6 refresh / resume | `getChatThread`; then `submitTurn` again with step 5's `turn_id` | the thread holds the customer message and step 5's reply blocks unchanged; the resend returns the stored response byte for byte (web.md §9; OpenAPI `submitTurn`: "a finished turn returns the stored reply") | row counts unchanged by the read; still one `turns` row for that `turn_id`; the scripted adapter received no new request |
| 7 guard, both ways | a second client logs in (new session) and reads step 4's thread | 404 `SESSION_NOT_FOUND` (web.md §4 `owned_thread`), while the first client's read still answers 200 | unchanged |
| 8 validation on | `submitTurn` with a 2,001-character text (OpenAPI `TextPayload.maxLength` 2000) | 400 `VALIDATION_ERROR`; `details` never holds the rejected value | no new `messages` or `turns` row |

Step 5's script is a turn with no task (DO-4 §4): planner choices `knowledge: "no"`, `account: "none"`, `scheduling:
"none"`, `handoff: "none"`, `topic: "other"`; classifier label `normal`; a responder answer that validates against the
responder's `output_model` (DO-4 §9). If the real graph stores different decision fields for this script, the
implementer reports it as a seam finding on the issue; the expectation is never edited to match.

**3. What it sets up for later tickets.** Each later `lane::build-loop` ticket adds **one file per journey it touches**,
`tests/journeys/j<N>/test_aea_<NN>.py` (N from the slice plan §0a journey map, NN the ticket), using only the fixtures
`support/README.md` lists, and never edits `support/` or another ticket's file (slice plan §0a, §3). AEA-51 and AEA-52 run
their integration on this harness; AEA-58 adds `tests/journeys/browser/` on the same launcher with `apps/web/dist`;
AEA-61 runs the launcher **without** the scripted ports (real adapters, `live` marker, `gate::paid`).

**The commands a reviewer runs** (the `journey` marker and the affected-journeys selector are AEA-01's; option names
below are this ticket's to fix and `support/README.md` records the final spelling):
1. `uv run pytest tests/journeys/support -q` (the harness checks itself).
2. `uv run pytest -m journey tests/journeys/j1 -v --journey-record=AEA-57` (J-1; writes the record).
3. Wave merge and before deploy: `uv run pytest -m journey tests/journeys --journeys-strict` (all journeys; blocked = fail).
At a ticket merge the gate runs AEA-01's affected-journeys command, which selects `j1` when a changed module is on its path.

### Source

- Rule `.claude/rules/integrated-journeys.md` §2 (the J-BOOK example's input → process → output shape), §3 rules 1, 2, 3,
  5, 6, §4 (levels and the nine record fields), §5 (who runs what), §6 ("AEA-57 | 2 | Journey harness: real app on a
  disposable DB copy, scripted adapter at the provider boundary (a deployed config can't select it), the first API-level
  journey, the merge-gate command, the evidence template").
- Rule `.claude/rules/build-loop-test-scope.md` *AEA addition* (journeys in the merge gate; "the suite has no paid calls";
  "until AEA-57 lands the harness, there is no journey gate to run").
- Slice plan §0a (Amendment 1: the `[journey]` criterion, the `j<N>/test_aea_<NN>.py` convention, journey map row J-1,
  "Integration tickets AEA-51 / 52 run on the harness"), row AEA-57, §3 rows `tests/journeys/`, `tests/contract/`.
- stage7/web.md §2 (cookie, credential check), §4 (`RequestContext.run_tag`, providers and "not bound", `owned_thread`),
  §6 (gate order, 401 vs 303), §9 (`run_turn`, idempotent `turn_id`, turn-row sources), §10 (`request`, `auth_event`),
  §13 (`assert_response_matches`), §14 (`SessionService.open` / `thread`), §15 (`create_app`, `ContainerOverrides`;
  R-W-8). `docs/plans/7b-decisions/residuals-web.md` R-W-8.
- stage7/graph-core.md §2 (`TurnInput`, `TurnContext`, `TurnTrace`, `TurnRecord`, `GraphOutcome`), §12 (`Settings` and env
  names). stage7/models.md §1 (`ProviderCall`, `Attempt.record`), §3 (`INVALID_OUTPUT` mapping), §7 (container wiring,
  `NullTraceSink` when Langfuse is unset). DO-4 §4 (`PlannerChoices`, `DangerAssessment`), §9, §12 (ports, gateway).
- stage7/cases.md §1.1 (`conversations`, `turns`, `messages`, `spend_ledger` columns), §1.4 (first-boot copy, read-only
  issued file), §1.5 (`temp_sqlite()`); staff.md §3 (`staff_sessions`).
- stage7/data.md §5–§6 (held-out case and key files; DAT-2 open). OpenAPI operations `login`, `startChatSession`,
  `getChatThread`, `submitTurn`, `TextPayload` (read only).
- DO-6 `docs/design/observability-contract.md` rows WF-1, WF-18; DO-7 M-22…M-26, M-29. PRD R-41, R-45, R-48; US-1, US-28.
- `apps/web/package.json` and `playwright.config.ts` (read only): the UX suite runs Prism on 4019 and Vite on 5184 and signs
  in with dev-only parameters, so it counts as `mock-tested` (rule §1); the harness binds neither port.
- Checklist `PROJECT-CHECKLIST.md` §8 line "Journey harness exists and runs in the merge gate … (AEA-57)".
- **Brief check:** serves "Deploy the agent as a web application at a public URL. The interface must be interactive: a
  reviewer should be able to type questions, probe edge cases, and watch the agent escalate." (Part B §6), by proving that
  path runs; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Disposable DB, issued file untouched: each run starts the real app on a fresh temp `MERIDIAN_DATA_DIR` whose `meridian.sqlite` is made by the app's own first-boot copy (cases.md §1.4); the five issued tables match the issued file row for row; the issued file's SHA-256 is equal before and after; the temp directory is gone after teardown. Level: integrated with a scripted model (harness self-check) — verify: `tests/journeys/support/test_support.py::test_disposable_copy_and_issued_untouched` — evidence: both hashes printed equal; five row counts equal; no temp path left.
- [ ] AC-2 [invariant] The scripted adapter parses like the adapters: a schema-valid structured script returns the typed value; a choice outside its field's options, an output failing `output_model` and unparseable JSON each return `INVALID_OUTPUT` with `Attempt.record` a `ProviderCall` (cost 0.0, `price_table`) and no exception; `provider` and `model` match the configured role; every request is recorded. Level: mock-tested (the adapter alone) — verify: `test_support.py::test_scripted_model_parses_like_adapters` — evidence: the three failures listed with their kind; recorded request count per call.
- [ ] AC-3 [negative] A deployed configuration cannot select the scripted adapter: nothing under `src/meridian/` imports from `tests/`, and no `Settings` field, env name or `ModelSettings` provider literal names it (graph-core §12; DO-4 §12) — verify: `test_support.py::test_scripted_model_not_selectable_in_deploy` (import scan of `src/meridian/` and field scan of `Settings`) plus `grep -rn "tests\.journeys\|scripted" src/meridian/` — evidence: scan passes; grep prints nothing.
- [ ] AC-4 [invariant] The launcher serves the real app on `127.0.0.1`, an OS-assigned port that is never 4019 or 5184, ready on uvicorn's started flag after the lifespan ran (not `/healthz`), and on teardown the thread has stopped and the container closed once. Level: integrated with a scripted model (harness self-check) — verify: `test_support.py::test_server_thread_ephemeral_port` — evidence: host, port and close count printed; thread not alive.
- [ ] AC-5 [failure/refusal] Every journey response is checked against the signed OpenAPI with AEA-23's `assert_response_matches` (web.md §13): a documented response passes; a response whose status or body the operation does not document fails the step with the operationId and status in the message. Level: mock-tested (client hook on a throwaway app) — verify: `test_support.py::test_client_validates_every_response` — evidence: the failing assertion text quoted.
- [ ] AC-6 [invariant] The DB-state reader is read-only: it opens the working copy with `mode=ro`, a write through it raises `sqlite3.OperationalError`, and it holds no open transaction between steps — verify: `test_support.py::test_db_reader_read_only` — evidence: the error text; `in_transaction` false after each read.
- [ ] AC-7 [failure/refusal] An unbound provider is reported, never passed: a step whose provider raises `RuntimeError("not bound: …")` (web.md §4) is reported blocked with the owning ticket; the record's *Blocked by* names it; with `--journeys-strict` the same step fails. Level: mock-tested (throwaway app with one provider unbound) — verify: `test_support.py::test_unbound_provider_blocked_then_strict_fails` — evidence: pytest shows `skipped` with "blocked-on AEA-40" without the option and `failed` with it; the record line quoted.
- [ ] AC-8 [journey] **J-1 steps 1–3** (signed-out guards, wrong login, login) through the real middleware and login route give exactly the responses and stored rows in *What to build* §2's table, every response passing AC-5's check. Level: integrated with a scripted model (no model call in these steps) — verify: `tests/journeys/j1/test_aea_57.py::test_j1_guards_and_login` — evidence: status, `Location`, cookie attributes and the `staff_sessions` row printed per step.
- [ ] AC-9 [journey] **J-1 steps 4, 6 (read), 7** (start session, refresh/resume read, the other session refused while the owner still reads) give exactly the responses and stored rows in §2's table. Level: integrated with a scripted model — verify: `j1/test_aea_57.py::test_j1_session_resume_and_owner_guard` — evidence: the `conversations` and greeting `messages` rows, the 404 and the owner's 200 printed.
- [ ] AC-10 [journey] **J-1 steps 5 and 6 (resend)**: the scripted no-task turn runs through the real `TurnService`, graph, gateway and ledger and stores the `messages`, `turns`, `spend_ledger` and `conversations` effects in §2's table; the reply's text block equals the scripted responder text; resending the same `turn_id` returns the stored response byte for byte with no new model request and one `turns` row. Level: integrated with a scripted model once `run_graph` is bound; before that the steps are reported blocked on AEA-51 (AC-7), never passed — verify: `j1/test_aea_57.py::test_j1_one_turn_and_resend` — evidence: stored rows printed, adapter request count unchanged on resend, or the blocked line with its ticket.
- [ ] AC-11 [negative] Validation and secret values: step 8's 2,001-character text (a distinctive sentinel prefix) gets 400 `VALIDATION_ERROR` and is absent from the response body, from every log record captured during the run and from the working-copy file; the run's demo password, session secret and `mhc_session` value are absent from the working-copy file, every captured log record and the evidence record; no new `messages` or `turns` row follows step 8 — verify: `j1/test_aea_57.py::test_j1_rejected_and_secret_values_absent` — evidence: 0 hits per value; row counts unchanged.
- [ ] AC-12 [capture] J-1's real entry points leave their workflow records (DO-6): WF-18, an `auth_event` with outcome `rejected` (step 2) then `ok` with the opaque `session_id` (step 3), and a `request` record per call whose `request_id` equals that response's `X-Request-ID` (web.md §10); WF-1, the rows of AC-9 and AC-10 per step. Records are checked present only; redaction stays CAP-1's and CAP-10's (rule §1, "journeys don't repeat them") — verify: `j1/test_aea_57.py::test_j1_records_per_step` — evidence: the records listed per step.
- [ ] AC-13 [invariant] No paid call and nothing off the machine: the J-1 run makes 0 non-loopback connections (socket guard), uses placeholder provider keys, no `LANGFUSE_*` and no `MERIDIAN_EVAL_KEY`, and reads nothing under `eval/cases/heldout/` or any held-out key directory (data.md §5–§6) — verify: `j1/test_aea_57.py` run under the support socket guard, plus `grep -rn "heldout\|key_dir" tests/journeys/` — evidence: 0 outbound connections reported; grep prints nothing.
- [ ] AC-14 [invariant] The evidence record holds rule §4's nine fields: *Tested revision* is the commit SHA plus `agent_version` ("uncommitted" when the tree is dirty), *Environment* names host, server command, DB copy source, frontend build "none (API level)", the scripted adapter and the configured model ids, *Result* lists pass, fail or blocked per J-1 step with any failing assertion quoted; without the record option no file is written — verify: `test_support.py::test_evidence_record_fields` — evidence: the nine rows present; no file without the option.
- [ ] AC-15 [capture] This ticket's own record exists: command 2 in *What to build* writes `docs/testing/journeys/YYYY-MM-DD-AEA-57.md` at level `integrated with a scripted model` for every step reached, with *Blocked by* naming each still-unbound provider's ticket (or "none") and J-1's measured wall time — verify: the command, then reading the file — evidence: the committed record.
- [ ] AC-16 [invariant] The extension convention is enforced for later tickets: `support/README.md` lists every public fixture and option, and the support checks fail when a listed fixture is missing or a file under `tests/journeys/j*/` is not `j<N>/test_aea_<NN>.py` with N in J-1…J-10 — verify: `test_support.py::test_readme_lists_public_fixtures` and `::test_journey_file_convention` — evidence: both pass; a misnamed temp file makes the second fail.
- [ ] AC-17 [invariant] The harness gives later journeys a wall-clock control, so J-8's expired-session step can run without a literal or a real 12-hour wait (AEA-52 J-8, AEA-62 AC-15): a support fixture moves the time the server's one wall clock reads (`get_wall_clock()`, web.md §4, MC-20: session expiry, limiter windows) forward by a given number of seconds and leaves the demo clock alone; with it, a session signed in through `login` still resolves at start + `Limits.web.login_session_lifetime_s` − 1 s and answers 401 `UNAUTHENTICATED` `details.reason: "expired"` at start + `Limits.web.login_session_lifetime_s` (web.md §2, §6, WEB-5; the value read from `Limits`, never a literal), while `getDemoClock` reports the same demo time before and after. The mechanism is test-only, edits nothing under `src/meridian/` and adds no production seam; web.md §15's `ContainerOverrides` carries no wall clock, so if no such mechanism reaches the container's callable, the plan records `blocked-on AEA-23` (a contract change goes to the orchestrator) and AEA-52's and AEA-62's expired steps stay reported blocked, never passed (AEA-62 Agent handoff, known residual) — verify: `test_support.py::test_wall_clock_control_expires_session` — evidence: the 200 before and the 401 with `reason: "expired"` after printed; the demo clock equal before and after; `support/README.md` lists the fixture.
- [ ] AC-18 [regression/context] Same change updates `.claude/reference/area-map.md` (`tests/journeys/support/` and J-1 planned → actual with the commit), `.claude/state/icm-progress.md` row *Integrated-journey protection* (evidence link replaced by AC-15's record), DO-3 §9 test layout (adds `tests/journeys/` with `support/` and `j<N>/test_aea_<NN>.py`), and ticks `PROJECT-CHECKLIST.md` §8 "Journey harness exists …" with the record path — verify: `git diff --stat` — evidence: only those rows change beside this issue's owned files.

### Observability

- Responsibilities: emits nothing itself (test code, no entry point). J-1 drives the real entry points of **WF-18** (demo
  login: `auth_event` with outcomes `rejected` and `ok`, the opaque `session_id`, the `request` record; web.md §10) and
  **WF-1** (customer chat: the `conversations`, `messages`, `turns` and `spend_ledger` rows per step) and asserts those
  records exist after each step. It never re-checks redaction (CAP-1, CAP-10 own that).
- Capture evidence: AC-12 (records per step), AC-11 (rejected and secret values absent), AC-15 (the record of the run).

### Evaluation

- Checks: J-1 joins the deterministic journey suite that runs in the merge gate. It is not an E-run: no DO-5 suite
  (E-1…E-8) is added or changed and no number is reported (rule §1 row "E-1…E-8 … Untouched"; rule §3.4 "a smoke run
  proves limited compatibility only", and the same holds here).
- Expected-answer authority: the signed OpenAPI for every wire shape (through `openapi_check`), `policy/texts.py` for the
  greeting, graph-core §2 and cases.md §1.1 for the stored fields, and the journey script for the scripted reply (the
  script is the answer key; answer quality is E-1's with real models, DO-5).

### Metrics

- References: M-22 (conversations and turns counted from the `conversations` and `turns` rows), M-23 (`turns.server_ms`),
  M-24 (`turns.outcome`, `degrade_reason`), M-25 and M-26 (`spend_ledger.cost_usd`), M-29 (`turns.trace_export`).
- Acceptance conditions: J-1's reader asserts these columns are present and filled on the rows the journey created, so
  each metric stays computable from stored records; the harness reports no metric value, and its disposable DB never
  reaches the deployed metrics (M-22 excludes nothing it could pollute).

### Blocked by

- AEA-02 (`Settings`, domain types, ports), AEA-10 (first-boot copy, schema, `temp_sqlite()` pattern), AEA-11 (scripted
  fakes), AEA-23 (`create_app`, middleware, login route, `web/deps.py`, `openapi_check`).

### Agent handoff

- Area / owner: test infrastructure for the integrated-journeys rule (A0 test layout, DO-3 §9). Owns `tests/journeys/support/`
  (all of it) and `tests/journeys/j1/test_aea_57.py`; writes `docs/testing/journeys/YYYY-MM-DD-AEA-57.md`.
- Contracts and shared surfaces: consumes `create_app()` and `assert_response_matches` (AEA-23), the container (AEA-01),
  `Settings` (AEA-02), first boot (AEA-10), the DO-4 §12 ports, and AEA-01's `journey` marker, `tests/journeys/` skeleton
  and affected-journeys command. Produces the fixtures, scripted adapter, launcher, client, DB reader, record writer and the
  strict and record options and the wall-clock control (AC-17) for every later `j<N>/test_aea_<NN>.py`, for AEA-51 and AEA-52 (which wait for it), AEA-58
  (`browser/`), AEA-59 (may reuse the launcher; does not wait) and AEA-61 (launcher without the scripted ports). **Must
  not edit:** anything under `src/meridian/`, `tests/fakes/`, `tests/fixtures/`, `tests/conftest.py`, AEA-01's
  `tests/journeys/` skeleton files, `pyproject.toml`, `apps/web/**`, `docs/ux/**`, the OpenAPI. If AEA-01's skeleton has no
  place to load the support plugin (its `tests/journeys/conftest.py` or `addopts`), record `blocked-on AEA-01` (a one-line
  follow-up there).
- Scope boundary / refusal: API level only (browser journeys, `dist` and selectors are AEA-58's); J-1 only (J-2…J-10 land
  with their tickets per the journey map); no expired-session step (J-8, AEA-52/58: the 12 h lifetime is a frozen `Limits`
  value); no OpenAPI coverage of every operationId (AEA-59); no live model (AEA-61); no redaction checks (CAP tests).
- **ND-1 settled (R-W-8; web.md §15):** the launcher calls `create_app(settings, overrides=ContainerOverrides(…))` with
  the scripted adapter in all three maps (`choice`, `structured`, `tools`); `ContainerOverrides` and the `create_app`
  signature are AEA-23's, the container's pass-through keyword AEA-01's, and `register_graph` (AEA-51) is the only
  reader. No env name, `Settings` field or CLI flag can build it, which keeps AC-3 true. AEA-23 is already a blocker, so
  the earlier `blocked-on AEA-23` for steps 5–6 is dropped once AEA-23 merges; steps 5–6 still report `blocked-on AEA-51`
  until `run_graph` is bound (AC-7, AC-10).
- **needs-decision ND-2: J-1 needs more than its blockers.** Steps 1–3 need AEA-44 (it binds the `LoginSessions` store
  the gate resolves on every non-public request); step 4 needs AEA-40 and AEA-30 (`SessionService` and its
  `DemoService`); step 5 needs AEA-26 (admission's `allow_turn`) and a bound `run_graph`, which AEA-51 (wave 3) binds.
  None is in the plan's blocker list, and a journey cannot use doubles for them (rule §3.1). Recommended (built on here):
  keep wave 2 and the planned blockers; build in parallel; **merge AEA-57 after AEA-26, 30, 40 and 44** in wave 2 (merge
  order, not a blocking edge); steps 5–6 report `blocked-on AEA-51` until AEA-51 binds `run_graph`, and AEA-51 (blocked by
  this ticket) carries the criterion that J-1 runs with 0 blocked steps under `--journeys-strict`. Alternative: add 26, 30,
  40, 44 as blockers, which moves this ticket to wave 3, AEA-51/52 to wave 4 and the critical path from 6 to 7.
  *Status:* slice plan §0a ("J-1 runs in two stages") adopts the recommended treatment of steps 5–6; the merge order
  after AEA-26, 30, 40 and 44 stays the orchestrator's call (residuals-web, *Orchestrator items*).
- Awaiting Innocent: DAT-2 — built on the recommended option B (held-out keys outside the repo until E-4); nothing here
  changes under any option, because the harness reads no case or key file (AC-13); if he picks an option that keeps keys
  in the repo, AC-13's grep also covers that path.
- Awaiting UX session: `docs/plans/ux-join/` did not exist when this spec was written (2026-10-21). This ticket needs no
  selector, build command or real-backend mode from it (API level); those contracts are AEA-58's and stay unfixed there.
- Wave and gates: wave 2; no human, paid or design gate (merge-order note in ND-2).
- Lane: `lane::build-loop` — test code and fixtures that tests read (ticket-lanes: code-read).
- Risk: None — slice plan row carries no `risk::security`: test-only code with no route, secret store or deploy path; it
  handles a per-run synthetic login pair and session secret that never leave the run (AC-11, AC-13).
- Entry points added or changed: None
