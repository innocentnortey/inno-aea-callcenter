# Signatures and types added at Stage 7 (2026-10-21), graph: tools part

**Topic:** graph, tools part (prefix GRT): tool dispatch and executor registration, `ToolCallScope`, the specialist
runner's inputs and its `GraphDeps` field, the identity service's result types and tables, the demo inbox's code,
the staff note's fee value, and R-44 quick checks. **Tickets:** AEA-22, AEA-27, AEA-35, AEA-39 (and the executor
owners AEA-28, AEA-33, the wiring ticket AEA-51). **Decision log:**
[`docs/plans/7b-decisions/graph-tools.md`](../../../plans/7b-decisions/graph-tools.md) (GRT-1…GRT-10).
**Signature-check pass (2026-10-21):** `ProviderMessages` given fields (§2, GRT-9; withdrawn in the residual pass in
favour of models.md §1); `IdentityRepos` and its row types signed (§5, GRT-10).
**Residual pass (2026-10-21, `docs/plans/7b-decisions/residuals-graph.md`):** R-G-3 (`SCHEDULE_FEES` tune-up row,
`MEMBER_ALLOWANCE_ROWS`, §4), R-G-4 (§2), R-G-12 and R-G-19 (who builds the task; `AppointmentView`,
`SchedulingSliceInputs`, §2–§3), R-G-17 (tool spans from the runner, §2).
**Status:** planned, nothing built. Written by the Stage 7b graph-tools resolver (Claude, Opus 5.5).
**Merge pass (2026-10-21):** aligned with `merge-clashes.md` MC-3, MC-20, MC-22 (no MC row names this file); identity
wire codes settled in §5 (the signed UX-3 contracts win); sibling citations corrected (graph-core GRC-6, GRC-10);
graph-nodes' and data's requests to this part applied (§1, §2). Ledger: *Changed at merge* lines on GRT-3, GRT-6.

These follow the sketch rules of [internal-components.md](../internal-components.md) (DO-4) §0: field names, types and
validators are the agreement; bodies are not. Types DO-4 already defines (`ToolDef`, `ToolCallScope`, `LookupEntry`,
`ToolError`, `ToolResult`, `Passage`, `KnowledgeResult`, `AccountResult`, `SchedulingResult`, `SpecialistTask`,
`ModelGateway`, `ToolCallingModel`, `IdentityState`) are referenced, not repeated, except where a field is added.
Sibling parts: [graph-core.md](graph-core.md) (GRC: `GraphDeps`, `TurnInput.message_id`, `TurnContext.intake`),
[graph-nodes.md](graph-nodes.md) (GRN: check events, signals).

**Labels:** [Decided §7, engineering] an interface, name, location or internal type decided here (rule
`system-design-questioning` 3) · [A] a default a named measurement replaces · [Source: …] settled by a document.
No item in this part waits on Innocent.

---

## 1. Tool dispatch and executor registration (AEA-22; GRT-1)

**In practice.** The account specialist's model asks for `read_invoices` before the code turn. The runner hands the
step's tool calls to `ToolDispatcher.dispatch(calls, kinds={account_read}, scope)`. The scope's `customer_id` is
`None`, so dispatch returns `ToolError(code=not_verified)` for that `tool_call_id`, never calls the executor, and writes
one `lookup_log` row saying the call was refused. After Omar's correct code, the same call with
`scope.customer_id = MHC-10002` runs the executor and the row records `INV-204411`.

```python
# domain/tools.py (AEA-02) — additions                                   [Decided §7, engineering] GRT-1
class ToolKind(StrEnum):                              # DO-4 §5 lists the values without the class
    KB_SEARCH = "kb_search"; ACCOUNT_READ = "account_read"; SLOT_SEARCH = "slot_search"
    BOOK = "book"; MOVE = "move"; CANCEL = "cancel"; CHANGE_REQUEST = "change_request"

class ToolErrorCode(StrEnum):                         # domain/common.py; DO-4 §5's eleven values, plus two
    NOT_ALLOWED = "not_allowed"; BAD_ARGUMENTS = "bad_arguments"; UNKNOWN_TOOL = "unknown_tool"
    NOT_VERIFIED = "not_verified"; NOT_SHOWN = "not_shown"; FEE_BEARING = "fee_bearing"
    OUTSIDE_SERVICE_AREA = "outside_service_area"; SLOT_TAKEN = "slot_taken"; BOOKING_CAP = "booking_cap"
    IDENTICAL_CALL = "identical_call"; TOOL_FAILED = "tool_failed"
    WRONG_SERVICE_TYPE = "wrong_service_type"; NOT_OWNED = "not_owned"
    # NEW: the two Refused.code values (DO-4 §14; cases.md §4 `Refused.code`, six values) that DO-4 §5's list lacked;
    #   the scheduling executors (AEA-28) map all six one-to-one.

class ToolSchema(MeridianModel):                      # ports/models.py; DO-4 §12 uses it in ToolStepRequest unnamed
    name: str; description: str
    input_schema: dict[str, JsonValue]                # = args_model.model_json_schema(), trimmed; never a scope field
    strict: bool = True                               # adapters send strict tools, tool_choice auto (research §1)

class ToolCall(MeridianModel):                        # ports/models.py; DO-4 §12's comment "ToolCall(id, name, args)"
    id: str; name: str
    args: dict[str, JsonValue] | None                 # None = the provider's arguments did not parse

class ToolCallRecord(MeridianModel):                  # one per dispatched call; in every SpecialistResult.tools
    tool_call_id: str
    name: str                                         # as the model sent it (an unknown name is kept, ≤ 64 chars)
    kind: ToolKind | None                             # None for unknown_tool
    outcome: Literal["ok", "refused", "failed"]       # refused = a guard or executor ToolError; failed = tool_failed
    error: ToolErrorCode | None                       # graph-core GRC-13 counts tool_failures from this
    record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]   # = the LookupEntry's
    lookup_id: int | None                             # the lookup_log row (None only if its write failed; logged)
    elapsed_ms: int
```

