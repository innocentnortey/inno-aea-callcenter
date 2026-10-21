# Graph evidence sweep: needs-decision items in AEA-02, 05, 12, 15, 21, 22, 27, 34, 35, 36, 37, 38, 39, 51

Scope: every `needs-decision` item in `docs/plans/tickets/AEA-NN.md`, grepped against the source set (internal-components, code-design, system-design, hard-problems, observability-contract, PRD, interview, worked-pairs, SP-1 spike, research note, UX structure docs, UI_CONTRACTS, OpenAPI). Quotes are verbatim, max 4 lines, `path:line`. Nothing here decides an item.

Notes on the sweep:
- AEA-05 has no `needs-decision` line in its ticket file, so it has no items here.
- Item 18 and item 36 are the same question (`run_specialist` signature). Decide once.
- Items 21, 25, 29, 30, 35 are the same question about DO-6 records for DO-1 §8.2 signals.
- Item 24 and item 28 are the same question (CheckEvent kinds).
- Item 37 (ND-51a) is the only ND item in the set.
- "Searched" lists the keywords grepped. Where a source is only partly on point, the quote is still given.

---

## AEA-02-1: UnitOfWork repository types

Ticket: `docs/plans/tickets/AEA-02.md:63-66`
> `needs-decision: how ports/runtime.py types UnitOfWork's seven repository attributes while their classes do not exist yet.` DO-4 §13 types them against `adapters/sqlite/repos_*.py` under `TYPE_CHECKING`, assuming A0 creates those files in wave 0; the slice plan gives them to AEA-10 in wave 1, so this ticket's type check cannot resolve them.

Quotes:
- `docs/design/contracts/internal-components.md:897-900`: "Repositories are CONCRETE classes in adapters/sqlite/repos_*.py, with no Protocols of their own (review S-6: / one implementation, temp-SQLite tests). Each file is owned by the area that writes its tables (code-design §8). / A0 creates all seven repo classes in wave 0 (the six per-area ones as empty stubs with a constructor) and / SqliteUnitOfWork constructs all seven; the attribute types below are imported under TYPE_CHECKING, so the port"
- `docs/design/code-design.md:585`: "| **0** | **A0 Foundation** | `config.py`, `domain/*`, `policy/{texts,limits}.py`, `privacy/redact.py`, `ports/*`, `adapters/sqlite/{db,migrate,repos_core}.py`, **empty class stubs of `repos_{spend,i" (cut by the table cell; the stub list continues on the same line)

---

## AEA-02-2: Where the Promise text check lives

Ticket: `docs/plans/tickets/AEA-02.md:67-70`
> `needs-decision: where the Promise text check lives.` DO-4 §7 puts a validator on the domain `Promise` that rejects any text not in `PROMISE_TABLE`, but that table is `policy/handoff.py` (AEA-14, wave 1), and `domain` may import only pydantic and other domain modules (DO-3 §4.1).

Quotes:
- `docs/design/contracts/internal-components.md:476-477`: "class Promise(MeridianModel):" / "\"\"\"Only policy/handoff.py (A6) constructs it. The validator rejects any `text` not in PROMISE_TABLE (R-26).\"\"\""
- `docs/design/contracts/internal-components.md:80`: "    promise: Promise                                 # §7; from the policy table"
- `docs/design/hard-problems.md:80`: "...booking rules in 100% of writes; promise text matching the table in 100% of cases."
- The DO-3 §4.1 import rule ("domain may import only pydantic and other domain modules"): no source found (searched: "imports only", "may import", "pydantic and other", "§4.1" in the source set).

---

## AEA-12-1: AI_PAUSED before SAFETY (paused + safety combination)

Ticket: `docs/plans/tickets/AEA-12.md:108-113`
> 1. DO-4 §3's order puts `AI_PAUSED` before `SAFETY`, while R-5 says the safety check "runs first on every turn". When a representative owns the chat and the customer types "CO alarm", does the AI send the safety instruction, or does the message only go to the representative?

Quotes:
- `docs/design/contracts/internal-components.md:212`: "def decide_gate(intake: Intake, flags: GateFlags) -> GateDecision: ...   # pure; order: paused → safety → burning → danger words → person → code → card → free text"
- `docs/prd/inno-aea-callcenter-prd.md:153`: "| R-5 | A deterministic safety check runs **first on every turn**. Gas or rotten-egg smell, CO alarm, sparks/smoke/flames, or burning smell with tripped breakers → the KB instruction in the same turn, before identity, lookup, queue or case"
- `docs/prd/inno-aea-callcenter-prd.md:351`: "  - Code gates first (safety, burning, danger, person, AI paused)."
- `docs/design/code-design.md:466-467`: "  G -->|ai_paused| CO[compose]" / "  G -->|safety · burning_ask · burning_answer · danger_rule| SF[safety]"

---

## AEA-12-2: GateFlags fields

Ticket: `docs/plans/tickets/AEA-12.md:114-116`
> 2. `decide_gate(intake, flags: GateFlags)` names a `GateFlags` type that DO-4 does not define. Which fields does it carry (controller, an open task for `CARD_CHOICE`, identity `code_sent`, a pending burning-smell question)?

Quotes:
- `docs/design/contracts/internal-components.md:212`: "def decide_gate(intake: Intake, flags: GateFlags) -> GateDecision: ..."
- `docs/design/contracts/internal-components.md:214-216` (nearest related type, not `GateFlags`): "class StateFlags(MeridianModel):                      # the ONLY state the planner and classifier see: flags, never values" / "    verified: bool" / "    open_task: Literal[\"none\", \"knowledge\", \"account\", \"scheduling\"]"
- A `class GateFlags` definition: no source found (searched: "GateFlags", "class GateFlags", "decide_gate").

