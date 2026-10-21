# UX ↔ backend join audit: customer side

**Date:** 2026-10-21. **Kind:** read-only audit (nothing in `apps/web/**`, `docs/ux/**` or any ticket was edited).
**Verification level:** reading only. No test, build or server was run for this audit; where a check below says
"passes", it quotes `docs/ux/04-prototype/PROTOTYPE_PLAN.md`, which is itself `mock-tested`
(`.claude/rules/integrated-journeys.md` §4).

**Scope.** CON-22 demo login, CON-1 session start and thread, CON-2 turns, CON-3 event stream, CON-4 person request,
CON-5 follow-up, CON-6…CON-9 demo inbox, staffing, clock read and reset; the SCR-1 chat (cards, "What's settled",
notices BUSY / TURN_TIMEOUT / RATE_LIMITED, refresh and resume), SCR-2, SCR-3 and SCR-12.

**Which source wins.** The OpenAPI (`docs/ux/03-structure/ui-contracts.openapi.yaml`) wins on every wire shape and code.
For backend behaviour the stage-7 addenda win over the ticket text: AEA-40…AEA-43 (dated 06:37) are not yet rewritten,
so `docs/design/contracts/stage7/web.md` and `docs/plans/7b-decisions/web.md` are read as their truth; AEA-23, AEA-26…29
and AEA-49 were read in their rewritten form (08:05–08:14).

**Severity.** **H** = a journey in the slice plan's map (J-1…J-9) fails or a screen cannot load in production.
**M** = a real-backend state the UI shows wrongly or a journey cannot assert reliably. **L** = cosmetic, a latent edge,
or a cost.

## What this looks like in practice (one example)

A reviewer is in a live chat. Riley (demo representative) has joined and written "Hi Omar, I can look at the
after-hours charge with you." The reviewer presses reload.

- **What the UI does.** It reads the thread id from `sessionStorage`, calls `getChatThread`, rebuilds the thread from
  `turns`, and reopens the CON-3 stream from the thread's **newest** event id (`useChat.ts:76-82`). Its history mapper
  is ready to draw staff messages and event lines from `turns` (`replyGroups.ts:58-61`).
- **What the backend will send.** `SessionService.thread` builds `turns` from "the thread's customer messages (text) and
  each completed turn's stored response blocks" (`stage7/web.md:485-489`). Riley's message, "Riley has joined", "The
  assistant is paused" and the greeting are not turns, and the stream will not replay them because it starts after them.
- **What the reviewer sees.** Their own messages and the assistant's replies, the panel saying a person is replying, and
  none of Riley's words. That is finding **A-1**, the first row below.

## (a) Fields, nulls, empty lists and enums

