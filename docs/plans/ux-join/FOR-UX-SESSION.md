# For the UX session: what the backend needs from `apps/web`, and when

**From:** the backend (Stage 7/8) track. **Date:** 2026-10-21. **You don't need anything else to act on this note.** The long
version, with every finding and its evidence, is in this folder: [`README.md`](README.md) (the join plan) and the three audits.

## 1. What the backend will do with your frontend

The backend is a FastAPI app in `src/meridian/`, built ticket by ticket (AEA-01…AEA-62). Four tickets touch your work:

- **AEA-49 (wave 2)** serves your production build, `apps/web/dist`, from the same origin as the API. Unknown page paths get
  `index.html`; files come from `/assets/` (and `/fonts/`). Signed out, a page load gets `303` to
  `/login?return_to=<path>&reason=none|expired` and an `/api` call gets `401 UNAUTHENTICATED`.
- **AEA-58 (wave 3)** builds `dist` with your recipe, starts the real server on a throwaway copy of the database, opens system
  Chrome, and signs in **through SCR-12 with the real demo login**. No `?signedin`, `?role` or `?scenario`. It walks J-1 (sign in,
  start a chat, one turn, reload, the same thread comes back) and the rate-limited login. It reads elements only through
  your selector contract.
- **AEA-62 (wave 4)** does the same for J-2 (answers with a source), J-3 (booking, then a follow-up), J-6 (escalation → queue
  → case view with its brief) and J-8 (role switch, reset from another tab, refresh).
- **AEA-55 (wave 5)** reruns **your UX-5 suite** against the real backend through Prism in proxy mode. It may change run
  configuration only, never your screens or specs. Anything it finds goes back to you.

The models in these runs are scripted (no paid calls). What is real: the server, the login, the cookie, the guards, the database
writes. That is the point: until now every UX test signed in with dev-only parameters, so none of them has met the real login.

## 2. What we need, and by when

