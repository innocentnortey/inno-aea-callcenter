# Signatures and types added at Stage 7 (2026-10-21), graph (core)

Part **core** of the graph topic (prefix GRC). It owns: where the per-turn types live, `TurnContext`, `TurnInput`
(with `form` and `message_id`), how the intake values and code digits reach the graph without entering state,
`GateFlags` and the gate's card rules, `GraphDeps`' fields, node spans, halt routing, the `settled_for` signature, the
chat window limits, what increments `FailureCounters`, and the type of the planner state key. Added at merge
(2026-10-21): the `check_events` key and two router edges (§11), the `specialists` and `cases` fields and
`agent/signals.py` (§4), `GraphOutcome` as `RunGraph`'s return and `TurnTrace` / `TurnRecord` for the turn row (§2),
and the answers to other topics' requests to graph (end of file). Added at the final cross-reference pass: AEA-02's
one `Settings` field list (§12). Added at the signature-check pass (2026-10-21): `NodeFn` (§4), `ReplyComposer` (§13),
`Zone`, `FeeNote`, `VisitView` (§14). Residual pass (2026-10-21, `docs/plans/7b-decisions/residuals-graph.md`): the pure
`TurnPayload` (§2, R-G-20), `GraphOutcome.closed_every_open_task` (§2, R-G-21), the `gate_result()` table (§3, R-G-10),
`GraphDeps.ledger` (§4, R-G-13), `RuleMatches` / `SafetyKind` in `domain/turn.py` (§8, R-G-1), the `SpecialistSend`
payload (§11, R-G-12), no `Settings.langfuse_export()` (§12, R-G-6), the wave-0 merge order for `RoleSpec.redaction`
(§12, R-G-18), and `Zone` / `FeeNote` owned by cases.md §2 (§14, R-G-2). The sibling parts (`graph-tools.md`,
`graph-nodes.md`) are referenced by type name only. Decisions and their basis: `docs/plans/7b-decisions/graph-core.md`
(GRC-1…GRC-25) and `residuals-graph.md` (R-G-n).

Labels: **[Source: …]** settled by a cited document; **[Decided §7, engineering]**; **[A]** an engineering default a
named measurement replaces. Everything below extends DO-4 (`contracts/internal-components.md`); a type not shown is
unchanged.

---

## 1. Where the per-turn types live (GRC-1, GRC-10)

```python
# domain/turn.py (AEA-02, wave 0). MOVED from agent/context.py: services take a TurnContext (HandoffService.open,
# DO-4 §7; ModelGateway.*, DO-4 §12), and services never import agent/ (DO-3 §2.1).
#   [Source: slice plan row AEA-02 "TurnContext in domain/turn.py so services never import agent/"]
TurnIds, TurnBudget, TurnContext, SpanHandle, CardChoice, GateFlags,     # definitions below; PlannerTrace, TurnTrace,
TurnRecord, GraphOutcome                                                  #   TurnRecord, GraphOutcome added at merge (§2)
TurnPayload (+ TextPayload, ChoicePayload, CodePayload, FormPayload)      # residual pass, R-G-20 (§2)
SafetyKind, RuleMatches                                                   # residual pass, R-G-1 (§8): DO-4 §3 put them in
                                                                          #   gates/rules.py, which domain/ may not import

# agent/context.py (AEA-21) keeps GraphDeps only (it names services, so it stays above them).
# ports/runtime.py (AEA-02) imports SpanHandle from domain/turn.py and re-exports it; TraceSink is unchanged
#   (models.md §4). SpanHandle's fields are models.md's, unchanged; only its file moves, because domain/ may not
#   import ports/ (ports → domain, DO-3 §2.1).   [Decided §7, engineering]

# adapters/sqlite/repos_{core,spend,identity,booking,cases,staff,ops}.py: AEA-02 creates all seven as empty classes
#   with a constructor taking the connection, so UnitOfWork's TYPE_CHECKING imports resolve in wave 0; AEA-10 and
#   the owning areas fill the bodies.   [Source: DO-4 §13 docstring; slice plan row AEA-02 "the seven
#   adapters/sqlite/repos_*.py as empty classes with constructors"; row AEA-10 "shells from 02"]
```

Consumers: AEA-02 (writes), AEA-20, AEA-21, AEA-29, AEA-35…AEA-40, AEA-42, AEA-51.

---

## 2. TurnInput, TurnContext and the intake carrier (GRC-10)

**In practice.** Omar submits the locate card: `{"kind": "form", "card_id": "locate-7c1e…", "values": {"name": "Omar
Patel", "phone": "512-555-0102"}}`. `TurnService` step 4 runs `parse_intake` once, stores the message row as
`"[details submitted]"` and gets its id (say 412). The graph's state receives `TurnInput(kind="form",
text_store="[details submitted]", message_id=412, card_id="locate-7c1e…")`; the name and phone travel only in
`TurnContext.intake`, which LangGraph never checkpoints. The identity node reads `ctx.intake.form` and calls
`IdentityService.locate`. After the turn, the phone exists nowhere except the lookup it fed.

```python
# domain/turn.py (AEA-02)                                               [Decided §7, engineering] GRC-10
class CardChoice(MeridianModel):                      # NEW: DO-4 named it without fields; = OpenAPI ChoicePayload
    card_id: str                                      # client-supplied, untrusted: matched by §3's rules, never trusted
    option: str                                       # e.g. "56" (slot), "yes", "not_sure", "new_code"

class TextPayload(MeridianModel):                     # NEW (R-G-20) = OpenAPI TextPayload
    kind: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=2000)
class ChoicePayload(CardChoice):                      # NEW (R-G-20) = OpenAPI ChoicePayload; CardChoice's two fields + kind
    kind: Literal["choice"] = "choice"
class CodePayload(MeridianModel):                     # NEW (R-G-20) = OpenAPI CodePayload
    kind: Literal["code"] = "code"
    card_id: str
    code: SecretStr                                   # ^[0-9]{6}$; secret: never logged, never in state (DO-4 §3 code_digits)
class FormPayload(MeridianModel):                     # NEW (R-G-20) = OpenAPI FormPayload
    kind: Literal["form"] = "form"
    card_id: str
    values: FormValues                                # DO-4 §3 FormValues (phone a SecretStr)
TurnPayload = Annotated[Union[TextPayload, ChoicePayload, CodePayload, FormPayload], Field(discriminator="kind")]
    # The ONE Python type of CON-2's payload: DO-4 §14 RunTurn.payload and parse_intake(payload: TurnPayload) (AEA-12).
    #   Pure, in domain/turn.py, so gates/ can import it (DO-3 §2.1). The OpenAPI schemas win on field names and limits;
    #   web/schemas/chat.py (AEA-40) validates the request body into this union and declares no second payload model.
    #   [Decided §7, engineering, R-G-20]

class Intake(MeridianModel):                          # DO-4 §3, one field added
    ...                                               # kind, text_store, code_digits, form, card_number_seen, choice
    card_id: str | None = None                        # NEW: the card a choice, code or form answers (OpenAPI payloads)

