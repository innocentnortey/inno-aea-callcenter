# UX-4 frontend: integration handoff for the backend plan

**Date:** 2026-10-21. **Scope:** `apps/web` (UX-4 prototype) against the 30 operations of
`docs/ux/03-structure/ui-contracts.openapi.yaml` (22 CONs, signed at UX-3). **Audience:** whoever writes the
backend integration checks (AEA-51, 52, 55, 57, 58, 59) and the UX session that owns `apps/web`.
**Method:** read-only audit on 2026-10-21; every claim was found by grepping the tests, scenarios and source on that date. **Update 2026-10-21 (unit-gap closure):** the unit-testable gaps were then closed in `apps/web` (new tests plus five small source fixes, section 3.5); the matrix cells, totals and gap list below reflect the state after that change, and the pre-change totals are kept in 2.2.
Test paths are relative to `apps/web/src` unless they start with `tests/`. Every new test file carries the tag `UNIT (fake transport)` in its title and a `MOCK-ONLY/UNIT` leading comment; none claims `REAL-BACKEND`.

**One-line summary.** Everything the frontend has ever been checked against is a Prism mock plus the dev layer
(`src/dev`) or a jsdom fake transport. Nothing has talked to a real server (nothing listens on :8000; `src/meridian`
is not a web app yet). That is the same position Riverside was in before its first real-server run, and it hid real
failures (section 3.4).

---

## 1. Verification status legend

Every claim in this document carries exactly one of these tags.

| Tag | Meaning | What it can prove | What it cannot prove |
|---|---|---|---|
| `MOCK-ONLY` | Ran in a browser against Prism (`npm run mock`, port 4019) with the dev layer (`npm run dev:mock`, port 5184, `?scenario=`, `?signedin=`, `?role=`). Playwright specs are `tests/e2e/smoke.spec.ts` and `tests/e2e/sweep.spec.ts`. | The screen loads in that state with no console error, one `h1`, no axe violation, no horizontal scroll, no `[contract drift]` line. | Anything the real server does. The dev layer decides the role, the 401/403 answers, which example comes back and what the stream says. The sweep asserts no screen content. |
| `UNIT` | Vitest (`npm test`, jsdom) with a fake transport (`src/test/fakeTransport.ts`) or a pure function test. Bodies come from `specExample()` (reads a named example out of the OpenAPI file), from `src/test/fixtures.ts`, or are hand-written in the test. | Component and reducer behaviour for a given body. | That a real server produces that body. |
| `REAL-BACKEND` | Ran against the actual FastAPI app. | Integration. | **Nothing carries this tag today.** It is the target state for every flow in section 4. |

`MOCK-ONLY` and `UNIT` both correspond to the project rule's `mock-tested` level
(`.claude/rules/integrated-journeys.md`, which also says the dev-only `?signedin=1&role=...` sign-in is why the
current Playwright suite counts as `mock-tested` only); `REAL-BACKEND` is its `integrated` level.

Where a statement is a plan or an expectation rather than a result, it is marked `PLANNED` (not a verification tag; it
is a statement about the backend plan, not about the UI).

---

## 2. Coverage matrix by operation

### How to read it

Cell values: **COVERED** (a test asserts it; path and test name given), **PARTIAL** (some of the cell is asserted),
**MOCK-ONLY** (only a dev-layer scenario loads the state; nothing asserts the content), **GAP** (nothing found),
**n/a** (the class does not apply). Types are `components["schemas"][...]` from `src/api/types.gen.ts`.

Column meanings:

- **(a) Optional fields absent.** In this spec every optional-looking field is `required` but `type: [..., "null"]`
  (nullable), so "absent" means `null`. I listed the nullable properties of each 2xx schema by walking the OpenAPI
  (counts in the Op column). Important: **no test anywhere renders a body with the key omitted**. Only `null` is
  tested (searched: no `delete`, no omit helper in any `*.test.ts*`). Riverside's server omitted keys (section 3.4), so
  `null` coverage is weaker evidence than it looks. This is gap G-01.
- **(b) Empty states.** Empty list or "nothing yet" bodies.
- **(c) Error responses.** The named codes the OpenAPI lists for that operation (from `src/api/contract.gen.json`).
  Shared 401 (`UNAUTHENTICATED`, `UNAUTHENTICATED_EXPIRED`) is in row "All authenticated ops" below, not repeated.
- **(d) Navigation guards.** Role gate, signed-out redirect with `return_to`, ended chat, not-found case, stream
  auth loss.

