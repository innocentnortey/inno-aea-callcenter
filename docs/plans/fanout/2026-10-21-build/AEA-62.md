# Plan — [AEA-62] browser journeys for integrated capabilities (J-2, J-3, J-6, J-8)

**Status:** planned — READY, **blocked-on AEA-58-F1** (one AEA-58 follow-up carrying additions A-1, A-2 and A-3 of §8
R-1: AEA-58 merged at `eb51ba4` **without** them) and **AEA-51** (`tests/integration/customer_support.py` and
`tests/graph/worked_pair_scenarios.py`, §4.4; AEA-51 itself waits on AEA-39). The UX session's
`docs/plans/ux-join/selectors.md` (still unpublished) and AEA-51's `run_graph` / `reply_composer` bindings are
**run-time** dependencies: missing ones show as *blocked* steps with their owner, never imported and never passed. No
`NEEDS-DECISION`: Decision 6 (D-8, start fresh) and WEB-1 (D-4, option A) are applied as decided; no contract change.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/62 (identical to
`docs/plans/tickets/AEA-62.md`) · **Base revision:** `main` `b68df7e` (earlier versions: `6b845a3`, `c9b17ea`, `bb9a471`,
`e22aebb`) · **Wave:** 4 · **Lane:** build-loop · **Risk:** none (no `risk::security`: plan → implement with tests →
review; no frozen tests) · **Gate:** inherits `gate::ux4` through AEA-58.
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (refresh 5) · **Implementer:** fanout-implementer (Sonnet).
**Branch / worktree:** the one the orchestrator creates (suggested `aea-62-browser-journeys` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-62`), cut from `main` **after** AEA-58-F1 and AEA-51 merged.

**Refresh 5 (2026-10-21, against `main` `b68df7e`; read this box first, then refresh 4).** Merged since `6b845a3`:
**AEA-58** (browser harness, `eb51ba4`), **AEA-35** (specialist runner, `1ce98c4`), **AEA-37** (plan node and
`join_plan`, `8d025b7`), **AEA-45** (staff cases API: `getQueue`, `getCase`, `1a6712a`), **AEA-52** (staff and demo
integration, `55d9adf`), AEA-53 and FIX-W1 (neither touches this slice). Still not merged: **AEA-51** (build ledger: "a
blocker is not merged"; AEA-39 is blocked), so `run_graph` and `reply_composer` are unbound and no chat turn can run.
`docs/plans/ux-join/selectors.md` is still unpublished (`CONTRACT_ROWS` is empty on `main`, so every on-screen step
reports `blocked-on UX session`, as AEA-58's own record shows). Unchanged since `6b845a3`: `src/meridian/agent/routers.py`,
`agent/nodes/{front,reply}.py`, `services/{session,turn,cases,handoff,_case_views}.py`, `tests/journeys/support/`,
`tests/journeys/j1/test_aea_57.py`, the ticket and the slice plan row. Every §4.5 import was re-run on `b68df7e` and gives
the same names and values. What changed in this version:
1. **AEA-58 merged without additions A-1…A-3** (§8 R-1). On `main` there is no `browser_journey_factory`, no
   `locate_by`, no `BrowserRun.screenshot_element`, and `SELECTOR_KEYS` holds only AEA-58's 16 keys, so a §4.3 key this
   slice needs raises `KeyError` in `missing_selectors`. The blocker is now **one AEA-58 follow-up, called AEA-58-F1
   here**, merged before this slice. A-1 is re-specified against the merged code: `open_browser_journey` already takes
   `environ_overrides`, so the index directory goes in as `MERIDIAN_INDEX_DIR`, and A-1 only adds `script`, `with_clock`
   and `overrides_for`.
2. **§4.2 now copies the merged browser API** (earlier it was copied from AEA-58's plan): `journey_chrome` is
   **module**-scoped; `ApiExchange.headers` is `list[tuple[str, str]]` (use `.header(name)`); the merged helpers
   `sign_in_to_scr1`, `thread_id_of`, `SIGN_IN_SCR1` and `ROOT_REDIRECT` exist and may be used;
   `test_no_selector_strings_outside_module` scans **every** `.py` under `tests/journeys/` for `locator(` and `get_by_`.
3. **AEA-37's `join_plan` is on `main` and matches the WP-8 tables:** a `membership_cancel` handoff forces
   `account = "membership"` and `knowledge = "yes"`, so the code turn runs an account task and a knowledge task (§4.6).
   **AEA-45's `getQueue` and `getCase` are mounted**, so J-6 and J-8 staff steps no longer block on AEA-45.
4. Context-row positions moved: the `icm-progress.md` *Integrated-journey protection* rows are now **line 46** (the
   AEA-57/AEA-58 row, the one to edit) and **line 59** (the older one); area-map row `3+` is line 47 and still ends
   "; the rest planned"; DO-3 §9's `journeys/` tree line is 717 and *Built on `main`* is line 724. §2, §5 step 9 and §8
   R-6 are updated.
5. §2 *owned by other slices* lists the files now in `j2` (`test_aea_35.py`, `test_aea_38.py`), `j6` (adds
   `test_aea_45.py`, `test_aea_52.py`) and `j8` (adds `test_aea_52.py`).
**Refresh 4 (2026-10-21, against `main` `6b845a3`; read this box first).** Merged since `c9b17ea`: **AEA-40** (CON-1 and
CON-2 chat routes, `SessionService`, `TurnService`; merge `f466ff7`), **AEA-30** (demo clock and scheduler, `cf8fd78`),
**AEA-35b** (`SpecialistTask`, `KnowledgeSlice`, `AccountSlice` in `domain/tools.py`, `3725c90`) and **AEA-36** (the real
front nodes `gates`, `safety`, `identity`, `c378698`). AEA-37 was sent back on a merge conflict (`6b845a3`), AEA-39 is at
NEEDS-DECISION, and AEA-35, AEA-45, AEA-51, AEA-52 and AEA-58 are not merged. Unchanged since `c9b17ea`:
`tests/journeys/support/`, `tests/journeys/j1/test_aea_57.py`, `tests/journeys/affected.py`, `agent/routers.py`, the
ticket, the slice plan, `docs/plans/stage7-signoff.md` and `docs/plans/ux-join/` (`selectors.md` is still unpublished).
AEA-58's plan still lacks additions A-1…A-3, so §8 R-1 stands, and its helper names in §4.2 still match. AEA-51's plan
names in §4.4 are unchanged. Every §4.5 import was re-run on `main` and gives the same names and values (tool names,
argument fields, report fields, `BRIEF_TITLES`, `PROMISE_TABLE["R26.refund"]`, the five `render(TextId…)` texts,
`REQUEST_ID_HEADER = "X-Request-ID"`, `login_session_lifetime_s = 43200`). What changed in this version, all from reading
the merged code:
1. **AEA-40 is no longer a run-time blocker.** `services/session.py::SessionService.thread` puts the greeting first
   with `turn_id = GREETING_TURN_ID = "greeting"`, so AC-7's `turns[0]["turn_id"] == "greeting"` now runs against real
   code. `web/deps.py::owned_thread` answers the same 404 `SESSION_NOT_FOUND` for a thread of another login session
   (AC-15 step 15e). `services/turn.py::TurnService` returns the stored response for a `turn_id` that is already
   `completed` (AC-8 step 8a). All three added to §4.6.
2. **AEA-30 is no longer a run-time blocker** (`demo_service` and `demo_clock` are bound). The chat needs now block only
   on AEA-51's `reply_composer` and `run_graph`: `web/container.py::register_chat` raises `RuntimeError("not bound:
   run_graph")` until AEA-51 binds them, which `browser_step`'s needs check reports as blocked with owner AEA-51.
3. **The identity flow on `main` (AEA-36) matches the turn tables of §5.** On the free-text opening turn the identity
   node calls nothing and returns `{}`, so `route_after_identity` goes to `facts` and the responder runs (the locate card
   comes from the reply composer). The locate turn calls `identity.locate` and then `send_code`. The code turn calls
   `verify`, and `route_after_identity` then sends the waiting tasks to their specialists on that same turn. Added to
   §4.6.
4. The icm-progress rows moved to **line 44** (AEA-57's row, the one to edit) **and line 54**. §2, §5 step 9 and §8 R-6
   are updated. The *owned by other slices* list in §2 now names the files present in `j2`, `j3`, `j6` and `j8` today.

**Refresh 3 (2026-10-21, against `main` `c9b17ea`).** Merged since `bb9a471`: **AEA-29** (cases and
handoff services, merge `ef561fc`), plus AEA-24, AEA-50 and AEA-54 (none of those three touches this slice). Still not
merged: AEA-58, AEA-51, AEA-52, AEA-30, AEA-35, AEA-37, AEA-39, AEA-40, AEA-45. `docs/plans/ux-join/selectors.md` is still
unpublished. AEA-58's refreshed plan (working copy at `c9b17ea`) still does **not** carry additions A-1…A-3, so §8 R-1
stands unchanged; its helper names in §4.2 still match. AEA-51's plan names in §4.4 are unchanged. `src/meridian/agent/`
is unchanged since `bb9a471`, so §4.5 and §4.6's graph lines still hold. What changed in this version, all from reading
AEA-29's merged code:
1. **AC-9's "`case_created` case event" is two rows on `main`.** `services/cases.py::CaseService.open_case` appends a
   `case_events` row with `kind = 'case_opened'` and an `events` row on the thread stream (`stream` = the bare thread id)
   with `type = 'case_created'` (stage7/cases.md: "`case_created` goes to the thread stream"). Step 5 asserts **both**
   (one each, the stream payload's `case_ref` equal to the reference). No expectation is loosened.
2. **AC-11's staff guidance exists only with the built index.** `web/container.py::_guidance()` reads
   `<index_dir>/staff_notes.json`; without it the server logs `staff_guidance_unavailable` and the brief gets no guidance
   item. `test_j6_case_view_brief_and_promise` therefore runs `browser_run(J6, index=True)`.
3. **The guidance item's text is the whole KB bullet** (`StaffGuidance.text`, matched by prefix in
   `services/handoff.py::resolve_staff_guidance`), placed under heading 7 with kind `fact`. AC-11 matches it with
   `startswith(STAFF_GUIDANCE_FOR[HandoffReason.REFUND][0])`.
4. **Wire shapes of the case view** (`services/_case_views.py`): `source_id = f"src-{lookup_log.id}"`; an item's
   `source_ids` lists only its `lookup_log` sources; every wire item text passes through `mask()`. AC-11's
   stored-vs-shown check therefore compares titles, item counts and kinds for all eight headings, and exact texts only
   for headings 2 and 4 (customer quotes with no contact value).
5. `handoff_service` and `case_service` are bound on `main`; J-6 steps now block only on AEA-45 (`getQueue`, `getCase`),
   AEA-40, AEA-51, AEA-30 and the UX selectors. The icm-progress rows moved to lines 43 and 52.

**Refresh note (2026-10-21, against `main` `bb9a471`; the first version was written against `e22aebb`).** Still true:
AEA-58, AEA-51, AEA-52, AEA-29, AEA-40, AEA-45 are not merged; `tests/journeys/support/` is unchanged; `selectors.md`
is unpublished; AEA-58's plan does not yet carry additions A-1…A-3. Changed in this version:
1. **Scripting uses AEA-51's `StepScript`, not the plain FIFO `JourneyScript` queue** (§4.4, §5 step 2). Reason: on the
   WP-8 code turn the account and knowledge specialists run in parallel (DO-4 §4 `join_plan`: "`membership_cancel`
   adds a membership read and a knowledge task"; "the tasks run in parallel"); both take from the one `Role.SPECIALIST`
   queue, so a FIFO hands entries out in thread order. `StepScript.set_step(..., by_marker=...)` picks a table by the
   request's text and indexes specialist tuples by tool round, so the outcome no longer depends on thread order. This
   widens addition A-1 (§8 R-1: `script` and `overrides_for` parameters).
2. **AC-4's branch is decided:** the invoice is read on the **code turn**. On `main`,
   `src/meridian/agent/routers.py::route_after_identity` resumes `waiting_identity` tasks as soon as the customer is
   verified (`_route_planned(_resumed(open_tasks), state)`), and `nodes/reply.py::_task_status` leaves an account task
   `waiting_identity` until then. No T4 fallback; a missing account card after the code is a seam finding (§8 R-10).
3. **Tool arguments are exact** from the argument models now on `main` (§4.5), not "copy from AEA-51's drivers".
4. **The WF-3 `thread_id` check moved out of the AC-4 flow into AC-17 only.** On `main` the request record takes
   `thread_id` from the path parameters only (`web/middleware.py`, `raw_thread = path_params.get("thread_id")`), and
   `GET /api/demo/inbox` has none, so the check is expected to fail as a seam finding (§8 R-9). It must not break J-2.
5. AC-12 runs with the built index (its knowledge specialist calls `kb_search`); the icm-progress row to edit is named
   exactly (the file has two rows with the same name, §5 step 9).

---

## 1. Goal and sources

### Goal (issue *What to build*, in short)

> "Nothing yet proves that a reviewer **in Chrome, on the production build, through the real login** can ask a
> membership question and see its source, book a visit and have it remembered after a reload, watch a refund request
> become a case that a representative opens with its brief, and switch roles without losing the chat."

**What it does, concretely (one leg, input → process → output).** The reviewer runs the command in §7 C-6. For
`test_j2_membership_with_source`, AEA-58's factory fixture starts the real app on a fresh port over a disposable copy of
the issued DB, serving `apps/web/dist`, with a built retrieval index and AEA-51's step-scripted model. Chrome opens `/`,
is sent to SCR-12, signs in through the form, and lands on SCR-1. The test sets the step table for one turn (planner,
classifier, knowledge specialist: one `kb_search` then `report_facts` citing a passage the test looked up beforehand,
and responder), types "What does the Comfort Club membership actually include?" and presses Send. Chrome shows the
reply with a "Source" chip naming `membership/comfort_club_overview.md`; the responder's adversarial "$149" sentence is
gone. The test then reads the working copy: the turn's `lookup_log` passage ids hold only current files, a
`check_events` row of kind `fact` with result `trimmed` exists for that turn, and there is no identity action and no
case. Every `/api/*` response Chrome received is checked against the OpenAPI when the test ends.

### Context

AEA-51 and AEA-52 prove J-2, J-3, J-6 and J-8 through the HTTP API; AEA-58 proves J-1 in a browser. This ticket moves
the integrated legs of J-2, J-3, J-6 and J-8 into Chrome (slice plan §0a, Amendment 1), using AEA-58's browser harness,
AEA-57's support package and AEA-51's script helpers, all unchanged. On `main` today (`b68df7e`) AEA-58's `browser/`
package is merged but without the three additions this slice needs (§8 R-1, AEA-58-F1), AEA-51's helpers and graph
bindings do not exist yet, and `docs/plans/ux-join/selectors.md` has not been published, so until those land every
on-screen step reports *blocked* with its owner.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-62.md` AC-1…AC-21, *Agent handoff*, *Blocked by* | Everything below |
| Slice plan | `docs/plans/slice-plan.md` §0a (AEA-62 puts J-2/3/6/8 in a browser), §1 row AEA-62 (blockers 58, 51, 52, 29, 40, 57; wave 4), §3 rows `tests/journeys/` ("one file per ticket per journey; `support/` is 57's alone") and `apps/web/**` | Owned paths; never edit `support/` or `browser/` |
| Rules | `.claude/rules/integrated-journeys.md` §2 (J-BOOK example), §3 rules 1, 2, 3, 5, 6, §4 (levels, nine record fields), §5, §6 (AEA-62 row); `build-loop-test-scope.md` + *AEA addition*; `context-maintenance.md`; workspace `code-structure.md` (tests ≤ 500 lines), `code-design-solid-modularity.md` | Record shape, who runs what, context rows in the same change |
| Requirements | PRD R-10, R-17, R-26, R-28, R-29, R-45, R-46, R-48; US-6…US-14, US-18…US-20, US-28; `docs/data/worked-pairs.md` WP-1, WP-2, WP-3, WP-4 (WP-4F turn-4 shape), WP-7, WP-8; brief audit K-8 | Expected values per leg |
| UX join | `docs/plans/ux-join/FOR-UX-SESSION.md` §3 (selector minimum), `README.md` ("a selector missing … `blocked-on UX selector <state>` for that step only"), `backend-amendments.md` AEA-62-1…3, `audit-customer.md` A-1, A-3, A-5, B-3, G-1, `audit-staff.md` A2, B1, B2, G1 | Selector keys (§4.3), blocked reporting |
| Component contracts (DO-4 + stage7 addenda; addenda win) | DO-4 §4 (`OpenTask.status`, `PlannedTask.needs_identity`, `join_plan`: membership_cancel adds a membership read and a knowledge task, tasks run in parallel), §5 (`KnowledgeReport`, `AccountReport`, `SchedulingReport`), §7 (`BRIEF_TITLES`, `BriefExtraction`, `Quote`); `stage7/graph-nodes.md` §1 (`CheckEvent`: `gate` every turn; `completion` and `fact` every turn the responder ran, result `pass` / `trimmed`), §2 (`check_quotes`: a quote must be an exact substring of its customer message), §3 (brief only on the turn a case opens); `stage7/graph-core.md` §2 (`TurnTrace`, `TurnRecord`), §3 (card ids, `decide_gate` rows 8–11: code entry, locate, task card choice, stale card → free text); `stage7/graph-tools.md` §1 (`ToolKind`, `report_facts`); `stage7/web.md` §2 (cookie, 43,200 s), §4, §6 (303 with `reason=none|expired`), §10 (`request`, `auth_event`), §13, §14 (`ThreadHistory`), §15 (wall clock); `stage7/staff.md` §1–§3; `stage7/cases.md` §1.1, §3.2, §5, §7 (seeds MHC-C-0005…0008; live cases from MHC-C-0009) | §4 below |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` schemas `TextBlock`, `SourceChip`, `LocatePromptBlock`, `CodePromptBlock`, `SlotCardBlock`, `ConfirmationBlock`, `AccountCardBlock`, `HandoffBlock`, `TurnResponse`, `ChatThread`, `InboxMessage`, `QueueRow`, `CaseDetail`, `Brief`, `BriefHeading`, `BriefItem`, `CaseSource`, `PromiseRecord`, `SessionInfo`; responses `RoleNotAllowed`, `SessionNotFound`; `listDemoInbox` ("scoped to the login session", no thread parameter) | §4.7 |
| Evaluation plan | DO-5 | n/a: no E-n suite, no number (ticket *Evaluation*) |
| Observability contract | DO-6 rows WF-1, WF-3 ("`thread_id` of the code request"), WF-4, WF-18, WF-19 | AC-17 |
| Key-metrics registry | DO-7 M-7, M-9, M-10, M-18, M-22, M-27 | Source columns asserted present on the rows each journey creates; no value reported |
| Current code read (`main` `6b845a3`; refresh 5 re-read on `b68df7e`: `tests/journeys/browser/*.py`, `agent/nodes/plan.py::join_plan`, `web/routes/staff_cases.py`, `web/schemas/staff_cases.py`, the build ledger) | `services/{session,turn}.py` (AEA-40: `GREETING_TURN_ID`, `SessionService.thread`, completed-turn replay), `web/routes/chat.py`, `web/deps.py` (`owned_thread`, `_owned`), `web/container.py::register_chat`, `agent/nodes/front.py` (AEA-36: `gates`, `identity`); `src/meridian/services/{cases,handoff,_case_views,_case_rules}.py` (AEA-29: `open_case` events, `BriefAssembler`, `resolve_staff_guidance`, `case_sources`, `brief_view`, `mask`), `adapters/sqlite/schema/{60_cases,90_staff}.sql`, `adapters/sqlite/repos_cases_state.py` (`next_case_ref`), `web/container.py` (`_guidance`), `web/deps.py` (`HANDOFF_SERVICE`, `CASE_SERVICE`); `tests/journeys/support/{steps,run,client,db,scripted_model,plugin,server,record,logtap,README}.py/md`, `tests/journeys/j1/test_aea_57.py`, `tests/journeys/affected.py`; `src/meridian/agent/routers.py` (`route_after_gates`, `route_after_identity`, `_route_planned`), `agent/nodes/reply.py` (`_task_status`), `agent/tools/{knowledge,account,scheduling}.py` (tool names, argument models, descriptions), `adapters/retrieval_fastembed.py`, `retrieval/settings.py`, `domain/{turn,specialists,handoff,records,common}.py`, `policy/{handoff,texts,limits}.py`, `web/{logging,middleware,frontend}.py`, `web/routes/{auth,demo}.py`, `adapters/sqlite/schema/00_core.sql`; the AEA-58 and AEA-51 plans in this folder (AEA-58 §5 steps 2–8; AEA-51 Part C1, Part D1) | §4 |

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| A knowledge report must cite a passage the search returned | graph-tools §2, DO-4 §5 | implicit | added PA-2 (pre-search) | step 3 |
| A brief `Quote` must be an exact substring of a customer message with that `message_id` | graph-nodes §2 | implicit | added: predict the message id, assert it after the turn | steps 5 |
| `completion` and `fact` `check_events` are written every turn the responder ran (result `pass` when nothing removed) | graph-nodes §1 | AC-7 says "no completion-check row" | in-ticket, read as: the turn's `completion` row has `result='pass'` and `removed=0`, and no row of that turn has `result='trimmed'` | step 4 (AC-7) |
| Parallel specialists on one turn (WP-8 code turn: account + knowledge) | DO-4 §4 `join_plan` | implicit | added: step-scripted model with `by_marker` (`StepScript`) | §4.4, step 2, §8 R-1 A-1 |
| A verified customer's waiting account task runs on the code turn | `routers.route_after_identity` on `main` | AC-4 "then … an account card" | decided: invoice read on the code turn; no fallback branch | step 3, §8 R-10 |
| WF-3 `request` record carries the code request's `thread_id` | DO-6 WF-3 | AC-17 | asserted in AC-17 only; expected seam finding (path-only `thread_id` on `main`) | step 6, §8 R-9 |
| A fresh login is role `customer`; landing on `/staff/cases/<ref>` after re-sign-in shows the role panel, not the case | staff.md §2 | implicit | AC-15 asserts the URL only | step 6 |
| Opening a new browser tab on `/` starts a second chat (thread id per tab, N-31) | SCREEN_SPECS SCR-1 | implicit | tab B in AC-13 / AC-20 opens `/role` (SCR-4), never `/` | step 6 |
| Element screenshots for cards in flows that showed identity values | ticket ("screenshot of the account card only") | yes | needs AEA-58 addition A-3 | §8 R-1 |
| "a `case_created` case event" (AC-9) | stage7/cases.md (thread stream gets `case_created`); `services/cases.py::open_case` | yes | decided: assert `case_events.kind = 'case_opened'` (1 row) **and** `events` (`stream` = thread id, `type = 'case_created'`, 1 row, payload `case_ref` = ref) | step 5 (AC-9) |
| Staff guidance needs `staff_notes.json` from the built index | `web/container.py::_guidance` | implicit | AC-11 runs with `index=True` | step 5 (AC-11) |
| Wire brief texts are masked; `source_ids` only from `lookup_log` sources | `services/_case_views.py::brief_view` | implicit | AC-11 compares stored and shown by title, count and kind; exact text for headings 2 and 4 | step 5 (AC-11) |
| Redaction of stored text, SSE frame bodies, live models, J-4/5/7/9/10 in a browser | CAP-n, AEA-41/59, AEA-61, slice plan | excluded | other-ticket | — |
| Selector contract for every asserted state | FOR-UX-SESSION §3 | yes | blocked-on UX session (run time, per step) | §4.3 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test code; drives WF-1, WF-3, WF-4, WF-18, WF-19, already registered) | — | — | — |

---

## 2. Boundary

### File map — owned files (the only files the implementer creates or edits)

| File | Create / modify | Responsibility | Target size |
|---|---|---|---|
| `tests/journeys/j2/test_aea_62.py` | create | **AEA-62's shared browser helpers** (§5 step 2) and J-2: membership, stale twin, billing, warranty (AC-2…AC-5) | ≤ 500 lines (hard cap) |
| `tests/journeys/j3/test_aea_62.py` | create | J-3: booking to confirmation, reload and follow-up memory, old card writes nothing (AC-6…AC-8) | ≤ 350 |
| `tests/journeys/j6/test_aea_62.py` | create | J-6: refund handoff, staff queue, case view, membership-cancel honest limit (AC-9…AC-12) | ≤ 400 |
| `tests/journeys/j8/test_aea_62.py` | create | J-8: role switch and resume, refusal then allowed, signed out and expired, header for four roles, role change elsewhere, evidence clean, records present (AC-13…AC-17, AC-19, AC-20) | ≤ 500 |
| `docs/testing/journeys/<run-date>-AEA-62.md` + folder `docs/testing/journeys/<run-date>-AEA-62/` (PNGs) | create (written by command C-6, then committed) | AC-18 record and screenshots | generated |
| `.claude/reference/area-map.md` | modify **one cell**: row `3+`, last column | AC-21 | — |
| `.claude/state/icm-progress.md` | modify **one row**: the *Integrated-journey protection* row whose evidence cell names AEA-57 and AEA-58 (today line 46) | AC-21 | ≤ 400 chars |
| `docs/design/code-design.md` | modify §9 only: the `journeys/` lines of the `tests/` tree and the *Built on `main`* sentence | AC-21 | — |

`tests/journeys/browser/README.md` is **not** edited: AEA-58's plan gives its README no journey list for later tickets,
so per AC-21 a list line would be a follow-up on AEA-58 (§8 R-6).

### Shared surfaces read only (never edit)

`tests/journeys/support/**` (AEA-57), `tests/journeys/browser/**` (AEA-58), `tests/conftest.py`,
`tests/journeys/README.md`, `tests/journeys/affected.py`, every `tests/journeys/j*/__init__.py`, every other
`tests/journeys/j*/test_aea_*.py` (import from `j1/test_aea_57.py` only), `tests/integration/**` and `tests/graph/**`
(AEA-51; import only), `tests/unit/**`, `tests/api/openapi_check.py`, `tests/fixtures/**`, `tests/fakes/**`, all of
`src/meridian/**`, `apps/web/**` (the build writes only the git-ignored `dist`), `docs/ux/**`, the OpenAPI,
`UI_CONTRACTS.md`, the briefing, issued data, `docs/archive/`, `docs/parked/`, `PROJECT-CHECKLIST.md`,
`.claude/state/resume.md`, `.claude/state/build-ledger.md` (the merge step's).

### Owned by other slices (do not touch)

`tests/journeys/browser/` and its plugin (AEA-58; a missing fixture, selector key or helper is a follow-up there, §8
R-1), `tests/journeys/support/` (AEA-57), AEA-51's `tests/integration/customer_support.py`,
`tests/integration/customer_api.py` and `tests/graph/worked_pair_scenarios.py`, every existing `tests/integration/*.py`
and `tests/graph/*.py`, the API-level `j2`/`j3`/`j6`/`j8` files of AEA-51 and AEA-52, the other tickets' files already in
`j2` (`test_aea_35.py`, `test_aea_38.py`), `j3` (`test_aea_27.py`, `test_aea_28.py`, `test_aea_34.py`, `test_aea_43.py`),
`j6` (`test_aea_29.py`, `test_aea_30.py`, `test_aea_45.py`, `test_aea_47.py`, `test_aea_52.py`) and `j8`
(`test_aea_31.py`, `test_aea_43.py`, `test_aea_44.py`, `test_aea_52.py`), `docs/plans/ux-join/selectors.md` (UX
session).

---

## 3. Requirements table

"Verify" names the exact test. Every journey test is marked `pytest.mark.journey`. Level for every row except the
static ones is **`integrated with a scripted model`**. Step names in quotes are the `journey.step` names the record shows.

| ID | Kind | Requirement (short) | How it is built | Verify | Level |
|---|---|---|---|---|---|
| AC-1 | invariant | Exactly the four `j<N>/test_aea_62.py` files + record; convention check passes; collected beside AEA-57's and AEA-58's journeys; nothing under `support/`, `browser/`, `tests/conftest.py`, `src/meridian/`, `apps/web/` changes | File map above | `uv run pytest tests/journeys/support -q` (`test_journey_file_convention`); `uv run pytest -m journey --collect-only -q`; `git diff --name-only main...HEAD` | static |
| AC-2 | **journey** (WP-1) | Three membership questions in one chat; each reply holds its own current facts; a "Source" chip names `membership/comfort_club_overview.md` and expands to its passage; per turn `lookup_log` ids back each chip; no identity action, no case, outcome not `handed_off` | `membership_leg()` driver (§5 step 3) | `tests/journeys/j2/test_aea_62.py::test_j2_membership_with_source` | integrated |
| AC-3 | negative | Stale twin never shown or cited: six stale strings absent; the "$149" draft trimmed with a `fact`/`trimmed` row; no `archive/` or `faq/faq_old_copy.md` passage id in any J-2 turn (all three legs); no chip names an excluded file | Same driver on its own server; `assert_no_excluded()` also called by AC-4 and AC-5 | `j2/test_aea_62.py::test_j2_stale_values_absent` | integrated |
| AC-4 | **journey** (WP-2) | Locate card filled from the working copy; code card "…ending in 02"; no invoice value before the code; code read from SCR-2 in a second tab; verified line; account card INV-204411 lines $89.00, $245.00, $144.00, total $478.00, due 2026-11-01; no "$149", no verdict; `verified` action then INV-204411 lookup; no case | `billing_through_code()` driver; invoice read on the code turn | `j2/test_aea_62.py::test_j2_invoice_after_code_as_billed` | integrated |
| AC-5 | **journey** (K-8) | Warranty answer 1-year with chip `warranty/warranty_policy.md` (2025-06-15); "90-day"/"90 days" absent; lookup ids include the current file, not `archive/warranty_terms_2023.txt`; no identity action | One knowledge turn | `j2/test_aea_62.py::test_j2_warranty_current_policy` | integrated |
| AC-6 | **journey** (WP-3; WF-1) | Code to phone ending 01; Monday windows 56/42/58, no Saturday; pick 8–12 → "You're booked. Here are the details." + confirmation card + "What's settled"; slot 56 not open, one appointment, one `booked` action with CON-2's `turn_id`, window-search lookups, no case, issued SHA unchanged | `book_slot_56()` driver | `tests/journeys/j3/test_aea_62.py::test_j3_book_to_confirmation` | integrated |
| AC-7 | **journey** (R-45, WP-4F turn-4 shape) | Reload: same thread, greeting first, confirmation card, settled visit; `getChatThread`, no second `startChatSession`; "Yes, please." reply kept whole (completion `pass`); settled = actions; counts unchanged | Driver + reload + follow-up turn | `j3/test_aea_62.py::test_j3_reload_and_follow_up_remembers` | integrated |
| AC-8 | failure/refusal | After reload, replaying the booking turn or tapping the old card's 1–5 pm window books nothing; counts and slot statuses equal | Driver + replay + old card | `j3/test_aea_62.py::test_j3_old_card_writes_nothing` | integrated |
| AC-9 | **journey** (WP-7; WF-1) | Handoff card: `MHC-C-NNNN` (≥ 0009), refund promise + "I can't promise an outcome.", due "Tue Oct 20 · 7:00 pm", follow-up legend; settled request; one `refund` P3 case, promise = table text `open`, `case_opened` case event + `case_created` thread-stream event, turn and conversation `handed_off` | `refund_case()` driver | `tests/journeys/j6/test_aea_62.py::test_j6_refund_handoff_in_chat` | integrated |
| AC-10 | **journey** | One click "Acting as" Representative → `/staff/queue`, "Riley · demo representative"; new row "P3 · Standard", ref, refund reason, "Unowned", due; four seeds; MHC-C-0008 "P0 · Safety" first; role column `representative` same `session_id`; reading writes no `case_events` | Driver + switch | `j6/test_aea_62.py::test_j6_case_in_staff_queue` | integrated |
| AC-11 | **journey** (WF-4; R-28, R-29) | SCR-6 `/staff/cases/<ref>`: "Unassigned, nobody owns it yet"; promise text + Open; eight headings = `BRIEF_TITLES`; section 4 "Customer says · not checked" with both claims; refund guidance sourced (CAS-33); every chip → `#src-<source_id>`; stored brief = shown; no `case_events`, `cases.version` unchanged | Driver (built index) + switch + open row | `j6/test_aea_62.py::test_j6_case_view_brief_and_promise` | integrated |
| AC-12 | **journey** (WP-8) | New chat: verify, renewal read; "I can't switch off auto-renewal from this chat."; handoff "…within 1 business day"; "Done, auto-renew is off" absent; SCR-5 lists it "P3 · Standard"; `membership_cancel` P3 case + promise; completion `trimmed` row; customer row unchanged | Own driver; parallel specialists through `by_marker` | `j6/test_aea_62.py::test_j6_membership_cancel_honest_limit` | integrated |
| AC-13 | **journey** (N-29, N-31, STF-19) | Switch to Representative → SCR-5; back to Customer → SCR-1 same conversation (`getChatThread`, no `startChatSession`); reload SCR-6 keeps the case and role (`getSession`); tab A chat works while tab B is representative; one `staff_sessions` row whose role follows; one conversation; no `case_events` from reads | Two tabs, one context | `tests/journeys/j8/test_aea_62.py::test_j8_role_switch_and_resume` | integrated |
| AC-14 | failure/refusal (rule §3.5) | Customer on `/staff/queue`: SCR-4 line, no staff data, `getQueue` 403 `ROLE_NOT_ALLOWED` `wrong_role`; Representative on that page → 200 | One tab | `j8/test_aea_62.py::test_j8_customer_refused_then_switch_allowed` | integrated |
| AC-15 | failure/refusal | Sign out on SCR-6 → SCR-12, row deleted, reload → 303 `reason=none`, sign in → that case URL; re-enter SCR-1 → one new `startChatSession`, earlier thread 404 `SESSION_NOT_FOUND`; clock past `login_session_lifetime_s` → 303 `reason=expired`, `Max-Age=0`, expired line, row deleted | Seed case MHC-C-0006; run clock | `j8/test_aea_62.py::test_j8_signed_out_and_expired` | integrated |
| AC-16 | negative | Codes, typed phones, demo password, `mhc_session` value absent from record, screenshot names, test ids, server logs, pytest output; no dev params; one origin; no held-out path | `identity_and_staff_path()` + scans | `j8/test_aea_62.py::test_j_aea62_evidence_clean`; `grep -rn heldout tests/journeys/j*/test_aea_62.py` | integrated (scan); static (grep) |
| AC-17 | capture | WF-1 turn records (+ lookups, checks, spend; case and promise for J-6); WF-3 `request` for `listDemoInbox` with the code request's `thread_id`; WF-4 `request` for `switchRole`, `getQueue`, `getCase`; WF-18 `ok` / `logged_out` same `session_id`; WF-19 `spa_fallback` | `identity_and_staff_path()` + log tap; `assert_turn_records()` step in every chat test | `j8/test_aea_62.py::test_j_aea62_records_present` (+ the "records" step of AC-2, 4, 5, 6, 9, 12) | integrated |
| AC-18 | capture | Reviewer command passes; every `/api/*` response validated (counts per op, 0 failures); issued SHA equal; `git status --porcelain apps/web` empty; record with all nine fields | C-6 | the command, then reading the record | integrated |
| AC-19 | invariant (AEA-62-1) | Header name and marked role equal `getSession` for customer, representative, supervisor, owner | Four switches | `j8/test_aea_62.py::test_j8_header_for_four_roles` | integrated |
| AC-20 | failure/refusal (AEA-62-2) | Tab B switches to Customer → tab A (SCR-6) shows `role.panel.wrong_role`; reset from tab B → tab A shows `role.panel.role_reset` on its next staff call; blocked on UX B1/B2 until their rows exist | Two tabs | `j8/test_aea_62.py::test_j8_role_change_elsewhere` | integrated |
| AC-21 | regression/context | area-map row, icm-progress row, DO-3 §9 | §5 step 9 | `git diff --stat main...HEAD` | — |
| PA-1 | invariant (plan-added) | After every scripted turn: no call since the turn's mark ended `invalid_output` or `exhausted`, and every role listed as *must* was called; the step table is cleared after the turn | `expect_turn()` | inside every turn step | integrated |
| PA-2 | invariant (plan-added) | Each knowledge script cites a passage the real index returns for that query, and the facts the responder states are in those passages (so a trimmed sentence means the check fired, not that the script was wrong) | `first_passage()` / `passages_hold()` pre-search | inside AC-2, AC-3, AC-5 | integrated |

**Worked pairs:** WP-1 (AC-2, AC-3), WP-2 (AC-4), WP-3 with WP-4F's turn-4 shape (AC-6…AC-8), WP-7 (AC-9…AC-11),
WP-8 (AC-12); K-8 for AC-5. **`[journey]` criteria:** AC-2, AC-4, AC-5, AC-6, AC-7, AC-9, AC-10, AC-11, AC-12, AC-13,
all at level `integrated with a scripted model`; the anchor (the J-BOOK journey of integrated-journeys §2) is AC-6
`test_j3_book_to_confirmation`.

---

## 4. Shared code to use (copied; do not paraphrase)

### 4.1 AEA-57 harness (`tests/journeys/support/`, on `main`; import only)

```python
from tests.journeys.support.run import JourneyRun            # fields: env, server, script, models, clock, db, logs,
    # guard, collector, strict, nodeid; properties: settings, app, container, base_url, demo_username;
    # secret_values() -> tuple[str, str]
from tests.journeys.support.scripted_model import RawToolCall, RawToolStep, ScriptedCall
    # ScriptedCall(role: Role, method, request, timeout_s, result: "ok"|"invalid_output"|"scripted_failure"|"exhausted")
from tests.journeys.support.steps import Missing, StepResult, blocked_message, owners_of, stop_blocked
    # Missing(what: str, owner: str); StepResult(journey, step, nodeid, status, detail, blocked_on, seconds)
    # stop_blocked(missing, *, strict) -> NoReturn  (pytest.skip, or pytest.fail under --journeys-strict)
from tests.journeys.support.db import issued_rows, sha256_file   # issued_rows(table) reads ISSUED_DB immutable
    # run.db is a DbReader: rows(sql, params) -> list[dict]; one(sql, params) -> dict; scalar(sql, params) -> Any;
    # count(table, where="", params=()) -> int; table_rows(table) -> list[tuple]
    # run.logs is a LogTap: wait_for(kind, predicate, *, timeout_s=2.0) -> dict; structured(kind) -> list[dict];
    # all_text() -> str
from tests.journeys.support.record import RecordData, build_record_data, render_record
    # RecordData(scope: str, values: Mapping[str, str])
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.j1.test_aea_57 import (
    CHAT_NEEDS,      # ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
    CLASSIFIER_RAW,  # '{"danger_level": "normal"}'
    CUSTOMER_TEXT,   # "Hi, what can you help me with?"
    PLANNER_RAW,     # all "none"/"no", topic "other"
    RESPONDER_TEXT,
    SIGN_IN_NEEDS,   # ("login_sessions", "demo_clock")
    TURN_NEEDS,      # (*CHAT_NEEDS, "turn_service", "run_graph")
)
```

Need names must be keys of `NEED_OWNERS`; operations must be keys of `OPERATION_OWNERS` (both in `support/steps.py`).
Names used here: needs `login_sessions`, `staff_access`, `session_service`, `turn_service`, `demo_service`,
`demo_clock`, `reply_composer`, `run_graph`, `identity_service`, `handoff_service`, `case_service`, `reset_service`;
operations `login`, `logout`, `getSession`, `switchRole`, `startChatSession`, `getChatThread`, `submitTurn`,
`listDemoInbox`, `getQueue`, `getCase`, `resetDemo`. All exist in the maps today.

`run.step` catches `Exception` only, so a `pytest.skip` raised inside a step records nothing; `block_here()` (§5 step
2) therefore records the `StepResult` itself before calling `stop_blocked`.

### 4.2 AEA-58 browser harness (`tests/journeys/browser/`, merged `eb51ba4`; copied from the code; A-n = AEA-58-F1)

```python
from tests.journeys.browser.pages import DESKTOP, PHONE, BrowserPage, BrowserRun, Device
    # DESKTOP = Device("chrome-desktop", 1280, 800); PHONE = Device("chrome-phone", 390, 844)
    # @dataclass BrowserPage(device: Device, context: BrowserContext, page: Page, net: NetworkLog)
    # @dataclass BrowserRun(run: JourneyRun, browser, channel: str, build: ProductionBuild, shots_dir: Path,
    #                       session: BrowserSession, test_name: str, pages: list[BrowserPage])
    #   .open(device) -> BrowserPage (new context: own cookie jar, viewport, locale en-US, tz America/Chicago, reduced
    #        motion, base_url = run.base_url, default timeout 15 s; a NetworkLog attached to the context)
    #   .screenshot(bp, label) -> Path   (label must match ^[a-z0-9-]{1,40}$; file <test_name>-<device>-<label>.png,
    #        appended to session.screenshots)
    #   .screenshot_element(bp, target: Locator, label) -> Path   (A-3; not on main yet)
    #   .close()  (teardown: validates every /api exchange of every page in .pages; raises on any OpenAPI failure)
from tests.journeys.browser.steps import (ROOT_REDIRECT, SIGN_IN_SCR1, SIGN_IN_SELECTORS, BrowserLogin, browser_step,
                                          first_hop, page_fetch, sign_in_to_scr1, sign_in_via_form, sign_out_via_shell,
                                          thread_id_of)
    # browser_step(run, journey, name, *, needs=(), operations=(), selectors=()) -> context manager; a missing selector
    #   row records the step blocked (owner "UX session", plus any missing needs) and calls stop_blocked; else run.step
    # SIGN_IN_SELECTORS = ("login.username", "login.password", "login.submit"); SIGN_IN_SCR1 = (*SIGN_IN_SELECTORS,
    #   "screen.scr1"); ROOT_REDIRECT = "/login?return_to=%2F&reason=none"
    # @dataclass(frozen=True) BrowserLogin(session_id: str, login: ApiExchange)   # the POST /api/login exchange (200)
    # sign_in_via_form(run, bp) -> BrowserLogin  (fills the demo pair from run, submits, asserts exactly one new
    #   staff_sessions row)
    # sign_in_to_scr1(brun, bp) -> BrowserLogin  (goto "/", first hop 303 to ROOT_REDIRECT, sign in, SCR-1 visible,
    #   page.url == base_url + "/")
    # thread_id_of(bp, since=0) -> str  (waits for startChatSession since the mark; asserts 201)
    # sign_out_via_shell(run, bp) -> ApiExchange (asserts 204)
    # first_hop(response) -> Response (first hop of a redirect chain); page_fetch(bp, path) -> {"status", "text"} (GET)
from tests.journeys.browser.selectors import SELECTOR_KEYS, locate, locate_in, missing_selectors
    # locate(page, key) -> Locator; locate_in(parent: Locator, key) -> Locator
    # locate_by(target: Page | Locator, key: str, value: str) -> Locator   (A-2; not on main yet)
from tests.journeys.browser.network import ApiExchange
    # @dataclass ApiExchange(index, method, url, path, operation_id: str | None, status: int,
    #   headers: list[tuple[str, str]], request_body: bytes | None, body: bytes | None = None, is_sse: bool = False,
    #   failed: str | None = None); .header(name) -> str | None (case-insensitive)
    # NetworkLog (bp.net): .mark() -> int; .operations(since=0) -> list[str]; .exchanges: list[ApiExchange];
    #   .wait_for(page, operation_id, *, since=0, timeout_ms=15_000, finished=True) -> ApiExchange
    #     (AssertionError "no <op> response within <ms> ms (seen: [...])" on timeout)
    #   .origins() -> set[str]; .dev_param_hits(*, allowed_urls=()) -> list[str]
from tests.journeys.browser.record import browser_record_values
    # browser_record_values(base: RecordData, session: BrowserSession, *, collector, root) -> dict[str, str]
```

Fixture: **`browser_journey_factory`** (A-1, §8 R-1), never `browser_journey`, because every AEA-62 run passes
AEA-51's `StepScript`, J-2, AC-11 and AC-12 need the built index, and AC-15 needs the run clock. `journey_chrome` is
**module**-scoped on `main` (a started sync Playwright breaks later `asyncio.run`). Each test module declares
`pytest_plugins = ("tests.journeys.browser.plugin",)` (AEA-58's loading rule; never import the plugin module).
`ApiExchange.body` and `request_body` are **bytes**: decode with `json.loads(ex.body)` (accepts bytes).
`test_browser_support.py::test_no_selector_strings_outside_module` scans every `.py` under `tests/journeys/`: the text
`locator(` or `get_by_` may not appear anywhere in this slice's files, comments included.

### 4.3 Selector keys this ticket uses

The only way to touch the DOM is `locate`, `locate_in` and `locate_by` (addition A-2) from AEA-58's `selectors.py`. No
test file of this ticket calls `locator(` or `get_by_`. Keys already in AEA-58's `SELECTOR_KEYS`: `screen.scr1`,
`screen.scr12`, `login.username`, `login.password`, `login.submit`, `chat.ready`, `chat.entry`, `chat.entry.customer`,
`chat.entry.assistant`, `chat.block.text`, `chat.composer`, `chat.send`, `shell.sign_out`.

Keys this ticket needs AEA-58 to add (addition A-2; each maps to a FOR-UX-SESSION §3 hook row or "a hook you choose"):

| Key | State it asserts / control | FOR-UX §3 row |
|---|---|---|
| `screen.scr2`, `screen.scr4`, `screen.scr5`, `screen.scr6` | that screen's root | "which screen is up" |
| `login.message.expired` | SCR-12 expired line | "login refused / throttled / expired" |
| `chat.source` | a cited source chip naming its document | "J-2 … a cited source names its document" |
| `chat.source.toggle` / `chat.source.excerpt` | the control that opens a chip / the quoted passage it shows | same (UX chooses) |
| `chat.block.locate_prompt`, `chat.block.code_prompt`, `chat.block.account_card`, `chat.block.slot_card`, `chat.block.confirmation`, `chat.block.handoff` | a reply block of that type (`[data-block-type]`) | "reply blocks" |
| `card.locate.name`, `card.locate.phone`, `card.locate.submit` | locate card inputs and submit | UX chooses |
| `card.code.input`, `card.code.submit` | code card input and submit | UX chooses |
| `card.slot.window_by_id` (parametric `{value}` = slot id), `card.slot.continue` | one window in a slot card; "Continue with this window" | UX chooses |
| `settled.visit`, `settled.request` | "What's settled" visit row and request row | `[data-visit-status]`, `[data-request-ref]` |
| `inbox.message.active`, `inbox.code` | SCR-2 newest active message; its code text | `[data-inbox-status=active]`; "code readable as text" |
| `shell.role.customer`, `shell.role.representative`, `shell.role.supervisor`, `shell.role.owner` | the radio in `role=radiogroup[name="Acting as"]` | "acting role" (present today) |
| `shell.header_name` | the shell's signed-in display name | UX chooses |
| `role.panel`, `role.panel.wrong_role`, `role.panel.role_reset` | SCR-4 / staff role panel, and with its reason | `[data-testid=role-panel][data-reason=…]` |
| `queue.row`, `queue.row_by_ref` (parametric) | every queue row in order; the row of one reference | "queue row" (present today) |
| `case.root`, `case.owner`, `case.promise`, `case.promise.open` | case loaded; owner line; promise card; promise with status open | `[data-testid=case]`, `case-owner`, `[data-promise-status]` |
| `brief.section_by_number` (parametric), `brief.heading`, `brief.item.tag` | `#brief-<n>`; its heading; the "Customer says · not checked" tag | `#brief-1…8` (present today) |
| `case.sources_tab`, `case.source_by_id` (parametric) | Sources tab; `#src-<source_id>` | "promise and sources" |
| `demo.reset`, `demo.reset_result` | SCR-3 reset control and its result | `[data-reset-result]` |

A key AEA-58 does not know raises `KeyError` inside `missing_selectors` (a harness bug, not a blocked step): if that
happens, **stop** and report `BLOCKED-ON AEA-58 addition A-2`; never catch it.

### 4.4 AEA-51 test helpers (from AEA-51's plan Part C1 and D1; import only; re-check names after it merges)

```python
from tests.integration.customer_support import StepScript, built_index_dir, fastembed_offline, step_overrides
    # built_index_dir() -> Path | None   (functools.cache; None when bge-small-en-v1.5 is not cached in var/fastembed)
    # fastembed_offline() -> context manager: sets FASTEMBED_CACHE_PATH (the cached model dir) and HF_HUB_OFFLINE=1
    # StepEntry = ScriptEntry | Stall | tuple[ScriptEntry | Stall, ...]
    # class StepScript(JourneyScript):
    #     def set_step(self, default: Mapping[Role, StepEntry], *,
    #                  by_marker: Mapping[str, Mapping[Role, StepEntry]] | None = None) -> None
    #     def calls_since(self, mark: int) -> tuple[ScriptedCall, ...]          # self.calls[mark:]
    #   Semantics (AEA-51 C1): a single entry answers EVERY call of its role in the step; a tuple is consumed in call
    #   order, and for Role.SPECIALIST it is indexed by the tool round of that specialist run (round 0 = first
    #   tool_step, round 1 = the step after the tool results); by_marker picks the first table (dict order) whose marker
    #   word appears in the request's JSON and that has the role, else the default table; a role with no entry -> the
    #   call records "exhausted". set_step replaces both tables and resets the counters.
    # step_overrides(settings, script: StepScript, *, wall_clock=None, trace=None)
    #     -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]
from tests.graph.worked_pair_scenarios import NORMAL, brief, planner, report, responder, step, tool
    # planner(**choices) -> str   PlannerChoices JSON; defaults knowledge "no", account "none", scheduling "none",
    #                              handoff "none", topic "other"
    # NORMAL -> str               classifier JSON with the "normal" label
    # responder(text) -> str      ResponderDraft JSON
    # brief(**fields) -> str      BriefExtraction(**fields).model_dump_json()
    # tool(name, args, call_id="call-1") -> RawToolCall;  report(model, **fields) -> RawToolCall named "report_facts"
    # step(*calls, text="") -> RawToolStep
```

If AEA-51's merged module names or signatures differ from these, use the merged ones and say so in the report; if
`StepScript`, `step_overrides` or `set_step(..., by_marker=...)` is missing, stop and report `BLOCKED-ON AEA-51`.

### 4.5 Production values used as expected values and script arguments (import from `main`; never retype)

```python
from meridian.agent.tools.knowledge import KB_SEARCH_NAME, KbSearchArgs        # "kb_search"; KbSearchArgs(query)
from meridian.agent.tools.account import READ_INVOICES_NAME, READ_MEMBERSHIP_NAME, ReadInvoicesArgs, ReadMembershipArgs
    # "read_invoices", "read_membership"; ReadInvoicesArgs(invoice_number: InvoiceId | None); ReadMembershipArgs()
from meridian.agent.tools.scheduling import BOOK_VISIT_NAME, FIND_WINDOWS_NAME, BookVisitArgs, FindWindowsArgs
    # "book_visit", "find_windows"; FindWindowsArgs(service_type, zone_hint=None, earliest=None, latest=None,
    #   window=None, wanted_text=""); BookVisitArgs(slot_id: int >= 1, issue: str 1..300)
from meridian.adapters.retrieval_fastembed import FastembedIndex
    # FastembedIndex(index_dir, *, model_cache_dir=None, embed_query=None).search(q, *, k, min_score) -> RetrievalResult
    # RetrievalResult(passages: tuple[Passage, ...], below_floor: bool);
    # Passage(passage_id, file, section, version_label, version_date, text, score); passage_id = f"{file}#{n}"
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K
from meridian.domain.common import Role      # PLANNER, CLASSIFIER, PLANNER_FALLBACK, SPECIALIST, RESPONDER, BRIEF
from meridian.domain.specialists import AccountReport, KnowledgeReport, ReportedPoint, SchedulingReport
    # KnowledgeReport(points: list[ReportedPoint] (max 5), answered: bool); ReportedPoint(text, passage_id)
    # AccountReport(summary: str <= 300); SchedulingReport(appointment_id: int, wanted_time: str, note: str <= 200)
from meridian.domain.handoff import BRIEF_TITLES, HandoffReason, Quote      # Quote(message_id, text)
    # BriefExtraction fields: needs, claims, open_decision
from meridian.policy.handoff import PROMISE_TABLE, STAFF_GUIDANCE_FOR
from meridian.policy.texts import TextId, render
from meridian.web.errors import REQUEST_ID_HEADER                            # the X-Request-ID header name
```

Script arguments (exact; built from the models so a rename fails at import):

| Use | Tool call |
|---|---|
| J-2 knowledge | `tool(KB_SEARCH_NAME, KbSearchArgs(query=<the row's query>).model_dump())` |
| AC-4 invoice | `tool(READ_INVOICES_NAME, ReadInvoicesArgs(invoice_number="INV-204411").model_dump(mode="json"))` |
| AC-6 windows | `tool(FIND_WINDOWS_NAME, FindWindowsArgs(service_type="hvac_repair", wanted_text="This Saturday if possible, 4 to 7, after work.").model_dump(mode="json"))` |
| AC-6 book | `tool(BOOK_VISIT_NAME, BookVisitArgs(slot_id=56, issue="AC not cooling").model_dump())` |
| AC-12 membership | `tool(READ_MEMBERSHIP_NAME, ReadMembershipArgs().model_dump())` |
| AC-12 knowledge | `tool(KB_SEARCH_NAME, KbSearchArgs(query="How do I cancel a Comfort Club membership?").model_dump())` |

- `render(TextId.GREETING)`, `render(TextId.VERIFIED)` = "Thanks, you're verified for this chat.",
  `render(TextId.BOOKED)` = "You're booked. Here are the details.", `render(TextId.PROMISE_REFUND_NO_OUTCOME)` = "I can't
  promise an outcome.", `render(TextId.FOLLOWUP_LEGEND)` = "We'll follow up by email unless you'd prefer a phone call."
- `PROMISE_TABLE["R26.refund"]` = "A representative will get to your refund request within 2 business days."
- `STAFF_GUIDANCE_FOR[HandoffReason.REFUND][0]` = "Issue refunds of any kind."
- `BRIEF_TITLES` = the eight headings ("Why this came to you" … "Who they are and how to reach them").
- `run.container.limits.web.login_session_lifetime_s` (43,200): read it, never write the number.
- Copy-text expected values from the ticket (SCREEN_SPECS copy, not selectors): "Code sent to the phone on record,
  ending in 02" / "… ending in 01", "8:00 am – 12:00 pm", "8:00 am → 12:00 pm", "Your visit", "Booked", "Tue Oct 20 ·
  7:00 pm", "Riley · demo representative", "P3 · Standard", "P0 · Safety", "Unowned", "Unassigned, nobody owns it yet",
  "Customer says · not checked", "Open", "You're acting as the customer. Switch to a staff role to see this.", "Your
  demo session ended, so please sign in again.", "I can't switch off auto-renewal from this chat.", "A representative
  will get back to you within 1 business day".
- Display names (staff.md §1): customer "Customer (demo)", representative "Riley, demo representative", supervisor
  "Demo supervisor", owner "Demo business owner".

### 4.6 Production behaviour this plan relies on (read on `main`; a difference at run time is a seam finding)

- `routers.route_after_gates`: kind `CODE_ENTRY` / `LOCATE` → `"identity"`; `CARD_CHOICE` on an open task → that task's
  specialist; free text → `["planner", "danger_classifier"]`.
- `routers._route_planned`: any planned task with `needs_identity` while not verified → `"identity"` (no specialist
  runs before the code).
- `routers.route_after_identity`: once `identity.status == "verified"`, an `act` plan's tasks or the open
  (`waiting_identity` / `open`) tasks are sent to their specialists **on that same code turn**.
- `routers.route_after_specialists` → escalation; `route_after_facts` → `["responder", "brief"]` when a handoff was
  created, else `["responder"]`.
- `web/middleware.py`: the `request` record's `thread_id` comes only from a `{thread_id}` path parameter.
- `services/cases.py::CaseService.open_case` (AEA-29, merged): reference = `max(highest number, 8) + 1` (so the first
  live case is `MHC-C-0009`); writes `cases`, `promises`, one `case_events` row `kind = 'case_opened'`, one `actions` row
  `case_opened`, and one `events` row `stream = <thread_id>`, `type = 'case_created'`, payload JSON with `case_ref`.
- `services/handoff.py::BriefAssembler`: headings 1, 3, 5, 6, 8 from stored facts; heading 2 (`needs`) and 4 (`claims`)
  from the extraction, each quote kept only if it is a substring of that customer message (kind `claim`); heading 7 =
  staff guidance items (kind `fact`, source the `staff_guidance` lookup row) plus the open decision (kind `decision`).
- `web/container.py::_guidance()`: guidance only when `<settings.index_dir>/staff_notes.json` exists.
- `services/_case_views.py`: `CaseSource.source_id = f"src-{lookup_log.id}"`; the guidance source has `title = "Agent
  discretion notes"`, `audience = "staff_only"`; `BriefItemView.text = mask(item.text)`.

- `services/session.py` (AEA-40, merged): `SessionService.thread` returns the greeting entry first with `turn_id =
  GREETING_TURN_ID = "greeting"`, then each turn's customer entry and its stored reply blocks; `getChatThread` carries
  `settled` from the same read.
- `services/turn.py::TurnService` (AEA-40, merged): `turns.begin` on a `turn_id` whose row is `completed` returns the
  stored response unchanged (no graph run, no model call, no write), so AC-8's replay answers 200 with the same
  `turn_id`.
- `web/deps.py::owned_thread` (AEA-40, merged): a thread of another login session answers the identical 404
  `SESSION_NOT_FOUND` (410 only for the caller's own ended thread), which is AC-15 step 15e's expectation.
- `agent/nodes/front.py::identity` (AEA-36, merged): free-text turn → no identity call; `LOCATE` → `identity.locate`,
  then `send_code` when located; `CODE_ENTRY` with digits → `identity.verify`.
- `web/container.py::register_chat` (AEA-40): `run_graph` and `reply_composer` are AEA-51's keys; until they are bound
  a chat turn raises `RuntimeError("not bound: <key>")`, so `TURN_NEEDS` steps report blocked with owner AEA-51.
- `agent/nodes/plan.py::join_plan` (AEA-37, merged `8d025b7`): when the handoff request is
  `HandoffReason.MEMBERSHIP_CANCEL` it sets `account = "membership"` and `knowledge = "yes"`; drafts are ordered account,
  scheduling, knowledge, with `needs_identity=True` for account and scheduling and `False` for knowledge. WP-8's opening
  turn therefore goes to identity (`_route_planned`, above), and the code turn runs the account and the knowledge
  specialist (the `CANCEL_MARKERS` case of §5 step 5).
- `web/routes/staff_cases.py` (AEA-45, merged `1a6712a`): `getQueue` and `getCase` are mounted; `QueueResponse`
  (`web/schemas/staff_cases.py`) is `{as_of, staffing, live[], needs_my_action[]}` of `QueueRowOut {…, priority
  {level, word}, owner: str | None, due_label: str | None, …}`.

### 4.7 Wire and storage shapes (OpenAPI and schema, read only)

- `TurnResponse`: `thread_id, turn_id, sequence, blocks[], settled, writes[], controller, notice, last_event_id`.
  Block types used: `text` (`text`, `sources: SourceChip[]`), `source_chip` (`source: SourceChip`), `locate_prompt`
  (`card_id`, `field_sets: [["name","phone"], …]`), `code_prompt` (`card_id`, `hint`, `state`), `slot_card`
  (`card_id`, `days[].date`, `days[].windows[] {slot_id: str, date, window, window_label, technician, member_only,
  taken}`), `confirmation` (`appointment_id`, `date`, `window_label`, `technician`, `fee_line`, `timeline`,
  `free_change_note`), `account_card` (`kind`, `invoice {invoice_id, lines[{description, amount{amount_cents,
  display}, source}], total, balance, due_on, paid}`), `handoff` (`reference`, `variant`, `promise_text`, `due_at`,
  `due_label`, `extra_lines`, `followup_chooser`).
- `SourceChip`: `passage_id, file, section, version_date, excerpt, audience, version_label`.
- `Settled`: `visit {appointment_id, date, window, window_label, technician, service_type, fee_line, status,
  change_request} | null`, `request {reference, promise_text, due_at, due_label, extra_lines, live_queued, followup} |
  null`, `identity {status, hint}`.
- `ChatThread`: `thread_id, state, turns[{turn_id, speaker, at, text, blocks}], settled, …`.
- `InboxResponse.messages[]`: `id, at, to_masked, body, code, status (active|used|expired), expires_at`.
- `QueueResponse`: `as_of, staffing, live[], needs_my_action[]` of `QueueRow {reference, priority {level, word},
  reason, customer_display_name, owner, due_at, due_label, due_state, lifecycle, seed, brief_status, …}`.
- `CaseDetail`: `case (CaseSummary: reference, reason, priority, lifecycle, owner, version, promise_status, …),
  promise (PromiseRecord: text, due_at, due_label, policy_row, status, …), brief {status, headings[8] {number, key,
  title, checked, items[{text, kind, source_ids[], changed}], …}}, sources[{source_id, lookup_log_id, …}], …`.
- `SessionInfo`: `authenticated, role, display_name, sees, signed_in_at`.
- Errors: `{"error": {"code", "field", "constraint", "details"}, "request_id"}`; `ROLE_NOT_ALLOWED` 403,
  `SESSION_NOT_FOUND` 404.
- Log records (`web/logging.py` allow-list): `request {record, request_id, route, status, duration_ms, caller_role,
  thread_id, error_kind}`; `auth_event {record, request_id, outcome (ok|rejected|rate_limited|logged_out), session_id,
  at}`; the SPA route name is `"spa_fallback"` (`web/frontend.py` `SPA_FALLBACK_ROUTE`).
- Tables (working copy, read with `run.db`): `conversations(thread_id, demo_session, outcome, …)`,
  `messages(id, thread_id, role, text, turn_id, kind, card_id, …)`, `turns(turn_id, thread_id, sequence, status,
  gate_result, outcome, server_ms, trace_export, model_calls, response, …)`, `actions(thread_id, turn_id, kind,
  record_id, …)`, `lookup_log(id, thread_id, turn_id, message_id, tool, record_ids, passage_ids, result_seen)`
  (`record_ids`, `passage_ids` are JSON arrays), `check_events(id, thread_id, at, check_kind ∈ {completion, fact,
  brief_fact, brief_quote, gate, classifier, brake}, turn_id, result ∈ {pass, trimmed, fallback, fired, raised},
  removed, claim_kinds, codes)`, `spend_ledger(thread_id, turn_id, role, …)`, `identity_threads(thread_id, status,
  customer_id, …)`, `cases(case_ref, thread_id, reason, priority, due_at, version, seed, …)`, `case_events(id, case_ref,
  kind, event_key, actor_role, detail_json, at)`, `events(id, stream, type, payload, at)`, `promises(case_ref, policy_row, text, status, due_at, …)`, `case_briefs(case_ref, brief_json, status)`,
  `staff_sessions(token_hash, session_id, role, role_reset_pending, signed_in_demo, created_real, expires_real)`; issued `customers`, `appointment_slots(slot_id, slot_date, window, tech_id,
  zone, service_type, status)`, `appointments(appointment_id, slot_id, customer_id, status, …)`.
- Dates: compare stored `due_at` with `datetime.fromisoformat(value) == datetime(2026, 10, 20, 19, 0, tzinfo=CHI)`
  (aware comparison; `CHI = ZoneInfo("America/Chicago")`).

### 4.8 Frontend paths (navigation targets, not selectors; from `apps/web/src/routes.ts`)

SCR-1 `/`, SCR-2 `/demo/inbox`, SCR-3 `/demo`, SCR-4 `/role`, SCR-5 `/staff/queue`, SCR-6 `/staff/cases/<reference>`,
SCR-12 `/login`.

---

## 5. Steps

Dependency direction: the four test files → AEA-58 `browser/` + AEA-51 helpers → AEA-57 `support/` → `meridian`. j3,
j6 and j8 import the shared helpers from `tests.journeys.j2.test_aea_62` (named imports only, never a `test_*` name).
Nothing imports the j-files except other j-files of this ticket.

### Step 0 — environment (no code)

1. `export UV_LINK_MODE=hardlink`; `df -h /home` (stop and report under 5 GB free).
2. Confirm AEA-58-F1 merged (AEA-58's package itself is on `main` since `eb51ba4`):
   `grep -n "def browser_journey_factory\|def locate_by\|def screenshot_element\|overrides_for" tests/journeys/browser/*.py`
   finds all four, and `uv run python -c "from tests.journeys.browser.selectors import SELECTOR_KEYS;
   print(sorted(SELECTOR_KEYS))"` lists every key of §4.3. Missing → stop, report `BLOCKED-ON AEA-58-F1 (addition A-<n>)`.
3. Confirm AEA-51 merged: `ls tests/integration/customer_support.py tests/graph/worked_pair_scenarios.py`. Missing → stop,
   report `BLOCKED-ON AEA-51`.
4. Confirm AEA-51's names: `uv run python -c "from tests.integration.customer_support import StepScript, step_overrides,
   built_index_dir, fastembed_offline; from tests.graph.worked_pair_scenarios import NORMAL, brief, planner, report,
   responder, step, tool"`. Fails → stop, report `BLOCKED-ON AEA-51` (or use the merged names, §4.4).
5. Build in the primary checkout (backend worktrees have no `node_modules`):
   `npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist`;
   then `git -C /home/linuxuser/workspaces/inno-aea-callcenter status --porcelain apps/web` prints nothing (else stop
   and report; do not revert anything there). `export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist`.

### Step 1 — module headers (all four files)

Each file starts with a docstring naming the journey, the level `integrated with a scripted model`, and that blocked
steps name their owner; then:

```python
pytest_plugins = ("tests.journeys.browser.plugin",)
pytestmark = pytest.mark.journey
```

### Step 2 — shared helpers (top of `tests/journeys/j2/test_aea_62.py`, section comment "AEA-62 shared browser helpers")

```python
J2, J3, J6, J8 = "J-2", "J-3", "J-6", "J-8"
CHI = ZoneInfo("America/Chicago")
VERIFY_NEEDS = (*TURN_NEEDS, "identity_service")
HANDOFF_NEEDS = (*TURN_NEEDS, "handoff_service", "case_service")
STAFF_NEEDS = ("login_sessions", "staff_access", "case_service")
CHAT_SELECTORS = ("chat.ready", "chat.composer", "chat.send", "chat.entry.assistant", "chat.block.text")
IDENTITY_SELECTORS = ("chat.block.locate_prompt", "card.locate.name", "card.locate.phone", "card.locate.submit",
                      "chat.block.code_prompt", "card.code.input", "card.code.submit", "screen.scr2",
                      "inbox.message.active", "inbox.code")
EXCLUDED_FILES = frozenset({"faq/faq_old_copy.md"})    # plus every file under "archive/" (R-10, DEC-4)
SEED_REFS = ("MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008")   # stage7/cases.md §7
ROLES = ("customer", "representative", "supervisor", "owner")
Table = Mapping[Role, StepEntry]          # StepEntry from tests.integration.customer_support

@dataclass(frozen=True)
class Turn:
    turn_id: str                     # the turn_id Chrome sent (request body)
    body: dict[str, Any]             # the 200 TurnResponse
    exchange: ApiExchange
    roles_called: frozenset[Role]

@dataclass(frozen=True)
class Verified:                       # values for AC-16 scans; never printed
    customer_id: str
    opening: Turn
    code_turn: Turn
    inbox: ApiExchange                # the listDemoInbox exchange (AC-17 WF-3)
    phone: str = field(repr=False)
    code: str = field(repr=False)
```

Functions (each ≤ ~30 lines; exact behaviour):

1. `block_here(run, journey, step, what, owner) -> NoReturn`: `missing = (Missing(what, owner),)`;
   `run.collector.add_step(StepResult(journey, step, run.nodeid, "blocked", blocked_message(missing),
   owners_of(missing), 0.0))`; `stop_blocked(missing, strict=run.strict)`. *Invariant: a blocked condition found
   mid-test is recorded with its owner and is never a pass.*
2. `page_text(page) -> str`: `page.evaluate("() => document.body.innerText")`. Used only for "not on the page" checks.
3. `page_post(bp, path, body: Mapping[str, Any]) -> dict[str, Any]`: `bp.page.evaluate("async ([p, b]) => { const r =
   await fetch(p, {method: 'POST', credentials: 'include', headers: {'content-type': 'application/json'}, body: b});
   return {status: r.status, text: await r.text()}; }", [path, json.dumps(body)])`. (The network log records and
   validates it like any other request.)
4. `second_tab(bp) -> BrowserPage`: `BrowserPage(device=bp.device, context=bp.context, page=bp.context.new_page(),
   net=bp.net)`. Same context, so same cookie and same login session; the shared `NetworkLog` sees its requests (it is
   attached to the context). Do **not** append it to `brun.pages`.
5. `blocks_of(body, kind) -> list[dict]`: `[b for b in body["blocks"] if b["type"] == kind]`.
   `chips_of(body) -> list[dict]`: every `b["sources"]` item of `text` blocks plus every `b["source"]` of `source_chip`
   blocks, in order.
6. `steps(run) -> StepScript`: `s = run.script`; `assert isinstance(s, StepScript), "run was not opened with AEA-51's
   StepScript"`; return `s`.
7. `expect_turn(run, bp, *, table: Table, must: Collection[Role], send: Callable[[], None], by_marker:
   Mapping[str, Table] | None = None) -> Turn` (PA-1):
   1. `script = steps(run)`; `calls_mark = len(script.calls)`; `net_mark = bp.net.mark()`.
   2. `script.set_step(table, by_marker=by_marker)`.
   3. `send()` (the caller clicks or types).
   4. `ex = bp.net.wait_for(bp.page, "submitTurn", since=net_mark, timeout_ms=70_000)`; `assert ex.status == 200,
      f"submitTurn answered {ex.status}"`.
   5. `turn_id = json.loads(ex.request_body)["turn_id"]`; `body = json.loads(ex.body)`; `assert body["turn_id"] ==
      turn_id`.
   6. `called = script.calls_since(calls_mark)`; `bad = [(c.role.value, c.result) for c in called if c.result in
      ("invalid_output", "exhausted")]`; `assert not bad, f"script problems: {bad}"`; `roles = frozenset(c.role for c
      in called)`; `missing = set(must) - roles`; `assert not missing, f"roles never called: {sorted(r.value for r in
      missing)}"`.
   7. `script.set_step({})` (nothing answers between turns; a stray call records `exhausted`, which the next
      `expect_turn` reports); `print(f"turn {turn_id}: roles {sorted(r.value for r in roles)}")`; return
      `Turn(turn_id, body, ex, roles)`.
   *Invariant: a script that disagrees with production fails the step (AEA-57 AC-2), and no entry leaks into the next
   turn.*
8. `say(run, bp, text, *, table, must, by_marker=None) -> Turn`: `locate(bp.page, "chat.ready").wait_for()`; then
   `expect_turn(...)` with a nested `def send() -> None: locate(bp.page, "chat.composer").fill(text);
   locate(bp.page, "chat.send").click()`.
9. `open_chat(run, bp) -> tuple[BrowserLogin, str]`: `hop = first_hop(bp.page.goto("/"))`; `assert hop.status == 303`;
   `mark = bp.net.mark()`; `login = sign_in_via_form(run, bp)`; `locate(bp.page, "screen.scr1").wait_for(state=
   "visible")`; `start = bp.net.wait_for(bp.page, "startChatSession", since=mark)`; `assert start.status == 201`;
   return `(login, json.loads(start.body)["thread_id"])`. Called inside a step with `needs=CHAT_NEEDS,
   operations=("login", "startChatSession"), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`.
10. `customer_contact(run, customer_id) -> tuple[str, str]`: `row = run.db.one("SELECT name, phone FROM customers WHERE
    customer_id = ?", (customer_id,))`; return `(row["name"], row["phone"])`. Never print either.
11. `submit_locate(run, bp, customer_id, *, previous: Turn, table, must) -> Turn`: assert the last `locate_prompt` block
    of `previous.body` has `["name", "phone"]` in its `field_sets`; `card = locate(bp.page,
    "chat.block.locate_prompt").last`; `name, phone = customer_contact(...)`; `send` fills `locate_in(card,
    "card.locate.name")` with `name`, `locate_in(card, "card.locate.phone")` with `phone`, clicks `locate_in(card,
    "card.locate.submit")`; returns `expect_turn(...)`.
12. `read_code_from_inbox(run, bp) -> tuple[str, ApiExchange]`: `tab = second_tab(bp)`; `mark = bp.net.mark()`;
    `tab.page.goto("/demo/inbox")`; `locate(tab.page, "screen.scr2").wait_for()`; `ex = bp.net.wait_for(tab.page,
    "listDemoInbox", since=mark)`; `assert ex.status == 200`; `newest = max((m for m in json.loads(ex.body)["messages"]
    if m["status"] == "active"), key=lambda m: m["at"])`; `shown = locate_in(locate(tab.page,
    "inbox.message.active").first, "inbox.code").inner_text().strip()`; `assert shown == newest["code"], "SCR-2 shows a
    different code than listDemoInbox returned"` (no value in the message); `tab.page.close()`; return `(shown, ex)`. No
    screenshot while the tab is open. **No WF-3 assertion here** (AC-17 owns it; §8 R-9).
13. `verify_in_chat(run, bp, customer_id, ending, *, opening, opening_table, code_table, code_must, code_by_marker=None)
    -> Verified`: (a) `t1 = say(run, bp, opening, table=opening_table, must={Role.PLANNER, Role.CLASSIFIER})`; assert
    `blocks_of(t1.body, "locate_prompt")`; (b) `t2 = submit_locate(run, bp, customer_id, previous=t1,
    table={Role.RESPONDER: responder("Please type the code when it arrives.")}, must=set())`; assert
    `blocks_of(t2.body, "code_prompt")`; `card = locate(bp.page, "chat.block.code_prompt").last`; `assert f"Code sent to
    the phone on record, ending in {ending}" in card.inner_text()`; (c) `code, inbox = read_code_from_inbox(run, bp)`;
    (d) `t3 = expect_turn(run, bp, table=code_table, by_marker=code_by_marker, must=code_must, send=<fill
    locate_in(card, "card.code.input") with code; click locate_in(card, "card.code.submit")>)`; assert
    `render(TextId.VERIFIED)` is in `locate(bp.page, "chat.entry.assistant").last.inner_text()`; return
    `Verified(customer_id, t1, t3, inbox, phone, code)` (phone from `customer_contact`).
14. `assert_no_excluded(run, thread_id) -> list[str]`: `ids = [pid for r in run.db.rows("SELECT passage_ids FROM
    lookup_log WHERE thread_id = ?", (thread_id,)) for pid in json.loads(r["passage_ids"])]`; `files = [p.split("#",
    1)[0] for p in ids]`; `bad = [f for f in files if f.startswith("archive/") or f in EXCLUDED_FILES]`;
    `assert bad == []`; print `passage ids: …`; return `ids`.
15. `first_passage(index_dir, query, file) -> Passage` (PA-2): `result = FastembedIndex(index_dir,
    model_cache_dir=Path(os.environ["FASTEMBED_CACHE_PATH"])).search(query, k=SEARCH_K, min_score=MIN_SCORE)` (only
    inside `browser_run(..., index=True)`, which holds `fastembed_offline()`); `hits = [p for p in result.passages if
    p.file == file]`; `assert not result.below_floor and hits, f"{query!r}: the index returned no passage from
    {file}"`; return `hits[0]`.
    `passages_hold(index_dir, query, needles) -> None`: the union of `p.text` over the same search's `passages`
    contains every needle; else `AssertionError(f"{query!r}: the passages lack {missing}; change the query wording,
    never the expected facts")`.
16. `knowledge_table(index_dir, query, file, point_text, reply, *, topic) -> Table`: `p = first_passage(...)`; return
    `{Role.PLANNER: planner(knowledge="yes", topic=topic), Role.CLASSIFIER: NORMAL, Role.SPECIALIST:
    (step(tool(KB_SEARCH_NAME, KbSearchArgs(query=query).model_dump())), step(report(KnowledgeReport,
    points=[ReportedPoint(text=point_text, passage_id=p.passage_id)], answered=True))), Role.RESPONDER:
    responder(reply)}`.
17. `assert_turn_records(run, thread_id) -> None` (AC-17, WF-1): for every `turns` row of the thread: `status ==
    "completed"`, `gate_result`, `outcome`, `server_ms` and `trace_export` not null; `run.db.count("check_events",
    "turn_id = ? AND check_kind = 'gate'", (t,)) == 1` (graph-nodes §1: one gate event every turn); and
    `run.db.count("spend_ledger", "turn_id = ?", (t,)) >= 1` for every turn whose `turns.model_calls > 0`. Print one
    line per turn: sequence, gate_result, outcome, server_ms, trace_export, lookup rows, check rows, spend rows.
18. `next_message_id(run) -> int`: `int(run.db.scalar("SELECT COALESCE((SELECT seq FROM sqlite_sequence WHERE name =
    'messages'), 0) + 1 AS n"))`.
19. `switch_role(run, bp, role) -> ApiExchange`: `mark = bp.net.mark()`; `locate(bp.page, f"shell.role.{role}").click()`;
    `ex = bp.net.wait_for(bp.page, "switchRole", since=mark)`; `assert ex.status == 200`; return `ex`.
20. `card_shot(brun, bp, key, label) -> Path`: `brun.screenshot_element(bp, locate(bp.page, key).last, label)`
    (addition A-3). Used for every card screenshot in a flow that showed a locate or code card.
21. `_overrides(settings, script, clock)`: `return step_overrides(settings, cast(StepScript, script), wall_clock=clock)`.
    `browser_run(factory, journey: str, *, index: bool = False, clock: bool = False) -> Iterator[tuple[BrowserRun, Path
    | None]]` (`@contextmanager`):
    1. `kwargs = {"with_clock": clock, "script": StepScript(), "overrides_for": _overrides}`.
    2. If `index`: `with fastembed_offline():` `index_dir = built_index_dir()`; if `index_dir is None`: `with
       factory(**kwargs) as brun: block_here(brun.run, journey, "0 index", "bge-small-en-v1.5 not cached in
       var/fastembed", "environment (fastembed model cache)")`; else `with factory(index_dir=index_dir, **kwargs) as
       brun: yield brun, index_dir`.
    3. Else `with factory(**kwargs) as brun: yield brun, None`.
    *Invariant: every AEA-62 run uses the step-scripted model; the knowledge runs hold the offline fastembed
    environment for the whole run (server and test process are one process).*

### Step 3 — J-2 tests (`tests/journeys/j2/test_aea_62.py`, PHONE)

Turn data (module constants; facts must be substrings of the reply):

| # | Customer text | `kb_search` query | Point text | Reply (responder entry) | Facts asserted visible | `passages_hold` needles |
|---|---|---|---|---|---|---|
| M1 | "What does the Comfort Club membership actually include?" | "What does the Comfort Club membership include?" | "Standard includes two tune-ups a year, priority scheduling and 15% off repairs." | "Comfort Club Standard includes two tune-ups a year (cooling and heating), priority scheduling, the $89 diagnostic fee waived, 15% off repairs, no after-hours dispatch fee, and maintenance reminders. The plan is $149 a year." | "two tune-ups", "priority scheduling", "$89", "15% off repairs", "after-hours", "reminders" | "$89", "15%" |
| M2 | "And how much is it?" | "How much does the Comfort Club membership cost?" | "Standard is $189 a year or $16.99 a month with a 12-month minimum." | "Standard is $189 a year, or $16.99 a month with a 12-month minimum. Each additional system is $99 a year." | "$189", "$16.99", "12-month minimum", "$99" | "$189", "$16.99", "$99" |
| M3 | "Does it cover plumbing?" | "Does the Comfort Club membership cover plumbing?" | "Plus is $269 a year and adds plumbing items." | "Standard covers heating and cooling only. Comfort Club Plus is $269 a year and adds an annual water-heater flush and inspection, a plumbing inspection, and 15% off plumbing repairs." | "$269", "water-heater flush", "plumbing inspection", "15% off plumbing repairs" | "$269" |

File `MEMBERSHIP_FILE = "membership/comfort_club_overview.md"`, topic `"membership"`. The "$149" sentence in M1 is the
adversarial draft (R-46 must remove it). `STALE = ("$149", "$12.99", "$219", "10% off", "cancel any time for a full
prorated refund", "transfers to a new address")`; compare lower-cased page text with lower-cased strings.

`membership_leg(brun, index_dir) -> tuple[BrowserPage, str, list[Turn]]`: `bp = brun.open(PHONE)`; step "2a sign in
and chat" (`open_chat`); for M1…M3: `passages_hold(index_dir, query, needles)` then step f"2b turn {n}"
(`needs=TURN_NEEDS, operations=("submitTurn",), selectors=(*CHAT_SELECTORS, "chat.source")`): `say(run, bp, text,
table=knowledge_table(index_dir, query, MEMBERSHIP_FILE, point, reply, topic="membership"), must={Role.PLANNER,
Role.CLASSIFIER, Role.SPECIALIST, Role.RESPONDER})`. Returns the page, thread id and turns.

1. **`test_j2_membership_with_source(browser_journey_factory)`** (AC-2) — `with browser_run(browser_journey_factory,
   J2, index=True) as (brun, index_dir):` run the leg, then per turn n, step f"2c checks {n}" (selectors
   `chat.entry.assistant`, `chat.block.text`, `chat.source`, `chat.source.toggle`, `chat.source.excerpt`):
   - `entry = locate(page, "chat.entry.assistant").last` (for n < 3 read the entry right after its turn, inside the
     leg loop, before the next turn; simplest: run checks inside the loop); every fact of the row is in
     `entry.inner_text()`.
   - `api_chips = chips_of(turn.body)`; at least one has `file == MEMBERSHIP_FILE` and none names an excluded file.
   - `chip = locate_in(entry, "chat.source").first`; `MEMBERSHIP_FILE in chip.inner_text()`; click
     `locate_in(chip, "chat.source.toggle")`; `locate_in(entry, "chat.source.excerpt").first.inner_text().strip() ==
     api_chips[0]["excerpt"].strip()`.
   - Stored: `ids = {pid for r in run.db.rows("SELECT passage_ids FROM lookup_log WHERE turn_id = ?", (turn.turn_id,))
     for pid in json.loads(r["passage_ids"])}`; `{c["passage_id"] for c in api_chips} <= ids`; print `chip files |
     lookup ids` side by side.
   - After turn 3: `run.db.count("actions", "thread_id = ? AND kind = 'verified'", (tid,)) == 0`;
     `run.db.count("cases", "thread_id = ?", (tid,)) == 0`; `run.db.scalar("SELECT outcome FROM conversations WHERE
     thread_id = ?", (tid,)) != "handed_off"`; `brun.screenshot(bp, "after-third-reply")`.
   - Step "2d records": `assert_turn_records(run, tid)`.
2. **`test_j2_stale_values_absent(browser_journey_factory)`** (AC-3) — its own `browser_run(index=True)` and
   `membership_leg`; step "3a stale strings": after each turn, `hits = {s: page_text(page).lower().count(s.lower()) for
   s in STALE}`; all zero; print the dict. Step "3b fact check removed $149": `rows = run.db.rows("SELECT * FROM
   check_events WHERE turn_id = ? AND check_kind = 'fact' AND result = 'trimmed'", (m1.turn_id,))`; `len(rows) == 1 and
   rows[0]["removed"] >= 1`; `"$149" not in json.dumps(rows[0])`. Step "3c no excluded source": `assert_no_excluded(run,
   tid)`; no API chip of any turn names an excluded file.
3. **`test_j2_invoice_after_code_as_billed(browser_journey_factory)`** (AC-4; WP-2; no index) — `with
   browser_run(browser_journey_factory, J2) as (brun, _):` `bp = brun.open(PHONE)`; step "4a sign in and chat"; step
   "4b ask, locate, code" (`needs=VERIFY_NEEDS, operations=("submitTurn", "listDemoInbox"), selectors=(*CHAT_SELECTORS,
   *IDENTITY_SELECTORS, "chat.block.account_card")`): `v = billing_through_code(run, bp, tid)` where
   `billing_through_code(run, bp, thread_id) -> Verified` = `verify_in_chat(run, bp, "MHC-10002", "02",
   opening=BILLING_TEXT, opening_table=BILLING_OPENING, code_table=BILLING_CODE, code_must={Role.SPECIALIST,
   Role.RESPONDER})` and, between the locate turn and the code turn, the no-invoice-value check below (implement by
   giving `verify_in_chat` an optional `before_code: Callable[[], None] | None = None` called right after (b)). Constants:
   `BILLING_TEXT = "I got an invoice, INV-204411, and I'm not sure what it's for."`;
   `BILLING_OPENING = {Role.PLANNER: planner(account="invoice", topic="billing"), Role.CLASSIFIER: NORMAL,
   Role.RESPONDER: responder("I can explain that invoice once I've confirmed your account.")}`;
   `BILLING_CODE = {Role.SPECIALIST: (step(tool(READ_INVOICES_NAME, ReadInvoicesArgs(invoice_number="INV-204411")
   .model_dump(mode="json"))), step(report(AccountReport, summary="Invoice INV-204411 lists a diagnostic visit, a
   contactor replacement and an after-hours dispatch."))), Role.RESPONDER: responder(INVOICE_REPLY)}`;
   `INVOICE_REPLY = "Invoice INV-204411 has three lines as billed: a diagnostic visit, $89.00; a contactor replacement,
   $245.00; and an after-hours dispatch, $144.00. The total is $478.00, due November 1, 2026."`.
   **The invoice is read on the code turn** (§4.6, `route_after_identity`): if the code turn's `roles never called:
   ['specialist']` assertion fires, that is a seam finding on AEA-37/AEA-39 (task resumption); report it; do not add a
   later turn.
   - Before the code turn: `for s in ("$478.00", "$245.00", "$144.00", "$89.00"): assert s not in page_text(page)`.
   - Visible after: last assistant entry contains `render(TextId.VERIFIED)`; `card = locate(page,
     "chat.block.account_card").last`; card text contains "INV-204411", "$89.00", "$245.00", "$144.00", "$478.00".
   - API: `acc = blocks_of(v.code_turn.body, "account_card")[-1]["invoice"]`; `acc["invoice_id"] == "INV-204411"`;
     `[l["amount"]["display"] for l in acc["lines"]] == ["$89.00", "$245.00", "$144.00"]`;
     `acc["total"]["display"] == "$478.00"`; `acc["due_on"] == "2026-11-01"`.
   - Not on the page: "$149"; and none of `VERDICT = ("bill is wrong", "charged incorrectly", "overcharged", "credit is
     owed", "owe you a credit")` (case-insensitive).
   - Stored: `ver = run.db.one("SELECT a.turn_id, t.sequence FROM actions a JOIN turns t ON t.turn_id = a.turn_id WHERE
     a.thread_id = ? AND a.kind = 'verified'", (tid,))`; `inv = [r for r in run.db.rows("SELECT l.id, l.record_ids,
     t.sequence FROM lookup_log l JOIN turns t ON t.turn_id = l.turn_id WHERE l.thread_id = ?", (tid,)) if
     "INV-204411" in json.loads(r["record_ids"])]`; `len(inv) >= 1` and every `r["sequence"] >= ver["sequence"]`;
     `run.db.count("cases", "thread_id = ?", (tid,)) == 0`; `assert_no_excluded(run, tid)`; print page values and the
     row order (sequence numbers and ids only).
   - `card_shot(brun, bp, "chat.block.account_card", "account-card")`. Step "4c records": `assert_turn_records`.
4. **`test_j2_warranty_current_policy(browser_journey_factory)`** (AC-5) — `browser_run(index=True)`;
   `WARRANTY_FILE = "warranty/warranty_policy.md"`, `ARCHIVE_WARRANTY = "archive/warranty_terms_2023.txt"`; text and
   query "How long is the repair warranty?"; point "Repairs carry a 1-year labor warranty on the part repaired.";
   reply "Repairs come with a 1-year labor warranty on the part we repaired."; topic `"warranty"`; `passages_hold`
   needle `"1"`. Steps "5a sign in and chat", "5b turn" (as 2b with `knowledge_table(..., WARRANTY_FILE, ...,
   topic="warranty")`), "5c checks": entry text contains "1-year"; a chip `file == WARRANTY_FILE` and `"2025-06-15" in
   (chip["version_date"] or "") + chip["version_label"]`; visible chip names the file; `"90-day"` and `"90 days"` absent
   from `page_text` (lower-cased); stored: the turn's lookup ids include one starting `WARRANTY_FILE + "#"` and none
   starting `ARCHIVE_WARRANTY`; `run.db.count("actions", "thread_id = ? AND kind = 'verified'", (tid,)) == 0`;
   `assert_no_excluded`; step "5d records".

### Step 4 — J-3 tests (`tests/journeys/j3/test_aea_62.py`, PHONE; no index)

`book_slot_56(brun, bp) -> Booking` (dataclass: `thread_id: str, booking: Turn, appointment_id: int, counts: dict[str,
Any]`), steps:

- "6a sign in and chat" (`open_chat`).
- "6b ask, locate, code" (`needs=VERIFY_NEEDS, operations=("submitTurn", "listDemoInbox")`,
  `selectors=(*CHAT_SELECTORS, *IDENTITY_SELECTORS, "chat.block.slot_card")`): `verify_in_chat(run, bp, "MHC-10001",
  "01", opening=BOOK_TEXT, opening_table={Role.PLANNER: planner(scheduling="book_new", topic="booking"),
  Role.CLASSIFIER: NORMAL, Role.RESPONDER: responder("I can look for a time once I've confirmed your account.")},
  code_table={Role.SPECIALIST: (step(tool(FIND_WINDOWS_NAME, FindWindowsArgs(service_type="hvac_repair",
  wanted_text="This Saturday if possible, 4 to 7, after work.").model_dump(mode="json"))), step(report(SchedulingReport,
  appointment_id=0, wanted_time="Saturday 4 to 7 pm", note="AC not cooling"))), Role.RESPONDER: responder("There's no
  Saturday evening window, so here are the earliest repair windows.")}, code_must={Role.SPECIALIST, Role.RESPONDER})`,
  `BOOK_TEXT = "I need to schedule a service call. My AC isn't cooling. This Saturday if possible, 4 to 7, after
  work."`. After the opening turn assert no `safety`/`emergency_line` block and no case (WP-3: not an emergency).
  Slot card checks: `card = blocks_of(code_turn.body, "slot_card")[-1]`; `mon = {w["slot_id"]: w for d in card["days"]
  if d["date"] == "2026-10-19" for w in d["windows"]}`; `{"56", "42", "58"} <= set(mon)`;
  `mon["56"]["technician"] == "Marta Kowalski"`, `mon["42"]["technician"] == "Ray Mendoza"`,
  `mon["58"]["technician"] == "Marta Kowalski"`; `mon["56"]["window_label"] == "8:00 am – 12:00 pm"`; no `d["date"] ==
  "2026-10-17"`; visible slot card text contains "8:00 am – 12:00 pm", "Marta Kowalski", "Ray Mendoza". Print offered
  windows (slot id, label, technician).
- "6c pick 8–12" (`needs=TURN_NEEDS, operations=("submitTurn",), selectors=("chat.block.slot_card",
  "card.slot.window_by_id", "card.slot.continue", "chat.block.confirmation", "settled.visit")`): `card_el =
  locate(page, "chat.block.slot_card").last`; `booking = expect_turn(run, bp, table={Role.SPECIALIST:
  (step(tool(BOOK_VISIT_NAME, BookVisitArgs(slot_id=56, issue="AC not cooling").model_dump())),
  step(report(SchedulingReport, appointment_id=0, wanted_time="", note="booked"))), Role.RESPONDER:
  responder(BOOKED_REPLY)}, must={Role.RESPONDER}, send=<click locate_by(card_el, "card.slot.window_by_id", "56");
  click locate_in(card_el, "card.slot.continue")>)`, `BOOKED_REPLY = "You're booked for Monday, October 19, 8:00 am to
  12:00 pm with Marta Kowalski."`. (If booking runs in code, the specialist entries simply go unused.)
  - Visible: page text contains `render(TextId.BOOKED)`; `conf = locate(page, "chat.block.confirmation").last` text
    contains "Your visit", "Booked", "8:00 am → 12:00 pm", "Marta Kowalski" and ("October 19" or "Oct 19"); `api =
    blocks_of(booking.body, "confirmation")[-1]`; `api["date"] == "2026-10-19"`; `api["fee_line"] in conf.inner_text()`;
    `"waived" in api["fee_line"].lower()`; `re.search(r"\$89(\.00)?\s+(is\s+)?due|amount due", page_text(page), re.I)
    is None`; `locate(page, "settled.visit")` text contains "Marta Kowalski"; `booking.body["settled"]["visit"]
    ["appointment_id"] == api["appointment_id"]` and `["status"] == "booked"`.
  - Stored: `run.db.scalar("SELECT status FROM appointment_slots WHERE slot_id = 56") != "open"`;
    `run.db.count("appointments", "customer_id = ? AND slot_id = ? AND status = 'scheduled'", ("MHC-10001", 56)) == 1`;
    `b = run.db.rows("SELECT * FROM actions WHERE thread_id = ? AND kind = 'booked'", (tid,))`; `len(b) == 1` and
    `b[0]["turn_id"] == booking.turn_id`; `run.db.count("lookup_log", "thread_id = ? AND tool = ?", (tid,
    FIND_WINDOWS_NAME)) >= 1`; `run.db.count("cases", "thread_id = ?", (tid,)) == 0`; `sha256_file(ISSUED_DB) ==
    run.env.issued_sha256_before`. `counts = {"appointments": run.db.count("appointments", "customer_id = ?",
    ("MHC-10001",)), "booked": len(b), "slot56": <status>, "slot58": <status>}`. Print row ids and both hashes.
  - `card_shot(brun, bp, "chat.block.confirmation", "confirmation-card")`.

1. **`test_j3_book_to_confirmation(browser_journey_factory)`** (AC-6) — `browser_run(J3)`; the driver, then step "6d
   records" (`assert_turn_records`).
2. **`test_j3_reload_and_follow_up_remembers(browser_journey_factory)`** (AC-7) — driver, then:
   - "7a reload" (`needs=TURN_NEEDS, operations=("getChatThread",), selectors=("chat.entry", "chat.block.text",
     "chat.entry.customer", "chat.block.confirmation", "settled.visit")`): `mark`; `page.reload()`; `read =
     bp.net.wait_for(page, "getChatThread", since=mark)`; `read.status == 200`; `read.path.endswith("/" + tid)`;
     `"startChatSession" not in bp.net.operations(mark)`; the first `chat.entry`'s `chat.block.text` text ==
     `render(TextId.GREETING)`; `json.loads(read.body)["turns"][0]["turn_id"] == "greeting"`; `locate(page,
     "chat.entry.customer").count() >= 3`; `locate(page, "chat.block.confirmation").count() >= 1`; settled visit text
     contains "Marta Kowalski" and `json.loads(read.body)["settled"]["visit"]["appointment_id"] == appointment_id`.
   - "7b follow-up" (`needs=TURN_NEEDS, operations=("submitTurn",), selectors=CHAT_SELECTORS`): `t = say(run, bp,
     "Yes, please.", table={Role.PLANNER: planner(topic="booking"), Role.CLASSIFIER: NORMAL, Role.RESPONDER:
     responder(FOLLOW_REPLY)}, must={Role.PLANNER, Role.CLASSIFIER, Role.RESPONDER})`, `FOLLOW_REPLY = "Yes, you're
     booked: Monday, October 19, 8:00 am to 12:00 pm with Marta Kowalski."`; the last assistant entry's text block
     `.strip() == FOLLOW_REPLY` (kept whole); `c = run.db.one("SELECT * FROM check_events WHERE turn_id = ? AND
     check_kind = 'completion'", (t.turn_id,))`; `c["result"] == "pass" and c["removed"] == 0`;
     `run.db.count("check_events", "turn_id = ? AND result = 'trimmed'", (t.turn_id,)) == 0`;
     `t.body["settled"]["visit"]["appointment_id"] == int(run.db.scalar("SELECT record_id FROM actions WHERE thread_id
     = ? AND kind = 'booked'", (tid,)))`; `t.body["settled"]["identity"]["status"] == "verified"`; counts equal the
     driver's. Print `", ".join(bp.net.operations())`, the reply text, and the counts before and after.
3. **`test_j3_old_card_writes_nothing(browser_journey_factory)`** (AC-8) — driver, reload (as 7a: only the
   `getChatThread` 200 and no `startChatSession`), then:
   - "8a replay booking turn" (`needs=TURN_NEEDS, operations=("submitTurn",)`): `r = page_post(bp,
     f"/api/chat/sessions/{tid}/turns", json.loads(booking.exchange.request_body))`; `r["status"] == 200`;
     `json.loads(r["text"])["turn_id"] == booking.turn_id`; counts equal. (No `set_step` needed: a replay runs no
     model.)
   - "8b old card" (`selectors=("chat.block.slot_card", "card.slot.window_by_id", "card.slot.continue")`): `w =
     locate_by(locate(page, "chat.block.slot_card").first, "card.slot.window_by_id", "58")`; if `not w.is_enabled()` or
     `w.get_attribute("aria-disabled") == "true"`: print "old card disabled after reload" (the visible *answered* state
     is out of scope until audit A-3 has an owner); else `expect_turn(run, bp, table={Role.PLANNER:
     planner(topic="booking"), Role.CLASSIFIER: NORMAL, Role.RESPONDER: responder("Your visit stays on Monday
     morning.")}, must=set(), send=<click w; click locate_in(card, "card.slot.continue")>)`. Then counts equal, slot 58
     status still `open`, and still exactly one `booked` row. Print counts and slot statuses before and after.

### Step 5 — J-6 tests (`tests/journeys/j6/test_aea_62.py`)

`refund_case(brun) -> RefundCase` (dataclass: `bp, thread_id, ref, turn, login`), PHONE:

- "9a sign in and chat".
- "9b refund" (`needs=HANDOFF_NEEDS, operations=("submitTurn",), selectors=(*CHAT_SELECTORS, "chat.block.handoff",
  "settled.request")`): `msg_id = next_message_id(run)`; `t = say(run, bp, REFUND_TEXT, table={Role.PLANNER:
  planner(handoff="refund", topic="billing"), Role.CLASSIFIER: NORMAL, Role.RESPONDER: responder("I'm sorry the repair
  didn't fix the problem."), Role.BRIEF: brief(needs=[Quote(message_id=msg_id, text="I want a full refund on the
  repair.")], claims=[Quote(message_id=msg_id, text="It didn't fix anything"), Quote(message_id=msg_id, text="I had to
  call another company")], open_decision="Decide between a refund, a warranty recall, or neither.")}, must={Role.PLANNER,
  Role.CLASSIFIER, Role.RESPONDER, Role.BRIEF})`, `REFUND_TEXT = "I want a full refund on the repair. It didn't fix
  anything and I had to call another company."`. Then `run.db.scalar("SELECT id FROM messages WHERE turn_id = ? AND
  role = 'customer'", (t.turn_id,)) == msg_id` (else stop: the id prediction is a plan error; report it, do not change
  the quotes).
  - API: `h = blocks_of(t.body, "handoff")[-1]`; `m = re.fullmatch(r"MHC-C-(\d{4})", h["reference"])`; `m and
    int(m.group(1)) >= 9`; `ref = h["reference"]`; `h["promise_text"] == PROMISE_TABLE["R26.refund"]`;
    `render(TextId.PROMISE_REFUND_NO_OUTCOME) in h["extra_lines"]`; `t.body["settled"]["request"]["reference"] == ref`.

1. **`test_j6_refund_handoff_in_chat(browser_journey_factory)`** (AC-9) — `browser_run(J6)`; driver; step "9c card and
   stored":
   - Visible: `card = locate(page, "chat.block.handoff").last` text contains `ref`, the promise text,
     `render(TextId.PROMISE_REFUND_NO_OUTCOME)`, "Tue Oct 20 · 7:00 pm", `render(TextId.FOLLOWUP_LEGEND)`; and the
     promise text appears before "I can't promise an outcome." in `card.inner_text()`; `locate(page, "settled.request")`
     text contains `ref`.
   - Stored: `c = run.db.one("SELECT * FROM cases WHERE thread_id = ?", (tid,))`; `c["case_ref"] == ref`; `c["reason"]
     == "refund"`; `c["priority"] == "P3"`; `datetime.fromisoformat(c["due_at"]) == datetime(2026, 10, 20, 19, 0,
     tzinfo=CHI)`; `p = run.db.one("SELECT * FROM promises WHERE case_ref = ?", (ref,))`; `p["text"] ==
     PROMISE_TABLE["R26.refund"]` and `p["status"] == "open"`; `run.db.count("case_events", "case_ref = ? AND kind =
     'case_opened'", (ref,)) == 1`; `ev = run.db.rows("SELECT payload FROM events WHERE stream = ? AND type =
     'case_created'", (tid,))`; `len(ev) == 1 and json.loads(ev[0]["payload"])["case_ref"] == ref` (refresh 3 item 1); `run.db.scalar("SELECT outcome FROM turns WHERE turn_id = ?", (t.turn_id,)) ==
     "handed_off"`; `run.db.scalar("SELECT outcome FROM conversations WHERE thread_id = ?", (tid,)) == "handed_off"`.
     Print the card text and rows. `brun.screenshot(bp, "handoff-card")` (no identity values were shown in this chat).
   - Step "9d records": `assert_turn_records`.
2. **`test_j6_case_in_staff_queue(browser_journey_factory)`** (AC-10) — `browser_run(J6)`; driver; step "10a switch"
   (`needs=STAFF_NEEDS, operations=("switchRole", "getQueue"), selectors=("shell.role.representative", "screen.scr5",
   "queue.row", "queue.row_by_ref")`): `before = run.db.one("SELECT session_id, role FROM staff_sessions")`;
   `events_before = run.db.count("case_events")`; `page.set_viewport_size({"width": DESKTOP.width, "height":
   DESKTOP.height})`; `mark`; `switch_role(run, bp, "representative")`; `q = bp.net.wait_for(page, "getQueue",
   since=mark)`; `q.status == 200`; `urlsplit(page.url).path == "/staff/queue"`; `locate(page, "screen.scr5").wait_for()`;
   `"Riley · demo representative" in page_text(page)`.
   - API: `rows = json.loads(q.body)["needs_my_action"]`; `refs = [r["reference"] for r in rows]`; `refs[0] ==
     "MHC-C-0008"`; `set(SEED_REFS) | {ref} <= set(refs)`; `mine = next(r for r in rows if r["reference"] == ref)`;
     `mine["priority"] == {"level": "P3", "word": "Standard"}`; `mine["owner"] is None`.
   - Visible: `row = locate_by(page, "queue.row_by_ref", ref)` text contains "P3 · Standard", `ref`, `mine["reason"]`,
     "Unowned", "Tue Oct 20 · 7:00 pm"; `first = locate(page, "queue.row").first` text contains "MHC-C-0008" and "P0 ·
     Safety"; `locate(page, "queue.row").count() >= 5`.
   - Stored: `after = run.db.one("SELECT session_id, role FROM staff_sessions")`; same `session_id`, role
     `representative` (before `customer`); `run.db.count("case_events") == events_before`. Print the row order and
     texts, role before and after. `brun.screenshot(bp, "scr5")`.
3. **`test_j6_case_view_brief_and_promise(browser_journey_factory)`** (AC-11) — **`browser_run(J6, index=True)`**
   (the staff guidance needs `staff_notes.json`, §4.6; without the cached model the run blocks with owner
   "environment (fastembed model cache)", never passes); driver; switch as 10a (only the 200 and
   the path); step "11a open case" (`needs=STAFF_NEEDS, operations=("getCase",), selectors=("queue.row_by_ref",
   "screen.scr6", "case.root", "case.owner", "case.promise", "case.promise.open", "brief.section_by_number",
   "brief.heading", "brief.item.tag", "case.sources_tab", "case.source_by_id")`): `version_before =
   run.db.scalar("SELECT version FROM cases WHERE case_ref = ?", (ref,))`; `events_before = run.db.count("case_events",
   "case_ref = ?", (ref,))`; `mark`; click `locate_by(page, "queue.row_by_ref", ref)`; `g = bp.net.wait_for(page,
   "getCase", since=mark)`; `g.status == 200`; `urlsplit(page.url).path == f"/staff/cases/{ref}"`; `d = json.loads(g.body)`.
   - Visible: `locate(page, "case.owner")` text contains "Unassigned, nobody owns it yet"; `locate(page,
     "case.promise.open")` visible and its text contains `PROMISE_TABLE["R26.refund"]` and "Open"; for `n` in 1…8:
     `locate_in(locate_by(page, "brief.section_by_number", str(n)), "brief.heading").inner_text().strip() ==
     BRIEF_TITLES[n - 1]`; section 4 (`sec4 = locate_by(page, "brief.section_by_number", "4")`): `locate_in(sec4,
     "brief.item.tag")` text contains "Customer says · not checked", and `sec4.inner_text()` contains "It didn't fix
     anything" and "I had to call another company".
   - API: `[h["title"] for h in d["brief"]["headings"]] == list(BRIEF_TITLES)`; heading 4 items with `kind == "claim"`
     include both quote texts; `h7 = d["brief"]["headings"][6]`; `guide = [i for i in h7["items"] if i["kind"] == "fact" and
     i["text"].startswith(STAFF_GUIDANCE_FOR[HandoffReason.REFUND][0])]`; `len(guide) == 1 and guide[0]["source_ids"]`;
     `g_src = next(s for s in d["sources"] if s["source_id"] == guide[0]["source_ids"][0])`; `g_src["audience"] ==
     "staff_only"`; `ids = {s for h in
     d["brief"]["headings"] for i in h["items"] for s in i["source_ids"]}`; `ids <= {s["source_id"] for s in
     d["sources"]}`; `d["promise"]["status"] == "open"`.
   - Visible chips: click `locate(page, "case.sources_tab")`; for each `sid` in `sorted(ids)`: `locate_by(page,
     "case.source_by_id", sid)` is visible. Print heading titles, claims, and `sid → title` pairs.
   - Stored: `stored = json.loads(run.db.scalar("SELECT brief_json FROM case_briefs WHERE case_ref = ?", (ref,)))`; its
     heading titles == `BRIEF_TITLES`; per heading `[i["kind"] for i in items]` equal `d`'s (same count, same order);
     for headings 2 and 4 the item texts equal `d`'s exactly (wire texts elsewhere are masked, §4.6); `cases.version == version_before`;
     `case_events` count unchanged. `brun.screenshot(bp, "case-brief")`.
4. **`test_j6_membership_cancel_honest_limit(browser_journey_factory)`** (AC-12; WP-8) — **`browser_run(J6,
   index=True)`** (its knowledge specialist calls `kb_search`), PHONE. "12a sign in and chat"; "12b ask, locate, code"
   (`needs=(*VERIFY_NEEDS, "handoff_service", "case_service")`, selectors `(*CHAT_SELECTORS, *IDENTITY_SELECTORS,
   "chat.block.handoff")`): `msg1 = next_message_id(run)` before the opening turn; `v = verify_in_chat(run, bp,
   "MHC-10001", "01", opening=CANCEL_TEXT, opening_table={Role.PLANNER: planner(account="membership",
   handoff="membership_cancel", topic="membership"), Role.CLASSIFIER: NORMAL, Role.RESPONDER: responder("I can help
   once I've confirmed your account.")}, code_table=CANCEL_CODE, code_by_marker=CANCEL_MARKERS,
   code_must={Role.SPECIALIST, Role.RESPONDER, Role.BRIEF})`; check `msg1` after the opening turn as in 9b.
   Constants: `CANCEL_TEXT = "I want to cancel my Comfort Club membership."`;
   `CANCEL_CLAIM = "Done, auto-renew is off."`;
   `CANCEL_CODE = {Role.RESPONDER: responder("I can't switch off auto-renewal from this chat. " + CANCEL_CLAIM),
   Role.BRIEF: brief(needs=[Quote(message_id=msg1, text=CANCEL_TEXT)], claims=[], open_decision="Switch off
   auto-renewal before the renewal date.")}` (built after `msg1` is known);
   `CANCEL_MARKERS = {KB_SEARCH_NAME: {Role.SPECIALIST: (step(tool(KB_SEARCH_NAME, KbSearchArgs(query="How do I cancel
   a Comfort Club membership?").model_dump())), step(report(KnowledgeReport, points=[], answered=False)))},
   READ_MEMBERSHIP_NAME: {Role.SPECIALIST: (step(tool(READ_MEMBERSHIP_NAME, ReadMembershipArgs().model_dump())),
   step(report(AccountReport, summary="Standard plan, renews 2026-11-03.")))}}` — **this dict order is required**: the
   knowledge request's JSON contains both words (`kb_search`'s description names `read_membership`), the account
   request's JSON contains only `read_membership`, and `by_marker` takes the first match in dict order. *Invariant:
   each specialist gets its own two rounds whatever order the threads run in.*
   - Visible: page text contains "I can't switch off auto-renewal from this chat." and not "Done, auto-renew is off";
     handoff card text contains "A representative will get back to you within 1 business day".
   - Stored: `c = run.db.one("SELECT * FROM cases WHERE thread_id = ?", (tid,))`: reason `membership_cancel`, priority
     `P3`; `run.db.count("promises", "case_ref = ?", (c["case_ref"],)) == 1`; `run.db.count("check_events", "turn_id = ?
     AND check_kind = 'completion' AND result = 'trimmed'", (v.code_turn.turn_id,)) >= 1`; `run.db.count("lookup_log",
     "turn_id = ? AND tool = ?", (v.code_turn.turn_id, READ_MEMBERSHIP_NAME)) >= 1`; the working-copy `customers` row of
     MHC-10001 equals the issued row (`[r for r in issued_rows("customers") if r[0] == "MHC-10001"] == [r for r in
     run.db.table_rows("customers") if r[0] == "MHC-10001"]`; compare, never print).
   - `card_shot(brun, bp, "chat.block.handoff", "cancel-handoff")` before switching.
   - "12c in the queue" (`needs=STAFF_NEEDS, operations=("switchRole", "getQueue"),
     selectors=("shell.role.representative", "queue.row_by_ref")`): desktop viewport; `switch_role`; `locate_by(page,
     "queue.row_by_ref", c["case_ref"])` text contains "P3 · Standard". Step "12d records": `assert_turn_records`.

### Step 6 — J-8 tests (`tests/journeys/j8/test_aea_62.py`, DESKTOP; every run through `browser_run`)

`SEED_CASE = "MHC-C-0006"` (a seed with no identity data; assert `run.db.count("cases", "case_ref = ? AND seed = 1",
(SEED_CASE,)) == 1` first). `EXPECTED_DISPLAY = {"customer": "Customer (demo)", "representative": "Riley, demo
representative", "supervisor": "Demo supervisor", "owner": "Demo business owner"}`.

1. **`test_j8_role_switch_and_resume(browser_journey_factory)`** (AC-13):
   - "13a sign in and chat": `open_chat` → `login`, `thread_a`; `sid = login.session_id`.
   - "13b to representative" (`needs=STAFF_NEEDS, operations=("switchRole", "getQueue"),
     selectors=("shell.role.representative", "screen.scr5")`): `switch_role`; path `/staff/queue`; role column
     `representative`, session id `sid`.
   - "13c back to customer" (`needs=CHAT_NEEDS, operations=("switchRole", "getChatThread"),
     selectors=("shell.role.customer", "screen.scr1")`): `mark`; `switch_role(..., "customer")`; path `/`; `read =
     bp.net.wait_for(page, "getChatThread", since=mark)`; `read.path.endswith("/" + thread_a)`; `"startChatSession" not
     in bp.net.operations(mark)`.
   - "13d case reload keeps role" (`needs=STAFF_NEEDS, operations=("switchRole", "getCase", "getSession"),
     selectors=("shell.role.representative", "screen.scr6")`): switch to representative;
     `page.goto(f"/staff/cases/{SEED_CASE}")`; getCase 200; `events = run.db.count("case_events", "case_ref = ?",
     (SEED_CASE,))`; `mark`; `page.reload()`; `s = bp.net.wait_for(page, "getSession", since=mark)`;
     `json.loads(s.body)["role"] == "representative"`; getCase 200 again since mark; `case_events` count unchanged.
   - "13e tab A chats while tab B is representative" (`needs=TURN_NEEDS, operations=("switchRole", "submitTurn"),
     selectors=(*CHAT_SELECTORS, "shell.role.customer", "shell.role.representative", "screen.scr4")`): switch tab A
     back to customer and `page.goto("/")` (resumes `thread_a`, no new start); `tab_b = second_tab(bp)`;
     `tab_b.page.goto("/role")`; `switch_role(run, tab_b, "representative")`; `bp.page.bring_to_front()`; `say(run, bp,
     CUSTOMER_TEXT, table={Role.PLANNER: PLANNER_RAW, Role.CLASSIFIER: CLASSIFIER_RAW, Role.RESPONDER:
     responder(RESPONDER_TEXT)}, must={Role.PLANNER, Role.CLASSIFIER, Role.RESPONDER})`; last assistant text ==
     `RESPONDER_TEXT`.
   - Stored: `run.db.count("staff_sessions") == 1`; its role `representative`, its session id `sid`;
     `run.db.count("conversations", "demo_session = ?", (sid,)) == 1`. Print the role column after each switch, the
     operation sequence, and the conversation count.
2. **`test_j8_customer_refused_then_switch_allowed(browser_journey_factory)`** (AC-14): `first_hop(page.goto("/"))`
   then `sign_in_via_form` (no chat needed); step "14a refused" (`needs=STAFF_NEEDS, operations=("getQueue",),
   selectors=("role.panel", "queue.row")`): `events = run.db.count("case_events")`; `mark`; `r =
   page.goto("/staff/queue")`; `r.status == 200`; `q = bp.net.wait_for(page, "getQueue", since=mark)`; `q.status ==
   403`; `err = json.loads(q.body)["error"]`; `err["code"] == "ROLE_NOT_ALLOWED"`; `err["details"]["reason"] ==
   "wrong_role"`; `locate(page, "role.panel").inner_text().strip()` contains "You're acting as the customer. Switch to a
   staff role to see this."; `locate(page, "queue.row").count() == 0`; role column `customer`; screenshot `refused`.
   Print code and reason only. Step "14b switch allowed" (`operations=("switchRole", "getQueue"),
   selectors=("shell.role.representative", "queue.row")`): `mark`; `switch_role`; `bp.net.wait_for(page, "getQueue",
   since=mark)` status 200; `locate(page, "queue.row").count() >= 4`; role column `representative`; `case_events`
   count unchanged; screenshot `allowed`.
3. **`test_j8_signed_out_and_expired(browser_journey_factory)`** (AC-15; `browser_run(J8, clock=True)`):
   - "15a sign in, chat, open case": `open_chat` → `login_1`, `thread_1`; switch to representative;
     `page.goto(f"/staff/cases/{SEED_CASE}")`; getCase 200.
   - "15b sign out on SCR-6" (`operations=("logout",), selectors=("shell.sign_out", "screen.scr12")`):
     `sign_out_via_shell`; `locate(page, "screen.scr12").wait_for()`; `run.db.count("staff_sessions", "session_id = ?",
     (login_1.session_id,)) == 0`.
   - "15c reload case signed out": `hop = first_hop(page.goto(f"/staff/cases/{SEED_CASE}"))`; `hop.status == 303`;
     `hop.headers["location"] == f"/login?return_to=%2Fstaff%2Fcases%2F{SEED_CASE}&reason=none"`.
   - "15d sign in again lands there" (`needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SELECTORS`):
     `login_2 = sign_in_via_form(run, bp)`; `login_2.session_id != login_1.session_id`; `urlsplit(page.url).path ==
     f"/staff/cases/{SEED_CASE}"` (a fresh login is role customer, so the page may show the role panel; only the URL is
     asserted).
   - "15e SCR-1 starts fresh" (`needs=CHAT_NEEDS, operations=("startChatSession", "getChatThread"),
     selectors=("screen.scr1",)`): `mark`; `page.goto("/")`; `start = bp.net.wait_for(page, "startChatSession",
     since=mark)`; `ops = bp.net.operations(mark)`; if any exchange in `bp.net.exchanges` with `index >= mark`,
     `operation_id == "getChatThread"` and `path.endswith("/" + thread_1)` exists: `block_here(run, J8, "15e SCR-1
     starts fresh", "SCR-1 start fresh (the page requested the earlier thread)", "UX session")`;
     `ops.count("startChatSession") == 1`; `json.loads(start.body)["thread_id"] != thread_1`; `f = page_fetch(bp,
     f"/api/chat/sessions/{thread_1}")`; `f["status"] == 404`; `json.loads(f["text"])["error"]["code"] ==
     "SESSION_NOT_FOUND"`. Print the operation sequence and the 404 body (it holds only `error` and `request_id`).
   - "15f expired" (`needs=(*SIGN_IN_NEEDS, "staff_access"), selectors=("login.message.expired",)`): if `run.clock is
     None`: `block_here(run, J8, "15f expired", "wall-clock control in the browser run", "AEA-58")`;
     `run.clock.advance(run.container.limits.web.login_session_lifetime_s + 1)`; `hop =
     first_hop(page.goto("/staff/queue"))`; `hop.status == 303`; `hop.headers["location"] ==
     "/login?return_to=%2Fstaff%2Fqueue&reason=expired"`; `cookies = [h["value"] for h in hop.headers_array() if
     h["name"].lower() == "set-cookie" and h["value"].startswith("mhc_session=")]`; `len(cookies) == 1 and "max-age=0"
     in cookies[0].lower()`; `locate(page, "login.message.expired").inner_text().strip() == "Your demo session ended, so
     please sign in again."`; `run.db.count("staff_sessions", "session_id = ?", (login_2.session_id,)) == 0`. Print
     statuses, `Location` values and row presence per step (never a cookie value).
4. **`test_j8_header_for_four_roles(browser_journey_factory)`** (AC-19): sign in; for each `role` in `ROLES` step
   f"19 {role}" (`needs=STAFF_NEEDS, operations=("getSession", "switchRole"), selectors=(f"shell.role.{role}",
   "shell.header_name")`): `mark`; if `role != "customer"`: `switch_role(run, bp, role)`; else `page.reload()`; `s =
   bp.net.wait_for(page, "getSession", since=mark)`; `body = json.loads(s.body)`; `body["role"] == role`;
   `body["display_name"] == EXPECTED_DISPLAY[role]`; `locate(page, "shell.header_name").inner_text().strip() ==
   body["display_name"]`; `locate(page, f"shell.role.{role}").is_checked()`. Print header reading beside the
   `getSession` body (role and display name only). If the page sends no `getSession` after a switch, that is the shell
   audit B5 seam: let the `wait_for` fail with its message.
5. **`test_j8_role_change_elsewhere(browser_journey_factory)`** (AC-20): sign in; tab A: switch to representative,
   `page.goto(f"/staff/cases/{SEED_CASE}")`, getCase 200. Step "20a wrong_role in tab A" (`needs=STAFF_NEEDS,
   operations=("switchRole", "getCase"), selectors=("shell.role.customer", "role.panel.wrong_role", "case.root")`):
   `tab_b = second_tab(bp)`; `tab_b.page.goto("/role")`; `switch_role(run, tab_b, "customer")`; `mark`;
   `bp.page.bring_to_front()`; `ex = bp.net.wait_for(bp.page, "getCase", since=mark)`; `ex.status == 403`;
   `json.loads(ex.body)["error"]["details"]["reason"] == "wrong_role"`; `locate(bp.page, "role.panel.wrong_role")`
   visible; `locate(bp.page, "case.root").count() == 0`; screenshot `wrong-role`. Step "20b role_reset in tab A"
   (`needs=(*STAFF_NEEDS, "reset_service"), operations=("switchRole", "resetDemo", "getCase"),
   selectors=("shell.role.representative", "demo.reset", "demo.reset_result", "role.panel.role_reset")`): tab B
   `switch_role(run, tab_b, "representative")`; `tab_b.page.goto("/demo")`; `mark`; click `locate(tab_b.page,
   "demo.reset")`; `bp.net.wait_for(tab_b.page, "resetDemo", since=mark)` status 200; `locate(tab_b.page,
   "demo.reset_result")` visible; `mark2 = bp.net.mark()`; `bp.page.bring_to_front()`; `bp.page.reload()`; `ex =
   bp.net.wait_for(bp.page, "getCase", since=mark2)`; `ex.status in (403, 404)`; when 403: `details.reason ==
   "role_reset"`; `locate(bp.page, "role.panel.role_reset")` visible; screenshot `role-reset`. Print tab A's panel
   reasons and the 403 bodies (code and reason only). Until the UX session's B1/B2 rows for `role.panel.wrong_role` /
   `role.panel.role_reset` exist, these steps report `blocked-on UX session` through the missing selectors (never
   passed).
6. **`identity_and_staff_path(brun) -> PathValues`** (shared by AC-16 and AC-17; module-level in j8; dataclass
   `PathValues(bp, thread_id: str, login: BrowserLogin, verified: Verified, first_page: Response, case_page: Response,
   exchanges: dict[str, ApiExchange], cookie: str = field(repr=False))`): `bp = brun.open(DESKTOP)`; "16a signed-out
   page" (`r = bp.page.goto("/")`; keep `r`); "16b sign in and chat" (`open_chat` without the first `goto`: write the
   sign-in and start wait inline; then `cookie = next(c["value"] for c in bp.context.cookies() if c["name"] ==
   "mhc_session")`); "16c identity" (`billing_through_code(run, bp, tid)` imported from j2; same needs and selectors as
   AC-4); "16d staff" (switch to representative → keep the `switchRole` and `getQueue` exchanges; `case_page =
   bp.page.goto(f"/staff/cases/{SEED_CASE}")` → keep the `getCase` exchange); "16e sign out" (`sign_out_via_shell` →
   keep it as `exchanges["logout"]`).
7. **`test_j_aea62_evidence_clean(browser_journey_factory, capsys, request)`** (AC-16): `browser_run(J8)`; run the
   path; step "16f scans" (no needs): `values = {"code": pv.verified.code, "phone": pv.verified.phone, "phone digits":
   re.sub(r"\D", "", pv.verified.phone), "demo password": run.settings.demo_password.get_secret_value(), "mhc_session
   value": pv.cookie}`; `captured = capsys.readouterr()`; `print(captured.out, end="")`; `record =
   render_record(RecordData("AEA-62", browser_record_values(build_record_data(scope="AEA-62", collector=run.collector,
   root=REPO_ROOT, command="j8"), brun.session, collector=run.collector, root=REPO_ROOT)))` (`REPO_ROOT =
   Path(__file__).resolve().parents[3]`); `places = {"server logs": run.logs.all_text(), "screenshot names":
   "\n".join(p.name for p in brun.shots_dir.glob("*")), "test id": request.node.nodeid, "record": record, "pytest
   output": captured.out + captured.err}`; for each value label: `hits = {w: t.count(val) for w, t in places.items()}`;
   `assert sum(hits.values()) == 0, f"{label}: {hits}"` (**counts only**). Then `bp.net.dev_param_hits() == []`;
   `bp.net.origins() == {run.base_url}`; `run.guard.blocked == []`. Print `secret hits: 0 per value; origins: {…}`.
8. **`test_j_aea62_records_present(browser_journey_factory)`** (AC-17): `browser_run(J8)`; run the path; step "17a
   records" (no extra needs). Collect every workflow's problems in `problems: list[str]` and assert `problems == []`
   **at the end**, so one missing record does not hide the others. Helper `rec(ex) = run.logs.wait_for("request",
   lambda r: r["request_id"] == ex.header(REQUEST_ID_HEADER))`:
   - WF-19: the signed-out `/` hop record (`first_hop(pv.first_page)`'s `REQUEST_ID_HEADER`) has `route ==
     "spa_fallback"`, `status == 303`, `caller_role == "anonymous"`; the `/staff/cases/MHC-C-0006` page load's record
     (`pv.case_page`) has `route == "spa_fallback"`.
   - WF-18: `ok = run.logs.wait_for("auth_event", lambda r: r["request_id"] ==
     pv.login.login.header(REQUEST_ID_HEADER))`; `ok["outcome"] == "ok"`; the logout exchange's `auth_event` has
     `outcome == "logged_out"`; both `session_id == pv.login.session_id`.
   - WF-3: `rec(pv.verified.inbox)` exists with `status == 200`, and `thread_id == pv.thread_id` — else append
     `"WF-3: the listDemoInbox request record has thread_id <value or empty>, not the code request's thread (seam: AEA-43
     route / AEA-23 request record)"` (§8 R-9; the expectation stays).
   - WF-4: `rec(switchRole)["status"] == 200`; `rec(getQueue)["caller_role"] == "representative"`;
     `rec(getCase)["caller_role"] == "representative"`.
   - WF-1: `assert_turn_records(run, pv.thread_id)` (inside `try/except AssertionError as e: problems.append(f"WF-1:
     {e}")`); the opening turn has `spend_ledger` rows (`>= 1`).
   - Print each record's `record`, `route`, `status` / `outcome`, `caller_role` and ids, then `problems`.

### Step 7 — run while iterating

C-1 per file (§7). Expect *blocked* skips with owners where AEA-39/AEA-51 or the UX selector rows are missing;
**no failures**. A failure whose cause is the real system storing or showing something other than the expected value is
a **seam finding on the owning ticket**: report it; never edit the expectation (AEA-57 §2 rule). Known likely finding:
AC-17's WF-3 line (§8 R-9).

### Step 8 — evidence run

C-6 with `--journey-record=AEA-62`. Read `docs/testing/journeys/<date>-AEA-62.md`: nine fields filled; *Blocked by*
names every blocked owner or "none". AEA-58's writer fills *Remaining limitations* with AEA-58's text; replace **only
that field's value** by hand with: "J-4, J-5, J-7, J-9 and J-10 are not in a browser (API level in their tickets and
the per-wave walkthroughs); SSE frames are not body-checked (status and content type only; AEA-41, AEA-59); scripted
model only (live models: AEA-61); redaction is not re-checked here (CAP-1, CAP-4, CAP-10, CAP-11); the card *answered*
state after reload is not asserted until audit A-3 has an owner; held-out data is never read", and say so in the
commit body.

### Step 9 — context rows and commits

1. **Commit 1** (code): `git add tests/journeys/j2/test_aea_62.py tests/journeys/j3/test_aea_62.py
   tests/journeys/j6/test_aea_62.py tests/journeys/j8/test_aea_62.py`; message `test(AEA-62): browser legs of J-2,
   J-3, J-6, J-8 on the production build` + body (levels, blocked owners, any seam findings) + last line
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
2. Context rows (AC-21), with commit 1's short SHA `<sha>`:
   - `.claude/reference/area-map.md` row `3+`, last cell: add before `; the rest planned` (or the cell's closing
     clause as AEA-58 left it): `; browser legs of J-2, J-3, J-6, J-8 `tests/journeys/j{2,3,6,8}/test_aea_62.py`
     actual (AEA-62, `<sha>`)`.
   - `.claude/state/icm-progress.md`: the *Integrated-journey protection* row whose evidence cell names AEA-57 and
     AEA-58 (today line 46; **not** the older row at line 59): append `; browser J-2/J-3/J-6/J-8 (AEA-62, `<sha>`)` after
     the AEA-58 clause and replace its record link with `[`AEA-62`](../../docs/testing/journeys/<date>-AEA-62.md)`; keep
     the row ≤ 400 characters (shorten wording, never drop a SHA); next cell: `Every J-2/3/6/8 browser step integrated
     under --journeys-strict (needs the UX selector contract)`. Do not delete or merge the duplicate row; mention it in
     the commit body.
   - `docs/design/code-design.md` §9: in the `journeys/` lines add `j2/j3/j6/j8 test_aea_62.py = AEA-62's browser legs`;
     in *Built on `main`* add `; `tests/journeys/j{2,3,6,8}/test_aea_62.py` (AEA-62, `<sha>`)`.
3. **Commit 2** (docs): `git add docs/testing/journeys/<date>-AEA-62.md docs/testing/journeys/<date>-AEA-62
   .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`; message `docs(AEA-62):
   journey record and context rows` + the Co-Authored-By line. No push.

### What the implementer must NOT do

- Edit anything under `tests/journeys/support/`, `tests/journeys/browser/`, `tests/integration/`, `tests/graph/`,
  `tests/conftest.py`, `src/meridian/`, `apps/web/`, `docs/ux/`, the OpenAPI, `UI_CONTRACTS.md`, or another ticket's
  `j<N>` file. A missing helper, fixture or selector key is a follow-up on AEA-58 / AEA-57 / AEA-51: stop and report.
- Use `JourneyScript.add` / the plain FIFO queue, or `browser_journey` (every run goes through `browser_run` with
  `StepScript`); reorder `CANCEL_MARKERS`.
- Call `locator(` or `get_by_` (selectors only through `locate`, `locate_in`, `locate_by`); use copy text as a
  selector; read `apps/web/src` to fill a selector gap.
- Use `?signedin`, `?role`, `?scenario`, `?staffing`, `?ex`, `?delay`; pytest-playwright's `page` / `context` /
  `browser` fixtures; `TestClient`, `dependency_overrides`, or a monkeypatch of `meridian`.
- Write a customer name, a phone number, a verification code, the demo password or a cookie value into a test file,
  an assert expression pytest would print, a print, a log line, a screenshot name or the record; take a screenshot while
  SCR-2, a locate card or a code card shows a value (use `card_shot` for cards in identity flows).
- Change an expected value to make a step pass (WF-3 included); add a later turn to make AC-4 pass; turn a blocked step
  into a pass; call `pytest.skip` directly (use `browser_step` or `block_here`).
- Build `apps/web` inside a test; run `playwright install`; add `node_modules` to the worktree; bind 4019 or 5184;
  read `eval/cases/heldout/` or any key directory; call a paid model; run pytest with `-n` above 2; `git add -A`;
  push; force-push.

---

## 6. Data and fixtures

Synthetic or issued only. The demo pair and session secret are random per run (AEA-57 `journey_environ`). The DB is the
issued scheduling DB copied by the app's first boot into a temp folder (never written; hash checked). Customers
MHC-10001 and MHC-10002 and invoice INV-204411 are issued seed rows named by the worked pairs; their names and phones
are read from the working copy at run time. Seed cases MHC-C-0005…0008 come from the app's seed (stage7/cases.md §7).
The retrieval index is AEA-51's `built_index_dir()` over the issued KB (bge-small-en-v1.5 from `var/fastembed`, offline).
The frontend is `apps/web/dist` from the production build (git-ignored). The step tables are this ticket's, written from
the worked pairs and the production output schemas.

---

## 7. Checks

All commands from the worktree root with `export UV_LINK_MODE=hardlink` and
`export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist`. Cap browser runs with
`perl -e 'alarm 300; exec @ARGV'`. No `-n` for browser runs (the Chrome fixture is session-scoped).

| # | When | Command | Passing looks like |
|---|---|---|---|
| C-1 | while iterating | `perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/j2/test_aea_62.py --browser-channel chrome -rs` (then j3, j6, j8) | every test passed or skipped with `blocked-on <owner>`; no failures, no errors (a seam finding is reported, not hidden) |
| C-2 | before the final commit (fast gates, cheapest first) | `uv run ruff format --check tests/journeys && uv run ruff check tests/journeys && uv run mypy` | clean |
| C-3 | before the final commit (affected tests and journeys) | `uv run pytest tests/journeys/support -q`; `uv run pytest tests/journeys/browser -q` (AEA-58's `test_browser_support.py`, incl. `test_no_selector_strings_outside_module`); then `uv run python -m tests.journeys.affected --base main --list-only` and `perl -e 'alarm 300; exec @ARGV' uv run python -m tests.journeys.affected --base main -- --browser-channel chrome -rs` | convention and selector checks pass; the list holds the four files; every selected journey passes or is blocked |
| C-4 | before the final commit | `uv run pytest -m journey --collect-only -q` | lists `tests/journeys/j{2,3,6,8}/test_aea_62.py::…` beside AEA-57's and AEA-58's journeys (AC-1) |
| C-5 | static (AC-1, AC-16) | `git diff --name-only main...HEAD`; `grep -rn heldout tests/journeys/j*/test_aea_62.py`; `grep -rnE "locator\(\|get_by_" tests/journeys/j*/test_aea_62.py`; `wc -l tests/journeys/j*/test_aea_62.py` | only §2 owned files; both greps print nothing; every file ≤ 500 lines |
| C-6 | evidence (AC-18, the reviewer command) | `npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist && perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/j2/test_aea_62.py tests/journeys/j3/test_aea_62.py tests/journeys/j6/test_aea_62.py tests/journeys/j8/test_aea_62.py --browser-channel chrome --journey-record=AEA-62 -rs` | exit 0; AEA-58's summary line `browser API responses validated: … failures: 0`; `journey record: …`; then `git -C /home/linuxuser/workspaces/inno-aea-callcenter status --porcelain apps/web` prints nothing |

**Full suite:** not needed. The change adds four journey files and docs; no shared fixture, setting, dependency or
cross-codebase module changes (`build-loop-test-scope.md`). The wave-4 merge and the pre-deploy gate run these files
with all journeys under `--journeys-strict`.

**Tests the implementer writes:** the 18 test functions of §5 steps 3–6 (the WP-N worked pairs among them: AC-2/3
WP-1, AC-4 WP-2, AC-6…8 WP-3, AC-9…11 WP-7, AC-12 WP-8; the J-BOOK anchor is AC-6). **Existing tests that must stay
green:** `tests/journeys/support/test_support.py` (including `test_journey_file_convention`), every other
`tests/journeys/j*/test_aea_*.py`, and AEA-58's `tests/journeys/browser/test_browser_support.py`.

---

## 8. Risks and requests

- **R-1 (request to the orchestrator; blocks this slice): AEA-58-F1, one follow-up on AEA-58's `browser/` package,
  merged before this slice.** AEA-58 merged at `eb51ba4` without the three additions earlier versions of this plan asked
  for. Open it as one small `lane::build-loop` ticket in AEA-58's area (files `tests/journeys/browser/server.py`,
  `plugin.py`, `selectors.py`, `pages.py`, `test_browser_support.py`, and the README's *Adding a browser journey later*
  paragraph), no `risk::security`, with its own self-checks in `test_browser_support.py`. Its exact content:
  - **A-1 run options.** In `server.py`: `OverridesFor = Callable[[Settings, JourneyScript, Callable[[], datetime] |
    None], tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]]`; `open_browser_journey(*, collector, strict,
    nodeid, build, environ_overrides=None, script: JourneyScript | None = None, with_clock: bool = False,
    overrides_for: OverridesFor | None = None)`: `script = script if script is not None else JourneyScript()`;
    `clock = StepClock() if with_clock else None` (`StepClock` from `tests.journeys.support.server`); `overrides, models
    = (overrides_for or _default_overrides)(settings, script, clock)` with `_default_overrides(s, sc, clk) =
    scripted_overrides(s, sc, wall_clock=clk)`; `JourneyRun(..., script=script, clock=clock, ...)`. Today's callers
    (`browser_journey`, `serve.py`) keep their behaviour. In `plugin.py`: fixture `browser_journey_factory(request,
    journey_chrome, production_build, tmp_path) -> Callable[..., AbstractContextManager[BrowserRun]]` whose callable
    `open_run(*, index_dir: Path | None = None, with_clock: bool = False, script: JourneyScript | None = None,
    overrides_for: OverridesFor | None = None)` composes exactly as `browser_journey` (same collector, strict flag,
    screenshots folder, `BrowserRun` fields, `close()` in `finally`), passing
    `environ_overrides={"MERIDIAN_INDEX_DIR": str(index_dir)}` when `index_dir` is given (`MERIDIAN_INDEX_DIR` is the
    `Settings` env name of `index_dir`, `src/meridian/config.py`). Why: J-2, AC-11 and AC-12 need the built index; AC-15
    needs the run clock; every AEA-62 run needs AEA-51's `StepScript` with `step_overrides` (parallel specialists,
    refresh note 1). AEA-58 stays independent of AEA-51: it accepts a script and a builder and imports nothing from it.
  - **A-2 selectors.** Add every key of §4.3 that is not already in `SELECTOR_KEYS` (state descriptions as in that
    table); allow a contract row whose `value` holds one `{value}` placeholder (parametric rows: `card.slot.window_by_id`,
    `queue.row_by_ref`, `brief.section_by_number`, `case.source_by_id`); add `locate_by(target: Page | Locator, key: str,
    value: str) -> Locator` (the same `css` / `role` / `label` dispatch as `locate`, the placeholder filled with
    `value`). Rows stay empty until `selectors.md` gives them, so those steps report `blocked-on UX session`.
  - **A-3 element screenshot.** `BrowserRun.screenshot_element(bp: BrowserPage, target: Locator, label: str) -> Path`,
    same label rule, path pattern and `session.screenshots` bookkeeping as `screenshot`, using
    `target.screenshot(path=str(path))`. Why: the ticket wants "a screenshot of the account card only" in flows that
    showed identity values.
  This slice must **not** work around a missing addition: no copy of `open_browser_journey` in a test file, no
  `.filter(has_text=…)` standing in for a parametric key, no direct `Locator.screenshot` call.
- **R-2 the UX selector contract does not exist.** `docs/plans/ux-join/selectors.md` is unpublished; until it lands
  and the hooks are in `dist`, every on-screen step reports `blocked-on UX session` (sign-in included, so in practice
  every test). Ask the UX session for the rows of §4.3 (FOR-UX-SESSION §2 says "before AEA-62"). Not a new decision.
- **R-3 model call pattern per turn.** The step tables assume the routing read on `main` (§4.6) and DO-3 §5.4 (free
  text: planner + classifier, then specialists and responder; locate and code turns: no planner; brief only when a case
  opens). `expect_turn` fails loudly on an `exhausted` or invalid call and on a *must* role that never ran; roles that
  are given an entry but not called are harmless. `join_plan` (AEA-37) and the specialist runner (AEA-35) are on `main`;
  the act node (AEA-39) is not; a mismatch at run time is reported as a seam finding on them, never guessed around.
- **R-4 brief quote message ids.** `next_message_id` predicts the customer message id from `sqlite_sequence`; the test
  asserts the prediction after the turn. A wrong prediction is a plan error (stop and report), never a reason to loosen
  the quote check.
- **R-5 the 300 s cap.** About 18 browser tests, each with its own server, plus a one-off index build (AEA-51's
  `built_index_dir`, cached per process). If C-6 exceeds 300 s, report the measured time; the reviewer command's cap is
  the ticket's and is not raised here.
- **R-6 shared context rows.** AEA-61 and AEA-55 also edit area-map row `3+`, the icm-progress journey row and DO-3 §9,
  and AEA-58-F1 may too. Each edit is one clause; the merge agent keeps both sides. AC-21's `browser/README.md` journey
  list is a follow-up on AEA-58 (its README has an *Adding a browser journey later* recipe but no journey list).
  `icm-progress.md` carries two *Integrated-journey protection* rows (lines 46 and 59 today); this slice edits only the
  AEA-57/AEA-58 one (line 46) and reports the duplicate for context upkeep.
- **R-7 test-to-test imports.** j3, j6 and j8 import helpers from `tests.journeys.j2.test_aea_62` (only non-`test_`
  names), as AEA-58 imports from `j1/test_aea_57.py`. The convention check forbids a separate helper module in `j<N>/`,
  and AC-1 limits this ticket to four files. j2 is therefore the tightest file against the 500-line cap (C-5).
- **R-8 expected copy may disagree with the build.** Strings such as "Riley · demo representative", "Tue Oct 20 · 7:00
  pm", "8:00 am → 12:00 pm" come from SCREEN_SPECS via the ticket. If `dist` renders other copy, that is a seam finding
  on the UX session, reported, not edited.
- **R-9 expected seam finding: WF-3 `thread_id`.** DO-6 WF-3 wants the `listDemoInbox` request record to carry the code
  request's `thread_id`, but on `main` the record's `thread_id` comes only from a `{thread_id}` path parameter and
  `GET /api/demo/inbox` has none (the inbox is scoped to the login session). AC-17 will most likely fail on that one
  line. Report it as a seam finding on AEA-43 (route) and AEA-23 (request record); it is not this ticket's to fix and
  the expectation is not edited. The orchestrator may want to open the follow-up early.
- **R-10 AC-4 decided on the code turn.** If the merged graph reads the invoice only on a later text turn, the code
  turn fails with `roles never called: ['specialist']`; that is a seam finding on AEA-37/AEA-39 against
  `route_after_identity`, not a reason to add a turn.
- **R-11 `by_marker` depends on tool descriptions.** `CANCEL_MARKERS` relies on `kb_search`'s description naming
  `read_membership` and no account tool description naming `kb_search` (true on `main`). If a later change puts
  `kb_search` into the account specialist's request text, both specialists get the knowledge table and the step fails
  loudly (`invalid_output`); report it.
- **R-12 source-card DOM id.** The wire `source_id` is already `src-<lookup_log id>` (§4.6), while the ticket and audit
  A2 speak of `#src-<source_id>`. Which DOM id the Sources tab renders is the UX session's `case.source_by_id` row; the
  test passes the wire `source_id` as the row's `{value}` and never builds an id itself. A row that cannot resolve a wire
  id is a seam finding on the UX session.
- **R-13 AC-11 needs the fastembed cache.** Like AC-2, AC-3, AC-5 and AC-12, AC-11 now needs `bge-small-en-v1.5` in
  `var/fastembed`; without it the test blocks with owner "environment (fastembed model cache)". Index build is once per
  process (`built_index_dir` is cached), so the extra cost is one more server start, not a second build.
- **No contract change needed.** WEB-1 option A (D-4) and start-fresh (D-8) are applied as decided.

---

## 9. Readiness and gates

**READY**, **BLOCKED-ON AEA-58-F1** (the AEA-58 follow-up with additions A-1, A-2, A-3 of §8 R-1; AEA-58 itself merged
at `eb51ba4` without them) and **AEA-51** (the imports in §4.4: `tests/integration/customer_support.py` — `StepScript`,
`step_overrides`, `built_index_dir`, `fastembed_offline` — and `tests/graph/worked_pair_scenarios.py`; AEA-51 waits on
AEA-39). Run-time dependencies, reported as *blocked* steps with their owners and never passed: AEA-51's `run_graph` and
`reply_composer` bindings (and through them AEA-39, the act node), and the UX session's `selectors.md` rows plus its
B1/B2, A-5 and B-3 fixes in `dist`. Already merged and no longer blocking: AEA-27 (identity), AEA-28 (booking), AEA-29
(cases and handoff), AEA-30 (demo clock), AEA-31 (reset), AEA-35 (specialist runner), AEA-36 (front nodes), AEA-37
(plan join), AEA-40 (chat routes; AEA-40-1 greeting after reload), AEA-43 (demo inbox), AEA-44 (staff sessions), AEA-45
(`getQueue`, `getCase`), AEA-52 (staff and demo integration), AEA-57 (harness, wall clock), AEA-58 (browser harness). No
`NEEDS-DECISION`.

**Gates:** no human, external, paid or live gate of its own; inherits `gate::ux4` through AEA-58. No model call is paid
(scripted adapter only).