class TurnInput(MeridianModel):                       # DO-4 §1, CHANGED; the ONLY intake data in state
    turn_id: TurnId
    message_id: int                                   # NEW: the `messages` row TurnService step 4 wrote for this turn
                                                      #   (core.messages.append → int, cases.md §1.2); ToolCallScope
                                                      #   and the lookup log carry it (DO-4 §5 line "message_id: int")
    kind: Literal["text", "choice", "code", "form"]   # CHANGED: + "form" (OpenAPI FormPayload, UXR-3)
    text_store: str                                   # STORE-redacted, as Intake.text_store
    card_id: str | None = None                        # NEW: = Intake.card_id
    choice: CardChoice | None = None
    card_number_seen: bool = False                    # NEW: = Intake.card_number_seen (R-13 reply)
    received_at: datetime                             # demo clock
    # Never here: code digits, FormValues (name, phone, customer_id, invoice_number, zip_or_city).

@dataclass(frozen=True)
class TurnContext:                                    # DO-4 §2, CHANGED; LangGraph runtime context (`context_schema`)
    ids: TurnIds
    budget: TurnBudget
    now: datetime                                     # ONE demo-clock reading per turn
    demo_session: str
    span: SpanHandle                                  # NEW (models.md MOD-10): TurnService (AEA-40) opens trace.turn(ids);
                                                      #   PersonRequestService (AEA-42) opens its own (web.md §8, MC-17)
    intake: Intake | None = None                      # NEW: this turn's parsed intake incl. code_digits and form
                                                      #   (SecretStr values). None outside a CON-2 turn (CON-4, jobs).
                                                      #   Not state: never checkpointed, never in a prompt, log or trace.

class PlannerTrace(MeridianModel):                    # NEW at merge (GRC-21): codes only, never text or a value
    model: str                                        # PlannerOutcome.model (the Jev or Sonnet model that answered or failed)
    fallback_used: bool                               # PlannerOutcome.fallback_used (Sonnet planner ran, SDQ-6)
    failure: ProviderFailureKind | None               # PlannerOutcome.failure.kind
    plan_mode: Literal["talk", "act"] | None          # Plan.mode; None when no plan was built (a halt before plan_join)
    plan_source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"] | None   # Plan.source
    intents: tuple[TaskIntent, ...] = ()              # Plan.tasks' intents, in order
    handoff_request: HandoffReason | None = None      # Plan.handoff_request
    topic: Literal["booking", "membership", "billing", "warranty", "other"] | None = None   # Plan.topic (M-3)
    planner_failed: bool = False                      # Plan.planner_failed (graph-nodes §5)

class TurnTrace(MeridianModel):                       # NEW at merge (GRC-21): the turn row's decision fields. Codes only, so
                                                      #   it is safe to persist and log. Built by compose's pure turn_trace()
    gate_result: Literal["clear", "safety", "burning_unclear", "danger", "person_requested", "ai_paused"]   # DO-6 values:
                                                      #   state.danger.label when state.danger.raised (a classifier raise
                                                      #   is recorded as danger / burning_unclear, DO-6 CAP-2, M-16), else
                                                      #   state.gate.gate_result() (DO-4 §3)
    path: TurnPath                                    # = reply.path (DO-4 §9)
    outcome: Literal["answered", "acted", "safety_reply", "handed_off", "to_staff", "degraded_handoff"]   # = reply.outcome
    degrade_reason: Literal["model_error", "tool_error", "timeout", "brake", "spend_cap", "rate_limit"] | None = None
                                                      # = reply.degrade_reason
    planner: PlannerTrace | None = None               # from state.planner (§9) and state.plan; None when the planner did
                                                      #   not run (a rule gate, a card, a code turn)
    danger_raised: bool = False                       # state.danger.raised; False when the classifier did not run
    specialists_run: tuple[Literal["knowledge", "account", "scheduling"], ...] = ()   # each this-turn SpecialistResult's
                                                      #   `kind` (its discriminator, DO-4 §5), in order

# agent/nodes/compose.py (AEA-21), pure; the ONE builder of TurnTrace:
def turn_trace(state: ConversationState, reply: ComposedReply) -> TurnTrace: ...
    # run_graph calls it on the final state (and, on GraphRecursionError, on the last checkpoint's state with
    #   compose's halt reply). No state key holds it.

class TurnRecord(MeridianModel):                      # NEW at merge (GRC-21): DO-4 §13 named it without fields. The
                                                      #   argument of core.turns.finish(turn_id, record) → one `turns` row
    status: Literal["completed", "failed"]            # failed → the same turn_id may re-run (web.md §9 rate_limited)
    trace: TurnTrace                                  # DO-6 `turn` fields gate_result, planner decision, specialists run,
                                                      #   outcome, degrade_reason (+ path, danger_raised)
    replied_at: datetime; server_ms: int              # DO-6 timing boundary; turn_id, ids, sequence and received_at
                                                      #   are stored by core.turns.begin(ids, received_at)
    model_calls: int; input_tokens: int; output_tokens: int; cost_usd: float   # summed from this turn_id's spend_ledger rows
    tool_calls: int                                   # this turn_id's lookup_log rows (one per dispatched call, graph-tools §1)
    trace_id: str | None; trace_export: ExportStatus  # models.md §4 (MOD-9, MOD-11)
    response: str                                     # the serialised response, opaque; replayed on a repeated turn_id
                                                      #   (cases.md §1.2 core.turns.begin / finish)

class GraphOutcome(MeridianModel):                    # NEW at merge (GRC-20): what run_graph hands TurnService
    reply: ComposedReply
    turn_trace: TurnTrace                             # GRC-21: turn_trace(final state, reply); the turn row's decision fields
    check_events: tuple[CheckEvent, ...] = ()         # this turn's events, ready to persist (built as §11 says):
                                                      #   state.check_events filtered to this turn_id + state.checked.events;
                                                      #   on RECURSION_LIMIT, run_graph's own CheckEvent.from_halt event
                                                      #   (graph-nodes §1) after the last checkpoint's events
    halt: Halt | None = None                          # the turn's halt, if any (DEADLINE → step 6's TURN_TIMEOUT reply)
    closed_every_open_task: bool = False              # NEW (R-G-21 = web R-W-5): run_graph sets it True when the final
                                                      #   state's plan is an `act` plan with at least one task AND, after
                                                      #   facts, no state.open_tasks item has status != "done"; False on a
                                                      #   halt or GraphRecursionError. DO-7 M-18's end rule "a turn that
                                                      #   closes every open task": TurnService (AEA-40) applies web.md §9's
                                                      #   outcome table to it and never reads state

RunGraph = Callable[[TurnInput, TurnContext], GraphOutcome]   # DO-4 §14 step 5's injected callable, CHANGED at merge:
                                                              #   was → ComposedReply, which left TurnService no way to
                                                              #   read the final state's check events or decision fields