---

## AEA-12-3: Reading BURNING_ANSWER (yes / no / unsure) from the reply

Ticket: `docs/plans/tickets/AEA-12.md:117-119`
> 3. How `BURNING_ANSWER` and its `yes` / `no` / `unsure` value are read from the customer's reply to R-7's question (`RuleMatches` has no answer field).

Quotes:
- `docs/design/contracts/internal-components.md:200`: "    AI_PAUSED = \"ai_paused\"; SAFETY = \"safety\"; BURNING_ASK = \"burning_ask\"; BURNING_ANSWER = \"burning_answer\""
- `docs/design/contracts/internal-components.md:207`: "    burning_answer: Literal[\"yes\", \"no\", \"unsure\"] | None = None"
- `docs/design/contracts/internal-components.md:177`: "class RuleMatches(MeridianModel):                     # gates/rules.py; typo-tolerant (R-5, R-47)" (the field list after this line was not re-read to confirm the absence of an answer field)
- `docs/prd/inno-aea-callcenter-prd.md:155`: "| R-7 | Burning smell with no breaker information: ask whether breakers have **already** tripped and whether there is smoke, sparks or flames (never ask them to check). If yes → R-5. If unclear → a conditional safety instruction, the emergency number a"

---

## AEA-15-1: "Done" names no ActionKind

Ticket: `docs/plans/tickets/AEA-15.md:108-111`
> 1. "Done" names no action: which `ActionKind` (if any) backs it, so that "Done, your visit is booked" can pass?

Quotes:
- `docs/design/contracts/internal-components.md:54-56`: "class ActionKind(StrEnum):" / "    BOOKED = \"booked\"; MOVED = \"moved\"; CANCELLED = \"cancelled\"" / "    CHANGE_REQUEST_SENT = \"change_request_sent\"; CASE_OPENED = \"case_opened\""
- `docs/design/hard-problems.md:264`: "reference (WP-8). **Never** \"Done, auto-renew is off\", which is what the human agent said."

---

## AEA-15-2: Who builds CheckEvent from CheckResult

Ticket: `docs/plans/tickets/AEA-15.md:112`
> 2. Who builds the `CheckEvent` from a `CheckResult`: a function here, or the reply node (AEA-38)?

Quotes:
- `docs/design/contracts/internal-components.md:654-660`: "class CheckResult(MeridianModel):" / "    text: str ..." / "class CheckEvent(MeridianModel):                      # DO-6 `check_event`" / "    check: Literal[\"completion\", \"fact\", \"brief_fact\", \"brief_quote\"]"
- `docs/design/contracts/internal-components.md:668`: "def check_completion(text: str, settled: Settled) -> CheckResult: ..."
- A builder function that maps `CheckResult` to `CheckEvent`: no source found (searched: "CheckEvent", "CheckResult", "check_event", "build").

---

## AEA-15-3: Brief quote check location (`quote_not_found`, `brief_quote`)

Ticket: `docs/plans/tickets/AEA-15.md:113-115`
> 3. The brief's quote check (`Removal` reason `quote_not_found`, `CheckEvent` `brief_quote`: every `Quote` an exact substring of its message, DO-4 §7, §10) is not among `checks.py`'s DO-4 functions. Does it live here or in AEA-38?

Quotes:
- `docs/design/contracts/internal-components.md:652`: "    reason: Literal[\"no_completed_action\", \"not_in_evidence\", \"quote_not_found\"]"
- `docs/design/contracts/internal-components.md:660`: "    check: Literal[\"completion\", \"fact\", \"brief_fact\", \"brief_quote\"]"
- `docs/design/contracts/internal-components.md:563`: "                          check: CheckResult | None) -> Brief: ...   # None → headings 2,4,7 \"not generated\""
- Which module owns the quote check: no source found beyond the above (searched: "quote_not_found", "brief_quote", "checks.py").

---

## AEA-21-1: Who emits node spans and how they reach the trace

Ticket: `docs/plans/tickets/AEA-21.md:133-134`
> - needs-decision: who emits node spans and how they reach the trace — `GraphDeps` has no `TraceSink` and `TurnContext` no `SpanHandle` (DO-4 §2), yet DO-6 rule 18 wants each node timed under the turn's trace. Shared with AEA-20.

Quotes:
- `docs/design/observability-contract.md:65`: "- Inside a turn, each node, model call and tool call is a timed span in the trace (rule 18), so a slow turn can be"
- `docs/design/contracts/internal-components.md:887-890`: "class TraceSink(Protocol):" / "    def turn(self, ids: TurnIds) -> ContextManager[SpanHandle]:" / "    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ..." / "    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ..."
- `docs/design/contracts/internal-components.md:164-167`: "class GraphDeps:                                      # constructor injection into build_graph(); nine fields (review C-4)" / "    gateway: ModelGateway; retrieval: RetrievalIndex; uow: UnitOfWorkFactory" / "    identity: IdentityService; scheduling: SchedulingService; handoff: HandoffService" (the nine-field list does not include `trace`)

---

## AEA-21-2: Halt routing (router to `escalation` or straight to `compose`)

Ticket: `docs/plans/tickets/AEA-21.md:135-137`
> - needs-decision: when a specialist sets `halt` (a brake), does the router go to `escalation` so DO-4 §6 rule 6 opens the `ai_failure` P3 case, or straight to `compose` as DO-3 §5.4 says ("every router sends a state with `halt` set straight to `compose`")? The two sources disagree; DO-4 §11 says a brake gives "a handoff reply with what is settled".

