# Plan — [AEA-37] graph: plan node (planner, danger classifier, join)

**Status:** planned — **READY, no blocker** (AEA-21 merged to `main` at `5531664`; §9)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/37 · **Base revision:** `dd1b110`
(main when refreshed: AEA-21 graph spine `5531664`, AEA-02b `5305d57`, AEA-57 journey harness `bd79a29`, AEA-17
`0a85270`, AEA-18 Jev adapter `900a1d8`, AEA-28 scheduling `2c2e8c5`, AEA-27 identity `13adc86`, and every earlier merge
in `.claude/state/build-ledger.md`. First planned against `16ca639`; refreshed against `775f591` + AEA-21's branch
`0a5b703`, then `0a85270`, `a81f59d`, and again here.)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (refreshed four times the same day) · **Implementer:** fanout-implementer on Sonnet ·
**Lane:** build-loop · **Risk:** none (no `risk::security`: no test-writer, no security review; AC-8 still proves the
JEV redaction) · **Wave:** 2 · **Gates:** none
**Slug / branch:** `graph-plan-node` → branch `aea-37-graph-plan-node`, worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-37` (the orchestrator creates it from `main`)

### Refresh 4 — 2026-10-21, against `main` `dd1b110` (read this first)

- **What changed on `main` since `a81f59d`:** AEA-18 (`adapters/models/openrouter_jev.py`, `register_jev`), AEA-28
  (`services/scheduling.py`, `repos_booking.py`, `agent/tools/scheduling.py`, `register_scheduling`), AEA-27
  (`services/identity.py`, `repos_identity.py`, `agent/tools/account.py`, `register_identity`), their tests, and the
  context docs. `git diff --stat a81f59d..dd1b110` touches **none** of the surfaces this plan names in §4, §6 or §7.1:
  no file under `src/meridian/{domain,ports,policy,privacy,gates}/`, `src/meridian/agent/{gateway,context,signals,graph,
  routers}.py`, `src/meridian/agent/nodes/`, `tests/graph/`, `tests/fakes/`, `tests/unit/agent/_gateway_doubles.py` or
  `tests/journeys/support/` changed. Every name in §4 and §6 still holds.
- **AEA-18's adapter fits PD-4.** `JevAdapter` sends `{"instructions": req.system, **req.state}` (it skips a state key
  named `instructions`) and one `{"type": "choice", "instructions", "criteria"}` entry per field; an answer outside a
  field's options comes back as a failure. This plan's state keys (`latest_message`, `recent_chat`, `flags`) never
  collide with `instructions`, and PA-4 (invalid answer → failure) matches the adapter.
- **R-1 is still open:** `tests/graph/test_spine.py` lines 104–133 still list `(plan, "planner")`,
  `(plan, "danger_classifier")` and `(plan, "plan_join")`. §7.2 handling is unchanged.
- **Merge by the tree, not one ticket at a time** (Innocent, relayed with this run). AEA-37 is a wave-2 node ticket with
  the same parent (AEA-21) as AEA-34, AEA-36, AEA-38 and AEA-39, and all five turn R-1's cases red. Applying R-1 once,
  when that group merges, serves all five. The implementer still commits on its own branch and never merges.
- **Context docs moved, the anchors did not.** In `docs/design/code-design.md` §3 the last `**Built:**` line is now the
  AEA-28 one (`services/scheduling.py`, …); the `nodes/plan.py` tree line (line 291) still ends `stub AEA-21 6df4f4c`
  and the `prompts/routing.py` tree line (line 298) has no marker. Area-map A7d Status is still `planned`. In
  `icm-progress.md` the last *Routes verified against code and tests* row is now AEA-27's. Step 12 already says "after
  the last existing one", so it is unchanged.
- **G-8 re-run on `dd1b110`:** still exactly `tests/graph/_spine_doubles.py`, `tests/graph/test_spine.py`,
  `tests/unit/agent/test_routers.py`.
- **The worktree already holds an earlier, uncommitted run of this plan.** `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-37`
  (branch `aea-37-graph-plan-node`, no commits of its own, based on `7d37888`, three merges behind `main`) has
  `src/meridian/agent/nodes/plan.py` modified (473 lines, every function of §4.7 present),
  `src/meridian/agent/prompts/routing.py` (147 lines), `tests/unit/agent/nodes/plan_fixtures.py` (233 lines) and an
  empty `tests/unit/agent/prompts/__init__.py`; no test file yet. **Keep that work** (new §5 step 0): bring the branch
  up to `main`, then check each file against §4–§6 and continue from step 3's tests instead of rewriting.
- AEA-34, AEA-36, AEA-38, AEA-39, AEA-29 and AEA-40 are still on branches, not on `main`; the J-5 journey steps stay
  blocked (§7.1), which is allowed.

### Refresh 3 — 2026-10-21, against `main` `a81f59d`

- `git diff --stat 0a85270..a81f59d` touches only `docs/plans/fanout/2026-10-21-build/AEA-29.md`: no source, test,
  schema, contract or addendum changed, so every Refresh 2 finding below still holds.
- Re-checked on `a81f59d` with an import-and-inspect script: the `PlannerChoices`, `Plan`, `DangerAssessment`,
  `StateFlags` and `PlannerTrace` field lists; the three `*Update` key sets; the `SignalName` values; `Role`,
  `HandoffReason.LATE_TECHNICIAN` / `UNSUPPORTED_ACTION`, `HaltReason.BRAKE_TASKS`; `ModelGateway.choose`; the
  `GraphDeps` fields; `Brakes().tasks_per_turn == 3`, `ContextLimits` 6 / 400; `emit_signal`;
  `CheckEvent.from_danger` / `from_halt`; `_spine_doubles` (`make_deps`, `make_ctx`, `make_input`, `install_doubles`);
  `build_gateway`; `FakeChoiceModel`; the harness's `JourneyRun.step` / `login`, `JourneyScript.add` / `remaining` /
  `problems`, `DbReader.rows` / `one` / `count`, `JourneyClient.call`. **All match.**
- R-1 is still open: `tests/graph/test_spine.py` lines 111–113 still list the three `plan` stubs. The `nodes/plan.py`
  tree line in `docs/design/code-design.md` §3 still ends `stub AEA-21 6df4f4c`; the last `**Built:**` line is still
  the AEA-06 one; the area-map A7d Status cell still reads `planned`. AEA-34 and AEA-36 are on branches, not on `main`.

### Refresh 2 — 2026-10-21, against `main` `0a85270` (the orchestrator re-checks only these)

- **AEA-21 is merged** (`5531664`), so the plan has no blocker. This planner re-read every name in §4.1–§4.4 and §6 on
  `main` with an import-and-inspect script: the domain types and their field sets, the `PlannerUpdate` / `DangerUpdate` /
  `PlanJoinUpdate` keys, `CheckEvent.from_danger` / `from_halt`, the `SignalName` values, the `GraphDeps` fields,
  `emit_signal`, `ModelGateway.choose`, `ModelOutcome`, `CallRecord.from_provider`, `Brakes`, `ContextLimits`, `redact`,
  `FakeChoiceModel(script, *, model=None)` with `.requests`, `build_gateway(**adapters) -> (ModelGateway, Doubles)`, and
  `_spine_doubles`' `make_deps(sink, uow=None)`, `make_ctx(turn_id, *, intake=None)`,
  `make_input(turn_id, text_store="Yes, please.")`, `no_rules()`, `install_doubles(monkeypatch, visits, **overrides)`,
  plus the routers. **All match.** For exact imports: `HandoffReason`, `Role` and `CallRecord` live in
  `meridian.domain.common` (`meridian.ports.models` re-exports `Role`). `IdentityState.status` values are
  `not_checked`, `located`, `code_sent`, `verified`, `not_verified`, `locked`.
- **AEA-57's journey harness is merged** (`bd79a29`). Its rules (`tests/journeys/support/README.md`) forbid
  monkeypatching `meridian` and forbid doubles above the model ports in `tests/journeys/**`. The first version's J-5
  file used `install_doubles`, so it would break those rules. AC-11 is now built in two parts:
  - **(a)** the same mock-level graph run, moved to a new owned unit file `tests/unit/agent/nodes/test_plan_graph.py`;
  - **(b)** `tests/journeys/j5/test_aea_37.py` on the harness: the `journey` fixture, raw scripted model output, API
    level. Its steps report *blocked* (skipped, never passed) until AEA-40, AEA-51 and AEA-29 bind `turn_service`,
    `run_graph` and `handoff_service`. This is the same shape as AEA-36's `test_aea_36.py` (§7.1).
- **R-1 is still open on `main`.** `tests/graph/test_spine.py::test_stubs_raise_loudly` (lines 104–133) still lists
  `(plan, "planner")`, `(plan, "danger_classifier")` and `(plan, "plan_join")`. The §7.2 handling is unchanged: commit,
  report the three cases, and the orchestrator applies R-1 before the merge.
- `tests/unit/agent/nodes/__init__.py` and `tests/journeys/j5/__init__.py` now exist on `main`; do not touch them.
  `tests/unit/agent/prompts/` does not exist yet, so create its empty `__init__.py`.
- `docs/design/code-design.md` §3: the `nodes/plan.py` tree line now ends `stub AEA-21 6df4f4c`. Step 12 replaces that
  token with `built AEA-37 <sha>`. The last `**Built:**` line is currently the AEA-06 one.
- `ConversationState` still has no `pending_change` key, so R-5 stands. No sign-off decision (D-4…D-15) bears on this
  ticket.
- Kept from Refresh 1: `ModelOutcome` is imported under `TYPE_CHECKING` only (§4.0, §4.4); PA-8 (JEV leaves the wording
  unchanged; 0 of 35 strings change); the AC-12 own-row pattern; PD-8 and PD-9.

---

## 1. Goal and sources

### 1.1 Goal (the issue's *What to build*, `docs/plans/tickets/AEA-37.md`)

> **US-5:** "As a **homeowner** with no cooling on a hot day, I need to book a visit like any repair, with a couple of
> skippable urgency questions, and to be given the emergency number first if I say someone is in danger, so that I'm
> neither frightened needlessly nor left waiting when it matters."

`agent/nodes/plan.py` replaces AEA-21's three stubs with `planner`, `danger_classifier` and `plan_join`, plus the pure
`join_plan`; `agent/prompts/routing.py` holds the planner and classifier wording and choice fields.

**What it does, concretely (the three worked pairs this plan's tests reproduce):**

| Input (latest customer message on a `FREE_TEXT` turn) | Planner (Jev) | Classifier (Jev) | Result in state |
|---|---|---|---|
| WP-3 "I need to schedule a service call. My AC isn't cooling." | `scheduling="book_new"`, `topic="booking"` | `normal` | `danger.raised=False`, one `classifier`/`pass` event; `plan = Plan(mode="act", tasks=(PlannedTask(order=1, specialist="scheduling", intent=BOOK_NEW, needs_identity=True),), handoff_request=None, topic="booking", source="planner")` |
| DANGER "my mother is 88 and it's 95 degrees in here" | anything | `danger` | `danger.raised=True`, one `classifier`/`raised` event (`codes=("danger",)`); AEA-21's router reads `danger.raised` first and sends the turn to `safety` |
| NODANGER "my AC isn't cooling" | `book_new` | `normal` | `raised=False`, `classifier`/`pass`; a normal booking plan |
| WP-1 turn 1 "What does the Comfort Club membership actually include?" | `knowledge="yes"`, `topic="membership"` | `normal` | `Plan(mode="act", tasks=(knowledge answer_question,), topic="membership", source="planner")` |
| WP-4F turn 4 "Yes, please." with no open task | all `none`/`no` | `normal` | `Plan(mode="talk", tasks=(), handoff_request=None, topic=<planner's>, source="planner")` |
| Any text; Jev fails twice, Sonnet fallback fails; no policy word, no open task | failure | — | `Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)`; one `planner_fallback` signal with `recovered=False`; AEA-21 routes it to `escalation` |

**How it works, in one paragraph.** The gate (AEA-36) has already decided the turn is `FREE_TEXT`. LangGraph runs
`planner` and `danger_classifier` in one superstep (DO-3 §2.2). The planner builds `PlannerInput` (JEV-redacted latest
message, at most 6 JEV-redacted recent chat lines of at most 400 characters, and `StateFlags`), asks five choice
questions through `deps.gateway.choose(Role.PLANNER, …)`, and on a gateway **failure** asks the same request once
through `Role.PLANNER_FALLBACK`; a gateway **halt** is written to `halt` and never falls back. The classifier asks one
`danger_level` question about the latest message only; its label may only raise the rules' verdict; on failure the
rules stand. `plan_join` turns the planner's choices, the gate's policy word and the open task into an ordered `Plan`
with code (SP-1's measured `normalize` steps) and fires the task brake when a plan would exceed
`limits.brakes.tasks_per_turn`.

### 1.2 Context

Wave 2 of the Stage 8 build. AEA-21 (merged, `5531664`) landed the graph spine, `GraphDeps`, `emit_signal`,
`timed_node` and a `plan.py` stub whose three functions raise `NotImplementedError`. This ticket replaces that stub in
place. The model gateway (AEA-20, on `main`: `ModelGateway`, `ModelOutcome` in `agent/gateway.py`) is reached only
through `GraphDeps.gateway`. The unit tests use a scripted gateway double that returns real `ModelOutcome[ChoiceAnswer]`
values. The turn-2+ prompt test (AC-9) and the mock-level graph run (AC-11 part a) go through a **real** `ModelGateway`
with AEA-11's recording `FakeChoiceModel` at the model port. AEA-57's harness (merged, `bd79a29`) runs the real app with
a scripted model. This ticket's J-5 steps (AC-11 part b) run on it and report *blocked* until AEA-40, AEA-51 and AEA-29
bind their services. Until then the journey evidence is `mock-tested`.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-37.md` | AC-1…AC-12, the worked pairs, the owned files, the "must not edit" list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-37 (blocked by 11, 12, 21; owns `nodes/plan.py`, `prompts/routing.py`), §0a (J-5), §3 collision map (`agent/nodes/*.py` stubs replaced in place; `agent/prompts/*.py` one file per ticket; context files: own row only) | Owned files; journey file name; context rows |
| Requirements | PRD R-8 (danger), R-45 (planner sees "the recent clean chat plus a state summary"), R-47 (rules first; raise-only classifier; on failure the rules stand); HP-2 (C); WP-1, WP-3, WP-4F, WP-7, WP-8 (`docs/data/worked-pairs.md`) | Raise-only; rules stand on failure; worked-pair inputs |
| Code design (DO-3) | `docs/design/code-design.md` §2.1 (agent → ports, core; never adapters), §2.2 (parallel superstep), §4.5, §5.3 (writer table), §5.4 (skeleton), §7 rows R-8, R-47, §10 C-1, C-2 | Layers; one writer per key; classifier failure → rules stand |
| Component contracts (DO-4) | `docs/design/contracts/internal-components.md` §0 (Sonnet `confidence` is `None`, never invented), §3 (`StateFlags`, `PlannerInput`, "What crosses this line: only `PlannerInput`"), §4 (`PlannerChoices`, `PlannerOutcome`, `DangerAssessment`, `TaskIntent`, `PlannedTask`, `Plan`, `join_plan` rules), §7 (`HandoffReason`), §11 (`ProviderFailure`, `Halt`, *OpenRouter error inside HTTP 200* row), §12 (`Role`, `ChoiceField`, `ChoiceRequest`, `ChoiceAnswer`, `ModelOutcome`, `ModelGateway.choose`), §16 (addenda win) | Exact shapes below |
| Addenda (win over DO-4) | `stage7/graph-nodes.md` §1 (`CheckEvent.from_danger`, `from_halt`), §4 (`SignalName`, `SignalRecord`, `emit_signal`; rows `classifier_fallback`, `planner_fallback`, `brake_fired`), §5 (`Plan.planner_failed`, GRN-7), §7 (CAP-2 DANGER: only the two Jev routing spans), §9.1 (`PlannerUpdate`, `DangerUpdate`, `PlanJoinUpdate`), §9.4 (node signatures); `stage7/graph-core.md` §2 (`TurnContext`, `PlannerTrace`), §4 (`GraphDeps`, `timed_node`), §5 (`BRAKE_HALTS`, `halt_route`), §7 (`ContextLimits.planner_lines` 6, `planner_line_chars` 400), §9 (state key `planner`), §11 (`check_events`, router edge 1), closing table *cases A-6* (`late_technician`); `stage7/data.md` §1 (`redact`, `RedactionProfile.JEV`, tokens `[name]`, `[phone]`, `[customer id]`, `[invoice id]`, `[code]`, `[card number removed]`, `[email]`, `[address]`); `stage7/models.md` §5 (gateway rules; halt never a fallback reason), cross-topic 4; `stage7/cases.md` §3.4 (rule 4 `late_technician`, `unsupported_action`; rule 6 `AI.planner_failed`) | Every signature and builder used |
| Decision ledgers | `docs/plans/7b-decisions/graph-nodes.md` GRN-2, 4, 5, 7, 9, 11; `graph-core.md` GRC-9, 11, 16, 18; `data.md` DAT-1; `docs/plans/stage7-signoff.md` D-14 (DAT-1 = option A: introduction patterns) | Already folded into the addenda |
| SP-1 measured wording | `docs/plans/fanout/2026-10-20-sp1/build.md` step 7 (`PLANNER_SYSTEM`, `PLANNER_FIELDS`, `CLASSIFIER_SYSTEM`, `CLASSIFIER_FIELDS`, `normalize` steps 1–5) and the `gates.is_affirmative` / `mentions_slot_pick` patterns (lines 505–506) | Copied verbatim in §4.5 and §4.6 |
| Sibling code (read only, binding names) | On `main`: `src/meridian/domain/{common,turn,state,actions,identity}.py`, `ports/models.py` (AEA-02); `agent/gateway.py` (AEA-20: `ModelGateway.choose`, `ModelOutcome`, `_redact_choice`); `privacy/redact.py` (AEA-04); `policy/limits.py` (AEA-01); `gates/gate.py` (AEA-12: `decide_gate`, read to confirm what reaches these nodes); `tests/fakes/models.py` (AEA-11: `FakeChoiceModel`, `provider_call`); `tests/unit/agent/_gateway_doubles.py` (AEA-20: `build_gateway`, `Doubles`). On `main` from AEA-21 (`5531664`): `agent/{context,signals,graph,routers}.py`, `agent/nodes/{plan,compose}.py`, `tests/graph/_spine_doubles.py`, `tests/graph/test_spine.py`; from AEA-57 (`bd79a29`): `tests/journeys/support/{README.md,run.py,steps.py,scripted_model.py}`, `tests/journeys/j1/test_aea_57.py`; schema `adapters/sqlite/schema/{00_core,60_cases}.sql` (`turns`, `check_events`, `cases` columns). Sibling plans: `AEA-21.md` §6 (the helper names are a contract with this ticket), `AEA-36.md` §7.6 (its J-5 file on the harness: the pattern copied here; PA-4 `rule_id` `R47.classifier_danger`), `AEA-36.md` (its burning plan uses `needs_identity=True` for `BOOK_NEW`, the same as this join), `AEA-34.md` R-3 (answered by PD-9) | Exact import paths; every name in §4 and §6 was read from this code |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` E-5 (danger recall 100 % on synthetic danger cases, false alarms ≤ 10 %), E-1 (trajectory WP-1…WP-8), E-3/E-4 (escalation recall depends on `handoff_request`) | Scored at Stage 9; kept passing at AEA-51; this ticket supplies the unit-level behaviour only |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-1 (emitters "planner, danger classifier"); *Records* `check_event`, `turn`; *Content and redaction* | One `classifier` event per run; codes only in events and signals |
| Key metrics (DO-7) | M-16, M-17 (from `classifier` events), M-3, M-4 (`PlannerTrace.topic`), M-19, M-20 (`handoff_request`), M-23, M-24, M-25, M-26 | Kept computable; no target set |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3 rule 4 (prompt ↔ consumer), §4 (record), `context-maintenance.md`; workspace `context-management-multi-turn` rules 1, 3, 4, 5; `code-design-solid-modularity`; `agent-architecture` rules 1, 3, 12, 13; `async-safety` rule 1; `pydantic-data-modeling` §1, §2 | See §5 and §7 |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files the implementer may create or edit)

| File | Create / modify | What |
|---|---|---|
| `src/meridian/agent/nodes/plan.py` | **replace** AEA-21's stub in place (same three function names and signatures) | `planner`, `danger_classifier`, `plan_join`, `join_plan`, `build_planner_input`, `rules_verdict`, `raise_only`, `TaskBrakeExceeded` (§4.7) |
| `src/meridian/agent/prompts/routing.py` | create | `PLANNER_SYSTEM`, `PLANNER_FIELDS`, `CLASSIFIER_SYSTEM`, `CLASSIFIER_FIELDS`, `DANGER_FIELD`, `planner_request`, `classifier_request` (§4.6) |
| `tests/unit/agent/nodes/test_plan_graph.py` | create | AC-11 part (a): the mock-level graph run (§7.1) |
| `tests/unit/agent/nodes/plan_fixtures.py` | create | gateway double, builders, constants shared by this ticket's tests (§6) |
| `tests/unit/agent/nodes/test_plan.py` | create | node tests (§7.1) |
| `tests/unit/agent/nodes/test_join_plan.py` | create | `join_plan` rows (§7.1) |
| `tests/unit/agent/prompts/__init__.py` | create **only if absent**, 0 bytes | package marker (AEA-35/38 may add the same empty file) |
| `tests/unit/agent/prompts/test_routing_prompts.py` | create | AC-8 and prompt ↔ consumer checks (§7.1) |
| `tests/unit/agent/prompts/test_routing_prompt_turns.py` | create | AC-9 (§7.1) |
| `tests/journeys/j5/test_aea_37.py` | create | AC-11 part (b): two J-5 steps on AEA-57's harness (§7.1) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-37.md` | create (run date) | AC-11 journey record (§7.4) |
| `.claude/reference/area-map.md` | edit the **A7d row's Status cell only** | AC-12 |
| `.claude/state/icm-progress.md` | **add one new** *Routes verified against code and tests* row (this ticket's own row); never edit another ticket's row or the *Last reconciled* line | AC-12 |
| `docs/design/code-design.md` | under `## 3. The module map` only: **add one new** `**Built:**` line after the last existing one, on the `nodes/plan.py` tree line replace the trailing `stub AEA-21 6df4f4c` with `built AEA-37 <sha>`, and append `   built AEA-37 <sha>` to the `prompts/routing.py` tree line (step 12) | AC-12 |

### 2.2 Shared surfaces read, never edited

`pyproject.toml`, `uv.lock`, `tests/conftest.py`, every existing `__init__.py`, `src/meridian/domain/*` and
`src/meridian/ports/*` (AEA-02), `src/meridian/policy/limits.py` (AEA-01), `src/meridian/privacy/redact.py` (AEA-04),
`src/meridian/agent/gateway.py` (AEA-20), `src/meridian/agent/{context,signals,graph,routers}.py` and
`src/meridian/agent/nodes/compose.py` (AEA-21), `src/meridian/gates/*` (AEA-05, AEA-12), `tests/graph/*` (AEA-21, incl.
`_spine_doubles.py`), `tests/unit/agent/_gateway_doubles.py` (AEA-20), `tests/unit/agent/nodes/compose_fixtures.py`
(AEA-21), `tests/fakes/*` (AEA-11), `tests/unit/test_import_direction.py`, `tests/journeys/affected.py`,
`tests/journeys/support/**` and every `tests/journeys/j*/__init__.py` (AEA-57), `tests/unit/agent/nodes/__init__.py` (exists),
`tests/journeys/README.md`, the OpenAPI file, `UI_CONTRACTS.md`, `docs/ux/**`, `apps/web/**`,
`docs/design/contracts/**`, the briefing, issued data, `docs/archive/**`, `docs/parked/**`.

### 2.3 Owned by other tickets — do not create or edit

`routers.py`, `graph.py`, `context.py`, `signals.py`, `compose.py` (AEA-21); `nodes/front.py` (AEA-36),
`nodes/load_context.py` (AEA-34), `nodes/act.py` (AEA-39), `nodes/reply.py` (AEA-38); `gates/*` (AEA-05, 12);
`agent/gateway.py`, `ModelOutcome` (AEA-20); every `domain/*` type (AEA-02); `decide_escalation` (AEA-14); the J-5
harness and `tests/journeys/support/` (AEA-57); `tests/graph/test_spine.py` (AEA-21 — see R-1); `tests/journeys/j5/test_aea_36.py` (AEA-36) and AEA-51's own J-5 file.

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's, verbatim intent) → implementation → verification

| AC | Requirement | Implemented by | Verified by (test or command) → what passing shows |
|---|---|---|---|
| AC-1 [invariant] | Raise-only: `danger.raised` is true only when the label is above the rules' verdict; `normal` never lowers anything (R-47) | `rules_verdict`, `raise_only`, `danger_classifier` (§4.7 B) | `tests/unit/agent/nodes/test_plan.py::test_classifier_raise_only` → 9 parametrised label × verdict rows pass; DANGER node run `raised=True`, NODANGER `raised=False` |
| AC-2 [failure/refusal] | Classifier failure (`body_error`, then `timeout`) → `DangerAssessment(label="normal", raised=False, failure=…)`, one `classifier` event `fallback`, `codes=("fallback", "<kind>")`, one `classifier_fallback` signal with that `cause`; turn continues; `plan` still written | `danger_classifier` failure branch; `plan_join` ignores `danger` | `test_plan.py::test_classifier_failure_rules_stand` (parametrised over `BODY_ERROR`, `TIMEOUT`) → fields as stated; no exception; `plan_join` then writes `plan` |
| AC-3 [failure/refusal] | Jev failure → exactly one `Role.PLANNER_FALLBACK` call, same fields; `fallback_used=True`, `model` = fallback's; one `planner_fallback` signal `recovered=True`. Gateway **halt** (`PROVIDER_SPEND_CAP`) → no fallback call, `halt` returned | `planner` (§4.7 A) | `test_plan.py::test_planner_fallback_sdq6` → call roles `[PLANNER, PLANNER_FALLBACK]`, identical `ChoiceRequest`; `::test_planner_halt_never_falls_back` → one `PLANNER` call, update keys `{"halt"}` |
| AC-4 [failure/refusal] | Both planners fail (GRN-7): no policy word / open task → `Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)`, signal `recovered=False`; with an open scheduling task and "Yes, please." → that task continued (`source="open_task"`, `planner_failed=False`) | `planner` + `join_plan` steps 1, 8, 11 | `test_plan.py::test_both_planners_fail_planner_failed_plan`, `::test_both_planners_fail_open_task_continues` → plan fields as stated |
| AC-5 [invariant] | `join_plan` normalize rows (WP-7, WP-8, `late_technician`, reschedule + appointments, "Yes, please." with / without open task, order, topic) | `join_plan` (§4.7 C) | `tests/unit/agent/nodes/test_join_plan.py` (one test per row, names in §7.1) → all pass |
| AC-6 [failure/refusal] | Task brake: more than `limits.brakes.tasks_per_turn` tasks → `Halt(reason=BRAKE_TASKS, node="plan_join")`, one `brake` event `codes=("brake_tasks", "plan_join")`, one `brake_fired` signal | `join_plan` step 9 raises `TaskBrakeExceeded`; `plan_join` catches it (§4.7 D) | `test_plan.py::test_task_brake_halts_with_event` (limit lowered to 2, see R-4) → halt, event, signal as stated; no `plan` key |
| AC-7 [invariant] | Key ownership: each node returns only its `TypedDict`'s keys; the two parallel branches never write the same non-reducer key; mypy strict passes | return types `PlannerUpdate`, `DangerUpdate`, `PlanJoinUpdate` | `test_plan.py::test_plan_nodes_write_only_own_keys` + G-3 (`uv run mypy …`) → key sets ⊆ TypedDict keys; overlap only `halt`, `check_events`; "Success: no issues found" |
| AC-8 [negative] | What crosses the line (DO-4 §3): planner request = JEV-redacted latest message + recent chat + `StateFlags` only; classifier = latest message only; no customer ID, invoice ID, phone, introduced name, code, card-like number, passage or tool output; no event or signal holds message text | `build_planner_input` (JEV), `planner_request`, `classifier_request`; codes-only events and signals | `tests/unit/agent/prompts/test_routing_prompts.py::test_requests_cross_only_planner_input` → seeded values absent from both requests, events and `meridian.signal` capture; `[name]`, `[phone]`, `[customer id]`, `[invoice id]` present |
| AC-9 [invariant] | Turn-2+ full prompt: turns 1, 2, 5 of WP-3; system text and every field identical and complete; `recent_chat` ≤ 6 × 400, oldest dropped first; same phone → same `[phone]` on turns 1 and 5 | `build_planner_input`, `planner_request`; driven through the real `ModelGateway` with AEA-11's recording `FakeChoiceModel` | `tests/unit/agent/prompts/test_routing_prompt_turns.py::test_stable_prefix_turns_1_2_5` → three requests captured at the model port, equal hashes, window within cap |
| AC-10 [capture] | `PlannerOutcome` carries `model`, Jev `probabilities`, `fallback_used`, `failure`; `DangerAssessment` carries `confidence`, `failure`; `Plan` carries every `PlannerTrace` field; one `classifier` event per run; Sonnet fallback `probabilities` `None` | §4.7 A, B, C | `test_plan.py::test_outcomes_carry_provenance_for_turn_trace` → fields from the doubles' answers; a `PlannerTrace` built from them validates |
| AC-11 [journey] | Extends J-5: DANGER reaches the safety path by the classifier raise; NODANGER books normally | (a) `tests/unit/agent/nodes/test_plan_graph.py`: AEA-21's real graph and composer, AEA-21 node doubles, the three real plan nodes, a real `ModelGateway` with `FakeChoiceModel`s (mock level). (b) `tests/journeys/j5/test_aea_37.py` on AEA-57's harness: the real app, a scripted raw model, assertions on blocks and on the `turns`, `check_events`, `cases` and `spend_ledger` rows | (a) in G-5 → both tests pass; (b) `uv run pytest -m journey tests/journeys/j5/test_aea_37.py -q -rs` → `2 skipped` with `blocked-on AEA-NN` reasons, or `2 passed` once every need is bound, never a failure; record at level `mock-tested`, *Blocked by* the owners in the skip reasons and AEA-51 |
| AC-12 [regression/context] | Area-map A7d row, ICM row, DO-3 §3 rows marked built, in the same change | §5 step 12 (own ICM row; own `**Built:**` line and the two tree markers) | `git diff --name-only main...HEAD` lists the three docs and the journey record; only this ticket's text changed in each |

### 3.2 Plan-added criteria (the reconciliation found them; the issue gets a comment proposing them)

| ID | Criterion | Basis | Test |
|---|---|---|---|
| PA-1 [invariant] | WP-3 example pair end to end through the three nodes (planner → classifier → join) gives the WP-3 row of §1.1 | Ticket *Example pair*; build-loop rule "the WP-N worked pair is one of the named tests" | `test_plan.py::test_wp3_example_pair` |
| PA-2 [invariant] | Prompt ↔ consumer: every `PLANNER_FIELDS` field name and option key equals `PlannerChoices`' field and `Literal` values exactly, in order; `CLASSIFIER_FIELDS` options equal `DangerAssessment.label`'s values | `integrated-journeys.md` §3 rule 4 | `test_routing_prompts.py::test_choice_fields_match_consumer_types` |
| PA-3 [invariant] | SP-1 wording kept verbatim where DO-4 did not extend it | Ticket "wording starts from SP-1's measured …" | `test_routing_prompts.py::test_sp1_wording_kept` |
| PA-4 [failure/refusal] | A Jev answer that fails `PlannerChoices` validation (a missing field) is a failure (`INVALID_OUTPUT`) and falls back; a classifier answer whose label is not an option is a failure (rules stand) | DO-4 §11 `INVALID_OUTPUT`; `pydantic-data-modeling` §2 | `test_plan.py::test_invalid_planner_answer_falls_back`, `::test_invalid_classifier_label_rules_stand` |
| PA-5 [invariant] | A gateway halt on the classifier writes only `halt` (no `danger`, no event); `plan_join` writes nothing when `state.halt` is set | graph-core §5 (halt routing runs first); M-17 counts classifier runs only | `test_plan.py::test_classifier_halt_writes_only_halt`, `::test_plan_join_skips_on_halt` |
| PA-6 [invariant] | On a turn whose `danger.raised` is true the task brake never fires (the turn must reach safety) | R-8 safety first; AEA-21 router order puts `halt_route` before `danger raised` | `test_plan.py::test_danger_raised_skips_brake` |
| PA-7 [invariant] | `plan.py` and `routing.py` import only the layers DO-3 §2.1 allows; `meridian.agent.gateway` only under `TYPE_CHECKING` | DO-3 §2.1; `code-design-solid-modularity` | `test_routing_prompts.py::test_plan_modules_import_allowed_layers` |
| PA-8 [invariant] | JEV redaction leaves every planner and classifier wording string unchanged, so the gateway's second redaction pass (system, instructions, options) sends exactly this wording | `integrated-journeys.md` §3 rule 4; AEA-20 `_redact_choice` (§4.4) | `test_routing_prompts.py::test_jev_leaves_wording_unchanged` |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Planner sees only `PlannerInput` | DO-4 §3 | AC-8 | in-ticket | step 4 |
| `recent_chat` from `state.chat_window`, ≤ 6 × 400, never re-read `messages` | graph-core §7; ticket | AC-9 | in-ticket | step 4 |
| The current turn's own line is not repeated in `recent_chat` | graph-core §7 "The newest customer message is sent separately" | no | **added** (§4.7 A step 1: lines with `turn_id == turn_input.turn_id` are dropped) | step 4 |
| Redact first, then cut to 400 chars | data.md §1; leak safety (a cut phone stops matching) | no | **added** | step 4 |
| Sonnet fallback only for a failure, never a halt | models.md cross-topic 4 | AC-3 | in-ticket | step 5 |
| `planner_fallback` cause = Jev failure kind, `recovered` = Sonnet answered | graph-nodes §4 | AC-3, AC-4 | in-ticket | step 5 |
| Gateway halt on the fallback call | models.md §5 | no | **added**: `planner` returns the Jev failure outcome plus the `halt`; no signal (R-6) | step 5 |
| Classifier halt | graph-core §5 | no | **added** PA-5 | step 6 |
| Invalid model output is a failure | DO-4 §11 `INVALID_OUTPUT` | no | **added** PA-4 | steps 5, 6 |
| Raise-only against the rules' verdict | R-47; DO-4 §4 | AC-1 | in-ticket | step 6 |
| One `classifier` event per run, `pass` included | GRN-5; M-17 | AC-2, AC-10 | in-ticket | step 6 |
| `join_plan` normalize steps, order by code, `topic` always set | DO-4 §4; SP-1 step 7 | AC-5 | in-ticket | step 7 |
| `planner` `unsupported_other` → `HandoffReason.UNSUPPORTED_ACTION` | cases.md §3.4 rule 4 | no | **added** (`_HANDOFF_REASON` map; `test_unsupported_other_maps_to_unsupported_action`) | step 7 |
| GRN-7 `planner_failed` plan | graph-nodes §5 | AC-4 | in-ticket | step 7 |
| `BRAKE_TASKS` halt + `brake` event + `brake_fired` | graph-nodes §1, §4 | AC-6 | in-ticket | step 8 |
| Brake must not pre-empt the safety path | R-8; AEA-21 router order | no | **added** PA-6 | step 8 |
| Halted turn: `plan_join` writes nothing | graph-core §2 `PlannerTrace.plan_mode` "None when no plan was built (a halt before plan_join)" | no | **added** PA-5 | step 8 |
| Node spans | graph-core §4 (`timed_node`, AEA-21) | Observability | other-ticket (AEA-21 wraps every node; nodes never call the sink) | — |
| `model_call` spans, ledger rows, redaction at the gateway | models.md §5 (AEA-20) | Observability | other-ticket (AEA-20) | — |
| `TurnTrace.planner` / `danger_raised` copied into the turn row | graph-core §2 (AEA-21 `turn_trace`) | AC-10 | other-ticket (AEA-21); this ticket proves the fields exist (AC-10) | — |
| Persisting events | web.md §9 (AEA-40) | Observability | other-ticket (AEA-40) | — |
| CAP-2 at the real entry point | graph-nodes §7 (AEA-51) | Observability | other-ticket (AEA-51); AC-11 asserts the two Jev roles at mock level, and through the harness once its steps are bound | — |
| E-5 recall / false alarms | DO-5 | Evaluation | other-ticket (scored at Stage 9; kept passing at AEA-51) | — |
| Late-technician transcript among planner eval cases | graph-core closing table A-6 [A] | Evaluation | other-ticket (AEA-06 eval cases); this ticket adds a synthetic unit row (AC-5) | — |
| `StateFlags.pending_change` | DO-4 §3 | no | **added**: AEA-02 does not build the `pending_change` state key (its §8.2), so the flag is read from `settled.current_visit().change_request` (R-5) | step 4 |
| Affirmative / slot-pick detection home | SP-1 `gates.is_affirmative`, `mentions_slot_pick` | no | **added** as private constants in `plan.py` (no owner exists in `gates/`; R-8) | step 7 |

| SP-1 continuation on a phone typed while unverified | SP-1 `normalize` step 5 | no | **not carried over** (PD-8): DO-4 §4 names only "Yes, please." and a slot pick | — |
| PRD R-45 "recent clean chat plus a state summary" for the planner | PRD R-45; DO-4 §3 | partly (AC-8, AC-9) | in-ticket: the summary is `StateFlags` (PD-9); answers AEA-34's R-3 for the planner side | step 4 |
| The gateway re-redacts `system`, `instructions` and `options` | AEA-20 `_redact_choice` | no | **added** PA-8 | step 3 |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None — WF-1 internals only (its CON-1/CON-2 entry is AEA-40) | WF-1 | yes (DO-6 WF-1) | M-1, M-3, M-4, M-6…M-9, M-14, M-16…M-26, M-29 |

---

## 4. Shared code to use (exact shapes; re-read the files on `main` before coding and **stop** if a name differs)

### 4.0 Module rules (both source files)

1. First line after the module docstring: `from __future__ import annotations`.
2. Absolute imports only. `plan.py` may import at run time: stdlib, `pydantic` (`ValidationError`), `langgraph.runtime`
   (`Runtime`), `meridian.domain.*`, `meridian.ports.models`, `meridian.policy.limits`, `meridian.privacy.redact`,
   `meridian.agent.context`, `meridian.agent.signals`, `meridian.agent.prompts.routing`; and **only inside
   `if TYPE_CHECKING:`** `meridian.agent.gateway` (for `ModelOutcome`). **Never** `meridian.agent.routers`,
   `meridian.agent.graph`, another `meridian.agent.nodes.*` module, `meridian.gates`, `meridian.services`,
   `meridian.adapters`, `anthropic`, `httpx`. `routing.py` may import: stdlib, `meridian.domain.turn`,
   `meridian.ports.models` only.
3. No module-level instances except immutable constants (`MappingProxyType`, tuples, `frozenset`, `re.Pattern`,
   strings, frozen pydantic models). No clock read, no logger, no settings at import.
4. Mypy strict with the pydantic plugin and `init_typed = true`: build IDs with their classes (`TurnId("…")`), enums with
   members. One statement per line. Errors and exception messages carry codes and counts only, never customer text.
5. Target size: `plan.py` ≤ 400 lines (hard cap 600), `routing.py` ≤ 150.

### 4.1 Types (AEA-02; import paths are binding)

```python
from meridian.domain.common import Halt, HaltReason, HandoffReason, ProviderFailure, ProviderFailureKind, ProviderName
from meridian.domain.state import ConversationState, DangerUpdate, OpenTask, PlanJoinUpdate, PlannerUpdate
from meridian.domain.turn import (CheckEvent, DangerAssessment, GateDecision, Plan, PlannedTask, PlannerChoices,
                                  PlannerInput, PlannerOutcome, RuleMatches, SignalName, SignalRecord, SpecialistKind,
                                  StateFlags, TaskIntent, Topic, TurnContext)
from meridian.ports.models import ChoiceAnswer, ChoiceRequest, ChoiceRole, Role
# TYPE_CHECKING only (§4.4): from meridian.agent.gateway import ModelOutcome
# routing.py: from meridian.domain.turn import PlannerInput; from meridian.ports.models import ChoiceField, ChoiceRequest
```

Shapes (copied from AEA-02 plan §4.1, §4.8, §4.10 and ports §4; DO-4 §3–§4, §11–§12; graph-nodes §1, §4, §5, §9.1):

```python
class RuleMatches(MeridianModel):   safety: SafetyKind | None; burning_unclear: bool; danger_words: bool; person: bool
                                    policy_trigger: HandoffReason | None; rule_ids: tuple[str, ...]; correction: bool
class GateDecision(MeridianModel):  kind: GateKind; rules: RuleMatches; burning_answer: … = None; resume_task_id: str | None = None
class StateFlags(MeridianModel):    verified: bool; open_task: Literal["none", "knowledge", "account", "scheduling"]
                                    open_task_intent: TaskIntent | None; slots_shown: int; has_open_case: bool; pending_change: bool
class PlannerInput(MeridianModel):  latest_message: str; recent_chat: tuple[str, ...]; flags: StateFlags
class PlannerChoices(LLMFacing):    knowledge: Literal["no", "yes"]
                                    account: Literal["none", "invoice", "membership", "appointments", "warranty"]
                                    scheduling: Literal["none", "book_new", "reschedule", "cancel", "confirm"]
                                    handoff: Literal["none", "refund", "billing_dispute", "membership_cancel",
                                                     "unsupported_other", "complaint_or_manager", "late_technician"]
                                    topic: Topic        # Literal["booking", "membership", "billing", "warranty", "other"]
class PlannerOutcome(MeridianModel): choices: PlannerChoices | None; probabilities: dict[str, dict[str, float]] | None
                                     model: str; fallback_used: bool; failure: ProviderFailure | None
class DangerAssessment(MeridianModel): label: Literal["normal", "burning_unclear", "danger"]; raised: bool
                                       confidence: float | None = Field(default=None, ge=0, le=1); failure: ProviderFailure | None
class TaskIntent(StrEnum): ANSWER_QUESTION, READ_INVOICE, READ_MEMBERSHIP, READ_APPOINTMENTS, READ_WARRANTY,
                           BOOK_NEW, RESCHEDULE, CANCEL, CONFIRM          # values = lower-case names
class PlannedTask(MeridianModel):   order: int = Field(ge=1, le=3); specialist: Literal["knowledge", "account", "scheduling"]
                                    intent: TaskIntent; needs_identity: bool; resumes_task_id: str | None = None
class Plan(MeridianModel):          mode: Literal["talk", "act"]; tasks: tuple[PlannedTask, ...] = Field(max_length=3)
                                    handoff_request: HandoffReason | None; topic: Topic
                                    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]
                                    planner_failed: bool = False
class ProviderFailure(MeridianModel): kind: ProviderFailureKind; provider: ProviderName; http_status: int | None
                                      retry_after_s: float | None; retryable: bool; provider_request_id: str | None
class Halt(MeridianModel):          reason: HaltReason; node: str; elapsed_ms: int
CheckEvent.from_danger(turn_id, danger) -> CheckEvent   # failure → "fallback", codes ("fallback", kind); raised →
                                                        #   "raised", (label,); else "pass", (label,)
CheckEvent.from_halt(turn_id, halt) -> CheckEvent       # BRAKE_* → check "brake", "fired", codes (reason, node)
class SignalRecord(MeridianModel):  record="signal"; name: SignalName; turn_id; thread_id; request_id; run_tag; node: str
                                    cause: str | None = None; role: Literal["planner", "classifier", "specialist",
                                    "responder", "brief"] | None = None; specialist=None; attempt=None; recovered: bool | None = None
class ChoiceField(MeridianModel):   name: str; instructions: str; options: dict[str, str] = Field(max_length=255)
class ChoiceRequest(MeridianModel): system: str; state: dict[str, JsonValue]; fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel):  choices: dict[str, str]; probabilities: dict[str, dict[str, float]] | None
class CallRecord(ProviderCall):     role: Role; attempt: int   # ProviderCall: provider: ProviderName; model: str; …;
                                                               #   provider_request_id: str | None; status; failure
class Role(StrEnum): PLANNER = "planner"; CLASSIFIER = "classifier"; PLANNER_FALLBACK = "planner_fallback"; …
# domain/state.py: OpenTask(task_id, specialist, intent, opened_turn, details: TaskDetails, status: Literal["open",
#   "waiting_identity", "done"]); ChatLine(speaker: Literal["customer", "assistant", "representative", "event"], text,
#   turn_id: TurnId | None, at); ConversationState keys used here: turn_input (.turn_id, .text_store), chat_window,
#   identity (.status), open_tasks, shown_slots, settled (Settled | None; .open_case; .current_visit() -> VisitView | None
#   with .change_request), gate, planner, danger, halt.
class PlannerUpdate(TypedDict, total=False):   planner: PlannerOutcome; halt: Halt
class DangerUpdate(TypedDict, total=False):    danger: DangerAssessment; check_events: tuple[CheckEvent, ...]; halt: Halt
class PlanJoinUpdate(TypedDict, total=False):  plan: Plan; check_events: tuple[CheckEvent, ...]; halt: Halt
```

### 4.2 Limits and redaction (on `main` now)

```python
from meridian.policy.limits import Brakes, ContextLimits      # Brakes.tasks_per_turn = 3; ContextLimits.planner_lines = 6,
                                                               #   planner_line_chars = 400; Limits.brakes, Limits.context
from meridian.privacy.redact import RedactionProfile, redact  # redact(text, RedactionProfile.JEV) -> Redacted (.text)
```

Measured on `main` (2026-10-21, this planner): `redact("my name is Omar Patel and my number is 512-555-0102", JEV).text
== "my name is [name] and my number is [phone]"`; `MHC-…` → `[customer id]`; `INV-…` → `[invoice id]`; a 16-digit
spaced card → `[card number removed]`; a standalone 6-digit code → `[code]`; `"I'm Omar Patel"` → `"I'm [name]"`;
`"Yes, please."` unchanged; JEV is idempotent.

### 4.3 AEA-21 (graph spine) — what this ticket calls

```python
from langgraph.runtime import Runtime                          # Runtime(context=ctx) works on langgraph 1.2.16
from meridian.agent.context import GraphDeps                   # frozen dataclass; fields in order: gateway: ModelGateway,
                                                               #   retrieval, uow, identity, scheduling, handoff, brief, demo,
                                                               #   limits: Limits, trace, specialists, cases, ledger (service
                                                               #   fields are `Any` aliases until their tickets land, PD-7)
from meridian.agent.signals import emit_signal                 # emit_signal(ids: TurnIds, record: SignalRecord) -> None;
                                                               #   logs one record on logger "meridian.signal" with
                                                               #   extra={"signal": record.model_dump(mode="json")};
                                                               #   ValueError if record.turn_id/thread_id ≠ ids
```

AEA-21's stub signatures (graph-nodes §9.4) — keep them **exactly**:

```python
def planner(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlannerUpdate: ...
def danger_classifier(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> DangerUpdate: ...
def plan_join(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlanJoinUpdate: ...
```

`build_graph` registers them by these names (`NODE_NAMES`: `"planner"`, `"danger_classifier"`, `"plan_join"`) and wraps
each in `timed_node`; nodes never call `deps.trace`. AEA-21's `route_after_plan_join` order: `halt_route` → `danger.raised`
→ `safety`; `plan.planner_failed and not plan.tasks` → `escalation`; `not plan.tasks and plan.handoff_request` →
`escalation` (PD-1); `talk` → `facts`; act without tasks → `facts` (PD-2); else `route_act_plan` (identity when any task
`needs_identity` and identity is not `verified`, else one `Send` per task).

### 4.4 The gateway (AEA-20, on `main`), called by injection only

```python
# src/meridian/agent/gateway.py (read only)
class ModelOutcome[T: BaseModel](MeridianModel):
    value: T | None
    calls: tuple[CallRecord, ...]
    failure: ProviderFailure | None
    halt: Halt | None

class ModelGateway:
    def choose(self, role: ChoiceRole, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]: ...

# src/meridian/ports/models.py
ChoiceRole = Literal[Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK]
```

Gateway rules this code relies on (models.md §5, built by AEA-20): it never raises; it has already made ≤ 2 attempts
when it returns a `failure` (so the node never retries); a `halt` (`DEADLINE`, `PROVIDER_SPEND_CAP`,
`BRAKE_SONNET_CALLS`) comes back with `value=None`; it JEV-redacts every string leaf of the request again,
**including `system` and every field's `instructions` and `options`** (`_redact_choice`) — PA-8 proves that pass leaves
this ticket's wording unchanged. `GraphDeps.gateway` is typed `ModelGateway` (AEA-21's `context.py` imports it under
`TYPE_CHECKING`), so `deps.gateway.choose(...)` is typed `ModelOutcome[ChoiceAnswer]` with no cast.

In `plan.py`, with the other imports: `if TYPE_CHECKING:` / `from meridian.agent.gateway import ModelOutcome`. It is used
only in the private helpers' annotations (`from __future__ import annotations` keeps them unevaluated). There is no
run-time import of `meridian.agent.gateway`: `plan.py` never constructs or depends on the gateway class.

### 4.5 `src/meridian/agent/prompts/routing.py` — wording (verbatim where marked)

```python
"""Planner and danger-classifier wording and choice fields (A7d, AEA-37). SP-1's measured text, extended only by the
DO-4 §4 † fields and the planner's late_technician option."""
from __future__ import annotations
from typing import Final
from meridian.domain.turn import PlannerInput
from meridian.ports.models import ChoiceField, ChoiceRequest

__all__ = ["CLASSIFIER_FIELDS", "CLASSIFIER_SYSTEM", "DANGER_FIELD", "PLANNER_FIELDS", "PLANNER_SYSTEM",
           "classifier_request", "planner_request"]

DANGER_FIELD: Final = "danger_level"
```

`PLANNER_SYSTEM: Final[str]` — **SP-1 verbatim** (one string, single spaces):

> You are the planner for Meridian Home Comfort's customer chat (heating, cooling and plumbing in Austin, Texas). You never write to the customer. Read STATE: the recent chat, any open task and the customer's latest message. For each field choose the one option that fits the customer's latest message, using the open task and recent chat to understand short replies. Choose "none" or "no" when the message does not need that kind of help. Private account details and any booking or change need the account or scheduling fields; public company questions need knowledge.

`PLANNER_FIELDS: Final[tuple[ChoiceField, ...]]` — five fields in this order; option dicts in this insertion order.
Rows marked **SP-1** are verbatim; rows marked **new** are this ticket's wording (decided here):

| # | `name` | `instructions` | `options` (key: description) |
|---|---|---|---|
| 1 | `knowledge` | **SP-1** Does the latest message ask about Meridian's public information: membership plans, prices, fees, warranty, hours, service area, services or policies? | **SP-1** `no`: No company information is needed to answer. · `yes`: The answer needs Meridian's knowledge base. |
| 2 | `account` | **SP-1** Does the customer need their own account records read? | **SP-1** `none`: No private record is needed. · `invoice`: Their invoice or bill: what a charge is for, the balance, the due date. · `membership`: Their own membership: tier, renewal date, cancelling it or stopping its renewal. · `appointments`: Their existing appointments, without changing them. · **new** `warranty`: Their own equipment's warranty: when it was installed or how long its warranty lasts. |
| 3 | `scheduling` | **SP-1** Does the customer want to book a new visit or change an existing one? | **SP-1** `none`: No booking or change is requested. · `book_new`: Book a new service visit, including picking a time the assistant offered for a new visit. · `reschedule`: Move an existing appointment to another time, including confirming a new time the assistant offered. · **new** `cancel`: Cancel an existing appointment. · **new** `confirm`: Check that an existing appointment is still on, or its date, time or technician, without changing it. |
| 4 | `handoff` | **SP-1** Does the message ask for something that must go to a staff member? | **SP-1** `none`: Nothing for staff. · `refund`: Asks for money back. · `billing_dispute`: Says a charge is wrong or disputes it. · `membership_cancel`: Wants to cancel a membership or stop it renewing. · `unsupported_other`: Asks the chat to send, email or change something it cannot, such as a copy of a document, a payment link or autopay. · `complaint_or_manager`: Complains about staff or work, asks for a manager, or mentions legal action or a chargeback. · **new** `late_technician`: Says a technician is late, has not arrived in the booked window, or missed the visit. |
| 5 | `topic` | **new** Which subject is the latest message mainly about? | **new** `booking`: Booking, moving, cancelling or checking a service visit, or a problem at home that needs a visit. · `membership`: The Comfort Club membership: what it includes, its price, renewal or cancelling it. · `billing`: An invoice, a charge, a payment, a refund or a fee. · `warranty`: A warranty: what it covers or how long it lasts. · `other`: Anything else, including a greeting or a short reply with no subject of its own. |

`CLASSIFIER_SYSTEM: Final[str]` — **SP-1 verbatim**:

> You check one customer message sent to a home heating, cooling and plumbing company. Choose "normal" unless the message itself says or clearly implies someone is in danger or there is an unexplained burning smell. You never reply to the customer.

`CLASSIFIER_FIELDS: Final[tuple[ChoiceField, ...]]` — **SP-1 verbatim**, one field:
`ChoiceField(name=DANGER_FIELD, instructions="Is anyone in danger because of conditions in the home, or is there a
burning smell whose cause is unclear?", options={"normal": "No one is said to be at risk: an ordinary comfort or service
problem, such as an AC not cooling or a question about a bill.", "burning_unclear": "Mentions a burning or electrical
smell without saying whether a breaker tripped.", "danger": "Says or clearly implies a person is at risk because of the
conditions, for example an elderly person, a baby or someone unwell in a very hot or very cold home, or water near
electrics."})`.

```python
def planner_request(planner_input: PlannerInput) -> ChoiceRequest:
    """The one planner request: system + fields are module constants (identical every turn); state is exactly
    PlannerInput (DO-4 §3 "What crosses this line: only PlannerInput")."""
    # return ChoiceRequest(system=PLANNER_SYSTEM, state=planner_input.model_dump(mode="json"), fields=PLANNER_FIELDS)

def classifier_request(latest_message: str) -> ChoiceRequest:
    """The classifier sees the latest message only (SP-1 shape)."""
    # return ChoiceRequest(system=CLASSIFIER_SYSTEM, state={"latest_message": latest_message}, fields=CLASSIFIER_FIELDS)
```

The caller passes already-redacted text; `routing.py` does no redaction and no I/O.

### 4.6 SP-1 follow-up patterns (private constants in `plan.py`)

```python
_AFFIRMATIVE: Final = re.compile(r"^\s*(yes|yeah|yep|yup|sure|ok|okay|please do|go ahead|sounds good|that works|perfect)\b",
                                 re.IGNORECASE)                                    # SP-1 gates.is_affirmative
_WEEKDAY: Final = re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE)
_RANGE: Final = re.compile(r"\b\d{1,2}\s*(?:to|-|–)\s*\d{1,2}\b")                 # SP-1 mentions_slot_pick
_WORKS: Final = re.compile(r"\bworks\b", re.IGNORECASE)
def _continues_open_task(text: str) -> bool:   # affirmative, or a weekday, a "4 to 7" range or "works"
```

### 4.7 `src/meridian/agent/nodes/plan.py` — signatures and algorithms

```python
"""Planner, raise-only danger classifier and plan join (A7d, AEA-37; graph-nodes §9.4)."""
__all__ = ["TaskBrakeExceeded", "build_planner_input", "danger_classifier", "join_plan", "plan_join", "planner",
           "raise_only", "rules_verdict"]

DangerLabel: TypeAlias = Literal["normal", "burning_unclear", "danger"]
_DANGER_RANK: Final[Mapping[str, int]] = MappingProxyType({"normal": 0, "burning_unclear": 1, "danger": 2})
_LABELS: Final[Mapping[str, DangerLabel]] = MappingProxyType({"normal": "normal", "burning_unclear": "burning_unclear",
                                                              "danger": "danger"})     # str → Literal narrowing
_UNKNOWN_MODEL: Final = "unknown"
_JEV: Final[ProviderName] = "openrouter_jev"
_ANTHROPIC: Final[ProviderName] = "anthropic"
_ACCOUNT_INTENT: Final[Mapping[str, TaskIntent]] = MappingProxyType({"invoice": TaskIntent.READ_INVOICE,
    "membership": TaskIntent.READ_MEMBERSHIP, "appointments": TaskIntent.READ_APPOINTMENTS,
    "warranty": TaskIntent.READ_WARRANTY})
_SCHEDULING_INTENT: Final[Mapping[str, TaskIntent]] = MappingProxyType({"book_new": TaskIntent.BOOK_NEW,
    "reschedule": TaskIntent.RESCHEDULE, "cancel": TaskIntent.CANCEL, "confirm": TaskIntent.CONFIRM})
_HANDOFF_REASON: Final[Mapping[str, HandoffReason | None]] = MappingProxyType({"none": None,
    "refund": HandoffReason.REFUND, "billing_dispute": HandoffReason.BILLING_DISPUTE,
    "membership_cancel": HandoffReason.MEMBERSHIP_CANCEL, "unsupported_other": HandoffReason.UNSUPPORTED_ACTION,
    "complaint_or_manager": HandoffReason.COMPLAINT_OR_MANAGER, "late_technician": HandoffReason.LATE_TECHNICIAN})
_TOPIC_BY_INTENT: Final[Mapping[TaskIntent, Topic]] = MappingProxyType({TaskIntent.ANSWER_QUESTION: "other",
    TaskIntent.READ_INVOICE: "billing", TaskIntent.READ_MEMBERSHIP: "membership",
    TaskIntent.READ_APPOINTMENTS: "booking", TaskIntent.READ_WARRANTY: "warranty", TaskIntent.BOOK_NEW: "booking",
    TaskIntent.RESCHEDULE: "booking", TaskIntent.CANCEL: "booking", TaskIntent.CONFIRM: "booking"})
_DEFAULT_TASKS_PER_TURN: Final = Brakes().tasks_per_turn

# (no private Protocol: the helpers below are annotated with ModelOutcome[ChoiceAnswer], imported under TYPE_CHECKING)
class TaskBrakeExceeded(Exception):
    def __init__(self, count: int, limit: int) -> None:   # message: f"plan has {count} tasks; the brake allows {limit}"
        self.count = count; self.limit = limit             # (two statements on two lines)

def build_planner_input(state: ConversationState, limits: ContextLimits) -> PlannerInput: ...
def rules_verdict(rules: RuleMatches) -> DangerLabel: ...
def raise_only(label: DangerLabel, verdict: DangerLabel) -> bool: ...
def join_plan(planner: PlannerOutcome | None, danger: DangerAssessment | None, gate: GateDecision,
              state: ConversationState, *, tasks_per_turn: int = _DEFAULT_TASKS_PER_TURN) -> Plan: ...
def planner(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlannerUpdate: ...
def danger_classifier(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> DangerUpdate: ...
def plan_join(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlanJoinUpdate: ...
```

Private helpers:
- `_choose(deps: GraphDeps, role: ChoiceRole, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]`:
  `return deps.gateway.choose(role, req, ctx)`. *The only place a model is asked.*
- `_model_of(outcome: ModelOutcome[ChoiceAnswer]) -> str`: `outcome.calls[-1].model if outcome.calls else
  _UNKNOWN_MODEL`.
- `_invalid_output(outcome: ModelOutcome[ChoiceAnswer], default: ProviderName) -> ProviderFailure`: `last =
  outcome.calls[-1] if outcome.calls else None`; `ProviderFailure(kind=ProviderFailureKind.INVALID_OUTPUT,
  provider=last.provider if last else default, http_status=None, retry_after_s=None, retryable=False,
  provider_request_id=last.provider_request_id if last else None)`.
- `_parse_planner(outcome: ModelOutcome[ChoiceAnswer], default: ProviderName) -> tuple[PlannerChoices | None,
  ProviderFailure | None]`: `outcome.failure` set → `(None, outcome.failure)`; `outcome.value is None` →
  `(None, _invalid_output(…))`; `PlannerChoices.model_validate(outcome.value.choices)` raising
  `pydantic.ValidationError` → `(None, _invalid_output(…))`; else `(choices, None)`.
  *Invariant: exactly one of the two is `None`.*
- `_signal(ctx, name: SignalName, *, node: str, role: Literal["planner", "classifier"] | None, cause: str,
  recovered: bool | None) -> None`: `emit_signal(ctx.ids, SignalRecord(name=name, turn_id=ctx.ids.turn_id,
  thread_id=ctx.ids.thread_id, request_id=ctx.ids.request_id, run_tag=ctx.ids.run_tag, node=node, cause=cause,
  role=role, recovered=recovered))`. *Codes only: `cause` is always an enum value.*
- `_elapsed_ms(ctx) -> int`: `max(0, int((time.monotonic() - ctx.budget.started) * 1000))`.
- `_cap(text: str, limit: int) -> str`: `text if len(text) <= limit else text[: limit - 1] + "…"`.
- `_last_open_task(state) -> OpenTask | None`: the **last** item of `state.open_tasks` whose `status != "done"`.

**A. `build_planner_input(state, limits)`** (pure; DO-4 §3; context-management rules 1, 4, 5):
1. `prior = [line for line in state.chat_window if line.turn_id != state.turn_input.turn_id]`. *The newest message is
   sent separately (graph-core §7), so it is never also a chat line.*
2. `window = prior[-limits.planner_lines:] if limits.planner_lines > 0 else []`. *Oldest dropped first; a fixed budget.*
3. `recent_chat = tuple(_cap(redact(f"{line.speaker}: {line.text}", RedactionProfile.JEV).text,
   limits.planner_line_chars) for line in window)`. *Redact before cutting, so a cut never leaves an unmasked
   fragment of a phone or card; each line ≤ 400 chars.*
4. `latest = redact(state.turn_input.text_store, RedactionProfile.JEV).text`. *`text_store` is already STORE-redacted;
   JEV adds names, phones, emails, street lines and IDs. The node never reads `messages` or `ctx.intake`.*
5. `task = _last_open_task(state)`; `visit = state.settled.current_visit() if state.settled is not None else None`;
   `flags = StateFlags(verified=state.identity.status == "verified", open_task=task.specialist if task else "none",
   open_task_intent=task.intent if task else None, slots_shown=len(state.shown_slots),
   has_open_case=state.settled is not None and state.settled.open_case is not None,
   pending_change=visit is not None and visit.change_request is not None)`. *Flags only, never values (no customer
   id, no record value).*
6. `return PlannerInput(latest_message=latest, recent_chat=recent_chat, flags=flags)`.

**A'. `planner(state, runtime, *, deps)`** (graph-nodes §9.4; SDQ-6; models.md cross-topic 4):
1. `ctx = runtime.context`; `req = planner_request(build_planner_input(state, deps.limits.context))`.
2. `jev = _choose(deps, Role.PLANNER, req, ctx)`.
3. `jev.halt is not None` → `return {"halt": jev.halt}`. *A halt is never a reason to fall back.*
4. `choices, jev_failure = _parse_planner(jev, _JEV)`. `choices is not None` → `return {"planner":
   PlannerOutcome(choices=choices, probabilities=jev.value.probabilities if jev.value is not None else None,
   model=_model_of(jev), fallback_used=False, failure=None)}`.
5. Otherwise (`jev_failure` set): `fb = _choose(deps, Role.PLANNER_FALLBACK, req, ctx)` — **the same `req` object**.
6. `fb.halt is not None` → `return {"planner": PlannerOutcome(choices=None, probabilities=None, model=_model_of(jev),
   fallback_used=False, failure=jev_failure), "halt": fb.halt}` and emit **no** signal (R-6).
7. `fb_choices, fb_failure = _parse_planner(fb, _ANTHROPIC)`; `_signal(ctx, SignalName.PLANNER_FALLBACK,
   node="planner", role="planner", cause=jev_failure.kind.value, recovered=fb_choices is not None)`.
8. `return {"planner": PlannerOutcome(choices=fb_choices, probabilities=None, model=_model_of(fb), fallback_used=True,
   failure=fb_failure)}`. *Sonnet reports no probabilities: `None`, never invented (DO-4 §0). Invariant for every
   `PlannerOutcome` written: `choices is None` ⇔ `failure is not None`; the Jev failure kind of a fallback lives in the
   signal's `cause`.*

**B. `rules_verdict`, `raise_only`, `danger_classifier`** (R-47):
- `rules_verdict(rules)`: `"danger"` if `rules.safety is not None or rules.danger_words`; elif `rules.burning_unclear` →
  `"burning_unclear"`; else `"normal"`.
- `raise_only(label, verdict)`: `return _DANGER_RANK[label] > _DANGER_RANK[verdict]`. *Never lowers: an equal or lower
  label raises nothing.*
- `danger_classifier`:
  1. `ctx = runtime.context`; `gate = state.gate`; `gate is None` → `raise ValueError("danger_classifier: no gate
     decision in state")`.
  2. `verdict = rules_verdict(gate.rules)`; `latest = redact(state.turn_input.text_store, RedactionProfile.JEV).text`.
  3. `out = _choose(deps, Role.CLASSIFIER, classifier_request(latest), ctx)`.
  4. `out.halt is not None` → `return {"halt": out.halt}`. *No run, no event (PA-5).*
  5. Parse: `out.failure` set → `failure = out.failure`; elif `out.value is None` → `failure = _invalid_output(out, _JEV)`;
     else `label = _LABELS.get(out.value.choices.get(DANGER_FIELD, ""))`; `label is None` → `failure =
     _invalid_output(out, _JEV)`.
  6. Failure → `danger = DangerAssessment(label="normal", raised=False, confidence=None, failure=failure)` and
     `_signal(ctx, SignalName.CLASSIFIER_FALLBACK, node="danger_classifier", role="classifier",
     cause=failure.kind.value, recovered=None)`. *The rules stand.*
  7. Success → `probs = out.value.probabilities`; `p = probs.get(DANGER_FIELD, {}).get(label) if probs else None`;
     `danger = DangerAssessment(label=label, raised=raise_only(label, verdict), confidence=None if p is None else
     min(1.0, max(0.0, float(p))), failure=None)`.
  8. `return {"danger": danger, "check_events": (CheckEvent.from_danger(ctx.ids.turn_id, danger),)}`. *Exactly one
     `classifier` event per run, `pass` included (M-17 denominator).*

**C. `join_plan(planner, danger, gate, state, *, tasks_per_turn)`** — pure; SP-1 `normalize` order; `danger` is
accepted for the DO-4 signature and changes nothing (the router reads `danger.raised`). Each step's invariant in italics:
1. `choices = planner.choices if planner is not None else None`. *A planner failure never blocks the rules.*
2. Start: `knowledge, account, scheduling, handoff = (choices.knowledge, choices.account, choices.scheduling,
   choices.handoff) if choices else ("no", "none", "none", "none")`.
3. `policy = gate.rules.policy_trigger`; `handoff_request = policy if policy is not None else _HANDOFF_REASON[handoff]`.
   *A policy word wins over the model.*
4. `handoff_request is HandoffReason.MEMBERSHIP_CANCEL` → `account = "membership"`, `knowledge = "yes"`. *WP-8 needs the
   renewal date and the cancellation rules.*
5. `scheduling != "none" and account == "appointments"` → `account = "none"`. *Scheduling reads appointments itself.*
6. `drafts: list[tuple[Literal["knowledge","account","scheduling"], TaskIntent, bool, str | None]]` in this order:
   account (`_ACCOUNT_INTENT[account]`, `needs_identity=True`), scheduling (`_SCHEDULING_INTENT[scheduling]`, `True`),
   knowledge `"yes"` (`TaskIntent.ANSWER_QUESTION`, `False`); `resumes_task_id=None`. *Order is set by code.*
7. `source = ("fallback_planner" if planner.fallback_used else "planner") if choices else "rules_only"`.
8. `acts = bool(drafts) or handoff_request is not None`. If `not acts` and `(task := _last_open_task(state))` and
   `_continues_open_task(state.turn_input.text_store)` → `drafts = [(task.specialist, task.intent,
   task.specialist != "knowledge", task.task_id)]`, `source = "open_task"`. *A bare "Yes, please." or a slot pick
   resumes the task even when a choice-only planner misses it; a private task still needs identity (R-14; R-7 below).*
9. `len(drafts) > tasks_per_turn` → `raise TaskBrakeExceeded(len(drafts), tasks_per_turn)`. *Checked before `Plan` is
   built (its `max_length=3` would otherwise raise a validation error).*
10. `planner_failed = planner is not None and choices is None and not drafts and handoff_request is None`. *GRN-7.*
11. `topic = choices.topic if choices else (_TOPIC_BY_INTENT[drafts[0][1]] if source == "open_task" else "other")`.
    *`topic` is set on every plan (M-3).*
12. `mode = "act" if drafts or handoff_request is not None or planner_failed else "talk"`.
13. `return Plan(mode=mode, tasks=tuple(PlannedTask(order=i + 1, specialist=s, intent=it, needs_identity=ni,
    resumes_task_id=r) for i, (s, it, ni, r) in enumerate(drafts)), handoff_request=handoff_request, topic=topic,
    source=source, planner_failed=planner_failed)`.

**D. `plan_join(state, runtime, *, deps)`**:
1. `ctx = runtime.context`. `state.halt is not None` → `return {}`. *A halted turn builds no plan (graph-core §2
   `plan_mode` None); the router's `halt_route` decides.*
2. `gate = state.gate`; `None` → `raise ValueError("plan_join: no gate decision in state")`.
3. `try: plan = join_plan(state.planner, state.danger, gate, state,
   tasks_per_turn=deps.limits.brakes.tasks_per_turn)`.
4. `except TaskBrakeExceeded:` if `state.danger is not None and state.danger.raised` → `return {}` (*PA-6: the brake
   never pre-empts the safety path*); else `halt = Halt(reason=HaltReason.BRAKE_TASKS, node="plan_join",
   elapsed_ms=_elapsed_ms(ctx))`; `_signal(ctx, SignalName.BRAKE_FIRED, node="plan_join", role=None,
   cause=HaltReason.BRAKE_TASKS.value, recovered=None)`; `return {"halt": halt, "check_events":
   (CheckEvent.from_halt(ctx.ids.turn_id, halt),)}`.
5. `return {"plan": plan}`.

---

## 5. Steps (build order; each ends with a check)

**Setup.** Work in the worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-37` (branch
`aea-37-graph-plan-node`). `export UV_LINK_MODE=hardlink`.

0. **Keep the earlier run's work and catch up with `main`** (Refresh 4). In the worktree:
   1. `git status --short` must show only `M src/meridian/agent/nodes/plan.py`, `?? src/meridian/agent/prompts/routing.py`,
      `?? tests/unit/agent/nodes/plan_fixtures.py`, `?? tests/unit/agent/prompts/` (plus any of this plan's other owned
      files). Anything outside §2.1 → stop and report; do not delete it.
   2. `git log --oneline main..HEAD` must be empty. Then `git merge --ff-only main`. `main`'s new commits touch none of
      these files, so the fast-forward keeps the uncommitted work in place. If git refuses, stop and report (never
      `git stash drop`, `git reset --hard`, `git checkout -- <file>` or `git clean`).
   3. `uv sync`.
   4. Read the four existing files against §4.5, §4.6, §4.7 and §6. Keep everything that matches, fix what differs, and
      add what is missing. `plan.py` is 473 lines: over the 400 target but under the 600 hard cap, so it is acceptable.
      Do not split it into a new module (that would be a file outside §2.1). Steps 1, 2 and 4–8 then become "check and
      complete" steps. Their checks still run.

`uv sync` (if step 0.3 has not already run it). Never copy a venv, and put no `node_modules` in the worktree. Import check
(the only "baseline"): `uv run python -c "import meridian.agent.context, meridian.agent.signals, meridian.agent.graph,
meridian.agent.nodes.plan, meridian.agent.gateway, tests.graph._spine_doubles, tests.unit.agent._gateway_doubles,
tests.fakes, tests.journeys.support.run"` exits 0. Then open `src/meridian/domain/{turn,state,common}.py`,
`src/meridian/ports/models.py`, `src/meridian/agent/{context,signals,gateway}.py`, `src/meridian/agent/nodes/plan.py`
(the stub), `tests/graph/_spine_doubles.py`, `tests/unit/agent/_gateway_doubles.py`, `tests/fakes/models.py`,
`tests/journeys/support/README.md` and `tests/journeys/j1/test_aea_57.py`. **Stop and report** if any name in §4.1–§4.4,
§6 or §7.1 differs. This planner checked them all on `0a85270` and `a81f59d`, and confirmed on `dd1b110` that none of
their files changed, so a difference means a sibling changed them since.

1. **Marker.** `test -e tests/unit/agent/prompts/__init__.py || touch tests/unit/agent/prompts/__init__.py` (0 bytes).
   `tests/unit/agent/nodes/__init__.py` already exists; leave it alone.
2. **`agent/prompts/routing.py`** per §4.5. Check: `uv run python -c "from meridian.agent.prompts.routing import
   PLANNER_FIELDS, CLASSIFIER_FIELDS; print(len(PLANNER_FIELDS), len(CLASSIFIER_FIELDS))"` prints `5 1`.
3. **`tests/unit/agent/nodes/plan_fixtures.py`** per §6, then **`test_routing_prompts.py`**
   (`test_choice_fields_match_consumer_types`, `test_sp1_wording_kept`, `test_jev_leaves_wording_unchanged`,
   `test_plan_modules_import_allowed_layers` — the last one fails until step 4 exists; that is expected). Check: the
   first three pass.
4. **`plan.py` part 1**: module header, imports (with the `TYPE_CHECKING` block), constants, `TaskBrakeExceeded`,
   helpers, `build_planner_input` (§4.7 A). Check: `uv run mypy src/meridian/agent/nodes/plan.py`.
5. **`planner`** (§4.7 A'). Write `test_planner_fallback_sdq6`, `test_planner_halt_never_falls_back`,
   `test_invalid_planner_answer_falls_back`. Check: they pass.
6. **`rules_verdict`, `raise_only`, `danger_classifier`** (§4.7 B). Write `test_classifier_raise_only`,
   `test_classifier_failure_rules_stand`, `test_invalid_classifier_label_rules_stand`,
   `test_classifier_halt_writes_only_halt`. Check: they pass.
7. **`join_plan`** (§4.7 C) + `tests/unit/agent/nodes/test_join_plan.py` (all rows in §7.1). Check: pass.
8. **`plan_join`** (§4.7 D). Write `test_task_brake_halts_with_event`, `test_plan_join_skips_on_halt`,
   `test_danger_raised_skips_brake`, `test_both_planners_fail_planner_failed_plan`,
   `test_both_planners_fail_open_task_continues`, `test_wp3_example_pair`, `test_plan_nodes_write_only_own_keys`,
   `test_outcomes_carry_provenance_for_turn_trace`. Check: `uv run pytest tests/unit/agent/nodes -q`.
9. **AC-8, AC-9**: `test_requests_cross_only_planner_input`, `test_stable_prefix_turns_1_2_5`. Check:
   `uv run pytest tests/unit/agent/prompts -q` (all, incl. the import-layer test).
10. **Graph run and journey (AC-11)**: `tests/unit/agent/nodes/test_plan_graph.py` and
    `tests/journeys/j5/test_aea_37.py` per §7.1. Check: `uv run pytest tests/unit/agent/nodes/test_plan_graph.py -q` →
    `2 passed`; `uv run pytest -m journey tests/journeys/j5/test_aea_37.py -q -rs` → `2 skipped` with `blocked-on AEA-NN`
    reasons (or `2 passed`), never a failure or a collection error.
11. **Gates** §7.3 in order, cheapest first; stop at the first red **except** the known R-1 conflict (§7.2). Then the
    feature commit:
    `git add src/meridian/agent/nodes/plan.py src/meridian/agent/prompts/routing.py tests/unit/agent/nodes/plan_fixtures.py
    tests/unit/agent/nodes/test_plan.py tests/unit/agent/nodes/test_join_plan.py tests/unit/agent/nodes/test_plan_graph.py
    tests/unit/agent/prompts/__init__.py tests/unit/agent/prompts/test_routing_prompts.py
    tests/unit/agent/prompts/test_routing_prompt_turns.py tests/journeys/j5/test_aea_37.py`; message `feat(graph): plan node — planner, raise-only classifier, join_plan (AEA-37)`.
12. **Context (AC-12) and record (AC-11)**, a second commit `docs(context): AEA-37 built paths and journey record`:
    - `docs/testing/journeys/<YYYY-MM-DD>-AEA-37.md` per §7.4 (use the feature commit's SHA).
    - `.claude/reference/area-map.md`, A7d row, **Status cell only**: if it reads `planned`, write `partly built:
      agent/nodes/plan.py, agent/prompts/routing.py actual (AEA-37, <sha>); agent/nodes/front.py planned (AEA-36)`;
      if AEA-36 already changed it, keep its text and add `; agent/nodes/plan.py, agent/prompts/routing.py actual
      (AEA-37, <sha>)`.
    - `.claude/state/icm-progress.md`: **add one row** (one line in the file) directly below the last *Routes verified
      against code and tests* row: `| Routes verified against code and tests | provisional | 2026-10-21: A7d →
      agent/nodes/plan.py, agent/prompts/routing.py checked against tests/unit/agent/nodes/test_{plan,join_plan}.py and
      tests/unit/agent/prompts/ (AEA-37, <sha>; <n> pass) | Each slice adds its route; verified when every area-map row
      is actual |` (≤ 400 characters; your run date if later; `<n>` = G-5's passed count). Edit no other row and not
      the *Last reconciled* line.
    - `docs/design/code-design.md`, `## 3. The module map` only. First, add a new line directly after the last existing
      `**Built:**` line, in the same shape as the existing ones (paths and sha in backticks): **Built:**
      `agent/nodes/plan.py`, `agent/prompts/routing.py` (AEA-37, `<sha>`). Second, on the tree line that starts
      `│   ├── nodes/plan.py`, replace the trailing `stub AEA-21 6df4f4c` with `built AEA-37 <sha>`. Third, append
      `   built AEA-37 <sha>` to the end of the tree line that starts `│   ├── prompts/routing.py`. Change nothing else
      in the file.
    - `git add` those four paths explicitly.

**Commits:** explicit `git add <paths>` only (never `-A`); last line of every message
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Commit only on your branch; never push `main`; never
force-push.

**Do not:**
- edit any file outside §2.1 (in particular `routers.py`, `graph.py`, `compose.py`, `tests/graph/*`, `gates/*`,
  `domain/*`, the OpenAPI file, `UI_CONTRACTS.md`, `docs/ux/**`, `apps/web/**`);
- import `meridian.agent.gateway` at run time (only inside `if TYPE_CHECKING:`), `meridian.gates`, services, adapters,
  `tests/*`, or read `ctx.intake`;
- retry a gateway call yourself, fall back on a halt, or call `Role.PLANNER_FALLBACK` more than once;
- let `danger_classifier` lower a verdict, or write `raised=True` on a failure;
- put customer text, a value or a model name in a `CheckEvent.codes`, a signal `cause` or an exception message;
- add a state key, a `domain/` type, a dependency, a customer sentence or a `# type: ignore`;
- write a full phone number, a six-digit code or a card-like number as a literal in any file (build test values
  from parts at run time, §6); call a paid model; mark anything `live`;
- run the full suite (no shared fixture, settings or dependency changes here); run pytest with more than `-n 2`;
  bind ports 4019 or 5184; read `.env`.

---

## 6. Data and fixtures (synthetic only)

**Source samples.** Worked pairs WP-1, WP-2 (the seeded name, IDs and phone), WP-3, WP-4F, WP-7, WP-8 from
`docs/data/worked-pairs.md`; DANGER and NODANGER from `docs/design/evaluation-plan.md` (synthetic, labelled there); a
synthetic late-technician sentence (labelled synthetic in its test docstring). IDs below are synthetic UUID4 constants.

**`tests/unit/agent/nodes/plan_fixtures.py`** (plain helpers, no pytest fixtures with side effects). It **reuses**
AEA-21's `tests/graph/_spine_doubles.py` (names fixed by AEA-21's plan §6) and AEA-11's `tests.fakes`, and builds real
`ModelOutcome` values:

```python
from tests.fakes import provider_call                           # AEA-11: keyword-only ProviderCall builder
from tests.graph._spine_doubles import DEMO_NOW, REQ, THREAD, RecordingSink, make_ctx, make_input, no_rules
from tests.graph._spine_doubles import make_deps as spine_deps
from meridian.agent.gateway import ModelOutcome                  # tests may import it at run time

TURN_0 = TurnId("0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d")          # earlier turn (open tasks, chat lines)
TURN_1 = TurnId("1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d")
TURN_2 = TurnId("2b3c4d5e-6f7a-4b8c-9d0e-1f2a3b4c5d6e")
TURN_3 = TurnId("3c4d5e6f-7a8b-4c9d-8e0f-1a2b3c4d5e6f")
TURN_4 = TurnId("4d5e6f7a-8b9c-4d0e-9f1a-2b3c4d5e6f7a")
TURN_5 = TurnId("5e6f7a8b-9c0d-4e1f-8a2b-3c4d5e6f7a8b")
JEV_MODEL = "jev-test-model"
SONNET_MODEL = "sonnet-test-model"

def seeded_phone() -> str        # "-".join(["512", "555", "01" + "02"])   WP-2's synthetic 555 number, from parts
def seeded_code() -> str         # "".join(["91", "42", "76"])             six digits, from parts
def seeded_card() -> str         # " ".join(["4000", "1234", "5678", "9010"])   card-like, from parts

def runtime(ctx: TurnContext) -> Runtime[TurnContext]            # Runtime(context=ctx)
def rules(**kw: Any) -> RuleMatches                               # no_rules().model_copy(update=kw)
def free_text_gate(**rule_kw: Any) -> GateDecision                # GateDecision(kind=GateKind.FREE_TEXT, rules=rules(**rule_kw))
def open_task(task_id: str = "t-1", *, specialist: SpecialistKind = "scheduling",
              intent: TaskIntent = TaskIntent.RESCHEDULE,
              status: Literal["open", "waiting_identity", "done"] = "open") -> OpenTask
    # OpenTask(task_id=…, specialist=…, intent=…, opened_turn=TURN_0, details=TaskDetails(), status=…)
def line(speaker: Literal["customer", "assistant", "representative", "event"], text: str,
         turn_id: TurnId | None) -> ChatLine                    # at=DEMO_NOW
def make_state(text: str, *, turn_id: TurnId = TURN_1, gate: GateDecision | None = None,
               chat: Sequence[ChatLine] = (), tasks: Sequence[OpenTask] = (), identity: IdentityState | None = None,
               settled: Settled | None = None, planner: PlannerOutcome | None = None,
               danger: DangerAssessment | None = None, halt: Halt | None = None,
               shown_slots: Sequence[ShownSlot] = ()) -> ConversationState
    # ConversationState(thread_id=THREAD, turn_input=make_input(turn_id, text), gate=gate or free_text_gate(),
    #   settled=settled or Settled(actions=(), open_case=None, read_at=DEMO_NOW), chat_window=list(chat),
    #   open_tasks=list(tasks), shown_slots=list(shown_slots), planner=planner, danger=danger, halt=halt,
    #   **({"identity": identity} if identity is not None else {}))
def merged(state: ConversationState, *updates: Mapping[str, Any]) -> ConversationState
    # applies each update with state.model_copy(update=…) in order; `check_events` are concatenated (the reducer's
    #   effect within one turn) and `halt` keeps the first non-None value (first_halt)
def choices(**kw: str) -> dict[str, str]
    # {"knowledge": "no", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"} | kw
def failure(kind: ProviderFailureKind, provider: ProviderName = "openrouter_jev") -> ProviderFailure
    # http_status=None, retry_after_s=None, provider_request_id=None,
    #   retryable=kind in {TIMEOUT, CONNECTION, RATE_LIMITED, OVERLOADED, SERVER}
def record(role: Role, fail: ProviderFailure | None = None) -> CallRecord
    # PLANNER, CLASSIFIER → model JEV_MODEL, provider "openrouter_jev"; PLANNER_FALLBACK → SONNET_MODEL, "anthropic"
    # CallRecord.from_provider(provider_call(provider=…, model=…, failure=fail), role=role, attempt=1)
def ok(role: Role, picks: dict[str, str], *,
       probabilities: dict[str, dict[str, float]] | None = None) -> ModelOutcome[ChoiceAnswer]
    # ModelOutcome[ChoiceAnswer](value=ChoiceAnswer(choices=picks, probabilities=probabilities),
    #   calls=(record(role),), failure=None, halt=None)
def failed(role: Role, kind: ProviderFailureKind) -> ModelOutcome[ChoiceAnswer]
    # f = failure(kind, <provider of role>); ModelOutcome[ChoiceAnswer](value=None, calls=(record(role, f),),
    #   failure=f, halt=None)
def halted(role: Role, reason: HaltReason) -> ModelOutcome[ChoiceAnswer]
    # ModelOutcome[ChoiceAnswer](value=None, calls=(), failure=None,
    #   halt=Halt(reason=reason, node=role.value, elapsed_ms=0))

class ScriptedGateway:                  # the gateway double (DO-4 §12 `choose` signature)
    def __init__(self, script: Mapping[Role, Sequence[ModelOutcome[ChoiceAnswer]]]) -> None   # one queue per role
    calls: list[tuple[Role, ChoiceRequest]]                                                     # every request, in order
    def choose(self, role: Role, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]
        # records (role, req); pops the role's next outcome; an empty or missing queue →
        #   raise AssertionError(f"unexpected {role.value} call")   (a test bug; plan.py has no `except` that hides it)
def make_deps(gateway: object, *, limits: Limits | None = None) -> GraphDeps
    # dataclasses.replace(spine_deps(RecordingSink()), gateway=cast("ModelGateway", gateway), limits=limits or Limits())
    #   (import ModelGateway under TYPE_CHECKING for the cast string, as _spine_doubles.py does)
```

**Test sentences.** WP-3 `"I need to schedule a service call. My AC isn't cooling."`; DANGER `"my mother is 88 and
it's 95 degrees in here"`; NODANGER `"my AC isn't cooling"`; WP-1 `"What does the Comfort Club membership actually
include?"`; WP-4F `"Yes, please."`; WP-7 `"I want a full refund on the repair. It didn't fix anything and I had to call
another company."`; WP-8 `"I want to cancel my Comfort Club membership."`; late technician (synthetic) `"The technician
was supposed to be here this morning and nobody has shown up."`; slot pick (WP-3 turn 2) `"This Saturday if possible, 4
to 7, after work."`.

**AC-8 seeds** (built at run time; never literals): `name_line = "Hi, my name is Omar Patel."`, customer ID
`"MHC-10002"`, invoice `"INV-204411"`, `seeded_phone()`, `seeded_card()`, `seeded_code()` (a prior chat line
`"customer"`: `f"the code is {seeded_code()}"`), plus `identity=IdentityState(status="located",
customer_id=CustomerId("MHC-10002"), masked_hint="the phone ending in 02", code_expires_at=None, tries_left=3,
codes_sent=1, verified_at=None)`.

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (names are binding)

Every node test calls the node function directly: `planner(state, runtime(ctx), deps=make_deps(gw))` with
`gw = ScriptedGateway({...})` and `ctx = make_ctx(TURN_1)`. Signals are captured with
`caplog.set_level(logging.INFO, logger="meridian.signal")` and read as
`[r.signal for r in caplog.records if r.name == "meridian.signal"]` (each a dict, `SignalRecord.model_dump(mode="json")`).

**`tests/unit/agent/nodes/test_plan.py`**
- `test_classifier_raise_only` — part 1, parametrised over the 9 (`label`, `verdict`) pairs of
  `("normal", "burning_unclear", "danger")²`: `raise_only(label, verdict) is (rank(label) > rank(verdict))`, with the
  expected booleans written out as a table in the test (True only for normal→burning_unclear, normal→danger,
  burning_unclear→danger read as verdict→label). Part 2: `rules_verdict` rows: `no_rules()` → `"normal"`;
  `burning_unclear=True` → `"burning_unclear"`; `danger_words=True` → `"danger"`; `safety=SafetyKind.CO` → `"danger"`.
  Part 3 (node): DANGER with a FREE_TEXT gate and classifier answer `danger` → `danger.raised is True`,
  `label == "danger"`, event `result == "raised"`, `codes == ("danger",)`; NODANGER + `normal` → `raised is False`,
  event `"pass"`, `codes == ("normal",)`; a gate with `danger_words=True` and answer `normal` → `label == "normal"`,
  `raised is False`.
- `test_classifier_failure_rules_stand` — parametrised `[ProviderFailureKind.BODY_ERROR, ProviderFailureKind.TIMEOUT]`:
  update `== {"danger": …, "check_events": (…,)}`; `danger == DangerAssessment(label="normal", raised=False,
  confidence=None, failure=<that failure>)`; one event `check == "classifier"`, `result == "fallback"`,
  `codes == ("fallback", kind.value)`; exactly one signal record, `name == "classifier_fallback"`, `cause == kind.value`,
  `node == "danger_classifier"`, `role == "classifier"`; exactly one `CLASSIFIER` call. Then `plan_join` on the merged
  state (planner `ok` WP-3 choices) returns a `plan` key.
- `test_invalid_classifier_label_rules_stand` — answer `{"danger_level": "maybe"}` → `failure.kind is INVALID_OUTPUT`,
  `label == "normal"`, `raised is False`, event `fallback`.
- `test_classifier_halt_writes_only_halt` — `halted(CLASSIFIER, DEADLINE)` → update `== {"halt": <that halt>}`; no signal.
- `test_planner_fallback_sdq6` — script: `PLANNER` → `failed(BODY_ERROR)`; `PLANNER_FALLBACK` → `ok(WP-3 choices)`.
  `[r for r, _ in gw.calls] == [Role.PLANNER, Role.PLANNER_FALLBACK]`; `gw.calls[0][1] == gw.calls[1][1]` (same request);
  outcome `fallback_used is True`, `model == SONNET_MODEL`, `probabilities is None`, `failure is None`,
  `choices.scheduling == "book_new"`; one signal `planner_fallback`, `cause == "body_error"`, `recovered is True`,
  `node == "planner"`, `role == "planner"`.
- `test_planner_halt_never_falls_back` — `PLANNER` → `halted(PLANNER, PROVIDER_SPEND_CAP)`: exactly one call
  (`PLANNER`); `set(update) == {"halt"}`; `update["halt"].reason is HaltReason.PROVIDER_SPEND_CAP`; no signal. Second
  case: Jev fails, fallback `halted(PLANNER_FALLBACK, DEADLINE)` → `set(update) == {"planner", "halt"}`,
  `planner.choices is None`, `fallback_used is False`, `failure.kind is BODY_ERROR`; no signal.
- `test_invalid_planner_answer_falls_back` — Jev `ok` with `topic` missing from the picks → one fallback call; the
  signal `cause == "invalid_output"`.
- `test_both_planners_fail_planner_failed_plan` (GRN-7 third pair) — Jev `failed(BODY_ERROR)`, fallback
  `failed(SERVER)`; text `"Can you help me?"`; no policy word, no open task: planner outcome `choices is None`,
  `failure.kind is SERVER`, `fallback_used is True`; signal `recovered is False`; then `plan_join` →
  `plan == Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)`.
- `test_both_planners_fail_open_task_continues` — same failures; text `"Yes, please."`; `tasks=(open_task("t-9",
  specialist="scheduling", intent=TaskIntent.RESCHEDULE),)`: `plan.source == "open_task"`, `planner_failed is False`,
  `mode == "act"`, `tasks == (PlannedTask(order=1, specialist="scheduling", intent=RESCHEDULE, needs_identity=True,
  resumes_task_id="t-9"),)`, `topic == "booking"`.
- `test_task_brake_halts_with_event` — `make_deps(gw, limits=Limits(brakes=Brakes(tasks_per_turn=2)))`; planner choices
  `account="invoice", scheduling="book_new", knowledge="yes"` (3 tasks): `set(update) == {"halt", "check_events"}`;
  `halt.reason is BRAKE_TASKS`, `halt.node == "plan_join"`; event `check == "brake"`, `result == "fired"`,
  `codes == ("brake_tasks", "plan_join")`; one signal `brake_fired`, `cause == "brake_tasks"`, `node == "plan_join"`.
- `test_plan_join_skips_on_halt` — state with `halt=Halt(reason=DEADLINE, node="planner", elapsed_ms=1)` → `{}`.
- `test_danger_raised_skips_brake` — the brake setup above plus `danger=DangerAssessment(label="danger", raised=True,
  failure=None)` → `{}`; no signal.
- `test_wp3_example_pair` (**WP-3 worked pair**, PA-1) — run `planner` and `danger_classifier` on the WP-3 sentence
  (`ok(PLANNER, choices(scheduling="book_new", topic="booking"))`, `ok(CLASSIFIER, {"danger_level": "normal"})`), merge
  their updates into the state with `state.model_copy(update=…)`, run `plan_join`: `danger.raised is False`; one
  `classifier` `pass` event; `plan == Plan(mode="act", tasks=(PlannedTask(order=1, specialist="scheduling",
  intent=TaskIntent.BOOK_NEW, needs_identity=True),), handoff_request=None, topic="booking", source="planner")`; exactly
  two calls, roles `{PLANNER, CLASSIFIER}`; no signal.
- `test_plan_nodes_write_only_own_keys` — collect the update of every path above (planner: ok, fallback, both fail,
  halt, fallback halt; classifier: ok, failure, halt; join: plan, brake, skip) and assert `set(u) <=
  PlannerUpdate.__required_keys__ | PlannerUpdate.__optional_keys__` (and the same for `DangerUpdate`, `PlanJoinUpdate`);
  and `({"planner", "halt"} & {"danger", "check_events", "halt"}) <= {"halt", "check_events"}` (the parallel branches
  share only reducer keys).
- `test_outcomes_carry_provenance_for_turn_trace` — Jev `ok` with `probabilities={"topic": {"booking": 0.9, "other":
  0.1}}` → `PlannerOutcome.probabilities` equal, `model == JEV_MODEL`, `fallback_used is False`, `failure is None`;
  classifier `ok` with `probabilities={"danger_level": {"normal": 0.97}}` → `confidence == 0.97`; a `PlannerTrace(
  model=o.model, fallback_used=o.fallback_used, failure=None, plan_mode=plan.mode, plan_source=plan.source,
  intents=tuple(t.intent for t in plan.tasks), handoff_request=plan.handoff_request, topic=plan.topic,
  planner_failed=plan.planner_failed)` validates; the fallback path's outcome has `probabilities is None` even when the
  fallback double returns probabilities; two classifier runs → two `classifier` events (one each).

**`tests/unit/agent/nodes/test_join_plan.py`** (pure; one test per AC-5 row plus plan-added rows; every test asserts
`topic`)
- `test_wp7_policy_word_wins` — WP-7 text, gate `free_text_gate(policy_trigger=HandoffReason.REFUND,
  rule_ids=("R24.refund",))`, planner `choices(topic="billing")` → `handoff_request is REFUND`, `tasks == ()`,
  `mode == "act"`, `source == "planner"`, `topic == "billing"`.
- `test_wp8_membership_cancel_reads_membership_then_knowledge` — `handoff="membership_cancel", topic="membership"` →
  intents `(READ_MEMBERSHIP, ANSWER_QUESTION)`, specialists `("account", "knowledge")`, orders `(1, 2)`,
  `needs_identity` `(True, False)`, `handoff_request is MEMBERSHIP_CANCEL`.
- `test_late_technician_maps_to_reason` — synthetic late sentence, `handoff="late_technician", topic="booking"` →
  `handoff_request is LATE_TECHNICIAN`, `tasks == ()`, `mode == "act"`.
- `test_unsupported_other_maps_to_unsupported_action` — `handoff="unsupported_other"` → `UNSUPPORTED_ACTION`.
- `test_reschedule_reads_appointments_itself` — `scheduling="reschedule", account="appointments"` → one task, scheduling
  `RESCHEDULE`, no account task.
- `test_yes_please_continues_open_task` — planner all none, `"Yes, please."`, open scheduling task `t-1` → `source ==
  "open_task"`, one task with `resumes_task_id == "t-1"`, `topic == <planner's topic>`.
- `test_slot_pick_continues_open_task` — WP-3 turn 2 sentence, open booking task (`intent=BOOK_NEW`) → continued.
- `test_yes_please_without_open_task_is_talk` (WP-4F) — `"Yes, please."`, no open task (or only `status="done"` ones),
  planner `choices(topic="booking")` → `Plan(mode="talk", tasks=(), handoff_request=None, topic="booking",
  source="planner")`.
- `test_tasks_ordered_account_scheduling_knowledge` — `account="invoice", scheduling="book_new", knowledge="yes"` →
  specialists `("account", "scheduling", "knowledge")`, orders `(1, 2, 3)`.
- `test_wp1_membership_question` — WP-1 turn 1, `knowledge="yes", topic="membership"` → `Plan(mode="act",
  tasks=(PlannedTask(order=1, specialist="knowledge", intent=ANSWER_QUESTION, needs_identity=False),),
  handoff_request=None, topic="membership", source="planner")`.
- `test_fallback_planner_source` — outcome with `fallback_used=True` and choices → `source == "fallback_planner"`.
- `test_task_brake_raises_before_plan` — 3 tasks with `tasks_per_turn=2` → `pytest.raises(TaskBrakeExceeded)`;
  `exc.count == 3`, `exc.limit == 2`; message contains no customer text.
- `test_choice_maps_cover_every_option` — `set(_ACCOUNT_INTENT) | {"none"}`, `set(_SCHEDULING_INTENT) | {"none"}`,
  `set(_HANDOFF_REASON)` equal `typing.get_args` of the matching `PlannerChoices` field; `set(_TOPIC_BY_INTENT) ==
  set(TaskIntent)` (import the private maps from the module; that is fine in tests).

**`tests/unit/agent/prompts/test_routing_prompts.py`**
- `test_requests_cross_only_planner_input` (AC-8) — state: latest text `f"{name_line} My number is {seeded_phone()}
  and my card is {seeded_card()}."`; chat lines (turn `TURN_0`): customer `"my customer number is MHC-10002"`, customer
  `"it's about INV-204411"`, customer `f"the code is {seeded_code()}"`; identity located with `MHC-10002`; WP-2-like
  open account task. Run `planner` (Jev `ok`) and `danger_classifier` (`failed(BODY_ERROR)`, so a signal exists) and a
  planner run whose Jev fails and fallback answers (a second signal). Captured planner request:
  `set(req.state) == {"latest_message", "recent_chat", "flags"}`, `set(req.state["flags"]) ==
  set(StateFlags.model_fields)`, each flag value is a `bool`, `int`, `str` or `None`. Classifier request:
  `set(req.state) == {"latest_message"}`. For each of `"Omar Patel"`, `"MHC-10002"`, `"INV-204411"`, `seeded_phone()`,
  `seeded_card()`, `seeded_code()`: absent from `req.model_dump_json()` of **both** requests, from every event's
  `model_dump_json()`, from every captured `record.signal` (as `json.dumps`) and from `caplog.text`. Present in the
  planner request dump: `"[name]"`, `"[phone]"`, `"[customer id]"`, `"[invoice id]"`.
- `test_choice_fields_match_consumer_types` (PA-2) — `[f.name for f in PLANNER_FIELDS] == ["knowledge", "account",
  "scheduling", "handoff", "topic"] == list(PlannerChoices.model_fields)`; for each field
  `tuple(f.options) == typing.get_args(PlannerChoices.model_fields[f.name].annotation)`;
  `tuple(CLASSIFIER_FIELDS[0].options) == typing.get_args(DangerAssessment.model_fields["label"].annotation)`;
  `CLASSIFIER_FIELDS[0].name == DANGER_FIELD`. (If `get_args` returns the alias for `topic`, unwrap with
  `typing.get_args(Topic)`.)
- `test_sp1_wording_kept` (PA-3) — `PLANNER_SYSTEM` and `CLASSIFIER_SYSTEM` equal the §4.5 strings (copy them into the
  test as expected constants); the SP-1 instructions and option descriptions of §4.5 rows marked SP-1 equal the table.
- `test_plan_modules_import_allowed_layers` (PA-7) — `ast` scan of `src/meridian/agent/nodes/plan.py` and
  `src/meridian/agent/prompts/routing.py` (paths from `Path(__file__).resolve().parents[4] / "src" / "meridian"`),
  splitting imports into module level and inside `if TYPE_CHECKING:` (copy the `_aea02_scan` pattern from
  `tests/unit/test_import_direction.py`; do not import from that file). Every imported module's top name is in
  `sys.stdlib_module_names | {"__future__"}` or `{"pydantic", "langgraph", "meridian"}`; run-time `meridian.*` imports
  start with an allowed prefix from §4.0 rule 2; `meridian.agent.gateway` appears **only** inside `TYPE_CHECKING`; none
  starts with `meridian.agent.routers`, `meridian.agent.graph`, `meridian.gates`, `meridian.services`,
  `meridian.adapters`, or is another `meridian.agent.nodes.*` module; print the import lists.
- `test_jev_leaves_wording_unchanged` (PA-8) — for `PLANNER_SYSTEM`, `CLASSIFIER_SYSTEM` and every `instructions` and
  option description in `PLANNER_FIELDS` and `CLASSIFIER_FIELDS` (35 strings; assert the count):
  `redact(s, RedactionProfile.JEV).text == s`. *The gateway JEV-redacts system, instructions and options again (§4.4);
  this proves the model receives exactly this wording.*

**`tests/unit/agent/prompts/test_routing_prompt_turns.py`**
- `test_stable_prefix_turns_1_2_5` (AC-9; context-management rules 3, 4, 5) — through the **real** gateway with a
  recording fake at the model port: `ans = ChoiceAnswer(choices=choices(scheduling="book_new", topic="booking"),
  probabilities=None)`; `fake = FakeChoiceModel([ans, ans, ans], model=JEV_MODEL)` (from `tests.fakes`);
  `gw, _d = build_gateway(planner=fake)` (from `tests.unit.agent._gateway_doubles`); `deps = make_deps(gw)`. Run
  `planner(state_n, runtime(make_ctx(turn_n)), deps=deps)` for the three turns below with the **same** `gw` (as in
  production). `fake.requests` then holds the three `ChoiceRequest`s exactly as the gateway sent them.
  - turn 1 (`TURN_1`): text `f"I need to schedule a service call. My AC isn't cooling. Call me on {seeded_phone()}."`;
    `chat_window` = that customer line only (current turn) → `req.state["recent_chat"] == []`.
  - turn 2 (`TURN_2`): text = the WP-3 slot-pick sentence; window = c1 (`TURN_1`), a1 (`TURN_1`), c2 (`TURN_2`,
    current) → `recent_chat == [f"customer: I need to schedule a service call. My AC isn't cooling. Call me on
    [phone].", "assistant: <a1 text>"]`.
  - turn 5 (`TURN_5`): text `f"Yes, still {seeded_phone()}."`; window = c1, a1 (`TURN_1`), c2, a2 (`TURN_2`), c3, a3
    (`TURN_3`), c4, a4 (`TURN_4`) + c5 (`TURN_5`, current) → `recent_chat` is exactly the last six earlier lines
    (c2 … a4); c1 and a1 absent; the `a3` entry (its text is 700 × `"x"`) has length 400 and ends with `"…"`.
  - Asserts: `len(fake.requests) == 3`; the three `req.system` equal each other and `== PLANNER_SYSTEM`;
    `sha256(json.dumps([f.model_dump() for f in req.fields], sort_keys=True).encode())` equal for all three and equal
    to the same hash over `PLANNER_FIELDS`; every `req.state["recent_chat"]` has `len ≤ 6` and every entry `len ≤ 400`;
    turn 1's and turn 5's `req.state["latest_message"]` contain `"[phone]"` and not `seeded_phone()`; turn 2's first
    `recent_chat` entry contains the same `"[phone]"` token (rule 5); print the three hashes.

**`tests/unit/agent/nodes/test_plan_graph.py`** (AC-11 part a; mock level; **not** a journey file, so no `journey`
marker). It uses AEA-21's real `build_graph`, `run_graph` and `ReplyComposer`. Every node except the three plan nodes is an
AEA-21 double (`tests/graph/_spine_doubles.install_doubles`). The planner and classifier talk to a **real**
`ModelGateway` from `tests.unit.agent._gateway_doubles.build_gateway`, with AEA-11 `FakeChoiceModel`s at the model port.
- Build (per test, a local helper `_run(monkeypatch, text, label) -> tuple[GraphOutcome, list[str], FakeChoiceModel,
  FakeChoiceModel, Doubles]`):
  1. `visits: list[str] = []`.
  2. Capture the real functions **before** installing doubles: `from meridian.agent.nodes import plan as plan_nodes`;
     `real = {"planner": plan_nodes.planner, "danger_classifier": plan_nodes.danger_classifier, "plan_join":
     plan_nodes.plan_join}`.
  3. `install_doubles(monkeypatch, visits, **real)`. `build_graph` reads `plan_nodes.planner` etc. at build time, so it
     must run after this.
  4. `planner_fake = FakeChoiceModel([ChoiceAnswer(choices=choices(scheduling="book_new", topic="booking"),
     probabilities=None)])`; `classifier_fake = FakeChoiceModel([ChoiceAnswer(choices={"danger_level": label},
     probabilities=None)])`.
  5. `gw, d = build_gateway(planner=planner_fake, classifier=classifier_fake)`; `deps = make_deps(gw)` (from
     `plan_fixtures`); `composer = ReplyComposer()`.
  6. `graph = build_graph(deps, checkpointer=InMemorySaver(), composer=composer)` (`InMemorySaver` from
     `langgraph.checkpoint.memory`).
  7. `turn_id = TURN_1`; `outcome = run_graph(graph, make_input(turn_id, text), make_ctx(turn_id), deps=deps,
     composer=composer)`.
- `test_danger_reaches_safety_by_classifier_raise`: DANGER, `label="danger"`.
  - Sees: `outcome.reply.blocks[0]` is an `EmergencyLineBlock` (`meridian.domain.blocks`);
    `outcome.reply.path == "danger"`; `outcome.reply.outcome == "safety_reply"`.
  - Stored (what `TurnService` persists): `outcome.turn_trace.gate_result == "danger"`;
    `outcome.turn_trace.danger_raised is True`. `outcome.check_events` holds exactly one `classifier` event, with
    `result == "raised"` and `codes == ("danger",)`.
  - Path: `"safety" in visits`; none of `"identity"`, `"run_specialist"`, `"responder"`, `"brief"`, `"handoff"` is in
    `visits`.
  - Model calls (CAP-2 at mock level): `len(planner_fake.requests) == 1`; `len(classifier_fake.requests) == 1`;
    `d.fallback.requests == []`; `d.responder.requests == []`; `d.specialist.requests == []`.
- `test_nodanger_routes_to_booking`: NODANGER, `label="normal"`.
  - Sees: exactly one `LocatePromptBlock` in `outcome.reply.blocks` (the booking's identity step: the task needs identity
    and `identity.status` is `"not_checked"`); no `EmergencyLineBlock`; `outcome.reply.outcome != "safety_reply"`.
  - Stored: `turn_trace.gate_result == "clear"`; `danger_raised is False`;
    `turn_trace.planner.intents == (TaskIntent.BOOK_NEW,)`; `turn_trace.planner.plan_source == "planner"`; exactly one
    `classifier` event, with `result == "pass"`.
  - Path: `"identity" in visits`; `"safety" not in visits`; `"handoff" not in visits` (no case).

**`tests/journeys/j5/test_aea_37.py`** (AC-11 part b; API level on AEA-57's harness). Model it on
`tests/journeys/j1/test_aea_57.py` and copy its call shapes. **Harness rules** (`tests/journeys/support/README.md`):
- `pytestmark = pytest.mark.journey`;
- never edit `tests/journeys/support/`;
- no `dependency_overrides`, no monkeypatch of `meridian`, no `TestClient`, no doubles above the model ports;
- every `/api` call names its `operation_id`;
- assert what the client sees **and** what was stored.

Module docstring (one triple-quoted string): `J-5 (slice plan section 0a), AEA-37 steps: DANGER reaches the safety path by
the classifier raise (two Jev routing calls, the emergency line first, one P1 case) and NODANGER books normally (locate
prompt, no case). API level on AEA-57's harness with the scripted model; the turn steps are reported blocked until
AEA-40, AEA-51 and AEA-29 bind their services.`

```python
from __future__ import annotations

import json
import uuid

import httpx
import pytest

from meridian.domain.common import Role
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J5 = "J-5"
SIGN_IN_NEEDS = ("login_sessions", "demo_clock")
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
TURN_NEEDS = (*CHAT_NEEDS, "turn_service", "run_graph")
DANGER_TURN_NEEDS = (*TURN_NEEDS, "handoff_service")
DANGER = "my mother is 88 and it's 95 degrees in here"
NODANGER = "my AC isn't cooling"
BOOK_RAW = '{"knowledge": "no", "account": "none", "scheduling": "book_new", "handoff": "none", "topic": "booking"}'
DANGER_RAW = '{"danger_level": "danger"}'
NORMAL_RAW = '{"danger_level": "normal"}'
RESPONDER_RAW = json.dumps({"text": "I can help book a visit for that. First I need to find your account."})
```

Helpers (module level, typed):
- `open_chat(journey: JourneyRun) -> tuple[JourneyClient, str]`:
  - `with journey.step(J5, "1 login", needs=SIGN_IN_NEEDS, operations=("login",)):` `signed = journey.login()`.
  - `with journey.step(J5, "2 start session", needs=CHAT_NEEDS, operations=("startChatSession",)):`
    `start = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")`; assert
    `start.status_code == 201`.
  - Return `(signed.client, start.json()["thread_id"])`.
- `submit(client: JourneyClient, thread_id: str, turn_id: str, text: str) -> httpx.Response`: copy J-1's `submit`
  (`operation_id="submitTurn"`, `body={"turn_id": turn_id, "payload": {"kind": "text", "text": text}}`).
- `classifier_events(journey: JourneyRun, turn_id: str) -> list[dict[str, Any]]`: `journey.db.rows("SELECT * FROM
  check_events WHERE turn_id = ? AND check_kind = 'classifier'", (turn_id,))` (add `from typing import Any`).

`test_j5_danger_raise_reaches_safety(journey: JourneyRun) -> None`:
1. `client, thread_id = open_chat(journey)`; `turn_id = str(uuid.uuid4())`.
2. `with journey.step(J5, "3 DANGER: classifier raise, emergency line first, P1 case", needs=DANGER_TURN_NEEDS,
   operations=("submitTurn",)):`
   - Script exactly two routing answers and nothing else: `journey.script.add(Role.PLANNER, BOOK_RAW)`;
     `journey.script.add(Role.CLASSIFIER, DANGER_RAW)`; `calls_before = len(journey.script.calls)`.
   - `r = submit(client, thread_id, turn_id, DANGER)`; `r.status_code == 200`.
   - What the user sees: `blocks = r.json()["blocks"]`; `blocks[0]["type"] == "emergency_line"`;
     `"locate_prompt" not in [x["type"] for x in blocks]`.
   - Model calls: `sorted(c.role.value for c in journey.script.calls[calls_before:]) == ["classifier", "planner"]`;
     `journey.script.problems() == ()`; `journey.script.remaining() == 0`;
     `journey.db.count("spend_ledger", "turn_id = ?", (turn_id,)) == 2`.
   - What was stored:
     - `turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))`; `turn["gate_result"] == "danger"`;
       `turn["danger_raised"] == 1`; `turn["outcome"] == "safety_reply"`; `turn["path"] == "danger"`.
     - `ev = classifier_events(journey, turn_id)`; `len(ev) == 1`; `ev[0]["result"] == "raised"`;
       `json.loads(ev[0]["codes"]) == ["danger"]`.
     - `journey.db.count("cases", "thread_id = ?", (thread_id,)) == 1`; `case = journey.db.one("SELECT * FROM cases WHERE
       thread_id = ?", (thread_id,))`; `case["reason"] == "danger"`; `case["priority"] == "P1"`;
       `case["handoff_trigger"] == "safety"`; `case["rule_id"] == "R47.classifier_danger"` (AEA-36 PA-4);
       `case["turn_id"] == turn_id`; `blocks[0]["case_reference"] == case["case_ref"]`.
   - Print one line: `step 3: block=emergency_line case=<case_ref> priority=P1 model_calls=2`.

`test_j5_nodanger_books_normally(journey: JourneyRun) -> None`:
1. `client, thread_id = open_chat(journey)`; `turn_id = str(uuid.uuid4())`.
2. `with journey.step(J5, "3 NODANGER: normal booking, no case", needs=TURN_NEEDS, operations=("submitTurn",)):`
   - Script: `journey.script.add(Role.PLANNER, BOOK_RAW)`; `journey.script.add(Role.CLASSIFIER, NORMAL_RAW)`;
     `journey.script.add(Role.RESPONDER, RESPONDER_RAW)`; `calls_before = len(journey.script.calls)`.
   - `r = submit(client, thread_id, turn_id, NODANGER)`; `r.status_code == 200`.
   - What the user sees: `types = [x["type"] for x in r.json()["blocks"]]`; `types.count("locate_prompt") == 1`;
     `"emergency_line" not in types`; `"safety" not in types`.
   - Model calls: `{c.role for c in journey.script.calls[calls_before:]} == {Role.PLANNER, Role.CLASSIFIER,
     Role.RESPONDER}`; `journey.script.problems() == ()`; `journey.script.remaining() == 0`.
   - What was stored: `turn["gate_result"] == "clear"`; `turn["danger_raised"] == 0`; `turn["plan_mode"] == "act"`;
     `turn["plan_source"] == "planner"`; `json.loads(turn["plan_intents"]) == ["book_new"]`;
     `turn["plan_topic"] == "booking"`; `turn["planner_failed"] == 0`. `ev = classifier_events(journey, turn_id)`:
     `len(ev) == 1`, `ev[0]["result"] == "pass"`, `json.loads(ev[0]["codes"]) == ["normal"]`.
     `journey.db.count("cases", "thread_id = ?", (thread_id,)) == 0`.
   - Print one line: `step 3: types=<types> intents=<plan_intents> cases=0`.

**How the blocked steps behave.** When a need is unbound, the harness skips the test at that step with
`blocked-on AEA-NN: …`. Later steps never run with unbound names. A blocked step never counts as a pass
(integrated-journeys §3 rule 1). Do **not** pass `--journeys-strict` in the ticket gate. Column names were checked on
`0a85270` (`turns`: `gate_result`, `path`, `outcome`, `plan_mode`, `plan_source`, `plan_intents`, `plan_topic`,
`planner_failed`, `danger_raised`; `check_events`: `check_kind`, `result`, `codes`; `cases`: `case_ref`, `reason`,
`priority`, `rule_id`, `handoff_trigger`, `turn_id`). Once the steps are unblocked, an assertion may fail because a
sibling stores a value differently from DO-4 or its plan (for example, `plan_intents` not stored as a JSON list, or
another `rule_id`). Treat that as a seam finding for AEA-51's merge. Do not loosen the assertion.

### 7.2 Existing tests that must stay green

`tests/unit/agent/**` (AEA-20's `test_gateway.py`, AEA-22's `tools/`, AEA-21's `test_{context,routers,signals}.py` and
`nodes/test_compose*.py`), `tests/graph/**` (AEA-21; they import `meridian.agent.graph`, which imports this module),
`tests/unit/test_import_direction.py`. **Known conflict (R-1, still open on `main` `dd1b110`):**
`tests/graph/test_spine.py::test_stubs_raise_loudly` is parametrised over all 14 stubs, including `(plan, "planner")`,
`(plan, "danger_classifier")` and `(plan, "plan_join")`; once this ticket replaces the stubs those three cases fail. Do
**not** edit that file. If R-1 is still not on `main` when you run G-4: check that the only failures are exactly those three
parametrised cases, quote them verbatim in your report, finish the remaining gates and **commit anyway** on your
branch (the merge waits for R-1, which the orchestrator applies). Any other red stops the commit.

### 7.3 Gates (cheapest first; stop at the first red; `export UV_LINK_MODE=hardlink`)

| # | Command | Passing looks like |
|---|---|---|
| G-1 | `uv run ruff format --check src/meridian/agent/nodes/plan.py src/meridian/agent/prompts/routing.py tests/unit/agent/nodes tests/unit/agent/prompts tests/journeys/j5/test_aea_37.py` | "N files already formatted" |
| G-2 | `uv run ruff check src/meridian/agent/nodes/plan.py src/meridian/agent/prompts/routing.py tests/unit/agent/nodes tests/unit/agent/prompts tests/journeys/j5/test_aea_37.py` | "All checks passed!" |
| G-3 | `uv run mypy src/meridian/agent tests/unit/agent tests/journeys/j5/test_aea_37.py` | "Success: no issues found" |
| G-4 | `uv run pytest tests/unit/agent tests/graph -q` (serial: AEA-21's timing test must not share CPUs) | all pass (see §7.2 for the one known conflict); report the count |
| G-5 | `uv run pytest tests/unit/agent/nodes/test_plan.py tests/unit/agent/nodes/test_join_plan.py tests/unit/agent/nodes/test_plan_graph.py tests/unit/agent/prompts -q -rA` | every non-journey test named in §7.1 listed as PASSED |
| G-6 | `uv run pytest -m journey tests/journeys/j5/test_aea_37.py -q -rs` | `2 skipped`, each reason `blocked-on AEA-NN: …` (quote both lines), or `2 passed` once every need is bound; never a failure or a collection error |
| G-7 | `uv run python -m tests.journeys.affected --base main` | selects every journey (a new file under `tests/journeys/` is an always-input, `ALWAYS_PREFIXES`), including `tests/journeys/j5/test_aea_37.py`; all selected pass or skip; report its summary lines |
| G-8 | `grep -rlE "meridian\.agent\.nodes\.plan\|agent\.nodes import .*plan\|meridian\.agent\.prompts\.routing\|meridian\.agent\.graph" tests/ \| sort` | on `0a85270` before this ticket: `tests/graph/_spine_doubles.py`, `tests/graph/test_spine.py`, `tests/unit/agent/test_routers.py`; after it, also this ticket's files under `tests/unit/agent/`. All of them are inside G-4's folders. Anything else: add it to G-4 and report it |
| G-9 | `grep -rnE "[0-9]{3}-[0-9]{3}-[0-9]{4}\|[0-9]{4} [0-9]{4} [0-9]{4}\|914276" src/meridian/agent/nodes/plan.py src/meridian/agent/prompts/routing.py tests/unit/agent/nodes tests/unit/agent/prompts tests/journeys/j5/test_aea_37.py` | no output (no literal phone, card or code; `tests/unit/agent/nodes` covers `test_plan_graph.py`) |

The full suite is **not** run: this ticket changes no shared fixture, settings, dependency or widely imported module
(`build-loop-test-scope.md`).

### 7.4 Journey record (AC-11): `docs/testing/journeys/<YYYY-MM-DD>-AEA-37.md`

Title `# Journey record: AEA-37 plan node`, then a `| Field | Value |` table in the shape of
`docs/testing/journeys/2026-10-21-AEA-20.md`:

| Field | Value |
|---|---|
| Claim | AEA-37 AC-11: on a free-text turn the raise-only classifier sends DANGER to the safety path and NODANGER to a normal booking (J-5), with exactly the two Jev routing calls (graph run with node doubles, `test_plan_graph.py`); GRN-7 and the SDQ-6 fallback behave as graph-nodes §4–§5 (unit tests). The J-5 steps on AEA-57's harness (`tests/journeys/j5/test_aea_37.py`) are written and reported blocked |
| Level | `mock-tested` |
| Tested revision | the feature commit SHA |
| Environment | VPS worktree, `uv run`, Python 3.12. Graph run: LangGraph 1.2.16 `InMemorySaver`, AEA-21 node doubles for every node but the three plan nodes, real `ModelGateway` with AEA-11 `FakeChoiceModel`s, no server, DB or provider. Journey: AEA-57 harness (real app under uvicorn on loopback, disposable DB copy, scripted raw model output), steps blocked before the turn |
| Command | G-5 and G-6 verbatim; G-7 |
| Result | counts per command; G-6's two skip reasons quoted verbatim |
| Evidence location | this record |
| Remaining limitations | the graph run uses doubles for the gate and safety nodes (AEA-36) and the case write (AEA-29); the J-5 steps that check the P1 case row, the stored turn and event rows and the two-call spend ledger are blocked; CAP-2 spans are AEA-51's; E-5 is scored at Stage 9 |
| Blocked by | the owners named in G-6's skip reasons (expected among AEA-30, AEA-40, AEA-51, AEA-29), and AEA-51 for J-5 at the CON-2 entry point (graph wiring) |
| Journeys that will exercise this code | J-5 (`tests/journeys/j5/test_aea_37.py`, this ticket; AEA-36's and AEA-51's J-5 files), and every journey with a free-text turn (J-1 step 5, J-2…J-4, J-9) once AEA-51 binds `run_graph` |

### 7.5 Evidence to report back

G-1…G-9 output lines; the three AC-9 hashes; G-6's two skip reasons verbatim; the journey record path and both commit SHAs; whether R-1 was already on
`main` (if not, the three failing case ids verbatim); any name in §4.1–§4.4 or §6 that differed on `main` (if any, you
should have stopped).

---

## 8. Risks and requests

### 8.1 Plan decisions (engineering; each reversible; reported for AEA-08's next reconcile)

| ID | Decision | Basis |
|---|---|---|
| PD-1 | `PlannerOutcome.failure` is the failure that left `choices` empty (Sonnet's when both fail; `None` when the fallback recovered); the Jev failure kind of a fallback is in the `planner_fallback` signal's `cause` | Keeps `choices is None ⇔ failure is not None`, which GRN-7's join reads; graph-nodes §4 puts the Jev kind in the signal |
| PD-2 | `join_plan` gains a keyword-only `tasks_per_turn` (default `Brakes().tasks_per_turn`) and raises `TaskBrakeExceeded` before building `Plan` | DO-4's `join_plan` has no limits argument; `Plan.tasks` `max_length=3` would raise a validation error first; every DO-4 call stays valid |
| PD-3 | `recent_chat` drops the current turn's own lines; each line is `"<speaker>: <text>"`, JEV-redacted, then cut to 400 chars with `"…"` | graph-core §7 (newest message sent separately); redact-then-cut never leaves an unmasked fragment |
| PD-4 | `ChoiceRequest.state` = `PlannerInput.model_dump(mode="json")` (keys `latest_message`, `recent_chat`, `flags`); classifier state `{"latest_message": …}` | DO-4 §3 "only `PlannerInput`"; AEA-18's adapter puts `instructions` first and copies the other keys |
| PD-5 | A continued open task gets `needs_identity = specialist != "knowledge"` | R-14: a private task needs identity; AEA-21 PD-4 uses `status == "waiting_identity"` for card choices — both are safe (the dispatch guard refuses an unverified write); see R-7 |
| PD-6 | Topic when the planner failed: the continued task's topic (`_TOPIC_BY_INTENT`), else `"other"` | GRN-7 fixes `"other"` for the failed plan; M-3 is an estimate |
| PD-7 | `mode = "act"` when the plan has tasks, a `handoff_request` or `planner_failed`; else `"talk"` | SP-1 `Decision.acts`; GRN-7 fixes `"act"` for the failed plan; AEA-21 PD-1 routes tasks-less handoffs either way |

| PD-8 | SP-1's third continuation trigger ("not verified and a phone in the text") is **not** carried over; only an affirmative or a slot pick continues an open task | DO-4 §4 names only "a bare 'Yes, please.' or a slot pick"; production identity is the locate form card (`GateKind.LOCATE` in AEA-12's `decide_gate`), not a phone typed as free text |
| PD-9 | The planner's "state summary" (PRD R-45) is `StateFlags`: flags only, no prose summary | DO-4 §3 ("What crosses this line: only `PlannerInput`"); answers AEA-34's R-3 for the planner side (the responder side is AEA-38) |

### 8.2 Requests to the orchestrator

- **R-1 (AEA-21's test; still open on `main` `dd1b110`; one fix serves AEA-34, 36, 37, 38, 39; apply it once when
  that wave-2 node group merges by the tree):**
  `tests/graph/test_spine.py::test_stubs_raise_loudly` must check only functions that are still stubs (e.g.
  `pytest.skip` a case whose `inspect.getsource(fn)` does not contain `"stub from AEA-21"`). Otherwise every wave-2
  node ticket (AEA-34, 36, 37, 38, 39) turns its cases red and would have to edit AEA-21's file — a five-way collision.
  This ticket does not edit it (§7.2).
- **R-2 (AEA-02b):** when `ConversationState` gains `pending_change`, switch `StateFlags.pending_change` to
  `state.pending_change is not None` (one line in `build_planner_input`; R-5).
- **R-3 (AEA-08):** record PD-1…PD-9 in DO-4 §4 / graph-nodes §9.4 (`tasks_per_turn` keyword, `TaskBrakeExceeded`, the
  `recent_chat` line format, PD-8, PD-9) at the next reconcile.

### 8.3 Collisions with sibling tickets

| Surface | Sibling | Handling |
|---|---|---|
| `src/meridian/agent/nodes/plan.py` | AEA-21 creates the stub | replaced in place; same names and signatures (`build_graph` reads them by name) |
| `tests/graph/test_spine.py` | AEA-21 | read only; R-1 |
| `tests/unit/agent/nodes/__init__.py`, `tests/unit/agent/prompts/__init__.py` | AEA-21, 34, 35, 36, 38, 39 | identical empty files merge cleanly |
| `tests/unit/agent/nodes/` | AEA-21 (`compose_fixtures.py`, `test_compose*.py`), AEA-34/36/38/39 (their `test_<module>.py`) | this ticket's files are `plan_fixtures.py`, `test_plan.py`, `test_join_plan.py` only; no `conftest.py` |
| `tests/journeys/j5/` | AEA-36 (`test_aea_36.py`), AEA-51 (its J-5 file) | one file per ticket (`test_aea_37.py`); `__init__.py` exists; no shared helper |
| `.claude/reference/area-map.md` A7d Status cell | AEA-36 shares the row | step 12 merges either order; expect a trivial text conflict |
| `docs/design/code-design.md` `**Built:**` line, `icm-progress.md` row | every ticket | append / replace own text only; trivial conflicts expected |

### 8.4 Other risks

- **R-4 — the task brake is unreachable at the shipped limit.** Three single-choice fields (account, scheduling,
  knowledge) produce at most three tasks, and the limit is three. AC-6 is therefore proven with the limit lowered to 2
  in the test's `Limits`; the brake guards a future fourth field or a lowered limit. No product decision.
- **R-5 — `pending_change` read from `settled`.** Until AEA-02b adds the state key, the flag comes from
  `Settled.current_visit().change_request` (DB authority). Same meaning (an open change request keeps the original
  visit, graph-core §14).
- **R-6 — fallback halted.** If the Sonnet fallback returns a halt (`DEADLINE`, Anthropic `PROVIDER_SPEND_CAP`), the
  node writes the Jev failure outcome plus the halt and no `planner_fallback` signal; the halt has its own signal
  outside the nodes (DO-4 §11).
- **R-7 — two resume rules.** AEA-21's card-choice resume (PD-4 there) and this ticket's text resume set
  `needs_identity` differently; both stay safe through the R-14 dispatch guard. Raised for AEA-08 to pick one rule.
- **R-8 — follow-up word lists.** SP-1's `is_affirmative` / `mentions_slot_pick` patterns have no home in `gates/`, so
  they are private constants here. If AEA-05 later owns them, this file imports them instead (a two-line change).
- **R-9 — router order.** AEA-21 runs `halt_route` before `danger raised`; a planner halt on a turn whose classifier
  raised would reach `compose` before `safety`. Practically unreachable (the planner is the turn's first model call,
  3 s cap, and an OpenRouter cap halts the classifier too); PA-6 removes the one in-ticket path (the brake). Noted for
  AEA-21 / AEA-08, not changed here.
- **Sibling shape drift:** if `main`'s `domain/*`, `ports/models.py`, `agent/gateway.py`, `agent/context.py`,
  `agent/signals.py`, `tests/graph/_spine_doubles.py`, `tests/unit/agent/_gateway_doubles.py` or `tests/fakes/*`
  differ from §4 / §6 / §7.1 in a name this plan uses, stop and report. AEA-21 is merged; its plan §6 fixed
  the helper names (`RecordingSink`, `make_deps`, `make_ctx`, `make_input`, `install_doubles`, `no_rules`, `THREAD`,
  `REQ`, `DEMO_NOW`) as a contract with this ticket.
- **R-10 — tests reuse other tickets' test helpers.** AC-9 and `test_plan_graph.py` import AEA-20's
  `tests/unit/agent/_gateway_doubles.py` (`build_gateway`) and AEA-21's `tests/graph/_spine_doubles.py`, read only. A
  rename breaks these tests at import (loud, not silent). The J-5 journey file uses only AEA-57's public harness
  (`journey` fixture, `JourneyRun`, `JourneyClient`), read only.
- **Sentinels:** the phone, card and code exist only at run time in tests (§6); G-9 proves no literal.

---

## 9. Readiness

**READY**, no blocker. No product decision is open: DAT-1 stands on option A per sign-off D-14, and GRN-7 and SDQ-6 are
decided. Every engineering gap is decided in §8.1 and reported. No signed contract changes.
- The slice-plan blockers are all on `main`: AEA-11 (`FakeChoiceModel`, `provider_call`, used in tests), AEA-12
  (`decide_gate`; not imported, because the tests build `GateDecision` directly) and AEA-21 (`5531664`: `GraphDeps`,
  `emit_signal`, the `plan.py` stub, `build_graph` / `run_graph` / `ReplyComposer`, `tests/graph/_spine_doubles.py`).
- Also on `main` and imported: AEA-02 (types, ports), AEA-04 (`redact`), AEA-01 (`Limits`), AEA-20 (`ModelOutcome`;
  `build_gateway` in tests), AEA-57 (journey harness).
- The J-5 journey steps need AEA-40, AEA-51 and AEA-29 to bind their services. Until then they are reported *blocked*,
  which the harness and `integrated-journeys.md` §4 allow. They are not a blocker for this ticket.
- **R-1** must be applied by the orchestrator (one guard in `tests/graph/test_spine.py`) before this ticket's merge gate
  can be green. Under tree merging it is applied once for the wave-2 node group (AEA-34, 36, 37, 38, 39). The
  implementer commits on its branch either way (§7.2).
- The worktree's uncommitted earlier run is kept and finished (§5 step 0); nothing is rewritten from scratch.

**Gates:** none (no human, paid or live gate). No security review (not `risk::security`).