| ID | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| A-1 | Resume loses everything that is not a customer message or a stored turn reply: the greeting (the US-1 "automated assistant" disclosure), representative messages, joined / paused / resumed / closed / staffing lines and the `shift_ended` handoff card. The UI expects them in `ChatThread.turns` and starts the stream after them. The UX plan already records "event lines are not stored" as a spec gap. | H | UI: `apps/web/src/screens/scr01/core/replyGroups.ts:50-64`, `core/useChat.ts:82`; plan: `docs/plans/fanout/2026-10-21-ux4/g1-chat-core.md:654`. Backend: `docs/design/contracts/stage7/web.md:485-489` (turns), `:400-403` (stream starts at the id the browser holds); staff messages are `messages` rows (`stage7/staff.md:320-326`). OpenAPI already allows them: `ChatThread.turns[].speaker` is `Speaker` with kinds `representative` and `event` (`ui-contracts.openapi.yaml:8203-8220`, `:9878-9903`) | AEA-40 (`SessionService.thread`) | AEA-40's rewrite states that `turns` holds, in time order: the greeting (assistant, `blocks: [TextBlock]`), every customer message, every completed turn's blocks, every representative message (`speaker.kind: representative`, `text`), every stored chat-event line (`speaker.kind: event`, `text` = the stored `line`), and a `shift_ended` handoff as an assistant turn with `blocks: [HandoffBlock]`. No OpenAPI change. The UI side needs no change for this shape. (Replaying the stream from 0 instead is not safe as built: `shift_ended` replaces `settled` with its old snapshot, `core/reducer.ts:113-115`.) |
| A-2 | A CON-4 person request is not a "turn reply" in the stored shape: its stored response is `{result, block, settled}`, not `blocks`, and no customer message row is written. After reload the handoff card (and its follow-up chooser) may be missing; the panel still shows the reference. | M | UI live: `core/useChat.ts:240-246`, `core/reducer.ts:89-95`. Backend: `stage7/web.md:290-294` (`PersonRequestOutcome`), `:316-318` (stored response), `:485-489` | AEA-40 + AEA-42 | `SessionService.thread` maps a CON-4 turn row to a customer turn (`text` "Talk to a person") plus an assistant turn with `blocks: [block]`. Write it into both rewrites. |
| A-3 | Card `answered` is lost on reload. Stored blocks keep `answered: null` from reply time; the UI's own `answered` map lives only in memory. After reload every slot card, yes/no and quick-check card is tappable again; a tap reaches the backend as a stale card and becomes free text with the option string (no write, but a confusing reply). | M | UI: `core/replyGroups.ts:34-38`, `core/model.ts:49` (`answered` in state only). Contract field: `HandoffBlock.answered` "The option already chosen, or null" (`ui-contracts.openapi.yaml:9313-9317`; same field on every card block). Backend: stored response is opaque (`stage7/web.md:486-487`); stale card → `FREE_TEXT` (`stage7/graph-core.md:216`) | Decide one: AEA-40 or UX session | Recommended AEA-40: `thread()` sets `answered` on each card block from the next customer turn that names its `card_id`, since `answered` is a contract field. Fallback in the UI: treat every `live: false` card as answered except the newest unanswered one. |
| A-4 | Try again after a reload sends a corrupted payload. History rebuilds every customer payload as `{kind: "text", text}` from the stored, redacted text ("[code entered]", "[details submitted]", or "Choice sent"). A TURN_TIMEOUT notice in history has no `card_id`, so its Try again stays enabled; it resends the latest customer turn with the same `turn_id`, and the backend re-runs a timed-out turn with the new payload. | M | UI: `core/replyGroups.ts:53-55`, `cards/NoticeCards.tsx:15`, `core/useChat.ts:275-284`. Backend: `docs/plans/tickets/AEA-40.md` AC-3 (failed or timed-out turn re-runs), AC-2 / AC-7 (stored redacted text) | UX session | Disable Try again on history entries (`live: false`), or retry only entries whose original payload is held locally. |
| A-5 | "What's settled" hides a cancellation. After a cancel, `settled.visit` is `null` (a cancelled visit is never "the visit"); the panel then says "Nothing booked yet." and draws the earlier-actions list only when a visit exists, so the cancel in `settled.actions` is not shown. The "earlier" list is also built by position (`slice(0, -1)`), which is wrong when the newest visit action cancels a second booking (the cap is 3). | M | UI: `core/components/SettledPanel.tsx:31`, `:45-65`. Backend: `stage7/graph-core.md:568-574` (`current_visit()`); `SettledVisit.status` has no `cancelled` (`ui-contracts.openapi.yaml:8381-8386`) | UX session | When `visit` is null, list the visit actions' `summary` lines; when it is not, list every visit action except the newest `booked`/`moved` one. |
| A-6 | Inbox code after a server restart: the process no longer holds the digits, so `code` is `"······"`, but the row can still read `active`. The UI enables Copy for `active` and reads the dots aloud one by one. | L | UI: `screens/scr02/InboxMessageCard.tsx:56-59`, `:66`. Backend: `stage7/graph-tools.md:333-334`, `:361-365` | AEA-27 / AEA-43; UX session | Backend reports `status: "expired"` whenever `code` is None. UI enables Copy only for a 6-digit code. |
| A-7 | History wording differs from the live row: live says "Code entered", "Details sent" or the option's label; reloaded rows show the stored "[code entered]", "[details submitted]", the raw option string, or "Choice sent" when `text` is null. | L | UI: `core/rowText.ts:8-12`, `core/replyGroups.ts:54`. Backend: AEA-40 AC-7; `stage7/graph-core.md:216` (stale choice stored as its option string) | AEA-40 + UX session | Agree one display text per payload kind; AEA-40 stores or maps to it. |
| A-8 | `ChatThread` has no `limits`; the UI caches them in `sessionStorage` and falls back to a hard-coded copy. Equal today; a resumed tab keeps stale values if `policy/limits.py` changes. | L | `core/storage.ts:5-13`, `core/pending.ts:12`; `ui-contracts.openapi.yaml:9867-9920` | UX session (accept) | Note only; adding `limits` to `ChatThread` would be an OpenAPI change (Innocent). |

