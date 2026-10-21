## [AEA-36] graph: front node (gates, safety, identity)

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

> **US-3:** "As a **homeowner** who smells gas, hears a CO alarm or sees sparks, smoke or flames, I need the safety
> instruction before anything else, so that I leave the home before I'm asked for a name or an account." (Also US-2,
> US-4, US-5, US-8.)

**Example pair (WP-5).** Input: "My carbon monoxide detector is going off." → the gates node returns `GateDecision(kind=
SAFETY, rules.safety=CO)` and one `gate` check event; the safety node makes **no model call and no identity or lookup
call**, emits `safety_reply_sent`, and opens a **P0** case by code through `deps.handoff.open(HandoffRequest(trigger=
"safety", reason=SAFETY, priority=P0, safety_kind=CO, …), ctx)` with no follow-up time promised (R-6; `R26.safety_none`).
The reply's first text is the KB instruction word for word ("Please leave the home immediately and call 911 or your gas
utility from outside. Don't flip any light switches, open windows near the furnace, or restart any equipment."),
rendered by compose (AEA-21) from `policy/texts.py` (AEA-03).

**Second pair (WP-6).** "I need to schedule a service call. I smell something burning from the vents." → gate
`BURNING_ASK`, `burning_card_id = "burn-<turn_id>"`, no case; compose shows the R-7 `burning_check` card (never "go and
check"). The answer `not_sure` on that card → `BURNING_ANSWER`, `unsure` → the safety node opens a **P1**
`burning_unclear` case. The answer `no` → the gates node writes a code-built booking plan instead (below).

**The behaviour.** `agent/nodes/front.py` replaces AEA-21's stub with three node functions, exactly the signatures of
`docs/design/contracts/stage7/graph-nodes.md` §9.3 (`fn(state, runtime: Runtime[TurnContext], *, deps) -> <Update>`, each
returning only the keys its `TypedDict` names, §9.1):

- **`gates(...) -> GatesUpdate`**: on every turn, first, `decide_gate(ctx.intake, flags_from_state(state))` (AEA-12; order
  per graph-core §3), so a safety phrase mid-chat or with typos comes first (R-5, R-47). Returns `gate`; one gate check
  event `CheckEvent.from_gate(turn_id, gate)` in `check_events` (graph-nodes §1, GRN-2, GRN-5); `burning_card_id` set to
  `burning_card_id(turn_id)` on `BURNING_ASK` and to None on every other result (graph-core §3, GRC-4: this node is its
  only writer); and, **only** when `gate.kind == BURNING_ANSWER` and `burning_answer == "no"`, the code-built `plan` of
  graph-nodes §6 (GRN-6, GRC-18): `Plan(mode="act", tasks=(PlannedTask(order=1, specialist="scheduling",
  intent=BOOK_NEW, needs_identity=True),), handoff_request=HandoffReason.BURNING_RULED_OUT, topic="booking",
  source="rules_only")`. `needs_identity=True` is the value `join_plan` gives a `BOOK_NEW` task (the `book` tool requires a
  verified customer, DO-4 §5 `requires_verified`); the reason value is CAS-16 option A (see Agent handoff). AEA-21's gates
  router then sends that plan through `route_act_plan` (identity first if needed, else the specialists fan-out).
- **`safety(...) -> SafetyUpdate`**: runs for gate `SAFETY`, `BURNING_ANSWER` `yes` or `unsure`, `DANGER_RULE`, and a
  classifier raise routed from `plan_join` (AEA-37). It makes no model call, no identity call and no lookup, never asks
  for contact details (R-6), and emits `safety_reply_sent` (cause = the turn's gate result: `state.danger.label` when the
  classifier raised, else `gate.gate_result()`; graph-nodes §4) through AEA-21's `emit_signal`. It then opens the case by
  code with `deps.handoff.open(HandoffRequest(...), ctx)` (AEA-29): `thread_id`/`turn_id` from `ctx.ids`; `trigger =
  "safety"`; `identity = state.identity`; `safety_kind = gate.rules.safety` when a safety rule matched, else None; `reason`
  `safety` for `SAFETY` and burning `yes`, `danger` for `DANGER_RULE` and a classifier `danger`, `burning_unclear` for
  burning `unsure` and a classifier `burning_unclear`; `priority = priority_for(reason)` (AEA-14, cases.md §3.3: safety
  P0; danger, burning_unclear P1); `rule_id` = the first fired rule id (`gate.rules.rule_ids`, AEA-05) or, where no rule
  fired (a classifier raise, an `unsure` answer), a stable id the plan names. If `open` raises it retries once; if the
  retry raises too it returns with no `HandoffResult` and no halt, so compose still renders the instruction (DO-1 §8.2
  *Safety turn*); either way after a failed first attempt it emits `case_write_failed` (`attempt = 2`, `recovered` =
  whether the retry wrote the case, cause `write_error`). Under GRC-3 option A a safety turn while `controller = human`
  also reaches this node; `HandoffService` is idempotent per thread, so the representative's open case is returned
  (`created = False`) and no second case opens; the customer message reaching the representative is AEA-40's.
- **`identity(...) -> IdentityNodeUpdate`**: for gate `LOCATE`, `Locator.from_form(ctx.intake.form)` (graph-tools §5,
  GRT-5) then `deps.identity.locate(thread_id, locator, ctx.now)`; on `Located`, `deps.identity.send_code(thread_id,
  ctx.demo_session, ctx.now)` in the same turn; a form with no complete locator (`from_form` → None) reaches no service and
  gives the same `NotVerified` step (R-16: identical for every cause). For gate `CODE_ENTRY`: with `ctx.intake.code_digits`
  → `deps.identity.verify(ctx.ids, digits, ctx.now)`; with the `new_code` choice on the code card → `send_code`.
  `identity_step` = the service's result as returned (`CodeSent`, `NotVerified`, `CodeCapReached`, `Verified`,
  `CodeWrong`, `CodeExpired`, `CodeLocked`; graph-tools §5), never re-grouped: compose maps each to its CON-2 code
  (`NOT_VERIFIED`, `CODE_WRONG`, `CODE_EXPIRED`, `CODE_LOCKED`, `CODE_CAP_REACHED`) and graph-core §8 counts `NotVerified`
  and `CodeWrong`. Then `identity` = `tx.core.reads.identity_state(thread_id)` in a short read-only `deps.uow()` after the
  service's own write. The digits and the form values are read only from `ctx.intake` (never checkpointed) and never copied
  into state, a return value, a log or a trace (R-15; graph-core §2 rules 1–3, GRC-10).

