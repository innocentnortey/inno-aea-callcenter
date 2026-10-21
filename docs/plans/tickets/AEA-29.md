## [AEA-29] cases and handoff: case service, handoff service, brief

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

> **US-14:** As a **homeowner** whose request needs a person, I need a reference number, the exact promise (who gets back
> to me and by when), and a choice of email or phone and a time window, so that I know what happens next and never repeat
> my story.
>
> **US-19:** As a **representative**, I need an eight-heading brief that keeps facts and customer claims apart, the
> pertinent sources (what the AI saw and the current value), the promise with the follow-up preference beside it, and the
> full chat one click away, so that I can act without re-asking the customer.

The case store's service layer and the handoff write, as one cohesive invariant (slice plan §2: "`open_case(tx, …)` is
HandoffService's own transaction, so they are one invariant"). Shapes are DO-4 §7 and §13 as revised by
`docs/design/contracts/stage7/cases.md` §5 (contract §5 wins where they differ, DO-4 §16).

- **`services/handoff.py` — `HandoffService(uow, cases, demo, clock, staff_guidance)`** (stage7/cases §5, CAS-33):
  `open(req, ctx) -> HandoffResult`. Inside **one** write unit of work: `presence = demo.presence(tx)` (read inside the
  transaction so a shift end cannot interleave), `promise = promise_for(reason, presence, now, window_start)` and
  `case_due_at(reason, promise, window_start)` (AEA-14, stage7/cases §3.2), then `cases.open_case(tx, req, promise, now)`.
  `cases`, `case_events`, `promises`, `actions(case_opened)` and `events(case_created)` commit together. **Both dues are
  stored** (CAS-10): `cases.due_at` = the case due (window start for `fee_bearing_change`, else the promise due) and
  `promises.due_at` = the customer promise. A live-queued case sets `conversations.live_state = 'queued'`. **One open
  case per thread:** a second open returns `created=False`, the same reference, adds a `case_event` for a new reason and
  raises the priority to the higher one (DO-4 §7 `HandoffResult`, CON-4 `already_open`). `alert = "supervisor_now"` for
  P0, P1 and `fee_bearing_change` (R-21). For each `StaffGuidance` mapped to `req.reason` (`STAFF_GUIDANCE_FOR`,
  stage7/cases §5) it appends one `lookup_log` row `LookupEntry(tool="staff_guidance", record_ids=(), passage_ids=(id,),
  result_seen=<text sha256>, turn_id=req.turn_id, message_id=anchor)` where `anchor =
  tx.core.messages.handoff_anchor(req.thread_id)` (CAS-38); idempotent per thread. Writes no `turn` row (web.md §8,
  AEA-42). Safety path: a failed write is retried once (DO-1 §8.2); the instruction is the front node's job and never
  waits on this.
- **`services/handoff.py` — `BriefAssembler()`** (pure; DO-4 §7): `assemble(case, state, lookups: Sequence[LookupRow])`
  builds the eight headings in `BRIEF_TITLES` order (1, 3, 5, 6, 8 origin `state`; 2, 4, 7 `extraction`), status
  `being_written`; `attach_extraction(brief, extraction, check)` fills 2, 4, 7 from a validated `BriefExtraction`
  (quotes must be exact substrings of a customer message of this thread) and the R-46 trims, or marks them
  `not_generated` when the extraction is `None`. Staff-only text (the staff-guidance rows, record-vs-policy mismatches
  such as INV-204411) enters only as heading 3 or 7 items with `source.kind = "lookup_log"`, `ref = str(LookupRow.id)`
  (DO-4 §7 note; `LookupRow` (fields as stage7/cases §1.2) is imported from `meridian.domain.tools`, AEA-02, never from
  an adapter, DO-3 §2.1; R-G-8). The reply node calls it and stores the result (stage7/graph-nodes §3,
  AEA-38).
- **`services/cases.py` — `CaseService(uow, clock)`** (stage7/cases §5, CAS-18; all DO-4 §13 methods): `open_case`,
  `attach_brief` (an upsert per case: a second call replaces the stored brief), `open_case_for_thread`, `queue` (CON-11),
  `detail` (CON-12), `oversight` (CON-17), `apply` (CON-13), `set_followup` (CON-5), `record_activity` (CON-15),
  `convert_live_queued(now, tx=None)` (shift end; with `tx` it joins `DemoService.set_staffing`'s transaction). Staffing
  for the queue is read from `tx.cases.demo_state`, so `CaseService` takes no `DemoService` (no cycle). CON-12's current
  values and `changed` flags come from `tx.core.reads.invoice / appointment / customer` (CAS-19); CON-17's
  `new_flags_count` from `tx.core.reads.new_flags_count()`. The rules it applies (`due_state`, queue order, the five
  oversight lanes, promise `kept` / `missed` / `changed`, the stream events it writes, ownership as `StaffRole` rendered
  through `STAFF_PERSONAS[role].name`) are stage7/cases §5's rules table, with `DUE_SOON_WINDOW` = 4 h and
  `UNOWNED_AFTER` = 30 min on the demo clock (CAS-20, [A]). `CaseSummary.allowed_actions` = the lifecycle × live-state
  table's actions intersected with `ROLE_ACTIONS[actor.role]` (staff.md §1, `domain/staff.py`, AEA-02; cases §5 rules
  table; R-W-13, R-G-16): the owner always gets `[]`. CON-12 customer lines carry `display_name =
  CUSTOMER_SPEAKER_NAME` ("Customer", staff.md §1; cases §5; R-W-14, R-G-16). Lifecycle per consolidated direction §6 and R-33:
  live-queued (staffed only) → unassigned → claimed → in progress → waiting (wake-up required) → resolved / closed
  unresolved.

