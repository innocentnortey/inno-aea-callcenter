# API ↔ UI contracts: CON-1…CON-21 as the backend will serve them (DO-4, part 2)

**Date:** 2026-10-21. **Status:** DRAFT **revision 3**: reconciled with the UX-3 contracts
[`UI_CONTRACTS.md`](../../ux/03-structure/UI_CONTRACTS.md) and
[`ui-contracts.openapi.yaml`](../../ux/03-structure/ui-contracts.openapi.yaml) (OpenAPI 3.1, 29 operations,
CON-1…CON-21). Those are UX-3 **proposals, not yet signed by Innocent**. Nothing here is built.

**Who owns what.** The UX session owns CON-1…CON-21 and their shapes; **the OpenAPI file is the authority for every
request and response field**, and this file does not repeat them. This file says, per contract, which component
serves it, whether the backend agrees field by field, and what the backend needs changed, written as requests
**UXR-n** to the UX session. Nothing under `docs/ux/` is edited from here.

**Labels:** [A] assumption · **proposal** awaiting the UX gate or Innocent · [Decided X].

---

## 0. Conventions: adopted from UX-3 as written

**What it looks like in practice.** The customer submits the locate card. The page posts CON-2 with
`{"turn_id": "…", "payload": {"kind": "form", "card_id": "locate-3", "values": {"name": "Omar Patel", "phone": "512-555-0102"}}}`.
`gates/gate.py` parses it as a `form` intake, stores "[details submitted]" in the chat, and hands the values to
`IdentityService.locate` by code: no model sees the phone number. The answer is HTTP 200 with a `code_prompt` block
(state `sent`, hint "the phone ending in 02") and `settled.identity.status = "code_sent"`.

