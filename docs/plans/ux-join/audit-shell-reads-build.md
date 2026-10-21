# UX ↔ backend join audit: shell, read pages, build and the join

**Status:** read-only audit, 2026-10-21. Nothing under `apps/web/**`, `docs/ux/**` or `docs/plans/tickets/**` was edited.
**Level of every claim here:** read from files, not executed (no Prism, Vite, Playwright or build was run for this audit).
**Scope:** app shell and router, login gate, role-switch navigation, the three read pages (SCR-9 / CON-18, SCR-10 / CON-19,
SCR-11 / CON-20), the production build and how AEA-49 serves it, the dev/mock layer, type generation, fixtures, the
Playwright/axe setup, the UX-5 suite plan, and real-backend mode for AEA-55 / AEA-58.
**Sources read:** `apps/web` (package.json, vite/playwright/ts configs, `scripts/`, `src/{main,App,router,routes}.ts(x)`,
`src/api`, `src/state`, `src/components/shell`, `src/screens/{reads,scr09,scr10,scr11,scr12}`, `tests/e2e`, `dist/`),
`docs/ux/04-prototype/PROTOTYPE_PLAN.md`, fan-out plans `foundation.md` and `g5-oversight-reads.md`, the OpenAPI
(`ui-contracts.openapi.yaml` 0.1.0-ux3), `SCREEN_SPECS.md` SCR-9…SCR-12, `stage7/{web,staff,cases,data}.md`,
`internal-components.md` §16, `slice-plan.md` (incl. the integrated-journeys amendment), tickets AEA-23, 48, 49 (rewritten
version), 50, 53, 55, the decision ledgers `7b-decisions/{web,staff}.md`, and `.claude/rules/integrated-journeys.md`.

Severity: **H** breaks a journey, a ticket's acceptance or the deploy, or misreports a number silently; **M** fails a
state or a check, or costs a rework round; **L** polish or a latent risk. Owner is who changes the thing.

## What already lines up (no action)

- The client calls relative `/api/...` paths with `credentials: "include"` (`src/api/client.ts:69`,
  `src/api/transport.ts:55,95`), and Vite's default base puts every built file (scripts, styles, lazy chunks, woff/woff2
  fonts) under `/assets/` (`dist/index.html:8-9`). Same-origin serving by AEA-49 needs no client change.
- `npm run dev` already proxies `/api` to `API_PORT` (`vite.config.ts:8,13`), the route AEA-55 plans to use.
- The dev layer is loaded only behind `import.meta.env.MODE === "mock"` (`src/main.tsx:13`), an ESLint rule forbids
  importing `src/dev` elsewhere, and the current `dist/` holds no scenario, `Prefer`, `?signedin` or panel strings.
- The client-side guard matches WEB-28: `RequireSession` sends a signed-out visitor to
  `/login?return_to=<path+search>&reason=none` (`src/router.tsx:40-43`), the same URL the server's 303 produces, and
  SCR-12 shows the "session ended" line for `reason=expired` (`src/screens/scr12/Scr12.tsx:25`). `return_to` is
  same-origin only (`src/lib/returnTo.ts`).
- Read-page clocks: SCR-9 compares CON-18 `as_of` with the demo clock and labels it "(demo time)"
  (`scr09/basis.ts`, `Scr09.tsx:67-75`), which matches STF-22; SCR-10's "Updated" line uses CON-19 `as_of`, which the
  contract fixes as wall-clock time.
- Null values: every tile and row shows "—" plus `null_reason` when `value` is null; a zero denominator disables
  "Open the cases" (`reads/MetricTile.tsx`, `reads/MeasuresTable.tsx`), as AEA-53 AC-2 expects.
- `openapi-typescript` is pinned exactly (7.13.0, lock and `package.json`), and `check:gen` regenerates both generated
  files into a temp dir and fails on any byte difference (`scripts/check-generated.mjs`).

