# Plan — [AEA-27] identity: one-time code, inbox, account reads

**Status:** planned. **READY**: every true import (AEA-02, AEA-04, AEA-10, AEA-13) is merged on `main`; no product
decision is open in this ticket; nothing blocks the start.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/27 (spec copy:
`docs/plans/tickets/AEA-27.md`) · **Base revision:** `e22aebb` (`main`, second refresh; first planned at `c15a6b1`,
refreshed at `16ca639`) · **Planner:** claude-opus-5-5, 2026-10-21 · **Implementer:** `fanout-implementer` on Sonnet ·
**Test-writer:** `test-writer-agent` (this ticket is `risk::security`: the §7.1 files are frozen first).
**Lane:** `lane::build-loop` · **Risk:** `risk::security` (frozen failing tests first; `security-privacy-agent` reads this
diff at the wave-2 merge) · **Wave:** 2.

**Refresh log (2026-10-21, against `main` `e22aebb`).** 143 commits landed since `16ca639`, among them AEA-02
(`f8c6860`), AEA-10 (`dc65bc5`), AEA-13 (`dc1f4da`, fee sentences option A), AEA-22 (`d76092f`), AEA-23 (`1e6889a`),
AEA-33 (`a45e3c2`) and AEA-57 (`bd79a29`, journey harness). The ticket, the slice-plan row and every stage7 addendum this
plan uses are unchanged (`git diff 16ca639..HEAD -- docs/design/contracts/` adds only built-notes to DO-4 §5 and the
gateway/ingest sections). Every name in §4 was checked on `main`; what changed in this plan:
1. **Nothing blocks.** The old "start after AEA-02/10/13 merge" condition is met. `blockedOn` is empty.
2. **Guard tests are on `main`.** `tests/unit/web/test_container.py` line 72 skips any hunk whose docstring lacks
   `No-op until`; `tests/unit/adapters/test_repo_shells.py` line 30 applies the "no public member" check only when the
   class docstring holds `AEA-02 creates the constructor only`. This ticket edits **neither** file; it only drops those
   phrases from its own two docstrings (steps 2.1, 6.1). The two conditional test-file edits are gone from §2.1.
3. **`invoice_owner` dropped.** `tx.core.reads.invoice(invoice_id)` (AEA-10, `repos_core_aux.ReadsRepo`) already returns
   an `InvoiceRow` with `customer_id`; locate-by-invoice uses it. `IdentityRepos` adds only `contact` and `contacts`
   beyond GRT-10 (§8 R-3).
4. **`last_row_id(cur, table)`** exists in `adapters/sqlite/db.py`; inserts use it instead of `cursor.lastrowid`.
5. **HMAC key handling copies `services/staff.py`** (AEA-44, merged): keep the `SecretStr`, derive
   `secret.get_secret_value().encode("utf-8")` per call, `hmac.new(key, msg, hashlib.sha256).hexdigest()`. No bytes copy
   of the secret on the instance.
6. **Account executors' not-verified message** now equals dispatch's `_MESSAGES[NOT_VERIFIED]` text word for word, so
   the model sees one wording whichever layer refuses (§4.3).
7. **Journey (AC-20).** AEA-57's harness is on `main` and records a step whose service or route is missing as
   `blocked-on AEA-NN` (skip). This ticket now writes `tests/journeys/j3/test_aea_27.py`: one step that runs today (the
   real app binds `identity_service`), one step declared with its needs that stays blocked on AEA-40, AEA-43 and AEA-51
   (§5 step 8; §8 R-1). The record stays `mock-tested`.
8. **Plan-added tests move to their own frozen file** `tests/services/test_identity_edges.py`, so
   `tests/services/test_identity.py` keeps every ticket-named test and stays under the 500-line test cap
   (`code-structure.md`).
9. **Context convention on `main`:** each slice adds its **own** ICM row and a `**Built:**` line in DO-3 §3 (siblings
   AEA-26, 32, 44 did); step 9 follows that instead of replacing a shared row.
10. **AEA-43's route** (worktree, not merged) calls `identity.inbox(str(session.session_id), now=now)` through a
    `Protocol` `inbox(self, demo_session: str, now: datetime)`; the parameter names below match it exactly.
11. **Risk IDs R-1…R-12 keep their numbers** (the AEA-36 plan cites R-5, R-6 and R-8). R-2, R-7 and R-11 are closed;
    R-13 and R-14 are new.
12. Issued data re-checked read-only: MHC-10002's phone ends in `02` and it has an email; INV-204411 is MHC-10002's,
    issued 2026-10-02, due 2026-11-01, 47800/47800, lines 8900/24500/14400; MHC-10003 is `plus`, renewal 2027-02-18,
    Lennox, installed 2025-11-30; 154 phones, 154 distinct last-10 digits; every customer has an email; 11 names are
    shared by two customers; no invoice has a negative line; `customers.phone` is `NOT NULL` (so a synthetic
    "no contact" customer uses `''`, not NULL); MHC-99991/99992/99993/99999 and INV-999999 do not exist.

## Goal

Quoted from the issue (`docs/plans/tickets/AEA-27.md`, *What to build*):

> **US-8 · Prove it's my account with a code before private details.** "As a **homeowner** asking about my bill, I need
> to receive a one-time code at the phone or email on my account and type it in the chat, so that nobody else can read
> my account by guessing my name." Acceptance: "I see only a masked hint ('the phone ending in 02'); the code never
> appears in the chat; no match, a wrong code three times or an expired code ends in a person without revealing whether
> an account exists."
>
> **US-9 · Understand my invoice, membership or warranty after the code.** Acceptance: "INV-204411 lines read as billed
> ($89, $245, $144); no verdict on whether the bill is right; a dispute starts a handoff."

In practice (WP-2): Omar Patel (MHC-10002) submits the locate card → `locate` → `Located(masked_hint="the phone ending in
02")`; `send_code` → `CodeSent(expires_at=now + 10 min, sends_left=2)`; the six digits exist only as their HMAC in
`identity_codes` and in this process's memory, and `inbox()` shows them as a `SecretStr`; Omar types them → `verify` →
`Verified(customer_id="MHC-10002")` with the `actions(verified)` row in the same transaction; then `read_invoices` returns
INV-204411 as billed, while the $144-vs-$149 and diagnostic-without-credit facts go to `AccountCapture.staff_notes` only.

## Context

Stage 7 cut 62 tickets; this is A4 (identity), wave 2. The code-design review found the parked `identity.py` hashed codes
with plain SHA-256 (reversible by trying a million values) and compared ISO strings; DO-3 §2.4 replaces that with
HMAC-SHA256 under the session secret, a per-conversation cap and demo-session scoping. graph-tools §5 (GRT-2, GRT-3,
GRT-10) fixed the result types, the tables and where the digits live. Callers (AEA-36 identity node, AEA-43 CON-6 route,
AEA-51 wiring, AEA-24 eval) build against the DO-4 §14 signatures in parallel and test with doubles.

---

## 1. Goal and sources

What the slice delivers: the `IdentityRepos` body (three tables + invoice reads), `IdentityService` (locate, send,
verify, inbox; the in-memory held digits; HMAC), the three account read executors behind `account_tools(uow)` with the
pure `staff_notes_for`, the `register_identity()` container hunk, and the J-3 identity journey file with its record.

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-27.md` AC-1…AC-21 | Everything; criteria quoted by ID in §3 |
| **Final contract (wins over DO-4, DO-4 §16)** | `docs/design/contracts/stage7/graph-tools.md` §1 (factories, no global registry), §3 (views, `StaffNote`, `AccountCapture`), §4 (account executors, `staff_notes_for`, `SCHEDULE_FEES`, `MEMBER_ALLOWANCE_ROWS`), §5 (result types, wire table, where the code lives, DDL, `IdentityRepos`, limits, reset), C-3, C-4, C-9, C-10 | Signatures in §4 below, copied |
| Storage addendum | `stage7/cases.md` §1.0 (`SqliteUnitOfWorkFactory`: `write=True` → `BEGIN IMMEDIATE`; rollback unless `commit()`), §1.1 (`40_identity.sql` = graph-tools §5), §1.2 (`core.reads.customer`, `core.reads.invoice`, `core.reads.identity_state`), §1.3 (reset clears the three tables), §1.5 (`temp_sqlite()`) | Transactions, reads, fixture |
| Web addendum | `stage7/web.md` §4 (`get_identity_service()` bound in AEA-27's hunk; routes pass `str(session.session_id)` as `demo_session`) | §5 step 6 |
| Graph-core | `stage7/graph-core.md` §2 (intake carrier: the identity node reads `ctx.intake.form` / `code_digits`), §12 (`Settings.session_secret`: "HMAC key for login tokens … and code hashing") | HMAC key; caller shape |
| Component contracts | `docs/design/contracts/internal-components.md` (DO-4) §1 (`ActionKey`, `ActionKind.VERIFIED`, `CompletedAction`, `IdentityState`), §5 (`ToolDef`, `ToolCallScope`, `LookupEntry`, `ToolError`, `ToolResult`, lookup-log rule), §13 (`UnitOfWork`, `core.actions.record` idempotent), §14 (`IdentityService` signatures) | Types and signatures |
| Code design | `docs/design/code-design.md` (DO-3) §2.1 (services call `tx.<repo>.<method>`, never SQL; agent → domain/policy/ports only), §2.4 (`identity.py` row: HMAC, injected clock, cap, N-11), §3 rows, §8 A4 | Layering; module homes |
| Decision ledger | `docs/plans/7b-decisions/graph-tools.md` GRT-1, 2, 3, 4, 5, 10; `residuals-graph.md` R-G-3 | Basis |
| Join amendment | `docs/plans/ux-join/backend-amendments.md` AEA-27-1 (= AC-18), §3 pattern A (journey) | AC-18, AC-20 |
| Requirements | PRD R-14, R-15, R-16, R-17 (`docs/prd/inno-aea-callcenter-prd.md`) | Behaviour |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md`: E-1 WP-2 invariant "nothing private before the code turn"; identity edge cases (no match, wrong ×3, expired) as synthetic cases | AC-10's inbox contract lets the harness read codes; no suite added |
| Observability contract (DO-6) | `docs/design/observability-contract.md` WF-1 (code entry inside CON-2), WF-3 (code-sent record: "hash and expiry only"), CAP-1, *Content and redaction* row "Verification codes (R-15): Never raw: hash and expiry only" | AC-16, AC-17 |
| Key-metrics registry (DO-7) | `docs/design/key-metrics-registry.md` M-21 (from `actions(verified)` ordering), M-8, M-11 | AC-6, AC-13, AC-14 |
| Rules | `.claude/rules/agent-tools.md` 1–5 (one job, routing descriptions, generated schemas, structured errors); `safe-validation-errors.md` 1, 5; `build-loop-test-scope.md` (+ AEA addition: affected journeys); `integrated-journeys.md` §3–§5; `context-maintenance.md` 3, 6; workspace `code-structure.md` (service 600, adapter 600, tests 500 lines hard cap) | Descriptions, errors, tests, record, sizes |
| Sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | None touches AEA-27; nothing here answers one differently |
| Code on `main` (read 2026-10-21 at `e22aebb`) | `domain/{identity,tools,specialists,actions,common,records,turn}.py`; `ports/runtime.py`; `adapters/sqlite/{db,repos_core,repos_core_aux,rows,migrate,repos_identity}.py`, `schema/40_identity.sql`; `policy/{booking,limits,texts}.py`; `agent/tools/{dispatch,knowledge}.py`; `services/staff.py` (HMAC pattern); `web/{container,deps}.py`; `tests/fixtures/sqlite.py`; `tests/journeys/support/` | §4 names copied from here |
| Sibling plans | `AEA-36.md` (cites this plan's R-5, R-6, R-8; its identity double writes our tables with raw SQL), `AEA-43.md` (`InboxReader` Protocol; `FakeIdentityService`) | Keep signatures, status values and risk IDs stable |
| Issued data (read, never written) | `docs/data/issued/meridian_dataset/scheduling_db/` (`invoices.line_items` = JSON array of `{"desc", "cents"}`); KB `faq/customer_faq.md` ("Diagnostic fee: $89. Applied as credit toward the repair if you approve the repair during the same visit."), `warranty/warranty_policy.md` | Shapes; staff-note sources |

### Source-contract reconciliation (obligations not already an AC)

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| A locate must never leave a previous customer bound to the thread (otherwise a later `send_code` sends to the old match) | R-16, GRT-3 | no | **added** PA-1: a no-match locate writes status `not_verified` with every customer column NULL | step 3.3 |
| A locked conversation stays locked (a re-locate must not reopen sends or tries) | R-15 (3 tries), GRT-3 | no | **added** PA-2: `locate` on a `locked` thread writes nothing and returns `NotVerified`; `send_code` on `locked` returns `CodeCapReached` | steps 3.3, 3.4 |
| A superseded code never shows `active` and never verifies | GRT-2, AC-18 spirit | no | **added** PA-3: a new send drops the previous code's held digits; `verify` checks only the newest code | steps 3.4, 3.5 |
| Email-only contact gives the email hint form `the email at o···@…` | graph-tools §5 `Located` comment | no | **added** PA-4 | step 3.2 |
| The service refuses limits the domain cannot hold (`tries_left ≤ 3`, `codes_sent ≤ 3`, `CodeSent.sends_left ≤ 2`) | DO-4 §1 `IdentityState`, `40_identity.sql` CHECK, `domain/identity.py` `Field(le=2)` | no | **added** PA-5: constructor `ValueError` | step 3.1 |
| Repository round trips (rows, invoice views from JSON, cross-account `None`) | GRT-10 | partly (AC-12) | **added** PA-6 (implementer tests) | step 2 |
| `register_identity()` builds one service bound to the container | slice plan §3; web.md §4 | AC text only | **added** PA-7 (implementer test) | step 6 |
| Wire-code mapping of results (`NOT_VERIFIED`, `CODE_WRONG`, …) | graph-tools §5 table | — | **other-ticket**: AEA-36 maps, compose renders | — |
| CON-6 route, `body` rendering, body-logging exclusion | graph-tools §5 `InboxMessage`, C-10 | — | **other-ticket**: AEA-43 | — |
| Writing the account reads' `lookup_log` rows (and STORE redaction of `result_seen`) | DO-4 §5 lookup-log rule | AC-17 (shape only) | **other-ticket**: AEA-22 dispatch (`_stamped` re-stamps `tool`, `message_id`, `turn_id`, redacts `result_seen`; merged) | — |
| Reset clearing of the three tables | cases.md §1.3 | — | **other-ticket**: AEA-10 `clear_demo_tables` (merged; `CLEARED_TABLES`) | — |
| Spans for tool calls | graph-tools §2 R-G-17 | — | **other-ticket**: AEA-35 runner | — |
| Handoff on lock / not-verified | R-16 | — | **other-ticket**: AEA-14/39 decide, AEA-29 opens the case | — |
| The `[journey]` step driven through CON-2 + CON-6 with the scripted model | AC-20, pattern A | AC-20 | **in-ticket at the level AC-20 allows today**: file created with a runnable wiring step and the CON-2/CON-6 step declared and blocked on AEA-40, AEA-43, AEA-51; record `mock-tested` | step 8; §8 R-1 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None added. The code turn (inside CON-2) and CON-6 are WF-1 / WF-3, registered in DO-6; their routes are AEA-40/AEA-43 | WF-1, WF-3 | DO-6 *Covered workflows* | CAP-1 (AEA-51) |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer or test-writer may create or edit)

