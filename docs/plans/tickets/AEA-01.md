## [AEA-01] foundation: scaffold, limits, composition-root stubs

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

User story: none applies directly; this is the shell every story's code sits in.
Example pair: none is a customer exchange. Its nearest observable behaviour: the gateway (AEA-20) asks for
`limits.brakes.sonnet_calls` and gets 6; the ledger (AEA-26) is built with `daily_cap_usd=limits.spend.daily_cap_usd`
and gets 30.0; the rate limiter (AEA-23) gets `limits.web.chat_turns_per_thread_per_min` = 20. No consumer holds a
second literal for any of them (merge-clashes MC-22).

The repository's Python shell, so every later ticket only adds its own modules. **`config.py` / `Settings` is not this
ticket's**: it moved to AEA-02 (slice plan row AEA-02 and §2; merge-clashes MC-21; graph-core §12, GRC-22).

1. **`pyproject.toml` and `uv.lock`, rewritten** to hold every dependency the design names, so no later ticket edits them
   (slice plan §3): FastAPI and its server; Pydantic; LangGraph pinned to **1.2.16** (DO-3 §2.2) with its SQLite
   checkpointer (`SqliteSaver`, DO-3 §2.1, §4.3); the sync `anthropic` SDK and `httpx` (DO-3 §2.1, §4.3); `fastembed` for
   `BAAI/bge-small-en-v1.5` (PRD R-11; stage7/data.md §3 `EMBEDDING_MODEL`); the Langfuse Python SDK v5
   (`mask_otel_spans`, DO-6 *Content and redaction*); `anyio` (`CapacityLimiter`, DO-3 §2.3; web.md §4
   `get_stream_poll_limiter`); a PDF parser for the fee PDF (R-9; the parked file uses `pypdf`). Dev: pytest, ruff, one
   type checker (the planner names it), and **`jsonschema>=4.18` and `pyyaml`** for AEA-23's shared OpenAPI response
   check (stage7/web.md §13; WEB-24). The parked file's `jinja2` and `python-multipart` go: there are no templates (slice
   plan §0).
2. **Package skeleton:** the directories of DO-3 §3 under `src/meridian/` (and `eval/`, `tests/` per DO-3 §9) with their
   package markers only. No other ticket's module is created here; in particular no `config.py`, no `domain/*` file and
   no `adapters/sqlite/repos_*.py` (AEA-02).
