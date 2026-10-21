# Internal component contracts (DO-4, part 1)

**Date:** 2026-10-21. **Status:** DRAFT **revision 3**: reconciled with the UX-3 contracts
(`docs/ux/03-structure/UI_CONTRACTS.md` and `ui-contracts.openapi.yaml`, proposals awaiting Innocent). Names that cross
the API boundary (error codes, brief fields, block and event names) now use the UX-3 names. Revision 2 (after the metz review; changes listed in
[code-design.md](../code-design.md) §11), planned, nothing built. **Owner of:** the typed hand-offs between the
components of DO-2 §A.1 and §A.4. **Module homes** are in [code-design.md](../code-design.md) §3; this file gives the
shapes only. **Labels:** [A] assumption · **proposal** a choice no requirement settles, awaiting Innocent · [Decided X]. SDQ-1…SDQ-10
were decided by Innocent on 2026-10-21 (SDQ-1: a **60 s** deadline; SDQ-2…SDQ-10 as recommended).

These are **sketches**: field names, types and validators are the agreement; method bodies are not. A builder may add a
private helper, never a field another component reads, without changing this file first.

---

## 0. Conventions every model follows

> Superseded at Stage 7: `domain/base.py` and `domain/ids.py` below are one file, `domain/common.py` (AEA-02; [code-design.md](../code-design.md) §3 and §4.1); the shapes are unchanged.

> Superseded at Stage 7: `retrieval/build_index.py` was merged into `retrieval/ingest.py` (code-design §11, S-1), which mints `PassageId`; see [stage7/data.md](stage7/data.md) §3 (AEA-16).

```python
class MeridianModel(BaseModel):
    """Base for every typed hand-off (domain/base.py)."""
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)

class LLMFacing(MeridianModel):
    """Schemas a model fills. extra='forbid' makes an invented field a loud validation failure
    (pydantic-data-modeling §2). Pipeline-assigned fields (ids, times, turn_id) never appear here; code stamps them
    on the wrapping model afterwards (§5)."""
```

- **Errors never carry values.** A failed validation reports field, stable code and constraint only
  (`safe-validation-errors.md`). `ValidationError.errors()` is never serialised without stripping `input`.
- **Interpreted values carry provenance.** A model-derived value says where it came from and, when the provider
  reports one, a confidence. Jev returns calibrated probabilities; Sonnet does not, so its `confidence` is `None`,
  never invented (`pydantic-data-modeling.md` §1).
- **Validated ID types** (`domain/ids.py`), each a `str` subclass with a core-schema validator:

| Type | Shape | Minted by |
|---|---|---|
| `ThreadId` | UUID4 | `SessionService.open` (CON-1) |
| `TurnId` | UUID4 | the browser, per CON-2 send (reused on "Try again") |
| `RequestId` | UUID4 | middleware, per HTTP request |
| `CustomerId` | `MHC-\d{5}` | issued data |
| `InvoiceId` | `INV-\d{6}` | issued data |
| `CaseRef` | `MHC-C-\d{4}` | `CaseService.open_case` (shown to the customer as the reference) |
| `PassageId` | `<file path>#<chunk n>` | `retrieval/build_index.py` |
| `EventId` | monotonically increasing integer per stream | `events` table |

---

## 1. Conversation state parts (R-45)

The state schema and who writes each key are in [code-design.md](../code-design.md) §5. Its parts:

```python
class ActionKind(StrEnum):
    BOOKED = "booked"; MOVED = "moved"; CANCELLED = "cancelled"
    CHANGE_REQUEST_SENT = "change_request_sent"; CASE_OPENED = "case_opened"
    FOLLOWUP_SAVED = "followup_saved"; VERIFIED = "verified"

class ActionKey(MeridianModel):
    """Idempotency key, UNIQUE in `actions`. A repeated turn (same turn_id) finds the row and does not write again."""
    thread_id: ThreadId
    turn_id: TurnId
    kind: ActionKind
    record_id: str                                  # appointment id, case ref, customer id …

class CompletedAction(MeridianModel):
    key: ActionKey
    kind: ActionKind
    records: dict[Literal["appointment", "slot", "old_slot", "case", "customer", "promise"], str]
    before: dict[str, str] | None = None             # e.g. {"date": "2026-10-16", "window": "12:00-16:00"}
    after: dict[str, str] | None = None              # e.g. {"date": "2026-10-19", "window": "08:00-12:00", "technician": "Marta"}
    at: datetime                                     # demo clock, tz-aware
    source: Literal["actions_table"] = "actions_table"   # provenance: never built from model text

class OpenCase(MeridianModel):
    case_ref: CaseRef
    reason: HandoffReason
    priority: Priority
    state: CaseState
    promise: Promise                                 # §7; from the policy table
    followup: FollowUp | None
    live_queued: bool

class Settled(MeridianModel):
    """Everything the conversation has done. Built ONLY from `actions` + `cases`/`promises` rows (DO-2 §A.3)."""
    actions: tuple[CompletedAction, ...]
    open_case: OpenCase | None
    read_at: datetime
    def has(self, kind: ActionKind, record_id: str | None = None) -> bool: ...
    def current_visit(self) -> VisitView | None: ...          # latest booked/moved, minus cancelled; with change request
    def only_turn(self, turn_id: TurnId) -> "Settled": ...    # eval only: R-46's literal "this turn" reading (review C-1)

class Controller(MeridianModel):
    kind: Literal["ai", "human"]
    representative_name: str | None = None            # "Riley (demo representative)"
    case_ref: CaseRef | None = None                   # authority: conversations.controller (code-design C-7)

class IdentityState(MeridianModel):
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None                    # set at "located"; never shown to any model before "verified"
    masked_hint: str | None                           # "the phone ending in 02"
    code_expires_at: datetime | None
    tries_left: int = Field(ge=0, le=3)               # IdentityLimits (proposal)
    codes_sent: int = Field(ge=0, le=3)               # cap 3 per conversation [A] (DO-1 §10)
    verified_at: datetime | None

class OpenTask(MeridianModel):
    task_id: str
    specialist: Literal["knowledge", "account", "scheduling"]
    intent: TaskIntent                                # §4
    opened_turn: TurnId
    details: TaskDetails                              # zip, city, service_type, wanted_text, appointment_id (all optional)
    missing: tuple[MissingInfo, ...]                  # locate_needed, zip_needed, slot_pick_needed, code_needed …
    status: Literal["open", "waiting_identity", "done"]

class ShownSlot(MeridianModel):                       # "shown, not held"; re-read inside the booking transaction
    slot_id: int; date: date; window: Window; technician: str; service_type: ServiceType
    zone: Zone; member_reserved: bool; shown_turn: TurnId

class FailureCounters(MeridianModel):
    failed_answers: int = 0; tool_failures: int = 0; identity_failures: int = 0
    corrections: int = 0; timeouts: int = 0; bookings: int = 0      # OD-6, R-41

class TurnInput(MeridianModel):
    turn_id: TurnId
    kind: Literal["text", "choice", "code"]
    text_store: str                                   # STORE-redacted; "[code entered]" for a code turn
    choice: CardChoice | None = None
    received_at: datetime                             # demo clock

class ChatLine(MeridianModel):
    speaker: Literal["customer", "assistant", "representative", "event"]
    text: str                                         # never tool output (R-45)
    turn_id: TurnId | None
    at: datetime
```

---

## 2. Per-turn context and budget

> Superseded at Stage 7: `TurnIds`, `TurnBudget` and `TurnContext` live in `domain/turn.py` (AEA-02; [slice plan](../../plans/slice-plan.md) row AEA-02), not `agent/context.py`, which keeps `GraphDeps` only; `TurnContext` gains `span: SpanHandle` (models MOD-10, merge-clashes MC-17) and `intake`: [stage7/graph-core.md](stage7/graph-core.md) §1, §2, §4.

```python
@dataclass(frozen=True)
class TurnBudget:
    started: float                                    # time.monotonic()
    deadline: float                                   # started + TurnLimits.deadline_s = 60 s [Decided SDQ-1]
    def remaining(self) -> float: ...
    def timeout_for(self, cap_s: float, min_call_s: float = 1.0) -> float | None:
        """min(cap_s, remaining()); None when less than min_call_s is left (the caller halts with DEADLINE)."""

class TurnIds(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId
    run_tag: Literal["live", "eval", "load"]          # "eval"/"load" only with the eval key (DO-6)
    run_id: str | None; agent_version: str

@dataclass(frozen=True)
class TurnContext:                                    # LangGraph runtime context [A: `context_schema` on langgraph 1.2.16;
    ids: TurnIds                                      #  fallback config["configurable"]["turn"]]
    budget: TurnBudget
    now: datetime                                     # ONE clock reading per turn
    demo_session: str

@dataclass(frozen=True)
class GraphDeps:                                      # constructor injection into build_graph(); nine fields (review C-4)
    gateway: ModelGateway; retrieval: RetrievalIndex; uow: UnitOfWorkFactory
    identity: IdentityService; scheduling: SchedulingService; handoff: HandoffService
    brief: BriefAssembler; demo: DemoService; limits: Limits
```

