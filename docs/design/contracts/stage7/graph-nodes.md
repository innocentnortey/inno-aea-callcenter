# Signatures and types added at Stage 7 (2026-10-21), graph: nodes

Part of the graph topic (split three ways: core GRC, tools GRT, nodes GRN). This part covers the check events the
nodes record, the DO-6 records for the DO-1 §8.2 failure signals, the brief's quote check and its persistence, what
the plan node does when both planners fail, the burning-smell "both ruled out" route, and the DANGER-span reading of
CAP-2, and how R-44 quick checks reach `TurnFacts` and the offer card; at the signature-check pass, each node
function's signature and update type by module (§9). Decisions and their basis:
[docs/plans/7b-decisions/graph-nodes.md](../../../plans/7b-decisions/graph-nodes.md) (GRN-1 … GRN-11). Everything here extends DO-4 (`internal-components.md`); nothing in DO-4 is removed.

**One turn, concretely.** WP-3's variant DANGER: *"my mother is 88 and it's 95 degrees in here"*. No word rule
matches, so the gate is `free_text`; the Jev planner and the raise-only classifier run in parallel; the classifier
says `danger`. The turn then records two check events (`gate` / `pass`, `classifier` / `raised`, and none from R-46
because the safety path skips the responder) and one `safety_reply_sent` signal; `run_graph` returns them in a
`GraphOutcome`, and `TurnService` persists `outcome.check_events` and the `turn` row from `outcome.turn_trace`
(`TurnTrace.gate_result = danger`, `outcome = safety_reply`; graph-core §2, GRC-21). Had the P1 case write failed, the
write would be retried once, a `case_write_failed` signal logged with whether the retry worked, and the instruction
sent either way.

---

## 1. `CheckEvent`: every check that fires, one shape (`domain/turn.py`, AEA-02) [GRN-2, GRN-5]

```python
CheckKind = Literal["completion", "fact", "brief_fact", "brief_quote",   # R-46 (DO-4 §10, unchanged)
                    "gate", "classifier", "brake"]                       # added: DO-6 *Records* `check_event`
                                                                         #   "code gate … R-47 classifier raise, brake"
class CheckEvent(MeridianModel):                      # DO-6 `check_event`; DO-4 §10 fields kept, two widened, one added
    check: CheckKind
    turn_id: TurnId
    result: Literal["pass", "trimmed", "fallback",    # R-46 (unchanged)
                    "fired", "raised"]                # gate: fired | pass; classifier: raised | pass | fallback; brake: fired
    removed: int = 0                                  # R-46 only
    claim_kinds: tuple[str, ...] = ()                 # R-46 only; kinds, never the removed text (unchanged)
    codes: tuple[str, ...] = ()                       # stable codes only, never message text or a value:
                                                      #   gate → (GateKind value, *RuleMatches.rule_ids)
                                                      #   classifier → (label,) or, on failure, ("fallback", ProviderFailureKind value)
                                                      #   brake → (HaltReason value, node name)

    @classmethod
    def from_check(cls, check: Literal["completion", "fact", "brief_fact", "brief_quote"], turn_id: TurnId,
                   removals: Sequence[Removal], *, fallback: bool = False) -> "CheckEvent":
        """fallback → "fallback"; no removals → "pass"; else "trimmed". removed = len(removals);
        claim_kinds = sorted distinct removal.claim.kind."""
    @classmethod
    def from_gate(cls, turn_id: TurnId, gate: GateDecision) -> "CheckEvent":
        """One per turn. "fired" when gate.kind ∉ {FREE_TEXT, CODE_ENTRY, LOCATE, CARD_CHOICE} or gate.rules.rule_ids is
        non-empty (a policy word on a free-text turn fires too); else "pass"."""
    @classmethod
    def from_danger(cls, turn_id: TurnId, danger: DangerAssessment) -> "CheckEvent":
        """One per classifier run: failure → "fallback"; raised → "raised"; else "pass"."""
    @classmethod
    def from_halt(cls, turn_id: TurnId, halt: Halt) -> "CheckEvent":
        """Only for BRAKE_* and RECURSION_LIMIT reasons; ValueError for DEADLINE, SPEND_CAP, PROVIDER_SPEND_CAP
        (those are turn outcomes, not brakes)."""
```

Label: [Decided §7, engineering]. Builders are pure classmethods in `domain/turn.py`, so the four producing nodes
share one mapping without depending on `checks.py`.

