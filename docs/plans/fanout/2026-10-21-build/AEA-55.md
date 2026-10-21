# Plan: [AEA-55] UI integration: `apps/web` against the real backend ("UI verify again")

**Status:** planned. **READY to build once its five blockers are merged** (BLOCKED-ON AEA-51, AEA-52, AEA-53, AEA-58,
AEA-62; see §9). The UX-5 gate is cleared for this ticket by Innocent's statement of 2026-10-21 (relayed by the
orchestrator) and by the checklist *Skips* row "UX-5 first run". The ★ boxes stay Innocent's.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/55 (identical to
`docs/plans/tickets/AEA-55.md`) · **Base revision:** `main` `c9b17ea` (2026-10-21; first written against `ef561fc`) · **Wave:** 5 · **Lane:**
`lane::build-loop` · **Risk:** none (no `risk::security`: plan → implement with tests → review; no frozen tests, no
security agent) · **Gates:** `gate::ux5` (cleared, above), `gate::paid` (AC-10 walkthrough only, Innocent's).
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet).
**Branch / worktree:** the one the orchestrator creates (suggested `aea-55-ui-verify-again` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-55`), cut from `main` after the five blockers merged.

**Refresh, 2026-10-21 (second version).** Re-checked against `main` at `c9b17ea`. Since `ef561fc`, nothing under
`apps/web/`, `tests/journeys/`, `tests/integration/`, `tests/graph/` or `src/meridian/` has changed. The copied
signatures, file contents and checklist line numbers (90, 91, 120, 127, 151; area map line 54) still hold. What changed
in this version:
1. Blocker states (§9). None of the five blockers is merged. AEA-53 is held at NEEDS-DECISION on its plan's R-1 grant.
   AEA-51 and AEA-52 wait on unmerged tickets. Step 0.2 now reads the build ledger, because merge-commit messages vary.
2. `VITE_CACHE_DIR` is now set for **every** `apps/web` command, not only the chain (Step 0.10). Vite and vitest
   therefore never write into the linked `node_modules`.
3. A stop rule for regenerated contract files (Step 7, R-13). Stage 7 decision D-5 has the UX session adding
   `CaseDetail.events.last_event_id` to the OpenAPI.
4. AC-8's spend check now uses the Chicago-day query shape from AEA-53 plan §6.4 (Step 6.7, test 4).
5. Tool versions and `format_wall` are recorded in §4.6.
6. Two sibling files were added to the do-not-touch list: `tests/integration/customer_scripts.py` (AEA-51, proposed
   in AEA-52's plan) and `test_reads_composition.py` (AEA-53).

---

## 1. Goal and sources

### Goal (issue *What to build*, in short)

> Checklist §8's "UI verify again" (ux-pipeline UX-5, second run): the React frontend UX-4 built in `apps/web/` is
> pointed at the real backend, and the UX-5 suite reruns with Prism in **proxy** mode between them, so any backend
> response that breaks a UI contract fails the run. … The report is `docs/testing/ui-verify-again.md`, linked from
> `PROJECT-CHECKLIST.md` §8.

### What it does in practice (input → process → output)

**Input.** One command on the worktree:
`MERIDIAN_UI_VERIFY=1 uv run pytest tests/integration/test_ui_run_records.py -v -s -rs`.

**Process.**
1. A module fixture starts the **real FastAPI app** in-process. It uses AEA-51's `open_customer_run`: a disposable copy
   of the issued DB, the built retrieval index, the scripted model at the provider boundary, and an in-memory trace
   exporter.
2. It probes the proxy chain (AC-14), then starts `prism proxy <OpenAPI> <backend> --errors` on a free port, and a
   **non-mock** Vite dev server whose `/api` goes to Prism.
3. It runs the UX-5 Playwright suite through Vite → Prism → backend with `E2E_TARGET=real`, in fixed invocations,
   each under a hard time cap:
   - the UX session's own `smoke` and `sweep` specs;
   - this ticket's new specs: WP-2, WP-5 and WP-7 driven through the UI; measure pages compared with the responses;
     a two-tab role test; every screen with axe, light and dark, at 1280 and 390, plus grayscale screenshots.
4. It runs Lighthouse's accessibility audit on all 12 screens, and a smoke run against the backend serving the
   production `dist/` at its own URL (AC-5).
5. The tests then read what the backend stored: the code never stored (AC-6), the page numbers equal to SQL counts
   (AC-8), the Prism log with 0 violations (AC-3). After that comes phase B: clock advance, the expired inbox code and
   the demo reset, which wipes chats and therefore runs last.

**Output.**
- Under `var/ui-verify/<stamp>/` (git-ignored): one status per test (`PASS` / `FAIL` / `NOT_RUN` with its reason),
  per-state axe rows, screenshots, Prism and Vite logs and probe results.
- The implementer turns these into `docs/testing/ui-verify-again.md`.
- The journeys (AC-13) run separately and produce `docs/testing/journeys/<date>-AEA-55.md`.

### Context

Stage 8 wave 5. The backend is integrated by AEA-51 (customer graph), AEA-52 (staff side) and AEA-53 (metrics reader).
AEA-49 serves `dist`, AEA-58 and AEA-62 put journeys in the browser, and AEA-57 provides the journey harness.
`apps/web` already has a real-backend mode (`E2E_TARGET=real`, `tests/e2e/support/state.ts` `RealState`) that signs
in through SCR-12, sends no dev parameter, and skips dev-only scenarios with a reason. The UX-5 first run was skipped
by Innocent (no `TRACEABILITY.md`, no `QA_REPORT.md`, no Lighthouse); the second run is not skipped.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-55.md` AC-1…AC-23, *Agent handoff* | Everything below |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-55 (wave 5; blockers 49, 51, 52, 53, 58, 62 + UX-5), §3 collision row `apps/web/**, docs/ux/**` ("55 changes `apps/web` config only after UX-5"), `tests/journeys/` row | Owned files; no edit outside `apps/web` run/test config |
| Checklist | `PROJECT-CHECKLIST.md` §4b line 90–91 (UX-5 first run skipped; gate box unticked), *Skips* row "UX-5 first run" (line 151), §8 lines 120 and 127 | AC-1 basis; AC-23 tick of line 120 only; line 127 is Innocent's ★ |
| Join plan | `docs/plans/ux-join/backend-amendments.md` AEA-55-1 (= AC-14), AEA-55-2 (= AC-15), §3 AEA-55 journey criterion (= AC-13, "runs all") | Probes; NOT_RUN rule; all journeys |
| Rules | `.claude/rules/integrated-journeys.md` §3 rule 3, §4 (levels, nine record fields), §6 last bullet ("The UX-5 suite and AEA-55 keep the visual and accessibility checks. They are not journey evidence where they sign in through dev-only parameters"); `build-loop-test-scope.md` + *AEA addition*; `context-maintenance.md` 3, 6, 7; workspace `code-structure.md` (tests ≤ 500 lines), `code-design-solid-modularity.md` | Levels; record; context rows; file sizes |
| UX-5 recipe | `/home/linuxuser/workspaces/.claude/skills/ux-pipeline/references/phases.md` UX-5 (suite contents, `perl -e 'alarm 500; exec @ARGV'` cap, Lighthouse navigation mode behind sign-in, loop rule, "UX-5 runs twice") | Suite shape; cap; failure routing |
| Contracts (DO-4 addenda win) | `stage7/data.md` §8 (report path DAT-25; the `wrong_role` → re-read `getSession` check, DAT-29 e); `stage7/staff.md` cross-topic apps/web item (R-W-18, STF-19: re-read `getSession` on focus, `visibilitychange` and after **every** 403 `ROLE_NOT_ALLOWED`; never keep staff data after a 403; role panel with `reset = details.reason === "role_reset"`); `stage7/web.md` §6 (gate; 303 with `return_to`), §12 (frontend serving), §13 (`assert_response_matches`) | AC-11; AC-5; response checks |
| Decisions | `docs/plans/7b-decisions/data.md` DAT-24 (scripted fakes for the suite; live models only for AC-10), DAT-25 (report path), DAT-29 e; `web.md` WEB-1 (decided A by D-4, `docs/plans/stage7-signoff.md`), WEB-28 (303 to `/login?return_to=…&reason=none\|expired`), WEB-32 | No paid call in the suite; AC-5 expects the server 303 |
| OpenAPI (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml`: 30 operationIds; security scheme `mhcSession` (cookie `mhc_session`) on every operation except `login`; `LoginRequest{username,password}`, `SwitchRoleRequest{role ∈ customer,representative,supervisor,owner}`, `ResetRequest{confirm: true}`, `StaffingRequest{mode}`, `ClockAdvanceRequest{step ∈ plus_1h,plus_4h,next_business_morning}` | Probe bodies; AC-8 client calls |
| Observability (DO-6) | `docs/design/observability-contract.md` rows WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-18, WF-19 | AC-6 (`request` record per response, code stored as "[code entered]"), AC-8 (reads count, never recompute) |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-18, M-22, M-23, M-24, M-26 as AEA-53 serves them | AC-8 SQL (copied from AEA-53's plan §6.4) |
| Evaluation (DO-5) | `docs/design/evaluation-plan.md` | n/a: no E-n number; AC-10 is compatibility evidence only |
| Sibling plans read (re-read at `c9b17ea`; AEA-53 and AEA-62 were refreshed since `ef561fc`, AEA-52 and AEA-58 are being edited by their planners) | `docs/plans/fanout/2026-10-21-build/AEA-51.md` §4 C1/C2/D1/D2 (`customer_support.py`, `worked_pair_scenarios.py` public API), `AEA-53.md` §4.3–§4.4, §6.4 (wire shapes, SQL), `AEA-58.md` §2, Step 0 (worktree build rule, `MERIDIAN_WEB_DIST_DIR`), `AEA-62.md` §7 C-6 (browser journey command), `AEA-52.md` §2 (owned `tests/integration/` file names) | §4 copies; collision check |
| Current code read | `apps/web/{package.json,playwright.config.ts,vite.config.ts,tsconfig.json,eslint.config.js,.gitignore}`, `apps/web/scripts/{check-dist,check-generated,prism-smoke}.mjs`, `apps/web/tests/e2e/{smoke,sweep,journey-chat-booking-handoff}.spec.ts`, `tests/e2e/support/state.ts`, `src/main.tsx`, `src/state/theme.ts`, `src/screens/reads/{format.ts,MetricTile.tsx,MeasuresTable.tsx,ScreenTitle.tsx}`, `src/screens/scr09/Scr09.tsx`, `scr10/{Scr10,SpendBar}.tsx`, `scr11/{Scr11,EvalMeasuresTable}.tsx`, `scr12/copy.ts`, `scr07/{DemoControls.tsx,copy.ts}`, `scr01/cards/{LocatePromptCard,CodePromptCard}.tsx`, `components/shell/RoleGate.tsx`, `api/useOp.ts`; `tests/journeys/support/{server,run,env,client,db,logtap,plugin,scripted_model}.py`; `tests/conftest.py`; `pyproject.toml`; `src/meridian/web/{errors,logging}.py`, `policy/limits.py` (`WebLimits`, `IdentityLimits.code_ttl_s = 600`), `gates/gate.py` (`CODE_ENTERED`), `domain/common.py` (`HandoffReason`), `services/_case_rules.py` (`reason_label`), `adapters/sqlite/schema/{00_core,40_identity}.sql`; re-read at `c9b17ea`: `apps/web/{vite.config.ts,tsconfig.json,playwright.config.ts,package.json,.gitignore}`, `tests/e2e/support/state.ts`, `tests/journeys/support/{server,run,env,plugin,client,db,logtap,scripted_model}.py`, `src/meridian/adapters/sqlite/db.py` (`format_wall`), `services/ledger.py` (`spend_today`), `services/reset.py` (seed refs MHC-C-0005…0008; MHC-10002 / INV-204411), `adapters/sqlite/repos_identity.py` (`customers(customer_id, name, phone, email)`), the OpenAPI (no `additionalProperties: false`; `CaseDetail` has no `events.last_event_id` yet) | §4 |

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| UX-5 signed before any `apps/web` change | Ticket AC-1; checklist §4b | AC-1 | in-ticket, **basis recorded**: the box is unticked and `docs/ux/05-verify/` does not exist (UX-5 first run skipped by Innocent, *Skips* row). The orchestrator relays Innocent's 2026-10-21 "UX track is done" for this ticket. AC-1 is reported with that basis; it is not ticked by an agent | Step 0.8, Step 13 §14 |
| `TRACEABILITY.md` decides which test covers which flow | Ticket *Evaluation* | AC-4 | in-ticket, **gap**: the file was not produced (skip). The suite is mapped by screen (SCR-1…12) and by AC instead; the report says so | Step 13 |
| Tests tagged `@mock-only` → `NOT_RUN` | AEA-55-2 / AC-15 | AC-15 | in-ticket: no `@mock-only` tag exists in `apps/web`; the equivalent is `RealState`'s `test.skip(…)` with "needs dev-layer forcing" plus the mock-only sweep scenarios. Those are the `NOT_RUN` list | Step 6 (statuses), Step 13 |
| The UX booking journey spec (`journey-chat-booking-handoff.spec.ts`, real mode "never run") | UX-5 suite | AC-4 | in-ticket as **`NOT_RUN` with reason**: a multi-turn booking needs per-turn scripted model steps, and the browser suite cannot change steps between turns. The same path runs in the browser as AEA-62 J-3/J-6 and as AEA-52 J-7 inside AC-13 | Step 6 `NOT_RUN_SPECS`; §8 R-4 |
| Lighthouse accessibility audit | UX-5 recipe | AC-4 | in-ticket: `npx --yes lighthouse@12` (not a project dependency), navigation mode with the session cookie header, desktop preset | Step 5 |
| Real-backend role handling (STF-19) | staff.md cross-topic; data.md §8 | AC-11 | in-ticket | Steps 4.5, 4.7 |
| Records left by UI-driven flows (WF-1, WF-3, WF-6) | DO-6 | AC-6, AC-8 | in-ticket | Step 6 |
| Every response checked against the OpenAPI | integrated-journeys §3 rule 3 | AC-3 | in-ticket (Prism `--errors` log) and plan-added: AC-8's own reads use `JourneyClient.call(..., operation_id=…)`, which runs `assert_response_matches` | Step 6 |
| Context rows in the same change | context-maintenance 3, 6, 7 | AC-23 | in-ticket | Step 14 |
| Live walkthrough on Sonnet and Jev, ≈20 turns, under the cap | DAT-24 | AC-10 | **other: Innocent** (`gate::paid`, ★). The implementer writes the walkthrough section's template and never makes a paid call | Step 13 §13 |
| Deploy | — | — | n/a: AEA-56 | — |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None added or changed (the frontend is a client of the existing routes) | WF-1, 2, 3, 4, 5, 6, 18, 19 driven from the browser | yes (DO-6) | as DO-6 lists |

---

## 2. Boundary

### Owned files (the only files the implementer creates or edits)

| File | Create / modify | Responsibility (one sentence) | Size cap |
|---|---|---|---|
| `apps/web/vite.config.ts` | modify | Two inert run hooks: `API_STREAM_PORT` sends the two SSE paths straight to the backend; `VITE_CACHE_DIR` moves the optimizer cache | — |
| `apps/web/tsconfig.json` | modify (one array entry) | Type-check the new Playwright config | — |
| `apps/web/playwright.ui-verify.config.ts` | create | Playwright config for the real-backend chain and the served-build smoke; starts no server | ≤ 60 |
| `apps/web/tests/ui-verify/support/chain.ts` | create | Shared helpers for the new specs: API capture, axe, themes, screenshots, report rows | ≤ 200 |
| `apps/web/tests/ui-verify/01-wp-flows.spec.ts` | create | WP-2, WP-5, WP-7 and a direct person request through the real UI (AC-6 browser leg, AC-7, AC-16, AC-17, AC-18 code-waiting) | ≤ 300 |
| `apps/web/tests/ui-verify/02-measures.spec.ts` | create | SCR-9, SCR-10, SCR-11 show the API's numbers unchanged (AC-9, AC-21) | ≤ 250 |
| `apps/web/tests/ui-verify/03-role-switch.spec.ts` | create | A staff tab whose role was switched in another tab (AC-11, first half) | ≤ 120 |
| `apps/web/tests/ui-verify/04-screens.spec.ts` | create | Every other screen and reachable state: axe, light/dark, screenshots, grayscale (AC-16, AC-18…AC-20, AC-22) | ≤ 250 |
| `apps/web/tests/ui-verify/90-clock-and-inbox.spec.ts` | create | Phase B: expired code on SCR-2, SCR-3 after a clock advance (AC-18, AC-20) | ≤ 120 |
| `apps/web/tests/ui-verify/99-role-reset.spec.ts` | create | Phase B: the same tab after a CON-9 reset gets `role_reset` and the role picker (AC-11, second half) | ≤ 100 |
| `apps/web/tests/ui-verify/served-smoke.spec.ts` | create | The backend-served build behind the real login (AC-5) | ≤ 100 |
| `apps/web/scripts/ui-verify-lighthouse.mjs` | create | Lighthouse accessibility audit of the 12 screens through the chain | ≤ 120 |
| `tests/integration/test_ui_run_records.py` | create | The chain fixture and the record checks (AC-3, AC-4 completion, AC-6, AC-8, AC-11 phase B, AC-14, AC-15) | ≤ 500 (hard) |
| `docs/testing/ui-verify-again.md` | create | The UX-5 second-run report (DAT-25) | — |
| `docs/testing/journeys/<run-date>-AEA-55.md` | create (written by `--journey-record=AEA-55`, then edited) | AC-13 record | — |
| `PROJECT-CHECKLIST.md` | modify **line 120 only** (§8 "Frontend: one integration step per contract …") | AC-23 tick + evidence link | — |
| `.claude/reference/area-map.md` | modify **the *Screens* paragraph only** (line 54 today) | AC-23 | — |
| `.claude/state/icm-progress.md` | modify: **add one** "Routes verified against code and tests" row | AC-23 | ≤ 400 chars |

Temporary, never committed: the symlink `apps/web/node_modules` (Step 0.6), everything under `var/ui-verify/`,
`apps/web/dist`, `apps/web/.tmp`, `apps/web/test-results`, `apps/web/tsconfig.tsbuildinfo` (all git-ignored).

### Shared surfaces: read and import, never edit

- `apps/web/src/**`: screens, components, `src/api/types.gen.ts`, `contract.gen.json`.
- The UX session's specs: `apps/web/tests/e2e/**`, including `support/state.ts`, which is imported, and the tracked
  `.gen/*.json` files.
- `apps/web/{package.json,package-lock.json,playwright.config.ts,eslint.config.js}`, `apps/web/scripts/*` (except the
  new `ui-verify-lighthouse.mjs`).
- `docs/ux/**`, `docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`.
- `src/meridian/**`, `tests/journeys/**` (support, browser, all journey files), `tests/integration/customer_support.py`,
  `customer_api.py`, `staff_support.py`, `staff_streams_support.py` (AEA-51/52; import only), `tests/graph/**`,
  `tests/api/openapi_check.py`, `tests/conftest.py`, `pyproject.toml`, `uv.lock`.
- The briefing, issued data, `docs/archive/`, `docs/parked/`.

### Owned by other slices (do not touch)

`tests/integration/{customer_support,customer_api,customer_scripts,test_customer_*,test_relayed_turn}.py` (AEA-51;
`customer_scripts.py` is proposed in AEA-52's plan), `tests/integration/test_reads_composition.py` (AEA-53),
`tests/integration/{staff_support,staff_streams_support,test_staff_*,test_demo_reset}.py` (AEA-52),
`tests/journeys/browser/**` (AEA-58), `tests/journeys/j*/test_aea_*.py` (each ticket), `tests/capture/**` (51, 52, 53,
24, 50), `docs/plans/ux-join/selectors.md` (UX session).

---

## 3. Requirements table

Level column: the integrated-journeys §4 level the evidence can claim. The UX-5 rerun passes through Prism proxy and a
dev server, so it is reported in its own right, not as journey evidence (§6). "Phase A" and "phase B" are the two
Playwright phases of the fixture (Step 6).

| ID | Kind | Requirement (short) | How it is built | Verify (test / command) | Level |
|---|---|---|---|---|---|
| AC-1 | failure/refusal | No `apps/web` change before UX-5 is signed | Step 0.8 records `grep -n "UX-5 signed off\|UX-5 first run" PROJECT-CHECKLIST.md` and `ls docs/ux/05-verify/` (absent) plus the orchestrator's relay of Innocent's 2026-10-21 statement; the report's §14 states the basis | Commands in Step 0.8; report §14 | n/a (gate) |
| AC-2 | invariant | Types regenerate with no diff; production build passes; no mock-only code in `dist` | No change to `src/`; new TS must type-check because `tsc -b` includes `tests/` | `cd apps/web && npm run check:gen && npm run build && npm run check:dist` → exit 0 each; `git diff --name-only -- apps/web/src` empty | static |
| AC-3 | invariant | 0 Prism violations over the full run | Run Prism writes `var/ui-verify/<stamp>/prism-proxy.log` | `test_ui_run_records.py::test_prism_log_has_no_violations` → no line containing `Violation:` | UX-5 rerun |
| AC-4 | invariant | UX-5 suite through the chain; every check ends PASS/FAIL/NOT_RUN/NEEDS_HUMAN_REVIEW; mock-only states NOT_RUN | Fixture phase A + B invocations (Step 6) under `perl -e 'alarm 500; exec @ARGV'`; `statuses.json`; Lighthouse summary | `::test_suite_completed_through_the_chain` (every test has a status; every `ui-verify/` spec PASS; `run.script.problems() == ()`; 12 Lighthouse rows) + report §5 | UX-5 rerun |
| AC-5 | failure/refusal | Backend-served build at one origin behind the real login | `served-smoke.spec.ts` on project `served-build` against a second app instance with `MERIDIAN_WEB_DIST_DIR=apps/web/dist`, `MERIDIAN_REQUIRE_FRONTEND=true` | Fixture invocation `served-build`; status PASS in `statuses.json`; screenshots `served-*.png` | integrated with a scripted model (real login, production build; no Prism) |
| AC-6 | capture | WP-2 through the UI: stored chat holds "[code entered]"; code in no DB text column, file, log line or span; every API response carries `X-Request-ID` matching a `request` record | TS WP-2 test writes `capture/wp2-chrome-desktop.json` (thread id, **sha256 of the code**, API exchanges); Python scans by hash | `tests/integration/test_ui_run_records.py::test_wp2_through_ui_leaves_no_code` → 0 hits; 0 missing request ids | UX-5 rerun (records from the real backend) |
| AC-7 | invariant | WP-5 safety instruction first on SCR-1; WP-7 promise + reference, same reference in SCR-5 beside MHC-C-0005…0008 | `01-wp-flows.spec.ts` tests "WP-5 …", "WP-7 …" | Their PASS in `statuses.json`; `capture/wp5-*.json`, `wp7-*.json` | UX-5 rerun |
| AC-8 | capture | CON-18 and CON-19 equal direct counts after WP-2/5/7 (volume, handoffs by reason, failures, latency sample size, spend) | Python reads CON-18/19 with its own login (owner) and compares with AEA-53's §6.4 SQL | `tests/integration/test_ui_run_records.py::test_reads_equal_records_after_flows` → 0 mismatches; per-measure table printed | integrated (real reader over records the UI left) |
| AC-9 | invariant | SCR-9/10/11 show the API's numbers unchanged; thresholds only as labelled alert settings | `02-measures.spec.ts`: response captured with `waitForResponse`, DOM compared through the page's own display formatters | Its 3 tests PASS × 2 projects; `capture/measures-SCR-*-*.json` with `mismatches: []` | UX-5 rerun |
| AC-10 | invariant | Innocent's live walkthrough; ★ "UI verify again" | **Not the implementer's**: report §13 is a template with tasks, fields and the launch command | Innocent | verified with live models (his run) |
| AC-11 | failure/refusal | Tab whose role was switched elsewhere → 403 `wrong_role`, re-reads `getSession`, role panel; after CON-9 reset → `role_reset`, role picker | `03-role-switch.spec.ts` (phase A), `99-role-reset.spec.ts` (phase B) | PASS of both; `capture/role-switch-*.json`, `capture/role-reset.json`; `::test_role_reset_and_clock_phase` | UX-5 rerun |
| AC-12 | negative | Not bound 4019/5184; diff only in owned files; demo password in no diff file | Free ports chosen by the fixture and asserted ∉ {4019, 5184}; `ss -ltn` saved; demo pair random per run (`journey_environ`) | `ports.txt`; `git diff --name-only main...HEAD` matches §2; `::test_prism_log_has_no_violations` also scans the output tree for secrets | static |
| AC-13 | **journey** | All journeys J-1…J-10 (API + AEA-58/62 browser legs) on the integrated branch after the run-config change and before the UX-5 rerun, at `integrated with a scripted model`; UX-5 rerun reported separately | Step 10 command | `perl -e 'alarm 1800; exec @ARGV' uv run pytest -m journey --journeys-strict --browser-channel chrome --journey-record=AEA-55 -rs` + `CONTRACT_STRICT=1 uv run pytest tests/contract -q -rs`; record `docs/testing/journeys/<date>-AEA-55.md` | **integrated with a scripted model** |
| AC-14 | invariant | Probes: (1) chat and case streams first frame ≤ 20 s through Prism, else route both streams to the backend; (2) cookieless `getChatThread` → backend `ApiError` 401 `UNAUTHENTICATED`, else Prism request validation off; (3) `MERIDIAN_COOKIE_SECURE=false`; (4) `[contract drift]` is mock-only | Fixture Step 6.8 on a separate probe Prism; `probes.json` | `::test_proxy_chain_probes`; report §3 | UX-5 rerun |
| AC-15 | negative | `@mock-only`-equivalent tests NOT_RUN with reasons; no dev query parameter in any request; sign-in only via SCR-12 with the env pair | `statuses.json` skip reasons; `devParamHits` in every new spec; Prism-log grep | `::test_prism_log_has_no_violations` (grep part); report §6 | UX-5 rerun |
| AC-16 | invariant | WF-1 SCR-1 states: axe 0 WCAG 2.2 AA (incl. contrast) at 1280/390, light/dark; grayscale shows state; WP-5 first | `checkState` in `01-wp-flows` and `04-screens` | `rows.jsonl` rows `AC-16`; grayscale review (Step 12) | UX-5 rerun |
| AC-17 | invariant | WF-2 SCR-1 handoff card + follow-up control after WP-7 and after a direct person request | `01-wp-flows` WP-7 and "person request" tests | rows `AC-17` | UX-5 rerun |
| AC-18 | invariant | WF-3 SCR-2 code waiting (axe, **no screenshot**) and expired (axe + screenshots + grayscale) | WP-2 test (code waiting), `90-clock-and-inbox` (expired) | rows `AC-18` | UX-5 rerun |
| AC-19 | invariant | WF-4 SCR-4…SCR-8; P0 safety row first; text beside colour | `04-screens` | rows `AC-19`; the SCR-5 "Safety first" assertion | UX-5 rerun |
| AC-20 | invariant | WF-5 SCR-3 nobody online, simulated staff on shift, after a clock advance | `04-screens` (two staffing states), `90-clock-and-inbox` | rows `AC-20` | UX-5 rerun |
| AC-21 | invariant | WF-6 SCR-9…SCR-11 after AC-8's flows | `02-measures` `checkState` | rows `AC-21` | UX-5 rerun |
| AC-22 | invariant | WF-18 SCR-12 empty, wrong pair (refusal line), session ended | `04-screens` SCR-12 test | rows `AC-22` | UX-5 rerun |
| AC-23 | regression/context | Checklist §8 line 120 ticked with evidence; area-map *Screens* note; ICM routes-verified row | Step 14 | `git diff --name-only` shows the three files | n/a |
| PA-1 (plan-added) | invariant | No secret (demo pair, session secret) in any file of the run output | Python scan of `var/ui-verify/<stamp>/` | `::test_prism_log_has_no_violations` | static |

**The ticket's WP-N pair:** WP-2 is primary: TS test "WP-2 …" plus `test_wp2_through_ui_leaves_no_code`. WP-5 and
WP-7 are the other two named pairs. **The `[journey]` criterion** is AC-13, at level `integrated with a scripted model`.

---

## 4. Shared code to use (copied from the current code and the merged siblings)

### 4.1 On `main` now (AEA-57 harness, AEA-23, config)

```python
# tests/journeys/support/server.py
FORBIDDEN_PORTS: frozenset[int] = frozenset({4019, 5184})
@contextmanager
def launch_server(settings: Settings, *, overrides: ContainerOverrides | None, startup_timeout_s: float = 30.0) -> Iterator[RunningServer]
class RunningServer: app; container; host: str; port: int; thread; @property base_url -> "http://127.0.0.1:<port>"

# tests/journeys/support/env.py
def journey_environ(root: Path) -> dict[str, str]
#   keys: ANTHROPIC_API_KEY, OPENROUTER_API_KEY (placeholders), MERIDIAN_DEMO_USERNAME ("journeyuser"+8 letters),
#   MERIDIAN_DEMO_PASSWORD ("journeypass"+20 letters), MERIDIAN_SESSION_SECRET, MERIDIAN_COOKIE_SECURE="false",
#   MERIDIAN_REQUIRE_FRONTEND="false", MERIDIAN_WEB_DIST_DIR=str(root/"no-dist"), MERIDIAN_DATA_DIR=str(root/"data"),
#   MERIDIAN_INDEX_DIR=str(root/"index")
class JourneyEnv: root; data_dir; web_dist_dir; index_dir; settings; issued_sha256_before; db_path; secret_values() -> (demo password, session secret)

# tests/journeys/support/run.py
class JourneyRun: env; server; script; models; clock; db: DbReader; logs: LogTap; guard; collector; strict; nodeid
    settings; app; container; base_url; demo_username (str); secret_values(); client() -> JourneyClient
    login(client=None) -> LoginResult(client, response, session_id, cookie)   # POST /api/login, asserts 200 + one new staff_sessions row

# tests/journeys/support/client.py
class JourneyClient:
    def call(self, method: str, path: str, *, operation_id: str | None, body: object | None = None,
             headers: Mapping[str, str] | None = None) -> httpx.Response   # runs assert_response_matches(response, operation_id)

# tests/journeys/support/db.py
class DbReader: rows(sql, params=()) -> list[dict]; one(sql, params=()) -> dict; scalar(sql, params=()) -> Any

# tests/journeys/support/logtap.py
class LogTap: structured(kind: str) -> list[dict[str, object]]; all_text() -> str
#   "request" records carry: record, request_id, route, status, duration_ms, caller_role, thread_id[, error_kind]

# tests/journeys/support/scripted_model.py
class JourneyScript: calls; problems() -> tuple[ScriptedCall, ...]   # calls whose result is "invalid_output" or "exhausted"
class ScriptedCall: role: Role; method; request; timeout_s; result

# src/meridian
from meridian.config import Settings            # Settings.from_env(environ); demo_username/demo_password: SecretStr; cookie_secure: bool
from meridian.domain.common import HandoffReason, Role   # Role.PLANNER, CLASSIFIER, PLANNER_FALLBACK, RESPONDER, BRIEF, SPECIALIST
from meridian.gates.gate import CODE_ENTERED     # Final = "[code entered]"
# meridian.web.errors: REQUEST_ID_HEADER = "X-Request-ID"; ApiError body = {"error": {"code", "field", "constraint", "details"}, "request_id"}
# policy/limits.py WebLimits: login_rejects_per_ip = 10 per 600 s; reads_per_ip_per_min = 240; IdentityLimits.code_ttl_s = 600
```

Tables and columns the checks read (schema on `main`): `messages(thread_id, role, text, kind ∈ text|choice|code|form)`,
`conversations(thread_id, run_tag, outcome, …)`, `turns(thread_id, run_tag, outcome, degrade_reason, server_ms, …)`,
`cases(case_ref, thread_id, reason, seed, …)`, `spend_ledger(cost_usd, recorded_at, …)`, `identity_codes(code_hmac,
…)` (the code is stored only as an HMAC), `demo_inbox(…)` (no code column), `customers(customer_id, name, phone, …)`.

### 4.2 From AEA-51 (merged before this ticket; names from its plan §4 C1 and D1 — **verify at Step 0.3**)

```python
# tests/integration/customer_support.py
StepEntry = ScriptEntry | Stall | tuple[ScriptEntry | Stall, ...]
class StepScript(JourneyScript):
    def set_step(self, default: Mapping[Role, StepEntry], *, by_marker: Mapping[str, Mapping[Role, StepEntry]] | None = None) -> None
    # one entry answers every call of its role; a tuple is consumed in call order (SPECIALIST: indexed by tool round);
    # by_marker: the FIRST marker (insertion order) found in the request JSON whose table has the role wins; set_step resets counters
def step_overrides(settings: Settings, script: StepScript, *, wall_clock=None, trace=None) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]
@dataclass(frozen=True)
class RunOptions: index: Literal["built", "empty"] = "built"; eval_key: bool = False; trace: TraceSink | None = None; with_clock: bool = False; deadline_s: int | None = None
class CustomerRun(JourneyRun): eval_key: str | None; @property steps -> StepScript
@contextmanager
def open_customer_run(request: pytest.FixtureRequest, options: RunOptions = RunOptions(), *, monkeypatch=None) -> Iterator[CustomerRun]
def build_capture_sink(registry: list[Any]) -> tuple[TraceSink, InMemorySpanExporter]
def finished_spans(sink: TraceSink, exporter: InMemorySpanExporter) -> list[ReadableSpan]

# tests/graph/worked_pair_scenarios.py
def planner(**choices: str) -> str        # PlannerChoices JSON; defaults knowledge="no", account="none", scheduling="none", handoff="none", topic="other"
def classifier(label: str) -> str
def responder(text: str) -> str
def brief(**fields: Any) -> str
def tool(name: str, args: Mapping[str, Any], call_id: str = "call-1") -> RawToolCall
def report(model: type, **fields: Any) -> RawToolCall
def step(*calls: RawToolCall, text: str = "") -> RawToolStep
NORMAL: str                                # classifier "normal"
TOOLS: Mapping[str, str]                  # "invoice" -> READ_INVOICES_NAME, …
def wp2(run, client=None) -> ScenarioResult;  def wp5(...);  def wp7(...)   # drivers: their run.steps.set_step(...) calls per turn are the source of the entries copied in Step 6.4
```

### 4.3 From AEA-53 (merged before this ticket)

- `MetricsReader` served by `GET /api/staff/owner-metrics` (`getOwnerMetrics`, roles owner and supervisor) and
  `GET /api/monitoring` (`getMonitoring`, any signed-in role).
- `reason_label`: import it from the **same module `src/meridian/services/metrics_reader.py` imports it from** (today
  it is defined in `meridian.services._case_rules`; Step 0.4 greps).
- Wire shapes (AEA-53 plan §4.3):
  - `Measure{id, label, numerator, denominator, unit, value, null_reason, kind, case_refs}`;
  - `Tile{id, label, value, unit, numerator, denominator, null_reason}`;
  - CON-18 fields `in_scope_correct_resolution`, `promises_kept_on_time`, `handoffs` (`Measure`), `outcomes[]`,
    `handoffs_by_reason[]`, `missed_promises[]`, `cases[]`;
  - CON-19 fields `health[Tile]` with labels `Conversations`, `Turns`, `Failures`, `Latency p50`, `Latency p95`,
    `Overdue job last ran`, `Handoff-only mode (1 = on)`; `spend{today_cents, cap_cents, day, resets_at}`;
    `correctness{containment_estimate: Tile, escalations_by_reason[Tile]}`; `alerts[]`; `trace_export: str`.
- CON-18 outcome labels: `Resolved by the AI` = `ai_resolved`, `Handed off to a person` = `handed_off`,
  `Safety reply given` = `safety_reply`, `Abandoned` = `abandoned`.
- Latency null reasons: `No turns yet` (0 values) and `Not enough turns yet (fewer than 20)` (fewer than 20).
  Nearest rank: `sorted[ceil(q·n) − 1]`.

### 4.4 `apps/web` (read only; used by the new specs)

```ts
// tests/e2e/support/state.ts (UX session): import { state, atPath, ROLE_RADIO, type Role } from "../e2e/support/state"
//   state.target === "real" when E2E_TARGET=real. RealState:
//   signInAs(page, role, path, opts?)  — clears cookies, signs in through /login with E2E_USERNAME/E2E_PASSWORD, switches
//                                        role through the "Acting as" radiogroup, then goes to `path`; opts.scenario → test.skip
//   visitSignedOut(page, path); setStaffing(page, on) — via /demo switch "Demo: simulate staff on shift";
//   reset(page) — /demo → button "Reset the demo" → dialog "Reset the demo?" → confirm
// src/screens/reads/format.ts (import for expected display values; type-only import inside is erased):
export function formatShare(value: number | null): string   // null → "—"; else `${Math.round(value*100)}%`
export function formatCount(n: number | null): string
export function nOfN(numerator: number | null, denominator: number | null, noun: string): string // null den → "—"; 0 → `0 ${noun}`; else `${num ?? 0} of ${den} ${noun}`
export function formatSeconds(ms: number | null): string     // `${(ms/1000).toFixed(1)} s`
export function formatCents(cents: number): string           // `$${(cents/100).toFixed(2)}`
export function formatTileValue(t: { value: number | null; unit: string }): string
```

Accessible names and copy used as **expected values or role/label locators** (from the components on `main`):
- Composer: textbox `Message`, button `Send` (exact), button `Talk to a person`.
- The conversation is `role=log` named `Conversation`, with one `[data-entry]` per entry.
- Locate card fields are labelled `Name on the account`, `Phone`, `Customer ID`, `Invoice number`; its submit
  button is `Send the code`.
- Code card: field `6-digit code`, button `Verify` (exact).
- Role switch: radiogroup `Acting as`, with radios matching `ROLE_RADIO` (`/Customer/`, `/Riley/`, `/supervisor/i`,
  `/owner/i`).
- SCR-12: `Username`, `Password` (exact), button `Sign in`. Refusal: "That username or password didn't work. Check
  the README and try again." Ended: "Your demo session ended, so please sign in again."
- Role panel: "You're acting as the customer. Switch to a staff role to see this." and "The demo was reset, so you're
  back to the customer role. Pick a role again."
- h1 texts: `Representative queue` (SCR-5), `Business-owner outcomes` (SCR-9), `Monitoring` (SCR-10),
  `Evaluation report` (SCR-11).
- SCR-10 cards: `section[aria-label="Health"]` and `section[aria-label="Correctness"]` (role `region`). Each
  `CardRow` is a `div` whose first child `div` holds a `span` (label) and an optional `p` (hint); its second child
  `div` holds the value. The spend row reads `"$x.xx of $y.yy daily cap"`.
- SCR-9 tables are captioned `Outcomes of stored conversations` and `Handoffs by reason`. Their rows are
  `th[scope=row]` (label) followed by `td` (count, `nOfN`) and `td` (share, `formatShare`, plus the null reason).
  SCR-9 tiles are `section[aria-labelledby]` with an h2 = `Measure.label`, a value `.t-time-hero`, and a line `nOfN`.
  Nouns: `in-scope conversations`, `promises due`, `conversations`; tables use `conversations` / `handoffs`.
- SCR-11 cells: `nOfN(num, den, "held-out cases" | "dev cases")` and `formatShare`.
  Empty: "No evaluation run yet."
- SCR-7 *Demo controls* disclosure: buttons `+1 hour`, `+4 hours`,
  `Next business morning (Mon 7:00 am)`. SCR-3 switch: `Demo: simulate staff on shift`.
- SCR-2 status words: `Active`, `Used`, `Expired`.
- Theme: `localStorage["mhc.theme"] = "light" | "dark"`, applied at load to `html[data-theme]`; light is the default.

### 4.5 Request bodies used directly (OpenAPI)

`POST /api/login {"username", "password"}` → 200 + `Set-Cookie: mhc_session=…` · `POST /api/chat/sessions` (no body) →
201 `{"thread_id", …}` · `PUT /api/session/role {"role": "representative" | "owner" | …}` → 200 ·
`GET /api/chat/sessions/{thread_id}/events` and `GET /api/staff/cases/{reference}/events` (SSE, heartbeat every 15 s) ·
`GET /api/chat/sessions/{thread_id}` without a cookie → 401 `{"error": {"code": "UNAUTHENTICATED", …}, "request_id"}`.

### 4.6 Versions and one storage helper (read at `c9b17ea`)

- Node packages in the primary checkout's `apps/web/node_modules`: `vite` 6.4.5, `vitest` 3.2.7, `@playwright/test`
  1.64.1, `@axe-core/playwright` 4.14.0, `@stoplight/prism-cli` 5.15.11, `typescript` 5.8.3. Prism 5's `proxy`
  command takes `-h`, `-p`, `--errors` and `--validate-request=false`.
- `npm run typecheck`, `npm run test` and `npm run build` each run `gen:types` and `examples` first. Those rewrite the
  tracked `src/api/types.gen.ts` and `src/api/contract.gen.json` from the OpenAPI (Step 7 stop rule).
- The OpenAPI has no `additionalProperties: false`. An extra field in a backend response is therefore not a Prism
  violation, but a missing required field or a wrong type is.

```python
# src/meridian/adapters/sqlite/db.py
def format_wall(dt: datetime) -> str:   # "The one wall-time format: UTC ISO-8601 (MC-20)"; raises ValueError on a naive datetime
# services/ledger.py: LedgerService.spend_today() sums spend_ledger.cost_usd between the Chicago-day bounds of its wall clock
```

---

## 5. Steps

Cheapest checks first; stop at the first red. Every command runs from the worktree root unless it says
`cd apps/web`. Never run `npm run dev`, `dev:mock`, `mock`, `smoke:mock`, `test:e2e`, or `npx playwright test` with the
default config: they bind 5184 or 4019.

### Step 0 — environment and preconditions (no code)

1. `export UV_LINK_MODE=hardlink`; `df -h /home` (stop and report if under 5 GB free).
2. Blockers merged:
   `awk -F'|' '$2 ~ /^ AEA-(51|52|53|58|62) $/ {print $2 $5}' .claude/state/build-ledger.md` must print five rows,
   each with state `merged`. The merge step maintains the ledger; merge-commit messages vary
   (`Merge AEA-57 …`, `Merge aea-24-…`), so do not grep `git log`. If any row is not `merged`, **stop: BLOCKED-ON**
   that ticket.
3. AEA-51's API is as §4.2 says:
   `grep -nE "^def (open_customer_run|step_overrides|build_capture_sink|finished_spans)|^class (StepScript|RunOptions|CustomerRun)" tests/integration/customer_support.py`
   and
   `grep -nE "^def (planner|classifier|responder|brief|tool|report|step|wp2|wp5|wp7)\b|^(NORMAL|TOOLS)\b" tests/graph/worked_pair_scenarios.py`.
   If a name is missing or its signature differs from §4.2, **stop and report** (the plan goes back to the planner).
4. AEA-53: `grep -n "reason_label" src/meridian/services/metrics_reader.py` → note the import line; use the same
   module in Step 6.
5. AEA-58: `uv run python -c "import pytest_playwright"` exits 0.
6. `node_modules` without a copy. This ticket must run Node in its own worktree because it edits `apps/web` config.
   The rule "no node_modules in a backend worktree" is about copies and disk, so **link** the primary checkout's
   folder:
   `test -e apps/web/node_modules || ln -s /home/linuxuser/workspaces/inno-aea-callcenter/apps/web/node_modules apps/web/node_modules && test -L apps/web/node_modules`.
   - Never `npm install`, `npm ci`, `npx playwright install` or `npm update`.
   - The link is git-ignored (`node_modules`).
   - Remove it at the end with `unlink apps/web/node_modules`. Never use `rm -r` and never add a trailing slash: that
     would delete the primary checkout's modules.
7. `cd apps/web && npx --yes lighthouse@12 --version` (caches Lighthouse in `~/.npm/_npx`; record the version). If it
   cannot be fetched, Lighthouse rows become `NOT_RUN` with that reason. Nothing else changes.
8. AC-1 evidence: `grep -n "UX-5 signed off\|UX-5 first run" PROJECT-CHECKLIST.md` and `ls docs/ux/05-verify/ 2>&1`.
   Save both outputs for report §14. **Do not tick anything.**
9. `ls /usr/bin/google-chrome`, `which perl ss` must succeed.
10. In every shell that runs an `apps/web` command (`npm run typecheck|lint|test|build|check:gen|check:dist`, `npx`),
    first run `export VITE_CACHE_DIR="$PWD/var/ui-verify/vite-cache-cli"` from the worktree root. *Invariant:* Vite and
    vitest keep their cache under this worktree's ignored `var/`. They never write into the primary checkout's
    `node_modules/.vite` through the link. The chain sets its own value (Step 6.6, item 7).

### Step 1 — `apps/web/vite.config.ts` and `apps/web/tsconfig.json`

Replace `vite.config.ts` with exactly this (mock behaviour and the vitest block unchanged):

```ts
/// <reference types="vitest/config" />
import { defineConfig, type ProxyOptions } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";

// AEA-55 (UI verify again): two run-configuration hooks, both inert unless their variable is set.
//   API_STREAM_PORT  sends the two SSE paths straight to the backend when Prism's proxy cannot stream them (AEA-55 AC-14).
//   VITE_CACHE_DIR   keeps the dependency-optimizer cache out of a node_modules shared through a link.
const STREAM_PATHS = ["^/api/chat/sessions/[^/?]+/events(\\?.*)?$", "^/api/staff/cases/[^/?]+/events(\\?.*)?$"];

export default defineConfig(({ mode }) => {
  const mock = mode === "mock";
  const target = mock ? `http://127.0.0.1:${process.env.MOCK_PORT ?? "4019"}` : `http://127.0.0.1:${process.env.API_PORT ?? "8000"}`;
  const proxy: Record<string, ProxyOptions> = {};
  const streamPort = mock ? undefined : process.env.API_STREAM_PORT;
  if (streamPort) for (const p of STREAM_PATHS) proxy[p] = { target: `http://127.0.0.1:${streamPort}`, changeOrigin: true };
  proxy["/api"] = { target, changeOrigin: true }; // after the stream keys: Vite uses the first matching key
  return {
    plugins: [react(), tailwindcss()],
    cacheDir: process.env.VITE_CACHE_DIR || undefined,
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: { proxy },
    test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"], include: ["src/**/*.test.{ts,tsx}"], restoreMocks: true },
  };
});
```

Invariant: with neither variable set, the proxy is `{"/api": {target, changeOrigin: true}}`, exactly as before.

`tsconfig.json`: change `"include": ["src", "tests", "playwright.config.ts", "vite.config.ts"]` to
`"include": ["src", "tests", "playwright.config.ts", "playwright.ui-verify.config.ts", "vite.config.ts"]`. Nothing else.

Check: `cd apps/web && npm run typecheck && npm run lint && npm run test` (vitest; `vite.config.ts` changed) → all
green.

### Step 2 — `apps/web/playwright.ui-verify.config.ts`

```ts
import { defineConfig } from "@playwright/test";
import path from "node:path";

