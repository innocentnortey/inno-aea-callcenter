# Plan — [AEA-51] integration A: the customer path end to end

**Status:** planned (READY as a plan). **Pass 1 is buildable now** (Parts A, B, C and four tests, §5 *Two passes*);
**pass 2 is BLOCKED-ON** AEA-39, AEA-21b and AEA-19-F1 (and AEA-40-F1 for one test), §9.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/51 (spec copy:
`docs/plans/tickets/AEA-51.md`) · **Base revision:** `main` at `b68df7e` (refresh 5, 2026-10-21; refresh 4 at `f466ff7`,
refresh 3 at `c9b17ea`, refresh 2 at `2ec19ad`, first written at `0dc2ad4`)
**Planner:** Opus 5.5 (`claude-opus-5-5`) · **Implementer:** `fanout-implementer` on Sonnet · **Lane:** `lane::build-loop`
· **Risk label:** none in the slice plan (see §8 R-9 for the orchestrator's confirmation) · **Wave:** 3

**Refresh 5 (2026-10-21, `main` at `b68df7e`, 63 commits after `f466ff7`).** Read this box first; everything below it
was re-checked against `main` and kept where it still holds. Where this box and anything later differ, this box wins.

1. **Merged since refresh 4:** AEA-35b (`3725c90`: `SpecialistTask`, `KnowledgeSlice`, `AccountSlice` in `domain/tools.py`,
   Innocent's home ruling, graph-tools.md *Home note*), AEA-36 (`c378698`: front node), AEA-35 (`1ce98c4`:
   `agent/specialists/{specs,runner}.py`, `agent/prompts/specialists.py`), AEA-37 (`8d025b7`: plan node,
   `agent/prompts/routing.py`), AEA-58 (`eb51ba4`), AEA-45 (`1a6712a`: staff cases API including CON-13
   `applyCaseAction`), AEA-53 (`b9be4dc`), FIX-W1 (`38d3884`: the contract driver bounds stream drives) and AEA-52
   pass 1 (`55d9adf`). All leave §9. Every blocker in the ticket's *Blocked by* is now on `main` **except AEA-39**.
2. **Names re-checked on `main`** (copied into §4.2, §4.3, D1): `SpecialistRunner(*, gateway, transcript, dispatcher,
   specs: Mapping[SpecialistKind, SpecialistSpec], brakes, trace)` keeps every argument as a public attribute (its own
   comment names AEA-51); `SPECS: Final[Mapping[SpecialistKind, SpecialistSpec]]` with keys `"knowledge"`, `"account"`,
   `"scheduling"` and tool kinds `{KB_SEARCH}`, `{ACCOUNT_READ}`, `{SLOT_SEARCH, BOOK, MOVE, CANCEL, CHANGE_REQUEST}`;
   the report tool is `REPORT_FACTS_TOOL = "report_facts"` (`agent/prompts/specialists.py`); tool spans are named
   `"tool:" + record.name`, or `"tool:unknown"` when the record has no kind; `DANGER_FIELD = "danger_level"` with
   options `"normal"`, `"burning_unclear"`, `"danger"`; planner choice fields `knowledge`, `account`, `scheduling`,
   `handoff`, `topic` (= `PlannerChoices`). `tests/journeys/support/steps.py` `NEED_OWNERS` maps `reply_composer` and
   `run_graph` to AEA-51, the two key names this hunk provides.
3. **Unchanged since `f466ff7`** (`git diff` empty): `web/app.py`, `web/deps.py`, `services/turn.py`, `config.py`,
   `agent/graph.py`, `agent/context.py`, `tests/journeys/support/`, `eval/harness/`, `tests/api/openapi_check.py`,
   `tests/fakes/`. `register_graph` is still the docstring-only no-op (`container.py` lines 1071–1077; file 1,134 lines).
4. **Still missing:** AEA-39 (ledger `blocked` only because it ran before AEA-35 merged; re-run pending): `act.py`'s
   `run_specialist`, `escalation` and `handoff` are AEA-21 stubs that raise `NotImplementedError`, and `route_after_gates`
   sends a chat-words person request to `handoff`. The three follow-ups are **still not cut** (no ticket file, ledger row
   or branch): AEA-19-F1 (`register_tracing` still provides `Key("trace")` itself, §8 R-1), AEA-21b (`compose.py` builds
   none of the five card blocks, `grep -c` 0, §8 R-13), AEA-40-F1 (`allow_turn()` line 318 before `parse_intake` line
   322, §8 R-14).
5. **New: two passes** (§5 *Two passes*, §9). Part A's imports are all on `main` and the act stubs run only when a turn
   reaches them, never at build, so Part A (without `Key("run_graph")`), B, C and four tests (AC-4, AC-5, AC-2 parts a–b, AC-1 part b and the
   structural part a) are buildable now. Binding `reply_composer` alone turns CON-1 from 500 into 201 on the real app,
   which several merged tickets wait on (R-21).
6. **New request received from AEA-52** (its plan §8 R-3): publish the WP-7 and WP-4 conversations as importable
   drivers. Met without a new file (R-19): `tests/graph/worked_pair_scenarios.py::wp7` and `::wp4`, with
   `ScenarioResult.case_refs` added (D2), opened on `tests.integration.customer_support.open_customer_run`. These names are
   now a published surface.
7. **Changed in place:** D1 `NORMAL = classifier("normal")` and `report()` uses `REPORT_FACTS_TOOL`; D2 `case_refs`;
   §2.2 makes AEA-52's integration helpers read-only and never imported; H3 appends a new ICM row (the file is
   append-style) and edits both copies of the duplicated A7a and A8 area-map rows (R-20); §7 known reds refreshed and the
   full suite wrapped in `timeout`; A0 split by pass. Disk: 15 GB free on `/` (84 %).

**Refresh 4 (2026-10-21, `main` at `f466ff7`, 22 commits after `c9b17ea`).** Kept as history; items 2, 3 and 6 are
superseded by refresh 5.

1. **Merged since refresh 3:** AEA-30 (`cf8fd78`, merge of `e5c4ce4`: `services/demo.py`, `services/scheduler.py`,
   `register_demo`) and AEA-40 (`f466ff7`: `services/session.py`, `services/turn.py`, `web/routes/chat.py`,
   `register_chat`). The ledger row for AEA-40 still says `blocked`, but the merge commit is on `main`. Both leave §9.
   `register_demo` provides exactly the keys §4.3 named (`Key("demo_clock")` = `DemoClock`, `deps.DEMO_SERVICE`,
   `Key("scheduler_job")`, `Key("scheduler_thread")`). `register_chat` provides `deps.TURN_SERVICE` and
   `deps.SESSION_SERVICE`. It reads `Key("ledger")` and `Key("trace")` **eagerly** in the `TurnService` factory
   (`container.py` lines 803–804), and `Key("run_graph")`, `deps.REPLY_COMPOSER`, `Key("demo_clock")` and
   `deps.DEMO_SERVICE` lazily. §4.1 gains the merged names (block "merged after `c9b17ea`").
2. **Still not on `main`:** AEA-35 and AEA-39 (NEEDS-DECISION: where the specialist task types live), AEA-36 and AEA-37
   (blocked; branches exist) and AEA-45 (blocked; a resume run is planned). `front.py`, `plan.py` and `act.py` are still
   AEA-21's `NotImplementedError` stubs, and `agent/specialists/` holds only `__init__.py`.
3. **The two follow-ups are still not cut** (no ticket file, ledger row or branch). AEA-19-F1 (§8 R-1): `register_tracing`
   (`container.py` lines 294–344) still provides `Key("trace")` itself. AEA-21b (§8 R-13): `compose.py` still builds none
   of the five card blocks (`grep -c` = 0).
4. **R-14 is now a follow-up on merged code.** AEA-40 merged with `allow_turn()` at `services/turn.py` line 318, before
   `parse_intake` at line 322. That is the order DO-4 §14 and stage7 web.md give ("admission checks `ledger.allow_turn()`
   only"). DO-4 §11 says "safety and CON-4 still work" at our cap. The ticket's *Agent handoff* already rules on this
   conflict: AC-24's safety half is `blocked-on AEA-40`. Because AEA-40 is merged, that blocker is now a follow-up,
   **AEA-40-F1** (to be cut; §8 R-14). AC-24's notice and CON-4 halves wait on nothing new, and nor does anything else.
5. **Changed in place by this refresh:**
   - AC-5 compares CON-1's `demo_clock.label` with `format_clock(DEMO_START)[0]` (`format_clock` returns
     `(label, date_label)`), and the greeting with `render(TextId.GREETING)`.
   - AC-24 and J-9 read the stored reasons `TurnService._reject` writes: `BUSY` and `RATE_LIMITED` give
     `degrade_reason = 'rate_limit'`, and `SPEND_CAP_REACHED` gives `'spend_cap'`. Each has `outcome = 'degraded_handoff'`
     and `trace_export = 'off'`.
   - AC-24's safety half moves into its own test, `test_spend_cap_safety_still_answered`, skipped while AEA-40-F1 is
     not on `main` (§5 F3).
   - AC-1's `run_graph` check stays behavioural, because `register_chat` hands `TurnService` a forwarding closure, not
     the compiled graph's object.
   - Check 5's baseline is measured: `mypy` reports `Success: no issues found in 468 source files` at `f466ff7` (the 24
     errors in the AEA-30 ledger row are gone).