| By | You provide | Why it is due then |
|---|---|---|
| **Before UX-4 sign-off** (AEA-49 and AEA-58 are gated on it; UX-4 is on the build's critical path from wave 3) | 1. The selector contract `docs/plans/ux-join/selectors.md` (§3) and the attributes built. 2. The build recipe written down and green (§4). 3. Your high fixes (§7). 4. The P1 fixes in the join plan's table (b): CU A-4, A-5, B-1, D-1, E-1, C-5/SH C2 favicon, C-6/SH D1 error boundary, F-2/F-3/F-4, ST B3, ST B6/SH C3, SH F3, F4. 5. A first real-backend run of J-1 by hand (§5). 6. The fixture dump script (§6) | Whatever is in `dist` at sign-off is what AEA-58 tests |
| **Before AEA-58 starts (wave 3)** | Selectors frozen. After this, a rename or removal is announced in this folder first (a one-line note in `selectors.md`'s change log), because it breaks a backend test | AEA-58 copies them into one module |
| **Before AEA-62 (wave 4)** | ST C3: J-6, J-7, J-8 reachable as product-driven steps (no dev forcing); for each SCREEN_SPECS state a journey asserts, `selectors.md` says how the real backend reaches it (a seed, an action, or "mock only"). Read-page fixes SH A2, A3, A4, B2, B3 | AEA-62 walks those screens |
| **Before UX-5 sign-off** | The UX-5 suite in two modes (§5); every remaining row of table (b) marked P6; report notes: SCR-11's mix sum is an allowed display sum (SH A6), the `[contract drift]` signal exists only in mock mode (SH G5) | AEA-55 reruns that suite |

## 3. The selector contract (minimum)

Publish it as `docs/plans/ux-join/selectors.md`. Keep it **runner-neutral**: ARIA roles with accessible names, and `data-*`
attributes. AEA-58 and AEA-62 are Python (pytest-playwright); AEA-55 runs your TypeScript suite; only the selectors and the
written sign-in steps carry over. Never key a selector on copy that UX-5 might reword. "Add" means it does not exist today
(outside `src/dev/` the app has 3 `data-testid`s and one `data-screen`).

| Journey step | Required hook | Today |
|---|---|---|
| Every journey: which screen is up | `[data-screen="SCR-n"]` on each of the twelve screen roots | SCR-1 only; add 11 |
| J-1 sign in | Username and password inputs by label; `role=button[name="Sign in"]` | present (list the exact names) |
| J-1, J-9 login refused / throttled / expired | `[data-login-message=refused\|rate-limited\|unreachable\|expired]` | add |
| J-1 chat state | SCR-1 root: `[data-thread-id]`, `[data-chat-state=starting\|ready\|start-failed\|ended-closed\|ended-reset\|ended-gone]`, `[data-stream=connecting\|open\|reconnecting\|closed]`, `[data-pending=hidden\|replying\|still\|gave-up]` | add |
| J-1 thread after reload | Each entry: `[data-entry]` (the existing `c:<turn_id>` / `<turn_id>:reply` pattern, documented) plus `[data-speaker=customer\|assistant\|representative\|event]`; the greeting is the first entry | entry present; speaker add |
| J-1, J-9 composer | `role=textbox` + `role=button[name="Send"]`; `[data-lock=none\|rate\|spend\|ended\|starting]` | lock add |
| J-1 customer row sent | `[data-delivery=pending\|sent\|failed]` | add |
| J-2 … J-5 reply blocks | Each block wrapper: `[data-block-type]`, `[data-card-id]`, `[data-answered=true\|false]`; a cited source names its document (a hook you choose, e.g. `[data-source-ref]`) | add |
| J-9 notices and errors | `[data-notice-code]` (BUSY, TURN_TIMEOUT, RATE_LIMITED, SPEND_CAP_REACHED); `[data-error-code]` on error cards | add |
| J-7 event lines | `[data-event-type]` (joined, paused, resumed, closed, staffing, shift_ended) | add |
| J-3 "What's settled" | The existing `data-block` plus `[data-identity-status]`, `[data-visit-status]`, `[data-request-ref]` | partly present |
| J-3 SCR-2 inbox | Per message `[data-inbox-id]`, `[data-inbox-status=active\|used\|expired]`; the code readable as text | add |
| J-7, J-8 SCR-3 demo controls | `[data-reset-result]`; the staffing switch as `role=switch` with `aria-checked` | add |
| J-8 acting role | `role=radiogroup[name="Acting as"]` → checked radio | present (`components/shell/RoleSwitch.tsx`) |
| J-8 role refused or reset | `[data-testid=role-panel][data-reason=wrong_role\|role_reset\|customer]` | add |
| J-6 queue row | `role=button` (or link) named `P<n> <word>, MHC-C-xxxx`; live row `role=button[name="Claim and join MHC-C-xxxx"]` (representative only) | present |
| J-6 queue empty / staffing | `[data-testid=queue-empty]`; `[data-testid=live-queue][data-staffing=nobody_online\|simulated_on_shift]` | add |
| J-6 case loaded | `[data-testid=case][data-lifecycle=…][data-version=n]`; owner `[data-testid=case-owner]` | add (the lifecycle `ol` is present) |
| J-6 brief | `#brief-1` … `#brief-8`; `[data-testid=brief][data-status=ready\|being_written\|failed]` | headings present; status add |
| J-6 promise and sources | `[data-promise-status=open\|kept\|missed\|changed]`; `#src-<source_id>` with `[data-changed-since]`, `[data-current-unavailable]` | add attributes |
| J-7 conversation and live box | `#msg-<message_id>[data-speaker=…]`; `[data-testid=live-box][data-mode=active\|disabled\|ended-by-reset][data-controller=ai\|human]` | id present; rest add |
| J-6, J-7 action result and conflict | `#case-result`, `#queue-result`; `[data-testid=action-error][data-code=…]` with `role=button[name="Reload"]`; `[data-testid=case-stale]` | results present; rest add |
| J-6 oversight, flags | `[data-lane=p0_p1\|overdue\|due_soon\|unowned\|stuck_waiting]`; `#demo-controls-result`; `[data-flag-id][data-status=new\|reviewed]` | lanes and flags add |
| J-10 read pages | Each region `[data-state=loading\|empty\|error\|stale\|partial]`; each number `[data-measure=<response path, e.g. health[2]>][data-field=value\|numerator\|denominator]` | add (`spend-fill` only) |

## 4. The build recipe (write it in `apps/web/README.md` too)

```sh
cd apps/web
npm ci                 # dev dependencies are needed: prebuild runs openapi-typescript and yaml; tsc -b checks tests/
npm run build          # prebuild regenerates src/api/types.gen.ts and contract.gen.json from
                       #   ../../docs/ux/03-structure/ui-contracts.openapi.yaml, then tsc -b && vite build → dist/
npm run check:dist
```

- **Output:** `apps/web/dist` (`index.html`, `assets/`, `fonts/`). Always the production mode; never `--mode mock` for `dist`.
- **Node:** add `engines.node` to `package.json` (the VPS runs v24.21.0). The deploy image pins to it.
- **Outside input:** the build reads the signed OpenAPI at `../../docs/ux/03-structure/ui-contracts.openapi.yaml`. The deploy image
  (AEA-50) will copy that one file to the same relative path, so you need not change this. If you add a `build:dist` that skips
  regeneration (`check:gen`, then `vite build`), say so here and AEA-50 can use it.
- **Asked of you:** `postbuild` runs `check:dist`; `check:dist` also fails when any `src/dev/` module is in the build manifest
  and when `requestExamples` is in the bundle; the favicon is imported so it lands under `/assets/` (a root file is answered
  with `index.html` or a 303); the router has a root `errorElement`.

## 5. Real-backend mode

- **Same origin, relative paths, cookie included.** You already call `/api/...` with `credentials: "include"`. Keep it.
- **The cookie** is `mhc_session`: HttpOnly, SameSite=Lax, Secure only when deployed. JavaScript never sees it. Local servers run
  with `MERIDIAN_COOKIE_SECURE=false`, or the browser drops it over plain http.
- **Two ways to point at the real server.** For your own iteration, `npm run dev` already proxies `/api` to
  `127.0.0.1:${API_PORT:-8000}`. For the tests that matter, extend your `E2E_TARGET`: `mock` (today), `real` (today: the Vite
  dev proxy) and **`served`** (new: no web server started; `E2E_BASE_URL` is the backend serving `dist`, which is what AEA-58
  and AEA-55 test). No literal ports in assertions; paths relative to `baseURL`.
- **Sign-in in real modes:** type `MERIDIAN_DEMO_USERNAME` and `MERIDIAN_DEMO_PASSWORD` from the environment into SCR-12;
  switch roles with the role switch; staffing with SCR-3. Never `?signedin`, `?role`, `?scenario`, `?staffing`, `?ex` or
  `?delay`. Tag the tests that need dev forcing `@mock-only`; AEA-55 records them as not run.
- **Write the sign-in steps down** in `selectors.md`, not only in code, because the Python suites re-implement them.
- **Screenshots:** `SHOTS_DIR` from the environment; write under `docs/ux/` only in mock mode.
- **Ports 4019 (Prism) and 5184 (Vite) are yours.** The backend never binds them.
- **Streams.** Chat events: `/api/chat/sessions/{id}/events`; case events: `/api/staff/cases/{ref}/events`. Heartbeat comment every
  15 s; replay from `Last-Event-ID`; the server closes the chat stream after `chat_closed` or `demo_reset`. For an ended thread
  the stream answers **404** if Innocent keeps the contract (Decision 4; today the OpenAPI documents only 401 and 404 there): treat
  404 or 410 on a stream as terminal and re-read the thread, which answers 410 `SESSION_ENDED`. Keep the two stream paths
  separately configurable in `vite.config.ts`, so AEA-55 can route them around Prism if Prism buffers them.

## 6. Fixture rules

AEA-59 checks the OpenAPI's own examples plus a generated set of variants. It cannot read your TypeScript dev fixtures, so:

1. **Dump them.** A script (like `tests/e2e/list-scenarios.ts`) that writes every dev fixture, every `OpForce.transform` output
   and every scripted stream event as JSON, one record per `{operationId, status, name, body}`, to a git-ignored path such as
   `apps/web/tests/e2e/.gen/fixtures.json`. Name the command and the path in `selectors.md`. AEA-59 validates it read-only.
2. **Every body validates** against the schema for its operation and status. The OpenAPI never sets `additionalProperties: false`,
   so an extra key passes silently: **never add a key the schema lacks.**
3. **Omitted optionals:** leave the key out. Don't send `null` for a field that is not nullable.
4. **Nulls:** every nullable field a screen reads has a fixture where it is `null`, and the screen shows it honestly ("—" plus
   `null_reason`, never "0").
5. **Empty lists:** every list a screen shows has an empty fixture (queue, inbox, flags, alerts, lanes).
6. **Error bodies:** `ApiError` `{error: {code, field, constraint, details}, request_id}`, with a code from the enum and only the
   statuses the operation documents. `ROLE_NOT_ALLOWED` always carries `details.role`, `needs` and `reason`.
7. **Behave like the backend** where a journey depends on it: one role per login, shared by every tab (`localStorage`, not
   `sessionStorage`); `role_reset` on every staff call until a role switch; per-action roles (only the supervisor may `assign`
   or `change_priority`); `allowed_actions` as §8 says; live actions never change the case version; `getChatThread` returns the
   greeting, staff messages and event lines; an inbox message whose code the server no longer holds is `expired`.
8. **Synthetic values only**, and none of them in `dist` (the contract index's request examples, a six-digit code, a phone
   number, currently ship in the bundle: CU F-2).

## 7. Your high findings (fix before UX-4 sign-off unless marked)

Paths are under `apps/web/`.

| Id | What breaks | Where |
|---|---|---|
| CU G-1 / ST G1 / SH G4 | No stable hooks; every journey would key on copy | `src/screens/scr01/Scr01.tsx:27`; `src/screens/scr01/core/components/SettledAside.tsx:29`; `src/screens/scr02/Scr02.tsx:36`; `src/screens/scr10/SpendBar.tsx` (the only hooks) |
| ST B1 / SH B1 | The role is read once; another tab's switch or a reset is never noticed, and writes fail naming the wrong role | `src/state/session.tsx:45-56`, `:62-78`; `src/screens/scr03/useResetDemo.ts:31-33`; `src/api/client.ts:91` |
| ST B2 | A 403 on the queue is invisible (the old queue stays up); SCR-6 says "didn't load"; the reset panel never shows there | `src/screens/scr05/useQueueFeed.ts:17-24`; `src/screens/scr05/Scr05.tsx:71-72`; `src/screens/scr06/Scr06.tsx:112-113`; `src/components/shell/RoleGate.tsx:20-25`; `src/screens/reads/ReadError.tsx:9-10`; `src/screens/scr06/errorCopy.ts:45` |
| ST C1 | The supervisor gets "Claim and join": the claim succeeds, the join answers 403, and a waiting chat is owned by someone who cannot join | `src/screens/scr05/QueueSections.tsx:26`; `src/screens/scr05/LiveRow.tsx:47-49`; `src/screens/scr06/claimAndJoin.ts:20-26` |
| ST C2 | The reply box is active for the supervisor on a joined case; Send, Hand back and Close each answer 403 | `src/screens/scr06/actionPlan.ts:25-29`; `src/screens/scr06/LiveBox.tsx:19-23`; `src/screens/scr06/Scr06.tsx:158-161` |
| SH S3 | Nothing validates your dev fixtures against the OpenAPI | `docs/ux/04-prototype/PROTOTYPE_PLAN.md:79`, `:105`; §6 above. Due before AEA-59 is planned (wave 2) |
| SH G1 (due UX-5) | Every e2e test enters through mock-only parameters, so all are `mock-tested` | `tests/e2e/smoke.spec.ts:30,45,50`; `tests/e2e/sweep.spec.ts:64-70,118,128,134,144,155-158` |

Your own `docs/ux/04-prototype/INTEGRATION_HANDOFF.md` §3 (G-01…G-16) overlaps: ST B2 extends your G-06, ST E3 is G-13, ST C3 is
G-02 and G-03.

## 8. Backend changes you can build against now

These are being added to the backend tickets ([`backend-amendments.md`](backend-amendments.md)); build to them, not to the
examples where they differ.

- **`getChatThread` returns the whole history** in time order: the greeting, every customer message, every reply, every
  representative message, every event line, and the shift-end card. Non-turn entries get stable ids (`msg:<id>`, `evt:<id>`).
  A "Talk to a person" press appears as a customer turn plus its handoff card. Card blocks come back with `answered` set
  (if this lands; otherwise treat every `live: false` card as answered except the newest unanswered one, CU A-3's fallback).
  History rows for codes, forms and choices use the live texts ("Code entered", "Details sent", the option's label).
- **`allowed_actions`** follows one rule: an action is listed if and only if the server would accept it from this role now. The
  owner always gets `[]`. The supervisor never gets `claim_and_join`, `join_chat`, `send_live_message`, `hand_back`,
  `close_chat`, `log_call` or `log_email`. `claim_and_join` only for the representative on a live-queued case while staff are on
  shift. `QueueRow` has no `allowed_actions`, so on SCR-5 decide by role (ST C1).
- **Live actions (join, send, hand back, close) never change the case `version` or lifecycle** and append no `case_changed`. So
  no reload is needed after them, and a later Resolve with the earlier version succeeds.
- **On staff screens the customer speaker's `display_name` is `null`**: show the kind label ("Customer"), never "You".
- **Read pages:** `unit` is one of `count`, `ms`, `share`; `share` is a 0–1 fraction. An `id` can repeat (M-27 per reason), but
  (`id`, `label`) pairs are unique, so key rows by both. AEA-53 will list its health tiles (labels, units, order) in a note in this
  folder; key SCR-10's empty state on the volume tile.
- **The inbox** marks a message `expired` whenever the server no longer holds its code (after a restart); enable Copy only for
  six digits.

## 9. Questions with Innocent that change your copy or contract

See [`decisions-for-innocent.md`](decisions-for-innocent.md). Don't change these until he answers:

1. **WEB-1**: which files load before sign-in. If he picks **B**, you build a self-contained login page (styles and script
   inlined) that matches SCR-12, as part of UX-4.
2. **`CaseDetail.events.last_event_id`**: if he adds it, connect the case stream with it as `Last-Event-ID`. If not, ignore
   replayed `chat_closed` / `controller_changed` events with `at <= detail.as_of` (ST B5's interim fix).
3. **The login throttle message**: SCREEN_SPECS N-28 says the throttle answers with the same sentence as a wrong password;
   UI_CONTRACTS CON-22 says "Too many attempts. Wait a moment and try again." Your code follows N-28 today (CU C-3).
4. **A chat after signing in again**: SCREEN_SPECS SCR-1 (session-ended row) says "the chat resumes if it is still open"; the
   backend gives every new login a new session, and an earlier session's thread answers 404, so today the app starts a new chat.
5. **DAT-3**: whether the README carries the login values; SCR-12's copy promises it does (CU C-4).

## 10. Please don't

- **Edit `docs/ux/03-structure/ui-contracts.openapi.yaml` or `UI_CONTRACTS.md`.** They are signed (UX-3). A change reopens UX-3,
  breaks the generated types both sides pin, and goes to Innocent. The same holds for the SCREEN_SPECS lines in §9 until he answers.
- **Add mock-only code that reaches `dist`.** Nothing outside `src/dev/` imports `src/dev/`, a `*.fixtures.ts` file or a test
  folder; dev hooks (`__mhcDevRoutes`) are read only under `import.meta.env.MODE === "mock"`; the request-examples index moves to
  `src/dev/`.
- **Rename or remove a selector after AEA-58 starts** without a line in `selectors.md`'s change log first.
- **Edit backend files** (`src/`, `tests/`, the tickets, the slice plan). Ask in this folder; a note here is read before each wave.
- **Commit or push** without Innocent's yes (project rule). He is being asked to commit the tree now (Decision 3).


## Decided by Innocent, 2026-10-21 (all recommendations taken)

- **WEB-1: option A.** Public-before-login files stay as the app is built (no separate login page).
- **Add `CaseDetail.events.last_event_id` to `ui-contracts.openapi.yaml`:** yes. **This is yours to do** in `docs/ux/**` (the backend session does not edit that file); tell the backend session when it lands. AEA-29, AEA-45 and the staff reads use it afterwards.
- **No 410** on `streamChatEvents`. **Login throttle:** a separate message line. **After signing in again:** SCR-1 starts a fresh chat (one new `startChatSession`); the earlier thread is not resumed.