```python
# agent/tools/dispatch.py (AEA-22)                                       [Decided §7, engineering] GRT-1
class ToolRegistry:
    def __init__(self, defs: Iterable[ToolDef]) -> None: ...
        # Raises ValueError at start-up (never at turn time) on a duplicate name or a name outside [a-z_]{1,64}.
    def get(self, name: str) -> ToolDef | None: ...
    def for_kinds(self, kinds: frozenset[ToolKind]) -> tuple[ToolDef, ...]: ...   # stable order: by name
    def check_covers(self, kinds: frozenset[ToolKind]) -> None: ...  # start-up: every kind a spec names has a tool

class DispatchedCall(MeridianModel):
    tool_call_id: str
    content: str                                      # JSON text the model receives, ≤ 4,000 chars (DO-4 §5)
    result: ToolResult                                # for the runner's capture; ToolError inside for_model on refusal
    record: ToolCallRecord

class ToolDispatcher:
    def __init__(self, registry: ToolRegistry, uow: UnitOfWorkFactory) -> None: ...
    def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]: ...    # generated, cached per kind set
    def dispatch(self, calls: Sequence[ToolCall], *, kinds: frozenset[ToolKind],
                 scope: ToolCallScope) -> tuple[DispatchedCall, ...]: ...
        # Same length and order as `calls`; never raises.
        # Guard order per call: unknown name → unknown_tool; kind not in `kinds` → not_allowed; args None or invalid
        #   against args_model → bad_arguments; requires_verified and scope.customer_id is None → not_verified.
        #   A refused call never executes.
        # Execute: executor(args_model instance, scope) with no unit of work open (DO-3 §2.3 rule 1); an exception →
        #   ToolError(tool_failed, retryable=False), logged by type name only.
        # Lookup log: executed read tools → ToolResult.lookup appended in its own short `uow(write=True)` after the
        #   executor returns; write tools with lookup_written=True → skipped; refused and failed calls → dispatch
        #   builds the entry itself: LookupEntry(tool=name, record_ids=(), passage_ids=(),
        #   result_seen="refused:<code>" | "failed", message_id=scope.message_id, turn_id=scope.ids.turn_id).
        #   So every call has exactly one row (AEA-22 AC-6). A failed lookup write is logged and leaves lookup_id None;
        #   it does not change what the model receives.
```

**Registration: a factory per executor area, called once by the container; no global registry.** Each executor
module exposes one factory that returns its `ToolDef`s with the executors bound to their dependencies. The graph
wiring (AEA-51) builds the one registry from the three factories; no area edits another area's hunk, and nothing
registers itself at import time (so tests build a registry from doubles).

```python
# agent/tools/knowledge.py (AEA-33)
def knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]: ...   # (KB_SEARCH bound to the index, data.md §4)
    # Returns one ToolDef with data.md §4's KB_SEARCH name, kind, KbSearchArgs and flags, its executor bound to
    #   `retrieval`. Nothing self-registers: AEA-51's registry is built from this factory (data.md §4, §9 item 5 agree).
# agent/tools/account.py (AEA-27)
def account_tools(uow: UnitOfWorkFactory) -> tuple[ToolDef, ...]: ...        # §4 below
# agent/tools/scheduling.py (AEA-28)
def scheduling_tools(scheduling: SchedulingService) -> tuple[ToolDef, ...]: ...   # names are AEA-28's choice

# web/container.py, graph-wiring hunk (AEA-51), illustrative:
registry = ToolRegistry((*knowledge_tools(retrieval), *account_tools(uow), *scheduling_tools(scheduling)))
for spec in SPECS.values(): registry.check_covers(spec.tool_kinds)
dispatcher = ToolDispatcher(registry, uow)
```

Consumers: AEA-22 (builds it), AEA-35 (runner calls `schemas` and `dispatch`), AEA-27/28/33 (factories), AEA-51
(wiring, start-up checks).

---

## 2. The specialist runner and its inputs (AEA-35, AEA-39; GRT-6)

**In practice.** WP-2 after the code: the act node builds a `SpecialistTask` for `read_invoice` and a
`ToolCallScope(customer_id=MHC-10002, shown_slot_ids=∅, now=ctx.now, message_id=turn_input.message_id, ids=ctx.ids)`
(via `scope_for`),
and calls `deps.specialists.run(task, scope, ctx)`. The runner starts a fresh provider message list with the masked
task text, asks the gateway for a tool step, passes the requested calls to the dispatcher, appends the results, and
stops at `report_facts`, a step with no tool call, 2 tool rounds, an identical call, or a gateway halt. The account
spec's builder folds the captured invoice into `AccountResult`.

