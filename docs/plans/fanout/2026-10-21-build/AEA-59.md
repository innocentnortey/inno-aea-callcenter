# Plan — [AEA-59] contract boundary: server and mock responses vs the signed OpenAPI

**Status:** planned — **READY**. Two criteria wait on another ticket. Everything else builds now.
- **AC-16 waits on AEA-57.** The J-1 journey file runs through AEA-57's harness, and AEA-57 is not on `main`: no `tests/journeys/support/`, no branch, no plan.
- **AC-14 waits on a small AEA-23 follow-up.** `assert_response_matches` puts the rejected value in its failure message. See §8 R-1.

**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/59 (identical to
`docs/plans/tickets/AEA-59.md`) · **Base revision:** `main` `4a76850` (AEA-47 merged at `23dd4ac`) · **Wave:** 2 ·
**Lane:** build-loop · **Risk:** none (no `risk::security`: plan → implement with tests → review; no frozen tests)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-59-contract-boundary` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-59`), cut from `main` at or after `4a76850`.

No earlier version of this plan existed at this path; this is the first write.

---

## 1. Goal and sources

### Goal (issue *What to build*, quoted in short)

"This issue makes that file [`docs/ux/03-structure/ui-contracts.openapi.yaml`, `0.1.0-ux3`, 30 operationIds] the checked
boundary in three places: what the **real server** answers, what the **mock fixtures** contain (including the awkward
variants a UI must survive), and whether `apps/web`'s **generated types** still match the file."

**What it does, concretely (one example per part).**
- **Server runner.** It reads `tests/contract/cases/staff_clock.py`, which AEA-47 wrote and which is on `main`. For the drive `advanceDemoClock/next_morning` it does four things:
  1. Builds the real app: `create_app(settings)` on a fresh temporary data dir. The app's own first boot copies the issued DB there.
  2. Logs in with the run's generated demo pair and switches the role to `supervisor` (`PUT /api/session/role`, example `SUPERVISOR`).
  3. Posts the `NEXT_MORNING` request example.
  4. Checks the answer: status 200, then `assert_response_matches(response, "advanceDemoClock")`.

  On `main` today `login` itself fails inside the app with `RuntimeError("not bound: get_login_sessions")`, because AEA-44 has not merged. So the drive is **skipped** with the reason `not bound: get_login_sessions`. With `CONTRACT_STRICT=1` the same drive **fails** with that reason.
- **Fixtures.** Every one of the 250 named response examples is wrapped as an `httpx.Response` and validated. So are about 1,000 allowed variants and about 2,900 counter-variants generated from them: optional fields omitted, nulls, empty lists, error bodies, required fields removed, a `null` where none is allowed, `[]` below `minItems`, an unknown error code, an undocumented status. Allowed variants must pass; counter-variants must raise `AssertionError`.
- **Drift.** `apps/web/node_modules/.bin/openapi-typescript` (pinned `7.13.0`) is run on the OpenAPI into pytest's `tmp_path`, and its output is compared byte for byte with `apps/web/src/api/types.gen.ts`. Measured 2026-10-21: byte-equal in 0.4 s.

### Context (≤ 6 lines)

Riverside's tests passed while real API responses lacked fields the UI expected (rule `integrated-journeys.md`). Several things are already on `main`:
- AEA-23's validator, `tests/api/openapi_check.py`;
- four route case files: `auth` (AEA-23), `events` (AEA-41), `handoff` (AEA-42) and `staff_clock` (AEA-47);
- the real app factory.

Each route ticket wrote its own case vocabulary and a local driver that runs on doubles. **No runner yet drives those cases through the real app, and nothing validates fixtures or generated types.** This ticket adds both. It adds no product code.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-59.md` (AC-1…AC-19, example pairs, *Agent handoff*) | Everything below |
| Rule: journeys | `.claude/rules/integrated-journeys.md` §1 rows "Route responses validated…", "Frontend types generated…"; §3 rules 1, 3, 5, 6; §4 levels + evidence record; §6 "AEA-23's OpenAPI check is the only response validator" | Real app with guards on; fixtures and variants; the generated-types check; evidence record fields; no second validator |
| Rule: build loop | `.claude/rules/build-loop-test-scope.md` + *AEA addition* ("At a wave merge, run all journeys plus the contract boundary checks"; no paid calls) | Affected tests only; strict mode at wave merges; no live calls |
| Web addendum (wins over DO-4) | `docs/design/contracts/stage7/web.md` §13 (`OperationSpec`, `Contract`, `load_contract`, `assert_response_matches`, `assert_sse_frames_match`, `ContractLoader`, R-W-9, R-W-10); §4 (`RuntimeError("not bound: <name>")`, providers, `owned_thread`); §6 (public API paths: only `POST /api/login`, `GET /healthz`); §7 (reset gate answers); §15 (`create_app`, `ContainerOverrides`, test-only) | §4 below copies the signatures |
| Graph-core addendum | `stage7/graph-core.md` §12 (`Settings`: generated test values for `demo_username`, `demo_password`, `session_secret`) | Settings come from `make_settings` (generated per test) |
| Models addendum | `stage7/models.md` §1–§3 (ports the scripted adapter stands behind) | No paid call; register_graph is a no-op until AEA-51 (§8 R-3) |
| Data addendum | `stage7/data.md` §5 (held-out custody, DAT-2) | Never open `eval/` (AC-15) |
| Slice plan | `docs/plans/slice-plan.md` §0a (Amendment 1; "AEA-59 has no dependency on the harness"; journey map J-1), §1 row AEA-59 (owned files, blockers 02 and 23, wave 2, lane B), §3 collision map (`tests/contract/` OpenAPI files are 59's; `tests/journeys/support/` is 57's; route files one per ticket) | Boundary in §2 |
| Code design | `docs/design/code-design.md` (DO-3) §9 test layout | AC-19 updates the `contract/` line |
| Component contracts | `docs/design/contracts/internal-components.md` (DO-4) §0 ("`details` never holds a rejected value") | Failure messages never carry values (AC-14) |
| API ↔ CON mapping | `docs/design/contracts/api-con-mapping.md` rows CON-1…CON-22 | The operation → route-file table (§5 step 3) |
| UX join | `docs/plans/ux-join/FOR-UX-SESSION.md` §6 (fixture dump: one record per `{operationId, status, name, body}`, e.g. `apps/web/tests/e2e/.gen/fixtures.json`, named in `selectors.md`); `docs/plans/ux-join/audit-shell-reads-build.md` S2, S3 | AC-17 reads the dump when `selectors.md` names it (it does not exist yet) |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` | n/a: no E-run, no expected answer; shape only (ticket *Evaluation*) |
| Observability contract (DO-6) | `docs/design/observability-contract.md` WF-1…WF-6, WF-18 | n/a: no entry point, no record; drives existing workflows only (ticket *Observability*) |
| Key-metrics registry (DO-7) | `docs/design/key-metrics-registry.md` | n/a: CON-18/19 bodies validated for shape only (ticket *Metrics*) |
| Stage 7 sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | None is re-decided here. D-5 (OpenAPI gains `CaseDetail.events.last_event_id`) is the UX session's change; the drift and index checks catch it if `apps/web` is not regenerated |

---

## 2. Boundary

### Owned files (the only files the implementer creates or edits)

| File | Create / modify | What it holds |
|---|---|---|
| `tests/contract/test_openapi_server.py` | create | Server-runner tests (AC-1, 2, 3, 4, 15 server part, 18) |
| `tests/contract/openapi_cases.py` | create | Case loading, the canonical vocabulary + aliases, static well-formedness checks, operation → route-file map, completeness |
| `tests/contract/openapi_driver.py` | create | Real-app launcher, exception tap, socket guard, drive realisation, bounded SSE reader, `blocked()` |
| `tests/contract/test_openapi_fixtures.py` | create | Fixture tests (AC-5…10, 14, 15 fixture part, 17) |
| `tests/contract/openapi_variants.py` | create | Document pointers, example iteration, `fake_response`, edge-variant generator, request examples, `contract_strict()` |
| `tests/contract/test_types_gen_drift.py` | create | Drift tests (AC-11, 12, 13) with their small helpers |
| `tests/contract/cases/README.md` | create | The case format, the vocabulary and **the documented example case** (AC-18) |
| `tests/fixtures/api/README.md` | create | The drop-point naming rule `<operationId>.<status>.<name>.json` (AC-10); git cannot track an empty folder |
| `tests/journeys/j1/test_aea_59.py` | create | J-1 contract step (AC-16); one skipped test until AEA-57 lands (§8 R-2) |
| `docs/testing/journeys/<run-date>-AEA-59.md` | create | Evidence record (AC-19); `<run-date>` = the date of the final run, `YYYY-MM-DD` |
| `.claude/reference/area-map.md` | modify | Only the **Status** cell of the row `3+ / Integration and journeys`: append AEA-59's clause (§5 step 13) |
| `.claude/state/icm-progress.md` | modify | Add **one** new row *Routes verified against code and tests* for AEA-59 (house pattern: one row per slice) |
| `docs/design/code-design.md` | modify | §9 only: the `contract/` line of the tree and the *Built on `main`* line |

The support modules split the server and fixture logic out of the test files. Without the split, one file would run past
`code-structure.md`'s 500-line cap for tests. The modules sit inside AEA-59's `tests/contract/` family (`test_openapi_*`,
`openapi_*`); no other ticket uses these names (§8 R-6).

### Read only (import or read, never edit)

- `tests/api/openapi_check.py` (AEA-23), `tests/api/web_shell_support.py` (AEA-23), `tests/api/events_support.py` (AEA-41),
  `tests/services/person_request_support.py` (AEA-42), `tests/fixtures/sqlite.py` (AEA-10).
- `tests/contract/cases/{auth,events,handoff,staff_clock}.py` and every future `tests/contract/cases/<route>.py` (route tickets).
- `src/meridian/**` (no edit at all; the runner only imports `create_app`, `deps` keys, `middleware` module, limits).
- `docs/ux/03-structure/ui-contracts.openapi.yaml`, `apps/web/package.json`, `apps/web/scripts/paths.mjs`,
  `apps/web/src/api/types.gen.ts`, `apps/web/src/api/contract.gen.json`, `apps/web/node_modules/.bin/openapi-typescript`,
  `apps/web/node_modules/openapi-typescript/package.json`, `docs/plans/ux-join/selectors.md` (when it exists), the UX dump
  file it names.

### Owned by others — must not touch

`tests/api/**`, `tests/journeys/support/**` (AEA-57), `tests/journeys/affected.py`, `tests/conftest.py`, `tests/fakes/**`,
`tests/contract/cases/*.py` and `tests/contract/cases/__init__.py`, `tests/contract/test_{retrieval,trace_sink}_contract.py`,
`pyproject.toml`, `uv.lock`, anything under `src/`, `apps/web/**`, `docs/ux/**`, `docs/archive/`, `docs/parked/`, `eval/**`,
the briefing and issued data.

---

## 3. Requirements table

The ticket's 19 criteria are verbatim at `docs/plans/tickets/AEA-59.md` lines 181–199 (identical to the issue). Each is
restated here in short. Every check command is run from the repository (or worktree) root.