---

## 3. Code gates → planner

```python
class SafetyKind(StrEnum): GAS = "gas"; CO = "co"; SPARKS_SMOKE_FLAMES = "sparks_smoke_flames"; BURNING_WITH_BREAKER = "burning_with_breaker"

class RuleMatches(MeridianModel):                     # gates/rules.py; typo-tolerant (R-5, R-47)
    safety: SafetyKind | None
    burning_unclear: bool                             # burning words, breaker state not stated (R-7)
    danger_words: bool                                # narrow explicit danger only (R-8 rule half)
    person: bool                                      # R-2
    policy_trigger: HandoffReason | None              # refund, billing_dispute, complaint_or_manager, legal_or_chargeback, commercial
    rule_ids: tuple[str, ...]                         # which rules fired → check_event

class FormValues(MeridianModel):                      # CON-2 `form` payload (UX-3 adapted UXR-3): locate and where cards
    name: str | None = None; phone: SecretStr | None = None          # D2: to the lookup only, never a prompt, log or trace
    customer_id: CustomerId | None = None; invoice_number: InvoiceId | None = None
    zip_or_city: str | None = None

class Intake(MeridianModel):                          # gates/gate.py parse_intake, before anything stores the text
    kind: Literal["text", "choice", "code", "form"]
    text_store: str                                   # STORE profile: cards → "[card number removed]", codes → "[code entered]",
                                                      #   a locate form → "[details submitted]", a where form → the ZIP or city
    code_digits: SecretStr | None                     # only for kind="code"; never logged, never in state
    form: FormValues | None                           # only for kind="form"; routed by code (LOCATE or CARD_CHOICE), no model
    card_number_seen: bool                            # → reply says cards aren't taken in chat (R-13)
    choice: CardChoice | None

class GateKind(StrEnum):
    AI_PAUSED = "ai_paused"; SAFETY = "safety"; BURNING_ASK = "burning_ask"; BURNING_ANSWER = "burning_answer"
    DANGER_RULE = "danger_rule"; PERSON = "person"; CODE_ENTRY = "code_entry"; LOCATE = "locate"
    CARD_CHOICE = "card_choice"; FREE_TEXT = "free_text"

class GateDecision(MeridianModel):
    kind: GateKind
    rules: RuleMatches
    burning_answer: Literal["yes", "no", "unsure"] | None = None
    resume_task_id: str | None = None                 # CARD_CHOICE / CODE_ENTRY continue an open task (proposal, DO-2 §A.6)
    def gate_result(self) -> Literal["clear", "safety", "burning_unclear", "danger", "person_requested", "ai_paused"]:
        """DO-6 status value. CODE_ENTRY, LOCATE, CARD_CHOICE, FREE_TEXT → "clear" (code-design C-6)."""

def decide_gate(intake: Intake, flags: GateFlags) -> GateDecision: ...   # pure; order: paused → safety → burning → danger words → person → code → card → free text

class StateFlags(MeridianModel):                      # the ONLY state the planner and classifier see: flags, never values
    verified: bool
    open_task: Literal["none", "knowledge", "account", "scheduling"]
    open_task_intent: TaskIntent | None
    slots_shown: int
    has_open_case: bool
    pending_change: bool

class PlannerInput(MeridianModel):                    # built in agent/nodes/plan.py
    latest_message: str                               # JEV profile: names, phones, emails, addresses, customer/invoice IDs,
    recent_chat: tuple[str, ...]                      #   codes, card-like numbers → placeholders (DO-1 §3.2)
    flags: StateFlags                                 # ≤ 6 lines × 400 chars [A, SP-1 build]; R-45's ~10-turn window is the responder's
```

**What crosses this line:** only `PlannerInput`. The planner never sees the customer ID, any record value, any
passage or any tool output. The classifier sees `latest_message` only (SP-1 shape).

---

## 4. Planner and classifier output

```python
class PlannerChoices(LLMFacing):
    """One Jev `choice` question per field (or Sonnet enum JSON in the fallback, Decided SDQ-6).
    SP-1's measured fields, plus two proposals marked †."""
    knowledge: Literal["no", "yes"]
    account: Literal["none", "invoice", "membership", "appointments", "warranty"]       # † warranty (R-17 install date)
    scheduling: Literal["none", "book_new", "reschedule", "cancel", "confirm"]          # † cancel, confirm (R-22, FLOW-6)
    handoff: Literal["none", "refund", "billing_dispute", "membership_cancel", "unsupported_other", "complaint_or_manager"]
    topic: Literal["booking", "membership", "billing", "warranty", "other"]            # † for M-3 (DO-7)

class PlannerOutcome(MeridianModel):
    choices: PlannerChoices | None                    # None → the turn still runs on rules and the open task
    probabilities: dict[str, dict[str, float]] | None # Jev only; provenance of the choice
    model: str
    fallback_used: bool                               # Sonnet planner ran [Decided SDQ-6]
    failure: ProviderFailure | None

class DangerAssessment(MeridianModel):
    label: Literal["normal", "burning_unclear", "danger"]
    raised: bool                                      # True only when label > the rules' verdict; never lowers (R-47)
    confidence: float | None = Field(default=None, ge=0, le=1)
    failure: ProviderFailure | None                   # on failure: label="normal", raised=False → the rules stand

class TaskIntent(StrEnum):                            # the plan in enums; Jev cannot write task text
    ANSWER_QUESTION = "answer_question"
    READ_INVOICE = "read_invoice"; READ_MEMBERSHIP = "read_membership"; READ_APPOINTMENTS = "read_appointments"
    READ_WARRANTY = "read_warranty"
    BOOK_NEW = "book_new"; RESCHEDULE = "reschedule"; CANCEL = "cancel"; CONFIRM = "confirm"

class PlannedTask(MeridianModel):
    order: int = Field(ge=1, le=3)
    specialist: Literal["knowledge", "account", "scheduling"]
    intent: TaskIntent
    needs_identity: bool
    resumes_task_id: str | None = None

class Plan(MeridianModel):
    mode: Literal["talk", "act"]
    tasks: tuple[PlannedTask, ...] = Field(max_length=3)   # Brakes.tasks_per_turn (proposal)
    handoff_request: HandoffReason | None             # from the planner's `handoff` field or a policy word
    topic: Literal["booking", "membership", "billing", "warranty", "other"]
    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]

def join_plan(planner: PlannerOutcome | None, danger: DangerAssessment | None,
              gate: GateDecision, state: ConversationState) -> Plan: ...
```

`join_plan` is pure and follows SP-1's measured `normalize` steps: a planner failure never blocks the rules; a policy
word overrides the planner's `handoff`; `membership_cancel` adds a membership read and a knowledge task; scheduling
reads appointments itself; a bare "Yes, please." or a slot pick continues the open task. **Order is set by code**
(account, then scheduling, then knowledge) for the reply's reading order; the tasks run in parallel because each is a
read or a single write through the scheduling service (DO-2 §A.1). Danger routing is not in `Plan`: the router reads
`danger.raised` first.

---

## 5. Specialist contracts

> Stage 7: the dispatcher's public API and executor registration (`ToolRegistry`, `ToolDispatcher.schemas` / `dispatch`, `DispatchedCall`, `ToolCallRecord`) are defined in [stage7/graph-tools.md](stage7/graph-tools.md) §1 (GRT-1); built by AEA-22 in `agent/tools/dispatch.py`.

> Superseded at Stage 7: the SONNET profile also masks contact details: emails, street addresses, and phones down to their last two digits (system design §3.2 and §10 *What each vendor sees*; [stage7/data.md](stage7/data.md) §1, DAT-5). The comments on `customer_text`, `task_messages` and `wanted_text` below read that way; no field or type changes.

