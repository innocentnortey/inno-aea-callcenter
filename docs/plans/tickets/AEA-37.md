## [AEA-37] graph: plan node (planner, danger classifier, join)

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

> **US-5:** "As a **homeowner** with no cooling on a hot day, I need to book a visit like any repair, with a couple of
> skippable urgency questions, and to be given the emergency number first if I say someone is in danger, so that I'm
> neither frightened needlessly nor left waiting when it matters."

**Example pair (WP-3 and the labelled synthetic DANGER / NODANGER cases).** Input "I need to schedule a service call. My
AC isn't cooling." → planner `scheduling="book_new"`, classifier `normal`, `danger.raised = False`, `Plan(mode="act",
tasks=(scheduling book_new, needs_identity),…, source="planner")`: a normal booking, no emergency number, no P1 case. Input
DANGER "my mother is 88 and it's 95 degrees in here" → no word rule matches, the gate is `free_text`, the classifier says
`danger`, `danger.raised = True`, and AEA-21's `plan_join` router sends the turn to the safety path (R-8). The turn records a
`classifier` / `raised` check event (graph-nodes §1, the opening example). NODANGER "my AC isn't cooling" → `raised = False`,
a `classifier` / `pass` event.

**Second pair (WP-1, WP-4F).** Turn 1 "What does the Comfort Club membership actually include?" → `Plan(mode="act",
tasks=(knowledge answer_question,), topic="membership", source="planner")`. WP-4F turn 4 "Yes, please." after turn 3
closed the move → no open task, so `Plan(mode="talk")`.

**Third pair (both planners fail, GRN-7).** Jev fails twice and the Sonnet fallback fails; the message holds no policy word,
there is no open task and no card choice → `Plan(mode="act", tasks=(), handoff_request=None, topic="other",
source="rules_only", planner_failed=True)`. AEA-21's router sends it to `escalation` (graph-core §11 edge 1), where rule 6
makes it `ai_failure` P3, `degraded=True`, rule id `AI.planner_failed` (cases.md §3.4): the customer gets a handoff reply.

**The behaviour.** `agent/nodes/plan.py` replaces AEA-21's stubs with three node functions, each
`fn(state, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> <Node>Update` (graph-nodes §9.4; update types §9.1), and
`agent/prompts/routing.py` holds their wording and choice fields:

- **`planner` → `PlannerUpdate` (`planner`, `halt`)** (Jev, `ChoiceModel`, `Role.PLANNER`, cap 3 s, DO-4 §12): builds
  `PlannerInput` (DO-4 §3) from the latest message and `recent_chat`, both in the JEV redaction profile (data.md §1: card,
  code, phone `[phone]`, email, street address, introduced name `[name]`, `MHC-…` / `INV-…` → placeholders), plus
  `StateFlags` (flags only, never values). `recent_chat` is taken from `state.chat_window` (built by AEA-34 under
  graph-core §7) and capped at `limits.context.planner_lines` (6) × `planner_line_chars` (400) [A, SP-1], oldest dropped
  first; the node never re-reads `messages`. It asks one choice question per `PlannerChoices` field (`knowledge`, `account`,
  `scheduling`, `handoff`, `topic`; DO-4 §4, with `handoff` gaining `late_technician`, graph-core closing table *cases A-6*)
  through `deps.gateway.choose(Role.PLANNER, …, ctx)`. If the gateway returns a **failure** after its ≤ 2 attempts, it asks
  the same typed question once through `Role.PLANNER_FALLBACK` (Sonnet) [Decided SDQ-6] with `fallback_used=True`; a
  gateway **halt** is never a reason to fall back (models.md cross-topic 4): it is written to `halt` and AEA-21's
  `halt_route` takes over. Writes the state key `planner: PlannerOutcome | None` (renamed from `planner_choices`, GRC-11,
  graph-core §9). Emits `planner_fallback` (graph-nodes §4) when the Sonnet planner ran, `cause` = the Jev failure kind,
  `recovered` = Sonnet answered.
- **`danger_classifier` → `DangerUpdate` (`danger`, `check_events`, `halt`)** (Jev, `Role.CLASSIFIER`): sees
  `latest_message` only (SP-1 shape), one `danger_level` field (`normal`, `burning_unclear`, `danger`); its label may only
  **raise** the rules' verdict, never lower it; on failure or timeout after its one retry the rules stand
  (`label="normal"`, `raised=False`, R-47) and it emits `classifier_fallback` with the failure kind. Every run appends one
  `CheckEvent.from_danger(turn_id, danger)` (`raised` / `pass` / `fallback`, `codes` = the label, or `("fallback", kind)`;
  graph-nodes §1, GRN-5).
- **`plan_join` → `PlanJoinUpdate` (`plan`, `check_events`, `halt`)**: the pure `join_plan(planner, danger, gate, state)
  -> Plan` (DO-4 §4) following SP-1's measured normalize steps: a planner failure never blocks the rules; a policy word
  (`gate.rules.policy_trigger`) overrides the planner's `handoff`; `membership_cancel` adds a membership read and a knowledge
  task; scheduling reads appointments itself; a bare "Yes, please." or a slot pick continues the open task; planner
  `late_technician` maps to `HandoffReason.LATE_TECHNICIAN`; order is set by code (account, then scheduling, then
  knowledge); `topic` is set on every plan (M-3). Both planners failed and nothing else gives a task or handoff →
  `planner_failed=True` as the third pair (graph-nodes §5). A plan that would exceed `limits.brakes.tasks_per_turn` (3)
  writes `Halt(reason=BRAKE_TASKS, node="plan_join")`, a `CheckEvent.from_halt` `brake` event and a `brake_fired` signal
  (graph-nodes §1, §4). Danger is not in `Plan`: the router reads `danger.raised` first (graph-core §11 router order).

Planner and classifier are two branches of one superstep (DO-3 §2.2); their wording starts from SP-1's measured
`PLANNER_SYSTEM`, `PLANNER_FIELDS`, `CLASSIFIER_SYSTEM` and `CLASSIFIER_FIELDS` (`docs/plans/fanout/2026-10-20-sp1/build.md`
step 7), extended only by the DO-4 §4 † fields and `late_technician`. Signals go out through `emit_signal(ids, record)`
(`agent/signals.py`, AEA-21; graph-nodes §4) as `signal` LOG records: IDs and codes only. Node spans come from AEA-21's
`timed_node` wrapper; nodes never call the trace sink (graph-core §4).

### Source

- DO-4 §3 (`StateFlags`, `PlannerInput`: "What crosses this line: only `PlannerInput`"), §4 (`PlannerChoices`,
  `PlannerOutcome`, `DangerAssessment`, `TaskIntent`, `PlannedTask`, `Plan`, `join_plan` rules), §11 (*OpenRouter error
  inside HTTP 200* row: planner → Sonnet fallback, classifier → rules stand), §12 (`ChoiceRequest`, `ChoiceField`,
  `ChoiceAnswer`, roles, Jev cap 3 s, `RoleSpec.redaction` JEV), §16 (addenda win).
- `docs/design/contracts/stage7/graph-nodes.md` §1 (`CheckEvent`, `from_danger`, `from_halt`; who builds which event), §4
  (`SignalName`, `SignalRecord`, `emit_signal`; rows `classifier_fallback`, `planner_fallback`, `brake_fired`), §5
  (`Plan.planner_failed`, GRN-7), §7 (CAP-2 on the DANGER path, GRN-9), §9.1 (`PlannerUpdate`, `DangerUpdate`,
  `PlanJoinUpdate`), §9.4 (node signatures).
- `docs/design/contracts/stage7/graph-core.md` §2 (`TurnContext`, `PlannerTrace`, `TurnTrace.planner` / `danger_raised`),
  §4 (`GraphDeps`, `timed_node`), §5 (`BRAKE_HALTS`, `halt_route`), §7 (`ContextLimits.planner_lines`,
  `planner_line_chars`), §9 (state key `planner`, GRC-11), §11 (`check_events` key and `add_turn_events`; router edge 1),
  closing table row *cases A-6* (`late_technician`).
- `docs/design/contracts/stage7/data.md` §1 (`redact`, `RedactionProfile.JEV`, placeholder tokens, the profile table);
  `docs/design/contracts/stage7/models.md` §5 (gateway rules), cross-topic 4 (fallback for a failure only, never a halt);
  `docs/design/contracts/stage7/cases.md` §3.4 (escalation rule 6 `AI.planner_failed`; rule 4 `D4.late_technician`).
- Decision ledgers: `docs/plans/7b-decisions/graph-nodes.md` GRN-2, GRN-4, GRN-5, GRN-7, GRN-9, GRN-11;
  `docs/plans/7b-decisions/graph-core.md` GRC-9, GRC-11, GRC-16, GRC-18; `docs/plans/7b-decisions/data.md` DAT-1.
- DO-3 §2.2, §4.5, §5.3, §5.4, §7 rows R-8, R-47; §10 C-1, C-2. DO-2 `system-design.md` §A.1, §A.6, §8.2 (*Danger
  classifier*, *Planner* rows), SDQ-6 = A.
- PRD R-8, R-45 (planner sees "the recent clean chat plus a state summary"), R-47; HP-1, HP-2 (C); WP-1, WP-3, WP-4F, WP-7,
  WP-8; SP-1 §3–§4 (mix B: Jev for planner and classifier). Rule `context-management-multi-turn.md` (rules 1, 3, 4, 5).
- Slice plan §0a (Amendment 1, journey J-5) and rule `.claude/rules/integrated-journeys.md` §3–§4.
- Slice plan row AEA-37; area-map row A7d (Front); ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Anything outside the handled call drivers routes to a human" and "Do not let the agent guess";
  touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Raise-only: for every classifier label against every rules verdict, `danger.raised` is true only when the label is above the rules' verdict, and a `normal` label never lowers anything (R-47) — verify: `tests/unit/agent/nodes/test_plan.py::test_classifier_raise_only` — evidence: table over the three labels × verdicts passes; DANGER → `raised=True`, NODANGER → `raised=False`.
- [ ] AC-2 [failure/refusal] A classifier failure (gateway double returns a `body_error` failure, then a `timeout` failure) gives `DangerAssessment(label="normal", raised=False, failure=…)`, one `classifier` check event with result `fallback` and `codes=("fallback", "<kind>")`, one `classifier_fallback` signal with that `cause`, and the turn continues to `plan_join` — verify: `test_plan.py::test_classifier_failure_rules_stand` — evidence: event, signal and danger fields as stated; no exception; `plan` still written.
- [ ] AC-3 [failure/refusal] A Jev planner failure triggers exactly one `Role.PLANNER_FALLBACK` call with the same fields; `fallback_used=True`, `model` names the fallback, one `planner_fallback` signal with `recovered=True`; a gateway **halt** on the planner (`PROVIDER_SPEND_CAP`) causes no fallback call and returns `halt` — verify: `test_plan.py::test_planner_fallback_sdq6`, `::test_planner_halt_never_falls_back` — evidence: recorded call roles planner → planner_fallback in the first; one planner call and a `halt` key in the second.
- [ ] AC-4 [failure/refusal] Both planners fail (GRN-7): with no policy word, open task or card choice, `join_plan` returns `Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)` and the signal has `recovered=False`; with an open scheduling task and "Yes, please.", the same failures give that task continued (`source="open_task"`, `planner_failed=False`) — verify: `test_plan.py::test_both_planners_fail_planner_failed_plan`, `::test_both_planners_fail_open_task_continues` — evidence: plan fields as stated in each case.
- [ ] AC-5 [invariant] `join_plan` normalize steps, table-driven: WP-7 "I want a full refund on the repair…" with planner `handoff="none"` → `handoff_request="refund"` (policy word wins); WP-8 "I want to cancel my Comfort Club membership." with `handoff="membership_cancel"` → tasks account `read_membership` then knowledge, `handoff_request="membership_cancel"`; `handoff="late_technician"` → `HandoffReason.LATE_TECHNICIAN`; `scheduling="reschedule"` with `account="appointments"` → no separate account task; "Yes, please." with an open scheduling task → that task continued (`source="open_task"`); without one → `mode="talk"`; tasks ordered account → scheduling → knowledge; `topic` set on every row — verify: `tests/unit/agent/nodes/test_join_plan.py` (one test per row) — evidence: all rows pass.
- [ ] AC-6 [failure/refusal] Task brake: planner choices that normalize to more than `limits.brakes.tasks_per_turn` (3) tasks make `plan_join` return `Halt(reason=BRAKE_TASKS, node="plan_join")`, one `brake` check event with `codes=("brake_tasks", "plan_join")` and one `brake_fired` signal — verify: `test_plan.py::test_task_brake_halts_with_event` — evidence: halt, event and signal as stated.
- [ ] AC-7 [invariant] Key ownership (graph-nodes §9.1): `planner` returns only keys of `PlannerUpdate`, `danger_classifier` only `DangerUpdate`, `plan_join` only `PlanJoinUpdate`, so the two parallel branches never write the same non-reducer key; the project's type check (the checker AEA-01 chose) passes on `agent/nodes/plan.py` against the `TypedDict`s — verify: `test_plan.py::test_plan_nodes_write_only_own_keys` and the type-check command — evidence: returned key sets as stated; type check clean.
- [ ] AC-8 [negative] What crosses the line (DO-4 §3): on a WP-2 conversation (the test builds "my name is Omar Patel", MHC-10002, INV-204411, a phone and a synthetic card-like number from parts, plus a prior code turn) the planner's captured `ChoiceRequest` holds only the JEV-redacted latest message, the recent chat and `StateFlags`; the classifier's holds the latest message only; neither holds the customer ID, invoice ID, phone, introduced name, code, card-like number, any passage or any tool output; and no `classifier` check event or `signal` record holds message text — verify: `tests/unit/agent/prompts/test_routing_prompts.py::test_requests_cross_only_planner_input` — evidence: seeded values absent from both captured requests, from the check events and from the `meridian.signal` log capture; placeholders `[name]`, `[phone]`, `[customer id]`, `[invoice id]` present.
- [ ] AC-9 [invariant] Turn-2+ full prompt (context-management rule 3): a recording fake choice model drives the planner on turns 1, 2 and 5 of a WP-3 conversation; the system text and every field's instructions and options are identical and complete on each turn; `recent_chat` is ≤ 6 lines × 400 chars with the oldest dropped first (rule 4); the same phone number renders to the same `[phone]` placeholder on turns 1 and 5 (rule 5; data.md §1) — verify: `tests/unit/agent/prompts/test_routing_prompt_turns.py::test_stable_prefix_turns_1_2_5` — evidence: three captured requests; prefix and field hashes equal; window within the cap.
- [ ] AC-10 [capture] Records for the turn row and the check-event table: `PlannerOutcome` carries `model`, Jev `probabilities`, `fallback_used` and `failure`; `DangerAssessment` carries `confidence` and `failure`; `Plan` carries `mode`, `source`, task intents, `handoff_request`, `topic` and `planner_failed` (every `PlannerTrace` field AEA-21's `turn_trace` copies, graph-core §2); `check_events` holds exactly one `classifier` event per classifier run — verify: `test_plan.py::test_outcomes_carry_provenance_for_turn_trace` — evidence: fields populated from the doubles' answers; Sonnet fallback `confidence` is `None`, never invented (DO-4 §0); one event per run.
- [ ] AC-11 [journey] Extends J-5 (slice plan §0a journey map): DANGER through CON-2 reaches the safety path by the classifier raise (gate `free_text`, two Jev routing calls, no specialist or responder call, the instruction first, a P1 case row) and NODANGER books normally with no case, asserting what the user sees and what is stored, in `tests/journeys/j5/test_aea_37.py` with the scripted model adapter — verify: `uv run pytest -m journey tests/journeys/j5/test_aea_37.py` — evidence: both steps pass at level `integrated with a scripted model`; until AEA-57's harness and AEA-51's J-5 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-37.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-12 [regression/context] In the same change: the area-map row A7d for `agent/nodes/plan.py` and `agent/prompts/routing.py` (planned → actual + commit), the ICM progress row *Routes verified against code and tests*, DO-3 §3's rows for those two files marked built — verify: `git diff --name-only` — evidence: those docs in the diff, only this ticket's rows changed.

### Observability

- Responsibilities: WF-1 (customer chat turn, its internals; DO-6 emitters "planner, danger classifier"). This ticket emits
  one `classifier` `check_event` per classifier run and a `brake` event for `BRAKE_TASKS` into the `check_events` state key
  (graph-nodes §1; `run_graph` hands them to `TurnService` in `GraphOutcome.check_events`, which persists them, AEA-40);
  the `signal` LOG records `planner_fallback`, `classifier_fallback` and `brake_fired` (graph-nodes §4; web.md §10); and the
  planner decision, plan and danger raise in state, which AEA-21's `turn_trace` copies into the `turn` row
  (`TurnTrace.planner`, `danger_raised`, `gate_result = danger` / `burning_unclear` on a raise; graph-core §2). Planner,
  classifier and fallback `model_call` spans and `spend_ledger` rows come from the gateway (AEA-20); node spans from
  `timed_node` (AEA-21). Codes only: no message text in any event, signal or span.
- Capture evidence: AC-10 and AC-2 at component level (state, events and signal capture), AC-8 for the forbidden values.
  CAP-2 (AEA-51) drives CON-2 with DANGER at the real entry point and asserts `gate_result = danger`, a P1 case, only the two
  parallel Jev routing spans before the instruction and no identity or lookup step (graph-nodes §7).

### Evaluation

- Checks: E-5 danger recall (100% on labelled synthetic danger cases [T]) and false alarms (≤ 10% on no-danger comfort
  cases [T]); E-1 trajectory (which specialist, in order) for WP-1…WP-8; E-3/E-4 escalation recall and false escalation
  depend on `handoff_request` from this join; one late-technician transcript among the planner cases (graph-core closing
  table *cases A-6*, [A]: SP-1 never measured `late_technician`). Kept passing at AEA-51 with fake models; scored at Stage 9.
- Expected-answer authority: R-8's rule for the danger labels on synthetic cases ("someone is in danger because of the
  conditions"); the gold labels fixed in each case file; Innocent's WP-3 decision; the D4 table for handoff reasons (DO-5
  *Expected-answer authority*).

### Metrics

- References: WF-1 inherits M-1, M-3, M-4, M-6, M-7, M-8, M-9, M-14, M-16, M-17, M-18, M-19, M-20, M-21, M-22, M-23, M-24,
  M-25, M-26, M-29. **Affected here:** M-16 (danger recall: `classifier` / `raised` with `turn.gate_result`), M-17 (false
  alarms; per-turn denominator = `classifier` events, one per run, so `pass` is recorded too, graph-nodes §1), M-3 and M-4
  (live rate and scope by planner topic, from `TurnTrace.planner.topic`; an estimate), M-19 and M-20 (escalation recall and
  false escalation depend on `handoff_request`), M-23 (latency: two Jev calls in one superstep, ≈ 0.2 s each on mix B, SP-1
  §3 [M]), M-24 (a `planner_failed` turn ends `degraded_handoff` / `model_error`), M-25 and M-26 (the Sonnet fallback's cost
  is recorded by the gateway). **Kept computable, not changed by this ticket:** M-1, M-6, M-7, M-8, M-9, M-14, M-18, M-21,
  M-22, M-29.
- Acceptance conditions: the classifier events and the `PlannerTrace` fields stay recordable from state (AC-10); M-16 and
  M-17 stay computable from the persisted `classifier` events. No target set or changed here.

### Blocked by

AEA-11, AEA-12, AEA-21 (slice plan). Calls (injected): `ModelGateway` (AEA-20) through `GraphDeps.gateway`, tested with a
double honouring DO-4 §12 and models.md §5.

### Agent handoff

- Area / owner: A7d Front (`agent/nodes/plan.py`, `agent/prompts/routing.py`).
- Contracts and shared surfaces: consumes `ModelGateway.choose` (AEA-20, double), `GateDecision` and `RuleMatches`
  (AEA-05, AEA-12), `redact` with `RedactionProfile.JEV` (AEA-04), `Limits.brakes` and `Limits.context` (AEA-01),
  `CheckEvent` builders, `SignalRecord`, the `*Update` types and `Plan.planner_failed` (AEA-02), `emit_signal` and
  `timed_node` (AEA-21). Produces the state keys `planner`, `danger`, `plan` and `check_events` entries for AEA-21's routers
  (danger first; edge 1 `planner_failed and not tasks` → escalation) and `turn_trace`, AEA-39 (fan-out; escalation reads
  `plan`) and AEA-38 (facts reads `plan`). Must not edit `routers.py`, `gates/*`, `gateway.py`, `domain/*`, other node files.
- Scope boundary / refusal: no routing edges (AEA-21), no safety reply or case (AEA-36), no specialist calls (AEA-39), no
  priority (AEA-14); card choices, code entry, person, safety and paused turns never reach these nodes (the gate routes them).
- Awaiting Innocent: DAT-1 — built on the recommended option (A: introduction patterns and the street-address pattern in
  `redact`); AC-8's name case uses an introduction ("my name is …"). If he picks B, the gateway (AEA-20) passes the located
  customer's values to `redact` and AC-8 gains a non-introduced name case; if C, only AEA-04 changes. This ticket's code
  does not change either way.
- Wave and gates: wave 2; no gate.
- Lane: build-loop — it changes source and tests (`ticket-lanes.md`).
- Risk: None per the slice plan (raw caller text reaches Jev only after JEV redaction, AC-8).
- Entry points added or changed: None — WF-1 internals only (its CON-1/CON-2 entry is AEA-40).
