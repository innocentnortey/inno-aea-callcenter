## [AEA-02] foundation: domain types, ports, typed settings, repository shells

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

> As a **homeowner** mid-booking, I need "what about Monday?" to apply to the visit we were just arranging, so that I
> don't start over every message. (US-17; R-45)

**Example pair 1 (WP-4F, the turn SP-1 got wrong; DO-3 §1).** Input: the `actions` rows of Linda Foster's (fictional,
MHC-10001) thread after turn 3: one `CompletedAction` with `kind = moved`, `records = {appointment, slot, old_slot}`,
`after = {date: 2026-10-19, window: 08:00-12:00, technician: Marta, service_type, fee_line}`, `source = actions_table`.
Expected output: `Settled.has(ActionKind.MOVED)` is true; `Settled.current_visit()` returns a `VisitView` for Monday,
October 19, 08:00-12:00 with Marta, `status = "moved"`, `change_request = None` (graph-core §14); `Settled.only_turn(<turn
4 id>)` holds no action. Turn 4's responder and the *What's settled* panel read this same object, so "Yes, it's moved"
can no longer be contradicted (N-27).

**Example pair 2 (DO-3 S-2).** Input: an environment that configures Jev (`openrouter_jev`) for the responder role.
Expected output: `Settings` validation fails at start-up, naming the field and the rule, before any request is served;
the error holds no secret value.

Every shared type and port, in the homes DO-3 §3 gives, with the shapes of DO-4 §0–§14 **as amended by the Stage 7
addenda** (DO-4 §16: where an addendum and an earlier DO-4 section disagree, the addendum wins). Eleven `domain/` files
(the slice plan row says nine; staff.md §1 adds `staff.py` (MC-2) and graph-tools §5 adds `identity.py`; AEA-08 records
both in DO-3 §4.1):

