# Plan — [AEA-58-F1] browser harness additions A-1…A-3 that AEA-62 needs

**Status:** planned — READY. Nothing to wait for: AEA-58's `tests/journeys/browser/` package is on `main` (`821e134`,
merged `eb51ba4`), AEA-57's harness is on `main`, AEA-51 is merged (`5539bca`). No signed contract changes.
**Issue:** none (wave-fix item, not a ticket; source of truth is `docs/plans/fanout/2026-10-21-build/AEA-62.md` §8 R-1,
§4.2, §4.3, §5 Step 0) · **Base revision:** `main` `8785135` · **Lane:** build-loop · **Risk:** none (no
`risk::security`: plan → implement with tests → review; no frozen tests, no security agent)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-22 · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-58-f1-browser-additions` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-58-F1`), cut from `main` at or after `8785135`.

---

## 1. Goal and sources

### Goal

Add the three harness pieces AEA-62 stops on at its Step 0, exactly as AEA-62 §8 R-1 specifies, without changing how
today's callers (`browser_journey` fixture, `serve.py`, `j1/test_aea_58.py`, `j9/test_aea_58.py`) behave:

- **A-1 run options.** `open_browser_journey` gains `script`, `with_clock` and `overrides_for`; a new fixture
  `browser_journey_factory` opens runs with an index directory, a run clock, a caller's script and a caller's override
  builder.
- **A-2 selectors.** 46 new logical keys in `SELECTOR_KEYS` (AEA-62 §4.3), parametric rows (one `{value}`
  placeholder), and `locate_by(target, key, value)`.
- **A-3 element screenshot.** `BrowserRun.screenshot_element(bp, target, label)`.

Concrete example of what AEA-62 will write once this lands:

```python
with browser_journey_factory(index_dir=idx, with_clock=True, script=StepScript(), overrides_for=_overrides) as brun:
    bp = brun.open(PHONE)
    ...
    row = locate_by(bp.page, "queue.row_by_ref", "MHC-C-0009")      # parametric key, value filled in
    brun.screenshot_element(bp, locate(bp.page, "chat.block.account_card").last, "account-card")
```

### Context

