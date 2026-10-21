## [AEA-59] contract boundary: server and mock responses vs the signed OpenAPI

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

**Why this exists (the Riverside lesson, `.claude/rules/integrated-journeys.md`).** Riverside's tests passed while "real
API responses lacked fields the UI expected", because routes were tested against fakes and the frontend against a mock,
and nobody checked that both sides honoured the same signed contract. The UI here is generated from
`docs/ux/03-structure/ui-contracts.openapi.yaml` (OpenAPI 3.1, `info.version` `0.1.0-ux3`, 30 operationIds across CON-1…CON-22).
This issue makes that file the checked boundary in three places: what the **real server** answers, what the **mock
fixtures** contain (including the awkward variants a UI must survive), and whether `apps/web`'s **generated types** still
match the file. Integrated-journeys rule 3; slice plan §0a (Amendment 1) and its row AEA-59.

**Example pair (input → process → output).**
- *Server.* Input: the real app (AEA-57's harness: `web/container.py` on a disposable copy of the issued DB, scripted
  model adapter, guards on) and the case for `startChatSession`. Process: log in with the demo pair from the test
  `Settings`, `POST /api/chat/sessions`, then `GET /api/chat/sessions/{thread_id}` with the returned id, and both again with
  no `mhc_session` cookie. Output: 201 and 200 bodies pass `assert_response_matches(response, "startChatSession")` /
  `(…, "getChatThread")` (web §13: status documented, content type, schema with `FormatChecker`, `X-Request-ID`); both
  unsigned calls are 401 `UNAUTHENTICATED` bodies that pass the same check. If AEA-40's route dropped `settled` (required
  by `StartSessionResponse`), the case fails naming the operationId, the status, the JSON pointer and `0.1.0-ux3`.
- *Missing case.* Input: the OpenAPI gains an operationId (after Innocent approves a contract change) and nobody adds a
  case. Output: `test_every_operation_has_a_case` fails listing that operationId; nothing passes by omission.
- *Fixture variant.* Input: the `STARTED` example of `startChatSession` 201. Process: generate variants (each optional
  property omitted, each nullable field `null`, each array without `minItems` emptied) and validate each through
  `assert_response_matches`. Output: every allowed variant passes, and the deliberate counter-variants (a `null` where
  the schema does not admit one, `[]` where `minItems ≥ 1`, an `error.code` outside the enum) fail, proving the check
  discriminates.
- *Drift.* Input: `apps/web/src/api/types.gen.ts` as committed. Process: run `apps/web`'s own pinned `openapi-typescript`
  binary on the OpenAPI into a pytest temp directory. Output: byte-equal → pass; any difference → fail with "stale
  generated file … regenerate in the UX session" and nothing under `apps/web` changed.

**The three files this issue owns** (slice plan row AEA-59), plus one journey file (Amendment 1):