## (a) Fields, nullables and enums on the three read pages vs what the backend will compute

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| A1 | **The unit vocabulary and the scale of `value` exist only in the examples.** The UI formats a value by `unit` (`"ms"` → seconds, `"share"` → percent of a 0–1 fraction, anything else → bare number) and SCR-9 / SCR-11 format every value as a share. The OpenAPI types `unit` as a free string; neither AEA-53 nor cases.md §9 fixes units, and AEA-53 describes failures as M-24 "per 100 turns" while DO-7's units are "% of conversations", "per 100 turns", "USD per day". A reader that emits `unit: "per 100 turns", value: 1.35` shows "1.35" with no unit; one that emits shares as 0–100 shows "7500%". Schema checks pass either way, and AEA-55 AC-9 (DOM equals response) passes too, so this misreports silently. | H | `apps/web/src/screens/reads/format.ts:23-27`; `scr09/Scr09.tsx:62`; `reads/MeasuresTable.tsx:39`; `scr11/EvalMeasuresTable.tsx:16`; OpenAPI `Measure.unit`, `Tile.unit` (string, no enum; examples use only `count`, `ms`, `share`); AEA-53 AC-3; `key-metrics-registry.md` *Unit* column | AEA-53 (the values); UX session (unknown units) | AEA-53 addendum, before it is planned: `unit` ∈ {`count`, `ms`, `share`}; `share` is a 0–1 fraction; every `EvalMeasure.value` is a 0–1 ratio (it has no `unit` field); M-24 is sent as a count with numerator and denominator, as the example does. UX: render an unrecognised unit as value plus the unit text, never as a bare count. An enum in the OpenAPI is a contract change, so it is Innocent's call. |
| A2 | **`Measure.kind` is ignored.** SCR-9 hard-codes the "Estimate" tag on the first tile and never reads `kind` for the other tiles or the outcomes and handoff rows. If AEA-53 marks any other measure `estimate`, it shows as measured. | M | `scr09/Scr09.tsx:78-79` (literal `true`), `reads/MeasuresTable.tsx` (no `kind`); OpenAPI `Measure.kind` enum `measured` / `estimate` | UX session | Show the tag when `m.kind === "estimate"`, on tiles and table rows. |
| A3 | **SCR-11 aligns measures by `id` alone.** The ids are not unique: the OpenAPI examples reuse `M-27` for every escalation reason, and DO-7 segments M-1 by topic. Two measures with one id give duplicate rows that both show the first one's numbers. | M | `scr11/evalRows.ts:14-17`; OpenAPI CON-19 `DEFAULT` (`M-27` twice); STF-18 (example ids are "illustrative and wrong in places") | UX session; AEA-53 | UX: key rows by `id` + `label`. AEA-53: say whether `id` is unique within a run, and make it so for CON-20. |
| A4 | **SCR-10's empty state is guessed from every health tile.** "No conversations since the last reset" shows only when every health tile is 0 or null. AEA-53 adds a `scheduler_last_run` health tile (cases.md §9) and a latency tile with a reason, so after a reset the empty line may never show; with zero conversations but a non-zero scheduler tile it is suppressed. | M | `scr10/Scr10.tsx:75`; `stage7/cases.md` §9 ("Adds a health Tile `scheduler_last_run`") | UX session; AEA-53 | UX: key the empty state on the volume tile (by label or id agreed with AEA-53). AEA-53: list the health tiles it emits (ids, labels, units) in its plan so the UI and J-10 assert the same set. |
| A5 | A null numerator with a known denominator renders "0 of N", which reads as a measured zero. | L | `reads/format.ts:15` (`numerator ?? 0`) | UX session | Render "—" when the numerator is null. |
| A6 | SCR-11's mix summary adds up transcript and synthetic counts in the browser; the contract has no summary field. It is a sum, not a metric, but AEA-55's Metrics line says "no metric is computed in the browser". | L | `scr11/evalRows.ts:28-31` | UX session / AEA-55 | Record it as an allowed display sum in the UX-5 report so AEA-55 does not flag it. |