| File | Action | Writer |
|---|---|---|
| `src/meridian/adapters/sqlite/repos_identity.py` | modify (AEA-02 shell → body; keep class name and constructor exactly) | implementer |
| `src/meridian/services/identity.py` | create | implementer |
| `src/meridian/agent/tools/account.py` | create | implementer |
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_identity`** (keep its name, parameters and the token `AEA-27`) | implementer |
| `tests/services/identity_support.py` | create (shared helpers for the three frozen files) | test-writer (frozen) |
| `tests/services/test_identity.py` | create (WP-2 + every ticket-named service test) | test-writer (frozen) |
| `tests/services/test_identity_edges.py` | create (PA-1…PA-5) | test-writer (frozen) |
| `tests/unit/agent/tools/test_account.py` | create (`tests/unit/agent/tools/__init__.py` already exists) | test-writer (frozen) |
| `tests/unit/adapters/sqlite/test_repos_identity.py` | create (`__init__.py` exists) | implementer |
| `tests/unit/web/test_register_identity.py` | create | implementer |
| `tests/journeys/j3/test_aea_27.py` | create (`tests/journeys/j3/__init__.py` exists) | implementer |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-27.md` | create (date = the day it is written, America/Chicago) | implementer |
| `.claude/reference/area-map.md` | modify the **A4 row's Status cell** only | implementer |
| `.claude/state/icm-progress.md` | **add** one *Routes verified against code and tests* row; append to the *Last reconciled* line | implementer |
| `docs/design/code-design.md` | §3: add one `**Built:**` line; append a status suffix to three tree lines | implementer |
| `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<YYYY-MM-DD>-aea-27-identity-claude-01.md` | create (outside this repo; never `git add` it from this repo) | implementer |

### 2.2 Shared surfaces: read, never edit