Quotes:
- `docs/design/contracts/internal-components.md:458` (DO-4 §6 rule 6): "| 6 | `halt` set, or a specialist `failed` twice in a row | escalate, `degraded=True` | `ai_failure` → P3 (PRD §5 *Reliability*) |"
- `docs/design/code-design.md:458` (DO-3 table row): "| `halt` | any node, when the budget or a brake stops it (first wins) | routers |"
- `docs/design/contracts/internal-components.md:751`: "| A brake fired | `degraded_handoff` / `brake` | Handoff reply with what is settled | `brake_fired` (with the b"
- The DO-3 §5.4 sentence "every router sends a state with `halt` set straight to `compose`": no source found (searched: "every router", "straight to", "halt set"). The DO-3 §5.4 graph skeleton at `code-design.md:463-472` has no `halt` edge.

---

## AEA-22-1: Dispatcher public signature and ToolDef registration

Ticket: `docs/plans/tickets/AEA-22.md:127-129`
> - needs-decision: the dispatcher's public signature (what the runner passes per step and gets back) and how the three executor areas register their `ToolDef`s (a registry call, or a mapping injected by the container) — neither is in DO-4 §5, and AEA-27/28/33/35 build against it in wave 2. AC-9 records the choice in DO-4 before they start.

Quotes:
- `docs/design/code-design.md:372`: "| `agent/tools/dispatch.py` | Generate tool schemas from `ToolDef`; validate, scope-check, execute and log every call. | `domain/tools.py`, executors in `agent/tools/{knowledge,account,scheduling}.py` |"
- `docs/design/contracts/internal-components.md:336`: "class ToolDef(MeridianModel):"
- `docs/design/code-design.md:607`: "| `web/container.py` | every area that adds an adapter or service | A0 writes one `register_<area>()` stub per area in wave 0; each area edits only its own function's hunk (review C-3) |" (container registration, not `ToolDef` registration)
- A dispatcher signature (runner input and output) and a `ToolDef` registry call: no source found (searched: "dispatch", "ToolDef", "register", "registry").

---

## AEA-27-1: Raw verification code in the inbox (CON-6)

Ticket: `docs/plans/tickets/AEA-27.md:146-149`
> 1. CON-6 must return the code (OpenAPI `InboxMessage.code`), but UI_CONTRACTS ("It is stored hashed") and DO-6 ("Verification codes … Never raw: hash and expiry only") forbid a raw code in the database. How does the inbox show it (for example: an in-memory store per login session, lost on restart; or the raw code in `demo_inbox` as a stated demo exception)?

Quotes:
- `docs/ux/03-structure/UI_CONTRACTS.md:37`: "The code (D3) appears in exactly two places: typed by the customer in a CON-2 `code` payload, and in the CON-6 demo inbox response. It is stored hashed."
- `docs/ux/03-structure/ui-contracts.openapi.yaml:10222-10224`: "        code:" / "          type: string" / "          description: \"DATA CLASS: secret. This is the ONLY response that carries a code.\""
- `docs/ux/03-structure/ui-contracts.openapi.yaml:2983`: "      x-data-class: \"SECRET: the code appears here and nowhere else. Masked recipient only. Never in model context, logs or traces. Stored hashed.\""
- `docs/design/observability-contract.md:184`: "| Verification codes (R-15) | Never raw: hash and expiry only | Never | Never | Never | Never |"
- `docs/design/code-design.md:215`: "│   ├── sqlite/repos_identity.py                 identity_codes, demo_inbox, invoices (read)                A4    1"
- An in-memory or session-scoped inbox option, or a stated demo exception: no source found (searched: "demo exception", "in-memory", "session", "demo_inbox", "login session").

---

## AEA-27-2: Which cap produces NotVerified (cap reached)

Ticket: `docs/plans/tickets/AEA-27.md:150-152`
> 2. DO-4 §14 lists "cap reached" among the causes of the identical `NotVerified`, while `send_code` also returns `CodeCapReached` (UI: `CODE_CAP_REACHED`, same sentence and card as `CODE_LOCKED`). Which cap does `NotVerified` cover?

Quotes:
- `docs/design/contracts/internal-components.md:959`: "    def send_code(self, thread_id: ThreadId, demo_session: str, now: datetime) -> CodeSent | NotVerified | CodeCapReached: ..."
- `docs/design/contracts/internal-components.md:723`: "    CODE_LOCKED = \"CODE_LOCKED\"; CODE_CAP_REACHED = \"CODE_CAP_REACHED\"; NOT_VERIFIED = \"NOT_VERIFIED\""
- The DO-4 §14 text listing "cap reached" as a cause of `NotVerified`: no source found (searched: "cap reached", "NotVerified", "CodeCapReached").

---

## AEA-27-3: Source of the $149 fee-schedule value for the staff note

Ticket: `docs/plans/tickets/AEA-27.md:153-155`
> 3. Where `account.py` gets the fee-schedule value ($149) it compares an invoice line against for the staff note: the fee schedule is a KB file (AEA-16/33); `policy/booking.py` (AEA-13) holds fee notes by tier.

