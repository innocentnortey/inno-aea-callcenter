# UX-4 prototype · slice FOUNDATION (shared foundation, runs first)

> **Planner:** `fanout-planner` · **Date:** 2026-10-21 · **Project:** `/home/linuxuser/workspaces/inno-aea-callcenter` · **Direction:** A5 Service desk, light first (Innocent ✓ 2026-10-21) · **UX-3 signed** 2026-10-21 · **Implementer:** `fanout-implementer` (Sonnet) · **Readiness:** READY (see §9)
> This slice finishes **before** the five screen groups start (rule `fanout-plan-then-implement`: shared foundation first). It builds no screen content: every screen is a stub that proves the shell, the route, the role gate and the state mechanism.
> **Lane / loop:** `lane::build-loop`, not `risk::security` (a prototype on a mock; the demo login is a fake in the dev layer). Loop: plan → implement (code **and** its tests) → affected tests → code review. No test-writer, no frozen tests, no security agent. This slice has no worked pair (WP-N): it changes no model behaviour.
> **No git here:** the folder is not a git repository. Do not run `git init`, commit or push (Innocent has not asked).

## 1. Goal and sources

**Deliver, in `apps/web/` (React 19 + Vite + TypeScript + Tailwind v4 + owned shadcn-style components over Radix + lucide-react):**

1. Package scaffold and scripts: `dev`, `mock`, `dev:mock`, `typecheck`, `lint`, `test`, `build`, `gen:types`, `examples` (plus `check:gen`, `check:dist`, `smoke:mock`, `test:e2e`).
2. Design tokens from `design.md` as CSS variables mapped into Tailwind v4, with light default and dark secondary; fonts as local files.
3. Shared components needed by two or more groups (tables in §4.7–§4.8).
4. App shell and router: one route per SCR-1…SCR-12, each with a stub screen file the groups later replace; session bootstrap, login redirect, role gate.
5. A typed API client built on types generated from the OpenAPI file (a contract change breaks the build), with a transport seam.
6. The dev-only layer (never in production builds): fake login and role helpers, Prism `Prefer` selection, role/session emulation, scripted event streams, call log, and the **state switcher** that can force every spec'd state of every screen.
7. The cross-screen link table from `IA.md` as typed data, with a test.
8. `docs/ux/04-prototype/PROTOTYPE_PLAN.md` skeleton.
9. The handover to five follow-on groups (§2.4) so their owned files are disjoint.

**Sources (read; cite when in doubt):**