| Topic | UX-3 convention | Backend note |
|---|---|---|
| Two kinds of failure | Composed outcomes are HTTP 200 (`ErrorBlock`, `NoticeBlock` + `Notice`, always with `settled`); 4xx/5xx only for requests that could not be processed | `ApiErrorCode` in [internal-components §11](internal-components.md#11-errors-halts-and-what-the-customer-sees) now uses the UX-3 names (VALIDATION_ERROR 400, VERSION_CONFLICT, CASE_ALREADY_CLAIMED, SPEND_CAP_REACHED, STAFF_AUTH_REQUIRED with `details.reason`, REQUEST_RATE_LIMITED 429, CODE_CAP_REACHED, AI_PAUSED, RESET_FAILED, HANDOFF_FAILED, ROLE_NOT_ALLOWED, CASE_NOT_FOUND, FLAG_NOT_FOUND) |
| Error body | `ApiError {error: {code, field, constraint, details}, request_id}` | One handler in `web/app.py` rewrites FastAPI's 422 to 400 `VALIDATION_ERROR`; `details` carries named extras only, never a value |
| Cookies | One cookie, `mhc_session`, set by login (CON-22); it carries the current role, owns threads and scopes the inbox. `mhc_demo` and `mhc_staff` are retired (OpenAPI `info.description`) | Reconciled at Stage 7 (AEA-08); the OpenAPI wins on wire names |
| IDs on the wire | `message_id`, `flag_id`, inbox `id` are strings | Integer row IDs are serialised as strings by `web/schemas/*` |
| Priority | `Priority {level, word}` (`Safety`, `Danger`, `Time-sensitive`, `Standard`, `Routine`) | `policy/handoff.py` owns the word per level |
| Identity status | `not_checked`, `code_sent`, `verified`, `not_verified`, `locked` | The internal `located` state is shown as `not_checked`: locating reveals nothing (R-16) |
| Fixed texts | Copied word for word from SCREEN_SPECS copy notes; `produced_by_code: true` on promise and reference | `policy/texts.py` copies them; a test compares with a fixture taken from the signed copy (UXR-18) |
| Timing constants | CON-1 `limits`: `turn_deadline_ms` 60000, `still_working_after_ms` 10000, `browser_give_up_after_ms` 65000, `max_message_chars` 2000 | Served from `policy/limits.py` [Decided SDQ-1]; see §3 for the [A] items |

---

## 1. Per contract: serving component and agreement

Area and wave are DO-3 §8's; the route file and its ticket are the slice plan's §3 (one route file and one schema file per ticket, AEA-08, 2026-10-21). "Agrees" means every request and response field in the OpenAPI is one the backend can
produce with the meaning UX-3 gives it.

| CON | operationIds | Served by (area) | Agreement | Backend notes |
|---|---|---|---|---|
| CON-1 | `startChatSession`, `getChatThread` | `web/routes/chat.py` → `services/session.py` (A8; AEA-40) | **Agrees** | `getChatThread` is new: reads `messages`, `conversations.state` and `settled` from A0's `repos_core` |
| CON-2 | `submitTurn` | `web/routes/chat.py` → `services/turn.py` → graph (A8, A7; AEA-40) | **Differs: UXR-21, UXR-24, UXR-25, UXR-26** | `form` payload → `gates/gate.py` intake (A1) and `nodes/front.py` (A7d): a locate form goes to `IdentityService.locate`, a where form sets the task's ZIP; both by code. `AI_PAUSED` notice composed by `nodes/compose.py` when `controller = human`. `TURN_IN_PROGRESS` carries `details.retry_after_ms` (2000 [A]) |
| CON-3 | `streamChatEvents` | `web/routes/events.py` (A8; AEA-41), async SSE polling `events` (`id > Last-Event-ID`) about once a second [A] | **Differs: UXR-25** (the `shift_ended` event embeds a `HandoffBlock`) | Event names as UX-3 (`staff_message`, `ai_resumed`; no `case_created` to the customer). Writers: A6 (`staffing_changed`, `clock_changed`, `shift_ended`, `demo_reset`), A9 (`representative_joined`, `staff_message`, `ai_paused`, `ai_resumed`, `chat_closed`) |
| CON-4 | `requestPerson` | `web/routes/handoff.py` → `services/person_request.py` → `services/handoff.py` (A8 → A6; AEA-42) | **Differs: UXR-25** | One open case per thread: a second tap or a second reason returns `already_open` with the same reference (internal-components §7) |
| CON-5 | `saveFollowUp` | `web/routes/handoff.py` → `CaseService.set_followup` (A8 → A6; AEA-42) | **Agrees** | `general_only` in the handoff block's `followup_chooser` when the customer is not verified |
| CON-6 | `listDemoInbox` | `web/routes/demo.py` → `IdentityService.inbox` (A8 → A4; AEA-43) | **Agrees** | The only response carrying a code; excluded from request logging bodies |
| CON-7 | `getStaffing`, `setStaffing` | `web/routes/demo.py` → `DemoService` (A8 → A6; AEA-43) | **Agrees** | Requires the demo login session (R-48, UXR-27); §3 item 5 superseded |
| CON-8 | `getDemoClock`, `advanceDemoClock` | read: `web/routes/demo.py` (A8; AEA-43); **advance: `web/routes/staff_clock.py` (A9; AEA-47)**, because it needs the supervisor session | **Agrees** | Advance is supervisor-only per UX-3 (DO-4 rev 2 had it open; UX-3 wins). The chat's "today" follows the demo clock [Decided, Innocent 2026-10-21] |
| CON-9 | `resetDemo` | `web/routes/demo.py` → `ResetService` (A8 → A6; AEA-43) | **Agrees** | Body `{confirm: true}`; 409 RESET_IN_PROGRESS on reset, 503 elsewhere; see §3 item 5 |
| CON-10 | `listDemoRoles`, `switchRole` | `web/routes/staff_session.py` → `services/staff.py` (A9; AEA-44) | **Agrees** | A role switch for the signed-in session (R-48), no passcode. `services/staff.py` also implements `require_staff(*roles)`, the one staff-session check every staff route uses; `web/deps.py` (AEA-23) declares it |
| CON-11 | `getQueue` | `web/routes/staff_cases.py` → `CaseService.queue` (A9 → A6; AEA-45) | **Agrees** | Backend orders rows; `age_label`, `due_label` from the demo clock |
| CON-12 | `getCase` | `web/routes/staff_cases.py` → `CaseService.detail` + lookup log (A9 → A6; AEA-45) | **Differs: UXR-24** (`CaseSource.version_date`) | Every role reads; owner gets `allowed_actions: []`, never ROLE_NOT_ALLOWED [settled by UX-3, proposal]. `Brief` fields as UX-3 (internal-components §7 aligned) |
| CON-13 | `applyCaseAction` | `web/routes/staff_cases.py` → `CaseService.apply` (A9 → A6; AEA-45) | **Agrees** | `expected_version` required; VERSION_CONFLICT with `details.changed_by`, `changed_at`, `current_version` |
| CON-14 | `liveChatAction` | `web/routes/staff_live.py` → `services/live_chat.py` (A9; AEA-46) | **Agrees** | Writes `conversations.controller` and the message in one transaction; appends the CON-3 and CON-21 events |
| CON-15 | `recordContactActivity` | `web/routes/staff_cases.py` → `CaseService.record_activity` (A9 → A6; AEA-45) | **Agrees** | Fixed label "Demo: recorded, not sent" |
| CON-16 | `createFlag`, `listFlags`, `reviewFlag` | `web/routes/staff_cases.py` → `FlagService` in `services/staff.py` (A9; AEA-45, AEA-44) | **Differs: UXR-22** | — |
| CON-17 | `getOversight` | `web/routes/staff_cases.py` → `CaseService.oversight` (A9 → A6; AEA-45) | **Agrees** | Lanes in UX-3's fixed order |
| CON-18 | `getOwnerMetrics` | `web/routes/reads.py` → `services/metrics_reader.py` (A10b; AEA-48, AEA-53) | **Agrees** | Route in ticket wave 2 (AEA-48), reader in wave 3 (AEA-53). `in_scope_correct_resolution` is the M-3 estimate (`kind: estimate`); the measured north star links to CON-20 |
| CON-19 | `getMonitoring` | `web/routes/reads.py` → `services/metrics_reader.py` (A10b; AEA-48, AEA-53) | **Differs: UXR-23** | Spend day midnight to midnight America/Chicago, `resets_at` from it; zero-traffic alert 4 h outside 22:00–06:00 Chicago [Decided 2026-10-21, per UX-3]. `as_of` is real time (§4) |
| CON-20 | `getLatestEval` | `web/routes/reads.py` → `services/metrics_reader.py` (A10b; AEA-48, AEA-53) | **Agrees** | Reads the eval results tables A11's harness writes |
| CON-21 | `streamCaseEvents` | **`web/routes/staff_live.py` (A9; AEA-46)**, async SSE polling the case's event stream | **Agrees** | Its own small async generator over `repos_core.events.after(...)`; no shared SSE helper with CON-3 until a third stream exists (code-design S-11) |
| CON-22 | `login`, `logout`, `getSession` | `web/routes/auth.py` (A8; AEA-23) | **Adopted** (UXR-27, R-48) | The one gate for the whole deployment: username and password from the Railway variables, `mhc_session` cookie, `UNAUTHENTICATED` (401) on every route except login and `/healthz`; login failures are one message (`LOGIN_FAILED`) and rate limited per IP |

**Count: 15 of 21 contracts agree field by field; 6 differ (CON-2, CON-3, CON-4, CON-12, CON-16, CON-19), each by a
request below; 0 gaps** (every one of the 29 operations has a serving component).
CON-22 (login, logout, getSession) came later with R-48 and is outside that count.

> **Reconciled 2026-10-21 (AEA-08):** the *Served by* cells name the route files as the slice plan split them (one route file and one schema file per ticket), CON-10's operationIds are the OpenAPI's, the cookie row follows the OpenAPI, and CON-22 has its row. No field, type, status code, error name or signature changed.

---

## 2. Requests to the UX session

### 2.1 UXR-1…UXR-20 (DO-4 rev 2): all closed

UX-3 adopted 17 and adapted 3; the backend accepts the three adaptations as written:

| UXR | UX-3 outcome | Backend |
|---|---|---|
| UXR-3 | Adapted: a fourth payload kind `form` | Accepted: `Intake.kind = "form"` with `FormValues` (internal-components §3); routed by code, never to a model |
| UXR-9 | Adapted: the staff stream is the new **CON-21** | Accepted: served by A9 (`web/routes/staff_live.py`, AEA-46) |
| UXR-10 | Adapted: `staff_message`, `ai_resumed`; no `case_created` to the customer | Accepted |
| UXR-18 | Adopted; TURN_TIMEOUT copy left to the copy owner | **Settled: UX owns customer copy.** The text is "This is taking longer than it should." (internal-components §11 fixed) |

### 2.2 New requests (UXR-21…UXR-26)

| # | Contract(s) | Request | Why the backend must differ |
|---|---|---|---|
| **UXR-21** | CON-2 `settled.visit` | Confirm the rule for **which** visit `settled.visit` shows when a conversation holds more than one (the booking cap is 3): the backend sends the visit this conversation **wrote or changed most recently**, and every other one stays visible in `settled.actions[]`. The alternative is `visits[]` | `SettledVisit` is a single object; without a rule, two builders could pick different visits and the panel would disagree with the words |
| **UXR-22** | CON-16 `Flag.reason` | `Flag.reason` is required in the response, but `FlagRequest` has no `reason`. Either add an optional `reason` to the request, or confirm the backend fills it from `target` with fixed labels ("The answer was wrong", "The brief was wrong or missing something", "The escalation was wrong") taken from the UX copy | The backend can't invent a staff reason; it needs a source for the field |
| **UXR-23** | CON-19 `MonitorAlert.type` | Add **`failure_rate_over_2pct`** and **`trace_export_failed`** to the alert types | DO-6's alert table has a failure-rate alert (> 2% [T], framing health list) and a trace-export alert; the UX-3 enum has neither, so the backend can't report them |
| **UXR-24** | CON-2 `SourceChip.version_date`; CON-12 `CaseSource.version_date` | Make `version_date` nullable and add **`version_label`** (the version as the file states it) | The KB's versions are not all dates: "Rev 2026-01" (`escalation_and_safety.md`), "2026 (image)" (holiday PNG), and two files are undated (`troubleshooting_before_you_call.md`, `technician_arrival_and_etas.md`). A required `date` forces the backend to invent one, which R-11's citation must not do |
| **UXR-25** | CON-2, CON-3, CON-4 `HandoffBlock.due_at`/`due_label`; CON-2 `ChangeRequestBlock.due_at`/`due_label` | Make both nullable | The `staffed` variant promises "when available", with no time (R-26); a fee-bearing change raised while staff are on shift is live-queued with no due time. Required non-null fields would force a made-up time |
| **UXR-26** | CON-2 `NoticeBlock` BUSY | Confirm the BUSY sentence the backend will hold in its message table (`policy/texts.py`): **"A lot of people are chatting right now, so I can't take this message. A person can pick it up."** + the person key [proposal] | UX-3 marks the BUSY text [A]; the code needs one fixed string, and UX owns customer copy |

---

### 2.3 UXR-27 (2026-10-21, Innocent's decision R-48)

| ID | Where | Request | Why |
|---|---|---|---|
| **UXR-27** | All CONs; CON-10; CON-9; CON-7 | Add an app-wide **demo login** (username + password, one pair from Railway variables): a login operation and screen before anything else, a session cookie on every request, logout, and `UNAUTHENTICATED` (401) on every route except login and `/healthz`. CON-10 becomes a **role switch** (customer, representative, supervisor, owner) for a signed-in session, with no passcode. Reset (CON-9) and the staffing toggle (CON-7) require the session. Make switching between customer and staff one click from any screen | Innocent, 2026-10-21: "it should be password-gated in general … we're going to need to be able to act as staff and act as the customer … make that easy for the reviewer" (PRD R-48) |

## 3. UX-3's [A] items for §6 to confirm

> **2026-10-21:** the staff-passcode and reset-gating items below are **superseded by R-48 / UXR-27** (one app-wide demo login with a free role switch; adopted as CON-22 and the new CON-10).

| # | Item | What DO-1/DO-2 imply | Recommendation | Needs Innocent? |
|---|---|---|---|---|
| 1 | **Code resend cap of 3 per conversation** | DO-1 §10: "at most 3 codes sent per conversation [A] (UX input)", with 10-minute expiry and 3 tries per code (R-15 defaults, decided) | **Confirm 3.** At 3 codes × 3 tries a guesser gets 9 tries at a million-value code (about 1 in 110,000), and the inbox can't be flooded. `CODE_CAP_REACHED` then hands off like `CODE_LOCKED` | No: it sits inside R-15's decided defaults. Mention it to him in passing |
| 2 | **65 s browser give-up; 15 s SSE heartbeat** | 65 s follows from SDQ-1's 60 s plus DO-1 §8.1's "deadline + 5 s" rule. DO-1 says nothing on heartbeats | **Confirm both.** The heartbeat keeps an idle stream open through Railway's proxy while the 1 s poll finds nothing [A: check Railway's idle timeout at first deploy, A12] | No |
| 3 (superseded by R-48) | **No-passcode demo staff sign-in** | DO-1 §10 and §3.3: "a label, not security", acceptable only because every record is fictional, stated in the README (OD-1, N-15) | **Keep no passcode for the reviewer's sake, but say it plainly on SCR-4 and in the README.** If he wants a guard, the cheapest one is a shared demo passcode in a Railway variable, given in the submission notes | **Yes: exposure choice.** Anyone with the URL can read every case and every live chat, including whatever another reviewer types into the customer chat, which could be real personal data |
| 4 (superseded by R-48: every page is behind the login) | **SCR-10 and SCR-11 readable without sign-in** | DO-1 doesn't say. DO-6: CON-19 is aggregates only, redacted by construction; eval reports are in the public repository anyway (R-42) | **Confirm: readable without sign-in.** Nothing on either page is private, and a reviewer reaches them in one click | No: it exposes nothing that isn't already public |
| 5 (superseded by R-48) | **Staffing toggle and demo reset open to any browser** | DO-1 §8.2: reset takes an exclusive lock, ends open chats and invalidates staff sessions; UX-3 throttles it per IP | **Staffing: keep open** (harmless and reversible). **Reset: keep open but add a global cool-down** (at most one reset every 5 minutes [A]) and the confirm step, so one visitor can't keep ending other reviewers' chats | **Yes for the reset: exposure choice.** Anyone on the public URL can end every open chat and wipe the cases another reviewer is demoing |

