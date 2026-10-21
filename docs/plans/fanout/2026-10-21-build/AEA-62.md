# Plan — [AEA-62] browser journeys for integrated capabilities (J-2, J-3, J-6, J-8)

**Status:** planned — READY, **blocked-on AEA-58** (its `tests/journeys/browser/` package plus the three additions in
§8 R-1, which the orchestrator should fold into AEA-58's plan before AEA-58 is built, or land as one AEA-58 follow-up
merged first) and **AEA-51** (two test-helper modules this plan imports, §4.4). AEA-52, AEA-40, AEA-29, AEA-45, AEA-43,
AEA-27, AEA-28 and the UX session's `docs/plans/ux-join/selectors.md` are **run-time** dependencies: missing ones show
as *blocked* steps, never imported and never passed. No `NEEDS-DECISION`: Decision 6 (D-8, start fresh) and WEB-1 (D-4,
option A) are applied as decided; no contract change is needed.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/62 (identical to
`docs/plans/tickets/AEA-62.md`) · **Base revision:** `main` `e22aebb` · **Wave:** 4 · **Lane:** build-loop ·
**Risk:** none (no `risk::security`: plan → implement with tests → review; no frozen tests) · **Gate:** inherits
`gate::ux4` through AEA-58 (met).
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet).
**Branch / worktree:** the one the orchestrator creates (suggested `aea-62-browser-journeys` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-62`), cut from `main` **after** AEA-58 and AEA-51 merged.

No earlier version of this plan existed at this path; this is the first write.

---

## 1. Goal and sources

### Goal (issue *What to build*, in short)

> "Nothing yet proves that a reviewer **in Chrome, on the production build, through the real login** can ask a
> membership question and see its source, book a visit and have it remembered after a reload, watch a refund request
> become a case that a representative opens with its brief, and switch roles without losing the chat."

**What it does, concretely (one leg, input → process → output).** The reviewer runs the command in §7 C-6. For
`test_j2_membership_with_source`, AEA-58's fixture starts the real app on a fresh port over a disposable copy of the
issued DB, serving `apps/web/dist`, with a built retrieval index and the scripted model. Chrome opens `/`, is sent to
SCR-12, signs in through the form, and lands on SCR-1. The test queues the scripted planner, classifier, knowledge
specialist (one `kb_search`, then `report_facts` citing a passage the test looked up beforehand) and responder entries
for one turn, types "What does the Comfort Club membership actually include?" and presses Send. Chrome shows the reply
with a "Source" chip naming `membership/comfort_club_overview.md`; the responder's adversarial "$149" sentence is gone.
The test then reads the working copy: the turn's `lookup_log` passage ids hold only current files, a `check_events`
row of kind `fact` with result `trimmed` exists for that turn, and there is no identity action and no case. Every
`/api/*` response Chrome received is checked against the OpenAPI when the test ends.

### Context

AEA-51 and AEA-52 prove J-2, J-3, J-6 and J-8 through the HTTP API; AEA-58 proves J-1 in a browser. This ticket moves
the integrated legs of J-2, J-3, J-6 and J-8 into Chrome (slice plan §0a, Amendment 1), using AEA-58's browser harness
and AEA-57's support package unchanged. On `main` today neither AEA-58's `browser/` package nor AEA-51's helpers exist,
and `docs/plans/ux-join/selectors.md` has not been published, so until those land every on-screen step reports
*blocked* with its owner.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-62.md` AC-1…AC-21, *Agent handoff*, *Blocked by* | Everything below |
| Slice plan | `docs/plans/slice-plan.md` §0a (AEA-62 puts J-2/3/6/8 in a browser), §1 row AEA-62 (blockers 58, 51, 52, 29, 40, 57; wave 4), §3 rows `tests/journeys/` ("one file per ticket per journey; `support/` is 57's alone") and `apps/web/**` | Owned paths; never edit `support/` or `browser/` |
| Rules | `.claude/rules/integrated-journeys.md` §2 (J-BOOK example), §3 rules 1, 2, 3, 5, 6, §4 (levels, nine record fields), §5, §6 (AEA-62 row); `build-loop-test-scope.md` + *AEA addition*; `context-maintenance.md`; workspace `code-structure.md` (tests ≤ 500 lines), `code-design-solid-modularity.md` | Record shape, who runs what, context rows in the same change |
| Requirements | PRD R-10, R-17, R-26, R-28, R-29, R-45, R-46, R-48; US-6…US-14, US-18…US-20, US-28; `docs/data/worked-pairs.md` WP-1, WP-2, WP-3, WP-4 (WP-4F turn-4 shape), WP-7, WP-8; brief audit K-8 | Expected values per leg |
| UX join | `docs/plans/ux-join/FOR-UX-SESSION.md` §3 (selector minimum), `README.md` ("a selector missing … `blocked-on UX selector <state>` for that step only"), `backend-amendments.md` AEA-62-1…3, `audit-customer.md` A-1, A-3, A-5, B-3, G-1, `audit-staff.md` A2, B1, B2, G1 | Selector keys (§4.3), blocked reporting |
| Component contracts (DO-4 + stage7 addenda; addenda win) | DO-4 §7 (`BRIEF_TITLES`, `BriefExtraction`, `Quote`, `Promise`), §5 (`KnowledgeReport`, `AccountReport`, `SchedulingReport`); `stage7/graph-nodes.md` §1 (`CheckEvent`: `completion` and `fact` written every turn the responder ran, result `pass` / `trimmed`), §2 (`check_quotes`: a quote must be an exact substring of its customer message), §3 (brief only on the turn a case opens); `stage7/graph-core.md` §3 (card ids), §6 (`settled_for`); `stage7/graph-tools.md` §1 (`ToolKind`, `report_facts`); `stage7/web.md` §2 (cookie, 43,200 s), §4, §6 (303 with `reason=none|expired`), §10 (`request`, `auth_event`), §13, §14 (`ThreadHistory`), §15 (wall clock); `stage7/staff.md` §1–§3 (one role per login session; `set_role`; logout and expiry delete the row); `stage7/cases.md` §1.1, §3.2, §5, §7 (seeds MHC-C-0005…0008; live cases from MHC-C-0009) | §4 below |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` schemas `TextBlock`, `SourceChip`, `LocatePromptBlock`, `CodePromptBlock`, `SlotCardBlock`, `ConfirmationBlock`, `AccountCardBlock`, `HandoffBlock`, `TurnResponse`, `ChatThread`, `InboxMessage`, `QueueRow`, `CaseDetail`, `Brief`, `BriefHeading`, `BriefItem`, `CaseSource`, `PromiseRecord`, `SessionInfo`; responses `RoleNotAllowed`, `SessionNotFound` | §4.6 |
| Evaluation plan | DO-5 | n/a: no E-n suite, no number (ticket *Evaluation*) |
| Observability contract | DO-6 rows WF-1, WF-3, WF-4, WF-18, WF-19 | AC-17 |
| Key-metrics registry | DO-7 M-7, M-9, M-10, M-18, M-22, M-27 | Source columns asserted present on the rows each journey creates; no value reported |
| Current code read | `tests/journeys/support/{steps,run,client,db,scripted_model,plugin,server,README}.py/md`, `tests/journeys/j1/test_aea_57.py`, `tests/journeys/README.md`; `src/meridian/policy/{handoff,texts,limits}.py`, `domain/{turn,specialists,handoff,common,tools}.py`, `agent/tools/{knowledge,dispatch}.py`, `adapters/retrieval_fastembed.py`, `retrieval/settings.py`, `adapters/sqlite/schema/{00_core,20_spend,40_identity,60_cases,90_staff}.sql`, `web/deps.py`; issued DB (read only, `immutable=1`); `apps/web/src/routes.ts` (paths only); the AEA-58 and AEA-51 plans in this folder | §4 |

---

## 2. Boundary

### File map — owned files (the only files the implementer creates or edits)

| File | Create / modify | Responsibility | Target size |
|---|---|---|---|
| `tests/journeys/j2/test_aea_62.py` | create | **AEA-62's shared browser helpers** (§5 step 2) and J-2: membership, stale twin, billing, warranty (AC-2…AC-5) | ≤ 500 lines |
| `tests/journeys/j3/test_aea_62.py` | create | J-3: booking to confirmation, reload and follow-up memory, old card writes nothing (AC-6…AC-8) | ≤ 350 |
| `tests/journeys/j6/test_aea_62.py` | create | J-6: refund handoff, staff queue, case view, membership-cancel honest limit (AC-9…AC-12) | ≤ 400 |
| `tests/journeys/j8/test_aea_62.py` | create | J-8: role switch and resume, refusal then allowed, signed out and expired, header for four roles, role change elsewhere, evidence clean, records present (AC-13…AC-17, AC-19, AC-20) | ≤ 500 |
| `docs/testing/journeys/<run-date>-AEA-62.md` + folder `docs/testing/journeys/<run-date>-AEA-62/` (PNGs) | create (written by command C-6, then committed) | AC-18 record and screenshots | generated |
| `.claude/reference/area-map.md` | modify **one cell**: row `3+`, last column | AC-21 | — |
| `.claude/state/icm-progress.md` | modify **one row**: *Integrated-journey protection* (evidence and next cells) | AC-21 | ≤ 400 chars |
| `docs/design/code-design.md` | modify §9 only: the `journeys/` lines of the `tests/` tree and the *Built on `main`* sentence | AC-21 | — |

`tests/journeys/browser/README.md` is **not** edited: AEA-58's plan gives its README no journey list for later tickets,
so per AC-21 a list line would be a follow-up on AEA-58 (§8 R-6).

### Shared surfaces read only (never edit)

`tests/journeys/support/**` (AEA-57), `tests/journeys/browser/**` (AEA-58), `tests/conftest.py`,
`tests/journeys/README.md`, `tests/journeys/affected.py`, every `tests/journeys/j*/__init__.py`, every other
`tests/journeys/j*/test_aea_*.py` (import from `j1/test_aea_57.py` only), `tests/integration/**` and `tests/graph/**`
(AEA-51; import only), `tests/api/openapi_check.py`, `tests/fixtures/**`, `tests/fakes/**`, all of `src/meridian/**`,
`apps/web/**` (the build writes only the git-ignored `dist`), `docs/ux/**`, the OpenAPI, `UI_CONTRACTS.md`, the
briefing, issued data, `docs/archive/`, `docs/parked/`, `PROJECT-CHECKLIST.md`, `.claude/state/resume.md`.

### Owned by other slices (do not touch)

`tests/journeys/browser/` and its plugin (AEA-58; a missing fixture, selector key or helper is a follow-up there, §8
R-1), `tests/journeys/support/` (AEA-57), AEA-51's `tests/integration/customer_support.py` and
`tests/graph/worked_pair_scenarios.py`, the API-level `j2`/`j3`/`j6`/`j8` files of AEA-51 and AEA-52,
`docs/plans/ux-join/selectors.md` (UX session).

---

## 3. Requirements table

"Verify" names the exact test. Every journey test is marked `pytest.mark.journey`. Level for every row except the
static ones is **`integrated with a scripted model`**. Step names in quotes are the `journey.step` names the record shows.

| ID | Kind | Requirement (short) | How it is built | Verify | Level |
|---|---|---|---|---|---|
| AC-1 | invariant | Exactly the four `j<N>/test_aea_62.py` files + record; convention check passes; collected beside AEA-57's and AEA-58's journeys; nothing under `support/`, `browser/`, `tests/conftest.py`, `src/meridian/`, `apps/web/` changes | File map above | `uv run pytest tests/journeys/support -q` (`test_journey_file_convention`); `uv run pytest -m journey --collect-only -q`; `git diff --name-only main...HEAD` | static |
| AC-2 | **journey** (WP-1) | Three membership questions in one chat; each reply holds its own current facts; a "Source" chip names `membership/comfort_club_overview.md` and expands to its passage; per turn `lookup_log` ids back each chip; no identity action, no case, outcome not `handed_off` | `membership_leg()` driver (§5 step 3) | `tests/journeys/j2/test_aea_62.py::test_j2_membership_with_source` | integrated |
| AC-3 | negative | Stale twin never shown or cited: six stale strings absent; the "$149" draft trimmed with a `fact`/`trimmed` row; no `archive/` or `faq/faq_old_copy.md` passage id in any J-2 turn (all three legs); no chip names an excluded file | Same driver on its own server; `assert_no_excluded()` also called by AC-4 and AC-5 | `j2/test_aea_62.py::test_j2_stale_values_absent` | integrated |
| AC-4 | **journey** (WP-2) | Locate card filled from the working copy; code card "…ending in 02"; no invoice value before the code; code read from SCR-2 in a second tab; verified line; account card INV-204411 lines $89.00, $245.00, $144.00, total $478.00, due 2026-11-01; no "$149", no verdict; `verified` action then INV-204411 lookup; no case | `billing_through_code()` driver | `j2/test_aea_62.py::test_j2_invoice_after_code_as_billed` | integrated |
| AC-5 | **journey** (K-8) | Warranty answer 1-year with chip `warranty/warranty_policy.md` (2025-06-15); "90-day"/"90 days" absent; lookup ids include the current file, not `archive/warranty_terms_2023.txt`; no identity action | One knowledge turn | `j2/test_aea_62.py::test_j2_warranty_current_policy` | integrated |
| AC-6 | **journey** (WP-3; WF-1) | Code to phone ending 01; Monday windows 56/42/58, no Saturday; pick 8–12 → "You're booked. Here are the details." + confirmation card + "What's settled"; slot 56 not open, one appointment, one `booked` action with CON-2's `turn_id`, window-search lookups, no case, issued SHA unchanged | `book_slot_56()` driver | `tests/journeys/j3/test_aea_62.py::test_j3_book_to_confirmation` | integrated |
| AC-7 | **journey** (R-45, WP-4F turn-4 shape) | Reload: same thread, greeting first, confirmation card, settled visit; `getChatThread`, no second `startChatSession`; "Yes, please." reply kept whole (completion `pass`); settled = actions; counts unchanged | Driver + reload + follow-up turn | `j3/test_aea_62.py::test_j3_reload_and_follow_up_remembers` | integrated |
| AC-8 | failure/refusal | After reload, replaying the booking turn or tapping the old card's 1–5 pm window books nothing; counts and slot statuses equal | Driver + replay + old card | `j3/test_aea_62.py::test_j3_old_card_writes_nothing` | integrated |
| AC-9 | **journey** (WP-7; WF-1) | Handoff card: `MHC-C-NNNN` (≥ 0009), refund promise + "I can't promise an outcome.", due "Tue Oct 20 · 7:00 pm", follow-up legend; settled request; one `refund` P3 case, promise = table text `open`, `case_created` event, turn and conversation `handed_off` | `refund_case()` driver | `tests/journeys/j6/test_aea_62.py::test_j6_refund_handoff_in_chat` | integrated |
| AC-10 | **journey** | One click "Acting as" Representative → `/staff/queue`, "Riley · demo representative"; new row "P3 · Standard", ref, refund reason, "Unowned", due; four seeds; MHC-C-0008 "P0 · Safety" first; role column `representative` same `session_id`; reading writes no `case_events` | Driver + switch | `j6/test_aea_62.py::test_j6_case_in_staff_queue` | integrated |
| AC-11 | **journey** (WF-4; R-28, R-29) | SCR-6 `/staff/cases/<ref>`: "Unassigned, nobody owns it yet"; promise text + Open; eight headings = `BRIEF_TITLES`; section 4 "Customer says · not checked" with both claims; refund guidance sourced (CAS-33); every chip → `#src-<source_id>`; stored brief = shown; no `case_events`, `cases.version` unchanged | Driver + switch + open row | `j6/test_aea_62.py::test_j6_case_view_brief_and_promise` | integrated |
| AC-12 | **journey** (WP-8) | New chat: verify, renewal read; "I can't switch off auto-renewal from this chat."; handoff "…within 1 business day"; "Done, auto-renew is off" absent; SCR-5 lists it "P3 · Standard"; `membership_cancel` P3 case + promise; completion `trimmed` row; customer row unchanged | Own driver | `j6/test_aea_62.py::test_j6_membership_cancel_honest_limit` | integrated |
| AC-13 | **journey** (N-29, N-31, STF-19) | Switch to Representative → SCR-5; back to Customer → SCR-1 same conversation (`getChatThread`, no `startChatSession`); reload SCR-6 keeps the case and role (`getSession`); tab A chat works while tab B is representative; one `staff_sessions` row whose role follows; one conversation; no `case_events` from reads | Two tabs, one context | `tests/journeys/j8/test_aea_62.py::test_j8_role_switch_and_resume` | integrated |
| AC-14 | failure/refusal (rule §3.5) | Customer on `/staff/queue`: SCR-4 line, no staff data, `getQueue` 403 `ROLE_NOT_ALLOWED` `wrong_role`; Representative on that page → 200 | One tab | `j8/test_aea_62.py::test_j8_customer_refused_then_switch_allowed` | integrated |
| AC-15 | failure/refusal | Sign out on SCR-6 → SCR-12, row deleted, reload → 303 `reason=none`, sign in → that case URL; re-enter SCR-1 → one new `startChatSession`, earlier thread 404 `SESSION_NOT_FOUND`; clock past `login_session_lifetime_s` → 303 `reason=expired`, `Max-Age=0`, expired line, row deleted | Seed case MHC-C-0006; run clock | `j8/test_aea_62.py::test_j8_signed_out_and_expired` | integrated |
| AC-16 | negative | Codes, typed phones, demo password, `mhc_session` value absent from record, screenshot names, test ids, server logs, pytest output; no dev params; one origin; no held-out path | `identity_and_staff_path()` + scans | `j8/test_aea_62.py::test_j_aea62_evidence_clean`; `grep -rn heldout tests/journeys/j*/test_aea_62.py` | integrated (scan); static (grep) |
| AC-17 | capture | WF-1 turn records (+ lookups, checks, spend; case and promise for J-6); WF-3 `request` for `listDemoInbox` with the code request's `thread_id`; WF-4 `request` for `switchRole`, `getQueue`, `getCase`; WF-18 `ok` / `logged_out` same `session_id`; WF-19 `spa_fallback` | `identity_and_staff_path()` + log tap; `assert_turn_records()` step in every chat test | `j8/test_aea_62.py::test_j_aea62_records_present` (+ the "records" step of AC-2, 4, 5, 6, 9, 12) | integrated |
| AC-18 | capture | Reviewer command passes; every `/api/*` response validated (counts per op, 0 failures); issued SHA equal; `git status --porcelain apps/web` empty; record with all nine fields | C-6 | the command, then reading the record | integrated |
| AC-19 | invariant (AEA-62-1) | Header name and marked role equal `getSession` for customer, representative, supervisor, owner | Four switches | `j8/test_aea_62.py::test_j8_header_for_four_roles` | integrated |
| AC-20 | failure/refusal (AEA-62-2) | Tab B switches to Customer → tab A (SCR-6) shows `role.panel.wrong_role`; reset from tab B → tab A shows `role.panel.role_reset` on its next staff call; blocked on UX B1/B2 until their rows exist | Two tabs | `j8/test_aea_62.py::test_j8_role_change_elsewhere` | integrated |
| AC-21 | regression/context | area-map row, icm-progress row, DO-3 §9 | §5 step 9 | `git diff --stat main...HEAD` | — |
| PA-1 | invariant (plan-added) | After every scripted turn: `run.script.problems() == ()`, each role listed as *must* was called, leftovers drained (never carried into the next turn) | `expect_turn()` | inside every turn step | integrated |
| PA-2 | invariant (plan-added) | Each knowledge script cites a passage the real index returns for that query, and the facts the responder states are in those passages (so a trimmed sentence means the check fired, not that the script was wrong) | `first_passage()` pre-search | inside AC-2, AC-3, AC-5 | integrated |

**Worked pairs:** WP-1 (AC-2, AC-3), WP-2 (AC-4), WP-3 with WP-4F's turn-4 shape (AC-6…AC-8), WP-7 (AC-9…AC-11),
WP-8 (AC-12); K-8 for AC-5. **`[journey]` criteria:** AC-2, AC-4, AC-5, AC-6, AC-7, AC-9, AC-10, AC-11, AC-12, AC-13,
all at level `integrated with a scripted model`; the anchor (the J-BOOK journey of integrated-journeys §2) is AC-6
`test_j3_book_to_confirmation`.

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| A knowledge report must cite a passage the search returned | graph-tools §2, DO-4 §5 | implicit | added PA-2 (pre-search) | step 3 |
| A brief `Quote` must be an exact substring of a customer message with that `message_id` | graph-nodes §2 | implicit | added: predict the message id, assert it after the turn | step 5 |
| `completion` and `fact` `check_events` are written every turn the responder ran (result `pass` when nothing removed) | graph-nodes §1 | AC-7 says "no completion-check row" | in-ticket, read as: the turn's `completion` row has `result='pass'` and `removed=0`, and no `completion`/`fact` row has `result='trimmed'` | step 4 (AC-7) |
| A fresh login is role `customer`; landing on `/staff/cases/<ref>` after re-sign-in shows the role panel, not the case | staff.md §2 | implicit | AC-15 asserts the URL only | step 6 |
| Opening a new browser tab on `/` starts a second chat (thread id per tab, N-31) | SCREEN_SPECS SCR-1 | implicit | tab B in AC-13 / AC-20 opens `/role` (SCR-4), never `/` | step 6 |
| Element screenshots for cards in flows that showed identity values | ticket ("screenshot of the account card only") | yes | needs AEA-58 addition A-3 | §8 R-1 |
| Redaction of stored text, SSE frame bodies, live models, J-4/5/7/9/10 in a browser | CAP-n, AEA-41/59, AEA-61, slice plan | excluded | other-ticket | — |
| Selector contract for every asserted state | FOR-UX-SESSION §3 | yes | blocked-on UX session (run time, per step) | §4.3 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test code; drives WF-1, WF-3, WF-4, WF-18, WF-19, already registered) | — | — | — |

---

## 4. Shared code to use (copied; do not paraphrase)

### 4.1 AEA-57 harness (`tests/journeys/support/`, on `main`; import only)

```python
from tests.journeys.support.run import JourneyRun            # .settings .app .container .base_url .demo_username
    # .script: JourneyScript  .db: DbReader  .logs: LogTap  .guard  .collector: StepCollector  .strict: bool
    # .nodeid: str  .clock: StepClock | None  .env.issued_sha256_before  .env.db_path  .secret_values()
from tests.journeys.support.scripted_model import JourneyScript, ScriptEntry, RawToolStep, RawToolCall
    # JourneyScript.add(role, *entries); .take(role) -> ScriptEntry | None (pops); .calls -> tuple[ScriptedCall, ...]
    # .remaining(role=None) -> int; .problems() -> calls whose result is "invalid_output" or "exhausted"
    # ScriptedCall(role, method, request, timeout_s, result)
from tests.journeys.support.steps import Missing, StepResult, blocked_message, owners_of, stop_blocked
    # Missing(what: str, owner: str); StepResult(journey, step, nodeid, status, detail, blocked_on, seconds)
    # stop_blocked(missing, *, strict) -> NoReturn  (pytest.skip, or pytest.fail under --journeys-strict)
from tests.journeys.support.db import issued_rows, sha256_file   # issued_rows(table) reads ISSUED_DB immutable
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

### 4.2 AEA-58 browser harness (`tests/journeys/browser/`, from AEA-58's plan; re-check names after it merges)

```python
from tests.journeys.browser.pages import DESKTOP, PHONE, BrowserPage, BrowserRun, Device
    # DESKTOP = Device("chrome-desktop", 1280, 800); PHONE = Device("chrome-phone", 390, 844)
    # BrowserPage(device, context, page, net: NetworkLog)
    # BrowserRun(run: JourneyRun, browser, channel, build, shots_dir, session, test_name, pages)
    #   .open(device) -> BrowserPage (new context: own cookie jar)
    #   .screenshot(bp, label) -> Path   (label must match ^[a-z0-9-]{1,40}$)
    #   .close()  (teardown: validates every /api exchange; raises on any OpenAPI failure)
from tests.journeys.browser.steps import (SIGN_IN_SELECTORS, BrowserLogin, browser_step, first_hop, page_fetch,
                                          sign_in_via_form, sign_out_via_shell)
    # browser_step(run, journey, name, *, needs=(), operations=(), selectors=()) -> context manager
    # BrowserLogin(session_id: str, login: ApiExchange); sign_out_via_shell(run, bp) -> ApiExchange (204)
    # first_hop(response) -> Response (first hop of a redirect chain); page_fetch(bp, path) -> {"status", "text"} (GET)
from tests.journeys.browser.selectors import locate, locate_in, missing_selectors
from tests.journeys.browser.network import ApiExchange
    # ApiExchange(index, method, url, path, operation_id, status, headers, request_body, body, is_sse, failed)
    #   .header(name) -> str | None
    # NetworkLog (bp.net): .mark() -> int; .operations(since=0) -> list[str];
    #   .wait_for(page, operation_id, *, since=0, timeout_ms=15_000, finished=True) -> ApiExchange
    #   .origins() -> set[str]; .dev_param_hits(*, allowed_urls=()) -> list[str]; .exchanges: list[ApiExchange]
```

Fixtures: `browser_journey` (one `BrowserRun` per test). This plan uses **`browser_journey_factory`** (addition A-1,
§8 R-1) because J-2 needs a built index and AC-15 needs the run clock. Each test module declares
`pytest_plugins = ("tests.journeys.browser.plugin",)` (AEA-58's loading rule; never import the plugin module).

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

### 4.4 AEA-51 test helpers (from AEA-51's plan, §5 C1 and D1; import only; re-check names after it merges)

```python
from tests.integration.customer_support import built_index_dir, fastembed_offline
    # built_index_dir() -> Path | None  (None when bge-small-en-v1.5 is not cached in var/fastembed); once per process
    # fastembed_offline() -> context manager setting FASTEMBED_CACHE_PATH and HF_HUB_OFFLINE=1 for the block
from tests.graph.worked_pair_scenarios import NORMAL, TOOLS, brief, planner, report, responder, step, tool
    # planner(**choices) -> str   PlannerChoices JSON; defaults knowledge "no", account "none", scheduling "none",
    #                              handoff "none", topic "other"
    # NORMAL -> str               classifier JSON with the "normal" label
    # responder(text) -> str      ResponderDraft JSON
    # brief(**fields) -> str      BriefExtraction JSON
    # tool(name, args, call_id="call-1") -> RawToolCall;  report(model, **fields) -> RawToolCall named "report_facts"
    # step(*calls, text="") -> RawToolStep
    # TOOLS: Mapping[str, str]    purpose -> ToolDef.name; keys used here: "invoice", "membership", "find_windows", "book"
```

**Tool arguments:** for `TOOLS["invoice"]`, `TOOLS["membership"]`, `TOOLS["find_windows"]` and `TOOLS["book"]`, copy the
argument dict exactly as AEA-51's merged drivers `wp2`, `wp8` and `wp3` pass it. **Which roles get an entry on which
turn:** follow the turn tables in §5; where AEA-51's merged driver for the same worked pair gives a role an entry on a
turn this plan does not (or the reverse), follow AEA-51's driver for the role set, keep this plan's texts, and say so
in the report. If the merged module names differ from these, use the merged names and report it.

### 4.5 Production values used as expected values (import; never retype)

```python
from meridian.agent.tools.knowledge import KB_SEARCH_NAME          # "kb_search"
from meridian.adapters.retrieval_fastembed import FastembedIndex   # FastembedIndex(index_dir).search(q, k=, min_score=)
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K        # 0.60, 3
from meridian.domain.common import Role                            # PLANNER, CLASSIFIER, PLANNER_FALLBACK, RESPONDER, BRIEF, SPECIALIST
from meridian.domain.specialists import AccountReport, KnowledgeReport, ReportedPoint, SchedulingReport
from meridian.domain.handoff import BRIEF_TITLES, HandoffReason, Quote
from meridian.policy.handoff import PROMISE_TABLE, STAFF_GUIDANCE_FOR
from meridian.policy.texts import TextId, render
```

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

### 4.6 Wire and storage shapes (OpenAPI and schema, read only)

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
- Tables (working copy, read with `run.db`): `conversations(thread_id, demo_session, outcome, …)`,
  `messages(id, thread_id, role, text, turn_id, kind, card_id, …)`, `turns(turn_id, thread_id, sequence, status,
  gate_result, outcome, server_ms, trace_export, response, …)`, `actions(thread_id, turn_id, kind, record_id, …)`,
  `lookup_log(id, thread_id, turn_id, message_id, tool, record_ids, passage_ids, result_seen)` (`record_ids`,
  `passage_ids` are JSON arrays), `check_events(thread_id, turn_id, check_kind, result, removed, claim_kinds, codes)`,
  `spend_ledger(thread_id, turn_id, role, …)`, `identity_threads(thread_id, status, customer_id, …)`,
  `cases(case_ref, thread_id, reason, priority, due_at, version, seed, …)`, `case_events(case_ref, kind, …)`,
  `promises(case_ref, policy_row, text, status, due_at, …)`, `case_briefs(case_ref, brief_json, status)`,
  `staff_sessions(session_id, role, …)`; issued `customers`, `appointment_slots(slot_id, slot_date, window, tech_id,
  zone, service_type, status)`, `appointments(appointment_id, slot_id, customer_id, status, …)`.
- Dates: compare stored `due_at` with `datetime.fromisoformat(value) == datetime(2026, 10, 20, 19, 0, tzinfo=CHI)`
  (aware comparison; `CHI = ZoneInfo("America/Chicago")`).

### 4.7 Frontend paths (navigation targets, not selectors; from `apps/web/src/routes.ts`)

SCR-1 `/`, SCR-2 `/demo/inbox`, SCR-3 `/demo`, SCR-4 `/role`, SCR-5 `/staff/queue`, SCR-6 `/staff/cases/<reference>`,
SCR-12 `/login`.

---

## 5. Steps

Dependency direction: the four test files → AEA-58 `browser/` → AEA-57 `support/` → `meridian`; j3, j6 and j8 import
the shared helpers from `tests.journeys.j2.test_aea_62` (named imports only, never a `test_*` name). Nothing imports
the j-files except other j-files of this ticket.

### Step 0 — environment (no code)

1. `export UV_LINK_MODE=hardlink`; `df -h /home` (stop and report under 5 GB free).
2. Confirm AEA-58 and AEA-51 merged: `ls tests/journeys/browser/{plugin,pages,steps,selectors,network}.py
   tests/integration/customer_support.py tests/graph/worked_pair_scenarios.py`. Missing → stop, report
   `BLOCKED-ON AEA-58` / `AEA-51`.
3. Confirm the three AEA-58 additions (§8 R-1): `grep -n "browser_journey_factory\|def locate_by\|def screenshot_element"
   tests/journeys/browser/*.py` finds all three, and `python - <<'EOF'` importing `SELECTOR_KEYS` shows every key of
   §4.3. Missing → stop, report `BLOCKED-ON AEA-58 addition A-<n>`.
4. Build in the primary checkout (backend worktrees have no `node_modules`):
   `npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist`;
   then `git -C /home/linuxuser/workspaces/inno-aea-callcenter status --porcelain apps/web` prints nothing (else stop
   and report; do not revert anything there). `export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist`.
5. Read AEA-51's merged drivers `wp2`, `wp3`, `wp8` (tool args and role sets, §4.4) and note any difference from the
   tables below.

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
EXCLUDED_FILES = frozenset({"faq/faq_old_copy.md"})    # plus every file under "archive/" (R-10, DEC-4)
SEED_REFS = ("MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008")   # stage7/cases.md §7
ROLES = ("customer", "representative", "supervisor", "owner")

@dataclass(frozen=True)
class Turn:
    turn_id: str                     # the turn_id Chrome sent (request body)
    body: dict[str, Any]             # the 200 TurnResponse
    exchange: ApiExchange
    roles_called: frozenset[Role]

@dataclass(frozen=True)
class Verified:                       # values for AC-16 scans; never printed
    customer_id: str
    code_turn: Turn
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
   net=bp.net)`. Same context, so same cookie and same login session; the shared `NetworkLog` sees its requests. Do
   **not** append it to `brun.pages`.
5. `blocks_of(body, kind) -> list[dict]`: `[b for b in body["blocks"] if b["type"] == kind]`.
   `chips_of(body) -> list[dict]`: every `b["sources"]` item of `text` blocks plus every `b["source"]` of `source_chip`
   blocks, in order.
6. `drain(run) -> int`: for each `Role` member, `while run.script.take(role) is not None: n += 1`; return `n`.
7. `expect_turn(run, bp, *, script: Mapping[Role, Sequence[ScriptEntry]], must: Collection[Role], send:
   Callable[[], None]) -> Turn` (PA-1):
   1. `calls_mark = len(run.script.calls)`; `net_mark = bp.net.mark()`.
   2. `for role, entries in script.items(): run.script.add(role, *entries)`.
   3. `send()` (the caller clicks or types).
   4. `ex = bp.net.wait_for(bp.page, "submitTurn", since=net_mark, timeout_ms=70_000)`; `assert ex.status == 200,
      f"submitTurn answered {ex.status}"`.
   5. `turn_id = json.loads(ex.request_body)["turn_id"]`; `body = json.loads(ex.body)`; `assert body["turn_id"] ==
      turn_id`.
   6. `called = frozenset(c.role for c in run.script.calls[calls_mark:])`; `assert run.script.problems() == (),
      f"script problems: {[(c.role.value, c.result) for c in run.script.problems()]}"`; `missing = set(must) - called;
      assert not missing, f"roles never called: {sorted(r.value for r in missing)}"`.
   7. `left = drain(run)`; `print(f"turn {turn_id}: roles {sorted(r.value for r in called)}; unused entries {left}")`.
   *Invariant: a script that disagrees with production fails the step (AEA-57 AC-2), and no entry leaks into the next
   turn.*
8. `say(run, bp, text, *, script, must) -> Turn`: `locate(bp.page, "chat.ready").wait_for()`; then `expect_turn(...,
   send=lambda: (locate(bp.page, "chat.composer").fill(text), locate(bp.page, "chat.send").click()))` (write it as a
   nested `def`, not a tuple lambda).
9. `open_chat(run, bp) -> tuple[BrowserLogin, str]`: `hop = first_hop(bp.page.goto("/"))`; `assert hop.status == 303`;
   `mark = bp.net.mark()`; `login = sign_in_via_form(run, bp)`; `locate(bp.page, "screen.scr1").wait_for(state=
   "visible")`; `start = bp.net.wait_for(bp.page, "startChatSession", since=mark)`; `assert start.status == 201`;
   return `(login, json.loads(start.body)["thread_id"])`. Called inside a step with `needs=CHAT_NEEDS,
   operations=("login", "startChatSession"), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`.
10. `customer_contact(run, customer_id) -> tuple[str, str]`: `row = run.db.one("SELECT name, phone FROM customers WHERE
    customer_id = ?", (customer_id,))`; return `(row["name"], row["phone"])`. Never print either.
11. `submit_locate(run, bp, customer_id, *, script, must) -> Turn`: `card = locate(bp.page,
    "chat.block.locate_prompt").last`; `name, phone = customer_contact(...)`; `send` fills `locate_in(card,
    "card.locate.name")` with `name`, `locate_in(card, "card.locate.phone")` with `phone`, clicks
    `locate_in(card, "card.locate.submit")`; returns `expect_turn(...)`. Before sending, assert the last
    `locate_prompt` block of the previous response offers `["name", "phone"]` in its `field_sets`.
12. `read_code_from_inbox(run, bp, thread_id) -> str`: `tab = second_tab(bp)`; `mark = bp.net.mark()`;
    `tab.page.goto("/demo/inbox")`; `ex = bp.net.wait_for(tab.page, "listDemoInbox", since=mark)`; `assert ex.status ==
    200`; `newest = max((m for m in json.loads(ex.body)["messages"] if m["status"] == "active"), key=lambda m: m["at"])`;
    `shown = locate_in(locate(tab.page, "inbox.message.active").first, "inbox.code").inner_text().strip()`;
    `assert shown == newest["code"], "SCR-2 shows a different code than listDemoInbox returned"` (no value in the
    message); `rec = run.logs.wait_for("request", lambda r: r["request_id"] == ex.header("x-request-id"))`;
    `assert rec["thread_id"] == thread_id` (WF-3); `tab.page.close()`; return `shown`. No screenshot while the tab is
    open.
13. `verify_in_chat(run, bp, customer_id, ending, *, opening, opening_script, code_script, code_must) -> Verified`:
    (a) `t1 = say(run, bp, opening, script=opening_script, must={Role.PLANNER, Role.CLASSIFIER})`; assert
    `blocks_of(t1.body, "locate_prompt")`; (b) `t2 = submit_locate(run, bp, customer_id, script={Role.RESPONDER:
    [responder("Please type the code when it arrives.")]}, must=set())`; `code_block = blocks_of(t2.body,
    "code_prompt")[-1]`; `card = locate(bp.page, "chat.block.code_prompt").last`; `assert f"Code sent to the phone on
    record, ending in {ending}" in card.inner_text()`; (c) `code = read_code_from_inbox(run, bp, thread_id)`;
    (d) `t3 = expect_turn(run, bp, script=code_script, must=code_must, send=<fill locate_in(card, "card.code.input")
    with code; click locate_in(card, "card.code.submit")>)`; assert `render(TextId.VERIFIED)` is in the last assistant
    entry's text; return `Verified(customer_id, t3, phone, code)`. The thread id comes from the caller.
14. `assert_no_excluded(run, thread_id) -> list[str]`: `ids = [pid for r in run.db.rows("SELECT passage_ids FROM
    lookup_log WHERE thread_id = ?", (thread_id,)) for pid in json.loads(r["passage_ids"])]`; `files = [p.split("#",
    1)[0] for p in ids]`; `bad = [f for f in files if f.startswith("archive/") or f in EXCLUDED_FILES]`;
    `assert bad == []`; print `passage ids: …`; return `ids`.
15. `first_passage(index_dir, query, file) -> Passage` (PA-2): `result = FastembedIndex(index_dir).search(query,
    k=SEARCH_K, min_score=MIN_SCORE)` (call inside `fastembed_offline()`, which every J-2 knowledge test wraps around
    its whole body); `hits = [p for p in result.passages if p.file == file]`; `assert not result.below_floor and hits,
    f"{query!r}: the index returned no passage from {file}"`; return `hits[0]`.
    `passages_hold(index_dir, query, needles) -> None`: the union of `p.text` over `result.passages` contains every
    needle; else `AssertionError(f"{query!r}: the passages lack {missing}; change the query wording, never the
    expected facts")`.
16. `knowledge_script(index_dir, query, file, point_text, reply, *, topic) -> dict[Role, list[ScriptEntry]]`:
    `p = first_passage(...)`; return `{Role.PLANNER: [planner(knowledge="yes", topic=topic)], Role.CLASSIFIER:
    [NORMAL], Role.SPECIALIST: [step(tool(KB_SEARCH_NAME, {"query": query}, "call-1")), step(report(KnowledgeReport,
    points=[ReportedPoint(text=point_text, passage_id=p.passage_id)], answered=True))], Role.RESPONDER:
    [responder(reply)]}`. (`report` takes the fields; if AEA-51's `report` expects plain dicts for nested models, pass
    `ReportedPoint(...).model_dump()`.)
17. `assert_turn_records(run, thread_id) -> None` (AC-17, WF-1): for every `turns` row of the thread: `status ==
    "completed"`, `gate_result`, `outcome`, `server_ms` and `trace_export` not null; `run.db.count("check_events",
    "turn_id = ?", (t,)) >= 1` (the gate event); and `run.db.count("spend_ledger", "turn_id = ?", (t,)) >= 1` for every
    turn whose `turns.model_calls > 0`. Print one line per turn: sequence, gate_result, outcome, server_ms,
    trace_export, lookup rows, check rows, spend rows.
18. `next_message_id(run) -> int`: `int(run.db.scalar("SELECT COALESCE((SELECT seq FROM sqlite_sequence WHERE name =
    'messages'), 0) + 1 AS n"))`.
19. `switch_role(run, bp, role) -> ApiExchange`: `mark = bp.net.mark()`; `locate(bp.page, f"shell.role.{role}").click()`;
    `ex = bp.net.wait_for(bp.page, "switchRole", since=mark)`; `assert ex.status == 200`; return `ex`.
20. `card_shot(brun, bp, key, label) -> Path`: `brun.screenshot_element(bp, locate(bp.page, key).last, label)`
    (addition A-3). Used for every card screenshot in a flow that showed a locate or code card.
21. `browser_run(factory, *, index: bool = False, clock: bool = False)`: context manager; if `index`: `index_dir =
    built_index_dir()`; when `None`, it opens a run without index only to record `block_here(run, journey, "0 index",
    "bge-small-en-v1.5 not cached in var/fastembed", "environment (fastembed model cache)")`; else
    `factory(index_dir=index_dir, with_clock=clock)`. Return `(brun, index_dir)`.

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

`membership_leg(brun, index_dir) -> tuple[str, list[Turn]]`: `bp = brun.open(PHONE)`; step "2a sign in and chat"
(`open_chat`); for M1…M3 step f"2b turn {n}" (`needs=TURN_NEEDS, operations=("submitTurn",),
selectors=(*CHAT_SELECTORS, "chat.source")`): `say(..., script=knowledge_script(...), must={PLANNER, CLASSIFIER,
SPECIALIST, RESPONDER})`. Returns the thread id and turns.

1. **`test_j2_membership_with_source(browser_journey_factory)`** (AC-2) — `with fastembed_offline():` around the body;
   `browser_run(index=True)`; run the leg, then per turn n, step f"2c checks {n}" (selectors `chat.entry.assistant`,
   `chat.block.text`, `chat.source`, `chat.source.toggle`, `chat.source.excerpt`):
   - `entry = locate(page, "chat.entry.assistant").last`; every fact of the row is in `entry.inner_text()`.
   - `api_chips = chips_of(turn.body)`; at least one has `file == MEMBERSHIP_FILE` and none names an excluded file.
   - `chip = locate_in(entry, "chat.source").first`; `MEMBERSHIP_FILE in chip.inner_text()`; click
     `locate_in(chip, "chat.source.toggle")`; `locate_in(entry, "chat.source.excerpt").first.inner_text().strip() ==
     api_chips[0]["excerpt"].strip()`.
   - Stored: `ids = {pid for r in rows("SELECT passage_ids FROM lookup_log WHERE turn_id = ?") for pid in
     json.loads(...)}`; `{c["passage_id"] for c in api_chips} <= ids`; print `chip files | lookup ids` side by side.
   - After turn 3: `run.db.count("actions", "thread_id = ? AND kind = 'verified'", (tid,)) == 0`;
     `run.db.count("cases", "thread_id = ?", (tid,)) == 0`; `run.db.scalar("SELECT outcome FROM conversations WHERE
     thread_id = ?", (tid,)) != "handed_off"`; `brun.screenshot(bp, "after-third-reply")`.
   - Step "2d records": `assert_turn_records(run, tid)`.
2. **`test_j2_stale_values_absent(browser_journey_factory)`** (AC-3) — its own run of `membership_leg`; step "3a stale
   strings": after each turn, `hits = {s: page_text(page).lower().count(s.lower()) for s in STALE}`; all zero; print the
   dict. Step "3b fact check removed $149": `rows = run.db.rows("SELECT * FROM check_events WHERE turn_id = ? AND
   check_kind = 'fact' AND result = 'trimmed'", (m1.turn_id,))`; `len(rows) == 1 and rows[0]["removed"] >= 1`;
   `"$149" not in json.dumps(rows[0])`. Step "3c no excluded source": `assert_no_excluded(run, tid)`; no API chip of
   any turn names an excluded file.
3. **`test_j2_invoice_after_code_as_billed(browser_journey_factory)`** (AC-4; WP-2; no index) — `bp =
   brun.open(PHONE)`; step "4a sign in and chat"; step "4b ask, locate, code" (`needs=VERIFY_NEEDS,
   operations=("submitTurn", "listDemoInbox"), selectors=(*CHAT_SELECTORS, "chat.block.locate_prompt",
   "card.locate.name", "card.locate.phone", "card.locate.submit", "chat.block.code_prompt", "card.code.input",
   "card.code.submit", "inbox.message.active", "inbox.code", "chat.block.account_card")`):
   `billing_through_code(run, bp, tid) -> Verified` =
   `verify_in_chat(run, bp, "MHC-10002", "02", opening=BILLING_TEXT, opening_script=BILLING_OPENING,
   code_script=BILLING_CODE, code_must={Role.SPECIALIST, Role.RESPONDER})`, with
   `BILLING_TEXT = "I got an invoice, INV-204411, and I'm not sure what it's for."`,
   `BILLING_OPENING = {PLANNER: [planner(account="invoice", topic="billing")], CLASSIFIER: [NORMAL], RESPONDER:
   [responder("I can explain that invoice once I've confirmed your account.")]}`,
   `BILLING_CODE = {SPECIALIST: [step(tool(TOOLS["invoice"], <wp2 args>)), step(report(AccountReport,
   summary="Invoice INV-204411 lists a diagnostic visit, a contactor replacement and an after-hours dispatch."))],
   RESPONDER: [responder(INVOICE_REPLY)]}`,
   `INVOICE_REPLY = "Invoice INV-204411 has three lines as billed: a diagnostic visit, $89.00; a contactor replacement,
   $245.00; and an after-hours dispatch, $144.00. The total is $478.00, due November 1, 2026."`.
   Before the code turn (after the locate turn): `for v in ("$478.00", "$245.00", "$144.00", "$89.00"): assert v not
   in page_text(page)`. After it:
   - Visible: last assistant entry contains `render(TextId.VERIFIED)`; `card = locate(page,
     "chat.block.account_card").last`; card text contains "INV-204411", "$89.00", "$245.00", "$144.00", "$478.00".
   - API: `acc = blocks_of(code_turn.body, "account_card")[-1]["invoice"]`; `acc["invoice_id"] == "INV-204411"`;
     `[l["amount"]["display"] for l in acc["lines"]] == ["$89.00", "$245.00", "$144.00"]`;
     `acc["total"]["display"] == "$478.00"`; `acc["due_on"] == "2026-11-01"`.
   - Not on the page: "$149"; and none of `VERDICT = ("bill is wrong", "charged incorrectly", "overcharged", "credit is
     owed", "owe you a credit")` (case-insensitive).
   - Stored: `v = run.db.one("SELECT a.turn_id, t.sequence FROM actions a JOIN turns t ON t.turn_id = a.turn_id WHERE
     a.thread_id = ? AND a.kind = 'verified'", (tid,))`; `inv = [r for r in run.db.rows("SELECT l.id, l.record_ids,
     t.sequence FROM lookup_log l JOIN turns t ON t.turn_id = l.turn_id WHERE l.thread_id = ?", (tid,)) if
     "INV-204411" in json.loads(r["record_ids"])]`; `len(inv) >= 1` and every `r["sequence"] >= v["sequence"]`;
     `run.db.count("cases", "thread_id = ?", (tid,)) == 0`; `assert_no_excluded(run, tid)`; print page values and the
     row order (sequence numbers and ids only).
   - **Branch decided now:** if AEA-51's merged `wp2` shows the invoice read happens only on a later text turn (its T4
     "What is it for?"), move `BILLING_CODE`'s specialist entries to a T4 `say(run, bp, "What is it for?",
     script={PLANNER: [planner(account="invoice", topic="billing")], CLASSIFIER: [NORMAL], SPECIALIST: <same>,
     RESPONDER: [responder(INVOICE_REPLY)]}, must=all four)`, keep `code_script={RESPONDER: [responder("Thanks.")]}`,
     and assert the account card after T4. Report which branch ran.
   - `card_shot(brun, bp, "chat.block.account_card", "account-card")`. Step "4c records": `assert_turn_records`.
4. **`test_j2_warranty_current_policy(browser_journey_factory)`** (AC-5) — index; `WARRANTY_FILE =
   "warranty/warranty_policy.md"`, `ARCHIVE_WARRANTY = "archive/warranty_terms_2023.txt"`; text and query "How long is
   the repair warranty?"; point "Repairs carry a 1-year labor warranty on the part repaired."; reply "Repairs come with
   a 1-year labor warranty on the part we repaired."; topic `"warranty"`; `passages_hold` needle `"1"`.
   Checks: entry text contains "1-year"; a chip `file == WARRANTY_FILE` and `"2025-06-15" in (chip["version_date"] or
   "") + chip["version_label"]`; visible chip names the file; `"90-day"` and `"90 days"` absent from `page_text`
   (lower-cased); stored: the turn's lookup ids include one starting `WARRANTY_FILE + "#"` and none starting
   `ARCHIVE_WARRANTY`; `run.db.count("actions", "thread_id = ? AND kind = 'verified'", (tid,)) == 0`;
   `assert_no_excluded`; step "5c records".

### Step 4 — J-3 tests (`tests/journeys/j3/test_aea_62.py`, PHONE; no index)

`book_slot_56(brun, bp) -> Booking` (dataclass: `thread_id, booking: Turn, appointment_id: int, counts: dict[str,
int]`), steps:

- "6a sign in and chat" (`open_chat`).
- "6b ask, locate, code" (`needs=VERIFY_NEEDS, operations=("submitTurn", "listDemoInbox")`, selectors as AC-4 plus
  `chat.block.slot_card`): `verify_in_chat(run, bp, "MHC-10001", "01", opening=BOOK_TEXT, opening_script={PLANNER:
  [planner(scheduling="book_new", topic="booking")], CLASSIFIER: [NORMAL], RESPONDER: [responder("I can look for a time
  once I've confirmed your account.")]}, code_script={SPECIALIST: [step(tool(TOOLS["find_windows"], <wp3 args>)),
  step(report(SchedulingReport, appointment_id=0, wanted_time="Saturday 4 to 7 pm", note="AC not cooling"))],
  RESPONDER: [responder("There's no Saturday evening window, so here are the earliest repair windows.")]},
  code_must={SPECIALIST, RESPONDER})`, `BOOK_TEXT = "I need to schedule a service call. My AC isn't cooling. This
  Saturday if possible, 4 to 7, after work."`. After the opening turn assert no `safety`/`emergency_line` block and no
  case (WP-3: not an emergency).
  Slot card checks: `card = blocks_of(code_turn.body, "slot_card")[-1]`; `mon = {w["slot_id"]: w for d in card["days"]
  if d["date"] == "2026-10-19" for w in d["windows"]}`; `{"56", "42", "58"} <= set(mon)`;
  `mon["56"]["technician"] == "Marta Kowalski"`, `mon["42"]["technician"] == "Ray Mendoza"`,
  `mon["58"]["technician"] == "Marta Kowalski"`; `mon["56"]["window_label"] == "8:00 am – 12:00 pm"`; no `d["date"] ==
  "2026-10-17"`; visible slot card text contains "8:00 am – 12:00 pm", "Marta Kowalski", "Ray Mendoza". Print offered
  windows (slot id, label, technician).
- "6c pick 8–12" (`needs=TURN_NEEDS, operations=("submitTurn",), selectors=("chat.block.slot_card",
  "card.slot.window_by_id", "card.slot.continue", "chat.block.confirmation", "settled.visit")`): `card_el =
  locate(page, "chat.block.slot_card").last`; `expect_turn(run, bp, script={SPECIALIST: [step(tool(TOOLS["book"], <wp3
  args for slot 56>)), step(report(SchedulingReport, appointment_id=0, wanted_time="", note="booked"))], RESPONDER:
  [responder(BOOKED_REPLY)]}, must={Role.RESPONDER}, send=<click locate_by(card_el, "card.slot.window_by_id", "56");
  click locate_in(card_el, "card.slot.continue")>)`, `BOOKED_REPLY = "You're booked for Monday, October 19, 8:00 am to
  12:00 pm with Marta Kowalski."`. (The specialist entries are drained if booking runs in code.)
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
    TOOLS["find_windows"])) >= 1`; `run.db.count("cases", "thread_id = ?", (tid,)) == 0`; `sha256_file(ISSUED_DB) ==
    run.env.issued_sha256_before`. `counts = {"appointments": …customer MHC-10001 rows…, "booked": len(b), "slot56":
    status, "slot58": status}`. Print row ids and both hashes.
  - `card_shot(brun, bp, "chat.block.confirmation", "confirmation-card")`.

1. **`test_j3_book_to_confirmation(browser_journey_factory)`** (AC-6) — the driver, then step "6d records"
   (`assert_turn_records`).
2. **`test_j3_reload_and_follow_up_remembers(browser_journey_factory)`** (AC-7) — driver, then:
   - "7a reload" (`needs=TURN_NEEDS, operations=("getChatThread",), selectors=("chat.entry", "chat.block.text",
     "chat.entry.customer", "chat.block.confirmation", "settled.visit")`): `mark`; `page.reload()`; `read =
     wait_for(page, "getChatThread", since=mark)`; `read.status == 200`; `read.path.endswith("/" + tid)`;
     `"startChatSession" not in bp.net.operations(mark)`; first entry's text block == `render(TextId.GREETING)`;
     `json.loads(read.body)["turns"][0]["turn_id"] == "greeting"`; `locate(page, "chat.entry.customer").count() >= 3`;
     `locate(page, "chat.block.confirmation").count() >= 1`; settled visit text contains "Marta Kowalski" and
     `json.loads(read.body)["settled"]["visit"]["appointment_id"] == appointment_id`.
   - "7b follow-up" (`needs=TURN_NEEDS, operations=("submitTurn",), selectors=CHAT_SELECTORS`): `t = say(run, bp,
     "Yes, please.", script={PLANNER: [planner(topic="booking")], CLASSIFIER: [NORMAL], RESPONDER:
     [responder(FOLLOW_REPLY)]}, must={PLANNER, CLASSIFIER, RESPONDER})`, `FOLLOW_REPLY = "Yes, you're booked: Monday,
     October 19, 8:00 am to 12:00 pm with Marta Kowalski."`; the last assistant entry's text block `.strip() ==
     FOLLOW_REPLY` (kept whole); `c = run.db.one("SELECT * FROM check_events WHERE turn_id = ? AND check_kind =
     'completion'", (t.turn_id,))`; `c["result"] == "pass" and c["removed"] == 0`; `run.db.count("check_events",
     "turn_id = ? AND result = 'trimmed'", (t.turn_id,)) == 0`; `t.body["settled"]["visit"]["appointment_id"] ==
     int(run.db.scalar("SELECT record_id FROM actions WHERE thread_id = ? AND kind = 'booked'", (tid,)))`;
     `t.body["settled"]["identity"]["status"] == "verified"`; counts equal the driver's. Print
     `", ".join(bp.net.operations())`, the reply text, and the counts before and after.
3. **`test_j3_old_card_writes_nothing(browser_journey_factory)`** (AC-8) — driver, reload (as 7a, fewer checks), then:
   - "8a replay booking turn" (`needs=TURN_NEEDS, operations=("submitTurn",)`): `r = page_post(bp,
     f"/api/chat/sessions/{tid}/turns", json.loads(booking.exchange.request_body))`; `r["status"] == 200`;
     `json.loads(r["text"])["turn_id"] == booking.turn_id`; counts equal.
   - "8b old card" (`selectors=("chat.block.slot_card", "card.slot.window_by_id", "card.slot.continue")`): `w =
     locate_by(locate(page, "chat.block.slot_card").first, "card.slot.window_by_id", "58")`; if `not w.is_enabled()` or
     `w.get_attribute("aria-disabled") == "true"`: print "old card disabled after reload" (the visible *answered* state
     is out of scope until audit A-3 has an owner); else `expect_turn(run, bp, script={PLANNER:
     [planner(topic="booking")], CLASSIFIER: [NORMAL], RESPONDER: [responder("Your visit stays on Monday
     morning.")]}, must=set(), send=<click w; click continue>)`. Then counts equal, slot 58 status still `open`, and
     still exactly one `booked` row. Print counts and slot statuses before and after.

### Step 5 — J-6 tests (`tests/journeys/j6/test_aea_62.py`)

`refund_case(brun) -> RefundCase` (dataclass: `bp, thread_id, ref, turn, login`), PHONE:

- "9a sign in and chat".
- "9b refund" (`needs=HANDOFF_NEEDS, operations=("submitTurn",), selectors=(*CHAT_SELECTORS, "chat.block.handoff",
  "settled.request")`): `msg_id = next_message_id(run)`; `t = say(run, bp, REFUND_TEXT, script={PLANNER:
  [planner(handoff="refund", topic="billing")], CLASSIFIER: [NORMAL], RESPONDER: [responder("I'm sorry the repair didn't
  fix the problem.")], BRIEF: [brief(needs=[Quote(message_id=msg_id, text="I want a full refund on the repair.")],
  claims=[Quote(message_id=msg_id, text="It didn't fix anything"), Quote(message_id=msg_id, text="I had to call another
  company")], open_decision="Decide between a refund, a warranty recall, or neither.")]}, must={PLANNER, CLASSIFIER,
  RESPONDER, BRIEF})`, `REFUND_TEXT = "I want a full refund on the repair. It didn't fix anything and I had to call
  another company."`. Then `run.db.scalar("SELECT id FROM messages WHERE turn_id = ? AND role = 'customer'",
  (t.turn_id,)) == msg_id` (else stop: the id prediction is a plan error; report it, do not change the quotes).
  Pass `Quote(...)` objects or their `model_dump()` as AEA-51's `brief()` accepts.
  - API: `h = blocks_of(t.body, "handoff")[-1]`; `m = re.fullmatch(r"MHC-C-(\d{4})", h["reference"])`; `m and
    int(m.group(1)) >= 9`; `h["promise_text"] == PROMISE_TABLE["R26.refund"]`;
    `render(TextId.PROMISE_REFUND_NO_OUTCOME) in h["extra_lines"]`; `t.body["settled"]["request"]["reference"] == ref`.

1. **`test_j6_refund_handoff_in_chat(browser_journey_factory)`** (AC-9) — driver; step "9c card and stored":
   - Visible: `card = locate(page, "chat.block.handoff").last` text contains `ref`, the promise text,
     `render(TextId.PROMISE_REFUND_NO_OUTCOME)`, "Tue Oct 20 · 7:00 pm", `render(TextId.FOLLOWUP_LEGEND)`; and the
     promise text appears before "I can't promise an outcome." in `card.inner_text()`; `locate(page, "settled.request")`
     text contains `ref`.
   - Stored: `c = run.db.one("SELECT * FROM cases WHERE thread_id = ?", (tid,))`; `c["case_ref"] == ref`; `c["reason"]
     == "refund"`; `c["priority"] == "P3"`; `datetime.fromisoformat(c["due_at"]) == datetime(2026, 10, 20, 19, 0,
     tzinfo=CHI)`; `p = run.db.one("SELECT * FROM promises WHERE case_ref = ?", (ref,))`; `p["text"] ==
     PROMISE_TABLE["R26.refund"]` and `p["status"] == "open"`; `run.db.count("case_events", "case_ref = ? AND kind =
     'case_created'", (ref,)) == 1`; `run.db.scalar("SELECT outcome FROM turns WHERE turn_id = ?", (t.turn_id,)) ==
     "handed_off"`; `run.db.scalar("SELECT outcome FROM conversations WHERE thread_id = ?", (tid,)) == "handed_off"`.
     Print the card text and rows. `brun.screenshot(bp, "handoff-card")` (no identity values were shown in this chat).
   - Step "9d records": `assert_turn_records`.
2. **`test_j6_case_in_staff_queue(browser_journey_factory)`** (AC-10) — driver; step "10a switch"
   (`needs=STAFF_NEEDS, operations=("switchRole", "getQueue"), selectors=("shell.role.representative", "screen.scr5",
   "queue.row", "queue.row_by_ref")`): `before_role = run.db.one("SELECT session_id, role FROM staff_sessions")`;
   `events_before = run.db.count("case_events")`; `page.set_viewport_size({"width": DESKTOP.width, "height":
   DESKTOP.height})`; `mark`; `switch_role(run, bp, "representative")`; `q = wait_for(page, "getQueue", since=mark)`;
   `q.status == 200`; `urlsplit(page.url).path == "/staff/queue"`; `locate(page, "screen.scr5").wait_for()`;
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
3. **`test_j6_case_view_brief_and_promise(browser_journey_factory)`** (AC-11) — driver; switch as 10a (fewer
   asserts); step "11a open case" (`needs=STAFF_NEEDS, operations=("getCase",), selectors=("queue.row_by_ref",
   "screen.scr6", "case.root", "case.owner", "case.promise", "case.promise.open", "brief.section_by_number",
   "brief.heading", "brief.item.tag", "case.sources_tab", "case.source_by_id")`): `version_before =
   run.db.scalar("SELECT version FROM cases WHERE case_ref = ?", (ref,))`; `events_before = run.db.count("case_events",
   "case_ref = ?", (ref,))`; `mark`; click `locate_by(page, "queue.row_by_ref", ref)`; `g = wait_for(page, "getCase",
   since=mark)`; `g.status == 200`; `urlsplit(page.url).path == f"/staff/cases/{ref}"`; `d = json.loads(g.body)`.
   - Visible: `locate(page, "case.owner")` text contains "Unassigned, nobody owns it yet"; `locate(page,
     "case.promise.open")` visible and its text contains `PROMISE_TABLE["R26.refund"]` and "Open"; for `n` in 1…8:
     `locate_in(locate_by(page, "brief.section_by_number", str(n)), "brief.heading").inner_text().strip() ==
     BRIEF_TITLES[n - 1]`; section 4: `locate_in(sec4, "brief.item.tag")` text contains "Customer says · not checked",
     and `sec4.inner_text()` contains "It didn't fix anything" and "I had to call another company".
   - API: `[h["title"] for h in d["brief"]["headings"]] == list(BRIEF_TITLES)`; heading 4 items with `kind == "claim"`
     include both quote texts; `guide = [i for h in d["brief"]["headings"] for i in h["items"] if i["text"] ==
     STAFF_GUIDANCE_FOR[HandoffReason.REFUND][0]]`; `guide and all(i["source_ids"] for i in guide)`; `ids = {s for h in
     d["brief"]["headings"] for i in h["items"] for s in i["source_ids"]}`; `ids <= {s["source_id"] for s in
     d["sources"]}`; `d["promise"]["status"] == "open"`.
   - Visible chips: click `locate(page, "case.sources_tab")`; for each `sid` in `sorted(ids)`: `locate_by(page,
     "case.source_by_id", sid)` is visible. Print heading titles, claims, and `sid → title` pairs.
   - Stored: `stored = json.loads(run.db.scalar("SELECT brief_json FROM case_briefs WHERE case_ref = ?", (ref,)))`; its
     heading titles == `BRIEF_TITLES` and per heading the item texts equal `d`'s; `cases.version == version_before`;
     `case_events` count unchanged. `brun.screenshot(bp, "case-brief")`.
4. **`test_j6_membership_cancel_honest_limit(browser_journey_factory)`** (AC-12; WP-8; own run, PHONE) — "12a sign in
   and chat"; "12b ask, locate, code" (`needs=(*VERIFY_NEEDS, "handoff_service", "case_service")`, selectors as AC-4
   plus `chat.block.handoff`): `msg1 = next_message_id(run)` before the opening turn; `verify_in_chat(run, bp,
   "MHC-10001", "01", opening="I want to cancel my Comfort Club membership.", opening_script={PLANNER:
   [planner(account="membership", handoff="membership_cancel", topic="membership")], CLASSIFIER: [NORMAL], RESPONDER:
   [responder("I can help once I've confirmed your account.")]}, code_script={SPECIALIST:
   [step(tool(TOOLS["membership"], <wp8 args>)), step(report(AccountReport, summary="Standard plan, renews
   2026-11-03."))], RESPONDER: [responder("I can't switch off auto-renewal from this chat. Done, auto-renew is off.")],
   BRIEF: [brief(needs=[Quote(message_id=msg1, text="I want to cancel my Comfort Club membership.")], claims=[],
   open_decision="Switch off auto-renewal before the renewal date.")]}, code_must={SPECIALIST, RESPONDER, BRIEF})`;
   check `msg1` after the opening turn as in 9b.
   - Visible: page text contains "I can't switch off auto-renewal from this chat." and not "Done, auto-renew is off";
     handoff card text contains "A representative will get back to you within 1 business day".
   - Stored: `c = run.db.one("SELECT * FROM cases WHERE thread_id = ?", (tid,))`: reason `membership_cancel`, priority
     `P3`; `run.db.count("promises", "case_ref = ?", (c["case_ref"],)) == 1`; `run.db.count("check_events", "turn_id = ?
     AND check_kind = 'completion' AND result = 'trimmed'", (code_turn.turn_id,)) >= 1`; `run.db.count("lookup_log",
     "turn_id = ? AND tool = ?", (code_turn.turn_id, TOOLS["membership"])) >= 1`; the working-copy `customers` row of
     MHC-10001 equals the issued row (`[r for r in issued_rows("customers") if r[0] == "MHC-10001"] == [r for r in
     run.db.table_rows("customers") if r[0] == "MHC-10001"]`; compare, never print).
   - "12c in the queue" (`needs=STAFF_NEEDS, operations=("switchRole", "getQueue"), selectors=("shell.role.representative",
     "queue.row_by_ref")`): desktop viewport; `switch_role`; `locate_by(page, "queue.row_by_ref", c["case_ref"])` text
     contains "P3 · Standard". `card_shot(brun, bp, "chat.block.handoff", "cancel-handoff")` before switching. Step "12d
     records": `assert_turn_records`.

### Step 6 — J-8 tests (`tests/journeys/j8/test_aea_62.py`, DESKTOP)

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
     wait_for(page, "getChatThread", since=mark)`; `read.path.endswith("/" + thread_a)`; `"startChatSession" not in
     operations(mark)`.
   - "13d case reload keeps role" (`operations=("switchRole", "getCase", "getSession"), selectors=("shell.role.representative",
     "screen.scr6")`): switch to representative; `page.goto(f"/staff/cases/{SEED_CASE}")`; getCase 200; `events =
     run.db.count("case_events", "case_ref = ?", (SEED_CASE,))`; `mark`; `page.reload()`; `s = wait_for(page,
     "getSession", since=mark)`; `json.loads(s.body)["role"] == "representative"`; getCase 200 again since mark;
     `case_events` count unchanged.
   - "13e tab A chats while tab B is representative" (`needs=TURN_NEEDS, operations=("switchRole", "submitTurn"),
     selectors=(*CHAT_SELECTORS, "shell.role.customer", "shell.role.representative")`): switch tab A back to customer and
     `page.goto("/")` (resumes `thread_a`, no new start); `tab_b = second_tab(bp)`; `tab_b.page.goto("/role")`;
     `switch_role(run, tab_b, "representative")`; `bp.page.bring_to_front()`; `say(run, bp, CUSTOMER_TEXT,
     script={PLANNER: [PLANNER_RAW], CLASSIFIER: [CLASSIFIER_RAW], RESPONDER: [json.dumps({"text": RESPONDER_TEXT})]},
     must={PLANNER, CLASSIFIER, RESPONDER})`; last assistant text == `RESPONDER_TEXT`.
   - Stored: `run.db.count("staff_sessions") == 1`; its role `representative`, its session id `sid`; `run.db.count(
     "conversations", "demo_session = ?", (sid,)) == 1`. Print the role column after each switch, the operation
     sequence, and the conversation count.
2. **`test_j8_customer_refused_then_switch_allowed(browser_journey_factory)`** (AC-14): sign in (no chat needed: use
   `sign_in_via_form` after the 303); step "14a refused" (`needs=STAFF_NEEDS, operations=("getQueue",),
   selectors=("role.panel", "queue.row")`): `events = run.db.count("case_events")`; `mark`; `r =
   page.goto("/staff/queue")`; `r.status == 200`; `q = wait_for(page, "getQueue", since=mark)`; `q.status == 403`;
   `err = json.loads(q.body)["error"]`; `err["code"] == "ROLE_NOT_ALLOWED"`; `err["details"]["reason"] ==
   "wrong_role"`; `locate(page, "role.panel").inner_text().strip()` contains "You're acting as the customer. Switch to a
   staff role to see this."; `locate(page, "queue.row").count() == 0`; role column `customer`; screenshot
   `refused`. Print code and reason only. Step "14b switch allowed" (`operations=("switchRole", "getQueue"),
   selectors=("shell.role.representative", "queue.row")`): `mark`; `switch_role`; `wait_for(page, "getQueue",
   since=mark)` status 200; `locate(page, "queue.row").count() >= 4`; role column `representative`; `case_events`
   count unchanged; screenshot `allowed`.
3. **`test_j8_signed_out_and_expired(browser_journey_factory)`** (AC-15; `browser_run(clock=True)`):
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
     selectors=("screen.scr1",)`): `mark`; `page.goto("/")`; `start = wait_for(page, "startChatSession", since=mark)`;
     `ops = bp.net.operations(mark)`; if any `getChatThread` exchange since `mark` has a path ending `"/" + thread_1`:
     `block_here(run, J8, "15e SCR-1 starts fresh", "SCR-1 start fresh (the page requested the earlier thread)", "UX
     session")`; `ops.count("startChatSession") == 1`; `json.loads(start.body)["thread_id"] != thread_1`; `f =
     page_fetch(bp, f"/api/chat/sessions/{thread_1}")`; `f["status"] == 404`; `json.loads(f["text"])["error"]["code"]
     == "SESSION_NOT_FOUND"`. Print the operation sequence and the 404 body (it holds only `error` and `request_id`).
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
   wait_for(page, "getSession", since=mark)`; `body = json.loads(s.body)`; `body["role"] == role`;
   `body["display_name"] == EXPECTED_DISPLAY[role]`; `locate(page, "shell.header_name").inner_text().strip() ==
   body["display_name"]`; `locate(page, f"shell.role.{role}").is_checked()`. Print header reading beside the
   `getSession` body (role and display name only). If the page sends no `getSession` after a switch, that is the shell
   audit B5 seam: let the `wait_for` fail with its message.
5. **`test_j8_role_change_elsewhere(browser_journey_factory)`** (AC-20): sign in; tab A: switch to representative,
   `page.goto(f"/staff/cases/{SEED_CASE}")`, getCase 200. Step "20a wrong_role in tab A" (`needs=STAFF_NEEDS,
   operations=("switchRole", "getCase"), selectors=("shell.role.customer", "role.panel.wrong_role")`): `tab_b =
   second_tab(bp)`; `tab_b.page.goto("/role")`; `switch_role(run, tab_b, "customer")`; `mark`;
   `bp.page.bring_to_front()`; `ex` = the first `getCase` or `getQueue` or `getSession` exchange since `mark` with status
   403, waited with `wait_for(bp.page, "getCase", since=mark)`; `json.loads(ex.body)["error"]["details"]["reason"] ==
   "wrong_role"`; `locate(bp.page, "role.panel.wrong_role")` visible; `locate(bp.page, "case.root").count() == 0`;
   screenshot `wrong-role`. Step "20b role_reset in tab A" (`needs=(*STAFF_NEEDS, "reset_service"),
   operations=("switchRole", "resetDemo", "getCase"), selectors=("shell.role.representative", "demo.reset",
   "demo.reset_result", "role.panel.role_reset")`): tab B `switch_role(run, tab_b, "representative")`;
   `tab_b.page.goto("/demo")`; `mark`; click `locate(tab_b.page, "demo.reset")`; `wait_for(tab_b.page, "resetDemo",
   since=mark)` status 200; `locate(tab_b.page, "demo.reset_result")` visible; `mark2`; `bp.page.bring_to_front()`;
   `bp.page.reload()`; `ex = wait_for(bp.page, "getCase", since=mark2)`; `ex.status in (403, 404)`; when 403:
   `details.reason == "role_reset"`; `locate(bp.page, "role.panel.role_reset")` visible; screenshot `role-reset`. Print
   tab A's panel reasons and the 403 bodies (code and reason only). Until the UX session's B1/B2 rows for
   `role.panel.wrong_role` / `role.panel.role_reset` exist, these steps report `blocked-on UX session` through the
   missing selectors (never passed).
6. **`identity_and_staff_path(brun) -> PathValues`** (shared by AC-16 and AC-17; module-level in j8; dataclass
   `PathValues(bp, thread_id, login, verified: Verified, exchanges: dict[str, ApiExchange], first_page: Response)`):
   `bp = brun.open(DESKTOP)`; "16a signed-out page" (`r = page.goto("/")`; keep `first_hop(r)` and `r`); "16b sign in
   and chat"; "16c identity" (`billing_through_code(run, bp, tid)` imported from j2; same needs and selectors as AC-4);
   "16d staff" (switch to representative → keep the `switchRole` and `getQueue` exchanges; `page.goto(f"/staff/cases/
   {SEED_CASE}")` → keep `getCase`); "16e sign out" (`sign_out_via_shell` → keep it).
7. **`test_j_aea62_evidence_clean(browser_journey_factory, capsys, request)`** (AC-16): run the path; step "16f scans"
   (no needs): `cookie = <the mhc_session value captured right after sign-in from bp.context.cookies()>` (capture it in
   "16b"); `values = {"code": v.code, "phone": v.phone, "phone digits": re.sub(r"\D", "", v.phone), "demo password":
   run.settings.demo_password.get_secret_value(), "mhc_session value": cookie}`; `captured = capsys.readouterr()`;
   `print(captured.out, end="")`; `record = render_record(RecordData("AEA-62", browser_record_values(build_record_data(
   scope="AEA-62", collector=run.collector, root=REPO_ROOT, command="j8"), brun.session, collector=run.collector,
   root=REPO_ROOT)))` (AEA-57 `record` and AEA-58 `record` imports, as AEA-58's AC-9 test does); `places = {"server
   logs": run.logs.all_text(), "screenshot names": "\n".join(p.name for p in brun.shots_dir.glob("*")), "test id":
   request.node.nodeid, "record": record, "pytest output": captured.out + captured.err}`; for each value label:
   `hits = {w: t.count(val) for w, t in places.items()}`; `assert sum(hits.values()) == 0, f"{label}: {hits}"`
   (**counts only**). Then `bp.net.dev_param_hits() == []`; `bp.net.origins() == {run.base_url}`;
   `run.guard.blocked == []`. Print `secret hits: 0 per value; origins: {…}`.
8. **`test_j_aea62_records_present(browser_journey_factory)`** (AC-17): run the path; step "17a records" (no extra
   needs): helper `rec(ex) = run.logs.wait_for("request", lambda r: r["request_id"] == ex.header("x-request-id"))`;
   - WF-19: the signed-out `/` hop record (`first_page` hop's `x-request-id`) has `route == "spa_fallback"`, `status ==
     303`, `caller_role == "anonymous"`; the `/staff/cases/MHC-C-0006` page load's record has `route ==
     "spa_fallback"`.
   - WF-18: `ok = run.logs.wait_for("auth_event", lambda r: r["request_id"] == login.login.header("x-request-id"))`;
     `ok["outcome"] == "ok"`; the logout exchange's `auth_event` has `outcome == "logged_out"`; both `session_id ==
     login.session_id`.
   - WF-3: the `listDemoInbox` record (already asserted inside `read_code_from_inbox`) is listed again here by id.
   - WF-4: `rec(switchRole)["status"] == 200`; `rec(getQueue)["caller_role"] == "representative"`;
     `rec(getCase)["caller_role"] == "representative"`.
   - WF-1: `assert_turn_records(run, tid)`; the opening turn has `spend_ledger` rows (`>= 1`).
   - Print each record's `record`, `route`, `status` / `outcome`, `caller_role` and ids.

### Step 7 — run while iterating

C-1 per file (§7). Expect *blocked* skips with owners where AEA-52/40/29/45/43/27/28 or the UX selector rows are
missing; **no failures**. A failure whose cause is the real system storing or showing something other than the
expected value is a **seam finding on the owning ticket**: report it; never edit the expectation (AEA-57 §2 rule).

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
   J-3, J-6, J-8 on the production build` + body (levels, blocked owners, any seam findings, which AC-4 branch ran) +
   last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
2. Context rows (AC-21), with commit 1's short SHA `<sha>`:
   - `.claude/reference/area-map.md` row `3+`, last cell: add before `; the rest planned` (or the cell's closing
     clause as AEA-58 left it): `; browser legs of J-2, J-3, J-6, J-8 `tests/journeys/j{2,3,6,8}/test_aea_62.py`
     actual (AEA-62, `<sha>`)`.
   - `.claude/state/icm-progress.md` row *Integrated-journey protection*: replace the evidence link with the AEA-62
     record (`[…-AEA-62.md](../../docs/testing/journeys/<date>-AEA-62.md)`), keep the row ≤ 400 characters; next
     cell: `Every J-2/3/6/8 browser step integrated under --journeys-strict (needs the UX selector contract)`.
   - `docs/design/code-design.md` §9: in the `journeys/` lines add `j2/j3/j6/j8 test_aea_62.py = AEA-62's browser legs`;
     in *Built on `main`* add `; `tests/journeys/j{2,3,6,8}/test_aea_62.py` (AEA-62, `<sha>`)`.
3. **Commit 2** (docs): `git add docs/testing/journeys/<date>-AEA-62.md docs/testing/journeys/<date>-AEA-62
   .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`; message `docs(AEA-62):
   journey record and context rows` + the Co-Authored-By line. No push.

### What the implementer must NOT do

- Edit anything under `tests/journeys/support/`, `tests/journeys/browser/`, `tests/integration/`, `tests/graph/`,
  `tests/conftest.py`, `src/meridian/`, `apps/web/`, `docs/ux/`, the OpenAPI, `UI_CONTRACTS.md`, or another ticket's
  `j<N>` file. A missing helper, fixture or selector key is a follow-up on AEA-58 / AEA-57 / AEA-51: stop and report.
- Call `locator(` or `get_by_` (selectors only through `locate`, `locate_in`, `locate_by`); use copy text as a
  selector; read `apps/web/src` to fill a selector gap.
- Use `?signedin`, `?role`, `?scenario`, `?staffing`, `?ex`, `?delay`; pytest-playwright's `page` / `context` /
  `browser` fixtures; `TestClient`, `dependency_overrides`, or a monkeypatch of `meridian`.
- Write a customer name, a phone number, a verification code, the demo password or a cookie value into a test file,
  an assert expression pytest would print, a print, a log line, a screenshot name or the record; take a screenshot while
  SCR-2, a locate card or a code card shows a value (use `card_shot` for cards in identity flows).
- Change an expected value to make a step pass; turn a blocked step into a pass; call `pytest.skip` directly (use
  `browser_step` or `block_here`).
- Build `apps/web` inside a test; run `playwright install`; add `node_modules` to the worktree; bind 4019 or 5184;
  read `eval/cases/heldout/` or any key directory; call a paid model; `git add -A`; push; force-push.

---

## 6. Data and fixtures

Synthetic or issued only. The demo pair and session secret are random per run (AEA-57 `journey_environ`). The DB is the
issued scheduling DB copied by the app's first boot into a temp folder (never written; hash checked). Customers
MHC-10001 and MHC-10002 and invoice INV-204411 are issued seed rows named by the worked pairs; their names and phones
are read from the working copy at run time. Seed cases MHC-C-0005…0008 come from the app's seed (stage7/cases.md §7).
The retrieval index is AEA-51's `built_index_dir()` over the issued KB. The frontend is `apps/web/dist` from the
production build (git-ignored). The scripted model entries are this ticket's, written from the worked pairs and the
production output schemas.

---

## 7. Checks

All commands from the worktree root with `export UV_LINK_MODE=hardlink` and
`export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist`. Cap browser runs with
`perl -e 'alarm 300; exec @ARGV'`. pytest `-n 2` at most (not needed here).

| # | When | Command | Passing looks like |
|---|---|---|---|
| C-1 | while iterating | `perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/j2/test_aea_62.py --browser-channel chrome -rs` (then j3, j6, j8) | every test passed or skipped with `blocked-on <owner>`; no failures, no errors |
| C-2 | before the final commit (fast gates, cheapest first) | `uv run ruff format --check tests/journeys && uv run ruff check tests/journeys && uv run mypy` | clean |
| C-3 | before the final commit (affected tests) | `uv run pytest tests/journeys/support -q` then `uv run python -m tests.journeys.affected --base main --list-only` and `perl -e 'alarm 300; exec @ARGV' uv run python -m tests.journeys.affected --base main -- --browser-channel chrome -rs` | convention check passes; the list holds the four files; every selected journey passes or is blocked |
| C-4 | before the final commit | `uv run pytest -m journey --collect-only -q` | lists `tests/journeys/j{2,3,6,8}/test_aea_62.py::…` beside AEA-57's and AEA-58's journeys (AC-1) |
| C-5 | static (AC-1, AC-16) | `git diff --name-only main...HEAD`; `grep -rn heldout tests/journeys/j*/test_aea_62.py`; `grep -rnE "locator\(\|get_by_" tests/journeys/j*/test_aea_62.py` | only §2 owned files; both greps print nothing |
| C-6 | evidence (AC-18, the reviewer command) | `npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist && perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/j2/test_aea_62.py tests/journeys/j3/test_aea_62.py tests/journeys/j6/test_aea_62.py tests/journeys/j8/test_aea_62.py --browser-channel chrome --journey-record=AEA-62 -rs` | exit 0; AEA-58's summary line `browser API responses validated: … failures: 0`; `journey record: …`; then `git -C /home/linuxuser/workspaces/inno-aea-callcenter status --porcelain apps/web` prints nothing |

**Full suite:** not needed. The change adds four journey files and docs; no shared fixture, setting, dependency or
cross-codebase module changes (`build-loop-test-scope.md`). The wave-4 merge and the pre-deploy gate run these files
with all journeys under `--journeys-strict`.

**Tests the implementer writes:** the 18 test functions of §5 steps 3–6. **Existing tests that must stay green:**
`tests/journeys/support/test_support.py` (including `test_journey_file_convention`), every other
`tests/journeys/j*/test_aea_*.py`, and AEA-58's `tests/journeys/browser/test_browser_support.py` (its
`test_no_selector_strings_outside_module` scans these files too).

---

## 8. Risks and requests

- **R-1 (request to the orchestrator; blocks this slice): three additions to AEA-58's `browser/` package.** AEA-58 is
  not built yet, so the cheapest route is to fold these into AEA-58's plan now; otherwise one AEA-58 follow-up merged
  before this slice.
  - **A-1 run options.** `server.browser_environ(root, dist_dir, *, index_dir: Path | None = None)` adds
    `MERIDIAN_INDEX_DIR=str(index_dir)` when given; `server.open_browser_journey(..., index_dir: Path | None = None,
    with_clock: bool = False)` builds `clock = StepClock() if with_clock else None`, passes `wall_clock=clock` to
    `scripted_overrides` and `clock=clock` to `JourneyRun`; plugin fixture `browser_journey_factory(request,
    journey_chrome, production_build, tmp_path) -> Callable[..., AbstractContextManager[BrowserRun]]`, whose callable
    `open_run(*, index_dir: Path | None = None, with_clock: bool = False)` composes exactly as `browser_journey` (same
    screenshots folder, same teardown validation). Why: J-2 needs the built index; AC-15 needs the run clock.
  - **A-2 selectors.** Add every key of §4.3 to `SELECTOR_KEYS` (state descriptions as in that table), allow a
    contract row whose `value` holds one `{value}` placeholder (parametric rows: `card.slot.window_by_id`,
    `queue.row_by_ref`, `brief.section_by_number`, `case.source_by_id`), and add `locate_by(target: Page | Locator, key:
    str, value: str) -> Locator` (same `css` / `role` / `label` dispatch, the placeholder filled with `value`). Rows stay
    empty until `selectors.md` gives them, so those steps report `blocked-on UX session`.
  - **A-3 element screenshot.** `BrowserRun.screenshot_element(bp: BrowserPage, target: Locator, label: str) -> Path`,
    same label rule, path pattern and session bookkeeping as `screenshot`, using `target.screenshot(path=...)`. Why: the
    ticket wants "a screenshot of the account card only" in flows that showed identity values.
- **R-2 the UX selector contract does not exist.** `docs/plans/ux-join/selectors.md` is unpublished; until it lands
  and the hooks are in `dist`, every on-screen step reports `blocked-on UX session` (sign-in included, so in practice
  every test). Ask the UX session for the rows of §4.3 (FOR-UX-SESSION §2 says "before AEA-62"). Not a new decision.
- **R-3 model call pattern per turn.** The scripted queues assume the DO-3 §5.4 skeleton (free text: planner +
  classifier, then specialists and responder; locate and code turns: no planner; brief only when a case opens).
  `expect_turn` fails loudly on a missing entry and drains unused ones, and §4.4 makes AEA-51's merged drivers the
  authority for role sets. A mismatch is reported, not guessed around.
- **R-4 brief quote message ids.** `next_message_id` predicts the customer message id from `sqlite_sequence`; the test
  asserts the prediction after the turn. A wrong prediction is a plan error (stop and report), never a reason to loosen
  the quote check.
- **R-5 the 300 s cap.** About 18 browser tests, each with its own server, plus a one-off index build (AEA-51's
  `built_index_dir`). If C-6 exceeds 300 s, report the measured time; the reviewer command's cap is the ticket's and
  is not raised here.
- **R-6 shared context rows.** AEA-58, AEA-61 and AEA-55 also edit area-map row `3+`, the icm-progress journey row and
  DO-3 §9. Each edit is one clause; the merge agent keeps both sides. AC-21's `browser/README.md` journey list is a
  follow-up on AEA-58 (its README has no such list).
- **R-7 test-to-test imports.** j3, j6 and j8 import helpers from `tests.journeys.j2.test_aea_62` (only non-`test_`
  names), as AEA-58 imports from `j1/test_aea_57.py`. The convention check forbids a separate helper module in `j<N>/`,
  and AC-1 limits this ticket to four files.
- **R-8 expected copy may disagree with the build.** Strings such as "Riley · demo representative", "Tue Oct 20 · 7:00
  pm", "8:00 am → 12:00 pm" come from SCREEN_SPECS via the ticket. If `dist` renders other copy, that is a seam finding
  on the UX session, reported, not edited.
- **No contract change needed.** WEB-1 option A (D-4) and start-fresh (D-8) are applied as decided.

---

## 9. Readiness

**READY**, **BLOCKED-ON AEA-58** (its `browser/` package plus additions A-1, A-2, A-3 of §8 R-1) and **AEA-51** (the
imports in §4.4: `tests/integration/customer_support.py`, `tests/graph/worked_pair_scenarios.py`). Run-time
dependencies, reported as *blocked* steps with their owners and never passed: AEA-52 / AEA-29 / AEA-45 (cases, queue,
case view), AEA-40 (chat routes, AEA-40-1 greeting after reload), AEA-43 (demo inbox), AEA-27 (identity), AEA-28
(booking), AEA-31 (reset, AC-20), and the UX session's `selectors.md` rows plus its B1/B2, A-5 and B-3 fixes in `dist`.
No `NEEDS-DECISION`.