**`ProviderMessages`** is defined once, in stage7/models.md §1 (MOD-17: `provider: ProviderName`, `model: str`,
`items: tuple[JsonValue, ...]`), which owns `ports/models.py`'s model types. GRT-9's second field set (`provider:
Literal["anthropic"]`, `payload`) is withdrawn (residual pass, R-G-4); its two rules moved to models.md §1 unchanged:
`append` refuses a list built for another (provider, model) with `ValueError`, and the object is never logged, traced or
stored. In this file "the message list" means that type.

```python
# ports/models.py (AEA-02)                                               [Decided §7, engineering] GRT-6
class ToolTranscript(Protocol):                       # the two message-building methods of ToolCallingModel (DO-4 §12)
    def start(self, user: str) -> ProviderMessages: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...
    # No HTTP, no ledger row, no span. Any ToolCallingModel satisfies it structurally; the container passes the SAME
    # adapter object the gateway holds for Role.SPECIALIST (models.md §7 builds one adapter per (provider, model)).
    # ModelGateway is unchanged (models.md §5: "The constructor and the three methods are DO-4 §12 unchanged").
```

```python
# agent/specialists/specs.py (AEA-35)                                    [Decided §7, engineering] GRT-6
@dataclass(frozen=True)
class RunOutcome:                                     # what the runner hands a spec's builder; never leaves the run
    task: SpecialistTask
    captured: tuple[KnowledgeCapture | AccountCapture | SchedulingCapture, ...]   # from ToolResult.captured, in order
    passages_returned: tuple[Passage, ...]            # every passage any kb_search returned this run
    report: LLMFacing | None                          # the validated report_facts args, or None
    quick_checks: tuple[Passage, ...]                 # §6; () unless the task asked for the offer
    tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]
    brake: HaltReason | None; failure: ProviderFailure | None

@dataclass(frozen=True)
class SpecialistSpec:
    kind: Literal["knowledge", "account", "scheduling"]
    tool_kinds: frozenset[ToolKind]                   # knowledge {kb_search}; account {account_read};
                                                      #   scheduling {slot_search, book, move, cancel, change_request}
    report_model: type[LLMFacing]                     # KnowledgeReport | AccountReport | SchedulingReport (DO-4 §5)
    render: Callable[[SpecialistTask, TurnContext], tuple[str, str, str]]   # (system_prefix, system_dynamic, user)
    build_result: Callable[[RunOutcome], SpecialistResult]                   # folds captures; never reads model text
                                                      #   for a record value (DO-4 §5 "captured by code")
SPECS: Mapping[Literal["knowledge", "account", "scheduling"], SpecialistSpec]

# agent/specialists/runner.py (AEA-35)                                   [Decided §7, engineering] GRT-6
class SpecialistRunner:                               # replaces DO-4 §5's free function run_specialist(spec, task, ctx)
    def __init__(self, *, gateway: ModelGateway, transcript: ToolTranscript, dispatcher: ToolDispatcher,
                 specs: Mapping[str, SpecialistSpec], brakes: Brakes, trace: TraceSink) -> None: ...
        # trace: NEW (R-G-17). After every dispatch (model rounds and the quick-check call), one span per
        #   DispatchedCall: trace.node(ctx.span, "tool:" + record.name if record.kind is not None else "tool:unknown",
        #   record.elapsed_ms, record.outcome). TraceSink.node is models.md §4's method, unchanged; the name comes from
        #   the registry (an unknown, model-supplied name never becomes a span name); no arguments, no result text.
        #   This is DO-6 rule 18's "tool call is a timed span" and CAP-1's nested tool span. The dispatcher (AEA-22)
        #   stays trace-free: it measures ToolCallRecord.elapsed_ms and emits nothing.
    def run(self, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext) -> SpecialistResult: ...
        # spec = specs[task.task.specialist] (a lookup, not a branch). Never raises.
        # tools sent = dispatcher.schemas(spec.tool_kinds) + the report_facts schema generated from spec.report_model;
        #   report_facts is handled by the runner and never dispatched (AEA-35 AC-2).
        # each model step: gateway.tool_step(Role.SPECIALIST, ToolStepRequest(...), ctx); its calls → result.calls;
        #   its halt → brake (DEADLINE, BRAKE_SONNET_CALLS, PROVIDER_SPEND_CAP) and stop; its failure → failure, stop.
        # loop rules = DO-4 §5 runner rules; tool rounds capped by brakes.tool_rounds (2, proposal).
        # `transcript.start(user)` receives the SONNET-profile text SpecialistTask already holds; the runner adds none.
        # The result's `brake` / `failure` (DO-4 §5 fields on every SpecialistResult) are copied from RunOutcome; the
        #   runner emits no signal and writes no check event (graph-nodes §4, GRN-4: AEA-39 emits).

def scope_for(state: ConversationState, ctx: TurnContext) -> ToolCallScope: ...      # agent/specialists/runner.py
    # customer_id = state.identity.customer_id only when state.identity.status == "verified", else None;
    # shown_slot_ids = frozenset(s.slot_id for s in state.shown_slots); now = ctx.now; ids = ctx.ids;
    # message_id = state.turn_input.message_id (graph-core §2, GRC-10). Pure; the act node calls it per task.
```