// AEA-55 "UI verify again": the UX-5 suite against the REAL backend. Starts no server. tests/integration/test_ui_run_records.py
// starts the backend, `prism proxy … --errors` in front of it and a non-mock Vite whose /api goes to Prism, then runs this
// config with E2E_BASE_URL = that Vite. Project served-build targets the backend's own URL (production dist, no Vite, no Prism).
if (process.env.E2E_TARGET !== "real") throw new Error("playwright.ui-verify.config.ts runs only with E2E_TARGET=real");
const out = process.env.UI_VERIFY_OUT;
const base = {
  channel: "chrome", locale: "en-US", timezoneId: "America/Chicago", reducedMotion: "reduce" as const,
  trace: "off" as const, video: "off" as const, screenshot: "off" as const, baseURL: process.env.E2E_BASE_URL,
};
const SERVED = /served-smoke\.spec\.ts$/;

export default defineConfig({
  testDir: "tests",
  timeout: 120_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  outputDir: out ? path.join(out, "pw-output") : "test-results/ui-verify",
  reporter: [["list"], ["json", { outputFile: process.env.UI_VERIFY_JSON ?? "test-results/ui-verify.json" }]],
  projects: [
    { name: "chrome-desktop", testIgnore: SERVED, use: { ...base, viewport: { width: 1280, height: 800 } } },
    { name: "chrome-phone", testIgnore: SERVED, use: { ...base, viewport: { width: 390, height: 844 } } },
    { name: "served-build", testMatch: SERVED, use: { ...base, baseURL: process.env.E2E_SERVED_URL, viewport: { width: 1280, height: 800 } } },
  ],
});
```

No traces, videos or automatic screenshots: they would hold typed text, including the password field.

### Step 3 — `apps/web/tests/ui-verify/support/chain.ts`

Exports, exactly these names. The file's first line is a comment: `// AEA-55: helpers for the UI-verify-again specs
(real backend through Prism proxy). Never imports src/dev.`

```ts
import { createHash } from "node:crypto";
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

