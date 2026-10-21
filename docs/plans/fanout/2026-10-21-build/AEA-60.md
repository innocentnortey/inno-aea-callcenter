# Plan — [AEA-60] contract: prompt ↔ consumer checks (rendered prompts vs parsers, ToolDefs and schemas)

**Status: BUILT AND MERGED.** Code commit `5f7725b`, merge `0e37fad`, ledger `84d826f` (row: `merged`). Do **not**
dispatch an implementer to rebuild it. The one step left (step 14, section 5a below) is **blocked on AEA-51** and only
upgrades AC-13's evidence level; AC-13 is already met as written (its evidence clause allows `mock-tested` + *Blocked by*
AEA-57, AEA-51 until those land).
**Issue:** GitLab `innocentnortey/inno-aea-callcenter#60` (copy: `docs/plans/tickets/AEA-60.md`) · **Base revision:** `main` `dbcd8b7` (refresh 1)
**Lane / risk:** `lane::build-loop`, no `risk::security` (tests only). Plan → implement (code and tests together) → affected tests → `code-review-agent`.
**Planner model:** claude-opus-5-5. **Implementer:** Sonnet.

**Refresh 1 (2026-10-21, `main` at `dbcd8b7`).** Read this box first. Where it and anything below differ, this box wins.
Sections 1–8 and *Deviations* are kept unchanged as the record of what was planned and built.

1. **What is on `main`** (from `git show --stat 5f7725b`): `tests/contract/test_prompts_vs_consumers.py` (448 lines),
   `tests/contract/_prompts_render.py`, `_prompts_checks.py`, `_prompts_malformed.py`, `_prompts_expect.py`,
   `_prompts_drift.py` (the last two are implementer deviations, see *Deviations*), `tests/journeys/j5/test_aea_60.py`,
   `tests/journeys/j9/test_aea_60.py`, `docs/testing/journeys/2026-10-21-AEA-60.md`, `docs/design/code-design.md` §9 line,
   `.claude/state/icm-progress.md` line 60. Steps 0–13 of section 5 are **done**.
2. **Result as recorded** (evidence record and ledger; numbers from the implementer's and merge agent's runs, not re-run by
   this planner): contract module 104 passed, 0 skipped, 0 xfailed; the three journey tests skipped, each
   `blocked-on AEA-51: reply_composer not bound`; ruff, format and mypy clean. The wave-3 seam audit at `0e37fad`
   (`.claude/state/resume.md`, *Stage 8: wave 3 context upkeep, AEA-60*) reports "Prompts vs consumers pass" and no
   AEA-60 finding.
3. **Nothing it depends on has moved.** `git diff --stat 0e37fad..dbcd8b7 -- src tests/journeys/support
   tests/journeys/j5/test_aea_37.py tests/unit/agent tests/contract tests/fakes tests/fixtures` is empty; the commits since
   the merge are the ledger, the context upkeep and FU-j1-demo-state (J-1 only).
4. **The journey legs will run, not skip forever, once AEA-51 lands.** Every name in their `needs` is a real container key
   (`web/deps.py` lines 77–78 `Key("handoff_service")`, `Key("case_service")`; `web/container.py` lines 767, 770
   `Key("run_graph")`, `Key("reply_composer")`), and `tests/journeys/support/steps.py` `missing_needs` raises `KeyError` on
   an unknown name, so the recorded skips prove the names resolve. The schema columns the legs read exist
   (`src/meridian/adapters/sqlite/schema/00_core.sql`: `degrade_reason` line 53, `plan_intents` 59, `planner_failed` 62,
   `danger_raised` 63; `check_events.check_kind` 106, `result` 108, `codes` 111).
5. **AEA-51 already runs these legs.** Its plan (`AEA-51.md`, refresh 6 item 4 and §8 R-23) binds `run_graph` in its pass
   2a and names `j5/test_aea_60.py` and `j9/test_aea_60.py` among the sibling tests that must pass at its check 8; a red
   one whose cause is in a sibling's code is reported `blocked-on <owner>`, never skipped. AEA-51's branch
   `aea-51-aea-51-customer-path` (`e9d07f3`, pass 1) touches no AEA-60 file (`git diff --stat main...e9d07f3 --
   tests/journeys tests/contract src/meridian/agent/prompts src/meridian/agent/nodes` adds only
   `tests/contract/test_model_ports_contract.py`).

## 5a. Remaining step (refresh 1)

