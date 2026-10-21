# Backend ticket amendments from the UX ↔ backend join

**Date:** 2026-10-21. **Status:** proposed text, not yet applied. A later pass copies each row into its ticket file under
`docs/plans/tickets/`. Nothing here edits a ticket, the slice plan, `apps/web/**` or `docs/ux/**`.
**Sources:** the three audits in this folder, [`README.md`](README.md) (the join plan; table (b) maps every finding to the id
used here), slice plan §0a (journey map and *Decisions taken while writing the journey specs*), `stage7/{web,staff,cases}.md`,
`7b-decisions/web.md`, and the coordinator's updates of 2026-10-21 (AEA-62, the `openapi_check` YAML rule, the per-route
contract case files).

## How to apply this file

- **Format.** Every row is a criterion in the tickets' format: `- [ ] AC-<next> [kind] … — verify: … — evidence: …`. Replace
  `<next>` with the ticket's next free number at the time of applying. Tickets were being rewritten while this was written
  (AEA-52, 53, 57, 58, 59, 60, 61, 62 changed between 08:17 and 08:31), so **re-read each ticket first**; a row marked
  *Replaces* names the criterion it replaces by its content as well as its number.
- **Kinds used:** `[invariant]`, `[failure/refusal]`, `[negative]`, `[contract]`, `[journey]`, `[regression/context]`, as the
  tickets already use them.
- **Conditional rows** (marked *If Innocent picks …*) are applied only after his answer in
  [`decisions-for-innocent.md`](decisions-for-innocent.md).
- **Engineering choices** made here (not owner choices): the owner of card `answered` after reload is AEA-40 (customer audit
  A-3); live actions do not change a case's version (staff audit A4, rule (i), which staff.md §5 already implies); the customer's
  `display_name` on staff reads is `null` (staff audit A3); the deploy image copies the OpenAPI into the web stage (shell audit F2).
  Each is labelled where it appears; a planner who finds one wrong records it in the plan and raises it, never works around it.

