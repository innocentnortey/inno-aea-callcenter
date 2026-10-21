# Plan — [AEA-19-F1] register_tracing honours Key("trace_override")

**Status:** planned (READY)
**Issue:** none (wave-fix item, not a ticket; source of truth is `AEA-51.md` §8 R-1) · **Base revision:** `main` `9d12b8f`
**Lane:** `lane::build-loop`. **Security label:** recommended **off** (see §8 R-4); if the orchestrator adds
`risk::security`, the five tests in §5 step 3 become frozen tests written first by `test-writer-agent`.
**Planner model:** claude-opus-5-5. **Implementer:** Sonnet.

---

## 1. Goal and sources

### Goal

`register_tracing` (AEA-19's hunk in `src/meridian/web/container.py`) provides `Key[TraceSink]("trace")` itself, at
register time, and `register_graph` (AEA-51) runs 22 hunks later. The container refuses a second `provide` of the same
key (`ContainerError("already provided: trace")`), so the test-only `ContainerOverrides.trace` sink can never reach
`TurnService` (AEA-40) or `PersonRequestService` (AEA-42), which both read `Key("trace")` when they are built.

This fix changes only `register_tracing`'s body and docstring:

- **When `Key[TraceSink]("trace_override")` is provided** (only AEA-51's `register_graph` will do that, from
  `overrides.trace`), `Key("trace")` resolves to that override sink, and the Langfuse sink, if one was built, is
  **not started** (no project-check HTTP call).
- **When it is not provided**, everything behaves exactly as now: the same sink choice from the four `LANGFUSE_*`
  settings, the same build-failure fallback, the same `on_alert` binding, the same start and close hooks.

Concrete example. Input: a test builds an app whose container has `register_tracing` (no Langfuse settings, so
`NullTraceSink` would be chosen), then `Key("trace_override")` bound to an `InMemoryTraceSink` `S`. Process: at
`container.build()`, the `Key("trace")` factory asks the container for `trace_override`, finds it, and returns `S`;
`TurnService` and `PersonRequestService` are built with `S`. Output: one customer turn ("hello") run through the
container's `TurnService` leaves exactly one `RecordedTurn` in `S.turns`, with that turn's `turn_id`. Without the
override the same turn records into `NullTraceSink`, as today.

### Sources (read by the planner; the implementer needs only this plan)

| Source | Location | What it obliges here |
|---|---|---|
| The request | `docs/plans/fanout/2026-10-21-build/AEA-51.md` §8 **R-1** (and §3.3 row "Sink choice … `overrides.trace` replaces it", §5 A2 step 1) | Mechanism: `Key("trace")` factory returns `c.get(Key[TraceSink]("trace_override"))` when provided; a `ContainerError` whose message is exactly `not provided: trace_override` → the existing choice; any other error re-raised. `register_graph` stays the only reader of `overrides`; no consumer key changes |
| AEA-19 plan | `docs/plans/fanout/2026-10-21-build/AEA-19.md` (AC-9, PA-7, PA-8, AC-11) | The existing behaviour that must not change; its tests in `tests/unit/web/test_register_tracing.py` are **frozen** (AEA-19 was `risk::security`) |
| Test-only overrides | `docs/design/contracts/stage7/web.md` §15 (`ContainerOverrides`, R-W-8) | `trace: TraceSink \| None` — "None → the container's own choice (models.md §7)"; only `register_graph` reads `overrides`; the deployed factory passes none |
| Sink choice | `docs/design/contracts/stage7/models.md` §7 (the illustrative wiring block: `trace = LangfuseTraceSink(...) if <all four LANGFUSE_* set> else NullTraceSink()`), §4 MOD-6 (start-up project check) | Unchanged on the no-override path |
| Container mechanics | `src/meridian/web/container.py` lines 29–124 (`ContainerError`, `Key`, `Container`) | `provide` refuses duplicates and anything after `build`; `get` raises `ContainerError(f"not provided: {name}")` and `ContainerError(f"provider cycle: …")`; `build()` builds every factory in insertion order, then runs starters |
| Build loop | `.claude/rules/build-loop-test-scope.md` + *AEA addition*; `.claude/rules/integrated-journeys.md` §4 | Implementer writes code and tests together; affected tests + fast gates + affected journeys before the final commit; one journey record |

Decisions D-4…D-15 in `docs/plans/stage7-signoff.md` are not touched by this fix (none concerns the trace key).

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer creates or edits)

