## [AEA-38] graph: reply node (facts, responder, brief, checks)

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

> **US-16:** "As a **homeowner**, I need the assistant never to say "done", "cancelled" or "refunded" unless it really did
> it, and to hand me to a person when it hits a limit, so that I can believe what it says." (Also US-4, US-7, US-17.)

**Example pair (WP-4F, turn 4: the SP-1 seam bug).** Turn 3 moved Linda Foster's (fictional) visit to Monday 8–12 with
Marta after she picked that window; its `moved` row is in `actions`. Turn 4 input: "Yes, please." Expected output: the
facts node re-reads `settled` through `core.settled_for(thread_id, ctx.now)` and finds the `moved` action; the responder
sees it under "ALREADY DONE IN THIS CONVERSATION"; the draft "Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with
Marta." passes the completion check (the claim matches a `moved` action in `settled`, SDQ-8 = A) and the fact check
("Monday", "8:00", "Marta" are in the evidence) (DO-3 §1).

**Second pair (WP-8).** "Just make sure it doesn't renew." with no completed action of that kind → a draft "Done,
auto-renew is off." has the sentence removed: "Done" is a generic completion word that passes only beside a
kind-specific claim that passes, and nothing backs it (`no_completed_action`, graph-nodes §2, GRN-1). The checks node
records a `completion` / `trimmed` event; the case, promise and reference come from code, never from the draft.

**Third pair (WP-7 brief).** WP-7's refund turn opens a case. The brief node writes the `being_written` brief at once
(CON-12 can show it), the extraction returns quotes "It didn't fix anything" and "I had to call another company"; the
checks node keeps both (exact substrings of the message text the extraction was given), and stores the final brief
(graph-nodes §3, GRN-8).

**The behaviour.** `agent/nodes/reply.py` replaces AEA-21's stubs with four node functions, each
`fn(state, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> <Node>Update` (graph-nodes §9.6; update types §9.1), and
`agent/prompts/reply.py` holds the responder and brief wording with trimmed output schemas (DO-3 §4.5):

- **`facts` → `FactsUpdate`** (`facts`, `settled`, `open_tasks`, `shown_slots`, `last_lookups`, `pending_change`,
  `counters`): builds `TurnFacts` (DO-4 §8) from `gate`, `plan`, `specialist_results`, `handoff`, `escalation` and
  `identity_step`; re-reads `settled` with `core.settled_for(thread_id, ctx.now)` in a read-only unit of work after this
  turn's writes (graph-core §6, GRC-12; the DB is the authority, DO-3 §5.1); is the **one committer** of durable task state
  (DO-3 §5.3); increments `FailureCounters` once per turn as graph-core §8 says (`failed_answers`, `tool_failures`,
  `identity_failures`, `corrections` from `gate.rules.correction`, `bookings`; never `timeouts`, which `load_context`
  copies); copies the passage ids of this turn's `SchedulingResult.quick_checks` into `TurnFacts.quick_checks` and those
  passages into `TurnFacts.passages`, in order, de-duplicated (graph-nodes §8, GRN-10). `TurnFacts.account` carries
  customer-facing fields only: no staff notes (HP-3). It still runs on a halted state; the router then skips responder,
  brief and checks (graph-core §5).
- **`responder` → `ResponderUpdate`** (`draft`, `check_events`, `halt`) (Sonnet, `StructuredModel`, `Role.RESPONDER`, cap
  12 s): renders `ResponderInput` (DO-4 §9) from `state.chat_window` exactly as AEA-34 built it (≤ 10 turns, 600 chars per
  line, 8,000 chars total [A], graph-core §7; this node never re-reads `messages`), `this_turn` labelled "WHAT HAPPENED THIS
  TURN", `settled` labelled "ALREADY DONE IN THIS CONVERSATION", the identity status word only, `today_label` from
  `ctx.now`, and the rules (no promise text, no reference, no "charged", no completion word unless backed by `settled`, no
  prices beyond the facts). Output `ResponderDraft(text ≤ 1200)`: words only; every card is composed by code. A gateway
  `BRAKE_SONNET_CALLS` halt writes `halt`, a `CheckEvent.from_halt` `brake` event and a `brake_fired` signal.