**Counts:** **57 amendments** across 21 tickets (50 unconditional, 7 applied only after one of Innocent's answers), plus **41 `[journey]` criteria**
(one for each build-loop ticket that has none; the other 15 already carry theirs), plus **one sentence** for the conventions
paragraph: **98 copy-ready criteria** in all.

---

## 1. The sentence for the conventions paragraph

Add to `docs/plans/tickets/_conventions.md` (and so to every ticket's opening paragraph), after the workflow sentence:

> **Every `lane::build-loop` issue carries exactly one `[journey]` criterion** (`.claude/rules/integrated-journeys.md`; slice plan
> §0a): it extends or runs the journeys of the §0a map that its code touches, in `tests/journeys/j<N>/test_aea_<NN>.py` (one file
> per issue per journey; `support/` is AEA-57's and `browser/` AEA-58's, never edited by others), states its verification level
> (`mock-tested`, `integrated with a scripted model`, `verified with live models`) and names *Blocked by* when the harness or the
> journey's landing issue has not merged; a bug fix first reproduces the failure as a journey step and, when it changes a guard,
> also asserts that the legitimate path still passes.

Optional second sentence (the §0a decision on contract cases; it applies only to route issues):

> **Route issues** (AEA-23, AEA-40…AEA-48) add the server cases of the operations they serve to their own
> `tests/contract/cases/<route>.py`; AEA-59 owns the runner, and from the wave-3 merge an operationId with no case fails it.

---

## 2. Amendments per ticket

Ids are `AEA-nn-k`; the join plan's table (b) cites them.

### AEA-08 (docs reconcile, `lane::direct`)

**AEA-08-1** (staff audit A5, A7; customer audit A-1; decisions 5 and 6)
- [ ] AC-<next> [regression/context] The reconcile record lists, without editing the OpenAPI, `UI_CONTRACTS.md` or SCREEN_SPECS: (1) the `applyCaseAction` 409 examples write `changed_at` with a space (`2026-10-16 14:31:00-05:00`) where the server emits ISO 8601 with `T`; (2) staff.md §8 lists `date_label` in `ClockAdvanced` while the OpenAPI `ClockAdvanceResponse` has only `now`, `label`, `became_overdue`, and the route returns the OpenAPI keys (AEA-47-1); (3) web.md §14's `thread()` comment ("customer messages and each completed turn's stored response blocks") is replaced by AEA-40-1's full-history rule; (4) SCREEN_SPECS N-28 vs UI_CONTRACTS CON-22 on the login-throttle copy, and SCREEN_SPECS SCR-1's "the chat resumes" after a new sign-in vs `owned_thread`'s 404, are open with Innocent (join decisions 5 and 6) — verify: `git diff --name-only` and a read of the record — evidence: four entries, each citing its audit row; web.md §14 updated; no path under `docs/ux/` in the diff.

### AEA-23 (web shell, `openapi_check`, CON-22 route) — wave 1

**AEA-23-1** (coordinator update; slice plan §0a decisions)
- [ ] AC-<next> [invariant] `load_contract()` reads the OpenAPI as YAML 1.2 with a loader that keeps timestamps and the YAML 1.1 words `yes`, `no`, `on`, `off`, `ON`, `OFF` as strings (a plain `yaml.safe_load` turns 371 example timestamps into `datetime` objects and those words into booleans), while `true` and `false` stay booleans: the `startChatSession` `STARTED` example's `greeting.at` loads as the string `2026-10-16T14:20:00-05:00`, and a walk over the whole loaded document finds no `datetime` or `date` value — verify: `tests/api/test_openapi_check.py::test_contract_keeps_yaml_strings` — evidence: 0 `datetime`/`date` instances; the named value printed with its type `str`.

**AEA-23-2** (staff audit B1, B2; shell audit B1)
- [ ] AC-<next> [failure/refusal] A refusal tells the browser what to re-read: every `ROLE_NOT_ALLOWED` that `require_staff` raises carries `details.role` = the role the session holds **on this request** (resolved per request, never cached between requests), `details.needs` in x-roles order and `details.reason`; when the `StaffAccess` double changes the session's role between two requests, the second 403 names the new role — verify: `tests/web/test_deps.py::test_role_refusal_names_current_role` — evidence: two 403 bodies with the two roles, both valid against `RoleNotAllowed`.

**AEA-23-3** (coordinator update: per-route contract cases)
- [ ] AC-<next> [contract] `tests/contract/cases/auth.py` holds the server cases for the operations this issue serves, `login` and `logout`: preconditions, every named request example, and each documented error status the route can produce (`login`: 400, 401 `LOGIN_FAILED`, 429 `LOGIN_RATE_LIMITED`; `logout`: 401) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "login or logout" -rs` once AEA-59's runner is merged — evidence: one pass per case; no `route not registered` or `not bound` skip for these two operations.

### AEA-27 (identity) — wave 2

**AEA-27-1** (customer audit A-6)
- [ ] AC-<next> [invariant] An inbox message whose digits this process no longer holds is never `active`: `IdentityService.inbox` reports `status: "expired"` with `code=None` for a row whose `held_by` is another boot id or whose expiry has passed, and keeps `active` with the code only while `_held` has it — verify: `tests/services/test_identity.py::test_inbox_not_held_is_expired` (temp SQLite; send a code, build a second `IdentityService` over the same file to stand for a restart, list the inbox from both) — evidence: first instance `active` with digits; second `expired`, `code` None.

### AEA-29 (cases and handoff) — wave 2

**AEA-29-1** (staff audit A1, high)
- [ ] AC-<next> [invariant] `allowed_actions` on every `CaseSummary` that `queue`, `detail`, `apply` and `oversight` return comes from one pure function of (lifecycle, owner role, the viewing actor's role, the conversation's `live_state`, staffing), and it lists an action **if and only if** the server would accept it now from that role: for every lifecycle × role (representative, supervisor, owner) × live state the planner tabulates, each listed CON-13 action sent to `apply` with the current version is not refused with `ROLE_NOT_ALLOWED` or `NOT_ALLOWED_IN_STATE`, and each CON-13 action not listed is; the other keys follow the same rule against their own operation (`claim_and_join`, `join_chat`, `send_live_message`, `hand_back`, `close_chat` → `liveChatAction`, representative only, staff.md §5 checks; `log_call`, `log_email` → `recordContactActivity`, representative only; `flag` → `createFlag`, representative and supervisor). Fixed points: the owner always gets `[]`; the supervisor never gets `claim_and_join`, `join_chat`, `send_live_message`, `hand_back`, `close_chat`, `log_call` or `log_email`; `claim_and_join` only for the representative on a `live_queued` case while staffing is `simulated_on_shift`; `assign` and `change_priority` only for the supervisor; for the representative, the `getCase` DEFAULT, WAITING and LIVE_JOINED shapes and the `applyCaseAction` CLAIMED shape give exactly those examples' lists for the same lifecycle and live state (the supervisor examples ASSIGNED and PRIORITY_CHANGED disagree with each other and are not used, STF-18). The plan holds the full table — verify: `tests/services/test_cases.py::test_allowed_actions_listed_iff_accepted` (parametrised over the table; `apply` real, a `LiveChatService` double honouring staff.md §5) and `::test_allowed_actions_match_representative_examples` — evidence: 0 listed-but-refused and 0 unlisted-but-accepted; the four example lists equal.

**AEA-29-2** (staff audit A2, high)
- [ ] AC-<next> [invariant] Every display value on the case views has one producer and matches the OpenAPI example for the same input (cases.md §5 "by name only", made concrete): `reason` is display text from one map over `HandoffReason` (never the enum value such as `billing_dispute`); `priority.word` from one map over P0–P4; `due_label` from `policy/handoff.due_label`, with the suffix ", the window start" exactly when the case due is a booked window start (WP-4); `age_label`, `follow_up_short`, `queued_at`, `other_cases[].status`, `identity.line`, `identity.demo_note` and `CaseSource.version_label` each from one named function; and `BriefItem.source_ids` use the same scheme as `CaseSource.source_id` (fixed in the plan and recorded in cases.md §5), so every id in any `source_ids` names a source in the same `CaseDetail` — verify: `tests/services/test_cases.py::test_display_values_match_openapi_examples` (MHC-C-0007 seed at DEMO_START against the `getCase` DEFAULT and `getQueue` SEEDED examples, field by field for the fields listed) and `::test_every_brief_source_id_resolves` (the four seeds and the WP-4 and WP-7 cases) — evidence: each listed field equal to the example, or listed with the reason it differs (an example value STF-18 calls illustrative); 0 unresolved `source_ids`.

**AEA-29-3** (staff audit A3; engineering choice: `null`)
- [ ] AC-<next> [negative] Staff reads never speak as or for the customer: in CON-12 `conversation`, every customer line's speaker is `{kind: "customer", display_name: null}`, never "You" (the OpenAPI example's customer-side wording) and never a name or contact value (the UI shows the kind label) — verify: `tests/services/test_cases.py::test_staff_conversation_customer_unnamed` — evidence: every customer line's `display_name` is null; "You" absent from the serialised `CaseDetail`.

**AEA-29-4** (staff audit A4, high; engineering, rule (i) from staff.md §5)
- [ ] AC-<next> [invariant] Only CON-13 actions, CON-15 activities and the scheduler and staffing transitions of cases.md §5 change a case's `version` or `lifecycle`; the conversation writes that live chat makes (controller, `live_state`, a representative message, `close`) change neither and append no `case_changed` — verify: `tests/services/test_cases.py::test_conversation_writes_keep_case_version` (a case at version n; the conversation-row writes `LiveChatService` makes, applied through the repositories; `detail` re-read) — evidence: version n and the lifecycle unchanged; 0 new `case_changed` rows.

**AEA-29-5** (staff audit B5) — *If Innocent picks A in Decision 2 (add `CaseDetail.events.last_event_id`)*
- [ ] AC-<next> [invariant] `CaseService.detail` sets `events.last_event_id` to the newest event id of `case:<ref>`, read in the same read transaction as the view, so a CON-21 connection resumed from it replays nothing the view already shows — verify: `tests/services/test_cases.py::test_detail_last_event_id_same_snapshot` (append events, read the detail, append one more) — evidence: the id equals the newest id at read time; only the later event is after it.

### AEA-40 (customer API: sessions and turns) — wave 2

**AEA-40-1** (customer audit A-1, high; AEA-58 AC-3 and AEA-62 AC-7 expect it)
- [ ] AC-<next> [invariant] `getChatThread` returns the whole conversation in time order (supersedes web.md §14's "customer messages and each completed turn's stored response blocks"): the greeting as an assistant turn with `blocks: [TextBlock]`; each customer message (`speaker.kind: customer`, `text` as stored); each completed turn's stored blocks; each representative message (`speaker: {kind: representative, display_name: "Riley"}`, `text`); each stored chat-event line of the thread's stream (`speaker: {kind: event, display_name: null}`, `text` = its `line`); a `shift_ended` handoff as an assistant turn with `blocks: [HandoffBlock]`. Entries that are not turns get a stable `turn_id` unique in the thread (`msg:<message_id>`, `evt:<event_id>`), and `last_event_id` is the newest event id, so a stream opened from it replays nothing already in `turns` — verify: `tests/services/test_session.py::test_thread_holds_full_history` (temp SQLite: greeting, one turn, a representative join, a staff message, hand back, a shift end) and `tests/api/test_chat.py::test_get_thread_full_history` with `assert_response_matches(response, "getChatThread")` — evidence: the entries in the stated order with the stated speakers; the body validates; ids unique.

**AEA-40-2** (customer audit A-2)
- [ ] AC-<next> [invariant] A CON-4 person request appears in the history: a `turns` row whose trace `gate_result` is `person_requested` (AEA-42's stored outcome) becomes a customer turn with `text` "Talk to a person" (the `policy/texts.py` entry the button uses; a follow-up on AEA-03 if it is missing) followed by an assistant turn with `blocks: [<stored block>]` (`HandoffBlock` or `LiveQueuedBlock`) — verify: `tests/services/test_session.py::test_thread_shows_person_request_card` — evidence: the two entries in order; the card's reference equals the case's.

**AEA-40-3** (customer audit A-3; engineering choice: this issue owns it)
- [ ] AC-<next> [invariant] Card answers survive a reload: every card block in `getChatThread` whose `card_id` a later customer turn of the thread answered carries `answered` = that option, and only cards nobody answered keep `answered: null`; the answer is read from the later turn's stored intake (kind, `card_id`, option), never from the redacted text. If AEA-10's `turns` or `messages` rows cannot give the `card_id`, the plan records `blocked-on AEA-10` for that column and the UX session's fallback stays in force (FOR-UX-SESSION §8) — verify: `tests/services/test_session.py::test_thread_marks_answered_cards` (a slot card answered, then a yes/no card left open) — evidence: the first card's `answered` is the chosen option; the second is null.

**AEA-40-4** (customer audit A-7) — *Replaces the first clause of AC-2 ("codes shown as '[code entered]'"); agree the three texts with the UX session first*
- [ ] AC-<next> [invariant] History rows read like the live rows: in `getChatThread` a code turn's `text` is "Code entered", a form turn's "Details sent", a choice turn's the option's label from the card it answered (the stored option string when that card is not in the thread), never "[code entered]", "[details submitted]" or null; the texts come from `policy/texts.py`, and the stored `messages` rows stay redacted as AC-8 requires — verify: `tests/api/test_chat.py::test_history_display_texts` — evidence: three rows with the three texts; the `messages` rows still hold "[code entered]" and "[details submitted]".

**AEA-40-5** (staff audit E1, A3; AC-11 already proves the append and its single commit)
- [ ] AC-<next> [invariant] The relayed customer message is a valid case event that names nobody: the `customer_message` payload AC-11 writes validates against the OpenAPI `CaseEvent` member for that type (through `assert_sse_frames_match` on a frame built from it), carries the STORE-redacted text and the message's `message_id` and `at`, and its customer speaker has `display_name: null` — verify: `tests/services/test_turn.py::test_customer_message_payload_valid_and_unnamed` — evidence: the frame validates; `display_name` null; a synthetic card number in the message is stored and relayed as "[card number removed]".

**AEA-40-6** (coordinator update: per-route contract cases)
- [ ] AC-<next> [contract] `tests/contract/cases/chat.py` holds the server cases for `startChatSession`, `getChatThread` and `submitTurn`: preconditions (login, a started thread), every named request example, and each documented error status the route can produce (401, 404 `SESSION_NOT_FOUND`, 410 `SESSION_ENDED`, 409 `TURN_IN_PROGRESS`, 400, 503) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "startChatSession or getChatThread or submitTurn" -rs` once AEA-59's runner is merged — evidence: one pass per case; a skip only as `not bound: <name>` naming a provider of a later issue (`run_graph`, AEA-51).

**AEA-40-7** (customer audit A-1; §0a "J-1 runs in two stages") — *Replaces AC-15*
- [ ] AC-<next> [journey] Extends J-1 and J-9 (slice plan §0a journey map): J-1, login → `startChatSession` → one turn → reload resumes the same thread through `getChatThread`, whose `turns` start with the greeting and hold the customer turn and its reply in order (AEA-40-1), with no second `startChatSession`; J-9, the `TURN_TIMEOUT`, `BUSY` and `RATE_LIMITED` notices reached through the real server; asserting what the user sees and the stored `conversations`, `messages` and `turns` rows, in `tests/journeys/j1/test_aea_40.py` and `tests/journeys/j9/test_aea_40.py` with the scripted model adapter — verify: `uv run pytest -m journey tests/journeys/j1/test_aea_40.py tests/journeys/j9/test_aea_40.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57's harness (J-1) and AEA-51 (the turn steps and J-9) land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-40.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 (`integrated-journeys.md` §4).

### AEA-41 (CON-3 chat event stream) — wave 2

**AEA-41-1** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/events.py` holds the server case for `streamChatEvents`: a started thread, a first connect with no `Last-Event-ID`, a resume with one, and each documented error status (401, 404), every frame checked with `assert_sse_frames_match` — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k streamChatEvents -rs` once AEA-59's runner is merged — evidence: the case passes with its frame count printed.

**AEA-41-2** (customer audit D-2) — *If Innocent picks B in Decision 4 (add 410 to `streamChatEvents` in the OpenAPI)*; under A (recommended) AC-7 and ND-1 stand as written
- [ ] AC-<next> [failure/refusal] *Replaces AC-7:* a connect to this session's ended thread answers 410 `SESSION_ENDED` with `details.reason` (`demo_reset` or `chat_closed`), as `owned_thread` decides; another session's or an unknown thread answers the identical 404 — verify: `tests/api/test_events.py::test_ended_thread_stream_410` with `assert_response_matches(response, "streamChatEvents")` against the amended OpenAPI — evidence: the 410 body validates; the two 404 bodies differ only in `request_id`.

### AEA-42 (CON-4 person request, CON-5 follow-up) — wave 2

**AEA-42-1** (customer audit A-2, B-1)
- [ ] AC-<next> [invariant] The CON-4 turn row is history-ready and a second press can draw the card: the row's stored response is the `PersonRequestOutcome` body exactly as returned (`result`, `block`, `settled`) and its trace `gate_result` is `person_requested`, so AEA-40's `thread()` can show it; a second press with a **new** `turn_id` on a thread with an open case answers `already_open` whose `block` is the open case's card (the same reference and promise text as the first answer) — verify: `tests/services/test_person_request.py::test_stored_outcome_is_history_ready` and `::test_already_open_block_names_existing_case` — evidence: the stored JSON equals the first response; the second response's `block.reference` and promise equal the first's.

**AEA-42-2** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/handoff.py` holds the server cases for `requestPerson` and `saveFollowUp`: preconditions (a thread; a thread with an open case; an unverified thread), every named request example, and each documented error status the route can produce (`requestPerson`: 400, 401, 404, 410, 503 `HANDOFF_FAILED`; `saveFollowUp`: 400, 401, 404, 409 `NOT_ALLOWED_IN_STATE` with `state` `no_open_case` and `not_verified`, 410) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "requestPerson or saveFollowUp" -rs` once AEA-59's runner is merged — evidence: one pass per case; skips only as `not bound: <name>` for a later issue's provider.

### AEA-43 (CON-6…CON-9 demo routes) — wave 2

**AEA-43-1** (customer audit A-6, with AEA-27-1)
- [ ] AC-<next> [invariant] The route never sends dots as an active code: a message the service returns with `code=None` is serialised with `status: "expired"`, code `"······"` and `INBOX_CODE_GONE`, even if a double returns it as `active`; a held code keeps `active` — verify: `tests/api/test_demo_routes.py::test_inbox_code_gone_is_expired` — evidence: the two bodies validate against `listDemoInbox`; statuses `expired` and `active`.

**AEA-43-2** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/demo.py` holds the server cases for `listDemoInbox`, `getStaffing`, `setStaffing`, `getDemoClock` and `resetDemo`: preconditions, every named request example, and each documented error status the routes can produce (429 on the three reads that document it, 400 on `setStaffing` and `resetDemo`, 503 `RESET_IN_PROGRESS`, 409 and 500 on `resetDemo`) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "listDemoInbox or Staffing or getDemoClock or resetDemo" -rs` once AEA-59's runner is merged — evidence: one pass per case.

### AEA-44 (staff sessions, role switch, flags) — wave 2

**AEA-44-1** (staff audit B1, B2; shell audit B1, B5)
- [ ] AC-<next> [failure/refusal] A tab can always find out its current role: `getSession` and `listDemoRoles` never answer 403 for any role, `role_reset` included; after a switch made by a second client on the same cookie, the first client's next `getSession` returns the new role; after a reset, **every** staff call from either client (three in a row, through a `require_staff`-guarded route) answers 403 `ROLE_NOT_ALLOWED` `reason: "role_reset"` until `switchRole`, while `getSession` answers 200 role `customer` throughout — verify: `tests/api/test_staff_session_routes.py::test_role_reread_after_switch_and_reset` — evidence: the call sequence with statuses and `details.reason` printed.

**AEA-44-2** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/staff_session.py` holds the server cases for `getSession`, `listDemoRoles` and `switchRole`: preconditions (a login; each role), every named request example (`TO_*`), and each documented error status the routes can produce (401; 400 and 503 `RESET_IN_PROGRESS` on `switchRole`) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "getSession or listDemoRoles or switchRole" -rs` once AEA-59's runner is merged — evidence: one pass per case.

### AEA-45 (staff case routes) — wave 2

**AEA-45-1** (staff audit A1, A2)
- [ ] AC-<next> [invariant] The routes add, drop and rewrite nothing in a case view: `allowed_actions` and every display field of `QueueRow`, `CaseSummary` and `CaseDetail` (`reason`, `priority.word`, `due_label`, `age_label`, `follow_up_short`, `queued_at`, `identity.line`, `BriefItem.source_ids`, `CaseSource.source_id`, `version_label`) reach the client exactly as the `CaseService` double returns them, for each staff role; the owner's `[]` comes from the double, not from the route — verify: `tests/api/test_staff_cases_routes.py::test_views_pass_through_unchanged` (a double returning distinctive values per field and per role) — evidence: the response JSON equals the double's serialised view for representative, supervisor and owner.

**AEA-45-2** (staff audit B5) — *If Innocent picks A in Decision 2*
- [ ] AC-<next> [invariant] `getCase` returns `events.last_event_id` from `CaseService.detail` unchanged and validates against the amended `CaseDetail` — verify: `tests/api/test_staff_cases_routes.py::test_case_detail_carries_last_event_id` with `assert_response_matches(response, "getCase")` — evidence: the field present and equal to the double's value.

**AEA-45-3** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/staff_cases.py` holds the server cases for `getQueue`, `getCase`, `applyCaseAction`, `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag` and `getOversight`: preconditions (a role per operation's x-roles; a seeded case reference), every named request example, and each documented error status the routes can produce (401, 403 `ROLE_NOT_ALLOWED`, 404, 400, 409 `VERSION_CONFLICT` / `CASE_ALREADY_CLAIMED` / `NOT_ALLOWED_IN_STATE`, 422 `REASON_REQUIRED` / `WAKE_UP_REQUIRED` / `OUTCOME_REQUIRED`) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "Queue or Case or Contact or Flag or Oversight" -rs` once AEA-59's runner is merged — evidence: one pass per case; skips only as `not bound: <name>` for a later issue's provider.

### AEA-46 (live takeover, CON-21 case stream) — wave 2

**AEA-46-1** (staff audit A4, high; rule (i))
- [ ] AC-<next> [invariant] Live actions leave the case alone: after `join`, `send`, `hand_back` and `close` on a claimed case at version n, the case's `version` is still n and its `lifecycle` unchanged, `case:<ref>` receives only `controller_changed` (join, hand back) and `chat_closed` (close) and no `case_changed`, and a CON-13 `resolve` sent afterwards with `expected_version` n is accepted — verify: `tests/services/test_live_chat.py::test_live_actions_keep_case_version` (temp SQLite; `CaseService` double honouring cases.md §5, or AEA-29's when merged) — evidence: version n before and after; the case-stream event types printed; the resolve accepted.

**AEA-46-2** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/staff_live.py` holds the server cases for `liveChatAction` (join, send, hand_back, close on a claimed live-queued case) and `streamCaseEvents` (first connect and resume), with each documented error status the routes can produce (401, 403, 404, 409 `NOT_LIVE` / `CASE_ALREADY_CLAIMED`, 400 field `text`), frames checked with `assert_sse_frames_match` — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "liveChatAction or streamCaseEvents" -rs` once AEA-59's runner is merged — evidence: one pass per case.

### AEA-47 (CON-8 clock advance) — wave 2

**AEA-47-1** (staff audit A7)
- [ ] AC-<next> [negative] The response carries exactly the OpenAPI keys: an `advanceDemoClock` 200 body has the keys `now`, `label` and `became_overdue` and no others, although `ClockAdvanced` (staff.md §8) also carries `date_label`; the OpenAPI sets no `additionalProperties: false`, so this test, not the schema check, catches drift — verify: `tests/api/test_staff_clock_routes.py::test_advance_response_keys_exact` — evidence: the sorted key list printed equals `["became_overdue", "label", "now"]`.

**AEA-47-2** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/staff_clock.py` holds the server case for `advanceDemoClock` (supervisor; `plus_1h`, `plus_4h`, `next_business_morning`) and each documented error status the route can produce (400 field `step`, 401, 403 for the representative, 503 `RESET_IN_PROGRESS`) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k advanceDemoClock -rs` once AEA-59's runner is merged — evidence: one pass per case.

### AEA-48 (reads API) — wave 2

**AEA-48-1** (shell audit A1, high)
- [ ] AC-<next> [failure/refusal] The read schemas refuse values the pages would misreport: in `web/schemas/reads.py`, `unit` is `Literal["count", "ms", "share"]` on `Measure` and `Tile`; a `share` value must lie in [0, 1]; every `EvalMeasure.value` lies in [0, 1]; and (`id`, `label`) pairs are unique within one response. A `MetricsReads` mapping that breaks any of these is a server bug: 500 and one log line naming the field and rule, never the value (the OpenAPI types `unit` as a free string, so this is stricter than the contract and still valid against it) — verify: `tests/api/test_reads_routes.py::test_unit_vocabulary_enforced` — evidence: three valid mappings pass; `unit: "per 100 turns"`, a share of 75 and a duplicate (`id`, `label`) each answer 500 naming the field.

**AEA-48-2** (coordinator update)
- [ ] AC-<next> [contract] `tests/contract/cases/reads.py` holds the server cases for `getOwnerMetrics`, `getMonitoring` and `getLatestEval`: preconditions (owner or supervisor for the first; any role for the others), and each documented error status the routes can produce (401, 403 on `getOwnerMetrics`, 429 and 503 on the other two) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "getOwnerMetrics or getMonitoring or getLatestEval" -rs` once AEA-59's runner is merged — evidence: one pass per case; skips only as `not bound: get_metrics_reads` until AEA-53.

### AEA-49 (serve `dist`) — wave 2

**AEA-49-1** (shell audit C4)
- [ ] AC-<next> [invariant] Cache rules and missing files: `index.html` and every SPA-fallback response carry `Cache-Control: no-cache`; files under `/assets/` carry `Cache-Control: public, max-age=31536000, immutable`; a missing file under `/assets/` or `/fonts/` answers 404 (never `index.html`, which a browser would try to run as a script), signed in and, under WEB-1 option A, signed out — verify: `tests/web/test_frontend.py::test_cache_headers_and_missing_asset_404` (fixture dist) — evidence: the headers printed per path; `/assets/missing.js` answers 404 in both states.

**AEA-49-2** (customer audit C-1, shell audit C1) — *Replaces AC-3's public list according to Innocent's answer in Decision 1*; under A (recommended) AC-3 stands as written
- [ ] AC-<next> [failure/refusal] *(If B)* Without `mhc_session`, only `GET /login` answers 200, with the UX session's self-contained login page (styles and script inline, no `/assets/` reference); `/assets/*`, `/fonts/*` and every other page path answer `303` to `/login?return_to=<path+query>&reason=none`; `/api/*` answers JSON 401 — verify: `tests/web/test_frontend.py::test_public_paths_option_b` — evidence: status per path printed; the login page body contains no `/assets/` URL. *(If C)* Without `mhc_session`, every page path answers `index.html` (200) and only `/api/*` is gated (JSON 401); AC-9's server-303 assertions move to the browser (AEA-58 AC-2 asserts the app reaching `/login?return_to=…&reason=…` after a 401) — verify: `tests/web/test_frontend.py::test_public_paths_option_c` — evidence: status per path printed.

### AEA-50 (deploy image) — wave 3

**AEA-50-1** (shell audit F2, F3, F4; customer audit F-1). Also change the *What to build* line "`web` (… `npm ci && npm run build`, reading `apps/web` only; DAT-21)" to "reads `apps/web` and the one file `docs/ux/03-structure/ui-contracts.openapi.yaml`, writes nothing back".
- [ ] AC-<next> [invariant] The `web` stage builds exactly as the UX session's recipe says: it copies `apps/web/` and the one file `docs/ux/03-structure/ui-contracts.openapi.yaml` to the same relative paths, uses the Node version `apps/web/package.json` `engines.node` names (or the recipe's, until `engines` exists), runs `npm ci` with dev dependencies (no `--omit=dev`, no `NODE_ENV=production` before the build), then `npm run build && npm run check:dist` with no `--mode`, and copies only `dist/` into the runtime image — verify: `docker build --target web .` then the AC-2 check on the full image — evidence: the build log shows `prebuild` regenerating from the copied spec and `check:dist` passing; `/app/apps/web/dist/index.html` present; no `node_modules` and no OpenAPI file in the runtime image.

### AEA-52 (integration B: staff and demo) — wave 3

**AEA-52-1** (staff audit A1, high)
- [ ] AC-<next> [invariant] `allowed_actions` holds at the real routes: on the seeded MHC-C-0007 and on a WP-7 case taken through claim → join, `getCase` as representative, supervisor and owner returns lists for which every listed action, sent next, is accepted, and one unlisted action of each operation is refused; the owner's list is `[]`; the supervisor's never holds a live-chat or contact key — verify: `tests/integration/test_staff_allowed_actions.py::test_listed_iff_accepted_per_role` — evidence: per role, the list and each action's accept or refuse result printed.

**AEA-52-2** (staff audit A4) — *Replaces in AC-4* "the staff CON-21 stream delivers `controller_changed` and `case_changed`" *with:*
"the staff CON-21 stream delivers `controller_changed` on join and on hand back and **no** `case_changed` for any live action (a `case_changed` arrives only after a CON-13 action, such as the resolve that follows); a `resolve` sent after hand back with the `version` read before the join is accepted".

**AEA-52-3** (staff audit E1, high)
- [ ] AC-<next> [invariant] The relayed customer message is the same on both staff surfaces: with Riley joined, a customer `submitTurn` produces one `customer_message` frame on CON-21 whose payload equals, field for field, the line `getCase` then returns in `conversation` for that `message_id` (customer `display_name` null); the customer's own `getChatThread` shows that message and Riley's reply in order — verify: `tests/integration/test_staff_streams.py::test_relayed_message_same_on_stream_and_case_view` — evidence: the two JSON objects printed and equal.

**AEA-52-4** (customer audit A-1)
- [ ] AC-<next> [invariant] The customer's reload after a takeover shows it: after join, a staff `send` and hand back, `getChatThread` holds in order the joined and paused lines, Riley's message (`speaker.kind: representative`, `display_name: "Riley"`) and the resumed line, and its `last_event_id` equals the newest event id of the thread's stream, so a CON-3 connection from it receives no frame already shown — verify: `tests/integration/test_staff_streams.py::test_reload_after_takeover_shows_staff_lines` — evidence: the entry list printed; 0 replayed frames.

**AEA-52-5** (staff audit A2, A4, E1; customer audit A-1) — *Replaces AC-15*
- [ ] AC-<next> [journey] **J-6, J-7, J-8** (slice plan Amendment 1, landed here): `tests/journeys/j6/test_aea_52.py` (WP-7 and WP-8: escalation → case → staff queue → case opened with the eight-heading brief and promise, every brief `source_ids` entry resolving to a source of the case), `j7/test_aea_52.py` ("Talk to a person" and live takeover: staff joins the same chat, the relayed customer line identical on CON-21 and in `getCase`, Riley's lines in the customer's `getChatThread` after a reload, hand back, then resolve with the pre-join version accepted), `j8/test_aea_52.py` (customer ↔ staff role switch seen by a second client on the same cookie, a reset sending both clients' staff calls to `role_reset` until a switch, refresh, signed-out and expired session), each asserting what the user sees **and** what is stored on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6 tests/journeys/j7 tests/journeys/j8` plus `docs/testing/journeys/<date>-AEA-52.md` (integrated-journeys §4) — evidence: pass per journey at level `integrated with a scripted model`; the record's fields filled.

### AEA-53 (metrics reader) — wave 3

**AEA-53-1** (shell audit A1, high)
- [ ] AC-<next> [invariant] One unit vocabulary on all three reads: every `Measure.unit` and `Tile.unit` is `count`, `ms` or `share`; a `share` value is a 0–1 fraction, never 0–100; every `EvalMeasure.value` is a 0–1 ratio; M-24 failures go out as a count with numerator and denominator (as the OpenAPI example does), never as "per 100 turns"; and every mapping passes AEA-48's `web/schemas/reads.py` models — verify: `tests/unit/services/test_metrics_reader.py::test_units_and_scales` over the J-10 run's rows — evidence: the set of units printed is a subset of {count, ms, share}; the minimum and maximum of every share value lie in [0, 1].

**AEA-53-2** (shell audit A3)
- [ ] AC-<next> [invariant] Measures can be told apart: (`id`, `label`) pairs are unique within each of CON-18, CON-19 and CON-20; where DO-7 splits one M-n (M-27 per reason, M-1 per topic) the split is named in the `label` and the `id` stays the registry's M-n (STF-18) — verify: `tests/unit/services/test_metrics_reader.py::test_measure_keys_unique` — evidence: 0 duplicate pairs across the three responses.

**AEA-53-3** (shell audit A4)
- [ ] AC-<next> [invariant] The CON-19 health tiles are a fixed, listed set: the plan lists each tile's position, label and unit (volume, failures, latency p50, latency p95, `scheduler_last_run`, and any other), the test asserts exactly that list in that order on an empty database and after the J-10 run, and the list is copied as one note into `docs/plans/ux-join/` so the UX session keys SCR-10's empty state on the volume tile — verify: `tests/unit/services/test_metrics_reader.py::test_health_tiles_fixed_list` — evidence: the list printed twice, equal.

**AEA-53-4** (shell audit A1) — *Adds to AC-9 (J-10), before "— verify":* "and that every unit on the three pages is `count`, `ms` or `share`, with each share's value between 0 and 1 and equal to its numerator over its denominator".

### AEA-55 (UI integration against the real backend) — wave 5

**AEA-55-1** (shell audit J1, C6, C7, G5)
- [ ] AC-<next> [invariant] The proxy chain is probed before the suite runs, and each result is recorded: (1) a chat stream and a case stream opened through `prism proxy … --errors` deliver their first frame or heartbeat within 20 s; if not, both stream paths are routed straight to the backend in the run configuration (`vite.config.ts` proxy, a configuration change this issue may make) and the exception is written down; (2) a cookieless `getChatThread` through the chain answers the backend's own `ApiError` 401 `UNAUTHENTICATED`, not a Prism body; if not, Prism's request validation is changed so the backend answers, and recorded; (3) the backend runs with `MERIDIAN_COOKIE_SECURE=false` over local http; (4) the report states that the dev-mode `[contract drift]` signal is mock-only and that AC-3's Prism log is the real contract check — verify: the run record `docs/ux/05-verify/` report section or `docs/testing/journeys/YYYY-MM-DD-AEA-55.md` — evidence: the four results, each with its outcome.

**AEA-55-2** (shell audit G1; risk 2 of the join plan)
- [ ] AC-<next> [negative] No dev parameter carries a real-backend result: tests the UX session tagged `@mock-only` are recorded `NOT_RUN` with their reason, never as passed; no request in the run carries `signedin`, `role`, `scenario`, `staffing`, `ex` or `delay` query parameters; every sign-in goes through SCR-12 with the demo pair from the environment — verify: the Playwright report and the Prism proxy log — evidence: the `NOT_RUN` list with reasons; a grep of the proxy log for those parameters prints nothing.

### AEA-58 (browser journeys) — wave 3

**AEA-58-1** (customer audit G-1, G-3; shell audit J3)
- [ ] AC-<next> [invariant] Selectors come only from the UX session's contract: each selector in the one module cites its row in `docs/plans/ux-join/selectors.md` and that file's revision; no test file holds a selector string of its own; a state the contract lacks is reported `blocked-on UX selector <state>` for that step only, never replaced by a copy-text selector — verify: `grep -rnE "locator\(|get_by_" tests/journeys --include=*.py` outside the module prints nothing; a read of the module — evidence: the empty grep; a row reference on every selector line.

**AEA-58-2** (customer audit A-1) — *Adds to AC-3, before "— verify":* "(the greeting after the reload depends on AEA-40-1; until it merges, that one assertion is reported *Blocked by* AEA-40, never passed or dropped)".

**AEA-58-3** (customer audit C-3) — *If Innocent picks B in Decision 5 (a separate throttle message)*; under A AC-6 stands
- [ ] AC-<next> [failure/refusal] *Replaces AC-6:* J-9 rate-limited login in the browser, on its own server instance: a wrong pair shows SCR-12's refusal line with the password cleared and the username kept; after `Limits.web.login_rejects_per_ip` rejects (read from `Limits`), the **right** pair answers `429 LOGIN_RATE_LIMITED` and the page shows the throttle line UI_CONTRACTS CON-22 gives, through `[data-login-message=rate-limited]`, and no `mhc_session` cookie is set — verify: `tests/journeys/j9/test_aea_58.py::test_rate_limited_login_throttle_line` — evidence: the 401s then the 429 printed with the two different lines. Level: `integrated with a scripted model`.

**AEA-58-4** (Decision 6) — *Applied after Innocent's answer; adds to AC-5 (sign out and back), before "— verify":* *(If A, start fresh)* "after signing in again, SCR-1 starts a new chat (one new `startChatSession`), and the earlier `thread_id` answers 404 `SESSION_NOT_FOUND` to the new session"; *(If B, resume)* "after signing in again in the same tab, SCR-1 shows the same conversation (`getChatThread` for the earlier `thread_id` answers 200 to the new session) and no new `startChatSession` is sent".

### AEA-59 (contract boundary checks) — wave 2

**AEA-59-1** (shell audit S3, high)
- [ ] AC-<next> [invariant] The UX session's dev fixtures pass the same checks as the OpenAPI's examples: when the dump the UX session names in `docs/plans/ux-join/selectors.md` exists (one record per `{operationId, status, name, body}`), every body passes `assert_response_matches` for its operation and status and every stream event `assert_sse_frames_match`, read only; when it does not exist yet, the check is skipped with `ux fixture dump missing: <path>`, and `CONTRACT_STRICT=1` fails it — verify: `uv run pytest tests/contract/test_openapi_fixtures.py -k ux_dump -rs` — evidence: the count of records checked, or the named skip.

**AEA-59-2** (coordinator update; §0a "AEA-59 has no dependency on the harness") — *only if the rewritten AEA-59 does not already say so*
- [ ] AC-<next> [invariant] Server cases live in one file per route issue: `tests/contract/test_openapi_server.py` collects `tests/contract/cases/*.py` (`auth`, `chat`, `events`, `handoff`, `demo`, `staff_session`, `staff_cases`, `staff_live`, `staff_clock`, `reads`), each written by its route issue; this issue writes the runner, the case format and a documented example case; the completeness check counts cases across all files and names, for each missing operationId, the file that should hold it — verify: `uv run pytest tests/contract/test_openapi_server.py -rs` — evidence: the case count per file printed; missing operationIds listed with their file.

### AEA-62 (browser journeys for integrated capabilities) — wave 4

**AEA-62-1** (shell audit B5)
- [ ] AC-<next> [invariant] The real `SessionInfo` is shown for every role: switching through Customer, Representative, Supervisor and Owner shows, for each, the header name and the marked role that `getSession` returns (`display_name` "Customer (demo)", "Riley, demo representative", "Demo supervisor", "Demo business owner"), never a value from the mock's `switchRole` body — verify: `tests/journeys/j8/test_aea_62.py::test_j8_header_for_four_roles` — evidence: four header readings beside four `getSession` bodies. Level: `integrated with a scripted model`.

**AEA-62-2** (staff audit B1, B2; applied once the UX session's B1/B2 fixes are in `dist`)
- [ ] AC-<next> [failure/refusal] A role change made elsewhere reaches an open staff tab: with SCR-6 open in tab A as the representative, switching to Customer in tab B and then focusing tab A shows the role panel with `[data-reason=wrong_role]` and no case data; a reset run from tab B then shows `[data-reason=role_reset]` in tab A on its next staff call, until a role switch — verify: `tests/journeys/j8/test_aea_62.py::test_j8_role_change_elsewhere` — evidence: tab A's panel reasons and the 403 bodies printed; screenshots of both panels. Level: `integrated with a scripted model`.

**AEA-62-3** (Decision 6) — *Applied after Innocent's answer; adds to AC-15, before "— verify":* the same sentence as AEA-58-4 for the answer he picks, asserted from SCR-6's sign-out and SCR-1's re-entry.

---

## 3. The `[journey]` criterion for every build-loop ticket

**The 56 build-loop tickets** (slice plan §0: 62 tickets, minus direct AEA-07, 08, 25, 54 and human AEA-09, 56). Journey ids come
from the §0a map (*First landed by* / *Extended by*); ids marked *(proposed)* are additions the join audits suggest, which the
applying pass may also add to the map's *Extended by* column (the slice plan is not edited here).

**Already present (15), keep as they are unless §2 says otherwise:**

| Ticket | Criterion | Journeys | §2 change |
|---|---|---|---|
| AEA-37 | AC-11 | J-5 | — |
| AEA-38 | AC-14 | J-2 | — |
| AEA-39 | AC-15 | J-3, J-4 | — |
| AEA-40 | AC-15 | J-1, J-9 | Replaced by AEA-40-7 |
| AEA-49 | AC-9 | J-1 (HTTP) | Follows Decision 1 (AEA-49-2) |
| AEA-50 | AC-16 | none | — |
| AEA-51 | AC-32 | lands J-2, J-3, J-4, J-5, J-9 (and J-1's turn steps, §0a) | — |
| AEA-52 | AC-15 | lands J-6, J-7, J-8 | Replaced by AEA-52-5 |
| AEA-53 | AC-9 | lands J-10 | Extended by AEA-53-4 |
| AEA-57 | AC-8…AC-10 | lands J-1 (API) | — |
| AEA-58 | AC-3, AC-6 | J-1, J-9 (browser) | AEA-58-2, -3 |
| AEA-59 | AC-16 | J-1 | — |
| AEA-60 | AC-13 | J-5, J-9 | — |
| AEA-61 | AC-5 | J-2, J-3, J-5 (scripted half) | — |
| AEA-62 | AC-2…AC-15 | lands browser legs of J-2, J-3, J-6, J-8 | AEA-62-1…3 |

**The four text patterns** (each row below is one of them, filled in):

- **A — extends** (wave 2 tickets whose code a journey runs): "Extends J-n (…): <the step>; asserting what the user sees and what
  is stored, in `tests/journeys/j<N>/test_aea_<NN>.py` … *Blocked by* the harness and the landing ticket until they merge."
- **C — runs none yet** (waves 0–1: the harness is AEA-57, wave 2): names the journeys that will exercise the code, so the seam
  audit knows where to look; level `mock-tested`, *Blocked by* AEA-57.
- **D — no journey path** (code a deterministic journey never reaches: provider adapters, tracing, eval): says where it is proved
  instead.
- **Special:** AEA-01 (owns the marker and the affected-journey command) and AEA-55 (runs all journeys).

**To add (41):**

| Ticket | Wave | Journeys | Pattern |
|---|---|---|---|
| AEA-01 | 0 | — (owns the marker) | special |
| AEA-02 | 0 | J-1…J-10 | C |
| AEA-03 | 0 | J-1, J-5, J-6, J-9 | C |
| AEA-04 | 0 | J-1, J-3 | C |
| AEA-05 | 0 | J-5, J-7 | C |
| AEA-06 | 0 | — | D |
| AEA-10 | 1 | J-1…J-10 | C |
| AEA-11 | 1 | — | D |
| AEA-12 | 1 | J-3, J-5, J-7 | C |
| AEA-13 | 1 | J-3, J-4 | C |
| AEA-14 | 1 | J-4, J-5, J-6 | C |
| AEA-15 | 1 | J-2 | C |
| AEA-16 | 1 | J-2 | C |
| AEA-17 | 1 | — | D |
| AEA-18 | 1 | — | D |
| AEA-19 | 1 | — | D |
| AEA-20 | 1 | J-1…J-5, J-9 | C |
| AEA-21 | 1 | J-1…J-5, J-9 | C |
| AEA-22 | 1 | J-2, J-3 | C |
| AEA-23 | 1 | J-1, J-8 | C |
| AEA-24 | 1 | — | D |
| AEA-26 | 2 | J-9 (proposed) | A |
| AEA-27 | 2 | J-3 (proposed) | A |
| AEA-28 | 2 | J-3, J-4 | A |
| AEA-29 | 2 | J-6; J-7 (proposed) | A |
| AEA-30 | 2 | J-7, J-6 (proposed) | A |
| AEA-31 | 2 | J-8 (proposed) | A |
| AEA-32 | 2 | J-10 (proposed) | A |
| AEA-33 | 2 | J-2 | A |
| AEA-34 | 2 | J-3 | A |
| AEA-35 | 2 | J-2 | A |
| AEA-36 | 2 | J-5 | A |
| AEA-41 | 2 | J-9; J-7 (proposed) | A |
| AEA-42 | 2 | J-7 | A |
| AEA-43 | 2 | J-3, J-8 (proposed) | A |
| AEA-44 | 2 | J-8 | A |
| AEA-45 | 2 | J-6 | A |
| AEA-46 | 2 | J-7 | A |
| AEA-47 | 2 | J-6 (proposed) | A |
| AEA-48 | 2 | J-10 | A |
| AEA-55 | 5 | J-1…J-10 (runs all) | special |

**The criteria, ready to copy:**

**AEA-01** (— (owns the marker))

- [ ] AC-<next> [journey] The journey gate exists before any journey does: the `journey` marker is registered, `uv run pytest -m journey --collect-only -q` exits 0 on the skeleton, and the affected-journey command run on this diff selects 0 journeys, prints "0 journeys affected" and exits 0; the record `docs/testing/journeys/YYYY-MM-DD-AEA-01.md` states level `mock-tested` and *Blocked by* AEA-57 (`integrated-journeys.md` §4) — verify: both commands and the record — evidence: their output; the record's Level and Blocked-by fields.

**AEA-02** (J-1…J-10)

- [ ] AC-<next> [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-02.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-10 (every path imports the domain types and ports) as the journeys that will exercise this code once AEA-57, AEA-51, AEA-52 and AEA-53 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.

**AEA-03** (J-1, J-5, J-6, J-9)

- [ ] AC-<next> [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-03.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1 (the greeting), J-5 (the safety instruction), J-6 (the promise text) and J-9 (the notice texts) as the journeys that will exercise this code once AEA-57, AEA-51 and AEA-52 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.

**AEA-04** (J-1, J-3)

- [ ] AC-<next> [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-04.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1 and J-3 (the stored "[code entered]" and "[details submitted]") as the journeys that will exercise this code once AEA-57 and AEA-51 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.

**AEA-05** (J-5, J-7)

- [ ] AC-<next> [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-05.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-5 (safety words) and J-7 ("talk to a person" words) as the journeys that will exercise this code once AEA-51 and AEA-52 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.

**AEA-06** (—)

- [ ] AC-<next> [journey] No deterministic journey reaches this code (the eval cases are read by AEA-24's harness and the E-runs, never by a journey, and the sealed held-out split never may be), so this issue extends none: the record `docs/testing/journeys/YYYY-MM-DD-AEA-06.md` says so and names where it is proved instead (AEA-24's tests and the Stage 9 E-runs) — verify: the record — evidence: the record's Level and Blocked-by fields.

**AEA-10** (J-1…J-10)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-10.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-10 (every journey reads and writes the working copy) as the journeys that will exercise this code once AEA-57, AEA-51, AEA-52 and AEA-53 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-11** (—)

- [ ] AC-<next> [journey] No deterministic journey reaches this code (`tests/fakes/` serves unit tests; journeys use AEA-57's scripted adapter at the provider boundary), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-11.md` says so and names where it is proved instead (the unit tests that import the fakes) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.

**AEA-12** (J-3, J-5, J-7)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-12.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-3 (code and form intake), J-5 (the gate decision) and J-7 (the person request) as the journeys that will exercise this code once AEA-51 and AEA-52 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-13** (J-3, J-4)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-13.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-3 (zones and windows) and J-4 (the 24-hour rule and fee) as the journeys that will exercise this code once AEA-51 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-14** (J-4, J-5, J-6)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-14.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-4, J-5 and J-6 (promise rows, priorities, the escalation decision) as the journeys that will exercise this code once AEA-51 and AEA-52 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-15** (J-2)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-15.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-2 (the completion and fact checks on grounded answers) as the journeys that will exercise this code once AEA-51 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-16** (J-2)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-16.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-2 (the ingested KB files, stale twins excluded) as the journeys that will exercise this code once AEA-51 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-17** (—)

- [ ] AC-<next> [journey] No deterministic journey reaches this code (journeys replace the provider call with the scripted adapter), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-17.md` says so and names where it is proved instead (`tests/contract/test_anthropic_adapter.py` and AEA-61's live smoke) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.

**AEA-18** (—)

- [ ] AC-<next> [journey] No deterministic journey reaches this code (journeys replace the provider call with the scripted adapter), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-18.md` says so and names where it is proved instead (`tests/contract/test_jev_adapter.py` and AEA-61's live smoke) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.

**AEA-19** (—)

- [ ] AC-<next> [journey] No deterministic journey reaches this code (journeys run with `NullTraceSink`), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-19.md` says so and names where it is proved instead (this issue's own tests, CAP-9 and AEA-61's trace records) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.

**AEA-20** (J-1…J-5, J-9)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-20.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-5 and J-9 (the gateway runs above the scripted adapter) as the journeys that will exercise this code once AEA-57 and AEA-51 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-21** (J-1…J-5, J-9)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-21.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-5 and J-9 (the graph spine, routers and compose) as the journeys that will exercise this code once AEA-57 and AEA-51 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-22** (J-2, J-3)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-22.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-2 and J-3 (tool dispatch, the verified guard, lookup-log rows) as the journeys that will exercise this code once AEA-51 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-23** (J-1, J-8)

- [ ] AC-<next> [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-23.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1 (the login, the guard redirect, the 401s) and J-8 (role refusals); AEA-57 is blocked by this issue, so it cannot run them itself as the journeys that will exercise this code once AEA-57 and AEA-52 land, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".

**AEA-24** (—)

- [ ] AC-<next> [journey] No deterministic journey reaches this code (the eval harness drives the HTTP API for E-runs, which are not journeys), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-24.md` says so and names where it is proved instead (its own tests and the Stage 9 runs) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.

**AEA-26** (J-9 (proposed))

- [ ] AC-<next> [journey] Extends J-9 (slice plan §0a journey map; J-9 is a proposed addition to the map, from the join audits): a turn while the `SpendGuard` reports the day's cap reached shows the `SPEND_CAP_REACHED` notice with the person action, and the stored `turn` row is `degraded_handoff` / `spend_cap` with no `spend_ledger` row of its own; asserting what the user sees and what is stored, in `tests/journeys/j9/test_aea_26.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j9/test_aea_26.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-26.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).

**AEA-27** (J-3 (proposed))

- [ ] AC-<next> [journey] Extends J-3 (slice plan §0a journey map; J-3 is a proposed addition to the map, from the join audits): J-3's identity step: the code sent to SCR-2's inbox (`listDemoInbox`) is read there, entered in the chat and verifies the customer; after a restart of the server on the same working copy the message reads `expired` with no code (customer audit A-6); the stored code row holds only the HMAC; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_27.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_27.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-27.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).

**AEA-28** (J-3, J-4)

- [ ] AC-<next> [journey] Extends J-3 and J-4 (slice plan §0a journey map): J-3, the booking re-reads the slot and stores the appointment, one `actions` row and its lookup row in one transaction; J-4, a change inside 24 hours leaves the appointment row unchanged and stores a change request; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_28.py` and `tests/journeys/j4/test_aea_28.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_28.py tests/journeys/j4/test_aea_28.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-28.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).

**AEA-29** (J-6; J-7 (proposed))

- [ ] AC-<next> [journey] Extends J-6 and J-7 (slice plan §0a journey map; J-7 is a proposed addition to the map, from the join audits): J-6, the escalated case appears in `getQueue` and `getCase` with eight headings, the policy promise, an `allowed_actions` list the server accepts for the viewing role, and every brief `source_ids` entry resolving to a source of the same case (staff audit A1, A2); J-7, after join, send and hand back the case `version` is unchanged (A4); asserting what the user sees and what is stored, in `tests/journeys/j6/test_aea_29.py` and `tests/journeys/j7/test_aea_29.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6/test_aea_29.py tests/journeys/j7/test_aea_29.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-29.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-30** (J-7, J-6 (proposed))

- [ ] AC-<next> [journey] Extends J-7 and J-6 (slice plan §0a journey map; both are proposed additions to the map, from the join audits): J-7, with staffing switched on (`setStaffing`) a person request is live-queued, and switching it off converts the case and writes `shift_ended` to the chat; J-6, advancing the demo clock past a case due puts the case in the Overdue lane; asserting what the user sees and what is stored, in `tests/journeys/j7/test_aea_30.py` and `tests/journeys/j6/test_aea_30.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j7/test_aea_30.py tests/journeys/j6/test_aea_30.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-30.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-31** (J-8 (proposed))

- [ ] AC-<next> [journey] Extends J-8 (slice plan §0a journey map; J-8 is a proposed addition to the map, from the join audits): a `resetDemo` from one client sends every staff call of both clients on that login to 403 `role_reset` until a role switch, ends the open chat (`demo_reset` on its stream, 410 on its thread) and restores the issued tables row for row; asserting what the user sees and what is stored, in `tests/journeys/j8/test_aea_31.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j8/test_aea_31.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-31.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-32** (J-10 (proposed))

- [ ] AC-<next> [journey] Extends J-10 (slice plan §0a journey map; J-10 is a proposed addition to the map, from the join audits): after the journey's turns, the monitoring read's alert states equal the stored `health_event` rows and the `scheduler_last_run` tile reflects the newest `job_runs` row; asserting what the user sees and what is stored, in `tests/journeys/j10/test_aea_32.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j10/test_aea_32.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-53 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-32.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-53 (`integrated-journeys.md` §4).

**AEA-33** (J-2)

- [ ] AC-<next> [journey] Extends J-2 (slice plan §0a journey map): a membership question retrieves the current membership document above the relevance floor and never its stale twin, and the stored `lookup_log` row names the passage the answer cites; asserting what the user sees and what is stored, in `tests/journeys/j2/test_aea_33.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j2/test_aea_33.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-33.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).

**AEA-34** (J-3)

- [ ] AC-<next> [journey] Extends J-3 (slice plan §0a journey map): the follow-up turn after a booking loads the completed action, controller and identity from the working copy, and its reply names the new window; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_34.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_34.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-34.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).

**AEA-35** (J-2)

- [ ] AC-<next> [journey] Extends J-2 (slice plan §0a journey map): the billing and warranty specialists stay inside their brakes and each answer shows the invoice or warranty source it used; asserting what the user sees and what is stored, in `tests/journeys/j2/test_aea_35.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j2/test_aea_35.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-35.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).

**AEA-36** (J-5)

- [ ] AC-<next> [journey] Extends J-5 (slice plan §0a journey map): a CO-alarm message gets the approved instruction as the first reply text and a P0 case row, before any specialist runs; asserting what the user sees and what is stored, in `tests/journeys/j5/test_aea_36.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j5/test_aea_36.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-36.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).

**AEA-41** (J-9; J-7 (proposed))

- [ ] AC-<next> [journey] Extends J-9 and J-7 (slice plan §0a journey map; J-7 is a proposed addition to the map, from the join audits): J-9, a stream reconnect with `Last-Event-ID` gets each missed event once and writes a `stream_reconnect` record; J-7, during a takeover the customer's stream delivers `representative_joined`, `ai_paused`, `staff_message` and `ai_resumed` in order; asserting what the user sees and what is stored, in `tests/journeys/j9/test_aea_41.py` and `tests/journeys/j7/test_aea_41.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j9/test_aea_41.py tests/journeys/j7/test_aea_41.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57, AEA-51 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-41.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 and AEA-52 (`integrated-journeys.md` §4).

**AEA-42** (J-7)

- [ ] AC-<next> [journey] Extends J-7 (slice plan §0a journey map): "Talk to a person" creates one case (live-queued while staffed), a second press with a new `turn_id` answers `already_open` with the same card, and after a reload the card is in `getChatThread` (customer audit A-2, B-1); asserting what the user sees and what is stored, in `tests/journeys/j7/test_aea_42.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j7/test_aea_42.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-42.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-43** (J-3, J-8 (proposed))

- [ ] AC-<next> [journey] Extends J-3 and J-8 (slice plan §0a journey map; both are proposed additions to the map, from the join audits): J-3, SCR-2's inbox lists the sent code as `active`, then `used`; J-8, `resetDemo` answers a valid `ResetResponse` and the staffing and clock reads return to their defaults; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_43.py` and `tests/journeys/j8/test_aea_43.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_43.py tests/journeys/j8/test_aea_43.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57, AEA-51 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-43.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 and AEA-52 (`integrated-journeys.md` §4).

**AEA-44** (J-8)

- [ ] AC-<next> [journey] Extends J-8 (slice plan §0a journey map): a role switch through one client is seen by a second client on the same cookie at its next `getSession`, and a refused staff call names the current role and its reason (staff audit B1); asserting what the user sees and what is stored, in `tests/journeys/j8/test_aea_44.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j8/test_aea_44.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-44.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-45** (J-6)

- [ ] AC-<next> [journey] Extends J-6 (slice plan §0a journey map): the representative claims the escalated case (`result_line` "Claimed · Riley (demo)"), the queue and case view carry `allowed_actions` and the display fields unchanged, and a stale `expected_version` answers `VERSION_CONFLICT`; asserting what the user sees and what is stored, in `tests/journeys/j6/test_aea_45.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6/test_aea_45.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-45.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-46** (J-7)

- [ ] AC-<next> [journey] Extends J-7 (slice plan §0a journey map): join, send, hand back and close through `liveChatAction`: the customer's thread shows each line, the case `version` is unchanged by all four (staff audit A4), and `streamCaseEvents` delivers `controller_changed` and no `case_changed`; asserting what the user sees and what is stored, in `tests/journeys/j7/test_aea_46.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j7/test_aea_46.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-46.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-47** (J-6 (proposed))

- [ ] AC-<next> [journey] Extends J-6 (slice plan §0a journey map; J-6 is a proposed addition to the map, from the join audits): the supervisor's `advanceDemoClock` `plus_4h` past WP-4's case due reports `became_overdue` 1, and the next `getQueue` shows that case `due_state: overdue`; asserting what the user sees and what is stored, in `tests/journeys/j6/test_aea_47.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6/test_aea_47.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-47.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).

**AEA-48** (J-10)

- [ ] AC-<next> [journey] Extends J-10 (slice plan §0a journey map): the three read routes return the reader's stored values field for field, with their labels, units from {count, ms, share} and denominators; asserting what the user sees and what is stored, in `tests/journeys/j10/test_aea_48.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j10/test_aea_48.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-53 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-48.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-53 (`integrated-journeys.md` §4).

**AEA-55** (J-1…J-10 (runs all))

- [ ] AC-<next> [journey] Runs every journey (J-1…J-10, API legs and the AEA-58 / AEA-62 browser legs) on the integrated branch after its run-configuration change, exactly as the wave-merge gate does, and records them at level `integrated with a scripted model`; the UX-5 rerun through Prism proxy is reported separately and is not journey evidence (`integrated-journeys.md` §6), and its `@mock-only` tests are `NOT_RUN` — verify: `uv run pytest -m journey` (the all-journeys command) plus the record `docs/testing/journeys/YYYY-MM-DD-AEA-55.md` — evidence: pass per journey; the record's fields.