Quotes:
- `docs/design/hard-problems.md:194`: "3. **Records disagree with policy.** INV-204411 bills $144 after-hours; the schedule says $149 (audit D-8). Your WP-2"
- `docs/prd/inno-aea-callcenter-prd.md:213` (R-17): "...INV-204411's $144 vs $149 is a staff note, not a customer verdict..."
- `docs/design/code-design.md:309`: "| `policy/booking.py` (A5) | Map a city or ZIP to a zone, decide fee-bearing changes, quote fees by tier. | `zone_for`, `hours_be"
- The question of whether `account.py` reads the KB file or `policy/booking.py`: no source found (searched: "fee schedule", "$149", "policy/booking", "account.py").

---

## AEA-27-4: DO-4 §14 identity types without fields (Locator, Located, NotVerified, CodeSent, CodeCapReached, Verified, CodeWrong, CodeExpired, CodeLocked, InboxMessage)

Ticket: `docs/plans/tickets/AEA-27.md:156-158`
> 4. DO-4 §14 names `Locator`, `Located`, `NotVerified`, `CodeSent`, `CodeCapReached`, `Verified`, `CodeWrong`, `CodeExpired`, `CodeLocked` and `InboxMessage` without fields; AEA-02 must define them, or this plan records `blocked-on AEA-02`.

Quotes:
- `docs/design/contracts/internal-components.md:958`: "    def locate(self, thread_id: ThreadId, locator: Locator, now: datetime) -> Located | NotVerified: ..."
- `docs/design/contracts/internal-components.md:960`: "    def verify(self, ids: TurnIds, digits: SecretStr, now: datetime) -> Verified | CodeWrong | CodeExpired | CodeLocked: ..."
- `docs/design/contracts/internal-components.md:962`: "    def inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]: ..."
- Class definitions for these names: no source found (searched: "class Locator", "class Located", "class NotVerified", "class CodeSent", "class Verified", "class CodeWrong", "class CodeCapReached").

---

## AEA-34-1: How the node reads IdentityState from the database

Ticket: `docs/plans/tickets/AEA-34.md:82-86`
> 1. `needs-decision:` how the node reads `IdentityState` from the database. Its tables (`identity_codes`, `40_identity.sql`) are AEA-27's, in the same wave, and DO-4 §14 `IdentityService` has no read-state method (only `locate`, `send_code`, `verify`, `inbox`); `GraphDeps.identity` is that service. Recommended: add `IdentityService.state(thread_id, now) -> IdentityState` to DO-4 §14 (AEA-02 follow-up) and call it through `GraphDeps`; otherwise record `blocked-on AEA-27` for AC-4.

Quotes:
- `docs/design/contracts/internal-components.md:957-962`: "class IdentityService:                               # each method opens and commits its own transaction (review S-6)" / "    def locate(...)" / "    def send_code(...)" / "    def verify(...)" / "    def inbox(...)" (no read-state method in this block)
- `docs/design/contracts/internal-components.md:98-99`: "class IdentityState(MeridianModel):" / "    status: Literal[\"not_checked\", \"located\", \"code_sent\", \"verified\", \"not_verified\", \"locked\"]"
- `docs/design/code-design.md:215`: "│   ├── sqlite/repos_identity.py                 identity_codes, demo_inbox, invoices (read)                A4    1"
- `docs/design/code-design.md:48`: "3. `agent/nodes/load_context.py` reads every completed action of this thread from the `actions` table and puts them in"

---

## AEA-34-2: Window size for turns (about 10 [A])