6. **Startable now (orchestrator's choice, §9).** Part B (AC-3) needs only the two adapters, which are on `main`. Part C's
   two support modules need only AEA-57's harness and AEA-23's overrides. Part A step 7 imports `SpecialistRunner` and
   `SPECS` (AEA-35), so Part A and everything from Part D on wait for §9.
7. **Other numbers:** `web/container.py` is 1,082 lines (R-3); 16 GB free on `/` (R-12).

**Refresh 3 (2026-10-21, `main` at `c9b17ea`, 55 commits after `2ec19ad`).** Kept as history; items 2 and 3 are
superseded by refresh 4 items 1 to 4.

1. **Merged since refresh 2:** AEA-29 (`ef561fc`), AEA-34 (`dd31214`), AEA-38 (`042ad35`), AEA-43 (`03f5334`), AEA-24
   (`7fddbf5`), AEA-50 (`67c5ffe`) and AEA-54 (docs). `register_cases` on `main` provides exactly the keys §4.3 named
   (`case_service`, `handoff_service`, `brief_assembler`) and reads `reply_composer`, `demo_clock` and `demo_service`
   only when a method runs, so the A2 order holds. Every other surface §4.1 copies is unchanged since `2ec19ad`
   (`git diff --stat 2ec19ad..c9b17ea` over them shows only AEA-59's `tests/contract/cases/demo.py`).
2. **Still not on `main`** (`.claude/state/build-ledger.md`): AEA-30 (blocked: its send-back failed), AEA-35 and AEA-39
   (NEEDS-DECISION: where the specialist task types live), AEA-36 and AEA-37 (blocked), AEA-40 (NEEDS-DECISION after
   review; branch head `5a4cdf0`, Parts A and B built), AEA-45 (blocked). On `main` the front, plan and act nodes are
   still AEA-21's `NotImplementedError` stubs, and `agent/specialists/` holds only `__init__.py`.
3. **The two follow-ups are still not cut.** AEA-19-F1 (§8 R-1): `register_tracing` still provides `Key("trace")`
   itself, and AEA-40's `register_chat` at `5a4cdf0` still reads it eagerly (`c.get(trace_key)` in the `TurnService`
   factory). AEA-21b (§8 R-13): `compose.py` builds none of the five card blocks. **R-14 still holds** at `5a4cdf0`
   (`services/turn.py` line 318 `allow_turn()` runs before line 322 `parse_intake`).
4. **Changed in place by this refresh:**
   - **F2 (AC-49…AC-51)** now drives AEA-24's runner in the test process through `eval.harness.cli.main(argv,
     deps=HarnessDeps(...))` with a temporary freeze file, the way AEA-24's own `run_cli` helper does.
     `eval/harness/freeze.json` does not exist on `main` and `run` takes no `--freeze-file`, so the old subprocess plan
     would always exit 3 (`not_frozen`). `eval/harness/deps.py` documents `HarnessDeps` as "a seam AEA-51 relies on".
   - **New PA-5** (open finding 1 of the second wave-2 seam audit, `.claude/state/resume.md`): AC-13's test also
     proves that a fabricated brief quote never reaches the stored brief.
   - AC-48 reads `events.type` (the column is `type`, not `kind`). AC-49's span check compares the masked `run_id`.
   - Check 7 names the two known reds on `main` that are not this ticket's (§7).
   - `web/container.py` is 942 lines (R-3); disk is 16 GB free (R-12).

**Refresh 2 (`2ec19ad`)** found R-13 and R-14, copied the merged names into §4.1, made `register_graph` return early
without a web shell (PD-15), read citations from `TextBlock.sources`, named the three account tools (there is no
appointments read tool), and required `retry-after` on AC-3's Anthropic 429 row. All of that still holds.

---

## 1. Goal and sources

### Goal (from the issue's *What to build*)

> Wave 2 built every customer-path piece against DO-4 signatures with doubles. This issue **wires the real objects
> together and proves every cross-ticket seam at the real entry point**: the HTTP API (CON-1, CON-2, CON-4, CON-5, CON-6)
> of the app `create_app()` builds through `web/container.py`.

Concretely, the slice delivers four things:

1. **The `register_graph` hunk** of `src/meridian/web/container.py`: it builds the model adapters (or takes the test
   overrides), the `ModelGateway`, the retrieval index, the tool registry and dispatcher, the `SpecialistRunner`, one
   `ReplyComposer`, `GraphDeps`, the graph compiled with the `SqliteSaver` checkpointer, and binds `run_graph`, which
   `TurnService` (AEA-40) already reads lazily as `Key("run_graph")`.
2. **`tests/contract/test_model_ports_contract.py`**: one contract both model adapters honour (AC-3).
3. **Tests through the running server** (real app, disposable DB copy, scripted model at the provider boundary): the
   first dev set (WP-1…WP-8, WP-4F, DANGER, NODANGER), CAP-1/2/3, the relayed turn, failure paths, load and
   eval-runner tag checks.
4. **Journeys J-2, J-3, J-4, J-5, J-9** and their evidence record, plus the context rows (AC-52).

### Context (why this ticket exists now)

Every wave-2 ticket built against doubles (slice plan §0 rule 1). Riverside's lesson (rule `integrated-journeys.md`) is
that parts can pass while the real path fails. This ticket is the first place the compiled graph, the real services and
the HTTP API run together. If a seam does not connect, the fix belongs to its owner as a small follow-up; this ticket
never patches a sibling in place.

### Sources (read by the planner; the implementer reads only what each step names)

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-51.md` | AC-1…AC-52, the seam table (21 rows), owned files, residual rulings R-W-8, R-G-6, R-G-13, R-G-17 |
| Slice plan | `docs/plans/slice-plan.md` §0 (rules 1–3), §0a (journey map; "AEA-51 switches on the strict mode"), §1 row AEA-51, §3 collision map | Owns only the `register_graph` hunk; tests in `tests/contract/` (cross-adapter file), `tests/capture/` (CAP-1…3), `tests/journeys/j{2,3,4,5,9}/test_aea_51.py` |
| Sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | D-8 (signing in again starts a fresh chat: a restart test must carry the cookie), D-9 (CON-4 builds no brief), D-13 (`ContainerOverrides.wall_clock`), **D-14: DAT-1, CAS-16, GRC-3 stay on their recommended option A** (so the ticket's three "Awaiting Innocent" notes are settled: build on A) |
| Code design (DO-3) | `docs/design/code-design.md` §1 (WP-4F turn), §2.1–§2.3 (rule 1: no transaction across a model call), §4.3, §5.4 (recursion limit 25), §6 (seams S-1…S-24), §9 (test folders) | Dependency direction; the seam table AC-52 annotates |
| Component contracts (DO-4) | `docs/design/contracts/internal-components.md` §11 (failure → customer), §12 (ports, gateway), §13 (ports, case service), §14 (service signatures, `TurnService.run_turn` steps) | Wiring and expected failure behaviour |
| Addenda (win over DO-4) | `stage7/models.md` §1–§7; `stage7/graph-core.md` §2, §4, §5, §6, §12, §13; `stage7/graph-tools.md` §1, §2, §5, §6; `stage7/graph-nodes.md` §1, §3, §4, §5, §6, §7; `stage7/cases.md` §3, §5, §6; `stage7/web.md` §4, §8, §9, §10, §13, §14, §15; `stage7/staff.md` §5, §7; `stage7/data.md` §1, §3, §4, §6, §9 | Every signature in §4 below |
| Requirements | PRD R-1…R-8, R-13…R-29, R-41, R-45…R-47; `docs/data/worked-pairs.md` WP-1…WP-8 (+ fee-free variant = WP-4F) | Expected outputs (expected-answer authority, DO-5) |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` E-1, E-5, E-6, E-7 | Hard gates exercised as code invariants with scripted outputs |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-1…WF-4, WF-9, WF-10, WF-12, WF-13; *Records*, *Correlation*, *Content and redaction*, *Status values*, *Missing instrumentation*; CAP-1…CAP-4, CAP-7, CAP-8 | Capture tests AC-17…AC-23, AC-30, AC-31, AC-42, AC-46…AC-51 |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-1, M-3, M-4, M-6…M-27, M-29 | Stay computable from the stored records; no target is set here |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§5, `context-maintenance.md`; workspace `context-management-multi-turn.md` rule 3 | Checks, journey gate, evidence record, turn-2+ prompt test |
| Current code | `src/meridian/web/{container,app,deps,logging}.py`, `config.py`, `agent/gateway.py`, `adapters/{checkpointer,retrieval_fastembed,tracing_langfuse}.py`, `retrieval/ingest.py`, `policy/limits.py`, `domain/turn.py`; `tests/unit/web/test_container.py`, `tests/unit/test_import_direction.py`, `tests/fakes/models.py`, `tests/unit/adapters/{_tracing_doubles,test_retrieval_fastembed}.py`, `tests/api/openapi_check.py`, `tests/journeys/affected.py`; since refresh 2 also `agent/{graph,context}.py`, `agent/tools/*.py`, `agent/nodes/compose.py`, `domain/blocks.py`, `adapters/models/{anthropic,openrouter_jev}.py`, `web/middleware.py` (`run_tag_of`), `tests/journeys/support/*.py`, `tests/contract/openapi_variants.py`; since refresh 3 also `services/{cases,handoff}.py`, `agent/nodes/{load_context,reply}.py`, `domain/handoff.py`, `adapters/sqlite/schema/{00_core,20_spend,60_cases}.sql`, `adapters/tracing_langfuse.py` (span metadata), `eval/harness/{cli,deps,freeze,cases,records,report}.py`; since refresh 4 also `services/{demo,session,turn}.py`, `web/routes/chat.py`, the `register_demo` and `register_chat` hunks; since refresh 5 also `agent/specialists/{specs,runner}.py`, `agent/prompts/{routing,specialists}.py`, `agent/nodes/{front,plan,act}.py`, `agent/graph.py` (node map), `agent/routers.py`, `tests/journeys/support/steps.py` (`NEED_OWNERS`), AEA-52's `tests/integration/staff_support.py` | §4 copies |
| Sibling plans (not on `main` at `b68df7e`) | Plan `AEA-39` in this folder (no branch); AEA-52's plan §8 R-3 (a request to this ticket) | Act-node behaviour this ticket waits on (§9); R-19 |
| Seam audits | `.claude/state/resume.md`: second wave-2 batch, open finding 1; wave-3 findings 1, 2, 4 and 8 | PA-5; check 7's known reds; the J-1 contract steps are an AEA-59 follow-up; the `PROVIDER_KEYS` test is a proposed follow-up |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer creates or edits)

| File | Create / modify | Responsibility (one sentence) | Target size |
|---|---|---|---|
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_graph`** | Bind the real graph, its dependencies and `run_graph`; the only reader of `overrides` | hunk ≤ 150 lines |
| `tests/contract/test_model_ports_contract.py` | create | AC-3: the shared failure contract of `AnthropicAdapter` and `JevAdapter` on recorded HTTP fixtures | ≤ 400 |
| `tests/integration/customer_support.py` | create | AEA-51's run launcher over AEA-57's public harness pieces: built index, `StepScript`, step models, environment with eval key, trace sink, `open_customer_run` | ≤ 450 |
| `tests/integration/customer_api.py` | create | HTTP helpers: open a chat, send text/choice/code/form, read the inbox code, find blocks, verify a customer, staff role switch | ≤ 300 |
| `tests/graph/worked_pair_scenarios.py` | create | One driver per worked pair (script + turns + returned ids), and `run_dev_set` used by AC-28, AC-30, AC-39, AC-42 | ≤ 500 |
| `tests/graph/test_worked_pairs_api.py` | create | AC-5…AC-16, AC-26, AC-27, AC-29, AC-34…AC-40 | ≤ 500 |
| `tests/integration/test_customer_composition.py` | create | AC-1, AC-2, AC-4, AC-41, AC-43, AC-44, AC-49, AC-50, AC-51 | ≤ 500 |
| `tests/integration/test_customer_failures.py` | create | AC-24, AC-25, AC-28, AC-45 | ≤ 400 |
| `tests/integration/test_relayed_turn.py` | create | AC-23 | ≤ 250 |
| `tests/capture/test_cap1_customer_chat.py` | create | AC-17, AC-18, AC-19, AC-20, AC-30, AC-31, AC-42 | ≤ 500 |
| `tests/capture/test_cap2_safety_first.py` | create | AC-21 | ≤ 200 |
| `tests/capture/test_cap3_handoff.py` | create | AC-22, AC-33, AC-46, AC-47, AC-48 | ≤ 400 |
| `tests/journeys/j2/test_aea_51.py`, `j3/…`, `j4/…`, `j5/…`, `j9/test_aea_51.py` | create (5 files) | AC-32: journeys J-2, J-3, J-4, J-5, J-9 with user-visible and stored assertions | ≤ 250 each |
| `docs/testing/journeys/<run-date>-AEA-51.md` | create (written by the record command, then committed) | AC-32 evidence record (integrated-journeys §4) | generated |
| `.claude/reference/area-map.md` | modify the last cell of every A7a and A8 row (each appears twice, R-20) and of row `3+` (*Integration and journeys*) | AC-52 | — |
| `.claude/state/icm-progress.md` | **append one** *Routes verified against code and tests* row (append-style, as every recent slice did) | AC-52 | ≤ 400 chars |
| `docs/design/code-design.md` | modify §6 only: append `Proven: <test> (AEA-51, <sha>)` to the last cell of each cut seam row this ticket proves | AC-52 | — |

No other file. The two support modules and the scenario module are AEA-51's own test helpers (slice plan §3: "Other
tickets put fixtures in their own test folder"). Helper modules may **not** go into `tests/journeys/j*/`: AEA-57's
convention check allows only `test_aea_<NN>.py` there.

### 2.2 Shared surfaces read only (never edit)

`src/meridian/**` except the `register_graph` hunk; every other `register_<x>()` hunk and the module-level imports of
`web/container.py`; `web/app.py` (`ContainerOverrides`, `create_app`), `web/deps.py`; `tests/conftest.py`,
`tests/fakes/**`, `tests/fixtures/**`, `tests/api/**` (import `tests.api.openapi_check` read-only), `tests/journeys/support/**`
(AEA-57's; import only), `tests/journeys/{README.md,affected.py,__init__.py}`, `tests/journeys/j*/__init__.py`, every other
`tests/journeys/j*/test_aea_*.py`, `tests/unit/adapters/{_tracing_doubles,test_retrieval_fastembed}.py` (import helpers
only), `tests/contract/_anthropic_fixtures.py` (AEA-17; not used, see §5 B1), `tests/contract/cases/**` (AEA-59),
`pyproject.toml`, `uv.lock`, `eval/**`, the OpenAPI, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, the briefing, issued
data, `docs/archive/`, `docs/parked/`, `.claude/state/resume.md`, the `Last reconciled:` line of `icm-progress.md`. Also AEA-52's
`tests/integration/{staff_support,staff_streams_support}.py`, `tests/integration/test_staff_*.py`, `test_demo_reset.py`,
`test_reads_composition.py` (AEA-53) and `tests/capture/test_cap5_clock_and_scheduler.py`: read only and **never imported**
(AEA-52 pass 2 edits its helpers; R-19).

### 2.3 Owned by other slices (do not touch)

`register_tracing` (AEA-19; the trace-key change in §8 R-1 is AEA-19's follow-up), `register_spend` (26),
`register_anthropic` (17), `register_jev` (18), `register_gateway` (20, stays an empty stub, AEA-20 plan R-3),
`register_retrieval` (33, stays empty), `register_tool_dispatch` (22, stays empty), `register_identity` (27),
`register_scheduling` (28), `register_cases` (29), `register_demo` (30), `register_chat` (40), `register_person_request`
(42), `register_demo_routes` (43), `register_staff_live` (46); every route, schema, node, service, `domain/*`, `ports/*`;
`tests/journeys/support/` (57); `tests/contract/test_openapi_*` (59); `tests/capture/` CAP-4/5 (52), CAP-6 (53), CAP-7/8
files (24), CAP-9 (50).

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's, verbatim in substance; one row each)

Notation: **S** = `tests/integration/customer_support.py`, **A** = `customer_api.py`, **W** = `worked_pair_scenarios.py`.
"Run" = `open_customer_run(...)` (§5 C). Every HTTP response passes `assert_response_matches` (inside `JourneyClient.call`).

| AC | Kind | Requirement (short) | How it is implemented | Verified by (test → evidence) |
|---|---|---|---|---|
| AC-1 | invariant | Real container binds every seam's real object; only the scripted adapter and in-memory exporter are substitutes, via `ContainerOverrides`; `run_graph` is the compiled graph's; `SqliteSaver` on `checkpoints.sqlite`; recursion limit 25; registry covers every spec; `runner.transcript is` the gateway's tool adapter; readiness ran; one `ReplyComposer`; `GraphDeps.ledger is` the ledger; `runner.trace is` the sink; per-role port + `RoleSpec` with and without overrides | `register_graph` (§5 A2) | `tests/integration/test_customer_composition.py::test_real_objects_bound` → class per seam row; identity asserts; per-role (port, spec) table printed |
| AC-2 | failure/refusal | Jev in a structured/tool role is unconfigurable: start-up fails naming the field, no value; after a turn every `spend_ledger.model` equals its role's `RoleSpec.model` | `config.py` validation (AEA-02) + gateway guard (AEA-20) + `register_graph` provider check (§5 A2 step 3) | `::test_role_maps_bound_and_guarded` → error text; role→model pairs from `SpendRepo.for_turn` |
| AC-3 | invariant | Both adapters: one HTTP attempt, never raise, `ProviderCall` always present, stop reason before content, same `ProviderFailureKind` for the shared situations (models.md §3) | Test only (§5 B1, decision PD-11) | `uv run pytest tests/contract/test_model_ports_contract.py` → every case passes for both; 0 network calls |
| AC-4 | failure/refusal | CON-1 and CON-2 without `mhc_session` → 401 `UNAUTHENTICATED`, `details.reason` `none` | AEA-23 gate, proven here | `::test_login_gate` → 401 bodies valid against the OpenAPI |
| AC-5 | invariant | CON-1 greeting = rendered fixed text (R-1); clock label = `format_clock(DEMO_START)` = "Fri Oct 16, 2026 · 10:00 am" | AEA-40 `SessionService` + AEA-30 `DemoClock` (both on `main`); assert the greeting `text` block equals `render(TextId.GREETING)` and `body["demo_clock"]["label"] == format_clock(DEMO_START)[0]` | `tests/graph/test_worked_pairs_api.py::test_greeting_and_demo_date` |
| AC-6 | invariant | WP-1: knowledge only; no `archive/` passage; citation in the lookup log; scripted `$149` removed by R-46 with a counts-only `check_event` | W `wp1` | `::test_wp1_membership_stale_twin` → 0 identity actions, 0 cases, 0 `archive/` ids, the removal event without `$149`, `$149` absent from reply |
| AC-7 | invariant | WP-2: locate by form; code only on CON-6 for this login session; invoice read before code → `not_verified`; after code the billed facts; dispute → P3 `billing_dispute` + promise + reference | W `wp2` | `::test_wp2_invoice_after_code` |
| AC-8 | invariant | WP-3: windows incl. 56, 42, 58, no Saturday; book 56 in one transaction; member fee note; concurrent 56 from another conversation → `SLOT_TAKEN`; issued file unchanged | W `wp3` + concurrent second chat | `::test_wp3_booking_and_one_slot_concurrency` |
| AC-9 | invariant | WP-4: `move` refused `fee_bearing`; row unchanged; P2 `fee_bearing_change`, case due 12:00 today, promise due Mon Oct 19 7:00 pm; promise text + extra lines; "I've moved it" removed | W `wp4` | `::test_wp4_fee_bearing_never_written` |
| AC-10 | invariant | WP-4F: move commits with `actions(moved)`; turn 4 "Yes, please." keeps "Yes, it's moved: Monday…" because `settled` came from `actions` | W `wp4f` | `::test_wp4f_move_carries_to_next_turn` |
| AC-11 | invariant | WP-5: KB instruction first, word for word; 0 model calls; P0 `safety`; no promise time; contact line after, as an offer; a detail-free next turn leaves P0 open | W `wp5` | `::test_wp5_co_alarm_safety_first` |
| AC-12 | invariant | WP-6: burning card first; `yes` → WP-5 text + P0; `not_sure` → cautious text, emergency number, P1 + `OD4.danger_review`; `no` → urgent booking offer + P2 `burning_ruled_out`, due = booked window start (CAS-16 A) | W `wp6` (three conversations) | `::test_wp6_burning_three_branches` |
| AC-13 | invariant | WP-7: `refund` P3, exact promise + "I can't promise an outcome.", due Tue Oct 20 7:00 pm, reference appended by code, follow-up question; scripted brief amount removed and heading flagged; refund guidance attached as a lookup-log brief item | W `wp7`; PA-5 fabricated quote | `::test_wp7_refund_handoff_and_brief` (+ PA-5 asserts) |
| AC-14 | invariant | WP-8: code first; renewal 2026-11-03 read with a lookup row; "Done, auto-renew is off" removed; P3 `membership_cancel`, rule `D4.membership_cancel`, promise, reference | W `wp8` | `::test_wp8_no_false_completion` |
| AC-15 | invariant | DANGER through the raise-only classifier: emergency number first; P1 `danger` + `OD4.danger_review`; `gate_result=danger`, `outcome=safety_reply`; nothing before the instruction | W `danger` | `::test_danger_emergency_first` |
| AC-16 | failure/refusal | NODANGER not raised; classifier error-in-200 → rules stand, `classifier_fallback` signal + `classifier` event; planner fails twice → Sonnet fallback; both fail → `ai_failure` P3, `degrade_reason=model_error` | W `nodanger` + 2 variants | `::test_nodanger_and_model_fallbacks` |
| AC-17 | capture | CAP-1 required records: `request` per HTTP call (+ `X-Request-ID`), one `conversation`, one `turn` per message with fields, one trace per turn with nested node/model/tool spans, lookup rows, R-46 event, one `gate` event per turn and one `classifier` event per classifier run, ledger rows, `thread_id` = checkpointer key = trace `session_id` | Run with a Langfuse sink over an in-memory exporter (needs §8 R-1) | `tests/capture/test_cap1_customer_chat.py::test_required_records_present` |
| AC-18 | negative | Code, card-like number, full phone, introduced name, sentinel phrase, key and cookie sentinels absent / masked as specified; log keys within allow-list; span scan covers node and model-call spans after the mask hook | Same run, scans | `::test_forbidden_values_absent` → 0 hits per value |
| AC-19 | negative | JEV-profile requests carry no phone, email, street, introduced name, `MHC-\d{5}`, `INV-\d{6}`; SONNET-profile requests carry no code, card, email, street, phone beyond `[phone ending NN]` | `script.calls` request bodies | `::test_model_requests_redacted` |
| AC-20 | negative | Code digits, form phone, card number never in checkpoints, `messages`, `turns`, `lookup_log`, `check_events`, logs, spans, model requests; placeholders present instead | `run.files_containing` + scans | `::test_intake_never_in_state` |
| AC-21 | capture | CAP-2: WP-5 no model span before the safety reply; DANGER only `planner` and `classifier` spans before it; P0/P1 cases; no identity/lookup step first | Sink spans in start-time order | `tests/capture/test_cap2_safety_first.py` |
| AC-22 | capture | CAP-3 after WP-7 + CON-4 + CON-5: case, events, promise from the table; CON-4 `turn` row values; `already_open` same reference; CON-5 stored; unverified `on_record` → 409 `NOT_ALLOWED_IN_STATE` | AEA-42 routes on the real `HandoffService` | `tests/capture/test_cap3_handoff.py` (`::test_cap3_records`) |
| AC-23 | capture | Relayed turn while a representative holds the chat: `AI_PAUSED` notice with `delivered_to_representative: true`, CON-21 `customer_message` with STORE text, `turn.outcome = to_staff`, 0 model calls; CO alarm while paused → safety card in the same turn, still delivered, controller stays human (GRC-3 A) | Staff role (CON-10), claim (CON-13), join (CON-14), CON-21 read | `tests/integration/test_relayed_turn.py` |
| AC-24 | failure/refusal | Day total $30 → `SPEND_CAP_REACHED`, no model call; safety turn still answered; CON-4 still opens a case; a scripted `PROVIDER_SPEND_CAP` trips the circuit; the next turn makes no model call | Real `LedgerService` | `tests/integration/test_customer_failures.py::test_spend_caps`; the safety half in `::test_spend_cap_safety_still_answered`, skipped `blocked-on AEA-40-F1` until it lands (§8 R-14) |
| AC-25 | failure/refusal | Brake, model error, tool error, deadline through the real graph; each a `degraded_handoff` row with its reason; conversations never `resolved`; "Try again" after a committed write does not repeat it | Scripted outputs + short deadline (PD-9) | `::test_brake_and_deadline` |
| AC-26 | invariant | Restart between the business write and the checkpoint: turn 4 still sees the move | Stop, restore the pre-turn-3 checkpoint files, restart (§5 E) | `tests/graph/test_worked_pairs_api.py::test_restart_between_write_and_checkpoint` |
| AC-27 | invariant | Turn-2+ prompt test: identical complete stable prefix per role on turns 1, 2, 5; window caps 10 turns / 8,000 chars / 600 per line; no tool output in `messages` or window; "what about Monday?" resolves against the open task | Request capture in `script.calls` | `::test_turn_two_plus_prompt_and_state` |
| AC-28 | invariant | No DB transaction open across any scripted model call (probe write with `busy_timeout` 0 succeeds) | `StepScript.probe` (§5 C3) over `run_dev_set` | `tests/integration/test_customer_failures.py::test_no_transaction_across_model_calls` |
| AC-29 | invariant | A three-task turn completes under recursion limit 25 | Planner choices with three intents | `tests/graph/test_worked_pairs_api.py::test_three_task_turn_under_recursion_limit` |
| AC-30 | capture | Record consistency over the dev set and CON-4 turns: lookup rows = tool calls, ledger rows = model calls, handed_off ⇒ case, `agent_version`, `trace_export`, `plan_topic` on planner turns, snapshots only what the tool showed | `run_dev_set` + SQL | `tests/capture/test_cap1_customer_chat.py::test_record_consistency_over_dev_set` |
| AC-31 | capture | CON-6 WF-3 records: `request` with the code request's `thread_id`; code row hash + expiry only; inbox body rendered only in the serialiser; second session empty; code absent from logs; sentinels absent; no phone/email; no outbound connection | Run with socket guard | `::test_wf3_inbox_records_and_scope` |
| AC-32 | journey | J-2, J-3, J-4, J-5, J-9 on AEA-57's harness pieces; user-visible and stored assertions; level `integrated with a scripted model`; evidence record | Five journey files (§5 G) | `uv run pytest -m journey tests/journeys/j2 tests/journeys/j3 tests/journeys/j4 tests/journeys/j5 tests/journeys/j9 --journey-record=AEA-51` + `docs/testing/journeys/<date>-AEA-51.md` |
| AC-33 | capture | "can I talk to a person" on CON-2 hands off on the first ask: `gate_result=person_requested`, `outcome=handed_off`, one case + promise, no specialist span or model call first | W `person_words` | `tests/capture/test_cap3_handoff.py::test_wf1_person_words_first_ask` |
| AC-34 | negative | Locate no-match, ambiguous match, three wrong codes → `identity_unverified` P3; byte-identical blocks for non-existent vs existing customer; no account value in reply or `settled` | W `identity_failures` | `tests/graph/test_worked_pairs_api.py::test_wf1_identity_failure_reveals_nothing` |
| AC-35 | invariant | WP-4 cancel leg: `cancel` refused `fee_bearing`; rows unchanged; P2 staff request; "$49 … applies under current policy", appointment stays; 0 `cancelled` actions | W `wp4_cancel` | `::test_wp4_fee_bearing_cancel_never_written` |
| AC-36 | invariant | Estimate: only `estimate` slots; booking writes an `estimate` appointment; confirmation names the Comfort Advisor | W `estimate` | `::test_estimate_books_comfort_advisor` |
| AC-37 | invariant | Quick checks offered once on a non-urgent repair booking (one `qc-<turn_id>` `kb_search`); decline books straight away; none on WP-5, DANGER, urgent no-heat; offer never sets `resolved` | W `quick_checks` | `::test_wf1_quick_checks_offered_never_required` |
| AC-38 | invariant | Off-corpus question → no-current-source reply + person offer, 0 citations; MHC-10003 warranty after code → install date + K-9 sentence word for word | W `no_source`, `warranty` | `::test_wf1_no_source_and_warranty` |
| AC-39 | invariant | `staffing` = `nobody_online` after start; 0 `live_queued` over the dev set, unstaffed promises; after CON-7 `simulated_on_shift`, staffing shown and a handoff is live-queued with `R26.staffed` text | `run_dev_set` + CON-7 | `::test_wf1_staffing_and_no_live_queue` |
| AC-40 | invariant | CON-8 `plus_1h` expires the code on the demo clock (wall clock seconds); CON-6 lists it `expired` with no code; entering it → `CODE_EXPIRED` | Supervisor role switch, CON-8, CON-6, CON-2 | `::test_wf3_code_expiry_follows_demo_clock` |
| AC-41 | failure/refusal | `run_id` header without the eval key → `run_tag=live`, no `run_id`; with the key → `run_id` and `run_tag=eval` | Run with `eval_key=True` | `tests/integration/test_customer_composition.py::test_run_id_honoured_only_with_eval_key` |
| AC-42 | invariant | Every stored status value within DO-6 *Status values*; `degrade_reason` only with `degraded_handoff`; `error_kind` on a forced 5xx | `run_dev_set` + forced 5xx (PD-14) | `tests/capture/test_cap1_customer_chat.py::test_status_values_within_lists` |
| AC-43 | invariant | 20 concurrent conversations: no `BUSY`/`RATE_LIMITED`; two racing for one slot → one booking, one `SLOT_TAKEN` | Threads + marker routing (PD-13) | `tests/integration/test_customer_composition.py::test_twenty_concurrent_conversations` |
| AC-44 | invariant | Real `JevAdapter` and `AnthropicAdapter` passed as overrides over recorded HTTP fixtures: WP-1 turn completes; Jev error-in-200 → Sonnet planner fallback; specialist 5xx every attempt → `model_error`; one HTTP request and one ledger row per attempt; no forced `tool_choice`; `provider.data_collection = deny` on every Jev body | `httpx.MockTransport` behind real adapters | `::test_real_adapters_through_con2` |
| AC-45 | failure/refusal | Spend cap reached and every read bucket exhausted: CON-4 never refused, still opens a case; CON-5 never 429 | Real ledger + driven reads | `tests/integration/test_customer_failures.py::test_person_request_never_limited` |
| AC-46 | capture | CON-4 `turn` row: `agent_version`, `server_ms`, `trace_id` whose trace holds the `turn` span with timed children; 0 ledger rows, 0 model calls | Sink spans | `tests/capture/test_cap3_handoff.py::test_wf2_turn_records` |
| AC-47 | negative | WF-2 forbidden values absent from records, logs, bodies; masked only in spans; scripted adapter not called during CON-4/CON-5 | Scans | `::test_wf2_forbidden_values_absent` |
| AC-48 | invariant | CON-4's `events(case_created)` row commits with its case; a held write lock beyond the retry → 503 `HANDOFF_FAILED`, neither row; event polled once | Separate connection holding `BEGIN IMMEDIATE` | `::test_con4_event_in_handoff_commit` |
| AC-49 | capture | AEA-24's runner plays one dev case against the app with the eval key; WF-1 records tagged `eval` + `run_id`; report has one case result; DB-copy check ran; keyless run → `live` | In-process AEA-24 runner (`cli.main` + `HarnessDeps`) (§5 F2) | `tests/integration/test_customer_composition.py::test_eval_runner_against_app_wf9` |
| AC-50 | capture | AEA-24 `load` suite, two conversations: one timing line per CON-2 call; records tagged `load`; DB-copy check 0 violations | In-process AEA-24 runner (`cli.main` + `HarnessDeps`) | `::test_load_runner_against_app_wf10` |
| AC-51 | capture | `--experiment XP-1` dev run of one case: ledger rows `eval` + `run_id`, counted in `spend_today()` | In-process AEA-24 runner (`cli.main` + `HarnessDeps`) + `LedgerService.spend_today()` | `::test_experiment_run_spend_wf12` |
| AC-52 | regression/context | Area map A7a, A8 (and 3+) "integrated (AEA-51)" + commit; ICM routes row; DO-3 §6 seam rows annotated | §5 H | `git diff --name-only main...HEAD` → owned files only |

### 3.2 Plan-added criteria (reconciliation found them; post them as one issue comment)

| ID | Criterion | Why | Test |
|---|---|---|---|
| PA-1 | An override port whose `provider` differs from the provider `Settings.models` names for that role fails start-up with `ValueError("override for role <role> has provider <p>; settings name <q>")` | models.md §7: ledger rows must name the configured provider and model; a mismatched override would hide that | `test_customer_composition.py::test_role_maps_bound_and_guarded` (extra case) |
| PA-2 | With an empty index directory the app still starts, `Key("retrieval_readiness")` reads `ok=False`, and one WARNING `retrieval_not_ready reasons=<comma list>` is logged on logger `meridian.graph` | data.md §9 item 6 says readiness runs at start-up but not what a failure does; AEA-57's J-1 and every existing full-app test run on an empty index | `test_customer_composition.py::test_real_objects_bound` (second app) |
| PA-3 | `register_graph` writes nothing and makes no network request at start-up | The deployed app must start with export off and no provider call (models.md §2: adapters make no request at construction) | `::test_real_objects_bound` under `socket_guard()` |
| PA-4 | The contract boundary checks run strict from this ticket on: `CONTRACT_STRICT=1 uv run pytest tests/contract -rs` passes for every customer-path operation (`startChatSession`, `getChatThread`, `submitTurn`, `streamChatEvents`, `requestPerson`, `saveFollowUp`, `listDemoInbox`, `getStaffing`, `setStaffing`, `getDemoClock`) | Slice plan §0a: "AEA-51 switches on the strict mode"; AEA-59 AC-1/AC-4 | §7 check 6 (no new file: AEA-59 owns the test) |
| PA-5 | WP-7's scripted brief carries one `claims` quote whose text (`"sentinel-quote-" + letters(10)`) is in no customer message: that text is absent from the case's `case_briefs.brief_json`, and the turn has a `check_events` row with `check_kind = 'brief_quote'` and `removed >= 1` | Second wave-2 seam audit, open finding 1 (`resume.md`): `BriefAssembler.attach_extraction` keeps every quote when `customer_messages` is `None`, and AEA-38's `reply.checks` calls it without that argument; `check_quotes` runs upstream, and the audit asks for a test that proves it on the real path | `tests/graph/test_worked_pairs_api.py::test_wp7_refund_handoff_and_brief` (extra asserts). Red → record `blocked-on AEA-38 follow-up` (pass `customer_messages`) on #51; never patch `reply.py` here |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| One adapter per (provider, model), memoised; same object to every role naming it | models.md §2, §7 | AC-1 | in-ticket | A2 step 2 |
| One `LedgerService` (no second instance: the circuit state and cap live in it) | models.md §6, §7; `register_spend` already provides `Key("ledger")` | AC-1, AC-2 | in-ticket; **reuse** the provided key (PD-1) | A2 |
| Sink choice from the four `langfuse_*` fields; `overrides.trace` replaces it | models.md §7, R-G-6, web.md §15, R-W-8 | AC-1 | **blocked-on AEA-19-F1** (`register_tracing` already provides `Key("trace")`; only a follow-up on it can let the override reach `TurnService` and `PersonRequestService`) | §8 R-1; A2 step 1 |
| Registry from the three factories; `check_covers` per spec at start-up | graph-tools §1 | AC-1 | in-ticket | A2 step 6 |
| `SpecialistRunner(transcript=` the gateway's specialist port, `trace=` the sink`)` | graph-tools §2, R-G-17 | AC-1, AC-17 | in-ticket | A2 step 7 |
| `FastembedIndex(settings.index_dir)`; `readiness()` at start-up | data.md §4, §9 item 6 | AC-1 | in-ticket; failure behaviour **added** (PA-2) | A2 step 5 |
| `GraphDeps` 13 fields incl. `trace`, `specialists`, `cases`, `ledger` | graph-core §4, R-G-13 | AC-1 | in-ticket | A2 step 9 |
| One `ReplyComposer` for compose, `PersonRequestService`, `SessionService.settled_view` | graph-core §13, web.md §14 | AC-1 | in-ticket: provide `deps.REPLY_COMPOSER` (both AEA-40 and AEA-42 already read that key) | A2 step 8 |
| Graph compiled with `SqliteSaver`, recursion 25, `context_schema=TurnContext`; `run_graph` bound | graph-core §2 rule 2, §4; DO-3 §5.4 | AC-1, AC-29 | in-ticket (AEA-21's `build_graph` already sets the schema and limit) | A2 step 10 |
| No `configurable` value carries `intake` | graph-core §2 rule 2 | AC-20 | in-ticket (AEA-21's `run_graph` sends only `thread_id`) | proven by AC-20 |
| The deployed factory passes no override | web.md §15 | AC-1 | in-ticket | AC-1 second app (`create_app(settings)`, no overrides) |
| Contract boundary strict mode from wave 3 | slice plan §0a; AEA-59 | no | **added** PA-4 | §7 check 6 |
| Staff guidance prefixes resolve at start-up | cases.md §5 | no | other-ticket: AEA-29's `register_cases` hunk | — |
| `on_alert` → `AlertWriter.fire` binding | MOD-7 | no | other-ticket: AEA-19 hunk, proven by CAP-9 (AEA-50) | — |
| CON-13 claim behaviour, staff side of S-7, S-11 customer stream, S-17, S-19 | ticket *Seams not proven here* | no | other-ticket: AEA-52 | AC-23 only uses claim as a step |
| R-W-12 / D-8 (fresh chat after a new login) | sign-off D-8 | no | n/a here; the restart test (AC-26) keeps the same login session by carrying its cookie | §5 E |
| CAS-16, GRC-3, DAT-1 | sign-off D-14 | "Awaiting Innocent" | **settled: option A** for all three | AC-12, AC-23, AC-19 as written |
| Live (paid) model runs | rule `integrated-journeys` §3 rule 4 | no | other-ticket: AEA-61 (wave 4) | — |
| A brief quote must be an exact substring of a customer message before it is stored | GRN-3; `resume.md` second wave-2 batch, finding 1 | no | **added** PA-5 | D2 `wp7`, D5 |
| J-1 response-contract steps once AEA-51 lands | `resume.md` wave-3 finding 2 | no | other-ticket: AEA-59 follow-up (not cut); this ticket never edits `tests/journeys/j1/` | — |
| Every `web/deps.py` `PROVIDER_KEYS` entry resolves on the assembled app | `resume.md` wave-1 finding 8 | no | other-ticket: proposed follow-up once AEA-29, 30, 40, 51 and 53 merge; AC-1 covers the keys this hunk provides | — |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| CON-1, CON-2 (chat turn incl. code entry; graph behind it) | WF-1 | DO-6 WF-1 row | E-1, E-5, E-6, E-7; M-1, M-3, M-4, M-6…M-9, M-14, M-16…M-26, M-29 |
| CON-4, CON-5 | WF-2 | DO-6 WF-2 row | M-10…M-13, M-15 |
| CON-6 | WF-3 | DO-6 WF-3 row | — |
| CON-2 relayed half | WF-4 | DO-6 WF-4 row | M-13, M-27 |
| App start-up (role maps, sink choice) | WF-13 | DO-6 WF-13 row | — |
| Eval runner against the app (AC-49…AC-51) | WF-9, WF-10, WF-12 | DO-6 rows | M-12, M-14…M-26 |

No new entry point is added; `register_graph` binds the graph behind WF-1 and wires services behind WF-1…WF-4.

---

## 4. Shared code to use (copied from current code, the addenda, or the sibling branch named)

### 4.1 On `main` now

```python
# src/meridian/web/container.py (AEA-01)
class ContainerError(RuntimeError): ...          # str(exc) == f"not provided: {name}" when nobody provided the key
@dataclass(frozen=True)
class Key[T]:
    name: str
class Container:
    @property
    def settings(self) -> Any: ...
    @property
    def limits(self) -> Limits: ...
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...   # ContainerError after build / duplicate
    def get[T](self, key: Key[T]) -> T: ...                                              # lazy, memoised; cycle → ContainerError
    def on_start(self, starter: Callable[[], None]) -> None: ...                        # before build only
    def on_close(self, closer: Callable[[], None]) -> None: ...
def register_graph(container: Container, app: FastAPI, *, settings: Any, limits: Limits, overrides: Any) -> None: ...
# build_container calls register_graph second to last (before register_frontend), then container.build(), which builds
# EVERY provided object in provide order and then runs the starters.

# src/meridian/web/app.py (AEA-23)
@dataclass(frozen=True)
class ContainerOverrides:
    choice: Mapping[ChoiceRole, ChoiceModel] | None = None
    structured: Mapping[StructuredRole, StructuredModel] | None = None
    tools: Mapping[ToolRole, ToolCallingModel] | None = None
    trace: TraceSink | None = None
    wall_clock: Callable[[], datetime] | None = None
def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> FastAPI: ...

# src/meridian/web/deps.py (AEA-23): keys used here
REPLY_COMPOSER: Key[Any] = Key("reply_composer")     # provided by THIS ticket
IDENTITY_SERVICE = Key("identity_service"); HANDOFF_SERVICE = Key("handoff_service"); CASE_SERVICE = Key("case_service")
DEMO_SERVICE = Key("demo_service"); UOW_FACTORY = Key("uow_factory"); WALL_CLOCK = Key("wall_clock")
EVAL_KEY_HEADER = "X-Meridian-Eval-Key"; RUN_ID_HEADER = "X-Meridian-Run-Id"; RUN_TAG_HEADER = "X-Meridian-Run-Tag"  # web/middleware.py

# Keys other hunks already provide (read with container.get, never re-provide)
Key("uow_factory")   # AEA-10, SqliteUnitOfWorkFactory
Key("checkpointer")  # AEA-10, adapters/checkpointer.py Checkpointer; .saver -> SqliteSaver; .path -> data_dir/"checkpoints.sqlite"
Key("ledger")        # AEA-26, LedgerService (satisfies the gateway's CallLedger, SpendGuard and ModelsStatus)
Key("trace")         # AEA-19, TraceSink (NullTraceSink unless Settings.langfuse_complete())

# src/meridian/config.py (AEA-02)
JEV_MODEL = "typesafe/jev-1.13"; SONNET_MODEL = "claude-sonnet-5-5"
class RoleSpec(MeridianModel): model: str; effort: Literal["low","medium","high"] | None; cap_s: float; max_tokens: int; redaction: RedactionProfile
class ModelSettings(MeridianModel):
    choice: dict[ChoiceRole, tuple[Literal["openrouter_jev", "anthropic"], RoleSpec]]
    structured: dict[StructuredRole, tuple[Literal["anthropic"], RoleSpec]]
    tools: dict[ToolRole, tuple[Literal["anthropic"], RoleSpec]]
class Settings(MeridianModel): ... models: ModelSettings; index_dir: Path; data_dir: Path; agent_version: str; eval_key: SecretStr | None
    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Settings: ...    # SettingsError names env vars and rules, never values
    def langfuse_complete(self) -> bool: ...
# Defaults: PLANNER, CLASSIFIER → ("openrouter_jev", JEV_MODEL, redaction JEV); PLANNER_FALLBACK, RESPONDER, BRIEF,
#   SPECIALIST → ("anthropic", SONNET_MODEL, redaction SONNET).

# src/meridian/agent/gateway.py (AEA-20)
class ModelGateway:
    def __init__(self, *, choice: Mapping[ChoiceRole, tuple[ChoiceModel, RoleSpec]],
                 structured: Mapping[StructuredRole, tuple[StructuredModel, RoleSpec]],
                 tools: Mapping[ToolRole, tuple[ToolCallingModel, RoleSpec]],
                 ledger: CallLedger, trace: TraceSink, redact: Redactor, limits: Limits) -> None: ...
    # raises ValueError: a role in the wrong map; a non-anthropic adapter in structured/tools ("role <r> in the <map>
    #   map needs an anthropic adapter"); a Jev role without the JEV profile.

# src/meridian/adapters/retrieval_fastembed.py (AEA-33)
class Readiness(MeridianModel): ok: bool; reasons: tuple[Literal["index_missing","dimension_mismatch","manifest_not_17","record_mismatch"], ...]
class FastembedIndex:
    def __init__(self, index_dir: Path, *, model_cache_dir: Path | None = None, embed_query: Callable[[str], np.ndarray] | None = None) -> None: ...  # no I/O
    def readiness(self) -> Readiness: ...      # never raises
    # search() raises RuntimeError("retrieval index not ready: …") on a missing index; query embedding uses fastembed
    #   with cache_dir=None, which reads the FASTEMBED_CACHE_PATH environment variable.

# src/meridian/agent/tools/knowledge.py (AEA-33)
def knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]: ...   # one ToolDef "kb_search"
# src/meridian/agent/tools/dispatch.py (AEA-22)
class ToolRegistry:
    def __init__(self, defs: Iterable[ToolDef]) -> None: ...                 # ValueError on duplicate / bad name
    def get(self, name: str) -> ToolDef | None: ...
    def for_kinds(self, kinds: frozenset[ToolKind]) -> tuple[ToolDef, ...]: ...
    def check_covers(self, kinds: frozenset[ToolKind]) -> None: ...
class ToolDispatcher:
    def __init__(self, registry: ToolRegistry, uow: UnitOfWorkFactory) -> None: ...

# src/meridian/privacy/redact.py (AEA-04): def redact(text: str, profile: RedactionProfile) -> Redacted
# src/meridian/policy/limits.py (AEA-01): Limits(turn=TurnLimits(deadline_s=60, …), brakes=Brakes(tasks_per_turn=3,
#   tool_rounds=2, sonnet_calls=6), identity=IdentityLimits(code_ttl_s=600, tries=3, max_sends=3), spend=SpendLimits(
#   daily_cap_usd=30.0), context=ContextLimits(window_turns=10, window_line_chars=600, window_total_chars=8000), …)
# src/meridian/domain/turn.py (AEA-02): TurnIds(thread_id, turn_id, request_id, run_tag, run_id, agent_version);
#   RunGraph = Callable[[TurnInput, TurnContext], GraphOutcome]; PlannerChoices(knowledge: "no"|"yes", account:
#   "none"|"invoice"|"membership"|"appointments"|"warranty", scheduling: "none"|"book_new"|"reschedule"|"cancel"|"confirm",
#   handoff: "none"|"refund"|"billing_dispute"|"membership_cancel"|"unsupported_other"|"complaint_or_manager"|
#   "late_technician", topic: "booking"|"membership"|"billing"|"warranty"|"other"); ResponderDraft(text: 1..1200 chars)
# src/meridian/domain/specialists.py: KnowledgeReport(points: list[ReportedPoint] ≤5, answered: bool);
#   AccountReport(summary ≤300); SchedulingReport(appointment_id: int, wanted_time: str, note ≤200)
# src/meridian/domain/handoff.py: BriefExtraction (LLM-facing; build entries with BriefExtraction(...).model_dump_json())
# src/meridian/domain/common.py: ProviderCall, CallRecord (CallRecord.from_provider(call, role=, attempt=))
# src/meridian/adapters/sqlite/repos_cases_state.py: DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
# src/meridian/adapters/sqlite/migrate.py: WORKING_DB_NAME ("meridian.sqlite"); checkpointer.py: CHECKPOINTS_DB_NAME
# src/meridian/retrieval/ingest.py: def main(argv: Sequence[str] | None = None, *, embed: EmbedFn | None = None) -> int
#   (flags --kb-dir, --transcriptions-dir, --out-dir); retrieval/settings.py: EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
# src/meridian/web/logging.py: REQUEST_LOGGER = "meridian.web.request"; SIGNAL_LOGGER = "meridian.signal";
#   RECORD_ATTR = "meridian_record"; ALLOWED_FIELDS: Mapping[str, frozenset[str]] (keys "request", "auth_event",
#   "stream_reconnect", "signal")

# tests on main (import only)
tests.fakes.models: ScriptedFailure(kind, http_status=None, retry_after_s=None, retryable=None); provider_call(*, provider, model, failure=None, stop_reason=None, …, cost_usd=0.0, …) -> ProviderCall
tests.api.openapi_check: assert_response_matches(response, operation_id); assert_sse_frames_match(frames, operation_id); load_contract()
tests.unit.adapters.test_retrieval_fastembed: KB_DIR, TRANSCRIPTIONS_DIR, cached_model_dir() -> Path | None
tests.unit.adapters._tracing_doubles: build_sink(registry, *, exporter=None, stub=None, …) -> (sink, exporter, stub, alerts);
    close_all(registry); span_strings(span) -> list[str]; trace_hex(span) -> str; PROJECT_ID; ok()
# Span facts (adapters/tracing_langfuse.py): turn span name "turn"; model-call span name f"model_call:{role.value}";
#   node spans named by the node (and "tool:<name>" from the runner); attribute "session.id" == str(thread_id);
#   sink.flush(); exporter.get_finished_spans().

# ---- merged after 0dc2ad4; copied from main at 2ec19ad ----
# web/container.py: register_anthropic provides Key[anthropic.Anthropic]("anthropic_client") (closed on shutdown);
#   register_jev provides Key[httpx.Client]("jev_http_client") and Key[Callable[[str], JevAdapter]]("jev_adapter_factory")
#   (ValueError for a model with no JEV_PRICES row; makes no request); register_identity provides
#   Key[IdentityService]("identity_service") (= deps.IDENTITY_SERVICE); register_scheduling provides
#   Key[SchedulingService]("scheduling"). register_gateway, register_retrieval and register_tool_dispatch stay
#   "No-op until" stubs: their objects are wired here.
# adapters/models/anthropic.py (AEA-17):
class AnthropicAdapter:                     # provider: ClassVar[ProviderName] = "anthropic"
    def __init__(self, client: anthropic.Anthropic, *, model: str) -> None: ...
def build_anthropic_client(api_key: SecretStr) -> anthropic.Anthropic: ...
#   HTTP 429 WITH retry-after -> RATE_LIMITED; 429 WITHOUT it -> PROVIDER_SPEND_CAP; 402 -> PROVIDER_SPEND_CAP;
#   stop_reason "refusal" -> REFUSAL, "max_tokens" -> MAX_TOKENS; tool requests send tool_choice {"type": "auto"}.
# adapters/models/openrouter_jev.py (AEA-18):
class JevAdapter:                           # provider: ClassVar[ProviderName] = "openrouter_jev"
    def __init__(self, http: httpx.Client, *, api_key: SecretStr, model: str) -> None: ...
#   every body carries "provider": {"data_collection": "deny"}; 402 -> PROVIDER_SPEND_CAP; 429 -> RATE_LIMITED
#   (retry-after parsed); an "error" object inside a 200 -> BODY_ERROR with http_status = inner code (retryable for
#   408/429/500/502/503/504/529); unparseable body or a choice not offered -> INVALID_OUTPUT.
# domain/common.py: ProviderFailureKind values timeout, connection, rate_limited, overloaded, server,
#   provider_spend_cap, our_spend_limit, bad_request, auth, not_found, body_error, refusal, max_tokens, invalid_output;
#   Role values planner, classifier, planner_fallback, specialist, responder, brief.
# agent/graph.py (AEA-21):
RECURSION_LIMIT: Final = 25
def build_graph(deps: GraphDeps, *, checkpointer: BaseCheckpointSaver[Any] | None, composer: ReplyComposer) -> CompiledGraph: ...
#   StateGraph(ConversationState, context_schema=TurnContext) ... .compile(checkpointer=...).with_config(recursion_limit=25)
def bind_run_graph(graph: CompiledGraph, *, deps: GraphDeps, composer: ReplyComposer) -> RunGraph: ...
# agent/context.py: @dataclass(frozen=True) class GraphDeps: the 13 fields of §4.2 in that order; IdentityService,
#   SchedulingService, HandoffService, BriefAssembler, DemoService, SpecialistRunner, CaseService are `TypeAlias = Any`
#   there until tightened (§8 R-15; not this ticket's file).
# agent/nodes/compose.py: class ReplyComposer (no constructor arguments). Builds TextBlock, SafetyBlock,
#   ConditionalSafetyBlock, BurningCheckBlock, EmergencyLineBlock, QuickChecksBlock, LocatePromptBlock, CodePromptBlock,
#   ConfirmationBlock, CancelledBlock, ChangeRequestBlock, HandoffBlock, LiveQueuedBlock, FailureOfferBlock, NoInfoBlock,
#   NoticeBlock, ErrorBlock. NOT built on main: SlotCardBlock, AccountCardBlock, AppointmentBlock, WherePromptBlock,
#   UrgencyQuestionsBlock (§8 R-13).
# domain/blocks.py:
class SourceChip(MeridianModel): passage_id: str; file: str; section: str; version_date: dt.date | None; excerpt: str; audience: Literal["customer"]; version_label: str
class TextBlock(BlockBase): type: Literal["text"]; text: str; sources: tuple[SourceChip, ...]
#   -> a reply's citations are the `file` values of TextBlock.sources.
# agent/tools/knowledge.py: KB_SEARCH_NAME: Final = "kb_search"; KbSearchArgs(query: str, 1..300 chars)
# agent/tools/account.py (AEA-27), all ToolKind.ACCOUNT_READ:
#   READ_INVOICES_NAME = "read_invoices"     ReadInvoicesArgs(invoice_number: InvoiceId | None = None)
#   READ_MEMBERSHIP_NAME = "read_membership" ReadMembershipArgs()
#   READ_WARRANTY_NAME = "read_warranty"     ReadWarrantyArgs()
def account_tools(uow: UnitOfWorkFactory) -> tuple[ToolDef, ...]: ...
# agent/tools/scheduling.py (AEA-28):
#   FIND_WINDOWS_NAME = "find_windows"                   FindWindowsArgs(service_type: ServiceType, zone_hint: str | None = None)
#   BOOK_VISIT_NAME = "book_visit"                       BookVisitArgs(slot_id: int, issue: str)
#   MOVE_VISIT_NAME = "move_visit"                       MoveVisitArgs(appointment_id: int, new_slot_id: int)
#   CANCEL_VISIT_NAME = "cancel_visit"                   CancelVisitArgs(appointment_id: int)
#   REQUEST_VISIT_CHANGE_NAME = "request_visit_change"   RequestVisitChangeArgs(appointment_id: int, change: "move" | "cancel", wanted_text: str = "")
def scheduling_tools(scheduling: SchedulingService) -> tuple[ToolDef, ...]: ...
# privacy/redact.py: Redactor: TypeAlias = Callable[[str, RedactionProfile], Redacted]; def redact(text, profile) -> Redacted
# policy/limits.py: TurnLimits.deadline_s = 60; max_in_flight = 30 (turn 31 gets BUSY); chat_turns_per_thread_per_min = 20;
#   reads_per_session_per_min (read the value from the file)
# web/middleware.py: run_tag_of(headers, eval_key) -> ("live", None) unless X-Meridian-Eval-Key matches (hmac compare);
#   a wrong key is the same as no key.
# tests/contract/openapi_variants.py (AEA-59): STRICT_ENV: Final = "CONTRACT_STRICT"; contract_strict() -> bool
# tests/journeys/support (AEA-57, merged bd79a29), public pieces this ticket composes:
#   env.journey_environ(root) -> dict (no eval key, no Langfuse names, no agent version); env.letters(n);
#   env.JourneyEnv(root, data_dir, web_dist_dir, index_dir, settings, issued_sha256_before); .db_path; .secret_values()
#   run.JourneyRun (dataclass: env, server, script, models, clock, db, logs, guard, collector, strict, nodeid,
#     clients=[]): .settings .app .container .base_url .demo_username .client() .login() -> LoginResult(client, response,
#     session_id, cookie) .step(journey, name, *, needs=(), operations=()) .files_containing(value) .close_clients()
#   run.open_journey(*, collector, strict, with_clock, nodeid)  (the order open_customer_run copies)
#   scripted_model: RawToolCall(id, name, arguments: str); RawToolStep(text, calls=(), stop_reason="end_turn");
#     ScriptEntry = str | RawToolStep | ScriptedFailure; ScriptedCall(role, method, request, timeout_s, result);
#     JourneyScript: take(role) is the one hook every ScriptedModel calls; record(call); calls; problems();
#     ScriptedModel(script, *, role, model): choose() answers INVALID_OUTPUT when the JSON keys differ from req.fields'
#     names; append() adds 2 items per round that has results (assistant + tool_results);
#     ScriptedAnthropicModel, ScriptedJevModel; scripted_model_for(provider, script, *, role, model);
#     role_specs(settings); scripted_overrides(settings, script, *, wall_clock) -> (ContainerOverrides with trace=None, models)
#   server.launch_server(settings, *, overrides, startup_timeout_s=30.0) -> RunningServer(app, container, host, port,
#     thread; .base_url); server.StepClock (callable; .advance(seconds)); server.socket_guard() -> SocketGuard(.blocked)
#   client.JourneyClient(base_url): .call(method, path, *, operation_id, body=None, headers=None) (validates every
#     /api response against the OpenAPI), .cookie(name="mhc_session"), .responses, ._http (httpx.Client)
#   logtap.tap_logs() -> LogTap(.structured(kind), .all_text(), .wait_for(...)); db.DbReader(path) (.rows, .one, .scalar,
#     .count, .table_rows); db.ISSUED_DB; db.sha256_file(path); steps.RunNote; steps.NEED_OWNERS; plugin.COLLECTOR_KEY;
#     pytest options --journey-record=<scope>, --journeys-strict

# ---- merged after 2ec19ad; copied from main at c9b17ea ----
# web/container.py register_cases (AEA-29): returns early without a web shell; provides deps.CASE_SERVICE ("case_service"),
#   deps.HANDOFF_SERVICE ("handoff_service") and Key[Any]("brief_assembler"); reads Key("demo_clock"), deps.DEMO_SERVICE and
#   deps.REPLY_COMPOSER only when a method runs (RuntimeError("not bound: <key>") until they are provided).
# services/handoff.py: class HandoffService; class BriefAssembler(staff_guidance=None);
#   BriefAssembler.attach_extraction(brief, extraction, facts_check, customer_messages: Mapping[int, str] | None = None)
#   (keeps every quote when customer_messages is None; AEA-38's reply.checks runs check_quotes first and passes none)
# domain/handoff.py: class Quote(LLMFacing): message_id: int; text: str (max 300)
#   class BriefExtraction(LLMFacing): needs: list[Quote] (1..2); claims: list[Quote] (max 5); open_decision: str (max 200)
# checks.py: check_quotes(extraction, shown) keeps a quote only when q.text is a substring of shown[q.message_id]
# storage (adapters/sqlite/schema/*.sql):
#   case_briefs(case_ref, thread_id, status, brief_json, updated_at)
#   check_events(id, thread_id, at, check_kind IN ('completion','fact','brief_fact','brief_quote','gate','classifier','brake'),
#                turn_id, result IN ('pass','trimmed','fallback','fired','raised'), removed, claim_kinds, codes)  -- no run_tag
#   events(id, stream, type, payload, at)
#   run_tag/run_id columns exist on conversations, turns and spend_ledger only (check_events reach them through turn_id)
# adapters/tracing_langfuse.py turn span metadata: attributes "langfuse.observation.metadata.run_tag" (= ids.run_tag) and
#   "langfuse.observation.metadata.run_id" (= redact(run_id, RedactionProfile.TRACE).text after the sink's mask)
# eval/harness (AEA-24, merged 7fddbf5) — the public pieces F2 uses:
from eval.harness.cli import main             # def main(argv: Sequence[str] | None = None, *, deps: HarnessDeps | None = None) -> int
from eval.harness.deps import HarnessDeps     # @dataclass(frozen=True): transport=None, judge=None, env=None,
                                              #   harness_root=HARNESS_ROOT, freeze_file=FREEZE_FILE, log_stream=None,
                                              #   wall_clock=<utc now>, ledger_dir=DEFAULT_LEDGER_DIR, issued_db=ISSUED_DB
from eval.harness.freeze import write_freeze  # def write_freeze(freeze_file: Path, *, root: Path = HARNESS_ROOT, repo_root: Path = REPO_ROOT) -> FreezeStamp
#   FREEZE_FILE = eval/harness/freeze.json (absent on main); `run` has no --freeze-file flag (only `freeze` has one)
#   run flags: --suite {worked-pairs,e2e,load} --split {dev,held-out} --repeats N (default 3) --base-url URL --experiment ID
#     --db-copy PATH --cases-dir DIR --reports-dir DIR --conversations N (default 20); also --dry-run, --judge,
#     --heldout-key-dir, --calibration
#   env read from HarnessDeps.env: MERIDIAN_EVAL_KEY, MERIDIAN_DEMO_USERNAME, MERIDIAN_DEMO_PASSWORD (UsageError if missing)
#   exit: 0 completed, 1 incomplete, 2 usage, 3 refused (not_frozen, tamper, held-out), 4 a gate failed, 5 leak blocked
#   cases.load_cases reads <cases_dir>/dev/*.case.json and <case_id>.key.json; --suite worked-pairs keeps WORKED_PAIR_IDS
#   report.write_report writes <reports_dir>/<run_id>.json (EvalReportFile: run: EvalRunRecord{run_id, suite, experiment_id,
#     status, ...}; results: tuple[EvalCaseResult{run_id, case_id, thread_id, outcome, ...}]; summary: dict with key
#     "db_check"), <run_id>.md, and <run_id>.client_side_turn_timings.jsonl (one ClientTurnTiming JSON line per CON-2 call)
# ---- merged after c9b17ea; copied from main at f466ff7 ----
# services/demo.py (AEA-30):
def format_clock(dt: datetime) -> tuple[str, str]: ...   # (label, date_label); label "Fri Oct 16, 2026 · 10:00 am" at DEMO_START
class DemoClock: ...        # DemoClock(uow); .now() reads the demo_state row, America/Chicago
class DemoService: ...      # DemoService(uow, clock, cases, *, wall_clock); .staffing() .clock_view() .set_staffing(...) .advance_clock(...)
# services/session.py (AEA-40): SessionService.open writes the conversation row and the greeting
#   TextBlock(block_id="blk-greeting", text=render(TextId.GREETING), sources=()) in one write transaction, no model call.
# web/container.py register_demo (AEA-30): web-shell guard; provides Key[DemoClock]("demo_clock"), deps.DEMO_SERVICE,
#   Key("scheduler_job"), Key("scheduler_thread") (thread started by a starter, stopped on close); reaches
#   deps.CASE_SERVICE only at a shift end.
# web/container.py register_chat (AEA-40): web-shell guard; provides deps.TURN_SERVICE ("turn_service") and
#   deps.SESSION_SERVICE ("session_service"). The TurnService factory calls c.get(Key("ledger")) and c.get(Key("trace"))
#   at build (EAGER), and passes run_graph as a forwarding closure that resolves container.get(Key("run_graph")) on each
#   call (RuntimeError("not bound: run_graph") until this hunk provides it). settled_view forwards to
#   container.get(deps.REPLY_COMPOSER).settled_view(settled, identity, controller). Starter: turns.fail_running() sweep.
# services/turn.py (AEA-40):
NoticeCode = Literal["BUSY", "SPEND_CAP_REACHED", "RATE_LIMITED", "TURN_TIMEOUT"]
class TurnService:
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, wall_clock: Callable[[], dt.datetime],
                 spend: SpendGuard, trace: TraceSink, run_graph: RunGraph, settled_view: SettledViewFn,
                 limits: Limits, agent_version: str, *, monotonic: Callable[[], float] = time.monotonic) -> None: ...
    def run_turn(self, cmd: RunTurn) -> TurnResponse: ...
#   Order: non-blocking slot (limits.admission.max_in_flight = 30) else BUSY; spend.allow_turn() False →
#   SPEND_CAP_REACHED; only then parse_intake(cmd.payload) (line 322). So at our cap a safety message gets the notice
#   (§8 R-14). _reject(code, reason) stores status "failed", TurnTrace(gate_result="clear", path="degraded",
#   outcome="degraded_handoff", degrade_reason=reason) with reason "rate_limit" (BUSY, RATE_LIMITED) or "spend_cap",
#   trace_id None, trace_export "off", and calls no model.
```

### 4.2 Addenda signatures this hunk consumes (DO-4 + stage7)

```python
# models.md §2 (AEA-17 / AEA-18)
class AnthropicAdapter:   # adapters/models/anthropic.py; provider: ClassVar = "anthropic"
    def __init__(self, client: anthropic.Anthropic, *, model: str) -> None: ...   # ValueError when model has no price row
class JevAdapter:         # adapters/models/openrouter_jev.py; provider: ClassVar = "openrouter_jev"
    def __init__(self, http: httpx.Client, *, api_key: SecretStr, model: str) -> None: ...
# graph-tools §1
def account_tools(uow: UnitOfWorkFactory) -> tuple[ToolDef, ...]: ...           # agent/tools/account.py (AEA-27)
def scheduling_tools(scheduling: SchedulingService) -> tuple[ToolDef, ...]: ...  # agent/tools/scheduling.py (AEA-28)
# graph-tools §2 (AEA-35)
SPECS: Mapping[Literal["knowledge", "account", "scheduling"], SpecialistSpec]   # agent/specialists/specs.py; SpecialistSpec.tool_kinds
class SpecialistRunner:   # agent/specialists/runner.py
    def __init__(self, *, gateway: ModelGateway, transcript: ToolTranscript, dispatcher: ToolDispatcher,
                 specs: Mapping[SpecialistKind, SpecialistSpec], brakes: Brakes, trace: TraceSink) -> None: ...
    # every argument kept as a public attribute (on main: AEA-35, 1ce98c4); SpecialistKind = Literal["knowledge",
    #   "account", "scheduling"] (domain/turn.py)
# graph-core §4 (AEA-21), field order exactly:
@dataclass(frozen=True)
class GraphDeps:          # agent/context.py
    gateway: ModelGateway; retrieval: RetrievalIndex; uow: UnitOfWorkFactory; identity: IdentityService
    scheduling: SchedulingService; handoff: HandoffService; brief: BriefAssembler; demo: DemoService; limits: Limits
    trace: TraceSink; specialists: SpecialistRunner; cases: CaseService; ledger: ModelsStatus
# graph-core §13: class ReplyComposer: def __init__(self) -> None   (agent/nodes/compose.py)
```

### 4.3 Names from sibling branches and plans (not DO-4; re-check in step A0 after they merge)

| Name | Status at `b68df7e` | Used as |
|---|---|---|
| `build_graph`, `bind_run_graph`, `GraphDeps`, `ReplyComposer` | on `main` (AEA-21, `5531664`); §4.1 | compile once; `Key("run_graph")` |
| `Key("anthropic_client")`, `Key("jev_adapter_factory")` | on `main` (AEA-17, AEA-18); §4.1 | `adapter_for` |
| `Key("scheduling")`, `deps.IDENTITY_SERVICE` (`"identity_service"`) | on `main` (AEA-28, AEA-27); §4.1 | `scheduling_tools`, `GraphDeps.scheduling`, `.identity` |
| `deps.CASE_SERVICE` (`"case_service"`), `deps.HANDOFF_SERVICE` (`"handoff_service"`), `Key[Any]("brief_assembler")` | on `main` (AEA-29, `ef561fc`); §4.1 | `GraphDeps.cases`, `.handoff`, `.brief` |
| `Key[DemoClock]("demo_clock")`, `deps.DEMO_SERVICE` (`"demo_service"`), `Key("scheduler_job")`, `Key("scheduler_thread")` | on `main` (AEA-30, `cf8fd78`); §4.1 | `GraphDeps.demo` |
| `deps.TURN_SERVICE`, `deps.SESSION_SERVICE`; reads `Key("run_graph")` and `Key("reply_composer")` lazily, `Key("ledger")` and `Key("trace")` **eagerly** in the `TurnService` factory | on `main` (AEA-40, `f466ff7`); §4.1 | what this hunk must provide; why §8 R-1 blocks the override |
| `SPECS` (`agent/specialists/specs.py`); `SpecialistRunner(*, gateway, transcript, dispatcher, specs, brakes, trace)` (`agent/specialists/runner.py`), constructor arguments kept as public attributes (PD-8) | on `main` (AEA-35, `1ce98c4`); §4.2 | the runner |
| `DANGER_FIELD = "danger_level"`, `CLASSIFIER_FIELDS` (options `normal`, `burning_unclear`, `danger`) (`agent/prompts/routing.py`); `REPORT_FACTS_TOOL = "report_facts"` (`agent/prompts/specialists.py`) | on `main` (AEA-37 `8d025b7`, AEA-35 `1ce98c4`) | D1 `classifier(...)`, `report(...)` |
| AEA-24 runner (`eval.harness.cli.main`, `HarnessDeps`, `write_freeze`) | on `main` (AEA-24, `7fddbf5`); §4.1 | F2 (in-process) |
| `tests/journeys/support/*` public API | on `main` (AEA-57, `bd79a29`); §4.1 | §5 C |

### 4.4 Request and response shapes (OpenAPI, the signed contract)

`POST /api/login` (`login`) `{"username","password"}`; `POST /api/chat/sessions` (`startChatSession`) → 201
`StartSessionResponse{thread_id, greeting, demo_clock{now,label,date_label}, staffing{mode,label,banner}, controller,
settled, events, limits}`; `POST /api/chat/sessions/{thread_id}/turns` (`submitTurn`) body `{"turn_id": <uuid4>,
"payload": TextPayload{"kind":"text","text"} | ChoicePayload{"kind":"choice","card_id","option"} |
CodePayload{"kind":"code","card_id","code"} | FormPayload{"kind":"form","card_id","values":{…}}}` → 200
`TurnResponse{thread_id, turn_id, sequence, blocks[], settled, writes, controller, notice, last_event_id}`; `notice` =
`Notice{code, actions, retry_turn_id, delivered_to_representative}`; block `type` values: `text`, `source_chip`,
`safety`, `conditional_safety`, `burning_check`, `emergency_line`, `quick_checks`, `urgency_questions`, `where_prompt`,
`locate_prompt`, `code_prompt`, `slot_card`, `confirmation`, `appointment`, `cancelled`, `account_card`,
`change_request`, `handoff`, `live_queued`, `failure_offer`, `no_info`, `notice`, `error`, `session_ended`.
`POST …/handoff` (`requestPerson`) `{"turn_id"}` → `HandoffResponse{result, block, settled}`; `PUT …/follow-up`
(`saveFollowUp`) `{"channel": "email"|"phone", "destination": "on_record"|"general", "window": "morning"|"afternoon"|"any"}`;
`GET /api/demo/inbox` (`listDemoInbox`) → `{"messages":[InboxMessage{id, at, to_masked, body, code, status, expires_at}]}`;
`PUT /api/demo/staffing` (`setStaffing`) `{"mode": "nobody_online"|"simulated_on_shift"}`; `POST /api/demo/clock`
(`advanceDemoClock`, supervisor) `{"step": "plus_1h"|"plus_4h"|"next_business_morning"}`; `PUT /api/session/role`
(`switchRole`) `{"role": "customer"|"representative"|"supervisor"|"owner"}`; `GET /api/staff/cases/{reference}`
(`getCase`); `POST /api/staff/cases/{reference}/actions` (`applyCaseAction`) `{"action": "claim", "expected_version": int}`;
`POST /api/staff/cases/{reference}/live` (`liveChatAction`) `{"action": "join"}`; `GET /api/staff/cases/{reference}/events`
(`streamCaseEvents`, SSE).

---

## 5. Steps

Build order: **A** wiring → **B** adapter contract → **C** support modules → **D** worked pairs → **E** turn-to-turn and
restart → **F** composition, failures, relayed turn → **G** capture → **H** journeys, record, context. Each part ends
with its own affected tests green. Commit after A+B, after C+D+E, after F+G, and the record/context commit last (§7).

**Two passes (refresh 5).**
- **Pass 1, buildable now:** Parts A, B and C, with one difference in A2: **do not provide `Key("run_graph")`** (step 10's
  second half) and end the A1 docstring's first sentence of the second paragraph with `Key("compiled_graph") (SqliteSaver
  from Key("checkpointer"), recursion limit 25); Key("run_graph") is provided once AEA-39's act node is on main.` in
  place of `… recursion limit 25) and Key("run_graph").`. *Invariant: while `act.py` is a stub, every journey that needs
  `run_graph` keeps its honest `blocked-on AEA-51` skip (AEA-57's `NEED_OWNERS` preflight) instead of turning red on a
  `NotImplementedError`; CON-1 and CON-4 still work because `reply_composer` is bound.* Tests in pass 1: from F1, `test_login_gate` (AC-4), `test_role_maps_bound_and_guarded` with
  parts (a) and (b) only, and `test_real_objects_bound` with part (b) plus the part (a) asserts that need neither a
  driven turn nor the trace override (open part (a) with `RunOptions()`, no `trace`; skip its `runner.trace is sink`,
  `graph_deps.trace is sink` and driven-WP-1 asserts for now); from D5, `test_greeting_and_demo_date` (AC-5).
  `tests/graph/worked_pair_scenarios.py` is not created in pass 1, and pass 1 writes no skipped placeholder for a
  pass-2 criterion. Pass-1 commits: commit 1 (A + B), then commit 1b `test(AEA-51): integration launcher, login gate,
  greeting and role guards (pass 1)` with `tests/integration/customer_support.py`, `tests/integration/customer_api.py`,
  `tests/integration/test_customer_composition.py` and `tests/graph/test_worked_pairs_api.py`. Run §7 checks 1, 2, 4–8
  and 11 on pass 1 and report (check 6, strict contract mode, is pass 2 only: `submitTurn` cannot pass strict without
  `run_graph`). Check 8 must show no journey newly red; journeys that skipped only for `reply_composer` may now run and
  must pass (name them).
- **Pass 2, after §9's prerequisites merge:** re-run A0, provide `Key("run_graph")` and restore A1's docstring word for
  word, then everything else, adding to the same files (AC-2 part (c); AC-1's `run_graph` assert, driven WP-1 turn and
  the `trace is sink` identities), then commits 2–4 of §7.

Design interfaces respected (rule `code-design-solid-modularity`): the slice **consumes** the ports (`ChoiceModel`,
`StructuredModel`, `ToolCallingModel`, `ToolTranscript`, `TraceSink`, `RetrievalIndex`, `UnitOfWorkFactory`) and the
service signatures of DO-4 §13–§14; it adds no Protocol, no service and no `src/` file. The composition root is the only
place concrete classes meet (DO-3 §2.1).

### Part A — the `register_graph` hunk

**A0. Pre-flight (at the start of each pass; §5 *Two passes*).**
```bash
export UV_LINK_MODE=hardlink
df -h /home                       # need ≥ 5 GB free; else stop and report
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-51 && uv sync
uv run python -c "from meridian.agent.graph import build_graph, bind_run_graph; from meridian.agent.context import GraphDeps; from meridian.agent.specialists.runner import SpecialistRunner; from meridian.agent.specialists.specs import SPECS; from meridian.agent.tools.account import account_tools; from meridian.agent.tools.scheduling import scheduling_tools; from meridian.adapters.models.anthropic import AnthropicAdapter; from meridian.adapters.models.openrouter_jev import JevAdapter; from meridian.agent.nodes.compose import ReplyComposer; from meridian.agent.prompts.routing import DANGER_FIELD, CLASSIFIER_FIELDS; from meridian.agent.prompts.specialists import REPORT_FACTS_TOOL; print('imports ok')"
grep -n 'Key\[[A-Za-z_.]*\]("\(anthropic_client\|jev_adapter_factory\|scheduling\|brief_assembler\|demo_clock\|trace_override\)")\|IDENTITY_SERVICE\|CASE_SERVICE\|HANDOFF_SERVICE\|DEMO_SERVICE' src/meridian/web/container.py
grep -n "def build_graph\|def bind_run_graph" src/meridian/agent/graph.py
grep -c "SlotCardBlock(\|AccountCardBlock(\|AppointmentBlock(" src/meridian/agent/nodes/compose.py   # expect 3 or more (§8 R-13)
grep -n "allow_turn\|parse_intake" src/meridian/services/turn.py   # the safety gate must run before allow_turn (§8 R-14)
ls src/meridian/agent/specialists/specs.py src/meridian/agent/specialists/runner.py
grep -c NotImplementedError src/meridian/agent/nodes/act.py   # 3 at b68df7e; pass 2 expects 0 (AEA-39 merged)
ls src/meridian/services/session.py src/meridian/web/routes/chat.py src/meridian/web/routes/demo.py tests/journeys/support/run.py
```
**Pass 1** expects `imports ok`, every key name of §4.3 present in its owner's hunk and every file listed; the
`trace_override`, compose-card and `act.py` greps may show the known values (absent, 0, 3). **Pass 2** expects
`imports ok`, every key name of §4.3 present in its owner's hunk, `Key("trace_override")` read inside
`register_tracing` (the AEA-19-F1 follow-up, §8 R-1), compose building the slot, account and appointment blocks (the
AEA-21b follow-up, §8 R-13), and every file listed. **Any difference → stop, report the exact mismatch on issue #51;
do not adapt the wiring to a guessed name.** One exception: the `allow_turn`/`parse_intake` grep (AEA-40-F1, §8 R-14).
If `allow_turn` still comes first, carry on: AC-24's safety half stays skipped as §5 F3 says. If `parse_intake` (or a
safety check) now comes first, remove that skip and the test must pass.

**A1. Docstring.** Replace the `register_graph` docstring with exactly:
```
"""AEA-51 integration: completes the graph and binds run_graph; the only reader of overrides (web.md §15, R-W-8).

Provides Key("model_ports") (the role → (port, RoleSpec) maps the gateway receives), Key("model_gateway"),
Key("retrieval_index") (FastembedIndex(settings.index_dir)), Key("retrieval_readiness") (its readiness(), read while the
container builds; not ready logs retrieval_not_ready and the app still starts), Key("tool_registry"),
Key("tool_dispatcher"), Key("specialist_runner"), deps.REPLY_COMPOSER (one ReplyComposer), Key("graph_deps"),
Key("compiled_graph") (SqliteSaver from Key("checkpointer"), recursion limit 25) and Key("run_graph"). A role present in
overrides.choice / .structured / .tools uses that port with its configured RoleSpec; overrides.trace is provided as
Key("trace_override"), which Key("trace") (AEA-19) then returns. Makes no request and writes nothing. An app
create_app did not build has no web shell, so this does nothing.
"""
```
(Keeps "AEA-51"; drops "No-op until", so AEA-01's stub test skips this hunk.)

**A2. Body.** Imports **inside the function** (the module import block must not change:
`tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`). Steps, each with the invariant it
protects:

0. **Web-shell guard.** `from meridian.web.middleware import WebShellState`; `if not isinstance(getattr(app.state,
   "web_shell", None), WebShellState): return`. *Invariant: the keys this hunk reads (AEA-29, AEA-30, AEA-40, AEA-42
   hunks) exist only in an app `create_app` built; every one of those sibling hunks returns early the same way, so a
   bare `build_container` call never fails on a key nobody provided.*
1. **Trace override (R-W-8).** `if overrides is not None and overrides.trace is not None: sink = overrides.trace;
   container.provide(Key[TraceSink]("trace_override"), lambda _c: sink)`. Everything below reads
   `container.get(Key[TraceSink]("trace"))`. *Invariant: one sink per app; the override reaches `TurnService`,
   `PersonRequestService` and every span of the graph through one key.*
2. **Adapters, one per (provider, model).** Inside a factory for `Key("model_ports")`:
   ```python
   adapters: dict[tuple[str, str], object] = {}
   def adapter_for(c: Container, provider: str, spec: RoleSpec) -> object:
       key = (provider, spec.model)
       if key not in adapters:
           if provider == "anthropic":
               adapters[key] = AnthropicAdapter(c.get(Key[Any]("anthropic_client")), model=spec.model)
           else:
               adapters[key] = c.get(Key[Callable[[str], Any]]("jev_adapter_factory"))(spec.model)
       return adapters[key]
   ```
   *Invariant: roles naming the same model share one adapter object (models.md §2), so the specialist's transcript and
   the gateway's tool port are the same object.*
3. **Pair each role with its `RoleSpec`, honouring overrides.** `typed = cast(Settings, settings)`. For each map name in
   `("choice", "structured", "tools")`: for each `role, (provider, spec)` in `getattr(typed.models, name).items()`:
   `given = getattr(overrides, name, None) if overrides is not None else None`; if `given` is not `None` and `role in
   given`: `port = given[role]`; if `port.provider != provider`: `raise ValueError(f"override for role {role.value} has
   provider {port.provider}; settings name {provider}")` (PA-1); else `port = adapter_for(c, provider, spec)`. Build
   `{role: (port, spec)}`. Provide `Key("model_ports")` as `MappingProxyType({"choice": MappingProxyType(choice),
   "structured": MappingProxyType(structured), "tools": MappingProxyType(tools)})`. *Invariant: the `RoleSpec` (model,
   caps, redaction) always comes from Settings, so ledger rows name the configured model (models.md §7).* Existing API
   tests pass `ContainerOverrides(wall_clock=...)` with all three maps `None`; every role then gets the real adapter,
   which makes no request at construction (models.md §2).
4. **Gateway.** `Key("model_gateway")` → `ModelGateway(choice=ports["choice"], structured=ports["structured"],
   tools=ports["tools"], ledger=c.get(Key("ledger")), trace=c.get(Key("trace")), redact=redact, limits=limits)`.
   *Invariant: the one `LedgerService` (circuit, cap) and the one sink; the constructor's role/provider/profile guards run
   at start-up.*
5. **Retrieval.** `Key("retrieval_index")` → `FastembedIndex(Path(typed.index_dir))`. `Key("retrieval_readiness")` →
   `ready = c.get(index_key).readiness()`; if `not ready.ok`: `logging.getLogger("meridian.graph").warning(
   "retrieval_not_ready reasons=%s", ",".join(ready.reasons))`; return `ready`. *Invariant: readiness runs once at
   start-up (`container.build()` builds every key); a missing index never stops the app (PA-2).*
6. **Registry and dispatcher.** `Key("tool_registry")` → `registry = ToolRegistry((*knowledge_tools(index),
   *account_tools(uow), *scheduling_tools(c.get(Key("scheduling")))))`; then `for spec in SPECS.values():
   registry.check_covers(spec.tool_kinds)`; return it. `Key("tool_dispatcher")` → `ToolDispatcher(registry, uow)`.
   *Invariant: every kind a specialist may use has a tool, checked at start-up, never at turn time.*
7. **Runner.** `Key("specialist_runner")` → `SpecialistRunner(gateway=c.get(gateway_key),
   transcript=ports["tools"][Role.SPECIALIST][0], dispatcher=c.get(dispatcher_key), specs=SPECS, brakes=limits.brakes,
   trace=c.get(Key("trace")))`. *Invariant (R-G-17): tool spans go to the same sink; the transcript is the gateway's
   specialist port object.*
8. **Composer.** `container.provide(deps.REPLY_COMPOSER, lambda _c: ReplyComposer())`. *Invariant: one instance for the
   compose node, `PersonRequestService` and `SessionService.settled_view` (both already read this key).*
9. **GraphDeps.** `Key("graph_deps")` → `GraphDeps(gateway=…, retrieval=c.get(index_key), uow=c.get(deps.UOW_FACTORY),
   identity=c.get(deps.IDENTITY_SERVICE), scheduling=c.get(Key("scheduling")), handoff=c.get(deps.HANDOFF_SERVICE),
   brief=c.get(Key("brief_assembler")), demo=c.get(deps.DEMO_SERVICE), limits=limits, trace=c.get(Key("trace")),
   specialists=c.get(runner_key), cases=c.get(deps.CASE_SERVICE), ledger=c.get(Key("ledger")))`. *Invariant (R-G-13):
   `ledger` is the container's `LedgerService` object.*
10. **Graph and `run_graph`.** `Key("compiled_graph")` → `build_graph(c.get(deps_key),
    checkpointer=c.get(Key("checkpointer")).saver, composer=c.get(deps.REPLY_COMPOSER))`. `Key("run_graph")` →
    `bind_run_graph(c.get(graph_key), deps=c.get(deps_key), composer=c.get(deps.REPLY_COMPOSER))`. *Invariant: one
    compiled graph per app; `TurnService` receives a `RunGraph` (graph-core §2).*
11. **Order of `provide` calls** (so the build order reads top to bottom): `trace_override` (if any), `model_ports`,
    `model_gateway`, `retrieval_index`, `retrieval_readiness`, `tool_registry`, `tool_dispatcher`, `specialist_runner`,
    `reply_composer`, `graph_deps`, `compiled_graph`, `run_graph`. Give every key a typed local, e.g. `gateway_key:
    Key[ModelGateway] = Key("model_gateway")`.

Do **not** in this hunk: build a second `LedgerService` or sink; call `container.get` outside a factory (siblings provide
after this function only in `register_frontend`, but factories keep the build order explicit); touch `app.state`; add a
route; catch and swallow construction errors (a wiring fault must fail start-up loudly); read `os.environ`.

**A3. Check.** `uv run ruff check src/meridian/web/container.py && uv run mypy src/meridian/web/container.py && uv run
pytest tests/unit/web tests/unit/test_import_direction.py -q` → green (the existing `test_container.py` must stay green).

### Part B — the cross-adapter contract (AC-3)

**B1. `tests/contract/test_model_ports_contract.py`.** Self-contained fixtures (do not import AEA-17's or AEA-18's
private test helpers). Build each adapter on an `httpx.MockTransport` that records requests:
- Anthropic: `client = anthropic.Anthropic(api_key="sk-test-" + secrets.token_hex(8), max_retries=0,
  http_client=httpx.Client(transport=transport))`; `AnthropicAdapter(client, model=SONNET_MODEL)`.
- Jev: `JevAdapter(httpx.Client(transport=transport), api_key=SecretStr("test-or-" + secrets.token_hex(8)),
  model=JEV_MODEL)` (the adapter posts to its own OpenRouter URL; the mock transport answers every URL).
- A timeout: the handler raises `httpx.ReadTimeout("timed out", request=request)`.

Decision **PD-11** (what "same kind" means, from models.md §3): the shared rows are asserted equal across both adapters:

| Situation | Anthropic response | Jev response | Kind (both) |
|---|---|---|---|
| timeout | handler raises `httpx.ReadTimeout` | same | `TIMEOUT`, retryable |
| rate limit | 429 + `retry-after: 2` + `{"type":"error","error":{"type":"rate_limit_error","message":"slow"}}` | 429 + `Retry-After: 2` + `{"error":{"code":429,"message":"slow"}}` | `RATE_LIMITED`, `retry_after_s == 2.0` |
| provider spend cap | 402 `billing_error` | 402 | `PROVIDER_SPEND_CAP`, not retryable |
| invalid choice | 200 message whose JSON text picks an option not offered | 200 whose choice is not offered | `INVALID_OUTPUT` |
| unparseable 200 body | 200, body `b"{not json"` | same | `INVALID_OUTPUT` |

The rate-limit row must send the `retry-after` header on the Anthropic side: `AnthropicAdapter` maps a 429 **without**
it to `PROVIDER_SPEND_CAP` (§4.1), so a header-less 429 is not a shared situation. If either adapter's merged mapping
disagrees with a row above, stop and report it on #51 with the observed kind; never change the expectation to match.

Per-adapter rows (asserted against §3, not equal): "error inside an HTTP 200" → Jev `BODY_ERROR` with `http_status` =
inner code (503 → retryable); Anthropic 200 whose body is `{"type":"error","error":{"type":"api_error"}}` →
`INVALID_OUTPUT` (the only §3 row a 200 can take). "Stop reason before content" → Anthropic only (§3 has no Jev row):
a 200 with valid JSON content but `stop_reason: "max_tokens"` → `MAX_TOKENS`, and `"refusal"` → `REFUSAL`.

Tests (all call `choose` with one two-option `ChoiceRequest`; Anthropic rows also via `structured` with
`ResponderDraft`): `test_shared_situations_same_kind[<situation>]`, `test_error_inside_200_per_mapping`,
`test_stop_reason_before_content_anthropic`, `test_one_attempt_never_raises_record_present` (for every situation:
exactly one request seen by the transport, no exception, `attempt.record` is a `ProviderCall` with `status ==
"error"` exactly when `failure` is set, `record.provider` and `.model` equal the constructor's). The module never opens a
socket (MockTransport only). Run: `uv run pytest tests/contract/test_model_ports_contract.py -q`.

**Commit 1** (A + B): `git add src/meridian/web/container.py tests/contract/test_model_ports_contract.py` →
`feat(AEA-51): register_graph binds the real graph; cross-adapter port contract`.

### Part C — support modules

**C1. `tests/integration/customer_support.py`** — exact public API:

```python
REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_SKIP = "bge-small-en-v1.5 is not cached locally (var/fastembed); the built-index tests need it"

@functools.cache
def built_index_dir() -> Path | None: ...
    # 1 cache = cached_model_dir(); None → return None
    # 2 out = Path(tempfile.mkdtemp(prefix="meridian-aea51-index-")) / "index"; atexit.register(shutil.rmtree, out.parent, True)
    # 3 model = TextEmbedding(EMBEDDING_MODEL, cache_dir=str(cache), local_files_only=True)
    # 4 embed = lambda texts: np.asarray([np.asarray(v) for v in model.embed(list(texts))], dtype=np.float32)
    # 5 rc = ingest.main(["--kb-dir", str(KB_DIR), "--transcriptions-dir", str(TRANSCRIPTIONS_DIR), "--out-dir", str(out)], embed=embed)
    # 6 assert rc == 0 and FastembedIndex(out, model_cache_dir=cache).readiness().ok; return out
    # Once per process (xdist: once per worker). This IS the ingest CLI's entry point with an injected embedder.
def require_index() -> Path: ...          # pytest.skip(INDEX_SKIP) when built_index_dir() is None

@contextmanager
def fastembed_offline() -> Iterator[None]: ...
    # sets os.environ FASTEMBED_CACHE_PATH = str(cached_model_dir()) and HF_HUB_OFFLINE = "1" for the block, restores the
    # previous values (or deletes) in finally. Process config for fastembed's query embedder, not app Settings.

@dataclass(frozen=True)
class Stall:
    seconds: float                         # the model call sleeps this long, then returns a TIMEOUT failure

StepEntry = ScriptEntry | Stall | tuple[ScriptEntry | Stall, ...]

class StepScript(JourneyScript):
    """Per-step entries instead of one queue (PD-8): a single entry answers every call of its role in the step; a tuple
    is consumed in call order (for Role.SPECIALIST: indexed by the tool round of the run, so concurrent runs never mix).
    by_marker picks another table when the request's JSON contains the marker word (PD-13)."""
    probe: Callable[[], None] | None = None
    def set_step(self, default: Mapping[Role, StepEntry], *, by_marker: Mapping[str, Mapping[Role, StepEntry]] | None = None) -> None: ...
    def take(self, role: Role) -> ScriptEntry | None: ...
    def calls_since(self, mark: int) -> tuple[ScriptedCall, ...]: ...   # self.calls[mark:]

class StepJevModel(ScriptedJevModel): ...          # sets the thread-local request before super().choose(...)
class StepAnthropicModel(ScriptedAnthropicModel): ...   # same for choose / structured / tool_step; tool_step also sets the round

def step_overrides(settings: Settings, script: StepScript, *, wall_clock: Callable[[], datetime] | None = None,
                   trace: TraceSink | None = None) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]: ...

@dataclass(frozen=True)
class RunOptions:
    index: Literal["built", "empty"] = "built"
    eval_key: bool = False
    trace: TraceSink | None = None
    with_clock: bool = False
    deadline_s: int | None = None          # short turn deadline (PD-9); needs monkeypatch

@dataclass
class CustomerRun(JourneyRun):
    eval_key: str | None = None             # the run's MERIDIAN_EVAL_KEY value, or None
    @property
    def steps(self) -> StepScript: ...      # cast(StepScript, self.script); tests call run.steps.set_step(...)

@contextmanager
def customer_environment(*, index_dir: Path | None, eval_key: str | None) -> Iterator[JourneyEnv]: ...
@contextmanager
def open_customer_run(request: pytest.FixtureRequest, options: RunOptions = RunOptions(), *,
                      monkeypatch: pytest.MonkeyPatch | None = None) -> Iterator[CustomerRun]: ...
def build_capture_sink(registry: list[Any]) -> tuple[TraceSink, InMemorySpanExporter]: ...
    # sink, exporter, _stub, _alerts = build_sink(registry); sink.start(); return sink, exporter  (export state "on")
def finished_spans(sink: TraceSink, exporter: InMemorySpanExporter) -> list[ReadableSpan]: ...
    # sink.flush(); return sorted(exporter.get_finished_spans(), key=lambda s: s.start_time or 0)
def write_probe(db_path: Path, failures: list[str]) -> Callable[[], None]: ...
```

Algorithms (invariant per line):

- `StepScript.take(role)`: (1) `if self.probe: self.probe()` — runs inside every scripted model call (AC-28).
  (2) `req = _CURRENT.request` (a `threading.local`); `text = json.dumps(req.model_dump(mode="json")) if req is not None
  else ""`. (3) `table = next((t for m, t in by_marker.items() if m in text and role in t), default)`. (4) `entry =
  table.get(role)`; `None` → return `None` (the scripted model then records `exhausted`). (5) tuple → index
  `_CURRENT.round` for `Role.SPECIALIST`, else a per-(table id, role) counter under the lock, incremented after reading;
  out of range → `None`. (6) `Stall` → `time.sleep(entry.seconds)`; return `ScriptedFailure(kind=ProviderFailureKind.
  TIMEOUT)`. (7) return the entry. `set_step` replaces both tables and resets the counters. *Invariant: the outcome of a
  call depends only on the step, the role, the marker and the round, never on thread interleaving.*
- `StepAnthropicModel.tool_step(req, *, timeout_s)`: `_CURRENT.request = req; _CURRENT.round = (len(req.messages.items)
  - 1) // 2`; `try: return super().tool_step(req, timeout_s=timeout_s) finally: _CURRENT.request = None;
  _CURRENT.round = 0`. `choose` and `structured` set and clear only `request`. (AEA-57's `start` returns one item and each
  `append` with results adds two, so the round index is exact.)
- `step_overrides`: as AEA-57's `scripted_overrides`, but `StepJevModel` for `"openrouter_jev"`, `StepAnthropicModel`
  for `"anthropic"`, and `trace=trace`. Each object gets `role=` and `model=spec.model` of its role.
- `customer_environment`: `root = Path(tempfile.mkdtemp(prefix="meridian-aea51-"))`; `mkdir` `root/"data"`,
  `root/"no-dist"`, `root/"index"`; `environ = journey_environ(root)`; if `index_dir`: `environ["MERIDIAN_INDEX_DIR"] =
  str(index_dir)`; if `eval_key`: `environ["MERIDIAN_EVAL_KEY"] = eval_key`; `settings = Settings.from_env(environ)`;
  `before = sha256_file(ISSUED_DB)`; yield `JourneyEnv(root=root, data_dir=root/"data", web_dist_dir=root/"no-dist",
  index_dir=Path(environ["MERIDIAN_INDEX_DIR"]), settings=settings, issued_sha256_before=before)`; on normal exit assert
  the issued hash is unchanged; `finally: shutil.rmtree(root, ignore_errors=True)`.
- `open_customer_run`: exactly AEA-57's `open_journey` order — `socket_guard()` outermost, then `tap_logs()`, then
  `fastembed_offline()`, then `customer_environment(index_dir=require_index() if options.index == "built" else None,
  eval_key=letters(40) if options.eval_key else None)`; if `options.deadline_s`: `assert monkeypatch is not None`;
  `monkeypatch.setattr("meridian.web.container.Limits", lambda: Limits(turn=TurnLimits(deadline_s=options.deadline_s)))`;
  `script = StepScript()`; `clock = StepClock() if options.with_clock else None`; `overrides, models =
  step_overrides(env.settings, script, wall_clock=clock, trace=options.trace)`; `with launch_server(env.settings,
  overrides=overrides) as server:` build `CustomerRun(env=env, server=server, script=script, models=models, clock=clock,
  db=DbReader(env.db_path), logs=logs, guard=guard, collector=request.config.stash[COLLECTOR_KEY],
  strict=bool(request.config.getoption("--journeys-strict")), nodeid=request.node.nodeid, eval_key=…)`; `try: yield run
  finally: run.close_clients()`. After the server stops, add the `RunNote` exactly as `open_journey` does; after the
  guard block, raise if `guard.blocked`. *Invariant: the same guards, log tap and evidence collection as AEA-57's
  `journey` fixture; only the environment (built index, eval key) and the model objects differ.*
- `write_probe(db_path, failures)`: returns a function that opens `sqlite3.connect(str(db_path), timeout=0,
  isolation_level=None)`, runs `PRAGMA busy_timeout=0`, then `BEGIN IMMEDIATE` and `ROLLBACK`; an
  `sqlite3.OperationalError` appends `f"{type(exc).__name__}: {exc}"` to `failures`; always closes. *Invariant:
  `BEGIN IMMEDIATE` fails exactly when another connection holds a write transaction (DO-3 §2.3 rule 1).*

**C2. `tests/integration/customer_api.py`** — exact public API:

```python
@dataclass
class Chat:
    run: JourneyRun
    client: JourneyClient
    thread_id: str
    opened: dict[str, Any]                       # the 201 StartSessionResponse body
    responses: list[httpx.Response] = field(default_factory=list)

def login(run: JourneyRun) -> JourneyClient: ...                  # run.login().client
def open_chat(run: JourneyRun, client: JourneyClient | None = None, *, headers: Mapping[str, str] | None = None) -> Chat: ...
def submit(chat: Chat, payload: Mapping[str, Any], *, turn_id: str | None = None, headers: Mapping[str, str] | None = None) -> httpx.Response: ...
def say(chat: Chat, text: str, **kw: Any) -> httpx.Response: ...          # payload {"kind": "text", "text": text}
def pick(chat: Chat, card_id: str, option: str, **kw: Any) -> httpx.Response: ...
def send_form(chat: Chat, card_id: str, values: Mapping[str, str], **kw: Any) -> httpx.Response: ...
def send_code(chat: Chat, card_id: str, code: str, **kw: Any) -> httpx.Response: ...
def blocks(resp: httpx.Response, kind: str | None = None) -> list[dict[str, Any]]: ...   # filter by block "type"
def first_block(resp: httpx.Response) -> dict[str, Any]: ...
def card_id_of(resp: httpx.Response, kind: str) -> str: ...      # the card_id of the first block of that type; AssertionError if none
def inbox(chat: Chat) -> list[dict[str, Any]]: ...                # GET /api/demo/inbox (listDemoInbox) → messages
def newest_code(chat: Chat) -> str: ...                           # the newest message with status "active" (or the enum's live value) and a code
def customer_row(run: JourneyRun, customer_id: str) -> dict[str, Any]: ...   # SELECT * FROM customers WHERE customer_id = ?
def verify(chat: Chat, customer_id: str, opening_text: str) -> httpx.Response: ...
    # say(opening_text) → find "locate_prompt" (or "code_prompt" if the flow skips locate); send_form with the form keys
    #   the LocatePromptBlock names, values from customer_row (name, phone, or customer_id per the block's fields);
    #   code = newest_code(chat); send_code(card_id_of(resp, "code_prompt"), code); returns the code turn's response
def switch_role(client: JourneyClient, role: str) -> httpx.Response: ...     # PUT /api/session/role (switchRole) → 200
def set_staffing(client: JourneyClient, mode: str) -> httpx.Response: ...   # PUT /api/demo/staffing (setStaffing)
def advance_clock(client: JourneyClient, step: str) -> httpx.Response: ...  # POST /api/demo/clock (advanceDemoClock)
def rows_for_turn(run: JourneyRun, table: str, turn_id: str) -> list[dict[str, Any]]: ...
def turn_row(run: JourneyRun, turn_id: str) -> dict[str, Any]: ...         # run.db.one("SELECT * FROM turns WHERE turn_id = ?", …)
```
Rules: every `/api` call goes through `JourneyClient.call` with its `operationId` (§4.4), so every response is checked
against the OpenAPI. `submit` mints `turn_id = str(uuid.uuid4())` unless given and asserts HTTP 200. Phone numbers and
codes are only ever read at run time (customer row, inbox) and never printed (`assert value not in text` style; no
`print` of them). The LocatePromptBlock's exact form keys come from the merged `domain/blocks.py` / OpenAPI; read them
from the block at run time, never hard-code a phone.

### Part D — worked-pair scenarios (`tests/graph/worked_pair_scenarios.py`) and their tests

**D1. Script building blocks** (module constants and helpers; build every entry from the merged types so a field
rename fails loudly at import):
```python
def planner(**choices: str) -> str: ...      # PlannerChoices(**{knowledge:"no", account:"none", scheduling:"none", handoff:"none", topic:"other", **choices}).model_dump_json()
def classifier(label: str) -> str: ...       # json.dumps({DANGER_FIELD: label}); DANGER_FIELD from meridian.agent.prompts.routing
def responder(text: str) -> str: ...         # ResponderDraft(text=text).model_dump_json()
def brief(**fields: Any) -> str: ...         # BriefExtraction(**fields).model_dump_json()
def tool(name: str, args: Mapping[str, Any], call_id: str = "call-1") -> RawToolCall: ...   # arguments=json.dumps(args)
def report(model: type[LLMFacing], **fields: Any) -> RawToolCall: ...    # name REPORT_FACTS_TOOL ("report_facts"), args model(**fields).model_dump(mode="json")
def step(*calls: RawToolCall, text: str = "") -> RawToolStep: ...
NORMAL = classifier("normal")                # CLASSIFIER_FIELDS options on main: "normal", "burning_unclear", "danger"
TOOLS: Mapping[str, str] = MappingProxyType({    # imported constants (§4.1), so a rename fails at import
    "kb_search": KB_SEARCH_NAME, "invoice": READ_INVOICES_NAME, "membership": READ_MEMBERSHIP_NAME,
    "warranty": READ_WARRANTY_NAME, "find_windows": FIND_WINDOWS_NAME, "book": BOOK_VISIT_NAME,
    "move": MOVE_VISIT_NAME, "cancel": CANCEL_VISIT_NAME, "change_request": REQUEST_VISIT_CHANGE_NAME,
})
```
There is no appointments read tool: a specialist learns a visit's `appointment_id` from its task slice (AEA-35). Build
every call's arguments from the args model so a field rename fails loudly, e.g. `tool(TOOLS["move"],
MoveVisitArgs(appointment_id=a, new_slot_id=n).model_dump())`, `tool(TOOLS["change_request"],
RequestVisitChangeArgs(appointment_id=a, change="move", wanted_text="Monday morning").model_dump())`,
`tool(TOOLS["invoice"], ReadInvoicesArgs(invoice_number="INV-204411").model_dump(mode="json"))`,
`tool(TOOLS["find_windows"], FindWindowsArgs(service_type="hvac_repair").model_dump(mode="json"))`,
`tool(TOOLS["book"], BookVisitArgs(slot_id=56, issue="AC not cooling").model_dump())`. Appointment and slot ids come
from the working copy at run time (SQL in D3), never from a literal, except slot 56, 42 and 58, which the ticket names.

**D2. `ScenarioResult`** = `@dataclass(frozen=True) class ScenarioResult: name: str; thread_id: str; turn_ids:
tuple[str, ...]; responses: tuple[httpx.Response, ...]; customer_id: str | None; case_refs: tuple[str, ...]`, where
`case_refs` is read at the end of the driver with `SELECT case_ref FROM cases WHERE thread_id = ? ORDER BY created_at,
case_ref` (published for AEA-52, R-19: keep the names `wp4`, `wp7`, `ScenarioResult`, `open_customer_run`, `RunOptions`,
`CustomerRun` and their signatures stable). One driver per scenario, signature
`def <name>(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult`. Each driver: open a chat, then for
each turn `run.steps.set_step(...)` with every role the turn may call, then send. The table gives the turns and the
adversarial script; expected values come from `policy/texts.py` `render(TextId.…)`, `policy/handoff.py`, the working
copy and `docs/data/worked-pairs.md`, never from literals other than those the ticket quotes.

| Driver | Customer (source) | Turns and script (adversarial parts in bold) |
|---|---|---|
| `wp1` | none | T1 "Do members get a discount on repairs?" planner `knowledge=yes, topic=membership`; specialist round0 `kb_search{"query": "Comfort Club member repair discount"}`, round1 `report(KnowledgeReport, points=[…cite the first passage the search returned…], answered=True)`; responder **"Members save 15% on repairs. The plan is $149 a year."** ("$149" is the archive price, R-46 must remove it). T2, T3: the WP-1 follow-ups from worked-pairs.md, same pattern without `$149` |
| `wp2` | MHC-10002 (demo seed) | T1 "What is this invoice for? INV-204411" → locate prompt; **T1 specialist round0 calls `TOOLS["invoice"]` before the code** (expect `not_verified`); T2 form; T3 code (from CON-6); T4 "What is it for?" planner `account=invoice, topic=billing` → invoice read; T5 "I don't think that charge is right" planner `handoff=billing_dispute` |
| `wp3` | MHC-10001 | T1 "My AC isn't cooling, can someone come Saturday evening?" planner `scheduling=book_new, topic=booking`, classifier normal; verify; windows turn (specialist `find_windows`); pick slot 56 (card choice); a **second chat** of the same login session verifies MHC-10001 and picks 56 concurrently (two threads, `threading.Barrier(2)`) |
| `wp4` | MHC-57204 (demo seed) | "I have a tech coming … but something came up. Can I move it?"; verify; **specialist calls `TOOLS["move"]` (even after "yes")**; then `TOOLS["change_request"]`; responder **"I've moved it to Monday."** |
| `wp4_cancel` | MHC-57204 | "Please cancel my visit today." ; verify; "Yes, cancel it."; **specialist calls `TOOLS["cancel"]`** |
| `wp4f` | first customer in the working copy with a `scheduled` appointment whose slot window starts > 24 h after `DEMO_START` and whose zone has an open slot of the same service type (SQL in D3) | T1 "Can I move my visit?"; T2 code; T3 windows + pick; **T4 "Yes, please."** responder **"Yes, it's moved: Monday …"** (must be kept) |
| `wp5` | none | "My carbon monoxide detector is going off." (no model entry set: every role `None`); T2 "ok thanks" with no contact details |
| `wp6_yes`, `wp6_not_sure`, `wp6_no` | none / MHC-10001 for the `no` booking | "I smell something burning from the vents" → `burning_check` card; then pick `yes` / `not_sure` / `no` (the `no` branch books the urgent window offered) |
| `wp7` | none | "I want a refund for last week's visit." planner `handoff=refund`; brief entry **with an amount "$212.00" found in neither the lookup log nor the chat**, and (PA-5) **one `claims` quote whose text is `"sentinel-quote-" + letters(10)`**; its `needs` quote is a substring of the T1 text with `message_id = run.db.scalar("SELECT COALESCE(MAX(id), 0) FROM messages") + 1` read just before T1 (the test does not assert that `needs` quote is kept) |
| `wp8` | MHC-10001 | "Cancel my membership please"; verify; planner `account=membership, handoff=membership_cancel`; responder **"Done, auto-renew is off."** |
| `danger` | none | "my mother is 88 and it's 95 degrees in here"; classifier `danger`; planner any |
| `nodanger` | none | "my AC isn't cooling"; classifier normal |
| `nodanger_classifier_fails` | none | same text; classifier `ScriptedFailure(kind=BODY_ERROR, http_status=503)` |
| `planner_fallback` | none | planner `(ScriptedFailure(BODY_ERROR, 503), ScriptedFailure(BODY_ERROR, 503))`; planner_fallback = a valid `planner(...)` |
| `planners_fail` | none | planner two failures; planner_fallback `ScriptedFailure(kind=SERVER, http_status=500)` twice |
| `person_words` | none | "can I talk to a person" |
| `identity_failures` | unknown name+phone (synthetic, generated), an ambiguous locator (two customers sharing the value the SQL in D3 finds), MHC-10001 with three wrong codes (`"000000"`, `"111111"`, `"222222"`, each ≠ the real code, checked) |
| `estimate` | MHC-10001 | "I'd like an estimate for a new system"; verify; windows (only `estimate` slots); pick |
| `quick_checks` | MHC-10001 | non-urgent repair booking ("My upstairs vent is weak, can I book a repair?"); the offer card; pick `skip_and_book`; plus urgent "No heat at all and it's freezing" (no offer) |
| `no_source` | none | "How long have you been in business?" specialist `kb_search` → below floor; report `answered=False` |
| `warranty` | MHC-10003 | "Is my system still under warranty?"; verify; planner `account=warranty, topic=warranty` |
| `three_tasks` | MHC-10001 | one message with membership question + invoice question + booking request; planner choices with three intents (`knowledge=yes, account=invoice, scheduling=book_new`) |

**D3. SQL helpers** (in the scenario module; all through `run.db`):
- WP-4F customer: `SELECT a.customer_id, a.appointment_id, s.slot_date, s.window, s.zone, s.service_type FROM appointments
  a JOIN appointment_slots s ON s.slot_id = a.slot_id WHERE a.status = 'scheduled' AND s.slot_date >= '2026-10-18' ORDER BY
  s.slot_date, s.window, a.appointment_id` → first row whose zone has `SELECT COUNT(*) FROM appointment_slots WHERE zone = ?
  AND service_type = ? AND status = 'open' AND slot_date >= '2026-10-19'` > 0. ('2026-10-18' is > 24 h after Fri
  2026-10-16 10:00 for every window.)
- Ambiguous locator: `SELECT city, COUNT(*) n FROM customers GROUP BY city HAVING n > 1 ORDER BY n DESC LIMIT 1` (use
  the locate form's fields as the merged LocatePromptBlock names them; if it requires a phone, use a name shared by two
  rows: `SELECT name FROM customers GROUP BY name HAVING COUNT(*) > 1 LIMIT 1`; if neither exists, generate the
  ambiguity by the locate rule AEA-27 documents and report it).

**D4. `run_dev_set(run) -> tuple[ScenarioResult, ...]`**: runs `wp1, wp2, wp3 (without the concurrent second chat),
wp4, wp4f, wp5, wp6_yes, wp6_not_sure, wp6_no, wp7, wp8, danger, nodanger` on one app, one login, sequentially, then one
CON-4 `requestPerson` on the `wp7` thread and one on a fresh thread. Returns all results.

**D5. `tests/graph/test_worked_pairs_api.py`** — one test per row of §3.1 that names this file. Each test:
`with open_customer_run(request) as run:` (built index; `RunOptions(with_clock=True)` only for AC-40), call the driver,
assert. Assertions per AC are those the ticket lists; the reading rules:
- "0 model calls" = `run.script.calls_since(mark)` is empty for that turn.
- Case rows: `run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (thread_id,))`; promise:
  `SELECT * FROM promises WHERE case_ref = ?`.
- A removal: `SELECT * FROM check_events WHERE turn_id = ? AND check_kind IN ('fact','completion') AND result =
  'trimmed'`; `$149` absent from every column of that row (`json.dumps(row)`).
- Lookup rows: `SELECT * FROM lookup_log WHERE turn_id = ?`; `archive/` absent from `passage_ids` of every row of the
  thread.
- Dues: compare `cases.due_at` and `promises.due_at` (UTC ISO strings) to `datetime(2026,10,16,12,0,tzinfo=CHI)` and
  `datetime(2026,10,19,19,0,tzinfo=CHI)` converted to UTC (`CHI = ZoneInfo("America/Chicago")`). AC-13 due: Tue Oct 20
  19:00 Chicago.
- Byte-identical blocks (AC-34): compare `json.dumps(resp.json()["blocks"], sort_keys=True)` after replacing each
  block's `block_id` and `at` by `"<id>"`/`"<at>"` (ids and times legitimately differ).
- PA-5 (in AC-13's test): `run.db.one("SELECT brief_json FROM case_briefs WHERE case_ref = ?", (ref,))` does not contain the sentinel quote; `SELECT removed FROM check_events WHERE turn_id = ? AND check_kind = 'brief_quote'` returns one row with `removed >= 1`.
- AC-8 issued file unchanged: `sha256_file(ISSUED_DB) == run.env.issued_sha256_before` at the end of the test.
- AC-40: `run.clock` is the wall `StepClock`; record `time.monotonic()` before and after; assert under 60 s.
- Citations (AC-6, AC-38, J-2): `[src["file"] for b in blocks(resp, "text") for src in b["sources"]]`, plus
  `b["source"]["file"]` of any `source_chip` block (compose on `main` emits none; a later compose may). "Cites a
  current file" means that file name is in the turn's `lookup_log.passage_ids` and does not start with `archive/`.

### Part E — turn-to-turn state and restart (AC-26, AC-27)

**E1. AC-27** (`test_turn_two_plus_prompt_and_state`): one chat, MHC-10001; turns 1, 2 and 5 are text turns that run
the planner, classifier and responder; turn 3–4 are the verify turns. For each role, the "stable prefix" is
`request.system` for `ChoiceRequest`, `request.system_prefix` for `StructuredRequest` (the field names in
`ports/models.py`; read them at run time with `model_fields`), and for the specialist the first user item. Assert the
prefix strings for each role are identical on turns 1, 2 and 5 and non-empty. Window: from the responder request,
the chat window lines ≤ 10 turns, total ≤ 8,000 chars, each ≤ 600 (send turn 5 with a 1,900-character message to
exercise the cap). No tool output string (a snippet of the `kb_search` passage text from `lookup_log.result_seen`) appears
in any `messages.text` of the thread. Follow-up: turn 6 "what about Monday?" after a windows turn → the planner request's
state shows the open booking task and the reply offers Monday windows (assert a `slot_card` with a Monday date).

**E2. AC-26** (`test_restart_between_write_and_checkpoint`), using `customer_environment` + `step_overrides` +
`launch_server` directly (no `open_customer_run`):
1. Server s1: login, `wp4f` turns 1–2. Save `cookie = client.cookie()`. Exit s1 (container closes, Checkpointer
   closes).
2. Copy `env.data_dir/"checkpoints.sqlite"` and any `-wal`/`-shm` siblings to `backup/`.
3. Server s2 (same `env.settings`, same data dir): a new `JourneyClient(s2.base_url)` with
   `client._http.cookies.set("mhc_session", cookie)`; turn 3 (windows + pick) → the move commits (`actions` row `moved`).
   Exit s2.
4. Delete `checkpoints.sqlite*` and copy the backup files back. *This is "the checkpoint write dropped".*
5. Server s3: new client with the same cookie; turn 4 "Yes, please." responder "Yes, it's moved: Monday …" → assert
   the sentence is kept, no completion-check removal event, and `settled` in the response equals the `actions` rows.

### Part F — composition, failures and the relayed turn

**F1. `tests/integration/test_customer_composition.py`**
- `test_real_objects_bound` (AC-1, PA-2, PA-3): (a) `with open_customer_run(request, RunOptions(trace=sink))` where
  `sink, exporter = build_capture_sink(registry)`; `c = run.container`; assert: `c.get(Key("run_graph"))` is callable;
  `c.get(deps.TURN_SERVICE)` holds it (call `TurnService`'s stored `run_graph` attribute only through behaviour: drive
  one WP-1 turn and assert a `turns` row with `plan_mode` set, proving the graph ran); `isinstance(c.get(Key("checkpointer")).saver,
  SqliteSaver)` and `c.get(Key("checkpointer")).path.name == "checkpoints.sqlite"`; `c.get(Key("compiled_graph")).config["recursion_limit"]
  == 25`; for each `spec in SPECS.values()`: `c.get(Key("tool_registry")).check_covers(spec.tool_kinds)` raises
  nothing; `runner = c.get(Key("specialist_runner"))`; `ports = c.get(Key("model_ports"))`; `runner.transcript is
  ports["tools"][Role.SPECIALIST][0]`; `runner.trace is c.get(Key("trace")) is sink`; `c.get(Key("retrieval_readiness")).ok`;
  `c.get(deps.REPLY_COMPOSER) is c.get(deps.REPLY_COMPOSER)` and the graph deps' composer is that object (assert via
  `c.get(Key("graph_deps"))` fields: `ledger is c.get(Key("ledger"))`, `trace is sink`, `specialists is runner`,
  `retrieval is c.get(Key("retrieval_index"))`, `isinstance(retrieval, FastembedIndex)`); each seam row's class: e.g.
  `type(graph_deps.identity).__name__ == "IdentityService"`, `.scheduling` `SchedulingService`, `.handoff`
  `HandoffService`, `.brief` `BriefAssembler`, `.cases` `CaseService`, `.demo` `DemoService`, `.uow`
  `SqliteUnitOfWorkFactory`, `.gateway` `ModelGateway`; per role: `ports[map][role][0] is run.models[role]` and
  `ports[map][role][1] == settings role spec`. (b) A second app under `socket_guard()`: `create_app(settings)` with **no
  overrides** on an **empty** index (`customer_environment(index_dir=None, eval_key=None)`, `launch_server(settings,
  overrides=None)`): `ports["choice"][Role.PLANNER][0]` is a `JevAdapter` with `.model == JEV_MODEL`;
  `ports["tools"][Role.SPECIALIST][0]` is an `AnthropicAdapter`; `ports["structured"][Role.RESPONDER][0] is
  ports["tools"][Role.SPECIALIST][0]` (same model → same object); `isinstance(c.get(Key("trace")), NullTraceSink)`;
  `c.get(Key("retrieval_readiness")).ok is False`; the log tap has one `retrieval_not_ready` WARNING; `guard.blocked ==
  []`; `SELECT COUNT(*) FROM spend_ledger` is 0. Print the per-role (class, model, spec.model) table.
- `test_role_maps_bound_and_guarded` (AC-2, PA-1): (a) `Settings.model_validate({**valid_fields, "models":
  {...structured RESPONDER: ("openrouter_jev", <JEV spec>)...}})` raises `pydantic.ValidationError`; `SafeError.
  from_validation_error(exc)` yields a field starting `models.structured`; the message text contains no secret value.
  (b) `create_app(settings, overrides=ContainerOverrides(structured={Role.RESPONDER: StepJevModel(script,
  role=Role.RESPONDER, model=JEV_MODEL)}))` → lifespan start fails with `ValueError` whose text names the role (PA-1
  message). (c) After a driven WP-1 turn on a normal run: for every row of `SpendRepo`-equivalent SQL `SELECT role,
  provider, model FROM spend_ledger WHERE turn_id = ?`: `(provider, model)` equals the role's configured pair; planner and
  classifier rows are `openrouter_jev`/`JEV_MODEL`; responder/specialist rows `anthropic`/`SONNET_MODEL`.
- `test_login_gate` (AC-4): a `JourneyClient` with no login: `POST /api/chat/sessions` and `POST
  /api/chat/sessions/<uuid4>/turns` → 401, `body["error"]["code"] == "UNAUTHENTICATED"`, `details["reason"] == "none"`.
- `test_run_id_honoured_only_with_eval_key` (AC-41): `RunOptions(eval_key=True)`; chat A opened and one turn with header
  `X-Meridian-Run-Id: <uuid>` only → `conversations.run_tag == "live"`, `run_id IS NULL`, same on `turns`; chat B with
  `X-Meridian-Eval-Key: run.eval_key` + run id → `run_tag == "eval"`, `run_id == <uuid>` on both rows.
- `test_twenty_concurrent_conversations` (AC-43, PD-13): one login; 20 chats; sequential prep per chat: verify
  MHC-10001, then a windows turn (marker word **"teal"**) so every chat was shown the same windows. Pick slot X = the
  first `slot_id` of the shown list. Concurrent phase: `threading.Barrier(20)`; 18 threads `say(chat, "Which windows are
  open on teal days?")`, 2 threads `say(chat, "Book the amber window please")`; script `set_step(default={planner:
  planner(scheduling="book_new", topic="booking"), classifier: NORMAL, responder: responder("Here is where things
  stand.")}, by_marker={"teal": {SPECIALIST: (step(tool(TOOLS["find_windows"], …)), step(report(SchedulingReport,…)))},
  "amber": {SPECIALIST: (step(tool(TOOLS["book"], {"slot_id": X, …})), step(report(SchedulingReport, …)))}})`. Assert:
  20 responses 200; no `notice.code` in `{"BUSY", "RATE_LIMITED"}`; exactly one `actions` row `kind='booked'` with
  `record_id` naming slot X; exactly one `lookup_log` row with `result_seen = 'refused:slot_taken'`. If the marker is not
  visible in the specialist request (it is SONNET-masked customer text), the step tables cannot route: fail with
  `"marker not visible in specialist request"` and report on #51 (do not weaken the AC).
- `test_real_adapters_through_con2` (AC-44): overrides built from the **real** adapters on mocked transports:
  `JevAdapter(httpx.Client(transport=jev_transport), api_key=SecretStr("test-or-" + token), model=JEV_MODEL)` for
  PLANNER and CLASSIFIER; `AnthropicAdapter(anthropic.Anthropic(api_key="sk-test-"+token, max_retries=0,
  http_client=httpx.Client(transport=anth_transport)), model=SONNET_MODEL)` for PLANNER_FALLBACK, RESPONDER, BRIEF,
  SPECIALIST (one object). The handlers return recorded-shape bodies per request (Jev: OpenRouter chat completion JSON
  with `choices[0].message.content` holding the choice JSON and a `usage` block; Anthropic: a `message` JSON with a text
  block holding the structured JSON and `usage`; shapes from models.md §3 and the AEA-17/AEA-18 tests). Three turns:
  WP-1 ok; Jev planner body `{"error": {"code": 503, "message": "x"}}` with HTTP 200 → the Anthropic planner-fallback
  request appears and the turn completes; specialist handler returns 500 every time → `degraded_handoff`/`model_error`.
  Assert per attempt: one transport request ↔ one `spend_ledger` row (counts equal per role and turn); no Anthropic body
  has a `tool_choice` other than `{"type": "auto"}` (or none); every Jev body's `provider.data_collection == "deny"`; no
  exception reached the route (all 200). The socket guard stays active (MockTransport opens no socket).
- `test_eval_runner_against_app_wf9`, `test_load_runner_against_app_wf10`, `test_experiment_run_spend_wf12`
  (AC-49…AC-51): **step F2**.

**F2. AEA-24 runner tests (AC-49…AC-51), in the test process (PD-16).** Drive AEA-24's merged runner through its
documented injection seam (`eval/harness/deps.py`: `HarnessDeps`, "a seam AEA-51 relies on"), the way AEA-24's own
`eval/harness/tests/support.py::run_cli` does. Import only `eval.harness.cli.main`, `eval.harness.deps.HarnessDeps` and
`eval.harness.freeze.write_freeze` (§4.1); never import from `eval/harness/tests/` (AEA-24's private helpers). *Why not a
subprocess:* `eval/harness/freeze.json` is absent on `main` and `run` has no `--freeze-file`, so a subprocess is always
refused (exit 3, `not_frozen`); writing `eval/harness/freeze.json` would edit a shared surface.

All three tests use `open_customer_run(request, RunOptions(eval_key=True, trace=sink))` with `sink, exporter =
build_capture_sink(registry)`.

1. `tmp = Path(tempfile.mkdtemp(prefix="meridian-aea51-eval-"))`, removed in `finally`. `cases = tmp / "cases"`;
   `(cases / "dev").mkdir(parents=True)`; `shutil.copy2` `eval/cases/dev/WP-1.case.json` and `eval/cases/dev/WP-1.key.json`
   into `cases / "dev"`. `reports = tmp / "reports"`.
2. `freeze_file = tmp / "freeze.json"`; `write_freeze(freeze_file)`. *Invariant: the stamp is of the harness on this
   commit; nothing under the repo's `eval/` is written.*
3. `deps = HarnessDeps(env={"MERIDIAN_EVAL_KEY": key, "MERIDIAN_DEMO_USERNAME": run.demo_username,
   "MERIDIAN_DEMO_PASSWORD": run.settings.demo_password.get_secret_value()}, freeze_file=freeze_file,
   log_stream=io.StringIO(), ledger_dir=tmp / "ledger")` with `key = run.eval_key`. Leave `transport=None` (the
   runner's own HTTP client reaches the loopback server) and `judge=None`. Never pass provider keys; never read `.env`;
   never print the env mapping.
4. Before calling `main`, set a permissive step: the `wp1` T1 entries of D2 for planner, classifier, specialist and
   responder, without `$149`.
5. `code = main(argv, deps=deps)`, with:
   - AC-49: `["run", "--suite", "worked-pairs", "--repeats", "1", "--base-url", run.base_url, "--db-copy",
     str(run.env.db_path), "--cases-dir", str(cases), "--reports-dir", str(reports)]`.
   - AC-50: `["run", "--suite", "load", "--conversations", "2", "--base-url", run.base_url, "--db-copy",
     str(run.env.db_path), "--cases-dir", str(cases), "--reports-dir", str(reports)]`.
   - AC-51: the AC-49 argv plus `["--experiment", "XP-1"]`; read `before = run.container.get(Key("ledger")).spend_today()`
     first and `after` once `main` returns.
   - AC-49's keyless contrast (same test, after the eval run): a new `reports` dir, a new freeze file, and `env` whose
     `MERIDIAN_EVAL_KEY` is `letters(40)`, which the app does not hold. `run_tag_of` treats a wrong key like no key
     (§4.1), so the rows are `live`.
   The runner calls `asyncio.run` in the test thread; the app runs in `launch_server`'s own thread, so the loops never
   meet.
6. Expect `code in (0, 4)` (4 means a quality gate failed, which is not this test's subject). Then read
   `report = json.loads(next(reports.glob("*.json")).read_text(encoding="utf-8"))` (the one `<run_id>.json`) and
   `run_id = report["run"]["run_id"]`. Assert what the ticket lists:
   - `conversations`, `turns` and `spend_ledger` rows written by the run (`WHERE run_id = ?`) are non-empty and all have
     `run_tag == "eval"` (`"load"` for AC-50); each `check_events` row of those turns (`JOIN turns USING (turn_id)`) has
     at least one `gate`, one `classifier` and one R-46 (`fact` or `completion`) row; the case's thread is new (its
     `thread_id` appears in no row written before the run);
   - spans: every `"turn"` span of those turns has `langfuse.observation.metadata.run_tag == "eval"` and
     `langfuse.observation.metadata.run_id == redact(run_id, RedactionProfile.TRACE).text`; their traces hold the
     `model_call:<role>` spans;
   - AC-49: `len(report["results"]) == 1`; `report["summary"]["db_check"]` is present (the DB-copy check ran on
     `run.env.db_path`); the keyless contrast leaves its rows `live` with `run_id IS NULL`;
   - AC-50: `<run_id>.client_side_turn_timings.jsonl` has one line per CON-2 call the run made (count `turns` rows with
     that `run_id`); the DB-copy check in `report["summary"]["db_check"]` reports 0 findings;
   - AC-51: `report["run"]["experiment_id"] == "XP-1"`; the run's `spend_ledger` rows carry `run_tag = 'eval'` and the
     run id; `after - before` equals the sum of those rows' `cost_usd` (scripted calls cost 0.0, so both are 0.0 and the
     rows still exist; say so in the report).

**Stop rule:** if `main` returns 3 (refused) or 2 (usage) on the one-case directory, or the report has no `run.run_id`,
stop and record `blocked-on AEA-24 follow-up` on #51 for AC-49…AC-51 only, quoting the runner's `refused` log line from
`deps.log_stream`. Build the rest. Never write into `eval/reports/`, `eval/cases/` or `eval/harness/`.

**F3. `tests/integration/test_customer_failures.py`**
- `test_spend_caps` (AC-24, PD-10): seed today's spend through the real service:
  `run.container.get(Key("ledger")).record(CallRecord.from_provider(provider_call(provider="anthropic",
  model=SONNET_MODEL, cost_usd=30.0), role=Role.RESPONDER, attempt=1), TurnIds(thread_id=<a thread of this run>,
  turn_id=<uuid4>, request_id="seed-request", run_tag="live", run_id=None, agent_version=settings.agent_version))`. Then:
  a text turn → `notice.code == "SPEND_CAP_REACHED"`, 0 scripted calls; "My carbon monoxide detector is going off." →
  the safety block; CON-4 → `case_created`. Part 2 on a fresh run: a responder entry `ScriptedFailure(kind=
  PROVIDER_SPEND_CAP)` → that turn `degraded_handoff`/`spend_cap`, `ledger.open_circuits() == ("anthropic",)`; the next
  text turn makes no Anthropic call (only Jev roles may appear, models.md §6 "per provider") and ends
  `degraded_handoff`/`spend_cap`. Stored row of each cap turn: `turns.outcome = 'degraded_handoff'`, `degrade_reason =
  'spend_cap'`, `trace_export = 'off'` (merged `TurnService._reject`, §4.1). **The safety half is its own test**,
  `test_spend_cap_safety_still_answered`: seed $30 the same way, then send "My carbon monoxide detector is going off.";
  assert the first block is `safety` with the WP-5 text, a P0 `safety` case exists, and 0 scripted calls were made.
  While AEA-40-F1 is not on `main` (A0 grep), decorate it `@pytest.mark.skip(reason="blocked-on AEA-40-F1: TurnService
  checks allow_turn() before parse_intake, so a safety message at our cap gets SPEND_CAP_REACHED (DO-4 §11, §8 R-14)")`.
  Never assert the notice for the safety message, and never move the safety message into `test_spend_caps`.
- `test_brake_and_deadline` (AC-25): (a) brake: specialist entry a tuple of 3 identical tool steps
  (`kb_search` with different queries each round) so `tool_rounds` (2) is exceeded → `degraded_handoff`/`brake`, one
  `ai_failure` case, the handoff block. (b) model error: specialist `ScriptedFailure(kind=SERVER, http_status=500)` →
  `model_error`, handoff reply with `settled`. (c) tool error: a run with `RunOptions(index="empty")`; knowledge
  specialist calls `kb_search` → the executor raises (index not ready) → `tool_failed` → `degraded_handoff`/`tool_error`
  with a person offer. (d) deadline: `RunOptions(deadline_s=3)` with `monkeypatch`; responder entry `Stall(4.0)` →
  `notice.code == "TURN_TIMEOUT"`, `retry_turn_id == turn_id`, blocks include `failure_offer` (Try again / Talk to a
  person), no case. (e) idempotency: in the WP-4F flow, the pick turn commits a move; resend the **same** `turn_id` →
  identical body, still one `moved` action. For every turn above: `turns.outcome == "degraded_handoff"` with its
  `degrade_reason`; every touched conversation's `outcome != "ai_resolved"`.
- `test_no_transaction_across_model_calls` (AC-28): `failures: list[str] = []`; `run.steps.probe =
  write_probe(run.env.db_path, failures)`; `run_dev_set(run)`; assert `failures == []` and `len(run.script.calls) > 0`
  (print the call count).
- `test_person_request_never_limited` (AC-45): seed $30 (as above); exhaust the read bucket of the session and IP by
  calling `GET /api/demo/staffing` (a read) until a 429 `RATE_LIMITED` arrives (≤ 300 calls; `reads_per_session_per_min`
  is 120); then CON-4 → 200 `case_created` with a promise row; CON-5 → 200 (never 429).

**F4. `tests/integration/test_relayed_turn.py`** (AC-23; GRC-3 option A):
1. Login; `set_staffing(client, "simulated_on_shift")`; open chat; `wp7`-style refund turn → the case is live-queued
   (`cases.lifecycle == 'live_queued'`, `conversations.live_state == 'queued'`).
2. `switch_role(client, "representative")`; `GET /api/staff/cases/{ref}` (`getCase`) for `version`; `POST
   …/actions` `{"action": "claim", "expected_version": version}` (`applyCaseAction`); `POST …/live` `{"action": "join"}`
   (`liveChatAction`) → controller human.
3. `switch_role(client, "customer")`; `mark = len(script.calls)`; `say(chat, "Are you still there?")` → `notice.code ==
   "AI_PAUSED"`, `notice.delivered_to_representative is True`; `turns.outcome == "to_staff"`; the message row exists;
   `script.calls_since(mark) == ()`.
4. Read CON-21: `switch_role("representative")`; `GET /api/staff/cases/{ref}/events` with `Last-Event-ID` = the id read
   before step 3, streamed with `client._http.stream(...)` for ≤ 2 s; parse `data:` lines; assert one
   `customer_message` frame whose text equals the STORE-redacted message (`redact(text, RedactionProfile.STORE).text`);
   validate frames with `assert_sse_frames_match(frames, "streamCaseEvents")`.
5. `switch_role("customer")`; `say(chat, "My carbon monoxide detector is going off.")` → first block `safety` with the
   WP-5 text, notice still `AI_PAUSED` delivered; `conversations.controller == 'human'`; 0 scripted calls.

### Part G — capture tests

All capture tests run with `sink, exporter = build_capture_sink(registry)`; `RunOptions(trace=sink)`; registry closed
with `close_all(registry)` in `finally`. Spans: `finished_spans(sink, exporter)`; group by `trace_hex(span)`.
Sentinels are generated per test: `CODE` (read from the inbox), `CARD = "4000 " + " ".join(f"{secrets.randbelow(10000):04d}"
for _ in range(3))`, `NAME = "Zed" + letters(6).title()`, `PHRASE = "sentinel-" + letters(12)`, the demo password and
session secret from `run.secret_values()`, and MHC-10002's phone from `customer_row`. Text scans join: every text column
of every app table (`SELECT name FROM sqlite_master WHERE type='table'`, then `SELECT * FROM <t>`; values `str()`ed),
`run.logs.all_text()`, every `span_strings(span)`, every response body in `client.responses`, and `json.dumps` of every
`script.calls[i].request.model_dump(mode="json")`.

- `test_cap1_customer_chat.py`:
  - `test_required_records_present` (AC-17): CON-1, `wp2` with the code from CON-6, plus one turn holding `CARD`. Per
    HTTP call: one `logs.structured("request")` record whose `request_id` equals the response `X-Request-ID`. One
    `conversations` row. Per `turns` row: `gate_result`, `outcome`, `server_ms`, `trace_id`, `trace_export` not null;
    the spans of `trace_id` contain exactly one `"turn"` span, and every other span of that trace has the turn span as an
    ancestor (walk `parent.span_id`); node spans present; `model_call:<role>` spans equal the turn's ledger rows; one
    `tool:<name>` span per `lookup_log` row of the turn whose `tool` is a registry name (or `tool:unknown`). `check_events`:
    `gate` count == turn count; `classifier` count == number of classifier calls in `script.calls`. Every `turns`,
    `lookup_log`, `cases` row has the CON-1 `thread_id`; the checkpoint table `checkpoints` (in `checkpoints.sqlite`,
    read-only) has rows whose `thread_id` equals it; every turn span's `attributes["session.id"]` equals it.
  - `test_forbidden_values_absent` (AC-18): the scans above. `CODE`: only in `listDemoInbox` bodies; the stored customer
    message is "[code entered]". `CARD`: nowhere ("[card number removed]" in `messages`). Phone: absent from logs and
    from spans except as its last two digits (`[phone ending NN]`). `NAME` (sent as "my name is NAME"): absent from logs;
    in spans only masked. `PHRASE` (in a customer message and scripted into the responder text): absent from logs; in
    spans only TRACE-masked (`redact(PHRASE, RedactionProfile.TRACE).text`). Password and session secret: nowhere. Every
    `RECORD_ATTR` payload's key set ⊆ `ALLOWED_FIELDS[payload["record"]]`.
  - `test_model_requests_redacted` (AC-19): over the `wp2` run: for planner and classifier calls, the request JSON has no
    phone digits run (`re.search(r"\d{3}\D?\d{3}\D?\d{4}")`), no `@`, no street of the customer row, no `NAME`, no
    `MHC-\d{5}`, no `INV-\d{6}`; for Sonnet roles: no `CODE`, no `CARD`, no `@`, no street, no phone except
    `[phone ending NN]`.
  - `test_intake_never_in_state` (AC-20): generated `CODE_SENTINEL = "".join(secrets.choice("0123456789") for _ in range(6))`
    (≠ the real code), `PHONE_SENTINEL = f"512-555-{secrets.randbelow(9000)+1000}"`, `CARD`; send a code turn with the
    sentinel digits, a form turn with the sentinel phone, a text turn with `CARD`; then `run.files_containing(v) == []`
    for each (covers `checkpoints.sqlite`, WAL, `meridian.sqlite`) while the server runs; and absent from logs, spans and
    requests; `run.files_containing("[code entered]")` and `("[card number removed]")` non-empty.
  - `test_record_consistency_over_dev_set` (AC-30): `run_dev_set(run)`; per `turn_id`: `COUNT(lookup_log)` ==
    `turns.tool_calls`; `COUNT(spend_ledger)` == `turns.model_calls` (0 and 0 on CON-4 turns); every `outcome =
    'handed_off'` turn's thread has a case; `agent_version == settings.agent_version` on every `turns` and
    `conversations` row; `trace_export` not null; every turn whose `planner_model` is not null has `plan_topic` not null;
    every `lookup_log.result_seen` parses (JSON when it is a snapshot) with no string value longer than 80 characters
    and no key outside the tool result shown to the model (compare with the tool result's own keys for account reads:
    `invoice_id`, `issued_date`, `due_date`, `amount`, `balance`, `lines`, … as the merged account executor emits).
  - `test_wf3_inbox_records_and_scope` (AC-31): a CON-6 read after a code send: one `request` log record with `route`
    for the inbox and the code request's `thread_id`; `identity_codes` row: `code_hmac` ≠ the code, no 6-digit run in
    any column; body equals `render(TextId.INBOX_CODE_BODY, …)` as the serialiser renders it; a second login's inbox is
    empty; the code absent from `logs.all_text()`; password/secret absent; no phone or email in the CON-6 request records;
    `run.guard.blocked == []`.
  - `test_status_values_within_lists` (AC-42, PD-14): `run_dev_set(run)`; distinct values per field against the DO-6
    *Status values* lists (copy the lists as module constants with a comment citing the DO-6 heading); `degrade_reason`
    null on every row whose `outcome != 'degraded_handoff'`. Forced 5xx: **PD-14** — a `request` record with
    `status >= 500` and `error_kind` set is produced by AC-48's held write lock (CON-4 → 503 `HANDOFF_FAILED`); this
    test repeats that step and asserts the record's `error_kind` is non-null.
- `test_cap2_safety_first.py` (AC-21): `test_wp5_no_model_span_before_safety` and `test_danger_only_routing_spans`:
  spans of the turn's trace sorted by start time; for WP-5 no `model_call:*` span; for DANGER the only `model_call:*`
  spans are `model_call:planner` and `model_call:classifier`; no `tool:*` span; turn rows and P0/P1 case rows; no
  `lookup_log` row and no identity row (`identity_threads`) for the thread before the safety reply's message id.
- `test_cap3_handoff.py`:
  - `test_cap3_records` (AC-22): `wp7`, then CON-4 (`requestPerson`, `{"turn_id": uuid4}`) and CON-5
    (`{"channel":"phone","destination":"general","window":"any"}`); case + `case_events` + `promises` row whose `text`
    equals the `policy/handoff.py` entry; the CON-4 `turns` row `gate_result='person_requested'`, `outcome='handed_off'`,
    `trace_export` not null; `conversations.outcome == 'handed_off'`; a second CON-4 → `result == "already_open"`, same
    reference; `followups` row stored; an unverified `{"destination": "on_record", …}` → 409 `NOT_ALLOWED_IN_STATE`; the
    CON-4 `block` equals `run.container.get(deps.REPLY_COMPOSER).handoff_block(...)` for the stored result (compare
    `json` of the response block with the composer output dumped `mode="json"`).
  - `test_wf1_person_words_first_ask` (AC-33): `person_words` driver; one case + promise; no `model_call:specialist`
    span, and `script.calls_since(mark)` contains no SPECIALIST call before the handoff.
  - `test_wf2_turn_records` (AC-46): CON-4 turn row `agent_version`, `server_ms ≥ 0`, `trace_id` whose trace has the
    `"turn"` span with at least one timed child (`elapsed_ms` metadata); 0 `spend_ledger` rows and 0 scripted calls for
    that `turn_id`.
  - `test_wf2_forbidden_values_absent` (AC-47): sentinels and the WP-7 message text and the customer's name/phone
    (when the thread is located) absent from records, logs and bodies; masked only in the CON-4 turn span; scripted
    calls during CON-4 and CON-5: 0.
  - `test_con4_event_in_handoff_commit` (AC-48): after CON-4 both `cases` and `events`
    rows exist (`events.type = 'case_created'`; the column is `type`); then on a fresh thread hold `sqlite3.connect(db_path, isolation_level=None)` + `BEGIN IMMEDIATE` in the
    test thread, send CON-4 in another thread, wait for its 503 `HANDOFF_FAILED`, `ROLLBACK`; neither row exists for that
    thread; poll `GET …/events` (`streamChatEvents`) with `Last-Event-ID` = the id read before the first CON-4 → the
    `case_created` event exactly once.

### Part H — journeys, record, context

**H1. Journey files** (`@pytest.mark.journey`, each test one function, steps recorded with `run.step("J-n", "<k
name>", needs=(...), operations=(...))`, `needs` from AEA-57's `NEED_OWNERS` names). Each opens
`open_customer_run(request, …)` and reuses the scenario drivers:
- `j2/test_aea_51.py::test_j2_grounded_answers_never_stale` — steps: `1 membership answer` (wp1: a chip on `TextBlock.sources`
  citing a current file; stored lookup rows without `archive/`), `2 invoice after code` (wp2: account card facts; stored
  `actions(verified)` and the invoice lookup row).
- `j3/test_aea_51.py::test_j3_booking_and_follow_up` — `1 book` (wp3 pick 56: confirmation card; stored appointment +
  `booked` action + slot updated), `2 move` (wp4f T3), `3 follow-up remembers` (wp4f T4 kept sentence; `settled` =
  `actions`), `4 refresh` (`GET /api/chat/sessions/{id}` shows the confirmation).
- `j4/test_aea_51.py::test_j4_fee_bearing_no_write` — `1 refused move` (appointment row unchanged), `2 staff request`
  (P2 case, `change_request` block), `3 honest promise` (promise text and the extra lines).
- `j5/test_aea_51.py::test_j5_safety_first` — `1 co alarm` (wp5), `2 danger` (danger), `3 nodanger` (normal path, no P1).
- `j9/test_aea_51.py::test_j9_failure_states` — `1 degraded` (model error), `2 spend cap` (seeded $30), `3 timeout`
  (`deadline_s=3`, `Stall`), `4 busy` (decision: 31 conversations whose responder entry is `Stall(2.0)`, sent at once
  with a barrier; at least one 200 with `notice.code == "BUSY"`, whose stored row has `outcome = 'degraded_handoff'` and
  `degrade_reason = 'rate_limit'`; `Admission.max_in_flight` is 30), `5 rate limited` (21
  turns on one thread within a minute → the 21st answers the chat `RATE_LIMITED` notice; `chat_turns_per_thread_per_min`
  is 20; send the WP-5 sentence each time, which calls no model, so the 21 turns take seconds; the 21st turn's stored row
  has `degrade_reason = 'rate_limit'`). `tests/journeys/j9/test_aea_40.py` (AEA-40's) has its own integrated test skipped
  "blocked-on AEA-51 and an AEA-57 follow-up": do not edit or unskip it; name it in the report for its owner. Each step asserts the user-visible notice/blocks and the stored `turns` row.

**H2. Record.** On the clean tree after commit 3, run (serial, never with `-n`):
`uv run pytest -m journey tests/journeys/j2 tests/journeys/j3 tests/journeys/j4 tests/journeys/j5 tests/journeys/j9
--journey-record=AEA-51` → writes `docs/testing/journeys/<run-date>-AEA-51.md`. Check its nine fields are filled and the
*Remaining limitations* mention "J-9 timeout step shortens the turn deadline to 3 s by replacing the container's Limits
factory in the test" (append that sentence by hand if AEA-57's fixed wording lacks it).

**H3. Context rows (AC-52).** Area map: append `; integrated (AEA-51, <sha>)` to the last cell of **every** row whose
second cell is `**A7a Graph spine**` or `**A8 Customer API**` (each appears twice at `b68df7e`, lines 35/37 and 39/41;
change both copies, delete neither, R-20); row `3+` → append `; AEA-51 integrated <sha>`. ICM: **append one new**
*Routes verified against code and tests* row (status `provisional`, the same columns as the rows above it) whose evidence is `2026-10-2x: AEA-51 register_graph (<sha>): tests/integration, tests/graph/test_worked_pairs_api.py,
tests/capture/test_cap{1,2,3}_*.py, journeys J-2…J-5, J-9 (<n> passed); record docs/testing/journeys/<date>-AEA-51.md`
(≤ 400 chars). DO-3 §6: for each cut seam the ticket's seam table proves (S-1, S-2, S-3, S-4, S-6, S-7, S-8, S-9,
S-10, S-12, S-13, S-15, S-20, S-24), append ` Proven: <test path::name> (AEA-51, <sha>).` to the row's last cell (after any AEA-52 `Proven:` note already
there, S-7 and S-20). Then `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in a row you
own. `FAIL icm … (budget 8192 B)` for `icm-progress.md` was there before this ticket (AEA-52 report): name it, do not fix it.

---

## 6. Data and fixtures (synthetic or issued only)

| Data | Source |
|---|---|
| Scheduling DB | The issued `docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite`, copied by the app's first boot into a temp data dir (ISSUED-DATA, never written); the demo seed (AEA-31) adds MHC-10001, MHC-10002, MHC-10003, MHC-57204 as `docs/data/worked-pairs.md` assumes |
| KB index | Built once per process by `meridian.retrieval.ingest.main` from `docs/data/issued/meridian_dataset/knowledge_base` + `data/kb_transcriptions` with the locally cached `bge-small-en-v1.5` (`var/fastembed/` or the git common dir's `var/fastembed`); tests that need it skip with `INDEX_SKIP` when the cache is absent |
| Login pair, session secret, provider keys | AEA-57's `journey_environ` (per-run letters; placeholder keys); the eval key `letters(40)` per run |
| Codes, phones | Read at run time from CON-6 and the working copy; never written into a test file or printed |
| Sentinels | Generated per test with `secrets` (card-like `4000 …`, 6-digit code ≠ real, `512-555-NNNN`, `Zed<letters>`, `sentinel-<letters>`); never committed values |
| Langfuse | `build_sink` from `tests/unit/adapters/_tracing_doubles.py`: per-test fake keys, `ProjectsStub(ok())` over `httpx.MockTransport`, `InMemorySpanExporter` |
| HTTP fixtures for AC-3/AC-44 | Hand-written response bodies in the test modules, shaped per models.md §3 and the AEA-17/AEA-18 test fixtures; no recorded secret |

---

## 7. Checks

Run from the worktree with `export UV_LINK_MODE=hardlink`. Cheapest first; stop at the first red.

| # | When | Command | Passing looks like |
|---|---|---|---|
| 1 | Iterating, Part A | `uv run pytest tests/unit/web tests/unit/test_import_direction.py -q` | green; `test_every_register_stub_present` still green |
| 2 | Iterating, Part B | `uv run pytest tests/contract/test_model_ports_contract.py -q` | every case passed, 0 skipped |
| 3 | Iterating, Parts C–G | `uv run pytest tests/graph/test_worked_pairs_api.py tests/integration tests/capture/test_cap1_customer_chat.py tests/capture/test_cap2_safety_first.py tests/capture/test_cap3_handoff.py -q -rs` | green; skips only `INDEX_SKIP` (none on the VPS) |
| 4 | Before the final commit: lint and format | `uv run ruff check src tests && uv run ruff format --check src tests` | no findings |
| 5 | Before the final commit: types | `uv run mypy` | `Success: no issues found` (AEA-52 and AEA-53 report 0 errors on `main`) |
| 6 | Before the final commit: contract boundary, strict (PA-4) | `CONTRACT_STRICT=1 uv run pytest tests/contract -rs` | green; no `route not registered` / `not bound` for a customer-path operation |
| 7 | Before the final commit: **full suite** (this change reaches everything: `web/container.py` is built by every app-level test, build-loop-test-scope "a module imported across the codebase") | `timeout 2400 uv run --with pytest-xdist pytest -n 2 -m "not journey" -q` | green, except the two known reds on `main` listed under this table; any other red stops the commit |
| 8 | Before the final commit: journeys (serial) | `uv run pytest -m journey tests/journeys -q -rs` then `uv run python -m tests.journeys.affected --base main` | green; J-1 (AEA-57) still green with the graph bound; the five AEA-51 journeys pass |
| 9 | Record | `uv run pytest -m journey tests/journeys/j2 tests/journeys/j3 tests/journeys/j4 tests/journeys/j5 tests/journeys/j9 --journey-record=AEA-51` | record written, level `integrated with a scripted model` for every step |
| 10 | Context | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL in an owned row |
| 11 | Diff scope | `git diff --name-only main...HEAD` | only §2.1 paths |

**Known reds on `main` at `b68df7e` (not this ticket's; never fixed or skipped here):**
`tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0` (stale since journeys exist),
`tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_script` (red on `main` before AEA-45, its ledger row), and under
`-n 2` only `tests/unit/adapters/test_tracing_langfuse.py::test_export_never_blocks_hanging_exporter` (timing flake). The
AEA-58 ledger row also saw the contract drives `liveChatAction/unknown_case` fail and `streamCaseEvents/unknown_case` hang;
FIX-W1 (`38d3884`) changed that driver afterwards, so both may now pass. **Expected to turn green with this ticket:**
`tests/journeys/j7/test_aea_30.py::test_j7_shift_end_converts_queued_case` (red because `startChatSession` answers 500
without `reply_composer`); if it stays red, quote its failure line for its owner. Handling: re-run any red alone with
`uv run pytest <nodeid> -q`; if it is listed here and red alone too, run it once on the main checkout (`cd
/home/linuxuser/workspaces/inno-aea-callcenter && uv run pytest <nodeid> -q`, read-only) and quote both results. If check 7
is ended by `timeout`, re-run it with `-v` to find the node that stopped progressing, run that node alone on the main
checkout under `timeout 120`, and re-run check 7 with `--deselect <nodeid>`; name it in the report. Any other red is this
ticket's.

The WP-N worked pairs this ticket owns are WP-1…WP-8 + WP-4F + DANGER + NODANGER (AC-6…AC-16); the single `[journey]`
criterion is AC-32 at level `integrated with a scripted model`. No test calls a paid model; no test is marked `live`.
`-n 2` is the most workers allowed on this machine; journeys and the record run serially (AEA-57's recorder writes only
on the controller).

**Commits** (explicit paths, never `git add -A`; each message ends with `Co-Authored-By: Claude Sonnet 5.5
<noreply@anthropic.com>`; commit only on the ticket branch; never push or force-push, the merge step pushes `main`):
1. `feat(AEA-51): register_graph binds the real graph; cross-adapter port contract` — container + contract test.
1b. (pass 1 only, §5 *Two passes*) `test(AEA-51): integration launcher, login gate, greeting and role guards (pass 1)`.
2. `test(AEA-51): worked pairs through the HTTP API on the real graph` — `tests/integration/customer_support.py`,
   `tests/integration/customer_api.py`, `tests/graph/worked_pair_scenarios.py`, `tests/graph/test_worked_pairs_api.py`.
3. `test(AEA-51): composition, failures, relayed turn, CAP-1…3, journeys J-2…J-5, J-9` — the remaining test files.
4. `docs(AEA-51): journey record and context rows` — the record, area map, ICM row, DO-3 §6.

**What the implementer must NOT do**
- Edit any file outside §2.1, another `register_*` hunk, the module imports of `container.py`, `tests/journeys/support/`,
  `pyproject.toml` / `uv.lock`, the OpenAPI, `apps/web/**`, `docs/ux/**`, issued data, the briefing, `docs/archive/`,
  `docs/parked/`.
- Patch a sibling's behaviour (a seam that does not connect is reported on #51 as `blocked-on AEA-NN`).
- Use `app.dependency_overrides`, `TestClient`, a service double, or `monkeypatch` of any `meridian` module **except**
  the one `meridian.web.container.Limits` replacement of PD-9 (AC-25, J-9 step 3).
- Read `.env`; set app settings through `os.environ` (only `FASTEMBED_CACHE_PATH` and `HF_HUB_OFFLINE` inside
  `fastembed_offline()`); bind any port but `127.0.0.1:0` (never 4019 or 5184); open a non-loopback socket.
- Put a phone number, code, card-like number, key, password or session secret literal in a test file, test name, log,
  print or commit.
- Weaken an expectation to match observed behaviour; turn a blocked step into a pass.
- Write the strings `heldout` or `key_dir` under `tests/journeys/` (AEA-57 AC-13 grep).

---

## 8. Risks and requests

| # | Kind | Item | Request / handling |
|---|---|---|---|
| R-1 | **Shared-primitive request (blocks AC-1, AC-17, AC-18, AC-21, AC-46, AC-47)** | `register_tracing` (AEA-19, merged) already provides `Key("trace")`, and `TurnService` (AEA-40) and `PersonRequestService` (AEA-42) read that key. `register_graph` runs later and the container refuses a second `provide`, so `overrides.trace` cannot reach the turn span from this hunk: AC-17's "one trace per turn with nested spans" would fail | **AEA-19-F1** (small follow-up on AEA-19's hunk, merged before AEA-51): `register_tracing` keeps its sink choice exactly as now but provides `Key[TraceSink]("trace")` through a factory that returns `c.get(Key[TraceSink]("trace_override"))` when that key is provided (`ContainerError` with message `not provided: trace_override` → the existing choice; any other error re-raised). Its own test adds one case. `register_graph` stays the only reader of `overrides` (R-W-8); no consumer key changes; no gap on `main`. **Status at `b68df7e` (re-checked): still not cut.** `register_tracing` (`container.py` lines 294–344) still provides `Key("trace")` itself, and the merged `register_chat` reads it eagerly in the `TurnService` factory (line 804); AEA-42's `register_person_request` reads it too. The need is unchanged. Because every `provide` runs before `container.build()`, the F1 factory sees `trace_override` when it is built |
| R-2 | Collision | `web/container.py` is shared; this hunk is the last large one | Edit only `register_graph`; module imports untouched |
| R-3 | Code size | `container.py` is 1,134 lines at `b68df7e` and grows by ~150 here (AEA-45 adds more); above the 700-line orchestrator cap of `code-structure.md` | Request to the integrator: a later AEA-01 follow-up may move the hunks into per-area wiring modules; not this ticket (the slice plan gives 3+ no `src/` file) |
| R-4 | Sibling names not in DO-4 | §4.3 names come from sibling plans/branches | Step A0 verifies them after merge; any difference stops the build |
| R-5 | Start-up cost | Every app-level test now builds the real graph, the registry and a readiness read | Measured by check 7; if the full suite slows by more than 30 %, report it (no lazy-loading hack here) |
| R-6 | Index build time | The session index build embeds 17 files once per process | `functools.cache`; with `-n 2`, twice. Fine on this machine |
| R-7 | Concurrency routing | AC-43 depends on the marker word surviving into the specialist's request text | Test fails loudly with a named message; reported, not weakened (PD-13) |
| R-8 | AEA-24 interface | AC-49…AC-51 depend on AEA-24's runner accepting the one-case directory and the injected env and freeze file | F2 runs it in-process through `HarnessDeps` (PD-16); on exit 2 or 3, stop and record `blocked-on AEA-24 follow-up` for those three ACs only |
| R-9 | Label | graph-core §2 rule 4 calls the intake test "(AEA-51, `risk::security`)"; the slice plan has no Sec label | Recommendation to the orchestrator: keep the label off. This ticket adds wiring with start-up guards and proves AEA-04/12/19/20's redaction at the entry point; the redaction code itself is in those `risk::security` tickets. If the orchestrator adds the label, AC-17…AC-20, AC-31, AC-47 become frozen tests written first by `test-writer-agent` |
| R-10 | Readiness policy | PA-2 lets the app start on an empty index | Matches data.md (readiness "never raises"); AEA-50's image builds the index, so production never runs empty; recorded as a plan-added criterion for Innocent's visibility in the issue comment |
| R-11 | `Limits` replacement in tests | PD-9 replaces the container's `Limits` factory for a short deadline | The only way to reach `TURN_TIMEOUT` without a 60 s wait; no Settings field or env name added (web.md §15 forbids test seams in Settings) |
| R-12 | Disk | 15 GB free on `/` (84 %) at refresh 5, 2026-10-21 | One worktree, hardlinked venv, temp index removed at exit; check `df -h /home` in A0 |
| R-13 | **Missing prerequisite (new at refresh 2)** | `agent/nodes/compose.py` (AEA-21's file) builds no `SlotCardBlock`, `AccountCardBlock`, `AppointmentBlock`, `WherePromptBlock` or `UrgencyQuestionsBlock`, and no `ErrorBlock SLOT_TAKEN` with fresh windows. AEA-21's plan §8.2 R-2 asked for an "AEA-21b compose cards" follow-up before AEA-51 (its blocker, AEA-13's fee note, merged as `dc1f4da`); it was never cut and no open branch builds the blocks. Without them the customer cannot pick a window or see account facts | **Request to the orchestrator: cut AEA-21b** (owner: AEA-21's area, `agent/nodes/compose.py` and its tests) and merge it before this ticket. Blocks AC-7, AC-8, AC-10, AC-12 (`no` branch), AC-14, AC-25(e), AC-26, AC-27 (Monday follow-up), AC-36, AC-37, AC-38, AC-43 and J-2 step 2, J-3. This ticket never builds a block. **Status at `b68df7e` (re-checked): still not cut;** `grep -c` of the five constructors in `compose.py` is 0 |
| R-14 | **Missing prerequisite (the ticket's own clause), now a follow-up** | AEA-40 merged (`f466ff7`) with `TurnService._run` checking `self._spend.allow_turn()` (`services/turn.py` line 318) before `parse_intake` (line 322). So at our cap a CO-alarm message gets `SPEND_CAP_REACHED`, not the WP-5 instruction. DO-4 §14 step 2 and stage7 web.md give that order; DO-4 §11's failure table says "safety and CON-4 still work". The ticket's *Agent handoff* settles which wins here: AC-24's safety half is `blocked-on AEA-40` | **Request to the orchestrator: cut AEA-40-F1** (owner: AEA-40's `services/turn.py` and its tests). Its outcome: at our cap, a message the deterministic safety gate catches (CO alarm, gas, smoke words; R-6) still gets the WP-5 instruction and its P0 case, with no model call; every other message keeps `SPEND_CAP_REACHED`. The mechanism is F1's planner's to choose. AEA-51 builds AC-24's notice and CON-4 halves now, and keeps the safety half in `test_spend_cap_safety_still_answered`, skipped as `blocked-on AEA-40-F1` until F1 lands (§5 F3). If the orchestrator reads F1 as changing the signed DO-4 §14 order rather than resolving a contradiction the ticket already ruled on, it goes to Innocent as a decision; this plan changes nothing in either case |
| R-15 | Typing follow-up, not a blocker | `agent/context.py` (AEA-21's file) types seven `GraphDeps` fields as `TypeAlias = Any`; AEA-21's R-3 offers the swap to "AEA-51 or a follow-up". That file is not in this ticket's owned list | Not done here. mypy passes either way, and AC-1 asserts the real classes at run time. Request a one-line-per-type follow-up on AEA-21's file after AEA-29, 30 and 35 merge |
| R-16 | Upstream | AEA-35 merged (`1ce98c4`) after Innocent's AEA-35b home ruling. AEA-39 (act node) is `blocked` in the ledger only because it ran before AEA-35 landed (`scope_for` missing); its re-run is pending, and no branch exists | Pass 2 waits for AEA-39 (§9). Nothing here depends on how AEA-39 is built beyond its graph-tools/graph-nodes node contracts |
| R-17 | Seam finding carried in | AEA-38's `reply.checks` calls `attach_extraction` without `customer_messages`, so the assembler's own quote check is off; `check_quotes` runs first | PA-5 proves the end result on the real path. Red → `blocked-on AEA-38 follow-up`, reported on #51, never patched here |
| R-18 | Pre-existing reds | Two tests on `main` are red or flaky for reasons outside this ticket (§7 check 7) | Named in check 7; quoted in the report; not fixed or skipped |
| R-19 | Request received from AEA-52 | AEA-52's plan §8 R-3 asks for the WP-7 and WP-4 conversations as importable functions in a proposed `tests/integration/customer_scripts.py` returning AEA-52's `Actor` | Met differently: a new file outside §2.1, typed by AEA-52's helpers, would make AEA-51 import AEA-52's test helpers. The published drivers are `tests/graph/worked_pair_scenarios.py::wp7(run, client=None) -> ScenarioResult` and `::wp4(...)`, with `ScenarioResult.case_refs` (D2), on `tests.integration.customer_support.open_customer_run(request, RunOptions(...))`; AEA-52 builds its `Actor` from `result.thread_id` and `result.case_refs[-1]`. Keep those names and signatures stable; say so in the issue comment on #51 and #52 |
| R-20 | Context defect (not ours) | `.claude/reference/area-map.md` holds the A7a row twice (lines 35 and 37) and the A8 row twice (39 and 41) at `b68df7e`, from append-style merges | H3 edits both copies so neither is stale; request a `lane::direct` clean-up from the orchestrator |
| R-21 | Recommendation to the orchestrator | Pass 1 binds `reply_composer`, so CON-1 answers 201 instead of 500 on the real app; `j7/test_aea_30.py` (red on `main`), AEA-52 pass 2's CON-1 legs and J-1's CON-1 step wait on that | Merge pass 1 as soon as its checks are green and keep #51 open for pass 2. The orchestrator's call; the plan works either way |

Design decisions taken here (engineering; recorded so the reviewer can check them): **PD-1** reuse `Key("ledger")` and
`Key("trace")`; **PD-2** = R-1; **PD-3** = PA-1; **PD-4** = PA-2; **PD-5** one adapter per (provider, model) through
AEA-17's client key and AEA-18's factory key; **PD-6** `register_gateway` stays empty (AEA-20 R-3); **PD-7** AEA-51's
launcher composes AEA-57's public pieces because the `journey` fixture's environment has an empty index, no eval key and
no trace override (journeys still record into AEA-57's collector through `JourneyRun.step`); **PD-8** per-step script
tables instead of one queue (parallel nodes and concurrent turns make queue order unknowable); **PD-9** short deadline by
replacing the container's `Limits` factory; **PD-10** spend at cap seeded through the real `LedgerService.record`;
**PD-11** AC-3's shared rows (§5 B1); **PD-12** AC-23 claims through CON-13 (`applyCaseAction`, AEA-45) because the
claim is a precondition of the join and the domain has no `CaseAction` type to call `CaseService.apply` with;
**PD-13** AC-43 marker routing (18 window turns, 2 booking racers); **PD-14** the forced 5xx of AC-42 is AC-48's held
write lock; **PD-15** `register_graph` returns early when the app has no web shell (A2 step 0), as the sibling hunks it
reads from do; **PD-16** AC-49…AC-51 run AEA-24's runner in-process through `HarnessDeps` with a temporary freeze file (F2); **PD-17** PA-5's sentinel brief quote rides on AC-13's WP-7 run instead of a separate test.

---

## 9. Readiness

**READY** as a plan (no product decision is needed: D-14 settles CAS-16, GRC-3 and DAT-1 on option A; every other choice
above is engineering and made). **Pass 1 is buildable now; pass 2 is BLOCKED-ON** the rows below (status at `b68df7e`):

| Prerequisite | Status | Why this ticket needs its result (not only its signature) | Waiting |
|---|---|---|---|
| **AEA-39** act node | ledger `blocked`, re-run pending (AEA-35 has merged); no branch | `run_specialist`, `escalation` and `handoff` raise `NotImplementedError`; every turn that runs a specialist, escalates, or hands off (including the chat-words person request: `route_after_gates` → `handoff`) reaches them | every pass-2 criterion that drives a CON-2 turn |
| **AEA-21b** compose cards | follow-up, not cut (§8 R-13) | slot, account and appointment blocks; `SLOT_TAKEN` with fresh windows | AC-7, AC-8, AC-10, AC-12, AC-14, AC-25, AC-26, AC-27, AC-36, AC-37, AC-38, AC-43, J-2, J-3 |
| **AEA-19-F1** trace override | follow-up, not cut (§8 R-1) | `overrides.trace` reaching `Key("trace")` | AC-1 (trace identities), AC-17, AC-18, AC-21, AC-46, AC-47, AC-49 |
| **AEA-40-F1** safety at our cap | follow-up, not cut (§8 R-14) | a safety message at our cap gets the instruction | AC-24's safety half only (`test_spend_cap_safety_still_answered`, skipped until it lands) |

Already on `main`: every other ticket in the issue's *Blocked by* (AEA-02, 11, 12, 17, 18, 19, 20, 22, 23, 24, 26, 27, 28,
29, 30, 33, 34, 35, 36, 37, 38, 40, 42, 43, 44, 46, 57, 59), plus AEA-35b, 45, 52 (pass 1), 53 and 58.

**Startable now (pass 1, §5 *Two passes*):** Part A (its imports are all on `main`; the act stubs run only when a turn
reaches them), Part B (AC-3), Part C, and `test_login_gate` (AC-4), `test_greeting_and_demo_date` (AC-5),
`test_role_maps_bound_and_guarded` parts (a)–(b) (AC-2) and `test_real_objects_bound` part (b) plus the structural part (a)
(AC-1, PA-1…PA-3). Pass 1 binds everything except `Key("run_graph")`. The orchestrator may merge pass 1 early (R-21).

**Gates:** none human; no paid call; the wave-3 merge runs `seam-audit-agent` across AEA-50…53 with all journeys
(integrated-journeys §5).