```

**What `TurnService` (AEA-40) does with it**, in web.md's step terms: step 5 calls `run_graph(input, context)` and gets
a `GraphOutcome`; step 6 reads `outcome.halt` (`DEADLINE` → the `TURN_TIMEOUT` reply from settled, and the trace's
`outcome` / `degrade_reason` become `degraded_handoff` / `timeout`); step 7 persists the reply message, the turn record
(`TurnRecord(trace=outcome.turn_trace, …)`) and the check events, one `core.check_events.append(event, thread_id)` row
per item of `outcome.check_events`; step 8 returns `outcome.reply` as the `TurnResponse`. Paths that run no graph build
the `TurnTrace` themselves: CON-4 (`gate_result="person_requested"`, `outcome="handed_off"`, web.md §8) and the
rate-limited turn (`outcome="degraded_handoff"`, `degrade_reason="rate_limit"`, web.md §9).

**Rules that make "never in state" true** [Decided §7, engineering]:
1. `TurnService` (AEA-40) builds the `Intake` once (`parse_intake`, AEA-12), writes the message row, then builds
   `TurnInput` from the Intake's non-secret fields plus the row id, and `TurnContext(…, intake=intake)`.
2. The graph runs with `context_schema=TurnContext` (langgraph 1.2.16). **The `config["configurable"]["turn"]` fallback
   in DO-4 §2 is not allowed to carry `intake`**: LangGraph copies configurable values into checkpoint metadata. If the
   fallback is ever needed, `intake` moves to a per-turn in-process map keyed by `turn_id` and cleared in `finally`.
3. Who reads `ctx.intake`: the gates node (`decide_gate(intake, flags)`) and the identity node (`verify` with
   `intake.code_digits`, `locate` with a `Locator` built from `intake.form`; `Locator` is graph-tools'). A where form
   for an open scheduling task is copied into that task's `details.zip`/`city` by the facts node, not its name/phone.
4. **Test (AEA-51, `risk::security`):** a CON-2 code turn with sentinel digits `"914276"` and a form turn with phone
   `"512-555-0199"`; neither string appears in any checkpoint blob or metadata row, `messages`, `turns`, `lookup_log`,
   `check_events`, log line, trace span payload or model request recorded by the fake gateway.

Consumers: AEA-02 (types, incl. `PlannerTrace`, `TurnTrace`, `TurnRecord`, `GraphOutcome`), AEA-10 (`core.turns.finish`
stores `TurnRecord`), AEA-12, AEA-21 (`turn_trace`, `run_graph`), AEA-36 (gates, identity), AEA-35/39 (`message_id` into
`ToolCallScope`), AEA-40 (builds both; persists `TurnRecord`), AEA-42 (`TurnContext(…, span=span, intake=None)` inside its
own `trace.turn(ids)`; its own `TurnTrace`; web.md §8, MC-17), AEA-51.

---

## 3. GateFlags and how cards are routed (GRC-3, GRC-4, GRC-5)

```python
# domain/turn.py (AEA-02)                                               [Decided §7, engineering] GRC-5
class GateFlags(MeridianModel):                       # the only state decide_gate sees; built from state by code
    ai_paused: bool                                   # state.controller.kind == "human"
    burning_card_id: str | None                       # state.burning_card_id: the R-7 question is waiting for an answer
    code_card_open: bool                              # state.identity.status == "code_sent"
    open_task_ids: tuple[str, ...]                    # state.open_tasks with status != "done"

# gates/gate.py (AEA-12)
def flags_from_state(state: ConversationState) -> GateFlags: ...       # pure
def card_target(card_id: str) -> CardTarget: ...                       # pure; parses the prefix
CardTarget = tuple[Literal["burning", "code", "locate", "task", "unknown"], str | None]   # (kind, task_id)
def burning_card_id(turn_id: TurnId) -> str: ...       # "burn-<turn_id>"; compose uses the same function for the card

# Card ids are minted by code only, with these prefixes:                 [Decided §7, engineering] GRC-5
#   "burn-<turn_id>"   the R-7 question card (OpenAPI BurningCheckBlock)
#   "code-<turn_id>"   the code card ("send a new code" is a choice on it)
#   "locate-<turn_id>" the locate form
#   "<task_id>.<n>"    any card that belongs to an open task (slot picks, where form, yes/no, quick checks)

# domain/state.py (AEA-02): ConversationState gains ONE durable key            GRC-4
    burning_card_id: str | None = None                # writer: the gates node ONLY. Set to burning_card_id(turn_id) when
                                                      #   the gate returns BURNING_ASK; set to None on every other result.
```

**`decide_gate` order and card rules** (AEA-12) [Decided §7, engineering, except item 0]:

| Step | Input | Result |
|---|---|---|
| 0 | the order of `AI_PAUSED` and `SAFETY` | **Innocent's (GRC-3).** Built as `SAFETY` first, then `AI_PAUSED`, until he answers; the order is one tuple in `gate.py` |
| 1 | `rules.safety` (R-5) | `SAFETY` |
| 2 | `flags.ai_paused` | `AI_PAUSED` |
| 3 | a choice whose card is `burning` (any `burn-` card, current or stale: a "yes" is never ignored) | `BURNING_ANSWER`, `burning_answer` = `yes` / `no` / `unsure` (option `not_sure`) |
| 4 | `rules.burning_unclear` | `BURNING_ASK` |
| 5 | `rules.danger_words` | `DANGER_RULE` |
| 6 | `rules.person` | `PERSON` |
| 7 | text while `flags.burning_card_id` is set (no step 1–6 match) | `BURNING_ANSWER`, `burning_answer="unsure"` (R-7 "If unclear → a conditional safety instruction") |
| 8 | kind `code`; or a choice on a `code` card while `flags.code_card_open` | `CODE_ENTRY` |
| 9 | kind `form` on a `locate` card | `LOCATE` |
| 10 | choice or form on a `task` card whose `task_id` is in `flags.open_task_ids` | `CARD_CHOICE`, `resume_task_id = task_id` |
| 11 | anything else (text; a stale or unknown card) | `FREE_TEXT`; a stale choice's `text_store` is its option string, a stale form's is `"[details submitted]"` and its values are discarded |

**`GateDecision.gate_result()`, every kind** (AEA-02 implements it; DO-4 §3 gave only the four `clear` kinds)
[Decided §7, engineering, R-G-10]:

| `kind` | `gate_result()` | Why |
|---|---|---|
| `SAFETY` | `safety` | R-5 |
| `AI_PAUSED` | `ai_paused` | R-31 |
| `BURNING_ASK` | `burning_unclear` | R-7: the question is asked because the breaker state is unknown |
| `BURNING_ANSWER`, `burning_answer="yes"` | `safety` | routes to safety, P0 (R-5); the same DO-6 value as a stated breaker trip |
| `BURNING_ANSWER`, `burning_answer="unsure"` | `burning_unclear` | routes to safety with the conditional instruction, P1 (R-7 "If unclear") |
| `BURNING_ANSWER`, `burning_answer="no"` | `clear` | both dangers ruled out; the turn routes to booking (graph-nodes §6), no safety instruction is sent |
| `DANGER_RULE` | `danger` | R-8 rule half |
| `PERSON` | `person_requested` | R-2 |
| `CODE_ENTRY`, `LOCATE`, `CARD_CHOICE`, `FREE_TEXT` | `clear` | DO-4 §3 (code-design C-6) |

So M-14 and M-17 count a "yes" as a safety turn and an "unsure" as a burning-unclear turn, exactly as if the rules had
matched them in words. AEA-12 asserts the three `BURNING_ANSWER` rows through `gate_result()`.

**The gates node's update carries `burning_card_id`** (R-G-11): graph-nodes §9.1 `GatesUpdate` lists it beside `gate`,
`check_events`, `plan` and `halt`, so the only writer this section names can write it.

Consumers: AEA-02, AEA-12, AEA-21 (compose mints card ids with these prefixes), AEA-36 (gates node writes
`burning_card_id`), AEA-28/33/35 (task cards use `<task_id>.<n>`).

---

## 4. GraphDeps, node spans and the runner (GRC-6)

```python
# agent/context.py (AEA-21)                                              [Decided §7, engineering] GRC-6
@dataclass(frozen=True)
class GraphDeps:                                      # DO-4 §2's nine fields, plus:
    gateway: ModelGateway; retrieval: RetrievalIndex; uow: UnitOfWorkFactory
    identity: IdentityService; scheduling: SchedulingService; handoff: HandoffService
    brief: BriefAssembler; demo: DemoService; limits: Limits
    trace: TraceSink                                  # NEW: node spans (below)
    specialists: SpecialistRunner                     # NEW: defined in stage7/graph-tools.md §2 (GRT-6); no dispatcher
                                                      #   field (the runner holds it). Read by the act node (AEA-39).
    cases: CaseService                                # NEW: DO-4 §13 / cases.md §5 (services/cases.py). Read by the
                                                      #   reply node for open_case_for_thread and attach_brief
                                                      #   (stage7/graph-nodes.md §3, GRN-8). Merge addition, GRC-15.
    ledger: ModelsStatus                              # NEW (R-G-13): the escalation node's EscalationInputs.models_disabled
                                                      #   = deps.ledger.models_disabled() (cases.md A-5). The container
                                                      #   passes the same LedgerService (models.md §6), which satisfies
                                                      #   ModelsStatus structurally; no node gets the whole ledger.