- **`brief` → `BriefUpdate`** (`brief_extraction`, `check_events`, `halt`) (Sonnet, `Role.BRIEF`, cap 12 s), beside the
  responder in the same superstep, only when a case opened this turn: `case = deps.cases.open_case_for_thread(thread_id)`
  (`None` → no brief); `lookups = tx.core.lookup_log.for_thread(thread_id)` in a read-only unit of work;
  `brief = deps.brief.assemble(case, state, lookups)` (status `being_written`); `deps.cases.attach_brief(case.case_ref,
  brief)`; then one structured call returns `BriefExtraction` (headings 2, 4, 7). A failed or invalid extraction leaves
  `brief_extraction = None` and emits `brief_failed` with the failure kind (graph-nodes §3, §4).
- **`checks` → `ChecksUpdate`** (`checked`): on the draft, `check_completion(text, settled)` and `check_facts(text,
  build_evidence(facts, settled, lookups))` from `checks.py` (AEA-15). On a brief turn, `check_quotes(extraction, shown)`
  (`shown` = message_id → the exact customer text the extraction call was given) and `check_facts(open_decision, …, chat)`;
  keeps the surviving quotes, `deps.brief.attach_extraction(brief, kept or None, facts_check or None)` and
  `deps.cases.attach_brief(case.case_ref, final)` (an upsert per case, cases.md §5). A failed `attach_brief` emits
  `brief_failed` / `write_error` and never fails the turn. A removed sentence leaves the rest; when nothing is left, or the
  responder failed, `CheckedReply.fallback_used` and compose (AEA-21) builds the reply from the facts' fixed fields plus a
  person offer (DO-4 §10), with a `responder_fallback` signal (`cause` = the failure kind, or `all_removed`). Writes
  `checked` with one `CheckEvent.from_check` per check run (`completion`, `fact`; `brief_quote`, `brief_fact` on a brief
  turn): kinds and counts only, never the removed text.

The promise and the reference are never in `ResponderDraft`; `compose` (AEA-21) appends them from `HandoffResult` after
the checks (R-26, R-46). Signals go out through `emit_signal` (`agent/signals.py`, AEA-21; graph-nodes §4).

### Source

- DO-4 §1 (`Settled`, `ChatLine`: "never tool output"), §7 (brief: `BRIEF_TITLES`, `BriefItem`, `BriefHeading`, `Brief`,
  `Quote`, `BriefExtraction`, `BriefAssembler.assemble` / `attach_extraction`; staff-only text never in any
  `ResponderInput`), §8 (`TurnFacts`), §9 (`ResponderInput`, `ResponderDraft`, `CheckedReply`), §10 (R-46 checks, SDQ-8 A),
  §11 (*Responder* failure row), §12 (`StructuredRequest`, roles, caps), §16 (addenda win).
- `docs/design/contracts/stage7/graph-nodes.md` §1 (`CheckEvent`, `from_check`, `from_halt`), §2 (`GENERIC_COMPLETION_WORDS`,
  `Claim.kind = "quote"`, `check_quotes`), §3 (the brief assembled, checked and stored), §4 (`responder_fallback`,
  `brief_failed`, `brake_fired`), §8 (quick checks into `TurnFacts`), §9.1 (`FactsUpdate`, `ResponderUpdate`, `BriefUpdate`,
  `ChecksUpdate`), §9.6 (node signatures).
- `docs/design/contracts/stage7/graph-core.md` §4 (`GraphDeps.cases`, `timed_node`), §5 (halt routing; facts on a halted
  state), §6 (`core.settled_for(thread_id, read_at)`), §7 (`ContextLimits`), §8 (`FailureCounters`, `RuleMatches.correction`),
  §11 (`check_events`, `add_turn_events`); `docs/design/contracts/stage7/cases.md` §1.2 (`core.lookup_log.for_thread`), §5
  (`CaseService.open_case_for_thread`, `attach_brief` upsert); `docs/design/contracts/stage7/graph-tools.md` §6 (quick
  checks in `SchedulingResult.quick_checks`).
- Decision ledgers: `docs/plans/7b-decisions/graph-nodes.md` GRN-1, GRN-2, GRN-3, GRN-4, GRN-8, GRN-10, GRN-11;
  `docs/plans/7b-decisions/graph-core.md` GRC-7, GRC-12, GRC-13, GRC-14, GRC-15.
- DO-3 §1 (the WP-4F turn), §5.1–§5.4 (`facts` is the one committer; responder ∥ brief, then checks, then compose), §7 rows
  R-4, R-28, R-45, R-46. DO-2 `system-design.md` §A.1, §A.3, §8.2 (*Responder*, *Brief extraction* rows), SDQ-2 = A, SDQ-8 =
  A.