## (b) UI state vs backend state

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| B1 | **The role lives on the server session, but the UI never re-reads it after a 403.** STF-19 settles that every tab shares one role and that "a staff tab whose role was switched elsewhere gets 403 `wrong_role` and re-reads `getSession`". The UI reads `getSession` once at start; a `ROLE_NOT_ALLOWED` (`wrong_role` or `role_reset`) only draws the role panel with the stale local role, and the role switch keeps marking the old role as current. data.md §8 / DAT-29 put this check in AEA-55, which may not edit `src/`, so it would fail there with no one able to fix it. | H | `src/state/session.tsx:45-56`; `src/api/client.ts:91` (only 401 is handled globally); `src/screens/reads/ReadError.tsx:9-11`; `7b-decisions/staff.md` STF-19; `stage7/data.md` §8 | UX session | On any `ROLE_NOT_ALLOWED`, and on window focus, re-read `getSession`, update the session, then render the panel from the fresh role. Add a mock scenario for "switched elsewhere" so the state is visible before AEA-55. |
| B2 | **"Cap reached" and the spend percent are computed in the browser.** The tag shows when `today_cents >= cap_cents`, while the decision the backend makes is the `spend_cap_reached` alert (the ledger can stop model calls before the cents round over). The two can disagree on one page. | M | `scr10/SpendBar.tsx:5,13`; OpenAPI CON-19 `alerts[].type spend_cap_reached`; AEA-55 *Metrics* ("no metric is computed in the browser") | UX session | Drive the tag from the alert's `state`; keep the bar as a display of the two numbers the response carries. |
| B3 | **Real time and demo time sit side by side without labels.** SCR-10's "Updated 2:20 pm" is wall-clock time (contract), `last_restart.at` and alert `fired_at` are wall-clock too, and the same header shows the demo date ("Fri Oct 16"). Nothing tells the reviewer which clock a time is on (US-25: nothing misleads about what is simulated). SCREEN_SPECS SCR-10 R1 still says "(demo time)". | M | `scr10/Scr10.tsx:80,93`; `scr10/AlertsList.tsx`; `components/shell/chrome.tsx` `DemoBar`; OpenAPI `MonitoringResponse.as_of` description; AEA-48 contract note 2 | UX session (copy); SCREEN_SPECS line through the UX track | Label wall-clock times "(real time)" on SCR-10; correct SCR-10 R1 in SCREEN_SPECS (UX track, listed for AEA-08). |
| B4 | SCR-11's stale line checks one run's `agent_version` (held-out if present, else dev). A stale dev run beside a current held-out run is not flagged; AEA-53 AC-5 labels each run. | L | `scr11/Scr11.tsx:75-76` | UX session | Compare each run with `current_agent_version` and label each one. |
| B5 | The mock answers `getSession` for supervisor and owner from the last `switchRole` body, because the OpenAPI has no such example. The real `SessionInfo` for those roles is first seen at AEA-58. | L | `PROTOTYPE_PLAN.md:40` | AEA-58 | J-8 asserts the header name and the marked role for all four roles. |

## (c) Guards outside mock mode, and what loads before login

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| C1 | **WEB-1 is still open.** AEA-49 is written for option A (`/login`, `/assets/`, `/fonts/` public). Option B means a second, self-contained login page the UX session would have to build and keep matching SCR-12; option C moves the redirect into the app. The login page's needs are otherwise met by A (see C2 for the one gap). | H | `7b-decisions/web.md` WEB-1 (Innocent); `AEA-49.md` *Awaiting Innocent* | Innocent | Answer WEB-1 before AEA-49 is planned. A needs no frontend work. |
| C2 | **`/favicon.svg` is outside the public prefixes.** It sits at the build root, so web.md §12 answers it with `index.html` (wrong type) when signed in and with a 303 when signed out, including on `/login`. AEA-49's handoff already notes it and leaves it for AEA-55. | M | `apps/web/public/favicon.svg`; `dist/index.html:6`; `stage7/web.md` §12; `AEA-49.md` *Scope boundary* | UX session | Cheapest: import the icon from `src/` so Vite hashes it into `/assets/`, or inline it as a data URI. Serving root files by name instead is a web.md §12 change. |
| C3 | **A transient error at start becomes a sign-out.** If the first `getSession` fails with anything but 401 (network, a 5xx while Railway starts the service), the session becomes "signed-out" and `RequireSession` sends the reviewer to `/login`, though the cookie is valid. This is the Riverside "guards break navigation outside mock mode" class. | M | `src/state/session.tsx:53`; `src/router.tsx:40-43` | UX session | Treat only 401 as signed out; show an error with "Try again" for other failures. |
| C4 | **No cache policy and no recovery from a stale build.** Neither web.md §12 nor AEA-49 sets `Cache-Control`. If a browser keeps an old `index.html` after a redeploy, it asks for chunks that no longer exist; the router has no `errorElement`, so the reviewer gets React Router's default crash page. The spec also does not say that a missing `/assets/x.js` answers 404 rather than `index.html` (which fails as a script with a MIME error). | M | `stage7/web.md` §12; `AEA-49.md` AC-1…AC-5 (no header, no missing-asset case); `src/router.tsx:76-97` | AEA-49 (headers, 404); UX session (error element) | AEA-49: `index.html` and every SPA-fallback response `Cache-Control: no-cache` (or `no-store`, since it is behind the login); `/assets/*` `public, max-age=31536000, immutable`; a missing file under `/assets/` answers 404. UX: see D1. |
| C5 | Production code still reads the dev hook `globalThis.__mhcDevRoutes`. Harmless (same origin), but it is a mock seam in `dist`. | L | `src/router.tsx:101` | UX session | Read it only when `import.meta.env.MODE === "mock"`. |
| C6 | Under Prism **proxy** mode (AEA-55), Prism answers a request without the cookie with its own 401 body rather than the backend's `ApiError`. Only `getSession`'s status check redirects; other calls need `code === "UNAUTHENTICATED"` to raise "auth lost". Whether Prism also logs these as violations (AC-3 requires 0) is untested. | L | `PROTOTYPE_PLAN.md:81`; `src/api/errors.ts:13-15`; `client.ts:91` | AEA-55 | Probe it in AEA-55's first run and record the result; if Prism intercepts, run its request validation so the backend answers 401s. |
| C7 | Local runs need `MERIDIAN_COOKIE_SECURE=false`, or the browser drops `mhc_session` over plain http. | L | `stage7/web.md` cross-topic GRA (`cookie_secure`) | AEA-57, AEA-58, AEA-55 | Set it in the journey and proxy-run environments; record it in the evidence. |

