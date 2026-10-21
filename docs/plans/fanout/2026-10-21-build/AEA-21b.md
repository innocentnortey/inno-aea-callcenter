# Plan — [AEA-21b] compose cards: slot, SLOT_TAKEN, account, where/urgency, appointment, no-fit (card-number notice deferred)

**Status:** planned (READY; one item, the card-number notice, is deferred to a texts follow-up, §8 R-1)
**Issue:** none (wave-fix item from AEA-21 plan §8.2 R-2 and AEA-51 plan §8 R-13) · **Base revision:** `main` `47da752` (re-checked: the merges after `2f70221` touch no planned surface except the area map, whose A7a row is unchanged)
**Lane:** `lane::build-loop` (changes running code). **Not** `risk::security`: compose is pure (no I/O, no auth, no
secret), so the loop is plan → implement (code + the tests named here) → affected tests → review. No test-writer, no
frozen-test manifest, no security agent.

---

## 1. Goal and sources

### 1.1 Goal

`src/meridian/agent/nodes/compose.py` (AEA-21) builds no `SlotCardBlock`, no `ErrorBlock` `SLOT_TAKEN` with
`fresh_windows`, no `AccountCardBlock`, no `AppointmentBlock`, no `WherePromptBlock`, no `UrgencyQuestionsBlock`, no
no-fit reply and no card-number notice (`grep -c` of those constructors in `compose.py` = 0). Without them the customer
cannot pick an arrival window (J-3 booking) or see account facts (J-2 invoice, WP-8 membership, warranty). AEA-51 and
AEA-62 are blocked on this (AEA-51 plan §8 R-13: AC-7, AC-8, AC-10, AC-12, AC-14, AC-25, AC-26, AC-27, AC-36, AC-37,
AC-38, AC-43, J-2 step 2, J-3).

This slice adds a new module `src/meridian/agent/nodes/compose_cards.py` holding the card builders (and the labels and
helpers both modules need, moved out of `compose.py` because `compose.py` is at 695 lines against a 700 cap), and
wires the builders into `ReplyComposer._answer` (graph-core §13, DO-4 §9 order). Each card is built from the state the
contract names, from the merged types on `main` (never retyped).

**In practice (J-3, the path this slice must unblock).** Turn 3 of WP-3: Linda (MHC-10001) has typed her code. The
identity node verified her, the router resumed her open booking task `task-1a2b3c4d-1`, and the scheduling specialist
returned `SchedulingResult(status="windows_shown", windows=(slot 56, slot 42, slot 58))`; `facts` kept the task `open`.
Compose now adds one `SlotCardBlock` with `card_id="task-1a2b3c4d-1.1"`, one day "Mon 19 · 3 open" holding the three
windows (Marta Kowalski, Ray Mendoza, Marta Kowalski), `standard_fee` `$89`, `hint` "Windows are shown, not held." and
no members note (she is verified). When she taps 56 the frontend posts `{card_id: "task-1a2b3c4d-1.1", option: "56"}`;
`decide_gate` reads the `task` prefix and returns `CARD_CHOICE` with `resume_task_id="task-1a2b3c4d-1"`, and the router
resumes the booking task. That chain is tested in §7.1 B (`test_j3_slot_card_choice_resumes_booking_task`).

### 1.2 Sources (read by the planner; the implementer reads only what a step names)

