# Plan — [AEA-29] cases and handoff: case service, handoff service, brief

**Status:** planned — READY once its prerequisites are on `main` (§9); BLOCKED-ON until then (refreshed 2026-10-21, see
*Refresh log*)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/29 (identical to
`docs/plans/tickets/AEA-29.md`) · **Base revision:** read against `main` `16ca639` (AEA-01, 03, 04, 08, 25 merged; no
`domain/`, `adapters/sqlite/` bodies, `policy/handoff.py` or `tests/fakes/` yet) plus the plans of AEA-02, 10, 11, 14, 16 in
this folder; **refreshed** against AEA-02's built, unmerged worktree (`aea-02-aea-02-domain-ports` `a33ce4c`) and the
AEA-10/11/14/16 plans as revised 12:08–12:14 UTC · **Wave:** 2 · **Lane:** build-loop · **Risk:** `risk::security` (frozen tests first; security agent at the
wave-2 merge)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (written 11:01 UTC, refreshed ~12:30 UTC, same model) · **Test-writer:** `test-writer-agent` (frozen files, §3d) ·
**Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-29-cases-handoff` in
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-29`), cut from `main` after every §9 prerequisite merged.

---

## Refresh log (2026-10-21, ~12:30 UTC; `main` still `16ca639`)

What changed since the 11:01 version, and why. Everything not listed was re-checked and still holds.

