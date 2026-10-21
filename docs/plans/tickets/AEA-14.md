## [AEA-14] policy: promises, priorities, escalation decision

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

> **US-14 · When it hands me off: a reference, an honest promise, and my choice of follow-up.** "As a homeowner whose
> request needs a person, I need a reference number, the exact promise (who gets back to me and by when), and a choice of
> email or phone and a time window, so that I know what happens next and never repeat my story." Acceptance: "nobody
> online → 'A representative will get back to you within 1 business day' with the due date and reference; refund →
> 'within 2 business days' (a response, not a refund); nothing says a message was sent."

Two pure modules, both code, never a model (R-25, R-26; HP-4 B). Final shapes: `docs/design/contracts/stage7/cases.md`
§3 and §5 (*cases §n*), which win over DO-4 §6–§7 where they differ (DO-4 §16).

- **`src/meridian/policy/handoff.py`** (DO-3 §4.1, A6):
  - **Business days and due times** (cases §3.1, CAS-9): `HOLIDAYS_CLOSED` (2026-05-25, 07-04, 09-07, 11-26, 11-27, 12-25,
    2027-01-01; KB `policies/holiday_hours_2026.png`), `SHORT_DAYS` (2026-12-24 closes 12:00), `CLOSE_OF_BUSINESS` 19:00,
    `PHONE_HOURS` (Mon–Fri 07:00–19:00, Sat 08:00–16:00; Sunday and closed holidays closed; FAQ). `is_business_day(d)`:
    Mon–Fri and not a closed holiday (Saturday is not a business day). `business_due(now, days)`: 19:00 Chicago on the
    `days`-th business day strictly after `now`'s calendar date; the time of day never matters. `phone_support_open(now)`.
    `due_label(dt)` → "Monday, October 19, 7:00 pm".
  - **The promise table** (cases §3.2, CAS-10, CAS-11): `PolicyRow = Literal["R26.unstaffed", "R26.refund", "R26.staffed",
    "R26.safety_none", "OD4.danger_review"]`; `PROMISE_TABLE: Mapping[PolicyRow, str]`, every string imported word for
    word from `policy/texts.py` (AEA-03), never typed here. `OD4.danger_review` is SCREEN_SPECS SCR-1's separate line
    under the emergency-line card ("No representative is online right now, so someone will review this online request
    within 1 business day. That is not the wait for emergency help; for that, please use the emergency line.").
  - **`promise_for(reason, presence, now, window_start=None) -> Promise`** (DO-4 §7 signature unchanged), first match:
    `safety` → `R26.safety_none`, text "", no due; `simulated_on_shift` (every other reason) → `R26.staffed`, no due,
    `live_queued` True; `danger`, `burning_unclear` with nobody online → `OD4.danger_review`, due `business_due(now, 1)`
    (WP-6 step 4); `refund` → `R26.refund`, due `business_due(now, 2)`, extra line "I can't promise an outcome."; anything
    else → `R26.unstaffed`, due `business_due(now, 1)`. `fee_bearing_change` adds the can't-guarantee line when
    `window_start < due_at` and the phone-support line when `phone_support_open(now)` (SCREEN_SPECS SCR-1 copy notes).
    `Promise.due_at` is **always** the customer promise, never the window start. `Promise` has no validator (GRC-2):
    this module is its only constructor.
  - **`case_due_at(reason, promise, window_start) -> datetime | None`**: the window start for `fee_bearing_change`, else
    `promise.due_at` (CAS-10; R-21 "internal due time at the window start"; OpenAPI CON-12 `FEE_BEARING_CHANGE` mock).
  - **`priority_for(reason, *, promise_due=None, renewal_date=None) -> Priority`** (cases §3.3): `safety` P0; `danger`,
    `burning_unclear` P1; `fee_bearing_change`, `late_technician` P2; `membership_cancel` P2 if `renewal_date` is set and
    `renewal_date <= promise_due.date()`, else P3 (CAS-14); `unsupported_action` P4 (CAS-12); `customer_requested_person`,
    `refund`, `billing_dispute`, `complaint_or_manager`, `legal_or_chargeback`, `commercial`, `identity_unverified`,
    `ai_failure` P3. The burning-smell "both ruled out" case is built on CAS-16's recommended option (Agent handoff).
  - `DUE_SOON_WINDOW = timedelta(hours=4)`, `UNOWNED_AFTER = timedelta(minutes=30)` [A] on the demo clock (CAS-20;
    replaced by the Stage 9 staff walkthrough).
  - `STAFF_GUIDANCE_FOR: Mapping[HandoffReason, tuple[str, ...]]` (cases §5, CAS-33): the opening words of each
    staff-only bullet in KB `internal/agent_discretion_notes.md`, quoted from the file, for `fee_bearing_change`,
    `late_technician`, `billing_dispute`, `complaint_or_manager` and `refund`. Staff guidance only; never customer text.
  - `D4_ROWS`: every row of consolidated direction §9.4's table (pay an invoice, autopay, auto-renew, upgrade, duplicate
    charge, registration check, repeat repair, install-warranty term, itemized copy, late technician, waitlist, quote vs
    invoice, refund, commercial quote, job inquiry), each with its case rule (none, P4 only if accepted, P4, P2, P3).
