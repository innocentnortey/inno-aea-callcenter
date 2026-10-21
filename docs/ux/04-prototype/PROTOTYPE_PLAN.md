# UX-4 prototype plan

## Status

UX-4, **foundation built** (2026-10-21): app shell, router, role gate, tokens, typed API client, dev layer and state switcher are in `apps/web/`. All five screen groups (G1 to G5) have landed and the integrator pass is done (2026-10-21): all 12 screens are real, the `yaml` dev dependency is declared, `.landed-wash` and `.check-draw` are in `base.css`, `requestPerson` defaults to `LIVE_QUEUED` when simulated staff are on shift, the sr-only `SCR-n · ` heading prefix is gone, and the "Prototype only" launcher sits top-right below 700 px so it never covers the chat composer. **Not yet done:** the browser look (light/dark, 390 px) for G3 and G5, `npm run smoke:mock` and the Playwright smoke (both need Prism or Vite running, which the integrator pass did not start).

## Run it

Two terminals from `apps/web/`: `npm run mock` (Prism, http://127.0.0.1:4019) and `npm run dev:mock` (Vite, http://127.0.0.1:5184, proxies `/api` to Prism, mounts the dev layer). From a laptop: `ssh -L 5184:127.0.0.1:5184 claude-vultr`. Ports: Prism 4019, Vite 5184, real API 8000 (only `npm run dev`, not built yet). Not ours: 4010/5173, 4012/5180, 4013/5183. Env: `WEB_PORT`, `MOCK_PORT`, `API_PORT`.

## What is clickable

| Screen | Route | Group | Status |
|---|---|---|---|
| SCR-1 Customer chat | `/` | G1 + G2 | stub |
| SCR-2 Demo delivery inbox | `/demo/inbox` | G3 | stub |
| SCR-3 Demo guide and controls | `/demo` | G3 | stub |
| SCR-4 Role switch | `/role` | G3 | stub |
| SCR-5 Representative queue | `/staff/queue` | G4 | stub |
| SCR-6 Case view | `/staff/cases/:reference` | G4 | stub |
| SCR-7 Supervisor oversight | `/staff/oversight` | G5 | stub |
| SCR-8 Review list of flags | `/staff/flags` | G5 | stub |
| SCR-9 Business-owner outcomes | `/staff/owner` | G5 | stub |
| SCR-10 Monitoring | `/monitoring` | G5 | stub |
| SCR-11 Evaluation report | `/eval` | G5 | stub |
| SCR-12 Demo login | `/login` | G3 | stub |

Working now on every screen: the demo-login gate (`/login?return_to=…&reason=none|expired`), the role switch (four roles, current marked, landings Customer to `/`, Representative to `/staff/queue`, Supervisor to `/staff/oversight`, Owner to `/staff/owner`; it stays on `/demo`, `/demo/inbox`, `/monitoring`, `/eval`), sign out, the role gate on staff screens, the demo bar and staffing banner, light and dark themes.

## What is faked, and how

Every fake lives in `src/dev/**`; nothing outside it knows about Prism, `Prefer` headers, cookies or delays.

| Fake | Mechanism |
|---|---|
| Demo login and cookie | Any non-empty username and password is accepted; `login` answers the `LOGGED_IN` example; the dev layer sets `mhc_session=prototype-synthetic` so Prism accepts calls (it stays set after sign-out: "signed out" is emulated, see below) |
| Role switch and role enforcement | `x-roles` from the OpenAPI decide: an operation whose roles exclude the current dev role is answered with the `ROLE_NOT_ALLOWED` example |
| Staffing, clock, reset worlds | `World` + reactions: setStaffing, resetDemo update the world; defaults pick `ON`/`OFF`, `SIMULATION_ON`/`STARTED`, `STAFFED_WITH_WAITING`/`SEEDED` |
| Session expiry and signed-out | `expireNext`, signed-out world: `UNAUTHENTICATED(_EXPIRED)` examples |
| Supervisor and owner `getSession` | Prism's `getSession` only has CUSTOMER and REPRESENTATIVE; the dev layer stores the body of the last `switchRole` (`TO_SUPERVISOR`, `TO_OWNER`) and answers from it |
| Scripted SSE | `src/dev/stream/dev-stream.ts`: scenario scripts, reaction `emit`, and the panel's Stream tab; Prism's stream body is read and discarded |
| Chat director | `src/dev/directors/*` pick the `submitTurn` example from the request (default `ANSWER_WITH_SOURCE`); typed words are never echoed |
| Delays and forced failures | `OpForce`: `delayMs`, `hang`, `fail: "network"`, `sequence` |

## The state switcher

Bottom bar "Prototype only" (collapsed to a pill), tabs **States · Session · Calls · Stream · Look**. States: a screen jumper, the current screen's scenarios grouped by the eight standard states (n/a cells greyed with the spec's reason), shared scenarios under "Anywhere", per-operation example selects, "Clear forces". Session: fake sign-in, role, expire, refuse next login, reset role, restart, theme, delay. Calls: every request (op, status, example, ms, **Drift**), copy JSON. Stream: chat events and drop/reconnect. Look: the component kit at `/__kit`.
URL parameters: `?signedin ?role ?staffing ?ex ?delay ?theme ?scenario`. Scenario ids are `scrNN.<kebab>` (`scr01-core` and `scr01-cards` for the two chat groups) and `shared.*` (`shared.session-ended`, `shared.role-reset`, `shared.staffing-on`, `shared.staffing-off`, `shared.offline`, `shared.slow`). The matrix is 12 screens x 8 states: 96 cells, 82 real, 14 n/a (`src/screens/matrix.ts`, re-exported by `src/dev/scenarios/matrix.ts`). A group flips `complete: true` in its scenario file when every real state has a scenario; `scenarios.coverage.test.ts` then enforces it.