```python
# domain/specialists.py (AEA-02): SpecialistTask gains one field         [Decided §7, engineering] GRT-8
class SpecialistTask(MeridianModel):                  # DO-4 §5, plus:
    offer_quick_checks: bool = False                  # set by the act node (§6); only scheduling BOOK_NEW tasks
```

> **Home note (AEA-35b, Innocent 2026-10-21):** `SpecialistTask`, `KnowledgeSlice` (`kind` only) and `AccountSlice` (`kind` only) live in `domain/tools.py`, not `domain/specialists.py`, because `specialists.py` cannot import `PlannedTask` from `domain/turn.py` without an import cycle; AEA-08 reconciles the file names above.

**`GraphDeps` field** (graph-core §4, GRC-6: "the fields graph-tools.md … name. Their names and types win"; AEA-21
adds it as written): `specialists: SpecialistRunner`. The dispatcher has no
`GraphDeps` field of its own: only the runner calls it.

**Who builds the `SpecialistTask`** (R-G-12): the act node, `run_specialist` (AEA-39), from the `PlannedTask` its
`SpecialistSend` carries, with graph-nodes §9.5's pure `build_specialist_task` (SONNET-masked texts, the slice, and §6's
`offer_quick_checks` rule). `route_act_plan` (AEA-21) only fans out (graph-core §11). The runner receives a finished task.

Consumers: AEA-35 (builds runner and specs; emits the tool spans), AEA-39 (builds each task, calls `scope_for` and
`deps.specialists.run`, one `Send` per task), AEA-21 (adds the field), AEA-51 (wiring: one adapter object to both the
gateway's tool map and `transcript`; test asserts `runner.transcript is` that adapter; passes the container's `trace`).

---

## 3. Specialist capture shapes (AEA-02 transcribes; AEA-27, 28, 33, 35 fill them)

DO-4 §5 names these as "defined in domain/specialists.py (A0)" without fields. View field names follow the OpenAPI
`AccountCardBlock` (amounts in integer cents; compose builds `Money`).                [Decided §7, engineering]

```python
class InvoiceLineView(MeridianModel):  description: str; amount_cents: int
class InvoiceView(MeridianModel):
    invoice_id: InvoiceId; lines: tuple[InvoiceLineView, ...]; total_cents: int; balance_cents: int
    issued_on: date; due_on: date; paid: bool         # as billed; never corrected (R-17)
class MembershipView(MeridianModel):  tier: Literal["none", "standard", "plus"]; renewal_date: date | None   # cases A-1
class WarrantyView(MeridianModel):  install_date: date; equipment_brand: str | None; sentence: str          # K-9 text
class StaffNote(MeridianModel):                       # staff-only (HP-3): brief and case view, NEVER the responder
    kind: Literal["billed_differs_from_schedule", "diagnostic_without_credit"]
    record_id: InvoiceId
    text: str = Field(max_length=300)                 # a fact, never a verdict (§5)
    source_file: Literal["pricing/2026_fee_schedule.pdf", "faq/customer_faq.md"]

class KnowledgeCapture(MeridianModel):  kind: Literal["knowledge"] = "knowledge"; result: RetrievalResult
class AccountCapture(MeridianModel):
    kind: Literal["account"] = "account"
    invoices: tuple[InvoiceView, ...] = (); membership: MembershipView | None = None
    warranty: WarrantyView | None = None; staff_notes: tuple[StaffNote, ...] = ()
class SchedulingCapture(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    windows: tuple[ShownSlot, ...] = (); write: WriteResult | None = None
    change_request: ChangeRequestDraft | None = None; refused: ToolErrorCode | None = None

# SchedulingResult (DO-4 §5) gains:                                                        GRT-8
    quick_checks: tuple[Passage, ...] = ()            # §6: troubleshooting passages offered (full passages for chips)

# domain/specialists.py (AEA-02): the two types SchedulingSlice needs     [Decided §7, engineering] R-G-19
class AppointmentView(MeridianModel):                 # DO-4 §5 SchedulingSlice.appointments named it without fields
    appointment_id: int
    date: date; window: Window                        # from the joined appointment_slots row
    service_type: ServiceType
    technician: str | None                            # technicians.name; None if the row has no technician
    is_warranty_visit: bool                           # no diagnostic fee applies when True (cases.md §4.1)
    # Never issue_description (audit D-11) and never customer_id (DO-4 §5: the model cannot name another customer).
    #   Built only by AppointmentsRepo.views_for_customer (cases.md §4.1); status is always 'scheduled' there.

class SchedulingSliceInputs(MeridianModel):           # what SchedulingService.slice_inputs returns (cases.md §4)
    zone: Zone | None                                 # → SchedulingSlice.customer_zone
    member: bool                                      # → SchedulingSlice.member
    appointments: tuple[AppointmentView, ...] = ()    # → SchedulingSlice.appointments
```