| Source | Sections used |
|---|---|
| `../.claude/skills/ux-pipeline/references/phases.md` | "UX-4 · Prototype" (lines ~197–228): real frontend folder, Prism mock, state switcher, dev-only mock machinery, no invented data, types generated, Prism validates every request |
| `../.claude/skills/ux-pipeline/references/tooling.md` | stack row "Prototype = the real frontend"; Prism 5.15.11; Playwright ≥ 1.64 (1.52 hangs on Node 24) |
| `docs/ux/03-structure/IA.md` | "Rules that apply to every screen", "Layout breakpoints", "Cross-screen links" |
| `docs/ux/03-structure/SCREEN_SPECS.md` | routes and Regions per screen; state matrix (96 cells: 82 real, 14 n/a); "Copy rules that apply on every screen"; "Contract needs" N-1…N-31 |
| `docs/ux/03-structure/UI_CONTRACTS.md` | conventions (cookie `mhc_session`, error shapes, ISO times), named errors, CON-1…CON-22 cards |
| `docs/ux/03-structure/ui-contracts.openapi.yaml` | 30 operations; `servers: http://localhost:4019`; `securitySchemes.mhcSession`; `x-roles` per operation; named examples |
| `docs/design/design.md` | §3 type, §4 colour (30 primitives, 21 semantic), §5 spacing/radii/lines/elevation, §6 motion, §7 dark, §8.0 component tokens (71), §8.1–8.11 anatomy, §9 responsive, §11 do/don't |
| `docs/artifacts/2026-10-21-direction-A5-service-desk.html` | reference look only; `design.md` wins on any difference |
| `../inno-riverside-onboarding/apps/web/` (package.json, vite.config.ts, src/api/client.ts, src/mock/*) and its `docs/ux/04-prototype/PROTOTYPE_PLAN.md` | worked precedent. **Departures here:** generated TypeScript types (Riverside kept a hand index), Radix-based owned components, no mock hooks inside `client.ts` (Riverside's `setClientHooks` lived there), real routes (not hash routes) |

## 2. Boundary

### 2.1 Owned files (the implementer may create or edit only these)

All paths relative to `/home/linuxuser/workspaces/inno-aea-callcenter/`. `apps/web/` does not exist yet.

```
apps/web/
  package.json  package-lock.json  tsconfig.json  vite.config.ts  eslint.config.js  index.html  .gitignore  components.json  README.md
  playwright.config.ts
  public/fonts/LICENSES/            (OFL text for the three families; see Step 3, item 8)
  scripts/paths.mjs  build-contract-index.mjs  check-generated.mjs  check-dist.mjs  check-fonts.py  prism-smoke.mjs  copy-font-licenses.mjs
  tests/e2e/smoke.spec.ts
  src/main.tsx  App.tsx  router.tsx  routes.ts  vite-env.d.ts
  src/styles/{index.css,theme.css,tokens.css,dark.css,fonts.css,base.css}
  src/lib/{cx.ts,time.ts,ids.ts,roles.ts,returnTo.ts}
  src/api/{types.gen.ts,contract.gen.json}           (GENERATED, committed; never hand-edit)
  src/api/{transport.ts,sse.ts,client.ts,errors.ts,refetch.ts,useOp.ts,useEventStream.ts}
  src/state/{session.tsx,demoStatus.tsx,theme.ts}
  src/components/ui/*          (primitives, §4.7)
  src/components/shared/*      (cross-group components, §4.8)
  src/components/shell/*       (AppFrame, headers, gates)
  src/test/{setup.ts,no24h.ts,render.tsx,fakeTransport.ts,fixtures.ts}
  src/screens/ScreenStub.tsx
  src/screens/scr01/{contract.ts,blocks.ts,index.ts,Scr01.tsx}   (contract.ts and blocks.ts: foundation-owned, FROZEN; index.ts and Scr01.tsx: stub, handed to G1)
  src/screens/scr01/cards/index.ts                                (stub, handed to G2)
  src/screens/scr02/{index.ts,Scr02.tsx} … scr12                  (twelve stub folders; see §2.4 for who takes each)
  src/dev/**                   (dev layer, §4.9; the group-owned stubs are listed in §2.4)
docs/ux/04-prototype/PROTOTYPE_PLAN.md
```

### 2.2 Read-only shared surfaces (never edit)

`docs/ux/03-structure/*` (incl. the OpenAPI file: a gap in it is a *request*, §8), `docs/design/design.md`, `docs/artifacts/**`, `.claude/**`, `CLAUDE.md`, `PROJECT-CHECKLIST.md`, `src/meridian/**`, `pyproject.toml`, `../inno-riverside-onboarding/**`.

### 2.3 Do not

- Do not edit `.claude/reference/area-map.md`, `docs/design/code-design.md`, `.claude/README.md`, `CLAUDE.md` or the checklist. The lines to reconcile are *reported* in §8.
- Do not edit the OpenAPI file, even to add a missing named example (request it, §8).
- Do not put `Prefer`, example names, fake cookies, delays, scenario names or `import.meta.env.MODE` checks anywhere outside `src/dev/**` and the one guarded block in `src/main.tsx`. Screens and `src/api/*` know nothing about Prism.
- Do not call `fetch` outside `src/api/transport.ts`. Screens call `callOp` / `useOp` / `useAction`.
- Do not use red, orange, amber or any hex value in components (only `src/styles/*` holds hex). Do not read `--color-safety`/`--safety-*` outside the allowlist in Step 3.
- Do not invent data a contract does not carry (no placeholder names, counts or times in screens or stubs). Stubs show ids, routes and state names only.
- Do not use 24-hour times or `text-transform: uppercase` on anything holding a time or date.
- Do not install shadcn through its CLI (it would overwrite the A5 tokens). Write the owned components by hand in shadcn style.
- Do not run `git`, start services you will not stop, or leave Prism/Vite running at the end.
- Do not add dependencies beyond §5 Step 1's list without recording the reason in `README.md`.

### 2.4 Hand-over: the five screen groups (proposal; the orchestrator confirms)

Each group is its own `fanout-planner` → `fanout-implementer` pair after this slice. Owned paths are disjoint; none edits `src/components/**`, `src/api/**`, `src/state/**`, `src/styles/**`, `src/lib/**`, `src/routes.ts`, `package.json` or any frozen foundation file.

| Group | Screens / CONs | Owned files (create/modify) | Also owns in `src/dev/` | Size |
|---|---|---|---|---|
| **G1 chat-core** | SCR-1 shell: top bar R1, demo bar R2, role-switch row R2b, banner R3, strip + panel R4 ("What's settled"), thread R6 with message rows and event lines, composer R7, pending lines, error/limit/timeout/busy/ended handling, CON-1/2/3/4 plumbing, safety **pinning** | `src/screens/scr01/{index.ts,Scr01.tsx}` + any new file under `src/screens/scr01/core/**`; tests `src/screens/scr01/core/**/*.test.tsx`; `docs/ux/04-prototype/groups/g1-chat-core.md` | `scenarios/scr01-core.ts`, `reactions/scr01-core.ts`, `directors/chat-core.ts`, `stream/chat-scripts.ts` | large |
| **G2 chat-cards** | Every reply block renderer: text with sources + source chip, safety (DANGER/WARNING) card, emergency-line, burning_check, quick_checks, urgency_questions, where_prompt, locate_prompt, code_prompt (4 sub-states), slot_card (day tabs, tiles), account_card, confirmation/appointment/cancelled, change_request, handoff + follow-up chooser (CON-5), live_queued, failure_offer, no_info, notice (rate/booking/spend/timeout/busy/paused), error blocks (SLOT_TAKEN etc.), session_ended | `src/screens/scr01/cards/**` (all files incl. `cards/index.ts`); tests `src/screens/scr01/cards/**/*.test.tsx`; `docs/ux/04-prototype/groups/g2-chat-cards.md` | `scenarios/scr01-cards.ts`, `reactions/scr01-cards.ts`, `directors/chat-cards.ts` | large |
| **G3 demo pages** | SCR-2 inbox, SCR-3 guide and controls (staffing switch, reset dialog), SCR-4 optional `/role` page, SCR-12 login | `src/screens/scr02/**`, `scr03/**`, `scr04/**`, `scr12/**`; `docs/ux/04-prototype/groups/g3-demo-pages.md` | `scenarios/scr02.ts`, `scr03.ts`, `scr04.ts`, `scr12.ts`; `reactions/scr02.ts`, `scr03.ts`, `scr04.ts`, `scr12.ts` | small |
| **G4 staff queue + case** | SCR-5 queue, SCR-6 case (header, split button, lifecycle line, promise card, eight-heading brief, claims card, sources/evidence tabs, live box, action area, activity log, CON-21 stream) | `src/screens/scr05/**`, `scr06/**`; `docs/ux/04-prototype/groups/g4-staff-case.md` | `scenarios/scr05.ts`, `scr06.ts`; `reactions/scr05.ts`, `scr06.ts`; `stream/case-scripts.ts` | large |
| **G5 oversight + reads** | SCR-7 supervisor oversight (alerts, five lanes, demo controls strip, assign/priority dialog), SCR-8 flags, SCR-9 owner outcomes, SCR-10 monitoring, SCR-11 evaluation | `src/screens/scr07/**`, `scr08/**`, `scr09/**`, `scr10/**`, `scr11/**`; intra-group shared pieces (metric tile, definition list, measures table) go in `src/screens/reads/**`; `docs/ux/04-prototype/groups/g5-oversight-reads.md` | `scenarios/scr07.ts` … `scr11.ts`; `reactions/scr07.ts` … `scr11.ts` | medium |

**Seams between groups.**
- G1↔G2: `src/screens/scr01/contract.ts` (types) and `blocks.ts` (renderer registry) are written here and frozen. G1's thread calls `renderBlock()`; G2 fills `cards/index.ts` (`export const cardRenderers: RendererMap`). A missing renderer shows a plain "Unsupported block: {type}" line, so G1 can run before G2 lands.
- G4↔G5: both use the shared `QueueRow` (built here).
- G3↔all: the role switch, sign-out, demo bar and staffing banner are shared components built here; G3 builds the *pages*.

**Shared-primitive requests a group may make** are in §8.3. A group never edits a foundation file; it writes the request in its `groups/gN-*.md` and the integrator decides.

## 3. Requirements table

| # | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| F-01 | UX-4 builds the prototype as the **real frontend in its real folder**, not `prototype/` (phases.md UX-4) | `apps/web/` | `ls apps/web/package.json`; no `prototype/` dir |
| F-02 | React + Vite + TypeScript + shadcn/ui (Radix), Tailwind v4, lucide-react (decision) | Step 1; owned components in `src/components/ui/` in shadcn style (cva + Radix + `cn`) | `npm run build` green; `package.json` deps |
| F-03 | Runs on a **Prism mock of the OpenAPI**, port 4019 (the file's `servers` entry) | `npm run mock` = `prism mock -p ${MOCK_PORT:-4019} -h 127.0.0.1 ../../docs/ux/03-structure/ui-contracts.openapi.yaml` | `curl -s -o /dev/null -w '%{http_code}' -H 'Cookie: mhc_session=x' http://127.0.0.1:4019/api/session` → 200 |
| F-04 | Vite dev on **5184** proxying `/api` to Prism (mock) or to the backend (`dev`) | `vite.config.ts` Step 1 | `npm run dev:mock`, open `http://127.0.0.1:5184`, network tab shows `/api/...` → 4019 |
| F-05 | **Types generated from the OpenAPI** so a contract change breaks the build | `gen:types` + `pretypecheck/prebuild/pretest/predev/predev:mock` regenerate; `check:gen` compares committed files with a fresh generation | Step 2 check: edit a copy of the spec in a scratch dir (not the real file), `check:gen` fails; real run passes |
| F-06 | **Mock-only machinery** (Prefer headers, fake session/login, role-switch fake, state switcher, call log) in a **dev-only layer excluded from production builds**, never inside the client the screens call | `src/dev/**` loaded only by `main.tsx` when `import.meta.env.MODE === "mock"`; ESLint `no-restricted-imports` bans `**/dev/**` outside `src/dev` and `main.tsx`; `scripts/check-dist.mjs` | `npm run build && npm run check:dist` passes (no `__MHC_DEV_LAYER__`, `mhc.dev.`, `Prototype only`, `prototype-synthetic` in `dist/`); `npm run lint` |
| F-07 | **No screen invents data**; a state Prism cannot show is faked in the mock layer or by a named OpenAPI example | Stubs render ids/state names only; `OpForce.transform` + stream scripts live in `src/dev/**`; gaps listed in §8.2 | Review; `src/styles/guard.test.ts` (no literals); §8.2 |
| F-08 | Every screen has a route; one per SCR-1…SCR-12 with the spec'd path (SCREEN_SPECS "Route" lines) | `src/routes.ts` `SCREENS` table + `router.tsx` | `src/routes.test.ts`; `src/screens/stubs.test.tsx` renders all 12 |
| F-09 | **Demo login gates every screen** except `/login` (IA rule, R-48); nothing readable without it; session-ended → SCR-12 with return | `RequireSession` + `onAuthLost`; `safeReturnTo` | `src/state/session.test.tsx`, `src/lib/returnTo.test.ts`, e2e smoke |
| F-10 | **Role switch on every screen after login**, four options, current marked, ticked, "current" in its accessible name, never in a menu, never missing; sign out beside it; `radiogroup` named "Acting as"; ≥ 44 px tall | `RoleSwitch` + `SignOutButton` in `ConsoleHeader` / `DemoPageHeader`; SCR-1 gets `RoleSwitch variant="row"` for G1 | `src/components/shared/RoleSwitch.test.tsx` |
| F-11 | Role switch landings: Customer→SCR-1, Rep→SCR-5, Supervisor→SCR-7, Owner→SCR-9; on SCR-2, SCR-3, SCR-10, SCR-11 the screen stays (IA cross-screen table; SCREEN_SPECS SCR-4 success) | `HOME_BY_ROLE`, `STAY_ON_ROLE_CHANGE` in `src/lib/roles.ts`; `useSession().switchRole` | `src/state/session.test.tsx` |
| F-12 | Staff screen opened as the customer shows "You're acting as the customer. Switch to a staff role to see this." with the switch beside it and **no staff data** (SCREEN_SPECS SCR-4 stale) | `RoleGate` (client check by `roles` on the route) and the same panel for any `ROLE_NOT_ALLOWED` | `src/components/shell/RoleGate.test.tsx`: no `callOp` made for a staff op while role is customer |
| F-13 | Cross-screen link table (IA.md "Cross-screen links", 9 rows) | `LINKS` in `src/routes.ts` | `src/routes.test.ts` (every `to` resolves to a registered route) |
| F-14 | Times are **12-hour** with minutes, lowercase meridiem, en dash with spaces, arrow `→` for headline windows, `<time datetime>`; contracts carry ISO; formatting is the frontend's job (design.md §3.4, §14.5; UX-2 gate condition) | `src/lib/time.ts`, `<Time>` / `<TimeWindow>` | `src/lib/time.test.ts`; `src/test/no24h.ts` helper |
| F-15 | Tokens: 30 colour primitives → 21 semantic → 71 component, plus 16 type, 15 spacing, 7 radius, 7 line, 2 elevation, 10 motion = **179** (design.md header tally), light on `:root`, dark under `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }` and `:root[data-theme="dark"]`, `color-scheme: light dark` | `src/styles/*.css` copied verbatim from design.md | `src/styles/tokens.test.ts` (counts and spot values) |
| F-16 | **Red is the safety card's alone** (§4.5 rule 1: "A lint rule at UX-4 fails the build if any other selector reads `--color-safety`") | guard test + Tailwind default palette removed (`--color-*: initial`) | `src/styles/guard.test.ts` |
| F-17 | No hex in components; components read semantic or component tokens only (§4.5 rule 5) | guard test | `src/styles/guard.test.ts` |
| F-18 | Fonts: Instrument Sans 600/700 (display), Inter 400/500/600 (body), Geist Mono 400/500/600 (refs, codes), self-hosted woff2, `font-display: swap`, OFL texts shipped; `tabular-nums` on `body`; Inter `cv11` (design.md §3.1) | `@fontsource/*` latin CSS imports (bundled woff2, no external request); licences copied to `public/fonts/LICENSES/` | `scripts/check-fonts.py`; Network tab shows no off-origin request; guard test greps for `fonts.googleapis` |
| F-19 | Type scale tokens and the four time styles (§3.2, §3.3); body 15 px on customer screens, 14 px console | `@theme` `--text-*` with `--line-height` companions | `tokens.test.ts` |
| F-20 | Focus ring `2px solid var(--focus-ring)`, offset 2 px, never removed; `scroll-padding-top` = sticky header height; targets 44 px (phone/coarse), 32 px console (design.md §8.2) | `base.css`, `Button`, `Field` | component tests assert classes/roles; Chrome DevTools check Step 12 |
| F-21 | Motion only as opt-in under `prefers-reduced-motion: no-preference`; tokens `--dur-*`, `--ease-*` (§6) | `base.css` | `tokens.test.ts` (motion token presence); manual |
| F-22 | Responsive: chat panel at ≥ 900 px; console 3 columns ≥ 1100 px; queue drawer 700–1099; one column < 700 (IA breakpoints; design §9) | `AppFrame` variants + tokens `--panel-width`, `--col-queue`, `--col-evidence`; groups build the columns | Step 12 DevTools resize at 390 / 800 / 1280 |
| F-23 | **Typed API client** from generated types: `callOp(op, args)` with typed path/query/body/response; named errors; 401 → login; composed errors (HTTP 200) are never thrown | `src/api/client.ts`, `errors.ts` | `src/api/client.test.ts` |
| F-24 | Cookie `mhc_session`; the client sends `credentials: "include"`; the client never writes the cookie | `transport.ts` | `client.test.ts`; guard test (no `document.cookie` outside `src/dev`) |
| F-25 | SSE: `Last-Event-ID` replay, event ids, heartbeat comments ignored (CON-3, CON-21) | `src/api/sse.ts` parser, `transport.openStream`, `useEventStream` | `src/api/sse.test.ts`, `src/api/useEventStream.test.tsx` |
| F-26 | State switcher can force **every spec'd state of every screen** (phases.md; SCREEN_SPECS matrix 12×8: 82 real, 14 n/a) | `src/dev/scenarios/matrix.ts` (the 96 cells), `Scenario` type, panel, coverage test that groups switch on with `complete = true` | `src/dev/scenarios.integrity.test.ts` (matrix counts, ids, ops, examples, routes valid); `scenarios.coverage.test.ts` (for each screen whose file sets `complete`, every real standard state has a scenario) |
| F-27 | **Prism validates every request** with no contract drift (phases.md Done-when) | dev transport reads Prism's `sl-violations` header and 422/problem responses → `CONTRACT_DRIFT` (console error + call log + thrown); `scripts/prism-smoke.mjs` sends every operation × every named example | `npm run smoke:mock` → 0 failures; Playwright smoke fails on any `[contract drift]` console line |
| F-28 | Call log of every request (op, status, example, ms, drift) | `src/dev/calllog.ts` + panel tab + `window.__mhcDev.calls` | `src/dev/calllog.test.ts` |
| F-29 | Fake login/role helpers: any non-empty credentials sign in; sign-out; session-expired; role-reset; refuse-next-login | `src/dev/session-fake.ts` + panel "Session" tab | `src/dev/resolve.test.ts`, e2e smoke |
| F-30 | Role and session emulation Prism cannot do: an op whose `x-roles` excludes the current dev role → 403 `ROLE_NOT_ALLOWED`; signed-out → 401 `UNAUTHENTICATED` | `src/dev/resolve.ts` using `roles` from `contract.gen.json` | `src/dev/resolve.test.ts` |
| F-31 | `getSession` has only CUSTOMER and REPRESENTATIVE examples; supervisor/owner come from the `switchRole` TO_* bodies | `src/dev/session-fake.ts` stores the last `switchRole` body and answers `getSession` from it | `resolve.test.ts` |
| F-32 | Light theme default whatever the system setting; dark secondary (decision, design §7) | `theme.ts` always sets `data-theme` (default `light`); toggle in dev panel; `?theme=` in mock mode | `src/state/theme.test.ts` |
| F-33 | Skip link, landmarks, one `h1` per screen, polite live region helper (SCREEN_SPECS a11y notes) | `AppFrame`, `Main`, `LiveRegion`/`useAnnounce` | stub test asserts one `h1`; e2e axe scan on 12 stubs = 0 violations |
| F-34 | Safe return-to after login (only same-origin relative paths) | `safeReturnTo()` | `src/lib/returnTo.test.ts` |
| F-35 | PROTOTYPE_PLAN.md skeleton: run commands, ports, what is clickable, what is faked, state switcher, contract check, deviations | Step 13 | file exists with the sections listed there |
| F-36 | Production build contains no dev layer | `check-dist.mjs` | `npm run check:dist` |

## 4. Shared code to use (copied from current sources; do not paraphrase)

### 4.1 Ports, URLs and files

| Thing | Value |
|---|---|
| Prism mock | `http://127.0.0.1:4019` (`MOCK_PORT` overrides) |
| Vite dev | `http://127.0.0.1:5184` (`WEB_PORT` overrides), `--strictPort` |
| Real backend (`npm run dev` only) | `http://127.0.0.1:${API_PORT:-8000}` **[A]**, not built yet |
| Taken by other projects (do not use) | 4010/5173 YourAI, 4012/5180 Riverside, 4013/5183 HouseAccount |
| OpenAPI file | `../../docs/ux/03-structure/ui-contracts.openapi.yaml` relative to `apps/web/` |
| Prism command | `prism mock -p 4019 -h 127.0.0.1 <openapi>` (`@stoplight/prism-cli` **5.15.11**, exact pin) |
| Vite proxy | `/api` → target, **no path rewrite** (the spec's paths already start with `/api`); `changeOrigin: true` |
| Auth in the mock | cookie `mhc_session` on every call except `login` (UI_CONTRACTS: "Prism needs the cookie"); value is irrelevant |

### 4.2 Contract facts the code depends on (verified in the OpenAPI file)

- 30 operationIds: `startChatSession getChatThread submitTurn streamChatEvents requestPerson saveFollowUp listDemoInbox getStaffing setStaffing getDemoClock advanceDemoClock resetDemo getQueue getCase applyCaseAction liveChatAction streamCaseEvents recordContactActivity createFlag listFlags reviewFlag getOversight getOwnerMetrics getMonitoring getLatestEval login logout getSession listDemoRoles switchRole`.
- Paths: `/api/chat/sessions` · `/api/chat/sessions/{thread_id}` · `…/turns` · `…/events` (SSE) · `…/handoff` · `…/follow-up` · `/api/demo/{inbox,staffing,clock,reset}` · `/api/staff/queue` · `/api/staff/cases/{reference}` · `…/actions` · `…/live` · `…/events` (SSE) · `…/activities` · `/api/staff/flags` · `/api/staff/flags/{flag_id}` (reviewFlag, PUT) · `/api/staff/oversight` · `/api/staff/owner-metrics` · `/api/monitoring` · `/api/eval/latest` · `/api/login` · `/api/logout` · `/api/session` · `/api/session/roles` · `/api/session/role`.
- `login` has `security: []` (no cookie); every other operation has `mhcSession`. `logout` answers **204**. `startChatSession` answers **201**; `recordContactActivity` and `createFlag` answer **201**.
- Error bodies (HTTP 4xx/5xx): `{"error":{"code","field","constraint","details"},"request_id"}`; named error responses live in `components.responses` (`Unauthenticated` has examples `UNAUTHENTICATED` and `UNAUTHENTICATED_EXPIRED`; `RoleNotAllowed` has `ROLE_NOT_ALLOWED` and `ROLE_NOT_ALLOWED_ROLE_RESET`). **Composed outcomes (SLOT_TAKEN, CODE_WRONG, RATE_LIMITED, TURN_TIMEOUT, BUSY…) are HTTP 200 blocks, never thrown.**
- `x-roles` per operation (entries can carry a trailing note, e.g. `representative (claim, release…)`: normalise with `entry.split(/\s+/)[0]`). Values: chat, demo, session, monitoring, eval ops → all four roles; `advanceDemoClock` supervisor; `getQueue` representative, supervisor; `getCase` representative, supervisor, owner; `applyCaseAction` representative, supervisor; `liveChatAction` representative; `streamCaseEvents` representative, supervisor, owner; `recordContactActivity` representative; `createFlag` representative, supervisor; `listFlags` representative, supervisor, owner; `reviewFlag` supervisor; `getOversight` supervisor; `getOwnerMetrics` owner, supervisor.
- The OpenAPI file uses YAML keys `OFF:` / `ON:` (getStaffing examples). Parse with the npm **`yaml` package v2 (YAML 1.2)**, where they are strings. Never PyYAML (1.1 turns them into booleans).
- `SessionInfo`: `{authenticated: true, role: "customer"|"representative"|"supervisor"|"owner", display_name, sees: string[], signed_in_at}`. `LoginResponse`: `{session: SessionInfo, landing: string}`. `SwitchRoleRequest`: `{role}`. `TurnRequest`: `{turn_id (uuid), payload}`; payload `kind` ∈ `text{text}` | `choice{card_id,option}` | `code{card_id,code}` | `form{card_id,values}`. `FollowUpRequest`: `{channel, destination, window}`. `HandoffRequest`: `{turn_id}`. `CaseActionRequest`: `{action, expected_version, reason?, wake_up_at?, outcome?, assignee?, priority?}`. `LiveActionRequest`: `{action, text?}`. `StartSessionResponse.limits`: `{turn_deadline_ms:60000, still_working_after_ms:10000, browser_give_up_after_ms:65000, max_message_chars:2000}`.
- Time fields are ISO 8601 with offset (demo clock America/Chicago, `-05:00` until Nov 1 2026). Many objects also carry `*_label` strings. **Decision: format every time from the ISO field with `src/lib/time.ts`; use a `*_label` only when its ISO twin is `null` (it then carries words such as "No due time: safety").**

### 4.3 Generated index shape (`src/api/contract.gen.json`, written by `scripts/build-contract-index.mjs`)

Keys sorted, 2-space JSON, trailing newline, byte-identical on re-run.

```json
{
  "source": "docs/ux/03-structure/ui-contracts.openapi.yaml",
  "specVersion": "0.1.0-ux3",
  "operations": {
    "getQueue": {
      "con": "CON-11", "method": "GET", "path": "/api/staff/queue",
      "auth": true, "stream": false,
      "roles": ["representative", "supervisor"],
      "success": [200],
      "responses": [
        { "status": 200, "examples": ["SEEDED", "STAFFED_WITH_WAITING", "ALL_CAUGHT_UP", "BRIEF_BEING_WRITTEN"] },
        { "status": 401, "examples": ["UNAUTHENTICATED", "UNAUTHENTICATED_EXPIRED"] },
        { "status": 403, "examples": ["ROLE_NOT_ALLOWED", "ROLE_NOT_ALLOWED_ROLE_RESET"] }
      ],
      "params": { "path": [], "query": [], "header": [] },
      "requestExamples": {}
    }
  }
}
```
`params.path/query/header` are arrays of `{ "name": string, "example": string|number|null }` (the parameter's `example`). `requestExamples` maps example name → the example `value` (inline JSON body). `success` lists 2xx statuses. `responses` resolves `$ref: "#/components/responses/…"` and lists `application/json` and `text/event-stream` example names (empty array when none). `stream` is true when a 200 response has `text/event-stream` content.

### 4.4 Type helpers (`src/api/client.ts` exports these; write them exactly, adjust only to satisfy `tsc`)

```ts
import type { operations, components } from "./types.gen";
export type OperationId = keyof operations;
export type Role = "customer" | "representative" | "supervisor" | "owner";

type Resp<K extends OperationId> = operations[K]["responses"];
type SuccessStatus = 200 | 201 | 204;
type JsonBody<R> = R extends { content: { "application/json": infer B } } ? B : undefined;
/** The body of the success response (200/201/204) of operation K. */
export type OkBody<K extends OperationId> = {
  [S in keyof Resp<K> & SuccessStatus]: JsonBody<Resp<K>[S]>;
}[keyof Resp<K> & SuccessStatus];
export type ReqBody<K extends OperationId> =
  operations[K] extends { requestBody: { content: { "application/json": infer B } } } ? B
  : operations[K] extends { requestBody?: { content: { "application/json": infer B } } } ? B | undefined
  : undefined;
export type PathParams<K extends OperationId> =
  operations[K] extends { parameters: { path: infer P } } ? P : undefined;
export type QueryParams<K extends OperationId> =
  operations[K] extends { parameters: { query?: infer Q } } ? Q : undefined;
export type CallArgs<K extends OperationId> =
  (PathParams<K> extends undefined ? { path?: never } : { path: PathParams<K> }) &
  (ReqBody<K> extends undefined ? { body?: never } : { body: ReqBody<K> }) &
  { query?: QueryParams<K>; signal?: AbortSignal };

export interface OpMeta {
  con: string; method: "GET" | "POST" | "PUT" | "DELETE"; path: string;
  auth: boolean; stream: boolean; roles: Role[]; success: number[];
  responses: { status: number; examples: string[] }[];
  params: { path: ParamMeta[]; query: ParamMeta[]; header: ParamMeta[] };
  requestExamples: Record<string, unknown>;
}
export interface ParamMeta { name: string; example: string | number | null }
export const OPS: Record<OperationId, OpMeta>;                 // from contract.gen.json
export function callOp<K extends OperationId>(op: K, args?: CallArgs<K>): Promise<OkBody<K>>;
export type ApiErrorBody = components["schemas"]["ApiError"];
```
Reduce `CallArgs` complexity if `tsc` fights it (e.g. make `path`/`body` optional-typed per operation); **correctness of `OkBody<K>`, `ReqBody<K>` and `PathParams<K>` at call sites matters, the exact conditional form does not.** Add a type-level test in `client.test.ts` with `expectTypeOf` (vitest) for `getQueue`, `submitTurn`, `getCase`, `logout`.

### 4.5 Errors and transport (write exactly)

```ts
// src/api/errors.ts
export class ApiError extends Error {
  constructor(
    public readonly status: number,           // 0 = network failure
    public readonly code: string,             // body.error.code, else "NETWORK" | "HTTP_<status>" | "CONTRACT_DRIFT"
    public readonly body: unknown,
    public readonly details: Record<string, unknown> | null = null,
    public readonly requestId: string | null = null,
    public readonly field: string | null = null,
  ) { super(code); }
  get isUnauthenticated() { return this.status === 401 && this.code === "UNAUTHENTICATED"; }
  get isRoleNotAllowed() { return this.status === 403 && this.code === "ROLE_NOT_ALLOWED"; }
}
export function toApiError(e: unknown): ApiError;          // anything thrown by fetch → ApiError(0,"NETWORK",…)

// src/api/transport.ts  (the ONLY file that calls fetch)
export interface CallContext { op: OperationId; method: string; path: string; body?: unknown }
export type StreamStatus = "connecting" | "open" | "reconnecting" | "closed";
export interface StreamSpec {
  op: "streamChatEvents" | "streamCaseEvents";
  path: Record<string, string>;                    // { thread_id } or { reference }
  lastEventId?: number;
  onEvent(data: unknown, id: number | null, eventType: string): void;
  onStatus(status: StreamStatus): void;
}
export interface StreamHandle { close(): void }
export interface ApiTransport {
  fetch(ctx: CallContext, url: string, init: RequestInit): Promise<Response>;
  openStream(spec: StreamSpec): StreamHandle;
}
export const defaultTransport: ApiTransport;       // fetch with credentials: "include"; SSE via fetch + ReadableStream + parseSse, reconnect 1 s→5 s, sends Last-Event-ID, stops on 401/403/404/410
export function setTransport(t: ApiTransport): void;   // called only by src/dev/install.ts
export function getTransport(): ApiTransport;

// src/api/refetch.ts
export function onRefetchAll(cb: () => void): () => void;   // useOp subscribes
export function refetchAll(): void;                          // used on role switch, after reset, by the dev panel
export function onAuthLost(cb: (reason: "none" | "expired") => void): () => void;
export function emitAuthLost(reason: "none" | "expired"): void;   // client.ts calls this on 401 UNAUTHENTICATED (not for login's own 401)
```
`callOp` behaviour, in order: build URL (`encodeURIComponent` every path param; throw `ApiError(0,"MISSING_PARAM",…)` if one is missing; append `?` + `URLSearchParams` for `query`); headers: `Accept: application/json`, plus `Content-Type: application/json` when a body exists; `transport.fetch({op,method,path,body}, url, {method, headers, body: JSON.stringify(body), credentials:"include", signal})`; if `status === 204` return `undefined`; parse JSON (`{}` on parse failure); if `res.ok` return the body; else throw `new ApiError(res.status, body.error?.code ?? "HTTP_"+status, body, body.error?.details ?? null, body.request_id ?? res.headers.get("X-Request-ID"), body.error?.field ?? null)`. On 401 `UNAUTHENTICATED` for any op except `login`, call `emitAuthLost(details.reason === "expired" ? "expired" : "none")` before throwing. Never retry, never read cookies.

### 4.6 Hooks (exact signatures)

```ts
// src/api/useOp.ts
export type OpStatus = "idle" | "loading" | "success" | "error";
export function useOp<K extends OperationId>(
  op: K, args: CallArgs<K> | null,                       // null = do not call (e.g. role not allowed yet)
  opts?: { pollMs?: number; pauseWhenHidden?: boolean; refetchOnFocus?: boolean },
): { data: OkBody<K> | undefined; error: ApiError | undefined; status: OpStatus; isRefetching: boolean; refetch(): Promise<void> };
export function useAction<K extends OperationId>(op: K): {
  run(args?: CallArgs<K>): Promise<OkBody<K>>;           // rejects with ApiError
  pending: boolean; error: ApiError | undefined; data: OkBody<K> | undefined; reset(): void;
};
// src/api/useEventStream.ts
export function useEventStream(spec: Omit<StreamSpec, "onEvent" | "onStatus"> | null,
  onEvent: (data: unknown, id: number | null, type: string) => void): { status: StreamStatus; lastEventId: number | null };
```
`useOp` keys its effect on `op` + `JSON.stringify(args)`; subscribes to `onRefetchAll`; aborts in-flight on unmount; polls with `setTimeout` chain (not `setInterval`) when `pollMs` is set, skipping ticks while `document.visibilityState !== "visible"` when `pauseWhenHidden` (default true); refetches on window `focus` when `refetchOnFocus` (default false). While refetching it keeps `data` and sets `isRefetching`.

### 4.7 UI primitives (`src/components/ui/`, shadcn style: `cva` variants, Radix where the spec asks for ARIA patterns, native elements elsewhere)

All read semantic/component tokens only. Every component forwards `className` (merged with `cn`) and `ref`. Exported from `src/components/ui/index.ts`.

| Component | Props | Notes (design.md ref) |
|---|---|---|
| `Button` | `variant: "primary"\|"secondary"\|"send"\|"text"` (default secondary); `density: "chat"\|"console"` (default chat: 44 px; console: 32 px); `loading?: boolean` (keeps width, disabled, `aria-busy`); `icon?: ReactNode`; native button props | §8.2. 8 px corners, never pills. One primary per card. `send` is the only charcoal button. **No red variant here**: Call 911 is G2's, inside the safety card |
| `Field` | `label: string; hint?: string; error?: string; children: (ids: {id, describedBy, invalid}) => ReactNode` | visible `<label>`; hint under label (13 px muted); invalid = 2 px ink edge + circle-i icon + message, never red; `aria-invalid`, `aria-describedby` |
| `TextInput`, `TextArea` | native props + `invalid?` | well fill, control edge, 44 px (chat) / 32 px (`density="console"`) |
| `Checkbox` | `label`, native props | native `<input type=checkbox>` (used for "Show password"); switch role is G3's, native checkbox with `role="switch"` |
| `Tag` | `tone: "plain"\|"strong"`; `icon?`; children | 6 px corners, filled, 13 px 600; strong = surface-selected fill + 1 px ink edge; **never outlined pill** |
| `Card`, `CardHeader`, `CardBody`, `CardRow` | `CardHeader {icon?, title, hint?, meta?, as?: "h2"\|"h3"\|"h4"}`; `CardRow {label, hint?, children, mono?: boolean}` | §8.4 generic card: hairline, 12 px radius, rail-tone header row, dashed row separators, values right-aligned 600 tabular |
| `Skeleton` | `height: number; width?: number\|string; rows?: number` | static `--color-surface-well` blocks at final height, **no shimmer** |
| `Disclosure` | `summary: ReactNode; children; open?; onOpenChange?; className` | native `<details>`; chevron turns 180° in `--dur-check`; used by the phone strip, source chips, queue drawer |
| `Dialog` | `open; onClose(); title: string; children; initialFocus?: "cancel"\|"first"; labelledBy?` | native `<dialog>` + `showModal()`, `--color-scrim` backdrop, focus returns to the opener on close, Escape closes (SCR-3, SCR-7 a11y notes) |
| `LiveRegion` | `politeness?: "polite"\|"assertive"` (default polite); children | visually hidden container with `aria-live`; plus `useAnnounce(): (msg: string) => void` from `AnnounceProvider` |
| `VisuallyHidden`, `Kbd` | children | `Kbd`: muted 12 px tag |
| `icons.ts` | re-exports from `lucide-react` under project names: `IconBack, IconHeadset, IconCalendar, IconClock, IconTicket, IconCopy, IconCheck, IconWarning, IconDoc, IconChevron, IconInfo, IconPhone, IconQuestion, IconQuote, IconUser, IconSignOut` | **one set, 14–18 px, 1.8 stroke, `currentColor`; never emoji** |

### 4.8 Shared components (`src/components/shared/` and `src/components/shell/`; used by two or more groups)

| Component | Props | Used by |
|---|---|---|
| `Time` | `iso: string\|null; format: "point"\|"short"\|"staff"\|"day"\|"sentence"\|"clock"; variant?: "hero"\|"due"\|"row"\|"meta"; fallback?: string` | all |
| `TimeWindow` | `startIso: string; endIso: string; arrow?: boolean; variant?: "hero"\|"due"\|"row"\|"meta"` | G1, G2, G4 |
| `RefChip` | `reference: string; copyable?: boolean` (mono `--text-ref`, copy icon, copy announces "Copied") | G1, G2, G4, G5 |
| `AssistantMark` | `size?: 18\|24\|30` (grey well, hairline, emerald glyph; **never a face**) | G1, G2, G4 |
| `PersonDisc` | `initial: string; size?: 18\|32` (indigo) | G1, G4, console header |
| `SpeakerLine` | `speaker: components["schemas"]["Speaker"]; at?: string; align?: "left"\|"right"` (name 600, " · " + rest muted + `<Time format="point" variant="meta">`) | G1, G4 |
| `MessageRow` | `speaker; at; layout: "bubble"\|"flat"; children` (assistant grey / customer **mint** / representative white + hairline; 4 px tip corner; `flat` = unbubbled transcript for SCR-6) | G1, G4 |
| `EventLine` | `icon?: ReactNode; at?: string; children` (centred between two `--event-line` hairlines; hidden "System event" prefix for screen readers) | G1, G4 |
| `RoleSwitch` | `variant?: "segmented"\|"row"` (row = SCR-1's own 44 px row) | every screen |
| `SignOutButton` | none (text button; calls `useSession().signOut()`) | every screen |
| `DemoBar` | none (reads `useDemoStatus()`; "Fri Oct 16, 2026 (demo date) · Nobody online"; 12 px centred grey strip; no icon, no amber) | G1, G3, console |
| `StaffingBanner` | none (renders only when `staffing.mode === "simulated_on_shift"`; circle-i icon; "Simulated staffing (demo). No Meridian employee is online.") | G1, console |
| `ConsoleHeader` | none (brand "Meridian · Staff console", role line with `PersonDisc`, demo date + time, staffing word, `StaffingBanner`, nav by role, `RoleSwitch`, `SignOutButton`) | G4, G5 |
| `DemoPageHeader` | `title: string; subtitle?: string; showDemoBar?: boolean` (+ `RoleSwitch`, `SignOutButton`) | G3, G5 (SCR-10/11) |
| `AppFrame` | `variant: "chat"\|"console"\|"page"\|"auth"; children` (canvas + 24 px frame, `--elev-frame`, skip link "Skip to main content", max widths: chat 1200 px, console 1440 px, page 960 px, auth 440 px) | all |
| `Main` | `children; id?: "main"` (`<main id="main" tabIndex={-1}>`) | all |
| `RoleGate` | `allow: Role[]; children` (renders the F-12 panel when the current role is not allowed; renders children and nothing else otherwise) | G4, G5 (and stubs) |
| `RoleNotAllowedPanel` | `role: Role; allow: Role[]` | `RoleGate`, any `ROLE_NOT_ALLOWED` response |
| `ErrorLine` | `message: string; onRetry?: () => void` (e.g. "The queue didn't load. Try again." + secondary button; `role="alert"` is **not** used: errors are polite) | G3, G4, G5 |
| `EmptyState` | `title: string; body?: string; action?: ReactNode` | G3, G4, G5 |
| `StaleLine` | `children; actionLabel?: string; onAction?()` (polite line, e.g. "2 cases changed. Show them.") | G1, G4, G5 |
| `ResultLine` | `children; id?` (polite result line, focus target after an action) | G3, G4, G5 |
| `QueueRow` | `row: components["schemas"]["QueueRow"]; selected?: boolean; showStaffTags?: boolean; onSelect?(reference): void; href?: string` (see below) | G4 (SCR-5, SCR-6 rail), G5 (SCR-7 lanes) |
| `PriorityTag` | `priority: components["schemas"]["Priority"]` ("P0 · Safety", "P1 · Danger" strong with warning icon in ink; P2–P4 plain; word always beside code) | G4, G5 |

**`QueueRow` exact behaviour (design.md §8.8, SCREEN_SPECS SCR-5):** `<button>` (or `<a href>` when `href` is given) in a list item, min 44 px high, grid `1fr auto`. Line 1: `row.reason` (600) + `PriorityTag`. Line 2 (`--text-time-meta`, muted): `{customer_display_name} · <RefChip> · ` then, if `due_state === "no_due_time"` the words "No due time: safety", else `Due <Time format="short" iso={due_at}>` (if `due_at` is null use `due_label`). If `due_state === "overdue"` add a strong `Tag` "Overdue" with the clock icon (never red, never a countdown). Line 3 when it applies: owner ("Unowned" when `owner` is null) · `follow_up_short` · tags "Demo seed" (`seed`), "Brief being written" (`brief_status === "being_written"`), and for `lifecycle === "waiting"` "Waiting · wakes <Time format="staff" iso={wake_up_at}>". Selected = `--qrow-selected-bg` + 1 px `--qrow-selected-edge`, `aria-current="true"`. **Accessible name, in this order:** `"{level} {word lowercased}, {reference}, {reason lowercased as given}, {owner or 'unowned'}, {due text}"`, e.g. `P0 safety, MHC-C-0008, gas smell reported in chat, unowned, no due time: safety` (SCREEN_SPECS SCR-5 a11y note).

### 4.9 Frozen interfaces written by this slice

**`src/routes.ts`**

```ts
import type { Role } from "@/lib/roles";
export type ScreenId = "SCR-1"|"SCR-2"|"SCR-3"|"SCR-4"|"SCR-5"|"SCR-6"|"SCR-7"|"SCR-8"|"SCR-9"|"SCR-10"|"SCR-11"|"SCR-12";
export interface ScreenDef { id: ScreenId; slug: string; path: string; title: string; roles: Role[]; frame: "chat"|"console"|"page"|"auth"; public?: boolean; group: "G1"|"G2"|"G3"|"G4"|"G5" }
export const ALL: Role[] = ["customer","representative","supervisor","owner"];
export const SCREENS: ScreenDef[] = [
  { id:"SCR-1",  slug:"scr01", path:"/",                          title:"Customer chat",          roles:ALL,                             frame:"chat",    group:"G1" },
  { id:"SCR-2",  slug:"scr02", path:"/demo/inbox",                title:"Demo delivery inbox",    roles:ALL,                             frame:"page",    group:"G3" },
  { id:"SCR-3",  slug:"scr03", path:"/demo",                      title:"Demo guide and controls",roles:ALL,                             frame:"page",    group:"G3" },
  { id:"SCR-4",  slug:"scr04", path:"/role",                      title:"Role switch",            roles:ALL,                             frame:"page",    group:"G3" },
  { id:"SCR-5",  slug:"scr05", path:"/staff/queue",               title:"Representative queue",   roles:["representative","supervisor"],  frame:"console", group:"G4" },
  { id:"SCR-6",  slug:"scr06", path:"/staff/cases/:reference",    title:"Case view",              roles:["representative","supervisor","owner"], frame:"console", group:"G4" },
  { id:"SCR-7",  slug:"scr07", path:"/staff/oversight",           title:"Supervisor oversight",   roles:["supervisor"],                   frame:"console", group:"G5" },
  { id:"SCR-8",  slug:"scr08", path:"/staff/flags",               title:"Review list of flags",   roles:["representative","supervisor","owner"], frame:"console", group:"G5" },
  { id:"SCR-9",  slug:"scr09", path:"/staff/owner",               title:"Business-owner outcomes",roles:["owner","supervisor"],           frame:"console", group:"G5" },
  { id:"SCR-10", slug:"scr10", path:"/monitoring",                title:"Monitoring",             roles:ALL,                             frame:"page",    group:"G5" },
  { id:"SCR-11", slug:"scr11", path:"/eval",                      title:"Evaluation report",      roles:ALL,                             frame:"page",    group:"G5" },
  { id:"SCR-12", slug:"scr12", path:"/login",                     title:"Demo login",             roles:ALL,                             frame:"auth",    group:"G3", public:true },
];
export function caseHref(reference: string): string;   // "/staff/cases/" + encodeURIComponent(reference)
export interface LinkDef { from: string[]; action: string; to: string; newTab?: boolean }
export const LINKS: LinkDef[];                         // the 9 rows below
```

`LINKS` (copy from IA.md "Cross-screen links"; `to` uses a `ScreenId`, `"role-home"`, `"asked-for-else-SCR-1"`, `"previous-else-SCR-5"` or `"SCR-6"` as the literal strings shown):

| from | action | to |
|---|---|---|
| SCR-1 | "Demo guide" | SCR-3 |
| SCR-1 code card | "Open the demo inbox" | SCR-2 (newTab: true) |
| any | Role switch: Customer | SCR-1 |
| any | Role switch: Representative / Supervisor / Owner | role-home (SCR-5 / SCR-7 / SCR-9; stays on SCR-2, SCR-3, SCR-10, SCR-11) |
| SCR-12 | Sign in | asked-for-else-SCR-1 |
| any | Session ended | SCR-12 |
| any | Sign out | SCR-12 |
| SCR-5, SCR-7, SCR-8, SCR-9 | Open a case | SCR-6 |
| SCR-9, SCR-3 | Monitoring, Evaluation | SCR-10, SCR-11 |
| SCR-6 | Back to queue | previous-else-SCR-5 |

**`src/lib/roles.ts`**

```ts
export type Role = "customer"|"representative"|"supervisor"|"owner";
export const ROLES: readonly Role[] = ["customer","representative","supervisor","owner"];
export const ROLE_LABEL: Record<Role,{ short: string; phone: string; full: string }> = {
  customer:       { short:"Customer",       phone:"Customer",   full:"Customer (demo)" },
  representative: { short:"Representative", phone:"Rep",        full:"Riley, demo representative" },
  supervisor:     { short:"Supervisor",     phone:"Supervisor", full:"Demo supervisor" },
  owner:          { short:"Owner",          phone:"Owner",      full:"Demo business owner" },
};   // runtime display names still come from getSession / listDemoRoles; these are the phone/short labels and test fallbacks
export const HOME_BY_ROLE: Record<Role,string> = { customer:"/", representative:"/staff/queue", supervisor:"/staff/oversight", owner:"/staff/owner" };
export const STAY_ON_ROLE_CHANGE: readonly string[] = ["/demo/inbox","/demo","/monitoring","/eval"];
export const CONSOLE_NAV: Record<Exclude<Role,"customer">,{ label: string; to: string }[]> = {
  representative: [{label:"Queue",to:"/staff/queue"},{label:"Review list",to:"/staff/flags"}],
  supervisor:     [{label:"Oversight",to:"/staff/oversight"},{label:"Review list",to:"/staff/flags"},{label:"Queue",to:"/staff/queue"}],
  owner:          [{label:"Outcomes",to:"/staff/owner"},{label:"Review list",to:"/staff/flags"}],
};   // owner's nav is a decision of this plan (IA gives none); supervisor and representative come from SCREEN_SPECS SCR-7 R1 / SCR-5 R1
```

**`src/state/session.tsx`**

```ts
export interface SessionApi {
  status: "loading" | "ready" | "signed-out";
  session: components["schemas"]["SessionInfo"] | null;
  role: Role | null;
  switching: Role | null;                 // the role being switched to; all four segments disabled while non-null
  switchError: string | null;             // "Couldn't switch role. Try again."
  switchRole(role: Role): Promise<void>;  // PUT /api/session/role; on success set session, refetchAll(), navigate per HOME_BY_ROLE / STAY_ON_ROLE_CHANGE
  signOut(): Promise<void>;               // POST /api/logout then navigate to /login
  setSession(s: SessionInfo): void;       // used by login screen (G3) after a successful login
}
export function SessionProvider(props: { children: ReactNode }): JSX.Element;
export function useSession(): SessionApi;
```
On mount: `callOp("getSession")`. 401 → `status: "signed-out"` and navigate to `/login?return_to=<current path+search>&reason=none|expired`. `onAuthLost` does the same from any later call. `switchRole` announces `Now acting as {session.display_name}` through `useAnnounce`. `ROLE_NOT_ALLOWED` with `details.reason === "role_reset"` is shown by `RoleNotAllowedPanel` as "The demo was reset, so you're back to the customer role. Pick a role again." (CON-10).

**`src/state/demoStatus.tsx`**: `DemoStatusProvider`, `useDemoStatus(): { clock: DemoClock|null; staffing: Staffing|null; refresh(): Promise<void>; setFromChat(next: Partial<{clock: DemoClock; staffing: Staffing}>): void; setSource(src: "poll"|"chat"): void }`. Reads `getDemoClock` and `getStaffing` on mount, on window focus and every 10 s while visible (`source === "poll"`); when G1's chat sets `source = "chat"` the poll stops and the chat pushes values from CON-1/CON-3. `refetchAll()` also refreshes.

**Chat contract (frozen), `src/screens/scr01/contract.ts`**

```ts
import type { ReactNode } from "react";
import type { components } from "@/api/types.gen";
export type ReplyBlock = components["schemas"]["ReplyBlock"];
export type Settled = components["schemas"]["Settled"];
export type BlockType = ReplyBlock["type"];
export type BlockOf<T extends BlockType> = Extract<ReplyBlock, { type: T }>;
export type ChatAction =
  | { kind: "text"; text: string }
  | { kind: "choice"; cardId: string; option: string }
  | { kind: "code"; cardId: string; code: string }
  | { kind: "form"; cardId: string; values: Record<string, string> }
  | { kind: "person" }                                           // CON-4 requestPerson
  | { kind: "followUp"; channel: "email"|"phone"; destination: "on_record"|"general"; window: "morning"|"afternoon"|"any" }   // CON-5
  | { kind: "retry"; turnId: string }                            // "Try again" reuses the same turn_id
  | { kind: "newChat" };
export interface BlockProps<T extends BlockType> {
  block: BlockOf<T>; settled: Settled | null;
  answered: boolean;                    // this card already received its answer (buttons disabled, choice kept)
  disabled: boolean;                    // chat ended / pending
  dispatch(action: ChatAction): Promise<void>;
  announce(message: string): void;      // polite region
  landed(target: "visit" | "request" | "identity"): void;   // mint wash on the matching panel block (not under reduced motion)
}
export type BlockRenderer<T extends BlockType> = (props: BlockProps<T>) => ReactNode;
export type RendererMap = { [T in BlockType]?: BlockRenderer<T> };
```
`src/screens/scr01/blocks.ts` exports `renderBlock(props: BlockProps<BlockType>): ReactNode` which looks up `cardRenderers[block.type]` (imported from `./cards`) and returns `<p>Unsupported block: {type}</p>` (neutral, 13 px muted) when missing. `src/screens/scr01/cards/index.ts` in this slice: `export const cardRenderers: RendererMap = {};`.

**Dev-layer interfaces (frozen), `src/dev/scenarios/types.ts`**

```ts
import type { OperationId, Role } from "@/api/client";
import type { ScreenId } from "@/routes";
export type StandardState = "default"|"empty"|"loading"|"partial"|"error"|"stale"|"success"|"disabled";
export type OpForce =
  | { example: string; status?: number; delayMs?: number; transform?: (body: any) => any }   // status only to disambiguate a name that exists under two statuses
  | { fail: "network"; delayMs?: number }                  // fetch rejects → ApiError(0,"NETWORK")
  | { hang: true }                                         // never resolves (loading state, 65 s give-up)
  | { sequence: OpForce[] };                               // consumed one per call; the last entry repeats
export interface Scenario {
  id: string;                 // `${slug}.${kebab}` e.g. "scr05.empty"; unique
  screen: ScreenId | "*";     // "*" only for the shared.* scenarios that work on any screen
  state: StandardState;       // which cell of the 12×8 matrix this shows
  flowState?: string;         // exact first-column text of the SCREEN_SPECS flow-state table, when it is one
  label: string;              // shown in the panel
  route: string;              // concrete path, e.g. "/staff/cases/MHC-C-0007"
  role?: Role;                // default: first role in the screen's `roles`
  staffing?: "nobody_online" | "simulated_on_shift";
  ops?: Partial<Record<OperationId, OpForce>>;
  stream?: StreamScript;      // see src/dev/stream/types.ts
  notes?: string;             // how it is reached when it is not a pure forced response
}
export interface ScreenScenarios { complete?: boolean; scenarios: Scenario[] }   // each src/dev/scenarios/<slug>.ts: `export const screenScenarios: ScreenScenarios`
export interface Reaction {                                      // src/dev/reactions/<slug>.ts: `export const reactions: Reaction[]`
  when: { op: OperationId; status?: number; example?: string };
  then(ctx: DevCtx): void;
}
export interface DevCtx {
  world: World;                                  // read-only snapshot
  setForce(op: OperationId, force: OpForce | null): void;
  setRole(role: Role): void;
  setStaffing(mode: "nobody_online" | "simulated_on_shift"): void;
  emit(thread: string, event: unknown): void;   // push a typed chat/case event into the scripted stream
  refetch(): void;                               // refetchAll()
}
export interface DirectorRule { (req: components["schemas"]["TurnRequest"], ctx: ChatDirectorCtx): string | undefined }  // returns a submitTurn example name; src/dev/directors/<name>.ts: `export const rules: DirectorRule[]`
```
The `World` type and `StreamScript` are defined by the implementer in `world.ts` and `stream/types.ts` (Step 11). `src/dev/scenarios/matrix.ts` exports `MATRIX: Record<ScreenId, Record<StandardState, { real: true } | { real: false; reason: string }>>` (data in §6.3).

## 5. Steps (build order; each step ends with its check)

Work in `apps/web/`. Run commands from there unless a path says otherwise. Check Node first: `node -v` must print v24.x (v24.21.0 on this VPS), `npm -v` ≥ 11. Disk: `df -h /home` must show ≥ 3 GB free before `npm install`.

### Step 0 · Preflight
1. Confirm `apps/web/` does not exist; `mkdir -p apps/web`. Confirm ports 4019 and 5184 are free (`ss -ltn | grep -E ':(4019|5184)\b'` prints nothing). If a port is taken by a process you did not start, stop and report (do not kill it).
2. `mkdir -p docs/ux/04-prototype/groups`.
**Check:** both dirs exist.

### Step 1 · Package scaffold
Create `apps/web/package.json` (`"type": "module"`, `"private": true`, `"name": "meridian-web"`). **Scripts (exact):**

```json
{
  "dev": "vite --host 127.0.0.1 --port ${WEB_PORT:-5184} --strictPort",
  "dev:mock": "vite --mode mock --host 127.0.0.1 --port ${WEB_PORT:-5184} --strictPort",
  "mock": "prism mock -p ${MOCK_PORT:-4019} -h 127.0.0.1 ../../docs/ux/03-structure/ui-contracts.openapi.yaml",
  "gen:types": "openapi-typescript ../../docs/ux/03-structure/ui-contracts.openapi.yaml -o src/api/types.gen.ts",
  "examples": "node scripts/build-contract-index.mjs",
  "check:gen": "node scripts/check-generated.mjs",
  "check:dist": "node scripts/check-dist.mjs",
  "smoke:mock": "node scripts/prism-smoke.mjs",
  "typecheck": "tsc -b --noEmit",
  "lint": "eslint .",
  "test": "vitest run",
  "test:e2e": "playwright test",
  "build": "tsc -b && vite build",
  "pretypecheck": "npm run gen:types && npm run examples",
  "pretest": "npm run gen:types && npm run examples",
  "prebuild": "npm run gen:types && npm run examples",
  "predev": "npm run gen:types && npm run examples",
  "predev:mock": "npm run gen:types && npm run examples"
}
```
**Dependencies** (install with `npm install`; pin the exact ones, take the newest compatible for the rest and record resolved versions in `README.md`):
- runtime: `react@^19.1`, `react-dom@^19.1`, `react-router@^7` (imports: `createBrowserRouter`, `createMemoryRouter` from `"react-router"`, `RouterProvider` from `"react-router/dom"`; if `tsc` disagrees with that split use the package's documented import for the installed version), `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`, `@radix-ui/react-slot`, `@radix-ui/react-tabs`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-radio-group`, `@fontsource/instrument-sans`, `@fontsource/inter`, `@fontsource/geist-mono`.
- dev: `vite@^6.3.5`, `@vitejs/plugin-react@^4.5`, `tailwindcss@^4.1.8`, `@tailwindcss/vite@^4.1.8`, `typescript@~5.8.3`, `openapi-typescript@7.13.0`, `yaml@^2`, `@stoplight/prism-cli@5.15.11`, `vitest@3.2.7`, `jsdom@26.1.0`, `@testing-library/react@16.3.3`, `@testing-library/dom@10.4.2`, `@testing-library/user-event@14.6.8`, `@types/react`, `@types/react-dom`, `@types/node`, `eslint@9.39.5`, `@eslint/js@9.39.5`, `typescript-eslint@8.72.0`, `eslint-plugin-react-hooks@5.2.0`, `globals@16.5.0`, `@playwright/test@^1.64.1`, `@axe-core/playwright@^4.10.1`.
- `components.json` (shadcn pointer, so a later `npx shadcn add` knows the aliases; do **not** run the CLI): `{ "$schema": "https://ui.shadcn.com/schema.json", "style": "new-york", "rsc": false, "tsx": true, "tailwind": { "config": "", "css": "src/styles/index.css", "baseColor": "neutral", "cssVariables": true }, "aliases": { "components": "@/components", "ui": "@/components/ui", "utils": "@/lib/cx", "lib": "@/lib", "hooks": "@/api" } }`.

`tsconfig.json`: copy Riverside's (`target ES2022`, `lib ES2022 DOM DOM.Iterable`, `module ESNext`, `moduleResolution bundler`, `jsx react-jsx`, `strict`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`, `skipLibCheck`, `isolatedModules`, `resolveJsonModule`, `types ["vite/client"]`, `noEmit`), add `"baseUrl": "."`, `"paths": { "@/*": ["src/*"] }`, `include: ["src", "tests", "playwright.config.ts", "vite.config.ts"]` (the `scripts/*.mjs` files are plain JavaScript and stay out).

`vite.config.ts`:
```ts
/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";
export default defineConfig(({ mode }) => {
  const mock = mode === "mock";
  const target = mock ? `http://127.0.0.1:${process.env.MOCK_PORT ?? "4019"}` : `http://127.0.0.1:${process.env.API_PORT ?? "8000"}`;
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: { proxy: { "/api": { target, changeOrigin: true } } },
    test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"], include: ["src/**/*.test.{ts,tsx}"], restoreMocks: true },
  };
});
```
`eslint.config.js`: Riverside's flat config (ignore `dist/`, `node_modules/`, `test-results/`, `playwright-report/`, `src/api/types.gen.ts`; `js.configs.recommended` + `tseslint.configs.recommended`; react-hooks rules; `no-unused-vars` with `argsIgnorePattern: "^_"`), **plus**:
- `files: ["src/**/*.{ts,tsx}"]`, `ignores: ["src/dev/**", "src/main.tsx", "src/**/*.test.{ts,tsx}"]` → `no-restricted-imports` pattern `{ group: ["**/dev/**", "@/dev/**"], message: "The dev-only layer is imported only by src/main.tsx" }`.
- `files: ["src/**/*.{ts,tsx}"]`, `ignores: ["src/api/transport.ts", "src/dev/**", "src/**/*.test.{ts,tsx}"]` → `no-restricted-globals: ["error", { name: "fetch", message: "Use callOp / useOp / useAction" }]`.
- `files: ["src/**/*.{ts,tsx}"]`, `ignores: ["src/dev/**", "src/**/*.test.{ts,tsx}"]` → `no-restricted-syntax` banning `MemberExpression[object.name="document"][property.name="cookie"]` ("Cookies are set by the server; the dev layer fakes it").

`.gitignore`: `node_modules`, `dist`, `test-results`, `playwright-report`, `.tmp`. (Generated `types.gen.ts` and `contract.gen.json` are **committed**; they are also regenerated by the pre-hooks.)
`index.html`: `<!doctype html><html lang="en">`, charset, viewport, `<title>Meridian Home Comfort</title>`, `<div id="root">`, `<script type="module" src="/src/main.tsx">`.
**Check:** `npm install` exits 0; `npx tsc -v`; `npx vite --version`; `npx prism --version` prints 5.15.11.

### Step 2 · Contract tooling and generated files
1. `scripts/paths.mjs`: exports `SPEC` (absolute path to the OpenAPI file, resolved from `import.meta.url`), `TYPES_OUT`, `INDEX_OUT`.
2. `scripts/build-contract-index.mjs`: read `SPEC`, `yaml.parse` (v2, YAML 1.2). Walk `paths`; for each operation (`get/post/put/delete`) write the §4.3 shape. Resolve `$ref` strings starting with `#/` by walking the parsed doc. Roles: `x-roles` array → `split(/\s+/)[0]` each; missing → all four. `auth = !(Array.isArray(op.security) && op.security.length === 0)`. Examples: names of `content["application/json"].examples` and `content["text/event-stream"].examples`. Param `example`: the parameter's `example` key or `null`. `requestExamples`: `requestBody.content["application/json"].examples[name].value`. Sort every object's keys alphabetically (operation ids too) and write `src/api/contract.gen.json` with `JSON.stringify(obj, null, 2) + "\n"`. Print `contract index: 30 operations`. Exit 1 if the count is not 30 (the spec says 30).
3. `scripts/check-generated.mjs`: run `openapi-typescript` (via `execFileSync("npx", ["openapi-typescript", SPEC, "-o", ".tmp/types.check.ts"])`) and the index builder with an `--out .tmp/contract.check.json` flag; compare bytes to `src/api/types.gen.ts` and `src/api/contract.gen.json`; exit 1 with a message naming the stale file. (The builder therefore takes an optional `--out` path.)
4. Run `npm run gen:types && npm run examples`.
**Check:** both generated files exist; `npm run check:gen` exits 0; `node -e "const c=require('./src/api/contract.gen.json');console.log(Object.keys(c.operations).length, c.operations.getStaffing.responses[0].examples)"` prints `30 [ 'OFF', 'ON' ]`.

