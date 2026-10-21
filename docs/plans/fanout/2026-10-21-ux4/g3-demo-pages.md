# UX-4 prototype · slice G3 (demo pages: SCR-2 inbox, SCR-3 guide and controls, SCR-4 `/role`, SCR-12 login)

> **Planner:** `fanout-planner` · **Date:** 2026-10-21 · **Project:** `/home/linuxuser/workspaces/inno-aea-callcenter` · **Implementer:** `fanout-implementer` (Sonnet) · **Readiness:** READY (see section 9)
> **Lane / loop:** `lane::build-loop`, not `risk::security` (the demo login is a fake on a mock; the real gate is a later backend slice). Loop: plan, implement (code **and** its tests), affected tests, code review. No test-writer, no frozen tests, no security agent. **No worked pair (WP-N):** this slice changes no model behaviour.
> **Runs after** the foundation slice (`docs/plans/fanout/2026-10-21-ux4/foundation.md`, cited below as **F§n**). It plans against the foundation's *defined* interfaces; some of those files were still being written when this plan was made (see Step 0).
> **No git here:** do not run `git init`, commit or push (Innocent has not asked).

## 1. Goal and sources

Replace the four foundation stubs `src/screens/scr02`, `scr03`, `scr04`, `scr12` (each is `index.ts` + `ScrNN.tsx`, F§2.1) with the real screens, add the scenarios and reactions that let the state switcher force every spec'd state of those four screens, and write the group note.