- **`src/meridian/policy/escalation.py`** (wave 1 here by the slice plan): `decide_escalation(EscalationInputs) ->
  EscalationDecision` (DO-4 §6), first match wins, rows 4, 6, 7 as revised in cases §3.4 (CAS-12, 13, 15; GRN-7):
  (1) gate `PERSON` → escalate `customer_requested_person` P3; (2) a policy word (refund, dispute, complaint or manager,
  legal or chargeback, commercial) → escalate per D4, P3; (3) `SchedulingResult.status == "staff_change_request"` →
  escalate `fee_bearing_change` P2, `R21.fee_bearing`; (4) plan `handoff_request` `membership_cancel` → escalate,
  `priority_for(…, promise_due=business_due(inputs.now, 1), renewal_date)` with the renewal date from
  `AccountResult.membership.renewal_date`, whatever the presence (`EscalationInputs.now`, added by AEA-02; cases §3.3–§3.4,
  R-G-15), `D4.membership_cancel`;
  `unsupported_action` → escalate P4, `D4.unsupported`; `late_technician` → escalate P2, `D4.late_technician`; other D4
  rows escalate or offer per the row; (5) identity `not_verified` or `locked` with a private task open → escalate
  `identity_unverified` P3; (6) `halt` set (only brake halts reach here, graph-core X-5), or any `SpecialistResult.status
  == "failed"` (already after its one retry), or `models_disabled`, or `plan.planner_failed and not plan.tasks` →
  escalate `ai_failure` P3, `degraded=True`, `AI.halt` / `AI.specialist_failed` / `AI.models_disabled` /
  `AI.planner_failed`; (7) `failed_answers ≥ 2` or `corrections ≥ 2` → offer `OD6.two_misses`, `timeouts ≥ 2` → offer
  `OD6.two_timeouts` [A: threshold 2, OD-6]; (8) otherwise none. `priority` always comes from `priority_for`. Rule ids:
  rule 1 `R2.person`, rule 2 `R24.<reason>` (`R24.refund`, `R24.billing_dispute`, `R24.complaint_or_manager`,
  `R24.legal_or_chargeback`, `R24.commercial`), rule 5 `R16.identity_unverified` (cases §3.4, R-G-14).