---

## 4. Account executors (AEA-27; GRT-4)

```python
# agent/tools/account.py (AEA-27)                                        [Decided §7, engineering]
class ReadInvoicesArgs(LLMFacing):
    invoice_number: InvoiceId | None = None           # the invoice the customer named, or None = this account's invoices
class ReadMembershipArgs(LLMFacing): pass
class ReadWarrantyArgs(LLMFacing): pass
# Tools: read_invoices, read_membership, read_warranty; kind account_read, effect "read", requires_verified True.
# Every read filters by scope.customer_id; an invoice number on another account reads as "no such invoice on this
# account" (ok=True, empty list): the same answer as a number that does not exist, so nothing reveals another account.
# for_model = the views only. captured = AccountCapture incl. staff_notes. LookupEntry.result_seen = ids and
# amounts, never staff-note text and never "149".

def staff_notes_for(invoice: InvoiceView, tier: Literal["none", "standard", "plus"]) -> tuple[StaffNote, ...]: ...
    # pure. Rule 1 (WP-2 "$144 vs $149 … always goes into the staff brief as a fact"): for each line whose description
    #   is a key of policy.booking.SCHEDULE_FEES, if amount_cents != the tier's scheduled amount → one
    #   billed_differs_from_schedule note: "INV-204411 bills After-hours dispatch at $144.00; the 2026 fee schedule
    #   lists $149.00 for non-members." A key in MEMBER_ALLOWANCE_ROWS is compared for tier "none" only (R-G-3): a
    #   member's "Seasonal tune-up" is included only twice a year, which the invoice cannot show, so a billed $129 to
    #   a member is not a difference the record proves (4 issued invoices bill it to members).
    # Rule 2 (WP-2 Gap, second way): a "Diagnostic visit" line beside at least one line that is not a scheduled fee and
    #   no negative (credit) line → one diagnostic_without_credit note: "INV-204411 bills the $89 diagnostic visit beside
    #   a repair with no credit line; the FAQ credits the diagnostic when the repair is approved at the same visit (the
    #   record does not say whether it was)."
```

```python
# policy/booking.py (AEA-13) — one constant added (cross-topic C-3)     [Source: pricing/2026_fee_schedule.pdf]
SCHEDULE_FEES: Mapping[str, Mapping[Literal["none", "standard", "plus"], int]] = {
    "Diagnostic visit":     {"none": 8900,  "standard": 0, "plus": 0},
    "After-hours dispatch": {"none": 14900, "standard": 0, "plus": 0},   # schedule row "After-hours emergency dispatch";
                                                                          #   key = the invoice line's wording (price book FEE-AH)
    "Seasonal tune-up":     {"none": 12900, "standard": 0, "plus": 0},   # R-G-3: schedule row "Seasonal tune-up (per
}                                                                         #   system) $129 / Included (2/yr)"; key = invoice
                                                                          #   wording (11 issued lines, price book HV-TUNE)
MEMBER_ALLOWANCE_ROWS: frozenset[str] = frozenset({"Seasonal tune-up"})  # R-G-3: member value is an allowance ("Included
                                                                          #   (2/yr)"), not a flat $0; staff_notes_for skips
                                                                          #   the member comparison for these keys
# fee_note's $89 and $129 read the same rows, so one constant owns the scheduled fee amounts. The tune-up row matters
#   for the customer: issued agents quoted the $89 diagnostic for tune-ups in 16 of 16 calls (handoff inventory SCH-TUNEUP).
```

---

## 5. Identity service: result types, tables, inbox (AEA-27; GRT-2, GRT-3, GRT-5)

**In practice.** Omar submits the locate card. The identity node builds `Locator.from_form(ctx.intake.form)` and calls
`locate` → `Located(masked_hint="the phone ending in 02")`, then `send_code` → `CodeSent(masked_hint=…,
expires_at=10:10, sends_left=2)`. The six digits exist in two places only: their HMAC in `identity_codes`, and the
process's in-memory inbox store until the code expires. The CON-6 route reads `inbox(demo_session)` and shows them.

