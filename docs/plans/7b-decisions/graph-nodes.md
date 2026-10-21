# 7b decisions: graph, nodes part (GRN)

**Topic:** graph (split core GRC / tools GRT / nodes GRN); this part covers items AEA-15-1, 15-2, 15-3, 35-4, 36-2,
36-3/37-3, 36-4, 37-1, 37-4, 38-2, 38-5, 39-1, 51-1. **Date:** 2026-10-21. **Status:** resolutions for the Stage 7b
ticket specs; nothing built.
**Signatures and types:** [`docs/design/contracts/stage7/graph-nodes.md`](../../design/contracts/stage7/graph-nodes.md)
(cited below as "contract §n"). **Evidence sweep:** [`graph-evidence.md`](graph-evidence.md), the headings above only; the
quotes relied on were re-checked in `internal-components.md` §6–§11, `observability-contract.md` (*Records*, CAP-2),
`system-design.md` §8.2 and SDQ-6, `code-design.md` §5.4, `hard-problems.md` HP-2, PRD R-5, R-7, R-8, R-47, and
`key-metrics-registry.md` M-12, M-16, M-17, M-24.
**Finished sibling addenda followed (read, not edited):** `cases.md` (CAS-15 rule 6, CAS-16, the reset table listing
`check_events`), `web.md` (WEB-11 and WEB-18: DO-1 §8.2 signals without a DO-6 record become LOG records, no table).

**Who decides** (rule `system-design-questioning` 3): a source settles it → **Source**; an interface, name, home or
internal type → **Eng** [Decided §7, engineering]; what to build, spend, which risk to accept or what the customer is
told → **Innocent**.

**Counts.** 13 ticket items collapse to **9 distinct items** (the five "DO-6 has no record" items are one; 36-3 and 37-3
are one). **Source-settled 2 · Engineering 6 · Innocent 0 new** (GRN-6's priority is CAS-16, already open for Innocent
in `cases.md`; referenced, not re-asked). GRN-10 (engineering) was added at the merge from graph-tools C-11.

---

## For Innocent