| # | Change | Evidence |
|---|---|---|
| RF-1 | **Defining modules made explicit (§4.1).** `HandoffReason`, `Priority`, `Presence`, `CaseState`, `Promise`, `FollowUp`, `SafetyKind`, `EventId` are *defined* in `meridian.domain.common`; `domain.handoff` re-exports the first six with explicit `X as X` imports, and `domain.state` re-exports `IdentityState` (defined in `domain.identity`), so the plan's imports type-check under `mypy --strict`. `SafetyKind` and `EventId` must come from `domain.common` (not re-exported). `EventId` is `Annotated[int, Field(ge=0)]`, not a class. | AEA-02 worktree `src/meridian/domain/{common,handoff,state,identity}.py` |
| RF-2 | **Stream keys are AEA-10's, not built here.** AEA-10 now exports `StreamKey`, `CASE_STREAM_PREFIX`, `thread_stream(thread_id)` (the bare thread id) and `case_stream(case_ref)` (`"case:" + ref`) from `meridian.adapters.sqlite.rows`. Step 0.4 no longer writes private helpers; every `thread_stream(…)` / `case_stream(…)` in this plan calls those two functions. | AEA-10 plan §4.3 `rows.py` |
| RF-3 | **`Speaker` already exists** in `meridian.domain.blocks` with exactly the OpenAPI `Speaker` shape (`kind`, `display_name: str \| None`, both required). The view-type follow-up reuses it; Appendix A no longer asks for a new one. | AEA-02 worktree `domain/blocks.py` line 19; OpenAPI `components.schemas.Speaker` |
| RF-4 | **One view-type follow-up for cases A-2, shared with AEA-30.** AEA-30's plan (§8 R-1) asks the orchestrator for the same AEA-02 follow-up and proposes `domain/views.py`; this plan now proposes the same module (was `domain/case_views.py`) so one ticket covers both. Still **no ticket cut** (`docs/plans/tickets/` has no AEA-02b). | AEA-30 plan §4.3, §8 R-1; `grep -rn 02b docs/plans/tickets` → nothing |
| RF-5 | **AC-23 still blocked.** `CaseDetail` in `ui-contracts.openapi.yaml` has exactly `case, promise, brief, identity, sources, conversation, activities, live, other_cases, agent_version, as_of`; no `events`. The file is unchanged since `ca9ab5c`. | `python3 -c "yaml…CaseDetail.properties"` |
| RF-6 | **R-5 corrected.** `policy/texts.py` has `OVERSIGHT_SHIFT_ENDED_ONE_WAITING` ("Simulated shift ended with 1 customer waiting. …"), but only for one waiting customer, and AEA-10's `DemoEventsRepo` has `insert` only (no read of the latest staffing change), so oversight still builds only `overdue` alerts. The email / general follow-up texts are still missing (only `FOLLOWUP_SAVED_PHONE`, `FOLLOWUP_LEGEND`). | `TextId` listing on `main`; AEA-10 §4.3 `DemoEventsRepo` |
| RF-7 | **R-3 re-verified.** `tests/unit/web/test_container.py::test_every_register_stub_present` calls each `register_*` on a fresh container and asserts `not fresh._factories`; filling `register_cases` would turn AEA-01's test red, so the hunk stays a no-op here. | `main` `tests/unit/web/test_container.py` lines 64–83 |
| RF-8 | **Step 0.3 gains a one-shot import check** (prints `ok`) so the implementer proves every name and module in one command before writing code. | §5 step 0.3 |
| RF-9 | Re-checked unchanged: every repository signature §4.1 lists (AEA-10 §4.3, incl. `set_live_state`, `latest_id`, `list_for_customer`, `briefs.upsert/get`, `SqliteUnitOfWork.connection` / `.committed`); `promise_for`, `case_due_at` (now also window start for `burning_ruled_out`, CAS-16 A), `due_label`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`, `STAFF_GUIDANCE_FOR` (five keys; refund prefix "Issue refunds of any kind.") in AEA-14 §4b; `FixedClock(at=WORKED_PAIRS_NOW)`, `.advanced(by)` (AEA-11); `StaffGuidance(passage_id, file, section, version_label, text, text_sha256)` (AEA-16); `ROLE_ACTIONS`, `STAFF_PERSONAS` (Riley / "Riley (demo)", "Demo supervisor", "Demo business owner"), `ASSIGNEE_ROLES`, `CUSTOMER_SPEAKER_NAME = "Customer"`, `StaffActor.owns`, `actor_for` (AEA-02 code); every `ApiErrorCode` this plan returns; `TextId.SHIFT_ENDED`, `RECORDED_NOT_SENT`, `FOLLOWUP_SAVED_PHONE`, `OVERSIGHT_OVERDUE`, `STAFFING_BANNER`, `GREETING`, `RedactionProfile.SONNET` on `main`; DO-3 arrow `SVC --> SQL` (services may import `adapters.sqlite.rows`). | as named |

---

## 1. Goal and sources

### Goal

From the issue's *What to build*:

> **US-14:** As a **homeowner** whose request needs a person, I need a reference number, the exact promise (who gets back
> to me and by when), and a choice of email or phone and a time window, so that I know what happens next and never repeat
> my story.
>
> **US-19:** As a **representative**, I need an eight-heading brief that keeps facts and customer claims apart, the
> pertinent sources (what the AI saw and the current value), the promise with the follow-up preference beside it, and the
> full chat one click away, so that I can act without re-asking the customer.

This ticket builds the **services only** (no route, no SQL, no model call):

- `src/meridian/services/handoff.py`: `HandoffService` (one write transaction: presence → promise → case + case event +
  promise + `actions(case_opened)` + `events(case_created)` + staff-guidance `lookup_log` rows) and `BriefAssembler`
  (pure eight-heading brief).
- `src/meridian/services/cases.py`: `CaseService` with every DO-4 §13 method (`open_case`, `attach_brief`,
  `open_case_for_thread`, `queue`, `detail`, `oversight`, `apply`, `set_followup`, `record_activity`,
  `convert_live_queued`).
- Two private helper modules inside the A6 area (this plan's decision, §8 R-9): `services/_case_rules.py` (pure rules
  and display values: `allowed_actions`, `due_state`, ordering, lanes, labels) and `services/_case_views.py` (builds the
  OpenAPI-shaped views from rows), so each file stays under the 600-line service cap.

**Concretely (the ticket's worked pair WP-7, demo clock Fri 2026-10-16 10:00 Chicago, nobody online):**

| Input | Output |
|---|---|
| `HandoffService.open(HandoffRequest(reason=refund, priority=P3, trigger="escalation", …), ctx)` for "I want a full refund on the repair. It didn't fix anything and I had to call another company." (seed cases MHC-C-0005…0008 present) | one new case `MHC-C-0009`, P3, lifecycle `unassigned`; stored promise `policy_row="R26.refund"`, text "A representative will get to your refund request within 2 business days.", `extra_lines=("I can't promise an outcome.",)`, `promises.due_at` = `cases.due_at` = Tue 2026-10-20 19:00 Chicago, `due_label` "Tuesday, October 20, 7:00 pm"; one `actions` row (`case_opened`), one `case_events` row (`case_opened`), one `events` row (`case_created`); `alert=None`; one `lookup_log` row `tool="staff_guidance"` for "Issue refunds of any kind." anchored on the refund message |
| `BriefAssembler.assemble(case, state, lookups)` then `attach_extraction(brief, extraction, check)` with needs = the refund sentence, claims = "It didn't fix anything", "I had to call another company" | heading 2 quotes the refund sentence; heading 4 holds the two claims (`checked=False`); heading 6 holds the promise text and its extra line; heading 7 holds the staff-guidance item with `source.kind="lookup_log"` |
| `open` again for the same thread | `created=False`, `MHC-C-0009`, no new `cases`, `actions` or `lookup_log` row |

### Context

Wave 2, critical path (AEA-02 → 10 → 29 → 51). The storage it writes through (`repos_cases`, `repos_core`, every `.sql`)
is AEA-10's; the promise/priority rules are AEA-14's; the types are AEA-02's; the clock fake is AEA-11's; `StaffGuidance`
is AEA-16's. Siblings in wave 2 (`DemoService` AEA-30, `LiveChatService` AEA-46, `FlagService` AEA-44) are used only
as test doubles honouring their contracts. The staff routes (AEA-45), CON-4/CON-5 routes (AEA-42) and the integration
tickets (AEA-51, 52) consume what this ticket produces. Decisions D-4…D-15 are all taken as recommended
(`docs/plans/stage7-signoff.md`); D-9 (CON-4 builds no brief) and D-14 (CAS-16 option A, GRC-3 option A) apply here.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-29.md` | AC-1…AC-24, WP-7 pair, owned files, must-not list, frozen ACs (AC-7 staff-only half, AC-12, AC-13, AC-20) |
| Cases addendum (wins over DO-4, DO-4 §16) | `docs/design/contracts/stage7/cases.md` §1.1–§1.2 (tables, repo names), §3.1–§3.3 (`business_due`, `PROMISE_TABLE`, `promise_for`, `case_due_at`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`), §5 (constructors, rules table, `STAFF_GUIDANCE_FOR`), §6 (`presence(tx)`), §7 (seed set) | every signature in §4; the rules table; both dues; the seed-shaped fixtures |
| DO-4 | `docs/design/contracts/internal-components.md` §1 (`ActionKey`, `CompletedAction`, `OpenCase`), §5 (`LookupEntry`), §7 (handoff types, `BriefAssembler`, `BRIEF_TITLES`), §13 (`CaseService`, `UnitOfWork`), §16 | method names; brief headings; one transaction |
| Staff addendum | `stage7/staff.md` §1 (`StaffRole`, `StaffActor`, `STAFF_PERSONAS`, `ASSIGNEE_ROLES`, `ROLE_ACTIONS`, `CUSTOMER_SPEAKER_NAME`), §5 (live checks; live actions never touch version), §7 (case stream writers), §12 (greeting row = anchor) | `allowed_actions` table; customer speaker; AC-21 |
| Graph addenda | `stage7/graph-nodes.md` §3 (brief assembled, checked, stored; `attach_brief` upsert), §2 (`check_quotes` runs in the node), §4 (`case_write_failed` signal emitted by AEA-36); `stage7/graph-core.md` §2 (`TurnInput.message_id`, `TurnContext`), §13 (`ReplyComposer.handoff_block` is the one block builder) | brief inputs; no signal emitted here; shift-end block via injection |
| Web addendum | `stage7/web.md` §8 (CON-4 calls `open` with `trigger="con4"`, `rule_id="CON4.person"`; `saveFollowUp` route pre-checks `not_verified`), §11 (`CHAT_EVENT_TYPES`; rows of other types are never sent), §14 (thread history reads a `shift_ended` row's stored `handoff` block) | stream keys and payloads |
| Data addendum | `stage7/data.md` §2 (`policy/texts.py`), §3 (`StaffGuidance` fields), §8a (`FixedClock`) | texts only from `TEXTS`; guidance fields; one clock per moment |
| Plans of the blockers | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0–§4.11, `AEA-10.md` §4.3, `AEA-14.md` §4b, `AEA-11.md` step 3, `AEA-16.md` | exact names, row models, repository methods; §4 copies them |
| Signed wire contract (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` (`QueueRow`, `QueueResponse`, `CaseSummary`, `Brief*`, `CaseSource`, `ChatLine`, `Activity`, `PromiseRecord`, `LiveState`, `CaseDetail`, `CaseActionRequest`, `ActivityRequest`, `FollowUpRequest`, `FollowUpView`, `Alert`, `Lane`, `OversightResponse`, `Ce*`, `EvShiftEnded`; examples `getQueue` SEEDED, `getCase` DEFAULT/WAITING/LIVE_JOINED, `applyCaseAction` CLAIMED); `UI_CONTRACTS.md` CON-4, 5, 11…13, 15, 17 | every view field name; error codes and details; example values AC-19 compares |
| UX copy (read only) | `docs/ux/03-structure/SCREEN_SPECS.md` lines 70, 154 (follow-up chooser words), 316–366 (SCR-6 copy: trim note, "Nothing recorded.", "No account match needed for safety.") | staff display strings and their sources |
| Product direction | `docs/analysis/2026-10-20-human-handoff-consolidated-direction.md` §5 (brief format), §6 (states, promise record, alerts), §9.5 (follow-up privacy) | heading content; lifecycle; general-only rule |
| Join amendments | `docs/plans/ux-join/backend-amendments.md` §2 (AEA-29-1…5), §3 (journey criterion); `audit-staff.md` A1–A4, B5 | AC-18…AC-23 |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-2 (line 77), WF-4 (line 79), *Records* (line 117), check "A handoff left no case" (line 237), CAP-3 (line 265) | records, correlation ids, the check query |
| Metrics (DO-7) / Eval (DO-5) | M-10…M-13, M-15, M-27; E-6 | `promises.text`, `policy_row`, `due_at`, status, `case_events`, `cases.owner_role`, `cases.due_at` stay computable |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`, workspace `code-design-solid-modularity.md`, `code-structure.md`, `async-safety.md` rule 1 | affected tests; journey record; context rows; file caps; loud stubs |

---

## 2. Boundary

### Owned files (the only files the test-writer and implementer may create or edit)

| File | Action | Who |
|---|---|---|
| `src/meridian/services/_case_rules.py` | create | implementer (§5 step 1) |
| `src/meridian/services/handoff.py` | create | implementer (steps 2, 4) |
| `src/meridian/services/cases.py` | create | implementer (steps 3, 5, 7, 8) |
| `src/meridian/services/_case_views.py` | create | implementer (step 6) |
| `tests/services/_case_fixtures.py` | create | **test-writer (frozen)** |
| `tests/services/_allowed_actions_table.py` | create | **test-writer (frozen)** |
| `tests/services/test_handoff.py` | create | **test-writer (frozen)** |
| `tests/services/test_cases.py` | create | **test-writer (frozen)** |
| `tests/unit/services/test_brief_assembler.py` | create | implementer |
| `tests/unit/services/test_case_rules.py` | create | implementer |
| `tests/journeys/j6/test_aea_29.py` | create | implementer |
| `tests/journeys/j7/test_aea_29.py` | create | implementer |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-29.md` | create (date = `date +%F` on the commit day) | implementer |
| `.claude/reference/area-map.md` | modify: the A6 row's *Status* cell only | implementer |
| `.claude/state/icm-progress.md` | modify: at most one *Routes verified* row's evidence cell (step 10) | implementer |
| `docs/design/code-design.md` | modify: the one `**Built:**` line under §3 only | implementer |
| `docs/design/contracts/stage7/cases.md` | modify: **append** one subsection "§5a Built by AEA-29" after §5's rules table (step 10); nothing else in the file | implementer |

`tests/services/__init__.py`, `tests/unit/services/__init__.py`, `tests/journeys/j6/__init__.py`,
`tests/journeys/j7/__init__.py` already exist (AEA-01). Do not add a `conftest.py` anywhere.

### Shared surfaces: read only (import or read, never edit)

`src/meridian/domain/*`, `src/meridian/ports/*` (AEA-02); `src/meridian/adapters/sqlite/{db,rows,repos_core,repos_cases,
migrate}.py` and `schema/*.sql` (AEA-10); `src/meridian/policy/handoff.py` (AEA-14); `src/meridian/policy/texts.py`
(AEA-03); `src/meridian/privacy/redact.py` (AEA-04); `src/meridian/retrieval/manifest.py` (AEA-16);
`src/meridian/web/container.py` (see §8 R-3: **not** edited); `tests/fakes/clock.py` (AEA-11);
`tests/fixtures/sqlite.py` (AEA-10); `tests/conftest.py`, `tests/journeys/affected.py`, `pyproject.toml`, `uv.lock`
(AEA-01); the OpenAPI, `UI_CONTRACTS.md`, `SCREEN_SPECS.md`, every other contract file.

### Other tickets' files: never touch

`services/{demo,scheduler,reset,live_chat,staff,person_request,turn,session}.py` (AEA-30, 30, 31, 46, 44, 42, 40, 40);
every `web/routes/*`, `web/schemas/*`, `web/deps.py`; `agent/**`; `policy/*`; `domain/*`; `retrieval/*`;
`adapters/**`; `tests/journeys/support/**` (AEA-57); `tests/unit/web/test_container.py`; `apps/web/**`; `docs/ux/**`;
the briefing, issued data, `docs/archive/`, `docs/parked/`. A missing type, method, column or sentence is a follow-up on
its owner (§8), never a local copy.

---

## 3. Requirements table

### 3a. Acceptance criteria (verbatim ids; full text in the issue) → how built → how verified

`TH` = `tests/services/test_handoff.py`, `TC` = `tests/services/test_cases.py` (both frozen, test-writer),
`TB` = `tests/unit/services/test_brief_assembler.py`, `TR` = `tests/unit/services/test_case_rules.py` (implementer).

| AC | Requirement (short) | Built by (§5 step) | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `open` commits cases, case_events, promises, actions(case_opened), events(case_created), guidance `lookup_log` in one unit of work, or none | steps 3, 4 (one `uow(write=True)`; `tx.commit()` once at the end) | TH `test_open_writes_all_rows_in_one_transaction`, `test_failure_after_case_row_leaves_no_rows` |
| AC-2 [invariant] | One open case per thread; new reason → one case_event + higher priority; same `turn_id` → zero rows; CON-4 always yields a case | step 3 (`open_case` already-open path) | TH `test_second_open_returns_already_open`, `test_repeat_turn_is_idempotent`, `test_new_reason_raises_priority`, `test_con4_always_yields_case` |
| AC-3 [invariant] | Stored promise = `promise_for(...)` for every reason × presence; live-queued sets `live_state='queued'` | steps 3, 4 | TH `test_promise_matches_table` (parametrised 16 reasons × 2 presences) |
| AC-4 [invariant] | Fee-bearing: case due = window start, promise due = Mon 19:00; alert for P0, P1, fee-bearing only | step 3 | TH `test_fee_bearing_stores_both_dues`, `test_alert_for_p0_p1_and_fee_bearing` |
| AC-5 [negative] | No promise-text argument anywhere; heading 6 only from the stored `Promise` | steps 2, 3, 4 | TB `test_heading_six_is_stored_promise`; TH `test_no_promise_text_parameter` |
| AC-6 [failure/refusal] | One retry; second failure → typed `CaseWriteFailed`; P0 case without a customer | step 4 | TH `test_safety_write_retried_once`, `test_safety_case_without_customer` |
| AC-7 [invariant] | One guidance row per `STAFF_GUIDANCE_FOR[reason]` passage, anchored on `handoff_anchor`; heading 7 item; never in responder inputs | steps 2, 4 | TH `test_staff_guidance_attached_not_responded`, `test_staff_guidance_anchor_without_customer_text` (**frozen security half**) |
| AC-8 [invariant] | Nobody online never live-queued; `convert_live_queued(now, tx)` converts, writes events, joins caller tx, returns count | steps 3, 5 | TC `test_unstaffed_never_live_queued`, `test_convert_live_queued`, `test_convert_joins_caller_transaction` |
| AC-9 [failure/refusal] | `apply` rejections and success writes | step 7 | TC `test_apply_rejections` (parametrised, one per code), `test_apply_success_writes_event` |
| AC-10 [invariant] | Promise kept / missed / open per the rules table | steps 7, 8 | TC `test_promise_status_kept_and_missed` |
| AC-11 [invariant] | `due_state`, queue order, five lanes, `new_flags_count`, current value + `changed` | steps 1, 6 | TC `test_queue_ordering`, `test_oversight_lanes_fixed_order`, `test_detail_current_value_changed`; TR unit tests |
| AC-12 [failure/refusal] | `set_followup`: no open case, unverified `on_record` refused, four fields stored, masked label | step 8 | TC `test_set_followup_rules` (**frozen security**) |
| AC-13 [negative] | No contact values in views or `case_events` | steps 1 (`mask`), 6, 7, 8 | TC `test_no_contact_values_in_views` (**frozen security**) |
| AC-14 [negative] | "Demo: recorded, not sent"; unclaimed → refused; no "sent you" wording | step 8 | TC `test_activity_recorded_not_sent` |
| AC-15 [invariant] | Eight headings, origins, sources ≥ 1, `not_generated`, quote substring, `attach_brief` upsert | steps 2, 3 | TB `test_eight_headings_in_order`, `test_extraction_none_marks_not_generated`, `test_quote_must_be_substring`, `test_wp7_brief_items`; TC `test_attach_brief_upserts` |
| AC-16 [negative] | Staff notes only in heading 3 or 7 with `lookup_log` sources | step 2 | TB `test_staff_notes_only_in_headings_3_or_7` |
| AC-17 [capture] | WF-2 records with correlation ids; "a handoff left no case" = 0 | steps 3, 4 | TH `test_wf2_records_present` |
| AC-18 [invariant] | `allowed_actions` = one pure function; listed iff accepted; representative example lists equal | steps 1, 7 | TC `test_allowed_actions_listed_iff_accepted`, `test_allowed_actions_match_representative_examples`, `test_allowed_actions_by_role`; table in Appendix B |
| AC-19 [invariant] | Every display value has one producer; matches the OpenAPI example for the same input; `source_ids` resolve | steps 1, 6 | TC `test_display_values_match_openapi_examples`, `test_every_brief_source_id_resolves` |
| AC-20 [negative] | Customer lines speak as "Customer", never "You" / a name | step 6 | TC `test_staff_conversation_customer_unnamed`, `test_customer_speaker_name` (**frozen security**) |
| AC-21 [invariant] | Live-chat conversation writes change neither version nor lifecycle | steps 6, 7 (no code reacts to conversation writes) | TC `test_conversation_writes_keep_case_version` |
| AC-22 [journey] | Extends J-6 and J-7; level `mock-tested`, *Blocked by* AEA-57, AEA-52 | step 9 | `uv run pytest -m journey tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py`; record `docs/testing/journeys/<date>-AEA-29.md` |
| AC-23 [invariant] | `detail` sets `events.last_event_id` in the same snapshot | **blocked-on UX session: OpenAPI amendment** (and the AEA-02b view type carrying it) | TC `test_detail_last_event_id_same_snapshot` is written and **skipped** with that reason; reported blocked, never passed |
| AC-24 [regression/context] | Area map A6 row, ICM row (if first A6 slice), code-design *Built*, contract gaps recorded against cases §5 | step 10 | `git diff --name-only main...HEAD` |

### 3b. Source-contract reconciliation (obligations the ACs do not spell out)

| # | Obligation | Governing source | In ticket | Disposition | Plan step / owner |
|---|---|---|---|---|---|
| O-1 | The case and demo **view types** (`QueueView`, `CaseDetail`, `OversightView`, `CaseAction`, `CaseActionRejected`, `FollowUpChoice`, `ActivityIn`, `Activity` and their nested parts) exist in `domain/` with OpenAPI field names | cases.md §5 "by name only", A-2; graph-core GRC-19 row *cases A-2* "Accepted (AEA-02 follow-up)"; AEA-02 plan §2.3 excludes them | named, not built | **blocked-on AEA-02b** (no such ticket exists yet; §8 R-1, Appendix A) | orchestrator cuts it; steps 6–8 wait for it |
| O-2 | `apply` must return the **wire** summary (with `allowed_actions`, `due_state`, `promise_status`), not DO-4's domain `CaseSummary` (which has none of those) | AC-18 ("every `CaseSummary` that … `apply` … return"); OpenAPI `CaseActionResponse.case` | implied | **added**: `apply(...) -> CaseSummaryView \| CaseActionRejected`; recorded in cases §5a | step 7; §8 R-2 |
| O-3 | `record_activity` must give the route both the activity and the updated case (`ActivityResponse {activity, case}`) and refuse with `CaseActionRejected` (CON-15 errors) | OpenAPI `recordContactActivity`; UI_CONTRACTS CON-15 | no | **added**: returns `ActivityResult \| CaseActionRejected` | step 8; §8 R-2 |
| O-4 | `set_followup` must refuse (`NOT_ALLOWED_IN_STATE` with `details.state` `no_open_case` / `not_verified`) | OpenAPI `saveFollowUp` 409; web.md §8 WEB-23 | AC-12 | in-ticket; return type `FollowUp \| CaseActionRejected` | step 8 |
| O-5 | `detail` of an unknown case must let the route answer 404 `CASE_NOT_FOUND` | OpenAPI `getCase` 404 | no | **added**: raises `CaseNotFound(case_ref)` (defined in `cases.py`) | step 6; §8 R-2 |
| O-6 | The `shift_ended` thread-stream row stores a `HandoffBlock` (web.md §14) built by the one block builder `ReplyComposer.handoff_block` (graph-core §13, `agent/`), which `services/` may not import | web.md §14; graph-core §13; DO-3 §2.1 | no | **added**: `CaseService(..., *, handoff_block: Callable[[HandoffResult], HandoffBlock \| LiveQueuedBlock] \| None = None)`; container (AEA-51) binds `composer.handoff_block`; `None` stores `"handoff": null` | step 5; §8 R-4 |
| O-7 | Heading 7 must show the staff-guidance **text**, but `lookup_log` stores only its sha256 and `BriefAssembler()` takes nothing | cases §5 (CAS-33, `result_seen=<text sha256>`); AC-7 | no | **added**: `BriefAssembler(staff_guidance: Mapping[PassageId, StaffGuidance] \| None = None)`; unknown id → item text `f"Staff guidance: {passage_id}"` | step 2; §8 R-4 |
| O-8 | "A Quote that is not an exact substring … is rejected" needs the thread's customer messages, which `attach_extraction(brief, extraction, check)` does not receive (the node's `check_quotes` already filters, graph-nodes §2–§3) | AC-15; graph-nodes §2 | AC-15 | **added**: optional keyword `customer_messages: Mapping[int, str] \| None = None`; when given, failing quotes are dropped and the heading marked trimmed | step 2; §8 R-4 |
| O-9 | `source_id` scheme shared by `BriefItem.source_ids` and `CaseSource.source_id`, recorded in cases §5 | AC-19 | yes | in-ticket: `source_id = f"src-{lookup_row.id}"`, `lookup_log_id = f"ll-{lookup_row.id}"`; only `lookup_log` sources become chips | steps 6, 10 |
| O-10 | Staff free text (reasons, outcomes, notes) and conversation text never carry a contact value into a view or a `case_event` | DO-6 WF-2/WF-4 ("No contact value in any `case_event` or event row"); AC-13 | partly | **added**: `mask(text) = redact(text, RedactionProfile.SONNET).text` on every staff free text before storing and on every customer-derived string in `detail` | steps 1, 6–8 |
| O-11 | `case_created` must not reach a wire stream it is not a type of | web.md §11 (`CHAT_EVENT_TYPES` filter); OpenAPI `CaseEvent` oneOf (no `case_created`) | no | **added**: `case_created` goes to the **thread** stream (CON-3 drops it by type); the case stream gets only `case_changed` and `chat_closed` from this ticket | steps 3, 5, 7 |
| O-12 | `DemoService` (AEA-30) does not exist on `main`; `HandoffService` needs only `presence(tx)` | DO-3 S-20 | no | private typing `Protocol` `_PresenceSource` in `handoff.py` (no runtime seam; AEA-30's class fits structurally) | step 4; §8 R-8 |
| O-13 | Retry on every trigger, not only safety | UI_CONTRACTS CON-4 "A case write that fails is retried once"; DO-4 §7 | AC-6 (safety) | **added** (same code path for all triggers) | step 4 |
| O-14 | `customer_id` stored on a case only for a **verified** identity (an unverified locate never names the customer to staff) | R-16; consolidated §9.5 | no | **added** | step 3 |
| O-15 | Email / general follow-up texts, the general destination label, and oversight alert lines other than `OVERSIGHT_OVERDUE` are not in `policy/texts.py` | data.md §2 (UX owns words); cases A-11 | no | **blocked-on AEA-03 follow-up** for those branches; they raise `NotImplementedError` naming it (async-safety rule 1); alerts list only `overdue` | step 8; §8 R-5 |
| O-16 | `register_cases()` container hunk | ticket *Agent handoff* | handoff only | **not edited here** (§8 R-3): wiring is AEA-51/52's, with the keys proposed there | — |
| O-17 | `case_write_failed` signal | graph-nodes §4 (emitter AEA-36) | AC-6 wording | other-ticket: **AEA-36** emits it from `CaseWriteFailed` | — |
| O-18 | DO-6 check "a handoff left no case" needs `cases.turn_id` = the request's `turn_id` | DO-6 line 237 | AC-17 | in-ticket | step 3 |
| O-19 | No `Promise(` constructor in `src/` outside `policy/handoff.py` | graph-core §10 (GRC-2) | — | in-ticket by construction; grep gate G-6 | §7 |
| O-20 | No `import sqlite3`, no SQL in `services/` | DO-3 §2.1 | — | in-ticket; grep gate G-7 | §7 |

### 3c. Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| Services behind CON-4, CON-5 (`HandoffService.open`, `CaseService.set_followup`) | WF-2 | yes (DO-6 line 77) | E-6; M-10…M-13, M-15; CAP-3 (AEA-51) |
| Services behind CON-11…13, 15, 17 | WF-4 | yes (DO-6 line 79) | M-13, M-27; CAP-4 (AEA-52) |
| Shift end (`convert_live_queued`) | WF-5 (staffing, AEA-30) | yes | R-30 |

No HTTP entry point is added here (AEA-42, 45, 51, 52 own them).

### 3d. Frozen tests (`risk::security`): the test-writer writes these **first**; the implementer must not edit them

The issue freezes AC-7 (staff-only half), AC-12, AC-13 and AC-20. Their verify paths name `tests/services/test_cases.py`
and `tests/services/test_handoff.py`, and the tamper check is per file, so **these four files are frozen whole**, with
every test §7.1 lists for them:

| Frozen file | Functions (exact names) | AC |
|---|---|---|
| `tests/services/_case_fixtures.py` | helpers only (§6) | — |
| `tests/services/_allowed_actions_table.py` | `TABLE`, `REPRESENTATIVE_EXAMPLES` (Appendix B) | AC-18 |
| `tests/services/test_handoff.py` | `test_open_writes_all_rows_in_one_transaction`, `test_failure_after_case_row_leaves_no_rows`, `test_second_open_returns_already_open`, `test_repeat_turn_is_idempotent`, `test_new_reason_raises_priority`, `test_con4_always_yields_case`, `test_promise_matches_table`, `test_fee_bearing_stores_both_dues`, `test_alert_for_p0_p1_and_fee_bearing`, `test_no_promise_text_parameter`, `test_safety_write_retried_once`, `test_safety_case_without_customer`, **`test_staff_guidance_attached_not_responded`**, **`test_staff_guidance_anchor_without_customer_text`**, `test_wf2_records_present`, `test_presence_read_inside_transaction` (plan-added) | AC-1…7, 17 |
| `tests/services/test_cases.py` | `test_unstaffed_never_live_queued`, `test_convert_live_queued`, `test_convert_joins_caller_transaction`, `test_apply_rejections`, `test_apply_success_writes_event`, `test_promise_status_kept_and_missed`, `test_queue_ordering`, `test_oversight_lanes_fixed_order`, `test_detail_current_value_changed`, **`test_set_followup_rules`**, **`test_no_contact_values_in_views`**, `test_activity_recorded_not_sent`, `test_attach_brief_upserts`, `test_allowed_actions_listed_iff_accepted`, `test_allowed_actions_match_representative_examples`, `test_allowed_actions_by_role`, `test_display_values_match_openapi_examples`, `test_every_brief_source_id_resolves`, **`test_staff_conversation_customer_unnamed`**, **`test_customer_speaker_name`**, `test_conversation_writes_keep_case_version`, `test_detail_last_event_id_same_snapshot` (skipped, AC-23) | AC-8…15, 18…21, 23 |

**Red for the right reason** before the implementer starts: `ModuleNotFoundError: No module named
'meridian.services.handoff'` / `'meridian.services.cases'`. The test-writer also runs `uv run pytest --collect-only -q`
(everything else still collects). What each test asserts is §7.1; the test-writer derives the code from it and from
§4–§6 (the shapes are fixed there). Keep each test file ≤ 500 lines by putting every builder in `_case_fixtures.py`.

---

## 4. Shared code to use

### 4.0 Find every name first (Step 0 does this; never define a domain type here)

The homes below are the blockers' plans. After they merge, confirm each with
`grep -rnE "^class <Name>\b|^<Name> *[:=]" src/meridian/` and import from the module that grep reports.

### 4.1 Imports (exact names, expected homes)

| Name | Expected module | Used in |
|---|---|---|
| `MeridianModel`, `ApiErrorCode`, `CaseRef`, `ThreadId`, `TurnId`, `CustomerId`, `InvoiceId`, `PassageId`, `EventId` (an `Annotated[int, Field(ge=0)]` alias, not a class), `SafetyKind` | `meridian.domain.common` | all |
| `StreamKey`, `CASE_STREAM_PREFIX`, `thread_stream`, `case_stream` | `meridian.adapters.sqlite.rows` (AEA-10 §4.3; RF-2) | cases |
| `HandoffReason`, `Priority`, `Presence`, `CaseState`, `Promise`, `FollowUp`, `CaseSummary`, `HandoffRequest`, `HandoffResult`, `Brief`, `BriefHeading`, `BriefItem`, `SourceRef`, `Quote`, `BriefExtraction`, `BRIEF_TITLES`, `BRIEF_KEYS`, `BRIEF_ORIGINS` | `meridian.domain.handoff` (the first six are defined in `domain.common` and explicitly re-exported here; RF-1) | all |
| `ActionKind`, `ActionKey`, `CompletedAction` | `meridian.domain.actions` | cases |
| `IdentityState`, `ConversationState`, `Controller` | `meridian.domain.state` (`IdentityState` is defined in `domain.identity` and re-exported here) | handoff, views |
| `TurnIds`, `TurnBudget`, `SpanHandle` | `meridian.domain.turn` | tests (`ctx()` builder) |
| `Speaker` | `meridian.domain.blocks` (exists; RF-3) | views (inside the view types) |
| `TurnContext`, `CheckResult` | `meridian.domain.turn` | handoff |
| `AccountResult`, `KnowledgeResult`, `SchedulingResult`, `StaffNote`, `ChangeRequestDraft` | `meridian.domain.specialists` | handoff (brief) |
| `LookupEntry`, `LookupRow` | `meridian.domain.tools` (**never** from an adapter, R-G-8) | handoff, views |
| `HandoffBlock`, `LiveQueuedBlock` | `meridian.domain.blocks` | cases (type of the injected callable) |
| `StaffRole`, `StaffActor`, `StaffPersona`, `actor_for`, `STAFF_PERSONAS`, `ASSIGNEE_ROLES`, `ROLE_ACTIONS`, `CUSTOMER_SPEAKER_NAME` | `meridian.domain.staff` | rules, cases, views, tests (`actor_for(StaffRole.REPRESENTATIVE)` builds a test actor) |
| `Clock`, `UnitOfWork`, `UnitOfWorkFactory` | `meridian.ports.runtime` | handoff, cases |
| `promise_for`, `case_due_at`, `due_label`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`, `PROMISE_TABLE` | `meridian.policy.handoff` (AEA-14 §4b) | rules, cases, handoff |
| `TEXTS`, `TextId`, `render`, `format_usd` | `meridian.policy.texts` (on `main`) | rules, cases, handoff |
| `redact`, `RedactionProfile` | `meridian.privacy.redact` (on `main`) | rules |
| `StaffGuidance` | `meridian.retrieval.manifest` (AEA-16) — import **only under `if TYPE_CHECKING:`** in `handoff.py` | handoff |
| `CaseRow`, `CaseEventRow`, `PromiseRow`, `FollowupRow`, `ActivityRow`, `ConversationRow`, `MessageRow`, `CustomerRow`, `InvoiceRow`, `AppointmentRow`, `StreamEvent`, `DemoStateRow` | `meridian.adapters.sqlite.rows` (AEA-10 §4.3; services → `adapters/sqlite` is allowed, DO-3 §2.1 arrow SVC → SQL) | cases, views |
| `DEMO_START`, `CLOSED_LIFECYCLES` | `meridian.adapters.sqlite.repos_cases` | tests only (`DEMO_START`), cases (`CLOSED_LIFECYCLES`) |
| the case view types of Appendix A | the module AEA-02b creates (proposed `meridian.domain.views`, one module for cases A-2's case and demo views, as AEA-30's plan R-1 also proposes; RF-4) — import from whatever module `grep -rn "^class QueueView" src/meridian/` reports | cases, views, tests |
| `FixedClock`, `WORKED_PAIRS_NOW` | `tests.fakes.clock` (AEA-11) | tests |
| `temp_sqlite`, `TempStore` | `tests.fixtures.sqlite` (AEA-10) | tests |

Shapes you rely on (copied from AEA-02 §4.6 / DO-4 §7; do not change):

```python
class CaseSummary(MeridianModel):          # domain; HandoffResult.case
    case_ref: CaseRef; reason: HandoffReason; priority: Priority; state: CaseState
    created_at: dt.datetime; promise: Promise; followup: FollowUp | None; version: int; seed: bool = False
    due_at: dt.datetime | None              # the CASE due (cases A-4)
class HandoffRequest(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; reason: HandoffReason; priority: Priority; rule_id: str
    trigger: Literal["gate", "escalation", "con4", "safety"]; identity: IdentityState
    change_request: ChangeRequestDraft | None = None; safety_kind: SafetyKind | None = None
class HandoffResult(MeridianModel):
    case: CaseSummary; created: bool; action: CompletedAction; alert: Literal["supervisor_now"] | None
class Promise(MeridianModel):              # fields only; ONLY policy/handoff.py constructs it (GRC-2)
    policy_row: str; text: str; due_at: dt.datetime | None; due_label: str | None
    extra_lines: tuple[str, ...] = (); live_queued: bool = False
class FollowUp(MeridianModel):             # = OpenAPI FollowUpView
    channel: Literal["email", "phone"]; destination_label: str; on_record: bool
    window: Literal["morning", "afternoon", "any"]; saved_line: str
class LookupEntry(MeridianModel):
    tool: str; record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]; result_seen: str
    message_id: int; turn_id: TurnId
class LookupRow(LookupEntry): id: int; thread_id: ThreadId
class StaffGuidance(MeridianModel):        # retrieval/manifest.py (data.md §3)
    passage_id: PassageId; file: Literal["internal/agent_discretion_notes.md"]
    section: str; version_label: str; text: str; text_sha256: str
# Brief, BriefHeading, BriefItem, SourceRef, Quote, BriefExtraction: DO-4 §7 exactly; Brief's validator enforces 8
# headings, numbers 1..8, titles = BRIEF_TITLES, keys = BRIEF_KEYS, origins = BRIEF_ORIGINS, heading 4 checked False,
# not_generated only on 2, 4, 7.
```

Repository calls this ticket makes (AEA-10 §4.3; **bodies are AEA-10's**; verify each signature in Step 0):

```python
tx.cases.cases.insert(row: CaseRow) -> None
tx.cases.cases.get(case_ref) -> CaseRow | None
tx.cases.cases.get_for_thread_open(thread_id) -> CaseRow | None
tx.cases.cases.list_open() -> tuple[CaseRow, ...]                     # non-closed, by created_at, case_ref
tx.cases.cases.list_for_customer(customer_id) -> tuple[CaseRow, ...]
tx.cases.cases.update_versioned(case_ref, expected_version, **changes) -> int | None   # new version or None
    # allowed keys: lifecycle, owner_role, owner_since, due_at, wake_up_at, priority, reason, resolved_at,
    #   queued_at, alert, customer_id, updated_at
tx.cases.case_events.append(event: CaseEventRow) -> int ; tx.cases.case_events.list_for_case(case_ref)
tx.cases.promises.insert(case_ref, promise, at) -> int                # status 'open'
tx.cases.promises.current(case_ref) -> PromiseRow | None ; .history(case_ref) -> tuple[PromiseRow, ...]
tx.cases.promises.set_status(case_ref, status, at, reason) -> bool    # updates the CURRENT row
tx.cases.followups.upsert(row: FollowupRow) ; .get(case_ref) -> FollowupRow | None
tx.cases.activities.insert(row: ActivityRow) -> int ; .list_for_case(case_ref)
tx.cases.briefs.upsert(brief, at) ; .get(case_ref) -> Brief | None
tx.cases.demo_state.get() -> DemoStateRow                              # .staffing
tx.cases.refs.next_case_ref() -> CaseRef                               # max(existing, seeds 0008) + 1
tx.core.actions.record(action: CompletedAction) -> CompletedAction ; .for_thread(thread_id)
tx.core.events.append(stream: StreamKey, event: StreamEvent) -> EventId ; .after(stream, last) ; .latest_id(stream)
tx.core.lookup_log.append(entry: LookupEntry) -> int ; .for_thread(thread_id) -> tuple[LookupRow, ...]
tx.core.messages.handoff_anchor(thread_id) -> int ; .all_for_thread(thread_id) -> tuple[MessageRow, ...]
tx.core.conversations.lookup(thread_id) -> ConversationRow | EndedThread | None
tx.core.conversations.set_live_state(thread_id, live_state, live_since) -> None
tx.core.reads.invoice(id) / .appointment(int) / .customer(id) / .identity_state(thread_id) / .new_flags_count()
tx.commit()                                                             # once; a second call is a no-op
```

Row shapes you build (AEA-10 §4.3, verbatim; build with keyword arguments):

```python
CaseRow(case_ref, thread_id, turn_id=None, customer_id=None, reason, priority, rule_id, trigger, lifecycle,
        owner_role=None, owner_since=None, due_at=None, wake_up_at=None, version=1, seed=False, safety_kind=None,
        change_request=None, alert=None, created_at, updated_at, resolved_at=None, queued_at=None)
CaseEventRow(id=None, case_ref, kind, key="", actor_role: "representative"|"supervisor"|"owner"|"ai"|"system",
             job_run_id=None, detail: dict[str, JsonValue] = {}, at)
FollowupRow(case_ref, thread_id, channel, destination_label, destination=None, on_record, window, saved_line, updated_at)
ActivityRow(id=None, case_ref, kind, outcome, note=None, actor_role: StaffRole, at)
StreamEvent(type: str (≤ 40), payload: dict[str, JsonValue] = {}, at)
```

### 4.2 What this ticket exports (exact; consumers rely on these names)

**`src/meridian/services/handoff.py`**

```python
__all__ = ["BriefAssembler", "CaseWriteFailed", "HandoffService", "TRIM_NOTE"]

TRIM_NOTE: Final = "Something here didn't match the record and was removed."
    # [Source: SCREEN_SPECS SCR-6 R6 line 317; OpenAPI getCase TRIMMED_STOP trim_note] staff copy

class CaseWriteFailed(Exception):
    """The case write failed twice (DO-1 §8.2). Carries no value: attempts and a cause code only."""
    attempts: int                                       # always 2
    cause: str                                          # always "write_error"
    def __init__(self, attempts: int = 2) -> None: ...  # message: "case write failed after 2 attempts"

class HandoffService:
    def __init__(self, uow: UnitOfWorkFactory, cases: CaseService, demo: _PresenceSource, clock: Clock,
                 staff_guidance: Mapping[HandoffReason, tuple[StaffGuidance, ...]] = MappingProxyType({})) -> None: ...
    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ...

class BriefAssembler:
    def __init__(self, staff_guidance: Mapping[PassageId, StaffGuidance] | None = None) -> None: ...
    def assemble(self, case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]) -> Brief: ...
    def attach_extraction(self, brief: Brief, extraction: BriefExtraction | None, check: CheckResult | None,
                          *, customer_messages: Mapping[int, str] | None = None) -> Brief: ...
