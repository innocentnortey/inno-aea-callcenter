# Plan — [AEA-57] journey harness: real server + disposable DB + scripted model

**Status:** planned — READY (every import this slice needs is on `main`: AEA-02, 10, 11, 23 merged, AEA-26 merged; the
sibling bindings J-1 needs at run time (AEA-30, 40, 44, 51) are reported as *blocked* steps, never imported)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/57 (identical to
`docs/plans/tickets/AEA-57.md`) · **Base revision:** `main` `24a5e9a` · **Wave:** 2 · **Lane:** build-loop ·
**Risk:** none (no `risk::security`: plan → implement with tests → review; no frozen tests)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-57-journey-harness` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-57`), cut from `main` at or after `24a5e9a`.

No earlier version of this plan existed at this path; this is the first write.

---

## 1. Goal and sources

### Goal (issue *What to build*, quoted in short)

> "This ticket lands the **journey harness** and the **first journey, J-1**, at the API level: the real FastAPI app, the
> real container, the real middleware and guards, a disposable copy of the issued database, and a scripted model at the
> provider boundary. Every later build ticket extends a journey with it, and the merge gate runs it."

**What it does, concretely.** A journey test asks for the `journey` fixture. The harness makes a temp folder, builds
`Settings` from a per-run environment mapping (a random letters-only demo login and session secret, placeholder provider
keys, no Langfuse, no eval key), and starts the **real** app (`create_app(settings, overrides=ContainerOverrides(...))`)
under uvicorn in a background thread on `127.0.0.1` with an OS-chosen port. The app's own first boot copies the issued
scheduling DB into `<temp>/data/meridian.sqlite` and applies every schema file. The test then talks HTTP to it with
`httpx`: every `/api/...` response is checked against the signed OpenAPI by AEA-23's `assert_response_matches`. A
read-only SQLite reader checks what was stored. When a step needs a service whose ticket has not landed (for example
`login_sessions`, AEA-44), the harness reports that step **blocked-on AEA-44** (pytest *skipped*), or *failed* under
`--journeys-strict`. With `--journey-record=AEA-57`, the run writes `docs/testing/journeys/<date>-AEA-57.md`.

Example (input → process → output): J-1 step 3 posts the run's demo pair to `POST /api/login` → the real middleware,
login route and AEA-44's `StaffSessionStore` run → the client sees `200 LoginResponse` with `session.role: "customer"` and
`Set-Cookie: mhc_session=…; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200` (no `Secure`), and the reader sees exactly one
new `staff_sessions` row whose `token_hash` differs from the cookie value. On today's `main` (no AEA-44) the same step is
reported `blocked-on AEA-44: login_sessions not bound`.

### Context

The integrated-journeys rule (Riverside lesson, 2026-10-21) made a journey gate part of every merge, but "until AEA-57
lands the harness, there is no journey gate to run" (`build-loop-test-scope.md` *AEA addition*). Six journey files already
exist at `mock-tested` level (j7, j8, j9, j10) and all name AEA-57 in their *Blocked by*. AEA-40, 44, 30 are being built in
parallel worktrees now; `REPLY_COMPOSER` and `run_graph` are bound by AEA-51 (wave 3). So in wave 2 only J-1 steps 1–3 can
reach the integrated level; steps 4–8 report *blocked* until those land (see §8 R-1).

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-57.md` (AC-1…AC-18, ND-1, ND-2) | Everything below |
| Slice plan | `docs/plans/slice-plan.md` §0a (journey map row J-1, "J-1 runs in two stages", conventions), §1 row AEA-57, §3 rows `tests/journeys/`, `tests/contract/` | Owned paths; `support/` is AEA-57's alone; later tickets add `j<N>/test_aea_<NN>.py` only |
| Rules | `.claude/rules/integrated-journeys.md` §2, §3 rules 1–3, 5, 6, §4 (levels, nine record fields), §5; `build-loop-test-scope.md` + *AEA addition*; `context-maintenance.md`; workspace `code-structure.md` (file sizes), `code-design-solid-modularity.md` | Harness shape, record format, what each role runs, context rows in the same change |
| Requirements | PRD R-41, R-45, R-48; US-1 (greeting says automated), US-28 (login, guards, expired session) | J-1 steps; AC-17 |
| Component contracts (DO-4 + stage7 addenda; addenda win) | `stage7/web.md` §2 (cookie, credential check), §4 (providers, "not bound", `owned_thread`), §6 (gate order, 401 vs 303), §9 (`run_turn`, idempotent `turn_id`, turn-row sources), §10 (`request`, `auth_event` records), §13 (`assert_response_matches`), §14 (`SessionService.open` / `thread`), §15 (`create_app`, `ContainerOverrides`, D-13 `wall_clock`); `stage7/models.md` §1 (`ProviderCall`, `Attempt.record`), §2 (one adapter per role/model; model ids), §3 (`INVALID_OUTPUT` mapping), §5 (gateway reads `adapter.provider`), §7 (container wiring, `NullTraceSink` when Langfuse unset); `stage7/graph-core.md` §2 (`TurnTrace`, `TurnRecord`), §12 (env names); `stage7/cases.md` §1.1 (tables), §1.4 (first-boot copy), §1.5 (`temp_sqlite()`); `stage7/staff.md` §3 (`staff_sessions`); DO-4 §4 (`PlannerChoices`), §9 (`ResponderDraft`), §12 (ports) | Signatures in §4 below |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | n/a: J-1 is not an E-run; no number is reported (ticket *Evaluation*) |
| Observability contract | DO-6 `docs/design/observability-contract.md` rows WF-1, WF-18 | AC-12: `auth_event`, `request` record per call; WF-1 rows per step |
| Key-metrics registry | DO-7 M-22…M-26, M-29 | Step 5 asserts the columns those metrics read are filled; the harness reports no metric value |
| Current code (read for this plan) | `src/meridian/web/{app,container,deps,middleware,errors,logging}.py`, `routes/auth.py`, `config.py`, `ports/models.py`, `domain/{common,turn,staff}.py`, `policy/{texts,limits}.py`, `adapters/sqlite/{db,migrate}.py`, `schema/*.sql`, `services/{health,reset}.py`; `tests/conftest.py`, `tests/journeys/{README.md,affected.py}`, existing `j7…j10` files, `tests/fakes/models.py`, `tests/fixtures/sqlite.py`, `tests/api/{openapi_check,web_shell_support}.py`; sibling plans AEA-30, 37, 40, 44 (for key names only) | §4 |

---

## 2. Boundary

### File map — owned files (the only files the implementer creates or edits)

| File | Create / modify | Responsibility (one sentence) | Target size |
|---|---|---|---|
| `tests/journeys/support/__init__.py` | create | Package marker; one-line docstring | 1 line |
| `tests/journeys/support/README.md` | create | Public fixtures, options, the `journey` API, step rules, the three commands | ~120 lines |
| `tests/journeys/support/plugin.py` | create | pytest options, the two public fixtures, the step collector and the record hook | ≤ 200 |
| `tests/journeys/support/env.py` | create | Per-run temp folder, environment mapping, `Settings.from_env`, issued-file hash before/after | ≤ 150 |
| `tests/journeys/support/scripted_model.py` | create | The scripted provider adapter, the per-role script, `scripted_overrides()` | ≤ 350 |
| `tests/journeys/support/server.py` | create | `StepClock`, the uvicorn launcher, the socket guard | ≤ 250 |
| `tests/journeys/support/client.py` | create | `JourneyClient` (httpx, cookies, OpenAPI check per response), cookie-attribute parser | ≤ 150 |
| `tests/journeys/support/logtap.py` | create | Root-logger handler that keeps every record; structured-record lookup and wait | ≤ 120 |
| `tests/journeys/support/db.py` | create | Read-only DB reader, issued-table rows, file hash | ≤ 150 |
| `tests/journeys/support/steps.py` | create | Need/operation owner maps, preflight, blocked handling, step and test result types, collector | ≤ 250 |
| `tests/journeys/support/record.py` | create | Build, render and write the nine-field evidence record | ≤ 250 |
| `tests/journeys/support/run.py` | create | `JourneyRun` (the object tests get) and `open_journey()` that wires all parts | ≤ 300 |
| `tests/journeys/support/test_support.py` | create | Harness self-checks AC-1…AC-7, AC-14, AC-16, AC-17 (+ socket guard, wall-clock mechanism) | ≤ 500 |
| `tests/journeys/j1/test_aea_57.py` | create | Journey J-1 (AC-8…AC-13) | ≤ 500 |
| `docs/testing/journeys/<run-date>-AEA-57.md` | create (written by command 2, then committed) | AC-15 evidence record | generated |
| `.claude/reference/area-map.md` | modify **one cell**: row `3+` *Integration and journeys*, last column | AC-18 | — |
| `.claude/state/icm-progress.md` | modify **one row**: *Integrated-journey protection* | AC-18 | ≤ 400 chars |
| `docs/design/code-design.md` | modify §9 only: add the `journeys/` lines to the tree and the *Built on `main`* sentence | AC-18 | — |
| `PROJECT-CHECKLIST.md` | modify **one line** (§8, line starting `- [ ] Journey harness exists`) | AC-18 | — |

### Shared surfaces read only (never edit)

`src/meridian/**` (all of it), `tests/conftest.py` (it already loads `tests.journeys.support.plugin` once the module exists:
`_OPTIONAL_PLUGINS`), `tests/journeys/README.md`, `tests/journeys/affected.py`, `tests/journeys/__init__.py`,
`tests/journeys/j*/__init__.py`, every other `tests/journeys/j*/test_aea_*.py`, `tests/fakes/**`, `tests/fixtures/**`,
`tests/api/**` (import `tests.api.openapi_check` read-only), `pyproject.toml`, `uv.lock`,
`docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, the briefing, issued data,
`docs/archive/`, `docs/parked/`, `.claude/state/resume.md`, the `Last reconciled:` line of `icm-progress.md`.

### Owned by other slices (do not touch)

`web/container.py` hunks (AEA-10…53), `web/deps.py` and `web/app.py` (AEA-23), `routes/chat.py` & `services/{session,turn}.py`
(AEA-40), `services/staff.py` (AEA-44), `services/demo.py` (AEA-30), `register_graph` (AEA-51), `tests/journeys/browser/`
(AEA-58), `tests/contract/test_openapi_*.py` (AEA-59). A missing provider or route is reported *blocked*, never stubbed.

---

## 3. Requirements table

Ticket criteria verbatim in substance (IDs as the ticket), then plan-added rows. "Verify" names the exact test.

| ID | Kind | Requirement (short) | How it is built | Verify (test / command) | Level |
|---|---|---|---|---|---|
| AC-1 | invariant | Fresh temp `MERIDIAN_DATA_DIR`; `meridian.sqlite` made by the app's own first boot; five issued tables equal the issued file row for row; issued SHA-256 equal before/after; temp dir gone after teardown | `env.journey_environment()` + `server.launch_server()` (step 3, 5) | `tests/journeys/support/test_support.py::test_disposable_copy_and_issued_untouched` | integrated with a scripted model (self-check) |
| AC-2 | invariant | Scripted adapter parses like the adapters: valid → typed value; bad option / failing `output_model` / unparseable JSON → `INVALID_OUTPUT`, `Attempt.record` a `ProviderCall` (cost 0.0, `price_table`), no exception; `provider`/`model` match the configured role; every request recorded | `scripted_model.py` (step 2) | `test_support.py::test_scripted_model_parses_like_adapters` | mock-tested |
| AC-3 | negative | No deployed config can select the scripted adapter: nothing under `src/meridian/` imports `tests`; no `Settings` field, env name or provider literal names it | AST import scan + `Settings`/`ENV_NAMES`/literal scan | `test_support.py::test_scripted_model_not_selectable_in_deploy` + `grep -rnE "tests\.journeys\|Scripted(Model\|Jev\|Anthropic)\|scripted_model" src/meridian/` prints nothing (see R-2 for why the grep is narrowed) | mock-tested |
| AC-4 | invariant | Launcher: `127.0.0.1`, OS-assigned port never 4019/5184, ready on uvicorn's `started` after the lifespan ran (not `/healthz`); teardown stops the thread, container closed once | `server.launch_server()` (step 5) | `test_support.py::test_server_thread_ephemeral_port` | integrated (self-check) |
| AC-5 | failure/refusal | Every journey response checked by `assert_response_matches`; undocumented status/body fails with operationId and status in the message | `client.JourneyClient.call` (step 6) | `test_support.py::test_client_validates_every_response` (httpx `MockTransport`) | mock-tested |
| AC-6 | invariant | DB reader is `mode=ro`; a write raises `sqlite3.OperationalError`; no open transaction between steps | `db.DbReader` (step 4) | `test_support.py::test_db_reader_read_only` | mock-tested |
| AC-7 | failure/refusal | Unbound provider → step *blocked* with owning ticket (skipped "blocked-on AEA-40"); record's *Blocked by* names it; `--journeys-strict` → failed | `steps.missing_needs`, `stop_blocked`, `record` (steps 7, 8) | `test_support.py::test_unbound_provider_blocked_then_strict_fails` | mock-tested |
| AC-8 | **journey** | J-1 steps 1–3 exactly as the ticket table | `j1/test_aea_57.py` | `tests/journeys/j1/test_aea_57.py::test_j1_guards_and_login` | **integrated with a scripted model** (no model call in these steps) |
| AC-9 | **journey** | J-1 steps 4, 6 (read), 7 | same file | `::test_j1_session_resume_and_owner_guard` | **integrated with a scripted model** |
| AC-10 | **journey** | J-1 steps 5, 6 (resend): rows stored; reply text = scripted responder text; resend byte-identical, no new model request, one `turns` row; blocked on AEA-51 until `run_graph` binds | same file | `::test_j1_one_turn_and_resend` | **integrated with a scripted model** once `run_graph` is bound |
| AC-11 | negative | Step 8: 2,001-char text → 400 `VALIDATION_ERROR`; sentinel absent from body, every captured log record, working-copy files; demo password, session secret, `mhc_session` value absent from files, logs, record; no new rows | same file | `::test_j1_rejected_and_secret_values_absent` | integrated |
| AC-12 | capture | WF-18: `auth_event` `rejected` (step 2) then `ok` with the opaque `session_id` (step 3); a `request` record per call whose `request_id` = that response's `X-Request-ID`; WF-1 rows per step (presence only) | same file + `logtap.LogTap` | `::test_j1_records_per_step` | integrated |
| AC-13 | invariant | 0 non-loopback connections (socket guard), placeholder keys, no `LANGFUSE_*`, no `MERIDIAN_EVAL_KEY`, nothing read from held-out case/key paths | `server.socket_guard()` in every `journey` run; env mapping | `::test_j1_offline_and_placeholders` (plan-added test name), the guard assertion in every `journey` teardown, and `grep -rn "heldout\|key_dir" tests/journeys/` prints nothing | integrated |
| AC-14 | invariant | Record has rule §4's nine fields; *Tested revision* = SHA + `agent_version` ("uncommitted" when dirty); *Environment* names host, server command, DB copy source, frontend "none (API level)", scripted adapter, model ids; *Result* per step; no file without the option | `record.py` (step 8) | `test_support.py::test_evidence_record_fields` | mock-tested |
| AC-15 | capture | This ticket's record exists at `docs/testing/journeys/<date>-AEA-57.md`, level per step, *Blocked by* each unbound owner (or "none"), J-1 wall time | command 2 (§7) then commit | read the file | integrated (steps reached) |
| AC-16 | invariant | `support/README.md` lists every public fixture and option; checks fail when a listed fixture is missing or a `j*/` file breaks `j<N>/test_aea_<NN>.py` (N in 1…10) | `plugin.PUBLIC_FIXTURES`, `plugin.OPTIONS`, `steps.convention_violations` | `test_support.py::test_readme_lists_public_fixtures`, `::test_journey_file_convention` | mock-tested |
| AC-17 | invariant | Wall-clock control: fixture moves `get_wall_clock()` forward; session resolves at start + lifetime − 1 s, 401 `UNAUTHENTICATED` `reason: "expired"` at start + lifetime (lifetime read from `Limits`); `getDemoClock` same before/after; mechanism = `ContainerOverrides(wall_clock=StepClock)`; without the fixture `wall_clock=None` | `server.StepClock`, `plugin.journey_clock` | `test_support.py::test_wall_clock_control_expires_session` (+ plan-added `::test_wall_clock_control_leaves_demo_clock`, `::test_wall_clock_control_moves_server_clock`) | integrated (expiry steps blocked on AEA-44 / AEA-43 until bound) |
| AC-18 | regression/context | Same change updates the four context rows | step 12 | `git diff --stat` shows only owned files + those four files | — |
| PA-1 | invariant (plan-added) | The socket guard refuses a non-loopback connect and allows loopback; restores `socket.socket.connect` on exit | `server.socket_guard()` | `test_support.py::test_socket_guard_refuses_non_loopback` | mock-tested |
| PA-2 | invariant (plan-added) | `OPERATION_OWNERS` covers exactly the OpenAPI's 30 operationIds | `steps.OPERATION_OWNERS` | asserted inside `::test_unbound_provider_blocked_then_strict_fails` | mock-tested |
| PA-3 | invariant (plan-added) | After a scripted turn, the script reports no `invalid_output` and no `exhausted` call and every queue is empty (a script that disagrees with the production schema fails J-1 visibly instead of degrading silently) | `JourneyScript.problems()`, `remaining()` | inside `::test_j1_one_turn_and_resend` | integrated |

**WP-N worked pair:** none applies. J-1's step 5 is a synthetic no-task turn (DO-4 §4), not one of WP-1…WP-8; its
input → output script is fixed in §6. **`[journey]` criteria:** AC-8, AC-9, AC-10, all at level *integrated with a
scripted model*.

### Source-contract reconciliation (obligations the issue might have missed)

| Obligation | Source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| Responses to page paths (not OpenAPI operations) still carry `X-Request-ID` | web.md §6 step 1 | implicit | added: `client.check_page_response` | step 6 |
| `turns.request_id` equals the HTTP `X-Request-ID` of that call (WF-1 correlation) | DO-6 WF-1; web.md §9 table | no | added (assert in AC-10 test) | step 11 |
| `turns.model_calls == 3`, `turns.cost_usd == 0.0` after the scripted turn | web.md §9 "counts … summed from spend_ledger rows"; M-25/26 | partly | added | step 11 |
| `staffing`, `limits`, `events.url` of `StartSessionResponse` validated | OpenAPI | yes via AC-5 check | in-ticket | — |
| Rate-limited reads (`startChatSession`, `getDemoClock`) stay under the bucket | web.md §5 | n/a | journeys make ≤ 3 such reads per session | — |
| Redaction of stored text | CAP-1, CAP-10 | excluded | other-ticket (CAP tests) | — |
| Browser level | rule §3.1 | excluded | other-ticket AEA-58 | — |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test code; J-1 drives WF-18 and WF-1, already registered) | — | — | — |

---

## 4. Shared code to use (copied from the current code; do not paraphrase)

### 4.1 App factory and overrides — `src/meridian/web/app.py` (AEA-23)

```python
@dataclass(frozen=True)
class ContainerOverrides:
    """Test-only substitutes. Only the lifespan reads this, and hands it once to the container builder."""
    choice: Mapping[ChoiceRole, ChoiceModel] | None = None
    structured: Mapping[StructuredRole, StructuredModel] | None = None
    tools: Mapping[ToolRole, ToolCallingModel] | None = None
    trace: TraceSink | None = None
    wall_clock: Callable[[], datetime] | None = None