**Who builds which event, and where it travels.**

| Event | Built by (ticket, file) | When | Carried to `TurnService` in |
|---|---|---|---|
| `gate` | AEA-36 `nodes/front.py` (gates node) | every turn | state key `check_events` (defined in stage7/graph-core.md §11, reducer `add_turn_events`) |
| `classifier` | AEA-37 `nodes/plan.py` | every turn the classifier runs | `check_events` |
| `brake` | the node that writes a halt whose reason is in graph-core §5 `BRAKE_HALTS`: AEA-39 `nodes/act.py` (from a `SpecialistResult.brake` in `BRAKE_HALTS`; the runner also passes `DEADLINE` and `PROVIDER_SPEND_CAP` through `brake`, graph-tools §2, and those write the halt with no `brake` event), AEA-38 `nodes/reply.py` (gateway `BRAKE_SONNET_CALLS` halt on the responder or brief), AEA-37 (`BRAKE_TASKS` in the join); and AEA-21 `run_graph` for `RECURSION_LIMIT` when it catches `GraphRecursionError` (graph-core §5) | when the halt is written | `check_events`; for `RECURSION_LIMIT` (no final state exists) `run_graph` reads the last checkpoint's events and appends its own event in `GraphOutcome.check_events` (graph-core §11) |
| `completion`, `fact` | AEA-38 `nodes/reply.py` (checks node) | every turn the responder ran | `checked.events` (DO-4 §9, unchanged; AC-11) |
| `brief_fact`, `brief_quote` | AEA-38 `nodes/reply.py` (checks node) | every turn a brief extraction returned | `checked.events` |

`run_graph` (AEA-21) collects this turn's `check_events` (filtered by `turn_id`) plus `checked.events`, and on
`RECURSION_LIMIT` its own `brake` event, into `GraphOutcome.check_events` (stage7/graph-core.md §2, §11; GRC-20).
`TurnService` (AEA-40) persists them as given in DO-4 §14 step 7, one row each through
`core.check_events.append(event, thread_id)` (web.md §9). The `check_events` table columns mirror `CheckEvent` plus
`thread_id` and `at` (`claim_kinds` and `codes` as JSON arrays): defined in stage7/cases.md §1.1.

M-16 reads `classifier` / `raised` with `turn.gate_result`; M-17's per-turn denominator is the `classifier` events
(one per run, so `pass` is recorded too); M-12 and M-21 read the R-46 kinds.

---

## 2. R-46 additions in `checks.py` (AEA-15) [GRN-1, GRN-3]

```python
GENERIC_COMPLETION_WORDS: tuple[str, ...] = ("done", "all set", "taken care of", "sorted", "finished",
                                             "completed", "that's handled")     # inline, beside COMPLETION_WORDS
# A generic word yields Claim(kind="completion", action_kind=None). It passes only when the SAME sentence also holds
# a kind-specific completion claim that passes. Otherwise the sentence is removed with reason "no_completed_action".
#   "Done, your visit is booked."   + settled has BOOKED → both claims pass, sentence kept
#   "Done, auto-renew is off."      → no ActionKind backs it (HP-4 :264, WP-8) → removed
#   "Done!" on its own              → removed (compose falls back if nothing is left, DO-4 §10)

class Claim(MeridianModel):                           # DO-4 §10; one kind added
    kind: Literal["completion", "number", "date", "time", "id", "amount", "quote"]
    span: tuple[int, int]; value: str
    action_kind: ActionKind | None = None
    # "quote": span = (0, len(quote.text)), value = str(quote.message_id). Never logged; CheckEvent keeps kinds only.

class QuoteCheck(MeridianModel):
    needs: tuple[Quote, ...]                          # the quotes that passed, original order
    claims: tuple[Quote, ...]
    removals: tuple[Removal, ...]                     # reason "quote_not_found"
    passed: bool                                      # no removals

def check_quotes(extraction: BriefExtraction, shown: Mapping[int, str]) -> QuoteCheck: ...
    # shown = message_id → the exact text the brief extraction call was given for that customer message (the node
    # holds it after rendering the prompt). A quote passes when its message_id is in `shown` and quote.text is an
    # exact substring of shown[message_id]; anything else is removed. Pure; no I/O.
```