```python
class SpecialistTask(MeridianModel):
    task: PlannedTask
    customer_text: str                                # SONNET profile: card-like numbers and codes masked, emails, street addresses; phones to their last two digits
    task_messages: tuple[str, ...]                    # the customer's messages for this open task, same profile
    slice: KnowledgeSlice | AccountSlice | SchedulingSlice   # only what the specialist needs (R-45)

class SchedulingSlice(MeridianModel):
    customer_zone: Zone | None
    member: bool
    appointments: tuple[AppointmentView, ...]         # no issue_description (audit D-11)
    shown_slots: tuple[ShownSlot, ...]
    pending_change: bool
    bookings_left: int
    # No customer_id: tools bind the verified customer from state in code; the model can't name another one.

# ── domain/tools.py (A0, wave 0): the executor areas A3, A4, A5 build against these without waiting for A7 (review B-1)
class ToolCallScope(MeridianModel):                   # what code binds; the model never supplies these
    ids: TurnIds
    customer_id: CustomerId | None                    # the VERIFIED customer from state, or None
    shown_slot_ids: frozenset[int]
    now: datetime
    message_id: int                                   # the customer message that led to this call (lookup log)

class LookupEntry(MeridianModel):                     # one lookup_log row (R-29)
    tool: str; record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]
    result_seen: str                                  # snapshot shown to the model, ids and values, no free text > 80 chars
    message_id: int; turn_id: TurnId

class ToolError(MeridianModel):                       # returned to the model, never raised into it (rule 5)
    code: ToolErrorCode                               # not_allowed, bad_arguments, unknown_tool, not_verified, not_shown,
    message: str                                      #   fee_bearing, outside_service_area, slot_taken, booking_cap,
    retryable: bool                                   #   identical_call, tool_failed

class ToolResult(MeridianModel):
    ok: bool
    for_model: JsonValue | ToolError                  # what the model sees (≤ 4,000 chars rendered)
    captured: KnowledgeCapture | AccountCapture | SchedulingCapture | None
        # per-tool record shapes (passages; invoice/membership/warranty views; shown slots, WriteResult,
        # ChangeRequestDraft) defined in domain/specialists.py (A0); the runner folds them into the results below
    lookup: LookupEntry
    lookup_written: bool                              # True when a write service already wrote it in its own transaction

class ToolDef(MeridianModel):
    name: str
    description: str                                  # what it returns, when to use, when NOT (sibling named) (agent-tools rule 2)
    args_model: type[LLMFacing]                       # JSON schema generated from it (rule 3)
    kind: ToolKind                                    # kb_search, account_read, slot_search, book, move, cancel, change_request
    effect: Literal["read", "write"]
    requires_verified: bool                           # False only for kb_search and the zone-only window search (R-14)
    executor: Callable[[LLMFacing, ToolCallScope], ToolResult] = Field(exclude=True)   # set by the owning area's module
```

**Lookup-log rule.** For a **read** tool, `agent/tools/dispatch.py` writes `ToolResult.lookup` in a short transaction of
its own. For a **write** tool, the executor passes the `LookupEntry` into the scheduling service, which writes it in the
same transaction as the booking and its `actions` row (DO-1 §9) and returns `lookup_written=True`; dispatch then skips it.

**Results are captured by code from tool results, not from the model's account of them** (SP-1 shape). The model's
`report_facts` adds only the fields named in its report model.

```python
class Passage(MeridianModel):
    passage_id: PassageId; file: str; section: str
    version_label: str                                # as the file states it: "Effective 2026-01-01", "Rev 2026-01", "undated"
    version_date: date | None                         # parsed when the label holds a full date; else None (UXR-24)
    text: str; score: float

class KnowledgePoint(MeridianModel):
    text: str = Field(max_length=500)
    passage_id: PassageId                             # validator: must be a passage returned in this run

class KnowledgeResult(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"
    status: Literal["answered", "no_current_source", "failed"]
    passages: tuple[Passage, ...]; points: tuple[KnowledgePoint, ...]
    quick_checks: tuple[PassageId, ...] = ()          # R-44, offered never required
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None

class AccountResult(MeridianModel):
    kind: Literal["account"] = "account"
    status: Literal["read", "not_verified", "failed"]
    invoices: tuple[InvoiceView, ...] = ()            # lines as billed; INV-204411 $144 stays as billed (R-17)
    membership: MembershipView | None = None
    warranty: WarrantyView | None = None              # install date + the term sentence (K-9)
    staff_notes: tuple[StaffNote, ...] = ()           # staff-only (HP-3): to the brief and case view, NEVER the responder
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None

class WriteResult(MeridianModel):
    action: CompletedAction                           # as committed, from the `actions` row
    confirmation: ConfirmationView                    # date, window, technician, fee_note (R-20)

class ChangeRequestDraft(MeridianModel):              # R-21, R-22: recorded, appointment untouched
    appointment_id: int
    change: Literal["move", "cancel"]
    wanted_text: str                                  # the customer's words (SONNET profile: emails, street addresses; phones to their last two digits)
    windows_shown: tuple[int, ...]                    # shown, not held
    hours_before: float                               # on the demo clock
    window_start: datetime                            # → internal due time (DO-1 §5.2 step 7)

class SchedulingResult(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    status: Literal["windows_shown", "written", "staff_change_request", "slot_taken", "out_of_area",
                    "no_fit", "not_verified", "booking_cap", "failed"]
    windows: tuple[ShownSlot, ...] = ()
    write: WriteResult | None = None
    change_request: ChangeRequestDraft | None = None
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None

SpecialistResult = Annotated[KnowledgeResult | AccountResult | SchedulingResult, Field(discriminator="kind")]

# What the model may report (the `report_facts` tool), per kind:
class KnowledgeReport(LLMFacing):
    points: list[ReportedPoint] = Field(max_length=5)     # {text ≤ 500, passage_id}
    answered: bool
class AccountReport(LLMFacing):
    summary: str = Field(max_length=300)                  # never judges a charge
class SchedulingReport(LLMFacing):
    appointment_id: int                                   # 0 = none
    wanted_time: str                                      # the customer's words, "" = none
    note: str = Field(max_length=200)

def run_specialist(spec: SpecialistSpec, task: SpecialistTask, ctx: TurnContext) -> SpecialistResult: ...
```

**Runner rules** (`agent/specialists/runner.py`): at most 2 tool rounds per specialist (proposal, DO-2 §A.1); the
message list lives for this run only; an identical call (same name + canonical args) stops the loop; no tool call ends
the loop (final-answer branch); every call returns with its `tool_call_id`; never raises. Each tool call writes one
`lookup_log` row through `agent/tools/dispatch.py`.

---

## 6. Escalation decision

```python
class EscalationInputs(MeridianModel):
    gate: GateDecision
    plan: Plan | None
    results: tuple[SpecialistResult, ...]
    counters: FailureCounters
    identity: IdentityState
    halt: Halt | None
    models_disabled: bool                             # our cap or the provider's

class EscalationDecision(MeridianModel):
    outcome: Literal["none", "offer", "escalate"]     # "offer" = ask "would you like a person?" (OD-6; D4 "only if accepted")
    reason: HandoffReason | None
    priority: Priority | None                         # set by policy/handoff.py (A6), never a model
    rule_id: str                                      # e.g. "R21.fee_bearing", "D4.membership_cancel", "OD6.two_misses"
    degraded: bool = False                            # a halt or failure caused it → turn.outcome = degraded_handoff

def decide_escalation(inputs: EscalationInputs) -> EscalationDecision: ...   # pure, policy/escalation.py
```