```

**`src/meridian/services/cases.py`**

```python
__all__ = ["CaseNotFound", "CaseService"]

class CaseNotFound(LookupError):
    """detail() of an unknown reference. Holds the reference (a code, not customer data)."""
    case_ref: str
    def __init__(self, case_ref: str) -> None: ...     # message: f"no case {case_ref}"

class CaseService:
    def __init__(self, uow: UnitOfWorkFactory, clock: Clock, *,
                 handoff_block: Callable[[HandoffResult], HandoffBlock | LiveQueuedBlock] | None = None) -> None: ...
    def open_case(self, tx: UnitOfWork, req: HandoffRequest, promise: Promise, now: dt.datetime) -> HandoffResult: ...
    def attach_brief(self, case_ref: CaseRef, brief: Brief) -> None: ...
    def open_case_for_thread(self, thread_id: ThreadId) -> CaseSummary | None: ...
    def queue(self, role: StaffRole, now: dt.datetime) -> QueueView: ...
    def detail(self, case_ref: CaseRef, role: StaffRole, now: dt.datetime) -> CaseDetail: ...   # raises CaseNotFound
    def oversight(self, now: dt.datetime) -> OversightView: ...
    def apply(self, case_ref: CaseRef, action: CaseAction, actor: StaffActor, expected_version: int,
              now: dt.datetime) -> CaseSummaryView | CaseActionRejected: ...
    def set_followup(self, thread_id: ThreadId, choice: FollowUpChoice,
                     now: dt.datetime) -> FollowUp | CaseActionRejected: ...
    def record_activity(self, case_ref: CaseRef, activity: ActivityIn, actor: StaffActor,
                        now: dt.datetime) -> ActivityResult | CaseActionRejected: ...
    def convert_live_queued(self, now: dt.datetime, tx: UnitOfWork | None = None) -> int: ...
```

**`src/meridian/services/_case_rules.py`** (private module; pure; the names below are its whole public surface inside
the package, each with a docstring):

```python
LiveState = Literal["not_live", "queued", "joined", "handed_back", "closed"]
DueState = Literal["on_time", "due_soon", "overdue", "no_due_time"]
LaneName = Literal["p0_p1", "overdue", "due_soon", "unowned", "stuck_waiting"]
CON13_ACTIONS: Final[tuple[str, ...]] = ("claim", "release", "start", "wait", "resolve", "close_unresolved",
                                         "assign", "change_priority")
ACTION_ORDER: Final[tuple[str, ...]] = ("claim", "claim_and_join", "join_chat", "send_live_message", "hand_back",
    "close_chat", "start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "assign",
    "change_priority", "flag")
CLOSED: Final[frozenset[str]] = frozenset({"resolved", "closed_unresolved"})
OWNER_LIFECYCLES: Final[Mapping[str, frozenset[str]]]       # step 1.2
LANE_ORDER: Final[tuple[LaneName, ...]] = ("p0_p1", "overdue", "due_soon", "unowned", "stuck_waiting")
REASON_LABEL: Final[Mapping[HandoffReason, str]]            # step 1.6
SAFETY_KIND_LABEL: Final[Mapping[str, str]]
PRIORITY_WORD: Final[Mapping[Priority, str]]
LIFECYCLE_WORD: Final[Mapping[str, str]]
WINDOW_WORD: Final[Mapping[str, str]]
def state_allows(action: str, *, lifecycle: str, owner_role: StaffRole | None, live_state: LiveState,
                 staffing: Presence, actor_role: StaffRole) -> bool: ...
def actions_for(*, lifecycle: str, owner_role: StaffRole | None, live_state: LiveState, staffing: Presence,
                actor_role: StaffRole) -> tuple[str, ...]: ...
def con13_refusal(action: str, *, lifecycle: str, owner_role: StaffRole | None, owner_since: dt.datetime | None,
                  actor_role: StaffRole) -> tuple[ApiErrorCode, dict[str, JsonValue]] | None: ...
def due_state(case_due: dt.datetime | None, now: dt.datetime) -> DueState: ...
def queue_key(priority: Priority, state: DueState, case_due: dt.datetime | None, created_at: dt.datetime,
              case_ref: str) -> tuple[object, ...]: ...
def lane_for(priority: Priority, state: DueState, lifecycle: str, created_at: dt.datetime,
             wake_up_at: dt.datetime | None, now: dt.datetime) -> LaneName | None: ...
def reason_label(reason: HandoffReason, safety_kind: str | None = None) -> str: ...
def follow_up_short(channel: str | None, window: str | None) -> str | None: ...
def clock_text(at: dt.datetime) -> str: ...                 # "2:14 pm", Chicago
def age_label(created_at: dt.datetime, now: dt.datetime, *, queued_at: dt.datetime | None = None) -> str: ...
def case_due_label(case_due: dt.datetime | None, *, is_window_start: bool) -> str | None: ...
def identity_view(identity: IdentityState) -> tuple[str, str, str]: ...      # (wire status, line, demo_note)
def staff_name(actor_role: str) -> str: ...                 # persona name, or "System" for "ai" / "system"
def promise_status_after_resolve(promise_due: dt.datetime | None, now: dt.datetime) -> Literal["kept", "missed"]: ...
def promise_status_after_activity(outcome: str, promise_due: dt.datetime | None, now: dt.datetime,
                                  current: str) -> str: ...