Ticket: `docs/plans/tickets/AEA-34.md:87-89`
> 2. `needs-decision (measurement-settled):` the window size, "about 10 [A]" turns (R-45); the planner names it as one constant in `policy/limits.py` (AEA-01's file: a follow-up if absent) or in this node, labelled [A].

Quotes:
- `docs/prd/inno-aea-callcenter-prd.md:147`: "...Turns beyond a window (about 10 [A]) are condensed into a typed summary copied..."
- `docs/design/code-design.md:307`: "| `policy/limits.py` | Hold every shared numeric limit in one place. | `TurnLimits` (60 s [Decided SDQ-1], role caps), `Admission"
- A constant for the window in `policy/limits.py`: no source found in the set (searched: "window size", "policy/limits", "about 10").

---

## AEA-35-1: run_specialist has no gateway, dispatcher or ToolCallScope inputs; ToolCallingModel start/append

Ticket: `docs/plans/tickets/AEA-35.md:139-143` (same question as AEA-39-2, item AEA-39-2 below)
> 1. DO-4 §5 `run_specialist(spec, task, ctx)` carries no gateway, no dispatcher and none of `ToolCallScope`'s inputs (the verified `customer_id`, `shown_slot_ids`, `message_id`), and `GraphDeps` (§2) has no runner field; also `ModelGateway` (§12) exposes only `tool_step`, while the loop needs the `ToolCallingModel` port's `start` and `append` to build and extend `ProviderMessages`. Where do these come from?

Quotes:
- `docs/design/contracts/internal-components.md:417`: "def run_specialist(spec: SpecialistSpec, task: SpecialistTask, ctx: TurnContext) -> SpecialistResult: ..."
- `docs/design/contracts/internal-components.md:315`: "    message_id: int                                   # the customer message that led to this call (lookup log)"
- `docs/design/contracts/internal-components.md:783`: "    messages: ProviderMessages                        # opaque, owned by the adapter (keeps thinking blocks intact)"
- `docs/design/code-design.md:322`: "| `ToolCallingModel` | The specialist loop; `auto` + strict tools, never forced `tool_choice` (research §1) | `AnthropicAdapter`, test fake |"
- `ModelGateway` with `tool_step` and `ToolCallingModel` `start` / `append`: "tool_step" not found in any source (searched: "tool_step", "ModelGateway").

---

## AEA-35-2: Knowledge report with zero valid points while passages were returned

Ticket: `docs/plans/tickets/AEA-35.md:141-143`
> 2. A knowledge report with zero valid points while passages were returned: `answered` from the passages (SP-1 build step 8.4 fallback) or `no_current_source`?

Quotes:
- `docs/prd/inno-aea-callcenter-prd.md:167`: "| R-13 | Answers come only from retrieved current text or tool results. No firm repair prices"
- `docs/prd/inno-aea-callcenter-prd.md:176`: "| Customers ask about | Answered from (current source) | Never from (excluded, R-10) | DB fields used |"
- `no_current_source`, "zero valid points", SP-1 "build step 8.4" fallback: no source found (searched: "no_current_source", "zero valid", "no valid point", "8.4", "fallback" in `docs/analysis/spikes/SP-1*.md`; the SP-1 hit at line 136 concerns latency, not this rule).

---

## AEA-35-3: R-44 quick checks: which specialist offers them, and from what

Ticket: `docs/plans/tickets/AEA-35.md:63` and `:143-145`
> 3. R-44 quick checks: DO-4 puts them only on `KnowledgeResult`, but a booking turn (WP-3) may run no knowledge task, and no slice carries an urgency flag ("skipped for urgent and safety cases"). Which specialist offers them, and from what?

Quotes:
- `docs/design/contracts/internal-components.md:368`: "    quick_checks: tuple[PassageId, ...] = ()          # R-44, offered never required"
- `docs/design/contracts/internal-components.md:591`: "    quick_checks: tuple[PassageId, ...] = ()"
- `docs/prd/inno-aea-callcenter-prd.md:146`: "| R-44 | Before booking a non-urgent repair, the KB's quick checks may be **offered**: very optional, never required, skipped for urgent and safety cases. A call counts as resolved by a check only if"
- `docs/ux/03-structure/IA.md:74`: "| On demand | **Quick checks list** (R-44), offered once with \"Skip\" as the first-class action (CON-2) | Very optional; never blocks booking | the offer line and \"Skip\" are visible; the list opens on tap |"
- Which specialist offers them on a WP-3 booking turn: no source found beyond the above (searched: "quick_checks", "R-44", "quick check").

---

## AEA-35-4: DO-6 has no record for brake_fired / specialist_failed

Ticket: `docs/plans/tickets/AEA-35.md:104-105`
> `needs-decision`: DO-6 names no record for these DO-1 §8.2 signals (see the list below).

Quotes:
- `docs/design/contracts/internal-components.md:751`: "| A brake fired | `degraded_handoff` / `brake` | Handoff reply with what is settled | `brake_fired` (with the b"
- `docs/design/observability-contract.md:54`: "| `turn` | `degrade_reason` (only with `degraded_handoff`) | `model_error`, `tool_error`, `timeout`, `brake`, `spend_cap`, `rate_limit` |"
- `docs/design/observability-contract.md:114`: "| `check_event` | which gate or check fired (code gate, R-46 completion or fact check, R-47 classifier raise, brake), its input IDs and result | Gates and checks |"
- A DO-6 record that carries `brake_fired` or `specialist_failed` as a named record: no source found (searched: "brake_fired", "specialist_failed").

---

## AEA-36-1: How Intake reaches the gates node

Ticket: `docs/plans/tickets/AEA-36.md:128-132`
> 1. How `Intake` reaches the gates node: DO-4 §14 has `TurnService` run intake (step 4), but state's `TurnInput.kind` lacks `"form"`, and `Intake.code_digits` / `FormValues.phone` are `SecretStr` values that must never be in state. Carrier: a per-turn field on `TurnContext` (not checkpointed), or verification in `TurnService` before `run_graph`?

Quotes:
- `docs/design/contracts/internal-components.md:947`: "    # 4 intake + STORE redaction; customer message row   5 run_graph(input, context)  (an injected callable, so A8"
- `docs/design/contracts/internal-components.md:190-191`: "class Intake(MeridianModel):                          # gates/gate.py parse_intake, before anything stores the text" / "    kind: Literal[\"text\", \"choice\", \"code\", \"form\"]"
- `docs/design/contracts/internal-components.md:195`: "    form: FormValues | None                           # only for kind=\"form\"; routed by code (LOCATE or CARD_CHOICE), no model"
- `docs/design/contracts/internal-components.md:960`: "    def verify(self, ids: TurnIds, digits: SecretStr, now: datetime) -> Verified | CodeWrong | CodeExpired | CodeLocked: ..."

---

## AEA-36-2: R-7 "both ruled out" → urgent booking plus priority case

Ticket: `docs/plans/tickets/AEA-36.md:131-133`
> 2. R-7's "both ruled out → offer the earliest booking, marked urgent, plus a priority case" (consolidated §9.2 step 4): the skeleton (DO-3 §5.4) sends every `burning_answer` to `safety → compose`, with no edge to the specialists, and no source names that case's priority.

Quotes:
- `docs/prd/inno-aea-callcenter-prd.md:155`: "...If yes → R-5. If unclear → a conditional safety instruction, the emergency number and a P1 case. If both are ruled out → an urgent booking plus a priority case | [Decided] D2; consolidated §9.2 | ..."
- `docs/design/code-design.md:467`: "  G -->|safety · burning_ask · burning_answer · danger_rule| SF[safety]"
- `docs/design/hard-problems.md:141`: "5. **Over-firing has a cost too.** Your WP-3 answer narrowed the urgent path because firing on every no-cooling report"
- The "consolidated §9.2" text and a priority for the both-ruled-out case: no source found (searched: "consolidated §9.2", "§9.2", "ruled out", "both ruled").

---

## AEA-36-3 / AEA-37-3: CheckEvent kinds for gate and classifier-raise events

Tickets: `docs/plans/tickets/AEA-36.md:134` ("3. `CheckEvent` kinds for gate and classifier events") and `docs/plans/tickets/AEA-36.md:93-95` ("DO-4 §10 `CheckEvent.check` has only `completion`, `fact`, `brief_fact`, `brief_quote`; DO-6 also expects gate and classifier-raise check events."). AEA-37's classifier-raise kind is the same item (AEA-37-3 below).

Quotes:
- `docs/design/contracts/internal-components.md:660`: "    check: Literal[\"completion\", \"fact\", \"brief_fact\", \"brief_quote\"]"
- `docs/design/observability-contract.md:114`: "| `check_event` | which gate or check fired (code gate, R-46 completion or fact check, R-47 classifier raise, brake), its input IDs and result | Gates and checks |"
- `docs/design/code-design.md:652`: "| C-2 | Readiness SD-6.3 note vs R-47 and DO-1 §8.2 | Readiness: a Jev classifier failure \"must fail toward raise or hand off\"; R-47 [Decided]: \"the rules stand\" | Follows R-47; records `classifier_fallback`. Raised for the read"

---

## AEA-36-4: DO-6 has no record for safety_reply_sent / case_write_failed

Ticket: `docs/plans/tickets/AEA-36.md:92-95`
> ...signals `safety_reply_sent` and `case_write_failed` (DO-1 §8.2). `needs-decision`: DO-4 §10 `CheckEvent.check` has only `completion`, `fact`, `brief_fact`, `brief_quote`; DO-6 also expects gate and classifier-raise check events.

Quotes:
- `docs/design/contracts/internal-components.md:515`: "    # Safety path: on a failed write, retry once; the instruction is sent either way (DO-1 §8.2)."
- `docs/design/observability-contract.md:52-53`: "| `turn` | `gate_result` | `clear`, `safety`, `burning_unclear`, `danger`, `person_requested`, `ai_paused` |" / "| `turn` | `outcome` | `answered` (just talk), `acted` (a specialist ran and finished), `safety_reply`, `handed_off`, `to_staff` ..."
- `safety_reply_sent` and `case_write_failed` as named DO-6 records: no source found (searched: "safety_reply_sent", "case_write_failed").

---

## AEA-37-1: Both planners fail and neither a rule nor the open task gives a plan

Ticket: `docs/plans/tickets/AEA-37.md:127-131`
> 1. Both planners fail and neither a rule nor the open task gives a plan: DO-1 §8.2 says "a handoff reply"; DO-4 §4 says the turn "still runs on rules and the open task" (which is `talk`). Which?

Quotes:
- `docs/design/contracts/internal-components.md:246`: "    choices: PlannerChoices | None                    # None → the turn still runs on rules and the open task"
- `docs/design/contracts/internal-components.md:282`: "`join_plan` is pure and follows SP-1's measured `normalize` steps: a planner failure never blocks the rules; a policy"
- `docs/design/code-design.md:320`: "| `ChoiceModel` | Jev (planner, classifier) and Sonnet (planner fallback [Decided SDQ-6]) both answer typed choices | `JevAdapter`, `AnthropicAdapter`, test fake |"
- `docs/design/contracts/internal-components.md:751`: "| A brake fired | `degraded_handoff` / `brake` | Handoff reply with what is settled | `brake_fired` (with the b" (the "handoff reply" wording is the DO-1 §8.2 table column; the "both planners fail" row is not in the listed sources)

---

## AEA-37-2: Type of the planner_choices state key

Ticket: `docs/plans/tickets/AEA-37.md:131-134`
> 2. DO-3 §5.2 types the state key as `planner_choices: PlannerChoices | None`, but `join_plan` takes `PlannerOutcome` (with `fallback_used`, `probabilities`, `failure`, which the turn record needs). Which type does the key hold?

Quotes:
- `docs/design/contracts/internal-components.md:236`: "class PlannerChoices(LLMFacing):"
- `docs/design/contracts/internal-components.md:245-246`: "class PlannerOutcome(MeridianModel):" / "    choices: PlannerChoices | None                    # None → the turn still runs on rules and the open task"
- `docs/design/contracts/internal-components.md:278`: "def join_plan(planner: PlannerOutcome | None, danger: DangerAssessment | None,"
- A `planner_choices` state key in DO-3 §5.2: no source found (searched: "planner_choices", "§5.2", "PlannerOutcome").

---

## AEA-37-3: CheckEvent kind for the classifier raise

Ticket: `docs/plans/tickets/AEA-37.md:135`
> 3. `CheckEvent` kind for the classifier raise (see Observability).

Quotes: same as AEA-36-3 (`internal-components.md:660`; `observability-contract.md:114`, "R-47 classifier raise"). The DO-4 `CheckEvent.check` literal has no classifier-raise value.

---

## AEA-37-4: DO-6 has no record for planner_fallback / classifier_fallback

Ticket: `docs/plans/tickets/AEA-37.md:94-96`
> `planner_fallback` and `classifier_fallback` (DO-1 §8.2). `needs-decision`: DO-4 §10 `CheckEvent.check` has no classifier-raise kind, and DO-6 names no record for these signals.

Quotes:
- `docs/design/code-design.md:652`: "| C-2 | Readiness SD-6.3 note vs R-47 and DO-1 §8.2 | ... | Follows R-47; records `classifier_fallback`. Raised for the read"
- `docs/design/code-design.md:320`: "| `ChoiceModel` | Jev (planner, classifier) and Sonnet (planner fallback [Decided SDQ-6]) both answer typed choices | ..."
- `planner_fallback` as a named DO-6 record: no source found (searched: "planner_fallback", "classifier_fallback").

---

## AEA-38-1: Which function rebuilds `settled` from rows

Ticket: `docs/plans/tickets/AEA-38.md:131-135`
> 1. Which function rebuilds `settled` from rows: `load_context` (AEA-34, same wave) owns the DB → `settled` read and has no DO-4 signature. Expose a shared builder (in AEA-10's `repos_core` or `domain`), or make AEA-38 `blocked-on AEA-34`?

Quotes:
- `docs/design/contracts/internal-components.md:84`: "class Settled(MeridianModel):"
- `docs/design/contracts/internal-components.md:647`: "def build_evidence(facts: TurnFacts, settled: Settled, lookups: Sequence[LookupRow],"
- `docs/design/code-design.md:48`: "3. `agent/nodes/load_context.py` reads every completed action of this thread from the `actions` table and puts them in"
- `docs/design/code-design.md:254`: "│   ├── nodes/load_context.py                    settled, controller, identity, chat window from the DB      A7a  2"

---

## AEA-38-2: How the brief is persisted

Ticket: `docs/plans/tickets/AEA-38.md:136-138`
> 2. How the brief is persisted: `CaseService.attach_brief` (DO-4 §13) is not reachable from `GraphDeps`, and `BriefAssembler` returns a `Brief` without storing it.

Quotes:
- `docs/design/contracts/internal-components.md:925`: "    def attach_brief(self, case_ref: CaseRef, brief: Brief) -> None: ..."
- `docs/design/contracts/internal-components.md:560-563`: "class BriefAssembler:" / "...check: CheckResult | None) -> Brief: ...   # None → headings 2,4,7 \"not generated\""
- `docs/design/contracts/internal-components.md:164-167`: "class GraphDeps:" (nine fields; `brief: BriefAssembler` is listed at line 167, `CaseService` is not among them)

---

## AEA-38-3: What increments FailureCounters (failed_answers, corrections, timeouts)

Ticket: `docs/plans/tickets/AEA-38.md:139-141`
> 3. What increments `FailureCounters.failed_answers`, `corrections` and `timeouts` (DO-4 §1 names them; OD-6 uses them; no rule is given, and a timed-out turn goes straight to compose, past `facts`).

Quotes:
- `docs/design/contracts/internal-components.md:120-122`: "class FailureCounters(MeridianModel):" / "    failed_answers: int = 0; tool_failures: int = 0; identity_failures: int = 0" / "    corrections: int = 0; timeouts: int = 0; bookings: int = 0      # OD-6, R-41"
- `docs/design/contracts/internal-components.md:459`: "| 7 | `failed_answers ≥ 2` or `corrections ≥ 2` | offer | — (OD-6 two-attempt rule [A: threshold 2]) |"
- `docs/design/contracts/internal-components.md:743`: "| Deadline reached (60 s, Decided SDQ-1) | `degraded_handoff` / `timeout` | ..." (timeout row)
- An increment rule for these counters: no source found (searched: "increment", "counts toward", "FailureCounters").

---

## AEA-38-4: Responder window per-line character cap

Ticket: `docs/plans/tickets/AEA-38.md:139-141`
> 4. The responder window's per-line character cap (context-management rule 4): R-45 gives "about 10 turns [A]"; no source caps a line (SP-1 used 400 chars for the planner).

Quotes:
- `docs/prd/inno-aea-callcenter-prd.md:147`: "...Turns beyond a window (about 10 [A]) are condensed into a typed summary copied..."
- `docs/design/contracts/internal-components.md:602`: "    settled: SettledForModel                          # labelled \"ALREADY DONE IN THIS CONVERSATION\" (R-45 fix)"
- A per-line character cap for the responder window: no source found (searched: "character cap", "per-line", "context-management rule 4", "10 turns").

---

## AEA-38-5: DO-6 has no record for responder_fallback / brief_failed

Ticket: `docs/plans/tickets/AEA-38.md:98-100`
> ...signals `responder_fallback` and `brief_failed` (DO-1 §8.2), with the responder failure ending the turn `degraded_handoff` / `model_error` (DO-4 §11). `needs-decision`: DO-6 names no record for these signals.

Quotes:
- `docs/design/contracts/internal-components.md:748`: "| Provider rate limit or 5xx/529, retry does not fit | `degraded_handoff` / `model_error` | Specialist: handoff"
- `docs/design/observability-contract.md:54`: "| `turn` | `degrade_reason` (only with `degraded_handoff`) | `model_error`, `tool_error`, `timeout`, `brake`, `spend_cap`, `rate_limit` |"
- `responder_fallback` and `brief_failed` as named DO-6 records: no source found (searched: "responder_fallback", "brief_failed").

---

## AEA-39-1: DO-6 has no record for specialist_failed / brake_fired

Ticket: `docs/plans/tickets/AEA-39.md:94-96`
> ...Signals `specialist_failed` and `brake_fired` (DO-1 §8.2) come from the results it passes on. `needs-decision`: DO-6 names no record for these signals.

Quotes:
- `docs/design/contracts/internal-components.md:751`: "| A brake fired | `degraded_handoff` / `brake` | Handoff reply with what is settled | `brake_fired` (with the b"
- `docs/design/observability-contract.md:54`: "| `turn` | `degrade_reason` (only with `degraded_handoff`) | `model_error`, `tool_error`, `timeout`, `brake`, `spend_cap`, `rate_limit` |"
- Same gap as AEA-35-4 (no DO-6 record named for `brake_fired` / `specialist_failed`; searched: "specialist_failed", "brake_fired").

---

## AEA-39-2: run_specialist has no gateway, dispatcher, ToolCallScope inputs, or runner; TurnInput has no message_id

Ticket: `docs/plans/tickets/AEA-39.md:130-133`
> `needs-decision`: DO-4 §5 `run_specialist(spec, task, ctx)` has no parameter for the gateway, the dispatcher or the `ToolCallScope` inputs (verified `customer_id`, `shown_slot_ids`, `message_id`), and `GraphDeps` has no runner field; `TurnInput` has no `message_id` either. Same item as AEA-35's needs-decision 1; decide once.

Quotes:
- `docs/design/contracts/internal-components.md:417`: "def run_specialist(spec: SpecialistSpec, task: SpecialistTask, ctx: TurnContext) -> SpecialistResult: ..."
- `docs/design/contracts/internal-components.md:124-125`: "class TurnInput(MeridianModel):" (field list at 125-130 was not re-read; grep found no `message_id` in `TurnInput` lines 124-196 itself, only in the lookup-log and `ToolCallScope`-related types at lines 315, 320, 552)
- `docs/design/contracts/internal-components.md:315`: "    message_id: int                                   # the customer message that led to this call (lookup log)"
- Same question as AEA-35-1 (decide once).

---

## AEA-51-1 (ND-51a): DANGER path, one model span allowed before the safety reply?

Ticket: `docs/plans/tickets/AEA-51.md:160-162`
> **ND-51a** `needs-decision:` CAP-2 says "no model span before the safety reply" for both WP-5 and DANGER. DANGER can reach the safety path two ways (DO-3 §5.4): the `danger_rule` gate (no model at all) or the raise-only classifier (one Jev span before the reply). If the rule does not match DANGER's wording, is the classifier's span the one model span allowed before the safety reply (recommended: yes, and no specialist, responder or brief span), or must the `danger_rule` match DANGER so no model runs?

Quotes:
- `docs/design/observability-contract.md:248`: "| CAP-2 | WF-1 with WP-5 (CO alarm) and DANGER | `turn` with `gate_result = safety` or `danger`, `outcome = safety_reply`; P0 or P1 case; no model span before the safety reply | Any identity or lookup step before the instruction |"
- `docs/design/code-design.md:466-471`: "  G -->|ai_paused| CO[compose]" / "  G -->|safety · burning_ask · burning_answer · danger_rule| SF[safety]" / "  G -->|free_text| PL[planner] & DC[danger_classifier]"
- `docs/design/hard-problems.md:91`: "  → Code gates (code: safety, danger, person)  ──→ Safety reply (fixed text, no model) ──→ send"
- `docs/design/hard-problems.md:153`: "| **C. Rules first, then a classifier that can only raise the level** *(recommended)* | The word rules run first and decide on their own when they match. A small, cheap model (the \"smaller model\" in PRD §6.2) then reads the me"
- `docs/design/observability-contract.md:205`: "TypeSafe through OpenRouter (Jev: planner and danger classifier), each after the intake masks."
- Whether the classifier span is the one permitted model span, and whether `danger_rule` must match DANGER's wording: no source found (searched: "danger_rule", "DANGER", "one model span", "raise-only", "no model span").

---

## Gap notes (not needs-decision lines)

These are the other "gap / missing / conflict / disagree" notes in the ticket files. They are ticket-process notes, not open design questions, so they are listed without a decision.

- `docs/plans/tickets/AEA-02.md:134-138`: "Frozen after wave 0: a missing field or method is its own small ticket merged before its dependants (slice plan §3)." and "no guessed fields for unsketched types (list them as `needs-decision`)". Sources: none in the set (refers to `docs/plans/slice-plan.md` §3, not in the source list).
- `docs/plans/tickets/AEA-12.md:101`: "model call, no new word rule (a missing rule goes to AEA-05)." Sources: none in the set.
- `docs/plans/tickets/AEA-21.md:127`: "missing one is a small AEA-03 follow-up); no new state key outside DO-3 §5.2." Sources: none in the set.
- `docs/plans/tickets/AEA-22.md:64`: DO-6 *Missing instrumentation* row. Source: `docs/design/observability-contract.md:209`: "## Missing instrumentation". Not a gap.
- `docs/plans/tickets/AEA-27.md:36`: "The record-vs-policy gap ($144 billed vs the fee schedule's $149, audit D-8) goes to `AccountResult.staff_notes` only". Sources: `docs/design/hard-problems.md:194` and `docs/prd/inno-aea-callcenter-prd.md:213`, cited under AEA-27-3.
- `docs/plans/tickets/AEA-51.md:148`: "Added in 7b (real dependencies missing from the slice-plan row; orchestrator to confirm): AEA-30 ... AEA-19 ... AEA-11". Sources: none in the set (slice plan not in source list).

---

## Count

Items: 37 (AEA-02: 2, AEA-12: 3, AEA-15: 3, AEA-21: 2, AEA-22: 1, AEA-27: 4, AEA-34: 2, AEA-35: 4, AEA-36: 4, AEA-37: 4, AEA-38: 5, AEA-39: 2, AEA-51: 1). Shared questions are listed under each ticket where they appear.