## (b) Frontend state vs backend state

Checked and consistent: `settled`, the controller (`replying`), identity status, the clock and staffing all come from
server responses or events; the role comes from `getSession` / `switchRole`; the browser keeps only the thread id (and
limits) per tab in `sessionStorage` and the theme in `localStorage`.

| ID | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| B-1 | A re-tapped "Talk to a person" after a lost response never shows the card. Each tap mints a new `turn_id`; if the first request created the case but its response was lost, the second gets `already_open` (the case's `turn_id` differs). The UI's `already_open` branch draws no card, only scrolls to an existing one, so the reference card and follow-up chooser never appear. | M | UI: `core/useChat.ts:233-262`, `:286`; `core/reducer.ts:90`. Backend: `stage7/web.md:302-304`, `:311-312` | UX session | Keep the pending person `turn_id` until a 2xx arrives (the same id returns the stored first result), and on `already_open` with no handoff card in the thread, render `res.block`. |
| B-2 | SCR-1 stops polling clock and staffing (it relies on CON-3 events). Once the chat ends the stream closes, so the demo bar on SCR-1 never refreshes except on window focus. | L | `state/demoStatus.tsx:45-56`; `core/useChat.ts:107-110`, `:144-147` | UX session | Set the source back to `poll` when the chat ends or the stream is not `open`. |
| B-3 | Sign out does not clear the stored thread id, so the next login's first chat probes the old thread (a 404 that looks like a foreign-thread probe in logs) before starting a new one. | L | `state/session.tsx:80-89`; `core/useChat.ts:85-88` | UX session | `clearThread()` on sign out. |
| B-4 | After a reset, only the tab that reset re-reads the session; other open tabs keep the old role label until a 403 `role_reset`. Customer screens accept every role, so only the header label is stale. | L | `screens/scr03/useResetDemo.ts:126-131`; `components/shell/RoleGate.tsx:8` | UX session | Re-read `getSession` on a `demo_reset` chat event and on focus. |

## (c) Guards outside mock mode

Checked and consistent: every call is same-origin with `credentials: "include"` (`api/client.ts:69`,
`api/transport.ts:55`, `:95`); no code outside `src/dev/` touches `document.cookie` (`dev/session-fake.ts:1`); a 401
`UNAUTHENTICATED` from any call except `login` sends the page to `/login?return_to=…&reason=none|expired`
(`api/client.ts:91`, `state/session.tsx:36-58`), matching the server's 303 for page loads (`stage7/web.md:245-252`);
the UI's `return_to` guard (`lib/returnTo.ts:2-7`) matches the server's (`stage7/web.md:252`).

| ID | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| C-1 | Whether the login page can load at all depends on WEB-1, still open. The built `index.html` needs `/assets/index-*.js`, `/assets/*.css` and lazy chunks before anyone is signed in. Option A works as built. Option B needs a separate self-contained login page that does not exist. Option C leaves the browser redirect (already built) as the only page guard. | H | `apps/web/dist/index.html:8-9`; `docs/plans/7b-decisions/web.md:23-47`, `:58`; `docs/plans/tickets/AEA-49.md:126-129` | Innocent (WEB-1), then UX session if B | Answer WEB-1 before UX-4 sign-off; if B, the UX session builds the standalone page. |
| C-2 | The real login has never been driven. The Playwright smoke signs in with dev-only `?signedin=1&role=…`, and the mock accepts any username and password and fakes `mhc_session`. The HttpOnly cookie, the 303 gate and the expiry path are untested in a browser. | M | `apps/web/tests/e2e/smoke.spec.ts:30`; `docs/ux/04-prototype/PROTOTYPE_PLAN.md:36`, `:39`; `.claude/rules/integrated-journeys.md` §1 row "Playwright smoke" | AEA-58 (J-1, J-8) + UX session | A Playwright project that signs in through SCR-12 against a real server (no dev parameters), handed to AEA-58. |
| C-3 | A login rate limit reads as wrong credentials. `LOGIN_RATE_LIMITED` gets the same message as `LOGIN_FAILED` ("That username or password didn't work. Check the README…"); while over the limit even the right pair gets 429, so a reviewer is told the README values are wrong. `Retry-After` / `retry_after_ms` are ignored. | M | `screens/scr12/useLogin.ts:9`, `:47-51`; `screens/scr12/copy.ts:11`; `docs/plans/tickets/AEA-23.md:88`, AC-7 (`:147`) | UX session | Separate copy: "Too many tries from here. Try again in N seconds." using `details.retry_after_ms`. |
| C-4 | The login copy promises the README holds the username and password; whether it does is DAT-3, an open question for Innocent. | L | `screens/scr12/copy.ts:6`, `:10`; `stage7/web.md:519`; `docs/plans/7b-decisions/web.md:16` | Innocent (DAT-3), then UX copy | Align the copy with the DAT-3 answer. |
| C-5 | `favicon.svg` sits at the build root, outside `/assets/` and `/fonts/`: signed in it is answered with `index.html`, signed out with a 303. | L | `apps/web/dist/index.html:6`; `docs/plans/tickets/AEA-49.md:125-127` | UX session | Import the icon so Vite emits it under `/assets/` (no backend change). |
| C-6 | No route `errorElement`: a lazy screen chunk that fails to load (a redeploy changed hashes; an asset answered with HTML under WEB-1 B/C or after expiry) shows React Router's default error page. | L | `src/router.tsx:71-74`, `:76-97` | UX session | A root `errorElement` that offers reload / sign in. |

## (d) Error codes

Checked and consistent: a composed outcome is HTTP 200 and is drawn from its block (`ErrorBlock`, `NoticeBlock`), and
only 4xx/5xx become `ApiError` (`api/client.ts:81-93`); handled per operation: `startChatSession` 401 / 429 / 503,
`getChatThread` 401 / 404 (clears, starts new) / 410 (ended), `submitTurn` 401 / 404 / 409 `TURN_IN_PROGRESS` (waits
`retry_after_ms`, same `turn_id`) / 410 / 503, `requestPerson` 410 / 503 `HANDOFF_FAILED`, `resetDemo` 409 / 500
(`core/errors.ts:18-31`, `core/useChat.ts:168-179`, `screens/scr03/useResetDemo.ts:136-143`).

| ID | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| D-1 | A 400 `VALIDATION_ERROR` on a turn, person request or follow-up is shown as retryable ("That didn't send. Your message is still here.") and Try again resends the same body, which can never pass. | M | `core/errors.ts:26`, `:28`, `:30`; `core/useChat.ts:200-203`; `ui-contracts.openapi.yaml:11873-11888` | UX session | `retryable: false` for 400; show "That couldn't be sent" without Try again. |
| D-2 | The stream can answer an undocumented 410. `owned_thread` answers 410 `SESSION_ENDED` for this session's ended thread on every consumer, AEA-41 included, but the OpenAPI documents only 401 and 404 for `streamChatEvents`, so AEA-23's `assert_response_matches` ("status is documented") fails on it. The UI stops the stream silently on 404 and 410 and never tells the chat, so a chat whose stream reconnects after a reset it missed stays "open" until the next send. | M | Backend: `stage7/web.md:149-155`, `:455-457`; OpenAPI: `ui-contracts.openapi.yaml:2527-2530`. UI: `api/transport.ts:26`, `:56-59`; `core/useChat.ts:144-148` | Innocent (OpenAPI: add 410 to CON-3, or rule that AEA-41 maps an ended thread to 404) + UX session | Whatever the contract says, the transport reports a terminal `ended` status and `useChat` dispatches `ENDED`. |
| D-3 | `saveFollowUp` 409 has two causes but one message: the UI always says "There's no open request to attach this to.", while the backend also sends `details.state: "not_verified"` for an unverified `on_record` request. The UI normally sends `general` in that case, so this needs a race to reach. | L | `core/errors.ts:14`, `:29`; `cards/FollowUpChooser.tsx:113`; `stage7/web.md:326-328` (WEB-23); OpenAPI example `state: no_open_case` (`ui-contracts.openapi.yaml:2880`) | UX session | Branch on `details.state`. |
| D-4 | The RATE_LIMITED hold is a UI guess (60 s); the notice carries no retry time and the server's thread bucket is 20 a minute. | L | `core/pending.ts:14`; `core/useChat.ts:196-199`; `ui-contracts.openapi.yaml:9625-9655`; `stage7/web.md:186` | UX session (accept) | Note only; a retry time in `Notice` would be an OpenAPI change. |

## (e) Server-Sent Events (CON-3)

Checked and consistent with AEA-41 and `stage7/web.md` §11: the transport uses `fetch` (not `EventSource`), sends
`Last-Event-ID` whenever it holds an id (0 on a new chat, so the server replays from 0 as WEB-16 decides), tracks the
highest `id:`, skips heartbeat comments, de-duplicates by event id, reconnects with backoff 1, 2, 4, 5 s, and stops on
401 (sign-in) / 403 / 404 / 410 (`api/transport.ts:40-92`; `api/sse.ts:8-35`; `core/useChat.ts:127-148`;
`core/reducer.ts:100-101`). The nine event names match `ChatEvent` (`ui-contracts.openapi.yaml:10186-10208`);
`chat_closed` and `demo_reset` end the chat in the UI, which closes the stream the server closes.

| ID | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| E-1 | No idle watchdog. If a proxy drops the connection without closing it, the 15 s heartbeats stop and the client waits on `reader.read()` forever, showing a healthy chat that receives nothing. | L | `api/transport.ts:63-79`; heartbeat `stage7/web.md:398` | UX session | Reconnect when no bytes arrive for 45 s (three heartbeats). |
| E-2 | `shift_ended` replaces `settled` with the snapshot stored in the event. A replay after a reconnect can deliver it after a later turn's `settled`, so the panel regresses until the next turn. | L | `core/reducer.ts:113-115`; `ui-contracts.openapi.yaml:10118-10144` | UX session | Keep the newer `settled` (compare by the latest `actions[].at`), or re-read the thread after a replay. |
| — | Resume does not replay history by design (it starts at `last_event_id`); the history must come from `turns`. | — | Counted as A-1 | — | — |
| — | The undocumented 410 on the stream. | — | Counted as D-2 | — | — |

## (f) Production build

Checked and consistent: the API base is the page's own origin (`/api/…` relative paths from the contract index and
`api/transport.ts:21-24`), which is what AEA-49 serves; `npm run dev` proxies `/api` to a real backend on `API_PORT`
(8000) and `dev:mock` to Prism (`vite.config.ts:8`, `:12`); the dev layer loads only when `MODE === "mock"`
(`src/main.tsx:13`) and `check:dist` passed at the integrator pass (`PROTOTYPE_PLAN.md:104`).