**Rule order (first match wins; proposal, each rule's source cited):**

| # | When | Outcome | Reason → priority |
|---|---|---|---|
| 1 | Gate `PERSON` (handled before the graph reaches here, listed for completeness) | escalate | `customer_requested_person` → P3 (R-2) |
| 2 | A policy word (refund, dispute, complaint or manager, legal or chargeback, commercial) | escalate | per D4: refund P3, dispute P3, complaint P3, commercial P3 (R-24) |
| 3 | `SchedulingResult.status == "staff_change_request"` | escalate | `fee_bearing_change` → P2, due at window start (R-21, R-22) |
| 4 | Planner `handoff` (`membership_cancel`, `unsupported_other`, …) | escalate or offer per the D4 row | D4 table (`policy/handoff.py`) |
| 5 | Identity `not_verified` or `locked` with a private task open | escalate | `identity_unverified` → P3; reply reveals nothing (R-16) |
| 6 | `halt` set, or a specialist `failed` twice in a row | escalate, `degraded=True` | `ai_failure` → P3 (PRD §5 *Reliability*) |
| 7 | `failed_answers ≥ 2` or `corrections ≥ 2` | offer | — (OD-6 two-attempt rule [A: threshold 2]) |
| 8 | otherwise | none | — |

---

## 7. Handoff: case, promise, brief

```python
class HandoffReason(StrEnum):
    SAFETY = "safety"; DANGER = "danger"; BURNING_UNCLEAR = "burning_unclear"
    CUSTOMER_REQUESTED_PERSON = "customer_requested_person"; REFUND = "refund"; BILLING_DISPUTE = "billing_dispute"
    COMPLAINT_OR_MANAGER = "complaint_or_manager"; LEGAL_OR_CHARGEBACK = "legal_or_chargeback"; COMMERCIAL = "commercial"
    LATE_TECHNICIAN = "late_technician"; FEE_BEARING_CHANGE = "fee_bearing_change"; MEMBERSHIP_CANCEL = "membership_cancel"
    UNSUPPORTED_ACTION = "unsupported_action"; IDENTITY_UNVERIFIED = "identity_unverified"; AI_FAILURE = "ai_failure"

class Priority(StrEnum): P0 = "P0"; P1 = "P1"; P2 = "P2"; P3 = "P3"; P4 = "P4"

class Promise(MeridianModel):
    """Only policy/handoff.py (A6) constructs it. The validator rejects any `text` not in PROMISE_TABLE (R-26)."""
    policy_row: str                                   # "R26.unstaffed", "R26.refund", "R26.staffed", "R26.safety_none"
    text: str                                         # the table string, word for word ("" for safety: no time promised)
    due_at: datetime | None                           # business-day rule on the demo clock; None for safety and live
    due_label: str | None                             # "Monday, October 19, 7:00 pm" (format owned by UX copy)
    extra_lines: tuple[str, ...] = ()                 # R-26 can't-guarantee line; phone-support line while open
    live_queued: bool = False

def promise_for(reason: HandoffReason, presence: Presence, now: datetime,
                window_start: datetime | None = None) -> Promise: ...      # pure

class HandoffRequest(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId
    reason: HandoffReason; priority: Priority; rule_id: str
    trigger: Literal["gate", "escalation", "con4", "safety"]
    identity: IdentityState
    change_request: ChangeRequestDraft | None = None
    safety_kind: SafetyKind | None = None

class CaseSummary(MeridianModel):
    case_ref: CaseRef; reason: HandoffReason; priority: Priority; state: CaseState
    created_at: datetime; promise: Promise; followup: FollowUp | None
    version: int                                      # optimistic concurrency (CON-13 VERSION_CONFLICT)
    seed: bool = False                                # demo seed (R-33)

class HandoffResult(MeridianModel):
    case: CaseSummary
    created: bool                                     # False → this thread already had an open case (idempotent): ONE open
                                                      #   case per thread; a new reason adds a case_event, raises priority to
                                                      #   the higher one, and returns the same reference (CON-4 already_open)
    action: CompletedAction                           # kind=case_opened; same transaction as the case
    alert: Literal["supervisor_now"] | None           # P0, P1, fee-bearing (R-21)

class HandoffService:                                # services/handoff.py (A6), concrete
    def __init__(self, uow: UnitOfWorkFactory, cases: CaseService, demo: DemoService, clock: Clock) -> None: ...
    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ...
    # Opens ONE unit of work and calls cases.open_case(tx, …): cases, case_events, promises, actions(case_opened),
    # events(case_created) commit together. The graph never holds a transaction (review S-6).
    # Safety path: on a failed write, retry once; the instruction is sent either way (DO-1 §8.2).
```

**The brief (R-28): eight fixed headings, always in this order** (consolidated direction §5):

```python
BRIEF_TITLES = ("Why this came to you", "What the customer needs", "What we know for sure",
                "What the customer says (not checked)", "What the AI did", "What we told the customer",
                "What you need to decide", "Who they are and how to reach them")

class SourceRef(MeridianModel):
    kind: Literal["lookup_log", "message", "action", "policy_row", "rule"]
    ref: str                                          # lookup_log id, message id, action key, policy row, rule id

class BriefItem(MeridianModel):                       # field names and kinds = OpenAPI `BriefItem`
    text: str
    kind: Literal["fact", "claim", "ai_action", "told_customer", "decision", "contact"]
                                                      # heading 1's reason → fact; heading 2's quotes → claim (unchecked words)
    sources: tuple[SourceRef, ...]                    # serialised as `source_ids`; every item opens its sources (R-29)
    changed: bool                                     # the source changed since the AI saw it

class BriefHeading(MeridianModel):                    # = OpenAPI `BriefHeading`
    number: int = Field(ge=1, le=8)
    key: Literal["why", "needs", "know", "says", "ai_did", "told", "decide", "who"]
    title: str                                        # == BRIEF_TITLES[number-1]; heading 8 "Who they are and how to reach them"
    origin: Literal["state", "extraction"]            # internal only: 1,3,5,6,8 state; 2,4,7 extraction
    checked: bool                                     # False for heading 4 ("NOT CHECKED")
    items: tuple[BriefItem, ...]                      # empty → the screen shows "Nothing recorded." (UX copy)
    trimmed: bool; trim_note: str | None              # set by the fact check
    not_generated: bool                               # extraction failed: headings 2, 4, 7 only

class Brief(MeridianModel):
    case_ref: CaseRef; thread_id: ThreadId; assembled_at: datetime
    status: Literal["ready", "being_written", "failed"]   # "being_written" until the extraction returns or fails
    headings: tuple[BriefHeading, ...]                # validator: exactly 8, numbers 1..8 in order, origins as above

class Quote(LLMFacing):
    message_id: int                                   # must be a customer message of this thread
    text: str = Field(max_length=300)                 # validator (code): exact substring of that message

class BriefExtraction(LLMFacing):                     # one Sonnet structured call, beside the responder
    needs: list[Quote] = Field(min_length=1, max_length=2)       # heading 2
    claims: list[Quote] = Field(max_length=5)                    # heading 4
    open_decision: str = Field(max_length=200)                   # heading 7; fact-checked like the reply

class BriefAssembler:
    def assemble(self, case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]) -> Brief: ...
    def attach_extraction(self, brief: Brief, extraction: BriefExtraction | None,
                          check: CheckResult | None) -> Brief: ...   # None → headings 2,4,7 "not generated"
```

Staff-only text (`internal/agent_discretion_notes.md`, record-vs-policy mismatches such as INV-204411) enters the brief
as heading 3 or 7 items with `source.kind = "lookup_log"` and is never part of any `ResponderInput` (R-10, HP-3).

---

## 8. Turn facts

```python
class TurnFacts(MeridianModel):
    """What THIS turn did. Reset every turn. Paired with Settled (the whole conversation) in the responder's input."""
    turn_id: TurnId
    gate_kind: GateKind
    plan_mode: Literal["talk", "act"] | None
    points: tuple[KnowledgePoint, ...]                 # answered knowledge, with passages for source chips
    passages: tuple[Passage, ...]
    no_source_tasks: tuple[TaskIntent, ...]            # → "I don't have that information" + person (R-13)
    account: AccountFactsView | None                   # customer-facing fields only; no staff notes
    windows_shown: tuple[ShownSlot, ...]
    writes_this_turn: tuple[CompletedAction, ...]
    change_request: ChangeRequestDraft | None
    handoff: HandoffResult | None
    escalation: EscalationDecision | None
    identity_step: IdentityStep | None                 # code_sent(masked hint) | verified | not_verified | wrong(tries_left) | expired | locked
    missing: tuple[MissingInfo, ...]
    notices: tuple[NoticeCode, ...]                    # card_number_removed, booking_cap, out_of_area …
    quick_checks: tuple[PassageId, ...] = ()
```

---

## 9. Responder: input and output

```python
class ResponderInput(MeridianModel):                  # rendered by agent/prompts/responder.py; SONNET profile applied
    chat_window: tuple[ChatLine, ...]                 # ~10 turns [A], R-45
    this_turn: TurnFacts                              # labelled "WHAT HAPPENED THIS TURN"
    settled: SettledForModel                          # labelled "ALREADY DONE IN THIS CONVERSATION" (R-45 fix)
    identity_status: str                              # status word only
    today_label: str                                  # from the clock
    rules: ResponderRules                             # no promise text, no reference, no "charged", no completion
                                                      #   word unless backed by `settled`; no prices beyond the facts

class ResponderDraft(LLMFacing):
    text: str = Field(min_length=1, max_length=1200)  # words only; every card is composed by code

class CheckedReply(MeridianModel):
    text: str
    removals: tuple[Removal, ...]
    fallback_used: bool                               # all text removed or responder failed → code text from facts
    events: tuple[CheckEvent, ...]

class ComposedReply(MeridianModel):                   # agent/nodes/compose.py → TurnService
    blocks: tuple[ReplyBlock, ...]                    # discriminated union (DO-4 api-con-mapping, CON-2)
    settled_view: SettledView                         # from Settled; identical source to the words (N-27)
    writes: tuple[CompletedAction, ...]               # this turn's writes (N-8)
    notice: Notice | None                             # TURN_TIMEOUT, BUSY, SPEND_CAP_REACHED, RATE_LIMITED, BOOKING_CAP,
                                                      #   AI_PAUSED (delivered_to_representative=True; outcome "to_staff")
    path: TurnPath                                    # safety, burning_questions, burning_unclear, danger, person, talk,
                                                      #   act, handoff, code, paused, degraded
    outcome: Literal["answered", "acted", "safety_reply", "handed_off", "to_staff", "degraded_handoff"]   # DO-6
    degrade_reason: Literal["model_error", "tool_error", "timeout", "brake", "spend_cap", "rate_limit"] | None
```

**The promise and the reference are never in `ResponderDraft`.** `compose` adds the handoff card from `HandoffResult`
(R-26), after the checks.

---

## 10. R-46 checks

```python
class Claim(MeridianModel):
    kind: Literal["completion", "number", "date", "time", "id", "amount"]
    span: tuple[int, int]
    value: str
    action_kind: ActionKind | None = None             # for completion claims, via COMPLETION_WORDS in checks.py

class EvidenceSet(MeridianModel):                     # checks.py
    amounts_cents: frozenset[int]; dates: frozenset[date]; times: frozenset[str]
    ids: frozenset[str]; numbers: frozenset[str]
    sources: dict[str, SourceRef]                     # value → where it came from
def build_evidence(facts: TurnFacts, settled: Settled, lookups: Sequence[LookupRow],
                   chat: Sequence[ChatLine] | None = None) -> EvidenceSet: ...   # chat only for the brief

class Removal(MeridianModel):
    claim: Claim
    reason: Literal["no_completed_action", "not_in_evidence", "quote_not_found"]

class CheckResult(MeridianModel):
    text: str                                         # with failing sentences removed
    removals: tuple[Removal, ...]
    passed: bool                                      # no removals

class CheckEvent(MeridianModel):                      # DO-6 `check_event`
    check: Literal["completion", "fact", "brief_fact", "brief_quote"]
    turn_id: TurnId
    result: Literal["pass", "trimmed", "fallback"]
    removed: int
    claim_kinds: tuple[str, ...]                      # kinds only; never the removed text

COMPLETION_WORDS: dict[ActionKind, tuple[str, ...]]  # inline in checks.py, its only reader (review B-2)

def check_completion(text: str, settled: Settled) -> CheckResult: ...
def check_facts(text: str, evidence: EvidenceSet) -> CheckResult: ...
```

- **[Decided SDQ-8 option A, Innocent 2026-10-21]:** a completion claim passes when `settled` holds an action of the
  matching kind (and record, when the sentence names one). `settled` already includes this turn's writes (re-read by
  the `facts` node). There is no scope flag (review C-1): the eval shows R-46's literal "this turn only" reading by
  passing `settled.only_turn(turn_id)` to the same function.
