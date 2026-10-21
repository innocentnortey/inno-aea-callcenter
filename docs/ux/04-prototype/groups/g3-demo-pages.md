# UX-4 group G3: demo pages (SCR-2 inbox, SCR-3 guide and controls, SCR-4 role page, SCR-12 login)

## Status

Built 2026-10-21 from `docs/plans/fanout/2026-10-21-ux4/g3-demo-pages.md`. Code in `apps/web/src/screens/scr02`, `scr03`, `scr04`, `scr12`; scenarios in `src/dev/scenarios/scr0{2,3,4}.ts` and `scr12.ts`; reactions in `src/dev/reactions/scr02.ts` and `scr03.ts`. The visual check (plan Step 7) was not run: the implementer had no browser tool.

## State table

| Screen | State | How it is reached | Scenario | Test |
|---|---|---|---|---|
| SCR-2 | default | one active code | `scr02.default` | `Scr02.test.tsx` default |
| SCR-2 | empty | no codes; also after a reset | `scr02.empty`, `scr02.empty-after-reset` | empty |
| SCR-2 | loading | hung read | `scr02.loading` | loading |
| SCR-2 | error | 503, 429, network | `scr02.error`, `scr02.error-rate-limited`, `scr02.error-network` | error then retry |
| SCR-2 | stale | new code arrives; used and expired; active expires | `scr02.stale-new-code`, `scr02.stale-used-and-expired`, `scr02.stale-expires-on-refresh` | polls, new code announced |
| SCR-2 | success | Copy code shows "Copied" 2 s | `scr02.success-copied` | copy |
| SCR-2 | disabled | Used and Expired rows | `scr02.disabled-used-expired` | used and expired |
| SCR-3 | default | staffing off / on | `scr03.default`, `scr03.default-on` | default |
| SCR-3 | loading | hung staffing read | `scr03.loading` | loading |
| SCR-3 | error | read, staffing write, reset, reset 409 | `scr03.error-read`, `scr03.error-staffing-write`, `scr03.error-reset`, `scr03.error-reset-in-progress` | read error, write error, reset failure, reset 409 |
| SCR-3 | stale | staffing changed elsewhere | `scr03.stale-staffing-changed` | stale |
| SCR-3 | success | on; off with 1 / 0 waiting; reset; reset with no chats | `scr03.success-on`, `.success-off-waiting`, `.success-off-none`, `.success-reset`, `.success-reset-quiet` | turn on, turn off, reset confirm |
| SCR-3 | disabled | saving; resetting | `scr03.disabled-saving`, `scr03.disabled-resetting` | turn on, reset confirm |
| SCR-4 | default | four roles, current marked | `scr04.default` | `Scr04.test.tsx` |
| SCR-4 | loading | hanging or slow switch | `scr04.loading` | while switching |
| SCR-4 | error | network, 503 | `scr04.error-network`, `scr04.error-reset-in-progress` | switch error |
| SCR-4 | stale | session ended; staff screen as customer; role reset | `scr04.stale-session-ended`, `scr04.stale-staff-as-customer`, `scr04.stale-role-reset` | foundation `RoleGate` tests |
| SCR-4 | success | lands on role home; stays on /demo | `scr04.success-lands-on-home`, `scr04.success-stays` | clicking a role sends PUT |
| SCR-4 | disabled | hung switch | `scr04.disabled-during-switch` | while switching |
| SCR-12 | default / loading / error / stale / success / disabled | see `src/dev/scenarios/scr12.ts` (11 scenarios) | `scr12.*` | `Scr12.test.tsx` |

## Faked in the mock, and how

