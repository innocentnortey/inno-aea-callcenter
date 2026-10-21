# Plan — [AEA-01] foundation: scaffold, limits, composition-root stubs

**Status:** planned (READY)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/1 (spec copy:
`docs/plans/tickets/AEA-01.md`) · **Base revision:** `9c3e7e7` (main, 2026-10-21)
**Lane:** `lane::build-loop` · **Risk:** none (no `risk::security`: no frozen tests, no security agent) · **Wave:** 0
**Planner:** Opus 5.5 (`claude-opus-5-5`), 2026-10-21 · **Implementer:** `fanout-implementer` (Sonnet)

This plan is written for an implementer that has not read the design. Every name, value, path and command below is
decided. If something here turns out wrong when you run it, stop and report back. Do not improvise.

---

## 1. Goal and sources

### Goal (from the issue's *What to build*)

> The repository's Python shell, so every later ticket only adds its own modules. **`config.py` / `Settings` is not this
> ticket's**: it moved to AEA-02.

In plain words, this ticket produces six things. When it is done, a fresh checkout can run `uv sync` and every later
ticket only adds its own files:

1. **`pyproject.toml` + `uv.lock`.** Every dependency the design names, plus the lint, format, type-check and pytest
   configuration.
2. **The package skeleton.** Empty `__init__.py` markers for every package in DO-3 §3 and the test layout in DO-3 §9.
3. **`src/meridian/policy/limits.py`.** One frozen `Limits` that holds every shared number, using the standard library
   only.
4. **`src/meridian/web/container.py`.** The one composition root: a `Container`, `build_container(...)`, and 27 no-op
   `register_<area>()` hunks, one per registering ticket.
5. **`tests/conftest.py`.** Suite-wide pytest configuration. It defines no fixtures yet.
6. **The journey gate skeleton.** The `tests/journeys/` package with `j1`…`j10` markers, the registered `journey`
   marker, and the affected-journeys command `python -m tests.journeys.affected`. Today it prints
   `0 journeys affected` and exits 0.