- A removed sentence leaves the rest; if nothing is left, `CheckedReply.fallback_used` and `compose` builds the reply
  from the facts' fixed fields plus a person offer (DO-1 §8.2 *Responder*).
- The brief runs `check_facts` with the chat included, and every `Quote` must be an exact substring of its message.

---

## 11. Errors, halts and what the customer sees

> Superseded at Stage 7: `STAFF_AUTH_REQUIRED` is gone; the HTTP codes are exactly the OpenAPI `ApiError.error.code` enum, which adds `UNAUTHENTICATED` (401, details.reason none | expired), `LOGIN_FAILED` (401) and `LOGIN_RATE_LIMITED` (429), and a wrong or reset role is 403 `ROLE_NOT_ALLOWED` (details.reason wrong_role | role_reset): [stage7/web.md](stage7/web.md) §1 (WEB-9).

```python
class ProviderFailureKind(StrEnum):
    TIMEOUT = "timeout"; CONNECTION = "connection"
    RATE_LIMITED = "rate_limited"                     # 429 with retry-after
    OVERLOADED = "overloaded"                         # 529
    SERVER = "server"                                 # 5xx, 504, OpenRouter 502/503
    PROVIDER_SPEND_CAP = "provider_spend_cap"         # Anthropic 429 with no retry-after (research §2b); OpenRouter 402
    OUR_SPEND_LIMIT = "our_spend_limit"               # Anthropic 400 "spend limit" we set
    BAD_REQUEST = "bad_request"; AUTH = "auth"; NOT_FOUND = "not_found"
    BODY_ERROR = "body_error"                         # OpenRouter `error` inside an HTTP 200 (readiness SD-6.3)
    REFUSAL = "refusal"; MAX_TOKENS = "max_tokens"    # stop_reason checked before content
    INVALID_OUTPUT = "invalid_output"                 # schema validation failed, or a choice not in its options

class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind
    provider: Literal["anthropic", "openrouter_jev"]
    http_status: int | None
    retry_after_s: float | None
    retryable: bool                                   # TIMEOUT, CONNECTION, RATE_LIMITED, OVERLOADED, SERVER;
                                                      #   BODY_ERROR only when its inner code is one of those
    provider_request_id: str | None                   # for support; never a payload or key

class HaltReason(StrEnum):
    DEADLINE = "deadline"                             # TURN_TIMEOUT at 60 s [Decided SDQ-1]
    BRAKE_TASKS = "brake_tasks"; BRAKE_TOOL_ROUNDS = "brake_tool_rounds"; BRAKE_SONNET_CALLS = "brake_sonnet_calls"
    BRAKE_IDENTICAL_CALL = "brake_identical_call"; RECURSION_LIMIT = "recursion_limit"
    SPEND_CAP = "spend_cap"; PROVIDER_SPEND_CAP = "provider_spend_cap"

class Halt(MeridianModel):
    reason: HaltReason; node: str; elapsed_ms: int

class ApiErrorCode(StrEnum):                          # domain/common.py; names = UX-3 (UI_CONTRACTS "Named errors")
    # composed notices (HTTP 200, NoticeBlock + Notice, `settled` included)
    TURN_TIMEOUT = "TURN_TIMEOUT"                     # 60 s deadline [Decided SDQ-1] (N-26)
    BUSY = "BUSY"                                     # 30 turns in flight [Decided SDQ-9]
    SPEND_CAP_REACHED = "SPEND_CAP_REACHED"; RATE_LIMITED = "RATE_LIMITED"; BOOKING_CAP = "BOOKING_CAP"
    AI_PAUSED = "AI_PAUSED"                           # a representative owns the chat; not a failure
    # composed errors (HTTP 200, ErrorBlock)
    SLOT_TAKEN = "SLOT_TAKEN"; OUT_OF_AREA = "OUT_OF_AREA"; CODE_WRONG = "CODE_WRONG"; CODE_EXPIRED = "CODE_EXPIRED"
    CODE_LOCKED = "CODE_LOCKED"; CODE_CAP_REACHED = "CODE_CAP_REACHED"; NOT_VERIFIED = "NOT_VERIFIED"
    # HTTP errors (ApiError {code, field, constraint, details}, never the value)
    VALIDATION_ERROR = "VALIDATION_ERROR"             # 400 (the one handler rewrites FastAPI's 422)
    REQUEST_RATE_LIMITED = "REQUEST_RATE_LIMITED"     # 429, per-IP limits on reads (R-41); not the chat's RATE_LIMITED
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"; SESSION_ENDED = "SESSION_ENDED"   # 404, 410
    TURN_IN_PROGRESS = "TURN_IN_PROGRESS"             # 409, details.retry_after_ms
    RESET_IN_PROGRESS = "RESET_IN_PROGRESS"; RESET_FAILED = "RESET_FAILED"; HANDOFF_FAILED = "HANDOFF_FAILED"
    STAFF_AUTH_REQUIRED = "STAFF_AUTH_REQUIRED"       # 401, details.reason: none | session_reset | expired
    ROLE_NOT_ALLOWED = "ROLE_NOT_ALLOWED"             # 403, actions only; every role may read a case (owner read-only)
    CASE_NOT_FOUND = "CASE_NOT_FOUND"; FLAG_NOT_FOUND = "FLAG_NOT_FOUND"
    CASE_ALREADY_CLAIMED = "CASE_ALREADY_CLAIMED"; VERSION_CONFLICT = "VERSION_CONFLICT"   # 409, details.changed_by/at
    NOT_ALLOWED_IN_STATE = "NOT_ALLOWED_IN_STATE"
    REASON_REQUIRED = "REASON_REQUIRED"; WAKE_UP_REQUIRED = "WAKE_UP_REQUIRED"; OUTCOME_REQUIRED = "OUTCOME_REQUIRED"   # 422
    NOT_LIVE = "NOT_LIVE"; NOT_CLAIMED_BY_YOU = "NOT_CLAIMED_BY_YOU"
```