| Gap | Mechanism | Source example |
|---|---|---|
| Inbox after a reset | reaction `resetDemo 200` forces `listDemoInbox` to `EMPTY` | `EMPTY` |
| Inbox after a code is sent | reaction `submitTurn CODE_SENT` forces `ONE_ACTIVE` | `ONE_ACTIVE` |
| `setStaffing` ignores the request body in Prism | reactions alternate `TURNED_ON` and `TURNED_OFF_WITH_WAITING` after each write | both |
| `setStaffing` has no "off, nobody waiting" example | `transform` on `TURNED_OFF_WITH_WAITING` sets `converted_cases: 0` | `TURNED_OFF_WITH_WAITING` |
| `resetDemo` with 0 chats ended | `transform` on `RESET` sets `open_chats_ended: 0, roles_reset: 0` | `RESET` |
| Polling that changes between calls | `sequence` forces whose first value is repeated (React StrictMode consumes the first two calls) | `EMPTY`/`ONE_ACTIVE`, `OFF`/`ON` |

Known artefacts: a first "off" click in a world started with `?staffing=on` and no scenario gets `TURNED_ON` (use `scr03.default-on`); every "off" says 1 waiting customer (use `scr03.success-off-none` for 0).

## Decisions made

- **G-1** after a reset the role is customer and the login stays (OpenAPI and CON-9 win over "role kept" in SCREEN_SPECS). The page re-reads the session and appends the CON-10 sentence when the role changed.
- **G-2** one sentence for every login refusal, including `LOGIN_RATE_LIMITED` and `VALIDATION_ERROR`.
- **G-3** `/role` shows `display_name` and `sees` from `listDemoRoles`; on failure it falls back to `ROLE_LABEL[role].full` with no description and no error text.
- **G-4** new copy (gaps): "Shift ended. Nobody is online."; "Copy didn't work. Select the code and copy it."; "Choose a demo role"; card titles "What is real and what is simulated", "Staffing", "How to play both roles", "Links".
- **G-5** the demo inbox and staff queue links open in a new tab; chat, monitoring and evaluation in the same tab.
- **G-6** the "demo date and how the clock moves" line from IA is not built (no copy in SCREEN_SPECS); the demo bar carries the date.

## Requests to the integrator

- R-F2, R-F3, R-F4 were handled by the integrator while G3 was built (login-page redirect, `Scenario.signedIn`, relaxed stub tests). `scr12.stale-already-signed-in` uses `signedIn: true`.
- R-F5 (answered by reading the code): `ResultLine` is `role="status"` and focusable (`tabIndex={-1}`); `StaleLine` is `role="status"`; `Dialog` marks Cancel with `data-dialog-cancel`.
- R-F6 for contract owners: (a) add a `setStaffing` example "off, nothing waiting"; (b) `listDemoInbox` `ONE_ACTIVE` expires 2:17 pm but `getDemoClock` `START` says 2:20 pm; (c) UI_CONTRACTS shows a different `LOGIN_RATE_LIMITED` sentence than SCREEN_SPECS SCR-12 and N-28; (d) SCREEN_SPECS N-14 and SCR-3 R6 say reset keeps the role, OpenAPI and CON-9 say it returns to customer.

## Deviations

- The code is read digit by digit with a visually hidden text next to an `aria-hidden` visible code, not `aria-label` on `<b>`.
- "Signing in..." shows immediately (design 8.2 says after 300 ms).
- `/role` shows the "Couldn't switch role. Try again." line under the list as well as in the header switch (two polite lines).
- Three scenarios use `screen: "*"` (`scr04.stale-staff-as-customer`, `scr04.stale-role-reset`, `scr04.success-stays`) because the integrity test ties a screen's scenarios to that screen's own route, and these must open `/staff/queue` or `/demo`.
- `scr12.stale-session-ended` opens `/login?return_to=...&reason=expired` directly for the same reason, instead of starting on `/staff/queue`.
- On SCR-2 the "Back to the chat" link appears once: inside the empty state when empty, in the foot otherwise.
- Three test files run past 150 lines (`Scr02.test.tsx`, `Scr03.test.tsx`, `Scr12.test.tsx`); they hold the plan's named tests.

## Checks

On 2026-10-21, from `apps/web`: `npm run lint` clean; `npm run typecheck` exit 0; G3 screens + `src/dev/reactions` + scenario integrity/coverage + `src/styles`: 12 files, 204 passed, 9 skipped (other groups' coverage); `src/routes.test.ts`, `src/screens/stubs.test.tsx`, `src/state`: 34 passed; `npm run build` and `npm run check:dist` clean.
