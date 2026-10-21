# 7b decisions: cases evidence sweep

Scope: the `needs-decision` items in AEA-10, 13, 14, 28, 29, 30, 31, 32, 52 and 53 (`docs/plans/tickets/AEA-NN.md`). This file records what the sources say. It makes no decision.

Sources searched: `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md` (consolidated), `docs/data/issued/**`, `docs/data/*.md`, `docs/design/*.md`, `docs/design/contracts/*.md`, `docs/ux/03-structure/*` (incl. `ui-contracts.openapi.yaml`), `docs/prd/*.md`, `docs/analysis/*.md`. Line numbers are as read on 2026-10-21. Quotes are shortened where marked with an ellipsis.

Items: 31 in total. Items with no source at all for the open question: 1 (AEA-14 item 5). Items where a related source exists but the specific gap named in the ticket is not defined anywhere: noted per item as "gap not defined in source".

---

## AEA-10 #1: restore_working_copy scope (reset rewrites five tables vs replaces file)

Item (AEA-10.md:135): "`restore_working_copy()` scope: DO-1 §9 says reset copies the DB from the issued file again; DO-6 *Storage and access* says spend, health, eval and deploy rows survive a reset. Does it rewrite only the five issued tables (and AEA-31 clears our conversation and case tables in its own transaction), or replace the file and re-create the kept tables' rows?"

- `docs/design/code-design.md:334`: "`adapters/sqlite/*` | Store and read rows; one transaction per unit of work. | WAL, `busy_timeout` 5 s [A]; the issued file opened read-only, only by `migrate.restore_working_copy` |"
- `docs/design/code-design.md:676`: "`ResetService` and `SchedulerJob` receive `restore_working_copy`, `clear_checkpoints`, `prune_checkpoints`, `seed_demo` as callables from the container"
- `docs/design/contracts/internal-components.md:982`: "def __init__(self, uow: UnitOfWorkFactory, restore_working_copy: Callable[[], None],"
- Scope of the rewrite (five issued tables vs whole file) is not stated in these lines. Search for "five issued" / "kept tables" in the sources found no further text.

## AEA-10 #2: temp_sqlite() home

Item (AEA-10.md:139): "`temp_sqlite()` home: DO-3 §9 places it in `tests/fakes/`; slice plan §3 gives `tests/fakes/` to AEA-11. Which file does AEA-10 own?"

- `docs/design/code-design.md:615`: "| `tests/fakes/` | A0 | Areas put their own fixtures in their own test folders |"
- `docs/design/code-design.md:626`: "InMemoryTraceSink, temp_sqlite() fixture (applies every schema/*.sql to a temp working copy)"
- `docs/design/code-design.md:641`: "`policy/limits.py`, `repos_core.py`, `tests/fakes/` or `conftest.py`."
- Ownership split between AEA-10 and AEA-11 is not stated in these lines; the slice plan §3 is not in the searched set.

## AEA-10 #3: demo_event record location

Item (AEA-10.md:141): "DO-6 WF-5's `demo_event` record: a row in `events`, in `demo_state`, or its own table in `60_cases.sql`?"

- `docs/design/observability-contract.md:80`: "| WF-5 | Demo controls: staffing (CON-7) and clock (CON-8) | user-operation | API, presence state, demo clock | `request_id`; a `demo_event` row per change | request, demo_event | CAP-5 |"
- `docs/design/observability-contract.md:118`: "| `job_run`, `eval_run`, `eval_case_result`, `experiment`, `ingest_run`, `deploy_record`, `reset_event`, `seed_event`, `demo_event` | the run records named in the registry | Their workflows |"
- `docs/design/code-design.md:671`: "`repos_cases` with `demo_state` and job/reset/seed records (A6)"
- No table for `demo_event` is named in the sources; `demo_state` and `events` are named in `docs/design/system-design.md:436` as tables but not as homes for `demo_event`.

## AEA-13 #1: exactly 24.0 hours away

