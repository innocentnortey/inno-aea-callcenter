## [AEA-27] identity: one-time code, inbox, account reads

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

> **US-8 · Prove it's my account with a code before private details.** "As a **homeowner** asking about my bill, I need
> to receive a one-time code at the phone or email on my account and type it in the chat, so that nobody else can read
> my account by guessing my name." Acceptance: "I see only a masked hint ('the phone ending in 02'); the code never
> appears in the chat; no match, a wrong code three times or an expired code ends in a person without revealing whether
> an account exists."
>
> **US-9 · Understand my invoice, membership or warranty after the code.** Acceptance: "INV-204411 lines read as billed
> ($89, $245, $144); no verdict on whether the bill is right; a dispute starts a handoff."

**Example pair (WP-2, Innocent ✓ 2026-10-20; graph-tools §1, §5 "In practice"):** **input** Omar submits the locate card
with name and phone for seeded **MHC-10002 Omar Patel**. **Output:** the identity node builds `Locator.from_form(…)` and
calls `locate` → `Located(masked_hint="the phone ending in 02")` and nothing else; `send_code` → `CodeSent(masked_hint=…,
expires_at=<now + 10 min>, sends_left=2)`; the six digits exist in two places only, their HMAC in `identity_codes` and
this process's in-memory store, and CON-6 `inbox()` shows them as a `SecretStr`. Omar types them → `verify` →
`Verified(customer_id="MHC-10002", action=…)`, with the `actions(verified)` row written in the same transaction. Then
`read_invoices` with `scope.customer_id = MHC-10002` returns **INV-204411**: issued 2026-10-02, due **2026-11-01**,
**$478.00**, unpaid; lines **Diagnostic visit $89**, **Contactor replacement $245**, **After-hours dispatch $144**, as
billed. The record-vs-policy gaps go to `AccountCapture.staff_notes` only, never to `for_model` or the lookup snapshot:
"INV-204411 bills After-hours dispatch at $144.00; the 2026 fee schedule lists $149.00 for non-members." and the
diagnostic-without-credit note (WP-2; HP-3; GRT-4).

The identity proof and the account reads behind it. Every shape below is defined in
[`stage7/graph-tools.md`](../../design/contracts/stage7/graph-tools.md) ("graph-tools §n"), which wins over DO-4 §14's
comments (DO-4 §16):