| ID | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| F-1 | The build needs the OpenAPI and the dev dependencies. `prebuild` regenerates `types.gen.ts` and the contract index from `../../docs/ux/03-structure/ui-contracts.openapi.yaml` with `openapi-typescript` and `yaml` (devDependencies). An image stage that copies only `apps/web`, or installs with `--omit=dev`, fails. Who adds the stage is still AEA-50's open ND-50c. | M | `apps/web/package.json:10-11`, `:19`, `:22`, `:59`, `:65`; `apps/web/scripts/paths.mjs:5`; `docs/plans/tickets/AEA-50.md:124` | AEA-50 (or its follow-up) + UX session | The UX session states the exact command (`npm ci && npm run build` from `apps/web`, Node version, `docs/ux/03-structure/` in the build context, output `apps/web/dist`); AEA-50 copies it. |
| F-2 | Mock metadata ships in `dist`. The client imports the whole contract index, including every OpenAPI request example: a six-digit code `482913`, "Omar Patel", "512-555-0102". It is synthetic or issued test data, so nothing leaks, but `check-dist` does not look for it, and a scan for code-like values (AEA-59, CAP checks) would flag the bundle. | L | `api/client.ts:2`, `:40`; `src/api/contract.gen.json` (`submitTurn.requestExamples`); `dist/assets/index-CY_6x921.js` contains them; `scripts/check-dist.mjs:11` | UX session | Split a runtime index (method, path, success codes) from a dev-only examples index under `src/dev/`; add a needle to `check-dist`. |
| F-3 | A dev hook is read in production: `__mhcDevRoutes` (harmless; it only adds routes a page script sets). | L | `src/router.tsx:101`; present in `dist/assets/index-CY_6x921.js` | UX session | Read it only under `MODE === "mock"`. |
| F-4 | `dist/` is older than the sources (`dist/index.html` 07:58, `contract.gen.json` 08:13, after the integrator edits). | L | file times in `apps/web/` | UX session | Rebuild and rerun `check:dist` at sign-off. |