class ModelsStatus(Protocol):                         # agent/context.py (AEA-21), beside GraphDeps   [Decided §7, R-G-13]
    def models_disabled(self) -> bool: ...            # = LedgerService.models_disabled (models.md §6): our cap reached or
                                                      #   any provider circuit open

# agent/signals.py (AEA-21, NEW file): emit_signal(ids: TurnIds, record: SignalRecord) -> None
#   defined in stage7/graph-nodes.md §4 (GRN-4); SignalRecord / SignalName live in domain/turn.py (AEA-02).
#   AEA-21 owns the file; nodes import it; it logs through web/logging.py's allow-list. Merge addition, GRC-17.

# agent/graph.py (AEA-21): the node function type (GRC-23). Each node module's functions are signed in
#   stage7/graph-nodes.md §9 as fn(state, runtime, *, deps); build_graph binds deps with functools.partial, which
#   leaves exactly this shape. Runtime is langgraph.runtime.Runtime (langgraph 1.2.16, context_schema=TurnContext).
NodeInput = Union[ConversationState, SpecialistSend]                 # SpecialistSend: the Send payload, graph-nodes §9
NodeUpdate = Union[LoadContextUpdate, GatesUpdate, SafetyUpdate, IdentityNodeUpdate, PlannerUpdate, DangerUpdate,
                   PlanJoinUpdate, SpecialistUpdate, EscalationUpdate, HandoffNodeUpdate, FactsUpdate,
                   ResponderUpdate, BriefUpdate, ChecksUpdate, ComposeUpdate]   # one TypedDict per node, graph-nodes §9
NodeFn = Callable[[NodeInput, Runtime[TurnContext]], NodeUpdate]

# agent/graph.py (AEA-21): every node is registered through one wrapper; nodes never call the sink themselves.
def timed_node(name: str, fn: NodeFn, deps: GraphDeps) -> NodeFn: ...
    # t0 = monotonic(); run fn; finally deps.trace.node(ctx.span, name, elapsed_ms, status)
    # status: "ok" | "halted" (the node returned a halt) | "error" (it raised; the exception propagates)
    # The span carries the name, timing and status only: no text, no values (DO-6 Content and redaction).
```

[Source: observability-contract.md line 65, rule 18 "each node, model call and tool call is a timed span";
models.md MOD-10 for the span on `TurnContext`.]

Consumers: AEA-21 (wrapper, fields, `ModelsStatus`, `agent/signals.py`), AEA-34…AEA-39 (nodes get timing for free),
AEA-38 (`deps.cases`), AEA-39 (`deps.specialists`, `deps.ledger`), AEA-51 (wires `trace`, `specialists`, `cases` and
`ledger` from the container; CAP-1 finds the node spans).

---

## 5. Halt routing (GRC-7)

```python
# agent/routers.py (AEA-21)                                             [Decided §7, engineering] GRC-7
BRAKE_HALTS = {BRAKE_TASKS, BRAKE_TOOL_ROUNDS, BRAKE_SONNET_CALLS, BRAKE_IDENTICAL_CALL}

def halt_route(state: ConversationState) -> Literal["escalation", "compose"] | None: ...
    # Every router calls this first. None → no halt, route as usual.
    # halt.reason in BRAKE_HALTS and state.escalation is None → "escalation"
    #     → decide_escalation rule 6 (ai_failure, degraded) → handoff → facts → compose
    # every other halt (DEADLINE, SPEND_CAP, PROVIDER_SPEND_CAP), or a brake after escalation ran → "compose"
# After `facts`, a halted state skips responder, brief and checks: compose builds the code reply (DO-4 §11 row).
```

| Halt | Path | What the customer gets [Source: DO-4 §11] |
|---|---|---|
| `BRAKE_*` | → escalation → handoff → facts → compose | "Handoff reply with what is settled"; `ai_failure` P3 case (DO-4 §6 rule 6; cases.md §3.4) |
| `DEADLINE` | → compose | `TURN_TIMEOUT` notice, *Try again* (same `turn_id`) and *Talk to a person*; no case |
| `SPEND_CAP`, `PROVIDER_SPEND_CAP` | → compose | `SPEND_CAP_REACHED` notice + person key; no case |
| `RECURSION_LIMIT` | LangGraph raises; `run_graph` (AEA-21) catches `GraphRecursionError` and returns a `GraphOutcome` (§2) with compose's halt reply built from `core.settled_for`, the halt, and its `brake` check event (§11) | as a brake, but no case (the graph cannot reach `handoff` after the error) |

Compose builds every halt's reply blocks; `TurnService` step 6 turns a returned `DEADLINE` halt into the
`TURN_TIMEOUT` notice fields (DO-4 §14).

Consumers: AEA-21, AEA-39 (escalation receives brake halts), AEA-38 (facts skips the responder on a halt), AEA-40.

---

## 6. The one `Settled` builder (GRC-12)

```python
# adapters/sqlite/repos_core.py (AEA-10 body)          [Source: slice plan row AEA-10 "settled_for(thread_id), the one
#                                                        builder of Settled … both load_context (34) and facts (38) call"]
core.settled_for(thread_id: ThreadId, read_at: datetime) -> Settled
    # Reads actions (core.actions.for_thread) + the thread's open case and its promise. read_at = the caller's demo-clock
    # reading (ctx.now in the graph). Callers: load_context (AEA-34), facts (AEA-38), compose's RECURSION_LIMIT path
    # (AEA-21), TurnService (AEA-40), PersonRequestService (AEA-42). Signature [Decided §7, engineering].