def fill_promise_text(promise: Promise, case_ref: str) -> str: ...
def mask(text: str) -> str: ...                             # redact(text, RedactionProfile.SONNET).text
def staffing_labels(mode: Presence) -> tuple[str, str | None]: ...   # (label, banner)
```

**`src/meridian/services/_case_views.py`**: private builders called only by `cases.py` (step 6 lists them).

---

## 5. Steps

Build inside DO-3's boundary: `services/` → `domain/`, `policy/`, `privacy/`, `ports/`, `adapters/sqlite` (rows and
repos via `tx`) only. Never import `agent/`, `web/`, `sqlite3`, or another service module (the sibling services arrive
by injection). No new interface beyond the two private helper modules and the typing-only `_PresenceSource` (§8 R-8,
R-9). Each file: docstring first, `from __future__ import annotations`, `import datetime as dt` (AEA-02 rule 1),
absolute imports, one statement per line, no module-level instances other than immutable constants.

### Step 0 — preconditions (stop and report if any fails)

1. `cd` into the AEA-29 worktree; `export UV_LINK_MODE=hardlink`; `uv sync` (never copy a venv; no `node_modules`).
2. `git log --oneline -40 main` shows AEA-02, AEA-10, AEA-11, AEA-14, AEA-16 **and AEA-02b** (Appendix A) merged, and
   the frozen test files exist with the test-writer's commit. If AEA-02b is missing: stop, report
   `BLOCKED-ON AEA-02b`. If the frozen files are missing: stop, report it.
3. Confirm every §4.1 name and the repository signatures:
   ```bash
   grep -rnE "^class (CaseSummary|HandoffRequest|HandoffResult|Brief|BriefHeading|BriefItem|SourceRef|Quote|BriefExtraction|LookupEntry|LookupRow|ConversationState|TurnContext|CheckResult|StaffActor|StaffGuidance|HandoffBlock|LiveQueuedBlock|CaseRow|CaseEventRow|PromiseRow|FollowupRow|ActivityRow|StreamEvent|MessageRow|ConversationRow)\b|^(BRIEF_TITLES|BRIEF_KEYS|BRIEF_ORIGINS|ROLE_ACTIONS|CUSTOMER_SPEAKER_NAME|ASSIGNEE_ROLES|STAFF_PERSONAS|StreamKey|Presence|CaseState)\b" src/meridian/
   grep -nE "def (insert|get|get_for_thread_open|list_open|list_for_customer|update_versioned|append|list_for_case|current|history|set_status|upsert|next_case_ref|record|for_thread|handoff_anchor|all_for_thread|set_live_state|lookup|invoice|appointment|customer|identity_state|new_flags_count|latest_id|after)\(" src/meridian/adapters/sqlite/repos_core.py src/meridian/adapters/sqlite/repos_cases.py
   grep -n "def thread_stream\|def case_stream\|^StreamKey\|^CASE_STREAM_PREFIX" src/meridian/adapters/sqlite/rows.py
   grep -n "PROMISE_TABLE\|def promise_for\|def case_due_at\|def due_label\|DUE_SOON_WINDOW\|UNOWNED_AFTER" src/meridian/policy/handoff.py
   ```
   Then prove every import in one command (it must print `ok`; RF-8):
   ```bash
   uv run python -c "
   from meridian.domain.common import ApiErrorCode, CaseRef, ThreadId, TurnId, CustomerId, InvoiceId, PassageId, EventId, SafetyKind
   from meridian.domain.handoff import HandoffReason, Priority, Presence, CaseState, Promise, FollowUp, CaseSummary, HandoffRequest, HandoffResult, Brief, BriefHeading, BriefItem, SourceRef, Quote, BriefExtraction, BRIEF_TITLES, BRIEF_KEYS, BRIEF_ORIGINS
   from meridian.domain.actions import ActionKind, ActionKey, CompletedAction
   from meridian.domain.state import ConversationState, Controller, IdentityState
   from meridian.domain.turn import TurnContext, TurnIds, TurnBudget, SpanHandle, CheckResult
   from meridian.domain.specialists import AccountResult, KnowledgeResult, StaffNote, ChangeRequestDraft
   from meridian.domain.tools import LookupEntry, LookupRow
   from meridian.domain.blocks import HandoffBlock, LiveQueuedBlock, Speaker
   from meridian.domain.staff import StaffRole, StaffActor, actor_for, STAFF_PERSONAS, ASSIGNEE_ROLES, ROLE_ACTIONS, CUSTOMER_SPEAKER_NAME
   from meridian.ports.runtime import Clock, UnitOfWork, UnitOfWorkFactory
   from meridian.policy.handoff import promise_for, case_due_at, due_label, business_due, priority_for, DUE_SOON_WINDOW, UNOWNED_AFTER, PROMISE_TABLE, STAFF_GUIDANCE_FOR
   from meridian.policy.texts import TEXTS, TextId, render, format_usd
   from meridian.privacy.redact import redact, RedactionProfile
   from meridian.retrieval.manifest import StaffGuidance
   from meridian.adapters.sqlite.rows import StreamKey, thread_stream, case_stream, CaseRow, CaseEventRow, PromiseRow, FollowupRow, ActivityRow, StreamEvent, MessageRow, ConversationRow, CustomerRow, InvoiceRow, AppointmentRow, DemoStateRow
   from meridian.adapters.sqlite.repos_cases import DEMO_START, CLOSED_LIFECYCLES
   from tests.fakes.clock import FixedClock, WORKED_PAIRS_NOW
   from tests.fixtures.sqlite import temp_sqlite, TempStore
   assert len(HandoffReason) == 16 and CUSTOMER_SPEAKER_NAME == 'Customer' and ROLE_ACTIONS[StaffRole.OWNER] == frozenset()
   assert set(STAFF_GUIDANCE_FOR) == {HandoffReason.REFUND, HandoffReason.FEE_BEARING_CHANGE, HandoffReason.LATE_TECHNICIAN, HandoffReason.BILLING_DISPUTE, HandoffReason.COMPLAINT_OR_MANAGER}
   assert str(case_stream(CaseRef('MHC-C-0009'))) == 'case:MHC-C-0009'
   print('ok')"
   ```
   and, separately, the view types (`from <module grep reported> import QueueView, CaseDetail, OversightView,
   CaseSummaryView, CaseAction, CaseActionRejected, FollowUpChoice, ActivityIn, Activity, ActivityResult`).
   Use exactly the reported modules. If a name or method is missing or its signature differs from §4: stop and report
   `BLOCKED-ON <owner>` naming it. Never define it here.
4. Read the merged body of `update_versioned` (which value types it accepts: enum members or `.value`, aware
   datetimes). **Do not build stream keys** (RF-2): import `thread_stream` and `case_stream` from
   `meridian.adapters.sqlite.rows` and call them wherever this plan writes `thread_stream(…)` / `case_stream(…)`.

### Step 1 — `services/_case_rules.py` (pure; then `tests/unit/services/test_case_rules.py`)

Module docstring: "Pure case rules and staff display values (A6): allowed actions, due state, queue order, oversight
lanes, labels. No I/O, no clock read; every time is an argument." Private `_CHICAGO = ZoneInfo("America/Chicago")`.

1. **Allowed actions (one predicate, two users; the iff guarantee of AC-18 comes from this).**
   `OWNER_LIFECYCLES = MappingProxyType({"start": frozenset({"claimed", "waiting"}), "wait": frozenset({"claimed",
   "in_progress"}), "resolve": frozenset({"claimed", "in_progress"}), "close_unresolved": frozenset({"claimed",
   "in_progress"}), "release": frozenset({"claimed", "in_progress", "waiting"}), "log_call": frozenset({"claimed",
   "in_progress"}), "log_email": frozenset({"claimed", "in_progress"})})` — derived from the representative examples
   CLAIMED, WAITING, LIVE_JOINED (STF-18 marks the supervisor examples illustrative).
2. `state_allows(action, *, lifecycle, owner_role, live_state, staffing, actor_role)`; `mine = owner_role is not None
   and owner_role == actor_role`:
   - `claim` → `lifecycle in {"live_queued", "unassigned"}`
   - `claim_and_join` → `lifecycle == "live_queued" and live_state == "queued" and staffing == "simulated_on_shift"`
   - `join_chat` → `mine and live_state == "queued"` (staff.md §5 checks 2, 3, 7; a repeat join on `joined` is a
     no-op, not an acceptance)
   - `send_live_message`, `hand_back`, `close_chat` → `mine and live_state == "joined"` (check 8)
   - any key of `OWNER_LIFECYCLES` → `mine and lifecycle in OWNER_LIFECYCLES[action]`
   - `assign`, `change_priority` → `lifecycle not in CLOSED`
   - `flag` → `True`
   - anything else → `ValueError("unknown action")`
   *Invariant:* one place decides what the state allows.
3. `actions_for(...)` → `tuple(a for a in ACTION_ORDER if a in ROLE_ACTIONS[actor_role] and state_allows(a, ...))`.
   The owner gets `()` because `ROLE_ACTIONS[OWNER]` is empty. *Invariant:* list = table ∩ role, in table order.
4. `con13_refusal(action, *, lifecycle, owner_role, owner_since, actor_role)` (only for `CON13_ACTIONS`; anything else
   → `ValueError`), first match:
   1. `action not in ROLE_ACTIONS[actor_role]` → `(ROLE_NOT_ALLOWED, {"role": actor_role.value, "needs": [r.value for
      r in (StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR) if action in ROLE_ACTIONS[r]], "reason": "wrong_role"})`
   2. `lifecycle in CLOSED` → `(NOT_ALLOWED_IN_STATE, {"state": lifecycle, "needs": "open"})`
   3. `action == "claim"`: `lifecycle in {"claimed", "in_progress", "waiting"}` → `(CASE_ALREADY_CLAIMED, {"claimed_by":
      staff_name(owner_role.value), "claimed_at": owner_since.isoformat() if owner_since else None})`; else `None`
   4. `action in {"assign", "change_priority"}` → `None`
   5. owner-required actions: `owner_role is None` → `(NOT_ALLOWED_IN_STATE, {"state": lifecycle, "needs":
      "claimed"})`; `owner_role != actor_role` → `(CASE_ALREADY_CLAIMED, {"claimed_by": staff_name(owner_role.value),
      "claimed_at": …})`; `lifecycle not in OWNER_LIFECYCLES[action]` → `(NOT_ALLOWED_IN_STATE, {"state": lifecycle,
      "needs": " or ".join(sorted(OWNER_LIFECYCLES[action]))})`; else `None`.
   *Invariant:* for every CON-13 action, `con13_refusal(...) is None` **iff** `action in actions_for(...)` (the unit
   test proves it over Appendix B).
5. `due_state(case_due, now)`: `None` → `"no_due_time"`; `case_due < now` → `"overdue"`; `case_due - now <=
   DUE_SOON_WINDOW` → `"due_soon"`; else `"on_time"`. *Invariant:* overdue is a state, never a negative countdown.
6. Display maps (staff copy; each `Final`, `MappingProxyType`, with the source comment):
   - `PRIORITY_WORD = {P0: "Safety", P1: "Danger", P2: "Time-sensitive", P3: "Standard", P4: "Routine"}` [OpenAPI
     `Priority.word` enum, same order]
   - `REASON_LABEL` (every one of the 16 members; the examples' values where they exist [OpenAPI getQueue SEEDED,
     STAFFED_WITH_WAITING, getCase FEE_BEARING_CHANGE]; the rest plan decisions): safety "Safety report in chat",
     danger "Someone may be in danger", burning_unclear "Burning smell, risk unclear", burning_ruled_out "Burning
     smell, danger ruled out", customer_requested_person "Asked for a person", refund "Refund request", billing_dispute
     "Billing dispute", complaint_or_manager "Complaint or manager request", legal_or_chargeback "Legal or chargeback
     request", commercial "Commercial request", late_technician "Late technician", fee_bearing_change "Fee-bearing
     change request", membership_cancel "Membership cancellation", unsupported_action "Request the assistant can't
     complete", identity_unverified "Identity not confirmed", ai_failure "Assistant couldn't finish"
   - `SAFETY_KIND_LABEL = {"gas": "Gas smell reported in chat", "co": "CO alarm reported in chat",
     "sparks_smoke_flames": "Sparks, smoke or flames reported in chat", "burning_with_breaker": "Burning smell with a
     tripped breaker reported in chat"}` [OpenAPI SEEDED "Gas smell reported in chat"]
   - `reason_label(reason, safety_kind=None)`: `SAFETY_KIND_LABEL[safety_kind]` when `reason is SAFETY` and the kind is
     known, else `REASON_LABEL[reason]`. *Invariant:* never the enum value.
   - `LIFECYCLE_WORD = {"live_queued": "Live-queued", "unassigned": "Unassigned", "claimed": "Claimed", "in_progress":
     "In progress", "waiting": "Waiting", "resolved": "Resolved", "closed_unresolved": "Closed unresolved"}` [the UI's
     `LIFECYCLE_LABEL`, `apps/web/src/screens/scr06/caseText.ts`, read only]
   - `WINDOW_WORD = {"morning": "mornings", "afternoon": "afternoons", "any": "any time"}` [SCREEN_SPECS line 70
     chooser "Mornings / Afternoons / Any time", lower-cased as line 154's saved example; the UI's `settledSummary.ts`]
7. `follow_up_short(channel, window)`: `None` when `channel is None`; phone → `f"Phone · {WINDOW_WORD[window or
   'any']}"`; email → `"Email"` when `window in (None, "any")`, else `f"Email · {WINDOW_WORD[window]}"`. [SEEDED
   "Phone · mornings", "Email"]
8. `clock_text(at)`: `local = at.astimezone(_CHICAGO)`; `h = local.hour % 12 or 12`; `f"{h}:{local.minute:02d}
   {'am' if local.hour < 12 else 'pm'}"`. Naive `at` → `ValueError("at must be timezone-aware")`.
9. `age_label(created_at, now, *, queued_at=None)`: `queued_at is not None` → `f"Waiting since {clock_text(queued_at)}"`.
   Else `m = max(0, int((now - created_at).total_seconds() // 60))`; `m < 60` → `f"Open {m} min"`; `m < 1440` →
   `h, r = divmod(m, 60)`; `f"Open {h} h"` if `r == 0` else `f"Open {h} h {r} min"`; else `d, rest = divmod(m,
   1440)`; `h = rest // 60`; `unit = "day" if d == 1 else "days"`; `f"Open {d} {unit}"` if `h == 0` else
   `f"Open {d} {unit} {h} h"`. [SEEDED "Open 4 min", "Open 1 day 4 h"; STAFFED "Waiting since 2:14 pm"]
10. `case_due_label(case_due, *, is_window_start)`: `None` when `case_due is None`; `label = due_label(case_due)`
    (AEA-14; "Monday, October 19, 7:00 pm"); `label + ", the window start"` when `is_window_start`. [AC-19; the UI reads
    only the suffix and formats `due_at` itself: `apps/web/src/screens/scr06/caseText.ts` `dueHeadline`]
11. `identity_view(identity)` → `(status, line, demo_note)`; `demo_note = "Demo simulation"` always [OpenAPI DEFAULT].
    Status map: `verified` → `verified`; `code_sent` → `code_sent`; `located` → `code_sent` if `identity.codes_sent > 0`
    else `not_checked`; `not_verified` → `not_verified`; `locked` → `locked`; `not_checked` → `not_checked`. Lines (staff
    copy; the verified line is SCREEN_SPECS line 366's without the gendered "He", which the record cannot support):
    verified "The customer entered the code sent to the phone on file. (Demo simulation. Not real ID proof.)";
    code_sent "A code was sent to the phone on file. The customer has not entered it yet. (Demo simulation.)";
    not_checked "The customer has not confirmed who they are in this chat."; not_verified "The customer could not be
    confirmed in this chat."; locked "Code entry is locked after too many tries. (Demo simulation.)".
12. `staff_name(actor_role)`: `STAFF_PERSONAS[StaffRole(actor_role)].name` for a staff role; `"System"` for `"ai"` or
    `"system"`.
13. `queue_key(priority, state, case_due, created_at, case_ref)` → `(tier, overdue, missing_due, due_ts, created_ts,
    case_ref)` with `tier = 0 if P0, 1 if P1, else 2`; `overdue = 0 if state == "overdue" else 1`; `missing_due = 1 if
    case_due is None else 0`; `due_ts = case_due.timestamp() if case_due else 0.0`; `created_ts =
    created_at.timestamp()`. *Invariant:* P0, P1, then overdue, then due ascending, then `created_at`; no-due after dated.
14. `lane_for(priority, state, lifecycle, created_at, wake_up_at, now)`, first match: `priority in {P0, P1}` →
    `"p0_p1"`; `state == "overdue"` → `"overdue"`; `state == "due_soon"` → `"due_soon"`; `lifecycle == "unassigned" and
    now - created_at >= UNOWNED_AFTER` → `"unowned"`; `lifecycle == "waiting" and wake_up_at is not None and wake_up_at
    < now` → `"stuck_waiting"`; else `None`.
15. `promise_status_after_resolve(promise_due, now)`: `None` → `"kept"`; `now <= promise_due` → `"kept"`; else
    `"missed"`. `promise_status_after_activity(outcome, promise_due, now, current)`: when `current not in {"open",
    "changed"}` → `current`; `outcome in {"reached", "left_message"}` and (`promise_due is None` or `now <=
    promise_due`) → `"kept"`; else `current`.
16. `fill_promise_text(promise, case_ref)`: `promise.text` when it has no `{`; otherwise
    `promise.text.format(due_label=promise.due_label or "", case_ref=case_ref)` (only `R26.unstaffed` carries
    `{due_label}` and `{case_ref}`, AEA-14 step 2; nothing else is substituted). *Invariant:* the words are the table's.
17. `mask(text)` → `redact(text, RedactionProfile.SONNET).text` (cards, codes, emails, street lines, phones down to their
    last two digits; data.md §1). `staffing_labels(mode)`: nobody_online → `("Nobody online", None)`;
    simulated_on_shift → `("Simulated staff on shift (demo)", TEXTS[TextId.STAFFING_BANNER])` [OpenAPI `Staffing.label`].

Write `tests/unit/services/test_case_rules.py` (§7.2) and run it (§7.3 command A).

### Step 2 — `BriefAssembler` in `services/handoff.py` (then `tests/unit/services/test_brief_assembler.py`)

`BriefAssembler(staff_guidance=None)`: store `dict(staff_guidance or {})` keyed by `PassageId`. No I/O, no clock.

**`assemble(case, state, lookups) -> Brief`** — build eight `BriefHeading`s from `BRIEF_TITLES`, `BRIEF_KEYS`,
`BRIEF_ORIGINS` (index i → number i+1), `checked = number != 4`, `trimmed=False`, `trim_note=None`,
`not_generated=False`, status `"being_written"`, `assembled_at = state.turn_input.received_at`, `case_ref`,
`thread_id = state.thread_id`. Usable lookups: `rows = [r for r in lookups if r.result_seen != "failed" and not
r.result_seen.startswith("refused:")]`. Items (each `BriefItem(text, kind, sources=(…,), changed=False)`; **every item has
≥ 1 source; an item that cannot be sourced is not added**):

1. **H1 why** (state): one `fact`: `f"{reason_label(case.reason, safety)}. Priority {case.priority.value}
   ({PRIORITY_WORD[case.priority]})."` where `safety = state.gate.rules.safety.value` when `state.gate` and its
   `rules.safety` are set, else `None`. Source `SourceRef(kind="rule", ref=rule)` with `rule =
   state.escalation.rule_id` when `state.escalation` is not `None` and `state.escalation.reason == case.reason`, else
   `case.reason.value`.
2. **H3 know** (state): from `state.specialist_results`:
   - each `AccountResult` with `status == "read"`: each `InvoiceView` → `fact` `f"Invoice {inv.invoice_id}: total
     {format_usd(inv.total_cents)}, balance {format_usd(inv.balance_cents)}, due {inv.due_on.isoformat()}."`, source
     the first row whose `record_ids` contains `str(inv.invoice_id)`;
   - each `StaffNote` in those results → `fact` with `text = note.text`, source the first row whose `record_ids`
     contains `str(note.record_id)` (**staff-only text enters only here, as a `lookup_log`-sourced item**, AC-16);
   - each `KnowledgeResult` with `status == "answered"`: each `KnowledgePoint` → `fact` `point.text`, source the first
     row whose `passage_ids` contains `point.passage_id`.
3. **H5 ai_did** (state): for each `CompletedAction` in `state.settled.actions` (when `settled` is not `None`) of kind
   `verified` → "Confirmed the customer with a code (demo simulation).", `booked` → `f"Booked appointment
   {records['appointment']}."`, `moved` → `f"Moved appointment {records['appointment']}."`, `cancelled` →
   `f"Cancelled appointment {records['appointment']}."`, `change_request_sent` → `f"Recorded a change request for
   appointment {records['appointment']}; the appointment itself was not changed."`; skip `case_opened` and
   `followup_saved`. Kind `ai_action`, source `SourceRef(kind="action", ref=f"{a.kind.value}:{a.key.record_id}")`.
   Then for each usable row whose `tool != "staff_guidance"`: `ai_action` `f"Looked up {_row_title(row)}."`, source
   `lookup_log` `str(row.id)` (`_row_title`: the same rules as step 6.4's `title`).
4. **H6 told** (state, the only producer of promise words, AC-5): when `case.promise.text != ""`: one `told_customer`
   item `fill_promise_text(case.promise, case.case_ref)`, then one `told_customer` item per `extra_lines` entry; each
   with source `SourceRef(kind="policy_row", ref=case.promise.policy_row)`. Safety (`text == ""`) → no items.
5. **H7 decide** (origin extraction; guidance placed now so it shows while the brief is being written): for each usable
   row with `tool == "staff_guidance"`: `fact` with `text = self._guidance[pid].text` when `pid = row.passage_ids[0]`
   is known, else `f"Staff guidance: {pid}"`; source `SourceRef(kind="lookup_log", ref=str(row.id))` (AC-7).
6. **H8 who** (state): `status, line, _ = identity_view(state.identity)`; one `fact` `line` with source
   `SourceRef(kind="action", ref=f"verified:{key.record_id}")` of the `VERIFIED` action when there is one, else
   `SourceRef(kind="message", ref=str(state.turn_input.message_id))`; when verified and `state.identity.customer_id`:
   a second `fact` `f"Record {customer_id}."` with the same source. When `case.reason is SAFETY` and the identity is not
   verified: replace both with one `fact` "No account match needed for safety." [SCREEN_SPECS line 354] sourced on the
   message.
7. Headings 2 and 4 start with no items.

**`attach_extraction(brief, extraction, check, *, customer_messages=None) -> Brief`** (returns a new `Brief`;
`model_copy` per heading, then `Brief.model_validate` of the whole so the shape validator runs):

1. `extraction is None` → headings 2, 4, 7 `not_generated=True` (heading 7 keeps its guidance items: they are staff
   safety-relevant facts), status `"failed"`; return.
2. Quote filter: `ok(q) = customer_messages is None or (q.message_id in customer_messages and q.text in
   customer_messages[q.message_id])`. Dropped quotes mark their heading `trimmed=True`, `trim_note=TRIM_NOTE`.
3. H2 items: each kept `extraction.needs` quote → `claim` `q.text`, source `SourceRef(kind="message",
   ref=str(q.message_id))`. H4: each kept `extraction.claims` → `claim` the same way (heading stays `checked=False`).
4. H7 decision: `text = check.text if check is not None else extraction.open_decision`; strip; when non-empty, append
   (after the guidance items) one `decision` item with source `SourceRef(kind="message", ref=str(first kept need's
   message_id))`, or, when no need was kept, the first guidance row's `lookup_log` source; with no possible source the
   item is not added. When `check is not None and check.removals`: H7 `trimmed=True`, `trim_note=TRIM_NOTE`.
5. Status `"ready"`. **Heading 6 is never touched here** (AC-5: no extraction field reaches it).

Then write `tests/unit/services/test_brief_assembler.py` (§7.2) and run it.

### Step 3 — `CaseService` core in `services/cases.py`: `open_case`, the summary, `attach_brief`, `open_case_for_thread`

Constructor stores `uow`, `clock`, `handoff_block`. Imported: `thread_stream`, `case_stream` (step 0.4). Private helpers:
`_rank(p) = int(p.value[1])` (P0 → 0), `_actor_for(trigger) = "system" if trigger == "con4" else "ai"`.

**`open_case(tx, req, promise, now) -> HandoffResult`** (runs inside the caller's transaction; never commits):

1. `existing = tx.cases.cases.get_for_thread_open(req.thread_id)`. If not `None` → **already-open path** (4).
2. **New case**, in this order (AC-1's failure test injects after the `cases` insert, so the order matters):
   1. `ref = tx.cases.refs.next_case_ref()`; `window_start = req.change_request.window_start if req.change_request
      else None`; `case_due = case_due_at(req.reason, promise, window_start)`; `lifecycle = "live_queued" if
      promise.live_queued else "unassigned"`; `alert = "supervisor_now" if req.priority in {P0, P1} or req.reason is
      FEE_BEARING_CHANGE else None`; `customer_id = req.identity.customer_id if req.identity.status == "verified" else
      None` (O-14).
   2. `tx.cases.cases.insert(CaseRow(case_ref=ref, thread_id=req.thread_id, turn_id=req.turn_id,
      customer_id=customer_id, reason=req.reason, priority=req.priority, rule_id=req.rule_id, trigger=req.trigger,
      lifecycle=lifecycle, due_at=case_due, version=1, seed=False, safety_kind=req.safety_kind.value if
      req.safety_kind else None, change_request=req.change_request.model_dump(mode="json") if req.change_request else
      None, alert=alert, created_at=now, updated_at=now, queued_at=now if promise.live_queued else None))`.
      *Protects:* both dues stored (CAS-10): `cases.due_at` is the case due.
   3. `tx.cases.promises.insert(ref, promise, now)` — the `Promise` exactly as `promise_for` built it (its `due_at` is
      the customer promise). *Protects:* M-10 reads the table text.
   4. `tx.cases.case_events.append(CaseEventRow(case_ref=ref, kind="case_opened", actor_role=_actor_for(req.trigger),
      detail={"reason": req.reason.value, "priority": req.priority.value, "rule_id": req.rule_id, "trigger":
      req.trigger, "thread_id": str(req.thread_id), "turn_id": str(req.turn_id), "version": 1}, at=now))`.
   5. `action = tx.core.actions.record(CompletedAction(key=ActionKey(thread_id=req.thread_id, turn_id=req.turn_id,
      kind=ActionKind.CASE_OPENED, record_id=str(ref)), kind=ActionKind.CASE_OPENED, records={"case": str(ref)},
      at=now))`.
   6. `tx.core.events.append(thread_stream(req.thread_id), StreamEvent(type="case_created", payload={"case_ref":
      str(ref), "thread_id": str(req.thread_id), "turn_id": str(req.turn_id), "reason": req.reason.value, "priority":
      req.priority.value, "lifecycle": lifecycle}, at=now))` (O-11).
   7. When `promise.live_queued`: `tx.core.conversations.set_live_state(req.thread_id, "queued", now)`.
   8. Return `HandoffResult(case=self._summary(tx, ref), created=True, action=action, alert=alert)`.
3. `_summary(tx, ref) -> CaseSummary`: `row = tx.cases.cases.get(ref)`; `prow = tx.cases.promises.current(ref)`;
   `f = tx.cases.followups.get(ref)`; `CaseSummary(case_ref=row.case_ref, reason=row.reason, priority=row.priority,
   state=row.lifecycle, created_at=row.created_at, promise=prow.promise, followup=None if f is None else
   FollowUp(channel=f.channel, destination_label=f.destination_label, on_record=f.on_record, window=f.window or "any",
   saved_line=f.saved_line), version=row.version, seed=row.seed, due_at=row.due_at)`.
4. **Already-open path** (AC-2): `ref = existing.case_ref`;
   1. `seen = {existing.reason} | {HandoffReason(e.detail["reason"]) for e in tx.cases.case_events.list_for_case(ref)
      if e.kind == "reason_added"}`.
   2. When `req.reason not in seen`: `raise_to = req.priority if _rank(req.priority) < _rank(existing.priority) else
      None`; when `raise_to`: `v = tx.cases.cases.update_versioned(ref, existing.version, priority=raise_to,
      alert="supervisor_now" if raise_to in {P0, P1} else existing.alert, updated_at=now)` (`None` → raise
      `RuntimeError("case changed during handoff")`; impossible inside the write transaction, kept as a guard), then
      `tx.core.events.append(case_stream(ref), StreamEvent(type="case_changed", payload={"version": v, "lifecycle":
      existing.lifecycle}, at=now))`. Append **one** `CaseEventRow(kind="reason_added", actor_role=_actor_for(...),
      detail={"reason": req.reason.value, "priority": req.priority.value, "rule_id": req.rule_id, "trigger":
      req.trigger, "turn_id": str(req.turn_id), "priority_from": existing.priority.value, "priority_to":
      (raise_to or existing.priority).value, "version": v or existing.version}, at=now)`.
   3. Same reason (or the same `turn_id` repeated): **no write at all**.
   4. `action` = the `CASE_OPENED` row of `tx.core.actions.for_thread(req.thread_id)` whose `key.record_id ==
      str(ref)`; if none (a seed with no action row), build `CompletedAction(key=ActionKey(thread_id=req.thread_id,
      turn_id=existing.turn_id or req.turn_id, kind=CASE_OPENED, record_id=str(ref)), kind=CASE_OPENED,
      records={"case": str(ref)}, at=existing.created_at)` **without** recording it.
   5. `summary = self._summary(tx, ref)`; `alert = "supervisor_now" if summary.priority in {P0, P1} or req.reason is
      FEE_BEARING_CHANGE else None`; return `HandoffResult(case=summary, created=False, action=action, alert=alert)`.
   *Protects:* one open case per thread; no second `cases`, `actions` or guidance row; CON-4 never refused (M-15).
5. **`attach_brief(case_ref, brief)`**: `brief.case_ref != case_ref` → `ValueError("brief belongs to another case")`;
   `with self._uow(write=True) as tx:` unknown case → `ValueError("unknown case")`; `tx.cases.briefs.upsert(brief,
   self._clock.now())`; `tx.commit()`. *Protects:* one stored brief per case (graph-nodes §3).
6. **`open_case_for_thread(thread_id)`**: read-only `with self._uow() as tx:`; `row =
   tx.cases.cases.get_for_thread_open(thread_id)`; `None` → `None`; else `self._summary(tx, row.case_ref)`.

### Step 4 — `HandoffService` in `services/handoff.py`

```python
class _PresenceSource(Protocol):              # typing only (O-12); AEA-30's DemoService satisfies it structurally
    def presence(self, tx: UnitOfWork | None = None) -> Presence: ...
```

Import `StaffGuidance` and `CaseService` under `if TYPE_CHECKING:` (no runtime import of `services.cases` is needed;
`handoff.py` only calls methods). Constructor stores everything; `clock` is kept for the DO-4 signature (`ctx.now` is
the one reading per turn, graph-core §2).

**`open(req, ctx) -> HandoffResult`**:

1. `now = ctx.now`; `window_start = req.change_request.window_start if req.change_request else None`.
2. Attempt loop, for `attempt in (1, 2)`:
   ```python
   try:
       with self._uow(write=True) as tx:
           result = self._open_in(tx, req, now, window_start)
           tx.commit()
       return result
   except Exception as exc:          # noqa: BLE001 — a failed write of any kind is retried once (DO-1 §8.2)
       last = exc
   raise CaseWriteFailed(attempts=2) from last
   ```
   *Protects:* nothing half-written (the unit of work rolls back on exit), one retry, a typed failure the caller can
   act on (AEA-36 emits `case_write_failed`; AEA-42 maps it to 503 `HANDOFF_FAILED`). The exception message carries no
   value.
3. `_open_in(tx, req, now, window_start)`:
   1. `presence = self._demo.presence(tx)` — **inside** the transaction, so a shift end cannot interleave.
   2. `promise = promise_for(req.reason, presence, now, window_start)` — the only promise source (AC-5).
   3. `result = self._cases.open_case(tx, req, promise, now)`.
   4. When `result.created` and `self._staff_guidance.get(req.reason)`: `anchor =
      tx.core.messages.handoff_anchor(req.thread_id)` (once); for each `g` in order: `tx.core.lookup_log.append(
      LookupEntry(tool="staff_guidance", record_ids=(), passage_ids=(g.passage_id,), result_seen=g.text_sha256,
      message_id=anchor, turn_id=req.turn_id))`. *Protects:* guidance reaches staff only (a sha, never the text, in the
      row; never in state); idempotent per thread (only on creation).
   5. Return `result`. **Writes no `turns` row** (web.md §8).

### Step 5 — `convert_live_queued(now, tx=None)` (AC-8)

1. `tx is None` → `with self._uow(write=True) as own: n = self._convert(own, now); own.commit(); return n`. Else
   `return self._convert(tx, now)` and **never commit** the caller's transaction.
2. `_convert(tx, now)`: for each `row in tx.cases.cases.list_open()` with `row.lifecycle == "live_queued"`:
   1. `window_start = dt.datetime.fromisoformat(row.change_request["window_start"]) if row.change_request and
      row.change_request.get("window_start") else None`.
   2. `new = promise_for(row.reason, "nobody_online", now, window_start)`; `case_due = case_due_at(row.reason, new,
      window_start)`.
   3. Promise rows: `tx.cases.promises.set_status(ref, "changed", now, "shift_ended")` (marks the old row);
      `tx.cases.promises.insert(ref, new, now)`; `tx.cases.promises.set_status(ref, "changed", now, "shift_ended")`
      (the new current row shows status `changed`, rules table). *Protects:* history kept; status `changed`.
   4. `v = tx.cases.cases.update_versioned(ref, row.version, lifecycle="unassigned", due_at=case_due, updated_at=now)`
      (`None` → `RuntimeError` guard). Reference, `created_at`, `queued_at` untouched.
   5. `tx.core.conversations.set_live_state(row.thread_id, "not_live", None)`.
   6. `tx.cases.case_events.append(CaseEventRow(case_ref=ref, kind="converted", actor_role="system",
      detail={"reason": "shift_ended", "policy_row": new.policy_row, "promise_status": "changed", "version": v},
      at=now))`.
   7. `result = HandoffResult(case=self._summary(tx, ref), created=False, action=<the case_opened action as step 3.4.4>,
      alert=None)`; `block = self._handoff_block(result) if self._handoff_block else None`.
   8. Events: thread stream `StreamEvent(type="shift_ended", payload={"line": TEXTS[TextId.SHIFT_ENDED], "speaker":
      {"kind": "event", "display_name": None}, "case_ref": str(ref), "handoff": block.model_dump(mode="json") if block
      else None}, at=now)`; case stream `StreamEvent(type="chat_closed", payload={"reason": "shift_ended"}, at=now)`;
      case stream `StreamEvent(type="case_changed", payload={"version": v, "lifecycle": "unassigned"}, at=now)`.
   9. Count it. Return the count.

### Step 6 — views: `services/_case_views.py`, then `queue`, `detail`, `oversight` in `cases.py`

All three open **one read-only** unit of work (`with self._uow() as tx:`) and read everything inside it.
`staffing = tx.cases.demo_state.get().staffing`.

1. `queue_row(row, prow, f, customer, brief, now) -> QueueRow` (Appendix A fields): `reference=str(row.case_ref)`,
   `priority=PriorityView(level=row.priority, word=PRIORITY_WORD[row.priority])`, `reason=reason_label(row.reason,
   row.safety_kind)`, `customer_display_name=customer.name if customer else "No name given"` [SEEDED],
   `owner=staff_name(row.owner_role.value) if row.owner_role else None`, `created_at`, `due_at=row.due_at`,
   `due_label=case_due_label(row.due_at, is_window_start=_is_window_start(row))`, `due_state=due_state(row.due_at,
   now)`, `wake_up_at`, `lifecycle`, `follow_up_short=follow_up_short(f.channel if f else None, f.window if f else
   None)`, `seed`, `brief_status=brief.status if brief else "being_written"`, `queued_at=row.queued_at if
   row.lifecycle == "live_queued" else None`, `age_label=age_label(row.created_at, now, queued_at=row.queued_at if
   row.lifecycle == "live_queued" else None)`. `_is_window_start(row)`: `row.change_request` has `window_start` and
   `row.due_at == fromisoformat(it)`. **No phone, email or address field exists on a row** (AC-13).
2. `summary_view(row, prow, actor_role, live_state, staffing, now) -> CaseSummaryView`: `reference`, `reason`,
   `priority`, `lifecycle`, `owner`, `created_at`, `due_at`, `due_label`, `due_state`, `wake_up_at` as in 1;
   `promise_status=prow.status`; `seed`; `version=row.version`; `allowed_actions=list(actions_for(lifecycle=
   row.lifecycle, owner_role=row.owner_role, live_state=live_state, staffing=staffing, actor_role=actor_role))`.
   `live_state` = the conversation's `live_state` (`"not_live"` when the lookup is not a `ConversationRow`).
3. `queue(role, now)`: `rows = tx.cases.cases.list_open()`; `live = [r for r in rows if r.lifecycle == "live_queued"]`
   only when `staffing == "simulated_on_shift"`, else `[]`, sorted by `(0 if P0 else 1 if P1 else 2, queued_at or
   created_at, case_ref)`; `needs = [r for r in rows if r.lifecycle != "live_queued" and r.owner_role in (None,
   role)]` sorted by `queue_key`. Return `QueueView(as_of=now, staffing=StaffingView(mode=staffing,
   label=…, banner=…), live=[…], needs_my_action=[…])`.
4. **Sources** `case_sources(rows: Sequence[LookupRow], reads, brief) -> list[CaseSource]`; skip `failed` and
   `refused:*` rows; for each row `r`:
   - `source_id = f"src-{r.id}"`, `lookup_log_id = f"ll-{r.id}"` (O-9, recorded in cases §5a).
   - `tool == "staff_guidance"`: `audience="staff_only"`, `title="Agent discretion notes"`,
     `ref="internal/agent_discretion_notes.md"`, `version_date=None`, `version_label="undated"`, `snapshot =
     {"passage": <text of the brief item citing this row>}` or `{"passage_id": r.passage_ids[0]}` when no brief item
     cites it, `current = snapshot`, `changed_since=False`, `changed_note="No change since the snapshot"`,
     `current_unavailable=False`.
   - otherwise `audience="customer"`; `snapshot = json.loads(r.result_seen)` when that parses to a `dict`, else
     `{"seen": r.result_seen}`; `rid = r.record_ids[0] if r.record_ids else None`:
     - `rid` matches `^INV-[0-9]{6}$` → `inv = tx.core.reads.invoice(InvoiceId(rid))`; `title=f"Invoice {rid}"`,
       `ref=f"invoices/{rid}"`, `current = {"amount_cents": inv.amount_cents, "balance_cents": inv.balance_cents,
       "issued_date": inv.issued_date.isoformat(), "due_date": inv.due_date.isoformat(), "appointment_id":
       inv.appointment_id}`;
     - `^MHC-[0-9]{5}$` → `c = reads.customer(CustomerId(rid))`; `title="Membership record"`, `ref=f"customers/{rid}"`,
       `current = {"membership_tier": c.membership_tier, "membership_renewal_date": c.membership_renewal_date.isoformat()
       if c.membership_renewal_date else None}` (**never** name, phone, email or address: AC-13);
     - `^[0-9]+$` → `a = reads.appointment(int(rid))`; `title=f"Appointment {rid}"`, `ref=f"appointments/{rid}"`,
       `current = {"slot_date": a.slot_date.isoformat(), "window": a.window, "status": a.status, "service_type":
       a.service_type, "technician": a.technician}`;
     - no record id but `r.passage_ids` → `file = r.passage_ids[0].split("#")[0]`; `title = ref = file`; `current=None`;
     - a read that returns `None`, or an unknown id shape → `current=None`;
     - records: `version_date=None`, `version_label="live record"`; passages: `version_label =
       snapshot["version_label"]` when it is a `str`, else `"undated"`; `version_date` = `date.fromisoformat` of
       `snapshot["version_date"]` when it parses, else `None`;
     - `current is None` → `current_unavailable=True`, `changed_since=False`, `changed_note=None`; else
       `changed_since = any(k in current and current[k] != v for k, v in snapshot.items())`, `changed_note = "Changed
       since the AI saw it" if changed_since else "No change since the snapshot"`, `current_unavailable=False`.
   - Every `str` leaf of `snapshot` and `current` passes through `mask` (O-10).
5. **Brief view** `brief_view(brief, changed_ids)`: no stored brief → status `"being_written"` and eight headings with
   `items=[]` (BRIEF_BEING_WRITTEN example); else each heading → `BriefHeadingView(number, key, title, checked,
   items=[BriefItemView(text=mask(i.text), kind=i.kind, source_ids=[f"src-{s.ref}" for s in i.sources if s.kind ==
   "lookup_log"], changed=any(f"src-{s.ref}" in changed_ids for s in i.sources if s.kind == "lookup_log"))],
   trimmed, trim_note, not_generated)` (`origin` is internal and dropped). *Protects:* every chip resolves to a source
   of the same `CaseDetail` (the assembler cites only this thread's rows; `detail` lists every usable row).
6. **Conversation** from `tx.core.messages.all_for_thread(thread_id)`: `ChatLineView(message_id=str(m.id),
   speaker=Speaker(kind=m.role, display_name=CUSTOMER_SPEAKER_NAME if m.role == "customer" else "Meridian assistant"
   if m.role == "assistant" else STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name), at=m.at, text=mask(m.text))`.
   *Protects:* AC-20 ("Customer", never "You" or a name); AC-13 (contacts masked).
7. **Promise record**: `prow = promises.current(ref)`; `text = fill_promise_text(prow.promise, ref)`; `due_at`,
   `due_label = prow.promise.due_label`, `policy_row`, `status = prow.status`; `follow_up = None` or
   `{channel, destination_label, on_record, window}` from the followup row; `history = [{"at": h.status_at or
   h.created_at, "text": fill_promise_text(h.promise, ref), "reason": h.status_reason or "changed"} for h in
   promises.history(ref) if h.id != prow.id]`.
8. **Activities**: `Activity(activity_id=f"act-{a.id}", kind, outcome, note=mask(a.note) if a.note else None, at,
   by=STAFF_PERSONAS[a.actor_role].signature, label=TEXTS[TextId.RECORDED_NOT_SENT])` [CALL_REACHED "Riley (demo)"].
9. **`detail(case_ref, role, now)`**: `row = cases.get(case_ref)`; `None` → `raise CaseNotFound(str(case_ref))`.
   `conv = core.conversations.lookup(row.thread_id)`; `identity = core.reads.identity_state(row.thread_id)`;
   `lookups = core.lookup_log.for_thread(row.thread_id)`; `brief = cases.briefs.get(case_ref)`; sources per 4;
   `changed_ids = {s.source_id for s in sources if s.changed_since}`; `status, line, note = identity_view(identity)`.
   Return `CaseDetail(case=summary_view(row, prow, role, live_state, staffing, now), promise=…, brief=…,
   identity=CaseIdentityView(status=status, line=line, demo_note=note), sources=…, conversation=…, activities=…,
   live=LiveStateView(state=conv.live_state, since=conv.live_since, controller=conv.controller.kind),
   other_cases=[OtherCase(reference=str(o.case_ref), status=LIFECYCLE_WORD[o.lifecycle]) for o in
   cases.list_for_customer(row.customer_id) if o.case_ref != row.case_ref] if row.customer_id else [],
   agent_version=conv.agent_version, as_of=now)`. **AC-23 (`events.last_event_id`) is not built** (blocked).
10. **`oversight(now)`**: `rows = list_open()`; each row gets `lane = lane_for(...)`; lanes dict in `LANE_ORDER`, each
    `Lane(count=len(rows_in_lane), rows=[queue_row(...)…] sorted by queue_key)` (empty lanes kept); `alerts =
    [Alert(type="overdue", case_ref=str(r.case_ref), line=render(TextId.OVERSIGHT_OVERDUE, case_ref=str(r.case_ref)),
    at=r.due_at) for r in overdue lane rows]` (other alert types wait on AEA-03b, §8 R-5);
    `live_queue_length = count of live_queued rows when staffing == "simulated_on_shift" else 0`; `new_flags_count =
    tx.core.reads.new_flags_count()`; `as_of = demo_now = now`; `staffing` view as in 3.

### Step 7 — `apply(case_ref, action, actor, expected_version, now)` (AC-9, AC-10, AC-18)

One `with self._uow(write=True) as tx:`; on any rejection return `CaseActionRejected` **without** `tx.commit()` (the
exit rolls back; nothing changed). Order of checks:

1. `row = cases.get(case_ref)`; `None` → `CaseActionRejected(code=CASE_NOT_FOUND, field=None, constraint=None,
   details={"reference": str(case_ref)})`.
2. Role: `action.action not in ROLE_ACTIONS[actor.role]` → the `ROLE_NOT_ALLOWED` tuple from `con13_refusal`.
3. Required fields (strings stripped; blank = missing): `release`, `close_unresolved`, `assign`, `change_priority`
   without `reason` → `REASON_REQUIRED`, `field="reason"`, `constraint=f"required for {action.action}"`; `wait` without
   `wake_up_at` → `WAKE_UP_REQUIRED`, `field="wake_up_at"`, `constraint="required for wait"`; `wait` with
   `wake_up_at <= now` → `VALIDATION_ERROR`, `field="wake_up_at"`, `constraint="must be after the demo time"`;
   `resolve` without `outcome` → `OUTCOME_REQUIRED`, `field="outcome"`, `constraint="required for resolve"`; `assign`
   without `assignee` → `VALIDATION_ERROR`, `field="assignee"`, `constraint="required for assign"`; `change_priority`
   without `priority` → `VALIDATION_ERROR`, `field="priority"`, `constraint="required for change_priority"`.
4. Version: `expected_version != row.version` → `VERSION_CONFLICT`, `details={"changed_by": staff_name(e.actor_role),
   "changed_at": e.at.isoformat(), "current_version": row.version}` where `e` is the newest `case_events` row whose
   `detail.get("version") == row.version` (fallback: the `case_opened` row).
5. State: `con13_refusal(action.action, lifecycle=row.lifecycle, owner_role=row.owner_role,
   owner_since=row.owner_since, actor_role=actor.role)` → reject with its code and details.
6. Changes (all with `updated_at=now`): claim → `lifecycle="claimed", owner_role=actor.role, owner_since=now`; release
   → `lifecycle="unassigned", owner_role=None, owner_since=None, wake_up_at=None`; start → `lifecycle="in_progress",
   wake_up_at=None`; wait → `lifecycle="waiting", wake_up_at=action.wake_up_at`; resolve → `lifecycle="resolved",
   resolved_at=now, wake_up_at=None`; close_unresolved → `lifecycle="closed_unresolved", resolved_at=now,
   wake_up_at=None`; assign → `owner_role=ASSIGNEE_ROLES[action.assignee], owner_since=now, lifecycle="claimed",
   wake_up_at=None`; change_priority → `priority=action.priority`. `v = update_versioned(case_ref, expected_version,
   **changes)`; `None` → `VERSION_CONFLICT` as in 4 (re-read).
7. Resolve only: `prow = promises.current(case_ref)`; when `prow.status in {"open", "changed"}`: `new =
   promise_status_after_resolve(prow.promise.due_at, now)`; `promises.set_status(case_ref, new, now, "resolved")`.
8. **One** `case_events` row: `kind=f"action:{action.action}"`, `actor_role=actor.role.value`, `detail={"action":
   action.action, "version": v, "reason": mask(reason) or None, "outcome": mask(outcome) or None, "wake_up_at":
   iso or None, "assignee": ASSIGNEE_ROLES[...].value or None, "priority_from"/"priority_to" (change_priority),
   "promise_status_to": new or None}` (omit `None` keys).
9. `events.append(case_stream(case_ref), StreamEvent(type="case_changed", payload={"version": v, "lifecycle":
   <new lifecycle>}, at=now))`.
10. Build the `CaseSummaryView` for `actor.role` (step 6.2) from the re-read row; `tx.commit()`; return it.
*Protects:* listed ⇔ accepted (steps 1.2–1.4); every change one `case_event` with the actor role; version + 1;
ownership stored as a role, rendered through `STAFF_PERSONAS`.

### Step 8 — `set_followup` and `record_activity` (AC-12, AC-13, AC-14, AC-10)

**`set_followup(thread_id, choice, now)`** — one write unit of work:

1. `row = cases.get_for_thread_open(thread_id)`; `None` → `CaseActionRejected(NOT_ALLOWED_IN_STATE, None, None,
   {"state": "no_open_case"})`.
2. `identity = core.reads.identity_state(thread_id)`; `choice.destination == "on_record" and identity.status !=
   "verified"` → `CaseActionRejected(NOT_ALLOWED_IN_STATE, None, None, {"state": "not_verified"})` (WEB-23; R-27).
3. Label and line (customer-facing; only contract-given formats):
   - phone + on_record: `customer = reads.customer(row.customer_id)` (a verified case has one; `None` → reject as 2);
     `digits = re.sub(r"[^0-9]", "", customer.phone)[-2:]`; `destination_label = f"the number ending in {digits}"`
     [OpenAPI `FollowUpView.destination_label` "e.g. the number ending in 02"; UI_CONTRACTS CON-5];
     `saved_line = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window=WINDOW_WORD[choice.window])`.
   - email + on_record, and every `general` destination: the saved line and the general label are not in
     `policy/texts.py` → `raise NotImplementedError("follow-up text for email/general: blocked-on AEA-03 follow-up")`
     (O-15; the route turns it into a 500 until AEA-03b lands). When AEA-03b adds the ids, this branch uses them.
4. `followups.upsert(FollowupRow(case_ref=row.case_ref, thread_id=thread_id, channel=choice.channel,
   destination_label=destination_label, destination=choice.destination, on_record=choice.destination == "on_record",
   window=choice.window, saved_line=saved_line, updated_at=now))` — **`destination` stores the choice
   (`on_record` / `general`), never the phone or email** (AC-13).
5. One `case_events` row `kind="followup_saved"`, `actor_role="system"`, `detail={"channel": …, "on_record": …,
   "window": …}`. No version change (AC-21: follow-up is not a lifecycle change). `tx.commit()`.
6. Return `FollowUp(channel, destination_label, on_record, window, saved_line)`. *Protects:* nothing says "sent".

**`record_activity(case_ref, activity, actor, now)`** — one write unit of work:

1. Unknown case → `CASE_NOT_FOUND`. Role: `("log_call" if activity.kind == "call" else "log_email") not in
   ROLE_ACTIONS[actor.role]` → `ROLE_NOT_ALLOWED` (`needs: ["representative"]`). `activity.expected_version !=
   row.version` → `VERSION_CONFLICT` (step 7.4). `not state_allows(<key>, lifecycle=…, owner_role=…, live_state=…,
   staffing=…, actor_role=actor.role)` → `NOT_ALLOWED_IN_STATE` with `details={"state": row.lifecycle, "needs":
   "claimed"}` (an unclaimed case, AC-14) or `CASE_ALREADY_CLAIMED` when another role owns it.
2. `aid = activities.insert(ActivityRow(case_ref=case_ref, kind=activity.kind, outcome=activity.outcome,
   note=mask(activity.note) if activity.note else None, actor_role=actor.role, at=now))`.
3. Promise: `prow = promises.current(case_ref)`; `new = promise_status_after_activity(activity.outcome,
   prow.promise.due_at, now, prow.status)`; when `new != prow.status`: `promises.set_status(case_ref, new, now,
   f"activity:{activity.outcome}")`.
4. `v = update_versioned(case_ref, activity.expected_version, updated_at=now)` (CON-15 is a versioned change, AC-21);
   one `case_events` row `kind="activity"`, `actor_role=actor.role.value`, `detail={"kind", "outcome", "version": v,
   "promise_status_to": new if changed}` (no note text in the event); `case_changed` to the case stream.
5. Return `ActivityResult(activity=Activity(activity_id=f"act-{aid}", kind, outcome, note, at=now,
   by=actor.signature, label=TEXTS[TextId.RECORDED_NOT_SENT]), case=<summary view for actor.role>)`;
   `tx.commit()`. *Protects:* R-34 — the label on every activity; no "sent you" / "emailed you" / "called you" string.

### Step 9 — journeys (AC-22)

Write `tests/journeys/j6/test_aea_29.py` and `tests/journeys/j7/test_aea_29.py` (§7.2), each with
`pytestmark = pytest.mark.journey` and a docstring stating "Level today: mock-tested (real services on a temp SQLite
copy; no server). Integrated level blocked by AEA-57 (harness) and AEA-52 (integrated staff side)." Import the helpers
from `tests.services._case_fixtures` (read only). Run `uv run pytest -m journey tests/journeys/j6/test_aea_29.py
tests/journeys/j7/test_aea_29.py -q`.

### Step 10 — record and context (AC-22, AC-24)

1. `docs/testing/journeys/<YYYY-MM-DD>-AEA-29.md` with every `integrated-journeys.md` §4 field: Claim "J-6 (escalated
   case in queue and case view: eight headings, policy promise, accepted `allowed_actions`, resolving `source_ids`) and
   J-7 (live-chat conversation writes keep the case version), AEA-29"; Level `mock-tested`; Tested revision (commit
   SHA); Environment (`temp_sqlite()` copy of the issued DB, no server, no model, `FixedClock`); Command (§7.3 D, E);
   Result (pass/fail per file); Evidence location (the implementer's report); Remaining limitations (no HTTP, no
   browser, no real `LiveChatService`, AC-23 skipped); **Blocked by: AEA-57, AEA-52** (and the UX session's OpenAPI
   amendment for AC-23).
2. `.claude/reference/area-map.md` A6 row *Status* cell: append `services/cases.py, services/handoff.py built (AEA-29,
   <sha>)` to whatever is there (other A6 tickets append too; on a merge conflict keep the union).
3. `.claude/state/icm-progress.md`: only if no *Routes verified* row cites an A6 slice yet, replace row 18's evidence
   cell with `2026-10-2x: A6 → services/cases.py, handoff.py against tests/services/ (AEA-29, <sha>; N passed)` (≤ 400
   characters); otherwise change nothing.
4. `docs/design/code-design.md` §3 `**Built:**` line: append `` `services/cases.py`, `services/handoff.py` (AEA-29,
   `<sha>`) ``.
5. `docs/design/contracts/stage7/cases.md`: append after §5's rules table a subsection `### 5a. Built by AEA-29
   (2026-10-2x): the source_id scheme and recorded gaps` listing, one bullet each: the `source_id` / `lookup_log_id`
   scheme (O-9); `apply` → `CaseSummaryView | CaseActionRejected` (O-2); `record_activity` → `ActivityResult |
   CaseActionRejected` (O-3); `set_followup` → `FollowUp | CaseActionRejected` (O-4); `CaseNotFound` (O-5);
   `CaseService(..., handoff_block=…)` and the `shift_ended` payload keys `line`, `speaker`, `case_ref`, `handoff`
   (O-6); `BriefAssembler(staff_guidance=…)` (O-7); `attach_extraction(..., customer_messages=…)` (O-8);
   `case_created` on the thread stream (O-11); `customer_id` only when verified (O-14); `CaseWriteFailed`. Mark each
   `[Decided §7, engineering; AEA-29 plan]`. Edit nothing else in the file.
6. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in the files you own.

### Step 11 — gates and commits

1. Run §7.3 A–F in order; stop at the first red and fix only owned files.
2. Commit 1 (code and implementer tests):
   `git add src/meridian/services/_case_rules.py src/meridian/services/_case_views.py src/meridian/services/cases.py
   src/meridian/services/handoff.py tests/unit/services/test_case_rules.py tests/unit/services/test_brief_assembler.py
   tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py`, message `AEA-29: case service, handoff
   service and brief assembler` + body listing ACs met and AC-23 blocked, last line
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
3. Commit 2 (record and context): `git add docs/testing/journeys/<date>-AEA-29.md .claude/reference/area-map.md
   docs/design/code-design.md docs/design/contracts/stage7/cases.md` (+ `.claude/state/icm-progress.md` only if
   changed), message `AEA-29: journey record and context rows`, same last line.
4. Never `git add -A`; never push; never edit a frozen file (if a frozen test looks wrong, stop and report).
5. Report: gate outputs, both SHAs, the record path with Level and Blocked-by, the AC table with verified / blocked,
   and every §8 request still open.

---

## 6. Data and fixtures

Synthetic or issued only. **No phone number, email, code or card-like number literal in any test file or name**:
contact values are read from the issued DB at run time (`reads.customer(CustomerId("MHC-10002"))`), and their digits-only
form is derived with `re.sub`.

`tests/services/_case_fixtures.py` (frozen; the test-writer writes it against the merged AEA-02/10 shapes):

- `CHI = ZoneInfo("America/Chicago")`; `NOW = WORKED_PAIRS_NOW` (Fri 2026-10-16 10:00 Chicago = `DEMO_START`).
- `store()` → context manager over `temp_sqlite()` (the issued DB copy; first boot runs AEA-10's migrations).
- `new_thread(tx, *, customer_text: str | None = None, at=NOW, run_tag="live") -> tuple[ThreadId, int]`: inserts a
  `ConversationRow` (fresh `ThreadId(str(uuid4()))`, `demo_session="test"`, `agent_version="test-0"`, `started_at=at`),
  the greeting (`messages.append(thread, "assistant", TEXTS[TextId.GREETING], at)`), and, when given, the customer
  message; returns the thread id and the newest message id.
- `request(thread, reason, *, priority=None, trigger="escalation", turn=None, verified_customer=None,
  change_request=None, safety_kind=None) -> HandoffRequest`: `priority` defaults to `priority_for(reason)` (AEA-14);
  `rule_id=f"TEST.{reason.value}"`; `identity` = `IdentityState(status="verified", customer_id=…, masked_hint=None,
  code_expires_at=None, tries_left=3, codes_sent=1, verified_at=NOW)` when `verified_customer`, else `not_checked`.
- `ctx(thread, turn, now=NOW) -> TurnContext` (build `TurnIds`, a `TurnBudget`, `demo_session="test"`, and the span and
  intake values AEA-02's `TurnContext` requires: read its merged constructor).
- `StaffingDemo` (double honouring cases §6 `presence(tx)`): `presence(self, tx=None)` returns
  `tx.cases.demo_state.get().staffing` and records `tx` in `self.seen`.
- `FlakyUow(inner, *, fail_writes: int)`: wraps a factory; for the first `fail_writes` write units of work it replaces
  `tx.cases.promises.insert` on that unit of work with a function raising `RuntimeError("injected")` (so the `cases`
  insert has already run when it fails); counts `self.write_attempts`.
- `guidance(reason) -> StaffGuidance`: `StaffGuidance(passage_id=PassageId("internal/agent_discretion_notes.md#3"),
  file="internal/agent_discretion_notes.md", section="Agents may NOT", version_label="undated", text=
  STAFF_GUIDANCE_FOR[reason][0], text_sha256=hashlib.sha256(text.encode()).hexdigest())` (the prefix string from
  AEA-14 stands in for the passage text).
- `services(uow, *, guidance_map=None, handoff_block=None)` → `(CaseService, HandoffService, BriefAssembler,
  StaffingDemo)` built with `FixedClock(NOW)`.
- `seed_shaped(tx)` → the four cases of cases.md §7, inserted **directly** (refs MHC-C-0005…0008, `seed=True`,
  `run_tag="seed"` threads): 0005 refund P3, customer `MHC-10023` (Robert Chen), created Tue 2026-10-13 10:00, promise
  `promise_for(REFUND, "nobody_online", created_at)` (due Thu 10-15 19:00), follow-up email; 0006 complaint_or_manager
  P3, customer `MHC-10052` (Maria Patel), created Fri 09:14, `R26.unstaffed` due Mon 10-19 19:00, follow-up phone
  afternoons; 0007 billing_dispute P3, customer `MHC-10002` (Omar Patel), created Fri 09:24, same promise, follow-up
  phone + on_record + mornings, one customer message "Nobody told me about an after-hours fee. I want that taken
  off.", one lookup row `read_invoices` with `record_ids=("INV-204411",)`, `result_seen=json.dumps({"amount_cents":
  47800, "balance_cents": 47800})`, and a stored brief from the real `BriefAssembler` (status `ready`); 0008 safety P0
  (`safety_kind="gas"`), no customer, created Fri 09:56, `R26.safety_none`. Each with its `case_opened` action and
  event. (The worked-pairs customers MHC-10001…10004, 57204 are avoided for 0005/0006, as cases §7 says.)
- `display_case(tx)` → the MHC-C-0007 shape with the **OpenAPI example's own inputs** (AC-19 "for the same input"):
  `created_at = 2026-10-16T14:14-05:00`, read at `now = 14:20`, due Mon 10-19 19:00, follow-up phone mornings,
  verified identity, version as stored.
- `wp7(tx)` / `wp4(tx)` → the WP-7 thread and request (message text from the ticket) and the WP-4 request
  (`MHC-57204`, `ChangeRequestDraft(appointment_id=1, change="move", wanted_text="Monday morning",
  windows_shown=(), hours_before=2.0, window_start=2026-10-16 12:00 Chicago)`).
- `case_in_state(tx, *, lifecycle, owner_role, live_state, staffing) -> CaseRef`: a fresh thread + `CaseRow` inserted
  directly in that state (+ promise, `set_live_state`, `demo_state.set_staffing`); used by Appendix B tests.

`tests/services/_allowed_actions_table.py` (frozen): `TABLE` = Appendix B rows as tuples; `REPRESENTATIVE_EXAMPLES` =
`{"getCase.DEFAULT": ("unassigned", None, "not_live", "nobody_online", ["claim", "flag"]), "getCase.WAITING":
("waiting", REPRESENTATIVE, "not_live", "nobody_online", ["start", "release", "flag"]), "getCase.LIVE_JOINED":
("in_progress", REPRESENTATIVE, "joined", "simulated_on_shift", ["send_live_message", "hand_back", "close_chat",
"log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"]), "applyCaseAction.CLAIMED":
("claimed", REPRESENTATIVE, "not_live", "nobody_online", ["start", "log_call", "log_email", "wait", "resolve",
"close_unresolved", "release", "flag"])}` (copied from the OpenAPI examples).

---

## 7. Checks

### 7.1 Frozen tests (the test-writer writes; what each asserts)

`tests/services/test_handoff.py` — each test opens its own `store()`; FixedClock `NOW` unless stated.

- `test_open_writes_all_rows_in_one_transaction` (AC-1): WP-7 open → exactly one row for the thread in `cases`, one
  `case_events` (`case_opened`), one `promises`, one `actions` (`case_opened`), one thread-stream event `case_created`,
  one `lookup_log` (`staff_guidance`) — counted through the repositories.
- `test_failure_after_case_row_leaves_no_rows` (AC-1): `FlakyUow(fail_writes=2)` → `open` raises `CaseWriteFailed`;
  zero rows for the thread in each of those six tables.
- `test_second_open_returns_already_open` (AC-2): open refund, then open billing_dispute (P3) → `created=False`, same
  `case_ref`; one `cases` row; one `actions` row; one guidance row; exactly one extra `case_events` row
  (`reason_added`).
- `test_repeat_turn_is_idempotent` (AC-2): open, then the identical request → zero new rows in all tables.
- `test_new_reason_raises_priority` (AC-2): P3 refund then P2 late_technician → case P2, version + 1, one
  `case_changed`; a separate thread: P3 open then `safety` P0 → one case, priority P0, `alert == "supervisor_now"`.
- `test_con4_always_yields_case` (AC-2): `trigger="con4"` with `customer_requested_person` on a fresh thread →
  `created=True`; again on a thread with an open case → `created=False`, same ref; never an exception.
- `test_promise_matches_table` (AC-3): parametrised over every `HandoffReason` × (`nobody_online`,
  `simulated_on_shift`); set staffing via `demo_state.set_staffing`; fee-bearing and burning_ruled_out get WP-4's
  `change_request`. Stored `PromiseRow.promise == promise_for(reason, presence, NOW, window_start)`; when
  `promise.live_queued`: case `lifecycle == "live_queued"` and the conversation's `live_state == "queued"`; WP-7, WP-8
  (`membership_cancel`, P3), danger/burning_unclear (`OD4.danger_review`, due Mon 19:00), safety (`R26.safety_none`,
  `""`, `due_at None`) spot-checked with literal policy rows and due times.
- `test_fee_bearing_stores_both_dues` (AC-4): WP-4 → case P2, `CaseRow.due_at == 2026-10-16 12:00 Chicago`, promise
  `due_at == 2026-10-19 19:00 Chicago`, `alert == "supervisor_now"`.
- `test_alert_for_p0_p1_and_fee_bearing` (AC-4): for every reason (own thread, `priority_for`), `alert ==
  "supervisor_now"` iff priority in {P0, P1} or reason is `fee_bearing_change`.
- `test_no_promise_text_parameter` (AC-5): `inspect.signature` of every public method of `HandoffService`,
  `CaseService`, `BriefAssembler` (and their constructors): no parameter name contains `"text"`; every parameter whose
  name contains `"promise"` is annotated `Promise` (string annotation `"Promise"` accepted).
- `test_safety_write_retried_once` (AC-6): `FlakyUow(fail_writes=1)` safety request → returns `created=True`,
  `write_attempts == 2`, one `cases` row; `FlakyUow(fail_writes=2)` → `CaseWriteFailed` with `attempts == 2` and no
  value in `str(exc)`.
- `test_safety_case_without_customer` (AC-6): safety, identity `not_checked` → one P0 row, `customer_id is None`.
- **`test_staff_guidance_attached_not_responded`** (AC-7): for each of refund, fee_bearing_change, late_technician,
  billing_dispute, complaint_or_manager (own thread with a customer message; `guidance_map={reason:
  (guidance(reason),)}`): one `lookup_log` row with `tool == "staff_guidance"`, `passage_ids == (pid,)`,
  `result_seen == sha256`, `record_ids == ()`, `message_id == handoff_anchor(thread)`, `turn_id == req.turn_id`;
  `BriefAssembler(staff_guidance={pid: g}).assemble(result.case, state, lookups)` has a heading-7 item with text `g.text`
  and `sources == (SourceRef(kind="lookup_log", ref=str(row.id)),)`; `g.text` is absent from
  `result.model_dump_json()` and from `tx.core.settled_for(thread, NOW).model_dump_json()` (what the responder's
  inputs are built from) and from the stored `lookup_log` row's JSON. Other reasons write no guidance row.
- **`test_staff_guidance_anchor_without_customer_text`** (AC-7): a thread with only the greeting, `trigger="con4"`,
  refund guidance mapped → the row's `message_id` equals the greeting message id.
- `test_wf2_records_present` (AC-17): after WP-7, the `cases` row, the `case_opened` event, the promise (text,
  `policy_row`, `due_at`), the `actions` row (`ActionKey` thread/turn/kind/ref) and the `case_created` event payload all
  carry the request's `thread_id` and `turn_id`; insert a turns row for that `turn_id` (`core.turns.begin`), set its
  outcome to `handed_off` through `tx.connection.execute` (test-only), then the DO-6 query `SELECT COUNT(*) FROM turns
  t WHERE t.outcome = 'handed_off' AND NOT EXISTS (SELECT 1 FROM cases c WHERE c.turn_id = t.turn_id)` returns 0.
- `test_presence_read_inside_transaction` (plan-added): `StaffingDemo.seen` holds exactly one unit of work and its
  `committed` is `True` after `open` returns.

`tests/services/test_cases.py`:

- `test_unstaffed_never_live_queued` (AC-8): nobody online, every reason (own thread) → 0 cases with `live_queued`.
- `test_convert_live_queued` (AC-8): on shift, two person requests (live-queued) and one unassigned refund; at
  `NOW + 1h`, `convert_live_queued(now)` returns 2; both cases `unassigned`, same refs and `created_at`, version + 1;
  current promise `policy_row == "R26.unstaffed"`, status `changed`, due = `business_due(now, 1)`; history has the old
  staffed text; conversations `live_state == "not_live"`; each thread stream has one `shift_ended` (payload `line ==
  TEXTS[SHIFT_ENDED]`; `handoff` is the recording double's dump); each case stream has `chat_closed` with `reason ==
  "shift_ended"` and `case_changed`; the refund case untouched.
- `test_convert_joins_caller_transaction` (AC-8): inside `with uow(write=True) as tx:` call `convert_live_queued(now,
  tx)` → 2, leave without `commit` → afterwards both cases still `live_queued`; with `commit` → converted.
- `test_apply_rejections` (AC-9): parametrised, one case per code — stale version → `VERSION_CONFLICT` with
  `changed_by`, `changed_at`, `current_version`; claim on a supervisor-claimed case → `CASE_ALREADY_CLAIMED`
  (`claimed_by == "Demo supervisor"`); release / close_unresolved / assign / change_priority without reason →
  `REASON_REQUIRED`; wait without wake-up → `WAKE_UP_REQUIRED`; resolve without outcome → `OUTCOME_REQUIRED`; resolve on
  an unassigned case → `NOT_ALLOWED_IN_STATE` (`details == {"state": "unassigned", "needs": "claimed"}`); assign and
  change_priority by the representative → `ROLE_NOT_ALLOWED`. Each: the `CaseRow`, `case_events` and events of the case
  are unchanged.
- `test_apply_success_writes_event` (AC-9): claim (rep) → version + 1, one `action:claim` event with `actor_role ==
  "representative"`, one `case_changed`, summary `owner == "Riley"`; assign `riley` by the supervisor → `owner ==
  "Riley"`; assign `supervisor` → `"Demo supervisor"`; a staff reason containing the issued phone number is stored
  masked.
- `test_promise_status_kept_and_missed` (AC-10): six fresh claimed cases (Mon 19:00 promise); clocks `FixedClock(NOW)`
  and `FixedClock(NOW).advanced(timedelta(days=4))`: resolve before → `kept`; resolve after → `missed`; activity reached
  before → `kept`; left_message before → `kept`; no_answer → `open`; safety case (no due) resolved → `kept`; each change
  in a `case_events` row's `detail["promise_status_to"]`.
- `test_queue_ordering` (AC-11): `seed_shaped` at `NOW` → `needs_my_action` refs `[0008, 0005, 0006, 0007]`, `live ==
  []`; due states `no_due_time`, `overdue`, `on_time`, `on_time`.
- `test_oversight_lanes_fixed_order` (AC-11): lanes keys in `LANE_ORDER`; `p0_p1 == [0008]`, `overdue == [0005]`,
  `due_soon == []`, `unowned == [0006, 0007]`, `stuck_waiting == []`; counts equal; `new_flags_count == 0`.
- `test_detail_current_value_changed` (AC-11): detail of 0007 → source `src-<id>` `current` has the invoice values,
  `changed_since False`; then `UPDATE invoices SET balance_cents = 0 WHERE invoice_id = 'INV-204411'` (test-only, via
  `tx.connection`) → `changed_since True`, `changed_note == "Changed since the AI saw it"`, and every brief item citing it
  has `changed True`.
- **`test_set_followup_rules`** (AC-12): no open case → `NOT_ALLOWED_IN_STATE` `{"state": "no_open_case"}`; unverified
  thread with `on_record` → `NOT_ALLOWED_IN_STATE` `{"state": "not_verified"}` and no followup row; verified MHC-10002
  phone / on_record / morning → stored row `channel == "phone"`, `destination == "on_record"`, `on_record is True`,
  `window == "morning"`; returned `destination_label == "the number ending in 02"`, `saved_line == "Follow-up saved:
  phone call, the number ending in 02, mornings."`; neither the full phone (both forms) nor the email appears in the
  returned object's JSON or the stored row's JSON.
- **`test_no_contact_values_in_views`** (AC-13): `seed_shaped`; append to 0007's thread a customer message containing
  the issued phone and email (read at run time); claim with a reason containing the phone; serialise `queue`,
  `oversight`, `detail(0007)` (`model_dump_json`) → neither `phone`, `re.sub(r"\D", "", phone)` nor `email` is a
  substring; every `case_events` row of 0007 likewise; `detail` sources have `audience` `staff_only` only for
  `staff_guidance` rows; queue/oversight rows have no key named `phone`, `email` or `address`.
- `test_activity_recorded_not_sent` (AC-14): unclaimed → `NOT_ALLOWED_IN_STATE`; claimed (rep) call reached →
  `activity.label == "Demo: recorded, not sent"`, `by == "Riley (demo)"`; detail activities all carry the label; no
  returned string (set_followup and record_activity JSON) contains "sent you", "emailed you" or "called you".
- `test_attach_brief_upserts` (AC-15): attach a `being_written` brief, then a `ready` one → `briefs.get(ref).status ==
  "ready"` and exactly one brief row for the case.
- `test_allowed_actions_listed_iff_accepted` (AC-18): for each `TABLE` row × role: listed = `actions_for(...)` and the
  `detail(...)` summary's list (equal); every CON-13 action is sent to the real `apply` (each on its own
  `case_in_state` copy, valid reason / wake-up `now + 1 day` / outcome / assignee `"riley"` / priority `P2`, current
  version) → listed ⇒ not refused; not listed ⇒ refused with `ROLE_NOT_ALLOWED`, `NOT_ALLOWED_IN_STATE` or
  `CASE_ALREADY_CLAIMED`; live keys against a `LiveChatDouble` (staff.md §5: join accepts iff owner == actor and live
  `queued`; send/hand_back/close iff owner == actor and `joined`; representative only); `log_call`/`log_email` against
  the real `record_activity`; `flag` against a `FlagDouble` (representative, supervisor). 0 listed-but-refused, 0
  unlisted-but-accepted.
- `test_allowed_actions_match_representative_examples` (AC-18): each `REPRESENTATIVE_EXAMPLES` entry equals
  `actions_for(...)` **in order**.
- `test_allowed_actions_by_role` (AC-18, R-G-16): one case per lifecycle, each role: the owner's list is `[]`; the
  supervisor's never contains claim_and_join, join_chat, send_live_message, hand_back, close_chat, log_call, log_email;
  the representative's never contains assign, change_priority; `claim_and_join` only in T01 for the representative.
- `test_display_values_match_openapi_examples` (AC-19): `display_case` at 14:20 vs `getCase` DEFAULT and `getQueue`
  SEEDED (MHC-C-0007 row) field by field: `reason == "Billing dispute"`, `priority == {"level": "P3", "word":
  "Standard"}`, `owner is None`, `due_state == "on_time"`, `wake_up_at is None`, `promise_status == "open"`, `seed is
  True`, `allowed_actions == ["claim", "flag"]`, `customer_display_name == "Omar Patel"`, `follow_up_short == "Phone ·
  mornings"`, `queued_at is None`, `age_label == "Open 6 min"`, `identity.demo_note == "Demo simulation"`, every
  source's `version_label == "live record"` for records. **Listed differences with their reason** (a dict asserted
  exactly): `due_label` ("Monday, October 19, 7:00 pm": cases §3.1 `due_label` is the producer; the UI reads only the
  suffix), `version` (STF-18 illustrative), `identity.line` (no gendered "He"), `promise.text` / `policy_row` (the
  example's wording and row name are illustrative; ours is the table's).
- `test_every_brief_source_id_resolves` (AC-19): for the four seed-shaped cases, WP-4 and WP-7 (briefs attached):
  every id in every item's `source_ids` is a `source_id` of the same `CaseDetail`; count of unresolved ids `== 0`.
- **`test_staff_conversation_customer_unnamed`** (AC-20): 0007 detail → every customer line's `speaker ==
  {"kind": "customer", "display_name": "Customer"}`.
- **`test_customer_speaker_name`** (AC-20): no `display_name` value anywhere in the serialised `CaseDetail` is `"You"`,
  `"Omar"` or `"Omar Patel"`.
- `test_conversation_writes_keep_case_version` (AC-21): claimed case at version n; through the repositories make the
  writes `LiveChatService` makes (`set_controller(..., live_state="joined", ...)`, `messages.append(..., "representative",
  ...)`, `set_controller(ai, live_state="handed_back")`, then `live_state="closed"`) → `detail` version n, lifecycle
  unchanged, no new `case_changed` rows on the case stream.
- `test_detail_last_event_id_same_snapshot` (AC-23): `@pytest.mark.skip(reason="blocked-on UX session: OpenAPI
  amendment CaseDetail.events.last_event_id (and AEA-02b carrying it)")`; body as the AC states.

### 7.2 Tests the implementer writes with the code

`tests/unit/services/test_case_rules.py` (pure):
- `test_state_allows_and_refusal_agree` — over every Appendix B row × role × CON-13 action: `con13_refusal(...) is
  None` iff the action is in `actions_for(...)`.
- `test_actions_for_examples_and_owner` — the four `REPRESENTATIVE_EXAMPLES`; the owner always `()`.
- `test_due_state_boundaries` — None, now − 1 min (overdue), now + 4 h (due_soon), now + 4 h 1 min (on_time).
- `test_queue_key_order` — P0 no-due, P3 overdue, P3 due Mon 19:00 created 09:14, P3 same due created 09:24, P3 no due.
- `test_lane_for_first_match` — a P1 overdue case lands in `p0_p1`; unassigned 29 min → None, 30 min → `unowned`;
  waiting with wake-up passed → `stuck_waiting`.
- `test_labels` — `age_label` for 4 min, 36 min, 2 h, 1 day 4 h, 3 days, queued "Waiting since 2:14 pm";
  `follow_up_short`; `reason_label` for every `HandoffReason` (non-empty, never the enum value) and the gas kind;
  `case_due_label(..., is_window_start=True)` ends with ", the window start".
- `test_identity_view_statuses` — all six `IdentityState.status` values map into the five wire values.
- `test_mask_removes_contacts` — the issued MHC-10002 phone and email (read at run time from the issued DB file via
  `sqlite3` read-only in the test, or via `temp_sqlite`) are absent after `mask`.

`tests/unit/services/test_brief_assembler.py` (pure; build `ConversationState`, `CaseSummary` with
`model_validate`):
- `test_eight_headings_in_order` (AC-15): numbers 1–8, titles `BRIEF_TITLES`, origins, heading 4 `checked False`, every
  item has ≥ 1 source, status `being_written`.
- `test_extraction_none_marks_not_generated` (AC-15): headings 2, 4, 7 `not_generated True`; 1, 3, 5, 6, 8 not; status
  `failed`; heading 7 keeps its guidance item.
- `test_quote_must_be_substring` (AC-15): a need whose text is not in `customer_messages[message_id]` is absent from
  heading 2, which is `trimmed True` with `TRIM_NOTE`; a valid one is present.
- `test_wp7_brief_items` (AC-15, WP-7): heading 2 = the refund sentence; heading 4 = the two claims; heading 6 = the
  refund promise text and "I can't promise an outcome."; heading 7 = the guidance item.
- `test_heading_six_is_stored_promise` (AC-5): heading 6's first item text `== case.promise.text` for WP-7 (no
  placeholders) and `== fill_promise_text(promise, ref)` for an `R26.unstaffed` promise; an extraction whose
  `open_decision` and quotes contain "A representative will refund you" leaves heading 6 unchanged.
- `test_staff_notes_only_in_headings_3_or_7` (AC-16): an `AccountResult` with the INV-204411 `StaffNote`
  (`kind="billed_differs_from_schedule"`, text "Our fee schedule says after-hours dispatch is $149, not $144.") and a
  lookup row for INV-204411 → the note text appears only in heading 3 (or 7) items, each with a `lookup_log` source.

`tests/journeys/j6/test_aea_29.py` — `test_j6_escalated_case_reaches_queue_and_case_view`: WP-7 through
`HandoffService.open` (nobody online, guidance mapped), the real assembler + `attach_extraction` + `attach_brief`; then
`queue(REPRESENTATIVE)` lists the ref; `detail` has eight headings, `promise.policy_row == "R26.refund"` and its text
from `PROMISE_TABLE`, `allowed_actions == ["claim", "flag"]` and a `claim` sent to `apply` is accepted, every
`source_ids` entry resolves.

`tests/journeys/j7/test_aea_29.py` — `test_j7_live_takeover_keeps_case_version`: on shift, a `con4` person request →
`live_queued`; claim (rep) → version v; the live-chat conversation writes (join, representative message, hand back) via
the repositories → `detail` version v, lifecycle `claimed`, no `case_changed` after the claim's.

### 7.3 Commands (run inside the worktree; `export UV_LINK_MODE=hardlink` first; cheapest first, stop at first red)

Owned Python files: `F="src/meridian/services/_case_rules.py src/meridian/services/_case_views.py
src/meridian/services/cases.py src/meridian/services/handoff.py tests/unit/services/test_case_rules.py
tests/unit/services/test_brief_assembler.py tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py"`.

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| A | Unit (while iterating) | `uv run pytest tests/unit/services -q` | all pass |
| B | Lint and format | `uv run ruff check $F tests/services && uv run ruff format --check $F` | `All checks passed!`; no file would be reformatted (never reformat a frozen file) |
| C | Type check | `uv run mypy src/meridian/services tests/services tests/unit/services tests/journeys/j6 tests/journeys/j7` | `Success: no issues found` |
| D | Affected tests | `uv run pytest tests/services tests/unit/services tests/unit/test_import_direction.py tests/unit/policy -q` (add `--with pytest-xdist … -n 2` at most) | all pass; exactly 1 skipped (`test_detail_last_event_id_same_snapshot`) |
| E | Journeys | `uv run pytest -m journey tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py -q`, then `uv run python -m tests.journeys.affected --base main` | 2 passed; the affected command selects and passes them (and any other journey present) |
| F | Collect + greps | `uv run pytest --collect-only -q >/dev/null`; G-6 `grep -n "Promise(" src/meridian/services/*.py` → nothing; G-7 `grep -nE "import sqlite3|execute\(" src/meridian/services/*.py` → nothing; G-8 `grep -rnE "meridian\.(agent|web)" src/meridian/services/_case_rules.py src/meridian/services/_case_views.py src/meridian/services/cases.py src/meridian/services/handoff.py` → nothing; G-9 `grep -rnE "[0-9]{3}-[0-9]{3}-[0-9]{4}|@example\.com" tests/services tests/unit/services tests/journeys/j6 tests/journeys/j7` → nothing | as stated |

**Existing tests that must stay green:** `tests/unit/test_import_direction.py`, `tests/unit/web/test_container.py`
(unchanged file, unchanged hunk), AEA-14's `tests/unit/policy/test_handoff.py`, AEA-10's `tests/unit/adapters/sqlite/`
(not modified; run only if a failure points there). **Full suite:** not required (no shared fixture, settings,
dependency or cross-package seam changes; rule `build-loop-test-scope`).

---

## 8. Risks and requests

- **R-1 AEA-02b (request to the orchestrator; blocks steps 6–8 and the frozen `test_cases.py`).** cases A-2 and
  graph-core GRC-19 accepted "case and demo view types in `domain/`" as an AEA-02 follow-up, AEA-02's plan defers them
  (§2.3), and **no ticket in `docs/plans/tickets/` carries them**. AEA-29 (and AEA-45, 30, 43, 47 for the demo views)
  cannot build without them, and AEA-29 is on the critical path. **Ask:** cut `AEA-02b: case and demo view types`
  (pure types, `lane::build-loop`, wave 1½) now, from Appendix A, merged before AEA-29's test-writer starts. **AEA-30's
  plan (§8 R-1) asks for the same follow-up** (the four demo views, proposed module `domain/views.py`); cut **one**
  ticket covering both lists in one module, `src/meridian/domain/views.py` (RF-4). Still uncut at the 12:30 refresh. Fallback
  the contract allows (cases A-2 "plain dicts shaped as the OpenAPI schema") weakens every input type; it needs this
  plan revised, so it is not recommended.
- **R-2 Return types beyond DO-4 §13** (O-2…O-5): `apply` → `CaseSummaryView | CaseActionRejected`, `record_activity`
  → `ActivityResult | CaseActionRejected`, `set_followup` → `FollowUp | CaseActionRejected`, `detail` raises
  `CaseNotFound`. Recorded in cases §5a (step 10). **Request to AEA-45 / AEA-42 planners:** map
  `CaseActionRejected.code` to the HTTP status of the OpenAPI response (404, 403, 409, 422, 400), `CaseNotFound` → 404,
  `NotImplementedError` from `set_followup` → 500 until AEA-03b.
- **R-3 `register_cases()` is left a no-op (decided here, engineering).** Its objects depend on `demo_clock` and
  `demo_service` from AEA-30 (same wave) and `uow_factory` from AEA-10; the lazy container builds every provider at
  `build()`, so a merge of AEA-29 before AEA-30 would break every app start, and AEA-01's frozen
  `test_every_register_stub_present` asserts each hunk is a no-op (AEA-17/18/20 hit the same). **Ask:** AEA-51 (or a
  one-hunk follow-up after AEA-30 merges) fills it with `Key[CaseService]("case_service")` →
  `CaseService(c.get(Key("uow_factory")), c.get(Key("demo_clock")), handoff_block=composer.handoff_block)`,
  `Key[BriefAssembler]("brief_assembler")` → `BriefAssembler(staff_guidance={g.passage_id: g for g in
  load_staff_guidance(index_dir)})`, `Key[HandoffService]("handoff_service")` → `HandoffService(uow, cases,
  c.get(Key("demo_service")), demo_clock, staff_guidance=<STAFF_GUIDANCE_FOR prefixes resolved to passages; a prefix
  matching none fails start-up>)`. **AEA-30's planner** must not make `register_demo` require `case_service` before
  that lands.
- **R-4 Optional constructor / keyword additions** (O-6, O-7, O-8): `CaseService(handoff_block=…)`,
  `BriefAssembler(staff_guidance=…)`, `attach_extraction(customer_messages=…)`. All optional, so AEA-31's seeds and
  AEA-38's node compile unchanged. **Requests:** AEA-38 passes `customer_messages=shown` (defence in depth beside
  `check_quotes`); AEA-40 (`thread()`) and AEA-41 (CON-3) read the `shift_ended` payload keys `line`, `speaker`,
  `case_ref`, `handoff` (a `HandoffBlock` dump, `null` until AEA-51 binds the composer) and build `settled` at send
  time; AEA-46's case-stream sender may rely on this ticket writing only `case_changed` and `chat_closed` there.
