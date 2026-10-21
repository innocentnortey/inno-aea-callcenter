# Plan — [AEA-29] cases and handoff: case service, handoff service, brief

**Status:** planned — **READY**, with two preconditions the orchestrator clears before the implementer starts (§9):
the test-writer amends two frozen-test defects (F-1, F-2, §3d), and the implementer merges `main` into the AEA-29 branch
(Step 0). AC-23 alone stays `blocked-on UX session: OpenAPI amendment`.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/29 (body identical to
`docs/plans/tickets/AEA-29.md`; checked 2026-10-21, no comments) · **Wave:** 2 · **Lane:** build-loop · **Risk:**
`risk::security` (frozen tests first; `security-privacy-agent` at the wave merge)
**Base revision:** committed `main` `29ca543` (AEA-02, 02b, 03, 04, 05, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 26,
31, 32, 33, 41, 42, 44, 46, 47, 48, 49, 57, 59 merged). The primary checkout is mid-merge of AEA-17 (staged files,
conflict markers in its working copy of `area-map.md`); this plan was checked against `git show HEAD:<path>` only.
**Frozen tests:** branch `aea-29-aea-29-cases-handoff` at `7c60f77` (worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-29`), four files, written by `test-writer-agent` from the previous
version of this plan. Read line by line for this refresh (§3d).
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (written 11:01 UTC, refreshed 12:30 UTC, refreshed again
~16:00 UTC against `29ca543` and the frozen tests) · **Implementer:** fanout-implementer (Sonnet).

---

## Refresh log

### Earlier refresh (12:30 UTC), still holds

RF-1 defining modules (`HandoffReason`, `Priority`, `Presence`, `CaseState`, `Promise`, `FollowUp`, `SafetyKind` live in
`domain.common`; `domain.handoff` re-exports the first six); RF-2 stream keys are AEA-10's `thread_stream` / `case_stream`
in `adapters.sqlite.rows`; RF-3 `Speaker` exists in `domain.blocks`; RF-5 AC-23 blocked; RF-6 email/general follow-up
texts missing from `policy/texts.py`; RF-8 one-shot import check in Step 0; RF-9 every repository signature. All
re-verified on `29ca543` with an import check (every name in §4.1 resolves) and by reading `repos_cases.py`,
`repos_cases_state.py`, `repos_core.py`, `repos_core_aux.py`, `rows.py`, `policy/handoff.py`, `policy/texts.py`.

### This refresh (~16:00 UTC, `main` `29ca543`)

| # | Change | Evidence |
|---|---|---|
| RF-10 | **AEA-02b merged: every view type exists in `meridian.domain.views`.** The old blocker R-1 and Appendix A are closed. Differences from the old Appendix A that matter: sequences are tuples; `CaseAction.expected_version: int` is **required** (the `apply(..., expected_version, ...)` parameter still decides; see Step 7); `allowed_actions: tuple[AllowedAction, ...]`; `AllowedAction`, `CaseActionName`, `DueState`, `BriefStatus`, `PromiseStatus` are exported `Literal` aliases. | `git show 5305d57`; `src/meridian/domain/views.py` (377 lines) |
| RF-11 | **The frozen tests exist** (`7c60f77`). Their branch predates AEA-02b and AEA-21, so Step 0 merges `main` into it. Two defects need a test-writer amendment before the implementer starts: **F-1** (`_DIFFERENCES` wrongly lists `promise.text`) and **F-2** (`guidance()` gives every reason the same passage id). Everything else in them matches this plan. | §3d |
| RF-12 | **`register_cases` is filled by this ticket** (reverses old R-3). AEA-01's `test_every_register_stub_present` skips any hunk whose docstring no longer says "No-op until"; AEA-51's plan reads `deps.CASE_SERVICE`, `deps.HANDOFF_SERVICE` and `Key("brief_assembler")` from this hunk and marks the staff-guidance resolution "other-ticket: AEA-29's `register_cases` hunk" (its line 196). Siblings (AEA-30's clock and `DemoService`, AEA-51's composer) are reached through forwarders that raise `RuntimeError("not bound: <key>")`, the pattern `register_staff_live` and `register_person_request` already use. | `tests/unit/web/test_container.py` lines 64–83; `AEA-51.md` lines 196, 494; `container.py` lines 640–690 |
| RF-13 | **The `shift_ended` row must carry `handoff` and `settled`.** AEA-41's CON-3 encoder sends the stored payload unchanged (`web/schemas/events.py` `chat_event_data`), and OpenAPI `EvShiftEnded` requires `speaker`, `line`, `handoff`, `settled`. The frozen tests pin `CaseService(uow, clock, handoff_block=...)`, so a second optional callable `settled_view=` is added; the container binds both to AEA-21's `ReplyComposer.handoff_block` / `.settled_view`. The payload drops the old plan's `case_ref` key (not in the schema). | OpenAPI `components.schemas.EvShiftEnded`; `agent/nodes/compose.py` lines 297, 319 |
| RF-14 | **Staff-guidance text is shown only when its hash matches the logged row.** `BriefAssembler` uses a `StaffGuidance` for a `lookup_log` row only when `g.text_sha256 == row.result_seen`; otherwise the item reads `Staff guidance: <passage id>`. The brief can then never show a passage other than the one logged. | cases §5 (CAS-33 `result_seen=<text sha256>`) |
| RF-15 | **`lookup_log.result_seen` has three formats on `main`:** JSON (the frozen fixture), `key=value` text (AEA-31's seed: `INV-204411 amount_cents=47800 balance_cents=47800`; kb_search: `below_floor=false; <pid>=0.812`), and `failed` / `refused:<code>` (dispatch). `parse_seen` (Step 1.18) reads all three. | `services/reset.py` line 267; `agent/tools/knowledge.py` line 109; `agent/tools/dispatch.py` line 414 |
| RF-16 | **Identity on the case view reads "verified" when the case carries a customer.** O-14 stores `cases.customer_id` only for a verified request, and seed threads (AEA-31) and the frozen `display_case` write no `identity_threads` row. `set_followup` keeps the strict thread check (WEB-23). | `repos_core_aux.py` `identity_state`; frozen `test_display_values_match_openapi_examples` asserts `identity.status == "verified"` |
| RF-17 | **AEA-31's first-boot seed will start running this ticket's `BriefAssembler()` on every real app start**: `register_reset.first_boot` seeds as soon as `meridian.services.handoff` imports. So the implementer adds a test of the real `seed_demo` with the real assembler, and runs the full suite once before the final commit (§7, rule `build-loop-test-scope`: code now executed on every app start). Tests built with `full_app` suppress starters, so AEA-46's tests that insert their own `MHC-C-0007` are not affected; the contract driver already expects the seed (`seeded_case_ref`). | `container.py` lines 437–495; `tests/api/web_shell_support.py` lines 414–431; `tests/contract/openapi_driver.py` lines 208–216 |
| RF-18 | **Real `LiveChatService` (AEA-46) and `FlagService` (AEA-44) are on `main`.** The J-7 journey drives the real `LiveChatService` (via `tests/services/live_chat_support.new_service`). The frozen AC-18 test keeps its live double (frozen). | `services/live_chat.py`; `services/staff.py` |
| RF-19 | **Journey level.** AEA-57 has landed; the integrated level is now blocked by AEA-30 (demo clock and `DemoService` unbound: login and CON-4 fail), AEA-45 (`getQueue`/`getCase` routes) and AEA-52. | resume note wave-2 finding 1; `container.py` |
| RF-20 | **Context-upkeep pattern changed:** each slice now appends its own ICM *Routes verified* row and marks its code-design tree rows `built AEA-NN <sha>`. The area map has the A6 row twice (wave-2 finding 9, a `lane::direct` ticket): edit the first copy only. | `HEAD:.claude/state/icm-progress.md`, `HEAD:docs/design/code-design.md` lines 258–271, `HEAD:.claude/reference/area-map.md` lines 31–32 |
| RF-21 | **AC-23 still blocked:** OpenAPI `CaseDetail` has no `events`, and `views.CaseDetail` says "no `events` until the UX amendment". | `python3 -c "yaml…CaseDetail.properties"` |
| RF-22 | **Email / general follow-up texts are still missing** (the `aea-03b-history-texts` branch adds only two history texts). Old R-5 stands. | `git diff main...aea-03b-history-texts -- src/meridian/policy/texts.py` |

---

## 1. Goal and sources

### Goal

> **US-14:** As a **homeowner** whose request needs a person, I need a reference number, the exact promise (who gets back
> to me and by when), and a choice of email or phone and a time window, so that I know what happens next and never repeat
> my story.
>
> **US-19:** As a **representative**, I need an eight-heading brief that keeps facts and customer claims apart, the
> pertinent sources (what the AI saw and the current value), the promise with the follow-up preference beside it, and the
> full chat one click away, so that I can act without re-asking the customer.

This ticket builds the **services**: no route, no SQL, no model call. It also fills its one container hunk.

- `src/meridian/services/handoff.py`:
  - `HandoffService`: one write transaction covering presence → promise → case, case event, promise row,
    `actions(case_opened)`, `events(case_created)` and the staff-guidance `lookup_log` rows.
  - `BriefAssembler`: the pure eight-heading brief.
  - `resolve_staff_guidance`: the pure prefix-to-passage resolver.
  - `CaseWriteFailed`.
- `src/meridian/services/cases.py`: `CaseService` with every DO-4 §13 method, plus `CaseNotFound`.
- Two private helper modules in the A6 area (old R-9): `services/_case_rules.py` (pure rules and display values) and
  `services/_case_views.py` (turns rows into the `domain.views` types). Each file stays under the 600-line service cap.
- `src/meridian/web/container.py`: the `register_cases` hunk only.

**Concretely (the worked pair WP-7, demo clock Fri 2026-10-16 10:00 Chicago, nobody online):**

| Input | Output |
|---|---|
| `HandoffService.open(HandoffRequest(reason=refund, priority=P3, trigger="escalation", …), ctx)` for "I want a full refund on the repair. It didn't fix anything and I had to call another company." (seeds MHC-C-0005…0008 present) | One new case `MHC-C-0009`, P3, lifecycle `unassigned`.<br>Stored promise: `policy_row="R26.refund"`, text "A representative will get to your refund request within 2 business days.", `extra_lines=("I can't promise an outcome.",)`.<br>`promises.due_at` = `cases.due_at` = Tue 2026-10-20 19:00 Chicago; `due_label` "Tuesday, October 20, 7:00 pm".<br>One `actions` row (`case_opened`), one `case_events` row (`case_opened`), one `events` row (`case_created`) on the thread stream; `alert=None`.<br>One `lookup_log` row with `tool="staff_guidance"` and `result_seen` = the sha256 of "Issue refunds of any kind.", anchored on the refund message. |
| `BriefAssembler.assemble(case, state, lookups)`, then `attach_extraction(brief, extraction, None, customer_messages=…)` with needs = the refund sentence and claims = "It didn't fix anything", "I had to call another company" | Heading 2 quotes the refund sentence. Heading 4 holds the two claims (`checked=False`). Heading 6 holds the promise text and its extra line. Heading 7 holds the staff-guidance item with `source.kind="lookup_log"`. |
| `open` again for the same thread | `created=False`, `MHC-C-0009`; no new `cases`, `actions` or `lookup_log` row |

### Context

Wave 2, critical path (AEA-02 → 10 → 29 → 51). Who owns what this ticket uses:
- AEA-10: the storage it writes through.
- AEA-14: the promise and priority rules.
- AEA-02 and AEA-02b: the types.
- AEA-11: the clock fake.
- AEA-16: `StaffGuidance`.
- AEA-31: the seed that will call `BriefAssembler()`.
- AEA-21: `ReplyComposer`, reached only through the container forwarder.

Siblings not on `main`, used only as doubles or forwarders: `DemoService` (AEA-30) and the `reply_composer` key
(AEA-51). Merged consumers that already call these services through doubles or `Any`:
- AEA-42: `PersonRequestService` and the CON-5 route.
- AEA-46: `LiveChatService`.
- AEA-21: the `GraphDeps` aliases.

Decisions D-4…D-15 are all taken as recommended (`docs/plans/stage7-signoff.md`). D-9 (CON-4 builds no brief) and D-14
(CAS-16 option A, GRC-3 option A) apply here, and nothing in this plan departs from them.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-29.md` | AC-1…AC-24, WP-7, owned files, must-not list, frozen ACs (AC-7 staff-only half, AC-12, AC-13, AC-20) |
| Cases addendum (wins over DO-4) | `docs/design/contracts/stage7/cases.md` §1.1–§1.2, §3.1–§3.3, §5 (constructors, rules table, `STAFF_GUIDANCE_FOR`, "the container resolves each prefix … a prefix that matches none fails start-up"), §6 (`presence(tx)`), §7 (seed set), A-2 (view types) | every signature in §4; the rules table; both dues |
| DO-4 | `docs/design/contracts/internal-components.md` §1, §5, §7, §13, §16 | method names; one transaction |
| Staff addendum | `stage7/staff.md` §1, §5, §7, §12 | `allowed_actions`; "Customer" speaker; AC-21 |
| Graph addenda | `stage7/graph-nodes.md` §2–§4; `stage7/graph-core.md` §2, §13 | brief inputs; `ReplyComposer` is the one block builder |
| Web addendum | `stage7/web.md` §8, §11, §14 | CON-4/CON-5 calls; stream types; `shift_ended` history reads the stored `handoff` |
| Data addendum | `stage7/data.md` §1–§3, §8a | `redact` profiles; `TEXTS`; `StaffGuidance`; `FixedClock` |
| Signed wire contract (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` (`QueueResponse`, `CaseSummary`, `CaseDetail`, `CaseSource`, `PromiseRecord`, `Activity*`, `Alert`, `Lane`, `OversightResponse`, `EvShiftEnded`, `CeCaseChanged`, `CeChatClosed`; examples `getQueue` SEEDED, `getCase` DEFAULT/WAITING/LIVE_JOINED, `applyCaseAction` CLAIMED/errors); `UI_CONTRACTS.md` CON-4, 5, 11…13, 15, 17 | field names; error codes and details; example values AC-19 compares |
| Code on `main` | `domain/{common,handoff,views,staff,state,actions,blocks,turn,tools,identity,specialists}.py`; `adapters/sqlite/{rows,repos_cases,repos_cases_state,repos_core,repos_core_aux}.py`; `policy/{handoff,texts}.py`; `privacy/redact.py`; `retrieval/{manifest,ingest}.py`; `services/{reset,live_chat,person_request,staff}.py`; `web/{container,deps}.py`, `web/routes/handoff.py`, `web/schemas/{events,staff_live,handoff}.py`; `agent/nodes/compose.py`, `agent/context.py` | §4 copies from them |
| Frozen tests | branch `aea-29-aea-29-cases-handoff` `7c60f77`: `tests/services/{_case_fixtures,_allowed_actions_table,test_handoff,test_cases}.py` | the exact API and behaviour §4–§5 must meet |
| Sibling plans | `AEA-30.md` (calls `convert_live_queued(now, tx)`), `AEA-45.md` §4.4 (calls `queue`, `detail`, `oversight`, `apply`, `record_activity`), `AEA-38.md` step 5 (`open_case_for_thread`, `assemble`, `attach_brief`), `AEA-36.md` (catches `Exception` from `open`), `AEA-51.md` (container keys) | the consumer side of every signature |
| Join amendments | `docs/plans/ux-join/backend-amendments.md` §2 (AEA-29-1…5), §3 | AC-18…AC-23 |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-2, WF-4, check "A handoff left no case" | records, correlation ids |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`; workspace `code-design-solid-modularity.md`, `code-structure.md`, `async-safety.md` rule 1 | affected tests; journey record; context rows; file caps; loud stubs |

---

## 2. Boundary

### Owned files

| File | Action | Who |
|---|---|---|
| `src/meridian/services/_case_rules.py` | create | implementer (Step 1) |
| `src/meridian/services/handoff.py` | create | implementer (Steps 2, 4) |
| `src/meridian/services/cases.py` | create | implementer (Steps 3, 5, 6, 7, 8) |
| `src/meridian/services/_case_views.py` | create | implementer (Step 6) |
| `src/meridian/web/container.py` | modify: **the `register_cases` function only** (docstring and body) | implementer (Step 9) |
| `tests/services/_case_fixtures.py` | exists (frozen); amendment F-2 by the **test-writer** | test-writer |
| `tests/services/_allowed_actions_table.py` | exists (frozen) | test-writer |
| `tests/services/test_handoff.py` | exists (frozen) | test-writer |
| `tests/services/test_cases.py` | exists (frozen); amendment F-1 by the **test-writer** | test-writer |
| `tests/services/test_cases_contract.py` | create | implementer (Step 10) |
| `tests/unit/services/test_case_rules.py` | create | implementer (Step 1) |
| `tests/unit/services/test_brief_assembler.py` | create | implementer (Step 2) |
| `tests/unit/web/test_register_cases.py` | create | implementer (Step 9) |
| `tests/journeys/j6/test_aea_29.py` | create | implementer (Step 11) |
| `tests/journeys/j7/test_aea_29.py` | create | implementer (Step 11) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-29.md` | create (date = `date +%F` on the commit day) | implementer (Step 12) |
| `.claude/reference/area-map.md` | modify: the *Status* cell of the **first** A6 row only | implementer (Step 12) |
| `.claude/state/icm-progress.md` | modify: append one *Routes verified* row | implementer (Step 12) |
| `docs/design/code-design.md` | modify: the `cases.py` and `handoff.py` tree rows, one new tree row for the two private modules, one new `**Built:**` line | implementer (Step 12) |
| `docs/design/contracts/stage7/cases.md` | modify: **append** subsection "§5a Built by AEA-29" after §5's rules table; nothing else | implementer (Step 12) |

`tests/services/__init__.py`, `tests/unit/services/__init__.py`, `tests/unit/web/__init__.py`, `tests/journeys/j6/__init__.py`
and `tests/journeys/j7/__init__.py` already exist. Do not add a `conftest.py` anywhere.

### Shared surfaces: read and import only

- `src/meridian/domain/*` (AEA-02, AEA-02b) and `src/meridian/ports/*`.
- `src/meridian/adapters/sqlite/*` and `schema/*.sql` (AEA-10).
- `src/meridian/policy/{handoff,texts}.py`, `src/meridian/privacy/redact.py`, `src/meridian/retrieval/{manifest,ingest}.py`.
- `src/meridian/web/deps.py`, `src/meridian/web/middleware.py`.
- `src/meridian/agent/nodes/compose.py`: tests only; `services/` never imports `agent/`.
- `src/meridian/services/{reset,live_chat,staff,person_request}.py`.
- Test support:
  - `tests/fakes/clock.py`, `tests/fixtures/sqlite.py`, `tests/api/openapi_check.py`, `tests/api/web_shell_support.py`.
  - `tests/services/live_chat_support.py`, `tests/services/person_request_support.py`.
  - `tests/journeys/support/**`, `tests/conftest.py`.
- Project files: `pyproject.toml`, `uv.lock`.
- Signed contracts: the OpenAPI, `UI_CONTRACTS.md`, `SCREEN_SPECS.md`, every other contract file.

### Other tickets' files: never touch

- Every other `register_*` function in `container.py`.
- `services/{demo,scheduler,turn,session,metrics_reader}.py`, every `web/routes/*`, `web/schemas/*`, `web/deps.py`.
- `agent/**`, `policy/*`, `domain/*`, `retrieval/*`, `adapters/**`.
- `tests/journeys/support/**`, `tests/unit/web/test_container.py`, every other ticket's tests.
- `apps/web/**`, `docs/ux/**`, the briefing, issued data, `docs/archive/`, `docs/parked/`.

A missing type, method, column or sentence is a follow-up on its owner (§8), never a local copy. **The four frozen files
are edited only by the test-writer** (F-1, F-2). If any other frozen assertion looks wrong, stop and report it. Never edit
it yourself.

---

## 3. Requirements table

### 3a. Acceptance criteria → how built → how verified

`TH` = `tests/services/test_handoff.py`, `TC` = `tests/services/test_cases.py` (both frozen), `TK` =
`tests/services/test_cases_contract.py`, `TB` = `tests/unit/services/test_brief_assembler.py`, `TR` =
`tests/unit/services/test_case_rules.py`, `TW` = `tests/unit/web/test_register_cases.py`.

| AC | Requirement (short) | Built by (§5 step) | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `open` commits cases, case_events, promises, actions(case_opened), events(case_created), guidance `lookup_log` in one unit of work, or none | 3, 4 | TH `test_open_writes_all_rows_in_one_transaction`, `test_failure_after_case_row_leaves_no_rows` |
| AC-2 [invariant] | One open case per thread; new reason → one case_event + higher priority; same `turn_id` → zero rows; CON-4 always yields a case | 3 | TH `test_second_open_returns_already_open`, `test_repeat_turn_is_idempotent`, `test_new_reason_raises_priority`, `test_con4_always_yields_case` |
| AC-3 [invariant] | Stored promise = `promise_for(...)` for every reason × presence; live-queued sets `live_state='queued'` | 3, 4 | TH `test_promise_matches_table` (16 × 2), `test_promise_literal_rows` |
| AC-4 [invariant] | Fee-bearing: case due = window start, promise due = Mon 19:00; alert for P0, P1, fee-bearing only | 3 | TH `test_fee_bearing_stores_both_dues`, `test_alert_for_p0_p1_and_fee_bearing` |
| AC-5 [negative] | No promise-text argument anywhere; heading 6 only from the stored `Promise` | 2, 3, 4 | TB `test_heading_six_is_stored_promise`; TH `test_no_promise_text_parameter` |
| AC-6 [failure/refusal] | One retry; second failure → typed `CaseWriteFailed`; P0 case without a customer | 4 | TH `test_safety_write_retried_once`, `test_safety_case_without_customer` |
| AC-7 [invariant] | One guidance row per mapped passage, anchored on `handoff_anchor`; heading 7 item; never in responder inputs | 2, 4 | TH `test_staff_guidance_attached_not_responded` (needs F-2), `test_staff_guidance_anchor_without_customer_text` (**frozen security half**); TB `test_guidance_text_needs_matching_hash` |
| AC-8 [invariant] | Nobody online never live-queued; `convert_live_queued(now, tx)` converts, writes events, joins caller tx, returns count | 3, 5 | TC `test_unstaffed_never_live_queued`, `test_convert_live_queued`, `test_convert_joins_caller_transaction`; TK `test_stream_rows_match_openapi_events` |
| AC-9 [failure/refusal] | `apply` rejections and success writes | 1, 7 | TC `test_apply_rejections` (11 cases), `test_apply_success_writes_event` |
| AC-10 [invariant] | Promise kept / missed / open per the rules table | 1, 7, 8 | TC `test_promise_status_kept_and_missed` |
| AC-11 [invariant] | `due_state`, queue order, five lanes, `new_flags_count`, current value + `changed` | 1, 6 | TC `test_queue_ordering`, `test_oversight_lanes_fixed_order`, `test_detail_current_value_changed`; TK `test_seed_demo_with_real_assembler` (the same order on AEA-31's real seed); TR unit tests |
| AC-12 [failure/refusal] | `set_followup`: no open case, unverified `on_record` refused, four fields stored, masked label | 8 | TC `test_set_followup_rules` (**frozen security**) |
| AC-13 [negative] | No contact values in views or `case_events` | 1 (`mask`), 6, 7, 8 | TC `test_no_contact_values_in_views` (**frozen security**) |
| AC-14 [negative] | "Demo: recorded, not sent"; unclaimed → refused; no "sent you" wording | 8 | TC `test_activity_recorded_not_sent` |
| AC-15 [invariant] | Eight headings, origins, sources ≥ 1, `not_generated`, quote substring, `attach_brief` upsert | 2, 3 | TB `test_eight_headings_in_order`, `test_extraction_none_marks_not_generated`, `test_quote_must_be_substring`, `test_wp7_brief_items`; TC `test_attach_brief_upserts` |
| AC-16 [negative] | Staff notes only in heading 3 or 7 with `lookup_log` sources | 2 | TB `test_staff_notes_only_in_headings_3_or_7` |
| AC-17 [capture] | WF-2 records with correlation ids; "a handoff left no case" = 0 | 3, 4 | TH `test_wf2_records_present` |
| AC-18 [invariant] | `allowed_actions` from one pure function; listed iff accepted; representative examples equal | 1, 7 | TC `test_allowed_actions_listed_iff_accepted`, `test_allowed_actions_match_representative_examples`, `test_allowed_actions_by_role`; table Appendix B (= frozen `TABLE`) |
| AC-19 [invariant] | One producer per display value; equal to the OpenAPI example for the same input or listed; `source_ids` resolve | 1, 6 | TC `test_display_values_match_openapi_examples` (needs F-1), `test_every_brief_source_id_resolves`; TK `test_views_match_openapi_schemas` |
| AC-20 [negative] | Customer lines speak as "Customer", never "You" / a name | 6 | TC `test_staff_conversation_customer_unnamed`, `test_customer_speaker_name` (**frozen security**) |
| AC-21 [invariant] | Live-chat conversation writes change neither version nor lifecycle | 6, 7 (nothing reacts to conversation writes) | TC `test_conversation_writes_keep_case_version`; J-7 journey with the real `LiveChatService` |
| AC-22 [journey] | Extends J-6 and J-7; level `mock-tested`; *Blocked by* AEA-30, AEA-45, AEA-52 | 11, 12 | `uv run pytest -m journey tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py -q`; record `docs/testing/journeys/<date>-AEA-29.md` |
| AC-23 [invariant] | `detail` sets `events.last_event_id` in the same snapshot | **blocked-on UX session: OpenAPI amendment** (and an AEA-02b follow-up adding `events` to `views.CaseDetail`) | TC `test_detail_last_event_id_same_snapshot` is frozen as **skipped** with that reason; report it blocked, never passed |
| AC-24 [regression/context] | Area map, ICM row, code-design status, contract gaps in cases §5 | 12 | `git diff --name-only main...HEAD` |

### 3b. Source-contract reconciliation (obligations the ACs do not spell out)

| # | Obligation | Governing source | Disposition | Step / owner |
|---|---|---|---|---|
| O-1 | View types in `domain/` with OpenAPI names | cases A-2 | **done by AEA-02b** (`domain/views.py`); import from there | §4.1 |
| O-2 | `apply` returns the wire summary (`CaseSummaryView`), not DO-4's domain `CaseSummary` | AC-18; OpenAPI `CaseActionResponse.case` | `apply(...) -> CaseSummaryView \| CaseActionRejected`; `result_line` is AEA-45's (`schemas/staff_cases.py`) | 7; cases §5a |
| O-3 | `record_activity` gives the activity and the updated case | OpenAPI `recordContactActivity` 201 `ActivityResponse` | returns `ActivityResult \| CaseActionRejected` | 8 |
| O-4 | `set_followup` refuses with `NOT_ALLOWED_IN_STATE` + `details.state` | OpenAPI `saveFollowUp` 409; web.md §8 WEB-23 | returns `FollowUp \| CaseActionRejected`; AEA-42's route already reads `.code` / `.details` | 8 |
| O-5 | `detail` of an unknown case lets the route answer 404 | OpenAPI `getCase` 404; AEA-45 H3 catches `LookupError` with `.case_ref` | raises `CaseNotFound(case_ref)` | 6 |
| O-6 | The `shift_ended` row must validate as `EvShiftEnded` (`speaker`, `line`, `handoff`, `settled`), and only the composer (`agent/`) builds the block and the panel | web.md §14; graph-core §13; DO-3 §2.1; RF-13 | `CaseService(..., handoff_block=…, settled_view=…)`. Each is an optional callable: with `None` the payload has `"handoff": null` and no `settled` key (unit tests only). The container binds both | 5, 9 |
| O-7 | Heading 7 must show the staff-guidance **text**, but `lookup_log` stores only its sha256 | CAS-33; AC-7 | `BriefAssembler(staff_guidance: Mapping[PassageId, StaffGuidance] \| None = None)`; text shown only on hash match (RF-14) | 2 |
| O-8 | A quote that is not an exact substring of a customer message is rejected | AC-15; graph-nodes §2 | optional keyword `customer_messages: Mapping[int, str] \| None = None` on `attach_extraction`. AEA-31's three-argument call still type-checks (`services/reset.py` `_BriefAssembler`) | 2 |
| O-9 | One `source_id` scheme for `BriefItem.source_ids` and `CaseSource.source_id` | AC-19 | `source_id = f"src-{row.id}"`, `lookup_log_id = f"ll-{row.id}"`; only `lookup_log` sources become chips | 6; cases §5a |
| O-10 | No contact value in any view or `case_event` | DO-6 WF-2/WF-4; AC-13 | `mask(text) = redact(text, RedactionProfile.SONNET).text`. SONNET masks cards, emails, phones (to "[phone ending NN]"), addresses and codes, and keeps invoice and customer IDs (`privacy/redact.py`). Applied to every staff free text before storing, and to every customer-derived string in a view | 1, 6–8 |
| O-11 | `case_created` must not reach a wire stream that does not know it | web.md §11; `CHAT_EVENT_TYPES` drop it | `case_created` goes to the **thread** stream (CON-3 never sends it). The case stream gets only `case_changed` and `chat_closed` from this ticket (`CASE_EVENT_TYPES` in `web/schemas/staff_live.py`) | 3, 5, 7 |
| O-12 | `DemoService` (AEA-30) is not on `main` | DO-3 S-20 | private typing `Protocol` `_PresenceSource` in `handoff.py`; the container forwarder satisfies it | 4, 9 |
| O-13 | Retry on every trigger | UI_CONTRACTS CON-4 "a case write that fails is retried once" | same code path for all triggers | 4 |
| O-14 | `customer_id` stored on a case only for a **verified** identity | R-16; consolidated §9.5 | in-ticket | 3 |
| O-15 | Email / general follow-up texts and the oversight alert lines other than `OVERSIGHT_OVERDUE` are not in `policy/texts.py` | data.md §2 (UX owns words); cases A-11 | **blocked-on AEA-03 follow-up** for those branches. They raise `NotImplementedError` naming it (async-safety rule 1); alerts list only `overdue` | 8; R-5 |
| O-16 | `register_cases` provides `case_service`, `handoff_service`, `brief_assembler` and resolves staff guidance at start-up | ticket *Agent handoff*; cases §5; AEA-51 plan line 196 | **in-ticket** (RF-12) | 9 |
| O-17 | `case_write_failed` signal | graph-nodes §4 | other-ticket: **AEA-36** emits it (catches `Exception`) | — |
| O-18 | DO-6 check needs `cases.turn_id` = the request's `turn_id` | DO-6 | in-ticket | 3 |
| O-19 | No `Promise(` constructor in `src/meridian/services/` | graph-core §10 (GRC-2) | in-ticket; grep gate | §7 |
| O-20 | No `import sqlite3`, no SQL in `services/` | DO-3 §2.1 | in-ticket; grep gate | §7 |
| O-21 | AEA-31's seed calls `BriefAssembler()` then `assemble` / `attach_extraction(brief, extraction, None)` on every first boot | `container.py` `register_reset`; `services/reset.py` `seed_demo` | in-ticket: defaults keep both calls valid; TK proves the real seed assembles | 2, 10 |
| O-22 | `result_seen` comes in three formats | RF-15 | `parse_seen` | 1 |
| O-23 | The case view's identity reads verified for a case opened by a verified customer | RF-16 | `identity_view(identity, case_customer=…)` | 1, 6 |

### 3c. Entry-point registration

| Entry point | Workflow | Registered in DO-6 | Inherits |
|---|---|---|---|
| Services behind CON-4, CON-5 (`HandoffService.open`, `CaseService.set_followup`) | WF-2 | yes | E-6; M-10…M-13, M-15; CAP-3 (AEA-51) |
| Services behind CON-11…13, 15, 17 | WF-4 | yes | M-13, M-27; CAP-4 (AEA-52) |
| Shift end (`convert_live_queued`) | WF-5 (AEA-30) | yes | R-30 |

No HTTP route is added here (AEA-42, 45, 51, 52 own them).

### 3d. Frozen tests (`risk::security`) and the two amendments

The test-writer froze four files at `7c60f77` from the previous plan: `tests/services/_case_fixtures.py`,
`tests/services/_allowed_actions_table.py`, `tests/services/test_handoff.py`, `tests/services/test_cases.py`. This refresh
read every test against the code on `main` and this plan.

**Shapes the frozen tests fix:**
- **Constructors:** `CaseService(uow, clock, handoff_block=…)`, `HandoffService(uow, cases, demo, clock, staff_guidance=…)`,
  `BriefAssembler(staff_guidance=…)`.
- **Inputs:** imported from `meridian.domain.views`.
- **Pure rules:** `meridian.services._case_rules` exports `CON13_ACTIONS`, `LANE_ORDER` and keyword-only `actions_for`.
- **Refusals:** detected by `hasattr(result, "code") and hasattr(result, "details")`.
- **Rows:** counted through `tx.connection`.

**Two defects.** The test-writer amends both **before** the implementer starts (same frozen-test process, new manifest
hash).

- **F-1 — `tests/services/test_cases.py`, `_DIFFERENCES` (lines 757–763).** It lists `"promise.text"` as a field that
  must differ from the `getCase` DEFAULT example. It cannot differ:
  - The promise record shows what the customer was told: the table text with `{due_label}` and `{case_ref}` filled.
  - For the example's own input (MHC-C-0007 created Fri 14:14), that text equals the example word for word. Checked:
    `promise_for(BILLING_DISPUTE, "nobody_online", 2026-10-16 14:14 Chicago)`, filled, equals `_EXAMPLE_PROMISE["text"]`.
  - Showing the raw template ("by {due_label}") to staff would be wrong, and AC-19 asks for equality "for the same
    input".

  **Amendment:** delete the line `"promise.text",  # the example's wording …` from `_DIFFERENCES`. Nothing else changes.
- **F-2 — `tests/services/_case_fixtures.py`, `guidance()` (lines 297–306).** Every reason gets
  `PassageId("internal/agent_discretion_notes.md#3")`. `services()` keys the assembler's map by passage id, so when
  several reasons are mapped only the last reason's passage survives. Then
  `test_staff_guidance_attached_not_responded[refund]`, `[fee_bearing_change]` and `[late_technician]` cannot find their
  text in heading 7.

  **Amendment:** give each reason its own id, e.g.
  `PassageId(f"internal/agent_discretion_notes.md#{list(STAFF_GUIDANCE_FOR).index(reason)}")`. Nothing else changes.
  With RF-14's hash check, a wrong passage is never shown, so the amended test proves the right text appears.

**Red for the right reason** after the amendment: `ModuleNotFoundError: No module named 'meridian.services.cases'` /
`'meridian.services.handoff'` / `'meridian.services._case_rules'`. Then `uv run pytest --collect-only -q` still collects
everything else.

| Frozen file | Functions | AC |
|---|---|---|
| `test_handoff.py` | `test_open_writes_all_rows_in_one_transaction`, `test_failure_after_case_row_leaves_no_rows`, `test_second_open_returns_already_open`, `test_repeat_turn_is_idempotent`, `test_new_reason_raises_priority`, `test_con4_always_yields_case`, `test_promise_matches_table`, `test_promise_literal_rows`, `test_fee_bearing_stores_both_dues`, `test_alert_for_p0_p1_and_fee_bearing`, `test_no_promise_text_parameter`, `test_safety_write_retried_once`, `test_safety_case_without_customer`, **`test_staff_guidance_attached_not_responded`**, **`test_staff_guidance_anchor_without_customer_text`**, `test_wf2_records_present`, `test_presence_read_inside_transaction` | AC-1…7, 17 |
| `test_cases.py` | `test_unstaffed_never_live_queued`, `test_convert_live_queued`, `test_convert_joins_caller_transaction`, `test_apply_rejections`, `test_apply_success_writes_event`, `test_promise_status_kept_and_missed`, `test_queue_ordering`, `test_oversight_lanes_fixed_order`, `test_detail_current_value_changed`, **`test_set_followup_rules`**, **`test_no_contact_values_in_views`**, `test_activity_recorded_not_sent`, `test_attach_brief_upserts`, `test_allowed_actions_listed_iff_accepted`, `test_allowed_actions_match_representative_examples`, `test_allowed_actions_by_role`, `test_display_values_match_openapi_examples`, `test_every_brief_source_id_resolves`, **`test_staff_conversation_customer_unnamed`**, **`test_customer_speaker_name`**, `test_conversation_writes_keep_case_version`, `test_detail_last_event_id_same_snapshot` (skipped, AC-23) | AC-8…15, 18…21, 23 |

---

## 4. Shared code to use

### 4.1 Imports (all verified on `29ca543` with one import check; Step 0.4 repeats it)

| Name | Module | Used in |
|---|---|---|
| `MeridianModel`, `ApiErrorCode`, `CaseRef`, `ThreadId`, `TurnId`, `CustomerId`, `InvoiceId`, `PassageId`, `SafetyKind` | `meridian.domain.common` | all |
| `HandoffReason`, `Priority`, `Presence`, `CaseState`, `Promise`, `FollowUp`, `CaseSummary`, `HandoffRequest`, `HandoffResult`, `Brief`, `BriefHeading`, `BriefItem`, `SourceRef`, `Quote`, `BriefExtraction`, `BRIEF_TITLES`, `BRIEF_KEYS`, `BRIEF_ORIGINS` | `meridian.domain.handoff` | all |
| `ActionKind`, `ActionKey`, `CompletedAction`, `Settled` | `meridian.domain.actions` | cases |
| `ConversationState`, `Controller`, `IdentityState` | `meridian.domain.state` | handoff, cases, rules |
| `TurnContext`, `CheckResult` | `meridian.domain.turn` | handoff |
| `AccountResult`, `KnowledgeResult` | `meridian.domain.specialists` | handoff (brief) |
| `LookupEntry`, `LookupRow` | `meridian.domain.tools` (**never** from an adapter, R-G-8) | handoff, views |
| `HandoffBlock`, `LiveQueuedBlock`, `SettledView`, `Speaker` | `meridian.domain.blocks` | cases, views |
| `QueueRow`, `QueueView`, `PriorityView`, `StaffingView`, `CaseSummaryView`, `BriefItemView`, `BriefHeadingView`, `BriefView`, `CaseSource`, `ChatLineView`, `Activity`, `PromiseFollowUp`, `PromiseHistoryItem`, `PromiseRecord`, `LiveStateView`, `CaseIdentityView`, `OtherCase`, `CaseDetail`, `CaseAction`, `CaseActionRejected`, `FollowUpChoice`, `ActivityIn`, `ActivityResult`, `Alert`, `Lane`, `OversightLanes`, `OversightView`, `AllowedAction`, `CaseActionName`, `DueState` | `meridian.domain.views` (AEA-02b) | rules, views, cases |
| `StaffRole`, `StaffActor`, `STAFF_PERSONAS`, `ASSIGNEE_ROLES`, `ROLE_ACTIONS`, `CUSTOMER_SPEAKER_NAME` | `meridian.domain.staff` | rules, views, cases |
| `Clock`, `UnitOfWork`, `UnitOfWorkFactory` | `meridian.ports.runtime` | handoff, cases |
| `promise_for`, `case_due_at`, `due_label`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`, `STAFF_GUIDANCE_FOR` | `meridian.policy.handoff` | rules, cases, handoff, container |
| `TEXTS`, `TextId`, `render`, `format_usd` | `meridian.policy.texts` | rules, cases, handoff |
| `redact`, `RedactionProfile` | `meridian.privacy.redact` | rules |
| `StaffGuidance` | `meridian.retrieval.manifest` (light module, MC-26; import under `if TYPE_CHECKING:` in `handoff.py`) | handoff |
| `load_staff_guidance` | `meridian.retrieval.ingest` (**container hunk only**, imported inside the function: the module imports numpy and pypdf) | container |
| `CaseRow`, `CaseEventRow`, `PromiseRow`, `FollowupRow`, `ActivityRow`, `ConversationRow`, `MessageRow`, `CustomerRow`, `InvoiceRow`, `AppointmentRow`, `StreamEvent`, `thread_stream`, `case_stream` | `meridian.adapters.sqlite.rows` (DO-3 arrow SVC → SQL) | cases, views |
| `CLOSED_LIFECYCLES` | `meridian.adapters.sqlite.repos_cases` | rules |
| `Container`, `ContainerError`, `Key` | `meridian.web.container` (same module) | hunk |
| `CASE_SERVICE`, `HANDOFF_SERVICE`, `DEMO_SERVICE`, `REPLY_COMPOSER`, `UOW_FACTORY` | `meridian.web.deps` (inside the hunk) | hunk |
| `WebShellState` | `meridian.web.middleware` (inside the hunk) | hunk |
| `FixedClock`, `WORKED_PAIRS_NOW`, `CHICAGO` | `tests.fakes.clock` | tests |
| `temp_sqlite`, `TempStore` | `tests.fixtures.sqlite` | tests |
| `assert_response_matches`, `assert_sse_frames_match`, `SseFrame` | `tests.api.openapi_check` | TK, journeys |
| `seed_demo` | `meridian.services.reset` | TK |
| `ReplyComposer` | `meridian.agent.nodes.compose` (tests only) | TK |
| `CHAT_EVENT_TYPES` | `meridian.web.schemas.events` (tests only) | TK |
| `CASE_EVENT_TYPES` | `meridian.web.schemas.staff_live` (tests only) | TK |
| `new_service`, `RILEY` | `tests.services.live_chat_support` (read only) | J-7 |
| every builder in `tests.services._case_fixtures` | frozen, read only | TK, TB, TW, journeys |

Shapes you rely on (copied from `main`; do not change):

```python
class CaseSummary(MeridianModel):      # domain.handoff; HandoffResult.case
    case_ref: CaseRef; reason: HandoffReason; priority: Priority; state: CaseState; created_at: dt.datetime
    promise: Promise; followup: FollowUp | None; version: int; seed: bool = False; due_at: dt.datetime | None
class HandoffRequest(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; reason: HandoffReason; priority: Priority; rule_id: str
    trigger: Literal["gate", "escalation", "con4", "safety"]; identity: IdentityState
    change_request: ChangeRequestDraft | None = None; safety_kind: SafetyKind | None = None
class HandoffResult(MeridianModel):
    case: CaseSummary; created: bool; action: CompletedAction; alert: Literal["supervisor_now"] | None
class Promise(MeridianModel):          # domain.common; ONLY policy/handoff.py constructs it (GRC-2)
    policy_row: str; text: str; due_at: dt.datetime | None; due_label: str | None
    extra_lines: tuple[str, ...] = (); live_queued: bool = False
class FollowUp(MeridianModel):         # domain.common, re-exported by domain.handoff
    channel: Literal["email", "phone"]; destination_label: str; on_record: bool
    window: Literal["morning", "afternoon", "any"]; saved_line: str
class LookupEntry(MeridianModel): tool; record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]; result_seen: str; message_id: int; turn_id: TurnId
class LookupRow(LookupEntry): id: int; thread_id: ThreadId
class StaffGuidance(MeridianModel): passage_id; file; section; version_label; text; text_sha256   # sha of text.strip()
class CaseAction(MeridianModel):       # domain.views
    action: CaseActionName; expected_version: int; reason: str | None = None; wake_up_at: dt.datetime | None = None
    outcome: str | None = None; assignee: Literal["riley", "supervisor"] | None = None; priority: Priority | None = None
class CaseActionRejected(MeridianModel): code: ApiErrorCode; field: str | None = None; constraint: str | None = None; details: dict[str, JsonValue] | None = None
class FollowUpChoice(MeridianModel): channel; destination: Literal["on_record", "general"]; window
class ActivityIn(MeridianModel): kind: Literal["call","email"]; outcome: Literal["reached","no_answer","left_message"]; note: str | None = None; expected_version: int
# Brief: validator enforces 8 headings, numbers 1..8, titles = BRIEF_TITLES, keys = BRIEF_KEYS, origins = BRIEF_ORIGINS,
#   heading 4 checked False, not_generated only on 2, 4, 7. BriefExtraction: needs 1..2 Quote, claims ≤ 5, open_decision ≤ 200.
# CheckResult: text: str; removals: tuple[Removal, ...]; passed: bool
# ConversationState: thread_id; settled; controller; identity; turn_input: TurnInput(turn_id, message_id, kind, text_store,
#   …, received_at); gate: GateDecision | None (.rules.safety: SafetyKind | None); escalation: EscalationDecision | None
#   (.reason, .rule_id); specialist_results: list[KnowledgeResult | AccountResult | SchedulingResult]
# AccountResult: status "read"|…; invoices: tuple[InvoiceView]; staff_notes: tuple[StaffNote(kind, record_id, text, source_file)]
# InvoiceView: invoice_id, total_cents, balance_cents, issued_on, due_on, … · KnowledgeResult: status "answered"|…; points: tuple[KnowledgePoint(text, passage_id)]
# ActionKind members: BOOKED, MOVED, CANCELLED, CHANGE_REQUEST_SENT, CASE_OPENED, FOLLOWUP_SAVED, VERIFIED
```

Repository calls (bodies are AEA-10's; verified on `main`):

```python
tx.cases.cases.insert(row: CaseRow) -> None
tx.cases.cases.get(case_ref) -> CaseRow | None
tx.cases.cases.get_for_thread_open(thread_id) -> CaseRow | None
tx.cases.cases.list_open() -> tuple[CaseRow, ...]            # not resolved/closed, by created_at, case_ref
tx.cases.cases.list_for_customer(customer_id) -> tuple[CaseRow, ...]
tx.cases.cases.update_versioned(case_ref, expected_version, **changes) -> int | None   # new version or None
    # keys allowed: lifecycle, owner_role, owner_since, due_at, wake_up_at, priority, reason, resolved_at, queued_at,
    #   alert, customer_id, updated_at (anything else raises ValueError); enum members and aware datetimes accepted
tx.cases.case_events.append(event: CaseEventRow) -> int ; .list_for_case(case_ref) -> tuple[CaseEventRow, ...]
    # UNIQUE (case_ref, kind, event_key) only where event_key <> '': leave key "" (the default)
tx.cases.promises.insert(case_ref, promise, at) -> int       # status 'open'
tx.cases.promises.current(case_ref) -> PromiseRow | None ; .history(case_ref) -> tuple[PromiseRow, ...]
tx.cases.promises.set_status(case_ref, status, at, reason) -> bool    # the CURRENT (max id) row
tx.cases.followups.upsert(row: FollowupRow) ; .get(case_ref) -> FollowupRow | None
tx.cases.activities.insert(row: ActivityRow) -> int ; .list_for_case(case_ref)
tx.cases.briefs.upsert(brief, at) ; .get(case_ref) -> Brief | None
tx.cases.demo_state.get() -> DemoStateRow                    # .staffing, .demo_now
tx.cases.refs.next_case_ref() -> CaseRef
tx.core.actions.record(action) -> CompletedAction            # idempotent on the key
tx.core.actions.for_thread(thread_id) -> tuple[CompletedAction, ...]
tx.core.events.append(stream: StreamKey, event: StreamEvent) -> EventId ; .after(stream, last) -> list[EventRow]
tx.core.lookup_log.append(entry: LookupEntry) -> int ; .for_thread(thread_id) -> tuple[LookupRow, ...]
tx.core.messages.handoff_anchor(thread_id) -> int            # newest customer message, else the first row (greeting)
tx.core.messages.all_for_thread(thread_id) -> tuple[MessageRow, ...]
tx.core.conversations.lookup(str(thread_id)) -> ConversationRow | EndedThread | None
tx.core.conversations.set_live_state(thread_id, live_state, live_since) -> None
tx.core.reads.invoice(InvoiceId) / .appointment(int) / .customer(CustomerId) -> row | None
tx.core.reads.identity_state(thread_id) -> IdentityState     # "not_checked" when the thread has no identity row
tx.core.reads.new_flags_count() -> int
tx.core.settled_for(thread_id, read_at) -> Settled
tx.commit()                                                  # once; the block exit rolls back otherwise
```

Row shapes you build (keyword arguments):

```python
CaseRow(case_ref, thread_id, turn_id=None, customer_id=None, reason, priority, rule_id, trigger, lifecycle, owner_role=None,
        owner_since=None, due_at=None, wake_up_at=None, version=1, seed=False, safety_kind=None, change_request=None,
        alert=None, created_at, updated_at, resolved_at=None, queued_at=None)
CaseEventRow(case_ref, kind (1..40 chars), actor_role: "representative"|"supervisor"|"owner"|"ai"|"system",
             detail: dict[str, JsonValue] = {}, at)
FollowupRow(case_ref, thread_id, channel, destination_label, destination=None, on_record, window, saved_line, updated_at)
ActivityRow(case_ref, kind, outcome, note=None, actor_role: StaffRole, at)
StreamEvent(type (≤ 40), payload: dict[str, JsonValue] = {}, at)
```

### 4.2 What this ticket exports (exact; consumers rely on these names)

**`src/meridian/services/handoff.py`**

```python
__all__ = ["TRIM_NOTE", "BriefAssembler", "CaseWriteFailed", "HandoffService", "resolve_staff_guidance"]

TRIM_NOTE: Final = "Something here didn't match the record and was removed."
    # [Source: SCREEN_SPECS SCR-6 line 317; OpenAPI getCase TRIMMED_STOP trim_note] staff copy

class CaseWriteFailed(Exception):
    """The case write failed twice (DO-1 §8.2). Carries no value."""
    attempts: int          # always 2
    cause: str             # always "write_error"
    def __init__(self, attempts: int = 2) -> None: ...   # super().__init__(f"case write failed after {attempts} attempts")

def resolve_staff_guidance(prefixes: Mapping[HandoffReason, tuple[str, ...]],
                           passages: Sequence[StaffGuidance]) -> Mapping[HandoffReason, tuple[StaffGuidance, ...]]: ...

class HandoffService:
    def __init__(self, uow: UnitOfWorkFactory, cases: CaseService, demo: _PresenceSource, clock: Clock,
                 staff_guidance: Mapping[HandoffReason, tuple[StaffGuidance, ...]] | None = None) -> None: ...
    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ...

class BriefAssembler:
    def __init__(self, staff_guidance: Mapping[PassageId, StaffGuidance] | None = None) -> None: ...
    def assemble(self, case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]) -> Brief: ...
    def attach_extraction(self, brief: Brief, extraction: BriefExtraction | None, check: CheckResult | None,
                          *, customer_messages: Mapping[int, str] | None = None) -> Brief: ...
```

(`staff_guidance=None`, not `= {}`: ruff B006/B008 reject a mutable or called default. cases §5's `= {}` means "no
guidance", and `None` means the same.)

**`src/meridian/services/cases.py`**

```python
__all__ = ["CaseNotFound", "CaseService", "staffing_view"]   # staffing_view re-exported from _case_rules (R-16)

HandoffBlockFn: TypeAlias = Callable[[HandoffResult], HandoffBlock | LiveQueuedBlock | None]
SettledViewFn: TypeAlias = Callable[[Settled, IdentityState, Controller], SettledView]

class CaseNotFound(LookupError):
    case_ref: str
    def __init__(self, case_ref: str) -> None: ...        # super().__init__(f"no case {case_ref}")

class CaseService:
    def __init__(self, uow: UnitOfWorkFactory, clock: Clock, *, handoff_block: HandoffBlockFn | None = None,
                 settled_view: SettledViewFn | None = None) -> None: ...
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

`set_followup` reads only `choice.channel`, `choice.destination`, `choice.window`. AEA-42's route passes its own
`FollowUpRequestBody`, which has the same three fields. Never `isinstance`-check `choice`.

**`src/meridian/services/_case_rules.py`**: private; pure (no I/O, no clock read); every name has a docstring.

```python
LiveState: TypeAlias = Literal["not_live", "queued", "joined", "handed_back", "closed"]
LaneName: TypeAlias = Literal["p0_p1", "overdue", "due_soon", "unowned", "stuck_waiting"]
CON13_ACTIONS: Final[tuple[CaseActionName, ...]] = ("claim", "release", "start", "wait", "resolve", "close_unresolved",
                                                    "assign", "change_priority")
ACTION_ORDER: Final[tuple[AllowedAction, ...]] = ("claim", "claim_and_join", "join_chat", "send_live_message",
    "hand_back", "close_chat", "start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release",
    "assign", "change_priority", "flag")
CLOSED: Final[frozenset[str]] = frozenset(CLOSED_LIFECYCLES)
OWNER_LIFECYCLES: Final[Mapping[str, frozenset[str]]]                     # step 1.1
LANE_ORDER: Final[tuple[LaneName, ...]] = ("p0_p1", "overdue", "due_soon", "unowned", "stuck_waiting")
REASON_LABEL: Final[Mapping[HandoffReason, str]] ; SAFETY_KIND_LABEL: Final[Mapping[str, str]]
PRIORITY_WORD: Final[Mapping[Priority, Literal["Safety", "Danger", "Time-sensitive", "Standard", "Routine"]]]
LIFECYCLE_WORD: Final[Mapping[str, str]] ; WINDOW_WORD: Final[Mapping[str, str]]
def state_allows(action: AllowedAction, *, lifecycle: str, owner_role: StaffRole | None, live_state: str,
                 staffing: str, actor_role: StaffRole) -> bool: ...
def actions_for(*, lifecycle: str, owner_role: StaffRole | None, live_state: str, staffing: str,
                actor_role: StaffRole) -> tuple[AllowedAction, ...]: ...
def con13_refusal(action: CaseActionName, *, lifecycle: str, owner_role: StaffRole | None,
                  owner_since: dt.datetime | None, actor_role: StaffRole) -> CaseActionRejected | None: ...
def missing_field_refusal(action: CaseAction, now: dt.datetime) -> CaseActionRejected | None: ...
def due_state(case_due: dt.datetime | None, now: dt.datetime) -> DueState: ...
def queue_key(priority: Priority, state: DueState, case_due: dt.datetime | None, created_at: dt.datetime,
              case_ref: str) -> tuple[int, int, int, float, float, str]: ...
def lane_for(priority: Priority, state: DueState, lifecycle: str, created_at: dt.datetime,
             wake_up_at: dt.datetime | None, now: dt.datetime) -> LaneName | None: ...
def reason_label(reason: HandoffReason, safety_kind: str | None = None) -> str: ...
def follow_up_short(channel: str | None, window: str | None) -> str | None: ...
def clock_text(at: dt.datetime) -> str: ...
def age_label(created_at: dt.datetime, now: dt.datetime, *, queued_at: dt.datetime | None = None) -> str: ...
def case_due_label(case_due: dt.datetime | None, *, is_window_start: bool) -> str | None: ...
def identity_view(identity: IdentityState, *, case_customer: bool) -> tuple[str, str, str]: ...  # (status, line, demo_note)
def staff_name(actor_role: str) -> str: ...
def promise_status_after_resolve(promise_due: dt.datetime | None, now: dt.datetime) -> Literal["kept", "missed"]: ...
def promise_status_after_activity(outcome: str, promise_due: dt.datetime | None, now: dt.datetime, current: str) -> str: ...
def fill_promise_text(promise: Promise, case_ref: str) -> str: ...
def mask(text: str) -> str: ...
def parse_seen(result_seen: str) -> dict[str, JsonValue]: ...
def staffing_view(mode: str) -> StaffingView: ...
```

**`src/meridian/services/_case_views.py`**: private builders that only `cases.py` calls (Step 6 lists them).

---

## 5. Steps

Stay inside DO-3's boundary. `services/` may import `domain/`, `policy/`, `privacy/`, `ports/`, `retrieval/manifest`
(TYPE_CHECKING only) and `adapters/sqlite` rows and repos (through `tx`). Never import `agent/`, `web/`, `sqlite3` or
another service module; siblings arrive by injection.

**Interfaces this ticket implements:** DO-4 §7 `HandoffService` and `BriefAssembler`; DO-4 §13 `CaseService` as revised
by cases §5.
**Interfaces it consumes:** the `UnitOfWork` port, the `Clock` port, `_PresenceSource` (structural; AEA-30's
`DemoService`), and the two composer callables (AEA-21's `ReplyComposer`).
No other new seam: the two private modules hide nothing behind an interface.

Every file:
- docstring first, then `from __future__ import annotations`, then `import datetime as dt`;
- absolute imports, one statement per line;
- no module-level instances except immutable constants (`Final`, `MappingProxyType`).

### Step 0 — preconditions (stop and report if any fails)

1. Work in `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-29` (branch `aea-29-aea-29-cases-handoff`).
   `export UV_LINK_MODE=hardlink`; never copy a venv; no `node_modules`; check `df -h /home` first (stop if under 4 GB free).
2. `git log --oneline -5` shows the test-writer's amendment commit for **F-1 and F-2** on top of `7c60f77`. Then confirm:
   - `grep -n '"promise.text"' tests/services/test_cases.py` prints nothing;
   - `grep -n 'agent_discretion_notes.md#3"' tests/services/_case_fixtures.py` prints nothing.

   If either fails, stop and report `blocked-on test-writer amendment F-1/F-2`.
3. `git merge --no-edit main`. It must bring in `src/meridian/domain/views.py`, `agent/nodes/compose.py` and
   `services/reset.py`. The frozen files are new paths, so no conflict is expected; a conflict anywhere is a stop.
   Then `uv sync`.
4. Prove every import in one command (it must print `ok`):
   ```bash
   uv run python -c "
   from meridian.domain.common import ApiErrorCode, CaseRef, ThreadId, TurnId, CustomerId, InvoiceId, PassageId, SafetyKind
   from meridian.domain.handoff import HandoffReason, Priority, Presence, CaseState, Promise, FollowUp, CaseSummary, HandoffRequest, HandoffResult, Brief, BriefHeading, BriefItem, SourceRef, Quote, BriefExtraction, BRIEF_TITLES, BRIEF_KEYS, BRIEF_ORIGINS
   from meridian.domain.actions import ActionKind, ActionKey, CompletedAction, Settled
   from meridian.domain.state import ConversationState, Controller, IdentityState
   from meridian.domain.turn import TurnContext, CheckResult
   from meridian.domain.specialists import AccountResult, KnowledgeResult
   from meridian.domain.tools import LookupEntry, LookupRow
   from meridian.domain.blocks import HandoffBlock, LiveQueuedBlock, SettledView, Speaker
   from meridian.domain.views import QueueRow, QueueView, PriorityView, StaffingView, CaseSummaryView, BriefItemView, BriefHeadingView, BriefView, CaseSource, ChatLineView, Activity, PromiseFollowUp, PromiseHistoryItem, PromiseRecord, LiveStateView, CaseIdentityView, OtherCase, CaseDetail, CaseAction, CaseActionRejected, FollowUpChoice, ActivityIn, ActivityResult, Alert, Lane, OversightLanes, OversightView, AllowedAction, CaseActionName, DueState
   from meridian.domain.staff import StaffRole, StaffActor, actor_for, STAFF_PERSONAS, ASSIGNEE_ROLES, ROLE_ACTIONS, CUSTOMER_SPEAKER_NAME
   from meridian.ports.runtime import Clock, UnitOfWork, UnitOfWorkFactory
   from meridian.policy.handoff import promise_for, case_due_at, due_label, business_due, priority_for, DUE_SOON_WINDOW, UNOWNED_AFTER, PROMISE_TABLE, STAFF_GUIDANCE_FOR
   from meridian.policy.texts import TEXTS, TextId, render, format_usd
   from meridian.privacy.redact import redact, RedactionProfile
   from meridian.retrieval.manifest import StaffGuidance
   from meridian.retrieval.ingest import load_staff_guidance
   from meridian.adapters.sqlite.rows import thread_stream, case_stream, CaseRow, CaseEventRow, PromiseRow, FollowupRow, ActivityRow, StreamEvent, MessageRow, ConversationRow, CustomerRow, InvoiceRow, AppointmentRow
   from meridian.adapters.sqlite.repos_cases import DEMO_START, CLOSED_LIFECYCLES
   from meridian.agent.nodes.compose import ReplyComposer
   from meridian.services.reset import seed_demo
   from meridian.web.deps import CASE_SERVICE, HANDOFF_SERVICE, DEMO_SERVICE, REPLY_COMPOSER, UOW_FACTORY
   from tests.fakes.clock import FixedClock, WORKED_PAIRS_NOW
   from tests.fixtures.sqlite import temp_sqlite
   from tests.api.openapi_check import assert_response_matches, assert_sse_frames_match, SseFrame
   assert len(HandoffReason) == 16 and CUSTOMER_SPEAKER_NAME == 'Customer' and ROLE_ACTIONS[StaffRole.OWNER] == frozenset()
   assert str(case_stream(CaseRef('MHC-C-0009'))) == 'case:MHC-C-0009'
   assert 'events' not in CaseDetail.model_fields
   print('ok')"
   ```
   If a name is missing, stop and report `blocked-on <owner>`. Never define it here.
5. Red check: `uv run pytest tests/services/test_handoff.py tests/services/test_cases.py -q` fails at collection with
   `ModuleNotFoundError: No module named 'meridian.services…'`. Anything else is a stop.

### Step 1 — `services/_case_rules.py`, then `tests/unit/services/test_case_rules.py`

Module docstring: "Pure case rules and staff display values (A6): allowed actions, refusals, due state, queue order,
oversight lanes, labels, masking. No I/O and no clock read; every time is an argument." Private
`_CHICAGO = ZoneInfo("America/Chicago")`.

1. `OWNER_LIFECYCLES = MappingProxyType({"start": frozenset({"claimed", "waiting"}), "wait": frozenset({"claimed",
   "in_progress"}), "resolve": frozenset({"claimed", "in_progress"}), "close_unresolved": frozenset({"claimed",
   "in_progress"}), "release": frozenset({"claimed", "in_progress", "waiting"}), "log_call": frozenset({"claimed",
   "in_progress"}), "log_email": frozenset({"claimed", "in_progress"})})`. This is derived from the representative
   examples CLAIMED, WAITING and LIVE_JOINED (STF-18 marks the supervisor examples illustrative).
2. `state_allows(action, *, lifecycle, owner_role, live_state, staffing, actor_role)`, with
   `mine = owner_role is not None and owner_role == actor_role`:
   - `claim` → `lifecycle in {"live_queued", "unassigned"}`.
   - `claim_and_join` → `lifecycle == "live_queued" and live_state == "queued" and staffing == "simulated_on_shift"`.
   - `join_chat` → `mine and live_state == "queued"`.
   - `send_live_message`, `hand_back`, `close_chat` → `mine and live_state == "joined"`.
   - any key of `OWNER_LIFECYCLES` → `mine and lifecycle in OWNER_LIFECYCLES[action]`.
   - `assign`, `change_priority` → `lifecycle not in CLOSED`.
   - `flag` → `True`.
   - anything else → `raise ValueError("unknown action")`.

   *Invariant:* one place decides what a state allows.
3. `actions_for(...)` → `tuple(a for a in ACTION_ORDER if a in ROLE_ACTIONS[actor_role] and state_allows(a, ...))`.
   The owner gets `()`. *Invariant:* the list is the table ∩ the role, in table order (= frozen `TABLE`, Appendix B).
4. `con13_refusal(action, *, lifecycle, owner_role, owner_since, actor_role)`. The first rule that matches wins:
   1. `action not in ROLE_ACTIONS[actor_role]` → `CaseActionRejected(code=ApiErrorCode.ROLE_NOT_ALLOWED,
      details={"role": actor_role.value, "needs": [r.value for r in (StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR)
      if action in ROLE_ACTIONS[r]], "reason": "wrong_role"})`.
   2. `lifecycle in CLOSED` → `NOT_ALLOWED_IN_STATE`, `details={"state": lifecycle, "needs": "open"}`.
   3. `action == "claim"`:
      - `lifecycle in {"claimed", "in_progress", "waiting"}` → `CASE_ALREADY_CLAIMED`,
        `details={"claimed_by": staff_name(owner_role.value) if owner_role else "System", "claimed_at":
        owner_since.isoformat() if owner_since else None}`;
      - otherwise `None`.
   4. `action in {"assign", "change_priority"}` → `None`.
   5. The owner-required actions (`start`, `wait`, `resolve`, `close_unresolved`, `release`):
      - `owner_role is None` → `NOT_ALLOWED_IN_STATE`, `details={"state": lifecycle, "needs": "claimed"}`;
      - `owner_role != actor_role` → `CASE_ALREADY_CLAIMED` with `claimed_by` / `claimed_at` as in 3;
      - `lifecycle not in OWNER_LIFECYCLES[action]` → `NOT_ALLOWED_IN_STATE`, `details={"state": lifecycle, "needs":
        " or ".join(sorted(OWNER_LIFECYCLES[action]))}`;
      - otherwise `None`.

   *Invariant:* for every CON-13 action, `con13_refusal(...) is None` **iff** the action is in `actions_for(...)`.
5. `missing_field_refusal(action, now)`. Strip strings first; a blank string counts as missing.
   - `action.action in {"release", "close_unresolved", "assign", "change_priority"}` without `reason` →
     `CaseActionRejected(code=REASON_REQUIRED, field="reason", constraint=f"required for {action.action}")`.
   - `wait` without `wake_up_at` → `WAKE_UP_REQUIRED`, `field="wake_up_at"`, `constraint="required for wait"`.
   - `wait` with `wake_up_at <= now` → `VALIDATION_ERROR`, `field="wake_up_at"`, `constraint="must be after the demo time"`.
   - `resolve` without `outcome` → `OUTCOME_REQUIRED`, `field="outcome"`, `constraint="required for resolve"`.
   - `assign` without `assignee` → `VALIDATION_ERROR`, `field="assignee"`, `constraint="required for assign"`.
   - `change_priority` without `priority` → `VALIDATION_ERROR`, `field="priority"`, `constraint="required for
     change_priority"`.
   - Otherwise `None`. `details` stays `None` (never echo a value).
6. `due_state(case_due, now)`:
   - `None` → `"no_due_time"`;
   - `case_due < now` → `"overdue"`;
   - `case_due - now <= DUE_SOON_WINDOW` → `"due_soon"`;
   - otherwise `"on_time"`.

   *Invariant:* overdue is a state, never a negative countdown.
7. Display maps (staff copy; each `Final` and `MappingProxyType`, with its source as a comment):
   - `PRIORITY_WORD = {P0: "Safety", P1: "Danger", P2: "Time-sensitive", P3: "Standard", P4: "Routine"}` [OpenAPI
     `Priority.word`].
   - `REASON_LABEL`, all 16 members [OpenAPI examples where they exist; the rest decided here, R-11]:
     safety "Safety report in chat", danger "Someone may be in danger", burning_unclear "Burning smell, risk unclear",
     burning_ruled_out "Burning smell, danger ruled out", customer_requested_person "Asked for a person", refund "Refund
     request", billing_dispute "Billing dispute", complaint_or_manager "Complaint or manager request",
     legal_or_chargeback "Legal or chargeback request", commercial "Commercial request", late_technician "Late
     technician", fee_bearing_change "Fee-bearing change request", membership_cancel "Membership cancellation",
     unsupported_action "Request the assistant can't complete", identity_unverified "Identity not confirmed",
     ai_failure "Assistant couldn't finish".
   - `SAFETY_KIND_LABEL = {"gas": "Gas smell reported in chat", "co": "CO alarm reported in chat", "sparks_smoke_flames":
     "Sparks, smoke or flames reported in chat", "burning_with_breaker": "Burning smell with a tripped breaker reported
     in chat"}`. Check the keys against `SafetyKind` values on `main` and use exactly those values.
   - `reason_label(reason, safety_kind=None)`: `SAFETY_KIND_LABEL[safety_kind]` when the reason is `SAFETY` and the
     kind is known; otherwise `REASON_LABEL[reason]`. Never the enum value.
   - `LIFECYCLE_WORD = {"live_queued": "Live-queued", "unassigned": "Unassigned", "claimed": "Claimed", "in_progress":
     "In progress", "waiting": "Waiting", "resolved": "Resolved", "closed_unresolved": "Closed unresolved"}`.
   - `WINDOW_WORD = {"morning": "mornings", "afternoon": "afternoons", "any": "any time"}`.
8. `follow_up_short(channel, window)`:
   - `None` when `channel is None`;
   - phone → `f"Phone · {WINDOW_WORD[window or 'any']}"`;
   - email → `"Email"` when `window in (None, "any")`, otherwise `f"Email · {WINDOW_WORD[window]}"`.

   [SEEDED "Phone · mornings", "Email"]
9. `clock_text(at)`:
   - a naive `at` → `ValueError("at must be timezone-aware")`;
   - otherwise `local = at.astimezone(_CHICAGO)`; `h = local.hour % 12 or 12`;
     `f"{h}:{local.minute:02d} {'am' if local.hour < 12 else 'pm'}"`.
10. `age_label(created_at, now, *, queued_at=None)`:
    - `queued_at is not None` → `f"Waiting since {clock_text(queued_at)}"`.
    - Otherwise compute `m = max(0, int((now - created_at).total_seconds() // 60))`:
      - `m < 60` → `f"Open {m} min"`;
      - `m < 1440` → `h, r = divmod(m, 60)`; `f"Open {h} h"` if `r == 0` else `f"Open {h} h {r} min"`;
      - otherwise `d, rest = divmod(m, 1440)`; `h = rest // 60`; `unit = "day" if d == 1 else "days"`;
        `f"Open {d} {unit}"` if `h == 0` else `f"Open {d} {unit} {h} h"`.

    [SEEDED "Open 4 min", "Open 6 min", "Open 1 day 4 h"]
11. `case_due_label(case_due, *, is_window_start)`:
    - `None` → `None`;
    - otherwise `due_label(case_due)`, plus `", the window start"` when `is_window_start` [AC-19].
12. `identity_view(identity, *, case_customer)` → `(status, line, demo_note)`. `demo_note = "Demo simulation"` always.
    - `status`:
      - `"verified"` when `identity.status == "verified" or case_customer` (RF-16);
      - otherwise `code_sent` → `code_sent`;
      - `located` → `code_sent` if `identity.codes_sent > 0` else `not_checked`;
      - `not_verified`, `locked`, `not_checked` → themselves.
    - Lines by status:
      - verified: "The customer entered the code sent to the phone on file. (Demo simulation. Not real ID proof.)";
      - code_sent: "A code was sent to the phone on file. The customer has not entered it yet. (Demo simulation.)";
      - not_checked: "The customer has not confirmed who they are in this chat.";
      - not_verified: "The customer could not be confirmed in this chat.";
      - locked: "Code entry is locked after too many tries. (Demo simulation.)".
13. `staff_name(actor_role)`: `STAFF_PERSONAS[StaffRole(actor_role)].name` for a staff role; `"System"` for `"ai"` and
    `"system"`.
14. `queue_key(priority, state, case_due, created_at, case_ref)` → `(tier, overdue, missing_due, due_ts, created_ts,
    case_ref)`, where:
    - `tier` = 0 for P0, 1 for P1, otherwise 2;
    - `overdue` = 0 when `state == "overdue"`, otherwise 1;
    - `missing_due` = 1 when `case_due is None`, otherwise 0;
    - `due_ts` = `case_due.timestamp()`, or `0.0` when there is no due.

    *Invariant:* P0, then P1, then overdue, then due ascending, then `created_at`; rows with no due come after dated ones.
15. `lane_for(priority, state, lifecycle, created_at, wake_up_at, now)`. The first rule that matches wins:
    - P0/P1 → `"p0_p1"`;
    - `"overdue"` → `"overdue"`;
    - `"due_soon"` → `"due_soon"`;
    - `lifecycle == "unassigned" and now - created_at >= UNOWNED_AFTER` → `"unowned"`;
    - `lifecycle == "waiting" and wake_up_at is not None and wake_up_at < now` → `"stuck_waiting"`;
    - otherwise `None`.
16. Promise status after an action:
    - `promise_status_after_resolve(due, now)`: `"kept"` when `due is None or now <= due`, otherwise `"missed"`.
    - `promise_status_after_activity(outcome, due, now, current)`:
      - `current` when `current not in {"open", "changed"}`;
      - `"kept"` when `outcome in {"reached", "left_message"}` and (`due is None` or `now <= due`);
      - otherwise `current`.
17. `fill_promise_text(promise, case_ref)`: `promise.text` when it contains no `{`; otherwise
    `promise.text.format(due_label=promise.due_label or "", case_ref=case_ref)`. Only `R26.unstaffed` carries the two
    placeholders. *Invariant:* the words are the table's.
18. `mask(text)` → `redact(text, RedactionProfile.SONNET).text`.

    `parse_seen(result_seen)` (RF-15):
    1. `s = result_seen.strip()`.
    2. If `s.startswith("{")`, try `json.loads(s)`; when that gives a `dict`, return it.
    3. Otherwise `pairs = re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s;,]+)", s)`. When `pairs` is non-empty, return
       `{k: int(v) if re.fullmatch(r"-?[0-9]+", v) else v for k, v in pairs}`.
    4. Otherwise return `{"seen": s}`.
19. `staffing_view(mode)`:
    - `nobody_online` → `StaffingView(mode=mode, label="Nobody online", banner=None)`;
    - `simulated_on_shift` → `StaffingView(mode=mode, label="Simulated staff on shift (demo)",
      banner=TEXTS[TextId.STAFFING_BANNER])`.

    [OpenAPI `Staffing` examples]

Write `tests/unit/services/test_case_rules.py` (§7.2) and run it (§7.3 A).

### Step 2 — `BriefAssembler` and `resolve_staff_guidance` in `services/handoff.py`, then `tests/unit/services/test_brief_assembler.py`

**`resolve_staff_guidance(prefixes, passages)`**: for each `reason, words in prefixes.items()` (in order) build
`tuple(next(g for g in passages if g.text.startswith(w)) for w in words)`. When a prefix matches no passage, raise
`ValueError(f"staff guidance prefix matches no passage: {reason.value}")`; the message names the reason, never the text.
Return a `MappingProxyType` of the result. *Invariant:* every mapped reason has exactly one passage per prefix, or
start-up fails (cases §5).

**`BriefAssembler(staff_guidance=None)`**: store `dict(staff_guidance or {})`. No I/O, no clock.

**`assemble(case, state, lookups) -> Brief`**:
- Build eight `BriefHeading`s from `BRIEF_TITLES`, `BRIEF_KEYS`, `BRIEF_ORIGINS` (index i → number i+1), with
  `checked = number != 4`, `trimmed=False`, `trim_note=None`, `not_generated=False`.
- Brief fields: `status="being_written"`, `assembled_at=state.turn_input.received_at`, `case_ref=case.case_ref`,
  `thread_id=state.thread_id`.
- Usable rows: `rows = [r for r in lookups if r.result_seen != "failed" and not r.result_seen.startswith("refused:")]`.
- Each item is `BriefItem(text, kind, sources=(…,), changed=False)`. **Every item has ≥ 1 source; an item that cannot be
  sourced is not added.**

1. **H1 why** (state): one `fact`, `f"{reason_label(case.reason, safety)}. Priority {case.priority.value}
   ({PRIORITY_WORD[case.priority]})."`.
   - `safety = state.gate.rules.safety.value` when `state.gate` and `state.gate.rules.safety` are set; otherwise `None`.
   - Source: `SourceRef(kind="rule", ref=rule)`. `rule = state.escalation.rule_id` when `state.escalation` is set and
     `state.escalation.reason == case.reason`; otherwise `case.reason.value`.
2. **H3 know** (state):
   - Each `AccountResult` with `status == "read"`:
     - each invoice `inv` → `fact` `f"Invoice {inv.invoice_id}: total {format_usd(inv.total_cents)}, balance
       {format_usd(inv.balance_cents)}, due {inv.due_on.isoformat()}."`, sourced on the first row whose `record_ids`
       contains `str(inv.invoice_id)`;
     - each `StaffNote` → `fact` with `text = note.text`, sourced on the first row whose `record_ids` contains
       `str(note.record_id)`. **Staff-only text enters only here, as a `lookup_log`-sourced item (AC-16).**
   - Each `KnowledgeResult` with `status == "answered"`: each point → `fact` `point.text`, sourced on the first row whose
     `passage_ids` contains `point.passage_id`.
   - "Sourced on row r" means `SourceRef(kind="lookup_log", ref=str(r.id))`.
3. **H5 ai_did** (state):
   - For each action in `state.settled.actions` (when `settled` is set), by kind:
     - `verified` → "Confirmed the customer with a code (demo simulation).";
     - `booked` → `f"Booked appointment {records['appointment']}."`;
     - `moved` → `f"Moved appointment {records['appointment']}."`;
     - `cancelled` → `f"Cancelled appointment {records['appointment']}."`;
     - `change_request_sent` → `f"Recorded a change request for appointment {records['appointment']}; the appointment
       itself was not changed."`;
     - skip `case_opened` and `followup_saved`.

     Use `.get("appointment", "")`, and skip an item whose record is missing. Kind `ai_action`; source
     `SourceRef(kind="action", ref=f"{a.kind.value}:{a.key.record_id}")`.
   - Then, for each usable row whose `tool != "staff_guidance"`: an `ai_action` item `f"Looked up {row_title(row)}."`,
     sourced on the row. `row_title` is a private function **in `_case_rules.py`**, shared with Step 6:
     - first record id matching `^INV-[0-9]{6}$` → `f"Invoice {rid}"`;
     - `^MHC-[0-9]{5}$` → `"Membership record"`;
     - `^[0-9]+$` → `f"Appointment {rid}"`;
     - otherwise, with passages, the file part of the first passage id (`pid.split("#")[0]`);
     - otherwise `row.tool`.
4. **H6 told** (state; the only producer of promise words, AC-5): when `case.promise.text != ""`, one `told_customer`
   item `fill_promise_text(case.promise, str(case.case_ref))`, then one `told_customer` item per `extra_lines` entry.
   Each has source `SourceRef(kind="policy_row", ref=case.promise.policy_row)`. Safety (`text == ""`) gives no items.
5. **H7 decide** (origin extraction; guidance is placed now so it shows while the brief is being written). For each usable
   row with `tool == "staff_guidance"`:
   - `pid = row.passage_ids[0] if row.passage_ids else None`; `g = self._guidance.get(pid) if pid else None`;
   - `text = g.text if g is not None and g.text_sha256 == row.result_seen else f"Staff guidance: {pid or 'unknown'}"`;
   - add a `fact` item with that text, sourced on the row.

   *Invariant (RF-14):* a guidance text is shown only when it is the passage that was logged.
6. **H8 who** (state):
   - `status, line, _ = identity_view(state.identity, case_customer=False)`.
   - One `fact` item `line`. Its source is `SourceRef(kind="action", ref=f"verified:{key.record_id}")` of the `VERIFIED`
     action when there is one; otherwise `SourceRef(kind="message", ref=str(state.turn_input.message_id))`.
   - When verified and `state.identity.customer_id` is set, add a second `fact` `f"Record
     {state.identity.customer_id}."` with the same source.
   - When `case.reason is SAFETY` and the identity is not verified, replace both with one `fact` "No account match needed
     for safety." [SCREEN_SPECS line 354], sourced on the message.
7. Headings 2 and 4 start empty.

**`attach_extraction(brief, extraction, check, *, customer_messages=None) -> Brief`** returns a new `Brief` (build new
headings, then `Brief.model_validate({...})` so the shape validator runs):

1. `extraction is None` → headings 2, 4 and 7 get `not_generated=True`, and the status is `"failed"`. Heading 7 keeps its
   guidance items. Return.
2. A quote is kept when `customer_messages is None or (q.message_id in customer_messages and q.text in
   customer_messages[q.message_id])`. A dropped quote marks its heading `trimmed=True`, `trim_note=TRIM_NOTE`.
3. H2: each kept need → `claim` `q.text`, source `SourceRef(kind="message", ref=str(q.message_id))`. H4: each kept claim,
   the same way (the heading stays `checked=False`).
4. H7 decision:
   - `text = (check.text if check is not None else extraction.open_decision).strip()`.
   - When non-empty, append one `decision` item after the guidance items. Its source is the first kept need's message;
     otherwise the first guidance row's `lookup_log` source; otherwise the item is not added.
   - When `check is not None and check.removals`, mark H7 `trimmed=True`, `trim_note=TRIM_NOTE`.
5. Status `"ready"`. **Never touch heading 6** (AC-5).

Write `tests/unit/services/test_brief_assembler.py` (§7.2) and run it.

### Step 3 — `CaseService` core in `services/cases.py`

The constructor stores `uow`, `clock`, `handoff_block`, `settled_view`. Private helpers:
`_rank(p) = int(p.value[1])`; `_actor_for(trigger) = "system" if trigger == "con4" else "ai"`;
`_alert(priority, reason) = "supervisor_now" if priority in {P0, P1} or reason is FEE_BEARING_CHANGE else None`.

**`open_case(tx, req, promise, now) -> HandoffResult`** runs in the caller's transaction and **never commits**.

1. `existing = tx.cases.cases.get_for_thread_open(req.thread_id)`. If it is set, take the **already-open path** (4).
2. **New case.** Keep this order: AC-1's failure test fails at the promise insert, after the case insert.
   1. Compute:
      - `ref = tx.cases.refs.next_case_ref()`;
      - `window_start = req.change_request.window_start if req.change_request else None`;
      - `case_due = case_due_at(req.reason, promise, window_start)`;
      - `lifecycle = "live_queued" if promise.live_queued else "unassigned"`;
      - `alert = _alert(req.priority, req.reason)`;
      - `customer_id = req.identity.customer_id if req.identity.status == "verified" else None` (O-14).
   2. Insert the case:
      `tx.cases.cases.insert(CaseRow(case_ref=ref, thread_id=req.thread_id, turn_id=req.turn_id,
      customer_id=customer_id, reason=req.reason, priority=req.priority, rule_id=req.rule_id, trigger=req.trigger,
      lifecycle=lifecycle, due_at=case_due, version=1, seed=False, safety_kind=req.safety_kind.value if
      req.safety_kind else None, change_request=req.change_request.model_dump(mode="json") if req.change_request else
      None, alert=alert, created_at=now, updated_at=now, queued_at=now if promise.live_queued else None))`.
      *Protects:* both dues are stored (CAS-10).
   3. `tx.cases.promises.insert(ref, promise, now)`.
   4. Append the case event: `tx.cases.case_events.append(CaseEventRow(case_ref=ref, kind="case_opened",
      actor_role=_actor_for(req.trigger), detail={"reason": req.reason.value, "priority": req.priority.value,
      "rule_id": req.rule_id, "trigger": req.trigger, "thread_id": str(req.thread_id), "turn_id": str(req.turn_id),
      "version": 1}, at=now))`.
   5. Record the action: `action = tx.core.actions.record(CompletedAction(key=ActionKey(thread_id=req.thread_id,
      turn_id=req.turn_id, kind=ActionKind.CASE_OPENED, record_id=str(ref)), kind=ActionKind.CASE_OPENED,
      records={"case": str(ref)}, at=now))`.
   6. Append the stream event: `tx.core.events.append(thread_stream(req.thread_id), StreamEvent(type="case_created",
      payload={"case_ref": str(ref), "thread_id": str(req.thread_id), "turn_id": str(req.turn_id), "reason":
      req.reason.value, "priority": req.priority.value, "lifecycle": lifecycle}, at=now))` (O-11).
   7. When `promise.live_queued`: `tx.core.conversations.set_live_state(req.thread_id, "queued", now)`.
   8. Return `HandoffResult(case=self._summary(tx, ref), created=True, action=action, alert=alert)`.
3. **`_summary(tx, ref) -> CaseSummary`**:
   - `row = tx.cases.cases.get(ref)`; `prow = tx.cases.promises.current(ref)`; `f = tx.cases.followups.get(ref)`.
   - If `row` or `prow` is `None`, raise `LookupError("case row missing")`.
   - Return `CaseSummary(case_ref=row.case_ref, reason=row.reason, priority=row.priority, state=row.lifecycle,
     created_at=row.created_at, promise=prow.promise, followup=None if f is None else FollowUp(channel=f.channel,
     destination_label=f.destination_label, on_record=f.on_record, window=f.window, saved_line=f.saved_line),
     version=row.version, seed=row.seed, due_at=row.due_at)`.
4. **Already-open path** (AC-2), with `ref = existing.case_ref`:
   1. `seen = {existing.reason} | {HandoffReason(e.detail["reason"]) for e in tx.cases.case_events.list_for_case(ref)
      if e.kind == "reason_added" and isinstance(e.detail.get("reason"), str)}`.
   2. When `req.reason not in seen`:
      - `raise_to = req.priority if _rank(req.priority) < _rank(existing.priority) else None`.
      - When `raise_to` is set:
        - `v = tx.cases.cases.update_versioned(ref, existing.version, priority=raise_to, alert=_alert(raise_to,
          existing.reason) or existing.alert, updated_at=now)`;
        - `v is None` → `raise RuntimeError("case changed during handoff")`;
        - then append `StreamEvent(type="case_changed", payload={"version": v, "lifecycle": existing.lifecycle},
          at=now)` to `case_stream(ref)`.
      - Append **one** `CaseEventRow(case_ref=ref, kind="reason_added", actor_role=_actor_for(req.trigger),
        detail={"reason": req.reason.value, "priority": req.priority.value, "rule_id": req.rule_id, "trigger":
        req.trigger, "turn_id": str(req.turn_id), "priority_from": existing.priority.value, "priority_to": (raise_to or
        existing.priority).value, "version": v if raise_to else existing.version}, at=now)`.
   3. The same reason, or the same `turn_id` repeated: **no write at all**.
   4. `action` = the `CASE_OPENED` action in `tx.core.actions.for_thread(req.thread_id)` whose `key.record_id ==
      str(ref)`. If there is none (a seed without an action row), build `CompletedAction(key=ActionKey(thread_id=
      req.thread_id, turn_id=existing.turn_id or req.turn_id, kind=CASE_OPENED, record_id=str(ref)), kind=CASE_OPENED,
      records={"case": str(ref)}, at=existing.created_at)` **without** recording it.
   5. `summary = self._summary(tx, ref)`; return `HandoffResult(case=summary, created=False, action=action,
      alert=_alert(summary.priority, req.reason))`.

   *Protects:* one open case per thread; no second `cases`, `actions` or guidance row; CON-4 is never refused (M-15).
5. **`attach_brief(case_ref, brief)`**:
   - `brief.case_ref != case_ref` → `ValueError("brief belongs to another case")`.
   - In `with self._uow(write=True) as tx:`, an unknown case → `ValueError("unknown case")`.
   - `tx.cases.briefs.upsert(brief, self._clock.now())`; `tx.commit()`.
6. **`open_case_for_thread(thread_id)`**: in a read-only `with self._uow() as tx:`, return `None` when
   `get_for_thread_open` returns `None`; otherwise `self._summary(tx, row.case_ref)`.

### Step 4 — `HandoffService` in `services/handoff.py`

```python
class _PresenceSource(Protocol):    # typing only (O-12); AEA-30's DemoService and the container forwarder fit it
    def presence(self, tx: UnitOfWork | None = None) -> Presence: ...
```

Import `StaffGuidance` and `CaseService` under `if TYPE_CHECKING:`. The constructor stores everything;
`staff_guidance` becomes `dict(staff_guidance or {})`.

**`open(req, ctx) -> HandoffResult`**:

1. `now = ctx.now` (the one demo-clock reading of the turn, graph-core §2);
   `window_start = req.change_request.window_start if req.change_request else None`.
2. Attempt loop:
   ```python
   last: Exception | None = None
   for _attempt in (1, 2):
       try:
           with self._uow(write=True) as tx:
               result = self._open_in(tx, req, now, window_start)
               tx.commit()
           return result
       except Exception as exc:  # noqa: BLE001 - any failed write is retried once (DO-1 §8.2)
           last = exc
   raise CaseWriteFailed(attempts=2) from last
   ```
   *Protects:* nothing half-written (the unit of work rolls back on exit); one retry; a typed failure with no value in
   its message.
3. `_open_in(tx, req, now, window_start)`:
   1. `presence = self._demo.presence(tx)`, read **inside** the transaction.
   2. `promise = promise_for(req.reason, presence, now, window_start)`: the only promise source (AC-5).
   3. `result = self._cases.open_case(tx, req, promise, now)`.
   4. When `result.created` and `self._staff_guidance.get(req.reason)`:
      - read `anchor = tx.core.messages.handoff_anchor(req.thread_id)` once;
      - for each `g` in order, `tx.core.lookup_log.append(LookupEntry(tool="staff_guidance", record_ids=(),
        passage_ids=(g.passage_id,), result_seen=g.text_sha256, message_id=anchor, turn_id=req.turn_id))`.
   5. Return `result`. **Write no `turns` row** (web.md §8).

### Step 5 — `convert_live_queued(now, tx=None)` (AC-8)

1. `tx is None` → `with self._uow(write=True) as own: n = self._convert(own, now); own.commit(); return n`. Otherwise
   `return self._convert(tx, now)`, and **never** commit the caller's transaction.
2. `_convert(tx, now)`: for each `row` in `tx.cases.cases.list_open()` with `row.lifecycle == "live_queued"`, with
   `ref = row.case_ref`:
   1. `window_start = dt.datetime.fromisoformat(cr["window_start"])` when `cr = row.change_request` is set and
      `cr.get("window_start")` is a `str`; otherwise `None`.
   2. `new = promise_for(row.reason, "nobody_online", now, window_start)`;
      `case_due = case_due_at(row.reason, new, window_start)`.
   3. Promise rows, in order:
      1. `tx.cases.promises.set_status(ref, "changed", now, "shift_ended")` marks the old row.
      2. `tx.cases.promises.insert(ref, new, now)`.
      3. `tx.cases.promises.set_status(ref, "changed", now, "shift_ended")` marks the new current row.
   4. `v = tx.cases.cases.update_versioned(ref, row.version, lifecycle="unassigned", due_at=case_due, updated_at=now)`.
      `None` → `RuntimeError("case changed during shift end")`. `case_ref`, `created_at` and `queued_at` stay untouched.
   5. `tx.core.conversations.set_live_state(row.thread_id, "not_live", None)`.
   6. Append `CaseEventRow(case_ref=ref, kind="converted", actor_role="system", detail={"reason": "shift_ended",
      "policy_row": new.policy_row, "promise_status": "changed", "version": v}, at=now)`.
   7. Build the result and the payload parts:
      - `result = HandoffResult(case=self._summary(tx, ref), created=False, action=<the case_opened action, as
        Step 3.4.4>, alert=None)`.
      - `block = self._handoff_block(result) if self._handoff_block is not None else None`.
      - Read `conv = tx.core.conversations.lookup(str(row.thread_id))`.
      - `controller = conv.controller if isinstance(conv, ConversationRow) else Controller(kind="ai")`.
      - `settled = self._settled_view(tx.core.settled_for(row.thread_id, now),
        tx.core.reads.identity_state(row.thread_id), controller) if self._settled_view is not None else None`.
   8. Append the events:
      - Thread stream: `StreamEvent(type="shift_ended", payload=payload, at=now)`, where `payload = {"speaker": {"kind":
        "event", "display_name": None}, "line": TEXTS[TextId.SHIFT_ENDED], "handoff": block.model_dump(mode="json") if
        block is not None else None}`, plus `payload["settled"] = settled.model_dump(mode="json")` when `settled` is
        set. (RF-13: `EvShiftEnded` keys; never add other keys.)
      - Case stream: `StreamEvent(type="case_changed", payload={"version": v, "lifecycle": "unassigned"}, at=now)`,
        then `StreamEvent(type="chat_closed", payload={"reason": "shift_ended"}, at=now)`.
   9. Count it.
3. Return the count.

The composer is called **inside** the transaction. It is pure (no I/O, no model call), so DO-3 §2.3 rule 1 (no
transaction across a model call) holds.

### Step 6 — views: `services/_case_views.py`, then `queue`, `detail`, `oversight` in `cases.py`

All three open **one read-only** unit of work (`with self._uow() as tx:`) and read everything inside it.
`staffing = tx.cases.demo_state.get().staffing`.

1. **`live_state_of(tx, thread_id) -> tuple[str, ConversationRow | None]`**: `conv = tx.core.conversations.lookup(str(thread_id))`;
   returns `(conv.live_state, conv)` for a `ConversationRow`, otherwise `("not_live", None)`.
2. **`is_window_start(row)`**: `row.change_request` holds a `window_start` string, and `row.due_at ==
   dt.datetime.fromisoformat(it)`.
3. **`queue_row(tx, row, now) -> QueueRow`**. Read `f = tx.cases.followups.get(row.case_ref)`,
   `brief = tx.cases.briefs.get(row.case_ref)`, and
   `customer = tx.core.reads.customer(row.customer_id) if row.customer_id else None`. Fields:
   - `reference=str(row.case_ref)`;
   - `priority=PriorityView(level=row.priority, word=PRIORITY_WORD[row.priority])`;
   - `reason=reason_label(row.reason, row.safety_kind)`;
   - `customer_display_name=customer.name if customer else "No name given"` [SEEDED];
   - `owner=staff_name(row.owner_role.value) if row.owner_role else None`;
   - `created_at=row.created_at`, `due_at=row.due_at`;
   - `due_label=case_due_label(row.due_at, is_window_start=is_window_start(row))`;
   - `due_state=due_state(row.due_at, now)`;
   - `wake_up_at=row.wake_up_at`, `lifecycle=row.lifecycle`;
   - `follow_up_short=follow_up_short(f.channel if f else None, f.window if f else None)`;
   - `seed=row.seed`;
   - `brief_status=brief.status if brief else "being_written"`;
   - `queued_at=row.queued_at if row.lifecycle == "live_queued" else None`;
   - `age_label=age_label(row.created_at, now, queued_at=<the same queued_at>)`.

   **No phone, email or address field exists on a row** (AC-13).
4. **`summary_view(tx, row, actor_role, staffing, now) -> CaseSummaryView`**:
   - `reference`, `reason`, `priority`, `lifecycle`, `owner`, `created_at`, `due_at`, `due_label`, `due_state`,
     `wake_up_at`: as in 3;
   - `promise_status=tx.cases.promises.current(row.case_ref).status`;
   - `seed`, `version=row.version`;
   - `allowed_actions=actions_for(lifecycle=row.lifecycle, owner_role=row.owner_role, live_state=live_state_of(tx,
     row.thread_id)[0], staffing=staffing, actor_role=actor_role)`.
5. **`queue(role, now)`**: `rows = tx.cases.cases.list_open()`.
   - `live`: the rows with lifecycle `live_queued`, only when `staffing == "simulated_on_shift"` (otherwise `()`).
     Sort by `(0 if P0 else 1 if P1 else 2, (row.queued_at or row.created_at).timestamp(), str(row.case_ref))`.
   - `needs`: `[r for r in rows if r.lifecycle != "live_queued" and r.owner_role in (None, role)]`, sorted by
     `queue_key(...)`.
   - Return `QueueView(as_of=now, staffing=staffing_view(staffing), live=tuple(...), needs_my_action=tuple(...))`.
6. **Sources: `case_sources(tx, lookups, brief) -> tuple[CaseSource, ...]`**. Skip `failed` and `refused:*` rows. For each
   remaining row `r`, in id order:
   - `source_id = f"src-{r.id}"`, `lookup_log_id = f"ll-{r.id}"` (O-9).
   - `tool == "staff_guidance"`:
     - `audience="staff_only"`, `title="Agent discretion notes"`, `ref="internal/agent_discretion_notes.md"`,
       `version_date=None`, `version_label="undated"`;
     - `snapshot = {"passage": <the text of the first brief item whose sources include ("lookup_log", str(r.id))>}`,
       or `{"passage_id": str(r.passage_ids[0])}` when no brief item cites it;
     - `current = snapshot`, `changed_since=False`, `changed_note="No change since the snapshot"`,
       `current_unavailable=False`.
   - Otherwise `audience="customer"`, `snapshot = parse_seen(r.result_seen)`, `rid = r.record_ids[0] if r.record_ids
     else None`:
     - `rid` matches `^INV-[0-9]{6}$` → `inv = tx.core.reads.invoice(InvoiceId(rid))`; `title=f"Invoice {rid}"`,
       `ref=f"invoices/{rid}"`; `current = None if inv is None else {"amount_cents": inv.amount_cents,
       "balance_cents": inv.balance_cents, "issued_date": inv.issued_date.isoformat(), "due_date":
       inv.due_date.isoformat(), "appointment_id": inv.appointment_id}`.
     - `^MHC-[0-9]{5}$` → `c = tx.core.reads.customer(CustomerId(rid))`; `title="Membership record"`,
       `ref=f"customers/{rid}"`; `current = None if c is None else {"membership_tier": c.membership_tier,
       "membership_renewal_date": c.membership_renewal_date.isoformat() if c.membership_renewal_date else None}`.
       **Never** name, phone, email or address (AC-13).
     - `^[0-9]+$` → `a = tx.core.reads.appointment(int(rid))`; `title=f"Appointment {rid}"`, `ref=f"appointments/{rid}"`;
       `current = None if a is None else {"slot_date": a.slot_date.isoformat(), "window": a.window, "status":
       a.status, "service_type": a.service_type, "technician": a.technician}`.
     - No record id but passages → `title = ref = r.passage_ids[0].split("#")[0]`; `current=None`.
     - Neither → `title = ref = r.tool`; `current=None`.
     - Version fields: records get `version_date=None` and `version_label="live record"`. Passages get
       `version_label = snapshot["version_label"]` when it is a `str`, otherwise `"undated"`, and `version_date` =
       `dt.date.fromisoformat(snapshot["version_date"])` when that parses, otherwise `None`.
     - Change fields:
       - `current is None` → `current_unavailable=True`, `changed_since=False`, `changed_note=None`;
       - otherwise `changed_since = any(k in current and current[k] != v for k, v in snapshot.items())`,
         `changed_note = "Changed since the AI saw it" if changed_since else "No change since the snapshot"`,
         `current_unavailable=False`.
   - Every `str` leaf of `snapshot` and `current` passes through `mask` (O-10). A private `_mask_tree(value)` recurses
     dicts and lists.
7. **Brief view `brief_view(brief, changed_ids) -> BriefView`**:
   - No stored brief → `BriefView(status="being_written", headings=<eight BriefHeadingView with items=(),
     checked=number != 4, trimmed=False, trim_note=None, not_generated=False>)`.
   - Otherwise each heading → `BriefHeadingView(number, key, title, checked, items=tuple(BriefItemView(text=mask(i.text),
     kind=i.kind, source_ids=tuple(f"src-{s.ref}" for s in i.sources if s.kind == "lookup_log"), changed=any(
     f"src-{s.ref}" in changed_ids for s in i.sources if s.kind == "lookup_log")) for i in h.items), trimmed, trim_note,
     not_generated)`.

   *Protects:* every chip resolves to a source of the same `CaseDetail`.
8. **Conversation**: one `ChatLineView(message_id=str(m.id), speaker=Speaker(kind=..., display_name=...), at=m.at,
   text=mask(m.text))` per row of `tx.core.messages.all_for_thread(thread_id)`. Speakers by `m.role`:
   - `customer` → `Speaker(kind="customer", display_name=CUSTOMER_SPEAKER_NAME)`;
   - `assistant` → `Speaker(kind="assistant", display_name="Meridian assistant")` [OpenAPI DEFAULT];
   - `representative` → `Speaker(kind="representative", display_name=STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name)`.

   *Protects:* AC-20 ("Customer", never "You" or a name) and AC-13 (contacts masked).
9. **Promise record**:
   - `prow = tx.cases.promises.current(ref)` and `f = tx.cases.followups.get(ref)`.
   - Build `PromiseRecord(text=fill_promise_text(prow.promise, str(ref)), due_at=prow.promise.due_at,
     due_label=prow.promise.due_label, policy_row=prow.promise.policy_row, status=prow.status, follow_up=...,
     history=...)`.
   - `follow_up` = `None` when there is no follow-up; otherwise `PromiseFollowUp(channel=f.channel,
     destination_label=f.destination_label, on_record=f.on_record, window=f.window)`.
   - `history` = `tuple(PromiseHistoryItem(at=h.status_at or h.created_at, text=fill_promise_text(h.promise, str(ref)),
     reason=h.status_reason or "changed") for h in tx.cases.promises.history(ref) if h.id != prow.id)`.
10. **Activities**: `Activity(activity_id=f"act-{a.id}", kind=a.kind, outcome=a.outcome, note=mask(a.note) if a.note else
    None, at=a.at, by=STAFF_PERSONAS[a.actor_role].signature, label="Demo: recorded, not sent")`. The label value is
    `TEXTS[TextId.RECORDED_NOT_SENT]`; assert at import that it equals the literal.
11. **`detail(case_ref, role, now)`**:
    - `row = tx.cases.cases.get(case_ref)`; `None` → `raise CaseNotFound(str(case_ref))`.
    - Read `live_state, conv = live_state_of(tx, row.thread_id)`, `identity = tx.core.reads.identity_state(row.thread_id)`,
      `lookups = tx.core.lookup_log.for_thread(row.thread_id)`, `brief = tx.cases.briefs.get(case_ref)`,
      `sources = case_sources(tx, lookups, brief)`, `changed_ids = {s.source_id for s in sources if s.changed_since}`.
    - `status, line, note = identity_view(identity, case_customer=row.customer_id is not None)`.
    - Return `CaseDetail(...)` with:
      - `case=summary_view(tx, row, role, staffing, now)`;
      - `promise=<9>`;
      - `brief=brief_view(brief, changed_ids)`;
      - `identity=CaseIdentityView(status=status, line=line, demo_note=note)`;
      - `sources=sources`;
      - `conversation=<8>`;
      - `activities=<10, in id order>`;
      - `live=LiveStateView(state=live_state, since=conv.live_since if conv else None, controller=conv.controller.kind
        if conv else "ai")`;
      - `other_cases=tuple(OtherCase(reference=str(o.case_ref), status=LIFECYCLE_WORD[o.lifecycle]) for o in
        tx.cases.cases.list_for_customer(row.customer_id) if o.case_ref != row.case_ref) if row.customer_id else ()`;
      - `agent_version=conv.agent_version if conv else "unknown"`;
      - `as_of=now`.
    - **Do not build `events` (AC-23 is blocked).**
12. **`oversight(now)`**:
    - `rows = list_open()`; each row gets `lane = lane_for(...)`.
    - Group the rows by lane into `OversightLanes(**{name: Lane(count=n, rows=<QueueRows sorted by queue_key>) for name
      in LANE_ORDER})`, keeping empty lanes.
    - `alerts = tuple(Alert(type="overdue", case_ref=str(r.case_ref), line=render(TextId.OVERSIGHT_OVERDUE,
      case_ref=str(r.case_ref)), at=r.due_at) for r in <overdue-lane rows>)`. Other alert types wait on R-5.
    - `live_queue_length` = the number of `live_queued` rows when staffing is on shift, otherwise 0.
    - `new_flags_count=tx.core.reads.new_flags_count()`.
    - Return `OversightView(as_of=now, demo_now=now, staffing=staffing_view(staffing), alerts=alerts, lanes=lanes,
      live_queue_length=..., new_flags_count=...)`.

### Step 7 — `apply(case_ref, action, actor, expected_version, now)` (AC-9, AC-10, AC-18)

One `with self._uow(write=True) as tx:`. **Every rejection returns without `tx.commit()`**: the exit rolls back and
nothing changes. **The `expected_version` parameter decides; `action.expected_version` is ignored.** Check in this order:

1. `row = tx.cases.cases.get(case_ref)`; `None` → `CaseActionRejected(code=CASE_NOT_FOUND, details={"reference":
   str(case_ref)})`.
2. Role: `action.action not in ROLE_ACTIONS[actor.role]` → the `ROLE_NOT_ALLOWED` rejection of
   `con13_refusal(action.action, …)`.
3. Required fields: `missing_field_refusal(action, now)`.
4. Version: `expected_version != row.version` → `CaseActionRejected(code=VERSION_CONFLICT, details={"changed_by":
   staff_name(e.actor_role), "changed_at": e.at.isoformat(), "current_version": row.version})`. `e` is the newest
   `case_events` row whose `detail.get("version") == row.version`; if there is none, the newest row; if there are no
   rows, use `changed_by="System"`, `changed_at=row.updated_at.isoformat()`.
5. State: `con13_refusal(action.action, lifecycle=row.lifecycle, owner_role=row.owner_role,
   owner_since=row.owner_since, actor_role=actor.role)` → reject with it.
6. Changes (every change also sets `updated_at=now`):
   - claim → `lifecycle="claimed", owner_role=actor.role, owner_since=now`;
   - release → `lifecycle="unassigned", owner_role=None, owner_since=None, wake_up_at=None`;
   - start → `lifecycle="in_progress", wake_up_at=None`;
   - wait → `lifecycle="waiting", wake_up_at=action.wake_up_at`;
   - resolve → `lifecycle="resolved", resolved_at=now, wake_up_at=None`;
   - close_unresolved → `lifecycle="closed_unresolved", resolved_at=now, wake_up_at=None`;
   - assign → `owner_role=ASSIGNEE_ROLES[action.assignee], owner_since=now, lifecycle="claimed", wake_up_at=None`;
   - change_priority → `priority=action.priority`.

   Then `v = tx.cases.cases.update_versioned(case_ref, expected_version, **changes)`. `None` → the
   `VERSION_CONFLICT` rejection of 4, re-reading the row.
7. Resolve and close_unresolved: `prow = tx.cases.promises.current(case_ref)`.
   - For **resolve** only, when `prow.status in {"open", "changed"}`: `new = promise_status_after_resolve(prow.promise.due_at,
     now)`, then `tx.cases.promises.set_status(case_ref, new, now, "resolved")`.
   - `close_unresolved` leaves the promise alone.
8. Append **one** `CaseEventRow(case_ref=case_ref, kind=f"action:{action.action}", actor_role=actor.role.value,
   detail=...)`. The detail holds `{"action": action.action, "version": v}`, plus each of these that is not `None`:
   - `"reason": mask(reason)`, `"outcome": mask(outcome)`;
   - `"wake_up_at": iso`;
   - `"assignee": ASSIGNEE_ROLES[...].value`;
   - `"priority_from"` / `"priority_to"` (change_priority);
   - `"promise_status_to": new`.
9. Append `StreamEvent(type="case_changed", payload={"version": v, "lifecycle": <new lifecycle>}, at=now)` to
   `case_stream(case_ref)`.
10. Re-read the row; build `summary_view(tx, row, actor.role, staffing, now)`; `tx.commit()`; return it.

*Protects:* listed ⇔ accepted (Step 1.2–1.5); one `case_event` per change with the actor role; version + 1; ownership
stored as a role and rendered through `STAFF_PERSONAS`.

### Step 8 — `set_followup` and `record_activity` (AC-12, AC-13, AC-14, AC-10)

**`set_followup(thread_id, choice, now)`**, in one write unit of work:

1. `row = tx.cases.cases.get_for_thread_open(thread_id)`; `None` → `CaseActionRejected(code=NOT_ALLOWED_IN_STATE,
   details={"state": "no_open_case"})`.
2. `identity = tx.core.reads.identity_state(thread_id)`. When `choice.destination == "on_record" and identity.status !=
   "verified"`, return the same code with `details={"state": "not_verified"}` (WEB-23, R-27).
3. Label and saved line (customer-facing; only contract-given formats):
   - phone + on_record:
     - `customer = tx.core.reads.customer(identity.customer_id)` (`None` → reject as in 2);
     - `digits = re.sub(r"[^0-9]", "", customer.phone)[-2:]`;
     - `destination_label = f"the number ending in {digits}"` [OpenAPI `FollowUpView.destination_label`; CON-5];
     - `saved_line = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window=WINDOW_WORD[choice.window])`.
   - email + on_record, and every `general` destination: `raise NotImplementedError("follow-up text for email/general:
     blocked-on AEA-03 follow-up (UX wording)")` (O-15, R-5). This happens before any write.
4. `tx.cases.followups.upsert(FollowupRow(case_ref=row.case_ref, thread_id=thread_id, channel=choice.channel,
   destination_label=destination_label, destination=choice.destination, on_record=choice.destination == "on_record",
   window=choice.window, saved_line=saved_line, updated_at=now))`. **`destination` stores the choice word
   (`on_record` / `general`), never the phone or email** (AC-13).
5. Append one `CaseEventRow(case_ref=row.case_ref, kind="followup_saved", actor_role="system", detail={"channel":
   choice.channel, "on_record": …, "window": choice.window}, at=now)`. No version change. `tx.commit()`.
6. Return `FollowUp(channel=..., destination_label=..., on_record=..., window=..., saved_line=...)`.

**`record_activity(case_ref, activity, actor, now)`**, in one write unit of work:

1. Checks, in order:
   - Unknown case → `CASE_NOT_FOUND`.
   - `key = "log_call" if activity.kind == "call" else "log_email"`.
   - `key not in ROLE_ACTIONS[actor.role]` → `ROLE_NOT_ALLOWED` with `details={"role": actor.role.value, "needs":
     ["representative"], "reason": "wrong_role"}`.
   - `activity.expected_version != row.version` → `VERSION_CONFLICT`, built as in Step 7.4.
   - `not state_allows(key, lifecycle=row.lifecycle, owner_role=row.owner_role, live_state=<live_state_of>,
     staffing=<demo_state>, actor_role=actor.role)`:
     - `row.owner_role is None` → `NOT_ALLOWED_IN_STATE` with `details={"state": row.lifecycle, "needs": "claimed"}`;
     - another role owns it → `CASE_ALREADY_CLAIMED`;
     - otherwise → `NOT_ALLOWED_IN_STATE` with `details={"state": row.lifecycle, "needs": "claimed or in_progress"}`.
2. `aid = tx.cases.activities.insert(ActivityRow(case_ref=case_ref, kind=activity.kind, outcome=activity.outcome,
   note=mask(activity.note) if activity.note else None, actor_role=actor.role, at=now))`.
3. Promise: `prow = current(case_ref)`; `new = promise_status_after_activity(activity.outcome, prow.promise.due_at, now,
   prow.status)`. When `new != prow.status`, call `set_status(case_ref, new, now, f"activity:{activity.outcome}")`.
4. Version and events:
   - `v = update_versioned(case_ref, activity.expected_version, updated_at=now)`; `None` → `VERSION_CONFLICT`.
   - Append one `CaseEventRow(kind="activity", actor_role=actor.role.value, detail={"kind": …, "outcome": …,
     "version": v}, plus "promise_status_to": new only when it changed)`. No note text in the event.
   - Append `case_changed` to the case stream.
5. Return `ActivityResult(activity=Activity(activity_id=f"act-{aid}", kind=…, outcome=…, note=<masked note>, at=now,
   by=actor.signature, label="Demo: recorded, not sent"), case=summary_view(tx, <re-read row>, actor.role, staffing,
   now))` after `tx.commit()`.

*Protects:* R-34. The label is on every activity, and no "sent you", "emailed you" or "called you" wording appears.

### Step 9 — the `register_cases` hunk in `web/container.py`, then `tests/unit/web/test_register_cases.py`

Replace only the `register_cases` function. Docstring (verbatim; it must contain "AEA-29" and must **not** contain
"No-op until"):

```
AEA-29 cases and handoff: CaseService, HandoffService, BriefAssembler (cases.md §5).

Provides deps.CASE_SERVICE ("case_service"), deps.HANDOFF_SERVICE ("handoff_service") and Key("brief_assembler") over
Key("uow_factory") (AEA-10). Siblings are read through forwarders only when a method needs them, so the app builds
before they are bound: Key("demo_clock") and deps.DEMO_SERVICE (AEA-30), deps.REPLY_COMPOSER (AEA-51); until then the
call raises RuntimeError("not bound: <key>"). Staff guidance: STAFF_GUIDANCE_FOR's prefixes are resolved against
load_staff_guidance(settings.index_dir) when the container builds; with no staff_notes.json there is no guidance (one
warning, no values), and a prefix that matches no passage fails start-up. An app that create_app did not build has no
web shell, so this does nothing.
```

Body. Every import goes **inside** the function (`test_container_imports_only_policy_limits`).

1. Import `logging`, `Path`, `MappingProxyType`, `HandoffReason`, `STAFF_GUIDANCE_FOR`, `CaseService`,
   `BriefAssembler`, `HandoffService`, `resolve_staff_guidance`, `CASE_SERVICE`, `HANDOFF_SERVICE`, `DEMO_SERVICE`,
   `REPLY_COMPOSER`, `UOW_FACTORY`, `WebShellState`.
2. `if not isinstance(getattr(app.state, "web_shell", None), WebShellState): return`.
3. `def _bound(key: Key[Any]) -> Any:` → `container.get(key)`. A `ContainerError` whose `str` is
   `f"not provided: {key.name}"` becomes `RuntimeError(f"not bound: {key.name}") from None`; any other error re-raises.
4. Forwarders, each a small class or function in the hunk, typed:
   - `_DemoClock.now()` → `_bound(Key[Any]("demo_clock")).now()`.
   - `_Presence.presence(tx=None)` → `_bound(DEMO_SERVICE).presence(tx)`.
   - `_handoff_block(result)` → `_bound(REPLY_COMPOSER).handoff_block(result)`.
   - `_settled_view(settled, identity, controller)` → `_bound(REPLY_COMPOSER).settled_view(settled, identity,
     controller)`.
5. Staff guidance, read once when the container builds HANDOFF_SERVICE:
   - `index_dir = getattr(settings, "index_dir", None)`.
   - If `index_dir is None or not (Path(index_dir) / "staff_notes.json").is_file()`: `passages = ()` and log
     `logging.getLogger(__name__).warning("staff_guidance_unavailable")`.
   - Otherwise `from meridian.retrieval.ingest import load_staff_guidance` and `passages =
     load_staff_guidance(Path(index_dir))`.
   - `by_reason = resolve_staff_guidance(STAFF_GUIDANCE_FOR, passages) if passages else MappingProxyType({})`. A
     `ValueError` propagates and fails `build()`, as cases §5 requires.
   - Do this in a helper `_guidance()` that returns `(by_reason, by_id)` with `by_id = {g.passage_id: g for g in
     passages}`, cached in a local `dict` so both providers share one read.
6. Provide:
   - `container.provide(CASE_SERVICE, lambda c: CaseService(c.get(UOW_FACTORY), _DemoClock(),
     handoff_block=_handoff_block, settled_view=_settled_view))`;
   - `container.provide(Key[Any]("brief_assembler"), lambda c: BriefAssembler(staff_guidance=_guidance()[1]))`;
   - `container.provide(HANDOFF_SERVICE, lambda c: HandoffService(c.get(UOW_FACTORY), c.get(CASE_SERVICE), _Presence(),
     _DemoClock(), staff_guidance=_guidance()[0]))`.

   Type the keys as in the sibling hunks (`Key[Any]`).

Write `tests/unit/web/test_register_cases.py` (§7.2) and run it, together with `tests/unit/web/test_container.py`.

### Step 10 — `tests/services/test_cases_contract.py` (seed, wire schemas, stream rows)

Write it (§7.2). It proves three things:
- AEA-31's real seed assembles with the real assembler (O-21);
- every view validates against the signed response schema (AC-19);
- the stored stream rows validate against the signed event schemas (O-6, O-11).

### Step 11 — journeys (AC-22)

Write `tests/journeys/j6/test_aea_29.py` and `tests/journeys/j7/test_aea_29.py` (§7.2). Each has
`pytestmark = pytest.mark.journey` and a module docstring stating:
"Level today: mock-tested (real services on a temp SQLite copy of the issued DB; real LiveChatService in J-7; no
server, no model). Integrated level blocked by AEA-30 (demo clock and DemoService), AEA-45 (getQueue/getCase routes) and
AEA-52 (integrated staff side)."

### Step 12 — record and context (AC-22, AC-24)

1. Write `docs/testing/journeys/<YYYY-MM-DD>-AEA-29.md` with every `integrated-journeys.md` §4 field:
   - Claim: "J-6 (escalated case in queue and case view: eight headings, policy promise, accepted `allowed_actions`,
     resolving `source_ids`) and J-7 (live takeover through the real LiveChatService keeps the case version), AEA-29".
   - Level: `mock-tested`.
   - Tested revision: the commit SHA.
   - Environment: `temp_sqlite()` copy of the issued DB, `FixedClock`, no server, no model.
   - Command: §7.3 E.
   - Result: pass/fail per file.
   - Evidence location: the implementer's report.
   - Remaining limitations: no HTTP, no browser, AC-23 skipped, email/general follow-up stub.
   - **Blocked by:** AEA-30, AEA-45, AEA-52, plus the UX session's OpenAPI amendment for AC-23.
2. `.claude/reference/area-map.md`: in the **first** A6 row (the one that already mentions `services/reset.py`), append
   `; services/cases.py, services/handoff.py (+ _case_rules.py, _case_views.py) actual (AEA-29, <sha>)` to the *Status*
   cell. Do not remove the duplicate second A6 row; that is wave-2 finding 9's ticket.
3. `.claude/state/icm-progress.md`: append one row after the last *Routes verified* row: `| Routes verified against code
   and tests | provisional | 2026-10-2x: area map A6 → services/cases.py, services/handoff.py checked against
   tests/services/test_{handoff,cases,cases_contract}.py, tests/unit/services/, tests/unit/web/test_register_cases.py
   (AEA-29, <sha>; N passed, 1 skipped) | Integrated level when AEA-30, AEA-45, AEA-52 land |`. Keep it ≤ 400
   characters.
4. `docs/design/code-design.md`:
   - In the tree rows for `cases.py` and `handoff.py` (the ones that today end in `A6    1`), append `   built AEA-29 <sha>`,
     the same format as `person_request.py`.
   - Add one tree row after the `handoff.py` continuation: `│   ├── _case_rules.py · _case_views.py              private
     rules and view builders of cases.py (AEA-29)          A6    2   built AEA-29 <sha>`.
   - Append one line after the last `**Built:**` line: `**Built:** services/cases.py, services/handoff.py,
     services/_case_rules.py, services/_case_views.py, the register_cases hunk (AEA-29, <sha>).`
5. `docs/design/contracts/stage7/cases.md`: append after §5's rules table a subsection `### 5a. Built by AEA-29
   (2026-10-2x): additions and recorded gaps`. One bullet each, every bullet marked `[Decided §7, engineering; AEA-29
   plan]`:
   - the `source_id` / `lookup_log_id` scheme (O-9);
   - `apply` → `CaseSummaryView | CaseActionRejected` (O-2);
   - `record_activity` → `ActivityResult | CaseActionRejected` (O-3);
   - `set_followup` → `FollowUp | CaseActionRejected` (O-4);
   - `CaseNotFound` (O-5);
   - `CaseService(..., handoff_block=…, settled_view=…)` and the `shift_ended` payload keys `speaker`, `line`,
     `handoff`, `settled` (O-6);
   - `BriefAssembler(staff_guidance=…)` and the hash rule (O-7, RF-14);
   - `attach_extraction(..., customer_messages=…)` (O-8);
   - `case_created` on the thread stream (O-11);
   - `customer_id` only when verified, and the case view's verified rule (O-14, RF-16);
   - `CaseWriteFailed`;
   - `resolve_staff_guidance` and the missing-file behaviour (O-16);
   - email/general follow-up blocked on the AEA-03 follow-up (O-15).

   Edit nothing else in the file.
6. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in the files you own.

### Step 13 — gates and commits

1. Run §7.3 A–H in order. Stop at the first red and fix only owned files.
2. Commit 1 (code and implementer tests):
   - `git add src/meridian/services/_case_rules.py src/meridian/services/_case_views.py src/meridian/services/cases.py
     src/meridian/services/handoff.py src/meridian/web/container.py tests/services/test_cases_contract.py
     tests/unit/services/test_case_rules.py tests/unit/services/test_brief_assembler.py
     tests/unit/web/test_register_cases.py tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py`.
   - Message `AEA-29: case service, handoff service, brief assembler and register_cases`, with a body listing the ACs met
     and AC-23 blocked. The last line is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
3. Commit 2 (record and context):
   - `git add docs/testing/journeys/<date>-AEA-29.md .claude/reference/area-map.md .claude/state/icm-progress.md
     docs/design/code-design.md docs/design/contracts/stage7/cases.md`.
   - Message `AEA-29: journey record and context rows`, with the same last line.
4. Never `git add -A`; never push; never force; never edit a frozen file.
5. Report:
   - the gate outputs and both SHAs;
   - the record path, with its Level and Blocked-by;
   - the AC table, each verified or blocked with its command and result;
   - every §8 request still open.

---

## 6. Data and fixtures

Synthetic or issued data only. **No phone number, email, code or card-like number literal in any test file or test
name.** Contact values are read from the issued DB at run time (`tx.core.reads.customer(CustomerId("MHC-10002"))`, as the
frozen `contact_of` does), and their digits-only form is derived with `re.sub`.

- **Frozen builders** (`tests/services/_case_fixtures.py`, read only): `store`, `new_thread`, `request`, `window_change`,
  `ctx`, `state_for`, `summary_of`, `services`, `StaffingDemo`, `FlakyUow`, `guidance`, `BlockRecorder`, `set_identity`,
  `rows_for_thread`, `contact_of`, `seed_shaped`, `display_case`, `wp7`, `wp4`, `case_in_state`, `thread_of`,
  `case_action`, `followup_choice`, `activity_in`, `j`, `jtext`, `is_rejected`, `code_of`, `NOW` (= `DEMO_START` = Fri
  2026-10-16 10:00 Chicago), `DISPLAY_NOW` (14:20), `OMAR`, `OMAR_MESSAGE`.
- **The real seed** (AEA-31): `seed_demo(tx, assembler=BriefAssembler())` writes MHC-C-0005…0008 with their threads,
  messages, one `read_invoices` lookup on 0007 (`result_seen` in `key=value` form), promises, follow-up (0007, phone,
  mornings), actions and briefs. Customers MHC-94339, MHC-39394, MHC-10002 come from the issued DB.
- **Synthetic staff-guidance index** (TW only): a temp directory with `staff_notes.json` = a JSON list of five
  `StaffGuidance` dicts. `passage_id` is `f"internal/agent_discretion_notes.md#{i}"`, `section` "Agents may" or "Agents
  may NOT", `version_label` "undated", `text = prefix + " (synthetic test passage)."` for each `STAFF_GUIDANCE_FOR`
  prefix, and `text_sha256 = hashlib.sha256(text.strip().encode()).hexdigest()`. A second file omits the refund passage.

---

## 7. Checks

### 7.1 Frozen tests (test-writer; what each asserts is in the files themselves, §3d)

Do not edit them. They pass unchanged once F-1 and F-2 are applied and Steps 1–8 are built. `test_detail_last_event_id_same_snapshot`
stays skipped (AC-23).

### 7.2 Tests the implementer writes with the code

`tests/unit/services/test_case_rules.py` (pure):
- `test_state_allows_and_refusal_agree`: over every Appendix B row × role × CON-13 action, `con13_refusal(...) is None`
  iff the action is in `actions_for(...)`.
- `test_actions_for_examples_and_owner`: the four representative examples (values as the frozen
  `REPRESENTATIVE_EXAMPLES`); the owner always `()`.
- `test_missing_field_refusal`: each code from Step 1.5 with its `field` and `constraint`; `wait` in the past →
  `VALIDATION_ERROR`; a complete action → `None`.
- `test_due_state_boundaries`: `None`; now − 1 min (overdue); now + 4 h (due_soon); now + 4 h 1 min (on_time).
- `test_queue_key_order`: P0 with no due, P3 overdue, P3 due Mon 19:00 created 09:14, P3 same due created 09:24, P3 with
  no due.
- `test_lane_for_first_match`: P1 overdue → `p0_p1`; unassigned 29 min → `None`, 30 min → `unowned`; waiting with the
  wake-up passed → `stuck_waiting`.
- `test_labels`:
  - `age_label` for 4 min, 6 min, 36 min, 2 h, 1 day 4 h, 3 days, and queued "Waiting since 2:14 pm";
  - `follow_up_short`;
  - `reason_label` for every `HandoffReason` (non-empty, never the enum value) and for the gas kind;
  - `case_due_label(..., is_window_start=True)` ends with ", the window start".
- `test_identity_view_statuses`: all six `IdentityState.status` values → the five wire values; `case_customer=True`
  makes `not_checked` read `verified`.
- `test_parse_seen_formats`:
  - `'{"amount_cents": 47800}'` → that dict;
  - `"INV-204411 amount_cents=47800 balance_cents=47800"` → `{"amount_cents": 47800, "balance_cents": 47800}`;
  - `"below_floor=false; faq/x.md#3=0.812"` → `{"below_floor": "false"}`;
  - `"no pairs here"` → `{"seen": "no pairs here"}`.
- `test_mask_removes_contacts`: MHC-10002's phone and email, read at run time through `temp_sqlite()`, are absent after
  `mask`, and "[phone ending" is present.
- `test_staffing_view_labels`: both modes, with the label, and the banner `TEXTS[TextId.STAFFING_BANNER]` / `None`.

`tests/unit/services/test_brief_assembler.py` (pure; build `ConversationState` and `CaseSummary` with
`model_validate`; build `Promise` values only through `promise_for`):
- `test_eight_headings_in_order` (AC-15): numbers 1–8, `BRIEF_TITLES`, origins, heading 4 `checked False`, every item
  has ≥ 1 source, status `being_written`.
- `test_extraction_none_marks_not_generated` (AC-15): headings 2, 4, 7 `not_generated True`; 1, 3, 5, 6, 8 not; status
  `failed`; heading 7 keeps its guidance item.
- `test_quote_must_be_substring` (AC-15): a need not in `customer_messages[message_id]` is absent from heading 2, which
  is `trimmed True` with `TRIM_NOTE`; a valid need is present.
- `test_wp7_brief_items` (AC-15, **WP-7 worked pair**): heading 2 = "I want a full refund on the repair."; heading 4 =
  "It didn't fix anything", "I had to call another company"; heading 6 = the `R26.refund` text and "I can't promise an
  outcome."; heading 7 = the guidance item for "Issue refunds of any kind." with a `lookup_log` source.
- `test_heading_six_is_stored_promise` (AC-5):
  - heading 6's first item equals `case.promise.text` for WP-7;
  - it equals `fill_promise_text(promise, ref)` for an `R26.unstaffed` promise;
  - an extraction whose `open_decision` and quotes contain "A representative will refund you" leaves heading 6
    unchanged.
- `test_staff_notes_only_in_headings_3_or_7` (AC-16): an `AccountResult` carries the INV-204411 `StaffNote`
  (`kind="billed_differs_from_schedule"`, text "Our fee schedule says after-hours dispatch is $149, not $144.") and there
  is a lookup row for INV-204411. The note text appears only in heading 3 (or 7) items, each with a `lookup_log` source.
- `test_guidance_text_needs_matching_hash` (RF-14, AC-7):
  - a guidance row whose `result_seen` matches the mapped passage shows its text;
  - a row with a different sha shows `"Staff guidance: <pid>"`;
  - an unmapped passage shows the same fallback.
- `test_resolve_staff_guidance_by_prefix`:
  - five synthetic passages resolve to one tuple per reason, in `STAFF_GUIDANCE_FOR` order;
  - removing the refund passage raises `ValueError` matching `refund`;
  - the message holds no passage text.

`tests/services/test_cases_contract.py` (temp SQLite):
- `test_seed_demo_with_real_assembler` (O-21, AC-11):
  - in one write unit of work, `seed_demo(tx, assembler=BriefAssembler()) == 4`;
  - each of MHC-C-0005…0008 has a stored brief with 8 headings and status `ready`;
  - 0007's heading 5 cites its `read_invoices` row;
  - `CaseService(uow, FixedClock(NOW)).queue(StaffRole.REPRESENTATIVE, NOW)` lists `[0008, 0005, 0006, 0007]` with due
    states `no_due_time`, `overdue`, `on_time`, `on_time`;
  - `oversight(NOW)` lanes: `p0_p1 == [0008]`, `overdue == [0005]`, `unowned == [0006, 0007]`;
  - `detail(0007)`: the invoice source has `current` set and `changed_since False`. After `UPDATE invoices SET
    balance_cents = 0 WHERE invoice_id = 'INV-204411'` (test-only, through `tx.connection`), `changed_since` is `True`.
- `test_views_match_openapi_schemas` (AC-19): on the real seed, `assert_response_matches(_resp(200, body), op)` for:
  - `getQueue` (REP and SUP);
  - `getCase` for each seed ref × each staff role;
  - `getOversight`;
  - after `apply(claim)` on 0006 and `record_activity(call, reached)`: `recordContactActivity` at status 201 with
    `j(result)`.

  `_resp` is a small dataclass with `status_code`, `headers={"content-type": "application/json"}`, `content` (JSON
  bytes) and `json()`, as in `tests/journeys/j7/test_aea_46.py`.
- `test_stream_rows_match_openapi_events` (O-6, O-11, AC-8):
  1. Staffing on shift; a CON-4 request (`customer_requested_person`, `trigger="con4"`) through `HandoffService` → live-queued.
  2. A second case claimed by REP.
  3. `CaseService(uow, FixedClock(NOW), handoff_block=composer.handoff_block, settled_view=composer.settled_view)` with
     `composer = ReplyComposer()`; `convert_live_queued(LATER)` returns 1.
  4. Thread-stream rows whose `type in CHAT_EVENT_TYPES` → `assert_sse_frames_match(frames, "streamChatEvents")`.
     `case_created` is present in the rows and is not a chat type.
  5. Case-stream rows whose `type in CASE_EVENT_TYPES` (both cases) → `assert_sse_frames_match(frames,
     "streamCaseEvents")`.
  6. The `shift_ended` payload keys are exactly `{"speaker", "line", "handoff", "settled"}`.

  Build frames like `tests/services/test_live_chat_events.py::_frames`.

`tests/unit/web/test_register_cases.py` (pattern of `test_register_person_request.py` / `test_register_staff_live.py`;
the app comes from `WebShellState(settings=make_settings(tmp_path), wall_clock=…, public_paths=PublicPaths())`; the
container settings are `types.SimpleNamespace(index_dir=<dir>)`):
- `test_register_binds_services`:
  - `uow_factory` comes from `temp_sqlite()`; nothing else is provided; `build()` succeeds;
  - `c.get(CASE_SERVICE)` is a `CaseService`, `c.get(HANDOFF_SERVICE)` a `HandoffService`,
    `c.get(Key("brief_assembler"))` a `BriefAssembler`;
  - the docstring has "AEA-29" and not "No-op until".
- `test_unbound_siblings_name_the_key`:
  - `handoff.open(...)` on a fresh thread raises `CaseWriteFailed` whose `__cause__` is `RuntimeError("not bound:
    demo_service")`;
  - `cases.attach_brief(...)` raises `RuntimeError` matching `not bound: demo_clock`.
- `test_staff_guidance_resolved_from_index`:
  - the synthetic five-passage `staff_notes.json`, plus `Key("demo_service")` provided as a stub whose `presence` returns
    `"nobody_online"`;
  - a refund `open` writes one `staff_guidance` row whose `result_seen` is the refund passage's sha.
- `test_unknown_prefix_fails_build`: the file without the refund passage → `c.build()` raises `ValueError` matching
  `refund`.
- `test_missing_index_gives_no_guidance`: an empty `index_dir` → `build()` succeeds and a refund `open` writes no
  `lookup_log` row.
- `test_register_ignores_app_without_web_shell`: a bare `FastAPI()` → nothing provided.

`tests/journeys/j6/test_aea_29.py` — `test_j6_escalated_case_reaches_queue_and_case_view`:
1. WP-7 through `HandoffService.open`, nobody online, refund guidance mapped (`services(uow, guidance_map=…)`).
2. The real assembler: `assemble`, then `attach_extraction(…, None, customer_messages={mid: text})`, then
   `attach_brief`.
3. What the user sees:
   - `queue(REP)` lists the ref;
   - `detail` has eight headings, `promise.policy_row == "R26.refund"`, `promise.text == PROMISE_TABLE["R26.refund"]`,
     and `case.allowed_actions == ["claim", "flag"]`;
   - every `source_ids` entry resolves;
   - both bodies pass `assert_response_matches` (`getQueue`, `getCase`).
4. A `claim` sent to `apply` is accepted (version + 1).
5. What is stored: one `cases` row, one `case_opened` action, one `staff_guidance` lookup row.

`tests/journeys/j7/test_aea_29.py` — `test_j7_live_takeover_keeps_case_version`:
1. Staffing on shift; a CON-4 request → `live_queued`, and the conversation is `queued`.
2. REP claims → version v.
3. The real `LiveChatService` (`new_service(uow, at=NOW)` from `tests.services.live_chat_support`, actor `RILEY`):
   `join`, `send(text="Hello, this is Riley.")`, `hand_back`. Each returns a `LiveView`.
4. `detail(ref, REP, NOW)`:
   - `case.version == v` and `case.lifecycle == "claimed"`;
   - `live.state == "handed_back"`;
   - the representative line's speaker is `{"kind": "representative", "display_name": "Riley"}`;
   - the body passes `assert_response_matches(…, "getCase")`.
5. No `case_changed` row on `case:<ref>` after the claim's.

### 7.3 Commands (in the worktree; `export UV_LINK_MODE=hardlink` first; cheapest first; stop at the first red)

Owned Python files: `F="src/meridian/services/_case_rules.py src/meridian/services/_case_views.py
src/meridian/services/cases.py src/meridian/services/handoff.py src/meridian/web/container.py
tests/services/test_cases_contract.py tests/unit/services/test_case_rules.py tests/unit/services/test_brief_assembler.py
tests/unit/web/test_register_cases.py tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py"`.

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| A | Unit, while iterating | `uv run pytest tests/unit/services tests/unit/web/test_register_cases.py -q` | all pass |
| B | Lint and format | `uv run ruff check $F tests/services && uv run ruff format --check $F` | `All checks passed!`; no owned file would be reformatted (never reformat a frozen file) |
| C | Type check | `uv run mypy src/meridian/services src/meridian/web/container.py tests/services tests/unit/services tests/unit/web/test_register_cases.py tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py` | `Success: no issues found` (a finding inside a frozen file is reported, not fixed) |
| D | Affected tests | `uv run --with pytest-xdist pytest -n 2 -q tests/services tests/unit/services tests/unit/web tests/unit/test_import_direction.py tests/api/test_handoff_routes.py tests/api/test_handoff_capture.py` | all pass; skipped = `test_detail_last_event_id_same_snapshot` plus any skips already on `main` |
| E | Journeys | `uv run pytest -m journey tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py -q`, then `uv run python -m tests.journeys.affected --base main` (any change under `tests/journeys/` selects every journey) | 2 passed; the affected run is green, skips only with "blocked" / "not bound" / "route not registered" reasons |
| F | Contract boundary | `uv run pytest tests/contract -q` | as green as on `main`; no new failure; skips only with "not bound" / "route not registered" reasons (the seed now satisfies `seeded_case_ref`) |
| G | Full suite, once before the final commit | `uv run --with pytest-xdist pytest -n 2 -q` | green. **Why the full suite** (rule `build-loop-test-scope`, "code reached by everything"): `register_cases` now builds at every app start, and `register_reset`'s first-boot seed now runs this ticket's `BriefAssembler` at every real app start (RF-17). A failure that does not reproduce when its node id is re-run serially (`uv run pytest <nodeid>`) is reported with both results |
| H | Collect + greps | `uv run pytest --collect-only -q >/dev/null`; `grep -n "Promise(" src/meridian/services/{cases,handoff,_case_rules,_case_views}.py` → nothing; `grep -nE "import sqlite3\|\.execute\(" src/meridian/services/{cases,handoff,_case_rules,_case_views}.py` → nothing; `grep -nE "meridian\.(agent\|web)" src/meridian/services/{cases,handoff,_case_rules,_case_views}.py` → nothing; `grep -rnE "[0-9]{3}-[0-9]{3}-[0-9]{4}\|@[a-z]+\.(com\|org\|net)" tests/services/test_cases_contract.py tests/unit/services tests/unit/web/test_register_cases.py tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py` → nothing | as stated |

**Existing tests that must stay green:**
- `tests/unit/web/test_container.py` (unchanged file; the filled hunk is skipped by its docstring rule);
- `tests/unit/test_import_direction.py`; `tests/unit/web/test_register_reset.py`; `tests/services/test_reset.py`;
- `tests/services/test_person_request.py`; `tests/services/test_live_chat*.py`;
- `tests/api/test_handoff_routes.py`, `tests/api/test_staff_live_*.py`;
- every journey under `tests/journeys/`.

---

## 8. Risks and requests

- **R-1 (closed)** AEA-02b merged (`domain/views.py`).
- **R-2 Return types beyond DO-4 §13** (O-2…O-5). They are recorded in cases §5a. AEA-45's plan already consumes them.
  AEA-42's CON-5 route maps a `CaseActionRejected` with `NOT_ALLOWED_IN_STATE` to 409, and anything else (including the
  `NotImplementedError` of R-5) to 500.
- **R-3 The hunk is filled here** (RF-12). **Note for AEA-51:**
  - do not provide `case_service`, `handoff_service` or `brief_assembler` again;
  - provide `reply_composer`, which the shift-end forwarder reads;
  - replace `agent/context.py`'s `Any` aliases with the real imports.

  **Note for AEA-30:** provide `Key("demo_clock")` and `deps.DEMO_SERVICE`. Build `DemoService` with
  `c.get(deps.CASE_SERVICE)`; `CaseService` does not need `DemoService`, so there is no cycle.
- **R-4 Optional additions** (O-6, O-7, O-8). AEA-31's three-argument `attach_extraction` call and `BriefAssembler()`
  still work. **Request to AEA-38:** pass `customer_messages=shown`. **AEA-40** reads the stored `shift_ended` `handoff`
  for thread history (web.md §14).
- **R-5 AEA-03 follow-up for missing customer texts** (orchestrator; words from the UX session). These are missing:
  - the email follow-up saved line;
  - the general-destination label and saved line;
  - oversight lines for `p0_p1_created`, `unowned`, `due_soon`, `stuck_waiting`;
  - a plural `shift_ended_with_queued`.

  Until they land:
  - email and general follow-ups raise `NotImplementedError`. **An unverified customer cannot save a follow-up, and the
    default channel (email) fails with a 500 on CON-5.**
  - oversight shows only `overdue` alerts.

  AC-12 tests the phone path only. **Ask:** cut the ticket now; it is small (texts plus one branch here).
- **R-6 Stacked retries.** AEA-36's node retries `open` once, and `open` retries once inside: up to 4 write attempts,
  each rolled back and idempotent.
- **R-7 Promise status after a shift end** is `changed`. AEA-30's scheduler uses `list_open_past`, which looks only at
  `status = 'open'`, so it never marks a `changed` promise missed. **Note for AEA-30 / AEA-53 (M-13):** include
  `changed` where "open promise" is meant, or accept the rule as written.
- **R-8 `_PresenceSource`** is a private typing `Protocol` (no runtime seam).
- **R-9 Two private modules** keep each file under the 600-line cap; they are not new seams.
- **R-10 CON-4 cases have no brief** (D-9): `brief_status` stays `being_written`.
- **R-11 Staff copy owned here** (reason labels, identity lines, `TRIM_NOTE`, "No name given", "System", "Agent
  discretion notes", "No account match needed for safety."). All of it is in `_case_rules.py`; the UX session may revise
  it in one place.
- **R-12 Shared context lines.** The area-map A6 row, the code-design rows and the ICM table are touched by AEA-30 and
  AEA-31 too: resolve merge conflicts as the union. The duplicate A6 row is wave-2 finding 9's.
- **R-13 Disk.** Check `df -h /home` before `uv sync`. The AC-18 iff test builds a few hundred cases in one store, which
  is fine. Use `pytest -n 2` at most.
- **R-14 First-boot seed activation** (RF-17). After this merge, every real app start (journey server, contract driver)
  seeds MHC-C-0005…0008 through the real assembler. TK proves that path. Apps built with `full_app` suppress starters,
  so the AEA-46 tests that insert their own MHC-C-0007 are unaffected. If gate E, F or G shows a sibling test that
  assumed "no seed rows", stop and report it with the node id (that test is the sibling's to fix); never edit it here.
- **R-15 Shift end before AEA-51.** With the container forwarder, `convert_live_queued` raises `not bound:
  reply_composer` when a live-queued case exists and AEA-51 has not merged. No live-queued case can exist before then:
  CON-4 needs the composer, and graph turns need AEA-40/51. **Note for AEA-30's planner:** `set_staffing` propagates
  that error, as its plan already says.
- **R-16 One producer for staffing labels.** `staffing_view(mode)` is exported from `services/cases.py`. **Request to
  AEA-30:** use it for `DemoService.staffing()` instead of a second `STAFFING_LABELS` table (same strings today).
- **R-17 Frozen file sizes.** `tests/services/test_cases.py` is 920 lines, against a 500-line cap for tests. This is the
  test-writer's, noted for review; it is not changed here.
- **R-18 AC-23** waits for the UX session's OpenAPI amendment and an AEA-02b follow-up adding `events` to
  `views.CaseDetail`. Then one step here: read `tx.core.events.latest_id(case_stream(ref))` inside `detail`'s unit of
  work, and un-skip the frozen test (test-writer).
- **No signed-contract change and no D-4…D-15 reversal.** Nothing here edits the OpenAPI, `UI_CONTRACTS.md` or
  `docs/ux/**`.

---

## 9. Readiness

**READY.** Every import this ticket needs is on `main` `29ca543`. Two preconditions come before the implementer starts:

| Precondition | Who | Check |
|---|---|---|
| Test-writer amendment **F-1** (`_DIFFERENCES` drops `"promise.text"`) and **F-2** (distinct passage id per reason in `guidance()`), committed on `aea-29-aea-29-cases-handoff` with a refreshed frozen-test manifest | orchestrator → `test-writer-agent` | Step 0.2 greps |
| `git merge --no-edit main` into the AEA-29 branch (brings AEA-02b, AEA-21, AEA-31 code) | implementer, Step 0.3 | the Step 0.4 import check prints `ok` |

Evidence-level only (not merge blockers):
- AEA-30, AEA-45 and AEA-52 for AC-22's integrated level;
- the UX session's OpenAPI amendment for AC-23;
- the AEA-03 follow-up for the email/general follow-up branch (R-5).

No product decision is needed. `ranModel`: `claude-opus-5-5`.

---

## Appendix B — the `allowed_actions` table (AC-18; = frozen `tests/services/_allowed_actions_table.py` `TABLE`)

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

These rows match the signed examples:
- T02 = `getCase` DEFAULT `[claim, flag]`;
- T03 = `applyCaseAction` CLAIMED and `recordContactActivity` CALL_REACHED;
- T10 = `getCase` WAITING;
- T09 = `getCase` LIVE_JOINED (exact order);
- T14 = RESOLVED `[flag]`.

The supervisor examples ASSIGNED and PRIORITY_CHANGED disagree with each other and are not used (STF-18, R-W-13).