```

---

## 7. Chat window limits (GRC-9, GRC-14)

```python
# policy/limits.py (AEA-01 file; a small follow-up if AEA-01 has merged)   GRC-9, GRC-14
@dataclass(frozen=True)
class ContextLimits:
    window_turns: int = 10            # [A] R-45 "about 10". Lines of the last 10 turn_ids, plus representative and
                                      #   event lines (turn_id None) since the oldest kept turn
    window_line_chars: int = 600      # [A] each ChatLine cut to 600 chars with "…"
    window_total_chars: int = 8_000   # [A] oldest lines dropped first until the window fits
    planner_lines: int = 6            # [A, SP-1] DO-4 §3: the planner's recent_chat, taken from the same window
    planner_line_chars: int = 400     # [A, SP-1]
# Limits (GraphDeps.limits) gains `context: ContextLimits`, beside `spend: SpendLimits` (models.md §6) and
#   `web: WebLimits` (web.md §5)
#   (merge-clashes MC-22: AEA-01 owns the one frozen `Limits`; no module-level constants).
```

`load_context` (AEA-34) applies the three window limits when it builds `chat_window` from `messages`; the responder
(AEA-38) and the planner (AEA-37) render from that window and never re-read `messages`. The newest customer message is
sent separately and is already capped at 2,000 characters by the OpenAPI `TextPayload`. **Replaced by:** the first full
eval run (E-1, E-2) measuring the p95 length of stored assistant replies (the line cap must be at or above it) and the
responder's p95 input tokens at turn 10+ against the turn-2 baseline (rule `context-management-multi-turn` 4).

---

## 8. FailureCounters: what increments each field (GRC-13)

```python
# Writer: the facts node (AEA-38), once per turn, from this turn's results; except `timeouts`.
# Counters are per conversation and never reset.                 [Decided §7, engineering; basis consolidated §3 C1, OD-6]
failed_answers    += 1  if any KnowledgeResult this turn has status "no_current_source" or "failed"
tool_failures     += 1  if any SpecialistResult this turn is "failed" or any ToolCallRecord ended in a ToolErrorCode
identity_failures += 1  if identity_step this turn is NotVerified or CodeWrong (graph-tools types)
corrections       += 1  if gate.rules.correction (NEW RuleMatches field, below)
bookings          += 1  per BOOKED CompletedAction this turn (R-41 cap)
timeouts          =    core.turns.timeouts_for(thread_id)    # copied by load_context (AEA-34) at turn start,
                                                             #   because a timed-out turn never reaches facts
# domain/turn.py (AEA-02), RuleMatches gains:
    correction: bool                                  # "that's not what I asked", "that's wrong", "no, I said …";
                                                      #   AEA-05's typo-tolerant phrase list (OD-6 signal)
```

**Where `SafetyKind` and `RuleMatches` live** [Decided §7, engineering, R-G-1]: both in `domain/turn.py` (AEA-02),
with DO-4 §3's fields plus `correction`, and `policy_trigger: HandoffReason | None` typed as DO-4 §3 has it (an
import inside `domain/`). `GateDecision.rules: RuleMatches` and `HandoffRequest.safety_kind: SafetyKind` are domain types
that `ConversationState` checkpoints, and `domain/` may not import `gates/` (DO-3 §2.1, §4.1). `gates/rules.py` (AEA-05)
imports them from `meridian.domain` and owns `match_rules` only: pure core importing pure core, no I/O. DO-4 §3's
`# gates/rules.py` comment on `RuleMatches` is superseded. Wave 0 merge order: AEA-02 before AEA-05 (see §12 for the
whole order).

`load_context` and `facts` both return `counters`, in sequence (never in one superstep), so no reducer is needed;
`load_context` changes only `timeouts`. Thresholds stay in `decide_escalation` rule 7 (cases.md §3.4: `≥ 2` [A, OD-6]).

---

## 9. The planner state key (GRC-11)

```python
# domain/state.py (AEA-02), DO-3 §5.2 CHANGED                                   [Decided §7, engineering]
    planner: PlannerOutcome | None                    # RENAMED from planner_choices: PlannerChoices | None.
                                                      #   Writer: planner node (AEA-37). Readers: plan_join, facts, and
                                                      #   compose's turn_trace() (TurnTrace.planner: model,
                                                      #   fallback_used, failure; §2, GRC-21).
```

---

## 10. Promise text check (GRC-2)

`domain.Promise` carries fields only (no validator). `policy/handoff.py` (AEA-14) is its only constructor and proves
every text: a test asserts each `promise_for` result's `text` is a `PROMISE_TABLE` value, and a grep test fails if
`Promise(` appears outside `policy/handoff.py` and `tests/`. [Decided §7, engineering; matches cases.md A-1]

---

## 11. The check-event key and two router edges (merge additions, GRC-16, GRC-18)

Requested by `stage7/graph-nodes.md` cross-topic 1–2; added at merge (2026-10-21).

```python
# domain/state.py (AEA-02): ConversationState gains ONE turn-scoped key            [Decided §7, engineering] GRC-16
    check_events: Annotated[tuple[CheckEvent, ...], add_turn_events] = ()
        # CheckEvent and its builders: stage7/graph-nodes.md §1 (domain/turn.py). Writers: gates (from_gate), plan
        #   (from_danger), and the node that writes a BRAKE_* halt (from_halt); R-46 events stay in checked.events.
        # Codes only, never text or values, so it is safe in the checkpoint.

def add_turn_events(left: tuple[CheckEvent, ...], right: tuple[CheckEvent, ...]) -> tuple[CheckEvent, ...]: ...
    # domain/state.py, pure. right empty → left. Otherwise keep only the left events whose turn_id == right[0].turn_id,
    # then append right. So the first event of a new turn drops the previous turn's events, and parallel writers in
    # one turn append. load_context writes nothing to this key (an append reducer cannot be "reset" by an update).

# run_graph (AEA-21) builds GraphOutcome.check_events (§2, GRC-20) from the final state:
#   tuple(e for e in state.check_events if e.turn_id == ctx.ids.turn_id) + tuple(state.checked.events if state.checked else ())
#   (the filter covers a turn that halted before its gates node ran). On GraphRecursionError there is no final state:
#   it reads the last checkpoint (graph.get_state), filters the same way, and appends
#   CheckEvent.from_halt(turn_id, <the RECURSION_LIMIT halt>) (graph-nodes §1); GraphOutcome.halt is that halt.
#   GraphOutcome.turn_trace = turn_trace(<final state, or the last checkpoint's>, reply) (§2, GRC-21).
# TurnService (AEA-40) persists GraphOutcome.check_events as given (§2); it never reads ConversationState.
```