AEA-58 merged at `eb51ba4` without these additions. AEA-62's Step 0 greps for `def browser_journey_factory`,
`def locate_by`, `def screenshot_element`, `overrides_for` and prints `SELECTOR_KEYS`; today all four are missing and
`SELECTOR_KEYS` has only AEA-58's 16 keys, so AEA-62 cannot start. This follow-up lands them first.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Source of truth | `docs/plans/fanout/2026-10-21-build/AEA-62.md` §8 R-1 (A-1, A-2, A-3), §4.2 (merged API copy), §4.3 (selector keys table), §5 Step 0 (the acceptance grep) | Exact signatures, the key list, the Step 0 check |
| AEA-58 plan | `docs/plans/fanout/2026-10-21-build/AEA-58.md` §5 *must NOT*, §7 checks | Same prohibitions (no `locator(`/`get_by_` outside `selectors.py`, no invented rows, no `playwright install`, no `node_modules` in the worktree) |
| Wall-clock seam | `docs/design/contracts/stage7/web.md` §15 (`ContainerOverrides.wall_clock`, D-13) | A-1's clock goes in only through `ContainerOverrides.wall_clock`, as AEA-57's `open_journey` does; no new seam |
| Settings | `src/meridian/config.py` `ENV_NAMES["index_dir"] == "MERIDIAN_INDEX_DIR"`, `Settings.index_dir: Path` | `index_dir` reaches the app only as the env name |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md`, `context-maintenance.md` | Affected tests + affected journeys + fast gates before the commit; no context-row change (no file, owner or route moves) |
| DO-3 / DO-4 | `docs/design/code-design.md` §9 (`journeys/browser/` line), `docs/design/contracts/internal-components.md` | n/a for signatures: neither names the browser harness API; this slice changes test-harness code only. DO-3 §9's `browser/` description stays true |
| Requirements, eval, observability, metrics | PRD, DO-5, DO-6, DO-7 | n/a: test harness only; no product entry point, no capture surface, no metric |

### Source-contract reconciliation

| Obligation | Governing source | In R-1 | Disposition | Plan step |
|---|---|---|---|---|
| `OverridesFor` alias; `open_browser_journey(..., script, with_clock, overrides_for)` | R-1 A-1 | yes | in-ticket | Step 1 |
| `browser_journey_factory` fixture with `open_run(*, index_dir, with_clock, script, overrides_for)` composing exactly as `browser_journey` | R-1 A-1 | yes | in-ticket | Step 2 |
| Today's callers keep their behaviour | R-1 A-1 | yes | in-ticket (one shared composer `_browser_run`, defaults equal today's) | Steps 1–2, check C-4 |
| Every §4.3 key in `SELECTOR_KEYS` with its state description | R-1 A-2 | yes | in-ticket | Step 3 |
| Parametric rows: one `{value}` placeholder; `locate_by` | R-1 A-2 | yes | in-ticket; **decided here:** the placeholder may sit in `value` or (role rows) in `name`, exactly one in total, so a `role=row name={value}` contract row also works | Step 3 |
| Rows stay empty until `selectors.md` gives them | R-1 A-2, AEA-58 AC-16 | yes | in-ticket: `CONTRACT_ROWS` stays `MappingProxyType({})` | Step 3 |
| A value put into a selector cannot break the selector | (plan-added PA-1) | no | added: `locate_by` accepts only `^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$` (covers `"56"`, `"4"`, `"MHC-C-0009"`, `"src-12"`) | Step 3 |
| A parametric key cannot be used without a value, and the reverse (plan-added PA-2) | — | no | added: `locate`/`locate_in` on a parametric key and `locate_by` on a plain key raise `ValueError` | Step 3 |
| `screenshot_element` with the same label rule, path pattern, bookkeeping | R-1 A-3 | yes | in-ticket | Step 4 |
| README paragraph *Adding a browser journey later* | R-1 | yes | in-ticket | Step 5 |
| Own self-checks in `test_browser_support.py` | R-1 | yes | in-ticket | Step 6 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test harness only) | — | — | — |

---

## 2. Boundary

### File map — owned files (the only files the implementer edits; no new files)

| File | Today (lines) | Change |
|---|---|---|
| `tests/journeys/browser/server.py` | 82 | A-1: `INDEX_DIR_ENV`, `OverridesFor`, `_default_overrides`, three new keyword parameters on `open_browser_journey` |
| `tests/journeys/browser/plugin.py` | 133 | A-1: private `_browser_run` composer; `browser_journey` delegates to it; new fixture `browser_journey_factory` |
| `tests/journeys/browser/selectors.py` | 88 | A-2: 46 keys, `PLACEHOLDER`, `PARAMETRIC_KEYS`, `PARAM_VALUE`, `fill_row`, `_row`, `_build`, `locate_by`; `locate`/`locate_in` go through `_build` |
| `tests/journeys/browser/pages.py` | 113 | A-3: `_shot_path` helper, `screenshot_element`; `screenshot` keeps its behaviour |
| `tests/journeys/browser/test_browser_support.py` | 287 | 8 new self-checks + 2 module fixture overrides (target ≤ 450 lines; hard cap 500) |
| `tests/journeys/browser/README.md` | 89 | Rewrite *Adding a browser journey later*; one sentence added to *Selectors* |

### Shared surfaces read only (never edit)

`tests/journeys/browser/{build,network,record,steps,serve,__init__}.py`, `tests/journeys/support/**` (AEA-57),
`tests/journeys/j1/test_aea_58.py`, `tests/journeys/j9/test_aea_58.py`, `tests/conftest.py`, `tests/journeys/affected.py`,
`tests/integration/customer_support.py` (AEA-51), `src/meridian/**`, `pyproject.toml`, `uv.lock`.

### Owned by other slices / never touched

`apps/web/**`, `docs/ux/**`, `docs/plans/ux-join/**` (the UX session's selector contract), `ui-contracts.openapi.yaml`,
`UI_CONTRACTS.md`, the briefing, issued data, `docs/archive/`, `docs/parked/`, AEA-62's files
(`tests/journeys/j{2,3,6,8}/test_aea_62.py`), the AEA-62 plan, `.claude/reference/area-map.md`,
`.claude/state/icm-progress.md`, `docs/design/code-design.md` (no row changes: no file, owner or route moves; DO-3 §9's
`browser/` description stays accurate). No other open branch (AEA-40, AEA-61, FU-person-request) touches
`tests/journeys/browser/` (checked with `git diff --name-only main...<branch>`).

---

## 3. Requirements table

| ID | Requirement (R-1 wording or plan-added) | How it is implemented | How it is verified |
|---|---|---|---|
| A-1a | `OverridesFor = Callable[[Settings, JourneyScript, Callable[[], datetime] \| None], tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]]` in `server.py` | Step 1.2 | mypy clean (C-3); `test_browser_journey_factory_run_options` passes a builder |
| A-1b | `open_browser_journey(*, collector, strict, nodeid, build, environ_overrides=None, script=None, with_clock=False, overrides_for=None)`: `script = script if script is not None else JourneyScript()`; `clock = StepClock() if with_clock else None`; `overrides, models = (overrides_for or _default_overrides)(settings, script, clock)`; `JourneyRun(..., script=script, clock=clock, ...)` | Step 1.3 | `test_browser_journey_factory_run_options` (the builder sees `(run.settings, script, run.clock)`; `run.script is script`; `run.clock` is a `StepClock`) |
| A-1c | Today's callers keep their behaviour | Defaults equal today's values; `browser_journey` delegates to the same composer | `test_browser_journey_factory_defaults_match_browser_journey`; C-4 runs `j1/test_aea_58.py` and `j9/test_aea_58.py` unchanged; mypy covers `serve.py` |
| A-1d | Fixture `browser_journey_factory(request, journey_chrome, production_build, tmp_path) -> Callable[..., AbstractContextManager[BrowserRun]]`; `open_run(*, index_dir=None, with_clock=False, script=None, overrides_for=None)` composes as `browser_journey` (same collector, strict flag, screenshots folder, `BrowserRun` fields, `close()` in `finally`), passing `environ_overrides={"MERIDIAN_INDEX_DIR": str(index_dir)}` when `index_dir` is given | Step 2 | `test_browser_journey_factory_run_options` (`run.settings.index_dir == idx`, `brun.build is` the fixture's build, `brun.test_name` is the test's name, `brun.pages == []`); `test_index_dir_env_is_the_settings_name` |
| A-2a | Every §4.3 key not already in `SELECTOR_KEYS` is added with its state description | Step 3.1 (46 keys; total 62) | `test_selector_keys_cover_aea62`; C-2 (Step 0 check) |
| A-2b | A contract row for a parametric key holds one `{value}` placeholder (keys `card.slot.window_by_id`, `queue.row_by_ref`, `brief.section_by_number`, `case.source_by_id`) | `PARAMETRIC_KEYS`, `fill_row` | `test_contract_rows_parametric_placeholders` (on the real rows); `test_locate_by_refuses_misuse` (a row with 0 or 2 placeholders) |
| A-2c | `locate_by(target: Page \| Locator, key: str, value: str) -> Locator`: same css / role / label dispatch as `locate`, placeholder filled | `_build` shared by all three | `test_locate_by_fills_one_placeholder` (css, role-with-name, label rows on a recording stand-in) |
| A-2d | Rows stay empty until `selectors.md` gives them; those steps report `blocked-on UX session` | `CONTRACT_ROWS` untouched | `test_selector_keys_cover_aea62` (`missing_selectors` over the 46 keys returns one `UX session` entry each, no `KeyError`); existing `test_selector_rows_cite_contract` |
| PA-1 | (plan-added) a `locate_by` value outside `^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$` raises `ValueError` | `PARAM_VALUE` in `fill_row` | `test_locate_by_refuses_misuse` |
| PA-2 | (plan-added) `locate`/`locate_in` on a parametric key, or `locate_by` on a plain key, raise `ValueError`; an unknown key raises `KeyError` | `_row` | `test_locate_by_refuses_misuse` |
| A-3 | `BrowserRun.screenshot_element(bp: BrowserPage, target: Locator, label: str) -> Path`: same label rule (`^[a-z0-9-]{1,40}$`), path `<shots_dir>/<test_name>-<device>-<label>.png`, appended to `session.screenshots`, using `target.screenshot(path=str(path))` | Step 4 | `test_screenshot_element_shoots_only_the_target` |
| R-1 README | *Adding a browser journey later* names the factory, its options, `locate_by` and `screenshot_element` | Step 5 | C-7 (text present); `test_no_held_out_paths_in_browser_files` still passes on the README |
| Step 0 | AEA-62 §5 Step 0.2 grep finds all four names and `SELECTOR_KEYS` lists every §4.3 key | Steps 1–4 | C-2 |
| No selector strings | `locator(` / `get_by_` appear only in `selectors.py` (and in `test_browser_support.py`, which the scan skips) | Step 3/4/6 | existing `test_no_selector_strings_outside_module`; C-6 |

**WP-N worked pair:** none applies. This is harness code; it runs no scripted conversation of its own. AEA-62 carries
the WP-1…WP-8 legs that use it.

**The single `[journey]` criterion (level `integrated with a scripted model`):** AEA-58's existing `[journey]` test
`tests/journeys/j1/test_aea_58.py::test_j1_login_turn_refresh_resume` (both widths) still passes or reports
`blocked-on <owner>` (on `main` `8785135` expect `blocked-on UX session`, since `CONTRACT_ROWS` is empty) after
`browser_journey` is re-routed through `_browser_run`. Run in C-4 against the production build.

---

## 4. Shared code to use (copied from `main` `8785135`; do not paraphrase)

### 4.1 AEA-57 harness (`tests/journeys/support/`, import only)

```python
# tests/journeys/support/server.py
class StepClock:                      # callable: () -> datetime (real UTC + offset); .advance(seconds); .offset_s
def launch_server(settings: Settings, *, overrides: ContainerOverrides | None, startup_timeout_s: float = 30.0)  # @contextmanager -> RunningServer
def socket_guard() -> Iterator[SocketGuard]                                                                    # @contextmanager

# tests/journeys/support/scripted_model.py
class JourneyScript:                  # JourneyScript() — per-role queues; AEA-51's StepScript subclasses it
class ScriptedModel: ...
def scripted_overrides(
    settings: Settings, script: JourneyScript, *, wall_clock: Callable[[], datetime] | None
) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]: ...

# tests/journeys/support/run.py
@dataclass
class JourneyRun:
    env: JourneyEnv; server: RunningServer; script: JourneyScript; models: Mapping[Role, ScriptedModel]
    clock: StepClock | None; db: DbReader; logs: LogTap; guard: SocketGuard; collector: StepCollector
    strict: bool; nodeid: str; clients: list[JourneyClient] = field(default_factory=list)
    # .settings -> self.env.settings ; .container ; .app ; .base_url

# tests/journeys/support/steps.py
@dataclass
class StepCollector:   # StepCollector(); .notes: list[RunNote]
# tests/journeys/support/plugin.py
COLLECTOR_KEY = pytest.StashKey["StepCollector"]()     # options --journeys-strict, --journey-record
```

### 4.2 Production names (import only)

```python
from meridian.config import ENV_NAMES, Settings      # ENV_NAMES["index_dir"] == "MERIDIAN_INDEX_DIR"; Settings.index_dir: Path
from meridian.domain.common import Role
from meridian.web.app import ContainerOverrides
# @dataclass ContainerOverrides(choice=None, structured=None, tools=None, trace=None,
#                               wall_clock: Callable[[], datetime] | None = None)   (web.md §15, D-13)
```

### 4.3 AEA-58 browser package (current code; what stays)

```python
# server.py today
def browser_environ(root: Path, dist_dir: Path) -> dict[str, str]
@contextmanager
def open_browser_journey(*, collector: StepCollector, strict: bool, nodeid: str, build: ProductionBuild,
                         environ_overrides: dict[str, str] | None = None) -> Iterator[JourneyRun]
#   body: socket_guard, tap_logs, journey_environment → browser_environ(base.root, build.dist_dir) →
#   environ.update(environ_overrides or {}) → Settings.from_env(environ) → dataclasses.replace(base, settings=settings,
#   web_dist_dir=build.dist_dir) → script = JourneyScript() → scripted_overrides(settings, script, wall_clock=None) →
#   launch_server → JourneyRun(clock=None, ...) → yield → close_clients → spend RunNote → socket-guard assertion

# pages.py
LABEL = re.compile(r"^[a-z0-9-]{1,40}$")
@dataclass class BrowserPage(device: Device, context: BrowserContext, page: Page, net: NetworkLog)
@dataclass class BrowserRun(run, browser, channel: str, build: ProductionBuild, shots_dir: Path,
                            session: BrowserSession, test_name: str, pages: list[BrowserPage] = [])
#   .open(device) -> BrowserPage ; .screenshot(bp, label) -> Path ; .close()

# selectors.py
@dataclass(frozen=True) class SelectorRow(key: str, kind: SelectorKind, value: str, name: str | None, row: str)
SelectorKind = Literal["css", "role", "label"]
SELECTOR_KEYS: Mapping[str, str]       # 16 keys today
CONTRACT_ROWS: Mapping[str, SelectorRow] = MappingProxyType({})
def missing_selectors(keys: Sequence[str]) -> tuple[Missing, ...]   # KeyError on a key not in SELECTOR_KEYS
def locate(page: Page, key: str) -> Locator
def locate_in(parent: Locator, key: str) -> Locator

# record.py
@dataclass class BrowserSession(build=None, channel=None, chrome_version=None, devices=set(), screenshots=[], ...)
# build.py
@dataclass class ProductionBuild(dist_dir: Path, index_sha256: str, check_line: str)
```

`serve.py` calls `open_browser_journey(collector=StepCollector(), strict=False, nodeid="serve", build=build,
environ_overrides={...})` and then `run.script.add(...)`: it must keep working unchanged (defaults give a fresh
`JourneyScript`).

---

## 5. Steps

Dependency direction stays: `plugin.py` → `server.py`, `pages.py` → AEA-57 `support/` → `meridian`. `selectors.py` →
`support/steps.py` only. No new module; no import of AEA-51 code anywhere in `browser/` (AEA-58 stays independent of
AEA-51: it accepts a script and a builder).

### Step 0 — environment (no code)

1. `export UV_LINK_MODE=hardlink`; `df -h /home` (stop and report under 5 GB free).
2. In the worktree: `uv sync` only if `.venv` is missing (hardlink mode; never copy a venv). No `node_modules`.
3. The production build is in the primary checkout (`/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist/index.html`
   exists on `8785135`). `export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist`.
   Only if `index.html` is missing: `npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist`,
   then `git -C /home/linuxuser/workspaces/inno-aea-callcenter status --porcelain apps/web` must print nothing.

### Step 1 — `server.py` (A-1)

1. Imports become (keep existing ones, add the new names):
   ```python
   import dataclasses
   from collections.abc import Callable, Iterator, Mapping
   from contextlib import contextmanager
   from datetime import datetime
   from pathlib import Path
   from typing import Final

   from meridian.config import ENV_NAMES, Settings
   from meridian.domain.common import Role
   from meridian.web.app import ContainerOverrides
   from tests.journeys.browser.build import ProductionBuild
   from tests.journeys.support.db import DbReader
   from tests.journeys.support.env import journey_environ, journey_environment
   from tests.journeys.support.logtap import tap_logs
   from tests.journeys.support.run import JourneyRun
   from tests.journeys.support.scripted_model import JourneyScript, ScriptedModel, scripted_overrides
   from tests.journeys.support.server import StepClock, launch_server, socket_guard
   from tests.journeys.support.steps import RunNote, StepCollector
   ```
   These are runtime imports (the alias below is evaluated at import time); `meridian.web.app` is already imported at
   runtime by `scripted_model.py`, so nothing new loads.
2. Module constants and the builder, after the imports:
   ```python
   INDEX_DIR_ENV: Final = ENV_NAMES["index_dir"]  # "MERIDIAN_INDEX_DIR" (src/meridian/config.py)

   OverridesFor = Callable[
       [Settings, JourneyScript, Callable[[], datetime] | None],
       tuple[ContainerOverrides, Mapping[Role, ScriptedModel]],
   ]


   def _default_overrides(
       settings: Settings, script: JourneyScript, clock: Callable[[], datetime] | None
   ) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]:
       """AEA-57's scripted_overrides: the default when a run passes no builder."""
       return scripted_overrides(settings, script, wall_clock=clock)
   ```
   Plain assignment for the alias (the repo style: `ScriptEntry = ...` in `scripted_model.py`; ruff `UP040` is ignored).
3. `open_browser_journey` signature becomes:
   ```python
   @contextmanager
   def open_browser_journey(
       *,
       collector: StepCollector,
       strict: bool,
       nodeid: str,
       build: ProductionBuild,
       environ_overrides: dict[str, str] | None = None,
       script: JourneyScript | None = None,
       with_clock: bool = False,
       overrides_for: OverridesFor | None = None,
   ) -> Iterator[JourneyRun]:
   ```
   Docstring: `"""Mirrors AEA-57's open_journey; differs in the settings (the build). Run options (AEA-58-F1): a
   caller's script, the run clock, a caller's override builder."""`
   Body changes, and only these: replace `script = JourneyScript()` and the `scripted_overrides(...)` line with
   ```python
           script = script if script is not None else JourneyScript()
           clock = StepClock() if with_clock else None
           overrides, models = (overrides_for or _default_overrides)(settings, script, clock)
   ```
   and pass `clock=clock` (not `clock=None`) to `JourneyRun`. Everything else (socket guard, log tap, env update order,
   `RunNote`, the guard assertion) stays byte-for-byte. Invariant protected: with no new arguments the run is the same
   as today's (fresh `JourneyScript`, no clock, AEA-57's models).
4. Do **not** use `script or JourneyScript()`: a script object must never be replaced because of truthiness.

### Step 2 — `plugin.py` (A-1 fixture)

1. Module-level imports stay stdlib, pytest and `TYPE_CHECKING` only. Add `from collections.abc import Callable,
   Iterator` and `from contextlib import AbstractContextManager, contextmanager`. Under `TYPE_CHECKING` add
   `from tests.journeys.browser.server import OverridesFor` and `from tests.journeys.support.scripted_model import
   JourneyScript`.
2. Move today's `browser_journey` body into a private composer (exact parameters):
   ```python
   @contextmanager
   def _browser_run(
       request: pytest.FixtureRequest,
       browser: Browser,
       build: ProductionBuild,
       tmp_path: Path,
       *,
       environ_overrides: dict[str, str] | None = None,
       script: JourneyScript | None = None,
       with_clock: bool = False,
       overrides_for: OverridesFor | None = None,
   ) -> Iterator[BrowserRun]:
       """One composition for both browser fixtures: collector, strict flag, screenshots folder, BrowserRun, close()."""
   ```
   The body is today's `browser_journey` body verbatim (same lazy imports, `collector`, `strict`, `session`, `scope`,
   `shots`), with `journey_chrome` → `browser`, `production_build` → `build`, and the `open_browser_journey(...)` call
   gaining `environ_overrides=environ_overrides, script=script, with_clock=with_clock, overrides_for=overrides_for`.
   `brun.close()` stays in `finally`.
3. `browser_journey` keeps its signature and becomes:
   ```python
   @pytest.fixture
   def browser_journey(
       request: pytest.FixtureRequest, journey_chrome: Browser, production_build: ProductionBuild, tmp_path: Path
   ) -> Iterator[BrowserRun]:
       with _browser_run(request, journey_chrome, production_build, tmp_path) as brun:
           yield brun
   ```
4. New fixture, right after it:
   ```python
   @pytest.fixture
   def browser_journey_factory(
       request: pytest.FixtureRequest, journey_chrome: Browser, production_build: ProductionBuild, tmp_path: Path
   ) -> Callable[..., AbstractContextManager[BrowserRun]]:
       """Runs with options (AEA-58-F1 A-1): `with browser_journey_factory(index_dir=..., with_clock=True,
       script=..., overrides_for=...) as brun:`. Each call opens one run; close it with the `with` block."""

       def open_run(
           *,
           index_dir: Path | None = None,
           with_clock: bool = False,
           script: JourneyScript | None = None,
           overrides_for: OverridesFor | None = None,
       ) -> AbstractContextManager[BrowserRun]:
           from tests.journeys.browser.server import INDEX_DIR_ENV

           environ = {INDEX_DIR_ENV: str(index_dir)} if index_dir is not None else None
           return _browser_run(
               request,
               journey_chrome,
               production_build,
               tmp_path,
               environ_overrides=environ,
               script=script,
               with_clock=with_clock,
               overrides_for=overrides_for,
           )

       return open_run
   ```
5. Module docstring first line: `"""The browser fixtures (production_build, journey_chrome, browser_journey,
   browser_journey_factory) and the two session hooks (AEA-58, AEA-58-F1). Loaded with` … (rest unchanged).
   `production_build`, `journey_chrome` and both hooks are not touched.

### Step 3 — `selectors.py` (A-2)

1. Imports: add `import re` and `from dataclasses import dataclass, replace` (replace the bare `dataclass` import).
2. Append these 46 entries to `SELECTOR_KEYS`, after `"shell.sign_out"`, in this order, with these exact descriptions:
   ```python
   "screen.scr2": "SCR-2 root is drawn",
   "screen.scr4": "SCR-4 root is drawn",
   "screen.scr5": "SCR-5 root is drawn",
   "screen.scr6": "SCR-6 root is drawn",
   "login.message.expired": "SCR-12 expired-session line",
   "chat.source": "a cited source chip naming its document",
   "chat.source.toggle": "the control that opens a source chip",
   "chat.source.excerpt": "the quoted passage an open source chip shows",
   "chat.block.locate_prompt": "a locate reply block ([data-block-type])",
   "chat.block.code_prompt": "a code reply block ([data-block-type])",
   "chat.block.account_card": "an account card reply block ([data-block-type])",
   "chat.block.slot_card": "a slot card reply block ([data-block-type])",
   "chat.block.confirmation": "a confirmation reply block ([data-block-type])",
   "chat.block.handoff": "a handoff reply block ([data-block-type])",
   "card.locate.name": "locate card name input",
   "card.locate.phone": "locate card phone input",
   "card.locate.submit": "locate card submit control",
   "card.code.input": "code card input",
   "card.code.submit": "code card submit control",
   "card.slot.window_by_id": "one window in a slot card, by slot id (parametric)",
   "card.slot.continue": "slot card 'Continue with this window' control",
   "settled.visit": "'What's settled' visit row ([data-visit-status])",
   "settled.request": "'What's settled' request row ([data-request-ref])",
   "inbox.message.active": "SCR-2 newest active message ([data-inbox-status=active])",
   "inbox.code": "SCR-2 code, readable as text",
   "shell.role.customer": "'Acting as' radio: Customer",
   "shell.role.representative": "'Acting as' radio: Representative",
   "shell.role.supervisor": "'Acting as' radio: Supervisor",
   "shell.role.owner": "'Acting as' radio: Owner",
   "shell.header_name": "the shell's signed-in display name",
   "role.panel": "SCR-4 / staff role panel ([data-testid=role-panel])",
   "role.panel.wrong_role": "role panel with reason wrong_role ([data-reason])",
   "role.panel.role_reset": "role panel with reason role_reset ([data-reason])",
   "queue.row": "every SCR-5 queue row, in order",
   "queue.row_by_ref": "the SCR-5 queue row of one case reference (parametric)",
   "case.root": "SCR-6 case loaded ([data-testid=case])",
   "case.owner": "SCR-6 owner line (case-owner)",
   "case.promise": "SCR-6 promise card ([data-promise-status])",
   "case.promise.open": "SCR-6 promise card with status open",
   "brief.section_by_number": "brief section #brief-<n> (parametric)",
   "brief.heading": "a brief section's heading",
   "brief.item.tag": "the 'Customer says · not checked' tag on a brief item",
   "case.sources_tab": "SCR-6 Sources tab",
   "case.source_by_id": "SCR-6 source #src-<source_id> (parametric)",
   "demo.reset": "SCR-3 reset control",
   "demo.reset_result": "SCR-3 reset result ([data-reset-result])",
   ```
   Total keys: 62. These are logical keys and descriptions only; **no row is added to `CONTRACT_ROWS`**.
3. After `UX_OWNER`, add:
   ```python
   PLACEHOLDER: Final = "{value}"
   PARAMETRIC_KEYS: frozenset[str] = frozenset(
       {"card.slot.window_by_id", "queue.row_by_ref", "brief.section_by_number", "case.source_by_id"}
   )
   PARAM_VALUE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")  # ids, references, section numbers
   ```
4. `missing_selectors` stays exactly as it is.
5. Replace `locate` and `locate_in` with the shared form below (same public signatures; behaviour for plain keys
   unchanged — the same `CONTRACT_ROWS[key]` `KeyError` for a known key without a row):
   ```python
   def placeholder_count(row: SelectorRow) -> int:
       return row.value.count(PLACEHOLDER) + (row.name or "").count(PLACEHOLDER)


   def fill_row(row: SelectorRow, value: str) -> SelectorRow:
       """A parametric row with its one {value} placeholder filled (in `value`, or in `name` for a role row)."""
       if not PARAM_VALUE.fullmatch(value):
           raise ValueError(f"bad selector value {value!r}: expected {PARAM_VALUE.pattern}")
       if placeholder_count(row) != 1:
           raise ValueError(f"row for {row.key!r} must hold exactly one {PLACEHOLDER}")
       name = None if row.name is None else row.name.replace(PLACEHOLDER, value)
       return replace(row, value=row.value.replace(PLACEHOLDER, value), name=name)


   def _row(key: str, *, parametric: bool) -> SelectorRow:
       if key not in SELECTOR_KEYS:
           raise KeyError(f"unknown selector key {key!r}: add it to SELECTOR_KEYS")
       if key in PARAMETRIC_KEYS and not parametric:
           raise ValueError(f"{key!r} is parametric: use locate_by")
       if parametric and key not in PARAMETRIC_KEYS:
           raise ValueError(f"{key!r} takes no value: use locate or locate_in")
       return CONTRACT_ROWS[key]


   def _build(target: Page | Locator, row: SelectorRow) -> Locator:
       if row.kind == "css":
           return target.locator(row.value)
       if row.kind == "role":
           return target.get_by_role(row.value, name=row.name, exact=True)  # type: ignore[arg-type]
       return target.get_by_label(row.value, exact=True)


   def locate(page: Page, key: str) -> Locator:
       return _build(page, _row(key, parametric=False))


   def locate_in(parent: Locator, key: str) -> Locator:
       return _build(parent, _row(key, parametric=False))


   def locate_by(target: Page | Locator, key: str, value: str) -> Locator:
       """A parametric key (PARAMETRIC_KEYS) with its value filled (AEA-58-F1 A-2)."""
       return _build(target, fill_row(_row(key, parametric=True), value))
   ```
   Invariant: `_row` reads the module global `CONTRACT_ROWS` at call time (never bind it as a default argument), so
   the self-checks can substitute rows with `monkeypatch.setattr`. If mypy reports the `type: ignore[arg-type]` as
   unused, or reports a different code on the union, use the code mypy names; do not widen to a bare `type: ignore`.
6. Module docstring: append one paragraph: `Parametric keys (PARAMETRIC_KEYS, AEA-58-F1): the row holds exactly one
   {value} placeholder (in value, or in name for a role row); tests reach it only through locate_by, which fills it
   with an id, reference or number matching PARAM_VALUE.`

### Step 4 — `pages.py` (A-3)

1. Under `TYPE_CHECKING`: `from playwright.sync_api import Browser, BrowserContext, Locator, Page`.
2. In `BrowserRun`, add the helper and rewrite `screenshot` through it; add `screenshot_element`:
   ```python
   def _shot_path(self, bp: BrowserPage, label: str) -> Path:
       if not LABEL.fullmatch(label):
           raise ValueError(f"bad screenshot label: {label!r}")
       self.shots_dir.mkdir(parents=True, exist_ok=True)
       return self.shots_dir / f"{self.test_name}-{bp.device.name}-{label}.png"

   def screenshot(self, bp: BrowserPage, label: str) -> Path:
       path = self._shot_path(bp, label)
       bp.page.screenshot(path=str(path), full_page=False)
       self.session.screenshots.append(path)
       return path

   def screenshot_element(self, bp: BrowserPage, target: Locator, label: str) -> Path:
       """Only the element (AEA-58-F1 A-3): a card shown next to identity values is shot alone."""
       path = self._shot_path(bp, label)
       target.screenshot(path=str(path))
       self.session.screenshots.append(path)
       return path
   ```
   Order of effects is the same as today's `screenshot`: label check first (nothing created on a bad label), then the
   folder, then the shot, then the bookkeeping. Do not write the text `locator(` anywhere in this file.
3. Module docstring: `"""Devices, pages and the run object (AEA-58): contexts, screenshots (page and element,
   AEA-58-F1), teardown validation (AC-7, PA-1)."""`

### Step 5 — `README.md`

1. Replace the whole *Adding a browser journey later* section body with:

   > One file `tests/journeys/j<N>/test_aea_<NN>.py` with `pytest_plugins = ("tests.journeys.browser.plugin",)`,
   > `browser_step(...)` for every step, and selectors only by key from `selectors.py`: `locate(page, key)`,
   > `locate_in(parent, key)`, and `locate_by(target, key, value)` for a parametric key such as `queue.row_by_ref`.
   >
   > Use the `browser_journey` fixture for a run with an empty script and no clock. Use `browser_journey_factory` when
   > the run needs options:
   >
   > ```python
   > with browser_journey_factory(index_dir=idx, with_clock=True, script=my_script, overrides_for=my_builder) as brun:
   >     bp = brun.open(DESKTOP)
   > ```
   >
   > `index_dir` reaches the app as `MERIDIAN_INDEX_DIR`; `with_clock=True` gives `brun.run.clock`, a `StepClock` the
   > test moves forward; `overrides_for(settings, script, clock)` builds the scripted models (default: AEA-57's
   > `scripted_overrides`). Every option is optional. `brun.screenshot_element(bp, target, label)` shoots one element
   > only, for a card shown next to identity values.
   >
   > A missing helper is a follow-up on AEA-58, merged first. A test file never calls `locator(` or `get_by_` itself.

   (Write it as plain Markdown, not as a quote block.)
2. In *Selectors*, append one sentence to the paragraph: `A parametric key (PARAMETRIC_KEYS) gets a row whose value
   (or, for a role row, name) holds exactly one {value} placeholder; tests reach it only through locate_by.` (with the
   names in backticks).

### Step 6 — `test_browser_support.py` (self-checks; no Chrome page opened, no npm)

1. New imports (merge into the existing blocks; keep ruff's isort order):
   `from collections.abc import Callable`, `from datetime import datetime`, `from types import MappingProxyType`,
   `from tests.journeys.browser import selectors as selectors_module`,
   `from tests.journeys.browser.pages import DESKTOP, BrowserPage, BrowserRun`,
   `from tests.journeys.browser.selectors import PARAMETRIC_KEYS, PLACEHOLDER, SelectorRow, fill_row, locate, locate_by, locate_in, placeholder_count`
   (merge with the existing `selectors` import), `from tests.journeys.browser.server import INDEX_DIR_ENV` (merge with
   `browser_environ`), `from tests.journeys.support.scripted_model import JourneyScript, scripted_overrides`,
   `from tests.journeys.support.server import StepClock` (merge with `launch_server`). Never import
   `tests.journeys.browser.plugin` (AEA-58's loading rule).
2. Module constant: `AEA62_KEYS: tuple[str, ...]` = the 46 keys of Step 3.2 in the same order (copy them).
3. Module-level fixture overrides (they shadow the plugin's fixtures for this module only; no existing test here
   requests them):
   ```python
   @pytest.fixture
   def production_build(tmp_path: Path) -> ProductionBuild:
       """Stand-in for the plugin's fixture in this module: a dist with only index.html (no npm, no Chrome)."""
       dist = tmp_path / "dist"
       dist.mkdir()
       (dist / "index.html").write_text("<!doctype html><title>self-check</title>", encoding="utf-8")
       return ProductionBuild(dist, "0" * 64, "self-check stand-in")


   @pytest.fixture
   def journey_chrome() -> Any:
       """Stand-in for the plugin's fixture in this module: no browser starts; these runs open no page."""
       return cast(Any, object())
   ```
4. A recording stand-in for a Playwright target (allowed here: this file is skipped by the selector-string scan):
   ```python
   class _Target:
       def locator(self, selector: str) -> tuple[str, ...]:
           return ("css", selector)

       def get_by_role(self, role: str, *, name: str | None, exact: bool) -> tuple[str, ...]:
           return ("role", role, str(name), str(exact))

       def get_by_label(self, text: str, *, exact: bool) -> tuple[str, ...]:
           return ("label", text, str(exact))
   ```
   Results of `locate*` on it are held as `got: Any = ...` (mypy `strict_equality` would reject comparing a `Locator`
   with a tuple).
5. The eight tests (names exact):
   1. `test_selector_keys_cover_aea62()`: `len(AEA62_KEYS) == 46` and `len(set(AEA62_KEYS)) == 46`; every key in
      `SELECTOR_KEYS` with a non-empty description; `len(SELECTOR_KEYS) == 62`; `PARAMETRIC_KEYS == {"card.slot.window_by_id",
      "queue.row_by_ref", "brief.section_by_number", "case.source_by_id"}` and `PARAMETRIC_KEYS <= set(SELECTOR_KEYS)`;
      `found = missing_selectors(AEA62_KEYS)` (no `KeyError`); when none of `AEA62_KEYS` is in `CONTRACT_ROWS` (true on
      `main`), `len(found) == 46` and every `m.owner == "UX session"`.
   2. `test_locate_by_fills_one_placeholder(monkeypatch)`: `monkeypatch.setattr(selectors_module, "CONTRACT_ROWS",
      MappingProxyType({...}))` with three rows:
      `SelectorRow("queue.row_by_ref", "css", '[data-case-ref="{value}"]', None, "self-check")`,
      `SelectorRow("case.source_by_id", "role", "link", "{value}", "self-check")`,
      `SelectorRow("brief.section_by_number", "label", "Brief section {value}", None, "self-check")`,
      plus a plain row `SelectorRow("case.root", "css", "[data-testid=case]", None, "self-check")`. Assert, on `t = _Target()`:
      `locate_by(cast(Any, t), "queue.row_by_ref", "MHC-C-0009") == ("css", '[data-case-ref="MHC-C-0009"]')`;
      `locate_by(cast(Any, t), "case.source_by_id", "src-12") == ("role", "link", "src-12", "True")`;
      `locate_by(cast(Any, t), "brief.section_by_number", "4") == ("label", "Brief section 4", "True")`;
      `locate(cast(Any, t), "case.root") == ("css", "[data-testid=case]")` and the same through `locate_in`
      (plain-key dispatch unchanged). Also `fill_row(row, "56")` on the css row returns a new row with `PLACEHOLDER`
      gone and the original row unchanged (frozen).
   3. `test_locate_by_refuses_misuse(monkeypatch)`: same substituted rows plus
      `SelectorRow("card.slot.window_by_id", "css", "[data-a='{value}'][data-b='{value}']", None, "self-check")`
      (two placeholders). With `pytest.raises(ValueError)`: `locate(cast(Any, t), "queue.row_by_ref")` (parametric
      without a value); `locate_by(cast(Any, t), "case.root", "x")` (plain key with a value);
      `locate_by(..., "queue.row_by_ref", 'a"b')`, `(..., "")`, `(..., "a b")`, `(..., "x" * 65)` (bad values);
      `locate_by(..., "card.slot.window_by_id", "56")` (two placeholders); `fill_row(SelectorRow("queue.row_by_ref",
      "css", "[data-case-ref]", None, "self-check"), "1")` (no placeholder). With `pytest.raises(KeyError)`:
      `locate_by(cast(Any, t), "no.such.key", "1")`.
   4. `test_contract_rows_parametric_placeholders()`: on the real `CONTRACT_ROWS`: for every row,
      `placeholder_count(row) == (1 if key in PARAMETRIC_KEYS else 0)` (import `placeholder_count` too). Passes vacuously
      on `main` (no rows yet); it guards the day `selectors.md` rows are transcribed.
   5. `test_screenshot_element_shoots_only_the_target(tmp_path)`: a stand-in target
      `class _Shot: paths: list[str]; def screenshot(self, *, path: str) -> None: self.paths.append(path); Path(path).write_bytes(b"png")`.
      `brun = BrowserRun(run=cast(Any, None), browser=cast(Any, None), channel="chrome", build=cast(Any, None),
      shots_dir=tmp_path / "shots", session=BrowserSession(), test_name="t")`;
      `bp = BrowserPage(DESKTOP, cast(Any, None), cast(Any, None), cast(Any, None))`.
      `path = brun.screenshot_element(bp, cast(Any, shot), "account-card")` →
      `path == tmp_path / "shots" / "t-chrome-desktop-account-card.png"`, `shot.paths == [str(path)]`, `path.is_file()`,
      `brun.session.screenshots == [path]`. Then `pytest.raises(ValueError)` for label `"Account Card"`, and afterwards
      `shot.paths` and `brun.session.screenshots` still have one entry each.
   6. `test_browser_journey_factory_run_options(request, browser_journey_factory, production_build, tmp_path)`:
      `idx = tmp_path / "idx"; idx.mkdir()`; `script = JourneyScript()`; `seen: list[tuple[Any, ...]] = []`;
      ```python
      def builder(settings: Settings, sc: JourneyScript, clock: Callable[[], datetime] | None) -> Any:
          seen.append((settings, sc, clock))
          return scripted_overrides(settings, sc, wall_clock=clock)
      ```
      `with browser_journey_factory(index_dir=idx, with_clock=True, script=script, overrides_for=builder) as brun:` assert
      `brun.run.script is script`; `isinstance(brun.run.clock, StepClock)`; `len(seen) == 1`;
      `seen[0][0] is brun.run.settings`, `seen[0][1] is script`, `seen[0][2] is brun.run.clock`;
      `brun.run.settings.index_dir == idx`; `brun.run.settings.require_frontend is True`;
      `brun.run.settings.web_dist_dir == production_build.dist_dir`; `brun.build is production_build`;
      `brun.pages == []`; `brun.test_name == "test_browser_journey_factory_run_options"`;
      `brun.shots_dir == tmp_path / "shots"` when `--journey-record` is not given (guard with
      `if not request.config.getoption("--journey-record")`; `request` is `pytest.FixtureRequest`).
   7. `test_browser_journey_factory_defaults_match_browser_journey(browser_journey_factory, tmp_path)`:
      `with browser_journey_factory() as brun:` `type(brun.run.script) is JourneyScript`; `brun.run.clock is None`;
      `brun.run.settings.index_dir != tmp_path / "idx"`; `brun.run.models` is non-empty. (Same composition path as the
      `browser_journey` fixture, which AEA-58's own journeys exercise in C-4.)
   8. `test_index_dir_env_is_the_settings_name(tmp_path)`: `INDEX_DIR_ENV == "MERIDIAN_INDEX_DIR"`; with
      `journey_environment() as base`: `environ = browser_environ(base.root, tmp_path / "dist")`,
      `environ[INDEX_DIR_ENV] = str(tmp_path / "idx")`, `Settings.from_env(environ).index_dir == tmp_path / "idx"`.
6. Existing tests stay unchanged. `test_no_held_out_paths_in_browser_files` forbids the strings `"held"+"out"` and
   `"key"+"_dir"` in every `browser/*.py` and `*.md`: do not write them (note `index_dir` is fine).

### Step 7 — run, then commit

1. Iterate with C-1, then C-2.
2. Before the commit, cheapest first: C-3, then C-4, C-5, C-6, C-7. Fix anything red in owned files only.
3. One commit:
   `git add tests/journeys/browser/server.py tests/journeys/browser/plugin.py tests/journeys/browser/selectors.py tests/journeys/browser/pages.py tests/journeys/browser/test_browser_support.py tests/journeys/browser/README.md`
   Message: `test(AEA-58-F1): browser run options, parametric selectors, element screenshots` + a body listing A-1, A-2
   (46 keys, rows still empty: steps report blocked-on UX session), A-3, the C-4 result line, + last line
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No push (only the merge step pushes `main`).

### What the implementer must NOT do

- Edit any file outside §2's owned list (`serve.py`, `steps.py`, `support/**`, `j*/test_aea_58.py`, `conftest.py`,
  `src/**`, `apps/web/**`, `docs/ux/**`, `docs/plans/ux-join/**`, the OpenAPI, `UI_CONTRACTS.md`, context rows).
- Add any row to `CONTRACT_ROWS`, set `SELECTORS_REVISION`, invent a selector value, or read `apps/web/src` to find one.
- Import anything from `tests/integration/` (AEA-51) into `browser/`; import `tests.journeys.browser.plugin` from a test.
- Write `locator(` or `get_by_` in any `.py` under `tests/journeys/` except `selectors.py` and `test_browser_support.py`.
- Change `production_build`, `journey_chrome`, the session hooks, or the order of effects in `open_browser_journey`.
- Run `playwright install`, add `node_modules` to the worktree, build `apps/web` inside a test, bind 4019 or 5184,
  call a paid model, read `.env`, `git add -A`, push, force-push, or run pytest with more than `-n 2`.

---

## 6. Data and fixtures

Synthetic only. The stand-in dist is one generated `index.html` (`<!doctype html><title>self-check</title>`) in
`tmp_path`. Selector values in the self-checks are synthetic ids in the app's formats: `"MHC-C-0009"` (case reference
form, `services/cases.py`), `"src-12"` (source id form, `services/_case_views.py` `f"src-{r.id}"`), `"56"`, `"4"`. The
demo pair and session secret come from AEA-57's `journey_environ` (random per run; never printed). The DB is AEA-57's
per-run copy. No customer identity, verification code, card-like number or phone number appears.

---

## 7. Checks

All from the worktree root with `export UV_LINK_MODE=hardlink` and
`export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist`.

| # | When | Command | Passing looks like |
|---|---|---|---|
| C-1 | while iterating | `uv run pytest tests/journeys/browser/test_browser_support.py -q -rs` | all pass (the two factory tests start a real server on a stand-in dist; no Chrome page) |
| C-2 | acceptance (AEA-62 §5 Step 0.2) | `grep -n "def browser_journey_factory\|def locate_by\|def screenshot_element\|overrides_for" tests/journeys/browser/*.py` and `uv run python -c "from tests.journeys.browser.selectors import SELECTOR_KEYS; print(sorted(SELECTOR_KEYS))"` | grep finds all four names (`plugin.py`, `selectors.py`, `pages.py`, `server.py`); the print lists 62 keys including every key of AEA-62 §4.3 |
| C-3 | before the commit (fast gates, cheapest first) | `uv run ruff format --check tests/journeys/browser && uv run ruff check tests/journeys/browser && uv run mypy` | clean |
| C-4 | before the commit (affected tests + affected journeys) | `perl -e 'alarm 900; exec @ARGV' uv run python -m tests.journeys.affected --base main -- --browser-channel chrome -rs` (`tests/journeys/` is in `ALWAYS_PREFIXES`, so every journey is selected, including `browser/test_browser_support.py`, `j1/test_aea_58.py`, `j9/test_aea_58.py`) | 0 failed, 0 errors; skips only with `blocked-on <owner>`; `test_j1_login_turn_refresh_resume` passes or reports `blocked-on UX session` |
| C-5 | before the commit | `uv run pytest -m journey --collect-only -q` | collects with no error (the plugin's new fixture loads in every browser module) |
| C-6 | before the commit | `grep -rnE "locator\(\|get_by_" tests/journeys --include=*.py \| grep -v -e tests/journeys/browser/selectors.py -e tests/journeys/browser/test_browser_support.py` | prints nothing |
| C-7 | before the commit | `git diff --name-only main...HEAD` (after the commit) or `git status --porcelain` (before) | only the six owned files |

**If C-4 shows a red** in a file that does not import `tests.journeys.browser` (e.g. a j-file needing a cached
embedding model), run that file alone on `main` in the primary checkout's state; if it is red there too, it is not this
slice's: report it with the failing line and do not fix it. A red in `test_browser_support.py`, `j1/test_aea_58.py` or
`j9/test_aea_58.py` is this slice's.

**Full suite:** not required. No `conftest.py`, settings, dependency or lockfile change; `plugin.py` loads only in
browser test modules. The merge agent runs the affected set (C-4's command).

**Tests the implementer writes:** the eight self-checks of Step 6.5. **Existing tests that must stay green:** every
other test in `test_browser_support.py`, `j1/test_aea_58.py`, `j9/test_aea_58.py`, and every journey C-4 selects.

---

## 8. Risks and requests

- **R-1 fixture override in the self-check module.** `test_browser_support.py` defines `production_build` and
  `journey_chrome` to shadow the plugin's for this module only. No existing test in the module requests them (checked on
  `8785135`). If a later ticket adds a real-Chrome test to this module, it must move to its own file. Recorded in the
  fixtures' docstrings.
- **R-2 placeholder in `name` (decided here).** R-1 says the placeholder is in `value`; the plan also allows it in
  `name` for a `role` row, exactly one in total. Reason: a contract row like `role=row name={value}` is the natural shape
  for `queue.row_by_ref`. This is a superset; every R-1-shaped row still works.
- **R-3 value pattern (decided here).** `PARAM_VALUE` rejects quotes, spaces and brackets so a value cannot change a
  selector's meaning. AEA-62's values (`"56"`, `"58"`, `"4"`, case references, `src-<n>`) all match. A future id with
  another character is a one-line change to the pattern in this module.
- **R-4 shared context rows.** None changed here. AEA-62 R-6 says AEA-58-F1 "may" touch area-map row `3+`; it does not
  need to (no file, owner or route moves), so there is no collision with AEA-61/AEA-55/AEA-62 on those rows.
- **R-5 run time.** C-4 selects every journey (all ten j-folders). The alarm is 900 s; report the measured time.
- **Collisions:** none. No other open branch edits `tests/journeys/browser/`. AEA-62 consumes these names next; its plan
  §4.2/§4.3 already matches the signatures above.

---

## 9. Readiness

**READY.** No product decision, no signed-contract change, no missing prerequisite. Gates: none (no human, paid or live
gate).

## Deviations

- `test_browser_support.py` is 535 lines after `ruff format` (plan target 450, hard cap 500); the 46-key tuple and eight
  tests expand under the formatter. Left as is: splitting needs a new file the plan does not own.
- C-4 had one red, `j1/test_aea_40.py::test_j1_code_turn_and_reload_through_the_real_server`: the fixed code `651964`
  (seed 4041) appeared inside a float uptime timestamp in the log tap. Not this slice (the file does not import
  `browser/`); it passed on an immediate re-run alone. A flaky digit-substring check; request for the owner of AEA-40's
  journey: assert on a delimited code, not a bare substring.