Nothing new. GRN-6 (AEA-36 item 2) is the routing half of **CAS-16** ("what priority does a burning smell get once both
dangers are ruled out?"), which `cases.md` already puts to Innocent with options and a recommendation. One answer serves
both tickets; the routing below does not depend on which level he picks.

---

## Resolutions

| ID | Question | Raised by | Resolution | Basis | Text the ticket should carry |
|---|---|---|---|---|---|
| GRN-1 | "Done" names no `ActionKind`: how can "Done, your visit is booked" pass? | AEA-15 #1 | **Eng.** `GENERIC_COMPLETION_WORDS` ("done", "all set", "taken care of", …) inline in `checks.py`. A generic word is a completion claim with `action_kind=None`; it passes only when the same sentence also holds a kind-specific completion claim that passes. "Done, your visit is booked" passes (BOOKED backed); "Done, auto-renew is off" and a bare "Done!" are removed (`no_completed_action`). Contract §2. | SDQ-8 A (Innocent 2026-10-21: a claim passes when `settled` holds "an action of the matching kind"); HP-4 :264 "Never 'Done, auto-renew is off'"; removal is the safe direction (CLAUDE.md "a confident wrong answer is worse than a handoff") | AEA-15 #1: "Settled (GRN-1): generic completion words pass only beside a backed kind-specific claim in the same sentence; add AC `test_checks.py::test_generic_done_needs_backed_kind` ('Done, your visit is booked' with a BOOKED action kept; WP-8's 'Done, auto-renew is off' removed; bare 'Done!' removed)." |
| GRN-2 | Who builds `CheckEvent` from a `CheckResult` (and from gates, the classifier, a brake)? | AEA-15 #2; AEA-36 Obs.; AEA-37 Obs.; AEA-38 AC-11 | **Eng.** Pure classmethods on `CheckEvent` in `domain/turn.py` (AEA-02): `from_check`, `from_gate`, `from_danger`, `from_halt`. AEA-38 calls `from_check`; AEA-36 `from_gate`; AEA-37 `from_danger`; the node that writes a BRAKE_* halt calls `from_halt`. R-46 events travel in `checked.events` (unchanged); the others in a per-turn state key `check_events` (graph-core). `TurnService` persists both. Contract §1. | DO-4 §10 gives `CheckEvent` and `CheckResult` but no builder; DO-4 §14 step 7 "persist … check events"; putting the builder in `domain/` means AEA-36/37 need no dependency on AEA-15 (slice plan rows: 36 and 37 do not depend on 15) | AEA-15 #2: "Settled (GRN-2): `CheckEvent.from_check` (AEA-02, `domain/turn.py`); `checks.py` builds no events." AEA-38: "Build R-46 events with `CheckEvent.from_check` (GRN-2)." |
| GRN-3 | Where the brief's quote check lives (`quote_not_found`, `brief_quote`) | AEA-15 #3 | **Eng.** In `checks.py` (AEA-15): `check_quotes(extraction, shown) -> QuoteCheck`; `shown` is message_id → the exact text the extraction call was given for that customer message. `Claim.kind` gains `"quote"`. AEA-38's checks node calls it and emits `brief_quote`. Contract §2. | DO-4 §10 last bullet "every `Quote` must be an exact substring of its message"; `Removal.reason` already has `quote_not_found`; `checks.py` is the R-46 module (code-design tree, A7c). Matching against the text the model saw avoids false removals when masking changed the stored text | AEA-15 #3: "Settled (GRN-3): `check_quotes` lives here; add AC `test_checks.py::test_quote_must_be_exact_substring` (an altered word or a non-customer message id → `quote_not_found`)." AEA-38: "Run `check_quotes` before `attach_extraction` (GRN-3, GRN-8)." |
| GRN-4 | DO-6 names no record for the DO-1 §8.2 signals `safety_reply_sent`, `case_write_failed`, `classifier_fallback`, `planner_fallback`, `specialist_failed`, `brake_fired`, `responder_fallback`, `brief_failed` | AEA-35-4, AEA-36-4, AEA-37-4, AEA-38-5, AEA-39-1 | **Eng.** One structured LOG record `signal` (`SignalName`, `SignalRecord` in `domain/turn.py`, AEA-02; `emit_signal` in `agent/signals.py`, AEA-21), IDs and codes only, no table. Emitters: AEA-36 (`safety_reply_sent`, `case_write_failed`), AEA-37 (`classifier_fallback`, `planner_fallback`), AEA-39 (`specialist_failed`, `brake_fired` from specialist results), AEA-38 (`responder_fallback`, `brief_failed`, and `brake_fired` when the gateway halts the responder or brief). `run_specialist` (AEA-35) emits nothing; it fills `brake` / `failure` on its result. A brake also writes a `brake` check event. M-24 keeps reading `turn.degrade_reason`. Contract §4. | DO-1 §8.2 names the signals and A.9 says they are DO-6's inputs; DO-6 *Records* has no row for them but lists "brake" under `check_event`; web.md WEB-11/WEB-18 set the storage rule for a §8.2 signal with no DO-6 record (LOG record, no table); DO-7 M-24 is defined on `turn.degrade_reason` | AEA-35 Obs.: "Settled (GRN-4): the runner emits no signal; it returns `brake` and `failure` on the result for AEA-39." AEA-36 / 37 / 38 / 39 Obs.: "Settled (GRN-4): emit `<signals>` with `emit_signal` per contract graph-nodes §4; add one test per signal asserting the record's name and cause, and that no message text appears in it." |
| GRN-5 | `CheckEvent` kinds for the gate and the classifier raise | AEA-36 #3, AEA-37 #3 | **Eng.** `CheckEvent.check` gains `"gate"`, `"classifier"`, `"brake"`; `result` gains `"fired"`, `"raised"`; a new `codes` field carries stable codes (gate kind + rule ids; classifier label or failure kind; halt reason + node). One `gate` event every turn; one `classifier` event every classifier run, `pass` included, so M-17's per-turn denominator exists. Contract §1. | DO-6 *Records*: `check_event` = "which gate or check fired (code gate, R-46 completion or fact check, R-47 classifier raise, brake), its input IDs and result"; DO-7 M-16 and M-17 read "`check_event` (classifier raise)", M-17 segmented per turn | AEA-36 #3 and AEA-37 #3: "Settled (GRN-5): `gate` / `classifier` check events via `CheckEvent.from_gate` / `from_danger`; AEA-37 AC: a non-raising run still records `classifier` / `pass`." |
| GRN-6 | R-7 "both ruled out → urgent booking plus a priority case": the skeleton sends every `burning_answer` to `safety`, and no source names the priority | AEA-36 #2 (= CAS-16) | **Routing: Eng.** `burning_answer == "no"` goes to the specialists fan-out with a code-built plan (one scheduling `BOOK_NEW` task, `handoff_request` = CAS-16's reason, `source="rules_only"`); "yes" and "unsure" keep going to `safety`. **Reason and priority: Innocent, CAS-16** (not re-decided). Contract §6. | PRD R-7 and consolidated §9.2 step 4 decide the behaviour (booking + case), so an edge to the specialists is needed; DO-3 §5.4 has none; cases.md CAS-16 holds the level | AEA-36 #2: "Routing settled (GRN-6): `burning_answer='no'` → specialists fan-out with the code-built plan in contract graph-nodes §6. Reason and priority open for Innocent (CAS-16); no AEA-36 test asserts a level until answered." |
| GRN-7 | Both planners fail and neither a rule nor the open task gives a plan: handoff reply (DO-1 §8.2) or run on rules and the open task (DO-4 §4)? | AEA-37 #1 | **Source.** A handoff reply. The two sources agree once read together: rules and the open task still run first (DO-4 §4); when they give nothing, `join_plan` returns `Plan(mode="act", tasks=(), source="rules_only", planner_failed=True)`, the router sends it to `escalation`, and rule 6 escalates `degraded=True`, `ai_failure` → P3, `degrade_reason = model_error`, as for a failed specialist. Contract §5. | DO-1 §8.2 Planner row, **Decided SDQ-6 (Innocent 2026-10-21)**: "if that fails too, a handoff reply"; DO-4 §4 comment covers the case where rules or the open task do give a plan; DO-4 §11 specialist row sets the handoff-reply pattern | AEA-37 #1: "Settled (GRN-7, DO-1 §8.2 / SDQ-6): `Plan.planner_failed=True` with no tasks → escalation rule 6 → degraded handoff (`model_error`); add AC `test_plan.py::test_both_planners_fail_hands_off` (Jev and Sonnet fakes both fail, no policy word or open task)." |
| GRN-8 | How the brief is persisted (`CaseService.attach_brief` is not reachable from `GraphDeps`; `BriefAssembler` stores nothing) | AEA-38 #2 | **Eng.** The reply node stores it twice: the brief node writes the `being_written` brief right after `assemble`, the checks node writes the final one after `check_quotes`, `check_facts` and `attach_extraction`; `attach_brief` replaces the stored brief. Reached through a `GraphDeps.cases: CaseService` field (requested from graph-core). A failed store logs `brief_failed` (`write_error`) and never fails the turn. Contract §3. | DO-4 §13 `attach_brief`; DO-4 §7 `Brief.status` "being_written until the extraction returns or fails"; DO-1 §8.2 brief row "off the critical path"; DO-3 §5.4 "brief, only if a case opened this turn" | AEA-38 #2: "Settled (GRN-8): store via `deps.cases.attach_brief` twice (being_written, then final) per contract graph-nodes §3; add AC `test_reply_brief.py::test_brief_stored_being_written_then_final`. Depends on graph-core adding `GraphDeps.cases`." |
| GRN-9 (ND-51a) | DANGER path: is the classifier's span the one model span allowed before the safety reply, or must `danger_rule` match DANGER's wording? | AEA-51 ND-51a | **Source.** The classifier path is the design: no word rule is written for DANGER's wording. CAP-2 is read per case: WP-5 (rule gate) has **no** model span before the reply; DANGER has only the two parallel Jev routing spans (`planner` and `classifier`; the ticket's "one span" misses the planner, which runs beside the classifier on every free-text turn) and **no** specialist, responder, brief or Sonnet span, and no identity or lookup step. Contract §7. | PRD R-47 / HP-2 C (Innocent 2026-10-20): rules first, then a classifier that may only raise; HP-2 "'In danger' has no word list … the classifier half is the only way to see 'someone in danger'"; R-8's rule half is "narrow explicit danger only"; DO-3 §5.4 `free_text → planner & danger_classifier → plan_join → safety`. R-5's "deterministic, no model" covers the safety list, not R-8 | AEA-51 ND-51a: "Settled (GRN-9): `test_cap2_safety_first.py` asserts no model span before the reply for WP-5, and for DANGER only the `planner` and `classifier` Jev spans (no specialist, responder, brief or Sonnet span; no identity or lookup step). No `danger_rule` is added for DANGER's wording." |