```python
# agent/routers.py (AEA-21): two edges added to DO-3 §5.4. halt_route (§5) still runs first in both routers.
#                                                                               [Decided §7, engineering] GRC-18
# 1. after plan_join: state.plan.planner_failed and not state.plan.tasks → "escalation"
#      (graph-nodes §5, GRN-7; escalation rule 6 makes it ai_failure P3, degraded, rule id AI.planner_failed).
#      Order in the plan_join router: halt_route → danger raised → this edge → the DO-3 §5.4 edges.
# 2. after gates: gate.kind == BURNING_ANSWER and gate.burning_answer == "no" → route_act_plan(state)
#      (graph-nodes §6, GRN-6). The gates node writes the code-built `plan` on this path only, so `plan` has two
#      writers on exclusive branches (plan_join; gates when the answer is "no"). route_act_plan is the SAME function
#      the plan_join router uses for an `act` plan: identity needed and missing → "identity", else → the
#      specialists fan-out (Send per task). "yes" and "unsure" still route to safety.
def route_act_plan(state: ConversationState) -> Literal["identity"] | list[Send]: ...
    # Pure. The fan-out is [Send("run_specialist", SpecialistSend(planned=t, state=state)) for t in state.plan.tasks]
    #   (graph-nodes §9.1). The router builds NO SpecialistTask: masking the text, the slice and the appointment read
    #   are the act node's (graph-nodes §9.5 build_specialist_task, R-G-12), because a router does no I/O and
    #   agent/routers.py (AEA-21, wave 1) may not import agent/nodes/act.py (AEA-39, wave 2).
```

Consumers: AEA-02 (key, reducer), AEA-21 (routers), AEA-36 (gates writes `plan` on the "no" path and the `gate`
event), AEA-37 (`classifier` event; `planner_failed`), AEA-38/39 (`brake` events), AEA-21 (`run_graph` builds
`GraphOutcome.check_events`), AEA-40 (persists them).

---

## 12. AEA-02's `Settings`: the one field list (final cross-reference pass, GRC-22)

The fields below were each accepted in a different place (the closing table's *models 3, data 1* and *web settings*
rows; data.md §9 item 1; web.md cross-topic GRA row; models.md §4, §7). No single list existed, so AEA-02 had to
assemble it from five files. This is that list; the rows it consolidates now point here. **Owner: AEA-02 `config.py`**
(slice plan row AEA-02 and §3 "Settings moved into 02 (it needs `Role`)"; Q-2; MC-21). AEA-01's ticket text still names
`config.py` as its own; the slice plan wins, and AEA-01 owns `policy/limits.py` only (MC-22).

```python
# config.py (AEA-02). One typed Settings, built once by the container from the environment; never a module-level
#   singleton, never touches the database (DO-3 §2.1, §2.4). Every secret is a SecretStr (slice plan row AEA-02).
#   AEA-09 (Railway) and AEA-54 (deployment guide) copy the env names from here (data.md §9 item 1, Q-2).
class Settings(MeridianModel):                        # [Decided §7, engineering] unless a field says otherwise
    # --- model providers (R-40) ---
    anthropic_api_key: SecretStr                      # ANTHROPIC_API_KEY
    openrouter_api_key: SecretStr                     # OPENROUTER_API_KEY (Jev)
    models: ModelSettings                             # DO-4 §12: the three typed role maps keyed by Role; a role in the
                                                      #   wrong map or Jev in a structured/tool role fails validation
                                                      #   (DO-3 S-2). Defaults in code (DO-1 §8.1); no env name.
    def role_model_map(self) -> Mapping[str, Any]: ...     # the role → model map as a plain mapping for
                                                      #   compute_agent_version (data.md §7, §9 item 1c)

    # --- this app's own Langfuse project (models.md §4 MOD-6; MC-21). All four optional ---
    langfuse_public_key: SecretStr | None = None      # LANGFUSE_PUBLIC_KEY
    langfuse_secret_key: SecretStr | None = None      # LANGFUSE_SECRET_KEY
    langfuse_base_url: str | None = None              # LANGFUSE_BASE_URL
    langfuse_project_id: str | None = None            # LANGFUSE_PROJECT_ID
    def langfuse_complete(self) -> bool: ...          # all four set → LangfuseTraceSink, else NullTraceSink (models.md §7)
    # No langfuse_export() (R-G-6): LangfuseExportSettings is AEA-19's (adapters/tracing_langfuse.py) and config.py may
    #   not import an adapter (DO-3 §2.1). The container builds it from the four fields above (models.md §4, §7).

    # --- demo login and request tagging (web.md §2, §4) ---
    demo_username: SecretStr                          # MERIDIAN_DEMO_USERNAME (R-48)
    demo_password: SecretStr                          # MERIDIAN_DEMO_PASSWORD (R-48)
    session_secret: SecretStr                         # MERIDIAN_SESSION_SECRET: HMAC key for login tokens (staff.md
                                                      #   §2, STF-5) and code hashing (DO-3 §2.4)
    eval_key: SecretStr | None = None                 # MERIDIAN_EVAL_KEY (DO-6 Correlation). None → no request is ever
                                                      #   tagged eval/load (web.md §4 RequestContext.run_tag)

    # --- web shell (web.md §2, §4, §12; WEB-9, WEB-30, WEB-32) ---
    cookie_secure: bool = False                       # MERIDIAN_COOKIE_SECURE; true on Railway (data.md §7)
    trust_proxy_headers: bool = False                 # MERIDIAN_TRUST_PROXY_HEADERS; true on Railway
    web_dist_dir: Path = Path("apps/web/dist")        # MERIDIAN_WEB_DIST_DIR; /app/apps/web/dist on Railway
    require_frontend: bool = False                    # MERIDIAN_REQUIRE_FRONTEND; true on Railway

    # --- storage and index (data.md §3, §4, §7) ---
    data_dir: Path = Path("var")                      # MERIDIAN_DATA_DIR; /data (the volume) on Railway. Holds
                                                      #   meridian.sqlite (working copy + app tables) and
                                                      #   checkpoints.sqlite (DO-1 §9, "What is on the volume")
    index_dir: Path = Path("var/index")               # MERIDIAN_INDEX_DIR; /app/index in the image.
                                                      #   FastembedIndex(index_dir) (data.md §4; closing table data 6)
    issued_db_path: Path                              # the issued scheduling DB, read-only (first boot and reset
                                                      #   copy from it; cases.md §1.3–§1.4); a code default under the
                                                      #   image's issued dataset, no env name

    # --- version stamp (data.md §7, §9 item 1b; DAT-22) ---
    agent_version: str = "dev"                        # MERIDIAN_AGENT_VERSION, set by the start command from
                                                      #   scripts/agent_version.py; every turn, conversation, deploy_record
                                                      #   and CON-20 current_agent_version stamp reads it
```