1. **`adapters/sqlite/repos_identity.py`** (body of AEA-02's shell, over the `40_identity.sql` that **AEA-10 writes**
   with graph-tools §5's columns: `identity_threads`, `identity_codes`, `demo_inbox`; slice plan §0, MC-10, C-4):
   `IdentityThreadRow`, `IdentityCodeRow`, `InboxRow` and `IdentityRepos(conn)` with `thread`, `save_thread`,
   `add_code` (`tries_left` 3), `newest_code`, `codes_sent`, `spend_try`, `mark_used`, `add_inbox`, `inbox_for` (newest
   first, the session's rows only), `code_for_inbox`, `invoices_for` and `invoice(customer_id, invoice_id)` (filtered by
   customer: another account's number reads as `None`, the same as a missing one) (GRT-10). Every method runs inside the
   caller's transaction; none commits. Times in these tables are **demo-clock** readings (the `now` DO-4 §14 passes),
   not wall time (MC-20).
2. **`services/identity.py`** (`IdentityService`, DO-4 §14's four signatures unchanged; each method opens and commits
   its own transaction). The constructor receives the unit-of-work factory, `Settings.session_secret` and
   `Limits.identity` (`IdentityLimits(code_ttl_s=600, tries=3, max_sends=3)`, AEA-01, C-9; no second literal), bound in
   this issue's `register_identity()` hunk; parameter names are this issue's own.
   - `locate(thread_id, locator, now)` → `Located | NotVerified`. `Locator` (AEA-02, `domain/identity.py`) holds
     exactly one of name + phone, customer ID or invoice number (R-15; a locator is not proof). Match rules: phone =
     digits only, last 10 equal; name = case- and space-insensitive full-name equality; 0 matches, more than 1, or a
     match with neither phone nor email → `NotVerified`. `masked_hint` is phone first ("the phone ending in 02"), else
     "the email at o···@…". Writes `identity_threads` status `located`.
   - `send_code(thread_id, demo_session, now)` → `CodeSent | NotVerified | CodeCapReached`: no located customer with a
     usable contact → `NotVerified`; 3 codes already sent in the conversation → `CodeCapReached` (state `locked`);
     otherwise **6 digits**, stored only as **HMAC-SHA256 under the session secret** (a plain hash of a 6-digit code is
     reversible by trying a million values, DO-3 §2.4) with `held_by = boot_id`, expiry `now + code_ttl_s`, one
     `demo_inbox` row for `demo_session` (`str(LoginSessionId)`) with `to_masked` "···02" and no code or body column.
   - **Where the digits live (GRT-2):** a process map `_held: dict[int, tuple[SecretStr, datetime]]` (inbox message id →
     digits, expiry) under a lock, plus `boot_id = uuid4()` per process; entries are pruned at expiry on every call.
     After a restart, a row whose `held_by` is not this `boot_id` counts as **expired** for `verify` and shows
     `code=None` in `inbox`.
   - `verify(ids, digits, now)` → `Verified | CodeWrong | CodeExpired | CodeLocked` (**never** `NotVerified`, GRT-3):
     correct and current → `Verified(customer_id, action)` with `actions(verified)` and `identity_threads` status
     `verified` in the **same** transaction, idempotent on its `ActionKey` (DO-3 §11 S-6); wrong → `CodeWrong(tries_left)`
     2 then 1; the 3rd wrong try, and any try after it → `CodeLocked`; expired or held by another boot →
     `CodeExpired(resend_offered, sends_left)` (`resend_offered` while under the send cap).
   - `inbox(demo_session, now)` → `tuple[InboxMessage, ...]`: this login session's messages only, newest first, each
     `active`, `used` or `expired`, `code` a `SecretStr` while this process holds the digits, else `None` (CON-6; N-11).
     The CON-6 route (AEA-43) unwraps it only while serialising.
   - **`NotVerified` has no fields** and is identical for no match, an ambiguous match and no usable contact; it covers
     no cap and no failed code (R-16; GRT-3). Each result reaches the customer as one CON-2 composed error per
     graph-tools §5's table (`NOT_VERIFIED`, `CODE_WRONG`, `CODE_EXPIRED`, `CODE_LOCKED`, `CODE_CAP_REACHED`); the
     identity node (AEA-36) maps them, this issue only returns them.
3. **`agent/tools/account.py`** (graph-tools §4; GRT-1, GRT-4): the factory `account_tools(uow) -> tuple[ToolDef, ...]`
   (no global or import-time registry; AEA-51 builds the `ToolRegistry`) returning `read_invoices`
   (`ReadInvoicesArgs(invoice_number: InvoiceId | None)`), `read_membership` and `read_warranty` (no-field args), each
   `kind` `account_read`, `effect` `"read"`, `requires_verified=True` (R-14), with no customer field in any args model
   (code binds `scope.customer_id`, DO-4 §5). Every read filters by `scope.customer_id`; an invoice number on another
   account reads as "no such invoice on this account" (`ok=True`, empty list), the same answer as a number that does not
   exist. `for_model` = the views only (`InvoiceView`, `MembershipView`, `WarrantyView`, graph-tools §3; amounts in
   integer cents); `captured` = `AccountCapture` including `staff_notes`; `lookup` = a `LookupEntry` whose
   `result_seen` holds ids and amounts, never staff-note text and never "149" (dispatch, AEA-22, writes it). Membership
   and warranty come from `core.reads.customer(customer_id)` (cases.md §1.2): tier and renewal date; install date with
   the warranty term sentence (2-year install labor; "5 years if you were a member at installation; a representative can
   confirm", R-17, K-9). The pure `staff_notes_for(invoice, tier)` reads `policy.booking.SCHEDULE_FEES` (AEA-13):
   rule 1, a scheduled-fee line billed at a different amount → one `billed_differs_from_schedule` note, except that a
   key in `MEMBER_ALLOWANCE_ROWS` ("Seasonal tune-up", AEA-13) is compared for tier `none` only, because its member value
   is an allowance ("Included (2/yr)"), not a price (graph-tools §4, R-G-3); rule 2, a
   "Diagnostic visit" line beside a non-scheduled line and no negative (credit) line → one `diagnostic_without_credit`
   note.
4. A `register_identity()` hunk in `web/container.py` (own hunk only) that builds the one `IdentityService` and binds
   `get_identity_service()` (web.md §4). No `register_` hunk for the tools (GRT-1).

### Source

- PRD R-14, R-15, R-16, R-17; DO-1 §10 rows *Identity code*, *No account fishing*; §A.4 *Identity service*.
- **Final contract:** [`stage7/graph-tools.md`](../../design/contracts/stage7/graph-tools.md) §1 (`ToolKind`,
  `ToolErrorCode`, factories, dispatch's lookup rule), §3 (capture shapes and views), §4 (account executors,
  `staff_notes_for`, `SCHEDULE_FEES`), §5 (identity result types, wire-code table, where the code lives, the three
  tables, `IdentityRepos`, limits, reset), cross-topic C-3, C-4, C-9, C-10; ledger
  [`7b-decisions/graph-tools.md`](../7b-decisions/graph-tools.md) GRT-1, GRT-2, GRT-3, GRT-4, GRT-5, GRT-10;
  residual [`7b-decisions/residuals-graph.md`](../7b-decisions/residuals-graph.md) R-G-3 (`MEMBER_ALLOWANCE_ROWS`). Join
  amendment AEA-27-1 (`docs/plans/ux-join/backend-amendments.md` §2; customer audit A-6).
  `stage7/cases.md` §1.0 (unit of work), §1.1 (`40_identity.sql` = graph-tools §5), §1.2 (`core.reads.customer`,
  `core.reads.identity_state`), §1.3 (reset clears `identity_threads`, `identity_codes`, `demo_inbox`), §2
  (`SCHEDULE_FEES` lives in `policy/booking.py`). `stage7/staff.md` §1 (`LoginSessionId`). `stage7/graph-core.md` §12
  (`Settings.session_secret`: "HMAC key for login tokens … and code hashing"). Merge MC-10, MC-20, MC-22.
- DO-4 §1 `IdentityState`, `ActionKey`, `CompletedAction`; §5 (`ToolDef`, `ToolCallScope`, `ToolResult`, `LookupEntry`,
  `AccountResult`, lookup-log rule); §7 (staff-only text); §14 `IdentityService`.
- DO-3 §2.4 (`identity.py` row), §3, §4.4, §7 R-15/R-16 row, §8 A4 row.
- OpenAPI `InboxMessage`, operationId `listDemoInbox` (CON-6; "the ONLY response that carries a code"); UI_CONTRACTS
  *Data classes* (D2, D3 "It is stored hashed"), *Named errors*.
- DO-6 WF-1, WF-3 (code-sent record: hash and expiry only), CAP-1, *Content and redaction* ("Verification codes: Never
  raw: hash and expiry only").
- WP-2 (`docs/data/worked-pairs.md`); HP-3; issued `SCHEMA.md` seeded customers MHC-10001…10004;
  `pricing/2026_fee_schedule.pdf` (via `SCHEDULE_FEES`).
- Slice plan row AEA-27; §3 rows `adapters/sqlite/repos_*.py`, `agent/tools/*.py`, `web/container.py`.
- **Brief check:** serves "They will ask their own questions and try to break it" (Deliverables 1) and "Do not let the
  agent guess" by refusing every private answer until a code proves the account, without revealing whether one exists;
  touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

Tests read Omar Patel's phone from the temp working copy at run time and take each code from `inbox()` at run time; no
phone number or code is written in a test file, fixture or test name (conventions). The session secret is generated at
test time.

- [ ] AC-1 [invariant] `locate` by each locator kind (name + phone, customer ID, invoice number) for MHC-10002 returns `Located` whose only value is `masked_hint == "the phone ending in 02"`, and writes `identity_threads` status `located` with the customer id — verify: `tests/services/test_identity.py::test_locate_each_locator_returns_masked_hint_only` (temp SQLite) — evidence: three cases pass; the serialised `Located` has exactly the fields `kind` and `masked_hint`.
- [ ] AC-2 [failure/refusal] No match, an ambiguous match (two customers sharing the name and phone digits in a test-built fixture row set) and a customer with neither phone nor email each return a `NotVerified` that compares equal and serialises byte-identically, and none writes a code or inbox row — verify: `tests/services/test_identity.py::test_not_verified_identical_for_every_cause` — evidence: the three serialisations equal `{"kind": "not_verified"}`; row counts unchanged.
- [ ] AC-3 [invariant] The match rules hold (graph-tools §5): the record's phone, read at run time and re-formatted with spaces, dashes, brackets and a leading country code, matches by its last 10 digits; the name matches regardless of case and extra spaces; a name that differs by one letter does not match and returns the same `NotVerified` as AC-2 — verify: `tests/services/test_identity.py::test_locate_match_rules` — evidence: the formatting variants all return `Located`; the near-miss returns `NotVerified`.
- [ ] AC-4 [invariant] `send_code` stores only `HMAC-SHA256(session_secret, digits)`, `held_by` = this instance's `boot_id`, `sent_at`, `expires_at = now + code_ttl_s` and `tries_left` 3, and writes one `demo_inbox` row for this `demo_session` with `to_masked` "···02"; the result is `CodeSent(sends_left=2)`; building the service with `IdentityLimits(code_ttl_s=60, …)` moves the expiry to 60 s, so no TTL literal lives in the service — verify: `tests/services/test_identity.py::test_send_code_stores_hmac_and_expiry_only` — evidence: `code_hmac` equals the HMAC recomputed in the test from the inbox's digits; no column of any table holds the six digits; both TTL cases asserted.
- [ ] AC-5 [failure/refusal] A fourth `send_code` in one conversation returns `CodeCapReached`, sets state `locked` and writes no inbox or code row; `send_code` on a thread with no located customer returns `NotVerified` — verify: `tests/services/test_identity.py::test_fourth_code_refused_and_unlocated_send` — evidence: inbox count stays 3; the unlocated case writes nothing.
- [ ] AC-6 [invariant] The correct code within the TTL returns `Verified(customer_id="MHC-10002")` and writes `actions(verified)` and `identity_threads` status `verified` in the same transaction; a fault injected after the action insert leaves neither; repeating with the same `ActionKey` writes no second row — verify: `tests/services/test_identity.py::test_verify_writes_verified_action_same_transaction` — evidence: one action row; the rollback case leaves zero rows and status `code_sent`.
- [ ] AC-7 [failure/refusal] Two wrong codes return `CodeWrong` with `tries_left` 2 then 1; the third returns `CodeLocked`; the correct code after the lock still returns `CodeLocked`; `verify` never returns `NotVerified` (GRT-3) — verify: `tests/services/test_identity.py::test_three_wrong_tries_lock` — evidence: the sequence asserted; the return type of every case is not `NotVerified`.
- [ ] AC-8 [failure/refusal] At exactly `expires_at` on the passed clock the code returns `CodeExpired(resend_offered=True, sends_left=…)` while under the cap, and one second before it is still accepted; at the cap `resend_offered` is `False` — verify: `tests/services/test_identity.py::test_expired_code_and_resend_under_cap` — evidence: the three instants asserted.
- [ ] AC-9 [failure/refusal] After a simulated restart (a new `IdentityService` instance over the same database), `verify` with the old code returns `CodeExpired` with resend offered under the cap, and `inbox` shows that message with `code=None` (GRT-2) — verify: `tests/services/test_identity.py::test_restart_expires_unheld_code` — evidence: both asserted; the old instance's digits never reach the new one.
- [ ] AC-10 [invariant] `inbox(demo_session)` returns only that session's messages, newest first, with status `active`, `used` (after a `Verified`) or `expired`, and `code` a `SecretStr` only while held; a second login session sees none of them — verify: `tests/services/test_identity.py::test_inbox_scoped_to_login_session` — evidence: two sessions give disjoint lists; the three statuses asserted; `code` is `None` for the expired message.
- [ ] AC-11 [invariant] Verification is per conversation: `Verified` in thread A leaves thread B, for the same customer, at `not_checked` through `core.reads.identity_state` — verify: `tests/services/test_identity.py::test_verification_is_per_conversation` — evidence: thread B's status asserted.
- [ ] AC-12 [failure/refusal] Every `ToolDef` from `account_tools(uow)` has `kind` `account_read`, `effect` `"read"`, `requires_verified=True` and an args model whose JSON schema has no customer field; `read_invoices` for MHC-10002 with another account's invoice number returns `ok=True` and an empty list, byte-identical to a number that does not exist — verify: `tests/unit/agent/tools/test_account.py::test_account_tool_defs_and_cross_account_invoice` — evidence: each def's flags asserted; the two results compare equal.
- [ ] AC-13 [invariant] The verified invoice read for MHC-10002 returns INV-204411 as billed (lines 8900, 24500, 14400 cents; total 47800; due 2026-11-01; `paid` false) in `for_model`, with no "149", no word judging the bill and no staff-note text in `for_model` or `LookupEntry.result_seen` — verify: `tests/unit/agent/tools/test_account.py::test_invoice_read_as_billed_staff_note_apart` — evidence: values asserted; "149" and each note's text absent from both.
- [ ] AC-14 [invariant] `staff_notes_for` on INV-204411 for a non-member returns exactly two `StaffNote`s (`billed_differs_from_schedule` naming $144.00 and $149.00; `diagnostic_without_credit`), both with `record_id` INV-204411; a Plus member's invoice with the diagnostic line billed at $0 gives none (GRT-4) — verify: `tests/unit/agent/tools/test_account.py::test_staff_notes_rules` — evidence: kinds, texts and source files asserted.
- [ ] AC-15 [invariant] `read_membership` returns tier and renewal date and `read_warranty` for MHC-10003 (Lennox installed 2025-11-30) returns the install date, the brand and the term sentence word for word, both read through `core.reads.customer` — verify: `tests/unit/agent/tools/test_account.py::test_membership_and_warranty_reads` — evidence: values equal the working copy's `customers` row; the sentence equals K-9's text.
- [ ] AC-16 [negative] After locate, send, a wrong try, a correct try and an invoice read, the code digits, the full phone number and the session secret are absent from every table's text (the digits appear only as their HMAC), from the captured log, from the in-memory trace sink, from every `ToolResult.for_model` and `LookupEntry.result_seen`, from every result object's serialisation and from every exception message; the digits' one permitted appearance is `inbox()`'s `SecretStr` (GRT-2) — verify: `tests/services/test_identity.py::test_code_phone_secret_absent_everywhere` — evidence: absence asserted per sink; `repr` of the inbox message shows the `SecretStr` mask.
- [ ] AC-17 [capture] The records CAP-1 (AEA-51) and WF-3 need are produced: the code-sent record (the `identity_codes` row: HMAC, `sent_at`, `expires_at`, no digits), the `actions(verified)` row with `records.customer`, and an account read's `ToolResult.lookup` with `tool`, `record_ids` (INV-204411), `message_id` and `turn_id` from the scope, ready for dispatch (AEA-22) to write — verify: `tests/services/test_identity.py::test_records_for_cap1_and_wf3` — evidence: each record present with its field set. No entry point is added here; CON-2 code entry and CON-6 are proven at their routes (AEA-40, AEA-43) and end to end in CAP-1.
- [ ] AC-18 [invariant] An inbox message whose digits this process no longer holds is never `active`: `IdentityService.inbox` reports `status: "expired"` with `code=None` for a row whose `held_by` is another boot id or whose expiry has passed, and keeps `active` with the code only while `_held` has it (customer audit A-6; amendment AEA-27-1; graph-tools §5 "where the code lives", GRT-2) — verify: `tests/services/test_identity.py::test_inbox_not_held_is_expired` (temp SQLite; send a code, build a second `IdentityService` over the same file to stand for a restart, list the inbox from both) — evidence: first instance `active` with digits; second `expired`, `code` None.
- [ ] AC-19 [invariant] `staff_notes_for` rule 1 skips the member comparison for a key in `MEMBER_ALLOWANCE_ROWS` (graph-tools §4, R-G-3): a Plus or standard member's "Seasonal tune-up" line billed at $129.00 gives no note; a non-member billed other than $129.00 for "Seasonal tune-up" still gets one `billed_differs_from_schedule` note — verify: `tests/unit/agent/tools/test_account.py::test_tune_up_member_no_note` — evidence: zero notes for the member cases; one note naming the billed amount and $129.00 for the non-member case.
- [ ] AC-20 [journey] Extends J-3 (slice plan §0a journey map; J-3's identity step is a proposed addition to the map, from the join audits; `backend-amendments.md` §3): J-3's identity step: the code sent to SCR-2's inbox (`listDemoInbox`) is read there, entered in the chat and verifies the customer; after a restart of the server on the same working copy the message reads `expired` with no code (customer audit A-6, AC-18); the stored code row holds only the HMAC; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_27.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_27.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-27.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-21 [regression/context] Same change updates: `.claude/reference/area-map.md` A4 rows (`services/identity.py`, `repos_identity.py`, `agent/tools/account.py`: planned → actual + commit), `.claude/state/icm-progress.md` (the affected row's evidence link), and DO-3 §3 rows for those files (status only) — verify: `git diff --name-only` — evidence: those paths besides the owned files; no `schema/*.sql` and no `policy/booking.py` in the diff.

### Observability

- Responsibilities: for the chat turn's code entry (WF-1, inside CON-2) and the demo inbox (WF-3): the code-sent record
  with hash and expiry only, `actions(verified)`, and the account reads' `LookupEntry` (written by dispatch, AEA-22;
  R-29). No code, full phone, email or session secret in any log, span, table text or response except the CON-6 inbox's
  `SecretStr` (DO-6 *Content*; UI_CONTRACTS D2, D3; GRT-2).
- Capture evidence: AC-17 here; AC-16 is the negative half. At the real entry points CAP-1 (AEA-51) drives WP-2 with the
  code read from the demo inbox and asserts the code absent from DB text, spans and logs.

### Evaluation

- Checks: keeps E-1's WP-2 invariant "nothing private before the code turn" and the identity edge cases DO-5 lists as
  synthetic cases (no match, wrong code three times, expired code) satisfiable; adds no suite. The eval harness (AEA-24)
  reads each code from CON-6, so AC-10's inbox contract is what lets E-1 drive WP-2.
- Expected-answer authority: the issued database (working copy) for account values, with invoices **as billed** (PRD
  R-17; WP-2 "wp2 144", Innocent ✓ 2026-10-20); R-15 / R-16 and graph-tools §5's result → code table for the identity
  outcomes; WP-2's *Gap* for the two staff notes.

### Metrics

- References: M-21 (rule "nothing private before a correct code"), M-8 (wrong facts in account answers), M-11 (the
  staff notes are brief items).
- Acceptance conditions: M-21 stays computable from `actions(verified)` ordering against the turn that first showed a
  record (AC-6, AC-17); M-8 and M-11 stay computable because values are read as billed and notes stay in
  `staff_notes` (AC-13, AC-14); no target is set here.

### Blocked by

AEA-04 (redaction profiles for logs and spans), AEA-10 (`40_identity.sql`, `core.reads.customer` /
`identity_state`, `repos_core.actions`, the unit of work, `temp_sqlite()`), AEA-13 (`policy/booking.SCHEDULE_FEES`,
added by GRT-4, and `MEMBER_ALLOWANCE_ROWS`, added by R-G-3; wave 1, so no wave moves).

AC-20's journey record names AEA-57 (harness, wave 2) and AEA-51 (the integrated turn) as *Blocked by* for its
integrated level only (`integrated-journeys.md` §4); they are evidence-level dependencies, not merge blockers, so no wave
moves.

### Agent handoff

- Area / owner: A4 Identity (DO-3 §8); slice plan AEA-27.
- Contracts and shared surfaces: consumes `Locator`, the result types and `InboxMessage` (`domain/identity.py`), the
  views and `AccountCapture` / `StaffNote` (`domain/specialists.py`), `ToolKind`, `ToolDef`, `ToolCallScope`,
  `ToolResult`, `LookupEntry`, `ActionKey` (AEA-02); `IdentityLimits` (AEA-01); `Settings.session_secret` (AEA-02); the
  unit of work, `core.reads.*`, `repos_core.actions` and the DDL (AEA-10); `SCHEDULE_FEES` and `MEMBER_ALLOWANCE_ROWS`
  (AEA-13; R-G-3). Journey: extends J-3's identity step in `tests/journeys/j3/test_aea_27.py` on AEA-57's harness
  (AC-20). Produces
  `IdentityService` for AEA-36 (front node: locate, send, verify), AEA-43 (CON-6 inbox), AEA-24 (reads codes via CON-6)
  and AEA-51 (wiring); `account_tools(uow)` for AEA-51's registry, dispatched by AEA-22 for the account specialist
  (AEA-35). Must not edit: `schema/*.sql`, `repos_core.py`, `db.py`, `domain/*`, `policy/*`, `gates/*`, other
  executors, other `register_` hunks.
- Scope boundary / refusal: no intake parsing of the code turn (AEA-12), no route (AEA-43), no mapping of results to
  wire codes or blocks (AEA-36, compose), no handoff on lock or not-verified (AEA-14 / AEA-39 decide; AEA-29 opens the
  case), no reset clearing (AEA-10's `clear_demo_tables`), no real SMS or email (DO-3 S-16), no verdict on any bill.
- Wave and gates: wave 2; no human gate. The session secret is a Railway variable at deploy (AEA-09); tests generate a
  placeholder at run time.
- Lane: build-loop — repository, service and executors the app runs.
- Risk: security (`risk::security`) — a bug here shows private account data without proof, leaks the code or full phone
  into logs, traces or tables, or lets an attacker learn whether an account exists.
- Entry points added or changed: None.