Item (AEA-13.md:115): "A window exactly 24.0 hours away: the FAQ says "more than 24 hours before the window are free" and "Inside 24 hours there is a $49 late-cancellation fee". Is exactly 24 hours fee-bearing or free?"

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:830`: "**Issued policy [Meridian].** Cancelling or rescheduling inside 24 hours of the window costs $49, for every tier"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:853`: "**Changes with no fee** (more than 24 hours before the window): the AI reschedules itself, under the normal booking rules"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:877`: "**Cancellation inside 24 hours [Innocent, 2026-10-20: "yes"]:** handled the same way. The same $49 applies, so the AI"
- `docs/data/issued/meridian_dataset/call_transcripts/CALL-20260707-0002.txt:13`: "Agent: No problem. Since it's more than 24 hours out there's no cancellation fee. You're all set."
- Exactly-24.0 boundary is not stated in any source (the sources use "inside" and "more than").

## AEA-13 #2: fee note for a plumbing booking

Item (AEA-13.md:117): "The fee note for a `plumbing` booking: the fee schedule and service catalog give no plumbing visit fee. What does the confirmation say?"

- `docs/data/issued/meridian_dataset/knowledge_base/pricing/repair_price_book_2026.csv:17`: "FEE-DIAG,Diagnostic visit,Fee,89,89,N,Waived for members" (a general visit fee, not plumbing-specific)
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:367`: "explain each line: Diagnostic visit $89, Contactor replacement $245, After-hours dispatch $144."
- `docs/data/issued/meridian_dataset/knowledge_base/pricing/repair_price_book_2026.csv:13`: "PL-DRN-01,Drain clearing,Plumbing,149,290,Plus only," (plumbing rows exist; none is a visit fee)
- No source states a plumbing-specific visit fee or the confirmation wording for a plumbing fee note. Searched: plumbing, visit fee, diagnostic, dispatch.

## AEA-13 #3: full list of Lakeway ZIPs not served

Item (AEA-13.md:119): "The full list of Lakeway ZIPs treated as not served (audit K-11 names 78734 and 78738 "e.g.")."

- `docs/data/issued/meridian_dataset/knowledge_base/policies/service_area.md:15`: "Not serviced: San Marcos, Bastrop, Elgin, Lakeway (west of 620)."
- `docs/analysis/2026-10-20-brief-audit.md:235`: "excludes San Marcos, Bastrop, Elgin and Lakeway "west of 620" | FAQ (2026-03-02) city list without them. `SCHEMA.md` zone map has **no zone** for Dripping Springs or Manor. "Austin: 787xx (all)" includes Lakeway's ZIP"
- `docs/prd/inno-aea-callcenter-prd.md:219`: "Lakeway west of 620 not served"
- No ZIP list for Lakeway is given in any source. Only the city name and "west of 620" appear.

## AEA-14 #1: business-day due rule

Item (AEA-14.md:127): "The business-day due rule is given only by examples (Friday 10:00 + 1 → Monday 7:00 pm; + 2 → Tuesday 7:00 pm). Is a business day Monday–Friday only (Saturday has phone hours), does the KB holiday image remove days, and what is the due when "now" is after 7:00 pm or on a weekend?"

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:383`: "(The "within 1 business day" wording is the settled part of OD-4. The due time assumes the FAQ phone hours, Mon–Fri"
- `docs/data/issued/meridian_dataset/knowledge_base/faq/customer_faq.md:5`: "- Phone support: Monday–Friday 7:00am–7:00pm, Saturday 8:00am–4:00pm. Closed Sunday."
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:445`: "- "A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.""
- Holiday handling: `docs/data/issued/README.md:17` lists `policies/holiday_hours_2026.png` (an image; not read). No source states the holiday effect on the business-day count or the after-7pm rule.

## AEA-14 #2: fee_bearing_change Promise.due_at (window start vs 1-business-day)