- **R-5 AEA-03b (missing customer texts; request to the orchestrator).** `policy/texts.py` has no email follow-up saved
  line, no general-destination label or saved line, and no oversight lines for `p0_p1_created`, `unowned`,
  `due_soon`, `stuck_waiting` (cases A-11 expected "the CON-17 decision lines"). `shift_ended_with_queued` has a line
  for exactly one waiting customer (`OVERSIGHT_SHIFT_ENDED_ONE_WAITING`) but no plural form, and AEA-10's
  `DemoEventsRepo` offers no read of the latest staffing change, so it is not built here either (RF-6). Until they
  land: email and general follow-ups raise `NotImplementedError` (so an **unverified customer cannot save a follow-up**,
  and the default channel, email, fails), and oversight shows only `overdue` alerts. AC-12's test uses the phone path
  only. **Ask:** the UX session supplies the words; AEA-03b adds `TextId`s; a one-step follow-up on AEA-29 wires them.
- **R-6 AEA-36 retries too.** AEA-36's node retries `open` once and `open` retries once inside, so a persistent failure
  costs up to 4 write attempts (each rolled back, idempotent). Harmless; AEA-36 may drop its own retry.
- **R-7 Promise status after a shift end.** The converted case's current promise is `changed` (rules table), so
  AEA-30's scheduler (which marks `missed` only from `open`, `list_open_past`) never marks it missed; it is judged on
  resolve or a contact activity. **Note for AEA-30 / AEA-53 (M-13):** include `changed` where "open promise" is meant,
  or accept the rule as written.