- PRD R-4, R-13, R-28, R-44, R-45, R-46; HP-1, HP-4; WP-1, WP-2 (✓ "wp2 144"), WP-4F, WP-7, WP-8; SP-1 §4. Rule
  `context-management-multi-turn.md` (rules 1–4).
- Slice plan §0a (Amendment 1, journey J-2) and rule `.claude/rules/integrated-journeys.md` §3–§4.
- Slice plan row AEA-38; area-map row A7c (Reply); ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Do not let the agent guess. A confident wrong answer is worse than a handoff" and "hands off
  with enough context that a human can pick up without starting over"; touches nothing out of scope; weakens nothing →
  proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `settled` comes from the database: when this turn's specialist result reports a `booked` write, the facts node's `settled` includes it only because the `actions` row exists in the temp working copy (read through `core.settled_for(thread_id, ctx.now)`); a specialist result claiming a write with no row adds nothing — verify: `tests/unit/agent/nodes/test_reply_facts.py::test_settled_reread_from_db` — evidence: `settled.actions` equals the rows in both cases.
- [ ] AC-2 [invariant] WP-4F turn 4: the completion claim "it's moved" passes against `settled` and the reply keeps it; the same draft with no `moved` row has the claim removed — verify: `tests/unit/agent/nodes/test_reply_checks.py::test_wp4f_turn4_claim_backed_by_settled` — evidence: `removals` empty in the first case, one `no_completed_action` removal in the second.
- [ ] AC-3 [failure/refusal] WP-8: "Done, auto-renew is off." is removed (generic word, no backing action, GRN-1) while "Done, your visit is booked." with a `booked` action in `settled` is kept; the WP-8 check event is `completion` / `trimmed` with `removed=1` and `claim_kinds=("completion",)`, and holds no removed text — verify: `test_reply_checks.py::test_wp8_generic_done_removed` — evidence: event fields as stated; the kept sentence present.
- [ ] AC-4 [failure/refusal] Fact check, WP-2: a draft sentence saying the after-hours fee is "$149" when the evidence holds the billed "$144" is removed (`not_in_evidence`); the $89 / $245 / $144 sentence stays — verify: `test_reply_checks.py::test_unmatched_amount_removed` — evidence: one removal; the kept text holds the billed amounts.
- [ ] AC-5 [failure/refusal] A responder failure (gateway double returns a failure after its retry) gives `fallback_used=True`, a `fallback` check event and a `responder_fallback` signal with `cause` = the failure kind; a draft whose every sentence is removed gives `fallback_used=True` and the signal with `cause="all_removed"`; neither raises — verify: `test_reply_checks.py::test_responder_failure_and_empty_draft_fallback` — evidence: both cases `fallback_used`; signals as stated; no model text in `checked.text`.
- [ ] AC-6 [failure/refusal] The brief runs only when `deps.cases.open_case_for_thread` returns a case: on a turn without one there is no brief call; with one, `attach_brief` is called first with a `being_written` brief and again with the final one; when the extraction fails, headings 2, 4 and 7 are `not_generated`, headings 1, 3, 5, 6, 8 stay and `brief_failed` is emitted; an `attach_brief` that raises emits `brief_failed` / `write_error` and the turn completes — verify: `tests/unit/agent/nodes/test_reply_brief.py::test_brief_only_when_case_opened`, `::test_brief_stored_twice`, `::test_brief_failure_not_generated`, `::test_attach_brief_failure_does_not_fail_turn` — evidence: call counts, heading flags and signals as stated.
- [ ] AC-7 [invariant] Brief checks, WP-7: the quotes "It didn't fix anything" and "I had to call another company" pass `check_quotes` as exact substrings of the text the extraction was shown; a paraphrased quote is removed (`quote_not_found`); a number in `open_decision` that is in neither the lookup log nor the chat is removed; the events are `brief_quote` and `brief_fact` with their removal counts — verify: `test_reply_brief.py::test_brief_quote_and_fact_checks` — evidence: removals and events as stated.
- [ ] AC-8 [negative] `ResponderInput` for WP-2 holds no staff note (the $144-vs-$149 staff fact, any `agent_discretion_notes` text), no raw tool output (`for_model` JSON), no promise text, no case reference, no code and no card-like number; `ResponderDraft` has no field for a promise or reference; no check event and no `signal` record holds draft or message text — verify: `tests/unit/agent/prompts/test_reply_prompts.py::test_responder_input_excludes_staff_tool_output_and_promise` — evidence: seeded strings (built in the test from parts) absent from the captured request, the check events and the `meridian.signal` log capture.
- [ ] AC-9 [invariant] Turn-2+ full prompt (context-management rule 3): a recording fake structured model drives the responder on turns 1, 2 and 5 of a WP-3 → WP-4F conversation; the stable `system_prefix` (automated assistant, not a person (R-1); the rules) is byte-identical and complete each turn; `settled` and this turn's facts are present under their labels; the chat window is `state.chat_window` as given (not a growing message list, never a re-read of `messages`) and within graph-core §7's caps (rule 4) — verify: `tests/unit/agent/prompts/test_reply_prompt_turns.py::test_stable_prefix_turns_1_2_5` — evidence: three captured requests; prefix hashes equal; window within its caps.
- [ ] AC-10 [invariant] Counters and quick checks (graph-core §8, graph-nodes §8): a turn with a `no_current_source` knowledge result adds 1 to `failed_answers`; `gate.rules.correction` adds 1 to `corrections`; a `NotVerified` identity step adds 1 to `identity_failures`; one `BOOKED` action adds 1 to `bookings`; `timeouts` is never changed by facts; a `SchedulingResult.quick_checks` of two passages (one repeated) gives `TurnFacts.quick_checks` of two ids in order and both passages in `TurnFacts.passages` — verify: `test_reply_facts.py::test_failure_counters_rules`, `::test_quick_checks_into_turn_facts` — evidence: counter deltas and lists as stated.
- [ ] AC-11 [failure/refusal] A gateway `BRAKE_SONNET_CALLS` halt on the responder writes `Halt(reason=BRAKE_SONNET_CALLS, node="responder")`, one `brake` check event with `codes=("brake_sonnet_calls", "responder")` and one `brake_fired` signal — verify: `test_reply_checks.py::test_sonnet_brake_on_responder` — evidence: halt, event and signal as stated.
- [ ] AC-12 [invariant] Key ownership (graph-nodes §9.1): `facts` returns only `FactsUpdate` keys, `responder` only `ResponderUpdate`, `brief` only `BriefUpdate`, `checks` only `ChecksUpdate`; the project's type check (the checker AEA-01 chose) passes on `agent/nodes/reply.py` against the `TypedDict`s — verify: `tests/unit/agent/nodes/test_reply_keys.py::test_reply_nodes_write_only_own_keys` and the type-check command — evidence: returned key sets as stated; type check clean.
- [ ] AC-13 [capture] `checked.events` holds one `CheckEvent` per check run (`completion`, `fact`, and on a brief turn `brief_quote`, `brief_fact`) with result `pass`, `trimmed` or `fallback`, ready for `run_graph` to put in `GraphOutcome.check_events` and `TurnService` (AEA-40) to persist; the `signal` records of AC-5, AC-6 and AC-11 carry `turn_id`, `thread_id`, `request_id`, `run_tag`, `node` and codes only — verify: `test_reply_checks.py::test_check_events_and_signals_emitted` — evidence: event list per scenario; signal fields as stated. (Real-entry-point capture: CAP-1 in AEA-51 asserts the R-46 `check_event` row.)
- [ ] AC-14 [journey] Extends J-2 (slice plan §0a journey map): the WP-2 invoice turn through CON-2 shows the billed $89 / $245 / $144 explanation with its source chip and no "$149", and the stored `check_events` rows hold the turn's `completion` and `fact` events; the WP-1 answer cites the current membership document, never its stale twin; in `tests/journeys/j2/test_aea_38.py` with the scripted model adapter — verify: `uv run pytest -m journey tests/journeys/j2/test_aea_38.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57's harness and AEA-51's J-2 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-38.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-15 [regression/context] In the same change: the area-map row A7c for `agent/nodes/reply.py` and `agent/prompts/reply.py` (planned → actual + commit), the ICM progress row *Routes verified against code and tests*, DO-3 §3's rows for those two files marked built — verify: `git diff --name-only` — evidence: those docs in the diff, only this ticket's rows changed.