This ticket writes **services only**. It calls `tx.cases.*` and `tx.core.*` repository methods that AEA-10 owns
(`repos_cases.py`, `repos_core.py`, every `.sql`); it edits none of them. Produces, for other issues: `HandoffService`
and `BriefAssembler` (AEA-36 safety, AEA-38 reply/brief, AEA-39 act, AEA-42 CON-4, AEA-31 seed briefs), `CaseService`
(AEA-30 scheduler and shift end, AEA-42 CON-5, AEA-45 CON-11…13/15/17, AEA-46 live chat, AEA-53 reads), wired for real
at AEA-51 and AEA-52.

**Example pair (WP-7, nobody online, demo clock Fri 2026-10-16 10:00, seeds present):** input `HandoffRequest(reason=refund,
priority=P3, trigger=escalation)` for "I want a full refund on the repair. It didn't fix anything and I had to call
another company." → output: one new case `MHC-C-0009` (live refs follow the seeds MHC-C-0005…0008, stage7/cases §7),
P3, promise text "A representative will get to your refund request within 2 business days." with extra line "I can't
promise an outcome.", `policy_row` `R26.refund`, promise `due_at` = case `due_at` = Tue 2026-10-20 19:00 Chicago
(`due_label` "Tuesday, October 20, 7:00 pm"), `actions(case_opened)`, `events(case_created)`, `alert=None`, one
`lookup_log` row for the staff guidance "Issue refunds of any kind." anchored on the refund message; brief heading 2
quotes the refund sentence, heading 4 holds "It didn't fix anything" and "I had to call another company" as claims,
heading 6 holds the promise text, heading 7 holds the staff guidance item. Calling `open` again for the same thread
returns `created=False` and `MHC-C-0009`.

### Source