| Source | Location | What it obliges here |
|---|---|---|
| Finding | `docs/plans/fanout/2026-10-21-build/AEA-21.md` §8.2 R-2; `AEA-51.md` §8 R-13 | The card list; J-3 needs the slot card; merge before AEA-51 and AEA-62 |
| Compose contract | `docs/design/contracts/stage7/graph-core.md` §13 (`ReplyComposer`), §3 (card ids: `"<task_id>.<n>"` for any card of an open task), §14 (`VisitView`) | One builder of blocks; pure; card id prefixes |
| Quick checks | `stage7/graph-nodes.md` §8 (GRN-10); `stage7/graph-tools.md` §6 | Unchanged behaviour; its card id now comes from the per-task counter |
| Burning "no" | `stage7/graph-nodes.md` §6 (GRN-6); sign-off D-14 (CAS-16 option A: P2 `burning_ruled_out`) | `SlotCardBlock.urgent` on that booking |
| Capture shapes | `stage7/graph-tools.md` §3 ("View field names follow the OpenAPI `AccountCardBlock` (amounts in integer cents; compose builds `Money`)") | Account card from `AccountResult` views; never `staff_notes` |
| DO-4 | `docs/design/contracts/internal-components.md` §1 (`OpenTask.missing: tuple[MissingInfo, ...]` "locate_needed, zip_needed …"), §8 (`TurnFacts.account/missing/notices`), §9, §11 (`SLOT_TAKEN` composed error) | Where prompt reads `missing`; those fields are **not built** on `main` (domain/state.py and domain/turn.py docstrings) |
| Wire shapes (signed, read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml`: schemas `SlotCardBlock`, `ErrorBlock`, `AccountCardBlock`, `AppointmentBlock`, `WherePromptBlock`, `UrgencyQuestionsBlock`, `FailureOfferBlock`, `ReplyBlock`; CON-2 examples `URGENCY_QUESTIONS`, `WHERE_PROMPT`, `SLOT_CARD`, `SLOT_CARD_MEMBER`, `VERIFIED_ACCOUNT_INVOICE`, `ACCOUNT_MEMBERSHIP`, `ACCOUNT_WARRANTY`, `APPOINTMENT`, `SLOT_TAKEN` | Field sets, labels (copied, PD-9 of AEA-21) |
| Screen states | `docs/ux/03-structure/SCREEN_SPECS.md` SCR-1 flow states ("Burning smell, both ruled out → slot card marked Urgent", "No window fits → … 'That's the earliest I can book…' + person offer", "Slot taken at write", "Confirm existing visit → Appointment card", "Account answer") | Which card each state shows |
| Worked pairs | `docs/data/worked-pairs.md` WP-2 (INV-204411 lines $89 / $245 / $144, total $478.00, due 2026-11-01, unpaid), WP-3 (Mon Oct 19: slot 56 8–12 Marta Kowalski, 42 12–4 Ray Mendoza, 58 1–5 Marta Kowalski), WP-8 (renewal 2026-11-03) | Test data; WP-3 is this slice's worked pair |
| Code on `main` | `src/meridian/agent/nodes/compose.py` (695 lines), `domain/blocks.py`, `domain/specialists.py`, `domain/state.py`, `domain/turn.py`, `domain/actions.py`, `domain/records.py`, `policy/booking.py` (`fee_note`), `policy/texts.py`, `gates/gate.py`, `agent/routers.py`, `agent/nodes/reply.py` (`facts`: task ids, task status), `agent/specialists/specs.py` (`build_scheduling_result`) | Every signature in §4 is copied from these |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §4–§5, `context-maintenance.md`, workspace `code-structure.md` (size caps), `code-design-solid-modularity.md` | Checks, journey record, area-map row |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer creates or edits)

| File | Current | Change |
|---|---|---|
| `src/meridian/agent/nodes/compose_cards.py` | does not exist | **create** (§4.3, step 1–3). Target ≤ 420 lines, hard stop 450 |
| `src/meridian/agent/nodes/compose.py` | 695 lines (AEA-21) | **modify**: move helpers out, wire the cards (§4.4, step 4). Must end ≤ 690 lines |
| `tests/unit/agent/nodes/compose_card_fixtures.py` | does not exist | **create**: synthetic builders (§6). ≤ 200 lines |
| `tests/unit/agent/nodes/test_compose_cards.py` | does not exist | **create**: pure builder tests (§7.1 A). ≤ 450 lines |
| `tests/unit/agent/nodes/test_compose_card_wiring.py` | does not exist | **create**: `ReplyComposer.compose` tests and the J-3 card-path seam (§7.1 B). ≤ 450 lines |
| `docs/testing/journeys/2026-10-21-AEA-21b.md` | does not exist | **create**: journey record (§7.4) |
| `.claude/reference/area-map.md` | A7a row (line 35) | **append** one clause to the Status cell of the **first** A7a row (step 7). Append-only; nothing else in the file |

### 2.2 Shared surfaces read only (never edit)

`src/meridian/domain/**` (blocks, specialists, state, turn, actions, records, common, identity), `src/meridian/policy/texts.py`,
`src/meridian/policy/booking.py`, `src/meridian/gates/gate.py`, `src/meridian/agent/routers.py`, `src/meridian/agent/graph.py`,
`src/meridian/agent/nodes/reply.py`, `src/meridian/agent/specialists/specs.py`, `tests/unit/agent/nodes/compose_fixtures.py`
(import only), `tests/unit/agent/nodes/test_compose.py`, `tests/unit/agent/nodes/test_compose_blocks.py`,
`tests/api/openapi_check.py`, `tests/contract/openapi_variants.py` (import only), the OpenAPI, `UI_CONTRACTS.md`,
`docs/ux/**`, `apps/web/**`, the briefing, issued data, `docs/archive/`, `docs/parked/`.

### 2.3 Owned by other slices (do not touch)

- AEA-51 (`aea-51-aea-51-customer-path` worktree): `web/container.py` `register_graph`, `tests/integration/`, `tests/graph/test_worked_pairs_api.py`, journeys J-2…J-5, J-9. Checked at planning: **no open branch edits any `compose*` file** (`git diff --name-only main...<branch>` over every local branch).
- AEA-62: browser legs of J-2, J-3, J-6, J-8.
- AEA-03 (texts, frozen): any new customer sentence (§8 R-1).
- AEA-02 (domain): `MissingInfo`, `OpenTask.missing`, `TurnFacts.account/missing/notices` (§8 R-3).

---

## 3. Requirements table

### 3.1 Acceptance criteria (one row each; kind in brackets)

| AC | Requirement | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | A `SchedulingResult` with `status="windows_shown"` and windows, plus an open scheduling task, yields one `SlotCardBlock`: `card_id` `"<task_id>.<n>"`; windows sorted by (date, window, slot_id); one `SlotDay` per date with label `"<Dow3> <day> · <n> open"`, `open_count = n`; each `SlotWindow` `slot_id=str(id)`, `window_label` from the label table, `member_only = member_reserved`, `taken=False`; one `Option` per window (`option=str(slot_id)`, `label=window_label`); `standard_fee` = `fee_note(service_type, "none")` as `Money(amount_cents, format_usd(...))`; `hint = TEXTS[SLOTS_NOT_HELD]`; `members_note = TEXTS[MEMBERS_NOTE]` unless identity is `verified` (then `None`) | `slot_card`, `scheduling_cards` (§4.3), step 2 | `test_compose_cards.py::test_slot_card_groups_windows_by_day`, `::test_slot_card_member_window_one_open_day_and_estimate_fee`; `test_compose_card_wiring.py::test_wp3_slot_card_on_code_turn` (WP-3) |
| AC-2 [negative] | No card when the result has no windows or no open scheduling task, and no block id or task card number is consumed | `slot_card` step 1 | `test_compose_cards.py::test_slot_card_omitted_without_windows_or_task` |
| AC-3 [failure/refusal] | `status="slot_taken"` yields `ErrorBlock(code="SLOT_TAKEN", text=TEXTS[SLOT_TAKEN], tries_left=None, fresh_windows=<slot card of result.windows>, person_key=False)`; with no alternatives (or no open task) `fresh_windows=None, person_key=True`. Nothing is booked (no write card) | `slot_taken_error` | `test_compose_cards.py::test_slot_taken_error_with_and_without_fresh_windows`; `test_compose_card_wiring.py::test_wp3_slot_taken_shows_fresh_windows` |
| AC-4 [failure/refusal] | `status="no_fit"` yields one `FailureOfferBlock(text=TEXTS[NO_WINDOW_FITS], person_key=True)`; an escalation `offer` on the same turn adds **no** second `FailureOfferBlock` | `scheduling_cards`; compose step 11 condition | `test_compose_card_wiring.py::test_no_fit_offers_a_person_once` |
| AC-5 [invariant] | `SlotCardBlock.urgent` is `True` iff this turn's gate is `BURNING_ANSWER` with `burning_answer="no"`, or the effective settled `open_case.reason is HandoffReason.BURNING_RULED_OUT`; else `False` | `is_urgent` | `test_compose_card_wiring.py::test_urgent_after_burning_ruled_out` |
| AC-6 [invariant] | An `AccountResult` with `status="read"` yields, in order, one `AccountCardBlock` per invoice (`kind="invoice"`, every amount `Money` with two-decimal display, `source=None`), then one membership card (only when `tier` is `standard`/`plus` and `renewal_date` is set; tier label from the KB headings), then one warranty card (`install_date`, `sentence` word for word). `not_verified` / `failed` results yield none. `staff_notes` are never read | `account_cards` | `test_compose_cards.py::test_wp2_invoice_card_as_billed`, `::test_membership_and_warranty_cards_and_omitted_variants`; `test_compose_card_wiring.py::test_wp2_invoice_card_after_verified_line`, `::test_wp8_membership_card`, `::test_account_card_never_carries_staff_notes` |
| AC-7 [invariant] | When the plan has a task with intent `CONFIRM` or `READ_APPOINTMENTS`, no `ConfirmationBlock`/`CancelledBlock` was added this turn, and `settled_view.visit` exists, one `AppointmentBlock` mirrors that visit (`label` "Your booked visit") | compose step 7a, `appointment_block` | `test_compose_card_wiring.py::test_appointment_card_only_for_a_visit_question_without_a_write` |
| AC-8 [invariant] | Where prompt: an open scheduling task whose `missing` (DO-4 §1, read by name, absent on `main`) contains `"zip_needed"`, on a turn where the scheduling results produced no block, yields one `WherePromptBlock(card_id="<task_id>.<n>", options=(), answered=None, label="ZIP code or city", submit_label="Show windows")`; with no `missing` attribute nothing is added | `task_missing`, `scheduling_cards` tail | `test_compose_card_wiring.py::test_where_prompt_reads_task_missing` |
| AC-9 [invariant] | `urgency_questions_block` builds the three skippable questions (`temp`, `water`, `risk`; texts `URGENCY_HOT_COLD`, `URGENCY_WATER`, `URGENCY_AT_RISK`; answers yes/no/skip; options skip). **Not wired** into compose (no state asks for it, §8 R-2) | `urgency_questions_block` | `test_compose_cards.py::test_where_prompt_and_urgency_question_shapes` |
| AC-10 [invariant] | Task card ids count per task inside one reply: quick checks then slot card for the same task are `"<task>.1"`, `"<task>.2"`; another task restarts at `.1` | `BlockIds.task_card`; quick checks call site | `test_compose_cards.py::test_task_card_ids_count_per_task`; `test_compose_card_wiring.py::test_quick_checks_and_slot_card_get_distinct_card_ids` |
| AC-11 [invariant] (J-3 seam) | The slot card's `card_id` posted back as a choice routes to `CARD_CHOICE` with `resume_task_id` = the booking task and the gates router sends one resumed `PlannedTask` (BOOK_NEW, `resumes_task_id` set) to the specialists | real `parse_intake`, `flags_from_state`, `decide_gate`, `route_after_gates` on compose's output | `test_compose_card_wiring.py::test_j3_slot_card_choice_resumes_booking_task` |
| AC-12 [contract] | Every new block (each variant above, including the omitted-optional ones: `members_note=None`, `fresh_windows=None`, `membership=None`, `warranty=None`, `invoice=None`, an invoice with no lines) validates against the OpenAPI `ReplyBlock` schema | test helper `assert_matches_openapi` | `test_compose_cards.py::test_new_blocks_match_openapi` (parametrized) |
| AC-13 [regression] | Existing behaviour unchanged: every test in `test_compose.py`, `test_compose_blocks.py`, `tests/graph/`, `test_act.py`, `test_plan_graph.py`, the prompt/consumer contract test and `test_cases_contract.py` stays green; `compose.py` ≤ 690 lines; `grep -c "staff_notes" src/meridian/agent/nodes/compose*.py` = 0 | step 4 (moves are behaviour-neutral) | §7.3 G-3, G-5 |
| AC-14 [journey] | The affected journeys run green at their current level (`uv run python -m tests.journeys.affected --base main`); a record at **`mock-tested`** names J-2 (account card) and J-3 (slot card, card path) and the seam test of AC-11; *Blocked by*: AEA-51 (graph not bound into the app, so no integrated booking path yet) and AEA-62 (browser legs) | journey record (step 6) | `docs/testing/journeys/2026-10-21-AEA-21b.md`; the command's output |
| AC-15 [regression/context] | Area map A7a row names `nodes/compose_cards.py` and AEA-21b | step 7 | `git diff --name-only main...HEAD` lists `.claude/reference/area-map.md` |

**Not delivered here (deferred, §8 R-1):** the card-number notice. The state exists (`TurnInput.card_number_seen`), but
`policy/texts.py` has no customer sentence for it and the signed `Notice.code` / `NoticeBlock.code` enums have no
card-number value; a new sentence is UX copy owned by AEA-03 (frozen module). Do **not** invent a sentence and do
**not** add a text id.

### 3.2 Source-contract reconciliation

| Obligation | Governing source | Disposition | Step / owner |
|---|---|---|---|
| Slot card from shown windows, `standard_fee`, `hint`, `members_note`, `urgent` | OpenAPI `SlotCardBlock`, SLOT_CARD(_MEMBER); SCREEN_SPECS | in-slice | steps 2, 4 |
| `SLOT_TAKEN` + fresh windows | DO-4 §11; OpenAPI SLOT_TAKEN | in-slice | steps 2, 4 |
| Account card, Money built by compose, no staff notes | graph-tools §3; HP-3 | in-slice | steps 2, 4 |
| Appointment card for "confirm my visit" | SCREEN_SPECS FLOW-6 row; OpenAPI APPOINTMENT | in-slice for visits in `settled`; **request** for visits booked outside the chat (no confirm-result view) | step 4; §8 R-4 |
| No-fit text + person offer | SCREEN_SPECS "No window fits"; `TextId.NO_WINDOW_FITS` | in-slice | steps 2, 4 |
| Where prompt from `MissingInfo.zip_needed` | DO-4 §1, §8 | in-slice, read by name (field not built) | steps 2, 4; §8 R-3 |
| Urgency questions | WP-3 required output 1; FLOW-5; OpenAPI URGENCY_QUESTIONS | builder in-slice; **wiring needs a producing state and a consumer that do not exist** | step 2; §8 R-2 |
| Card-number reply (R-13) | system-design "the reply says cards aren't taken in chat"; DO-4 §8 `notices` | **deferred**: needs a new UX sentence (AEA-03) | §8 R-1 |
| `TurnFacts.account` (`AccountFactsView`) | DO-4 §8 | n/a here: compose reads `AccountResult` directly (its views are the customer-facing fields; `staff_notes` never read). Same data, no new type | — |
| Card ids `<task_id>.<n>` | graph-core §3 | in-slice (per-task counter) | step 1 |

### 3.3 Entry-point registration

| Entry point | Workflow | Registered | Inherits |
|---|---|---|---|
| None (compose is reached only through `run_graph`, CON-2 WF-1) | — | — | — |

---

## 4. Shared code to use (copied from `main` at `47da752`)

### 4.1 Module rules for both compose files

1. First line after the module docstring: `from __future__ import annotations`; dates as `import datetime as dt`.
2. Absolute imports only. `compose_cards.py` may import only: stdlib, `meridian.domain.*`, `meridian.policy.texts`,
   `meridian.policy.booking` (`fee_note`, pure), and nothing from `meridian.agent.*`, services, adapters, ports or
   `langgraph`. `compose.py` additionally imports `meridian.agent.nodes.compose_cards` (one direction only:
   `compose_cards` never imports `compose`).
3. No module-level instances except immutable constants (frozen models, tuples, `MappingProxyType`, `frozenset`,
   strings). No clock read, no logger, no settings.
4. Mypy strict with the pydantic plugin and `init_typed = true`: build fields with their real types.
5. **Never reference `staff_notes`** in either file (not even in a comment: AC-13's grep is literal). Never read
   `ctx.intake` or `state.turn_input.text_store`.
6. Every customer sentence is `TEXTS[TextId.X]`; never type a sentence. Non-sentence labels are the constants in §4.3.

### 4.2 Types and functions used (exact, from `main`)

```python
# src/meridian/domain/blocks.py
class Speaker(MeridianModel): kind: Literal["assistant", "customer", "representative", "event"]; display_name: str | None
class Option(MeridianModel): option: str; label: str; disabled: bool; reason: str | None
class Money(MeridianModel): amount_cents: int; display: str
class BlockBase(MeridianModel): block_id: str; speaker: Speaker; at: dt.datetime
class UrgencyQuestion(MeridianModel): question_id: str; text: str; answers: tuple[Option, ...]
class UrgencyQuestionsBlock(BlockBase): type="urgency_questions"; card_id: str; options: tuple[Option, ...];
    answered: str | None; questions: tuple[UrgencyQuestion, ...]; skippable: Literal[True] = True
class WherePromptBlock(BlockBase): type="where_prompt"; card_id: str; options: tuple[Option, ...]; answered: str | None;
    label: str; submit_label: str
class SlotWindow(MeridianModel): slot_id: str; date: dt.date; window: str; window_label: str; technician: str;
    member_only: bool; taken: bool
class SlotDay(MeridianModel): date: dt.date; label: str; open_count: int; windows: tuple[SlotWindow, ...]
class SlotCardBlock(BlockBase): type="slot_card"; card_id: str; options: tuple[Option, ...]; answered: str | None;
    urgent: bool; days: tuple[SlotDay, ...]; standard_fee: Money; hint: str; members_note: str | None
class AppointmentBlock(BlockBase): type="appointment"; appointment_id: int; date: dt.date; window_label: str;
    technician: str; fee_line: str; label: Literal["Your booked visit"] = "Your booked visit"
class AccountInvoiceLine(MeridianModel): description: str; amount: Money; source: SourceChip | None
class AccountInvoice(MeridianModel): invoice_id: str; lines: tuple[AccountInvoiceLine, ...]; total: Money;
    balance: Money; due_on: dt.date; paid: bool
class AccountMembership(MeridianModel): tier: str; renewal_date: dt.date
class AccountWarranty(MeridianModel): install_date: dt.date; sentence: str
class AccountCardBlock(BlockBase): type="account_card"; kind: Literal["invoice", "membership", "warranty"];
    invoice: AccountInvoice | None; membership: AccountMembership | None; warranty: AccountWarranty | None
class FailureOfferBlock(BlockBase): type="failure_offer"; text: str; person_key: bool
class NoticeBlock(BlockBase): type="notice"; code: Literal["RATE_LIMITED", "BOOKING_CAP", "SPEND_CAP_REACHED",
    "TURN_TIMEOUT", "BUSY", "AI_PAUSED"]; text: str; person_key: bool
class ErrorBlock(BlockBase): type="error"; code: Literal["SLOT_TAKEN", "OUT_OF_AREA", "CODE_WRONG", "CODE_EXPIRED",
    "CODE_LOCKED", "CODE_CAP_REACHED", "NOT_VERIFIED"]; text: str; tries_left: int | None;
    fresh_windows: SlotCardBlock | None; person_key: bool
class Notice(MeridianModel): code: Literal[...same six...]; actions: tuple[Literal["try_again", "talk_to_person"], ...];
    retry_turn_id: str | None; delivered_to_representative: bool
class SettledVisit(VisitView): window_label: str      # VisitView: appointment_id: int; date; window; technician: str;
                                                      #   service_type; fee_line: str; status; change_request
ReplyBlock = Annotated[TextBlock | ... | ErrorBlock | SessionEndedBlock, Field(discriminator="type")]

# src/meridian/domain/records.py
Window = Literal["08:00-12:00", "12:00-16:00", "13:00-17:00", "16:00-19:00"]
ServiceType = Literal["hvac_repair", "hvac_tune_up", "plumbing", "estimate"]
class ShownSlot(MeridianModel): slot_id: int; date: dt.date; window: Window; technician: str; service_type: ServiceType;
    zone: Zone; member_reserved: bool; shown_turn: TurnId
class FeeNote(MeridianModel): service_type; tier; fee_row: str | None; amount_cents: int; waived: bool; line: str

# src/meridian/domain/specialists.py
class InvoiceLineView(MeridianModel): description: str; amount_cents: int
class InvoiceView(MeridianModel): invoice_id: InvoiceId; lines: tuple[InvoiceLineView, ...]; total_cents: int;
    balance_cents: int; issued_on: dt.date; due_on: dt.date; paid: bool
class MembershipView(MeridianModel): tier: Literal["none", "standard", "plus"]; renewal_date: dt.date | None
class WarrantyView(MeridianModel): install_date: dt.date; equipment_brand: str | None; sentence: str
class AccountResult(MeridianModel): kind="account"; status: Literal["read", "not_verified", "failed"];
    invoices: tuple[InvoiceView, ...] = (); membership: MembershipView | None = None; warranty: WarrantyView | None = None;
    staff_notes: ... = (); tools; calls; brake=None; failure=None
class SchedulingResult(MeridianModel): kind="scheduling"; status: Literal["windows_shown", "written",
    "staff_change_request", "slot_taken", "out_of_area", "no_fit", "not_verified", "booking_cap", "failed"];
    windows: tuple[ShownSlot, ...] = (); write=None; change_request=None; quick_checks: tuple[Passage, ...] = (); tools; calls; ...
SpecialistResult = Annotated[KnowledgeResult | AccountResult | SchedulingResult, Field(discriminator="kind")]

# src/meridian/domain/state.py
class OpenTask(MeridianModel): task_id: str; specialist: SpecialistKind; intent: TaskIntent; opened_turn: TurnId;
    details: TaskDetails; status: Literal["open", "waiting_identity", "done"]      # NO `missing` field on main
class ConversationState: ... identity: IdentityState; open_tasks: list[OpenTask]; gate: GateDecision | None;
    plan: Plan | None; specialist_results: list[SpecialistResult]; ...

# src/meridian/domain/actions.py
class Settled(MeridianModel): actions; open_case: OpenCase | None; read_at
class OpenCase(MeridianModel): case_ref; reason: HandoffReason; priority; state; promise; followup; live_queued

# src/meridian/domain/common.py
class HandoffReason(StrEnum): ... BURNING_RULED_OUT = "burning_ruled_out"

# src/meridian/domain/turn.py
class GateKind(StrEnum): ... BURNING_ANSWER = "burning_answer"; CARD_CHOICE = "card_choice"; CODE_ENTRY = "code_entry"
class GateDecision: kind: GateKind; rules: RuleMatches; burning_answer: Literal["yes", "no", "unsure"] | None = None;
    resume_task_id: str | None = None
class TaskIntent(StrEnum): ... BOOK_NEW = "book_new"; RESCHEDULE; CANCEL; CONFIRM = "confirm"; READ_APPOINTMENTS = "read_appointments"
@dataclass(frozen=True) class TurnContext: ids: TurnIds; budget; now: dt.datetime; demo_session; span; intake=None
class ChoicePayload(CardChoice): kind: Literal["choice"] = "choice"     # CardChoice: card_id: str; option: str

# src/meridian/policy/booking.py
def fee_note(service_type: ServiceType, tier: Literal["none", "standard", "plus"]) -> FeeNote: ...
    # hvac_repair/plumbing → 8900 ("Diagnostic visit"); hvac_tune_up → 12900; estimate → 0 (fee_row None)

# src/meridian/policy/texts.py
def format_usd(cents: int) -> str: ...      # "$89", "$12.50", "$1,250"; raises ValueError on negative
TextId.SLOT_TAKEN          "Sorry, that window just went. Here are the next open ones."
TextId.NO_WINDOW_FITS      "That's the earliest I can book. I can't add you to a waitlist from here."
TextId.SLOTS_NOT_HELD      "Windows are shown, not held."
TextId.MEMBERS_NOTE        "Members' fees and member-only windows appear after the code."
TextId.URGENCY_HOT_COLD    "Is it very hot or very cold in your home right now?"
TextId.URGENCY_WATER       "Is water still running?"
TextId.URGENCY_AT_RISK     "Is anyone at higher risk, like an older person, a baby or someone unwell?"
TextId.OUT_OF_AREA, BOOKING_CAP, FAILURE_OFFER (existing uses, unchanged)

# src/meridian/gates/gate.py (tests only)
def parse_intake(payload: TurnPayload) -> Intake: ...
def flags_from_state(state: ConversationState) -> GateFlags: ...
def decide_gate(intake: Intake, flags: GateFlags) -> GateDecision: ...
def card_target(card_id: str) -> CardTarget: ...   # "<task>.<n>" → ("task", "<task>") via r"(?P<task>.+)\.(?P<n>[0-9]+)"

# src/meridian/agent/routers.py (tests only)
def route_after_gates(state: ConversationState) -> RouterResult: ...
    # CARD_CHOICE → _route_planned(_resumed([task]), state) → list[Send("run_specialist", SpecialistSend(planned=…, state=…))]
    #   when identity is verified; PlannedTask(order=1, specialist, intent, needs_identity=(status=="waiting_identity"),
    #   resumes_task_id=task.task_id)

# src/meridian/agent/nodes/reply.py (facts; read only): new task ids are f"task-{str(turn_id)[:8]}-{planned.order}";
#   a scheduling task stays "open" when its result is "windows_shown" or "slot_taken".
```

### 4.3 `src/meridian/agent/nodes/compose_cards.py` — the full public surface

Module docstring (exactly this meaning, wording free): "Card builders for the compose node (AEA-21b): the labels and
block ids both compose modules use, and the cards built from specialist results and the open task. Pure: no I/O, no
model, no clock read. Sentences come from `policy/texts.py`; non-sentence labels are copied from the OpenAPI CON-2
examples (AEA-21 PD-9) or the KB's tier headings."

```python
__all__ = [
    "ASSISTANT", "DOW3", "MON3", "WINDOW_LABELS", "BlockIds", "BlockKw", "ErrCode", "NoticeCode",
    "account_cards", "appointment_block", "error_block", "exact_money", "is_urgent", "make_notice",
    "notice_block", "offer_block", "open_scheduling_task", "scheduling_cards", "slot_card", "slot_taken_error",
    "task_missing", "urgency_questions_block", "where_prompt_block", "window_label",
]
```

**Moved unchanged from `compose.py` (same values, public names):**

| New name in `compose_cards.py` | Was in `compose.py` | Notes |
|---|---|---|
| `ASSISTANT` | `_ASSISTANT` (line 35) | `b.Speaker(kind="assistant", display_name="Meridian assistant")` |
| `WINDOW_LABELS` | `_WINDOW_LABELS` (36–43) | same four entries |
| `DOW3`, `MON3` | `_DOW3`, `_MON3` (44–45) | |
| `ErrCode` | `_ErrCode` (97–99) | **add** `"SLOT_TAKEN"` as the first member: `Literal["SLOT_TAKEN", "OUT_OF_AREA", "CODE_WRONG", "CODE_EXPIRED", "CODE_LOCKED", "CODE_CAP_REACHED", "NOT_VERIFIED"]` |
| `NoticeCode` | `_NoticeCode` (100) | unchanged |
| `window_label(window: str) -> str` | `_window_label` (104–105) | `return WINDOW_LABELS.get(window, window)` |
| `class BlockKw(TypedDict)` | `_Base` (192–195) | `block_id: str; speaker: b.Speaker; at: dt.datetime` |
| `class BlockIds` | `_Ids` (198–208) | `__init__(self, ctx: tn.TurnContext)`, attribute `turn_id: str`, `kw(self) -> BlockKw`; **plus** `task_card` (below) |
| `offer_block(ids: BlockIds, text: str | None = None) -> b.FailureOfferBlock` | `_offer` (218–219) | `text=TEXTS[TextId.FAILURE_OFFER] if text is None else text`, `person_key=True` |
| `error_block(ids: BlockIds, code: ErrCode, text: str, tries_left: int | None = None) -> b.ErrorBlock` | `_error` (222–230) | unchanged body (`fresh_windows=None`, `person_key=tries_left is None`) |
| `notice_block(ids: BlockIds, code: NoticeCode, text: str) -> b.NoticeBlock` | `_notice_block` (233–234) | unchanged |
| `make_notice(code: NoticeCode, actions: tuple[Literal["try_again", "talk_to_person"], ...], retry: str | None = None, to_rep: bool = False) -> b.Notice` | `_notice` (237–243) | unchanged body; renamed so it never shadows a local `notice` |

`BlockIds` after the move (the only behaviour addition):

```python
class BlockIds:
    """Block ids for one reply (the k-th block gets `blk-<turn>-<k>`) and task card ids (`<task_id>.<n>`, graph-core §3)."""

    def __init__(self, ctx: tn.TurnContext) -> None:
        self.turn_id = str(ctx.ids.turn_id)
        self._at = ctx.now
        self._n = 0
        self._task_cards: dict[str, int] = {}

    def kw(self) -> BlockKw: ...                       # unchanged from _Ids.kw

    def task_card(self, task_id: str) -> str:
        """The next card id of this task in this reply: "<task_id>.1", then ".2" (PD-8 of AEA-21, now counted)."""
        n = self._task_cards.get(task_id, 0) + 1
        self._task_cards[task_id] = n
        return f"{task_id}.{n}"
```

**New constants** (exact values):

```python
_TIER_LABELS: Mapping[str, str] = MappingProxyType(
    {"standard": "Comfort Club (Standard)", "plus": "Comfort Club Plus"}       # KB tier headings (PD-21b-3)
)
_WHERE_LABEL = "ZIP code or city"                                             # OpenAPI WHERE_PROMPT; SCREEN_SPECS
_WHERE_SUBMIT = "Show windows"
_SKIP = b.Option(option="skip", label="Skip", disabled=False, reason=None)
_YES_NO_SKIP = (
    b.Option(option="yes", label="Yes", disabled=False, reason=None),
    b.Option(option="no", label="No", disabled=False, reason=None),
    _SKIP,
)
_URGENCY: tuple[tuple[str, TextId], ...] = (
    ("temp", TextId.URGENCY_HOT_COLD), ("water", TextId.URGENCY_WATER), ("risk", TextId.URGENCY_AT_RISK)
)                                                                              # OpenAPI URGENCY_QUESTIONS ids
_ZIP_NEEDED = "zip_needed"                                                     # DO-4 §1 MissingInfo value
```

**New functions** (signatures binding; bodies follow the numbered steps):

```python
def exact_money(cents: int) -> b.Money:
    """Invoice amounts as billed, always two decimals: 8900 → "$89.00", 125000 → "$1,250.00", -1250 → "-$12.50"."""
```
1. `sign = "-" if cents < 0 else ""`; `dollars, rem = divmod(abs(cents), 100)`.
2. `return b.Money(amount_cents=cents, display=f"{sign}${dollars:,}.{rem:02d}")`.
   *Invariant: matches the OpenAPI invoice example (`$89.00`) and AEA-62's J-2 text checks; `format_usd` is not used
   here because it drops zero cents and refuses negatives.*

```python
def open_scheduling_task(state: ConversationState) -> OpenTask | None:
    """The first open task of the scheduling specialist (status != "done"), or None."""
    return next((t for t in state.open_tasks if t.specialist == "scheduling" and t.status != "done"), None)

def task_missing(task: OpenTask) -> frozenset[str]:
    """DO-4 §1 `OpenTask.missing` (MissingInfo) is not built yet (AEA-02 plan 8.2): read it by name, so the where
    prompt appears the day the field lands, and nothing happens before."""
    raw = getattr(task, "missing", None)
    return frozenset(str(m) for m in raw) if raw else frozenset()

def is_urgent(state: ConversationState, settled: Settled) -> bool:
    """The code-built urgent booking after a burning "no" (graph-nodes §6; CAS-16 A: P2 burning_ruled_out)."""
```
`is_urgent` steps: (1) `gate = state.gate`; `ruled_out_now = gate is not None and gate.kind is tn.GateKind.BURNING_ANSWER
and gate.burning_answer == "no"`; (2) `case = settled.open_case`; (3) `return ruled_out_now or (case is not None and
case.reason is HandoffReason.BURNING_RULED_OUT)`. *Invariant: the flag survives the identity detour (burning "no" →
locate → code → windows on a later turn) because the P2 case stays open in `settled`.*

```python
def slot_card(
    ids: BlockIds, windows: Sequence[ShownSlot], *, task: OpenTask | None, urgent: bool, verified: bool
) -> b.SlotCardBlock | None:
```
1. If `task is None or not windows`: `return None` **before** calling `ids.kw()` or `ids.task_card()` (AC-2: no id is
   consumed).
2. `ordered = sorted(windows, key=lambda s: (s.date, s.window, s.slot_id))`.
3. `card_id = ids.task_card(task.task_id)`; `base = ids.kw()`.
4. Days: `itertools.groupby(ordered, key=lambda s: s.date)`; for each `(day, group)`: `ws = tuple(group)`;
   `b.SlotDay(date=day, label=f"{DOW3[day.weekday()]} {day.day} · {len(ws)} open", open_count=len(ws),
   windows=tuple(b.SlotWindow(slot_id=str(s.slot_id), date=s.date, window=s.window, window_label=window_label(s.window),
   technician=s.technician, member_only=s.member_reserved, taken=False) for s in ws))`.
   The separator is `" · "` (space, U+00B7, space), as in the OpenAPI example "Wed 21 · 2 open".
5. `options = tuple(b.Option(option=str(s.slot_id), label=window_label(s.window), disabled=False, reason=None) for s in ordered)`.
6. `fee = fee_note(ordered[0].service_type, "none")`; `standard_fee = b.Money(amount_cents=fee.amount_cents,
   display=format_usd(fee.amount_cents))` (estimate → `0`, `"$0"`).
7. `return b.SlotCardBlock(**base, card_id=card_id, options=options, answered=None, urgent=urgent, days=days,
   standard_fee=standard_fee, hint=TEXTS[TextId.SLOTS_NOT_HELD], members_note=None if verified else TEXTS[TextId.MEMBERS_NOTE])`.
   *Invariant: every shown window is open (the tool shows only open slots), so `taken` is always `False` and no "Full"
   day is ever emitted.*

```python
def slot_taken_error(
    ids: BlockIds, windows: Sequence[ShownSlot], *, task: OpenTask | None, urgent: bool, verified: bool
) -> b.ErrorBlock:
```
1. `base = ids.kw()` (the error's id comes first, as in the OpenAPI example blk-3 / blk-5).
2. `fresh = slot_card(ids, windows, task=task, urgent=urgent, verified=verified)`.
3. `return b.ErrorBlock(**base, code="SLOT_TAKEN", text=TEXTS[TextId.SLOT_TAKEN], tries_left=None, fresh_windows=fresh,
   person_key=fresh is None)`.

```python
def scheduling_cards(
    state: ConversationState, settled: Settled, ids: BlockIds
) -> tuple[list[b.ReplyBlock], b.Notice | None]:
    """Step 9 of compose: one block per scheduling result, then the where prompt when nothing else was shown."""
```
1. `blocks: list[b.ReplyBlock] = []`; `notice: b.Notice | None = None`; `task = open_scheduling_task(state)`;
   `verified = state.identity.status == "verified"`; `urgent = is_urgent(state, settled)`.
2. For `result in state.specialist_results`, skipping anything that is not a `SchedulingResult`:
   - `"out_of_area"` → `blocks.append(error_block(ids, "OUT_OF_AREA", TEXTS[TextId.OUT_OF_AREA]))` (moved, unchanged);
   - `"booking_cap"` and `notice is None` → `notice = make_notice("BOOKING_CAP", ("talk_to_person",))` and
     `blocks.append(notice_block(ids, "BOOKING_CAP", TEXTS[TextId.BOOKING_CAP]))` (moved, unchanged; once per reply);
   - `"slot_taken"` → `blocks.append(slot_taken_error(ids, result.windows, task=task, urgent=urgent, verified=verified))`;
   - `"windows_shown"` → `card = slot_card(...same args...)`; append when not `None`;
   - `"no_fit"` → `blocks.append(offer_block(ids, TEXTS[TextId.NO_WINDOW_FITS]))`;
   - any other status → nothing.
3. Where prompt: `if not blocks and task is not None and _ZIP_NEEDED in task_missing(task):`
   `card_id = ids.task_card(task.task_id)`; `blocks.append(where_prompt_block(ids, card_id))`.
4. `return blocks, notice`.

```python
def account_cards(ids: BlockIds, results: Sequence[SpecialistResult]) -> list[b.AccountCardBlock]:
    """Customer-facing account facts as cards (graph-tools §3): invoices as billed, membership, warranty."""
```
1. For each `r` in `results` that is an `AccountResult` with `r.status == "read"`, in order:
2. for each `inv` in `r.invoices`: append `b.AccountCardBlock(**ids.kw(), kind="invoice", invoice=b.AccountInvoice(
   invoice_id=str(inv.invoice_id), lines=tuple(b.AccountInvoiceLine(description=line.description,
   amount=exact_money(line.amount_cents), source=None) for line in inv.lines), total=exact_money(inv.total_cents),
   balance=exact_money(inv.balance_cents), due_on=inv.due_on, paid=inv.paid), membership=None, warranty=None)`;
3. `m = r.membership`; if `m is not None and m.tier in _TIER_LABELS and m.renewal_date is not None`: append
   `b.AccountCardBlock(**ids.kw(), kind="membership", invoice=None, membership=b.AccountMembership(
   tier=_TIER_LABELS[m.tier], renewal_date=m.renewal_date), warranty=None)`;
4. `w = r.warranty`; if `w is not None`: append `b.AccountCardBlock(**ids.kw(), kind="warranty", invoice=None,
   membership=None, warranty=b.AccountWarranty(install_date=w.install_date, sentence=w.sentence))`.
5. Return the list. *Invariant: reads only `invoices`, `membership`, `warranty`; the staff-only notes on the same result
   never reach a block (HP-3, AEA-21 AC-13).*

```python
def appointment_block(ids: BlockIds, visit: b.SettledVisit) -> b.AppointmentBlock:
    return b.AppointmentBlock(**ids.kw(), appointment_id=visit.appointment_id, date=visit.date,
                              window_label=visit.window_label, technician=visit.technician, fee_line=visit.fee_line)

def where_prompt_block(ids: BlockIds, card_id: str) -> b.WherePromptBlock:
    return b.WherePromptBlock(**ids.kw(), card_id=card_id, options=(), answered=None, label=_WHERE_LABEL,
                              submit_label=_WHERE_SUBMIT)

def urgency_questions_block(ids: BlockIds, card_id: str) -> b.UrgencyQuestionsBlock:
    """Built and tested, not wired: no state asks for the questions yet and nothing consumes the answers (plan R-2)."""
    return b.UrgencyQuestionsBlock(**ids.kw(), card_id=card_id, options=(_SKIP,), answered=None,
        questions=tuple(b.UrgencyQuestion(question_id=qid, text=TEXTS[tid], answers=_YES_NO_SKIP) for qid, tid in _URGENCY))
```

Imports for `compose_cards.py` (exactly these; ruff isort order):
`datetime as dt`, `itertools`, `collections.abc.Mapping, Sequence`, `types.MappingProxyType`, `typing.Literal, TypedDict`;
`from meridian.domain import blocks as b`, `from meridian.domain import turn as tn`,
`from meridian.domain.actions import Settled`, `from meridian.domain.common import HandoffReason`,
`from meridian.domain.records import ShownSlot`,
`from meridian.domain.specialists import AccountResult, SchedulingResult, SpecialistResult`,
`from meridian.domain.state import ConversationState, OpenTask`, `from meridian.policy.booking import fee_note`,
`from meridian.policy.texts import TEXTS, TextId, format_usd`.

### 4.4 `compose.py` after the change (what moves, what is wired)

1. **Delete** the definitions of `_ASSISTANT`, `_WINDOW_LABELS`, `_DOW3`, `_MON3`, `_ErrCode`, `_NoticeCode`,
   `_window_label`, `_Base`, `_Ids`, `_offer`, `_error`, `_notice_block`, `_notice`. Keep `_day`, `_date_in`, `_chip`,
   `_chips`, `_write_summary`, `_identity_status`, `_open_case`, `_effective_settled`, `_emergency_number`, `_reply`,
   every other constant, and the class.
2. **Import** from `meridian.agent.nodes.compose_cards`: `ASSISTANT, DOW3, MON3, BlockIds, BlockKw, ErrCode,
   account_cards, appointment_block, error_block, make_notice, notice_block, offer_block, scheduling_cards,
   window_label` (import only what `compose.py` still uses; ruff F401 decides — `NoticeCode` is not needed there).
3. **Rename the uses** (mechanical): `_ASSISTANT`→`ASSISTANT`, `_window_label(`→`window_label(`, `_DOW3`→`DOW3`,
   `_MON3`→`MON3`, `_Ids`→`BlockIds` (type hints and `halt_reply`), `_Base(`→`BlockKw(` (in `handoff_block`),
   `_offer(ids)`→`offer_block(ids)`, `_error(`→`error_block(`, `_notice_block(`→`notice_block(`,
   `_notice(`→`make_notice(`, `cast(_ErrCode, …)`→`cast(ErrCode, …)`. Drop `TypedDict` from the `typing` import.
4. Add one module constant: `_VISIT_INTENTS = frozenset({tn.TaskIntent.CONFIRM, tn.TaskIntent.READ_APPOINTMENTS})`.
5. `compose()` passes the effective settled to `_answer`: `return self._answer(state, ids, settled, writes, view)`;
   `_answer` signature becomes
   `def _answer(self, state: ConversationState, ids: BlockIds, settled: Settled, writes: tuple[CompletedAction, ...], view: b.SettledView) -> tn.ComposedReply:`.
6. Inside `_answer` (the numbered comments already there stay; insert the new ones):
   - delete the line `notice: b.Notice | None = None` (step 9 now assigns `notice`);
   - after step 4 (no source): `blocks.extend(account_cards(ids, state.specialist_results))  # 4a. account cards (AEA-21b)`;
   - after step 7 (write cards):
     ```python
     # 7a. the booked visit for a visit question, unless a write card already shows it (AEA-21b)
     wrote = any(isinstance(x, b.ConfirmationBlock | b.CancelledBlock) for x in blocks)
     if plan is not None and any(t.intent in _VISIT_INTENTS for t in plan.tasks) and not wrote and view.visit:
         blocks.append(appointment_block(ids, view.visit))
     ```
   - replace the whole step-9 `for` loop with:
     ```python
     # 9. scheduling results: errors, booking cap, slot card, SLOT_TAKEN, no fit, where prompt (AEA-21b)
     scheduled, notice = scheduling_cards(state, settled, ids)
     blocks.extend(scheduled)
     ```
   - step 11 condition becomes `if escalation is not None and escalation.outcome == "offer" and not any(isinstance(x, b.FailureOfferBlock) for x in blocks):`
     (AEA-21 §4.10 item 11 already said "no `FailureOfferBlock` yet"; the old `not fallback` is covered because a
     fallback turn already added one).
7. In `_quick_checks`: `card_id=ids.task_card(task.task_id)` instead of `card_id=f"{task.task_id}.1"` (first card of
   that task in the reply is still `.1`; `test_quick_checks_inline` keeps passing).
8. Update the module docstring's first paragraph to add: "Card builders live in `compose_cards.py` (AEA-21b)."

Resulting block order in step D (DO-4 §9 as AEA-21 built it, with the new items in **bold**): identity error →
verified line → main text / fallback offer → no-source → **account cards** → code prompt → locate prompt → write cards →
**appointment** → quick checks → **scheduling results (out of area, booking cap, SLOT_TAKEN, slot card, no fit, where
prompt)** → change request → offer → handoff card last.

---

## 5. Steps (build order; each ends with a check)

Work in the worktree the orchestrator created for this item (branch e.g. `aea-21b-compose-cards`).
`export UV_LINK_MODE=hardlink` once per shell. No baseline suite (main is green).

1. **Create `compose_cards.py` with the moved names only** (§4.3 "Moved unchanged" table + `BlockIds.task_card`), and
   switch `compose.py` to import them (§4.4 items 1–3, 7, 8). No new card yet.
   Check: `uv run ruff check src/meridian/agent/nodes && uv run mypy src/meridian/agent/nodes && uv run --with
   pytest-xdist pytest -n 2 tests/unit/agent/nodes/test_compose.py tests/unit/agent/nodes/test_compose_blocks.py
   tests/graph -q` → all pass (behaviour-neutral move).
2. **Add the new constants and functions** of §4.3 to `compose_cards.py` (`exact_money`, `open_scheduling_task`,
   `task_missing`, `is_urgent`, `slot_card`, `slot_taken_error`, `scheduling_cards`, `account_cards`,
   `appointment_block`, `where_prompt_block`, `urgency_questions_block`).
   Check: `uv run mypy src/meridian/agent/nodes`; `wc -l src/meridian/agent/nodes/compose_cards.py` ≤ 450.
3. **Write `compose_card_fixtures.py` and `test_compose_cards.py`** (§6, §7.1 A). Run them:
   `uv run pytest tests/unit/agent/nodes/test_compose_cards.py -q` → all pass.
4. **Wire compose** (§4.4 items 4–6). Check: `wc -l src/meridian/agent/nodes/compose.py` ≤ 690;
   `uv run mypy src/meridian/agent/nodes`.
5. **Write `test_compose_card_wiring.py`** (§7.1 B) and run it with the two existing compose test files.
6. **Gates, affected tests and journeys** (§7.3 G-1…G-6), then write the journey record (§7.4).
7. **Area map:** in `.claude/reference/area-map.md`, line 35 (the **first** `| 2 | **A7a Graph spine** |` row, whose
   Status cell starts "partly built (AEA-21, 6df4f4c)"), append to the end of the Status cell, before the closing
   ` |`: `; AEA-21b (wave fix, branch <your branch>): nodes/compose_cards.py actual (card builders split out of
   compose.py: slot card, SLOT_TAKEN, account, appointment, where prompt, urgency questions; card-number notice deferred)`.
   Touch nothing else in the file (the duplicate row on line 37 stays as it is).
8. **Commit** (explicit paths, never `git add -A`), two commits:
   - `git add src/meridian/agent/nodes/compose_cards.py src/meridian/agent/nodes/compose.py tests/unit/agent/nodes/compose_card_fixtures.py tests/unit/agent/nodes/test_compose_cards.py tests/unit/agent/nodes/test_compose_card_wiring.py`
     → `feat(graph): compose cards - slot, SLOT_TAKEN, account, appointment, where, no-fit (AEA-21b)`
   - `git add docs/testing/journeys/2026-10-21-AEA-21b.md .claude/reference/area-map.md`
     → `docs(AEA-21b): journey record and area map for compose_cards.py`
   Each message body: one paragraph of what and why; last line exactly
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push (the merge step pushes main).

---

## 6. Data and fixtures (synthetic or issued only)

`tests/unit/agent/nodes/compose_card_fixtures.py` (new). Import `compose_fixtures as fx` for `THREAD`, `TURN3`,
`TURN4`, `DEMO_NOW`, `make_ctx`, `state`, `facts`, `gate`, `handoff_result`, `passage`. No phone numbers, no codes,
no card-like numbers, no names beyond the issued technicians and customer ids. Builders (names binding):

| Builder | Returns | Values (source) |
|---|---|---|
| `BOOKING_TASK_ID = "task-1a2b3c4d-1"` | str | the id `facts` mints for `TURN3` order 1 (`reply.py`: `f"task-{str(turn_id)[:8]}-{order}"`) |
| `booking_task(status="open", intent=TaskIntent.BOOK_NEW, task_id=BOOKING_TASK_ID) -> OpenTask` | `OpenTask(task_id, specialist="scheduling", intent, opened_turn=fx.TURN3, details=TaskDetails(), status)` | |
| `wp3_windows() -> tuple[ShownSlot, ...]` | three `ShownSlot`s, **given in the order 58, 56, 42** (so the test proves the sort) | WP-3: `slot_id=56, date=dt.date(2026, 10, 19), window="08:00-12:00", technician="Marta Kowalski"`; `42, 2026-10-19, "12:00-16:00", "Ray Mendoza"`; `58, 2026-10-19, "13:00-17:00", "Marta Kowalski"`; all `service_type="hvac_repair", zone="north", member_reserved=False, shown_turn=fx.TURN4` |
| `wednesday_member_window() -> ShownSlot` | `slot_id=61, date=dt.date(2026, 10, 21), window="16:00-19:00", technician="Marta Kowalski", service_type="hvac_repair", zone="north", member_reserved=True, shown_turn=fx.TURN4` | synthetic |
| `scheduling(status, windows=()) -> SchedulingResult` | `SchedulingResult(status=status, windows=windows, tools=(), calls=())` | |
| `verified_identity() -> IdentityState` | `IdentityState(status="verified", customer_id=CustomerId("MHC-10001"), masked_hint="the phone ending in 01", code_expires_at=None, tries_left=3, codes_sent=1, verified_at=fx.DEMO_NOW)` | WP-3 customer (masked hint only) |
| `wp2_invoice() -> InvoiceView` | `InvoiceView(invoice_id=InvoiceId("INV-204411"), lines=(InvoiceLineView(description="Diagnostic visit", amount_cents=8900), InvoiceLineView(description="Contactor replacement", amount_cents=24500), InvoiceLineView(description="After-hours dispatch", amount_cents=14400)), total_cents=47800, balance_cents=47800, issued_on=dt.date(2026, 10, 2), due_on=dt.date(2026, 11, 1), paid=False)` | WP-2 (issued DB) |
| `account_read(*, invoices=(), membership=None, warranty=None, staff_notes=()) -> AccountResult` | `AccountResult(status="read", invoices=…, membership=…, warranty=…, staff_notes=…, tools=(), calls=())` | |
| `warranty() -> WarrantyView` | `WarrantyView(install_date=dt.date(2025, 6, 2), equipment_brand=None, sentence="Labor is covered for 2 years from the install date; a representative can confirm whether the 5-year term applies.")` | OpenAPI ACCOUNT_WARRANTY example text |
| `booked_action(turn=fx.TURN3) -> CompletedAction` | `BOOKED` action for appointment `"30412"`, `records={"appointment": "30412", "slot": "56"}`, `after={"date": "2026-10-19", "window": "08:00-12:00", "technician": "Marta Kowalski", "service_type": "hvac_repair", "fee_line": "Diagnostic fee: waived for Comfort Club members (normally $89)"}`, `at=fx.DEMO_NOW - dt.timedelta(minutes=5)` | WP-3 booked visit (fee line = `fee_note("hvac_repair", "standard").line`) |
| `ruled_out_case() -> OpenCase` | `OpenCase(case_ref=CaseRef("MHC-C-0009"), reason=HandoffReason.BURNING_RULED_OUT, priority=Priority.P2, state="unassigned", promise=fx.handoff_result("R26.unstaffed", "A person will call.").case.promise, followup=None, live_queued=False)` | CAS-16 A |
| `assert_matches_openapi(block: b.ReplyBlock) -> None` | validates `block.model_dump(mode="json")` with `Draft202012Validator(ref_schema("/components/schemas/ReplyBlock"), registry=load_contract().registry)`; `errors = [e.message[:200] for e in validator.iter_errors(...)]`; `assert errors == []` | imports: `from jsonschema import Draft202012Validator`, `from tests.api.openapi_check import load_contract`, `from tests.contract.openapi_variants import ref_schema` |
| `class TaskWithMissing(OpenTask)` | test-only subclass with `missing: tuple[str, ...] = ()` | stands in for DO-4 §1's field until AEA-02 adds it |

Sentinel for the staff-note test: `_STAFF_SENTINEL = "SENTINEL-STAFF-NOTE-21B"` in a `StaffNote(kind="diagnostic_without_credit",
record_id=InvoiceId("INV-204411"), text=_STAFF_SENTINEL, source_file="faq/customer_faq.md")`.

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (names binding)

**A. `tests/unit/agent/nodes/test_compose_cards.py`** (pure builders; `ids = BlockIds(fx.make_ctx())`)

| Test | Asserts |
|---|---|
| `test_slot_card_groups_windows_by_day` | `slot_card(ids, wp3_windows(), task=booking_task(), urgent=False, verified=True)`: `card_id == "task-1a2b3c4d-1.1"`; `[o.option for o in options] == ["56", "42", "58"]`; one day, `date == 2026-10-19`, `label == "Mon 19 · 3 open"`, `open_count == 3`; windows' `(slot_id, technician, window_label)` == `("56", "Marta Kowalski", "8:00 am – 12:00 pm")`, `("42", "Ray Mendoza", "12:00 pm – 4:00 pm")`, `("58", "Marta Kowalski", "1:00 pm – 5:00 pm")`; all `taken is False`; `standard_fee == Money(amount_cents=8900, display="$89")`; `hint == TEXTS[TextId.SLOTS_NOT_HELD]`; `members_note is None`; `urgent is False`; `block_id == f"blk-{fx.TURN4}-1"`. Then the same call with `verified=False, urgent=True` on a fresh `BlockIds`: `members_note == TEXTS[TextId.MEMBERS_NOTE]`, `urgent is True` |
| `test_slot_card_member_window_one_open_day_and_estimate_fee` | windows `(*wp3_windows(), wednesday_member_window())`: two days, second label `"Wed 21 · 1 open"`, its window `member_only is True`; a single estimate window (`service_type="estimate"`) gives `standard_fee == Money(amount_cents=0, display="$0")` |
| `test_slot_card_omitted_without_windows_or_task` | `slot_card(ids, (), task=booking_task(), …) is None`; `slot_card(ids, wp3_windows(), task=None, …) is None`; then `ids.kw()["block_id"] == f"blk-{fx.TURN4}-1"` and `ids.task_card("task-1a2b3c4d-1") == "task-1a2b3c4d-1.1"` (nothing consumed) |
| `test_slot_taken_error_with_and_without_fresh_windows` | with `wp3_windows()`: `code == "SLOT_TAKEN"`, `text == TEXTS[TextId.SLOT_TAKEN]`, `tries_left is None`, `person_key is False`, `fresh_windows` is a `SlotCardBlock` with three options, error `block_id` ends `-1` and the card's ends `-2`; with `()`: `fresh_windows is None`, `person_key is True` |
| `test_wp2_invoice_card_as_billed` | `account_cards(ids, [account_read(invoices=(wp2_invoice(),))])` → one card, `kind == "invoice"`, `invoice_id == "INV-204411"`, line displays `["$89.00", "$245.00", "$144.00"]`, every line `source is None`, `total.display == balance.display == "$478.00"`, `due_on == 2026-11-01`, `paid is False`, `membership is None and warranty is None` |
| `test_membership_and_warranty_cards_and_omitted_variants` | `standard` + renewal 2026-11-03 → tier `"Comfort Club (Standard)"`; `plus` → `"Comfort Club Plus"`; `tier="none"` → no card; `renewal_date=None` → no card; warranty → `install_date == 2025-06-02`, `sentence` equal to the fixture text; invoice with `lines=()` → card with `lines == ()`; `AccountResult(status="not_verified", …)` and `"failed"` → `[]`; order for one result with all three: invoice, membership, warranty |
| `test_exact_money_formats_cents_thousands_and_credits` | `exact_money(8900).display == "$89.00"`, `exact_money(125000).display == "$1,250.00"`, `exact_money(-1250).display == "-$12.50"`, `exact_money(5).display == "$0.05"` |
| `test_where_prompt_and_urgency_question_shapes` | `where_prompt_block(ids, "t-1.1")`: `label == "ZIP code or city"`, `submit_label == "Show windows"`, `options == ()`, `answered is None`; `urgency_questions_block(ids, "t-1.2")`: question ids `["temp", "water", "risk"]`, texts `[TEXTS[URGENCY_HOT_COLD], TEXTS[URGENCY_WATER], TEXTS[URGENCY_AT_RISK]]`, each answers `["yes", "no", "skip"]`, `options` `["skip"]`, `skippable is True` |
| `test_task_card_ids_count_per_task` | `task_card("t-1")` → `"t-1.1"`, `"t-1.2"`; `task_card("t-2")` → `"t-2.1"`; `card_target("t-1.2") == ("task", "t-1")` (from `meridian.gates.gate`) |
| `test_new_blocks_match_openapi` | parametrized (ids are the case names) over: slot card verified, slot card unverified + urgent, SLOT_TAKEN with fresh, SLOT_TAKEN without, invoice card, invoice card with no lines, membership card, warranty card, appointment block (from `Settled(actions=(booked_action(),), …).current_visit()` turned into `b.SettledVisit` via `ReplyComposer().settled_view(...)`.visit), where prompt, urgency questions, no-fit `offer_block(ids, TEXTS[TextId.NO_WINDOW_FITS])` → `assert_matches_openapi(block)` |

**B. `tests/unit/agent/nodes/test_compose_card_wiring.py`** (`COMPOSER = ReplyComposer()`; states from `fx.state(...)`;
`checked(text)` as in `test_compose_blocks.py`, defined locally)

| Test | State | Asserts |
|---|---|---|
| `test_wp3_slot_card_on_code_turn` (**WP-3, this slice's worked pair**) | `gate=fx.gate(GateKind.CODE_ENTRY)`, `identity=verified_identity()`, `plan=Plan(mode="act", tasks=(PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=False, resumes_task_id=BOOKING_TASK_ID),), handoff_request=None, topic="booking", source="card_choice")`, `specialist_results=[scheduling("windows_shown", wp3_windows())]`, `open_tasks=[booking_task()]`, `facts=fx.facts(windows_shown=wp3_windows())`, `checked=checked("There's no Saturday evening window, so here are the earliest repair windows.")` | block types `[TextBlock, SlotCardBlock]`; the card as in A row 1 (`members_note is None`); `reply.path == "code"`, `reply.outcome == "acted"`; `reply.writes == ()` |
| `test_j3_slot_card_choice_resumes_booking_task` (**J-3 card path**, AC-11) | the state above; `card = <its SlotCardBlock>` | `intake = parse_intake(ChoicePayload(card_id=card.card_id, option="56"))`; `decision = decide_gate(intake, flags_from_state(st))`; `decision.kind is GateKind.CARD_CHOICE` and `decision.resume_task_id == BOOKING_TASK_ID`; `sends = route_after_gates(st.model_copy(update={"gate": decision, "plan": None}))`; `isinstance(sends, list) and len(sends) == 1`; `planned = sends[0].arg["planned"]`; `planned.resumes_task_id == BOOKING_TASK_ID`, `planned.intent is TaskIntent.BOOK_NEW`; print the card id and the routed task |
| `test_wp3_slot_taken_shows_fresh_windows` | as WP-3 state but `specialist_results=[scheduling("slot_taken", wp3_windows()[1:])]` | one `ErrorBlock` `SLOT_TAKEN` whose `fresh_windows.options` are `["42", "58"]`; no `ConfirmationBlock`; no top-level `SlotCardBlock` |
| `test_no_fit_offers_a_person_once` | `gate=FREE_TEXT`, `specialist_results=[scheduling("no_fit")]`, `open_tasks=[booking_task()]`, `escalation=EscalationDecision(outcome="offer", reason=None, priority=None, rule_id="AI.failed_answers")`, `facts=fx.facts()`, `checked=checked("Ok.")` | exactly one `FailureOfferBlock`, its `text == TEXTS[TextId.NO_WINDOW_FITS]`, `person_key is True`; `reply.degrade_reason is None` |
| `test_urgent_after_burning_ruled_out` | (a) `gate=fx.gate(GateKind.BURNING_ANSWER, burning_answer="no")` + windows + task; (b) `gate=CODE_ENTRY`, `settled=Settled(actions=(), open_case=ruled_out_case(), read_at=fx.DEMO_NOW)` + windows + task; (c) WP-3 state | slot card `urgent` is `True`, `True`, `False` |
| `test_wp2_invoice_card_after_verified_line` | `gate=CODE_ENTRY`, `identity_step=Verified(customer_id=CustomerId("MHC-10002"), action=<a VERIFIED action for TURN4>)`, `specialist_results=[account_read(invoices=(wp2_invoice(),))]`, `facts=fx.facts()`, `checked=checked("Here is invoice INV-204411 as billed.")` | block types `[TextBlock, TextBlock, AccountCardBlock]`, the first text `== TEXTS[TextId.VERIFIED]` |
| `test_wp8_membership_card` | `specialist_results=[account_read(membership=MembershipView(tier="standard", renewal_date=dt.date(2026, 11, 3)))]` | one membership card, `renewal_date == 2026-11-03`, tier `"Comfort Club (Standard)"` |
| `test_account_card_never_carries_staff_notes` | `account_read(invoices=(wp2_invoice(),), staff_notes=(<sentinel note>,))` | `_STAFF_SENTINEL not in reply.model_dump_json()`; an `AccountCardBlock` is present |
| `test_appointment_card_only_for_a_visit_question_without_a_write` | `settled=Settled(actions=(booked_action(),), open_case=None, read_at=fx.DEMO_NOW)`; plan with one `PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.CONFIRM, needs_identity=True)` | one `AppointmentBlock` with `appointment_id == 30412`, `window_label == "8:00 am – 12:00 pm"`, `label == "Your booked visit"`. Variants: intent `READ_APPOINTMENTS` (`specialist="account"`) → one card; a talk plan → none; `settled` with no actions → none; the `booked_action(turn=fx.TURN4)` (a write this turn) → one `ConfirmationBlock` and **no** `AppointmentBlock` |
| `test_where_prompt_reads_task_missing` | `open_tasks=[TaskWithMissing(**booking_task().model_dump(), missing=("zip_needed",))]`, `specialist_results=[]`, `gate=FREE_TEXT`, `facts=fx.facts()`, `checked=checked("Where is the visit?")` | one `WherePromptBlock` with `card_id == "task-1a2b3c4d-1.1"`; with `open_tasks=[booking_task()]` → none; with `missing=("zip_needed",)` **and** `scheduling("windows_shown", wp3_windows())` → a slot card and **no** where prompt |
| `test_quick_checks_and_slot_card_get_distinct_card_ids` | `gate=FREE_TEXT`, `open_tasks=[booking_task()]`, `facts=fx.facts(quick_checks=(PassageId("faq/troubleshooting_before_you_call.md#1"),), passages=(fx.passage("faq/troubleshooting_before_you_call.md#1", "Check the thermostat."),))`, `specialist_results=[scheduling("windows_shown", wp3_windows())]` | `QuickChecksBlock.card_id == "task-1a2b3c4d-1.1"`, `SlotCardBlock.card_id == "task-1a2b3c4d-1.2"` |

Imports for B (beyond fixtures): `from meridian.agent.nodes.compose import ReplyComposer`, `from meridian.agent.routers
import route_after_gates`, `from meridian.gates.gate import decide_gate, flags_from_state, parse_intake`,
`from meridian.domain.turn import ChoicePayload, EscalationDecision, GateKind, Plan, PlannedTask, TaskIntent`,
`from meridian.domain.identity import Verified`, `from meridian.domain.specialists import MembershipView, StaffNote`.

### 7.2 Existing tests that must stay green

`tests/unit/agent/nodes/test_compose.py`, `tests/unit/agent/nodes/test_compose_blocks.py` (both unedited),
`tests/graph/test_spine.py`, `tests/graph/test_run_graph.py`, `tests/unit/agent/nodes/test_act.py`,
`tests/unit/agent/nodes/test_plan_graph.py`, the other `tests/unit/agent/**` files, `tests/contract/test_prompts_vs_consumers.py`,
`tests/services/test_cases_contract.py`. If one goes red, the move or the wiring changed behaviour: fix the code, never
the existing test.

### 7.3 Gates (cheapest first; stop at the first red; `export UV_LINK_MODE=hardlink`; never `-n` above 2)

| # | Command | Pass looks like |
|---|---|---|
| G-1 | `uv run ruff check src/meridian/agent/nodes tests/unit/agent/nodes && uv run ruff format --check src/meridian/agent/nodes tests/unit/agent/nodes` | no findings (run `uv run ruff format <files>` on your own files first) |
| G-2 | `uv run mypy src/meridian/agent tests/unit/agent tests/graph` | `Success: no issues found` |
| G-3 | `uv run --with pytest-xdist pytest -n 2 tests/unit/agent tests/graph tests/contract/test_prompts_vs_consumers.py tests/services/test_cases_contract.py -q -rs` | 0 failed; skips only with their existing reasons |
| G-4 | `uv run python -m tests.journeys.affected --base main` | prints the affected journeys (expect J-2 and J-3 files that import compose, e.g. `tests/journeys/j2/test_aea_38.py`, `tests/journeys/j3/test_aea_34.py`, `tests/journeys/j3/test_aea_39.py`, `tests/journeys/j4/test_aea_39.py`) and runs them: 0 failed |
| G-5 | `wc -l src/meridian/agent/nodes/compose.py src/meridian/agent/nodes/compose_cards.py tests/unit/agent/nodes/compose_card_fixtures.py tests/unit/agent/nodes/test_compose_cards.py tests/unit/agent/nodes/test_compose_card_wiring.py` and `grep -c "staff_notes" src/meridian/agent/nodes/compose.py src/meridian/agent/nodes/compose_cards.py` | ≤ 690, ≤ 450, ≤ 200, ≤ 450, ≤ 450; both counts `0` |
| G-6 | `grep -c "SlotCardBlock(\|AccountCardBlock(\|AppointmentBlock(\|WherePromptBlock(\|UrgencyQuestionsBlock(" src/meridian/agent/nodes/compose_cards.py` | ≥ 5 (AEA-51's own pre-check reads this) |

No full suite: nothing here reaches everything (no fixture, settings, dependency or cross-package module change).

### 7.4 Journey record: `docs/testing/journeys/2026-10-21-AEA-21b.md`

Title `# Journey record: AEA-21b compose cards (slot, SLOT_TAKEN, account, appointment, where, no-fit)`, then the table:

| Field | Value to write |
|---|---|
| Claim | AEA-21b: compose builds the slot card (incl. urgent, members note), `SLOT_TAKEN` with fresh windows, account cards (invoice as billed, membership, warranty), the appointment card, the no-fit person offer and the where prompt (read from `OpenTask.missing` once it exists); the slot card's id routes back to the open booking task (J-3 card path). Card-number notice not built (plan R-1) |
| Level | `mock-tested` (the composer and the real gate and router functions on typed states; no server path runs the graph until AEA-51 binds it) |
| Tested revision | the commit SHA that adds this record (or "uncommitted" if written before the commit) |
| Environment | host, Python 3.12, uv; no server; no model adapter; no DB |
| Command | G-3 and G-4 exactly as run |
| Result | pass/fail counts of G-3 and G-4; the printed card id and routed task of `test_j3_slot_card_choice_resumes_booking_task` |
| Evidence location | this file plus the pytest output |
| Remaining limitations | no browser or real-server run; appointment card only for visits booked in this chat (R-4); where prompt waits for `OpenTask.missing` (R-3); urgency questions not wired (R-2); card-number notice deferred (R-1) |
| Blocked by | AEA-51 (graph bound into the app → J-2/J-3 at `integrated with a scripted model`); AEA-62 (browser legs of J-2/J-3) |

### 7.5 Evidence to report back

Branch and the two commit SHAs; G-1…G-6 output (counts, line counts); the journey record path; the list of affected
journeys G-4 ran; any deviation from this plan with its reason.

---

## 8. Risks and requests

### 8.1 Plan decisions (engineering; each reversible)

| ID | Decision | Basis |
|---|---|---|
| PD-21b-1 | Split into `nodes/compose_cards.py`; the shared labels and block-id helpers move there with public names; `compose.py` imports them (one direction) | `compose.py` at 695/700 (`code-structure`); orchestrator instruction "split into agent/compose_cards.py"; no new interface or seam (same module group, plain functions) |
| PD-21b-2 | `standard_fee` = `fee_note(service_type of the first shown window, "none")`, display `format_usd`; invoice amounts use `exact_money` (two decimals) | OpenAPI SLOT_CARD (`$89`) vs VERIFIED_ACCOUNT_INVOICE (`$89.00`); AEA-62 J-2 checks `$89.00` |
| PD-21b-3 | Tier labels from the KB headings: `standard` → "Comfort Club (Standard)", `plus` → "Comfort Club Plus"; tier `none` or no renewal date → no membership card | `MembershipView.tier` is a code; `AccountMembership.renewal_date` is required; the OpenAPI "Comfort Plus" is an illustration |
| PD-21b-4 | `members_note` present exactly when identity is not `verified` | OpenAPI SLOT_CARD vs SLOT_CARD_MEMBER; the SLOT_TAKEN example shows a note with a verified customer, which this plan treats as illustrative (no contract change) |
| PD-21b-5 | `urgent` = burning "no" this turn, or an open `burning_ruled_out` case | graph-nodes §6; CAS-16 A (D-14); SCREEN_SPECS "slot card marked Urgent" |
| PD-21b-6 | Task card numbers count per task per reply (`BlockIds.task_card`) | graph-core §3 `<task_id>.<n>`; quick checks and slot card can share a turn |
| PD-21b-7 | No fit → `FailureOfferBlock(NO_WINDOW_FITS)`; the escalation offer is skipped when any `FailureOfferBlock` is already in the reply | SCREEN_SPECS "No window fits … + person offer"; AEA-21 §4.10 item 11 wording |
| PD-21b-8 | `SLOT_TAKEN` `person_key = fresh_windows is None` | OpenAPI SLOT_TAKEN (`false` with windows); with nothing to pick, the person key is the way on |
| PD-21b-9 | Appointment card from `settled_view.visit` on a `CONFIRM`/`READ_APPOINTMENTS` task, never beside a write card | OpenAPI APPOINTMENT (card = `settled.visit`); FLOW-6 |
| PD-21b-10 | Where prompt reads `OpenTask.missing` by name (`getattr`), only when no scheduling block was shown | DO-4 §1; same tolerance stance as AEA-21 (`last_lookups`) and `act.py` `_has_pending_change` |
| PD-21b-11 | Urgency questions: builder only, not wired | No state asks for them and nothing consumes the answers (R-2) |
| PD-21b-12 | Invoice line `source = None` | `AccountResult` carries no line → passage link; inventing one by text matching would be fragile |

### 8.2 Requests to the orchestrator

- **R-1 (card-number notice; needs UX words → Innocent).** The state exists (`TurnInput.card_number_seen`, set by
  `parse_intake` when redaction removed a card-like number), and system-design says "the reply says cards aren't taken
  in chat" (R-13; audit K-17, L-4). But no customer sentence exists in `policy/texts.py` (frozen; "a missing sentence is
  a small follow-up ticket"), no UX copy exists for it in `UI_CONTRACTS.md` / `SCREEN_SPECS.md`, and the signed
  `Notice`/`NoticeBlock` code enums have no card-number value, so the reply must be a `TextBlock`. Proposed follow-up
  **AEA-03c (texts)**: add `TextId.CARD_NOT_TAKEN = "limits.card_not_taken"` with UX-approved words (proposal for
  Innocent: "I can't take card numbers in this chat, so I removed it. Payments go through a secure link, never the
  chat."), then a 3-line compose hunk after step 3: `if state.turn_input.card_number_seen:
  blocks.append(b.TextBlock(**ids.kw(), text=TEXTS[TextId.CARD_NOT_TAKEN], sources=()))` plus one test. Not blocking
  J-2/J-3.
- **R-2 (urgency questions: no producer, no consumer).** WP-3 (checked by Innocent) says the skippable urgency details
  "get asked once, and go into the booking note"; FLOW-5 puts them after the quick-check offer. Nothing on `main` asks
  for them (no state, no `MissingInfo` value) or stores the answers (no booking-note field; `BookVisitArgs.issue` is
  model-written). The builder is ready (`urgency_questions_block`). A ticket must define the trigger (e.g. a
  `MissingInfo` value or a facts flag on the BOOK_NEW turn), the answer handling (a `CARD_CHOICE` on `<task>.<n>` with
  the `yes/no/skip` options) and where the answers go. Owner suggestion: AEA-08 (contract), then AEA-39/AEA-28 + a
  one-line compose wiring.
- **R-3 (where prompt state; FLOW-5 order).** `OpenTask.missing` / `MissingInfo` (DO-4 §1, §8) were deferred by AEA-02
  (its §8.2) and AEA-02b built only the view types, so the where prompt cannot appear yet. Also, `join_plan` and the
  burning-"no" plan set `needs_identity=True` for every scheduling task (`plan.py`, `front.py:70`), so the code comes
  **before** the windows, while FLOW-5 (UX-2 finding R1-1, a proposal) and the OpenAPI SLOT_CARD example ("Windows in
  the zone, before the code") show windows first. J-3 (AEA-62) is written code-first, so nothing here is blocked; the
  divergence should be recorded by AEA-08 and, if windows-before-code is wanted, put to Innocent.
- **R-4 (appointment card for visits not booked in this chat).** `SchedulingResult` carries no appointment views, so a
  "confirm my visit" for a phone-booked appointment (WF FLOW-6 on an issued appointment) shows no card; the responder's
  words still answer it. A follow-up could add `appointments: tuple[AppointmentView, ...] = ()` to `SchedulingResult`
  (DO-4 §5 change, AEA-02 + AEA-35) and a compose branch.
- **R-5 (AEA-08 reconcile).** Add `agent/nodes/compose_cards.py` to DO-3 §3's tree under A7a; record PD-21b-2…12 beside
  graph-core §13.

### 8.3 Collisions with other slices

| Surface | Sibling | Handling |
|---|---|---|
| `compose.py` | none open (checked every local branch at `2f70221`) | this slice is the only writer |
| `.claude/reference/area-map.md` A7a row | AEA-51 marks rows "integrated (AEA-51)" | append-only clause; a conflict is resolved by keeping both (build-loop rule) |
| `docs/testing/journeys/` | every ticket adds its own dated file | new file name is unique |
| AEA-51 pre-check (`grep -c "SlotCardBlock(\|AccountCardBlock(\|AppointmentBlock(" src/meridian/agent/nodes/compose.py`, expects ≥ 3) | AEA-51 plan line 707 | the constructors now live in `compose_cards.py`; **tell AEA-51's planner/implementer to grep `src/meridian/agent/nodes/compose_cards.py`** (G-6 proves ≥ 5 there) |

### 8.4 Other risks

- **Behaviour drift during the move.** Step 1 runs the two existing compose test files and `tests/graph` before any new
  code; any red there is a move mistake.
- **Line cap.** If `compose.py` exceeds 690 after step 4, move `_code_prompt` and `_quick_checks` bodies into
  `compose_cards.py` as `code_prompt_block(state, ids)` / `quick_checks_block(state, ids)` with identical behaviour;
  do not shorten by removing comments that carry plan ids.
- **`card_target` greediness.** Task ids contain `-` and digits; the regex `(?P<task>.+)\.(?P<n>[0-9]+)` takes the last
  `.`; task ids never contain `.` (`reply.py` mints `task-<8 hex>-<order>`). `test_task_card_ids_count_per_task` pins it.
- **OpenAPI validator import** reaches into `tests/contract/openapi_variants.py`; if that module's import becomes
  heavy or circular, copy its two-line `ref_schema` into `compose_card_fixtures.py` instead (same `CONTRACT_URI`).

---

## 9. Readiness

**READY** for the implementer, against `main` `47da752` (re-checked: the merges after `2f70221` touch no planned surface except the area map, whose A7a row is unchanged). Every type used is merged (AEA-02, AEA-02b, AEA-13 `fee_note`,
AEA-35 results, AEA-38 facts, AEA-39 act, AEA-12 gate). No signed contract changes; no decision taken at sign-off
(D-4…D-15) is answered differently (CAS-16 option A drives `urgent`).

Not in this slice, by design: the **card-number notice** waits on a texts follow-up with UX words (R-1, Innocent's
copy); the **urgency questions** are built but unwired until a producing state exists (R-2); the **where prompt** lights
up when `OpenTask.missing` lands (R-3). None of these blocks J-2, J-3, AEA-51 or AEA-62.

**Gates:** none (no human, paid or live gate). No security review (not `risk::security`).