| File | Contents and the section that defines them |
|---|---|
| `domain/common.py` | `MeridianModel`, `LLMFacing` (DO-4 §0); validated IDs `ThreadId`, `TurnId`, `RequestId` (UUID4), `CustomerId` `MHC-\d{5}`, `InvoiceId` `INV-\d{6}`, `CaseRef` `MHC-C-\d{4}`, `PassageId` `<file path>#<chunk n>`, `EventId` (DO-4 §0); `ApiErrorCode` = the OpenAPI `ApiError.error.code` enum (adds `UNAUTHENTICATED`, `LOGIN_FAILED`, `LOGIN_RATE_LIMITED`; drops `STAFF_AUTH_REQUIRED`; web.md §1, WEB-9); `ToolErrorCode` with 13 values (graph-tools §1, GRT-1); `ProviderFailureKind`, `HaltReason`, `SafeError` (DO-4 §11) |
| `domain/records.py` | `Customer`, `Technician`, `Invoice`, `Passage` (DO-4); `Slot`, `Appointment` (cases.md §4.1, CAS-36); `Zone` = `Literal["north", "central", "south"]` and `FeeNote(service_type, tier, fee_row, amount_cents, waived, line 1–120)` (cases.md §2, CAS-34; R-G-2) |
| `domain/actions.py` | `ActionKind`, `ActionKey`, `CompletedAction`, `OpenCase`, `Settled` with `has`, `current_visit`, `only_turn` (DO-4 §1); `VisitChange`, `VisitView` and the `current_visit()` rule (graph-core §14) |
| `domain/state.py` | `ConversationState` of DO-3 §5.2 with its reducers (`specialist_results` appends; `halt` first writer wins), changed by graph-core §3 (`burning_card_id`), §9 (`planner: PlannerOutcome \| None`, renamed from `planner_choices`) and §11 (`check_events` with the pure reducer `add_turn_events`); the node update `TypedDict`s (`GatesUpdate` keys `gate`, `check_events`, `plan`, `halt`, `burning_card_id`: graph-nodes §9.1, R-G-11) and `SpecialistSend(TypedDict): planned: PlannedTask; state: ConversationState` (graph-nodes §9.1, R-G-12); `Controller`, `IdentityState`, `OpenTask`, `ShownSlot`, `FailureCounters`, `ChatLine` (DO-4 §1) |
| `domain/turn.py` | `TurnIds`, `TurnBudget` (DO-4 §2); `TurnContext` with `span` and `intake`, `CardChoice`, `Intake` (+ `card_id`), `TurnInput` (+ `form` kind, `message_id`, `card_id`, `card_number_seen`), `PlannerTrace`, `TurnTrace`, `TurnRecord`, `GraphOutcome` (+ `closed_every_open_task: bool = False`, graph-core §2, R-G-21 = web R-W-5), `RunGraph` (graph-core §1–§2, GRC-10, GRC-20, GRC-21); the pure `TurnPayload` union (`TextPayload`, `ChoicePayload(CardChoice)`, `CodePayload`, `FormPayload`, discriminated on `kind`, OpenAPI field names and limits; graph-core §2, R-G-20; `web/schemas/chat.py` validates into it, R-W-15); `SpanHandle` (models.md §4, file per graph-core §1); `GateFlags` (graph-core §3, GRC-5); `GateDecision.gate_result()` implementing graph-core §3's table for every kind (R-G-10); `SafetyKind` and `RuleMatches` (DO-4 §3 fields plus `correction: bool`, graph-core §8; `policy_trigger: HandoffReason \| None`; R-G-1); `CheckKind`, `CheckEvent` with its four builders (graph-nodes §1, GRN-2); `SignalName`, `SignalRecord` (graph-nodes §4, GRN-4); the gate, planner, danger, escalation, facts, responder and R-46 check types of DO-4 §3, §4, §6, §8–§10 (the planner `handoff` literal gains `"late_technician"`, graph-core GRC-19 row *cases A-6*; `EscalationInputs` gains `now: datetime`, cases.md §3.4, R-G-15) |
| `domain/specialists.py` | DO-4 §5 types; `SpecialistTask.offer_quick_checks` (graph-tools §2, GRT-8); capture shapes `InvoiceLineView`, `InvoiceView`, `MembershipView`, `WarrantyView`, `StaffNote`, `KnowledgeCapture`, `AccountCapture`, `SchedulingCapture`, and `SchedulingResult.quick_checks` (graph-tools §3); `AppointmentView` and `SchedulingSliceInputs` (graph-tools §3, R-G-19) |
| `domain/tools.py` | `ToolDef`, `ToolCallScope`, `ToolResult`, `ToolError`, `LookupEntry` (DO-4 §5); `LookupRow(LookupEntry)` with `id: int`, `thread_id: ThreadId` (cases.md §1.2, CAS-38; R-G-8); `ToolKind`, `ToolCallRecord` (graph-tools §1, GRT-1) |
| `domain/handoff.py` | `HandoffReason`, `Priority`, `Promise` (**fields only, no text validator**: graph-core §10, GRC-2; AEA-14 is its only constructor), `CaseSummary` (+ `due_at: datetime \| None`, cases A-4), `Brief` and `BRIEF_TITLES`, the brief and handoff types of DO-4 §7 |
| `domain/blocks.py` | the `ReplyBlock` union and `SettledView`; every member takes its fields from the OpenAPI schema of the same name (`HandoffBlock`, `LiveQueuedBlock`, `QuickChecksBlock`, `EmergencyLineBlock`, …; `SettledView` = OpenAPI `Settled`; graph-core §13, web.md §8) |
| `domain/staff.py` | `DemoRole`, `StaffRole`, `StaffPersona`, `STAFF_PERSONAS`, `StaffActor`, `actor_for`, `ASSIGNEE_ROLES`, `LoginSessionId` (the one definition), `LoginSession`, `IssuedSession`, `SessionMissing`, `SessionExpired`, `RoleRefusal`, `SessionInfoData(role, display_name, sees, signed_in_at)` (moved from `services/staff.py`, R-W-1), and the constants `CUSTOMER_SPEAKER_NAME = "Customer"` (R-W-14) and `ROLE_ACTIONS: Mapping[StaffRole, frozenset[str]]` (R-W-13), all as staff.md §1 writes them (MC-1, MC-2, MC-4, MC-5) |
| `domain/identity.py` | `Locator` (with `from_form` and the exactly-one validator), `Located`, `NotVerified` (no fields), `CodeSent`, `CodeCapReached`, `Verified`, `CodeWrong`, `CodeExpired`, `CodeLocked`, `InboxMessage` (graph-tools §5, GRT-5) |

Ports and settings:

- `ports/models.py`: `Role`, `ChoiceField`, `ChoiceRequest`, `ChoiceAnswer`, `StructuredRequest`, `ToolStepRequest`,
  `ToolStep`, the `ChoiceRole` / `StructuredRole` / `ToolRole` aliases (DO-4 §12); `ProviderName`, `ProviderCall`,
  `CallRecord(ProviderCall)` with `from_provider`, `Attempt.record: ProviderCall`, `ProviderMessages(provider:
  ProviderName, model: str, items: tuple[JsonValue, ...])` (models.md §1, MOD-1, MOD-17; R-G-4: graph-tools §2 points
  there), `TokenPrice` (frozen dataclass of four floats; models.md §1, R-G-5); a read-only `provider: ProviderName` attribute on the three model Protocols
  `ChoiceModel`, `StructuredModel`, `ToolCallingModel` (models.md cross-topic 2); `ToolSchema`, `ToolCall` (graph-tools
  §1); `ToolTranscript` (graph-tools §2, GRT-6).