**Not in `Settings`:** every numeric limit (the $30 daily cap, rate limits, brakes, window sizes) is in AEA-01's one
frozen `Limits` (`policy/limits.py`, MC-22; §7 here, web.md §5, models.md §6). The parked `.env.example`'s
`MERIDIAN_DAILY_SPEND_CAP_USD`, `MERIDIAN_LLM_MODEL`, `MERIDIAN_FAST_MODEL` and `MERIDIAN_TODAY` are not carried over:
the cap is `limits.spend.daily_cap_usd`, the models are `ModelSettings`' code defaults, and the demo clock lives in the
database (`demo_state.demo_now`, cases.md §1.1). `.env.example` lists the names above (AEA-02, beside `config.py`).

**`RoleSpec.redaction` and the wave-0 merge order** [Decided §7, engineering, R-G-18]. `config.py`'s `RoleSpec.redaction`
is typed `RedactionProfile`, which stays in `privacy/redact.py` (AEA-04, data.md §1; standard library only).
`config.py → privacy` is a legal pure-core import (code-design A0 held both files), so no type moves; the edge the slice
plan's §2 audit missed is recorded as a merge order inside wave 0: **AEA-04 → AEA-02 → AEA-05**, with AEA-01 and
AEA-03 in parallel (AEA-05 waits on AEA-02 for `RuleMatches`, §8). A planner whose dependency is not on `main` records
`blocked-on AEA-0N` for the importing file only and builds the rest.

Consumers: AEA-02 (writes), AEA-09 and AEA-54 (env names), AEA-19 (the four `langfuse_*` fields, through the container), AEA-20 (`models`), AEA-23
(`demo_*`, `session_secret`, `eval_key`, `cookie_secure`, `trust_proxy_headers`), AEA-44 (`session_secret`), AEA-49
(`web_dist_dir`, `require_frontend`), AEA-50 (`agent_version`, `role_model_map`), AEA-51 (container: all of it).

---

## 13. `ReplyComposer`: the one builder of reply blocks (signature-check pass, GRC-24)

**In practice.** WP-4's move turn ends with `facts` and `checks` done. The compose node calls
`composer.compose(state, ctx)`: it turns `checked.text` into a text block, `facts` into a confirmation card, and
`settled` into the `settled` panel, and returns the `ComposedReply` `TurnService` sends. CON-4 (no graph) asks the same
object for just the handoff card: `composer.handoff_block(result)`. One class, so the card a customer sees after "talk
to a person" is byte-for-byte the card a graph handoff produces.

```python
# agent/nodes/compose.py (AEA-21). DO-3 :255 names the class; web.md §4 get_reply_composer() provides it (WEB-20).
#   Pure: no I/O, no model, no clock read (every time comes from ctx.now or a stored row). Texts from policy/texts.py.
class ReplyComposer:                                  # one concrete class, no Protocol, stateless
    def __init__(self) -> None: ...                   # a class (not free functions) so web/deps.py hands out one
                                                      #   instance and tests override it with a recording double
    def compose(self, state: ConversationState, ctx: TurnContext) -> ComposedReply: ...
        # every path, incl. a halted state (it then delegates to halt_reply with state.settled). Blocks in DO-4 §9 order;
        # the handoff card from state.handoff via handoff_block, after the checks (R-26); quick checks per graph-nodes §8.
    def halt_reply(self, halt: Halt, settled: Settled, ctx: TurnContext) -> ComposedReply: ...
        # DO-4 §11's halt rows (graph-core §5 table). run_graph calls it on GraphRecursionError with
        #   core.settled_for(thread_id, ctx.now), since no final state exists.
    def handoff_block(self, result: HandoffResult) -> HandoffBlock | LiveQueuedBlock: ...
        # pure, usable outside a graph turn (X-9, WEB-20). live_queued promise → LiveQueuedBlock, else HandoffBlock.
    def settled_view(self, settled: Settled, identity: IdentityState, controller: Controller) -> SettledView: ...
        # SettledView = the OpenAPI `Settled` schema. visit = settled.current_visit() mapped field for field (§14) plus
        # window_label formatted from `window`; identity "located" is shown as "not_checked" (api-con-mapping §0);
        # replying = controller.kind and representative_name. PersonRequestService (web.md §8) calls it too.
```

`SettledView` = the OpenAPI `Settled` schema: `ComposedReply.settled_view` and `PersonRequestOutcome.settled` carry it
as the wire shape, so it has no second field list here. [Decided §7, engineering]

Consumers: AEA-21 (writes it; the compose node and `run_graph` call it), AEA-42 (`handoff_block`, `settled_view`),
AEA-40 (receives `ComposedReply`), AEA-51 (container provides one instance).

---

## 14. Types other topics named for AEA-02: `Zone`, `FeeNote`, `VisitView` (signature-check pass, GRC-25)

`Settled.current_visit` (DO-4 §1) returns a `VisitView` DO-4 never defines; its fields are below. **`Zone` and `FeeNote`
are not defined here** (residual pass, R-G-2): their one definition is cases.md §2 (CAS-34), the booking policy that
builds them, and AEA-02 transcribes them into `domain/records.py` unchanged. An earlier GRC-25 field set for `FeeNote`
(`schedule_row`, `scheduled_cents`, `charged_cents`, `waived_by_membership`) is withdrawn; `VisitView.fee_line` below
is `FeeNote.line` of cases.md §2.

```python
# domain/actions.py (AEA-02), beside Settled                            [Decided §7, engineering] GRC-25
class VisitChange(MeridianModel):                     # = OpenAPI SettledVisit.change_request
    change: Literal["move", "cancel"]
    wanted_text: str                                  # the customer's words as STORE-redacted at intake
    fee_line: str                                     # "The $49 fee applies under current policy." (policy/texts.py)

class VisitView(MeridianModel):                       # = OpenAPI SettledVisit, minus window_label (display; compose adds it)
    appointment_id: int
    date: date
    window: Window                                    # "HH:MM-HH:MM", as appointment_slots.window
    technician: str
    service_type: ServiceType
    fee_line: str                                     # FeeNote.line, stored on the booking's action row at write time
    status: Literal["booked", "moved", "original_stays"]
    change_request: VisitChange | None
```

**How `Settled.current_visit()` builds it** (pure, from `actions` only; DO-4 §1 "built ONLY from actions + cases"):
the newest `BOOKED` or `MOVED` action whose `records["appointment"]` has no later `CANCELLED` action; `None` if there is
none (a cancelled visit is never "the visit"; it stays in `settled.actions`). Its `after` dict gives `date`, `window`,
`technician`, `service_type`, `fee_line`. A later `CHANGE_REQUEST_SENT` action for the same appointment sets
`status="original_stays"` and `change_request` from that action's `after` (`change`, `wanted_text`, `fee_line`);
otherwise `status` is the action kind. Cross-topic X-10 asks AEA-28 to write those `after` keys.

Consumers: AEA-02 (writes the types; `Zone`, `FeeNote` from cases.md §2), AEA-13 (`zone_for`, `fee_note` return them), AEA-28 (writes the `after` keys),
AEA-34/38 (`settled`), AEA-21 (`settled_view`).

---

## Cross-topic assumptions