Label: [Decided §7, engineering]. Basis: DO-4 §10 last bullet ("every `Quote` must be an exact substring of its
message") and `Removal.reason = "quote_not_found"`; `checks.py` is the R-46 module (code-design tree, A7c).

---

## 3. Brief: assembled, checked and stored by the reply node (AEA-38) [GRN-8]

Only on a turn where a case opened (DO-3 §5.4 "brief, only if a case opened this turn"):

```text
brief node   (nodes/reply.py, parallel to the responder):
  case    = deps.cases.open_case_for_thread(thread_id)                     # CaseSummary | None (None → no brief)
  lookups = tx.core.lookup_log.for_thread(thread_id)                       # read-only tx (cross-topic 3)
  brief   = deps.brief.assemble(case, state, lookups)                       # status "being_written"
  deps.cases.attach_brief(case.case_ref, brief)                            # CON-12 can show "being written" at once
  extraction = gateway BRIEF call → BriefExtraction | failure               # failure → brief_failed signal, extraction None
checks node  (nodes/reply.py):
  q        = check_quotes(extraction, shown)                                # §2
  facts_ck = check_facts(extraction.open_decision, build_evidence(facts, settled, lookups, chat))
  kept     = extraction.model_copy(update={"needs": list(q.needs), "claims": list(q.claims)})
             # model_copy does not re-validate, so zero surviving needs is allowed; heading 2 then shows
             # "Nothing recorded." (UX copy)
  final    = deps.brief.attach_extraction(brief, kept or None, facts_ck or None)
  deps.cases.attach_brief(case.case_ref, final)                             # replaces the stored brief (upsert per case)
  events  += CheckEvent.from_check("brief_quote", …, q.removals), CheckEvent.from_check("brief_fact", …, facts_ck.removals)
```

Label: [Decided §7, engineering]. `deps.cases: CaseService` is defined in stage7/graph-core.md §4 (GRC-15);
`attach_brief` is an upsert per case (stage7/cases.md §5); `core.lookup_log.for_thread` is stage7/cases.md §1.2.
A failed `attach_brief` is logged as a `brief_failed` signal with cause `write_error` and does not fail the turn
(DO-1 §8.2: the brief is off the critical path).

---

## 4. Failure signals: the `signal` log record (`domain/turn.py` types, AEA-02; `agent/signals.py`, AEA-21) [GRN-4]

DO-1 §8.2 names eight signals the nodes raise; DO-6 names no record for them. They become one structured log record,
the same storage rule the web topic used for `stream_reconnect` (WEB-18) and `request` / `auth_event` (WEB-11): no
table, through `web/logging.py`'s LOG-profile allow-list formatter.

```python
class SignalName(StrEnum):
    SAFETY_REPLY_SENT = "safety_reply_sent"; CASE_WRITE_FAILED = "case_write_failed"
    CLASSIFIER_FALLBACK = "classifier_fallback"; PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST_FAILED = "specialist_failed"; BRAKE_FIRED = "brake_fired"
    RESPONDER_FALLBACK = "responder_fallback"; BRIEF_FAILED = "brief_failed"

class SignalRecord(MeridianModel):                    # LOG record {"record": "signal", ...}; IDs and codes only
    record: Literal["signal"] = "signal"
    name: SignalName
    turn_id: TurnId; thread_id: ThreadId; request_id: RequestId
    run_tag: Literal["live", "eval", "load"]
    node: str                                         # graph node name
    cause: str | None = None                          # a code: ProviderFailureKind or HaltReason value, gate_result,
                                                      #   "all_removed", "write_error"; never text, never a payload
    role: Literal["planner", "classifier", "specialist", "responder", "brief"] | None = None
    specialist: Literal["knowledge", "account", "scheduling"] | None = None
    attempt: int | None = None
    recovered: bool | None = None

# agent/signals.py (AEA-21):
def emit_signal(ids: TurnIds, record: SignalRecord) -> None: ...
    # logging.getLogger("meridian.signal").info("signal", extra={"signal": record.model_dump(mode="json")})
```

| Signal | Emitted by | When | `cause` | Turn outcome effect |
|---|---|---|---|---|
| `safety_reply_sent` | AEA-36 safety node | every safety, burning-unclear or danger instruction built | `gate_result` value | `safety_reply` (DO-6) |
| `case_write_failed` | AEA-36 safety node | once per P0/P1 case write whose first attempt failed, after the one retry: `attempt = 2`, `recovered` = the retry wrote the case | `write_error` | none: the instruction is sent either way (DO-1 §8.2) |
| `classifier_fallback` | AEA-37 plan node | classifier failed or timed out after its one retry; rules stand (R-47) | failure kind | none |
| `planner_fallback` | AEA-37 plan node | Jev planner failed twice and the Sonnet planner ran; `recovered` = Sonnet answered | Jev failure kind | none if recovered; else GRN-7 (§5) |
| `specialist_failed` | AEA-39 act node | a `SpecialistResult.status == "failed"` with no `brake` | `failure.kind`, or `tool_error` when `failure` is None | `degraded_handoff` / `model_error` or `tool_error` (DO-4 §11) |
| `brake_fired` | the writer of a `brake` check event (§1 table, incl. `run_graph` for `RECURSION_LIMIT`) | with the `brake` check event | `HaltReason` value | `degraded_handoff` / `brake` |
| `responder_fallback` | AEA-38 reply node | responder failed (`cause` = failure kind) or every sentence was removed (`cause = "all_removed"`) | as stated | failure → `degraded_handoff` / `model_error`; `all_removed` → none (a check outcome, not a failure) |
| `brief_failed` | AEA-38 reply node | extraction failed or was invalid, or `attach_brief` failed | failure kind or `write_error` | none (off the critical path) |

`SpecialistRunner.run` (AEA-35, graph-tools §2; it replaces DO-4 §5's `run_specialist`) emits nothing: it returns
`brake` and `failure` on its result, and AEA-39 emits. A `brake` of `DEADLINE` or `PROVIDER_SPEND_CAP` raises no node
signal: those halts are signalled outside the nodes (`turn_timeout`, `provider_spend_cap`, DO-4 §11).
M-24 still counts from `turn.degrade_reason` (DO-7); the signal records are for logs and the capture checks, not for a
page. Label: [Decided §7, engineering].

---

## 5. Both planners fail and nothing else gives a plan (AEA-37) [GRN-7]

```python
class Plan(MeridianModel):                            # DO-4 §4; one field added
    ...
    planner_failed: bool = False                      # Jev twice and the Sonnet fallback all failed (not models_disabled)

# join_plan (nodes/plan.py, AEA-37): rules and the open task still apply first (DO-4 §4). When its `planner` argument
# (state key `planner: PlannerOutcome | None`, graph-core §9) has `choices is None` because Jev twice and the Sonnet
# fallback all failed (`failure` set) AND no policy word, open task or card choice yields a task or handoff_request:
#   Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)
```

The turn then ends in a handoff reply, as DO-1 §8.2 [Decided SDQ-6] says: the router sends a plan with
`planner_failed and not tasks` to `escalation` (stage7/graph-core.md §11 edge 1), and escalation rule 6 escalates it
`degraded=True`, `ai_failure` → P3, rule id `AI.planner_failed` (stage7/cases.md §3.4); the reply's
`degrade_reason = model_error` (DO-4 §11 provider-failure row; carried to the turn row by `TurnTrace.degrade_reason`,
graph-core §2). Label: [Source: DO-1 §8.2, Decided SDQ-6].

---

## 6. Burning smell, both dangers ruled out (AEA-36) [GRN-6]

`burning_answer == "no"` no longer goes to `safety`. The gates node writes a code-built `plan` (on this path only) and
the gates router sends it through `route_act_plan` (identity first if needed, else the specialists fan-out): router
edge defined in stage7/graph-core.md §11 edge 2.

```python
Plan(mode="act",
     tasks=(PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW,
                        needs_identity=<as join_plan sets it for BOOK_NEW>),),
     handoff_request=<CAS-16's reason>, topic="booking", source="rules_only")
```

`"yes"` → safety (R-5, P0); `"unsure"` → safety (conditional instruction, emergency number, P1). The urgency mark on
the booking note is the fixed text `booking.urgent_note` (`policy/texts.py`, AEA-03; defined in stage7/data.md, `booking`
group). The case's reason and priority are **CAS-16,
open for Innocent** (cases.md); until answered, `priority_for` raises `NotImplementedError` on this path and no AEA-36
test asserts a level. Label: routing [Decided §7, engineering]; reason and priority [Innocent, CAS-16].

---

## 7. CAP-2 on the DANGER path (AEA-51) [GRN-9]

| Case | Path | Model spans allowed before the safety reply |
|---|---|---|
| WP-5 (CO alarm) | `safety` rule gate | **none** |
| DANGER ("my mother is 88 and it's 95 degrees in here") | `free_text` → planner ∥ classifier → `plan_join` (raised) → `safety` | the two parallel Jev routing spans only (`planner`, `classifier`); **no** specialist, responder, brief or Sonnet span |

`test_cap2_safety_first.py` asserts exactly this table, plus "no identity or lookup step before the instruction".
No word rule is written to match DANGER's wording. Label: [Source: R-47 / HP-2 C, Decided 2026-10-20; DO-3 §5.4].

---

## 8. R-44 quick checks into `TurnFacts` and the offer card (AEA-38 facts, AEA-21 compose) [GRN-10]

graph-tools §6 puts the offered troubleshooting passages in `SchedulingResult.quick_checks: tuple[Passage, ...]`
(graph-tools §3). From there:

```text
facts node (nodes/reply.py, AEA-38), every turn:
  TurnFacts.quick_checks = the passage_id of every Passage in this turn's SchedulingResult.quick_checks, in order,
                           de-duplicated                                       # DO-4 §8 field, unchanged type
  TurnFacts.passages    += those Passages, de-duplicated by passage_id         # so compose can build their chips
compose (agent/nodes/compose.py, AEA-21), on the turn TurnFacts.quick_checks is non-empty:
  QuickChecksBlock(card_id = "<task_id>.<n>" of the booking task (graph-core §3), options skip_and_book, show_checks,
                   answered = None, offer_text = UX copy (policy/texts.py),
                   checks = [{text: p.text, source: SourceChip from p} for each quick-check passage])
  # checks are sent inline, so "Show the checks" opens without another turn; a later choice on the card is a
  # CARD_CHOICE on the open task (graph-core §3 step 10) and re-sends nothing.
```

Label: [Decided §7, engineering]. Basis: graph-tools cross-topic C-11 (its recommended option); OpenAPI
`QuickChecksBlock.checks` (array of `{text, source}` or null); DO-4 §8 `TurnFacts.quick_checks`, `.passages`.
Consumers: AEA-38, AEA-21.

---

## 9. Node functions, one module at a time (signature-check pass, GRN-11)

**In practice.** `build_graph(deps)` (AEA-21) registers each node as
`timed_node("gates", partial(gates, deps=deps), deps)`; once `deps` is bound, every node has graph-core §4's `NodeFn`
shape `(state, runtime) -> <its update>`. `runtime` is LangGraph's `Runtime[TurnContext]` (`context_schema`, langgraph
1.2.16), so a node reads `runtime.context.now`, `.ids`, `.budget`, `.intake`. Each node returns **only the keys DO-3
§5.3 gives it**; the return type is a `TypedDict` naming exactly those keys, so a node that writes a key it does not
own fails the type check, not a review. A7a's stubs (AEA-21) have these signatures and raise `NotImplementedError`.
[Decided §7, engineering]

### 9.1 Update types (`domain/state.py`, AEA-02)

```python
# total=False: a node returns a subset (e.g. no `halt` unless one fires). Keys and types are ConversationState's.
class LoadContextUpdate(TypedDict, total=False):
    settled: Settled; controller: Controller; identity: IdentityState; chat_window: list[ChatLine]
    counters: FailureCounters                         # only `timeouts` changes here (graph-core §8)
class GatesUpdate(TypedDict, total=False):
    gate: GateDecision; check_events: tuple[CheckEvent, ...]; plan: Plan; halt: Halt   # plan: burning "no" only (§6)
    burning_card_id: str | None                       # R-G-11: graph-core §3's durable key; this node is its ONLY writer
                                                      #   (set on BURNING_ASK, None on every other result)
class SafetyUpdate(TypedDict, total=False):
    handoff: HandoffResult; halt: Halt
class IdentityNodeUpdate(TypedDict, total=False):
    identity: IdentityState; identity_step: IdentityStep; halt: Halt
class PlannerUpdate(TypedDict, total=False):
    planner: PlannerOutcome; halt: Halt                # key renamed by graph-core §9 (GRC-11)
class DangerUpdate(TypedDict, total=False):
    danger: DangerAssessment; check_events: tuple[CheckEvent, ...]; halt: Halt     # `classifier` event (§1)
class PlanJoinUpdate(TypedDict, total=False):
    plan: Plan; check_events: tuple[CheckEvent, ...]; halt: Halt                   # BRAKE_TASKS → `brake` event
class SpecialistUpdate(TypedDict, total=False):
    specialist_results: list[SpecialistResult]; check_events: tuple[CheckEvent, ...]; halt: Halt
class EscalationUpdate(TypedDict, total=False):
    escalation: EscalationDecision
class HandoffNodeUpdate(TypedDict, total=False):
    handoff: HandoffResult; halt: Halt
class FactsUpdate(TypedDict, total=False):
    facts: TurnFacts; settled: Settled; open_tasks: list[OpenTask]; shown_slots: list[ShownSlot]
    last_lookups: LastLookups; pending_change: ChangeRequestRef | None; counters: FailureCounters
class ResponderUpdate(TypedDict, total=False):
    draft: ResponderDraft | None; check_events: tuple[CheckEvent, ...]; halt: Halt  # BRAKE_SONNET_CALLS → `brake`
class BriefUpdate(TypedDict, total=False):
    brief_extraction: BriefExtraction | None; check_events: tuple[CheckEvent, ...]; halt: Halt
class ChecksUpdate(TypedDict, total=False):
    checked: CheckedReply
class ComposeUpdate(TypedDict):
    reply: ComposedReply

class SpecialistSend(TypedDict):                      # the Send payload route_act_plan builds, one per planned task
    planned: PlannedTask                              #   (graph-core §11); run_specialist's input instead of the state.
                                                      #   CHANGED (R-G-12): was `task: SpecialistTask`; the act node builds
                                                      #   the task (§9.5), because the router does no I/O or masking
    state: ConversationState                          # the state at fan-out; scope_for(state, ctx) reads it (graph-tools §2)
```

### 9.2 Module: agent/nodes/load_context.py (AEA-34)

```python
def load_context(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> LoadContextUpdate: ...
    # one read-only tx: core.settled_for(thread_id, ctx.now) (graph-core §6), controller from
    # core.conversations.lookup, core.reads.identity_state, core.messages.recent → chat_window with graph-core §7's
    # limits, core.turns.timeouts_for → counters.timeouts. Writes nothing to check_events (graph-core §11).
```

### 9.3 Module: agent/nodes/front.py (AEA-36)

```python
def gates(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> GatesUpdate: ...
    # decide_gate(ctx.intake, flags) (graph-core §3); CheckEvent.from_gate; the code-built plan on burning "no" (§6)
def safety(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> SafetyUpdate: ...
    # the fixed safety instruction first (R-5), then deps.handoff.open for the P0/P1 case; no model (§7 CAP-2)
def identity(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> IdentityNodeUpdate: ...
    # locate (Locator.from_form(ctx.intake.form)), send_code, or verify(ctx.intake.code_digits) on deps.identity
    #   (graph-tools §5); then core.reads.identity_state for the refreshed `identity`
```

### 9.4 Module: agent/nodes/plan.py (AEA-37)

```python
def planner(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlannerUpdate: ...
def danger_classifier(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> DangerUpdate: ...
def plan_join(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> PlanJoinUpdate: ...
    # join_plan(...) as DO-4 §4 and §5 here; planner and danger_classifier run in one superstep
```

### 9.5 Module: agent/nodes/act.py (AEA-39)

```python
def run_specialist(payload: SpecialistSend, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> SpecialistUpdate: ...
    # task = build_specialist_task(payload["planned"], payload["state"], ctx, scheduling=inputs, limits=deps.limits),
    #   where inputs = deps.scheduling.slice_inputs(customer_id) for a scheduling task whose state.identity is
    #   verified (cases.md §4, R-G-19), else None; the read closes before the run (DO-3 §2.3 rule 1).
    # then deps.specialists.run(task, scope_for(payload["state"], ctx), ctx) → [result]; a result.brake in
    #   BRAKE_HALTS → halt + CheckEvent.from_halt; emits the failure signals of §4 (the runner emits none)
def build_specialist_task(planned: PlannedTask, state: ConversationState, ctx: TurnContext, *,
                          scheduling: SchedulingSliceInputs | None, limits: Limits) -> SpecialistTask: ...
    # agent/nodes/act.py (AEA-39), pure. THE builder of SpecialistTask (R-G-12) [Decided §7, engineering]:
    #   customer_text = redact(state.turn_input.text_store, RedactionProfile.SONNET).text; task_messages = the open
    #   task's customer messages, same profile; slice per planned.specialist (DO-4 §5): SchedulingSlice(customer_zone
    #   and member and appointments from `scheduling`, or None / False / () when it is None; shown_slots =
    #   state.shown_slots; pending_change = state.pending_change is not None; bookings_left = the R-41 booking cap in
    #   limits − state.counters.bookings); offer_quick_checks per graph-tools §6's three conditions. No customer_id.
def escalation(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> EscalationUpdate: ...
    # decide_escalation(inputs) (DO-4 §6; cases.md §3.4), incl. rule 6 for brake halts (graph-core §5).
    #   inputs.models_disabled = deps.ledger.models_disabled() (graph-core §4, R-G-13); inputs.now = ctx.now (R-G-15)
def handoff(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> HandoffNodeUpdate: ...
    # deps.handoff.open(request, ctx) once per turn, idempotent on the turn's ActionKey. On the PERSON gate the node
    #   builds the request itself: customer_requested_person, priority_for → P3, rule_id "R2.person", trigger "gate"
    #   (cases.md §3.4 residual note, R-G-14)
```

### 9.6 Module: agent/nodes/reply.py (AEA-38)

```python
def facts(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> FactsUpdate: ...
    # the one committer of durable task state (DO-3 §5.3); re-reads settled; graph-core §8 counters; §8 quick checks
def responder(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ResponderUpdate: ...
def brief(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> BriefUpdate: ...
    # §3: only on a turn whose case opened; attach_brief before and after the extraction
def checks(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> ChecksUpdate: ...
    # R-46 (DO-4 §10, §2 here) on the draft, and the brief's quote and fact checks (§3)
```

### 9.7 Module: agent/nodes/compose.py (AEA-21)

```python
def compose(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps,
            composer: ReplyComposer) -> ComposeUpdate: ...
    # {"reply": composer.compose(state, ctx)} (graph-core §13); turn_trace(state, reply) stays run_graph's (graph-core §2)
```

Consumers: AEA-02 (§9.1 types), AEA-21 (stubs with these signatures, `build_graph`, compose; `route_act_plan` sends
`planned`), AEA-34, 36, 37, 38, 39 (each fills its module; AEA-39 also `build_specialist_task`).
Residual pass (2026-10-21, `docs/plans/7b-decisions/residuals-graph.md`): R-G-11 (`GatesUpdate.burning_card_id`),
R-G-12 (`SpecialistSend.planned`, `build_specialist_task`), R-G-13…R-G-15 and R-G-19 (escalation inputs, person-gate
rule id, slice inputs).

---

## Cross-topic assumptions

1. **graph-core (state): accepted at merge** (graph-core §11, GRC-16): `check_events: Annotated[tuple[CheckEvent, ...],
   add_turn_events]`, reset by its reducer (not by `load_context`). **Settled at merge** (graph-core §2, GRC-20,
   GRC-21): `RunGraph` returns `GraphOutcome(reply, turn_trace, check_events, halt)`; `run_graph` filters by `turn_id`
   and adds its `RECURSION_LIMIT` event, so `TurnService` never reads state.
2. **graph-core (`GraphDeps`, routers): accepted at merge** (graph-core §4 `cases: CaseService`, `agent/signals.py`;
   §11 edge 1 `plan_join → escalation` on `plan.planner_failed and not plan.tasks`, edge 2 `gates → route_act_plan`
   on `burning_answer == "no"`).
3. **cases (AEA-10 storage): accepted at merge** (cases §1.1 `check_events` columns; §1.2
   `core.check_events.append(event: CheckEvent, thread_id: ThreadId) -> int`,
   `core.lookup_log.for_thread(thread_id) -> tuple[LookupRow, ...]`; §5 `attach_brief` is an upsert per case).
4. **cases (AEA-14 escalation): accepted at merge** (cases §3.4 rule 6: `plan.planner_failed and not plan.tasks` →
   `ai_failure` P3, `degraded=True`, rule id `AI.planner_failed`).
5. **data (AEA-03 texts): accepted at merge** (`booking.urgent_note`, data.md `booking` group).
6. **web (AEA-23 logging, AEA-40 turn service): accepted at merge** (web §10 `signal` record on the LOG allow-list;
   §9 step 7 persists both event carriers).
7. **graph-tools:** `SpecialistRunner.run` (graph-tools §2) keeps filling `SpecialistResult.brake` / `failure` and
   emits no signal.

Accepted from siblings: graph-tools C-11 (quick checks into `TurnFacts`, inline `checks` on the offer card) → §8.