### Step 3 · Tokens, theme, fonts, base CSS
Copy values **verbatim** from design.md; never retype a hex by memory.

1. `src/styles/tokens.css` (plain `:root` custom properties, no Tailwind): the 30 colour **primitives** (§4.1), the 71 **component tokens** (§8.0; `--target-min: 44px` etc. as listed; `--btn-primary-split-rule: color-mix(in srgb, var(--color-on-accent) 35%, transparent)`), 15 **spacing** (§5.1 `--space-0-5 … --space-16`), 7 **line** tokens (§5.4, e.g. `--line-hair: 1px solid var(--color-border-hair)`), 2 **elevation** tokens (§5.5; light values on `:root`), the 10 **motion** tokens (§6: `--dur-control:150ms; --dur-fade:200ms; --dur-check:160ms; --dur-landed-in:160ms; --dur-landed-hold:640ms; --dur-landed-out:400ms; --delay-pending:300ms; --ease-enter:cubic-bezier(0,0,.58,1); --ease-exit:cubic-bezier(.42,0,1,1); --ease-move:cubic-bezier(.42,0,.58,1)`).
2. `src/styles/theme.css`:
   ```css
   @import "tailwindcss";
   @theme static {
     --color-*: initial;   /* removes Tailwind's default palette: no red/amber/orange utilities exist */
     /* 21 semantic colours, light values referencing primitives, exactly the §4.2 table (--color-canvas … --color-scrim) */
     /* radius: --radius-frame --radius-card --radius-control --radius-tag --radius-tip --radius-sharp --radius-round */
     /* type: --text-caption: 12px; --text-caption--line-height: 16px; … for the 12 tokens of §3.2 and the 4 time styles of §3.3 */
     --font-display: "Instrument Sans", "Helvetica Neue", Arial, sans-serif;
     --font-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
     --font-mono: "Geist Mono", ui-monospace, Menlo, monospace;
   }
   ```
   `--radius-*` and `--text-*` use Tailwind's own namespaces, so `rounded-card`, `text-body`, `text-time-hero` exist. Letter-spacing/weight/family for the type tokens that need them (`--text-section`, `--text-signal`, `--text-code`) go in `@layer components` classes `.t-section`, `.t-signal`, `.t-code`, `.t-ref`, `.t-lead`, `.t-title`, `.t-card-title`, `.t-name`, `.t-time-hero|due|row|meta` in `base.css` (family, weight, tracking from §3.2/§3.3; `.t-section` and `.t-signal` are the **only** uppercase classes and are never applied to a `<Time>`).