def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> FastAPI: ...
# lifespan: container = build_container(app, resolved, overrides=overrides); app.state.container = container;
#           finally: app.state.container = None; container.close()
```

Import: `from meridian.web.app import ContainerOverrides, create_app`.

### 4.2 Container — `src/meridian/web/container.py` (AEA-01)

```python
class ContainerError(RuntimeError): ...
@dataclass(frozen=True)
class Key[T]:
    name: str
class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    settings (property) -> Any; limits (property) -> Limits; closed (property) -> bool
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...
    def get[T](self, key: Key[T]) -> T: ...   # raises ContainerError(f"not provided: {name}") when nobody provided it
    def on_start(self, starter: Callable[[], None]) -> None: ...
    def on_close(self, closer: Callable[[], None]) -> None: ...   # allowed after build, until closed; closers run newest first
    def build(self) -> None: ...
    def close(self) -> None: ...   # idempotent
```

Container key names the harness checks (strings; keys are equal by name): `"login_sessions"`, `"staff_access"`,
`"flag_service"`, `"session_service"`, `"turn_service"`, `"person_requests"`, `"handoff_service"`, `"case_service"`,
`"reply_composer"`, `"identity_service"`, `"demo_service"`, `"reset_service"`, `"reset_gate"`, `"live_chat"`,
`"metrics_reads"`, `"uow_factory"`, `"stream_poll_limiter"`, `"rate_limiter"`, `"wall_clock"`, `"heartbeat"` (all in
`web/deps.py`), plus `"demo_clock"` (AEA-30 plan PA-1), `"run_graph"` (AEA-40 plan R-6 / AEA-51), `"ledger"` (AEA-26),
`"trace"` (AEA-19), `"checkpointer"`, `"restore_working_copy"` (AEA-10).

### 4.3 Providers — `src/meridian/web/deps.py` (AEA-23)

```python
WALL_CLOCK: Key[Callable[[], datetime]] = Key("wall_clock")
def get_wall_clock(request: Request) -> Callable[[], datetime]: ...
def get_session_service(request: Request) -> Any: ...
def provided[T](app: Starlette, provider: Callable[..., T]) -> T: ...
# _bound(...) turns ContainerError("not provided: <key>") into RuntimeError(f"not bound: {provider.__name__}")
```

### 4.4 Middleware facts — `src/meridian/web/middleware.py`

`SESSION_COOKIE = "mhc_session"`, `HEALTHZ_PATH = "/healthz"`, `OPERATIONS_BY_ROUTE` (30 entries; equal to the OpenAPI's
operation set — verified 2026-10-21). Unauthenticated `/api/*` → `401 UNAUTHENTICATED details={"reason": "none"|"expired"}`;
unauthenticated GET page → `303` to `"/login?" + urlencode({"return_to": path, "reason": reason}, quote_via=quote)` →
`/login?return_to=%2Fstaff%2Fqueue&reason=none`. Login cookie built by
`session_cookie(token, max_age=limits.web.login_session_lifetime_s, secure=settings.cookie_secure)` →
`mhc_session=<token>; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200` (+ `; Secure` only when secure).

### 4.5 Log records — `src/meridian/web/logging.py`

```python
REQUEST_LOGGER = "meridian.web.request"; AUTH_LOGGER = "meridian.web.auth"; RECORD_ATTR = "meridian_record"
def emit_record(logger_name: str, fields: Mapping[str, object]) -> None:
    logging.getLogger(logger_name).info(str(fields["record"]), extra={RECORD_ATTR: dict(fields)})
# request:    {"record": "request", "request_id", "route", "status", "duration_ms", "caller_role", "thread_id", ["error_kind" on 5xx]}
# auth_event: {"record": "auth_event", "request_id", "outcome": "ok"|"rejected"|"rate_limited"|"logged_out", "session_id", "at"}
```

The `request` record is emitted in the middleware's `finally`, i.e. possibly **after** the client already has the response:
always look it up with `LogTap.wait_for(...)` (polls up to 2 s), never with a single read.

### 4.6 Settings — `src/meridian/config.py` (AEA-02)

```python
JEV_MODEL = "typesafe/jev-1.13"; SONNET_MODEL = "claude-sonnet-5-5"
class RoleSpec(MeridianModel): model: str; effort: ...; cap_s: float; max_tokens: int; redaction: RedactionProfile
class ModelSettings(MeridianModel):
    choice: dict[ChoiceRole, tuple[Literal["openrouter_jev", "anthropic"], RoleSpec]]
    structured: dict[StructuredRole, tuple[Literal["anthropic"], RoleSpec]]
    tools: dict[ToolRole, tuple[Literal["anthropic"], RoleSpec]]
ENV_NAMES: Mapping[str, str]   # 17 names, e.g. "demo_username" -> "MERIDIAN_DEMO_USERNAME"
class Settings(MeridianModel):
    anthropic_api_key: SecretStr; openrouter_api_key: SecretStr; models: ModelSettings = <defaults>
    langfuse_public_key/secret_key: SecretStr | None; langfuse_base_url/project_id: str | None
    demo_username: SecretStr; demo_password: SecretStr; session_secret: SecretStr; eval_key: SecretStr | None
    cookie_secure: bool = False; trust_proxy_headers: bool = False; web_dist_dir: Path; require_frontend: bool = False
    data_dir: Path = Path("var"); index_dir: Path; issued_db_path: Path = Path("docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite")
    agent_version: str = "dev"
    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Settings: ...   # reads only the 17 names; never os.environ itself
    def langfuse_complete(self) -> bool: ...
```

Default role map: planner → `("openrouter_jev", JEV_MODEL)`, classifier → `("openrouter_jev", JEV_MODEL)`,
planner_fallback → `("anthropic", SONNET_MODEL)`, responder → `("anthropic", SONNET_MODEL)`, brief →
`("anthropic", SONNET_MODEL)`, specialist → `("anthropic", SONNET_MODEL)`.

### 4.7 Model ports — `src/meridian/ports/models.py` (AEA-02) and `domain/common.py`

```python
ChoiceRole = Literal[Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK]
StructuredRole = Literal[Role.RESPONDER, Role.BRIEF]; ToolRole = Literal[Role.SPECIALIST]
class ChoiceField(MeridianModel): name: str; instructions: str; options: dict[str, str] = Field(max_length=255)
class ChoiceRequest(MeridianModel): system: str; state: dict[str, JsonValue]; fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel): choices: dict[str, str]; probabilities: dict[str, dict[str, float]] | None
class StructuredRequest[T: BaseModel](MeridianModel):
    system_prefix: str; system_dynamic: str; user: str; output_model: type[T]; max_tokens: int; effort: Literal["low","medium","high"] | None
class ToolSchema(MeridianModel): name: str; description: str; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolCall(MeridianModel): id: str; name: str; args: dict[str, JsonValue] | None
class ProviderMessages(MeridianModel): provider: ProviderName; model: str; items: tuple[JsonValue, ...]
class ToolStepRequest(MeridianModel):
    system_prefix: str; system_dynamic: str; messages: ProviderMessages; tools: tuple[ToolSchema, ...]; max_tokens: int; effort: ...
class ToolStep(MeridianModel): text: str; tool_calls: tuple[ToolCall, ...]; raw: ProviderTurn; stop_reason: str | None
class Attempt[T: BaseModel](MeridianModel): value: T | None; record: ProviderCall; failure: ProviderFailure | None
class ChoiceModel(Protocol):
    provider: ClassVar[ProviderName]
    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...
class StructuredModel(Protocol):
    provider: ClassVar[ProviderName]
    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...
class ToolCallingModel(Protocol):
    provider: ClassVar[ProviderName]
    def start(self, user: str) -> ProviderMessages: ...
    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...
    def append(self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]) -> ProviderMessages: ...
# domain/common.py
ProviderName = Literal["anthropic", "openrouter_jev"]
class ProviderFailureKind(StrEnum): ... INVALID_OUTPUT = "invalid_output" (14 values)
class ProviderFailure(MeridianModel): kind; provider: ProviderName; http_status: int | None; retry_after_s: float | None; retryable: bool; provider_request_id: str | None
class Role(StrEnum): PLANNER="planner"; CLASSIFIER="classifier"; PLANNER_FALLBACK="planner_fallback"; SPECIALIST="specialist"; RESPONDER="responder"; BRIEF="brief"
```

**`provider` is a `ClassVar`**, so one Python class can carry only one value. The scripted adapter is therefore one class
`ScriptedModel` (all three ports) with two one-line subclasses that only set `provider` (`ScriptedAnthropicModel`,
`ScriptedJevModel`) — the same pattern as AEA-11's `FakeChoiceModel` / `FakeAnthropicChoiceModel`.

### 4.8 Test doubles you may reuse — `tests/fakes/__init__.py` (AEA-11)

`from tests.fakes import ScriptedFailure, provider_call`:
`provider_call(*, provider, model, failure=None, stop_reason=None, ...) -> ProviderCall` builds a `ProviderCall` with
`cost_usd=0.0`, `cost_source="price_table"`, `status="error" if failure else "ok"`. `ScriptedFailure(kind,
http_status=None, retry_after_s=None, retryable=None)`.

### 4.9 Domain types used by assertions

`from meridian.domain.turn import ResponderDraft` (`text: str = Field(min_length=1, max_length=1200)`),
`from meridian.policy.texts import TextId, render` (`render(TextId.GREETING)` → the greeting, no placeholders),
`from meridian.policy.limits import Limits` (`Limits().web.login_session_lifetime_s == 43_200`; in a run use
`journey.container.limits.web.login_session_lifetime_s`), `from meridian.adapters.sqlite.migrate import ISSUED_TABLES,
WORKING_DB_NAME, schema_files` (`ISSUED_TABLES = ("customers", "technicians", "appointment_slots", "appointments",
"invoices")`, `WORKING_DB_NAME = "meridian.sqlite"`), `from tests.fixtures.sqlite import ISSUED_DB, temp_sqlite`.

### 4.10 OpenAPI check — `tests/api/openapi_check.py` (AEA-23, read-only)

```python
def assert_response_matches(response: _ResponseLike, operation_id: str) -> None: ...
# raises AssertionError("[OpenAPI 0.1.0-ux3] <operationId>: status 418 is not documented (documented: [...])") etc.
def load_contract() -> Contract: ...   # .operations: Mapping[str, OperationSpec] (30 operationIds)
```

Documented statuses used by J-1 (from `load_contract()`, 2026-10-21): `login` 200/400/401/429; `getSession` 200/401;
`startChatSession` 201/401/429/503; `getChatThread` 200/401/404/410; `submitTurn` 200/400/401/404/409/410/503;
`getDemoClock` 200 (`DemoClock`: `now`, `label`, `date_label`)/401/429.

### 4.11 Wire shapes asserted (OpenAPI, read-only)

`StartSessionResponse {thread_id, greeting: TextBlock{block_id, type:"text", speaker, at, text, sources}, demo_clock:
DemoClock, staffing, controller {kind, display_name}, settled: Settled{built_from, visit, request, identity{status, hint},
replying, actions}, events {url, last_event_id}, limits}`; `ChatThread {thread_id, state, turns[{turn_id, speaker{kind,
display_name}, at, text, blocks}], settled, demo_clock, staffing, last_event_id}`; `TurnRequest {turn_id (uuid), payload:
TextPayload {kind:"text", text (1..2000)}}`; `TurnResponse {thread_id, turn_id, sequence, blocks, settled, writes,
controller, notice, last_event_id}`; `ApiError {error {code, field, constraint, details}, request_id}`.

### 4.12 Stored columns asserted (`adapters/sqlite/schema/*.sql`, AEA-10)

`conversations(thread_id, demo_session, run_tag, run_id, agent_version, started_at, …, outcome, …,
last_customer_wall_at, controller, controller_name, …, live_state, …)`; `messages(id, thread_id, role, text, at, turn_id,
kind, card_id, choice_option)`; `turns(turn_id, thread_id, request_id, run_tag, …, agent_version, sequence, received_at,
status, gate_result, path, outcome, degrade_reason, …, plan_mode, …, specialists_run TEXT DEFAULT '[]', replied_at,
server_ms, model_calls, input_tokens, output_tokens, cost_usd, tool_calls, trace_id, trace_export, response)`;
`spend_ledger(id, recorded_at, thread_id, turn_id, request_id, run_tag, run_id, agent_version, role, provider, model,
attempt, …, cost_usd, cost_source, status, failure_kind, …)`; `staff_sessions(token_hash PK, session_id UNIQUE, role,
role_reset_pending, signed_in_demo, created_real, expires_real)`; `demo_state(id=1, demo_now, staffing)`. The working DB
is WAL mode (`adapters/sqlite/db.py` `connect`).

### 4.13 Libraries (already dependencies; add none)

`uvicorn 0.54.0` (`uvicorn.Config`, `uvicorn.Server`; `Server.started`, `Server.should_exit`, `Server.force_exit`,
`Server.servers[0].sockets[0].getsockname()`; signal capture is skipped off the main thread), `httpx 0.28.1`
(`httpx.Client`, `httpx.MockTransport`; cookies kept for a `127.0.0.1` host — verified 2026-10-21), `fastapi 0.156.8`
(`fastapi.routing.iter_route_contexts`), `pytest 9.1.1` (`pytest.StashKey`, `pytest.skip.Exception`,
`pytest.fail.Exception`).

---

## 5. Steps

Build in this order; each step is checkable on its own. Module dependency direction: `plugin` → `run` → (`env`,
`server`, `client`, `logtap`, `db`, `scripted_model`, `steps`, `record`); nothing in `support/` imports `plugin` except
`test_support.py`. Nothing in `support/` is imported by `src/meridian/`.

**Import rule for `plugin.py`:** at module level import only the standard library and `pytest` (plus `TYPE_CHECKING`-only
imports for annotations). Every other import happens inside the fixture or hook body. Reason: the root conftest loads this
plugin into **every** pytest session; a broken `meridian` import must not stop unrelated tests from starting.

### Step 1 — `env.py`: per-run environment and the issued-file guard

```python
REPO_ROOT = Path(__file__).resolve().parents[3]
PLACEHOLDER_ANTHROPIC_KEY = "journey-placeholder-anthropic-not-a-key"
PLACEHOLDER_OPENROUTER_KEY = "journey-placeholder-openrouter-not-a-key"

def letters(n: int) -> str: ...   # "".join(secrets.choice(string.ascii_lowercase) for _ in range(n))

def journey_environ(root: Path) -> dict[str, str]:
    """The environment the deployed app would get, for one run. Holds the per-run demo pair and secret: never print it."""
    return {
        "ANTHROPIC_API_KEY": PLACEHOLDER_ANTHROPIC_KEY,
        "OPENROUTER_API_KEY": PLACEHOLDER_OPENROUTER_KEY,
        "MERIDIAN_DEMO_USERNAME": "journeyuser" + letters(8),
        "MERIDIAN_DEMO_PASSWORD": "journeypass" + letters(20),
        "MERIDIAN_SESSION_SECRET": letters(48),
        "MERIDIAN_COOKIE_SECURE": "false",
        "MERIDIAN_REQUIRE_FRONTEND": "false",
        "MERIDIAN_WEB_DIST_DIR": str(root / "no-dist"),
        "MERIDIAN_DATA_DIR": str(root / "data"),
        "MERIDIAN_INDEX_DIR": str(root / "index"),
    }   # MERIDIAN_EVAL_KEY, the four LANGFUSE_*, MERIDIAN_TRUST_PROXY_HEADERS, MERIDIAN_AGENT_VERSION: deliberately absent

@dataclass(frozen=True)
class JourneyEnv:
    root: Path; data_dir: Path; web_dist_dir: Path; index_dir: Path
    settings: Settings
    issued_sha256_before: str
    @property
    def db_path(self) -> Path: return self.data_dir / WORKING_DB_NAME
    def secret_values(self) -> tuple[str, str]:  # (demo password, session secret)

@contextmanager
def journey_environment() -> Iterator[JourneyEnv]: ...
```

`journey_environment()` algorithm (invariant per line):
1. `root = Path(tempfile.mkdtemp(prefix="meridian-journey-"))` — not pytest's `tmp_path` (that one is kept after the run;
   AC-1 needs the folder gone).
2. `mkdir` `root/"data"` (empty; the app's first boot writes `meridian.sqlite` into it), `root/"no-dist"`, `root/"index"`.
3. `settings = Settings.from_env(journey_environ(root))` — the same path the deployed app uses; **never** touch `os.environ`.
4. If `Path(settings.issued_db_path).resolve() != ISSUED_DB.resolve()`: raise
   `RuntimeError("journey harness: run pytest from the repository root (Settings.issued_db_path resolves elsewhere)")`.
5. `before = sha256_file(ISSUED_DB)` (from `db.py`); yield `JourneyEnv(...)`.
6. After the body (normal exit only): `after = sha256_file(ISSUED_DB)`; if different raise
   `AssertionError("the issued scheduling DB changed during the journey run")`.
7. `finally: shutil.rmtree(root, ignore_errors=True)`.

### Step 2 — `scripted_model.py`: the scripted adapter

```python
@dataclass(frozen=True)
class RawToolCall:
    id: str
    name: str
    arguments: str            # the provider's raw JSON text for the arguments

@dataclass(frozen=True)
class RawToolStep:
    text: str
    calls: tuple[RawToolCall, ...] = ()
    stop_reason: str | None = "end_turn"

ScriptEntry = str | RawToolStep | ScriptedFailure   # str = raw JSON text of a choice or structured answer

CallResult = Literal["ok", "invalid_output", "scripted_failure", "exhausted"]

@dataclass(frozen=True)
class ScriptedCall:
    role: Role
    method: Literal["choose", "structured", "tool_step"]
    request: ChoiceRequest | StructuredRequest[Any] | ToolStepRequest
    timeout_s: float
    result: CallResult

CHOICE_ROLES = frozenset({Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK})
STRUCTURED_ROLES = frozenset({Role.RESPONDER, Role.BRIEF})
TOOL_ROLES = frozenset({Role.SPECIALIST})

class JourneyScript:
    """Per-role queues of raw provider output, consumed in order; shared by every ScriptedModel of one run. Thread-safe."""
    def __init__(self) -> None: ...
    def add(self, role: Role, *entries: ScriptEntry) -> None: ...
    def take(self, role: Role) -> ScriptEntry | None: ...      # None when the role's queue is empty
    def record(self, call: ScriptedCall) -> None: ...
    @property
    def calls(self) -> tuple[ScriptedCall, ...]: ...
    def remaining(self, role: Role | None = None) -> int: ...   # None = all roles
    def problems(self) -> tuple[ScriptedCall, ...]: ...         # calls whose result is "invalid_output" or "exhausted"

class ScriptedModel:
    """Test-only provider adapter for journeys (integrated-journeys rule §3.1). Implements ChoiceModel, StructuredModel and
    ToolCallingModel and parses raw scripted output the way the real adapters do (stage7/models.md §3). Never imported by
    src/meridian; reachable only through ContainerOverrides, which no env name or Settings field can build."""
    provider: ClassVar[ProviderName] = "anthropic"
    def __init__(self, script: JourneyScript, *, role: Role, model: str) -> None: ...
    @property
    def model(self) -> str: ...
    @property
    def role(self) -> Role: ...
    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...
    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...
    def start(self, user: str) -> ProviderMessages: ...
    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...
    def append(self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]) -> ProviderMessages: ...

class ScriptedAnthropicModel(ScriptedModel):
    provider: ClassVar[ProviderName] = "anthropic"

class ScriptedJevModel(ScriptedModel):
    provider: ClassVar[ProviderName] = "openrouter_jev"

def scripted_model_for(provider: ProviderName, script: JourneyScript, *, role: Role, model: str) -> ScriptedModel: ...

def scripted_overrides(
    settings: Settings, script: JourneyScript, *, wall_clock: Callable[[], datetime] | None
) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]: ...
```

Rules:
- `JourneyScript.add` raises `TypeError` when an entry does not fit the role: choice and structured roles accept `str` or
  `ScriptedFailure`; the tool role accepts `RawToolStep` or `ScriptedFailure`. (Invariant: a script mistake is caught when
  written, not mid-turn.)
- One lock (`threading.Lock`) guards the queues and the call list (planner and classifier run in parallel threads).
- **Every method records exactly one `ScriptedCall`** with its request and `timeout_s` (AC-2 "every request is recorded").
- `ok` record: `provider_call(provider=self.provider, model=self.model, stop_reason=<see below>)` → cost 0.0,
  `price_table`, status `ok`. It is a `ProviderCall`, never a `CallRecord` (the gateway wraps it, MOD-1).
- Invalid output: `failure = ProviderFailure(kind=ProviderFailureKind.INVALID_OUTPUT, provider=self.provider,
  http_status=200, retry_after_s=None, retryable=False, provider_request_id=None)`; record
  `provider_call(provider=…, model=…, failure=failure)`; return `Attempt(value=None, record=record, failure=failure)`.
  Never raise (models.md §3 catch-all: "never raises").
- `ScriptedFailure` entry: `retryable = entry.retryable if entry.retryable is not None else (entry.kind in {TIMEOUT,
  CONNECTION, RATE_LIMITED, OVERLOADED, SERVER} or (entry.kind is BODY_ERROR and entry.http_status in {408, 429, 500, 502,
  503, 504, 529}))`; build `ProviderFailure(kind=entry.kind, provider=self.provider, http_status=entry.http_status,
  retry_after_s=entry.retry_after_s, retryable=retryable, provider_request_id=None)`; result `"scripted_failure"`.
- Empty queue (`take` returns `None`): return the invalid-output `Attempt` and record result `"exhausted"`. (Invariant:
  the server keeps running and the journey fails on `problems()`; a `BaseException` raised inside the server's worker or
  LangGraph threads could hang the run.)

`choose` (invariant: a choice outside its field's options never becomes a value):
1. `entry = take(role)`; handle `None` / `ScriptedFailure` as above.
2. `data = json.loads(entry)`; `json.JSONDecodeError` → invalid.
3. `data` must be a `dict` whose values are all `str`, with `set(data) == {f.name for f in req.fields}` and
   `data[f.name] in f.options` for every field → else invalid.
4. Return `Attempt[ChoiceAnswer](value=ChoiceAnswer(choices=data, probabilities=None), record=ok(stop_reason=None), failure=None)`.

`structured` (invariant: only an `output_model`-valid object is returned):
1. take / failure as above. 2. `json.loads` → must be a `dict` → else invalid.
3. `value = req.output_model.model_validate(data)`; `pydantic.ValidationError` → invalid.
4. Return `Attempt(value=value, record=ok(stop_reason="end_turn"), failure=None)`.

`tool_step` (invariant: unparseable arguments become `args=None`, never a failure — models.md §3, graph-tools dispatch
handles it):
1. take / failure as above (entry must be `RawToolStep`).
2. For each `RawToolCall`: `try: parsed = json.loads(call.arguments) except json.JSONDecodeError: parsed = None`;
   `args = parsed if isinstance(parsed, dict) else None`; `ToolCall(id=call.id, name=call.name, args=args)`.
3. `raw = {"text": entry.text, "tool_calls": [{"id": c.id, "name": c.name, "arguments": c.arguments} for c in entry.calls],
   "stop_reason": entry.stop_reason}`.
4. Return `Attempt[ToolStep](value=ToolStep(text=entry.text, tool_calls=…, raw=raw, stop_reason=entry.stop_reason),
   record=ok(stop_reason=entry.stop_reason), failure=None)`.

`start` / `append`: same bodies as `tests/fakes/models.py` `FakeToolModel.start` / `.append` (copy the logic, not the
class): `start` returns `ProviderMessages(provider=self.provider, model=self.model, items=({"role": "user", "content":
user},))`; `append` raises `ValueError("ProviderMessages were built for another provider or model")` on a mismatch, then
appends `{"role": "assistant", "text": step.text, "tool_calls": [...]}` and, when `results` is non-empty,
`{"role": "tool_results", "results": [{"tool_call_id": i, "content": c} ...]}`.

`scripted_model_for`: `ScriptedJevModel` for `"openrouter_jev"`, `ScriptedAnthropicModel` for `"anthropic"`.

`scripted_overrides` (invariant: each role's object carries the provider and model that role's `RoleSpec` names, so ledger
rows name the configured model — models.md §7):
```python
choice = {role: scripted_model_for(p, script, role=role, model=spec.model) for role, (p, spec) in settings.models.choice.items()}
structured = {role: scripted_model_for(p, script, role=role, model=spec.model) for role, (p, spec) in settings.models.structured.items()}
tools = {role: scripted_model_for(p, script, role=role, model=spec.model) for role, (p, spec) in settings.models.tools.items()}
overrides = ContainerOverrides(choice=choice, structured=structured, tools=tools, trace=None, wall_clock=wall_clock)
return overrides, {**choice, **structured, **tools}
```
`trace=None` keeps the container's own choice (`NullTraceSink`, because no `LANGFUSE_*` is set).

### Step 3 — `server.py`: wall clock, launcher, socket guard

```python
FORBIDDEN_PORTS: frozenset[int] = frozenset({4019, 5184})   # the UX track's Prism and Vite ports

class StepClock:
    """The journey wall clock (Innocent D-13; web.md §15): real UTC time plus an offset the test moves forward."""
    def __init__(self) -> None: ...
    def __call__(self) -> datetime: ...          # datetime.now(UTC) + timedelta(seconds=offset), read under a lock
    def advance(self, seconds: float) -> None: ...   # ValueError when seconds < 0
    @property
    def offset_s(self) -> float: ...

@dataclass
class RunningServer:
    app: FastAPI
    container: Container
    host: str
    port: int
    thread: threading.Thread
    close_count: int = 0
    @property
    def base_url(self) -> str: return f"http://{self.host}:{self.port}"
    def note_closed(self) -> None: self.close_count += 1

@contextmanager
def launch_server(settings: Settings, *, overrides: ContainerOverrides | None, startup_timeout_s: float = 30.0) -> Iterator[RunningServer]: ...

class SocketGuard:
    blocked: list[tuple[str, int]]
    def check(self, address: object) -> None: ...

@contextmanager
def socket_guard() -> Iterator[SocketGuard]: ...
```

`launch_server` algorithm:
1. `app = create_app(settings, overrides=overrides)`.
2. `config = uvicorn.Config(app, host="127.0.0.1", port=0, lifespan="on", log_config=None, access_log=False, http="h11",
   loop="asyncio", ws="none", timeout_graceful_shutdown=5)` — `log_config=None` stops uvicorn from reconfiguring logging;
   port 0 = OS-assigned (never 4019 or 5184 by construction; still asserted).
3. `server = uvicorn.Server(config)`; `thread = threading.Thread(target=server.run, name="journey-uvicorn", daemon=True)`;
   `thread.start()`.
4. Poll every 0.02 s until `server.started` is `True`. If the thread dies first → `RuntimeError("journey server stopped
   during start-up (the app lifespan failed; see the captured log)")`. If `startup_timeout_s` passes →
   `server.should_exit = True`, `thread.join(10)`, `RuntimeError("journey server did not start within …s")`. **Readiness is
   `server.started` (set by uvicorn after the lifespan startup completed and the socket is listening), never `/healthz`**.
5. `container = app.state.container`; if `None` → `RuntimeError`. `port = server.servers[0].sockets[0].getsockname()[1]`;
   if `port in FORBIDDEN_PORTS` or `port <= 0` → stop the server and raise.
6. `running = RunningServer(app, container, "127.0.0.1", port, thread)`; `container.on_close(running.note_closed)`.
7. `try: yield running` / `finally: server.should_exit = True; thread.join(timeout=15); if thread.is_alive():
   server.force_exit = True; thread.join(timeout=5)`. The lifespan closes the container exactly once (AC-4).

`socket_guard` (invariant: no request leaves loopback, in any thread of the process):
1. Save `original_connect = socket.socket.connect`, `original_connect_ex = socket.socket.connect_ex`.
2. Replace both on the `socket.socket` class (`# type: ignore[method-assign]`) with wrappers that call
   `guard.check(address)` first, then the original.
3. `SocketGuard.check`: if `address` is not a tuple (AF_UNIX path) → allow. `host = str(address[0])`; `"localhost"` →
   allow. `ip = ipaddress.ip_address(host.split("%")[0])` — a `ValueError` (a hostname) counts as non-loopback.
   `ip.is_loopback` → allow. Otherwise append `(host, int(address[1]))` to `blocked` (under a lock) and raise
   `OSError(errno.EACCES, "journey socket guard: non-loopback connection refused")`.
4. `finally`: restore both originals.

### Step 4 — `db.py`: read-only reader

```python
class DbReader:
    def __init__(self, db_path: Path) -> None: ...
    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]: ...
        # sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, isolation_level=None, timeout=5.0)
        # conn.row_factory = sqlite3.Row; closed in finally; one connection per assertion
    def rows(self, sql: str, params: Sequence[object] = ()) -> list[dict[str, Any]]: ...
        # after fetchall: if conn.in_transaction: raise AssertionError("DbReader left a transaction open")
    def one(self, sql: str, params: Sequence[object] = ()) -> dict[str, Any]: ...    # AssertionError unless exactly one row
    def scalar(self, sql: str, params: Sequence[object] = ()) -> Any: ...
    def count(self, table: str, where: str = "", params: Sequence[object] = ()) -> int: ...
        # table must match ^[a-z_]+$ (ValueError otherwise); f"SELECT COUNT(*) FROM {table}" + (f" WHERE {where}" if where else "")  # noqa: S608
    def table_rows(self, table: str) -> list[tuple[Any, ...]]: ...   # SELECT * FROM {table} ORDER BY rowid  # noqa: S608

def issued_rows(table: str, issued_path: Path = ISSUED_DB) -> list[tuple[Any, ...]]: ...
    # sqlite3.connect(f"{issued_path.resolve().as_uri()}?mode=ro&immutable=1", uri=True); ORDER BY rowid; close in finally
def sha256_file(path: Path) -> str: ...   # hashlib.sha256 over 1 MiB chunks of open(path, "rb")
```

`isolation_level=None` means autocommit: a `SELECT` never opens a transaction, so the reader never holds a read
transaction across a request (AC-6).

### Step 5 — `logtap.py`: keep every log record

```python
class LogTap(logging.Handler):
    def __init__(self) -> None: ...                 # level DEBUG; list of LogRecord under a lock
    def emit(self, record: logging.LogRecord) -> None: ...
    def structured(self, kind: str) -> list[dict[str, object]]: ...
        # dict(record.__dict__[RECORD_ATTR]) for each record whose RECORD_ATTR payload is a Mapping with payload["record"] == kind
    def wait_for(self, kind: str, predicate: Callable[[Mapping[str, object]], bool], *, timeout_s: float = 2.0) -> dict[str, object]: ...
        # poll every 0.01 s; on timeout AssertionError(f"no {kind} record matched within {timeout_s}s")
    def all_text(self) -> str: ...
        # for each record: logging.Formatter().format(record) + "\n" + repr(vars(record)); joined with "\n"

@contextmanager
def tap_logs() -> Iterator[LogTap]: ...   # logging.getLogger().addHandler(tap); finally removeHandler
```

Attach to the **root** logger: `meridian.*`, `uvicorn.*` and `httpx` records all propagate there (handler levels, not
ancestor logger levels, decide), so the secret scan sees every record the run produced.

### Step 6 — `client.py`: the journey client

```python
class JourneyClient:
    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None) -> None: ...
        # httpx.Client(base_url=base_url, follow_redirects=False, timeout=httpx.Timeout(70.0), transport=transport)
        # 70 s: the turn deadline is 60 s (Limits.turn) and the browser gives up at 65 s
    responses: list[httpx.Response]
    def call(self, method: str, path: str, *, operation_id: str | None, body: object | None = None,
             headers: Mapping[str, str] | None = None) -> httpx.Response: ...
    def cookie(self, name: str = "mhc_session") -> str | None: ...
    def close(self) -> None: ...

def check_page_response(response: httpx.Response) -> None: ...   # AssertionError unless "X-Request-ID" in response.headers
def set_cookie_lines(response: httpx.Response) -> list[str]: ...  # response.headers.get_list("set-cookie")
def cookie_attributes(line: str) -> dict[str, str | None]: ...
    # "mhc_session=abc; Path=/; HttpOnly" -> {"mhc_session": "abc", "path": "/", "httponly": None}; names after the first lower-cased
```

`call` algorithm (invariant: no API response escapes the OpenAPI check):
1. If `path.startswith("/api/")` and `operation_id is None` → `AssertionError(f"{method} {path}: an API step must name its
   operationId")` **before** sending.
2. `response = self._http.request(method, path, json=body, headers=headers)`; append to `responses`.
3. If `operation_id` is set: `try: assert_response_matches(response, operation_id) except AssertionError as exc: raise
   AssertionError(f"{operation_id} -> HTTP {response.status_code}: {exc}") from None`. Never put the response body in the
   message.
4. Else (a page path): `check_page_response(response)`.

### Step 7 — `steps.py`: owners, preflight, results, collector, convention

```python
NEED_OWNERS: Mapping[str, str] = MappingProxyType({
    "login_sessions": "AEA-44", "staff_access": "AEA-44", "flag_service": "AEA-44",
    "session_service": "AEA-40", "turn_service": "AEA-40",
    "demo_service": "AEA-30", "demo_clock": "AEA-30",
    "reply_composer": "AEA-51", "run_graph": "AEA-51",
    "person_requests": "AEA-42", "handoff_service": "AEA-29", "case_service": "AEA-29",
    "identity_service": "AEA-27", "reset_service": "AEA-31", "live_chat": "AEA-46", "metrics_reads": "AEA-53",
    "ledger": "AEA-26", "trace": "AEA-19", "heartbeat": "AEA-32",
    "uow_factory": "AEA-10", "checkpointer": "AEA-10", "restore_working_copy": "AEA-10",
    "reset_gate": "AEA-23", "rate_limiter": "AEA-23", "stream_poll_limiter": "AEA-23", "wall_clock": "AEA-23",
})
OPERATION_OWNERS: Mapping[str, str] = MappingProxyType({
    "login": "AEA-23", "logout": "AEA-23",
    "getSession": "AEA-44", "listDemoRoles": "AEA-44", "switchRole": "AEA-44",
    "startChatSession": "AEA-40", "getChatThread": "AEA-40", "submitTurn": "AEA-40",
    "streamChatEvents": "AEA-41",
    "requestPerson": "AEA-42", "saveFollowUp": "AEA-42",
    "listDemoInbox": "AEA-43", "getStaffing": "AEA-43", "setStaffing": "AEA-43", "getDemoClock": "AEA-43", "resetDemo": "AEA-43",
    "advanceDemoClock": "AEA-47",
    "getQueue": "AEA-45", "getCase": "AEA-45", "applyCaseAction": "AEA-45", "recordContactActivity": "AEA-45",
    "createFlag": "AEA-45", "listFlags": "AEA-45", "reviewFlag": "AEA-45", "getOversight": "AEA-45",
    "liveChatAction": "AEA-46", "streamCaseEvents": "AEA-46",
    "getOwnerMetrics": "AEA-48", "getMonitoring": "AEA-48", "getLatestEval": "AEA-48",
})   # exactly the 30 OpenAPI operationIds (PA-2)

@dataclass(frozen=True)
class Missing:
    what: str      # "login_sessions not bound" | "operation startChatSession not routed"
    owner: str     # "AEA-44"

@dataclass(frozen=True)
class StepResult:
    journey: str                       # "J-1"
    step: str                          # "3 login"
    nodeid: str
    status: Literal["pass", "fail", "blocked"]
    detail: str                        # "" on pass; first line of the failure (≤ 300 chars); the blocked message
    blocked_on: tuple[str, ...]
    seconds: float

@dataclass(frozen=True)
class TestOutcome:
    nodeid: str
    outcome: str                       # "passed" | "failed" | "skipped"
    duration_s: float

@dataclass(frozen=True)
class RunNote:                         # one per launched server
    host: str; port: int; agent_version: str
    models: Mapping[str, str]          # role value -> "provider/model"
    issued_sha256: str; spend_rows: int; spend_total_usd: float; outbound_blocked: int

class StepCollector:
    def __init__(self) -> None: ...    # steps: list[StepResult]; tests: list[TestOutcome]; notes: list[RunNote]
    def add_step(self, result: StepResult) -> None: ...
    def add_test(self, outcome: TestOutcome) -> None: ...
    def add_note(self, note: RunNote) -> None: ...

JOURNEY_NODEID = re.compile(r"^tests/journeys/(j(?:[1-9]|10)|browser)/")

def missing_needs(container: Container, app: FastAPI, needs: Sequence[str], operations: Sequence[str]) -> tuple[Missing, ...]: ...
def blocked_message(missing: Sequence[Missing]) -> str: ...
def stop_blocked(missing: Sequence[Missing], *, strict: bool) -> NoReturn: ...
def convention_violations(root: Path) -> list[str]: ...
```

`missing_needs` (invariant: a step runs only when every service and route it touches is bound; an unknown name is a harness
bug, not a skip):
1. For each `name` in `needs`: if `name not in NEED_OWNERS` → `KeyError(f"unknown need {name!r}: add it to NEED_OWNERS
   (a follow-up on AEA-57)")`. `try: container.get(Key[object](name)) except ContainerError as exc: if str(exc) ==
   f"not provided: {name}": append Missing(f"{name} not bound", NEED_OWNERS[name]); else: raise`.
2. `routed = {getattr(ctx, "operation_id", None) for ctx in iter_route_contexts(app.router.routes)}`.
3. For each `op` in `operations`: unknown → `KeyError`; `op not in routed` → `Missing(f"operation {op} not routed",
   OPERATION_OWNERS[op])`.
4. Import `ContainerError`, `Key` and `iter_route_contexts` **inside** the function (step 5 import rule).

`blocked_message`: owners de-duplicated in first-seen order: `f"blocked-on {', '.join(owners)}: {'; '.join(m.what for m in
missing)}"` → e.g. `blocked-on AEA-40, AEA-30: session_service not bound; demo_service not bound`.

`stop_blocked`: `if strict: pytest.fail(msg + " [--journeys-strict]", pytrace=False)`; else `pytest.skip(msg)`.

`convention_violations(root)`: for every directory `d` in `root/"tests"/"journeys"` whose name starts with `j` and is not
`__pycache__`: the name must match `^j([1-9]|10)$` else violation `f"{d.name}: not j1…j10"`; for every `*.py` file in it
except `__init__.py`: name must match `^test_aea_\d{2}\.py$` else violation `f"{d.name}/{f.name}: not test_aea_<NN>.py"`.
Return the sorted list.

### Step 8 — `record.py`: the evidence record

```python
FIELDS: tuple[str, ...] = ("Claim", "Level", "Tested revision", "Environment", "Command", "Result",
                           "Evidence location", "Remaining limitations", "Blocked by")
SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,40}$")
LEVEL = "integrated with a scripted model"

@dataclass(frozen=True)
class RecordData:
    scope: str
    values: Mapping[str, str]          # one entry per FIELDS name

def tested_revision(root: Path, agent_version: str) -> str: ...
def build_record_data(*, scope: str, collector: StepCollector, root: Path, command: str) -> RecordData: ...
def render_record(data: RecordData) -> str: ...
def record_path(root: Path, scope: str, day: date) -> Path: ...     # root/"docs/testing/journeys"/f"{day.isoformat()}-{scope}.md"
def maybe_write_record(scope: str | None, *, root: Path, collector: StepCollector, command: str, day: date) -> Path | None: ...
```

- `tested_revision`: `sha = git -C root rev-parse --short HEAD`; `dirty = git -C root status --porcelain -- src tests
  eval pyproject.toml uv.lock` is non-empty; return `f"{sha}; agent_version {agent_version}"` or `f"uncommitted (HEAD
  {sha}); agent_version {agent_version}"`; if git fails → `f"unknown (git unavailable); agent_version {agent_version}"`.
  Use `subprocess.run([...], capture_output=True, text=True, check=False)`.
- `build_record_data` uses only steps and tests whose `nodeid` matches `JOURNEY_NODEID` (self-checks stay out). Values:
  - **Claim** — `f"{scope}: journeys {ids} through the real app over HTTP (API level) with the scripted model; per-step results under Result"` (ids sorted, e.g. `J-1`).
  - **Level** — `LEVEL + " for the steps marked pass"`; when no step passed: `"none reached: every step was blocked or failed"`.
  - **Tested revision** — `tested_revision(root, note.agent_version)` from the first `RunNote` (`"dev"` when none).
  - **Environment** — `f"{host} (ephemeral port per test, last {port}); server: uvicorn.Server in a background thread over create_app(Settings.from_env(<journey environ>), overrides=ContainerOverrides(choice, structured, tools, wall_clock)); DB copy: docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite (sha256 {issued_sha256}) copied by the app's first boot into a temp MERIDIAN_DATA_DIR; frontend build: none (API level); model adapter: ScriptedModel (tests/journeys/support/scripted_model.py); model ids: {role=provider/model, …}"`.
  - **Command** — the `command` argument.
  - **Result** — one line per step joined with `<br>`: `f"{journey} · {step} ({test function name}): pass"`, `"…: fail: {detail}"`, `"…: {detail}"` for blocked (detail starts `blocked-on`); then `f"{journey} wall time: {sum of TestOutcome.duration_s for that journey's nodeids:.1f} s across {n} tests"`; when no step ran: `"no journey steps ran"`.
  - **Evidence location** — `f"this file; pytest output of the command; spend_ledger rows written: {sum spend_rows}, total cost_usd {sum spend_total_usd:.2f}; non-loopback connections refused: {sum outbound_blocked}"`.
  - **Remaining limitations** — `"API level only (browser journeys: AEA-58); scripted model only (live models: AEA-61); J-1 only (other journeys land with their tickets); redaction is not re-checked here (CAP tests); held-out data is never read"`. (Wording is fixed; note "held-out" carries a hyphen.)
  - **Blocked by** — sorted unique owners of blocked steps joined with `", "`, or `"none"`.
- `render_record`: `f"# Journey record: {scope} (journey harness run)\n\n| Field | Value |\n|---|---|\n"` + one row per
  `FIELDS` name in order: `f"| {name} | {value} |"`, where `value` has `|` replaced by `\|` and newlines by `<br>`.
- `maybe_write_record`: `None` scope → return `None`, write nothing. Else `SCOPE_PATTERN` must match (else
  `ValueError`); `path.parent.mkdir(parents=True, exist_ok=True)`; write UTF-8; return the path.
- The record never receives the demo pair, the session secret or a cookie value: none of those is in `StepCollector`.

### Step 9 — `run.py`: `JourneyRun` and `open_journey()`

```python
@dataclass(frozen=True)
class LoginResult:
    client: JourneyClient
    response: httpx.Response
    session_id: str          # the new staff_sessions.session_id (opaque UUID)
    cookie: str              # the mhc_session value: assert with it, never print it

@dataclass
class JourneyRun:
    env: JourneyEnv
    server: RunningServer
    script: JourneyScript
    models: Mapping[Role, ScriptedModel]
    clock: StepClock | None
    db: DbReader
    logs: LogTap
    guard: SocketGuard
    collector: StepCollector
    strict: bool
    nodeid: str
    clients: list[JourneyClient] = field(default_factory=list)

    @property
    def settings(self) -> Settings: ...
    @property
    def app(self) -> FastAPI: ...
    @property
    def container(self) -> Container: ...
    @property
    def base_url(self) -> str: ...
    @property
    def demo_username(self) -> str: ...            # settings.demo_username.get_secret_value()
    def secret_values(self) -> tuple[str, str]: ...    # env.secret_values()
    def client(self) -> JourneyClient: ...          # new client with its own cookie jar; closed at teardown
    def login(self, client: JourneyClient | None = None) -> LoginResult: ...
    @contextmanager
    def step(self, journey: str, name: str, *, needs: Sequence[str] = (), operations: Sequence[str] = ()) -> Iterator[None]: ...
    def files_containing(self, value: str) -> list[str]: ...   # names (relative to data_dir) of files whose bytes contain value
    def close_clients(self) -> None: ...

@contextmanager
def open_journey(*, collector: StepCollector, strict: bool, with_clock: bool, nodeid: str) -> Iterator[JourneyRun]: ...
```

`login` algorithm: `c = client or self.client()`; `before = {r["session_id"] for r in self.db.rows("SELECT session_id FROM
staff_sessions")}`; `resp = c.call("POST", "/api/login", operation_id="login", body={"username": …, "password": …})`;
`resp.status_code != 200` → `AssertionError(f"login answered HTTP {resp.status_code}")`; `new = after - before`; exactly one
else `AssertionError(f"login stored {len(new)} new staff_sessions rows, expected 1")`; `cookie = c.cookie()`; missing →
`AssertionError("login set no mhc_session cookie")`; return `LoginResult`.

`step` algorithm (invariant: a blocked step never counts as a pass; every step leaves exactly one `StepResult`):
1. `start = time.perf_counter()`; `missing = missing_needs(self.container, self.app, needs, operations)`.
2. If `missing`: `add_step(StepResult(journey, name, self.nodeid, "blocked", blocked_message(missing), owners, 0.0))`
   then `stop_blocked(missing, strict=self.strict)` (raises).
3. `try: yield` — `except Exception as exc: add_step(... "fail", first line of str(exc)[:300] or type name ...); raise`
   — `except BaseException: raise` (skip/fail/KeyboardInterrupt pass through unrecorded) — `else: add_step(... "pass", "",
   (), time.perf_counter() - start)`.

`files_containing(value)`: for every file under `env.data_dir.rglob("*")` (includes `-wal`, `-shm`, checkpoints), read
bytes, return names whose bytes contain `value.encode("utf-8")`. Call it while the server is still running.

`open_journey` algorithm (order matters; each line names what it protects):
```python
with socket_guard() as guard, tap_logs() as logs, journey_environment() as env:   # guard outermost: active through teardown
    script = JourneyScript()
    clock = StepClock() if with_clock else None                                    # without the fixture: wall_clock=None (real time)
    overrides, models = scripted_overrides(env.settings, script, wall_clock=clock)
    with launch_server(env.settings, overrides=overrides) as server:
        run = JourneyRun(env=env, server=server, script=script, models=models, clock=clock, db=DbReader(env.db_path),
                         logs=logs, guard=guard, collector=collector, strict=strict, nodeid=nodeid)
        try:
            yield run
        finally:
            run.close_clients()                                                     # before the server stops
    spend = DbReader(env.db_path).one("SELECT COUNT(*) AS n, COALESCE(SUM(cost_usd), 0.0) AS total FROM spend_ledger")
    collector.add_note(RunNote(host=server.host, port=server.port, agent_version=env.settings.agent_version,
                               models={r.value: f"{m.provider}/{m.model}" for r, m in models.items()},
                               issued_sha256=env.issued_sha256_before, spend_rows=int(spend["n"]),
                               spend_total_usd=float(spend["total"]), outbound_blocked=len(guard.blocked)))
# env exited: issued hash re-checked, temp root removed
if guard.blocked:
    raise AssertionError(f"journey socket guard refused {len(guard.blocked)} non-loopback connection(s): {guard.blocked}")
```

### Step 10 — `plugin.py`: options, fixtures, record hook

```python
PUBLIC_FIXTURES: tuple[str, ...] = ("journey", "journey_clock")
OPTIONS: tuple[str, ...] = ("--journey-record", "--journeys-strict")
COLLECTOR_KEY = pytest.StashKey["StepCollector"]()

def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("journeys", "integrated journeys (AEA-57)")
    group.addoption("--journey-record", action="store", default=None, metavar="SCOPE",
                    help="write docs/testing/journeys/<date>-<SCOPE>.md for this run (integrated-journeys rule §4)")
    group.addoption("--journeys-strict", action="store_true", default=False,
                    help="a blocked journey step fails instead of being skipped (wave merge and pre-deploy runs)")

def pytest_configure(config: pytest.Config) -> None:
    # import StepCollector lazily; register one _JourneyRecorder(config) with
    # config.pluginmanager.register(recorder, "meridian-journey-recorder"); config.stash[COLLECTOR_KEY] = recorder.collector

class _JourneyRecorder:
    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None: ...
        # when JOURNEY_NODEID matches and (report.when == "call" or report.skipped): add TestOutcome(nodeid, outcome, duration)
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None: ...
        # if hasattr(config, "workerinput"): return  (xdist worker: no record)
        # scope = config.getoption("--journey-record"); command = "uv run pytest " + shlex.join(config.invocation_params.args)
        # path = maybe_write_record(scope, root=Path(config.rootpath), collector=…, command=command,
        #                           day=datetime.now(ZoneInfo("America/Chicago")).date())
        # if path: terminal reporter (config.pluginmanager.get_plugin("terminalreporter")) .write_line(f"journey record: {path}")

@pytest.fixture
def journey(request: pytest.FixtureRequest) -> Iterator[JourneyRun]:
    """A running real app on a disposable DB copy with the scripted model (see support/README.md)."""
    from tests.journeys.support.run import open_journey
    with open_journey(collector=request.config.stash[COLLECTOR_KEY],
                      strict=bool(request.config.getoption("--journeys-strict")),
                      with_clock="journey_clock" in request.fixturenames,
                      nodeid=request.node.nodeid) as run:
        yield run

@pytest.fixture
def journey_clock(journey: JourneyRun) -> StepClock:
    """The run's wall clock; .advance(seconds) moves get_wall_clock() forward, the demo clock stays (D-13)."""
    assert journey.clock is not None
    return journey.clock
```

`request.fixturenames` holds the test's whole fixture closure, so `journey` knows whether `journey_clock` was asked for and
passes `wall_clock=None` otherwise (AC-17 last clause).

### Step 11 — the two test files (named tests below), then README

Write `test_support.py` and `j1/test_aea_57.py` as specified in §7.1/§7.2, then `support/README.md` (§7.3). Run the self-
checks and J-1 (§7 commands 1, 2) until green or *blocked* exactly where §7.2 says.

### Step 12 — commits, record, context rows

1. Lint, format, type check, affected tests, affected journeys, full suite (§7 table) → green.
2. Commit 1 (code and tests only): `git add tests/journeys/support tests/journeys/j1/test_aea_57.py` →
   `feat(AEA-57): journey harness (tests/journeys/support) and journey J-1`. Note its short SHA as `<sha>`.
3. If `main` moved since the branch was cut (AEA-44, 40, 30 may have merged): `git merge --no-edit main` (never rebase a
   pushed branch, never force-push), re-run §7 commands 1–2. More J-1 steps then reach the integrated level.
4. On the now-clean tree run **command 2** (`--journey-record=AEA-57`); it writes `docs/testing/journeys/<run-date>-AEA-57.md`
   with *Tested revision* `<sha or merge sha>; agent_version dev`.
5. Edit the four context rows (exact text in §7.4), using the record's file name and `<sha>`.
6. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .`; fix any FAIL that is in a row you own.
7. Commit 2: `git add docs/testing/journeys/<run-date>-AEA-57.md .claude/reference/area-map.md .claude/state/icm-progress.md
   docs/design/code-design.md PROJECT-CHECKLIST.md` → `docs(AEA-57): journey record and context rows`.
8. Every commit message ends with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Explicit paths only;
   never `git add -A`. Do not push (the merge step pushes `main`).

### What the implementer must NOT do

- Edit anything under `src/meridian/`, `tests/conftest.py`, `tests/fakes/`, `tests/fixtures/`, `tests/api/`,
  `tests/journeys/{README.md,affected.py,__init__.py}`, any `tests/journeys/j*/__init__.py`, another ticket's journey file,
  `pyproject.toml`, `uv.lock`, `apps/web/**`, `docs/ux/**`, the OpenAPI, `UI_CONTRACTS.md`, issued data, the briefing,
  `docs/archive/`, `docs/parked/`.
- Use `app.dependency_overrides`, `monkeypatch` on any `meridian` module, `TestClient`, a session-store or service double, or
  any stand-in above the three model ports **inside J-1**. (Self-checks AC-5 and AC-7 use a throwaway transport / bare
  container on purpose; they are labelled `mock-tested`.)
- Set or read `os.environ` for the app, read `.env`, or bind any port except `127.0.0.1:0`.
- Print or write the demo username, demo password, session secret, a cookie value or a `token_hash`.
- Write the strings `heldout` or `key_dir` anywhere under `tests/journeys/` (AC-13's grep must print nothing; write
  "held-out" with a hyphen in prose).
- Turn a blocked step into a pass, edit an expectation to match observed behaviour, or catch `pytest.skip.Exception`.
  A J-1 expectation that the real code contradicts is reported as a seam finding on issue #57.
- Add a dependency, a `Settings` field, an env name, a CLI flag or a route.
- Patch `os._exit` or the watchdog (see R-5).
- Edit the `Last reconciled:` line of `icm-progress.md` or `.claude/state/resume.md`.

---

## 6. Data and fixtures (synthetic only)

| Data | Value / source |
|---|---|
| Demo pair, session secret | Per run, letters only: `"journeyuser" + 8 letters`, `"journeypass" + 20 letters`, 48 letters (`env.letters`, `secrets.choice`). Never written to disk or printed |
| Provider keys | Fixed placeholders `journey-placeholder-anthropic-not-a-key`, `journey-placeholder-openrouter-not-a-key` (not secrets) |
| Database | The issued `meridian_scheduling.sqlite` (ISSUED-DATA, read-only), copied by the app's own first boot into the temp data dir |
| Step 5 customer text | `"Hi, what can you help me with?"` |
| Step 5 script (the answer key) | `Role.PLANNER`: `'{"knowledge": "no", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"}'` (DO-4 §4 `PlannerChoices` field names); `Role.CLASSIFIER`: `'{"danger_level": "normal"}'` (field name `DANGER_FIELD = "danger_level"` from the AEA-37 plan §4.6; if AEA-37 merges another name the classifier call shows as `invalid_output` and PA-3 fails: report it, do not change the expectation silently); `Role.RESPONDER`: `json.dumps({"text": RESPONDER_TEXT})` validated against `ResponderDraft` |
| `RESPONDER_TEXT` | `"I can answer questions about memberships, billing and warranties, or help you find a time for a service visit. What would you like to do?"` (no completion word, no price, no promise, so R-46 checks have nothing to trim) |
| Step 8 text | `SENTINEL = "zqrejectedsentinel"`; `text = SENTINEL + "a" * (2001 - len(SENTINEL))` (2,001 characters, letters only) |
| Wrong password (step 2) | `"wrongpass" + letters(12)` |
| `turn_id`s | `str(uuid.uuid4())` per turn |
| AC-2 tool script | `RawToolStep(text="", calls=(RawToolCall(id="call-a", name="read_invoices", arguments='{"invoice_id": "INV-A"}'), RawToolCall(id="call-b", name="read_invoices", arguments='{bad')), stop_reason="tool_use")` |

---

## 7. Checks

### 7.1 `tests/journeys/support/test_support.py` (not marked `journey`; harness self-checks)

| Test | What it does and asserts | Prints (evidence) |
|---|---|---|
| `test_disposable_copy_and_issued_untouched` (AC-1) | `with socket_guard(), journey_environment() as env:` assert `not env.db_path.exists()`; `with launch_server(env.settings, overrides=None):` assert `env.db_path.exists()`; for each `ISSUED_TABLES` table `DbReader(env.db_path).table_rows(t) == issued_rows(t)`; every table named by `CREATE TABLE IF NOT EXISTS (\w+)` in each `schema_files()` file exists in `sqlite_master`; keep `root = env.root`. After both blocks: `not root.exists()` and `sha256_file(ISSUED_DB) == env.issued_sha256_before` | both hashes; five row counts; "temp root removed: True" |
| `test_scripted_model_parses_like_adapters` (AC-2) | Planner `ScriptedJevModel(script, role=Role.PLANNER, model=JEV_MODEL)` with a two-field `ChoiceRequest` (`knowledge` {no, yes}, `topic` {other, billing}): valid → `value.choices == {...}`, `probabilities is None`, `failure is None`, `record` is a `ProviderCall` and not a `CallRecord`, `provider == "openrouter_jev"`, `model == JEV_MODEL`, `cost_usd == 0.0`, `cost_source == "price_table"`, `status == "ok"`; option `"maybe"` → `INVALID_OUTPUT`, `retryable is False`, `record.status == "error"`, no exception; `'{"knowledge": "no"'` (unparseable) → `INVALID_OUTPUT`. Responder `ScriptedAnthropicModel(..., role=Role.RESPONDER, model=SONNET_MODEL)` with `StructuredRequest(output_model=ResponderDraft, …)`: `{"text": "hello"}` → `ResponderDraft`; `{"text": ""}` → `INVALID_OUTPUT`; `"not json"` → `INVALID_OUTPUT`. Specialist tool step (§6) → `tool_calls[0].args == {"invoice_id": "INV-A"}`, `tool_calls[1].args is None`, `failure is None`. One more planner `choose` on the empty queue → `INVALID_OUTPUT` and `script.problems()` has one `"exhausted"` call. `len(script.calls) == 8`. `JourneyScript().add(Role.SPECIALIST, "text")` raises `TypeError`. `scripted_overrides(Settings.from_env(journey_environ(tmp_path)), JourneyScript(), wall_clock=None)`: for every role, `models[role].provider` / `.model` equal that role's configured provider / `RoleSpec.model` | the three failure kinds; calls per role |
| `test_scripted_model_not_selectable_in_deploy` (AC-3) | AST-scan every `src/meridian/**/*.py`: no `Import`/`ImportFrom` (level 0) whose module is `tests` or starts with `tests.`; no `Settings.model_fields` name and no `ENV_NAMES` value contains `scripted`, `journey` or `fake` (case-insensitive); `set(get_args(ProviderName)) == {"anthropic", "openrouter_jev"}`; every `Literal` value reachable in `ModelSettings.model_fields[...].annotation` (recursive `get_origin`/`get_args` walk) is in that set; `ScriptedAnthropicModel.provider` and `ScriptedJevModel.provider` are in that set (so the only route in is `ContainerOverrides`) | "import scan: 0 offenders" |
| `test_server_thread_ephemeral_port` (AC-4) | `with socket_guard(), journey_environment() as env, launch_server(env.settings, overrides=None) as server:` `host == "127.0.0.1"`, `0 < port`, `port not in {4019, 5184}`, `server.container is server.app.state.container`, `server.container.get(WALL_CLOCK)` is not a `StepClock`, `thread.is_alive()`. After the launcher block: `not thread.is_alive()`, `close_count == 1`, `server.container.closed`, `server.app.state.container is None` | host, port, close count, thread alive |
| `test_client_validates_every_response` (AC-5) | `httpx.MockTransport` handler: `GET /api/session` → 401 documented `ApiError` body `{"error": {"code": "UNAUTHENTICATED", "field": None, "constraint": None, "details": {"reason": "none"}}, "request_id": rid}` with header `X-Request-ID: rid`; `GET /api/demo/clock?case=status` → 418 `{}`; `GET /api/demo/clock?case=body` → 200 `{"now": 5}` with `X-Request-ID`. `JourneyClient("http://journey.test", transport=...)`: the 401 passes; the 418 raises `AssertionError` whose text contains `getDemoClock` and `418`; the 200 raises with `getDemoClock` and `200`; `call("GET", "/api/demo/clock", operation_id=None)` raises before sending (handler call count unchanged) | the two failing assertion texts |
| `test_db_reader_read_only` (AC-6) | `with temp_sqlite() as store:` `reader = DbReader(store.db_path)`; `with reader.connect() as conn:` an `INSERT INTO demo_state (id, demo_now, staffing) VALUES (1, 'x', 'nobody_online')` raises `sqlite3.OperationalError` matching `readonly`; after a `SELECT 1`, `conn.in_transaction is False`; `reader.count("conversations") >= 0` returns without error | the error text |
| `test_unbound_provider_blocked_then_strict_fails` (AC-7, PA-2) | `container = Container(settings=None, limits=Limits())`; provide only `Key[object]("login_sessions")`; `build()`; `app = FastAPI(); app.state.container = container`. `missing_needs(container, app, ("login_sessions", "session_service"), ("startChatSession",))` → two `Missing`, both owner `AEA-40`; `provided(app, get_session_service)` raises `RuntimeError` matching `not bound: get_session_service` (the provider agrees, web.md §4); `stop_blocked(missing, strict=False)` raises `pytest.skip.Exception` matching `blocked-on AEA-40`; `strict=True` raises `pytest.fail.Exception` matching `blocked-on AEA-40`; a collector holding that blocked `StepResult` (nodeid `tests/journeys/j1/test_aea_57.py::x`) renders a record whose *Blocked by* row contains `AEA-40` and whose *Result* contains `blocked-on AEA-40`; `missing_needs(..., ("not_a_need",), ())` raises `KeyError`; `set(OPERATION_OWNERS) == set(load_contract().operations)` | the record's Blocked by line |
| `test_evidence_record_fields` (AC-14) | Build a `StepCollector` with one pass, one fail, one blocked J-1 step, two `TestOutcome`s and one `RunNote`; `data = build_record_data(scope="AEA-57", collector=c, root=REPO_ROOT, command="uv run pytest -m journey tests/journeys/j1")`; `render_record(data)` contains `f"| {f} |"` for each of the nine `FIELDS`, in order; *Tested revision* matches `^([0-9a-f]{7,40}|uncommitted \(HEAD [0-9a-f]+\)|unknown \(git unavailable\)); agent_version ` ; *Environment* contains `127.0.0.1`, `none (API level)`, `ScriptedModel` and a model id; *Result* contains `: pass`, `: fail: ` and `blocked-on`. `maybe_write_record(None, root=tmp_path, …)` returns `None` and `not (tmp_path / "docs").exists()`; with `"AEA-57"` it returns `tmp_path/"docs/testing/journeys/<day>-AEA-57.md"`, which exists; `"../x"` raises `ValueError` | the nine field names |
| `test_readme_lists_public_fixtures` (AC-16) | Parse `support/README.md`: bullets ``- `name` `` under `## Public fixtures` == set(`PUBLIC_FIXTURES`); bullets ``- `--option…` `` under `## Options` (name up to `=` or backtick) == set(`OPTIONS`); AST of `plugin.py`: function names decorated with `pytest.fixture` / `pytest.fixture(...)` ⊇ `PUBLIC_FIXTURES` (a listed name with no fixture fails) | the listed names |
| `test_journey_file_convention` (AC-16) | `convention_violations(REPO_ROOT) == []`; in `tmp_path` build `tests/journeys/j3/test_bad.py` and `tests/journeys/j11/test_aea_99.py` → two violations | violations of the temp tree |
| `test_socket_guard_refuses_non_loopback` (PA-1) | Inside `socket_guard()`: `socket.create_connection(("192.0.2.1", 9), timeout=0.2)` raises `OSError` whose text contains `journey socket guard`; `guard.blocked == [("192.0.2.1", 9)]`; a listening `127.0.0.1:0` socket accepts a loopback connect. After exit `socket.socket.connect` is the original | blocked list |
| `test_wall_clock_control_moves_server_clock` (AC-17 mechanism; runs today) | Uses `journey, journey_clock`: `journey.container.get(WALL_CLOCK) is journey_clock`; `real = datetime.now(UTC)`; `journey_clock.advance(3600)`; `seen = provided(journey.app, get_wall_clock)()`; `seen.utcoffset() == timedelta(0)`; `3599 s <= seen - real <= 3605 s` | offset seen |
| `test_wall_clock_control_expires_session` (AC-17) | `lifetime = journey.container.limits.web.login_session_lifetime_s`. `with journey.step("harness", "wall clock expires a session", needs=("login_sessions",), operations=("login", "getSession")):` `signed = journey.login()`; `journey_clock.advance(lifetime - 1)`; `GET /api/session` (`getSession`) → 200; `journey_clock.advance(1)`; again → 401, `error.code == "UNAUTHENTICATED"`, `error.details.reason == "expired"` | the 200, the 401 with reason |
| `test_wall_clock_control_leaves_demo_clock` (AC-17 demo-clock clause) | `with journey.step("harness", "wall clock leaves the demo clock", needs=("login_sessions", "demo_service", "demo_clock"), operations=("login", "getDemoClock")):` login; `before = GET /api/demo/clock (getDemoClock).json()["now"]`; `journey_clock.advance(lifetime)`; login again with a new client; `after = …["now"]`; `after == before` | before/after |