export function env(name: string): string                 // throws Error(`${name} is required (set by tests/integration/test_ui_run_records.py)`) when unset
export const OUT: string                                   // env("UI_VERIFY_OUT"); mkdirSync of OUT/capture, OUT/screens, OUT/gray at module load
export const DEV_PARAMS = ["signedin", "role", "scenario", "staffing", "ex", "delay"] as const;
export const AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
export type Result = "PASS" | "FAIL" | "NOT_RUN" | "NEEDS_HUMAN_REVIEW";
export interface ApiExchange { method: string; path: string; query: string; status: number; requestId: string | null }

export function recordApi(page: Page, into: ApiExchange[]): void
//   page.on("response", r => { const u = new URL(r.url()); if (!u.pathname.startsWith("/api/")) return;
//     into.push({ method: r.request().method(), path: u.pathname, query: u.search, status: r.status(), requestId: r.headers()["x-request-id"] ?? null }); })
export function devParamHits(xs: ApiExchange[], urls: string[] = []): string[]
//   every exchange query and every url whose URLSearchParams has a key in DEV_PARAMS → "<path>?<key>"
export const sha256 = (s: string): string => createHash("sha256").update(s, "utf8").digest("hex");
export function writeJson(name: string, data: unknown): void      // OUT/capture/<name>.json, JSON.stringify(data, null, 1)
export function row(r: { check: string; screen: string; state: string; project: string; theme: string; result: Result;
                         axe: string[]; shot: string; gray: string; evidence: string }): void   // appends one JSON line to OUT/rows.jsonl
