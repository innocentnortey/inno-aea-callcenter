## [AEA-28] scheduling: windows, writes, change requests

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

> **US-10 · Book a repair or tune-up that fits my area, my membership and my day.** "As a **homeowner**, I need to see
> open windows in my zone (member-reserved ones if I'm a member), pick one, and get a confirmation with the date, window,
> technician and the fee that applies to me." Acceptance: "only valid slots are offered; a slot taken meanwhile gives
> alternatives, never a double booking; out-of-area gets an honest no."
>
> **US-12 · Move my visit: myself when it's free, through a person when it costs $49.** Acceptance: "a fee-free move
> confirms the new window; a fee-bearing request shows 'the $49 fee applies under current policy', 'your original
> appointment stays until a representative confirms', and a reference." Also US-11 (estimates) and US-13 (confirm or
> cancel).

**Example pairs (issued DB, read 2026-10-21; `docs/data/worked-pairs.md`):**
- **WP-3** (Innocent ✓ 2026-10-20): verified **MHC-10001 Linda Foster**, Round Rock → north zone, standard member, wants
  `hvac_repair` "This Saturday … 4 to 7". **Output** of `find_windows`: `WindowsFound(zone="north", exact_fit=False, …)`:
  no 16:00–19:00 window on Saturday (that window is Tue/Thu only) and no north repair slot on Sat 10/17 or Sun 10/18; the
  earliest offered are **slot 56** Mon 2026-10-19 08:00–12:00 Marta Kowalski, **slot 42** Mon 12:00–16:00 Ray Mendoza,
  **slot 58** Mon 13:00–17:00 Marta Kowalski. Booking the one she picks returns a `WriteResult` whose confirmation has
  date, window and technician, and a `FeeNote` with the diagnostic fee **waived (member)**.
- **WP-4** (decided D3, revised Stage 3): verified **MHC-57204**, appointment **1** on slot 2, **2026-10-16 12:00–16:00**,
  demo clock 2026-10-16 10:00 (two hours before). `move` and `cancel` return `Refused(code="fee_bearing",
  hours_before=2.0)` and write nothing; `request_change` returns a `ChangeRequestDraft` with `hours_before` 2.0,
  `window_start` 2026-10-16T12:00-05:00, the windows shown **not held**, and the appointment untouched. **WP-4F**
  (fee-free variant): appointment **94** on 2026-10-23 08:00–12:00 is more than 24 hours out, so `move` to a shown slot
  writes it.

The only writer of slots and appointments in the working copy (DO-2 §A.5), with every booking rule in code (HP-3). The
types are defined in [`stage7/cases.md`](../../design/contracts/stage7/cases.md) §4 and §4.1 ("cases §n") and the
executor rules in [`stage7/graph-tools.md`](../../design/contracts/stage7/graph-tools.md) §1, §3:

1. **`adapters/sqlite/repos_booking.py`** (body of AEA-02's shell, over the issued tables the working copy holds and the
   `50_booking.sql` that **AEA-10 writes**; slice plan §0, MC-10; CAS-36): `BookingRepos(conn)` holding `SlotsRepo`
   (`search(zone, service_type, *, member, earliest, latest, window, limit)`: status `open`, plus `reserved_members` when
   `member`, ordered by date, window, id, read-only; `get_for_update(slot_id)`; `set_status`), `AppointmentsRepo`
   (`insert(slot_id, customer_id, issue_description, created_at) -> int` with status `scheduled`, `get`,
   `for_customer` (status `scheduled`, by slot date), `views_for_customer(customer_id) -> tuple[AppointmentView, ...]`
   (joins slots and technicians; no issue text, no customer id; cases §4.1, R-G-19), `move`, `set_status`) and
   `TechniciansRepo.name(tech_id)`, all over
   the unit of work's one connection; `Slot` and `Appointment` are AEA-02's (`domain/records.py`).