- DO-4 §1 (`ActionKey`, `CompletedAction`, `OpenCase`), §5 (`LookupEntry`), §7 (handoff types, `HandoffService`, brief),
  §13 (`CaseService`, `UnitOfWork` repository rule), §16; `docs/design/contracts/stage7/cases.md` §1.1 (`cases.due_at`,
  `promises.due_at`, `live_state`, `lookup_log`), §1.2 (`core.reads.*`, `handoff_anchor`, `LookupRow`, `cases.*`
  repository names), §3.1–§3.3 (`business_due`, `PROMISE_TABLE`, `case_due_at`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`), §5
  (constructors, rules table, `STAFF_GUIDANCE_FOR`), §7 (seed refs); `stage7/staff.md` §1 (`StaffRole`, `StaffActor`,
  `STAFF_PERSONAS`, `ASSIGNEE_ROLES`), §5 (`live_state` values), §12 (greeting row as the anchor); `stage7/graph-nodes.md`
  §3 (brief assembled, checked, stored); `stage7/web.md` §1 (`ApiErrorCode` = OpenAPI enum), §8 (CON-4 calls `open`);
  `stage7/data.md` §2–§3 (`policy/texts.py`, `StaffGuidance`).
- Decision ledger `docs/plans/7b-decisions/cases.md`: CAS-10, CAS-18, CAS-19, CAS-20, CAS-21, CAS-33, CAS-38; merge
  `merge-clashes.md` MC-2, MC-12, MC-26; residuals `7b-decisions/residuals-graph.md` R-G-8 (`LookupRow` home), R-G-9
  (`FixedClock`), R-G-16, and `7b-decisions/residuals-web.md` R-W-13 (`ROLE_ACTIONS`), R-W-14 (`CUSTOMER_SPEAKER_NAME`).
- Join amendments AEA-29-1…AEA-29-4 (`docs/plans/ux-join/backend-amendments.md` §2; staff audit A1, A2, A3, A4) and
  the §3 `[journey]` criterion; staff.md §5 (live actions leave the case version alone).
- DO-3 §4.4 (`services/cases.py`, `services/handoff.py` rows), §5.1, §6 S-7 (one concrete `CaseService`; "staff routes
  never call `open_case`"), S-20, §2.3 rule 1 (no transaction across a model call).
- Consolidated direction §5 (brief format), §6 (states, priority, promise record, alerts), §8 OD-4/OD-5, §9.3, §9.4,
  §9.5 (follow-up privacy rule), §10; PRD R-2, R-6, R-25…R-29, R-33, R-34; system design §8.2, §A.4, §A.5.
- `docs/ux/03-structure/UI_CONTRACTS.md` CON-4, CON-5, CON-11…CON-13, CON-15, CON-17 and the OpenAPI operations
  `saveFollowUp`, `applyCaseAction`, `recordContactActivity` (wire shapes win); DO-6 WF-2, WF-4, CAP-3, CAP-4 and the
  check "A handoff left no case"; DO-5 E-6; DO-7 M-10…M-13, M-15, M-27; WP-4, WP-5, WP-7, WP-8; HP-4.
- **Brief check:** serves "Escalation must be graceful: the agent recognizes it is out of scope, tells the caller what is
  happening, and hands off with enough context that a human can pick up without starting over."; touches nothing out of
  scope; weakens nothing → proceed.

### Acceptance criteria

Clock tests use `FixedClock(...)` / `.advanced(...)` from `tests/fakes/clock.py` (stage7/data.md §8a, DAT-32), one clock
per moment (R-G-9); no second clock fake.

- [ ] AC-1 [invariant] `HandoffService.open` commits `cases`, `case_events`, `promises`, `actions(case_opened)`, `events(case_created)` and its staff-guidance `lookup_log` rows in one unit of work, or none of them — verify: `tests/services/test_handoff.py::test_open_writes_all_rows_in_one_transaction` and `::test_failure_after_case_row_leaves_no_rows` (`temp_sqlite()` from `tests/fixtures/sqlite.py`, a repository double that raises after the case insert) — evidence: first test finds the rows for the thread in each table; second finds zero in all of them.
- [ ] AC-2 [invariant] One open case per thread: a second `open` for a thread with an open case (different reason, the same `turn_id` repeated, or a safety request while a case is open) returns `created=False`, the same `case_ref`, writes no second `cases`, `actions` or staff-guidance row, adds one `case_event` for a new reason and keeps the higher priority; a `trigger="con4"` request always yields a case (created or already open), never a refusal (M-15) — verify: `tests/services/test_handoff.py::test_second_open_returns_already_open`, `::test_repeat_turn_is_idempotent`, `::test_new_reason_raises_priority`, `::test_con4_always_yields_case` — evidence: one `cases` row; P3 then P2 leaves the case at P2; a safety request on an open P3 case leaves one case at P0; repeat `turn_id` adds zero rows.
- [ ] AC-3 [invariant] Every stored promise is the policy table's, word for word, for its reason and presence (stage7/cases §3.2): WP-7 refund unstaffed → `R26.refund`, "A representative will get to your refund request within 2 business days." plus "I can't promise an outcome.", due Tue 2026-10-20 19:00; WP-8 `membership_cancel` unstaffed (renewal 2026-11-03) → `R26.unstaffed` "A representative will get back to you within 1 business day", P3, due Mon 2026-10-19 19:00; danger or burning_unclear unstaffed → `OD4.danger_review`, due Mon 2026-10-19 19:00; WP-5 safety → `R26.safety_none`, text "" and `due_at` None; any non-safety reason staffed → `R26.staffed` "A representative will join this chat when available", `live_queued=True`, state live-queued, `due_at` None, `conversations.live_state = 'queued'` — verify: `tests/services/test_handoff.py::test_promise_matches_table` (parametrised over every `HandoffReason` × {`nobody_online`, `simulated_on_shift`} with a `DemoService` double honouring stage7/cases §6 `presence(tx)` and `FixedClock` from `tests/fakes/clock.py`) — evidence: every stored `promises.text`, `policy_row` and `due_at` equal `promise_for(...)`'s; the live-queued rows have `live_state = 'queued'`.
- [ ] AC-4 [invariant] Fee-bearing change request (WP-4, CAS-10): `reason=fee_bearing_change`, `change_request.window_start` Fri 2026-10-16 12:00 → case P2, `cases.due_at` = 12:00 (window start), `promises.due_at` = Mon 2026-10-19 19:00 (the customer promise), `alert="supervisor_now"`; P0 and P1 also return `supervisor_now`, every other reason `None` — verify: `tests/services/test_handoff.py::test_fee_bearing_stores_both_dues` and `::test_alert_for_p0_p1_and_fee_bearing` — evidence: the two stored dues differ as stated; alert set for exactly P0, P1 and `fee_bearing_change`.
- [ ] AC-5 [negative] Promise text never comes from a model or a request: `HandoffService`, `CaseService` and `BriefAssembler` accept no promise-text argument; heading 6 ("What we told the customer") is built only from the stored `Promise`, and a `BriefExtraction` carrying promise-like text cannot change it — verify: `tests/unit/services/test_brief_assembler.py::test_heading_six_is_stored_promise` and `tests/services/test_handoff.py::test_no_promise_text_parameter` (signature inspection) — evidence: heading 6 text equals `case.promise.text`; no public method has a parameter named or typed as promise text.
- [ ] AC-6 [failure/refusal] Safety path (R-6, DO-1 §8.2): with `trigger="safety"` and a first write failure, the write is retried once; a second failure surfaces as a typed handoff failure (signal `case_write_failed`), never silently dropped; a P0 case is created even when `identity.customer_id` is None — verify: `tests/services/test_handoff.py::test_safety_write_retried_once` and `::test_safety_case_without_customer` — evidence: two attempts on a double that fails once and one case row; two failures → the typed failure; unmatched caller → one P0 row.
- [ ] AC-7 [invariant] Staff guidance reaches staff, never the customer (CAS-33, CAS-38): for `refund`, `fee_bearing_change`, `late_technician`, `billing_dispute` and `complaint_or_manager`, `open` appends one `lookup_log` row per `STAFF_GUIDANCE_FOR[reason]` passage with `tool = "staff_guidance"` and `message_id = handoff_anchor(thread_id)`; a CON-4 before any customer text names the greeting row; the assembled brief shows each as a heading 7 item with `source.kind = "lookup_log"`; no `ResponderInput` built from this thread's state contains the guidance text — verify: `tests/services/test_handoff.py::test_staff_guidance_attached_not_responded` and `::test_staff_guidance_anchor_without_customer_text` — evidence: one guidance row per passage with the anchor id; heading 7 item present; guidance text absent from the responder input.
- [ ] AC-8 [invariant] Nobody online never yields a live-queued case (R-30: 0 occurrences), and `convert_live_queued(now, tx)` turns every live-queued case into unassigned with the same reference and `created_at`, the promise status `changed` and its text, row and due recomputed by `promise_for(reason, "nobody_online", now)` (stage7/cases §3.2, §5 rules table), history kept, `shift_ended` to each affected thread stream and `chat_closed` (reason `shift_ended`) to each case stream, `live_state` back to `not_live`, all in the caller's transaction when `tx` is given, and returns the count — verify: `tests/services/test_cases.py::test_unstaffed_never_live_queued`, `::test_convert_live_queued`, `::test_convert_joins_caller_transaction` — evidence: 0 live-queued rows across all reasons unstaffed; converted count equals queued count; references and `created_at` unchanged; a rollback of the caller's transaction leaves every case live-queued.
- [ ] AC-9 [failure/refusal] `apply` (CON-13) enforces versions and rules: stale `expected_version` → `VERSION_CONFLICT` with `changed_by`, `changed_at`, `current_version`; claim on a claimed case → `CASE_ALREADY_CLAIMED`; release, close_unresolved, assign or change_priority without a reason → `REASON_REQUIRED`; wait without a wake-up → `WAKE_UP_REQUIRED`; resolve without an outcome → `OUTCOME_REQUIRED`; an action the state does not allow → `NOT_ALLOWED_IN_STATE`; assign or change_priority by a representative → `ROLE_NOT_ALLOWED`; assign maps `riley`/`supervisor` through `ASSIGNEE_ROLES` — verify: `tests/services/test_cases.py::test_apply_rejections` (one parametrised case per code) and `::test_apply_success_writes_event` — evidence: each rejection returns `CaseActionRejected` with the named code and changes no row; each success writes one `case_event` (actor role, action, reason), bumps `version` by 1, writes one `case_changed` event to `case:<ref>`, and every owner / claimed_by / changed_by string equals `STAFF_PERSONAS[role].name` ("Riley", "Demo supervisor").
- [ ] AC-10 [invariant] Promise status follows the promise due on the demo clock (CAS-21): resolving at or before `promises.due_at` marks it `kept`; after, `missed`; a `record_activity` with outcome `reached` or `left_message` at or before the promise due marks it `kept`; `no_answer` leaves it `open`; a promise with no due is `kept` on resolve — verify: `tests/services/test_cases.py::test_promise_status_kept_and_missed` (FixedClock before and after due) — evidence: statuses `kept`, `missed`, `kept`, `kept`, `open`, `kept` respectively, each change with a `case_event`.
- [ ] AC-11 [invariant] `queue`, `detail` and `oversight` apply stage7/cases §5's rules: `due_state` from the **case** due (`no_due_time` / `overdue` / `due_soon` within `DUE_SOON_WINDOW` / `on_time`), overdue a state and never a negative countdown; queue order P0, P1, then overdue, then case due ascending, then `created_at`, no-due rows after dated ones in a priority; oversight's five lanes in fixed order (P0 and P1 · Overdue · Due soon · Unowned (unassigned, age ≥ `UNOWNED_AFTER`, whatever the staffing) · Stuck waiting), each case in the first lane it qualifies for, empty lanes kept; `new_flags_count` from `core.reads.new_flags_count()`; CON-12 items carry the current value and `changed` from `core.reads.*` — verify: `tests/services/test_cases.py::test_queue_ordering`, `::test_oversight_lanes_fixed_order`, `::test_detail_current_value_changed` — evidence: row and lane order equal a hand-built expected list for the four seed-shaped cases of stage7/cases §7 at DEMO_START (MHC-C-0008 in P0 and P1, MHC-C-0005 Overdue, MHC-C-0006 and MHC-C-0007 Unowned); an invoice changed after the lookup shows `changed: true`.
- [ ] AC-12 [failure/refusal] `set_followup` (CON-5, R-27, consolidated §9.5): no open case → `NOT_ALLOWED_IN_STATE`; an unverified customer can save `general` only (`on_record` refused); channel, destination, on-record flag and window are stored; the returned destination is masked — verify: `tests/services/test_cases.py::test_set_followup_rules` — evidence: `on_record` rejected for `identity.status != verified`; stored row has all four fields; response label "the number ending in 02" for seeded MHC-10002.
- [ ] AC-13 [negative] Contact values never leave in views (security: follow-up contact details, slice plan §0): `QueueView` and `OversightView` rows carry the display name only, no phone, email or address; `CaseDetail` shows contacts masked ("the phone ending in 02") and codes redacted in the conversation; staff-only sources carry `audience: staff_only` and appear only in `detail` — verify: `tests/services/test_cases.py::test_no_contact_values_in_views` (seeded MHC-10002 Omar Patel, phone 512-555-0102, email on record) — evidence: `512-555-0102`, `5125550102` and the record's email are absent from the serialised `QueueView`, `OversightView` and `CaseDetail` and from every `case_event` row.
- [ ] AC-14 [negative] Nothing claims a send (R-34): every `Activity` carries the fixed label "Demo: recorded, not sent" from `policy/texts.py`; `record_activity` on an unclaimed case → `NOT_ALLOWED_IN_STATE`; no string returned by `set_followup` or `record_activity` contains "sent you", "emailed you" or "called you" — verify: `tests/services/test_cases.py::test_activity_recorded_not_sent` — evidence: label present on every activity; forbidden strings absent.
- [ ] AC-15 [invariant] The brief always has exactly eight headings in `BRIEF_TITLES` order with origins 1, 3, 5, 6, 8 `state` and 2, 4, 7 `extraction`; heading 4 `checked=False`; every item has at least one `SourceRef`; with `extraction=None` headings 2, 4, 7 are `not_generated` and the other five present; a `Quote` that is not an exact substring of a customer message of the thread is rejected; `attach_brief` twice for one case leaves one stored brief, the second — verify: `tests/unit/services/test_brief_assembler.py::test_eight_headings_in_order`, `::test_extraction_none_marks_not_generated`, `::test_quote_must_be_substring`, `::test_wp7_brief_items`, and `tests/services/test_cases.py::test_attach_brief_upserts` — evidence: the WP-7 brief has the refund quote under heading 2, the two claims under heading 4, the promise under heading 6; the failure case has five filled headings; one brief row after two calls.
- [ ] AC-16 [negative] Staff-only text never reaches the customer side: an `AccountResult.staff_notes` item (the INV-204411 fee-schedule mismatch) appears only as a heading 3 or 7 item with `source.kind = "lookup_log"`, and `BriefAssembler` exposes nothing a `ResponderInput` can read — verify: `tests/unit/services/test_brief_assembler.py::test_staff_notes_only_in_headings_3_or_7` — evidence: the note text appears only in those headings.
- [ ] AC-17 [capture] The WF-2 records exist after a handoff with their correlation IDs: `cases` with `case_ref`, `thread_id`, `turn_id`; `case_events`; `promises` with text, `policy_row`, `due_at`; `actions(case_opened)` keyed by `ActionKey`; `events(case_created)`; and the DO-6 check "a handoff left no case" counts 0 for the turn — verify: `tests/services/test_handoff.py::test_wf2_records_present` — evidence: each row carries the request's `thread_id` and `turn_id`; the check query returns 0. (CAP-3 through the real CON-4 entry point is AEA-51's; CAP-4 is AEA-52's.)
- [ ] AC-18 [invariant] `allowed_actions` on every `CaseSummary` that `queue`, `detail`, `apply` and `oversight` return comes from one pure function of (lifecycle, owner role, the viewing actor's role, the conversation's `live_state`, staffing), computed as `actions_for(case, live_state, staffing, actor) & ROLE_ACTIONS[actor.role]` (cases §5 rules table; staff.md §1; R-W-13, R-G-16), and it lists an action **if and only if** the server would accept it now from that role: for every lifecycle × role (representative, supervisor, owner) × live state the planner tabulates, each listed CON-13 action sent to `apply` with the current version is not refused with `ROLE_NOT_ALLOWED` or `NOT_ALLOWED_IN_STATE`, and each CON-13 action not listed is; the other keys follow the same rule against their own operation (`claim_and_join`, `join_chat`, `send_live_message`, `hand_back`, `close_chat` → `liveChatAction`, representative only, staff.md §5 checks; `log_call`, `log_email` → `recordContactActivity`, representative only; `flag` → `createFlag`, representative and supervisor). Fixed points: the owner always gets `[]`; the supervisor never gets `claim_and_join`, `join_chat`, `send_live_message`, `hand_back`, `close_chat`, `log_call` or `log_email`; the representative never gets `assign` or `change_priority`; `claim_and_join` only for the representative on a `live_queued` case while staffing is `simulated_on_shift`; `assign` and `change_priority` only for the supervisor; for the representative, the `getCase` DEFAULT, WAITING and LIVE_JOINED shapes and the `applyCaseAction` CLAIMED shape give exactly those examples' lists for the same lifecycle and live state (the supervisor examples ASSIGNED and PRIORITY_CHANGED disagree with each other and are not used, STF-18, R-W-13). The plan holds the full table (amendment AEA-29-1; staff audit A1) — verify: `tests/services/test_cases.py::test_allowed_actions_listed_iff_accepted` (parametrised over the table; `apply` real, a `LiveChatService` double honouring staff.md §5), `::test_allowed_actions_match_representative_examples` and `::test_allowed_actions_by_role` (one seeded-shape case per lifecycle, each role; R-G-16) — evidence: 0 listed-but-refused and 0 unlisted-but-accepted; the four example lists equal; the owner's lists all `[]`.
- [ ] AC-19 [invariant] Every display value on the case views has one producer and matches the OpenAPI example for the same input (cases §5 "by name only", made concrete): `reason` is display text from one map over `HandoffReason` (never the enum value such as `billing_dispute`); `priority.word` from one map over P0–P4; `due_label` from `policy/handoff.due_label` (cases §3.1), with the suffix ", the window start" exactly when the case due is a booked window start (WP-4); `age_label`, `follow_up_short`, `queued_at`, `other_cases[].status`, `identity.line`, `identity.demo_note` and `CaseSource.version_label` each from one named function; and `BriefItem.source_ids` use the same scheme as `CaseSource.source_id` (fixed in the plan and recorded in cases §5), so every id in any `source_ids` names a source in the same `CaseDetail` (amendment AEA-29-2; staff audit A2) — verify: `tests/services/test_cases.py::test_display_values_match_openapi_examples` (an MHC-C-0007-shaped case at DEMO_START, built as AC-11's seed-shaped fixtures per stage7/cases §7, against the `getCase` DEFAULT and `getQueue` SEEDED examples, field by field for the fields listed) and `::test_every_brief_source_id_resolves` (the four seed-shaped cases and the WP-4 and WP-7 cases) — evidence: each listed field equal to the example, or listed with the reason it differs (an example value STF-18 calls illustrative); 0 unresolved `source_ids`.
- [ ] AC-20 [negative] Staff reads never speak as or for the customer: in CON-12 `conversation`, every customer line's speaker is `{kind: "customer", display_name: CUSTOMER_SPEAKER_NAME}` ("Customer", staff.md §1; cases §5 rules table; R-W-14, R-G-16), never "You" (the OpenAPI example's customer-side wording) and never the customer's name or a contact value (amendment AEA-29-3; staff audit A3) — verify: `tests/services/test_cases.py::test_staff_conversation_customer_unnamed` and `::test_customer_speaker_name` (seeded MHC-10002 Omar Patel) — evidence: every customer line's `display_name` equals `CUSTOMER_SPEAKER_NAME`; no `display_name` in the serialised `CaseDetail` is "You", "Omar" or "Omar Patel".
- [ ] AC-21 [invariant] Only CON-13 actions, CON-15 activities and the scheduler and staffing transitions of cases §5 change a case's `version` or `lifecycle`; the conversation writes that live chat makes (controller, `live_state`, a representative message, `close`) change neither and append no `case_changed` (staff.md §5; R-W-16; amendment AEA-29-4; staff audit A4) — verify: `tests/services/test_cases.py::test_conversation_writes_keep_case_version` (a case at version n; the conversation-row writes `LiveChatService` makes, applied through the repositories; `detail` re-read) — evidence: version n and the lifecycle unchanged; 0 new `case_changed` rows.
- [ ] AC-22 [journey] Extends J-6 and J-7 (slice plan §0a journey map; J-7 is a proposed addition to the map for this ticket, from the join audits; `backend-amendments.md` §3): J-6, the escalated case appears in `getQueue` and `getCase` with eight headings, the policy promise, an `allowed_actions` list the server accepts for the viewing role, and every brief `source_ids` entry resolving to a source of the same case (staff audit A1, A2; AC-18, AC-19); J-7, after join, send and hand back the case `version` is unchanged (A4; AC-21); asserting what the user sees and what is stored, in `tests/journeys/j6/test_aea_29.py` and `tests/journeys/j7/test_aea_29.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-29.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-23 [invariant] `CaseService.detail` sets `CaseDetail.events.last_event_id` to the newest event id of `case:<ref>`, read in the same read transaction as the view, so a CON-21 connection resumed from it replays nothing the view already shows (Decision 2 option A, Innocent 2026-10-21; amendment AEA-29-5; staff audit B5). The field comes from the UX session's OpenAPI amendment (`docs/ux/**`); until it lands and the `CaseDetail` view type carries it, this AC is reported `blocked-on UX session: OpenAPI amendment`, never passed or dropped — verify: `tests/services/test_cases.py::test_detail_last_event_id_same_snapshot` (append events, read the detail, append one more) — evidence: the id equals the newest id at read time; only the later event is after it.
- [ ] AC-24 [regression/context] Same change updates: the area-map row for `services/cases.py` and `services/handoff.py` (planned → built, commit); the `.claude/state/icm-progress.md` row "Routes verified against code and tests" evidence if this is the first built A6 slice; DO-3 code-design status for these two modules (planned → built) and any contract gap found, recorded against stage7/cases §5 — verify: `git diff --name-only` — evidence: those files in the diff, only this ticket's rows.

### Observability

- Responsibilities: for WF-2 (and the case side of WF-1 and WF-4), emit `case`, `case_event` (actor role, action,
  reason), `promise` (text, policy row, due time, status changes), `actions(case_opened)`, the staff-guidance
  `lookup_log` rows, and `events` (`case_created`, `case_changed`, `shift_ended`, `chat_closed`), each carrying
  `thread_id`, `turn_id` and `case_ref` (DO-6 *Correlation*); signal `case_write_failed` on a failed safety write (system
  design §8.2). For WF-4, every CON-13 and CON-15 change writes one `case_event` with the actor role. Preserve DO-6's
  check "a handoff left no case" (expected count 0) by writing the case and the `case_opened` action in one transaction.
  No contact value in any `case_event` or event row (AC-13).
- Capture evidence: AC-17 at the service boundary (with AC-9 for the WF-4 `case_event`); CAP-3 (AEA-51) and CAP-4
  (AEA-51 relayed turn, AEA-52) drive the real entry points.

### Evaluation

- Checks: E-6 handoff and brief slice: promise and reference equal the policy table (invariant), required brief items
  present (assertion), no number, date, ID or amount in a brief that is not in the lookup log or chat (invariant, with
  AEA-15's fact check); E-1 hard gate "promise text equal to the table" on WP-4, WP-5, WP-7, WP-8. WF-4: flags feed the
  review list (R-37), never the eval set unreviewed; this ticket writes no flag (AEA-44) and adds nothing to the eval set.
- Expected-answer authority: the policy table (`PROMISE_TABLE`, stage7/cases §3.2) and the D4 priority table, never the
  model (DO-5 *Expected-answer authority*, "Handoff promise, priority and reference"); each case's hand-written
  required-item list for the brief.

### Metrics

- References: M-10 promise text consistency, M-11 brief required-item recall, M-12 invented facts in briefs, M-13 promises
  kept on time, M-15 person on the first request, M-27 unowned and overdue cases.
- Acceptance conditions: M-10 and M-13 stay computable from `promises.text`, `policy_row`, `due_at`, status and
  `case_events`; M-15 from CON-4 turns that always yield a case (AC-2; the `turn.outcome` row is AEA-42's); M-27 from
  `cases.owner_role` and `cases.due_at`; seed rows stay a named segment (`seed` flag). Targets are DO-7's approved ones
  (M-10 100%, M-12 0, M-11 ≥ 90%, M-13 ≥ 90%, M-15 100%), measured at Stage 9, not here.

### Blocked by

AEA-10 (`repos_cases`, `repos_core` incl. `core.reads.*`, `handoff_anchor`, `lookup_log.append`, every `.sql`), AEA-14
(`policy/handoff.py`: `promise_for`, `case_due_at`, `priority_for`, `STAFF_GUIDANCE_FOR`, `DUE_SOON_WINDOW`,
`UNOWNED_AFTER`, `due_label`), AEA-16 (the `StaffGuidance` type in `retrieval/manifest.py`; MC-26; wave 1). Also
imports, from wave 0: `domain/staff.py` with `ROLE_ACTIONS` and `CUSTOMER_SPEAKER_NAME` (AEA-02; R-W-13, R-W-14) and
`LookupRow` in `domain/tools.py` (AEA-02; R-G-8). All are waves 0–1, so no wave moves.

`LiveChatService` (AEA-46, same wave) is used only as a double honouring staff.md §5 (AC-18), and `tests/fakes/clock.py`
is AEA-11's (wave 1). AC-22's journey record names AEA-57 (harness, wave 2) and AEA-52 (the integrated staff side) as
*Blocked by* for its integrated level only (`integrated-journeys.md` §4); they are evidence-level dependencies, not merge
blockers, so no wave moves.

UX session: OpenAPI amendment (Decision 2 option A, Innocent 2026-10-21) — the UX session adds `CaseDetail.events.last_event_id`
to `docs/ux/03-structure/ui-contracts.openapi.yaml` in `docs/ux/**`; this ticket never edits the OpenAPI and uses the field only
after that lands. Evidence-level for the ticket, but AC-23 cannot be built without it: the field must exist in the
`CaseDetail` view type this service returns (cases A-2: fields from the OpenAPI, homed in `domain/` by the AEA-02 follow-up,
which this ticket must not edit). So AC-23 alone waits (`blocked-on UX session: OpenAPI amendment`, and on the AEA-02
follow-up carrying the field); every other AC proceeds, and no wave moves (the UX session is outside the wave graph).

### Agent handoff

- Area / owner: A6 Cases and handoff (area map); owns `src/meridian/services/cases.py`, `src/meridian/services/handoff.py`,
  their tests under `tests/services/` and `tests/unit/services/`, and its own `register_cases()` hunk in
  `web/container.py` (builds `CaseService`, `BriefAssembler`, `HandoffService`; the container resolves
  `STAFF_GUIDANCE_FOR` against `load_staff_guidance()` at AEA-51).
- Contracts and shared surfaces: consumes DO-4 §1/§5/§7/§13 types (AEA-02), stage7/cases §3 policy (AEA-14), §1.2
  repositories (AEA-10), `DemoService.presence(tx)` (AEA-30, same wave: injected double honouring stage7/cases §6),
  `LiveChatService` (AEA-46, same wave: double honouring staff.md §5, AC-18 only), `Clock`, `FixedClock` (AEA-11),
  `policy/texts.py` (AEA-03), `StaffGuidance` (AEA-16), `ROLE_ACTIONS`, `CUSTOMER_SPEAKER_NAME` and `LookupRow`
  (AEA-02). Produces `HandoffService`, `BriefAssembler` and
  `CaseService` for AEA-30, 31, 36, 38, 39, 42, 45, 46, 51, 52, 53. Must not edit `repos_cases.py`, `repos_core.py`, any
  `.sql`, `policy/*`, `domain/*`, `retrieval/*`, any route or schema file.
- Scope boundary / refusal: no routes, no SQL, no DDL, no model call (the brief extraction call is AEA-38's); no staff
  route may call `open_case` (DO-3 S-7, enforced by review grep in AEA-45/46). Promise text only from the table; never a
  waiver, refund or outcome promise (OD-4 ix); staff guidance never in a `ResponderInput` (R-10, HP-3).
- Evidence level (`.claude/rules/integrated-journeys.md` §4): these service tests are `mock-tested`; AC-22 extends J-6
  (case creation → staff queue → case with brief) and J-7 (live takeover leaves the case version alone) in
  `tests/journeys/j6/test_aea_29.py` and `tests/journeys/j7/test_aea_29.py`; until AEA-57 and AEA-52 land, the record
  states `mock-tested` and *Blocked by* AEA-57, AEA-52.
- Note for the orchestrator: amendment AEA-29-3 as written in `backend-amendments.md` says `display_name: null`; the
  contract (staff.md §1, cases §5 rules table; R-W-14, R-G-16) says `CUSTOMER_SPEAKER_NAME` ("Customer"). AC-20 follows
  the contract (DO-4 §16: the addendum wins); both forbid "You" and any name or contact value.
- Wave and gates: wave 2; no human or external gate. Critical-path ticket (AEA-02 → 10 → 29 → 51): the planner may split
  steps inside the ticket, not the ticket.
- Lane: build-loop — changes source and tests that code reads (ticket-lanes).
- Risk: security (`risk::security`, slice plan §0) — it stores follow-up contact details and builds every staff view of
  a customer; a bug could show a full phone number or email in a queue row, a case event or a log, or save an on-record
  destination for an unverified customer. `test-writer-agent` freezes AC-12, AC-13 and AC-20 (and AC-7's staff-only half)
  failing first; `security-privacy-agent` reads this diff at the wave-2 merge.
- Decided by Innocent 2026-10-21: join Decision 2 option A (`docs/plans/ux-join/decisions-for-innocent.md`) — amendment
  AEA-29-5 applied as AC-23 (`CaseDetail.events.last_event_id` read in the view's snapshot). The OpenAPI change is the UX
  session's (`docs/ux/**`); this ticket uses the field only after it lands (*Blocked by*).
- Awaiting Innocent: GRC-3 — built on the recommended option A (a safety turn while a person holds the chat still calls
  `open`, which returns the existing case raised to P0, AC-2); under B or C no safety handoff reaches `open` while a
  person holds the chat, and AC-2's safety-on-open-case path is exercised only outside live chat.
- Awaiting Innocent: CAS-16 — built on the recommended option A (no code here: AEA-02 adds `burning_ruled_out` and AEA-14
  its P2 row, and AC-3's parametrisation picks the new reason up); under A its case due would be the booked window
  start, like `fee_bearing_change` (AC-4's two-dues storage); under B (P1) its promise row becomes `OD4.danger_review` and
  `alert = "supervisor_now"`; under C nothing here changes.
- Entry points added or changed: WF-2 (services behind CON-4, CON-5) and WF-4 (services behind CON-11…CON-13, CON-15,
  CON-17); their HTTP entry points are AEA-42, AEA-45, AEA-51, AEA-52.