1. **`tests/contract/test_openapi_server.py`**: every operationId driven through the real app.
   - **Cases live in one file per route issue** (slice plan §0a, "AEA-59 has no dependency on the harness"; AEA-59-2):
     the runner collects `tests/contract/cases/*.py` (`auth`, `chat`, `events`, `handoff`, `demo`, `staff_session`,
     `staff_cases`, `staff_live`, `staff_clock`, `reads`), each written by its route issue (AEA-23, AEA-40…AEA-48); this
     issue writes the runner, the case format and one documented example case, and never writes a route issue's file.
   - **One case per operationId**, keyed by operationId. A case names its preconditions (log in; `switchRole` to a role
     the operation's `x-roles` allows for staff operations; `startChatSession` for thread-scoped operations; a seeded
     case `reference` from the demo seed for case-scoped operations), the request (every named request example the
     OpenAPI gives the operation, read from the file), and the statuses it drives: the success status; 401
     `UNAUTHENTICATED` without a session for every operation except `login` (public, web §6), whose wrong-pair case is
     401 `LOGIN_FAILED`; and 400 `VALIDATION_ERROR` with a malformed body for every operation that documents 400 and
     takes a body. Other documented statuses (404, 409, 410, 429, 503, …) are proven by the route tickets that own them
     (AEA-23, AEA-40…AEA-48) as cases in their own `tests/contract/cases/<route>.py`, run by this runner with the same
     helper; this issue does not duplicate them.
   - **Every response a case receives** goes through AEA-23's `assert_response_matches(response, operation_id)`; the two
     SSE operations (`streamChatEvents`, `streamCaseEvents`) read frames for a bounded time and go through
     `assert_sse_frames_match(frames, operation_id)` (web §13). No second validator is written (integrated-journeys §6).
   - **Completeness:** `test_every_operation_has_a_case` asserts the case ids equal `load_contract().operations`' keys
     exactly, and fails listing each operationId with no case and each case whose operationId the file no longer has.
     The 30 is read from the file, never hard-coded.
   - **Not yet wired is said, never hidden.** In wave 2 most routes and services land beside this issue. A case whose
     method and path template are not in the app's routes is skipped with the reason `route not registered:
     <operationId>`; a case that meets web §4's `RuntimeError("not bound: <name>")` is skipped with `not bound: <name>`.
     With `CONTRACT_STRICT=1` in the environment (test-only switch, read only by this file, never by `src/`), both are
     failures. The wave merge from wave 3 on and the pre-deploy run use strict mode (rule `build-loop-test-scope`, *AEA
     addition*: "At a wave merge, run all journeys plus the contract boundary checks").
   - **Guards on, nothing bypassed:** the app comes from AEA-57's harness with no `dependency_overrides`, the real login,
     gate, rate limiter and persistence; the only substitute is the scripted model adapter at the provider boundary
     (integrated-journeys rule 1). `resetDemo` runs last, on its own app instance, because it rewrites the DB copy.
2. **`tests/contract/test_openapi_fixtures.py`**: every mock fixture and a generated edge set.
   - **YAML 1.2 reading.** The OpenAPI's examples are read the way `apps/web` and Prism read them (`build-contract-index.mjs`:
     "YAML 1.2 via the `yaml` package: OFF/ON stay strings"): timestamps stay strings, `yes`/`no`/`on`/`off` stay strings,
     and example names `ON`/`OFF` stay names. Measured 2026-10-21: a plain `yaml.safe_load` turns 371 example timestamps
     into `datetime`, `option: yes` / `label: Yes` in the `BurningCheckBlock` examples into `True`, and `getStaffing`'s
     example names into booleans, so every such example would fail for the loader's reason, not the contract's.
   - **Named examples:** every response example (250 today) of every operation and status, wrapped as an
     `httpx.Response` with its status, content type and a generated `X-Request-ID`, through `assert_response_matches`;
     the SSE `FRAMES` examples through `assert_sse_frames_match`. A documented status with no example (today only
     `logout` 204, which has no body) is listed by name, not skipped silently.
   - **Generated edge set**, from each named example as the base, per integrated-journeys rule 3 ("optionals omitted,
     nulls, empty lists, and every documented error response"):
     - *omitted optionals*: each property not in its object schema's `required`, removed one at a time at every depth
       the example reaches → must pass;
     - *nulls*: each property whose schema admits `null` set to `null` → must pass; for each object schema, one
       property whose schema does not admit `null` set to `null` → must fail;
     - *empty lists*: each array with no `minItems` set to `[]` → must pass; each array with `minItems ≥ 1` set to
       `[]` → must fail;
     - *error bodies*: for every operation and every documented status ≥ 400, each named example passes, one `ApiError`
       body per `error.code` that status's schema allows passes, and a body with a code outside `Contract.error_codes`
       fails.
     The run prints the count of variants per kind, so a reviewer sees the set was not empty. An allowed variant that
     fails is a **contract finding**: the issue stops and it goes to Innocent (the signed contract stays
     authoritative; integrated-journeys rule 3). It is never excluded to make the suite green.
   - **`apps/web`'s contract index, read only:** `apps/web/src/api/contract.gen.json`'s `specVersion` equals the
     OpenAPI's `info.version`, its operation set equals `Contract.operations`, and each operation's method, path,
     success statuses and request examples equal the file's. A stale index fails with the UX session's regenerate
     command in the message (`npm run examples`), never regenerated here.
   - **API-shaped fakes this project adds.** Any fake HTTP response body a later backend test or journey needs is saved
     as `tests/fixtures/api/<operationId>.<status>.<name>.json` (body only); this file validates every file there through
     `assert_response_matches` and fails on an undocumented operationId or status. Today the folder is empty: AEA-11's
     six doubles are model, clock, index and trace fakes, not API bodies.
3. **`tests/contract/test_types_gen_drift.py`**: the generated-types freshness check in the merge gate, reading
   `apps/web` and never writing it.
   - Runs `apps/web/node_modules/.bin/openapi-typescript` directly (never `npm run …` or `npx`: `gen:types`,
     `pretest`, `pretypecheck` and `check:gen` all write inside `apps/web`, `check:gen` into `apps/web/.tmp/`) on
     `docs/ux/03-structure/ui-contracts.openapi.yaml` with the same arguments `gen:types` uses, output into pytest's
     `tmp_path`, working directory `tmp_path`; compares bytes with `apps/web/src/api/types.gen.ts`.
   - First checks the binary is the pinned one: `apps/web/node_modules/openapi-typescript/package.json` `version` equals
     the exact pin in `apps/web/package.json` `devDependencies` (`7.13.0` today). A missing binary or another version
     **fails** with a message naming both; the test never installs anything.
   - A snapshot of `apps/web` (every file outside `node_modules/`: path, size, SHA-256) is equal before and after.
4. **`tests/journeys/j1/test_aea_59.py`** (journey, Amendment 1 convention): J-1 (login → start session → one turn →
   refresh/resume; signed-out redirect) through AEA-57's harness, asserting that every HTTP response the journey received
   passed `assert_response_matches` for its operationId, the signed-out 401 included.

**What this extends for later tickets.**
- *Journeys:* each later build-loop ticket adds its own `tests/journeys/j<N>/test_aea_<NN>.py` (one file per ticket, so
  tickets in a wave never edit the same file) and never edits `tests/journeys/support/` (AEA-57) or this issue's files.
- *Contract cases:* a route ticket adds the server cases of the operations it serves, with each documented error status
  its route can produce, to its own `tests/contract/cases/<route>.py` (AEA-23-3, AEA-40-6, AEA-41-1, AEA-42-2, AEA-43-2,
  AEA-44-2, AEA-45-3, AEA-46-2, AEA-47-2, AEA-48-2); it never edits this issue's runner. A new operationId only arrives
  through an Innocent-approved OpenAPI change, and that change must add its case to the owning route file (the
  completeness test names the file and fails in strict mode until it does).
- *Fixtures:* any API-shaped fake lands in `tests/fixtures/api/` under the naming above and is validated automatically.

**Verification levels** (integrated-journeys §4): the server cases and the J-1 file are `integrated with a scripted
model` (API level: real server, DB copy, guards on; the frontend build is AEA-58's browser level). The fixture, index and
drift checks run no server and are `mock-tested`. Nothing here is `verified with live models` (AEA-61).

**The command a reviewer runs** (cheapest first after lint and type check):
`uv run pytest tests/contract/test_types_gen_drift.py tests/contract/test_openapi_fixtures.py tests/contract/test_openapi_server.py tests/journeys/j1/test_aea_59.py -rs`
(`-rs` prints every skip reason), then the strict form the wave merge uses:
`CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -rs`. In wave 2 the strict form is expected to
fail on the operations whose routes or services have not merged; it lists them by name.

### Source

- Rule `.claude/rules/integrated-journeys.md` §1 rows "Route responses validated against `ui-contracts.openapi.yaml`"
  and "Frontend types generated from the OpenAPI", §3 rules 1, 3 and 5, §4 (levels and evidence record), §5 (who runs
  what), §6 ("AEA-23's OpenAPI check is the only response validator; AEA-59 calls it from more places") and the ticket
  table row AEA-59; rule `.claude/rules/build-loop-test-scope.md` *AEA addition* (wave merge runs "all journeys plus the
  contract boundary checks").
- Slice plan §0a (Amendment 1: journey map J-1, the `tests/journeys/j<N>/test_aea_<NN>.py` convention, where the two
  tracks connect) and row AEA-59 (title, owned files, blockers 02 and 23, wave 2, lane B, not `risk::security`).
- **Final contract:** [`stage7/web.md`](../../design/contracts/stage7/web.md) §13 (`OperationSpec`, `Contract`,
  `load_contract`, `assert_response_matches`, `assert_sse_frames_match`, `operations_documenting`; WEB-24, WEB-38), §4
  (`RuntimeError("not bound: <name>")`, providers), §6 (public paths: only `POST /api/login` and `GET /healthz` on the
  API side), §1 (`ApiError`; `ApiErrorCode` equals the OpenAPI enum, WEB-9); [`stage7/graph-core.md`](../../design/contracts/stage7/graph-core.md)
  §12 (`Settings`: `demo_username`, `demo_password`, `session_secret`, `eval_key`, test values generated at run time);
  [`stage7/models.md`](../../design/contracts/stage7/models.md) §1–§3 (the model ports the scripted adapter stands
  behind; no paid call); [`stage7/data.md`](../../design/contracts/stage7/data.md) §5 (held-out case files apart from
  their keys; DAT-2 custody) — this issue never opens `eval/`.
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml` (wins on every wire shape): all 30 operationIds, their
  `x-roles`, request and response examples, `components.responses` (`ValidationError`, `SessionNotFound`, `SessionEnded`,
  `TurnInProgress`, `ResetInProgress`, `RoleNotAllowed`, `CaseNotFound`, `TooManyRequests`, `Unauthenticated`,
  `LoginFailed`, `LoginRateLimited`). `docs/ux/03-structure/UI_CONTRACTS.md` CON-1…CON-22.