## (g) Journey selectors

| ID | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| G-1 | Almost no stable state hooks. Outside `src/dev/` the app has three `data-testid`s (`strip-line`, `inbox-loading`, `spend-fill`) and one `data-screen` (SCR-1). Cards carry no type, card id or answered state; notices no code; the composer lock, the pending phase (replying / still working / gave up), stream status, the ended state, the thread id and identity status exist only as copy text. J-1, J-3, J-7 and J-9 must assert those states, and the slice plan says AEA-58's selectors come from a UX contract in this folder that does not exist yet. | H | `screens/scr01/Scr01.tsx:27`; `core/components/SettledAside.tsx:29`; `screens/scr02/Scr02.tsx:36`; `screens/scr10/SpendBar.tsx`; `docs/plans/slice-plan.md:79-87`, `:91-93`, `:178` | UX session | Publish the selector contract (minimum list below) and add the attributes. |
| G-2 | The smoke test identifies screens by `[data-screen]` or the page title; only SCR-1 has the attribute. | M | `apps/web/tests/e2e/smoke.spec.ts:30-34` | UX session | `data-screen="SCR-n"` on all twelve screens. |
| G-3 | The Playwright runners differ. AEA-58 is pytest-playwright; the UX suite is `@playwright/test` whose config always starts Prism and Vite. "Its Playwright configuration to reuse" cannot be reused as written. | M | `docs/plans/slice-plan.md:91-93`, `:178`; `apps/web/playwright.config.ts:9-13` | AEA-58 + UX session | Agree the runner. If UX's is reused, add a `real` project: base URL from the environment, no `webServer`, sign-in through SCR-12. |
| G-4 | Entry ids embed turn UUIDs (`data-entry="c:<uuid>"`, `"<uuid>:reply"`). Usable for "this turn's reply", not as fixed selectors. | L | `core/components/Thread.tsx:44`; `core/replyGroups.ts:55-57` | UX session | Keep; document the pattern in the selector contract. |