**Concrete example (the ticket's example pair).** Later, the gateway (AEA-20) reads `limits.brakes.sonnet_calls` and
gets `6`. The ledger (AEA-26) is built with `daily_cap_usd=limits.spend.daily_cap_usd` and gets `30.0`. The rate
limiter (AEA-23) reads `limits.web.chat_turns_per_thread_per_min` and gets `20`. All three read the **same** `Limits`
object that `build_container` made, and no consumer holds a second literal (merge-clashes MC-22). The test
`tests/unit/web/test_container.py::test_example_pair_one_limits_object` proves this.

### Sources (read by the planner; the implementer does not need to re-read them)

| Source | Section | What it fixes for this ticket |
|---|---|---|
| `docs/design/code-design.md` (DO-3) | §2.1 | One composition root `web/container.py`; builds once, injects by constructor, closes everything on shutdown; no module-level clients or settings singletons |
| DO-3 | §2.2 | LangGraph pinned to 1.2.16 |
| DO-3 | §2.3 | 60 s deadline [Decided SDQ-1], 30 in flight [Decided SDQ-9], browser waits deadline + 5 s (rule 5) |
| DO-3 | §3 | The package tree under `src/meridian/` (+ `eval/harness/`) |
| DO-3 | §4.1 row `policy/limits.py` | `TurnLimits`, `Admission`, `Brakes`, `IdentityLimits`, booking cap; "depends on: none" |
| DO-3 | §8 collision map, §9 test layout | One `register_<area>()` stub per area; `tests/{fakes,unit,contract,services,graph,api,capture,live}/` |
| `docs/design/contracts/internal-components.md` (DO-4) | §2 `TurnBudget` (`TurnLimits.deadline_s`), §12 (`RoleSpec.cap_s` is **not** in limits; `ModelGateway(…, limits: Limits)`), §14 / §2 `GraphDeps.limits: Limits` | `Limits` is passed whole to the gateway and the graph |
| `docs/design/contracts/stage7/models.md` | §6 `SpendLimits`, §7 container wiring, cross-topic 3 (`brakes.sonnet_calls = 6`) | Exact `SpendLimits` text; the container is the only builder |
| `docs/design/contracts/stage7/web.md` | §4 (providers resolve from the container on `app.state`), §5 `WebLimits`, §6 `PublicPaths` filled by hunks, §12 `register_frontend(container: Container, app: FastAPI)`, §13 dev deps `jsonschema>=4.18` + PyYAML, §15 `ContainerOverrides` pass-through (R-W-8) | Exact `WebLimits` text; hunks need `app`; the `Container` type name; `overrides` reaches only `register_graph` |
| `docs/design/contracts/stage7/graph-core.md` | §7 `ContextLimits`; §12 (Settings is AEA-02's; every numeric limit is in `Limits`) | Exact `ContextLimits` text |
| `docs/design/contracts/stage7/graph-tools.md` | §1 (tools wired in `register_graph`), §5 + C-9 (`brakes.tool_rounds`, `IdentityLimits(code_ttl_s=600, tries=3, max_sends=3)`) | Field names |
| `docs/design/contracts/stage7/data.md` | §3 (`vectors.npy` → numpy), §4 (no `register_` hunk for AEA-33) | numpy is a named dependency; AEA-33 stub stays empty |
| `docs/design/contracts/stage7/cases.md` | §6 `register_demo()`, §8 `register_ops()`; §5–§6 constructors (`CaseService(uow, clock)`, `DemoService(uow, clock, cases)`, `HandoffService(uow, cases, demo, clock, …)`) | Two hunk names; and the cross-hunk object cycle that makes lazy providers necessary (§5, step 4) |
| `docs/design/contracts/api-con-mapping.md` | §0 *Timing constants* | CON-1 `turn_deadline_ms` 60000, `still_working_after_ms` 10000, `browser_give_up_after_ms` 65000, `max_message_chars` 2000 |
| `docs/plans/7b-decisions/merge-clashes.md` | MC-21 (Settings → AEA-02), MC-22 (one frozen `Limits`, owner AEA-01) | Shape of `limits.py` |
| `docs/plans/7b-decisions/residuals-web.md` | R-W-8 | Builder takes `overrides`, hands it to `register_graph` untouched |
| `docs/plans/slice-plan.md` | §0a (journey map J-1…J-10, merge gate), §1 row AEA-01, §2 (wave 0 has no internal edges), §3 collision map | Owned files; the 25 registering tickets |
| `.claude/rules/integrated-journeys.md` | §3 rule 1, §4 (levels, record format), §5 | The record and its level `mock-tested` |
| `.claude/rules/build-loop-test-scope.md` | AEA addition | "Affected" journeys = path imports or calls a changed module, route, prompt, schema or frontend build input; when unsure, run it |
| `docs/plans/tickets/AEA-57.md` | *Agent handoff*, commands | AEA-57 needs a place to load its pytest plugin; it must not edit `tests/conftest.py`, `pyproject.toml` or this skeleton |
| `docs/plans/stage7-signoff.md` | D-2 (parked tree set aside), D-4…D-15 | Nothing in D-4…D-15 changes this ticket. D-13 (wall clock) lives in AEA-23's `ContainerOverrides`, which passes through here untouched |
| PRD `docs/prd/inno-aea-callcenter-prd.md` | R-15 (10-min expiry, 3 attempts: Decided), R-41 (abuse limits, booking cap, spend cap, brakes) | Labels on the values |

---

## 2. Boundary

### Owned files: the only files you may create or edit

**Create (new files):**

| Path | What |
|---|---|
| `pyproject.toml` | §4.1 below, exactly |
| `uv.lock` | generated by `uv lock`, never hand-edited |
| `src/meridian/__init__.py` | empty (0 bytes) |
| `src/meridian/{domain,policy,privacy,ports,gates,adapters,adapters/sqlite,adapters/models,retrieval,services,agent,agent/tools,agent/nodes,agent/specialists,agent/prompts,web,web/schemas,web/routes}/__init__.py` | 18 empty markers (0 bytes each) |
| `src/meridian/policy/limits.py` | §4.2 below |
| `src/meridian/web/container.py` | §4.3 below |
| `eval/__init__.py`, `eval/harness/__init__.py` | empty markers |
| `tests/__init__.py` | empty |
| `tests/conftest.py` | §4.4 below |
| `tests/{unit,fakes,fixtures,contract,contract/cases,services,graph,api,capture,live,integration,journeys}/__init__.py` | 12 empty markers |
| `tests/unit/{domain,policy,privacy,ports,gates,adapters,retrieval,services,agent,web}/__init__.py` | 10 empty markers (unit tests mirror `src/meridian`, DO-3 §9) |
| `tests/journeys/j1/__init__.py` … `tests/journeys/j10/__init__.py` | 10 empty markers (journey map J-1…J-10, slice plan §0a) |
| `tests/journeys/affected.py` | the affected-journeys command, §4.5 |
| `tests/journeys/README.md` | short conventions page, §5 step 9 |
| `tests/unit/test_skeleton.py` | AC-1 |
| `tests/unit/test_import_direction.py` | AC-5, AC-7 |
| `tests/unit/test_affected_journeys.py` | AC-9 selector logic |
| `tests/unit/policy/test_limits.py` | AC-3, AC-4 |
| `tests/unit/web/test_container.py` | AC-6 and the example pair |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-01.md` | AC-9 evidence record (date = the day you run it, America/Chicago) |

**Modify (existing files):**

| Path | Change |
|---|---|
| `.gitignore` | append three lines: `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` |
| `.claude/reference/area-map.md` | AC-11: preamble sentence + A0 row status (step 12) |
| `.claude/state/icm-progress.md` | AC-11: *Physical scaffold* row + *Last reconciled* line (step 12) |
| `docs/design/code-design.md` | AC-11: line 6 status sentence only (step 12) |

**Why every marker is a 0-byte file.** Wave-0 siblings (AEA-02, 03, 04, 05, 06) build in parallel and may add the same
marker, for example `tests/unit/policy/__init__.py` from AEA-03 or `src/meridian/privacy/__init__.py` from AEA-04.
Two branches that add an identical empty file merge cleanly in git. A marker with content would conflict.

### Shared surfaces: read, never edit

- `docs/design/**` except the one line in `code-design.md` named above, `docs/plans/**`, `docs/ux/**`, `apps/web/**`,
  `docs/ux/03-structure/ui-contracts.openapi.yaml`, `docs/ux/03-structure/UI_CONTRACTS.md`, the briefing,
  `docs/data/issued/**`, `docs/archive/**`.
- `docs/parked/2026-10-21-first-attempt/**`. You may read it and copy shapes from it. **Never edit, move or import it**
  (AC-10).
- `.env`, `.env.example`. Never read `.env`.

### Files other tickets own: do not create or touch

- `src/meridian/config.py`, `src/meridian/domain/*.py` (anything but `__init__.py`), `src/meridian/ports/*.py`,
  `src/meridian/adapters/sqlite/repos_*.py`: AEA-02.
- `src/meridian/policy/texts.py`: AEA-03. `src/meridian/privacy/redact.py`: AEA-04. `src/meridian/gates/rules.py`:
  AEA-05.
- `eval/cases/**`: AEA-06. `eval/harness/*.py` other than `__init__.py`: AEA-24.
- `tests/journeys/support/**`: AEA-57. `tests/journeys/browser/**`: AEA-58. `tests/fakes/*.py` other than the
  marker: AEA-11. `tests/fixtures/sqlite.py`: AEA-10. `scripts/**`, `Dockerfile`, `railway.json`: AEA-50.
- `README.md`, `SUBMISSION.md`, `.claude/README.md`, `CLAUDE.md`.

### Interfaces this slice produces (others build against them; keep the names exactly)

- `meridian.policy.limits`: `Limits`, `TurnLimits`, `Admission`, `Brakes`, `IdentityLimits`, `BookingLimits`,
  `SpendLimits`, `WebLimits`, `ContextLimits`.
- `meridian.web.container`: `Container`, `Key`, `ContainerError`, `build_container`, and the 27 `register_*` names in
  §4.3.
- `tests/journeys/affected.py`: `journey_files(root)`, `select_journeys(changed, root)`, `main(argv)`; the command
  line in §4.5.
- The `journey` and `live` pytest markers. The optional plugin module name `tests.journeys.support.plugin`, which
  AEA-57 creates and `tests/conftest.py` loads once it exists.

---

## 3. Requirements table

Every acceptance criterion of the issue (verbatim IDs), plus the obligations the sources add.

| # | Requirement (ID-cited) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 | Clean checkout installs; every DO-3 §3 package imports | Steps 1–3: `pyproject.toml`, `uv lock`, `uv sync`, the markers | `uv sync` exit 0; `uv run python -c "import meridian"` exit 0; `uv run pytest tests/unit/test_skeleton.py::test_every_planned_package_imports -s` lists 20 packages |
| AC-2 | Dependency set names every dependency of item 1; LangGraph 1.2.16; no `jinja2`, no `python-multipart` | §4.1 dependency table, copied line for line | Read back `pyproject.toml` against §4.1; `uv tree --depth 1` shows `langgraph v1.2.16`; `uv tree \| grep -iE "jinja2\|multipart"` prints nothing |
| AC-3 | `Limits` holds the decided and proposed values exactly | §4.2 | `tests/unit/policy/test_limits.py::test_values_match_their_sources` (32 parametrised cases, each with its source) |
| AC-4 | Frozen; one literal per value; `turn_deadline_ms` = deadline × 1000; no module-level numeric constant | §4.2 (properties derive the two CON-1 ms values) | `tests/unit/policy/test_limits.py::test_frozen_and_single_literal` prints the public names (classes only) |
| AC-5 | `limits.py` imports only the standard library; no role caps | §4.2 imports only `__future__` and `dataclasses` | `tests/unit/test_import_direction.py::test_limits_imports_stdlib_only` prints every import seen |
| AC-6 | Container builds and closes; every stub present exactly once, no-op, each called with the one `Limits` and the given Settings; `overrides` reaches only `register_graph` as the same object; `None` when not given | §4.3 | `tests/unit/web/test_container.py::test_every_register_stub_present`, `::test_build_and_close_without_adapters`, `::test_overrides_reach_register_graph_untouched` |
| AC-7 | Container imports no other ticket's module at run time; no module-level client or settings singleton under `src/meridian/` | §4.3: module-level imports are `__future__`, stdlib, `meridian.policy.limits`; `fastapi` only under `TYPE_CHECKING`; hunks import inside their own bodies | `tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`; reviewer grep (§7 G-9) prints nothing |
| AC-8 | Fast gates green, cheapest first | §7 | `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run pytest` (full suite: this ticket changes the dependencies, the lockfile and `conftest.py`) |
| AC-9 [journey] | Journey gate exists before any journey: marker registered; `uv run pytest -m journey --collect-only -q` exits 0; affected command selects 0, prints "0 journeys affected", exits 0; record states level `mock-tested`, *Blocked by* AEA-57 | §4.4 (exit-5 → 0 only while no journey file exists), §4.5, step 11 | Both commands' output; `docs/testing/journeys/<date>-AEA-01.md` Level and Blocked-by fields. **Level: `mock-tested`** (no server, no DB, no model) |
| AC-10 | Parked tree unchanged; nothing imports from it | Never touch `docs/parked/` | `git diff --stat main -- docs/parked/` empty; `grep -rnE "(import\|from) +.*parked" src tests` empty |
| AC-11 | Context updated in the same change | Step 12 (second commit, citing the first commit's SHA) | The diff of the three context files |
| Ex. pair | Gateway gets 6, ledger gets 30.0, limiter gets 20, all from one `Limits` | §4.3 passes the one object to every hunk | `tests/unit/web/test_container.py::test_example_pair_one_limits_object` |
| S-1 (plan-added) | Hunks must share built objects, start threads after everything is built, and close what they opened. The 29 ↔ 30 constructor chain (`DemoClock` → `CaseService` → `DemoService` → `HandoffService`, cases.md §5–§6) crosses two hunks both ways, so eager construction in hunk order cannot work | `Container.provide/get` (lazy, memoised, cycle-checked), `on_start`, `on_close`, `build`, `close` (§4.3) | `test_container.py::test_provide_get_builds_once_in_any_order`, `::test_unknown_duplicate_and_cycle_raise`, `::test_build_runs_starters_after_every_object`, `::test_close_runs_closers_once_newest_first`, `::test_failed_build_closes_what_was_opened` |
| S-2 (plan-added) | Every `register_*` hunk receives the FastAPI `app`: route tickets include routers from their hunk (AEA-23 item 2), AEA-49 mounts files and registers public paths (web.md §6, §12) | Stub signature `(container, app, *, settings, limits)` | `test_every_register_stub_present` checks each call's arguments |
| S-3 (plan-added) | `register_frontend` runs **last**: its SPA fallback answers every unmatched GET, so every API router must be included before it | Call order in `build_container` (§4.3) | `test_every_register_stub_present` checks the order |
| S-4 (plan-added) | `live` marker registered now, so AEA-61's `@pytest.mark.live` passes `--strict-markers` without a pyproject edit | §4.1 `markers` | `tests/unit/test_skeleton.py::test_journey_and_live_markers_registered` |
| S-5 (plan-added) | AEA-57 needs a place to load its pytest plugin without editing AEA-01 files (AEA-57 *Agent handoff*) | `tests/conftest.py` loads `tests.journeys.support.plugin` when the module exists (§4.4) | `tests/unit/test_skeleton.py::test_optional_journey_plugin_is_absent_today` |
| S-6 (plan-added) | Journey test basenames repeat across folders (`j2/test_aea_51.py`, `j3/test_aea_51.py`), and pytest's default import mode fails on duplicate basenames outside packages | `j1`…`j10` `__init__.py` markers | Implicit: collection succeeds once journeys land; `test_skeleton.py::test_every_planned_package_imports` imports `tests.journeys.j1`…`j10` |
| S-7 (plan-added) | numpy is a named dependency (data.md §3 index file `vectors.npy`) | §4.1 | AC-2 read-back |
| S-8 (plan-added) | Type stubs for the two untyped dev libraries mypy will see (PyYAML, jsonschema) | `types-pyyaml`, `types-jsonschema` in dev | AC-2 read-back; `uv run mypy` green |

**Observability, evaluation, metrics:** N/A as the ticket states. No entry point, record or span. M-26's one literal
(`spend.daily_cap_usd` 30.0) and M-23's bound (60 s) are declared here and asserted by AC-3.

**Entry-point registration:** None. `python -m tests.journeys.affected` is test tooling, not a product entry point,
so no WF-n row applies.

**Source reconciliation: nothing needs a decision.**
- Role caps stay out of `Limits` (DO-4 §12; AEA-02 owns `RoleSpec.cap_s`).
- `STREAM_POLL_S`, `STREAM_HEARTBEAT_S` and `CapacityLimiter(4)` stay out (web.md §11, §4).
- `probe_after_s` stays a `LedgerService` default (models.md cross-topic 3: "unless AEA-01 adds it"). It is not added.
- D-4…D-15 do not touch this ticket.

The orchestrator should post the plan-added rows S-1…S-8 on issue #1 as proposed criteria. The implementer does not
post them.

---

## 4. Shared code to use (exact shapes)

### 4.1 `pyproject.toml`: write exactly this

```toml
[project]
name = "meridian-agent"
version = "0.1.0"
description = "Meridian Home Comfort AI service agent (AEA FDE Challenge)"
requires-python = ">=3.12,<3.13"
dependencies = [
  "fastapi>=0.156",
  "uvicorn[standard]>=0.54",
  "pydantic>=2.14",
  "langgraph==1.2.16",
  "langgraph-checkpoint-sqlite>=3.1.2",
  "anthropic>=1.17",
  "httpx>=0.28",
  "fastembed>=0.9",
  "numpy>=2.0",
  "langfuse>=5,<6",
  "anyio>=4.15",
  "pypdf>=6.21",
]

[dependency-groups]
dev = [
  "pytest>=9.1",
  "ruff>=0.17",
  "mypy>=2.4",
  "jsonschema>=4.18",
  "pyyaml>=6.0",
  "types-pyyaml>=6.0",
  "types-jsonschema>=4.18",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/meridian"]

[tool.pytest.ini_options]
testpaths = ["tests", "eval"]
pythonpath = ["."]
addopts = "--strict-markers --strict-config -ra"
xfail_strict = true
markers = [
  "journey: an integrated journey (.claude/rules/integrated-journeys.md); selected by `pytest -m journey` and by `python -m tests.journeys.affected`",
  "live: calls a paid model provider; never part of a default or merge-gate run (DO-3 §9 tests/live/; integrated-journeys.md rule 4)",
]

[tool.ruff]
line-length = 110
target-version = "py312"
extend-exclude = ["docs", "apps", "var", "data", ".claude"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "S", "RUF"]
ignore = ["E501", "RUF001", "RUF002", "RUF003"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S105", "S106", "S603", "S607"]

[tool.ruff.lint.isort]
known-first-party = ["meridian", "tests", "eval"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
files = ["src/meridian", "tests", "eval"]

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
```

**Dependency table (AC-2 read-back must match line for line):**

| Group | Line | Why (source) |
|---|---|---|
| runtime | `fastapi>=0.156` | the web layer (DO-3 §2.1) |
| runtime | `uvicorn[standard]>=0.54` | its server (data.md §7 start command) |
| runtime | `pydantic>=2.14` | every typed model (DO-4 §0) |
| runtime | `langgraph==1.2.16` | pinned (DO-3 §2.2) |
| runtime | `langgraph-checkpoint-sqlite>=3.1.2` | `SqliteSaver` (DO-3 §2.1, §4.3) |
| runtime | `anthropic>=1.17` | sync Anthropic SDK (DO-3 §2.1, §4.3) |
| runtime | `httpx>=0.28` | Jev adapter client and TestClient (DO-3 §4.3) |
| runtime | `fastembed>=0.9` | `BAAI/bge-small-en-v1.5` (PRD R-11; data.md §3) |
| runtime | `numpy>=2.0` | `vectors.npy` index file (data.md §3) |
| runtime | `langfuse>=5,<6` | Langfuse SDK v5 (DO-6 *Content and redaction*) |
| runtime | `anyio>=4.15` | `CapacityLimiter` (DO-3 §2.3; web.md §4) |
| runtime | `pypdf>=6.21` | fee PDF parser (R-9; parked file used pypdf) |
| dev | `pytest>=9.1` | tests |
| dev | `ruff>=0.17` | lint and format |
| dev | `mypy>=2.4` | **the one type checker** (later tickets already cite `uv run mypy …`: AEA-20, 21, 24) |
| dev | `jsonschema>=4.18` | AEA-23's OpenAPI response check (web.md §13; WEB-24) |
| dev | `pyyaml>=6.0` | loads the OpenAPI (web.md §13) |
| dev | `types-pyyaml>=6.0` | mypy stubs for PyYAML |
| dev | `types-jsonschema>=4.18` | mypy stubs for jsonschema |

Not present: `jinja2`, `python-multipart` (no templates, slice plan §0), `python-dotenv`, `pydantic-settings`,
`pytest-xdist` (run it with `uv run --with pytest-xdist` when needed), `pytest-playwright` (AEA-58 adds its own line).

The planner resolved this exact set with `uv lock` in a scratch copy on 2026-10-21. It resolved 102 packages,
`langgraph 1.2.16`, `langfuse 5.0.4`, `mypy 2.4.0`, `pytest 9.1.1`, `ruff 0.17.1`, and no jinja2 or python-multipart.
The same scratch run confirmed mypy 2.4 in strict mode with the pydantic plugin accepts PEP 695 generics.

### 4.2 `src/meridian/policy/limits.py`: write exactly this

Field names, values and comments are final. Do not add module-level assignments of any kind (AC-4).

```python
"""Every shared numeric limit in one place (DO-3 §4.1; merge-clashes MC-22).

The composition root (web/container.py) builds ONE frozen ``Limits``. GraphDeps.limits and ModelGateway(..., limits=...)
receive it whole (DO-4 §2, §12, §14); every other consumer receives the part it needs from the container. No other module
holds a second literal for any value here. Standard library only (DO-3 §4.1 "depends on: none").

Labels: [Decided X] a recorded decision this file only applies; proposal: a choice awaiting Innocent; [A] an assumption,
with the measurement that replaces it; [T] a target.

Not here, on purpose: the per-role model call caps (RoleSpec.cap_s in AEA-02's config.py ModelSettings defaults,
DO-4 §12); the CON-3/CON-21 stream constants STREAM_POLL_S and STREAM_HEARTBEAT_S (web.md §11, AEA-41); the stream
CapacityLimiter(4) (web.md §4, AEA-23).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TurnLimits:
    """One customer turn's time budget, and the CON-1 timing values the browser reads (api-con-mapping §0)."""

    deadline_s: int = 60  # [Decided SDQ-1] the per-turn deadline (DO-4 §2 TurnBudget; DO-3 §2.3)
    still_working_after_ms: int = 10_000  # CON-1; SCREEN_SPECS SCR-1 "Still working on this…" at about 10 s
    browser_grace_s: int = 5  # [A] DO-3 §2.3 rule 5: the browser waits deadline + 5 s; replaced by the
    #   Railway proxy-timeout check at first deploy (A12)
    max_message_chars: int = 2_000  # CON-1; the OpenAPI TextPayload maxLength

    @property
    def turn_deadline_ms(self) -> int:
        """CON-1 ``turn_deadline_ms``: the one deadline in milliseconds (60000), never typed twice."""
        return self.deadline_s * 1_000

    @property
    def browser_give_up_after_ms(self) -> int:
        """CON-1 ``browser_give_up_after_ms`` [A]: deadline plus the browser grace, in milliseconds (65000)."""
        return (self.deadline_s + self.browser_grace_s) * 1_000


@dataclass(frozen=True)
class Admission:
    """How many customer turns may run at once (DO-3 §2.3)."""

    max_in_flight: int = 30  # [Decided SDQ-9] turn 31 gets BUSY with the person key and no model call


@dataclass(frozen=True)
class Brakes:
    """Loop brakes inside one turn (R-41; agent-architecture rules 5, 15). All three are proposals."""

    tasks_per_turn: int = 3  # proposal (code-design §4.1; DO-4 §4 Plan.tasks max_length=3)
    tool_rounds: int = 2  # proposal (graph-tools C-9; the specialist runner's tool loop)
    sonnet_calls: int = 6  # proposal (models.md cross-topic 3; SP-1 mix B reached exactly 6 in 7 of 192 turns [M])


@dataclass(frozen=True)
class IdentityLimits:
    """One-time code limits (R-15; graph-tools §5, C-9)."""

    code_ttl_s: int = 600  # [Decided R-15] 10-minute expiry
    tries: int = 3  # [Decided R-15] 3 attempts
    max_sends: int = 3  # proposal [A] at most 3 codes sent per conversation (DO-4 §14 IdentityService)


@dataclass(frozen=True)
class BookingLimits:
    """The R-41 booking cap (DO-4 §1 FailureCounters.bookings; ToolErrorCode booking_cap)."""

    max_per_conversation: int = 3  # proposal (code-design §4.1)


@dataclass(frozen=True)
class SpendLimits:
    """Our model-spend cap (models.md §6). Limits.spend, beside Limits.web."""

    daily_cap_usd: float = 30.0  # our cap, US dollars per America/Chicago day
    #   [T] system design §2 "$30/day" (Q-061; DO-7 M-26); the ONE literal


@dataclass(frozen=True)
class WebLimits:
    """Rate limits and session timing for the web shell (web.md §5; WEB-2, WEB-4, WEB-5; MC-14, MC-22).

    Each [A] is "set above 20" (PRD §5) for the 20-at-once load, and is replaced by the E-8 load re-measure at Stage 9
    (0 limited responses at 20 conversations from one IP and one login) and by abuse seen in the deploy logs.
    """

    chat_turns_per_thread_per_min: int = 20  # [A] a person types far fewer; one scripted case has ≤ ~10 turns
    chat_turns_per_session_per_min: int = 600  # [A] 20 closed-loop conversations at SP-1's p50 4.7 s ≈ 255/min [C], ×2
    chat_turns_per_ip_per_min: int = 600  # [A] same arithmetic: the harness and a reviewer's office share one IP
    reads_per_session_per_min: int = 120  # [A] apps/web polls the demo status every 10 s per open tab (POLL_MS)
    reads_per_ip_per_min: int = 240  # [A]
    login_rejects_per_ip: int = 10  # [A] rejected attempts per window; while over, every attempt (even the
    login_reject_window_s: int = 600  #   right pair) answers 429 LOGIN_RATE_LIMITED + Retry-After (AEA-23 AC-5)
    resets_per_ip: int = 10  # [A] per window; never reached by a reviewer, so not a cool-down (R-48)
    reset_window_s: int = 600
    login_session_lifetime_s: int = 43_200  # 12 h absolute, no idle timeout [Decided §7, engineering; WEB-5]
    reset_wait_s: int = 5  # [A] [Source: UI_CONTRACTS *Still open* "the 5 s reset-lock wait"] (web.md §7)


@dataclass(frozen=True)
class ContextLimits:
    """Chat window limits (graph-core §7; GRC-9, GRC-14). Replaced by the first full eval run (E-1, E-2)."""

    window_turns: int = 10  # [A] R-45 "about 10". Lines of the last 10 turn_ids, plus representative and
    #   event lines (turn_id None) since the oldest kept turn
    window_line_chars: int = 600  # [A] each ChatLine cut to 600 chars with "…"
    window_total_chars: int = 8_000  # [A] oldest lines dropped first until the window fits
    planner_lines: int = 6  # [A, SP-1] DO-4 §3: the planner's recent_chat, taken from the same window
    planner_line_chars: int = 400  # [A, SP-1]


@dataclass(frozen=True)
class Limits:
    """The one frozen set of shared limits (MC-22), built once by web/container.py."""

    turn: TurnLimits = field(default_factory=TurnLimits)
    admission: Admission = field(default_factory=Admission)
    brakes: Brakes = field(default_factory=Brakes)
    identity: IdentityLimits = field(default_factory=IdentityLimits)
    booking: BookingLimits = field(default_factory=BookingLimits)
    spend: SpendLimits = field(default_factory=SpendLimits)
    web: WebLimits = field(default_factory=WebLimits)
    context: ContextLimits = field(default_factory=ContextLimits)
```

Running `ruff format` may re-wrap the trailing comments. That is fine. Values and names must not change.

### 4.3 `src/meridian/web/container.py`: interface and behaviour

**Module docstring** (write it with this meaning; the wording may be tightened):
- `build_container` makes the one `Limits`, takes the built `Settings` and the FastAPI `app` from its caller (the app
  lifespan in `web/app.py`, AEA-23), and calls one `register_<area>()` hunk per registering ticket in a fixed order.
- Each hunk belongs to the ticket named in its docstring. That ticket edits only that function's body (slice plan §3).
- Hunks cooperate through `Container.provide/get` (lazy, built once), `on_start` (threads and sweeps, run after every
  object is built) and `on_close` (release, newest first).
- **A hunk imports its own modules inside its own function body. This file's module-level imports never change after
  AEA-01.** That keeps wave 0 free of internal edges and stops later tickets from colliding on the import block.
- No module-level clients, settings or singletons (DO-3 §2.1).

**Module-level imports: exactly these and nothing else:**

```python
from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from meridian.policy.limits import Limits

if TYPE_CHECKING:
    from fastapi import FastAPI
```

**Types (exact signatures):**

```python
class ContainerError(RuntimeError):
    """A wiring mistake: an unknown, duplicate or cyclic provider, or use after build or close."""


@dataclass(frozen=True)
class Key[T]:
    """Names one provided object, e.g. Key[LedgerService]("ledger"). Two keys are equal when their names are."""

    name: str


class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    @property
    def settings(self) -> Any: ...      # AEA-02's meridian.config.Settings; typed Any so this file imports no
                                        #   other ticket's module (slice plan §2). Hunks narrow it themselves.
    @property
    def limits(self) -> Limits: ...
    @property
    def closed(self) -> bool: ...
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...
    def get[T](self, key: Key[T]) -> T: ...
    def on_start(self, starter: Callable[[], None]) -> None: ...
    def on_close(self, closer: Callable[[], None]) -> None: ...
    def build(self) -> None: ...
    def close(self) -> None: ...


def build_container(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container: ...
```

Use PEP 695 generics (`class Key[T]`, `def get[T]`). **Do not** write a module-level `T = TypeVar("T")`: it would be a
module-level call (AC-7 grep).

**Container behaviour: numbered rules, each with the invariant it protects:**

1. `__init__` stores `settings` and `limits` and creates private state:
   - `_factories: dict[str, Callable[[Container], object]]` (insertion-ordered);
   - `_objects: dict[str, object]`;
   - `_building: list[str]`;
   - `_starters: list[Callable[[], None]]`;
   - `_closers: list[Callable[[], None]]`;
   - `_built = False`, `_closed = False`.

   *Invariant: the container holds no `overrides`, so no hunk but `register_graph` can reach them (R-W-8).*
2. `provide(key, factory)`:
   - if `_built` or `_closed`, raise `ContainerError(f"provide after build: {key.name}")`;
   - if `key.name` is already in `_factories`, raise `ContainerError(f"already provided: {key.name}")`;
   - otherwise store the factory and **do not call it**.

   *Invariant: one provider per name; hunk order does not matter for construction.*
3. `get(key)`:
   1. If `_closed`, raise `ContainerError(f"get after close: {key.name}")`.
   2. If the name is already built, return `cast(T, _objects[name])`.
   3. If the name was never provided, raise `ContainerError(f"not provided: {key.name}")`.
   4. If the name is in `_building`, raise `ContainerError(f"provider cycle: {chain}")`, where `chain` is
      `" -> ".join(_building[_building.index(name):] + [name])`.
   5. Otherwise append the name to `_building`, call the factory with `self`, and pop the name in a `finally` block.
      Store the result in `_objects` and return it.

   *Invariant: every object is built at most once; a true cycle fails loudly with its chain, never by recursing
   without end.*
4. `on_start(starter)`: if `_built`, raise `ContainerError("on_start after build")`; else append the starter.
   `on_close(closer)`: if `_closed`, raise `ContainerError("on_close after close")`; else append the closer.
5. `build()`:
   1. If `_built`, raise `ContainerError("already built")`.
   2. For every name in `list(_factories)`, in provide order, call `self.get(Key[object](name))`.
   3. Set `_built = True`.
   4. Call each starter in registration order.

   *Invariant: everything is constructed at start-up, so a wiring error surfaces at boot and not on a request; no
   thread starts before every object it might read exists.*
6. `close()`:
   1. If `_closed`, return (a second call does nothing).
   2. Set `_closed = True`.
   3. Pop and call closers newest first. Collect each `Exception` and keep going.
   4. After all closers ran, if any failed, raise `ExceptionGroup("container close failed", errors)`.

   *Invariant: everything opened is released exactly once (DO-3 §2.1, "closes everything on shutdown").*
7. `build_container(app, settings, *, overrides=None)`:
   1. Set `limits = Limits()` and `container = Container(settings=settings, limits=limits)`.
   2. Inside `try:`, call the 27 hunks **by name, in the order of the table below**. Each call is
      `register_x(container, app, settings=settings, limits=limits)`. The one exception is
      `register_graph(container, app, settings=settings, limits=limits, overrides=overrides)`. Then call
      `container.build()`.
   3. On `except BaseException:` run `with contextlib.suppress(Exception): container.close()`, then `raise`.
   4. Return `container`.

   Call the hunks by their module-global names inside the function body. Do **not** collect them in a tuple at import
   time: the tests monkeypatch the module attributes. Do not set `app.state` here. Storing the container on
   `app.state` is the lifespan's job (AEA-23).

   *Invariant: one `Limits` per container, shared by identity with every hunk; a failed build leaks nothing.*

**The 27 hunks.** Each is a public module function with **only a docstring as its body**. The docstring's first
sentence names the ticket exactly as below. Signature:
`def register_x(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:`. `register_graph`
adds `, overrides: Any` after `limits`, with no default.

| Order | Function | Ticket | Docstring (first line, exact) |
|---|---|---|---|
| 1 | `register_storage` | AEA-10 | `AEA-10 storage: SQLite unit of work, migrations and first boot, checkpointer (cases.md §1).` |
| 2 | `register_web` | AEA-23 | `AEA-23 web shell: login routes, reset gate, rate limiter, public paths, web/deps.py bindings (web.md §1–§7).` |
| 3 | `register_ops` | AEA-32 | `AEA-32 ops: health events, heartbeat, watchdog, alerts (cases.md §8).` |
| 4 | `register_tracing` | AEA-19 | `AEA-19 tracing: Langfuse or null trace sink and the project-key check (models.md §4, §7).` |
| 5 | `register_spend` | AEA-26 | `AEA-26 spend: LedgerService and the spend guard (models.md §6).` |
| 6 | `register_anthropic` | AEA-17 | `AEA-17 models: the Anthropic adapter (models.md §2, §7).` |
| 7 | `register_jev` | AEA-18 | `AEA-18 models: the Jev adapter via OpenRouter (models.md §3, §7).` |
| 8 | `register_gateway` | AEA-20 | `AEA-20 models: the ModelGateway (DO-4 §12; models.md §5, §7).` |
| 9 | `register_retrieval` | AEA-33 | `AEA-33 retrieval: empty unless AEA-33 needs it; knowledge_tools() is wired in register_graph (data.md §4).` |
| 10 | `register_tool_dispatch` | AEA-22 | `AEA-22 tools: empty unless AEA-22 needs it; the ToolRegistry and ToolDispatcher are wired in register_graph (graph-tools §1).` |
| 11 | `register_identity` | AEA-27 | `AEA-27 identity: IdentityService and the demo inbox (graph-tools §5).` |
| 12 | `register_scheduling` | AEA-28 | `AEA-28 scheduling: SchedulingService (cases.md §4).` |
| 13 | `register_cases` | AEA-29 | `AEA-29 cases and handoff: CaseService, HandoffService, BriefAssembler (cases.md §5).` |
| 14 | `register_demo` | AEA-30 | `AEA-30 demo: DemoClock, staffing, the scheduler job thread (cases.md §6).` |
| 15 | `register_reset` | AEA-31 | `AEA-31 reset: ResetService and the demo seed (cases.md §7).` |
| 16 | `register_staff_session` | AEA-44 | `AEA-44 staff: StaffSessionStore, FlagService, CON-10 routes (staff.md §2).` |
| 17 | `register_chat` | AEA-40 | `AEA-40 customer API: SessionService, TurnService, CON-1 and CON-2 routes, the start-up turn sweep (web.md §9, §14).` |
| 18 | `register_events` | AEA-41 | `AEA-41 customer API: the CON-3 event stream route (web.md §11).` |
| 19 | `register_person_request` | AEA-42 | `AEA-42 customer API: PersonRequestService, CON-4 and CON-5 routes (web.md §8).` |
| 20 | `register_demo_routes` | AEA-43 | `AEA-43 customer API: CON-6 to CON-9 demo routes (web.md §7).` |
| 21 | `register_staff_cases` | AEA-45 | `AEA-45 staff API: queue, case, actions, contact log, flags, oversight routes (staff.md §6).` |
| 22 | `register_staff_live` | AEA-46 | `AEA-46 staff API: LiveChatService, CON-14 and CON-21 routes (staff.md §5, §7).` |
| 23 | `register_staff_clock` | AEA-47 | `AEA-47 staff API: the CON-8 clock-advance route (staff.md §8).` |
| 24 | `register_metrics_reader` | AEA-53 | `AEA-53 reads: MetricsReader bound to get_metrics_reads() (cases.md §9).` |
| 25 | `register_reads` | AEA-48 | `AEA-48 reads API: CON-18 to CON-20 routes (staff.md §9).` |
| 26 | `register_graph` | AEA-51 | `AEA-51 integration: completes the graph and binds run_graph; the only reader of overrides (web.md §15, R-W-8).` |
| 27 | `register_frontend` | AEA-49 | `AEA-49 frontend: serves apps/web/dist; runs last so its SPA fallback never shadows an API route (web.md §12).` |

Add a second docstring line to every hunk: `No-op until <ticket> fills it.` Use the hunk's ticket, for example
`No-op until AEA-10 fills it.`

The names `register_demo`, `register_ops`, `register_frontend` and `register_graph` come from the addenda. The other
23 are named by area here, as the ticket asks. The 25 tickets of slice plan §3 plus 49 and 51 make 27.

### 4.4 `tests/conftest.py`: write with this content and behaviour

```python
"""Suite-wide pytest configuration (AEA-01). Shared fixtures only; each ticket keeps its own fixtures in its own test
folder (slice plan §3). No fixtures are shared yet."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tests.journeys.affected import journey_files

# AEA-57 creates tests/journeys/support/plugin.py (its options and fixtures); it is loaded only once it exists.
_OPTIONAL_PLUGINS = ("tests.journeys.support.plugin",)


def _module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


pytest_plugins = [name for name in _OPTIONAL_PLUGINS if _module_exists(name)]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """`pytest -m journey` before any journey exists is not a failure (AEA-01 AC-9). Once a journey file exists,
    an empty journey selection is a real error again."""
    markexpr = str(session.config.getoption("markexpr") or "")
    if (
        exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED
        and markexpr.split()[:1] == ["journey"]
        and not journey_files(Path(session.config.rootpath))
    ):
        session.exitstatus = pytest.ExitCode.OK
```

Why it is shaped this way:
- pytest returns exit code 5 when `-m journey` deselects everything. The planner reproduced this with pytest 9.1.1 and
  checked that this hook turns it into 0.
- `pytest_plugins` is allowed here because `tests/conftest.py` is loaded as an initial conftest for every run over
  `tests`. A non-top-level conftest would be rejected by pytest.

### 4.5 `tests/journeys/affected.py`: the affected-journeys command

**Command line (the merge gate's one command):**

```
uv run python -m tests.journeys.affected [--base REF] [--files PATH ...] [--root DIR] [--list-only] [-- PYTEST_ARGS ...]
```

- `--base REF` (default `main`): the diff is `REF...HEAD`, plus uncommitted and untracked files.
  - Implementer before commit: `--base main`.
  - Merge gate after merging into main: `--base <main SHA before the merge>`, for example `--base HEAD^1` on a merge
    commit.
- `--files PATH ...`: use these repo-relative paths as the changed set and call no git (tests use this).
- `--root DIR` (default: the repo root, `Path(__file__).resolve().parents[2]`): tests point it at a temporary tree.
- `--list-only`: print the selection and do not run pytest.
- Everything after a literal `--` is passed to pytest unchanged. Split `argv` at the first `"--"` yourself, before
  argparse.

**Output (exact):**

```
changed files: <k> (base <REF>)          ← with --files: "changed files: <k> (given)"
<n> journeys affected                    ← n == 1: "1 journey affected"
  <path>                                 ← one line per selected journey, sorted
```

- When `n > 0` and `--list-only` is absent, also print `running: <the command joined with spaces>`. Then run
  `[sys.executable, "-m", "pytest", "-m", "journey", *selected, *pytest_args]` with
  `subprocess.call(..., cwd=root)` and return its exit code.
- When `n == 0`, return 0.
- When git fails (for example an unknown ref), print `affected: git failed: <stderr first line>` to stderr and return 2.

**Functions (exact signatures; all paths are POSIX strings relative to the root):**

```python
ALWAYS_EXACT: tuple[str, ...] = ("pyproject.toml", "uv.lock", "tests/conftest.py",
                                 "docs/ux/03-structure/ui-contracts.openapi.yaml")
ALWAYS_PREFIXES: tuple[str, ...] = ("apps/web/", "docs/data/issued/", "data/", "tests/journeys/")

def journey_files(root: Path) -> list[str]: ...
def changed_files(base: str, root: Path) -> list[str]: ...
def module_name_for(rel_path: str) -> str | None: ...
def module_index(root: Path) -> dict[str, Path]: ...
def imported_modules(path: Path, module: str, index: Mapping[str, Path]) -> set[str] | None: ...
def closure(module: str, index: Mapping[str, Path]) -> tuple[set[str], bool]: ...
def select_journeys(changed: Sequence[str], root: Path) -> list[str]: ...
def main(argv: Sequence[str] | None = None) -> int: ...

if __name__ == "__main__":
    raise SystemExit(main())
```

(`ALWAYS_EXACT` and `ALWAYS_PREFIXES` are tuples of strings in a test module. The "no module-level numeric constant"
rule applies only to `policy/limits.py`.)

**Algorithm: numbered steps and the invariant each one protects:**

1. **`journey_files(root)`.** A journey file is either:
   - `tests/journeys/j<digits>/test_*.py`, where the folder name matches `^j\d+$`; or
   - `tests/journeys/browser/**/test_*.py`.

   Return them sorted. `support/`, `README.md`, `affected.py` and anything else are not journeys.
   *Invariant: only the files the slice plan §0a convention names are journeys; today the list is empty.*
2. **`changed_files(base, root)`.** Take the sorted union of the output lines of these three commands, each run with
   `subprocess.run([...], cwd=root, check=True, capture_output=True, text=True)`:
   - `git diff --name-only --no-renames <base>...HEAD`;
   - `git diff --name-only --no-renames HEAD`;
   - `git ls-files --others --exclude-standard`.

   *Invariant: a branch's commits, its uncommitted edits and its new files are all counted; `--no-renames` reports
   both sides of a rename.*
3. **`module_name_for(rel_path)`.** Map a path to a module name:
   - `src/meridian/a/b.py` → `meridian.a.b`;
   - `src/meridian/a/__init__.py` → `meridian.a`;
   - `tests/x/y.py` → `tests.x.y`;
   - `eval/h/r.py` → `eval.h.r`;
   - any other path, or a non-`.py` path → `None`.
4. **`module_index(root)`.** For every `*.py` under `src/meridian`, `tests` and `eval`, map
   `module_name_for(path) → absolute Path`.
5. **`imported_modules(path, module, index)`.**
   1. Run `ast.parse` on the file's UTF-8 text. On `SyntaxError`, return `None`.
   2. Walk every node with `ast.walk`, so imports inside functions and inside `if TYPE_CHECKING:` count too.
   3. For `Import`, take each `alias.name`.
   4. For `ImportFrom`, start from `node.module`. When `node.level > 0`, resolve the import against the importing
      module's package:
      - the package parts are `module.split(".")` if the file is an `__init__.py`, else `module.split(".")[:-1]`;
      - drop the last `level - 1` parts;
      - append `node.module` when it is set.

      The result is the base. Take the base, and also `f"{base}.{alias.name}"` for each alias that is not `*`.
   5. Resolve every candidate to the **longest dotted prefix present in `index`**, and keep those.

   *Invariant: `from tests.journeys.support import harness` reaches `tests.journeys.support.harness`, and
   `meridian.web.app.create_app` reaches `meridian.web.app`.*
6. **`closure(module, index)`.** Run a breadth-first search from `module` over `imported_modules`. For every module
   reached, also add each parent package present in `index` (`a.b.c` adds `a` and `a.b`). Return
   `(reached, uncertain)`, where `uncertain` is `True` if any file returned `None`.
   *Invariant: "a journey's path imports a changed module" is answered statically, including the container's
   function-level imports once hunks are filled.*
7. **`select_journeys(changed, root)`.**
   1. Compute `journeys = journey_files(root)`. If it is empty, return `[]`.
   2. Walk each changed path `p`:
      - If `p` is in `journeys`, select `p` itself.
      - Else, if `p` is in `ALWAYS_EXACT` or starts with any of `ALWAYS_PREFIXES`, set `everything = True`.
      - Else, if `p` ends with `.py` and `module_name_for(p)` is not `None`, add that module to `touched`. If the file
        no longer exists, also add its parent package (the name minus its last part).
      - Else, if `p` is under `src/meridian/` and is not `.py` (SQL schema, templates), add the module name of the
        nearest ancestor directory that contains an `__init__.py` in the current tree. For example,
        `src/meridian/adapters/sqlite/schema/00_core.sql` → `meridian.adapters.sqlite`.
      - Every other path (docs, `.claude/`, `eval/` data) selects nothing.
   3. If `everything` is true, return all `journeys`.
   4. Otherwise, when `touched` is not empty, a journey `j` is also selected when `closure(module_name_for(j))`
      intersects `touched` or is `uncertain` (a file on its path did not parse). When `touched` is empty, no
      further journey is selected.
   5. Return the selection sorted.

   *Invariant: "when unsure, run it" (build-loop-test-scope AEA addition). Config, lockfile, conftest, harness,
   OpenAPI, issued data and the frontend build input select every journey; a changed SQL schema selects every journey
   that imports the storage package.*

**Do not** import anything from `meridian` in `affected.py`. It reads files, not modules, so it works even when a
change breaks imports.

---

## 5. Steps (build order; each step is small enough to check)

Work in your own worktree or branch from `main` at `9c3e7e7` or later. If the orchestrator has not named a branch, use
`aea-01-foundation`. Run `export UV_LINK_MODE=hardlink` in every shell. Never copy a venv; `uv sync` makes the
worktree's own `.venv`.

1. **Write `pyproject.toml`** exactly as §4.1. Append `.mypy_cache/`, `.pytest_cache/` and `.ruff_cache/` (one per
   line) to `.gitignore`.
2. **Create the package markers** (all 0 bytes; use `touch`, not an editor, so they stay 0 bytes):
   - `src/meridian/__init__.py` and the 18 `src/meridian/**/__init__.py` of §2;
   - `eval/__init__.py`, `eval/harness/__init__.py`;
   - `tests/__init__.py`, the 12 `tests/*/__init__.py`, the 10 `tests/unit/*/__init__.py`;
   - `tests/journeys/j1/__init__.py` … `tests/journeys/j10/__init__.py`.

   Check: `find src/meridian tests eval -name __init__.py -size +0` prints nothing.
3. **Lock and sync:** `uv lock`, then `uv sync`. Check: `uv run python -c "import meridian"` exits 0, and
   `uv tree --depth 1` shows `langgraph v1.2.16`.
4. **Write `src/meridian/policy/limits.py`** exactly as §4.2. Check:
   `uv run python -c "from meridian.policy.limits import Limits; l = Limits(); print(l.turn.turn_deadline_ms, l.turn.browser_give_up_after_ms, l.spend.daily_cap_usd)"`
   prints `60000 65000 30.0`.
5. **Write `tests/unit/policy/test_limits.py`** (tests named in §7). Run
   `uv run pytest tests/unit/policy -q`; it must be green.
6. **Write `src/meridian/web/container.py`** per §4.3: the types first, then the 27 hunks, then `build_container`.
7. **Write `tests/unit/web/test_container.py`** (§7). Run `uv run pytest tests/unit/web -q`; it must be green.
8. **Write `tests/journeys/affected.py`** per §4.5, then **`tests/conftest.py`** per §4.4 (the conftest imports
   `journey_files` from it).
9. **Write `tests/journeys/README.md`.** About 25 lines covering:
   - the layout: `j1`…`j10` map to J-1…J-10 in slice plan §0a; `support/` is AEA-57's; `browser/` is AEA-58's;
   - the rule that each ticket adds only `j<N>/test_aea_<NN>.py` and marks its tests `@pytest.mark.journey`;
   - the affected command and its merge-gate form (`--base <pre-merge SHA>`);
   - where AEA-57's plugin goes (`tests/journeys/support/plugin.py`; `tests/conftest.py` loads it automatically);
   - the record location `docs/testing/journeys/YYYY-MM-DD-<scope>.md` and the three levels, citing
     `integrated-journeys.md` §4.

   No secrets or demo credentials.
10. **Write `tests/unit/test_affected_journeys.py`, `tests/unit/test_import_direction.py` and
    `tests/unit/test_skeleton.py`** (§7). Run them green.
11. **Run the gates and the journey checks** in the order of §7. Fix anything red. Then make **commit 1**:
    - stage with explicit paths only: `git add pyproject.toml uv.lock .gitignore src/meridian eval/__init__.py
      eval/harness/__init__.py tests`;
    - run `git status --short` and compare the staged list against §2. Nothing else may be staged, and nothing under
      `docs/parked/` may appear;
    - commit with the message:
      `feat(foundation): scaffold, limits, composition-root stubs (AEA-01)` + blank line + one-paragraph body + blank
      line + `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` as the **last** line.
12. **Write the record and the context updates, then make commit 2.** `<sha1>` = commit 1's short SHA. Get today's
    date with `TZ=America/Chicago date +%F`.
    - `docs/testing/journeys/<date>-AEA-01.md`: a title line plus a two-column table with the nine fields of
      `integrated-journeys.md` §4:
      - Claim: "AEA-01 AC-9: the journey gate exists before any journey: `journey` marker registered;
        `pytest -m journey --collect-only -q` exits 0; the affected-journeys command selects 0 journeys on this diff";
      - Level: `mock-tested`;
      - Tested revision: `<sha1>`;
      - Environment: "VPS, `uv run`, Python 3.12; no server, no database, no model";
      - Command: the two commands exactly as run;
      - Result: pass, with the output lines quoted (`0 journeys affected`);
      - Evidence location: "this record";
      - Remaining limitations: "No journey exists yet; nothing integrated is claimed";
      - Blocked by: "AEA-57 (journey harness and J-1)".
    - `.claude/reference/area-map.md`:
      - replace the sentence `**Every code path below is planned.** No product code exists yet;` with
        `**Every code path below is planned unless its row says built.** AEA-01 (\`<sha1>\`) built the package
        skeleton;`. Keep the rest of that paragraph;
      - in the A0 row's *Status* cell, replace `planned` with:
        `partly built: AEA-01 \`<sha1>\` (\`pyproject.toml\`, package skeleton, \`policy/limits.py\`,
        \`web/container.py\` with 27 \`register_<area>()\` stubs, \`tests/conftest.py\`, \`tests/journeys/\` skeleton);
        \`config.py\` is AEA-02's; the rest planned`.
    - `.claude/state/icm-progress.md`:
      - *Physical scaffold* row → Status `established`;
      - Evidence: `Backend spine: \`pyproject.toml\`, \`src/meridian/\` package skeleton, \`policy/limits.py\`,
        \`web/container.py\`, \`tests/\` and \`tests/journeys/\` skeleton (AEA-01 \`<sha1>\`); frontend
        [\`apps/web/\`](../../apps/web/) (UX-4, gate unsigned)`;
      - Next check: `Area map rows turn actual as wave-0/1 tickets land`. Keep the row under 400 characters;
      - prefix the *Last reconciled* line with `<date> — AEA-01 scaffold (scaffold row); earlier, `.
    - `docs/design/code-design.md` line 6: replace `**Nothing here is built: every path below is planned.**` with
      `**Built so far (AEA-01, \`<sha1>\`): \`pyproject.toml\`, the §3 and §9 package markers, \`policy/limits.py\`,
      \`web/container.py\` (stubs), \`tests/conftest.py\`; every other path below is planned.**`
    - Stage with explicit paths:
      `git add docs/testing/journeys/<date>-AEA-01.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`.
    - Commit: `docs(context): AEA-01 built paths and journey record` + body + the same `Co-Authored-By` last line.
13. **Do not push or merge.** The merge step does that. Report back using the evidence list in §7.

---

## 6. Data and fixtures

No product data. Every test builds what it needs in memory or in `tmp_path`:
- a stand-in settings object: `types.SimpleNamespace(name="stand-in")`;
- an app: `fastapi.FastAPI()`;
- sentinel overrides: `object()`;
- fake repo trees for the selector: small `.py` files written under `tmp_path`, shown below;
- a throw-away git repo in `tmp_path` for `changed_files`. Run each git command there with
  `-c user.name=aea01-test -c user.email=aea01@example.invalid`.

There are no phone numbers, codes, card-like numbers, credentials or `.env` reads anywhere.

Selector fake tree (used by several tests; build it with a helper `_tree(tmp_path, files: dict[str, str])` that writes
each file and its parent dirs):

```
src/meridian/__init__.py                ""
src/meridian/policy/__init__.py         ""
src/meridian/policy/limits.py           ""
src/meridian/gates/__init__.py          ""
src/meridian/gates/rules.py             ""
src/meridian/adapters/__init__.py       ""
src/meridian/adapters/sqlite/__init__.py ""
src/meridian/adapters/sqlite/db.py      ""
src/meridian/adapters/sqlite/schema/00_core.sql  "-- schema"
src/meridian/web/__init__.py            ""
src/meridian/web/app.py                 "from meridian.policy.limits import Limits\n\ndef create_app():\n    from meridian.adapters.sqlite import db\n"
tests/__init__.py                       ""
tests/journeys/__init__.py              ""
tests/journeys/support/__init__.py      "from .harness import launch\n"
tests/journeys/support/harness.py       "from meridian.web.app import create_app\n"
tests/journeys/j1/__init__.py           ""
tests/journeys/j1/test_aea_57.py        "from tests.journeys.support import launch\n"
tests/journeys/j2/__init__.py           ""
tests/journeys/j2/test_aea_51.py        "import json\n"
```

Here `j1` reaches `meridian.web.app`, `meridian.policy.limits`, `meridian.adapters.sqlite.db` and its parent packages.
`j2` imports nothing of ours.

---

## 7. Checks

### Tests the implementer writes with the code (all must pass)

**`tests/unit/policy/test_limits.py`**
- `test_values_match_their_sources`: parametrised over 32 `(path, expected, source)` rows. It reads
  `operator.attrgetter(path)(Limits())` and asserts `== expected`, with the source in the assertion message. Rows
  (path → value; source):
  - `turn.deadline_s` → 60 (SDQ-1; DO-4 §2)
  - `turn.turn_deadline_ms` → 60000 (api-con-mapping §0)
  - `turn.still_working_after_ms` → 10000 (api-con-mapping §0; SCR-1)
  - `turn.browser_grace_s` → 5 (DO-3 §2.3 rule 5)
  - `turn.browser_give_up_after_ms` → 65000 (api-con-mapping §0)
  - `turn.max_message_chars` → 2000 (api-con-mapping §0)
  - `admission.max_in_flight` → 30 (SDQ-9)
  - `brakes.tasks_per_turn` → 3, `brakes.tool_rounds` → 2, `brakes.sonnet_calls` → 6 (code-design §4.1; graph-tools
    C-9; models.md cross-topic 3)
  - `identity.code_ttl_s` → 600, `identity.tries` → 3, `identity.max_sends` → 3 (R-15; graph-tools C-9)
  - `booking.max_per_conversation` → 3 (code-design §4.1; R-41)
  - `spend.daily_cap_usd` → 30.0 (models.md §6; M-26)
  - the eleven `web.*` values of §4.2 (web.md §5)
  - the five `context.*` values of §4.2 (graph-core §7)

  Use `pytest.param(..., id=path)`.
- `test_every_field_has_a_source_case`: every dataclass field of every part (via `dataclasses.fields`), plus the two
  properties `turn.turn_deadline_ms` and `turn.browser_give_up_after_ms`, appears as a `path` in the parametrised list.
  A new field without a source row fails here.
- `test_frozen_and_single_literal` (AC-4):
  - for `Limits()` and each part, assigning to every field raises `dataclasses.FrozenInstanceError`;
  - `l.turn.turn_deadline_ms == l.turn.deadline_s * 1000`;
  - parse `limits.py` with `ast`: its top-level statements are only `ImportFrom`, `ClassDef` and the docstring `Expr`,
    with no `Assign` or `AnnAssign`;
  - the module's public names defined in it (`not n.startswith("_")` and `getattr(obj, "__module__", None) ==
    "meridian.policy.limits"`) are all classes; print them.

**`tests/unit/test_import_direction.py`**
- `test_limits_imports_stdlib_only` (AC-5):
  - collect every `Import`/`ImportFrom` in `src/meridian/policy/limits.py` (`ast.walk`) and assert each top-level name
    is in `sys.stdlib_module_names`. `__future__` is in it; if your Python's set lacks it, allow it explicitly;
  - assert no dataclass field in any part is named `cap_s` or ends with `_cap_s`, and no class or field name contains
    `role` (case-insensitive);
  - print the imports seen.
- `test_container_imports_only_policy_limits` (AC-7):
  - walk the **top-level** statements of `src/meridian/web/container.py`. Skip the body of an `if TYPE_CHECKING:` node,
    but collect what it imports separately;
  - assert the `meridian*` modules imported at module level == `{"meridian.policy.limits"}`;
  - assert the TYPE_CHECKING imports == `{"fastapi"}`;
  - do **not** assert anything about imports inside function bodies: hunks import their own modules there once
    their owners fill them, and this test must stay green after that;
  - print what was seen.

**`tests/unit/web/test_container.py`** (import `meridian.web.container as container_mod`; spy by
`monkeypatch.setattr(container_mod, name, spy)` for each of the 27 names, where the spy records
`(name, args, kwargs)`). Keep the expected list as a module-level tuple `EXPECTED_HUNKS` of `(name, "AEA-NN")` in
§4.3 order.
- `test_every_register_stub_present` (AC-6):
  - the module's `register_*` functions (`inspect.isfunction`) equal the names of `EXPECTED_HUNKS` as a set;
  - each docstring contains its `AEA-NN`;
  - with spies installed, `build_container(FastAPI(), stand_in)` calls each exactly once **in `EXPECTED_HUNKS` order**,
    and each call's positional args are `(container, app)`;
  - each **original** function called with a fresh `Container(settings=stand_in, limits=Limits())` and `FastAPI()`
    returns `None` and leaves `build()` with nothing to build;
  - print the list.
- `test_build_and_close_without_adapters` (AC-6):
  - with spies, `c = build_container(app, stand_in)`;
  - every recorded call's `kwargs["settings"] is stand_in` and `kwargs["limits"] is c.limits`, the same object across
    all 27;
  - `isinstance(c.limits, Limits)`, `c.settings is stand_in`, `not c.closed`;
  - `c.get(Key[object]("uow"))` raises `ContainerError` matching `"not provided: uow"`;
  - `c.close()` sets `c.closed`, and a second `c.close()` raises nothing;
  - this test never imports `meridian.config`.
- `test_overrides_reach_register_graph_untouched` (AC-6):
  - with spies and `sentinel = object()`, `build_container(app, stand_in, overrides=sentinel)`;
  - the `register_graph` call has `kwargs["overrides"] is sentinel`;
  - no other call has an `"overrides"` key, and `sentinel` is in no other call's args or kwargs values;
  - a second build without `overrides` gives `register_graph` `kwargs["overrides"] is None`;
  - print `id(sentinel)` and the received id.
- `test_example_pair_one_limits_object` (the ticket's example):
  - with spies, build;
  - the `limits` received by `register_gateway`, `register_spend` and `register_web` is one object, and on it
    `brakes.sonnet_calls == 6`, `spend.daily_cap_usd == 30.0`, `web.chat_turns_per_thread_per_min == 20`.
- `test_provide_get_builds_once_in_any_order`:
  - on a bare `Container`, provide `B` (whose factory calls `c.get(Key[int]("A")) + 1`) **before** `A`
    (factory returns 41, counting its calls);
  - `get(B) == 42`;
  - after `build()`, both stay built and A's factory ran once.
- `test_unknown_duplicate_and_cycle_raise`:
  - `get` of an unknown key → `"not provided: x"`;
  - providing the same name twice → `"already provided: x"`;
  - `A → B → A` → `ContainerError` matching `"provider cycle: A -> B -> A"`;
  - `provide` after `build()` → `"provide after build"`.
- `test_build_runs_starters_after_every_object`:
  - a starter registered first records `c.get(Key[str]("late"))`, where `"late"` is provided afterwards;
  - `build()` runs it once and it sees the value;
  - `on_start` after build raises.
- `test_close_runs_closers_once_newest_first`:
  - closers append `1, 2, 3` → the log reads `[3, 2, 1]`;
  - a failing middle closer still lets the others run and raises `ExceptionGroup`;
  - a second `close()` adds nothing.
- `test_failed_build_closes_what_was_opened`:
  - monkeypatch `register_storage` to `container.on_close(lambda: log.append("closed"))`, and `register_ops` to raise
    `RuntimeError("boom")`;
  - `build_container` raises `RuntimeError("boom")` and `log == ["closed"]`.

**`tests/unit/test_affected_journeys.py`** (uses the §6 fake tree, `main([... "--root", str(tmp), "--list-only"])` and
`capsys`):
- `test_no_journey_yet_prints_zero_and_exits_0`: against the **real** repo root with
  `--files pyproject.toml src/meridian/policy/limits.py --list-only`, the exit is 0 and stdout contains the line
  `0 journeys affected`.
- `test_changed_module_on_the_path_selects_the_journey`: `src/meridian/policy/limits.py` selects only
  `tests/journeys/j1/test_aea_57.py`.
- `test_module_off_every_path_selects_none`: `src/meridian/gates/rules.py` and `docs/x.md` → `0 journeys affected`.
- `test_always_inputs_select_every_journey`: parametrised over `pyproject.toml`, `uv.lock`, `tests/conftest.py`,
  `apps/web/src/main.tsx`, `docs/ux/03-structure/ui-contracts.openapi.yaml`, `docs/data/issued/x.db`,
  `tests/journeys/support/harness.py` → both journeys.
- `test_non_python_file_maps_to_its_package`: `src/meridian/adapters/sqlite/schema/00_core.sql` selects j1 and not j2.
- `test_changed_journey_file_selects_itself`: `tests/journeys/j2/test_aea_51.py` selects only j2.
- `test_relative_import_followed`: changing `tests/journeys/support/harness.py` would hit ALWAYS, so instead assert
  directly that `closure("tests.journeys.j1.test_aea_57", module_index(tmp))[0]` contains
  `tests.journeys.support.harness` and `meridian.adapters.sqlite.db`.
- `test_syntax_error_on_a_path_selects_conservatively`: make j2 import `meridian.bad` and write
  `src/meridian/bad.py = "def ("`; changing `src/meridian/gates/rules.py` then selects j2.
- `test_changed_files_reads_commits_edits_and_untracked`:
  - in a tmp git repo made with `git init -b main`, commit `a.txt` on `main`, `git switch -c work`, commit `b.txt`, edit `a.txt` uncommitted, and
    create untracked `c.txt`;
  - `changed_files("main", tmp) == ["a.txt", "b.txt", "c.txt"]`.
- `test_bad_base_returns_2`: `main(["--base", "no-such-ref", "--root", str(git_tmp)])` returns 2.
- `test_run_invokes_pytest_with_journey_marker`:
  - monkeypatch `tests.journeys.affected.subprocess.call` to record the command and return 0;
  - without `--list-only`, on the fake tree with `pyproject.toml` changed, the recorded command is
    `[sys.executable, "-m", "pytest", "-m", "journey", "tests/journeys/j1/test_aea_57.py",
    "tests/journeys/j2/test_aea_51.py", "-x"]` (passing `-- -x`), and the return is 0.

**`tests/unit/test_skeleton.py`**
- `test_every_planned_package_imports` (AC-1): `importlib.import_module` each of these 20 packages, then print them:
  `meridian`, `meridian.domain`, `meridian.policy`, `meridian.privacy`, `meridian.ports`, `meridian.gates`,
  `meridian.adapters`, `meridian.adapters.sqlite`, `meridian.adapters.models`, `meridian.retrieval`,
  `meridian.services`, `meridian.agent`, `meridian.agent.tools`, `meridian.agent.nodes`, `meridian.agent.specialists`,
  `meridian.agent.prompts`, `meridian.web`, `meridian.web.schemas`, `meridian.web.routes`, `eval.harness`. Also import
  `tests.journeys.j1` … `tests.journeys.j10`.
- `test_journey_and_live_markers_registered` (AC-9, S-4): `pytestconfig.getini("markers")` has one entry starting
  `journey:` and one starting `live:`.
- `test_optional_journey_plugin_is_absent_today` (S-5): `tests.conftest.pytest_plugins == []` while
  `tests/journeys/support/plugin.py` does not exist. **Mark it with
  `@pytest.mark.skipif(Path("tests/journeys/support/plugin.py").exists(), reason="AEA-57 plugin present")`** (use the
  repo-root path from `Path(__file__).resolve().parents[2]`), so it never breaks once AEA-57 lands.

**There is no WP-N worked pair.** The ticket says no customer exchange applies. Its example pair is the test
`test_example_pair_one_limits_object`.

### Existing tests that must stay green

None exist (`tests/` is empty on `9c3e7e7`). `apps/web/**` checks are UX-owned and are not run.

### Commands, cheapest first; stop at the first red

Every command runs from the worktree root with `UV_LINK_MODE=hardlink` exported.

| # | Command | Passing looks like |
|---|---|---|
| G-1 | `uv sync` | exit 0 |
| G-2 | `uv run python -c "import meridian"` | exit 0, no output |
| G-3 | `uv run ruff check` | `All checks passed!` |
| G-4 | `uv run ruff format --check` | `N files already formatted` |
| G-5 | `uv run mypy` | `Success: no issues found in N source files` |
| G-6 | `uv run pytest` | all passed, exit 0. **This is the full suite, on purpose:** this ticket changes the dependencies, the lockfile and `tests/conftest.py`, which reach everything (build-loop-test-scope). It is a few seconds; do not add `-n` |
| G-7 | `uv run pytest -m journey --collect-only -q` | `no tests collected (N deselected)`, exit 0 (AC-9) |
| G-8 | `uv run python -m tests.journeys.affected --base main` | `changed files: <k> (base main)` then `0 journeys affected`, exit 0 (AC-9; the affected-journeys run for this ticket) |
| G-9 | `grep -rnE "^[A-Za-z_][A-Za-z0-9_]*( *:[^=]*)? *= *[A-Za-z_][A-Za-z0-9_.]*\(" src/meridian/` | no output (AC-7 reviewer grep) |
| G-10 | `git diff --stat main -- docs/parked/` and `grep -rnE "(import\|from) +.*parked" src tests` | both print nothing (AC-10) |
| G-11 | `uv tree --depth 1` and `uv tree \| grep -iE "jinja2\|multipart"` | first shows `langgraph v1.2.16`; second prints nothing (AC-2) |
| G-12 | `find src/meridian tests eval -name __init__.py -size +0` | no output |
| G-13 | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` (after commit 2) | no `FAIL` lines |

While iterating, run only the file you are working on, e.g. `uv run pytest tests/unit/web -q`. Never use more than
`-n 2`. Do not start a server and do not bind any port. No test makes a network call or a paid model call.

### Evidence to report back

- Both commit SHAs.
- The outputs of G-1…G-13.
- The `-s` output of `test_every_planned_package_imports`, `test_frozen_and_single_literal`,
  `test_limits_imports_stdlib_only`, `test_container_imports_only_policy_limits`, `test_every_register_stub_present`
  and `test_overrides_reach_register_graph_untouched`. Run them with `uv run pytest <node ids> -s -q`.
- The `pyproject.toml` dependency read-back next to the §4.1 table.
- The record path, with its Level and Blocked-by fields.

---

## 8. Risks and requests

1. **Wave-0 merge order (for the orchestrator).** AEA-02, 03, 04, 05 and 06 have no `pyproject.toml`, test config or
   lock until AEA-01 is on main. They cannot run `uv run pytest` before then. **Recommend merging AEA-01 first in wave
   0.** If a sibling merges first with its own `pyproject.toml`, `uv.lock` or `tests/conftest.py`, that is a
   collision with this ticket's owned files (slice plan §3), and the sibling should drop them.
2. **Empty-marker overlap with siblings.** Siblings may add the same `__init__.py` markers. Empty files merge cleanly.
   A marker with content conflicts. Siblings should keep markers 0 bytes.
3. **Context files edited by AEA-08 (lane::direct, wave 0).** It edits `area-map.md` and may touch `code-design.md`
   and the ICM file in the same wave. Step 12 changes only the A0 row, one preamble sentence, one ICM row with its
   reconciled line, and code-design line 6. If a textual conflict appears at merge, keep both edits. Separately,
   `.claude/README.md` still says "No backend code exists yet". That sentence is AEA-08's or the orchestrator's to
   update (not owned here).
4. **`Settings` is typed `Any` in the container.** AEA-02's `config.py` may not be on main when AEA-01 merges, so
   importing it, even under `TYPE_CHECKING`, would fail mypy. Hunks narrow it themselves
   (`settings: Settings = container.settings`, or a typed parameter in their own helper). `overrides` is `Any` for the
   same reason (it is AEA-23's `ContainerOverrides` in `web/app.py`, which imports the container). An optional
   follow-up after AEA-02 and AEA-23 merge could tighten both annotations under `TYPE_CHECKING`. Nothing depends on it.
5. **Shared primitive defined here, worth a glance before the AEA-10 and AEA-23 plans.** The `Container` API (`Key`,
   `provide/get`, `on_start`, `on_close`, `build`, `close`) is this ticket's engineering choice. No addendum specifies
   it. It is needed because the 29 ↔ 30 constructors cross hunks in both directions (cases.md §5–§6) and the watchdog
   (32) needs the ledger (26) from a later hunk. Consumers should:
   - provide objects through factories;
   - start threads and sweeps in `on_start` (AEA-30's scheduler, AEA-32's watchdog, AEA-40's `fail_running` sweep);
   - release resources in `on_close`;
   - never call `get` directly in a hunk body for an object another hunk provides.
6. **Hunks run inside the app lifespan.** Starlette has already built its middleware stack by then. A hunk may include
   routers, mount files and set `app.state`, but **cannot add middleware** (Starlette raises once the app has
   started). Middleware belongs in `create_app` (AEA-23). AEA-49 should import its mount function under another name
   inside the hunk, e.g. `from meridian.web.frontend import register_frontend as mount_frontend`, because the hunk is
   also called `register_frontend`.
7. **Untyped third-party packages.** If `fastembed` or `langfuse` ship no type information, their importers (AEA-33,
   AEA-19) add `# type: ignore[import-untyped]` on that import line in their own file. Do not add a mypy override to
   `pyproject.toml` now (strict mode warns about unused override sections).
8. **Later dependency lines.** AEA-58 (`pytest-playwright`) and possibly AEA-02 (`pydantic-settings`, if it reads env
   through it) each add one line plus a regenerated lock at their merge, and that merge runs the full suite (slice plan
   §3). This plan does not add them: the ticket's item 1 does not name them.
9. **No spec gaps and no contract problems found.** No signed contract changes. Decisions D-4…D-15 are unaffected.

---

## 9. Readiness

**READY.** No product decision is needed, no signed contract changes, and nothing blocks it (`blockedOn`: none). Wave
0 has no internal edges for this ticket.

**Gates:** none (no human, paid, live or UX gate).