**From failure to customer, per kind.** The customer never sees a provider's name, status or message.

| What happened | Turn outcome / degrade reason (DO-6) | What the customer gets | Signal (DO-1 §8.2) |
|---|---|---|---|
| Deadline reached (60 s, Decided SDQ-1) | `degraded_handoff` / `timeout` | The UX copy "This is taking longer than it should." (UX owns customer copy; `policy/texts.py` copies it) + whatever `settled` holds + keys *Try again* (same `turn_id`) and *Talk to a person*; notice `TURN_TIMEOUT` | `turn_timeout` |
| Admission limit (30 in flight, Decided SDQ-9) | `degraded_handoff` / `rate_limit` | Notice `BUSY` with the sentence from the code's message table (`policy/texts.py`; proposed wording in api-con-mapping UXR-26) + person key; no model ran | `turn_rejected_busy` |
| Our $30/day cap reached | `degraded_handoff` / `spend_cap` | Notice `SPEND_CAP_REACHED` ("I can't answer more questions right now. A person can pick this up.") + person key; safety and CON-4 still work | `spend_cap_reached` |
| Provider spend cap (Anthropic 429 without `retry-after`; OpenRouter 402) | `degraded_handoff` / `spend_cap` | As above; `ModelGateway` trips the circuit: no further model calls until reset | `provider_spend_cap` |
| Provider rate limit, retry fits the deadline | — (retried once) | nothing visible | `model_call.retries` |
| Provider rate limit or 5xx/529, retry does not fit | `degraded_handoff` / `model_error` | Specialist: handoff reply with what is settled. Responder: code text from facts + person offer | `specialist_failed`, `responder_fallback` |
| OpenRouter error inside HTTP 200 | `BODY_ERROR`: planner → Sonnet fallback (Decided SDQ-6); classifier → rules stand (R-47) | nothing visible when the fallback works | `planner_fallback`, `classifier_fallback` |
| Per-session or per-IP rate limit (R-41) | `degraded_handoff` / `rate_limit` | Notice `RATE_LIMITED`; field disabled; person key never limited | `rate_limited` |
| A brake fired | `degraded_handoff` / `brake` | Handoff reply with what is settled | `brake_fired` (with the brake named) |
| A representative owns the chat (`controller = human`) | `to_staff` (not a failure) | Notice `AI_PAUSED`, `delivered_to_representative: true`; the message is written to the thread and appears on CON-21 as `customer_message` | — |

---

## 12. Model ports and the gateway

> Superseded at Stage 7: adapters return a `ProviderCall` in `Attempt.record`, and the gateway wraps it as `CallRecord.from_provider(…, role, attempt)` ([stage7/models.md](stage7/models.md) §1, MOD-1; merge-clashes MC-28); `Redactor`, used below, is defined in [stage7/data.md](stage7/data.md) §1 as the type of `redact` (MC-23).

```python
class Role(StrEnum):
    PLANNER = "planner"; CLASSIFIER = "classifier"; PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST = "specialist"; RESPONDER = "responder"; BRIEF = "brief"

class ChoiceField(MeridianModel):
    name: str; instructions: str
    options: dict[str, str]                           # insertion order shown; ≤ 255 (Jev limit)

class ChoiceRequest(MeridianModel):
    system: str; state: dict[str, JsonValue]          # already redacted; flags only
    fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel):
    choices: dict[str, str]                           # validated against each field's options by the adapter
    probabilities: dict[str, dict[str, float]] | None

class StructuredRequest(MeridianModel, Generic[T]):
    system_prefix: str                                # stable, cache-controlled
    system_dynamic: str
    user: str
    output_model: type[T]                             # sent as output_config.format; trimmed schema (pydantic-ai-agents §4)
    max_tokens: int; effort: Literal["low", "medium", "high"] | None

class ToolStepRequest(MeridianModel):
    system_prefix: str; system_dynamic: str
    messages: ProviderMessages                        # opaque, owned by the adapter (keeps thinking blocks intact)
    tools: tuple[ToolSchema, ...]; max_tokens: int; effort: Literal["low", "medium", "high"] | None

class ToolStep(MeridianModel):
    text: str; tool_calls: tuple[ToolCall, ...]       # ToolCall(id, name, args: dict | None) — None = unparseable
    raw: ProviderTurn; stop_reason: str | None

class CallRecord(MeridianModel):                      # one per HTTP attempt → spend_ledger + span
    role: Role; provider: str; model: str; attempt: int
    latency_ms: int; input_tokens: int; output_tokens: int; cache_read_tokens: int; cache_write_tokens: int
    thinking_tokens: int; cost_usd: float; status: Literal["ok", "error"]
    failure: ProviderFailure | None; provider_request_id: str | None; stop_reason: str | None

class Attempt(MeridianModel, Generic[T]):
    value: T | None; record: CallRecord; failure: ProviderFailure | None

class ChoiceModel(Protocol):
    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...

class StructuredModel(Protocol):
    def structured(self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...

class ToolCallingModel(Protocol):
    def start(self, user: str) -> ProviderMessages: ...
    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...   # (tool_call_id, JSON text)
```

**Contract every implementation honours (tested in `tests/contract/test_model_ports_contract.py`):** one HTTP attempt
per call; never raises (failures come back in `Attempt.failure`); the same `ProviderFailureKind` for the same situation
on either provider, **each adapter mapping its own inputs** (SDK exceptions for Anthropic, raw HTTP status and body for
OpenRouter); there is no shared classifier module (review S-2);
`record` always present, including on failure; `stop_reason` checked before content; a forced `tool_choice` is never
sent (it returns 400 on Sonnet 5.5, research §1). `JevAdapter` implements `ChoiceModel` only and sends
`provider.data_collection: "deny"` on every request.

```python
ChoiceRole = Literal[Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK]
StructuredRole = Literal[Role.RESPONDER, Role.BRIEF]
ToolRole = Literal[Role.SPECIALIST]

class RoleSpec(MeridianModel):                        # config.py, from env; one line per role
    model: str
    effort: Literal["low", "medium", "high"] | None
    cap_s: float                                      # Jev 3, specialist 8, responder 12, brief 12 (proposal, DO-1 §8.1)
    max_tokens: int
    redaction: RedactionProfile                       # JEV for planner/classifier; SONNET for the rest

class ModelSettings(MeridianModel):                   # config.py; validated at start-up (review S-4)
    choice: dict[ChoiceRole, tuple[Literal["openrouter_jev", "anthropic"], RoleSpec]]
    structured: dict[StructuredRole, tuple[Literal["anthropic"], RoleSpec]]   # Jev is not a legal value here
    tools: dict[ToolRole, tuple[Literal["anthropic"], RoleSpec]]
    # A role in the wrong map, or Jev configured for a structured or tool role, fails Settings validation.

class ModelOutcome(MeridianModel, Generic[T]):
    value: T | None; calls: tuple[CallRecord, ...]; failure: ProviderFailure | None; halt: Halt | None

class ModelGateway:
    def __init__(self, *, choice: Mapping[ChoiceRole, tuple[ChoiceModel, RoleSpec]],
                 structured: Mapping[StructuredRole, tuple[StructuredModel, RoleSpec]],
                 tools: Mapping[ToolRole, tuple[ToolCallingModel, RoleSpec]],
                 ledger: LedgerService, trace: TraceSink, redact: Redactor, limits: Limits) -> None: ...
    def choose(self, role: ChoiceRole, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]: ...
    def structured(self, role: StructuredRole, req: StructuredRequest[T], ctx: TurnContext) -> ModelOutcome[T]: ...
    def tool_step(self, role: ToolRole, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[ToolStep]: ...

# Built in web/container.py, for example:
# ModelGateway(choice={PLANNER: (jev, …), CLASSIFIER: (jev, …), PLANNER_FALLBACK: (sonnet, …)},
#              structured={RESPONDER: (sonnet, …), BRIEF: (sonnet, …)}, tools={SPECIALIST: (sonnet, …)}, …)
```