## (d) Error and empty states

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| D1 | **No error boundary anywhere.** A render error on a real response (an unexpected null) or a failed chunk load shows React Router's default "Unexpected Application Error" page instead of SCREEN_SPECS' error copy. Mock data, which always matches the examples, never triggers it. | M | `grep -rn "errorElement\|ErrorBoundary" apps/web/src` → none; `src/router.tsx:76-97` | UX session | Add a root `errorElement`: "Something went wrong. Reload the page." with a reload button; on a chunk-load error, reload once. |
| D2 | SCR-10 shows the "Alerts" heading over an empty list when `alerts` is `[]`. | L | `scr10/AlertsList.tsx:12` | UX session | Add a "No alerts configured" line. |
| D3 | SCREEN_SPECS SCR-10 *empty* says health tiles show "—"; the UI shows "0". | L | `scr10/Scr10.tsx:89`; SCREEN_SPECS SCR-10 states | UX session | Align one with the other (UX track). |
| D4 | Several read-page states exist only as client-side transforms over examples (`withNullPromises`, `rebaseMonitoring`, …). On the real backend they need seeded data or they are `NOT_RUN`. | L | `PROTOTYPE_PLAN.md:69` | AEA-53 seeds; AEA-58 (J-9, J-10) | List each state's real-data recipe in the selector contract (see "What the UX session must provide"). |

## (f) The production build

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| F1 | **`apps/` and `docs/ux/` are not in git.** Build-loop tickets work in worktrees cut from `main`, so AEA-58 (serves `dist`), AEA-59 (type drift, fixtures), AEA-50 (image web stage) and AEA-23's `openapi_check` (reads the signed OpenAPI) would see neither the frontend nor the contract. | H | `git status --short` → `?? apps/`, `?? docs/ux/`; `git ls-files apps \| wc -l` → 0 | Innocent / UX session | Commit `apps/web` (without `dist`, `node_modules`, `test-results`; its `.gitignore` already excludes them) and `docs/ux/` at UX-4 sign-off, before wave 1 (AEA-23) is dispatched. |
| F2 | **`npm run build` reads a file outside `apps/web`.** `prebuild` regenerates types and the op index from `../../docs/ux/03-structure/ui-contracts.openapi.yaml`, but DAT-21 says the image's web stage reads `apps/web` only, so that stage fails as specified. `tsc -b` also type-checks `tests/` and `playwright.config.ts`, so the stage needs dev dependencies (`npm ci` without `--omit=dev`, no `NODE_ENV=production`). | H | `apps/web/package.json:19,22`; `scripts/paths.mjs:5`; `tsconfig.json:20`; `stage7/data.md` §7 (DAT-21) | AEA-50, with a UX decision | Pick one: (a) AEA-50 copies the spec to the same relative path and runs plain `npm ci && npm run build && npm run check:dist`; or (b) the UX session adds `build:dist` (no regeneration; runs `check:gen`, then `vite build`) so the stage really reads `apps/web` only. (b) keeps DAT-21 true. |
| F3 | **`check:dist` is a five-string denylist and is not chained to the build.** `vite build --mode mock` would put the dev layer in `dist`, and only the panel's strings would catch it. Nothing checks the module graph. | M | `scripts/check-dist.mjs:11`; `package.json` (no `postbuild`) | UX session; AEA-50 | UX: `postbuild: npm run check:dist`; build with `manifest: true` and fail if any module under `src/dev/` is in it. AEA-50 runs exactly `npm run build`. |
| F4 | No `engines` field or `.nvmrc`; the VPS has Node v24.21.0, and the image's Node version is not stated. | L | `apps/web/package.json`; `node --version` | UX session; AEA-50 | Add `engines.node`; AEA-50 pins the base image to it. |
| F5 | The production tab title carries internal screen ids ("SCR-10 · Monitoring · Meridian"), and the smoke test depends on it. | L | `src/screens/reads/ScreenTitle.tsx:7`; `tests/e2e/smoke.spec.ts` | UX session | Use "Monitoring · Meridian"; tests read `data-screen` (G4). |