Routing between the nodes is AEA-21's routers; every text (safety, danger, burning question, identity prompts) is composed
by AEA-21's compose from `policy/texts.py` (AEA-03). This ticket chooses no wording.

### Source

- `docs/design/contracts/stage7/graph-nodes.md` §1 (`CheckEvent.from_gate`), §4 (`SignalRecord`, `safety_reply_sent`,
  `case_write_failed`), §6 (burning "no"), §7 (CAP-2 per path), §9.1 (`GatesUpdate`, `SafetyUpdate`,
  `IdentityNodeUpdate`), §9.3 (signatures); `stage7/graph-core.md` §2 (`TurnInput`, `TurnContext.intake`, rules 1–4), §3
  (`GateFlags`, card ids, `burning_card_id`, `decide_gate` order), §4 (`GraphDeps`, `timed_node`, `agent/signals.py`), §8
  (`identity_failures`), §11 (`check_events`, edge 2, `route_act_plan`); `stage7/graph-tools.md` §5 (`Locator`, identity
  result types, CON-2 codes, `reads.identity_state`); `stage7/cases.md` §1.2 (`reads.identity_state`), §3.2–§3.3
  (`promise_for`, `priority_for`), §5 (`HandoffService.open`, idempotent per thread); DO-4 §1, §3, §7 (`HandoffRequest`,
  `HandoffResult`), §11 failure table, §14 (`IdentityService` signatures), §16.
- Decisions: `docs/plans/7b-decisions/graph-core.md` GRC-3 (Innocent; interim A), GRC-4, GRC-5, GRC-6, GRC-10, GRC-18;
  `graph-nodes.md` GRN-2, GRN-4, GRN-5, GRN-6, GRN-9, GRN-11; `graph-tools.md` GRT-3, GRT-5; `cases.md` CAS-16
  (Innocent; built on A); `residuals-graph.md` R-G-11 (`GatesUpdate.burning_card_id`).
- DO-3 §3 (`agent/nodes/front.py`), §5.3 (key ownership: `gate`; `handoff` by `safety`; `identity_step`; `identity` again
  after a DB write), §5.4 (skeleton), §7 rows R-5, R-6, R-7, R-8, R-15, R-16.