**Example pair.** Input: WP-7, "I want a full refund on the repair. It didn't fix anything and I had to call another
company.", nobody online, clock Friday 2026-10-16 10:00. Expected output: reason `refund`, P3; Promise text "A
representative will get to your refund request within 2 business days." with "I can't promise an outcome.", due Tuesday,
October 20, 7:00 pm (WP-7). Input: WP-4, fee-bearing request, window today 12:00–16:00, Friday 10:00, nobody online.
Expected output: `escalate`, `fee_bearing_change`, P2, rule `R21.fee_bearing`; Promise `R26.unstaffed` due Monday,
October 19, 7:00 pm plus "I can't promise anyone will confirm a change before your appointment starts; until a
representative confirms, please plan on the technician arriving 12:00 pm – 4:00 pm." and "Phone support is open until
7:00 pm today if you'd like to call."; `case_due_at` = 2026-10-16 12:00 (the window start).

### Source
- stage7/cases.md §3.1–§3.4, §5 (`STAFF_GUIDANCE_FOR`, due-state rules); decision ledger `docs/plans/7b-decisions/cases.md`
  CAS-9…CAS-16, CAS-20, CAS-33; stage7/graph-core.md §10 (GRC-2, no `Promise` validator), §8 (`FailureCounters`), X-5;
  stage7/graph-nodes.md §5 (`Plan.planner_failed`, GRN-7); stage7/graph-tools.md §3 (`MembershipView.renewal_date`);
  residuals `docs/plans/7b-decisions/residuals-graph.md` R-G-14 (rule ids), R-G-15 (`EscalationInputs.now`).
- DO-4 internal-components §6 (`EscalationInputs`, `EscalationDecision`, rule table), §7 (`HandoffReason`, `Priority`,
  `Promise`, `promise_for`, `HandoffRequest`), §16; DO-3 code-design §4.1, §6 S-3; DO-2 system-design §A.1 (*Escalation
  check*), §8.1–§8.2, §8.3 (*Promise and due time: refuse to improvise*).
- PRD R-6, R-7, R-8, R-16, R-21, R-22, R-24, R-25, R-26, R-27; consolidated direction §6 (*Priority*, *The promise
  record*), §9.1–§9.4 (D4 table); HP-4; WP-4, WP-5, WP-6, WP-7, WP-8; US-14; SCREEN_SPECS SCR-1 copy notes; KB
  `faq/customer_faq.md`, `policies/holiday_hours_2026.png`, `internal/agent_discretion_notes.md` (read-only).
- Slice plan §1 row AEA-14 (links M-10).
- **Brief check:** serves "Escalation must be graceful: the agent recognizes it is out of scope, tells the caller what
  is happening, and hands off with enough context that a human can pick up without starting over." and "Anything outside
  the handled call drivers routes to a human."; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] `business_due` follows cases §3.1: Fri 2026-10-16 10:00 +1 → Mon 10-19 19:00, +2 → Tue 10-20 19:00; Fri 20:00 +1 → Mon 19:00; Sat and Sun +1 → Mon 19:00; Mon 08:00 +1 → Tue 19:00; Wed 2026-11-25 +1 → Mon 11-30 19:00 (Thanksgiving closed); Saturday is never a business day (CAS-9) — verify: `tests/unit/policy/test_handoff.py::test_business_due_after_hours`, `::test_business_due_weekend`, `::test_business_due_thanksgiving` — evidence: each tz-aware Chicago datetime.