### 7.2 `tests/journeys/j1/test_aea_57.py` (`pytestmark = pytest.mark.journey`)

Module constants (exact):
```python
J1 = "J-1"
LOGIN_NEEDS = ("login_sessions",)
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
SUBMIT_NEEDS = (*CHAT_NEEDS, "turn_service")
TURN_NEEDS = (*SUBMIT_NEEDS, "run_graph")
```
`CUSTOMER_TEXT`, `RESPONDER_TEXT`, `PLANNER_RAW`, `CLASSIFIER_RAW`, `SENTINEL` as §6. Small module helpers:
`start_session(journey, client) -> httpx.Response` (`POST /api/chat/sessions`, `startChatSession`, assert 201),
`submit(client, thread_id, turn_id, text) -> httpx.Response` (`POST /api/chat/sessions/{thread_id}/turns`, `submitTurn`,
body `{"turn_id": turn_id, "payload": {"kind": "text", "text": text}}`), `thread_counts(journey, thread_id) -> dict[str, int]`
(`messages`, `turns`, `spend_ledger` counts `WHERE thread_id = ?`, plus `conversations` count for that id),
`request_record(journey, response) -> dict` (`journey.logs.wait_for("request", lambda r: r["request_id"] ==
response.headers["X-Request-ID"])`).