| ID | Requirement (short) | How it is built | Verified by |
|---|---|---|---|
| AC-1 | Every operationId has exactly one case across `tests/contract/cases/*.py`; count read from `load_contract()`; each missing id named with its route file; strict fails on missing | `openapi_cases.completeness()` + operation → file map (§5 step 3) | `tests/contract/test_openapi_server.py::test_every_operation_has_a_case`, the same with `CONTRACT_STRICT=1`, and (plan-added, replaces the scratch run) `::test_completeness_names_a_removed_case` |
| AC-2 | Each registered + bound operation's success response from the real app passes `assert_response_matches` (SSE: `assert_sse_frames_match`), per named request example; `app.dependency_overrides` empty | `openapi_driver.real_app()` + `run_drive()` over every 2xx drive | `::test_success_matches_contract[<op>/<drive>]` |
| AC-3 | 401 `UNAUTHENTICATED` with no cookie for every op except `login`; `login` 401 `LOGIN_FAILED` to a wrong pair; 400 `VALIDATION_ERROR` for a malformed body on every op that documents 400 and takes a body | Runner-generated drives (§5 step 7) | `::test_unauthenticated_matches_contract[<op>]`, `::test_validation_error_matches_contract[<op>]` |
| AC-4 | Only two skip reasons: `route not registered: <operationId>` and `not bound: <name>`; strict turns both into failures | `openapi_driver.blocked()`; route check before preconditions; exception tap (§5 step 5) | `uv run pytest tests/contract/test_openapi_server.py -rs` and `CONTRACT_STRICT=1 …` |
| AC-5 | Examples read as YAML 1.2: `STARTED` `greeting.at` is the str `2026-10-16T14:20:00-05:00`; `BURNING_CHECK` option `"yes"`; `getStaffing` 200 names `ON`, `OFF` | Asserts on `load_document()` (AEA-23's `ContractLoader`) | `tests/contract/test_openapi_fixtures.py::test_examples_read_as_yaml_1_2` |
| AC-6 | All named response examples (250) pass; both SSE `FRAMES` pass; statuses with no example listed (exactly `logout 204`) | `iter_response_examples()` + `fake_response()` | `::test_named_examples_match[<op>/<status>/<name>]`, `::test_statuses_without_examples_have_no_body` |
| AC-7 | Allowed variants pass; counts per kind printed and each above zero | `body_variants()` + error bodies | `::test_edge_variants_accepted`. **Deviation, measured:** the contract marks every response property `required` (135 response-reachable object schemas, 0 optional; planner scan 2026-10-21). So the *omitted-optional* count is 0 by the contract, not by the generator. The test asserts `omitted > 0 or optional_response_properties() == []` and prints the scan. *Required-omitted* counter-variants (AC-8) give the omit kind its discrimination (§8 R-4) |
| AC-8 | Counter-variants rejected: null where not allowed, `[]` under `minItems ≥ 1`, unknown `error.code`, undocumented status; count > 0 | Counter kinds in `body_variants()` + per-op status 418 + per-status bad code | `::test_counter_variants_rejected` |
| AC-9 | `apps/web/src/api/contract.gen.json` agrees with the OpenAPI; a mismatch names the operation and `npm run examples` | Field-by-field compare (§5 step 10) | `::test_contract_index_matches_openapi` (measured 2026-10-21: agrees) |
| AC-10 | Every `tests/fixtures/api/<operationId>.<status>.<name>.json` passes; unknown op or undocumented status fails | `check_api_fixtures(folder)` | `::test_api_fixtures_match` (0 files today) and (plan-added, replaces the scratch file) `::test_api_fixture_names_refused` |
| AC-11 | `types.gen.ts` equals a fresh generation; difference fails naming the file and `npm run gen:types` | Pinned binary, `tmp_path`, byte compare | `tests/contract/test_types_gen_drift.py::test_types_gen_is_current` and (plan-added, replaces the scratch run) `::test_types_gen_detects_drift` |
| AC-12 | Missing binary or version ≠ exact pin → fail naming path and both versions; never installs or skips; no `npm` process | `check_pinned_binary()` on temp doubles + subprocess spy | `::test_refuses_missing_or_unpinned_binary` |
| AC-13 | Nothing under `apps/web` written; `.tmp/` state unchanged; only the `openapi-typescript` binary executed | Snapshot (path, size, SHA-256) before/after + recording spy | `::test_apps_web_untouched` |
| AC-14 | Generated password, cookie value, six-digit code absent from the `AssertionError` text, captured output and the evidence record; failure still names op, status and pointer | Three broken bodies (§5 step 11) | `tests/contract/test_openapi_fixtures.py::test_failure_messages_carry_no_values`. **Fails on today's AEA-23 helper** (measured: `"… at session/role: 'pwzq…' is not one of […]"`). See §8 R-1 |
| AC-15 | No outbound connection, no paid call, never opens `eval/` | Socket guard (autouse in the server module) + open spy | `::test_no_outbound_connections` (server file), `::test_never_reads_eval` (fixtures file) |
| AC-16 | J-1 through AEA-57's harness: every response passes its operationId; journey assertions still pass | **blocked-on AEA-57** (§8 R-2): placeholder file with one skipped `journey` test | `uv run pytest tests/journeys/j1/test_aea_59.py -m journey -rs` → 1 skipped, reason names AEA-57 |
| AC-17 | UX dev-fixture dump checked when `selectors.md` names it; else skipped `ux fixture dump missing: <path>`; strict fails | `ux_dump_path()` + validation | `uv run pytest tests/contract/test_openapi_fixtures.py -k ux_dump -rs` → skipped today (no `selectors.md`) |
| AC-18 | Runner collects `tests/contract/cases/*.py`; writes the runner, case format and one documented example case; per-file counts printed; missing ids listed with their file | `openapi_cases.load_case_files()`; `cases/README.md` example | `::test_every_operation_has_a_case -rsP`, `::test_case_files_are_well_formed`, `::test_case_format_example_is_valid` |
| AC-19 | Context rows + evidence record; nothing under `apps/web/**`, `docs/ux/**`, `eval/` | §5 steps 13–14 | `git diff --name-only main...HEAD` |

**Obligations from the sources that the ticket states only indirectly (reconciliation):**

| Obligation | Source | Disposition | Where |
|---|---|---|---|
| No second response validator; jsonschema used only to *pick* a `oneOf` member while walking an example | integrated-journeys §6; ticket "No second validator is written" | in-ticket | §5 step 9; every verdict comes from `assert_response_matches` |
| Precondition responses (login, role switch, start session, …) also pass `assert_response_matches` | ticket "Every response a case receives goes through…" | added | §5 step 6 |
| Failure text from the runner never prints a response body (bodies of `listDemoInbox` carry a code) | DO-4 §0; ticket AC-14 spirit | added | §5 step 6 (messages carry status and error code only) |
| Generated values are letters-only or runtime-random; no literal code, card-like number or phone number | ticket conventions | in-ticket | §6 |
| Drift check works inside a backend worktree (no `node_modules` there, and none may be installed) | task constraint "no node_modules in a backend worktree" | added | §5 step 12 (binary from the primary checkout, pure-file lookup) |
| `resetDemo` runs on its own app instance | ticket server part | in-ticket | every drive gets its own app (§5 step 4) |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

---

## 4. Shared code to use (copied from `main` `4a76850`)

### `tests/api/openapi_check.py` (AEA-23; the only validator)

```python
CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "ux" / "03-structure" / "ui-contracts.openapi.yaml"
CONTRACT_URI = "urn:meridian:ui-contracts"
class ContractLoader(yaml.SafeLoader): ...          # YAML 1.2 style; load_document() uses it
@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    method: Literal["get", "post", "put", "patch", "delete"]
    path_template: str
    responses: Mapping[str, Mapping[str, JsonValue]]  # status -> {content type -> {"$ref": CONTRACT_URI + "#" + quoted pointer}}; {} when no content
    event_schema: str | None                          # "ChatEvent" / "CaseEvent" for the two SSE operations
@dataclass(frozen=True)
class Contract:
    source: Path; version: str; operations: Mapping[str, OperationSpec]; error_codes: frozenset[str]; registry: Registry[Any]
@dataclass(frozen=True)
class SseFrame:
    event: str | None; id: str | None; data: str
@functools.cache
def load_document() -> Mapping[str, Any]: ...       # the whole OpenAPI, read with ContractLoader
@functools.cache
def load_contract() -> Contract: ...
def assert_response_matches(response: _ResponseLike, operation_id: str) -> None: ...
    # _ResponseLike: .status_code: int, .headers (get + `in`), .content: bytes, .json()
    # Checks: status documented; content type documented (when a body is documented); body schema (FormatChecker);
    # X-Request-ID header present; for {"error": …} bodies: code in Contract.error_codes AND body request_id == header.
def assert_sse_frames_match(frames: Sequence[SseFrame], operation_id: str) -> None: ...
def operations_documenting(status: str) -> frozenset[str]: ...
```

Response schemas in `OperationSpec.responses` are `{"$ref": "urn:meridian:ui-contracts#<pointer>"}` where `<pointer>` is
percent-encoded with `urllib.parse.quote(pointer, safe="/~")` (`{`→`%7B`). Decode with `urllib.parse.unquote`.
**Do not import** `_FORMATS`, `_fail` or any other underscore name.

### `tests/api/web_shell_support.py` (AEA-23)

```python
SESSION_COOKIE_NAME = "mhc_session"
def rand_word(length: int = 16, prefix: str = "zq") -> str: ...        # letters only
def make_settings(tmp_path: Path, **changes: Any) -> Settings: ...     # generated demo pair, session secret, provider keys;
    # data_dir=tmp_path/"data", index_dir=tmp_path/"index", web_dist_dir=tmp_path/"no-dist", require_frontend=False;
    # reads nothing from the environment. eval_key stays None (run_tag "live").
def demo_pair(settings: Settings) -> dict[str, str]: ...               # {"username": …, "password": …}
def make_client(app: FastAPI, *, peer: str = "198.51.100.7") -> TestClient: ...
    # TestClient(app, client=(peer, 50000), follow_redirects=False, raise_server_exceptions=False); use as a context manager
def cookie_header(token: str) -> dict[str, str]: ...                   # {"Cookie": "mhc_session=<token>"}
def session_cookie_value(response: Any) -> str | None: ...             # token from the response's Set-Cookie
def effective_routes(app: FastAPI) -> list[RouteInfo]: ...             # flattens included routers (app.routes alone does not)
@dataclass(frozen=True)
class RouteInfo:
    path: str; methods: frozenset[str]; operation_id: str | None; endpoint: Callable[..., Any] | None   # methods upper-case, no HEAD/OPTIONS
```

### `tests/api/events_support.py` (AEA-41)

```python
def payload(event_type: str) -> dict[str, JsonValue]: ...   # deep copy of PAYLOADS[event_type]; keys: representative_joined,
    # ai_paused, staff_message, ai_resumed, chat_closed, demo_reset
def append_stored(uow: UnitOfWorkFactory, stream: str, items: Sequence[tuple[str, dict[str, JsonValue]]], *,
                  at: datetime = WP2_JOINED_AT) -> list[int]: ...   # appends through the real repos, returns event ids
def parse_sse_text(text: str) -> list[SseFrame | str]: ...  # str items are comments (": heartbeat")
```

### `tests/services/person_request_support.py` (AEA-42) and `tests/fixtures/sqlite.py` (AEA-10)

```python
def verify_thread(store: TempStore, thread_id: ThreadId, *, now: datetime = NOW) -> None: ...
    # inserts identity_threads(status 'verified', customer MHC-10002) + a VERIFIED action through store.uow
@dataclass(frozen=True)
class TempStore:
    data_dir: Path; db_path: Path; issued_path: Path; uow: SqliteUnitOfWorkFactory
ISSUED_DB: Path   # absolute path of the issued meridian_scheduling.sqlite
```

### Product code (import only)

```python
from meridian.web.app import ContainerOverrides, create_app
def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> FastAPI: ...
    # the lifespan builds the container (routers are included DURING the lifespan, so list routes after `with client:`)
import meridian.web.middleware as middleware_module   # tap target: middleware_module.render_unhandled_error
    # GateMiddleware catches every route/dependency exception raised before the response starts and calls
    # render_unhandled_error(request_id) inside its `except Exception` block (middleware.py lines 517–521), so
    # sys.exc_info()[1] there is the exception. The 500 body is only {"request_id": …}.
from meridian.web.deps import RESET_GATE, UOW_FACTORY  # Key[ResetGate] "reset_gate", Key[UnitOfWorkFactory] "uow_factory"
    # read via run.app.state.container.get(KEY)
from meridian.services.reset_gate import ResetGate    # .hold() -> context manager; .held() -> bool
from meridian.policy.limits import WebLimits          # WebLimits().login_rejects_per_ip == 10
from meridian.adapters.sqlite.migrate import WORKING_DB_NAME   # "meridian.sqlite"
from meridian.domain.common import ThreadId
```

`Settings.issued_db_path` defaults to a **relative** path. Always pass `issued_db_path=ISSUED_DB`
(`tests/fixtures/sqlite.py`) to `make_settings`.

### Facts measured on `main` `4a76850` (planner scratch runs, not committed)

- `create_app(make_settings(tmp))` inside `make_client(app)` → `POST /api/login` = 500. The tap shows
  `RuntimeError: not bound: get_login_sessions`. A cookie-less `GET /api/chat/sessions/<uuid>` behaves the same, because the
  middleware calls `get_login_sessions` first.
- Registered operations today: `advanceDemoClock`, `login`, `logout`, `requestPerson`, `saveFollowUp`, `streamChatEvents`.
- 250 named response examples; all pass `assert_response_matches` when wrapped with `X-Request-ID = body["request_id"]`
  (when present) else a fresh id. One documented status with no example: `logout 204` (no body).
- Variant counts from a pointer-based walker:

  | Kind | Count | Verdict |
  |---|---|---|
  | null allowed | 710 | all pass |
  | empty list allowed | 324 | all pass |
  | null where not allowed | 1,433 | all fail |
  | `[]` below `minItems` | 7 | all fail |
  | required property omitted | 1,437 | all fail |
  | error-code bodies (95 error statuses × 22 codes) | 2,090 | all pass |
  | unknown code, one per error status | 95 | all fail |

  Runtime ≈ 5 s.
- Every documented error status (95) uses exactly `#/components/schemas/ApiError`.
- `contract.gen.json` agrees with the OpenAPI field by field.
- `openapi-typescript` 7.13.0 output from a temp cwd with absolute paths is byte-equal to `types.gen.ts`.
- `apps/web` outside `node_modules`: 497 files, 4.3 MB. `apps/web/.tmp/` **already exists**.

---

## 5. Steps (build order; each step ends with something you can run)

> Environment for every command: `export UV_LINK_MODE=hardlink`. Run from the worktree root. Never `npm`, `npx`,
> `uv add`, or a copied venv. `pytest -n 2` at most (these files run fine serially).

### Step 1 — `tests/contract/openapi_variants.py`: document pointers and examples

Module docstring: one paragraph on what the module does, plus the rule "every verdict comes from `assert_response_matches`;
jsonschema is used here only to choose which `oneOf`/`anyOf` member an example instance matches".

```python
REPO_ROOT: Final = Path(__file__).resolve().parents[2]
STRICT_ENV: Final = "CONTRACT_STRICT"

def contract_strict() -> bool:                          # read only by tests/contract/*; never by src/
    return os.environ.get(STRICT_ENV) == "1"

def pointer_of(ref: str) -> str:
    """'urn:meridian:ui-contracts#/a/b%7Bx%7D' or '#/a/b' -> '/a/b{x}' (unquoted JSON pointer)."""
def node_at(pointer: str) -> Any:
    """Walk load_document() by a JSON pointer ('' is the root); '~1' -> '/', '~0' -> '~'; list parts are ints."""
def deref(pointer: str) -> tuple[str, Any]:
    """Follow $ref chains from the node at `pointer` (both ref forms); return (final pointer, node). Bound: 30 hops."""
def ref_schema(pointer: str) -> dict[str, str]:
    return {"$ref": CONTRACT_URI + "#" + quote(pointer, safe="/~")}
def resolve(node: Any) -> Any:
    """Follow '#/…' $ref chains on a document node (responses, requestBodies, examples)."""

@dataclass(frozen=True)
class NamedExample:
    operation_id: str
    status: str            # "200", "401", …
    content_type: str      # "application/json" or "text/event-stream"
    name: str
    value: JsonValue
    schema_pointer: str    # pointer_of(contract.operations[op].responses[status][content_type]["$ref"])
    @property
    def id(self) -> str: return f"{self.operation_id}/{self.status}/{self.name}"

def iter_response_examples() -> list[NamedExample]:
    """Every named response example, in document order: for each path, method in ('get','post','put','patch','delete')
    with an operationId, each status in op['responses'], response = resolve(raw), each content type in
    response.get('content') or {}, each name in media.get('examples') or {}, value = resolve(example)['value']."""

def statuses_without_examples() -> list[tuple[str, str, bool]]:
    """(operationId, status, documents_a_body) for each documented status none of whose content types has an example."""

def request_examples(operation_id: str) -> dict[str, JsonValue]:
    """{name: deep copy of resolve(example)['value']} for the op's application/json requestBody examples; {} when none."""

def fake_response(status: str | int, content_type: str | None, body: JsonValue | None) -> httpx.Response:
    """httpx.Response with the status, `content-type` (omitted when None) and X-Request-ID set to body['request_id']
    when body is a dict with a str request_id, else 'req-' + uuid4().hex; content = json.dumps(body).encode() or b''
    when body is None."""

def sse_frames(text: str) -> list[SseFrame]:
    """[item for item in parse_sse_text(text) if isinstance(item, SseFrame)] (events_support.parse_sse_text)."""
```

Check: `uv run python -c "from tests.contract.openapi_variants import iter_response_examples as f; print(len(f()))"` → `250`.

### Step 2 — `tests/contract/openapi_variants.py`: the edge-variant generator

```python
ALLOWED_KINDS: Final = ("omitted", "null", "empty")
COUNTER_KINDS: Final = ("required_omitted", "null_not_allowed", "empty_below_min_items")

@dataclass(frozen=True)
class Variant:
    kind: str                         # one of ALLOWED_KINDS + COUNTER_KINDS
    path: tuple[str | int, ...]       # JSON path inside the body ("" root never used for omit/null)
    body: JsonValue                   # the mutated deep copy
    @property
    def allowed(self) -> bool: return self.kind in ALLOWED_KINDS

def body_variants(example: NamedExample) -> list[Variant]: ...
def optional_response_properties() -> list[str]: ...
```

Algorithm for `body_variants`. Walk the example **by document pointer**, never by resolved dicts: a resolved sub-schema
loses its base URI, and nested `#/…` refs then fail with `PointerToNowhere`. The planner hit exactly this.

1. `views(ptr, inst) -> list[str]`: `ptr, node = deref(ptr)`. The result is `[ptr]`, plus, recursively, `views(f"{ptr}/allOf/{i}", inst)`
   for every `allOf` member, plus, for `k in ("oneOf", "anyOf")`, `views(f"{ptr}/{k}/{i}", inst)` for each member whose
   `Draft202012Validator(ref_schema(f"{ptr}/{k}/{i}"), registry=load_contract().registry).is_valid(inst)` is true.
   *Invariant: only members the example actually matches contribute properties, so a variant is judged against the branch
   the UI would render.*
2. `admits_null(ptr) -> bool`: `ptr, node = deref(ptr)`. True when:
   - `node` is not a dict;
   - `type == "null"`, or `"null"` is in a `type` list;
   - `const is None`;
   - `None` is in `enum`;
   - any `oneOf`/`anyOf` member admits null, or every `allOf` member does;
   - `node` has none of `type`, `properties`, `items`, `enum`, `const`, `oneOf`, `anyOf`, `allOf`, `$ref` (unconstrained).

   Otherwise false.
3. `walk(ptr, inst, path, out)`, case 1, `inst` is a dict:
   1. Merge, over `views(ptr, inst)`, `properties` (first pointer wins: `f"{view}/properties/{escaped name}"`, escaping `~`→`~0`, `/`→`~1`) and the union of `required`.
   2. If any present key is required, append **one** `required_omitted` (the first required key in instance order).
   3. For each present key with a known property pointer:
      - not required → append `omitted`;
      - value is not `None` and `admits_null(prop)` → append `null`;
      - value is not `None`, not `admits_null(prop)`, and no `null_not_allowed` has been added for this object yet → append **one** `null_not_allowed`.
   4. Recurse into the value.
4. `walk(ptr, inst, path, out)`, case 2, `inst` is a list. Take the first view whose node has `items`. If `inst` is non-empty, append `empty` (when `minItems` is absent or 0) or `empty_below_min_items` (when `minItems ≥ 1`), and recurse into each item with `f"{view}/items"`.
5. Apply each `(kind, path)` to a `copy.deepcopy(example.value)`: `*_omitted` → `del`; `null*` → `None`; `empty*` → `[]` (path `()` → the whole body becomes `[]`).
6. Start pointer: `example.schema_pointer`. SSE examples (`content_type == "text/event-stream"`) get **no** variants: their value is frame text.

`optional_response_properties()`: walk every response schema pointer of every operation, following `$ref`, `properties/*`,
`items`, `allOf/i`, `oneOf/i`, `anyOf/i` and `contentSchema`, with a visited set. Return sorted
`f"{pointer}/{name}"` for every property not in its object's `required`. **Expected today: `[]` (135 object schemas visited).**

Check: `uv run python -c "from tests.contract.openapi_variants import *; from collections import Counter; print(Counter(v.kind for e in iter_response_examples() for v in body_variants(e)))"`. Expect counts near §4's facts (null ≈ 710, empty ≈ 324, null_not_allowed ≈ 1433, empty_below_min_items ≈ 7, required_omitted ≈ 1437, omitted 0).

### Step 3 — `tests/contract/openapi_cases.py`: case files, vocabulary, static checks, completeness

```python
CASES_DIR: Final = Path(__file__).resolve().parent / "cases"
README_PATH: Final = CASES_DIR / "README.md"

@dataclass(frozen=True)
class CaseFile:
    stem: str                                   # "auth", "events", …
    route_file: object                          # the module's ROUTE_FILE (must equal stem)
    cases: Mapping[str, Mapping[str, Any]]      # the module's CASES

def load_case_files() -> list[CaseFile]:
    """importlib.import_module(f"tests.contract.cases.{p.stem}") for every p in sorted(CASES_DIR.glob('*.py'))
    except __init__.py and names starting with '_'. A module without CASES/ROUTE_FILE gets cases={} and route_file=None
    (the static check reports it)."""
```

**Operation → route file** (from `api-con-mapping.md`; derived from the operation's `x-con`, so no operationId is hard-coded):

```python
ROUTE_FILE_BY_CON: Final[Mapping[str, str]] = MappingProxyType({
    "CON-1": "chat", "CON-2": "chat", "CON-3": "events", "CON-4": "handoff", "CON-5": "handoff",
    "CON-6": "demo", "CON-7": "demo", "CON-8": "demo", "CON-9": "demo", "CON-10": "staff_session",
    "CON-11": "staff_cases", "CON-12": "staff_cases", "CON-13": "staff_cases", "CON-14": "staff_live",
    "CON-15": "staff_cases", "CON-16": "staff_cases", "CON-17": "staff_cases", "CON-18": "reads",
    "CON-19": "reads", "CON-20": "reads", "CON-21": "staff_live", "CON-22": "auth",
})
ROUTE_FILE_OVERRIDES: Final[Mapping[tuple[str, str], str]] = MappingProxyType({("CON-8", "post"): "staff_clock"})

def operation_node(operation_id: str) -> Mapping[str, Any]: ...  # load_document()["paths"][spec.path_template][spec.method]
def expected_route_file(operation_id: str) -> str:
    """override by (x-con, method), else ROUTE_FILE_BY_CON[x-con], else f'<no route file for {x-con}>'."""
def is_public(operation_id: str) -> bool:
    return operation_node(operation_id).get("security") == []    # only `login` today
def staff_role_for(operation_id: str) -> str | None:
    """roles = [str(e).split()[0] for e in x-roles] (missing x-roles -> all four). None when 'customer' is in roles,
    else roles[0] (e.g. getOwnerMetrics -> 'owner', advanceDemoClock -> 'supervisor')."""
```

**Vocabulary.** The route files on `main` and in flight use different words for the same step. The runner maps each one to a
canonical step, and `cases/README.md` documents the canonical words for every later route ticket.

```python
PRECONDITIONS: Final[Mapping[str, str]] = MappingProxyType({   # word -> canonical step
    "login": "login",
    "thread": "thread", "started_thread": "thread", "start_thread": "thread",
    "open_case": "open_case",
    "verified": "verified",
    "ended": "ended",
    "unknown": "unknown",
    "role:customer": "role:customer", "role:representative": "role:representative",
    "role:supervisor": "role:supervisor", "role:owner": "role:owner",
    "as_customer": "role:customer", "as_representative": "role:representative",
    "as_supervisor": "role:supervisor", "as_owner": "role:owner",
})
SETUPS: Final[Mapping[str, str]] = MappingProxyType({
    "login_rejects_exhausted": "login_rejects_exhausted",
    "reset_held": "reset_held", "reset_gate_held": "reset_held",
    "other_session_thread": "other_session_thread",
    "ended_thread": "ended",
})
LOCAL_DRIVER_ONLY: Final[Mapping[str, str]] = MappingProxyType({   # setups the real app cannot produce without a double
    "handoff_fails": "needs a failing HandoffService double; proved by the route's local driver (mock-tested)",
    "turn_running": "needs a turn left running mid-request; proved by the route's local driver (mock-tested)",
})
PATH_WORDS: Final = frozenset({"started", "unknown", "malformed", "other_session", "ended", "seeded_case"})
MALFORMED_THREAD_ID: Final = "thr_9d41"
ALLOWED_DRIVE_KEYS: Final = frozenset({"name", "status", "code", "preconditions", "setup", "body", "path", "thread",
                                       "events", "last_event_id", "frames", "response_example"})
# "response_example" is checked by the route's own driver; the runner ignores it.
```

```python
@dataclass(frozen=True)
class Drive:
    operation_id: str
    file: str                                   # route file stem
    spec: Mapping[str, Any]                     # the drive dict as written
    @property
    def id(self) -> str: return f"{self.operation_id}/{self.spec.get('name', '?')}"
    @property
    def status(self) -> int: return int(self.spec["status"])

def all_drives(files: Sequence[CaseFile]) -> list[Drive]: ...      # file order, then op order, then drive order
def local_driver_reason(drive: Drive) -> str | None:               # LOCAL_DRIVER_ONLY[setup] or None
def check_cases_mapping(cases: Mapping[str, Mapping[str, Any]], where: str) -> list[str]: ...
def case_file_problems(files: Sequence[CaseFile]) -> list[str]: ...
def completeness(files: Sequence[CaseFile]) -> tuple[dict[str, list[str]], list[str], list[str]]: ...
    # (found ids per file stem, missing lines "op → tests/contract/cases/<file>.py", unknown-id lines)
def missing_operations(found_ids: Iterable[str]) -> list[str]: ...  # pure: sorted(set(contract ops) - found), each as
    # f"{op} → tests/contract/cases/{expected_route_file(op)}.py"
```

`check_cases_mapping` returns one problem string per violation (prefix `where`, then `op/drive`). The checks, in order:
1. `cases` is a dict; each key is in `load_contract().operations`. Otherwise: `case for unknown operationId <op>`.
2. Each value has `public` (bool) equal to `is_public(op)`, and `drives` (a non-empty tuple or list of dicts).
3. Each drive's keys are a subset of `ALLOWED_DRIVE_KEYS`. `name` matches `^[a-z0-9_]+$` and is unique within the op.
   `str(status)` is in `spec.responses`.
4. `code`, when present, is in `contract.error_codes` and `status >= 400`.
5. `preconditions` is a tuple or list. Each word is in `PRECONDITIONS`.
6. `setup`, when present, is in `SETUPS` or `LOCAL_DRIVER_ONLY`.
7. `body` is `None`, or a dict with exactly one of `example`, `raw`, `text`.
   - `example` must be in `request_examples(op)`.
   - `credentials`, when present, must be in `("configured", "wrong_password")` and comes only with `example`.
   - `turn_id`, when present, must be `"new"` and comes only with `example`.
8. `path`, when present, is a dict whose keys are path parameters of `spec.path_template` (regex `\{(\w+)\}`). `thread` is accepted only when the template has `{thread_id}`.
9. `events`, when present, is allowed only for `streamChatEvents`, needs a thread precondition, and every element is a key of `events_support.PAYLOADS`. Import the dict, read only.
10. `last_event_id` is `None` or `{"after_event": n}` with `1 <= n <= len(events)`.
11. `frames` (int ≥ 1) is required when `spec.event_schema` is set and the status is 200. The **last** seeded event must then be `chat_closed` or `demo_reset`, so the stream ends.
12. Coverage:
    - at least one drive per op has a 2xx status;
    - every name in `request_examples(op)` appears as `body.example` in at least one 2xx drive. Otherwise: `request example <NAME> has no success drive`.

`case_file_problems` returns these, in order:
- `ROUTE_FILE != stem`;
- a missing `CASES`;
- every `check_cases_mapping` problem;
- an operationId that appears in more than one file;
- an op in the wrong file, `expected_route_file(op) != stem`.

The last one exists to keep ownership honest.

Check: `uv run python -c "from tests.contract.openapi_cases import *; print(case_file_problems(load_case_files()))"`
→ `[]` on `main` (auth, events, handoff, staff_clock). If it is not empty, read the problem. A problem is a defect in a
route file only when the route file breaks its **own** documented vocabulary. Otherwise the runner's vocabulary is
missing a word, so fix this module, never a route file.

### Step 4 — `tests/contract/openapi_driver.py`: launcher, exception tap, socket guard

```python
STREAM_READ_TIMEOUT_S: Final = 5.0
GUARD_MESSAGE: Final = "AEA-59 socket guard: non-loopback connect refused"

def blocked(reason: str) -> NoReturn:
    """pytest.fail(reason) when contract_strict() else pytest.skip(reason). The only two reasons ever passed:
    'route not registered: <operationId>' and the verbatim 'not bound: …' message."""

def install_exception_tap(monkeypatch: pytest.MonkeyPatch) -> list[BaseException]:
    """Replace meridian.web.middleware.render_unhandled_error with a wrapper that appends sys.exc_info()[1] (when not
    None) to the returned list, then returns the original's JSONResponse unchanged. Behaviour of the app is unchanged;
    this only observes."""

def install_socket_guard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Patch socket.socket.connect, socket.socket.connect_ex and socket.getaddrinfo. For AF_INET/AF_INET6 addresses
    whose host is not loopback ('127.*', '::1', 'localhost'), append the host to the returned list and raise
    ConnectionRefusedError(GUARD_MESSAGE) (getaddrinfo: socket.gaierror(GUARD_MESSAGE)). AF_UNIX and loopback pass
    through to the saved originals."""

@dataclass
class AppRun:
    app: FastAPI
    client: TestClient
    settings: Settings
    registered: frozenset[tuple[str, str]]       # {(method lower, path template)} from effective_routes(app)
    taps: list[BaseException]
    main_token: str | None = None
    main_thread: str | None = None
    other_thread: str | None = None
    event_ids: list[int] = field(default_factory=list)

@contextmanager
def real_app(tmp_path: Path, taps: list[BaseException]) -> Iterator[AppRun]:
    settings = make_settings(tmp_path, issued_db_path=ISSUED_DB)
    app = create_app(settings)                    # no overrides (see §8 R-3)
    with make_client(app) as client:
        assert not app.dependency_overrides, "the contract runner never overrides a dependency"
        registered = frozenset((m.lower(), r.path) for r in effective_routes(app) for m in r.methods)
        yield AppRun(app, client, settings, registered, taps)
```

*Invariants.*
- One fresh app, data dir and first-boot DB copy per test item, so `resetDemo` and rate-limit state never leak between drives.
- No `dependency_overrides`.
- The real middleware, login, gate, rate limiter and persistence run.

### Step 5 — `openapi_driver.py`: sending a request and reading its outcome

```python
def send(run: AppRun, operation_id: str, *, path: str, token: str | None, body: Mapping[str, Any] | None,
         extra_headers: Mapping[str, str] | None = None) -> httpx.Response-like:
```
Steps, in order:
1. `spec = load_contract().operations[operation_id]`. If `(spec.method, spec.path_template) not in run.registered`, call
   `blocked(f"route not registered: {operation_id}")`.
2. Build the headers: `cookie_header(token)` when `token` is given, plus `extra_headers`.
3. Build the body:
   - `{"raw": v}` → `json=v`;
   - `{"text": s}` → `content=s` plus `Content-Type: application/json`;
   - `{"json": v}` (internal form produced by step 6) → `json=v`;
   - `None` → no body.
4. Remember `n = len(run.taps)`. Call `run.client.request(spec.method.upper(), path, headers=…, …)`, then **always**
   `run.client.cookies.clear()`, because tokens travel only as explicit headers.
5. If the status is 500 and `len(run.taps) > n`, take `exc = run.taps[-1]`.
   - If `isinstance(exc, RuntimeError)` and `str(exc).startswith("not bound: ")`, call `blocked(str(exc))`.
   - Otherwise `pytest.fail(f"{operation_id}: unhandled {type(exc).__name__} (500)")`. Never print `str(exc)` here,
     because it may hold a value.
6. Return the response.

*Invariant:* a failure message names the operation, the drive and the status, plus `error.code` when the body is an
`ApiError`. It **never** includes a response body.

### Step 6 — `openapi_driver.py`: preconditions, path, body, main request (`run_drive`)

`def run_drive(run: AppRun, drive: Drive) -> str` returns a one-line evidence string such as `advanceDemoClock/next_morning: 200`.
Run the steps in this order.

1. `op = drive.operation_id`, `spec = …`, `d = drive.spec`.
   - `words = [PRECONDITIONS[w] for w in d["preconditions"]]`.
   - `setup = SETUPS.get(d.get("setup", ""))`. A local-driver-only drive is never passed here (step 8 filters it).
2. **Main route first:** if `(spec.method, spec.path_template) not in run.registered`, call
   `blocked(f"route not registered: {op}")`.
3. **Session.** A session is needed when any word is not in `{"unknown"}`, or when setup is `"ended"` or `"other_session_thread"`.
   - Post `login` (CON-22) with `demo_pair(run.settings)`, with no token. Expect 200 and `assert_response_matches(r, "login")`.
   - Read `run.main_token = session_cookie_value(r)`; assert it is not None.
   - Any other status fails with `precondition login answered <status>`.

   Every precondition call below goes through `send()` (so `route not registered` and `not bound` apply), checks its
   expected status, then calls `assert_response_matches`.
4. **Role:** for a word `role:<r>`, PUT `switchRole` with `json=request_examples("switchRole")[r.upper()]` and the main
   token. Expect 200.
5. **Thread:** when the words include `thread`, `verified`, `open_case` or `ended`, POST `startChatSession` with no body
   and the main token. Expect 201. Then `run.main_thread = r.json()["thread_id"]`.
6. **Verified:** when the words include `verified`, seed the working copy:
   `verify_thread(TempStore(data_dir=Path(run.settings.data_dir), db_path=Path(run.settings.data_dir) / WORKING_DB_NAME,
   issued_path=ISSUED_DB, uow=run.app.state.container.get(UOW_FACTORY)), ThreadId(run.main_thread))`.
7. **Open case:** when the words include `open_case`, POST `requestPerson` on the main thread with
   `json={**request_examples("requestPerson")["BUTTON"], "turn_id": str(uuid.uuid4())}` and the main token. Expect 200.
8. **Ended:** when the words or setup include `ended`, POST `resetDemo` with `json=request_examples("resetDemo")["CONFIRM"]`
   and the main token. Expect 200. The main thread now answers 410 to its owner.
9. **Other session:** when setup is `other_session_thread`, post a second `login`, take its token, and POST
   `startChatSession` with it. Expect 201. Then `run.other_thread = thread_id`.
10. **Login throttle:** when setup is `login_rejects_exhausted`, post `login` `WebLimits().login_rejects_per_ip` times with
    `{"username": pair["username"], "password": rand_word(14, "pw")}`. Expect 401 each time.
11. **Events seed:** when `d` has `events`:
    `run.event_ids = append_stored(run.app.state.container.get(UOW_FACTORY), run.main_thread, [(k, payload(k)) for k in d["events"]])`.
12. **Path parameters:** for each `{param}` in `spec.path_template`, take
    `value = d.get("path", {}).get(param)`, or `d.get("thread")` when `param == "thread_id"`. Resolve it:
    - `"started"` and `"ended"` → `run.main_thread`. When that is None, fail: `path word needs a thread precondition`.
    - `"unknown"` → `str(uuid.uuid4())`.
    - `"malformed"` → `MALFORMED_THREAD_ID`.
    - `"other_session"` → `run.other_thread`.
    - `"seeded_case"` → `seeded_case_ref(run)`, defined below.
    - any other string → used literally.
    - `None` (not given) defaults by parameter:
      - `thread_id` → a fresh UUID when the words include `unknown`; else `run.main_thread`; else a fresh UUID;
      - `reference` → `seeded_case_ref(run)` when a session was made, else `"MHC-C-0001"`;
      - any other parameter (`flag_id`) → a fresh UUID.

    `seeded_case_ref(run)` opens `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)` and runs
    `SELECT case_ref FROM cases ORDER BY case_ref LIMIT 1`. When there is no row, it calls
    `blocked("not bound: demo seed (no row in cases; AEA-29/AEA-31 first-boot seed)")`.
13. **Body:**
    - `None` → no body;
    - `{"example": n}` → `v = request_examples(op)[n]`, then:
      - `credentials == "configured"` → `v.update(demo_pair(run.settings))`;
      - `credentials == "wrong_password"` → `v.update(username=pair["username"], password=rand_word(14, "pw"))`;
      - `turn_id == "new"` → `v["turn_id"] = str(uuid.uuid4())`;
      - then send `{"json": v}`;
    - `{"raw": v}` and `{"text": s}` pass through.
14. **Token on the main request:** `run.main_token` only when the **original** words include `login`; otherwise no cookie.
    The handoff `no_session` drives create a thread but send without a cookie.
15. **Extra headers:** `Last-Event-ID: str(run.event_ids[n - 1])` when `d.get("last_event_id") == {"after_event": n}`.
16. **Send:**
    - **SSE success:** when `spec.event_schema` is set and `drive.status == 200`, call
      `read_sse(run, url, headers, frames=d["frames"])` (step 7). Assert `status == 200`, that the `content-type` starts with
      `text/event-stream`, and that exactly `d["frames"]` frames arrived. Then `assert_sse_frames_match(frames, op)`.
    - **Otherwise:** call `send(...)`. When setup is `reset_held`, send inside
      `with run.app.state.container.get(RESET_GATE).hold():`.
17. **Verdict (non-SSE):**
    - `response.status_code == drive.status`. Message: `f"{drive.id}: expected {drive.status}, got {status}"`, plus
      `f" ({code})"` when the body is JSON with an `error.code`.
    - `d.get("code")` equals `body["error"]["code"]`.
    - `assert_response_matches(response, op)`.
    - Return the evidence line.

### Step 7 — `openapi_driver.py`: bounded SSE reader

```python
@dataclass(frozen=True)
class SseRead:
    status: int | None
    content_type: str
    frames: tuple[SseFrame, ...]
    error: BaseException | None

def read_sse(run: AppRun, path: str, headers: Mapping[str, str], *, frames: int,
             timeout_s: float = STREAM_READ_TIMEOUT_S) -> SseRead:
    """Run on the TestClient's own event loop: `portal = run.client.portal; assert portal is not None;
    return portal.call(_read_sse, run.app, path, dict(headers), frames, timeout_s)`."""
```

`_read_sse` is an `async def`. Copy the raw-ASGI pattern of `tests/api/events_support.open_stream`, but take the path and
headers as arguments:
- `scope`: `type`, `asgi`, `http_version "1.1"`, `method "GET"`, `scheme`, `path`, `raw_path`, `query_string b""`,
  `headers` (lower-case bytes, including `host: testserver` and `cookie: mhc_session=<token>` from the given headers),
  `client ("198.51.100.7", 50000)`, `server`, `state {}`.
- `receive`: the first call returns the request message; later calls wait for a `disconnect` event.
- `send`: records the status and headers on `http.response.start`, and pushes body bytes into a memory stream.
- `run()` wraps `await app(scope, receive, send)` in `try/except BaseException as exc: error = exc` and `finally: done.set()`.

Inside `async with anyio.create_task_group() as tg`, start `run`. Then, under `with anyio.move_on_after(timeout_s):`, keep
receiving chunks into a text buffer until one of these happens:
- the stream ends;
- `len(sse_frames(buffer.rsplit("\n\n", 1)[0] + "\n\n")) >= frames`.

After that, set the disconnect event, wait for `done` under `anyio.move_on_after(timeout_s)`, and cancel the task group.
Return the frames parsed from the complete blocks.

If `error` is a `RuntimeError` starting with `not bound: `, the caller calls `blocked(str(error))`. Any other error fails with
its type name. *Invariant: a stream that never ends costs at most `2 × timeout_s` and fails as "expected N frames,
got M". It never hangs the suite.*

### Step 8 — `tests/contract/test_openapi_server.py`

Module docstring: the three tests families, levels (`integrated with a scripted model` for drives — no model is reached
until AEA-51; `mock-tested (static)` for the file checks), the two skip reasons, `CONTRACT_STRICT=1`.

```python
FILES = load_case_files()
DRIVES = all_drives(FILES)
RUNNABLE = [d for d in DRIVES if local_driver_reason(d) is None and isinstance(d.spec.get("status"), int)]
SUCCESS = [d for d in RUNNABLE if 200 <= d.status < 300]
ROUTE_ERRORS = [d for d in RUNNABLE if d.status >= 300]
UNAUTH_OPS = sorted(op for op in load_contract().operations if not is_public(op))
VALIDATION_OPS = sorted(op for op, s in load_contract().operations.items()
                        if "400" in s.responses and "requestBody" in operation_node(op))

@pytest.fixture(autouse=True)
def socket_guard(monkeypatch) -> list[str]: return install_socket_guard(monkeypatch)
@pytest.fixture
def taps(monkeypatch) -> list[BaseException]: return install_exception_tap(monkeypatch)
```

| Test | Body |
|---|---|
| `test_case_files_are_well_formed` | `problems = case_file_problems(FILES)`; print each; `assert problems == []` (both modes) |
| `test_every_operation_has_a_case` | `found, missing, unknown = completeness(FILES)`. Print, per file, `f"cases/{stem}.py: {len(ids)} ({', '.join(ids)})"`. Print `f"missing ({len(missing)} of {len(load_contract().operations)}):"` and each line. Print `local-driver only:` with each `drive.id — reason`. Assert `unknown == []` always. When `contract_strict()`, `assert missing == []`, with all missing lines in the message |
| `test_completeness_names_a_removed_case` | `ids = [op for f in FILES for op in f.cases]`; take `removed = ids[0]` (`login` on main); `lines = missing_operations(set(ids) - {removed})`; assert a line starts with `removed` and ends with `f"tests/contract/cases/{expected_route_file(removed)}.py"` |
| `test_case_format_example_is_valid` | Read `README_PATH`. Take the text between the lines `<!-- example-case:start -->` and `<!-- example-case:end -->`, strip the fenced `python` lines, and take the text after the first `=`. `cases = ast.literal_eval(that)`. `assert check_cases_mapping(cases, "cases/README.md") == []` |
| `test_success_matches_contract[drive]` | `@pytest.mark.parametrize("drive", SUCCESS, ids=lambda d: d.id)`; `with real_app(tmp_path, taps) as run: print(run_drive(run, drive))` |
| `test_route_cases_match_contract[drive]` | Same over `ROUTE_ERRORS` |
| `test_unauthenticated_matches_contract[op]` | Parametrize over `["login", *UNAUTH_OPS]`. `login`: post `{"username": pair["username"], "password": rand_word(14, "pw")}` with no token; expect 401 `LOGIN_FAILED`. Others: path parameters filled with defaults for "no session" (`thread_id`/`flag_id` → fresh UUID, `reference` → `"MHC-C-0001"`), body = the first request example (`{"json": …}`) or `None`, no token; expect 401 `UNAUTHENTICATED`. Both go through `send()`, so `route not registered` and `not bound` apply; then `assert_response_matches` |
| `test_validation_error_matches_contract[op]` | Parametrize over `VALIDATION_OPS` (13 today). Build a **synthetic** drive and pass it to `run_drive`: preconditions `("login",)` when not public, plus `f"role:{staff_role_for(op)}"` when not None, plus `"thread"` when the template has `{thread_id}`; path `{"reference": "seeded_case"}` when the template has `{reference}`; body `{"text": "not json"}`; status 400; code `VALIDATION_ERROR`. Wrap it as `Drive(op, "<generated>", spec)` |
| `test_no_outbound_connections` | 1. `assert socket_guard == []`. 2. `with pytest.raises(ConnectionRefusedError, match="AEA-59 socket guard"): socket.create_connection(("192.0.2.1", 9), timeout=0.5)`, then `assert socket_guard == ["192.0.2.1"]` and `socket_guard.clear()`. 3. `with real_app(tmp_path, taps) as run:` post `login`, `startChatSession` and a `GET` on the thread path with raw `run.client` calls, ignoring statuses (some are 500 until AEA-40/44). 4. `assert socket_guard == []`. Print `refused connects: 0` |

*Invariant for AC-4:* `pytest.skip` is called **only** inside `blocked()`, with a reason that starts with
`route not registered: ` or `not bound: `. Grep check: `grep -n "pytest.skip\|pytest.mark.skip" tests/contract/test_openapi_server.py tests/contract/openapi_driver.py tests/contract/openapi_cases.py`
→ only the one line in `blocked()`.

### Step 9 — `tests/contract/test_openapi_fixtures.py`

Module docstring: level `mock-tested` (no server). Every verdict comes from AEA-23's helpers. A failing allowed variant is a
**contract finding**: stop and report it, never exclude it.

| Test | Body |
|---|---|
| `test_examples_read_as_yaml_1_2` | `doc = load_document()`. Three checks: <br>1. `started = doc["paths"]["/api/chat/sessions"]["post"]["responses"]["201"]["content"]["application/json"]["examples"]["STARTED"]["value"]`, then `assert started["greeting"]["at"] == "2026-10-16T14:20:00-05:00" and type(...) is str`. <br>2. `burning = doc["paths"]["/api/chat/sessions/{thread_id}/turns"]["post"]["responses"]["200"]["content"]["application/json"]["examples"]["BURNING_CHECK"]["value"]["blocks"][0]["options"][0]`, then `assert burning["option"] == "yes" and burning["label"] == "Yes"`. <br>3. `assert sorted(doc["paths"]["/api/demo/staffing"]["get"]["responses"]["200"]["content"]["application/json"]["examples"]) == ["OFF", "ON"]` |
| `test_named_examples_match[example]` | `@pytest.mark.parametrize("example", iter_response_examples(), ids=lambda e: e.id)`. JSON: `assert_response_matches(fake_response(e.status, e.content_type, e.value), e.operation_id)`. SSE: `assert isinstance(e.value, str)`; `frames = sse_frames(e.value)`; `assert frames`; `assert_sse_frames_match(frames, e.operation_id)` |
| `test_statuses_without_examples_have_no_body` | `rows = statuses_without_examples()`; print `f"{op} {status}"` for each; assert every row has `documents_a_body is False`. Expected print: `logout 204` |
| `test_edge_variants_accepted` | Run in three parts. <br>1. Allowed variants: for every JSON example `e` and every `v` in `body_variants(e)` with `v.allowed`, call `assert_response_matches(fake_response(e.status, e.content_type, v.body), e.operation_id)`. On `AssertionError`, collect `f"{e.id} {v.kind} at {'/'.join(map(str, v.path))}"` (no values). <br>2. Error bodies: for each op, status in `spec.responses` with `int(status) >= 400` and `"application/json"` in its media, and each `code` in `sorted(contract.error_codes)`: `body = {"error": {"code": code, "field": None, "constraint": None, "details": None}, "request_id": "req-" + uuid4().hex}`; validate the same way (kind `error`). Before the loop, assert the status schema pointer derefs to `/components/schemas/ApiError`; any other schema → `pytest.fail("status schema is not ApiError; extend the error-body generator")`. <br>3. Print `omitted=<n> null=<n> empty=<n> error=<n>`, then `optional response properties (scan): <list or 'none'>`. Assert `collected == []`, `null > 0`, `empty > 0`, `error > 0`, and `omitted > 0 or optional_response_properties() == []` |
| `test_counter_variants_rejected` | For every JSON example `e` and every counter variant: `with pytest.raises(AssertionError): assert_response_matches(...)`. When a counter passes, collect its id and kind, then fail listing all. Also: <br>• **Unknown code**, one per documented error status: the error body above with `code = "AEA59_NOT_A_CODE"`. <br>• **Undocumented status**, one per op: take the op's first example body and wrap it with status `"418"`. <br>Print the counts per counter kind; assert each is > 0 |
| `test_contract_index_matches_openapi` | `problems = index_mismatches()` (defined in `openapi_variants.py`, see step 12): `index = json.loads((REPO_ROOT / "apps/web/src/api/contract.gen.json").read_text("utf-8"))`. Compare: <br>• `specVersion` with `contract.version`; <br>• the operation set; <br>• per op: `method == spec.method.upper()`, `path == spec.path_template`, `sorted(success) == sorted(int(s) for s in spec.responses if 200 <= int(s) < 300)`, `requestExamples == request_examples(op)`. <br>Collect every mismatch as `f"{op}: {field} differs"`, then fail once: `"apps/web/src/api/contract.gen.json is stale (OpenAPI {contract.version}): …; regenerate in the UX session with `npm run examples` in apps/web"` |
| `test_api_fixtures_match` | `n = check_api_fixtures(REPO_ROOT / "tests/fixtures/api")`; print `f"tests/fixtures/api: {n} files"` (expected 0) |
| `test_api_fixture_names_refused` | In `tmp_path` write `getQueue.418.x.json` = `{}`, then `with pytest.raises(AssertionError, match="getQueue: status 418 is not documented")`. Then a fresh dir with `noSuchOp.200.x.json`: `match="unknown operationId noSuchOp"`. Then a fresh dir with `badname.json`: `match="name must be <operationId>.<status>.<name>.json"` |
| `test_failure_messages_carry_no_values` | §5 step 11 |
| `test_never_reads_eval` | §5 step 11 |
| `test_ux_dump_fixtures_match` | §5 step 10 |

`check_api_fixtures(folder: Path) -> int` lives in the test module. For each `p` in `sorted(folder.glob("*.json"))`:
1. Match `^(?P<op>[A-Za-z][A-Za-z0-9]*)\.(?P<status>\d{3})\.(?P<name>[A-Za-z0-9_-]+)\.json$`. No match → raise
   `AssertionError(f"{p.name}: name must be <operationId>.<status>.<name>.json")`.
2. When `op` is not in the contract → raise `AssertionError(f"{p.name}: unknown operationId {op}")`.
3. When `status` is not in `spec.responses` → raise `AssertionError(f"{p.name}: {op}: status {status} is not documented")`.
4. Read the body as JSON. The content type is the documented one, or `None` when that status has no content. Then
   `assert_response_matches(fake_response(...), op)`.

Return the count.

### Step 10 — fixtures: contract index (above) and the UX dump (AC-17)

`ux_dump_path() -> tuple[Path | None, str]` in the test module:
1. `selectors = REPO_ROOT / "docs/plans/ux-join/selectors.md"`. If it does not exist, return
   `(None, "docs/plans/ux-join/selectors.md")`.
2. Otherwise find the first backticked path matching `` `([^`]*fixtures[^`]*\.json)` `` in its text. When there is none,
   return `(None, "a fixtures .json path in docs/plans/ux-join/selectors.md")`.
3. Resolve the match relative to `REPO_ROOT` when it starts with `apps/`, else relative to `REPO_ROOT / "apps/web"`.
   Return `(path, str(path relative to REPO_ROOT))`.

`test_ux_dump_fixtures_match`:
1. `path, label = ux_dump_path()`. If `path is None or not path.exists()`, set `reason = f"ux fixture dump missing: {label}"`,
   then `pytest.fail(reason)` when `contract_strict()`, else `pytest.skip(reason)`.
2. `records = json.loads(path.read_text("utf-8"))`. Assert it is a list of dicts with keys `operationId`, `status`,
   `name`, `body`.
3. For each record:
   - **SSE** (`spec.event_schema` set and `str(status) == "200"`):
     - `body` is a str → `sse_frames(body)`;
     - `body` is a dict → `[SseFrame(event=str(body.get("type")), id=str(body["event_id"]) if "event_id" in body else None, data=json.dumps(body))]`;
     - `body` is a list → that dict form applied per element;
     - then `assert_sse_frames_match(...)`.
   - **Otherwise:** `assert_response_matches(fake_response(str(status), <documented content type or None>, body), op)`.
4. Collect the failures as `f"{op} {status} {name}"`. Print `ux fixture dump: <n> records checked`.

Read only; never write the dump.

### Step 11 — fixtures: AC-14 and AC-15

`test_failure_messages_carry_no_values(capsys)`:
1. Generate the values at runtime:
   - `password = rand_word(14, "pw")`;
   - `cookie = secrets.token_urlsafe(32)`;
   - `code = f"{secrets.randbelow(10**6):06d}"`.

   Never put them in a test id or a docstring.
2. Build three broken bodies (deep copies of the examples):
   - (a) `login` 200 `LOGGED_IN` with `body["session"]["role"] = password`;
   - (b) `login` 200 `LOGGED_IN` with `body["session"]["signed_in_at"] = cookie`;
   - (c) `listDemoInbox` 200 `ONE_ACTIVE` with `body["messages"][0]["status"] = code`.
3. For each: `with pytest.raises(AssertionError) as raised: assert_response_matches(fake_response("200", "application/json", body), op)`.
   Then `text = str(raised.value)` and assert:
   - `op in text`;
   - `"200" in text`;
   - the pointer is in `text`: `"session/role"`, `"session/signed_in_at"`, `"messages/0/status"`;
   - the secret is **not** in `text`.
4. `out = capsys.readouterr()`; assert none of the three values appear in `out.out + out.err`.
5. For each file `docs/testing/journeys/*-AEA-59.md` that exists, assert none of the three values appear in it.

**On today's `main` this test fails at step 3** (the helper formats `error.message`, which embeds the value). Handle that as
§8 R-1 says.

`test_never_reads_eval(monkeypatch)`:
1. `opened: list[str] = []`. Patch `builtins.open` and `io.open` with a spy that appends `os.fspath(file)` when `file` is a
   `str` or `os.PathLike`, then calls the saved real `io.open`.
2. Under the spy, call:
   - `load_document.__wrapped__()`, so the OpenAPI is really read;
   - `iter_response_examples()`, plus `body_variants()` on the first five JSON examples;
   - `check_api_fixtures(REPO_ROOT / "tests/fixtures/api")`;
   - `json.loads((REPO_ROOT / "apps/web/src/api/contract.gen.json").read_text("utf-8"))`;
   - `ux_dump_path()`.
3. Assert `opened` is not empty, which proves the spy saw the OpenAPI read.
4. Assert that `eval_root = (REPO_ROOT / "eval").resolve()` does not appear in `Path(p).resolve().parents` and is not equal
   to `Path(p).resolve()`, for every `p` in `opened`. Print `eval/ paths opened: 0`.

### Step 12 — `tests/contract/test_types_gen_drift.py`

Module docstring: reads `apps/web`, never writes it; never `npm`/`npx`; level `mock-tested (static)`.

```python
REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WEB_ROOT: Final = REPO_ROOT / "apps" / "web"
SPEC: Final = REPO_ROOT / "docs" / "ux" / "03-structure" / "ui-contracts.openapi.yaml"
TYPES: Final = WEB_ROOT / "src" / "api" / "types.gen.ts"
BINARY_REL: Final = Path("node_modules/.bin/openapi-typescript")
PACKAGE_REL: Final = Path("node_modules/openapi-typescript/package.json")
GEN_TYPES_SCRIPT: Final = "openapi-typescript ../../docs/ux/03-structure/ui-contracts.openapi.yaml -o src/api/types.gen.ts"

def primary_checkout(repo_root: Path) -> Path:
    """repo_root itself unless repo_root/'.git' is a FILE (a linked worktree): then read its 'gitdir: <path>' line
    (relative paths resolve against repo_root); <path> is <main>/.git/worktrees/<name>, so return Path(<path>).parents[2].
    Pure file reads, no subprocess (AC-13's spy must see only the generator)."""

def generator_root(repo_root: Path) -> Path:
    """repo_root/'apps/web' when its node_modules binary exists, else primary_checkout(repo_root)/'apps/web'.
    A backend worktree has no node_modules and must not get one; the primary checkout's pinned install is used read-only."""

def pinned_version(package_json: Path) -> str:
    """devDependencies['openapi-typescript'] from apps/web/package.json; must match ^\\d+\\.\\d+\\.\\d+$ else
    AssertionError(f"openapi-typescript is not exactly pinned in {package_json}: {value!r}")."""

def check_pinned_binary(gen_root: Path, pin: str) -> Path:
    """binary = gen_root/BINARY_REL; pkg = gen_root/PACKAGE_REL. Missing either -> AssertionError(f"openapi-typescript
    binary missing at {binary} (apps/web/package.json pins {pin}); this check never installs: run `npm ci` in apps/web
    in the UX session"). json version != pin -> AssertionError(f"openapi-typescript at {binary} is {version}, but
    apps/web/package.json pins {pin}"). Returns binary. Starts no process."""

def check_gen_types_script(package_json: Path) -> None:
    """scripts['gen:types'] == GEN_TYPES_SCRIPT else AssertionError("apps/web gen:types arguments changed; update
    test_types_gen_drift.py (UX-session deliverable R-W-10)")."""

def generate_types(binary: Path, spec: Path, out_dir: Path) -> Path:
    """subprocess.run([str(binary), str(spec), "-o", str(out)], cwd=out_dir, capture_output=True, text=True,
    timeout=120, check=False) with out = out_dir/'types.gen.ts'; non-zero -> AssertionError(f"openapi-typescript exited
    {code}"). Returns out."""

def assert_types_current(binary: Path, pin: str, spec: Path, committed: Path, out_dir: Path) -> None:
    """fresh = generate_types(...); if fresh.read_bytes() != committed.read_bytes(): AssertionError(f"stale generated
    file apps/web/src/api/types.gen.ts: it differs from a fresh openapi-typescript {pin} run on {spec.name} (OpenAPI
    {load_contract().version}); regenerate in the UX session with `npm run gen:types` in apps/web. This check never
    writes apps/web.")"""

def snapshot(root: Path) -> dict[str, tuple[int, str]]:
    """{relative posix path: (size, sha256 hex)} for every regular file under root whose relative parts do not contain
    'node_modules'; symlinks skipped."""
```

| Test | Body |
|---|---|
| `test_types_gen_is_current(tmp_path)` | `pkg = WEB_ROOT / "package.json"`; `check_gen_types_script(pkg)`; `pin = pinned_version(pkg)`; `binary = check_pinned_binary(generator_root(REPO_ROOT), pin)`; `assert_types_current(binary, pin, SPEC, TYPES, tmp_path)`; print `f"openapi-typescript {pin} at {binary}: byte-equal"` |
| `test_types_gen_detects_drift(tmp_path)` | Copy `SPEC`'s text to `tmp_path / "spec.yaml"` with `.replace("max_message_chars", "max_message_chars_renamed")` (assert the token occurs). Create `tmp_path / "out"`. `with pytest.raises(AssertionError, match="stale generated file"): assert_types_current(binary, pin, tmp_path / "spec.yaml", TYPES, tmp_path / "out")` |
| `test_refuses_missing_or_unpinned_binary(tmp_path, monkeypatch)` | Spy: patch `subprocess.run` and `subprocess.Popen` with functions that append the argv to `calls` and raise `AssertionError("no process may start")`. <br>(a) Empty `tmp_path / "a"` → `pytest.raises(AssertionError, match="binary missing at")`; assert the message contains both `str(tmp_path / "a" / BINARY_REL)` and `"7.13.0"` (pass `pin="7.13.0"` explicitly). <br>(b) `tmp_path / "b"` with an empty file at `BINARY_REL` and `PACKAGE_REL` = `{"version": "7.12.0"}` → match `"is 7.12.0, but apps/web/package.json pins 7.13.0"`. <br>(c) `tmp_path / "c" / "package.json"` = `{"devDependencies": {"openapi-typescript": "^7.13.0"}}` → `pinned_version` raises `"not exactly pinned"`. <br>Finally `assert calls == []` |
| `test_apps_web_untouched(tmp_path, monkeypatch)` | 1. `roots = {WEB_ROOT, generator_root(REPO_ROOT)}`; `before = {r: snapshot(r) for r in roots}`; `tmp_before = (WEB_ROOT / ".tmp").exists()`. 2. Spy: patch `subprocess.run` with a recorder that appends the argv list, then delegates to the saved real `subprocess.run`. 3. Run `test_types_gen_is_current`'s body (the same helper calls into `tmp_path`) and `openapi_variants.index_mismatches()` (the contract-index comparison). 4. Assert `snapshot(r) == before[r]` for each root; `(WEB_ROOT / ".tmp").exists() == tmp_before`; `calls` is not empty; for each argv, `argv[0] == str(binary)` and no element's basename is `npm` or `npx`. Print `apps/web files compared: <n>; processes: <len(calls)> (openapi-typescript only)` |

Move the contract-index comparison into `openapi_variants.py` as `index_mismatches() -> list[str]` (the field list from
step 9), so `test_contract_index_matches_openapi` and `test_apps_web_untouched` share it.

### Step 13 — `tests/contract/cases/README.md` and `tests/fixtures/api/README.md`

`tests/contract/cases/README.md`. The sections, in order:
1. **What a case file is**: one per route ticket. Each holds `ROUTE_FILE: Final = "<stem>"` and
   `CASES: Final[dict[str, dict[str, object]]]`, keyed by operationId. The file → operations table comes from §5 step 3's
   map; list all ten stems with their operations.
2. **Drive keys**, as a table: `name`, `status`, `code`, `preconditions`, `setup`, `body`, `path`, `thread`, `events`,
   `last_event_id`, `frames`, `response_example`, each with its meaning and the step it triggers.
3. **Vocabulary**: the canonical words with the real-app step each runs (§5 step 6). Then a sentence: "aliases accepted for
   files written before this format", with the alias list. Then the local-driver-only setups and why.
4. **Path words**: `started`, `unknown`, `malformed` (`thr_9d41`), `other_session`, `ended`, `seeded_case`; anything else
   is sent literally.
5. **What the runner adds itself**: the 401 and 400 drives (AC-3), and the login wrong pair.
6. **Skip reasons and strict mode.**
7. **The documented example case**, between the marker lines exactly as below. `test_case_format_example_is_valid`
   parses it.

````markdown
<!-- example-case:start -->
```python
EXAMPLE_CASES = {
    "getChatThread": {
        "public": False,
        "drives": (
            {"name": "read", "status": 200, "preconditions": ("login", "thread"),
             "path": {"thread_id": "started"}, "body": None},
            {"name": "no_session", "status": 401, "code": "UNAUTHENTICATED", "preconditions": (),
             "path": {"thread_id": "unknown"}, "body": None},
            {"name": "unknown_thread", "status": 404, "code": "SESSION_NOT_FOUND", "preconditions": ("login",),
             "path": {"thread_id": "unknown"}, "body": None},
            {"name": "ended_thread", "status": 410, "code": "SESSION_ENDED", "preconditions": ("login", "thread"),
             "setup": "ended_thread", "path": {"thread_id": "ended"}, "body": None},
        ),
    },
}
```
<!-- example-case:end -->
````

8. **How to run your cases**: `uv run pytest tests/contract/test_openapi_server.py -k <operationId> -rs`, and the same with
   `CONTRACT_STRICT=1`.

`tests/fixtures/api/README.md`, about 10 lines:
- the naming rule `<operationId>.<status>.<name>.json` (body only, synthetic values);
- that `tests/contract/test_openapi_fixtures.py::test_api_fixtures_match` validates every file here, and that an unknown operation or undocumented status fails;
- no secrets, codes, card-like numbers or full phone numbers.

### Step 14 — `tests/journeys/j1/test_aea_59.py` (AC-16, blocked)

```python
"""J-1 contract step (AEA-59 AC-16): every HTTP response J-1 receives passes assert_response_matches for its operationId.

Level when it runs: integrated with a scripted model (AEA-57's harness: real app on a disposable DB copy, scripted
adapter at the provider boundary). Blocked by AEA-57: tests/journeys/support/ (the harness and its per-response hook)
is not on main, and this file must not edit support/. When AEA-57 lands, a follow-up on AEA-59 replaces the skip with:
login, startChatSession, submitTurn, getChatThread after a refresh, and a signed-out getChatThread (401), each response
checked by the harness's own hook and listed by operationId, plus J-1's user-visible and stored-row assertions.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.journey


@pytest.mark.skip(reason="blocked-on AEA-57: tests/journeys/support/ (journey harness and its response hook) is not on main")
def test_j1_every_response_matches_contract() -> None:
    """Placeholder: see the module docstring for the steps it will assert."""
```

### Step 15 — context updates (AC-19) and the evidence record

1. **`.claude/reference/area-map.md`**, row `| 3+ | **Integration and journeys** | …`. Change the last cell (`planned`)
   to the following, filling in the commit:
   `partly built: AEA-59 (`<short sha>`): tests/contract/{test_openapi_server,openapi_cases,openapi_driver,test_openapi_fixtures,openapi_variants,test_types_gen_drift}.py, tests/contract/cases/README.md (the case format; each cases/<route>.py is its route ticket's), tests/fixtures/api/ (drop point), tests/journeys/j1/test_aea_59.py (blocked on AEA-57); the rest planned`.
   The ticket says "A0 test rows", but the row that lists `tests/contract/` and owner 59 is this one, so change only this
   row's Status cell.
2. **`.claude/state/icm-progress.md`**: add one row directly after the last *Routes verified against code and tests* row,
   ≤ 400 characters:
   `| Routes verified against code and tests | provisional | <date>: AEA-59 contract boundary (<sha>): test_openapi_fixtures.py, test_types_gen_drift.py pass; test_openapi_server.py <p> passed / <s> skipped (not bound / not registered); record docs/testing/journeys/<date>-AEA-59.md | Each slice adds its route; verified when every area-map row is actual |`
3. **`docs/design/code-design.md` §9**:
   - Replace the `contract/` lines of the tree with:
     `├── contract/         test_model_ports_contract.py (JevAdapter + AnthropicAdapter, recorded fixtures: same failure`
     `│                     kinds), test_retrieval_contract.py, test_trace_sink_contract.py; OpenAPI boundary (AEA-59):`
     `│                     test_openapi_server.py over cases/<route>.py (one per route ticket), test_openapi_fixtures.py,`
     `│                     test_types_gen_drift.py`.
   - Change the *Built on `main`* line to:
     `**Built on `main`:** `tests/fakes/` (AEA-11, `c33f12c`); `tests/contract/` OpenAPI boundary checks (AEA-59, `<sha>`); the rest of this tree is planned.`
4. **Evidence record `docs/testing/journeys/<run-date>-AEA-59.md`**, with the nine fields of integrated-journeys §4:
   - **Claim**: AEA-59 contract boundary (server cases, fixtures, generated types). J-1 contract step blocked.
   - **Level per check**:
     - server drives: `integrated with a scripted model` (real app in process, guards on, DB copy). No model is reached until AEA-51; say so.
     - static case checks, fixtures, index and drift: `mock-tested`.
     - J-1: not run.
   - **Tested revision**: the commit SHA (or "uncommitted").
   - **Environment**: host `claude-vultr`, Python and uv versions, node version, `openapi-typescript` 7.13.0 and its path (primary checkout), the DB copy source (the issued SQLite via first boot), and "no model adapter reached".
   - **Command**: the two commands from §7.
   - **Result**: pass, skip and fail counts from the runs; the per-kind variant counts; the strict-run failures by name.
   - **Evidence location**: this file plus the pytest output.
   - **Remaining limitations**:
     - local-driver-only drives, listed;
     - the dev-scenario dump is absent;
     - the drift check uses the primary checkout's `node_modules`;
     - omitted-optional is 0 by contract;
     - no browser (AEA-58).
   - **Blocked by**:
     - each operation skipped with its reason (`not bound: get_login_sessions` → AEA-44; `route not registered: <op>` → its route ticket from §5 step 3's map);
     - AC-16 → AEA-57;
     - AC-14 → the AEA-23 follow-up, if it is still xfail.

   **No** demo pair, cookie, session secret or code.

### Step 16 — gates and commit

1. Lint and format, then type check, then tests, then journeys (§7). Stop at the first red.
2. `git status --short` must show only the owned files of §2.
3. `git add` with each path listed explicitly. Never use `-A`.
4. Commit, for example
   `AEA-59: contract boundary checks (server cases runner, fixtures and variants, generated-types drift)`. The last line of
   the message is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

Do not push. The merge step pushes.

---

## 6. Data and fixtures

- **No new data file.** `tests/fixtures/api/` stays empty, holding only its README. Every body comes from the signed
  OpenAPI's own examples, or from deep copies of them that this plan mutates.
- **Values generated at runtime:**

  | Value | Source |
  |---|---|
  | demo pair, session secret, provider keys | `make_settings` → `rand_word` (letters only) |
  | AC-14 password | `rand_word(14, "pw")` |
  | AC-14 cookie | `secrets.token_urlsafe(32)` |
  | AC-14 six-digit code | `secrets.randbelow(10**6)` |
  | turn ids | `uuid.uuid4()` |
  | request ids | `"req-" + uuid4().hex` |

- **Database:** the issued `docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite`, copied by the
  app's own first boot (`migrate`) into each test's `tmp_path / "data"`. It is never opened for writing.
- **Seeds**, written into a test's own working copy and nothing else:
  - `events` through `events_support.append_stored`;
  - `verified` through `person_request_support.verify_thread` (issued customer `MHC-10002`).
- **Forbidden in code, ids, docstrings or the record:** a literal six-digit code, a card-like number, a full phone number,
  the demo password.

---

## 7. Checks

Run from the worktree root with `export UV_LINK_MODE=hardlink`. Cheapest first; stop at the first red.

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check tests/contract tests/journeys/j1/test_aea_59.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check tests/contract tests/journeys/j1/test_aea_59.py` | no file would be reformatted |
| 3 | Type check | `uv run mypy tests/contract tests/journeys/j1/test_aea_59.py` | `Success: no issues found` |
| 4 | Drift + fixtures (mock-tested) | `uv run pytest tests/contract/test_types_gen_drift.py tests/contract/test_openapi_fixtures.py -rsP` | All pass. `test_ux_dump_fixtures_match` is skipped with `ux fixture dump missing: docs/plans/ux-join/selectors.md`. `test_failure_messages_carry_no_values` passes, or is `xfail` per §8 R-1. Printed counts: 250 examples, `logout 204`, per-kind variant counts > 0 (omitted 0 with scan `none`), `tests/fixtures/api: 0 files`, `eval/ paths opened: 0` |
| 5 | Server runner, default | `uv run pytest tests/contract/test_openapi_server.py -rsP` | Static tests pass; `test_no_outbound_connections` passes; every other item **passes or is skipped** with exactly `not bound: …` or `route not registered: …`. On `4a76850` expect every drive skipped as `not bound: get_login_sessions` (AEA-44 not merged) |
| 6 | Server runner, strict (wave-merge form) | `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -rs` | **Expected red in wave 2**: failures only for the missing cases (completeness) and for the blocked drives, each naming its reason. Record the counts; do not try to make it green |
| 7 | Journey file | `uv run pytest tests/journeys/j1/test_aea_59.py -m journey -rs` | `1 skipped` with the AEA-57 reason |
| 8 | Affected journeys | `uv run python -m tests.journeys.affected --base main --list-only`, then run what it lists: `uv run python -m tests.journeys.affected --base main -- -rs` | The listed journeys pass or skip with their own reasons (no journey imports these modules; expect only j1 or none) |
| 9 | Grep checks | `grep -n "pytest.skip\|mark.skip" tests/contract/test_openapi_server.py tests/contract/openapi_driver.py tests/contract/openapi_cases.py` → only `blocked()`; `git diff --name-only main...HEAD` → only §2 owned paths, nothing under `apps/web/`, `docs/ux/`, `eval/`, `src/` | As stated |

**Tests the implementer writes with the code (WP pair).** The ticket's worked pair is the *Server* example: the
`startChatSession` → `getChatThread` success, plus both unsigned 401s. That pair is
`test_success_matches_contract[startChatSession/started]`, `[getChatThread/read]` and
`test_unauthenticated_matches_contract[startChatSession]`, `[getChatThread]`. They come alive when AEA-40's `chat.py`
merges. Until then the runner names `startChatSession` and `getChatThread` as missing, with the file
`tests/contract/cases/chat.py`. The *Missing case* pair is `test_completeness_names_a_removed_case`. The *Fixture variant*
pair is `test_edge_variants_accepted` and `test_counter_variants_rejected`. The *Drift* pair is
`test_types_gen_is_current` and `test_types_gen_detects_drift`.

**Existing tests that must stay green.** This change edits no existing module, so none of them is affected. Do **not** run
the full suite: no conftest, settings, dependency or cross-package module changes (rule `build-loop-test-scope`). As a
spot check that nothing collided, run `uv run pytest tests/api/test_openapi_check.py tests/api/test_contract_cases_auth.py tests/api/test_contract_cases_staff_clock.py -q`.

---

## 8. Risks and requests

- **R-1, request to the orchestrator: an AEA-23 follow-up for AC-14.** Measured on `4a76850`, `assert_response_matches`
  produces `[OpenAPI 0.1.0-ux3] login: 200 body breaks the schema at session/role: 'pwzq…' is not one of [...]`. It formats
  jsonschema's `error.message`, which embeds the instance. Its enum-code branch also prints `{code!r}`.
  - **Fix** (≤ 10 lines in `tests/api/openapi_check.py`, owned by AEA-23):
    - the schema failure message becomes `f"{status} body breaks the schema at {where}: {error.validator} failed"` (the same for the SSE helper);
    - the code branch becomes `"error code is outside the documented enum"`.

    Pointers and operation ids stay. The orchestrator can write it inline under the fan-out rule's one-file exception, then
    merge it before or after AEA-59.
  - **Implementer's rule:** at start, run `grep -n "error.message" tests/api/openapi_check.py`.
    - **No match** (the follow-up is in): write AC-14 as specified.
    - **A match:** add exactly
      `@pytest.mark.xfail(strict=True, reason="blocked-on AEA-23 follow-up: openapi_check failure messages embed the instance value (jsonschema error.message); AEA-59 AC-14")`
      to `test_failure_messages_carry_no_values`, and say so in the report and the record.

    Strict xfail turns into a failure the day the follow-up merges, which forces the marker's removal. Never weaken the
    test's assertions.
- **R-2, blocked-on AEA-57 (AC-16 only).** AEA-57 has no code, branch or plan, and its fixture names are explicitly "this
  ticket's to fix" (AEA-57 *What to build* §3). So a J-1 contract step cannot be written against it without inventing names.
  `test_aea_59.py` lands as a named skip.
  - **Follow-up on AEA-59 after AEA-57 merges:** fill the test from `tests/journeys/support/README.md`'s fixtures.
  - **If AEA-57's client hook does not expose each response:** that is a follow-up on AEA-57, never an edit to `support/`.

  The server runner itself does **not** depend on AEA-57. The slice plan §0a settled that AEA-59 has no dependency on the
  harness. The runner builds the real app through the same `create_app(settings)` and first-boot copy that AEA-57 uses.
  It runs in process for a reason: it needs the raised `not bound:` exception, which a socket-served app reduces to a bare 500.
- **R-3, scripted model once AEA-51 lands.** The runner launches with `overrides=None`. That is exact today:
  `register_graph` is a no-op, so no model port is reachable. Once AEA-51 binds the graph, `submitTurn`'s success drives
  would reach the real adapters. The socket guard then refuses the connect, and AC-15 fails loudly; nothing is paid.
  **Request:** when AEA-57 has merged, a small follow-up on AEA-59 passes AEA-57's scripted adapter in
  `ContainerOverrides(choice=…, structured=…, tools=…)` from `real_app()`. AEA-51's plan should list this as its
  prerequisite, before AEA-51 switches strict mode on.
- **R-4, AC-7 deviation (engineering, measured).** Every response property in `0.1.0-ux3` is `required`, so "omitted
  optionals" cannot be above zero. The plan asserts the count matches a scan of response-reachable schemas, and adds
  required-omitted counter-variants so the omit dimension still discriminates. This is not a contract change. The reviewer
  should see it named in the record.
- **R-5, vocabulary drift across route files.** On `main` and in flight there are synonyms: `started_thread`/`start_thread`/`thread`,
  `as_<role>`/`role:<role>`, `reset_held`/`reset_gate_held`. The runner maps them (§5 step 3), and `cases/README.md`
  fixes the canonical words. **Request:** the orchestrator points the planners of AEA-43, AEA-45, AEA-46 and AEA-48 (case
  files not yet written) at `tests/contract/cases/README.md`. A new word in a later file fails
  `test_case_files_are_well_formed` with its name; the fix is a follow-up on AEA-59 (this module), never a route-file edit.
  Two words are known gaps:
  - AEA-46's `streamCaseEvents` cannot use `events` seeding: the runner seeds thread streams only.
  - AEA-45's `reviewFlag` needs a created flag: there is no path word for one yet. A literal is sent, and a mismatch fails
    loudly.
- **R-6, new support-module names.** `openapi_cases.py`, `openapi_driver.py` and `openapi_variants.py` keep each file
  under the test-file cap. They sit in AEA-59's `tests/contract/` family, and no other ticket's owned list uses these
  names. The orchestrator should add them to AEA-59's row in its collision check.
- **R-7, worktree generator.** A backend worktree has no `apps/web/node_modules`, and one must never be installed there.
  So `generator_root()` falls back to the primary checkout's pinned binary, read only, located by reading `.git` as a
  file. If the primary checkout has no `node_modules` either, AC-11 fails with the missing-binary message. That is the
  intended behaviour (AC-12), not a reason to skip.
- **R-8, local-driver-only drives.** `requestPerson/handoff_failed` (needs a failing HandoffService) and AEA-40's
  `submitTurn/turn_in_progress` (needs a turn left running) cannot be produced on the real app without a double. They
  are listed, not run. Their proof stays the route's local driver (`mock-tested`), and the record says so.
- **R-9, runtime.** Each drive builds its own app. That is about 0.1–0.3 s each, roughly 15–40 s for today's 35 drives
  plus the 43 generated ones. On `main` today they skip fast at `login`. Do not share apps between drives; isolation is the
  point.
- **Collisions with other slices.** None on files. Shared surfaces read: `tests/api/*_support.py` (a later edit by their
  owners could break an import; the runner uses only the names copied in §4), and the OpenAPI (an approved change means
  new cases plus regenerated `apps/web` files).

---

## 9. Readiness

**READY.** Every decision above is made, and the implementer needs no product answer.
- **AC-16 is blocked-on AEA-57.** It lands as a named skip, and a follow-up fills it.
- **AC-14 waits on the AEA-23 follow-up (R-1).** It is written now, and marked strict-xfail only if the helper is
  unchanged at implementation time.
- Nothing needs a change to a signed contract.
- None of D-4…D-15 is re-decided.

**Gates:** none. There is no human, paid, live or UX gate: the plan reads `apps/web` and never runs a model.


## Deviations

Recorded by the implementer, 2026-10-21 (base `main` `0dedd59`, not `4a76850`).

- **Vocabulary extended for `staff_live.py` and `staff_session.py`, which merged after the plan.** `reference` is an allowed
  drive key; `last_event_id` may be an int (a literal header value); the words `live_case_claimed`, `live_case_joined`,
  `live_case_unclaimed`, `case_claimed_by_supervisor` and `case_events` are local-driver-only (the real app cannot seed
  them without a double), so those drives are listed and not run. Fixed in `openapi_cases.py`, never in a route file (plan R-5).
- **`CASES` on `main` now covers 11 operations in 6 files** (auth, events, handoff, staff_clock, staff_live, staff_session);
  19 operations are missing a case and are named with their file.
- **Every drive that passes the gate's clock lookup skips with `not bound: demo_clock`** (48 drives on this base), so the
  default run's real-app passes are the 401/400/login cases that fail before it. Reported in the record's *Blocked by*.
- **AC-14 is `xfail(strict=True)`** per R-1: `grep -n "error.message" tests/api/openapi_check.py` still matches (two lines).
  Run with `--runxfail` it fails on `assert secret not in text`, the intended reason.
- **AC-16 is a named skip** per R-2 (AEA-57 is not on `main`).
- **Context rows cite the branch name instead of a short sha** (the sha does not exist until the commit that contains the row).
- **Unrequested in the plan:** `index_mismatches()` lives in `openapi_variants.py` as step 12 says; `openapi_driver.py` imports
  `render_unhandled_error` from `meridian.web.errors` (the middleware re-imports it, mypy does not treat it as exported) and
  patches the name in `meridian.web.middleware`.