### Observability

- Responsibilities: WF-1 (customer chat turn, its internals; DO-6 emitters "responder, R-46 checks"). This ticket emits the
  R-46 `check_event`s (`completion`, `fact`, `brief_quote`, `brief_fact`) in `checked.events` and a `brake` event for
  `BRAKE_SONNET_CALLS` in `check_events`, both carried to `TurnService` by `GraphOutcome.check_events` (graph-core §2, §11)
  and persisted by AEA-40; the `signal` LOG records `responder_fallback`, `brief_failed` and `brake_fired` (graph-nodes §4;
  web.md §10), with a responder failure ending the turn `degraded_handoff` / `model_error` (DO-4 §11); and the brief rows
  through `CaseService.attach_brief` (the case store; read by CON-12). Responder and brief `model_call` spans and
  `spend_ledger` rows come from the gateway (AEA-20); node spans from `timed_node` (AEA-21). Codes and counts only.
- Capture evidence: AC-13 at component level, AC-8 for the forbidden values; CAP-1 (AEA-51) finds the R-46 `check_event` at
  the real CON-2 entry point.

### Evaluation

- Checks: E-1 hard gate "no completion claim without a successful write" (read per SDQ-8 A against the conversation's
  `settled`; the eval also shows R-46's literal reading via `settled.only_turn(turn_id)`, DO-4 §10), E-1 must-say /
  must-not-say for WP-1 and WP-2, E-6 brief required-item recall and invented facts; kept passing at AEA-51.
- Expected-answer authority: the case's hand-written required-item list, and "any number, date, ID or amount not in the
  lookup log or the chat is an invented fact" (DO-5, *Handoff brief* row); SDQ-8 for completion claims.

### Metrics

- References: WF-1 inherits M-1, M-3, M-4, M-6, M-7, M-8, M-9, M-14, M-16, M-17, M-18, M-19, M-20, M-21, M-22, M-23, M-24,
  M-25, M-26, M-29. **Affected here:** M-8 (wrong-answer rate: fact-check removals), M-21 (completion claims without a
  write, from `completion` events), M-24 (responder failures as `degraded_handoff` / `model_error`), M-23 (responder ∥
  brief in one superstep), M-25 and M-26 (Sonnet cost recorded by the gateway), M-7 (`TurnFacts.passages` carry each
  answer's source file for the chips), M-1 (the facts and checked words feed resolution scoring). Also, from WF-2's
  handoff: M-11 (brief required-item recall) and M-12 (invented facts in briefs, from `brief_fact` events). **Kept
  computable, not changed by this ticket:** M-3, M-4, M-6, M-9, M-14, M-16, M-17, M-18, M-19, M-20, M-22, M-29.
- Acceptance conditions: M-12 and M-21 stay computable from the persisted `check_event`s (AC-13). No target set or changed.

### Blocked by

AEA-10, AEA-11, AEA-15, AEA-21 (slice plan). Calls (injected): `ModelGateway` (AEA-20) through `GraphDeps.gateway`;
`BriefAssembler` and `CaseService` (AEA-29) through `GraphDeps.brief` and `GraphDeps.cases`; each tested with a double
honouring DO-4 §7, §12, §13 and cases.md §5.

### Agent handoff

- Area / owner: A7c Reply (`agent/nodes/reply.py`, `agent/prompts/reply.py`).
- Contracts and shared surfaces: consumes `checks.py` incl. `check_quotes` and `GENERIC_COMPLETION_WORDS` (AEA-15),
  `ModelGateway.structured` (AEA-20, double), `BriefAssembler` and `CaseService.open_case_for_thread` / `attach_brief`
  (AEA-29, doubles), `GraphDeps.uow` with `core.settled_for` and `core.lookup_log.for_thread` (AEA-10), `ContextLimits`
  (AEA-01), the `*Update` types, `CheckEvent` builders and `SignalRecord` (AEA-02), `emit_signal` and `timed_node` (AEA-21).
  Produces `facts`, `draft`, `brief_extraction`, `checked`, the durable task keys and the stored brief for AEA-21 (compose,
  `turn_trace`, `run_graph`), AEA-40 (persists the events) and AEA-45 (CON-12 reads the brief). Must not edit `checks.py`,
  `compose.py`, `load_context.py`, `services/*`, `domain/*`, `repos_*.py`.
- Scope boundary / refusal: no promise, reference or card text (compose); no new check rules (AEA-15 owns `checks.py`);
  no window building (AEA-34 applies graph-core §7's caps); no streaming (SDQ-2 A).
- Wave and gates: wave 2; no gate.
- Lane: build-loop — it changes source and tests (`ticket-lanes.md`).
- Risk: None per the slice plan.
- Entry points added or changed: None — WF-1 internals only (its CON-1/CON-2 entry is AEA-40).