## (g) Selectors, test ids and the suites

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| G1 | **Every e2e test enters its state through mock-only URL parameters** (`?signedin=1&role=…`, `?scenario=…`) and some assert mock-only content (the scripted "$149" reply; `demo` / `demo` credentials). Against the real backend none of them can run as written, and AEA-55 may change configuration only, not specs. This is exactly the bypass integrated-journeys §1 calls `mock-tested` only. | H | `tests/e2e/smoke.spec.ts:30,45,50`; `tests/e2e/sweep.spec.ts:64-70,118,128,134,144,155-158`; `integrated-journeys.md` §1 | UX session (UX-5 suite) | Write the UX-5 suite in two modes: a sign-in fixture that types the demo login from `MERIDIAN_DEMO_USERNAME` / `MERIDIAN_DEMO_PASSWORD` and switches role with the role switch; mock-only tests tagged `@mock-only`, so AEA-55 records them `NOT_RUN` with a reason. |
| G2 | **Ports and origin are hard-coded.** `baseURL` and the web servers are fixed at 5184 / 4019 with `reuseExistingServer: false`, and two assertions match `127\.0\.0\.1:5184`. AEA-55 AC-11 forbids those ports during its run. | M | `playwright.config.ts:10-13`; `smoke.spec.ts:54`; `sweep.spec.ts:149` | UX session | `E2E_MODE=mock\|proxy\|served` and `E2E_BASE_URL`; start web servers only in `mock`; assert paths relative to `baseURL`. |
| G3 | The sweep always writes screenshots into `docs/ux/04-prototype/screenshots`; a rerun by AEA-55 or AEA-58 would write under `docs/ux/**`, which tickets may not touch. | M | `tests/e2e/sweep.spec.ts:19-20,91` | UX session | `SHOTS_DIR` from the environment, defaulting to the UX folder only in `mock` mode. |
| G4 | **No stable hooks for journey assertions.** Only `data-testid="spend-fill"` and `data-screen="SCR-1"` exist. AEA-55 AC-9 (each displayed numerator, denominator and value equals the response) and AEA-58's journeys need to find a value by its field, and ids are not unique (A3). | M | `grep data-testid\|data-screen apps/web/src` → `SpendBar.tsx:10`, `Scr01.tsx:27` | UX session | Publish a selector contract (below): `data-screen` on every screen root; `data-state` (`loading` / `empty` / `error` / `stale` / `partial`) on each read region; `data-measure` (the response path, e.g. `promises_kept_on_time`, `health[2]`) with `data-field` (`value` / `numerator` / `denominator`) on SCR-9/10/11 numbers; role + accessible name for every control. |
| G5 | The `[contract drift]` signal exists only in the dev transport, so in real mode the suites' drift assertions pass vacuously. Contract checking moves to Prism proxy's log (AEA-55 AC-3) and AEA-59. | L | `src/dev/transport.ts:12-76` | AEA-55 | Say so in the UI-verify-again report; AC-3 is the real check. |

## Contract-boundary scripts: what exists and what is missing

