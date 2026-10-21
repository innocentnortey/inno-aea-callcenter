## [AEA-62] browser journeys for integrated capabilities

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

> **Brief, Part B §6:** "The interface must be interactive: a reviewer should be able to type questions, probe edge
> cases, and watch the agent escalate." **US-28:** "sign in once with the demo login … then switch between acting as
> the customer and acting as a representative, supervisor or business owner in one click from any screen".

**Why this ticket exists.** AEA-51 and AEA-52 prove J-2, J-3, J-6 and J-8 through the HTTP API, and AEA-58 proves J-1 in
a browser. Nothing yet proves that a reviewer **in Chrome, on the production build, through the real login** can ask a
membership question and see its source, book a visit and have it remembered after a reload, watch a refund request
become a case that a representative opens with its brief, and switch roles without losing the chat. Those are the
Riverside failure classes (frontend state vs backend state, guards outside mock mode, fields the UI expects;
`.claude/rules/integrated-journeys.md`). Slice plan §0a: "AEA-62 (new, wave 4) puts J-2, J-3, J-6 and J-8 in a browser,
because they need the integrated graph." This also answers AEA-58's open question of who moves those journeys into the
browser.

**What it does, in practice (one leg, input → process → output).** *Input:* signed in through SCR-12 as the customer,
the browser types WP-1's "What does the Comfort Club membership actually include?" into SCR-1. *Process:* the real
server runs the gates, the real `FastembedIndex` over the 17-file manifest, the real graph and the R-46 checks; only the
provider call is AEA-57's scripted adapter, whose responder draft deliberately adds the archive's "$149". *Output, what
the user sees:* the reply states the current Standard benefits with a "Source" chip naming
`membership/comfort_club_overview.md`; "$149" is not on the page. *Output, what was stored:* that turn's `lookup_log`
row lists only current files (no `archive/` id), a `check_event` records the fact check's removal, and no identity
action or case exists. A 200 with the right words but the wrong stored rows fails the journey (rule §3.2).