```python
# domain/identity.py (AEA-02)                                            [Decided §7, engineering] GRT-5
class Locator(MeridianModel):                         # built by code from FormValues; a model never supplies one
    name: str | None = None; phone: SecretStr | None = None
    customer_id: CustomerId | None = None; invoice_number: InvoiceId | None = None
    # validator: exactly one of (name AND phone), customer_id, invoice_number (R-15). Errors carry no value.
    @classmethod
    def from_form(cls, form: FormValues) -> "Locator | None": ...  # None when the form holds no complete locator
    # Match rules (AEA-27): phone = digits only, last 10 equal; name = case- and space-insensitive full-name equality.
    # 0 matches → no match; > 1 → ambiguous; a match with neither phone nor email → no contact.

class Located(MeridianModel):
    kind: Literal["located"] = "located"
    masked_hint: str                                  # "the phone ending in 02" (phone first, else "the email at o···@…")
class NotVerified(MeridianModel):                     # NO fields: identical for no match, ambiguous, no usable contact
    kind: Literal["not_verified"] = "not_verified"    #   (R-16; UI_CONTRACTS NOT_VERIFIED). Not used for any cap (GRT-3).
class CodeSent(MeridianModel):
    kind: Literal["code_sent"] = "code_sent"; masked_hint: str; expires_at: datetime; sends_left: int = Field(ge=0, le=2)
class CodeCapReached(MeridianModel):                  # the 4th send in a conversation (UI CODE_CAP_REACHED); state → "locked"
    kind: Literal["code_cap_reached"] = "code_cap_reached"
class Verified(MeridianModel):
    kind: Literal["verified"] = "verified"; customer_id: CustomerId; action: CompletedAction   # actions(verified) row
class CodeWrong(MeridianModel):
    kind: Literal["code_wrong"] = "code_wrong"; tries_left: int = Field(ge=1, le=2)
class CodeExpired(MeridianModel):
    kind: Literal["code_expired"] = "code_expired"; resend_offered: bool; sends_left: int = Field(ge=0, le=2)
class CodeLocked(MeridianModel):                      # 3rd wrong try, or any try after the lock
    kind: Literal["code_locked"] = "code_locked"

class InboxMessage(MeridianModel):                    # CON-6; fields = OpenAPI InboxMessage
    id: str; at: datetime; to_masked: str             # "···02"
    code: SecretStr | None                            # the digits while this process holds them (below); else None
    status: Literal["active", "used", "expired"]; expires_at: datetime
    # The CON-6 route (AEA-43) unwraps `code` only while serialising the response and renders `body` from
    # policy/texts: INBOX_CODE_BODY with the digits, or INBOX_CODE_GONE and code "······" when `code` is None.
```

`IdentityService` keeps DO-4 §14's four signatures. Three clarifications:
- **`NotVerified` covers no cap and no failed code** (GRT-3; settled at merge 2026-10-21). `send_code` returns
  `NotVerified` when the thread has no located customer with a usable contact; `CodeCapReached` when 3 codes were
  already sent. `verify` never returns `NotVerified`. DO-4 §14's comment "and cap reached" and system design §10's
  *No account fishing* "and failed code all return the same `NOT_VERIFIED`" are superseded; AEA-08 (docs reconcile)
  edits both.
- **Wire codes: the signed UX-3 contracts win** [Source: UI_CONTRACTS *Named errors* rows CODE_WRONG … NOT_VERIFIED;
  SCREEN_SPECS SCR-1 rows 104–107; OpenAPI CON-2 composed errors]. Each result reaches the customer as exactly one
  CON-2 composed error (HTTP 200, `error` block):

  | Result | CON-2 code | Blocks (UI_CONTRACTS) |
  |---|---|---|
  | `NotVerified` (no match, ambiguous, no contact; byte-identical) | `NOT_VERIFIED` | `error` + `handoff` |
  | `CodeWrong(tries_left)` | `CODE_WRONG` | `error` + `code_prompt` (wrong, `tries_left`) |
  | `CodeExpired(resend_offered, sends_left)` | `CODE_EXPIRED` | `error` + `code_prompt` (expired, `resend_offered`) |
  | `CodeLocked` (3rd wrong try, or any try after) | `CODE_LOCKED` | `error` + `handoff` |
  | `CodeCapReached` (the 4th send) | `CODE_CAP_REACHED` | `error` + `handoff`, same sentence and card as `CODE_LOCKED` |

  No account is revealed by the separate codes: a code is only ever sent after a match. The identity node (AEA-36)
  maps result → `IdentityStep` and compose renders the code; neither re-groups them.
- **Reading state:** the identity node and `load_context` read `IdentityState` through `core.reads.identity_state`
  (cases.md §1.2), derived from the tables below.

**Where the code lives (GRT-2).** `services/identity.py` holds `_held: dict[int, tuple[SecretStr, datetime]]`
(inbox message id → digits, expiry) under a lock, plus `boot_id = uuid4()` per process. `send_code` writes the HMAC row
with `held_by = boot_id` and puts the digits in `_held`; entries are dropped at expiry (pruned on every call). After a
restart, `verify` treats a row whose `held_by` differs from this process's `boot_id` as **expired** (`CodeExpired`,
resend offered while under the cap), and `inbox` shows it with `code=None`. One process and one replica is the
deployment (system design §11 decisions 1–2); the multi-replica step (system design scale path step 6) must revisit this.