- [ ] AC-2 [invariant] `phone_support_open` is True Fri 10:00, False Fri 19:30, True Sat 09:00, False Sun 10:00, False on 2026-12-25 and on 2026-12-24 at 13:00 (FAQ hours; holiday image) — verify: `test_handoff.py::test_phone_support_hours` — evidence: the six values.
- [ ] AC-3 [invariant] Nobody online, a case-creating reason other than refund, safety, danger and burning-unclear → `R26.unstaffed`, text equal to the table's 1-business-day string, from Friday 10:00 due Monday, October 19, 7:00 pm with `due_label` "Monday, October 19, 7:00 pm" (SCREEN_SPECS SCR-1; WP-8) — verify: `test_handoff.py::test_unstaffed_promise_and_due` — evidence: text, row, `due_at` 2026-10-19T19:00-05:00, label.
- [ ] AC-4 [invariant] Refund → `R26.refund`, the 2-business-day string, extra line "I can't promise an outcome.", due Tuesday, October 20, 7:00 pm from Friday 10:00 (WP-7) — verify: `test_handoff.py::test_wp7_refund_promise` — evidence: text, extra line, `due_at`.
- [ ] AC-5 [invariant] Staffed (`simulated_on_shift`) for any reason but safety → `R26.staffed` "A representative will join this chat when available", `due_at` None, `live_queued` True (R-26) — verify: `test_handoff.py::test_staffed_promise` — evidence: the four fields for refund and for danger.
- [ ] AC-6 [invariant] Safety → `R26.safety_none`, text "", `due_at` None, P0: no follow-up time promised (R-6, R-26; WP-5) — verify: `test_handoff.py::test_safety_promises_no_time` — evidence: the four fields, staffed and unstaffed.
- [ ] AC-7 [invariant] Danger and burning-unclear with nobody online → `OD4.danger_review`, the SCREEN_SPECS separate line word for word, due `business_due(now, 1)`, and no second `R26.unstaffed` promise (CAS-11; WP-6 step 4) — verify: `test_handoff.py::test_p1_danger_review_line` — evidence: row, text, `due_at` Mon 19:00.
- [ ] AC-8 [invariant] Fee-bearing change (WP-4, Friday 10:00, window 12:00–16:00 today, nobody online) → `R26.unstaffed` due Mon 19:00 plus the can't-guarantee line naming "12:00 pm – 4:00 pm" and the phone-support line; the same request on a Sunday has no phone-support line; a window after the due has no can't-guarantee line; `case_due_at` returns the window start for it and `promise.due_at` for every other reason (CAS-10) — verify: `test_handoff.py::test_wp4_fee_bearing_lines_and_case_due` — evidence: the extra lines per case; `Promise.due_at` never equals the window start; the two case dues.
- [ ] AC-9 [invariant] Every `Promise.text` is a `PROMISE_TABLE` value, and every table string equals its `policy/texts.py` text character for character (M-10's comparison imports this table) — verify: `test_handoff.py::test_promise_texts_are_the_table` — evidence: membership and equality over every reason × presence.
- [ ] AC-10 [invariant] `priority_for` per cases §3.3: one assertion per `HandoffReason`, incl. `unsupported_action` P4, `late_technician` P2, and `membership_cancel` P3 for WP-8 (renewal 2026-11-03, promise due 2026-10-19) and P2 when the renewal is 2026-10-19 (CAS-12, CAS-14) — verify: `test_handoff.py::test_priority_per_reason` — evidence: the priority per reason and both membership cases.
- [ ] AC-11 [invariant] `D4_ROWS` contains every row of consolidated §9.4's table with its case rule, and `STAFF_GUIDANCE_FOR` maps exactly the five reasons of cases §5, each prefix a substring of `internal/agent_discretion_notes.md` — verify: `test_handoff.py::test_d4_rows_and_staff_guidance` — evidence: 15 rows matching the table; five reasons; each prefix found in the KB file.
- [ ] AC-12 [invariant] `decide_escalation` follows the order of DO-4 §6 with cases §3.4's rows, first match wins: gate `PERSON` → escalate P3; policy word `refund` → escalate P3; `staff_change_request` → P2 `R21.fee_bearing`; plan `membership_cancel` (WP-8) → P3 `D4.membership_cancel`; `unsupported_action` → P4 `D4.unsupported`; `late_technician` → P2 `D4.late_technician`; `failed_answers` = 2 → offer `OD6.two_misses`; `timeouts` = 2 → offer `OD6.two_timeouts`; nothing → none; a case matching rules 3 and 7 together returns rule 3 — verify: `tests/unit/policy/test_escalation.py::test_rule_order_first_match`, `::test_rule7_two_timeouts` — evidence: outcome, reason, priority and `rule_id` per scenario, with the rule ids of cases §3.4 (R-G-14): `R2.person` for the gate, `R24.refund` for the policy word (and `R24.<reason>` for each other rule-2 reason), `R16.identity_unverified` for rule 5 (AC-14's scenarios).
- [ ] AC-13 [failure/refusal] Rule 6: a brake `halt`, a single specialist result with status `failed`, `models_disabled`, or `plan.planner_failed` with no tasks each → escalate `ai_failure` P3 with `degraded=True` and `AI.halt` / `AI.specialist_failed` / `AI.models_disabled` / `AI.planner_failed`, so the turn ends `degraded_handoff` and is never counted as a resolution (CAS-15; GRN-7; PRD §5 *Reliability*) — verify: `test_escalation.py::test_rule6_single_failed_specialist`, `::test_rule6_models_disabled`, `::test_rule6_halt_and_planner_failed` — evidence: the decision fields for each trigger.
- [ ] AC-14 [failure/refusal] Identity `not_verified` or `locked` with a private task open → escalate `identity_unverified` P3, `rule_id` `R16.identity_unverified` (R-16; cases §3.4, R-G-14) — verify: `test_escalation.py::test_unverified_private_task_escalates` — evidence: both statuses, each with that `rule_id`.
- [ ] AC-15 [negative] `Promise(` is constructed nowhere outside `policy/handoff.py` and `tests/` (GRC-2), and no `PROMISE_TABLE` text or extra line contains any `STAFF_GUIDANCE_FOR` prefix or the whole words "waive", "discount", "refunded" or "sent" (staff-only guidance never reaches the customer; US-14 "nothing says a message was sent"; consolidated §9.3) — verify: `test_handoff.py::test_promise_construction_and_no_staff_text` — evidence: the source scan finds no other constructor; the text scan over every reason × presence × clock passes.
- [ ] AC-16 [invariant] Both modules are pure: no I/O, no clock read (`now` is an argument), no model, no import of `services/`, `agent/` or adapters (DO-3 §2.1) — verify: `test_escalation.py::test_policy_modules_are_pure` — evidence: forbidden modules absent from their imports; repeated calls equal.
- [ ] AC-17 [invariant] `membership_cancel` priority uses the 1-business-day due (cases §3.3–§3.4, R-G-15): `decide_escalation` passes `promise_due = business_due(inputs.now, 1)` to `priority_for`, whatever the presence; renewal ≤ `business_due(now, 1).date()` → P2, later → P3 (WP-8: Fri 2026-10-16 10:00, due Mon 10-19, renewal 2026-11-03 → P3; renewal 2026-10-19 → P2), the same with presence `simulated_on_shift` and `nobody_online` — verify: `tests/unit/policy/test_escalation.py::test_membership_cancel_priority_uses_business_due` — evidence: P3 and P2 for the two renewals under both presences; `rule_id` `D4.membership_cancel`.
- [ ] AC-18 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-14.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-4, J-5 and J-6 (promise rows, priorities, the escalation decision) as the journeys that will exercise this code once AEA-51 and AEA-52 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-19 [regression/context] Docs updated in the same change: `.claude/reference/area-map.md` A6 row (`policy/handoff.py`) and A7b row (`policy/escalation.py`, built in wave 1 by this ticket) planned → actual with the commit, `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 status planned → built — verify: `git diff --name-only` — evidence: the three files in the diff.

### Observability
- Responsibilities: no record of its own (pure); it supplies the values WF-1's and WF-2's records carry: the `promise`
  text, `policy_row`, customer due and case due (DO-6 `case`, `case_event`, `promise`; stored by AEA-29), the `rule_id`
  that names which trigger fired, and `degraded`, which makes `turn.outcome = degraded_handoff`.
- Capture evidence: AC-9 (texts are the table) and AC-13 (`degraded` set) here; at the real entry point, CAP-3 (WF-2:
  promise with due time and text from the policy table, none from the model) in AEA-51.

### Evaluation
- Checks: E-6 handoff slice (promise equals the table), E-3/E-4 escalation recall and false escalation, E-1's WP-4,
  WP-6, WP-7 and WP-8.
- Expected-answer authority: the policy table (exact strings), the D4 priority table and cases §3.1's business-day rule,
  never the model (DO-5 *Expected-answer authority*: PRD R-24, R-26; OD-4; consolidated §9.4).

### Metrics
- References: M-10 (promise text consistency), M-13 (promises kept on time: needs the customer `due_at`), M-19
  (escalation recall), M-20 (false escalation), M-27 (overdue cases: needs the case due).
- Acceptance conditions: M-10 stays computable by comparing `promise.text` with the importable `PROMISE_TABLE` (AC-9);
  M-13 needs a tz-aware customer `due_at` on every non-safety, non-live promise (AC-3, AC-4, AC-7) and M-27 the case due
  from `case_due_at` (AC-8). Targets are DO-7's, not set here.

### Blocked by
AEA-02, AEA-03

### Agent handoff
- Area / owner: A6 policy (`src/meridian/policy/handoff.py`) and A7b policy (`src/meridian/policy/escalation.py`).
- Contracts and shared surfaces: consumes DO-4 §6–§7 types with `EscalationInputs.now` (cases §3.4, R-G-15),
  `Presence`, `MembershipView`, `FailureCounters`, `Plan` (AEA-02) and the promise, fee-bearing and
  `OD4.danger_review` texts (AEA-03). Produces `promise_for`, `case_due_at`,
  `priority_for`, `business_due`, `is_business_day`, `phone_support_open`, `due_label`, `PROMISE_TABLE`, `D4_ROWS`,
  `STAFF_GUIDANCE_FOR`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER` for `HandoffService` / `CaseService` (AEA-29), the scheduler's
  thresholds (`DUE_SOON_WINDOW`, `UNOWNED_AFTER`, cases §3.3) and `next_business_morning` (AEA-30), the seeds (AEA-31),
  the safety path (AEA-36), the eval's M-10 check (AEA-24); `decide_escalation` for the act node (AEA-39, which sets
  `inputs.now = ctx.now` and builds the person-gate request with `rule_id="R2.person"`, R-G-14, R-G-15). Must not edit `policy/texts.py` (a missing sentence is a follow-up on
  AEA-03), `domain/*` or `policy/booking.py`.
- Scope boundary / refusal: no case write, no reference minting (AEA-29), no customer wording beyond the table strings,
  no follow-up sending (R-34), no fee waiver.
- Wave and gates: wave 1; no gate.
- Lane: build-loop — source and tests.
- Risk: None.
- Awaiting Innocent: CAS-16 — built on the recommended option A: a burning smell with both dangers clearly ruled out
  gets reason `burning_ruled_out` (needs AEA-02 to add the `HandoffReason` value, graph A-3), P2, promise `R26.unstaffed`
  (or `R26.staffed`), and `case_due_at` = the urgent booking's window start, else the promise due; one AC-10 assertion
  and one AC-8 case cover it. If he picks B, the row becomes P1 and the promise `OD4.danger_review`; if C, P3 with the
  case due = the promise due; either way only that row, its two assertions and AEA-02's enum value change.
- Entry points added or changed: None

**Resolved (residual pass 2026-10-21):**
1. Resolved R-G-15 (cases §3.3–§3.4): `EscalationInputs` gains `now: datetime` (AEA-02); `decide_escalation` passes
   `promise_due = business_due(inputs.now, 1)` for `membership_cancel`, whatever the presence; no `HandoffService`
   re-derivation (AC-17).