## The contract check

`npm run gen:types` (openapi-typescript) and `npm run examples` (operation index) regenerate `src/api/types.gen.ts` and `contract.gen.json`; `typecheck`, `test`, `build`, `dev` run them first, so a contract change breaks the build. `npm run check:gen` fails when the committed files are stale. `npm run smoke:mock` sends every operation x every named example to Prism and fails on a wrong status or an `sl-violations` error. In the browser, a Prism violation becomes a `[contract drift]` console error, a call-log row marked **Drift**, and a thrown `CONTRACT_DRIFT` error. The Playwright smoke (12 routes x 2 widths, axe) fails on any drift line.

## Per-group notes

- [G1 chat core](groups/g1-chat-core.md): SCR-1 shell and chat plumbing.
- [G2 chat cards](groups/g2-chat-cards.md): the card blocks in the SCR-1 thread.
- [G3 demo pages](groups/g3-demo-pages.md): SCR-2, SCR-3, SCR-4, SCR-12.
- [G4 staff queue and case](groups/g4-staff-queue-case.md): SCR-5, SCR-6.
- [G5 oversight and reads](groups/g5-oversight-reads.md): SCR-7 to SCR-11.

### Dev fixtures vs named OpenAPI examples

Most states use a **named OpenAPI example**, forced by a scenario. These states use a **dev fixture or a transform** instead (from the group notes):

- **G1/G2 (SCR-1):** partial reply, staffed emergency line, quick-checks list, slot card (urgent), cancelled-with-write, change request (cancel, staffed), refund handoff, general-only handoff, no window fits (`src/dev/scenarios/scr01-cards.fixtures.ts`; cards C-4, C-5, C-9); every chat event beyond the three OpenAPI ones (`src/dev/stream/events.ts`).
- **G3 (SCR-2 to 4, 12):** named examples and reactions only; no fixtures recorded in its note.
- **G4 (SCR-5, SCR-6):** release / start / close-unresolved result lines, owner and supervisor `allowed_actions` (owner read-only case), stream events beyond FRAMES, and case pages 0005, 0006, 0012 with empty briefs (`case.fixtures.ts`, `case-transforms.ts`, `directors/case-actions.ts`).
- **G5 (SCR-7 to 11):** transforms in `scenarios/g5-transforms.ts` (`withLiveQueue`, `withoutRow`, `withNullPromises`, `withExtraFlag`, `withReviewed`, `rebaseMonitoring`) over named examples, because no example covers those cases.