Step names (exact strings; the record uses them): `"1 signed out"`, `"2 wrong login"`, `"3 login"`, `"4 start session"`,
`"5 one turn"`, `"6 refresh/resume read"`, `"6 resend"`, `"7 owner guard"`, `"8 validation"`,
`"secret values absent after login"`, `"secret values absent after step 8"`.

| Test | Steps (each inside `with journey.step(J1, <name>, needs=…, operations=…)`) and assertions |
|---|---|
| `test_j1_guards_and_login` (AC-8) | **1** (`needs=LOGIN_NEEDS`): new client; `GET /api/chat/sessions/{uuid4}` (`getChatThread`) → 401, `error.code == "UNAUTHENTICATED"`, `error.details == {"reason": "none"}`; `GET /staff/queue` (`operation_id=None`, page) → 303, `Location == "/login?return_to=%2Fstaff%2Fqueue&reason=none"`; `journey.db.count("staff_sessions") == 0`. **2** (`LOGIN_NEEDS`, ops `("login",)`): `POST /api/login` right username, wrong password → 401 `LOGIN_FAILED`; no `mhc_session=` Set-Cookie line; `staff_sessions` count 0. **3** (`LOGIN_NEEDS`, `("login",)`): `signed = journey.login()`; body `session.authenticated is True`, `session.role == "customer"`, `landing == "/"`; exactly one `mhc_session=` Set-Cookie line; `cookie_attributes(line)`: `path == "/"`, `"httponly" in`, `samesite == "Lax"`, `max-age == str(journey.container.limits.web.login_session_lifetime_s)`, `"secure" not in`; `staff_sessions` count 1; that row `session_id == signed.session_id`, `role == "customer"`, `token_hash != signed.cookie`, and `signed.cookie not in repr(row)`. Print status, Location, cookie attribute names/values (not the token), session_id and role |
| `test_j1_session_resume_and_owner_guard` (AC-9) | **3** login (as above, shorter). **4** (`CHAT_NEEDS`, `("login", "startChatSession")`): `start = start_session(...)`; 201; `greeting.type == "text"`, `greeting.text == render(TextId.GREETING)`; `controller == {"kind": "ai", "display_name": None}`; `settled.visit is None`, `settled.request is None`, `settled.actions == []`; `events.last_event_id == 0`, `events.url == f"/api/chat/sessions/{thread_id}/events"`. Stored: `conversations` row for `thread_id`: `demo_session == signed.session_id`, `run_tag == "live"`, `outcome == "open"`, `agent_version == journey.settings.agent_version`, `controller == "ai"`, `live_state == "not_live"`, `last_customer_wall_at is None`; `messages` for the thread: exactly 1, `role == "assistant"`, `text == render(TextId.GREETING)`; `datetime.fromisoformat(demo_state.demo_now) == datetime.fromisoformat(start["demo_clock"]["now"])` (row `id = 1`). **6 read** (`CHAT_NEEDS`, `("getChatThread",)`): counts before; `GET /api/chat/sessions/{thread_id}` → 200; `state == "open"`; `turns` has 1 entry, `turn_id == "greeting"`, `speaker.kind == "assistant"`, its first block's text is the greeting; counts after == before. **7** (`CHAT_NEEDS`, `("login", "getChatThread")`): `other = journey.login()` (new client); other's read of the same thread → 404 `SESSION_NOT_FOUND`; the first client's read → 200; counts unchanged |
| `test_j1_one_turn_and_resend` (AC-10, PA-3) | **3**, **4** as above. **5** (`TURN_NEEDS`, `("submitTurn",)`): add the three script entries (§6); `calls_before = len(journey.script.calls)`; `turn_id = uuid4`; `first = submit(...)` → 200; exactly one block with `type == "text"` and its `text == RESPONDER_TEXT`; `journey.script.problems() == ()`; `journey.script.remaining() == 0`; `{c.role for c in calls[calls_before:]} == {Role.PLANNER, Role.CLASSIFIER, Role.RESPONDER}`. Stored: one customer `messages` row with this `turn_id`, `text == CUSTOMER_TEXT`, `kind == "text"`; one `turns` row: `status == "completed"`, `gate_result == "clear"`, `plan_mode == "talk"`, `outcome == "answered"`, `json.loads(specialists_run) == []`, `server_ms` is an int ≥ 0, `replied_at` not null, `trace_export == "off"` (no Langfuse → `NullTraceSink`), `agent_version == settings.agent_version`, `request_id == first.headers["X-Request-ID"]`, `model_calls == 3`, `cost_usd == 0.0`; `spend_ledger` rows for the turn: 3, each `cost_usd == 0.0`, `status == "ok"`, `run_tag == "live"`, and `(provider, model)` equals the configured pair for its `role`; `conversations.last_customer_wall_at` not null. **6 read** (`TURN_NEEDS`, `("getChatThread",)`): counts before; thread → entries `[greeting, customer, assistant]`; entry 1 `speaker.kind == "customer"`, `text == CUSTOMER_TEXT`, `turn_id == turn_id`; entry 2 `speaker.kind == "assistant"`, `blocks == first.json()["blocks"]`; counts unchanged. **6 resend** (`TURN_NEEDS`, `("submitTurn",)`): `calls = len(script.calls)`; `same = submit(... same turn_id ...)` → 200; `same.content == first.content`; `len(script.calls) == calls`; `turns` rows for `turn_id` == 1; thread counts unchanged |
| `test_j1_rejected_and_secret_values_absent` (AC-11) | **3** login. **"secret values absent after login"** (`LOGIN_NEEDS`): for each `v` in `(*journey.secret_values(), signed.cookie)`: `journey.files_containing(v) == []` and `v not in journey.logs.all_text()`. **4** start. **8** (`SUBMIT_NEEDS`, `("submitTurn",)`): counts before; `bad = submit(..., SENTINEL + "a" * (2001 - len(SENTINEL)))` → 400, `error.code == "VALIDATION_ERROR"`, `SENTINEL not in bad.text`; counts after == before. **"secret values absent after step 8"** (`LOGIN_NEEDS`): for each `v` in `(SENTINEL, *journey.secret_values(), signed.cookie)`: not in any data-dir file, not in `logs.all_text()`, and not in `render_record(build_record_data(scope="AEA-57", collector=journey.collector, root=REPO_ROOT, command="j1"))`. Print hit counts (0 each) |
| `test_j1_records_per_step` (AC-12) | **1**: for both responses, `request_record` exists with `status == response.status_code` and `caller_role == "anonymous"`. **2**: `auth_event` with `request_id == response X-Request-ID`, `outcome == "rejected"`, `session_id is None`; its `request` record exists. **3**: `auth_event` `outcome == "ok"`, `session_id == signed.session_id`; `request` record exists. **4** (`CHAT_NEEDS`): `request` record for the start call with `caller_role == "customer"`; one `conversations` row and one greeting `messages` row for the new thread (presence only). Print the records per step (never a cookie) |
| `test_j1_offline_and_placeholders` (AC-13; no needs) | `journey.settings.anthropic_api_key.get_secret_value() == PLACEHOLDER_ANTHROPIC_KEY`, same for OpenRouter; `journey.settings.langfuse_complete() is False`; `journey.settings.eval_key is None`; `journey.settings.web_dist_dir` is an empty directory; `journey.guard.blocked == []` (the teardown re-checks it after the run) |