export async function axeViolations(page: Page): Promise<string[]>
//   (await new AxeBuilder({ page }).withTags(AXE_TAGS).analyze()).violations.map(v => `${v.id} (${v.nodes.length}): ${v.nodes[0]?.target.join(" ") ?? ""}`)
export const radios = (page: Page) => page.getByRole("radiogroup", { name: "Acting as" }).first();
export const conversation = (page: Page) => page.getByRole("log", { name: "Conversation" });
export const entries = (page: Page) => conversation(page).locator("[data-entry]");
export async function send(page: Page, text: string): Promise<void>
//   await expect(async () => { await page.getByRole("textbox", { name: "Message" }).fill(text);
//     await page.getByRole("button", { name: "Send", exact: true }).click({ timeout: 2_000 }); }).toPass({ timeout: 15_000 });
export function startedThread(page: Page): Promise<string>
//   page.waitForResponse(r => new URL(r.url()).pathname === "/api/chat/sessions" && r.request().method() === "POST" && r.status() === 201,
//     { timeout: 30_000 }).then(async r => String((await r.json()).thread_id))   — create it BEFORE signing in
export async function fillLocate(page: Page): Promise<void>
//   for [label, value] of [["Name on the account", env("E2E_CUSTOMER_NAME")], ["Phone", env("E2E_CUSTOMER_PHONE")],
//     ["Customer ID", "MHC-10002"], ["Invoice number", "INV-204411"]]:
//     const f = page.getByLabel(label, { exact: true }).last(); if (await f.isVisible()) await f.fill(value);
//   then click page.getByRole("button", { name: "Send the code" }).last()
export async function checkState(page: Page, s: { check: string; screen: string; state: string; noShot?: boolean;
                                  secret?: string; reach?: (p: Page) => Promise<void> }): Promise<string[]>
```

`checkState` algorithm (the invariant each step protects):
1. `const project = test.info().project.name; const problems: string[] = []`.
2. For `theme` of `["light", "dark"]`:
   1. `await page.evaluate(t => localStorage.setItem("mhc.theme", t), theme)`. The page is already on the app origin
      because every caller has navigated first.
   2. `await (s.reach ?? (p => p.reload().then(() => undefined)))(page)`. *Invariant:* the state is reached, or
      reloaded, with the theme already stored. States that do not survive a reload (SCR-12 wrong pair) pass a `reach`
      that recreates them.
   3. `await expect(page.locator("html")).toHaveAttribute("data-theme", theme)`; then
      `await page.locator("h1").first().waitFor({ timeout: 15_000 })`, then `await page.waitForTimeout(500)`. Never
      wait for `networkidle`: the SSE streams keep the network busy.
   4. `const v = await axeViolations(page)`.
   5. `const text = await page.locator("body").innerText()`. `const shoot = !s.noShot && !(s.secret && text.includes(s.secret))`.
      *Invariant:* no screenshot is ever taken while the verification code is on screen (AC-18).
   6. If `shoot`:
      - `base = \`${s.screen}-${slug(s.state)}-${project}-${theme}\`` with `slug = x => x.toLowerCase().replace(/[^a-z0-9]+/g, "-")`;
      - `shot = path.join(OUT, "screens", base + ".png")`; `await page.screenshot({ path: shot })`;
      - `const tag = await page.addStyleTag({ content: "html{filter:grayscale(1)!important}" })`;
      - `gray = path.join(OUT, "gray", base + ".png")`; `await page.screenshot({ path: gray })`;
      - `await tag.evaluate(n => n.remove())`.
   7. `row({ check: s.check, screen: s.screen, state: s.state, project, theme, result: v.length ? "FAIL" : "PASS", axe: v, shot: shoot ? shot : "", gray: shoot ? gray : "", evidence: v.length ? v.join("; ") : "axe: 0 violations" })`.
   8. `problems.push(...v.map(x => \`${s.screen} ${s.state} ${theme}: ${x}\`))`.
3. Set the theme back to `"light"` (`localStorage.setItem`) and return `problems`. Callers do
   `expect.soft(problems).toEqual([])`, so the flow continues and the test still fails.

### Step 4 — the specs (`apps/web/tests/ui-verify/`)

Shared rules for every spec:
- Import `state` from `"../e2e/support/state"` and the helpers from `"./support/chain"`.
- Collect `/api` exchanges with `recordApi` from before the first navigation, and page URLs with
  `page.on("framenavigated", f => { if (f === page.mainFrame()) urls.push(f.url()); })`.
- End with `expect(devParamHits(xs, urls)).toEqual([])`.
- Collect `pageerror` into an array that must be empty.
- Text constants that the Python script tables key on are defined once at the top of `01-wp-flows.spec.ts`, and
  `90-clock-and-inbox.spec.ts` re-declares the one it needs. They must be byte-identical to the Python constants
  (Step 6.4):

```ts
export const WP2_T1 = "What is this invoice for? INV-204411";
export const WP2_T4 = "Can you explain the lines on that invoice?";
export const WP5 = "My carbon monoxide detector is going off.";
export const WP7 = "I want a refund for last week's visit.";
export const REFUND_PROMISE = "A representative will get to your refund request within 2 business days.";
export const SAFETY_START = "Please leave the home immediately and call 911";
export const SEED_REFS = ["MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008"];
```

**4.1 `01-wp-flows.spec.ts`: four tests, in this order.**

1. `WP-2: locate, read the code on SCR-2, see the invoice as billed` (AC-6 browser leg, AC-16, AC-18 code-waiting).
   - `test.skip(test.info().project.name !== "chrome-desktop", "WP-2 runs once per chain run: its scripted steps are consumed in call order")`.
   - `const threadP = startedThread(page)`; `await state.signInAs(page, "customer", "/")`;
     `const threadId = await threadP`.
   - `await send(page, WP2_T1)`;
     `await expect(page.getByRole("button", { name: "Send the code" }).last()).toBeVisible({ timeout: 30_000 })`;
     `await fillLocate(page)`;
     `await expect(page.getByLabel("6-digit code").last()).toBeVisible({ timeout: 30_000 })`.
   - Second tab: `const tab2 = await page.context().newPage(); recordApi(tab2, xs); await tab2.goto("/demo/inbox")`.
     `await expect(tab2.getByText("Active").first()).toBeVisible({ timeout: 15_000 })`.
     `const code = /\b(\d{6})\b/.exec(await tab2.locator("main").innerText())?.[1]`;
     `expect(code, "a six-digit code on SCR-2").toBeTruthy()`.
   - `expect.soft(await checkState(tab2, { check: "AC-18", screen: "SCR-2", state: "code waiting", noShot: true })).toEqual([])`.
     `const codeHash = sha256(code!)`; `await tab2.close()`. *Invariant:* the code value never leaves this test
     except as its SHA-256; nothing prints it.
   - `const before = await entries(page).count()`; `await page.getByLabel("6-digit code").last().fill(code!)`;
     `await page.getByRole("button", { name: "Verify", exact: true }).last().click()`;
     `await expect.poll(() => entries(page).count(), { timeout: 30_000 }).toBeGreaterThan(before)`.
   - Mirror the remaining turns of AEA-51's merged `wp2` driver after the code turn. If that driver has a turn 4,
     `await send(page, WP2_T4)`. Then
     `await expect(conversation(page)).toContainText("$478.00", { timeout: 30_000 })` and `toContainText("INV-204411")`.
   - `expect.soft(await checkState(page, { check: "AC-16", screen: "SCR-1", state: "invoice read after the code", secret: code! })).toEqual([])`.
   - `writeJson("wp2-chrome-desktop", { thread_id: threadId, code_sha256: codeHash, exchanges: xs })`.
2. `WP-5: the safety instruction is the first reply text` (both projects; AC-7, AC-16).
   - `threadP`; sign in as the customer; `await send(page, WP5)`.
   - Find the customer's entry index:
     `const i = await entries(page).evaluateAll((els, t) => els.findIndex(e => (e.textContent ?? "").includes(t)), WP5)`;
     `expect(i).toBeGreaterThanOrEqual(0)`; `await expect.poll(() => entries(page).count(), { timeout: 30_000 }).toBeGreaterThan(i + 1)`.
   - `const reply = entries(page).nth(i + 1)`; `await expect(reply).toContainText(SAFETY_START)`;
     `const t = await reply.innerText(); const k = t.indexOf(SAFETY_START); expect(t.slice(0, k)).not.toMatch(/[?.!]/)`.
     *Invariant:* nothing sentence-like comes before the instruction (DOM text order).
   - `checkState(… { check: "AC-16", screen: "SCR-1", state: "safety reply (WP-5)" })`.
   - `writeJson(\`wp5-${project}\`, { thread_id, exchanges: xs })`.
3. `WP-7: refund promise and reference, then the same reference in the representative queue` (both projects; AC-7,
   AC-17).
   - Sign in as the customer (with `threadP`); `await send(page, WP7)`;
     `await expect(conversation(page)).toContainText(REFUND_PROMISE, { timeout: 30_000 })`;
     `const ref = /(MHC-C-\d{4})/.exec(await conversation(page).innerText())?.[1]`; `expect(ref).toBeTruthy()`.
   - `checkState(… { check: "AC-17", screen: "SCR-1", state: "refund handoff card and follow-up choice (WP-7)" })`.
   - `await radios(page).getByRole("radio", { name: /Riley/ }).click()`; `await expect(page).toHaveURL(/\/staff\/queue/)`;
     `await expect(page.locator("main")).toContainText(ref!, { timeout: 30_000 })`; for each of `SEED_REFS`:
     `await expect(page.locator("main")).toContainText(r)`.
   - `writeJson(\`wp7-${project}\`, { thread_id, reference: ref, exchanges: xs })`.
4. `WF-2: Talk to a person on the first ask` (both projects; AC-17).
   - Sign in as the customer; `await expect(page.getByRole("textbox", { name: "Message" })).toBeVisible({ timeout: 15_000 })`.
   - `await page.getByRole("button", { name: "Talk to a person" }).first().click()`;
     `await expect(conversation(page)).toContainText(/MHC-C-\d{4}/, { timeout: 30_000 })`.
   - `checkState(… { check: "AC-17", screen: "SCR-1", state: "direct person request" })`.

**4.2 `02-measures.spec.ts`: three tests, both projects (AC-9, AC-21).**

Each test registers `const resP = page.waitForResponse(r => new URL(r.url()).pathname === <op path> && r.status() === 200, { timeout: 30_000 })`
**before** `state.signInAs`, then reads `const body = await (await resP).json()`. It builds a `mismatches: string[]`
array, then calls `writeJson(\`measures-${screen}-${project}\`, { response: body, mismatches })`,
`expect(mismatches).toEqual([])` and finally `checkState(… { check: "AC-21", screen, state: "after the WP flows" })`.