3. `src/styles/dark.css`: the §4.2 dark column and the dark `--elev-popover`, under the two selectors from F-15 (`@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { … } }` and `:root[data-theme="dark"] { … }`), `color-scheme` set on `:root` as `light dark`.
4. `src/styles/fonts.css`: `@import "@fontsource/instrument-sans/latin-600.css"; …/latin-700.css; @fontsource/inter/latin-400.css, latin-500.css, latin-600.css; @fontsource/geist-mono/latin-400.css, latin-500.css, latin-600.css`. (Local woff2 bundled by Vite; `font-display: swap` comes from the packages.)
5. `src/styles/base.css`: `body { font-family: var(--font-body); font-size: 15px; line-height: 22px; color: var(--color-text); background: var(--color-canvas); font-variant-numeric: tabular-nums; font-feature-settings: 'cv11'; -webkit-font-smoothing: antialiased }`; `h1,h2,h3 { text-wrap: balance }`, `p { text-wrap: pretty }`; focus ring `:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px }`; `html { scroll-padding-top: var(--sticky-offset, 0px) }`; hover rule only inside `@media (hover: hover)`; all transitions only inside `@media (prefers-reduced-motion: no-preference)`; `.sr-only`.
6. `src/styles/index.css`: `@import "./fonts.css"; @import "./tokens.css"; @import "./theme.css"; @import "./dark.css"; @import "./base.css";` (order matters: tokens before theme).
7. `src/state/theme.ts`: `applyTheme(): void` sets `document.documentElement.dataset.theme` to `localStorage["mhc.theme"]` if it is `"light"` or `"dark"`, else `"light"` (light default whatever the system setting); `setTheme(t)`.
8. `scripts/copy-font-licenses.mjs` copies each family's `LICENSE` from `node_modules/@fontsource/<name>/` to `public/fonts/LICENSES/<name>-OFL.txt`; run it once and keep the three files. `scripts/check-fonts.py` (run with `uv run --no-project --with fonttools --with brotli python -I scripts/check-fonts.py`): open the installed `latin-400`/`600` woff2 files and print whether GSUB has `tnum` (all three families) and `cv11` (Inter); exit 0 always, print `MISSING tnum <family>` lines.
9. Tests: `src/styles/tokens.test.ts` — read the four CSS files as text; assert the **category counts** (30 colour primitives, 21 semantic colours, 71 component tokens, 16 type, 15 spacing, 7 radius, 7 line, 2 elevation, 10 motion = 179), ignoring `--text-*--line-height` companions and the `--color-*: initial` line; assert spot values: `--color-canvas` light `#E5E9F0` (via `--cool-100`) and dark `#0B0F12`; `--color-accent` `#007847`/`#00BC6F`; `--color-safety` `#B42318`/`#C8312F`; `--emerald-700: #007847`; `--panel-width: 340px`; `--col-queue: 280px`; `--col-evidence: 300px`. `src/styles/guard.test.ts` — walk `src/**/*.{ts,tsx,css}` and fail on: (a) `--color-safety|--color-on-safety|--safety-|--focus-ring-on-safety|radius-sharp|bg-safety|text-safety|border-safety` in any file **outside** `src/styles/` and files whose path matches `/^src\/screens\/scr01\/cards\/.*[Ss]afety/`; (b) a hex literal `#[0-9a-fA-F]{3,8}\b` in `src/components/**` or `src/screens/**` (tests and `src/dev/**` excluded); (c) the words `red-`, `amber`, `orange` as Tailwind classes in `src/components/**` or `src/screens/**`; (d) `fonts.googleapis|fonts.gstatic|cdn\.` anywhere; (e) the string literals `"Prefer"` / `'Prefer'` or `mhc_session=` outside `src/dev/**` and test files.
**Check:** `npx vitest run src/styles` green. If `check-fonts.py` prints `MISSING tnum …` for a family, keep going, note it under *Known deviations* in PROTOTYPE_PLAN and report it (do not switch fonts).