### 7.3 `tests/journeys/support/README.md` (exact headings; the AC-16 test parses two of them)

```
# Journey harness (AEA-57)
<one paragraph: what it runs — real app under uvicorn, disposable DB copy, scripted model, OpenAPI check per response>
## Public fixtures
- `journey` — a running real app on a disposable DB copy with the scripted model; returns `JourneyRun`
- `journey_clock` — the run's wall clock (`StepClock`); `.advance(seconds)` moves `get_wall_clock()` forward; the demo clock stays
## Options
- `--journey-record=SCOPE` — write `docs/testing/journeys/<date>-<SCOPE>.md` for this run
- `--journeys-strict` — a blocked step fails instead of being skipped (wave merge, pre-deploy)
## The `journey` object
<bullets: settings, app, container, base_url, script (JourneyScript.add/calls/remaining/problems), models, db (DbReader),
 logs (LogTap.structured/wait_for/all_text), guard, client(), login(), step(), secret_values(), files_containing(), demo_username>
## Writing a step
<a 10-line example with journey.step("J-n", "<name>", needs=(...), operations=(...)) and client.call(..., operation_id=...)>
## Blocked steps
<NEED_OWNERS / OPERATION_OWNERS; skipped "blocked-on AEA-NN"; strict = failed; a missing name is a follow-up on AEA-57>
## Rules for journey files
<one file per ticket per journey: tests/journeys/j<N>/test_aea_<NN>.py (N 1…10); mark `pytest.mark.journey`; never edit
 support/; no dependency_overrides, monkeypatch of meridian, TestClient or doubles above the model ports; every /api call
 names its operationId; assert what the client sees and what was stored>
## Commands
1. `uv run pytest tests/journeys/support -q -rs`
2. `uv run pytest -m journey tests/journeys/j1 -v --journey-record=AEA-57`
3. `uv run pytest -m journey tests/journeys --journeys-strict`
Ticket merge: `uv run python -m tests.journeys.affected --base <main SHA before the merge>`.
```