```sql
-- adapters/sqlite/schema/40_identity.sql (AEA-10 writes the DDL; AEA-27 the repository bodies) [Decided §7, engineering]
identity_threads(thread_id TEXT PRIMARY KEY, status TEXT NOT NULL CHECK (status IN
    ('not_checked','located','code_sent','verified','not_verified','locked')), customer_id TEXT NULL,
    masked_hint TEXT NULL, channel TEXT NULL CHECK (channel IN ('phone','email')), verified_at TEXT NULL, updated_at TEXT NOT NULL)
identity_codes(id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, customer_id TEXT NOT NULL,
    code_hmac TEXT NOT NULL, held_by TEXT NOT NULL, sent_at TEXT NOT NULL, expires_at TEXT NOT NULL,
    tries_left INTEGER NOT NULL CHECK (tries_left BETWEEN 0 AND 3), used_at TEXT NULL, inbox_message_id INTEGER NOT NULL)
demo_inbox(id INTEGER PRIMARY KEY AUTOINCREMENT, demo_session TEXT NOT NULL, thread_id TEXT NOT NULL,
    to_masked TEXT NOT NULL, sent_at TEXT NOT NULL, expires_at TEXT NOT NULL)   -- no code column, no body column
-- IdentityState: status/customer_id/masked_hint/verified_at from identity_threads; codes_sent = count of the thread's
-- identity_codes rows; code_expires_at, tries_left from its newest row (3 when none).
-- Times (sent_at, expires_at, used_at, verified_at, updated_at) are DEMO-clock readings (the `now` DO-4 §14 passes =
--   ctx.now), not wall time, so none carries a `_real`/`_wall` suffix (cases.md §1.1 wall-time rule, MC-20).
-- demo_inbox.demo_session = str(LoginSessionId) (staff.md §1, domain/staff.py; web.md §4 "routes pass str(session.session_id)").
```

The repository over those tables (AEA-10 creates the shell; AEA-27 fills the body). Every method runs inside the
caller's transaction (`tx.identity`, DO-4 §13); none commits. `IdentityService` is its only caller, plus the invoice
reads `account.py`'s executors make. [Decided §7, engineering] GRT-10

```python
# adapters/sqlite/repos_identity.py (AEA-27 body)
class IdentityThreadRow(MeridianModel):               # one identity_threads row
    thread_id: ThreadId; status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None; masked_hint: str | None; channel: Literal["phone", "email"] | None
    verified_at: datetime | None; updated_at: datetime
class IdentityCodeRow(MeridianModel):                 # one identity_codes row; code_hmac never leaves the service
    id: int; thread_id: ThreadId; customer_id: CustomerId; code_hmac: str; held_by: str
    sent_at: datetime; expires_at: datetime; tries_left: int = Field(ge=0, le=3); used_at: datetime | None
    inbox_message_id: int
class InboxRow(MeridianModel):                        # one demo_inbox row (no code, no body columns)
    id: int; demo_session: str; thread_id: ThreadId; to_masked: str; sent_at: datetime; expires_at: datetime

class IdentityRepos:
    def __init__(self, conn: sqlite3.Connection) -> None: ...         # the AEA-10 shell's constructor, unchanged
    def thread(self, thread_id: ThreadId) -> IdentityThreadRow | None: ...
    def save_thread(self, row: IdentityThreadRow) -> None: ...         # upsert on thread_id
    def add_code(self, thread_id: ThreadId, customer_id: CustomerId, code_hmac: str, held_by: str,
                 sent_at: datetime, expires_at: datetime, inbox_message_id: int) -> int: ...   # tries_left = 3
    def newest_code(self, thread_id: ThreadId) -> IdentityCodeRow | None: ...
    def codes_sent(self, thread_id: ThreadId) -> int: ...              # the cap check (≤ 3 per conversation)
    def spend_try(self, code_id: int) -> int: ...                      # tries_left − 1, floored at 0; returns the new value
    def mark_used(self, code_id: int, used_at: datetime) -> None: ...
    def add_inbox(self, demo_session: str, thread_id: ThreadId, to_masked: str, sent_at: datetime,
                  expires_at: datetime) -> int: ...                    # the inbox message id add_code records
    def inbox_for(self, demo_session: str) -> tuple[InboxRow, ...]: ...  # newest first; the session's rows only (N-11)
    def code_for_inbox(self, inbox_message_id: int) -> IdentityCodeRow | None: ...   # active / used / expired status
    def invoices_for(self, customer_id: CustomerId) -> tuple[InvoiceView, ...]: ...   # account.py; as billed (R-17)
    def invoice(self, customer_id: CustomerId, invoice_id: InvoiceId) -> InvoiceView | None: ...
        # filtered by customer_id: another account's number reads as None, the same as a missing one (§4)
    # Membership and warranty are columns of `customers` (A0's table): account.py builds MembershipView and WarrantyView
    #   from core.reads.customer(customer_id) (cases.md §1.2), not from this repository.
```

Limits: TTL 600 s, 3 tries, 3 sends come from `Limits.identity: IdentityLimits` in AEA-01's `policy/limits.py` (MC-22
owner; code-design :307), passed by the container; `services/identity.py` holds no second literal.
After a reset, `identity_codes` and `demo_inbox` are cleared (cases.md §1.3) while `_held` may still hold digits for
the cleared rows: they are unreachable (the inbox reads `demo_inbox`; ids are AUTOINCREMENT, never reused) and are
pruned at expiry.

Consumers: AEA-02 (types), AEA-10 (DDL, `reads.identity_state`, reset clears `identity_threads` too), AEA-27 (service,
repos), AEA-36 (identity node), AEA-43 (CON-6 route), AEA-03 (two texts), AEA-24 (eval reads the code from CON-6).

---

## 6. R-44 quick checks (AEA-35, AEA-39; GRT-8)