- **SCR-9** (`/staff/owner`, role `owner`, op `/api/staff/owner-metrics`):
  - Tiles: for `[key, noun]` of `[["in_scope_correct_resolution", "in-scope conversations"], ["promises_kept_on_time", "promises due"], ["handoffs", "conversations"]]`:
    - `m = body[key]`;
    - `card = page.locator("section[aria-labelledby]").filter({ has: page.getByRole("heading", { level: 2, name: m.label }) }).first()`;
    - `t = await card.innerText()`;
    - mismatch unless `t.includes(formatShare(m.value))` and `t.includes(nOfN(m.numerator, m.denominator, noun))`.
  - Tables: for `[caption, field, noun]` of `[["Outcomes of stored conversations", "outcomes", "conversations"], ["Handoffs by reason", "handoffs_by_reason", "handoffs"]]`:
    - if `body[field].length === 0`, expect the text `None yet.` to be visible;
    - else, for each `m`: `r = page.getByRole("table", { name: caption }).getByRole("row").filter({ has: page.getByRole("rowheader", { name: m.label, exact: true }) })`;
      `cells = r.getByRole("cell")`;
    - mismatch unless `(await cells.nth(0).innerText()).trim() === nOfN(m.numerator, m.denominator, noun)` and
      `(await cells.nth(1).innerText()).trim().startsWith(formatShare(m.value))`.
- **SCR-10** (`/monitoring`, role `customer`, op `/api/monitoring`).
  - Helper: `const xp = (s: string) => s.includes("'") ? \`concat('${s.split("'").join(\`', "'", '\`)}')\` : \`'${s}'\``.
  - Helper: `const cardRow = (region, label, starts = false) => region.locator(\`xpath=.//span[${starts ? "starts-with(normalize-space(.), " + xp(label) + ")" : "normalize-space(.)=" + xp(label)}]/../..\`).first()`.
  - `health = page.getByRole("region", { name: "Health" })`.
  - For each `tile` in `body.health`:
    - `rowEl = cardRow(health, tile.label)`; `value = (await rowEl.locator(":scope > div").nth(1).innerText()).trim()`;
    - expected `tile.value != null ? formatTileValue(tile) : "—"`;
    - the hint is the `tileHint` copied from `Scr10.tsx`:
      `tile.value == null ? tile.null_reason : (tile.numerator != null && tile.denominator != null ? \`${tile.numerator} of ${tile.denominator} turns\` : undefined)`.
      When it is defined, `rowEl` text must include it.
  - Spend: `health` text includes `\`${formatCents(body.spend.today_cents)} of ${formatCents(body.spend.cap_cents)} daily cap\``.
  - Trace export: `cardRow(health, "Trace export")` text includes `body.trace_export`.
  - Threshold: `(await health.innerText()).includes("12.5")` must be false. The latency line belongs in the alert
    lines only.
  - `correctness = page.getByRole("region", { name: "Correctness" })`; `ce = body.correctness.containment_estimate`:
    - `cardRow(correctness, ce.label, true)` value cell `=== formatShare(ce.value)`;
    - its text includes `ce.value == null ? ce.null_reason : nOfN(ce.numerator, ce.denominator, "live conversations")`.
  - Escalations: for each `t` in `body.correctness.escalations_by_reason`, `cardRow(correctness, t.label)` value
    cell `=== formatCount(t.value)`. If the list is empty, the text `No escalations since the last reset.` is
    visible.
- **SCR-11** (`/eval`, role `customer`, op `/api/eval/latest`):
  - If both `body.splits.held_out` and `body.splits.dev` are null: `No evaluation run yet.` is visible, and
    `(await page.locator("main").innerText())` contains no `%`.
  - Else, for each present split (`noun = "held-out cases" | "dev cases"`) and each measure `m`: the main text
    includes `nOfN(m.numerator, m.denominator, noun)` and `formatShare(m.value)`.

**4.3 `03-role-switch.spec.ts`: one test (AC-11, first half; STF-19).**
`test.skip(project !== "chrome-desktop", "runs once: the role belongs to the session, not the viewport")`. Uses
`browser` and **one context with two pages**. The role is shared through the session cookie, so two separate contexts
would be two logins.

1. `ctx = await browser.newContext({ baseURL: test.info().project.use.baseURL, viewport: test.info().project.use.viewport })`;
   `tab1 = await ctx.newPage()`.
   Record `tab1` requests with timestamps:
   `const reqs: { path: string; method: string; at: number }[] = []; tab1.on("request", r => reqs.push({ path: new URL(r.url()).pathname, method: r.method(), at: Date.now() }))`.
2. `await state.signInAs(tab1, "representative", "/staff/cases/MHC-C-0005")`;
   `await expect(tab1.locator("h1").first()).toBeVisible()`. SCR-6's rail polls `getQueue` every 10 s.
3. `tab2 = await ctx.newPage(); await tab2.goto("/staff/queue")`;
   `const switchedAt = Date.now(); await radios(tab2).getByRole("radio", { name: /Customer/ }).click()`;
   `await expect.poll(() => new URL(tab2.url()).pathname).toBe("/")`.
4. `const forbiddenP = tab1.waitForResponse(r => new URL(r.url()).pathname.startsWith("/api/staff/") && r.status() === 403, { timeout: 30_000 })`;
   `await tab1.bringToFront(); await tab1.evaluate(() => window.dispatchEvent(new Event("focus")))`.
5. `const body = await (await forbiddenP).json()`; `expect(body.error.code).toBe("ROLE_NOT_ALLOWED")`;
   `expect(body.error.details.reason).toBe("wrong_role")`.
6. `await expect.poll(() => reqs.filter(r => r.path === "/api/session" && r.method === "GET" && r.at >= switchedAt).length, { timeout: 15_000 }).toBeGreaterThan(0)`.
7. `await expect(tab1.getByText("You're acting as the customer. Switch to a staff role to see this.")).toBeVisible({ timeout: 15_000 })`;
   `await expect(radios(tab1)).toBeVisible()`. *Invariant:* no staff data stays on screen after the 403. The panel
   replaces it.
8. `writeJson("role-switch-chrome-desktop", { status: 403, code: body.error.code, reason: body.error.details.reason, session_reads_after_switch: n })`;
   `await ctx.close()`.

**4.4 `04-screens.spec.ts`: one test per entry below, both projects.**
Each test signs in with `state.signInAs(page, role, path)`. For `role: null` it uses `state.visitSignedOut(page, path)`.
Then it runs the entry's `prepare` (if any), then `checkState` per state, and ends with `expect.soft(problems).toEqual([])`.

| Screen | Check | Path | Role | States (`prepare` → state name; `reach` where a reload would lose the state) |
|---|---|---|---|---|
| SCR-12 | AC-22 | `/login` | null | "empty" (`reach`: `visitSignedOut(p, "/login")`); "wrong pair" (`reach`: `visitSignedOut(p, "/login")`, fill `Username` "not-the-user", `Password` "not-the-password", click `Sign in`, expect the refusal line visible and `Password` value `""`); "session ended" (`reach`: `p.goto("/login?return_to=%2F&reason=expired")`, expect the ended line visible) |
| SCR-1 | AC-16 | `/` | customer | "greeting" (expect textbox `Message` visible); then `prepare`: `send(page, "Hello there")` and wait for `entries` count ≥ 3 → "after a reply" |
| SCR-2 | AC-18 | `/demo/inbox` | customer | "empty inbox" |
| SCR-3 | AC-20 | `/demo` | customer | `prepare`: if switch `Demo: simulate staff on shift` is checked, `setChecked(false)` → "nobody online"; `prepare`: `setChecked(true)`, `toBeChecked()` → "simulated staff on shift"; **finally** `setChecked(false)` and `toBeChecked({ checked: false })`. *Invariant:* staffing is off again for every later test |
| SCR-4 | AC-19 | `/role` | customer | "role switch" |
| SCR-5 | AC-19 | `/staff/queue` | representative | "queue": before `checkState`, `await expect(page.getByRole("heading", { level: 1, name: "Representative queue" })).toBeVisible()`. Then the first case row (`page.locator("main li, main tr, main article").filter({ hasText: /MHC-C-\d{4}/ }).first()`) `toContainText("Safety")`. If none of `li`/`tr`/`article` wraps a row on the real page, print `await page.locator("main").innerHTML()` once in a debug run, pick the element that wraps one case, and write a one-line comment naming it |
| SCR-6 | AC-19 | `/staff/cases/MHC-C-0007` | representative | "case view" |
| SCR-7 | AC-19 | `/staff/oversight` | supervisor | "oversight lanes" |
| SCR-8 | AC-19 | `/staff/flags` | representative | "flags list" |

SCR-9…SCR-11 are covered by `02-measures.spec.ts` and are not repeated here.

**4.5 `90-clock-and-inbox.spec.ts`: one test, phase B, desktop only (AC-18 expired, AC-20 after clock).**
`test.skip(project !== "chrome-desktop", "phase B runs once")`.

1. Sign in as the customer; `await send(page, WP2_T1)`; wait for `Send the code`; `await fillLocate(page)`; expect
   `6-digit code` visible.
2. `await radios(page).getByRole("radio", { name: /supervisor/i }).click()`;
   `await expect(page).toHaveURL(/\/staff\/oversight/)`; `await page.getByText("Demo controls", { exact: true }).click()`.
   `const clockP = page.waitForResponse(r => new URL(r.url()).pathname === "/api/demo/clock" && r.request().method() === "POST")`;
   `await page.getByRole("button", { name: "+1 hour" }).click()`; `expect((await clockP).status()).toBe(200)`.
3. `await radios(page).getByRole("radio", { name: /Customer/ }).click()`; `await page.goto("/demo/inbox")`.
   - `const expired = await page.getByText("Expired", { exact: true }).first().waitFor({ state: "visible", timeout: 15_000 }).then(() => true, () => false)`.
   - If `expired`: `checkState(… { check: "AC-18", screen: "SCR-2", state: "expired code" })`. The code is dead, so
     screenshots are allowed; the AC names this state for the grayscale review.
   - Else: `row({ check: "AC-18", screen: "SCR-2", state: "expired code", project, theme: "light", result: "NOT_RUN", axe: [], shot: "", gray: "", evidence: "no 'Expired' status within 15 s of +1 hour demo time (the code expiry may follow the wall clock)" })`,
     plus `test.info().annotations.push({ type: "not_run", description: <same> })`.
4. `await page.goto("/demo")`; `checkState(… { check: "AC-20", screen: "SCR-3", state: "after a clock advance" })`.

**4.6 `99-role-reset.spec.ts`: one test, phase B, desktop only (AC-11 second half).**
This test runs **last** because the reset clears every chat. Steps:

1. As in 4.3 steps 1–2: one context, `tab1` signed in as representative on `/staff/cases/MHC-C-0005`.
2. `tab2 = await ctx.newPage(); await tab2.goto("/demo"); await state.reset(tab2)`.
3. `forbiddenP` (as 4.3 step 4); `bringToFront` and dispatch `focus`; then `body.error.code === "ROLE_NOT_ALLOWED"`
   and `body.error.details.reason === "role_reset"`.
4. `await expect(radios(tab1)).toBeVisible({ timeout: 15_000 })`, then
   `await expect(tab1.getByText(/The demo was reset, so you're back to the customer role\. Pick a role again\.|You're acting as the customer\. Switch to a staff role to see this\./)).toBeVisible()`.
   Record which line appeared in `writeJson("role-reset", { code, reason, panel_line })`.

**4.7 `served-smoke.spec.ts`: one test, project `served-build` (AC-5).**

1. Collect exchanges and URLs as above; `const resp = await page.goto("/staff/queue")`.
2. `await expect(page).toHaveURL(/\/login\?.*return_to=%2Fstaff%2Fqueue/)`. Then
   `expect(resp?.request().redirectedFrom()?.url() ?? "", "the server answered with a redirect").toContain("/staff/queue")`.
   *Invariant:* WEB-28's 303 comes from the server, not from the app.
3. `await page.screenshot({ path: path.join(OUT, "screens", "served-1-login.png") })`. The fields are empty at
   this point.
4. Fill `Username` and `Password` (exact) from `env("E2E_USERNAME")` and `env("E2E_PASSWORD")`, click `Sign in`;
   `await expect.poll(() => new URL(page.url()).pathname, { timeout: 15_000 }).toBe("/staff/queue")`;
   `await expect(page.getByText("You're acting as the customer. Switch to a staff role to see this.")).toBeVisible()`.
5. `await page.goto("/")`; `await expect(page.getByRole("textbox", { name: "Message" })).toBeVisible({ timeout: 15_000 })`;
   screenshot `served-2-chat.png`.
6. `await radios(page).getByRole("radio", { name: /Riley/ }).click()`; `await expect(page).toHaveURL(/\/staff\/queue/)`;
   `await expect(page.getByRole("heading", { level: 1, name: "Representative queue" })).toBeVisible()`; screenshot
   `served-3-queue.png`.
7. For `[p, op, h1]` of `[["/monitoring", "/api/monitoring", "Monitoring"], ["/eval", "/api/eval/latest", "Evaluation report"]]`:
   register `waitForResponse` for `op`, `goto(p)`, expect status 200 and the h1 visible.
8. `expect(await page.evaluate(() => (window as unknown as { __mhcDev?: unknown }).__mhcDev)).toBeUndefined()`;
   `devParamHits` empty; `pageerror` empty; `writeJson("served-smoke", { exchanges: xs, urls })`.

### Step 5 — `apps/web/scripts/ui-verify-lighthouse.mjs`

First line: `// AEA-55: Lighthouse accessibility audit of the 12 screens through the UI-verify chain (navigation mode, desktop preset).`

1. Read the required env `UI_VERIFY_BASE_URL`, `UI_VERIFY_OUT`, `E2E_USERNAME`, `E2E_PASSWORD`; throw if any is
   missing. `out = path.join(UI_VERIFY_OUT, "lighthouse")`; `mkdirSync(out, { recursive: true })`;
   `headersFile = path.join(out, ".headers.json")`.
2. `SCREENS = [["SCR-12","/login",null],["SCR-1","/","customer"],["SCR-2","/demo/inbox","customer"],["SCR-3","/demo","customer"],["SCR-4","/role","customer"],["SCR-5","/staff/queue","representative"],["SCR-6","/staff/cases/MHC-C-0007","representative"],["SCR-7","/staff/oversight","supervisor"],["SCR-8","/staff/flags","representative"],["SCR-9","/staff/owner","owner"],["SCR-10","/monitoring","customer"],["SCR-11","/eval","customer"]]`.
3. `try`:
   - Log in with `fetch(base + "/api/login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ username, password }) })`
     and require status 200.
   - `cookie = res.headers.getSetCookie().map(c => c.split(";")[0]).find(c => c.startsWith("mhc_session="))`; throw
     if missing.
   - `writeFileSync(headersFile, JSON.stringify({ Cookie: cookie }), { mode: 0o600 })`.
   - For each screen:
     1. If `role`, `PUT base + "/api/session/role"` with `{ role }` and the `cookie` header; require status 200.
     2. Run `execFileSync("npx", ["--yes", "lighthouse@12", base + p, "--only-categories=accessibility", "--output=json", \`--output-path=${file}\`, "--quiet", "--preset=desktop", "--max-wait-for-load=20000", "--chrome-flags=--headless=new --no-sandbox", ...(role ? [\`--extra-headers=${headersFile}\`] : [])], { stdio: "ignore", timeout: 120_000, env: { ...process.env, CHROME_PATH: "/usr/bin/google-chrome" } })`,
        with `file = path.join(out, \`${screen}.json\`)`. If it throws, push a `FAIL` row with note
        `lighthouse exited: <first line>` and continue.
     3. `lhr = JSON.parse(readFileSync(file))`; `delete lhr.configSettings?.extraHeaders`; rewrite `file`.
        *Invariant:* the session cookie is not kept in the report.
     4. `failing = lhr.categories.accessibility.auditRefs.filter(a => a.weight > 0 && lhr.audits[a.id].score === 0).map(a => a.id)`;
        `final = lhr.finalDisplayedUrl ?? lhr.finalUrl`.
     5. `result = role && new URL(final).pathname === "/login" ? "FAIL" : failing.length ? "FAIL" : "PASS"`. A redirect
        to `/login` adds the note `redirected to login: the cookie was not applied`.
     6. Push `{ screen, path: p, role, result, score: lhr.categories.accessibility.score, failing, note }`.