- **R-8 `_PresenceSource`** is a private typing `Protocol` in `handoff.py` (no runtime seam): it lets `handoff.py` type
  the injected `DemoService` without importing a sibling that may merge later. Replace with a `TYPE_CHECKING` import of
  `DemoService` in a later change if wanted.
- **R-9 Two private modules** (`_case_rules.py`, `_case_views.py`) inside the A6 area keep each file under the
  600-line service cap (`code-structure.md`). Not new seams (no interface, imported only by `cases.py` / `handoff.py`);
  the area map row names them.
- **R-10 Brief for CON-4 cases (D-9).** CON-4 builds no brief, so such a case shows `brief_status: being_written`
  indefinitely. UX may want a distinct state; no contract change made here.
- **R-11 Staff copy owned here.** `REASON_LABEL`, identity lines, `TRIM_NOTE`, "No name given", "System", "Agent
  discretion notes", "No account match needed for safety." are staff-facing strings sourced from the OpenAPI examples
  and SCREEN_SPECS where they exist and decided here otherwise; the UX session may revise them in one place
  (`_case_rules.py`).
- **R-12 Shared context lines.** The area-map A6 row, the code-design `**Built:**` line and the ICM row are touched by
  AEA-14, 30, 31 too; expect textual merge conflicts — resolve as the union.