| Source | Sections used |
|---|---|
| `docs/ux/03-structure/SCREEN_SPECS.md` | SCR-2 (line 170), SCR-3 (202), SCR-4 (237), SCR-12 (549); "Copy rules that apply on every screen" (19); State matrix (602); Contract needs N-11, N-12, N-14, N-15, N-28, N-29, N-30 (642-662); note 10 "R-48 side effects" (676) |
| `docs/ux/03-structure/IA.md` | rules table ("login gates every screen", "role switch always visible"), per-screen tables SCR-2, SCR-3, SCR-4, SCR-12, "Cross-screen links" |
| `docs/ux/03-structure/UI_CONTRACTS.md` | CON-6, CON-7, CON-9, CON-10, CON-22; "Named errors" table; "Settled at section 6"; "Closed by R-48" |
| `docs/ux/03-structure/ui-contracts.openapi.yaml` | operations `listDemoInbox`, `getStaffing`, `setStaffing`, `getDemoClock`, `resetDemo`, `login`, `logout`, `getSession`, `listDemoRoles`, `switchRole`; components `InboxMessage`, `Staffing`, `StaffingResponse`, `ResetResponse`, `RolesResponse`, `SessionInfo`, `LoginResponse`; named responses `Unauthenticated`, `LoginFailed`, `LoginRateLimited`, `ResetInProgress`, `TooManyRequests` |
| `docs/design/design.md` | 3.5 (labels and hints), 8.2 (buttons, fields, tags, focus), 8.4 (generic card), 8.7 (demo bar), 8.11 (demo inbox message, role buttons), 10 (copy tone), 11 (do/don't) |
| `docs/artifacts/2026-10-21-direction-A5-service-desk.html` | looked at: it only has a dialog stub of the inbox (lines 662-665); the four demo pages have no reference screen. `design.md` wins. |
| Foundation F§4.4-4.9 | `callOp`/`useOp`/`useAction`, `ApiError`, `useSession`, `useDemoStatus`, shared components, `Scenario`/`Reaction` types, `SCREENS`, `HOME_BY_ROLE`, `safeReturnTo` |

## 2. Boundary

All paths relative to `/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/` unless they start with `docs/`.

### 2.1 Owned files (create or modify; nothing else)

```
src/screens/scr02/   index.ts (modify)  Scr02.tsx (modify)  useInbox.ts  InboxMessageCard.tsx  InboxList.tsx  useCopyCode.ts  copy.ts  Scr02.test.tsx
src/screens/scr03/   index.ts (modify)  Scr03.tsx (modify)  RealVsSimulated.tsx  StaffingControl.tsx  useStaffingControl.ts  Switch.tsx  TwoRoles.tsx  DemoLinks.tsx  ResetControl.tsx  useResetDemo.ts  copy.ts  Scr03.test.tsx  Switch.test.tsx  copy.test.ts
src/screens/scr04/   index.ts (modify)  Scr04.tsx (modify)  RoleChoices.tsx  copy.ts  Scr04.test.tsx
src/screens/scr12/   index.ts (modify)  Scr12.tsx (modify)  LoginForm.tsx  AlreadySignedIn.tsx  useLogin.ts  destination.ts  copy.ts  Scr12.test.tsx  destination.test.ts
src/dev/scenarios/scr02.ts  scr03.ts  scr04.ts  scr12.ts     (modify: replace the stub body, keep the export name)
src/dev/reactions/scr02.ts  scr03.ts                           (modify)
src/dev/reactions/g3.test.ts                                   (create; tests the two reaction files)
docs/ux/04-prototype/groups/g3-demo-pages.md                   (create)
```
`index.ts` stays exactly `export { default } from "./ScrNN";` (do not change it; list it only because it exists). Keep every file under about 150 lines; split before that.

`src/dev/reactions/scr04.ts` and `scr12.ts` (G3's by F§2.4) need **no** content: shared reactions already cover `switchRole` and `login` (F§Step 8). Leave the stubs untouched. G3 owns **no** files in `src/dev/directors/` or `src/dev/stream/` (F§2.4 gives it none; the caller's mention of them is answered: nothing to write there).

### 2.2 Read-only shared surfaces (never edit)

`docs/ux/03-structure/*` (including the OpenAPI file), `docs/design/design.md`, `docs/artifacts/**`, `.claude/**`, `CLAUDE.md`, everything the foundation owns: `src/components/**`, `src/api/**`, `src/state/**`, `src/styles/**`, `src/lib/**`, `src/routes.ts`, `src/router.tsx`, `src/main.tsx`, `src/test/**`, `src/screens/ScreenStub.tsx`, `src/dev/**` except the files in 2.1, `tests/e2e/**`, `scripts/**`, `package.json` and lock files, `eslint.config.js`. Other groups' folders: `src/screens/scr01/**`, `scr05`-`scr11`, `reads/**`.

### 2.3 Do not

- Do not edit a foundation file, even for a one-line fix. Write the request in `groups/g3-demo-pages.md` (F§8.3) and in your report.
- Do not call `fetch`, read or write `document.cookie`, import anything from `@/dev/**` into a screen, or write the strings `Prefer` / `mhc_session=` outside `src/dev/**` and test files (ESLint and `src/styles/guard.test.ts` fail the build).
- Do not use red, amber, orange or a hex literal anywhere; do not use `text-transform: uppercase` on a time or date; no 24-hour times; no spinner or shimmer.
- Do not add the field `signedIn` to a `Scenario` object: the frozen type has no such field (F§4.9). Describe the needed world in `notes` (see 4.4).
- Do not invent data a contract does not carry. Copy that this plan lists as a *gap* is the only copy that is not verbatim from a spec.
- Do not install dependencies. Do not run `git`.

## 3. Requirements table

**How verified** names a test file (all in section 7) or a scenario id (section 4.4, how it is reached). "Unit" tests use `renderWithProviders` with a fake transport (F§Step 6); "scenario" means the state switcher in `npm run dev:mock`.

### 3.1 SCR-2 Demo delivery inbox (`/demo/inbox`)

| ID | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| G3-2-01 | R1: header "Demo delivery inbox · Simulated messages"; sentence "Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification."; shared role switch and Sign out (SCR-2 R1; CON-10, CON-22) | `DemoPageHeader title="Demo delivery inbox" showDemoBar` (role switch and sign out come from it). In `Main`: `h1` "Simulated messages" (a11y note: one `h1`), then the sentence as `<p>` | `Scr02.test.tsx` "header" |
| G3-2-02 | R2: newest first; each "To ···02 · Fri 2:07 pm", body, status Active (expires 2:17 pm) / Used / Expired, "Copy code" (CON-6; N-11) | `<ol>` of `InboxMessageCard`; sort a copy by `at` descending (defensive; the API already sends newest first). Card header = `To {to_masked} · ` + `<Time iso={at} format="staff"/>`; body paragraph = `body`; code in `<b>` (`t-code` class); `Tag` with the status word; active adds muted "Expires " + `<Time iso={expires_at} format="point"/>` | `Scr02.test.tsx` "default" |
| G3-2-03 | a11y: code read digit by digit "4 8 2 9 1 3" | `<b><span aria-hidden="true">{code}</span><VisuallyHidden>{code.split("").join(" ")}</VisuallyHidden></b>` (a visually hidden text instead of `aria-label` on `<b>`, which has no role and is ignored by readers; same effect, one deviation, recorded in the group note) | `Scr02.test.tsx` "code is read digit by digit" |
| G3-2-04 | R3 foot: "This inbox carries codes only. Follow-ups are recorded on the case, never sent." and "Back to the chat" | static `<footer>`; the link behaviour in G3-2-12 | `Scr02.test.tsx` "foot" |
| G3-2-05 | default: header and the newest message with its code | `status === "success"` and `messages.length > 0` | scenario `scr02.default`; unit "default" |
| G3-2-06 | empty: "No codes yet. When the chat sends a code, it appears here. Ask the chat about your bill or book a visit to get one." + "Back to the chat" (reset FLOW-12 also lands here) | `EmptyState title="No codes yet." body="When the chat sends a code, it appears here. Ask the chat about your bill or book a visit to get one." action={<BackToChat/>}` | scenario `scr02.empty`, `scr02.empty-after-reset`; unit "empty" |
| G3-2-07 | loading: header renders; one message-shaped skeleton for up to 1 s | while `data === undefined && status === "loading"`: wrapper `<div data-testid="inbox-loading" aria-busy="true">` with one `<Skeleton height={132}/>` (final card height, no shimmer) | scenario `scr02.loading`; unit "loading" |
| G3-2-08 | partial: n/a (matrix) | nothing built; no scenario | `scenarios.integrity` n/a cell |
| G3-2-09 | error: "The inbox didn't load. Try again." with retry; header stays (CON-6 errors: RESET_IN_PROGRESS 503, REQUEST_RATE_LIMITED 429) | `data === undefined && status === "error"`: `ErrorLine message="The inbox didn't load. Try again." onRetry={refetch}`. Any error code gives the same line. If `data` exists, a failed refresh is ignored (the last list stays) | scenarios `scr02.error`, `scr02.error-rate-limited`, `scr02.error-network`; unit "error then retry" |
| G3-2-10 | stale: refresh every 5 s while visible and on focus; expired code shows "Expired", copy disabled; a new code is announced "New code received" | `useOp("listDemoInbox", {}, { pollMs: 5000, pauseWhenHidden: true, refetchOnFocus: true })`. Status is **trusted from the server** (see Risks R2: do not derive expiry from the clock). `useInbox` keeps a `Set` of ids seen; on a refresh where an id not in the set appears, and it is not the first load, call `useAnnounce()("New code received")` | scenarios `scr02.stale-new-code`, `scr02.stale-used-and-expired`, `scr02.stale-expires-on-refresh`; unit "new code announced", "polls every 5 s" |
| G3-2-11 | success: "Copied" next to the button for 2 s | `useCopyCode(code)`: `navigator.clipboard.writeText`; on success set `copiedId` for 2000 ms (`setTimeout`, cleared on unmount) and show `<span aria-live="polite">Copied</span>`; on rejection show "Copy didn't work. Select the code and copy it." for 2 s (gap, section 8.4) | scenario `scr02.success-copied`; unit "copy" |
| G3-2-12 | disabled: "Copy code" disabled on Used and Expired with the status word as the reason | `disabled={status !== "active"}`, `aria-describedby` = id of the status Tag | scenario `scr02.disabled-used-expired`; unit "used and expired" |
| G3-2-13 | interaction: Back to the chat switches to the opener tab when possible, else opens `/` | `BackToChat` renders `<Link to="/">`; `onClick`: if `window.opener && !window.opener.closed` then `e.preventDefault(); try { window.opener.focus(); } catch {}` else let the link navigate. Note `rel="noopener"` links (G2) leave `window.opener` null, so the fallback `/` is the normal path | `Scr02.test.tsx` "back to the chat" (two cases) |
| G3-2-14 | role switch changes role and the page stays; sign out goes to SCR-12 (IA table; F§4.9 `STAY_ON_ROLE_CHANGE`) | comes from the foundation header and `SessionProvider`; this screen has no role code | unit "role switch present"; foundation `session.test.tsx` |
| G3-2-15 | copy: masked recipient only; never "SMS" or "email"; 12-hour times | only `to_masked`; copy file has no "SMS"/"email" | `Scr02.test.tsx` uses `expectNo24HourTimes` and `queryByText(/sms|email/i)` |
| G3-2-16 | a11y: list is `ol`; copy button 44 px; status in words | `ol`/`li`; `Button density="chat"` (44 px) | unit roles; Step 8 visual check |
| G3-2-17 | N-11: per message `expires_at`, `status`, masked recipient; scoped to the browser's session | the screen reads only those fields; scoping is the server's (nothing to do client-side; see section 8) | unit (fields); contract review |

### 3.2 SCR-3 Demo guide and controls (`/demo`)

| ID | Requirement | How implemented | How verified |
|---|---|---|---|
| G3-3-01 | R1: "Demo guide · How this demo works"; demo bar (date, staffing); shared role switch and Sign out (CON-8 clock read, CON-7, CON-10, CON-22) | `DemoPageHeader title="Demo guide" showDemoBar`; `h1` "How this demo works" | `Scr03.test.tsx` "header" |
| G3-3-02 | R2 Real vs simulated, static (two columns, stack on phones) | `RealVsSimulated`: `Card` with `CardHeader as="h2" title="What is real and what is simulated"`; grid `min-[700px]:grid-cols-2`; `h3` "Real" and "Simulated", each a `<ul>` with the exact items in `scr03/copy.ts` (list in 4.3) | `Scr03.test.tsx` "real vs simulated" |
| G3-3-03 | R3 Staffing: current state in words; switch "Demo: simulate staff on shift"; one line "The chat will offer a live queue, and the staff console will show it." (CON-7) | `StaffingControl`: `CardRow label="Staffing"` value = `staffing.label` (or "Checking…"); `Switch` (native checkbox, `role="switch"`, visible label); the one-line sentence under it | `Scr03.test.tsx` "default" |
| G3-3-04 | R4 Two roles: four numbered steps, static | `TwoRoles`: `<ol>` of the four sentences in 4.3 | `Scr03.test.tsx` "steps" |
| G3-3-05 | R5 Links: Chat, Demo inbox, Staff queue, Monitoring, Evaluation; chat opens in this tab, console in a new tab | `DemoLinks`: paths read from `SCREENS` by id (SCR-1, SCR-2, SCR-5, SCR-10, SCR-11). Chat, Monitoring, Evaluation: `<Link>` same tab. Demo inbox (SCR-2 route line: "opened in a new tab") and Staff queue: `<a target="_blank" rel="noopener">`. The new-tab choice for the inbox is a gap decision (8.4) | `Scr03.test.tsx` "links" asserts hrefs and `target` |
| G3-3-06 | R6 Reset: "Reset the demo" with consequence and a confirm step; needs the login session; login kept | `ResetControl`: `Card` "Reset the demo", consequence paragraph (`RESET_CONSEQUENCE`), secondary `Button` "Reset the demo" that opens the `Dialog` | `Scr03.test.tsx` "reset dialog" |
| G3-3-07 | default: all regions, staffing "Nobody online", switch off | `getStaffing` OFF | scenarios `scr03.default`, `scr03.default-on` |
| G3-3-08 | empty, partial: n/a (matrix) | none | `scenarios.integrity` |
| G3-3-09 | loading: static regions at once; staffing line and switch "Checking…", switch disabled until CON-7 answers | `useOp("getStaffing",...)` `data === undefined && status === "loading"` shows value "Checking…" and `disabled` switch; the other cards render normally | scenario `scr03.loading`; unit "loading" |
| G3-3-10 | error (a): read fails: "Staffing status is unavailable." with retry; static guide still shows | `data === undefined && status === "error"`: `ErrorLine message="Staffing status is unavailable." onRetry={refetch}`; switch disabled | scenario `scr03.error-read`; unit "read error" |
| G3-3-11 | error (b): write fails: "Staffing didn't change. Try again." next to the switch; switch returns to its last known state | optimistic display (`pendingMode`), revert on rejection; message in a polite line under the switch for **any** failure (including RESET_IN_PROGRESS 503) | scenario `scr03.error-staffing-write`; unit "write error reverts" |
| G3-3-12 | error (c): reset fails: "The reset didn't finish. Nothing was half-reset; try again." | any failure of `resetDemo` except the 409 below | scenario `scr03.error-reset`; unit "reset failure" |
| G3-3-13 | CON-9: RESET_IN_PROGRESS (409): "Resetting…" stays | button stays disabled and labelled "Resetting…" for `details.retry_after_ms` (fallback 5000) while a polite line says "The demo is resetting. Try again in a few seconds." (this sentence is UI_CONTRACTS' RESET_IN_PROGRESS text); then enables | scenario `scr03.error-reset-in-progress`; unit "409" |
| G3-3-14 | stale: every 10 s and on focus re-read; if changed: "Staffing changed since you opened this page." and the switch moves | `useOp("getStaffing", {}, { pollMs: 10000, pauseWhenHidden: true, refetchOnFocus: true })`; `lastKnownMode` ref set on first data and after each **own** write; a later `data.mode !== lastKnownMode` while no write is pending shows `StaleLine` "Staffing changed since you opened this page." and updates `lastKnownMode` | scenario `scr03.stale-staffing-changed`; unit "staffing changed elsewhere" |
| G3-3-15 | success: on: "Simulated staff on shift (demo). The banner now shows on the chat and the console." | `ResultLine` text from `staffingSuccessLine("simulated_on_shift", n)` | scenario `scr03.success-on`; `copy.test.ts`; unit |
| G3-3-16 | success: off with waiting: "Shift ended. 1 waiting customer now has the 1-business-day promise." (N-12: converted count) | `converted_cases` from `StaffingResponse`: 1 gives the exact sentence; n > 1: "Shift ended. {n} waiting customers now have the 1-business-day promise."; 0: "Shift ended. Nobody is online." (gap, 8.4) | scenarios `scr03.success-off-waiting`, `scr03.success-off-none`; `copy.test.ts` |
| G3-3-17 | success: reset: "Demo reset. Bookings, cases and codes are back to the start, and the date is Fri Oct 16, 2026. Open chats have ended." (N-14) | `resetSuccessLine(openChatsEnded)`: always the first sentence; append " Open chats have ended." only when `open_chats_ended > 0` (FLOW-12 "reset during a live chat"). Then, when the role changed, append the CON-10 sentence "The demo was reset, so you're back to the customer role. Pick a role again." (G3-3-20) | scenarios `scr03.success-reset`, `scr03.success-reset-quiet`; `copy.test.ts`; unit |
| G3-3-18 | disabled: switch disabled while saving; reset button disabled while a reset runs ("Resetting…") | `pendingMode !== null` disables the switch; `useAction("resetDemo").pending` disables the reset button and swaps its label | scenarios `scr03.disabled-saving`, `scr03.disabled-resetting`; unit |
| G3-3-19 | confirm dialog: title "Reset the demo?" + "This ends every open chat, clears cases made during the demo, restores the seeded cases and sets the date back to Fri Oct 16, 2026."; buttons "Reset the demo" and "Cancel"; Cancel has focus by default; native `<dialog>`, focus trapped, returned to the reset button | foundation `Dialog open onClose title="Reset the demo?" initialFocus="cancel"`; children: the consequence paragraph and two buttons, **Cancel first in DOM order, then "Reset the demo"** (so `initialFocus="first"` is a safe fallback; see Step 5 note on how Dialog identifies Cancel). Confirm closes the dialog, then the page button shows "Resetting…" | unit "dialog"; Step 8 visual check |
| G3-3-20 | Reset keeps the login; the role goes back to customer (OpenAPI `resetDemo` description, CON-9, SCREEN_SPECS note 10(a)); SCREEN_SPECS N-14 and R6 say "role kept": **conflict, decision: OpenAPI wins** (section 8.4 G-1) | after a successful reset: `callOp("getSession")` then `useSession().setSession(s)`, then `refetchAll()` and `useDemoStatus().refresh()`. If the role before the click was not `customer` and the new role is `customer`, append the CON-10 role-reset sentence to the success line | unit "reset returns role to customer" |
| G3-3-21 | links Monitoring, Evaluation (IA cross-screen row: SCR-9, SCR-3 to SCR-10, SCR-11) | G3-3-05 | unit |
| G3-3-22 | a11y: switch is a native checkbox with `role="switch"` and a visible label; results announce politely; targets 44 x 44 px | `Switch.tsx` (4.5); `ResultLine`/`StaleLine` (verify they are live regions, Step 5 note) | `Switch.test.tsx`; unit |
| G3-3-23 | copy: "simulated" never applied to the assistant; no claim anyone is online | copy file review | `copy.test.ts` asserts no line pairs "assistant" with "simulated" and no "online" except "Nobody online"/"Nobody is online" |
| G3-3-24 | N-30: SCR-3's toggle and reset need the login session, like every CON | global 401 path (`emitAuthLost`); nothing screen-specific | foundation `session.test.tsx`; scenario `shared.session-ended` |

### 3.3 SCR-4 Role switch (`/role`, optional full page; the header control is foundation's)

| ID | Requirement | How implemented | How verified |
|---|---|---|---|
| G3-4-01 | The control in every header: "Acting as", four segments, current filled and ticked, "current" in its accessible name, never a menu, Sign out beside it, radiogroup, arrow keys, polite announcement, first control after skip link, 44 px | **Foundation** (`RoleSwitch`, F§Step 6 item 3 and F-10). G3 builds none of it | foundation `RoleSwitch.test.tsx`; G3 `Scr04.test.tsx` checks it is present on `/role` |
| G3-4-02 | Full page: R3 statement "These are demo roles, not real accounts. There is no second password. Everything here is fictional." | `Scr04.tsx`, static `<p>` | `Scr04.test.tsx` "statement" |
| G3-4-03 | R4: four buttons, each one title and one line | `RoleChoices`: data from `useOp("listDemoRoles", {})` (`roles[].display_name` as title, `roles[].sees` as the line). The contract's `sees` wording differs from SCREEN_SPECS R4's shorter lines; the contract is the source of truth for what each role sees (CON-10 Reads), so no spec text is hard-coded (G-3). Each is a `<button>` card in an `<ul>`, not a primary (all equals, design 8.11) | `Scr04.test.tsx` "four roles from the contract" |
| G3-4-04 | R5 foot: "Back to the demo guide" | `<Link to="/demo">` (path from `SCREENS` SCR-3) | `Scr04.test.tsx` "foot" |
| G3-4-05 | default: four roles, current marked; screen unchanged | the current role (`useSession().role`) is rendered as a **non-button** `<div aria-current="true">` with a `Tag` "Current" and VisuallyHidden ", current"; the other three are buttons | scenario `scr04.default`; unit |
| G3-4-06 | empty, partial: n/a | none | `scenarios.integrity` |
| G3-4-07 | loading: chosen segment "Switching…", all four disabled, screen stays until the answer | `useSession().switching`: the matching button shows "Switching…"; every button `disabled` while `switching !== null` | scenario `scr04.loading`; unit "switching" |
| G3-4-08 | error: "Couldn't switch role. Try again." under the control, current stays marked | show `useSession().switchError` under the role list via `ErrorLine` (no retry button; clicking a role again is the retry). The header control shows the same string; two polite lines is accepted | scenarios `scr04.error-network`, `scr04.error-reset-in-progress`; unit |
| G3-4-09 | stale (a): session ended: next call UNAUTHENTICATED goes to SCR-12 with "Your demo session ended, so please sign in again." | foundation `emitAuthLost` navigates to `/login?return_to=%2Frole&reason=expired`; G3-12-12 shows the line | scenario `scr04.stale-session-ended` |
| G3-4-10 | stale (b): staff screen opened as customer shows "You're acting as the customer. Switch to a staff role to see this." with the switch beside it, no staff data | foundation `RoleGate` and `RoleNotAllowedPanel` (F-12). Nothing built here; the scenario lets the reviewer reach it | scenarios `scr04.stale-staff-as-customer`, `scr04.stale-role-reset` |
| G3-4-11 | success: Customer to SCR-1, Representative SCR-5, Supervisor SCR-7, Owner SCR-9; the new role marked and announced | `useSession().switchRole(role)` does request, announce and navigation (F§4.9). Called as `void switchRole(role)` from the button | foundation `session.test.tsx`; G3 `Scr04.test.tsx` checks the PUT body `{ role }`; scenario `scr04.success-lands-on-home` |
| G3-4-12 | success: on SCR-2, SCR-3, SCR-10, SCR-11 the screen stays | foundation `STAY_ON_ROLE_CHANGE` | scenario `scr04.success-stays` (route `/demo`) |
| G3-4-13 | disabled: all segments disabled during a switch; current segment is not pressable | G3-4-07 and G3-4-05 | scenario `scr04.disabled-during-switch` |
| G3-4-14 | no password field anywhere on this control | none rendered | `Scr04.test.tsx` "no password" |
| G3-4-15 | a11y: one `h1` | `h1` "Choose a demo role" (gap, 8.4: SCREEN_SPECS names no h1 text for this page) | `Scr04.test.tsx` |
| G3-4-16 | N-15, N-29: role is per login session in the cookie, so a second tab sees the change on its next staff call; chat routes ignore the role | server behaviour; nothing client-side. Group note states it | n/a |
| G3-4-17 | Role list failure | if `listDemoRoles` fails, fall back to four buttons labelled `ROLE_LABEL[role].full` with no description line and **no error text** (the header switch still works; no copy invented) | `Scr04.test.tsx` "roles list fails" |

### 3.4 SCR-12 Demo login (`/login`, public, frame `auth`)

| ID | Requirement | How implemented | How verified |
|---|---|---|---|
| G3-12-01 | R1: brand mark and "Demo access"; statement "This is a demonstration of Meridian's assistant. These are not Meridian accounts, and everything here is fictional." | inside one `Card`: a plain-text line "Meridian Home Comfort" (no logo asset, no icon: the spec forbids a logo treatment that could pass as a real sign-in), `h1` "Demo access", the statement | `Scr12.test.tsx` "default" |
| G3-12-02 | R2: message line, empty by default; `aria-live="polite"` | `<p id="login-message" aria-live="polite">` always mounted, neutral style | `Scr12.test.tsx` |
| G3-12-03 | R3: "Username" (hint "From the README"), "Password" (hint "From the README"), "Show password" checkbox, "Sign in" (the one emerald button) | `LoginForm`: two `Field`+`TextInput`, `Checkbox label="Show password"`, `Button variant="primary" type="submit"`. `name`/`autoComplete`: `username` with `username`, `password` with `current-password`; `spellCheck={false}`, `autoCapitalize="none"`; `<form method="post" onSubmit>` with `preventDefault` so nothing reaches the URL | `Scr12.test.tsx` |
| G3-12-04 | R4 foot: "The username and password are in the README that came with the submission." Never the values | static `<p>` | `Scr12.test.tsx` |
| G3-12-05 | default: empty fields, focus on Username | `useEffect` focuses the username input when the form is shown | `Scr12.test.tsx` "focus" |
| G3-12-06 | loading: button "Signing in…", both fields read-only | `useAction("login").pending`; `readOnly` on both, `Button loading`, label swapped immediately (design 8.2 says after 300 ms; deviation recorded) | scenario `scr12.loading`; unit |
| G3-12-07 | disabled: "Sign in" disabled while either field is empty and while in flight | `canSubmit = username.trim() !== "" && password !== ""` | scenarios `scr12.disabled-empty-fields`, `scr12.disabled-in-flight`; unit |
| G3-12-08 | error (refused): one line "That username or password didn't work. Check the README and try again." whatever the cause; password cleared, username kept, focus on Password; `aria-invalid` on both fields with the message as description (N-28) | `useLogin` maps `ApiError.code` in `["LOGIN_FAILED","LOGIN_RATE_LIMITED","VALIDATION_ERROR"]` to ONE branch: set message, `setPassword("")`, focus password. `aria-invalid="true"` and `aria-describedby="login-message"` (appended to the Field's own describedBy) on both inputs. **Decision G-2:** LOGIN_RATE_LIMITED shows the same sentence (SCREEN_SPECS SCR-12 and N-28 win over UI_CONTRACTS' "Too many attempts…") | scenarios `scr12.error-refused`, `scr12.error-rate-limited`; unit "same handling for both codes" |
| G3-12-09 | error (unreachable): "Couldn't reach the demo. Try again." (network, not login) | any other `ApiError` (status 0 / NETWORK, 5xx): that sentence; fields keep their values; `aria-invalid` not set | scenario `scr12.error-unreachable`; unit |
| G3-12-10 | stale (a): sent back after the session ended: "Your demo session ended, so please sign in again."; after sign-in land on the page asked for | `useSearchParams`: show the line only when `reason === "expired"`; destination from `return_to` (G3-12-13) | scenario `scr12.stale-session-ended`; unit |
| G3-12-11 | stale (b): already signed in: "You're already signed in. Continue to the demo, or sign out." with "Continue" and "Sign out"; form hidden | `AlreadySignedIn` when `useSession().status === "ready" && session && !leaving`. Continue: `navigate(resolveDestination(returnTo, HOME_BY_ROLE[session.role]))`; Sign out: `useSession().signOut()` | scenario `scr12.stale-already-signed-in`; unit |
| G3-12-12 | success: redirect to the page asked for, else SCR-1 as customer; no success screen (CON-22 `landing: "/"`) | `resolveDestination(returnTo, res.landing)` (4.2); `navigate(dest, { replace: true })` | `destination.test.ts`; scenarios `scr12.success-chat`, `scr12.success-asked-page` |
| G3-12-13 | `return_to` is only a same-origin relative path (F-34) | `resolveDestination` uses `safeReturnTo`, ignores any `return_to` that starts with `/login` | `destination.test.ts` |
| G3-12-14 | No flash of "already signed in" after a successful sign-in | `leaving` state set **before** `setSession(res.session)` | `Scr12.test.tsx` "no flash" |
| G3-12-15 | partial, empty: n/a | none | `scenarios.integrity` |
| G3-12-16 | a11y: one `h1` "Demo access"; labelled fields; button is `type="submit"`; targets 44 px; keyboard-only; reads statement, message, form | DOM order as listed; shared controls provide 44 px | `Scr12.test.tsx`; Step 8 |
| G3-12-17 | Copy: never "staff login", "customer portal", "Meridian account", "Forgot password", "Create account", "Need help?" | copy file review | `Scr12.test.tsx` `queryByText(/forgot|create account|need help|staff login/i)` is null |
| G3-12-18 | "Public": the one route that answers without a session; no role switch (frame `auth`) | `AppFrame variant="auth"`, no header | `Scr12.test.tsx` "no role switch" |

### 3.5 Dev layer (state switcher, F-26)

| ID | Requirement | How implemented | How verified |
|---|---|---|---|
| G3-D-01 | Every real standard state of SCR-2, 3, 4, 12 has at least one scenario (F§Step 7 coverage test) | the four scenario files (4.4) with `complete: true` | `src/dev/scenarios.integrity.test.ts`, `src/dev/scenarios.coverage.test.ts` (foundation tests, must pass) |
| G3-D-02 | Mock gaps that Prism cannot show (F§8.2): staffing OFF response, inbox after reset and after CODE_SENT, polling changes | reactions and transforms (4.4, 4.6); each listed in the group note | `src/dev/reactions/g3.test.ts` |

## 4. Shared code to use

### 4.1 Foundation interfaces consumed (names from F§4.4-4.9; the code under `src/` is the truth, see Step 0)

```ts
import { callOp, type OperationId } from "@/api/client";          // OPS, callOp<K>(op, args?)
import { useOp, useAction } from "@/api/useOp";
import { ApiError } from "@/api/errors";                          // .status .code .details .isUnauthenticated
import { refetchAll } from "@/api/refetch";
import { useSession } from "@/state/session";                     // SessionApi (4.1a)
import { useDemoStatus } from "@/state/demoStatus";               // { clock, staffing, refresh(), setFromChat, setSource }
import { SCREENS } from "@/routes";                               // ScreenDef { id, slug, path, title, roles, frame, public?, group }
import { ROLES, ROLE_LABEL, HOME_BY_ROLE, type Role } from "@/lib/roles";
import { safeReturnTo } from "@/lib/returnTo";
import type { components } from "@/api/types.gen";
import { AppFrame, Main, DemoPageHeader, ErrorLine, EmptyState, StaleLine, ResultLine, Time } from "@/components/shared"  // or the real barrel/paths
import { Button, Field, TextInput, Checkbox, Tag, Card, CardHeader, CardBody, CardRow, Skeleton, Dialog, VisuallyHidden, useAnnounce } from "@/components/ui"
import { IconCheck, IconClock, IconCopy, IconBack } from "@/components/ui/icons"
```
The barrel paths are the foundation's choice; open the files and import from where they really are.

**4.1a `SessionApi`** (F§4.9): `status: "loading"|"ready"|"signed-out"`, `session: SessionInfo|null`, `role: Role|null`, `switching: Role|null`, `switchError: string|null`, `switchRole(role): Promise<void>`, `signOut(): Promise<void>`, `setSession(s: SessionInfo): void`.

**4.1b Call shapes** (types come from `types.gen.ts`; `CallArgs` is `{ path?, body?, query?, signal? }`):

| Use | Call |
|---|---|
| Inbox | `useOp("listDemoInbox", {}, { pollMs: 5000, pauseWhenHidden: true, refetchOnFocus: true })` returns `InboxResponse { messages: InboxMessage[] }` |
| Staffing read | `useOp("getStaffing", {}, { pollMs: 10000, pauseWhenHidden: true, refetchOnFocus: true })` returns `Staffing { mode: "nobody_online"\|"simulated_on_shift"; label: string; banner: string\|null }` |
| Staffing write | `useAction("setStaffing").run({ body: { mode } })` returns `StaffingResponse { mode; label; converted_cases: number }` |
| Reset | `useAction("resetDemo").run({ body: { confirm: true } })` returns `ResetResponse { ok: true; open_chats_ended: number; clock: DemoClock; roles_reset: number }`; errors: 409 `RESET_IN_PROGRESS` (`details.retry_after_ms`), 500 `RESET_FAILED`, 400, 401 |
| Roles | `useOp("listDemoRoles", {})` returns `{ roles: { role: Role; display_name: string; sees: string }[] }` |
| Role switch | `useSession().switchRole(role)` (never call `switchRole` op directly) |
| Session refresh | `callOp("getSession")` returns `SessionInfo`; then `useSession().setSession(info)` |
| Login | `useAction("login").run({ body: { username, password } })` returns `LoginResponse { session: SessionInfo; landing: string }`; errors: 401 `LOGIN_FAILED`, 429 `LOGIN_RATE_LIMITED` (`details.retry_after_ms`), 400 `VALIDATION_ERROR`. `login` has `security: []` and a 401 from it does **not** trigger the global auth-lost redirect (F§Step 5) |
| Logout | `useSession().signOut()` |

### 4.2 `scr12/destination.ts` (exact signature)

```ts
import { safeReturnTo } from "@/lib/returnTo";
/** Where to go after sign-in or "Continue". `returnTo` is the raw `return_to` query value. */
export function resolveDestination(returnTo: string | null | undefined, fallback: string | null | undefined): string {
  const asked = returnTo && !returnTo.startsWith("/login") ? safeReturnTo(returnTo) : "/";
  if (asked !== "/") return asked;
  return safeReturnTo(fallback ?? "/");
}
```
`destination.test.ts` cases: `("/staff/queue","/")` gives `/staff/queue`; `(null,"/")` gives `/`; `("//evil.com","/")` gives `/`; `("https://x","/")` gives `/`; `("/login?return_to=%2Fx","/")` gives `/`; `("/\\evil","/")` gives `/`; `(undefined,"/staff/owner")` gives `/staff/owner`; `("/demo/inbox?x=1","/")` gives `/demo/inbox?x=1`.

### 4.3 Exact copy (put each in the screen's `copy.ts`; tests assert the **literal** strings, not the constants)

SCR-2 `copy.ts`: `HEADER_TITLE="Demo delivery inbox"`, `H1="Simulated messages"`, `STATEMENT="Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification."`, `FOOT="This inbox carries codes only. Follow-ups are recorded on the case, never sent."`, `BACK="Back to the chat"`, `EMPTY_TITLE="No codes yet."`, `EMPTY_BODY="When the chat sends a code, it appears here. Ask the chat about your bill or book a visit to get one."`, `ERROR="The inbox didn't load. Try again."`, `NEW_CODE="New code received"`, `COPY="Copy code"`, `COPIED="Copied"`, `COPY_FAILED="Copy didn't work. Select the code and copy it."`, status words `Active`, `Used`, `Expired`.

SCR-3 `copy.ts`:
- `REAL`: "The assistant and its answers", "Meridian's knowledge base", "Bookings, written to a working copy of the scheduling database", "What you type as Riley".
- `SIMULATED`: "The date (Fri Oct 16, 2026)", "Staffing (nobody is online unless you turn on the simulation)", "The one-time code (sent to a demo inbox)", `Follow-ups and calls ("Demo: recorded, not sent")`.
- `STEPS`: "Keep the chat open in this tab." / "Use the role switch at the top to act as Representative (Riley), or open the console in a second tab." / "Ask the chat for a person." / "Claim and join from the queue, then switch back to Customer to see Riley's reply."
- `SWITCH_LABEL="Demo: simulate staff on shift"`, `SWITCH_HINT="The chat will offer a live queue, and the staff console will show it."`, `CHECKING="Checking…"`, `READ_ERROR="Staffing status is unavailable."`, `WRITE_ERROR="Staffing didn't change. Try again."`, `STALE="Staffing changed since you opened this page."`
- `ON_LINE="Simulated staff on shift (demo). The banner now shows on the chat and the console."`
- `RESET_CONSEQUENCE="This ends every open chat, clears cases made during the demo, restores the seeded cases and sets the date back to Fri Oct 16, 2026."`, `RESET_TITLE="Reset the demo?"`, `RESET_BUTTON="Reset the demo"`, `RESETTING="Resetting…"`, `CANCEL="Cancel"`, `RESET_DONE="Demo reset. Bookings, cases and codes are back to the start, and the date is Fri Oct 16, 2026."`, `RESET_CHATS=" Open chats have ended."`, `RESET_FAILED="The reset didn't finish. Nothing was half-reset; try again."`, `RESET_BUSY="The demo is resetting. Try again in a few seconds."`, `ROLE_RESET="The demo was reset, so you're back to the customer role. Pick a role again."`
- pure functions: `staffingSuccessLine(mode, converted: number): string` (on gives `ON_LINE`; off with 1 gives "Shift ended. 1 waiting customer now has the 1-business-day promise."; off with n>1 gives "Shift ended. {n} waiting customers now have the 1-business-day promise."; off with 0 gives "Shift ended. Nobody is online.") and `resetSuccessLine(openChatsEnded: number, roleWasReset: boolean): string`.

SCR-4 `copy.ts`: `H1="Choose a demo role"`, `STATEMENT="These are demo roles, not real accounts. There is no second password. Everything here is fictional."`, `BACK="Back to the demo guide"`, `CURRENT="Current"`, `SWITCHING="Switching…"`.

SCR-12 `copy.ts`: `BRAND="Meridian Home Comfort"`, `H1="Demo access"`, `STATEMENT="This is a demonstration of Meridian's assistant. These are not Meridian accounts, and everything here is fictional."`, `USERNAME="Username"`, `PASSWORD="Password"`, `HINT="From the README"`, `SHOW="Show password"`, `SIGN_IN="Sign in"`, `SIGNING_IN="Signing in…"`, `FOOT="The username and password are in the README that came with the submission."`, `REFUSED="That username or password didn't work. Check the README and try again."`, `UNREACHABLE="Couldn't reach the demo. Try again."`, `ENDED="Your demo session ended, so please sign in again."`, `ALREADY="You're already signed in. Continue to the demo, or sign out."`, `CONTINUE="Continue"`, `SIGN_OUT="Sign out"`.

### 4.4 Dev-layer types (F§4.9, frozen)

```ts
// src/dev/scenarios/types.ts (foundation)
export type StandardState = "default"|"empty"|"loading"|"partial"|"error"|"stale"|"success"|"disabled";
export type OpForce =
  | { example: string; status?: number; delayMs?: number; transform?: (body: any) => any }
  | { fail: "network"; delayMs?: number }
  | { hang: true }
  | { sequence: OpForce[] };
export interface Scenario { id: string; screen: ScreenId | "*"; state: StandardState; flowState?: string; label: string; route: string; role?: Role; staffing?: "nobody_online"|"simulated_on_shift"; ops?: Partial<Record<OperationId, OpForce>>; stream?: StreamScript; notes?: string }
export interface ScreenScenarios { complete?: boolean; scenarios: Scenario[] }   // each file: `export const screenScenarios: ScreenScenarios`
export interface Reaction { when: { op: OperationId; status?: number; example?: string }; then(ctx: DevCtx): void }   // each file: `export const reactions: Reaction[]`
// DevCtx: { world; setForce(op, force|null); setRole(role); setStaffing(mode); emit(thread, event); refetch() }
```
Facts about the mock that shape the scenarios (F§Step 8, read them again in `src/dev/resolve.ts` once it exists):
- A force on an authenticated op is ignored while the world is **signed out** (precedence step 2 beats step 3). A scenario therefore cannot make `getSession` answer 200 for a signed-out world, and `Scenario` has no `signedIn` field. Scenarios for SCR-12 that need a specific sign-in world say so in `notes` (and request R-F3, section 8).
- A `sequence` force is consumed **per call, across every caller of that op**, and React StrictMode (on in `main.tsx`) runs each mount effect twice, so **the first two entries of a sequence are consumed by the mount itself**. Every sequence in this plan therefore repeats its first value twice (or more) before the change. In production-like single mounts the change just arrives one poll later.
- `useOp` aborts the previous in-flight call when it starts a new one, but the dev transport has already consumed the sequence step.

### 4.5 `scr03/Switch.tsx` (G3 owns it; F§8.3)

```ts
export interface SwitchProps {
  checked: boolean; onCheckedChange(next: boolean): void;
  label: string; hint?: string; disabled?: boolean; id?: string; describedBy?: string;
}
```
Markup: `<label class="flex min-h-11 items-center gap-3">` containing a visually hidden native `<input type="checkbox" role="switch" checked disabled>` first (class `peer`), a track and thumb `<span>`s styled from the peer state (`peer-checked:`, `peer-focus-visible:` ring with the focus-ring token, `peer-disabled:` well fill), then the label text and, under it, the hint. Track on = accent token, off = well token with control edge. Transitions only under `motion-safe:`. Space and click toggle (native). Do not set `aria-checked` yourself (the native checkbox exposes it).

## 5. Steps

Work in `apps/web/`. After each step run its check. Keep screens as three layers: **hook** (`useX`, calls `useOp`/`useAction`, no JSX), **presentational parts** (props in, JSX out), **screen** (frame plus composition). Pure copy logic lives in `copy.ts` so it is testable without React. The only seams consumed are the foundation interfaces in 4.1 and `Scenario`/`Reaction`; do not add an abstraction.

### Step 0 · Preflight (no edits)
1. `cd /home/linuxuser/workspaces/inno-aea-callcenter/apps/web`. Confirm these exist (the foundation slice must have finished): `src/routes.ts`, `src/router.tsx`, `src/state/session.tsx`, `src/state/demoStatus.tsx`, `src/screens/ScreenStub.tsx`, `src/screens/scr02/Scr02.tsx`, `scr03/Scr03.tsx`, `scr04/Scr04.tsx`, `scr12/Scr12.tsx`, `src/components/ui/index.ts`, `src/components/shared/*`, `src/components/shell/*`, `src/test/render.tsx`, `src/dev/scenarios/{types,index,matrix,scr02,scr03,scr04,scr12}.ts`, `src/dev/reactions/{index,shared,scr02,scr03}.ts`. If any is missing, stop and report `BLOCKED-ON foundation`.
2. Open and read (props and behaviour, not guesses): `ScreenStub.tsx` (copy its frame, header, `Main`, title effect), `Dialog.tsx` (how Cancel gets initial focus), `ResultLine.tsx`, `StaleLine.tsx`, `ErrorLine.tsx`, `EmptyState.tsx`, `Card.tsx` (is `CardHeader.title` a `ReactNode`?), `Field.tsx`, `TextInput.tsx` (forwards `ref`; sets `aria-invalid`?), `Button.tsx`, `Tag.tsx`, `DemoPageHeader.tsx` (is its title an `h1`? it must not be; if it is, report and stop), `src/styles/theme.css` (the real Tailwind utility names for the semantic tokens), `src/test/render.tsx`, `src/test/fixtures.ts`, `src/dev/resolve.ts` if present.
3. `npm run typecheck` passes before you start.
**Check:** the three lines above are true; list any deviation from 4.1 in your report.

### Step 1 · SCR-12 login (smallest; everything else needs a way in)
1. `scr12/copy.ts`, `scr12/destination.ts` (4.2) and `destination.test.ts`. Run `npx vitest run src/screens/scr12/destination.test.ts`.
2. `useLogin.ts`: returns `{ username, setUsername, password, setPassword, show, setShow, phase, message, canSubmit, submit(), usernameRef, passwordRef, invalid }`. `submit()` in this order (the invariant each step protects is in brackets):
   1. return if `!canSubmit` or already submitting. [no double submit]
   2. `setMessage("")` is **not** called here: the previous refusal stays until the new answer. [no flicker of the live region]
   3. `const res = await login.run({ body: { username, password } })`.
   4. On success: `setLeaving(true)` **first** [no "already signed in" flash], then `setPassword("")`, `session.setSession(res.session)`, `navigate(resolveDestination(returnTo, res.landing), { replace: true })`. [credentials never linger in state or history; destination is always a safe relative path]
   5. On `ApiError` whose `code` is in `["LOGIN_FAILED","LOGIN_RATE_LIMITED","VALIDATION_ERROR"]`: **one** branch: `message = REFUSED`, `setPassword("")`, focus `passwordRef`. [N-28: same sentence, same field handling for every refusal cause]
   6. Any other error: `message = UNREACHABLE`, keep both fields, no `aria-invalid`.
3. `LoginForm.tsx` (presentational) and `AlreadySignedIn.tsx` (presentational: the `ALREADY` sentence, `Continue`, `Sign out` buttons; `Continue` is the primary).
4. `Scr12.tsx`: `AppFrame variant="auth"`, `Main`, one `Card`: BRAND line, `h1`, STATEMENT, message `<p id="login-message" aria-live="polite">`, then either `AlreadySignedIn` or `LoginForm` (G3-12-11). Message priority: refusal or unreachable text, else `ENDED` when `searchParams.get("reason") === "expired"`, else empty. Read `return_to` and `reason` with `useSearchParams()`; ignore a `return_to` that starts with `/login` (the foundation's redirect may produce `return_to=%2Flogin`; see R-F2). Set `document.title` like `ScreenStub` does. Show the form while `status === "loading"`.
5. Tests: `Scr12.test.tsx` (7.1).
**Check:** `npx vitest run src/screens/scr12` green; `npm run typecheck` green.

### Step 2 · SCR-4 `/role` page
1. `scr04/copy.ts`; `RoleChoices.tsx` (props: `roles: { role: Role; title: string; line: string | null }[]`, `current: Role | null`, `switching: Role | null`, `onPick(role)`); render per G3-4-05/07. The chosen button during `switching` shows "Switching…" but keeps its accessible name (`aria-label={title}` plus visible text).
2. `Scr04.tsx`: frame `page`, `DemoPageHeader title="Role switch" showDemoBar`, `Main`: `h1`, STATEMENT, `RoleChoices`, `ErrorLine message={switchError}` when non-null, foot `<Link to={path of SCR-3}>`. Data: `useOp("listDemoRoles", {})`; on error or while loading, build `roles` from `ROLES`/`ROLE_LABEL[role].full` with `line: null` (G3-4-17; skeleton rows while loading are optional).
3. Tests: `Scr04.test.tsx`.
**Check:** `npx vitest run src/screens/scr04` green.

### Step 3 · SCR-2 inbox
1. `scr02/copy.ts`; `useCopyCode.ts` (`{ copiedId, failedId, copy(id, code) }`, timers cleared on unmount).
2. `useInbox.ts`: wraps `useOp("listDemoInbox", ...)`; returns `{ messages (sorted by at descending), phase: "loading"|"error"|"empty"|"list", refetch }`; owns the "seen ids" ref and the `useAnnounce()` call (skip the first successful load; announce once per refresh that adds at least one new id).
3. `InboxMessageCard.tsx` (one message), `InboxList.tsx` (`ol`), `BackToChat` (inline in `Scr02.tsx` or its own tiny file; click logic G3-2-13).
4. `Scr02.tsx`: frame `page`, `DemoPageHeader title="Demo delivery inbox" showDemoBar`, `Main`: `h1`, STATEMENT, the phase body, footer (FOOT + BackToChat).
5. Tests: `Scr02.test.tsx`.
**Check:** `npx vitest run src/screens/scr02` green.

### Step 4 · SCR-3 guide and controls
1. `scr03/copy.ts` (4.3 including the two pure functions) and `copy.test.ts` (exact sentences for on, off 0/1/2, reset 0/2 with and without role reset, a forbidden-words check per G3-3-23).
2. `Switch.tsx` + `Switch.test.tsx` (4.5).
3. `useStaffingControl.ts`: wraps the polled `useOp("getStaffing")` and `useAction("setStaffing")`. Algorithm (invariants in brackets):
   1. `lastKnown` ref starts `null`; the first data sets it silently. [no false "changed" on load]
   2. `toggle(next: boolean)`: `mode = next ? "simulated_on_shift" : "nobody_online"`; `setPendingMode(mode)`; `setResult(null)`; `try { const r = await setStaffing.run({ body: { mode } }); lastKnown.current = r.mode; setResult({ kind: "success", mode: r.mode, converted: r.converted_cases }); await demoStatus.refresh(); await refetch(); } catch { setResult({ kind: "error" }) } finally { setPendingMode(null) }`. [optimistic switch reverts on failure; the shared demo bar and banner refresh after a write]
   3. Effect on `data`: if `pendingMode === null` and `lastKnown.current !== null` and `data.mode !== lastKnown.current` then `lastKnown.current = data.mode; setResult({ kind: "stale" })`. [own writes never trigger the stale line; a change elsewhere does]
   4. `checked = pendingMode ? pendingMode === "simulated_on_shift" : data?.mode === "simulated_on_shift"`; `disabled = data === undefined || pendingMode !== null`.
4. `StaffingControl.tsx` (presentational: `CardRow`, `Switch`, hint, `ErrorLine`/`StaleLine`/`ResultLine` per result kind), `RealVsSimulated.tsx`, `TwoRoles.tsx`, `DemoLinks.tsx` (paths from `SCREENS`).
5. `useResetDemo.ts`: `{ open, setOpen, confirm(), busy, result }`. `confirm()` in order: remember `roleBefore = session.role`; close the dialog; `await reset.run({ body: { confirm: true } })`; on success `try { setSession(await callOp("getSession")) } catch {}`, `refetchAll()`, `await demoStatus.refresh()`, result = success line with `roleWasReset = roleBefore !== "customer" && newRole === "customer"`. On `ApiError` with `status === 409`/`code === "RESET_IN_PROGRESS"`: result `busy` line, keep `busy` true for `details.retry_after_ms ?? 5000` ms (timer cleared on unmount), then false. Any other failure: `RESET_FAILED` line. [all-or-nothing wording; the login stays; the header reflects the server's role]
6. `ResetControl.tsx`: card, consequence paragraph, the button (`disabled`/label from `busy`), the `Dialog` (Cancel first, then confirm; `initialFocus="cancel"` if `Dialog` documents a Cancel marker, else `initialFocus="first"`), result line. After the result appears, move focus to the result line only if `ResultLine` is focusable (`tabIndex={-1}` or forwards a ref); otherwise rely on the polite announcement. If `ResultLine`/`StaleLine` are not live regions (`role="status"` or `aria-live="polite"`), also call `useAnnounce()` with the same text.
7. `Scr03.tsx`: frame `page`, `DemoPageHeader title="Demo guide" showDemoBar`, `Main`: `h1`, cards in order R2, R3, R4, R5, R6 (card titles: "What is real and what is simulated", "Staffing", "How to play both roles", "Links", "Reset the demo"; the titles are this plan's wording from the IA table names).
8. Tests: `Scr03.test.tsx`.
**Check:** `npx vitest run src/screens/scr03` green.

### Step 5 · Scenarios and reactions
1. Replace the body of `src/dev/scenarios/scr02.ts`, `scr03.ts`, `scr04.ts`, `scr12.ts` with the lists in 4.6, `complete: true`, same export name (`screenScenarios`), imports `import type { ScreenScenarios } from "./types";`. Every scenario carries `screen`, `state`, `label` (plain words), `route`, and `notes` wherever the table says how it is reached.
2. Fill `src/dev/reactions/scr02.ts` and `scr03.ts` exactly as in 4.7. Leave `scr04.ts`, `scr12.ts` as the foundation wrote them.
3. `src/dev/reactions/g3.test.ts` (7.2).
**Check:** `npx vitest run src/dev/reactions/g3.test.ts src/dev/scenarios.integrity.test.ts src/dev/scenarios.coverage.test.ts` green. If the integrity test rejects a `route` containing a query string, strip the query from the `route` (4.6 uses none except where noted) and tell the integrator.

### Step 6 · Group note
Write `docs/ux/04-prototype/groups/g3-demo-pages.md` with these sections, in order: **Status** · **State table** (one row per real state of the four screens: screen, state, how it is reached, scenario id, test) · **Faked in the mock, and how** (the forces, transforms and reactions of 4.6-4.7, each with the OpenAPI example it starts from) · **Decisions made** (G-1 to G-6, section 8.4) · **Requests to the integrator** (R-F1 to R-F6, section 8.3 and 8.2, copied verbatim) · **Deviations** (the `VisuallyHidden` code, immediate "Signing in…", the two polite lines on `/role`) · **Checks** (the commands and their results).

### Step 7 · Visual check (only if Chrome DevTools MCP is available; otherwise say "not run")
`npm run mock` and `npm run dev:mock` in the background (ports 4019 and 5184; remember the PIDs and stop only those). Open `http://127.0.0.1:5184/login?signedin=0`, then use the panel's States tab to reach each scenario in 4.6 at 390 and 1280 px wide. Check: no horizontal scroll; focus ring visible on every control; `/role` buttons and the Copy button at least 44 px tall; no red anywhere; 12-hour times only; the switch is reachable and toggles with Space. Fix defects in owned files. List what you checked in the report.

### Step 8 · Final gates
Run section 7 once, in order.

## 4.6 Scenario lists (exact ids; `route` is a path only)

Notation: `ops` entries are written `op: force`. `OFF/ON` etc. are the named examples already in the OpenAPI file (checked against `OPS[op].responses`). Role defaults to the first role of the screen (customer); a role is stated only where it differs.

**`scr02.ts`** (`screen: "SCR-2"`, route `/demo/inbox`)

| id | state | flowState | ops | notes |
|---|---|---|---|---|
| `scr02.default` | default | `code arrives (FLOW-3)` | `listDemoInbox: { example: "ONE_ACTIVE" }` | |
| `scr02.empty` | empty | | `listDemoInbox: { example: "EMPTY" }` | |
| `scr02.empty-after-reset` | empty | `reset (FLOW-12)` | `listDemoInbox: { example: "ONE_ACTIVE" }` | "Reached by: open this, go to /demo, reset the demo, come back: the reaction in 4.7 empties the inbox." |
| `scr02.loading` | loading | | `listDemoInbox: { hang: true }` | skeleton stays until you leave |
| `scr02.error` | error | | `listDemoInbox: { example: "RESET_IN_PROGRESS" }` | CON-6 503 |
| `scr02.error-rate-limited` | error | | `listDemoInbox: { example: "REQUEST_RATE_LIMITED" }` | 429 |
| `scr02.error-network` | error | | `listDemoInbox: { fail: "network" }` | |
| `scr02.stale-new-code` | stale | `code arrives (FLOW-3)` | `listDemoInbox: { sequence: [{ example: "EMPTY" }, { example: "EMPTY" }, { example: "ONE_ACTIVE" }] }` | "Starts empty; within about 10 s a code appears and 'New code received' is announced." |
| `scr02.stale-used-and-expired` | stale | `code used` | `listDemoInbox: { example: "USED_AND_EXPIRED" }` | Used and Expired rows |
| `scr02.stale-expires-on-refresh` | stale | | `listDemoInbox: { sequence: [{ example: "ONE_ACTIVE" }, { example: "ONE_ACTIVE" }, { example: "USED_AND_EXPIRED" }] }` | "Active at first; after a refresh the first code is Expired and a Used one is announced as new." |
| `scr02.success-copied` | success | | `listDemoInbox: { example: "ONE_ACTIVE" }` | "Press Copy code: 'Copied' shows for 2 s." |
| `scr02.disabled-used-expired` | disabled | | `listDemoInbox: { example: "USED_AND_EXPIRED" }` | copy disabled with the status word |

**`scr03.ts`** (`screen: "SCR-3"`, route `/demo`; `staffing` default `nobody_online`)

| id | state | flowState | staffing / ops | notes |
|---|---|---|---|---|
| `scr03.default` | default | | `getStaffing: { example: "OFF" }` | |
| `scr03.default-on` | default | `simulation on / off (FLOW-8)` | `staffing: "simulated_on_shift"`; `getStaffing: { example: "ON" }`, `setStaffing: { example: "TURNED_OFF_WITH_WAITING" }` | switch starts on |
| `scr03.loading` | loading | | `getStaffing: { hang: true }` | "Checking…", switch disabled, static regions visible |
| `scr03.error-read` | error | | `getStaffing: { fail: "network" }` | retry link |
| `scr03.error-staffing-write` | error | | `getStaffing: { example: "OFF" }`, `setStaffing: { fail: "network" }` | "Flip the switch: it returns to off with the error line." |
| `scr03.error-reset` | error | | `resetDemo: { example: "RESET_FAILED" }` | 500 |
| `scr03.error-reset-in-progress` | error | | `resetDemo: { example: "RESET_IN_PROGRESS" }` | 409 |
| `scr03.stale-staffing-changed` | stale | | `getStaffing: { sequence: [OFF, OFF, OFF, OFF, OFF, ON] }` (each `{ example }`) | "Within about 20 s: 'Staffing changed since you opened this page.' and the switch moves. Quicker: in the panel's per-operation select set getStaffing to ON." |
| `scr03.success-on` | success | `simulation on / off (FLOW-8)` | `getStaffing: { example: "OFF" }`, `setStaffing: { example: "TURNED_ON" }` | |
| `scr03.success-off-waiting` | success | `shift ended with live-queued customers` | `staffing: "simulated_on_shift"`; `getStaffing: { example: "ON" }`, `setStaffing: { example: "TURNED_OFF_WITH_WAITING" }` | "Turn the switch off: 1 waiting customer line." |
| `scr03.success-off-none` | success | | same as above but `setStaffing: { example: "TURNED_OFF_WITH_WAITING", transform: (b) => ({ ...b, converted_cases: 0 }) }` | the 0-customers line (valid against `StaffingResponse`) |
| `scr03.success-reset` | success | `reset during a live chat (FLOW-12)` | `resetDemo: { example: "RESET" }`; role `representative` | "Reset: the line includes 'Open chats have ended.' and the role-reset sentence; the header role returns to Customer." |
| `scr03.success-reset-quiet` | success | | `resetDemo: { example: "RESET", transform: (b) => ({ ...b, open_chats_ended: 0, roles_reset: 0 }) }` | no chats sentence |
| `scr03.disabled-saving` | disabled | | `getStaffing: { example: "OFF" }`, `setStaffing: { hang: true }` | "Flip the switch: it stays disabled while saving." |
| `scr03.disabled-resetting` | disabled | | `resetDemo: { hang: true }` | "Confirm a reset: the button reads 'Resetting…' and stays disabled." |

**`scr04.ts`** (`screen: "SCR-4"`)

| id | state | route / role | ops | notes |
|---|---|---|---|---|
| `scr04.default` | default | `/role` | `listDemoRoles: { example: "ROLES" }` | |
| `scr04.loading` | loading | `/role` | `switchRole: { example: "TO_REPRESENTATIVE", delayMs: 4000 }` | "Click Representative: 'Switching…' for 4 s." |
| `scr04.error-network` | error | `/role` | `switchRole: { fail: "network" }` | "Couldn't switch role. Try again." |
| `scr04.error-reset-in-progress` | error | `/role` | `switchRole: { example: "RESET_IN_PROGRESS" }` | 503 |
| `scr04.stale-session-ended` | stale | `/role` | `listDemoRoles: { example: "UNAUTHENTICATED_EXPIRED" }` | goes to SCR-12 with the ended line |
| `scr04.stale-staff-as-customer` | stale | `/staff/queue`, role `customer` | none (the foundation's role emulation answers 403) | F-12 panel |
| `scr04.stale-role-reset` | stale | `/staff/queue`, role `customer` | `getQueue: { example: "ROLE_NOT_ALLOWED_ROLE_RESET" }` | "The demo was reset, so you're back to the customer role. Pick a role again." |
| `scr04.success-lands-on-home` | success | `/role` | none | "Click a role: you land on its home. Needs R-F1 to return the clicked role." |
| `scr04.success-stays` | success | `/demo` | none | role switch on SCR-3: the page stays |
| `scr04.disabled-during-switch` | disabled | `/role` | `switchRole: { hang: true }` | all four disabled |

**`scr12.ts`** (`screen: "SCR-12"`, route `/login` unless stated)

| id | state | flowState | ops | notes |
|---|---|---|---|---|
| `scr12.default` | default | `first visit (FLOW-12)` | none | "Needs a signed-out world: panel Session tab, Restart; or open /login?signedin=0." |
| `scr12.loading` | loading | | `login: { hang: true }` | type anything, Sign in |
| `scr12.error-refused` | error | `wrong login (FLOW-12)` | `login: { example: "LOGIN_FAILED" }` | |
| `scr12.error-rate-limited` | error | | `login: { example: "LOGIN_RATE_LIMITED" }` | same sentence as refused (G-2) |
| `scr12.error-unreachable` | error | | `login: { fail: "network" }` | |
| `scr12.stale-session-ended` | stale | `session expired on any screen` | route `/staff/queue`, role `representative`; `getSession: { example: "UNAUTHENTICATED_EXPIRED" }`, `getQueue: { example: "UNAUTHENTICATED_EXPIRED" }` | the foundation redirects to `/login?return_to=%2Fstaff%2Fqueue&reason=expired` |
| `scr12.stale-already-signed-in` | stale | `signed in already` | none | "Needs a signed-in world: panel Session tab, Fake sign-in on, then this scenario; or open /login?signedin=1." |
| `scr12.success-chat` | success | | none | "Sign in with anything: you land on the chat as the customer." |
| `scr12.success-asked-page` | success | | route `/staff/queue` | "Needs a signed-out world. Sign in: you land on /staff/queue (as the customer, so the role-gate panel shows)." |
| `scr12.disabled-empty-fields` | disabled | | none | button disabled until both fields are filled |
| `scr12.disabled-in-flight` | disabled | | `login: { hang: true }` | fields read-only, button disabled |

## 4.7 Reactions (exact)

`src/dev/reactions/scr02.ts`:
```ts
import type { Reaction } from "../scenarios/types";
// FLOW-12: a reset clears every code. Source example: listDemoInbox EMPTY.
// FLOW-3: the chat sending a code puts one in the inbox. Source example: listDemoInbox ONE_ACTIVE.
export const reactions: Reaction[] = [
  { when: { op: "resetDemo", status: 200 }, then: (ctx) => ctx.setForce("listDemoInbox", { example: "EMPTY" }) },
  { when: { op: "submitTurn", example: "CODE_SENT" }, then: (ctx) => ctx.setForce("listDemoInbox", { example: "ONE_ACTIVE" }) },
];
```
`src/dev/reactions/scr03.ts` (the setStaffing example must follow the request, but the mock picks examples without reading the body; alternate after each write; the shared reaction already moves `world.staffing` from the request body):
```ts
import type { Reaction } from "../scenarios/types";
// setStaffing has only TURNED_ON and TURNED_OFF_WITH_WAITING (no "off, nobody waiting"). After a write, the next write is the opposite one.
export const reactions: Reaction[] = [
  { when: { op: "setStaffing", example: "TURNED_ON" }, then: (ctx) => ctx.setForce("setStaffing", { example: "TURNED_OFF_WITH_WAITING" }) },
  { when: { op: "setStaffing", example: "TURNED_OFF_WITH_WAITING" }, then: (ctx) => ctx.setForce("setStaffing", { example: "TURNED_ON" }) },
];
```
Known artefacts (list in the group note): a first "off" click with the world started as `?staffing=on` and no scenario gets `TURNED_ON` (use `scr03.default-on`); every "off" says 1 waiting customer (use `scr03.success-off-none` for 0).

## 6. Data and fixtures

Synthetic only; every value is an OpenAPI named example: inbox `msg-1` code `482913`, `msg-2` code `117204`, masked recipient `···02`, times `2026-10-16T14:07:00-05:00` and `…14:17:00-05:00`; staffing `OFF`/`ON`; `TURNED_ON`, `TURNED_OFF_WITH_WAITING`; `RESET` (`open_chats_ended: 2`, `roles_reset: 1`, clock `2026-10-16T14:20:00-05:00`); roles `ROLES`; sessions `CUSTOMER`, `REPRESENTATIVE`, `TO_SUPERVISOR`, `TO_OWNER`; login placeholders `<demo-username>` / `<demo-password>` (use them in tests as typed text; no real credentials exist). Reuse `SESSION_*` and `STAFFING_*` from `src/test/fixtures.ts`; define inbox, reset, roles and login bodies as constants at the top of each test file with a comment naming the OpenAPI example they copy. No file may contain the real demo username or password.

## 7. Checks

All commands run from `apps/web/`. Test environment and helpers: F§Step 6 (`renderWithProviders(ui, { route, transport, role })`, `makeFakeTransport`, `jsonResponse` in `src/test/fakeTransport.ts`, `expectNo24HourTimes` in `src/test/no24h.ts`). Use Vitest fake timers for the 2 s, 5 s, 10 s and 5000 ms cases. If jsdom lacks `HTMLDialogElement.showModal`/`close`, the foundation's `setup.ts` or `Dialog.test.tsx` shows the stub to reuse; do not edit `setup.ts`, define it in the test file.

### 7.1 Tests the implementer writes (names are the `it(...)` titles; add more if needed)

`src/screens/scr02/Scr02.test.tsx`: "header: h1, statement, role switch present", "default: newest message with masked recipient, 12-hour time, code, Active status and expiry", "code is read digit by digit", "empty: exact copy and Back to the chat", "loading: skeleton and header", "error then retry", "used and expired: copy disabled, status words", "copy: writes the code, shows Copied for 2 s", "copy failure shows the fallback line", "polls every 5 s", "new code is announced after the first load only", "back to the chat: focuses the opener when there is one", "back to the chat: navigates to / when there is no opener", "no sms/email wording, no 24-hour times".

`src/screens/scr03/Scr03.test.tsx`: "header and static regions render with the staffing call pending", "default: switch off, label Nobody online, links with hrefs and targets, four steps", "loading: Checking… and switch disabled", "read error: message and retry", "turn on: body {mode}, switch disabled while pending, exact success line, demo status refreshed", "turn off with 1, 2 and 0 converted: exact lines", "write error: exact line and the switch reverts", "stale: change elsewhere shows the line and moves the switch; an own write does not", "reset dialog: opens with exact text, Cancel has focus, Cancel sends nothing", "reset confirm: body {confirm:true}, button Resetting… and disabled, exact success line with Open chats have ended", "reset with no chats ended omits that sentence", "reset returns the role to customer: getSession re-read, header shows Customer, role-reset sentence appended", "reset failure: exact line, button enabled again", "reset 409: disabled for retry_after_ms with the busy line".
`src/screens/scr03/Switch.test.tsx`: "has role switch and a visible label", "toggles on click and Space", "disabled blocks toggling", "hint is described-by".
`src/screens/scr03/copy.test.ts`: the pure functions and the forbidden-words check.

`src/screens/scr04/Scr04.test.tsx`: "h1, statement and foot link", "four roles from listDemoRoles with display name and sees", "current role is not a button and says current", "clicking a role sends PUT {role}", "while switching: chosen shows Switching… and all are disabled", "switch error shows Couldn't switch role. Try again. and keeps the current role marked", "roles list fails: four buttons from ROLE_LABEL, no error text", "no password field".

`src/screens/scr12/Scr12.test.tsx` (route `/login`, `getSession` answers 401 `UNAUTHENTICATED` unless a test says otherwise; mock `useNavigate` with `vi.mock("react-router", ...)` returning a spy): "default: h1, statement, hints, Show password, foot, no role switch, Username focused, Sign in disabled", "Sign in enables only when both fields are filled", "Enter submits the body {username,password} and nothing goes to the URL", "in flight: Signing in…, fields read-only", "LOGIN_FAILED: exact line, password cleared, username kept, Password focused, both fields aria-invalid and described by the message", "LOGIN_RATE_LIMITED gives the identical sentence and handling", "network failure: Couldn't reach the demo. Try again., fields kept", "success: setSession and navigate to return_to", "success without return_to goes to /", "unsafe return_to goes to /", "reason=expired shows the ended line; reason=none does not", "already signed in (getSession 200): sentence, Continue and Sign out, form hidden", "Continue goes to return_to or the role home", "Sign out calls logout", "no flash of the already-signed-in panel after a successful login", "no forbidden login wording".
`src/screens/scr12/destination.test.ts`: the eight cases in 4.2.

`src/dev/reactions/g3.test.ts`: "resetDemo 200 forces the inbox to EMPTY", "submitTurn CODE_SENT forces the inbox to ONE_ACTIVE", "setStaffing TURNED_ON forces the next write to TURNED_OFF_WITH_WAITING and the reverse", "reactions ignore other ops" (build a fake `DevCtx` with `vi.fn()` for `setForce`).

### 7.2 Commands

While iterating (one folder at a time): `npx vitest run src/screens/scr12`, then `scr04`, `scr02`, `scr03`, then `npx vitest run src/dev/reactions/g3.test.ts src/dev/scenarios.integrity.test.ts src/dev/scenarios.coverage.test.ts`. After each step `npm run typecheck`.

**Once before reporting, in this order, stop at the first red** (fast gates first, per rule `build-loop-test-scope`; this slice touches no shared fixture, settings, dependency or cross-codebase module, so the full suite is not needed):

| # | Command | Passing looks like |
|---|---|---|
| 1 | `npm run lint` | 0 errors; no new `react-hooks/exhaustive-deps` warnings |
| 2 | `npm run typecheck` | exits 0 |
| 3 | `npx vitest run src/screens/scr02 src/screens/scr03 src/screens/scr04 src/screens/scr12 src/dev/reactions src/dev/scenarios.integrity.test.ts src/dev/scenarios.coverage.test.ts src/styles` | all green (`src/styles` = the guard test, which fails on red, hex, `Prefer`, cookie literals) |
| 4 | `npx vitest run src/routes.test.ts src/screens/stubs.test.tsx src/state` | `routes` and `state` green. **`stubs.test.tsx` is expected to fail only on the four assertions "exactly one h1 containing its id" for SCR-2, 3, 4, 12** (the real h1 texts are "Simulated messages", "How this demo works", "Choose a demo role", "Demo access"). Do not edit the foundation test; report the exact failing test names (R-F4). Any other failure is yours to fix |
| 5 | `npm run build && npm run check:dist` | build exits 0; check prints no hits (proves no screen imports the dev layer) |

Existing tests that must stay green: everything under `src/api`, `src/lib`, `src/components`, `src/state`, `src/styles`, `src/routes.test.ts`, `src/dev/*.test.ts`, except the four stub assertions named above. The Python suite is untouched and not run. The Playwright smoke (`tests/e2e/smoke.spec.ts`) asserts the stub h1 prefix and will fail for these four screens until R-F4 lands; do not run it as a gate, and do not edit it.

## 8. Risks and requests

### 8.1 Collisions with other slices
1. **Foundation tests that name the stub h1** (`src/screens/stubs.test.tsx`, `tests/e2e/smoke.spec.ts`): see R-F4. Other groups (G1, G2, G4, G5) will hit the same thing; the integrator fixes it once.
2. **`src/dev/scenarios/shared.ts` and `src/dev/reactions/shared.ts`** (foundation) overlap with G3 on `switchRole`, `login`, `logout`, `setStaffing`, `resetDemo`: G3's reactions only add forces on `listDemoInbox` and `setStaffing`; they never touch `world` and run after the shared ones. If G5 (SCR-7 shift switch) also needs the setStaffing alternation, it is already global (a force on the op), so G5 writes nothing.
3. **`Switch.tsx` is G3-local** (F§8.3). G5's SCR-7 shift switch builds its own wrapper unless the integrator promotes it.
4. **`useAnnounce` and `useDemoStatus().refresh()`** are used by G1 too; G3 only calls them.
5. No file overlap with G1, G2, G4, G5: G3 writes only `scr02`, `scr03`, `scr04`, `scr12`, `dev/scenarios/scr0{2,3,4}.ts` + `scr12.ts`, `dev/reactions/scr0{2,3}.ts` + `g3.test.ts`, and its group note.

### 8.2 What Prism cannot show (mechanism used)
| Gap | Mechanism |
|---|---|
| `setStaffing` has no "off, nobody waiting" example | `transform` on `TURNED_OFF_WITH_WAITING` (`converted_cases: 0`); alternation reactions (4.7) |
| The mock answers `setStaffing` with `TURNED_ON` whatever the request | alternation reactions (4.7) |
| Inbox after a reset or a CODE_SENT turn | reactions (4.7) |
| Polling that changes between calls (new code, expiry, staffing elsewhere) | `sequence` forces with the first value repeated for StrictMode (4.4) |
| 0 chats ended on reset | `transform` on `RESET` |
| `ONE_ACTIVE` example has `expires_at` 2:17 pm but the `START` clock says 2:20 pm | not worked around: the screen trusts the server `status` (R2). Request to the contract owners: move one of the two example times |

### 8.3 Requests to the integrator (shared files; G3 edits none of them)
- **R-F1 (needed for SCR-4 success and every role switch in the mock).** `src/dev/resolve.ts` / `defaults.ts` choose `switchRole`'s example without reading the request: the default is "first 2xx example", so clicking Supervisor would answer `TO_REPRESENTATIVE`. Add, before the defaults step: for `switchRole`, `Prefer: code=200, example=TO_${body.role.toUpperCase()}` (examples `TO_REPRESENTATIVE`, `TO_SUPERVISOR`, `TO_OWNER`, `TO_CUSTOMER` exist). Same idea for `setStaffing` (`ON` to `TURNED_ON`, `OFF` to `TURNED_OFF_WITH_WAITING`) would make G3's alternation reactions redundant; they are harmless if it lands.
- **R-F2.** `SessionProvider` must not redirect when the current path is `/login` (a 401 `getSession` on the login page is the normal signed-out case; redirecting would write `return_to=%2Flogin`). On `/login` it should just set `status: "signed-out"`; and when `getSession` answers 200 on `/login` it must set `status: "ready"` and `session` (that is how SCR-12 knows "already signed in"). G3 defends against `return_to` starting with `/login` but cannot fix the redirect.
- **R-F3.** Add `signedIn?: boolean` to `Scenario` (default: `true`, except `screen === "SCR-12"` where the default is `false`) and make `applyScenario` set `world.signedIn` from it. Until then G3's SCR-12 scenarios describe the needed world in `notes`.
- **R-F4.** Relax `src/screens/stubs.test.tsx` and `tests/e2e/smoke.spec.ts`: after a group replaces a stub, check "exactly one `h1`" (and, for the e2e, the role switch and no drift) instead of "h1 starts with SCR-n". G3's h1 texts: SCR-2 "Simulated messages", SCR-3 "How this demo works", SCR-4 "Choose a demo role", SCR-12 "Demo access".
- **R-F5.** Confirm `ResultLine` and `StaleLine` are polite live regions and `ResultLine` is focusable (`tabIndex={-1}` or ref); confirm how `Dialog` marks the Cancel button for `initialFocus="cancel"`. G3 adapts to what exists (Steps 0 and 4).
- **R-F6.** Contract owners: (a) add `setStaffing` example "off, nothing waiting"; (b) `listDemoInbox` `ONE_ACTIVE` vs `getDemoClock` `START` times disagree (code expires 2:17 pm, clock says 2:20 pm); (c) UI_CONTRACTS says `LOGIN_RATE_LIMITED` shows "Too many attempts. Wait a moment and try again." but SCREEN_SPECS SCR-12 and N-28 require the same sentence as a refusal; align one of them; (d) SCREEN_SPECS N-14 and SCR-3 R6 say reset keeps "the current role" but OpenAPI `resetDemo`, CON-9 and note 10(a) say the role returns to customer; align.

### 8.4 Decisions made in this plan (reversible, none needs Innocent before building)
- **G-1 Reset and role.** OpenAPI and CON-9 win over the SCREEN_SPECS "role kept" wording: after a reset the role is customer and the login stays (G3-3-20). One call `getSession` plus `setSession` keeps the header true.
- **G-2 Rate-limit sentence.** The login screen gives one sentence for every refusal including `LOGIN_RATE_LIMITED` (SCREEN_SPECS SCR-12 and N-28; it also keeps the throttle from being probed). Reversal: one branch in `useLogin.ts` and one constant.
- **G-3 Roles text.** `/role` shows the contract's `display_name` and `sees`, not SCREEN_SPECS R4's shorter lines (no hard-coded role text; the contract exists to carry it).
- **G-4 Gaps filled with new copy** (the only non-verbatim copy): "Shift ended. Nobody is online." (off, 0 converted); "Copy didn't work. Select the code and copy it."; "Choose a demo role" (h1 of `/role`); card titles "What is real and what is simulated", "Staffing", "How to play both roles", "Links"; the role-reset sentence appended to the reset line reuses CON-10's existing sentence.
- **G-5 Links.** Demo inbox and Staff queue open in a new tab on SCR-3; Chat, Monitoring and Evaluation in the same tab.
- **G-6 Not built (spec gap).** IA lists a "demo date and how the clock moves" line on SCR-3; SCREEN_SPECS has no copy or region for it. Not built; the demo bar carries the date. SCR-3 R2's "Fri Oct 16, 2026" is static text as specified and stays that after a supervisor advances the clock.
- Other: "Signing in…" appears immediately (design 8.2 says after 300 ms); the unreachable-network refusal keeps both fields.

## 9. Readiness

**READY.** No `NEEDS-DECISION`. The decisions in 8.4 are copy and precedence choices with a documented reversal. Dependencies on the foundation are R-F1 to R-F5: the slice builds and its unit tests pass without them, but the in-browser checks of SCR-4 success (R-F1), SCR-12 (R-F2, R-F3) and the e2e smoke (R-F4) need the integrator to apply them. If Step 0 finds a foundation file missing, report `BLOCKED-ON foundation`.

Report back with: the section 7.2 outputs (all five), the list of foundation props or behaviours that differed from 4.1, the Step 7 notes (or "not run"), and any place you deviated from this plan and why.