`src/meridian/domain/*`, `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02); `src/meridian/adapters/sqlite/{db,
migrate,rows,repos_core,repos_core_aux,repos_cases,repos_cases_state}.py`, every `schema/*.sql`, `tests/fixtures/sqlite.py`
(AEA-10); `src/meridian/policy/booking.py` (AEA-13); `src/meridian/policy/{limits,texts}.py` (AEA-01, AEA-03);
`src/meridian/privacy/redact.py` (AEA-04); `src/meridian/agent/tools/{dispatch,knowledge}.py` (AEA-22, AEA-33);
`src/meridian/web/deps.py` (AEA-23); every other `register_*()` hunk in `web/container.py` and its module-level imports;
`pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/unit/test_import_direction.py`, `tests/unit/web/test_container.py`,
`tests/unit/adapters/test_repo_shells.py`, `tests/unit/adapters/sqlite/helpers.py`, `tests/journeys/support/**`,
`tests/journeys/affected.py` (AEA-01, AEA-02, AEA-10, AEA-57); `tests/fakes/` (AEA-11).

### 2.3 Must not

- Edit any file outside §2.1: another ticket's `register_*()` hunk, `schema/*.sql`, `repos_core*.py`, `db.py`, `rows.py`,
  `domain/*`, `policy/*`, `gates/*`, other executors (`agent/tools/{dispatch,knowledge,scheduling}.py`), the two guard
  tests, the journey harness.
- Edit the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
  `docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, any `docs/design/contracts/**`.
  A needed contract change stops the work and goes back to the orchestrator (`NEEDS-DECISION`).
- Write a code, a full phone number, an email, a card-like number or a secret into code, a log, a test file, a fixture
  literal, a test name, the journey file or the journey record. Tests read Omar's phone from the temp working copy and
  take codes from `inbox()` at run time; the secret comes from `secrets.token_urlsafe(32)` at run time.
- Log, print or trace anything from `services/identity.py` or `agent/tools/account.py` (no `logging` import, no `print`,
  no `TraceSink`). Exception messages carry no value.
- Store the digits anywhere but `_held`; store only `HMAC-SHA256(session_secret, digits)` (lowercase hex) in
  `identity_codes`. Keep no `bytes` copy of the secret on the instance.
- Put a TTL, try or send literal (`600`, `3`) in `services/identity.py`; they come from `IdentityLimits`.
- Register tools in `register_identity` or at import time (GRT-1: AEA-51 builds the `ToolRegistry`).
- Map results to wire codes, render inbox bodies, open cases, or send real SMS/email.
- Write the CON-2/CON-6 body of the J-3 step or any scripted model output for it (that would guess AEA-51's graph; §8 R-1).
- Call a paid model; bind ports 4019 or 5184; start a server by hand (the journey harness starts its own on an
  OS-assigned port); `git add -A`; push; force-push; copy a venv; create `node_modules`; run pytest with more than `-n 2`.
  Never read `.env`.

---

## 3. Requirements table

AC text is the issue's (quoted by ID; the issue governs). "Frozen" = written by the test-writer before implementation.
All service tests use `temp_sqlite()` (a disposable copy of the issued DB) and an `IdentityService` built per test.

| ID | Requirement (short) | How it is implemented | Verified by (frozen unless noted) |
|---|---|---|---|
| AC-1 [invariant] | `locate` by name+phone, customer ID, invoice number for MHC-10002 → `Located` with only `masked_hint == "the phone ending in 02"`; `identity_threads` status `located` + customer id | step 3.3 | `tests/services/test_identity.py::test_locate_each_locator_returns_masked_hint_only` (parametrised over the three locator kinds) |
| AC-2 [failure/refusal] | No match, ambiguous match, no usable contact → `NotVerified` equal and byte-identical (`{"kind":"not_verified"}`); no code or inbox row | step 3.3 (one refusal path) | `::test_not_verified_identical_for_every_cause` |
| AC-3 [invariant] | Phone: digits only, last 10 equal (spaces, dashes, brackets, leading country code); name: case and extra spaces ignored; a one-letter near-miss → same `NotVerified` | step 3.3 (`_digits`, `_norm_name`) | `::test_locate_match_rules` |
| AC-4 [invariant] | `send_code` stores only HMAC, `held_by = boot_id`, `sent_at`, `expires_at = now + code_ttl_s`, `tries_left` 3; one inbox row with `to_masked` "···02"; `CodeSent(sends_left=2)`; TTL from `IdentityLimits` (60 s case) | step 3.4 | `::test_send_code_stores_hmac_and_expiry_only` |
| AC-5 [failure/refusal] | 4th send → `CodeCapReached`, state `locked`, no new rows; send with no located customer → `NotVerified`, writes nothing | step 3.4 | `::test_fourth_code_refused_and_unlocated_send` |
| AC-6 [invariant] | Correct code in TTL → `Verified("MHC-10002")` + `actions(verified)` + status `verified` in one tx; a fault after the action insert leaves neither; same `ActionKey` again writes no second row | step 3.5 | `::test_verify_writes_verified_action_same_transaction` |
| AC-7 [failure/refusal] | Wrong ×2 → `CodeWrong(2)`, `CodeWrong(1)`; 3rd → `CodeLocked`; correct after lock → `CodeLocked`; never `NotVerified` | step 3.5 | `::test_three_wrong_tries_lock` |
| AC-8 [failure/refusal] | At exactly `expires_at` → `CodeExpired(resend_offered=True, …)` under the cap; 1 s before → accepted; at the cap `resend_offered=False` | step 3.5 (`now >= expires_at` is expired) | `::test_expired_code_and_resend_under_cap` |
| AC-9 [failure/refusal] | After a restart (new instance, same DB) the old code → `CodeExpired` (resend offered); `inbox` shows `code=None` | `boot_id` per instance; `held_by` check | `::test_restart_expires_unheld_code` |
| AC-10 [invariant] | `inbox(demo_session)` only that session's messages, newest first; `active` / `used` / `expired`; `code` only while held; second session sees none | step 3.6 | `::test_inbox_scoped_to_login_session` |
| AC-11 [invariant] | `Verified` in thread A leaves thread B (same customer) `not_checked` via `core.reads.identity_state` | per-thread rows only | `::test_verification_is_per_conversation` |
| AC-12 [failure/refusal] | Every account `ToolDef`: `kind` `account_read`, `effect` `"read"`, `requires_verified=True`, no customer field in args schema; another account's invoice number → `ok=True`, empty list, byte-identical to a missing number | step 4 | `tests/unit/agent/tools/test_account.py::test_account_tool_defs_and_cross_account_invoice` |
| AC-13 [invariant] | INV-204411 as billed (8900, 24500, 14400; total 47800; due 2026-11-01; `paid` false) in `for_model`; no "149", no judging word, no staff-note text in `for_model` or `result_seen` | step 4 | `test_account.py::test_invoice_read_as_billed_staff_note_apart` |
| AC-14 [invariant] | `staff_notes_for(INV-204411, "none")` → exactly two notes (texts in §4.4), `record_id` INV-204411; a Plus invoice with the diagnostic at $0 → none | step 4.2 | `test_account.py::test_staff_notes_rules` |
| AC-15 [invariant] | `read_membership` tier + renewal; `read_warranty` for MHC-10003 → 2025-11-30, Lennox, `WARRANTY_TERM_SENTENCE` word for word; both through `core.reads.customer` | step 4 | `test_account.py::test_membership_and_warranty_reads` |
| AC-16 [negative] | After locate, send, wrong, correct, invoice read: digits, full phone, secret absent from every non-issued table, logs, trace (no emitter), `for_model`, `result_seen`, every result serialisation, exception messages; digits only in `inbox()`'s `SecretStr` | §2.3 "must not"; steps 3–4 | `test_identity.py::test_code_phone_secret_absent_everywhere` |
| AC-17 [capture] | Code-sent record (HMAC, `sent_at`, `expires_at`, no digits), `actions(verified)` with `records.customer`, account read's `ToolResult.lookup` (`tool`, `record_ids` INV-204411, `message_id`, `turn_id` from scope) | steps 3.4, 3.5, 4 | `test_identity.py::test_records_for_cap1_and_wf3` |
| AC-18 [invariant] | Inbox message not held → never `active`: other `held_by` or past expiry → `expired`, `code=None`; `active` with code only while held | step 3.6 | `test_identity.py::test_inbox_not_held_is_expired` |
| AC-19 [invariant] | `MEMBER_ALLOWANCE_ROWS`: member "Seasonal tune-up" at $129.00 → no note; non-member tune-up ≠ $129.00 → one note naming both amounts | step 4.2 | `test_account.py::test_tune_up_member_no_note` |
| AC-20 [journey] | J-3 identity step | journey file (wiring step runs; CON-2/CON-6 step blocked on AEA-40, AEA-43, AEA-51) + record at level **`mock-tested`**, *Blocked by* AEA-40, AEA-43, AEA-51 | `uv run pytest -m journey tests/journeys/j3/test_aea_27.py -q -rs` (1 passed, 1 skipped `blocked-on …`) + the record (implementer) |
| AC-21 [regression/context] | Area map A4 row, ICM row, DO-3 §3 rows updated; no `schema/*.sql`, no `policy/booking.py` in the diff | step 9 | `git diff --name-only main...HEAD` |
| **WP-2** (worked pair) | Omar: form → locate → send → inbox → verify → `read_invoices` → INV-204411 as billed, two staff notes in capture only | steps 3–4 | `test_identity.py::test_wp2_omar_locate_code_verify_invoice` |
| PA-1 (plan-added) | No-match locate after a match unbinds the customer: status `not_verified`, `customer_id` NULL; a following `send_code` → `NotVerified`, no row | step 3.3 | `tests/services/test_identity_edges.py::test_relocate_no_match_unbinds_customer` |
| PA-2 (plan-added) | `locked` thread: `locate` → `NotVerified`, no write; `send_code` → `CodeCapReached`, no row | steps 3.3, 3.4 | `test_identity_edges.py::test_locked_thread_stays_locked` |
| PA-3 (plan-added) | A resend drops the previous code: old message `expired` with `code=None`; old digits → `CodeWrong` (only the newest code counts) | steps 3.4, 3.5 | `test_identity_edges.py::test_resend_supersedes_previous_code` |
| PA-4 (plan-added) | Email-only contact → `Located(masked_hint="the email at s···@…")`, `to_masked` `s···@…` | step 3.2 | `test_identity_edges.py::test_email_only_contact_hint` |
| PA-5 (plan-added) | Constructor rejects `tries` or `max_sends` outside 1…3, `code_ttl_s` ≤ 0, an empty secret, with a value-free `ValueError` | step 3.1 | `test_identity_edges.py::test_constructor_rejects_out_of_domain_limits` |
| PA-6 (plan-added) | `IdentityRepos` round trips; `invoice()` cross-account → `None`; malformed `line_items` → `StorageError` without the value | step 2 | `tests/unit/adapters/sqlite/test_repos_identity.py` (implementer; §7.2) |
| PA-7 (plan-added) | `register_identity()` provides one `IdentityService` under `Key("identity_service")` built from `uow_factory`, `settings.session_secret`, `limits.identity` | step 6 | `tests/unit/web/test_register_identity.py::test_register_identity_builds_one_service` (implementer) |

---

## 4. Shared code to use

Every name below was found on `main` at `e22aebb`. Import each from the module listed; never define a second copy.

### 4.1 Imports

| Name | Module | Used in |
|---|---|---|
| `MeridianModel`, `LLMFacing`, `CustomerId`, `InvoiceId`, `ThreadId`, `ToolErrorCode` | `meridian.domain.common` | repo rows, args models, errors |
| `ActionKind`, `ActionKey`, `CompletedAction` | `meridian.domain.actions` | verify |
| `Locator`, `Located`, `NotVerified`, `CodeSent`, `CodeCapReached`, `Verified`, `CodeWrong`, `CodeExpired`, `CodeLocked`, `InboxMessage`, `FormValues` (tests), `IdentityState` (tests) | `meridian.domain.identity` | service |
| `TurnIds` | `meridian.domain.turn` | verify |
| `ToolDef`, `ToolCallScope`, `ToolResult`, `ToolError`, `LookupEntry`, `ToolKind` | `meridian.domain.tools` | executors |
| `InvoiceLineView`, `InvoiceView`, `MembershipView`, `WarrantyView`, `StaffNote`, `AccountCapture` | `meridian.domain.specialists` | repo + executors |
| `MembershipTier` (= `Literal["none", "standard", "plus"]`) | `meridian.domain.records` | `staff_notes_for` |
| `UnitOfWorkFactory`, `UnitOfWork` | `meridian.ports.runtime` | service, executors |
| `IdentityLimits` (frozen dataclass: `code_ttl_s=600`, `tries=3`, `max_sends=3`); `Limits.identity` | `meridian.policy.limits` | service, hunk |
| `SCHEDULE_FEES` (`Mapping[str, Mapping[Literal["none","standard","plus"], int]]`: Diagnostic visit 8900/0/0, After-hours dispatch 14900/0/0, Seasonal tune-up 12900/0/0), `MEMBER_ALLOWANCE_ROWS` (`frozenset({"Seasonal tune-up"})`) | `meridian.policy.booking` | `staff_notes_for` |
| `format_usd` (`"$89"`, `"$12.50"`, `"$1,250"`; raises on negative) | `meridian.policy.texts` | rule-2 note text |
| `format_wall`, `parse_wall`, `integrity_errors`, `last_row_id`, `StorageError` | `meridian.adapters.sqlite.db` | repository only |
| `Container`, `Key` | `meridian.web.container` | hunk, its test, journey |
| `SecretStr`, `Field`, `TypeAdapter` | `pydantic` | `TypeAdapter` builds pattern IDs from text |
| `temp_sqlite`, `TempStore` (`data_dir`, `db_path`, `issued_path`, `uow: SqliteUnitOfWorkFactory`) | `tests.fixtures.sqlite` | tests |
| `ISSUED_TABLES` (`("customers", "technicians", "appointment_slots", "appointments", "invoices")`) | `meridian.adapters.sqlite.migrate` | AC-16 table scan |
| `ReadsRepo` | `meridian.adapters.sqlite.repos_core_aux` | AC-15 spy (tests only) |
| `new_thread`, `new_turn`, `customer_id`, `invoice_id`; `DEMO_START` | `tests.unit.adapters.sqlite.helpers`; `meridian.adapters.sqlite.repos_cases` | test support may reuse (read only) |
| `JourneyRun` | `tests.journeys.support.run` | journey file |

Facts about these shapes that the code depends on:
- `ReadsRepo.customer(customer_id) -> CustomerRow | None` (`rows.CustomerRow`: `phone: str` (plain), `email: str | None`,
  `membership_tier`, `membership_renewal_date: date | None`, `system_brand: str | None`, `system_install_date: date | None`).
- `ReadsRepo.invoice(invoice_id) -> InvoiceRow | None` (`rows.InvoiceRow.customer_id: CustomerId`; raises
  `StorageError("invoices", "line_items not JSON")` on bad JSON).
- `ReadsRepo.identity_state(thread_id) -> IdentityState` (status `not_checked` when no row; `codes_sent` counts
  `identity_codes` rows; `tries_left` is the newest code's, 3 when none).
- `ActionsRepo.record(action) -> CompletedAction`: same key and same `records`/`before`/`after` returns the stored row;
  same key with different content raises `StorageError("actions", "UNIQUE (…)")`. `ActionsRepo.for_thread(thread_id)`.
- The unit of work: `with uow(write=True) as tx:` runs `BEGIN IMMEDIATE`; `with uow() as tx:` runs `PRAGMA query_only=ON`
  + `BEGIN DEFERRED`; anything not followed by `tx.commit()` is rolled back; an exception rolls back. `tx.identity` is
  this ticket's `IdentityRepos`; `tx.core.reads`, `tx.core.actions` are AEA-10's.
- `format_wall` stores UTC ISO-8601 and rejects naive datetimes; `parse_wall` returns UTC-aware datetimes. Aware
  datetimes in different zones compare correctly, so `NOW` in America/Chicago equals its UTC reading.
- Dispatch (AEA-22) calls `defn.executor(args, scope)` with **no unit of work open**, catches any `Exception` from it as
  `tool_failed`, re-stamps `lookup.tool`, `message_id`, `turn_id` and redacts `result_seen` with the STORE profile, and
  writes the `lookup_log` row itself when `effect == "read"`. Its `_CODE` pattern masks six-digit runs not preceded by
  `INV-`, `$` or `\d[.,]`.

**Construction rules (mypy strict over `src`, `tests`, `eval`; pydantic-mypy `init_typed = true`, `init_forbid_extra =
true`).** Build every pydantic model with keyword arguments, never positionally. Build rows read from SQLite with
`Model.model_validate({...})` from plain values (that also validates the ID patterns). Make an ID from text outside a model
with a module-level adapter, e.g. `_CUSTOMER_ID: Final = TypeAdapter(CustomerId)` then `_CUSTOMER_ID.validate_python(text)`;
never `CustomerId(text)` (it skips the pattern). Update a frozen model with `row.model_copy(update={...})`. `MeridianModel`
is `frozen=True`, `extra="forbid"`, `str_strip_whitespace=True`, `hide_input_in_errors=True`.

**Layering (DO-3 §2.1; matches `services/staff.py`, `services/ledger.py`).** `services/identity.py` may import
`meridian.domain.*`, `meridian.policy.limits`, `meridian.ports.runtime` and the row types from
`meridian.adapters.sqlite.repos_identity`; never `sqlite3`, never SQL. `agent/tools/account.py` imports
`meridian.domain.*`, `meridian.policy.{booking,texts}` and `meridian.ports.runtime` only — **never `meridian.adapters`,
never `meridian.services`, never `meridian.agent.tools.dispatch`**. `web/container.py` keeps its module-level imports
unchanged: the hunk imports inside its own body (`tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`).

### 4.2 Signatures this ticket implements (copied; graph-tools §4–§5, DO-4 §14)

```python
# src/meridian/adapters/sqlite/repos_identity.py  (graph-tools §5, GRT-10; ContactRow/contact/contacts added, R-3)
class IdentityThreadRow(MeridianModel):
    thread_id: ThreadId
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None
    masked_hint: str | None
    channel: Literal["phone", "email"] | None
    verified_at: datetime | None
    updated_at: datetime

class IdentityCodeRow(MeridianModel):          # code_hmac never leaves the service
    id: int
    thread_id: ThreadId
    customer_id: CustomerId
    code_hmac: str
    held_by: str
    sent_at: datetime
    expires_at: datetime
    tries_left: int = Field(ge=0, le=3)
    used_at: datetime | None
    inbox_message_id: int

class InboxRow(MeridianModel):                 # no code, no body columns
    id: int
    demo_session: str
    thread_id: ThreadId
    to_masked: str
    sent_at: datetime
    expires_at: datetime

class ContactRow(MeridianModel):               # added: the locate inputs, contacts wrapped as secrets
    customer_id: CustomerId
    name: str
    phone: SecretStr | None
    email: SecretStr | None

class IdentityRepos:
    def __init__(self, conn: sqlite3.Connection) -> None: ...          # the shell's constructor, unchanged
    def thread(self, thread_id: ThreadId) -> IdentityThreadRow | None: ...
    def save_thread(self, row: IdentityThreadRow) -> None: ...         # upsert on thread_id
    def add_code(self, thread_id: ThreadId, customer_id: CustomerId, code_hmac: str, held_by: str,
                 sent_at: datetime, expires_at: datetime, inbox_message_id: int,
                 *, tries_left: int = 3) -> int: ...                   # keyword: the service passes limits.tries
    def newest_code(self, thread_id: ThreadId) -> IdentityCodeRow | None: ...
    def codes_sent(self, thread_id: ThreadId) -> int: ...
    def spend_try(self, code_id: int) -> int: ...                      # tries_left − 1, floored at 0; returns new value
    def mark_used(self, code_id: int, used_at: datetime) -> None: ...
    def add_inbox(self, demo_session: str, thread_id: ThreadId, to_masked: str, sent_at: datetime,
                  expires_at: datetime) -> int: ...
    def inbox_for(self, demo_session: str) -> tuple[InboxRow, ...]: ...  # newest first; the session's rows only
    def code_for_inbox(self, inbox_message_id: int) -> IdentityCodeRow | None: ...
    def invoices_for(self, customer_id: CustomerId) -> tuple[InvoiceView, ...]: ...   # as billed (R-17)
    def invoice(self, customer_id: CustomerId, invoice_id: InvoiceId) -> InvoiceView | None: ...
    def contact(self, customer_id: CustomerId) -> ContactRow | None: ...               # added
    def contacts(self) -> tuple[ContactRow, ...]: ...                                  # added; ORDER BY customer_id
```

```python
# src/meridian/services/identity.py  (DO-4 §14 signatures unchanged; constructor parameter names are this ticket's)
class IdentityService:
    def __init__(self, uow: UnitOfWorkFactory, *, session_secret: SecretStr, limits: IdentityLimits) -> None: ...
    @property
    def boot_id(self) -> str: ...                                      # str(uuid4()) made once per instance
    def locate(self, thread_id: ThreadId, locator: Locator, now: datetime) -> Located | NotVerified: ...
    def send_code(self, thread_id: ThreadId, demo_session: str, now: datetime) -> CodeSent | NotVerified | CodeCapReached: ...
    def verify(self, ids: TurnIds, digits: SecretStr, now: datetime) -> Verified | CodeWrong | CodeExpired | CodeLocked: ...
    def inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]: ...
    # private: _held: dict[int, tuple[SecretStr, datetime]] (inbox message id → digits, expiry) under self._lock
```

```python
# src/meridian/agent/tools/account.py  (graph-tools §4)
class ReadInvoicesArgs(LLMFacing):
    invoice_number: InvoiceId | None = Field(default=None, description=INVOICE_NUMBER_HELP)
class ReadMembershipArgs(LLMFacing): pass
class ReadWarrantyArgs(LLMFacing): pass

WARRANTY_TERM_SENTENCE: Final[str]          # §4.4
def account_tools(uow: UnitOfWorkFactory) -> tuple[ToolDef, ...]: ...   # (read_invoices, read_membership, read_warranty)
def staff_notes_for(invoice: InvoiceView, tier: MembershipTier) -> tuple[StaffNote, ...]: ...
```

Shapes consumed (copied from `main`): `ToolCallScope(ids: TurnIds, customer_id: CustomerId | None, shown_slot_ids:
frozenset[int], now: datetime, message_id: int)`; `LookupEntry(tool: str, record_ids: tuple[str, ...], passage_ids:
tuple[PassageId, ...], result_seen: str, message_id: int, turn_id: TurnId)`; `ToolError(code: ToolErrorCode, message: str,
retryable: bool)`; `ToolResult(ok: bool, for_model: ToolError | JsonValue, captured: Capture | None, lookup: LookupEntry,
lookup_written: bool)`; `ToolDef(name, description, args_model: type[LLMFacing], kind: ToolKind, effect:
Literal["read","write"], requires_verified: bool, executor: Callable[[LLMFacing, ToolCallScope], ToolResult])`;
`CompletedAction(key: ActionKey, kind: ActionKind, records: dict[Literal["appointment","slot","old_slot","case","customer",
"promise"], str], before=None, after=None, at: datetime, source="actions_table")`; `ActionKey(thread_id, turn_id, kind,
record_id: str)`; `InboxMessage(id: str, at, to_masked, code: SecretStr | None, status: Literal["active","used","expired"],
expires_at)`; `CodeSent.sends_left: Field(ge=0, le=2)`; `CodeWrong.tries_left: Field(ge=1, le=2)`;
`CodeExpired(resend_offered: bool, sends_left: Field(ge=0, le=2))`; `StaffNote(kind: Literal["billed_differs_from_schedule",
"diagnostic_without_credit"], record_id: InvoiceId, text: str = Field(max_length=300), source_file:
Literal["pricing/2026_fee_schedule.pdf", "faq/customer_faq.md"])`; `AccountCapture(kind="account", invoices=(),
membership=None, warranty=None, staff_notes=())`; `MembershipView(tier, renewal_date: date | None)`;
`WarrantyView(install_date: date, equipment_brand: str | None, sentence: str)`.

### 4.3 Fixed values (exact strings)

| Name (module-private unless stated) | Value |
|---|---|
| mask dots | `"···"` (three U+00B7 MIDDLE DOT, as in graph-tools §5 and the OpenAPI `···02`) |
| ellipsis | `"…"` (U+2026) |
| phone hint | `f"the phone ending in {last2}"` ; phone `to_masked` `f"···{last2}"` |
| email hint | `f"the email at {first}···@…"` ; email `to_masked` `f"{first}···@…"` (`first` = first character of the local part) |
| `NOT_VERIFIED_MESSAGE` (account.py) | `"The customer has not been verified yet. Account tools work only after the one-time code is entered."` (= dispatch's `_MESSAGES[ToolErrorCode.NOT_VERIFIED]`, copied, not imported) |
| `INVOICE_NUMBER_HELP` (account.py) | `"The invoice number named in the conversation (INV- and six digits). Omit it to read every invoice on this account."` |
| tool names (public `Final`s) | `READ_INVOICES_NAME = "read_invoices"`, `READ_MEMBERSHIP_NAME = "read_membership"`, `READ_WARRANTY_NAME = "read_warranty"` |
| constructor errors | `ValueError("session secret is empty")`, `ValueError("identity limits outside the domain bounds")`, `ValueError("now must be timezone-aware")` |

Descriptions (agent-tools rule 2; exact; they mirror `knowledge.py`'s routing style):
- `read_invoices`: `"Returns this verified account's invoices as billed: invoice number, issue and due dates, line items with amounts in cents, total, balance and whether it is paid. Pass invoice_number to read one invoice, or omit it to read all of them. Use for bill, balance and line-item questions. Do not use for membership (read_membership) or warranty (read_warranty). It reports amounts as billed and never judges whether a charge is right."`
- `read_membership`: `"Returns this verified account's Comfort Club membership tier (none, standard or plus) and renewal date. Use for membership status and renewal questions. Do not use for invoices (read_invoices) or warranty (read_warranty)."`
- `read_warranty`: `"Returns this verified account's system install date, equipment brand and the installation labor warranty term. Use for warranty questions about the installed system. Do not use for invoices (read_invoices) or membership (read_membership)."`

### 4.4 Staff notes and the warranty sentence (exact)

- `WARRANTY_TERM_SENTENCE = "Meridian's labor warranty on a full system installation is 2 years; 5 years if you were a member at installation; a representative can confirm."`
  (Decision: no `TextId` exists for it in `policy/texts.py`; it is model-facing tool data, so it lives in `account.py`.
  It carries PRD R-17's quoted words and the KB's "2-year labor warranty on all full system installations".)
- Rule 1 note text: `f"{invoice_id} bills {description} at {_usd2(billed)}; the 2026 fee schedule {tail}."` where
  `tail = f"lists {_usd2(scheduled)} for {_TIER_PHRASE[tier]}"` when `scheduled > 0`, else `f"waives it for {_TIER_PHRASE[tier]}"`;
  `_TIER_PHRASE = {"none": "non-members", "standard": "standard members", "plus": "plus members"}`;
  `_usd2(c) = ("-" if c < 0 else "") + f"${abs(c) // 100:,}.{abs(c) % 100:02d}"` (so `$144.00`, `$2,140.00`).
  `source_file="pricing/2026_fee_schedule.pdf"`.
  → INV-204411, tier none: `"INV-204411 bills After-hours dispatch at $144.00; the 2026 fee schedule lists $149.00 for non-members."`
- Rule 2 note text: `f"{invoice_id} bills the {format_usd(diag)} diagnostic visit beside a repair with no credit line; the FAQ credits the diagnostic when the repair is approved at the same visit (the record does not say whether it was)."`,
  `source_file="faq/customer_faq.md"`.
  → `"INV-204411 bills the $89 diagnostic visit beside a repair with no credit line; the FAQ credits the diagnostic when the repair is approved at the same visit (the record does not say whether it was)."` (191 characters; cap 300)

---

## 5. Steps (build order; each checkable)

Module boundary: A4 only. Interfaces implemented: DO-4 §14 `IdentityService`, graph-tools §4 `account_tools` factory,
graph-tools §5 `IdentityRepos`. Interfaces consumed: `UnitOfWorkFactory` (port), `core.reads.{customer,invoice,
identity_state}`, `core.actions.{record,for_thread}` (AEA-10), `ToolDef`/`ToolResult` (AEA-02). No new Protocol or
abstraction.

### Step 0 — environment and prerequisites

1. In your worktree: `export UV_LINK_MODE=hardlink`; `uv sync` (hardlinked; no venv copy, no `node_modules`). Check
   `df -h /home` first; stop and report if under 4 GB free.
2. Import check (no baseline suite): `uv run python -c "import meridian.adapters.sqlite.repos_identity, meridian.policy.booking, meridian.web.container, tests.fixtures.sqlite"`.
3. The test-writer's frozen commit (`test(identity): frozen failing tests for AEA-27`) is on your branch. Run
   `uv run pytest tests/services/test_identity.py tests/services/test_identity_edges.py tests/unit/agent/tools/test_account.py -q`
   once: everything red for the right reason (`ModuleNotFoundError` for `meridian.services.identity` /
   `meridian.agent.tools.account`, or `AttributeError` on `IdentityRepos`). **Never edit a frozen file** (tamper check); a
   frozen test that looks wrong goes back to the orchestrator.

### Step 1 — nothing to do in schema

`40_identity.sql` is AEA-10's and already matches graph-tools §5: `identity_threads` (7 columns, status and channel
CHECKs), `identity_codes` (10 columns, `tries_left BETWEEN 0 AND 3`, index `ix_identity_codes_thread (thread_id, id)`),
`demo_inbox` (6 columns). No foreign keys reach these tables or `actions`, so tests need no `conversations` row.

### Step 2 — `adapters/sqlite/repos_identity.py` (PA-6; AC-12's cross-account half)

Every method runs on `self._conn` inside the caller's transaction; **none commits** and none sets
`self._conn.row_factory` (the connection is shared with six other repositories; read rows as tuples by position, as
`repos_core.py` does). Parameterised SQL with plain string literals only (no f-string SQL: ruff `S608`). Times are
written with `format_wall(dt)` and read with `parse_wall(text)`; dates with `date.fromisoformat`. Pass ids as `str(x)`.

1. Keep the module docstring's first line and the constructor `def __init__(self, conn: sqlite3.Connection) -> None:
   self._conn = conn` exactly (`test_repo_shells.py` checks its type hints and that `cls(sqlite3.connect(":memory:"))`
   builds without touching the database). Replace the `IdentityRepos` class docstring with exactly
   `"Repositories for 40_identity (identity_threads, identity_codes, demo_inbox) and the invoice reads; body AEA-27 (graph-tools §5, GRT-10)."`
   so it no longer contains `AEA-02 creates the constructor only`.
2. Row models exactly as §4.2, defined in this module (siblings keep their rows beside their repository:
   `repos_staff.FlagRow`, `repos_spend.SpendRow`).
3. Methods:
   - `thread`: `SELECT thread_id, status, customer_id, masked_hint, channel, verified_at, updated_at FROM identity_threads WHERE thread_id = ?` → `IdentityThreadRow.model_validate({...})` or `None`.
   - `save_thread(row)`: `INSERT INTO identity_threads (thread_id, status, customer_id, masked_hint, channel, verified_at, updated_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(thread_id) DO UPDATE SET status=excluded.status, customer_id=excluded.customer_id, masked_hint=excluded.masked_hint, channel=excluded.channel, verified_at=excluded.verified_at, updated_at=excluded.updated_at` inside `with integrity_errors("identity_threads"):`.
   - `add_code(...)`: `INSERT INTO identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, tries_left, used_at, inbox_message_id) VALUES (?,?,?,?,?,?,?,NULL,?)` under `integrity_errors("identity_codes")`; return `last_row_id(cur, "identity_codes")`.
   - `newest_code`: `... FROM identity_codes WHERE thread_id = ? ORDER BY id DESC LIMIT 1`. `codes_sent`: `SELECT COUNT(*) FROM identity_codes WHERE thread_id = ?`.
   - `spend_try(code_id)`: `UPDATE identity_codes SET tries_left = MAX(tries_left - 1, 0) WHERE id = ?`; `cur.rowcount == 0` → `raise StorageError("identity_codes", "no row")`; then `SELECT tries_left FROM identity_codes WHERE id = ?` and return it as `int`.
   - `mark_used`: `UPDATE identity_codes SET used_at = ? WHERE id = ?`; `rowcount == 0` → `StorageError("identity_codes", "no row")`.
   - `add_inbox`: `INSERT INTO demo_inbox (demo_session, thread_id, to_masked, sent_at, expires_at) VALUES (?,?,?,?,?)` → `last_row_id(cur, "demo_inbox")`. `inbox_for`: `... WHERE demo_session = ? ORDER BY id DESC`.
   - `code_for_inbox`: `... WHERE inbox_message_id = ? ORDER BY id DESC LIMIT 1`.
   - `invoices_for`: `SELECT invoice_id, issued_date, due_date, amount_cents, balance_cents, line_items FROM invoices WHERE customer_id = ? ORDER BY issued_date DESC, invoice_id DESC` → `_view(row)` each.
   - `invoice(customer_id, invoice_id)`: same columns `WHERE invoice_id = ? AND customer_id = ?` → `_view` or `None`.
     *Invariant (GRT-10):* another account's number and a missing number both read `None` (no account is revealed).
   - `contact`: `SELECT customer_id, name, phone, email FROM customers WHERE customer_id = ?` →
     `ContactRow.model_validate({"customer_id": r[0], "name": r[1], "phone": SecretStr(r[2]) if r[2] else None,
     "email": SecretStr(r[3]) if r[3] else None})` (an empty string counts as absent). `ContactRow` exists so the contact
     never travels unwrapped (`CustomerRow.phone` is a plain `str`).
   - `contacts`: same columns, all rows, `ORDER BY customer_id`.
4. `_view(row) -> InvoiceView` (module-private):
   1. `try: items = json.loads(row[5])` / `except (TypeError, ValueError): raise StorageError("invoices", "line_items not JSON") from None`.
   2. `items` must be a `list`; each item a `dict` with a `str` `"desc"` and an `int` (not `bool`) `"cents"`; else
      `raise StorageError("invoices", "line_items shape") from None`.
   3. `InvoiceView.model_validate({"invoice_id": row[0], "lines": [{"description": i["desc"], "amount_cents": i["cents"]} for i in items], "total_cents": row[3], "balance_cents": row[4], "issued_on": date.fromisoformat(row[1]), "due_on": date.fromisoformat(row[2]), "paid": row[4] == 0})`.
   *Invariant:* values as billed, never corrected (R-17); no error text holds a value.
5. Write `tests/unit/adapters/sqlite/test_repos_identity.py` (§7.2) and run it. Expected size: under 400 lines.

### Step 3 — `services/identity.py`

Module-private pure helpers: `_digits(text) -> str` = `"".join(ch for ch in text if ch in "0123456789")` (never
`str.isdigit`, which accepts non-ASCII digits); `_norm_name(text) -> str` = `" ".join(text.split()).casefold()`;
`_mask(contact: ContactRow) -> tuple[Literal["phone", "email"], str, str] | None`: phone usable when `contact.phone` is set
and `len(d := _digits(phone)) >= 10` → `("phone", f"the phone ending in {d[-2:]}", f"···{d[-2:]}")`; else email usable when
set, contains `"@"` and its local part is non-empty → `("email", f"the email at {local[0]}···@…", f"{local[0]}···@…")`;
else `None`. `_new_code() -> str` = `f"{secrets.randbelow(1_000_000):06d}"`.

1. **Constructor** (PA-5): `if not session_secret.get_secret_value(): raise ValueError("session secret is empty")`;
   if not `1 <= limits.tries <= 3` or not `1 <= limits.max_sends <= 3` or `limits.code_ttl_s <= 0` →
   `ValueError("identity limits outside the domain bounds")`. Keep `self._uow = uow`, `self._secret = session_secret`
   (the `SecretStr`, as `services/staff.py` does), `self._limits = limits`, `self._boot_id = str(uuid.uuid4())`,
   `self._held: dict[int, tuple[SecretStr, datetime]] = {}`, `self._lock = threading.Lock()`. No `__repr__` override.
   Private helpers:
   - `_hmac(digits: str) -> str` = `hmac.new(self._secret.get_secret_value().encode("utf-8"), digits.encode("utf-8"), hashlib.sha256).hexdigest()`.
   - `_sends_left(codes_sent: int) -> int` = `max(0, min(2, self._limits.max_sends - codes_sent))`.
   - `_check_now(now)`: `if now.tzinfo is None or now.utcoffset() is None: raise ValueError("now must be timezone-aware")`.
   - Under `self._lock`: `_prune(now)` deletes every `_held` entry whose expiry `<= now`; `_hold(inbox_id, digits, expires_at)`;
     `_held_code(inbox_id) -> SecretStr | None` (returns, does not remove); `_drop(inbox_id)` (`pop(…, None)`).
   Every public method first calls `_check_now(now)` then `_prune(now)`.

2. **Masking** — `_mask` above (PA-4). *Invariant:* only two digits of a phone or one letter of an email ever leave.

3. **`locate(thread_id, locator, now)`** (AC-1…AC-3, PA-1, PA-2):
   1. `with self._uow(write=True) as tx:` (`BEGIN IMMEDIATE`: one writer).
   2. `thread = tx.identity.thread(thread_id)`. If `thread is not None and thread.status == "locked"` → `return NotVerified()`
      (no write; the lock is final for the conversation).
   3. Candidates (`Locator` guarantees exactly one group is set):
      - `locator.customer_id is not None` → `c = tx.identity.contact(locator.customer_id)`; `matches = [c] if c else []`.
      - `locator.invoice_number is not None` → `inv = tx.core.reads.invoice(locator.invoice_number)`; `c =
        tx.identity.contact(inv.customer_id) if inv else None`; `matches = [c] if c else []`.
      - else (name + phone; both set) → `want = _digits(locator.phone.get_secret_value())`; if `len(want) < 10` →
        `matches = []`; else `want10 = want[-10:]`, `want_name = _norm_name(locator.name)`, `matches = [c for c in
        tx.identity.contacts() if c.phone is not None and len(d := _digits(c.phone.get_secret_value())) >= 10 and
        d[-10:] == want10 and _norm_name(c.name) == want_name]`. (mypy: assert-narrow `locator.phone` and `locator.name`
        with an `if ... is None: matches = []` branch, never `assert`.)
   4. `mask = _mask(matches[0]) if len(matches) == 1 else None`.
   5. If `mask is None` (0 matches, more than 1, or no usable contact): `tx.identity.save_thread(IdentityThreadRow(
      thread_id=thread_id, status="not_verified", customer_id=None, masked_hint=None, channel=None, verified_at=None,
      updated_at=now))`; `tx.commit()`; `return NotVerified()`.
      *Invariant (R-16, GRT-3):* the three causes take one code path, write the same row and return `NotVerified()`
      with no field; a previous match is unbound (PA-1).
   6. Else `channel, hint, _ = mask`; `save_thread(IdentityThreadRow(thread_id=thread_id, status="located", customer_id=
      matches[0].customer_id, masked_hint=hint, channel=channel, verified_at=None, updated_at=now))`; `commit()`;
      `return Located(masked_hint=hint)`. (A re-locate of a `verified` thread therefore de-verifies it: safe direction.)

4. **`send_code(thread_id, demo_session, now)`** (AC-4, AC-5, PA-2, PA-3):
   1. `with self._uow(write=True) as tx:`; `thread = tx.identity.thread(thread_id)`.
   2. `thread is None` or `thread.status in ("not_checked", "not_verified")` or `thread.customer_id is None` →
      `return NotVerified()` (no write).
   3. `thread.status == "locked"` → `return CodeCapReached()` (no write; same customer card as `CODE_LOCKED`, graph-tools §5).
   4. `sent = tx.identity.codes_sent(thread_id)`; if `sent >= self._limits.max_sends`: `save_thread(thread.model_copy(
      update={"status": "locked", "updated_at": now}))`; `commit()`; `return CodeCapReached()`. *Invariant:* the 4th send
      writes no code and no inbox row (AC-5).
   5. `contact = tx.identity.contact(thread.customer_id)`; `mask = _mask(contact) if contact else None`; `mask is None` →
      `return NotVerified()` (no write).
   6. `channel, hint, to_masked = mask`; `digits = _new_code()`; `expires_at = now + timedelta(seconds=self._limits.code_ttl_s)`.
   7. `previous = tx.identity.newest_code(thread_id)` (read before inserting).
   8. `inbox_id = tx.identity.add_inbox(demo_session, thread_id, to_masked, now, expires_at)`;
      `tx.identity.add_code(thread_id, thread.customer_id, self._hmac(digits), self._boot_id, now, expires_at, inbox_id, tries_left=self._limits.tries)`;
      `save_thread(IdentityThreadRow(thread_id=thread_id, status="code_sent", customer_id=thread.customer_id,
      masked_hint=hint, channel=channel, verified_at=None, updated_at=now))`. (Statuses `located`, `code_sent` and
      `verified` all reach here; a send on a `verified` thread moves it to `code_sent`: access drops until the new code
      is entered — safe direction, §8 R-5.)
   9. `self._hold(inbox_id, SecretStr(digits), expires_at)`; then `try: tx.commit()` / `except BaseException:
      self._drop(inbox_id); raise`. *Invariant:* digits are held only for a committed row, and a fresh committed row is
      never shown `expired` (AC-18).
   10. After the `with` block: `if previous is not None: self._drop(previous.inbox_message_id)` (PA-3: a superseded
       message reads `expired`).
   11. Never pass `digits` anywhere else. `return CodeSent(masked_hint=hint, expires_at=expires_at,
       sends_left=self._sends_left(sent + 1))` (first send → 2).

5. **`verify(ids, digits, now)`** (AC-6…AC-9, PA-3) — never returns `NotVerified` (GRT-3):
   1. `with self._uow(write=True) as tx:`; `thread = tx.identity.thread(ids.thread_id)`.
   2. `thread is not None and thread.status == "verified" and thread.customer_id is not None` → `existing = next((a for a
      in tx.core.actions.for_thread(ids.thread_id) if a.kind == ActionKind.VERIFIED and a.key.record_id ==
      str(thread.customer_id)), None)`; if found → `return Verified(customer_id=thread.customer_id, action=existing)` (no
      write, no try spent: the idempotent replay of AC-6; also protects AEA-10's R-3 "same key, different content").
   3. `thread is None` or `thread.status in ("not_checked", "not_verified", "locked")` or `thread.customer_id is None` →
      `return CodeLocked()` (no usable code in this conversation; fail closed to a person; no write).
   4. `sent = tx.identity.codes_sent(ids.thread_id)`; `left = self._sends_left(sent)`; `expired = CodeExpired(resend_offered=left > 0, sends_left=left)`.
   5. `thread.status == "located"` (a locate after the last send) → `return expired`.
   6. `code = tx.identity.newest_code(ids.thread_id)`; `code is None` or `code.customer_id != thread.customer_id` or
      `code.used_at is not None` → `return expired`.
   7. `code.tries_left == 0` → `return CodeLocked()`.
   8. Expiry (AC-8, AC-9): `now >= code.expires_at` or `code.held_by != self._boot_id` or
      `self._held_code(code.inbox_message_id) is None` → `return expired` (no try spent).
   9. Compare in constant time: `ok = hmac.compare_digest(self._hmac(digits.get_secret_value()), code.code_hmac)`.
   10. `ok`: `action = CompletedAction(key=ActionKey(thread_id=ids.thread_id, turn_id=ids.turn_id, kind=ActionKind.VERIFIED,
       record_id=str(code.customer_id)), kind=ActionKind.VERIFIED, records={"customer": str(code.customer_id)}, at=now)`;
       `stored = tx.core.actions.record(action)`; `tx.identity.mark_used(code.id, now)`;
       `tx.identity.save_thread(thread.model_copy(update={"status": "verified", "verified_at": now, "updated_at": now}))`;
       `tx.commit()`; then (after the commit) `self._drop(code.inbox_message_id)`; `return Verified(customer_id=code.customer_id, action=stored)`.
       *Invariant (AC-6):* the action row, `used_at` and status commit together or not at all; `_held` changes only after
       the commit (an injected fault leaves the code usable).
   11. Not `ok`: `left_tries = tx.identity.spend_try(code.id)`; if `left_tries == 0`: `save_thread(thread.model_copy(update=
       {"status": "locked", "updated_at": now}))`; `commit()`; `self._drop(code.inbox_message_id)`; `return CodeLocked()`.
       Else `commit()`; `return CodeWrong(tries_left=left_tries)`.
   - Never raise on a wrong, expired or locked code; exceptions come only from storage faults and carry no value.

6. **`inbox(demo_session, now)`** (AC-10, AC-18):
   1. `with self._uow() as tx:` (read-only). For each `row` in `tx.identity.inbox_for(demo_session)` (newest first):
      `code = tx.identity.code_for_inbox(row.id)`.
   2. Status: `code is not None and code.used_at is not None` → `"used"`; elif `code is None` or `now >= row.expires_at`
      or `code.held_by != self._boot_id` or `self._held_code(row.id) is None` → `"expired"`; else `"active"`.
   3. `code_value = self._held_code(row.id) if status == "active" else None`.
   4. `InboxMessage(id=str(row.id), at=row.sent_at, to_masked=row.to_masked, code=code_value, status=status, expires_at=row.expires_at)`.
   5. Return the tuple in that order. *Invariant (AC-18):* `active` ⇔ this process holds the digits, unused, unexpired.

Expected size: 250–350 lines (service cap 600).

### Step 4 — `agent/tools/account.py` (AC-12…AC-15, AC-19)

1. Args models and constants as §4.2–§4.4 (no docstrings on the args models, so the generated schema carries no extra
   text; `ReadMembershipArgs` / `ReadWarrantyArgs` bodies are `pass`).
2. **`staff_notes_for(invoice, tier)`** (pure; AC-14, AC-19):
   1. `notes: list[StaffNote] = []`.
   2. Rule 1, for each `line` in `invoice.lines` in order: if `line.description in SCHEDULE_FEES`: if
      `line.description in MEMBER_ALLOWANCE_ROWS and tier != "none"` → skip the line; `scheduled =
      SCHEDULE_FEES[line.description][tier]`; if `line.amount_cents != scheduled` → append `StaffNote(kind=
      "billed_differs_from_schedule", record_id=invoice.invoice_id, text=<rule-1 text, §4.4>, source_file=
      "pricing/2026_fee_schedule.pdf")`.
   3. Rule 2: `diag = [ln for ln in invoice.lines if ln.description == "Diagnostic visit" and ln.amount_cents > 0]`;
      `other = [ln for ln in invoice.lines if ln.description not in SCHEDULE_FEES]`; `credit = [ln for ln in
      invoice.lines if ln.amount_cents < 0]`; if `diag and other and not credit` → append one `StaffNote(kind=
      "diagnostic_without_credit", record_id=invoice.invoice_id, text=<rule-2 text with diag[0].amount_cents>,
      source_file="faq/customer_faq.md")`. (`amount_cents > 0`: a diagnostic billed at $0 has nothing to credit —
      AC-14's Plus case.)
   4. `return tuple(notes)`. *Invariant:* facts, never verdicts; the scheduled amount appears only here (never in
      `for_model` or `result_seen`).
3. **`account_tools(uow)`** returns `(ToolDef(name=READ_INVOICES_NAME, description=…, args_model=ReadInvoicesArgs,
   kind=ToolKind.ACCOUNT_READ, effect="read", requires_verified=True, executor=<closure>), <read_membership>,
   <read_warranty>)` in that order. No registry, no import-time side effect (same shape as `knowledge_tools`).
4. Every executor `(args: LLMFacing, scope: ToolCallScope) -> ToolResult`:
   1. `if not isinstance(args, <its args model>): raise TypeError("<tool name> expects <ArgsModel>")`.
   2. `scope.customer_id is None` → `ToolResult(ok=False, for_model=ToolError(code=ToolErrorCode.NOT_VERIFIED,
      message=NOT_VERIFIED_MESSAGE, retryable=False), captured=None, lookup=LookupEntry(tool=<name>, record_ids=(),
      passage_ids=(), result_seen="refused:not_verified", message_id=scope.message_id, turn_id=scope.ids.turn_id),
      lookup_written=False)` (defence in depth; dispatch refuses first).
   3. `with uow() as tx:` (read-only; dispatch runs executors with none open). Read, build, return inside the block.
      `lookup_written=False` always (dispatch writes the row).
   4. `row = tx.core.reads.customer(cid)`; `row is None` → `raise LookupError("customer row missing")` (dispatch turns
      it into `tool_failed`; no id in the message).
5. **`read_invoices`**: `views = tx.identity.invoices_for(cid)` when `args.invoice_number is None`, else
   `(v,) if (v := tx.identity.invoice(cid, args.invoice_number)) else ()`. `tier = row.membership_tier`.
   `for_model = {"invoices": [v.model_dump(mode="json") for v in views]}`;
   `captured = AccountCapture(invoices=views, staff_notes=tuple(n for v in views for n in staff_notes_for(v, tier)))`;
   `lookup = LookupEntry(tool=READ_INVOICES_NAME, record_ids=tuple(str(v.invoice_id) for v in views), passage_ids=(),
   result_seen=_invoices_seen(views), message_id=scope.message_id, turn_id=scope.ids.turn_id)`.
   `_invoices_seen(())` = `"invoices: none"`; else `"; ".join(f"{v.invoice_id} total {_usd2(v.total_cents)} balance
   {_usd2(v.balance_cents)} lines {' / '.join(_usd2(ln.amount_cents) for ln in v.lines)}" for v in views)`
   (→ `"INV-204411 total $478.00 balance $478.00 lines $89.00 / $245.00 / $144.00"`; dollar form so dispatch's STORE
   profile never mistakes a six-digit cents amount for a code).
   *Invariant (AC-12):* another account's number and a missing number give the identical `ToolResult`.
6. **`read_membership`**: `view = MembershipView(tier=row.membership_tier, renewal_date=row.membership_renewal_date)`;
   `for_model = {"membership": view.model_dump(mode="json")}`; `captured = AccountCapture(membership=view)`;
   `record_ids=(str(cid),)`; `result_seen = f"membership tier {view.tier} renewal {view.renewal_date.isoformat() if view.renewal_date else 'none'}"`.
7. **`read_warranty`**: if `row.system_install_date is None` → `view = None`, `result_seen = "warranty install none"`;
   else `view = WarrantyView(install_date=row.system_install_date, equipment_brand=row.system_brand,
   sentence=WARRANTY_TERM_SENTENCE)`, `result_seen = f"warranty install {view.install_date.isoformat()} brand
   {(view.equipment_brand or 'none')[:40]}"`. `for_model = {"warranty": view.model_dump(mode="json") if view else None}`;
   `captured = AccountCapture(warranty=view)`; `record_ids=(str(cid),)`.

Expected size: 200–280 lines.

### Step 5 — run the frozen tests until green

`uv run pytest tests/services/test_identity.py tests/services/test_identity_edges.py tests/unit/agent/tools/test_account.py -q`.
Fix code, never the frozen tests.

### Step 6 — `register_identity()` hunk (PA-7)

1. Replace only `register_identity`'s docstring and body in `src/meridian/web/container.py`. Docstring, exactly:
   ```
   """AEA-27 identity: IdentityService and the demo inbox (graph-tools §5).

   Provides Key[IdentityService]("identity_service"), the one IdentityService, built from the "uow_factory" key
   (AEA-10), settings.session_secret (the HMAC key, graph-core §12) and limits.identity (C-9). web/deps.py resolves
   get_identity_service from that key (AEA-23); the identity node (AEA-36), the CON-6 route (AEA-43) and GraphDeps
   (AEA-51) all use it.
   """
   ```
   It keeps the token `AEA-27` (`EXPECTED_HUNKS` check) and no longer contains `No-op until` (so the guard at
   `test_container.py` line 72 skips this hunk).
2. Body (the ledger hunk's shape, `register_spend`):
   ```python
   from meridian.ports.runtime import UnitOfWorkFactory
   from meridian.services.identity import IdentityService

   uow_key: Key[UnitOfWorkFactory] = Key("uow_factory")  # = web.deps.UOW_FACTORY (keys are equal by name)

   def build(c: Container) -> IdentityService:
       return IdentityService(c.get(uow_key), session_secret=settings.session_secret, limits=limits.identity)

   container.provide(Key[IdentityService]("identity_service"), build)
   ```
   No `on_start`, no `on_close`, no tool registration.
3. **Binding `get_identity_service`**: `web/deps.py` already maps `get_identity_service` → `IDENTITY_SERVICE =
   Key("identity_service")`; keys are equal by name, so providing the key here **is** the binding. Do not edit `deps.py`.
4. Write `tests/unit/web/test_register_identity.py` (§7.2) and run it with `tests/unit/web/test_container.py
   tests/unit/web/test_deps.py tests/unit/test_import_direction.py`.

### Step 7 — fast gates and affected tests (§7.3)

### Step 8 — journey file and record (AC-20)

1. Create `tests/journeys/j3/test_aea_27.py` exactly in this shape (harness rules: `tests/journeys/support/README.md`;
   no `dependency_overrides`, no monkeypatch of `meridian`, no `TestClient`, no doubles; no code, phone or secret
   literal):
   ```python
   """J-3 identity step (AEA-27; J-3's identity step is a proposed addition to the journey map, backend-amendments §3,
   pattern A). API level on AEA-57's harness: the real app, container and DB copy, scripted model.

   Step 0 runs today: the real app binds identity_service to the one IdentityService. Step 1 (code sent to SCR-2's
   inbox via listDemoInbox, entered through submitTurn, verified; a restart on the same working copy reads the message
   expired with no code; the stored row holds only the HMAC) is declared with its needs and stays blocked until
   AEA-40 (startChatSession, submitTurn), AEA-43 (listDemoInbox) and AEA-51 (run_graph) land. Its body is written with
   the graph's scripted outputs once AEA-51 lands (plan R-1).
   """

   from __future__ import annotations

   import uuid
   from datetime import UTC, datetime

   import pytest

   from meridian.services.identity import IdentityService
   from meridian.web.container import Key
   from tests.journeys.support.run import JourneyRun

   pytestmark = pytest.mark.journey

   J3 = "J-3"
   IDENTITY_TABLES = ("identity_threads", "identity_codes", "demo_inbox")
   CODE_STEP_NEEDS = ("login_sessions", "session_service", "turn_service", "run_graph", "identity_service")
   CODE_STEP_OPERATIONS = ("startChatSession", "submitTurn", "listDemoInbox")


   def test_j3_identity_service_bound_in_real_app(journey: JourneyRun) -> None:
       with journey.step(J3, "identity 0 service bound", needs=("identity_service",)):
           key: Key[IdentityService] = Key("identity_service")
           svc = journey.container.get(key)
           assert isinstance(svc, IdentityService)
           assert svc is journey.container.get(key)
           assert uuid.UUID(svc.boot_id).version == 4
           assert svc.inbox(str(uuid.uuid4()), now=datetime.now(UTC)) == ()
           for table in IDENTITY_TABLES:
               assert journey.db.count(table) == 0, table


   def test_j3_code_from_inbox_verifies_restart_reads_expired(journey: JourneyRun) -> None:
       with journey.step(
           J3,
           "identity 1 code from inbox verifies; restart reads expired",
           needs=CODE_STEP_NEEDS,
           operations=CODE_STEP_OPERATIONS,
       ):
           pytest.skip("J-3 identity body not written yet: needs AEA-51's scripted graph outputs (AEA-27 plan R-1)")
   ```
   Today the second test skips with `blocked-on AEA-40, AEA-51, AEA-43: …` from the harness (its own message), never
   reaching the body. `pytest.skip` inside the step is a `BaseException`, so the step records no false pass.
2. Run `uv run pytest -m journey tests/journeys/j3/test_aea_27.py -q -rs`. Passing looks like `1 passed, 1 skipped`, the
   skip reason starting `blocked-on`. Quote it in the record.
3. Create `docs/testing/journeys/<YYYY-MM-DD>-AEA-27.md`, layout of `docs/testing/journeys/2026-10-21-AEA-33.md` (title
   line, then the two-column table, then the "step to add" paragraph):
   - **Claim:** AEA-27 identity service, repository, account executors and `register_identity` (AC-1…AC-19, PA-1…PA-7);
     J-3 identity step 0 (the real app binds `identity_service`).
   - **Level:** `mock-tested` for the capability. Step 0 ran on AEA-57's harness (real app, real container, DB copy),
     but it calls the service from the test process, not through a route, so it does not lift the capability's level.
   - **Tested revision:** the commit SHA of the final code commit.
   - **Environment:** VPS worktree, Python 3.12, `temp_sqlite()` copies of the issued scheduling DB; the harness's own
     server on an OS-assigned loopback port for step 0; no model call, no paid call.
   - **Command:** the §7.3 affected-test command; `uv run pytest -m journey tests/journeys/j3/test_aea_27.py -q -rs`;
     `uv run python -m tests.journeys.affected --base main -- -q -rs`.
   - **Result:** `<N> passed` for the tests; the journey result line and the skip reason quoted; the affected-journeys
     output line(s) quoted.
   - **Evidence location:** GitLab issue #27 comment; this file.
   - **Remaining limitations:** CON-6 (`listDemoInbox`) and the code turn through CON-2 are not driven; the restart case
     is proven at the service level only (two instances over one file).
   - **Blocked by:** AEA-40 (`startChatSession`, `submitTurn`), AEA-43 (`listDemoInbox`), AEA-51 (`run_graph`; lands J-3).
   Then: "Journey step to add once all three land (`tests/journeys/j3/test_aea_27.py`, step 1): submit Omar's locate
   card through `submitTurn` (name and phone read from the DB copy at run time); `listDemoInbox` shows one `active`
   message with `to_masked` `···02`; enter its code through `submitTurn`; the thread reads verified and an
   `actions(verified)` row exists; `identity_codes` holds a 64-character HMAC and no digits; after a server restart on
   the same working copy `listDemoInbox` shows that message `expired` with no code (AC-18)."
   No code, phone, email or secret in the record.

### Step 9 — context (AC-21) and dev log

1. `.claude/reference/area-map.md`, the A4 row's **Status** cell: `planned` → `built: services/identity.py,
   adapters/sqlite/repos_identity.py (body), agent/tools/account.py actual (AEA-27, <sha>); container key identity_service`.
   Touch no other cell or row.
2. `docs/design/code-design.md` §3:
   - add one line after `**Built:** `policy/booking.py` (AEA-13, `cab183b`).`:
     `**Built:** `services/identity.py`, `adapters/sqlite/repos_identity.py` body, `agent/tools/account.py` (AEA-27, `<sha>`).`
   - append `   built AEA-27 <sha>` to the end of each of the three tree lines that start with `│   ├── sqlite/repos_identity.py`,
     `│   ├── identity.py                              locate, issue…` (the `services/` one, not `domain/`) and
     `│   ├── tools/account.py` (the AEA-33 `tools/knowledge.py` line shows the form). Nothing else.
3. `.claude/state/icm-progress.md`: **add** a new row directly after the last *Routes verified against code and tests*
   row: `| Routes verified against code and tests | provisional | 2026-10-21: area map A4 → services/identity.py,
   repos_identity.py, agent/tools/account.py checked against tests/services/test_identity{,_edges}.py,
   tests/unit/agent/tools/test_account.py, test_repos_identity.py, test_register_identity.py (AEA-27, <sha>; <N> passed);
   record docs/testing/journeys/<date>-AEA-27.md | Each slice adds its route; verified when every area-map row is actual |`
   (≤ 400 characters in the row; shorten paths if needed). Append `; AEA-27 identity (A4 routes row)` to the end of the
   *Last reconciled* line's first clause (`… — AEA-49 frontend serving (routes row)` → `… (routes row); AEA-27 identity (A4 routes row)`).
4. `git diff --name-only main...HEAD` must show no `schema/*.sql`, no `policy/booking.py`, and nothing outside §2.1.
5. Dev log file (outside the repo) per `.claude/reference/dev-log.md`: run header + one entry (Changed / Why / Checked /
   Remaining). No code, phone or secret.

### Step 10 — commits

Explicit paths only (`git add <path> …`; never `-A`). Suggested commits: `feat(identity): IdentityRepos body (AEA-27)` ·
`feat(identity): IdentityService with HMAC code, held digits, inbox (AEA-27)` · `feat(identity): account read executors
and staff notes (AEA-27)` · `feat(identity): register_identity hunk (AEA-27)` · `test(journeys): J-3 identity step
(AEA-27)` · `docs(AEA-27): journey record and context rows`. Every message ends with the line
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push (the merge step does).

---

## 6. Data and fixtures

All synthetic or issued; nothing personal is typed into a file.

| Data | Source | How tests get it |
|---|---|---|
| MHC-10002 (Omar Patel) name and phone | issued `customers` (temp copy) | `identity_support.customer_contact(store, "MHC-10002")` reads them at run time through a `sqlite3` connection on `store.db_path` |
| INV-204411 and its lines | issued `invoices` | through `IdentityRepos` / the executor; tests assert the billed values (8900, 24500, 14400, 47800, 2026-10-02, 2026-11-01) |
| Another account's invoice number | issued `invoices` | `SELECT invoice_id FROM invoices WHERE customer_id <> 'MHC-10002' ORDER BY invoice_id LIMIT 1` at run time (today `INV-200000`; never hard-code it) |
| Missing invoice number | synthetic | `"INV-999999"`; the test asserts it is absent first |
| MHC-10003 membership/warranty | issued `customers` | executor; expected values read from the same row at run time (`plus`, `2027-02-18`, `Lennox`, `2025-11-30`) |
| Ambiguous twin | synthetic, mutation of MHC-10002 (dimension: duplicate identity) | `INSERT INTO customers (customer_id, name, phone, email, service_address, city, zip, membership_tier) SELECT 'MHC-99991', name, phone, email, service_address, city, zip, 'none' FROM customers WHERE customer_id = 'MHC-10002'` on the temp copy |
| No-contact customer | synthetic | `('MHC-99992', 'Synthetic Nocontact', '', NULL, 'synthetic address', 'Austin', '78701', 'none')` (`phone` is `NOT NULL`, so `''`) |
| Email-only customer | synthetic | `('MHC-99993', 'Synthetic Mailonly', '', <email built at run time: "s" + uuid4().hex[:8] + "@example.test">, 'synthetic address', 'Austin', '78701', 'none')` |
| Synthetic invoice views (pure tests) | synthetic | `InvoiceView.model_validate({"invoice_id": "INV-900001", "lines": [{"description": "Diagnostic visit", "amount_cents": 0}, {"description": "Contactor replacement", "amount_cents": 24500}], "total_cents": 24500, "balance_cents": 24500, "issued_on": "2026-10-01", "due_on": "2026-10-31", "paid": False})`, and likewise for the tune-up cases (§7.1 AC-19 row) |
| Session secret | generated | `SecretStr(secrets.token_urlsafe(32))` per test |
| Codes | generated by the service | taken from `inbox()` (`msg.code.get_secret_value()`) at run time; wrong codes = `f"{(int(d) + 1) % 1_000_000:06d}"` |
| Clock | fixed | `NOW = DEMO_START` (`datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))`, imported from `meridian.adapters.sqlite.repos_cases`); later instants by `timedelta` |
| Ids | generated | `new_thread()`, `new_turn()` from `tests.unit.adapters.sqlite.helpers`; `TurnIds.model_validate({"thread_id": str(t), "turn_id": str(new_turn()), "request_id": str(uuid4()), "run_tag": "live", "run_id": None, "agent_version": "test"})`; `demo_session = str(uuid4())` |

`tests/services/identity_support.py` (frozen, test-writer; under 300 lines) holds: `NOW`; `new_secret()`; `make_service(store,
*, secret=None, limits=None) -> IdentityService` (default `IdentityLimits()`); `turn_ids(thread_id) -> TurnIds`;
`customer_contact(store, customer_id) -> tuple[str, str]`; `insert_customer(store, row: dict[str, object | None])` (raw
insert + commit on the temp copy); `only_code(svc, session, now) -> str` (the single active message's digits); `wrong(d) ->
str`; `count(store, table) -> int`; `non_issued_text(store, *, skip_columns=("code_hmac",)) -> str` (every value of every
table in `sqlite_master` except `ISSUED_TABLES` and `sqlite_sequence`, joined, without the HMAC column; the HMAC is checked
separately, R-8); `hmac_hex(secret, digits) -> str`; `locator(**fields: object) -> Locator` (= `Locator.model_validate(fields)`);
`scope_for_customer(customer_id: str | None, *, message_id=1) -> ToolCallScope` (= `ToolCallScope.model_validate({"ids":
turn_ids(new_thread()), "customer_id": customer_id, "shown_slot_ids": frozenset(), "now": NOW, "message_id":
message_id})`). Each test module wraps `temp_sqlite()` in its own `store` fixture (no `conftest.py` in `tests/services/`:
that folder is shared by other wave-2 tickets). Use a fresh `IdentityService` per scenario where a test runs several
(the held-digit map prunes by each call's `now`).

---

## 7. Checks

### 7.1 Frozen tests (test-writer writes these first, red; commit `test(identity): frozen failing tests for AEA-27`)

All four files follow §4.1's construction rules so `uv run mypy` stays green over `tests/`, and stay under 500 lines each.
The test-writer also runs `uv run pytest --collect-only -q` (everything collects) and the three files once (red for the
right reason: missing modules).

`tests/services/test_identity.py` (each uses a fresh `temp_sqlite()` store and `make_service`):

| Test | Arrange → act → assert |
|---|---|
| `test_wp2_omar_locate_code_verify_invoice` (WP-2) | `name, phone = customer_contact(store, "MHC-10002")`; `loc = Locator.from_form(FormValues(name=name, phone=SecretStr(phone)))`, `assert loc is not None`; `locate` → `Located(masked_hint="the phone ending in 02")`; `send_code(t, session, NOW)` → `CodeSent` with `expires_at == NOW + timedelta(minutes=10)`, `sends_left == 2`; `inbox(session, NOW)` → one message, `status == "active"`, `isinstance(code, SecretStr)`; `verify(ids, code, NOW + 1 min)` → `Verified`, `customer_id == "MHC-10002"`, `action.kind == ActionKind.VERIFIED`; then `account_tools(store.uow)[0].executor(ReadInvoicesArgs(), scope_for_customer("MHC-10002"))` → `for_model["invoices"][0]["invoice_id"] == "INV-204411"`, line amounts `[8900, 24500, 14400]`; `captured.staff_notes` kinds `["billed_differs_from_schedule", "diagnostic_without_credit"]`; `"149"` not in `json.dumps(for_model)` |
| `test_locate_each_locator_returns_masked_hint_only` (AC-1) | parametrise `kind ∈ {"name_phone", "customer_id", "invoice"}` (build the `Locator` at run time); result `== Located(masked_hint="the phone ending in 02")`; `set(json.loads(r.model_dump_json())) == {"kind", "masked_hint"}`; in a read uow `tx.core.reads.identity_state(t)` `.status == "located"` and `.customer_id == "MHC-10002"` |
| `test_not_verified_identical_for_every_cause` (AC-2) | insert MHC-99991 twin and MHC-99992; causes: `locator(customer_id="MHC-99999")` (assert absent first), Omar's name+phone (now ambiguous), `locator(customer_id="MHC-99992")`; each on a new thread; all three results `== NotVerified()` and `model_dump_json() == '{"kind":"not_verified"}'`; `count(store, "identity_codes")` and `count(store, "demo_inbox")` stay 0; each thread's `identity_threads` row has `status == "not_verified"` and NULL `customer_id`, `masked_hint`, `channel` |
| `test_locate_match_rules` (AC-3) | `d` = digits of Omar's phone; variants `f"({d[:3]}) {d[3:6]}-{d[6:]}"`, `f"{d[:3]} {d[3:6]} {d[6:]}"`, `f"+1 {d[:3]}-{d[3:6]}-{d[6:]}"`, `"1" + d`, `f"  {d}  "` → each `Located`; names `name.upper()`, `name.lower()`, `"  " + name.replace(" ", "   ") + " "` → `Located`; near-miss `name[:-1] + ("x" if name[-1] != "x" else "y")` → `== NotVerified()` |
| `test_send_code_stores_hmac_and_expiry_only` (AC-4) | locate + send with `IdentityLimits()`; newest code row (read uow): `code_hmac == hmac_hex(secret, digits_from_inbox)`, `held_by == svc.boot_id`, `sent_at == NOW`, `expires_at == NOW + 600 s`, `tries_left == 3`; one `demo_inbox` row with `to_masked == "···02"` and `demo_session == session`; result `sends_left == 2`; the digits do not occur in `non_issued_text(store)`; `PRAGMA table_info(demo_inbox)` has no column named `code` or `body`; a second service with `IdentityLimits(code_ttl_s=60)` on a new thread → `expires_at == NOW + 60 s` |
| `test_fourth_code_refused_and_unlocated_send` (AC-5) | locate; 3 sends → `CodeSent` (`sends_left` 2, 1, 0); 4th → `CodeCapReached()`; `identity_state.status == "locked"`; `count(demo_inbox) == 3`, `count(identity_codes) == 3`; a new thread never located: `send_code` → `NotVerified()`, counts unchanged, no `identity_threads` row for it |
| `test_verify_writes_verified_action_same_transaction` (AC-6) | (a) fault: `monkeypatch.setattr(IdentityRepos, "mark_used", <raises RuntimeError("injected fault")>)`; `pytest.raises(RuntimeError)` on `verify`; then 0 `actions` rows for the thread and status `code_sent`; `monkeypatch.undo()`; (b) `verify` same digits → `Verified`, one `actions` row (kind `verified`, `records == {"customer": "MHC-10002"}`), status `verified`; (c) `verify(ids)` again (same `TurnIds`) → `Verified` with equal `action`, still one row |
| `test_three_wrong_tries_lock` (AC-7) | `wrong(d)` ×2 → `CodeWrong(tries_left=2)`, `CodeWrong(tries_left=1)`; 3rd → `CodeLocked()`; correct `d` → `CodeLocked()`; `not isinstance(r, NotVerified)` for all four; status `locked` |
| `test_expired_code_and_resend_under_cap` (AC-8) | thread X: send at `NOW`, verify at `NOW + 599 s` → `Verified`; thread Y: send at `NOW`, verify at `NOW + 600 s` → `CodeExpired(resend_offered=True, sends_left=2)`; thread Z: sends at `NOW`, `NOW+1s`, `NOW+2s`, verify the newest digits at `NOW + 2 s + 600 s` → `CodeExpired(resend_offered=False, sends_left=0)` |
| `test_restart_expires_unheld_code` (AC-9) | svc1 locate + send; `d` from svc1.inbox; svc2 = `make_service(store, secret=same)`; `svc2.verify(ids, d, NOW + 1 min)` → `CodeExpired(resend_offered=True, sends_left=2)`; `svc2.inbox(session, NOW + 1 min)` → that message `code is None`, `status == "expired"`; `d not in repr(svc2.inbox(...))` |
| `test_inbox_scoped_to_login_session` (AC-10) | session S1: T1 send at `NOW`; T2 send at `NOW+200s`, verified at `NOW+250s`; T3 send at `NOW+300s`; session S2: T4 send; `inbox(S1, NOW + 650 s)` → ids descending = [T3, T2, T1 messages]; statuses `["active", "used", "expired"]`; codes `[SecretStr, None, None]`; S2's list shares no id with S1's; a fresh session → `()` |
| `test_verification_is_per_conversation` (AC-11) | thread A locate/send/verify Omar; thread B never touched → `identity_state(B).status == "not_checked"`; thread B located only → `"located"`, never `"verified"` |
| `test_code_phone_secret_absent_everywhere` (AC-16) | `caplog.set_level(logging.DEBUG)`; locate (name+phone), send, wrong try, correct try, `read_invoices`; collect every returned object's `model_dump_json()`, inbox `repr`s, `non_issued_text(store)`, `caplog.text`, the executor's `json.dumps(for_model)` and `lookup.result_seen`, and `str(exc)`/`repr(exc)` of an AC-6-style injected fault; assert `digits`, the stored phone string, its 10 digits and the secret occur in none of them, while `"SecretStr('**********')" in repr(inbox_message)`; separately, `code_hmac` is 64 lowercase hex characters and not equal to the digits; AST of `src/meridian/services/identity.py` and `src/meridian/agent/tools/account.py`: no `import logging`, no `print(` call, no name `TraceSink` |
| `test_records_for_cap1_and_wf3` (AC-17) | after the WP-2 flow: newest `identity_codes` row has a 64-char lowercase hex `code_hmac`, `sent_at`, `expires_at`; `PRAGMA table_info(identity_codes)` names exactly `id, thread_id, customer_id, code_hmac, held_by, sent_at, expires_at, tries_left, used_at, inbox_message_id`; `core.actions.for_thread(t)` has one `verified` action with `records["customer"] == "MHC-10002"`; the `read_invoices` result's `.lookup.tool == "read_invoices"`, `.record_ids == ("INV-204411",)`, `.message_id == scope.message_id`, `.turn_id == scope.ids.turn_id`, `.lookup_written is False` |
| `test_inbox_not_held_is_expired` (AC-18) | svc1 send; `svc1.inbox` → `active`, `code` a `SecretStr` whose value is 6 ASCII digits; svc2 (same file, same secret) `inbox` → `expired`, `code is None` |

`tests/services/test_identity_edges.py` (plan-added; same fixtures):

| Test | Arrange → act → assert |
|---|---|
| `test_relocate_no_match_unbinds_customer` (PA-1) | locate Omar (`Located`); locate `locator(customer_id="MHC-99999")` on the same thread → `NotVerified()`; state `not_verified`, `customer_id is None`; `send_code` → `NotVerified()`, 0 code rows |
| `test_locked_thread_stays_locked` (PA-2) | lock by three wrong tries; `locate` Omar again → `NotVerified()` and state still `locked`; `send_code` → `CodeCapReached()`; code count unchanged |
| `test_resend_supersedes_previous_code` (PA-3) | send, `d1`; send again, `d2`; `inbox` → newest `active` (d2), older `expired` with `code None`; `verify(d1)` → `CodeWrong(tries_left=2)` (if `d1 == d2`, skip that one assertion with a note); `verify(d2)` → `Verified` |
| `test_email_only_contact_hint` (PA-4) | insert MHC-99993; `locate(customer_id)` → `Located(masked_hint="the email at s···@…")`; send → inbox `to_masked == "s···@…"`; the email string absent from `non_issued_text` |
| `test_constructor_rejects_out_of_domain_limits` (PA-5) | `IdentityLimits(tries=4)`, `(tries=0)`, `(max_sends=0)`, `(max_sends=4)`, `(code_ttl_s=0)`, and `SecretStr("")` each → `ValueError`; messages contain no digit |

`tests/unit/agent/tools/test_account.py`:

| Test | Arrange → act → assert |
|---|---|
| `test_account_tool_defs_and_cross_account_invoice` (AC-12) | `defs = account_tools(store.uow)`; names `("read_invoices", "read_membership", "read_warranty")`; each `kind == ToolKind.ACCOUNT_READ`, `effect == "read"`, `requires_verified is True`; property names of `d.args_model.model_json_schema()` ∩ `set(ToolCallScope.model_fields)` is empty and none contains `"customer"`; `ToolRegistry(defs)` from `meridian.agent.tools.dispatch` builds without error; `read_invoices` with another account's number and with `"INV-999999"` → both `ok is True`, `for_model == {"invoices": []}`, `r1.model_dump_json() == r2.model_dump_json()`; with `scope.customer_id=None` → `ok is False`, `for_model.code == ToolErrorCode.NOT_VERIFIED` |
| `test_invoice_read_as_billed_staff_note_apart` (AC-13) | `read_invoices(ReadInvoicesArgs(invoice_number=<"INV-204411" via TypeAdapter>))` for MHC-10002: invoice dict `issued_on == "2026-10-02"`, `due_on == "2026-11-01"`, `total_cents == 47800`, `balance_cents == 47800`, `paid is False`, lines `[("Diagnostic visit", 8900), ("Contactor replacement", 24500), ("After-hours dispatch", 14400)]`; `s = json.dumps(for_model) + lookup.result_seen`: `"149" not in s`; none of `("wrong", "incorrect", "overcharg", "error", "mistake", "should", "differ", "schedule")` in `s.lower()`; neither note text in `s` |
| `test_staff_notes_rules` (AC-14) | `inv` = `IdentityRepos` read of INV-204411 (read uow) → `staff_notes_for(inv, "none")` == the two `StaffNote`s with the exact texts of §4.4, `record_id == "INV-204411"`, sources `pricing/2026_fee_schedule.pdf`, `faq/customer_faq.md`; synthetic Plus view `INV-900001` (§6: `Diagnostic visit` 0, `Contactor replacement` 24500) with tier `"plus"` → `()` |
| `test_membership_and_warranty_reads` (AC-15) | spy: wrap `ReadsRepo.customer` (from `meridian.adapters.sqlite.repos_core_aux`) with a counting wrapper via `monkeypatch.setattr`; MHC-10003: `read_membership` → `{"membership": {"tier": <row tier>, "renewal_date": <row date>}}` equal to the working copy's row (`plus`, `2027-02-18`); `read_warranty` → `install_date == "2025-11-30"`, `equipment_brand == "Lennox"`, `sentence == WARRANTY_TERM_SENTENCE == "Meridian's labor warranty on a full system installation is 2 years; 5 years if you were a member at installation; a representative can confirm."`; spy count ≥ 2 |
| `test_tune_up_member_no_note` (AC-19) | synthetic views via `InvoiceView.model_validate` (§6 shape): `INV-900002` with one line `Seasonal tune-up` 12900, tiers `"standard"` and `"plus"` → `()`; `INV-900003` with one line `Seasonal tune-up` 11900, tier `"none"` → exactly one note, kind `billed_differs_from_schedule`, text `"INV-900003 bills Seasonal tune-up at $119.00; the 2026 fee schedule lists $129.00 for non-members."` |

### 7.2 Implementer-written tests (with the code)

- `tests/unit/adapters/sqlite/test_repos_identity.py` (temp store; write uow + explicit `commit()` where a later read
  needs it):
  `test_thread_upsert_and_code_rows` (save/read a thread twice → one row with the second values; `add_code` →
  `tries_left` 3 by default and as passed; `spend_try` 3→2→1→0→0; `mark_used`; unknown id → `StorageError` with
  `table == "identity_codes"`); `test_inbox_rows_newest_first_per_session`; `test_invoice_views_as_billed_and_cross_account_none`
  (INV-204411 view values; `invoice(MHC-10003, INV-204411) is None`; `invoices_for(MHC-10002)` contains INV-204411);
  `test_malformed_line_items_hides_value` (raw `UPDATE invoices SET line_items = '<sentinel not json>'` on the temp copy
  → `StorageError`, the sentinel not in `str(exc)`); `test_contacts_wrap_secrets` (`repr(contact)` shows neither phone
  nor email; `contacts()` length 154 on the fresh copy).
- `tests/unit/web/test_register_identity.py::test_register_identity_builds_one_service` (shape of
  `test_register_spend.py`): with `temp_sqlite()`, `c = Container(settings=types.SimpleNamespace(session_secret=SecretStr(
  secrets.token_urlsafe(32))), limits=Limits())`; `c.provide(Key[Any]("uow_factory"), lambda _c: store.uow)`;
  `register_identity(c, FastAPI(), settings=c.settings, limits=c.limits)`; `c.build()`;
  `c.get(Key[IdentityService]("identity_service"))` is an `IdentityService`, the same object twice; a locate + send of
  MHC-10002 through it has `expires_at == NOW + 600 s` (proves `limits.identity` was passed); `"No-op until" not in
  (register_identity.__doc__ or "")` and `"AEA-27" in register_identity.__doc__`; `c.close()` in `finally`.

### 7.3 Commands (from the worktree root; `export UV_LINK_MODE=hardlink`)

While iterating (affected tests only):

```bash
uv run pytest tests/services/test_identity.py tests/services/test_identity_edges.py \
  tests/unit/agent/tools/test_account.py tests/unit/adapters/sqlite/test_repos_identity.py \
  tests/unit/web/test_register_identity.py -q
```

Once before the final commit — cheapest first, stop at the first red:

```bash
uv run ruff format --check src tests && uv run ruff check src tests
uv run mypy
uv run pytest tests/services/test_identity.py tests/services/test_identity_edges.py \
  tests/unit/agent/tools/ tests/unit/adapters/sqlite/ tests/unit/adapters/test_repo_shells.py \
  tests/unit/ports/test_protocol_shapes.py tests/unit/web/ tests/unit/test_import_direction.py -q
uv run pytest -m journey tests/journeys/j3/test_aea_27.py -q -rs
uv run python -m tests.journeys.affected --base main -- -q -rs
```

Why this set is "affected" (rule `build-loop-test-scope`): `tests/unit/adapters/sqlite/` (incl. `test_uow.py`, which
constructs `IdentityRepos`), `test_repo_shells.py`, `test_protocol_shapes.py` and `tests/unit/web/` (incl.
`test_container.py`, `test_deps.py`) are every test file that imports `repos_identity`, the container or names the
identity key (`grep -rlE "repos_identity|services\.identity|tools\.account|register_identity|IdentityRepos|IdentityService|account_tools|identity_service" tests eval`);
`tests/unit/agent/tools/` holds the registry that will list `account_tools`. No full suite: no shared fixture, settings,
dependency or cross-codebase module changes here. You may add `uv run --with pytest-xdist pytest -n 2 …` to the unit run
(never more than `-n 2`); run journeys serially.

Passing looks like: ruff and format clean; mypy `Success: no issues found`; every listed test passes (report the count);
the J-3 file gives `1 passed, 1 skipped` with a `blocked-on AEA-40, AEA-51, AEA-43` reason (owner order as the harness
prints it); the affected-journeys command prints its changed-file count and the journeys it selected (the `web/container.py`
hunk is in every harness journey's import closure, so expect most or all of `tests/journeys/j*/test_aea_*.py`) and then
their pytest result: passes, plus skips whose reason starts `blocked-on` or `blocked:`; **no failure and no error**.
Journeys make no paid call. Quote both journey outputs in the report and the record.

---

## 8. Risks and requests

- **R-1 · Journey step 1 body deferred (AC-20).** Driving SCR-2 → chat → verify needs AEA-40 (`startChatSession`,
  `submitTurn`), AEA-43 (`listDemoInbox`) and AEA-51 (`run_graph`, the scripted outputs of every graph role on the code
  turn). Writing the scripted outputs now would guess AEA-51's graph, which the ticket conventions forbid. This ticket
  writes the file with step 0 running and step 1 declared and blocked, plus the `mock-tested` record AC-20 allows.
  **Request to the orchestrator:** once AEA-51 lands, run a small follow-up on AEA-27's journey file (only that file and
  the record) to replace step 1's `pytest.skip` with the body the record describes, using AEA-51's J-3 scripts. Until
  then a `--journeys-strict` run (wave merge) reports step 1 as blocked on its owners, which is the harness's intended
  behaviour for a sibling that has not landed.
- **R-2 · Shared guard tests — closed.** Both guards are on `main` (`test_container.py` line 72, `test_repo_shells.py`
  line 30). This ticket edits neither file.
- **R-3 · Two read methods added to `IdentityRepos` beyond GRT-10** (`contact`, `contacts`) and a keyword `tries_left` on
  `add_code`. Locate needs to find a customer by name+phone, and no signed method does that; `core.reads.customer` returns
  a plain-string phone. Only this ticket's service calls them; no contract type changes. `contacts()` reads all 154 rows
  (fine at DO-1 scale; the Postgres step replaces it with an indexed digits column). The old `invoice_owner` is gone:
  locate-by-invoice uses AEA-10's `core.reads.invoice`. Reviewer: confirm no other caller.
- **R-4 · `get_identity_service` binding — closed.** `web/deps.py` on `main` resolves it from `Key("identity_service")`.
- **R-5 · Behaviours decided in this plan (engineering, no contract change, no product question):** a locked thread
  stays locked across re-locates (`NotVerified`, no write) and sends (`CodeCapReached`); a no-match re-locate unbinds the
  customer; a re-locate de-verifies a verified thread; a send on a verified thread moves it to `code_sent`; a resend
  supersedes the previous code; `verify` with no usable code returns `CodeLocked` (fail closed to a person), and in
  status `located` returns `CodeExpired`; rule 2 needs a diagnostic billed above $0 (AC-14's Plus case); the warranty
  sentence text (§4.4). Post these on issue #27 so AEA-36 (identity node) and AEA-38 (reply) know them; the AEA-36 plan
  already cites this item.
- **R-6 · Demo-session binding is the caller's.** `send_code(thread_id, demo_session, now)` trusts `demo_session`
  (DO-4 §14 signature); the inbox is scoped by it (N-11). **Request to AEA-36/AEA-51:** pass the conversation's own
  `str(session.session_id)` (web.md §4); CAP-1 proves it end to end. The AEA-36 plan (I-3, I-4) does.
- **R-7 · Names may differ on `main` — closed.** Every §4 name was found on `main` at `e22aebb`.
- **R-8 · Six-digit collision in AC-16's scans.** The random code could, by chance (about 1 in 10⁵ per run), appear
  inside a UUID or a timestamp in table text. `non_issued_text` skips `code_hmac` (checked separately); if a collision is
  ever seen, the helper re-runs the flow with a new code rather than weakening the check. The AEA-36 plan reuses this
  guard.
- **R-9 · AEA-10 R-3 (`actions.record` conflict rule).** A retried verify never recomputes the action: step 3.5.2
  returns the stored action before any write, so the same key never carries different content.
- **R-10 · Disk.** `/` at 90% (9.0 GB free at this refresh): one worktree, hardlinked venv, no `node_modules`; check
  `df -h /home` before `uv sync`.
- **R-11 · AEA-13 decision — closed.** AEA-13 merged with fee sentences option A (`dc1f4da`); the two constants this
  ticket imports are as graph-tools §4 fixes them.
- **R-12 · STORE redaction and `result_seen`.** Dispatch applies STORE to `result_seen`; its `_CODE` pattern skips digits
  after `INV-` and `$`, which is why `_invoices_seen` uses dollar amounts: a six-digit cents value would otherwise be
  masked as a code.
- **R-13 · One HMAC key for login tokens and codes (new).** graph-core §12 makes `Settings.session_secret` the key for
  both, and AC-4 recomputes the plain `HMAC-SHA256(session_secret, digits)`, so no domain-separation prefix is possible
  without changing the ticket. The risk is small: login tokens are 43-character `token_urlsafe(32)` strings and codes are
  six digits, so neither input can stand for the other, and the hashes live in different tables. The security reviewer
  may note it; it is not a decision for this ticket.
- **R-14 · Context-file merge conflicts (new).** `area-map.md`, `icm-progress.md` and `code-design.md` are edited by every
  slice in the wave; this ticket touches only its own A4 cell, one new row and one new line, so a conflict is a
  neighbouring-line conflict the merge agent resolves by keeping both sides.
- **No contract change, no decision reopened.** Nothing here alters `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`,
  DO-4/addenda types, or any of D-4…D-15.

---

## 9. Readiness

**READY.** No `NEEDS-DECISION`. **Blocked on: nothing.**

True imports, all merged on `main`: **AEA-02** (`domain/*`, `ports/runtime.py`, `config.Settings.session_secret`, the
`IdentityRepos` shell), **AEA-10** (`adapters/sqlite/db.py`, `40_identity.sql`, `repos_core*.py`, `migrate.ISSUED_TABLES`,
`tests/fixtures/sqlite.py`, the `uow_factory` key), **AEA-13** (`policy/booking.py`), **AEA-04** (not imported; dispatch
uses it). **AEA-57** (harness) is merged and used by the journey file.

**Not blocked on:** AEA-36/43/51/24 (consumers; build against DO-4 §14 with doubles), AEA-40/43/51 (journey step 1
evidence level only, R-1).

**Order for the orchestrator:** `test-writer-agent` writes §7.1 (`identity_support.py`, `test_identity.py`,
`test_identity_edges.py`, `test_account.py`; red for the right reason) and commits it; then `fanout-implementer` runs
steps 0–10. `security-privacy-agent` reads this diff at the wave-2 merge (HMAC, held digits, `NotVerified` identity,
cross-account reads, no value in errors/logs, R-13).

## Gates

None (no human, external, paid or live gate). Merge gate: lint and format, type check, the §7.3 affected tests, the
affected journeys; security review at the wave-2 merge.