**In practice.** Turn 1 of WP-3-style chat: "my AC stopped cooling, can someone come out?" The plan opens a new
scheduling `BOOK_NEW` task; no safety gate fired and the classifier raised nothing. The act node sets
`offer_quick_checks=True`. Before the loop, the runner makes one code-built `kb_search` call through the dispatcher
(query = the task's masked text), keeps only passages from `faq/troubleshooting_before_you_call.md`, and the scheduling
builder puts them in `SchedulingResult.quick_checks`. The `lookup_log` row records the passages. Nothing is offered if
no troubleshooting passage clears the floor.

**Rule (act node, AEA-39)** [Decided §7, engineering; Source: R-44, FLOW-5 order "Non-urgent repair? → offer; urgent or
safety → FLOW-2", then the urgency questions]: `offer_quick_checks = True` only when all hold:
1. the task is `scheduling` with intent `BOOK_NEW` and `resumes_task_id is None` (the turn the booking task opens, so
   it is offered once);
2. `details.service_type` is `hvac_repair`, `plumbing` or unknown (not `hvac_tune_up`, not `estimate`);
3. `gate.kind == FREE_TEXT` and not `danger.raised` (at offer time "urgent" means the safety and danger paths; the
   urgency questions come after the offer in FLOW-5). So graph-nodes §6's code-built urgent booking after a burning
   "no" (gate `BURNING_ANSWER`, GRN-6) never offers quick checks.

**Runner** (AEA-35): the call is a `ToolCall(id="qc-<turn_id>", name="kb_search",
args={"query": task.customer_text[:300]})` (name and `KbSearchArgs.query` ≤ 300: data.md §4) dispatched with `kinds={kb_search}`; it is not a model tool round and is
not counted against `brakes.tool_rounds`. `KnowledgeResult.quick_checks` keeps DO-4's meaning (AEA-35 AC-8).

Consumers: AEA-35, AEA-39; AEA-38 copies the passage ids into `TurnFacts.quick_checks` and the passages into
`TurnFacts.passages` (graph-nodes).

---

## Cross-topic assumptions

| # | Owner | What this part assumes | If the owner decides otherwise |
|---|---|---|---|
| C-1 | graph-core (GRC-6, AEA-21) | `GraphDeps` gains `specialists: SpecialistRunner`; no dispatcher field. **Settled:** graph-core §4 defers to this file's names | GRT-6 reopens |
| C-2 | graph-core (GRC-10) | `TurnInput.message_id: int` (written); `scope_for` reads it | — (already written) |
| C-3 | cases (AEA-13) | `policy/booking.py` gains `SCHEDULE_FEES` (§4); `fee_note` reads it. **Settled:** cases.md §2 lists it and points here | AEA-27 keeps the table in `account.py` with the same source line |
| C-4 | cases (AEA-10, CAS-3) | `40_identity.sql` as §5, incl. `identity_threads`; `reads.identity_state` derives as §5; `reset.clear_demo_tables` clears `identity_threads` beside `identity_codes`, `demo_inbox`. **Settled:** cases.md §1.1 cites §5 and §1.3's *Cleared* list names all three | AEA-27 records `blocked-on AEA-10` for the missing column/table |
| C-5 | data (AEA-03 texts) | `INBOX_CODE_BODY` = SCR-2's "Your Meridian Home Comfort verification code is {digits}. It expires in 10 minutes."; `INBOX_CODE_GONE` = "This code is no longer shown. Ask the chat for a new code if you need one." [proposal wording]. **Settled:** data.md §2 `identity` group (`identity.inbox_code_body`, `identity.inbox_code_gone`; placeholder `digits`, DAT-29) | AEA-43 uses whatever ids AEA-03 defines |
| C-6 | data (AEA-33) | `knowledge_tools(retrieval)` returns the `KB_SEARCH` def bound to the index (data.md §4, cross-topic 5: "the executor-registry call" is this factory) | — |
| C-7 | cases (AEA-28) | `scheduling_tools(scheduling)`; executors map `Refused.code` to the same-named `ToolErrorCode` (two values added in §1) | — |
| C-8 | models (AEA-17/20) | `ToolSchema`, `ToolCall` live in `ports/models.py`; `ToolCallingModel.start/append` unchanged; the gateway unchanged | GRT-6 reopens if the gateway must own message building |
| C-9 | AEA-01 `policy/limits.py` (owner per MC-22) | the one frozen `Limits` has `brakes.tool_rounds` (2) and `identity: IdentityLimits(code_ttl_s=600, tries=3, max_sends=3)` (code-design :307 names `Brakes`, `IdentityLimits`; MC-22 adds `spend`, `web` beside them) | AEA-27/35 read whatever field names AEA-01 declares |
| C-10 | web (AEA-43 CON-6) | the route unwraps `InboxMessage.code` only in the response serialiser and renders `body` per §5 | — |
| C-11 | graph-nodes (AEA-38, compose) | `TurnFacts.quick_checks` and `.passages` filled from `SchedulingResult.quick_checks`; recommended: compose sends `QuickChecksBlock.checks` on the offer turn so "Show the checks" opens inline without another turn | compose may re-read on the `show_checks` choice instead |
| C-12 | AEA-08 (docs reconcile) | DO-4 §14's "cap reached" and system design §10's "failed code" are removed from the `NOT_VERIFIED` grouping (§5) | — (the UX-3 contracts win either way) |
