# Plan — [AEA-14] policy: promises, priorities, escalation decision

**Status:** planned — READY; **BLOCKED-ON AEA-02** (domain types) until it is on `main` (see §9)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/14 (identical to
`docs/plans/tickets/AEA-14.md`) · **Base revision:** `main` at `16ca639` (refreshed 2026-10-21; AEA-01, AEA-03, AEA-04,
AEA-08 and AEA-25 are merged; **AEA-02 is not**: `src/meridian/domain/` holds only `__init__.py`). Cut the worktree from
`main` **after AEA-02 merges**. · **Wave:** 1 · **Lane:** build-loop · **Risk:** none (no `risk::security`: no frozen
tests, no security agent)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (first written against `bc02266`; refreshed against
`16ca639`) · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates for AEA-14 (suggested `aea-14-policy-handoff-escalation` in
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-14`).

**What changed in the 2026-10-21 refresh** (so a reader of the older version knows): (1) AEA-03's `policy/texts.py` and
AEA-01's scaffold are now on `main`, so only AEA-02 blocks; (2) exact import homes now come from AEA-02's plan §4.0
(re-exports), not a grep guess; (3) **AC-15's source scan now bans only `Promise(...)` and `Promise.model_construct(...)`
and explicitly allows `Promise.model_validate(...)`**, because AEA-10's plan (§4.1, lines 211–213) rebuilds stored
promises with `Promise.model_validate({...})` in `repos_cases.py`; the older scan would have gone red when AEA-10
merged (§8 R-9); (4) `icm-progress.md` on `main` has two *Routes verified* rows (a merge artefact); step 9 says which
one to edit.

---

## 1. Goal and sources

### Goal

From the issue's *What to build* (US-14): "As a homeowner whose request needs a person, I need a reference number, the
exact promise (who gets back to me and by when), and a choice of email or phone and a time window, so that I know what
happens next and never repeat my story." This ticket delivers the two **pure, code-only** modules that decide that
promise and the escalation behind it (R-25, R-26; HP-4 B):

- `src/meridian/policy/handoff.py`: business days and due times, the promise table, `promise_for`, `case_due_at`,
  `priority_for`, two thresholds, the staff-guidance prefixes, and the D4 rows.
- `src/meridian/policy/escalation.py`: `decide_escalation(inputs) -> EscalationDecision`, rules 1–8, first match wins.

**Concretely, what the implementer delivers** (the ticket's worked pairs):

| Input | Output |
|---|---|
| WP-7: `promise_for(HandoffReason.REFUND, "nobody_online", Fri 2026-10-16 10:00 Chicago)`; `priority_for(REFUND)` | `Promise(policy_row="R26.refund", text="A representative will get to your refund request within 2 business days.", due_at=2026-10-20T19:00-05:00, due_label="Tuesday, October 20, 7:00 pm", extra_lines=("I can't promise an outcome.",), live_queued=False)`; `Priority.P3` |
| WP-4: a `SchedulingResult(status="staff_change_request")` in `EscalationInputs`, Fri 10:00, then `promise_for(FEE_BEARING_CHANGE, "nobody_online", Fri 10:00, window_start=Fri 2026-10-16 12:00)` | decision `escalate`, `fee_bearing_change`, `P2`, `rule_id="R21.fee_bearing"`; promise `R26.unstaffed` due Monday, October 19, 7:00 pm with extra lines "I can't promise anyone will confirm a change before your appointment starts; until a representative confirms, please plan on the technician arriving 12:00 pm – 4:00 pm." and "Phone support is open until 7:00 pm today if you'd like to call."; `case_due_at(...)` = 2026-10-16T12:00-05:00 (the window start) |
| WP-8: plan `handoff_request=MEMBERSHIP_CANCEL`, an `AccountResult` whose membership renews 2026-11-03, `now` Fri 10:00 | `escalate`, `membership_cancel`, `P3`, `rule_id="D4.membership_cancel"` (renewal 2026-10-19 instead → `P2`) |

### Context

Wave 1. Both modules are pure functions over AEA-02's domain types and AEA-03's sentences; nothing here stores, sends or
calls a model. They are called later by `HandoffService` / `CaseService` (AEA-29), the scheduler (AEA-30), the seeds
(AEA-31), the safety path (AEA-36), the act node (AEA-39) and the eval's M-10 check (AEA-24); AEA-10 (same wave) only
rebuilds stored `Promise` rows and never imports this module. `policy/escalation.py` was moved from wave 3 into this
wave-1 ticket by the slice plan §2 (it is pure). Decisions D-4…D-15 were all taken as recommended
(`docs/plans/stage7-signoff.md`); D-14 keeps CAS-16 on option A, so the burning-smell "both ruled out" row
(`burning_ruled_out`, P2) is **built**, not left as `NotImplementedError` (the "PENDING Innocent" comment in cases §3.3
and the older note in graph-nodes §6 predate D-14).

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-14.md` | AC-1…AC-19; worked pairs WP-4, WP-7 (+ WP-8 in AC-17); CAS-16 option A (Agent handoff); must not edit `policy/texts.py`, `domain/*`, `policy/booking.py` |
| Cases addendum (wins over DO-4 §6–§7) | `docs/design/contracts/stage7/cases.md` §3.1–§3.4 (lines 319–423), §5 (`STAFF_GUIDANCE_FOR`) | every constant and signature in §4 below; rule table rows 4, 6, 7; residuals R-G-14 (rule ids), R-G-15 (`EscalationInputs.now`) |
| DO-4 | `docs/design/contracts/internal-components.md` §6, §7, §4 (`Plan`), §5 (results), §1 (`IdentityState`, `FailureCounters`), §11 (`Halt`), §16. Changed since `bc02266` only in §5/§13/§14 comments (AEA-08), none affecting this ticket | `EscalationInputs`, `EscalationDecision`, `HandoffReason`, `Priority`, `Promise`, `promise_for` signature; rule order |
| Graph addenda | `stage7/graph-core.md` §8 (`FailureCounters` writers; thresholds stay in rule 7), §10 (GRC-2, lines 439–443: "`policy/handoff.py` (AEA-14) is its only constructor … `Promise(` appears outside `policy/handoff.py` and `tests/`"); `stage7/graph-nodes.md` §5 (`Plan.planner_failed`), §6; `stage7/graph-tools.md` §3 (`MembershipView.renewal_date`) | rule 6's planner row; rule 4's renewal date; AC-15 scan |
| Data addendum | `stage7/data.md` §2 (`policy/texts.py`) | all customer words come from `policy/texts.py`; never typed here |
| AEA-03 code on `main` | `src/meridian/policy/texts.py` (`__all__ = PLACEHOLDERS, TEXTS, TextId, TextRenderError, format_usd, render`) | §4a text ids and `render` signature, copied from the file |
| AEA-02 plan (types not yet on `main`) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0 (homes and re-exports), §4.1, §4.4, §4.5, §4.6, §4.8 | the exact import homes and field lists in §4a and §6 |
| AEA-10 plan (same wave) | `docs/plans/fanout/2026-10-21-build/AEA-10.md` §4.1 lines 211–213, 1184 | rebuilds stored promises with `Promise.model_validate` → AC-15's scan must allow it (§8 R-9) |
| Decision ledgers | `docs/plans/7b-decisions/cases.md` CAS-9…CAS-16, CAS-20, CAS-33; `residuals-graph.md` R-G-14, R-G-15; `docs/plans/stage7-signoff.md` D-4…D-15 | as cited per row in §3; D-14 → CAS-16 option A |
| Code design (DO-3) | `docs/design/code-design.md` §2.1 (pure core imports nothing that does I/O), §3 (line 181 `**Built:**`), §4.1 | `policy/handoff.py` depends on handoff types + texts; `policy/escalation.py` on turn types + `policy/handoff` |
| System design (DO-2) | `docs/design/system-design.md` §8.1–§8.3 (*Promise and due time: refuse to improvise*) | promise and due from code only; one retry then handoff (rule 6) |
| Requirements | PRD R-6, R-7, R-8, R-16, R-21, R-22, R-24, R-25, R-26, R-27; US-14; WP-4, WP-5, WP-6, WP-7, WP-8 | rows in §3 |
| Product direction | `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md` §6 *Priority*, *The promise record*; §9.3; §9.4 (D4 table, lines 886–927) | P0–P4 classes; the 15 D4 rows verbatim (parse re-run 2026-10-21 on `16ca639`: 15 rows, equal to the literal in step 5) |
| UX copy (read only) | `docs/ux/03-structure/SCREEN_SPECS.md` lines 115, 147, 152–153 | can't-guarantee line "when the window starts before the promise"; phone line "only while phone support is open"; OD4 separate line |
| KB (issued, read only) | `knowledge_base/internal/agent_discretion_notes.md` (all four distinct prefixes found once each, re-checked 2026-10-21); `faq/customer_faq.md` (phone hours); `policies/holiday_hours_2026.png` (via CAS-9) | staff-guidance prefixes are substrings of the notes file; holidays; hours |
| Issued data (read only) | `docs/data/issued/meridian_dataset/scheduling_db/SCHEMA.md` line 25 | the four windows `08:00-12:00`, `12:00-16:00`, `13:00-17:00`, `16:00-19:00` (used to name the window end, step 3) |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` E-6, E-1/E-3/E-4 | promise must equal the policy table; this ticket supplies the table, the harness is AEA-24 |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-1, WF-2 (`case`, `case_event`, `promise`) | no record of its own (pure); supplies `promise.text`, `policy_row`, both dues, `rule_id`, `degraded` |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-10, M-13, M-27; M-19, M-20 | M-10 compares `promise.text` with importable `PROMISE_TABLE`; M-13 needs tz-aware `Promise.due_at`; M-27 needs `case_due_at` |
| Tool config on `main` | `pyproject.toml` (ruff line 110, rules `E W F I B UP S RUF`, `S101` allowed only in `tests/**`; mypy strict + `pydantic.mypy` with `init_typed = true`; tests may be untyped) | the gates in §7 and the typing notes in §6 |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3 rule 1, §4; `context-maintenance.md`; workspace `code-design-solid-modularity.md` | affected tests only; journey record `mock-tested`, *Blocked by* AEA-57; context rows updated in the same change; pure core, no new seam |

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Action | Notes |
|---|---|---|
| `src/meridian/policy/handoff.py` | **create** | §4b, §5 steps 1–5 |
| `src/meridian/policy/escalation.py` | **create** | §5 step 6 |
| `tests/unit/policy/test_handoff.py` | **create** | 20 tests (§7) |
| `tests/unit/policy/test_escalation.py` | **create** | 13 tests (§7) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-14.md` | **create** | AC-18 record; `<YYYY-MM-DD>` = `date +%F` on the commit day |
| `.claude/reference/area-map.md` | **modify: two *Status* cells only** (the last column) | the A6 row and the A7b row (step 9) |
| `docs/design/code-design.md` | **modify: the one `**Built:**` line under §3's first paragraph** (line 181 on `16ca639`) | append this ticket's two files (step 9) |
| `.claude/state/icm-progress.md` | **modify: one row only** | *Routes verified against code and tests*, the row named in step 9 |

`tests/unit/policy/__init__.py` already exists (AEA-01). Do not add a `conftest.py`; every helper lives inside the two
test files. `tests/unit/policy/test_handoff.py` does not collide with AEA-02's `tests/unit/domain/test_handoff.py`
(both folders have `__init__.py`, so pytest names them `tests.unit.policy.test_handoff` and
`tests.unit.domain.test_handoff`).

### Shared surfaces: read only (import or read, never edit)

`src/meridian/domain/*` (AEA-02), `src/meridian/policy/texts.py` (AEA-03), `src/meridian/policy/__init__.py`,
`pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/journeys/**` (AEA-01), every `docs/design/**` contract,
`docs/plans/**` (this plan is the planner's), the consolidated direction doc, the KB, SCREEN_SPECS.

### Other tickets' files: never touch

`policy/texts.py` (a missing sentence is a follow-up on AEA-03), `policy/booking.py` (AEA-13), `policy/limits.py`
(AEA-01), `domain/*` (AEA-02; a missing field or enum value is a follow-up on AEA-02), `adapters/**` (AEA-02, AEA-10),
`services/*` (AEA-29, 30, 31), `agent/**` (AEA-21, 36, 37, 39), `tests/unit/test_import_direction.py` (AEA-01/02/03/04/05
append to it; this ticket puts its purity test in `test_escalation.py` instead, as AC-16 names), `tests/fakes/**`
(AEA-11), `apps/web/**`, `docs/ux/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, the briefing, issued data,
`docs/archive/`, `docs/parked/`.

---

## 3. Requirements table

### 3a. Acceptance criteria (verbatim IDs from the issue) and how each is built and verified

Every test below is in `tests/unit/policy/test_handoff.py` (H) or `tests/unit/policy/test_escalation.py` (E). Clock
values are `datetime(..., tzinfo=ZoneInfo("America/Chicago"))`. `FRI_10 = 2026-10-16 10:00`.

| AC | Requirement (short; full text in the issue) | Built by | Verified by |
|---|---|---|---|
| AC-1 | `business_due` per cases §3.1; Saturday never a business day | step 1 | H `test_business_due_after_hours` (Fri 10:00 +1 → Mon 10-19 19:00; +2 → Tue 10-20 19:00; Fri 20:00 +1 → Mon 19:00; Mon 10-19 08:00 +1 → Tue 10-20 19:00), `test_business_due_weekend` (Sat 10-17 10:00 and Sun 10-18 10:00 +1 → Mon 10-19 19:00; `is_business_day(date(2026,10,17))` False, `(2026,10,18)` False, `(2026,10,19)` True), `test_business_due_thanksgiving` (Wed 2026-11-25 10:00 +1 → Mon 2026-11-30 19:00, offset −06:00; `is_business_day` False on 11-26, 11-27) |
| AC-2 | `phone_support_open` six values | step 1 | H `test_phone_support_hours`: Fri 10-16 10:00 True; Fri 10-16 19:30 False; Sat 10-17 09:00 True; Sun 10-18 10:00 False; Fri 2026-12-25 10:00 False; Thu 2026-12-24 13:00 False |
| AC-3 | Nobody online, other reasons → `R26.unstaffed`, due Mon 19:00, label | step 3 | H `test_unstaffed_promise_and_due` |
| AC-4 | Refund → `R26.refund`, extra line, due Tue 19:00 (WP-7) | step 3 | H `test_wp7_refund_promise` |
| AC-5 | Staffed → `R26.staffed`, no due, `live_queued` True | step 3 | H `test_staffed_promise` |
| AC-6 | Safety → `R26.safety_none`, "", no due, P0 | steps 3, 4 | H `test_safety_promises_no_time` |
| AC-7 | Danger / burning-unclear unstaffed → `OD4.danger_review` | step 3 | H `test_p1_danger_review_line` |
| AC-8 | Fee-bearing lines; `case_due_at` (+ CAS-16 case) | step 3 | H `test_wp4_fee_bearing_lines_and_case_due` |
| AC-9 | Every `Promise.text` is a table value; table == texts | steps 2, 3 | H `test_promise_texts_are_the_table` |
| AC-10 | `priority_for` per reason (+ CAS-16 assertion) | step 4 | H `test_priority_per_reason` |
| AC-11 | `D4_ROWS` = consolidated §9.4 (15 rows); `STAFF_GUIDANCE_FOR` five reasons, KB substrings | step 5 | H `test_d4_rows_and_staff_guidance` |
| AC-12 | `decide_escalation` order, first match; rule ids | step 6 | E `test_rule_order_first_match`, `test_rule7_two_timeouts` |
| AC-13 | Rule 6 four triggers → `ai_failure` P3 degraded | step 6 | E `test_rule6_single_failed_specialist`, `test_rule6_models_disabled`, `test_rule6_halt_and_planner_failed` |
| AC-14 | Unverified/locked + private task → `identity_unverified` P3 | step 6 | E `test_unverified_private_task_escalates` |
| AC-15 | `Promise(` only in `policy/handoff.py`; no staff text in customer text | steps 3, 5 | H `test_promise_construction_and_no_staff_text` (scan rule in §7: `Promise(...)` and `Promise.model_construct(...)` banned; `Promise.model_validate(...)` allowed for stored-row rebuilds, R-9) |
| AC-16 | Both modules pure | steps 1–6 | E `test_policy_modules_are_pure` |
| AC-17 | `membership_cancel` uses `business_due(now, 1)` whatever the presence | step 6 | E `test_membership_cancel_priority_uses_business_due` |
| AC-18 [journey] | No journey yet: record at `mock-tested`, *Blocked by* AEA-57, names J-4, J-5, J-6; affected command prints "0 journeys affected" | step 9 | the record + `uv run python -m tests.journeys.affected --base main --list-only` |
| AC-19 | Area map A6 + A7b rows, ICM row, code-design §3 *Built* line | step 9 | `git diff --name-only main...HEAD` lists the three files |

### 3b. Source-contract reconciliation (obligations the issue's ACs do not spell out)

| Obligation | Governing source | In ticket | Disposition | Plan step / owner |
|---|---|---|---|---|
| CAS-16 option A: `burning_ruled_out` → P2; promise falls to `R26.unstaffed` / `R26.staffed`; `case_due_at` = window start, else promise due; one AC-10 assertion, one AC-8 case | ticket *Agent handoff*; D-14; cases ledger CAS-16 | yes (Agent handoff) | in-ticket | steps 3, 4; asserted in AC-8 and AC-10 tests |
| Escalation rule 4 row for `burning_ruled_out` (the graph-nodes §6 code-built plan carries it): escalate, `priority_for` (P2), `rule_id="R7.burning_ruled_out"` | graph-nodes §6; PRD R-7; ticket rule 4 "other D4 rows escalate … per the row" | reason yes, id no | **added** (id chosen here: R-7 is its requirement, same `R<n>.` style as R2/R16/R21/R24) | step 6; E `test_rule4_burning_ruled_out_and_unexpected_reason` |
| Rule 4 with any other plan reason (never produced today): escalate with `priority_for(reason)`, `rule_id=f"PLAN.{reason.value}"` (safe default: a handoff, never a silent "none") | source-authority rule 7 ("a confident wrong answer is worse than a handoff") | no | **added** | step 6; same test |
| Rule 2 also fires when the **plan** carries an R-24 reason (the planner's `refund`, `billing_dispute`, `complaint_or_manager`), because `join_plan` folds the policy word into `Plan.handoff_request` (DO-4 §4) and R-24 treats them alike; `rule_id` stays `R24.<reason>` | DO-4 §4 `Plan.handoff_request` "from the planner's `handoff` field or a policy word"; R-24 | no | **added** | step 6; E `test_rule2_ids_for_every_policy_reason` |
| Rule 8's `rule_id` (field is required): `"none"` | DO-4 §6 (`rule_id: str`, required) | no | **added** | step 6 |
| Rule 5's "private task open" = a planned task with `needs_identity`, or an account/scheduling result with status `not_verified` | DO-4 §6 row 5; §4 `PlannedTask.needs_identity`; §5 statuses | no (undefined) | **added** (definition) | step 6 |
| On a short day (2026-12-24, closes 12:00) the due is that day's close (12:00), not 19:00 | cases §3.1 "Close of business on the `days`-th business day"; `SHORT_DAYS` | ticket says "19:00" | **added** (the contract's wording; see §8 R-3) | step 1; H `test_business_due_short_day_and_new_year` |
| The phone-support line says "until 7:00 pm today", so it is added only when phone support is open **and** today's phone close is 19:00 (Mon–Fri, not a short day). On a Saturday (closes 16:00) it would be false, so it is omitted | SCREEN_SPECS line 153 "only while phone support is open"; FAQ hours; source-authority rule 7 | ticket: "when `phone_support_open(now)`" | **added** (narrower, never false; AC-8's weekday and Sunday cases are unchanged; see §8 R-2) | step 3; H `test_fee_bearing_phone_line_never_false` |
| The can't-guarantee line needs the window **end** ("12:00 pm – 4:00 pm") but `promise_for` receives only `window_start` (DO-4 §7 signature unchanged; `ChangeRequestDraft` has only `window_start`). The end is read from the four issued windows, whose starts are unique (SCHEMA.md; 528 slot rows checked 2026-10-21: 180 / 150 / 150 / 48) | cases §3.2; SCHEMA.md line 25 | no | **added** (see §8 R-1) | step 3; H `test_window_text_from_issued_windows` |
| `case_due_at` for `FEE_BEARING_CHANGE` with `window_start=None` returns `promise.due_at` (the contract body would return `None`; a fee-bearing request always carries a window start, so this branch only guards a case from losing its due) | cases §3.2 body; CAS-10; M-27 | no | **added** | step 3.6; H `test_wp4_fee_bearing_lines_and_case_due` (e) |
| Naive datetimes are refused (`ValueError`, names only), so every due is tz-aware Chicago (M-13) | M-13; FixedClock rule (data.md §8a) | partly (AC-1 "tz-aware") | **added** | step 1; H `test_naive_times_and_bad_days_refused` |
| `due_label` format incl. morning and noon ("8:00 am", "12:00 pm") | cases §3.1 `due_label` | example only | **added** | step 1; H `test_due_label_format` |
| `decide_escalation`'s `priority` always equals `priority_for(...)` | ticket "priority always comes from `priority_for`" | yes (prose) | in-ticket, asserted | E `test_rule_order_first_match` checks it per scenario |
| GRC-2 scan scope: `Promise(...)` and `Promise.model_construct(...)` outside `policy/handoff.py` are banned; `Promise.model_validate(...)` (rebuilding a stored row, AEA-10) is allowed | graph-core §10 wording "`Promise(` appears outside"; AEA-10 plan §4.1 | yes (AC-15) | in-ticket, scope stated | H `test_promise_construction_and_no_staff_text`; §8 R-9 |
| `STAFF_GUIDANCE_FOR` resolved against `load_staff_guidance()` at start-up; unmatched prefix fails start-up | cases §5, CAS-33 | no | other-ticket: **AEA-51** (container) and AEA-29 (writes the `lookup_log` rows) | — |
| Both dues stored (`cases.due_at` from `case_due_at`, `promises.due_at` from `Promise.due_at`) | CAS-10 | no | other-ticket: **AEA-29** (stores), **AEA-30** (overdue vs missed) | — |
| `Promise.text` stays the **template** (`{due_label}`, `{case_ref}` unfilled for `R26.unstaffed`); rendering with the reference happens where the reference exists | AC-9 ("table string … character for character"); AEA-03 texts; cases §3.2 | implied | in-ticket (AC-9); rendering is **AEA-21** (`ReplyComposer.handoff_block`) / **AEA-29** | — |
| Wire `policy_row` value (OpenAPI examples show `nobody_online_1_business_day`; schema is a free `string`) | OpenAPI `PromiseView.policy_row` | no | n/a here: any string is valid; the staff serialiser (AEA-45) decides what it shows | — |
| Container / composition: none (pure module, no `register_<area>()` hunk) | slice plan §3 | — | n/a: nothing to register | — |

### 3c. Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — (pure functions; WF-1 / WF-2 carry their values: AEA-51, AEA-29) |

---

## 4. Shared code to use

### 4a. Imports (exact names and modules)

**Text module — on `main` now** (`src/meridian/policy/texts.py`, AEA-03):

```python
from meridian.policy.texts import TEXTS, TextId, render
# TEXTS: Final[Mapping[TextId, str]]            (MappingProxyType)
# def render(text_id: TextId, /, **values: str) -> str      # raises TextRenderError (a KeyError) on a missing or extra placeholder
```

The `TextId` members this ticket reads (values and texts copied from the file):

| Member | Value | Text |
|---|---|---|
| `PROMISE_UNSTAFFED` | `"promise.unstaffed"` | "No representative is online right now. A representative will get back to you within 1 business day, by {due_label}. Your reference is {case_ref}." |
| `PROMISE_REFUND` | `"promise.refund"` | "A representative will get to your refund request within 2 business days." |
| `PROMISE_REFUND_NO_OUTCOME` | `"promise.refund_no_outcome"` | "I can't promise an outcome." |
| `PROMISE_STAFFED` | `"promise.staffed"` | "A representative will join this chat when available. You can keep chatting with me while you wait, if you like." |
| `PROMISE_DANGER_REVIEW` | `"promise.danger_review"` | "No representative is online right now, so someone will review this online request within 1 business day. That is not the wait for emergency help; for that, please use the emergency line." |
| `PROMISE_SAFETY_NONE` | `"promise.safety_none"` | "" |
| `FEE_CANT_GUARANTEE` | `"fee_change.cant_guarantee"` | "I can't promise anyone will confirm a change before your appointment starts; until a representative confirms, please plan on the technician arriving {window}." |
| `FEE_PHONE_SUPPORT_OPEN` | `"fee_change.phone_support_open"` | "Phone support is open until 7:00 pm today if you'd like to call." |

**Domain types — from AEA-02 (not on `main` yet).** AEA-02's plan §4.0 defines several types in a lower module and
re-exports them from their home; **import from the home** in this column (the same object either way):

| Name | Import from | Used in |
|---|---|---|
| `HandoffReason`, `Priority`, `Presence`, `Promise` | `meridian.domain.handoff` | both modules + tests |
| `EscalationInputs`, `EscalationDecision`, `GateDecision`, `GateKind`, `RuleMatches`, `Plan`, `PlannedTask`, `TaskIntent` | `meridian.domain.turn` | escalation (`EscalationInputs`, `EscalationDecision`, `GateKind`) + tests |
| `AccountResult`, `SchedulingResult`, `KnowledgeResult`, `MembershipView`, `ChangeRequestDraft` | `meridian.domain.specialists` | escalation (`AccountResult`, `SchedulingResult`) + tests |
| `IdentityState`, `FailureCounters` | `meridian.domain.state` | tests only (escalation reads them as attributes) |
| `Halt`, `HaltReason` | `meridian.domain.common` (no other home) | tests only |

Shapes relied on (AEA-02 plan §4.1, §4.4, §4.5, §4.8 — DO-4 §6–§7 with the stage-7 additions; copy, do not change):

```python
class HandoffReason(StrEnum):   # 16 values: DO-4 §7's 15 + BURNING_RULED_OUT (CAS-16 A, D-14)
    SAFETY = "safety"; DANGER = "danger"; BURNING_UNCLEAR = "burning_unclear"
    CUSTOMER_REQUESTED_PERSON = "customer_requested_person"; REFUND = "refund"; BILLING_DISPUTE = "billing_dispute"
    COMPLAINT_OR_MANAGER = "complaint_or_manager"; LEGAL_OR_CHARGEBACK = "legal_or_chargeback"; COMMERCIAL = "commercial"
    LATE_TECHNICIAN = "late_technician"; FEE_BEARING_CHANGE = "fee_bearing_change"; MEMBERSHIP_CANCEL = "membership_cancel"
    UNSUPPORTED_ACTION = "unsupported_action"; IDENTITY_UNVERIFIED = "identity_unverified"; AI_FAILURE = "ai_failure"
    BURNING_RULED_OUT = "burning_ruled_out"

class Priority(StrEnum): P0 = "P0"; P1 = "P1"; P2 = "P2"; P3 = "P3"; P4 = "P4"
Presence = Literal["nobody_online", "simulated_on_shift"]          # cases A-1

class Promise(MeridianModel):                       # fields only, NO validator (GRC-2); frozen, extra="forbid"
    policy_row: str
    text: str
    due_at: dt.datetime | None
    due_label: str | None
    extra_lines: tuple[str, ...] = ()
    live_queued: bool = False

class EscalationInputs(MeridianModel):
    gate: GateDecision
    plan: Plan | None
    results: tuple[SpecialistResult, ...]            # Annotated[KnowledgeResult | AccountResult | SchedulingResult, discriminator="kind"]
    counters: FailureCounters                         # failed_answers, tool_failures, identity_failures, corrections, timeouts, bookings (all int = 0)
    identity: IdentityState
    halt: Halt | None
    models_disabled: bool
    now: dt.datetime                                  # R-G-15

class EscalationDecision(MeridianModel):
    outcome: Literal["none", "offer", "escalate"]
    reason: HandoffReason | None
    priority: Priority | None
    rule_id: str
    degraded: bool = False

class RuleMatches(MeridianModel):   # all seven required
    safety: SafetyKind | None; burning_unclear: bool; danger_words: bool; person: bool
    policy_trigger: HandoffReason | None; rule_ids: tuple[str, ...]; correction: bool
class GateKind(StrEnum):            # AI_PAUSED, SAFETY, BURNING_ASK, BURNING_ANSWER, DANGER_RULE, PERSON = "person",
                                    # CODE_ENTRY, LOCATE, CARD_CHOICE, FREE_TEXT = "free_text"
class GateDecision(MeridianModel):
    kind: GateKind; rules: RuleMatches; burning_answer: Literal["yes", "no", "unsure"] | None = None
    resume_task_id: str | None = None
class TaskIntent(StrEnum):          # ANSWER_QUESTION, READ_INVOICE = "read_invoice", READ_MEMBERSHIP, READ_APPOINTMENTS,
                                    # READ_WARRANTY, BOOK_NEW, RESCHEDULE, CANCEL, CONFIRM
class PlannedTask(MeridianModel):
    order: int (1..3); specialist: Literal["knowledge", "account", "scheduling"]; intent: TaskIntent
    needs_identity: bool; resumes_task_id: str | None = None
class Plan(MeridianModel):
    mode: Literal["talk", "act"]; tasks: tuple[PlannedTask, ...] (max 3); handoff_request: HandoffReason | None
    topic: Literal["booking", "membership", "billing", "warranty", "other"]
    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]; planner_failed: bool = False
class IdentityState(MeridianModel):
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None; masked_hint: str | None; code_expires_at: dt.datetime | None
    tries_left: int (0..3); codes_sent: int (0..3); verified_at: dt.datetime | None
class Halt(MeridianModel): reason: HaltReason; node: str; elapsed_ms: int     # HaltReason.BRAKE_TASKS = "brake_tasks"
class MembershipView(MeridianModel): tier: Literal["none", "standard", "plus"]; renewal_date: dt.date | None
class ChangeRequestDraft(MeridianModel):
    appointment_id: int; change: Literal["move", "cancel"]; wanted_text: str; windows_shown: tuple[int, ...]
    hours_before: float; window_start: dt.datetime
class KnowledgeResult(MeridianModel):   # kind="knowledge"; status: "answered" | "no_current_source" | "failed"
    passages: tuple[Passage, ...]; points: tuple[KnowledgePoint, ...]; quick_checks = (); tools: tuple[...]; calls: tuple[...]
    brake: HaltReason | None = None; failure: ProviderFailure | None = None
class AccountResult(MeridianModel):     # kind="account"; status: "read" | "not_verified" | "failed"
    invoices = (); membership: MembershipView | None = None; warranty = None; staff_notes = (); tools; calls; brake = None; failure = None
class SchedulingResult(MeridianModel):  # kind="scheduling"; status: "windows_shown" | "written" | "staff_change_request"
    # | "slot_taken" | "out_of_area" | "no_fit" | "not_verified" | "booking_cap" | "failed"
    windows = (); write = None; change_request: ChangeRequestDraft | None = None; quick_checks = (); tools; calls; brake = None; failure = None
```

If AEA-02 as merged differs from any line above (a missing name, value or field), stop and report it (step 0); never
define or patch a domain type here.

### 4b. What this ticket exports (exact; consumers AEA-29, 30, 31, 36, 39, 24 rely on these names)

`src/meridian/policy/handoff.py`:

```python
__all__ = ["CLOSE_OF_BUSINESS", "D4_ROWS", "DUE_SOON_WINDOW", "HOLIDAYS_CLOSED", "PHONE_HOURS", "PROMISE_TABLE",
           "SHORT_DAYS", "STAFF_GUIDANCE_FOR", "UNOWNED_AFTER", "D4CaseRule", "D4Row", "PolicyRow", "business_due",
           "case_due_at", "due_label", "is_business_day", "phone_support_open", "priority_for", "promise_for"]

HOLIDAYS_CLOSED: Final[frozenset[date]] = frozenset({date(2026, 5, 25), date(2026, 7, 4), date(2026, 9, 7),
    date(2026, 11, 26), date(2026, 11, 27), date(2026, 12, 25), date(2027, 1, 1)})   # KB policies/holiday_hours_2026.png (CAS-9)
SHORT_DAYS: Final[Mapping[date, time]] = MappingProxyType({date(2026, 12, 24): time(12, 0)})   # same image, "Christmas Eve 7am - 12pm"
CLOSE_OF_BUSINESS: Final = time(19, 0)                                                 # FAQ phone support Mon–Fri 7:00am–7:00pm
PHONE_HOURS: Final[Mapping[int, tuple[time, time]]] = MappingProxyType({
    0: (time(7, 0), time(19, 0)), 1: (time(7, 0), time(19, 0)), 2: (time(7, 0), time(19, 0)),
    3: (time(7, 0), time(19, 0)), 4: (time(7, 0), time(19, 0)), 5: (time(8, 0), time(16, 0))})   # weekday(); 6 (Sunday) absent = closed

def is_business_day(d: date) -> bool: ...
def business_due(now: datetime, days: int) -> datetime: ...
def phone_support_open(now: datetime) -> bool: ...
def due_label(dt: datetime) -> str: ...

PolicyRow = Literal["R26.unstaffed", "R26.refund", "R26.staffed", "R26.safety_none", "OD4.danger_review"]
PROMISE_TABLE: Final[Mapping[PolicyRow, str]]          # values are TEXTS[...] (step 2), never typed here

def promise_for(reason: HandoffReason, presence: Presence, now: datetime,
                window_start: datetime | None = None) -> Promise: ...
def case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None: ...
def priority_for(reason: HandoffReason, *, promise_due: datetime | None = None,
                 renewal_date: date | None = None) -> Priority: ...

DUE_SOON_WINDOW: Final = timedelta(hours=4)        # [A] CAS-20; replaced by the Stage 9 staff walkthrough
UNOWNED_AFTER: Final = timedelta(minutes=30)       # [A] CAS-20; same measurement; both on the demo clock

STAFF_GUIDANCE_FOR: Final[Mapping[HandoffReason, tuple[str, ...]]]     # step 5, exactly five keys
D4CaseRule = Literal["none", "p4_if_accepted", "p4", "p2", "p3"]
@dataclass(frozen=True, slots=True)
class D4Row:
    request: str            # the table's bold request label
    evidence: str           # the parenthesis after it (inventory codes)
    case_rule: D4CaseRule   # the Case column's leading rule
    note: str | None        # the rest of the Case column, `**` removed; None when nothing follows
D4_ROWS: Final[tuple[D4Row, ...]]                     # step 5, 15 rows in table order
```

`src/meridian/policy/escalation.py`:

```python
__all__ = ["OFFER_AFTER", "R24_REASONS", "decide_escalation"]
OFFER_AFTER: Final = 2                              # [A: threshold 2, OD-6] rule 7; graph-core §8 keeps it here
R24_REASONS: Final[frozenset[HandoffReason]] = frozenset({HandoffReason.REFUND, HandoffReason.BILLING_DISPUTE,
    HandoffReason.COMPLAINT_OR_MANAGER, HandoffReason.LEGAL_OR_CHARGEBACK, HandoffReason.COMMERCIAL})
def decide_escalation(inputs: EscalationInputs) -> EscalationDecision: ...
```

No other public name. Private helpers start with `_`. Sizes: both files are well under the 300-line utility cap
(`code-structure.md`); `handoff.py` ≈ 220 lines, `escalation.py` ≈ 90.

---

## 5. Steps

Build order inside the module boundary DO-3 gives (pure core: `policy/` imports `domain/` and `policy/texts` only;
`policy/escalation.py` imports `policy/handoff.py`, never the reverse). No new interface, seam or abstraction: this slice
implements DO-4 §6–§7's functions as written and consumes AEA-02's types and AEA-03's texts.

**Do not:** define or alter any domain type; type a customer sentence in either module; read a clock
(`datetime.now`, `date.today`, `time.time`, `time.monotonic`); open a file in `src/`; use `assert` in `src/` (ruff `S101`);
use `strftime` for labels (locale-dependent); import from `meridian.services`, `meridian.agent`, `meridian.adapters`,
`meridian.ports`, `meridian.web`; edit any file outside §2's owned list; add a `conftest.py`; mark any test `live` or
`journey`; run the full suite; `git add -A`; push.

### Step 0 — preconditions (stop if any fails)

1. `cd` into the AEA-14 worktree. `export UV_LINK_MODE=hardlink`. `uv sync` (never copy a venv; no `node_modules`).
2. `git log --oneline -20` must show AEA-02 merged (and AEA-01, AEA-03, already on `main` at `16ca639`).
   `ls src/meridian/domain/handoff.py src/meridian/domain/turn.py src/meridian/domain/specialists.py
   src/meridian/domain/state.py src/meridian/domain/common.py src/meridian/policy/texts.py` must succeed. If not: stop,
   report `BLOCKED-ON AEA-02`.
3. Prove every imported name and the fields this plan relies on exist, in one command (it must print `ok`):
   ```bash
   uv run python -c "
   from meridian.domain.handoff import HandoffReason, Priority, Presence, Promise
   from meridian.domain.turn import EscalationInputs, EscalationDecision, GateDecision, GateKind, RuleMatches, Plan, PlannedTask, TaskIntent
   from meridian.domain.specialists import AccountResult, SchedulingResult, KnowledgeResult, MembershipView, ChangeRequestDraft
   from meridian.domain.state import IdentityState, FailureCounters
   from meridian.domain.common import Halt, HaltReason
   from meridian.policy.texts import TEXTS, TextId, render
   assert HandoffReason('burning_ruled_out') and len(HandoffReason) == 16
   assert 'planner_failed' in Plan.model_fields and 'now' in EscalationInputs.model_fields
   assert 'policy_trigger' in RuleMatches.model_fields and 'renewal_date' in MembershipView.model_fields
   assert 'presence' not in EscalationInputs.model_fields
   assert set(Promise.model_fields) == {'policy_row','text','due_at','due_label','extra_lines','live_queued'}
   print('ok')"
   ```
   If any import or assertion fails: stop and report `BLOCKED-ON AEA-02` with the failing line (a missing name or field
   is a small follow-up on AEA-02, never a definition here).
4. Read the merged class bodies of `GateDecision`, `RuleMatches`, `Plan`, `PlannedTask`, `IdentityState`,
   `FailureCounters`, `AccountResult`, `SchedulingResult`, `KnowledgeResult`, `ChangeRequestDraft`, `Halt` so the test
   builders (§6) pass every required field. If AEA-02 added a required field not in §4a, fill it with a neutral value in
   the builder only.

### Step 1 — business days and labels (`policy/handoff.py`)

Module docstring: one paragraph: "Promise, due time and priority rules for a handoff (A6). Pure: no I/O, no clock read
(`now` is always an argument), no model. Every customer sentence comes from `policy/texts.py`." Imports:
`from __future__ import annotations`, `dataclasses.dataclass`, `datetime` (`date`, `datetime`, `time`, `timedelta`),
`collections.abc.Mapping`, `types.MappingProxyType`, `typing` (`Final`, `Literal`), `zoneinfo.ZoneInfo`, then the domain
and texts imports of §4a. Private `_CHICAGO: Final = ZoneInfo("America/Chicago")`.

Write the constants of §4b exactly, then:

1. `_local(dt: datetime, name: str) -> datetime`: if `dt.tzinfo is None or dt.utcoffset() is None` raise
   `ValueError(f"{name} must be timezone-aware")` (a name, never the value); return `dt.astimezone(_CHICAGO)`.
   *Protects:* every due and label is Chicago time (M-13; never a server wall clock).
2. `is_business_day(d)`: `d.weekday() < 5 and d not in HOLIDAYS_CLOSED`. *Protects:* Saturday is never a business day
   (CAS-9); `SHORT_DAYS` days **are** business days.
3. `_close_on(d: date) -> time`: `SHORT_DAYS.get(d, CLOSE_OF_BUSINESS)`.
4. `business_due(now, days)`:
   1. if `days < 1`: `ValueError("days must be at least 1")`;
   2. `d = _local(now, "now").date()` (the time of day is ignored from here on);
   3. `count = 0`; loop: `d += timedelta(days=1)`; if `is_business_day(d)`: `count += 1`; stop when `count == days`
      (strictly **after** now's calendar date);
   4. return `datetime.combine(d, _close_on(d), tzinfo=_CHICAGO)`.
   *Protects:* Fri 10:00 and Fri 20:00 give the same Monday; weekends and closed holidays are skipped; 2026-12-24's due
   is 12:00 (its close).
5. `_phone_hours_on(d: date) -> tuple[time, time] | None`: `None` if `d in HOLIDAYS_CLOSED`; `hours =
   PHONE_HOURS.get(d.weekday())`, `None` if absent; if `d in SHORT_DAYS`: `(hours[0], min(hours[1], SHORT_DAYS[d]))`;
   else `hours`.
6. `phone_support_open(now)`: `local = _local(now, "now")`; `hours = _phone_hours_on(local.date())`; `False` if None;
   `hours[0] <= local.time() < hours[1]` (the closing minute is closed).
7. `_clock_text(t: time) -> str`: `hour12 = t.hour % 12 or 12`; `f"{hour12}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}"`
   ("8:00 am", "12:00 pm", "4:00 pm", "7:00 pm").
8. `due_label(dt)`: `local = _local(dt, "dt")`; English names from two private tuples (`_WEEKDAYS = ("Monday", …,
   "Sunday")`, `_MONTHS = ("January", …, "December")`), **not** `strftime`:
   `f"{_WEEKDAYS[local.weekday()]}, {_MONTHS[local.month - 1]} {local.day}, {_clock_text(local.time())}"` →
   "Monday, October 19, 7:00 pm".

Then write the step-1 tests (§7: AC-1, AC-2 and the plan-added `short_day`, `naive`, `due_label` tests) and run them
(§7 command A).

### Step 2 — the promise table

```python
_ROW_TEXT: Final[Mapping[PolicyRow, TextId]] = MappingProxyType({
    "R26.unstaffed": TextId.PROMISE_UNSTAFFED, "R26.refund": TextId.PROMISE_REFUND,
    "R26.staffed": TextId.PROMISE_STAFFED, "R26.safety_none": TextId.PROMISE_SAFETY_NONE,
    "OD4.danger_review": TextId.PROMISE_DANGER_REVIEW})
PROMISE_TABLE: Final[Mapping[PolicyRow, str]] = MappingProxyType({row: TEXTS[tid] for row, tid in _ROW_TEXT.items()})
```

Values are the **raw** `TEXTS` strings (the unstaffed one keeps `{due_label}` and `{case_ref}`): AC-9 compares them
character for character, M-10 compares stored `promise.text` with them, and the reference does not exist yet when the
promise is made (AEA-29 mints it). Never type a sentence in this file.

### Step 3 — `promise_for`, `case_due_at`, the window text

1. `_ISSUED_WINDOW_END: Final[Mapping[time, time]] = MappingProxyType({time(8, 0): time(12, 0), time(12, 0): time(16, 0),
   time(13, 0): time(17, 0), time(16, 0): time(19, 0)})` with the comment `# [Source: scheduling_db/SCHEMA.md "window"
   08:00-12:00, 12:00-16:00, 13:00-17:00, 16:00-19:00; starts are unique, so the start names the window]`.
2. `_window_text(window_start: datetime) -> str`: `start = _local(window_start, "window_start").time()`; `end =
   _ISSUED_WINDOW_END.get(start)`; if `end is None`: `ValueError("window_start is not the start of an issued window")`;
   return `f"{_clock_text(start)} – {_clock_text(end)}"` (U+2013 en dash with a space each side: "12:00 pm – 4:00 pm";
   ruff `RUF001` is ignored in `pyproject.toml`, so the literal is fine).
   *Protects:* the customer is never told a window that is not the one in the data.
3. `_make(row: PolicyRow, due_at: datetime | None, extra: tuple[str, ...] = (), live: bool = False) -> Promise`: the
   **only** `Promise(` call in `src/`: `Promise(policy_row=row, text=PROMISE_TABLE[row], due_at=due_at,
   due_label=None if due_at is None else due_label(due_at), extra_lines=extra, live_queued=live)`.
   *Protects:* GRC-2 (one constructor; `text` always a table value).
4. `promise_for(reason, presence, now, window_start=None)`, first match:
   1. `local_now = _local(now, "now")` (validates `now` even on paths that compute no due);
   2. `reason is HandoffReason.SAFETY` → `_make("R26.safety_none", None)` (R-6: no time promised; staffed or not);
   3. `presence == "simulated_on_shift"` → `_make("R26.staffed", None, _fee_lines(reason, local_now, None,
      window_start), live=True)` (`_fee_lines` is step 3.5; it returns `()` unless the reason is `FEE_BEARING_CHANGE`);
   4. `reason in {HandoffReason.DANGER, HandoffReason.BURNING_UNCLEAR}` → `_make("OD4.danger_review", business_due(now,
      1))` (CAS-11; no second `R26.unstaffed` promise);
   5. `reason is HandoffReason.REFUND` → `_make("R26.refund", business_due(now, 2),
      (render(TextId.PROMISE_REFUND_NO_OUTCOME),))`;
   6. else → `due = business_due(now, 1)`; `_make("R26.unstaffed", due, _fee_lines(reason, local_now, due,
      window_start))`. `BURNING_RULED_OUT` lands here (CAS-16 A) with no extra lines.
5. `_fee_lines(reason: HandoffReason, local_now: datetime, due: datetime | None, window_start: datetime | None) ->
   tuple[str, ...]`: `()` unless `reason is HandoffReason.FEE_BEARING_CHANGE`. Otherwise build, in this order:
   1. the can't-guarantee line `render(TextId.FEE_CANT_GUARANTEE, window=_window_text(window_start))` **only when**
      `window_start is not None and due is not None and window_start < due` (staffed: `due` is `None` → no line);
   2. the phone line `render(TextId.FEE_PHONE_SUPPORT_OPEN)` **only when** `phone_support_open(local_now)` **and**
      `_phone_hours_on(local_now.date())` is not `None` and its `[1] == CLOSE_OF_BUSINESS` (the sentence says "until
      7:00 pm today"; a Saturday or a short day would make it false).
   *Protects:* SCREEN_SPECS lines 115/153 and US-14 ("nothing says a message was sent"); `Promise.due_at` is always the
   customer promise and never the window start (CAS-10).
6. `case_due_at(reason, promise, window_start)`: if `reason in {HandoffReason.FEE_BEARING_CHANGE,
   HandoffReason.BURNING_RULED_OUT}` and `window_start is not None` → `window_start`; else `promise.due_at`. (Contract
   body for fee-bearing; CAS-16 A adds the burning row; with no window both fall back to the promise due, so a case never
   loses its due.)

Write the step-3 tests and run them.

### Step 4 — `priority_for` and the thresholds

```python
_PRIORITY: Final[Mapping[HandoffReason, Priority]] = MappingProxyType({
    HandoffReason.SAFETY: Priority.P0,
    HandoffReason.DANGER: Priority.P1, HandoffReason.BURNING_UNCLEAR: Priority.P1,
    HandoffReason.FEE_BEARING_CHANGE: Priority.P2, HandoffReason.LATE_TECHNICIAN: Priority.P2,
    HandoffReason.BURNING_RULED_OUT: Priority.P2,                     # CAS-16 option A (D-14)
    HandoffReason.UNSUPPORTED_ACTION: Priority.P4,                    # CAS-12
    HandoffReason.CUSTOMER_REQUESTED_PERSON: Priority.P3, HandoffReason.REFUND: Priority.P3,
    HandoffReason.BILLING_DISPUTE: Priority.P3, HandoffReason.COMPLAINT_OR_MANAGER: Priority.P3,
    HandoffReason.LEGAL_OR_CHARGEBACK: Priority.P3, HandoffReason.COMMERCIAL: Priority.P3,
    HandoffReason.IDENTITY_UNVERIFIED: Priority.P3, HandoffReason.AI_FAILURE: Priority.P3})
```

`priority_for(reason, *, promise_due=None, renewal_date=None)`:
1. `reason is HandoffReason.MEMBERSHIP_CANCEL` → `Priority.P2` if `renewal_date is not None and promise_due is not None
   and renewal_date <= _local(promise_due, "promise_due").date()`, else `Priority.P3` (CAS-14).
2. else `_PRIORITY[reason]`; a reason missing from the table raises `ValueError(f"no priority for reason
   {reason.value}")` (an enum code, not customer data). The test proves every member is covered.

Then the two `Final` thresholds of §4b. Write the AC-10 test and the thresholds test, and run.

### Step 5 — staff guidance and D4 rows

```python
STAFF_GUIDANCE_FOR: Final[Mapping[HandoffReason, tuple[str, ...]]] = MappingProxyType({
    HandoffReason.FEE_BEARING_CHANGE: ("Waive the $49 late-cancellation fee once per customer per year",),
    HandoffReason.LATE_TECHNICIAN: ("Waive the diagnostic fee when the technician arrived more than 30 minutes",),
    HandoffReason.BILLING_DISPUTE: ("Extend a 10% courtesy discount on a repair invoice under $500",),
    HandoffReason.COMPLAINT_OR_MANAGER: ("Extend a 10% courtesy discount on a repair invoice under $500",),
    HandoffReason.REFUND: ("Issue refunds of any kind.",),
})   # [Source: KB internal/agent_discretion_notes.md; cases §5, CAS-33]. Staff guidance only; never customer text.
```

`D4_ROWS` (copy exactly; Unicode `§` and `→` and the backticks are part of the strings; re-verified by parsing §9.4 on
`16ca639`):

```python
D4_ROWS: Final[tuple[D4Row, ...]] = (   # [Source: consolidated direction §9.4 table, in order]
    D4Row("Pay an invoice", "BILL-PAY 14; §5.2", "p4", "due date in the brief; P2 if the invoice is past due"),
    D4Row("Set up autopay", "BILL-AUTOPAY 14", "p4_if_accepted", None),
    D4Row("Turn off auto-renew", "MEM-CANCEL 13", "p2", "if renewal falls within the follow-up window, else P3"),
    D4Row("Upgrade to Plus", "MEM-UPGRADE 6", "p4", "the AI does not change `membership_tier` without payment"),
    D4Row("Duplicate charge", "BILL-DUP 11", "none", "at first; P3 if both posted; a dispute → supervisor (P3)"),
    D4Row("Registration check", "WAR-REGISTER 10; WAR-PARTS 7", "p4_if_accepted", None),
    D4Row("Repeat repair under warranty", "WAR-REPEAT 6", "p4",
          "for staff to check history; the AI does not set `is_warranty_visit` on a claim"),
    D4Row("Install-warranty term", "WAR-CLAIM 14", "none", "unless a booking or a confirmation is wanted"),
    D4Row("Itemized copy by email", "BILL-EXPLAIN 13", "p4_if_accepted", None),
    D4Row("Late technician", "SCH-LATE 9", "p2", None),
    D4Row("Waitlist / earlier slot", "34 booking calls", "none", "unless urgent (P1) or the customer asks for a person"),
    D4Row("Quote vs invoice", "BILL-DISPUTE 16", "p3", None),
    D4Row("Refund", "BILL-REFUND 8", "p3", None),
    D4Row("Commercial quote", "COMMERCIAL 5", "p3", "routed to commercial"),
    D4Row("Job inquiry", "HIRING 6", "none", None),
)
```

Write the AC-11, AC-9 and AC-15 tests and run `test_handoff.py` whole.

### Step 6 — `policy/escalation.py`

Docstring: "Decide whether a turn becomes a handoff, an offer of a person, or neither (A7b; DO-4 §6 with cases §3.4).
Pure: first match wins; priority always from `policy/handoff.priority_for`." Imports: `from __future__ import
annotations`, `typing.Final`, `from meridian.domain.handoff import HandoffReason, Priority`, `from meridian.domain.turn
import EscalationDecision, EscalationInputs, GateKind`, `from meridian.domain.specialists import AccountResult,
SchedulingResult`, and `from meridian.policy.handoff import business_due, priority_for`.

Private `_escalate(reason: HandoffReason, rule_id: str, priority: Priority | None = None, degraded: bool = False) ->
EscalationDecision` returning `EscalationDecision(outcome="escalate", reason=reason, priority=priority if priority is
not None else priority_for(reason), rule_id=rule_id, degraded=degraded)`, and `_offer(rule_id: str) ->
EscalationDecision` returning `EscalationDecision(outcome="offer", reason=None, priority=None, rule_id=rule_id)`.

`decide_escalation(inputs)`, in this exact order; return at the first rule that matches:

1. **Rule 1** `inputs.gate.kind == GateKind.PERSON` → `_escalate(HandoffReason.CUSTOMER_REQUESTED_PERSON, "R2.person")`
   (P3, R-2).
2. **Rule 2** `trigger = inputs.gate.rules.policy_trigger`; if `trigger in R24_REASONS` → `_escalate(trigger,
   f"R24.{trigger.value}")`. Else if `inputs.plan is not None and inputs.plan.handoff_request in R24_REASONS` → the same
   with the plan's reason. (All five are P3.)
3. **Rule 3** any `r` in `inputs.results` with `isinstance(r, SchedulingResult) and r.status == "staff_change_request"`
   → `_escalate(HandoffReason.FEE_BEARING_CHANGE, "R21.fee_bearing")` (P2, R-21/R-22).
4. **Rule 4** `inputs.plan is not None and inputs.plan.handoff_request is not None` (and not in `R24_REASONS`, already
   handled), with `reason = inputs.plan.handoff_request`:
   - `MEMBERSHIP_CANCEL` → `renewal = _renewal_date(inputs.results)` (the first `AccountResult` whose `membership is
     not None` → `membership.renewal_date`, else `None`); `_escalate(reason, "D4.membership_cancel",
     priority=priority_for(reason, promise_due=business_due(inputs.now, 1), renewal_date=renewal))`. No presence is
     read (R-G-15).
   - `UNSUPPORTED_ACTION` → `_escalate(reason, "D4.unsupported")` (P4).
   - `LATE_TECHNICIAN` → `_escalate(reason, "D4.late_technician")` (P2).
   - `BURNING_RULED_OUT` → `_escalate(reason, "R7.burning_ruled_out")` (P2).
   - any other value → `_escalate(reason, f"PLAN.{reason.value}")`.
5. **Rule 5** `inputs.identity.status in ("not_verified", "locked")` and `_private_task_open(inputs)` →
   `_escalate(HandoffReason.IDENTITY_UNVERIFIED, "R16.identity_unverified")` (P3, R-16). `_private_task_open`: `True`
   if `inputs.plan is not None and any(t.needs_identity for t in inputs.plan.tasks)`, or any result that is an
   `AccountResult` or `SchedulingResult` with `status == "not_verified"`.
6. **Rule 6** (degraded; `reason=AI_FAILURE`, P3, `degraded=True`), the id by the first true test in this order:
   `inputs.halt is not None` → `"AI.halt"`; any result with `r.status == "failed"` → `"AI.specialist_failed"`;
   `inputs.models_disabled` → `"AI.models_disabled"`; `inputs.plan is not None and inputs.plan.planner_failed and not
   inputs.plan.tasks` → `"AI.planner_failed"`.
7. **Rule 7** `c = inputs.counters`: `c.failed_answers >= OFFER_AFTER or c.corrections >= OFFER_AFTER` →
   `_offer("OD6.two_misses")`; else `c.timeouts >= OFFER_AFTER` → `_offer("OD6.two_timeouts")`.
8. **Rule 8** → `EscalationDecision(outcome="none", reason=None, priority=None, rule_id="none")`.

*Invariants:* first match wins (a scheduling change request with two misses is rule 3, not 7); no model text, clock
read or I/O; `priority` on every `escalate` equals `priority_for(reason, …)`; `degraded` is `True` only on rule 6.

Write `test_escalation.py` and run both test files.

### Step 7 — fast gates and affected checks (§7 commands B–D)

### Step 8 — commit 1 (code and tests)

`git add src/meridian/policy/handoff.py src/meridian/policy/escalation.py tests/unit/policy/test_handoff.py
tests/unit/policy/test_escalation.py` (explicit paths, never `-A`). Message:

```
feat(policy): promises, priorities and the escalation decision (AEA-14)

policy/handoff.py: business days and due times (CAS-9), the R-26 promise table from policy/texts.py,
promise_for / case_due_at (CAS-10, CAS-11), priority_for (CAS-12..14, CAS-16 A), thresholds (CAS-20),
STAFF_GUIDANCE_FOR (CAS-33), D4_ROWS. policy/escalation.py: decide_escalation, rules 1-8 (cases 3.4,
R-G-14, R-G-15). Pure; unit tests only (wave 1, no journey harness yet).

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

### Step 9 — journey record and context rows; commit 2

1. Create `docs/testing/journeys/<YYYY-MM-DD>-AEA-14.md` (same shape as `2026-10-21-AEA-03.md` on `main`):

   ```markdown
   # Journey record: AEA-14 promises, priorities and the escalation decision

   | Field | Value |
   |---|---|
   | Claim | AEA-14 AC-18: `policy/handoff.py` and `policy/escalation.py` are pure policy; their evidence is unit tests. J-4 (fee-bearing change: P2 case, honest promise), J-5 (safety and danger: P0/P1 cases, no time promised, the OD4 review line) and J-6 (escalation → case → staff queue with the promise) will exercise this code once AEA-51 and AEA-52 land |
   | Level | `mock-tested` |
   | Tested revision | `<commit-1 SHA>` |
   | Environment | VPS, `uv run`, Python 3.12; no server, no database, no model |
   | Command | `uv run pytest tests/unit/policy/test_handoff.py tests/unit/policy/test_escalation.py -v`; `uv run python -m tests.journeys.affected --base main --list-only` |
   | Result | <N> passed. Affected: `changed files: <k> (base main)` then `0 journeys affected` |
   | Evidence location | this record |
   | Remaining limitations | No journey exists yet; nothing integrated is claimed; the real entry point's CAP-3 check is AEA-51 |
   | Blocked by | AEA-57 (journey harness); then AEA-51 (J-4, J-5) and AEA-52 (J-6) |
   ```
   Fill `<…>` from the actual runs; quote the exact output lines.
2. `.claude/reference/area-map.md`: the *Status* cell is the **last** column (a *Tickets* column precedes it since
   AEA-08). Change two cells only; leave every other cell and row as found:
   - A6 row (`**A6 Cases and handoff**`): `planned` → ``planned; `policy/handoff.py` actual (AEA-14, `<sha>`)``.
   - A7b row (`**A7b Act**`): `planned` → ``planned; `policy/escalation.py` actual (AEA-14, `<sha>`; built in wave 1,
     slice plan §2)``.
   If a cell already holds another ticket's "actual" note, append yours after a `; `.
3. `docs/design/code-design.md`: the line `**Built:** …` directly under §3's first paragraph (on `16ca639`:
   ``**Built:** `policy/texts.py` (AEA-03, `2689582`).``): append `` · `policy/handoff.py`, `policy/escalation.py`
   (AEA-14, `<sha>`)`` before the final period. If the line does not exist, add ``**Built:** `policy/handoff.py`,
   `policy/escalation.py` (AEA-14, `<sha>`).`` after a blank line below "Owner area and wave in the right-hand columns
   (§8). Sizes follow `code-structure.md`."
4. `.claude/state/icm-progress.md`: on `16ca639` there are **two** rows named *Routes verified against code and tests*
   (lines 17–18, a merge artefact). Edit **only** the row whose last cell reads "Each slice adds its route; verified when
   every area-map row is actual" (the AEA-03-pattern row, line 18 today); if only one such-named row exists when you
   get there, edit that one. Keep status `provisional`; replace its evidence cell with `2026-10-21: area map A6 →
   `policy/handoff.py` and A7b → `policy/escalation.py` checked against `tests/unit/policy/test_handoff.py` and
   `test_escalation.py` (AEA-14, `<sha>`; <N> pass)` (keep the row ≤ 400 characters). Do not delete or merge the other
   row (not yours; reported in §8 R-6).
5. `git add` those four paths explicitly; commit `docs(context): AEA-14 policy built; journey record mock-tested` with
   the `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` line last. Do not push.

### Step 10 — report

Report: both SHAs; the command lines and their last output lines from §7 B–D; the test count; each AC with its test
and result; the plan-added behaviours (short-day due, Saturday phone line omitted, window end from issued windows,
fee-bearing `case_due_at` fallback, `model_validate` allowed by the GRC-2 scan) stated plainly.

---

## 6. Data and fixtures

All synthetic or issued, no personal data, no phone numbers, codes or card-like numbers. No fixture files: builders
live in the test modules.

- **Clocks** (in both test files): `CHI = ZoneInfo("America/Chicago")`; `def at(y, mo, d, h=10, mi=0) -> datetime:
  return datetime(y, mo, d, h, mi, tzinfo=CHI)`. `FRI_10 = at(2026, 10, 16)` (= `WORKED_PAIRS_NOW`, data.md §8a;
  worked-pairs header). Do not import `tests/fakes/clock.py` (AEA-11, may not be merged; not needed for pure functions).
- **Expected strings** are read from `meridian.policy.texts.TEXTS` / `render(...)` (never retyped), except the
  worked-pair literals the ticket fixes, which the tests also assert literally: "A representative will get to your
  refund request within 2 business days.", "I can't promise an outcome.", the WP-4 can't-guarantee sentence ending
  "arriving 12:00 pm – 4:00 pm." and "Phone support is open until 7:00 pm today if you'd like to call.".
- **Typing in tests** (mypy strict with `init_typed = true`; tests may be untyped): leave builder parameters that feed a
  `Literal` field (`status`, `kind`) **unannotated** (they become `Any`), or annotate them with the exact `Literal`.
  Never annotate them `str`. Pass enum members (`GateKind.FREE_TEXT`, `TaskIntent.READ_INVOICE`), never their strings.
- **Escalation builders** in `test_escalation.py` (fill any extra required field AEA-02 added with a neutral value):
  - `_rules(**kw) -> RuleMatches`: `RuleMatches(safety=None, burning_unclear=False, danger_words=False, person=False,
    policy_trigger=None, rule_ids=(), correction=False)`, overridden by `kw` (build the dict, then
    `RuleMatches.model_validate({...})` if mypy objects to `**kw`).
  - `_gate(kind=GateKind.FREE_TEXT, **rule_kw) -> GateDecision(kind=kind, rules=_rules(**rule_kw))`.
  - `_plan(handoff=None, tasks=(), planner_failed=False) -> Plan(mode="act", tasks=tasks, handoff_request=handoff,
    topic="other", source="planner", planner_failed=planner_failed)`.
  - `_task(needs_identity=True) -> PlannedTask(order=1, specialist="account", intent=TaskIntent.READ_INVOICE,
    needs_identity=needs_identity)`.
  - `_identity(status="verified") -> IdentityState(status=status, customer_id=None, masked_hint=None,
    code_expires_at=None, tries_left=3, codes_sent=0, verified_at=None)`.
  - `_account(renewal, status="read") -> AccountResult(status=status, membership=None if renewal is None else
    MembershipView(tier="standard", renewal_date=renewal), tools=(), calls=())`.
  - `_scheduling(status) -> SchedulingResult(status=status, change_request=<draft if status == "staff_change_request"
    else None>, tools=(), calls=())` with the draft `ChangeRequestDraft(appointment_id=1, change="move",
    wanted_text="Monday morning instead", windows_shown=(), hours_before=2.0, window_start=at(2026, 10, 16, 12))`.
  - `_knowledge(status="failed") -> KnowledgeResult(status=status, passages=(), points=(), tools=(), calls=())`.
  - `_halt() -> Halt(reason=HaltReason.BRAKE_TASKS, node="act", elapsed_ms=1200)`.
  - `_inputs(**kw) -> EscalationInputs`: defaults `gate=_gate(), plan=None, results=(), counters=FailureCounters(),
    identity=_identity(), halt=None, models_disabled=False, now=FRI_10`, overridden by `kw`.
- **Read-only files the tests open** (paths from `ROOT = Path(__file__).resolve().parents[3]`):
  `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md` (AC-11),
  `docs/data/issued/meridian_dataset/knowledge_base/internal/agent_discretion_notes.md` (AC-11),
  `src/meridian/**/*.py` (AC-15, AC-16). Open with `encoding="utf-8"`; never write.

---

## 7. Checks

### Tests the implementer writes with the code (all must pass)

`tests/unit/policy/test_handoff.py` (20):

| Test | Asserts |
|---|---|
| `test_business_due_after_hours` | AC-1 rows listed in §3a; each result `== at(...)` with hour 19 and `.utcoffset() == timedelta(hours=-5)` for October |
| `test_business_due_weekend` | AC-1 weekend rows and the three `is_business_day` values |
| `test_business_due_thanksgiving` | Wed 11-25 +1 → `datetime(2026, 11, 30, 19, 0, tzinfo=CHI)`, offset −6 h; 11-26 and 11-27 not business days |
| `test_phone_support_hours` | AC-2's six values in order |
| `test_unstaffed_promise_and_due` | for every reason except SAFETY, DANGER, BURNING_UNCLEAR, REFUND, FEE_BEARING_CHANGE: `promise_for(r, "nobody_online", FRI_10)` has `policy_row == "R26.unstaffed"`, `text == PROMISE_TABLE["R26.unstaffed"]`, `due_at == at(2026,10,19,19)`, `due_at.isoformat() == "2026-10-19T19:00:00-05:00"`, `due_label == "Monday, October 19, 7:00 pm"`, `extra_lines == ()`, `live_queued is False` |
| `test_wp7_refund_promise` | WP-7 output in §1 exactly; `due_label == "Tuesday, October 20, 7:00 pm"`; `priority_for(HandoffReason.REFUND) is Priority.P3` |
| `test_staffed_promise` | refund and danger, `"simulated_on_shift"`: row `R26.staffed`, `text == TEXTS[TextId.PROMISE_STAFFED]` (starts "A representative will join this chat when available"), `due_at is None`, `due_label is None`, `live_queued is True`, `extra_lines == ()` |
| `test_safety_promises_no_time` | both presences: `R26.safety_none`, `text == ""`, `due_at is None`, `due_label is None`, `live_queued is False`; `priority_for(SAFETY) is Priority.P0` |
| `test_p1_danger_review_line` | DANGER and BURNING_UNCLEAR, `"nobody_online"`, FRI_10: row `OD4.danger_review`, `text == TEXTS[TextId.PROMISE_DANGER_REVIEW]`, `due_at == at(2026,10,19,19)`, `extra_lines == ()`, and `PROMISE_TABLE["R26.unstaffed"] not in (p.text, *p.extra_lines)` |
| `test_wp4_fee_bearing_lines_and_case_due` | (a) FRI_10, window `at(2026,10,16,12)`: row `R26.unstaffed`, due Mon 19:00, `extra_lines == (CANT_12, PHONE)` where `CANT_12` is the full WP-4 sentence and `PHONE` the phone sentence; `p.due_at != window`; `case_due_at(FEE_BEARING_CHANGE, p, window) == window`; (b) Sun `at(2026,10,18)`, window `at(2026,10,19,12)`: `extra_lines == (CANT_12,)`; (c) FRI_10, window `at(2026,10,20,8)` (after the due): `extra_lines == (PHONE,)`; (d) every other reason except BURNING_RULED_OUT, window `at(2026,10,16,12)`: `case_due_at(r, promise_for(r, "nobody_online", FRI_10, window), window) == promise.due_at`; (e) **CAS-16 A**: BURNING_RULED_OUT, FRI_10, window `at(2026,10,16,12)`: row `R26.unstaffed`, `extra_lines == ()`, `case_due_at == window`; with `window_start=None`, `case_due_at == promise.due_at`; FEE_BEARING_CHANGE with `window_start=None`: `case_due_at == promise.due_at` |
| `test_fee_bearing_phone_line_never_false` (plan-added) | Sat `at(2026,10,17,9)`, window `at(2026,10,19,8)`: `phone_support_open` is True but `extra_lines == (render(TextId.FEE_CANT_GUARANTEE, window="8:00 am – 12:00 pm"),)` (no phone line); Thu `at(2026,12,24,10)`: no phone line; staffed FRI_10 fee-bearing: `extra_lines == (PHONE,)`, `due_at is None` |
| `test_window_text_from_issued_windows` (plan-added) | windows starting 08:00, 12:00, 13:00, 16:00 give "8:00 am – 12:00 pm", "12:00 pm – 4:00 pm", "1:00 pm – 5:00 pm", "4:00 pm – 7:00 pm" inside the can't-guarantee line of `promise_for(FEE_BEARING_CHANGE, "nobody_online", FRI_10, at(2026, 10, 19, h))` (all four are before the Mon 19:00 due); `at(2026, 10, 19, 9)` raises `ValueError` |
| `test_promise_texts_are_the_table` | `set(PROMISE_TABLE) == set(typing.get_args(PolicyRow))`; each value equals its `TEXTS[TextId...]` (map in step 2); over reasons × presences × clocks {FRI_10, Fri 20:00, Sat 09:00, Sun 10:00, Thu 2026-12-24 10:00} × windows {None, `at(2026,10,16,12)`}: every `p.text in PROMISE_TABLE.values()` |
| `test_priority_per_reason` | a dict of expected priority for every member except MEMBERSHIP_CANCEL (values from step 4, incl. `BURNING_RULED_OUT: P2`, `UNSUPPORTED_ACTION: P4`, `LATE_TECHNICIAN: P2`); `set(expected) | {MEMBERSHIP_CANCEL} == set(HandoffReason)`; membership: no args → P3; `promise_due=at(2026,10,19,19)`, renewal `date(2026,11,3)` → P3 (WP-8); renewal `date(2026,10,19)` → P2; renewal `date(2026,10,18)` → P2 |
| `test_d4_rows_and_staff_guidance` | parse §9.4 (algorithm below) → 15 tuples; `[(r.request, r.evidence, r.case_rule, r.note) for r in D4_ROWS] == parsed`; `set(STAFF_GUIDANCE_FOR) == {FEE_BEARING_CHANGE, LATE_TECHNICIAN, BILLING_DISPUTE, COMPLAINT_OR_MANAGER, REFUND}`; every prefix is a substring of the KB notes file text |
| `test_promise_construction_and_no_staff_text` | **Source scan (GRC-2):** AST of every `src/meridian/**/*.py` except `src/meridian/policy/handoff.py`: no `ast.Call` whose `func` is `Name(id="Promise")` or an `Attribute` with `attr == "Promise"` (e.g. `handoff.Promise(...)`), and no `ast.Call` whose `func` is `Attribute(value=Name(id="Promise"), attr="model_construct")`. **`Promise.model_validate(...)` is allowed** (AEA-10 rebuilds stored rows with it; graph-core §10 bans `Promise(`). The test also asserts `src/meridian/policy/handoff.py` itself contains exactly one `Promise(` call (in `_make`). **Text scan:** over the AC-9 grid, no `p.text` or extra line contains any `STAFF_GUIDANCE_FOR` prefix, and none matches `re.compile(r"\b(waive|discount|refunded|sent)\b", re.I)` ("representative" does not match `\bsent\b`) |
| `test_business_due_short_day_and_new_year` (plan-added) | Wed `at(2026,12,23)` +1 → `datetime(2026,12,24,12,0,tzinfo=CHI)`; Thu `at(2026,12,24)` +1 → Mon `datetime(2026,12,28,19,0,tzinfo=CHI)`; Thu `at(2026,12,31)` +1 → Mon `datetime(2027,1,4,19,0,tzinfo=CHI)`; `is_business_day(date(2026,12,24))` True |
| `test_naive_times_and_bad_days_refused` (plan-added) | `business_due(datetime(2026,10,16,10), 1)`, `phone_support_open(naive)`, `due_label(naive)`, `promise_for(REFUND, "nobody_online", naive)` each raise `ValueError` whose message names the argument and contains no digit; `business_due(FRI_10, 0)` raises `ValueError`; a UTC-aware `now` equal to FRI_10 gives the same due as FRI_10 |
| `test_due_label_format` (plan-added) | `at(2026,10,19,19)` → "Monday, October 19, 7:00 pm"; `at(2026,10,20,8)` → "Tuesday, October 20, 8:00 am"; `at(2026,12,24,12)` → "Thursday, December 24, 12:00 pm"; `at(2026,11,2,0,5)` → "Monday, November 2, 12:05 am" |
| `test_thresholds_values` (plan-added) | `DUE_SOON_WINDOW == timedelta(hours=4)`, `UNOWNED_AFTER == timedelta(minutes=30)` |

**D4 parse algorithm** (AC-11 test): `lines = DOC.read_text(encoding="utf-8").splitlines()`; `start =
lines.index("### 9.4 Requests the issued systems cannot complete (D4)")`; `end = lines.index("### 9.5 Follow-up channel
(OD-5)")`; for each `line` in `lines[start:end]` that starts with `"| **"`: `cells = [c.strip() for c in
line.strip().strip("|").split(" | ")]`; `m = re.fullmatch(r"\*\*(.+?)\*\* \((.+)\)", cells[0])` → `request, evidence`;
`case = cells[-1].replace("**", "")`; `token = re.match(r"^(P4 only if (?:the customer accepts|accepted)|None|P[0-4])",
case).group(1)`; `rule = "p4_if_accepted" if token.startswith("P4 only if") else {"None": "none", "P2": "p2", "P3": "p3",
"P4": "p4"}[token]`; `note = case[len(token):].lstrip(" ;,") or None`. Assert 15 rows. (Re-run by the planner on
`16ca639`, 2026-10-21: output equals the `D4_ROWS` literal in step 5.)

`tests/unit/policy/test_escalation.py` (13):

| Test | Asserts (outcome, reason, priority, rule_id[, degraded]) |
|---|---|
| `test_rule_order_first_match` | PERSON gate → (escalate, CUSTOMER_REQUESTED_PERSON, P3, "R2.person"); PERSON + policy word REFUND → still "R2.person"; policy word REFUND → (escalate, REFUND, P3, "R24.refund"); `_scheduling("staff_change_request")` → (escalate, FEE_BEARING_CHANGE, P2, "R21.fee_bearing"); WP-8 plan MEMBERSHIP_CANCEL + `_account(date(2026,11,3))` → (escalate, MEMBERSHIP_CANCEL, P3, "D4.membership_cancel"); plan UNSUPPORTED_ACTION → (escalate, …, P4, "D4.unsupported"); plan LATE_TECHNICIAN → (…, P2, "D4.late_technician"); `FailureCounters(failed_answers=2)` → (offer, None, None, "OD6.two_misses"); `corrections=2` → same; `failed_answers=1` → none; nothing → (none, None, None, "none", degraded False); staff change request + `failed_answers=2` → "R21.fee_bearing"; for every `escalate` result above, `priority == priority_for(reason, …)` with the same arguments; `degraded is False` on all of these |
| `test_rule7_two_timeouts` | `timeouts=2` → (offer, None, None, "OD6.two_timeouts"); `timeouts=2, failed_answers=2` → "OD6.two_misses"; `timeouts=1` → none |
| `test_rule6_single_failed_specialist` | one `_knowledge("failed")` → (escalate, AI_FAILURE, P3, "AI.specialist_failed", True); one `_account(None, status="failed")` → same id |
| `test_rule6_models_disabled` | `models_disabled=True` → (escalate, AI_FAILURE, P3, "AI.models_disabled", True) |
| `test_rule6_halt_and_planner_failed` | `halt=_halt()` → "AI.halt", degraded; `plan=_plan(planner_failed=True)` → "AI.planner_failed", degraded; `plan=_plan(planner_failed=True, tasks=(_task(False),))` → none |
| `test_unverified_private_task_escalates` | statuses `not_verified` and `locked`, `plan=_plan(tasks=(_task(True),))` → (escalate, IDENTITY_UNVERIFIED, P3, "R16.identity_unverified"); `not_verified` with `results=(_account(None, status="not_verified"),)` and no plan → same; `not_verified` with no private task → none |
| `test_membership_cancel_priority_uses_business_due` | FRI_10, plan MEMBERSHIP_CANCEL: renewal 2026-11-03 → P3; renewal 2026-10-19 → P2; no account result → P3; all `rule_id == "D4.membership_cancel"`; `"presence" not in EscalationInputs.model_fields` (the decision cannot depend on staffing, R-G-15; AC-17's "under both presences" holds because no presence input exists) and the P2/P3 results equal `priority_for(MEMBERSHIP_CANCEL, promise_due=business_due(FRI_10, 1), renewal_date=…)` |
| `test_rule2_ids_for_every_policy_reason` (plan-added) | for each reason in `R24_REASONS`: via `policy_trigger` and via `plan.handoff_request` → (escalate, reason, P3, f"R24.{reason.value}"); `R24_REASONS` has exactly the five values |
| `test_rule4_burning_ruled_out_and_unexpected_reason` (plan-added) | plan BURNING_RULED_OUT → (escalate, BURNING_RULED_OUT, P2, "R7.burning_ruled_out"); plan CUSTOMER_REQUESTED_PERSON (never produced today) → (escalate, …, P3, "PLAN.customer_requested_person") |
| `test_rule3_needs_a_scheduling_change_request` (plan-added) | `_scheduling("windows_shown")` → none; `_scheduling("failed")` → rule 6 "AI.specialist_failed" |
| `test_policy_modules_are_pure` | AST of `policy/handoff.py` and `policy/escalation.py`: every import is stdlib (`sys.stdlib_module_names` ∪ `{"__future__"}`) or starts with `meridian.domain` or is `meridian.policy.texts` / `meridian.policy.handoff`; nothing from `meridian.services`, `meridian.agent`, `meridian.adapters`, `meridian.ports`, `meridian.web`; no call to `open`, and no attribute call named `now`, `today`, `utcnow`, `monotonic`, `perf_counter`, or `time.time`; `promise_for(...)` twice and `decide_escalation(_inputs(...))` twice give equal results |
| `test_offer_after_is_two` (plan-added) | `OFFER_AFTER == 2` |
| `test_decision_shape_for_none_and_offer` (plan-added) | none/offer decisions carry `reason is None`, `priority is None`, `degraded is False` |

The ticket's worked pairs are in `test_wp7_refund_promise` (WP-7), `test_wp4_fee_bearing_lines_and_case_due` (WP-4) and
`test_membership_cancel_priority_uses_business_due` (WP-8). The single `[journey]` criterion is AC-18 at level
`mock-tested` (record + affected command; no journey test file).

### Commands (run inside the worktree; `export UV_LINK_MODE=hardlink` first)

**A. While iterating** (affected tests only):
```bash
uv run pytest tests/unit/policy/test_handoff.py tests/unit/policy/test_escalation.py -q
```

**B. Once before commit 1, cheapest first; stop at the first red:**
```bash
F="src/meridian/policy/handoff.py src/meridian/policy/escalation.py tests/unit/policy/test_handoff.py tests/unit/policy/test_escalation.py"
uv run ruff format $F && uv run ruff format --check $F
uv run ruff check $F
uv run mypy $F
grep -rln "meridian.policy.handoff\|meridian.policy.escalation\|policy.handoff\|policy.escalation" tests/ eval/ 2>/dev/null
uv run pytest tests/unit/policy/ -v -rP
```
Pass looks like: format "4 files already formatted"; ruff "All checks passed!"; mypy "Success: no issues found in 4
source files"; the grep lists only the two new test files (if it lists others, add them to the pytest line); pytest
"33 passed" for the two new files plus whatever `tests/unit/policy/` already holds (AEA-01's `test_limits.py`, AEA-03's
`test_texts.py`), 0 failed. `-n` is not needed; if used, at most `-n 2`. (AEA-04's merge failed on `ruff format
--check`: run the formatter before committing.)

**C. Affected journeys** (AEA addition):
```bash
uv run python -m tests.journeys.affected --base main --list-only
```
Pass: output `changed files: <k> (base main)` then `0 journeys affected`. (If a journey exists by the time this runs,
e.g. AEA-57 in wave 2, and the command selects any, run it without `--list-only` and record the result instead.)

**D. Collection sanity** (the suite still collects): `uv run pytest --collect-only -q | tail -3` → no errors.

**Not run:** the full suite (nothing here reaches everything: no `conftest.py`, settings, dependency or cross-package
module change; `build-loop-test-scope.md`). No paid model call anywhere (no test is `live`).

---

## 8. Risks and requests

- **R-1 Window end not in the signature.** The can't-guarantee line must name "12:00 pm – 4:00 pm", but `promise_for`
  (DO-4 §7, unchanged) and `ChangeRequestDraft` carry only `window_start`. The plan reads the end from the four issued
  windows, whose starts are unique (SCHEMA.md line 25; checked against the 528 slot rows on 2026-10-21). A start that is
  not an issued one raises `ValueError` (a programming error upstream, AEA-28), so a wrong window is never shown. If a
  fifth window ever appears in the data, `_ISSUED_WINDOW_END` needs a row. No contract change requested.
- **R-2 Phone line on Saturdays.** The fixed sentence says "until 7:00 pm today", true only on a full weekday. Following
  the ticket literally would tell a Saturday customer (phones close 4:00 pm) something false. The plan omits the line
  then (and on 2026-12-24). AC-8's own cases (Friday: line; Sunday: no line) are unaffected. If Innocent wants a
  Saturday line, it needs a new sentence with a placeholder in `policy/texts.py` (AEA-03 follow-up) and SCREEN_SPECS
  copy (UX session); nothing here blocks on it.
- **R-3 Short-day due.** cases §3.1 says "close of business"; the ticket says "19:00". The plan uses the day's close
  (12:00 on 2026-12-24), which only differs on that one date and keeps the promise inside opening hours. Flag for the
  reviewer; reversible by one line (`_close_on`).
- **R-4 Engineering ids chosen here** (`R7.burning_ruled_out`, `PLAN.<reason>`, and rule 8's `"none"`). They are
  internal `rule_id` strings that AEA-39 passes through and AEA-21's trace records; no contract lists them. If the
  orchestrator prefers other strings, change the constants and the two plan-added tests only.
- **R-5 Stale CAS-16 notes.** graph-nodes §6 ("`priority_for` raises `NotImplementedError` … until answered") and cases
  §3.3's "PENDING Innocent (CAS-16)" predate D-14 (option A). This ticket, AEA-02, AEA-36, AEA-39 and AEA-51 all build A.
  Request to the integrator: refresh those two sentences in a `lane::direct` docs change so later readers don't re-open
  it. Not this ticket's files.
- **R-6 Shared context files.** The area map, `icm-progress.md` and the code-design *Built* line are edited by every
  ticket's `[regression/context]` AC. This ticket touches only two *Status* cells, one ICM row and one line; the merge
  step must take both sides of any conflict in those lines. `icm-progress.md` on `16ca639` carries **two** rows named
  *Routes verified against code and tests* (AEA-04's and AEA-03's, from a merge): step 9 edits only the AEA-03-pattern
  row. Request to the integrator: collapse the duplicate in a `lane::direct` change.
- **R-7 Blocker shapes.** The plan relies on AEA-02 adding `BURNING_RULED_OUT`, `EscalationInputs.now`,
  `Plan.planner_failed`, `RuleMatches.policy_trigger`, `MembershipView.renewal_date`, `Presence` in `domain/handoff.py`
  (re-exported) and `Halt` in `domain/common.py`, all as in AEA-02's plan §4. Step 0.3 checks each in one command; a
  missing one is a small follow-up on AEA-02, never a definition here.
- **R-8 `zoneinfo` data.** `ZoneInfo("America/Chicago")` needs the system tz database (present on the VPS) or the
  `tzdata` package. AEA-11's `FixedClock` has the same need. Request to AEA-50 (Dockerfile): make sure the slim image
  has `tzdata` (apt) or add the `tzdata` wheel; not this ticket's file.
- **R-9 GRC-2 scan vs AEA-10's row rebuild (collision avoided).** AEA-10's plan (same wave, `repos_cases.py`) rebuilds
  stored promises with `Promise.model_validate({...})` and `OpenCase.model_validate(...)`. An AC-15 scan that also
  banned `model_validate` (as this plan's earlier version did) would turn red on whichever of the two merges second.
  The scan now follows graph-core §10's wording: `Promise(...)` and `Promise.model_construct(...)` are banned outside
  `policy/handoff.py`; `model_validate` is allowed because it only re-reads a promise this module made and stored.
  AEA-29's own grep gate (G-6: `grep -n "Promise(" src/meridian/services/*.py`) agrees.
- No shared primitive is requested; no collision with another ticket's owned files.

---

## 9. Readiness

**READY**, **BLOCKED-ON AEA-02** until it reaches `main`:

- **AEA-02** (domain types: `HandoffReason` incl. `burning_ruled_out`, `Priority`, `Promise`, `Presence`,
  `EscalationInputs` with `now`, `EscalationDecision`, `GateDecision`, `GateKind`, `RuleMatches`, `Plan` with
  `planner_failed`, `PlannedTask`, `TaskIntent`, the three results, `MembershipView`, `ChangeRequestDraft`,
  `IdentityState`, `FailureCounters`, `Halt`, `HaltReason`) — imported by both modules and their tests; these are real
  imports, not sibling calls a double could replace (the ticket forbids defining domain types here). Ledger state on
  2026-10-21: `planned` (`risk::security`, frozen tests first; merges after AEA-04, which is on `main`).
- **AEA-03** (`policy/texts.py`) — **on `main`** (`60617f9`); no longer blocking.
- **AEA-01** (scaffold, `pyproject.toml` gates, `tests.journeys.affected`) — **on `main`** (`07924f5`); no longer
  blocking.

No product decision is needed: CAS-16 is decided (D-14, option A), no decision D-4…D-15 is answered differently, and no
signed contract changes. Gates: none (no human, paid or live gate).