## Count

| Class | H | M | L |
|---|---|---|---|
| (a) fields | 1 | 4 | 3 |
| (b) state | 0 | 1 | 3 |
| (c) guards | 1 | 2 | 3 |
| (d) error codes | 0 | 2 | 2 |
| (e) SSE | 0 | 0 | 2 |
| (f) build | 0 | 1 | 3 |
| (g) selectors | 1 | 2 | 1 |
| **Total (33)** | **3** | **12** | **17** |

## What the UX session must provide for the customer journeys, and by when

The order the tracks join (slice plan §0a): **UX-4 signed → AEA-49 serves `dist` → AEA-58 runs the browser journeys →
UX-5 reruns its suite against the real backend → AEA-55.** AEA-49 and AEA-58 both carry `gate::ux4`, so everything a
journey needs from the frontend is due at UX-4 sign-off.

### Before UX-4 sign-off (AEA-49 and AEA-58 cannot start without these)

1. **WEB-1 answered and applied (C-1).** Innocent picks A, B or C. If B, the UX session ships the self-contained `/login`
   page as part of UX-4.
2. **A production build recipe (F-1, F-4).** One command, its Node version, its inputs (`apps/web` plus
   `docs/ux/03-structure/ui-contracts.openapi.yaml`), its output (`apps/web/dist`), a fresh `dist`, `check:dist` green,
   and `check:dist` extended to the example index (F-2). Favicon under `/assets/` (C-5).
