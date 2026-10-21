## [AEA-13] policy: booking rules

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

> **US-10 · Book a repair or tune-up that fits my area, my membership and my day.** "As a homeowner, I need to see open
> windows in my zone (member-reserved ones if I'm a member), pick one, and get a confirmation with the date, window,
> technician and the fee that applies to me, so that I know exactly who is coming, when, and for how much." Also served:
> US-11 (estimates), US-12 (free move vs the $49 path), US-13 (cancel).

`src/meridian/policy/booking.py` is the pure rule table the scheduling service and its executors (AEA-28) apply (DO-3
§4.1, S-3). Its final shapes are `docs/design/contracts/stage7/cases.md` §2 (*cases §2*), which wins over DO-4 (DO-4 §16):

- **`zone_for(city_or_zip: str) -> Zone | None`** (`None` = not served; `Zone = Literal["north", "central", "south"]`,
  CAS-34). City → zone from issued `SCHEMA.md` (north: Round Rock, Cedar Park, Pflugerville, Georgetown, Leander, Hutto ·
  central: Austin · south: Kyle, Buda). ZIP → zone from the ZIP groups in KB `policies/service_area.md` (updated
  2026-04-01) mapped to their city's zone, Austin 787xx → central. Dripping Springs 78620 and Manor 78653 → `central`
  (audit Q-3, Innocent 2026-10-20; configured in our code, never an edit to `SCHEMA.md`). Not served:
  `NOT_SERVED_CITIES = {"San Marcos", "Bastrop", "Elgin", "Lakeway"}` [Source: `service_area.md`] and
  `LAKEWAY_ZIPS = {"78734", "78738"}` [A] (CAS-8; each is 787xx, so the specific exclusion wins over "Austin: 787xx
  (all)"; replaced by a check of the full USPS list for Lakeway at Stage 9). Any city or ZIP in no list → `None`.
- **`hours_before(now: datetime, slot_date: date, window: Window) -> float`**: hours from the injected "now" (the demo
  clock, R-3) to the start of the window, read from the window string (`08:00-12:00`, `12:00-16:00`, `13:00-17:00`,
  `16:00-19:00`, SCHEMA.md) in America/Chicago; negative once the window has started.
- **`fee_bearing(hours: float) -> bool`** = `hours < 24.0` (CAS-6) [Source: `pricing/2026_fee_schedule.pdf` "Late
  cancellation (<24h) $49 … Supersedes all prior fee schedules"]: exactly 24.0 hours is free; a started or past window is
  fee-bearing. Every tier pays it; nothing here waives it (D3 = DEC-2).
- **`SCHEDULE_FEES`** (stage7/graph-tools.md §4, C-3, R-G-3; lives here, AEA-13 writes it) holds three rows:
  `"Diagnostic visit"` → none 8900, standard 0, plus 0; `"After-hours dispatch"` → none 14900, standard 0, plus 0;
  `"Seasonal tune-up"` → none 12900, standard 0, plus 0 (key = the invoice line's wording). Beside it,
  **`MEMBER_ALLOWANCE_ROWS = frozenset({"Seasonal tune-up"})`** (graph-tools §4, R-G-3: the member value is an allowance,
  "Included (2/yr)", not a flat $0). One constant owns the scheduled fee amounts; AEA-27's `staff_notes_for` reads both.
- **`fee_note(service_type: ServiceType, tier: Literal["none", "standard", "plus"]) -> FeeNote`** (CAS-7, CAS-34,
  R-G-2, R-G-3) returns cases §2's `FeeNote` (`service_type`, `tier`, `fee_row`, `amount_cents`, `waived`, `line`):
  `hvac_repair` and `plumbing` → the `"Diagnostic visit"` row ($89 non-member, waived for Comfort Club and Plus; the $89
  is read from `SCHEDULE_FEES`, never a second literal); `hvac_tune_up` → the `"Seasonal tune-up"` row
  (`fee_note("hvac_tune_up", "none")` → 12900; `"standard"` / `"plus"` → 0 and waived; fee schedule "Seasonal tune-up
  (per system) $129 / Included (2/yr)"); `estimate` → `fee_row=None`, 0, not waived ("Free in-home estimate with a
  Comfort Advisor", `services/service_catalog.md`). `tier` is the **verified** customer's tier, `"none"` when unverified
  (R-14). The `line` is the customer sentence (= OpenAPI `ConfirmationBlock.fee_line`, e.g. "Standard diagnostic fee:
  $89"): `FeeNote.line = render(<booking fee TextId>, amount=format_usd(amount_cents))` (cases §2, data.md §2, R-G-7,
  R-W-7); a waived row renders the waived text with the scheduled non-member amount
  (`format_usd(SCHEDULE_FEES[fee_row]["none"])`). No dollar literal in `booking.py`; never model text.

`Zone` and `FeeNote` are transcribed from cases §2 (CAS-34) into `domain/records.py` by AEA-02 (R-G-2; domain may not
import policy, DO-3 §2.1).
Slot status, service-type match, member-reserved slots and the booking cap are applied by the scheduling service
(AEA-28), not here.

**Example pair.** Input: WP-4, customer MHC-57204 (Austin, not a member), tune-up today 12:00–16:00, clock Friday
2026-10-16 10:00. Expected output: `zone_for("Austin")` = `central`; `hours_before` = 2.0; `fee_bearing(2.0)` = True, so
the AI records a staff change request and never moves it (R-21). Input: WP-3, MHC-10001 Linda Foster, Round Rock,
Standard member, `hvac_repair`. Expected output: zone `north`; the diagnostic fee is waived (member), not the $89 the
transcript's agent quoted.

### Source
- stage7/cases.md §2 (`Zone`, `FeeNote` — the one definition, R-G-2 —, `LAKEWAY_ZIPS`, `NOT_SERVED_CITIES`, `zone_for`,
  `hours_before`, `fee_bearing`, `fee_note`); decision ledger `docs/plans/7b-decisions/cases.md` CAS-6, CAS-7, CAS-8,
  CAS-34; residuals `docs/plans/7b-decisions/residuals-graph.md` R-G-2, R-G-3, R-G-7 and `residuals-web.md` R-W-7;
  stage7/graph-tools.md §4 (`SCHEDULE_FEES`, `MEMBER_ALLOWANCE_ROWS`, C-3, R-G-3); stage7/graph-core.md §14 (points to
  cases §2 for `Zone` and `FeeNote`; its GRC-25 field set is withdrawn); stage7/data.md §2 (`policy/texts.py` `render`
  with the `amount` placeholder, `format_usd`, `booking` group; the `FeeNote.line` citation there is cases.md §2).
- DO-3 code-design §4.1 (`policy/booking.py`), §6 S-3, S-15; DO-4 §5 (`ChangeRequestDraft.hours_before`, `window_start`;
  `ConfirmationView.fee_note`), §14 (`SchedulingService` refusals `fee_bearing`, `outside_service_area`).
- PRD R-3, R-14, R-18, R-20, R-21, R-22, R-23; consolidated direction §9.3; audit K-11 and Q-3; HP-3; WP-3, WP-4 (and its
  fee-free variant WP-4F); US-10…US-13; OpenAPI `ConfirmationBlock.fee_line` (read-only).
- Issued `scheduling_db/SCHEMA.md` (zone map, windows); KB `policies/service_area.md`, `faq/customer_faq.md`,
  `pricing/2026_fee_schedule.pdf`, `services/service_catalog.md`, `membership/comfort_club_overview.md` (read-only).
- Slice plan §1 row AEA-13.
- **Brief check:** serves "Handle the full flow: the caller asks for an appointment, the agent checks availability, and
  either confirms the booking or offers alternatives."; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] `zone_for` maps every city in `SCHEMA.md`'s zone map to its zone (Round Rock → north, Austin → central, Kyle → south, and the rest) and returns only the three `Zone` values — verify: `tests/unit/policy/test_booking.py::test_city_to_zone_schema_map` — evidence: one assertion per listed city.
- [ ] AC-2 [invariant] `zone_for` maps every ZIP group in `service_area.md` to its city's zone, and any 787xx ZIP to `central` unless it is in `LAKEWAY_ZIPS` — verify: `test_booking.py::test_zip_groups_to_zone` — evidence: one assertion per listed ZIP.
- [ ] AC-3 [invariant] Dripping Springs, 78620, Manor and 78653 → `central` (Q-3) — verify: `test_booking.py::test_new_april_2026_areas_central` — evidence: four assertions.
- [ ] AC-4 [failure/refusal] San Marcos, Bastrop, Elgin, Lakeway, the ZIPs 78734 and 78738 (CAS-8), and a city or ZIP in no list → `None`, so the service answers `outside_service_area` (R-18: out-of-area gets an honest no) — verify: `test_booking.py::test_not_served_areas` — evidence: each returns `None`.
- [ ] AC-5 [invariant] `hours_before` uses the injected time, never the server clock: WP-4 (Fri 2026-10-16 10:00, window `12:00-16:00` that day) → 2.0; a window that started an hour ago → −1.0 — verify: `test_booking.py::test_wp4_two_hours_before` — evidence: 2.0 and −1.0, with the server clock patched to a different date and unused.
- [ ] AC-6 [invariant] `fee_bearing` is True for WP-4 (2.0 hours), True for a started window (−1.0), False for WP-4F's visit more than 24 hours away (e.g. 2026-10-22 08:00 from Fri 10:00), and False at exactly 24.0 hours (CAS-6; R-21, R-22) — verify: `test_booking.py::test_fee_bearing_boundary` — evidence: the four values.
- [ ] AC-7 [invariant] `fee_note` returns cases §2's `FeeNote`: `fee_row`, `amount_cents` for the tier, `waived`, `line` (R-G-2). By tier: `hvac_repair` and `plumbing` → `fee_row` `"Diagnostic visit"`, 8900 cents for `none`, 0 and waived for `standard` and `plus` (WP-3: waived for Linda Foster), the non-member `line` equal to "Standard diagnostic fee: $89" (OpenAPI example); `estimate` → `fee_row` None and 0 cents (CAS-7, CAS-34) — verify: `test_booking.py::test_fee_note_by_tier` — evidence: one assertion per service type × tier on all six fields.
- [ ] AC-8 [invariant] `SCHEDULE_FEES` holds the three rows of graph-tools §4 (`"Diagnostic visit"`, `"After-hours dispatch"`, `"Seasonal tune-up"`) with their amounts, `MEMBER_ALLOWANCE_ROWS == frozenset({"Seasonal tune-up"})` (R-G-3), and the amount in every `FeeNote` equals `SCHEDULE_FEES[fee_row][tier]` (no second `89` or `129` literal in the module) — verify: `test_booking.py::test_schedule_fees_single_source` — evidence: the three rows and the allowance set equal; a source scan finds `8900` once and `12900` once.
- [ ] AC-9 [negative] No fee note `line`, for any tier or service, contains the word "charged", a waived late-change fee, or the excluded old-FAQ figure $79 (SCREEN_SPECS SCR-1 *Never on this screen*; R-21; inventory: `faq/faq_old_copy.md` must not be used) — verify: `test_booking.py::test_fee_note_never_charged_or_waived` — evidence: the scan over every combination passes.
- [ ] AC-10 [negative] An unknown ZIP or city string (a distinctive value) passed to `zone_for` returns `None`, raises nothing, and is never written to a log record (`safe-validation-errors.md`; `OutOfArea` never stores the input, cases §4) — verify: `test_booking.py::test_unknown_location_not_logged` — evidence: `None`; the value absent from `caplog`.
- [ ] AC-11 [invariant] The module is pure: no I/O, no clock read, no import of `services/`, `agent/` or adapters; every `line` comes from `policy/texts.py` `render` (DO-3 §2.1) — verify: `test_booking.py::test_booking_module_is_pure` — evidence: forbidden modules absent from its imports; a monkeypatched `render` is called for each `fee_note`.
- [ ] AC-12 [invariant] `fee_note` tune-up and estimate rows as stated (graph-tools §4, cases §2, R-G-3): `fee_note("hvac_tune_up", "none")` → `fee_row` `"Seasonal tune-up"`, 12900, not waived; `"standard"` and `"plus"` → 0 and waived; `fee_note("estimate", …)` → `fee_row=None`, 0, not waived, for every tier — verify: `tests/unit/policy/test_booking.py::test_fee_note_tune_up_and_estimate` — evidence: one assertion per tier for each of the two service types.
- [ ] AC-13 [invariant] Every fee `line` is `render(<booking fee TextId>, amount=format_usd(amount_cents))`, and a waived row's is the waived text with `amount=format_usd(SCHEDULE_FEES[fee_row]["none"])` (cases §2 `FeeNote.line`; data.md §2 `amount` placeholder and `format_usd`; R-G-7, R-W-7); `booking.py` holds no dollar literal — verify: `test_booking.py::test_fee_line_rendered_with_format_usd` (spies on `render` and `format_usd`) and a source scan of `booking.py` for `\$[0-9]` — evidence: per service type × tier the `amount` passed to `render` equals `format_usd` of the stated cents ("$89", "$129"); the scan finds nothing.
- [ ] AC-14 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-13.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-3 (zones and windows) and J-4 (the 24-hour rule and fee) as the journeys that will exercise this code once AEA-51 lands, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-15 [regression/context] Docs updated in the same change: `.claude/reference/area-map.md` A5 row (`policy/booking.py` planned → actual with the commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 status planned → built — verify: `git diff --name-only` — evidence: the three files in the diff.

### Observability
N/A — pure functions with no entry point and no record of their own: the decisions they feed are recorded by AEA-28's
write transaction (`actions`, `lookup_log` rows; the `FeeNote.line` stored on the action's `after`, graph-core X-10) and
AEA-29's case for a fee-bearing request. A reviewer may disagree if they expect a `check_event` per refusal; DO-6 names
none for booking rules.

### Evaluation
- Checks: E-7 booking validity (zone and fixed-clock rules on the DB copy) and E-1's WP-3, WP-4 and WP-4F.
- Expected-answer authority: deterministic rules from `SCHEMA.md` (zone, service, status, member slots, fixed clock),
  Q-3 for the two new towns, the fee schedule for the 24-hour boundary (CAS-6), and Innocent's Stage 3 rule for
  fee-bearing changes (DO-5 *Expected-answer authority*).

### Metrics
- References: M-9 (booking-rule validity), M-21 (no fee-bearing move or cancel by the AI).
- Acceptance conditions: both stay computable from the DB-copy check and `eval_case_result` invariants; targets are
  DO-7's (100% valid writes, 0 violations), measured at Stage 9, not here.

### Blocked by
AEA-02, AEA-03 (`render` with the `amount` placeholder, `format_usd` and the `booking` fee texts, data.md §2, R-W-7;
both wave 0, so the wave is unchanged)

### Agent handoff
- Area / owner: A5 Scheduling policy (`src/meridian/policy/booking.py`).
- Contracts and shared surfaces: consumes `Zone`, `FeeNote` (cases §2, R-G-2), `ServiceType`, `Window` from `domain/`
  (AEA-02) and `policy/texts.py` `render` and `format_usd` (AEA-03, R-W-7; injected through import; tests may patch them).
  Produces `zone_for`, `hours_before`, `fee_bearing`, `fee_note`, `SCHEDULE_FEES`, `MEMBER_ALLOWANCE_ROWS`,
  `LAKEWAY_ZIPS`, `NOT_SERVED_CITIES` for `services/scheduling.py` and `agent/tools/scheduling.py` (AEA-28),
  `SCHEDULE_FEES` and `MEMBER_ALLOWANCE_ROWS` for `agent/tools/account.py` (AEA-27, which is blocked by this issue), and, through
  `ChangeRequestDraft.hours_before` / `window_start`, the handoff due time (AEA-14, AEA-29). Must not edit `domain/*` or
  `policy/texts.py` (a missing `booking` text is a follow-up on AEA-03).
- Scope boundary / refusal: no database read, no slot-status or member-slot check, no booking write, no fee waiver or
  discount of any kind (D3 = DEC-2), no customer wording typed here.
- Wave and gates: wave 1; no gate.
- Lane: build-loop — source and tests.
- Risk: None.
- Entry points added or changed: None

**Resolved (residual pass 2026-10-21):**
1. Resolved R-G-2: cases.md §2 (CAS-34) is the one `FeeNote` (`service_type, tier, fee_row, amount_cents, waived,
   line`); graph-core §14's GRC-25 set is withdrawn. AC-7 is written against it.
2. Resolved R-G-3: `SCHEDULE_FEES` holds three rows (graph-tools §4) and `MEMBER_ALLOWANCE_ROWS`; AC-8 and AC-12 cover
   them. The fee line is built through `render(…, amount=format_usd(…))` (R-G-7, R-W-7; AC-13).