Everything else is a named example. `/staff/cases` with no reference has no scenario (`scr06.no-case` was not added: the integrity test only accepts routes that match `/staff/cases/:reference`, so it would need a route and matrix change).

## Known mock artefacts

- Prism's SSE answer is one finite text body; only three chat events exist as OpenAPI examples. Every other chat event and every case event is a dev fixture typed against the schema (`src/dev/stream/events.ts`). Request: named examples in the OpenAPI.
- `getSession` has no SUPERVISOR or OWNER example (worked around above).
- Write-then-read consistency (claim then read the case, clock advance then overdue) is done by reactions and `OpForce.sequence`, not by a server.
- Typed words are not echoed back; the reply is the chosen example's fixed text.
- States with no named example (owner read-only case, fee and overdue variants) use `OpForce.transform` only when the result still validates; otherwise they are requests to add an example.
- `RESET_IN_PROGRESS` exists under 503 for most operations and 409 for `resetDemo`: use `?ex=resetDemo:409/RESET_IN_PROGRESS`.
- Prism answers 401 itself when the cookie is missing (probe: `GET /api/session` without a cookie returns 401), so the dev layer always keeps the fake cookie and emulates "signed out" by asking for the `UNAUTHENTICATED` example.

## Known deviations

- Stack: React/Vite SPA with owned shadcn-style components, not server templates (reconcile lines are in the foundation plan section 8.1).
- Fonts via `@fontsource` latin files (no preload, no `size-adjust` metrics): design.md 3.1 asks for them at UX-4; deferred to UX-5.
- `check-fonts.py`: `tnum` is present in Instrument Sans and Inter, **missing in Geist Mono** (all its digits are the same width, so this is harmless); Inter's `cv11` is **missing** from the @fontsource latin files, so `font-feature-settings: "cv11"` has no effect (single-storey *a* not applied). Open decision for UX-5: whether to self-host the full Inter file.
- Owner console nav (`Outcomes · Review list`) is this plan's decision; IA gives none.
- Role-gate copy for non-customer roles is a proposal ("You're acting as {role}. Switch to {roles} to see this.").
- The OpenAPI `reviewFlag` is `PATCH`, not `PUT`.

## Data

Synthetic only. Every value comes from the OpenAPI named examples (Omar Patel, MHC-C-0007/0008, Riley, demo clock `2026-10-16T14:20:00-05:00`).

## Checks

| Command | Result |
|---|---|
| `npm run lint` | Pass (2026-10-21, no output) |
| `npm run typecheck` | Pass (gen:types and examples ran first; 30 operations) |
| `npm run check:gen` | Pass ("generated files are current") |
| `npm test` | Pass: 115 files, 1043 passed, 1 skipped (1044) |
| `npm run build && npm run check:dist` | Pass ("dist is clean: no dev-layer markers") |
| `npm run smoke:mock` | Not run (needs Prism running; no long-lived servers started) |
| Playwright smoke | Not run (needs Vite and Prism running) |
| Browser sweep, `chrome-desktop` (`--workers=6 --fully-parallel`) | Pass: 478 run (474 scenario-theme runs + 4 flows), 478 passed, 0 failed |
| Browser sweep, `chrome-phone` (same flags) | Pass: 478 run, 241 passed, 0 failed, 237 skipped (dark runs are desktop-only) |

Integrator results measured 2026-10-21 in `apps/web/`. Foundation results are in the implementer's report.