**What changed on 2026-10-21.** Cells below name the new tests. The keys-omitted evidence (column a) comes from a helper, `src/test/spec.ts`, that reads the OpenAPI file, finds every property whose schema allows `null` (or that the schema does not list as `required`), and deletes it from a named example: each key alone (all elements of an array at once), then all together. Each variant is rendered through the real screen or card and must show the same text and buttons as the same body with those keys set to `null`. Only keys present in a named example can be deleted, so a nullable key that no example contains is not exercised (the one such case is the `getChatThread` cell). Error bodies in the new tests come from `specError()` in the same file (the spec's own error examples); the 29 older hand-written bodies are listed and capped by `test/fixtures.audit.test.ts` (G-05).

### 2.0 Shared rows

| Concern | Cell |
|---|---|
| 401 `UNAUTHENTICATED` / `UNAUTHENTICATED_EXPIRED` on any call | **COVERED** `[UNIT]` `api/client.test.ts` "emits auth lost on 401 UNAUTHENTICATED with the expired reason, not for login"; `state/session.test.tsx` "a 401 on getSession goes to the login with return_to"; **new** `state/session.stream.test.tsx` (a stream 401, expired and none, lands on `/login?return_to=...&reason=...`; a `getSession` 401 keeps `reason=expired`; a 401 on `logout` still ends on `/login`) and `routes.guards.test.tsx` "Signed out" (every guarded route, `reason=none`). **MOCK-ONLY** `shared.session-ended` scenario, `tests/e2e/smoke.spec.ts` (the dev layer answers 401 from its `signedin=0` flag, not from a cookie). |
| Redirect target after login | **COVERED** `[UNIT]` `screens/scr12/Scr12.test.tsx` "success: setSession and navigate to return_to", "unsafe return_to goes to /"; `lib/returnTo.test.ts`. **MOCK-ONLY** `tests/e2e/sweep.spec.ts` "flow: demo login returns to return_to". |
| 403 `ROLE_NOT_ALLOWED` / `ROLE_NOT_ALLOWED_ROLE_RESET` as a **response** | **COVERED** `[UNIT]` **new** `state/roleDenied.test.tsx` (G-06): for SCR-5, 6, 7, 8, 9 the spec's two 403 examples produce the role panel, a second `getSession`, and a role switch that shows Customer; the case stream's 403 does the same (G-13). Needed one source fix (3.5, fix 2). **MOCK-ONLY** `shared.role-reset` scenario. The real cookie path stays `UNVERIFIED` (section 4.5). |

### 2.1 Matrix

| Operation (CON) | (a) Nullable fields absent | (b) Empty state | (c) Error responses | (d) Navigation guard |
|---|---|---|---|---|
| **startChatSession** (CON-1), 8 nullable | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-1 new chat" (STARTED, SIMULATION_ON: each omissible key deleted alone and all together; text equals the null version). Older: `screens/scr01/core/settledSummary.test.ts`, `screens/scr01/core/components/TopBar.test.tsx`. | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-1 start" (429 `REQUEST_RATE_LIMITED` shows "Try again in a moment.", 503 `RESET_IN_PROGRESS` the reset sentence; both from the spec's bodies). Older: `screens/scr01/core/errors.test.ts`, `screens/scr01/Scr01.test.tsx` "start failure shows the retry and still the role switch". | Signed out: shared row. |
| **getChatThread** (CON-1), 20 nullable | **PARTIAL** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-1 resumed thread" (OPEN, ENDED_BLOCK: every omissible key those two examples contain). Block types the two examples do not contain (`code_prompt` `expires_at`, `resends_left`, `tries_left`; `handoff` `due_label`) are exercised as turn blocks only (`screens/scr01/chat.omitted.test.tsx`), never inside a resumed thread, because the spec has no such thread example (G-10). | **COVERED** `[UNIT]` `screens/emptied.arrays.test.tsx` "SCR-1 resumed thread" (`turns: []` and every other array emptied, alone and together). | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-1 resume" (404 `SESSION_NOT_FOUND` starts a new chat, 410 `SESSION_ENDED` shows "This chat has ended."); older `screens/scr01/core/useChat.test.tsx` "404 on resume clears storage and starts a new chat". | **COVERED** `[UNIT]` ended chat: `screens/scr01/Scr01.test.tsx` "an ended thread shows the ended composer and still the role switch"; `cards/SessionEndedCard.test.tsx`. |
| **submitTurn** (CON-2), 23 nullable | **COVERED** `[UNIT]` `screens/scr01/chat.omitted.test.tsx`: all 37 named examples through the card registry (every omissible key alone, then all, each block equal to its null version) and through SCR-1 end to end (omit-all for every example, every single key for 9 examples). Found and fixed one defect (3.5, fix 5). | **COVERED** `[UNIT]` `screens/emptied.arrays.test.tsx` "a reply with blocks: [] and a thread with turns: [] in SCR-1" (`blocks: []` alone leaves the field usable; every array emptied for all 37 examples). | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-1 submitTurn": 400, 404, 409 `TURN_IN_PROGRESS`, 410, 503 from the spec's bodies, sentences pinned. Composed 200 outcomes (`RATE_LIMITED`, `SPEND_CAP_REACHED`, `BOOKING_CAP`, `TURN_TIMEOUT`, `BUSY`, `AI_PAUSED`, `FAILURE_OFFER`, `NO_INFO`, `SLOT_TAKEN`, `OUT_OF_AREA`, `CODE_*`, `NOT_VERIFIED`) as before: `screens/scr01/core/useChat.test.tsx`, `screens/scr01/cards/NoticeCards.test.tsx`, `screens/scr01/cards/ErrorCard.test.tsx`, `screens/scr01/cards/CodePromptCard.test.tsx`. | **COVERED** `[UNIT]` ended: 410 above; representative in chat: `screens/scr01/Scr01.test.tsx` "a representative joining changes the top bar and the placeholder". |
| **streamChatEvents** (CON-3), 0 on the envelope; event union has nullable fields | **COVERED** `[UNIT]` `screens/events.omitted.test.tsx` "chat events with keys omitted (SCR-1)" (9 event types: 3 from the spec's FRAMES, 6 typed dev fixtures validated against the `ChatEvent` schema; text equals the null version). | n/a | **COVERED** `[UNIT]` `api/transport.stream.test.ts` (G-04): `Last-Event-ID` resent after a server close (14 for the spec's ids 12 to 14), never lowered by a replay, 5xx and network errors back off 1, 2, 4, 5 s, a good connection resets the backoff, 404 and 410 stop with no auth-lost signal, 401 carries `expired` or `none`, `close()` ends the loop; `screens/scr06/caseStream.replay.test.tsx` (a replayed chat frame is shown once; the chat stream is not reopened after `chat_closed`). | **COVERED** `[UNIT]` stream auth loss: `state/session.stream.test.tsx` "the chat stream's 401 (no session) lands on /login with return_to=/ and reason=none". Ended chat closes the stream: `screens/scr06/caseStream.replay.test.tsx` "after chat_closed the stream is not reopened", `screens/scr01/core/reducer.test.ts`. |
| **requestPerson** (CON-4), 9 nullable | **COVERED** `[UNIT]` `screens/scr01/chat.omitted.test.tsx` "requestPerson CASE_CREATED / LIVE_QUEUED / ALREADY_OPEN" (clicked through SCR-1, every variant equal to its null version). | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-1 requestPerson": 400, 404, 410, 503 `HANDOFF_FAILED` (sentences pinned). `ALREADY_OPEN` stays in `screens/scr01/core/useChat.test.tsx`. | **COVERED** `[UNIT]` pressed during start: `screens/scr01/core/useChat.test.tsx` "Talk to a person during start waits for the start". Ended: 410 above. |
| **saveFollowUp** (CON-5), 4 nullable | **COVERED** `[UNIT]` `screens/scr01/chat.omitted.test.tsx` "the settled panel after saveFollowUp with keys omitted" (PHONE_MORNINGS, 7 omissible keys). | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-1 saveFollowUp": 400, 404, 409 `NOT_ALLOWED_IN_STATE` ("There's no open request to attach this to."), 410. | **COVERED** `[UNIT]` ended: 410 above. |
| **listDemoInbox** (CON-6), 0 | n/a | **COVERED** `[UNIT]` `screens/scr02/Scr02.test.tsx` "empty: exact copy and Back to the chat"; "used and expired: copy disabled". | **PARTIAL** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-2 inbox" renders 429 and 503 from the spec's bodies, and `screens/polled.reads.test.tsx` shows the 5 s poll keeps the list on a 429 or 503. Partial because 429 shows "The inbox didn't load. Try again." and not the shared sentence "Try again in a moment."; UI_CONTRACTS.md names copy for SCR-2's 503 only, so the 429 wording is unpinned. | n/a |
| **getStaffing** (CON-7), 1 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-3 demo bar (staffing)" (OFF, ON; `banner` omitted); `test/fixtures.ts` `STAFFING_OFF`. | n/a | **PARTIAL** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-3 demo bar: getStaffing" (429 renders, no code shown, h1 intact); `screens/polled.reads.test.tsx` "SCR-3 staffing switch" (the label stays on a poll's 429). Partial because no sentence is shown for a failed background read; none is specified. | n/a |
| **setStaffing** (CON-7), 0 | n/a | `converted_cases: 0`: **COVERED** `[UNIT]` `screens/scr03/copy.test.ts` "off with 0" (dev-transform body, see G-14 in 3.3). | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-3 setStaffing": 400, 503 (both "Staffing didn't change. Try again."). | n/a |
| **getDemoClock** (CON-8), 0 | n/a | n/a | **PARTIAL** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-3 demo bar: getDemoClock" (429 renders, no code shown). Partial for the same reason as `getStaffing`. | n/a |
| **advanceDemoClock** (CON-8, supervisor only), 0 | n/a | n/a | **PARTIAL** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-7 advanceDemoClock": 400, 403 `ROLE_NOT_ALLOWED`, 403 `ROLE_NOT_ALLOWED_ROLE_RESET`, 503 all render "The clock didn't move. Try again." (no code shown). Partial because UI_CONTRACTS.md gives a role sentence for 403 and this screen shows the generic one; the shared client re-reads the session on any 403 (`api/client.ts`, proved on reads in `state/roleDenied.test.tsx`). | **COVERED** `[UNIT]` `routes.guards.test.tsx` "SCR-7 Supervisor oversight as customer / representative / owner" (role panel, no data call). |
| **resetDemo** (CON-9), 0 | n/a | `open_chats_ended: 0`: **COVERED** `[UNIT]` `screens/scr03/Scr03.test.tsx` "reset with no chats ended omits that sentence" (dev-transform body). | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-3 resetDemo": 400, 409 `RESET_IN_PROGRESS`, 500 `RESET_FAILED` (sentences pinned). | **COVERED** `[UNIT]` `screens/scr03/Scr03.test.tsx` "reset returns the role to customer: getSession re-read". |
| **getSession** (CON-10), 0 | n/a | n/a | 401: shared row. | Signed out: shared row. |
| **listDemoRoles** (CON-10), 0 | n/a | n/a | **COVERED** `[UNIT]` `screens/scr04/Scr04.test.tsx` "roles list fails: four buttons from ROLE_LABEL, no error text" (the spec lists only the shared 401). | n/a |
| **switchRole** (CON-10), 0 | n/a | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-4 switchRole": 400, 503 ("Couldn't switch role. Try again."); older `components/shell/RoleSwitch.test.tsx`, `state/session.test.tsx`. | **COVERED** `[UNIT]` landing per role: `state/session.test.tsx`. **MOCK-ONLY** `tests/e2e/sweep.spec.ts` "flow: role switch round trip". |
| **getQueue** (CON-11), 15 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-5 queue" (4 examples, every omissible key of every row, incl. `owner`, `due_*`, `wake_up_at`, `queued_at`, `age_label`). | **COVERED** `[UNIT]` `screens/scr05/Scr05.test.tsx` "empty state copy"; `screens/emptied.arrays.test.tsx` "SCR-5 queue". | **COVERED** `[UNIT]` 403 as a response: `state/roleDenied.test.tsx` "SCR-5 queue" (both 403 examples: role panel, session re-read, switch shows Customer); `screens/errors.spec.test.tsx` "SCR-5 queue". Read error: `screens/scr05/Scr05.test.tsx` "error shows retry and retry refetches". | **COVERED** `[UNIT]` `routes.guards.test.tsx` "SCR-5 Representative queue as ..." (4 roles) and "Signed out" "SCR-5 /staff/queue". |
| **getCase** (CON-12), 14 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-6 case" (7 examples; `promise.follow_up.window`, `sources.*.current`, `speaker.display_name`, `live.since`, `trim_note`, `changed_note`...). Two defects found and fixed (3.5, fix 3). | **COVERED** `[UNIT]` `screens/emptied.arrays.test.tsx` "SCR-6 case" (`conversation`, `activities`, `sources`, `other_cases`, brief `items`, each alone and together). | **COVERED** `[UNIT]` 403: `state/roleDenied.test.tsx` "SCR-6 case"; 404 `CASE_NOT_FOUND`: `screens/errors.spec.test.tsx` "SCR-6 case" (sentence pinned); older `screens/scr06/Scr06.test.tsx` "case not found panel". | **COVERED** `[UNIT]` `routes.guards.test.tsx` "SCR-6 Case view as ..." (4 roles), owner read-only on a joined chat. |
| **applyCaseAction** (CON-13), 4 | **COVERED** `[UNIT]` `screens/actions.omitted.test.tsx` "Claim" (CLAIMED, WAITING, RESOLVED, ASSIGNED, PRIORITY_CHANGED: `case.owner`, `due_at`, `due_label`, `wake_up_at` omitted, clicked through SCR-6). | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-6 applyCaseAction (Claim)" and "(Release)": 400, 403 x2, 404, 409 `VERSION_CONFLICT` / `CASE_ALREADY_CLAIMED` / `NOT_ALLOWED_IN_STATE`, 422 `REASON_REQUIRED` / `WAKE_UP_REQUIRED` / `OUTCOME_REQUIRED`, every sentence pinned (G-15 closed). | **COVERED** `[UNIT]` role gate: `routes.guards.test.tsx`; menu follows `allowed_actions`: `screens/scr06/actionPlan.test.ts`. |
| **liveChatAction** (CON-14, representative only), 3 | **COVERED** `[UNIT]` `screens/actions.omitted.test.tsx` "Send a live message", "Hand back", "Close the chat", "Claim and join (join answer)" (`controller.display_name`, `live.since`, `message`, `message.speaker.display_name` omitted). | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-6 liveChatAction (Send)": 400, 403 `NOT_CLAIMED_BY_YOU`, 404, 409 `NOT_LIVE`, 409 `CASE_ALREADY_CLAIMED`. | **COVERED** `[UNIT]` `routes.guards.test.tsx` "supervisor on a joined live chat: sending is refused with the spec's 403"; joined state disables after hand back: `screens/scr06/LiveBox.test.tsx`. |
| **streamCaseEvents** (CON-21) | **COVERED** `[UNIT]` `screens/events.omitted.test.tsx` "case events with keys omitted (SCR-6)" (5 event types: 2 from FRAMES, 3 typed dev fixtures validated against `CaseEvent`). | n/a | **COVERED** `[UNIT]` `api/transport.stream.test.ts` "a case stream 403 (role changed) and 404 stop with no auth-lost signal", "a 401 carries the body's reason"; `state/roleDenied.test.tsx` "G-13" (stream 403: session re-read, role gate replaces the live box, no retry). | **COVERED** `[UNIT]` stream auth loss: `state/session.stream.test.tsx` "the case stream's 401 (expired) lands on /login with the case path as return_to and reason=expired"; `demo_reset` and `chat_closed` end the live box: `screens/scr06/Scr06.test.tsx`, `screens/scr06/caseReducer.test.ts`. A replayed frame is shown once (3.5, fix 4): `screens/scr06/caseStream.replay.test.tsx`. |
| **recordContactActivity** (CON-15, representative only), 5 | **COVERED** `[UNIT]` `screens/actions.omitted.test.tsx` "Log a call" (CALL_REACHED, EMAIL_LEFT_MESSAGE: `activity.note`, `case.*` omitted). | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-6 recordContactActivity": 400, 403 x2, 404, 409 `NOT_ALLOWED_IN_STATE`, 409 `VERSION_CONFLICT`. | **COVERED** `[UNIT]` `routes.guards.test.tsx` "supervisor logging a call that the server refuses (ROLE_NOT_ALLOWED) reads as a role sentence"; owner is read-only (no log buttons). |
| **createFlag** (CON-16), 5 | **COVERED** `[UNIT]` `screens/actions.omitted.test.tsx` "Flag a case" (ANSWER: `reason`, `message_id`, `note`, `reviewed_*` omitted). | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-6 createFlag": 400, 403 x2, 404 `CASE_NOT_FOUND`. | n/a |
| **listFlags** (CON-16), 5 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-8 flags" (THREE; every nullable column omitted). | **COVERED** `[UNIT]` `screens/scr08/Scr08.test.tsx` "empty list sentence" (EMPTY); `screens/emptied.arrays.test.tsx` "SCR-8 flags". | **COVERED** `[UNIT]` 403: `state/roleDenied.test.tsx` "SCR-8 flags"; read failure: `screens/scr08/Scr08.test.tsx` "load failure shows the sentence". | **COVERED** `[UNIT]` `routes.guards.test.tsx` "SCR-8 Review list of flags as ..." (4 roles); `screens/scr08/Scr08.test.tsx` "representative sees disabled buttons and the hint". |
| **reviewFlag** (CON-16, supervisor only), 5 | **COVERED** `[UNIT]` `screens/actions.omitted.test.tsx` "reviewFlag response with keys omitted instead of null (SCR-8)". | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-8 reviewFlag": 400, 403 x2 ("Supervisors mark flags reviewed."), 404 `FLAG_NOT_FOUND` ("That flag is gone. It may have been cleared by a demo reset."). | See listFlags. |
| **getOversight** (CON-17, supervisor only), 37 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-7 oversight" (4 examples: every row nullable in every lane, `alerts.*.case_ref`, `staffing.banner`). | **COVERED** `[UNIT]` `screens/scr07/Scr07.test.tsx` "empty oversight keeps all five lanes and shows the sentence"; `screens/emptied.arrays.test.tsx` "SCR-7 oversight". | **COVERED** `[UNIT]` 403: `state/roleDenied.test.tsx` "SCR-7 oversight"; load failure: `screens/scr07/Scr07.test.tsx`. | **COVERED** `[UNIT]` `routes.guards.test.tsx` "SCR-7 Supervisor oversight as ..." (4 roles). |
| **getOwnerMetrics** (CON-18, owner or supervisor), 20 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-9 owner outcomes" (SEEDED, EMPTY: every measure's `value`, `numerator`, `denominator`, `null_reason` omitted). Defect found and fixed (3.5, fix 1). | **COVERED** `[UNIT]` `screens/scr09/Scr09.test.tsx` "empty shows the sentence and dash tiles"; `screens/emptied.arrays.test.tsx` "SCR-9 owner". | **COVERED** `[UNIT]` 403: `state/roleDenied.test.tsx` "SCR-9 owner outcomes"; failure: `screens/scr09/Scr09.test.tsx` "error shows the sentence". | **COVERED** `[UNIT]` `routes.guards.test.tsx` "SCR-9 Business-owner outcomes as ..." (4 roles, so the representative too). |
| **getMonitoring** (CON-19), 13 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-10 monitoring" (6 examples; tile `value`, `numerator`, `denominator`, `null_reason`, `alerts.*.fired_at`, `last_restart`). Defect found and fixed (3.5, fix 1). | **COVERED** `[UNIT]` `screens/scr10/Scr10.test.tsx` "empty shows the sentence"; `screens/emptied.arrays.test.tsx` "SCR-10 monitoring". | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-10 monitoring" (429 "Try again in a moment.", 503 reset sentence); `screens/polled.reads.test.tsx` (30 s poll keeps the tiles). | n/a (all roles) |
| **getLatestEval** (CON-20), 11 | **COVERED** `[UNIT]` `screens/omitted.keys.test.tsx` "SCR-11 evaluation" (4 examples; `min`, `max`, `target`, `mix.*.tests`, `splits.*`, `headline`). Defect found and fixed (3.5, fix 1). | **COVERED** `[UNIT]` `screens/scr11/Scr11.test.tsx` "empty (NO_RUN) shows the sentence and no number". | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-11 evaluation" (429, 503). | n/a |
| **login** (CON-22), 0 | n/a | n/a | **COVERED** `[UNIT]` `screens/errors.spec.test.tsx` "SCR-12 login": 400 `VALIDATION_ERROR`, 401 `LOGIN_FAILED`, 429 `LOGIN_RATE_LIMITED` (one identical sentence); older `screens/scr12/Scr12.test.tsx` incl. network failure. | **COVERED** `[UNIT]` `reason=expired`, already signed in: `screens/scr12/Scr12.test.tsx`; the login page is not redirected: `routes.guards.test.tsx` "the login page itself is not redirected". **MOCK-ONLY** `tests/e2e/sweep.spec.ts` "flow: demo login returns to return_to". |
| **logout** (CON-22), 0 | n/a | n/a | **COVERED** `[UNIT]` 204: `api/client.test.ts` "returns undefined on 204"; 401: `state/session.stream.test.tsx` "logout answered 401 UNAUTHENTICATED ... still ends on /login". | **COVERED** `[UNIT]` `state/session.test.tsx` "signOut calls logout then goes to /login". |

### 2.2 Totals (counted from the matrix cells by script, 30 operations x 4 classes = 120 cells)

Rule: a cell counts once, by its **weakest** keyword (GAP beats PARTIAL beats MOCK-ONLY beats COVERED), so a cell that
has one untested error code among five is a GAP. "Covered by reference" cells (for example "Signed out: shared row")
count as COVERED.

**After the 2026-10-21 unit-gap closure (this table):**

| Class | n/a | Applies | COVERED | PARTIAL | MOCK-ONLY | GAP |
|---|---|---|---|---|---|---|
| (a) nullable fields absent | 10 | 20 | 19 | 1 | 0 | 0 |
| (b) empty states | 18 | 12 | 12 | 0 | 0 | 0 |
| (c) error responses | 0 | 30 | 26 | 4 | 0 | 0 |
| (d) navigation guards | 7 | 23 | 21 | 0 | 2 | 0 |

**Before (as printed on 2026-10-21 in the first version of this file):**

| Class | n/a | Applies | COVERED | PARTIAL | MOCK-ONLY | GAP |
|---|---|---|---|---|---|---|
| (a) nullable fields absent | 10 | 20 | 3 | 3 | 0 | 14 |
| (b) empty states | 18 | 12 | 9 | 0 | 0 | 3 |
| (c) error responses | 0 | 30 | 2 | 4 | 1 | 23 |
| (d) navigation guards | 8 | 22 | 13 | 3 | 3 | 3 |

Recount note: running the same script over the old matrix gives (a) to (c) exactly as printed and, for (d), n/a 7, applies 23, COVERED 14, PARTIAL 3, MOCK-ONLY 3, GAP 3: the printed (d) row was one cell off. The two remaining (d) MOCK-ONLY cells (`switchRole`, `login`) count as MOCK-ONLY only because each also cites a Playwright MOCK-ONLY run beside a COVERED unit test; no (d) cell is weaker than a unit test.

Reading the totals: **no cell is tagged `REAL-BACKEND`.** "COVERED" means `UNIT` against a fixture built from the spec's named examples or its error examples; it says the UI copes with those bodies, not that a server sends them. Of the 85 applicable cells, 78 are COVERED, 5 PARTIAL, 2 MOCK-ONLY (see the note), 0 GAP. The five PARTIAL cells and why: `getChatThread` (a) (no spec example of a resumed thread holding the block types that carry the most nullable keys), and four (c) cells whose copy is unpinned or divergent: `listDemoInbox` 429, `getStaffing` 429, `getDemoClock` 429 (a failed background read shows nothing; no copy is specified) and `advanceDemoClock` 403 (generic line where UI_CONTRACTS.md has a role sentence). The remaining weakness is the one this file opened with: every body is a fixture, so a real server's key omission, ordering, header and cookie behaviour are still `UNVERIFIED` (4.8).

---

## 3. Gaps ranked by integration risk

Risk = (how likely the real backend breaks it) x (how badly the demo looks if it does) x (how invisible it is today).
Each item says what to add, where, what it asserts and which generated type it builds from. "Fixture builder" means
`specExample()` in `screens/scr06/specExample.ts` (reads the named OpenAPI example; do not retype bodies).

### 3.1 Ranked list

Status column added 2026-10-21 ("closed (unit)" means every unit-testable part is covered by the named tests and the rest
is a `REAL-BACKEND` journey; "open" means not attempted here). G-02 and G-03 were out of scope for this change (another
session owns `tests/e2e`).

| ID | Class | Risk | Gap | Status 2026-10-21 |
|---|---|---|---|---|
| G-01 | a | **High** | Keys omitted, not null. | **Closed (unit).** Helper `test/spec.ts` (`omittedVariants`); `screens/omitted.keys.test.tsx` (SCR-1 start and resume, 3 staffing/demo bar, 5, 6, 7, 8, 9, 10, 11), `screens/scr01/chat.omitted.test.tsx` (submitTurn x37, requestPerson, saveFollowUp), `screens/actions.omitted.test.tsx` (CON-13 to 16 responses), `screens/events.omitted.test.tsx` (both streams' events), `test/spec.selftest.test.ts` (the helper itself). 3 of the source defects in 3.5 (fixes 1, 3, 5) came from this gap. Residual: only keys present in a named example are deleted; real-server omission is `UNVERIFIED`. |
| G-02 | harness | **High** | The Playwright suite cannot run in proxy mode; it is built on dev-layer URL parameters. | **Open.** Out of scope here (`tests/e2e` belongs to another session). |
| G-03 | journey | **High** | No cross-flow journey exists, in any mode. | **Open.** Out of scope here. |
| G-04 | d / stream | **High** | SSE replay, reconnect and server-close behaviour is unverified; `transport.ts` has 2 tests. | **Closed (unit).** `api/transport.stream.test.ts` (14 tests: `Last-Event-ID`, backoff, server close, 404/410/403/401), `state/session.stream.test.tsx` (stream 401 to `/login?return_to=`), `screens/scr06/caseStream.replay.test.tsx` (replay delivered once on both screens; chat stream not reopened after `chat_closed`). Residual: the case stream is not closed after `chat_closed` and re-asks every 1 s if a real server ends it each time; real SSE replay needs `REAL-BACKEND`. |
| G-05 | drift | **High** | Error bodies are hand-written, with codes and shapes outside the spec. | **Closed for new tests, residual for old.** `specError()` in `test/spec.ts`; every new error test uses it (`screens/errors.spec.test.tsx`: 115 tests, one per spec error example per trigger, 25 operations). `test/fixtures.audit.test.ts` caps the 29 older hand-written bodies and pins the 5 off-spec codes in them (`X`, `BOOM`, `NOT_FOUND`, `NETWORK`, `MISSING_PARAM`); the old tests were not edited. |
| G-06 | c | Medium-high | 403 as a response (role changed server-side) never rendered. | **Closed (unit).** `state/roleDenied.test.tsx` (SCR-5, 6, 7, 8, 9 x both 403 examples). One source fix (3.5, fix 2). Residual: after the session re-read, the generic role panel replaces the contract's reset sentence ("The demo was reset, so you're back to the customer role. Pick a role again."), which the panel component has but never shows after a re-read. |
| G-07 | drift | Medium-high | Request bodies are not closed in the spec; Prism cannot flag extra or missing request fields. | **Closed (unit).** `api/requests.audit.test.tsx`: strict checker (unknown key, missing key, type, enum, uuid, length) over all 13 request schemas, with call sites driven through `useChat` + the real gateway, the 9 SCR-6 forms, SCR-6 buttons, SCR-3, 4, 7, 8, 12. No unmatched field found, so no OpenAPI request is raised. Not driven: `applyCaseAction` `start`, the bar's `Join chat` body, `submitTurn` retry (their bodies are literals pinned by older tests). |
| G-08 | c | Medium | 429 on polled reads and 400 on writes are untested. | **Closed (unit).** `screens/errors.spec.test.tsx` (every 400/429/503 the spec lists for a trigger), `screens/polled.reads.test.tsx` (inbox 5 s, staffing 10 s, monitoring 30 s keep what is shown on a 429/503). Residual: three PARTIAL (c) cells in 2.1 (no copy for a failed background read; inbox 429 wording). |
| G-09 | drift | Medium | Preformatted `*_label` strings are parsed or printed raw. | **Open** (fixture drift, outside classes a to d). |
| G-10 | drift | Medium | `getChatThread` and `getSession` examples are narrower than the real range (always `nobody_online`; no supervisor/owner). | **Open** (fixture drift). It is why `getChatThread` (a) is PARTIAL. |
| G-11 | drift | Medium | Dev-fixture states have no OpenAPI example; they are typed but unvalidated at runtime. | **Open, one slice done.** The 6 chat and 3 case event fixtures are now validated against the spec's event schemas (`screens/events.omitted.test.tsx` "shape"); the card fixtures, case transforms and `g5-transforms` are not. |
| G-12 | drift | Medium | Test replies depend on the dev layer's chat director, which picks the example from the typed words. | **Open** (e2e). |
| G-13 | d | Medium | Stream 403 after a role switch or reset ends silently. | **Closed (unit).** `state/roleDenied.test.tsx` "G-13" and `api/transport.stream.test.ts` (403 and 404 stop, no retry). One source fix (3.5, fix 2). Residual: a 404 or 410 on a stream still stops with no line on screen. |
| G-14 | b | Low-medium | Empty arrays inside non-list bodies (`turns`, `blocks`, `conversation`, `activities`, `sources`). | **Closed (unit).** `test/spec.ts` `emptiedVariants`; `screens/emptied.arrays.test.tsx` (158 cases: every array of every named example of 12 read operations emptied alone and together; all 37 turn examples with every array emptied; `blocks: []` alone). No defect found. |
| G-15 | c | Low-medium | Non-render coverage only for case-action error copy (`NOT_ALLOWED_IN_STATE`, `WAKE_UP_REQUIRED`, `OUTCOME_REQUIRED`, `NOT_CLAIMED_BY_YOU`). | **Closed (unit).** `screens/errors.spec.test.tsx` "SCR-6 applyCaseAction (Claim)/(Release)/liveChatAction": rendered through the real forms and buttons with the spec's bodies, sentences pinned. |
| G-16 | sweep | Low-medium | The `sweep.spec.ts` scenarios assert no content, so a listed scenario is not evidence of behaviour. | **Open.** Out of scope here. |

Also added, not a numbered gap: `routes.guards.test.tsx` covers class (d) for every screen x every role (44 cases), every guarded route signed out (11), the not-found page, the login page not being redirected, owner read-only and the supervisor's refused writes.

Gap items by primary class (16 items): **a** 1 (G-01), **b** 1 (G-14), **c** 3 (G-06, G-08, G-15), **d** 2 (G-04, G-13),
**fixture drift** 6 (G-05, G-07, G-09, G-10, G-11, G-12), **harness / journey** 3 (G-02, G-03, G-16). Matrix cell
counts are in 2.2; they are cells, not items. After this change: **9 of 16 items closed on the unit side** (G-01, 04, 05, 06,
07, 08, 13, 14, 15), 1 partly (G-11), 6 open (G-02, 03, 09, 10, 12, 16). Every class a to d item is closed.

### 3.2 Implementer-ready tests

This section is the original plan, kept as written. What was built instead, and where, is in the Status column of 3.1; where a
file name here differs from 3.1 (for example `test/spec.ts` instead of `src/test/omitNullable.ts`), 3.1 is right.

**G-01. Render with keys omitted.** *File:* new `src/test/omitNullable.ts` plus new cases in `screens/scr06/Scr06.test.tsx`,
`screens/scr05/Scr05.test.tsx`, `screens/scr07/Scr07.test.tsx`, `screens/scr01/core/useChat.test.tsx` (resume),
`screens/scr01/cards/cards.coverage.test.tsx`. *Build:* the helper reads `contract` (the same YAML as `specExample`),
collects every property typed `[x, "null"]` in the response schema, and deletes those keys from a clone of the named
example. *Fixture types:* `components["schemas"]["CaseDetail"]`, `QueueResponse`, `OversightResponse`, `ChatThread`,
`TurnResponse`, `StartSessionResponse`, `HandoffResponse`. *Asserts:* the screen renders with exactly one `h1`, no
thrown error, no visible text `undefined` or `null`, and the same action buttons as the null version. *Also assert:*
`QueueRow` with `owner` omitted still says Unowned. Pair with AEA-59 `test_openapi_fixtures.py`, which PLANNED already
generates "omitted optionals" on the server side; this is the matching client side.

**G-02. Make the e2e suite state-setup pluggable.** *Why:* every spec in `tests/e2e/` enters a state with dev-layer
query params (`?signedin=1&role=representative&staffing=on&scenario=scr05.live-queued`). The dev layer is not in a
production build (`src/main.tsx` only installs it when `MODE === "mock"`; `scripts/check-dist.mjs` enforces that), so
none of these specs can run against a real server. *File:* new `tests/e2e/support/world.ts` exporting
`enter(page, { role, staffing, scenario })`. In mock mode it keeps the URL parameters. In proxy mode it does real
calls: `page.request.post("/api/login", { data: LoginRequest })`, `PUT /api/session/role` with `SwitchRoleRequest`,
`PUT /api/demo/staffing` with `StaffingRequest`, `POST /api/demo/reset` with `ResetRequest` (`{ confirm: true }`), then
`page.goto(route)`. Select the mode with `E2E_MODE=mock|proxy` in `playwright.config.ts`. *Asserts:* the same spec
files pass in both modes for the states that have a real equivalent; mock-only scenarios (forced errors, `hang`)
are tagged `@mock` and skipped in proxy mode. *Types:* `components["schemas"]["LoginRequest"]`, `SwitchRoleRequest`,
`StaffingRequest`, `ResetRequest`.

**G-03. The cross-flow journey.** See section 4.7; implement first as a mock rehearsal, then in proxy mode.

**G-04. Transport behaviour.** *File:* `api/transport.test.ts` (add; builds on the existing fake `fetch`). *Add four
tests:* (1) after a stream body ends, the next request carries `Last-Event-ID` equal to the highest id seen (frames
from `specExample("/api/chat/sessions/{thread_id}/events", "get", "200", "FRAMES")`, parsed with `SseParser`; the
example is one text blob of ids 12, 13, 14, so the expected header is `14`); (2) a duplicate id after reconnect is
delivered once to `useChat` (extend `useChat.test.tsx` "events update state and the demo bar"); (3) a 200 response
that closes after a `chat_closed` frame does not reconnect forever once the consumer sets the spec to null
(`useChat` does; `scr06/useCaseStream.ts` must be checked, it has no equivalent test); (4) `404` and `410` stop
without `emitAuthLost`. *Types:* `ChatEvent`, `CaseEvent`. Then extend `state/session.test.tsx` with "a 401 from a
stream goes to the login with return_to" (emit through `emitAuthLost` from the stream path).

**G-05. Spec-built error bodies and a fixture audit.** *File:* new `screens/scr06/specError.ts` next to
`specExample.ts` (same loader; resolves `components.responses.*` such as `SessionNotFound`, `RoleNotAllowed`,
`TooManyRequests`, `ResetInProgress`). Replace the hand-written bodies:
`{ error: { code: "RESET_IN_PROGRESS" } }` (`Scr02`, `Scr03`, `Scr04`), `{ error: { code: "X" } }` (`Scr09`, `Scr04`),
`{ error: { code: "BOOM" } }` (`Scr07`, `Scr08`), `NOT_FOUND` (`Scr02/03/04` default handlers; not a spec code).
*Meta test:* new `test/fixtures.audit.test.ts` that wraps `jsonResponse` and fails if a 4xx/5xx body's `error.code`
is not in `OPS[op].responses[*].examples` for the op being called. *Types:* `components["schemas"]["ApiError"]`.

**G-06. 403 as a response.** *Files:* one test each in `Scr05`, `Scr06`, `Scr07`, `Scr09` test files, plus
`state/session.test.tsx`. Feed `specError("getQueue", 403, "ROLE_NOT_ALLOWED_ROLE_RESET")` to a screen the session
says is allowed. *Asserts:* the screen shows its role panel (not a raw error), `getSession` is re-read, and the
role switch shows the new role. This is exactly the sequence a real demo reset produces.

**G-07. Close the request bodies and check every call site.** The OpenAPI contains zero `additionalProperties`
(grep), so Prism accepts a request with a misspelt or extra field. *File:* new `api/requests.audit.test.ts`. Load
the request schemas (`TurnRequest`, `HandoffRequest`, `FollowUpRequest`, `StaffingRequest`, `ClockAdvanceRequest`,
`ResetRequest`, `SwitchRoleRequest`, `CaseActionRequest`, `LiveActionRequest`, `ActivityRequest`, `FlagRequest`,
`FlagReviewRequest`, `LoginRequest`), deep-clone them with `additionalProperties: false`, and validate the bodies
captured by `calls` in the existing screen tests (Scr03 "turn on: body {mode}", Scr08 "an empty note is sent as
null", `ActionForms.test.tsx`, `AssignDialog.test.tsx`). Report the unmatched fields to the UX owner as an OpenAPI
request; do not edit the spec from here.

**G-08. 429 and 400.** *Files:* `Scr02.test.tsx` (the 5 s poll: a 429 keeps the last list and shows a retry line),
`Scr10.test.tsx`, `Scr11.test.tsx`, `Scr03.test.tsx` (`getStaffing`, `getDemoClock`). Bodies from `specError(op, 429,
"REQUEST_RATE_LIMITED")`. Table-driven 400 test in `api/validation.test.ts`: each write op surfaces `VALIDATION_ERROR`
as a field-level or generic line and never crashes.

**G-09. Labels.** *Files:* `components/shared/QueueRow.test.tsx`, `scr05/LiveRow.test.tsx`, `scr06/caseText.test.ts`,
`scr01/cards/VisitCards.test.tsx`. The UI prints `row.due_label` raw (`QueueRow.tsx`), strips a `Waiting since `
prefix from `age_label` with a regex (`LiveRow.tsx`), splits `due_label` on `, the window start` (`caseText.ts`) and
parses `window_label` into times (`VisitCards.tsx` `parseWindowLabel`). Add cases where the label has a different but
valid wording and where ISO and label disagree; assert ISO wins when both are present and the page never prints a
24-hour time. *Types:* `QueueRow`, `CaseSummary`, `AppointmentBlock`, `SettledVisit`. Backend side: AEA-59 must assert
label text equals the spec example format.

**G-10. Narrow examples.** `getChatThread` only has `OPEN` (staffing `nobody_online`) and `ENDED_BLOCK`; `defaultExample`
(`dev/defaults.ts`) only switches `startChatSession` with staffing. `getSession` has CUSTOMER and REPRESENTATIVE
only; `dev/session-fake.ts` replays the last `switchRole` body for the other two roles. *Test:* in `useChat.test.tsx`
a resume with `staffing.mode = "simulated_on_shift"` and a representative turn (build from `ChatThread` OPEN with a
transform; see G-11 for adding spec examples), asserting top bar and banner. In proxy mode: switch to supervisor,
reload, assert still supervisor.

**G-11. Dev-fixture states.** See 3.3 for the list. *File:* new `dev/fixtures.audit.test.ts`: validate every dev
fixture and transform output against the OpenAPI JSON Schema at runtime (ajv or the `yaml`-loaded schema), not only
against the TypeScript type. Request the missing states as named examples from the OpenAPI owner (UXR-style request).

**G-12. Replies chosen by the typed words.** `dev/directors/chat-core.ts` and `chat-cards.ts` choose the `submitTurn`
example from the request text; `sweep.spec.ts` "flow: customer sends a chat message and sees a reply" asserts the
literal sentence "after-hours dispatch fee is $149". Against the scripted model of AEA-57 the text will differ.
*Change:* the proxy-mode variant asserts the block type (a source chip is present) and a persisted message count,
not the sentence.

**G-13. Stream 403 after role change.** `STOP_STATUSES` makes a 403 on a stream stop silently. *Test:* `Scr06.test.tsx`
with the stream opener returning 403: the live box must show a reconnect/role line, not stay "live" with no events.

**G-14. Empty arrays.** Cases in `Scr06.test.tsx` (`conversation: []`, `activities: []`, `sources: []`), `useChat.test.tsx`
(`turns: []`), `cards.coverage.test.tsx` (`blocks: []`).

**G-15. Rendered case-action errors.** `Scr06.test.tsx`: one test each for 422 `WAKE_UP_REQUIRED`, 422 `OUTCOME_REQUIRED`,
409 `NOT_ALLOWED_IN_STATE`, 403 `NOT_CLAIMED_BY_YOU` through the real form (`ActionForms`) with `specError` bodies.

**G-16. Sweep assertions.** `sweep.spec.ts` should read the `notes`/`state` of each scenario and assert one
state-specific fact (for example the scenario's empty sentence), otherwise it stays a layout/axe sweep.

### 3.3 Fixture-drift risks (places the tests depend on something Prism or the dev layer supplies)

| Risk | Where | Why it will not survive a real backend |
|---|---|---|
| First 2xx example by default | `dev/defaults.ts` `first2xx()` | Unlisted ops get Prism's first example (e.g. `listDemoInbox` `ONE_ACTIVE`, `getOversight` `SEEDED`); a real server answers from live state. |
| Request bodies ignored | `dev/resolve.ts` | Prism returns the same example whatever the body says. Only `submitTurn`, `switchRole` and `setStaffing` have dev-side logic that reads the body; every other write (`applyCaseAction`, `recordContactActivity`, `createFlag`, `saveFollowUp`) is answered by `dev/directors/case-actions.ts` or a fixed example. The body is checked only by unit tests, never by a server. |
| SSE body is finite | Prism's `streamChatEvents` / `streamCaseEvents` body (3 frames, ids 12 to 14 and 5 to 6) is "read and discarded" (`dev/stream/dev-stream.ts`) | In mock mode the dev layer replaces the transport entirely, so the real `openStream` loop (backoff, `Last-Event-ID`, no-self-close after a terminal event) has never run against any server. |
| Preformatted `*_label` strings | `due_label`, `age_label`, `window_label`, `version_label`, `label` of clock/staffing | See G-09. The UI parses some of them. |
| `getChatThread` | Always `OPEN` unless forced; staffing always `nobody_online` | A resumed thread with a representative or a staffed banner has never been rendered from a spec body. |
| `getSession` for supervisor/owner | `dev/session-fake.ts` | The spec has no such examples; reload behaviour is untested. |
| Fake cookie | `dev/session-fake.ts` writes `mhc_session=prototype-synthetic` through `document.cookie` | Real cookie is `HttpOnly` (AEA-23), so JS cannot read or set it; nothing outside `src/dev` touches `document.cookie`, which is good, but the real Set-Cookie path (and `Secure` on http://127.0.0.1) is unexercised. |
| Role enforcement | `dev/resolve.ts` step 4 (`x-roles`) | The dev layer answers 403 from the world's role; the real server answers from the cookie. |
| Forced errors | `OpForce` (`example`, `fail`, `hang`, `sequence`) | Real servers cannot be told to fail on request; the proxy-mode suite will need backend hooks (AEA-57 scripted model, a reset-in-progress switch). |
| Dev-fixture states with no named OpenAPI example | listed below | Typed against `types.gen.ts` but never validated at runtime and never produced by a server. |

**Dev-fixture states with no named OpenAPI example** (from `// dev fixture: no named example` comments and
`docs/ux/04-prototype/groups/*.md`):

- Chat events: `ai_resumed`, `chat_closed` (chat), `staffing_changed`, `shift_ended`, `clock_changed`, `demo_reset`
  (`dev/stream/events.ts`). Only `representative_joined`, `ai_paused`, `staff_message` have an example.
- Case events: `controller_changed`, `case_changed`, `demo_reset` (`dev/stream/events.ts`); only `customer_message` and `chat_closed` have one.
- `submitTurn` card states: urgent slot card, staffed emergency line, shown quick checks, partial `NO_INFO`, staffed
  `HANDOFF` and the refund variant, staffed `CHANGE_REQUEST`, cancel variant, `CANCELLED` write (`dev/scenarios/scr01-cards.fixtures.ts`).
- Case ops: case references 0005, 0006, 0012 rewritten from other examples; result lines for `release`, `start`,
  `close_unresolved` (`dev/directors/case-actions.ts`); the HANDED_BACK live response with `since`.
- Demo controls: `setStaffing` off with nobody waiting (`converted_cases: 0`), `resetDemo` with 0 chats ended
  (`docs/ux/04-prototype/groups/g3-demo-pages.md`).
- Oversight and flags: `withoutRow`, `withLiveQueue`, `withExtraFlag`, `withReviewed`, `withNullPromises`
  (`dev/scenarios/g5-transforms.ts`; `docs/ux/04-prototype/groups/g5-oversight-reads.md`).
- The owner/supervisor `allowed_actions` sets in `getCase` (G4 note: "dev fixtures").

### 3.4 What Riverside showed (evidence from `../inno-riverside-onboarding`)

Riverside built its prototype on Prism, then moved `apps/web` to the real server (RO-20 to RO-22). Its git history
and `SUBMISSION.md` record what the real server exposed:

1. **Server-omitted optional fields crashed screens.** Commit `20c0dd4` ("staff SCR-21/22 read contract-optional
   fields the server omits (walkthrough D-4: every enquiry detail crashed; unbooked rows said 'in home')"), with
   `0cfb838` and `f792b89`. The RO-18 plan serialises bodies with `exclude_none=True`, so optional keys disappeared.
   This is G-01 here.
2. **A fixed Prism "first example" shape hid a server contract error.** Commit `7db22e9` ("bank answer ids accepted
   as value_code (walkthrough defect: every help answer matching a suggestion was discarded as invalid_output)"). The
   mock accepted any answer; the real server rejected the ids the UI sent. This is the AEA analogue of G-07 and G-12
   (the mock ignores request bodies).
3. **Mock-mode stand-ins sent fabricated ids and fake turns.** `RO-22 Part D1` (merge `4809588`) removed a synthetic
   enquiry id, and commits `f067b16` / `564736c` fixed an Edit that "sent a fake turn". These were frontend behaviours
   that only worked because the mock accepted anything. Compare AEA's `?ex=` forcing and the chat director.
4. **The contract was only closed after the fact.** `docs/plans/fanout/2026-10-19-ux4-integration/A-contracts.md`
   records that "Prism reports 0 request violations only because no request schema sets `additionalProperties: false`",
   that operations borrowed other operations' bodies, and that a fallback chain (`slotId ?? slot_id ?? id`) "hides drift".
   AEA has the same zero `additionalProperties` (G-07). RO-22 Part E then added 11 missing response codes to the
   contract (`68880d9`), the AEA analogue being the 403/429/400 gaps above.

Riverside's own QA register states the limit plainly: "Every row is evidence about the prototype running on mocks.
None of it is evidence about the real backend" (`docs/ux/05-verify/QA_REPORT.md`). The same sentence applies to this repo.

### 3.5 Source defects the new tests found (all fixed in `src/`, none in the OpenAPI file)

Each was found by a new test failing against unchanged source, then fixed with the smallest edit that makes it pass. The
old tests were not touched and still pass.

| # | Defect | Fix | Found by |
|---|---|---|---|
| 1 | A measure whose `value`, `numerator`, `denominator`, `min`, `max` or `target` is **omitted** (not null) printed `undefined`, `NaN s`, "undefined of 74 turns" or dropped the reason line, because the code tested `=== null`. SCR-9, SCR-10, SCR-11. | `=== null` / `!== null` became `== null` / `!= null` in `screens/reads/format.ts`, `screens/reads/MeasuresTable.tsx`, `screens/scr09/Scr09.tsx`, `screens/scr10/Scr10.tsx`, `screens/scr11/evalRows.ts`. | `screens/omitted.keys.test.tsx` (SCR-9, SCR-10, SCR-11) |
| 2 | A `403 ROLE_NOT_ALLOWED` (demo reset or role change on the server) left the browser's session on the old role: the role switch kept showing Representative while the server treated the user as Customer; a case stream that answered 403 stopped silently with the live box still "live". | New signal `emitRoleDenied` / `onRoleDenied` in `api/refetch.ts`, raised by `api/client.ts` on a 403 `ROLE_NOT_ALLOWED` and by `api/transport.ts` on a stream 403; `state/session.tsx` re-reads `getSession` on it. | `state/roleDenied.test.tsx` (G-06, G-13) |
| 3 | A case with `promise.follow_up.window` omitted lost the "No preference" label; a source with `current` omitted showed a "Now" column of `undefined` values. SCR-6. | `window == null` in `screens/scr06/caseText.ts`; `current != null` in `screens/scr06/SnapshotTable.tsx`. | `screens/omitted.keys.test.tsx` (SCR-6) |
| 4 | A case-stream event replayed after a reconnect (same `event_id`) was added to the timeline twice ("Chat closed at 2:24 pm" twice, duplicate React keys). The chat stream already de-duplicated; the case stream did not. | `withEvent()` in `screens/scr06/caseReducer.ts` ignores an event id it already holds. | `screens/scr06/caseStream.replay.test.tsx` |
| 5 | A settled visit with `change_request` omitted was treated as "original stays" (`!== null`), changing the panel text. SCR-1. | `v.change_request != null` in `screens/scr01/core/components/SettledPanel.tsx`. | `screens/scr01/chat.omitted.test.tsx` (BOOKED) |
| 6 | A 401 with `details.reason = "expired"` (from `getSession`, any call, or a stream) navigated to `/login?...&reason=expired` and was immediately overwritten by `RequireSession` with `reason=none`, so the login page never said the session had ended. | `SessionProvider` keeps `lostReason`; `RequireSession` in `router.tsx` forwards it. | `state/session.stream.test.tsx` |

Every fix has a failing-before / passing-after test above. Fix 2 adds a request on every 403 (one `getSession`); it cannot loop,
because a 401 from that read raises the existing auth-lost signal, not the new one.

### 3.6 Observations not fixed (product or backend decisions, listed so they are not lost)

- **Supervisor on a joined live chat.** SCR-6 shows an active reply box to the supervisor; the server's live action is representative-only (`NOT_CLAIMED_BY_YOU`, section 4.4). The refusal is handled ("Claim the case first.", `routes.guards.test.tsx`), but whether a supervisor may reply is a product decision.
- **Copy that differs from `UI_CONTRACTS.md`.** 403 on case writes reads "You can't do that as Riley, demo representative." (contract: "This isn't available to the demo [role] role."); `advanceDemoClock` 403 reads the generic clock line; SCR-2's 429 reads the inbox sentence.
- **Reset sentence after a 403.** The contract's "The demo was reset, so you're back to the customer role. Pick a role again." exists in `RoleNotAllowedPanel` (`reset`), but once the session is re-read the role gate shows the ordinary panel instead.
- **Case stream after `chat_closed`.** It stays subscribed (a later `case_changed` is legal) and re-asks every 1 s if the server ends it each time. Pinned in `screens/scr06/caseStream.replay.test.tsx`; needs the real server's behaviour.
- **Streams that stop for good (404, 410) show nothing.** Tested to stop quietly (`api/transport.stream.test.ts`); the page does not say the live view has stopped.
- **`assign` and `change_priority` forms send `reason: ""` when left empty.** Valid against the schema; the server answers `REASON_REQUIRED`, which renders correctly.

---

## 4. Integration dependencies by flow

The backend plan (areas from `docs/design/code-design.md` section 8; tickets from `docs/plans/slice-plan.md` and
`docs/plans/tickets/`): **A8** customer API (AEA-23 app, middleware and demo login; AEA-40 CON-1/2; AEA-41 CON-3;
AEA-42 CON-4/5; AEA-43 CON-6 to 9), **A9** staff console (AEA-44 CON-10; AEA-45 CON-11 to 13, 15 to 17; AEA-46 CON-14
and CON-21; AEA-47 CON-8 advance), **A10a/A10b** ops and reads (AEA-48 CON-18 to 20, AEA-53 metrics reader),
**A12** deploy (AEA-49 serves `apps/web/dist`, AEA-50). Support: AEA-57 journey harness (real server, disposable DB,
scripted model), AEA-58 browser journeys, AEA-59 contract boundary, AEA-51/52 integration A/B, AEA-55 UI integration.
Owners of the behaviour behind the routes: AEA-27 identity and code, AEA-28 scheduling, AEA-29 cases and handoff,
AEA-30 demo clock and staffing, AEA-31 reset, graph AEA-21/34 to 39.

Backend journey ids (J-1 to J-10) are defined in `docs/plans/slice-plan.md`. Browser journeys below are the
frontend names to write; they reuse those ids. `docs/plans/ux-join/` is cited by the slice plan as the place for the
UX session's join deliverables, but it does not exist yet; this document is the first of those.

Common to all flows `REAL-BACKEND: none`. Order of arrival matters because each flow needs the one before it.

### 4.1 Order the real backend must arrive in

1. AEA-23 (app, middleware, login, `mhc_session`, error envelope, `Retry`/rate-limit hooks) and AEA-49 (serve `dist`): nothing in the UI loads without them.
2. AEA-44 (`getSession`, `listDemoRoles`, `switchRole`) with AEA-43 (inbox, staffing, clock read, reset).
3. AEA-40, 41, 42 (customer chat), with the scripted model of AEA-57 and booking via AEA-28, identity via AEA-27.
4. AEA-29, 30, 31, then AEA-45, 46, 47 (staff side).
5. AEA-48 and AEA-53 (reads), AEA-32 (alerts feeding monitoring).
6. AEA-51, 52 (integration), AEA-58 (browser journeys on `dist`), then AEA-55 (this UI against the real backend, `gate::ux5`).

### 4.2 Customer chat (CON-1, 2, 3, 4, 5)

- **Operations:** `startChatSession`, `getChatThread`, `submitTurn`, `streamChatEvents`, `requestPerson`, `saveFollowUp`.
- **Backend must provide:** thread owned by the login session; `last_event_id` on start and thread so the stream can resume;
  whole replies in `blocks` with `settled`; composed outcomes as HTTP 200 (`notice`, `error` blocks); `turn_id`
  idempotency (a finished turn returns the stored reply; a failed one re-runs); `TURN_IN_PROGRESS` with `retry_after_ms`;
  60 s `TURN_TIMEOUT`; 30-in-flight `BUSY`; SSE with replay on `Last-Event-ID` (WEB-16).
- **Journey names:** `chat.start-resume` (J-1), `chat.grounded-answer` (J-2), `chat.retry-same-turn-id` (J-1/J-9),
  `chat.timeout-and-busy` (J-9).
- **UNVERIFIED until then:** `turn_id` retry returns the stored reply `[MOCK-ONLY]` today; `TURN_IN_PROGRESS`
  semantics; `TURN_TIMEOUT` at 60 s against a slow scripted model (the 65 s browser give-up is a fake-timer `UNIT`);
  resume with a populated thread (nullable block fields, G-01/G-10); rate limit as 200 `RATE_LIMITED` vs 429.

### 4.3 Booking (slot_card, bookSlot, SLOT_TAKEN, confirmation)

There is no `bookSlot` operation. Booking is a `submitTurn` with a `choice` payload (`ChoicePayload`: `card_id`,
`option`) on a `slot_card` block; the result is an `appointment` or `confirmation` block, `SLOT_TAKEN` is an `error`
block with a fresh slot card, and `settled.visit` carries the booking.

- **Backend must provide:** AEA-28 windows and write; AEA-27 verified identity gate (code card: `CODE_SENT`,
  `CODE_WRONG`, `CODE_EXPIRED`, `CODE_LOCKED`, `CODE_CAP_REACHED`); `window_label` formatted like the spec examples.
- **Journey names:** `booking.slot-to-confirmation` (J-3), `booking.slot-taken-refresh` (J-3/J-9), `booking.fee-bearing-change` (J-4).
- **UNVERIFIED until then:** `SLOT_TAKEN` race (a second browser takes the slot); the confirmation's `appointment_id`
  against the DB; follow-up "yes, please" remembering the booked action (WP-3, WP-4F); ISO vs `window_label` agreement.

### 4.4 Staff handoff (requestPerson, queue, claim, join, live chat, hand back, close)

- **Operations:** `requestPerson`, `getQueue`, `getCase`, `applyCaseAction`, `liveChatAction`, `streamCaseEvents`,
  `streamChatEvents` (the customer's view), `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag`.
- **Backend must provide:** case with 8-heading brief and promise (AEA-29); version field and `VERSION_CONFLICT` with
  `details.current_version` (the UI shows who changed it); `allowed_actions` per role and lifecycle; `claim` then `join`
  as two calls (the UI runs `getCase`, claim, join in order and tells a half-success apart, `scr06/claimAndJoin.ts`);
  case stream events `customer_message`, `controller_changed`, `case_changed`, `chat_closed`, `demo_reset`; chat stream
  events `representative_joined`, `ai_paused`, `staff_message`, `ai_resumed`, `chat_closed`.
- **Journey names:** `handoff.request-to-queue` (J-6), `handoff.claim-join-reply` (J-7), `handoff.hand-back-and-close` (J-7),
  `handoff.version-conflict-two-staff` (J-6/J-7), `handoff.flag-and-review` (J-6).
- **UNVERIFIED until then:** both streams' event ids and replay; `VERSION_CONFLICT` and `CASE_ALREADY_CLAIMED` from a real second
  session; `NOT_CLAIMED_BY_YOU` (representative-only live action, so a supervisor takeover cannot work); idempotency of the
  claim button on double click (`applyCaseAction` has no idempotency key).

### 4.5 Login, session, role (CON-10, CON-22)

- **Backend must provide:** `login` sets `mhc_session` (`HttpOnly`, `SameSite=Lax`, `Secure` in deploy); the role lives in
  the cookie; `switchRole` changes it; `getSession` returns the right `SessionInfo` for all four roles; 401 with
  `details.reason = "expired"` after expiry; 403 `ROLE_NOT_ALLOWED` and `ROLE_NOT_ALLOWED_ROLE_RESET` after a demo reset.
- **Journey names:** `session.login-return-to` (J-1), `session.role-switch-reload` (J-8), `session.expired` (J-8),
  `session.role-reset-after-demo-reset` (J-8).
- **UNVERIFIED until then:** 401/403 enforcement **by real cookie** (the dev layer decides today, `dev/resolve.ts`);
  `Secure` cookie behaviour on `http://127.0.0.1`; `getSession` for supervisor and owner after reload; the shape of
  `details.reason`.

### 4.6 Demo controls and oversight/reads (CON-6 to 9; CON-16 to 20)

- **Demo controls (CON-6 to 9):** inbox (code messages with masked recipient), staffing toggle (`converted_cases` on
  turn-off), clock (supervisor advance; `ADVANCED`), reset (all-or-nothing; `open_chats_ended`, `roles_reset`, 409/503
  during reset). **Journeys:** `demo.inbox-code-read` (J-3), `demo.staffing-off-converts-waiting` (J-7), `demo.clock-advance-overdue` (J-6),
  `demo.reset-ends-chats-and-roles` (J-8).
- **Oversight and reads (CON-16 to 20):** five lanes (`getOversight`), owner metrics with seeds and `null_reason`,
  monitoring with alerts and `fired_at`, latest eval (both splits, `NO_RUN`). **Journeys:** `reads.oversight-after-advance` (J-6),
  `reads.owner-metrics-stored` (J-10), `reads.monitoring-alert-firing` (J-10), `reads.eval-no-run` (J-10).
- **UNVERIFIED until then:** reset while a stream is open (`demo_reset` event on both streams, 503 on every call in between);
  alert `fired_at` and `case_ref` nulls; metric denominators being stored counts, not recomputed (AEA-53); `data age`
  line against the real clock; polling rate limits (SCR-2 polls every 5 s, SCR-5 and SCR-7 poll for changes).

### 4.7 The cross-flow journey (verify customer chat, booking and staff handoff together)

One browser journey, two browser contexts (customer and staff), because the failures that matter appear at the seams:

**`journey.customer-booking-then-person`** (backend ids J-3, J-6, J-7, J-8):

1. Staff context: login, `PUT /api/session/role` to representative, open `/staff/queue`; staffing on via `setStaffing`
   (supervisor, or a seeded state).
2. Customer context: login, open `/`, ask a question that leads to the slot card, pick a window (`submitTurn` choice),
   see the confirmation (assert `settled.visit` in the side panel and the stored appointment via the AEA-57 DB reader).
3. Customer: attempt a second booking so `SLOT_TAKEN` is returned (second context holds the slot), see the fresh slot card.
4. Customer: press **Talk to a person** (`requestPerson`), see the `live_queued` card and a `case_reference`.
5. Staff: the queue shows the live row (without reload, via the poll or stream); **Claim and join**
   (`getCase`, `applyCaseAction` claim, `liveChatAction` join); the case brief shows the booking attempt and the
   `SLOT_TAKEN` outcome; the AI is paused on the customer side (top bar names the representative, `ai_paused` event).
6. Staff sends a message (`liveChatAction` send). **Customer sees the representative message** in the thread
   (`staff_message` frame, ids replayed correctly on a mid-way page reload of the customer tab).
7. Staff hands back (`handed_back`): customer sees the assistant return (`ai_resumed`). Staff closes: customer
   composer is ended.

Pass condition: every step passes in `E2E_MODE=proxy`, with Prism validating every response (`--errors`), no
`[contract drift]` console error, one axe pass at steps 2, 5 and 7, and a persisted-state assertion (case row, message
rows) after steps 2, 4 and 6. Write the **mock rehearsal first** (the dev layer's `emit` reaction plays steps 5 to 7
from two scripted streams) so every selector exists before the backend does; label it `MOCK-ONLY` and do not count it.

Additional required journeys listed above map to the backend plan: `chat.start-resume`, `session.role-switch-reload`,
`demo.reset-ends-chats-and-roles`.

### 4.8 UNVERIFIED register (all `MOCK-ONLY` or `UNIT` at best)

| Item | Today | Needs |
|---|---|---|
| SSE replay by event id | `UNIT` (2026-10-21): the real `openStream` loop resends `Last-Event-ID` (14 for the spec's ids 12 to 14), never lowers it, backs off 1, 2, 4, 5 s, and both screens show a replayed frame once (`api/transport.stream.test.ts`, `screens/scr06/caseStream.replay.test.tsx`); no server has produced a frame | `chat.start-resume` with a mid-stream reload against a real server |
| 401/403 enforcement by real cookie | dev layer (`dev/resolve.ts`) and `smoke.spec.ts` URL flag | `session.*` journeys, `REAL-BACKEND` |
| Idempotency / `turn_id` retry | `UNIT` `useChat.test.tsx` (same id re-sent); store-and-return untested | `chat.retry-same-turn-id` |
| `Idempotency-Key` header | **not in the spec** (zero matches in the OpenAPI); the web client does not send one; `turn_id` is the only key, and writes in CON-13/14/15/16 have none | decide: spec request to the UX owner, or accept double-submit guards in the UI only |
| Version conflicts | `UNIT` with the spec's `VERSION_CONFLICT` body (`screens/errors.spec.test.tsx`) | `handoff.version-conflict-two-staff` |
| Rate limits (429, 200 `RATE_LIMITED`) | `UNIT` for the 200 composed notice and (2026-10-21) for every 429 the spec lists, built from the spec's `REQUEST_RATE_LIMITED` body (`screens/errors.spec.test.tsx`, `screens/polled.reads.test.tsx`) | a real limiter test |
| `TURN_TIMEOUT` | fake timers | slow scripted model |
| ISO times vs `*_label` | both printed; some labels parsed | G-09 and AEA-59 label equality |
| `getSession` for all four roles after reload | dev layer replays `switchRole` | `session.role-switch-reload` |
| Reset during open streams | scripted `demo_reset` event | `demo.reset-ends-chats-and-roles` |

---

## 5. Connect-to-real-backend procedure

### 5.1 Facts about the current wiring

- `npm run dev` (script `vite --host 127.0.0.1 --port ${WEB_PORT:-5184} --strictPort`): non-mock mode. `vite.config.ts`
  proxies `/api` to `http://127.0.0.1:${API_PORT:-8000}` with `changeOrigin: true`. **This path has never been run
  against anything** (README: "not built yet"). No dev layer is installed (`src/main.tsx` only does so when `MODE === "mock"`),
  so the app comes up signed out and goes to `/login`.
- `npm run dev:mock` (`vite --mode mock`): proxy target is Prism at `MOCK_PORT` (4019) and the dev layer is installed.
- Ports: web 5184, Prism 4019, API 8000. Other projects own 4010/5173, 4012/5180, 4013/5183; AEA tickets are told never to bind 4019 or 5184 (`docs/plans/tickets/_conventions.md`).
- The client always sends `credentials: "include"`, calls relative `/api/...` URLs, and reads cookies never. The server paths in the OpenAPI already start with `/api`, so the backend app must mount under `/api` (or sit behind a proxy that does).
- Demo credentials come from the server settings `MERIDIAN_DEMO_USERNAME` / `MERIDIAN_DEMO_PASSWORD` (AEA-23); the dev layer accepts anything.

### 5.2 Steps (first connection, manual)

1. Start the backend on `127.0.0.1:8000` (AEA-57 harness or the dev server once A8 exists) with a disposable DB and the scripted model; set the demo credentials.
2. `cd apps/web && API_PORT=8000 npm run dev` (this regenerates `types.gen.ts` and `contract.gen.json` first via `predev`; `npm run check:gen` must be clean).
3. Open `http://127.0.0.1:5184/` (from a laptop: `ssh -L 5184:127.0.0.1:5184 claude-vultr`). Expect the redirect to `/login?return_to=%2F&reason=none`. Sign in with the demo pair. Check the `Set-Cookie` in DevTools (`HttpOnly`, `SameSite=Lax`; on http the `Secure` flag must be absent or Chrome must accept it on 127.0.0.1) and that `GET /api/session` returns 200.
4. Walk the screens with each role; record first failure per operation as a bug against the owning ticket in section 4.
5. Watch the browser console: there will be no `[contract drift]` lines, because that detector exists only in the dev layer. Use proxy mode (5.3) to get drift detection against a real server.

### 5.3 Prism in proxy mode (validating real responses)

Per `ux-pipeline/references/phases.md` UX-5, "UX-5 runs twice": the second run, after the build, runs the same
Playwright tests with Prism in **proxy** mode, so any response that breaks a UI contract fails.

```
# terminal 1: the real backend on :8000
# terminal 2: Prism validates and forwards
cd apps/web
npx prism proxy ../../docs/ux/03-structure/ui-contracts.openapi.yaml http://127.0.0.1:8000 \
    -p 4019 -h 127.0.0.1 --errors
# terminal 3: Vite, non-mock, pointing at Prism
MOCK_PORT=4019 API_PORT=4019 npm run dev
```

`--errors` makes Prism return an error for a request or response that violates the document, so a bad real response
fails the test visibly. (Check the flag name against the installed version, `@stoplight/prism-cli` 5.15.11, with
`npx prism proxy --help` before relying on it; it has not been run here.) Prism proxy needs the cookie to pass
through unchanged; `credentials: "include"` and `changeOrigin` already do this.

### 5.4 Switching the e2e suite to proxy mode

Today `playwright.config.ts` hard-starts `npm run mock` and `npm run dev:mock` with `reuseExistingServer: false`, and
every spec enters its state with dev-layer URL parameters. To run in proxy mode:

1. Do G-02 first (the `enter()` helper and `E2E_MODE`). Without it, no existing spec can run.
2. In `playwright.config.ts`, when `E2E_MODE=proxy`: `webServer` starts only Prism proxy and `npm run dev` (the backend is started outside Playwright or by AEA-58's runner), `reuseExistingServer: true`, and the base URL stays `http://127.0.0.1:5184`.
3. Tag forced-failure scenarios `@mock`; skip them in proxy mode (`--grep-invert @mock`). Keep the sweep (axe, layout, screenshots) in both modes, but remember G-16.
4. Fail the proxy run on any non-2xx the test did not expect (the sweep's `watchFlow` already lists them as annotations), and on any Prism violation (`sl-violations` header or a Prism error body; `detectDrift` in `dev/transport.ts` is the pattern to reuse in a Playwright `page.on("response")` hook).
5. Run under a hard cap: `perl -e 'alarm 500; exec @ARGV' npx playwright test`.
6. Both viewports (1280 and 390) and axe on every state visited stay in force (UX-5 pitfalls in `phases.md`).

### 5.5 Exit criteria per flow

A flow is done when the stated journey passes `REAL-BACKEND` in proxy mode **and** its unit gaps are closed:

| Flow | Exit criteria |
|---|---|
| Login / session / role | `session.*` journeys pass with a real cookie; 401 expired and 403 role-reset both land in the right place; no dev-layer parameter needed; G-06 closed. |
| Customer chat | `chat.*` journeys pass; a reload resumes the thread with the stream replaying from `last_event_id`; `turn_id` retry returns the stored reply; G-01, G-04, G-10, G-14 closed. |
| Booking | `booking.*` journeys pass including `SLOT_TAKEN`; DB shows exactly one appointment; the confirmation window equals the stored window. |
| Staff handoff | `handoff.*` journeys pass with two real sessions; `VERSION_CONFLICT` provoked by a real second session; `journey.customer-booking-then-person` (4.7) passes end to end; G-04 (case stream), G-13, G-15 closed. |
| Demo controls | `demo.*` journeys pass; reset during open streams ends chats on both sides; G-08 closed. |
| Oversight and reads | `reads.*` journeys pass; metrics equal stored counts; G-01 (null reasons, `fired_at`) closed. |
| Whole app | Prism proxy run reports 0 violations; zero `[contract drift]` or `console.error` in all journeys; `INTEGRATION_HANDOFF` UNVERIFIED register (4.8) has no remaining `UNVERIFIED` row; G-02, G-05, G-07 closed; the slice plan's AEA-55 gate (`gate::ux5`) can be ticked. |

---

Unit-side status (2026-10-21): G-01, G-04, G-05, G-06, G-07, G-08, G-13, G-14 and G-15 have their unit tests (3.1), so the
"and its unit gaps are closed" half of each row above is met for those items; G-02, G-03 and G-16 (e2e) are still open, and no row's
`REAL-BACKEND` journey exists yet.

---

## 6. Documents read

`docs/ux/03-structure/ui-contracts.openapi.yaml` (30 `operationId`s), `apps/web/src/api/{types.gen.ts, contract.gen.json,
client.ts, transport.ts}`, `apps/web/src/dev/**`, all `*.test.ts(x)` under `apps/web/src` (711 test titles, 140 `describe`
blocks), `apps/web/tests/e2e/*`, `docs/ux/04-prototype/{PROTOTYPE_PLAN.md,groups/*.md}`,
`../.claude/skills/ux-pipeline/references/phases.md` (UX-5), `docs/design/contracts/README.md`,
`docs/design/code-design.md` (areas A0 to A12), `docs/plans/slice-plan.md`, `docs/plans/tickets/*.md` (titles),
`../inno-riverside-onboarding` (git log, `SUBMISSION.md`, `docs/plans/fanout/2026-10-19-ux4-integration/A-contracts.md`, `docs/ux/05-verify/QA_REPORT.md`).
Not run: Playwright, Prism, the dev server or any test suite (read-only audit); every test name above was read from source.

---

## E2E status (G-02 and G-03, 2026-10-21)

Written by the e2e session; the matrix cells above are untouched. Files: `apps/web/tests/e2e/support/state.ts` (new),
`apps/web/tests/e2e/journey-chat-booking-handoff.spec.ts` (new), `smoke.spec.ts` and `sweep.spec.ts` (refactored onto
`state`), `apps/web/playwright.config.ts` (target switch). Env var is `E2E_TARGET=mock|real` (not `E2E_MODE=proxy` as 3.2 and 5.4 proposed).

| Item | Status | Tag |
|---|---|---|
| G-02 pluggable state: `state.signInAs / visitSignedOut / applyScenario / setStaffing / reset`, two implementations | **Done.** Mock keeps the dev-layer URL parameters (same URLs as before). Real signs in through SCR-12, switches role through the "Acting as" control, sets staffing and resets through SCR-3, sends no dev parameter, and skips any scenario with the reason "needs dev-layer forcing". | `MOCK-ONLY` (mock path run); real path **not run** (nothing on :8000) |
| smoke (14 tests) and sweep (12 flows incl. the 4 interaction flows) on `state` | Mock results unchanged in kind: all pass; the chat-reply flow asserts the fee sentence in mock and only "a reply entry follows" in real (G-12). | `MOCK-ONLY` |
| G-03 journey `journey.customer-booking-then-person` (section 4.7), hand-back and close variants | **Mock rehearsal passes** on desktop and phone (2 tests each, repeated 2x). Real variant written, tagged `[REAL-BACKEND — not yet run]`, skips if `GET /api/healthz` fails. | `MOCK-ONLY` rehearsal; does not count as `REAL-BACKEND` |

What the mock cannot rehearse faithfully (each place is marked `MOCK:` in the spec): the dev world is per browser page, so the
customer and staff contexts share nothing. (1) `SLOT_TAKEN` comes from the chat director, not from a second customer. (2) "Talk
to a person" is forced to `LIVE_QUEUED` and returns MHC-C-0007 while the staff queue's seeded live row is MHC-C-0012. (3) Every
chat stream event (`representative_joined`, `ai_paused`, `staff_message`, `ai_resumed`, `chat_closed`) is pushed into the
customer tab with `window.__mhcDev.emit`, carrying the text the staff tab really sent: this proves the customer screen renders
them, not that a server delivers them or replays ids. (4) The case brief is the fixed mock one (no booking attempt, no
`SLOT_TAKEN`). (5) No persisted-state assertions (case row, message rows, reload replay): the real variant has them, unrun.
The real-mode booking steps (second customer takes the window: identity form, code from SCR-2) are assumptions about the
scripted model and the seeded identity (`E2E_CUSTOMER_NAME`, `E2E_CUSTOMER_PHONE`).

Finding from the rehearsal: on the 390 px phone, after Claim and join the case view stays on the "Brief" tab and the live reply
box is under "Evidence", so a representative must tap Evidence to reply. The journey does that tap on the phone.

Commands (from `apps/web`):

```
# mock (default): starts Prism :4019 and vite --mode mock :5184 itself
timeout 600 npx playwright test --project=chrome-desktop --workers=6 --fully-parallel
timeout 600 npx playwright test --project=chrome-phone   --workers=6 --fully-parallel
npx playwright test journey --project=chrome-desktop            # just the rehearsal

# real: start nothing from Playwright. Backend first, then a NON-mock dev server that proxies /api to it
API_PORT=8000 npm run dev                                       # terminal 1 (backend already listening on :8000)
E2E_TARGET=real E2E_USERNAME=<demo user> E2E_PASSWORD=<demo password> \
  E2E_CUSTOMER_NAME=<seeded name> E2E_CUSTOMER_PHONE=<seeded phone> \
  npx playwright test journey smoke --project=chrome-desktop    # terminal 2; E2E_BASE_URL overrides http://127.0.0.1:5184
# with Prism validating (5.3): API_PORT=4019 npm run dev, Prism proxy on 4019 -> :8000, same E2E_TARGET=real command
```

Real mode: `sweep.spec.ts` scenarios all skip (every one is dev-forced); `state.reset()` resets the shared backend for everyone;
run real-mode workers=1 (the config default). Not yet checked in real mode: the spec's selectors beyond what the mock renders.

Full-sweep reliability note: the machine was at load 12 to 25 and another session regenerated `src/api/types.gen.ts` and
`contract.gen.json` repeatedly, which makes the Vite dev server full-reload pages mid-test. At 6 workers 106 (desktop) and 67 (phone)
sweep scenarios failed with `h1 count 0` or "Execution context was destroyed"; the failing set changed every run, and every
failed scenario passed when re-run with fewer workers (desktop: 106, 26, 24, 6, then 0; phone: 67, 16, then 0). No failure was
in smoke, the journey, or a flow other than one role-switch flow that passed on re-run.