Item (AEA-14.md:130): "For `fee_bearing_change`, `Promise.due_at`: the window start (consolidated §9.3: the case's internal due time, "a staff target, not a promise to the customer") or the 1-business-day due the customer is told? Where does the other one live?"

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:858`: "- **The due time is the window start.** The case is **P2 time-sensitive**, and its internal due time is the start of the"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:860`: "by due time. This is a staff target, not a promise to the customer."
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:859`: "appointment window, not one business day. The supervisor view alerts at once, and the case sorts above other P2 cases"
- Where the other value is stored is not stated.

## AEA-14 #3: danger / burning-unclear (P1) with nobody online

Item (AEA-14.md:132): "Danger and burning-unclear (P1) cases with nobody online: SCREEN_SPECS shows a separate "reviewed within 1 business day" line that is not an R-26 table string. Which `policy_row`, text and due do they carry?"

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:699`: "...the online case will be reviewed within 1 business day, never as the emergency wait. Without a"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:147`: "| **Nobody online** | No queue and no "someone will join shortly". "No representative is online right now. A representative will get back to you within 1 business day. Your reference is …""
- `docs/ux/03-structure/SCREEN_SPECS.md:97`: "| Burning smell, both ruled out | FLOW-2 → FLOW-5 | default | Urgent booking: slot card marked "Urgent" | CON-2 |"
- The "reviewed within 1 business day" line named in SCREEN_SPECS was not found in SCREEN_SPECS itself (searched: reviewed, reviewed within, 1 business day). The `policy_row` value for these cases is not stated.

## AEA-14 #4: unsupported_action / unsupported_other row, priority, outcome; producer of late_technician

Item (AEA-14.md:134): "`unsupported_action` / the planner's `unsupported_other`: which D4 row, priority and outcome apply, and what produces `late_technician` (no planner value or rule names it)?"

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:1050`: "| **D4** Unsupported requests | Decided (principle + list) | Serious cases get priority; limited answers allowed; unfinished tasks get a case; requests for a person honoured | Priority thresholds tuned in testing |"
- `docs/design/contracts/internal-components.md:456`: "| 4 | Planner `handoff` (`membership_cancel`, `unsupported_other`, …) | escalate or offer per the D4 row | D4 table (`policy/handoff.py`) |"
- `docs/design/contracts/internal-components.md:471`: "LATE_TECHNICIAN = "late_technician"; FEE_BEARING_CHANGE = "fee_bearing_change"; MEMBERSHIP_CANCEL = "membership_cancel"" (defined as a constant; no producer named)
- `docs/design/contracts/internal-components.md:472`: "UNSUPPORTED_ACTION = "unsupported_action"; IDENTITY_UNVERIFIED = "identity_unverified"; AI_FAILURE = "ai_failure"". No D4 row for `unsupported_action` text found.

## AEA-14 #5: "follow-up window" that makes membership cancel P2

Item (AEA-14.md:136): "Membership cancel: what is the "follow-up window" that makes it P2 instead of P3 (consolidated §9.4)?"

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:910`: "| **Turn off auto-renew** (MEM-CANCEL 13) | After the code: read `membership_renewal_date` and tier; explain the cancellation rules (`membership/comfort_club_overview.md`) |" (the nearest passage; it does not define a follow-up window)
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:482`: "| **Waiting** | Blocked on the customer, another team or a scheduled follow-up window | Named person |" (a generic term, not a time)
- No source found defining a "follow-up window" for membership cancel. Searched: follow-up window, follow-up, membership_cancel, MEM-CANCEL, cancel membership.

## AEA-14 #6: failure-signal reading ("failed twice in a row", two timeouts, models_disabled)

Item (AEA-14.md:137): "Rule 6 says a specialist "failed twice in a row", while DO-1 §8.2 ends the turn in a handoff after one failure plus its retry; DO-1 §8.1 says two timeouts in a conversation lead to a person offer, which rule 7 does not list; and `models_disabled` is an input no rule uses. Which reading holds?"

- `docs/design/contracts/internal-components.md:458`: "| 6 | `halt` set, or a specialist `failed` twice in a row | escalate, `degraded=True` | `ai_failure` → P3 (PRD §5 *Reliability*) |"
- `docs/design/system-design.md:387`: "- Two timeouts in one conversation count as a failure signal (OD-6): the next reply offers a person."
- `docs/design/contracts/internal-components.md:437`: "models_disabled: bool                             # our cap or the provider's"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:724`: "**OD-6. Failure-signal thresholds. Decided as a starting point.** The two-attempt thresholds (C1) are hypotheses for"
- DO-1 §8.2 text itself was not in the searched set as a quote.

## AEA-14 #7: R-7 "both ruled out" path

Item (AEA-14.md:140): "R-7's "both ruled out" path ("an urgent booking plus a priority case", WP-6 step 3): which reason and priority?"

- `docs/prd/inno-aea-callcenter-prd.md:155`: "| R-7 | Burning smell with no breaker information: ask whether breakers have **already** tripped and whether there is smoke, sparks or flames (never ask them to check). If yes → R-5. If unclear → a conditional safety instruction, the emergency number and a P1 case. If both are ruled ou…"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:825`: "4. **Only when both are clearly ruled out:** offer the earliest booking, marked urgent, and create a priority case so"
- `docs/ux/03-structure/SCREEN_SPECS.md:97`: "| Burning smell, both ruled out | FLOW-2 → FLOW-5 | default | Urgent booking: slot card marked "Urgent" | CON-2 |"
- The priority value of the case (and reason) is cut off in the PRD line; the consolidated line says only "a priority case". WP-6 was not searched.