### 7.4 Context rows (AC-18; replace `<sha>` and `<run-date>`)

- `.claude/reference/area-map.md`, row starting `| 3+ | **Integration and journeys**`, last cell `planned` →
  `partly built: \`tests/journeys/support/\` (journey harness) and J-1 \`tests/journeys/j1/test_aea_57.py\` actual (AEA-57, \`<sha>\`); the rest planned`.
- `.claude/state/icm-progress.md`, row *Integrated-journey protection*: keep status `provisional`; evidence cell →
  `2026-10-21: harness \`tests/journeys/support/\` + J-1 (AEA-57, \`<sha>\`); record [\`<run-date>-AEA-57.md\`](../../docs/testing/journeys/<run-date>-AEA-57.md) lists blocked steps and owners`;
  last cell → `Every J-1 step integrated under \`--journeys-strict\` (AEA-51 carries it)`. Row ≤ 400 characters.
- `docs/design/code-design.md` §9: insert before the `└── live/` line:
  ```
  ├── journeys/         integrated journeys (rule integrated-journeys): support/ = AEA-57's harness (real app under uvicorn
  │                     on a disposable DB copy, scripted model at the provider boundary, client, DB reader, record writer);
  │                     j<N>/test_aea_<NN>.py, one file per ticket per journey; browser/ (AEA-58)
  ```
  and append to the *Built on `main`* sentence: `; \`tests/journeys/support/\` and \`tests/journeys/j1/test_aea_57.py\` (AEA-57, \`<sha>\`)`.