### Step 4 · Libraries
- `src/lib/cx.ts`: `export function cn(...inputs: ClassValue[]): string { return twMerge(clsx(inputs)); }`.
- `src/lib/ids.ts`: `newTurnId(): string` (`crypto.randomUUID()` with a v4 fallback).
- `src/lib/returnTo.ts`: `safeReturnTo(value: string | null | undefined): string` returns `value` only when it matches `/^\/(?![\/\\])/` (starts with a single `/`, not `//` or `/\`) and contains no `\n` or `\r`; otherwise `"/"`. Test: `"/staff/queue"` ok, `"//evil.com"`, `"https://x"`, `"/\\evil"`, `null` → `"/"`.
- `src/lib/time.ts` (America/Chicago via `Intl.DateTimeFormat(..., { timeZone: "America/Chicago" })` and `formatToParts`; **assemble the string from parts**, because newer ICU puts U+202F before AM/PM and capitalises it):
  ```ts
  export const DEMO_TZ = "America/Chicago";
  export function formatTimePoint(iso: string): string;               // "7:00 pm", "12:00 pm", "12:00 am"
  export function formatTimeRange(startIso: string, endIso: string): string;       // "8:00 am – 12:00 pm"  (en dash U+2013 with spaces)
  export function formatTimeRangeArrow(startIso: string, endIso: string): string;  // "8:00 am → 12:00 pm"  (U+2192)
  export function formatDateTimeShort(iso: string): string;           // "Mon Oct 19 · 7:00 pm"  (middle dot U+00B7)
  export function formatStaffTime(iso: string): string;               // "Mon 7:00 pm"
  export function formatDayShort(iso: string): string;                // "Wed Oct 21"
  export function formatDayLong(iso: string): string;                 // "Wednesday, October 21, 2026"
  export function formatSentence(iso: string): string;                // "Monday, October 19, 7:00 pm"
  export function formatClockLabel(iso: string): string;              // "Fri Oct 16 · 2:20 pm"
  export function formatDemoDate(iso: string): string;                // "Fri Oct 16, 2026 (demo date)"
  ```
  `src/lib/time.test.ts` (exact): `formatTimePoint("2026-10-19T19:00:00-05:00")==="7:00 pm"`; `"2026-10-16T12:00:00-05:00"`→`"12:00 pm"`; `"2026-10-17T00:00:00-05:00"`→`"12:00 am"`; `formatTimeRange("2026-10-21T08:00:00-05:00","2026-10-21T12:00:00-05:00")==="8:00 am – 12:00 pm"`; arrow variant `"8:00 am → 12:00 pm"`; `formatDateTimeShort("2026-10-19T19:00:00-05:00")==="Mon Oct 19 · 7:00 pm"`; `formatStaffTime(same)==="Mon 7:00 pm"`; `formatDemoDate("2026-10-16T14:20:00-05:00")==="Fri Oct 16, 2026 (demo date)"`; `formatSentence("2026-10-19T19:00:00-05:00")==="Monday, October 19, 7:00 pm"`; a post-DST value `"2026-11-02T08:00:00-06:00"` → `"8:00 am"`; and an offset-different input `"2026-10-19T20:00:00-04:00"` → `"7:00 pm"` (converted to Chicago). No output may match `/ |[AP]M/`.
- `src/lib/roles.ts` as in §4.9.
- `src/test/no24h.ts`: `export function expectNo24HourTimes(container: HTMLElement): void` fails if `container.textContent` matches `/\b(?:[01]?\d|2[0-3]):[0-5]\d\b(?!\s?[ap]m)/i` (a time without am/pm). Note: version strings like `1.2.3` do not match; the code card's six digits are never colon-formatted.
**Check:** `npx vitest run src/lib` green.

### Step 5 · API layer
Implement `src/api/{errors,transport,sse,refetch,client,useOp,useEventStream}.ts` per §4.4–§4.6.
- `sse.ts`: `export class SseParser { push(chunk: string): SseFrame[] }`, `interface SseFrame { id: number | null; event: string; data: string; comment?: string }`. Handles `\n` and `\r\n`, multi-line `data:`, comment lines (`: heartbeat` → a frame with `comment` and no data, which `openStream` swallows), frames split across chunks, `id:` parsed to integer, default `event` `"message"`.
- `defaultTransport.openStream`: `fetch(url, { headers: { Accept: "text/event-stream", "Last-Event-ID": String(lastId) }, credentials: "include", signal })`; status updates `connecting → open → reconnecting`; backoff 1 s, 2 s, 4 s, 5 s cap; stop and set `closed` on 401/403/404/410; track the highest id seen and use it on reconnect; `onEvent(JSON.parse(frame.data), frame.id, frame.event)`.
- `client.ts` exposes `OPS`, `callOp`, the type helpers, `ApiErrorBody`.
- `src/test/fakeTransport.ts`: `makeFakeTransport(handler: (ctx, url, init) => Response | Promise<Response>): ApiTransport` and `jsonResponse(status, body, headers?)`.
- Tests: `src/api/sse.test.ts` (two frames in one chunk; one frame split over three chunks; CRLF; a `: heartbeat` comment; `id:` absent → `null`); `src/api/client.test.ts` (path params are `encodeURIComponent`-ed: `getCase` with `reference: "MHC-C-0007"`; missing param → `ApiError` code `MISSING_PARAM`; `callOp("logout")` on 204 → `undefined`; `callOp("startChatSession")` returns the 201 body; error body `{error:{code:"CASE_NOT_FOUND",…},request_id:"r1"}` on 404 → `ApiError` with `status 404`, `code "CASE_NOT_FOUND"`, `requestId "r1"`; 401 `UNAUTHENTICATED` calls `emitAuthLost` with `"expired"` when `details.reason==="expired"`; a 401 from `login` does **not** emit; a network failure → `ApiError(0,"NETWORK")`; **a 200 composed error** such as `{blocks:[{type:"error",code:"SLOT_TAKEN"…}]}` is returned, not thrown; `OPS.getQueue.roles` equals `["representative","supervisor"]`; type tests with `expectTypeOf`); `src/api/useOp.test.tsx` (loading → success; `refetchAll()` refetches; `args: null` makes no call; unmount aborts).
**Check:** `npx vitest run src/api` green; `npm run typecheck` green.

### Step 6 · Providers, shell, router, stubs
1. `src/test/render.tsx`: `renderWithProviders(ui, { route?: string, transport?: ApiTransport, role?: Role })` wraps `createMemoryRouter` + `AnnounceProvider` + `SessionProvider` + `DemoStatusProvider` with a fake transport that answers `getSession`, `getStaffing`, `getDemoClock` with minimal valid bodies built from the **OpenAPI example values** (copy the `CUSTOMER`/`REPRESENTATIVE` session bodies and the `START`/`OFF` bodies into `src/test/fixtures.ts`, quoting the spec) .
2. `src/state/session.tsx`, `src/state/demoStatus.tsx` per §4.9.
3. `src/components/ui/*` (§4.7) and `src/components/shared/*`, `src/components/shell/*` (§4.8). Build in this order so each compiles: `cx` → `icons` → `Tag/PriorityTag` → `Button` → `Field/TextInput/Checkbox` → `Card*` → `Skeleton` → `Disclosure` → `Dialog` → `LiveRegion/AnnounceProvider` → `Time/TimeWindow/RefChip` → `AssistantMark/PersonDisc/SpeakerLine/MessageRow/EventLine` → `RoleSwitch/SignOutButton/DemoBar/StaffingBanner` → `ConsoleHeader/DemoPageHeader/AppFrame/Main/RoleGate/RoleNotAllowedPanel` → `ErrorLine/EmptyState/StaleLine/ResultLine` → `QueueRow`.
   - **`RoleSwitch` construction:** Radix `RadioGroup.Root` named "Acting as" (`aria-label="Acting as"`), four `RadioGroup.Item`s in `ROLES` order; segment text shows `ROLE_LABEL[role].short` at ≥ 700 px and `.phone` below (two spans, one `sr-only`-toggled by a media class), accessible name always `ROLE_LABEL[role].full` plus `", current"` for the checked one; the checked segment is filled (`--color-surface-selected`, 1 px ink edge, check icon) and its `onValueChange` does nothing; while `switching !== null` all four are `disabled` and the chosen shows "Switching…"; the error line "Couldn't switch role. Try again." sits under the group (`role="status"`); each segment ≥ 44 px tall on phone widths, 32 px console. It is the first control after the skip link.
   - `AppFrame` renders the skip link first, then the frame; `frame="auth"` is a single narrow column with no role switch.
   - `RoleGate` calls nothing itself; it reads `useSession().role`.
   - `RoleNotAllowedPanel` copy: when `role === "customer"` exactly `You're acting as the customer. Switch to a staff role to see this.` (SCREEN_SPECS SCR-4 stale); otherwise (proposal) `You're acting as {ROLE_LABEL[role].full}. Switch to {allowed full names joined with " or "} to see this.`; the `RoleSwitch` renders beside it; a `role_reset` panel uses the CON-10 sentence in §4.9.
4. `src/routes.ts` (§4.9), `src/router.tsx` (exports `createAppRouter()`, **not** a module-level router, because the dev layer registers its `/__kit` route before the first render; `App.tsx` calls it once inside `useMemo`; it builds `createBrowserRouter` with a root layout that mounts `AnnounceProvider`, `SessionProvider`, `DemoStatusProvider`, a theme effect and `<Outlet/>`; `/login` public; everything else under `RequireSession`, which renders a frame skeleton while `status === "loading"` and `<Navigate to="/login?return_to=…&reason=…">` when signed out; per-screen `lazy(() => import("@/screens/<slug>"))`; a `*` route renders a plain "Page not found" with a link to `/`), `src/App.tsx` (`<RouterProvider router={router}/>`), `src/main.tsx`:
   ```tsx
   import { StrictMode } from "react"; import { createRoot } from "react-dom/client";
   import "./styles/index.css";
   import { applyTheme } from "./state/theme"; import App from "./App";
   function start() { applyTheme(); createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>); }
   // Mock mode only (`npm run dev:mock`). Vite replaces import.meta.env.MODE at build time, so a production build drops this
   // branch and src/dev/ entirely (checked by scripts/check-dist.mjs).
   if (import.meta.env.MODE === "mock") void import("./dev/install").then((m) => { m.installDev(); start(); });
   else start();
   ```
5. `src/screens/ScreenStub.tsx`: `ScreenStub({ id, title, states }: { id: ScreenId; title: string; states: StandardState[] })` renders the right frame and header for the screen (`ConsoleHeader` for console screens inside `RoleGate`; `DemoPageHeader` for page screens; `DemoBar` + `RoleSwitch variant="row"` for SCR-1; none for SCR-12), then `<Main><h1>{id} · {title}</h1>` with one line "Stub: this screen is built by {group}." and a definition list of the route path and the real standard states from `MATRIX`. No data, no invented copy beyond that. For SCR-6 it reads the `:reference` param and prints it. `document.title = "{id} · {title} · Meridian"`.
6. Twelve folders `src/screens/scrNN/{index.ts,ScrNN.tsx}`; `index.ts` is `export { default } from "./ScrNN";`; `ScrNN.tsx` is the stub (default export). SCR-1 also gets `contract.ts`, `blocks.ts`, `cards/index.ts` (§4.9). SCR-12's stub has the form-less statement only (G3 builds the form).
7. Tests: `src/routes.test.ts` (12 screens, unique ids/paths/slugs, `SCREENS.find(s => s.id === "SCR-12").public`, every `LINKS.to` is a `ScreenId` or one of the four literals, `caseHref("MHC-C-0007") === "/staff/cases/MHC-C-0007"`); `src/screens/stubs.test.tsx` (each of the 12 routes renders exactly one `h1` containing its id when the role is allowed; SCR-5 as customer renders the F-12 sentence and `callOp` was not called for `getQueue`); `src/state/session.test.tsx` (switchRole matrix: Customer→`/`, Representative→`/staff/queue`, Supervisor→`/staff/oversight`, Owner→`/staff/owner`; on `/demo`, `/demo/inbox`, `/monitoring`, `/eval` the path is unchanged; a 401 on `getSession` navigates to `/login?return_to=%2Fstaff%2Fqueue&reason=none`; `signOut` calls `logout` then `/login`); `src/state/theme.test.ts` (default `light`, stored `dark` wins, junk ignored); component tests: `RoleSwitch.test.tsx` (radiogroup named "Acting as", four radios in order, checked one's name ends ", current", switching disables all, error line text), `QueueRow.test.tsx` (the accessible name example above; "Overdue" tag has a clock icon and no `red`; "Demo seed" tag; `owner:null` → "Unowned"; the 12-hour check via `expectNo24HourTimes`), `PriorityTag.test.tsx` (P0 → "P0 · Safety", P1 "P1 · Danger" strong; P3 "P3 · Standard" plain), `Dialog.test.tsx` (`showModal` called, Escape closes, focus returns), `Time.test.tsx` (`<time datetime="2026-10-19T19:00:00-05:00">7:00 pm</time>`; null → fallback; hero arrow `aria-hidden` with hidden "to"), `Button.test.tsx` (loading keeps label width via `aria-busy`, disabled, the four variants).
**Check:** `npm run typecheck`, `npx vitest run src/components src/state src/screens src/routes.test.ts` green.

### Step 7 · The state matrix and scenario plumbing (dev layer part 1)
1. `src/dev/scenarios/matrix.ts`: the 96 cells from §6.3 (82 real, 14 n/a with the spec's reason strings).
2. `src/dev/scenarios/types.ts` (§4.9), `src/dev/stream/types.ts`:
   ```ts
   export interface StreamStep { afterMs: number; event: unknown }          // a typed ChatEvent / CaseEvent payload
   export interface StreamScript { thread?: string; steps: StreamStep[]; dropAfterMs?: number }
   ```
3. Twelve `src/dev/scenarios/scr01-core.ts`, `scr01-cards.ts`, `scr02.ts` … `scr12.ts` stubs, each exactly: `export const screenScenarios: ScreenScenarios = { complete: false, scenarios: [] };` plus `src/dev/scenarios/shared.ts` (foundation-owned, real content): cross-screen scenarios available on any screen, ids prefixed `shared.`: `shared.session-ended` (`getSession: { example: "UNAUTHENTICATED_EXPIRED", status: 401 }`), `shared.role-reset` (`getStaffing`/any staff op → 403 `ROLE_NOT_ALLOWED_ROLE_RESET`), `shared.staffing-on`, `shared.staffing-off`, `shared.offline` (`fail: "network"` on `getSession`, `getStaffing`, `getDemoClock`), `shared.slow` (every shared op `delayMs: 4000`). They carry `screen: "SCR-1"` etc. only as a placeholder: give `Scenario.screen` the extra value `"*"` for shared ones (widen the type: `screen: ScreenId | "*"`).
4. `src/dev/scenarios/index.ts`: `allScenarios(): Scenario[]` (merge shared + the 13 files), `scenariosFor(screen: ScreenId): Scenario[]`, `isComplete(slug): boolean`, `SCENARIO_FILES` array of `{ slug, group, screenScenarios }`.
5. `src/dev/reactions/index.ts` imports `reactions` from `shared.ts` and the thirteen stub files (`scr01-core.ts`, `scr01-cards.ts`, `scr02.ts` … `scr12.ts`; each `export const reactions: Reaction[] = [];`) and concatenates them. `src/dev/directors/index.ts` imports `rules` from `chat-core.ts` and `chat-cards.ts` (stubs `export const rules: DirectorRule[] = [];`) and exports `pickTurnExample(req): string` which returns the first rule's answer, else `"ANSWER_WITH_SOURCE"`. `src/dev/stream/chat-scripts.ts` (G1) and `case-scripts.ts` (G4) stubs: `export const chatScripts: Record<string, StreamScript> = {};` / `caseScripts`.
6. Tests: `src/dev/scenarios.integrity.test.ts` — matrix has 96 cells, 82 real, 14 n/a, the 14 n/a keys equal the §6.3 list; for every scenario returned by `allScenarios()`: id unique and starts with its file's slug (or `shared.`), `route` matches a `SCREENS` path pattern (`:reference` filled), every `ops` key is an `OperationId`, every `example` exists in `OPS[op].responses[*].examples` (unless it is a `sequence`, then check each), `role` allowed by the screen, `state` is a `StandardState`, and (when `real: false` in the matrix for that cell) the scenario's `state` is not an n/a cell. `src/dev/scenarios.coverage.test.ts` — for each file whose `complete === true`, every **real** standard state of its screens has ≥ 1 scenario; for files with `complete: false` the test is skipped with `it.skip`, so the foundation suite passes with stubs and each group's final commit flips its flag.
**Check:** `npx vitest run src/dev/scenarios` green.

### Step 8 · Dev transport, world, resolve (dev layer part 2)
`src/dev/world.ts`:
```ts
export interface World {
  signedIn: boolean; role: Role; sessionBody: SessionInfo | null;   // body of the last login/switchRole (for getSession)
  staffing: "nobody_online" | "simulated_on_shift";
  expireNext: boolean; refuseNextLogin: boolean; roleResetPending: boolean;
  delayMs: number | "hang" | 0;                                     // global; per-op OpForce wins
  forces: Partial<Record<OperationId, OpForce>>;                   // current forces (sequences carry a cursor inside the store, not the force)
  scenarioId: string | null;
}
export function getWorld(): World; export function setWorld(patch: Partial<World>): void; export function subscribe(cb: () => void): () => void;
export function resetWorld(): void;   // signed out, role customer, staffing off, no forces
```
Persisted in `sessionStorage["mhc.dev.world"]` (per tab). **URL params read once at install and override the stored world** (then written back with `history.replaceState` so the URL reproduces the state): `?signedin=0|1` (default 0 when nothing is stored), `?role=customer|representative|supervisor|owner`, `?staffing=on|off`, `?ex=getQueue:SEEDED,getStaffing:ON` (comma list of `opId:NAME`; `opId:409/NAME` disambiguates), `?delay=1500|4000|hang`, `?theme=light|dark`, `?scenario=<id>`.

`src/dev/resolve.ts` — **pure, unit-tested**: `resolveCall(ctx: CallContext, meta: OpMeta, world: World, defaults: DefaultMap, takeSequenceStep: (op) => OpForce | undefined): Resolution` with
```ts
type Resolution =
  | { kind: "short-circuit"; response: { status: number; body?: unknown } }       // answered without Prism (getSession for supervisor/owner, signed-out 401…)
  | { kind: "prism"; prefer: string; delayMs: number; transform?: (b: any) => any }
  | { kind: "network-fail"; delayMs: number }
  | { kind: "hang" };
```
**Precedence, first match wins (implement as numbered steps in code):**
1. `op === "login"`: if `world.refuseNextLogin` → Prism `Prefer: code=401, example=LOGIN_FAILED` (clear the flag after use); else normal (Prism returns `LOGGED_IN`).
2. Not signed in and `meta.auth` → Prism `Prefer: code=401, example=UNAUTHENTICATED`. `world.expireNext` → `UNAUTHENTICATED_EXPIRED`, then `signedIn=false`, flag cleared.
3. An explicit force for `op` (URL `?ex`, scenario, panel): `{sequence}` takes the next step; `{hang}` → hang; `{fail}` → network-fail; `{example}` → Prism with `Prefer: code=<status of that example from OPS>, example=<name>` (use `status` when the name exists under two statuses).
4. Role emulation: `meta.roles` does not include `world.role` → Prism `Prefer: code=403, example=ROLE_NOT_ALLOWED` (or `ROLE_NOT_ALLOWED_ROLE_RESET` once when `world.roleResetPending`).
5. `op === "getSession"` and `world.sessionBody` set → short-circuit 200 with that body (it came from a Prism `switchRole`/`login` response: nothing invented). If null: Prism `CUSTOMER`.
6. `op === "submitTurn"` → Prism `Prefer: example=<pickTurnExample(body)>`.
7. Defaults table (`src/dev/defaults.ts`): `getStaffing` → `staffing === "simulated_on_shift" ? "ON" : "OFF"`; `startChatSession` → `"SIMULATION_ON"` when staffing on, else `"STARTED"`; `getDemoClock` `START`; `listDemoRoles` `ROLES`; `getQueue` → `STAFFED_WITH_WAITING` when staffing on else `SEEDED`; every other operation → the **first** 2xx example listed in `OPS[op].responses` (Prism's own default). Group files may override via `reactions` + forces; they never edit `defaults.ts`.
8. `delayMs`: the force's `delayMs`, else `world.delayMs`.
`Prefer` value: `code=<status>, example=<name>` (always both, so a 4xx example is selectable).

`src/dev/transport.ts`: `wrapTransport(base: ApiTransport): ApiTransport` — `fetch(ctx, url, init)`: run `resolveCall`; apply `delayMs` with `setTimeout`; for `short-circuit` return a synthetic `Response` (JSON, `X-Request-ID: dev`); for `prism` add header `Prefer`, call `base.fetch`, then **drift check**: if `res.headers.get("sl-violations")` includes `"severity":"Error"` or the body `type` contains `stoplight.io/prism/errors` → `console.error("[contract drift] <op> <method> <path>: <detail>")`, record in the call log, and return a `Response` with status 599 and `{error:{code:"CONTRACT_DRIFT"}}` (so `callOp` throws `ApiError` code `CONTRACT_DRIFT`); apply `transform` to the JSON body when present (typed by the caller's scenario; re-validate nothing); log the call; run reactions (`reactions` matching `{op,status,example}`) **after** the response is recorded. `openStream(spec)` → the dev stream opener (Step 9). Shared reactions in `src/dev/reactions/shared.ts`: `login` 200 → `signedIn=true`, `role=customer`, `sessionBody=response.session`, write cookie `mhc_session=prototype-synthetic; path=/; SameSite=Lax` (via `session-fake.ts`); `logout` → `signedIn=false`, clear cookie, `sessionBody=null`; `switchRole` 200 → `role`, `sessionBody`; `setStaffing` 200 → `world.staffing` from the **request body** `mode`; `resetDemo` 200 → `role="customer"`, `sessionBody=null` (getSession falls back to CUSTOMER), `roleResetPending=true`, `refetch()`.
`src/dev/session-fake.ts`: `setSessionCookie()`, `clearSessionCookie()` (the only `document.cookie` writers in the app), `fakeLoginRules`: any non-empty username and password is accepted; the panel offers "Refuse next login", "Expire session", "Reset role".

Tests (`src/dev/resolve.test.ts`): precedence (signed-out beats a force; a force beats role emulation; sequence cursor advances and repeats the last), role emulation by `x-roles` (customer on `getQueue` → 403; owner on `getCase` → no 403; representative on `advanceDemoClock` → 403), `getSession` answered from `sessionBody` for supervisor (no Prism call), `Prefer` strings (`"code=200, example=SEEDED"`, `"code=409, example=VERSION_CONFLICT"`), `submitTurn` default `ANSWER_WITH_SOURCE`, `delay` precedence, URL param parsing (`?ex=getQueue:SEEDED,getStaffing:ON`, `?ex=applyCaseAction:409/NOT_ALLOWED_IN_STATE`), drift detection (a `Response` with `sl-violations: [{"severity":"Error"…}]` → status 599). `src/dev/calllog.test.ts` (ring buffer of 200; entries have `{t, op, method, path, status, example, ms, drift}`; `window.__mhcDev.calls()` returns them).
**Check:** `npx vitest run src/dev` green.

### Step 9 · Scripted streams (dev layer part 3)
`src/dev/stream/dev-stream.ts`: `createDevStreamOpener(fetchViaDev: ApiTransport["fetch"]): ApiTransport["openStream"]`. For each `openStream(spec)`: call the dev `fetch` once for the stream operation (so Prism still validates the cookie, the path and `Last-Event-ID`; the body is read and **discarded** unless a scenario sets `stream.useFrames`), set status `open`, then deliver events only from (a) the active scenario's `stream.steps` (each `afterMs`), (b) `emit(thread, event)` from reactions, (c) the panel's "Stream" tab buttons. Event ids are assigned by the opener (monotonic per stream key). `drop()` sets `reconnecting` and buffers events; `resume()` sets `open` and replays the buffer in order (the Last-Event-ID behaviour of N-2). A `demo_reset` or `chat_closed` event closes the stream after delivery. The opener parses the Prism `FRAMES` text with the **same** `SseParser` when `useFrames` is set, so the parser is exercised.
Panel "Stream" tab buttons (typed with `components["schemas"]["ChatEvent"]` / `CaseEvent`, so a schema change breaks the build): chat: `representative_joined`, `ai_paused`, `staff_message`, `ai_resumed`, `chat_closed`, `staffing_changed`, `shift_ended`, `clock_changed`, `demo_reset`, plus "Drop connection" / "Reconnect". Their payloads are built by helpers in `src/dev/stream/events.ts` **from values quoted in the OpenAPI examples** (Riley, "Hi Omar, I can look at the after-hours charge with you.", `2026-10-16T14:22:00-05:00`, reference `MHC-C-0007`); each helper carries a comment naming the OpenAPI example it copies, and the ones with no example (everything except the three in `FRAMES`) carry `// dev fixture: no named example in the OpenAPI (see foundation plan §8.2)`.
Test `src/dev/stream.test.ts`: events delivered in order with increasing ids; `drop` buffers and `resume` replays; `chat_closed` closes.
**Check:** `npx vitest run src/dev/stream.test.ts` green.

### Step 10 · The panel, call log UI, kit route, installer (dev layer part 4)
- `src/dev/install.ts` begins with `export const __MHC_DEV_LAYER__ = "mhc-dev-layer";` and `installDev()` does: read URL params → `setWorld`; `setTransport(wrapTransport(defaultTransport))`; if `signedIn` set the fake cookie; apply theme param; mount the panel in its **own** React root appended to `document.body` (id `mhc-dev-panel-root`), so it cannot disturb the app tree; expose `window.__mhcDev = { world, calls, scenarios, apply(id), emit(...) }`; if `?scenario=` apply it.
- `src/dev/Panel.tsx`: bottom bar **"Prototype only"** (charcoal surface from tokens, never red), collapsed to a small pill at bottom right; expanded it has tabs **States · Session · Calls · Stream · Look**:
  - **States:** screen jumper (the 12 screens + "go"); for the **current route's screen** the scenarios grouped by the eight standard states (n/a cells shown greyed with their reason, from `MATRIX`) then its `flowState` ones, plus the `shared.*` list under "Anywhere"; clicking a scenario → `applyScenario(id)`: set role, staffing, forces, stream, **navigate to `route`** (`window.history.pushState` + `popstate` event so the SPA router re-renders), `refetchAll()`, and write `?scenario=id` to the URL. A "Clear forces" button; a per-operation select for every operation the current screen has called (taken from the call log), listing its named examples from `OPS` (`opId: NAME`), which sets a force and updates `?ex=`.
  - **Session:** signed-in toggle ("Fake sign-in"), role select (sets the world role **without** a Prism call), "Expire session", "Refuse next login", "Reset role", "Restart" (reset world, clear cookie, go to `/login`), theme toggle (light/dark → `localStorage["mhc.theme"]` + `applyTheme()`), delay select (off / 1.5 s / 4 s / hang).
  - **Calls:** table of the call log (time, op, method, path, status, example, ms) with a red-free "drift" marker as the word **Drift**; "Copy JSON" button; counts by op; a "Clear" button.
  - **Stream:** the buttons from Step 9 for the open stream key(s).
  - **Look:** a link to `/__kit` (below).
- `src/dev/Kit.tsx`: route `/__kit` (registered by `installDev` through `window.__mhcDevRoutes`, which `router.tsx` reads **only if defined**: `const devRoutes = (globalThis as {__mhcDevRoutes?: RouteObject[]}).__mhcDevRoutes ?? []`; no import of `src/dev` from `router.tsx`). The kit renders every shared and ui component in all its states, light and dark side by side, using no API data (use obviously synthetic labels such as "Example row"): Button variants and states, Field states, Tags and PriorityTag P0–P4, Card with header meta, Skeleton, Disclosure, Dialog trigger, RoleSwitch (with a fake in-memory session), QueueRow in each lifecycle/due state built from a typed `QueueRow` literal copied from the OpenAPI `SEEDED` example (cite it in a comment), MessageRow (assistant, customer, representative, flat), EventLine, ErrorLine, EmptyState, StaleLine, DemoBar.
- `src/dev/defaults.ts`, `src/dev/calllog.ts` as specified.
**Check:** `npm run typecheck`, `npm run lint`, `npx vitest run src/dev` green.

### Step 11 · Prism smoke and Playwright route smoke
1. `scripts/prism-smoke.mjs` (Node ≥ 24, global `fetch`; reads `contract.gen.json`; `MOCK_PORT` default 4019): for every **non-stream** operation and every `(status, exampleName)` in `responses`: send the request with `Cookie: mhc_session=smoke` (omit for `login`), path params from `params.path[*].example` (fallback `"x"`), body from the operation's first `requestExamples` value (for `submitTurn` use `TEXT`), header `Prefer: code=<status>, example=<name>`. **Expect `res.status === status` and no `sl-violations` header with `"severity":"Error"`.** Also send every `requestExamples` entry once with no `Prefer` and expect a 2xx. For the two stream operations send one GET and expect 200 and `content-type` containing `text/event-stream`. Informational probe (never fails the run): `GET /api/session` without a cookie and print the status (the plan assumes Prism answers 401; the dev layer emulates it either way). Print a summary table (`N requests, M failures`) and exit 1 on any failure.
2. `playwright.config.ts`: `webServer` array starting `npm run mock` (port 4019) and `npm run dev:mock` (port 5184) with `reuseExistingServer: false`, `timeout: 60000`; one project `chrome-desktop` (`channel: "chrome"`, viewport 1280×800, `reducedMotion: "reduce"`, `locale: "en-US"`, `timezoneId: "America/Chicago"`), one `chrome-phone` (390×844). `testDir: "tests/e2e"`. Always run under a hard cap (below).
3. `tests/e2e/smoke.spec.ts`: for each of the 12 screens and a role the screen allows (SCR-1…4, 10, 11 as `customer`; SCR-5 `representative`; SCR-6 `/staff/cases/MHC-C-0007` `representative`; SCR-7 `supervisor`; SCR-8 `representative`; SCR-9 `owner`; SCR-12 with `?signedin=0`): `page.goto(path + "?signedin=1&role=" + role)` (SCR-12: `/login`); expect exactly one `h1` whose text starts with `SCR-<n>`, the role switch (`getByRole("radiogroup", { name: "Acting as" })`) present on every screen except SCR-12, **no** `console` message containing `[contract drift]`, no `pageerror`, then `new AxeBuilder({ page }).analyze()` has 0 violations. Plus two flow checks: (a) signed-out visit to `/staff/queue` lands on `/login?return_to=%2Fstaff%2Fqueue&reason=none`, (b) the role switch click Customer→Representative lands on `/staff/queue` and Representative→Customer on `/`.
**Check:** with Prism up (see §7) `npm run smoke:mock` → `0 failures`; `perl -e 'alarm 300; exec @ARGV' npx playwright test` green.

### Step 12 · Visual and responsive check (Chrome DevTools MCP, no screenshots committed)
Start `npm run mock` and `npm run dev:mock`. Open `http://127.0.0.1:5184/__kit` (mock mode) and check light then dark at 1280 and 390 wide (`emulate`/`resize_page`): every component renders in both themes with no horizontal page scroll; focus rings visible (Tab through the kit); tags are filled (no outlined pills); no red anywhere; times read 12-hour. Then `/login` → fake sign-in via the panel → each of the 12 routes (use the panel jumper) at 390 and 1280: header, role switch (≥ 44 px tall at 390), demo bar. Fix defects in owned files; list what you checked in the report. Stop both servers when done.

### Step 13 · Build, dist check, docs
1. `npm run build`; `npm run check:dist`: `scripts/check-dist.mjs` scans `dist/**/*.{js,css,html}` and exits 1 if any of `__MHC_DEV_LAYER__`, `mhc.dev.`, `Prototype only`, `prototype-synthetic`, `fonts.googleapis` appears (or if `dist/` is missing); do **not** search for the bare word `Prefer`, libraries contain it.
2. `README.md` (short): what `apps/web` is, run commands, ports, env vars (`WEB_PORT`, `MOCK_PORT`, `API_PORT`), URL parameters, resolved dependency versions, the "do not hand-edit generated files" note.
3. `docs/ux/04-prototype/PROTOTYPE_PLAN.md` skeleton, sections in this order, each with its content from this plan and `TODO(integrator)` only where a group result is needed: **Status** (UX-4, foundation built, groups pending) · **Run it** (the commands and ports of §4.1; two terminals; SSH tunnel `ssh -L 5184:127.0.0.1:5184 claude-vultr`) · **What is clickable** (table: SCR → route → group → status `stub`) · **What is faked, and how** (rows: demo login and cookie; role switch and role enforcement; staffing/clock/reset worlds; session expiry; supervisor/owner `getSession`; scripted SSE; chat director; delays and forced failures; every fake lives in `src/dev/**`) · **The state switcher** (panel tabs, URL params, scenario ids) · **The contract check** (`gen:types`, `check:gen`, `smoke:mock`, drift lines, Playwright smoke) · **Per-group notes** (links to `groups/g*.md`) · **Known mock artefacts** (§8.2 list) · **Known deviations** (stack departures: React/Vite SPA instead of server templates; hand-written shadcn-style components; fonts via `@fontsource` (no preload, no `size-adjust` metrics yet: design.md §3.1 asks for them at UX-4 and they are deferred to UX-5); `tnum` result from `check-fonts.py`; owner nav; role-gate copy for non-customer roles) · **Data** (synthetic only, from the OpenAPI examples) · **Checks** (table to fill: commands and results).
**Check:** the three files exist; `npm run check:dist` exits 0.

### Step 14 · Final gates
Run the full gate list in §7 once, in order, and paste the results into the report.

## 6. Data and fixtures

Synthetic only; **every value comes from the OpenAPI named examples** (Omar Patel, MHC-C-0007/0008, INV-204411, technician Jun Park, Riley, `2026-10-16T14:20:00-05:00` demo clock). Nothing is invented in the foundation: stubs show ids and state names; test fixtures in `src/test/fixtures.ts` and the kit's typed literals quote OpenAPI examples and name the example in a comment.

### 6.3 The state matrix (SCREEN_SPECS "State matrix"; `src/dev/scenarios/matrix.ts`)

All 96 cells (12 screens × the eight standard states `default empty loading partial error stale success disabled`) are `real: true` **except** these 14 n/a cells (store the spec's reason verbatim):

| Cell | Reason |
|---|---|
| SCR-2 partial | n/a: each message is delivered whole; there is nothing to show half of |
| SCR-3 empty | n/a: the guide is static content and always has something to show |
| SCR-3 partial | n/a: the only live data is staffing and the clock; if either fails it is the error state for that control while the static guide still shows |
| SCR-4 empty | n/a: the four roles are fixed |
| SCR-4 partial | n/a: a switch either changes the role or it doesn't |
| SCR-7 partial | n/a: one oversight read returns every lane together (CON-17); there is no half-loaded lane to show |
| SCR-8 partial | n/a: each flag is stored whole with its case and message references |
| SCR-9 success | n/a: the page is read-only; opening cases is navigation, not an action with a result |
| SCR-10 success | n/a: read-only page with no actions |
| SCR-10 disabled | n/a: no controls on this page |
| SCR-11 success | n/a: read-only page |
| SCR-11 disabled | n/a: no controls |
| SCR-12 empty | n/a: nothing is listed; the empty form is the default state |
| SCR-12 partial | n/a: a login is accepted or refused; there is no half-signed-in state |

Count check: 96 cells, **82 real**, 14 n/a.

## 7. Checks

**Ports:** Prism **4019**, Vite **5184**, real API 8000 [A] (only `npm run dev`). Start the two servers in the background, remember their PIDs, and stop **only those PIDs** at the end.

**While iterating** (from `apps/web/`): `npx vitest run <path>` for the file you are on; `npm run typecheck` after each step.

**Once before reporting, in this order, stopping at the first red** (lint/format first, then types, then tests, per `build-loop-test-scope`; this slice adds config, dependencies and shared modules to a new package, so the **whole web suite** is "affected"):

| # | Command | Passing looks like |
|---|---|---|
| 1 | `npm run lint` | 0 errors, 0 warnings that are new (react-hooks `exhaustive-deps` warnings must be fixed, not ignored) |
| 2 | `npm run typecheck` | exits 0 (this regenerates the types first) |
| 3 | `npm run check:gen` | exits 0 |
| 4 | `npm test` | all green; expected files: `src/lib/time.test.ts`, `src/api/{sse,client,useOp}.test.ts(x)`, `src/styles/{tokens,guard}.test.ts`, `src/routes.test.ts`, `src/screens/stubs.test.tsx`, `src/state/{session,theme}.test.ts(x)`, `src/components/**/{RoleSwitch,QueueRow,PriorityTag,Dialog,Time,Button}.test.tsx`, `src/lib/returnTo.test.ts`, `src/dev/{resolve,calllog,stream}.test.ts`, `src/dev/scenarios.{integrity,coverage}.test.ts` |
| 5 | `npm run build && npm run check:dist` | build exits 0; check prints no hits |
| 6 | `(npm run mock &) ; sleep 6; npm run smoke:mock` | `N requests, 0 failures`; the unauthenticated probe line is printed |
| 7 | `perl -e 'alarm 300; exec @ARGV' npx playwright test` | all projects green: 12 screens × 2 widths, no `[contract drift]`, axe 0 violations |
| 8 | Step 12 (DevTools) | listed in the report; nothing red, no horizontal scroll |

Existing tests that must stay green: none exist in `apps/web/`; the Python suite (`tests/`, `src/meridian/`) is untouched and not run.
No formatter gate exists for this package (no Prettier in the house web stack); ESLint is the only style gate.

## 8. Risks and requests

### 8.1 Collisions and conflicts to flag

1. **Fonts: the brief said "Geist/Geist Mono"; `design.md` §3 says Instrument Sans (display) + Inter (body) + Geist Mono.** This plan follows `design.md` (Innocent signed it at the UX-3 gate and the caller named it as the authority). If Innocent wants Geist Sans instead, only `fonts.css`, `--font-display`/`--font-body` and `check-fonts.py` change.
2. **Stack departure from the area map / code design (report only, do not edit).** Lines that need reconciling by the integrator:
   - `.claude/reference/area-map.md` line 46: "**Screens** (`web/templates/{customer,staff}/`, `web/static/`) are the UX track's; A8 and A9 wire them." → screens live in `apps/web/` (React/Vite SPA); A8/A9 serve JSON only; A8 `web/app.py` (or A12) serves `apps/web/dist` with an `index.html` fallback for the SPA paths.
   - `.claude/reference/area-map.md` A12 Deploy row (`Dockerfile`, `railway.json`, `scripts/`): the image build gains a Node stage (`npm ci && npm run build` in `apps/web/`, which needs `docs/ux/03-structure/ui-contracts.openapi.yaml` in the build context because `prebuild` regenerates types).
   - `docs/design/code-design.md` line 277: `└── templates/ · static/   per UX-3/UX-4 (the UX track owns the screens)   A8/A9` → remove; replace with "screens: `apps/web/` (outside `src/meridian/`)".
   - `docs/design/code-design.md` lines 273–276: the route comments "+ page", "+ inbox and guide pages", "+ pages", "+ read pages" (`routes/chat.py`, `routes/demo.py`, `routes/staff.py`, `routes/reads.py`) → the routes serve JSON only; the pages are SPA routes.
   - `docs/design/code-design.md` line 612 (collision map row `web/templates/`, `web/static/` | A8 (customer), A9 (staff)) → replace by `apps/web/` owned by the UX/§8 integration track; A8/A9 do not touch it.
   - `pyproject.toml` lists `jinja2` (needed only for server-rendered templates): candidate to drop (A0/A8 decision, not this slice).
   - Router/entry lines: `.claude/README.md` "No product code exists yet" and its layout block (add `apps/web/` as actual); `CLAUDE.md` "System boundaries" row "Screens and UI contracts" (home `docs/ux/` → add `apps/web/`); `.claude/state/icm-progress.md` rows that route the UX-4 prototype.
3. **Contract carries both ISO times and preformatted `*_label` strings.** This plan formats from ISO (design.md §14.5). Request to the contract owners: keep the labels only where they hold non-time words.
4. **`getSession` examples cover only CUSTOMER and REPRESENTATIVE.** Handled in the dev layer from the `switchRole` TO_SUPERVISOR / TO_OWNER bodies (F-31); a named `SUPERVISOR`/`OWNER` example would remove the fake.
5. **Prism's cookie enforcement is assumed** (UI_CONTRACTS: "Prism needs the cookie") but is probed, not relied on: the dev layer emulates 401 itself.
6. **`npm run dev` (real backend) is untested** until the backend exists; the proxy target port 8000 is `[A]`.
7. **Playwright needs Chrome** (`/usr/bin/google-chrome` exists on the VPS). Always run under the 300 s cap; 1.52 hangs on Node 24 (hence `^1.64.1`).
8. The older plan `docs/plans/fanout/2026-10-21-ux/a5-prototype.md` is the standalone HTML direction prototype; it is unrelated and untouched.
9. **Disk is ~86% full** (13 GB free): `npm install` adds ~600 MB; do not `npx playwright install` (use `channel: "chrome"`).

### 8.2 What Prism's static examples cannot show (the dev layer fakes it; groups use these mechanisms)

| Gap | Where it bites | Mechanism in this foundation |
|---|---|---|
| **SSE** (CON-3, CON-21): Prism returns one finite text body | SCR-1 joined/paused/staff messages/closed/reset/staffing/clock events, "Reconnecting…" stale state; SCR-6 live box | `createDevStreamOpener` + scripts + panel Stream tab; only 3 events exist as OpenAPI examples (`FRAMES`: `representative_joined`, `ai_paused`, `staff_message`); `ai_resumed`, `chat_closed`, `staffing_changed`, `shift_ended`, `clock_changed`, `demo_reset` and every `CaseEvent` are **dev fixtures typed against the schema** (request: named examples in the OpenAPI) |
| Write-then-read consistency | claim → case reads; staffing on → banner everywhere and `getQueue`/`startChatSession`; clock advance → overdue; reset → role back to customer and chats ended | `World` + `Reaction`s (shared ones built here; per-screen ones by groups) + `OpForce.sequence` |
| Role enforcement and session expiry | SCR-4 stale line; SCR-5…9 as customer; "Your demo session ended" on SCR-12 | `resolve.ts` using `x-roles`; `expireNext` |
| Supervisor/owner `getSession` | header after reload | `sessionBody` from `switchRole` |
| Typed words are never echoed | the assistant's reply to what the customer typed | `directors/*` pick the next `submitTurn` example from the request (text keywords, card choice, code, form); the reply text is the example's, fixed |
| Time-based pending states (300 ms, 10 s, 60 s, 65 s give-up) | SCR-1 loading and timeout | `OpForce.delayMs` / `hang` / `fail: "network"`; `TURN_TIMEOUT` is a real example |
| Polling that changes between calls | "2 cases changed. Show them." (SCR-5), "1 new flag" (SCR-8), "New code received" (SCR-2), lanes "updated" (SCR-7), "numbers are as of…" (SCR-9), data-age (SCR-10) | `OpForce.sequence` (first read one example, later reads another) |
| States with no named example | e.g. SCR-6 owner read-only (`allowed_actions: []`), SCR-6 fee/overdue variants, SCR-12 "already signed in" | `OpForce.transform` on the nearest example, **only** when the result still validates against the type; otherwise a request to add a named example. Each group lists its transforms in its `groups/*.md` |
| Idempotent retry (`turn_id`) and `TURN_IN_PROGRESS` | "Try again" | `sequence` of `TURN_TIMEOUT` then `ANSWER_WITH_SOURCE`; proves one request is sent, not server idempotency |
| Clipboard, focus, timers, `<dialog>` | copy code, reset confirm | client-only; unit/e2e tests by the owning group |

### 8.3 Shared-primitive requests each group may make (to the integrator, never edited in place)

- **G1:** a `useScrollToLatest` helper if two groups need it; a `ChatSession` context if G2 needs more than `BlockProps` (propose in `g1-chat-core.md`).
- **G2:** `OptionTile` (slot/follow-up/yes-no tiles) and `Tabs`/day-tab primitive **if G4 also needs them** (default: each builds its own inside its folder using the installed Radix packages).
- **G3:** the `Switch` primitive (native checkbox with `role="switch"`) if G5's SCR-7 shift switch needs the same one: G5 requests it; default is G3 owns `src/screens/scr03/Switch.tsx` and G5 builds its own wrapper.
- **G4:** `SplitButton` and `Tabs`: built inside `src/screens/scr06/` (not shared); promote only if another group needs them.
- **G5:** `MetricTile`, `DefinitionList`, measures table live in `src/screens/reads/`; a shared `Table` primitive only if G4's activity log also wants it.
- Any group: a new `OperationId` default in `src/dev/defaults.ts`, a new token, a missing icon: request in the group file; the integrator edits.

### 8.4 Spec gaps found while planning (no product decision needed; recorded)

1. IA gives no console nav for the **owner**; this plan sets `Outcomes · Review list` (§4.9). Changeable in one constant.
2. SCREEN_SPECS words the role-gate panel only for the customer; the sentence for other roles is a proposal (`RoleNotAllowedPanel`).
3. `/role` (SCR-4 full page) is marked "proposed" in IA/SCREEN_SPECS; it is routed and stubbed so the role-landing table has a target; G3 builds it, and may report "not built" without breaking anything.
4. SCREEN_SPECS SCR-1 says role switch in "its own 44 px row" on a phone; the shared `RoleSwitch variant="row"` provides it, G1 places it.
5. design.md §3.1 asks for fallback metric overrides (`size-adjust`…) and font preloads "computed at UX-4": deferred to UX-5 (recorded as a deviation).
6. **`RESET_IN_PROGRESS` appears under 503 for some operations and 409 for `resetDemo`**: `OpForce.status` disambiguates; the `?ex=` form is `opId:409/RESET_IN_PROGRESS`.

## 9. Readiness

**READY.** No `NEEDS-DECISION`: the font naming difference is resolved in favour of `design.md`; the other open points in §8.4 are copy/constant choices this plan already makes. No `BLOCKED-ON`.

Report back with: the three §7 outputs (steps 1–7), the DevTools notes (step 8), the `check-fonts.py` result, the list of resolved dependency versions, and any place you had to deviate from this plan with the reason.

## Deviations

Recorded by the foundation implementer, 2026-10-21.

1. **`reviewFlag` is `PATCH`**, not `PUT` (OpenAPI `/api/staff/flags/{flag_id}`). The index script walks `get/post/put/patch/delete`; `OpMeta.method` includes `"PATCH"`. Without it the index found 29 operations, not 30.
2. **State matrix data lives in `src/screens/matrix.ts`**, re-exported by `src/dev/scenarios/matrix.ts`. The production stubs must list their real states, but ESLint bans importing `src/dev/**` and the dev layer is excluded from production builds.
3. **`ScreenStub` takes only `id`**; title, group and states come from `SCREENS` and the matrix.
4. **`src/screens/scr01/blocks.tsx`** (not `.ts`): it returns JSX. Import as `./blocks` as planned.
5. **Fake cookie is always set and never cleared** in mock mode (plan: set only when signed in; clear on logout). Prism answers 401 itself, with no named error body, when the cookie is missing (probe: 401), which would make `callOp` throw `HTTP_401` instead of `UNAUTHENTICATED`. "Signed out" is emulated by asking Prism for the `UNAUTHENTICATED` example.
6. **`switchRole` answers with the `TO_<ROLE>` example for the requested role** (resolve step 5b), and role changes made from the panel or `?role=` fetch that example to fill `sessionBody` (`applyRole`). Needed for F-31; Prism would otherwise always return `TO_REPRESENTATIVE`.
7. **`installDev()` is async** (it seeds the session body before the first render); `main.tsx` chains `.then(start)`.
8. **`pickTurnExample(req, ctx)`** takes the director context as a second argument (the rules' `DirectorRule` signature already had it).
9. **`LINKS` has 11 entries**: the IA row "Monitoring, Evaluation" is two entries (SCR-10, SCR-11) so every `to` is a single `ScreenId`.
10. **`@theme static` + `[data-kit-theme]`**: `tokens.css` and `dark.css` also match `[data-kit-theme]` so the kit can show light and dark side by side (component tokens must be re-declared in a scope to re-resolve).
11. **`tailwind-merge` is extended with the type-scale names** (`src/lib/cx.ts`), otherwise `text-body` removed `text-[color:…]` classes; colour and border arbitrary values use `text-[color:var(…)]` / `border-[color:var(…)]`.
12. **Console density is 44 px below 700 px and on coarse pointers**, 32 px otherwise (design.md 8.2), for `Button`, `TextInput`, `TextArea` and `RoleSwitch`.
13. **Tests drop `AbortSignal` from `Request`** in `src/test/setup.ts` (jsdom signals are rejected by undici inside react-router).
14. **Step 12 used Playwright screenshots** (Chrome channel, light and dark, 1280 and 390) instead of the Chrome DevTools MCP, which this implementer's toolset does not include. Screenshots were not kept.