| # | Owner | What this file relies on | If it turns out otherwise |
|---|---|---|---|
| X-1 | models (settled, models.md §4) | `SpanHandle`'s fields are models.md's; only its file moves to `domain/turn.py`, re-exported by `ports/runtime.py` | If models keeps it in `ports/`, `TurnContext` moves to `ports/runtime.py` instead (services may import ports) |
| X-2 | cases (AEA-10) | `core.settled_for(thread_id, read_at)` as §6; web.md's shorthand `core.settled_for(thread_id)` passes the demo-clock reading its caller already holds | — (settled at merge: cases.md §1.2 cites §6 here) |
| X-3 | cases (AEA-10) | Two `repos_core` reads added: `core.turns.timeouts_for(thread_id) -> int` (turn rows with degrade reason `timeout`) and `core.messages.recent(thread_id, turns: int) -> tuple[MessageRow, ...]` for the window | — (settled at merge: cases.md §1.2 lists both) |
| X-4 | cases (settled, cases.md §1.2) | `core.reads.identity_state(thread_id) -> IdentityState` is how `load_context` reads identity | — |
| X-5 | cases (cases.md §3.4) | Rule 6 "`halt` set" is reached only by brake halts (§5); deadline and spend halts never reach `decide_escalation` | If CAS wants a case on every timeout, the router changes, and DO-4 §11's *Try again* row conflicts |
| X-6 | web (AEA-40, WEB-14) | `TurnService` builds `TurnInput` and `TurnContext` as §2, with `message_id` from step 4's `core.messages.append` | — |
| X-7 | graph-tools | `Locator`, `NotVerified`, `CodeWrong` types; `SpecialistRunner` (§2 there), now the `GraphDeps.specialists` field (§4 here); `ToolCallScope.message_id` = `TurnInput.message_id` | — |
| X-8 | graph-nodes | `CheckEvent` and its builders (§1 there), carried in the `check_events` key (§11 here); `SignalRecord` and `emit_signal` (§4 there; file `agent/signals.py`, §4 here); `deps.cases` (§4 here); `Plan.planner_failed` (§5 there) | — |
| X-9 | web (AEA-42, WEB-20) | `ReplyComposer.handoff_block(result)` pure, usable outside a graph turn: accepted for AEA-21; class signed in §13 (GRC-24) | — |
| X-10 | cases (AEA-28 scheduling writes) | Each `BOOKED` / `MOVED` action's `after` holds `date`, `window`, `technician`, `service_type`, `fee_line` (= `fee_note(...).line`); each `CHANGE_REQUEST_SENT` action's `after` holds `change`, `wanted_text`, `fee_line` (§14, GRC-25) | `current_visit()` would need a `booking` read, and `Settled` would stop being built from `actions` alone (DO-4 §1) |

### Requests other topics addressed to graph (AEA-02, AEA-21, AEA-51), answered at merge (GRC-19)

Merge 2026-10-21. The graph-tools requests (AEA-22 registry, data cross-topic 5) are answered in graph-tools.md §1.

| From | Request | Answer |
|---|---|---|
| graph-nodes cross-topic 1–2 | `check_events` key; `GraphDeps.cases`; edges `plan_join → escalation`, `gates → fan-out`; `agent/signals.py` | **Accepted:** §11, §4 (GRC-15…GRC-18). The key is reset by its reducer, not by `load_context`; `run_graph` returns `GraphOutcome` (§2, GRC-20) so `TurnService` gets the events and the `RECURSION_LIMIT` event |
| graph-tools C-1 | `GraphDeps.specialists: SpecialistRunner`, no dispatcher field | **Accepted:** §4 (GRC-15) |
| models 1 (MOD-10) | `TurnContext.span: SpanHandle` | **Accepted:** §2 |
| models 2 | AEA-02 transcribes models §1 and §4 types into `ports/models.py`, `ports/runtime.py` | **Accepted**, except `SpanHandle`, which lives in `domain/turn.py` and is re-exported (§1; models §4 agrees) |
| models 3, data 1 (MC-21) | `Settings` (AEA-02 `config.py`) declares `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_PROJECT_ID`, data §9 item 1's env names, `agent_version` (`MERIDIAN_AGENT_VERSION`, default `"dev"`) and the role → model map as a plain mapping | **Accepted** (engineering, AEA-02); the full field list is §12 (GRC-22) |
| models 4 | A gateway `halt` of any reason ends the turn through the halt path; the Sonnet planner fallback is for a `failure` only | **Accepted:** §5 `halt_route` runs first in every router |
| web (WEB-9, settings) | `ApiErrorCode` = the OpenAPI enum; `Settings` adds `cookie_secure`, `trust_proxy_headers`, `web_dist_dir` (default `apps/web/dist`), `require_frontend` (default False) | **Accepted** (engineering, AEA-02); in §12's `Settings` (GRC-22) |
| web (WEB-14, WEB-20) | `TurnInput` / `TurnContext` / intake carrier; pure `handoff_block` | **Accepted:** §2, X-6, X-9 |
| staff (GRA) | staff.md §1 types; `StreamKey` case variant `case:<CaseRef>`; wire `controller.display_name` = `STAFF_PERSONAS[REPRESENTATIVE].name` | **Accepted**, with the types in `domain/staff.py`, not `domain/common.py` (MC-2); `LoginSessionId` also in `domain/staff.py` (staff.md §1; final cross-reference pass, superseding MC-3's `domain/common.py`) |
| cases A-1 | `Zone`, `Window`, `ServiceType`, `FeeNote`, `ShownSlot`, `Presence`, `CaseState`, `Promise` (fields only), `MembershipView.renewal_date`, `HandoffReason` as DO-4 sketches them | **Accepted** (`Promise`: GRC-2) |
| cases A-2 | Case and demo view types in `domain/`, fields from the named OpenAPI schemas | **Accepted** (AEA-02 follow-up). The metrics reads are `Mapping[str, object]` through web.md §4 `MetricsReads`, not `JsonObject` (MC-6) |
| cases A-3 | `HandoffReason` gains the R-7 "both ruled out" value | **Accepted once Innocent answers CAS-16**; until then no value is added |
| cases A-4 | `CaseSummary.due_at: datetime \| None` | **Accepted** (AEA-02) |
| cases A-5 | `FailureCounters.timeouts` = the thread's `TURN_TIMEOUT` turns; `models_disabled` from the ledger | **Accepted:** §8; the ledger reaches the escalation node as `GraphDeps.ledger: ModelsStatus` (§4, residual R-G-13) |
| cases A-6 | Late technicians reach `Plan.handoff_request = late_technician` | **Accepted** (engineering): the planner's `handoff` literal (DO-4 §4) gains `"late_technician"` and `join_plan` maps it to `HandoffReason.LATE_TECHNICIAN`. [A]: SP-1 never measured this value; AEA-37's planner cases include one late-technician transcript |
| cases A-13 | On the P1 unstaffed path, compose (AEA-21) puts `OD4.danger_review` in `EmergencyLineBlock.separate_line` and shows no second `R26.unstaffed` promise | **Accepted** (AEA-21 compose) |
| data 6 | AEA-51 wires `FastembedIndex(Settings.index_dir)` as `GraphDeps.retrieval` and calls `readiness()` at start-up | **Accepted** |