| File | Change | Limit |
|---|---|---|
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_tracing`** (currently lines 294–344) | ≈ +18 lines; nothing else in the file changes, including the module import block |
| `tests/unit/web/test_register_tracing_override.py` | **create** | ≤ 220 lines |
| `docs/testing/journeys/2026-10-21-AEA-19-F1.md` | **create** (journey record; use the America/Chicago date of the run if it is not 2026-10-21) | — |

### 2.2 Shared surfaces, read only (never edit)

- `tests/unit/web/test_register_tracing.py` — **frozen** (AEA-19, `risk::security`). Must stay byte-for-byte unchanged and green.
- `tests/unit/web/test_container.py`, `tests/unit/web/test_register_chat.py`, `tests/unit/web/test_register_person_request.py`.
- `tests/fakes/` (`InMemoryTraceSink`, `FixedClock`), `tests/services/chat_doubles.py`, `tests/services/chat_storage.py`,
  `tests/fixtures/sqlite.py`, `tests/api/web_shell_support.py`, `tests/unit/adapters/_tracing_doubles.py`.
- `src/meridian/adapters/tracing_langfuse.py`, `src/meridian/services/turn.py`, `src/meridian/services/person_request.py`,
  `src/meridian/web/app.py`, `src/meridian/web/deps.py`, `src/meridian/web/middleware.py`.

### 2.3 Owned by other slices (do not touch)

- `register_graph` (lines 1071–1077) — **AEA-51 builds it** (its step A2.1 provides `Key[TraceSink]("trace_override")`).
  Do not add a provider of `trace_override` anywhere in `src/`; do not read `overrides` in `register_tracing`.
- `register_chat`, `register_person_request` and every other hunk; `Container`, `Key`, `ContainerError`, `build_container`.
- Never edit: the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
  `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, any `.claude/` file, `docs/plans/**` (except nothing: this plan is the planner's).

---

## 3. Requirements table

| ID | Requirement (source) | How it is implemented | How it is verified |
|---|---|---|---|
| F1-1 [invariant] | With `Key("trace_override")` bound, `Key("trace")` resolves to it when Langfuse is **not** configured (R-1) | `chosen(c, null_sink)` factory (§5 step 1) | `tests/unit/web/test_register_tracing_override.py::test_override_replaces_null_sink` |
| F1-2 [invariant] | With the override bound and all four `LANGFUSE_*` set, `Key("trace")` is the override and the Langfuse sink is **not started**; it is still closed with the container; no Langfuse key value appears in any log line | `chosen(c, sink)` + `start_if_chosen` starter; `on_close(sink.close)` unchanged | `::test_override_wins_over_langfuse_and_langfuse_is_not_started` |
| F1-3 [boundary] | With the override bound and the Langfuse sink failing to build, `Key("trace")` is the override; the existing `trace_sink_error op=build` line is still logged | `chosen(c, fallback)` | `::test_override_replaces_build_failure_fallback` |
| F1-4 [failure] | A `ContainerError` other than `not provided: trace_override` (e.g. a provider cycle) is re-raised, never swallowed into the default sink | `if str(exc) != f"not provided: {override_key.name}": raise` | `::test_other_container_errors_are_not_swallowed` |
| F1-5 [invariant, worked pair] | Both consumers get the override: `TurnService` and `PersonRequestService` hold it, and a turn run through the container records into it; the no-override twin records into the settings choice (`NullTraceSink`) | No consumer change; the key resolves at build time | `::test_override_reaches_turn_and_person_request_services` and `::test_without_override_services_get_the_settings_choice` |
| F1-6 [regression] | With no override the container behaves exactly as before | No-override path keeps the same objects, log lines and hooks; `start_if_chosen` calls `sink.start()` exactly when `Key("trace")` is the Langfuse sink, i.e. always when no override is bound | Frozen `tests/unit/web/test_register_tracing.py` (all 4 tests, 7 cases) unchanged and green; `tests/unit/web/test_container.py` green (it requires the docstring to contain `AEA-19` and **not** `No-op until`) |
| F1-7 [journey] | Single journey criterion: every journey that imports `web/container.py` passes with the same results as on `main` (they run the no-override path) | — | `uv run python -m tests.journeys.affected --base main -- -rs`; record `docs/testing/journeys/2026-10-21-AEA-19-F1.md`, **Level `integrated with a scripted model`** for the no-override path; the override path is `mock-tested` (unit level) and **Blocked by AEA-51** (no journey binds `trace_override` until `register_graph` does) |
| F1-8 [gate] | ruff and mypy clean | — | §7 checks 1–3 |
| F1-9 [privacy] | No raw exception or secret in logs | The fix adds **no** log line; it re-raises unexpected `ContainerError`s (the build fails loudly; `build_container` already closes and re-raises) | F1-2's caplog assertion |

**Worked pair.** No WP-N from `docs/data/worked-pairs.md` applies: this fix has no customer-facing behaviour. The
worked-pair-shaped evidence is F1-5: the same one-turn input ("hello") with and without the override, and the sink
each run records into.

**Entry-point registration.** None: no entry point, route or workflow is added or changed.

---

## 4. Shared code to use (copied from `main` at `9d12b8f`)

### 4.1 Container (`src/meridian/web/container.py`)

```python
class ContainerError(RuntimeError):
    """A wiring mistake: an unknown, duplicate or cyclic provider, or use after build or close."""

@dataclass(frozen=True)
class Key[T]:
    name: str

class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...
        # raises ContainerError(f"provide after build: {key.name}") / ContainerError(f"already provided: {key.name}")
    def get[T](self, key: Key[T]) -> T: ...
        # ContainerError(f"get after close: {name}") / ContainerError(f"not provided: {name}") /
        # ContainerError(f"provider cycle: {chain}"); memoised; works after build() (returns the built object)
    def on_start(self, starter: Callable[[], None]) -> None: ...   # ContainerError("on_start after build")
    def on_close(self, closer: Callable[[], None]) -> None: ...
    def build(self) -> None: ...    # get() every factory in insertion order, set built, then run starters in order
    def close(self) -> None: ...    # closers newest first; ExceptionGroup if any fail
```

The same "absent key" idiom already used by `register_chat` (lines 772–778) and `register_person_request`:

```python
        except ContainerError as exc:
            if str(exc) == f"not provided: {key.name}":
                ...
            raise
```

### 4.2 The current `register_tracing` (lines 294–344, verbatim)

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
        LangfuseExportSettings,
        LangfuseTraceSink,
        NullTraceSink,
        TraceAlertReason,
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

    export_settings = LangfuseExportSettings(
        public_key=pk, secret_key=sk, base_url=base_url, project_id=project_id
    )
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

### 4.3 Consumers (unchanged; why the key must be right at build time)

- `register_chat` (line 769: `trace_key: Key[Any] = Key("trace")`; line 804: `c.get(trace_key)` inside the `TURN_SERVICE`
  factory) → `TurnService.__init__(uow, demo_clock, wall_clock, spend, trace: TraceSink, run_graph, settled_view, limits,
  agent_version, *, monotonic=...)`, stored as `self._trace`; `run_turn` opens `with self._trace.turn(ids) as span:`
  (`services/turn.py` line 379).
- `register_person_request` (line 873: `("trace", Key[Any]("trace"))`) → `PersonRequestService(uow, handoff, composer,
  trace, demo_clock, wall_clock)` (keywords), stored as `self._trace`. If any of its six keys is absent it provides a
  private `_NotBound` instead, which has no `_trace`.
- `ContainerOverrides` (`web/app.py` line 46): `trace: TraceSink | None = None`. AEA-51 will do
  `container.provide(Key[TraceSink]("trace_override"), lambda _c: sink)` inside `register_graph`.

### 4.4 Test helpers (copied signatures)

```python
# tests/fakes/__init__.py
from tests.fakes import FixedClock, InMemoryTraceSink
class InMemoryTraceSink:                       # tests/fakes/trace.py
    def __init__(self, *, status: ExportStatus = "sent") -> None: ...
    @property
    def turns(self) -> tuple[RecordedTurn, ...]: ...
@dataclass
class RecordedTurn:  ids: TurnIds; trace_id: str; model_calls: list; nodes: list; closed: bool = False

# tests/api/web_shell_support.py
def make_settings(tmp_path: Path, **changes: Any) -> Settings: ...   # field names, generated secrets, no env read

# tests/fixtures/sqlite.py
@contextmanager
def temp_sqlite(*, issued_path: Path = ISSUED_DB) -> Iterator[TempStore]: ...   # TempStore(data_dir, db_path, issued_path, uow)

# tests/services/chat_doubles.py
WALL_NOW = dt.datetime(2026, 10, 21, 15, 30, tzinfo=dt.UTC)
class FakeSpendGuard:  def __init__(self, allow: bool = True) -> None: ...
class ScriptedRunGraph: def __init__(self, *items) -> None: ...      # no items → answered_outcome
class FakeComposer: ...                                               # settled_view only
def text_payload(text: str) -> dict[str, Any]: ...
def make_cmd(thread_id, payload, *, turn_id=None, demo_session=DEMO_SESSION, run_tag="live", run_id=None) -> Any  # RunTurn; .turn_id

# tests/services/chat_storage.py
def seed_thread(uow, demo_session=DEMO_SESSION, *, controller=None, outcome="open", at=WORKED_PAIRS_NOW, run_tag="live") -> ThreadId

# tests/unit/adapters/_tracing_doubles.py
BASE_URL = "http://langfuse.test"; PROJECT_ID = "proj-aea19-this-app"
def tracing_module() -> Any: ...          # importlib of meridian.adapters.tracing_langfuse
def new_keys() -> tuple[str, str]: ...    # fresh (pk, sk) per sink: one SDK pipeline per public key per process

# meridian.web.deps
TURN_SERVICE: Key[Any] = Key("turn_service"); PERSON_REQUESTS: Key[Any] = Key("person_requests")
HANDOFF_SERVICE = Key("handoff_service"); REPLY_COMPOSER = Key("reply_composer"); UOW_FACTORY = Key("uow_factory")
# meridian.web.middleware
WebShellState(settings=..., wall_clock=..., public_paths=PublicPaths())
```

`Settings` fields (`meridian/config.py` lines 175–178): `langfuse_public_key: SecretStr | None`,
`langfuse_secret_key: SecretStr | None`, `langfuse_base_url: str | None`, `langfuse_project_id: str | None`.

---

## 5. Steps

**Step 0 — orient (no edits).**
```bash
cd <your worktree>; export UV_LINK_MODE=hardlink
git log --oneline -1 main            # 9d12b8f or later
grep -n "trace_override" src/ tests/ -r   # expect no output (nobody provides or reads it yet)
sed -n 294,344p src/meridian/web/container.py   # must match §4.2; if not, stop and report the diff
```
If `register_graph` on `main` already provides `trace_override` (AEA-51 merged first), still proceed: this fix is what
makes that provide reach the consumers; report it.

**Step 1 — replace `register_tracing` (body and docstring only).** Write exactly this (the import block inside the
function is unchanged):

```python
def register_tracing(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-19 tracing: Langfuse or null trace sink and the project-key check (models.md §4, §7).

    Provides Key[TraceSink]("trace"). LangfuseTraceSink only when all four LANGFUSE_* settings are set
    (Settings.langfuse_complete()); otherwise NullTraceSink and no alert (MOD-6 step 5, MC-24). The sink's on_alert
    calls the container's "alert_writer".fire("trace_export_failed", reason) (AEA-32, cases.md §8); until that key
    exists it logs a fixed line. One LangfuseTraceSink per Langfuse public key per process.

    AEA-19-F1: when Key[TraceSink]("trace_override") is provided (only register_graph does, from the test-only
    ContainerOverrides.trace; web.md §15, R-W-8), Key("trace") returns that sink and the Langfuse sink is never
    started. Any ContainerError other than "not provided: trace_override" is re-raised.
    """
    import logging

    from meridian.adapters.tracing_langfuse import (
        LangfuseExportSettings,
        LangfuseTraceSink,
        NullTraceSink,
        TraceAlertReason,
    )
    from meridian.config import Settings
    from meridian.ports.runtime import TraceSink
    from meridian.privacy.redact import redact

    log = logging.getLogger("meridian.tracing")
    trace_key = Key[TraceSink]("trace")
    override_key = Key[TraceSink]("trace_override")

    def chosen(c: Container, default: TraceSink) -> TraceSink:
        try:
            return c.get(override_key)
        except ContainerError as exc:
            if str(exc) != f"not provided: {override_key.name}":
                raise
            return default

    typed = cast(Settings, settings)
    pk, sk = typed.langfuse_public_key, typed.langfuse_secret_key
    base_url, project_id = typed.langfuse_base_url, typed.langfuse_project_id
    if not typed.langfuse_complete() or pk is None or sk is None or base_url is None or project_id is None:
        null_sink = NullTraceSink()
        container.provide(trace_key, lambda c: chosen(c, null_sink))
        return

    def on_alert(reason: TraceAlertReason) -> None:
        try:
            writer = container.get(Key[Any]("alert_writer"))
        except ContainerError:
            log.warning("trace_alert_unbound reason=%s", reason)
            return
        writer.fire("trace_export_failed", reason)

    export_settings = LangfuseExportSettings(
        public_key=pk, secret_key=sk, base_url=base_url, project_id=project_id
    )
    try:
        sink = LangfuseTraceSink(export_settings, redact, on_alert)
    except Exception as exc:
        log.warning("trace_sink_error op=build error=%s", type(exc).__name__)
        fallback = NullTraceSink()
        container.provide(trace_key, lambda c: chosen(c, fallback))
        return

    def start_if_chosen() -> None:
        if container.get(trace_key) is sink:
            sink.start()

    container.provide(trace_key, lambda c: chosen(c, sink))
    container.on_start(start_if_chosen)
    container.on_close(sink.close)
```

The invariant each part protects:

1. **`chosen` is called inside the factory, not at register time.** `register_graph` provides `trace_override` 22 hunks
   later, but every `provide` happens before `container.build()`, so when the `Key("trace")` factory runs (during
   `build()`), the override is visible. *Invariant: one sink per app, chosen once, memoised.*
2. **Only the exact message `not provided: trace_override` means "absent".** A cycle (`provider cycle: …`) or a
   use-after-close error is a wiring bug and must fail the build. *Invariant: no wiring mistake silently degrades to
   the settings sink.*
3. **`start_if_chosen` replaces `on_start(sink.start)`.** With no override `container.get(trace_key) is sink` is always
   true, so start runs exactly as before (same position in the starter list). With an override the Langfuse sink is
   never started, so no project-check HTTP request leaves the test process. *Invariant: an override means "this sink,
   not Langfuse".* `container.get` after `build()` returns the memoised object (it only refuses after close).
4. **`on_close(sink.close)` stays unconditional.** `LangfuseTraceSink.close()` is safe on a sink that never started
   (it sets the stop event, joins no thread, shuts down the client, provider and HTTP client, logging only
   `trace_sink_error op=close_<name> error=<ExceptionType>`). *Invariant: the httpx client and OTel provider built at
   register time are always released.*
5. **The `lambda _c:` parameters become `lambda c:`** because they now use the container. No other line changes.

Run the frozen tests now: `uv run pytest -q tests/unit/web/test_register_tracing.py tests/unit/web/test_container.py`
→ all pass.

**Step 2 — fast gates on the hunk.** `uv run ruff check src/meridian/web/container.py`,
`uv run ruff format --check src/meridian/web/container.py`, `uv run mypy src/meridian/web/container.py` → clean.
(mypy accepts `chosen(c, null_sink)` because `NullTraceSink` and `LangfuseTraceSink` already satisfy `TraceSink`: the
current `container.provide(trace_key, lambda _c: null_sink)` type-checks.)

**Step 3 — create `tests/unit/web/test_register_tracing_override.py`.** Module docstring:
`"""AEA-19-F1: register_tracing returns Key("trace_override") as Key("trace") when it is provided (AEA-51 §8 R-1)."""`

Imports (sorted by ruff's isort; `meridian` and `tests` are first-party):

```python
from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from meridian.config import Settings
from meridian.policy.limits import Limits
from meridian.ports.runtime import TraceSink
from meridian.services.person_request import PersonRequestService
from meridian.services.turn import TurnService
from meridian.web.container import (
    Container,
    ContainerError,
    Key,
    register_chat,
    register_person_request,
    register_tracing,
    register_web,
)
from meridian.web.deps import PERSON_REQUESTS, TURN_SERVICE
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.web_shell_support import make_settings
from tests.fakes import FixedClock, InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.chat_doubles import (
    WALL_NOW,
    FakeComposer,
    FakeSpendGuard,
    ScriptedRunGraph,
    make_cmd,
    text_payload,
)
from tests.services.chat_storage import seed_thread
from tests.unit.adapters._tracing_doubles import BASE_URL, PROJECT_ID, new_keys, tracing_module
```

Module constants and helpers:

```python
TRACE = Key[TraceSink]("trace")
OVERRIDE = Key[TraceSink]("trace_override")


@pytest.fixture
def containers() -> Iterator[list[Container]]:
    opened: list[Container] = []
    yield opened
    for c in opened:
        c.close()


def langfuse_settings(tmp_path: Path) -> tuple[Settings, str, str]:
    pk, sk = new_keys()
    settings = make_settings(
        tmp_path,
        langfuse_public_key=pk,
        langfuse_secret_key=sk,
        langfuse_base_url=BASE_URL,
        langfuse_project_id=PROJECT_ID,
    )
    return settings, pk, sk


def tracing_only(opened: list[Container], settings: Settings, override: object | None) -> Container:
    """register_tracing first, then the override (as register_graph does, later), then build."""
    c = Container(settings=settings, limits=Limits())
    opened.append(c)
    register_tracing(c, FastAPI(), settings=settings, limits=c.limits)
    if override is not None:
        c.provide(OVERRIDE, lambda _c: override)  # type: ignore[arg-type,return-value]
    c.build()
    return c
```

(Drop the `# type: ignore` if mypy reports it unused; `tests.*` has `disallow_untyped_defs = false` but still checks
calls. If mypy complains instead, type `override` as `TraceSink | None` and pass `InMemoryTraceSink()` directly.)

```python
def wired_services(
    opened: list[Container], store: TempStore, tmp_path: Path, override: InMemoryTraceSink | None
) -> Container:
    """The real tracing, chat and person-request hunks on one container; siblings are doubles."""
    settings = make_settings(tmp_path)          # no LANGFUSE_* → the settings choice is NullTraceSink
    limits = Limits()
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=settings, wall_clock=lambda: WALL_NOW, public_paths=PublicPaths()
    )
    c = Container(settings=settings, limits=limits)
    opened.append(c)
    for name, obj in (
        ("uow_factory", store.uow),
        ("ledger", FakeSpendGuard(True)),
        ("demo_clock", FixedClock()),
        ("run_graph", ScriptedRunGraph()),
        ("reply_composer", FakeComposer()),
        ("handoff_service", object()),
    ):
        c.provide(Key[Any](name), lambda _c, o=obj: o)  # type: ignore[misc]
    register_web(c, app, settings=settings, limits=limits)
    register_tracing(c, app, settings=settings, limits=limits)
    register_chat(c, app, settings=settings, limits=limits)
    register_person_request(c, app, settings=settings, limits=limits)
    if override is not None:
        c.provide(OVERRIDE, lambda _c: override)   # last, as register_graph runs after both consumers
    c.build()
    return c
```

The six tests (names exact; each docstring starts with its failure-mode word):

1. `test_override_replaces_null_sink(tmp_path, containers)` — `"""invariant (F1-1): no LANGFUSE_* and an override bound: Key("trace") is the override."""`
   `sink = InMemoryTraceSink()`; `c = tracing_only(containers, make_settings(tmp_path), sink)`;
   `assert c.get(TRACE) is sink`.

2. `test_override_wins_over_langfuse_and_langfuse_is_not_started(tmp_path, monkeypatch, caplog, containers)` —
   `"""invariant (F1-2, F1-9): all four LANGFUSE_* and an override: the override is used, Langfuse is never started, keys never logged."""`
   `tl = tracing_module()`; `started: list[object] = []`;
   `monkeypatch.setattr(tl.LangfuseTraceSink, "start", lambda self: started.append(self))`;
   `caplog.set_level(logging.DEBUG)`; `settings, pk, sk = langfuse_settings(tmp_path)`;
   `sink = InMemoryTraceSink()`; `c = tracing_only(containers, settings, sink)`;
   `assert c.get(TRACE) is sink`; `assert started == []`; `c.close()` (must not raise);
   `assert pk not in caplog.text and sk not in caplog.text`.
   (The real `LangfuseTraceSink` is constructed: no network happens at construction; `close()` releases it.)

3. `test_override_replaces_build_failure_fallback(tmp_path, monkeypatch, caplog, containers)` —
   `"""boundary (F1-3): the Langfuse sink cannot be built and an override is bound: the override is used; the build-failure line is still logged."""`
   Monkeypatch `tl.LangfuseTraceSink` with a local class `BrokenSink` whose `__init__(self, settings, redact, on_alert)`
   raises `RuntimeError("cannot build")` (same pattern as the frozen test); `caplog.set_level(logging.DEBUG)`;
   `settings, _, _ = langfuse_settings(tmp_path)`; `sink = InMemoryTraceSink()`;
   `c = tracing_only(containers, settings, sink)`; `assert c.get(TRACE) is sink`;
   `assert "trace_sink_error op=build error=RuntimeError" in caplog.text`; `assert "cannot build" not in caplog.text`.

4. `test_other_container_errors_are_not_swallowed(tmp_path, containers)` —
   `"""failure (F1-4): an override factory that reads Key("trace") is a cycle; the build raises instead of falling back."""`
   `c = Container(settings=make_settings(tmp_path), limits=Limits())`; `containers.append(c)`;
   `register_tracing(c, FastAPI(), settings=c.settings, limits=c.limits)`;
   `c.provide(OVERRIDE, lambda cc: cc.get(TRACE))`;
   `with pytest.raises(ContainerError, match="provider cycle: trace -> trace_override -> trace"): c.build()`.

5. `test_override_reaches_turn_and_person_request_services(tmp_path, containers)` —
   `"""invariant (F1-5, worked pair, with override): both consumers hold the override, and one turn records into it."""`
   ```python
   with temp_sqlite() as store:
       thread = seed_thread(store.uow)
       cmd = make_cmd(thread, text_payload("hello"))
       sink = InMemoryTraceSink()
       c = wired_services(containers, store, tmp_path, sink)
       turns = c.get(TURN_SERVICE)
       requests = c.get(PERSON_REQUESTS)
       assert isinstance(turns, TurnService) and turns._trace is sink
       assert isinstance(requests, PersonRequestService) and requests._trace is sink
       assert c.get(TRACE) is sink
       turns.run_turn(cmd)
       assert [t.ids.turn_id for t in sink.turns] == [cmd.turn_id]
       assert sink.turns[0].closed
       print([t.ids.turn_id for t in sink.turns])
       c.close()   # close before temp_sqlite removes the data dir
   ```

6. `test_without_override_services_get_the_settings_choice(tmp_path, containers)` —
   `"""regression (F1-5/F1-6, worked pair, no override): both consumers hold the settings choice (NullTraceSink)."""`
   Same as 5 with `override=None`: `tl = tracing_module()`; `chosen = c.get(TRACE)`;
   `assert isinstance(chosen, tl.NullTraceSink)`; `assert turns._trace is chosen and requests._trace is chosen`;
   `turns.run_turn(cmd)` returns without raising (the turn ran with the null sink). `c.close()` inside the `with`.

Keep the file ≤ 220 lines. Synthetic values only (§6).

**Step 4 — affected tests and gates** (§7, in order, stop at the first red).

**Step 5 — affected journeys** (§7 check 6) and write the journey record (§5 step 6).

**Step 6 — journey record** `docs/testing/journeys/2026-10-21-AEA-19-F1.md` (date = America/Chicago date of the run),
using the `integrated-journeys.md` §4 fields:

| Field | Value to write |
|---|---|
| Claim | AEA-19-F1: `register_tracing` returns `Key("trace_override")` as `Key("trace")` when it is provided, and leaves the no-override path unchanged (F1-1…F1-9) |
| Level | No-override path: `integrated with a scripted model` (the affected journeys). Override path: `mock-tested` (unit tests with doubles) |
| Tested revision | the commit SHA of the code commit; "uncommitted" if run before it |
| Environment | Host `claude-vultr`; Python 3.12; uv; journeys as `tests.journeys.affected` launches them; no model reached beyond the scripted adapter; no Langfuse settings |
| Command | the exact commands of §7 checks 4 and 6 |
| Result | pass/fail counts per command; the journeys selected count; any pre-existing red quoted with its assertion |
| Evidence location | this file plus the pytest output |
| Remaining limitations | No journey binds a trace override yet, so the override path has no integrated evidence |
| Blocked by | AEA-51 (`register_graph` provides `trace_override` from `overrides.trace`; its AC-1/AC-17 carry the integrated proof) |

**Step 7 — commit** on your branch (factory mode; never push; never `git add -A`):
```bash
git add src/meridian/web/container.py tests/unit/web/test_register_tracing_override.py \
        docs/testing/journeys/2026-10-21-AEA-19-F1.md
git commit -F- <<'EOF'
fix(AEA-19-F1): register_tracing honours Key("trace_override")

Key("trace") now returns the trace_override sink when register_graph provides it
(AEA-51 §8 R-1), so the test-only ContainerOverrides.trace reaches TurnService and
PersonRequestService. With no override the sink choice, fallback, alert binding and
start/close hooks are unchanged; an overridden Langfuse sink is never started.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

## 6. Data and fixtures

Synthetic only. Langfuse keys come from `tests/unit/adapters/_tracing_doubles.py::new_keys()` (`pk-lf-test-<uuid>`,
`sk-lf-test-<uuid>`), base URL `http://langfuse.test`, project `proj-aea19-this-app`. App secrets come from
`make_settings` (generated per test, nothing read from the environment). The SQLite store is `temp_sqlite()`, a
per-test copy of the issued DB built by `migrate`; the issued file is never written. Turn text is `"hello"`. No phone
number, code, card-like number or real person appears. No network: the Langfuse sink is constructed but never started
in the override tests (and `start` is monkeypatched in test 2); no model call anywhere.

---

## 7. Checks

`PATHS = src/meridian/web/container.py tests/unit/web/test_register_tracing_override.py`

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check $PATHS` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check $PATHS` | `2 files already formatted` |
| 3 | Type check | `uv run mypy $PATHS` | `Success: no issues found in 2 source files` |
| 4a | Tests while iterating | `uv run pytest -q -rP tests/unit/web/test_register_tracing_override.py tests/unit/web/test_register_tracing.py tests/unit/web/test_container.py tests/unit/web/test_register_chat.py tests/unit/web/test_register_person_request.py` | all pass; the frozen file's 7 cases unchanged |
| 4b | Affected tests, once before the commit (every test file importing the changed module) | `uv run --with pytest-xdist pytest -n 2 -q -rs $(grep -rlE "meridian\.web\.container\|register_tracing" tests/ \| grep -v '^tests/journeys/' \| grep -E '/test_[^/]*\.py$') tests/unit/test_import_direction.py tests/unit/test_skeleton.py` | no failures; skips only with their existing reasons |
| 5 | Frozen file untouched | `git diff --exit-code main -- tests/unit/web/test_register_tracing.py` | exit 0, no output |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main -- -rs` (serial) | about 30 journeys selected at `9d12b8f`; all pass or skip with their existing `blocked-on …` reasons |
| 7 | Scope | `git diff --name-only main` | exactly the three owned files |
| 8 | Collect | `uv run pytest --collect-only -q > /dev/null` | exit 0 |

**A red that is not yours.** If a test in 4b or a journey in 6 fails, prove whether it already failed on `main`:
`git stash push src/meridian/web/container.py`, re-run only that test id, `git stash pop`. If it fails both ways, quote
its assertion in your report and the journey record and do not fix, skip or edit it. If it passes on `main` and fails
with the change, the fix is wrong: return to step 1.

**Full suite:** not required. The change is one hunk's body in one module; no shared fixture, setting, dependency,
lockfile or cross-package seam changes (`build-loop-test-scope.md`). The 4b set already covers every test importing the
module.

**Capture verification / evaluation check:** n/a. No workflow, entry point, prompt or model path changes; CAP-1 at the
real entry point is AEA-51's AC-17.

### Must not do

- Do not edit `tests/unit/web/test_register_tracing.py` or any other existing test.
- Do not edit `register_graph`, any other hunk, the `Container` class, `build_container` or the module import block.
- Do not add a `has()` / `provided()` method to `Container`; use the exact-message idiom.
- Do not read `overrides` in `register_tracing`; do not provide `trace_override` anywhere in `src/`.
- Do not move the Langfuse sink's construction into the factory (it would change the no-override build timing and the
  frozen tests' expectations).
- Do not add a log line (in particular none that prints the exception text, settings or keys).
- No `monkeypatch` of any `meridian` module other than `tracing_langfuse` (as the frozen tests do); no network; no paid
  call; no `.env` read; do not bind ports 4019 or 5184; pytest `-n 2` at most; `export UV_LINK_MODE=hardlink`.

---

## 8. Risks and requests

| # | Kind | Item | Handling |
|---|---|---|---|
| R-1 | Collision | AEA-51's branch edits `register_graph` in the same file; this fix edits only `register_tracing` | Different hunks, ≈ 750 lines apart; git merges them cleanly. Merge this fix **before** AEA-51 (its §8 R-1 asks for that). If AEA-51 merges first, nothing breaks: its `trace_override` provide is inert until this lands |
| R-2 | File size | `container.py` is 1,134 lines (orchestrator cap 700, `code-structure.md`); this adds ≈ 18 | Already AEA-51 §8 R-3's request to the integrator (split hunks into per-area modules later); not this fix |
| R-3 | Behaviour detail | With an override and Langfuse configured, the Langfuse sink is built (httpx client, OTel provider) but never started; it is still closed | Intended; proved by test 2. The deployed factory never passes an override (web.md §15), so production always takes the start path |
| R-4 | Label | AEA-19 was `risk::security`; this fix touches its hunk | Recommendation: no `risk::security`. A bug here could at worst stop Langfuse starting or pick a test sink; it cannot export more data, grant access or expose a key (no new log line, and the override exists only in test code). The frozen AEA-19 tests stay untouched and must pass. If the orchestrator labels it, the six new tests become frozen tests first and the diff goes to the wave-merge security review |
| R-5 | Follow-up for others | AEA-51 plan §3.3 marks AC-1/AC-17/AC-18/AC-21/AC-46/AC-47 `blocked-on AEA-19-F1` | After merge the orchestrator updates AEA-51's status line; not this fix's files |
| R-6 | Journey run time | ~30 journeys run serially | Acceptable; `-n 2` only if the orchestrator asks |

No `NEEDS-DECISION`: no signed contract changes (web.md §15 already says `trace` replaces the container's choice), and
no stage-7 decision is reopened.

---

## 9. Readiness

**READY.** Every import exists on `main` at `9d12b8f`; nothing waits on another branch. `blockedOn`: none.

## Gates

None (no human, external, paid or live gate).
