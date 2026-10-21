# Plan — [AEA-19] tracing: Langfuse sink, null sink, project-key check

**Status:** planned — **READY** (blocked on the AEA-02 merge for imports only; see §9)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/19 · **Base revision:** `16ca639` (main at
planning; AEA-01, AEA-03, AEA-04 and AEA-25 merged; AEA-02 not yet)
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21. **Builders:** `test-writer-agent` (frozen tests first,
`risk::security`), then `fanout-implementer` (Sonnet). `security-privacy-agent` reads this diff at the wave-1 merge.

**Refresh log (second pass, 2026-10-21).** Re-checked against the code on `main` (`16ca639`, unchanged since the first
pass), the installed `langfuse 5.0.4` / `opentelemetry-sdk 1.45.1` / `httpx 0.28.1`, AEA-02's plan as it stood at 12:08 and
its frozen tests on branch `aea-02-aea-02-domain-ports` (`de9bb42`, tests only, no code yet), AEA-04's `privacy/redact.py`,
`tests/journeys/affected.py`, and the sibling plans AEA-10, 17, 20, 32. What changed:
1. **R-1 (AEA-01's stub test) now has one agreed fix** shared by the hunk tickets (AEA-17 plan §3.5, AEA-10 plan R-13): a
   two-line `continue` in `test_every_register_stub_present`, made by whichever hunk ticket lands first. This plan adopts it
   word for word (§2.1, step T-4b, §8 R-1) instead of the first pass's `ast` proposal, so §7's affected tests are all green.
2. AEA-02's types are confirmed field for field (§4.1). Its ID types are strict-pattern `str` subclasses, so the test
   doubles build `TurnIds` with `TurnIds.model_validate` from plain strings (§6.2 `turn_ids`, §6.3 PA-1).
3. Key names confirmed: AEA-32's plan provides `Key[AlertWriter]("alert_writer")` with `fire(alert_type, reason_code)`
   and lists this ticket as the binder; `Key[TraceSink]("trace")` is used by no other plan under another name.
4. `S-233` is still free in `docs/source/source-register.md` (last row `S-232`). Nothing else changed.

The planner prototyped the risky SDK mechanics in a throwaway copy against the installed `langfuse 5.0.4` /
`opentelemetry-sdk 1.45.1` (results quoted where they matter); nothing was written to the repo but this file.

---

## 1. Goal and sources

**Goal (issue *What to build*, verbatim in substance).** Every turn becomes one trace (the turn, each node and each model
attempt nested under it), sent to this app's own project in the Langfuse v4 on Innocent's VPS. Two things must never
happen: a private value reaching that trace, and tracing slowing or failing a customer's turn. So the sink masks in our
process before export, exports on a background thread through a bounded queue that drops (and counts) instead of
waiting, and at start-up asks Langfuse which project its keys belong to; on any other project export stays off for the
life of the process and an alert fires. With no Langfuse settings the app runs the **null sink** and every turn's
`trace_export` reads `off`.

**What it does in practice (example).** Turn `t-1` of thread `th-9`: `TurnService` (AEA-40) opens
`with trace.turn(ids) as span:`; the gateway (AEA-20) calls `trace.model_call(span, record, masked_in, masked_out)` twice;
nodes call `trace.node(span, "front", 12, "ok")`. On exit the sink has offered 4 spans to its 1,024-slot queue, none
dropped, the last batch was fine → `trace.export_status(span) == "sent"`, and `span.trace_id` is the 32-hex id that
AEA-40 writes to `turn.trace_id`. If the customer had typed "my name is Omar Patel, 512-555-0102", the span Langfuse
receives reads "my name is [name], [phone ending 02]".

**Sources (exact sections).**

| Source | Section | What it fixes here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-19.md` (= issue #19) | AC-1…AC-12, WP-2 pair, owned files, must-not-edit list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-19 (wave 1, **Sec**, blocked by 02, 04), §3 collision map (`web/container.py`: own hunk only) | Boundary |
| Addendum (wins over DO-4) | `docs/design/contracts/stage7/models.md` §4 (trace types, `LangfuseExportSettings`, sink, project check steps 1–5, export queue, status table), §7 (container wiring), cross-topic 2, 3, 5, 6, 7 | Every signature and rule below |
| Decisions | `docs/plans/7b-decisions/models.md` MOD-6, MOD-7, MOD-8, MOD-9; `merge-clashes.md` MC-21, MC-23, MC-24; `residuals-graph.md` R-G-6 | Check rule, alert type, queue, status meanings, no `langfuse_export()` |
| Redaction | `docs/design/contracts/stage7/data.md` §1 (`redact`, `Redactor`, `RedactionProfile.TRACE`); code on main `src/meridian/privacy/redact.py` | The TRACE profile masks card, email, phone (`[phone ending NN]`), address, code, introduced name; keeps `MHC-`/`INV-` ids |
| Settings | `stage7/graph-core.md` §12 (`Settings.langfuse_*`, `langfuse_complete()`); AEA-02 plan §4.14 | The four fields; the hunk reads them, never a `langfuse_export()` |
| Alerts | `stage7/cases.md` §8 (`AlertWriter.fire(alert_type, reason_code)`, `trace_export_failed` fires and clears) | What `on_alert` is bound to |
| DO-4 | `docs/design/contracts/internal-components.md` §13 (`TraceSink`, superseded note: `export_status(turn)`), §16 | Port shape |
| DO-3 | `docs/design/code-design.md` §4.2 (`TraceSink`: off, Langfuse, in-memory), §4.3 row `adapters/tracing_langfuse.py`, §9 test layout, S-10 | Module home, dependency direction (adapter → ports/domain/privacy) |
| DO-6 | `docs/design/observability-contract.md` *Content and redaction* (table + steps 2–3), *Missing instrumentation* rows "Traces are not exported" / "wrong Langfuse project", *Capture verification* (in-memory exporter), WF-1/WF-13/WF-17, CAP-1, CAP-9 | What a span may hold; how tests capture |
| DO-1 | system design §8.2 *Langfuse on the VPS*, §8.3 (drop rather than block), §10 *Redaction*, §11 decision 8 | Never block a turn |
| DO-7 | M-29 (trace export completeness, Stage 7 note on `sent`) | Status semantics |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §4, `context-maintenance.md` rules 5–6 | Frozen tests first; affected tests; journey record; S-233 before citing |

---

## 2. Boundary

### 2.1 Owned files (the only files the test-writer and implementer may create or edit)

| File | State on main | Who | Change |
|---|---|---|---|
| `src/meridian/adapters/tracing_langfuse.py` | absent | implementer | **create** (§5 Phase I) |
| `src/meridian/web/container.py` | AEA-01 stub | implementer | **only the body of `register_tracing`** (keep its signature and first docstring line) |
| `tests/unit/web/test_container.py` | AEA-01 (merged) | test-writer | **conditional, two inserted lines only** (step T-4b; AEA-17 plan §3.5): make the edit only if it is not already on `main` |
| `tests/unit/adapters/_tracing_doubles.py` | absent | test-writer (**frozen**) | **create**: shared doubles/builders for the three test files |
| `tests/contract/test_trace_sink_contract.py` | absent | test-writer (**frozen**) | **create** |
| `tests/unit/adapters/test_tracing_langfuse.py` | absent | test-writer (**frozen**) | **create** |
| `tests/unit/web/test_register_tracing.py` | absent | test-writer (**frozen**) | **create** |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-19.md` | absent | implementer | **create** (AC-11; date = the day you run it, America/Chicago) |
| `.claude/reference/area-map.md` | exists | implementer | row **A10a** status cell only (AC-12) |
| `.claude/state/icm-progress.md` | exists | implementer | row *Routes verified against code and tests*: evidence cell only (AC-12) |
| `docs/design/code-design.md` | exists | implementer | §3 tree line for `tracing_langfuse.py` only (AC-12) |
| `docs/source/source-register.md` | exists | implementer | append row **S-233** (AC-12) |
| `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<YYYY-MM-DD>-aea-19-tracing-claude-01.md` | absent | implementer | **create** (AC-12; outside this repo, never `git add`ed here) |

Existing package markers already on main: `tests/unit/adapters/__init__.py`, `tests/unit/web/__init__.py`,
`tests/contract/__init__.py`, `src/meridian/adapters/__init__.py`. Do not create or edit them.

### 2.2 Shared surfaces: read only

`src/meridian/privacy/redact.py` (AEA-04), `src/meridian/web/container.py` outside `register_tracing` (AEA-01),
`src/meridian/policy/limits.py` (AEA-01), `pyproject.toml` / `uv.lock` (AEA-01), `tests/conftest.py` (AEA-01),
`tests/unit/web/test_container.py` (AEA-01; only T-4b's two lines may change), `tests/unit/test_import_direction.py` (shared), `tests/journeys/**`
(AEA-01, 57, 58), `src/meridian/{domain,ports}/*`, `src/meridian/config.py` (AEA-02), `tests/fakes/*` (AEA-11),
`tests/capture/*` (AEA-50, 51), `services/health.py`, `repos_ops.py` (AEA-32).

### 2.3 Never touch

Briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
`docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `.env` (never read it either), any other
ticket's `register_*` hunk, any stage7 addendum or DO-n file other than the one line in §2.1.

---

## 3. Requirements table

`risk::security`: every row marked **F** is a frozen test the test-writer writes first (§5 Phase T). "PA-n" rows are
plan-added (template *Source-contract reconciliation*: the issue omitted them; the merge step posts them on issue #19).

| ID | Requirement (verbatim or cited) | How it is implemented | Verified by |
|---|---|---|---|
| AC-1 [negative] | Seeded values never reach an exported span, even when a caller passes them unmasked: full phone `512-555-0102`, "Omar Patel" (introduced as "my name is Omar Patel"), a six-digit code, a synthetic card-like number and a fake key value are absent; `[phone ending 02]` and the invoice facts remain | In-process `_mask_text` on every caller text (TRACE `redact` + key strip) **and** the `mask_otel_spans` hook on every exported span (I-6, I-8) | **F** `tests/contract/test_trace_sink_contract.py::test_mask_hook_strips_seeded_values` |
| AC-2 [invariant] | The mask runs on every exported span: turn, node, model-call spans and a span created directly through the Langfuse client | Hook is installed on the client (`mask_otel_spans=`), so it sees every span the client exports (I-8) | **F** `…contract…::test_mask_applies_to_all_span_kinds` |
| AC-3 [failure/refusal] | Export never blocks or fails a turn: with an exporter that hangs or errors, and with the queue full, `turn`/`model_call`/`node` each return within 50 ms [A]; past `queue_max_spans` (1,024) the excess is dropped and `dropped_spans()` equals the spans refused; no exception reaches the caller | Admission counter in `should_export_span` (I-7), background BSP worker, recording exporter catches errors (I-4), every public call wrapped (I-9, I-10) | **F** `tests/unit/adapters/test_tracing_langfuse.py::test_export_never_blocks` |
| AC-4 [failure/refusal] | Keys that are not this app's project (another `id`; several projects incl. ours; 401): export off, every `export_status` `off`, `on_alert("wrong_project")` exactly once, **no span sent**, no re-check | `_check_project` → `wrong_project` → state `off_wrong_project` (I-5) | **F** `…test_tracing_langfuse.py::test_wrong_project_keys_turn_export_off` |
| AC-5 [failure/refusal] | Unreachable (connection error, timeout, 503): `start()` returns without raising, export off, `on_alert("project_check_failed")` once, after `recheck_after_s` on a fake clock the check runs again; when it passes, export turns on; spans exported only after | state `off_check_failed`, recheck thread calling `_recheck_if_due()` (I-5) | **F** `…::test_unreachable_at_start_rechecks` |
| AC-6 [invariant] | This app's keys (exactly one project, `id` == `LANGFUSE_PROJECT_ID`; name irrelevant): export on; one trace per turn, session id = `thread_id`; `SpanHandle.trace_id` = that 32-hex id | Root span under `propagate_attributes(session_id=thread_id, trace_name="turn")`; children via `root.start_observation` (I-9) | **F** `…::test_one_trace_per_turn_with_session_id` |
| AC-7 [capture] | `export_status(span)` yields exactly one of `off`/`sent`/`failed` per handle with MOD-9 meanings; two concurrent turns get their own status | Per-turn `_TurnState` counters; `_status_for` (I-10) | **F** `…::test_export_status_values` |
| AC-8 [invariant] | `NullTraceSink` honours the same Protocol, sends nothing, yields `trace_id=None`, reports `off`; both sinks pass one conformance test | `NullTraceSink` (I-11) | **F** `tests/contract/test_trace_sink_contract.py::test_sinks_conform` |
| AC-9 [invariant] | Container hunk builds `LangfuseTraceSink` only when all four `LANGFUSE_*` set, else `NullTraceSink`, without calling `on_alert`; export settings built from `Settings`' four fields, never `Settings.langfuse_export()` | `register_tracing` body (I-12) | **F** `tests/unit/web/test_register_tracing.py::test_sink_choice_by_settings` |
| AC-10 [negative] | No key value reaches logs, alerts or spans; `on_alert` args are only the reason code; the project-check response body is not logged | Fixed log strings (class names / status ints only), key strip in `_mask_text`, `langfuse` logger pinned to WARNING (I-3, I-5, I-6) | **F** `tests/unit/adapters/test_tracing_langfuse.py::test_keys_never_logged` (see note ¹) |
| AC-11 [journey] | No deterministic journey reaches this code (journeys run with `NullTraceSink`): the affected-journey command selects none and exits 0; the record says so and names where it is proved instead | Record file (C-1) | `uv run python -m tests.journeys.affected --base main` → `0 journeys affected`; `docs/testing/journeys/<date>-AEA-19.md` Level `mock-tested` |
| AC-12 [regression/context] | Same change: area-map A10a row; ICM evidence; DO-3 status for this file; S-233 registered; dev-log entry | C-2…C-6 | `git diff --stat` on those paths |
| PA-1 (DO-6 table, row "IDs, statuses, timings, token counts, cost: Yes"; DO-6 line 113 `model_call` span fields) | IDs (even a UUID holding a six-digit run), model, usage, cost, role, attempt, latency, HTTP status, provider request id pass unchanged; the generation carries the masked full context | Pass-through key set and UUID-shape check in the hook (I-8); `_call_metadata` (I-9) | **F** `tests/contract/test_trace_sink_contract.py::test_ids_and_numbers_pass_unchanged` |
| PA-2 (fail closed; DO-6 "Never") | If masking raises, the text becomes `[removed]`; nothing raw leaves | `_safe_mask`, `_removed_updates` (I-6, I-8) | **F** `…test_tracing_langfuse.py::test_mask_fails_closed` |
| PA-3 (SDK media path runs *before* the hook) | A `data:…;base64,` header never reaches the Langfuse client, so the SDK's media upload (which bypasses `mask_otel_spans`) cannot fire on customer text | `_DATA_URI_PATTERN` in `_mask_text`, applied in-process (I-6) | **F** `…::test_data_uri_never_reaches_client` |
| PA-4 (BSP's own queue must never drop silently) | `queue_max_spans` must be 1…2048 (OTel's `BatchSpanProcessor` default deque is 2048 and drops the *oldest* silently); positive intervals | Constructor validation (I-3) | **F** `…::test_settings_bounds_rejected` |
| PA-5 (DO-3 §2.1 dependency direction) | The adapter imports only stdlib, `httpx`, `langfuse` (public modules), `opentelemetry`, `pydantic`, and `meridian.{domain,ports,privacy.redact}` | Import list (I-2) | **F** `…::test_adapter_import_direction` |
| PA-6 (async-safety rule 2) | Every thread and client the sink opens is closed by `close()`; `close()` is idempotent | `close()` (I-13) | **F** `…::test_close_is_idempotent_and_stops_recheck` |
| PA-7 (MOD-7 binding, models.md §7, cases.md §8) | The hunk's `on_alert` calls the container's `alert_writer.fire("trace_export_failed", reason)`; with no writer bound it logs a fixed line and never raises | `register_tracing` (I-12) | **F** `tests/unit/web/test_register_tracing.py::test_on_alert_reaches_alert_writer` |
| PA-8 (never fail start-up) | If the Langfuse sink cannot be constructed, the hunk provides `NullTraceSink` and logs a fixed line | `register_tracing` (I-12) | **F** `…test_register_tracing.py::test_build_failure_falls_back_to_null` |

¹ AC-10 in the ticket reads `::test_keys_never_logged` right after AC-9's file. The behaviour under test is the sink's
(start-up check, alerts, spans), so it lives in the sink's unit file; AC-9's file covers the hunk's alert binding (PA-7).
The reviewer should read the path as `tests/unit/adapters/test_tracing_langfuse.py::test_keys_never_logged`.

**Other obligations reconciled (no new test):** collector-side masking not used (DO-6 step 2, n/a by design); never
YourAI's keys or project (enforced by AC-4's id check); no database write (the sink has no UoW; `turn` row is AEA-40's,
other-ticket); CAP-1 at the real entry point (AEA-51, other-ticket); CAP-9 at start-up of the image (AEA-50,
other-ticket); `InMemoryTraceSink` (AEA-11, other-ticket); evaluator firing on `off` (AEA-32, other-ticket); M-29 on
CON-19 (AEA-53, other-ticket); the deployed route and `LANGFUSE_PROJECT_ID` value (AEA-09/56, `lane::human`).

**Entry-point registration:** None. This ticket adds no entry point; it feeds WF-1 (spans, `trace_export`), WF-13
(start-up export on/off) and WF-17 (alert), all already in DO-6.

---

## 4. Shared code to use (copied from current code and the addenda)

### 4.1 From AEA-02 (not on main yet; signatures from `stage7/models.md` §1/§4 and the AEA-02 plan §4.1, §4.8, §4.14)

```python
# meridian.ports.runtime (re-exports from meridian.domain.turn)
ExportStatus = Literal["off", "sent", "failed"]

@dataclass(frozen=True)
class SpanHandle:
    turn_id: TurnId
    trace_id: str | None                                  # 32-hex; None from NullTraceSink
    native: object = field(default=None, compare=False, repr=False)

class TurnIds(MeridianModel):                             # frozen pydantic model, extra="forbid"
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId   # str subclasses, canonical lower-case UUID4
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; agent_version: str

class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> AbstractContextManager[SpanHandle]: ...
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...

# meridian.ports.models (re-exports from meridian.domain.common)
class ProviderCall(MeridianModel):
    provider: Literal["anthropic", "openrouter_jev"]; model: str; latency_ms: int
    input_tokens: int; output_tokens: int; cache_read_tokens: int; cache_write_tokens: int; thinking_tokens: int
    cost_usd: float; cost_source: Literal["reported", "price_table"]; status: Literal["ok", "error"]
    failure: ProviderFailure | None; provider_request_id: str | None; stop_reason: str | None
class CallRecord(ProviderCall):
    role: Role; attempt: int                              # 1..2
class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind; provider: ProviderName; http_status: int | None
    retry_after_s: float | None; retryable: bool; provider_request_id: str | None
class Role(StrEnum): PLANNER="planner"; CLASSIFIER="classifier"; PLANNER_FALLBACK="planner_fallback"
                     SPECIALIST="specialist"; RESPONDER="responder"; BRIEF="brief"

# meridian.config
class Settings(MeridianModel):
    langfuse_public_key: SecretStr | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_base_url: str | None = None
    langfuse_project_id: str | None = None
    # required: anthropic_api_key, openrouter_api_key, demo_username, demo_password, session_secret (SecretStr)
    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Settings: ...   # reads ENV_NAMES only; blank = unset
    def langfuse_complete(self) -> bool: ...              # all four set and non-blank
# ENV_NAMES: ANTHROPIC_API_KEY, OPENROUTER_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL,
#   LANGFUSE_PROJECT_ID, MERIDIAN_DEMO_USERNAME, MERIDIAN_DEMO_PASSWORD, MERIDIAN_SESSION_SECRET, ...
```

**Confirmed (second pass)** against AEA-02's plan §4.1, §4.8, §4.13, §4.14 and its frozen `tests/unit/test_config.py`:
`Role`, `ProviderName = Literal["anthropic", "openrouter_jev"]`, `ProviderCall`, `CallRecord` (with `attempt: int =
Field(ge=1, le=2)` and `from_provider`) are defined in `domain/common.py` and re-exported by `ports/models.py`;
`ExportStatus`, `SpanHandle`, `TurnIds` are defined in `domain/turn.py` and re-exported by `ports/runtime.py`;
`ThreadId`/`TurnId`/`RequestId` are strict-pattern `str` subclasses (canonical lower-case UUID4); `Settings` also has
`eval_key`, `cookie_secure`, `trust_proxy_headers`, `web_dist_dir`, `require_frontend`, `data_dir`, `index_dir`,
`issued_db_path`, `agent_version` (all defaulted); `from_env` treats a blank value as unset; `config.py` may import
`meridian.privacy.redact` but never an adapter. **After AEA-02 merges, the merged code wins** (names, import home):
confirm with `grep -n "class CallRecord\|class TurnIds\|class SpanHandle\|ExportStatus =\|def langfuse_complete"
src/meridian/domain/*.py src/meridian/ports/*.py src/meridian/config.py` before writing code. Stop and report
(`blocked-on AEA-02 follow-up`) only if a type this plan needs is missing or has different fields.

### 4.2 From AEA-04 (on main, `src/meridian/privacy/redact.py`)

```python
class RedactionProfile(StrEnum): STORE="store"; SONNET="sonnet"; JEV="jev"; TRACE="trace"; LOG="log"
@dataclass(frozen=True)
class Redacted:
    text: str; replaced: Mapping[RedactionKind, int]; length: int
Redactor: TypeAlias = Callable[[str, RedactionProfile], Redacted]
def redact(text: str, profile: RedactionProfile) -> Redacted: ...
# TRACE replaces: card → "[card number removed]", email → "[email]", phone → "[phone ending NN]",
#   street line → "[address]", six-digit code → "[code]", introduced name → "<intro>[name]". Keeps MHC-/INV- ids.
# Idempotent: no placeholder matches a pattern again.
```

### 4.3 From AEA-01 (on main, `src/meridian/web/container.py`)

```python
class ContainerError(RuntimeError): ...
@dataclass(frozen=True)
class Key[T]:
    name: str                                             # equality by name
class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...   # raises after build
    def get[T](self, key: Key[T]) -> T: ...               # ContainerError("not provided: x") / ("get after close: x")
    def on_start(self, starter: Callable[[], None]) -> None: ...   # run after every object is built
    def on_close(self, closer: Callable[[], None]) -> None: ...    # run newest first
    def build(self) -> None: ...
    def close(self) -> None: ...

def register_tracing(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-19 tracing: Langfuse or null trace sink and the project-key check (models.md §4, §7).

    No-op until AEA-19 fills it.
    """
```
Module-level imports of `container.py` never change (AEA-01 test `test_container_imports_only_policy_limits`); the
hunk imports inside its body. `Any`, `cast`, `Key`, `Container`, `ContainerError` are already in scope.

### 4.4 Third-party APIs (installed: `langfuse 5.0.4`, `opentelemetry-sdk 1.45.1`, `httpx 0.28.1`; all `py.typed`)

```python
from langfuse import Langfuse, LangfuseSpan, propagate_attributes, __version__   # all in langfuse.__all__
from langfuse.types import (AttributeValue, MaskOtelSpansParams, MaskOtelSpansResult, OtelSpanIdentifier,
                            OtelSpanPatch)
Langfuse(*, public_key, secret_key, base_url, timeout: int | None, debug: bool, tracing_enabled: bool,
         flush_at: int | None, flush_interval: float | None, mask_otel_spans: MaskOtelSpansFunction | None,
         should_export_span: Callable[[ReadableSpan], bool] | None, tracer_provider: TracerProvider | None,
         span_exporter: SpanExporter | None, ...)
# client.start_observation(*, name, as_type="span"|"generation", input=, output=, metadata=, level=, status_message=,
#     model=, usage_details: dict[str, int], cost_details: dict[str, float]) -> LangfuseSpan / LangfuseGeneration
# obs.start_observation(...same keywords...) creates a CHILD of obs (explicit parent; works from any thread)
# obs.trace_id: str (32 lowercase hex); obs.end()
# client.flush(); client.shutdown()
# propagate_attributes(*, session_id: str | None, trace_name: str | None, ...) -> context manager; spans created
#   inside it get attribute "session.id" (and "langfuse.trace.name"). Must wrap child creation too (other threads).

from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import format_trace_id
from opentelemetry.exporter.otlp.proto.http import Compression
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# OTLPSpanExporter(endpoint: str, headers: Mapping[str, str], timeout: float, compression: Compression)

import httpx   # httpx.Client(base_url=, auth=httpx.BasicAuth(user, pw), timeout=, transport=, follow_redirects=False)
               # tests: httpx.MockTransport(handler)
```

**SDK facts the design rests on (prototyped by the planner):**
1. Passing `span_exporter=X` and `mask_otel_spans=hook` makes the client's `LangfuseSpanProcessor` (an OTel
   `BatchSpanProcessor`) export through `LangfuseTransformingSpanExporter(X, hook)`: the hook sees **every** span the
   client exports, once per batch, then `X.export(masked_spans)` is called. If the hook raises, the SDK drops the whole
   batch (fail closed) and returns SUCCESS without calling `X`.
2. `should_export_span(span)` is called **twice** per span: at start (`span.end_time is None`, only for app-root
   marking) and at end (`end_time` set; returning `False` keeps the span out of the BSP queue). Prototype: start flags
   `[True, True, False, True]` for turn/child start/child end/next start.
3. The BSP's own queue is a `deque(maxlen=2048)` that silently drops the **oldest** span and is not configurable
   through Langfuse, so this module bounds and counts admission itself (MOD-8 "wraps its own processor"). The BSP
   worker wakes at `flush_at` spans or every `flush_interval` seconds.
4. Prototype, cap 4, `flush_at=512`, `flush_interval=3600`: 7 spans offered → 3 dropped, 4 exported after `flush()`,
   pending back to 0 (deterministic). Cap 1,024 with a hanging exporter, 1,601 spans: worst call 5.2 ms; exported 1,536
   + dropped 65 = 1,601 (conservation holds; the exact split depends on when the worker pops its first batch).
5. `LangfuseResourceManager` is a per-process singleton **keyed by public key**: a second `Langfuse(...)` with the same
   public key reuses the first one's tracer provider and hook. Tests must use a fresh public key per sink.

---

## 5. Steps

DO-3 dependency direction: `adapters/tracing_langfuse.py` implements the `TraceSink` port (`ports/runtime.py`) and
depends on `ports`, `domain` and `privacy/redact.py` only; the composition root (`web/container.py`) is the only place
that names it. No new seam: the alert writer is reached through the container by name (§8 R-2).

### Phase T — test-writer (frozen failing tests, `risk::security`)

Run only after **AEA-02 is merged to main** and your worktree is cut from that main. `export UV_LINK_MODE=hardlink`
then `uv sync` in the worktree. Never copy a venv.

T-1. Create `tests/unit/adapters/_tracing_doubles.py` exactly as §6.2. It must import at module top only stdlib,
     `httpx`, `pydantic`, `opentelemetry.*`, `meridian.ports.*`, `meridian.domain.*`, `meridian.privacy.redact`; the
     module under test is imported **inside** functions with `importlib.import_module("meridian.adapters.tracing_langfuse")`
     so every file collects before it exists.
T-2. Create `tests/contract/test_trace_sink_contract.py` with AC-1, AC-2, AC-8, PA-1 (§6.3).
T-3. Create `tests/unit/adapters/test_tracing_langfuse.py` with AC-3…AC-7, AC-10, PA-2…PA-6 (§6.4).
T-4. Create `tests/unit/web/test_register_tracing.py` with AC-9, PA-7, PA-8 (§6.5).
T-4b. **AEA-01's stub test (conditional; AEA-17 plan §3.5, word for word).** Run
     `grep -n 'No-op until" not in' tests/unit/web/test_container.py`. If it prints a line, another hunk ticket already
     made the edit: change nothing. Otherwise, in `test_every_register_stub_present`, insert as the **first two lines of
     the loop body** `for name, func in originals.items():` exactly:
```python
        if "No-op until" not in (func.__doc__ or ""):
            continue  # filled by its ticket, whose own test covers the hunk
```
     Nothing else in that file changes (the stub-presence, docstring-ticket and call-order assertions stay). *Invariant:
     an unfilled stub is still proved a no-op; a filled hunk is proved by its own ticket's test.*
T-5. Every test function annotated `-> None`; ruff-clean and formatted with the project config
     (`uv run ruff check …`, `uv run ruff format …` on the four files).
T-6. Red for the right reason: `uv run pytest -q tests/contract/test_trace_sink_contract.py
     tests/unit/adapters/test_tracing_langfuse.py tests/unit/web/test_register_tracing.py` → the adapter tests fail with
     `ModuleNotFoundError: No module named 'meridian.adapters.tracing_langfuse'`; the register tests fail on their
     assertions (the stub provides nothing → `ContainerError: not provided: trace`). `uv run pytest -q
     tests/unit/web/test_container.py` stays green (the stub still says "No-op until", so T-4b's lines change nothing
     yet). Then `uv run pytest --collect-only -q` exits 0.
T-7. Commit only the four files, plus `tests/unit/web/test_container.py` if T-4b edited it (`git add <those paths>`),
     message `test(tracing): frozen failing tests for AEA-19`,
     last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Record the frozen-test manifest as the
     workflow requires.

### Phase I — implementer

I-0. **Before you start.** Read this plan, `stage7/models.md` §4 and §7, and the four frozen test files. Never edit a
     frozen file (tamper check). If a frozen test contradicts this plan or the addendum, stop and report the exact
     assertion. `export UV_LINK_MODE=hardlink`; `uv sync` in your worktree.

I-1. **Create `src/meridian/adapters/tracing_langfuse.py`** with a module docstring: "Trace sinks (AEA-19,
     stage7/models.md §4). `LangfuseTraceSink` masks every span in our process and again in Langfuse's `mask_otel_spans`
     hook, exports on a background thread through a bounded queue that drops and counts instead of waiting, and turns
     export on only after Langfuse confirms the keys belong to this app's project. `NullTraceSink` exports nothing."
     Target ≤ 450 lines (adapter target 400, cap 600).

I-2. **Imports (exactly these):** `from __future__ import annotations`; stdlib `base64`, `logging`, `math`, `re`,
     `threading`, `time`, `collections.abc.{Callable, Iterator, Mapping, Sequence}`, `contextlib.contextmanager`,
     `dataclasses.{dataclass, field}`, `typing.Literal`; third party per §4.4 (`httpx`, `langfuse`, `langfuse.types`,
     `opentelemetry.*`, `pydantic.SecretStr`); ours: `from meridian.ports.models import CallRecord`,
     `from meridian.ports.runtime import ExportStatus, SpanHandle, TurnIds`,
     `from meridian.privacy.redact import RedactionProfile, Redactor`. **Never** import `langfuse._client.*`,
     `meridian.config`, `meridian.services`, `meridian.web`, `meridian.agent`, another adapter, or call
     `opentelemetry.trace.set_tracer_provider` / `langfuse.get_client`.
     `__all__ = ["LangfuseExportSettings", "LangfuseTraceSink", "NullTraceSink", "TraceAlert", "TraceAlertReason"]`.
     `_log = logging.getLogger(__name__)`.

I-3. **Public types and constructor (exact):**
```python
TraceAlertReason = Literal["wrong_project", "project_check_failed"]
TraceAlert = Callable[[TraceAlertReason], None]          # the reason code only; never a key, URL or body (MOD-7)

@dataclass(frozen=True)
class LangfuseExportSettings:                             # built by the container from Settings' four langfuse_* fields
    public_key: SecretStr
    secret_key: SecretStr
    base_url: str
    project_id: str
    queue_max_spans: int = 1024                           # [A] MOD-8
    batch_interval_s: float = 5.0                         # [A]
    export_timeout_s: float = 5.0                         # [A]; the exporter's own, never a turn's
    check_timeout_s: float = 5.0                          # [A]; the start-up project check
    recheck_after_s: float = 600.0                        # [A]; only after project_check_failed

class LangfuseTraceSink:                                  # implements TraceSink
    def __init__(self, settings: LangfuseExportSettings, redact: Redactor, on_alert: TraceAlert, *,
                 span_exporter: SpanExporter | None = None,      # tests: in-memory; None → OTLP to Langfuse
                 transport: httpx.BaseTransport | None = None,   # tests: httpx.MockTransport for the project check
                 clock: Callable[[], float] = time.monotonic,    # tests: a fake clock (recheck, hung detection)
                 recheck_poll_s: float | None = None) -> None: ...  # None → min(recheck_after_s, 30.0)
    def start(self) -> None: ...                          # runs the project check; never raises
    @contextmanager
    def turn(self, ids: TurnIds) -> Iterator[SpanHandle]: ...
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...
    def dropped_spans(self) -> int: ...                   # trace_export_dropped (DO-1 §8.2), since start
    def flush(self) -> None: ...                          # export what is queued now; never raises
    def close(self) -> None: ...                          # idempotent; container on_close
```
     The four keyword-only parameters, `flush()` and `close()` are additions to the addendum sketch (constructor
     positional signature unchanged); §8 R-4.

     Module constants:
```python
_EXPORT_BATCH_SPANS = 512                 # BSP max_export_batch_size (flush_at); independent of queue_max_spans
_BSP_QUEUE_CEILING = 2048                 # OTel BatchSpanProcessor default deque; our cap must stay at or below it
_PROJECTS_PATH = "/api/public/projects"
_OTLP_TRACES_PATH = "/api/public/otel/v1/traces"
_KEY_REMOVED = "[key removed]"
_REMOVED = "[removed]"
_DATA_URI_REMOVED = "[data uri removed]"
_KEY_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:sk|pk)-[A-Za-z0-9][A-Za-z0-9_-]{7,}")
_DATA_URI_PATTERN = re.compile(r"data:[A-Za-z0-9.+/-]*;base64,", re.IGNORECASE)
_UUID4 = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
_META = "langfuse.observation.metadata."
_ID_KEYS = frozenset({"session.id", _META + "turn_id", _META + "thread_id", _META + "request_id"})
_PASS_THROUGH_KEYS = frozenset({
    "langfuse.trace.name", "langfuse.environment", "langfuse.release", "langfuse.version",
    "langfuse.observation.type", "langfuse.observation.level", "langfuse.observation.model.name",
    "langfuse.observation.usage_details", "langfuse.observation.cost_details",
    "langfuse.internal.as_root", "langfuse.internal.is_app_root",
    *(_META + k for k in ("run_tag", "agent_version", "role", "provider", "attempt", "latency_ms", "call_status",
                          "failure_kind", "http_status", "cost_source", "stop_reason", "provider_request_id",
                          "thinking_tokens", "elapsed_ms")),
})
_ExportState = Literal["pending", "on", "off_wrong_project", "off_check_failed"]
```
     `__init__` steps (invariant in italics):
     1. Validate: `if not 1 <= settings.queue_max_spans <= _BSP_QUEUE_CEILING: raise ValueError("queue_max_spans:
        out_of_range (1..2048)")`; for each of `batch_interval_s`, `export_timeout_s`, `check_timeout_s`,
        `recheck_after_s`: `if not value > 0: raise ValueError(f"{name}: must_be_positive")`. *The BSP deque can never
        reach its own silent-drop limit.* Messages never contain a value.
     2. Store `settings`, `redact`, `on_alert`, `clock`; `self._pk = settings.public_key.get_secret_value()`,
        `self._sk = settings.secret_key.get_secret_value()`, `self._base = settings.base_url.rstrip("/")`,
        `self._recheck_poll_s = recheck_poll_s if recheck_poll_s is not None else min(settings.recheck_after_s, 30.0)`.
     3. State: `self._lock = threading.Lock()`; `self._state: _ExportState = "pending"`;
        `self._alerted: set[TraceAlertReason] = set()`; `self._pending = 0`; `self._dropped = 0`;
        `self._last_batch_failed = False`; `self._batch_started_at: float | None = None`;
        `self._last_check_at: float | None = None`; `self._turns: dict[str, _TurnState] = {}`; `self._started = False`;
        `self._closed = False`; `self._stop = threading.Event()`; `self._recheck_thread: threading.Thread | None = None`.
     4. `self._http = httpx.Client(base_url=self._base, auth=httpx.BasicAuth(self._pk, self._sk),
        timeout=settings.check_timeout_s, transport=transport, follow_redirects=False)`.
     5. `inner = span_exporter if span_exporter is not None else self._build_otlp_exporter()`;
        `self._recorder = _RecordingExporter(inner, self._batch_started, self._batch_finished)`.
     6. `self._provider = TracerProvider(sampler=ALWAYS_ON)` — *a private provider; the global one is never set.*
     7. `self._client = Langfuse(public_key=self._pk, secret_key=self._sk, base_url=self._base,
        timeout=max(1, math.ceil(settings.export_timeout_s)), debug=False, tracing_enabled=True,
        flush_at=_EXPORT_BATCH_SPANS, flush_interval=settings.batch_interval_s, mask_otel_spans=self._mask_hook,
        should_export_span=self._admit, tracer_provider=self._provider, span_exporter=self._recorder)`.
     8. `logging.getLogger("langfuse").setLevel(logging.WARNING)` — *`LANGFUSE_DEBUG=true` would otherwise log
        unmasked span bodies and the public key at DEBUG.*

     `_build_otlp_exporter()`: `token = base64.b64encode(f"{self._pk}:{self._sk}".encode()).decode("ascii")`; headers
     `{"Authorization": f"Basic {token}", "x-langfuse-sdk-name": "python", "x-langfuse-sdk-version": __version__,
     "x-langfuse-public-key": self._pk, "x-langfuse-ingestion-version": "4"}` (the SDK's own default set);
     `return OTLPSpanExporter(endpoint=self._base + _OTLP_TRACES_PATH, headers=headers,
     timeout=self._settings.export_timeout_s, compression=Compression.Gzip)`.

I-4. **`_RecordingExporter(SpanExporter)`** (private class) — *records whether the most recent batch failed or hangs.*
```python
class _RecordingExporter(SpanExporter):
    def __init__(self, inner: SpanExporter, started: Callable[[], None], finished: Callable[[bool], None]) -> None: ...
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        # 1 started()  2 ok = inner.export(spans) == SpanExportResult.SUCCESS, any Exception → ok = False and
        #   _log.warning("trace_export_batch_error error=%s", type(exc).__name__)  3 finally finished(ok)
        # 4 return SUCCESS if ok else FAILURE
    def shutdown(self) -> None: self._inner.shutdown()
    def force_flush(self, timeout_millis: int = 30000) -> bool: return self._inner.force_flush(timeout_millis)
```
     Sink side: `_batch_started()`: under lock `self._batch_started_at = self._clock()`. `_batch_finished(ok)`: under
     lock `self._batch_started_at = None; self._last_batch_failed = not ok`.
     `_export_hung(now)`: `self._batch_started_at is not None and now - self._batch_started_at >
     self._settings.export_timeout_s`.

I-5. **Start-up check (MOD-6), numbered:**
     `_check_project() -> Literal["pass", "wrong_project", "project_check_failed"]` (never raises):
     1. `try: response = self._http.get(_PROJECTS_PATH)` `except Exception as exc:` log
        `_log.info("trace_project_check unreachable error=%s", type(exc).__name__)` and return `"project_check_failed"`
        (*connection errors, timeouts and any unexpected error re-check later*).
     2. `_log.info("trace_project_check http_status=%d", response.status_code)` — *the status only; never the body or
        URL.*
     3. `status_code >= 500` → `"project_check_failed"`.
     4. `status_code != 200` (401, 403, 404, 3xx, 429, …) → `"wrong_project"` (*"any other answer"*).
     5. `try: body = response.json()` `except ValueError:` → `"wrong_project"`.
     6. `data = body.get("data") if isinstance(body, dict) else None`; if `not isinstance(data, list) or len(data) != 1`
        → `"wrong_project"` (*an organisation-scoped key listing several projects fails*).
     7. If `not isinstance(data[0], dict) or data[0].get("id") != self._settings.project_id` → `"wrong_project"`
        (*ids compared, never names*). Else `"pass"`.

     `start()`: under lock, return if `self._started or self._closed`, else set `self._started = True`; then
     `result = self._check_project()`; `self._apply_check(result)`; the whole body after the lock in
     `try/except Exception` logging `"trace_sink_error op=start error=%s"` with the class name. *Never raises.*

     `_apply_check(result)`:
     1. Under lock: if closed, return. `self._last_check_at = self._clock()`.
        `pass` → `self._state = "on"`. `wrong_project` → `self._state = "off_wrong_project"`; alert `"wrong_project"`
        if not already in `self._alerted` (add it). `project_check_failed` → `self._state = "off_check_failed"`; alert
        `"project_check_failed"` if not already alerted (add it); if `self._recheck_thread is None`, create
        `threading.Thread(target=self._recheck_loop, name="meridian-trace-recheck", daemon=True)` and remember to
        start it.
     2. Outside the lock: `_log.info("trace_project_check result=%s", result)`; start the thread if created; if an
        alert is due, `self._fire_alert(reason)`.
     *Each reason alerts at most once per process; `on` and `off_wrong_project` are terminal.*

     `_fire_alert(reason)`: `try: self._on_alert(reason)` `except Exception as exc: _log.warning("trace_alert_failed
     reason=%s error=%s", reason, type(exc).__name__)`. *Only the reason code is ever passed.*

     `_recheck_if_due()`: under lock: return unless `not self._closed and self._state == "off_check_failed" and
     self._last_check_at is not None and self._clock() - self._last_check_at >= self._settings.recheck_after_s`; set
     `self._last_check_at = self._clock()` (claims this check). Outside the lock: `self._apply_check(self._check_project())`.
     `_recheck_loop()`: `while not self._stop.wait(self._recheck_poll_s):` call `_recheck_if_due()` in try/except
     (log class name); then `if self._state != "off_check_failed": return`.

I-6. **Masking text (two layers, same function).**
```python
def _mask_text(self, text: str) -> str:
    out = text
    for secret in (self._sk, self._pk):           # exact own keys first, before redact can split their digits
        if secret:
            out = out.replace(secret, _KEY_REMOVED)
    out = _KEY_PATTERN.sub(_KEY_REMOVED, out)     # any sk-/pk- style key (Anthropic, OpenRouter, Langfuse)
    out = self._redact(out, RedactionProfile.TRACE).text
    return _DATA_URI_PATTERN.sub(_DATA_URI_REMOVED, out)

def _safe_mask(self, text: str) -> str:           # in-process layer; fail closed
    try:
        return self._mask_text(text)
    except Exception:
        return _REMOVED
```
     *Every caller-supplied string is masked before it reaches the Langfuse client (so the SDK's media processing, which
     runs before the hook, never sees a data URI or raw value) and again at export.*

I-7. **Admission (`should_export_span=self._admit`) — the bounded queue (MOD-8).**
```python
def _admit(self, span: ReadableSpan) -> bool:
    if span.end_time is None:                     # Langfuse's start-time call (app-root marking only)
        return self._state == "on"
    if span.context is None:
        return False
    trace_id = format_trace_id(span.context.trace_id)
    with self._lock:
        turn = self._turns.get(trace_id)
        if self._state != "on" or self._closed:   # export off: not queued, not counted as dropped
            if turn is not None:
                turn.saw_off = True
            return False
        if self._pending >= self._settings.queue_max_spans:
            self._dropped += 1                    # dropped_spans()
            if turn is not None:
                turn.dropped += 1
            return False
        self._pending += 1
        if turn is not None:
            turn.offered += 1
        return True
```
     *Counting happens exactly once per span (at end); adding a span never blocks; `pending` ≤ `queue_max_spans` ≤ 2048.*

I-8. **The hook (`mask_otel_spans=self._mask_hook`).**
```python
def _mask_hook(self, *, params: MaskOtelSpansParams) -> MaskOtelSpansResult:
    with self._lock:                              # every span leaving the queue frees one slot, exactly once
        self._pending = max(0, self._pending - len(params.spans))
    patches: dict[OtelSpanIdentifier, OtelSpanPatch | None] = {}
    for ident, span in params.spans.items():
        try:
            updates = self._masked_updates(span.attributes)
        except Exception:
            updates = _removed_updates(span.attributes)          # fail closed for this span
        if updates:
            patches[ident] = OtelSpanPatch(set_attributes=updates)
    return MaskOtelSpansResult(span_patches=patches)
```
     `_masked_updates(attributes: Mapping[str, AttributeValue]) -> dict[str, AttributeValue]`, for each `key, value`:
     1. `key in _PASS_THROUGH_KEYS` → skip (*values our code sets from typed fields: ids, enums, numbers*).
     2. `key in _ID_KEYS and isinstance(value, str) and _UUID4.fullmatch(_unquote(value))` → skip (*a UUID may contain a
        six-digit run the CODE rule would eat*); otherwise fall through and mask.
     3. `isinstance(value, str)` → `masked = self._mask_text(value)`; record if changed.
     4. A non-empty `Sequence` whose items are all `str` (check `str` first; `str` is a Sequence) →
        `tuple(self._mask_text(v) for v in value)`; record if changed. Other values (bool, int, float, numeric
        sequences) are left as they are.
     `_unquote(v)`: `v[1:-1]` when `len(v) >= 2 and v[0] == '"' and v[-1] == '"'`, else `v` (Langfuse JSON-encodes
     metadata values). `_removed_updates(attributes)`: every `str` value → `_REMOVED`; every sequence holding a `str` →
     `tuple(_REMOVED for _ in value)`. Module-level functions.
     *The hook never raises; if it somehow did, the SDK drops the batch (fail closed).*

I-9. **Span creation.** Private state per turn:
```python
@dataclass(eq=False)
class _TurnState:
    owner: object
    session_id: str
    observation: LangfuseSpan | None
    trace_id: str | None
    saw_off: bool = False
    setup_failed: bool = False
    offered: int = 0
    dropped: int = 0
    status: ExportStatus | None = None
```
     `_state_of(handle)`: `native = handle.native`; return it when `isinstance(native, _TurnState) and native.owner is
     self`, else `None`.

     `turn(ids)` (a `@contextmanager` generator):
     1. `session = str(ids.thread_id)`; if `self._state != "on" or self._closed` (pending, off or closed): `state =
        _TurnState(owner=self, session_id=session, observation=None, trace_id=None, saw_off=True)`; no span is created.
     2. Else: build `meta = {"turn_id": str(ids.turn_id), "thread_id": session, "request_id": str(ids.request_id),
        "run_tag": ids.run_tag, "agent_version": ids.agent_version}`, plus `"run_id": self._safe_mask(ids.run_id)` when
        `ids.run_id is not None` (*untrusted header value*). `try:` `with propagate_attributes(session_id=session,
        trace_name="turn"): obs = self._client.start_observation(name="turn", as_type="span", metadata=meta)`;
        `state = _TurnState(owner=self, session_id=session, observation=obs, trace_id=obs.trace_id)`; under lock
        `self._turns[obs.trace_id] = state`. `except Exception as exc:` log `"trace_sink_error op=turn error=%s"`
        (class name); `state = _TurnState(owner=self, session_id=session, observation=None, trace_id=None,
        setup_failed=True)`.
     3. `handle = SpanHandle(turn_id=ids.turn_id, trace_id=state.trace_id, native=state)`; `try: yield handle`
        `finally:` (a) if `state.observation is not None`: `try: state.observation.end()` except → log class name
        (*the root span's admission happens here, before the status*); (b) under lock: `state.status =
        self._status_for(state, self._clock())`; `if state.trace_id: self._turns.pop(state.trace_id, None)`.
        *Exceptions raised by the caller's block propagate unchanged; the sink's own never do.*

     `model_call(parent, record, masked_input, masked_output)` — whole body in `try/except Exception` logging
     `"trace_sink_error op=model_call error=%s"`:
     1. `state = self._state_of(parent)`; return if `state is None or state.observation is None`.
     2. `with propagate_attributes(session_id=state.session_id): gen = state.observation.start_observation(
        name=f"model_call:{record.role.value}", as_type="generation", input=self._safe_mask(masked_input),
        output=self._safe_mask(masked_output), model=record.model, usage_details={"input": record.input_tokens,
        "output": record.output_tokens, "cache_read": record.cache_read_tokens, "cache_write":
        record.cache_write_tokens}, cost_details={"total": record.cost_usd}, metadata=self._call_metadata(record),
        level="ERROR" if record.status == "error" else None, status_message=record.failure.kind.value if
        record.failure is not None else None)`; then `gen.end()`.
     `_call_metadata(record) -> dict[str, object]`: `{"role": record.role.value, "provider": record.provider,
     "attempt": record.attempt, "latency_ms": record.latency_ms, "call_status": record.status, "cost_source":
     record.cost_source, "thinking_tokens": record.thinking_tokens}` plus, only when not `None`: `"failure_kind":
     record.failure.kind.value`, `"http_status": record.failure.http_status`, `"stop_reason": record.stop_reason`,
     `"provider_request_id": record.provider_request_id`.

     `node(parent, name, elapsed_ms, status)` — same guard and `try/except` (`op=node`):
     `with propagate_attributes(session_id=state.session_id): span = state.observation.start_observation(
     name=self._safe_mask(name), as_type="span", metadata={"elapsed_ms": elapsed_ms, "node_status":
     self._safe_mask(status)})`; `span.end()`. (*The hook cannot change span names, so names are masked here.* Tool
     spans arrive as `"tool:<name>"` through this method, R-G-17.)

I-10. **Status (MOD-9).**
```python
def _status_for(self, state: _TurnState, now: float) -> ExportStatus:     # call with self._lock held
    if state.saw_off:
        return "off"
    if state.setup_failed or state.dropped > 0:
        return "failed"
    if self._last_batch_failed or self._export_hung(now):
        return "failed"
    return "sent"

def export_status(self, turn: SpanHandle) -> ExportStatus:
    state = self._state_of(turn)
    if state is None:
        return "off" if turn.trace_id is None else "failed"
    with self._lock:
        return state.status if state.status is not None else self._status_for(state, self._clock())
```
     *Fixed when the turn closes; one value per handle; concurrent turns never share counters.* `dropped_spans()`:
     under lock `return self._dropped`. `flush()`: `try: self._client.flush()` except → log class name.

I-11. **`NullTraceSink`** (exact):
```python
class NullTraceSink:                                      # implements TraceSink; exports nothing, holds nothing
    @contextmanager
    def turn(self, ids: TurnIds) -> Iterator[SpanHandle]:
        yield SpanHandle(turn_id=ids.turn_id, trace_id=None)
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None:
        return None
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None:
        return None
    def export_status(self, turn: SpanHandle) -> ExportStatus:
        return "off"
```

I-12. **`register_tracing` body** (replace only the second docstring paragraph and add the body; keep the signature and
     first docstring line):
```python
def register_tracing(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-19 tracing: Langfuse or null trace sink and the project-key check (models.md §4, §7).

    Provides Key[TraceSink]("trace"). LangfuseTraceSink only when all four LANGFUSE_* settings are set
    (Settings.langfuse_complete()); otherwise NullTraceSink and no alert (MOD-6 step 5, MC-24). The sink's on_alert
    calls the container's "alert_writer".fire("trace_export_failed", reason) (AEA-32, cases.md §8); until that key
    exists it logs a fixed line. One LangfuseTraceSink per Langfuse public key per process.
    """
    import logging

    from meridian.adapters.tracing_langfuse import (
        LangfuseExportSettings, LangfuseTraceSink, NullTraceSink, TraceAlertReason,
    )
    from meridian.config import Settings
    from meridian.ports.runtime import TraceSink
    from meridian.privacy.redact import redact

    log = logging.getLogger("meridian.tracing")
    trace_key = Key[TraceSink]("trace")
    typed = cast(Settings, settings)
    pk, sk = typed.langfuse_public_key, typed.langfuse_secret_key
    base_url, project_id = typed.langfuse_base_url, typed.langfuse_project_id
    if not typed.langfuse_complete() or pk is None or sk is None or base_url is None or project_id is None:
        null_sink = NullTraceSink()
        container.provide(trace_key, lambda _c: null_sink)
        return

    def on_alert(reason: TraceAlertReason) -> None:
        try:
            writer = container.get(Key[Any]("alert_writer"))
        except ContainerError:
            log.warning("trace_alert_unbound reason=%s", reason)
            return
        writer.fire("trace_export_failed", reason)

    export_settings = LangfuseExportSettings(public_key=pk, secret_key=sk, base_url=base_url, project_id=project_id)
    try:
        sink = LangfuseTraceSink(export_settings, redact, on_alert)
    except Exception as exc:
        log.warning("trace_sink_error op=build error=%s", type(exc).__name__)
        fallback = NullTraceSink()
        container.provide(trace_key, lambda _c: fallback)
        return
    container.provide(trace_key, lambda _c: sink)
    container.on_start(sink.start)
    container.on_close(sink.close)
```
     *Never a `Settings.langfuse_export()`; `config.py` stays free of adapter imports (R-G-6). The sink is built at
     register time so `on_close` is registered before anything else can fail.* Format with ruff (the import may wrap).
     **The new docstring must not contain the words "No-op until" and must still contain `AEA-19`**: AEA-01's
     `test_every_register_stub_present` checks the ticket token and, after T-4b, skips a hunk whose docstring no longer
     says "No-op until". `on_alert` may run on the re-check thread after the container closed: `container.get` then
     raises `ContainerError("get after close: alert_writer")`, which the `except ContainerError` branch absorbs.

I-13. **`close()`** (idempotent): under lock, return if closed, else `self._closed = True`; `self._stop.set()`; join the
     recheck thread if any (`timeout=self._settings.check_timeout_s + 1.0`); then, each in its own `try/except
     Exception` logging the class name: `self._client.shutdown()`, `self._provider.shutdown()`, `self._http.close()`.
     *Everything the constructor opened is released; a second call does nothing.*

I-14. Run the checks of §7 (affected tests while iterating; full gate once before the final commit). Commit 1:
     `git add src/meridian/adapters/tracing_langfuse.py src/meridian/web/container.py`, message
     `feat(tracing): Langfuse and null trace sinks with project check (AEA-19)`, last line
     `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

### Phase C — context and evidence (same branch, after Phase I passes)

C-1. **Journey record** `docs/testing/journeys/<YYYY-MM-DD>-AEA-19.md` (America/Chicago date of the run), the AEA-04
     record's table shape:
     | Field | Value |
     |---|---|
     | Claim | AEA-19 `adapters/tracing_langfuse.py` and the `register_tracing` hunk: AC-1…AC-10 and PA-1…PA-8. No journey reaches this code: journeys run with `NullTraceSink`. |
     | Level | `mock-tested` |
     | Tested revision | commit 1's SHA |
     | Environment | VPS worktree, Python 3.12, `uv run`; real Langfuse SDK 5.0.4 client with an in-memory span exporter and a stubbed `/api/public/projects`; no server, no network, no model |
     | Command | the affected-tests command of §7 and `uv run python -m tests.journeys.affected --base main` |
     | Result | the pass count; "0 journeys affected" |
     | Evidence location | GitLab issue #19 comment; this file |
     | Remaining limitations | No export to a real Langfuse (OTLP path and the project check against a live server are unproved here); names only by introduction patterns (DAT-1 A) |
     | Blocked by | AEA-51 (CAP-1 at the real entry point), AEA-50 (CAP-9 start-up with right and wrong keys), AEA-61 (live trace records); no journey uses a Langfuse sink |
C-2. **Area map** `.claude/reference/area-map.md`, row **A10a Ops**, last cell `planned` →
     `partly built: adapters/tracing_langfuse.py actual (AEA-19, \`<commit-1 SHA>\`); the rest planned`.
C-3. **ICM** `.claude/state/icm-progress.md`, row *Routes verified against code and tests*: replace the evidence cell
     with `<date>: AEA-19 adapters/tracing_langfuse.py (<SHA>): tests/contract/test_trace_sink_contract.py,
     tests/unit/adapters/test_tracing_langfuse.py, tests/unit/web/test_register_tracing.py pass (<n> passed); earlier
     AEA-04 privacy/redact.py` (≤ 400 characters; keep the other cells).
C-4. **DO-3** `docs/design/code-design.md` §3 tree line
     `│   └── tracing_langfuse.py                      LangfuseTraceSink (mask hook, bounded queue), NullTraceSink A10a  1`
     → append `   built AEA-19 <SHA>` (same style as the `privacy/redact.py` line). Change nothing else in the file.
C-5. **Source register** `docs/source/source-register.md`: confirm `S-233` is still unused
     (`grep -c "S-233" docs/source/source-register.md` → 0; if taken, use the next free S-N and say so in the report),
     then append as the last table row:
     `| S-233 | Langfuse docs, *Public API* — https://langfuse.com/docs/api-and-data-platform/features/public-api | PRIMARY-VENDOR (vendor documentation) | 2026-10-21 | "A successful response returns the project associated with your API key": \`GET /api/public/projects\` with Basic auth (public key, secret key) returns \`data[]\` with \`id\`, \`name\`, \`organization\`. Cited by stage7/models.md §4 (MOD-6) and \`adapters/tracing_langfuse.py\` (AEA-19) |`
C-6. **Dev log** `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<date>-aea-19-tracing-claude-01.md`
     per `.claude/reference/dev-log.md` (header: project, date/timezone America/Chicago, topic, writer `fanout-implementer`
     on Sonnet, host VPS, branch/base SHA; one entry with **Changed / Why / Checked / Remaining**, 50–100 words). It is
     outside this repo: write it, never `git add` it here.
C-7. Commit 2: `git add docs/testing/journeys/<date>-AEA-19.md .claude/reference/area-map.md .claude/state/icm-progress.md
     docs/design/code-design.md docs/source/source-register.md`, message `docs(context): AEA-19 tracing built; journey
     record and S-233`, last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push (the merge
     step pushes main). Never `git add -A`; never force-push.

### What the implementer must NOT do

- Edit a frozen test file (T-4b's two lines in `tests/unit/web/test_container.py` are the test-writer's, not yours),
  `tests/unit/test_import_direction.py`, any other
  `register_*` hunk, `container.py`'s module-level imports, `pyproject.toml`/`uv.lock`, `privacy/redact.py`,
  `config.py`, `ports/*`, `domain/*`, `tests/fakes/*`, `tests/capture/*`, any addendum or contract file.
- Import `langfuse._client.*` (private), call `langfuse.get_client()` or `opentelemetry.trace.set_tracer_provider()`,
  use `propagate_attributes(as_baggage=True)`, or add collector-side masking.
- Log, alert or raise with a key, URL, response body, span text or `str(exc)`; log only fixed strings, reason codes,
  HTTP status ints and exception class names.
- Make any network call in a default test (no `live` test is required; do not add one); bind ports 4019 or 5184.
- Read `.env` or source the workspace `.env`; put a real-looking phone, code, card number or key literal in code.
- Block a turn on export (no `queue.put` with timeout, no `flush()` inside `turn`/`model_call`/`node`).
- Change `export_status` to take no argument, or write to any database.

---

## 6. Data and fixtures (synthetic only)

### 6.1 Values

All private-looking values are built at run time (no literal full phone, code, card or key in source), following AEA-04's
`tests/unit/privacy/test_redact.py` helpers. The only literals are the issued, fictional WP-2 identifiers from
`docs/data/worked-pairs.md` WP-2: **Omar Patel**, **MHC-10002**, **INV-204411**, **$478.00**, due 2026-11-01.

| Value | How it is built (seed 19, `random.Random(19)`) | Source |
|---|---|---|
| Phone | `"-".join(("512", "555", "01" + "02"))` → the WP-2 phone; last two digits `02` | ticket WP-2 (fictional 555-01xx) |
| Code | `str(rng.randint(100000, 999999))` | synthetic |
| Card-like number | 16 random digits grouped by 4 with spaces | synthetic (AEA-04 `_card`) |
| Fake provider key | `"sk-ant-test-" + "".join(rng.choice("abcdef0123456789") for _ in range(24))` | synthetic |
| Langfuse keys | `(f"pk-lf-test-{uuid.uuid4().hex}", f"sk-lf-test-{uuid.uuid4().hex}")`, fresh per sink | synthetic (SDK singleton per key, §4.4 fact 5) |
| Project ids | `PROJECT_ID = "proj-aea19-this-app"`, `OTHER_PROJECT_ID = "proj-aea19-other-app"`, `PROJECT_NAME = "meridian-call-center"` | synthetic |
| Base URL | `"http://langfuse.test"` (never resolved: `MockTransport`) | synthetic |

WP-2 text (`wp2_text(values)`):
`f"Hi, my name is Omar Patel, phone {phone}. My code is {code}. Card {card}. Key {api_key}. Invoice INV-204411 for
MHC-10002 is $478.00, due 2026-11-01."`

### 6.2 `tests/unit/adapters/_tracing_doubles.py` (frozen; exact API)

```python
PROJECT_ID: str; OTHER_PROJECT_ID: str; PROJECT_NAME: str; BASE_URL: str          # §6.1
def new_keys() -> tuple[str, str]: ...
def seeded_values(seed: int = 19) -> dict[str, str]: ...      # keys: "phone", "code", "card", "api_key"
def wp2_text(values: Mapping[str, str]) -> str: ...
def turn_ids(run_id: str | None = None, turn_id: str | None = None) -> TurnIds: ...
    # TurnIds.model_validate({"thread_id": str(uuid.uuid4()), "turn_id": turn_id or str(uuid.uuid4()),
    #     "request_id": str(uuid.uuid4()), "run_tag": "live", "run_id": run_id, "agent_version": "test"})
    # (plain strings through validation; never call ThreadId(...)/TurnId(...) directly)
def call_record(**overrides: object) -> CallRecord: ...
    # defaults: provider="anthropic", model="claude-sonnet-5-5", latency_ms=1200, input_tokens=100, output_tokens=20,
    # cache_read_tokens=0, cache_write_tokens=0, thinking_tokens=0, cost_usd=0.0004, cost_source="price_table",
    # status="ok", failure=None, provider_request_id="req_test_0001", stop_reason="end_turn",
    # role=Role.RESPONDER, attempt=1; built with CallRecord.model_validate({...defaults, **overrides})

class ProjectsStub:                                           # the /api/public/projects endpoint
    def __init__(self, *handlers: Callable[[httpx.Request], httpx.Response]) -> None: ...
    requests: list[httpx.Request]                             # every request seen, in order
    @property
    def transport(self) -> httpx.MockTransport: ...           # MockTransport(self)
    def __call__(self, request: httpx.Request) -> httpx.Response: ...
        # append request; use handlers[min(len(requests) - 1, len(handlers) - 1)]
def ok(project_id: str = PROJECT_ID, name: str = PROJECT_NAME) -> Callable[[httpx.Request], httpx.Response]: ...
    # 200 {"data": [{"id": project_id, "name": name, "organization": {"id": "org-test", "name": "Test org"}}]}
def other() -> Callable[...]: ...        # 200, one project: id OTHER_PROJECT_ID, name PROJECT_NAME (same name as ours)
def several() -> Callable[...]: ...      # 200, two projects: ours and OTHER_PROJECT_ID
def status(code: int) -> Callable[...]: ...   # Response(code, json={"message": "nope-body-marker"})
def connect_error() -> Callable[...]: ...     # raises httpx.ConnectError("unreachable", request=request)
def read_timeout() -> Callable[...]: ...      # raises httpx.ReadTimeout("timed out", request=request)
def unexpected_error() -> Callable[...]: ...  # raises ValueError("unexpected")

class FakeClock:
    now: float                                                # starts at 1000.0
    def __call__(self) -> float: ...
    def advance(self, seconds: float) -> None: ...

class HangingExporter(SpanExporter):                          # export() blocks until release is set
    release: threading.Event
    spans: list[ReadableSpan]
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult: ...   # release.wait(timeout=30); store; SUCCESS
    def shutdown(self) -> None: ...                           # release.set()
class ErroringExporter(SpanExporter):
    calls: int
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult: ...   # calls += 1; raise RuntimeError("export failed for test")
    def shutdown(self) -> None: ...

def span_strings(span: ReadableSpan) -> list[str]: ...        # span.name + every str attribute value + str items of sequences
def trace_hex(span: ReadableSpan) -> str: ...                 # format(span.context.trace_id, "032x")

def build_sink(registry: list[Any], *, exporter: SpanExporter | None = None, stub: ProjectsStub | None = None,
               clock: FakeClock | None = None, alerts: list[object] | None = None,
               keys: tuple[str, str] | None = None, redactor: Redactor | None = None,
               recheck_poll_s: float = 3600.0,
               **overrides: Any) -> tuple[Any, SpanExporter, ProjectsStub, list[object]]: ...
    # tl = importlib.import_module("meridian.adapters.tracing_langfuse")
    # exporter default InMemorySpanExporter(); stub default ProjectsStub(ok()); clock default FakeClock();
    # alerts default []; keys default new_keys(); redactor default meridian.privacy.redact.redact
    # settings = tl.LangfuseExportSettings(public_key=SecretStr(pk), secret_key=SecretStr(sk), base_url=BASE_URL,
    #     project_id=PROJECT_ID, **{"batch_interval_s": 3600.0, **overrides})
    # on_alert records the full positional args tuple: alerts.append(args) via `lambda *args: alerts.append(args)`
    # sink = tl.LangfuseTraceSink(settings, redactor, on_alert, span_exporter=exporter, transport=stub.transport,
    #     clock=clock, recheck_poll_s=recheck_poll_s)
    # registry.append(sink); return sink, exporter, stub, alerts
def close_all(registry: list[Any]) -> None: ...
    # for each sink: if its exporter is a HangingExporter set release first (tests keep the pair), then sink.close()
```
Each test file defines `@pytest.fixture def sinks() -> Iterator[list[Any]]` that yields a list and calls
`close_all(list)` at teardown. `batch_interval_s=3600.0` keeps the BSP worker asleep, so nothing is exported until a test
calls `sink.flush()` (deterministic).

### 6.3 `tests/contract/test_trace_sink_contract.py` (frozen)

- `test_mask_hook_strips_seeded_values` (AC-1): `sink.start()`; `with sink.turn(turn_ids()) as h:`
  `sink.model_call(h, call_record(), wp2_text(v), wp2_text(v))`; `sink.node(h, "front", 12, "ok")`; then a direct span
  `sink._client.start_observation(name="direct", input=wp2_text(v)).end()`; `sink.flush()`. Over every exported span's
  `span_strings`: `v["phone"]`, `"Omar Patel"`, `v["code"]`, `v["card"]`, `v["api_key"]`, both Langfuse keys are absent;
  per value, `re.sub(r"\D", "", v["card"])` is not in `re.sub(r"\D", "", s)`; the model-call span's
  `langfuse.observation.input` contains `"[phone ending 02]"`, `"my name is [name]"`, `"INV-204411"`, `"$478.00"`,
  `"MHC-10002"`; the direct span's input contains `"[phone ending 02]"` and `"INV-204411"`. Print the masked input.
- `test_mask_applies_to_all_span_kinds` (AC-2): `code = seeded_values()["code"]`; turn with `turn_ids(run_id=f"run-{code}")`;
  inside: `node(h, f"tool:{code}", 3, f"failed {code}")`, `model_call(h, call_record(), f"code {code}", f"again {code}")`;
  a direct client span with `input=f"code {code}"` and `metadata={"note": f"code {code}"}`; flush. Exactly 4 spans; for
  each: `code` absent from `span_strings` and `"[code]"` present in at least one of its strings (turn: the `run_id`
  metadata; node: name; model call: input; direct: input). The direct span proves the hook alone masks.
- `test_sinks_conform` (AC-8): parametrised `["null", "langfuse"]`. `sink: TraceSink = …` (annotated, so mypy proves the
  Protocol). `with sink.turn(ids) as h`: `isinstance(h, SpanHandle)`, `h.turn_id == ids.turn_id`; `model_call(...)` and
  `node(...)` return `None`; `export_status(h)` ∈ `{"off","sent","failed"}`. Null: `h.trace_id is None`, status `"off"`,
  and the null sink has no `_client` attribute (sends nothing). Langfuse: `re.fullmatch(r"[0-9a-f]{32}", h.trace_id)`,
  status `"sent"`.
- `test_ids_and_numbers_pass_unchanged` (PA-1): `ids = turn_ids(turn_id="3f1c2a4e-8b7d-4e21-9a6b-a123456b7c8d")` (a
  canonical UUID4 whose last group holds the six-digit run `123456`, which the CODE rule would otherwise mask); `call_record(input_tokens=123456, cost_usd=0.012345,
  failure=<ProviderFailure kind=TIMEOUT, provider="anthropic", http_status=408, retry_after_s=None, retryable=True,
  provider_request_id=None>, status="error", attempt=2, latency_ms=8001)`. After flush: root span attribute
  `langfuse.observation.metadata.turn_id == json.dumps(str(ids.turn_id))` and `session.id == str(ids.thread_id)`;
  generation span: `langfuse.observation.model.name == "claude-sonnet-5-5"`, `json.loads(usage_details)["input"] ==
  123456`, `json.loads(cost_details)["total"] == 0.012345`, metadata `attempt == "2"`, `latency_ms == "8001"`,
  `http_status == "408"`, `role == '"responder"'`, `langfuse.observation.level == "ERROR"`.

### 6.4 `tests/unit/adapters/test_tracing_langfuse.py` (frozen)

- `test_export_never_blocks` (AC-3), four parts, each timing every call with `time.perf_counter()` (turn enter, each
  `node`/`model_call`, turn exit) and asserting `max < 0.050`; print the max in ms:
  1. **Hanging, default cap 1,024**: `HangingExporter`; `start()`; one turn with 1,600 `node` calls and 50 `model_call`
     calls; after the turn: `dropped = sink.dropped_spans()`, `dropped > 0`, `dropped >= 1651 - (1024 + 512)`,
     `export_status(h) == "failed"`; then `exporter.release.set()`, `sink.flush()`, and
     `len(exporter.spans) + dropped == 1651` (the spans refused are exactly the ones not exported).
  2. **Small cap, deterministic**: `queue_max_spans=8`, in-memory exporter; one turn with 20 `node` calls → after exit
     `dropped_spans() == 13` (21 offered incl. the root, 8 admitted); flush → exactly 8 spans exported.
  3. **Erroring exporter**: `ErroringExporter`; turn A with 5 nodes; `sink.flush()` raises nothing; turn B with 5 nodes:
     calls under 50 ms, `export_status(hB) == "failed"`, `exporter.calls >= 1`.
  4. **Client failure**: `monkeypatch.setattr(sink._client, "start_observation", <raises RuntimeError>)`; `with
     sink.turn(...) as h` raises nothing, `h.trace_id is None`, `node`/`model_call` raise nothing,
     `export_status(h) == "failed"`.
- `test_wrong_project_keys_turn_export_off` (AC-4): parametrised `other()`, `several()`, `status(401)`, `status(403)`.
  `start()`; `alerts == [("wrong_project",)]`; `len(stub.requests) == 1`, its URL path `== "/api/public/projects"` and
  its `Authorization` header `== "Basic " + base64(pk:sk)`; a turn with a node and a model call → `h.trace_id is None`,
  `export_status(h) == "off"`; a direct client span is created and ended; `flush()`; `len(exporter.get_finished_spans())
  == 0`; `clock.advance(601)`; `sink._recheck_if_due()`; still one request and one alert.
- `test_unreachable_at_start_rechecks` (AC-5): parametrised `connect_error()`, `read_timeout()`, `status(503)`,
  `unexpected_error()` (plan-added case), each followed by `ok()` in the stub. `sink.start()` returns `None` (no raise);
  `alerts == [("project_check_failed",)]`; turn A → `export_status == "off"`, `trace_id is None`;
  `clock.advance(599)`; `_recheck_if_due()` → 1 request; `clock.advance(1)`; `_recheck_if_due()` → 2 requests, alerts
  unchanged; turn B → `"sent"`; flush → every exported span's `trace_hex == hB.trace_id`.
- `test_one_trace_per_turn_with_session_id` (AC-6): stub `ok(name="some-other-name")`; turn with one node and one model
  call; flush; exactly 3 spans; all `trace_hex == h.trace_id` (32 hex); the span named `"turn"` has `parent is None`
  and attribute `langfuse.trace.name == "turn"`; the other two have `parent.span_id == root.context.span_id`; all three
  have `session.id == str(ids.thread_id)`. A second turn gets a different trace id.
- `test_export_status_values` (AC-7): (a) healthy → `"sent"`; (b) `queue_max_spans=4`, a turn with 6 nodes → `"failed"`;
  (c) `ErroringExporter`: turn A, `flush()`, turn B → `"failed"`; (d) `NullTraceSink` → `"off"`, sink with stub
  `other()` → `"off"`; (e) interleaved, `queue_max_spans=4`: enter A and B (`cm.__enter__()`), `node(A)`, `node(B)`,
  `node(B)`, exit A (root admitted, 4th slot) → A `"sent"`; `node(B)` (dropped), exit B → B `"failed"`; (f) each status
  read twice is the same and every value seen ∈ `{"off","sent","failed"}`.
- `test_keys_never_logged` (AC-10): `monkeypatch.setenv("LANGFUSE_DEBUG", "true")`; `caplog.set_level(logging.DEBUG)`.
  Three sinks: stub `status(401)`; stub `connect_error()`; stub `ok()` plus a model call whose `masked_input` contains
  both Langfuse keys, then flush. Keys absent from `caplog.text` and from every record's `args`; `"nope-body-marker"`
  absent from `caplog.text`; every alert call is exactly `("wrong_project",)` or `("project_check_failed",)`; keys
  absent from every exported span string.
- `test_mask_fails_closed` (PA-2): `redactor` that raises `RuntimeError` for every call; `ok()` stub; a model call with
  `wp2_text(v)`; flush; the generation's `langfuse.observation.input == "[removed]"`; no seeded value anywhere.
- `test_data_uri_never_reaches_client` (PA-3): model call with `masked_input="see data:text/plain;base64,QUJD end"`;
  flush; input contains `"[data uri removed]"` and not `"base64,"`.
- `test_settings_bounds_rejected` (PA-4): `queue_max_spans` 0 and 4096, `batch_interval_s=0` → `ValueError` at
  construction; the message contains the field name and no key.
- `test_adapter_import_direction` (PA-5): `ast` scan of `src/meridian/adapters/tracing_langfuse.py`: no relative import;
  every top-level name ∈ stdlib ∪ `{"httpx", "langfuse", "opentelemetry", "pydantic", "meridian"}`; no module starting
  `langfuse._`; `meridian.*` imports ⊆ `{"meridian.ports.models", "meridian.ports.runtime", "meridian.privacy.redact"}`
  ∪ `meridian.domain.*`. Print the list.
- `test_close_is_idempotent_and_stops_recheck` (PA-6): stub `connect_error()`, `build_sink(..., recheck_poll_s=0.01)`;
  `start()`; a thread named
  `"meridian-trace-recheck"` is alive; `close()`; `close()` again raises nothing; the thread is no longer alive within
  2 s.

### 6.5 `tests/unit/web/test_register_tracing.py` (frozen)

Helpers in the file: `BASE_ENV = {"ANTHROPIC_API_KEY": "test-anthropic", "OPENROUTER_API_KEY": "test-openrouter",
"MERIDIAN_DEMO_USERNAME": "demo-user", "MERIDIAN_DEMO_PASSWORD": "demo-pass-test", "MERIDIAN_SESSION_SECRET":
"session-secret-test"}`; `langfuse_env()` returns the four `LANGFUSE_*` values (fresh `new_keys()`, `BASE_URL`,
`PROJECT_ID`); `run_hunk(settings, alert_writer=None)` builds `Container(settings=settings, limits=Limits())`, provides
`Key[Any]("alert_writer")` when given, calls `register_tracing(c, FastAPI(), settings=settings, limits=c.limits)`,
`c.build()`, returns `c` (caller closes it).

- `test_sink_choice_by_settings` (AC-9): a recording writer `fire(*args)`; for each of the four `LANGFUSE_*` names
  missing in turn: `Settings.from_env(BASE_ENV | env_without_it)` → `c.get(Key[TraceSink]("trace"))` is a
  `NullTraceSink`; writer calls `== []`. Then all four set, with `monkeypatch.setattr(LangfuseTraceSink, "start",
  recording_start)`: the sink is a `LangfuseTraceSink`; `start` called once (by `build()`'s starters);
  `sink._settings == LangfuseExportSettings(public_key=SecretStr(pk), secret_key=SecretStr(sk), base_url=BASE_URL,
  project_id=PROJECT_ID)`; writer calls `== []`; `not hasattr(Settings, "langfuse_export")` and
  `"langfuse_export" not in inspect.getsource(register_tracing)`. Close each container.
- `test_on_alert_reaches_alert_writer` (PA-7): `monkeypatch.setattr(tracing_module, "LangfuseTraceSink", FakeSink)`
  where `FakeSink.__init__(self, settings, redact, on_alert)` stores `on_alert` and has no-op `start`/`close`. With a
  writer bound: `captured_on_alert("wrong_project")` → writer calls `== [("trace_export_failed", "wrong_project")]`.
  Without a writer: the call raises nothing and `caplog.text` contains `"trace_alert_unbound reason=wrong_project"`.
- `test_build_failure_falls_back_to_null` (PA-8): `FakeSink.__init__` raises `RuntimeError`; all four set →
  `NullTraceSink` provided; no exception; `"trace_sink_error op=build"` logged.

---

## 7. Checks

Run from the worktree root after `export UV_LINK_MODE=hardlink` and `uv sync`. Cheapest first; stop at the first red.
No `-n` needed (these tests use threads; run them serially).

`PATHS = src/meridian/adapters/tracing_langfuse.py src/meridian/web/container.py tests/unit/adapters/_tracing_doubles.py
tests/unit/adapters/test_tracing_langfuse.py tests/contract/test_trace_sink_contract.py tests/unit/web/test_register_tracing.py
tests/unit/web/test_container.py`

| Check | Command | Passing looks like |
|---|---|---|
| Lint | `uv run ruff check $PATHS` | `All checks passed!` |
| Format | `uv run ruff format --check $PATHS` | `7 files already formatted` |
| Type check | `uv run mypy $PATHS` | `Success: no issues found in 7 source files` |
| Affected tests (iterate + final) | `uv run pytest -q -rP tests/contract/test_trace_sink_contract.py tests/unit/adapters/test_tracing_langfuse.py tests/unit/web/test_register_tracing.py tests/unit/web/test_container.py tests/unit/test_import_direction.py tests/unit/test_skeleton.py` | all pass (T-4b's lines let the filled `register_tracing` through `test_every_register_stub_present`); if that one test still fails, report its assertion and do not edit the file (§8 R-1) |
| Who else is affected | `grep -rln "tracing_langfuse\|register_tracing\|meridian.web.container" tests/ src/` | only the files above |
| Journeys (AC-11) | `uv run python -m tests.journeys.affected --base main` | `0 journeys affected`, exit 0 |
| Collect | `uv run pytest --collect-only -q` | exit 0 |
| Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py /home/linuxuser/workspaces/inno-aea-callcenter` | no new FAIL |
| Capture verification | n/a here: CAP-1 is AEA-51's, CAP-9 is AEA-50's (§3) | — |
| Evaluation check | n/a (ticket *Evaluation*: no E-check added) | — |

**Full suite:** not required. The change adds a leaf adapter, its tests and one hunk; no shared fixture, setting,
dependency or lockfile changes (rule `build-loop-test-scope`).

**Existing tests that must stay green:** `tests/unit/web/test_container.py` (all of it, with T-4b's lines),
`tests/unit/test_import_direction.py` (in particular `test_container_imports_only_policy_limits`: the hunk's imports are
inside the function), `tests/unit/test_skeleton.py`, and AEA-02's tests if the merge brings them into the run.

---

## 8. Risks and requests

**Requests to the orchestrator / integrator (no product decision):**

1. **R-1 — AEA-01's `test_every_register_stub_present` fails for every filled hunk.** It calls each real hunk with
   `SimpleNamespace(name="stand-in")` as settings and asserts `not fresh._factories`; a filled `register_tracing` reads
   `settings.langfuse_*` (AttributeError) and provides a key. This plan does **not** work around it inside the hunk (an
   `isinstance` early return would hide a mis-wired container). It adopts the fix the hunk-ticket plans already agreed
   (AEA-17 §3.5, AEA-10 R-13): the two-line `continue` of step T-4b, made by whichever hunk ticket lands first, skipped by
   the rest. **Collision with AEA-01 (merged) and every hunk ticket (10, 17, 18, 26, 27, …):** identical text, so a
   merge of two copies conflicts trivially; the merge step keeps one copy. Request to the integrator: settle it once, at
   the first hunk merge of wave 1.
2. **R-2 — Container key names this ticket fixes (other tickets must use them):** `Key[TraceSink]("trace")` (AEA-51's
   `register_graph` reads it for `ModelGateway(trace=…)`, `SpecialistRunner`, `TurnService`, `PersonRequestService`;
   AEA-20's plan R-3 asked who builds the gateway) and `Key[AlertWriter]("alert_writer")` (AEA-32's `register_ops`
   should provide it; until then `on_alert` logs `trace_alert_unbound` and the evaluator still shows
   `trace_export_failed` from `off`/`failed` turns, MC-24). Forward to the AEA-32 and AEA-51 planners.
3. **R-3 — Direct third-party imports.** The adapter imports `opentelemetry-sdk` and
   `opentelemetry-exporter-otlp-proto-http`, which are installed as `langfuse>=5,<6` dependencies but not declared in
   `pyproject.toml` (AEA-01's). Optional follow-up on AEA-01: declare them (one line each plus a regenerated lock; that
   merge runs the full suite). Not a blocker.
4. **R-4 — Additions to the models.md §4 sketch:** four keyword-only constructor parameters (`span_exporter`,
   `transport`, `clock`, `recheck_poll_s`) and two methods (`flush()`, `close()`). The positional signature and every
   named type are unchanged; addenda are drafts, not signed contracts. A one-line note in models.md §4 would help AEA-50
   and AEA-51 (not this ticket's file).
5. **R-5 — Issue comment.** Post PA-1…PA-8 on issue #19 at merge, as the template asks.

**Design risks (accepted, recorded):**

- **SDK coupling.** The design relies on two SDK behaviours (fact 1: hook on every exported span; fact 2:
  `should_export_span` called at start with `end_time is None` and at end). Both are public parameters; the start-time
  call is an implementation detail, so `_admit` answers it without counting. A Langfuse upgrade inside `>=5,<6` that
  changes either is caught by AC-2/AC-3/AC-7.
- **OTLP headers copied from the SDK** (`x-langfuse-ingestion-version: 4`, Basic auth, endpoint
  `/api/public/otel/v1/traces`). Not exercised by any default test (no network); first proved by AEA-50's CAP-9 stub and
  AEA-61's live trace record. `LANGFUSE_OTEL_TRACES_EXPORT_PATH` is ignored on purpose.
- **One sink per public key per process** (SDK singleton). Production builds one; tests use fresh keys. A second app
  instance in one process with the same keys (only possible in tests) would share the first one's pipeline.
- **`sent` blind window** (MOD-9): turns closing between Langfuse going down and the first failed or hung batch read
  `sent` (≈ batch interval + export timeout, ~10 s [A]).
- **Pass-through keys** (`_PASS_THROUGH_KEYS`) are trusted because only this sink creates spans on its private client;
  a span created directly on `_client` with free text under one of those exact keys would not be masked. No code path
  does that; `_client` is private.
- **Status code 429 at start-up** is "any other answer" → `wrong_project` (literal MOD-6 step 3). If Langfuse
  rate-limits the check, export stays off until a redeploy; the alert makes it visible.
- **Environment overrides.** `LANGFUSE_TRACING_ENABLED=false` or `OTEL_SDK_DISABLED=true` in the deployed environment
  would silently disable spans while the check reports on; neither is set by this project (data.md §9 lists the
  variables). `OTEL_BSP_MAX_QUEUE_SIZE` below 2048 would re-enable the BSP's silent drop; not set.
- **Timing threshold** 50 ms [A] per call under parallel CPU load: the planner measured a 5.2 ms worst case; if the
  frozen test flakes on a loaded host, report the measured max instead of editing the test.
- **Shared doc lines:** the area-map A10a row is later edited by AEA-32; the ICM *Routes verified* row and the source
  register are touched by several wave-1 tickets. The merge step keeps every ticket's change on the shared line.
- **AEA-02 drift.** This plan copies AEA-02's plan; if the merged code renamed `Settings.from_env`, a re-export home or
  a field, the merged code wins (adjust imports only). A missing type stops the work (`blocked-on AEA-02`).
- No signed contract (`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`) is touched; no decision D-4…D-15 is answered
  differently (DAT-1 option A and DAT-4 option A stand; with DAT-4 B nothing here changes).

---

## 9. Readiness

**READY**, with one import blocker: **AEA-02** must be merged first (`meridian.ports.runtime` `SpanHandle`,
`ExportStatus`, `TurnIds`, `TraceSink`; `meridian.ports.models` `CallRecord`, `Role`, `ProviderFailure`;
`meridian.config.Settings` with the four `langfuse_*` fields and `langfuse_complete()`). AEA-01 and AEA-04 are on main.
Same-wave and later siblings (AEA-11, 20, 32, 40, 42, 50, 51, 53) are reached by Protocol or container key only.

**Merge gate note:** T-4b's two lines (or the identical lines from an earlier hunk merge) must be on the branch, or
`test_every_register_stub_present` stays red (§8 R-1). No journey gate exists before AEA-57; the affected-journey command
must print `0 journeys affected`.

No `NEEDS-DECISION`.

## Gates

None human, external, paid or live for the build. `risk::security`: frozen tests first (Phase T);
`security-privacy-agent` reads this diff at the wave-1 merge. Turning export on in the deployed app is a deploy-time
`gate::human` step outside this ticket (Innocent creates the Langfuse project and sets `LANGFUSE_PROJECT_ID`; models.md
cross-topic 7).

## Deviations

Implementer (Sonnet 5.5), 2026-10-21, commit `2d5b692` on `aea-19-aea-19-langfuse-sink`.

1. **SDK logger guard (I-3 step 8 replaced).** The plan pinned the `langfuse` logger to WARNING after building the
   client. The SDK resets its own logger level while starting and logs the public key at INFO (`Startup: Langfuse
   tracer successfully initialized | public_key=...`), so frozen `test_keys_never_logged` failed. Fix: a private
   `_LogGuard` logging filter on the `langfuse` logger, added before the client is built, that drops records below
   WARNING and scrubs our two keys from the rest; `close()` removes it.
2. **File size.** `adapters/tracing_langfuse.py` is about 660 lines after `ruff format` (plan target 450, adapter cap
   600). Not split: the plan names one file; a split needs the integrator's say-so.
3. **`_str_items` helper** replaces the plan's `_is_str_sequence` so mypy can narrow the attribute-value union without
   `type: ignore`. Behaviour is the same.
4. Context edits: the ICM *Routes verified* row exists twice on the branch; the second (latest) row's evidence cell was
   replaced, so the merge step should keep each ticket's evidence on the shared line.