**Step 14 — upgrade AC-13's evidence after AEA-51 merges.** Start only when the ledger row for AEA-51 reads `merged`.
Branch from `main` (`aea-60-f1-journey-level` or the orchestrator's name), `export UV_LINK_MODE=hardlink`, no venv copy.

1. Run `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py -rs`.
2. **All three pass** (`test_j5_malformed_classifier_reply_books_normally`, `test_j9_both_planners_malformed_hand_off_degraded`,
   `test_j9_malformed_responder_draft_falls_back`): edit only these two docs.
   - `docs/testing/journeys/2026-10-21-AEA-60.md`: replace the *Level* field's journey half with `integrated with a scripted
     model` (the contract module stays `mock-tested`); *Tested revision* = the `main` commit you ran on; *Command* unchanged;
     *Result* = the pass counts from step 1 plus the contract module's count from
     `uv run pytest tests/contract/test_prompts_vs_consumers.py -q` (expect 104 passed); *Blocked by* = `none`. Keep *Claim*
     and *Remaining limitations* (C-1, C-2, no live model: AEA-61).
   - `.claude/state/icm-progress.md` line 60 (the AEA-60 row): replace `J-5/J-9 test_aea_60.py blocked-on AEA-51` with
     `J-5/J-9 test_aea_60.py 3 passed (integrated, scripted model)`. Replace in place; add no row.
   This is docs only (nothing code or tests read), so the orchestrator may do it as `lane::direct` (`ticket-lanes.md`):
   one agent, no worktree, commit straight to the working branch between merges.
3. **A leg is red.** Run it alone with `-x -rs`. Then:
   - If the leg's own expectation contradicts the signed contract (DO-4 §10 failure offer and handoff block; graph-nodes §4
     signal table; cases.md §3.4 rule 6, `ai_failure` P3; web.md §9–§10), fix only that leg in
     `tests/journeys/j5/test_aea_60.py` or `tests/journeys/j9/test_aea_60.py`, citing the contract line in the commit
     body. This is `lane::build-loop` (a `fanout-implementer` with this plan).
   - If the product code contradicts the contract, leave the leg red, do not edit it, and report `blocked-on <owner>` with
     the failing assertion line on #60 and on the owner's issue (graph wiring, turn service, composer → AEA-51; act node,
     escalation → AEA-39; reply nodes → AEA-38; plan nodes → AEA-37; case and handoff services → AEA-29).
   - A missing harness capability (raw bodies, `stop_reason`, a `NEED_OWNERS` entry) is a follow-up on AEA-57, never an
     edit to `tests/journeys/support/`.
   - Known: J-9(a)'s brief raw quotes `message_id: 1`; if that is not the customer's message id, `check_quotes` trims the
     quote and nothing the leg asserts changes (R-2). Do not "fix" it.
4. Checks before the commit (cheapest first): if a leg changed, `uv run ruff check` and `uv run ruff format --check` on
   the changed leg, then `uv run mypy` on it; then step 1's command (all pass); then
   `uv run python -m tests.journeys.affected --base main --list-only` and confirm both legs are listed. No full suite
   (docs and journey files only; nothing shared changed). `pytest -n 2` at most if you parallelise. Do not bind ports 4019
   or 5184 (the harness picks its own).
5. Commit with explicit paths (`git add docs/testing/journeys/2026-10-21-AEA-60.md .claude/state/icm-progress.md` plus any
   changed leg), never `-A`; message `docs(AEA-60): J-5/J-9 legs at integrated level after AEA-51` (or `test(AEA-60): …`
   when a leg changed); last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push; the merge step
   pushes `main`.

**Must not do in step 14:** re-create or edit any `tests/contract/_prompts_*.py` or `test_prompts_vs_consumers.py`
(they pass on `main`); edit `src/`, `agent/prompts/`, `tests/journeys/support/`, `tests/journeys/j5/test_aea_37.py` or any
other ticket's file; add `skip`/`xfail`/`live`; put a phone, card-like number, code or real name anywhere.

---

## 1. Goal and sources

**Goal (ticket "What to build").** One default-suite contract module, `tests/contract/test_prompts_vs_consumers.py`, that
(1) renders every prompt the graph sends through the real builders and nodes on turns 1, 2 and 5 of one fixture
conversation, (2) compares what each prompt offers the model with what its consumer accepts, in both directions,
(3) feeds malformed and unsupported provider output through the real adapters (stubbed HTTP), the real `ModelGateway` and
the real node / runner / dispatcher and asserts the documented fallback, and (4) proves each check fails on a drifted copy.
Plus two journey files that extend J-5 and J-9 through CON-2 with the scripted model. It writes no product code.

**Worked pairs (the ticket's WP-N pair, named so the reviewer can find them):**
- *Example pair 1 (drift caught)*: `test_routing_fields_match_planner_choices_and_danger_label` (pass on today's
  `routing.py`) and `test_check_fails_on_drift[planner-handoff-added]` (adding `cancel_membership` fails with
  `routing.planner.handoff offers 'cancel_membership'; PlannerChoices.handoff does not accept it`).
- *Example pair 2 (malformed answer)*: `test_malformed_routing_outputs[e1-classifier-emergency]` (NODANGER, Jev body
  `{"danger_level": "emergency"}` → `DangerAssessment(label="normal", raised=False, failure=invalid_output)`, one
  `classifier` event `fallback` with codes `("fallback", "invalid_output")`, one `classifier_fallback` signal, the turn
  continues to `plan_join` and books).

**Sources (all read for this plan):**
- Ticket `docs/plans/tickets/AEA-60.md` (AC-1…AC-15), slice plan `docs/plans/slice-plan.md` §0a (Amendment 1, journey map
  J-5, J-9), §1 row AEA-60, §3 collision map rows `tests/contract/` (prompt and OpenAPI files) and `tests/journeys/`.
- Rules: `.claude/rules/integrated-journeys.md` §3 rules 4–6, §4 (levels, evidence record fields), §5, §6;
  `.claude/rules/build-loop-test-scope.md` incl. *AEA addition*.
- DO-4 `docs/design/contracts/internal-components.md` §0 ("Errors never carry values"), §4, §5, §7, §9, §11, §12; addenda
  `docs/design/contracts/stage7/models.md` §1, §3, §5 (the gateway's `model_call(…, masked_input, masked_output)` per
  attempt, MOD-10), `graph-tools.md` §1, §2 (PD-9 `report_facts` schema untrimmed), `graph-nodes.md` §1, §4 (signal table),
  §5 (GRN-7), §9.4–§9.6, `cases.md` §3.4 rule 6, `data.md` §5 (DAT-2), §8a (`FixedClock`).
- Decisions: `docs/plans/stage7-signoff.md` D-14 (CAS-16 option A → `HandoffReason.BURNING_RULED_OUT` exists in code;
  DAT-2 option B → held-out keys outside the repo, `/home/linuxuser/.meridian-sealed/heldout/`).
- Current code on `main` (`b68df7e`): every module listed in section 4.

## 2. Boundary

**Owned files (the only files the implementer creates or edits):**

| File | Action | Purpose |
|---|---|---|
| `tests/contract/test_prompts_vs_consumers.py` | create | the 12 test functions named in section 7 (thin; ≤ 500 lines) |
| `tests/contract/_prompts_render.py` | create | private helper: ids/ctx, `RecordingGateway`, the fixture conversation, render functions, offered sets, inventory (≤ 500 lines) |
| `tests/contract/_prompts_checks.py` | create | private helper: `Drift`, every comparison helper, the code-only set, the held-out/socket guard (≤ 500 lines) |
| `tests/contract/_prompts_malformed.py` | create | private helper: real adapters on stubbed transports, gateway builder, raw bodies, case runners, `CaseRun` records (≤ 500 lines) |
| `tests/journeys/j5/test_aea_60.py` | create | AC-13 J-5 leg |
| `tests/journeys/j9/test_aea_60.py` | create | AC-13 J-9 legs (a) and (b) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-60.md` | create | evidence record (date = the day you write it, `date +%F`) |
| `docs/design/code-design.md` | modify | §9 tree `contract/` entry and the "Built on `main`" line only (AC-15) |
| `.claude/state/icm-progress.md` | modify | append one *Routes verified against code and tests* row (append-style) |

The three `_prompts_*.py` helpers are a plan decision: the project keeps files under a 500-line cap (AEA-17 and AEA-40
split files for it) and the ticket's content will not fit in one module. They follow AEA-17's precedent of a private
`tests/contract/_anthropic_fixtures.py`. No other ticket names these paths (collision map §3).

**Shared surfaces, read only (import, never edit):** everything under `src/meridian/`; `tests/fakes/`;
`tests/fixtures/sqlite.py`; `tests/unit/agent/_gateway_doubles.py`; `tests/unit/agent/nodes/plan_fixtures.py`;
`tests/unit/agent/nodes/reply_fixtures.py`; `tests/unit/agent/specialists/_doubles.py`;
`tests/contract/_anthropic_fixtures.py`; `tests/journeys/support/**`; `tests/conftest.py`.

**Never touch:** `src/**` (a mismatch you find is a defect on the owning ticket; leave the test red and report it),
`agent/prompts/*.py` (AC-11 drifts are monkeypatched copies), other tickets' tests and helpers, `tests/journeys/support/`
(a missing harness capability is a follow-up on AEA-57), `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `apps/web/**`,
`docs/ux/**`, the OpenAPI / `UI_CONTRACTS.md`, the briefing, `docs/data/issued/**`, `docs/archive/`, `docs/parked/`,
`.claude/reference/area-map.md` (no area row owns `tests/contract/`; say so in the MR), `eval/cases/heldout/`.

## 3. Requirements table

| Req | What (ticket AC, short) | How it is implemented | Verified by |
|---|---|---|---|
| AC-1 | Every `Role` and `SPECS` kind has a rendered case through its real builder on turns 1, 2, 5; offered sets identical on the three turns; a missing role/kind fails by name | `_prompts_render.RENDERERS` maps every role value and `specialist:<kind>` to a render function that drives the real node/runner with `RecordingGateway`; `_prompts_checks.missing_cases(names, renderers)`; `offered_set(role, request)` compared across turns | `::test_every_role_and_spec_has_a_rendered_case` (one param per role and kind, plus the extra-name bite `["triage"]`) |
| AC-2 | Planner field names = `PlannerChoices` fields; option keys = `Literal` set both ways (incl. `late_technician`), ≤ 255 each; fallback request = planner request; classifier offers exactly `normal, burning_unclear, danger` = `DangerAssessment.label`; quoted option keys in system/instructions exist in the request | `check_choice_fields(role, request, consumer_model)`, `check_quoted_keys(role, request)` in `_prompts_checks` | `::test_routing_fields_match_planner_choices_and_danger_label` |
| AC-3 | Every offered planner value has a consumer path through `join_plan`, `HandoffReason` mapping, `priority_for`, `decide_escalation`, `SPECS`, `Plan.topic` | parametrised over every (field, option) of the rendered planner request | `::test_join_plan_accepts_every_offered_value` |
| AC-4 | No prompt offers a code-only value; no tool/report/output field lets the model set priority, case reference, promise or customer id | `CODE_ONLY` set ∩ offered handoff-bearing sets = ∅; `FORBIDDEN_FIELDS` ∩ property names of every sent schema = ∅ (see clarification C-1) | `::test_no_prompt_offers_a_code_only_value` |
| AC-5 | Specialist tools = `dispatcher.schemas(spec.tool_kinds)` + `report_facts`; names resolve, match `[a-z_]{1,64}`, kind ∈ `spec.tool_kinds`; no registry name `report_facts`; `check_covers` passes; schema = trimmed `args_model` schema, `strict=True`, no `ToolCallScope` field; `report_facts` schema = `spec.report_model.model_json_schema()`; tool names in the wording are sent | `check_specialist_request(kind, request, registry, task)` | `::test_specialist_tools_match_registry_and_report_models` (per kind) |
| AC-6 | Responder `output_model is ResponderDraft`, schema sent = trimmed schema (`text` 1–1200, no promise/reference), both labelled blocks present; brief `output_model is BriefExtraction`; brief message ids rendered = keys of `shown` given to `check_quotes` (customer messages only), byte-identical text | `check_responder_request(request)`, `check_brief_ids(rendered, shown, customer_ids)`; `check_quotes` wrapped (spy) via `monkeypatch.setattr(reply, "check_quotes", spy)` | `::test_reply_schemas_and_brief_message_ids_match_checks` (WP-7 refund turn) |
| AC-7 | Malformed routing outputs (a–e) → documented fallback | `run_routing_case(case_id, caplog)` in `_prompts_malformed` | `::test_malformed_routing_outputs` (7 params) |
| AC-8 | Malformed specialist outputs through the real dispatcher and runner; step failures at the act node → `specialist_failed` + rule 6 | `run_specialist_case`, `run_act_case` | `::test_malformed_specialist_outputs` (11 params; 3 go through the act node, step 9) |
| AC-9 | Malformed reply outputs (responder, brief, quotes) → documented fallback | `run_reply_case`, `run_brief_case` | `::test_malformed_reply_outputs` (11 params) |
| AC-10 | Markers never appear in failures, call records, signals, check events, tool errors, tool records, lookup rows, logs, trace spans (clarification C-2), stored brief | substring search over the `CaseRun` of four marker cases | `::test_rejected_values_absent_from_records` |
| AC-11 | Six drifted copies fail with role, field, value | `monkeypatch` copies + `pytest.raises(Drift, match=…)` on the same helpers AC-2/5/6 use | `::test_check_fails_on_drift` (6 params); `git diff --stat src/` empty |
| AC-12 | Dev data only; no held-out open; no socket | `sys.addaudithook` guard (installed once, switched on by a module-scoped autouse fixture) | `::test_no_heldout_reads_and_no_network` + module teardown assertion |
| AC-13 | J-5 and J-9 through CON-2 with raw provider bodies | two journey files on AEA-57's harness (`journey.step(..., needs=...)`; blocked steps are reported `blocked-on`, never passed) | `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py -rs` |
| AC-14 | Every malformed case leaves its WF-1 records, codes only | assertions over `CaseRun` per case of AC-7…AC-9 | `::test_malformed_cases_leave_their_records` (29 params) |
| AC-15 | Docs in the same change | section 5 step 12 | `git diff --name-only` |

**Clarifications this plan makes (engineering, within the signed contracts; the orchestrator posts them on issue #60 as a comment):**
- **C-1 (AC-4 vs AC-2).** AC-4's code-only list includes `danger` and `burning_unclear`, which are also the classifier's
  `danger_level` options that AC-2 requires. The code-only list is a list of `HandoffReason` values ("values only code may
  set", DO-4 §7). The classifier's options feed `DangerAssessment.label` (raise-only, R-47), never `HandoffReason`. So AC-4
  is checked against every **handoff-bearing** offered set: all five planner fields (and the identical `planner_fallback`
  request), every specialist tool and `report_facts` enum value, and the responder/brief output schemas. The classifier's
  `danger_level` set is exempt, and the test asserts that exemption by name (`EXEMPT = {("classifier", "danger_level")}`).
  `CODE_ONLY` includes `burning_ruled_out` (CAS-16 option A, D-14; `HandoffReason.BURNING_RULED_OUT` is on `main`).
- **C-2 (AC-10 vs models.md §5).** The gateway writes each attempt's model output, masked with the TRACE profile, into the
  `model_call` span's `masked_output` (models.md §5 rule 7, MOD-10, signed). For values the **adapter** rejects (the choice
  marker, the 1,201-char draft) the attempt has no value, so `masked_output == ""` and the marker must be absent from every
  span field. For values a **downstream** consumer rejects (the 301-char query refused by the dispatcher; the paraphrased
  quote removed by `check_quotes`) the adapter accepted the output, so the contract puts it in that one span's
  `masked_output`. For those two markers the test asserts: absent from every record, log, lookup row, tool error, the
  next request's tool results and the stored brief, and, in the trace sink, absent from every field **except** the
  `masked_output` of the single `model_call` span whose attempt produced it. Changing that would change a signed
  contract, which this ticket may not do.

## 4. Shared code to use (copied from `main` `b68df7e`)

**Imports to use (exact paths).** Use module aliases for the two fixture modules because both define `TURN_1…TURN_5`
with different values: `from tests.unit.agent.nodes import plan_fixtures as pf` and
`from tests.unit.agent.nodes import reply_fixtures as rf`.

```python
# product code (read only)
from meridian.agent.prompts import routing as routing_prompts            # PLANNER_FIELDS, CLASSIFIER_FIELDS (monkeypatch targets)
from meridian.agent.prompts import specialists as specialist_prompts     # ACCOUNT_PREFIX (monkeypatch target)
from meridian.agent.prompts.routing import DANGER_FIELD                  # "danger_level"
from meridian.agent.prompts.reply import LABEL_SETTLED, LABEL_THIS_TURN, trimmed_schema
from meridian.agent.nodes.plan import danger_classifier, join_plan, plan_join, planner
from meridian.agent.nodes import reply                                   # reply.responder / reply.brief / reply.checks; reply.check_quotes (spy target)
from meridian.agent.nodes import act                                     # act.run_specialist / act.escalation (AEA-39; step 9 only)
from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.routers import route_after_plan_join
from meridian.agent.specialists.specs import REPORT_FACTS_TOOL, SPECS, RunOutcome, SpecialistSpec
from meridian.agent.specialists.runner import SpecialistRunner
from meridian.agent.tools.dispatch import ToolDispatcher, ToolRegistry
from meridian.agent.tools.knowledge import knowledge_tools
from meridian.agent.tools.account import account_tools
from meridian.agent.tools.scheduling import scheduling_tools
from meridian.agent.gateway import ModelGateway, ModelOutcome
from meridian.agent.context import GraphDeps
from meridian.adapters.models.openrouter_jev import JevAdapter
from meridian.adapters.models.anthropic import AnthropicAdapter
from meridian.checks import check_quotes
from meridian.policy.escalation import decide_escalation
from meridian.policy.handoff import priority_for
from meridian.policy.limits import Brakes, Limits
from meridian.services.handoff import BriefAssembler
from meridian.domain.common import FailureCounters, HandoffReason, LLMFacing, Priority, ProviderFailure, ProviderFailureKind, Role, ToolErrorCode
from meridian.domain.turn import (CheckEvent, DangerAssessment, EscalationInputs, Plan, PlannedTask, PlannerChoices,
    PlannerOutcome, ResponderDraft, SignalName, SpanHandle, TaskIntent, TurnBudget, TurnContext, TurnIds)
from meridian.domain.handoff import BriefExtraction, Quote
from meridian.domain.state import ConversationState, SpecialistSend
from meridian.domain.tools import SpecialistTask, ToolCallScope
from meridian.ports.models import ChoiceAnswer, ChoiceRequest, StructuredRequest, ToolStep, ToolStepRequest
# test support (read only)
from tests.fakes import WORKED_PAIRS_NOW, FakeIndex, FixedClock, InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.agent._gateway_doubles import RecordingLedger, default_doubles, gateway_kwargs
from tests.unit.agent.specialists._doubles import WP1_INCLUDES, WP1_MINIMUM, WP1_PRICE, make_task, scheduling_slice
from tests.contract._anthropic_fixtures import MODEL as SONNET_MODEL, Recorder, adapter_for, ok, respond, sequence
```

**Signatures you call (from the code, not the contracts):**

```python
# agent/prompts/routing.py
PLANNER_FIELDS: Final[tuple[ChoiceField, ...]]   # knowledge(no,yes) account(none,invoice,membership,appointments,warranty)
                                                 # scheduling(none,book_new,reschedule,cancel,confirm)
                                                 # handoff(none,refund,billing_dispute,membership_cancel,unsupported_other,complaint_or_manager,late_technician)
                                                 # topic(booking,membership,billing,warranty,other)
CLASSIFIER_FIELDS: Final[tuple[ChoiceField, ...]]  # danger_level(normal,burning_unclear,danger)
def planner_request(planner_input: PlannerInput) -> ChoiceRequest   # reads module-global PLANNER_FIELDS at call time
def classifier_request(latest_message: str) -> ChoiceRequest       # reads module-global CLASSIFIER_FIELDS at call time
# agent/nodes/plan.py
def planner(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlannerUpdate
def danger_classifier(state, runtime, *, deps) -> DangerUpdate      # {"danger": DangerAssessment, "check_events": (CheckEvent,)}
def plan_join(state, runtime, *, deps) -> PlanJoinUpdate
def join_plan(planner: PlannerOutcome | None, danger: DangerAssessment | None, gate: GateDecision,
              state: ConversationState, *, tasks_per_turn: int = 3) -> Plan
# agent/nodes/reply.py
def responder(state, runtime, *, deps) -> ResponderUpdate          # draft None + responder_fallback signal on failure
def brief(state, runtime, *, deps) -> BriefUpdate                  # needs deps.cases.open_case_for_thread, deps.brief, deps.uow
def checks(state, runtime, *, deps) -> ChecksUpdate                # calls the module-global check_quotes(ext, shown)
# agent/nodes/act.py (AEA-39 fills the bodies; signatures already on main)
def run_specialist(payload: SpecialistSend, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> SpecialistUpdate
def escalation(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> EscalationUpdate
# agent/nodes/compose.py
class ReplyComposer:  def compose(self, state: ConversationState, ctx: TurnContext) -> ComposedReply
# agent/specialists
@dataclass(frozen=True) class SpecialistSpec: kind; tool_kinds: frozenset[ToolKind]; report_model: type[LLMFacing];
    render: Callable[[SpecialistTask, TurnContext], tuple[str, str, str]]; build_result: Callable[[RunOutcome], SpecialistResult]
@dataclass(frozen=True) class RunOutcome: task; captured; passages_returned; report: LLMFacing | None; quick_checks; tools; calls; brake; failure
class SpecialistRunner:
    def __init__(self, *, gateway: ModelGateway, transcript: ToolTranscript, dispatcher: ToolDispatcher,
                 specs: Mapping[SpecialistKind, SpecialistSpec], brakes: Brakes, trace: TraceSink) -> None
    def run(self, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext) -> SpecialistResult
# agent/tools
class ToolRegistry:  def __init__(self, defs: Iterable[ToolDef]); def get(self, name) -> ToolDef | None;
                     def for_kinds(self, kinds) -> tuple[ToolDef, ...]; def check_covers(self, kinds) -> None  # raises ValueError
class ToolDispatcher: def __init__(self, registry: ToolRegistry, uow: UnitOfWorkFactory);
                      def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]
def knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]        # kb_search (KbSearchArgs.query 1..300)
def account_tools(uow: UnitOfWorkFactory) -> tuple[ToolDef, ...]           # read_invoices, read_membership, read_warranty
def scheduling_tools(scheduling: SchedulingService) -> tuple[ToolDef, ...] # book_visit, cancel_visit, find_windows, move_visit, request_visit_change
# gateway: constructor keyword arguments come from gateway_kwargs(d, limits) (returns dict[str, Any]); override "trace"
class ModelGateway:
    def choose(self, role: ChoiceRole, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]
    def structured[T](self, role: StructuredRole, req: StructuredRequest[T], ctx: TurnContext) -> ModelOutcome[T]
    def tool_step(self, role: ToolRole, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[ToolStep]
class ModelOutcome[T](MeridianModel): value: T | None; calls: tuple[CallRecord, ...]; failure: ProviderFailure | None; halt: Halt | None
# adapters
JevAdapter(http: httpx.Client, *, api_key: SecretStr, model: str)   # model must be "typesafe/jev-1.13"
AnthropicAdapter(client: anthropic.Anthropic, *, model: str)        # model must be "claude-sonnet-5-5"; build via adapter_for(handler)
# policy / checks / services
def decide_escalation(inputs: EscalationInputs) -> EscalationDecision
def priority_for(reason: HandoffReason, *, promise_due=None, renewal_date=None) -> Priority  # raises ValueError if unknown
def check_quotes(extraction: BriefExtraction, shown: Mapping[int, str]) -> QuoteCheck
class BriefAssembler: def __init__(self, staff_guidance=None); assemble(case, state, lookups) -> Brief;
                      attach_extraction(brief, extraction, check, *, customer_messages=None) -> Brief  # None → headings 2,4,7 not_generated, status "failed"
```

**Fixture helpers you reuse (read only):**
- `pf.make_state(text, *, turn_id, gate=None, chat=(), tasks=(), identity=None, settled=None, planner=None, danger=None, halt=None, shown_slots=())`,
  `pf.line(speaker, text, turn_id)`, `pf.open_task(task_id="t-1", *, specialist, intent, status="open")`, `pf.free_text_gate()`,
  `pf.runtime(ctx)`, `pf.choices(**kw)` (base `{"knowledge":"no","account":"none","scheduling":"none","handoff":"none","topic":"other"}`),
  texts `pf.WP1, pf.WP3, pf.WP3_PICK, pf.WP4F, pf.WP7, pf.WP8, pf.DANGER, pf.NODANGER`, ids `pf.TURN_1…pf.TURN_5`.
  `make_state` sets `thread_id` to the spine thread: always `.model_copy(update={"thread_id": rf.THREAD})`.
- `rf.THREAD`, `rf.TURN_4`, `rf.state(**overrides)`, `rf.turn_input(*, turn, message_id, text)`, `rf.facts(**overrides)`,
  `rf.settled(*actions)`, `rf.case_summary()`, `rf.handoff_result(case)`, `rf.FakeCaseService(case)` (`.attached`),
  `rf.seed(store, *, customer=[(turn_id, text)], lookups=(), actions=())` → message ids (writes into `rf.THREAD`),
  `rf.deps(*, uow, gw, cases=None, brief=None, limits=None)` → `GraphDeps`, `rf.WP7_MESSAGE`.
- `default_doubles(**adapters)` with keywords `planner, classifier, fallback, responder, brief, specialist`;
  `gateway_kwargs(d, limits=None)`; `RecordingLedger` (`.records: list[tuple[CallRecord, TurnIds]]`, `.models_disabled()`).
- `adapter_for(handler) -> (AnthropicAdapter, Recorder)`; `ok(content, *, stop_reason="end_turn")`;
  `respond(status, *, json=None, content=None)`; `sequence(*handlers)`; `Recorder.requests`, `Recorder.bodies()`.
- `make_task(specialist, intent, text, *, messages=(), offer_quick_checks=False, slice_=None) -> SpecialistTask`.
- `InMemoryTraceSink().turn(ids)` (context manager yielding the `SpanHandle` the gateway must use), `.turns[i].model_calls`
  (`RecordedModelCall(record, masked_input, masked_output)`), `.turns[i].nodes`.
- Messages table roles are only `'customer'`, `'assistant'`, `'representative'`; append extra roles with
  `tx.core.messages.append(rf.THREAD, role, text, WORKED_PAIRS_NOW, turn_id=turn, kind="text")` inside
  `with store.uow(write=True) as tx: …; tx.commit()`. Lookup rows: `tx.core.lookup_log.for_thread(rf.THREAD)` (`LookupRow`, field `result_seen`).
- Signals: `caplog.set_level(logging.INFO, logger="meridian.signal")`; records `r.__dict__["signal"]` where `r.name == "meridian.signal"`.

**Raw provider bodies.**
- Jev (HTTP 200 JSON): `{"id": "gen-test-0060", "model": "typesafe/jev-1.13", "answers": {<field>: {"type": "choice", "choice": <value>}}, "usage": {"input_tokens": 300, "output_tokens": 20}}`.
  Missing field = omit the key from `answers`; unparseable = `httpx.Response(200, content=b"{not json", headers={"content-type": "application/json"})`.
  The Jev adapter rejects a choice not in the field's options or a missing field with `INVALID_OUTPUT`, `retryable=False`.
- Anthropic: `ok([{"type": "text", "text": json.dumps(obj)}], stop_reason="end_turn")` for choose/structured;
  tool step: `ok([{"type": "tool_use", "id": "toolu_01", "name": <name>, "input": <dict or a str for args=None>}], stop_reason="tool_use")`;
  unparseable: `respond(200, content=b"{not json")`; `stop_reason="max_tokens"` / `"refusal"` → `MAX_TOKENS` / `REFUSAL`
  (neither retryable in `anthropic.py` `_RETRYABLE`, so one attempt).

## 5. Steps

Build in this order; run the module after each step (`uv run pytest tests/contract/test_prompts_vs_consumers.py -q`).

**Step 0 — preconditions.** On your branch: `grep -c NotImplementedError src/meridian/agent/nodes/act.py` must print `0`
(AEA-39 merged). If it prints more, stop and report `BLOCKED-ON AEA-39` without writing code. `export UV_LINK_MODE=hardlink`.

**Step 1 — `_prompts_render.py`: ids, context, recording gateway.**
1. Constants: `THREAD = rf.THREAD`; `NOW = FixedClock().now()` (== `WORKED_PAIRS_NOW`); `JEV_MODEL = "typesafe/jev-1.13"`.
2. `@contextmanager def case_ctx(sink: InMemoryTraceSink, turn_id: TurnId) -> Iterator[TurnContext]`: `ids = TurnIds(thread_id=THREAD, turn_id=turn_id, request_id=RequestId(str(uuid.uuid4())), run_tag="live", run_id=None, agent_version="test")`; inside `with sink.turn(ids) as span:` yield `TurnContext(ids=ids, budget=TurnBudget(started=t, deadline=t + 60.0), now=NOW, demo_session="demo-test", span=span)` with `t = time.monotonic()`. Invariant: the span is opened by the same sink the gateway writes to (`InMemoryTraceSink._own` raises otherwise).
3. `class RecordingGateway` with DO-4 §12 method signatures `choose(role, req, ctx)`, `structured(role, req, ctx)`, `tool_step(role, req, ctx)`; constructor `(outcomes: Mapping[Role, Sequence[ModelOutcome[Any]]])`; each call appends `(role, req)` to `self.requests` and pops the next outcome for that role (raise `AssertionError(f"unexpected {role.value} call")` when empty). Builders: `ok_choice(picks) -> ModelOutcome[ChoiceAnswer]`, `ok_value(value) -> ModelOutcome[Any]`, `failed(kind, provider) -> ModelOutcome[Any]` (a `ProviderFailure` with `http_status=None, retry_after_s=None, retryable=False, provider_request_id=None`), `end_step() -> ModelOutcome[ToolStep]` (`ToolStep(text="", tool_calls=(), raw={"role": "assistant", "content": []}, stop_reason="end_turn")`). Pass it where `ModelGateway` is typed with `cast("ModelGateway", gw)`.
4. `class NoScheduling`: `__getattr__` raises `AssertionError("AEA-60 never executes a scheduling tool")`. The registry factory only closes over it.
5. `def build_registry(store: TempStore, index: FakeIndex) -> ToolRegistry`: `ToolRegistry((*knowledge_tools(index), *account_tools(store.uow), *scheduling_tools(cast(Any, NoScheduling()))))` (exactly AEA-51's wiring order, graph-tools §1).

**Step 2 — the fixture conversation and render functions (`_prompts_render.py`).**
1. `CONVERSATION: tuple[tuple[TurnId, str, str], ...]` = (turn id, customer text, assistant reply), synthetic, from WP-3/WP-4F:
   `(pf.TURN_1, pf.WP3, "I can help book a visit for that.")`, `(pf.TURN_2, pf.WP3_PICK, "Saturday 16:00-19:00 is open.")`,
   `(pf.TURN_3, "Saturday afternoon works best.", "Here are two windows.")`, `(pf.TURN_4, "Yes, the 4 to 7 window.", "Shall I book it?")`,
   `(pf.TURN_5, pf.WP4F, "")`. `RENDER_TURNS = (0, 1, 4)` (turns 1, 2, 5).
2. `def routing_state(k: int) -> ConversationState`: `pf.make_state(text_k, turn_id=turn_k, chat=[pf.line("customer", t, id), pf.line("assistant", a, id) for earlier turns], tasks=[] if k == 0 else [pf.open_task("t-1", specialist="scheduling", intent=TaskIntent.BOOK_NEW)]).model_copy(update={"thread_id": THREAD})`.
3. `def seed_conversation(store) -> dict[str, list[int]]`: write every customer line (role `customer`), every non-empty assistant line (role `assistant`) and one `("representative", "A team member is checking the schedule.")` on `pf.TURN_4`; return ids by role.
4. Render functions, each returning `list[tuple[Role, ChoiceRequest | StructuredRequest[Any] | ToolStepRequest]]` for one turn index `k`, all through the real node or runner:
   - `render_planner(k)`: `planner(routing_state(k), pf.runtime(ctx), deps=pf.make_deps(gw))` with `gw = RecordingGateway({Role.PLANNER: [failed(INVALID_OUTPUT, "openrouter_jev")], Role.PLANNER_FALLBACK: [ok_choice(pf.choices())]})`. This yields both the `planner` and the `planner_fallback` request. (`pf.make_deps(gateway)` is the plan fixture's builder.)
   - `render_classifier(k)`: `danger_classifier(...)` with `{Role.CLASSIFIER: [ok_choice({"danger_level": "normal"})]}`.
   - `render_specialist(kind, k)`: a `SpecialistRunner(gateway=cast(ModelGateway, gw), transcript=<AnthropicAdapter from adapter_for(handler that raises AssertionError)>, dispatcher=ToolDispatcher(registry, store.uow), specs=SPECS, brakes=Brakes(), trace=sink)`, `gw = RecordingGateway({Role.SPECIALIST: [end_step()]})`; task `make_task(kind, intent, text_k, messages=<earlier customer texts>)` with intent `ANSWER_QUESTION` / `READ_INVOICE` / `BOOK_NEW` and `slice_=scheduling_slice()` for scheduling; scope `ToolCallScope(ids=ctx.ids, customer_id=None, shown_slot_ids=frozenset(), now=ctx.now, message_id=<seeded customer id of turn k>)`. Return the recorded `ToolStepRequest` and keep the task (AC-5 reads its slice).
   - `render_responder(k)`: `reply.responder(rf.state(turn_input=rf.turn_input(turn=turn_k, message_id=id_k, text=text_k), facts=rf.facts(turn_id=turn_k), chat_window=<lines>), runtime, deps=rf.deps(uow=store.uow, gw=cast(ModelGateway, gw)))`, `gw` scripted `{Role.RESPONDER: [ok_value(ResponderDraft(text="I can help with that."))]}`.
   - `render_brief(k)`: `reply.brief(rf.state(turn_input=…, handoff=rf.handoff_result(rf.case_summary()), facts=rf.facts(turn_id=turn_k)), runtime, deps=rf.deps(uow=store.uow, gw=…, cases=rf.FakeCaseService(rf.case_summary()), brief=BriefAssembler()))`, `gw` scripted `{Role.BRIEF: [ok_value(<valid BriefExtraction quoting the seeded WP3 message>)]}`.
5. `RENDERERS: Mapping[str, Callable[...]]` keyed `"planner"`, `"planner_fallback"`, `"classifier"`, `"responder"`, `"brief"`, `"specialist:knowledge"`, `"specialist:account"`, `"specialist:scheduling"`. The role `"specialist"` is covered when every `specialist:<kind>` key for `SPECS` exists.
6. `def offered_set(role: str, request) -> object`: choice → `{f.name: frozenset(f.options) for f in request.fields}`; tool step → `(tuple((t.name, json.dumps(t.input_schema, sort_keys=True), t.strict) for t in request.tools))`; structured → `json.dumps(request.output_model.model_json_schema(), sort_keys=True)`.

**Step 3 — `_prompts_checks.py`: `Drift` and the comparison helpers.** Every helper raises `class Drift(AssertionError)` with a message naming role, field and value, never customer text. Message forms (exact; AC-11 matches them):
- `f"{role}.{field} offers '{value}'; {consumer} does not accept it"`
- `f"{role}.{field} does not offer '{value}'; {consumer} accepts it"`
- `f"{role} has no rendered case"` (inventory)
- `f"specialist.{kind} wording names '{token}'; no tool sent with it"`
- `f"responder.output_model offers '{name}'; ResponderDraft does not accept it"`
- `f"brief.shown offers message {mid} which is not a customer message of this thread"`

Helpers (signatures are decisions of this plan):
1. `def literal_values(model: type[BaseModel], field: str) -> frozenset[str]`: `frozenset(typing.get_args(model.model_fields[field].annotation))` (works for `Topic` and the inline `Literal`s; verified on `main`).
2. `def check_choice_fields(role: str, request: ChoiceRequest, consumer: type[BaseModel], *, fields: Mapping[str, str] | None = None, code_only: frozenset[str] = frozenset()) -> None`. For the planner: field names must equal `set(PlannerChoices.model_fields)` (raise `Drift(f"{role} sends field '{name}'; PlannerChoices has no such field")` / the reverse); for each field compare option keys with `literal_values` both ways, ignoring `code_only` in the reverse direction; assert `len(options) <= 255`. For the classifier call it with `consumer=DangerAssessment, fields={DANGER_FIELD: "label"}` (request field → consumer field) and the consumer name `"DangerAssessment.label"`.
3. `def check_quoted_keys(role: str, request: ChoiceRequest) -> None`: every `re.findall(r'"([a-z_]+)"', text)` over `request.system` and each `field.instructions` must be in the union of the request's option keys (today: planner `none`, `no`; classifier `normal`).
4. `CODE_ONLY: frozenset[str] = frozenset({"safety", "danger", "burning_unclear", "customer_requested_person", "legal_or_chargeback", "commercial", "fee_bearing_change", "identity_unverified", "ai_failure", "burning_ruled_out"})`; assert at import that `CODE_ONLY <= {r.value for r in HandoffReason}`. `FORBIDDEN_FIELDS = frozenset({"priority", "case_ref", "case_reference", "reference", "promise", "promise_text", "customer_id"})`. `EXEMPT = frozenset({("classifier", "danger_level")})` (clarification C-1).
5. `def property_names(schema: object) -> set[str]` (recursive over `properties` and `$defs`) and `def enum_values(schema) -> set[str]` (recursive over `enum` lists).
6. `def trimmed(args_model: type[LLMFacing]) -> dict[str, Any]`: an independent copy of the title-stripping rule (drop every `"title"` key whose value is a `str`, except names directly under `properties` / `$defs`, never recurse into `default`, `examples`, `const`, `enum`). Do **not** import `dispatch._trimmed_schema` (comparing a function with itself proves nothing).
7. `def check_specialist_request(kind: str, request: ToolStepRequest, registry: ToolRegistry, dispatcher: ToolDispatcher, task: SpecialistTask) -> None`, the AC-5 list, in this order (each failure is a `Drift` naming kind, tool, field):
   1. `names = [t.name for t in request.tools]`; `names == [s.name for s in dispatcher.schemas(spec.tool_kinds)] + [REPORT_FACTS_TOOL]` (order as sent);
   2. each non-report name: `re.fullmatch(r"[a-z_]{1,64}", name)`, `registry.get(name) is not None`, `registry.get(name).kind in spec.tool_kinds`;
   3. `registry.get(REPORT_FACTS_TOOL) is None`; `registry.check_covers(spec.tool_kinds)` does not raise;
   4. each tool: `strict is True`; `input_schema == trimmed(defn.args_model)`; `set(input_schema.get("properties", {})) == set(defn.args_model.model_fields)`; `input_schema["additionalProperties"] is False`; `property_names(input_schema) & set(ToolCallScope.model_fields) == set()`;
   5. the `report_facts` tool: `input_schema == spec.report_model.model_json_schema()` (PD-9, untrimmed);
   6. wording: tokens `re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", request.system_prefix + "\n" + request.system_dynamic)`; each token must be in `allowed = set(names) | property_names(all sent schemas) | enum_values(all sent schemas) | json_keys(task.slice.model_dump(mode="json"))`. Today's tokens (measured on `main`): knowledge `kb_search, passage_id, report_facts`; account `read_invoices, read_membership, read_warranty, report_facts`; scheduling `appointment_id, hvac_repair, hvac_tune_up, report_facts, shown_slots, wanted_time` — all allowed.
8. `def check_responder_request(request: StructuredRequest[Any]) -> None`: `request.output_model is ResponderDraft` else `Drift` naming each extra property (`property_names(model_json_schema) - {"text"}`); `json.loads(trimmed_schema(ResponderDraft)) == {"additionalProperties": False, "properties": {"text": {"maxLength": 1200, "minLength": 1, "type": "string"}}, "required": ["text"], "type": "object"}`; `trimmed_schema(ResponderDraft) in request.system_prefix`; `LABEL_THIS_TURN in request.system_dynamic and LABEL_SETTLED in request.system_dynamic`; `property_names(...) & FORBIDDEN_FIELDS == set()`.
9. `def parse_brief_lines(user: str) -> dict[int, str]`: lines matching `^\[message (\d+)\] (.*)$`.
   `def check_brief_ids(rendered: Mapping[int, str], shown: Mapping[int, str], customer_ids: set[int]) -> None`: every rendered id in `customer_ids` (else the `brief.shown …` Drift); `dict(rendered) == dict(shown)` (ids and byte-identical text).
10. `def missing_cases(names: Iterable[str], renderers: Mapping[str, object]) -> None`: raise `Drift(f"{name} has no rendered case")` for the first name with no key (`specialist` is satisfied by the `specialist:<kind>` keys of every `SPECS` kind).
11. The held-out / socket guard (AC-12):
    - `HELD_OUT_PREFIXES: list[str] = [str(REPO_ROOT / "eval" / "cases" / "heldout"), str(Path.home() / ".meridian-sealed")]` where `REPO_ROOT = Path(__file__).resolve().parents[2]`.
    - `@dataclass class Guard: active: bool = False; opens: list[str]; connects: list[str]`; `GUARD = Guard()`.
    - `def _hook(event: str, args: tuple[object, ...]) -> None`: return at once unless `GUARD.active`; on `"open"` with a `str | bytes | os.PathLike` first arg, `os.path.abspath(os.fsdecode(arg))` starting with any prefix → append; on `"socket.connect"` or `"socket.getaddrinfo"` → append the event name. Wrap the body in `try/except Exception: pass` (an audit hook must never raise).
    - `def install_guard() -> None`: `sys.addaudithook(_hook)` once (module flag). Invariant: audit hooks cannot be removed, so the hook is inert unless `GUARD.active`.

**Step 4 — tests AC-1 to AC-6** in `test_prompts_vs_consumers.py` (each opens its own `temp_sqlite()` and `InMemoryTraceSink()`):
- `test_every_role_and_spec_has_a_rendered_case(name)` parametrised over `[r.value for r in Role] + [f"specialist:{k}" for k in SPECS]`: run the renderer for k in `RENDER_TURNS`; assert one request per turn for that role; assert `offered_set` equal on the three turns; for `planner_fallback` assert its request `==` the planner request of the same turn. Inside the same test (one extra param `"triage"` is not possible on `Role`, so do it once, in the `name == "planner"` param): `with pytest.raises(Drift, match="triage has no rendered case"): missing_cases([*(r.value for r in Role), "triage"], RENDERERS)`.
- `test_routing_fields_match_planner_choices_and_danger_label()`: render turn 1; `check_choice_fields("routing.planner", planner_req, PlannerChoices)`; same for the fallback request; `check_choice_fields("routing.classifier", classifier_req, DangerAssessment, fields={DANGER_FIELD: "label"})`; `[f.name for f in classifier_req.fields] == [DANGER_FIELD]`; `check_quoted_keys` on both; assert `"late_technician"` in the handoff options.
- `test_join_plan_accepts_every_offered_value(field, option)`: parametrise at import over `[(f.name, o) for f in routing_prompts.PLANNER_FIELDS for o in f.options]` (data-driven). Build `PlannerOutcome(choices=PlannerChoices.model_validate(pf.choices(**{field: option})), probabilities=None, model=JEV_MODEL, fallback_used=False, failure=None)`; `plan = join_plan(outcome, None, pf.free_text_gate(), pf.make_state(pf.NODANGER))`. Then: every `t.specialist in SPECS`; if `field == "topic"`: `plan.topic == option`; if `field == "handoff" and option != "none"`: `plan.handoff_request is EXPECTED_HANDOFF[option]` with `EXPECTED_HANDOFF = {"refund": REFUND, "billing_dispute": BILLING_DISPUTE, "membership_cancel": MEMBERSHIP_CANCEL, "unsupported_other": UNSUPPORTED_ACTION, "complaint_or_manager": COMPLAINT_OR_MANAGER, "late_technician": LATE_TECHNICIAN}` (cases.md §3.4; written out in the test, never imported from `plan._HANDOFF_REASON`), `priority_for(plan.handoff_request)` returns a `Priority`, and `decide_escalation(EscalationInputs(gate=pf.free_text_gate(), plan=plan, results=(), counters=FailureCounters(), identity=state.identity, halt=None, models_disabled=False, now=NOW))` has `outcome == "escalate"`, `reason is plan.handoff_request`, `priority is not None`.
- `test_no_prompt_offers_a_code_only_value()`: for every rendered choice request except `EXEMPT` pairs, `set(options) & CODE_ONLY == set()` (message names role, field, value); assert the exemption exists by name (`("classifier", "danger_level") in EXEMPT`); for every specialist request, `(property_names ∪ enum_values of every tool schema) & CODE_ONLY == set()` and `property_names & FORBIDDEN_FIELDS == set()`; same `FORBIDDEN_FIELDS` check on `ResponderDraft` and `BriefExtraction` schemas.
- `test_specialist_tools_match_registry_and_report_models(kind)` parametrised over `list(SPECS)`: `check_specialist_request(...)` on the turn-1 request.
- `test_reply_schemas_and_brief_message_ids_match_checks(monkeypatch)`: WP-7 refund turn: seed `rf.WP7_MESSAGE` (customer, `rf.TURN_4`), one assistant and one representative line; `check_responder_request(<rendered responder request>)`; brief: `request.output_model is BriefExtraction`; spy `seen: list[dict[int, str]]`, `monkeypatch.setattr(reply, "check_quotes", lambda ext, shown: (seen.append(dict(shown)), check_quotes(ext, shown))[1])`; run `reply.brief` then `reply.checks` on the state with `brief_extraction` set to the brief node's value; `check_brief_ids(parse_brief_lines(brief_req.user), seen[0], customer_ids)` where `customer_ids` = ids of rows with `role == "customer"` from `tx.core.messages.all_for_thread(THREAD)`.

**Step 5 — `_prompts_malformed.py`: real adapters and the gateway.**
1. `def jev_adapter(handler: Callable[[httpx.Request], httpx.Response]) -> tuple[JevAdapter, list[httpx.Request]]`: records requests; `JevAdapter(httpx.Client(transport=httpx.MockTransport(recording)), api_key=SecretStr("test-key-" + secrets.token_hex(8)), model=JEV_MODEL)`.
2. `def jev_body(answers: Mapping[str, str]) -> dict[str, Any]` and `def jev_ok(answers) -> handler` per section 4.
3. `def real_gateway(*, sink: InMemoryTraceSink, ledger: RecordingLedger, **adapters: object) -> ModelGateway`: `d = default_doubles(ledger=ledger, **adapters)`; `return ModelGateway(**{**gateway_kwargs(d), "trace": sink})`. Unused roles keep the scripted doubles from `default_doubles`.
4. `@dataclass class CaseRun`: `case_id`, `ledger: RecordingLedger`, `sink: InMemoryTraceSink`, `signals: list[dict[str, Any]]`, `log_records: list[logging.LogRecord]`, `check_events: list[CheckEvent]`, `lookup_rows: list[LookupRow]`, `tool_records: list[ToolCallRecord]`, `failures: list[ProviderFailure]`, `requests: dict[str, int]` (HTTP requests per adapter), `next_request_bodies: list[dict]` (Anthropic bodies after the first), `stored_briefs: list[Brief]`, `result: object` (node update, `SpecialistResult`, `Plan`, `CheckedReply`, `ComposedReply` as relevant), `outcome: RunOutcome | None`, `ctx: TurnContext`.
5. `MARK_OPTION = "zq-rejected-option-7731"`, `MARK_QUERY = "zq-rejected-query-7731"`, `MARK_DRAFT = "zq-rejected-draft-7731"`; `def padded(marker: str, length: int) -> str: return "a" * (length - len(marker) - 1) + " " + marker` (assert `len == length`).
6. Case runners, each `(case_id: str, caplog: pytest.LogCaptureFixture) -> CaseRun`, each with its own `temp_sqlite()`, sink, ledger and `case_ctx`. `caplog.set_level(logging.DEBUG)` and `caplog.clear()` at the start; collect `list(caplog.records)` at the end.

   **`run_routing_case`** (AC-7). Planner and classifier each get their own `JevAdapter`; `fallback` is `adapter_for(...)`. State `pf.make_state(text, turn_id=pf.TURN_1).model_copy(update={"thread_id": THREAD})`:

   | case_id | text | Jev planner body | Sonnet fallback text | Jev classifier body |
   |---|---|---|---|---|
   | `a-choice-outside-options` | `pf.WP3` | BOOK answers but `knowledge = MARK_OPTION` | BOOK JSON | — |
   | `b-missing-field` | `pf.WP3` | BOOK answers without `topic` | BOOK JSON | — |
   | `c-unparseable-json` | `pf.WP3` | `content=b"{not json"` | BOOK JSON | — |
   | `d1-fallback-extra-field` | `pf.NODANGER` | `knowledge = "maybe"` | BOOK JSON plus `"urgency": "today"` | — |
   | `d2-fallback-option-outside` | `pf.NODANGER` | `knowledge = "maybe"` | BOOK JSON with `"handoff": "cancel_membership"` | — |
   | `e1-classifier-emergency` | `pf.NODANGER` | BOOK answers (valid) | — | `{"danger_level": "emergency"}` |
   | `e2-classifier-empty` | `pf.NODANGER` | BOOK answers (valid) | — | `{}` (no answers) |

   BOOK = `pf.choices(scheduling="book_new", topic="booking")`. For a–d run `planner(...)` then `plan_join(merged_state)` (merge with `state.model_copy(update=dict(update))`); for e run `planner`, `danger_classifier`, then `plan_join` on the state with both updates merged, and `route_after_plan_join(state_with_plan)`.

   **`run_specialist_case`** (AC-8, runner level). Seed one customer message (`rf.seed(store, customer=[(rf.TURN_4, pf.WP1)])`); `index = FakeIndex(passages=(WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM))`; real registry and `ToolDispatcher(registry, store.uow)`; `adapter, recorder = adapter_for(sequence(*handlers))` used as both the gateway's `specialist` adapter and the runner's `transcript`; spy specs: `specs = {**SPECS, kind: dataclasses.replace(SPECS[kind], build_result=spy)}` where `spy` records the `RunOutcome` and returns `SPECS[kind].build_result(outcome)` (observation only); `SpecialistRunner(gateway=gw, transcript=adapter, dispatcher=dispatcher, specs=specs, brakes=Brakes(), trace=sink)`; scope with `customer_id=None` and the seeded `message_id`. Step 2 handler for "the run goes on" = `ok([{"type": "text", "text": "Done."}])`.

   | case_id | task | step 1 tool_use(s) | step 2 |
   |---|---|---|---|
   | `unknown-tool` | knowledge / ANSWER_QUESTION / `pf.WP1` | `issue_refund` `{"amount_cents": 47800}` | end |
   | `not-allowed` | knowledge | `read_invoices` `{}` | end |
   | `args-none` | knowledge | `kb_search` input `"not-json{"` (a string) | end |
   | `extra-customer-id` | knowledge | `kb_search` `{"query": "membership", "customer_id": "C-0001"}` | end |
   | `query-301` | knowledge | `kb_search` `{"query": padded(MARK_QUERY, 301)}` | end |
   | `invoice-pattern` | account / READ_INVOICE / "What is my bill for?" | `read_invoices` `{"invoice_number": "INV-12"}` | end |
   | `report-6-points` | knowledge | `kb_search {"query": "membership"}` and `report_facts {"answered": true, "points": [6 × {"text": "Two tune-ups a year.", "passage_id": str(WP1_INCLUDES.passage_id)}]}` in the same step | none (the runner returns after a step with a report) |
   | `report-summary-301` | account / READ_MEMBERSHIP | `report_facts {"summary": "s" * 301}` only | none |

   **`run_act_case`** (AC-8, act node; step 9). Same store and runner as above (knowledge, no spy needed) with one handler: `step-unparseable` → `respond(200, content=b"{not json")`; `step-max-tokens` → `ok([{"type": "text", "text": "partial"}], stop_reason="max_tokens")`; `step-refusal` → `ok([{"type": "text", "text": ""}], stop_reason="refusal")`. `deps = GraphDeps(gateway=gw, retrieval=index, uow=store.uow, identity=None, scheduling=NoScheduling(), handoff=None, brief=None, demo=None, limits=Limits(), trace=sink, specialists=runner, cases=None, ledger=ledger)`; `planned = PlannedTask(order=1, specialist="knowledge", intent=TaskIntent.ANSWER_QUESTION, needs_identity=False)`; `state = rf.state(turn_input=rf.turn_input(turn=rf.TURN_4, message_id=mid, text=pf.WP1))`; `update = act.run_specialist(SpecialistSend(planned=planned, state=state), pf.runtime(ctx), deps=deps)`; then `state2 = state.model_copy(update={"specialist_results": update["specialist_results"], "plan": Plan(mode="act", tasks=(planned,), handoff_request=None, topic="other", source="planner")})` and `esc = act.escalation(state2, pf.runtime(ctx), deps=deps)["escalation"]`.

   **`run_reply_case`** (AC-9 responder). Seed WP-7; `state = rf.state(turn_input=rf.turn_input(turn=rf.TURN_4, message_id=mid, text=rf.WP7_MESSAGE), facts=rf.facts(), settled=rf.settled())`; responder adapter `adapter_for(handler)`; `upd = reply.responder(state, rt, deps=deps)`; `s2 = state.model_copy(update={"draft": upd["draft"]})`; `checked = reply.checks(s2, rt, deps=deps)["checked"]`; `composed = ReplyComposer().compose(s2.model_copy(update={"checked": checked}), ctx)`. Bodies: `draft-empty` `{"text": ""}`; `draft-1201` `{"text": padded(MARK_DRAFT, 1201)}`; `draft-extra-promise` `{"text": "Your visit is booked.", "promise": "tomorrow"}`; `draft-refusal` stop_reason `"refusal"`.

   **`run_brief_case`** (AC-9 brief). Seed WP-7 (customer), `"I'm sorry the repair didn't fix it."` (assistant) and `"A team member is reviewing your refund."` (representative); `cases = rf.FakeCaseService(rf.case_summary())`; `deps = rf.deps(uow=store.uow, gw=gw, cases=cases, brief=BriefAssembler())`; `state = rf.state(turn_input=…, handoff=rf.handoff_result(rf.case_summary()), facts=rf.facts(), settled=rf.settled())`; `b = reply.brief(state, rt, deps=deps)`; `checked = reply.checks(state.model_copy(update={"brief_extraction": b["brief_extraction"]}), rt, deps=deps)["checked"]`. Let `cid, aid, rid` be the seeded ids and `Q = {"message_id": cid, "text": "full refund"}`. Bodies (JSON text of a `BriefExtraction`-shaped object):

   | case_id | body |
   |---|---|
   | `brief-needs-0` | `{"needs": [], "claims": [], "open_decision": "Decide on the refund."}` |
   | `brief-needs-3` | `{"needs": [Q, Q, Q], "claims": [], "open_decision": "Decide on the refund."}` |
   | `brief-claims-6` | `{"needs": [Q], "claims": [Q]*6, "open_decision": "Decide on the refund."}` |
   | `brief-decision-201` | `{"needs": [Q], "claims": [], "open_decision": "d" * 201}` |
   | `quote-ai-message` | `{"needs": [Q], "claims": [{"message_id": aid, "text": "the repair"}], "open_decision": "Decide on the refund."}` |
   | `quote-staff-message` | `{"needs": [Q], "claims": [{"message_id": rid, "text": "reviewing your refund"}], "open_decision": "Decide on the refund."}` |
   | `quote-paraphrase` | `{"needs": [Q], "claims": [{"message_id": cid, "text": "I want my money back " + MARK_DRAFT}], "open_decision": "Decide on the refund."}` |

**Step 6 — `test_malformed_routing_outputs(case_id)`** (expected values; `K = ProviderFailureKind`):
- a, b, c: `requests == {"jev_planner": 1, "fallback": 1}`; planner update `PlannerOutcome.fallback_used is True`, `choices` = BOOK; plan `source == "fallback_planner"`, one task `BOOK_NEW`; exactly one signal `{"name": "planner_fallback", "cause": "invalid_output", "role": "planner", "node": "planner", "recovered": True}`; the Jev `CallRecord` has `status == "error"`, `failure.kind is K.INVALID_OUTPUT`, `attempt == 1` (no retry).
- d1, d2: `requests == {"jev_planner": 1, "fallback": 1}`; `PlannerOutcome(choices=None, fallback_used=True, failure.kind=INVALID_OUTPUT)`; plan `== Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)`; one `planner_fallback` signal with `recovered is False`.
- e1, e2: `requests["jev_classifier"] == 1`; `danger == DangerAssessment(label="normal", raised=False, confidence=None, failure=<failure with kind INVALID_OUTPUT>)` (compare `label`, `raised`, `failure.kind`); `check_events == [CheckEvent(check="classifier", turn_id=ctx.ids.turn_id, result="fallback", codes=("fallback", "invalid_output"))]`; exactly one signal `classifier_fallback` (`role == "classifier"`, `node == "danger_classifier"`, `cause == "invalid_output"`); `plan_join` returns `{"plan": …}` with tasks `(BOOK_NEW,)` and no `halt`; `route_after_plan_join(...) != "safety"`.

**Step 7 — `test_malformed_specialist_outputs(case_id)`** (runner-level cases; the three `step-*` ids dispatch to `run_act_case`, step 9):
- `unknown-tool`: `tool_records == [<name "issue_refund", kind None, outcome "refused", error UNKNOWN_TOOL, lookup_id not None>]`; one lookup row, `tool == "issue_refund"`, `result_seen == "refused:unknown_tool"`; `requests["specialist"] == 2` (the run went on); `index.searches == []`.
- `not-allowed`: one record `kind is ToolKind.ACCOUNT_READ`, `error is NOT_ALLOWED`; lookup `"refused:not_allowed"`.
- `args-none`, `extra-customer-id`, `query-301`: one record `error is BAD_ARGUMENTS`; lookup `"refused:bad_arguments"`; `index.searches == []` (the executor never ran); `requests["specialist"] == 2`.
- `invoice-pattern`: one record `name == "read_invoices"`, `error is BAD_ARGUMENTS`; lookup `"refused:bad_arguments"`; result `AccountResult.status == "failed"`, `invoices == ()`.
- `report-6-points`: spy `outcome.report is None`; result `KnowledgeResult.status == "no_current_source"`, `points == ()`; `len(index.searches) == 1`; one lookup row for `kb_search`.
- `report-summary-301`: `outcome.report is None`; `AccountResult.status == "failed"`, `membership is None`, `invoices == ()`, `tools == ()`; no lookup row.

**Step 8 — `test_malformed_reply_outputs(case_id)`:**
- `draft-*`: `upd == {"draft": None}`; one signal `{"name": "responder_fallback", "role": "responder", "node": "responder", "cause": "invalid_output" (or "refusal" for draft-refusal), "attempt": 1}`; `checked.fallback_used is True`, `checked.text == ""`; `composed` has a block with `type == "failure_offer"` and `person_key is True`, `composed.outcome == "degraded_handoff"`, `composed.degrade_reason == "model_error"`; `requests["responder"] == 1`.
- `brief-needs-0`, `brief-needs-3`, `brief-claims-6`, `brief-decision-201`: `b == {"brief_extraction": None}`; one `brief_failed` signal, `cause == "invalid_output"`, `role == "brief"`; the last brief in `cases.attached` has `status == "failed"` and headings 2, 4, 7 `not_generated is True` (others `False`); `reply.checks` returned a `CheckedReply` (the turn is not failed).
- `quote-ai-message`, `quote-staff-message`, `quote-paraphrase`: `b["brief_extraction"]` is not None; `checked.events` contains `CheckEvent(check="brief_quote", result="trimmed", removed=1)`; the stored brief's heading 4 items contain no item whose text equals the removed quote; no `brief_failed` signal.

**Step 9 — act-node part of AC-8 (needs AEA-39).** `step-unparseable` / `step-max-tokens` / `step-refusal` via `run_act_case`: `update["specialist_results"][0].status == "failed"` and `.failure.kind` is `INVALID_OUTPUT` / `MAX_TOKENS` / `REFUSAL`; `requests["specialist"] == 1`; exactly one signal `{"name": "specialist_failed", "node": "run_specialist", "role": "specialist", "specialist": "knowledge", "cause": <kind value>}`; `esc.outcome == "escalate"`, `esc.reason is HandoffReason.AI_FAILURE`, `esc.priority is Priority.P3`, `esc.rule_id == "AI.specialist_failed"`, `esc.degraded is True` (cases.md §3.4 rule 6). If AEA-39's node names or fields differ from graph-nodes §4/§9.5, report the mismatch as a defect on AEA-39; do not adapt the test to a contract-breaking value.

**Step 10 — AC-10, AC-11, AC-12, AC-14.**
- `test_rejected_values_absent_from_records(caplog)`: run `a-choice-outside-options` (MARK_OPTION), `query-301` (MARK_QUERY), `draft-1201` (MARK_DRAFT) and `quote-paraphrase` (MARK_DRAFT). For each `CaseRun` build the haystack: `json.dumps` of every `failure.model_dump(mode="json")`, every ledger `CallRecord`, every signal dict, every `CheckEvent`, every `ToolCallRecord`, every `LookupRow`, every stored brief, the `tool_result` contents of `next_request_bodies`, and every log record (`record.getMessage()` plus `json.dumps(record.__dict__, default=str)`). Assert the marker is not a substring. Trace sink: for MARK_OPTION and the 1,201-char draft, the marker is absent from every `masked_input` and `masked_output`; for MARK_QUERY and the paraphrase, the marker is absent from every `masked_input`, and present (if at all) only in the `masked_output` of the one span whose attempt produced it (clarification C-2): assert `[i for i, c in enumerate(spans) if marker in c.masked_output] in ([], [producing_index])`.
- `test_check_fails_on_drift(drift_id, monkeypatch)`: six params, each `pytest.raises(Drift, match=re.escape(<expected message>))`:
  - `planner-handoff-added`: monkeypatch `routing_prompts.PLANNER_FIELDS` with a copy whose `handoff` field has `cancel_membership` added; re-render via `routing_prompts.planner_request(...)`; `check_choice_fields("routing.planner", req, PlannerChoices)` → `routing.planner.handoff offers 'cancel_membership'; PlannerChoices.handoff does not accept it`.
  - `planner-late-technician-removed`: same, `late_technician` removed → `routing.planner.handoff does not offer 'late_technician'; PlannerChoices.handoff accepts it`.
  - `classifier-emergency-added`: monkeypatch `routing_prompts.CLASSIFIER_FIELDS` with `emergency` added → `routing.classifier.danger_level offers 'emergency'; DangerAssessment.label does not accept it`.
  - `specialist-refund-invoice`: monkeypatch `specialist_prompts.ACCOUNT_PREFIX` to `ACCOUNT_PREFIX + " Call refund_invoice when asked."`, re-render through `SPECS["account"].render(task, ctx)` and the runner → `specialist.account wording names 'refund_invoice'; no tool sent with it`.
  - `responder-promise-field`: `class DriftedDraft(LLMFacing): text: str; promise: str` (defined in the test); `req.model_copy(update={"output_model": DriftedDraft})` → `responder.output_model offers 'promise'; ResponderDraft does not accept it`.
  - `brief-staff-message`: rendered map plus the representative message id → `brief.shown offers message <rid> which is not a customer message of this thread`.
  Build the copies with `ChoiceField.model_copy(update={"options": …})` and tuple rebuilds; never write to the prompt modules.
- Module guard: in `test_prompts_vs_consumers.py`, `@pytest.fixture(scope="module", autouse=True) def _no_heldout_no_network() -> Iterator[None]`: `install_guard(); GUARD.active = True; yield; GUARD.active = False; assert GUARD.opens == [] and GUARD.connects == [], (GUARD.opens, GUARD.connects)`.
  `test_no_heldout_reads_and_no_network(tmp_path)`: assert `GUARD.active`; record `before = (list(GUARD.opens), list(GUARD.connects))`; prove the hook bites without touching held-out data: append `str(tmp_path)` to `HELD_OUT_PREFIXES`, `(tmp_path / "probe.txt").write_text("x")`, `open(tmp_path / "probe.txt").close()`, assert a new entry under `tmp_path`, remove the prefix and those entries; `sys.audit("socket.connect", None, ("127.0.0.1", 9))` (an audit event only, no socket), assert recorded, remove it; finally assert `before == ([], [])` (no held-out open and no socket by earlier tests in this worker; the fixture teardown covers the rest of the module). Put this test **last** in the file.
- `test_malformed_cases_leave_their_records(case_id, caplog)` parametrised over every case id of AC-7…AC-9 (7 + 11 + 11 = 29): ledger has one record per HTTP attempt, each failed attempt `status == "error"` with `failure.kind` = the case's kind and `role` = the case's role; the sink has exactly as many `model_calls` as ledger records, with matching `record` objects; every signal carries `name, cause, role, node, turn_id == ctx.ids.turn_id, thread_id == THREAD, request_id == ctx.ids.request_id, run_tag == "live"`; classifier cases carry the `classifier` event; quote cases carry the `brief_quote` event; specialist cases have exactly one lookup row per dispatched call (`len(lookup_rows) == len(tool_records)`). (`step-*` cases go through `run_act_case`.)

**Step 11 — journeys (AC-13)**, copying `tests/journeys/j5/test_aea_37.py`'s structure (`pytestmark = pytest.mark.journey`, `open_chat`, `submit`, `journey.step(J, name, needs=…, operations=("submitTurn",))`, `journey.script.add(Role.X, raw)`, `journey.db.one/rows/count`). `TURN_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer", "turn_service", "run_graph")`; `HANDOFF_NEEDS = (*TURN_NEEDS, "handoff_service", "case_service")`. Steps without their services bound are skipped by the harness as `blocked-on …`; never pass them another way.
- `tests/journeys/j5/test_aea_60.py::test_j5_malformed_classifier_reply_books_normally`: script `PLANNER` BOOK raw (`'{"knowledge": "no", "account": "none", "scheduling": "book_new", "handoff": "none", "topic": "booking"}'`), `CLASSIFIER` `'{"danger_level": "emergency"}'`, `RESPONDER` `json.dumps({"text": "I can help book a visit for that. First I need to find your account."})`; submit `NODANGER`. Assert: 200; block types include `locate_prompt` once, no `emergency_line`, no `safety`; `journey.db.count("cases", "thread_id = ?", (thread_id,)) == 0`; the turn row `danger_raised == 0`, `plan_intents == ["book_new"]`; `check_events` rows with `check_kind = 'classifier'` for the turn: exactly one, `result == "fallback"`, `json.loads(codes) == ["fallback", "invalid_output"]`; `[(c.role, c.result) for c in journey.script.problems()] == [(Role.CLASSIFIER, "invalid_output")]`; `journey.script.remaining() == 0`.
- `tests/journeys/j9/test_aea_60.py::test_j9_both_planners_malformed_hand_off_degraded` (needs `HANDOFF_NEEDS`): script `PLANNER` `'{"knowledge": "maybe", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"}'`, `CLASSIFIER` `'{"danger_level": "normal"}'`, `PLANNER_FALLBACK` the same five keys valid plus `"urgency": "today"`, `RESPONDER` a valid draft, `BRIEF` `json.dumps({"needs": [{"message_id": 1, "text": "question"}], "claims": [], "open_decision": ""})` (schema-valid; its quote may be trimmed; the brief is not asserted here); submit `"Hello, I have a question."`. Assert: 200; one block `type == "handoff"` whose `reference` equals the case row's `case_ref` and whose `promise_text` is non-empty; turn row `outcome == "degraded_handoff"`, `degrade_reason == "model_error"`, `planner_failed == 1`; one case for the thread with `reason == "ai_failure"`, `priority == "P3"`; problems `== [(Role.PLANNER, "invalid_output"), (Role.PLANNER_FALLBACK, "invalid_output")]` (compare as a sorted list).
- `…::test_j9_malformed_responder_draft_falls_back` (needs `TURN_NEEDS`): script PLANNER BOOK raw, CLASSIFIER normal, RESPONDER `'{"text": ""}'`; submit `NODANGER`. Assert: a `failure_offer` block with `person_key is True`; no `text` block from the model; turn `outcome == "degraded_handoff"`, `degrade_reason == "model_error"`; `cases` count 0; problems `== [(Role.RESPONDER, "invalid_output")]`.

**Step 12 — docs (AC-15) and the evidence record.**
1. `docs/design/code-design.md` §9 tree, the `contract/` entry (currently ending `test_types_gen_drift.py`): append `; prompt ↔ consumer checks (AEA-60): test_prompts_vs_consumers.py with private helpers _prompts_render.py, _prompts_checks.py, _prompts_malformed.py`. The "**Built on `main`:**" line: append `; \`tests/contract/test_prompts_vs_consumers.py\` and \`j5/\`, \`j9/test_aea_60.py\` (AEA-60, branch \`<your branch>\`)`. No other edit.
2. `.claude/state/icm-progress.md`: append one row after the last *Routes verified against code and tests* row: `| Routes verified against code and tests | provisional | <date>: AEA-60 prompt ↔ consumer checks: tests/contract/test_prompts_vs_consumers.py (<N> passed) against agent/prompts/{routing,specialists,reply}.py, agent/nodes/{plan,act,reply}.py, agent/specialists/, agent/tools/, both adapters, gateway; journeys j5/j9 test_aea_60.py (<passed or blocked-on …>); record docs/testing/journeys/<date>-AEA-60.md | Each slice adds its route; verified when every area-map row is actual |`.
3. `docs/testing/journeys/<date>-AEA-60.md` with every field of `integrated-journeys.md` §4: Claim (AC-1…AC-14 mock-tested; AC-13 J-5/J-9 legs), Level (`mock-tested` for the contract module; journeys at the level the run reached, `mock-tested` + *Blocked by* AEA-51 while the harness reports `blocked-on`), Tested revision, Environment (host, Python, uv, no network, stubbed transports, scripted journey adapter), Command (section 7), Result (numbers from the run), Evidence location, Remaining limitations (no live model: AEA-61; trace-span carve-out C-2; classifier exemption C-1), Blocked by.
4. Do not edit `.claude/reference/area-map.md`; say "area map unchanged: no area row owns `tests/contract/`" in the commit message body.

**Step 13 — commit** on your branch: `git add <each owned path>` (never `-A`), message `test(AEA-60): prompt ↔ consumer checks and J-5/J-9 malformed-output legs` with a body listing C-1, C-2 and the area-map note, last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push.

## 6. Data and fixtures

Synthetic or development-only: worked-pair texts from `plan_fixtures.py` (WP-1, WP-3, WP-3 pick, WP-4F, WP-7, WP-8,
DANGER, NODANGER), WP-1 passages from `specialists/_doubles.py`, `rf.case_summary()` (`MHC-C-0042`), the issued SQLite
copied by `temp_sqlite()` (never written in place), `FixedClock()` (Friday 2026-10-16 10:00 America/Chicago), API keys
built at run time (`"sk-test-" + secrets.token_hex(12)` via `_anthropic_fixtures`, `"test-key-" + secrets.token_hex(8)`).
The markers are made-up strings. No phone number, card-like number, verification code, real name or e-mail appears; the
`amount_cents` and `customer_id` values (`47800`, `"C-0001"`) are synthetic and never real records. Nothing reads
`eval/cases/heldout/` or the sealed key directory.

## 7. Checks

**While iterating:** `uv run pytest tests/contract/test_prompts_vs_consumers.py -q` (serial: the module-scoped guard
expects one process; at most `-n 2` if you add xdist, and then the guard's teardown covers each worker).

**Once before the final commit (cheapest first, stop at the first red):**
1. `uv run ruff check tests/contract/test_prompts_vs_consumers.py tests/contract/_prompts_render.py tests/contract/_prompts_checks.py tests/contract/_prompts_malformed.py tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py`
   and `uv run ruff format --check` on the same six files.
2. `uv run mypy tests/contract/test_prompts_vs_consumers.py tests/contract/_prompts_render.py tests/contract/_prompts_checks.py tests/contract/_prompts_malformed.py tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py` → `Success: no issues found`.
3. `uv run pytest tests/contract/test_prompts_vs_consumers.py -q -rs` → all pass, 0 skipped, 0 xfailed. Expected count: 8 (AC-1) + 1 + N(AC-3, one per planner option: 2+5+5+7+5 = 24) + 1 + 3 + 1 + 7 + 11 + 11 + 1 + 6 + 29 + 1 = **105** tests.
4. `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py -rs` → each test passes or is skipped with the harness's `blocked-on AEA-…` reason (never failed). Record which in the evidence file.
5. Tests that must stay green (shared-surface neighbours): `uv run pytest tests/journeys/support/test_support.py tests/unit/test_affected_journeys.py tests/contract/test_anthropic_adapter.py tests/contract/test_jev_adapter.py -q` (new journey files follow the `j<N>/test_aea_<NN>.py` convention; the adapter fixtures you import are unchanged).
6. `uv run python -m tests.journeys.affected --base main --list-only` (paste the list into the evidence record).
7. `git diff --name-only main` lists only the nine owned paths; `git diff --stat main -- src/` is empty (AC-11, AC-15).

No full suite: this change adds test files only and touches no shared fixture, setting or dependency (`build-loop-test-scope.md`).
No paid or live call; nothing is marked `live`.

## 8. Risks and requests

- **R-1, AEA-39 (blocker for step 9).** The act-node clause of AC-8 and J-9(a)'s handoff path need AEA-39's real
  `run_specialist` / `escalation` / `handoff`. The orchestrator dispatches this implementer after AEA-39 merges. If AEA-39's
  signal `node` or fields differ from graph-nodes §4/§9.5 (`node="run_specialist"`, `role="specialist"`, `specialist=<kind>`,
  `cause=<failure kind>`), that is a defect on AEA-39, not a test change.
- **R-2, AEA-51.** J-5/J-9 steps stay `blocked-on AEA-51` (`reply_composer`, `run_graph`) until AEA-51 binds them; the
  evidence record says `mock-tested` with *Blocked by* AEA-51 (`integrated-journeys.md` §4). The J-9(a) brief raw quotes
  `message_id: 1`; when AEA-51 lands, if that id is not the customer's, the quote is trimmed and nothing asserted changes.
- **R-3, clarifications C-1 and C-2** (section 3) narrow AC-4 and AC-10 to what the signed contracts allow. Request: the
  orchestrator posts them on issue #60 before review so the reviewer reads the ACs with them.
- **R-4, three private helper files** beyond the slice-plan row (500-line cap). No other ticket names them; the collision map
  row stays "AEA-60's alone".
- **R-5, coupling to other tickets' test helpers** (`plan_fixtures`, `reply_fixtures`, `specialists/_doubles`,
  `_gateway_doubles`, `_anthropic_fixtures`). A later rename there breaks this module at import; the affected-test rule
  ("any test file that imports a changed module") makes that visible at that ticket's merge.
- **R-6, a real mismatch found while building.** If a check goes red on `main` code (not on a typo in the test), keep the test
  red, do not weaken it, and report it with the owning ticket (routing/specialists/reply prompts → AEA-37/35/38; parsers →
  AEA-17/18/22; nodes → AEA-37/38/39). The ticket's scope boundary forbids fixing it here.
- **R-7, audit hook.** `sys.addaudithook` is process-wide and permanent; the hook is inert unless `GUARD.active` and never
  raises. Do not add any other global hook or patch `socket`.
- **R-8, affected-journey mapping.** AEA-60's journey files must be selected when a prompt or schema changes
  (`build-loop-test-scope.md` AEA addition). `tests/journeys/affected.py` is AEA-57's; if its import-based selection does not
  pick these files for a prompt change, that is a follow-up request on AEA-57, not an edit here.

**Must not do:** edit any `src/` file or prompt module; edit another ticket's tests or helpers or `tests/journeys/support/`;
import `dispatch._trimmed_schema` or `plan._HANDOFF_REASON`; use `pytest.skip`/`xfail` anywhere in the contract module
(the journeys rely only on the harness's own `blocked-on` skip); mark anything `live`; open a socket; read held-out paths;
put a phone, card-like number, code or real name in any fixture or test id; exceed 500 lines in any file; `git add -A`;
push; bind ports 4019 or 5184.

## 9. Readiness

**Refresh 1: READY, nothing to build now; step 14 is BLOCKED-ON AEA-51.** Steps 0–13 are built and merged (`0e37fad`);
AC-1…AC-12, AC-14 and AC-15 are met on `main`, and AC-13 is met at the level its own evidence clause allows
(`mock-tested`, *Blocked by* AEA-51). The orchestrator dispatches step 14 only after AEA-51 merges; if AEA-51's own
check 8 already shows the three legs passing, step 14 is the two-doc update in 5a.2. No `NEEDS-DECISION`: CAS-16 and
DAT-2 stay on their D-14 options, C-1 and C-2 stay inside signed contracts, and no signed contract needs a change.

*Original readiness (kept for the record):* READY, with BLOCKED-ON AEA-39 for step 9 only; AEA-39 merged (`12e46ee`)
before the build, so step 9 was built and passes.

## Deviations

Recorded by the implementer, 2026-10-21 (branch `aea-60-prompt-consumer-checks`).

- **Two more private helper files.** `tests/contract/test_prompts_vs_consumers.py` came to 706 lines with all 12 test
  functions' bodies, over the 500-line test cap. The expected-fallback assertions for AC-7..AC-9 moved to
  `tests/contract/_prompts_expect.py` and the six drifted copies of AC-11 to `tests/contract/_prompts_drift.py`; the test
  module is now 449 lines. Same ownership rule as the other three helpers (no other ticket names these paths).
- **Test count is 104, not 105.** The plan's own terms (8+1+24+1+3+1+7+11+11+1+6+29+1) sum to 104; AC-1 has 8 params
  (the five non-specialist roles plus three kinds; the `specialist` role is covered by the three kinds).
  `test_malformed_specialist_outputs` is split in two functions: 8 runner-level params and
  `test_malformed_step_failures_at_the_act_node` (3 params) for the act-node cases.
- **`step 0` held:** `act.py` had 0 `NotImplementedError` (AEA-39 merged, `12e46ee`), so step 9 is built and passes.
- **Journey files import constants from `tests/journeys/j5/test_aea_37.py`** (`BOOK_RAW`, `NODANGER`, `NORMAL_RAW`,
  `RESPONDER_RAW`, `TURN_NEEDS`, `open_chat`, `submit`) instead of copying them. A rename there breaks these files at
  import (same coupling as R-5).
- **Pre-existing red on `main`, not ours:** `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0`
  expects "0 journeys affected" but journeys now exist. Shown by stashing this branch's files and rerunning.