4. `finally`: `rmSync(headersFile, { force: true })`.
5. Write `summary.json` (an array of 12 rows) and print one line per row: `SCR-n RESULT score failing-ids`.

### Step 6 — `tests/integration/test_ui_run_records.py` (≤ 500 lines)

**6.1 Module header.** Docstring, three lines: what it starts, which ACs, and "Opt-in: `MERIDIAN_UI_VERIFY=1`
(needs `apps/web/node_modules`, a built `apps/web/dist`, system Chrome and the built index)".

`pytestmark = pytest.mark.skipif(os.environ.get("MERIDIAN_UI_VERIFY") != "1", reason="UI-verify chain: set MERIDIAN_UI_VERIFY=1 (AEA-55; needs apps/web/node_modules, apps/web/dist, /usr/bin/google-chrome, the built index)")`.

Imports:
- `meridian.config.Settings`, `meridian.domain.common.{HandoffReason, Role}`, `meridian.gates.gate.CODE_ENTERED`,
  `meridian.adapters.sqlite.db.format_wall`; `datetime.{date, datetime, time, timedelta}` and `zoneinfo.ZoneInfo`;
- `reason_label` from the module found in Step 0.4;
- `tests.integration.customer_support.{RunOptions, StepScript, build_capture_sink, finished_spans, open_customer_run, step_overrides}`;
- `tests.graph.worked_pair_scenarios.{NORMAL, TOOLS, brief, planner, report, responder, step, tool}` (only those used);
- `tests.journeys.support.env.journey_environ`, `tests.journeys.support.server.{FORBIDDEN_PORTS, launch_server}`.

**6.2 Constants.**
`REPO_ROOT = Path(__file__).resolve().parents[2]`; `WEB_DIR = REPO_ROOT / "apps" / "web"`;
`SPEC = REPO_ROOT / "docs/ux/03-structure/ui-contracts.openapi.yaml"`; `CHROME = Path("/usr/bin/google-chrome")`;
`CAP_S = 500`; `STREAM_PROBE_S = 20.0`; `CONFIG = "playwright.ui-verify.config.ts"`;
`DEV_PARAM_RE = re.compile(r"[?&](signedin|role|scenario|staffing|ex|delay)=")`; `SIX = re.compile(r"(?<!\d)\d{6}(?!\d)")`;
`SIX_B = re.compile(rb"(?<!\d)\d{6}(?!\d)")`;
`DEFAULT_REPLY = "Thanks. I can help with bookings, memberships, billing and warranty questions."`. The four
`WP2_T1`, `WP2_T4`, `WP7` texts are byte-identical to Step 4. Markers:
`WP2_T4_MARKER = "explain the lines"`, `WP2_T1_MARKER = "What is this invoice for"`,
`WP7_MARKER = "refund for last week"`.

```python
PROJECTS = ("chrome-desktop", "chrome-phone")
PHASE_A = (                                   # run in this order; each (label, files) once per project
    ("wp-flows", ("tests/ui-verify/01-wp-flows.spec.ts",)),
    ("measures-roles", ("tests/ui-verify/02-measures.spec.ts", "tests/ui-verify/03-role-switch.spec.ts")),
    ("ux-smoke-sweep", ("tests/e2e/smoke.spec.ts", "tests/e2e/sweep.spec.ts")),
    ("screens", ("tests/ui-verify/04-screens.spec.ts",)),
)
PHASE_B = ("tests/ui-verify/90-clock-and-inbox.spec.ts", "tests/ui-verify/99-role-reset.spec.ts")   # chrome-desktop only
NOT_RUN_SPECS = {
    "e2e/journey-chat-booking-handoff.spec.ts": "multi-turn booking needs per-turn scripted model steps, which the browser "
    "suite cannot set between turns; the same path runs in the browser as AEA-62 J-3/J-6 and AEA-52 J-7 (AC-13)",
}
```

**6.3 Small helpers** (each ≤ 15 lines):
- `free_port() -> int`: bind `("127.0.0.1", 0)`, read the port, close; loop while the port is in
  `FORBIDDEN_PORTS`.
- `wait_http(url, timeout_s=60) -> None`: poll `httpx.get(url, timeout=2)` until any status below 500; else
  `RuntimeError`.
- `wait_port(port, timeout_s=60) -> None`: `socket.create_connection(("127.0.0.1", port), 1)` until it connects.
- `node_env(extra: Mapping[str, str]) -> dict[str, str]`: `{k: os.environ[k] for k in ("PATH", "HOME", "LANG", "TMPDIR", "XDG_RUNTIME_DIR") if k in os.environ} | dict(extra)`.
  *Invariant:* no provider key or other shell secret reaches a Node process or its logs.
- `start(cmd: list[str], *, env, log: Path) -> subprocess.Popen[bytes]`: `cwd=WEB_DIR`,
  `stdout=log.open("ab")`, `stderr=subprocess.STDOUT`, `start_new_session=True`.
- `stop(proc) -> None`: `os.killpg(proc.pid, signal.SIGTERM)`; `proc.wait(10)`; on timeout `os.killpg(…, SIGKILL)`.
  Ignore `ProcessLookupError`.
- `prism_cmd(port, upstream, *, validate) -> list[str]`:
  `["npx", "prism", "proxy", "-h", "127.0.0.1", "-p", str(port), str(SPEC), upstream, "--errors", *([] if validate else ["--validate-request=false"])]`.
- `statuses(report: Path) -> list[dict[str, str]]`: walk the Playwright JSON (`suites` recursively; each
  `spec.tests[]`). Emit `{"file": spec["file"] or the suite's, "title", "project": test["projectName"], "result", "reason"}`.
  Map `status` `expected` → PASS, `skipped` → NOT_RUN (reason = the first annotation with type `skip` or `not_run`),
  `unexpected`/`flaky` → FAIL (reason = the first line of `results[-1]["error"]["message"]`, cut to 200 chars). A
  missing report file gives one FAIL row with reason `no report (time cap or crash)`.
- `first_frame_s(client, path) -> float | None`: `start = time.monotonic()`; inside
  `client.stream("GET", path, headers={"Accept": "text/event-stream"}, timeout=httpx.Timeout(STREAM_PROBE_S + 5, read=STREAM_PROBE_S))`,
  return `None` unless status is 200; for `chunk in r.iter_raw()`, return the elapsed time on the first non-empty
  chunk. Catch `httpx.ReadTimeout` and return `None`. Return `None` if the elapsed time is over `STREAM_PROBE_S`.
- `code_hits(chain, digest) -> list[str]` (Step 6.7).

**6.4 Script tables** (`script_tables() -> tuple[dict[Role, Any], dict[str, dict[Role, Any]]]`).
- `default = {Role.PLANNER: planner(), Role.CLASSIFIER: NORMAL, Role.RESPONDER: responder(DEFAULT_REPLY)}`.
- `markers` is a dict built **in this insertion order**:
  1. `WP2_T4_MARKER`: the per-role entries of AEA-51's `wp2` driver turn 4 (its `set_step(default=…)` mapping).
     Copy it only if the driver has a turn 4.
  2. `WP2_T1_MARKER`: the entries of `wp2` turns 1–3, per role. A role called in more than one of those turns
     becomes a **tuple in call order**. `Role.SPECIALIST` keeps the driver's round-indexed tuple for turn 1.
  3. `WP7_MARKER`: the `wp7` driver's single-turn mapping.
- *Invariant 1:* turn 4's request also carries the turn-1 text in its chat window, so its marker must come first.
- *Invariant 2:* marker phrases are taken from the customer's own words, never from a word a prompt contains.
  `run.script.problems()` being empty after phase A proves no call fell through (Step 6.6).
- WP-5 needs no entry: the safety gate answers before any model call (AEA-51 `wp5`: "no model entry set").
- Copy each entry by **calling the same helpers with the same arguments as the driver** (for example
  `planner(account="invoice", topic="billing")`). Never paste JSON.

**6.5 The `Chain` dataclass.**

```python
@dataclass
class Chain:
    run: Any                      # CustomerRun
    out: Path
    sink: Any
    exporter: Any
    prism_url: str
    vite_url: str
    prism_log: Path
    probes: dict[str, str]
    secrets: tuple[str, ...]
    node: dict[str, str]          # node_env of the chain invocations (holds the demo pair: never print)
    def playwright(self, label: str, project: str, files: Sequence[str], extra: Mapping[str, str] = {}) -> Path: ...
```

`playwright()`:
- `report = self.out / f"pw-{label}-{project}.json"`;
- `subprocess.run(["perl", "-e", f"alarm {CAP_S}; exec @ARGV", "npx", "playwright", "test", "--config", CONFIG, "--project", project, *files], cwd=WEB_DIR, env=self.node | dict(extra) | {"UI_VERIFY_JSON": str(report)}, stdout=log, stderr=STDOUT)`,
  with `log = self.out / f"pw-{label}-{project}.log"`;
- return `report`.
- Exit code 142 (SIGALRM) is not an exception: `statuses()` shows the missing or partial report.

**6.6 The fixture** `@pytest.fixture(scope="module") def chain(request: pytest.FixtureRequest) -> Iterator[Chain]`.
Numbered, with the invariant each step protects:

1. Preconditions. Raise `RuntimeError`, never skip, once the opt-in is set:
   - `WEB_DIR/"node_modules/.bin/playwright"` and `…/.bin/prism` exist;
   - `WEB_DIR/"dist/index.html"` exists ("build first: `cd apps/web && npm run build && npm run check:dist`"; never
     build in a test);
   - `CHROME` exists; `shutil.which("perl")` and `shutil.which("ss")` are set.
2. `out = REPO_ROOT / "var" / "ui-verify" / datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d-%H%M%S")`;
   `out.mkdir(parents=True)`.
3. `sink, exporter = build_capture_sink([])`.
4. `with open_customer_run(request, RunOptions(trace=sink)) as run:` (built index; socket guard, log tap, scripted
   model, issued-DB hash check all from AEA-51/57).
5. `default, markers = script_tables(); run.steps.set_step(default, by_marker=markers)`.
6. Data preconditions:
   - `run.db.scalar("SELECT COUNT(*) FROM cases WHERE seed = 1") >= 4`;
   - `cust = run.db.one("SELECT name, phone FROM customers WHERE customer_id = ?", ("MHC-10002",))`.
     *Invariant:* the name and phone are read at run time and passed only through the environment, never written
     in a file.
7. Build `node = node_env({...})`:
   - `E2E_TARGET="real"`, `E2E_USERNAME=run.demo_username`,
     `E2E_PASSWORD=run.settings.demo_password.get_secret_value()`;
   - `E2E_CUSTOMER_NAME=str(cust["name"])`, `E2E_CUSTOMER_PHONE=str(cust["phone"])`;
   - `UI_VERIFY_OUT=str(out)`, `VITE_CACHE_DIR=str(out / "vite-cache")`.

   `secrets = (*run.secret_values(), run.demo_username)`.
8. **Probes (AC-14)** on a separate probe Prism (`probe_port = free_port()`, log `out/prism-probe.log`):
   1. Start it with `validate=True`; `wait_port`.
   2. Probe (2): `r = httpx.get(f"{probe}/api/chat/sessions/{uuid.uuid4()}", timeout=10)`. The outcome is `backend`
      when `r.status_code == 401 and r.json().get("error", {}).get("code") == "UNAUTHENTICATED" and "request_id" in r.json()`,
      else `prism:{status}`. If not `backend`: stop the probe Prism, restart it with `validate=False`, and probe again.
      Still not `backend` → `RuntimeError("AC-14(2): …")` (stop and report). Record `validate_request` as `on` or
      `off`.
   3. Probe (1): `with httpx.Client(base_url=probe, timeout=30) as c:`
      - `POST /api/login` with the demo pair → 200;
      - `POST /api/chat/sessions` → 201 → `thread_id`;
      - `chat_s = first_frame_s(c, f"/api/chat/sessions/{thread_id}/events")`;
      - `PUT /api/session/role {"role": "representative"}` → 200;
      - `case_s = first_frame_s(c, "/api/staff/cases/MHC-C-0005/events")`.
   4. `bypass = chat_s is None or case_s is None`. If `bypass`, run the same two streams **directly against
      `run.base_url`** (a new client and login). If either still has no first frame, raise
      `RuntimeError("AC-14(1): the backend stream sends nothing in 20 s")`: the backend's owner (AEA-41/AEA-52)
      gets it.
   5. Stop the probe Prism. Write `out/probes.json` with the record
      `probes = {"unauthenticated": …, "validate_request": "on|off", "chat_stream_s": f"{chat_s:.1f}" or "none", "case_stream_s": …, "stream_routing": "direct-to-backend" if bypass else "prism", "backend_chat_stream_s": …, "backend_case_stream_s": …, "cookie_secure": str(run.settings.cookie_secure).lower(), "contract_drift": "mock-only (apps/web/src/dev/transport.ts); the Prism proxy log is the contract check"}`.
9. Run Prism: `prism_port = free_port()`; start with the decided `validate`, log `out/prism-proxy.log`; `wait_port`.
10. Vite: `vite_port = free_port()`.
    - Start `["npx", "vite", "--host", "127.0.0.1", "--port", str(vite_port), "--strictPort"]` with
      `node | {"API_PORT": str(prism_port)} | ({"API_STREAM_PORT": str(run.server.port)} if bypass else {})`,
      log `out/vite.log`.
    - `wait_http(f"http://127.0.0.1:{vite_port}/")`. `node["E2E_BASE_URL"] = vite_url`.
    - *Invariant:* `npx vite` (not `npm run dev`) skips `predev`, so nothing regenerates.
11. Ports: write `subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout` to `out/ports.txt`. Assert
    `{run.server.port, prism_port, vite_port}.isdisjoint(FORBIDDEN_PORTS)`.
12. Phase A: for `label, files in PHASE_A`: for `project in PROJECTS`: `chain.playwright(label, project, files)`.
    Build the `Chain` object before this step so the method can be used.
13. Lighthouse:
    `subprocess.run(["perl", "-e", "alarm 900; exec @ARGV", "node", "scripts/ui-verify-lighthouse.mjs"], cwd=WEB_DIR, env=node | {"UI_VERIFY_BASE_URL": vite_url}, stdout=(out/"lighthouse.log").open("ab"), stderr=STDOUT)`.
14. Served build (AC-5):
    - `root = Path(tempfile.mkdtemp(prefix="meridian-aea55-served-"))`; make `root/"data"`, `root/"no-dist"`,
      `root/"index"`.
    - `environ = journey_environ(root) | {"MERIDIAN_WEB_DIST_DIR": str(WEB_DIR / "dist"), "MERIDIAN_REQUIRE_FRONTEND": "true"}`;
      `s2 = Settings.from_env(environ)`.
    - `script2 = StepScript(); script2.set_step(default)`; `overrides2, _ = step_overrides(s2, script2)`.
    - `with launch_server(s2, overrides=overrides2) as served:`
      `chain.playwright("served", "served-build", ("tests/ui-verify/served-smoke.spec.ts",), {"E2E_SERVED_URL": served.base_url, "E2E_USERNAME": s2.demo_username.get_secret_value(), "E2E_PASSWORD": s2.demo_password.get_secret_value()})`.
    - `finally: shutil.rmtree(root, ignore_errors=True)`.
    - Add `s2`'s two demo values and its session secret to `chain.secrets`.