## AEA-28: cross-issue types (WindowQuery, WindowsFound, OutOfArea, SlotTaken, Refused)

Item (AEA-28.md:158): "**needs-decision:** none beyond the cross-issue item that DO-4 §14 names `WindowQuery`, `WindowsFound`, `OutOfArea`, `SlotTaken` and `Refused` without fields; AEA-02 must define them, or this plan records `blocked-on AEA-02`."

- `docs/design/contracts/internal-components.md:967`: "def find_windows(self, query: WindowQuery, now: datetime) -> WindowsFound | OutOfArea: ..."
- `docs/design/contracts/internal-components.md:969`: "lookup: LookupEntry) -> WriteResult | SlotTaken | Refused: ..."
- `docs/design/contracts/internal-components.md:971`: "lookup: LookupEntry) -> WriteResult | SlotTaken | Refused: ...                    # refuses fee-bearing"
- The five types are named in these signatures; no field list for any of them was found in the searched sources.

## AEA-29 #1: CaseService constructor and DemoService method signatures

Item (AEA-29.md:102): "DO-4 §13 gives `CaseService` methods but no constructor, and DO-4 does not define `DemoService`'s method signatures (`staffing`, `set_staffing`, `advance_clock`, DO-3 §4.4). AEA-29 and AEA-30 call each other: fix both in DO-4 §14 (AEA-02 follow-up) before either plan is checked."

- `docs/design/contracts/internal-components.md:922`: "class CaseService:                                    # services/cases.py (A6): ONE concrete class (review S-7, S-8)"
- `docs/design/contracts/internal-components.md:167`: "brief: BriefAssembler; demo: DemoService; limits: Limits"
- `docs/design/code-design.md:351`: "| `services/cases.py` | Own the case lifecycle, its version, follow-up and activities. | concrete `CaseService` (§13) | UoW, clock |"
- Gap: no `DemoService` method signature (`staffing`, `set_staffing`, `advance_clock`) found in any searched source. No `CaseService` constructor line found beyond the class header. Searched: DemoService, staffing, set_staffing, advance_clock, CaseService.

## AEA-29 #2: CON-12 "current value" and "changed" flag (invoice and appointment re-read)

Item (AEA-29.md:105): "CON-12's "current value" and the brief items' `changed` flag need a re-read of invoices (`repos_identity`, AEA-27) and appointments (`repos_booking`, AEA-28); DO-4 names no such read. Recommended: inject a `current_value(SourceRef)` callable per DO-3 S-20, wired to the real repositories at AEA-52; otherwise record `blocked-on AEA-27, AEA-28` for that part."

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:303`: "shows **the snapshot** (what the AI saw) and **the current value**, with a "changed since" marker when they differ."
- `docs/prd/inno-aea-callcenter-prd.md:236`: "| R-29 | **Lookup log:** every tool call records tool, record or passage ID, time, the result seen, and the message that used it. The case shows only pertinent sources, each as a snapshot plus the current value with a "changed since" marker |"
- `docs/design/code-design.md:215`: "│   ├── sqlite/repos_identity.py                 identity_codes, demo_inbox, invoices (read)                A4    1"
- `docs/design/contracts/internal-components.md:905`: "identity: IdentityRepos    # A4: identity_codes, demo_inbox, invoices (read)"
- No source names a read of appointments for `current_value`. The `current_value(SourceRef)` callable is named only in the ticket.

## AEA-29 #3: due-soon window and unowned threshold

Item (AEA-29.md:109): "the due-soon window and the unowned threshold behind `due_state = due_soon` and the Due soon / Unowned lanes ("proposed thresholds, to tune", consolidated §6); no value is set in any source."

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:513`: "### Alerts (proposed thresholds, to tune) [Inference]"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:518`: "| **Unowned** | Unassigned longer than a set time while staff are on shift | Supervisor |"
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:519`: "| **Due soon** | Within a set window of the due time and not resolved | Owner, then supervisor |"
- Confirmed: no numeric value in any searched source (searched: due soon, unowned, proposed thresholds, to tune, set window).

## AEA-29 #4: does no_answer / left_message before due keep the promise

Item (AEA-29.md:111): "does a contact attempt with outcome `no_answer` or `left_message` before due keep the promise (M-13 "a recorded contact")? AC-9 counts only `reached` until decided."