- `PROJECT-CHECKLIST.md` §8: `- [ ] Journey harness exists …` → `- [x] Journey harness exists …` and replace
  `` `docs/testing/journeys/YYYY-MM-DD-AEA-57.md` `` with `` [`docs/testing/journeys/<run-date>-AEA-57.md`](docs/testing/journeys/<run-date>-AEA-57.md) ``.

### 7.5 Commands — cheapest first, stop at the first red (run from the worktree root; `export UV_LINK_MODE=hardlink`)

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check tests/journeys/support tests/journeys/j1/test_aea_57.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check tests/journeys/support tests/journeys/j1/test_aea_57.py` | `… files already formatted` |
| 3 | Types | `uv run mypy` (the configured `src/meridian`, `tests`, `eval`) | `Success: no issues found` |
| 4 | Self-checks (command 1) | `uv run pytest tests/journeys/support -q -rs` | all pass except `test_wall_clock_control_expires_session` (skipped `blocked-on AEA-44: …` until AEA-44 is on the branch) and `test_wall_clock_control_leaves_demo_clock` (skipped `blocked-on AEA-44, AEA-30, AEA-43 …` until bound) |
| 5 | J-1 (command 2, while iterating without the record option) | `uv run pytest -m journey tests/journeys/j1 -v -rs` | `test_j1_offline_and_placeholders` passes; every other test passes **or** is skipped with a `blocked-on AEA-NN` reason naming only unmerged tickets (on `24a5e9a`: `AEA-44` first); never failed |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | selects every journey (a `tests/journeys/` change is an always-input) and pytest exits 0 |
| 7 | Full suite, once before commit 1 | `uv run pytest -q` (serial; if it exceeds ~10 min, `uv run --with pytest-xdist pytest -n 2 -q`) | 0 failed. Why the full suite: the root conftest loads this plugin into **every** pytest session, which is the "shared fixture (`conftest.py`)" case of `build-loop-test-scope.md` |
| 8 | Strict run (report only, not a gate for this ticket) | `uv run pytest -m journey tests/journeys --journeys-strict -rs` | J-1 blocked steps show as **failed** with the same `blocked-on` text; quote the summary in the report |
| 9 | Record (command 2, after commit 1, clean tree) | `uv run pytest -m journey tests/journeys/j1 -v --journey-record=AEA-57` | prints `journey record: …/docs/testing/journeys/<run-date>-AEA-57.md`; the file has the nine rows |
| 10 | Grep evidence (AC-3, AC-13) | `grep -rnE "tests\.journeys\|Scripted(Model\|Jev\|Anthropic)\|scripted_model" src/meridian/` and `grep -rn "heldout\|key_dir" tests/journeys/` | both print nothing |
| 11 | Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL in an owned row |
| 12 | Diff scope (AC-18) | `git diff --stat main...HEAD` | only §2's owned files |

The implementer's report quotes: commands 1–7 results, the pytest summary lines of 4, 5, 8, the record path and its
*Blocked by* row, and both grep outputs.

---

## 8. Risks and requests

- **R-1 (collision of expectations, not files).** The slice plan says AEA-57 "runs the login, guard and resume steps from
  wave 2". Reading the code and the sibling plans shows the resume steps need more: `startChatSession` builds `settled` with
  `ReplyComposer.settled_view`, and `REPLY_COMPOSER` is bound by **AEA-51** (AEA-40 plan R-6), plus `demo_clock` /
  `demo_service` (AEA-30) and `session_service` (AEA-40). So in wave 2 only J-1 steps 1–3 can reach *integrated* (after
  AEA-44 merges); steps 4–8 report `blocked-on AEA-51` (and others) until wave 3. The harness reports this honestly; no
  decision is needed, but the orchestrator should not expect a green strict run before AEA-51. ND-2's merge-order advice
  stands: merge AEA-57 after AEA-44 (and 40, 30) so its record shows the most reached steps.
- **R-2 (ticket evidence command).** AC-3's literal `grep -rn "tests\.journeys\|scripted" src/meridian/` already prints one
  line today: `src/meridian/policy/limits.py:91` (a comment, "one scripted case has ≤ ~10 turns", about eval cases). That
  file is AEA-01's and may not be edited. The plan narrows the grep to identifiers (`tests\.journeys`, `ScriptedModel`,
  `ScriptedJev`, `ScriptedAnthropic`, `scripted_model`) and keeps the stronger AST import scan in the test. Report this
  substitution on issue #57.
- **R-3 (classifier field name).** `danger_level` comes from the AEA-37 plan, not merged code. If AEA-37 merges another
  name, PA-3 makes step 5 fail with an `invalid_output` problem; that is a seam finding for AEA-37/51, reported, not patched
  by editing the expectation.
- **R-4 (`--journeys-strict` reach).** Strict mode turns only steps declared through `journey.step` into failures. The
  existing mock-level journey files (j7 `test_aea_42.py`, …) use `@pytest.mark.skip` for their blocked parts; those stay
  *skipped* under command 3. Their owners convert them when they move onto the harness (AEA-51/52).
- **R-5 (watchdog in the test process).** AEA-32's watchdog calls `os._exit` after 3 consecutive `/healthz` failures
  (45 s). Journeys run seconds and the heartbeat is in-process, so this should not fire; the plan forbids patching it. If a
  journey run ever dies without a pytest report, check `health_events` for `restart` and report it on #57.
- **R-6 (future start-up needs).** If a later hunk (e.g. AEA-33 retrieval) needs a built index or a network download at
  start-up, the launcher fails loudly ("journey server stopped during start-up") because `MERIDIAN_INDEX_DIR` is empty and
  the socket guard refuses downloads. The fix is a follow-up on AEA-57 (a prebuilt test index), merged first.
- **R-7 (later owners).** `NEED_OWNERS` lists today's container keys. A ticket whose step needs a new key adds it through a
  follow-up on AEA-57 (support is AEA-57's alone; slice plan §3).
- **No shared primitive is requested.** Everything J-1 needs from `web/app.py` (`ContainerOverrides`, `wall_clock`) is
  already on `main`; no contract change is needed.

---

## 9. Readiness

**READY.** Every import the slice needs is on `main` `24a5e9a` (AEA-02 `Settings`/ports, AEA-10 first boot and
`temp_sqlite`, AEA-11 fakes, AEA-23 `create_app`/`ContainerOverrides`/`openapi_check`, AEA-26 ledger). Sibling services
(AEA-30, 40, 44, 51, 43) are consumed only at run time and reported as *blocked* steps; none is imported. No signed contract
changes, no decision D-4…D-15 is reopened (D-13's wall-clock mechanism is used exactly as decided), and no product decision
is needed.

**Gates:** none (no human, paid, design or UX gate). **blockedOn:** none.

---

## Deviations

- **Login success needs `demo_clock` (AEA-30).** Reading `register_staff_session` (AEA-44, merged): `StaffSessionStore.start` reads the demo clock, so `POST /api/login` with the right pair answers 500 `not bound: demo_clock` until AEA-30 binds it. The plan listed only `login_sessions` for J-1 step 3. The J-1 file therefore uses `SIGN_IN_NEEDS = ("login_sessions", "demo_clock")` for step 3 and for the wall-clock self-check; steps 1 and 2 keep `LOGIN_NEEDS`. Today step 3 reports `blocked-on AEA-30`.
- **Step 1 declares no `operations`.** The gate answers 401 before routing, so `getChatThread` need not be routed for step 1 (declaring it made step 1 blocked on AEA-40 for no reason).
- **Step names:** step 3 is split into `3 login` (sign-in) and `3 login cookie and row` (cookie attributes and stored row), both in the record.
- **Convention self-check:** `j11` as a folder is one violation and `j3/test_bad.py` another (two in total, as the plan said); `j11/test_aea_99.py` is not reported separately.
- **Steps 4 to 8 were not exercised against real services** (AEA-40, 30, 51 not on `main`); they were written from the plan and type-checked only. Steps 1 to 3 and the wall-clock expiry check were exercised once with a throwaway `demo_clock` provider (not committed).