| # | Script the join needs | Exists | Missing | Sev | Owner |
|---|---|---|---|---|---|
| S1 | Build `dist` the way AEA-49 / AEA-50 / AEA-58 consume it | `npm run build` (`tsc -b && vite build`, after regenerating types); `npm run check:dist`; output `apps/web/dist/{index.html, assets/, fonts/LICENSES/, favicon.svg}` | A build that reads only `apps/web` (F2); `check:dist` chained to the build plus a module-graph check (F3); a written recipe (Node version, `npm ci` with dev deps, the command, the output path) for AEA-50 and AEA-58 | H (F2) | UX session + AEA-50 |
| S2 | Regenerate types and fail on a diff | `npm run check:gen` (pinned `openapi-typescript` 7.13.0; compares `types.gen.ts` **and** `contract.gen.json` byte for byte) | It runs in no gate (there is no CI file), and the "committed" files are untracked (F1). AEA-59's `test_types_gen_drift.py` covers `types.gen.ts` only, yet `client.ts` builds every URL and method from `contract.gen.json` (`client.ts:40`). | M | AEA-59 (add `contract.gen.json` to the drift test, or simply run `npm run check:gen`); Innocent (F1) |
| S3 | Validate mock fixtures against the OpenAPI, including omitted optionals, nulls, empty lists and error bodies | `npm run smoke:mock` sends every operation × named example to Prism and checks the status and `sl-violations` (request-side); dev stream events and fixtures are TypeScript-typed | Nothing validates response bodies against the schema with a JSON-Schema validator; `OpForce.transform` outputs are unchecked (PROTOTYPE_PLAN.md:79 says "only when the result still validates", with no check); there is no generator for edge variants; `smoke:mock` has not been run (PROTOTYPE_PLAN.md:105). AEA-59's `test_openapi_fixtures.py` validates Prism examples and a generated edge set, but it cannot read TypeScript dev fixtures. | H | UX session: a script (like `tests/e2e/list-scenarios.ts`) that dumps every dev fixture, transform output and scripted stream event to JSON, e.g. `apps/web/tests/e2e/.gen/fixtures.json`, for AEA-59 to validate read-only |

## The join chain (AEA-55, AEA-58 run modes)

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| J1 | **Server-sent events through Prism proxy are unproven.** AEA-55 routes all `/api` traffic through `prism proxy … --errors`. If Prism buffers a response to validate it, the chat and case streams (`text/event-stream`, never-ending) hang. | M | `AEA-55.md` *What to build*; `src/api/transport.ts:40-92` | AEA-55 | Probe it first. If it hangs, send `/api/chat/sessions/*/events` and `/api/staff/cases/*/events` straight to the backend in the Vite proxy (run config, which AEA-55 may change) and record the exception. |
| J2 | **J-10's browser half has no runner in its wave.** The slice-plan map says J-10 (read pages "show stored values with their labels") is first landed by AEA-53, but AEA-53 and AEA-58 (the browser runner) are both wave 3, so AEA-53 can land only the API half. | M | `slice-plan.md` journey map J-10; rows AEA-53, AEA-58 | Orchestrator (slice plan) | Make J-10's browser assertions AEA-58's (or an AEA-53 follow-up after AEA-58), using G4's `data-measure` hooks. |
| J3 | AEA-58 is pytest-playwright (Python); AEA-55 reruns the UX TypeScript suite. Only the selectors and the login steps carry over, not code. | L | `slice-plan.md` row AEA-58 | UX session | Keep the selector contract runner-neutral (roles, names, `data-*`), and write the sign-in steps down, not only in code. |

## Counts

**37 findings: H 7 · M 16 · L 14.** S1 restates F2 and F3, so it is not counted again.

- **H:** A1, B1, C1, F1, F2, G1, S3
- **M:** A2, A3, A4, B2, B3, C2, C3, C4, D1, F3, G2, G3, G4, J1, J2, S2
- **L:** A5, A6, B4, B5, C5, C6, C7, D2, D3, D4, F4, F5, G5, J3

## What the UX session must provide for the shell and the join, and by when