- **R-13 Disk.** `df -h /home` shows 83 % used (16 GB free). Each `temp_sqlite()` copies a 112 KB file; the iff test
  builds several hundred cases in one store — fine. Use `pytest -n 2` at most.
- **No signed-contract change and no D-4…D-15 reversal.** Nothing here edits `ui-contracts.openapi.yaml`,
  `UI_CONTRACTS.md` or `docs/ux/**`; AC-23 waits for the UX session's amendment; D-9 and D-14 are followed.

---

## 9. Readiness

**READY as a plan; BLOCKED-ON these prerequisites before the test-writer starts:**

| Prerequisite | Why (the import truly needed) | Status on `main` `16ca639` |
|---|---|---|
| AEA-02 | every domain type, `ports.runtime` | built in worktree `a33ce4c`, **not merged** |
| AEA-10 | `repos_core`, `repos_cases`, rows, `temp_sqlite` | not merged |
| AEA-11 | `tests/fakes/clock.py` `FixedClock` | not merged |
| AEA-14 | `policy/handoff.py` (`promise_for`, `case_due_at`, `due_label`, thresholds, `STAFF_GUIDANCE_FOR` in tests) | not merged |
| AEA-16 | `StaffGuidance` | not merged |
| **AEA-02b** (to be cut, §8 R-1; one ticket with AEA-30's four demo views) | the case view types (Appendix A) | **no ticket exists** (re-checked 12:30) |
| AEA-03b (to be cut, §8 R-5) | email / general follow-up texts, oversight alert lines | **no ticket exists**; only those branches wait |
| UX session OpenAPI amendment | AC-23 only (`CaseDetail.events.last_event_id`) | not landed (`CaseDetail` has no `events`; OpenAPI unchanged since `ca9ab5c`) |

`LiveChatService` (AEA-46), `DemoService` (AEA-30), `FlagService` (AEA-44), `ReplyComposer` (AEA-21) are used only as
doubles or injected callables; AEA-57 / AEA-52 are evidence-level blockers for AC-22's integrated level, not merge
blockers. No product decision is needed.

---

## Appendix A — the view types AEA-29 consumes (request for AEA-02b; field names = the OpenAPI property names)

Proposed module `src/meridian/domain/views.py`, shared with AEA-30's four demo views (RF-4; imports `common`, `handoff`,
`staff`, `blocks` only). Every class is a
`MeridianModel`; date-times `dt.datetime`, dates `dt.date`; nullable OpenAPI fields `X | None` and required.