3. **`policy/limits.py`: one frozen `Limits`** (merge-clashes MC-22; DO-4 `GraphDeps.limits`, `ModelGateway(…, limits:
   Limits)`), standard library only (DO-3 §4.1 "depends on: none"), no module-level constants. Its fields, each a
   frozen dataclass whose definition is owned by the cited addendum:
   - turn deadline **60 s** [Decided SDQ-1] (DO-4 §2 `TurnLimits.deadline_s`) and admission **30** turns in flight
     [Decided SDQ-9] (code-design §4.1 `TurnLimits`, `Admission`). Role call caps are **not** here: they are
     `RoleSpec.cap_s` in AEA-02's `ModelSettings` defaults (DO-4 §12; graph-core §12), one literal each;
   - `brakes`: 3 tasks per turn, **2 tool rounds**, **6 Sonnet calls** per turn, all proposals (code-design §4.1
     `Brakes`; graph-tools C-9; models.md cross-topic 3);
   - `identity: IdentityLimits(code_ttl_s=600, tries=3, max_sends=3)` (graph-tools C-9, §5; R-15);
   - the booking cap, 3 per conversation, proposal (code-design §4.1; DO-4 §1 `FailureCounters.bookings`; `ToolErrorCode`
     `booking_cap`, graph-tools §1); its field name is stated in the plan;
   - the CON-1 timing values under their wire names: `turn_deadline_ms` 60000, `still_working_after_ms` 10000,
     `browser_give_up_after_ms` 65000, `max_message_chars` 2000 (api-con-mapping §0 *Timing constants*; served by
     AEA-40's `SessionService`, web.md §14), the 60000 derived from the one 60 s value, not typed twice;
   - `spend: SpendLimits(daily_cap_usd=30.0)` [T] per America/Chicago day (stage7/models.md §6, the one literal; DO-7 M-26);
   - `web: WebLimits` with web.md §5's eleven values, each keeping its `[A]` comment and the measurement that replaces it
     (WEB-2, WEB-4, WEB-5, MC-14): `chat_turns_per_thread_per_min` 20, `chat_turns_per_session_per_min` 600,
     `chat_turns_per_ip_per_min` 600, `reads_per_session_per_min` 120, `reads_per_ip_per_min` 240, `login_rejects_per_ip`
     10, `login_reject_window_s` 600, `resets_per_ip` 10, `reset_window_s` 600, `login_session_lifetime_s` 43_200,
     `reset_wait_s` 5;
   - `context: ContextLimits` (graph-core §7, GRC-9, GRC-14): `window_turns` 10, `window_line_chars` 600,
     `window_total_chars` 8_000, `planner_lines` 6, `planner_line_chars` 400, each `[A]`.
   Proposal and `[A]` values carry a comment naming them so. **Not here:** the CON-3/CON-21 stream constants
   `STREAM_POLL_S` and `STREAM_HEARTBEAT_S` (web.md §11, AEA-41's route file) and the `CapacityLimiter(4)` (web.md §4,
   AEA-23).
4. **`web/container.py`:** the one composition root (DO-3 §2.1). It creates the one `Limits`, receives the built
   `Settings` from its caller (the app lifespan in `web/app.py`, AEA-23; `Settings` is AEA-02's, built once, DO-3 §2.1)
   and passes both to one `register_<area>()` stub per registering ticket, each a no-op today: the slice plan §3 list
   (AEA-10, 17, 18, 19, 20, 22, 23, 26, 27, 28, 29, 30, 31, 32, 33, 40, 41, 42, 43, 44, 45, 46, 47, 48, 53), plus
   **`register_frontend` (AEA-49; web.md §12, WEB-29)** and `register_graph` (completed by AEA-51). Where an addendum
   names the function, that name is used (`register_demo` AEA-30, cases.md §6; `register_ops` AEA-32, cases.md §8;
   `register_frontend`; `register_graph`); the others are named by area in the plan with the ticket in a comment. The
   AEA-22 and AEA-33 stubs stay empty unless their owners need one: their tools are wired in `register_graph`
   (graph-tools §1; data.md §4). The builder also takes `overrides` from its caller and hands it to `register_graph`
   untouched, exactly as it handles `Settings` (no import; `ContainerOverrides` is AEA-23's, `web/app.py`, web.md §15)
   (R-W-8). It closes everything it built on shutdown. No module-level clients. At run time it
   imports no other ticket's module, so wave 0 keeps no internal edges (slice plan §2).
5. **`tests/conftest.py`** (shared fixtures only; tickets keep their own fixtures in their own test folders; `temp_sqlite()`
   is AEA-10's, `tests/fixtures/sqlite.py`), lint, format and type-check configuration.
6. **The journey gate's skeleton** (slice plan §1 row AEA-01 and §0a; `.claude/rules/integrated-journeys.md`): the
   `tests/journeys/` package skeleton (no `support/`, which is AEA-57's, and no `browser/`, AEA-58's), the registered
   `journey` pytest marker, and the one command the merge gate runs for affected journeys (it selects the journeys whose
   path imports or calls a changed module, route, prompt, schema or frontend build input, `build-loop-test-scope.md`
   AEA addition; how it maps a diff to journeys is the planner's, stated in the plan). With no journey written yet it
   selects none and says so (AC-9).

**Settled (Innocent, 2026-10-21: "d2 set aside"):** the parked first-attempt tree was moved, unedited, to
`docs/parked/2026-10-21-first-attempt/` (`pyproject.toml`, `uv.lock`, `src_meridian/` = the old `src/meridian/`). It is
reference only: **read and copied, never imported**. `src/` is empty, so this ticket creates `pyproject.toml` and the
`src/meridian/` skeleton fresh. AEA-05, AEA-13 and AEA-16 read the old files at the new path for shapes (DO-3 §2.4;
data.md DAT-11). `data/kb_transcriptions/` and `var/` stay where they are.

### Source

- DO-3 §2.1 (layers, composition root, no singletons), §2.2 (LangGraph 1.2.16), §2.3 (60 s, 30 in flight), §2.4 (parked
  code), §3 (module tree), §4.1 (`policy/limits.py` row: `TurnLimits`, `Admission`, `Brakes`, `IdentityLimits`, booking
  cap), §8 collision map, §9 (test layout)
- DO-4 §2 (`TurnBudget` uses `TurnLimits.deadline_s`), §12 (`RoleSpec.cap_s`; `ModelGateway(…, limits: Limits)`), §14
  (`GraphDeps.limits`)
- stage7/models.md §6 (`SpendLimits`), cross-topic 3; stage7/web.md §5 (`WebLimits`), §12 (`register_frontend`), §13
  (dev dependencies); stage7/graph-core.md §7 (`ContextLimits`); stage7/graph-tools.md §5, C-9 (`brakes.tool_rounds`,
  `IdentityLimits`); stage7/data.md §3, §4 (no `register_` hunk for AEA-33); stage7/cases.md §6, §8 (`register_demo`,
  `register_ops`)
- Decision ledgers: merge-clashes MC-14, MC-21, MC-22; web WEB-2, WEB-4, WEB-5, WEB-24, WEB-29; graph-core GRC-9, GRC-14
- api-con-mapping §0 (*Timing constants*)
- stage7/web.md §15 (`ContainerOverrides` passed through the container); residual ruling
  `docs/plans/7b-decisions/residuals-web.md` R-W-8
- Slice plan §0a (journey map, merge gate); `.claude/rules/integrated-journeys.md`; `.claude/rules/build-loop-test-scope.md`
  (AEA addition); `docs/plans/ux-join/backend-amendments.md` §3 (AEA-01 row, pattern *special*)
- PRD R-15 (identity limits), R-41 (abuse limits, booking cap, spend cap, brakes), §5 (load, spend)
- Slice plan §1 row AEA-01, §2 (Wave 0 keeps no internal edges), §3 rows `pyproject.toml`, `web/container.py`,
  `tests/conftest.py`
- **Brief check:** serves "Production-thinking expected: system should be able to run unmanned for a month, failures
  should be observable" (every limit in one place and one composition root make the later failure handling
  configurable and testable); touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] A clean checkout installs and every package of DO-3 §3 imports — verify: `uv sync` then `uv run python -c "import meridian"` and `uv run pytest tests/unit/test_skeleton.py::test_every_planned_package_imports` — evidence: both commands exit 0; the test lists each package it imported.
- [ ] AC-2 [invariant] The dependency set names every dependency in *What to build* item 1 (including `jsonschema>=4.18` and `pyyaml` as dev dependencies), LangGraph resolves to 1.2.16, and neither `jinja2` nor `python-multipart` is present — verify: read-back of `pyproject.toml` and `uv tree --depth 1` — evidence: the plan's dependency table matches the read-back line for line.
- [ ] AC-3 [invariant] `Limits` holds the decided and proposed values exactly: deadline 60 s, admission 30, brakes 3 / 2 / 6, identity 600 s / 3 / 3, booking cap 3, CON-1 values 60000 / 10000 / 65000 / 2000, `spend.daily_cap_usd` 30.0, the eleven `web` values and the five `context` values — verify: `tests/unit/policy/test_limits.py::test_values_match_their_sources` (one parametrised case per field, each citing its source section) — evidence: every case passes.
- [ ] AC-4 [invariant] `Limits` and each part are frozen and there is one literal per value: assigning to any field raises, `turn_deadline_ms` equals the deadline in seconds × 1000, and no module-level numeric constant exists in `policy/limits.py` — verify: `tests/unit/policy/test_limits.py::test_frozen_and_single_literal` — evidence: passes; the module's public names are printed (classes only).
- [ ] AC-5 [invariant] `policy/limits.py` imports only the standard library, and role caps are absent from it (they are `RoleSpec.cap_s`, AEA-02) — verify: `tests/unit/test_import_direction.py::test_limits_imports_stdlib_only` — evidence: passes; the scan lists every import it saw.
- [ ] AC-6 [invariant] The container builds and closes with every `register_<area>()` stub in *What to build* item 4 present exactly once (slice plan §3 list + `register_frontend` + `register_graph`), all no-ops, each called with the one `Limits` and the `Settings` it was given; an `overrides` object given to the builder reaches `register_graph` as the same object and no other stub receives it, and with none given `register_graph` receives `None` (web.md §15, R-W-8) — verify: `tests/unit/web/test_container.py::test_every_register_stub_present`, `::test_build_and_close_without_adapters` (a stand-in settings object, no `config.py` import) and `::test_overrides_reach_register_graph_untouched` (a stand-in object, no `web/app.py` import) — evidence: the stub list in the test equals the item-4 list; the three pass; the identity check on `overrides` printed.
- [ ] AC-7 [negative] The container imports no other ticket's module at run time and no module-level client or settings singleton exists anywhere under `src/meridian/` — verify: `tests/unit/test_import_direction.py::test_container_imports_only_policy_limits` plus the reviewer's grep for module-level instantiation in `src/meridian/` — evidence: test passes; grep output empty.
- [ ] AC-8 [invariant] The fast gates pass on the skeleton, cheapest first — verify: `uv run ruff check`, `uv run ruff format --check`, the chosen type check, `uv run pytest` — evidence: four green outputs in the implementer's report (a dependency change reaches everything, so this ticket's merge runs the full suite, rule `build-loop-test-scope`).
- [ ] AC-9 [journey] The journey gate exists before any journey does: the `journey` marker is registered, `uv run pytest -m journey --collect-only -q` exits 0 on the skeleton, and the affected-journey command run on this diff selects 0 journeys, prints "0 journeys affected" and exits 0; the record `docs/testing/journeys/YYYY-MM-DD-AEA-01.md` states level `mock-tested` and *Blocked by* AEA-57 (`integrated-journeys.md` §4) — verify: both commands and the record — evidence: their output; the record's Level and Blocked-by fields.
- [ ] AC-10 [invariant] The parked first attempt stays reference-only: `docs/parked/2026-10-21-first-attempt/` is unchanged by this ticket and no file under `src/` or `tests/` imports from it — verify: `git diff --stat -- docs/parked/` and `grep -rnE "(import|from) +.*parked" src tests` — evidence: both empty (Innocent's decision, 2026-10-21: set aside).
- [ ] AC-11 [regression/context] Context updated in the same change — verify: diff — evidence: `.claude/reference/area-map.md` A0 row notes `policy/limits.py`, `web/container.py`, `tests/conftest.py`, `pyproject.toml` planned → actual with the commit (and no longer lists `config.py` under this ticket); `.claude/state/icm-progress.md` row *Physical scaffold* provisional → established with the commit; DO-3 §3 status line notes these paths built.

### Observability

N/A — this ticket adds no entry point, writes no record and emits no span; the container's stubs register nothing yet
and `Limits` is constants. A reviewer could disagree only on the composition root: it is the place WF-13's start-up
runs, but the deploy record and its capture check (CAP-9) are AEA-50's, and the trace sink is wired by AEA-19 and
AEA-51.

### Evaluation

N/A — no behaviour here is scored by E-1…E-8; the limits it declares are exercised by their consumers' tests and by E-8's
load re-measure at Stage 9, whose expected-answer authority is the 12.5 s line (DO-5 *Acceptance conditions*), not this
module.

### Metrics

- References: M-26 (daily spend against the cap): `spend.daily_cap_usd` 30.0 is the one literal the ledger and the alert
  evaluator receive (models.md §6; cases.md §8). M-23 is bounded by the 60 s deadline declared here.
- Acceptance conditions: the declared values equal the approved ones (Q-061 $30; Innocent 2026-10-21 Chicago day; SDQ-1
  60 s; SDQ-9 30) and every consumer receives them from the container, so M-26 stays computable against one cap; no
  target is computed here.

### Blocked by

None (slice plan wave 0). No edge to AEA-02 or AEA-04: `Limits` imports nothing, and the container takes `Settings`
from its caller instead of importing `config.py`.

### Agent handoff

- Area / owner: A0 Foundation (area map row A0; DO-3 §8).
- Contracts and shared surfaces: produces `Limits` (`policy/limits.py`) for AEA-20, 21, 23, 26, 27, 28, 32, 34, 35, 37,
  40, 44, 51, 53 (each receives its field from the container); the `register_<area>()` stubs each listed ticket fills
  (only its own hunk, slice plan §3); `pyproject.toml` / `uv.lock` (a later addition is one line plus a regenerated lock
  at merge, slice plan §3); `tests/conftest.py`; the `tests/journeys/` skeleton, the `journey` marker and the
  affected-journey command every later ticket's `[journey]` criterion and the merge gate use; the container's
  pass-through of `overrides` to `register_graph` (AEA-23 defines `ContainerOverrides`, AEA-51 reads it, R-W-8). Must
  not edit: `tests/journeys/support/` (AEA-57), `tests/journeys/browser/` (AEA-58), `config.py`, `domain/*`, `ports/*`,
  `adapters/sqlite/repos_*.py` (AEA-02), `privacy/redact.py` (AEA-04), `policy/texts.py` (AEA-03), `apps/web/**`,
  `docs/ux/**`, the OpenAPI file.
- Scope boundary / refusal: no service, adapter, repository, schema or route body; no database access; no `Settings`;
  no deletion or overwrite of parked code until decided.
- Wave and gates: wave 0; no gate (the parked-tree decision is settled above).
- Lane: build-loop — it changes dependencies, the lockfile, configuration and test setup, all of which code and tests
  read (`ticket-lanes`).
- Risk: None (slice plan; the secrets moved to AEA-02 with `Settings`).
- Entry points added or changed: None.