| # | Deliverable | Why | Needed by |
|---|---|---|---|
| U1 | `apps/web` and `docs/ux/` committed (or Innocent's ruling on how tickets read them) | F1: worktrees see nothing otherwise | Before wave 1 dispatch (AEA-23's `openapi_check` reads the OpenAPI) |
| U2 | A build that reads only `apps/web` (`build:dist`), `postbuild` `check:dist` with the module-graph check, `engines.node`, and a written recipe: command, Node version, dev dependencies, output path `apps/web/dist` | F2, F3, F4; AEA-50 (DAT-21) and AEA-58 build it | UX-4 sign-off (AEA-49 and AEA-58 are gated on it; AEA-50 in wave 3 consumes the recipe) |
| U3 | Favicon in the hashed asset graph or inlined | C2 | UX-4 sign-off (before AEA-49's tests fix the public list) |
| U4 | Shell fixes: re-read `getSession` on `ROLE_NOT_ALLOWED` and focus (B1); only 401 signs out (C3); root `errorElement` with chunk-reload (D1); dev hook read only in mock (C5) | Riverside classes (b), (c), (d); AEA-55 cannot edit `src/` | UX-4 sign-off |
| U5 | Read-page fixes: `kind`-driven Estimate tag (A2); rows keyed by `id` + `label` (A3); empty state keyed on the volume tile (A4); unknown units rendered honestly (A1, UX half); cap tag from the alert (B2); real-time labels (B3) | So J-10 and AEA-55 AC-9 assert the same truths as AEA-53 | Before AEA-53 is planned (wave 3); at the latest before AEA-58 adds J-10 |
| U6 | **Selector contract** in `docs/plans/ux-join/` (G4): per screen, the `data-screen`, `data-state` and `data-measure` / `data-field` hooks, the role + name of each control, and, for each SCREEN_SPECS state, how it is reached on the real backend (seed, action or "mock only") (D4) | AEA-58 "Selectors come from the UX session's contract"; AEA-55 AC-9 | UX-4 sign-off (AEA-58 starts in wave 3 against it) |
| U7 | Fixture dump script (S3) | AEA-59 validates mock fixtures and variants read-only | Before AEA-59 is planned (wave 2) |
| U8 | Dual-mode Playwright: `E2E_MODE`, `E2E_BASE_URL`, env-driven sign-in, `@mock-only` tags, `SHOTS_DIR`, no literal ports (G1–G3) | AEA-55 may change configuration only | UX-5 (the suite is written there); needed before UX-5 is signed |
| U9 | UX-5 report notes: allowed browser-side display sums (A6), drift detection is mock-only (G5) | AEA-55 AC-4 / *Metrics* | UX-5 sign-off |

Innocent's items in the same window: **WEB-1** (C1) before AEA-49 is planned; the unit enum (A1) only if he wants it in
the OpenAPI rather than in AEA-53's addendum.

## Join timeline (the ordered points where the two tracks connect)

| Step | Point | UX session | Backend track | Innocent |
|---|---|---|---|---|
| 0 | Before wave 1 / 2 dispatch | Commit `apps/web` and `docs/ux` (U1); fixture dump (U7) | AEA-23 builds `openapi_check` against the committed OpenAPI; AEA-59 planned with `contract.gen.json` in its drift test | Rule on U1 if needed; answer WEB-1 |
| 1 | **UX-4 sign-off** (checklist §4b) | Lands U2–U4 and U6 (U5 may follow); `npm run build && npm run check:dist` green on the committed tree | Unblocks `gate::ux4` on AEA-49 and AEA-58 | Signs UX-4 |
| 2 | **AEA-49** (wave 2) | None (read-only consumer) | `web/frontend.py`: mount, SPA fallback, WEB-1 public paths, cache headers and missing-asset 404 (C4), tests on a fixture `dist` | Decides AEA-49's `risk::security` label (WEB-36) |
| 3 | **AEA-57** (wave 2), then **AEA-58** (wave 3) | Answers selector questions (U6); U5 lands before J-10 | AEA-57: API-level J-1 on the real app; AEA-58 builds `dist` with the U2 recipe, serves it through AEA-49 and runs J-1 (then J-8, J-9, J-10) in a browser via the normal login; AEA-50 builds the image's web stage from the same recipe; AEA-53 binds the reader | None |
| 4 | **UX-5** | Writes the dual-mode suite (U8), `TRACEABILITY.md`, `QA_REPORT.md`, report notes (U9), on the Prism mock | None (AEA-58 browser journeys are the integrated evidence meanwhile) | Signs UX-5 |
| 5 | **AEA-55** (wave 4) | None (screens frozen; failures go back to the owning phase) | Prism proxy chain (probe J1, C6 first), the UX-5 suite in `proxy` mode, the backend-served smoke, AC-9 through the `data-measure` hooks | ★ "UI verify again" |
| 6 | AEA-56 deploy | — | Image with `dist`, `MERIDIAN_REQUIRE_FRONTEND=true` | Deploys and smoke tests |