- `ports/runtime.py`: `RetrievalResult`, `IndexInfo`, `RetrievalIndex`, `Clock`, `UnitOfWorkFactory`, `UnitOfWork`
  (DO-4 §13); `ExportStatus` and `TraceSink` with `export_status(turn: SpanHandle)` (models.md §4, MOD-9); re-exports
  `SpanHandle` from `domain/turn.py` (graph-core §1). `UnitOfWork`'s seven attributes are typed under `TYPE_CHECKING`
  against the repository shells below (GRC-1).
- `config.py`: `RoleSpec`, `ModelSettings` (DO-4 §12; the three role maps keyed by `Role`, Jev legal only in the choice
  map; role caps as `RoleSpec.cap_s` code defaults: Jev 3 s, specialist 8 s, responder 12 s, brief 12 s, proposal, DO-1
  §8.1; `RoleSpec.redaction: RedactionProfile`, `JEV` for planner and classifier and `SONNET` for the rest, which the
  gateway applies as `redact(text, spec.redaction)`, models.md §5 rule 4) and **one `Settings` with exactly graph-core §12's fields and env names** (GRC-22; MC-21): `ANTHROPIC_API_KEY`,
  `OPENROUTER_API_KEY`, `models`, `role_model_map()`, the four optional `LANGFUSE_*` values incl.
  `LANGFUSE_PROJECT_ID` and `langfuse_complete()` (no `langfuse_export()`: the container builds AEA-19's
  `LangfuseExportSettings` from the four fields, models.md §7, R-G-6), `MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`,
  `MERIDIAN_SESSION_SECRET`, optional `MERIDIAN_EVAL_KEY`, `MERIDIAN_COOKIE_SECURE`, `MERIDIAN_TRUST_PROXY_HEADERS`,
  `MERIDIAN_WEB_DIST_DIR`, `MERIDIAN_REQUIRE_FRONTEND`, `MERIDIAN_DATA_DIR`, `MERIDIAN_INDEX_DIR`, `issued_db_path` (code
  default, no env name), `MERIDIAN_AGENT_VERSION` (default `"dev"`). Every secret is a `SecretStr`. Built once by the
  container's caller, never a module-level singleton, never touches the database (DO-3 §2.1, §2.4). No numeric limit
  (those are AEA-01's `Limits`). How it reads the environment is the planner's; a new dependency it needs is a one-line
  AEA-01 follow-up (slice plan §3). `.env.example` beside it lists the names above with no values.
- `adapters/sqlite/repos_{core,spend,identity,booking,cases,staff,ops}.py`: seven empty classes `CoreRepos`, `SpendRepo`,
  `IdentityRepos`, `BookingRepos`, `CaseRepos`, `StaffRepos`, `OpsRepos`, each with exactly
  `__init__(self, conn: sqlite3.Connection) -> None` and nothing else (cases.md §1.0, CAS-35; graph-core §1). AEA-10 and
  the owning areas fill the bodies.

**Types DO-4 names that no section sketches** (for example `TurnBegin`, `StreamKey`, `StreamEvent`, `Notice`): a type
serialised to the browser takes its fields from the OpenAPI schema it becomes (read-only; api-con-mapping §1); one with
no sketch, no addendum and no OpenAPI schema is listed in the plan as `blocked-on` the owning topic, never filled by
guess.

**Not here:** `GraphDeps` (`agent/context.py`, AEA-21); `ModelGateway` (AEA-20); `Limits` (`policy/limits.py`, AEA-01);
`LangfuseExportSettings` (`adapters/tracing_langfuse.py`, AEA-19); `EndedThread`, `Cleared` (AEA-10, cases.md §1.2,
CAS-38; `LookupRow` is this ticket's, R-G-8); `LoginSessions` and `StaffAccess` Protocols (`web/deps.py`, AEA-23, MC-1); `RoleCard`,
`ROLE_CARDS` (AEA-44); the scheduling service types `WindowQuery`, `WindowsFound`, `OutOfArea`, `SlotTaken`, `Refused`
(`services/scheduling.py`, AEA-28, CAS-17); the case and demo view types of cases A-2 (`QueueView`, `CaseDetail`, …,
`ResetDone`: an AEA-02 follow-up ticket, graph-core GRC-19 row *cases A-2*); `PROMISE_TABLE` and `promise_for`
(AEA-14); `match_rules` (AEA-05).

**Resolved contract questions (residual pass 2026-10-21, `docs/plans/7b-decisions/residuals-graph.md`; nothing waits):**
1. Resolved R-G-1: `domain/turn.py` defines `SafetyKind` and `RuleMatches` (DO-4 §3 fields plus `correction: bool`,
   graph-core §8), with `policy_trigger: HandoffReason | None`. AEA-05 imports them and owns `match_rules` only.
2. Resolved R-G-2: transcribe `Zone` and `FeeNote` from cases.md §2 (CAS-34) into `domain/records.py`; graph-core §14 no
   longer defines them.
3. Resolved R-G-4: `ProviderMessages(provider: ProviderName, model: str, items: tuple[JsonValue, ...])` from models.md
   §1; graph-tools §2 points there.
4. Resolved R-G-6: no `langfuse_export()` on `Settings`.

Also added by the residual pass (each in the table above): `TokenPrice` (R-G-5), `LookupRow` (R-G-8), the `gate_result()`
table (R-G-10), `GatesUpdate.burning_card_id` (R-G-11), `SpecialistSend.planned` (R-G-12), `EscalationInputs.now`
(R-G-15), `AppointmentView` / `SchedulingSliceInputs` (R-G-19), `TurnPayload` (R-G-20), `GraphOutcome.closed_every_open_task`
(R-G-21); `SessionInfoData`, `CUSTOMER_SPEAKER_NAME`, `ROLE_ACTIONS` (residuals-web R-W-1, R-W-13, R-W-14).

### Source

- DO-4 §0–§14 (types and signatures), §16 (addenda win over earlier sections)
- stage7/graph-core.md §1–§3, §8–§14 and the GRC-19 table; stage7/graph-nodes.md §1, §4, §9.1; stage7/graph-tools.md §1,
  §2, §3, §5; stage7/models.md §1, §4, cross-topic 2–3; stage7/staff.md §1; stage7/cases.md §1.0, §2, §4.1, A-1…A-4;
  stage7/web.md §1
- Residual rulings (2026-10-21): `docs/plans/7b-decisions/residuals-graph.md` R-G-1, R-G-2, R-G-4, R-G-5, R-G-6,
  R-G-8, R-G-10, R-G-11, R-G-12, R-G-15, R-G-18, R-G-19, R-G-20, R-G-21; `residuals-web.md` R-W-1, R-W-5, R-W-13,
  R-W-14, R-W-15; stage7/cases.md §1.2 (`LookupRow`), §3.4 (`EscalationInputs.now`); stage7/graph-core.md §2, §3, §8
- Journey map: slice plan §0a; `.claude/rules/integrated-journeys.md`; `docs/plans/ux-join/backend-amendments.md` §3
- Decision ledgers: graph-core GRC-1, GRC-2, GRC-4, GRC-5, GRC-10, GRC-11, GRC-13, GRC-16, GRC-19…GRC-22, GRC-25;
  graph-nodes GRN-2, GRN-4; graph-tools GRT-1, GRT-5, GRT-6, GRT-8, GRT-9; models MOD-1, MOD-9, MOD-10, MOD-17; cases
  CAS-16, CAS-34, CAS-35, CAS-36; web WEB-9; staff STF-1, STF-2; merge-clashes MC-1…MC-5, MC-21; final-xref-A, -B, -C
- DO-3 §2.1 (dependency direction), §2.4 (`config.py` row), §3 (module homes), §4.1 (`domain/*` rows), §4.2 (ports), §5
  (state, who writes which key), §6 S-1, S-2, S-6, S-8, S-10, S-13, S-20
- DO-6 *Status values*, *Records* (`check_event`, `model_call`, `turn`), *Correlation* (`agent_version`, eval key)
- api-con-mapping §0–§1; OpenAPI schemas for wire-facing types and the error-code enum (read-only)
- PRD R-26 (promise texts), R-28 (brief headings), R-40 (Railway variables), R-45 (typed state), R-46 (checks), R-48
  (demo login variables)
- Slice plan §1 row AEA-02, §2 (Settings moved into 02; wave 0 keeps no internal edges), §3 rows `domain/*`, `ports/*`,
  `config.py`, `adapters/sqlite/repos_*.py` (frozen after their wave)
- **Brief check:** serves "failure handling must be clean (agent admits uncertainty and hands off rather than guessing)"
  — typed hand-offs with `extra="forbid"` make an invented field a loud failure, and `Settled` makes "what was done" one
  authority; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

`risk::security`: `test-writer-agent` freezes AC-3, AC-10, AC-11, AC-13, AC-14 and AC-15 as failing tests before the
implementer starts.

- [ ] AC-1 [invariant] Every pydantic model in `domain/*`, `ports/*` and `config.py` inherits `MeridianModel`'s configuration (or `LLMFacing`'s): `extra="forbid"`, frozen, `hide_input_in_errors`, `str_strip_whitespace` — verify: `tests/unit/domain/test_conventions.py::test_every_model_uses_meridian_config` (walks every class; dataclasses such as `TurnBudget`, `TurnContext`, `SpanHandle` are listed and skipped by name) — evidence: test passes and prints the class count.
- [ ] AC-2 [failure/refusal] Malformed IDs are rejected: a non-UUID4 `ThreadId` / `TurnId` / `RequestId`, `CustomerId` not `MHC-\d{5}`, `InvoiceId` not `INV-\d{6}`, `CaseRef` not `MHC-C-\d{4}`, `PassageId` without `#<n>` — verify: `tests/unit/domain/test_ids.py` (parametrised) — evidence: each case raises with field, code and constraint.
- [ ] AC-3 [negative] A distinctive rejected value is absent from every error a caller can serialise: `SafeError` and `str()` of the validation error carry field, stable code and constraint, never the input — verify: `tests/unit/domain/test_conventions.py::test_rejected_value_absent_from_safe_error` — evidence: the sentinel value (built at run time) is found in neither output (DO-4 §0; rule `safe-validation-errors`).
- [ ] AC-4 [invariant] Enums and status literals carry exactly their sources' values: `ActionKind` (7), `GateKind` (10), `HandoffReason` (DO-4 §7's 15 plus `burning_ruled_out`, CAS-16 option A), `Priority` (P0–P4), `ToolErrorCode` (13, graph-tools §1), `ToolKind` (7), `CheckKind` (7), `SignalName` (8), `DemoRole` (4), `StaffRole` (3), `ProviderName` (2); `ApiErrorCode` equals the OpenAPI enum; `TurnTrace.gate_result`, `.outcome`, `.degrade_reason` and `ExportStatus` equal DO-6 *Status values* — verify: `tests/unit/domain/test_enums.py` (the OpenAPI file is read, never written) — evidence: each set compared, none differ.
- [ ] AC-5 [invariant] `Settled` behaves as the WP-4F example and graph-core §14's rule: `has`; `current_visit` returns the newest `BOOKED`/`MOVED` visit with no later `CANCELLED` action, built from `after` keys only, with `status="original_stays"` and `change_request` set by a later `CHANGE_REQUEST_SENT`, else `None`; `only_turn` filters to one turn — verify: `tests/unit/domain/test_actions.py::test_wp4f_move_is_settled`, `::test_cancelled_visit_is_not_current`, `::test_change_request_keeps_original`, `::test_only_turn_filters_to_one_turn` — evidence: four passes.
- [ ] AC-6 [invariant] `Brief` accepts only exactly 8 headings, numbered 1–8 in order, titles equal to `BRIEF_TITLES`, origins state for 1, 3, 5, 6, 8 and extraction for 2, 4, 7, and heading 4 `checked = False` (R-28, DO-4 §7) — verify: `tests/unit/domain/test_handoff.py::test_brief_shape` — evidence: each broken shape is rejected; the valid one passes.
- [ ] AC-7 [failure/refusal] Every bound in the sketches holds on both sides: `IdentityState.tries_left`, `.codes_sent` 0–3; `Plan.tasks` ≤ 3; `PlannedTask.order` 1–3; `ResponderDraft.text` 1–1200; `KnowledgePoint.text` ≤ 500; `Quote.text` ≤ 300; `BriefExtraction.needs` 1–2, `claims` ≤ 5, `open_decision` ≤ 200; `DangerAssessment.confidence` 0–1; `CallRecord.attempt` 1–2; `CodeSent.sends_left` 0–2; `CodeWrong.tries_left` 1–2; `StaffNote.text` ≤ 300 — verify: `tests/unit/domain/test_bounds.py` (parametrised, one case per bound each side) — evidence: in-bound passes, out-of-bound fails.
- [ ] AC-8 [invariant] The state reducers behave as specified: `specialist_results` appends; `halt` keeps the first writer; `add_turn_events` returns `left` for an empty `right`, otherwise keeps only `left` events with `right[0].turn_id` and appends `right` (graph-core §11) — verify: `tests/unit/domain/test_state.py::test_reducers` — evidence: passes, including a new-turn case that drops the previous turn's events and a two-writer case in one turn that keeps both.
- [ ] AC-9 [invariant] `CheckEvent`'s builders map as graph-nodes §1 says: `from_check` → pass / trimmed / fallback with `removed` and sorted distinct `claim_kinds`; `from_gate` → fired for a kind outside {FREE_TEXT, CODE_ENTRY, LOCATE, CARD_CHOICE} or any rule id, else pass; `from_danger` → fallback / raised / pass; `from_halt` raises `ValueError` for DEADLINE, SPEND_CAP and PROVIDER_SPEND_CAP; and `GateDecision.gate_result()` maps CODE_ENTRY, LOCATE, CARD_CHOICE, FREE_TEXT to `clear` (code-design C-6) — verify: `tests/unit/domain/test_turn.py::test_check_event_builders` and `::test_gate_result_mapping` — evidence: both pass.
- [ ] AC-10 [negative] Private values never sit in a field a log, checkpoint or model could print: `FormValues.phone`, `Intake.code_digits`, `Locator.phone`, `IssuedSession.token` and `InboxMessage.code` are `SecretStr`, so sentinel digits, phone and token (assembled at run time) are absent from `repr()` and `model_dump_json()`; `TurnInput` has no `code_digits` or `form` field; `CheckEvent`, `SignalRecord`, `PlannerTrace` and `TurnTrace` have no free-text field — verify: `tests/unit/domain/test_conventions.py::test_secret_fields_absent_from_repr_and_dump` and `::test_record_types_hold_codes_only` — evidence: sentinels not found; the field lists of the four record types printed.
- [ ] AC-11 [failure/refusal] `Locator` accepts exactly one of (name and phone), `customer_id`, `invoice_number`, its error carries no supplied value, and `from_form` returns `None` for an incomplete form (graph-tools §5) — verify: `tests/unit/domain/test_identity.py::test_locator_exactly_one` and `::test_from_form_incomplete_is_none` — evidence: each wrong combination raises without the sentinel name or phone in the message; the incomplete form gives `None`.
- [ ] AC-12 [invariant] `Settings` builds from a complete environment with the code-default role maps (planner and classifier on `openrouter_jev`; planner fallback, responder, brief and specialist on `anthropic`), reads each value from graph-core §12's env name, and `.env.example` lists exactly those names with no values — verify: `tests/unit/test_config.py::test_valid_environment_builds` and `::test_env_example_matches_settings` — evidence: both pass; the second prints the name list it compared.
- [ ] AC-13 [failure/refusal] Jev configured for responder, brief or specialist, or any role placed in the wrong map, fails `Settings` validation naming the field and the rule; a missing required secret (`MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`, `MERIDIAN_SESSION_SECRET`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`) stops start-up with the variable's name — verify: `tests/unit/test_config.py::test_jev_in_structured_or_tool_role_rejected`, `::test_role_in_wrong_map_rejected`, `::test_missing_required_secret_named` (parametrised) — evidence: each raises with field, code and constraint or the variable name.
- [ ] AC-14 [negative] A distinctive sentinel secret value (built at run time, never a real key) in every `SecretStr` field is absent from `repr(settings)`, `str(settings)`, `role_model_map()`, every validation-error report and captured log output — verify: `tests/unit/test_config.py::test_secret_values_absent_from_repr_errors_and_logs` — evidence: the sentinel is found in none of the outputs (DO-6: key values "Never" in every column).
- [ ] AC-15 [invariant] `langfuse_complete()` is true only when all four `LANGFUSE_*` values are set, and absent keys leave `Settings` valid (export off, models.md §4 step 5) — verify: `tests/unit/test_config.py::test_langfuse_complete_needs_all_four` (parametrised over the 16 combinations) — evidence: true in exactly one case.
- [ ] AC-16 [invariant] The ports have the signatures DO-4 §12–§13 and the addenda give: minimal in-test stubs assign to `ChoiceModel`, `StructuredModel`, `ToolCallingModel` (each with a `provider` attribute), `ToolTranscript`, `TraceSink` (with `export_status(turn)`), `RetrievalIndex`, `Clock`, `UnitOfWorkFactory` and `UnitOfWork` without a type error, and `CallRecord.from_provider` copies every `ProviderCall` field and adds `role` and `attempt` — verify: the type check over `tests/unit/ports/test_protocol_shapes.py` and `pytest tests/unit/ports/test_call_record.py` — evidence: type check clean; test passes; AEA-11's fakes will be held to the same file.
- [ ] AC-17 [invariant] The seven repository shells exist with exactly the one constructor, and `UnitOfWork`'s `TYPE_CHECKING` attribute types resolve against them — verify: `tests/unit/adapters/test_repo_shells.py::test_seven_shells_one_constructor` and the type check over `ports/runtime.py` — evidence: test lists seven classes, each with `__init__(self, conn)` and no other public member; type check clean.
- [ ] AC-18 [invariant] Dependency direction: `domain/*` imports only pydantic, the standard library and other `domain` modules; `ports/*` imports only `domain` at run time (adapters only under `TYPE_CHECKING`); `config.py` imports only pydantic, the standard library, `domain`, `ports` and `privacy.redact` (`RedactionProfile`); nothing in these imports `anthropic`, `httpx`, `fastembed`, `langfuse`, `langgraph` or `sqlite3` (the repository shells excepted) — verify: `tests/unit/test_import_direction.py::test_domain_ports_config_imports` (static scan) — evidence: passes; the scan lists every import it saw.
- [ ] AC-19 [invariant] `GateDecision.gate_result()` implements graph-core §3's table for every kind: every `GateKind` maps to its DO-6 value, and the three `BURNING_ANSWER` answers map yes → `safety`, unsure → `burning_unclear`, no → `clear` (R-G-10) — verify: `tests/unit/domain/test_turn.py::test_gate_result_table` — evidence: one parametrised case per row of graph-core §3's table, all pass; the table printed.
- [ ] AC-20 [invariant] The staff-surface constants equal staff.md §1: `ROLE_ACTIONS[OWNER]` is empty; `ROLE_ACTIONS[SUPERVISOR]` is exactly `claim, release, start, wait, resolve, close_unresolved, assign, change_priority, flag`; `ROLE_ACTIONS[REPRESENTATIVE]` holds every other `CaseSummary.allowed_actions` key and neither `assign` nor `change_priority`; every key in any set is a value of the OpenAPI `allowed_actions` enum (read, never written); `CUSTOMER_SPEAKER_NAME == "Customer"` (R-W-13, R-W-14) — verify: `tests/unit/domain/test_staff.py::test_role_actions_and_customer_speaker_match_staff_md` — evidence: passes; the three sets printed.
- [ ] AC-21 [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-02.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-10 (every path imports the domain types and ports) as the journeys that will exercise this code once AEA-57, AEA-51, AEA-52 and AEA-53 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.
- [ ] AC-22 [regression/context] Context updated in the same change — verify: diff — evidence: area-map A0 row notes `config.py`, `domain/*` (eleven files), `ports/*` and the seven repository shells planned → actual with the commit; DO-3 §3 status line notes them built; the ICM row *Routes verified against code and tests* names this ticket's tests once they pass; the plan reports (not edits) any DO-4 §0–§14 line still contradicting an addendum for AEA-08.

### Observability

- Responsibilities: defines the shapes DO-6's records are built from, for the workflows that write them (WF-1, WF-2,
  WF-4, WF-9, WF-10 turns; WF-18 sessions): `TurnIds` (`request_id`, `thread_id`, `turn_id`, `run_tag`, `run_id`,
  `agent_version`), `TurnRecord` / `TurnTrace` / `PlannerTrace` (the `turn` row), `CallRecord` (`model_call` span and
  `spend_ledger`), `CheckEvent` (`check_event`, codes only), `SignalRecord` (the `signal` log record), `ExportStatus`
  (`turn.trace_export`). Preserves: no field that would carry a code, card number, phone or token into a record (AC-10).
  Emits nothing itself and adds no entry point.
- Capture evidence: AC-4 and AC-10 are this ticket's component-level guards; they never stand in for the capture checks.
  CAP-1…CAP-3 (AEA-51) drive CON-1/CON-2/CON-4 and find these records at the real entry points.

### Evaluation

- Checks: none added. E-1's WP-4F state-seam item (DO-5 *Failure categories*: State seam) relies on `Settled` reading the
  `actions` rows; AC-5 is its unit-level guard.
- Expected-answer authority: the `actions` table is the authority for what the conversation has done (DO-3 §5.1; DO-4 §1
  "built ONLY from actions + cases").

### Metrics

- References: M-3, M-18, M-20, M-22, M-24 read `turn.outcome`, `degrade_reason` and `gate_result`; M-16 and M-17 read
  `classifier` `CheckEvent`s with `gate_result`; M-29 reads `trace_export` (`ExportStatus`). Their value sets are defined
  here.
- Acceptance conditions: those value sets equal DO-6 *Status values* (AC-4), so the metrics stay computable from the
  stored records; no metric is computed here.

### Blocked by

None (slice plan wave 0). **One same-wave import the slice plan's §2 audit missed:** `RoleSpec.redaction` is typed
`RedactionProfile` (DO-4 §12; models.md §5 rule 4 keeps it on the spec), which lives in `privacy/redact.py` (AEA-04,
standard library only). Merge AEA-04 first inside wave 0; if it is not on `main` when this plan is written, the plan
records `blocked-on AEA-04` for `config.py` only and builds the rest. **Wave-0 merge order: AEA-04 → AEA-02 → AEA-05**
(R-G-18; AEA-01 and AEA-03 in parallel): AEA-05 merges after this ticket, because `gates/rules.py` imports `RuleMatches`
and `SafetyKind` from `domain/turn.py` (R-G-1). Both edges are inside wave 0; no wave moves. The parked `docs/parked/2026-10-21-first-attempt/src_meridian/config.py` is handled under
AEA-01's needs-decision; nothing parked is overwritten before that answer.

### Agent handoff

- Area / owner: A0 Foundation (area map row A0).
- Contracts and shared surfaces: produces every domain type, port, `Settings` and the repository shells for every later
  ticket: AEA-05 (imports `RuleMatches`, `SafetyKind`, `HandoffReason`; merges after this ticket, R-G-1) and AEA-12 (gate
  types, `TurnPayload`), AEA-10 (`UnitOfWork`, shells, `TurnRecord`, `LookupRow`), AEA-11 (fakes implement the ports),
  AEA-15 and AEA-29 (`LookupRow`, R-G-8), AEA-17/18/19/20 (`ProviderCall`, `CallRecord`, `TokenPrice`, `TraceSink`,
  `ModelSettings`), AEA-21 (`SpecialistSend`, `closed_every_open_task`), AEA-23/44 (`domain/staff.py` incl.
  `SessionInfoData`, `Settings`), AEA-28/39 (`AppointmentView`, `SchedulingSliceInputs`, `EscalationInputs.now`), AEA-29
  (`ROLE_ACTIONS`, `CUSTOMER_SPEAKER_NAME`), AEA-36 (`GatesUpdate.burning_card_id`), AEA-40 (`TurnPayload`,
  R-W-15), AEA-27 (`domain/identity.py`), AEA-09 and AEA-54 (env names from `Settings`), AEA-50 (`agent_version`,
  `role_model_map`). Frozen after wave 0: a missing field or method is its own small ticket merged before its
  dependants (slice plan §3). Must not edit: `policy/*` (AEA-01, AEA-03), `privacy/*` (AEA-04), `gates/*`, anything
  else under `adapters/`, `agent/`, `services/`, `web/`, the OpenAPI file.
- Scope boundary / refusal: types, Protocols, validators, the pure `Settled` helpers, the reducers and the `CheckEvent`
  builders only; no repository body, no SQL, no I/O; no guessed fields for an unsketched type; no `Promise` text
  validator (GRC-2); the four formerly contested types follow their residual rulings (R-G-1, R-G-2, R-G-4, R-G-6).
- Wave and gates: wave 0; merge order AEA-04 → AEA-02 → AEA-05 (R-G-18): merged after AEA-04 (the `RedactionProfile`
  import above) and before AEA-05 (R-G-1); security review at the wave-0 merge; gate: none open beyond CAS-16 below.
- Lane: build-loop — source, configuration and tests every module reads (`ticket-lanes`).
- Risk: security — `Settings` holds every secret the app uses (provider keys, session secret, demo login, eval key,
  Langfuse keys), and the domain types decide whether a code, phone or login token can ever reach a log, checkpoint or
  prompt (slice plan §0; DO-6 *Content and redaction*).
- Awaiting Innocent: CAS-16 — built on the recommended option (A: `HandoffReason.BURNING_RULED_OUT = "burning_ruled_out"`
  added now, since `domain/` is frozen after wave 0); if he picks another option the value is renamed or removed in a
  one-line follow-up merged before AEA-14 and AEA-36, and AC-4's count changes with it (graph-core GRC-19 row *cases A-3*
  otherwise waits for his answer).
- Entry points added or changed: None.
