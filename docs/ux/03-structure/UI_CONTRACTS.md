# UX-3 · UI contracts (what each screen needs from the backend)

> Status: DRAFT: every card is **specified (UX-3, proposal)** until the §6 Design gate · Date: 2026-10-21 · OpenAPI: [`ui-contracts.openapi.yaml`](ui-contracts.openapi.yaml) (OpenAPI 3.1, 30 operations)
> Card format and rules: `.claude/skills/ux-pipeline/references/ui-contracts.md`
> Inputs: draft CON-1…CON-20 in [`USER_FLOWS.md`](../01-planning/USER_FLOWS.md) (IDs and meanings kept) · screens and the contract needs N-1…N-27 in [`SCREEN_SPECS.md`](SCREEN_SPECS.md) · decisions of 2026-10-21 (Innocent and system design §6, §8.1) · DO-4's requests UXR-1…UXR-20 in `docs/design/contracts/api-con-mapping.md` §5 (adopted below).

## How to read this file

**What a contract is, in practice.** The customer taps the window "8:00 am – 12:00 pm" on a slot card. The page posts one request to CON-2 with a `turn_id` and the card's `option`. The backend answers HTTP 200 with a list of reply blocks (here: a confirmation ticket) and a `settled` object that says what the conversation has done so far (here: one booking). If the window was taken a moment earlier, the answer is still HTTP 200, but the block is `error: SLOT_TAKEN` with fresh windows, so the screen can say "Sorry, that window just went." and show a new card. If the screen can show a state, some response here can produce it.

**Two kinds of failure, kept apart (UXR-1).**

| Kind | HTTP | Example | What the screen gets |
|---|---|---|---|
| Composed outcome: the server decided what to say | **200** | SLOT_TAKEN, CODE_WRONG, NOT_VERIFIED, RATE_LIMITED, TURN_TIMEOUT, BUSY, AI_PAUSED | An `error` block or a `notice` **plus `settled`**, so the "What's settled" panel stays true |
| Request the server could not process | **4xx / 5xx** | VALIDATION_ERROR, SESSION_NOT_FOUND, SESSION_ENDED, UNAUTHENTICATED, VERSION_CONFLICT | `{error: {code, field, constraint, details}, request_id}`. Never the rejected value |

**Conventions on every operation.**