- `docs/design/key-metrics-registry.md:65`: "| M-13 | Promises kept on time (V3, lagging) | outcome | Does the handoff keep its word? | Promises with a recorded contact or resolution before the due time ÷ promises whose due time has passed |"
- `docs/design/key-metrics-registry.md:65` (same line, continued): "...Promises due in the window, on the simulated clock in the proto..." (the numerator wording is "a recorded contact or resolution"; the sources do not define which outcomes count as contact)
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:533`: "**Promises kept on time** as a share of promises due, with the missed ones;"
- No source found for `no_answer` or `left_message` as contact outcomes. Searched: no_answer, left_message, recorded contact, contact attempt.

## AEA-30 #1: DemoService method signatures (same question as AEA-29 #1)

Item (AEA-30.md:92): "`DemoService` method signatures are not in DO-4 (DO-3 §4.4 names `staffing`, `set_staffing`, `advance_clock` only); AEA-29, 40, 43, 47 call them. Add to DO-4 §14 (AEA-02 follow-up) before wave 2 plans are checked."

- See AEA-29 #1 quotes (`internal-components.md:167`, `:511`, `code-design.md:348`).
- `docs/design/contracts/internal-components.md:511`: "def __init__(self, uow: UnitOfWorkFactory, cases: CaseService, demo: DemoService, clock: Clock) -> None: ..."
- `docs/design/code-design.md:348`: "| `services/session.py` | Open a conversation with its fixed greeting. | `SessionService.open` | UoW, clock, `DemoService`, texts |"
- Gap: no method signature for `DemoService` found.

## AEA-30 #2: due-soon window and unowned threshold (same question as AEA-29 #3)

Item (AEA-30.md:94): "the due-soon window and the unowned threshold ("Unassigned longer than a set time while staff are on shift"; "Within a set window of the due time") are "proposed thresholds, to tune" (consolidated §6) with no value in any source."

- See AEA-29 #3 quotes: `consolidated.md:513`, `:518`, `:519`.
- `docs/ux/03-structure/IA.md:169`: "**Five lanes in fixed order**: P0 and P1 · Overdue · Due soon · Unowned · Stuck waiting." (lane order only; no threshold)

## AEA-30 #3: who writes the health_event for a missed scheduler tick

Item (AEA-30.md:97): "who writes the `health_event` for a missed scheduler tick (DO-6 WF-7 and *Missing instrumentation*): `SchedulerJob` (needs a DO-4 constructor addition, `repos_ops` is AEA-32's) or AEA-32's health service reading the last `job_run`. Recommended: AEA-32, so DO-4 §14 stays frozen; until decided this ticket writes `job_run` only."

- `docs/design/observability-contract.md:117`: "| `health_event` | health check results, restarts, alerts firing and clearing, missed job ticks | Health check, alert evaluator, WF-7 |"
- `docs/design/observability-contract.md:82`: "| WF-7 | Due-soon and overdue job on the fixed clock (consolidated direction §10) | background-job | Scheduler, case store, promise records | `job_run_id` per tick; `case_ref` per case touched | job_run, case_event (`due_soon`, `overdue`), promise status cha…"
- `docs/design/observability-contract.md:251`: "| CAP-5 | WF-5 and WF-7: advance the demo clock past a promise's due time | `demo_event`; a `job_run` per tick; the promise marked overdue; overdue `health_event` when a tick is skipped | — |"
- `docs/design/code-design.md:360`: "| `services/health.py` | Keep the heartbeat, record health events, exit after repeated failures. | `Heartbeat`, `Watchdog` | UoW (`repos_ops`) |" (health service owns health events, supporting the AEA-32 option)
- The sources name WF-7 and CAP-5 as the trigger; they do not say which class writes the row.

## AEA-30 #4: demo clock start time on Fri 2026-10-16 (10:00 vs 14:20)

Item (AEA-30.md:101): "the demo clock's start time of day on Fri 2026-10-16: 10:00 (worked pairs header; WP-4 "two hours away" from a 12–4pm window) or 14:20 (UI_CONTRACTS CON-8 `START` mock). Recommended 10:00, since WP-4's fee rule depends on it."

- `docs/data/worked-pairs.md:15`: "The clock is the dataset's "today", Friday 2026-10-16, 10:00. Nobody is online (the default)."
- `docs/data/worked-pairs.md:158`: "Austin (central), not a member, tune-up appointment 1 **today, 12pm–4pm**, two hours away. The transcript's "tomorrow""
- `docs/data/worked-pairs.md:165`: "2. Read the appointment: tune-up today 12–4pm, 2 hours away, so inside 24 hours."
- `docs/ux/03-structure/UI_CONTRACTS.md:20`: "Times are ISO 8601 with offset (America/Chicago, the demo clock)." (no `START` value found)
- The 14:20 value was not found in `UI_CONTRACTS.md` or `ui-contracts.openapi.yaml` (searched: 14:20, START, clock).

## AEA-31 #1: which cases make the demo seed

Item (AEA-31.md:84): "which cases make the demo seed. Sources say only "a few labelled demo cases (built from inventory cases, marked 'demo seed')" (consolidated §8; R-33). Recommended: the four rows in CON-11's `SEEDED` mock (MHC-C-0005 refund, MHC-C-0006 conduct complaint, MHC-C-0007 billing dispute INV-204411, MHC-C-0008 gas-smell safety), with promises recomputed from the table at the demo start."

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:643`: "work. the case store starts with a few labelled demo cases (built from inventory cases, marked "demo seed")."
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:552`: "| 2 | Seeded dispute, INV-204411 | `SCHEMA.md` seed, synthetic customer lines | Sources (snapshot vs current), full lifecycle |"
- `docs/data/issued/README.md:18`: "`SCHEMA.md` gives status values, the city→zone map, expected booking behaviour and four seeded test customers"
- The `SEEDED` mock in CON-11 and the MHC-C-0005…0008 IDs were not found in `docs/ux/03-structure/*` (searched: SEEDED, seeded, MHC-C-0005). No source names those four case rows.

## AEA-31 #2: reset clears tables owned by sibling tickets (identity_codes, demo_inbox, staff_sessions)

Item (AEA-31.md:88): "reset must clear or reset tables that same-wave siblings own and DO-4 names no method for: `identity_codes` and `demo_inbox` (`repos_identity`, AEA-27) and session roles in `staff_sessions` (`repos_staff`, AEA-44). Recommended: each owner adds one `clear_for_reset()` method to its repository, named in DO-4 §13 before planning (an AEA-02 follow-up); for roles, alternatively a reset generation in `demo_state` (AEA-10) that AEA-44 compares on each staff call. Until decided, record `blocked-on AEA-27, AEA-44` for those two parts; AC-4 and AC-6 are not narrowed."

- `docs/design/system-design.md:436`: "`demo_state` (presence, clock), `staff_sessions`. WAL mode, `busy_timeout` 5 s [A]."
- `docs/design/system-design.md:435`: "`followups`, `lookup_log`, `actions`, `turns`, `model_calls`, `identity_codes`, `demo_inbox`, `events`, `flags`,"
- `docs/design/contracts/internal-components.md:905`: "identity: IdentityRepos    # A4: identity_codes, demo_inbox, invoices (read)"
- `docs/design/system-design.md:659`: "| **Identity service** | Locate, issue, hash, deliver, verify and expire codes; caps (3 tries, 3 codes [A]) | `identity_codes`, `demo_inbox` | Code gates, account and scheduling tools; CON-6 |"
- No `clear_for_reset()` method and no "reset generation" appears in any searched source.

## AEA-31 #3: all-or-nothing join of restore_working_copy and clear_checkpoints

Item (AEA-31.md:93): "how `restore_working_copy` (a file-level restore, AEA-10) and `clear_checkpoints` (the separate `checkpoints.sqlite`) join one all-or-nothing reset. If AEA-10's callables cannot be made restorable on failure (for example by restoring into a temporary file and swapping last), record `blocked-on AEA-10`; AC-2 is not narrowed."

- `docs/design/code-design.md:335`: "| `adapters/checkpointer.py` | Build the LangGraph checkpointer; prune and clear it. | `checkpoints.sqlite`, its own file and lock (DO-1 §4); `prune(keep=2)` [Decided SDQ-10] and `clear()` are handed to A6's services as callables |"
- `docs/design/code-design.md:355`: "| `services/reset.py` | Restore the demo all-or-nothing. | `ResetService(uow, restore_working_copy, clear_checkpoints, seed_demo)` | injected callables (review S-3) |"
- `docs/design/code-design.md:676`: "`ResetService` and `SchedulerJob` receive `restore_working_copy`, `clear_checkpoints`, `prune_checkpoints`, `seed_demo` as callables from the container"
- The sources require all-or-nothing reset (`services/reset.py`) but do not state the restore-on-failure mechanism.

## AEA-32 #1: window for latency and failure-rate alerts; evaluator frequency

Item (AEA-32.md:80): "the window the latency (p95 > 12.5 s) and failure-rate (> 2%) alerts are computed over, and how often the evaluator runs. DO-6 and DO-7 say "turns in the window" without a length."

- `docs/design/key-metrics-registry.md:76`: "...Live turns in the window, and load-run turns;..."
- `docs/design/key-metrics-registry.md:113`: "| M-24 | Turns degraded by a model or tool error or timeout | Turns, per 100 | Provider; role; reason | Operator (monitoring page) | Alert line 2% [T] | Continuously on the page |"
- `docs/design/key-metrics-registry.md:112`: "Hard line p95 ≤ 12.5 s at 20 at once [T]; baseline 10.2 s [M]" (M-23 gives the 12.5 s line but no alert window)
- No window length or evaluator frequency found. Searched: window, alert window, 12.5, 2%, turns in the window.

## AEA-32 #2: heartbeat staleness bound

Item (AEA-32.md:82): "the heartbeat's staleness bound and what advances it (DO-3 §2.3 says only "an in-memory heartbeat"). Measurement-settled [A]; the planner proposes it as a named constant."

- `docs/design/code-design.md:147`: "3. **`/healthz` is `async def` and reads an in-memory heartbeat**, never the pool or SQLite, so a pool busy with long"
- `docs/design/code-design.md:360`: "| `services/health.py` | Keep the heartbeat, record health events, exit after repeated failures. | `Heartbeat`, `Watchdog` | UoW (`repos_ops`) |"
- `docs/design/contracts/api-con-mapping.md:111`: "| 2 | **65 s browser give-up; 15 s SSE heartbeat** | 65 s follows from SDQ-1's 60 s plus DO-1 §8.1's "deadline + 5 s" rule. DO-1 says nothing on heartbeats |" (a different heartbeat)
- No staleness bound value and no description of what advances the heartbeat beyond "in-memory" were found.

## AEA-32 #3: who writes the health_event for a missed scheduler tick (same question as AEA-30 #3)

Item (AEA-32.md:84): "who writes the `health_event` for a missed scheduler tick (DO-6 WF-7): this ticket reading the last `job_run` (`repos_cases`, AEA-10), or AEA-30's `SchedulerJob` (needs a DO-4 constructor change). Recommended: this ticket, as a stale-`job_run` check in the evaluator."

- See AEA-30 #3 quotes: `observability-contract.md:117`, `:82`, `:251`; `code-design.md:360`.
- `docs/design/contracts/internal-components.md:907`: "cases: CaseRepos           # A6: cases, case_events, promises, followups, activities, demo_state, job_runs, reset/seed"
- `docs/design/code-design.md:360` places health events in `services/health.py` on `repos_ops`, not in `repos_cases`.

## AEA-32 #4: how eval results reach eval_run / eval_case_result

Item (AEA-32.md:87): "how eval results reach `eval_run` / `eval_case_result`: the harness is HTTP-only (DO-3 §3, DO-5) and system design §A.5 says the harness writes `eval/` output, while api-con-mapping CON-20 says CON-20 "reads the eval results tables A11's harness writes". This ticket only creates the tables and reads; the writer is AEA-24/AEA-53's call."

- `docs/design/system-design.md:685`: "| Eval results | `eval/` output written by the harness (owned by `evaluation-plan.md`) | Reported numbers, per split | Eval harness | CON-20, README |"
- `docs/design/contracts/api-con-mapping.md:64`: "| CON-20 | `getLatestEval` | `web/routes/reads.py` → `services/metrics_reader.py` (A10b) | **Agrees** | Reads the eval results tables A11's harness writes |"
- `docs/design/observability-contract.md:84`: "| WF-9 | End-to-end eval, dev split and sealed held-out split (R-38, R-39) | validation | Eval runner, the whole agent (WF-1 path), DB-copy checker | `run_id` + `case_id`; ..." (names eval_run and eval_case_result as outputs)
- The two sources differ (`eval/` file output vs tables written by the harness). No source names AEA-24 or AEA-53 as the writer.

## AEA-52 ND-52a: owner of the relayed-turn proof (CAP-4)

Item (AEA-52.md:123): "**ND-52a** `needs-decision:` CAP-4 requires the relayed customer turn (`outcome = to_staff`), but that message enters through CON-2 and the graph's `ai_paused` gate, which only AEA-51 binds. Options: **(A, recommended)** move AC-14 to AEA-51 and add AEA-44 and AEA-46 as AEA-51 blockers (both wave 2, so no wave moves); (B) make AEA-51 a blocker of this issue, which pushes this issue to wave 4, AEA-55 to wave 5 and AEA-56 to wave 6 (critical path 6 → 7); (C) leave the relayed-turn record to AEA-55's UI run. Which should own the relayed-turn proof?"

- `docs/design/contracts/internal-components.md:622`: "#   AI_PAUSED (delivered_to_representative=True; outcome "to_staff")"
- `docs/design/contracts/internal-components.md:752`: "| A representative owns the chat (`controller = human`) | `to_staff` (not a failure) | Notice `AI_PAUSED`, `delivered_to_representative: true`; the message is written to the thread and appears on CON-21 as `customer_message` | — |"
- `docs/design/observability-contract.md:53`: "| `turn` | `outcome` | `answered` (just talk), `acted` (a specialist ran and finished), `safety_reply`, `handed_off`, `to_staff` (AI paused; the message went to the representative), `degraded_handoff` |"
- `docs/design/observability-contract.md:251`: "| CAP-5 | ..." (no CAP-4 row found in this sweep; `ai_paused` gate binding is not stated in the searched sources beyond internal-components.md:209)

## AEA-53: no writer for conversation.outcome = abandoned

Item (AEA-53.md:118): "Reported gap (not a decision for this issue): **no ticket writes `conversation.outcome = abandoned`** (M-18's 30-minute end rule, DO-7 difference 4). Until a writer exists, M-18's numerator is 0 by construction, and CON-18 must show that honestly rather than derive it."

- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:533`: "...outcomes (resolved by AI, escalated, abandoned, failed) with denominators; handoffs by reason linked to example cases..."
- `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md:537`: "**abandoned** conversation (S-166; audit E-1)."
- `docs/design/observability-contract.md:53`: "| `turn` | `outcome` | `answered` (just talk), `acted` (...), `safety_reply`, `handed_off`, `to_staff` ..., `degraded_handoff` |" (the turn outcome list has no `abandoned` value; the conversation outcome is not in this row)
- `docs/analysis/2026-10-20-brief-audit.md:105`: "times *without* turning wrong answers, abandoned conversations or unsafe deflection into apparent"
- The M-18 30-minute end rule and "DO-7 difference 4" were not found in the searched sources (searched: abandon, abandoned, M-18, 30-minute).

---

## Summary

- Items: 31 (AEA-10: 3; AEA-13: 3; AEA-14: 7; AEA-28: 1; AEA-29: 4; AEA-30: 4; AEA-31: 3; AEA-32: 4; AEA-52: 1; AEA-53: 1).
- No source at all for the open question: 1 (AEA-14 #5, "follow-up window").
- Source found for the item but the specific value or term the item asks for is not defined anywhere: AEA-13 #1 (exact 24.0), AEA-13 #2 (plumbing visit fee), AEA-13 #3 (Lakeway ZIP list), AEA-14 #1 (holiday effect, after-7pm rule), AEA-14 #4 (`late_technician` producer, `unsupported_action` row), AEA-14 #6 (which reading holds), AEA-29 #1 and AEA-30 #1 (DemoService signatures), AEA-29 #2 (appointment re-read), AEA-29 #3 and AEA-30 #2 (thresholds, no values), AEA-30 #4 (14:20 mock not found), AEA-31 #1 (SEEDED mock not found), AEA-31 #2 (`clear_for_reset`, reset generation), AEA-32 #1 (alert window), AEA-32 #2 (staleness bound), AEA-32 #4 (eval writer).
- Duplicates across tickets: DemoService signatures (AEA-29 #1 = AEA-30 #1); due-soon/unowned thresholds (AEA-29 #3 = AEA-30 #2); missed-tick `health_event` writer (AEA-30 #3 = AEA-32 #3); restore/checkpoint reset join (AEA-10 #1 relates to AEA-31 #3).
- Not searched: the PDF fee schedule (`pricing/2026_fee_schedule.pdf`), the holiday image (`policies/holiday_hours_2026.png`), `docs/design/evaluation-plan.md` beyond grep hits, `DO-1`/`DO-3`/`DO-4` section text, the slice plan §3, and `WP-6`. Those would need their own pass.