15. Write `out/statuses.json`: every row of every `pw-*.json` so far, plus one `NOT_RUN` row per `NOT_RUN_SPECS` item
    for both projects.
16. `yield chain`.
17. Teardown (`finally` around 9–16):
    - `stop(vite)`, `stop(prism)`; `shutil.rmtree(out / "vite-cache", ignore_errors=True)`.
    - If `git -C REPO_ROOT diff --quiet -- apps/web/tests/e2e/.gen` fails, run
      `git -C REPO_ROOT checkout -- apps/web/tests/e2e/.gen`. That only restores tracked files this run changed.

**6.7 Tests, in this order** (pytest runs them in file order; never run this module with `-n`).

1. `test_proxy_chain_probes(chain)` (AC-14):
   - `chain.probes["unauthenticated"] == "backend"`; `["cookie_secure"] == "false"`;
   - `["stream_routing"] in ("prism", "direct-to-backend")`; if direct, both `backend_*_stream_s != "none"`;
   - print the probes as JSON.
2. `test_suite_completed_through_the_chain(chain)` (AC-4, AC-5, AC-7, AC-9, AC-11a):
   - `st = json.loads((chain.out / "statuses.json").read_text())`;
   - every `result` is in the four values;
   - `[s for s in st if s["file"].startswith("ui-verify/") and s["result"] == "FAIL"] == []`;
   - `chain.run.script.problems() == ()`. The failure message lists `f"{c.role.value}:{c.result}"` only, never the
     request;
   - `lighthouse/summary.json` has 12 rows;
   - print the counts per result.
3. `test_wp2_through_ui_leaves_no_code(chain)` (AC-6):
   1. `cap = json.loads((chain.out / "capture" / "wp2-chrome-desktop.json").read_text())`.
   2. `n = run.db.scalar("SELECT COUNT(*) FROM messages WHERE thread_id = ? AND text = ?", (cap["thread_id"], CODE_ENTERED))`;
      `assert n >= 1`.
   3. `hits = code_hits(chain, cap["code_sha256"])`; `assert hits == []`. Locations only, never a value.
   4. `ids = {str(r["request_id"]) for r in run.logs.structured("request")}`;
      `missing = [f'{x["method"]} {x["path"]} {x["status"]}' for x in cap["exchanges"] if not x["requestId"] or x["requestId"] not in ids]`;
      `assert missing == []`.
   5. Print `WP-2: {n} "[code entered]" message(s); 0 code hits; {len(cap["exchanges"])} responses matched to request records`.

   `code_hits` algorithm. *Invariant:* the code is compared only as `sha256(candidate) == digest`, so its value is
   never held, printed or written. Sources:
   - every table in `sqlite_master` (type `table`) and every column from `PRAGMA table_info("<t>")`:
     `SELECT "<c>" AS v FROM "<t>" WHERE typeof("<c>") = 'text'`. Any `SIX` match whose hash equals the digest adds
     `f"{t}.{c}"`;
   - every file under `run.env.data_dir.rglob("*")` (catches `checkpoints.sqlite`, WAL files and free pages) with
     `SIX_B` adds `f"file {p.name}"`;
   - `run.logs.all_text()` adds `"log"`;
   - every span from `finished_spans(chain.sink, chain.exporter)`: `json.dumps({"name": s.name, "attributes": dict(s.attributes or {}), "events": [{"name": e.name, "attributes": dict(e.attributes or {})} for e in s.events]}, default=str)`
     adds `f"span {s.name}"`.
4. `test_reads_equal_records_after_flows(chain)` (AC-8). These are the AEA-53 §6.4 SQL queries.
   1. Preconditions:
      - `wp2-chrome-desktop`, `wp5-chrome-desktop` and `wp7-chrome-desktop` captures exist, and each `thread_id`
        has one `conversations` row;
      - `SELECT COUNT(*) FROM cases WHERE case_ref = ? AND reason = 'refund'` (the WP-7 reference) is 1;
      - `SELECT COUNT(*) FROM cases WHERE thread_id = ? AND reason = 'safety'` (the WP-5 thread) is 1.
   2. `c = run.login().client`;
      `c.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "owner"})`;
      `CHI = ZoneInfo("America/Chicago")`; `d0 = datetime.now(CHI).date()`;
      `owner = c.call("GET", "/api/staff/owner-metrics", operation_id="getOwnerMetrics").json()`;
      `mon = c.call("GET", "/api/monitoring", operation_id="getMonitoring").json()`;
      `d1 = datetime.now(CHI).date()`.
   3. CON-18, with `ended = SELECT COUNT(*) FROM conversations WHERE run_tag IN ('live','seed') AND outcome <> 'open'`:
      - `owner["handoffs"]` denominator == `ended`; its numerator == the same query `AND outcome = 'handed_off'`;
      - each `owner["outcomes"]` row: numerator == the count for `OUTCOME_OF[label]`, denominator == `ended`;
      - `by_reason = {r["reason"]: r["n"] for r in rows("SELECT k.reason AS reason, COUNT(*) AS n FROM cases k JOIN conversations c ON c.thread_id = k.thread_id WHERE c.run_tag IN ('live','seed') GROUP BY k.reason")}`;
      - `{m["label"]: m["numerator"] for m in owner["handoffs_by_reason"]} == {reason_label(HandoffReason(r)): n for r, n in by_reason.items()}`;
      - every row's denominator is `sum(by_reason.values())`.
   4. CON-19, with `L = "FROM turns t JOIN conversations c ON c.thread_id = t.thread_id WHERE t.run_tag = 'live' AND c.run_tag = 'live'"`.
      Tiles are looked up by label:
      - `Conversations` == `SELECT COUNT(*) FROM conversations WHERE run_tag = 'live'`;
      - `Turns` == `SELECT COUNT(*) {L}`;
      - `Failures`: when turns > 0, numerator == `… {L} AND t.outcome = 'degraded_handoff' AND t.degrade_reason IN ('model_error','tool_error','timeout')`
        and denominator == turns; else its value is `None`;
      - latency sample: `ms = sorted(int(r["ms"]) for r in rows(f"SELECT t.server_ms AS ms {L} AND t.server_ms IS NOT NULL"))`
        and `n = len(ms)`. For `Latency p50`/`p95` with q 0.5/0.95: if `n == 0`, null reason `No turns yet`; if
        `n < 20`, null reason `Not enough turns yet (fewer than 20)`; else value == `ms[math.ceil(q * n) - 1]`;
      - `{t["label"]: t["value"] for t in mon["correctness"]["escalations_by_reason"]}` == the by-reason map over
        `c.run_tag = 'live'` only;
      - spend (AEA-53 plan §6.4 shape; `spend_today()` sums the wall-clock Chicago day). If `d0 == d1`:
        - `start = datetime.combine(d0, time(0), tzinfo=CHI)`;
        - `end = datetime.combine(d0 + timedelta(days=1), time(0), tzinfo=CHI)` (DST-safe: built from the next date,
          not `start + 24 h`);
        - `want = round(float(run.db.scalar("SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger WHERE recorded_at >= ? AND recorded_at < ?", (format_wall(start), format_wall(end)))) * 100)`;
        - check `mon["spend"]["today_cents"] == want`.

        Else print `spend not compared: the reads crossed Chicago midnight`.
   5. Collect each inequality as `f"{measure}: page {got} != records {want}"`; print a per-measure table
      (measure, page, records); `assert mismatches == []`.
5. `test_role_reset_and_clock_phase(chain)` (phase B; AC-11b, AC-18 expired, AC-20 after clock):
   - `default, markers = script_tables(); chain.run.steps.set_step(default, by_marker=markers)`, which resets the
     counters (same tables as fixture step 5);
   - `report = chain.playwright("phase-b", "chrome-desktop", PHASE_B)`;
   - append its statuses to `statuses.json`;
   - `assert [s for s in statuses(report) if s["result"] == "FAIL"] == []`.
6. `test_prism_log_has_no_violations(chain)` (AC-3, AC-15, AC-12, PA-1):
   - `lines = chain.prism_log.read_text(errors="replace").splitlines()`;
   - `[l for l in lines if "Violation:" in l] == []` (print up to 20 of them on failure);
   - `[l for l in lines if DEV_PARAM_RE.search(l)] == []`;
   - leaked: every file under `chain.out` (and `chain.prism_log`) whose bytes contain any of `chain.secrets` encoded
     as UTF-8. Assert the list of relative paths is `[]`.

### Step 7 — `apps/web` fast gates and AC-2

`cd apps/web && npm run lint && npm run typecheck && npm run test && npm run check:gen && npm run build && npm run check:dist`.
Every command exits 0. Then `git status --porcelain -- src` prints nothing: `types.gen.ts` and `contract.gen.json` are
unchanged.

**Stop rule (R-13).** The pre-scripts regenerate the two tracked files from the OpenAPI on `main`. If
`git status --porcelain -- src` lists either one, the OpenAPI and the committed generated files disagree. One way this
happens: the D-5 `CaseDetail.events.last_event_id` edit landed without its regenerated types. When that happens:
1. Never commit them. Restore with
   `git checkout -- apps/web/src/api/types.gen.ts apps/web/src/api/contract.gen.json` (run from the worktree root).
2. Stop, and report to the orchestrator for the UX session, with the `git diff --stat` you saw before restoring.
3. AC-2 is then not met. Fixing it is not this ticket's job.

### Step 8 — Python fast gates

`uv run ruff format tests/integration/test_ui_run_records.py && uv run ruff check tests/integration/test_ui_run_records.py && uv run mypy tests/integration/test_ui_run_records.py`
→ clean. `uv run pytest tests/integration/test_ui_run_records.py -q -rs` without the opt-in → collected and skipped
with the reason (proves import and collection).

### Step 9 — Commit 1 (code and config)

`git add apps/web/vite.config.ts apps/web/tsconfig.json apps/web/playwright.ui-verify.config.ts apps/web/scripts/ui-verify-lighthouse.mjs apps/web/tests/ui-verify tests/integration/test_ui_run_records.py`.
Message: `test(AEA-55): UI verify again — Playwright through Prism proxy against the real backend` + a body (what, the
two inert Vite hooks, how to run) + last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Check
`git status` first: the `node_modules` link must not be staged (it is ignored).

### Step 10 — AC-13: all journeys, before the UX-5 rerun

```bash
export MERIDIAN_WEB_DIST_DIR="$PWD/apps/web/dist"
perl -e 'alarm 1800; exec @ARGV' uv run pytest -m journey --journeys-strict --browser-channel chrome --journey-record=AEA-55 -rs
CONTRACT_STRICT=1 uv run pytest tests/contract -q -rs
```

- Expect exit 0, with every journey passing; the plugin writes `docs/testing/journeys/<date>-AEA-55.md`.
- Edit only these fields of that record:
  - *Claim*: "AEA-55 AC-13: all journeys J-1…J-10 on the integrated branch after the run-configuration change, as
    the wave-merge gate runs them";
  - *Level*: `integrated with a scripted model`;
  - *Remaining limitations*: add "the UX-5 rerun through Prism proxy is reported in `docs/testing/ui-verify-again.md`
    and is not journey evidence (integrated-journeys §6)".