3. **The selector contract, `docs/plans/ux-join/selectors.md` (G-1, G-2, G-4).** The minimum the customer journeys need:
   - every screen: `data-screen="SCR-n"`;
   - SCR-1 root: `data-thread-id`, `data-chat-state` (`starting` | `ready` | `start-failed` | `ended-closed` |
     `ended-reset` | `ended-gone`), `data-stream` (`connecting` | `open` | `reconnecting` | `closed`), `data-pending`
     (`hidden` | `replying` | `still` | `gave-up`);
   - composer: `data-lock` (`none` | `rate` | `spend` | `ended` | `starting`);
   - each reply block wrapper: `data-block-type`, `data-card-id`, `data-answered`; notices `data-notice-code`; error
     cards `data-error-code`;
   - customer rows `data-delivery` (`pending` | `sent` | `failed`); event lines `data-event-type`;
   - "What's settled": the existing `data-block` plus `data-identity-status`, `data-visit-status`, `data-request-ref`;
   - SCR-12: `data-login-message` (`refused` | `rate-limited` | `unreachable` | `expired`);
   - SCR-2: `data-inbox-id`, `data-inbox-status` per message; SCR-3: `data-reset-result`, the staffing switch's checked
     state.
4. **The UX-owned fixes a customer journey would hit:** A-4 (J-9 Try again), A-5 (J-3 panel), B-1 (J-7 person card),
   C-3 (J-1 / J-8 login), D-1 (J-9), the UI half of D-2 (J-1 resume after reset), E-1. A-3 needs its owner chosen first
   (recommended AEA-40).
5. **A real-backend mode for tests (C-2, G-3).** A Playwright project or recipe that signs in through SCR-12 with the
   demo login from the environment, no `?signedin` / `?role` / `?scenario`, and a base URL from the environment; the
   runner choice agreed with AEA-58.
6. **Fixtures for AEA-59.** The dev scenarios and contract index stay where they are; the UX session names which files
   are the fixtures AEA-59 validates (read-only), including the dev-only event fixtures in `src/dev/stream/events.ts`.

### Before AEA-58 starts (wave 3)

- Selectors frozen: a selector rename after this point is a change to AEA-58's journeys and is announced in this folder.
- The backend rows these journeys depend on have landed in the rewrites: A-1 and A-2 (AEA-40, AEA-42), A-6
  (AEA-27 / AEA-43), D-2's contract answer (Innocent), F-1's build stage (AEA-50).

### Before UX-5 sign-off

- Copy decisions that follow open answers: C-4 (DAT-3), A-7 (history wording, agreed with AEA-40).
- The UX-5 suite's real-backend rerun plan for AEA-55 (Prism proxy mode), using the same selector contract.

### Before AEA-55

- The UX-5 suite runs against AEA-58's server on the production build; any selector or state the suite asserts that
  AEA-58 does not is added to the contract first.

## Decisions this audit raises (not answered here)

1. **WEB-1** (Innocent): which files load before the demo login (C-1).
2. **CON-3 410** (Innocent, OpenAPI change): document 410 on `streamChatEvents`, or have AEA-41 answer an ended thread
   with 404 (D-2).
3. **Owner of `answered` after reload** (engineering, AEA-40 rewrite or UX session): A-3.
4. **DAT-3** (Innocent, already logged): whether the README carries the login values (C-4).