- Base `/api`, JSON. `X-Request-ID` on every response. Times are ISO 8601 with offset (America/Chicago, the demo clock). Money is integer cents plus the display string the policy text uses ("$49").
- Cookies: **one session cookie, `mhc_session`**, set by login (CON-22). It identifies the login session (which owns that session's chat threads and scopes the demo inbox) and **carries the current role** (customer, representative, supervisor, owner). It replaces `mhc_demo` and `mhc_staff`, which are retired; `mhc_session` is the only cookie left. `HttpOnly`, `SameSite=Lax`, `Secure` in deploy. A thread this login session does not own answers `404 SESSION_NOT_FOUND`, the same as an unknown one. Two tabs in one browser share the session and the role; chat routes do not check the role, so a customer chat keeps working in one tab while another tab acts as staff.
- Every block carries `speaker {kind, display_name}` and `at`. Cards with keys carry `card_id`, `options[]` and `answered`.
- **Prism needs the cookie.** The mock enforces the cookie security scheme, so the UX-4 prototype must send `mhc_session` (any value) on every call except login, or the mock answers 401. Login returns the customer role; switching role is a PUT to `/api/session/role`.
- Examples are synthetic or issued test data: Omar Patel (MHC-10002), INV-204411, MHC-C-0007, technician Jun Park, code 482913 (only in CON-6), the fictional emergency number (512) 555-0199. Numbers in CON-18/19/20 examples are **made-up example values**, not results.

**Data classes** (used in every card's "Data class" line).

| Class | What | May go to the model | Logs and traces | Customer UI | Staff UI | Monitoring page |
|---|---|---|---|---|---|---|
| D0 Public | Policy text, fees, windows, source passages | yes | yes | yes | yes | yes |
| D1 Demo identifiers | Case reference, invoice number, appointment id | yes (as tool results) | yes | yes | yes | counts only |
| D2 Customer PII | Name, phone, email, address, customer ID | **locator fields go to the lookup tool only; never in prompts beyond that** | **redacted** | **masked** ("the phone ending in 02"); never the full value | name and masked contact | **never** |
| D3 Secret | The one-time code | **never** | **never** | never (only the typed entry) | never | never |
| D4 Staff-only | Discretion notes, brief, flags, staff notes, reasons | brief only (it writes it) | redacted | **never** | yes | never |
| D5 Aggregates | Counts, rates, latencies, spend | n/a | yes | n/a | yes | yes (redacted by construction) |

The code (D3) appears in exactly two places: typed by the customer in a CON-2 `code` payload, and in the CON-6 demo inbox response. It is stored hashed.

**Access (decided 2026-10-21, R-48).** **One demo login gates the whole deployment** (chat, staff console, demo controls, monitoring and evaluation). Every route except `login` (CON-22) and `/healthz` answers `401 UNAUTHENTICATED` without a session. After login the session has a role (customer, representative, supervisor, owner) that anyone signed in can switch with no passcode (CON-10). A staff route called by a role that may not use it answers `403 ROLE_NOT_ALLOWED`. SCR-10 and SCR-11 are **no longer readable without sign-in**: the earlier proposal is reversed. The demo staff passcode and reset gating are closed by R-48: no passcode, and the login is the only gate (no separate cool-down).

## Contract map

| Screen | Contract | Operations |
|---|---|---|
| SCR-1 Customer chat | CON-1 | startChatSession, getChatThread |
| SCR-1 Customer chat | CON-2 | submitTurn |
| SCR-1 Customer chat | CON-3 | streamChatEvents |
| SCR-1 Customer chat | CON-4 | requestPerson |
| SCR-1 Customer chat | CON-5 | saveFollowUp |
| SCR-2 Demo delivery inbox | CON-6 | listDemoInbox |
| SCR-3 Demo guide and controls | CON-7, CON-8, CON-9 | getStaffing, setStaffing, getDemoClock, resetDemo |
| SCR-4 Staff role pick (now the role switch) | CON-10 (+ CON-7, CON-8 for the header) | listDemoRoles, switchRole, getSession |
| SCR-12 Demo login | CON-22 | login, logout |
| SCR-1 to SCR-11 shared header (role switcher) | CON-10 | getSession, listDemoRoles, switchRole |
| SCR-5 Representative queue | CON-11 (+ CON-13, CON-14 on claim and join) | getQueue |
| SCR-6 Case view | CON-12, CON-13, CON-14, CON-15, CON-16, CON-21 | getCase, applyCaseAction, liveChatAction, recordContactActivity, createFlag, streamCaseEvents |
| SCR-7 Supervisor oversight | CON-17 (+ CON-13, CON-7, CON-8) | getOversight, applyCaseAction, setStaffing, advanceDemoClock |
| SCR-8 Review list of flags | CON-16 | listFlags, reviewFlag |
| SCR-9 Business-owner outcomes | CON-18 | getOwnerMetrics |
| SCR-10 Monitoring | CON-19 | getMonitoring |
| SCR-11 Evaluation report | CON-20 | getLatestEval |

**Operations per contract:** CON-1 ×2 · CON-2 ×1 · CON-3 ×1 · CON-4 ×1 · CON-5 ×1 · CON-6 ×1 · CON-7 ×2 · CON-8 ×2 · CON-9 ×1 · CON-10 ×3 (listDemoRoles, switchRole, getSession) · CON-11 ×1 · CON-12 ×1 · CON-13 ×1 · CON-14 ×1 · CON-15 ×1 · CON-16 ×3 · CON-17 ×1 · CON-18 ×1 · CON-19 ×1 · CON-20 ×1 · **CON-21 ×1 (new)** · **CON-22 ×2 (new)** = 30.

**Why CON-21 exists (N-3).** The staff side of the live chat needs the customer's replies to arrive on SCR-6. CON-12 is a snapshot read, and CON-14 is write-only; stretching either to carry a long-lived stream would give one contract two shapes (a request and a stream) and two access stories. A separate stream keeps CON-3's format and replay rules and puts the staff role check in one place. DO-4 asked for the same (UXR-9).

## Named errors, and what each screen does

**Composed (HTTP 200, in `error` or `notice` blocks of CON-2, always with `settled`).**

| Code | Block | Screen response (SCR-1) |
|---|---|---|
| SLOT_TAKEN | `error` + fresh `slot_card` | "Sorry, that window just went. Here are the next open ones." Nothing booked |
| OUT_OF_AREA | `error` | "Sorry, that address is outside Meridian's service area, so I can't book a visit there." + Talk to a person |
| CODE_WRONG | `error` + `code_prompt` (wrong, `tries_left`) | Field marked invalid: "That code doesn't match. 2 tries left." |
| CODE_EXPIRED | `error` + `code_prompt` (expired, `resend_offered`) | "That code has expired. Codes last 10 minutes." + "Send a new code" while under the per-conversation cap of 3 (decided 2026-10-21) |
| CODE_LOCKED | `error` + `handoff` | Field disabled; "I can't confirm your account here. A representative will help." + handoff card |
| CODE_CAP_REACHED | `error` + `handoff` | Same sentence and card as CODE_LOCKED: the fourth code is refused |
| NOT_VERIFIED | `error` + `handoff` | **Identical for every cause** (no match, ambiguous, no contact): same sentence, same card, nothing that reveals whether an account exists |
| RATE_LIMITED | `notice` | "I can't take more messages in this chat right now." Field disabled; person key stays |
| BOOKING_CAP | `notice` | "I can't make more bookings in this chat." + person key |
| SPEND_CAP_REACHED | `notice` | "I can't answer more questions right now. A person can pick this up." Handoff-only mode; the person key (CON-4) opens the case. Safety and the person key still work |
| TURN_TIMEOUT | `notice` + top-level `notice.actions` | Code-built card: "This is taking longer than it should." with **Try again** (resends the same `turn_id`) and **Talk to a person** |
| BUSY | `notice` | Above 30 turns in flight: refused at once, no model call, "A lot of people are chatting right now, so I can't take this message. A person can pick it up." + person key (sentence agreed with DO-4, UXR-26) |
| AI_PAUSED | `notice` (`delivered_to_representative: true`) | A representative owns the chat; the message went to them. Not a failure: the screen shows "Riley is in this chat, so the assistant is paused." |

**HTTP errors (request could not be processed).**

| Code | Status | Where | Screen response |
|---|---|---|---|
| VALIDATION_ERROR | 400 | any request with a body or parameter | Field message on the card or form; names the field and the rule, never the value |
| REQUEST_RATE_LIMITED | 429 | read operations without a 4xx of their own (added to satisfy the lint rule and R-41 per-IP limits) | "Try again in a moment." Not the chat's RATE_LIMITED |
| SESSION_NOT_FOUND | 404 | CON-1, 2, 3, 4, 5 | Same as an unknown thread: offer "Start a new chat" |
| SESSION_ENDED | 410 | CON-1 (thread), 2, 4, 5 | "This chat has ended." composer disabled, "Start a new chat" |
| TURN_IN_PROGRESS | 409 | CON-2 | Keep "replying…"; retry after `retry_after_ms` with the same `turn_id` |
| RESET_IN_PROGRESS | 503 / 409 | most operations during CON-9's lock | "The demo is resetting. Try again in a few seconds." |
| RESET_FAILED | 500 | CON-9 | "The reset didn't finish. Nothing was half-reset; try again." |
| HANDOFF_FAILED | 503 | CON-4 | Error line with the person key still shown; tap again |
| UNAUTHENTICATED | 401 | **every operation except `login` and `/healthz`** | The page shows the login screen (SCR-12). `details.reason` is `none` or `expired` |
| LOGIN_FAILED | 401 | CON-22 `login` | One message for every cause: "That username or password didn't work." (never says which) |
| LOGIN_RATE_LIMITED | 429 | CON-22 `login` | "Too many attempts. Wait a moment and try again." (`Retry-After`) |
| ROLE_NOT_ALLOWED | 403 | any staff operation called by a role that may not use it (the customer role on any staff route, a representative assigning a case) | "This isn't available to the demo [role] role." Flags: "Supervisors mark flags reviewed." `details.reason` is `wrong_role` or `role_reset` (a demo reset sent the role back to customer). **Replaces UNAUTHENTICATED** for "signed in, wrong role" |
| CASE_NOT_FOUND / FLAG_NOT_FOUND | 404 | CON-12, 13, 14, 15, 16, 21 | "No case MHC-C-0099. It may have been cleared by a demo reset." + back to the queue |
| CASE_ALREADY_CLAIMED | 409 | CON-13, CON-14 | "Already claimed by [name] at [time]. Reload." |
| VERSION_CONFLICT | 409 | CON-13, CON-15 | "This case changed since you opened it ([who] at [time]). Reload to see it." (`details.changed_by`, `changed_at`, `current_version`) |
| NOT_ALLOWED_IN_STATE | 409 | CON-5, 13, 15 | "Claim the case first." / no open case |
| REASON_REQUIRED, WAKE_UP_REQUIRED, OUTCOME_REQUIRED | 422 | CON-13 | "Add a reason to release this case." / "Waiting needs a wake-up time." / "Resolving needs an outcome." |
| NOT_LIVE | 409 | CON-14 | "This chat ended" (including "because the demo was reset") |
| NOT_CLAIMED_BY_YOU | 403 | CON-14 | "Claim the case first." |

Names from the screen specs and DO-4 that were **renamed to the decided list**: CONFLICT_STALE → VERSION_CONFLICT; ALREADY_CLAIMED → CASE_ALREADY_CLAIMED; SPEND_CAP → SPEND_CAP_REACHED; VALIDATION_FAILED → VALIDATION_ERROR; STAFF_SESSION_REQUIRED, SESSION_RESET and UNAUTHENTICATED are gone: "not signed in" is UNAUTHENTICATED (401) and "wrong role" is ROLE_NOT_ALLOWED (403).

---

### CON-1 · Start a conversation, or resume one after a reload
- Screens: SCR-1 Chat · Flows: FLOW-1, FLOW-12
- Requirements: R-1, R-3, R-30, R-40 · Stories: US-1, US-25
- Operations (operationId): `startChatSession` (POST /api/chat/sessions), `getChatThread` (GET /api/chat/sessions/{thread_id})
- Reads: thread id; the greeting as a `text` block (fixed text, no model); demo clock (`now`, `label`, `date_label`); staffing (`mode`, `label`, `banner`); controller (`ai`); empty `settled`; the CON-3 address and `last_event_id`; the timing constants the UI uses (`turn_deadline_ms` 60000, `still_working_after_ms` 10000, `browser_give_up_after_ms` 65000 [A], `max_message_chars` 2000). `getChatThread` adds the turns so far, `state` (open, closed, ended_by_reset) and `settled`.
- Writes: creates the thread, owned by the login session.
- States the UI must be able to show: greeting in default state (nobody online) · simulated staffing on (banner) · resumed thread · ended thread (a `session_ended` block in the list, or 410 on a turn).
- Errors (code → screen response): RESET_IN_PROGRESS → try again shortly; SESSION_NOT_FOUND / SESSION_ENDED on resume → "Start a new chat"; REQUEST_RATE_LIMITED.
- Guarantees: the greeting always says it is an automated assistant, never claims to be human (R-1). The demo date and staffing come from the contract, never the browser clock or the server clock.
- Timing budget: p95 ≤ 500 ms [A] (no model).
- Data class and where it may go: D0 and D1. No PII. The transcript has codes redacted and never carries tool output.
- Access: any signed-in role; a thread is readable only by the login session that owns it (`mhc_session`).
- Mock examples: STARTED, SIMULATION_ON; OPEN, ENDED_BLOCK; errors SESSION_NOT_FOUND, SESSION_ENDED, RESET_IN_PROGRESS.
- Status: specified (UX-3, proposal)

### CON-2 · One turn: a message, a card key, a code or a form
- Screens: SCR-1 Chat · Flows: FLOW-1, FLOW-2, FLOW-3, FLOW-4, FLOW-5, FLOW-6, FLOW-7
- Requirements: R-1, R-2, R-4, R-5, R-6, R-7, R-8, R-13, R-14, R-15, R-16, R-17, R-18, R-19, R-20, R-21, R-22, R-23, R-26, R-27, R-41, R-44, R-45, R-46, R-47
- Operations (operationId): `submitTurn` (POST /api/chat/sessions/{thread_id}/turns)
- Reads: **the reply is a typed list of blocks** (a discriminated union on `type`), each with a speaker and a time:

  | `type` | What it is |
  |---|---|
  | `text` | Answer text with `sources[]` (file, section, `version_date` or null, `version_label`, quoted passage). **`version_label` is the version as the file states it** ("Rev 2026-01", "2026 (image)", "undated"); a date is never invented (UXR-24) |
  | `source_chip` | A stand-alone "Where this comes from" chip |
  | `safety` | The safety card: fixed Meridian text, no model, P0 case written by code, pinned |
  | `conditional_safety` | Burning smell with unclear risk (WARNING), emergency line, P1 case |
  | `burning_check` | The R-7 question with Yes / No / Not sure |
  | `emergency_line` | Someone in danger from no heat, no cooling or a leak (R-8): number first, separate 1-business-day line only when nobody is online |
  | `quick_checks` | The optional quick-checks offer (Skip and book / Show the checks) |
  | `urgency_questions` | Three skippable urgency questions |
  | `where_prompt` | ZIP code or city |
  | `locate_prompt` | Name + phone, or customer ID, or invoice number |
  | `code_prompt` | States `sent`, `wrong` (`tries_left`), `expired` (`resend_offered`, `resends_left`, cap of 3 per conversation, decided 2026-10-21), `locked`. **Masked hint only, never the code** |
  | `slot_card` | Arrival windows by day, the standard fee, "Windows are shown, not held.", `urgent`, member-only windows after the code |
  | `account_card` | Invoice (lines as billed, no verdict), membership (tier, renewal date), warranty (install date, sentence) |
  | `confirmation` | Booked visit: date, window, technician, fee line, timeline |
  | `appointment` | An existing visit ("Your booked visit") |
  | `cancelled` | A fee-free cancellation, "There's no fee." |
  | `change_request` | Fee-bearing move or cancel: fee line, "original stays" line, wanted time, windows shown (not held), reference, promise, due time (null when staff are on shift), can't-guarantee line |
  | `handoff` | Reference, exact promise text, due time (**null for the staffed promise**, "when available"; UXR-25), follow-up chooser |
  | `live_queued` | Staffed promise text and reference |
  | `failure_offer` | "It sounds like I'm not getting this right. Would you like a person?" |
  | `no_info` | "I don't have that information." + person key |
  | `notice` | The limit, timeout, busy or paused sentence + person key |
  | `error` | A named composed error (table above), with `fresh_windows` for SLOT_TAKEN |
  | `session_ended` | "This chat has ended." + "Start a new chat" |

  Plus `settled`, `writes[]`, `controller`, `notice`, `last_event_id`, `sequence`.
  **`settled`** drives the C2 "What's settled" panel: `visit` (appointment, window, technician, fee line, status booked / moved / original_stays, any pending change request), `request` (reference, promise text, due time and its label, extra lines, live-queued, follow-up), `identity` (status, masked hint), `replying` (ai or human, name) and `actions[]`. **It is built from conversation state, meaning every completed write in the conversation, not from the last turn alone** (N-27, R-45, R-46). **`settled.visit` is the visit this conversation wrote or changed most recently** (UXR-21); with more than one (the booking cap is 3), every other visit stays visible in `settled.actions[]`. Example: a move done in turn 3 is still in `settled` in turn 4 ("Yes, please."), so the card and the words cannot say it was not done.
  **`writes[]`** lists this turn's completed writes (booked, moved, cancelled, change_request_sent, case_opened, followup_saved, verified). One turn can hold two. **Completion wording ("booked", "cancelled", "moved") is allowed only for a kind that appears in `writes[]` or `settled.actions`**; the R-46 check enforces it and the screen may not add such wording itself.
  **Promise text and reference are produced by code** (R-46, R-26). Each block that carries them has `produced_by_code: true`. The promise arrives as `promise_text` (the policy-table sentence), `due_label` and `extra_lines`; the screen joins them as "{promise_text}, {due_label}. {extra_lines}" (UXR-19). The words of the fixed texts (safety, promise, fee lines, limit sentences) are copied from SCREEN_SPECS's copy notes word for word.
- Writes: request body `{turn_id, payload}`. `turn_id` is a UUID minted by the browser and reused unchanged by Try again. `payload` is one of: `text` (1–2,000 characters), `choice` (`card_id`, `option`: a slot pick, Yes / No / Not sure, Skip, Show the checks, Send a new code), `code` (`card_id`, six digits) or `form` (`card_id`, `values`: name, phone, customer_id, invoice_number, zip_or_city). **Card choices go back through this same operation as a structured `choice`**, routed by code to the open task. (`form` is a fourth kind DO-4 did not list: locator fields and a ZIP are not an option value.)
- States the UI must be able to show: every SCR-1 state in SCREEN_SPECS: greeting, answered with source, partial (blocks answered and "I don't have that information."), safety takeover (pinned), burning-smell question, conditional card, emergency line, quick checks, urgency questions, where card, slots, locate card, code sent / wrong / expired / locked, verified, account answer, booked, appointment, cancelled, change request, handoff, live-queued, failure offer, limit, spend cap, timeout, busy, paused, ended.
- Errors (code → screen response): the composed table above (SLOT_TAKEN, OUT_OF_AREA, CODE_WRONG, CODE_EXPIRED, CODE_LOCKED, CODE_CAP_REACHED, NOT_VERIFIED, RATE_LIMITED, BOOKING_CAP, SPEND_CAP_REACHED, TURN_TIMEOUT, BUSY, AI_PAUSED) as HTTP 200; and VALIDATION_ERROR (400), SESSION_NOT_FOUND (404), TURN_IN_PROGRESS (409), SESSION_ENDED (410), RESET_IN_PROGRESS (503).
- Guarantees:
  - **Deadline 60 s from server receipt**, then a code-built `TURN_TIMEOUT` reply (Try again and Talk to a person). **The browser gives up at deadline + 5 s = 65 s (decided 2026-10-21)** and shows "That didn't send. Your message is still here."
  - **`BUSY` above 30 turns in flight**: refused at once, no model call, person offer.
  - **No streaming and no progress events.** The reply arrives whole, because the R-46 checks need the full text. The UI shows "replying…" at 300 ms and "Still working on this…" at about 10 s.
  - **Idempotent per `turn_id`**: a finished turn returns the stored reply unchanged; a failed or timed-out one re-runs, and any committed write is found by its idempotency key, not repeated. Two timeouts in one conversation count as a failure signal (the next reply offers a person).
  - The safety rules run first on every turn and never wait on the model. Safety, "Talk to a person" and handoff are never refused for limits.
  - `NOT_VERIFIED` is identical for every cause. The code never reaches the model, logs or traces.
  - A booking re-reads the slot inside its transaction; "shown, not held".
- Timing budget: **target p95 ≤ 12.5 s** (measured 10.2 s at 20 chats at once in SP-1) · hard deadline 60 s · safety turns need no model, p95 ≤ 500 ms [A].
- Data class and where it may go: D0 and D1 in replies; D2 only as masked hints; **D3: `payload.code` is compared by code against the stored hash and never reaches the model, logs or traces**; locator fields go to the lookup tool only; customer text is redacted before any model call; traces redacted.
- Access: any signed-in role (`mhc_session`); the thread must be this login session's.
- Mock examples: 37 named responses (adds HANDOFF_STAFFED: no due time) covering every block type and every composed error (ANSWER_WITH_SOURCE, SAFETY, CONDITIONAL_SAFETY, BURNING_CHECK, EMERGENCY_LINE, NO_INFO, QUICK_CHECKS, URGENCY_QUESTIONS, WHERE_PROMPT, SLOT_CARD, SLOT_CARD_MEMBER, LOCATE_PROMPT, CODE_SENT, VERIFIED_ACCOUNT_INVOICE, ACCOUNT_MEMBERSHIP, ACCOUNT_WARRANTY, BOOKED, APPOINTMENT, CANCELLED, CHANGE_REQUEST, HANDOFF, LIVE_QUEUED, FAILURE_OFFER, then SLOT_TAKEN, OUT_OF_AREA, CODE_WRONG, CODE_EXPIRED, CODE_LOCKED, CODE_CAP_REACHED, NOT_VERIFIED, RATE_LIMITED, BOOKING_CAP, SPEND_CAP_REACHED, TURN_TIMEOUT, BUSY, AI_PAUSED); five request examples (TEXT, CHOICE_SLOT, CODE, FORM_LOCATE, FORM_WHERE); errors VALIDATION_ERROR, SESSION_NOT_FOUND, TURN_IN_PROGRESS, SESSION_ENDED, RESET_IN_PROGRESS. Select one with `Prefer: code=200, example=SLOT_TAKEN`.
- Status: specified (UX-3, proposal)

### CON-3 · Live events for one chat (SSE, with replay)
- Screens: SCR-1 Chat · Flows: FLOW-8, FLOW-12
- Requirements: R-3, R-30, R-31, R-33
- Operations (operationId): `streamChatEvents` (GET /api/chat/sessions/{thread_id}/events, `text/event-stream`)
- Reads: a stream. **Open on every chat session**, not only a live handoff, so the demo bar and banner update when the reviewer changes staffing or the clock in another tab. Each frame has `id: <int>`, `event: <type>` and `data: <JSON>`. Events: `representative_joined`, `staff_message`, `ai_paused`, `ai_resumed`, `chat_closed`, `staffing_changed`, `shift_ended` (carries the async promise and the **same reference**, and a new `settled`), `clock_changed` (the chat's date follows the demo clock), `demo_reset`. A heartbeat comment every 15 s (decided 2026-10-21). No progress events.
- Writes: none. Reconnect with the `Last-Event-ID` header: missed events replay in order (N-2).
- States the UI must be able to show: joined / paused / staff messages / handed back / closed event lines and the top bar; staffing banner on and off; "Reconnecting… Staffing and messages may be out of date." and its clearing after replay; shift ended before a claim; demo reset ended the chat; the date chip moving.
- Errors (code → screen response): SESSION_NOT_FOUND (404) → start a new chat. After `chat_closed` or `demo_reset` the server closes the stream.
- Guarantees: ordered, replayable by event id; async, so an open stream holds no worker thread. Names follow the decided list; the earlier drafts' `representative_message` is `staff_message` and `handed_back` is `ai_resumed`.
- Timing budget: first event within 1 s of a change [A].
- Data class and where it may go: D0/D1; staff messages are real text typed by the demo representative; D2 masked only; no codes.
- Access: any signed-in role (`mhc_session`); the thread must be this login session's.
- Mock examples: FRAMES (a representative joins, the AI pauses, Riley writes); error SESSION_NOT_FOUND.
- Status: specified (UX-3, proposal)

### CON-4 · "Talk to a person"
- Screens: SCR-1 Chat · Flows: FLOW-7, FLOW-8
- Requirements: R-2, R-24, R-25, R-26, R-30, R-41
- Operations (operationId): `requestPerson` (POST /api/chat/sessions/{thread_id}/handoff)
- Reads: `result` (`case_created`, `live_queued`, `already_open`), a `handoff` or `live_queued` block, `settled`.
- Writes: `{turn_id}` (the press is logged as a turn). Creates the case with its priority and promise from the policy table.
- States the UI must be able to show: handoff card (reference, promise, due, follow-up chooser) · live-queued card · second tap scrolls to the existing card ("Your request" highlights).
- Errors (code → screen response): HANDOFF_FAILED (503) → error line, person key still shown, tap again; SESSION_NOT_FOUND; SESSION_ENDED; VALIDATION_ERROR.
- Guarantees: **works during RATE_LIMITED, SPEND_CAP_REACHED and BUSY** (no model, never limited), so "Talk to a person" is never disabled. **Idempotent**: a second tap returns `already_open` with the same reference and creates no second case. Reference and promise are produced by code.
- Timing budget: p95 ≤ 1 s [A] (no model). A case write that fails is retried once.
- Data class and where it may go: D1; no PII in the request or the card; the brief is written off the critical path (D4).
- Access: any signed-in role (`mhc_session`); the thread must be this login session's.
- Mock examples: CASE_CREATED, LIVE_QUEUED, ALREADY_OPEN; errors HANDOFF_FAILED, SESSION_NOT_FOUND, SESSION_ENDED, VALIDATION_ERROR.
- Status: specified (UX-3, proposal)

### CON-5 · Save the follow-up choice
- Screens: SCR-1 Chat · Flows: FLOW-7
- Requirements: R-27, R-34
- Operations (operationId): `saveFollowUp` (PUT /api/chat/sessions/{thread_id}/follow-up)
- Reads: the saved follow-up (`channel`, `destination_label` such as "the number ending in 02", `on_record`, `window`, `saved_line`) and `settled`. The chooser's options (channels with masked labels and an `on_record` flag, windows, `general_only`) arrive inside the `handoff` block.
- Writes: `channel` (email, phone), `destination` (`on_record` or `general`), `window` (`morning`, `afternoon`, `any`).
- States the UI must be able to show: chooser open with the promise and reference already shown (partial) · "Follow-up saved: phone call, the number ending in 02, mornings." · general-only chooser for an unverified customer.
- Errors (code → screen response): NOT_ALLOWED_IN_STATE (409, no open case) → "There's no open request to attach this to."; SESSION_NOT_FOUND; SESSION_ENDED; VALIDATION_ERROR.
- Guarantees: an unverified customer can save `general` only; private details go only to a destination on record after verification. **Nothing in any response says a message was sent** (R-34).
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: D2 masked in every response; the full destination stays on the record and is never shown or sent to the model.
- Access: any signed-in role (`mhc_session`); the thread must be this login session's.
- Mock examples: PHONE_MORNINGS (request and response), EMAIL_GENERAL (request); errors NOT_ALLOWED_IN_STATE, SESSION_NOT_FOUND, SESSION_ENDED, VALIDATION_ERROR.
- Status: specified (UX-3, proposal)

### CON-6 · Demo inbox: the simulated code messages
- Screens: SCR-2 Inbox (and the code card's link to it) · Flows: FLOW-3, FLOW-12
- Requirements: R-15, R-34 · Stories: US-8, US-25
- Operations (operationId): `listDemoInbox` (GET /api/demo/inbox) · **demo only** (`x-demo-only: true`, tag `demo-only`)
- Reads: messages newest first: `id`, `at`, `to_masked` ("···02"), `body`, `code`, `status` (active, used, expired), `expires_at`.
- Writes: none.
- States the UI must be able to show: newest code · no codes yet · used and expired rows (copy disabled) · a new code arriving (list refreshes every 5 s while visible).
- Errors (code → screen response): RESET_IN_PROGRESS (503) → "The inbox didn't load. Try again."; REQUEST_RATE_LIMITED. An empty list is normal.
- Guarantees: **scoped to the login session** (`mhc_session`): the chat tab and the inbox tab share it, and two reviewers logged in separately never see each other's codes. Codes only, never follow-ups. Nothing is sent to anyone.
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: **D3. This is the only response that carries a code.** It never reaches the model, logs or traces. Masked recipient only; stored hashed.
- Access: any signed-in role; only this login session's codes.
- Mock examples: ONE_ACTIVE, EMPTY, USED_AND_EXPIRED; errors RESET_IN_PROGRESS, REQUEST_RATE_LIMITED.
- Status: specified (UX-3, proposal)

### CON-7 · Simulated staffing
- Screens: SCR-3 Demo guide, SCR-7 Oversight (and the header of SCR-4 to SCR-9) · Flows: FLOW-8, FLOW-10, FLOW-12
- Requirements: R-30, R-31
- Operations (operationId): `getStaffing` (GET), `setStaffing` (PUT) at /api/demo/staffing · **demo only**
- Reads: `mode` (nobody_online, simulated_on_shift), `label`, `banner` ("Simulated staffing (demo). No Meridian employee is online."). `setStaffing` adds `converted_cases`: the live-queued cases that took the async promise because the shift ended.
- Writes: `{mode}`.
- States the UI must be able to show: "Nobody online" (default) · on, with banner · "Shift ended. 1 waiting customer now has the 1-business-day promise." · "Checking…" while pending.
- Errors (code → screen response): VALIDATION_ERROR; RESET_IN_PROGRESS; "Staffing didn't change. Try again." for any failure.
- Guarantees: **default is nobody online.** Idempotent. Turning it off converts every live-queued case (same reference, same creation time) and emits `shift_ended` to each affected chat and `staffing_changed` to all open chats. Never implies a real employee is online.
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: D0; no PII.
- Access: any signed-in role (R-48); no separate cool-down; the supervisor repeats the switch on SCR-7.
- Mock examples: OFF, ON (read); TURNED_ON, TURNED_OFF_WITH_WAITING (write); errors VALIDATION_ERROR, RESET_IN_PROGRESS.
- Status: specified (UX-3, proposal)

### CON-8 · The demo clock
- Screens: SCR-3, SCR-7, and the demo bar of SCR-1 and the console header · Flows: FLOW-10
- Requirements: R-3, R-33
- Operations (operationId): `getDemoClock` (GET), `advanceDemoClock` (POST) at /api/demo/clock · **demo only**
- Reads: `now`, `label`, `date_label`. `advanceDemoClock` adds `became_overdue` (how many cases turned overdue).
- Writes: `{step}`: `plus_1h`, `plus_4h`, `next_business_morning` (Mon 7:00 am).
- States the UI must be able to show: "Fri Oct 16, 2026 (demo date)" · "Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue." · no back key ("To go back to Fri Oct 16, reset the demo.").
- Errors (code → screen response): VALIDATION_ERROR (any other step); UNAUTHENTICATED, ROLE_NOT_ALLOWED (supervisor only) → "The clock didn't move. Try again."
- Guarantees: **one demo clock for everything. Decided (Innocent, 2026-10-21): the chat's "today" follows the demo clock.** Advancing it moves the chat's date and relative dates through the CON-3 `clock_changed` event. It starts at Fri 2026-10-16, moves only when advanced, **never the server clock**, and never backwards: reset (CON-9) returns to Fri 2026-10-16. Due states recompute at once. (This closes SCREEN_SPECS note 6; the earlier `unknown` is resolved.)
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: D0; no PII.
- Access: read by any browser; advance by the demo supervisor only.
- Mock examples: START, ADVANCED (read); NEXT_MORNING, PLUS_1H (advance); errors VALIDATION_ERROR, UNAUTHENTICATED, ROLE_NOT_ALLOWED.
- Status: specified (UX-3, proposal)

### CON-9 · Reset the demo
- Screens: SCR-3 Demo guide · Flows: FLOW-12
- Requirements: R-19, R-33, R-40 · Stories: US-25, US-26
- Operations (operationId): `resetDemo` (POST /api/demo/reset) · **demo only**
- Reads: `ok`, `open_chats_ended`, `staff_sessions_invalidated`, `clock` (back to Fri 2026-10-16).
- Writes: `{confirm: true}` (the screen's dialog supplies it).
- States the UI must be able to show: "Demo reset. Bookings, cases and codes are back to the start, and the date is Fri Oct 16, 2026. Open chats have ended." · "Resetting…" · "The reset didn't finish. Nothing was half-reset; try again."
- Errors (code → screen response): RESET_FAILED (500) → the message above; RESET_IN_PROGRESS (409) → "Resetting…" stays; VALIDATION_ERROR.
- Guarantees: **all-or-nothing** under an exclusive lock (turns in flight wait up to 5 s [A]); nothing is half-reset. It restores the working DB copy, cases, seeded cases, codes and the clock. **Open chats end** (`demo_reset` event; SESSION_ENDED on later calls). **Every session's role goes back to customer** (ROLE_NOT_ALLOWED, `details.reason: role_reset`, on the next staff call); the login itself stays, so nobody has to log in again.
- Timing budget: p95 ≤ 10 s [A].
- Data class and where it may go: D0; no PII. Everything the demo created is cleared.
- Access: any signed-in role (decided, R-48: the login is the gate; no separate cool-down). A per-IP throttle stays as a safety net [A].
- Mock examples: RESET; errors RESET_IN_PROGRESS, RESET_FAILED, VALIDATION_ERROR.
- Status: specified (UX-3, proposal)

### CON-10 · Role switch for a signed-in session (customer · representative · supervisor · owner)
- Screens: SCR-1, SCR-2, SCR-3, SCR-4, SCR-5, SCR-6, SCR-7, SCR-8, SCR-9, SCR-10, SCR-11 (the switcher lives in the shared header of every one of them; SCR-4 is the full role pick) · Flows: FLOW-8, FLOW-9, FLOW-10, FLOW-11, FLOW-12
- Requirements: R-31, R-32, R-48 (the demo login)
- Operations (operationId): `listDemoRoles` (GET /api/session/roles), `switchRole` (PUT /api/session/role), `getSession` (GET /api/session). **What changed:** the old staff sign-in operations are gone. `createStaffSession` is now `switchRole`, `getStaffSession` is now `getSession`, `listStaffRoles` is now `listDemoRoles` (and lists four roles, customer included), and `endStaffSession` is gone: logging out is CON-22 `logout`.
- Reads: the four roles with display names and what each sees ("Customer (demo)", "Riley, demo representative", "Demo supervisor", "Demo business owner"); the current session and its role.
- Writes: `{role}` on the same `mhc_session`. **No passcode.** One click from any screen.
- States the UI must be able to show: the switcher with the current role · "Switching…" · the new role's chrome · after a demo reset, "The demo was reset, so you're back to the customer role. Pick a role again." (ROLE_NOT_ALLOWED, `details.reason: role_reset`).
- Errors (code → screen response): UNAUTHENTICATED (401) → SCR-12; VALIDATION_ERROR (400); RESET_IN_PROGRESS (503).
- Guarantees: a role switch changes only the current role on the session; it does not change thread ownership or the inbox scope, and it does not end the chat. Chat routes ignore the role; staff routes require one (customer on a staff route is ROLE_NOT_ALLOWED). The role is a label for the reviewer, not security: **the login (CON-22) is the gate.** Every role name contains "demo".
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: no PII; roles are demo labels.
- Access: any signed-in role.
- Mock examples: ROLES; CUSTOMER, REPRESENTATIVE (getSession); TO_REPRESENTATIVE, TO_SUPERVISOR, TO_OWNER, TO_CUSTOMER (switchRole); errors UNAUTHENTICATED (both reasons), VALIDATION_ERROR, RESET_IN_PROGRESS.
- Status: specified (UX-3, proposal)

### CON-11 · The representative queue
- Screens: SCR-5 Queue (and the compact list in SCR-6) · Flows: FLOW-7, FLOW-8, FLOW-9, FLOW-12
- Requirements: R-25, R-30, R-32, R-33 · Stories: US-18, US-20
- Operations (operationId): `getQueue` (GET /api/staff/queue)
- Reads: `staffing`; `live` (only while staffed: oldest first, P0 and P1 on top, `queued_at`, never a wait estimate); `needs_my_action` (P0 and P1 first, then due time, overdue first). Each row: priority and word, reference, reason, customer display name, owner, `created_at`, `due_at`, `due_label`, `due_state` (on_time, due_soon, overdue, no_due_time), `wake_up_at`, lifecycle, follow-up short form, `seed`, `brief_status`, `age_label`.
- Writes: none (claiming is CON-13, joining is CON-14).
- States the UI must be able to show: seeded rows · all caught up · "Brief being written" · live-queue rows when staffed · no live queue when nobody is online · Overdue after the clock moves · "2 cases changed" (list refreshes every 10 s).
- Errors (code → screen response): UNAUTHENTICATED → SCR-12; ROLE_NOT_ALLOWED.
- Guarantees: ordering is done by the backend; a P0 row has `no_due_time`; "Overdue" is a state, never a negative countdown.
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: D1 and D2 (display name only, no phone, email or address); staff UI only.
- Access: demo representative and supervisor.
- Mock examples: SEEDED, STAFFED_WITH_WAITING, ALL_CAUGHT_UP, BRIEF_BEING_WRITTEN; errors UNAUTHENTICATED, ROLE_NOT_ALLOWED.
- Status: specified (UX-3, proposal)

### CON-12 · Case view: brief, sources, conversation, promise
- Screens: SCR-6 Case view (and the destination of SCR-5, SCR-7, SCR-8, SCR-9) · Flows: FLOW-9, FLOW-10, FLOW-11
- Requirements: R-28, R-29, R-30, R-33, R-34, R-37 · Stories: US-19, US-21
- Operations (operationId): `getCase` (GET /api/staff/cases/{reference})
- Reads: **brief status and eight fixed headings** (facts and claims apart; stop 4 "NOT CHECKED"; a heading the fact check trimmed carries `trimmed` and its note; an empty heading reads "Nothing recorded."); **per-source snapshot vs current with `changed_since`** and `current_unavailable`, each with `version_date` (nullable) and `version_label` (UXR-24); the promise record (exact text, policy row, due time, status open / kept / missed / changed, history, follow-up beside it); identity status; the conversation (codes redacted); activities; live state; other cases for the customer; **`allowed_actions` per lifecycle state and role**; `version`; **seed flag**; **`as_of`**; **the agent version**.
- Writes: none.
- States the UI must be able to show: unassigned case with Claim · brief being written · source unreadable ("the snapshot is shown alone") · trimmed stop · changed-since marker · P0 "No due time: safety" · live joined · waiting with wake-up · fee-bearing change request (due at the window start) · seeded case · case not found · role not allowed.
- Errors (code → screen response): CASE_NOT_FOUND (404) → "No case MHC-C-0099. It may have been cleared by a demo reset."; ROLE_NOT_ALLOWED (403, the customer role only; owner and the staff roles read); UNAUTHENTICATED (401).
- Guarantees: the snapshot is what the AI saw; the current value is re-read now; the screen needs no client-side rules to disable keys. The owner role may read cases (FLOW-11 opens them from a metric) but has no actions. **Settled from the sources (orchestrator, 2026-10-21, proposal):** every demo staff role, owner included, may **read** any case (FLOW-11; consolidated §6 "Open the cases behind any number"); the owner gets the case **read-only**, with `allowed_actions: []`. No role is refused a read, so CON-12 never returns ROLE_NOT_ALLOWED; that error stays for actions (CON-13/14/15, flags).
- Timing budget: p95 ≤ 800 ms [A].
- Data class and where it may go: D4 and D2 (name, masked contact); **staff-only sources (the agent discretion notes) appear only here, with `audience: staff_only`, never in any customer response**; traces redacted; brief text is never copied back into a customer reply.
- Access: demo representative, supervisor, owner (read only).
- Mock examples: DEFAULT, BRIEF_BEING_WRITTEN, TRIMMED_STOP, SAFETY_CASE, LIVE_JOINED, WAITING, FEE_BEARING_CHANGE; errors CASE_NOT_FOUND, ROLE_NOT_ALLOWED, UNAUTHENTICATED.
- Status: specified (UX-3, proposal)

### CON-13 · Change a case: claim, release, wait, resolve, close, assign, change priority
- Screens: SCR-6 Case view, SCR-7 Oversight (also SCR-5 on "Claim and join") · Flows: FLOW-8, FLOW-9, FLOW-10
- Requirements: R-25, R-31, R-32, R-33 · Stories: US-18, US-20, US-21, US-22
- Operations (operationId): `applyCaseAction` (POST /api/staff/cases/{reference}/actions)
- Reads: the updated `case` summary (lifecycle, owner, priority, due, `promise_status`, new `version`, `allowed_actions`) and a result line.
- Writes: `{action, expected_version, reason?, wake_up_at?, outcome?, assignee?, priority?}`. Actions: claim, release (reason), start, wait (wake-up time), resolve (outcome), close_unresolved (reason), assign (reason), change_priority (reason).
- States the UI must be able to show: "Claimed · Riley (demo)" · waiting with a wake-up time · resolved (promise Kept, or Missed if past due) · released back to Unassigned · assigned · priority changed with its reason.
- Errors (code → screen response): VERSION_CONFLICT (409) → "This case changed since you opened it ([who] at [time]). Reload."; CASE_ALREADY_CLAIMED (409); NOT_ALLOWED_IN_STATE (409); REASON_REQUIRED, WAKE_UP_REQUIRED, OUTCOME_REQUIRED (422); ROLE_NOT_ALLOWED (403); CASE_NOT_FOUND; UNAUTHENTICATED; VALIDATION_ERROR.
- Guarantees: **`expected_version` is required** and a stale one gives 409 VERSION_CONFLICT with `changed_by`, `changed_at`, `current_version`. No open-ended waiting. Reasons are logged. Resolving after the due time marks the promise Missed.
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: D4 (reasons and outcomes are staff free text); staff only.
- Access: representative (claim, release, start, wait, resolve, close); supervisor (all, including assign and change_priority).
- Mock examples: CLAIMED, WAITING, RESOLVED, ASSIGNED, PRIORITY_CHANGED (responses); CLAIM, WAIT, RESOLVE, RELEASE, ASSIGN, CHANGE_PRIORITY (requests); errors VERSION_CONFLICT, CASE_ALREADY_CLAIMED, NOT_ALLOWED_IN_STATE, REASON_REQUIRED, WAKE_UP_REQUIRED, OUTCOME_REQUIRED, ROLE_NOT_ALLOWED, CASE_NOT_FOUND, UNAUTHENTICATED, VALIDATION_ERROR.
- Status: specified (UX-3, proposal)

### CON-14 · Live chat: join, reply, hand back, close
- Screens: SCR-6 Case view · Flows: FLOW-8
- Requirements: R-30, R-31, R-33 · Stories: US-15, US-20
- Operations (operationId): `liveChatAction` (POST /api/staff/cases/{reference}/live)
- Reads: the new controller, live state (not_live, queued, joined, handed_back, closed) and, for `send`, the stored message.
- Writes: `{action: join | send | hand_back | close, text?}`. A message is written into the **same thread** as the customer's chat.
- States the UI must be able to show: joined, AI paused, live box open · message sent · handed back (live box disabled) · chat closed (next keys Resolve and Close unresolved) · "This chat ended because the demo was reset."
- Errors (code → screen response): NOT_LIVE (409); NOT_CLAIMED_BY_YOU (403); CASE_ALREADY_CLAIMED (409); CASE_NOT_FOUND; UNAUTHENTICATED; VALIDATION_ERROR.
- Guarantees: `join` needs a case you claimed and a customer waiting while simulated staff are on shift. It sets the controller to human and emits `representative_joined` and `ai_paused` on the customer's CON-3. `hand_back` emits `ai_resumed`; `close` emits `chat_closed`. What the reviewer types as Riley is sent for real into the same conversation (only the staffing is simulated).
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: the typed message is D0-like free text that goes to the customer; staff only until sent; logs redacted.
- Access: demo representative.
- Mock examples: JOINED, SENT, HANDED_BACK, CLOSED; requests JOIN, SEND, HAND_BACK, CLOSE; errors NOT_LIVE, CASE_ALREADY_CLAIMED, NOT_CLAIMED_BY_YOU, CASE_NOT_FOUND, UNAUTHENTICATED, VALIDATION_ERROR.
- Status: specified (UX-3, proposal)

### CON-15 · Record a contact attempt (recorded, not sent)
- Screens: SCR-6 Case view · Flows: FLOW-9
- Requirements: R-34 · Stories: US-14, US-21
- Operations (operationId): `recordContactActivity` (POST /api/staff/cases/{reference}/activities)
- Reads: the stored activity (kind, outcome, note, time, by) and the case summary. **Every activity carries the fixed label "Demo: recorded, not sent".**
- Writes: `{kind: call | email, outcome: reached | no_answer | left_message, note?, expected_version}`.
- States the UI must be able to show: "Called ···02 · Reached the customer · Demo: recorded, not sent" · key disabled until the case is claimed.
- Errors (code → screen response): NOT_ALLOWED_IN_STATE (409) → "Claim the case first."; VERSION_CONFLICT (409); ROLE_NOT_ALLOWED; CASE_NOT_FOUND; UNAUTHENTICATED; VALIDATION_ERROR.
- Guarantees: **no call is placed and nothing is sent**; no response says otherwise (R-34).
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: D4 (staff note); staff only.
- Access: demo representative.
- Mock examples: CALL_REACHED, EMAIL_LEFT_MESSAGE; request CALL; errors NOT_ALLOWED_IN_STATE, VERSION_CONFLICT, ROLE_NOT_ALLOWED, CASE_NOT_FOUND, UNAUTHENTICATED, VALIDATION_ERROR.
- Status: specified (UX-3, proposal)

### CON-16 · Flags and the review list
- Screens: SCR-6 Case view (flag), SCR-8 Review list · Flows: FLOW-9, FLOW-10
- Requirements: R-37 · Stories: US-21, US-23
- Operations (operationId): `createFlag` (POST /api/staff/flags), `listFlags` (GET /api/staff/flags), `reviewFlag` (**PATCH** /api/staff/flags/{flag_id})
- Reads: flags newest first: target (answer, brief, escalation), reason, case reference, message id, note, flagged by, time, status (new, reviewed), reviewer and note.
- Writes: `createFlag` `{case_ref, target, message_id?, reason?, note?}` (`reason` is a free-text staff note, D4, UXR-22; the review list and `Flag.reason` show it, null when left blank); `reviewFlag` `{status: "reviewed", note?}`.
- States the UI must be able to show: "Added to the review list." · flags listed · "No flags yet…" · "Marked reviewed." · "Supervisors mark flags reviewed." for the representative.
- Errors (code → screen response): ROLE_NOT_ALLOWED (403) on review for a representative; FLAG_NOT_FOUND, CASE_NOT_FOUND (404); UNAUTHENTICATED; VALIDATION_ERROR.
- Guarantees: **nothing here changes the knowledge base, prompts or eval set automatically**; people decide each fix (R-37).
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: D4 (notes and the flagged message text); staff only.
- Access: demo representative and supervisor create; supervisor marks reviewed; owner can list.
- Mock examples: ANSWER (create), THREE and EMPTY (list), REVIEWED (patch); errors as above.
- Status: specified (UX-3, proposal)

### CON-17 · Supervisor oversight
- Screens: SCR-7 Oversight · Flows: FLOW-8, FLOW-10
- Requirements: R-30, R-32, R-33 · Stories: US-22, US-23
- Operations (operationId): `getOversight` (GET /api/staff/oversight)
- Reads: `as_of`, `demo_now`, `staffing`; **alerts as decision lines** (P0/P1 created, unowned, due soon, overdue, stuck waiting, shift ended with queued customers), each with a case reference and "what to do"; **lanes in fixed order** (P0 and P1 · Overdue · Due soon · Unowned · Stuck waiting) with counts and rows (owner, age from the demo clock, due, follow-up preference); `live_queue_length`; `new_flags_count`.
- Writes: none (assign and priority are CON-13; the shift switch is CON-7; the clock is CON-8).
- States the UI must be able to show: seeded lanes and alert · nothing urgent · after advancing the clock (a case turned overdue) · shift ended with a customer waiting.
- Errors (code → screen response): UNAUTHENTICATED; ROLE_NOT_ALLOWED (supervisor only).
- Guarantees: one read returns every lane together (no half-loaded lane); an empty lane keeps its place.
- Timing budget: p95 ≤ 800 ms [A].
- Data class and where it may go: D1 and D2 (display name only); staff only.
- Access: demo supervisor.
- Mock examples: SEEDED, AFTER_ADVANCE, SHIFT_ENDED_WITH_WAITING, NOTHING_URGENT; errors UNAUTHENTICATED, ROLE_NOT_ALLOWED.
- Status: specified (UX-3, proposal)

### CON-18 · Business-owner outcomes
- Screens: SCR-9 Business-owner outcomes · Flows: FLOW-11
- Requirements: R-32, R-35, R-39 · Stories: US-24
- Operations (operationId): `getOwnerMetrics` (GET /api/staff/owner-metrics)
- Reads: per measure `id` (M-n), label, numerator, denominator, unit, value, `null_reason`, `kind` (measured or estimate), `case_refs`; `as_of`; `seeds_included` and `seed_count`; the outcomes, handoffs by reason, missed promises, and the cases behind every number. **`in_scope_correct_resolution` is a labelled estimate from live chats** ("Estimate from live chats (no verified answers)"). **The measured north star comes only from the held-out eval run (CON-20)**; `measured_north_star_link` points to `/eval`.
- Writes: none.
- States the UI must be able to show: tiles with denominators · "No outcomes yet" (zero denominators) · a measure with "—" and its reason · numbers older than the demo clock ("as of 2:20 pm; the demo time is now Mon 7:00 am") · a zero-denominator number that is not a link.
- Errors (code → screen response): UNAUTHENTICATED; ROLE_NOT_ALLOWED; "Outcomes didn't load. Try again."
- Guarantees: stored data only; every rate has its denominator; a handoff is never called containment; seeds are counted and named; "not a target".
- Timing budget: p95 ≤ 1 s [A].
- Data class and where it may go: D5 plus case references; no PII.
- Access: demo business owner (and supervisor).
- Mock examples: SEEDED (made-up values), EMPTY; errors UNAUTHENTICATED, ROLE_NOT_ALLOWED.
- Status: specified (UX-3, proposal)

### CON-19 · Monitoring
- Screens: SCR-10 Monitoring · Flows: FLOW-11
- Requirements: R-35, R-36, R-41 · Stories: US-27
- Operations (operationId): `getMonitoring` (GET /api/monitoring)
- Reads: `as_of` (wall-clock time; the "Updated" line shows it) and `demo_now` (business date only); **health tiles** (volume, failures with share, latency p50 and p95, each a numerator, denominator or a null with a reason); **spend** against the $30 cap with `resets_at`; **correctness** as a separate group (the containment estimate, escalations by reason); **alerts as decision lines**, each `firing` or `quiet`; the alert settings; the last health-check restart; trace export status.
- Writes: none.
- States the UI must be able to show: all quiet · cap reached · p95 over 12.5 s · "Not enough turns yet (fewer than 20)" · nothing since the reset · zero-traffic alert · "This data is [n] minutes old." (refresh every 30 s).
- Errors (code → screen response): RESET_IN_PROGRESS; REQUEST_RATE_LIMITED; "Monitoring didn't load. Try again."
- Guarantees: **alerts live on the page only** (no push channel, R-35):
  - **Spend:** one alert, at the cap ($30 per day). No 80% warning. **The spend day is midnight to midnight America/Chicago** (real time, decided 2026-10-21).
  - **Latency:** an alert when p95 exceeds 12.5 s per turn.
  - **Health-check restarts:** an alert with the time of the last restart.
  - **Failure rate:** an alert when more than 2% of turns failed [T] (DO-6, UXR-23).
  - **Trace export:** an alert when traces are being dropped (DO-6, UXR-23); the traces themselves are never shown here.
  - **Zero traffic:** an alert after **4 hours with no new live chat**, not counting late night, **22:00 to 06:00 Austin time** (America/Chicago), a configurable assumption [A] (decided 2026-10-21).
  Health and correctness never share a group (R-35). Redacted by construction: no codes, no card-like numbers, minimal PII, no trace links.
- Timing budget: p95 ≤ 1 s [A].
- Data class and where it may go: D5. Redacted aggregates only; traces stay in Langfuse on the VPS and are never shown here.
- Access: any signed-in role (R-48). **Reverses the earlier "readable without sign-in" proposal.** Aggregates only.
- Mock examples: DEFAULT (made-up values), FIRING, TOO_FEW_TURNS, EMPTY, ZERO_TRAFFIC_FIRING, FAILURE_AND_TRACE_FIRING; errors RESET_IN_PROGRESS, REQUEST_RATE_LIMITED. **Closed (decided 2026-10-21):** the "Updated [time]" line uses wall-clock time (`as_of`). Spend and alert timers run on real time; the demo clock drives the business date only (`demo_now`).
- Status: specified (UX-3, proposal)

### CON-20 · Latest evaluation run, per split
- Screens: SCR-11 Evaluation report · Flows: FLOW-11
- Requirements: R-12, R-38, R-39 · Stories: US-27
- Operations (operationId): `getLatestEval` (GET /api/eval/latest)
- Reads: **per split (dev, sealed held-out)**, each a run with run id, date, agent version, size, mix (category, count, origin transcript or synthetic, what a synthetic case tests) and measures as "n of N" (with min and max over repeats); `headline` (from the held-out split only); `current_agent_version`; the dev label ("Dev (we read and fixed these, so it overstates)"); redacted dev failures.
- Writes: none.
- States the UI must be able to show: both splits · "No held-out run yet" with dev labelled · "This run used an earlier version of the agent" · "No evaluation run yet. No number is shown before then."
- Errors (code → screen response): RESET_IN_PROGRESS; REQUEST_RATE_LIMITED; "The evaluation report didn't load. Try again."
- Guarantees: the headline is never a dev number; a target (60–75%, ≥ 90%) appears only in a column labelled Target, never as a result; every number has its denominator.
- Timing budget: p95 ≤ 1 s [A].
- Data class and where it may go: D5 and D0; dev failures are redacted summaries.
- Access: any signed-in role (R-48). **Reverses the earlier "readable without sign-in" proposal.**
- Mock examples: BOTH_SPLITS (made-up values), DEV_ONLY, STALE_RUN, NO_RUN; errors RESET_IN_PROGRESS, REQUEST_RATE_LIMITED.
- Status: specified (UX-3, proposal)

### CON-21 · Staff-side live stream for one case (new)
- Screens: SCR-6 Case view · Flows: FLOW-8
- Requirements: R-31, R-33 · Stories: US-15, US-20
- Operations (operationId): `streamCaseEvents` (GET /api/staff/cases/{reference}/events, `text/event-stream`)
- Reads: a stream in CON-3's format with `Last-Event-ID` replay. Events: `customer_message` (so the representative sees replies arrive), `controller_changed`, `chat_closed` (closed by staff or shift ended), `demo_reset`, `case_changed` (new version and lifecycle). No progress events.
- Writes: none.
- States the UI must be able to show: the customer's reply arriving in the live box · "This chat ended because the demo was reset." · a case changed elsewhere (prompts a reload before the next action).
- Errors (code → screen response): UNAUTHENTICATED; CASE_NOT_FOUND.
- Guarantees: replayable by event id; async; opened while a case view is open.
- Timing budget: first event within 1 s of a change [A].
- Data class and where it may go: D4 and D2; customer messages with codes redacted; staff only.
- Access: demo representative, supervisor, owner (read only).
- Mock examples: FRAMES (a customer reply, then the chat closes); errors UNAUTHENTICATED, CASE_NOT_FOUND.
- Status: specified (UX-3, proposal)

### CON-22 · Demo login (one username and password gates the whole deployment)
- Screens: SCR-12 Demo login · Flows: FLOW-12
- Requirements: R-48, R-40 · Stories: US-25
- Operations (operationId): `login` (POST /api/login), `logout` (POST /api/logout)
- Reads: the new session (role `customer`, display name, what it sees) and where to go next (`/`).
- Writes: `{username, password}`. Success sets the `mhc_session` cookie. The credentials come from the Railway variables `MERIDIAN_DEMO_USERNAME` and `MERIDIAN_DEMO_PASSWORD` (one pair, shared with reviewers); the examples use placeholders only (`<demo-username>`, `<demo-password>`). `logout` clears the cookie.
- States the UI must be able to show: the login form · "Signing in…" · "That username or password didn't work." · "Too many attempts. Wait a moment and try again." · any other page redirecting here after UNAUTHENTICATED.
- Errors (code → screen response): LOGIN_FAILED (401): **one message for every cause**, never says which part was wrong; LOGIN_RATE_LIMITED (429) with `Retry-After`; VALIDATION_ERROR (400) for an empty field.
- Guarantees: **every route except `login` and `/healthz` answers 401 UNAUTHENTICATED without a session.** A new login starts as the customer role. Attempts are rate limited per IP. The password is compared by code, never returned, logged or traced.
- Timing budget: p95 ≤ 500 ms [A].
- Data class and where it may go: **secret**: the credentials never reach the model, logs or traces; responses carry no username or password.
- Access: public (the only route besides `/healthz`).
- Mock examples: LOGGED_IN; request PLACEHOLDERS; errors LOGIN_FAILED, LOGIN_RATE_LIMITED, VALIDATION_ERROR.
- Status: specified (UX-3, proposal)

---

## State coverage check (review question 1)

Every data-driven state in the SCREEN_SPECS state matrix has a response that produces it. The states that are purely client-side are named at the end.

| Screen | States and the response that produces each |
|---|---|
| SCR-1 | default, empty: CON-1 STARTED. loading, error (send failed): client, plus CON-2 timeout. partial: CON-2 `text` + `no_info`; handoff with the chooser open. stale: CON-3 replay and `staffing_changed`; slot cards "not held". success: CON-2 BOOKED, VERIFIED_ACCOUNT_INVOICE, HANDOFF; CON-5 PHONE_MORNINGS. disabled: CON-2 RATE_LIMITED notice, CON-3 `chat_closed`, `demo_reset`, SESSION_ENDED; taken windows from `slot_card` (`taken`, `disabled`). Flow states: SAFETY, CONDITIONAL_SAFETY, BURNING_CHECK, EMERGENCY_LINE, QUICK_CHECKS, OUT_OF_AREA, SLOT_CARD, LOCATE_PROMPT, CODE_SENT, CODE_WRONG, CODE_EXPIRED, CODE_LOCKED, NOT_VERIFIED, SLOT_TAKEN, BOOKED, APPOINTMENT, CANCELLED, CHANGE_REQUEST, HANDOFF, LIVE_QUEUED, FAILURE_OFFER, BOOKING_CAP, SPEND_CAP_REACHED, TURN_TIMEOUT, BUSY, AI_PAUSED; CON-3 `representative_joined`, `ai_paused`, `ai_resumed`, `chat_closed`, `shift_ended`, `demo_reset`, `staffing_changed`, `clock_changed` |
| SCR-2 | default, stale, disabled: CON-6 ONE_ACTIVE, USED_AND_EXPIRED. empty: EMPTY. error: RESET_IN_PROGRESS / any failure. success: client (copied) |
| SCR-3 | default: CON-7 OFF + CON-8 START. error, success: CON-7 and CON-9 results and errors (RESET_FAILED). stale: CON-7 re-read. disabled: client pending |
| SCR-4 | default: CON-10 ROLES (listDemoRoles). error: VALIDATION_ERROR or failure. stale: ROLE_NOT_ALLOWED `role_reset`, getSession. success: switchRole. The screen's old "sign-in" is now the role switch; SCR-12 and CON-22 own the login |
| SCR-12 | login, error (LOGIN_FAILED, LOGIN_RATE_LIMITED), success (LOGGED_IN): CON-22; UNAUTHENTICATED sends any page here |
| SCR-5 | default: CON-11 SEEDED. empty: ALL_CAUGHT_UP. partial: BRIEF_BEING_WRITTEN. disabled: STAFFED_WITH_WAITING absent (`staffing` = nobody online). success: CON-13 CLAIMED. stale: re-read, `due_state` |
| SCR-6 | default: CON-12 DEFAULT. empty: CASE_NOT_FOUND / client. partial: BRIEF_BEING_WRITTEN, TRIMMED_STOP, `current_unavailable`. error: CASE_NOT_FOUND, ROLE_NOT_ALLOWED, REASON_REQUIRED, WAKE_UP_REQUIRED, OUTCOME_REQUIRED. stale: `changed_since`, VERSION_CONFLICT. success: CON-13, CON-15, CON-16. disabled: `allowed_actions`. Flow states: LIVE_JOINED, WAITING, SAFETY_CASE, FEE_BEARING_CHANGE, NOT_LIVE, `shift_ended`/`case_changed` |
| SCR-7 | default, empty, stale: CON-17 SEEDED, NOTHING_URGENT, AFTER_ADVANCE. success: CON-8 NEXT_MORNING, CON-7 TURNED_OFF_WITH_WAITING, CON-13 ASSIGNED. error: VALIDATION_ERROR, REASON_REQUIRED. disabled: no backwards step exists |
| SCR-8 | default, empty, success, disabled: CON-16 list, EMPTY, REVIEWED, ROLE_NOT_ALLOWED |
| SCR-9 | default, empty, partial (null reasons), stale (`as_of` vs CON-8), disabled (zero denominator): CON-18 SEEDED, EMPTY |
| SCR-10 | default, empty, partial, stale, alerts: CON-19 DEFAULT, EMPTY, TOO_FEW_TURNS, FIRING, ZERO_TRAFFIC_FIRING |
| SCR-11 | default, empty, partial, stale: CON-20 BOTH_SPLITS, NO_RUN, DEV_ONLY, STALE_RUN |

**Client-side states (no contract response, by design):** "Starting the chat…" and "Meridian assistant is replying…" (timers from the CON-1 `limits`), "That didn't send. Your message is still here." (transport failure or the 65 s give-up), "Reconnecting…" (a dropped stream), "Copied", "Checking…", "Resetting…", and saving and disabled keys while a request is in flight.

## Contract needs N-1…N-27: where each landed

| N | Landed in | Note |
|---|---|---|
| N-1 | CON-3 | All nine events on every chat; names follow the decided list (`staff_message`, `ai_resumed`) |
| N-2 | CON-3, CON-21 | Event ids and `Last-Event-ID` replay |
| N-3 | **CON-21 (new)** | Why: see "Why CON-21 exists" |
| N-4, N-27 | CON-2 `settled` | From conversation state; `built_from: conversation_state` |
| N-5 | CON-2 | `speaker` and `at` on every block |
| N-6 | CON-2 | All 24 block types; code prompt sub-states |
| N-7 | CON-2 | Composed errors as 200; BOOKING_CAP and SESSION_ENDED included |
| N-8 | CON-2 `writes[]` | A list, not one flag (UXR-5) |
| N-9 | CON-4 | `already_open`; works under every cap |
| N-10 | CON-5 | Masked labels, `on_record`, windows, `general_only` |
| N-11 | CON-6 | Scoped to the `mhc_session` login session |
| N-12 | CON-7 | `converted_cases` |
| N-13 | CON-8 | Steps, `became_overdue`, forward only |
| N-14 | CON-9 | All-or-nothing; roles go back to customer, the login stays |
| N-15 | CON-10 | Roles, GET, DELETE; no passcode |
| N-16 | CON-11 | All row fields |
| N-17 | CON-12 | Snapshot vs current, `trimmed`, `allowed_actions`, `version`, `seed`, `as_of`, agent version |
| N-18, N-19 | CON-13, CON-14 | Renamed to the decided names |
| N-20 | CON-15 | Fixed label |
| N-21 | CON-16 | PATCH |
| N-22 | CON-17 | Alerts, counts, queue length |
| N-23 | CON-18 | Per-measure null reasons; seed count |
| N-24 | CON-19 | `as_of`, null reasons, alerts, last restart, redaction |
| N-25 | CON-20 | Per split, versions |
| N-26 | CON-2 | Decided 2026-10-21 (60 s, BUSY, no streaming, SSE with replay) |
| N-27 | CON-2, CON-3 | `settled` built from conversation state (every completed write), not the latest turn; `writes[]` lists this turn's writes (R-45, R-46) |
| N-28 | CON-22 | `login` / `logout`, `mhc_session`, `LOGIN_FAILED` (one message), `LOGIN_RATE_LIMITED`, `UNAUTHENTICATED` on every other route |
| N-29 | CON-10, CON-11…CON-18 | `ROLE_NOT_ALLOWED` under the customer role; role held once per login session; chat routes ignore the role |
| N-30 | CON-7, CON-9 | Session required; no separate cool-down; per-IP reset throttle [A] |
| N-31 | CON-2, CON-3, CON-10 | A chat survives a role switch (chat ignores the role); reset keeps the login and sets the role to customer |

**Not fully expressed:** (1) Settled: the owner reads cases read-only (CON-12 card); the SCREEN_SPECS SCR-6 refusal state is replaced by a read-only state. (2) N-27's scope (this conversation, not just this turn) follows the decision on SDQ-8; if that decision changes, only `settled.actions` changes. (3) The SCR-1 loading, give-up and reconnect lines are client behaviour driven by the constants in CON-1 `limits` and the CON-3 stream, so nothing in a response produces them.

## DO-4 requests (UXR-N): adopted / adapted / rejected

| UXR | Outcome | Reason |
|---|---|---|
| UXR-1 | Adopted | 4xx only for requests the server could not process; composed outcomes are 200 with an `error` or `notice` block plus `settled`. The panel stays true on every limit card |
| UXR-2 | Adopted | Browser-minted `turn_id` on every turn, reused by Try again |
| UXR-3 | Adapted | Typed `text` / `choice` / `code` payload adopted with `card_id`, `options`, `answered`. **Added a fourth kind, `form`**, for the locate and where cards: name, phone and ZIP are not an option value |
| UXR-4 | Adopted | TURN_TIMEOUT at 60 s and BUSY above 30 are notices with `try_again` and `talk_to_person`; browser give-up at 65 s; "Still working on this…" at about 10 s |
| UXR-5 | Adopted | `writes[]` replaces the single flag |
| UXR-6 | Adopted | The `SettledView` shape is the `settled` object; I added `built_from` and `actions[]` (the whole conversation's writes) so the words and the panel read the same rows |
| UXR-7 | Adopted | `locked` reaches the handoff card in the same reply; one NOT_VERIFIED text for every cause |
| UXR-8 | Adapted | The session scopes the inbox and owns threads, but the cookie is now the single `mhc_session` (UXR-27); `mhc_demo` and `mhc_staff` are retired |
| UXR-9 | Adapted | Staff-side stream added as **CON-21** (a new contract, not "CON-3b"), because a stream and a snapshot are different shapes with their own access check |
| UXR-10 | Adapted | CON-3 open on every chat, as asked. The event list follows Innocent's decided names (`staff_message`, `ai_resumed`) rather than `representative_message` and `handed_back`; `case_created` is not in the decided list and is not sent to the customer |
| UXR-11 | Adopted | `turn_id` on CON-4; `already_open` in the response |
| UXR-12 | Adopted | `destination: on_record \| general` and windows `morning \| afternoon \| any` [A] |
| UXR-13 | Adopted (decided) | Innocent decided on 2026-10-21: the chat's date follows the demo clock through `clock_changed`; reset returns to Fri 2026-10-16; never the server clock |
| UXR-14 | Adopted | GET and DELETE on /api/staff/session (plus a roles list) |
| UXR-15 | Adopted | `expected_version` on actions and on contact activities; `changed_by`, `changed_at` on VERSION_CONFLICT |
| UXR-16 | Adopted | PATCH /api/staff/flags/{id} |
| UXR-17 | Adopted | No 80% alert; the cap itself and 12.5 s. Added the zero-traffic alert (4 hours, not counting 22:00 to 06:00 Austin time [A]) and the spend day (midnight to midnight America/Chicago), both decided 2026-10-21 |
| UXR-18 | Adopted | Fixed texts are copied word for word from SCREEN_SPECS's copy notes (the safety wording uses "immediately", note 1; no "No fee has been charged", note 2). Left for the copy owner: SCREEN_SPECS says "This is taking longer than it should." and system design §8.1 says "I'm sorry, this is taking longer than it should."; I used SCREEN_SPECS's |
| UXR-19 | Adopted | `promise_text`, `due_label` and `extra_lines` are sent apart and the screen joins them: "{promise_text}, {due_label}. {extra_lines}" |
| UXR-20 | Adopted | No progress events anywhere; nothing waits for one |
| UXR-21 | Adopted | `settled.visit` is the visit this conversation wrote or changed most recently; the others stay in `settled.actions[]`. Stated on the CON-2 card and in the schema |
| UXR-22 | Adopted | `reason` added to the createFlag request: an optional free-text staff note (D4). `Flag.reason` may be null. The UX copy's three fixed labels stay as the screen's flag kinds, not as `reason` |
| UXR-23 | Adopted | CON-19 alert types `failure_rate_over_2pct` (more than 2% of turns failed [T]) and `trace_export_failed`, each with a decision line and a firing example |
| UXR-24 | Adopted | `version_date` nullable and `version_label` added on the source chip (CON-2) and on `CaseSource` (CON-12). The label is the version as the file states it ("Rev 2026-01", "undated"); no date is invented |
| UXR-25 | Adopted | `due_at` and `due_label` nullable on `HandoffBlock` and `ChangeRequestBlock`; new example HANDOFF_STAFFED. The `shift_ended` event embeds the same block |
| UXR-27 | Adopted (decided, R-48) | One demo login gates the whole deployment. New **CON-22** (`login`, `logout`, screen SCR-12); `UNAUTHENTICATED` (401) on every route except login and `/healthz`; CON-10 becomes the four-role switch (no passcode, in every shared header); CON-7 and CON-9 need only the session (no separate cool-down); one `mhc_session` cookie replaces `mhc_demo` and `mhc_staff`; SCR-10 and SCR-11 are no longer public |
| UXR-26 | Adopted | BUSY sentence: "A lot of people are chatting right now, so I can't take this message. A person can pick it up." + the person key |

**Rejected: none.** No request conflicted with a screen state.

## Settled at §6 on 2026-10-21 (no longer [A])

The per-conversation code resend cap of 3 · the 65 s browser give-up · the 15 s stream heartbeat · ~~SCR-10 and SCR-11 readable without sign-in~~ (reversed by R-48: behind the login) · the staffing toggle open to any browser · the BUSY sentence · CON-19's "Updated [time]" uses wall-clock time (spend and alert timers run on real time; the demo clock drives the business date only, which closes the last `unknown`) · the 4-hour zero-traffic alert with quiet hours 22:00 to 06:00 Austin time (the hours remain a configurable setting).

## Closed by R-48 (2026-10-21)

- **The staff sign-in passcode:** none. The login is the gate; the role switch is a label.
- **Reset gating:** none beyond the login (no separate cool-down). A per-IP throttle stays as a safety net [A].

## Still open

Only numbers to tune at build: the timing budgets other than the 12.5 s p95 and the 60 s deadline, the 5 s reset-lock wait and the per-IP throttle.

## Other notes

- CON-12's owner question is settled: the owner reads cases with `allowed_actions: []`, never ROLE_NOT_ALLOWED.
- Brief heading 8 is fixed as **"Who they are and how to reach them"** (gender-neutral; the consolidated example's "he" was one case's wording).
- REQUEST_RATE_LIMITED (429) is new: it exists so every read operation has a documented 4xx and so R-41's per-IP limit has a name distinct from the chat's RATE_LIMITED.