| Type | OpenAPI schema | Notes |
|---|---|---|
| `StaffingView` | `Staffing` | `mode: Presence`, `label: str`, `banner: str \| None` (also AEA-30, 43) |
| `PriorityView` | `Priority` | `level: Priority`, `word: Literal["Safety", "Danger", "Time-sensitive", "Standard", "Routine"]` |
| `QueueRow` | `QueueRow` | 16 fields; `due_state` and `lifecycle` and `brief_status` as the enums |
| `QueueView` | `QueueResponse` | `as_of`, `staffing: StaffingView`, `live`, `needs_my_action` |
| `CaseSummaryView` | `CaseSummary` | 14 fields incl. `promise_status`, `version`, `allowed_actions: list[<the 16-value Literal>]` (named so it cannot be confused with DO-4's domain `CaseSummary`) |
| `BriefItemView`, `BriefHeadingView`, `BriefView` | `BriefItem`, `BriefHeading`, `Brief` | wire shapes: `source_ids: list[str]`, no `origin`; `BriefView.headings` exactly 8 |
| `CaseSource` | `CaseSource` | `snapshot: dict[str, JsonValue]`, `current: dict[str, JsonValue] \| None`, `audience: Literal["customer", "staff_only"]` |
| `Speaker` | `Speaker` | **already exists**: reuse `meridian.domain.blocks.Speaker` (same fields as the OpenAPI schema); do not define a second one (RF-3) |
| `ChatLineView` | `ChatLine` | named so it cannot be confused with `domain.state.ChatLine` |
| `Activity` | `Activity` | `label: Literal["Demo: recorded, not sent"]` |
| `PromiseFollowUp`, `PromiseHistoryItem`, `PromiseRecord` | `PromiseRecord` (+ its `follow_up` object and `history` item) | `follow_up: PromiseFollowUp \| None`; `window: str \| None` there |
| `LiveStateView` | `LiveState` | |
| `CaseIdentityView`, `OtherCase` | `CaseDetail.identity`, `CaseDetail.other_cases[]` | |
| `CaseDetail` | `CaseDetail` | + `events` once the UX amendment lands (AC-23) |
| `CaseAction` | `CaseActionRequest` | `action: Literal[8 values]`, `expected_version: int`, `reason`, `wake_up_at`, `outcome`, `assignee: Literal["riley", "supervisor"] \| None`, `priority: Priority \| None` (each defaulting to `None`) |
| `CaseActionRejected` | `ApiError.error` | `code: ApiErrorCode`, `field: str \| None`, `constraint: str \| None`, `details: dict[str, JsonValue] \| None` |
| `FollowUpChoice` | `FollowUpRequest` | `channel`, `destination: Literal["on_record", "general"]`, `window` |
| `ActivityIn` | `ActivityRequest` | `kind`, `outcome`, `note: str \| None = None`, `expected_version: int` |
| `ActivityResult` | `ActivityResponse` | `activity: Activity`, `case: CaseSummaryView` |
| `Alert`, `Lane`, `OversightLanes`, `OversightView` | `Alert`, `Lane`, `OversightResponse.lanes`, `OversightResponse` | |
| `ClockView`, `ClockAdvanced`, `StaffingChange`, `ResetDone` | cases A-2's demo views | not used by AEA-29; listed so one follow-up covers A-2 |

`FollowUp` (= `FollowUpView`) already exists in AEA-02.

## Appendix B — the `allowed_actions` table (AC-18; `actions_for` output; representative / supervisor / owner)

| Row | lifecycle | owner role | live state | staffing | representative | supervisor | owner |
|---|---|---|---|---|---|---|---|
| T01 | live_queued | — | queued | simulated_on_shift | claim, claim_and_join, flag | claim, assign, change_priority, flag | — |
| T02 | unassigned | — | not_live | nobody_online | claim, flag | claim, assign, change_priority, flag | — |
| T03 | claimed | representative | not_live | nobody_online | start, log_call, log_email, wait, resolve, close_unresolved, release, flag | assign, change_priority, flag | — |
| T04 | claimed | representative | queued | simulated_on_shift | join_chat, start, log_call, log_email, wait, resolve, close_unresolved, release, flag | assign, change_priority, flag | — |
| T05 | claimed | representative | joined | simulated_on_shift | send_live_message, hand_back, close_chat, start, log_call, log_email, wait, resolve, close_unresolved, release, flag | assign, change_priority, flag | — |
| T06 | claimed | representative | handed_back | simulated_on_shift | start, log_call, log_email, wait, resolve, close_unresolved, release, flag | assign, change_priority, flag | — |
| T07 | claimed | representative | closed | simulated_on_shift | start, log_call, log_email, wait, resolve, close_unresolved, release, flag | assign, change_priority, flag | — |
| T08 | in_progress | representative | not_live | nobody_online | log_call, log_email, wait, resolve, close_unresolved, release, flag | assign, change_priority, flag | — |
| T09 | in_progress | representative | joined | simulated_on_shift | send_live_message, hand_back, close_chat, log_call, log_email, wait, resolve, close_unresolved, release, flag | assign, change_priority, flag | — |
| T10 | waiting | representative | not_live | nobody_online | start, release, flag | assign, change_priority, flag | — |
| T11 | claimed | supervisor | not_live | nobody_online | flag | start, wait, resolve, close_unresolved, release, assign, change_priority, flag | — |
| T12 | in_progress | supervisor | not_live | nobody_online | flag | wait, resolve, close_unresolved, release, assign, change_priority, flag | — |
| T13 | waiting | supervisor | not_live | nobody_online | flag | start, release, assign, change_priority, flag | — |
| T14 | resolved | representative | not_live | nobody_online | flag | flag | — |
| T15 | closed_unresolved | supervisor | not_live | nobody_online | flag | flag | — |
| T16 | unassigned | — | not_live | simulated_on_shift | claim, flag | claim, assign, change_priority, flag | — |

Checks against the signed examples: T02 = `getCase` DEFAULT `[claim, flag]`; T03 = `applyCaseAction` CLAIMED and
`recordContactActivity` CALL_REACHED; T10 = `getCase` WAITING `[start, release, flag]`; T09 = `getCase` LIVE_JOINED
(exact order); T14 = RESOLVED `[flag]`. The supervisor examples ASSIGNED and PRIORITY_CHANGED disagree with each other
and are not used (STF-18, R-W-13).