**Gateway rules, in order:** refuse at once if models are disabled (our cap or the provider circuit); `timeout =
ctx.budget.timeout_for(spec.cap_s)`, and a `None` returns `halt=DEADLINE` without a call; at most **2 attempts**, the
second only for a retryable failure whose wait (`retry_after_s`, or backoff 0.5–1 s) plus 1 s still fits; every
attempt writes a `spend_ledger` row and a masked span; `PROVIDER_SPEND_CAP` trips the circuit (`services/ledger.py`);
the per-turn Sonnet-call brake (6, proposal) is counted here.

**Role caps under the 60 s deadline [Decided SDQ-1].** The deadline bounds the turn; the role caps (proposal) bound
each call, so one stalled call cannot use the whole minute. With 60 s, the one retry DO-1 allows almost always fits;
the attempt count stays at 2 (DO-1 §11 decision 5 is not an SDQ and is unchanged).

---

## 13. Other ports, storage and the case service

> Superseded at Stage 7: `UnitOfWork.cases` (`CaseRepos`) belongs to A0 (AEA-10), not A6: AEA-10 owns `repos_cases.py` whole and writes every `schema/*.sql`, because five tickets write the cases tables (slice plan §0 deviation 1; [code-design.md](../code-design.md) §8). The `# A6` comments and the "owned by the area that writes its tables" sentence below are read that way.

> Superseded at Stage 7: AEA-02 creates all seven `adapters/sqlite/repos_*.py` as empty shells; AEA-10 writes every `schema/*.sql` and fills `repos_core` and `repos_cases`, and AEA-26, 27, 28, 44, 32 fill spend, identity, booking, staff, ops (slice plan §0 deviation 1, rows AEA-02 and AEA-10; merge-clashes MC-10); added repository methods: [stage7/cases.md](stage7/cases.md) §1.2.

> Superseded at Stage 7: `TraceSink.export_status` takes the turn's handle, `export_status(turn: SpanHandle)` ([stage7/models.md](stage7/models.md) §4, MOD-9; MC-28).

```python
class RetrievalResult(MeridianModel):
    passages: tuple[Passage, ...]                     # top k, current files only (excluded files are never indexed)
    below_floor: bool                                 # nothing cleared the relevance floor → "no current source"
class IndexInfo(MeridianModel):
    embedding_model: Literal["BAAI/bge-small-en-v1.5"]; dimension: int; chunks: int; manifest_hash: str; files: int

class RetrievalIndex(Protocol):
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult: ...
    def info(self) -> IndexInfo: ...                  # readiness: files == 17 in the manifest, dimension matches

class Clock(Protocol):
    def now(self) -> datetime: ...                    # tz-aware America/Chicago; never the server's wall clock (R-3)

# No event Protocols (orchestrator decision 2026-10-21, review S-5): writers append to `events` with
# tx.events.append(...) inside their own transaction; the SSE routes poll `events WHERE stream = ? AND id > ?`
# about once a second [A] on a CapacityLimiter(4), and a reconnect replays from Last-Event-ID. Same path live and replay.

class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> ContextManager[SpanHandle]: ...
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self) -> Literal["off", "sent", "failed"]: ...   # → turn.trace_export (DO-6)

class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> ContextManager[UnitOfWork]: ...

class UnitOfWork(Protocol):                           # the transaction boundary; one SQLite transaction on meridian.sqlite
    """Repositories are CONCRETE classes in adapters/sqlite/repos_*.py, with no Protocols of their own (review S-6:
    one implementation, temp-SQLite tests). Each file is owned by the area that writes its tables (code-design §8).
    A0 creates all seven repo classes in wave 0 (the six per-area ones as empty stubs with a constructor) and
    SqliteUnitOfWork constructs all seven; the attribute types below are imported under TYPE_CHECKING, so the port
    never imports adapters at runtime. Owning areas fill only their own file; db.py and this port stay frozen (RB-1).
    Trigger to add repository Protocols: the Postgres step (DO-1 §7 step 5) starts."""
    core: CoreRepos            # A0: conversations, messages, turns, actions, lookup_log, check_events, events, customers
    spend: SpendRepo           # A2
    identity: IdentityRepos    # A4: identity_codes, demo_inbox, invoices (read)
    booking: BookingRepos      # A5: appointment_slots, appointments, technicians
    cases: CaseRepos           # A0 (AEA-10): cases, case_events, promises, followups, activities, demo_state, job_runs, reset/seed
    staff: StaffRepos          # A9: staff_sessions, flags
    ops: OpsRepos              # A10a: health_events, deploy_records, eval results (read)
    def commit(self) -> None: ...

# The methods every area relies on (concrete, listed so builders agree on names):
#   core.actions.record(action: CompletedAction) -> CompletedAction        idempotent on ActionKey: returns the existing row
#   core.actions.for_thread(thread_id) -> tuple[CompletedAction, ...]
#   core.lookup_log.append(entry: LookupEntry) -> int
#   core.events.append(stream: StreamKey, event: StreamEvent) -> EventId; core.events.after(stream, last: EventId) -> list
#   core.turns.begin(ids, received_at) -> TurnBegin                        new | completed(stored response) | running | failed
#   core.turns.finish(turn_id, record: TurnRecord) -> None
#   booking.slots.get_for_update(slot_id) -> Slot | None                    re-read inside the transaction (R-19)
#   booking.slots.set_status(slot_id, status) -> None

class CaseService:                                    # services/cases.py (A6): ONE concrete class (review S-7, S-8)
    def open_case(self, tx: UnitOfWork, req: HandoffRequest, promise: Promise, now: datetime) -> HandoffResult: ...
                                                      # the only service method that takes a caller's tx (HandoffService)
    def attach_brief(self, case_ref: CaseRef, brief: Brief) -> None: ...
    def open_case_for_thread(self, thread_id: ThreadId) -> CaseSummary | None: ...
    def queue(self, role: StaffRole, now: datetime) -> QueueView: ...                     # CON-11
    def detail(self, case_ref: CaseRef, role: StaffRole, now: datetime) -> CaseDetail: ...   # CON-12
    def oversight(self, now: datetime) -> OversightView: ...                              # CON-17
    def apply(self, case_ref: CaseRef, action: CaseAction, actor: StaffActor,
              expected_version: int, now: datetime) -> CaseSummary | CaseActionRejected: ...   # CON-13
    def set_followup(self, thread_id: ThreadId, choice: FollowUpChoice, now: datetime) -> FollowUp: ...   # CON-5
    def record_activity(self, case_ref: CaseRef, activity: ActivityIn, actor: StaffActor, now: datetime) -> Activity: ...  # CON-15
    def convert_live_queued(self, now: datetime) -> int: ...                              # shift end (N-12)
    # Staff routes never call open_case; code-review-agent checks it with a grep, not an interface.
```

---

## 14. Service signatures used across areas

> Superseded at Stage 7: `NotVerified` no longer covers "cap reached": the fourth send returns `CodeCapReached` (`CODE_CAP_REACHED`), and a failed code is `CodeWrong`, `CodeExpired` or `CodeLocked` ([stage7/graph-tools.md](stage7/graph-tools.md) §5, GRT-3; graph-tools ledger C-12). The `NotVerified` comment in `IdentityService` below is corrected to match.

> Superseded at Stage 7: `ResetService` takes web's `ResetGate` and `reset(now, *, request_id, session_id, role) -> ResetDone | ResetFailed` (`None, None` for the operator script), and `SchedulerJob` gains a UTC `wall_clock`: [stage7/cases.md](stage7/cases.md) §6–§7, merge-clashes MC-19, MC-20.