- `apps/web` (read only, UX-owned): `package.json` scripts `gen:types`, `examples`, `check:gen` and the exact pin
  `openapi-typescript` `7.13.0`; `scripts/paths.mjs` (`SPEC`, `TYPES_OUT`, `INDEX_OUT`); `scripts/check-generated.mjs`
  (writes `apps/web/.tmp/`, so it is not run from here); `scripts/build-contract-index.mjs` (YAML 1.2; 30 operations);
  `README.md` *Do not hand-edit*. `docs/plans/ux-join/` (the UX session's deliverables) does not exist yet on
  2026-10-21; see Agent handoff.
- DO-3 §9 (`tests/contract/`, `tests/api/`); DO-6 WF-1…WF-6, WF-18 (the operations driven); AEA-11 (the six fakes, none
  API-shaped); AEA-57 (harness); AEA-23 AC-24 (the validator's own tests).
- **Brief check:** serves "Deployed URL — a live web app the reviewer can interact with directly. They will ask their own
  questions and try to break it, so make sure edge cases and escalation behave" (Deliverables 1) by proving the screens
  and the server agree on every response shape, including empty, null and error bodies; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Every operationId in the OpenAPI has exactly one server case across `tests/contract/cases/*.py` and no case names an operationId the file lacks; the count comes from `load_contract().operations`, never a literal; each operationId with no case is named with the route file that should hold it (AEA-59-2), and with `CONTRACT_STRICT=1` (the wave merge from wave 3 on, slice plan §0a; amendments §1) a missing case fails — level: mock-tested (static) — verify: `tests/contract/test_openapi_server.py::test_every_operation_has_a_case` and the same with `CONTRACT_STRICT=1` — evidence: the found case ids per file and the missing ids with their file printed; the strict run fails on exactly the missing ones; a scratch run with one case removed fails strictly naming that operationId (shown in the implementer's report, not committed).
- [ ] AC-2 [invariant] Each registered and bound operation's success response from the real app (AEA-57 harness, disposable DB copy, scripted model adapter, no `dependency_overrides`) passes `assert_response_matches`, for every named request example the operation has; SSE operations pass `assert_sse_frames_match` on the frames read — level: integrated with a scripted model — verify: `tests/contract/test_openapi_server.py::test_success_matches_contract` (parametrised by operationId and request example) — evidence: one pass per registered operation and example; `app.dependency_overrides` asserted empty.
- [ ] AC-3 [failure/refusal] Every operation except `login` answers 401 `UNAUTHENTICATED` with no session cookie, `login` answers 401 `LOGIN_FAILED` to a wrong pair, and every operation that documents 400 and takes a body answers 400 `VALIDATION_ERROR` to a malformed body; each body passes `assert_response_matches` — level: integrated with a scripted model — verify: `tests/contract/test_openapi_server.py::test_unauthenticated_matches_contract`, `::test_validation_error_matches_contract` — evidence: one pass per operation; the gate is live (no case reaches a route without the login).
- [ ] AC-4 [failure/refusal] A case whose route is not registered is skipped with `route not registered: <operationId>`, a case that meets `RuntimeError("not bound: <name>")` is skipped with `not bound: <name>`, and with `CONTRACT_STRICT=1` both are failures; nothing else is ever skipped — level: integrated with a scripted model — verify: `uv run pytest tests/contract/test_openapi_server.py -rs` and `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -rs` — evidence: the default run's skip list names each unwired operation and its reason; the strict run fails on exactly those; the evidence record's *Blocked by* field lists them.
- [ ] AC-5 [invariant] The fixture check reads the OpenAPI's examples as YAML 1.2: the `STARTED` example's `greeting.at` arrives as the string `2026-10-16T14:20:00-05:00`, the `BurningCheckBlock` example's option arrives as `"yes"`, and `getStaffing`'s 200 examples are named `ON` and `OFF` — level: mock-tested — verify: `tests/contract/test_openapi_fixtures.py::test_examples_read_as_yaml_1_2` — evidence: three type and value assertions pass; the loader rule itself is AEA-23's criterion (`ContractLoader`, web.md §13, R-W-9; AEA-23-1), so a coercing loader is AEA-23's failure, not a blocker here.
- [ ] AC-6 [invariant] Every named response example (250 today) passes `assert_response_matches` for its operation and status, and both SSE `FRAMES` examples pass `assert_sse_frames_match`; the documented statuses with no example are listed by name — level: mock-tested — verify: `tests/contract/test_openapi_fixtures.py::test_named_examples_match` — evidence: one pass per example; the listed exceptions are exactly `logout 204`.
- [ ] AC-7 [invariant] The generated edge set passes where the schema allows it: each optional property omitted, each nullable field `null`, each array without `minItems` emptied, and one `ApiError` body per `error.code` each documented error status allows — level: mock-tested — verify: `tests/contract/test_openapi_fixtures.py::test_edge_variants_accepted` — evidence: pass; the printed counts per kind (omitted, null, empty, error) are each above zero.
- [ ] AC-8 [failure/refusal] The counter-variants are rejected: `null` where the schema admits none, `[]` where `minItems ≥ 1`, an `error.code` outside `Contract.error_codes`, and an undocumented status for the operation — level: mock-tested — verify: `tests/contract/test_openapi_fixtures.py::test_counter_variants_rejected` — evidence: each raises `AssertionError` from `assert_response_matches`; the printed count of counter-variants is above zero.
- [ ] AC-9 [invariant] `apps/web/src/api/contract.gen.json` agrees with the OpenAPI (`specVersion` = `info.version`, same operation set, same method, path, success statuses and request examples per operation); a mismatch fails naming the operation and `npm run examples` as the UX session's fix — level: mock-tested — verify: `tests/contract/test_openapi_fixtures.py::test_contract_index_matches_openapi` — evidence: pass on the committed index.
- [ ] AC-10 [invariant] Every file under `tests/fixtures/api/` named `<operationId>.<status>.<name>.json` passes `assert_response_matches`; a file naming an unknown operationId or an undocumented status fails — level: mock-tested — verify: `tests/contract/test_openapi_fixtures.py::test_api_fixtures_match` — evidence: pass with the folder empty (0 files reported); a scratch file `getQueue.418.x.json` fails (implementer's report, not committed).
- [ ] AC-11 [invariant] `apps/web/src/api/types.gen.ts` equals a fresh generation by `apps/web/node_modules/.bin/openapi-typescript` run into `tmp_path`; a difference fails naming the file and `npm run gen:types` as the UX session's fix — level: mock-tested (static) — verify: `tests/contract/test_types_gen_drift.py::test_types_gen_is_current` — evidence: pass on the committed file; a scratch copy of the OpenAPI with one field renamed, passed through the test's spec-path parameter, fails (implementer's report).
- [ ] AC-12 [failure/refusal] A missing `openapi-typescript` binary, or one whose `package.json` version differs from the exact pin in `apps/web/package.json` (`7.13.0`), fails the drift check with a message naming the binary path and both versions; it never installs or skips — verify: `tests/contract/test_types_gen_drift.py::test_refuses_missing_or_unpinned_binary` (binary path and version source pointed at temp doubles) — evidence: two failures with the named message; no `npm` process started (subprocess spy).
- [ ] AC-13 [negative] The drift and fixture checks write nothing under `apps/web`: the snapshot of every file outside `node_modules/` (path, size, SHA-256) is equal before and after, `apps/web/.tmp/` is not created by the run, and no `npm`/`npx` command is executed — verify: `tests/contract/test_types_gen_drift.py::test_apps_web_untouched` — evidence: snapshot equality asserted; the subprocess spy shows only the `openapi-typescript` binary.
- [ ] AC-14 [negative] No sensitive value reaches a failure message or the evidence record: a distinctive login password, session cookie value and six-digit inbox code generated at test time, placed in a deliberately broken `login` body and a broken `listDemoInbox` body, are absent from the `AssertionError` text, pytest's captured output and `docs/testing/journeys/<date>-AEA-59.md`; the failure still names the operationId, status and JSON pointer — verify: `tests/contract/test_openapi_fixtures.py::test_failure_messages_carry_no_values` — evidence: absence asserted in all three; if AEA-23's helper prints the instance, this fails and goes back to AEA-23.
- [ ] AC-15 [negative] The default run makes no outbound connection and no paid call, and never opens `eval/`: during the server cases a socket guard refuses any non-loopback connect and records none; an `open` spy during the fixture checks records no path under `eval/` (held-out custody, data.md §5, DAT-2) — verify: `tests/contract/test_openapi_server.py::test_no_outbound_connections`, `tests/contract/test_openapi_fixtures.py::test_never_reads_eval` — evidence: zero refused connects; zero `eval/` paths.
- [ ] AC-16 [journey] J-1 through AEA-57's harness: every HTTP response the journey receives (login, `startChatSession`, `submitTurn`, `getChatThread` after the refresh, and the signed-out 401) passes `assert_response_matches` for its operationId, and the journey's own user-visible and stored-row assertions still pass — level: integrated with a scripted model — verify: `uv run pytest tests/journeys/j1/test_aea_59.py -m journey` — evidence: pass with the per-response operationIds listed; if the harness exposes no way to see each response, the plan records `blocked-on AEA-57` instead of editing `tests/journeys/support/`.
- [ ] AC-17 [invariant] The UX session's dev fixtures pass the same checks as the OpenAPI's examples (shell audit S3; AEA-59-1): when the dump the UX session names in `docs/plans/ux-join/selectors.md` exists (one record per `{operationId, status, name, body}`), every body passes `assert_response_matches` for its operation and status and every stream event `assert_sse_frames_match`, read only; when it does not exist yet, the check is skipped with `ux fixture dump missing: <path>`, and `CONTRACT_STRICT=1` fails it — verify: `uv run pytest tests/contract/test_openapi_fixtures.py -k ux_dump -rs` — evidence: the count of records checked, or the named skip.
- [ ] AC-18 [invariant] Server cases live in one file per route issue (AEA-59-2; slice plan §0a): `tests/contract/test_openapi_server.py` collects `tests/contract/cases/*.py` (`auth`, `chat`, `events`, `handoff`, `demo`, `staff_session`, `staff_cases`, `staff_live`, `staff_clock`, `reads`), each written by its route issue; this issue writes the runner, the case format and a documented example case; the completeness check counts cases across all files and names, for each missing operationId, the file that should hold it — verify: `uv run pytest tests/contract/test_openapi_server.py -rs` — evidence: the case count per file printed; missing operationIds listed with their file.
- [ ] AC-19 [regression/context] Same change updates: `.claude/reference/area-map.md` (A0 test rows for `tests/contract/test_openapi_server.py`, `tests/contract/cases/` (the case format; route files owned by their route issues), `test_openapi_fixtures.py`, `test_types_gen_drift.py`, `tests/fixtures/api/` and `tests/journeys/j1/test_aea_59.py`, planned → actual + commit), `.claude/state/icm-progress.md` (the *Routes verified against code and tests* row's evidence link), DO-3 §9 `tests/contract/` status line, and the evidence record `docs/testing/journeys/YYYY-MM-DD-AEA-59.md` with every field of integrated-journeys §4 (claim, level per check, revision, environment, the two commands above, result, evidence location, remaining limitations, *Blocked by* listing the unwired operations) — verify: `git diff --name-only` — evidence: those paths in the diff, nothing under `apps/web/**`, `docs/ux/**` or `eval/`.

### Observability

N/A — test-only issue: it adds no entry point and emits no log, trace or table record. It drives WF-1…WF-6 and WF-18
through the real app and checks wire shapes only (including `X-Request-ID` on every response, inside
`assert_response_matches`). Record capture stays with the CAP-n tests (DO-6) and their owners; journeys do not re-check
redaction (integrated-journeys §6). A reviewer could argue the evidence record is an observability output; it is test
evidence under integrated-journeys §4, not a DO-6 record.

### Evaluation

N/A — no DO-5 suite is added or run, and no expected answer is decided here: a contract check proves shape, not
correctness of content, and it is never cited as an E-run result (integrated-journeys rule 4 and §1 row "E-1…E-8").
A reviewer could disagree because `getLatestEval` (CON-20) bodies are checked; only their shape is, and the values stay
AEA-53's and AEA-24's.

### Metrics

N/A — no M-n is computed, emitted or changed. The CON-18 and CON-19 bodies that display M-1…M-29 are validated for shape
only (labels, nulls with `null_reason`, empty lists); whether each value stays computable from stored records is AEA-53's
CAP-6 proof. A reviewer could disagree because a shape failure there would hide a metric on SCR-9/SCR-10; that failure is
caught here as a contract failure, not as a metric.

### Blocked by

AEA-02 (`ApiErrorCode`, `Settings`), AEA-23 (`tests/api/openapi_check.py`, `create_app`, the gate, `web/deps.py`).
Same-wave sibling used through its own surface, not a blocking edge: AEA-57 (`tests/journeys/support/`: the real app on a
disposable DB copy and the scripted model adapter, launched through `create_app(settings, overrides=…)`, web.md §15; it in
turn uses AEA-10's `temp_sqlite()` and AEA-11's fakes). Settled by slice plan §0a; see the note at the end.

### Agent handoff

- Area / owner: A0 test support (DO-3 §9 `tests/contract/`); slice plan AEA-59; journey file per Amendment 1.
- Contracts and shared surfaces: consumes AEA-23's `load_contract`, `assert_response_matches`, `assert_sse_frames_match`
  and `Contract.error_codes` (web §13), `create_app` and the gate; AEA-57's harness (app builder, login helper, scripted
  adapter, J-1); the OpenAPI and `apps/web/src/api/{types.gen.ts,contract.gen.json}` and
  `apps/web/node_modules/.bin/openapi-typescript` **read only**. Produces the contract boundary checks the wave merge and
  the pre-deploy run execute (consumed by AEA-51 and AEA-52, which are blocked by this issue, and by AEA-56's full-suite
  run), and the `tests/fixtures/api/` drop point. Must not edit: `tests/api/openapi_check.py` (AEA-23),
  `tests/journeys/support/` (AEA-57), `tests/fakes/` (AEA-11), `tests/conftest.py` (AEA-01), any route or schema file,
  the OpenAPI, `UI_CONTRACTS.md`, anything under `apps/web/**`.
- Scope boundary / refusal: no new response validator; no regeneration of `types.gen.ts` or `contract.gen.json`; no
  `npm`/`npx`; no route-specific error statuses beyond 401 and 400 (the route tickets own the rest); no browser (AEA-58);
  no live model (AEA-61); no prompt checks (AEA-60). A response, example or variant that disagrees with the contract is
  investigated; a needed contract change stops the issue and goes to Innocent (checklist *Skips* row for §7).
- Wave and gates: wave 2; no human, UX or paid gate (it only reads `apps/web`). Strict mode is expected red until the
  wave-3 integration tickets bind every service.
- Lane: build-loop — it adds tests the merge gate runs.
- Risk: None (not `risk::security` in the slice plan): it changes no product path. AC-14 and AC-15 still keep codes,
  credentials and held-out material out of its output because CON-6 and CON-22 bodies pass through it.
- **Cross-ticket finding for AEA-23, settled (R-W-9; web.md §13):** with plain `yaml.safe_load` the OpenAPI's examples
  come back with YAML 1.1 coercions (371 timestamps as `datetime`, `yes`/`Yes` as `True`, example names `ON`/`OFF` as
  booleans; measured 2026-10-21). `load_contract` now reads the file with `ContractLoader(yaml.SafeLoader)` (no timestamp
  resolver; booleans only `true`/`false`), and that rule is AEA-23's criterion (AEA-23-1). AEA-59 no longer records
  `blocked-on AEA-23` for AC-5–AC-7.
- **Awaiting UX session** (`docs/plans/ux-join/` not yet written; slice plan §0a lists these as the UX session's
  deliverables):
  1. *Dev scenarios:* `apps/web/src/dev/scenarios/*` are TypeScript transforms over the examples, not data files, so a
     Python test cannot validate their resolved bodies without editing `apps/web`. Needed: a JSON export of every
     scenario's resolved response bodies (path and format fixed by the UX session). Until then they are checked only by
     `apps/web`'s own type check against `types.gen.ts` (`mock-tested`), and the evidence record says so. AC-17 checks the
     export once `docs/plans/ux-join/selectors.md` names it (R-W-10: a UX-session deliverable, not a contract gap; web.md
     §13).
  2. *Drift-check contract:* that `src/api/types.gen.ts` stays the committed path, `gen:types` keeps its arguments
     (spec path and `-o`, no flags) and `openapi-typescript` stays exactly pinned. AC-11 and AC-12 read those from
     `apps/web/package.json` and `scripts/paths.mjs` today (R-W-10: a UX-session deliverable, not a contract gap; web.md
     §13).
  3. *Selectors and build command:* none used here (no browser); AEA-58 consumes them.
- Entry points added or changed: None

**Settled (was needs-decision 1; slice plan §0a, "AEA-59 has no dependency on the harness"):** AEA-57 is not a formal
blocker and AEA-59 stays in wave 2; the per-route case files (AC-18) let route issues prove their own operations, and
AEA-51 switches on strict mode from wave 3. The server cases and AC-16 still run on AEA-57's launcher, so the in-wave
order is AEA-57 first (merge order, not a blocking edge); if AEA-57 is not on `main` when the plan is written, the plan
records `blocked-on AEA-57` for those cases only and builds the fixture, index and drift checks.