- DO-2 `system-design.md` §A.1 (code gates, safety reply rows), §8.2 (*Safety turn* row), §8.3 (*Safety instruction: answer
  always*); `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md` §9.2 (burning smell, D2).
- PRD R-2, R-5, R-6, R-7, R-8, R-15, R-16, R-47; HP-2; WP-5, WP-6 (✓ Innocent 2026-10-20), WP-2 (identity steps).
- `docs/design/contracts/api-con-mapping.md` §0 (a locate form is routed by code, no model sees the phone).
- Router rows: area map A7d Front; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Everything the agent cannot handle must escalate cleanly to a human" and "Do not let the agent
  guess. A confident wrong answer is worse than a handoff"; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] The gates node runs `decide_gate(ctx.intake, flags_from_state(state))` on every turn and returns only `GatesUpdate` keys: a CO phrase with a typo ("my carbon monoxid alarm is going off") on turn 5 of a booking conversation with an open task yields `SAFETY` ahead of the open task — verify: `tests/unit/agent/nodes/test_front.py::test_gate_first_every_turn_mid_chat` (AEA-12's real `decide_gate`) — evidence: `gate.kind == "safety"`; returned keys ⊆ {`gate`, `check_events`, `burning_card_id`}.
- [ ] AC-2 [invariant] Gate check event and burning card (GRN-5, GRC-4): every gates run returns exactly one `CheckEvent` with `check="gate"`, this turn's id and `codes = (GateKind value, *rule_ids)` (`fired` for WP-5, `pass` for plain free text); `burning_card_id` is `"burn-<turn_id>"` after `BURNING_ASK` and None after any other gate — verify: `test_front.py::test_gate_event_and_burning_card_id` — evidence: event fields per case; card id set then cleared.
- [ ] AC-3 [invariant] Burning "no" (GRN-6, GRC-18): a `no` choice on a `burn-` card returns the code-built plan (one scheduling `BOOK_NEW` task, order 1, `needs_identity=True`, `handoff_request = burning_ruled_out`, topic `booking`, source `rules_only`), and no other gate result writes `plan` — verify: `test_front.py::test_burning_no_writes_code_built_plan` — evidence: plan fields equal; `plan` absent from every other case's return.
- [ ] AC-4 [invariant] WP-5: the safety node calls `deps.handoff.open` once with `trigger="safety"`, `reason="safety"`, `priority="P0"`, `safety_kind="co"`, and makes zero gateway, identity-service and lookup calls — verify: `test_front.py::test_wp5_safety_p0_no_model_no_identity` (recording doubles for every `GraphDeps` field) — evidence: 1 handoff call; 0 gateway, 0 identity, 0 retrieval and 0 dispatcher calls; returns the `HandoffResult`.
- [ ] AC-5 [invariant] Safety paths (WP-6, R-7, R-8): burning `yes` → P0 `safety`; burning `unsure` → P1 `burning_unclear`; `DANGER_RULE` → P1 `danger`; a routed classifier raise with label `danger` → P1 `danger`, with label `burning_unclear` → P1 `burning_unclear`; `BURNING_ASK` never reaches the safety node and opens no case — verify: `test_front.py::test_burning_and_danger_paths` (table-driven, AEA-14's real `priority_for`) — evidence: one row per path with reason and priority as stated.
- [ ] AC-6 [failure/refusal] A failing case write is retried once: when the retry succeeds the node returns its `HandoffResult` and emits `case_write_failed` with `attempt=2`, `recovered=True`; when both attempts raise the node returns normally with no `HandoffResult` and no `halt`, emits `case_write_failed` with `recovered=False`, and `safety_reply_sent` is still emitted — verify: `test_front.py::test_safety_case_write_retried_once_instruction_kept` (caplog on `meridian.signal`) — evidence: 2 handoff attempts per case; signal records as stated; no exception.
- [ ] AC-7 [invariant] GRC-3 option A: with `controller.kind == "human"`, a CO-alarm turn reaches the safety node, `deps.handoff.open` is called once and the double's idempotent result (`created=False`, the existing case reference) is returned; no second case — verify: `test_front.py::test_safety_while_representative_owns_chat` — evidence: one open call; `created` False; same case reference.
- [ ] AC-8 [invariant] Identity, WP-2: a locate form for Omar Patel → `Locator.from_form` → `locate` → `send_code` in one turn; `identity_step` is the `CodeSent` result with masked hint "the phone ending in 02"; a later code turn → `verify(ctx.ids, digits, ctx.now)` → `identity_step` `Verified`; after each service call `identity` equals `core.reads.identity_state(thread_id)` read in a read-only unit of work — verify: `test_front.py::test_wp2_locate_send_verify` (identity-service double; AEA-10's `temp_sqlite()` seeded with the identity rows) — evidence: call order locate → send_code → verify; step and state as stated.
- [ ] AC-9 [failure/refusal] Identity outcomes are passed through, never re-grouped: no match, an ambiguous match, no usable contact and an incomplete form (`from_form` → None, no service call) all give a `NotVerified` step that serialises byte-identically; `CodeWrong(tries_left)`, `CodeExpired`, `CodeLocked` and `CodeCapReached` come back as the service returned them; a `new_code` choice calls `send_code`, not `verify` (GRT-3, GRT-5) — verify: `test_front.py::test_identity_results_passed_through` — evidence: the four `NotVerified` serialisations equal; each other type unchanged; call made per case.
- [ ] AC-10 [negative] The code digits and the locate form's phone and name never enter state, a return value, a signal or a log: after a code turn and a locate turn (a synthetic code and a phone built in the test, never literals), the serialised graph state, every value the three nodes return and every captured log record (including `signal` records) contain neither, and the gateway double recorded no call — verify: `test_front.py::test_code_and_form_values_never_leave_intake` (caplog) — evidence: both sentinels absent; 0 gateway calls. (The checkpoint-wide sentinel test of graph-core §2 rule 4 is AEA-51's.)
- [ ] AC-11 [invariant] Key ownership (DO-3 §5.3, graph-nodes §9.1): `gates` returns only `gate`, `check_events`, `burning_card_id` and (burning "no" only) `plan`; `safety` only `handoff` (or nothing); `identity` only `identity_step` and `identity`; none writes a planner, reply, durable-task or `settled` key — verify: `test_front.py::test_front_nodes_write_only_own_keys` — evidence: returned key sets as stated.
- [ ] AC-12 [capture] Records for WF-1: the gates node's `gate` check event (codes only, never text) and the safety node's `safety_reply_sent` record carry `turn_id`, `thread_id`, `request_id`, `run_tag`, `node="safety"` and the gate-result cause (WP-5 → `safety`; DANGER_RULE → `danger`), and a sentinel phrase in the customer's message is absent from both — verify: `test_front.py::test_check_event_and_signal_records` (caplog on `meridian.signal`) — evidence: record fields as stated; sentinel absent. (Real-entry-point capture: CAP-2 in AEA-51 — no model span before the reply for WP-5; only the two Jev routing spans for DANGER, graph-nodes §7.)
- [ ] AC-13 [journey] Extends J-5 (slice plan §0a journey map; backend-amendments §3): a CO-alarm message gets the approved instruction as the first reply text and a P0 case row, before any specialist runs; asserting what the user sees and what is stored, in `tests/journeys/j5/test_aea_36.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j5/test_aea_36.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-36.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-14 [regression/context] Docs updated in the same change; context-management rule 3 does not apply (these nodes render no model prompt; stated in the plan) — verify: `git diff --name-only` — evidence: `.claude/reference/area-map.md` A7d row (`agent/nodes/front.py` planned → actual with the commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 `nodes/front.py` status planned → built, all three in the diff with only this ticket's rows changed.

### Observability

- Responsibilities (WF-1): one `gate` check event per turn through `check_events` (persisted by AEA-40 from
  `GraphOutcome.check_events`; DO-6 *Records* `check_event` "which gate or check fired"); the gate decision that compose's
  `turn_trace` turns into `turn.gate_result` (graph-core §2); the signal records `safety_reply_sent` and
  `case_write_failed` through `emit_signal` (graph-nodes §4, GRN-4; codes only); the P0/P1 `case`, `case_event` and
  `promise` rows written by `HandoffService` (AEA-29) in one transaction; no `model_call` span on the safety path (CAP-2).
  Node spans come from AEA-21's `timed_node`; these nodes never call `TraceSink`.
- Capture evidence: AC-12 (records), AC-4 (no model call before the case), AC-10 (no code or phone); CAP-2 (AEA-51) drives
  CON-2 with WP-5 and DANGER at the real entry point and asserts no identity or lookup step before the instruction.

### Evaluation

- Checks: E-5 safety and danger slice (the safety instruction is the first text; no identity, lookup or case step before
  it; danger cases get the emergency number first and a P1 case), E-1 WP-5 and WP-6 hard gates, and E-1's "nothing
  private before the code turn" for WP-2, kept passing at AEA-51.
- Expected-answer authority: KB `policies/escalation_and_safety.md` for the words; PRD R-5–R-8, R-47 and Innocent's
  decisions (WP-6 ✓ 2026-10-20) for the paths; R-15, R-16 and the UX-3 named errors for identity (DO-5
  *Expected-answer authority*).

### Metrics

- References: M-14 (safety instruction first), M-15 (person on the first request: `turn.gate_result = person_requested`),
  M-16 (danger recall), M-17 (false alarms: `gate` and `classifier` check events per turn), M-21 (nothing private before a
  correct code), M-22 (handoffs by reason).
- Acceptance conditions: `turn.gate_result` and the `gate` check event stay computable from what this ticket leaves in
  state (AC-2, AC-12); P0/P1 cases are rows written by AEA-29. No target set or changed here.

### Blocked by

AEA-11, AEA-12, AEA-14, AEA-21 (slice plan row). Calls (injected): `IdentityService` (AEA-27) and `HandoffService`
(AEA-29) through `GraphDeps`, as doubles honouring DO-4 §14, §7 and graph-tools §5. The `[journey]` AC-13's integrated
level only (not this ticket's merge): AEA-57 (harness) and AEA-51 (lands J-5, wave 3).

### Agent handoff

- Area / owner: A7d Front; owns `src/meridian/agent/nodes/front.py` (replacing AEA-21's stub in place) and
  `tests/unit/agent/nodes/test_front.py`.
- Contracts and shared surfaces: consumes `decide_gate`, `flags_from_state`, `burning_card_id` (AEA-12), `priority_for`
  (AEA-14), `GatesUpdate`/`SafetyUpdate`/`IdentityNodeUpdate`, `CheckEvent.from_gate`, `SignalRecord`, `HandoffRequest`,
  `Locator` and the identity result types (AEA-02), `emit_signal` and `timed_node` (AEA-21), `core.reads.identity_state`
  and `temp_sqlite()` (AEA-10), fakes (AEA-11). Produces `gate`, `check_events`, `burning_card_id` and the burning-"no"
  `plan` for AEA-21's routers and compose and AEA-37; `handoff` for AEA-38 (facts) and AEA-21 (compose); `identity_step`
  and `identity` for AEA-38 and AEA-39 (escalation rule 5). Must not edit `agent/{graph,routers,context,signals}.py`,
  `agent/nodes/compose.py`, `policy/*`, `gates/*`, `domain/*` or other node files. `GatesUpdate` carries
  `burning_card_id: str | None` (graph-nodes §9.1, R-G-11; AEA-02 writes it in wave 0), so this node, the key's only
  writer (graph-core §3), returns it directly.
- Scope boundary / refusal: no wording (compose and `policy/texts.py`), no person-request handoff (the `PERSON` gate routes
  to AEA-39's escalation and handoff nodes), no planner or classifier (AEA-37), no booking (the burning-"no" plan only
  hands the task to the specialists), no priority table (AEA-14).
- Awaiting Innocent: GRC-3 — built on the recommended option A (safety before AI-paused: a safety message while a
  representative owns the chat reaches this node, AC-7); if he picks B, AEA-12's tuple flips and AC-7 is replaced by an
  `AI_PAUSED` case that never reaches the safety node; if C, burning and danger-word turns under `controller = human` also
  reach these nodes and AC-7 gains those rows.
- Awaiting Innocent: CAS-16 — built on the recommended option A (reason `burning_ruled_out`, added to `HandoffReason` by
  AEA-02; P2 by AEA-14's `priority_for`); AC-3 asserts the reason only, never a priority. If he picks C, nothing changes
  here (only AEA-14's row); if B, the plan's `handoff_request` becomes the reason that option carries and AC-3's expected
  value changes with it.
- Evidence level (`.claude/rules/integrated-journeys.md` §4): the node tests are `mock-tested`; the J-5 journey step
  (AC-13) records `mock-tested` and `Blocked by: AEA-57, AEA-51` until both merge.
- Wave and gates: wave 2; no gate.
- Lane: build-loop — it changes source and tests (`ticket-lanes.md`).
- Risk: security (`risk::security`, slice plan row) — the identity node handles the verification code and the locate
  form's name and phone (R-15); a bug could put them in state, the checkpoint or a log, or verify the wrong customer.
  Frozen failing tests first (AC-8, AC-9, AC-10 at least) and the security agent at the wave-2 merge.
- Entry points added or changed: None