```python
class TurnService:
    def run_turn(self, cmd: RunTurn) -> TurnResponse: ...
    # 1 admission (≤ 30 in flight, Decided SDQ-9) → BUSY   2 SpendGuard → SPEND_CAP_REACHED   3 turns.begin(turn_id):
    #   completed → return the stored response; running → TURN_IN_PROGRESS; new or failed → run
    # 4 intake + STORE redaction; customer message row   5 run_graph(input, context)  (an injected callable, so A8
    #   builds before the graph exists; the container passes the compiled graph's invoke)
    # 6 halt DEADLINE → TURN_TIMEOUT reply from settled   7 persist reply message, turn record, check events
    # 8 return ComposedReply as TurnResponse (api-con-mapping CON-2)

class RunTurn(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId; demo_session: str
    payload: TurnPayload                              # text | choice | code (api-con-mapping CON-2)
    run_tag: Literal["live", "eval", "load"]; run_id: str | None

class IdentityService:                               # each method opens and commits its own transaction (review S-6)
    def locate(self, thread_id: ThreadId, locator: Locator, now: datetime) -> Located | NotVerified: ...
    def send_code(self, thread_id: ThreadId, demo_session: str, now: datetime) -> CodeSent | NotVerified | CodeCapReached: ...
    def verify(self, ids: TurnIds, digits: SecretStr, now: datetime) -> Verified | CodeWrong | CodeExpired | CodeLocked: ...
                                                      # Verified writes actions(verified) in the same transaction
    def inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]: ...       # CON-6, scoped (N-11)
    # Codes: 6 digits, HMAC-SHA256(session secret), 10-minute expiry, 3 tries, ≤ 3 sends per conversation [A].
    # NotVerified is identical for no match, ambiguous and no contact (R-16).

class SchedulingService:                             # each method opens and commits its own transaction
    def find_windows(self, query: WindowQuery, now: datetime) -> WindowsFound | OutOfArea: ...
    def book(self, key: ActionKey, scope: ToolCallScope, slot_id: int, issue: str,
             lookup: LookupEntry) -> WriteResult | SlotTaken | Refused: ...
    def move(self, key: ActionKey, scope: ToolCallScope, appointment_id: int, new_slot_id: int,
             lookup: LookupEntry) -> WriteResult | SlotTaken | Refused: ...                    # refuses fee-bearing
    def cancel(self, key: ActionKey, scope: ToolCallScope, appointment_id: int,
               lookup: LookupEntry) -> WriteResult | Refused: ...                              # refuses fee-bearing
    def request_change(self, key: ActionKey, scope: ToolCallScope, appointment_id: int,
                       change: Literal["move", "cancel"], wanted_text: str,
                       lookup: LookupEntry) -> ChangeRequestDraft | Refused: ...
    # Each write: one transaction = slot re-read + write + actions row + lookup_log row (DO-1 §9).
    # scope carries the verified customer, the shown slot ids and the clock reading.
    # Refused.code ∈ {fee_bearing, not_shown, outside_service_area, wrong_service_type, booking_cap, not_owned}.

class ResetService:                                  # services/reset.py (A6): adapters injected as callables (review S-3)
    def __init__(self, uow: UnitOfWorkFactory, restore_working_copy: Callable[[], None],
                 clear_checkpoints: Callable[[], None], seed_demo: Callable[[UnitOfWork], int]) -> None: ...
    def reset(self, now: datetime) -> ResetDone: ...

class SchedulerJob:                                   # services/scheduler.py (A6)
    def __init__(self, uow: UnitOfWorkFactory, cases: CaseService, clock: Clock,
                 prune_checkpoints: Callable[[], int]) -> None: ...                  # prune(keep=2) [Decided SDQ-10]
    def tick(self) -> JobRun: ...

class LedgerService:
    def record(self, call: CallRecord, ids: TurnIds) -> None: ...
    def spend_today(self) -> float: ...                # America/Chicago midnight to midnight (decided 2026-10-21, per
                                                      #   UI_CONTRACTS CON-19; DO-7 M-26 still says UTC, reported)
    def allow_turn(self) -> bool: ...                  # $30/day [T]; a running turn may overrun by one turn's cost
    def trip_provider_cap(self, failure: ProviderFailure) -> None: ...
    def models_disabled(self) -> bool: ...
```

---

## 15. Sources

DO-2 §A.1–§A.6, DO-1 §8–§9, §11 and SDQ-1…SDQ-10 as decided by Innocent 2026-10-21 (orchestrator message) · PRD R-2, R-5–R-8, R-13–R-29, R-41, R-44–R-47 ·
SP-1 build plan §4.1, §4.4, steps 7–9 (shapes reused and changed where noted) · research §1, §2b, §4 · readiness SD-6.3 ·
consolidated direction §5, §6, §9.3, §9.4 · DO-6 records and status values · SCREEN_SPECS N-4, N-6–N-9, N-26, N-27.

---

## 16. Stage 7 addenda (2026-10-21)

**Why this section exists.** Writing the Stage 7b ticket specs showed that many shapes the tickets need were missing
here: which file a type lives in, what an adapter returns versus what the gateway adds, the login session, the reset
gate, the storage columns, the tool dispatcher. The resolvers added them in eight addenda under
[`stage7/`](stage7/) rather than rewriting this file. **Each addendum is the single definition of every shape it
owns. Where §16 (an addendum) and an earlier section of this file disagree, §16 wins.** The `> Superseded at Stage 7`
notes above mark the known disagreements; a disagreement without a note is still settled by the addendum. Where two
addenda disagree, [`docs/plans/7b-decisions/merge-clashes.md`](../../plans/7b-decisions/merge-clashes.md) names the
single owner. Decision logs per topic are in `docs/plans/7b-decisions/<topic>.md`.

| Addendum | What it defines | AEA tickets |
|---|---|---|
| [`stage7/models.md`](stage7/models.md) (MOD) | `ProviderCall` vs `CallRecord` (what an adapter reports vs what the gateway adds); adapter constructors and the prices they own; the complete provider-failure mapping; trace types (`SpanHandle`, `TraceSink.export_status(turn)`, the Langfuse sink and its settings); the gateway rules restated; `LedgerService` with the circuit rule; the container wiring this implies | AEA-17, 18, 19, 20, 26 (`20_spend.sql` by AEA-10) |
| [`stage7/data.md`](stage7/data.md) (DAT) | `privacy/redact.py`; `policy/texts.py`; the retrieval build (`retrieval/{settings,manifest,ingest}.py`, the ingest CLI); the fastembed adapter and the knowledge tool; eval case files; eval harness records, report and ledger; deploy (`Dockerfile`, `railway.json`, `scripts/`); documents | AEA-03, 04, 06, 07, 08, 09, 11, 16, 24, 25, 33, 50, 54, 55, 56 |
| [`stage7/cases.md`](stage7/cases.md) (CAS) | Storage: tables and columns, repository methods added to §13, what a reset restores and clears, the reset callables, the test fixture home; booking policy; handoff policy (business days, promise table and due times, priority, escalation rows 4, 6, 7); scheduling service types; `CaseService` and `HandoffService`; demo clock, staffing and scheduler; reset and seed; ops (health, alerts, `repos_ops`); the metrics reader; integration | AEA-10, 13, 14, 28, 29, 30, 31, 32, 52, 53 |
| [`stage7/web.md`](stage7/web.md) (WEB) | Wire errors (one `ApiProblem`, one handler, `ApiErrorCode` = the OpenAPI enum); the login session as the web shell sees it; the `require_staff` declaration; request context and the providers in `web/deps.py`; rate limits; the gate and public paths; the reset gate (`services/reset_gate.py`); CON-4 person request; CON-2 additions; web log records; CON-3 stream rules; frontend serving; the shared OpenAPI response check | AEA-01 (rate-limit numbers), 23, 40, 41, 42, 43, 49 |
| [`stage7/staff.md`](stage7/staff.md) (STF) | Staff roles and the acting identity (`StaffRole`, `StaffActor`, personas); `services/staff.py` (login-session store, role check, flags); staff storage; what a reset does to staff state; `services/live_chat.py`; staff route rules; the CON-21 case stream; CON-8 clock advance; metrics reads; time sources on staff wire fields; behaviour during a reset | AEA-44, 45, 46, 47, 48 |
| [`stage7/graph-core.md`](stage7/graph-core.md) (GRC) | Where the per-turn types live (`domain/turn.py`); `TurnInput`, `TurnContext` (`span`, `intake`) and the intake carrier; `GateFlags` and card ids; `GraphDeps`, node spans and the runner; halt routing; the one `Settled` builder (`settled_for`); chat window limits; what increments `FailureCounters`; the planner state key; the promise text check | AEA-02, 12, 21 (also 01, 10, 14, 36, 37, 38) |
| [`stage7/graph-tools.md`](stage7/graph-tools.md) (GRT) | Tool dispatch and executor registration (`ToolSchema`, `ToolCall`, `ToolCallRecord`); the specialist runner and its inputs; specialist capture shapes; account executors; identity service result types, tables and inbox; R-44 quick checks | AEA-22, 27, 35, 39 (executors 28, 33; wiring 51) |
| [`stage7/graph-nodes.md`](stage7/graph-nodes.md) (GRN) | `CheckEvent` (one shape for every check); R-46 additions in `checks.py`; the brief assembled, checked and stored by the reply node; failure signals (the `signal` log record, `agent/signals.py`); both planners failing; burning smell with both dangers ruled out; CAP-2 on the DANGER path | AEA-02, 15, 21, 36, 37, 38, 51 |