---

## 4. The open `unknown`: which clock "Updated [time]" uses on SCR-10

**Settled by the System track (§6), 2026-10-21; adopted by the UX track in CON-19 (`as_of`): real (wall-clock) time,** labelled as such, e.g. "Updated 2:20 pm (real time)", with the demo time
shown only in the demo bar.

**Why.** The monitoring page reports what actually ran: spend resets at real Chicago midnight, alert timers (zero
traffic for 4 hours) run on real time, and DO-6's freshness check ("This data is n minutes old") compares real
timestamps. A demo-clock "Updated" line would say "Mon 7:00 am" for data written seconds ago and make a fresh page look
stale. The demo clock belongs to case due times (SCR-5…SCR-9), not to operations. CON-19 already sends both
(`as_of` real, `demo_now`), so this changes copy only. Not a question for Innocent.

---

## 5. Sources

UI_CONTRACTS.md (UX-3, 2026-10-21) and `ui-contracts.openapi.yaml` (29 operations, 115 schemas, read field by field) ·
SCREEN_SPECS copy notes and N-1…N-27 · DO-1 §3.3, §8.1–§8.2, §10 · DO-6 alerts and *Missing instrumentation* · DO-7
M-3, M-26 · PRD R-11, R-15, R-16, R-26, R-42 · issued KB file headers (version strings) via `retrieval/manifest.py`'s
seed (parked `src/meridian/kb/manifest.py`).