- A strict failure caused only by blocked steps (for example the UX selector contract for AEA-58's on-screen steps)
  is reported per journey with its owner in *Blocked by*. AC-13 is then **not met**: say so and continue with
  Step 11; do not hide it.
- A red journey is a finding for its owner ticket. AEA-55 fixes nothing outside §2.

### Step 11 — the UX-5 rerun

`MERIDIAN_UI_VERIFY=1 perl -e 'alarm 5400; exec @ARGV' uv run pytest tests/integration/test_ui_run_records.py -v -s -rs`
(serial; no `-n`).

Iterate only on AEA-55's own files. While iterating, a single spec can be re-run by temporarily narrowing `PHASE_A` in
a scratch edit; restore it before committing. If a 429 `REQUEST_RATE_LIMITED` or `LOGIN_RATE_LIMITED` appears:
- re-run once after 60 s;
- record it in the report as a finding on the per-IP read limit (`WebLimits.reads_per_ip_per_min = 240`; owner AEA-23).

What to do with a failure:
- A failure in the UX session's specs (`e2e/*`) is **recorded, not fixed**. For example, `sweep.spec.ts` "flow: demo
  login returns to return_to" types `demo`/`demo` and is expected to FAIL against the random pair. Route it per the
  loop rule: selector or test defect → UX-4 / UX session; backend behaviour → its AEA owner; contract → Innocent.
- A Prism `Violation:` line is a **stop**. Report it to the orchestrator with the operation, field and side, for
  Innocent. Never edit either side.

### Step 12 — Grayscale review (AC-16…AC-22)

Open each `var/ui-verify/<stamp>/gray/*-chrome-desktop-light.png` and the dark ones of SCR-5, SCR-7 and SCR-10 with
the Read tool (one image per state). For each state, ask: "is the state, priority, lane or status still told apart by
text, an icon or a shape?"
- If yes, record `PASS`.
- If it is unclear, record `NEEDS_HUMAN_REVIEW` with the reason.
- Never record `PASS` for a state you did not look at. Mark the unopened phone images `NEEDS_HUMAN_REVIEW: not
  reviewed (phone width)`, unless you opened them.

### Step 13 — Report `docs/testing/ui-verify-again.md`

Plain sentences, concrete first (global explanation style). No password, username, cookie, code or phone. Sections,
in this order:
1. *What this is*: the second UX-5 run (DAT-25); the level; the revision (`git rev-parse --short HEAD`); the date; the
   runner (agent); the chain as one line: browser → Vite (non-mock) → `prism proxy --errors` → real app (scripted
   model, disposable DB).
2. *How to rerun*: the Step 11 command; the prerequisites (link or install `apps/web/node_modules`; build `dist`;
   Chrome; built index); the ports are random and never 4019 or 5184.
3. *Probe results (AC-14)*: the four results from `probes.json`, each with its outcome. Write any exception (streams
   routed to the backend, request validation off) as a sentence with its reason. Item (4) reads: "the dev-mode
   `[contract drift]` signal exists only in mock mode (`apps/web/src/dev/transport.ts`); the Prism proxy log is the
   real contract check".
4. *Contract check (AC-3)*: the violation count, the log path, and the number of lines Prism handled.
5. *Results*: one table built from `statuses.json` and `rows.jsonl`, with columns Check (AC) · Screen / flow ·
   State · Viewport · Theme · Result · Evidence (axe ids or "0 violations"; screenshot path; reason). Lighthouse is
   one row per screen from `lighthouse/summary.json`.
6. *Not run (AC-15)*: grouped by reason: the dev-layer scenarios, plus `journey-chat-booking-handoff.spec.ts` with
   its reason. Add "no request carried `signedin`, `role`, `scenario`, `staffing`, `ex` or `delay`".
7. *Records left by the UI (AC-6, AC-8)*: the printed lines of both tests; the per-measure table.
8. *Role handling (AC-11)*: both captured responses and the screens shown.
9. *Served build (AC-5)*: the steps, the PASS, and `served-*.png`.
10. *Accessibility per workflow (AC-16…AC-22)*: one short table per WF with axe and Lighthouse results and the
    grayscale verdict.
11. *Findings and where they go*: each FAIL with its owner per the UX-5 loop rule.
12. *Evidence location*: `var/ui-verify/<stamp>/` on the VPS (git-ignored: screenshots are not committed, for disk
    and for AC-12's file list). Name the subfolders.
13. *Walkthrough with live models (AC-10, Innocent)*. A template only:
    - the core tasks to attempt: WP-1 membership question, WP-2 invoice after the code, booking (WP-3/WP-4F),
      WP-5 CO alarm, WP-7 refund, "Talk to a person", role switch to the representative and the case view, owner
      outcomes, monitoring, evaluation;
    - any task left `NEEDS_HUMAN_REVIEW` above;
    - the launch command: copy the live launcher command from AEA-61's merged live-smoke record if it exists, else
      write "pending AEA-61";
    - fields to fill: observed behaviour per task, model ids, spend-ledger total, and the level
      `verified with live models`;
    - the line "Innocent ✓ ____ (checklist §8 'UI verify again')".
14. *Gate basis (AC-1)*: the two Step 0.8 outputs; the *Skips* row; the orchestrator's relay of Innocent's
    2026-10-21 statement; "the UX-5 ★ box stays Innocent's".
15. *Limitations*:
    - no `TRACEABILITY.md`, so the suite is mapped by screen;
    - the scripted model, so wording is not product wording;
    - the booking journey is covered by AC-13 instead;
    - Lighthouse runs on the desktop preset only;
    - any `NEEDS_HUMAN_REVIEW`.

### Step 14 — context rows (AC-23)

- `PROJECT-CHECKLIST.md` line 120: tick it (`[x]`) **only if** AC-3 shows 0 violations and every `ui-verify/` spec
  passed. Append ` — evidence: [docs/testing/ui-verify-again.md](docs/testing/ui-verify-again.md) (AEA-55, <date>)`.
  Otherwise leave it unticked and append ` — run <date>: see [docs/testing/ui-verify-again.md](docs/testing/ui-verify-again.md) (not yet clean)`.
  **Never touch line 91 (UX-5 ★) or line 127 (UI verify again ★).**
- `.claude/reference/area-map.md` *Screens* paragraph (line 54 today): after the sentence about AEA-49 serving
  `dist`, insert: `AEA-55 ran the frontend against the real backend through Prism proxy (`apps/web/playwright.ui-verify.config.ts`, `tests/integration/test_ui_run_records.py`; report [ui-verify-again](../../docs/testing/ui-verify-again.md), <commit>).`
- `.claude/state/icm-progress.md`: add one row after the last "Routes verified against code and tests" row:
  `| Routes verified against code and tests | provisional | <date>: area map *Screens* → apps/web against the real backend (AEA-55, <commit>): test_ui_run_records.py (6 tests) and the UI-verify run, report docs/testing/ui-verify-again.md | Innocent's walkthrough and ★ "UI verify again" |`
  (≤ 400 characters).

### Step 15 — boundary check, clean-up, Commit 2

1. `git diff --name-only main...HEAD` plus the staged files ⊆ §2's owned list (AC-12). Save the output for the report.
2. `unlink apps/web/node_modules` (the link only). `git status --porcelain` shows nothing unexpected. The
   `var/ui-verify/` folder stays (ignored).
3. `git add docs/testing/ui-verify-again.md docs/testing/journeys/<date>-AEA-55.md PROJECT-CHECKLIST.md .claude/reference/area-map.md .claude/state/icm-progress.md`.
   If the plugin wrote a screenshot folder `docs/testing/journeys/<date>-AEA-55/`, add it.
   Message: `docs(AEA-55): UI verify again report, journey record, context rows` + last line
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No push (the merge step pushes `main`).

### What the implementer must NOT do

- Edit anything outside §2:
  - no `apps/web/src/**`, `types.gen.ts`, `contract.gen.json`, `package.json`, `package-lock.json`,
    `playwright.config.ts` or `eslint.config.js`;
  - no UX spec under `apps/web/tests/e2e/**`; no `docs/ux/**`, OpenAPI or `UI_CONTRACTS.md`;
  - no `src/meridian/**`, `tests/journeys/**`, AEA-51/52 helper or `tests/conftest.py`;
  - no `pyproject.toml` or `uv.lock`.
- Fix a failing UX spec, or change a screen, to make the run pass. Edit either side of a contract mismatch.
- Run any npm script or Playwright command that binds 4019 or 5184 (`dev`, `dev:mock`, `mock`, `smoke:mock`,
  `test:e2e`, the default Playwright config).
- `npm install`, `npm ci`, `npx playwright install`; copy `node_modules`; `rm -r` the link.
- Use `?signedin`, `?role`, `?scenario`, `?staffing`, `?ex` or `?delay` anywhere.
- Print, log, assert in a printable message, screenshot or write:
  - the demo username or password, the session secret, an `mhc_session` value;
  - the verification code (only its SHA-256);
  - the customer's phone.
- Tick the UX-5 ★ box or the "UI verify again" ★ line.
- Call a paid model, set provider keys, or run AC-10.
- Run this module with `-n`. Build `apps/web` inside a test.
- `git add -A`; commit `var/`, `dist/` or screenshots; push; force-push.
- Record a state as PASS that was not reached against the real backend. Mock-only is `NOT_RUN`.

---

## 6. Data and fixtures (synthetic only)

| Data | Source | How it enters the run |
|---|---|---|
| Customer MHC-10002 (Omar Patel), invoice INV-204411 ($478.00) | Demo seed over the issued scheduling DB (`services/reset.py` seed; `docs/data/worked-pairs.md` WP-2, "synthetic: partly") | Read from the working copy at run time (`customers` row) → env `E2E_CUSTOMER_NAME` / `E2E_CUSTOMER_PHONE`; never written in a file |
| Seed cases MHC-C-0005…MHC-C-0008 | AEA-31 first-boot demo seed | Asserted present (`cases.seed = 1`, ≥ 4) |
| Demo login pair, session secret | `journey_environ` (random letters per run) | Python → env `E2E_USERNAME` / `E2E_PASSWORD`; scanned for in the output tree (PA-1) |
| Wrong pair `not-the-user` / `not-the-password` | Invented, obviously not a credential | SCR-12 refusal state |
| WP texts (§4 Step 4 constants) | `docs/data/worked-pairs.md` WP-2, WP-5, WP-7, plus two plain follow-up sentences | Typed by Playwright; marker keys of the scripted tables |
| Scripted model outputs | AEA-51 `tests/graph/worked_pair_scenarios.py` drivers `wp2`, `wp7` (helpers, not pasted JSON) + one default reply | `StepScript.set_step` |
| Verification code | Generated by the real `IdentityService` in the run | Read from SCR-2 in the browser; only its SHA-256 leaves the test |

No held-out eval case is read; no real person's data; the issued DB is never written (AEA-51/57 hash check).

---

## 7. Checks

Every `apps/web` command below runs after Step 0.10's `export VITE_CACHE_DIR=…` in the same shell. Run the
gates cheapest first and stop at the first red.

| When | Command | Passing looks like |
|---|---|---|
| While iterating (TS) | `cd apps/web && npm run typecheck && npm run lint` | exit 0 |
| While iterating (Python) | `uv run ruff check tests/integration/test_ui_run_records.py && uv run mypy tests/integration/test_ui_run_records.py` | clean |
| Affected tests (`vite.config.ts` changed) | `cd apps/web && npm run test` | vitest green, same count as on `main` |
| AC-2 | `cd apps/web && npm run check:gen && npm run build && npm run check:dist` | three exits 0; `dist is clean: no dev-layer markers`; `git status --porcelain -- apps/web/src` empty |
| Collection without opt-in | `uv run pytest tests/integration/test_ui_run_records.py -q -rs` | 6 skipped, with the opt-in reason |
| Fast gates before the final commit | `uv run ruff format --check tests/integration/test_ui_run_records.py && uv run ruff check tests/integration/test_ui_run_records.py && uv run mypy tests/integration/test_ui_run_records.py`; `cd apps/web && npm run lint && npm run typecheck` | all clean; results in the report to the orchestrator |
| AC-13 journeys (the affected journeys: `apps/web/` changed, so all are selected; the wave-merge form) | `export MERIDIAN_WEB_DIST_DIR=$PWD/apps/web/dist; perl -e 'alarm 1800; exec @ARGV' uv run pytest -m journey --journeys-strict --browser-channel chrome --journey-record=AEA-55 -rs` and `CONTRACT_STRICT=1 uv run pytest tests/contract -q -rs` | exit 0; record written at `integrated with a scripted model` |
| The UX-5 rerun (the six named tests) | `MERIDIAN_UI_VERIFY=1 perl -e 'alarm 5400; exec @ARGV' uv run pytest tests/integration/test_ui_run_records.py -v -s -rs` | 6 passed: `test_proxy_chain_probes`, `test_suite_completed_through_the_chain`, `test_wp2_through_ui_leaves_no_code`, `test_reads_equal_records_after_flows`, `test_role_reset_and_clock_phase`, `test_prism_log_has_no_violations`; UX-spec FAILs are allowed and reported |
| AC-12 | `git diff --name-only main...HEAD` | only §2 files |

Full suite: **not** run. This change touches no shared fixture, settings, dependency, lockfile, or module imported
across the codebase. `apps/web` config changes select every journey, which Step 10 runs.

---

## 8. Risks and requests

- **R-1, node_modules link (request to the orchestrator).** The orchestrator's rule says "no node_modules in a backend
  worktree". This ticket edits `apps/web` config and must run Node in that same tree, so Step 0.6 **links** the
  primary checkout's folder: no copy, no disk cost, git-ignored, unlinked at the end. Side effects into the shared
  folder are kept out: `VITE_CACHE_DIR` moves Vite's cache into `var/`. If the orchestrator refuses the link, the
  only alternative is running the UI chain from the primary checkout after merge (merge-then-run). That needs a
  different plan.
- **R-2, AC-1 cannot be met literally.** The UX-5 ★ box is unticked, and `docs/ux/05-verify/{QA_REPORT,TRACEABILITY}.md`
  do not exist (Innocent skipped the first run). The plan proceeds on the orchestrator's relay plus the *Skips* row
  and reports that basis. AC-1 stays open for Innocent.
- **R-3, no `TRACEABILITY.md`**, so there is no FLOW-n → test map. Coverage is reported per screen and per AC.
- **R-4, the UX booking journey is `NOT_RUN`.** The scripted model is stepped per turn in API tests, but the browser
  suite cannot change steps between turns, and marker routing cannot tell booking turns apart. AC-13 runs the same
  path in the browser (AEA-62 J-3, J-6) and over the API (AEA-52 J-7). If Innocent wants this spec green through
  Prism, it needs a test-only step-control hook in AEA-51's support. That is **not** added here.
- **R-5, expected UX-spec FAIL:**
  - `sweep.spec.ts` "flow: demo login returns to return_to" hardcodes `demo`/`demo`; the real run uses a random
    pair. It is reported for the UX session, not fixed.
  - `smoke.spec.ts` and `sweep.spec.ts` were written against the mock and may have more first-contact selector
    misses. Same routing.
- **R-6, Prism and SSE.** Prism's proxy probably buffers the upstream body to validate it, so the stream probe will
  likely route both SSE paths straight to the backend (the AC-14 exception). That is recorded, and it means stream
  frames are not contract-checked by Prism. AEA-59's server-contract cases cover them.
- **R-7, per-IP limits.** The whole suite comes from 127.0.0.1: `reads_per_ip_per_min = 240`, and
  `login_rejects_per_ip = 10` per 10 min (this run makes about 4 rejects). A 429 is retried once and reported
  (Step 11).
- **R-8, screenshots are not committed** (disk at about 83%; AC-12's file list). They stay under
  `var/ui-verify/<stamp>/` on the VPS, and the report names them. If Innocent wants them in git, that is a one-line
  follow-up adding a folder beside the report.
- **R-9, Lighthouse via `npx --yes lighthouse@12`** (a network fetch once, outside `package.json`). If it is
  unavailable, the rows are `NOT_RUN` with the reason.
- **R-10, AEA-58's selector contract** (`docs/plans/ux-join/selectors.md`, UX session) is still missing on `main`. If
  it is still missing at build time, AEA-58's on-screen journey steps are *blocked* and `--journeys-strict` fails
  (AC-13 not met, reported with owner "UX session").
- **R-11, upstream holds (build ledger at `c9b17ea`).** Upstream of AEA-51 and AEA-52:
  - AEA-35, AEA-37 and AEA-39 are held at `NEEDS-DECISION`;
  - AEA-30, AEA-36, AEA-40 and AEA-45 are `blocked`.

  AEA-53 is held at `NEEDS-DECISION` (its plan's R-1 grant is not recorded). AEA-58 and AEA-62 wait on those. Any
  delay there delays this ticket. None of them is a decision this ticket needs.
- **R-12, scripted-table fidelity.** WP-2's entries come from AEA-51's driver. If WP-2 still fails through the UI
  (`script.problems()` not empty, or a marker word turns out to occur in a prompt), the implementer stops and sends
  the plan back to the planner. It does not change markers ad hoc.
- **R-13, OpenAPI regeneration (D-5).** The Stage 7 sign-off (D-5) has the UX session adding
  `CaseDetail.events.last_event_id` to `ui-contracts.openapi.yaml`. It is not on `main` at `c9b17ea`. If it lands with
  its regenerated `types.gen.ts` and `contract.gen.json`, nothing changes here. If it lands without them, Step 7's stop
  rule applies, and this ticket never commits generated files. Prism does not flag the extra field either way
  (§4.6).
- **Collisions.**
  - `tests/integration/` is shared by folder with AEA-51, AEA-52 and AEA-53. The file names differ, so there is no
    overlap.
  - `PROJECT-CHECKLIST.md`, `area-map.md` and `icm-progress.md` are append-style shared context files. A merge
    conflict there is resolved by keeping both sides.
  - `apps/web/**` has no other owner in Stage 8; the UX session should not be editing `vite.config.ts` or
    `tsconfig.json` in parallel. The orchestrator should confirm.
- **Contract problems found while planning:** none.

---

## 9. Readiness

**READY**, BLOCKED-ON **AEA-51, AEA-52, AEA-53, AEA-58, AEA-62** being merged into `main`. Step 0.2 checks this.

State at `c9b17ea` (build ledger): AEA-51 `blocked` (a blocker is not merged), AEA-52 `blocked` (same), AEA-53
`blocked` (NEEDS-DECISION: R-1 grant), AEA-58 `blocked` (a blocker is not merged), AEA-62 `blocked` (same). AEA-49
and AEA-57, also named in the slice-plan row, are merged.

| Blocker | Why it is truly needed |
|---|---|
| AEA-51 | **Imports:** `tests/integration/customer_support.py` (`open_customer_run`, `StepScript`, `step_overrides`, `build_capture_sink`, `finished_spans`, `RunOptions`); `tests/graph/worked_pair_scenarios.py` (script helpers and the `wp2`/`wp7` entries); and the real customer graph behind CON-2 |
| AEA-52 | **Runtime:** staff routes on the real services, behind SCR-5…SCR-8 and AC-7, AC-11, AC-19; journeys J-6, J-7, J-8 for AC-13 |
| AEA-53 | **Runtime:** the real `MetricsReader` behind CON-18…CON-20 (AC-8, AC-9, AC-21); `reason_label` import path |
| AEA-58 | **Runtime:** `pytest-playwright` (`--browser-channel`) and the browser J-1/J-9 journeys that AC-13 runs |
| AEA-62 | **Runtime:** the browser legs of J-2, J-3, J-6 and J-8 that AC-13 runs |

No `NEEDS-DECISION`. The UX-5 gate question was answered by Innocent (relayed); R-1 is an orchestrator confirmation,
not a product decision.