2. **`services/scheduling.py`** (cases §4; CAS-17): the five types `WindowQuery`, `WindowsFound`, `OutOfArea`,
   `SlotTaken`, `Refused` are **defined here**, beside the service (only this issue's files read them), and
   `SchedulingService` keeps DO-4 §14's five method signatures and adds `slice_inputs` (cases §4, R-G-19); each method
   opens and commits its own transaction. The
   constructor receives the unit-of-work factory and the booking cap from AEA-01's `Limits` (code-design :307 "booking
   cap 3", proposal; PRD R-41 "a cap on bookings per session"); parameter names are this issue's own, bound in its
   `register_scheduling()` hunk.
   - `find_windows(query, now)` → `WindowsFound | OutOfArea`: zone from `policy/booking.zone_for(query.zone_hint)`
     (AEA-13; `None` → `OutOfArea(reason="not_served" | "unknown_location")`, the input string never stored; Lakeway
     and its ZIPs 78734, 78738 are not served, cases §2); `open` slots of the requested service type in that zone, plus
     `reserved_members` only for `member_tier` `standard` or `plus` (from the verified customer; `none` when unverified,
     R-14); the requested fit first, then the earliest alternatives, at most `query.limit` (3 [A]); `exact_fit=False`
     when the request can't be met (R-18). Read-only: the zone-only search works unverified with the standard fee (US-10).
   - `book(key, scope, slot_id, issue, lookup)`, `move(key, scope, appointment_id, new_slot_id, lookup)`,
     `cancel(key, scope, appointment_id, lookup)` → `WriteResult | SlotTaken | Refused` (`cancel`: `WriteResult |
     Refused`): **one write transaction = slot re-read (`get_for_update`) + write + `actions` row + `lookup_log` row**
     (DO-1 §9; R-19). Refusals, checked before any write: `not_shown` (slot not in `scope.shown_slot_ids`),
     `outside_service_area`, `wrong_service_type`, `booking_cap` (a fourth booking in the conversation; the count is read
     in the same transaction), `not_owned` (another customer's appointment), and for `move` / `cancel` `fee_bearing`
     (`policy/booking.fee_bearing(hours_before(scope.now, …))`, under 24.0 h on the demo clock, exactly 24.0 h is free;
     R-21, R-22; CAS-6) with `Refused.hours_before` set. An unverified scope is refused before any read of private rows.
     A slot no longer free → `SlotTaken(slot_id, alternatives)` with fresh windows read in the same transaction. `move`
     and `cancel` free the old slot to `open` (`SCHEMA.md`); `WriteResult.confirmation` carries date, window,
     technician (`TechniciansRepo.name`) and `policy/booking.fee_note(service_type, tier)` (R-20); estimates book only
     `estimate` slots (R-23). Idempotent on `ActionKey`: a repeated turn finds the `actions` row and writes nothing
     (DO-4 §1).
   - `request_change(key, scope, appointment_id, change, wanted_text, lookup)` → `ChangeRequestDraft | Refused`: records
     `actions(change_request_sent)` + the `lookup_log` row in one transaction (DO-1 §5.2 step 5) and changes **no**
     appointment or slot row (R-21: "never moves it, even on a yes"); `ChangeRequestDraft.window_start` feeds the case's
     internal due time (`case_due_at`, cases §3.2; AEA-29 opens the case).
   - `slice_inputs(customer_id)` → `SchedulingSliceInputs` (cases §4, R-G-19; the type and `AppointmentView` are
     AEA-02's domain types, graph-tools §3, `domain/specialists.py`): one read-only unit of work; `zone` from
     `zone_for(zip, else city)`, `member = membership_tier != "none"`, `appointments` from `views_for_customer`; an
     unknown customer gives `SchedulingSliceInputs(zone=None, member=False, appointments=())`. The act node (AEA-39) calls
     it for a verified scheduling task only and fills `SchedulingSlice.customer_zone`, `.member`, `.appointments`.
3. **`agent/tools/scheduling.py`** (graph-tools §1, C-7; GRT-1): the factory `scheduling_tools(scheduling) ->
   tuple[ToolDef, ...]` (no global or import-time registry; AEA-51 builds the `ToolRegistry`; tool names are this
   issue's choice) with one tool per `ToolKind` of the scheduling specialist (graph-tools §2: `slot_search`, `book`,
   `move`, `cancel`, `change_request`); `slot_search` is `effect` `"read"` and the only one with
   `requires_verified=False` (R-14); the four others are `"write"`. Args models carry no customer field. The read
   returns its `LookupEntry` with `lookup_written=False` for dispatch (AEA-22) to write; the writes pass the `LookupEntry`
   into the service and return `lookup_written=True` (DO-4 §5 lookup-log rule). `Refused.code` maps one-to-one to the
   same-named `ToolErrorCode` (graph-tools §1 adds `wrong_service_type`, `not_owned`), `SlotTaken` to `slot_taken` and
   `OutOfArea` to `outside_service_area`; `captured` is a `SchedulingCapture` (`windows`, `write`, `change_request`,
   `refused`; graph-tools §3). Model-facing results exclude the appointments' issue text (audit D-11; `Appointment`
   field note, cases §4.1).
4. A `register_scheduling()` hunk in `web/container.py` (own hunk only) that builds the one `SchedulingService`. No
   `register_` hunk for the tools (GRT-1).

### Source

- PRD R-14, R-18, R-19, R-20, R-21, R-22, R-23, R-41 (booking cap); HP-3 (Innocent ✓ 2026-10-20: the fee rule,
  cancellations the same way).
- **Final contract:** [`stage7/cases.md`](../../design/contracts/stage7/cases.md) §1.0 (unit of work: `write=True` is
  `BEGIN IMMEDIATE`, `busy_timeout` 5000 ms [A]), §1.1–§1.3 (the issued tables restored by a reset; ids continue from
  the issued maximum), §2 (`Zone`, `FeeNote`, `zone_for`, `hours_before`, `fee_bearing`, `fee_note`, `LAKEWAY_ZIPS`,
  `NOT_SERVED_CITIES`), §3.2 (`case_due_at`), §4 (the five types), §4.1 (`BookingRepos`, `Slot`, `Appointment`); ledger
  [`7b-decisions/cases.md`](../7b-decisions/cases.md) CAS-6, CAS-7, CAS-8, CAS-17, CAS-34, CAS-36; residual
  [`7b-decisions/residuals-graph.md`](../7b-decisions/residuals-graph.md) R-G-19 (`slice_inputs`, `views_for_customer`).
  [`stage7/graph-tools.md`](../../design/contracts/stage7/graph-tools.md) §1 (`ToolKind`, `ToolErrorCode`, factories,
  dispatch), §2 (scheduling `tool_kinds`), §3 (`SchedulingCapture`), C-7; ledger GRT-1. Merge MC-10.
- DO-4 §1 (`ActionKey`, `CompletedAction`, `ShownSlot`), §5 (`ToolDef`, `ToolCallScope`, `ToolResult`, `WriteResult`,
  `ChangeRequestDraft`, `SchedulingResult`, `SchedulingSlice`, lookup-log rule), §11 (`SLOT_TAKEN`, `OUT_OF_AREA`,
  `BOOKING_CAP`), §13 (`booking.slots.*`), §14 `SchedulingService`.
- DO-3 §3, §4.4, §7 R-18…R-23 rows, §8 A5 row; DO-1 §5.2 (WP-4 traced), §8.2 rows *Booking write*, *Slot shown, then
  taken*, §8.3, §9 (write order).
- Issued `SCHEMA.md` (statuses, windows, zone map, expected behaviour, seeded customers); WP-3, WP-4, WP-4F.
- DO-5 E-7; DO-7 M-9, M-21.
- Slice plan row AEA-28; §3 rows `adapters/sqlite/repos_*.py`, `agent/tools/*.py`, `web/container.py`.
- **Brief check:** serves "Handle the full flow: the caller asks for an appointment, the agent checks availability, and
  either confirms the booking or offers alternatives"; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

All service tests run over `temp_sqlite()` (a temp working copy from `tests/fixtures/sqlite.py`) with a fixed demo
clock; the issued file's checksum is asserted unchanged after each test module.

- [ ] AC-1 [invariant] WP-3: `find_windows` for verified MHC-10001 (`member_tier` `standard`), `hvac_repair`, wanting Saturday 16:00–19:00, returns `WindowsFound(zone="north", exact_fit=False)` with no Saturday or Sunday north repair window and offers slots 56, 42 and 58 (Mon 2026-10-19) with their technicians — verify: `tests/services/test_scheduling.py::test_find_windows_wp3_offers_earliest_north_repair` — evidence: slot ids, windows, technician names and `exact_fit` asserted.
- [ ] AC-2 [invariant] An unverified zone-only search never returns a `reserved_members` slot and its fee note quotes the standard (`none`) tier; a verified standard or plus member also gets `reserved_members` slots; a verified non-member never does — verify: `tests/services/test_scheduling.py::test_member_reserved_only_for_verified_members` — evidence: three cases pass.
- [ ] AC-3 [failure/refusal] A Lakeway address and each of ZIPs 78734 and 78738 return `OutOfArea(reason="not_served")`; an unrecognisable place returns `OutOfArea(reason="unknown_location")`; ZIPs 78620 and 78653 search the zone `zone_for` gives them; the input string is absent from the result — verify: `tests/services/test_scheduling.py::test_out_of_area_and_zip_towns` — evidence: pass; the serialised `OutOfArea` holds only `reason`.
- [ ] AC-4 [invariant] `book` commits slot `booked`, a `scheduled` appointment, `actions(booked)` and the `lookup_log` row together, and a fault injected after the appointment insert leaves none of the four — verify: `tests/services/test_scheduling.py::test_book_writes_four_rows_in_one_transaction` — evidence: four rows on success, zero after the fault; `WriteResult.confirmation` has date, window, technician and, for MHC-10001, a `FeeNote` with `waived=True`.
- [ ] AC-5 [failure/refusal] A slot booked by someone else between being shown and `book` returns `SlotTaken(slot_id, alternatives)` with fresh windows read in the same transaction and writes nothing — verify: `tests/services/test_scheduling.py::test_slot_taken_refuses_and_writes_nothing` — evidence: row counts unchanged; the alternatives exclude the taken slot.
- [ ] AC-6 [invariant] E-7: two threads booking the same slot at once, each on its own connection, yield exactly one `WriteResult` and one `SlotTaken`; the slot has one appointment — verify: `tests/services/test_scheduling_concurrency.py::test_one_slot_two_bookers` (two `SqliteUnitOfWorkFactory` connections, the real `busy_timeout`) — evidence: 0 double bookings over 20 repeats.
- [ ] AC-7 [invariant] The same `ActionKey` sent twice yields one appointment, one `actions` row and one `lookup_log` row, and the second call returns the first call's `WriteResult` — verify: `tests/services/test_scheduling.py::test_book_idempotent_on_action_key` — evidence: one row in each table; the two results compare equal.
- [ ] AC-8 [failure/refusal] Each `Refused` code writes nothing: `not_shown` (slot not in `scope.shown_slot_ids`), `outside_service_area`, `wrong_service_type`, `booking_cap` (the fourth booking in one conversation, with the cap read from the injected `Limits`), `not_owned` (another customer's appointment); an unverified scope is refused before any read of private rows — verify: `tests/services/test_scheduling.py::test_refusals_write_nothing` (parametrised) — evidence: one case per code; row counts unchanged; the repository double records no private read for the unverified case.
- [ ] AC-9 [invariant] WP-4F: moving appointment 94 (2026-10-23 08:00–12:00; its slot 189 is `central` / `plumbing` in the issued data although the appointment says "Annual tune-up", audit D-11) to a shown `open` slot of the same zone and service type frees the old slot to `open`, books the new one, updates the appointment and writes `actions(moved)` with `before` and `after`, all in one transaction — verify: `tests/services/test_scheduling.py::test_move_fee_free_wp4f` — evidence: both slot statuses and the action's `before` / `after` asserted.
- [ ] AC-10 [failure/refusal] WP-4: with the demo clock at 2026-10-16 10:00, `move` and `cancel` of appointment 1 return `Refused(code="fee_bearing", hours_before=2.0)`, and the appointment row and slot 2 are identical before and after; at exactly 24.0 h before the window the same `cancel` is free (CAS-6) — verify: `tests/services/test_scheduling.py::test_fee_bearing_move_and_cancel_never_write` — evidence: row snapshots equal (M-21: 0 fee-bearing writes); the 24.0 h case writes.
- [ ] AC-11 [invariant] WP-4: `request_change` for appointment 1 returns a `ChangeRequestDraft` (`change` move, `hours_before` 2.0, `window_start` 2026-10-16T12:00-05:00, `windows_shown` the shown slot ids), writes `actions(change_request_sent)` and the `lookup_log` row in one transaction, and leaves every appointment and slot row (including the windows shown) unchanged — verify: `tests/services/test_scheduling.py::test_request_change_wp4_records_and_touches_nothing` — evidence: draft fields asserted; slot and appointment snapshots equal.
- [ ] AC-12 [invariant] `cancel` more than 24 hours out sets the appointment `cancelled`, frees the slot to `open` and writes `actions(cancelled)` — verify: `tests/services/test_scheduling.py::test_cancel_fee_free` — evidence: pass.
- [ ] AC-13 [invariant] An estimate request offers and books only `estimate` slots, and the confirmation names the Comfort Advisor (R-23) — verify: `tests/services/test_scheduling.py::test_estimate_books_estimate_slots_only` — evidence: no other service type in the windows.
- [ ] AC-14 [invariant] `AppointmentsRepo.for_customer("MHC-10001")` returns the scheduled 2026-10-22 08:00–12:00 visit (`SCHEMA.md` seeded row), and a booking after a reset gets the next id after the issued maximum (cases §1.3, §4.1) — verify: `tests/adapters/sqlite/test_repos_booking.py::test_for_customer_and_next_id` — evidence: date, window and the new id asserted.
- [ ] AC-15 [invariant] `scheduling_tools(scheduling)` returns one `ToolDef` per scheduling kind with `effect` and `requires_verified` as above (False only for `slot_search`); no args model has a customer field; the read returns a `LookupEntry` with `lookup_written=False`; the writes return `lookup_written=True` and leave exactly one `lookup_log` row; every `Refused.code`, `SlotTaken` and `OutOfArea` maps to its same-named `ToolErrorCode` — verify: `tests/unit/agent/tools/test_scheduling_tools.py::test_tool_defs_lookup_rule_and_error_codes` — evidence: pass per tool and per code.
- [ ] AC-16 [negative] Model-facing results (`ToolResult.for_model`, `LookupEntry.result_seen`) and the service's log lines hold no appointment issue text, no full phone number and no email; a seeded distinctive issue string written to a fixture appointment never appears in them — verify: `tests/unit/agent/tools/test_scheduling_tools.py::test_for_model_excludes_issue_text_and_contact` — evidence: absence asserted in result, lookup snapshot and captured log.
- [ ] AC-17 [capture] The records E-7, M-9, M-21 and CAP-1 read are produced for every write: `actions` rows with kind, `records`, `before` / `after` and the demo-clock `at`, and `lookup_log` rows with `turn_id` and `message_id` from the scope, written in the write's own transaction — verify: `tests/services/test_scheduling.py::test_write_records_carry_turn_and_message` — evidence: field sets asserted for book, move, cancel and request_change. No entry point is added; the CON-2 path is proven end to end by AEA-51 (WP-3, WP-4, WP-4F).
- [ ] AC-18 [invariant] `slice_inputs("MHC-57204")` returns zone `central`, `member` False and appointment 1 as an `AppointmentView` with date, window and technician, never `issue_description` or a customer id; an unknown customer returns `zone=None`, `member=False`, no appointments (cases §4–§4.1, R-G-19) — verify: `tests/services/test_scheduling.py::test_slice_inputs` — evidence: the three fields asserted; the serialised view has no `issue_description` key; the unknown-customer result asserted.
- [ ] AC-19 [journey] Extends J-3 and J-4 (slice plan §0a journey map; `backend-amendments.md` §3): J-3, the booking re-reads the slot and stores the appointment, one `actions` row and its lookup row in one transaction; J-4, a change inside 24 hours leaves the appointment row unchanged and stores a change request; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_28.py` and `tests/journeys/j4/test_aea_28.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_28.py tests/journeys/j4/test_aea_28.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-28.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-20 [regression/context] Same change updates: `.claude/reference/area-map.md` A5 rows (`services/scheduling.py`, `repos_booking.py`, `agent/tools/scheduling.py`: planned → actual + commit), `.claude/state/icm-progress.md` (the affected row's evidence link), and DO-3 §3 rows for those files (status only) — verify: `git diff --name-only` — evidence: those paths besides the owned files; no `schema/*.sql`, `policy/*` or issued-data path in the diff.

### Observability

- Responsibilities: for the chat turn (WF-1), every write's `actions` row and every scheduling call's `lookup_log` row
  (R-29) with `turn_id`, `thread_id` (copied from the message row by `core.lookup_log.append`, cases §1.2) and
  `message_id`, written in the write's own transaction; the outcomes `slot_taken`, `booking_failed` (lock timeout) and
  the refusals reach the turn record through `SchedulingResult.status` (DO-1 §8.2 signals). No issue text, full contact
  detail or customer free text in logs.
- Capture evidence: AC-17 here; AC-16 is the negative half; CAP-1 at the real CON-2 entry point in AEA-51.

### Evaluation

- Checks: E-7 booking validity (the one-slot concurrency test is AC-6); keeps E-1's WP-3, WP-4 and WP-4F hard gates
  satisfiable (appointment row untouched on WP-4; valid writes on WP-3 and WP-4F).
- Expected-answer authority: deterministic rules from `SCHEMA.md` (zone, service type, open status, member-reserved
  slots, fixed clock), PRD R-18 / R-19 / R-23 and Q-3 (zone mapping), cases §2 (the fee schedule's 24-hour rule);
  Innocent's Stage 3 rule for fee-bearing changes (R-21, R-22; HP-3) (DO-5 *Expected-answer authority*).

### Metrics

- References: M-9 (valid writes ÷ writes; double bookings), M-21 (no fee-bearing move or cancel by the AI).
- Acceptance conditions: both stay computable from `actions` rows and the DB copy (the harness's DB-copy check, AEA-24;
  AC-6, AC-10, AC-17); the targets (100% valid, 0 double bookings, 0 violations; approved Q-020, R-21, R-22) are gates
  run at Stage 9, not results here.

### Blocked by

AEA-10 (the working copy, `50_booking.sql`, `repos_core.actions` / `lookup_log`, the unit of work, `temp_sqlite()`),
AEA-13 (`policy/booking.py`: `zone_for`, `hours_before`, `fee_bearing`, `fee_note`, `SCHEDULE_FEES`). `AppointmentView`
and `SchedulingSliceInputs` come from AEA-02 (wave 0, R-G-19), already merged; no wave moves.

AC-19's journey record names AEA-57 (harness, wave 2) and AEA-51 (the integrated turn) as *Blocked by* for its
integrated level only (`integrated-journeys.md` §4); they are evidence-level dependencies, not merge blockers, so no wave
moves.

### Agent handoff

- Area / owner: A5 Scheduling (DO-3 §8); slice plan AEA-28.
- Contracts and shared surfaces: consumes `ActionKey`, `CompletedAction`, `ShownSlot`, `Slot`, `Appointment`,
  `ToolKind`, `ToolErrorCode`, `ToolDef`, `ToolCallScope`, `ToolResult`, `LookupEntry`, `WriteResult`,
  `ChangeRequestDraft`, `SchedulingCapture` (AEA-02); the booking cap in `Limits` (AEA-01); `policy/booking.py` (AEA-13);
  the unit of work, repository shells and working copy (AEA-10); the demo clock reading in `scope.now`. Produces
  `SchedulingService` for AEA-35 (specialist runner via the executors), AEA-39 (act node: a `ChangeRequestDraft` becomes
  `staff_change_request` → AEA-29's handoff) and AEA-51 (wiring); `scheduling_tools(scheduling)` for AEA-51's registry,
  dispatched by AEA-22; `AppointmentsRepo.for_customer`; `AppointmentsRepo.views_for_customer` and
  `SchedulingService.slice_inputs` for AEA-39's act node, which fills `SchedulingSlice` from them (cases §4–§4.1,
  R-G-19). Consumes `AppointmentView` and `SchedulingSliceInputs` (AEA-02, graph-tools §3). Journey: extends J-3 and J-4
  in `tests/journeys/j3/test_aea_28.py` and `tests/journeys/j4/test_aea_28.py` on AEA-57's harness (AC-19). Must not
  edit: `policy/booking.py`, `schema/*.sql`, `repos_core.py`, `db.py`, `domain/*`, other executors, other `register_`
  hunks, the issued DB.
- Scope boundary / refusal: never writes a fee-bearing change, never waives or discounts a fee (DEC-2), opens no case
  (the handoff for a change request is AEA-29's), no reply wording (AEA-35 / AEA-38), no emergency booking (`SCHEMA.md`:
  safety escalates), no appointments-read tool (the scheduling specialist's kinds are graph-tools §2's five and its
  slice carries the appointments, DO-4 §5 `SchedulingSlice`).
- Wave and gates: wave 2; no human gate.
- Lane: build-loop — repository, service and executors the app runs.
- Risk: None — it writes demo bookings to the working copy under rules, with no secret, access or PII exposure beyond
  AC-16's guard (slice plan: not **Sec**).
- Entry points added or changed: None.