| GRN-10 | How R-44 quick checks reach `TurnFacts` and the offer card (graph-tools C-11) | graph-tools cross-topic C-11 (added at merge, 2026-10-21) | **Eng.** The facts node copies the passage ids of `SchedulingResult.quick_checks` into `TurnFacts.quick_checks` and the passages into `TurnFacts.passages` (de-duplicated); compose sends `QuickChecksBlock.checks` inline on the offer turn (C-11's recommended option), card id `<task_id>.<n>`. Contract §8. | graph-tools §3, §6, C-11; OpenAPI `QuickChecksBlock.checks` (array or null); DO-4 §8 `TurnFacts` | AEA-38: "Settled (GRN-10): fill `TurnFacts.quick_checks` / `.passages` from `SchedulingResult.quick_checks` per contract graph-nodes §8." AEA-21: "Compose sends `QuickChecksBlock.checks` inline on the offer turn (GRN-10)." |
| GRN-11 | Each node function's signature, so DO-3's node modules (`load_context.py`, `front.py`, `act.py`, `reply.py`) have a signed home (signature-check pass, 2026-10-21) | `signature_check.py`: "node module agent/nodes/{act,front,load_context,reply}.py names no class" | Contract §9: every node is `fn(state, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> <Node>Update`, one `TypedDict` per node naming exactly its DO-3 §5.3 keys (plus `check_events` and `halt` where §1 and graph-core §5 let it write them); `run_specialist` takes the `SpecialistSend` payload `{task, state}`; `compose` also takes `composer`. One `### Module: agent/nodes/<file>.py` heading per module. | Engineering. DO-3 §5.3 (one writer per key), graph-core §4 (`NodeFn`, GRC-23), §11 (`route_act_plan` builds one `Send` per task), graph-tools §2 (`scope_for(state, ctx)`). | AEA-21: "Stubs carry graph-nodes §9's signatures (GRN-11)." AEA-34, 36, 37, 38, 39: "Your node functions are graph-nodes §9.<n>; return only the keys its `TypedDict` names (GRN-11)." |

**Merge notes (2026-10-21).** `merge-clashes.md` (MC-1…MC-28) covers the five non-graph addenda only; no MC row names
this file. Aligned with sibling owners at merge:
- GRN-2, GRN-4 — *Changed at merge (graph-tools GRT-6):* `run_specialist` is now `SpecialistRunner.run`; the runner
  passes `DEADLINE` / `PROVIDER_SPEND_CAP` through `brake`, so a `brake` event and `brake_fired` are written only for
  graph-core §5 `BRAKE_HALTS`; `run_graph` (AEA-21) writes the `RECURSION_LIMIT` one (graph-core §5). Contract §1, §4.
- GRN-7 — wording aligned with graph-core GRC-11 (state key `planner: PlannerOutcome | None`). Decision unchanged.
- GRN-10 added from graph-tools C-11 (plain engineering addition, not in any MC row).
- Cross-topic requests 1–6 were accepted by their owners at merge (graph-core §4, §11; cases §1.1, §1.2, §3.4, §5;
  data `booking.urgent_note`; web §9, §10); the contract now cites those sections. One part is still open:
  graph-core §2 `RunGraph -> ComposedReply` gives `TurnService` no route to the final state's `check_events` (or
  `run_graph`'s `RECURSION_LIMIT` event); graph-core to settle. *Settled (final xref, 2026-10-21):* graph-core §2
  GRC-20/GRC-21 — `RunGraph` returns `GraphOutcome(reply, turn_trace, check_events, halt)`; contract §1 and the opening
  example now cite it. GRN-7: `degrade_reason = model_error` is cited to DO-4 §11, not cases §3.4.
- GRN-8: contract §3 now types `open_case_for_thread` as `CaseSummary | None` (DO-4 §13). Decision unchanged.

---

## Contradictions between sources (reported, not edited)

1. **CAP-2 vs R-47 / DO-3 §5.4.** DO-6 CAP-2 asserts "no model span before the safety reply" for DANGER as well as WP-5;
   the decided detection design (R-47, HP-2 C) can only reach DANGER through the classifier, after two Jev spans.
   Resolved by the decided source (GRN-9); DO-6's CAP-2 row should be reworded by its owner at the next DO-6 edit.
2. **DO-4 §4 vs DO-1 §8.2 (both planners fail).** "None → the turn still runs on rules and the open task" reads as if
   the turn continues; DO-1 §8.2 (Decided SDQ-6) says a handoff reply. Reconciled in GRN-7: the first applies when the
   rules or open task give a plan, the second when they don't.
3. **DO-4 §6 rule 6 "failed twice in a row"** vs DO-1 §8.2's one retry: already settled by CAS-15; GRN-7 adds the
   planner case to the same rule (cross-topic 4 in the contract).

## Cross-topic requests (from contract "Cross-topic assumptions")

graph-core: `check_events` state key, `GraphDeps.cases`, two router edges, `agent/signals.py`. Cases: `check_events`
columns, `core.check_events.append`, `core.lookup_log.for_thread`, `attach_brief` replaces, rule 6 + `AI.planner_failed`.
Data: one urgent booking-note text. Web: LOG allow-list for `signal`; `TurnService` persists both event carriers.
Tools: the runner emits no signal.

---

## Residual pass (2026-10-21)

Full rows in [`residuals-graph.md`](residuals-graph.md). All engineering; none for Innocent.

| ID | Change in `stage7/graph-nodes.md` |
|---|---|
| R-G-11 | §9.1: `GatesUpdate.burning_card_id` |
| R-G-12 | §9.1: `SpecialistSend.planned: PlannedTask` (was `task`); §9.5: `build_specialist_task`, the one builder |
| R-G-13, R-G-15 | §9.5: escalation fills `models_disabled` from `deps.ledger` and `now` from `ctx.now` |
| R-G-14 | §9.5: the person-gate `HandoffRequest` carries `rule_id="R2.person"` |
| R-G-19 | §9.5: `run_specialist` reads `deps.scheduling.slice_inputs` for a verified scheduling task |