**The four journeys, one file each** (slice plan §0a and §3 *tests/journeys/* row: one file per ticket per journey):

| File | Journey | Legs, from the worked pairs and the KB | Width (`apps/web/playwright.config.ts` projects) |
|---|---|---|---|
| `tests/journeys/j2/test_aea_62.py` | J-2 / rule `J-DRIVERS` | **Membership** WP-1 (stale twin `archive/comfort_club_overview.md`); **billing** WP-2 (MHC-10002, INV-204411, code from SCR-2, lines as billed); **warranty** "How long is the repair warranty?" (AEA-33 AC-2's query; audit K-8: 1 year on the repaired part from `warranty/warranty_policy.md` eff. 2025-06-15, never the 90 days of `archive/warranty_terms_2023.txt`) | 390×844 `chrome-phone` (SCR-1 is phone first) |
| `tests/journeys/j3/test_aea_62.py` | J-3 / `J-BOOK` | WP-3 booking (MHC-10001, north zone, Standard member, code to the phone ending 01, slot 56 Mon Oct 19 8:00 am – 12:00 pm Marta Kowalski) → confirmation → reload → a follow-up turn in WP-4F's turn-4 shape ("Yes, please.") that remembers the booking (R-45, N-27) | 390×844 |
| `tests/journeys/j6/test_aea_62.py` | J-6 / `J-ESC` | WP-7 refund ("I want a full refund on the repair. It didn't fix anything and I had to call another company.") → handoff card → role switch → SCR-5 row → SCR-6 with the eight-heading brief and promise; WP-8 cancel-membership as the second case (no false completion) | chat 390×844; console 1280×800 `chrome-desktop` (SCR-5/6 are laptop first) |
| `tests/journeys/j8/test_aea_62.py` | J-8 / `J-AUTH` | customer ↔ representative role switch from any screen (N-29, N-31), refresh and resume of the chat **and** of a case view, the customer-role refusal on a staff page and its legitimate path, signed out, expired session | 1280×800 |

**Every browser step asserts two things** (rule §3.2): what Chrome shows, located through AEA-58's selectors module, and
the persisted effect, read from the disposable working copy with AEA-57's read-only DB-state reader (`mode=ro`). Each
leg runs in its own conversation on its own fresh server instance from AEA-58's session fixture, so legs never share
limiter, identity or case state. Customer data (names, phones) and verification codes are read **at run time** from
the working copy and from SCR-2 (CON-6 `listDemoInbox`, opened in a second tab as SCREEN_SPECS SCR-1 says), never
written into a test file, and no screenshot is taken while a locate card, a code card or SCR-2 shows such a value.

**Scripted model outputs.** This ticket writes its own scripts per leg, in its own files, from the worked pair and the
production output schemas; AEA-57's adapter validates each against the real `output_model` and options, so a script that
disagrees with production fails the journey (AEA-57 AC-2). Scripts are adversarial where a gate is code's job, as AEA-51
does: the WP-1 responder adds "$149"; the WP-8 responder claims "Done, auto-renew is off". If the real system stores or
shows something other than the expected values here, the implementer reports a seam finding on the owning ticket; the
expectation is never edited to match (AEA-57 §2 rule).

**How it runs.** Entirely on what AEA-58 and AEA-57 provide, unchanged: AEA-58's browser fixtures (production `dist`
through the real app with `require_frontend=True`, system Chrome, viewports, locale `en-US`, timezone `America/Chicago`,
reduced motion), its selectors module, and its session-end hook that validates every `/api/*` response with AEA-23's
`assert_response_matches`; AEA-57's launcher, scripted adapter, login helper (demo pair from the per-run environment,
never the README), DB-state reader, evidence-record writer and blocked/strict options. Authentication, the gate, rate
limits, validation, the SQLite working copy and the checkpointer are all on; the dev-only `?signedin`, `?role`,
`?scenario` parameters are never used. A missing fixture, selector or control is a follow-up on AEA-58 (`browser/`) or
AEA-57 (`support/`), merged first; this ticket never edits either.

**The reviewer command** (time cap: apps/web README's Playwright rule; record option spelling per AEA-57's
`support/README.md`): `npm --prefix apps/web run build && npm --prefix apps/web run check:dist && perl -e 'alarm 300;
exec @ARGV' uv run pytest -m journey tests/journeys/j2/test_aea_62.py tests/journeys/j3/test_aea_62.py
tests/journeys/j6/test_aea_62.py tests/journeys/j8/test_aea_62.py --browser-channel chrome --journey-record=AEA-62`.

**Verification level.** Every journey criterion proves **`integrated with a scripted model`** (integrated-journeys §4:
real server, real DB copy, guards on, production build, scripted adapter). None proves `verified with live models`
(AEA-61's budgeted smoke) and none is a quality or containment number (E-runs, DO-5). J-4, J-5, J-7, J-9 and J-10 stay at
API level in their tickets and in each wave's recorded browser walkthrough (slice plan row).

**Produced for other issues.** AEA-55 and AEA-56 wait for this ticket: the browser evidence for the integrated customer
and staff paths exists before the UX-5 rerun and the deploy. The wave-4 merge and the pre-deploy gate run these four
files with all other journeys (`build-loop-test-scope.md`, *AEA addition*).

### Source

- Slice plan §0a (Amendment 1: journey map rows J-2, J-3, J-6, J-8; "AEA-62 (new, wave 4) puts J-2, J-3, J-6 and J-8 in a
  browser"; the open items for Innocent and the UX session), row AEA-62 (title, scope, blockers 58, 51, 52, wave 4,
  build-loop, no `risk::security`), §3 collision rows `tests/journeys/` ("one file per ticket per journey; `support/` is
  57's alone") and `apps/web/**`.
- `.claude/rules/integrated-journeys.md` §2 (the `J-BOOK` worked example: no dev parameters, the reload, stored-effect
  checks, the issued-DB hash; "A `200` from CON-2 with an unchanged row fails the journey"), §3 rules 1, 2 (`J-DRIVERS`,
  `J-BOOK`, `J-ESC`, `J-AUTH`), 3, 5 (a guard change shows the bad case blocked **and** the legitimate path passing), 6,
  §4 (levels; the nine record fields), §5, §6 (row "AEA-62 | 4 | Browser legs of J-2, J-3, J-6, J-8 against the
  production build"). `.claude/rules/build-loop-test-scope.md` *AEA addition*.
- Tickets this extends (read, never edited): AEA-58 (browser runner, selectors module, response hook, recipe; AC-7,
  AC-9, AC-10, AC-14), AEA-57 (`support/`; AC-2, AC-6, AC-7, AC-14, AC-16). The API-level journeys whose legs this
  moves into the browser: AEA-51 AC-6 (WP-1), AC-7 (WP-2), AC-8 (WP-3), AC-10 (WP-4F), AC-13 (WP-7), AC-14 (WP-8), AC-32;
  AEA-52 AC-5 (role refusals), AC-15.
- `docs/plans/ux-join/audit-customer.md` (A-1 history after reload, A-3 card `answered`, A-5 settled panel, B-3 sign-out
  thread id, G-1 selectors) and `audit-staff.md` (A2 presentation fields and the `source_id` join, B1/B2 role re-read,
  G1 and the staff selector table).
- `docs/data/worked-pairs.md` WP-1, WP-2, WP-3, WP-4 (fee-free variant, WP-4F), WP-7, WP-8; `docs/analysis/2026-10-20-brief-audit.md`
  K-8 (repair warranty); PRD §3 driver C (warranty), §4.3a knowledge map, R-10 (excluded files, DEC-4), R-17, R-26,
  R-28, R-29, R-45, R-48; US-6…US-14, US-18…US-20, US-28.
- SCREEN_SPECS SCR-1 (source chip, account card, slot card, confirmation card, handoff card, "What's settled"; copy notes
  for promise texts), SCR-2, SCR-4 (role switch; stale line), SCR-5, SCR-6 (eight-section brief, promise card, sources),
  SCR-12 (refusal and session-ended lines); N-27, N-29 (one role per login session; chat routes ignore the role), N-31.
- Contracts: stage7/web.md §2 (cookie, lifetime 43,200 s absolute on the wall clock, WEB-5), §4 (`owned_thread`,
  `get_wall_clock`), §6 (gate order, the 303 with `reason=none|expired`, WEB-28), §10 (`request`, `auth_event`), §13
  (`assert_response_matches`), §14 (`SessionService.thread` returns `ThreadHistory`: greeting, customer lines, turn
  replies, CON-4 rows, representative and event lines in time order; R-W-6, superseding the earlier "customer messages and
  each completed turn's stored response blocks"); stage7/staff.md §1–§3 (one role per login session, STF-19; `staff_sessions` columns;
  `set_role`; "logout and expiry delete the row"), §6; stage7/cases.md §1.1 (`conversations`, `cases`, `promises`,
  `lookup_log`, `check_events`, `turns`), §3.2 (promise table, two dues, CAS-10), §5 (`HandoffService`, CAS-33 staff
  guidance); DO-4 §7 (`BRIEF_TITLES`, `BriefItem.sources` → `source_ids`); graph-core §13 (`settled_view`); decision
  ledgers WEB-1 (open), WEB-5, WEB-28, STF-19, GRC-12, CAS-10, CAS-33. OpenAPI operations `login`, `logout`,
  `getSession`, `switchRole`, `startChatSession`, `getChatThread`, `submitTurn`, `listDemoInbox`, `getQueue`, `getCase`
  (read only).
- DO-6 `docs/design/observability-contract.md` rows WF-1, WF-3, WF-4, WF-18, WF-19; DO-7 M-7, M-9, M-10, M-18, M-22, M-27.
- **Brief check:** serves "Deploy the agent as a web application at a public URL. The interface must be interactive: a
  reviewer should be able to type questions, probe edge cases, and watch the agent escalate." (Part B §6), by proving
  the answer, booking, escalation and role paths run in a browser through the real login before deploy; touches nothing
  out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] One file per journey, no shared file edited: this ticket adds exactly `tests/journeys/j2/test_aea_62.py`, `j3/test_aea_62.py`, `j6/test_aea_62.py`, `j8/test_aea_62.py` and its record; AEA-57's file-convention check passes on them; `uv run pytest -m journey --collect-only -q` lists them beside AEA-57's and AEA-58's journeys; nothing under `tests/journeys/support/`, `tests/journeys/browser/`, `tests/conftest.py`, `src/meridian/` or `apps/web/` changes. Level: static — verify: `uv run pytest tests/journeys/support -q` (AEA-57 `test_journey_file_convention`) and `git diff --name-only` — evidence: convention check passes; collected ids; diff lists only the owned files and the context rows of AC-21.
- [ ] AC-2 [journey] **J-2 membership (WP-1)**, three questions in one chat. Sees: each reply holds its own facts from the current file (Standard: two tune-ups a year, priority scheduling, $89 diagnostic waived, 15% off repairs, no after-hours dispatch fee, reminders; $189/year or $16.99/month with a 12-month minimum, $99/year per additional system; Plus $269/year adds the plumbing items), each with a "Source" chip naming `membership/comfort_club_overview.md` that expands to its quoted passage. Stored: per turn, the `lookup_log` passage ids that back each chip, no identity action, no case, conversation outcome not `handed_off`. Level: integrated with a scripted model — verify: `tests/journeys/j2/test_aea_62.py::test_j2_membership_with_source` — evidence: per turn the chip file and the `lookup_log` ids printed side by side; screenshot after the third reply.
- [ ] AC-3 [negative] **J-2 stale twin never shown or cited:** none of "$149", "$12.99", "$219", "10% off", "cancel any time for a full prorated refund", "transfers to a new address" appears on the page in any J-2 membership turn; the scripted draft that adds "$149" has it removed by the R-46 fact check with a `check_events` row for that turn; no `lookup_log` passage id in any J-2 turn (all three legs) is under `archive/` or is `faq/faq_old_copy.md` (R-10, DEC-4); no chip names an excluded file. Level: integrated with a scripted model — verify: `j2/test_aea_62.py::test_j2_stale_values_absent` — evidence: 0 page hits per string; the removal `check_events` row; the passage-id list with 0 excluded files.
- [ ] AC-4 [journey] **J-2 billing (WP-2):** the locate card is filled with the account name and phone read from the working copy at run time; the code card reads "Code sent to the phone on record, ending in 02"; before the code, no invoice value is on the page; the code is read from SCR-2 in a second tab and typed into the code card; then "Thanks, you're verified for this chat." and an account card for INV-204411 with lines $89.00, $245.00, $144.00, total $478.00, due 2026-11-01 as billed, and no "$149" and no verdict word on the page (WP-2 decision "wp2 144"). Stored: an `actions` row `verified` for this thread; one `lookup_log` row whose record ids include INV-204411, written after the `verified` row; no case. Level: integrated with a scripted model — verify: `j2/test_aea_62.py::test_j2_invoice_after_code_as_billed` — evidence: the page values and the row order printed; screenshot of the account card only.
- [ ] AC-5 [journey] **J-2 warranty (K-8):** "How long is the repair warranty?" gets a reply stating the 1-year labor warranty on the part repaired with a "Source" chip naming `warranty/warranty_policy.md` (effective 2025-06-15); "90-day" and "90 days" are not on the page. Stored: the turn's `lookup_log` passage ids include `warranty/warranty_policy.md` and not `archive/warranty_terms_2023.txt`; no identity action (a policy question needs no code). Level: integrated with a scripted model — verify: `j2/test_aea_62.py::test_j2_warranty_current_policy` — evidence: chip file and passage ids printed; 0 page hits for the archive term.
- [ ] AC-6 [journey] **WF-1 (CON-2 from the browser), J-3 booking to confirmation (WP-3):** the code goes to the phone ending 01; the slot card offers Monday Oct 19 windows including "8:00 am – 12:00 pm" (slot 56, Marta Kowalski), 12–4 pm (Ray Mendoza) and 1–5 pm (Marta Kowalski) and no Saturday window; tapping 8:00 am – 12:00 pm and "Continue with this window" shows "You're booked. Here are the details." and the confirmation card ("Your visit", "Booked", "8:00 am → 12:00 pm", the date, the technician, the member fee waiver of CAS-7, never an $89 amount due), and "What's settled" shows the same visit. Stored: slot 56 no longer open, one appointment for MHC-10001 in that window, one `actions` row `booked` whose `turn_id` is the one CON-2 returned, the `lookup_log` rows for the window search; no case; the issued DB file's SHA-256 unchanged. Level: integrated with a scripted model — verify: `tests/journeys/j3/test_aea_62.py::test_j3_book_to_confirmation` — evidence: offered windows, card fields, row ids and both hashes printed; screenshot of the confirmation card.
- [ ] AC-7 [journey] **J-3 reload and follow-up memory (R-45, WP-4F turn-4 shape):** after a reload the same thread shows the greeting first, then the customer turns and the confirmation card from the stored blocks (full history per web.md §14 `ThreadHistory`, R-W-6, owned by AEA-40's AEA-40-1), and "What's settled" still shows the visit (from `getChatThread`'s `settled`); Chrome sends `getChatThread` for the same `thread_id` and no second `startChatSession`; the follow-up "Yes, please." gets the scripted reply that claims the booking and names Monday, 8:00 am and Marta, kept whole because `load_context` read the `booked` action into `settled` (GRC-12, SDQ-8). Stored: no completion-check `check_events` row for that turn; CON-2's `settled` equals the thread's `actions` rows; still one appointment and one `booked` row. Level: integrated with a scripted model — verify: `j3/test_aea_62.py::test_j3_reload_and_follow_up_remembers` — evidence: operation sequence printed (e.g. `login, startChatSession, submitTurn…, getChatThread, submitTurn`); the reply text; row counts before and after.
- [ ] AC-8 [failure/refusal] **J-3 no second write from an old card:** after the reload, tapping the slot card's 1–5 pm window (or resending the booking turn) books nothing: the slot and appointment rows and the `actions` rows are unchanged and no second `booked` row exists (`ActionKey` idempotency; a stale card becomes free text, graph-core §3, audit A-3) — verify: `j3/test_aea_62.py::test_j3_old_card_writes_nothing` — evidence: row counts and slot statuses before and after equal. Level: integrated with a scripted model. The card's visible "answered" state after reload is asserted only once audit A-3 has an owner (Agent handoff).
- [ ] AC-9 [journey] **J-6 escalation in chat (WP-7):** the refund message shows the handoff card with a reference in the form `MHC-C-NNNN` (MHC-C-0009 onward, after the four seeds), "A representative will get to your refund request within 2 business days." followed by "I can't promise an outcome.", the "Due" row "Tue Oct 20 · 7:00 pm", and the follow-up legend "We'll follow up by email unless you'd prefer a phone call."; "What's settled" shows the request with that reference. Stored: one `cases` row (reason `refund`, priority P3, `due_at` Tue Oct 20, 7:00 pm), one `promises` row whose text equals the `policy/handoff.py` table entry (cases.md §3.2) with status `open`, a `case_created` case event, the turn's `outcome` `handed_off` and the conversation's `outcome` `handed_off`; the reference on the page equals the stored one. Level: integrated with a scripted model — verify: `tests/journeys/j6/test_aea_62.py::test_j6_refund_handoff_in_chat` — evidence: card text and rows printed; screenshot of the handoff card.
- [ ] AC-10 [journey] **J-6 staff list:** one click on "Acting as" Representative from SCR-1 lands on SCR-5 (`/staff/queue`) with "Riley · demo representative"; the new case's row shows "P3 · Standard", its reference, the refund reason, "Unowned" and due "Tue Oct 20 · 7:00 pm" beside the four seed rows, MHC-C-0008 "P0 · Safety" first ("Safety and danger first, then by due time"). Stored: the `staff_sessions` row for this login now has role `representative` (same `session_id`); reading the queue writes no `case_events` row. Level: integrated with a scripted model — verify: `j6/test_aea_62.py::test_j6_case_in_staff_queue` — evidence: the row order and texts printed; role column before and after; screenshot of SCR-5.
- [ ] AC-11 [journey] **WF-4 (CON-12 `getCase` from the staff console), J-6 case opened with its brief (R-28, R-29):** opening the row shows SCR-6 at `/staff/cases/<ref>` with "Unassigned, nobody owns it yet", the promise card quoting the exact promise text and status Open, and eight brief sections whose headings equal `BRIEF_TITLES` in order (DO-4 §7), section 4 tagged "Customer says · not checked" holding "It didn't fix anything" and "I had to call another company" as claims, and the staff refund guidance attached as a sourced item (CAS-33); every brief chip resolves to a source card on the Sources tab (`#src-<source_id>`, audit A2). Stored: the brief's eight headings and their items equal what is shown; opening the case writes no `case_events` row and no change to `cases.version`. Level: integrated with a scripted model — verify: `j6/test_aea_62.py::test_j6_case_view_brief_and_promise` — evidence: headings, claims, chip → source pairs printed; screenshot of the brief.
- [ ] AC-12 [journey] **J-6 second case, no false completion (WP-8):** in a new chat as the customer, the cancel-membership request (after the code, renewal 2026-11-03 read) shows "I can't switch off auto-renewal from this chat." and a handoff card with "A representative will get back to you within 1 business day"; "Done, auto-renew is off" (the scripted claim) is not on the page; as the representative, SCR-5 lists this case with "P3 · Standard". Stored: a `membership_cancel` P3 case and its promise; a completion-check `check_events` row for the removed claim; no write to the customer's membership. Level: integrated with a scripted model — verify: `j6/test_aea_62.py::test_j6_membership_cancel_honest_limit` — evidence: page texts; case and check rows printed.
- [ ] AC-13 [journey] **J-8 role switch and resume:** with a chat open, switching to Representative shows SCR-5; switching back to Customer returns to SCR-1 and the **same** conversation (Chrome sends `getChatThread` for the same `thread_id` and no new `startChatSession`, N-31); reloading SCR-6 on a case shows the same case with the role still representative (`getSession`); the chat in tab A keeps working while tab B acts as representative, because chat routes ignore the role (N-29). Stored: one `staff_sessions` row whose `role` follows each switch with an unchanged `session_id` (STF-19); one `conversations` row; no `case_events` from reads. Level: integrated with a scripted model — verify: `tests/journeys/j8/test_aea_62.py::test_j8_role_switch_and_resume` — evidence: role column after each switch, operation sequence, conversation count printed.
- [ ] AC-14 [failure/refusal] **J-8 the role guard blocks and the legitimate path passes (rule §3 rule 5):** acting as the customer, opening `/staff/queue` shows SCR-4's line "You're acting as the customer. Switch to a staff role to see this." and no staff data, and its `getQueue` call answers 403 `ROLE_NOT_ALLOWED` with `details.reason` `wrong_role`; choosing Representative on that page then shows the queue with 200. Stored: no case read or write recorded for the refused call; the role column changes only on the switch. Level: integrated with a scripted model — verify: `j8/test_aea_62.py::test_j8_customer_refused_then_switch_allowed` — evidence: the 403 body (code and reason only) and the following 200 printed; screenshots of both states.
- [ ] AC-15 [failure/refusal] **J-8 signed out and expired:** "Sign out" on SCR-5 lands on SCR-12, the `staff_sessions` row is deleted, and reloading `/staff/cases/<ref>` answers the 303 to `/login?return_to=%2Fstaff%2Fcases%2F<ref>&reason=none`; signing in again lands on that case page. With the wall clock moved past `Limits.web.login_session_lifetime_s` (read from `Limits`, never a literal) the next navigation answers the 303 with `reason=expired` and `Set-Cookie: mhc_session` `Max-Age=0`, SCR-12 shows "Your demo session ended, so please sign in again.", and the row is deleted (staff.md §3, web.md §6). Level: integrated with a scripted model — verify: `j8/test_aea_62.py::test_j8_signed_out_and_expired` — evidence: statuses, `Location`, row presence per step printed; or, for the expired step only, AEA-57's blocked line naming the follow-up (Agent handoff), never a pass.
- [ ] AC-16 [negative] **Nothing private leaks into evidence, and no mock path is used:** the verification codes read from SCR-2, the full phone numbers typed into locate cards, the demo password and the `mhc_session` value appear in none of: the evidence record, screenshot files and names, test ids, captured server logs and the pytest output; no screenshot is taken while SCR-2, a locate card or a code card shows a value; no navigation carries `signedin`, `role`, `scenario`, `staffing`, `ex` or `delay`; every request goes to the test server's own `127.0.0.1:<port>` origin; nothing under `eval/cases/heldout/` or a held-out key directory is opened — verify: `j8/test_aea_62.py::test_j_aea62_evidence_clean` (scans the record, output dir and caplog for each run-time value; request origins from Playwright `request` events) plus `grep -rn heldout tests/journeys/j*/test_aea_62.py` — evidence: 0 hits per value; one origin; empty grep. Level: integrated with a scripted model (scan); static (grep).
- [ ] AC-17 [capture] **The browser paths leave their workflow records** (DO-6 rows; records checked present only, redaction stays with CAP-1, CAP-4, CAP-10, CAP-11): **WF-1** a `turn` row per J-2, J-3, J-6 message with `gate_result`, `outcome`, `server_ms`, `trace_export`, plus its `lookup_log`, `check_events` and `spend_ledger` rows, and the case and promise for J-6; **WF-3** a `request` record for each `listDemoInbox` read carrying the code request's `thread_id`; **WF-4** `request` records for `switchRole`, `getQueue` and `getCase` with `caller_role` as switched; **WF-18** `auth_event` `ok` at sign-in and `logged_out` at sign-out with the same opaque `session_id`; **WF-19** `request` records with route `spa_fallback` for page loads — verify: `j8/test_aea_62.py::test_j_aea62_records_present` (caplog on the in-process server plus the DB-state reader over the J-2, J-3, J-6, J-8 runs) — evidence: records listed per workflow with their ids. Level: integrated with a scripted model.
- [ ] AC-18 [capture] **One gate and one record:** the reviewer command passes on the integrated branch; every `/api/*` response in the four files passed AEA-58's session-end check (count per operationId, 0 failures; an undocumented status fails the run); the issued DB's SHA-256 is equal before and after; `git status --porcelain apps/web` is empty; `docs/testing/journeys/YYYY-MM-DD-AEA-62.md` holds every integrated-journeys §4 field (claim J-2, J-3, J-6, J-8 browser legs; level `integrated with a scripted model`; SHA and `agent_version`; environment with build hash, `scripted` adapter, Chrome channel and version; the command; pass, fail or blocked per leg with any failing assertion quoted; screenshots beside it; remaining limitations, at least J-4, J-5, J-7, J-9, J-10 not in a browser, re-login resume not asserted; *Blocked by* naming every blocked step's owner or "none") — verify: the reviewer command, then reading the record — evidence: pass line, response counts, two equal hashes, empty status, the filled record.
- [ ] AC-19 [invariant] The real `SessionInfo` is shown for every role (shell audit B5; AEA-62-1): switching through Customer, Representative, Supervisor and Owner shows, for each, the header name and the marked role that `getSession` returns (`display_name` "Customer (demo)", "Riley, demo representative", "Demo supervisor", "Demo business owner"), never a value from the mock's `switchRole` body — verify: `tests/journeys/j8/test_aea_62.py::test_j8_header_for_four_roles` — evidence: four header readings beside four `getSession` bodies. Level: `integrated with a scripted model`.
- [ ] AC-20 [failure/refusal] A role change made elsewhere reaches an open staff tab (staff audit B1, B2; AEA-62-2; R-W-18: the server already resolves the role per request and keeps `role_reset` until `switchRole`, staff.md §2): with SCR-6 open in tab A as the representative, switching to Customer in tab B and then focusing tab A shows the role panel with `[data-reason=wrong_role]` and no case data; a reset run from tab B then shows `[data-reason=role_reset]` in tab A on its next staff call, until a role switch. Applied once the UX session's B1/B2 fixes are in `dist`; until then these steps report `blocked-on UX session B1/B2`, never passed — verify: `tests/journeys/j8/test_aea_62.py::test_j8_role_change_elsewhere` — evidence: tab A's panel reasons and the 403 bodies printed; screenshots of both panels. Level: `integrated with a scripted model`.
- [ ] AC-21 [regression/context] Same change updates `.claude/reference/area-map.md` (journeys row: J-2, J-3, J-6, J-8 browser legs planned → actual with the commit), `.claude/state/icm-progress.md` row *Integrated-journey protection* (evidence link replaced by AC-18's record), DO-3 `docs/design/code-design.md` §9 test layout (the four `j<N>/test_aea_62.py` files and their status), and `tests/journeys/browser/README.md`'s journey list only if AEA-58 left a line for later tickets to add (otherwise a follow-up on AEA-58) — verify: `git diff --stat` — evidence: only those rows change beside this issue's owned files.

### Observability

- Responsibilities: emits no new record and adds no entry point (test code). It **preserves and proves**, through the
  browser path on the production build, the records these workflows require (DO-6 rows): **WF-1** customer chat (`turn`,
  `conversation`, `lookup_log`, `check_event`, `spend_ledger`; case and promise when handed off), **WF-3** demo inbox
  (`request` with the code request's `thread_id`; code hash and expiry only), **WF-4** staff console (`request` with the
  staff role on every call), **WF-18** demo login and logout (`auth_event` with the opaque `session_id`, never the
  username, password or cookie), **WF-19** page serving (`request` with route `spa_fallback`). It writes the
  integrated-journeys §4 evidence record. Redaction checks stay with CAP-1, CAP-4, CAP-10 and CAP-11 (rule §1:
  "journeys don't repeat them").
- Capture evidence: AC-17 (records present at the browser entry points), AC-16 (codes, phones, password and cookie
  absent from evidence and logs), AC-18 (the evidence record and the response checks).

### Evaluation

- Checks: no DO-5 suite (E-1…E-8) is added or changed and no number is reported; the four journeys join the
  deterministic journey suite in the merge gate (integrated-journeys §1 row "E-1…E-8 … Untouched"). A reviewer could
  argue the J-2 replies should be scored; free-text quality is E-1's with real models (AEA-24, Stage 9).
- Expected-answer authority: the worked pairs (WP-2, WP-3 checked by Innocent 2026-10-20; WP-1, WP-7, WP-8 "sure") for
  each leg's facts and refusals; the current KB file named by PRD §4.3a's knowledge map and the R-10 exclusions for every
  source chip (DO-5 *expected answers* table); brief audit K-8 for the warranty term; the issued DB (working copy) for
  account values and windows; `policy/handoff.py`'s promise table (cases.md §3.2) for promise texts and dues;
  SCREEN_SPECS copy notes for visible wording; the signed OpenAPI for every wire shape; the journey script for the
  scripted replies.

### Metrics

- References: M-7 (answers citing an excluded file: the J-2 `lookup_log` passage ids), M-9 (booking-rule validity: the
  J-3 write's slot, zone and member rules), M-10 (promise text equals the table entry: J-6's `promises.text`), M-18
  (conversations ended with neither resolution nor handoff: `conversations.outcome`), M-22 (conversations, turns and
  handoffs by reason), M-27 (open unowned cases: the J-6 case is unowned until claimed).
- Acceptance conditions: each journey asserts the source columns those metrics read are present and filled on the rows it
  created (AC-2…AC-13, AC-17), so they stay computable from stored records; the suite reports no metric value, and its
  disposable DB never reaches the deployed pages.

### Blocked by

- AEA-58 (browser runner, selectors module, response hook, production-build serving through AEA-49; carries `gate::ux4`).
- AEA-51 (the bound graph: J-2 and J-3 turns; `j2`/`j3` at API level).
- AEA-52 (real staff services: J-6 and J-8 at API level).
- AEA-28 (`SchedulingService.book` and its `fee_note`: the J-3 confirmation card AC-6 proves for R-20). Added at the
  coverage repair 2026-10-21 so the integration owner is directly blocked by the component it proves; AEA-28 is wave 2
  and already upstream through AEA-51, so the wave stays 4.
- AEA-40 (AEA-40-1: `getChatThread` full history, audit-customer A-1; AC-7's greeting after reload) and AEA-29 (AEA-29-2:
  display values and the `source_id` scheme, audit-staff A2; AC-11's chip → source check). Both are wave 2 and already
  upstream of AEA-52, so the wave stays 4.
- AEA-57 AC-17 (the wall-clock control for AC-15's expired step); AEA-57 is upstream already, so no wave change.

Calls (injected): none. It drives the real app; it consumes AEA-58's and AEA-57's fixtures and AEA-23's
`assert_response_matches` (through AEA-58's hook).

### Agent handoff

- Area / owner: journeys (integrated-journeys §6, AEA-62 row). Owns `tests/journeys/j2/test_aea_62.py`,
  `tests/journeys/j3/test_aea_62.py`, `tests/journeys/j6/test_aea_62.py`, `tests/journeys/j8/test_aea_62.py`, the record
  `docs/testing/journeys/YYYY-MM-DD-AEA-62.md` and its screenshots. The slice plan row's "`tests/journeys/browser/`" is
  read with §3's collision rule: `browser/` is AEA-58's, `support/` is AEA-57's; this ticket adds only its `j<N>` files.
- Contracts and shared surfaces: consumes AEA-58's browser fixtures, selectors module and session-end response hook;
  AEA-57's launcher, scripted adapter, login helper, DB-state reader, record writer and strict option; `Limits.web`
  (AEA-01); the OpenAPI (read only); `apps/web/dist` (UX-4, read only). Produces the browser evidence for J-2, J-3, J-6,
  J-8 that AEA-55 and AEA-56 wait for, and four files the wave and pre-deploy gates run. **Must not edit:**
  `tests/journeys/support/`, `tests/journeys/browser/`, `tests/conftest.py`, `tests/api/openapi_check.py`, any
  `src/meridian/` file, other tickets' `j<N>` files, `apps/web/**`, `docs/ux/**`, the OpenAPI.
- Follow-ups this may need (record `blocked-on AEA-NN`, merged first; never worked around): a selector AEA-58's module
  lacks → AEA-58. The wall-clock control for AC-15's expired step (the gate reads `get_wall_clock()`, web.md §4/§6) is
  now AEA-57 AC-17; if that criterion lands as `blocked-on AEA-23`, AC-15's expired step is reported blocked, never
  passed.
- Seams these journeys depend on, now owned (from `docs/plans/ux-join/`; a failure here is a seam finding on the owner,
  not an edit to the expectation): audit-customer **A-1** is AEA-40's AEA-40-1 (`getChatThread` holds the greeting,
  representative messages and event lines; web.md §14 `ThreadHistory`, R-W-6), so AC-7 asserts the greeting after reload;
  audit-staff **A2** is AEA-29's AEA-29-2 (display values and the `source_id` scheme behind AC-11's chip → source check).
  Audit-customer **A-3** (card `answered` after reload) is AEA-40's AEA-40-3 unless AEA-10's rows cannot give the
  `card_id`, in which case the UX session's fallback treats every history card as spent (R-W-6); AC-8's visible half stays
  out until that outcome is known.
- Awaiting UX session (`docs/plans/ux-join/` has the two audits but no `selectors.md` yet; nothing here invents a
  selector): (1) the **selector contract** for every state these journeys assert: SCR-1 block type, card id and
  answered state, source chip, "What's settled" visit and request rows, the account, slot, confirmation and handoff
  cards; SCR-2 message and code; SCR-5 rows; SCR-6 brief status, promise status, `#src-<source_id>` attributes, the role
  panel (audit-customer G-1 minimum list; audit-staff selector table, "add" rows). Present today and usable: the
  "Acting as" radiogroup, queue row button names, `#brief-1`…`#brief-8`, `#case-result`. Until the contract lands the
  planner records `blocked-on UX session selector contract` for the affected steps. (2) UX-owned fixes the journeys
  would hit: A-3 (card `answered` after reload; AC-8's visible half), A-5 (the settled panel; AC-7), B-3 (sign-out keeps
  the old thread id; AC-15's re-sign-in), staff B1/B2 (role re-read across tabs, R-W-18; AC-13's second tab sees only its
  next staff call change, and AC-20's panel steps wait on the B1/B2 fixes being in `dist`). (3) The runner choice and real-backend recipe are AEA-58's, used
  as AEA-58 fixes them.
- Awaiting Innocent: WEB-1 — built on the recommended option A (`/login`, `/assets/`, `/fonts/` load without a
  session). If he picks B (a self-contained login page), the journey steps stay the same and only the SCR-12 selectors
  and AC-17's WF-19 records before sign-in change. If he picks C (the whole shell public), AC-15's signed-out and expired
  steps assert the app reaching `/login?return_to=…&reason=…` after a 401 instead of a server 303.
- Scope boundary / refusal: browser legs of J-2, J-3, J-6 and J-8 only; J-4, J-5, J-7, J-9, J-10 stay at API level and in
  the wave walkthroughs (slice plan row). Claim, join, live reply and hand back are J-7 (AEA-52), not here. The WP-4F
  **move** stays at API level (AEA-51 AC-10); here J-3's follow-up memory is shown on WP-3's booking. **Chat resume after
  signing in again** is not asserted: SCR-1 says the chat resumes, but web.md §2 starts a new login session and §4's
  `owned_thread` answers 404 for another session's thread; slice plan §0a lists it as open for Innocent and the UX
  session, so AC-15 asserts landing on the `return_to` page only. No production code, no live model calls (AEA-61), no
  Prism, Vite dev server or UX-5 suite (AEA-55), no redaction re-checks (CAP tests), no build of `apps/web` inside a test.
- Wave and gates: wave 4; no own human gate (it inherits `gate::ux4` through AEA-58). At the wave-4 merge and before
  deploy the merge agent runs these four files with all journeys under the strict option; ticket merges run them when a
  diff touches a module, route, prompt, schema or frontend build input on their path (`build-loop-test-scope.md`, *AEA
  addition*).
- Lane: `lane::build-loop` — it adds test code the merge gate runs (ticket-lanes: tests are code-read).
- Risk: None per the slice plan. It changes no production code; it handles verification codes, phone numbers, the demo
  pair and the session cookie only inside the test run, and AC-16 keeps all four out of evidence and logs.
- Entry points added or changed: None
